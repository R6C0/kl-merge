/* klwaitvan_logic.h - [BotFill] OnlineLegWaitVan / OnlineLegWaitIdx / OnlineLegWaitMaxS, the PURE decision (no game memory, no log, no clock). Included by klbotfill.c and klwaitvan_test.c.
   Bench RT3 (DM09, OnlineLegScale + OnlineLegStallS, re/dm09_van_timing_1101.md): the legs now complete (12 reached) but all 7 bots died on street legs 2..6 between 23:42:31 and 23:43:16,
   because the van's boarding object first appeared (probe state 2) at 23:43:06, about 249 s into the round and 17 s before the round was over. The bots walked into the street minutes
   before the van existed. A bot with loot that is heading for the escape stops at the hold leg (OnlineLegWaitIdx, 0-based) and waits there while the van state is below 2 (and the van was
   not called by the hook); at state >= 2 it runs the remaining legs. All default 0 = today. NOT run live. */
#ifndef KLWAITVAN_LOGIC_H
#define KLWAITVAN_LOGIC_H

/* wait state of one bot (klbf_ob[].wv) */
#define KWV_IDLE 0         /* not waiting, not released */
#define KWV_WAITING 1      /* standing at the hold leg */
#define KWV_RELEASED 2     /* done (van came, or the cap ran out): never waits again this route */

/* what the pass does with the bot this tick */
#define KWV_NONE 0         /* nothing: the leg logic runs as before */
#define KWV_START 1        /* the bot arrived at the hold leg and the van is not there: start waiting (log) */
#define KWV_HOLD 2         /* keep waiting: the leg timeout / stall must not fire */
#define KWV_REL_VAN 3      /* the van is there (state >= 2, or the hook called it): release (log) */
#define KWV_REL_CAP 4      /* the safety cap ran out: release (log) */

/* the van is "there": probe state [rules+0x1dc] 2 or higher (2/3/4 coming / waiting, 5+ leaving: nothing left to wait for), or the hook has called it. state < 0 = unreadable = not there. */
static int kwv_van_ready(int vstate, int called)
{
    return vstate >= 2 || called != 0;
}

/* The decision. on = OnlineLegWaitVan and the legs exist; wv = the bot's wait state; leg = its current leg (0-based), idx = OnlineLegWaitIdx;
   arrived = the leg logic would advance now (reached, timed out or stalled); waitedMs = time since the wait began; capS = OnlineLegWaitMaxS (0 = no cap). */
static int kwv_step(int on, int wv, int leg, int idx, int arrived, int vstate, int called, unsigned long waitedMs, int capS)
{
    if (!on || wv == KWV_RELEASED) return KWV_NONE;
    if (wv == KWV_WAITING) {
        if (kwv_van_ready(vstate, called)) return KWV_REL_VAN;
        if (capS > 0 && waitedMs >= (unsigned long)capS * 1000ul) return KWV_REL_CAP;
        return KWV_HOLD;
    }
    if (leg != idx || !arrived) return KWV_NONE;
    return kwv_van_ready(vstate, called) ? KWV_NONE : KWV_START;
}

#define KWV_CALL_GRACE_MS 30000ul      /* GUESS: the call is made at the latest this long after the first carrier began to wait, even if a carrier is still on a leg below the hold */

/* OnlineLegWaitCall: should the hook call the van now, from the hold? callOn = the key, waitOn = OnlineLegWaitVan, afterLegs = OnlineVanAfterLegs, vhKnown = the exit trigger's vehicle handle
   is known, called = already called (by anyone), vstate = probe state (0 = nothing under way; the game's own call refuses otherwise), nWait = carriers waiting at the hold, nNeed = OnlineLegWaitCallN
   (0 = all: wait for the carriers still below the hold), nBelow = live carriers (phase 2, loot) still on a leg below the hold, firstAgeMs = how long the longest-waiting carrier has waited.
   Call when someone waits and: nNeed >= 1 carriers wait, or no carrier is left below the hold, or the grace ran out.
   klbf_ot_call_van keeps the rest (Sv vtable, state 0, not last, no hold, clock >= 20 s); it needs no bot near the trigger (0x71e180 takes the rules object and the vehicle handle only). */
static int kwv_call_ok(int callOn, int waitOn, int afterLegs, int vhKnown, int called, int vstate, int nWait, int nNeed, int nBelow, unsigned long firstAgeMs)
{
    if (!(callOn && waitOn && afterLegs && vhKnown && !called && vstate == 0 && nWait >= 1)) return 0;
    return (nNeed >= 1 && nWait >= nNeed) || nBelow <= 0 || firstAgeMs >= KWV_CALL_GRACE_MS;
}

/* A hook call made from the hold must not strip the legs (klway_logic.h kwy_legs_left returns 0 once `called`): the legs see `called` as 0 while this bot still has legs and the call was the hook's own wait call. */
static int kwv_legs_called(int called, int hookWaitCall, int waitOn, int leg, int nlegs)
{
    if (called && hookWaitCall && waitOn && leg < nlegs) return 0;
    return called;
}

/* A wait that has gone on this long with no exit trigger handle known is worth a log line */
static int kwv_novh_log(int waitOn, int vhKnown, unsigned long firstAgeMs)
{
    return waitOn && !vhKnown && firstAgeMs >= 30000ul;
}

/* The stall cut (OnlineLegStallS) is off for the legs once the van is there: the bots run, they do not stop to be re-pathed in the street. */
static int kwv_nostall(int on, int vstate, int called)
{
    return on && kwv_van_ready(vstate, called);
}
#endif
