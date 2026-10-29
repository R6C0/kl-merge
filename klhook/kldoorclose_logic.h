/* kldoorclose_logic.h - pure logic of kldoorclose.c ([KLHook] DoorCloseMs), so kldoorclose_test.c can check it off-game. 2026-10-28.
 * All times are GetTickCount() ms; differences are unsigned so a tick wrap does not matter. */
#ifndef KLDOORCLOSE_LOGIC_H
#define KLDOORCLOSE_LOGIC_H

#define KLDC_N          8                      /* proxies followed at once (Retomoto has 2 lifts; M09_B lobby banks may add more) */
#define KLDC_STALE_MS   120000                 /* a close this long overdue is given up (level left): nothing is touched */

struct kldc_p { unsigned long me, at, seen; int done; };   /* proxy object, tick of its open, leaf-0 start ms last seen, closed/given up */

/* slot for proxy 'me': its own, else an empty or finished one, else -1 */
static int kldc_slot(const struct kldc_p *t, int n, unsigned long me)
{
    int k, f = -1;
    for (k = 0; k < n; k++) { if (t[k].me == me) return k; if (f < 0 && (!t[k].me || t[k].done)) f = k; }
    return f;
}

/* slot for a NEWLY FOUND proxy: its own, else an empty one, else -1. Never evicts a followed (done) slot: that thrashed the table and re-logged
   'following' every walk when more proxies than slots qualified. */
static int kldc_slot_free(const struct kldc_p *t, int n, unsigned long me)
{
    int k, f = -1;
    for (k = 0; k < n; k++) { if (t[k].me == me) return k; if (f < 0 && !t[k].me) f = k; }
    return f;
}

/* The door proxy's handler ran (an OPEN): leaf-0 start ms 'st' (the game ms of the restart, [leaf+0x34]) differs from the last one seen, the
   leaf plays ([leaf+0x99]), and the leaf's ints [leaf+0xd0]/[leaf+0xd4] are the proxy's own first/last ([proxy+0x23c]/[+0x240], nonzero last):
   the handler wrote them. Our own close writes 75/160 instead, so it never counts as an open. */
static int kldc_is_open(unsigned long seen, unsigned long st, int act99, unsigned long ifirst, unsigned long ilast, unsigned long pfirst, unsigned long plast)
{
    return st && st != seen && act99 && ilast && ifirst == pfirst && ilast == plast;
}

/* tick of the open, from the game-ms clock: the start was (gms - st) ms ago */
static unsigned long kldc_open_at(unsigned long now, unsigned long gms, unsigned long st)
{
    unsigned long at = (!gms || gms < st) ? now : now - (gms - st);   /* unreadable / odd clock: treat as just now, never wrap */
    return at ? at : 1;
}

/* 0 = not yet, 1 = close now, 2 = give up (stale), 3 = due but a player is at the car: postponed, ask again next tick */
static int kldc_step(unsigned long now, unsigned long at, int ms, int busy)
{
    unsigned long el = now - at;
    if (ms <= 0 || el < (unsigned long)ms) return 0;
    if (el > (unsigned long)ms + KLDC_STALE_MS) return 2;
    return busy ? 3 : 1;
}
/* Online (DoorCloseRemote=1) gate: 1 = check entry i too (on, a network session, and i is not one of the two LOCAL selectors, which are always
   checked). kldc_busy calls it once with i=0, sel=-1 before walking the session hero table (10-29). */
static int kldc_remote_slot(int i, int sel0, int sel1, int online, int remote_on)
{
    return remote_on && online && i >= 0 && i < 28 && i != sel0 && i != sel1;
}

/* Remote hold (DoorCloseRemote=1, 10-29 A1HOLD1: a joiner quit while in the car, his table entry kept its last feet and the host held the doors until
   the stale give-up). Per table entry: a hold counts only while the entry's feet moved within still_ms AND the continuous time it has been in a car box
   is under max_ms. A departed peer's feet never change, so his hold ends still_ms later. A live player who stands still in the car for longer
   than still_ms also stops holding (the doors then close: accepted, he can step out and in). max_ms bounds even a feet-jittering stale entry;
   it re-arms only after the entry leaves every car box. Local players are not subject to this. */
struct kldc_r { float f[3]; unsigned long moved, since; };   /* last feet, tick feet last moved, tick this entry's continuous box stay began (0 = not in a box) */
#define KLDC_MOVE_EPS 0.5f                     /* GUESS: world units; the feet of a standing player are bit-stable, a walking one moves far more per tick */
static int kldc_rhold(struct kldc_r *r, unsigned long now, const float *feet, int in_box, int still_ms, int max_ms)
{
    int k, mv = 0;
    for (k = 0; k < 3; k++) { float d = feet[k] - r->f[k]; if (d > KLDC_MOVE_EPS || d < -KLDC_MOVE_EPS) mv = 1; }
    if (!r->moved || mv) { r->moved = now ? now : 1; for (k = 0; k < 3; k++) r->f[k] = feet[k]; }
    if (!in_box) { r->since = 0; return 0; }
    if (!r->since) { r->since = now ? now : 1; r->moved = r->since; }       /* first look inside the box: counts as fresh */
    if (still_ms > 0 && now - r->moved >= (unsigned long)still_ms) return 0;
    if (max_ms > 0 && now - r->since >= (unsigned long)max_ms) return 0;
    return 1;
}
#endif
