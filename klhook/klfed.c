/*
 * klfed.c - COMING BACK AS A FED in an Arcade round: the dead player returns as a policeman and hunts the AI
 * heisters; a dead AI heister's parked policeman (level data of tools\kl_fa_fed.py) is released at that heister's
 * DEATH and not when he boards. Owner, 2026-10-10: 'i want to make it so you can come back as a fed or the ai
 * heisters can come back as feds too'.
 * Part of KLHook (to be included by klhook.c after klbot.c, SHIP and TEST alike; the three lines are at the end of
 * this comment). DATA WRITES ONLY: one dword of kl2.exe's zero-filled .data and bytes / floats of heap objects. No
 * game function is called, no code byte and no import slot changes. Research: re\fed_respawn.md (two passes);
 * spec and live checks: re\fed.md. Every address below was disassembled again for this file (debug\dasm.py,
 * kl2.exe build 0490, 2026-10-10). NOTHING HERE HAS RUN IN THE GAME. Everything is OFF unless [Fed] Enable=1 and
 * the part's own key are set.
 *
 * 0. WHERE IT ACTS
 *    Only in an Arcade session (the game's own test 0x7f6850: [session+0x5c] == 4, [session+0x54] not 2 / 3) whose
 *    round runs ([session+0x70] == 0x19), whose rules object is ZGameRulesHeist (vtable 0xbd3514), and only while
 *    the level that runs is NOT the stock level of its slot: klsteam.c's klx_level_verdict == 2, the verdict under
 *    which every Steam write of the round is blocked (the same gate as klbot.c section 0, written again here so
 *    that this file does not depend on klbot.c). Not on a stock level, not when the archive was not seen, not when
 *    the Steam write guard is off. The log part reads only and runs in every Arcade round.
 *
 * 1. THE GAME'S OWN PATH (EXE = read in the disassembly)
 *    ZGameRulesHeist still holds Fragile Alliance's 'dead criminal comes back as police':
 *    - kill rule, slot 11 = 0x704610: status of the local client's record = 7, countdown +0x08 = 5.0, flag 4, then
 *      0x7047b5 `call 0x67f480` ('is the round over?'). Yes (stock Arcade, always): the round clock is cut to 3 s.
 *      No (0x70482d): if slot 112 (0x4549f0: client flags 8 and 0x80 clear) -> status = 1, +0x11 = 0, flag 0x4000.
 *    - 0x67f480 begins `cmp dword [0x168ea60], 0 / je +4 / xor al, al / ret`: while that dword is not 0 the answer
 *      is 'no'. The exe refers to 0x168ea60 twice (here and in the server class's twin 0x86f520), both compares;
 *      nothing writes it; it lies in the zero-filled tail of .data, outside every hashed range (klranges.h).
 *    - status 1, per frame (0x58b40c): countdown -= dt; under 4.0 the second death-camera phase ('You respawn as
 *      police'); at 0: 0x4b28d0 - pick a free police player object (0x54cab0: first entry of the session's player
 *      table whose slot is in use, whose ZFFPlayer+0x273c == 3 and whose 'used' byte +9 is 0; it sets that byte),
 *      `int3` at 0x4b2984 when there is none, place it at an AFTER_DEATH spawn point (slot 199, type 2), police
 *      byte ZFFPlayer+0x2723 = 1 and client flag 8 (slot 204 = 0x7622f0), status 0, make it the local player
 *      (0x4d2ef0 -> ZSessionHandlerSP slot 53 = 0x42deb0 -> 0x537700).
 *    - the player table: T = [[session+4]+8] (ZSessionHandlerSP, vtable 0xbd1be4, slot 17 = 0x6e2650); [T] entries
 *      of 12 bytes (+4 the ZFFPlayer, +9 used), [T+4] one byte per entry (0 = in use), [T+0xc] their number.
 *      Nothing in single player clears a used byte: a level load has 8 police bodies and each respawn takes one.
 *    - round end, slot 192 = 0x5dff40: [rules+0x200] -= dt; at 0, with the vehicle state [rules+0x1dc] 0 or >= 7,
 *      a life is taken unless client 0 escaped, and the round ends. Slot 42 = 0x47d190 (the 'over' branch's cut)
 *      writes one value to [rules+0x4c], [rules+0x200] and [score+0x40].
 *    - a police human: the AI heisters (team 2) shoot him, the police AI does not (ZSoldier slot 111, 0x8824e7);
 *      he cannot board (0x68414e); a second death is final (slot 112 is false for police).
 *    Client flags = dword [score + 0x1d4 + 4 * index] (0x704787): 4 dead, 8 police, 0x80, 0x100 died once,
 *    0x4000 waiting to respawn. Crew records as klbot.c 1: [rules+0x348] + i * 0x7c, in-use byte [rules+0x34c] + i
 *    == 0, number [rules+0x354]; record +0 client block (byte 0 'not local', byte 1 the index), +4 the actor of an
 *    AI member, +8 float countdown, +0x10 status (0 in play, 1 dead and waiting to return as police, 4 aboard,
 *    5 / 6 escaped, 7 dead), +0x11 death-camera phase, +0x14 the police object's index (0xff = none), +0x79 mask 1
 *    = an AI member.
 *
 * 2. THE PLAYER (key Player)
 *    Each tick on the game's thread:
 *        armed =  the gate of section 0
 *             and record 0 is the local human and the local player object is a ZFFPlayer (vtable 0xbb45f4)
 *             and (   record 0 status 1                                  -- dead and waiting: held until he stands
 *                  or record 0 status 0, the local player a criminal (type byte 2, police byte 0), client flags
 *                     0x88 clear, at least MinCrew AI heisters in play (status 0), at least one free police body )
 *        [0x168ea60] = armed ? 1 : 0
 *    So the dword is 1 at the moment the human dies, the kill rule takes its 'no' branch and the game does the
 *    rest by itself. It is put back to 0 the moment he is aboard, police, dead for good, the round is not running,
 *    the level is stock, or anything of the above cannot be read; from the fallback thread too (ON only from the
 *    game's thread). A value that is neither 0 nor 1, or a 1 this file did not write, is left alone and said.
 *    WHY HOLDING IT IS HARMLESS (the gate's three callers): the kill rule - the purpose; the respawn (0x4b2a2c) -
 *    'no' there puts camera and HUD back to play (0x4ea400); the 'vehicle has left' routine (0x80530e) - for a
 *    living criminal on foot its own table says 'no' anyway, and the dword is off while record 0 is aboard.
 *    NO FREE POLICE BODY = the game's int3 at 0x4b2984: the hook counts the table before arming and stands down
 *    with a log line when no entry of type 3 is free.
 *    ROUND END (key EndSeconds): with the human as police nothing ends the round when the last criminal is gone
 *    (the bots' kill rule 0x485740 has no such test); it would run to the clock (600 s from the round start,
 *    0x8c7a8b). When record 0 is in play as police and no other record is in play, waiting or aboard, the hook
 *    writes once what slot 42 writes: [rules+0x4c] = [rules+0x200] = [score+0x40] = EndSeconds, if the clock is
 *    later than that. Slot 192 then ends the round by itself (and takes the life: a fed did not escape).
 *    NOT DONE, on purpose: giving the life back; a second return (8 bodies, one per respawn); choosing the body
 *    (record +0x14 written beforehand); anything on a stock level.
 *
 * 3. THE AI HEISTERS (key Bots; needs a build made by tools\kl_fa_fed.py)
 *    That build parks one police squad per heister (ZSquadScript field 3 = 0: not in the world) and names its hunt
 *    rout in the heister squad's field 8, the list ZSquadScript's update (slot 25 = 0x47e440) sends through
 *    0x87ebf0 when the squad's count of living men reaches 0. THE CATCH (0x71adc0): 'living' is actor+0x576 != 0
 *    and actor+0x8f0 == 0 and actor+0x5cd == 0, and the boarding rule sets actor+0x8f0 = 1 (0x684253): a heister
 *    who BOARDS the escape vehicle releases his fed as well. With Bots=0 the hook leaves that as it is.
 *    Bots=1 makes it deaths only, with two data writes per heister. The script object is reached from the crew
 *    record by pointers, every step checked:
 *        actor   = [record + 4]            vtable 0xbb3bac ZFFActor
 *        soldier = [actor + 0x77c]         [soldier + 0x40] == actor                  (0x7b390a, 0x7b3963)
 *        squad   = [soldier + 0x4f4]       vtable 0xbccdac ZSquad@CPPScript           (0x7b3966)
 *        script  = [squad + 0x164] - 0xe8  vtable 0xbcce3c ZSquadScript, [script + 0x3c] == squad,
 *                                          [squad + 0x168] == script + 0x104          (0x6316b0, 0x7697f1)
 *        and the script's member list [script+0x4c] .. [script+0x50] holds exactly this actor, [script+0x48] == 1.
 *    The update looks at its lists only when living < [script+0x40], and sends field 8 when living == 0 and the
 *    byte [script+0x20b] is 0 (0x47e472, 0x47e509; 0x87ebf0 sets the byte). So:
 *        heister in play, first seen:   byte [script+0x20b] = 1       muted: boarding and death send nothing
 *        his record becomes 7 (dead):   byte [script+0x20b] = 0 ; dword [script+0x40] = 1
 *                                       -> the game's next update sends field 8 once and sets the byte again
 *    The hook then watches the byte come back to 1 ('the game sent the list') for 5 s and says which.
 *    Bots=2 mutes only: no AI fed at all on such a build (the control run).
 *    ASSUMPTIONS, said plainly: that the script's update still runs once its only man is dead (if the 'sent' line
 *    never comes, it does not: use Bots=0); that nothing else reads [script+0x20b] / +0x40 in Arcade (found: the
 *    constructor 0x455c60, slots 14, 21, 22, 25 and 0x87ebf0); how Arcade resets squads between two rounds on the
 *    same loaded level is not known - the hook walks the chain again whenever a record is in play again.
 *    On a build without the level data the two writes send an empty list: nothing happens.
 *    NOT POSSIBLE, so not written: an AI heister through the player's path (0x4b28d0 ends in 0x537700, which
 *    rewrites the LOCAL player index: the human would be moved into that body); a dead actor standing up as
 *    police (no routine found); releasing a squad by the hook alone (that is a message to a rout = a game call).
 *
 * KLHook.ini
 *   [Fed]
 *   Enable=0          1 = this file is on (then only the log; each part below has its own key)
 *   Log=1             0 none, 1 the round's table and every change, 2 also a line a second
 *   Player=0          1 = the dead player comes back as police (section 2)
 *   MinCrew=1         AI heisters that must be in play for the player's return to be armed
 *   EndSeconds=3      the hook's round end when a police human has nobody left to hunt; 0 = leave it to the clock
 *   Nudge=1           the fed's OBJECTIVE line in the log (reads only; 0 = off): while you are a fed and have stood NudgeIdle=12 s, or the nearest live AI
 *                     heister is NudgeFar=6000 units (60 m) away, 'fed: OBJECTIVE: hunt record N ... offset x/y/z' every NudgeEvery=12 s. There is NO on-screen
 *                     part: that needs the HUD module (klhud*.c, not this file's) - this is the data a marker would use.
 *   Bots=0            0 = the level data alone (a fed at the heister's death AND when he boards), 1 = deaths only,
 *                     2 = muted: no AI fed (section 3)
 *
 * LOG (prefix 'fed:'; the lead's live checks F0..F6 are in re\fed.md with the line that proves each)
 *   fed: on; Player=1 MinCrew=1 EndSeconds=3 Bots=1 ...
 *   fed: round N: rules ..., K crew records (A AI), record 0 police index ff, local player object P ...
 *   fed: police bodies: entry 9 player ... type 3 used 0 police 0 model 1919 | ...   (8 of type 3, 8 free)
 *   fed: ARMED: your death will not end the round (A AI heisters in play, F police bodies free)
 *   fed: stood down: <why>
 *   fed: you: status 0 -> 1 (dead, waiting to return as police; countdown 5.0 s)
 *   fed: YOU ARE A FED: local player object 9 (type 3, police byte 1) at (x, y, z); client flags ... ; body 9 used
 *   fed: YOU STAND at (x, y, z) 5xx ms after you became police (object ...)      <- the place to judge by: the line
 *        above is printed in the tick the pointer changes and can read (0, 0, 0) or the body's parked place
 *   fed: nobody is left to hunt: the round clock 412.0 s -> 3.0 s
 *   fed: bot 3: squad script ... (squad ..., 1 man, latch 0, count 1): MUTED
 *   fed: bot 3 is DEAD: latch 0 and count 1 written: the game sends its 'wiped out' list at the next update
 *   fed: bot 3: the game sent the list after 16 ms (latch 1 again): its fed is released
 *   fed: bot 3: the latch is still 0 after 5 s: the squad script's update does not run for a dead squad
 *   fed: bot 5 is aboard: muted, no fed
 *
 * TESTED OFF-GAME ONLY (2026-10-10; scratch program klfed_test.c: this file included as it is over made-up session,
 * rules, score, handler, player-table, player, actor, soldier, squad and script objects, with the kill rule's two
 * branches simulated): armed / not armed in every case of section 2, the stand-down without a free body, nothing
 * written on a stock or unknown level and with the guard off, ON never from the fallback thread, the round-end
 * write once, mute / release / 'sent' / time-out, every refusal of the chain. That proves this file's own logic
 * and nothing about the game.
 *
 * THE LEAD'S THREE LINES IN klhook.c (compiled that way in a scratch copy, SHIP and TEST):
 *   #include "klfed.c"           after  #include "klbot.c"
 *   klp_tick(game_thread);       in klh_tick, after  klb_tick(game_thread);
 *   klp_init();                  in DllMain, after  klb_init();
 * and the [Fed] block above in klhook\KLHook.ini, a row 'klfed.c  x  x  the dead return as police (data only)' in
 * the file table, and two rows in the patch-site table: '0x168ea60  round-never-ends switch = 1 / 0  ST  .data
 * 0 checks  NOT RUN' and '[script]+0x20b, +0x40  squad script latch / count  ST  heap  outside  NOT RUN'.
 */
