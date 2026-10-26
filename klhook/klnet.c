/*
 * klnet.c - MULTIPLAYER, first piece: a LOG of what a network session is (who hosts, which rules class runs, which
 * level index the peers were given, what kind of Steam lobby the game made, the twelve update numbers of Net-Z's
 * extrapolation filter), and - behind a key of its own - a TUNE of those update numbers, the data side of 'less
 * spin botty'. Part of KLHook (to be included by klhook.c; SHIP and TEST alike). re\netcode_fa.md is the note this
 * file belongs to; re\netcode.md has the first reading of the netcode.
 *
 * NOTHING HERE HAS RUN IN THE GAME. NOT WIRED (klhook.c does not include it yet - the three lines are at the end of
 * this comment). Everything is OFF unless KLHook.ini has [Net] Log=1 or Tune=1.
 *
 * WHAT IT IS NOT: it starts nothing, joins nothing, makes no lobby, calls no Steam interface and no game routine,
 * patches no code, and has nothing to do with the level redirect (klslot.c). The lobby fingerprint and the redirect
 * from lobby data of re\netcode_fa.md 2 are a DESIGN, not in this file.
 *
 * 1. THE LOG ([Net] Log=1; reads only, any thread)
 *    sm = [0x168e598], the session manager (ZSessionManagerMultiplayer, vtable 0xbd1ebc). EXE, read 2026-10-11:
 *      [sm+0x54]  the net role. 0x7f6850 / 0x863a60 jump on it: 0 and 1 = a local session (Arcade, story),
 *                 2 = this machine is the SERVER, 3 = a CLIENT (0x4b0a40: `cmp [ecx+0x54],3`).
 *      [sm+0x5c]  the game type: 4 = the Fragile Alliance family - Arcade AND online FA / Undercover Cop / Cops &
 *                 Robbers (0x6c9ec4 `push 4 ; call 0x5be510` in the online create 0x6c9c10; the multiplayer state
 *                 machine 0x6c49a0 tests it nine times). So '+0x5c == 4' alone is NOT 'Arcade' (re\netcode_fa.md 3).
 *      [sm+0x70]  the session state (0x8e6a20). 0x12 = the level is being loaded (EXE for a network host too: the
 *                 load path 0x6c5300..0x6c53db ends in it), 0x19 = the round runs, 0x1f = the score page - the last
 *                 two are ARCADE knowledge; that an online session uses the same numbers, and whether it leaves
 *                 0x13..0x1f between two rounds, is ASSUMED (live check N3 lists the 'net: state' lines for it).
 *      [sm+4]     the session handler: ZSessionHandlerSP 0xbd1be4 (Arcade), ...Server 0xbd27bc, ...Client 0xbd262c.
 *      [sm+8]     the map name the session will load, 0x40 bytes (0x4e7da0).
 *      [sm+0xbf]  the level index (a SLOT index 0..8 = F01..F09) the host chose (0x6c9ca0); [sm+0xbe] the index a
 *                 client was given (the 'missing content pack' test 0x6c4bcd); [sm+0xb9] / [sm+0xb8] min / max players.
 *      [sm+0x84]  D = the replicated server object (DDL_ZServer), 0 until it exists. Its reliable scalars keep the
 *                 value in the byte at +4 of the dataset, XORed: level index = byte [D+0x1b0] ^ 0xac (0x467ae0 ->
 *                 0x5b1400), second index = byte [D+0x190] ^ 0xac (0x8dc7f0), game type = byte [D+0x110] ^ 0xdc
 *                 (0x83f980 -> 0x532840); strings are a char * at +4: map name [D+0x234] (0x4468a0), and [D+0x254]
 *                 (0x57b2d0; ASSUMED m_szVersion - its only caller, ZSessionHandlerClient slot 97 at 0x53919c, throws
 *                 the result away: no version is compared there).
 *                 BOTH SIDES TURN THE INDEX INTO A SCENE NAME THROUGH THEIR OWN LEVEL LIST ([0x168f750] slot 15):
 *                 the host at 0x6c536f, a client at 0x491fd1. The name itself only travels with `-o MPMap`.
 *      [sm+0x17c] S = the online service (0x5c9dd0 is the getter), ZOnlineServiceSteam 0xbd597c. From its
 *                 CreateSession 0x8e4fe0: [S+0x35c] byte 'a session exists', [S+0x370..+0x390) a copy of the session
 *                 properties (dword +0 = which fields are set, byte +5 = max players, word +8: bit 4 = PRIVATE,
 *                 set from the menu option MP_PrivateGame == 1 by 0x518b50; bit 5 = RANKED, set from MP_RankedGame == 0
 *                 by 0x810df0; a session that is both loses the private bit, 0x6c9df8), [S+0x36f] byte ranked,
 *                 [S+0x35e] 8 bytes = the lobby id (the create task writes it through the pointer 0x8e5143 hands it),
 *                 [S+0x390] the own Steam id.
 *                 A CLIENT (JoinSession 0x6d8640, slot 45 of the service; found by the review, re-read): it writes
 *                 [S+0x35c] = 1, the lobby id [S+0x35e] / [S+0x362] from the search result +0x6d / +0x71 (0x6d8739,
 *                 0x6d8746) and the ranked byte [S+0x36f] from its second argument (0x6d874c; who passes it was looked
 *                 for and NOT found - no call through slot +0xb4 near the service getter) - and NOT the property
 *                 block S+0x370. So on a client the private / ranked BITS are whatever the last CreateSession on
 *                 that machine left, or zeros: this file does not use them on a client, and A CLIENT CANNOT TELL
 *                 FROM MEMORY WHETHER THE LOBBY IT JOINED IS PRIVATE.
 *                 The lobby type the game asks Steam for (0x8e514b..0x8e5174): ranked -> 3 (invisible), else
 *                 private -> 1 (friends only), else 2 (public).
 *      rules = [[0x168e9e4]+0x54]: ZGameRulesHeist 0xbd3514 (Arcade), ZGameRulesFragileAllianceSv 0xbd2eb4 (host),
 *              ...Cl 0xbd31e4 (client). The three are siblings (RTTI) and share 62 / 66 of 203 vtable slots: NONE of the
 *              offsets the Arcade parts of this hook use (crew records, vehicle state, hero table) may be used on
 *              the other two.
 *      [0x168e59c] the FA sub-mode: 0 Fragile Alliance, 1 Undercover Cop, 2 Cops & Robbers.
 *    Lines (said when what they show changes; nothing at all while the session is local unless Log=2):
 *      net: session: SERVER, game type 4 (FA family, sub-mode 0), state 0x12; handler ZSessionHandlerServer; rules
 *           ZGameRulesFragileAllianceSv; players 2..8; level index 2 (F03), map 'Locations/F03/F03_Main'
 *      net: server object 1a2b3c00: level index 2 (F03), second index 2, game type 4, map '', text at +0x250 ''
 *      net: lobby 0186000001234567 (service 0a1b2c00): PRIVATE (friends only, type 1) - private bit 1, ranked bit 0,
 *           ranked byte 0, max players 8                                               (a host)
 *      net: lobby 0186000001234567 (service 0a1b2c00, session byte 1): JOINED - ranked byte 0; kind not known on a
 *           client                                                                       (a client)
 *    When a network session ends (the role is local again) everything said is forgotten, so the next session of
 *    the same process says all its lines again, also when it is the same in every field.
 *      net: state 0x12 -> 0x16
 *      net: level SCENES\Locations\F03\F03_Main.gms: NOT stock (<why>)
 *      net: update numbers (B = 100): actor position min 100 max 2000 tolerance 30.0 | actor angle ... | player
 *           position min 100 max 2000 tolerance 20.0 | player angle min 100 max 2000 tolerance 30.0 | camera angle
 *           min 200 ... 40.0 | aim point min 150 ... 5.0
 *
 * 2. THE TUNE ([Net] Tune=1 and at least one number; DATA writes into kl2.exe's .data, no hashed range)
 *    What the numbers are (re\netcode.md 8.2, re-read 2026-10-11): each extrapolated dataset has
 *      - a 'min' interval in ms (dword): no update to a station sooner than this after the last one (0x902e80:
 *        `cmp [0xd35424],0 ; jle` = 0 or less switches the test off). Stock: 150 in the file, overwritten at every
 *        Net-Z start by 0x4825b0 with B = [sm+0x158] = 100 (constructor 0x8c4b5b) - camera angle 2 x B, aim 1.5 x B;
 *      - a 'max' interval in ms (dword): an update is forced after this long (0x861430). Stock 2000, never rewritten;
 *      - a tolerance object: float [+0] = the allowed error SQUARED (0x990e40; +4 / +8 / +0xc / +0x10 are the
 *        coefficients of a polynomial in the distance, all 0 in this game, dword [+0x18] its degree, 0, and float
 *        [+0x1c] = -1.0: 0x990f00(tol) = 0x990e40(tol, 0, 0, -1.0)), set at
 *        every Net-Z start by 0x4825b0 through 0x990f00: actor position 30, actor angle 30, player position 20,
 *        player angle 30 (30 / 1024 of a turn = 10.5 degrees), camera angle 40, aim point 5.
 *        0x4825b0's one caller is 0x7ee35d in the Net-Z start 0x7ee0c0, which slot 1 of BOTH handlers calls with
 *        ecx = sm (server 0x66a820 at 0x66a854, client 0x5f6690 at 0x5f66a3; 0x7ee0c0 is not itself a slot).
 *      dataset            tolerance   max        min
 *      actor position     0x168f1e4   0xd34664   0xd34668
 *      actor angle        0x168f244   0xd34684   0xd34688
 *      player position    0x168f440   0xd35420   0xd35424
 *      player angle       0x168f4b0   0xd35458   0xd3545c
 *      camera angle       0x168f510   0xd35478   0xd3547c
 *      aim point          0x168f570   0xd35498   0xd3549c
 *    ONLY THE SENDER'S NUMBERS COUNT: a player's own machine decides when his position and heading go out, the
 *    host's when an AI's do. So every peer needs the same hook and keys, and a tuned player looks better to the
 *    others whether or not they are tuned.
 *    What the keys do: PlayerMs = min of player position and angle (camera 2 x, aim 1.5 x, the stock ratios);
 *    RefreshMs = max of the four player datasets (the upper bound of how long a remote copy can keep turning on
 *    a lost 'stopped turning' packet: stock 2 s); PosTol / AngTol = player position / angle tolerance; ActorMs,
 *    ActorRefreshMs, ActorPosTol, ActorAngTol the same for AI (the host's machine). -1 = that number is left alone.
 *    A FIRST TRY (re\netcode_fa.md 4): PlayerMs=50 RefreshMs=300 AngTol=12, the rest -1.
 *    WHEN (all of it, else nothing is written and what was written goes back):
 *      - Tune=1 and a number;
 *      - this machine is SERVER or CLIENT of a game type 4 session;
 *      - the session state is 0x13..0x1f: AFTER the load state 0x12, so that the level's archive has been opened
 *        again and klsteam's verdict is this level's, not the one before (the window itself is ASSUMED online, see
 *        [sm+0x70]: if online states lie outside it the tune never acts - it fails shut);
 *      - the scene the engine names is the slot of THIS session's level index (the replicated server object's, on
 *        a host without one yet [sm+0xbf]): 'Locations\F03\F03_Main' for index 2. With `-o MPMap` the scene is
 *        not named by the index and the tune does not act;
 *      - that level is NOT the stock one of its slot (klsteam.c's verdict 2 - the gate every part of this hook has);
 *      - HOST: the service's ranked byte and ranked bit are 0 and its PRIVATE bit is 1 - the game itself made a
 *        friends-only lobby. Proved from memory;
 *      - CLIENT: the ranked byte is 0 (it rests on JoinSession's second argument, whose caller was not found) AND
 *        the ini has TuneClient=1. A client cannot see the lobby's kind (above), so on a client the 'private
 *        lobbies only' rule RESTS ON THE PLAYER'S WORD: TuneClient=1 means 'I only join friends-only lobbies, by
 *        invitation, while this line stands'. Without it a client writes nothing, ever. (A lobby datum set by a
 *        hooked host - re\netcode_fa.md 2.4, not built - is what would replace the word.)
 *    A number that no longer holds what the hook wrote is left at the put-back: the game has set it again.
 *    Before a write the memory must look as this file expects (a min of 1..1000, a max of 100..10000, a
 *    tolerance object of degree 0 with only its first float set): a number that does not is left alone and said.
 *    COST AND RISK: more packets up (stock: at most 10 position + 10 heading updates a second to each peer;
 *    PlayerMs=50 doubles that; with eight players a sender feeds seven peers). Net-Z's own throttling under load was
 *    NOT read. Nothing here can make a peer's game fail a check: the numbers are not replicated and no peer
 *    compares them. It does NOT cure the cause of a spin (the receiver extrapolates linearly from two samples
 *    without a cap, 0x992f10, and the correction is an unreliable packet): it shortens it. A cure needs code.
 *
 * KLHook.ini
 *   [Net]
 *   Log=0            1 = the lines of section 1 for a network session; 2 = also for local sessions (Arcade)
 *   Tune=0           1 = the numbers below may be written (see WHEN)
 *   TuneClient=0     1 = also when this machine has JOINED: the player's word that the lobby is friends-only
 *   PlayerMs=-1      16..500     RefreshMs=-1       100..5000 (and over the min)
 *   PosTol=-1        1..100      AngTol=-1          1..100
 *   ActorMs=-1       16..500     ActorRefreshMs=-1  100..5000
 *   ActorPosTol=-1   1..100      ActorAngTol=-1     1..100
 *
 * WIRING (klhook.c; not done):
 *   #include "klnet.c"            below  #include "klvis.c"
 *   klnet_init();                 below  klvis_init();
 *   klnet_tick(game_thread);      below  klvis_tick();
 */
