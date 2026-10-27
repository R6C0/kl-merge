/*
 * klcrew_rt.c - THE AI CREW FOLLOWS THE JUMP: on a level made of two places that only kljoin.c joins (Retomoto
 * Tower: the tower's navigation mesh part and the lobby + street part have no polygon in common), the AI heisters
 * are put in front of the jump entry by the game's own actor teleport when the player's jump is requested. The
 * level's own JumpPoint list then starts their street route (tools\kl_fa_bots_rt.py writes both: the list and the
 * [CrewJoin] section of the level's KLJoin.ini). Owner, 2026-10-10: 'bots on retomoto please'.
 * Part of KLHook (to be included by klhook.c AFTER kljoin.c, SHIP and TEST alike; the three lines are at the end of
 * this comment). NO data write and no code byte: calls of ONE game function (two with Retrigger=1) from the game's
 * own thread. Spec, the reading it rests on, the live checks R1..R8: re\bots_retomoto.md.
 * NOTHING HERE HAS RUN IN THE GAME. Off unless KLHook.ini has [CrewJoin] Enable=1. Arcade only (ZGameRulesHeist).
 *
 * 1. THE GAME'S MECHANISM (kl2.exe build 0490, read 2026-10-10 with debug\dasm.py; EXE = seen in the code)
 *    - 0x62a900 = void __thiscall teleport(actor, const float rot[9], const float pos[3], char a, char b), ret 0x10.
 *      EXE: it calls actor->vtable[0x5bc](0.0f), actor->vtable[0x2a8](rot, pos) (the transform), vtable[0x5d4](pos,
 *      1, 0), with a != 0 resets the animation state (0x6270d0 / 0x7613f0), clears [[actor+0x7c0]], and with b != 0
 *      and a network session (0x863a60([0x168e598])) sends the place to the peers.
 *      WHO CALLS IT (22 call sites): ZFFActor's OWN vtable slot 18 (0x6ccc80) on itself at 0x6ccdc1 (it restores an
 *      actor's saved state: reads a place and a matrix from a stream, then this call) - so `this` = a ZFFActor is
 *      the game's own use; ZFFPlayer's slot 18 (0x803c40) the same; the AI scripts ZAirlockGoal (0x48eeb0),
 *      ZExitVehicleGoal (0x6e2c40), ZCloseCombat (0x656fb0), ZCustomDeath (0x5a4f40), ZPlayMiniScene (0x6b6550),
 *      ZAttackMountedWeaponTactic (0x6fbc10) on `[[script+4]+0x40]`, the script's actor; and the jump itself:
 *      0x8f3fa0, the routine 0x57e110 moves the players with, calls it at 0x8f4128 for every member of the STORY
 *      crew (`push 1 ; push 1 ; push &pos ; mov ecx,[member+0x40] ; push rot`), the members 100 units apart
 *      (0x8f4100, float 0xb5c050). That crew walk is the one a Fragile Alliance player has no list for (crash
 *      0x8f40c9, run RT3; kljoin.c uses the debug request, which skips it). This file does for the Fragile
 *      Alliance crew what 0x8f4128 does for the story crew, with the same routine and the same two flags.
 *      THE ROUTINE HAS AN int3: 0x62a9a4..0x62a9b8, `if ([actor+0x77c] == 0 && [actor+0x780] == 0) int3`. What
 *      the two pointers are is NOT established (+0xe4 / +0xec of the first are used: ASSUMPTION the physics body).
 *      An actor with both zero is never handed to the routine here.
 *      rot: 0x7f07a0 (the constructor 0x4d99a0 uses for it) writes nine floats, 1 at +0, +0x10, +0x20: a 3x3
 *      matrix. The identity is passed (which way the bots look for the first moment is not chosen).
 *    - The jump, as kljoin.c's comment has it: 0x57e110 - `if ([0x156b358]) { both requests = 0; index = [gamedata+
 *      0x8d4]; 0x8f3fa0(entry position, ...) moves the local players; 0x72e0f0([entry+0x1c]) }`. 0x72e0f0 (its only
 *      caller is 0x57e1da) sends the message word [0x1689020] ('AITrigger') to every object of the ZJumpPoint's
 *      reference list [jp+0x34]. ZDefendBehaviourRout's slot 26 (0x4ebed0) takes it: `if (!this[0x41] && (!this
 *      [0x42] || !this[0x40])) { vtable[0x88](); this[0x40] = 1; }` = the step starts. Stock use of such a list for
 *      a friendly AI: campaign L05, `Jumppoints!Jump04` and `Jump05` name `AI!Friendly!B6!Kane_B6\FollowLynch` (a
 *      FollowBehaviourRout; read from the level with tools\kl_fa.py).
 *    - Crew records as klbot.c 1: rules = [[0x168e9e4]+0x54] (vtable 0xbd3514), records [rules+0x348] + i * 0x7c,
 *      in-use byte [rules+0x34c] + i == 0, number [rules+0x354]; record +4 the actor (vtable 0xbb3bac), +0x10 status
 *      (0 = in play, 4 = aboard, 7 = dead), +0x79 mask 1 = an AI member.
 *
 * 2. WHAT THE HOOK DOES
 *    Only on the level whose archive has a KLJoin.ini with a [CrewJoin] section (kljoin.c found and read that file:
 *    never beside a stock archive), in Arcade, once per round.
 *    EARLY (the form the design rests on): in the tick in which the debug jump request is pending for THE entry
 *    of [CrewJoin] ([0x156b358] != 0 and [gamedata+0x8d4] = its index - kljoin.c has just written both, klt_tick
 *    runs right after klj_tick) and the tick is on the game's thread, every AI record in play is teleported to
 *    Place.n (n = its order among the AI records in play). The game then, in its own update, moves the player and
 *    sends 'AITrigger': the bots' street steps start with the bots already standing on the street's mesh part.
 *    LATE (the request was consumed before a game-thread tick saw it - the fallback thread wrote it): when a local
 *    player stands within Radius of Target after he was farther than From in this round, the same teleport. The
 *    street steps were then started while the bots stood in the tower; what a DefendBehaviourRout does with a
 *    place on another mesh part for those frames is NOT established. Retrigger=1 calls 0x72e0f0 once more after
 *    the late teleport (the game's own routine on the entry's own ZJumpPoint; a step that is already running is
 *    started again by slot 26 unless its byte 0x42 is set - which property that byte is, is not established).
 *    NOT moved: a record that is aboard or dead, an actor whose vtable is not ZFFActor's, whose node has flag bit
 *    10 (the test 0x8f3fcf makes for a player) or whose two pointers of the int3 are both zero (the same test guards
 *    the second int3, 0x62aa43), and a bot that is already within Near of Target in the plan and 1000 in height.
 *    Since the review (re\crew_talk_review.md 2.2 a) also an actor whose [actor+0x7c0] is null or not writable data
 *    (0x62a998 `mov edx,[esi+0x7c0]` / `mov [edx],0`, no test in the game) or whose [actor+0x50c] is null or has no
 *    vtable of the game with a code address at +0xac (0x62a9e8 calls it, no test in the game), or whose non-zero
 *    pointer of the int3 pair cannot be read at +0xec (0x62a9d2). The game's own callers hand over actors a script
 *    owns; the hook reaches the actor from a crew record, so it tests what they take for granted.
 *    The EARLY form needs kljoin.c ON ([KLHook] Join=1, the default): the places and the entry come from the file
 *    kljoin.c read, and the request is kljoin.c's. With Join=0 this part is inert and says so at start.
 *    ARCADE ONLY (session mode 4), where there is one machine. Online the actors belong to the host and every
 *    player jumps on his own machine at his own time (kljoin.c, MULTIPLAYER): when the crew should move there, and
 *    which test says 'this machine is the host', is NOT worked out.
 *
 * KLHook.ini
 *   [CrewJoin]
 *   Enable=0          1 = this file is on
 *   Retrigger=0       1 = after a LATE teleport the entry's 'AITrigger' list is sent again (0x72e0f0)
 *   Log=1
 * KLJoin.ini beside the level archive (written by tools\kl_fa_bots_rt.py)
 *   [CrewJoin]
 *   Name=06_Exit            the jump entry: its name must contain this, and
 *   Target=6272 563 -6305   it must stand within Tolerance (8) of this
 *   Radius=300  From=2000   the late form
 *   Near=1500               a bot this near to Target already is left where it is
 *   Lift=0                  added to the height of every place
 *   Places=7                Place.1 .. Place.8 = x y z, feet on the navigation mesh
 *
 * LOG
 *   crewjoin: on; Retrigger=0
 *   crewjoin: 7 places from <file> for level f01\f01_main: entry '06_Exit' at (6272, 563, -6305)
 *   crewjoin: the jump to entry 5 '...06_Exit' is pending: 7 AI heisters in play are moved first (EARLY)
 *   crewjoin: bot 3 (actor ...) at (2431, 19600, 512) -> place 3 (5912, 570, -6185): now at (5912, 570, -6185)
 *   crewjoin: bot 5 (actor ...) NOT moved: aboard / dead / no body pointers / already at the entry
 *   crewjoin: LATE: the player is at the entry, the request was not seen pending: 7 AI heisters moved now
 *   crewjoin: 'AITrigger' sent again to the list of '06_Exit'
 *
 * THE LEAD'S THREE LINES IN klhook.c (compiled that way off-game: re\bots_retomoto.md 5):
 *   #include "klcrew_rt.c"       after  #include "kljoin.c"
 *   klt_tick(game_thread);       in klh_tick, DIRECTLY after  klj_tick();   (the order is the early form)
 *   klt_init();                  in DllMain, after  klj_init();
 * and the [CrewJoin] block above in klhook\KLHook.ini, and a row 'klcrew_rt.c  x  x  AI crew follows the jump' in
 * the file table (calls: 0x62a900, 0x72e0f0; no data, no code).
 */