#ifndef KLFED_C
#define KLFED_C

#define KLP_SESSION    0x0168e598             /* +4 the session handler, +0x54, +0x5c = mode (4 = Arcade), +0x70 = state */
#define KLP_SETTINGS   0x0168e9e4             /* +0x54 = the rules object */
#define KLP_SWITCH     0x0168ea60             /* the gate's developer variable: not 0 = 'the round is not over' */
#define KLP_GATE       0x0067f480             /* 'is the round over?' */
#define KLP_RULES_VT   0x00bd3514             /* ZGameRulesHeist */
#define KLP_HANDLER_VT 0x00bd1be4             /* ZSessionHandlerSP */
#define KLP_PLAYER_VT  0x00bb45f4             /* ZFFPlayer */
#define KLP_ACTOR_VT   0x00bb3bac             /* ZFFActor */
#define KLP_SQUAD_VT   0x00bccdac             /* ZSquad@CPPScript */
#define KLP_SCRIPT_VT  0x00bcce3c             /* ZSquadScript */
#define KLP_NREC       32
#define KLP_NBODY      64
#define KLP_ROUND      0x19
#define KLP_T(t)       ((t) ? (t) : 1)        /* a time stamp that is never 0 */

/* klsteam.c is included after this file (klhook.c): the level gate of section 0 */
static int klx_on;
static int klx_level_verdict(const char *scene, char *why);          /* 0 no level, 1 stock, 2 not stock, 3 not known; why[200] */