#ifndef KLNET_C
#define KLNET_C

#define KLNET_SESSION   0x0168e598
#define KLNET_SETTINGS  0x0168e9e4            /* +0x54 = the rules object */
#define KLNET_SUBMODE   0x0168e59c
#define KLNET_SVC_VT    0x00bd597c            /* ZOnlineServiceSteam */
#define KLNET_NDS       6

static int klx_level_verdict_raw(const char *scene, char *why);      /* klsteam.c: 0 no level, 1 stock, 2 not stock, 3 not known; why[200]. The RAW one:
                                                                        [KLHook] AllMaps (Arcade only) never reaches a network session */

static const struct { const char *name; DWORD tol, max, min; int actor; int mul2; } klnet_ds[KLNET_NDS] = {
    { "actor position",  0x0168f1e4, 0x00d34664, 0x00d34668, 1, 2 },
    { "actor angle",     0x0168f244, 0x00d34684, 0x00d34688, 1, 2 },
    { "player position", 0x0168f440, 0x00d35420, 0x00d35424, 0, 2 },
    { "player angle",    0x0168f4b0, 0x00d35458, 0x00d3545c, 0, 2 },
    { "camera angle",    0x0168f510, 0x00d35478, 0x00d3547c, 0, 4 },         /* min = 2 x the player's */
    { "aim point",       0x0168f570, 0x00d35498, 0x00d3549c, 0, 3 },         /* min = 1.5 x */
};

