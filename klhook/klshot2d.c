/* klshot2d.c - [Sound] RemoteShot2D / RemoteShot2DDist (2026-10-28, wk-shot2d; re/gun_ui_sounds_1028.md section 3). kl2.exe read statically, NOT run live.
 *
 * ONLINE a remote human's gunshot is the same sound slot (4, shot_player) and group volume as your own, but it is played 3D with distance falloff (flag 0 into 0x9025b0),
 * while your own shot is 2D (flag 1). RemoteShot2D makes a remote ZFFPlayer shooter within RemoteShot2DDist of the local pawn play 2D too (full volume, like your own shot);
 * farther ones stay 3D so the direction still reads. Arcade is untouched: everything is gated on kl_online() (klhook.c), which is 0 in Arcade / story / no session.
 *   RemoteShot2D     0 = off (default), 1 = on, 2 = DRY (log only, nothing changes)
 *   RemoteShot2DDist cm (game units, GUESS: 1 unit = 1 cm), default 1500; the remote shooter's 3D distance to the local pawn must be <= this
 *
 * WHY NOT E8 DETOURS ON THE CALLS TO 0x503650 (the brief's idea): its arg2 is NOT the 2D flag. 0x503650(this = weapon, arg1 = shooter, arg2 = ?) computes the 2D byte itself
 * (0x5036d4..0x503708: shooter == [gd+0x828+4*(char)[gd+0x898]], i.e. 0x660b00(0), or the session test) and OVERWRITES its own arg1 stack slot with it ([esp+0x10], 0x503702/0x503708),
 * then pushes it as arg2 of 0x9025b0 (#def slot 4). So the caller cannot ask for 2D. The two sites that matter are INSIDE 0x503650, both reached only for a ZFFPlayer shooter
 * (a non-ZFFPlayer jumps at 0x5036ce to the slot-1 npc path):
 *   site A 0x503764  8b 4c 24 10 51   mov ecx,[esp+0x10] ; push ecx        (default state, [[shooter+0x54]+0x42]==0; then `push 4` = slot 4, the 2D byte is the computed one)
 *   site B 0x50375b  b8 04 00 00 00   mov eax,4                            (then `push ebx` = 2D 0 and `push eax`; state outside 1..6 with [[shooter+0x54]+0x42]!=0)
 * Both are patched with E9 rel32 to a naked stub (the 5 patched bytes are exactly one or two whole instructions, nothing else jumps into them: checked by disassembly).
 * WHICH CALLERS: the stub only acts when 0x503650 was called from the FIRE path, i.e. its return address (at [esp+0xc] on entry to both sites: ebx, edi, ebp pushed at 0x503650..0x5036a5,
 * then ret) is 0x4cca6d (the call at 0x4cca68: `mov ecx,esi ; push edi(shooter) ; push [esp+0x24]`, E8 rel32 = e8 e3 6b 03 00). The calls at 0x8c567b / 0x8c56ea / 0x8c5837 are NOT shots: they
 * run right after `mov [owner+0xd70],5 / 4 / 6` (the owner state that 0x503650 maps to slots 0 / 9 / 3 via the table at 0x5039a4), on `this = [ecx+0x2c]`, not the fire routine; so they are
 * excluded (GUESS: states 4..6 are not shots; if one of them reaches slot 4 through site A it is simply not touched).
 * Register handling: both stubs save EFLAGS and every general register around the C decision (pushad / pushfd ... popfd / popad), re-run the displaced instruction(s) themselves and jump
 * back. The decision runs under __try; any fault = the original behaviour. A refused patch (SHIP build / SessionSafe / other bytes) is logged and nothing changes. */
#ifndef KLSHOT2D_C
#define KLSHOT2D_C

#define KLSS_SITE_A   0x00503764u
#define KLSS_SITE_B   0x0050375bu
#define KLSS_BACK_A   0x00503769u              /* after `push ecx` (the `push 4` follows) */
#define KLSS_BACK_B   0x00503760u              /* after `mov eax,4` (`push ebx ; push eax` follow) */
#define KLSS_PUSH_B   0x0050376bu              /* the `mov ecx,edi ; call 0x9025b0` both paths join */
#define KLSS_FIRE_RET 0x004cca6du              /* return address of the call 0x4cca68 -> 0x503650 */