static struct { int on, log, player, mincrew, bots, nudge, nudge_idle, nudge_every; float end, nudge_far; } klp;   /* nudge*: section 4 (the fed's objective line) */

struct klp_rec { int used, ai; DWORD at, actor, client, cflags; BYTE status, cam, body, local, index; float wait; };
struct klp_snap {
    DWORD sm, rules, score, state, handler, table, player; int n, human, ai_play, ai_n;
    BYTE veh, sel, ptype, ppolice; float clock, feet[3];
    struct klp_rec r[KLP_NREC];
};
struct klp_bodies { int n, type3, free_, first; };

static struct {                               /* what is remembered of the round */
    DWORD rules, state; int round, ended, ours, told_thread, told_foreign, was_fed;
    const char *why; struct klp_rec h; DWORD player; int have_h;
    DWORD fed_t, fed_p;                       /* when and as which object he became police: the second place line (below) */
} klp_r;
static struct { DWORD at, actor, squad, script, since; BYTE state, status; } klp_b[KLP_NREC];
enum { KLP_NONE, KLP_MUTED, KLP_RELEASED, KLP_SENT, KLP_REFUSED, KLP_TIMEOUT, KLP_LATE };

static int klp_finite(float f) { return f == f && f > -1e9f && f < 1e9f; }
static int klp_put8(DWORD at, BYTE v, const char *what) { return klh_data((void *)(DWORD_PTR)at, &v, 1, what); }
static int klp_put32(DWORD at, DWORD v, const char *what) { return klh_data((void *)(DWORD_PTR)at, &v, 4, what); }
static int klp_putf(DWORD at, float v, const char *what) { return klh_data((void *)(DWORD_PTR)at, &v, 4, what); }

/* ---------------------------------------------------------------- reading */