static struct {
    int log, tune, tune_client, any;
    LONG player_ms, refresh_ms, actor_ms, actor_refresh_ms;
    float pos_tol, ang_tol, actor_pos_tol, actor_ang_tol;
} klnet;

struct klnet_num { DWORD min, max; float tol2; int ok; };
static struct { int have; struct klnet_num stock[KLNET_NDS], ours[KLNET_NDS]; int wrote[KLNET_NDS]; } klnet_t;

static const char *klnet_vt_name(DWORD vt)
{
    switch (vt) {
    case 0x00bd1be4: return "ZSessionHandlerSP";
    case 0x00bd248c: return "ZSessionHandlerMP";
    case 0x00bd262c: return "ZSessionHandlerClient";
    case 0x00bd27bc: return "ZSessionHandlerServer";
    case 0x00bd3514: return "ZGameRulesHeist";
    case 0x00bd2eb4: return "ZGameRulesFragileAllianceSv";
    case 0x00bd31e4: return "ZGameRulesFragileAllianceCl";
    case 0: return "none";
    }
    if (vt && vt == klh_rules_vt2) return "ZGameRulesFragileAllianceSv";
    if (vt && vt == klh_rules_vt3) return "ZGameRulesFragileAllianceCl";
    return "another class";
}

static const char *klnet_role_name(DWORD role) { return role == 2 ? "SERVER" : role == 3 ? "CLIENT" : role < 2 ? "local" : "?"; }

