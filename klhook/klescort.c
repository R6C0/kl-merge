/*
 * klescort.c - ONE OR TWO AI HEISTERS STAY NEAR THE HUMAN PLAYER and fight beside him; the others keep their routes.
 * Owner, 2026-10-10: 'the backstab helping out via being next to you', 'make the ai heisters go like with lynch or
 * someone else random every time'. Part of KLHook (included by klhook.c after klbot.c, SHIP and TEST alike).
 * NO data write and no code byte: calls of ONE game function - the soldier's own 'defend this place' order, the one
 * the level scripts and the heist rules themselves give - from the game's own thread. Full account, the reading it
 * rests on and the live checks E0..E5: re\bots_escort.md. Everything below was read in kl2.exe build 0490 for this
 * file (debug\dasm.py, 2026-10-10). NOTHING HERE HAS RUN IN THE GAME. Off unless [Bots] Enable=1 AND Escort=1 or 2.
 *
 * 1. THE GAME'S MECHANISM (EXE = seen in the code)
 *    soldier = [actor + 0x77c] (set by the soldier's constructor 0x761900, `mov [edx+0x77c], esi`; the ONLY class
 *    is CPPScript::ZSoldier, vtable 0xbd0954, made by ZSoldierRout slot 13 = 0x622ae0), [soldier + 0x40] = the actor.
 *    [soldier + 0x64c] = the DEFEND POSITION, a 0x1c-byte block made in the soldier's slot 17 (0x6ab250; constructor
 *    0x40b540): +0 x y z, +0xc and +0x10 a move style and 'style given', +0x11 'changed', +0x12 'queued',
 *    +0x14 the soldier, +0x18 float 1.0. [soldier + 0x648] = the defend goal (+8 its state). EXE.
 *    THE ORDER: ZSoldier vtable +0x13c = 0x760e50 = void __thiscall (soldier, const float pos[3], char soft,
 *    char reset, char unused), ret 0x10. EXE, whole:
 *      - in a network session on a client: returns (Arcade is neither);
 *      - actor->vtable[0x620]() (0x86dba0: [actor + 0x770] != 0 = somebody holds this actor as a human shield):
 *        the place goes to another goal (soldier vtable +0x160). The hook never calls in that case;
 *      - soft2 = soft, but 1 when [soldier + 0xec] != 0 and the place is nearer than 250 units (squared distance
 *        under 62500.0, 0xb7eb28) - 'he is there already';
 *      - reset: [soldier + 0x720] = 0;   [soldier + 0x4fc] = soft2;
 *      - 0x412910 (defend block, pos): asks the pathfinder [[[0xdd2640] + 0xac] + 0xc] (vtable +0x80, then +0x84)
 *        for the place ON THE NAVIGATION MESH and stores that, or pos itself when the pathfinder has none.
 *        So the order snaps its own point: the hook needs no mesh query of its own. (ASSUMPTION for what the two
 *        virtual calls are - 'nearest polygon' and 'point on it'; the stored place is read back and logged.)
 *      - block +0x11 = 1; then: defend goal idle (state 0 or 4) -> soldier vtable +0x1b4 (0x6e49b0: every running
 *        goal is interrupted), the goal is queued (0x6cabf0, priority 150), vtable +0x50 (1); goal running and not
 *        soft2 -> 0x7bbf70 (the block is queued for a new plan); running and soft2 -> nothing more.
 *    WHO CALLS IT (38 call sites): ZDefendBehaviourGoal's run 0x686920 at 0x686bac / 0x686df2 with (place, 0, 1, 0)
 *    - this is what every Defend step of the bots' route chain does; ZDefendPlayerPosBehaviour 0x622d52 with (the
 *    nearest player's place, 0 on the first pass / 1 later, 1, 0); ZDefendNPCPos, ZDefendCurrentPos, ZMove, ZFlanking,
 *    ZLeapFrog, ZRunForHelp, ZGrenadeAttack goals the same way; the soldier's own tactics (ZAttackTarget,
 *    ZStayInCoverGoal, ZCloseInOnTarget) with (place, x, 0, 0); and - THE PRECEDENT FOR A CALL FROM OUTSIDE THE
 *    SOLDIER'S OWN SCRIPT - ZGameRulesHeist slot 194 (0x8fa6d0, the vehicle's state change) at 0x8fb04c: when the
 *    vehicle starts to WAIT (state 3 / 4) it walks the crew records exactly as this file does and, for every AI
 *    record (+0x79 mask 1) with heist stage >= 3 whose [actor + 0x77c] is not null:
 *        soldier->vtable[0x1b4]();  soldier->vtable[0x13c](&place, 1, 1, 0);
 *    with place = the boarding object's position + 500 along its own x axis (0x8faf72..0x8fafe6).
 *    HOW A DEFEND STEP WAITS (0x686c42..0x686ce1): for every member, until the actor's vtable +0x3d0 says yes, or
 *    [soldier + 0x4fc] != 0, or the member is within 10 or 1000 (by the goal's +0x40, not read further) of the step's place. Then the
 *    step is over and its NEXT list is triggered. So: a step whose man was sent elsewhere WAITS; a step whose man
 *    got a SOFT order (or an order to a place he is within 250 of) is OVER at once.
 *    Heist stages are raised by the trigger boxes for whoever stands in them (ZOnlineGamePlayTrigger 0x8d2740 ->
 *    0x5dd890, a maximum; kind 2 = BOARDS also calls the boarding rule, slot 45 = 0x6840a0, which takes any AI
 *    record in play while the vehicle waits - no stage is asked for). EXE.
 *    The human: [gamedata + 0x828 + 4 * (char)[gamedata + 0x898]], feet at +0x460 (kljoin.c, seen live); the game's
 *    own 'nearest player' (0x7263d0) takes the world place of [player + 4], the object's node, and skips a player
 *    whose node has flag bit 10. A bot's place: the same node arithmetic on [actor + 4] (0x60b160 does exactly
 *    that for a soldier): v = M * v + position for the node and every parent (0x7b3020 -> 0x6be1c0, 0x42a4d0).
 *
 * 2. WHAT THE HOOK DOES
 *    Only in an Arcade round that runs (session state 0x19) on a level that is NOT the stock one of its slot
 *    (klbot.c section 0: the same gate as Backstab / Bribe / Leave / Van), from the game's own thread.
 *    CHOICE, 3 s after the round started (the crew has registered): of the AI records in play that are not
 *    traitors, the Escort nearest to the human, drawn at random among the nearest Escort + 2 (so it is not the
 *    same man every round: at the start all seven stand in one row). EscortRecord=<i> names the first one instead.
 *    HOLD, twice a second per escort:
 *      - the defend block is read. If it no longer holds what the hook's last order left there, somebody else gave
 *        an order: farther than 600 from ours = the bot's own route chain (kept as 'its route place'; the hook's
 *        hold is over until the next order), nearer = one of the soldier's own tactics moved it (taken as ours).
 *        GUESS: the 600; nothing in the block says who wrote it.
 *      - the human is farther than EscortFar (800 = 8 m) from the BOT, and the hook has no hold or the human has
 *        moved more than EscortRetarget (500) from it, and the last order is EscortEvery (2 s) old: ONE call
 *        soldier->vtable[0x13c](&p, 0, 1, 0) - the arguments of a Defend step - with p = EscortSide (300) from the
 *        human towards the bot (the second escort 70 degrees round), at the human's height. The game snaps it.
 *        The bot is then at least EscortFar - EscortSide from p: never within the 250 that would make the order
 *        'soft' and end the chain's waiting step.
 *      - a bot that has not come 1 m nearer to its place 12 s after an order gets the human's own place once
 *        (a point beside him may lie behind a wall; where he stands is on the mesh).
 *    Never a teleport, never a write: between two orders the bot is the game's own soldier holding a defend
 *    position - cover, fire, leash and spacing work as they do at any hold place of its route.
 *    AGAINST THE MAP'S CHAIN - who wins, and why that is safe. Both sides use the same routine, which only
 *    replaces the place and queues a plan: the LAST caller wins, nothing is left half written.
 *      a. A Defend step that was running when the hook ordered keeps waiting for its man (he is not at its place
 *         and the order was not soft). Its NEXT is not triggered: the chain stands still behind him.
 *      b. A step started by something else (a TriggerDelay2, a TriggerActorsDead, the jump list) orders him to
 *         ITS place: the bot turns and goes. The hook sees the block change, remembers the place, and calls him
 *         back only when he is EscortFar from the human again - so the chain gets up to 8 m of its way, then the
 *         hook wins again and the step of (b) waits like (a).
 *      c. The stage boxes are places, not chain steps: an escort gets stage 1 / 2 / 3 when it walks through them
 *         beside the human, or later on its own route.
 *    RELEASE - the escort must still board:
 *      - the vehicle WAITS (state 3 / 4; EscortUntil=1: already while it drives in): an escort at stage 3 is left
 *        alone - the rules' slot 194 has just ordered it to the boarding place itself. An escort under stage 3
 *        (its chain stood still, so it never walked its last leg) gets the rules' own place by the same order with
 *        (place, 0, 1, 0): boarding object + 500 along its x axis, computed from the node data as 0x8faf72 does.
 *        Not soft, unlike the rules' call: a soft order would end the waiting step of (a) and the chain's next
 *        step would send the bot back into the level. On the way it crosses the BOARDS box, which gives stage 3
 *        and boards it. ASSUMPTION: the box is where the rules' place is (it is where stage-3 bots are sent).
 *      - the human is dead or aboard, or (EscortStage=1..3, default off) has reached that heist stage: when the
 *        hook's hold is still the bot's place and a route place is known, ONE order back to it (place, 0, 1, 0):
 *        the waiting step of (a) ends when he arrives and the chain goes on from where it stood. If the vehicle
 *        waits later and the bot is in play under stage 3, the boarding order above, once (EscortBoard=0: not).
 *      - the escort is dead, aboard, a traitor, or no longer the actor that was chosen: dropped, no call.
 *        EscortRefill=1 chooses another for a slot that was dropped before the release.
 *    WHAT IS TESTED BEFORE EVERY CALL (the game's own callers hand over a soldier a script owns; the hook comes
 *    from a crew record): the first 16 code bytes of 0x760e50; record in use, mask 1, not mask 2, status 0, still
 *    the actor chosen; actor's vtable 0xbb3bac; its node without flag bit 10; [actor + 0x576] == 1 (the test
 *    ZDefendPlayerPosBehaviour makes before it orders a member, 0x622c8d); [actor + 0x770] == 0; soldier's vtable
 *    0xbd0954 whose entry +0x13c is 0x760e50; [soldier + 0x40] == actor; the defend block readable with its +0x14
 *    == soldier; the defend goal readable; the pathfinder object and its two vtable entries inside kl2.exe.
 *    NOT ESTABLISHED: what [actor + 0x576] is beyond 'this member takes orders' (a downed or ragdolled bot?); what
 *    [soldier + 0xec] is; which of the soldier's tactics move the defend block by themselves and how far; whether
 *    a bot called away from a loot place drops what it does cleanly (the rules' slot 194 does the same to bots
 *    at stage 3, with the interrupt 0x1b4 on top); two escorts whose places snap to the same polygon.
 *
 * TESTED OFF-GAME ONLY: both builds compile. The logic has not run against a made-up round (klbot.c had such a
 * rig; this file has none yet).
 *
 * KLHook.ini
 *   [Bots]
 *   Enable=1            klbot.c must be on (the crew records are read through it)
 *   Escort=0            0 off, 1 or 2 = that many AI heisters stay near the human
 *   EscortDry=0         1 = everything is chosen and logged, NOTHING is called (live check E0)
 *   EscortFar=800       the human farther than this from the escort: it is called to him (100 = 1 m)
 *   EscortSide=300      how far beside the human its place is;  0 = the human's own place
 *   EscortRetarget=500  the human has moved this far from the escort's place: a new place
 *   EscortEvery=2       seconds between two orders to one escort, at least
 *   EscortUntil=3       vehicle state that ends the escort: 3 = it waits, 1 = it drives in
 *   EscortStage=0       1..3 = also ends when the HUMAN has reached that heist stage
 *   EscortBoard=1       a released escort under stage 3 is sent to the boarding place when the vehicle waits
 *   EscortRefill=0      1 = an escort that died is replaced
 *   EscortRecord=-1     crew record of the first escort (a test aid); -1 = the nearest
 *   EscortLog=1         2 = also every order and every place the route chain gave
 *
 * LOG (the lines the live checks look for)
 *   escort: on; Escort=1 Far=800 Side=300 ...
 *   escort: you: record 0, player 1a2b3c00, feet (x, y, z), node (x, y, z)                        once per round
 *   escort: record 3 (actor ..., soldier ...) chosen: 2.1 m from you, 7 bot(s) could be; its place now (x, y, z)
 *   escort: record 3 re-pointed: you are 12.4 m away at (x, y, z); place asked (x, y, z), the game set (x, y, z);
 *           2 order(s) since the last line; its route place (x, y, z)                              at most every 5 s
 *   escort: record 3 released (the vehicle waits, state 3): sent to the boarding place (x, y, z)
 *   escort: record 3 released (you are aboard): back to its route place (x, y, z)
 *   escort: record 3 dropped: its record says dead
 */
