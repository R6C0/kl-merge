/* klcamprappel_test.c - off-game checks of klcamprappel_logic.h. Build: cl /nologo /W3 klcamprappel_test.c */
#include <stdio.h>
#include "klcamprappel_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    unsigned short all[5] = { 1, 2, 3, 4, 5 }, none[5] = { 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF }, one[5] = { 1, 2, 0xFFFF, 4, 5 };
    float X[3] = { 0, 1000, 0 }, G[3] = { 0, 0, 0 }, w[3], a[3] = { 1, 0, 0 }, b[3] = { 0.99f, 0.14f, 0 }, c[3] = { 0, 0, 1 };
    CHECK(kcamr_mode_parse(0) == KCAMR_OFF);
    CHECK(kcamr_mode_parse("") == KCAMR_OFF);
    CHECK(kcamr_mode_parse("0") == KCAMR_OFF);
    CHECK(kcamr_mode_parse("1") == KCAMR_DRY);
    CHECK(kcamr_mode_parse("2") == KCAMR_NATIVE);
    CHECK(kcamr_mode_parse("3") == KCAMR_LIVE);
    CHECK(kcamr_mode_parse("4") == KCAMR_AUTO);
    CHECK(kcamr_mode_parse("5") == KCAMR_OFF);
    CHECK(kcamr_mode_parse("Native") == KCAMR_NATIVE);
    CHECK(kcamr_mode_parse("AUTO") == KCAMR_AUTO);
    CHECK(kcamr_mode_parse("dry") == KCAMR_DRY);
    CHECK(kcamr_mode_parse("live") == KCAMR_LIVE);
    CHECK(kcamr_mode_parse("natives") == KCAMR_OFF);
    CHECK(kcamr_mode_parse("nat") == KCAMR_OFF);
    CHECK(kcamr_clips_present(all) == 5 && kcamr_native_ok(all));
    CHECK(kcamr_clips_present(none) == 0 && !kcamr_native_ok(none));
    CHECK(kcamr_clips_present(one) == 4 && !kcamr_native_ok(one));
    CHECK(kcamr_decide(KCAMR_NATIVE, 1, 0) == 1);
    CHECK(kcamr_decide(KCAMR_NATIVE, 0, 0) == 0);          /* the refusal: no clips -> stock native never runs */
    CHECK(kcamr_decide(KCAMR_DRY, 1, 0) == 0);
    CHECK(kcamr_decide(KCAMR_OFF, 1, 0) == 0);
    CHECK(kcamr_decide(KCAMR_AUTO, 1, 1) == 0);
    CHECK(kcamr_decide(KCAMR_LIVE, 1, 0) == 1);
    CHECK(kcamr_segments(1000, 100, 2) == 5);
    CHECK(kcamr_segments(1000, 100, 3) == 4);
    CHECK(kcamr_segments(10, 100, 2) == 1);
    CHECK(kcamr_segments(0, 100, 2) == 1);
    CHECK(kcamr_segments(100000, 10, 0.5f) == 12);
    CHECK(kcamr_segments(300, 100, 0.0f) == 12 || kcamr_segments(300, 100, 0.0f) >= 1);
    kcamr_waypoint(X, G, 0, 4, w); CHECK(fabs(w[1] - 750) < 0.01);
    kcamr_waypoint(X, G, 3, 4, w); CHECK(fabs(w[1]) < 0.01);
    kcamr_waypoint(X, G, 0, 0, w); CHECK(fabs(w[1]) < 0.01);   /* n clamps to 1: lands on the ground */
    CHECK(kcamr_same_dir(a, a));
    CHECK(kcamr_same_dir(a, b));
    CHECK(!kcamr_same_dir(a, c));
    CHECK(kcamr_idle(0, 0) == 1);
    CHECK(kcamr_idle(1, 1) == 1);
    CHECK(kcamr_idle(1, 0) == 0);
    /* landing camera */
    CHECK(kcamr_land_parse(0) == KCAMR_L_OFF && kcamr_land_parse("") == KCAMR_L_OFF);
    CHECK(kcamr_land_parse("auto") == KCAMR_L_AUTO && kcamr_land_parse("AUTO") == KCAMR_L_AUTO && kcamr_land_parse("4") == KCAMR_L_AUTO);
    CHECK(kcamr_land_parse("turn") == KCAMR_L_TURN && kcamr_land_parse("cam") == KCAMR_L_CAM && kcamr_land_parse("turncam") == KCAMR_L_TURNCAM);
    CHECK(kcamr_land_parse("5") == KCAMR_L_OFF && kcamr_land_parse("camx") == KCAMR_L_OFF);
    CHECK(kcamr_land_resolve(KCAMR_L_AUTO, 1, 1) == KCAMR_L_TURNCAM);   /* wall ahead (M02) */
    CHECK(kcamr_land_resolve(KCAMR_L_AUTO, 1, 0) == KCAMR_L_CAM);       /* open (M09) */
    CHECK(kcamr_land_resolve(KCAMR_L_AUTO, 0, 1) == KCAMR_L_CAM);       /* ray unavailable: cam only, never a blind flip */
    CHECK(kcamr_land_resolve(KCAMR_L_TURN, 1, 1) == KCAMR_L_TURN);
    CHECK(kcamr_land_resolve(KCAMR_L_OFF, 1, 1) == KCAMR_L_OFF);
    CHECK(kcamr_landed(1, 0x10, 5, 1, 0) && !kcamr_landed(0, 0x10, 5, 1, 0));
    CHECK(!kcamr_landed(1, 0x10, 4, 1, 0) && !kcamr_landed(1, 0x10, 5, 0x10, 0) && !kcamr_landed(1, 0x10, 5, 1, 1) && !kcamr_landed(1, 3, 5, 1, 0));
    {
        int yi; float M[9];
        for (yi = 0; yi < 360; yi += 15) {
            kcamr_yaw_matrix((float)yi, M);
            CHECK(fabs(kcamr_yaw(M) - yi) < 0.05 || fabs(fabs(kcamr_yaw(M) - yi) - 360) < 0.05);
        }
        M[0] = 0; M[2] = 0; CHECK(kcamr_yaw(M) < 0);
    }
    CHECK(fabs(kcamr_land_yaw(100, KCAMR_L_TURN) - 280) < 1e-3 && fabs(kcamr_land_yaw(200, KCAMR_L_TURNCAM) - 20) < 1e-3);
    CHECK(fabs(kcamr_land_yaw(200, KCAMR_L_CAM) - 200) < 1e-3);
    CHECK(kcamr_land_cam(KCAMR_L_CAM) == 1 && kcamr_land_cam(KCAMR_L_TURNCAM) == 1 && kcamr_land_cam(KCAMR_L_TURN) == 0 && kcamr_land_cam(KCAMR_L_OFF) == 0);
    CHECK(kcamr_camtune_idle(1, 1) && !kcamr_camtune_idle(0, 1) && !kcamr_camtune_idle(1, 0));
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
