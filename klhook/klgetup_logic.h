/* klgetup_logic.h - [BotFill] OnlineGetUp, the PURE decisions (no game memory, no log, no clock of its own). Included by klbotfill.c and klgetup_test.c.
   Two halves (re/bot_getup_online.md):
     HOST  : a downed human (his body's D state [[player+0x2948]+4] is 1 lying / 2 falling) gets the nearest free AI heister sent to him with the same
             order the Arcade rush uses (kle_order2); the order is repeated every KGU_REORDER_MS while he is not there yet.
     DOWNED MACHINE: a bot standing by his own body (the Arcade BotRange, 4 m, same floor) adds `per_s` presses' worth a second to the mash meter
             (kld_o.h.meter, [Down] MashHold) - the same thing kladren.c does for the Arcade human (kld_s.meter floor), as a local write on the machine
             that owns the get-up. Nothing is sent: the stock GettingUp message (0x6cd720) carries the rise to the others as in any online get-up. */
#ifndef KLGETUP_LOGIC_H
#define KLGETUP_LOGIC_H
#include <math.h>
#include <string.h>

#define KGU_REORDER_MS 2500      /* Arcade kad_rush: an order again every 2.5 s while the rusher is not by him */
#define KGU_STOP_CM    200.0f    /* Arcade BotAnimNear 2 m: the place the rusher is sent to */

/* [D+4]: 1 lying, 2 falling are 'down'; 0 up, 3 getting up are not (the same reading as kladren.c / kldown_hold.h). */
static int kgu_downed(unsigned long ds) { return ds == 1 || ds == 2; }

/* nearest candidate: d[i] < 0 = not a candidate; returns its index or -1 (a NaN is never near) */
static int kgu_pick(const float *d, int n, float range)
{
    int i, best = -1; float bd = 1e30f;
    for (i = 0; i < n; i++) if (d[i] >= 0 && d[i] <= range && d[i] < bd) { bd = d[i]; best = i; }
    return best;
}

/* wk-botpar BP13 (OnlineGetUpFreeFirst / OnlineGetUpBusyRange): kgu_pick with the busy bots (walking out / carrying money) held back. busy[i] != 0 = a walker-out or carrier.
   busyRange > 0: a busy bot farther than that is no candidate (BP13: a walker-out sent from 27 m swung -2.8 .. +4.3 m/s and never got nearer than 14.4 m);
   freeFirst: a free bot within `range` wins over every busy one, however near the busy one is (BP12: the free bot 0 sprinted straight to him). Both 0 = kgu_pick. */
static int kgu_pick_b(const float *d, const int *busy, int n, float range, float busyRange, int freeFirst)
{
    int i, best = -1, bestFree = -1; float bd = 1e30f, bf = 1e30f;
    for (i = 0; i < n; i++) {
        if (!(d[i] >= 0 && d[i] <= range)) continue;
        if (busy[i]) { if (busyRange > 0 && d[i] > busyRange) continue; if (d[i] < bd) { bd = d[i]; best = i; } }
        else { if (d[i] < bf) { bf = d[i]; bestFree = i; } if (d[i] < bd) { bd = d[i]; best = i; } }
    }
    return freeFirst && bestFree >= 0 ? bestFree : best;
}

/* the place a rusher is sent to: `stop` cm from the human toward the bot (the bot's own side), on the human's height; a bot already within `stop`
   is sent to the human's feet. */
static void kgu_place(const float bot[3], const float hum[3], float stop, float out[3])
{
    float dx = bot[0] - hum[0], dz = bot[2] - hum[2], l = (float)sqrt(dx * dx + dz * dz);
    out[1] = hum[1];
    if (!(l > stop)) { out[0] = hum[0]; out[2] = hum[2]; return; }
    out[0] = hum[0] + dx / l * stop; out[2] = hum[2] + dz / l * stop;
}

/* is an order due? last = tick of the last one (0 = none yet). Every KGU_REORDER_MS while he lies: a downed man does not move, so the repeat is the
   Arcade 'ordered again' (kad_rush). */
static int kgu_due(DWORD now, DWORD last)
{
    return !last || now - last >= KGU_REORDER_MS;
}

