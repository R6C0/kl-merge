/* klht_test.c - OFF-GAME check of klhud_tags_dist.h: the HeadMaxDist / HeadFade arithmetic of the head tags (option D of
 * re\hud_tags_sight.md). Nothing about the game; the position reads it feeds on are klescort.c's, proven live.
 *   cl /nologo /W4 klht_test.c      or      tools/run_harness_linux.sh klht_test
 * Distances are centimetres (the game's units: 100 = 1 m); HeadMaxDist / HeadFade are metres. */
#include <windows.h>
#include <stdio.h>
#include <math.h>
#include "klhud_tags_dist.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    int a, prev, d;
    /* off: everything drawn at full alpha */
    CHECK(klht_alpha_at(0.0f, 0.0f, 5.0f) == 255);
    CHECK(klht_alpha_at(99999.0f, 0.0f, 5.0f) == 255);
    CHECK(klht_alpha_at(-1.0f, 0.0f, 5.0f) == 255);
    /* a failed read (-1) or NaN: drawn, as the stock does */
    CHECK(klht_alpha_at(-1.0f, 25.0f, 5.0f) == 255);
    CHECK(klht_alpha_at((float)sqrt(-1.0), 25.0f, 5.0f) == 255);
    /* 25 m, fade 5: full to 20 m, gone at 25 m, in between a straight line */
    CHECK(klht_alpha_at(0.0f, 25.0f, 5.0f) == 255);
    CHECK(klht_alpha_at(2000.0f, 25.0f, 5.0f) == 255);
    CHECK(klht_alpha_at(2250.0f, 25.0f, 5.0f) == 127);
    CHECK(klht_alpha_at(2499.0f, 25.0f, 5.0f) == 1);          /* 0.51 -> never 0 while nearer than the limit */
    CHECK(klht_alpha_at(2500.0f, 25.0f, 5.0f) == 0);
    CHECK(klht_alpha_at(9000.0f, 25.0f, 5.0f) == 0);
    /* monotone, never rises with distance */
    for (prev = 255, d = 0; d <= 3000; d += 7) { a = klht_alpha_at((float)d, 25.0f, 5.0f); CHECK(a <= prev && a >= 0 && a <= 255); prev = a; }
    /* a hard cut (fade 0) */
    CHECK(klht_alpha_at(2499.0f, 25.0f, 0.0f) == 255);
    CHECK(klht_alpha_at(2500.0f, 25.0f, 0.0f) == 0);
    /* a fade as long as the limit: starts at 0 m */
    CHECK(klht_alpha_at(0.0f, 10.0f, 10.0f) == 255);
    CHECK(klht_alpha_at(500.0f, 10.0f, 10.0f) == 127);
    /* the colour keeps its RGB and takes the alpha */
    CHECK(klht_with_alpha(0xfff3f0eau, 0) == 0x00f3f0eau);
    CHECK(klht_with_alpha(0xfff3f0eau, 127) == 0x7ff3f0eau);
    CHECK(klht_with_alpha(0xffe8831fu, 255) == 0xffe8831fu);
    CHECK(klht_with_alpha(0x00000000u, 300) == 0x2c000000u);   /* only the low byte of a bad alpha is taken */
    printf("%d checks, %d failed\n", checks, fails);
    printf(fails ? "FAIL\n" : "ALL PASS\n");
    return fails ? 1 : 0;
}