#ifndef KLESCORT_C
#define KLESCORT_C

#define KLE_ORDER       0x00760e50            /* ZSoldier vtable +0x13c: (pos, soft, reset, unused) */
#define KLE_SOLDIER_VT  0x00bd0954            /* CPPScript::ZSoldier, the class's only vtable */
#define KLE_HELD_VT     0x0086dba0            /* ZFFActor vtable +0x620: [actor + 0x770] != 0 */
#define KLE_MAX         2
#define KLE_ROUTE       600.0f                /* a foreign place farther than this from ours = the route chain's. GUESS */

static struct {
    int n, dry, log, record, refill, until, stage, board; DWORD every; float far_, side, retarget;
} kle;

struct kle_e {
    int rec, mode;                            /* mode: 0 free, 1 hold, 2 released (may still be sent aboard), 3 done */
    DWORD actor, soldier, order_at, log_at; int orders, direct, told_soft, have_target, have_route;
    float target[3], route[3], d_order;
};
static struct {
    DWORD rules, state, round_at; int stages, picked, told_you, told_none, told_gate; char used[KLB_NREC];
    struct kle_e e[KLE_MAX];
} kle_r;

static float kle_dist(const float a[3], const float b[3])
{
    return (float)sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
}
static int kle_ok3(const float v[3]) { return klb_finite(v[0]) && klb_finite(v[1]) && klb_finite(v[2]); }