/* wk-botpar OnlineGetUpKeepGoal: after the first order, is a repeat order needed? Called once a pass (1 s).
   prevD / curD = the bot's distance (cm) to the downed man at the last check and now (prevD < 0 = no earlier check), movedCm = how far the target
   stands from where the standing order sent the bot, stallMs = time since the distance last shrank by KGU_PROGRESS_CM between two checks.
   0 = keep going (do not re-order), 1 = target moved, 2 = stalled. */
#define KGU_PROGRESS_CM 50.0f
#define KGU_MOVED_CM    200.0f
#define KGU_STALL_MS    3000u
static int kgu_keep(float prevD, float curD, float movedCm, DWORD stallMs)
{
    if (movedCm >= KGU_MOVED_CM) return 1;
    if (prevD >= 0 && prevD - curD >= KGU_PROGRESS_CM) return 0;
    return stallMs >= KGU_STALL_MS ? 2 : 0;
}

/* wk-botpar OnlineGetUpDetour (BP8/BP9 root cause): kgu_keep reads the STRAIGHT-LINE distance, but a bot sent round a wall or railing runs a route whose
   straight-line distance first grows (BP8 3.3 -> 12.8 m at 4.8 m/s, BP9 24.6 -> 15.9 -> 23.7 m), and one that arrived (by seat, the caller `continue`s before
   the keep test) may drift off again while the stall clock kept running through the time it stood there. So:
   walkedCm = how far the bot itself moved since the last tick it counted as progress (>= KGU_WALK_CM = running, a detour, not stalled), but only while the order
   is younger than KGU_DETOUR_MS (a route that long is no route); arrivedLeft = the bot stood by him since this order and is now KGU_LEFT_CM out again: order it back at once. */
#define KGU_WALK_CM     300.0f
#define KGU_DETOUR_MS   20000u
#define KGU_LEFT_CM     500.0f
static int kgu_keep_d(float prevD, float curD, float movedCm, DWORD stallMs, float walkedCm, DWORD ordAgeMs, int arrived)
{
    if (movedCm >= KGU_MOVED_CM) return 1;
    if (arrived && curD >= KGU_LEFT_CM) return 2;
    if (prevD >= 0 && prevD - curD >= KGU_PROGRESS_CM) return 0;
    if (walkedCm >= KGU_WALK_CM && ordAgeMs < KGU_DETOUR_MS) return 0;
    return stallMs >= KGU_STALL_MS ? 2 : 0;
}

/* wk-botpar OnlineGetUpRecede (BP14, BP13): a rushing bot sent from 14.7 m was 34 m away 15 s later and never re-ordered, because the game resumes the bot's earlier move goal
   (the stack walk / the exit walk) under the rush order and Detour / KeepGoal excused the walk (moved >= 3 m itself). prevD < 0 = no earlier check; ordD <= 0 = order distance unknown.
   1 = receding: it got >= KGU_RECEDE_STEP_CM farther since the last check, or it is more than KGU_RECEDE_ORD_CM beyond the distance it was ordered from. A sideways route that is
   neither is not receding. GUESS: 2 m on both limits (the owner's figure), a route round a wall that first leads away is re-ordered too (re-ordering a bot that is truly routing costs a restart). */
#define KGU_RECEDE_STEP_CM 200.0f
#define KGU_RECEDE_ORD_CM  200.0f
#define KGU_RECEDE_GAP_MS  3000u   /* rate limit: no receding verdict until the order is this old (a bot running off at 3 m/s would otherwise be re-ordered every 1 s pass; GUESS 3 s = KGU_STALL_MS) */
static int kgu_recede(float prevD, float curD, float ordD, DWORD ordAgeMs)
{
    if (!(curD >= 0) || ordAgeMs < KGU_RECEDE_GAP_MS) return 0;
    if (prevD >= 0 && curD - prevD >= KGU_RECEDE_STEP_CM) return 1;
    return ordD > 0 && curD - ordD > KGU_RECEDE_ORD_CM;
}

/* a helper counts when within `range` (cm) horizontally and `dy` (cm) in height */
static int kgu_helper_ok(float dist, float dy, float range, float dymax)
{
    return dist >= 0 && dist <= range && dy >= -dymax && dy <= dymax;
}

