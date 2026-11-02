/* klcensus_logic.h - [BotFill] OnlineTriggersCensus "new cops" set, the PURE part (no game memory, no log, no clock). Included by klbotfill.c and klcensus_test.c.
   TP2 11-02: the live-cop count only fell (22 -> 21 -> 18) because bots kill cops faster than a wave arrives, so a wave can hide behind kills. The census keeps the actor
   pointers of the cops seen alive in the scan at the fire (fixed array, KCS_MAX); at +10 s / +30 s a live cop NOT in that set is "new" (arrived after the fire), a set member
   not seen alive any more is "gone". GUESS: a pooled actor reused for a respawn keeps its pointer and is not counted new (undercount, never a false wave). If more than KCS_MAX
   cops were alive, the overflow flag is set and the "new" figure is an upper bound. Default off with the census key, log only. */
#ifndef KLCENSUS_LOGIC_H
#define KLCENSUS_LOGIC_H

#define KCS_MAX 256

struct kcs_set { unsigned long p[KCS_MAX]; int n; int over; };

static void kcs_clear(struct kcs_set *s) { s->n = 0; s->over = 0; }

static int kcs_has(const struct kcs_set *s, unsigned long p)
{
    int i;
    for (i = 0; i < s->n; i++) if (s->p[i] == p) return 1;
    return 0;
}

/* adds p once; a full set sets .over and drops p. Returns 1 when p was added. */
static int kcs_add(struct kcs_set *s, unsigned long p)
{
    if (!p || kcs_has(s, p)) return 0;
    if (s->n >= KCS_MAX) { s->over = 1; return 0; }
    s->p[s->n++] = p; return 1;
}

/* one scan's tally against the base set (the cops at the fire): feed every live cop actor to kcs_tally_cop() */
struct kcs_tally { int live, fresh, kept; };

static void kcs_tally_clear(struct kcs_tally *t) { t->live = t->fresh = t->kept = 0; }

static void kcs_tally_cop(struct kcs_tally *t, const struct kcs_set *base, unsigned long p)
{
    t->live++;
    if (kcs_has(base, p)) t->kept++; else t->fresh++;
}

/* set members not seen alive in the tallied scan */
static int kcs_gone(const struct kcs_set *base, const struct kcs_tally *t)
{
    int g = base->n - t->kept; return g < 0 ? 0 : g;
}

#endif