/* The world place of a scene node, and (dir != 0) its x axis in the world: 0x7b3020 / 0x717890 done from the node
   data - nine floats at +0, the position at +0x24, the parent at +0x50 (0x6be1c0: x' = x*m6 + y*m3 + z*m0 ...). */
static int kle_node(DWORD node, float pos[3], float dir[3])
{
    float v[3] = { 0, 0, 0 }, d[3] = { 1, 0, 0 }, m[12], t[3]; int depth;
    if (!node) return 0;
    for (depth = 0; node && depth < 32; depth++) {
        if (!klh_rd(node, m, sizeof m)) return 0;
        t[0] = v[0] * m[6] + v[1] * m[3] + v[2] * m[0] + m[9];
        t[1] = v[0] * m[7] + v[1] * m[4] + v[2] * m[1] + m[10];
        t[2] = v[0] * m[8] + v[1] * m[5] + v[2] * m[2] + m[11];
        memcpy(v, t, sizeof v);
        t[0] = d[0] * m[6] + d[1] * m[3] + d[2] * m[0];
        t[1] = d[0] * m[7] + d[1] * m[4] + d[2] * m[1];
        t[2] = d[0] * m[8] + d[1] * m[5] + d[2] * m[2];
        memcpy(d, t, sizeof d);
        node = klh_rd32(node + 0x50);
    }
    if (node || !kle_ok3(v) || !kle_ok3(d)) return 0;
    memcpy(pos, v, sizeof v);
    if (dir) memcpy(dir, d, sizeof d);
    return 1;
}