#ifndef KLCREW_RT_C
#define KLCREW_RT_C

#define KLT_SESSION    0x0168e598             /* +0x5c = mode (4 = Arcade), +0x70 = state */
#define KLT_SETTINGS   0x0168e9e4             /* +0x54 = the rules object */
#define KLT_RULES_VT   0x00bd3514             /* ZGameRulesHeist */
#define KLT_ACTOR_VT   0x00bb3bac             /* ZFFActor */
#define KLT_TELEPORT   0x0062a900             /* (actor, rot[9], pos[3], 1, 1) */
#define KLT_AITRIGGER  0x0072e0f0             /* (ZJumpPoint): 'AITrigger' to its reference list */
#define KLT_REQUEST    0x0156b358             /* the debug jump request (kljoin.c) */
#define KLT_NREC       32
#define KLT_NPLACE     8

static struct { int on, log, retrigger, fedskip; } klt;
static struct {
    int have, nplace; char key[64], file[MAX_PATH], name[48]; FILETIME ft;
    float target[3], tol, radius, from, near_, lift, place[KLT_NPLACE][3];
} klt_lv;
static struct { DWORD rules; int left, done, far_seen, told, fedtold; } klt_r;

static int klt_same_code(DWORD va, const BYTE *bytes, int n)
{
    BYTE c[16];
    return n <= (int)sizeof c && klh_rd((DWORD_PTR)KLH_VA(va), c, n) && !memcmp(c, bytes, n);
}