/* skip the get-up pass for this van state? 1/2 coming, 3/4 waiting, 5 leaving (re/retomoto_street.md 6). ignore 0 (the old rule): skip 1..5.
   ignore 1 (OnlineGetUpIgnoreVan): never skip, as Arcade's rush with its default RushVan=0 (kladren.c kad_vanlive; re/getup_arcade_range_1101.md). */
static int kgu_van_skip(int vstate, int ignore) { return !ignore && vstate >= 1 && vstate <= 5; }

/* may a bot in this phase / tally answer a downed human? phase 0 idle, 1 walks to a stack, 2 walks out (to the van), 3 aboard, 4 takes a stack.
   busy 0 (the old rule): phase 0 / 1 with nothing carried. busy 1 (OnlineGetUpBusy, Arcade's Rush: any bot not down, not rushing, not escorting):
   carriers and exit walkers too; a bot taking a stack (4, a few seconds) or aboard (3) never. */
static int kgu_free(int phase, int tally, int busy)
{
    if (phase == 0 || phase == 1) return busy || tally <= 0;
    return busy && phase == 2;
}

/* the mash meter with a helper by: + per_s x dt (dt clamped to 0.25 s, as kldh_step), raised at most up to `cap` (a meter already above it is left
   alone, never lowered). A NaN or non-positive input changes nothing. */
static float kgu_boost(float meter, float dt, float per_s, float cap)
{
    float n;
    if (!(dt > 0) || !(per_s > 0) || !(meter >= 0) || !(cap > 0)) return meter;
    if (dt > 0.25f) dt = 0.25f;
    n = meter + per_s * dt;
    if (n > cap) n = cap;
    return n > meter ? n : meter;
}

/* wk-botpar OnlineGetUpFlopMeter: with Flop on, the whole knock-down is the fall (D state 2), so the MashHold meter above is never fed; the flop's own
   mash meter (kld_s.meter: speed FlopBase + FlopPerPress x meter) is held at `floor` or more while a helper stands by, as kladren.c does for Arcade ([Adrenaline]
   Meter 3.0). No helper, floor <= 0 or a NaN meter: unchanged. */
static float kgu_floor(float meter, int helped, float floor)
{
    if (!helped || !(floor > 0) || !(meter == meter)) return meter;
    return meter < floor ? floor : meter;
}

/* wk-botpar BP12 (OnlineGetUpDetour): the bot stood on the spot the game set for it (189, 12, 1791) and was re-ordered every 3.5 s as 'stalled at 3.7 m',
   because the host's replica of the diving body slid ~1.5 m after the order. A bot within KGU_GOAL_CM of its own set goal, and within `nearCm` (OnlineGetUpNear) of
   the body, has arrived. goalD < 0 = no goal known. */
#define KGU_GOAL_CM 100.0f
static int kgu_at_goal(float bodyD, float goalD, float nearCm)
{
    return goalD >= 0 && goalD <= KGU_GOAL_CM && bodyD >= 0 && bodyD <= nearCm;
}

/* wk-botpar BP15 (OnlineGetUpHold): bot 5 closed to 3.6 m, then walked off 8.2 m and again 9.1 m (the rush goal completed on arrival and the game resumed its stack walk),
   so the joiner's helper scan (limit 4 m) saw 334 cm once and 466 cm later. A rusher within KGU_HOLD_NEAR_CM of him is ordered to a spot KGU_HOLD_STOP_CM from him
   every KGU_HOLD_GAP_MS. GUESS: 4 m = the helper limit (OnlineGetUpNear), 1 m place, 900 ms (the pass runs once a second, so about every pass). */
#define KGU_HOLD_NEAR_CM 400.0f
#define KGU_HOLD_STOP_CM 100.0f
#define KGU_HOLD_GAP_MS  900u
static int kgu_hold_near(float bdst) { return bdst >= 0 && bdst <= KGU_HOLD_NEAR_CM; }
static int kgu_hold_due(DWORD now, DWORD last) { return !last || now - last >= KGU_HOLD_GAP_MS; }
/* BP17 (11-01): the hold kept bot 6 at 2.7 - 3.6 m for 3 s (the joiner saw it at 388 cm), then it stood at 4.0 m, fell out of the 4 m test and walked off to
   9 - 14 m. Once a bot has been held (held > 0), keep holding while it is within KGU_HOLD_KEEP_CM. GUESS: 8 m (BP15's walk-offs peaked at 8.2 - 9.1 m). */