/* -> 1 and *s when an Arcade session with a ZGameRulesHeist object is up (whatever the session state) */
static int klp_read(struct klp_snap *s)
{
    DWORD gs, recs, freeb, sub = 0, n = 0, gd; BYTE raw[0x7c], b = 0, cl[2]; int i;
    memset(s, 0, sizeof *s); s->human = -1; s->sel = 0xff;
    if (!(s->sm = klh_rd32((DWORD_PTR)KLH_VA(KLP_SESSION))) || klh_rd32(s->sm + 0x5c) != 4 || !klh_rd(s->sm + 0x54, &sub, 4) || sub == 2 || sub == 3) return 0;
    if (!klh_rd(s->sm + 0x70, &s->state, 4)) return 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLP_SETTINGS))) || !(s->rules = klh_rd32(gs + 0x54)) || klh_rd32(s->rules) != KLP_RULES_VT) return 0;
    if (!klh_rd(s->rules + 0x354, &n, 4) || !n || n > KLP_NREC) return 0;
    if (!(recs = klh_rd32(s->rules + 0x348)) || !(freeb = klh_rd32(s->rules + 0x34c)) || !(s->score = klh_rd32(s->rules + 0x5f8))) return 0;
    if (!klh_rd(s->rules + 0x1dc, &s->veh, 1) || !klh_rd(s->rules + 0x200, &s->clock, 4)) return 0;
    s->n = (int)n;
    for (i = 0; i < s->n; i++) {
        struct klp_rec *r = &s->r[i];
        if (!klh_rd(freeb + i, &b, 1) || b || !klh_rd(recs + 0x7c * i, raw, sizeof raw)) continue;
        r->used = 1; r->at = recs + 0x7c * i; r->client = *(DWORD *)raw; r->actor = *(DWORD *)(raw + 4);
        r->wait = *(float *)(raw + 8); r->status = raw[0x10]; r->cam = raw[0x11]; r->body = raw[0x14]; r->ai = raw[0x79] & 1;
        r->local = 0; r->index = 0xff;
        if (!r->ai && r->client && klh_rd(r->client, cl, 2)) { r->local = cl[0] == 0; r->index = cl[1]; }
        if (r->index < 12) klh_rd(s->score + 0x1d4 + 4 * r->index, &r->cflags, 4);
        if (r->ai) { s->ai_n++; s->ai_play += r->status == 0; }
        else if (s->human < 0) s->human = i;
    }
    /* the handler and its player table (ZSessionHandlerSP only: the multiplayer handler is another class) */
    if ((s->handler = klh_rd32(s->sm + 4)) != 0 && klh_rd32(s->handler) == KLP_HANDLER_VT) s->table = klh_rd32(s->handler + 8);
    else s->handler = 0;
    /* the local player (0x660b00): [gamedata + 0x828 + 4 * (char)[gamedata + 0x898]] */
    if ((gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) != 0 && klh_rd(gd + 0x898, &s->sel, 1) && s->sel < 28 &&
        (s->player = klh_rd32(gd + 0x828 + 4 * s->sel)) != 0 && klh_pvt(s->player) == KLP_PLAYER_VT &&
        klh_rd(s->player + 0x273c, &s->ptype, 1) && klh_rd(s->player + 0x2723, &s->ppolice, 1)) {
        if (!klh_rd(s->player + 0x460, s->feet, 12)) memset(s->feet, 0, sizeof s->feet);
    } else s->player = 0;
    return 1;
}

/* Section 0: is the level that runs now seen and NOT the stock one? why[200] says which. */
static int klp_level(char why[200])
{
    char scene[160], w[200]; int v;
    if (!klx_on) { strcpy(why, "the Steam write guard is not on, so no level archive is judged"); return 0; }
    if (!klh_scene(scene, sizeof scene)) { strcpy(why, "there is no scene name"); return 0; }
    v = klx_level_verdict(scene, w);
    if (v == 2) { snprintf(why, 200, "this level is not the stock one (%.150s)", w); return 1; }
    if (v == 1) strcpy(why, "this level is the STOCK one of its slot");
    else if (v == 3) snprintf(why, 200, "this level is not known (%.150s)", w);
    else snprintf(why, 200, "the scene '%.100s' is no level", scene);
    return 0;
}

/* The session's player table: how many police bodies (type 3) there are and how many are free, as the game's pick
   0x54cab0 counts them. line (may be 0, 900 bytes): the entries in words. -> 0 when the table cannot be read. */
static int klp_count(const struct klp_snap *s, struct klp_bodies *o, char *line)
{
    DWORD ents, slots, n = 0, i, model; BYTE e[12], slot, type, pol; int k = 0;
    memset(o, 0, sizeof *o); o->first = -1;
    if (line) line[0] = 0;
    if (!s->table || !(ents = klh_rd32(s->table)) || !(slots = klh_rd32(s->table + 4)) || !klh_rd(s->table + 0xc, &n, 4) || !n || n > KLP_NBODY) return 0;
    o->n = (int)n;
    for (i = 0; i < n; i++) {
        DWORD pl;
        if (!klh_rd(slots + i, &slot, 1) || !klh_rd(ents + 12 * i, e, 12)) return 0;
        if (slot) continue;                                   /* the slot is not in use */
        pl = *(DWORD *)(e + 4);
        if (!pl || klh_pvt(pl) != KLP_PLAYER_VT || !klh_rd(pl + 0x273c, &type, 1) || !klh_rd(pl + 0x2723, &pol, 1)) {
            if (line && k < 820) k += snprintf(line + k, 900 - k, "%s%lu NOT a ZFFPlayer (%08lx)", k ? " | " : "", i, pl);
            continue;
        }
        if (type == 3) { o->type3++; if (!e[9]) { o->free_++; if (o->first < 0) o->first = (int)i; } }
        if (line && k < 820 && (type == 3 || pl == s->player)) {
            model = klh_rd32(klh_rd32(pl + 4) + 0x68);
            k += snprintf(line + k, 900 - k, "%s%lu %08lx type %u used %u police %u model %lu%s", k ? " | " : "", i, pl, type, e[9], pol, model, pl == s->player ? " = YOU" : "");
        }
    }
    return 1;
}

/* ---------------------------------------------------------------- the player (section 2) */

static void klp_switch(int want, int game_thread, const char *why, const struct klp_snap *s, const struct klp_bodies *b)
{
    static const BYTE gate[12] = { 0x83, 0x3d, 0x60, 0xea, 0x68, 0x01, 0x00, 0x56, 0x8b, 0xf1, 0x74, 0x04 };   /* cmp dword [0x168ea60],0 ; push esi ; mov esi,ecx ; je +4 */
    BYTE code[12]; DWORD cur = 0xffffffff;
    if (!klh_rd((DWORD_PTR)KLH_VA(KLP_SWITCH), &cur, 4)) return;
    if (cur > 1 || (cur == 1 && !klp_r.ours)) {               /* not ours: never touched */
        if (!klp_r.told_foreign++) klog("fed: the dword at %08x holds %lu, which this hook did not write: it is left alone and the player's return is off", KLP_SWITCH, cur);
        return;
    }
    if (want && (!klh_rd((DWORD_PTR)KLH_VA(KLP_GATE), code, sizeof code) || memcmp(code, gate, sizeof gate))) { want = 0; why = "the round-over test at 0067f480 is not the code this build knows"; }
    if (want && !game_thread && !cur) {                       /* ON only between two frames of the game itself */
        if (!klp_r.told_thread++) klog("fed: the tick is not on the game's thread ([KLHook] Tick=0?): the player's return cannot be armed");
        return;
    }
    if ((DWORD)want != cur) {
        if (!klp_put32((DWORD)(DWORD_PTR)KLH_VA(KLP_SWITCH), (DWORD)want, "the round-over test's switch (zero-filled .data)")) {
            if (klp_r.why != (const char *)1) { klp_r.why = (const char *)1; klog("fed: the dword at %08x could NOT be written (%s)", KLP_SWITCH, want ? "arming" : "standing down"); }
            return;
        }
        klp_r.ours = want;
    }
    if (why != klp_r.why) {                                   /* said when the reason changes (the texts are literals) */
        klp_r.why = why;
        if (!klp.log) return;
        if (want) klog("fed: ARMED: your death will not end the round - you come back as police (%d AI heister(s) in play, %d of %d police bodies free)", s ? s->ai_play : 0, b ? b->free_ : 0, b ? b->type3 : 0);
        else klog("fed: stood down: %s", why);
    }
}

