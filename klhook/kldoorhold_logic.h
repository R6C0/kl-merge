/* kldoorhold_logic.h - [BotFill] OnlineDoorHold / OnlineDoorHoldS, the PURE decision (no game memory, no log, no clock). Included by klbotfill.c and kldoorhold_test.c.
   Q34B (DD01 online): the vault cases sit behind doors (ZOnlineMoneyCtrl +0x5c = 1) that the Ally squad scripts kick open (KickDoorBehaviourRout -> 'DoorOpened'). The tactics order every bot to
   the first armed stack as soon as ONE door opens (10 armed + 48 shut at +38 s, +48 stays all round), which pulls the bots out of their squad scripts, so the other doors are never kicked.
   Arcade opens all 58 by +105 s. With OnlineDoorHold=1 a bot with an empty tally gets NO new stack order while shut doors remain, for at most OnlineDoorHoldS s from the round start, or until the
   shut count has not fallen for 25 s since the first armed stack appeared (GUESS 25 s: a squad kick cycle is ~10-20 s in the Q34B log). Default 0 = today. NOT run live. */
#ifndef KLDOORHOLD_LOGIC_H
#define KLDOORHOLD_LOGIC_H

#define KDH_STALL_MS 25000u
enum { KDH_NONE = 0, KDH_OPEN = 1, KDH_TIMER = 2, KDH_STALL = 3, KDH_LATE = 4 };   /* end reasons (KDH_LATE: the clock is low, the late-exit rules own the bots) */

struct kdh_st {
    int state;             /* 0 not started, 1 holding, 2 ended (latched for the round) */
    int reason;            /* KDH_* once ended */
    int ev;                /* 1 = hold just started, 2 = just ended: the caller logs it and clears this */
    int armed;             /* an armed stack has been seen this round */
    int min_shut;          /* lowest shut count seen since the first armed stack */
    int zero_n;            /* consecutive ticks with no shut stack (2 = all open) */
    unsigned zero_now;     /* the tick of the last zero count */
    unsigned min_at;       /* tick when min_shut was reached (or the first armed stack appeared) */
};

static int kdh_clamp(int s) { return s < 20 ? 20 : s > 150 ? 150 : s; }

/* one tick (idempotent for the same now). start = round start tick, nshut = stacks behind shut doors, narmed = armed takeable stacks, late = clock is low. Returns 1 while holding. */
static int kdh_step(struct kdh_st *h, int on, int hold_s, unsigned now, unsigned start, int nshut, int narmed, int late)
{
    if (!on || h->state == 2) return 0;
    if (h->state == 0) {
        if (nshut <= 0) return 0;                       /* no shut doors: nothing to wait for, nothing latched */
        h->state = 1; h->ev = 1;
    }
    if (narmed > 0 && !h->armed) { h->armed = 1; h->min_shut = nshut; h->min_at = now; }
    if (h->armed && nshut < h->min_shut) { h->min_shut = nshut; h->min_at = now; }
    if (nshut > 0) h->zero_n = 0;
    else {      /* review: one zero tick may be a failed registry read; "all open" needs two different ticks in a row (same now = same tick, the caller runs this once per bot) */
        if (!h->zero_n || now != h->zero_now) { h->zero_n++; h->zero_now = now; }
        if (h->zero_n >= 2) { h->state = 2; h->reason = KDH_OPEN; h->ev = 2; return 0; }
    }
    if (late) { h->state = 2; h->reason = KDH_LATE; h->ev = 2; return 0; }
    if ((unsigned)(now - start) >= (unsigned)kdh_clamp(hold_s) * 1000u) { h->state = 2; h->reason = KDH_TIMER; h->ev = 2; return 0; }
    if (h->armed && (unsigned)(now - h->min_at) >= KDH_STALL_MS) { h->state = 2; h->reason = KDH_STALL; h->ev = 2; return 0; }
    return 1;
}

/* does the hold apply to this bot: only a bot that carries nothing; a carrier keeps heading for the van */
static int kdh_applies(int holding, int tally) { return holding && tally == 0; }
#endif
