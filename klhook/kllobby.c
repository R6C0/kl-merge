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
 * [Lobby] Solo=1 (2026-10-25, owner: 'system link you can play by yourself and not have this "all players left"'). Seen live (SL2/SL4): a
 *   host alone starts the round (MinPlayers=1) and ~0.3 s after the FAWaitForPlayers page opens the session goes 0x19 -> 0x29 and the
 *   window FAStatus_HostDisconnect covers the round for good. WHAT THE EXE SHOWS (static, kl2.exe 0490):
 *   - sm vtable slot 3 = 0x61a410 (CERTAIN) takes ONE stack argument, an error word (callers: 0x4e4c0e the Steam lobby owner changed = 2 / 0x200,
 *     0x5d91b7 kicked = 2, 0x57da58 = 0x12, ~10 sites = 8 'wrong state', many 'push 0' = clear). It stores it in [sm+0x1b4]; with the LOW NIBBLE
 *     set and bit 0x10 clear (0x61a56b..0x61a575) it calls SetState (slot 26, 0x74c080): states 0x17..0x2a -> 0x29 (0x61a59b), 0x10..0x16 and 0x2b -> 0x2d
 *     (bit 0x10 set). Then 0x61a792: bit 0x10 clear -> 0x420960 opens FAStatus_HostDisconnect (the name at 0xb1b120, CERTAIN).
 *   - WHICH caller raises it with one human is NOT established (GUESS: a 'peers left' check); the wrapper below logs the caller's return address
 *     and the word the first times (that names it). Reading everything else the same, this is the one place all callers pass.
 *   THE LEVER (SHIP-safe, data only): the session manager is a HEAP object; its vtable pointer [sm] is swapped for a private 28-slot copy
 *     (as klchar.c does for the option object; the stock .rdata vtable is never written) whose slot 3 clears the low nibble of the word when
 *     this machine is the HOST (role 2) of a game type 4 session with at most 1 human connected. Everything else (a real error with two or more
 *     humans, a client) passes unchanged. The wrapper runs on the game's thread, called by the game. [Lobby] Solo=1 also implies MinPlayers=1.
 *     Other KLHook modules that test the sm class use KLH_SM_VT_OK (klhook.c), which accepts the copy.
 *
 * KLHook.ini
 *   [Lobby]
 *   MinPlayers=0     0 = off (the game's own rule). 1..8: the host's Ready starts the round once this many are connected.
 *   Solo=0           1 = (recommended off) a host alone in a System Link / Private Match FA lobby can play the round: no HostDisconnect.
 */
#ifndef KLLOBBY_C
#define KLLOBBY_C

#include <intrin.h>                                           /* _ReturnAddress */
static int kllb_min, kllb_solo;
static DWORD kllb_vt[1 + 28];                                    /* [0] = the RTTI locator, [1..28] = the 28 slots of 0xbd1ebc */
static void (__fastcall *kllb_real3)(void *, void *, DWORD);     /* stock slot 3, 0x61a410 */
static LONG kllb_seen, kllb_masked;
static BYTE kllb_orig;                                           /* the target the lobby had before the host's Ready lowered it (klbotfill.c: fill = this - connected) */

static void kllb_init(void)
{
    kllb_min = GetPrivateProfileIntA("Lobby", "MinPlayers", 0, klh_ini);
    if (kllb_min < 0 || kllb_min > 8) kllb_min = 0;
    kllb_solo = GetPrivateProfileIntA("Lobby", "Solo", 0, klh_ini) != 0;
    if (kllb_solo && !kllb_min) { kllb_min = 1; klog("lobby: [Lobby] Solo=1 implies MinPlayers=1"); }
    if (!kllb_min && GetPrivateProfileIntA("Bots", "OnlineFill", 0, klh_ini)) { kllb_min = 1; klog("lobby: [Bots] OnlineFill=1 implies MinPlayers=1"); }
    if (kllb_min) klog("lobby: MinPlayers=%d - a hosted FA lobby starts on the host's Ready once that many are connected", kllb_min);
}

/* humans connected = the size of the handler's list [[sm+4]+8] +8 .. +0xc (what 0x698250 returns), 99 when unreadable */
static int kllb_connected(DWORD sm)
{
    DWORD h, v, lo, hi;
    if (!(h = klh_rd32(sm + 4)) || !(v = klh_rd32(h + 8))) return 99;
    lo = klh_rd32(v + 8); hi = klh_rd32(v + 0xc);
    return (lo && hi >= lo && hi - lo <= 16) ? (int)(hi - lo) : 99;
}

/* sm vtable slot 3 (0x61a410, thiscall, one stack argument, ret 4 = __fastcall with the unused edx): the session error word */
static void __fastcall kllb_slot3(void *self, void *edx, DWORD word)
{
    DWORD role = 0, mode = 0, state = 0; int n = 99, mask = 0;
    if ((word & 0xf) && kllb_solo) {
        if (klh_rd((DWORD_PTR)self + 0x54, &role, 4) && klh_rd((DWORD_PTR)self + 0x5c, &mode, 4) && klh_rd((DWORD_PTR)self + 0x70, &state, 4)) n = kllb_connected((DWORD)(DWORD_PTR)self);
        mask = role == 2 && mode == 4 && n <= 1;
        if (InterlockedIncrement(&kllb_seen) <= 12)
            klog("lobby: Solo: session error word %08lx from %p (role %lu, game type %lu, state 0x%lx, %d connected): %s", (unsigned long)word,
                 (void *)((DWORD_PTR)_ReturnAddress() - (DWORD_PTR)klh_image() + KL2_BASE), (unsigned long)role, (unsigned long)mode, (unsigned long)state, n,
                 mask ? "low nibble cleared (the round goes on)" : "passed unchanged");
        if (mask) { InterlockedIncrement(&kllb_masked); word &= ~0xfu; }
    }
    kllb_real3(self, edx, word);
}

/* give the session manager the private vtable (once), whenever it shows the stock one */
static void kllb_install(DWORD sm)
{
    static LONG told; DWORD vt;
    if (!kllb_vt[0]) {
        if (!klh_rd((DWORD_PTR)KLH_VA(0xbd1ebc - 4), kllb_vt, sizeof kllb_vt)) return;
        if (kllb_vt[1 + 3] != (DWORD)KLH_VA(0x61a410) || kllb_vt[1 + 26] != (DWORD)KLH_VA(0x74c080) || kllb_vt[1 + 27] != (DWORD)KLH_VA(0x6c49a0)) {
            if (!InterlockedExchange(&told, 1)) klog("lobby: Solo: sm vtable slots 3 / 26 / 27 are %08lx / %08lx / %08lx, not the known ones: Solo is off", kllb_vt[1 + 3], kllb_vt[1 + 26], kllb_vt[1 + 27]);
            kllb_solo = 0; return;
        }
        kllb_real3 = (void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)kllb_vt[1 + 3];
        kllb_vt[1 + 3] = (DWORD)(DWORD_PTR)kllb_slot3;
        klh_sm_vt2 = (DWORD)(DWORD_PTR)&kllb_vt[1];
    }
    vt = klh_sm_vt2;
    if (klh_data((void *)(DWORD_PTR)sm, &vt, 4, "session manager vtable") && !InterlockedExchange(&told, 1))
        klog("lobby: Solo: session manager %08lx now has the private vtable %08lx (slot 3 = the error word filter)", (unsigned long)sm, (unsigned long)vt);
}

static void kllb_tick(void)
{
    static DWORD last, told_sm; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, h, v, lo, hi; BYTE cur = 0, want;
    if (!kllb_min || !klh_exe_ok || now - last < 200) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)))) return;
    if (kllb_solo && klh_rd32(sm) == 0xbd1ebc) kllb_install(sm);
    if (!KLH_SM_VT_OK(klh_rd32(sm))) return;
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
