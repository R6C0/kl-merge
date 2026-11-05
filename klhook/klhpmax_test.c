/* klhpmax_test.c - off-game harness for klhpmax_logic.h (the one registry of every hook writer of an AI heister's maximum health; klgrudge.c, klbotfill.c and klbotdown.c include the same header). No windows.h.
   The writers below repeat, call for call, what klgrudge.c kly_health2 / kly_undo, klbotfill.c klbf_ot_health and klbotdown.c (FedHealth) do around the registry; the OLD_* pair repeats the
   code before the fix (each writer's private 'the game's maximum' / 'my last write') and is run to show the harness sees the bug (RV1A_DD05 2026-11-05: 350 -> 350000).
   Build: cl /nologo /W3 klhpmax_test.c /Fe:klhpmax_test.exe     Run: klhpmax_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klhpmax_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

#define H 0x2000u
#define A 0x1000u
static struct { float cur, max; unsigned int actor; } ob;      /* the health object: +4 current, +8 maximum, +0x24 the actor */
static int alive(unsigned int h, unsigned int a) { return h == H && ob.actor == a; }
static void game_gives(float max) { ob.max = max; ob.cur = max; }      /* the game makes / refills the object (a respawn writes the same number again) */

/* klgrudge.c kly_health2 (+ klbotfill.c's guards): factor f of writer GRUDGE */
static float g_ours;      /* b->hwrote */
static void grudge(float f)
{
    struct khpm_ent *e; float wmax, wcur;
    if (f == 1.0f && g_ours == 0) return;
    if (!(e = khpm_find(H, A, alive, f != 1.0f || g_ours != 0))) return;
    khpm_see(e, ob.max);
    if (!khpm_plan(e, KHPM_GRUDGE, f, ob.max, &wmax)) { g_ours = f != 1.0f ? e->base * f : 0; return; }
    if (ob.cur <= 0) return;      /* hwrote unchanged, so a put-back is tried again */
    wcur = ob.cur * wmax / ob.max; ob.max = wmax; ob.cur = wcur; khpm_done(e, wmax);
    g_ours = f != 1.0f ? e->base * f : 0;      /* only once the write is in */
}
/* klgrudge.c kly_undo: only our factor goes */
static void grudge_undo(void)
{
    struct khpm_ent *e; float v;
    if (g_ours != 0 && (e = khpm_find(H, A, alive, 0)) != 0) {
        khpm_see(e, ob.max);
        if (khpm_plan(e, KHPM_GRUDGE, 1.0f, ob.max, &v)) { float c = ob.cur * v / ob.max; ob.max = v; khpm_done(e, v); if (ob.cur > 0) ob.cur = c; }
    }
    g_ours = 0;
}
/* klbotfill.c klbf_ot_health: factor mul of writer BOTFILL (hv = what it just read) */
static void botfill(int mul)
{
    struct khpm_ent *e; float t, c;
    if (mul <= 1) return;
    if (!(ob.cur > 0) || ob.max < 1 || ob.max > 100000.0f) return;
    if (!(e = khpm_find(H, A, alive, 1))) return;
    khpm_see(e, ob.max);
    if (!khpm_plan(e, KHPM_BOTFILL, (float)mul, ob.max, &t)) return;
    c = ob.cur * t / ob.max; ob.max = t; ob.cur = c; khpm_done(e, t);
}
/* klbotdown.c FedHealth in / out */
static void fed_in(float k)
{
    struct khpm_ent *e = khpm_find(H, A, alive, 1); float nmax;
    khpm_see(e, ob.max); khpm_plan(e, KHPM_FED, k, ob.max, &nmax);
    ob.cur = ob.cur * nmax / ob.max; ob.max = nmax; khpm_done(e, nmax);
}
static void fed_out(void)
{
    struct khpm_ent *e = khpm_find(H, A, alive, 0); float to;
    if (!e) return;
    khpm_see(e, ob.max);
    if (khpm_plan(e, KHPM_FED, 1.0f, ob.max, &to)) { ob.cur = ob.cur * to / ob.max; ob.max = to; khpm_done(e, to); }
}

