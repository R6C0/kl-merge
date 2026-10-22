/*
 * kllobby.c - [Lobby] MinPlayers: lets a Fragile Alliance lobby start with fewer than 4 players, the way Dead Men's
 * config allowed 1. Part of KLHook (included by klhook.c after klnet.c, SHIP and TEST alike); DATA writes only.
 *
 * WHAT THE EXE SHOWS (read 2026-10-22, kl2.exe 0490):
 *   sm = [0x168e598] (ZSessionManagerMultiplayer, vtable 0xbd1ebc). [sm+0xb9] = the lobby's minimum number of players
 *   (getter 0x54d140; the lobby row "Number of players"), [sm+0xb8] = the maximum.
 *   The host's LEFT on that row (0x7dc4f9) does min-1 and floors it at 4 (6 in Cops & Robbers, [0x168e59c] == 2);
 *   RIGHT (0x7dcb57) caps it at 8 (12). Both then call the setter 0x739f20, which only clamps to
 *   [players connected (session handler slot 0x48), 12]: the engine itself has no floor of 4.
 *   The 4 is a menu rule, so writing the byte is enough; the code (0x7dc519 `cmp eax,4 / mov al,4`) is not touched
 *   (a SHIP build may not write code).
 * WHAT IT DOES: while this machine is the SERVER (role 2) of a game type 4 session in the lobby (state 0xd / 0xe),
 *   the minimum is held at max(MinPlayers, 1): a larger value (the default 6, or a press of LEFT / RIGHT) goes back.
 *   GUESS: the round starts once the ready players reach the minimum (0x5d4985 compares a ready count with it);
 *   proven only by a live run. A client writes nothing (its byte is not what the host decides on).
 *
 * KLHook.ini
 *   [Lobby]
 *   MinPlayers=0     0 = off (the game's own rule). 1..8: the minimum the host's lobby is held at.
 */
#ifndef KLLOBBY_C
#define KLLOBBY_C

static int kllb_min;

static void kllb_init(void)
{
    kllb_min = GetPrivateProfileIntA("Lobby", "MinPlayers", 0, klh_ini);
    if (kllb_min < 0 || kllb_min > 8) kllb_min = 0;
    if (kllb_min) klog("lobby: MinPlayers=%d - a hosted FA lobby is held at that minimum", kllb_min);
}

static void kllb_tick(void)
{
    static DWORD last, told_sm; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, h, v; BYTE cur = 0, want;
    if (!kllb_min || !klh_exe_ok || now - last < 200) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || klh_rd32(sm) != 0xbd1ebc) return;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4) || !klh_rd(sm + 0xb9, &cur, 1)) return;
    if (role != 2 || mode != 4 || (state != 0xd && state != 0xe)) { told_sm = 0; return; }
    want = (BYTE)kllb_min;
    if (cur <= want) return;
    if (!klh_data((void *)(DWORD_PTR)(sm + 0xb9), &want, 1, "lobby minimum players")) return;
    if (told_sm != sm) {
        h = klh_rd32(sm + 4); v = h ? klh_rd32(h + 8) : 0;
        klog("lobby: minimum players %u -> %u (host, state 0x%lx; connected list %ld bytes)", cur, want, state,
             v ? (long)(klh_rd32(v + 0xc) - klh_rd32(v + 8)) : -1L);
        told_sm = sm;
    }
}

#endif /* KLLOBBY_C */
