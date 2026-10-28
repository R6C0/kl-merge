/* klleaf_logic.h - pure logic of the escape-lift leaf probe (klprobe.c [Probe] DoorLeaves) and of kljoin.c's door-aware CarStall
 * ([Join] CarStallAfterDoorMs), so klleaf_test.c can check it off-game. 2026-10-28 (A1LIFT3g could not tell whether the door leaves move).
 * All times are GetTickCount() ms; differences are unsigned so a tick wrap does not matter. */
#ifndef KLLEAF_LOGIC_H
#define KLLEAF_LOGIC_H

#define KLLEAF_SPAN_MS  6000                   /* a sample series lasts 6 s after an accepted door proxy ... */
#define KLLEAF_STEP_MS   250                   /* ... one sample every 250 ms */

/* Sample number (1-based) that is due, 0 = none yet / series over.
   acc = tick of the proxy accept (0 = none), last = how many samples of THIS series were taken. Returns last+1 when due, else 0.
   The first sample is due at once at the accept (n=1 at t=0), the last at t = SPAN (n = SPAN/STEP + 1 = 25). */
static int klleaf_due(unsigned long now, unsigned long acc, int last)
{
    unsigned long el;
    if (!acc) return 0;
    el = now - acc;
    if (el > KLLEAF_SPAN_MS + KLLEAF_STEP_MS) return 0;                 /* series over (a late tick still gets its final sample above) */
    if (last >= (int)(KLLEAF_SPAN_MS / KLLEAF_STEP_MS) + 1) return 0;
    return el >= (unsigned long)last * KLLEAF_STEP_MS ? last + 1 : 0;
}

/* CarStall gate. 1 = the stall timer must NOT count now. after_ms 0 = old behaviour (never gated).
   Reference = the last lift-proxy accept only (door_at, 0 = never seen: the SHIP build or [Probe] DoorProxy off -> never gated, CarStall
   as before). Not the ride start: the ride box (KLJoin box 9) is entered AFTER the doors' own trigger box, so gating on it would only push
   every SHIP jump past CarWait (c9 review 10-28). A stale accept (an earlier fire) is simply older than after_ms. */
static int klleaf_stall_gated(unsigned long now, unsigned long door_at, int after_ms)
{
    if (after_ms <= 0 || !door_at) return 0;
    return now - door_at < (unsigned long)after_ms;
}
#endif
