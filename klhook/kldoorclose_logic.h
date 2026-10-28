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
#endif
