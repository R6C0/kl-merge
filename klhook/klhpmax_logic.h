/* klhpmax_logic.h - ONE registry for every hook writer of an AI heister's MAXIMUM health (health object [actor+0x5fc]: +4 current, +8 maximum, +0x24 the actor), the PURE part (no game memory,
   no log, no clock). Included by klgrudge.c (CrewHealth / BackstabHealth / traits, Arcade and [Bots] OnlineCrewHealth), klbotfill.c (klbf_ot_health, [BotFill] OnlineHealthMul),
   klbotdown.c (FedHealth) and klhpmax_test.c.
   BUG (bench RV1A_DD05 2026-11-05, host log, one bot, the game gave 350): each writer kept its OWN note of 'the game's maximum' and took any maximum that was not its own last write as
   'a new maximum of the game's', so the two compounded: grudge 350 -> 700, botfill 700 -> 3500, grudge 3500 -> 7000 ('the game gave 3500'), botfill 7000 -> 35000, grudge -> 70000, botfill
   -> 350000 (it stopped only because both refuse max > 100000). Intended 350 x 2 x 5 = 3500. Every online bench since 11-04 had bots at 140000-350000, so no online AI heister ever went down.
   Here: per health object (h, actor) the registry holds the game's base, the last value ANY hook writer put there (wrote, 0 = nothing of ours) and one factor per writer (1 = none). A maximum that
   equals wrote is the hook's, never the game's; anything else (a respawn that writes the same 350 again included) is the game's and is the new base. The wanted maximum is always base x the
   product of the factors, so the writers compose and a writer that lets go only drops its own factor (khpm_plan with 1). */
#ifndef KLHPMAX_LOGIC_H
#define KLHPMAX_LOGIC_H
#include <math.h>

#define KHPM_N 64                  /* objects remembered (a round has 4 to 12 AI heisters; stale ones are reused first) */
enum { KHPM_GRUDGE, KHPM_BOTFILL, KHPM_FED, KHPM_W };      /* one factor slot per writer */
struct khpm_ent { unsigned int h, actor; int used; float base, wrote, f[KHPM_W]; };
static struct khpm_ent khpm_t[KHPM_N];
static int khpm_next;
typedef int (*khpm_alive_fn)(unsigned int h, unsigned int actor);      /* does the object h still belong to that actor (the caller reads [h+0x24]) */

static int khpm_same(float a, float b) { return fabsf(a - b) <= 0.01f; }

/* the entry of (h, actor); create = make one when there is none (a free slot, else the first whose object is gone, else round robin). The same h with another actor is a reused object: reset. */
static struct khpm_ent *khpm_find(unsigned int h, unsigned int actor, khpm_alive_fn alive, int create)
{
    int i, k; struct khpm_ent *e;
    for (i = 0; i < KHPM_N; i++) if (khpm_t[i].used && khpm_t[i].h == h) {
        e = &khpm_t[i];
        if (e->actor == actor) return e;
        if (!create) return 0;
        goto fresh;
    }
    if (!create) return 0;
    for (i = 0; i < KHPM_N && khpm_t[i].used; i++) ;
    for (k = 0; i == KHPM_N && k < KHPM_N; k++) if (alive && !alive(khpm_t[k].h, khpm_t[k].actor)) i = k;
    if (i == KHPM_N) { i = khpm_next; khpm_next = (khpm_next + 1) % KHPM_N; }
    e = &khpm_t[i];
fresh:
    e->used = 1; e->h = h; e->actor = actor; e->base = 0; e->wrote = 0;
    for (k = 0; k < KHPM_W; k++) e->f[k] = 1.0f;
    return e;
}

/* a maximum was read: the hook's own (== wrote) changes nothing; else it is the game's (first sight, a new object, a respawn that writes the same number again) and becomes the base.
   A new base also drops every writer's factor (review wou2kgqnw: a pooled actor / object at the same addresses next round kept last round's factors, so OnlineHealthMul alone wrote x 2 x 5
   with OnlineCrewHealth off): a writer still on sets its factor again on its next pass, one that is off no longer counts. */
static void khpm_see(struct khpm_ent *e, float max)
{
    int k;
    if (e->wrote != 0 && khpm_same(max, e->wrote)) return;
    if (e->base == 0 || e->wrote != 0 || !khpm_same(max, e->base)) { e->base = max; e->wrote = 0; for (k = 0; k < KHPM_W; k++) e->f[k] = 1.0f; }
}

/* writer w now wants factor f (1 = let go). Returns 1 and the maximum to write in *want when the value read (max) is not it yet. Call khpm_see(e, max) first. */
static int khpm_plan(struct khpm_ent *e, int w, float f, float max, float *want)
{
    int k; float t = e->base;
    e->f[w] = f;
    for (k = 0; k < KHPM_W; k++) t *= e->f[k];
    *want = t;
    return !khpm_same(max, t);
}

/* the write of t went in: remember it as the hook's (0 when t is the game's own number again) */
static void khpm_done(struct khpm_ent *e, float t) { e->wrote = khpm_same(t, e->base) ? 0 : t; }
#endif
