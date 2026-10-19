/*
 * klnetfix.c - MULTIPLAYER, receiver side: an EXPERIMENT on the one receiver-side number that sits in writable memory
 * (the "hold time" of Net-Z's dead-reckoning policies), plus a read-only check of those policies. Part of KLHook
 * (to be included by klhook.c, after klnet.c; SHIP and TEST alike). re\netcode_receiver.md is the note.
 *
 * NOTHING HERE HAS RUN IN THE GAME. NOT WIRED (the three lines are at the end of this comment). EVERYTHING IS OFF
 * unless KLHook.ini has one of the keys below set to a number.
 *
 * WHAT THE EXE SHOWS (READ 2026-10-19, kl2.exe 0490; the note has the addresses):
 *   - Each extrapolated dataset has a 0x20-byte tolerance object (klnet.c) followed by a 0x18-byte POLICY, made by
 *     0x990de0 at start-up: +0 float 4.0, +4 float -1.0, +8 dword 1000, +0xc dword 250, +0x10 byte 1, +0x14 dword 3500.
 *     The policy of the player position is 0x168f460 (0x8df1c0 pushes it for 0x991510); of the actor position
 *     0x168f204 (0x5c1710). 0x991510 stores a new sample into a model and, when the model has no end time yet, gives
 *     it one: sample time + policy +0x14 (3500 ms). 0x9914c0 tests a time against the model's two end times; 0x992ab0
 *     then re-derives the extrapolation numbers through the state machine 0x991fd0 instead of using the stored ones.
 *   - WHAT THAT DOES TO A MODEL AT ITS END TIME IS A GUESS: hold the last value, or re-fit from the three int16 samples
 *     (which could be jumpier, not calmer). That is why this is an experiment and every key is off.
 *   Hashed ranges are not touched: the policies live at 0x168f204..0x168f5a8, .data/.bss (klranges.h: only
 *   0xb11000-0xb8ac00, 0xb8b000-0xbeb000 and 0xc7a000-0xccc000 are hashed).
 *
 * KLHook.ini
 *   [Net]
 *   HoldHeadingMs=0    0 = off.  500..3500: the end time of the player angle, camera angle and aim point models
 *   HoldPosMs=0        0 = off.  500..3500: the end time of the player position models (RISK: a runner who sends nothing)
 *   HoldActorHeadingMs=0  0 = off. 500..3500: the same for AI headings   (the host's AI, as seen by a client)
 *   HoldActorPosMs=0   0 = off.  500..3500: the same for AI positions
 *   HoldLog=0          1 = say the nine policies once per session (reads only; the check that the layout is as read)
 *   Applies only while this machine is SERVER or CLIENT of a game type 4 session, state 0x13..0x1f, NOT ranked
 *   (the service's ranked byte is 0), and only to a policy that still looks like the game made it. A value the game
 *   has changed itself is left alone; when the session ends or the gate closes the game's value goes back.
 *   It changes ONLY how this machine shows other people (GUESS for a host: its models are also the server's view, so
 *   the two position keys act on a CLIENT only). No packet differs. Set the keys BEFORE joining: models read it when made.
 *   A new value is read by a model when it is created: models already alive keep their old end time.
 *
 * WIRING (klhook.c; not done):
 *   #include "klnetfix.c"         below  #include "klnet.c"
 *   klnetfix_init();              below  klnet_init();
 *   klnetfix_tick(game_thread);   below  klnet_tick(game_thread);
 */
#ifndef KLNETFIX_C
#define KLNETFIX_C

#define KLNF_N 9

static const struct { const char *name; DWORD pol; int kind; } klnf_pol[KLNF_N] = {      /* kind: 0 position, 1 heading */
    { "actor position",  0x0168f204, 0 },     /* tolerance 0x168f1e4 + 0x20 (klnet.c); 0x5c1710 pushes it for 0x991510 */
    { "actor angle",     0x0168f264, 1 },     /* tolerance 0x168f244 + 0x20 */
    { "(unnamed) 2c4",   0x0168f2c4, -1 },
    { "(unnamed) 3a0",   0x0168f3a0, -1 },
    { "(unnamed) 400",   0x0168f400, -1 },
    { "player position", 0x0168f460, 0 },     /* tolerance 0x168f440 + 0x20; 0x8df1c0 pushes it for 0x991510 */
    { "player angle",    0x0168f4d0, 1 },     /* tolerance 0x168f4b0 + 0x20 */
    { "camera angle",    0x0168f530, 1 },     /* tolerance 0x168f510 + 0x20 */
    { "aim point",       0x0168f590, 1 },     /* tolerance 0x168f570 + 0x20 */
};

static struct { LONG head, pos, ahead, apos; int log, any; DWORD role; } klnf;
static struct { int have; DWORD stock[KLNF_N], ours[KLNF_N]; int wrote[KLNF_N]; int told; } klnf_t;

/* the policy as 0x990de0 makes it; the hold time may be the game's 3500 or ours */
static int klnf_shape(DWORD pol, DWORD *hold)
{
    BYTE b[0x18]; DWORD w[6];
    if (!klh_rd((DWORD_PTR)KLH_VA(pol), b, sizeof b)) return 0;
    memcpy(w, b, sizeof w);
    if (w[0] != 0x40800000u || w[1] != 0xbf800000u || w[2] != 1000 || w[3] != 250 || b[0x10] != 1) return 0;
    *hold = w[5];
    return w[5] >= 100 && w[5] <= 10000;
}

