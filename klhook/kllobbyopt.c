/*
 * kllobbyopt.c - [Lobby] TimeMax / TimeMin / RoundsMax: more choices on the Fragile Alliance lobby rows "Heist time (minutes)" and
 * "Number of rounds". Part of KLHook (included by klhook.c after kllobby.c, SHIP and TEST alike); DATA writes only. 2026-10-25.
 *
 * WHAT THE EXE SHOWS (kl2.exe 0490, read statically 2026-10-25; re\lobby_options.md):
 *   The rows are NOT scene data: the lobby's ToggleText/Option lists do not exist for them. LobbyInfoTimeLimit / LobbyInfoNumberOfRounds
 *   are plain text slots filled by MercsShowInfoFALobby (tags LobbyTimeLimit 0x62bdb7, LobbyNumberOfRounds 0x62bd81: "%d", minutes =
 *   0x6d3130 / 60.0, rounds = 0x6a1a90), and the arrows send ZW_LEFT / ZW_RIGHT to the selector MercsFASelectorFALobby
 *   (ZMercsFASelectorLobby, vtable 0xbbd364, slot 10 = 0x7dc060, three stack args, ret 0xc; the first is the key: 0x7d left, 0x7e right).
 *   The CLAMPS ARE CODE IMMEDIATES in that function (CERTAIN, read from the instructions):
 *     focus row [self+0x88] = -2 Heist time:   LEFT 0x7dc3c7: new = cur-1, floor 3 (0x7dc412..); RIGHT 0x7dca25: new = cur+1, ceiling 5 (0x7dca71..)
 *     focus row [self+0x88] = -1 Rounds:       LEFT 0x7dc2bc: cur-1 floor 3 (Cops & Robbers [0x168e59c]==2: cur-2, floor 4); RIGHT 0x7dc918:
 *                                              cur+1 ceiling 5 (mode 2: cur+2, ceiling 6)
 *     focus row -3 = Number of players: floor 4 / ceiling 8 (mode 2: 6 / 12): left alone here.
 *   Where the value goes (CERTAIN): time: sm byte [sm+0x4b] (setter 0x6cff90, getter 0x6ff8f0), the game settings' replicated object
 *   (0x7bb2a0 -> vtbl+0xa4 takes the SECONDS as a float: minutes * 60.0, 0xb35e60), the menu store key MP_TimeLimit (0xb29c74, minutes),
 *   0x69dff0 on the menu data block, then 0x549e80 (Steam lobby data RoundTime / NumRounds). Rounds: the same object's vtbl+0x9c (a byte),
 *   0x5b5f30(sm, n), store key MP_NumberOfRounds (0xb68cc8, value n-1), 0x5de930. The replicated fields are m_fRoundTime (float) and
 *   m_iNumRounds (int8) (re\netcode.md), so 10 minutes and 10 rounds fit the wire type. The profile save (0x479960) keeps bytes. A client
 *   never validates these numbers in the lobby (no compare in the readers 0x62bd90 / 0x6325c4); the consumers of the round count compare
 *   'current round == rounds' (last round tests at 0x4fa1a9, 0x508d51, 0x50516f), no per-round table was found (GUESS: none exists).
 * WHAT IT DOES: the selector object (found by name every 300 ms, heap) gets a PRIVATE 36-slot vtable copy (the .rdata vtable is hashed and
 *   never written; the pattern of kllobby.c / klshoppage.c) whose slot 10 is ours. Everything passes to the stock function unchanged EXCEPT
 *   the key presses the stock clamps would swallow, host in the lobby (state 0xd, the same three gates the stock case has), game mode != 2:
 *     RIGHT on Heist time with cur >= 5 and cur < TimeMax, RIGHT on Rounds with cur >= 5 and cur < RoundsMax,
 *     LEFT  on Heist time with cur <= 3 and cur > TimeMin  (stock floor 3).
 *   There the stock function is called with the value first set to 4 (so the stock path - its writes, the Steam lobby update, its tail - runs
 *   exactly as for a press that changes the value) and then the four setters above are called again with the wanted value. The game's own
 *   setters and the stock handler do all the work. LEFT on Rounds already works from any value (cur-1, floor 3): not touched.
 *
 * KLHook.ini
 *   [Lobby]
 *   TimeMax=0       0 = stock (5). 6..20: the host can raise the Heist time to this many minutes.
 *   TimeMin=0       0 = stock (3). 1..2: the host can lower the Heist time to this many minutes.
 *   RoundsMax=0     0 = stock (5). 6..20: the host can raise the number of rounds to this many.
 *   PlayersMax=0    0 = stock (8). 9..12 (engine ceiling): the host can raise 'Number of players' to this many (RIGHT clamp 0x7dcb78 / 0x7dcb7d taken over).
 *                   A 9th heister has no seat in a stock level: [Lobby] ExtraSeats (TEST build) and reound_end_online.md.
 */
