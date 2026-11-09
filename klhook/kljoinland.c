/*
 * kljoinland.c - the move of kljoin.c's [Join] Land= (2026-11-09). Included by klhook.c after klfallrescue.c (uses klfc_guard, klfc_pose,
 * klfc_cur_act, klfc_movid, KLFC_TELE of klfreeclimb.c; klj_land, klj_cs, klj_feet of kljoin.c; klland_step of klland_logic.h).
 *
 * WHY: a jump always lands ON the jump point (kljoin.c: Target= is only a check). DD10 Flat Raid's ledge ride ends on 06_Exit (8300, 0, 1100),
 * the van's drive-in lane and the parked van's body; bench dd10ledgefix1109 (live map, KLJoin 600409d7) jumped there and was KILLED BY RED 3.6 s
 * later as the van drove in. The exit box's south strip (8300, 750) lived through the drive-in and the wait (dd10side1109).
 *
 * WHAT: kljoin.c's klj_fire arms klj_land (entry place, Land= place, request tick) when the box has Land=, [KLHook] JoinLand=1 and no network
 * session. Here, on the game thread's gameplay tick only: once his feet are within 300 of the entry (300 ms .. 3 s after the request, see
 * klland_logic.h) and no action / seat / carrier runs, the local player is put at Land (+10 up) with his own rotation by 0x82cc40
 * (P, M, pos, resetVel 1, force 0, net 0) - the placement klfallrescue.c / klunstick.c use live - and his velocity floats are zeroed.
 * Cover first left as klfallrescue.c does. A fault disables it for the session (logged). The AI crew is not moved (it lands on the entry).
 * GUESS: that a move 300+ ms after the jump is late enough for the game's own placement (RT4: on the entry within 0.25 s) and early enough
 * for the van (the death came 3.6 s after the request); that 0x82cc40 with force 0 accepts a floor place 320 units away.
 *
 * LOG   join: player 0 landed: moved from (8300, 0, 1100) to (8300, 10, 780) (box 11 Land=, 412 ms after the request)
 *       join: player 0 NOT landed (box 11 Land=): he is not at the jump point (no jump, or he moved on)
 */
#ifndef KLJOINLAND_C
#define KLJOINLAND_C

static int kljl_dead;

static int kljl_body(void *unused)
{
    DWORD gd, P, now = GetTickCount(); signed char pi = -1; BYTE b = 0; int r, busy, have, id; float feet[3] = { 0, 0, 0 }, M[9], pf[3], to[3];
    const char *why = 0;
    (void)unused;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)))) return 0;
    if (!klh_rd(gd + 0x898 + klj_land.player, &pi, 1) || pi < 0 || pi > 27) P = 0;
    else P = klh_rd32(gd + 0x828 + 4 * pi);
    if (P && (klh_pvt(P) != KLFC_PLAYER_VT || !klfc_ok(P, 0x2e00) || !klh_rd(P + 0x2720, &b, 1) || !(b & 2))) P = 0;   /* not a ZFFPlayer / not the local human */
    have = P && klj_feet(P, feet);
    busy = !P || klfc_cur_act(P) != 0 || klh_rd32(P + 0xd50) || klh_rd32(P + 0xd44);
    r = klland_step(now, klj_land.at, have, feet, klj_land.entry, busy, &why);
    if (r < 0) { klj_land.armed = 0; klog("join: player %d NOT landed (box %d Land=): %s", klj_land.player, klj_land.box + 1, why); return 0; }
    if (r == 0 || !klfc_pose(P, M, pf)) return 0;
    klj_land.armed = 0;
    to[0] = klj_land.land[0]; to[1] = klj_land.land[1] + 10.0f; to[2] = klj_land.land[2];
    id = klfc_movid(P);
    if (id == 8 && klh_rd32(P + 0x2810)) KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_LEAVECOVER)(P, 0);
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, const float *, const float *, int, int, int), KLFC_TELE)(P, 0, M, to, 1, 0, 0);
    { float z[3] = { 0, 0, 0 }; klh_data((void *)(DWORD_PTR)(P + 0x808), z, 12, "join land velocity"); }
    klog("join: player %d landed: moved from (%.0f, %.0f, %.0f) to (%.0f, %.0f, %.0f) (box %d Land=, %lu ms after the request)", klj_land.player,
         feet[0], feet[1], feet[2], to[0], to[1], to[2], klj_land.box + 1, now - klj_land.at);
    return 0;
}

static void kljl_tick(int game_thread)
{
    if (!klj_land.armed || kljl_dead || !game_thread || !klh_exe_ok) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;           /* the gameplay call of the main loop only */
    EnterCriticalSection(&klj_cs);
    if (klj_land.armed && kl_online()) { klj_land.armed = 0; klog("join: Land= dropped: a network session started"); }
    if (klj_land.armed && klfc_guard("join land", kljl_body, 0) < 0) { klj_land.armed = 0; kljl_dead = 1; klog("join: Land= DISABLED for this session (fault) - restart the game before testing again"); }
    LeaveCriticalSection(&klj_cs);
}
#endif /* KLJOINLAND_C */
