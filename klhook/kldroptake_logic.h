/* kldroptake_logic.h - [BotFill] OnlineDropTake / OnlineDropTakeM, the PURE decision (no game memory, no log, no clock). Included by klbotfill.c and kldroptake_test.c.
   Q31/Q32/Q33 (DD07, DM06, DM01 online): the loot is CARRIED by cops, the stock actor-death script 0x6d2500 empties each type-0 stack and arms a type-1 drop object, the stack scan tracks
   the drop but skips it, so after 40-120 s the scan reads 0 armed stacks and every bot does OnlineIdleVan to an empty exit. Arcade's bots loot those drops. With OnlineDropTake=1 a bot that
   has no stack to take and carries nothing is given the nearest tracked drop that passes kdf_drop_ok (unhidden, armed after a real stack drain) within OnlineDropTakeM, and OnlineIdleVan
   is held back for it while such a drop exists. Default 0 = today. NOT run live. */
#ifndef KLDROPTAKE_LOGIC_H
#define KLDROPTAKE_LOGIC_H

/* one tracked type-1 drop as the pick sees it (filled by klbotfill.c from klbf_dr[]) */
struct kdt_cand {
    int hid;               /* node hidden bit: 1 hidden, 0 shown, -1 unreadable */
    int drn;               /* armed within +-3 s of a real stack drain */
    int amt;               /* amount, must be > 0 */
    int posok;             /* position readable */
    int taken;             /* another bot already walks to it */
    int bad;               /* blacklisted (a bot gave up on it) */
    float dist;            /* game units from the bot */
};

/* hidden/undrained/unreadable drops are never a target (round-start pool objects, SP2B: 'skipped: hidden 1 ... a round-start pool object'). Same rule as OnlineDropFollow (kdf_drop_ok). */
static int kdt_ok(const struct kdt_cand *c)
{
    return c->amt > 0 && c->posok && c->hid == 0 && c->drn != 0 && !c->bad;
}

/* max_d <= 0 = off (no pick, nothing exists). Returns the index of the nearest drop that is ok, free (not taken) and within max_d, or -1.
   *exists (may be NULL) = 1 when ANY ok drop within max_d exists, taken or not: the bot must not call the van while money still lies on the floor. */
static int kdt_pick(const struct kdt_cand *c, int n, float max_d, int *exists)
{
    int i, best = -1; float bd = 1e30f;
    if (exists) *exists = 0;
    if (max_d <= 0) return -1;
    for (i = 0; i < n; i++) {
        if (!kdt_ok(&c[i]) || !(c[i].dist <= max_d)) continue;
        if (exists) *exists = 1;
        if (c[i].taken) continue;
        if (c[i].dist < bd) { bd = c[i].dist; best = i; }
    }
    return best;
}

/* should this bot look for a drop at all: key on, no stack to take (best < 0), nothing carried, still allowed to carry more */
static int kdt_wanted(int on, int best, int tally, int grabs, int carry)
{
    return on && best < 0 && tally == 0 && grabs < carry;
}
#endif