static void klnet_slot_name(int idx, char out[8]) { if (idx >= 0 && idx < 9) snprintf(out, 8, "F%02d", idx + 1); else strcpy(out, "none"); }

/* the twelve numbers as they stand; ok = the memory looks like what section 2 describes */
static void klnet_read_nums(struct klnet_num n[KLNET_NDS])
{
    int i; float c[5]; DWORD deg = 1;
    for (i = 0; i < KLNET_NDS; i++) {
        memset(&n[i], 0, sizeof n[i]);
        if (!klh_rd((DWORD_PTR)KLH_VA(klnet_ds[i].min), &n[i].min, 4) || !klh_rd((DWORD_PTR)KLH_VA(klnet_ds[i].max), &n[i].max, 4)) continue;
        if (!klh_rd((DWORD_PTR)KLH_VA(klnet_ds[i].tol), c, sizeof c) || !klh_rd((DWORD_PTR)KLH_VA(klnet_ds[i].tol + 0x18), &deg, 4)) continue;
        n[i].tol2 = c[0];
        n[i].ok = n[i].min >= 1 && n[i].min <= 1000 && n[i].max >= 100 && n[i].max <= 10000 &&
                  c[0] == c[0] && c[0] > 0.0f && c[0] <= 10000.0f && c[1] == 0.0f && c[2] == 0.0f && c[3] == 0.0f && c[4] == 0.0f && deg == 0;
    }
}

static float klnet_sqrt(float v) { float x = v > 1.0f ? v * 0.5f : 1.0f; int i; if (!(v > 0.0f)) return 0.0f; for (i = 0; i < 24; i++) x = 0.5f * (x + v / x); return x; }