static float klt_num(const char *key, const char *def, const char *file)
{
    char t[32];
    GetPrivateProfileStringA("CrewJoin", key, def, t, sizeof t, file);
    return (float)atof(t);
}

/* the [CrewJoin] section of the KLJoin.ini kljoin.c has read for the running level (never a stock archive's) */
static void klt_source(void)
{
    char key[64], file[MAX_PATH], t[32]; FILETIME ft; int i, n;
    EnterCriticalSection(&klj_cs);
    snprintf(key, sizeof key, "%s", klj_map_key); snprintf(file, sizeof file, "%s", klj_map_file); ft = klj_map_ft;
    LeaveCriticalSection(&klj_cs);
    if (!strcmp(key, klt_lv.key) && !_stricmp(file, klt_lv.file) && !CompareFileTime(&ft, &klt_lv.ft)) return;
    memset(&klt_lv, 0, sizeof klt_lv);
    strcpy(klt_lv.key, key); strcpy(klt_lv.file, file); klt_lv.ft = ft;
    if (!key[0] || !file[0]) return;
    if (!GetPrivateProfileStringA("CrewJoin", "Name", "", klt_lv.name, sizeof klt_lv.name, file) || !klj_vec("CrewJoin", "Target", file, klt_lv.target)) {
        if (GetPrivateProfileStringA("CrewJoin", 0, "", t, sizeof t, file)) klog("crewjoin: [CrewJoin] of %s refused: it needs Name= and Target=", file);
        return;
    }
    klt_lv.tol = klt_num("Tolerance", "8", file); klt_lv.radius = klt_num("Radius", "300", file); klt_lv.from = klt_num("From", "2000", file);
    klt_lv.near_ = klt_num("Near", "1500", file); klt_lv.lift = klt_num("Lift", "0", file);
    n = (int)GetPrivateProfileIntA("CrewJoin", "Places", 0, file);
    for (i = 0; i < n && i < KLT_NPLACE; i++) {
        snprintf(t, sizeof t, "Place.%d", i + 1);
        if (!klj_vec("CrewJoin", t, file, klt_lv.place[klt_lv.nplace])) break;
        klt_lv.nplace++;
    }
    if (!klt_lv.nplace) { klog("crewjoin: [CrewJoin] of %s refused: no Place.1", file); return; }
    klt_lv.have = 1;
    klog("crewjoin: %d places from %s for level %s: entry '%s' at (%g, %g, %g)", klt_lv.nplace, file, key, klt_lv.name, klt_lv.target[0], klt_lv.target[1], klt_lv.target[2]);
}