static int klss_mode, klss_dist = 1500, klss_patched;
static DWORD klss_back_a, klss_back_b, klss_push_b, klss_fire_ret, klss_force;
static LONG klss_n_fire, klss_n_remote, klss_n_force, klss_n_far, klss_n_fault, klss_logn;
static DWORD klss_logt;

static void klss_log(const char *fmt, DWORD shooter, int site, float d)
{
    DWORD now = GetTickCount();
    if (klss_logn >= 300 || now - klss_logt < 1000) return;      /* at most one line a second, 300 a run */
    klss_logt = now; klss_logn++;
    klog(fmt, shooter, site == 0 ? 'A' : 'B', d, klss_dist, (long)klss_n_fire, (long)klss_n_remote, (long)klss_n_force, (long)klss_n_far);
}

/* 1 = play this shot 2D. Called from both stubs (cdecl; the stubs preserve every register around it). */
static int __cdecl klss_decide(DWORD shooter, DWORD ret, int site)
{
    int r = 0;
    __try {
        DWORD gd, loc = 0; BYTE sel = 0xff; float a[3], b[3], d = 0; int ha, hb;
        if (!klss_mode || ret != klss_fire_ret || !shooter) return 0;      /* only the fire path (0x4cca68) */
        InterlockedIncrement(&klss_n_fire);
        if (!kl_online()) return 0;                                         /* Arcade / story / no session: untouched */
        gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c));
        if (gd && klh_rd(gd + 0x898, &sel, 1) && sel < 28) loc = klh_rd32(gd + 0x828 + 4 * sel);      /* = 0x660b00(0), the callee's own "local pawn" */
        if (shooter == loc) return 0;                                       /* already 2D (site A) / left as it is */
        InterlockedIncrement(&klss_n_remote);
        /* positions: scene node first, then +0x460, as klauto.c kla_player_pos (the node follows the body, +0x460 can go stale) */
        ha = kle_node(klh_rd32(shooter + 4), a, 0) || (klh_rd(shooter + 0x460, a, 12) && (a[0] != 0 || a[2] != 0));
        hb = loc && (kle_node(klh_rd32(loc + 4), b, 0) || (klh_rd(loc + 0x460, b, 12) && (b[0] != 0 || b[2] != 0)));
        if (!ha || !hb) { klss_log("shot2d: remote shooter %08lx site %c: no position for it or the local pawn (%.0f); stays 3D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, 0.0f); return 0; }
        d = sqrtf((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
        if (!(d <= (float)klss_dist)) { InterlockedIncrement(&klss_n_far); klss_log("shot2d: remote shooter %08lx site %c at %.0f cm: beyond the limit, stays 3D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, d); return 0; }
        InterlockedIncrement(&klss_n_force);
        if (klss_mode == 2) { klss_log("shot2d: DRY remote shooter %08lx site %c at %.0f cm: would play 2D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, d); return 0; }
        klss_log("shot2d: remote shooter %08lx site %c at %.0f cm: played 2D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, d);
        r = 1;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        r = 0;
        if (InterlockedIncrement(&klss_n_fault) <= 5) klog("shot2d: FAULT %08lx in the decision; the original 3D/2D flag is kept", (unsigned long)GetExceptionCode());
    }
    return r;
}

/* site A, entered by E9 from 0x503764 with the stack of 0x503650 after its 3 pushes: [esp]=ebp(shooter) +4 edi +8 ebx +0xc ret +0x10 arg1/2D byte */
static __declspec(naked) void klss_stub_a(void)
{
    __asm {
        pushad
        pushfd
        mov eax, [esp + 0x24 + 0x0c]      ; return address of 0x503650
        push 0
        push eax
        push ebp                          ; the shooter
        call klss_decide
        add esp, 12
        mov klss_force, eax
        popfd
        popad
        mov ecx, [esp + 0x10]             ; the displaced instruction pair
        cmp klss_force, 0
        je keep
        mov cl, 1                         ; the 2D byte (0x9025b0 reads only its low byte, movzx at 0x9025d7)
    keep:
        push ecx
        jmp dword ptr [klss_back_a]
    }
}
/* site B, entered by E9 from 0x50375b (mov eax,4) with the same stack */
static __declspec(naked) void klss_stub_b(void)
{
    __asm {
        pushad
        pushfd
        mov eax, [esp + 0x24 + 0x0c]
        push 1
        push eax
        push ebp
        call klss_decide
        add esp, 12
        mov klss_force, eax
        popfd
        popad
        mov eax, 4                        ; the displaced instruction: #def slot 4
        cmp klss_force, 0
        je keep
        push 1                            ; 2D instead of `push ebx` (0)
        push eax
        jmp dword ptr [klss_push_b]
    keep:
        jmp dword ptr [klss_back_b]
    }
}

static void klss_init(void)
{
    static const BYTE ea[5] = { 0x8b, 0x4c, 0x24, 0x10, 0x51 }, eb[5] = { 0xb8, 0x04, 0x00, 0x00, 0x00 };
    BYTE put[5]; DWORD rel; int okA, okB;
    klss_mode = (int)GetPrivateProfileIntA("Sound", "RemoteShot2D", 0, klh_ini); if (klss_mode < 0 || klss_mode > 2) klss_mode = 0;      /* (recommended off: not yet run live) */
    klss_dist = (int)GetPrivateProfileIntA("Sound", "RemoteShot2DDist", 1500, klh_ini); if (klss_dist < 0) klss_dist = 0; if (klss_dist > 1000000) klss_dist = 1000000;
    if (!klss_mode) return;
    if (!klh_exe_ok) { klog("shot2d: RemoteShot2D=%d but this is not the known kl2.exe; nothing is patched", klss_mode); return; }
    klss_back_a = (DWORD)(DWORD_PTR)KLH_VA(KLSS_BACK_A); klss_back_b = (DWORD)(DWORD_PTR)KLH_VA(KLSS_BACK_B); klss_push_b = (DWORD)(DWORD_PTR)KLH_VA(KLSS_PUSH_B);
    klss_fire_ret = (DWORD)(DWORD_PTR)KLH_VA(KLSS_FIRE_RET);
    {   /* the fire-path call itself must still be the E8 to 0x503650 this was written against, else the return-address gate would never match: refuse */
        BYTE c[5]; DWORD want = 0x503650u - (0x4cca68u + 5);
        if (!klh_rd((DWORD_PTR)KLH_VA(0x4cca68), c, 5) || c[0] != 0xE8 || memcmp(c + 1, &want, 4)) { klog("shot2d: the call at 0x4cca68 is not `call 0x503650`; nothing is patched"); return; }
    }
    put[0] = 0xE9; rel = (DWORD)(DWORD_PTR)klss_stub_a - (DWORD)(DWORD_PTR)KLH_VA(KLSS_SITE_A + 5); memcpy(put + 1, &rel, 4);
    okA = klh_poke(KLH_VA(KLSS_SITE_A), ea, 5, put, 5, "shot2d site A");
    rel = (DWORD)(DWORD_PTR)klss_stub_b - (DWORD)(DWORD_PTR)KLH_VA(KLSS_SITE_B + 5); memcpy(put + 1, &rel, 4);
    okB = klh_poke(KLH_VA(KLSS_SITE_B), eb, 5, put, 5, "shot2d site B");
    klss_patched = okA + okB;
    klog("shot2d: RemoteShot2D=%d (2 = dry) dist %d cm: site A 0x503764 %s, site B 0x50375b %s%s", klss_mode, klss_dist, okA ? "patched" : "REFUSED (other bytes, SHIP build or SessionSafe)",
         okB ? "patched" : "REFUSED (other bytes, SHIP build or SessionSafe)", klss_patched == 0 ? "; nothing changes" : "");
}

#endif /* KLSHOT2D_C */
