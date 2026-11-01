/* klguard_logic.h - [BotFill] OnlineGuardMode, the PURE decisions (no game memory, no clock of its own). Included by klbotfill.c and klguard_test.c.
   BP5 (DD08): 47 free stacks, every one with a live cop within 25 m (3D, no alert / floor test), so no bot ever found an unguarded stack and OnlineGuardTake=0
   held them until the idle-van branch sent them out empty. GUESS: the map is dense / several floors fall inside one 25 m sphere (ncop was not logged).
     floor gate : a cop on another floor (|dy| > floor_cm) does not guard the stack (floor_cm <= 0 = off, the old 3D test).
     bypass     : when every free stack is guarded and there are at least min_stacks of them (the test cannot tell stacks apart), the bot takes the stack with
                  the fewest cops near it (ties: the nearest to the bot), at most one release per gap_ms for the whole host (BO8c: all 5 went in at once). */
#ifndef KLGUARD_LOGIC_H
#define KLGUARD_LOGIC_H
#include <math.h>

/* does a cop at c guard a stack at s? radius > 0 required; NaN never guards */
static int kgg_guards(const float *c, const float *s, float radius, float floor_cm)
{
    float dx = c[0] - s[0], dy = c[1] - s[1], dz = c[2] - s[2], d2 = dx * dx + dy * dy + dz * dz;
    if (!(d2 == d2) || !(radius > 0)) return 0;
    if (floor_cm > 0 && !(fabs(dy) <= floor_cm)) return 0;
    return d2 <= radius * radius;
}

/* may the bypass fire? nguard = guarded free stacks, nfree = free stacks (all guarded when equal); last = tick of the last release (0 = none) */
static int kgg_bypass_ok(int nguard, int nfree, int min_stacks, unsigned int now, unsigned int last, unsigned int gap_ms)
{
    if (nguard <= 0 || nguard != nfree || nguard < min_stacks) return 0;
    return last == 0 || (int)(now - last) >= (int)gap_ms;
}

/* pick among guarded stacks: fewest cops, tie nearest to the bot; cnt[i] < 0 = not a candidate; returns index or -1 */
static int kgg_pick(const int *cnt, const float *dist, int n)
{
    int i, best = -1;
    for (i = 0; i < n; i++) {
        if (cnt[i] < 0 || !(dist[i] == dist[i])) continue;
        if (best < 0 || cnt[i] < cnt[best] || (cnt[i] == cnt[best] && dist[i] < dist[best])) best = i;
    }
    return best;
}

/* OnlineGuardLiveOnly: radius that counts a cop as guarding a stack. BP8 (DD08): the 47 stacks sit in one cluster ~12 m x 5.5 m, so a 25 m sphere around ANY stack
   holds the same ~38 cops (nothing to tell stacks apart). tight > 0 and < wide (e.g. OnlineLootFinishCopM 8 m) narrows it; otherwise the wide radius. */
static float kgg_radius(float wide, float tight, int live_only)
{
    if (live_only && tight > 0 && (wide <= 0 || tight < wide)) return tight;
    return wide;
}

/* OnlineGuardLiveOnly: BP9 (DD08) logged the first cops at exactly (0,0,0) at the round start (GUESS: not placed yet). Same 1 cm test as klbotfill.c's feet reads. */
static int kgg_origin(const float *p)
{
    return fabsf(p[0]) <= 1 && fabsf(p[1]) <= 1 && fabsf(p[2]) <= 1;
}

/* OnlineGuardCarrierCm (wk-botscore-1101, default 0 = off): a cop standing within carrier_cm of a stack is the person the money is ON (Q31 DD07: the cop spread
   equals the stack spread on all three axes, 5 cops for 5 stacks; DM06 and DD05 the same), not a separate guard. Arcade's bots take those stacks (ARC1: DD05 6/6,
   DD07 5/5, DM06 4/4); the 8 m / 25 m guard test counts the carrier and holds the bots for the whole round. GUESS: 150 cm; carrier_cm <= 0 = off.
   GUESS (premise): "the cop at the stack is its carrier" is a CORRELATION read from the Q31 logs (cop spread = stack spread), not proven. A real guard standing within
   carrier_cm of a stack is dropped from the guard count too (risk: the bots walk into it and die, as in ARC1 DD07). */
static int kgg_carrier(const float *c, const float *s, float carrier_cm)
{
    float dx = c[0] - s[0], dy = c[1] - s[1], dz = c[2] - s[2];
    if (!(carrier_cm > 0)) return 0;
    return (dx * dx + dy * dy + dz * dz) <= carrier_cm * carrier_cm;      /* NaN compares false: not a carrier */
}

/* OnlinePartialRetry (wk-botscore-1101, default 0 = off): Q31 DD06 R1: five bots stopped a stack part-way ("bot moved away" from the stack, 4 to 10 m, limit 2.5 m), every other stack was blacklisted
   for the 45 s retry, so the same tick they were sent to the exit with their partial tally and never looked at a stack again (hook tally 3.13M, 2 stacks counted taken of 8, BEHIND Arcade's 5.55M / 8 of 8, not zero; scorecard re/bots_online_scorecard_1101.md).
   hold = stay at the pick (phase 0) instead of committing to the exit walk: a carrier with room for another grab, a blacklisted/taken stack still in the list,
   the partial stop younger than wait_ms and enough clock left. partial_at 0 = no partial stop. */
static int kgg_partial_hold(int on, int tally, int grabs, int carry, int idle_van, int nhold, unsigned int now, unsigned int partial_at, unsigned int wait_ms, float left_s, float min_left_s)
{
    if (!on || tally <= 0 || idle_van || grabs >= carry || nhold <= 0 || !partial_at) return 0;
    if ((int)(now - partial_at) >= (int)wait_ms) return 0;
    return left_s > min_left_s;
}
#endif