/* the local player: his object, his feet (+0x460, kljoin.c) and his node's place (what 0x7263d0 measures with) */
static int kle_human(DWORD *player, float feet[3], float nodepos[3])
{
    DWORD gd, pl, node, fl = 0; BYTE sel = 0xff, type = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3) return 0;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * sel)) || !klh_rd(pl + 0x273c, &type, 1) || type != 2) return 0;
    if (!klh_rd(pl + 0x460, feet, 12) || !kle_ok3(feet)) return 0;
    if (!(node = klh_rd32(pl + 4)) || !klh_rd(node + 0x3c, &fl, 4) || (fl >> 10 & 1)) return 0;      /* 0x7263fa: such a player is nobody's 'nearest player' */
    if (!kle_node(node, nodepos, 0)) memcpy(nodepos, feet, 12);
    *player = pl;
    return 1;
}

/* Is crew record i a bot the order may be given to, now? -> 0 and why[100], or 1 with its actor, soldier and place. */
static int kle_bot(const struct klb_snap *s, int i, DWORD *actor_, DWORD *soldier_, float pos[3], char why[100])
{
    const struct klb_rec *r = &s->r[i]; DWORD actor = r->actor, node, soldier, fl = 0, held = 1, blk, goal, tmp; BYTE b576 = 0, raw[0x1c];
    why[0] = 0;
    if (i < 0 || i >= s->n || !r->used) { strcpy(why, "its record is gone"); return 0; }
    if (!(r->flags & 1)) { strcpy(why, "its record is not an AI member's"); return 0; }
    if (r->flags & 2) { strcpy(why, "it is a traitor"); return 0; }
    if (r->status) { snprintf(why, 100, "its record says %s", r->status == 4 ? "aboard" : r->status == 7 ? "dead" : r->status == 6 ? "escaped" : "not in play"); return 0; }
    if (!actor || klh_rd32(actor) != KLB_ACTOR_VT) { strcpy(why, "its actor is not a ZFFActor"); return 0; }
    if (klh_rd32((DWORD_PTR)KLH_VA(KLB_ACTOR_VT + 0x620)) != KLE_HELD_VT) { strcpy(why, "ZFFActor's 'held' test is not the one this build knows"); return 0; }
    if (!(node = klh_rd32(actor + 4)) || !klh_rd(node + 0x3c, &fl, 4) || (fl >> 10 & 1)) { strcpy(why, "its node is off (flag bit 10)"); return 0; }
    if (!klh_rd(actor + 0x576, &b576, 1) || b576 != 1) { strcpy(why, "its actor takes no orders now ([actor+0x576] is not 1)"); return 0; }
    if (!klh_rd(actor + 0x770, &held, 4) || held) { strcpy(why, "somebody holds it as a human shield"); return 0; }
    if (!(soldier = klh_rd32(actor + 0x77c)) || klh_rd32(soldier) != KLE_SOLDIER_VT || klh_rd32(soldier + 0x40) != actor) { strcpy(why, "actor +0x77c is not its ZSoldier"); return 0; }
    if (!(blk = klh_rd32(soldier + 0x64c)) || !klh_rd(blk, raw, sizeof raw) || *(DWORD *)(raw + 0x14) != soldier) { strcpy(why, "its soldier has no defend block yet"); return 0; }
    if (!(goal = klh_rd32(soldier + 0x648)) || !klh_rd(goal + 8, &tmp, 4)) { strcpy(why, "its soldier has no defend goal yet"); return 0; }
    if (!kle_node(node, pos, 0)) { strcpy(why, "its place cannot be read"); return 0; }
    *actor_ = actor; *soldier_ = soldier;
    return 1;
}