#ifndef KLLOBBYOPT_C
#define KLLOBBYOPT_C

static int kllo_tmax, kllo_tmin, kllo_rmax, kllo_pmax, kllo_clockfix;
static void klrk_init(void);                                         /* klroundkeep.c (included later) */
static void klrk_tick(void);
static DWORD kllo_vt[1 + 36];                                         /* [0] = RTTI locator, [1..36] = slots 0..35 of 0xbbd364 */
static DWORD (__fastcall *kllo_real10)(void *, void *, DWORD, DWORD, DWORD);
static LONG kllo_told, kllo_n;

typedef DWORD (__fastcall *kllo_f0)(void *self, void *edx);
typedef DWORD (__fastcall *kllo_f1)(void *self, void *edx, DWORD a);
typedef DWORD (__fastcall *kllo_f2)(void *self, void *edx, DWORD a, DWORD b);
typedef DWORD (__fastcall *kllo_f3)(void *self, void *edx, DWORD a, DWORD b, DWORD c);
typedef DWORD (__fastcall *kllo_ff)(void *self, void *edx, float a);

static void kllo_init(void)
{
    kllo_tmax = GetPrivateProfileIntA("Lobby", "TimeMax", 0, klh_ini);
    kllo_tmin = GetPrivateProfileIntA("Lobby", "TimeMin", 0, klh_ini);
    kllo_rmax = GetPrivateProfileIntA("Lobby", "RoundsMax", 0, klh_ini);
    kllo_pmax = GetPrivateProfileIntA("Lobby", "PlayersMax", 0, klh_ini);
    if (kllo_pmax < 9 || kllo_pmax > 12) kllo_pmax = 0;
    klrk_init();
    kllo_clockfix = GetPrivateProfileIntA("Lobby", "RoundClockFix", 0, klh_ini) != 0;
    if (kllo_clockfix) klog("lobbyopt: RoundClockFix=1 (GUESS): [rules+0x4c] is set to the lobby heist time at the round start when it holds less");
    if (kllo_tmax < 6 || kllo_tmax > 20) kllo_tmax = 0;
    if (kllo_tmin < 1 || kllo_tmin > 2) kllo_tmin = 0;
    if (kllo_rmax < 6 || kllo_rmax > 20) kllo_rmax = 0;
    if (kllo_pmax) klog("lobbyopt: Number of players up to %d (stock 8; engine ceiling 12). A 9th heister needs a seat: see [Lobby] ExtraSeats (TEST) in klroundkeep.c", kllo_pmax);
    if (kllo_tmax || kllo_tmin || kllo_rmax)
        klog("lobbyopt: Heist time %d..%d minutes, rounds 3..%d (0 = stock 3..5)", kllo_tmin ? kllo_tmin : 3, kllo_tmax ? kllo_tmax : 5, kllo_rmax ? kllo_rmax : 5);
}