static LONG klnf_want(int kind, int actor)
{
    /* positions on the CLIENT only: the host's models also hold what the server believes (hits, loot reach) and
       relays to third parties (0x991510 is reached from ~40 replicated reads) - GUESS that a client's are display only */
    return kind == 1 ? (actor ? klnf.ahead : klnf.head) : kind == 0 && klnf.role == 3 ? (actor ? klnf.apos : klnf.pos) : 0;
}

static void klnf_apply(int act)
{
    int i, n = 0, bad = 0;
    for (i = 0; i < KLNF_N; i++) {
        DWORD cur = 0, want; LONG ms;
        if (!klnf_shape(klnf_pol[i].pol, &cur)) { if (klnf_pol[i].kind >= 0) bad++; continue; }
        if (klnf_t.wrote[i] && cur != klnf_t.ours[i]) { klnf_t.stock[i] = cur; klnf_t.wrote[i] = 0; }      /* the game wrote it again: that is the stock value now */
        if (!klnf_t.wrote[i]) klnf_t.stock[i] = cur;
        ms = klnf_pol[i].kind < 0 ? 0 : klnf_want(klnf_pol[i].kind, i < 2);
        want = (act && ms > 0) ? (DWORD)ms : klnf_t.stock[i];
        if (!act && !klnf_t.wrote[i]) continue;                                                     /* nothing of ours to put back */
        if (cur != want && (act ? 1 : cur == klnf_t.ours[i])) {
            if (klh_data((void *)KLH_VA(klnf_pol[i].pol + 0x14), &want, 4, "Net-Z dead-reckoning hold time")) {
                n++; klnf_t.wrote[i] = act && want != klnf_t.stock[i]; klnf_t.ours[i] = want;
            }
        }
    }
    klnf_t.have = 1;
    if (n) klog("netfix: %s %d hold time(s) (heading %ld ms, position %ld ms, AI heading %ld ms, AI position %ld ms; 0 = left alone; the game's value was %lu)%s",
                act ? "wrote" : "put back", n, klnf.head, klnf.pos, klnf.ahead, klnf.apos, klnf_t.stock[5], bad ? "; a policy not as read was left alone" : "");
}

static void klnetfix_tick(int game_thread)
{
    static DWORD last; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, svc; BYTE ranked = 1; int act, i;
    (void)game_thread;
    if ((!klnf.any && !klnf.log) || !klh_exe_ok || now - last < 250) return;
    last = now;
    act = 0;
    if ((sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4)) {
        svc = klh_rd32(sm + 0x17c);
        act = (role == 2 || role == 3) && mode == 4 && state >= 0x13 && state <= 0x1f && svc && klh_rd32(svc) == 0x00bd597c &&
              klh_rd(svc + 0x36f, &ranked, 1) && !ranked;                                       /* same service object and ranked byte as klnet.c */
        if (act && role == 2) {                                         /* a host's byte can be stale: also its ranked BIT, as klnet.c */
            BYTE props[0x20];
            if (!klh_rd(svc + 0x370, props, sizeof props) || ((props[8] >> 5) & 1)) act = 0;
        }
        klnf.role = role;
    }
    if (klnf.any && (act || klnf_t.have)) klnf_apply(klnf.any && act);
    if (klnf.log && act && !klnf_t.told) {
        char line[900]; int len = 0;
        for (i = 0; i < KLNF_N && len < 760; i++) {
            DWORD hold = 0; int ok = klnf_shape(klnf_pol[i].pol, &hold);
            len += snprintf(line + len, sizeof line - len, "%s%s %08lx hold %lu ms%s", i ? " | " : "", klnf_pol[i].name, klnf_pol[i].pol, hold, ok ? "" : " (NOT as read)");
        }
        klog("netfix: policies: %s", line);
        klnf_t.told = 1;
    }
    if (!act) klnf_t.told = 0;
}

static LONG klnf_key(const char *key)
{
    LONG v = (LONG)GetPrivateProfileIntA("Net", key, 0, klh_ini);
    if (v == 0) return 0;
    if (v < 500 || v > 3500) { klog("netfix: %s=%ld is outside 500..3500: left alone", key, v); return 0; }
    return v;
}

static void klnetfix_init(void)
{
    klnf.head = klnf_key("HoldHeadingMs"); klnf.pos = klnf_key("HoldPosMs");
    klnf.ahead = klnf_key("HoldActorHeadingMs"); klnf.apos = klnf_key("HoldActorPosMs");
    klnf.log = GetPrivateProfileIntA("Net", "HoldLog", 0, klh_ini) != 0;
    klnf.any = klnf.head > 0 || klnf.pos > 0 || klnf.ahead > 0 || klnf.apos > 0;
    if (klnf.any || klnf.log)
        klog("netfix: on; HoldHeadingMs=%ld HoldPosMs=%ld HoldActorHeadingMs=%ld HoldActorPosMs=%ld HoldLog=%d (0 = off); data writes only, online FA, not ranked; EXPERIMENT: what a model does at its end time is a GUESS",
             klnf.head, klnf.pos, klnf.ahead, klnf.apos, klnf.log);
}

#endif /* KLNETFIX_C */
