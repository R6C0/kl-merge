/* klgetup_logic.h - [BotFill] OnlineGetUp, the PURE decisions (no game memory, no log, no clock of its own). Included by klbotfill.c and klgetup_test.c.
   Two halves (re/bot_getup_online.md):
     HOST  : a downed human (his body's D state [[player+0x2948]+4] is 1 lying / 2 falling) gets the nearest free AI heister sent to him with the same
             order the Arcade rush uses (kle_order2); the order is repeated every KGU_REORDER_MS while he is not there yet.
     DOWNED MACHINE: a bot standing by his own body (the Arcade BotRange, 4 m, same floor) adds `per_s` presses' worth a second to the mash meter
             (kld_o.h.meter, [Down] MashHold) - the same thing kladren.c does for the Arcade human (kld_s.meter floor), as a local write on the machine
             that owns the get-up. Nothing is sent: the stock GettingUp message (0x6cd720) carries the rise to the others as in any online get-up. */
#ifndef KLGETUP_LOGIC_H
#define KLGETUP_LOGIC_H

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
static int kgu_recede(float prevD, float curD, float ordD)
{
    if (!(curD >= 0)) return 0;
    if (prevD >= 0 && curD - prevD >= KGU_RECEDE_STEP_CM) return 1;
    return ordD > 0 && curD - ordD > KGU_RECEDE_ORD_CM;
}

/* a helper counts when within `range` (cm) horizontally and `dy` (cm) in height */
static int kgu_helper_ok(float dist, float dy, float range, float dymax)
{
    return dist >= 0 && dist <= range && dy >= -dymax && dy <= dymax;
}

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

#endif