/* the menu value store [[0xdd265c]+0x824]: Get(key, def) = vtbl+8, Set(key, value, 0) = vtbl+0x14 of the object that mgr->vtbl+0x14 returns */
static DWORD kllo_store(void)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), mgr = gd ? klh_rd32(gd + 0x824) : 0, vt, fn;
    if (!mgr || !(vt = klh_rd32(mgr)) || !(fn = klh_rd32(vt + 0x14))) return 0;
    return ((kllo_f0)(DWORD_PTR)fn)((void *)(DWORD_PTR)mgr, 0);
}

/* the real stores of the two values, each read its own way: time = [sm+0x4b] / so float / menu store; rounds = so byte / menu store */
typedef float (__fastcall *kllo_gf)(void *self, void *edx);
/* 2026-10-25 live SL7: vtbl+0x94 read NaN in every state = NOT a float getter (GUESS: it is the setter's neighbour with another signature); the read is dropped,
   time is proven by sm byte + menu store and, in TEST, by the measured span of the round (kllo_roundlog) */
static float kllo_fget(DWORD so) { (void)so; return -1.0f; }
static int kllo_sget(DWORD st, DWORD key)
{
    DWORD sv, fn;
    if (!st || !(sv = klh_rd32(st)) || !(fn = klh_rd32(sv + 8))) return -999;
    return (int)((kllo_f2)(DWORD_PTR)fn)((void *)(DWORD_PTR)st, 0, key, 0);
}
static int kllo_tsm(DWORD sm) { return (signed char)((kllo_f0)KLH_VA(0x6ff8f0))((void *)(DWORD_PTR)sm, 0); }
static int kllo_rso(DWORD so) { return (signed char)(BYTE)((kllo_f0)(DWORD_PTR)klh_rd32(klh_rd32(so) + 0xa0))((void *)(DWORD_PTR)so, 0); }

static void kllo_tset(DWORD sm, DWORD so, DWORD st, DWORD es, int n)
{
    ((kllo_f1)KLH_VA(0x6cff90))((void *)(DWORD_PTR)sm, 0, n);
    ((kllo_ff)(DWORD_PTR)klh_rd32(klh_rd32(so) + 0xa4))((void *)(DWORD_PTR)so, 0, (float)(n * 60.0));
    if (st) ((kllo_f3)(DWORD_PTR)klh_rd32(klh_rd32(st) + 0x14))((void *)(DWORD_PTR)st, 0, 0xb29c74, n, 0);
    if (es) ((kllo_f1)KLH_VA(0x69dff0))((void *)(DWORD_PTR)es, 0, n);
}
static void kllo_rset(DWORD sm, DWORD so, DWORD st, DWORD es, int n)
{
    ((kllo_f1)(DWORD_PTR)klh_rd32(klh_rd32(so) + 0x9c))((void *)(DWORD_PTR)so, 0, n);
    ((kllo_f1)KLH_VA(0x5b5f30))((void *)(DWORD_PTR)sm, 0, n);
    if (st) ((kllo_f3)(DWORD_PTR)klh_rd32(klh_rd32(st) + 0x14))((void *)(DWORD_PTR)st, 0, 0xb68cc8, n - 1, 0);
    if (es) ((kllo_f1)KLH_VA(0x5de930))((void *)(DWORD_PTR)es, 0, n);
}
/* players: the same setters the stock RIGHT case calls after its clamp (0x7dcb9e..0x7dcc02): b9 target 0x739f20, b8 max 0x6f7fb0(n, 0), 0x4b5fc0, store MP_NumberOfPlayers = n-1, 0x678d90 on the menu block */
static void kllo_pset(DWORD sm, DWORD st, DWORD es, int n)
{
    ((kllo_f1)KLH_VA(0x739f20))((void *)(DWORD_PTR)sm, 0, n);
    ((kllo_f2)KLH_VA(0x6f7fb0))((void *)(DWORD_PTR)sm, 0, n, 0);
    ((kllo_f0)KLH_VA(0x4b5fc0))((void *)(DWORD_PTR)sm, 0);
    if (st) ((kllo_f3)(DWORD_PTR)klh_rd32(klh_rd32(st) + 0x14))((void *)(DWORD_PTR)st, 0, 0xb56714, n - 1, 0);
    if (es) ((kllo_f1)KLH_VA(0x678d90))((void *)(DWORD_PTR)es, 0, n);
}
/* every real store of time + rounds on one log line (first 120 calls) */
static void kllo_state(const char *what, DWORD sm, DWORD so, DWORD st)
{
    static LONG n;
    if (InterlockedIncrement(&n) <= 120)
        klog("lobbyopt: %s: TIME sm=%d store=%d | ROUNDS so=%d store=%d", what, kllo_tsm(sm), kllo_sget(st, 0xb29c74), kllo_rso(so), kllo_sget(st, 0xb68cc8) + 1);
}