static int kle_block(DWORD soldier, float pos[3])
{
    DWORD blk = klh_rd32(soldier + 0x64c);
    return blk && klh_rd(blk, pos, 12) && kle_ok3(pos);
}

/* what 0x760e50 and 0x412910 use without a test of their own */
static int kle_callable(char why[100])
{
    static const BYTE code[16] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x0c, 0x56, 0x8b, 0xf1, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8 };      /* 0x760e50 */
    DWORD sys, a, pf, vt;
    if (klh_rd32((DWORD_PTR)KLH_VA(KLE_SOLDIER_VT + 0x13c)) != KLE_ORDER || !klb_same_code(KLE_ORDER, code, sizeof code)) { strcpy(why, "the soldier's order routine is not the one this build knows"); return 0; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(a = klh_rd32(sys + 0xac)) || !(pf = klh_rd32(a + 0xc)) || !(vt = klh_rd32(pf))) { strcpy(why, "there is no pathfinder object ([[sysif+0xac]+0xc])"); return 0; }
    if (!klt_code(klh_rd32(vt + 0x80)) || !klt_code(klh_rd32(vt + 0x84))) { strcpy(why, "the pathfinder object is no object of the game"); return 0; }
    return 1;
}

/* ONE call of the game's order (game thread only). want = the place asked; got = what the defend block holds after.
   -> 1 called, 0 not (why says), 2 dry run. */
static int kle_order(struct kle_e *e, const float want[3], float got[3], char why[100])
{
    float p[4]; BYTE soft = 0;
    memcpy(got, want, 12);
    if (!kle_ok3(want)) { strcpy(why, "the place is not a number"); return 0; }
    if (!kle_callable(why)) return 0;
    if (kle.dry) return 2;
    p[0] = want[0]; p[1] = want[1]; p[2] = want[2]; p[3] = 0;
    ((void (__fastcall *)(void *, void *, const float *, int, int, int))(DWORD_PTR)KLH_VA(KLE_ORDER))((void *)(DWORD_PTR)e->soldier, 0, p, 0, 1, 0);
    if (!kle_block(e->soldier, got)) memcpy(got, want, 12);
    if (klh_rd(e->soldier + 0x4fc, &soft, 1) && soft && !e->told_soft++)
        klog("escort: record %d: the game took an order as 'he is there already' ([soldier+0x4fc] = 1): a waiting step of its route chain ends now (said once per escort)", e->rec);
    return 1;
}

/* the rules' own boarding place: boarding object + 500 along its x axis (0x8faf72..0x8fafe6) */
static int kle_boarding(DWORD rules, float out[3])
{
    DWORD obj, node; float p[3], x[3];
    if (!(obj = klh_rd32(rules + 0x1e0)) || !(node = klh_rd32(obj + 4)) || !kle_node(node, p, x)) return 0;
    out[0] = p[0] + 500.0f * x[0]; out[1] = p[1] + 500.0f * x[1]; out[2] = p[2] + 500.0f * x[2];
    return kle_ok3(out);
}

