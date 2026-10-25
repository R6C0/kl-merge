/*
 * kllobby.c - [Lobby] MinPlayers: lets a Fragile Alliance lobby start with fewer than 4 players, the way Dead Men's
 * config allowed 1. Part of KLHook (included by klhook.c after klnet.c, SHIP and TEST alike); DATA writes only.
 *
 * WHAT THE EXE SHOWS (read 2026-10-22/23, kl2.exe 0490; re\lobby_start.md has the full reading by e8):
 *   sm = [0x168e598] (ZSessionManagerMultiplayer, vtable 0xbd1ebc). [sm+0xb9] = the lobby's TARGET size (getter 0x54d140;
 *   the lobby row "Number of players"), [sm+0xb8] = the maximum. The host's LEFT on that row (0x7dc4f9) floors it at 4
 *   (6 in Cops & Robbers); the setter 0x739f20 only clamps to [connected, 12]: the engine itself has no floor of 4.
 *   It is also the JOIN gate: ZSessionHandlerServer slot 49 (0x5067c7) refuses a new peer once [sm+0xb9] <= connected.
 *   The start is the state machine 0x6c49a0: in 0xd a 15 s countdown runs while connected >= [sm+0xb9]; the host's own
 *   Ready (lobby action 0x5a9920) moves 0xd -> 0xe at once; 0xe -> 0xf needs connected >= [sm+0xb9] and every peer's
 *   replicated state >= 0xe (each player's Ready), then the level loads.
 *   Connected = 0x698250 = the size of the handler's list [[sm+4]+8] +8 .. +0xc (H2: 1 with the host alone, so the host counts).
 * WHAT IT DOES: while this machine HOSTS a game type 4 lobby, nothing is written until the host itself has pressed Ready
 *   (state 0xe); then, with at least MinPlayers connected, the target is lowered to the number connected, so the round
 *   starts as soon as everyone in it is Ready. Before the host's Ready the target stays what the game / the menu set, so
 *   more players can still join (H2's version held it at MinPlayers from the start and would have turned a 3rd away).
 *   A client writes nothing. Not replicated to the clients (the game's own path calls 0x6484d0): H2 started without it.
 *
 * KLHook.ini
 *   [Lobby]
 *   MinPlayers=0     0 = off (the game's own rule). 1..8: the host's Ready starts the round once this many are connected.
 */
#ifndef KLLOBBY_C
#define KLLOBBY_C

static int kllb_min;
static BYTE kllb_orig;                                           /* the target the lobby had before the host's Ready lowered it (klbotfill.c: fill = this - connected) */

static void kllb_init(void)
{
    kllb_min = GetPrivateProfileIntA("Lobby", "MinPlayers", 0, klh_ini);
    if (kllb_min < 0 || kllb_min > 8) kllb_min = 0;
    if (!kllb_min && GetPrivateProfileIntA("Bots", "OnlineFill", 0, klh_ini)) { kllb_min = 1; klog("lobby: [Bots] OnlineFill=1 implies MinPlayers=1"); }
    if (kllb_min) klog("lobby: MinPlayers=%d - a hosted FA lobby starts on the host's Ready once that many are connected", kllb_min);
}

static void kllb_tick(void)
{
    static DWORD last, told_sm; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, h, v, lo, hi; BYTE cur = 0, want;
    if (!kllb_min || !klh_exe_ok || now - last < 200) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || klh_rd32(sm) != 0xbd1ebc) return;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4) || !klh_rd(sm + 0xb9, &cur, 1)) return;
    if (role != 2 || mode != 4 || state != 0xe) { if (state < 0xd || state > 0xf) told_sm = 0; if (state < 0xd) kllb_orig = 0; return; }
    if (!(h = klh_rd32(sm + 4)) || !(v = klh_rd32(h + 8))) return;
    lo = klh_rd32(v + 8); hi = klh_rd32(v + 0xc);
    if (!lo || hi < lo || hi - lo > 16) return;                   /* the count 0x698250 returns, read as data */
    if ((int)(hi - lo) < kllb_min || cur <= (BYTE)(hi - lo)) return;
    want = (BYTE)(hi - lo);
    if (!kllb_orig) kllb_orig = cur;
    if (!klh_data((void *)(DWORD_PTR)(sm + 0xb9), &want, 1, "lobby target players")) return;
    if (told_sm != sm) { klog("lobby: host Ready with %u connected: target players %u -> %u (round starts when all are Ready)", want, cur, want); told_sm = sm; }
}

#endif /* KLLOBBY_C */