static DWORD __fastcall kllo_slot10(void *self, void *edx, DWORD a, DWORD b, DWORD c)
{
    int focus, tmode = 0, pmode = 0, cur = 0, want = 0, pre = 0, t0, r0; DWORD sm, st, so, mode = 0, sv, fn, es, g; float f0;
    if ((a != 0x7d && a != 0x7e) || !(kllo_tmax || kllo_tmin || kllo_rmax || kllo_pmax)) goto stock;
    if (!klh_rd((DWORD_PTR)self + 0x88, &focus, 4) || (focus != -2 && focus != -1 && !(focus == -3 && kllo_pmax))) goto stock;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd((DWORD_PTR)KLH_VA(0x168e59c), &mode, 4) || mode == 2) goto stock;
    if (klh_rd32(sm) != 0xbd1ebc && !KLH_SM_VT_OK(klh_rd32(sm))) goto stock;
    /* the stock case's own gates: 0x8df480(sm) true, 0x8e6a20(sm) == 0xd, store.Get(0xb41ea0) != 0 */
    if (!(BYTE)((kllo_f0)KLH_VA(0x8df480))((void *)(DWORD_PTR)sm, 0)) goto stock;
    if (((kllo_f0)KLH_VA(0x8e6a20))((void *)(DWORD_PTR)sm, 0) != 0xd) goto stock;
    if (!(st = kllo_store()) || !(sv = klh_rd32(st)) || !(fn = klh_rd32(sv + 8))) goto stock;
    if (!((kllo_f2)(DWORD_PTR)fn)((void *)(DWORD_PTR)st, 0, 0xb41ea0, 0)) goto stock;
    if (!(so = ((kllo_f0)KLH_VA(0x7bb2a0))((void *)(DWORD_PTR)klh_rd32((DWORD_PTR)KLH_VA(0x168e9e4)), 0))) goto stock;    /* the settings' replicated object */
    tmode = focus == -2; pmode = focus == -3;
    /* the value of the row NOT pressed, before the press: the press must leave it alone (live SL6: time read 5 after the rounds presses) */
    t0 = kllo_tsm(sm); f0 = kllo_fget(so); r0 = kllo_rso(so);
    cur = pmode ? (signed char)((kllo_f0)KLH_VA(0x54d140))((void *)(DWORD_PTR)sm, 0) : tmode ? t0 : r0;     /* players: [sm+0xb9] */
    if (pmode) {
        /* players RIGHT: stock ceiling 8 (0x7dcb78 / 0x7dcb7d). Same take-over as time / rounds: at 8 and above, cur+1 up to PlayersMax, cur at the max */
        if (a == 0x7e && cur >= 8) { want = cur < kllo_pmax ? cur + 1 : cur; pre = 4; }
    } else if (a == 0x7e) {
        int mx = tmode ? kllo_tmax : kllo_rmax;
        /* live SL7: at the max one more press let the stock clamp reset the value to 5. Above the stock range the press is ALWAYS taken over:
           cur+1 below the max, cur itself at the max (re-applied after the stock call) */
        if (mx && cur >= 5) { want = cur < mx ? cur + 1 : cur; pre = 4; }
    } else if (tmode && kllo_tmin && cur <= 3) { want = cur > kllo_tmin ? cur - 1 : cur; pre = 4; }
    kllo_state("before press", sm, so, st);
    if (want) {
        /* 1. lower the stored value so the stock handler's own clamp lets the press through (it then writes cur+1 / cur-1 itself) */
        if (pmode) { ((kllo_f1)KLH_VA(0x739f20))((void *)(DWORD_PTR)sm, 0, pre); ((kllo_f2)KLH_VA(0x6f7fb0))((void *)(DWORD_PTR)sm, 0, pre, 0); }
        else if (tmode) ((kllo_f1)KLH_VA(0x6cff90))((void *)(DWORD_PTR)sm, 0, pre);
        else ((kllo_f1)(DWORD_PTR)klh_rd32(klh_rd32(so) + 0x9c))((void *)(DWORD_PTR)so, 0, pre);
    }
    g = kllo_real10(self, edx, a, b, c);
    es = ((kllo_f0)(DWORD_PTR)klh_rd32(klh_rd32(sm) + 0x2c))((void *)(DWORD_PTR)sm, 0);
    if (es) es = ((kllo_f0)(DWORD_PTR)klh_rd32(klh_rd32(es) + 0x140))((void *)(DWORD_PTR)es, 0);
    st = kllo_store();
    kllo_state("after stock", sm, so, st);
    /* 2. the wanted value, through the same setters the stock path calls */
    if (want) {
        if (!es) klog("lobbyopt: no menu data block, %s left at the stock value", tmode ? "time" : "rounds");
        else if (pmode) kllo_pset(sm, st, es, want);
        else if (tmode) kllo_tset(sm, so, st, es, want); else kllo_rset(sm, so, st, es, want);
        if (InterlockedIncrement(&kllo_n) <= 60) klog("lobbyopt: %s %d -> %d (the stock clamp would have kept %d)", pmode ? "Number of players" : tmode ? "Heist time" : "Number of rounds", cur, want, pmode ? 8 : a == 0x7e ? 5 : 3);
    }
    /* 3. the row NOT pressed must still hold what it held before; if any of its stores moved, put them all back. GUESS at the live-SL6 cause:
          the stock rounds path or the replication resyncs the time from a stale copy; the line below names the store that moved. */
    if (pmode) {
        /* the players row leaves time and rounds alone: nothing to restore */
    } else if (es && tmode) {
        if (kllo_rso(so) != r0 || kllo_sget(st, 0xb68cc8) + 1 != r0) {
            klog("lobbyopt: ROUNDS moved by a time press (was %d; now so=%d store=%d): restored", r0, kllo_rso(so), kllo_sget(st, 0xb68cc8) + 1);
            kllo_rset(sm, so, st, es, r0);
        }
    } else if (es) {
        if (kllo_tsm(sm) != t0 || kllo_sget(st, 0xb29c74) != t0) {
            klog("lobbyopt: TIME moved by a rounds press (was %d min; now sm=%d store=%d): restored", t0, kllo_tsm(sm), kllo_sget(st, 0xb29c74));
            kllo_tset(sm, so, st, es, t0);
        }
    }
    if (es) { BYTE one = 1; klh_data((BYTE *)(DWORD_PTR)es + 0xa, &one, 1, "lobby options: menu block dirty flag"); }
    ((kllo_f0)KLH_VA(0x549e80))((void *)(DWORD_PTR)sm, 0);
    kllo_state("final", sm, so, st);
    return g;
