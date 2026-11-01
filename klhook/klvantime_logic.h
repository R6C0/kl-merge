/* klvantime_logic.h - [BotFill] OnlineVanAfterLegs / OnlineVanBoPos / OnlineVanFarHold, the PURE decisions (no game memory, no log, no clock). Included by klbotfill.c and klvantime_test.c.
   Research wk-vantime-1101 (re/dm09_van_timing_1101.md), from the RT2L log (DM09, 7 bots, 8 legs, 0 boarded):
     - the scan took the vehicle object's STALE node (24235, -59842, 13883) for the van (OnlineVanPosSane was 0): with a van "known" the exit-trigger lookup was skipped (vh 0), nothing
       ever called the van (klbf_ot_arrive needs a trigger), and after leg 8 the bots were ordered at the stale place;
     - the van came only through LastVehicle at clock 1.2 s: state 0 -> 2 (drives in, 7 s) -> 4 (waits) -> 6, the boarding object [rules+0x1e0] at (-1852, 121, 8675) -> (-1851, 113, 10462);
     - OnlineVanHold never held: it only looks at state 3 (DM09 showed 2/4/6) with 20 s or more on the clock, and its walkers need a goal (box or trigger; both unknown).
   All three keys default 0 = today. NOT run live. */
#ifndef KLVANTIME_LOGIC_H
#define KLVANTIME_LOGIC_H
#include <math.h>

#define KVT_ABS_CM 40000.0f      /* as KVP_ABS_CM (klgetup_logic.h): a coordinate beyond 400 m is not a place on these maps */
#define KVT_REF_CM 50000.0f      /* as KVP_REF_CM: within 500 m of an exit trigger / escape box */
#define KVT_FAR_CAP_S 40         /* GUESS: the hold may run this long when a bot with loot is still far from the box (the plain OnlineHoldMaxS is 15 s); the klbotfill.c key OnlineVanFarHoldS overrides */

/* OnlineVanAfterLegs: 1 = the phase-2 walk treats the van as NOT known once the exit trigger is (the trigger lookup also runs while a van object is known; the legs, the arrival at
   the trigger, the van call and the stall test then run as on a stock map). Off or no trigger yet: the old rules. */
static int kvt_van_for_walk(int on, int triggerKnown, int vanKnown)
{
    if (on && triggerKnown) return 0;
    return vanKnown != 0;
}

/* OnlineVanAfterLegs: may the exit-trigger lookup run although a van object is known? (the old rule: only without a van) */
static int kvt_lookup_ok(int on, int vanKnown)
{
    return on || !vanKnown;
}

/* OnlineVanBoPos: is the boarding object's place [rules+0x1e0] -> node usable as the walk goal? on, van state 1..4 (GUESS: DM09 showed 2 coming and 4 waiting; DD maps 1/3), not
   the origin (an unplaced node), every coordinate within KVT_ABS_CM, and (when refs exist) within KVT_REF_CM of one exit trigger / escape box place. */
static int kvt_bo_ok(int on, int vstate, const float *p, int nref, const float (*ref)[3])
{
    int i;
    if (!on || vstate < 1 || vstate > 4) return 0;
    for (i = 0; i < 3; i++) if (!(fabsf(p[i]) <= KVT_ABS_CM)) return 0;      /* also rejects NaN */
    if (fabsf(p[0]) <= 1 && fabsf(p[1]) <= 1 && fabsf(p[2]) <= 1) return 0;
    if (nref <= 0) return 1;
    for (i = 0; i < nref; i++) {
        float dx = p[0] - ref[i][0], dy = p[1] - ref[i][1], dz = p[2] - ref[i][2];
        if (dx * dx + dy * dy + dz * dz <= KVT_REF_CM * KVT_REF_CM) return 1;
    }
    return 0;
}

/* OnlineVanBoPos: 1 = a bot that is past its legs (called, or no leg left) and has no escape box to walk to goes to the boarding object instead of the trigger / the van object */
static int kvt_use_bo(int boOk, int bxOn, int called, int leg, int nlegs)
{
    return boOk && !bxOn && (called || leg >= nlegs);
}

/* OnlineVanFarHold: the van hold (klbf_vh_pass) also runs in state 4 (GUESS: the waiting state of DM09's van; DD's is 3) */
static int kvt_hold_state_ok(int farOn, int vstate)
{
    return vstate == 3 || (farOn && vstate == 4);
}

/* OnlineVanFarHold: a walker with loot that is farther than holdM (but still walking, phase 2) counts as "in range" for the hold: the effective nearest distance becomes nearM.
   nFar = such walkers, dmin = the old nearest-walker distance (1e30 = none). */
static float kvt_eff_dmin(int farOn, float dmin, int nFar, float nearM)
{
    if (farOn && nFar > 0 && dmin > nearM) return nearM;
    return dmin;
}

/* OnlineVanFarHold: the cap of one visit in seconds. A far walker seen during the visit lifts it to farS (never lowered again in the same visit, so a walker that arrives does not cut the hold). */
static int kvt_cap_s(int farOn, int farSeen, int baseS, int farS)
{
    if (farOn && farSeen && farS > baseS) return farS;
    return baseS;
}

/* OnlineVanFarHold: count the walkers (phase 2, tally > 0) farther than holdM from the goal. d[] are horizontal cm; n entries; carrier[i] 1 = tally > 0. */
static int kvt_count_far(const float *d, const int *carrier, int n, float holdM)
{
    int i, c = 0;
    for (i = 0; i < n; i++) if (carrier[i] && d[i] > holdM) c++;
    return c;
}
#endif
