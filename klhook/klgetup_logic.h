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

/* a helper counts when within `range` (cm) horizontally and `dy` (cm) in height */
static int kgu_helper_ok(float dist, float dy, float range, float dymax)
{
    return dist >= 0 && dist <= range && dy >= -dymax && dy <= dymax;
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

#endif