/* the index of the [CrewJoin] entry in the level's jump list, -1 = not there; *jp = its ZJumpPoint */
static int klt_entry(DWORD gd, DWORD *jp, char name[64])
{
    DWORD lo = 0, hi = 0; BYTE ent[32]; int count, i, k;
    if (!klh_rd(gd + 0x8c4, &lo, 4) || !klh_rd(gd + 0x8c8, &hi, 4) || !lo || hi <= lo) return -1;
    count = (int)((hi - lo) >> 5);
    if (count > KLJ_MAXLIST) return -1;
    for (i = 0; i < count; i++) {
        if (!klh_rd(lo + 32 * i, ent, 32) || !klh_rdstr(*(DWORD *)ent, name, 64) || !klj_contains(name, klt_lv.name)) continue;
        for (k = 0; k < 3 && fabs(((float *)(ent + 4))[k] - klt_lv.target[k]) <= klt_lv.tol; k++) ;
        if (k == 3) { *jp = *(DWORD *)(ent + 0x1c); return i; }
    }
    return -1;
}

/* the two pointers 0x62a900 uses without a test of its own (re\crew_talk_review.md 2.2 a): what must hold of them */
static int klt_writable(DWORD p, DWORD n)
{   /* committed, writable data that reaches n bytes: `mov dword [edx], 0` at 0x62a99e must not fault */
    MEMORY_BASIC_INFORMATION mbi;
    return p > 0xffff && VirtualQuery((void *)(DWORD_PTR)p, &mbi, sizeof mbi) && mbi.State == MEM_COMMIT && !(mbi.Protect & PAGE_GUARD) &&
           (mbi.Protect & (PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE)) && (BYTE *)(DWORD_PTR)p + n <= (BYTE *)mbi.BaseAddress + mbi.RegionSize;
}
static int klt_code(DWORD va)
{   /* an address inside kl2.exe's image (a vtable entry of the game: every one points into .text) */
    return va >= KL2_BASE + 0x1000 && va < KL2_BASE + KL2_IMAGESIZE;
}

/* What 0x62a900 takes for granted of the actor it is handed (section 2, NOT moved) -> 0 = it may be called, else
   why not. Reads only. klhop.c makes the same tests through this function. */
static const char *klt_refuse(DWORD actor)
{
    DWORD node, fl3c = 0, body[2] = { 0, 0 }, p7c0 = 0, p50c = 0, vt = 0, tmp = 0;
    if (klh_rd32(actor) != KLT_ACTOR_VT) return "its actor is not a ZFFActor";
    if (!(node = klh_rd32(actor + 4)) || !klh_rd(node + 0x3c, &fl3c, 4) || (fl3c >> 10 & 1)) return "its node is off (flag bit 10)";
    if (!klh_rd(actor + 0x77c, body, 8) || (!body[0] && !body[1])) return "both pointers the game's routine asserts on are zero";
    if (!klh_rd((body[0] ? body[0] : body[1]) + 0xec, &tmp, 4)) return "the pointer at +0x77c / +0x780 cannot be read at +0xec (0x62a9d2)";
    if (!klh_rd(actor + 0x7c0, &p7c0, 4) || !p7c0 || !klt_writable(p7c0, 4)) return "[actor+0x7c0], which the game's routine writes through (0x62a99e), is null or not writable";
    if (!klh_rd(actor + 0x50c, &p50c, 4) || !p50c || !klh_rd(p50c, &vt, 4) || !klt_code(klh_rd32((DWORD_PTR)KLH_VA(vt + 0xac)))) return "[actor+0x50c], which the game's routine calls through (0x62a9e8, vtable +0xac), is null or no object of the game";
    return 0;
}