/* what is said about record 0 and the local player when it changes: the proof lines of checks F1 - F4 */
static void klp_say_human(const struct klp_snap *s, const struct klp_bodies *b)
{
    const struct klp_rec *h = s->human >= 0 ? &s->r[s->human] : 0, *p = &klp_r.h;
    static const char *const st[8] = { "in play", "dead, waiting to return as police", "status 2", "status 3 (timed, then spectating)", "aboard", "escaped", "escaped", "dead for good" };
    if (!h || !klp.log) return;
    if (klp_r.have_h && (h->status != p->status || h->body != p->body || ((h->cflags ^ p->cflags) & 0x41fc))) {
        if (h->status != p->status) klog("fed: you: status %u -> %u (%s; countdown %.1f s, death camera phase %u, client flags %08lx, police index %02x)", p->status, h->status, st[h->status & 7], klp_finite(h->wait) ? h->wait : -1.0f, h->cam, h->cflags, h->body);
        else klog("fed: you: client flags %08lx -> %08lx, police index %02x -> %02x (status %u)", p->cflags, h->cflags, p->body, h->body, h->status);
    }
    if (klp_r.have_h && s->player != klp_r.player) {
        if (s->player && s->ppolice) {
            klp_r.was_fed = 1;
            klog("fed: YOU ARE A FED: local player object %u (%08lx, type %u, police byte %u) at (%.0f, %.0f, %.0f); client flags %08lx, record 0 status %u, police index %02x; %d of %d police bodies still free", s->sel, s->player, s->ptype, s->ppolice,
                 s->feet[0], s->feet[1], s->feet[2], h->cflags, h->status, h->body, b ? b->free_ : -1, b ? b->type3 : -1);
            klp_r.fed_t = KLP_T(GetTickCount()); klp_r.fed_p = s->player;
        } else klog("fed: the local player is now object %u (%08lx, type %u, police byte %u) at (%.0f, %.0f, %.0f)", s->sel, s->player, s->ptype, s->ppolice, s->feet[0], s->feet[1], s->feet[2]);
    }
    /* The line above is printed in the tick the local player pointer changes, and on some maps that is before the
       game has placed the body (the owner's log 2026-10-11: 'at (0, 0, 0)' at 12:43:29, 12:44:04, 15:06:59, 15:14:34).
       So the place is said once more half a second later: the line the live checks of re\fed_points.md 6 are read by.
       A read of the same three floats, nothing written. */
    if (klp_r.fed_t && GetTickCount() - klp_r.fed_t >= 500) {
        if (s->player && s->player == klp_r.fed_p)
            klog("fed: YOU STAND at (%.0f, %.0f, %.0f) %lu ms after you became police (object %08lx): where the game put you (the line above can read a tick early)",
                 s->feet[0], s->feet[1], s->feet[2], (unsigned long)(GetTickCount() - klp_r.fed_t), s->player);
        klp_r.fed_t = 0;
    }
    klp_r.h = *h; klp_r.player = s->player; klp_r.have_h = 1;
}

static void klp_player_tick(const struct klp_snap *s, int act, const char *lvwhy, int game_thread)
{
    const struct klp_rec *h = s->human >= 0 ? &s->r[s->human] : 0; struct klp_bodies b; const char *why; int want = 0, have, i, left = 0;
    have = klp_count(s, &b, 0);
    klp_say_human(s, have ? &b : 0);
    if (!klp.player) return;
    if (!act) why = lvwhy;                                    /* the caller's text lives as long as the answer (a static buffer) */
    else if (s->state != KLP_ROUND) why = "no round is running";
    else if (!h || s->human != 0 || !h->local || h->index != 0) why = "record 0 is not the local human";
    else if (!s->handler) why = "the session handler is not ZSessionHandlerSP";
    else if (h->status == 1) { want = 1; why = "armed (waiting)"; }      /* dead and waiting: held until he stands */
    else if (!s->player) why = "there is no local player object";
    else if (h->status == 4) why = "you are aboard the escape vehicle";
    else if (h->status != 0) why = "you are out of the round (escaped or dead for good)";
    else if (s->ppolice) why = "you are police";
    else if (s->ptype != 2) why = "the local player is not a heister object";
    else if (h->cflags & 0x88) why = "your client flags do not allow a return (police or 0x80)";
    else if (s->ai_play < klp.mincrew) why = "too few AI heisters are in play (MinCrew): nobody to hunt";
    else if (!have) why = "the session's player table cannot be read";
    else if (!b.free_) why = b.type3 ? "NO FREE POLICE BODY is left in this level load (each return takes one of 8; the game has an int3 there): your death is the stock one" : "this level has no police player object";
    else { want = 1; why = "armed"; }
    klp_switch(want, game_thread, why, s, &b);
    /* ---- the round end, when a police human has nobody left to hunt */
    if (!act || !game_thread || s->state != KLP_ROUND || klp.end <= 0 || klp_r.ended || !h || h->status != 0 || !s->ppolice || !(h->cflags & 8)) return;
    for (i = 0; i < s->n; i++) if (i != s->human && s->r[i].used && (s->r[i].status == 0 || s->r[i].status == 1 || s->r[i].status == 3 || s->r[i].status == 4)) left++;
    if (left) return;
    klp_r.ended = 1;
    if (!klp_finite(s->clock) || s->clock <= klp.end) { klog("fed: nobody is left to hunt; the round clock is at %.1f s already: nothing written", klp_finite(s->clock) ? s->clock : -1.0f); return; }
    if (klp_putf(s->rules + 0x200, klp.end, "round end timer (as slot 42 / 193 write it)")) {
        klp_putf(s->rules + 0x4c, klp.end, "round clock (slot 42)"); klp_putf(s->score + 0x40, klp.end, "round clock on the score object (slot 42)");
        klog("fed: nobody is left to hunt: the round clock %.1f s -> %.1f s (vehicle state %u; the game's own end takes the life: a fed did not escape)", s->clock, klp.end, s->veh);
    } else klog("fed: nobody is left to hunt, but the round clock could NOT be written: the round runs to its clock (%.0f s)", s->clock);
}

