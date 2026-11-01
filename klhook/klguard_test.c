/* klguard_test.c - off-game harness for klguard_logic.h. Build: cl /nologo /W3 klguard_test.c /Fe:klguard_test.exe   Run: exit 0 = all pass */
#include <stdio.h>
#include <math.h>
#include "klguard_logic.h"
static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)
int main(void)
{
    float s[3] = { 0, 0, 0 }, c1[3] = { 1000, 0, 0 }, c2[3] = { 1000, 900, 0 }, cn[3] = { 0, 0, 0 }, d[4] = { 500, 300, 300, -1 };
    int cnt[4] = { 3, 2, 2, -1 };
    CHECK(kgg_guards(c1, s, 2500, 0), "3D hit");
    CHECK(kgg_guards(c2, s, 2500, 0), "no floor gate: other floor guards (old rule)");
    CHECK(!kgg_guards(c2, s, 2500, 400), "floor gate: 9 m above does not guard");
    CHECK(kgg_guards(c1, s, 2500, 400), "same floor still guards");
    CHECK(!kgg_guards(c1, s, 500, 400), "outside radius");
    cn[0] = (float)sqrt(-1.0); CHECK(!kgg_guards(cn, s, 2500, 400), "NaN never guards");
    CHECK(!kgg_guards(c1, s, 0, 0), "radius 0 = no guard");
    CHECK(kgg_bypass_ok(47, 47, 8, 100000, 0, 15000), "all guarded, first release");
    CHECK(!kgg_bypass_ok(6, 6, 8, 100000, 0, 15000), "DD04: too few stacks to say the test is blind");
    CHECK(!kgg_bypass_ok(5, 6, 1, 100000, 0, 15000), "one stack free: old path");
    CHECK(!kgg_bypass_ok(47, 47, 8, 110000, 100000, 15000), "gap not over");
    CHECK(kgg_bypass_ok(47, 47, 8, 115000, 100000, 15000), "gap over");
    CHECK(kgg_bypass_ok(47, 47, 8, 5, 4294967000U, 15000) == 0, "tick wrap: 5 ms after");
    CHECK(!kgg_bypass_ok(0, 0, 0, 1, 0, 1), "nothing free");
    CHECK(kgg_pick(cnt, d, 4) == 1, "fewest cops then nearest, got %d", kgg_pick(cnt, d, 4));
    cnt[1] = cnt[2] = -1; CHECK(kgg_pick(cnt, d, 4) == 0, "only candidate");
    cnt[0] = -1; CHECK(kgg_pick(cnt, d, 4) == -1, "none");
    CHECK(kgg_radius(2500, 800, 1) == 800, "live-only: tight radius");
    CHECK(kgg_radius(2500, 800, 0) == 2500, "off: wide radius");
    CHECK(kgg_radius(2500, 0, 1) == 2500, "tight 0: wide");
    CHECK(kgg_radius(500, 800, 1) == 500, "tight wider than wide: wide");
    CHECK(kgg_radius(0, 800, 1) == 800, "wide 0 (guard off) with live-only: tight");
    { float z0[3] = { 0, 0, 0 }, zn[3] = { 0.5f, -0.5f, 1 }, st[3] = { -112, 79, 549 }, y2[3] = { 0, 2, 0 };
      CHECK(kgg_origin(z0), "origin: (0,0,0) skipped");
      CHECK(kgg_origin(zn), "origin: within 1 cm skipped");
      CHECK(!kgg_origin(st), "origin: a DD08 stack position kept");
      CHECK(!kgg_origin(y2), "origin: 2 cm up kept"); }
    { float st[3] = { 10298, 80, 7398 }, on[3] = { 10300, 80, 7399 }, nr[3] = { 10298, 80, 7798 }, nn[3] = { 0, 0, 0 };
      CHECK(kgg_carrier(on, st, 150), "carrier: a cop 2 cm away is the carrier");
      CHECK(!kgg_carrier(nr, st, 150), "carrier: a cop 4 m away is a guard");
      CHECK(!kgg_carrier(on, st, 0), "carrier: 0 = off");
      CHECK(!kgg_carrier(on, st, -5), "carrier: negative = off");
      nn[0] = (float)sqrt(-1.0); CHECK(!kgg_carrier(nn, st, 150), "carrier: NaN is no carrier"); }
    CHECK(kgg_partial_hold(1, 440000, 0, 2, 0, 5, 100000, 90000, 60000, 200, 90), "partial hold: DD06 case");
    CHECK(!kgg_partial_hold(0, 440000, 0, 2, 0, 5, 100000, 90000, 60000, 200, 90), "partial hold: key off");
    CHECK(!kgg_partial_hold(1, 0, 0, 2, 0, 5, 100000, 90000, 60000, 200, 90), "partial hold: nothing carried");
    CHECK(!kgg_partial_hold(1, 440000, 2, 2, 0, 5, 100000, 90000, 60000, 200, 90), "partial hold: carry limit reached");
    CHECK(!kgg_partial_hold(1, 440000, 0, 2, 1, 5, 100000, 90000, 60000, 200, 90), "partial hold: idle-van order wins");
    CHECK(!kgg_partial_hold(1, 440000, 0, 2, 0, 0, 100000, 90000, 60000, 200, 90), "partial hold: no stack left to wait for");
    CHECK(!kgg_partial_hold(1, 440000, 0, 2, 0, 5, 100000, 0, 60000, 200, 90), "partial hold: no partial stop");
    CHECK(!kgg_partial_hold(1, 440000, 0, 2, 0, 5, 150000, 90000, 60000, 200, 90), "partial hold: wait over");
    CHECK(!kgg_partial_hold(1, 440000, 0, 2, 0, 5, 100000, 90000, 60000, 80, 90), "partial hold: clock low");
    CHECK(kgg_partial_hold(1, 440000, 0, 2, 0, 5, 5, 4294967000U, 60000, 200, 90), "partial hold: tick wrap, 300 ms after");
    printf("klguard_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