/* Is 0x62a900 the routine this build knows (its first 14 bytes)? */
static int klt_tele_known(void)
{
    static const BYTE tele_code[14] = { 0x81, 0xec, 0x90, 0x00, 0x00, 0x00, 0xd9, 0xee, 0x53, 0x56, 0x57, 0x8b, 0xf1, 0x8b };          /* 0x62a900 */
    return klt_same_code(KLT_TELEPORT, tele_code, sizeof tele_code);
}

/* THE call: the game's own actor teleport with the identity matrix and the two flags 0x8f4128 passes. Game thread
   only, and only for an actor klt_refuse() let through while klt_tele_known() holds. */
static void klt_teleport_ex(DWORD actor, const float pos[3], const float *rotp, int a, int b)
{
    static const float rot[12] = { 1, 0, 0,  0, 1, 0,  0, 0, 1,  0, 0, 0 };      /* nine are read (0x7f07a0); three spare */
    float p[4];
    p[0] = pos[0]; p[1] = pos[1]; p[2] = pos[2]; p[3] = 0;
    ((void (__fastcall *)(void *, void *, const float *, const float *, int, int))(DWORD_PTR)KLH_VA(KLT_TELEPORT))((void *)(DWORD_PTR)actor, 0, rotp ? rotp : rot, p, a, b);
}
static void klt_teleport(DWORD actor, const float pos[3]) { klt_teleport_ex(actor, pos, 0, 1, 1); }

/* Game thread only. Every AI crew record in play to its place -> how many were moved. */
static int klt_move(DWORD rules)
{
    DWORD recs = klh_rd32(rules + 0x348), inuse = klh_rd32(rules + 0x34c); int cap = (int)klh_rd32(rules + 0x354), i, n = 0, moved = 0;
    if (cap < 1 || !recs || !inuse) return 0;
    if (cap > KLT_NREC) cap = KLT_NREC;
    for (i = 0; i < cap; i++) {
        DWORD at = recs + (DWORD)i * 0x7c, actor; BYTE u = 1, fl = 0, status = 0xff; float was[3] = { 0, 0, 0 }, is[3] = { 0, 0, 0 }, pos[3]; const char *why = 0;
        if (!klh_rd(inuse + i, &u, 1) || u || !klh_rd(at + 0x79, &fl, 1) || !(fl & 1) || !(actor = klh_rd32(at + 4))) continue;
        if (!klh_rd(at + 0x10, &status, 1) || status) continue;                 /* aboard, dead: not in play, takes no place */
        if (n >= klt_lv.nplace) { if (klt.log) klog("crewjoin: bot %d NOT moved: the level has %d places", i, klt_lv.nplace); continue; }
        memcpy(pos, klt_lv.place[n], sizeof pos); pos[1] += klt_lv.lift;
        klh_rd(actor + 0x460, was, 12);                                         /* ASSUMPTION: the feet, as a player's +0x460 (same base class); for the log and the Near test only */
        why = klt_refuse(actor);
        if (!why && fabs(was[0] - klt_lv.target[0]) < klt_lv.near_ && fabs(was[2] - klt_lv.target[2]) < klt_lv.near_ && fabs(was[1] - klt_lv.target[1]) < 1000) why = "it is at the entry already";
        if (why) { if (klt.log) klog("crewjoin: bot %d (actor %08lx) NOT moved: %s", i, actor, why); continue; }
        n++;                                                                    /* v82: a place is used up only by a bot that takes it (a bot left at the entry no longer leaves a hole in the ring) */
        klt_teleport(actor, pos);
        klh_rd(actor + 0x460, is, 12); moved++;
        if (klt.log) klog("crewjoin: bot %d (actor %08lx) at (%.0f, %.0f, %.0f) -> place %d (%.0f, %.0f, %.0f): now at (%.0f, %.0f, %.0f)", i, actor, was[0], was[1], was[2], n, pos[0], pos[1], pos[2], is[0], is[1], is[2]);
    }
    return moved;
}

