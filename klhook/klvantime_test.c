/* klvantime_test.c - off-game harness for klvantime_logic.h ([BotFill] OnlineVanAfterLegs / OnlineVanBoPos / OnlineVanFarHold pure decisions; klbotfill.c includes the same header).
   Proves the decisions, NOT that bots walk or board (re/dm09_van_timing_1101.md). No windows.h.
   Build: cl /nologo /W3 klvantime_test.c /Fe:klvantime_test.exe     Run: klvantime_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klvantime_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    /* DM09 numbers from the RT2L log */
    float stale[3] = { 24235, -59842, 13883 }, bo2[3] = { -1852, 121, 8675 }, bo4[3] = { -1852, 121, 10459 }, org[3] = { 0, 0, 0 };
    float trig[1][3] = { { -3000, 500, 10550 } };
    float d[4] = { 7000, 1500, 300, 9000 }; int car[4] = { 1, 1, 1, 0 };

    /* OnlineVanAfterLegs */
    CHECK(kvt_van_for_walk(0, 1, 1) == 1 && kvt_van_for_walk(0, 0, 1) == 1 && kvt_van_for_walk(0, 1, 0) == 0, "key 0 = today (a known van stays)");
    CHECK(kvt_van_for_walk(1, 1, 1) == 0, "key 1 + trigger known: the van object is ignored for the walk");
    CHECK(kvt_van_for_walk(1, 0, 1) == 1, "key 1 but no trigger yet: the van stays (old behaviour)");
    CHECK(kvt_van_for_walk(1, 0, 0) == 0 && kvt_van_for_walk(1, 1, 0) == 0, "no van, no change");
    CHECK(kvt_lookup_ok(0, 1) == 0 && kvt_lookup_ok(0, 0) == 1, "key 0: lookup only without a van (today)");
    CHECK(kvt_lookup_ok(1, 1) == 1 && kvt_lookup_ok(1, 0) == 1, "key 1: lookup also with a van");

    /* OnlineVanBoPos */
    CHECK(kvt_bo_ok(0, 2, bo2, 1, (const float (*)[3])trig) == 0, "key 0 never");
    CHECK(kvt_bo_ok(1, 0, bo2, 1, (const float (*)[3])trig) == 0, "state 0: no boarding object yet");
    CHECK(kvt_bo_ok(1, 1, bo2, 1, (const float (*)[3])trig) == 0 && kvt_bo_ok(1, 2, bo2, 1, (const float (*)[3])trig) == 0, "states 1 / 2: the vehicle drives in, its place moves: no goal");
    CHECK(kvt_bo_ok(1, 3, bo4, 1, (const float (*)[3])trig) == 1, "state 3 (DD): parked, ok");
    CHECK(kvt_bo_ok(1, 4, bo4, 1, (const float (*)[3])trig) == 1, "DM09 state 4: ok");
    CHECK(kvt_bo_ok(1, 5, bo4, 1, (const float (*)[3])trig) == 0 && kvt_bo_ok(1, 7, bo4, 1, (const float (*)[3])trig) == 0, "leaving / gone: no");
    CHECK(kvt_bo_ok(1, 4, stale, 1, (const float (*)[3])trig) == 0 && kvt_bo_ok(1, 4, stale, 0, 0) == 0, "the stale van place is refused with and without refs");
    CHECK(kvt_bo_ok(1, 4, org, 0, 0) == 0, "origin = unplaced");
    CHECK(kvt_bo_ok(1, 4, bo2, 0, 0) == 1, "no refs known: only the absolute test");
    { float far_[3] = { -39000, 100, -39000 }; CHECK(kvt_bo_ok(1, 4, far_, 1, (const float (*)[3])trig) == 0, "within 400 m abs but 500 m+ from the trigger: refused"); }
    { float nan_[3] = { 1, 1, 1 }; nan_[0] = (float)sqrt(-1.0); CHECK(kvt_bo_ok(1, 4, nan_, 0, 0) == 0, "NaN refused"); }
    CHECK(kvt_use_bo(1, 0, 0, 8, 8) == 1, "legs done: boarding object");
    CHECK(kvt_use_bo(1, 0, 0, 3, 8) == 0, "still on the legs and not called: legs first");
    CHECK(kvt_use_bo(1, 0, 1, 3, 8) == 1, "called: boarding object even mid-route");
    CHECK(kvt_use_bo(1, 1, 1, 8, 8) == 0, "an escape box wins (DD maps unchanged)");
    CHECK(kvt_use_bo(0, 0, 1, 8, 8) == 0, "not ok: no");
    CHECK(kvt_use_bo(1, 0, 0, 0, 0) == 1, "no route configured: boarding object");

    /* OnlineVanFarHold */
    CHECK(kvt_hold_state_ok(0, 3) == 1 && kvt_hold_state_ok(0, 4) == 0 && kvt_hold_state_ok(1, 4) == 1 && kvt_hold_state_ok(1, 2) == 0 && kvt_hold_state_ok(1, 5) == 0, "hold states");
    CHECK(kvt_eff_dmin(0, 1e30f, 2, 1800.0f) == 1e30f, "key 0: dmin untouched");
    CHECK(kvt_eff_dmin(1, 1e30f, 0, 1800.0f) == 1e30f, "no far walker: untouched");
    CHECK(kvt_eff_dmin(1, 1e30f, 2, 1800.0f) == 1800.0f, "far walker, nobody near: dmin = nearM");
    CHECK(kvt_eff_dmin(1, 900.0f, 2, 1800.0f) == 900.0f, "a nearer walker keeps its own distance");
    CHECK(kvt_eff_dmin(1, 2500.0f, 1, 1800.0f) == 1800.0f, "nearest 25 m but a far one: nearM");
    CHECK(kvt_cap_s(0, 1, 15, 40) == 15 && kvt_cap_s(1, 0, 15, 40) == 15 && kvt_cap_s(1, 1, 15, 40) == 40 && kvt_cap_s(1, 1, 60, 40) == 60, "cap");
    CHECK(kvt_count_far(d, car, 4, 3000.0f) == 1, "only the carrier farther than 30 m: got %d", kvt_count_far(d, car, 4, 3000.0f));
    CHECK(kvt_count_far(d, car, 4, 10000.0f) == 0 && kvt_count_far(d, car, 0, 3000.0f) == 0, "none");

    /* OnlineVanMoverProbe: kcw_counts */
    { float nan_ = (float)sqrt(-1.0), inf_ = (float)HUGE_VAL;
      CHECK(kcw_counts(0, 0, 0, 3000, 10000) == 0, "a standing bot does not count");
      CHECK(kcw_counts(300, 0, 0, 3000, 10000) == 1, "3 m in 2 s inside 100 m counts");
      CHECK(kcw_counts(0, 0, 300, 20000, 10000) == 0, "a mover outside 100 m does not count");
      CHECK(kcw_counts(200, 0, 0, 3000, 10000) == 1 && kcw_counts(199, 0, 0, 3000, 10000) == 0, "exactly 200 cm counts, 199 does not");
      CHECK(kcw_counts(0, 120, 160, 3000, 10000) == 1, "3D displacement (120,160 = 200)");
      CHECK(kcw_counts(300, 0, 0, 10000, 10000) == 1 && kcw_counts(300, 0, 0, 10001, 10000) == 0, "the range edge is inside");
      CHECK(kcw_counts(nan_, 0, 0, 3000, 10000) == 0 && kcw_counts(300, inf_, 0, 3000, 10000) == 0 && kcw_counts(300, 0, 0, nan_, 10000) == 0 && kcw_counts(300, 0, 0, 3000, inf_) == 0 && kcw_counts(300, 0, 0, 3000, nan_) == 0, "NaN / inf: no");
    }

    /* OnlineVanCrewHold: kcw_add / kcw_reason / kcw_shield_cap_ms / kcw_latch / kcw_moved */
    { float nan_ = (float)sqrt(-1.0), inf_ = (float)HUGE_VAL; int r, tick; float tm, used, dwell, added;
      CHECK(kcw_add(1.8f, 2.0f, 45, 0, 60, 3) == 45.0f, "Arcade log 1.8 -> 46.8: adds 45");
      CHECK(kcw_add(1.8f, 2.0f, 45, 0, 5, 3) == 5.0f, "step 5");
      CHECK(kcw_add(1.8f, 2.0f, 45, 40, 60, 3) == 5.0f && kcw_add(1.8f, 2.0f, 45, 44.5f, 60, 3) == 0.5f, "budget left caps the add");
      CHECK(kcw_add(1.8f, 2.0f, 45, 44.6f, 60, 3) == 0, "under 0.5 s left = used");
      CHECK(kcw_add(2.0f, 2.0f, 45, 0, 60, 3) == 0 && kcw_add(0, 2.0f, 45, 0, 60, 3) == 0 && kcw_add(-1, 2.0f, 45, 0, 60, 3) == 0 && kcw_add(nan_, 2.0f, 45, 0, 60, 3) == 0 && kcw_add(inf_, 2.0f, 45, 0, 60, 3) == 0, "window is (0, 2.0)");
      CHECK(kcw_add(1.8f, 2.0f, 45, 0, 60, 0) == 0, "no walker, no add");
      CHECK(kcw_add(1.8f, 2.0f, 0, 0, 60, 3) == 0 && kcw_add(1.8f, 2.0f, nan_, 0, 60, 3) == 0 && kcw_add(1.8f, 2.0f, 45, -1, 60, 3) == 0 && kcw_add(1.8f, 2.0f, 45, 0, 0, 3) == 0 && kcw_add(1.8f, 2.0f, 45, 0, nan_, 3) == 0, "budget 0 inert; NaN / negative / step 0: no");
      CHECK(kcw_reason(1, 0, 3, 0, 45) == 1 && kcw_reason(0, 1, 3, 0, 45) == 2 && kcw_reason(1, 1, 3, 0, 45) == 3, "reason bits");
      CHECK(kcw_reason(0, 1, 0, 0, 45) == 0 && kcw_reason(1, 1, 0, 0, 45) == 1, "crew on, no walker: legacy bit only");
      CHECK(kcw_reason(1, 1, 3, 44.8f, 45) == 1 && kcw_reason(0, 1, 3, 44.8f, 45) == 0, "budget used: crew bit gone");
      CHECK(kcw_reason(1, 0, 3, 0, 45) == 1 && kcw_reason(0, 0, 3, 0, 45) == 0, "crew off: never bit 2");
      CHECK(kcw_shield_cap_ms(45, 2) == 55000u && kcw_shield_cap_ms(0, 2) == 10000u && kcw_shield_cap_ms(30, 2) < kcw_shield_cap_ms(45, 2), "shield cap");
      CHECK(kcw_latch(0, 1, 0) == 0 && kcw_latch(0, 0, 1) == 1 && kcw_latch(1, 0, 1) == 0 && kcw_latch(1, 1, 0) == 1, "latch");
      CHECK(kcw_moved(199, 0, 0) == 0 && kcw_moved(200, 0, 0) == 1 && kcw_moved(0, 120, 160) == 1 && kcw_moved(nan_, 0, 0) == 0, "moved");
      /* sequence: timer falls 8 -> window, 1 s ticks, 3 walkers, budget 45, legacy near walker present too (verifier fix 1) */
      tm = 8.0f; used = 0; added = 0; dwell = 0;
      for (tick = 0; tick < 200 && tm > 0; tick++) {
          float a;
          r = kcw_reason(tick < 15, 1, 3, used, 45);      /* legacy reason ends at the 15 s OnlineHoldMaxS cap */
          if (r && kcw_floor_ok(r)) {      /* r == 0: vh_pass returns before any write */ if (tm < 3.0f) tm = 3.0f; }      /* legacy floor, only without the crew reason */
          a = (r & 2) ? kcw_add(tm, 2.0f, 45, used, 60, 3) : 0;
          if (a > 0) { tm += a; used += a; added += a; }
          tm -= 1.0f; dwell += 1.0f;
      }
      CHECK(added == 45.0f, "legacy near walker + crew walker: the 45 s are added (got %.1f)", added);
      CHECK(dwell >= 50.0f && dwell <= 56.0f, "dwell about 8 + 45 s (got %.0f)", dwell);
      /* the old floor alone would have kept tm >= 2 forever: prove the bug the fix avoids */
      tm = 8.0f; added = 0;
      for (tick = 0; tick < 30; tick++) { if (tm < 3.0f) tm = 3.0f; added += kcw_add(tm, 2.0f, 45, 0, 60, 3); tm -= 1.0f; }
      CHECK(added == 0, "with the floor always on the window never opens");
      CHECK(kcw_floor_ok(3) == 0 && kcw_floor_ok(2) == 0 && kcw_floor_ok(1) == 1 && kcw_floor_ok(0) == 1, "floor only without bit 2");
    }

    {   /* OnlineVanCallFirst */
        float nanv = (float)sqrt(-1.0);
        CHECK(kvt_cf_active(0, 1) == 0 && kvt_cf_active(1, 0) == 0 && kvt_cf_active(0, 0) == 0 && kvt_cf_active(1, 1) == 1, "callfirst needs both keys");
        CHECK(kvt_cf_clamp(45, 1.8f, 200, 10) == 45.0f, "plenty of clock: the whole add");
        CHECK(kvt_cf_clamp(45, 1.8f, 43, 10) == 0.0f, "DD07/DD03 low clock (43 s left): no add");
        CHECK(kvt_cf_clamp(45, 1.8f, 100, 10) > 27.9f && kvt_cf_clamp(45, 1.8f, 100, 10) < 28.3f, "100 s left: add capped to ~28.2 s");
        CHECK(kvt_cf_clamp(45, 1.8f, 71.8f, 10) == 0.0f && kvt_cf_clamp(45, 1.8f, 72.0f, 10) == 0.0f && kvt_cf_clamp(45, 1.8f, 72.5f, 10) > 0.4f, "under 0.5 s of room = none");
        CHECK(kvt_cf_clamp(5, 1.8f, 100, 10) == 5.0f, "a small add that fits stays");
        CHECK(kvt_cf_clamp(0, 1.8f, 200, 10) == 0.0f && kvt_cf_clamp(-3, 1.8f, 200, 10) == 0.0f, "no add in = none");
        CHECK(kvt_cf_clamp(nanv, 1.8f, 200, 10) == 0.0f && kvt_cf_clamp(45, nanv, 200, 10) == 0.0f && kvt_cf_clamp(45, 1.8f, nanv, 10) == 0.0f && kvt_cf_clamp(45, 1.8f, 200, nanv) == 0.0f, "NaN = none");
        CHECK(kvt_cf_clamp(45, 1.8f, 0, 10) == 0.0f && kvt_cf_clamp(45, 1.8f, -5, 10) == 0.0f, "no clock = none");
        CHECK(kvt_cf_clamp(45, 1.8f, 200, 0) == 45.0f && kvt_cf_clamp(45, 1.8f, 110, 0) > 47.9f - 46.0f, "margin 0");
        CHECK(kvt_cf_carrier_ok(1310000) == 1 && kvt_cf_carrier_ok(1) == 1 && kvt_cf_carrier_ok(0) == 0 && kvt_cf_carrier_ok(-5) == 0, "only a bot with tally > 0 calls early");
    }
    {   /* OnlineVanCrewNoShield */
        CHECK(kvt_cw_noshield_ok(1, 0, 1, 0) == 1, "key on, unreadable van, shield wanted: timer-only add");
        CHECK(kvt_cw_noshield_ok(0, 0, 1, 0) == 0, "key off: refused as today");
        CHECK(kvt_cw_noshield_ok(1, 0, 1, 1) == 0, "readable van whose shield failed: still refused");
        CHECK(kvt_cw_noshield_ok(1, 1, 1, 0) == 0 && kvt_cw_noshield_ok(1, 0, 0, 0) == 0, "shield ok / not wanted: no special case");
        CHECK(kvt_cw_refused_shield(0, 1) == 1 && kvt_cw_refused_shield(2, 1) == 0 && kvt_cw_refused_shield(0, 0) == 0, "summary label refused (no shield)");
    }

    printf("klvantime_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