stock:
    return kllo_real10(self, edx, a, b, c);
}

/* ---- the round clock (live SL7/SL9: a 10-minute setting gave rounds of 83 s / 83 s / 40 s between state 25 and 31) ----
 * hud_values.md: time left = float [rules+0x4c], played = [rules+0x50], END timer [rules+0x200] (600.0 at the reset), round length [score+0x3c] =
 * 0x6d3130() (the constant 360.0 in Arcade; where an online round gets it is NOT READ - GUESS: not from [sm+0x4b]). rules = [[0x168e9e4]+0x54],
 * score = [rules+0x5f8] (klbot.c). klo_clock_line() logs all of it (TEST: at the round start, every 10 s and at the end).
 * [Lobby] RoundClockFix=1 (default 0, GUESS, off until the log shows [rules+0x4c] is the clock): once per round, in the first 5 s of state 0x19,
 * if [rules+0x4c] holds less than the lobby's heist time, it is set to minutes * 60 (data write). */
static DWORD kllo_rules(DWORD *score)
{
    DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(0x168e9e4)), r = gs ? klh_rd32(gs + 0x54) : 0;
    *score = r ? klh_rd32(r + 0x5f8) : 0;
    return r;
}
static float kllo_rf(DWORD a) { float f = -1.0f; if (a) klh_rd(a, &f, 4); return f; }
static void kllo_clock_line(const char *what, DWORD sm)
{
    DWORD sc, r = kllo_rules(&sc);
    klog("lobbyopt: round clock %s: rules %08lx left[+4c]=%.1f played[+50]=%.1f endtimer[+200]=%.1f | score %08lx len[+3c]=%.1f cut[+40]=%.1f m[+44]=%d | lobby heist time sm=%d min",
         what, (unsigned long)r, kllo_rf(r ? r + 0x4c : 0), kllo_rf(r ? r + 0x50 : 0), kllo_rf(r ? r + 0x200 : 0), (unsigned long)sc,
         kllo_rf(sc ? sc + 0x3c : 0), kllo_rf(sc ? sc + 0x40 : 0), sc ? (int)(signed char)klh_rd32(sc + 0x44) : -1, kllo_tsm(sm));
}
static void kllo_clock_tick(int stt, DWORD sm)
{
    static DWORD t25, lastlog; static int did, fixed; DWORD now = GetTickCount(), sc, r; float left, want;
    if (stt != 25) { t25 = 0; did = 0; fixed = 0; return; }
    if (!t25) { t25 = now ? now : 1; did = 0; fixed = 0; }
#ifdef KLHOOK_TEST
    if (!did && now - t25 >= 1500) { did = 1; kllo_clock_line("1.5 s into the round", sm); lastlog = now; }
    if (did && now - lastlog >= 10000) { lastlog = now; kllo_clock_line("running", sm); }
#endif
    if (kllo_clockfix && !fixed && now - t25 >= 1000 && now - t25 < 5000 && (r = kllo_rules(&sc)) != 0) {
        want = (float)(kllo_tsm(sm) * 60); left = kllo_rf(r + 0x4c); fixed = 1;
        if (left > 0.0f && left < want - 5.0f && klh_data((void *)(DWORD_PTR)(r + 0x4c), &want, 4, "lobby options: round clock [rules+0x4c]"))
            klog("lobbyopt: RoundClockFix: [rules+0x4c] %.1f -> %.1f s (lobby heist time %d min)", left, want, kllo_tsm(sm));
    }
}

