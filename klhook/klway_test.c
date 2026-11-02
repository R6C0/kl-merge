/* klway_test.c - off-game harness for klway_logic.h ([BotFill] OnlineWayPerMap / OnlineLegHopDy pure decisions; klbotfill.c includes the same header).
   Proves the decisions, NOT that bots walk or are carried (re/open_work_log.md wk-rtroute-1101).
   Build (x86): cl /nologo /W3 klway_test.c /Fe:klway_test.exe     Run: klway_test.exe (exit 0 = all pass) */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klway_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    /* DM09 example route: P1 lift floor (tower), P2.. street */
    float pts[4][3] = { { 2560, 19601, 740 }, { 2600, 114, -5920 }, { 440, -52, -5000 }, { -1840, -47, -3360 } };
    float ex[3] = { -3000, 500, 10550 }, tower[3] = { 477, 19600, -81 }, street[3] = { 6272, 563, -6305 }, past[3] = { -2800, -40, 9000 };

    CHECK(kwy_use_slot(0, 1, 5) == 1 && kwy_use_slot(0, 0, 0) == 1, "mode 0 = slot only");
    CHECK(kwy_use_slot(1, 1, 3) == 0, "mode 1, per-map present");
    CHECK(kwy_use_slot(1, 1, 0) == 1 && kwy_use_slot(1, 0, 0) == 1, "mode 1 falls back to the slot");
    CHECK(kwy_use_slot(2, 1, 0) == 0, "mode 2, redirected map without a section: no slot route");
    CHECK(kwy_use_slot(2, 0, 0) == 1 && kwy_use_slot(2, 0, 4) == 0, "mode 2, stock map");
    CHECK(kwy_use_slot(9, 1, 0) == 1, "bad mode = today");

    /* old behaviour (hopdy 0): from the tower the first leg ahead is leg 0; from the street legs 0.. are skipped only by distance */
    { float far_[3] = { 2430, 19600, 510 }; far_[0] = -3000 + 12400.0f; far_[2] = 10550;      /* 12.4 km from the exit, as the Q34 bots */
      CHECK(kwy_start(far_, ex, pts, 4, 0, 300) == 0, "12.4 km bot: leg 0 (today)"); }
    CHECK(kwy_start(tower, ex, pts, 4, 0, 300) == 4, "today a bot in the hall (11.2 km) skips the lift leg (no nearer): got %d", kwy_start(tower, ex, pts, 4, 0, 300));
    /* hopdy 1500: tower bot still leg 0; street bot skips the lift leg by height */
    CHECK(kwy_start(tower, ex, pts, 4, 1500, 300) == 0, "tower bot keeps the lift leg with hopdy, got %d", kwy_start(tower, ex, pts, 4, 1500, 300));
    CHECK(kwy_start(street, ex, pts, 4, 1500, 300) == 1, "street bot starts at leg 1, got %d", kwy_start(street, ex, pts, 4, 1500, 300));
    CHECK(kwy_start(past, ex, pts, 4, 1500, 300) == 4, "past every leg");
    /* a bot on neither floor's height has no leg */
    { float mid[3] = { 0, 9000, 0 }; CHECK(kwy_start(mid, ex, pts, 4, 1500, 300) == 4, "no leg at a height nobody has"); }

    CHECK(!kwy_hold(19600, 114, 0, 1000, KWY_HOLD_MS), "hopdy 0 never holds");
    CHECK(kwy_hold(19600, 114, 1500, 20000, KWY_HOLD_MS), "tower bot holds for the carry");
    CHECK(!kwy_hold(570, 114, 1500, 20000, KWY_HOLD_MS), "carried: next leg is on its floor");
    CHECK(kwy_carried(2, 570, 19600, 114, 1500), "held then carried: leg counts as reached");
    CHECK(!kwy_carried(0, 570, 19600, 114, 1500), "never held: no early hit");
    CHECK(!kwy_carried(2, 19600, 19600, 114, 1500), "still on the tower floor: no hit");
    CHECK(!kwy_carried(2, 570, 19600, 114, 0), "hopdy 0: off");
    CHECK(!kwy_hold(19600, 114, 1500, KWY_HOLD_MS, KWY_HOLD_MS), "hold cap reached");
    CHECK(!kwy_hold(19600, 19601, 1500, 100, KWY_HOLD_MS), "same floor next leg");

    /* wk-rt2-1101 */
    CHECK(!kwy_legs_left(0, 1, 0, 0, 0, 8, 0) && kwy_legs_left(1, 1, 0, 0, 0, 8, 0), "van known: legs only with OnlineLegsWithVan (no trigger needed)");
    CHECK(!kwy_legs_left(1, 1, 1, 0, 0, 8, 0) && !kwy_legs_left(1, 1, 0, 0, 1, 8, 0) && !kwy_legs_left(1, 1, 0, 0, 0, 8, 8) && !kwy_legs_left(1, 1, 0, 0, 0, 0, 0), "box / called / done / no legs: no legs");
    CHECK(kwy_legs_left(0, 0, 0, 1, 0, 5, 2) && !kwy_legs_left(0, 0, 0, 0, 0, 5, 2) && kwy_legs_left(1, 0, 0, 1, 0, 5, 2) && !kwy_legs_left(1, 0, 0, 0, 0, 5, 2), "no van: needs the trigger as before");
    { float tp[3] = { 1, 2, 3 }, vp[3] = { 4, 5, 6 };
      CHECK(kwy_exit(1, 1, 0, tp, vp) == vp && kwy_exit(0, 1, 0, tp, vp) == tp && kwy_exit(1, 1, 1, tp, vp) == tp && kwy_exit(1, 0, 0, tp, vp) == tp, "exit point: van only when withVan, van and no trigger"); }
    CHECK(!kwy_class_ok(0, 0xbb0000, 0xbb3bac, 0xbb3bac) && kwy_class_ok(0, 0xbb3bac, 0, 0xbb3bac) && kwy_class_ok(1, 0xbb0000, 0xbb3bac, 0xbb3bac) && !kwy_class_ok(1, 0xbb3bac, 0x1234, 0xbb3bac), "priv vtable: class ok only through avt when on");
    CHECK(ksp_changed(-9, -9, -9, 5, 1, 1), "first read is a line");
    CHECK(!ksp_changed(1000, 1, 1, 1000, 1, 1) && ksp_changed(1000, 1, 1, 0, 1, 1) && ksp_changed(1000, 1, 1, 1000, 2, 1) && ksp_changed(1000, 1, 1, 1000, 1, 0), "poll: a line only on a change");
    CHECK(ksp_changed(1000, 1, 1, -1, -1, -1), "poll: unreadable is a change");
    CHECK(!kdf_drop_ok(1, 1) && !kdf_drop_ok(0, 0) && !kdf_drop_ok(-1, 1) && kdf_drop_ok(0, 1), "dropfollow: hidden or undrained pool drop is skipped");

    {   /* wk-rt9-1102 OnlineLateExitRoute */
        float rp[3][3] = { { 0, 0, 0 }, { 3000, 0, 0 }, { 3000, 0, 4000 } }, o[3] = { 0, 0, 0 }, ex2[3] = { 3000, 0, 5000 };
        CHECK(fabs(kwy_route_cm(o, rp, 3, 0, ex2) - 8000) < 1, "route: all legs then exit");
        CHECK(fabs(kwy_route_cm(o, rp, 3, 2, ex2) - 6000) < 1, "route: from leg 2");
        CHECK(fabs(kwy_route_cm(o, rp, 0, 0, ex2) - 5831) < 2, "route: no legs = straight");
        CHECK(kwy_late_s(0, 75, 31000, 130, 20) == 75, "route off = base");
        CHECK(kwy_late_s(1, 0, 31000, 130, 20) == 0, "base 0 stays off");
        CHECK(kwy_late_s(1, 75, 31000, 130, 20) == 258, "DM09 310 m: 258 s");
        CHECK(kwy_late_s(1, 75, 1000, 130, 20) == 75, "short route: never below base");
        CHECK(kwy_late_s(1, 75, 900000, 130, 20) == 400, "clamped to 400");
        CHECK(kwy_late_s(1, 75, 31000, 0, 20) == 75 && kwy_late_s(1, 75, -1, 130, 20) == 75, "bad pace or length = base");
    }
    printf("klway_test: %d checks, %d failed\n", checks, fails);
    return fails != 0;
}
