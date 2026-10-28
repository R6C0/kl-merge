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
    printf("klguard_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