static void kllo_clockpoll(void)
{   /* SHIP and TEST: the state poll behind kllo_clock_tick (TEST: the clock log lines; [Lobby] RoundClockFix: the write) */
    static DWORD last; DWORD now = GetTickCount(), sm;
#ifndef KLHOOK_TEST
    if (!kllo_clockfix) return;
#endif
    if (now - last < 250 || !klh_exe_ok) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || (klh_rd32(sm) != 0xbd1ebc && !KLH_SM_VT_OK(klh_rd32(sm)))) return;
    kllo_clock_tick((int)((kllo_f0)KLH_VA(0x8e6a20))((void *)(DWORD_PTR)sm, 0), sm);
}

#ifdef KLHOOK_TEST
/* TEST: the replicated m_fRoundTime (seconds, so vtbl+0x94) at every session state change; leaving the lobby state 0xd = the round starting */
static void kllo_roundlog(void)
{
    static DWORD last, t25; static int ls = -1; DWORD now = GetTickCount(), sm, so, holder; int stt;
    if (now - last < 250) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || (klh_rd32(sm) != 0xbd1ebc && !KLH_SM_VT_OK(klh_rd32(sm)))) return;
    stt = (int)((kllo_f0)KLH_VA(0x8e6a20))((void *)(DWORD_PTR)sm, 0);
    if (stt == ls) return;
    if (stt == 25 || stt == 31) kllo_clock_line(stt == 25 ? "at state 25" : "at state 31 (round over)", sm);
    holder = klh_rd32((DWORD_PTR)KLH_VA(0x168e9e4));
    so = holder ? ((kllo_f0)KLH_VA(0x7bb2a0))((void *)(DWORD_PTR)holder, 0) : 0;
    klog("lobbyopt-test: session state %d -> %d: time sm=%d min, rounds so=%d", ls, stt, kllo_tsm(sm), so ? kllo_rso(so) : -1);
    if (stt == 25) t25 = now ? now : 1;
    if (stt == 31 && t25) { klog("lobbyopt-test: ROUND LENGTH: state 25 -> 31 took %.1f s (set heist time %d min = %d s; polled every 250 ms)", (now - t25) / 1000.0, kllo_tsm(sm), kllo_tsm(sm) * 60); t25 = 0; }
    ls = stt;
}
#endif

