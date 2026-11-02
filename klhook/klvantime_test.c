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

    printf("klvantime_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