static void klnet_log_nums(const struct klnet_num n[KLNET_NDS], DWORD b, const char *what)
{
    char line[700]; int i, len = 0;
    for (i = 0; i < KLNET_NDS && len < (int)sizeof line - 110; i++)
        len += snprintf(line + len, sizeof line - len, "%s%s min %lu max %lu tolerance %.1f%s", i ? " | " : "", klnet_ds[i].name, n[i].min, n[i].max, klnet_sqrt(n[i].tol2), n[i].ok ? "" : " (NOT as expected)");
    klog("net: update numbers, %s (B = %lu; ms; a tolerance is in world units / 1024ths of a turn): %s", what, b, line);
}

/* what the keys ask of dataset i, given what stands there; -> 1 when something differs */
static int klnet_want(int i, const struct klnet_num *cur, struct klnet_num *want)
{
    LONG ms = klnet_ds[i].actor ? klnet.actor_ms : klnet.player_ms, rf = klnet_ds[i].actor ? klnet.actor_refresh_ms : klnet.refresh_ms;
    float tol = i == 0 ? klnet.actor_pos_tol : i == 1 ? klnet.actor_ang_tol : i == 2 ? klnet.pos_tol : i == 3 ? klnet.ang_tol : -1.0f;
    *want = *cur;
    if (ms > 0) want->min = (DWORD)(ms * klnet_ds[i].mul2 / 2);
    if (rf > 0) want->max = (DWORD)rf;
    if (want->max <= want->min) want->max = want->min + 50;          /* the forced refresh stays above the min */
    if (tol > 0.0f) want->tol2 = tol * tol;
    return want->min != cur->min || want->max != cur->max || want->tol2 != cur->tol2;
}

static void klnet_tune(int act, DWORD b)
{
    struct klnet_num cur[KLNET_NDS], want; int i, n = 0, refused = 0;
    if (!klnet.tune || !klnet.any) return;
    if (!act) {                                               /* put back what is still ours */
        if (!klnet_t.have) return;
        klnet_read_nums(cur);
        for (i = 0; i < KLNET_NDS; i++) {
            if (!klnet_t.wrote[i]) continue;
            if (cur[i].min == klnet_t.ours[i].min && cur[i].min != klnet_t.stock[i].min) n += klh_data((void *)KLH_VA(klnet_ds[i].min), &klnet_t.stock[i].min, 4, "Net-Z min update interval (stock)");
            if (cur[i].max == klnet_t.ours[i].max && cur[i].max != klnet_t.stock[i].max) n += klh_data((void *)KLH_VA(klnet_ds[i].max), &klnet_t.stock[i].max, 4, "Net-Z max update interval (stock)");
            if (cur[i].tol2 == klnet_t.ours[i].tol2 && cur[i].tol2 != klnet_t.stock[i].tol2) n += klh_data((void *)KLH_VA(klnet_ds[i].tol), &klnet_t.stock[i].tol2, 4, "Net-Z error tolerance (stock)");
        }
        memset(&klnet_t, 0, sizeof klnet_t);
        klog("net: tune: the session is over or no longer one the tune acts on: %d number(s) put back to what the game had (a number the game has set again itself is left)", n);
        return;
    }
    klnet_read_nums(cur);
    if (!klnet_t.have) {                                      /* the first pass of this session: what stands there is the game's */
        memcpy(klnet_t.stock, cur, sizeof cur); memset(klnet_t.wrote, 0, sizeof klnet_t.wrote); klnet_t.have = 1;
        klnet_log_nums(cur, b, "the game's, before the tune");
    }
    for (i = 0; i < KLNET_NDS; i++) {
        if (!cur[i].ok) { refused++; continue; }
        if (klnet_t.wrote[i]) {                               /* a number the game has set again (a new Net-Z start: 0x4825b0 rewrites min and tolerance) is the stock value now */
            if (cur[i].min != klnet_t.ours[i].min) klnet_t.stock[i].min = cur[i].min;
            if (cur[i].max != klnet_t.ours[i].max) klnet_t.stock[i].max = cur[i].max;
            if (cur[i].tol2 != klnet_t.ours[i].tol2) klnet_t.stock[i].tol2 = cur[i].tol2;
        }
        if (!klnet_want(i, &klnet_t.stock[i], &want)) continue;
        if (want.min != cur[i].min) n += klh_data((void *)KLH_VA(klnet_ds[i].min), &want.min, 4, "Net-Z min update interval");
        if (want.max != cur[i].max) n += klh_data((void *)KLH_VA(klnet_ds[i].max), &want.max, 4, "Net-Z max update interval");
        if (want.tol2 != cur[i].tol2) n += klh_data((void *)KLH_VA(klnet_ds[i].tol), &want.tol2, 4, "Net-Z error tolerance");
        klnet_t.ours[i] = want; klnet_t.ours[i].ok = 1; klnet_t.wrote[i] = 1;
    }
    if (n) {
        klnet_read_nums(cur);
        klog("net: tune: %d number(s) written%s", n, refused ? "; a dataset whose memory is not as expected was left alone" : "");
        klnet_log_nums(cur, b, "now");
    }
}