static void kle_pick(const struct klb_snap *s, const float hp[3], DWORD now)
{
    struct { int rec; float d; DWORD actor, soldier; } c[KLB_NREC], t; int nc = 0, i, k, slot, pool; char why[100]; float bp[3], blk[3];
    for (slot = 0; slot < kle.n && kle_r.e[slot].mode; slot++) ;
    if (slot >= kle.n) return;
    for (i = 0; i < s->n; i++) {
        if (!s->r[i].used || !(s->r[i].flags & 1) || kle_r.used[i]) continue;
        if (!kle_bot(s, i, &c[nc].actor, &c[nc].soldier, bp, why)) continue;
        c[nc].rec = i; c[nc].d = kle_dist(bp, hp); nc++;
    }
    if (!nc) {
        if (!kle_r.told_none++) klog("escort: no AI heister can be chosen yet (in play, not a traitor, with a soldier that takes orders): trying again");
        return;
    }
    for (i = 1; i < nc; i++) for (k = i; k > 0 && c[k].d < c[k - 1].d; k--) { t = c[k]; c[k] = c[k - 1]; c[k - 1] = t; }
    pool = nc < kle.n + 2 ? nc : kle.n + 2;   /* at random among the nearest Escort + 2: at the start they stand in one row */
    k = -1;
    if (kle.record >= 0 && !kle_r.picked) for (i = 0; i < nc; i++) if (c[i].rec == kle.record) k = i;
    if (k < 0) { klb_seed = klb_seed * 1103515245u + 12345u; k = (int)((klb_seed >> 16) % (DWORD)pool); }
    memset(&kle_r.e[slot], 0, sizeof kle_r.e[slot]);
    kle_r.e[slot].rec = c[k].rec; kle_r.e[slot].mode = 1; kle_r.e[slot].actor = c[k].actor; kle_r.e[slot].soldier = c[k].soldier;
    kle_r.used[c[k].rec] = 1; kle_r.picked++;
    if (kle_block(c[k].soldier, blk) && (blk[0] || blk[1] || blk[2])) { memcpy(kle_r.e[slot].route, blk, 12); kle_r.e[slot].have_route = 1; }
    else blk[0] = blk[1] = blk[2] = 0;
    klog("escort: record %d (actor %08lx, soldier %08lx) chosen%s: %.1f m from you, %d bot(s) could be; its place now (%.0f, %.0f, %.0f)%s; it is called when you are more than %.0f m from it%s",
         c[k].rec, c[k].actor, c[k].soldier, kle.record == c[k].rec ? " (EscortRecord)" : "", c[k].d / 100, nc, blk[0], blk[1], blk[2], kle_r.e[slot].have_route ? "" : " = none yet", kle.far_ / 100, kle.dry ? " - DRY RUN: nothing is called" : "");
    (void)now;
}

/* a place EscortSide from the human towards the bot, the second escort 70 degrees round; the human's height */
static void kle_place(const float hp[3], const float bp[3], int slot, int direct, float out[3])
{
    float dx = bp[0] - hp[0], dz = bp[2] - hp[2], l = (float)sqrt(dx * dx + dz * dz), c = 1, sn = 0, x;
    memcpy(out, hp, 12);
    if (direct || kle.side <= 0 || l < 1.0f) return;
    dx /= l; dz /= l;
    if (slot) { c = 0.342f; sn = 0.940f; }
    x = dx * c - dz * sn; dz = dz * c + dx * sn; dx = x;
    out[0] = hp[0] + dx * kle.side; out[2] = hp[2] + dz * kle.side;
}

static void kle_hold(const struct klb_snap *s, int slot, const float hp[3], const float bp[3], DWORD now)
{
    struct kle_e *e = &kle_r.e[slot]; float cur[3], want[3], got[3], d = kle_dist(bp, hp), dt; char why[100]; int direct = 0, r;
    if (kle_block(e->soldier, cur)) {
        if (e->have_target && kle_dist(cur, e->target) > 5.0f) {             /* somebody else gave an order since ours */
            if (kle_dist(cur, e->target) > KLE_ROUTE) {
                memcpy(e->route, cur, 12); e->have_route = 1; e->have_target = 0;
                if (kle.log >= 2) klog("escort: record %d: its route chain ordered it to (%.0f, %.0f, %.0f); it goes there until you are %.0f m from it", e->rec, cur[0], cur[1], cur[2], kle.far_ / 100);
            } else memcpy(e->target, cur, 12);                               /* a tactic of its own moved the place a little: still our hold */
        } else if (!e->have_target && (cur[0] || cur[1] || cur[2])) { memcpy(e->route, cur, 12); e->have_route = 1; }
    }
    if (!(d > kle.far_)) return;                                             /* near enough (a NaN is not far) */
    if (e->order_at && now - e->order_at < kle.every) return;
    if (e->have_target) {
        dt = kle_dist(bp, e->target);
        if (kle_dist(hp, e->target) <= kle.retarget) {                       /* the place is still beside the human: he is on his way */
            if (e->direct || now - e->order_at < 12000 || dt < e->d_order - 100.0f) return;
            direct = 1;                                                      /* 12 s and not 1 m nearer: the human's own place, once */
        }
    }
    kle_place(hp, bp, slot, direct, want);
    r = kle_order(e, want, got, why);
    if (!r) {
        if (!e->log_at || now - e->log_at >= 5000) { e->log_at = KLB_T(now); klog("escort: record %d NOT re-pointed: %s", e->rec, why); }
        e->order_at = KLB_T(now);
        return;
    }
    e->order_at = KLB_T(now); e->orders++; e->direct = direct; e->d_order = kle_dist(bp, got);
    if (r == 1) { memcpy(e->target, got, 12); e->have_target = 1; }
    if (kle.log >= 2 || !e->log_at || now - e->log_at >= 5000) {
        klog("escort: record %d %s: you are %.1f m away at (%.0f, %.0f, %.0f); place asked (%.0f, %.0f, %.0f)%s, the game set (%.0f, %.0f, %.0f); %d order(s) since the last line; its route place (%.0f, %.0f, %.0f)%s",
             e->rec, r == 2 ? "WOULD be re-pointed (dry run)" : "re-pointed", d / 100, hp[0], hp[1], hp[2], want[0], want[1], want[2], direct ? " = where you stand (it did not get nearer in 12 s)" : "",
             got[0], got[1], got[2], e->orders, e->route[0], e->route[1], e->route[2], e->have_route ? "" : " = none seen");
        e->log_at = KLB_T(now); e->orders = 0;
    }
    (void)s;
}