/* the code BEFORE the fix, both writers (klgrudge.c kly_health2 and klbotfill.c klbf_ot_health as they were) */
static float og_max0, og_wrote, ob_wrote;
static void old_grudge(float f)
{
    float wmax, wcur;
    if (ob.max < 1 || ob.max > 100000) return;
    if (og_max0 == 0) { og_max0 = ob.max; og_wrote = 0; }
    else if (fabsf(ob.max - og_max0) > 0.01f && (og_wrote == 0 || fabsf(ob.max - og_wrote) > 0.01f)) { og_max0 = ob.max; og_wrote = 0; }
    wmax = og_max0 * f;
    if (fabsf(ob.max - wmax) <= 0.01f) return;
    wcur = ob.cur * wmax / ob.max; ob.max = wmax; ob.cur = wcur; og_wrote = fabsf(wmax - og_max0) > 0.01f ? wmax : 0;
}
static void old_botfill(int mul)
{
    if (ob.max == ob_wrote) return;
    if (ob.max < 1 || ob.max > 100000) return;
    ob.cur *= (float)mul; ob.max *= (float)mul; ob_wrote = ob.max;
}

static void reset(float game_max)
{
    memset(khpm_t, 0, sizeof khpm_t); khpm_next = 0; g_ours = 0; og_max0 = og_wrote = ob_wrote = 0;
    ob.actor = A; game_gives(game_max);
}
#define NEAR(a, b) (fabsf((a) - (b)) < 0.5f)

