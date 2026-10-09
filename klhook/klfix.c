/*
 * klfix.c - repairs of faults that are in kl2.exe itself, by DATA writes only. Part of KLHook (included by
 * klhook.c, SHIP and TEST alike); uses klhook.c's klog, klh_rd32, klh_data, klh_exe_ok, KLH_VA.
 *
 * 1. THE LEADERBOARD ROW COUNT (the score-page crash of run RN11, kl2 0x838922; re\crash_scorepage.md)
 *    ZLeaderBoardServiceSteam (vtable 0xbd5cc4, 0x3208 bytes, built once at boot in ZOnlineServiceSteam's
 *    constructor) holds 114 rows of 0x70 bytes from +0x18 and their count at +0x31fc. Its constructor 0x659790
 *    never writes the count; the only writer is 0x5554aa, when a Steam leaderboard download comes back with at
 *    least one row. The game heap does not clear new blocks, so until then the count is whatever the block
 *    held before. The Arcade score page asks "which row is mine?" (slot 6, 0x8388e0) as soon as its friends
 *    request has ended, with rows or without, and walks that many rows: a leftover above 114 runs into the
 *    object's own tail and calls through a null vtable. No level data is on that path; a stock Subway round
 *    runs the same instructions.
 *      lb = [[[0x168e598] + 0x17c] + 0x198]     valid while [0x168e598] is a ZSessionManagerMultiplayer
 *                                               (vtable 0xbd1ebc) and lb's vtable is 0xbd5cc4
 *      no row held (+0x10 first == +0x14 past-last) and no request running (+0x31f8 == 0)  ->  [lb+0x31fc] = 0
 *    That is the value the constructor should have stored; after a download with rows the game maintains the
 *    field itself. Done once per process, as soon as the chain resolves (the service exists from boot, long
 *    before any page asks). One heap dword: outside every hashed range (re\antitamper.md 2.1).
 *    LIVE (the same write in klauto, 2026-10-09, re\fa_round.md 7.4): values found in eight boots 0, 0,
 *    0x90000003, 0xffffffff, 0, 0, 0, 0 - leftovers as predicted; none above 114 came up, so the crash itself
 *    was not reproduced; six score pages after the write, no fault.
 *    When the tick comes from the fallback thread and not from the game's (klhook.c) the write is not
 *    synchronised with the game. ASSUMPTION that this is harmless: it happens at boot, the game's only write
 *    of the field needs a finished Steam download, and both writers store a valid count.
 *    [KLHook] LbFix=0 only logs the value found ([Auto] LbFix=0 of older test inis is honoured too).
 */
#ifndef KLFIX_C
#define KLFIX_C

static int klf_lb_on = 1, klf_lb_done;

static void klf_lbfix(void)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(0x168e598)), svc, lb, first = 0, last = 0, req = 0, count = 0, zero = 0; int wrote = 0;
    if (!sm || klh_rd32(sm) != 0xbd1ebc) return;
    svc = klh_rd32(sm + 0x17c); if (!svc) return;
    lb = klh_rd32(svc + 0x198); if (!lb || klh_rd32(lb) != 0xbd5cc4) return;
    if (!klh_rd(lb + 0x10, &first, 4) || !klh_rd(lb + 0x14, &last, 4) || !klh_rd(lb + 0x31f8, &req, 4) || !klh_rd(lb + 0x31fc, &count, 4)) return;
    klf_lb_done = 1;
    if (first == last && !req && count && klf_lb_on) wrote = klh_data((void *)(DWORD_PTR)(lb + 0x31fc), &zero, 4, "leaderboard row count");
    klog("leaderboard service %08lx: first %ld, past-last %ld, request %08lx, row count %ld (%08lx)%s", lb, (long)first, (long)last, req, (long)count, count,
         first != last || req ? " - rows held or a request running: left alone" : !count ? " - already 0" : !klf_lb_on ? " - LbFix=0: left as found" :
         !wrote ? " - NOT written (refused or not writable)" :
         (long)count > 114 ? " -> set to 0 (WOULD HAVE CRASHED the score page: more than the 114 rows held)" : " -> set to 0 (harmless value)");
}

static void klf_init(void)
{
    klf_lb_on = GetPrivateProfileIntA("KLHook", "LbFix", 1, klh_ini) && GetPrivateProfileIntA("Auto", "LbFix", 1, klh_ini);
}

static void klf_tick(void)
{
    static DWORD calls;
    if (klh_exe_ok && !klf_lb_done && !(calls++ & 15)) klf_lbfix();        /* every 16th tick until the service has been seen once */
}

#ifdef KLHOOK_HARNESS
/* off-game: run the fix against made-up objects reached through a mapped copy of the image */
__declspec(dllexport) int klf_test_lbfix(void *mapped) { klh_delta = (LONG_PTR)((DWORD_PTR)mapped - KL2_BASE); klh_exe_ok = 1; klf_lb_done = 0; klf_lbfix(); return klf_lb_done; }
#endif
#endif /* KLFIX_C */