static void klnet_tick(int game_thread)
{
    static DWORD last, sig0, state0 = 0xffffffff, lobsig0, dsig0, numsig0, slot_since; static int toldgate = -1, net0; static char scene0[160], why0[200];
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, handler, hvt, gs, rules, rvt, svc, d, sub = 0, sig, b = 0, numsig; BYTE idx_host = 0xff, idx_cl = 0xff, minp = 0, maxp = 0;
    char map[72], scene[160], why[200], slot[8], key[64], wantkey[24]; int net, verdict = 0, act = 0, i, idx = -1, slot_ok = 0; struct klnet_num nums[KLNET_NDS];
    BYTE props[0x20], exists = 0, ranked = 0, d_idx = 0xff; DWORD lob[2] = { 0, 0 }; int have_svc = 0, priv = 0, rank = 0;
    (void)game_thread;
    if ((!klnet.log && !klnet.tune) || !klh_exe_ok || now - last < 100) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) { klnet_tune(0, 0); return; }
    net = role == 2 || role == 3;
    if (net != net0) {                                        /* a network session begins or is over: everything said is forgotten, so a second
                                                                 session of this process that is the same in every field says its lines again */
        sig0 = lobsig0 = dsig0 = numsig0 = 0; state0 = 0xffffffff; scene0[0] = 0; why0[0] = 0; toldgate = -1; slot_since = 0;
        net0 = net;
    }
    klh_rd(sm + 0x158, &b, 4);
    handler = klh_rd32(sm + 4); hvt = handler ? klh_rd32(handler) : 0;
    rules = (gs = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SETTINGS))) != 0 ? klh_rd32(gs + 0x54) : 0; rvt = rules ? klh_rd32(rules) : 0;
    klh_rd((DWORD_PTR)KLH_VA(KLNET_SUBMODE), &sub, 4);
    klh_rd(sm + 0xbf, &idx_host, 1); klh_rd(sm + 0xbe, &idx_cl, 1); klh_rd(sm + 0xb9, &minp, 1); klh_rd(sm + 0xb8, &maxp, 1);
    if (!klh_rd(sm + 8, map, 0x40)) map[0] = 0;
    map[0x40] = 0;
    for (i = 0; map[i]; i++) if ((BYTE)map[i] < 0x20 || (BYTE)map[i] > 0x7e) { map[i] = 0; break; }
    /* the service and its lobby */
    if ((svc = klh_rd32(sm + 0x17c)) != 0 && klh_rd32(svc) == KLNET_SVC_VT && klh_rd(svc + 0x370, props, sizeof props) &&
        klh_rd(svc + 0x35c, &exists, 1) && klh_rd(svc + 0x36f, &ranked, 1) && klh_rd(svc + 0x35e, lob, 8)) {
        have_svc = 1; priv = (props[8] >> 4) & 1; rank = (props[8] >> 5) & 1;
    }
    /* the level */
    if (klh_scene(scene, sizeof scene)) verdict = klx_level_verdict_raw(scene, why); else { scene[0] = 0; why[0] = 0; }
    /* the level index of THIS session: the replicated server object's (what both load paths use, 0x6c536f / 0x491fd1);
       a host that has no such object yet has the index it chose itself. Is the scene the engine names that slot? */
    if ((d = klh_rd32(sm + 0x84)) != 0 && klh_rd(d + 0x1b0, &d_idx, 1)) idx = (signed char)(d_idx ^ 0xac);
    else if (role == 2) idx = (signed char)idx_host;
    if (idx >= 0 && idx < 9 && scene[0] && klh_level_key(scene, key, sizeof key)) {
        snprintf(wantkey, sizeof wantkey, "f%02d\\f%02d_main", idx + 1, idx + 1);
        slot_ok = !strcmp(key, wantkey);
    }

    /* ---- the tune: only a network session of the FA family, past its load, in the scene of its own level index, on a
            level that is not stock, not ranked; on the host only when the game itself made the lobby private (proved from
            memory); on a client only on the player's word, TuneClient=1 (a client cannot see the lobby's kind) */
    if (klnet.tune && klnet.any) {
        int is_ranked = role == 2 ? (ranked || rank) : ranked != 0;          /* a client's property bits are stale: its ranked BYTE alone */
        int gate = !net ? 1 : mode != 4 ? 2 : role == 3 && !klnet.tune_client ? 8 : state < 0x13 || state > 0x1f ? 3 : !slot_ok ? 9 : verdict != 2 ? 4 :
                   !have_svc ? 5 : is_ranked ? 6 : role == 2 && !priv ? 7 : 0;
        act = !gate;
        if (gate != 9) slot_since = 0; else if (!slot_since) slot_since = now ? now : 1;
        if (net && gate != toldgate && gate != 3 && (gate != 9 || now - slot_since >= 5000)) {      /* 9 is said only once it has stood 5 s: it is passed through at every load */
            static const char *const say[10] = { "acts on this session", "", "the game type is not 4 (Fragile Alliance family)", "", "the level is the stock one of its slot, or not known",
                "the online service object is not the one this build knows", "the session is RANKED", "this machine hosts and the session is not private (friends only)",
                "this machine has JOINED the session and a client cannot tell from memory whether the lobby is private; TuneClient=1 is the player's word that it is (friends only, joined by invitation)",
                "the scene the engine names is not the slot of this session's level index (not known yet, or -o MPMap is in use)" };
            klog("net: tune: %s%s%s", gate ? "nothing is written: " : "", say[gate],
                 !gate ? role == 3 ? " - as a CLIENT, on the player's word (TuneClient=1) that the lobby is friends-only; the ranked byte is 0" : " - as the HOST of a lobby the game made friends-only (private bit 1, ranked 0)" : "");
            toldgate = gate;
        }
        klnet_tune(act, b);
    }
    if (!klnet.log || (!net && klnet.log < 2)) { state0 = state; return; }

    /* ---- the log */
    sig = role * 31 + mode; sig = sig * 31 + hvt; sig = sig * 31 + rvt; sig = sig * 31 + idx_host; sig = sig * 31 + idx_cl; sig = sig * 31 + sub;
    for (i = 0; map[i]; i++) sig = sig * 31 + (BYTE)map[i];
    if (sig != sig0) {
        klnet_slot_name(net && role == 3 ? (signed char)idx_cl : (signed char)idx_host, slot);
        klog("net: session: %s (role %lu), game type %lu%s, sub-mode %lu, state 0x%lx; handler %s; rules %s; players %u..%u; level index host-set %d / given %d (%s), map '%s'",
             klnet_role_name(role), role, mode, mode == 4 ? " (FA family)" : "", sub, state, klnet_vt_name(hvt), klnet_vt_name(rvt), minp, maxp, (signed char)idx_host, (signed char)idx_cl, slot, map);
        if (net && rvt == 0x00bd3514) klog("net: NOTE: a network role with the Arcade rules class - not a case this file knows");
        sig0 = sig;
    } else if (state != state0 && state0 != 0xffffffff) klog("net: state 0x%lx -> 0x%lx", state0, state);
    state0 = state;
    /* the replicated server object */
    if ((d = klh_rd32(sm + 0x84)) != 0) {
        BYTE a = 0, c = 0, t = 0; char dmap[72], ver[72]; DWORD dsig;
        klh_rd(d + 0x1b0, &a, 1); klh_rd(d + 0x190, &c, 1); klh_rd(d + 0x110, &t, 1);
        a ^= 0xac; c ^= 0xac; t ^= 0xdc;
        klh_rdstr(klh_rd32(d + 0x234), dmap, sizeof dmap); klh_rdstr(klh_rd32(d + 0x254), ver, sizeof ver);
        dsig = d * 31 + a; dsig = dsig * 31 + c; dsig = dsig * 31 + t;
        for (i = 0; dmap[i]; i++) dsig = dsig * 31 + (BYTE)dmap[i];
        for (i = 0; ver[i]; i++) dsig = dsig * 31 + (BYTE)ver[i];
        if (dsig != dsig0) {
            klnet_slot_name((signed char)a, slot);
            klog("net: server object %08lx: level index %d (%s) - each peer turns it into a scene name through its OWN level list -, second index %d, game type %u, map '%s', text at +0x250 '%s'",
                 d, (signed char)a, slot, (signed char)c, t, dmap, ver);
            dsig0 = dsig;
        }
    } else dsig0 = 0;
    if (have_svc) {
        DWORD lsig = svc * 31 + lob[0]; lsig = lsig * 31 + lob[1]; lsig = lsig * 31 + (role == 3 ? 0x100u : props[8]);      /* a client's property bits are stale: no part of what is said */
        lsig = lsig * 31 + exists; lsig = lsig * 31 + ranked;
        if (lsig != lobsig0 && (exists || lob[0] || lob[1])) {
            if (role == 3)                                    /* JoinSession 0x6d8640 writes the id and the ranked byte, never the property block */
                klog("net: lobby %08lx%08lx (service %08lx, session byte %u): JOINED - ranked byte %u%s; kind (private / public) not known on a client: the join does not write the property bits, and what stands there (private bit %d, ranked bit %d) is left from this machine's own last hosting",
                     lob[1], lob[0], svc, exists, ranked, ranked ? " = RANKED" : "", priv, rank);
            else
                klog("net: lobby %08lx%08lx (service %08lx, session byte %u): %s - private bit %d, ranked bit %d, ranked byte %u, max players %u (the type is what the game's own create routine 0x8e514b derives from these bits)",
                     lob[1], lob[0], svc, exists, (ranked || rank) ? "RANKED (invisible, type 3)" : priv ? "PRIVATE (friends only, type 1)" : "PUBLIC (type 2)", priv, rank, ranked, props[5]);
        }
        lobsig0 = lsig;
    }
    if (scene[0] && verdict && (strcmp(scene, scene0) || strcmp(why, why0))) {
        klog("net: level %s: %s (%s)%s", scene, verdict == 1 ? "stock" : verdict == 2 ? "NOT stock" : "not known", why,
             verdict == 2 ? " - EVERY PEER MUST HAVE LOADED THE IDENTICAL BUILD OF IT: nothing in the game checks that (re\\netcode_fa.md 2)" : "");
        snprintf(scene0, sizeof scene0, "%s", scene); snprintf(why0, sizeof why0, "%s", why);
    }
    klnet_read_nums(nums);
    for (numsig = b, i = 0; i < KLNET_NDS; i++) { numsig = numsig * 31 + nums[i].min; numsig = numsig * 31 + nums[i].max; numsig = numsig * 31 + *(DWORD *)&nums[i].tol2; }
    if (numsig != numsig0) { klnet_log_nums(nums, b, act ? "with the tune" : "as they stand"); numsig0 = numsig; }
}