/* ---------------------------------------------------------------- the AI heisters (section 3) */

/* crew record's actor -> its one-man squad's script, every step checked. -> 1, or 0 and why[100] */
static int klp_chain(DWORD actor, DWORD *squad, DWORD *script, char why[100])
{
    DWORD soldier, sq, lists, sc, mb = 0, me = 0, n = 0;
    *squad = *script = 0;
    if (!actor || klh_rd32(actor) != KLP_ACTOR_VT) { snprintf(why, 100, "its actor %08lx is not a ZFFActor (vtable %08lx)", actor, actor ? klh_rd32(actor) : 0); return 0; }
    if (!(soldier = klh_rd32(actor + 0x77c)) || klh_rd32(soldier + 0x40) != actor) { snprintf(why, 100, "actor +0x77c (%08lx) is not its soldier", soldier); return 0; }
    if (!(sq = klh_rd32(soldier + 0x4f4)) || klh_rd32(sq) != KLP_SQUAD_VT) { snprintf(why, 100, "soldier +0x4f4 (%08lx) is not a ZSquad", sq); return 0; }
    lists = klh_rd32(sq + 0x164); sc = lists - 0xe8;
    if (lists < 0x10000 + 0xe8 || klh_rd32(sc) != KLP_SCRIPT_VT || klh_rd32(sc + 0x3c) != sq || klh_rd32(sq + 0x168) != sc + 0x104) { snprintf(why, 100, "squad %08lx +0x164 (%08lx) does not lead to its ZSquadScript", sq, lists); return 0; }
    if (!klh_rd(sc + 0x4c, &mb, 4) || !klh_rd(sc + 0x50, &me, 4) || !klh_rd(sc + 0x48, &n, 4) || n != 1 || me - mb != 4 || klh_rd32(mb) != actor) { snprintf(why, 100, "squad script %08lx is not a one-man squad of this actor (%lu man, list of %lu)", sc, n, (me - mb) / 4); return 0; }
    *squad = sq; *script = sc;
    return 1;
}

static int klp_script_ok(int i)
{
    DWORD n = 0;
    return klp_b[i].script && klh_rd32(klp_b[i].script) == KLP_SCRIPT_VT && klh_rd32(klp_b[i].script + 0x3c) == klp_b[i].squad && klh_rd(klp_b[i].script + 0x48, &n, 4) && n == 1;
}

static void klp_bots_tick(const struct klp_snap *s, DWORD now)
{
    int i; char why[100];
    for (i = 1; i < s->n; i++) {
        const struct klp_rec *r = &s->r[i]; BYTE latch = 0; DWORD cnt = 0;
        if (!r->used || !r->ai) { if (klp_b[i].at) memset(&klp_b[i], 0, sizeof klp_b[i]); continue; }
        if (klp_b[i].at != r->at || klp_b[i].actor != r->actor || (r->status == 0 && klp_b[i].status != 0)) {      /* a new record, a new actor, or in play again = a new round */
            memset(&klp_b[i], 0, sizeof klp_b[i]); klp_b[i].at = r->at; klp_b[i].actor = r->actor; klp_b[i].status = 0xff;
        }
        if (klp_b[i].state == KLP_NONE) {
            if (r->status != 0) {                             /* first seen out of play: its squad was never muted by us */
                klp_b[i].state = KLP_LATE; klp_b[i].status = r->status;
                if (klp.log) klog("fed: bot %d was first seen with status %u: its squad is left as it is", i, r->status);
                continue;
            }
            if (!klp_chain(r->actor, &klp_b[i].squad, &klp_b[i].script, why)) {
                klp_b[i].state = KLP_REFUSED; klp_b[i].status = r->status;
                klog("fed: bot %d: %s: its squad is left alone (the level data acts by itself)", i, why);
                continue;
            }
            klh_rd(klp_b[i].script + 0x20b, &latch, 1); klh_rd(klp_b[i].script + 0x40, &cnt, 4);
            if (!latch && !klp_put8(klp_b[i].script + 0x20b, 1, "squad script: the 'wiped out' latch (muted)")) {
                klp_b[i].state = KLP_REFUSED; klp_b[i].status = r->status;
                klog("fed: bot %d: squad script %08lx could NOT be written: left alone", i, klp_b[i].script);
                continue;
            }
            klp_b[i].state = KLP_MUTED;
            if (klp.log) klog("fed: bot %d (actor %08lx): squad script %08lx (squad %08lx, 1 man, latch %u, count %lu): MUTED - %s", i, r->actor, klp_b[i].script, klp_b[i].squad, latch, cnt,
                              klp.bots == 1 ? "its 'wiped out' list is sent at its death only, not when it boards" : "Bots=2: no fed for this heister");
        }
        if (klp_b[i].state == KLP_MUTED && r->status != klp_b[i].status && klp_b[i].status != 0xff) {
            if (r->status == 7 && klp.bots == 1) {
                if (!klp_script_ok(i)) { klp_b[i].state = KLP_REFUSED; klog("fed: bot %d is DEAD, but its squad script %08lx is no longer the object it was: nothing written", i, klp_b[i].script); }
                else if (klp_put8(klp_b[i].script + 0x20b, 0, "squad script: the 'wiped out' latch (released)") && klp_put32(klp_b[i].script + 0x40, 1, "squad script: last count of living men")) {
                    klp_b[i].state = KLP_RELEASED; klp_b[i].since = KLP_T(now);
                    klog("fed: bot %d is DEAD: latch 0 and count 1 written to squad script %08lx: the game sends its 'wiped out' list at the next update", i, klp_b[i].script);
                } else { klp_b[i].state = KLP_REFUSED; klog("fed: bot %d is DEAD, but squad script %08lx could NOT be written", i, klp_b[i].script); }
            } else if (klp.log) klog("fed: bot %d is %s: muted, no fed", i, r->status == 4 ? "aboard" : r->status == 7 ? "dead" : "out of play");
        } else if (klp_b[i].state == KLP_RELEASED) {
            if (klh_rd(klp_b[i].script + 0x20b, &latch, 1) && latch) {
                klp_b[i].state = KLP_SENT;
                klog("fed: bot %d: the game sent the list after %lu ms (latch 1 again): its fed is released, if the level has one", i, now - klp_b[i].since);
            } else if (now - klp_b[i].since >= 5000) {
                klp_b[i].state = KLP_TIMEOUT;
                klog("fed: bot %d: the latch is still 0 after 5 s: the squad script's update does not run for a dead squad - no fed by this way (use Bots=0)", i);
            }
        }
        klp_b[i].status = r->status;
    }
}

