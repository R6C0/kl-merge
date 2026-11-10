/* klexitoff_test.c - klexitoff_logic.h outside the game (pure logic, no Windows calls).
 *   cl /nologo /W3 klexitoff_test.c /Fe:klexitoff_test.exe        or      gcc -m32 -Wall klexitoff_test.c -o klexitoff_test
 * exit code 0 = every check passed. */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klexitoff_logic.h"

static int bad;
#define CHECK(c, ...) do { if (!(c)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

/* an axis-aligned box centred at bc with half extents hx, hz, shrunk by a margin of 100 cm */
struct box { float c[3], hx, hz; };
static int in_box(void *ctx, const float p[3])
{
    const struct box *b = (const struct box *)ctx;
    return fabs(p[0] - b->c[0]) <= b->hx - 100.0f && fabs(p[2] - b->c[2]) <= b->hz - 100.0f;
}
/* distance of p from the infinite line through a with unit direction d (x/z) */
static float line_dist(const float a[3], const float d[2], const float p[3])
{
    return (float)fabs((p[0] - a[0]) * d[1] - (p[2] - a[2]) * d[0]);
}

int main(void)
{
    struct box big = { { 6855, 0, 26051 }, 4509, 2371 }, strip = { { 0, 0, 0 }, 450, 120 };
    float out[3], lane[2], van[3], lx[2] = { 1, 0 };
    int r;

    /* DD01-like: box centre (6855, 26051), the van comes from the west along x (z 26051 + 131 off): the target must clear the 150 cm footprint */
    van[0] = -3000; van[1] = 0; van[2] = 26182;
    r = klxo_target(big.c, van, lx, 400, in_box, &big, out);
    CHECK(r == 1, "a big box moves the target");
    CHECK(klxo_lane(big.c, van, lx, lane) == 1, "lane comes from the van");
    { float d_to_lane = (float)fabs(out[2] - 26182);   /* the real lane is horizontal at z 26182 */
      CHECK(d_to_lane > 150.0f + 40.0f, "target %.0f cm from the real lane (want > 190)", d_to_lane); }
    CHECK(in_box(&big, out), "target stays inside the margin box");
    CHECK(fabs(out[1] - big.c[1]) < 0.01f, "height untouched");

    /* off <= 0 or under the minimum = the centre */
    CHECK(klxo_target(big.c, van, lx, 0, in_box, &big, out) == 0 && out[0] == big.c[0] && out[2] == big.c[2], "off 0 = centre");
    CHECK(klxo_target(big.c, van, lx, 100, in_box, &big, out) == 0 && out[2] == big.c[2], "off under the minimum = centre");
    CHECK(klxo_target(big.c, van, lx, 400, NULL, &big, out) == 0, "no inside test = centre");

    /* a van that is not placed (0,0,0) or on the centre: falls back to the long axis (x) -> shift along z */
    van[0] = van[1] = van[2] = 0;
    r = klxo_target(big.c, van, lx, 400, in_box, &big, out);
    CHECK(r == 1 && fabs(out[0] - big.c[0]) < 0.5f && fabs(fabs(out[2] - big.c[2]) - 400) < 0.5f, "origin van: long-axis lane, z shift 400 (got %.0f %.0f)", out[0], out[2]);
    van[0] = big.c[0] + 100; van[1] = 0; van[2] = big.c[2];
    CHECK(klxo_lane(big.c, van, lx, lane) == 0, "van 100 cm from the centre is no direction");
    CHECK(klxo_lane(big.c, NULL, NULL, lane) == -1, "nothing usable = -1");
    CHECK(klxo_target(big.c, NULL, NULL, 400, in_box, &big, out) == 0 && out[0] == big.c[0], "no lane = centre");

    /* a strip box (900 x 240): 100 cm margin leaves z +-20; no shift of 250+ fits = the centre */
    CHECK(klxo_target(strip.c, NULL, lx, 400, in_box, &strip, out) == 0 && out[0] == 0 && out[2] == 0, "strip too narrow = centre");

    /* only one side fits: the box edge is near the van side's opposite; it takes the free side */
    { struct box edge = { { 0, 0, 0 }, 3000, 600 };      /* margin box z +-500: 400 fits both ways */
      float lz[2] = { 1, 0 };
      r = klxo_target(edge.c, NULL, lz, 600, in_box, &edge, out);      /* 600 fails, 480 (80 %) fits */
      CHECK(r == 1 && fabs(fabs(out[2]) - 480) < 0.5f, "shrinks to 80 %% (got z %.0f)", out[2]);
      edge.c[2] = 0; edge.hz = 600;
      r = klxo_target(edge.c, NULL, lz, 1000, in_box, &edge, out);      /* 1000, 800 fail, 600 fails (500 max): centre */
      CHECK(r == 0, "no size fits = centre"); }

    /* a diagonal lane (DM06B-like): the target is perpendicular to it, clear of the line by the offset */
    { struct box b2 = { { 0, 0, 0 }, 3000, 3000 }; float v2[3] = { -2000, 0, -2000 }, d[2] = { 0.7071068f, 0.7071068f };
      r = klxo_target(b2.c, v2, lx, 400, in_box, &b2, out);
      CHECK(r == 1 && fabs(line_dist(b2.c, d, out) - 400) < 1.0f, "diagonal: %.1f cm off the lane", line_dist(b2.c, d, out)); }

    if (bad) { printf("klexitoff_test: %d FAILED\n", bad); return 1; }
    printf("klexitoff_test: all checks passed\n");
    return 0;
}