/* v82c: is the local player (the one the jump moves) police? Same bytes as klfed.c (player + 0x2723 'ppolice', and the same KLP_PLAYER_VT vtable check, so a stale slot is never read as police). */
static int klt_local_police(DWORD gd)
{
    BYTE sel = 0xff, pol = 0; DWORD pl;
    if (!klh_rd(gd + 0x898, &sel, 1) || sel >= 28 || !(pl = klh_rd32(gd + 0x828 + 4 * sel)) || klh_pvt(pl) != 0x00bb45f4 /* KLP_PLAYER_VT, as klfed.c: a stale slot is not read */ || !klh_rd(pl + 0x2723, &pol, 1)) return 0;
    return pol != 0;
}

/* 2026-10-27 (kljoin.c FedRide): how many AI heisters in play (records as klt_move reads them) have their feet above height y. 0 = none above, -1 = none in play at all, or
   the rules object / records could not be read (then a fed is never held back). Reads only; any thread. */
static int klt_crew_above(float y)
{
    DWORD gs, rules, recs, inuse; int cap, i, n = 0, play = 0;
    if (!klh_exe_ok || !(gs = klh_rd32((DWORD_PTR)KLH_VA(KLT_SETTINGS))) || !(rules = klh_rd32(gs + 0x54)) || klh_rd32(rules) != KLT_RULES_VT) return 0;
    recs = klh_rd32(rules + 0x348); inuse = klh_rd32(rules + 0x34c); cap = (int)klh_rd32(rules + 0x354);
    if (cap < 1 || !recs || !inuse) return 0;
    if (cap > KLT_NREC) cap = KLT_NREC;
    for (i = 0; i < cap; i++) {
        DWORD at = recs + (DWORD)i * 0x7c, actor; BYTE u = 1, fl = 0, status = 0xff; float feet[3];
        if (!klh_rd(inuse + i, &u, 1) || u || !klh_rd(at + 0x79, &fl, 1) || !(fl & 1) || !(actor = klh_rd32(at + 4))) continue;
        if (!klh_rd(at + 0x10, &status, 1) || status) continue;
        play++;
        if (klh_rd(actor + 0x460, feet, 12) && feet[1] > y) n++;      /* ASSUMPTION as klt_move: the feet at actor + 0x460, y up */
    }
    return n ? n : (play ? 0 : -1);      /* review 10-27: -1 = records readable but NO AI heister in play yet (round start: a fed would be 'crew down' and thrown to the street at once) */
}