#define KGU_HOLD_KEEP_CM 800.0f
static int kgu_hold_on(float bdst, int held) { return kgu_hold_near(bdst) || (held > 0 && bdst >= 0 && bdst <= KGU_HOLD_KEEP_CM); }

/* wk-botpar BP16b (OnlineGetUpPlateau; ce's 10-29 diagnosis, open_work_log 10-29 ~07:20): bot 4 dithered 9 - 14.7 m from the seat for 18 s, re-ordered every ~3 s (KeepGoal stalled /
   Recede) and never came nearer; BP13 14.4, BP14 ~14, BP15 8 - 9 m the same. Not combat, not a fighting pass: the order place (the joiner's beacon spot) is most likely UNREACHABLE for
   the host's planner, which stops short. So the rush is given up, not repeated:
     kgu_best    : *bestD = the nearest the bot has stood to him since this rush began (< 0 = none yet); returns 1 when curD improves it by KGU_PLATEAU_GAIN_CM or more (the caller stamps
                   the tick), else leaves it - smaller gains add up until they make the metre, so a slow but real approach still counts.
     kgu_plateau : 1 = the bot is still more than stopCm + KGU_PLATEAU_FAR_CM out and has not gained a metre in KGU_PLATEAU_MS: stop re-ordering it, release it, keep it out of the
                   pick (kgu_plateau_out) for KGU_PLATEAU_OUT_MS, and send the seat's next bot to the host's replica feet instead of the beacon place (the fallback place).
     kgu_plateau_out: is the bot still excluded? platAt = tick of its plateau (0 = none).
   GUESS: 5 m / 1 m / 5 s / 10 s are the figures of the 10-29 note, not measured. A bot that merely waits 5 s for its order to take effect at > stop + 5 m is given up too (then re-picked 10 s later). */
#define KGU_PLATEAU_FAR_CM  500.0f
#define KGU_PLATEAU_GAIN_CM 100.0f
#define KGU_PLATEAU_MS      5000u
#define KGU_PLATEAU_OUT_MS  10000u
#define KGU_PLATEAU_BACK_CM 500.0f      /* review 10-30: a bot that once stood near (best 3 m) and was then carried back out (BP15's 3.6 <-> 9 m, a resumed stack walk) would never plateau, its best being inside stop + 5 m for good: standing KGU_PLATEAU_BACK_CM or more BEYOND its best re-stamps the best at the far place and its clock starts anew. GUESS 5 m. */
static int kgu_best(float *bestD, float curD)
{
    if (!(curD >= 0)) return 0;
    if (!(*bestD >= 0) || *bestD - curD >= KGU_PLATEAU_GAIN_CM || curD - *bestD >= KGU_PLATEAU_BACK_CM) { *bestD = curD; return 1; }
    return 0;
}
static int kgu_plateau(float bestD, DWORD bestAgeMs, float stopCm)
{
    if (!(bestD >= 0)) return 0;
    return bestD > stopCm + KGU_PLATEAU_FAR_CM && bestAgeMs >= KGU_PLATEAU_MS;
}
static int kgu_plateau_out(DWORD now, DWORD platAt) { return platAt != 0 && now - platAt < KGU_PLATEAU_OUT_MS; }

/* wk-botpar BP16b, the Recede side: BP16b's re-orders every ~3 s were half 'receding' verdicts on a bot that was MOVING - trying routes round the obstacle (9 -> 14.7 -> 9 m), a detour, not a
   retreat. A bot that moved >= KGU_WALK_CM itself since its last progress point (walkedCm, the Detour measure) and stands no more than KGU_RECEDE_WALK_CM beyond the distance it was ordered
   from is on a route: no receding verdict. BP14's runaway (ordered at 14.7 m, 34 m later; the game resumed its stack walk) is still caught once it is > 8 m beyond the order distance.
   walkedCm 0 (OnlineGetUpDetour off, or the bot stood still) = kgu_recede unchanged. GUESS: 8 m - a route round a wall or railing takes a bot a few metres out, a resumed stack walk takes it tens. */
