/* klvanrest_test.c - off-game harness for klvanrest_logic.h ([BotFill] OnlineVanRest). Build (x86): cl /nologo /W3 klvanrest_test.c /Fe:klvanrest_test.exe ; exit 0 = all pass */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klvanrest_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    float rest[3], r0[3] = { -23647, -980, -2700 };
    float org[3] = { 0, 0, 0 }, org1[3] = { 1, -1, 0.5f }, placed[3] = { -1852, 121, 8420 };
    float near_[3] = { -23647 + 60, -980, -2700 + 60 }, edge[3] = { -23647 + 100, -980, -2700 }, off[3] = { -23647 + 101, -980, -2700 }, far_[3] = { -23000, -980, -2700 };
    float nan3[3] = { 0, 0, 0 };
    nan3[0] = (float)sqrt(-1.0);

    CHECK(kvr_parse("-23647 -980 -2700", rest) && memcmp(rest, r0, 12) == 0, "plain");
    CHECK(kvr_parse("(-23647, -980, -2700)", rest) && rest[0] == -23647 && rest[2] == -2700, "separators");
    CHECK(!kvr_parse("", rest) && !kvr_parse("1 2", rest) && !kvr_parse("a b c", rest) && !kvr_parse(0, rest), "bad / absent = not configured");
    CHECK(!kvr_parse("1e30 0 0", rest) && !kvr_parse("nan 0 0", rest), "absurd / NaN refused");

    /* OFF (key absent): identical to the old guard for every input */
    CHECK(kvr_not_here(org, 0, 0) && kvr_not_here(org1, 0, 0) && !kvr_not_here(placed, 0, 0), "off: origin test only");
    CHECK(!kvr_not_here(r0, 0, r0) && !kvr_not_here(near_, 0, r0), "off: a van at the rest place counts as here (old behaviour)");
    CHECK(kvr_not_here(nan3, 0, 0) == !(fabs(nan3[0]) > 1 || fabs(nan3[1]) > 1 || fabs(nan3[2]) > 1), "off: NaN place = exactly the old guard's answer (not accepted)");
    /* ON */
    CHECK(kvr_not_here(org, 1, r0) && kvr_not_here(org1, 1, r0), "on: origin still not here");
    CHECK(kvr_not_here(r0, 1, r0) && kvr_not_here(near_, 1, r0) && kvr_not_here(edge, 1, r0), "on: within 100 cm of rest = not here");
    CHECK(!kvr_not_here(off, 1, r0) && !kvr_not_here(far_, 1, r0) && !kvr_not_here(placed, 1, r0), "on: 101 cm away / driven-in van = here");

    printf("klvanrest_test: %d checks, %d fails\n", checks, fails);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails ? 1 : 0;
}
