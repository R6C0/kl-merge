/* kldroptable_logic.h - [BotFill] type-1 drop table (klbf_dr[]) eviction, the PURE decision (no game memory, no log, no clock). Included by klbotfill.c and kldroptable_test.c.
   DT1A_DD07 round 1: all 133 type-1 pool objects are armed (hidden 1, never drained) at round start, the 32-slot table is filled by the first 32 of them, and a real drop
   (a dead carrier's 900000, unhidden) that lands on one of the other 101 pool objects is never tracked, so no bot is sent to it. When the table is full a candidate that is not a
   hidden never-drained pool object replaces the OLDEST hidden, never-drained entry that no bot is walking to. Only reached through klbf_df_see (OnlineStackProbe / DropFollow /
   DropTake on), so with those keys at 0 nothing changes. NOT run live. */
#ifndef KLDROPTABLE_LOGIC_H
#define KLDROPTABLE_LOGIC_H

/* one table slot as the eviction sees it (filled by klbotfill.c from klbf_dr[]) */
struct kdtb_ent {
    int used;              /* slot holds an object */
    int hid;               /* node hidden bit: 1 hidden, 0 shown, -1 unreadable */
    int drn;               /* armed within +-3 s of a real stack drain */
    int target;            /* a bot currently has it as its target */
    unsigned int age;      /* ms since first sighting (now - first, unsigned wrap safe) */
};

/* a candidate may push a pool object out unless it is itself a hidden pool object (hidden 1; a new object has never drained). hidden -1 (unreadable) counts as a real candidate: it is not
   the known pool signature, and the old code tracked it too. */
static int kdtb_cand_ok(int hid)
{
    return hid != 1;
}

/* a slot that may be replaced: hidden 1, never drained, not a bot's target */
static int kdtb_victim_ok(const struct kdtb_ent *e)
{
    return e->used && e->hid == 1 && e->drn == 0 && !e->target;
}

/* index of the slot to replace for a candidate with hidden bit cand_hid, or -1 (keep the table as it is). Oldest = largest age, the lowest index on a tie. */
static int kdtb_evict(const struct kdtb_ent *e, int n, int cand_hid)
{
    int i, best = -1; unsigned int ba = 0;
    if (!kdtb_cand_ok(cand_hid)) return -1;
    for (i = 0; i < n; i++) {
        if (!kdtb_victim_ok(&e[i])) continue;
        if (best < 0 || e[i].age > ba) { best = i; ba = e[i].age; }
    }
    return best;
}
#endif