/* find the lobby selector by name and give it the private vtable (the old one is the .rdata original, never written) */
static void kllo_tick(void)
{
    static DWORD last; DWORD now = GetTickCount(), gd, mgr, e, vt, nv;
#ifdef KLHOOK_TEST
    kllo_roundlog();
#endif
    kllo_clockpoll();
    klrk_tick();
    if (!(kllo_tmax || kllo_tmin || kllo_rmax || kllo_pmax) || !klh_exe_ok || now - last < 300) return;
    last = now;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != (DWORD)(DWORD_PTR)KLH_VA(0xbb7dc8)) return;
    if (!(e = (DWORD)(DWORD_PTR)((void *(__fastcall *)(void *, void *, const char *))KLH_VA(0x83faf0))((void *)(DWORD_PTR)mgr, 0, "MercsFASelectorFALobby"))) return;
    vt = klh_rd32(e);
    if (!kllo_vt[0]) {
        if (vt != (DWORD)(DWORD_PTR)KLH_VA(0xbbd364)) { if (!InterlockedExchange(&kllo_told, 1)) klog("lobbyopt: the lobby selector has vtable %08lx, not the known one: left alone", (unsigned long)vt); return; }
        if (!klh_rd((DWORD_PTR)KLH_VA(0xbbd364 - 4), kllo_vt, sizeof kllo_vt)) return;
        if (kllo_vt[1 + 10] != (DWORD)(DWORD_PTR)KLH_VA(0x7dc060)) { if (!InterlockedExchange(&kllo_told, 1)) klog("lobbyopt: slot 10 is %08lx, not 0x7dc060: left alone", (unsigned long)kllo_vt[1 + 10]); kllo_vt[0] = 0; return; }
        kllo_real10 = (DWORD (__fastcall *)(void *, void *, DWORD, DWORD, DWORD))(DWORD_PTR)kllo_vt[1 + 10];
        kllo_vt[1 + 10] = (DWORD)(DWORD_PTR)kllo_slot10;
    }
    nv = (DWORD)(DWORD_PTR)&kllo_vt[1];
    if (vt == nv) return;
    if (vt != (DWORD)(DWORD_PTR)KLH_VA(0xbbd364)) return;
    if (klh_data((void *)(DWORD_PTR)e, &nv, 4, "lobby options: selector vtable (private copy)")) klog("lobbyopt: lobby selector %08lx wrapped (slot 10)", (unsigned long)e);
}

#endif