static void klt_tick(int game_thread)
{
    static const BYTE trig_code[14] = { 0x51, 0x53, 0x8b, 0xd9, 0x83, 0x7b, 0x34, 0x00, 0x74, 0x5d, 0x8b, 0x4b, 0x34, 0x8b };          /* 0x72e0f0 */
    static int toldcode;
    char scene[160], key[64], name[64]; DWORD sm, gs, rules, state, gd, jp = 0, req = 0, pl; int pend = -1, e, i, n; BYTE sel[2]; float feet[3];
    if (!klt.on || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLT_SESSION))) || klh_rd32(sm + 0x5c) != 4) return;                       /* Arcade only */
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    klt_source();
    if (!klt_lv.have || strcmp(key, klt_lv.key)) return;                                                           /* not the level the file belongs to */
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLT_SETTINGS))) || !(rules = klh_rd32(gs + 0x54)) || klh_rd32(rules) != KLT_RULES_VT) return;
    state = klh_rd32(sm + 0x70);
    if (rules != klt_r.rules) { memset(&klt_r, 0, sizeof klt_r); klt_r.rules = rules; }
    if (state < 0x12 || state > 0x19) { if (state >= 0x1f) klt_r.left = 1; return; }                               /* not inside a round (states: klcrew.c 3) */
    if (klt_r.left) { memset(&klt_r, 0, sizeof klt_r); klt_r.rules = rules; }                                      /* the next round */
    if (klt_r.done) return;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || (e = klt_entry(gd, &jp, name)) < 0) return;
    if (!klt_tele_known() || !klt_same_code(KLT_AITRIGGER, trig_code, sizeof trig_code)) {
        if (!toldcode++) klog("crewjoin: the game routines are not the ones this build knows: nothing is moved");
        return;
    }
    /* EARLY: kljoin.c's request for this entry is pending - the game has not moved the player yet */
    if (klh_rd((DWORD_PTR)KLH_VA(KLT_REQUEST), &req, 4) && klh_rd(gd + 0x8d4, &pend, 4) && req && pend == e) {
        if (!game_thread) { if (!klt_r.told++) klog("crewjoin: the jump to entry %d is pending but this tick is not on the game's thread: the late form will be tried", e); return; }
        if (klt.fedskip && klt_local_police(gd)) {   /* v82c: a fed's spawn fires the box 0.57 s after he appears (log 2026-10-17 11:09): the crew was dumped in the street mid-fight; they walk to the lift (CrewHop) instead */
            if (!klt_r.fedtold++) klog("crewjoin: the jump to entry %d '%s' is the local FED's: the AI heisters are NOT moved (FedSkip=1); they reach the street by the lift hops", e, name);
            return;
        }
        klog("crewjoin: the jump to entry %d '%s' is pending: the AI heisters in play are moved first (EARLY)", e, name);
        n = klt_move(rules); klt_r.done = 1;
        klog("crewjoin: %d moved; the game's own jump sends 'AITrigger' to the entry's list next", n);
        return;
    }
    /* LATE: a local player stands at the entry after he was far from it */
    if (!klh_rd(gd + 0x898, sel, 2)) return;
    for (i = 0; i < 2; i++) {
        float d2;
        if (sel[i] == 0xff || sel[i] >= 28 || !(pl = klh_rd32(gd + 0x828 + 4 * sel[i])) || !klh_rd(pl + 0x460, feet, 12)) continue;
        d2 = (feet[0] - klt_lv.target[0]) * (feet[0] - klt_lv.target[0]) + (feet[1] - klt_lv.target[1]) * (feet[1] - klt_lv.target[1]) + (feet[2] - klt_lv.target[2]) * (feet[2] - klt_lv.target[2]);
        if (!(d2 <= klt_lv.from * klt_lv.from)) { klt_r.far_seen = 1; continue; }                                  /* a NaN is far */
        if (!klt_r.far_seen || d2 > klt_lv.radius * klt_lv.radius || !game_thread) continue;
        if (klt.fedskip && klt_local_police(gd)) { if (!klt_r.fedtold++) klog("crewjoin: LATE: the local FED stands at the entry: the AI heisters are NOT moved (FedSkip=1)"); continue; }
        klog("crewjoin: LATE: player %d is at the entry '%s' (%.0f, %.0f, %.0f), the request was not seen pending: the AI heisters are moved now", i, name, feet[0], feet[1], feet[2]);
        n = klt_move(rules); klt_r.done = 1;
        if (klt.retrigger && n && jp) {
            ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLT_AITRIGGER))((void *)(DWORD_PTR)jp, 0);
            klog("crewjoin: %d moved; 'AITrigger' sent again to the list of '%s' (ZJumpPoint %08lx)", n, name, jp);
        } else klog("crewjoin: %d moved; their street steps were started by the jump BEFORE they stood here (Retrigger=%d)", n, klt.retrigger);
        return;
    }
}

static void klt_init(void)
{
    memset(&klt, 0, sizeof klt); memset(&klt_lv, 0, sizeof klt_lv); memset(&klt_r, 0, sizeof klt_r);
    klt.on = GetPrivateProfileIntA("CrewJoin", "Enable", 0, klh_ini) != 0;
    klt.retrigger = GetPrivateProfileIntA("CrewJoin", "Retrigger", 0, klh_ini) != 0;
    klt.fedskip = GetPrivateProfileIntA("CrewJoin", "FedSkip", 1, klh_ini) != 0;      /* v82c, default ON */
    klt.log = (int)GetPrivateProfileIntA("CrewJoin", "Log", 1, klh_ini);
    if (klt.on) klog("crewjoin: on; the AI crew follows the player's jump on a level whose KLJoin.ini has [CrewJoin]; Retrigger=%d%s", klt.retrigger,
                     klj_tick_on ? "" : " - but [KLHook] Join=0: no jump is requested, so nothing is moved");
}

#endif /* KLCREW_RT_C */
