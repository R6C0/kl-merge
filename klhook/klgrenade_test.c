/* klgrenade_test.c - off-game checks of klgrenade_logic.h. Build: cl /nologo /W3 klgrenade_test.c */
#include <stdio.h>
#include "klgrenade_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
static int near_(float a, float b, float e) { return fabsf(a - b) <= e; }
int main(void)
{
    struct klgr_cfg c = { 2000.0f, 1000.0f, 1500.0f, 150.0f, 70.0f }; struct klgr_plan p;
    volatile float zero = 0.0f; float feet[3] = { 0, 0, 0 }, aim[3] = { 1000, 0, 0 }, nan = zero / zero;
    float bad[3];
    /* straight throw 10 m along +x */
    CHECK(klgr_plan_throw(feet, aim, &c, &p));
    CHECK(near_(p.rel[0], 70.0f, 0.01f) && near_(p.rel[1], 150.0f, 0.01f) && near_(p.rel[2], 0.0f, 0.01f));
    CHECK(p.v[0] > 0 && near_(p.v[2], 0.0f, 0.01f));
    CHECK(near_(p.t, p.dist / 1000.0f, 0.001f));
    CHECK(p.v[1] > 0);                                    /* lobbed: gravity term lifts it */
    {   /* the ballistic arc lands on the target height: y(t) = rel_y + vy*t - 0.5*g*t^2 == aim_y (no clamp in this case) */
        float y = p.rel[1] + p.v[1] * p.t - 0.5f * KLGR_GRAVITY * p.t * p.t;
        CHECK(near_(y, aim[1], 0.5f));
    }
    /* range clamp: a target 50 m away is thrown at 20 m */
    aim[0] = 5000;
    CHECK(klgr_plan_throw(feet, aim, &c, &p));
    CHECK(near_(p.dist, 2000.0f, 0.01f));
    /* speed cap */
    CHECK(sqrtf(p.v[0] * p.v[0] + p.v[1] * p.v[1] + p.v[2] * p.v[2]) <= c.vmax + 0.01f);
    /* too close horizontally (< 50 cm) refused; just beyond is accepted and thrown 3 m ahead (L < 100 rule) */
    aim[0] = 40; CHECK(!klgr_plan_throw(feet, aim, &c, &p));
    aim[0] = 60; aim[1] = 150;
    CHECK(klgr_plan_throw(feet, aim, &c, &p));
    CHECK(near_(p.dist, 300.0f, 0.01f) || p.dist >= 100.0f);
    /* z direction and negative direction */
    aim[0] = 0; aim[1] = 0; aim[2] = -800;
    CHECK(klgr_plan_throw(feet, aim, &c, &p));
    CHECK(near_(p.rel[2], -70.0f, 0.01f) && p.v[2] < 0 && near_(p.v[0], 0.0f, 0.01f));
    /* non-finite and huge refused */
    bad[0] = nan; bad[1] = 0; bad[2] = 0; CHECK(!klgr_plan_throw(feet, bad, &c, &p)); CHECK(!klgr_plan_throw(bad, aim, &c, &p));
    bad[0] = 2e9f; CHECK(!klgr_plan_throw(feet, bad, &c, &p));
    bad[0] = 200000.0f; CHECK(!klgr_plan_throw(feet, bad, &c, &p));      /* > 1 km horizontally */
    /* minimum flight time 0.25 s */
    aim[0] = 150; aim[1] = 150; aim[2] = 0; CHECK(klgr_plan_throw(feet, aim, &c, &p)); CHECK(p.t >= 0.25f);
    /* config clamps */
    { struct klgr_cfg w = { -5, 99999, 0, nan, 9999 }; klgr_cfg_clamp(&w);
      CHECK(w.range == 300.0f && w.speed == 3000.0f && w.vmax == 300.0f && w.up == 0.0f && w.fwd == 200.0f); }
    /* ammo */
    { int c1, r1, e;
      e = klgr_consume(2, 3, 1, &c1, &r1); CHECK(c1 == 1 && r1 == 3 && !e);
      e = klgr_consume(1, 3, 1, &c1, &r1); CHECK(c1 == 1 && r1 == 2 && !e);          /* clip emptied, refilled from reserve */
      e = klgr_consume(1, 3, 0, &c1, &r1); CHECK(c1 == 0 && r1 == 3 && !e);          /* no refill */
      e = klgr_consume(1, 0, 1, &c1, &r1); CHECK(c1 == 0 && r1 == 0 && e);
      e = klgr_consume(0, 2, 1, &c1, &r1); CHECK(c1 == 1 && r1 == 0 && !e);
      e = klgr_consume(1, -1, 1, &c1, &r1); CHECK(c1 == 0 && r1 == 0 && e); }
    CHECK(klgr_unxor(0xbeebbeebul ^ 5ul) == 5); CHECK(klgr_unxor(0xbeebbeebul) == 0);
    /* launch proof */
    CHECK(klgr_launched(3, 4, 1, 0, 1, 8)); CHECK(!klgr_launched(3, 3, 1, 0, 1, 8)); CHECK(!klgr_launched(3, 4, 0, 0, 1, 8));
    CHECK(!klgr_launched(3, 4, 1, 2, 2, 8)); CHECK(!klgr_launched(3, 4, 1, 0, 1, 0));
    /* cooldown, wrap safe */
    CHECK(klgr_cool_over(0, 5, 1000)); CHECK(!klgr_cool_over(1000, 1500, 1000)); CHECK(klgr_cool_over(1000, 2000, 1000));
    CHECK(!klgr_cool_over(0xfffffff0ul, 0x10ul, 1000)); CHECK(klgr_cool_over(0xfffffff0ul, 0x2000ul, 1000));
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