/* why: 1 the human is out of play, 2 the vehicle, 3 the human's stage */
static void kle_release(const struct klb_snap *s, int slot, int reason, DWORD now)
{
    struct kle_e *e = &kle_r.e[slot]; const struct klb_rec *r = &s->r[e->rec]; float bd[3], got[3]; char why[100], what[80]; int waiting = s->veh == 3 || s->veh == 4, k;
    if (reason == 1) snprintf(what, sizeof what, "you are %s", s->human >= 0 && s->r[s->human].status == 4 ? "aboard" : "out of play");
    else if (reason == 2) snprintf(what, sizeof what, "the vehicle %s, state %u", waiting ? "waits" : "comes", s->veh);
    else snprintf(what, sizeof what, "you are at heist stage %u", s->human >= 0 ? s->r[s->human].stage : 0);
    e->mode = 2;
    if (waiting) {
        e->mode = 3;
        if (r->stage >= 3) { klog("escort: record %d released (%s): it is at stage 3, the game's rules send it aboard themselves", e->rec, what); return; }
        if (!kle.board) { klog("escort: record %d released (%s): EscortBoard=0, it is left where it is", e->rec, what); return; }
        if (!kle_boarding(s->rules, bd)) { klog("escort: record %d released (%s): the boarding place cannot be read, nothing is called", e->rec, what); return; }
        k = kle_order(e, bd, got, why);
        if (k) klog("escort: record %d released (%s): %s to the boarding place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f); it is at stage %u", e->rec, what, k == 2 ? "WOULD be sent (dry run)" : "sent", bd[0], bd[1], bd[2], got[0], got[1], got[2], r->stage);
        else klog("escort: record %d released (%s): NOT sent to the boarding place: %s", e->rec, what, why);
        return;
    }
    if (e->have_target && e->have_route) {
        k = kle_order(e, e->route, got, why);
        if (k) klog("escort: record %d released (%s): %s to its route place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f)", e->rec, what, k == 2 ? "WOULD go back (dry run)" : "back", e->route[0], e->route[1], e->route[2], got[0], got[1], got[2]);
        else klog("escort: record %d released (%s): NOT sent back to its route place: %s", e->rec, what, why);
    } else klog("escort: record %d released (%s): %s", e->rec, what, e->have_target ? "no route place was seen, it stays where it is until its chain orders it" : "its route chain's order is the one it has");
    e->have_target = 0;
    (void)now;
}