/* Where a fed stands (w_fedmove, 2026-10-14; the owner on Retomoto: 'fed gets stuck in elevator'). READS ONLY, a log line.
   The one fed of his evening who came back in the tower (20:16:26, (2605, 19601, -176)) had a crew that had gone down by
   [CrewHop] meanwhile; he walked 77 s, took the join box (20:17:43) and was dead 1.9 s after the jump - where he stood in
   those 77 s the log does not say. So, while you are a fed in play:
   - 'fed: you have stood N s at (x, y, z)': you have not moved 1 m for 10 s (once per spot, again after 30 s more);
   - 'fed: you are on another level of height than the whole crew': every AI heister in play is more than 5000 above or
     below you (Retomoto: the tower 19600 .. 21000, the street -50 .. 570) - once a life; and when it ends.
   The crew's places: [actor + 0x460] (klcrew_rt.c's 'feet', an ASSUMPTION it states; the hop lines read it as the node). */
static struct { DWORD player, since, said, nudged; float at[3]; int apart; } klp_w;

static void klp_where(const struct klp_snap *s)
{
    const struct klp_rec *h = s->human >= 0 ? &s->r[s->human] : 0; DWORD now = GetTickCount(); float d2, ft[3], dy, mindy = 1e9f; int i, n = 0, apart;
    if (!klp.log || s->state != KLP_ROUND || !h || h->status != 0 || !s->player || !s->ppolice || !klp_finite(s->feet[0]) || !klp_finite(s->feet[1]) || !klp_finite(s->feet[2])) { klp_w.player = 0; return; }
    if (s->player != klp_w.player) { memset(&klp_w, 0, sizeof klp_w); klp_w.player = s->player; klp_w.since = KLP_T(now); memcpy(klp_w.at, s->feet, 12); }
    d2 = (s->feet[0] - klp_w.at[0]) * (s->feet[0] - klp_w.at[0]) + (s->feet[1] - klp_w.at[1]) * (s->feet[1] - klp_w.at[1]) + (s->feet[2] - klp_w.at[2]) * (s->feet[2] - klp_w.at[2]);
    if (d2 > 100.0f * 100.0f) {
        if (klp_w.said) klog("fed: you move again after %.0f s at (%.0f, %.0f, %.0f)", (now - klp_w.since) / 1000.0, klp_w.at[0], klp_w.at[1], klp_w.at[2]);
        klp_w.since = KLP_T(now); klp_w.said = 0; memcpy(klp_w.at, s->feet, 12);
    } else if (now - klp_w.since >= 10000 && (!klp_w.said || now - klp_w.said >= 30000)) {
        klp_w.said = KLP_T(now);
        klog("fed: you have stood %.0f s at (%.0f, %.0f, %.0f) (within 1 m; local player object %u)", (now - klp_w.since) / 1000.0, s->feet[0], s->feet[1], s->feet[2], s->sel);
    }
    {   /* section 4: the fed's objective (2026-10-18, overnight audit: 'the fed stands idle 10 to 29 s repeatedly, no clear job'): the nearest LIVE heister */
        int bi = -1; float bd = 1e9f, bp[3] = {0, 0, 0};
        for (i = 0; i < s->n; i++) {
            const struct klp_rec *r = &s->r[i];
            if (!r->used || !r->ai || r->status || !r->actor || !klh_rd(r->actor + 0x460, ft, 12) || !klp_finite(ft[1]) || (!ft[0] && !ft[1] && !ft[2])) continue;
            n++; dy = (float)fabs(ft[1] - s->feet[1]); if (dy < mindy) mindy = dy;
            { float dx = ft[0] - s->feet[0], dz = ft[2] - s->feet[2], dd = (float)sqrt(dx * dx + dy * dy + dz * dz); if (klp_finite(dd) && dd < bd) { bd = dd; bi = i; memcpy(bp, ft, 12); } }
        }
        if (klp.nudge && bi >= 0 && (now - klp_w.since >= (DWORD)klp.nudge_idle * 1000 || bd >= klp.nudge_far) && (!klp_w.nudged || now - klp_w.nudged >= (DWORD)klp.nudge_every * 1000)) {
            float dx = bp[0] - s->feet[0], dz = bp[2] - s->feet[2];      /* world units; which way the camera looks is not read, so the offset is given per axis */
            klp_w.nudged = KLP_T(now);
            klog("fed: OBJECTIVE: hunt record %d, the nearest of %d heister(s) still in play: %.0f m away, offset x %+.0f m, y %+.0f m, z %+.0f m, at (%.0f, %.0f, %.0f); %s (stood %.0f s)", bi, n, bd / 100, dx / 100, (bp[1] - s->feet[1]) / 100, dz / 100,
                 bp[0], bp[1], bp[2], bd >= klp.nudge_far ? "you are far from the crew" : "you are standing still", (now - klp_w.since) / 1000.0);
        }
    }
    apart = n && mindy > 5000.0f;
    if (apart != klp_w.apart) {
        if (apart) klog("fed: you are on another level of height than the whole crew: you at (%.0f, %.0f, %.0f), the nearest of %d AI heister(s) in play %.0f above or below (Retomoto: only the join box before the tower car takes you down)",
                        s->feet[0], s->feet[1], s->feet[2], n, mindy);
        else if (klp_w.apart == 1) klog("fed: you are at the crew's level of height again: (%.0f, %.0f, %.0f)", s->feet[0], s->feet[1], s->feet[2]);
        klp_w.apart = apart;
    }
}

/* ---------------------------------------------------------------- the tick */

