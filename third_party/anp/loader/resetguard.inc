/* resetguard.inc (13 Oct) - D3D device reset: drop the render command lists built before the reset.
   ANP_guards.txt reset=on|all|off (default on). Import-slot hook only (kl2 IAT KERNEL32!SetEvent 0xb100fc, checked by
   name through the import table); no kl2 code byte is changed (CEG).

   Bug (kl2, static RE; m12_1556\evidence.txt, re-verified 13 Oct by disassembly):
   - ZRenderWintelD3D (vt 0xb97454, r = [[0xdd2640]+0x970]) slot 41 0x459ac0 waits for the render thread, then calls
     slot 158 0x84eb50 (vt+0x278). TestCooperativeLevel (0x6535e0) = D3DERR_DEVICENOTRESET -> 0x456bf0: r+0x11a8 = 1,
     OnLostDevice on the resource list r+0x1908 (frees the D3DPOOL_DEFAULT render targets), Reset (0x622580),
     OnResetDevice (recreates them at NEW addresses), then, threaded (r+0x11b5): ResetEvent(r+0x11d4),
     SetEvent(r+0x11d0) at 0x456d6c (return address 0x456d72), r+0x11a8 = 0. Slot 41 then jumps to 0x66e530, which
     kicks the render thread (SetEvent r+0x11d4) on the command list built earlier in the same frame.
   - Render thread 0x561330: waits r+0x11d4; if r+0x11a8: SetEvent(r+0x11c4), wait r+0x11d0 (parked during the reset);
     else runs the list [cb+0xa868c+4*[cb+0xa8694]] (cb = r+0xfc) with 0x7c1c30: commands from [l+0x14] to [l+0xc].
   - Those commands hold raw surface/texture pointers (0x55ba70: SetRT [r+0x1814]+0x4c, blur src [r+0x17dc]+0x44), so
     the replay touches freed D3D objects (13 Oct 15:56 M12: d3d9 GetDesc on a stale surface, render thread).
     kl2's other RT-recreate paths (0x6803a0, 0x7ec850) call slot 14 0x696100 first, which empties both lists:
       0x696157: l = [cb+0xa868c+4*idx], [l+8] = 0, [l+0xc] = [l+0x14]; 0x696177: the other list ([cb+0xa8690-4*idx]).
     0x456bf0 does not.
   Fix: in the SetEvent import hook, only when the return address is 0x456d72, the handle is r+0x11d0 and r+0x11a8 is
   still 1 (reset succeeded, render thread parked on r+0x11d0, nothing reads the lists): empty both lists exactly as
   slot 14 does, BEFORE the event is set. Cost: one frame not drawn after a device reset.
   reset=all also covers 0x8bba00 (renderer state 4 recreate, e.g. a display mode change: 0x787a30 releases the RTs,
   Reset, recreate, then the same ResetEvent/SetEvent(r+0x11d0) at 0x8bbc5d, return address 0x8bbc63) - same condition
   (r+0x11a8 set). Off by default: not tied to a crash yet; with reset=on that site is only logged.
   Diagnostics: changes of r+0x11a8 (device lost flag), r+0x1188 (renderer state; 4 = recreate path) and r+0x11b6
   (frame waited but not kicked) from the PeekMessage tick (rate-limited). */

#define RG_VT_RENDER    0xb97454
#define RG_RA_RESET     0x456d72
#define RG_RA_RECREATE  0x8bbc63
typedef BOOL (WINAPI *SetEvent_t)(HANDLE);
static SetEvent_t real_SetEvent;
static volatile LONG g_rgResets, g_rgRecreates, g_rgDropped;
static int g_rgLines;