int main(void)
{
    int i;

    /* the bug, old code: alternate ticks compound until both refuse > 100000 */
    reset(350);
    for (i = 0; i < 40; i++) { old_grudge(2.0f); old_botfill(5); }
    CHECK(ob.max > 3500.0f * 2, "OLD code model: the harness must see the compounding (max %.0f)", ob.max);
    CHECK(ob.max > 100000.0f / 10, "OLD code model ends high, like the bench's 350000 (max %.0f)", ob.max);

    /* new: both writers tick alternately many times: 350 x 2 x 5 = 3500, and stays (grudge first) */
    reset(350);
    for (i = 0; i < 200; i++) { grudge(2.0f); botfill(5); CHECK(ob.max < 3501.0f, "max %.0f must never pass 3500 (tick %d)", ob.max, i); }
    CHECK(NEAR(ob.max, 3500), "grudge first: settles at 3500 (%.0f)", ob.max);
    CHECK(NEAR(ob.cur, 3500), "health keeps its share (full stays full): %.0f", ob.cur);
    /* botfill first, the order of the bench's host */
    reset(350);
    for (i = 0; i < 200; i++) { botfill(5); grudge(2.0f); }
    CHECK(NEAR(ob.max, 3500), "botfill first: settles at 3500 (%.0f)", ob.max);
    /* many ticks of one writer only */
    for (i = 0; i < 50; i++) grudge(2.0f);
    for (i = 0; i < 50; i++) botfill(5);
    CHECK(NEAR(ob.max, 3500), "repeats of one writer change nothing (%.0f)", ob.max);

    /* a share is kept through the composition: half health stays half */
    reset(350); grudge(2.0f); ob.cur = ob.max / 2; botfill(5); grudge(2.0f);
    CHECK(NEAR(ob.max, 3500) && NEAR(ob.cur, 1750), "half health stays half: %.0f of %.0f", ob.cur, ob.max);

    /* the game writes a new maximum (the pooled actor respawns with 350 again, or a new number): re-based, composed again */
    reset(350);
    for (i = 0; i < 10; i++) { grudge(2.0f); botfill(5); }
    game_gives(350);
    grudge(2.0f); botfill(5); grudge(2.0f); botfill(5);
    CHECK(NEAR(ob.max, 3500), "respawn with the same 350: 3500 again (%.0f)", ob.max);
    game_gives(364);
    botfill(5); grudge(2.0f); botfill(5);
    CHECK(NEAR(ob.max, 3640), "the game gives 364: 364 x 2 x 5 = 3640 (%.0f)", ob.max);
    game_gives(500);
    grudge(2.0f); botfill(5);
    CHECK(NEAR(ob.max, 5000), "the game gives 500: 5000 (%.0f)", ob.max);

    /* review wou2kgqnw: the same pooled object next round with OnlineCrewHealth off - grudge's old factor must not stay in the product */
    reset(350);
    for (i = 0; i < 5; i++) { grudge(2.0f); botfill(5); }
    game_gives(350);
    for (i = 0; i < 5; i++) botfill(5);
    CHECK(NEAR(ob.max, 1750), "next round, grudge off: botfill alone 350 x 5 = 1750, no stale x2 (%.0f)", ob.max);
    game_gives(280); fed_in(3.0f);
    for (i = 0; i < 5; i++) botfill(5);
    CHECK(NEAR(ob.max, 4200), "new base 280: Fed x3 and botfill x5 = 4200 (%.0f)", ob.max);
    game_gives(280);
    for (i = 0; i < 5; i++) botfill(5);
    CHECK(NEAR(ob.max, 1400), "Fed gone with the respawn, botfill alone 1400 (%.0f)", ob.max);

    /* a down bot (health 0) when grudge first wants its factor: no write, and grudge tries again once he is up */
    reset(350); ob.cur = 0; grudge(2.0f);
    CHECK(NEAR(ob.max, 350) && g_ours == 0, "down: no write, hwrote stays 0 (%.0f, %.0f)", ob.max, g_ours);
    ob.cur = 350; grudge(2.0f);
    CHECK(NEAR(ob.max, 700) && g_ours != 0, "up again: x2 goes in (%.0f)", ob.max);

    /* one writer off (undo): the other's factor stays */
    reset(350);
    for (i = 0; i < 5; i++) { grudge(2.0f); botfill(5); }
    grudge_undo();
    CHECK(NEAR(ob.max, 1750), "grudge off: 350 x 5 = 1750 (%.0f)", ob.max);
    for (i = 0; i < 5; i++) { grudge(1.0f); botfill(5); }
    CHECK(NEAR(ob.max, 1750), "grudge off, botfill still ticking: stays 1750 (%.0f)", ob.max);
    grudge(2.0f); botfill(5);
    CHECK(NEAR(ob.max, 3500), "grudge back on: 3500 (%.0f)", ob.max);

    /* grudge alone: undo gives the game's own number back, the share kept */
    reset(350); grudge(2.0f); CHECK(NEAR(ob.max, 700), "grudge alone x2 (%.0f)", ob.max);
    ob.cur = 350; grudge_undo();
    CHECK(NEAR(ob.max, 350) && NEAR(ob.cur, 175), "undo alone: 350, health at the same share: %.0f of %.0f", ob.cur, ob.max);
    grudge(1.0f); botfill(1);
    CHECK(NEAR(ob.max, 350), "factors of 1 touch nothing (%.0f)", ob.max);

    /* undo when the game's own maximum has changed meanwhile: the game's number stays */
    reset(350); grudge(2.0f); game_gives(280); grudge_undo();
    CHECK(NEAR(ob.max, 280), "the game gave 280 after our write: undo leaves it (%.0f)", ob.max);

    /* a dead man's object is left alone */
    reset(350); grudge(2.0f); ob.cur = 0; botfill(5); grudge(3.0f);
    CHECK(NEAR(ob.max, 700), "down (health 0): no write (%.0f)", ob.max);

    /* FedHealth (Arcade, police) composes with CrewHealth and comes back alone */
    reset(280); grudge(2.0f); fed_in(3.0f); grudge(2.0f); fed_in(3.0f);
    CHECK(NEAR(ob.max, 1680), "280 x 2 x 3 = 1680 (%.0f)", ob.max);
    fed_out();
    CHECK(NEAR(ob.max, 560), "FedHealth out: CrewHealth stays (%.0f)", ob.max);
    grudge_undo();
    CHECK(NEAR(ob.max, 280), "all out: the game's 280 (%.0f)", ob.max);

    /* the table: another actor in the same object is a fresh entry; a full table reuses stale entries first */
    reset(350); grudge(2.0f);
    ob.actor = 0x1111u;
    CHECK(khpm_find(H, 0x1111u, alive, 0) == 0, "same object, other actor, no create: none");
    CHECK(khpm_find(H, 0x1111u, alive, 1) != 0 && khpm_find(H, 0x1111u, alive, 1)->base == 0, "reused object: reset entry");
    reset(350);
    for (i = 0; i < KHPM_N + 10; i++) CHECK(khpm_find(0x3000u + i, 0x5000u + i, alive, 1) != 0, "table never refuses a new object (%d)", i);

    printf("klhpmax_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