static void klp_round_line(const struct klp_snap *s)
{
    struct klp_bodies b; char line[900]; const struct klp_rec *h = s->human >= 0 ? &s->r[s->human] : 0;
    klog("fed: round %d: rules %08lx, %d crew record(s), %d AI (%d in play), record 0 %s, status %u, police index %02x, client flags %08lx; local player object %u (%08lx, type %u, police byte %u); round clock %.0f s",
         klp_r.round, s->rules, s->n, s->ai_n, s->ai_play, h && h->local ? "is the local human" : "is NOT the local human", h ? h->status : 0xff, h ? h->body : 0xff, h ? h->cflags : 0, s->sel, s->player, s->ptype, s->ppolice,
         klp_finite(s->clock) ? s->clock : -1.0f);
    if (!s->handler) klog("fed: police bodies: the session handler is not ZSessionHandlerSP (vtable %08lx): the table is not read", klh_rd32(klh_rd32(s->sm + 4)));
    else if (!klp_count(s, &b, line)) klog("fed: police bodies: the player table at %08lx cannot be read", s->table);
    else klog("fed: police bodies: %s   (%d entries, %d of type 3, %d free%s)", line, b.n, b.type3, b.free_, b.free_ ? "" : ": NONE FREE");
}

static void klp_tick(int game_thread)
{
    static DWORD last, lastline; static char lvwhy[200], told[200]; static DWORD toldrules;
    struct klp_snap s; DWORD now = GetTickCount(); char why[200]; int arcade, act = 0;
    if (!klp.on || !klh_exe_ok) return;
    if (game_thread ? now - last < 50 : now - last < 100) return;
    last = now;
    arcade = klp_read(&s);
    if (!arcade) {                                            /* no Arcade round object: nothing of ours may stay behind */
        if (klp.player) klp_switch(0, game_thread, "no Arcade session", 0, 0);
        klp_r.rules = 0; klp_r.have_h = 0; memset(klp_b, 0, sizeof klp_b);
        return;
    }
    if (s.rules != klp_r.rules || (s.state == KLP_ROUND && klp_r.state != KLP_ROUND)) {      /* a new round */
        int n = klp_r.round + 1, ours = klp_r.ours, tf = klp_r.told_foreign, tt = klp_r.told_thread; const char *w = klp_r.why;
        memset(&klp_r, 0, sizeof klp_r); klp_r.rules = s.rules; klp_r.round = n; klp_r.ours = ours; klp_r.told_foreign = tf; klp_r.told_thread = tt; klp_r.why = w;
        memset(klp_b, 0, sizeof klp_b);              /* review: a script pointer of the last round must not be written through (squads may be rebuilt) */
        if (s.state == KLP_ROUND && klp.log) klp_round_line(&s);
    }
    klp_r.state = s.state;
    if (klp.player || klp.bots) {
        act = klp_level(why);                                 /* asked every pass: the verdict changes when the archive is opened */
        if (s.rules != toldrules || strcmp(why, told)) {
            toldrules = s.rules; strcpy(told, why); strcpy(lvwhy, why);
            klog("fed: %s: Player / Bots %s", why, act ? "may act, as far as their keys are set; the Steam guard blocks every write of this round" : "do nothing here (they act only on a level that is not stock); the log runs");
        }
    }
    klp_player_tick(&s, act, lvwhy, game_thread);
    klp_where(&s);                                            /* a log line: where a fed stands (reads only) */
    if (klp.bots && act && game_thread && s.state == KLP_ROUND) klp_bots_tick(&s, now);
    if (klp.log >= 2 && now - lastline >= 1000) {
        const struct klp_rec *h = s.human >= 0 ? &s.r[s.human] : 0; DWORD sw = 0xffffffff;
        lastline = now; klh_rd((DWORD_PTR)KLH_VA(KLP_SWITCH), &sw, 4);
        klog("fed: s%lx clock %.0f s van %u | you status %u wait %.1f cam %u body %02x flags %08lx | player %u type %u police %u | AI %d in play of %d | switch %lu", s.state, klp_finite(s.clock) ? s.clock : -1.0f, s.veh,
             h ? h->status : 0xff, h && klp_finite(h->wait) ? h->wait : -1.0f, h ? h->cam : 0xff, h ? h->body : 0xff, h ? h->cflags : 0, s.sel, s.ptype, s.ppolice, s.ai_play, s.ai_n, sw);
    }
}

static void klp_init(void)
{
    char t[32]; int v;
    klp.on = GetPrivateProfileIntA("Fed", "Enable", 0, klh_ini) != 0;
    if (!klp.on) return;
    v = (int)GetPrivateProfileIntA("Fed", "Log", 1, klh_ini); klp.log = v < 0 ? 0 : v > 2 ? 2 : v;
    klp.player = GetPrivateProfileIntA("Fed", "Player", 0, klh_ini) != 0;
    v = (int)GetPrivateProfileIntA("Fed", "MinCrew", 1, klh_ini); klp.mincrew = v < 1 ? 1 : v > 31 ? 31 : v;
    v = (int)GetPrivateProfileIntA("Fed", "Bots", 0, klh_ini); klp.bots = v < 0 ? 0 : v > 2 ? 2 : v;
    GetPrivateProfileStringA("Fed", "EndSeconds", "3", t, sizeof t, klh_ini);
    klp.end = (float)atof(t); if (!klp_finite(klp.end) || klp.end < 0) klp.end = 0; else if (klp.end > 0 && klp.end < 1) klp.end = 1; else if (klp.end > 600) klp.end = 600;
    v = (int)GetPrivateProfileIntA("Fed", "Nudge", 1, klh_ini); klp.nudge = v != 0;      /* a log line only (reads): on by default */
    v = (int)GetPrivateProfileIntA("Fed", "NudgeIdle", 12, klh_ini); klp.nudge_idle = v < 3 ? 3 : v > 300 ? 300 : v;
    v = (int)GetPrivateProfileIntA("Fed", "NudgeEvery", 12, klh_ini); klp.nudge_every = v < 3 ? 3 : v > 300 ? 300 : v;
    GetPrivateProfileStringA("Fed", "NudgeFar", "6000", t, sizeof t, klh_ini); klp.nudge_far = (float)atof(t); if (!klp_finite(klp.nudge_far) || klp.nudge_far < 500) klp.nudge_far = 6000;
    klog("fed: on; Log=%d Player=%d (MinCrew=%d EndSeconds=%.0f) Bots=%d (%s); data writes only; Arcade only, and everything but the log only on a level that is not the stock one of its slot",
         klp.log, klp.player, klp.mincrew, klp.end, klp.bots, klp.bots == 1 ? "a heister's fed at his death only" : klp.bots == 2 ? "muted: no AI fed" : "the level data alone");
}

#endif /* KLFED_C */