static LONG klnet_key(const char *key, LONG lo, LONG hi)
{
    LONG v = (LONG)GetPrivateProfileIntA("Net", key, -1, klh_ini);
    if (v < 0) return -1;
    if (v < lo || v > hi) { klog("net: %s=%ld is outside %ld..%ld: left alone", key, v, lo, hi); return -1; }
    return v;
}

static void klnet_init(void)
{
    klnet.log = GetPrivateProfileIntA("Net", "Log", 0, klh_ini);
    klnet.tune = GetPrivateProfileIntA("Net", "Tune", 0, klh_ini) != 0;
    klnet.tune_client = GetPrivateProfileIntA("Net", "TuneClient", 0, klh_ini) == 1;
    klnet.player_ms = klnet_key("PlayerMs", 16, 500); klnet.refresh_ms = klnet_key("RefreshMs", 100, 5000);
    klnet.actor_ms = klnet_key("ActorMs", 16, 500); klnet.actor_refresh_ms = klnet_key("ActorRefreshMs", 100, 5000);
    klnet.pos_tol = (float)klnet_key("PosTol", 1, 100); klnet.ang_tol = (float)klnet_key("AngTol", 1, 100);
    klnet.actor_pos_tol = (float)klnet_key("ActorPosTol", 1, 100); klnet.actor_ang_tol = (float)klnet_key("ActorAngTol", 1, 100);
    klnet.any = klnet.player_ms > 0 || klnet.refresh_ms > 0 || klnet.actor_ms > 0 || klnet.actor_refresh_ms > 0 ||
                klnet.pos_tol > 0 || klnet.ang_tol > 0 || klnet.actor_pos_tol > 0 || klnet.actor_ang_tol > 0;
    if (!klnet.log && !klnet.tune) return;
    klog("net: on; Log=%d Tune=%d TuneClient=%d (PlayerMs=%ld RefreshMs=%ld PosTol=%.0f AngTol=%.0f ActorMs=%ld ActorRefreshMs=%ld ActorPosTol=%.0f ActorAngTol=%.0f; -1 = left alone)%s; the log reads only; the tune writes data only (twelve numbers of kl2.exe's .data), only in a network session of the Fragile Alliance family, after its load, on a level that is not the stock one of its slot; as HOST only when the game made the lobby private (friends only) and not ranked - read from memory; as CLIENT %s; no Steam call, no game call, no lobby is made or joined by this part",
         klnet.log, klnet.tune, klnet.tune_client, klnet.player_ms, klnet.refresh_ms, klnet.pos_tol, klnet.ang_tol, klnet.actor_ms, klnet.actor_refresh_ms, klnet.actor_pos_tol, klnet.actor_ang_tol,
         klnet.tune && !klnet.any ? " - Tune=1 without a number: nothing will be written" : "",
         klnet.tune_client ? "ON THE PLAYER'S WORD (TuneClient=1): a client cannot see whether the lobby it joined is private, only that its ranked byte is 0 - join friends-only lobbies by invitation only while this line stands" : "never (TuneClient=0)");
}

#endif /* KLNET_C */