#define KGU_RECEDE_WALK_CM 800.0f
static int kgu_recede_w(float prevD, float curD, float ordD, DWORD ordAgeMs, float walkedCm)
{
    if (walkedCm >= KGU_WALK_CM && ordD > 0 && curD >= 0 && curD - ordD <= KGU_RECEDE_WALK_CM) return 0;
    return kgu_recede(prevD, curD, ordD, ordAgeMs);
}

/* OnlineVanPosSane (bots_online_scorecard_1101 G1): the escape van's place is read from its vehicle object's scene node. DM09 (Q31) gave
   (24235, -59842, 13883) while the real boarding object stood at (-1852, 121, 8420): a node that was never placed. Plausible = every coordinate
   within KVP_ABS_CM (400 m) AND, when reference places are known (exit trigger, escape boxes), within KVP_REF_CM (500 m, 3D) of one of them.
   Bounds chosen from the logs: stock maps keep every object within |coord| ~ 15000 cm (DD02 exit leg points y 6010, DM09 boarding y 121, x -1852);
   the bogus y was 59842. A called van drives in from a few hundred metres at most. Off (on = 0): always plausible (the old rule). */
#define KVP_ABS_CM 40000.0f
#define KVP_REF_CM 50000.0f
static int kvp_sane(int on, const float *p, int nref, const float (*ref)[3])
{
    int i;
    if (!on) return 1;
    for (i = 0; i < 3; i++) if (!(fabsf(p[i]) <= KVP_ABS_CM)) return 0;      /* also rejects NaN */
    if (nref <= 0) return 1;
    for (i = 0; i < nref; i++) {
        float dx = p[0] - ref[i][0], dy = p[1] - ref[i][1], dz = p[2] - ref[i][2];
        if (dx * dx + dy * dy + dz * dz <= KVP_REF_CM * KVP_REF_CM) return 1;
    }
    return 0;
}

/* OnlineTriggerOriginSkip (G3): a bot whose place reads exactly the origin (1 cm, as kgg_origin) is not placed yet (DD01: 7 bots at (0,0,0) counted
   "inside" a box at the origin and fired it). Returns 1 = leave this bot out of the inside test. */
static int kvp_origin_skip(int on, const float *p)
{
    return on && fabsf(p[0]) <= 1 && fabsf(p[1]) <= 1 && fabsf(p[2]) <= 1;
}

/* OnlineUnplacedGuard (G3): 1 = nb > 0 bots, all nb of them at the origin, and the round is older than minMs. */
static int kvp_all_unplaced(int on, int nb, int norigin, unsigned long ageMs, unsigned long minMs)
{
    return on && nb > 0 && norigin == nb && ageMs > minMs;
}

/* OnlineTriggersSkipPickups (wk-trigdm-1101, re/bots_trigger_cops_1028.md section 8): Dead Men's own FA grafts carry TriggerBox2 boxes that are NOT cop waves:
   the campaign pick-ups ('PCnnnn_' nodes: cash registers / drawers / cash boxes / jewels / watches / credit card / money boxes with an Attach child) and the
   characters' own interact boxes (civilians, clerks, gang members, FBI agents, the senator: a TriggerBox2 whose only target is its own node). All are players-only,
   so OnlineTriggersExtra would fire them for a bot (a pick-up the tactics module may also take, an interact the bots must not do). Name check on the node path,
   case-insensitive, 1 = leave this box alone: the keywords match the box's own LEAF name (after the last separator), a 'PCnnnn_' segment anywhere in the path also matches.
   GUESS: the path string [[obj+4]+0x6c] holds the whole path (or at least the leaf); the keywords include the leaf
   names of the pick-up children (cashbox, money_attach, attach01 under PCnnnn) so a leaf-only string still matches most of them. */