static BYTE *rg_renderer(void) {
    DWORD app = readable((void*)0xdd2640, 4) ? *(DWORD*)0xdd2640 : 0;
    BYTE *r = (app && readable((void*)(app + 0x970), 4)) ? *(BYTE**)(app + 0x970) : 0;
    return (r && readable(r, 0x1910) && *(DWORD*)r == RG_VT_RENDER) ? r : 0;
}
/* empty both render command lists as slot 14 does; returns the number of list bytes dropped, *cnt = sum of [l+8] */
static DWORD rg_empty_lists(BYTE *r, int act, DWORD *cnt, DWORD *n8, DWORD *nb) {
    BYTE *cb = readable(r + 0xfc, 4) ? *(BYTE**)(r + 0xfc) : 0; DWORD bytes = 0; *cnt = 0;
    n8[0] = n8[1] = nb[0] = nb[1] = 0;
    if (!cb || !readable(cb + 0xa868c, 8)) return 0;
    for (int k = 0; k < 2; k++) {
        BYTE *l = *(BYTE**)(cb + 0xa868c + 4 * k);
        if (!l || !readable(l, 0x18)) continue;
        n8[k] = *(DWORD*)(l + 8); nb[k] = *(DWORD*)(l + 0xc) - *(DWORD*)(l + 0x14);
        *cnt += n8[k]; bytes += nb[k];
        if (act) { *(DWORD*)(l + 8) = 0; *(DWORD*)(l + 0xc) = *(DWORD*)(l + 0x14); }
    }
    return bytes;
}
static void rg_on_set(HANDLE h, DWORD ra) {
    BYTE *r = rg_renderer();
    if (!r || h != *(HANDLE*)(r + 0x11d0)) return;
    int lost = r[0x11a8] != 0, reset = ra == RG_RA_RESET;
    /* review 13 Oct: 0x8bba00 (state-4 recreate) never sets +0x11a8, and at 0x456bf0 it is always set (0x456bfc), so
       'lost' only informs; both sites run after slot 41's wait (render thread idle) */
    int act = reset ? 1 : (g_gReset == 2);
    DWORD cnt, n8[2], nb[2], bytes = rg_empty_lists(r, act, &cnt, n8, nb);
    LONG n = InterlockedIncrement(reset ? &g_rgResets : &g_rgRecreates);
    if (act) InterlockedExchangeAdd(&g_rgDropped, (LONG)cnt);
    if (g_rgLines++ < 200)
        anp_log("resetguard: device %s #%ld (kl2 %s ok, lost flag %d, thread %lu) - %s %lu pending render commands "
                "(lists +8 %lu/%lu, bytes %lu/%lu)", reset ? "reset" : "recreate", n, reset ? "0x456bf0" : "0x8bba00", lost,
                GetCurrentThreadId(), act ? "dropped" : "NOT dropped", cnt, n8[0], n8[1], nb[0], nb[1]);
    (void)bytes;
}
static BOOL WINAPI my_SetEvent(HANDLE h) {
    DWORD ra = (DWORD)__builtin_return_address(0);
    if ((ra == RG_RA_RESET || ra == RG_RA_RECREATE) && g_gReset) rg_on_set(h, ra);
    return real_SetEvent(h);
}
static void resetguard_install(void) {
    if (!g_gReset) { anp_log("resetguard: off (ANP_guards.txt reset=off)"); return; }
    static const BYTE s1[] = {0x8b, 0x8f, 0xd0, 0x11, 0x00, 0x00, 0x51, 0xff, 0x15, 0xfc, 0x00, 0xb1, 0x00,
                              0xc6, 0x87, 0xa8, 0x11, 0x00, 0x00, 0x00};                          /* 0x456d65 */
    static const BYTE s2[] = {0x8b, 0x8e, 0xd0, 0x11, 0x00, 0x00, 0x51, 0xff, 0x15, 0xfc, 0x00, 0xb1, 0x00,
                              0x5f, 0xc6, 0x86, 0xa8, 0x11, 0x00, 0x00, 0x00};                    /* 0x8bbc56 */
    static const BYTE s14[] = {0x8b, 0x86, 0xfc, 0x00, 0x00, 0x00, 0x8b, 0x88, 0x94, 0x86, 0x0a, 0x00, 0x8b, 0x84, 0x88,
                               0x8c, 0x86, 0x0a, 0x00, 0x8b, 0x50, 0x14, 0xc7, 0x40, 0x08, 0x00, 0x00, 0x00, 0x00,
                               0x89, 0x50, 0x0c};                                                  /* 0x696157 */
    if (!code_byte_ok(0x456d65, s1, sizeof s1) || !code_byte_ok(0x8bbc56, s2, sizeof s2) || !code_byte_ok(0x696157, s14, sizeof s14)) {
        g_gReset = 0; anp_log("resetguard: unexpected kl2 bytes at 0x456d65 / 0x8bbc56 / 0x696157 - NOT installed"); return;
    }
    hook_iat(GetModuleHandleA(NULL), "kernel32.dll", "SetEvent", my_SetEvent, (void**)&real_SetEvent);
    if (!real_SetEvent) g_gReset = 0;
    anp_log("resetguard: SetEvent import hook %s (mode %s: drop the pre-reset render lists after 0x456bf0%s)",
            real_SetEvent ? "ok" : "MISSING - guard off", g_gReset == 2 ? "all" : "on", g_gReset == 2 ? " and 0x8bba00" : "");
}
/* PeekMessage tick: log renderer state changes (data reads only) */
static void resetguard_tick(DWORD now) {
    static DWORD last, lastB6Log; static BYTE *lr; static int la8 = -1, lb6 = -1, init; static DWORD l1188 = 0xffffffff;
    static LONG b6Changes, b6Logged;
    if (now - last < 50) return;
    last = now;
    BYTE *r = rg_renderer();
    if (!r) return;
    int a8 = r[0x11a8], b6 = r[0x11b6]; DWORD s = *(DWORD*)(r + 0x1188);
    if (r != lr) {
        lr = r; la8 = a8; lb6 = b6; l1188 = s;
        if (!init++ || g_rgLines++ < 200)
            anp_log("resetguard: renderer %p threaded(+11b5)=%d lost(+11a8)=%d state(+1188)=%lu +11b6=%d", r, r[0x11b5], a8, s, b6);
        return;
    }
    if ((a8 != la8 || s != l1188) && g_rgLines++ < 200)
        anp_log("resetguard: renderer lost(+11a8) %d -> %d state(+1188) %lu -> %lu (+11b6 %d) resets %ld recreates %ld dropped %ld",
                la8, a8, l1188, s, b6, g_rgResets, g_rgRecreates, g_rgDropped);
    if (b6 != lb6) {
        b6Changes++;
        if (b6Logged < 10 || now - lastB6Log >= 10000) {
            b6Logged++; lastB6Log = now;
            if (g_rgLines++ < 200) anp_log("resetguard: renderer +11b6 %d -> %d (%ld changes so far)", lb6, b6, b6Changes);
        }
    }
    la8 = a8; l1188 = s; lb6 = b6;
}
