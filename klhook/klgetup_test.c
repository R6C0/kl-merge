/* klgetup_test.c - off-game harness for klgetup_logic.h ([BotFill] OnlineGetUp pure decisions; klbotfill.c includes the same header).
   Proves the decisions, NOT that the game follows the order or that a replica's D state reads (re/bot_getup_online.md lists those as GUESS).
   Build (x86): cl /nologo /W3 klgetup_test.c /Fe:klgetup_test.exe     Run: klgetup_test.exe (exit 0 = all pass) */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klgetup_logic.h"
#include "kldown_hold.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    float d[4], out[3], hum[3] = { 1000, 50, 2000 }, bot[3] = { 1000, 50, 2800 }, m;
    struct kldh h; DWORD clk = 1000; int i, e, hold = 1;

    /* the down states */
    CHECK(!kgu_downed(0) && kgu_downed(1) && kgu_downed(2) && !kgu_downed(3) && !kgu_downed(7), "downed states");

    /* the pick: nearest within range, -1 when none / all ineligible / NaN */
    d[0] = -1; d[1] = 900; d[2] = 400; d[3] = 2600;
    CHECK(kgu_pick(d, 4, 2500) == 2, "nearest is 2, got %d", kgu_pick(d, 4, 2500));
    CHECK(kgu_pick(d, 4, 300) == -1, "none within 300");
    d[2] = (float)sqrt(-1.0);
    CHECK(kgu_pick(d, 4, 2500) == 1, "NaN skipped, got %d", kgu_pick(d, 4, 2500));
    CHECK(kgu_pick(d, 0, 2500) == -1, "empty");
    {   /* BP13: busy = walker-out / carrier */
        float e[3] = { 2700, 4000, 6000 }; int bz[3] = { 1, 0, 0 };
        CHECK(kgu_pick_b(e, bz, 3, 8000, 0, 0) == 0 && kgu_pick(e, 3, 8000) == 0, "both off: the nearest, as kgu_pick");
        CHECK(kgu_pick_b(e, bz, 3, 8000, 1500, 0) == 1, "busy cap 15 m: the busy 27 m bot is out, the nearest free one is");
        CHECK(kgu_pick_b(e, bz, 3, 8000, 0, 1) == 1, "free first: a farther free bot beats a nearer busy one");
        e[1] = 9000; e[2] = 9000;
        CHECK(kgu_pick_b(e, bz, 3, 8000, 0, 1) == 0 && kgu_pick_b(e, bz, 3, 8000, 1500, 1) == -1, "no free bot in range: the busy one unless capped");
        e[0] = 1200; CHECK(kgu_pick_b(e, bz, 3, 8000, 1500, 1) == 0, "busy within its cap still answers");
    }

    /* the place: 200 cm from him toward the bot, his height; a bot already inside goes to his feet */
    kgu_place(bot, hum, KGU_STOP_CM, out);
    CHECK(fabs(out[0] - 1000) < 0.01 && fabs(out[2] - 2200) < 0.01 && out[1] == 50, "place (%.1f %.1f %.1f)", out[0], out[1], out[2]);
    bot[2] = 2100; kgu_place(bot, hum, KGU_STOP_CM, out);
    CHECK(out[0] == 1000 && out[2] == 2000, "inside: feet");
    bot[0] = hum[0]; bot[2] = hum[2]; kgu_place(bot, hum, KGU_STOP_CM, out);
    CHECK(out[0] == 1000 && out[2] == 2000, "same spot: no divide by zero");

    /* the cadence */
    CHECK(kgu_due(5000, 0), "first order due");
    CHECK(!kgu_due(5000 + KGU_REORDER_MS - 1, 5000), "not before 2.5 s");
    CHECK(kgu_due(5000 + KGU_REORDER_MS, 5000), "at 2.5 s");
    CHECK(!kgu_due(100, 4294967000UL) && kgu_due(3000, 4294967000UL), "tick wrap (396 ms after the last order across the wrap: not due; 3296 ms: due)");

    /* OnlineGetUpKeepGoal: keep while closing, re-order when the target moved or the bot stalled for 3 s */
    CHECK(kgu_keep(5000, 4800, 0, 0) == 0, "closing 2 m: keep");
    CHECK(kgu_keep(5000, 4960, 0, 1000) == 0, "40 cm in a check, 1 s without progress: keep");
    CHECK(kgu_keep(5000, 4960, 0, 2999) == 0 && kgu_keep(5000, 4990, 0, 3000) == 2, "stalled exactly at 3 s: re-order");
    CHECK(kgu_keep(5000, 4950, 0, 9000) == 0, "50 cm shrink counts as progress even when the stall clock is old");
    CHECK(kgu_keep(5000, 4000, 199, 0) == 0 && kgu_keep(5000, 4000, 200, 0) == 1, "target moved 2 m: re-order though closing");
    CHECK(kgu_keep(-1, 4000, 0, 0) == 0 && kgu_keep(-1, 4000, 0, 3500) == 2, "no earlier check: only the stall clock decides");
    CHECK(kgu_keep(4000, 4300, 0, 3000) == 2, "moving away: stalled");

    /* OnlineGetUpDetour: a bot running a route (walked >= 3 m) is not stalled; one that arrived and left is re-ordered */
    CHECK(kgu_keep_d(4000, 4300, 0, 3500, 299, 5000, 0) == 2 && kgu_keep_d(4000, 4300, 0, 3500, 300, 5000, 0) == 0, "detour: walked 3 m = running, not stalled");
    CHECK(kgu_keep_d(4000, 4300, 0, 3500, 900, 20000, 0) == 2 && kgu_keep_d(4000, 4300, 0, 3500, 900, 19999, 0) == 0, "detour allowance ends 20 s after the order");
    CHECK(kgu_keep_d(300, 400, 0, 0, 0, 9000, 1) == 0 && kgu_keep_d(300, 500, 0, 0, 0, 9000, 1) == 2, "arrived then 5 m out: re-order at once");
    CHECK(kgu_keep_d(5000, 4000, 200, 0, 900, 1000, 0) == 1, "detour never hides a moved target");
    CHECK(kgu_keep_d(5000, 4400, 0, 9000, 0, 9000, 0) == 0 && kgu_keep_d(5000, 5000, 0, 3000, 0, 9000, 0) == 2, "no walk: as kgu_keep");
    CHECK(kgu_free(0, 0, 0) && kgu_free(1, 0, 0), "busy off: idle / stack walk with nothing carried are free");
    CHECK(!kgu_free(0, 150000, 0) && !kgu_free(2, 300000, 0), "busy off: a carrier or exit walker is not (BP11: 0 free bots)");
    CHECK(kgu_free(0, 150000, 1) && kgu_free(2, 300000, 1), "busy on: carriers and exit walkers answer (Arcade Rush)");
    CHECK(!kgu_free(3, 300000, 1) && !kgu_free(4, 0, 1), "busy on: aboard / taking a stack never");

    CHECK(kgu_floor(0.5f, 1, 3.0f) == 3.0f && kgu_floor(4.0f, 1, 3.0f) == 4.0f, "flop meter: raised to the floor, never lowered");
    CHECK(kgu_floor(0.5f, 0, 3.0f) == 0.5f && kgu_floor(0.5f, 1, 0) == 0.5f, "flop meter: no helper / floor off: unchanged");
    m = (float)sqrt(-1.0); CHECK(kgu_floor(m, 1, 3.0f) != kgu_floor(m, 1, 3.0f), "flop meter: NaN stays NaN");

    CHECK(kgu_at_goal(372, 30, 400) && !kgu_at_goal(372, 101, 400) && !kgu_at_goal(401, 0, 400) && !kgu_at_goal(372, -1, 400), "at its set goal (BP12: 3.7 m from the slid replica)");

    /* the helper test: 4 m, same floor (2 m) */
    CHECK(kgu_helper_ok(300, 10, 400, 200) && !kgu_helper_ok(401, 0, 400, 200) && !kgu_helper_ok(100, 250, 400, 200) && !kgu_helper_ok(-1, 0, 400, 200), "helper_ok");

    /* the meter */
    CHECK(kgu_boost(0, 1.0f / 60, 3.0f, 9) > 0.049f && kgu_boost(0, 1.0f / 60, 3.0f, 9) < 0.051f, "one frame of help");
    CHECK(kgu_boost(0, 5.0f, 3.0f, 9) == 0.75f, "a hitch is clamped to 0.25 s: %.3f", kgu_boost(0, 5.0f, 3.0f, 9));
    CHECK(kgu_boost(8.99f, 0.2f, 3.0f, 9) == 9.0f, "capped at the cap");
    CHECK(kgu_boost(12, 0.1f, 3.0f, 9) == 12, "a meter above the cap is not lowered");
    CHECK(kgu_boost(1, 0.1f, 0, 9) == 1 && kgu_boost(1, -1, 3, 9) == 1 && kgu_boost(-1, 0.1f, 3, 9) == -1, "no help, bad dt, bad meter: unchanged");
    m = (float)sqrt(-1.0); CHECK(kgu_boost(m, 0.1f, 3, 9) != kgu_boost(m, 0.1f, 3, 9), "NaN stays NaN (not written back by the caller: meter >= 0 fails)");

    /* with kldh_step (MashHold, need 8, decay 1.5, per 1): a man who never presses lies for ever alone, with a helper at 3 a second he is free after
       about need / (per_s - decay) seconds = 5.3 s; a man pressing 3 a second without help needs 8 / (3 - 1.5) = 5.3 s too, with help 8 / 4.5 = 1.8 s */
    memset(&h, 0, sizeof h);
    for (i = 0; i < 60 * 30 && hold; i++) {
        clk += 16;
        h.meter = kgu_boost(h.meter, 1.0f / 60, 3.0f, 9.0f);
        hold = kldh_step(&h, 1, 0, 1.0f / 60, 1.0f, 1.5f, 8.0f, clk, 0, 1, &e);
    }
    CHECK(!hold && i > 60 * 4 && i < 60 * 7, "helper alone frees him in %d frames (expected about 5.3 s = 320)", i);
    memset(&h, 0, sizeof h); hold = 1;
    for (i = 0; i < 60 * 30 && hold; i++) {      /* no helper, never pressing: held to the end of the test */
        clk += 16;
        hold = kldh_step(&h, 1, 0, 1.0f / 60, 1.0f, 1.5f, 8.0f, clk, 0, 1, &e);
    }
    CHECK(hold && i == 60 * 30, "no helper, no press: still held");

    CHECK(kgu_recede(1300, 1500, 1467, 5000) == 1 && kgu_recede(1300, 1499, 1467, 5000) == 0, "recede: grew exactly 2 m between checks");
    CHECK(kgu_recede(-1, 1668, 1467, 5000) == 1 && kgu_recede(-1, 1667, 1467, 5000) == 0, "recede: more than 2 m beyond the order distance");
    CHECK(kgu_recede(800, 870, 1467, 5000) == 0 && kgu_recede(870, 800, 1467, 5000) == 0, "recede: closing / sideways is not receding");
    CHECK(kgu_recede(800, 3410, 1467, 5000) == 1 && kgu_recede(3410, 3000, 1467, 5000) == 1, "recede: BP14 34 m from a 14.7 m order, even while it closes a little");
    CHECK(kgu_recede(100, 100, 0, 5000) == 0 && kgu_recede(-1, 5000, 0, 5000) == 0 && kgu_recede(100, -1, 1000, 5000) == 0, "recede: unknown order distance / bad input: no verdict");
    CHECK(kgu_recede(800, 3410, 1467, 2999) == 0 && kgu_recede(800, 3410, 1467, 3000) == 1, "recede: rate limit, no verdict before the order is 3 s old");
    CHECK(kgu_hold_near(360) && kgu_hold_near(400) && !kgu_hold_near(401) && !kgu_hold_near(-1), "hold: within 4 m (BP15 3.6 m)");
    CHECK(kgu_hold_due(5000, 0) && !kgu_hold_due(5899, 5000) && kgu_hold_due(5900, 5000) && kgu_hold_due(100, 4294967000UL) == 0, "hold: due at once, then every 900 ms");
    { float b2[3] = { 1000, 50, 2800 }; kgu_place(b2, hum, KGU_HOLD_STOP_CM, out); CHECK(fabs(out[2] - 2100) < 0.01, "hold place 1 m from him"); }

    /* OnlineGetUpPlateau (BP16b): the best-distance clock and the give-up verdict */
    { float best = -1; DWORD at = 0, t = 100000;
      CHECK(kgu_best(&best, 1470) == 1 && best == 1470, "best: the first reading stamps");
      at = t;
      CHECK(kgu_best(&best, 1400) == 0 && best == 1470, "best: 0.7 m is not a metre yet (best kept)");
      CHECK(kgu_best(&best, 1369) == 1 && best == 1369, "best: 1.01 m since the stamp, added up over two checks");
      CHECK(kgu_best(&best, 1500) == 0 && best == 1369, "best: farther out does not move it");
      CHECK(kgu_best(&best, -1) == 0 && kgu_best(&best, (float)sqrt(-1.0)) == 0 && best == 1369, "best: bad / NaN input ignored");
      CHECK(!kgu_plateau(1369, 4999, KGU_HOLD_STOP_CM) && kgu_plateau(1369, 5000, KGU_HOLD_STOP_CM), "plateau: 13.7 m out, no metre gained for 5 s (BP16b 9 - 14.7 m for 18 s)");
      CHECK(!kgu_plateau(600, 9000, KGU_HOLD_STOP_CM) && kgu_plateau(601, 9000, KGU_HOLD_STOP_CM), "plateau: only beyond stop + 5 m (1 m stop: 6 m)");
      CHECK(!kgu_plateau(700, 9000, KGU_STOP_CM) && kgu_plateau(701, 9000, KGU_STOP_CM), "plateau: 2 m stop: 7 m");
      CHECK(!kgu_plateau(-1, 9000, KGU_STOP_CM) && !kgu_plateau((float)sqrt(-1.0), 9000, KGU_STOP_CM), "plateau: no best yet / NaN: no verdict");
      CHECK(!kgu_plateau_out(5000, 0) && kgu_plateau_out(14999, 5000) && !kgu_plateau_out(15000, 5000), "plateau: out of the pick for 10 s, 0 = never plateaued");
      CHECK(kgu_plateau_out(100, 4294967000UL), "plateau: out survives the tick wrap");
      (void)at; }

    /* Recede with the walk excuse (BP16b): a moving bot a few metres beyond its order distance is routing; BP14's runaway is still caught */
    CHECK(kgu_recede(900, 1470, 900, 5000) == 1 && kgu_recede_w(900, 1470, 900, 5000, 350) == 0, "recede_w: 9 -> 14.7 m while moving 3.5 m = a route, not a retreat");
    CHECK(kgu_recede_w(900, 1470, 900, 5000, 299) == 1 && kgu_recede_w(900, 1470, 900, 5000, 0) == 1, "recede_w: standing still (walked < 3 m) = kgu_recede");
    CHECK(kgu_recede_w(1470, 2270, 1470, 5000, 900) == 0 && kgu_recede_w(2270, 2271, 1470, 5000, 900) == 1, "recede_w: the excuse ends 8 m beyond the order distance (BP14 14.7 -> 34 m is caught at 22.7)");
    CHECK(kgu_recede_w(-1, 3410, 0, 5000, 900) == 0 && kgu_recede_w(800, 3410, 1467, 5000, 900) == 1, "recede_w: no order distance = no excuse, and no verdict without an earlier check (as kgu_recede); 34 m is caught");
    CHECK(kgu_recede_w(800, 1100, 900, 2999, 0) == 0, "recede_w: the 3 s rate limit stands");
    printf("klgetup_test: %d check(s), %d failure(s)\n", checks, fails);
    printf(fails ? "FAIL\n" : "ALL PASS\n");
    return fails ? 1 : 0;
}