static void kle_tick(int game_thread)
{
    static DWORD last; static int toldthread; struct klb_snap s; DWORD now = GetTickCount(), player = 0, actor, soldier; char why[200], w[100];
    float hp[3], hn[3], bp[3], bd[3], got[3]; const struct klb_rec *h; int i, stages = 0, human_in, rel = 0, waiting, k;
    if (!kle.n || !klb.on || !klh_exe_ok || now - last < 500) return;
    last = now;
    if (!klb_read(&s)) { kle_r.rules = 0; return; }
    for (i = 0; i < s.n; i++) if (s.r[i].used) stages += s.r[i].stage;
    if (s.rules != kle_r.rules || (s.state == KLB_ROUND && kle_r.state != KLB_ROUND) || stages < kle_r.stages) {      /* a new round: as klbot.c's klb_act */
        memset(&kle_r, 0, sizeof kle_r); kle_r.rules = s.rules; kle_r.round_at = KLB_T(now);
    }
    kle_r.state = s.state; kle_r.stages = stages;
    if (s.state != KLB_ROUND) return;
    if (!klb_level(why)) {                    /* klbot.c section 0: nothing on a stock level, on an unknown one, or without the Steam guard */
        if (!kle_r.told_gate++) klog("escort: %s: no escort here (it acts only on a level that is not stock)", why);
        return;
    }
    if (!game_thread) { if (!toldthread++) klog("escort: the tick is not on the game's thread ([KLHook] Tick=0?): nothing is ordered"); return; }
    h = s.human >= 0 ? &s.r[s.human] : 0;
    human_in = h && h->status == 0 && kle_human(&player, hp, hn);
    waiting = s.veh == 3 || s.veh == 4;
    if (human_in && !kle_r.told_you++)
        klog("escort: you: record %d, player %08lx, feet (%.0f, %.0f, %.0f), node (%.0f, %.0f, %.0f) - the two should agree to within a body's height", s.human, player, hp[0], hp[1], hp[2], hn[0], hn[1], hn[2]);
    if (!human_in) rel = 1;
    else if (s.veh >= (BYTE)kle.until && s.veh <= 5) rel = 2;
    else if (kle.stage && h->stage >= kle.stage) rel = 3;
    for (i = 0; i < kle.n; i++) {
        struct kle_e *e = &kle_r.e[i];
        if (e->mode != 1 && e->mode != 2) continue;
        if (!kle_bot(&s, e->rec, &actor, &soldier, bp, w) || actor != e->actor || soldier != e->soldier) {
            klog("escort: record %d dropped: %s", e->rec, w[0] ? w : "its actor is no longer the one chosen");
            k = e->mode; memset(e, 0, sizeof *e);
            if (k == 2 || !kle.refill) e->mode = 3;                           /* mode 0 = the slot may be given to another */
            continue;
        }
        if (e->mode == 1) {
            if (rel) kle_release(&s, i, rel, now);
            else kle_hold(&s, i, hp, bp, now);
        } else if (waiting && kle.board) {                                    /* released earlier; now the vehicle waits */
            e->mode = 3;
            if (s.r[e->rec].stage >= 3) continue;                             /* the rules have sent it themselves */
            if (!kle_boarding(s.rules, bd)) { klog("escort: record %d (released): the vehicle waits but the boarding place cannot be read", e->rec); continue; }
            k = kle_order(e, bd, got, w);
            if (k) klog("escort: record %d (released, stage %u): the vehicle waits: %s to the boarding place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f)", e->rec, s.r[e->rec].stage, k == 2 ? "WOULD be sent (dry run)" : "sent", bd[0], bd[1], bd[2], got[0], got[1], got[2]);
            else klog("escort: record %d (released): NOT sent to the boarding place: %s", e->rec, w);
        }
    }
    if (!rel && now - kle_r.round_at >= 3000) kle_pick(&s, hn, now);          /* one slot per pass */
}

static void kle_init(void)
{
    int v;
    memset(&kle, 0, sizeof kle); memset(&kle_r, 0, sizeof kle_r);
    if (!klb.on) return;                      /* [Bots] Enable=0: klbot.c is off, and so is this */
    v = (int)GetPrivateProfileIntA("Bots", "Escort", 0, klh_ini);
    kle.n = v < 0 ? 0 : v > KLE_MAX ? KLE_MAX : v;
    if (!kle.n) return;
    kle.dry = GetPrivateProfileIntA("Bots", "EscortDry", 0, klh_ini) != 0;
    kle.log = klb_pos("EscortLog", 1, 2);
    kle.record = (int)GetPrivateProfileIntA("Bots", "EscortRecord", -1, klh_ini); if (kle.record >= KLB_NREC) kle.record = -1;
    kle.refill = GetPrivateProfileIntA("Bots", "EscortRefill", 0, klh_ini) != 0;
    kle.until = GetPrivateProfileIntA("Bots", "EscortUntil", 3, klh_ini) == 1 ? 1 : 3;
    kle.stage = klb_pos("EscortStage", 0, 3);
    kle.board = GetPrivateProfileIntA("Bots", "EscortBoard", 1, klh_ini) != 0;
    kle.every = (DWORD)klb_pos("EscortEvery", 2, 60) * 1000; if (kle.every < 1000) kle.every = 1000;
    kle.far_ = klb_inif("EscortFar", "800"); if (!klb_finite(kle.far_) || kle.far_ < 400) kle.far_ = 400;      /* under 4 m the place could come within the game's 250 */
    kle.side = klb_inif("EscortSide", "300"); if (!klb_finite(kle.side) || kle.side < 0) kle.side = 0;
    if (kle.side > kle.far_ - 300) kle.side = kle.far_ - 300;                 /* the bot stays at least 3 m from the place it is called to */
    kle.retarget = klb_inif("EscortRetarget", "500"); if (!klb_finite(kle.retarget) || kle.retarget < kle.side + 100) kle.retarget = kle.side + 100;
    klog("escort: on; Escort=%d Far=%.0f Side=%.0f Retarget=%.0f Every=%lu s Until=%d Stage=%d Board=%d Refill=%d Record=%d%s; Arcade only, on a level that is not the stock one of its slot; one game call (the soldier's own order %08x), no write",
         kle.n, kle.far_, kle.side, kle.retarget, kle.every / 1000, kle.until, kle.stage, kle.board, kle.refill, kle.record, kle.dry ? " DRY RUN (nothing is called)" : "", KLE_ORDER);
}

#endif /* KLESCORT_C */
