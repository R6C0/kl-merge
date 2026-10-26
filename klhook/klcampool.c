/* klcampool.c - [CamPool]: give back a player camera the game leaked at a quick round restart (included from klcamsmooth.c).
 *
 * CRASH IT ANSWERS (peer kl-merge-ce, COVER6 DM05A in F01, Arcade, 2026-10-26 03:20, out_all_1026d_test): two MissionFailedReload
 * restarts (session 0x19 -> 0x16 -> 0x18) 10 s apart, then the int3 at 0x60a5bf and a FATAL write to 0xba0 in 0x586eb0.
 * FINDINGS (peer's 3-agent workflow, its verifier; the release routine re-read here 2026-10-26):
 *   - The ZCameraHandler at [gd+0x15d8] keeps vector 0 at +4 (begin) / +8 (end) of 8-byte entries: camera pointer, free byte at +4
 *     (nonzero = free). Each ZFFCamera1 registers one at load (0x890a30); DM05A has exactly 2.
 *   - TAKE 0x5f6d70 (only caller 0x60a5b0 in the player init 0x60a520, run at every 0x16 -> 0x18) returns the first free entry into
 *     [P+0xbd8] and never gives the old [P+0xbd8] back first.
 *   - RELEASE 0x418310: thiscall, ecx = the handler, one stack argument = the camera pointer, ret 4 (READ: 0x418310..0x41835d scans
 *     vector 0 only, cmp bl,1); a pointer it does not find is a no-op. Its only caller 0x7b68d0 (player deinit-camera) runs at the
 *     round's own end states (0x20 / 0x28, slot 21), so a normal restart (0x19 -> 0x1f .. 0x27 -> 0x16) balances; the direct
 *     0x19 -> 0x16 restart leaks one entry per restart and the 2nd one in a load empties a pool of 2.
 * WHAT IT DOES (SHIP-legal: reads + one game call, no code patch): once a second while the session is 0x19 (the round runs), on the
 *   game thread: when vector 0 has NO free entry and a taken entry's camera is held by no player's [P+0xbd8] (all 28 slots of
 *   [gd+0x828]), it calls 0x418310(handler, that camera). The leak of the first restart is so given back before a second one needs it.
 *   It never touches a camera a player holds, and does nothing while any entry is free.
 *   GUESS: nothing but a player's +0xbd8 holds a pool camera (the FA escape camera is looked up by name in 0x7b68d0, not taken here).
 * ini: [CamPool] Enable=1 (recommended on)   Log=1 (one line per release, one line at the first check of a load)
 */
#ifndef KLCAMPOOL_C
#define KLCAMPOOL_C

#define KLCP_RELEASE 0x00418310u
#define KLCP_SM      0x0168e598u

static struct { int enable, log, told, nrel; DWORD last, handler; } kcp;

static void klcampool_init(void)
{
    memset(&kcp, 0, sizeof kcp);
    kcp.enable = GetPrivateProfileIntA("CamPool", "Enable", 1, klh_ini) != 0;
    kcp.log = GetPrivateProfileIntA("CamPool", "Log", 1, klh_ini) != 0;
    if (kcp.enable) klog("campool: on - a pool camera held by no player is given back (0x418310) when the pool has none free (recommended on)");
}

static void klcampool_tick(int game_thread)
{
    static const BYTE rel[13] = { 0x53, 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x10, 0x32, 0xdb, 0x8d, 0xa4, 0x24, 0x00 };      /* 0x418310 (read from kl2.exe 2026-10-26) */
    DWORD now = GetTickCount(), gd, sm, h, b, e, n, i, ent[2 * 16], held[KLCAM_NPL]; int nfree = 0, k, nh = 0;
    if (!kcp.enable || !klh_exe_ok || !game_thread || now - kcp.last < 1000) return;
    kcp.last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLCP_SM))) || klh_rd32(sm + 0x70) != 0x19) return;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(h = klh_rd32(gd + 0x15d8))) return;
    if (!(b = klh_rd32(h + 4)) || !(e = klh_rd32(h + 8)) || e <= b || (n = (e - b) / 8) > 16) return;
    if (!klh_rd(b, ent, n * 8)) return;
    for (i = 0; i < n; i++) if (ent[2 * i + 1] & 0xff) nfree++;
    if (h != kcp.handler) { kcp.handler = h; if (kcp.log) klog("campool: handler %08lx: %lu camera(s) in the pool, %d free", h, n, nfree); }
    if (nfree) return;
    for (k = 0; k < KLCAM_NPL; k++) { DWORD pl = klh_rd32(gd + 0x828 + 4 * k), c; if (pl && klh_rd32(pl) == KLCAM_PL_VT && (c = klh_rd32(pl + 0xbd8))) held[nh++] = c; }
    if (!klb_same_code(KLCP_RELEASE, rel, sizeof rel)) { if (!kcp.told && (kcp.told = 1)) klog("campool: 0x418310 is not the routine this build knows: nothing done"); return; }
    for (i = 0; i < n; i++) {
        DWORD cam = ent[2 * i]; BYTE fl = 0xff;
        for (k = 0; k < nh && held[k] != cam; k++) ;
        if (!cam || k < nh) continue;
        __try { ((void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLCP_RELEASE))((void *)(DWORD_PTR)h, 0, cam); }
        __except (EXCEPTION_EXECUTE_HANDLER) { klog("campool: 0x418310 faulted on camera %08lx (caught)", cam); return; }
        klh_rd(b + i * 8 + 4, &fl, 1);
        kcp.nrel++;
        if (kcp.log) klog("campool: pool %08lx had 0 of %lu free; camera %08lx (entry %lu) is held by no player (%d hold one): given back, free byte now %u (release %d this run)", h, n, cam, i, nh, fl, kcp.nrel);
        return;                                     /* one a second is plenty */
    }
}

#endif
