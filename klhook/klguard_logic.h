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
#endif