static int kvp_pickup_box(int on, const char *path)
{
    char l[200]; const char *leaf; int i, j;
    static const char *kw[] = { "cashregister", "cashdrawer", "cashbox", "moneybox", "money_attach", "jewel", "watches", "creditcard", "civilian", "waitress",
                                "clerk_", "gangmember", "fbi-agent", "senator", "hostage", 0 };
    if (!on || !path) return 0;
    for (i = 0; path[i] && i < (int)sizeof l - 1; i++) l[i] = (char)((path[i] >= 'A' && path[i] <= 'Z') ? path[i] + 32 : path[i]);
    l[i] = 0; leaf = l;
    for (i = 0; l[i]; i++) if (l[i] == '\\' || l[i] == '/' || l[i] == '!') leaf = l + i + 1;      /* the keywords look at the box's OWN leaf name only (the group separators are '\\' and '!'): a cop / script box under a 'Civilians!' group must stay */
    for (j = 0; kw[j]; j++) if (strstr(leaf, kw[j])) return 1;
    for (i = 0; l[i]; i++) if ((i == 0 || l[i - 1] == '\\' || l[i - 1] == '/' || l[i - 1] == '!') && l[i] == 'p' && l[i + 1] == 'c' && l[i + 2] >= '0' && l[i + 2] <= '9' && l[i + 3] >= '0' && l[i + 3] <= '9'
                                  && l[i + 4] >= '0' && l[i + 4] <= '9' && l[i + 5] >= '0' && l[i + 5] <= '9' && l[i + 6] == '_') return 1;      /* a 'PCnnnn_' pick-up segment */
    return 0;
}

/* OnlineTriggersSkipPickups name SOURCE (2026-11-02, bench CS1A DM03: the old read [[box+4]+0x6c] came back EMPTY for every box). Cause found in the code: klbf_trig_scan
   already holds node = [[box+0x24]+4] (the entity's scene node, the one kle_node reads the place from and klauto.c reads the name from: [[entity+4]+0x6c], klauto.c 1332),
   but the name read used [box+4], the controller object's own +4, not the entity's node. src 1 = the node name (first), src 2 = the legacy [box+4] read (kept as a
   fallback). Both empty -> src 0 and the box is kept. Returns kvp_pickup_box on the first non-empty name. GUESS: the node name string holds the path (or at least the leaf). */
static int kvp_pickup_decide(int on, const char *nodeNm, const char *legacyNm, int *src)
{
    const char *n = (nodeNm && nodeNm[0]) ? nodeNm : 0; int s = 1;
    if (!n && legacyNm && legacyNm[0]) { n = legacyNm; s = 2; }
    if (src) *src = n ? s : 0;
    return n ? kvp_pickup_box(on, n) : 0;
}

/* Box-name pick for klbf_ramp_name (2026-11-02; same wrong-object mistake as kvp_pickup_decide fixed): the scene-node name first (src 1), else the legacy [[box+4]+0x6c]
   read (src 2), else "" (src 0). Copies at most cap-1 chars into out (NUL-terminated). */
static void kvp_name_pick(const char *nodeNm, const char *legacyNm, char *out, int cap, int *src)
{
    const char *n = (nodeNm && nodeNm[0]) ? nodeNm : 0; int s = 1, i = 0;
    if (!n && legacyNm && legacyNm[0]) { n = legacyNm; s = 2; }
    if (src) *src = n ? s : 0;
    if (!out || cap < 1) return;
    if (n) for (; i < cap - 1 && n[i]; i++) out[i] = n[i];
    out[i] = 0;
}

/* Online escort humans (2026-11-02, bench ES1A/B DM03: "8 human(s) read" with 2 human seats): the session player table holds the AI heisters too, so a table heister whose
   feet are within r of a bot's own place IS that bot. 1 = it stands on a bot (drop it), 0 = keep. GUESS: r = 40 as klsync.c klsy_human ("40 units around a player's feet =
   his own body"); a NaN distance is not near. */
static int kvp_on_bot(const float f[3], const float (*bots)[3], int nb, float r)
{
    int b;
    for (b = 0; b < nb; b++) {
        float dx = f[0] - bots[b][0], dy = f[1] - bots[b][1], dz = f[2] - bots[b][2];
        if (dx * dx + dy * dy + dz * dz < r * r) return 1;
    }
    return 0;
}

#endif
