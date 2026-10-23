/* klcv_test.c - OFF-GAME check of klchar_voice.h: which .SND offset the body choice asks for, the bank-base arithmetic and the
 * definition-head test of re\bots_voice.md 6.5. Pure numbers; the game reads are klchar.c's (klh_rd / klh_data), not here.
 *   cl /nologo /W4 klcv_test.c      or      tools/run_harness_linux.sh klcv_test */
#include <windows.h>
#include <stdio.h>
#include "klchar_voice.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    struct klcv_cfg off = { 0, 0, 0 }, k = { 1000, 0, 5000 }, kl = { 1000, 2000, 5000 }, nomat = { 1000, 2000, 0 };
    int ch;
    /* off unless the material offset and at least one voice are given */
    CHECK(!klcv_enabled(&off)); CHECK(!klcv_enabled(&nomat)); CHECK(klcv_enabled(&k)); CHECK(klcv_enabled(&kl));
    for (ch = 0; ch <= 16; ch++) CHECK(klcv_want(&off, ch) == 0);
    for (ch = 0; ch <= 16; ch++) CHECK(klcv_want(&nomat, ch) == 0);
    /* Kane -> Kane's set, Lynch -> Lynch's, every other body (stock 1..8, the other Dead Men ones, 0 = the game's own) -> 0 */
    CHECK(klcv_want(&kl, KLCV_KANE) == 1000); CHECK(klcv_want(&kl, KLCV_LYNCH) == 2000);
    CHECK(klcv_want(&k, KLCV_KANE) == 1000); CHECK(klcv_want(&k, KLCV_LYNCH) == 0);
    for (ch = 0; ch <= 16; ch++) if (ch != KLCV_KANE && ch != KLCV_LYNCH) CHECK(klcv_want(&kl, ch) == 0);
    /* bank base = material definition address - its .SND offset */
    CHECK(klcv_base(0x1a005000u, 5000) == 0x1a005000u - 5000);
    CHECK(klcv_base(0, 5000) == 0);
    CHECK(klcv_base(0x1a005000u, 0) == 0);
    CHECK(klcv_base(100, 5000) == 0);                      /* the definition cannot lie below the bank */
    /* a definition is accepted only with the head words [5][0xcdcdcdcd] */
    CHECK(klcv_def(0x1a000000u, 1000, 5, 0xcdcdcdcdu) == 0x1a000000u + 1000);
    CHECK(klcv_def(0x1a000000u, 1000, 4, 0xcdcdcdcdu) == 0);
    CHECK(klcv_def(0x1a000000u, 1000, 5, 0) == 0);
    CHECK(klcv_def(0, 1000, 5, 0xcdcdcdcdu) == 0);
    CHECK(klcv_def(0x1a000000u, 0, 5, 0xcdcdcdcdu) == 0);
    CHECK(klcv_def(0xfffffff0u, 0x100, 5, 0xcdcdcdcdu) == 0);     /* wrapped */
    printf("%d checks, %d failed\n", checks, fails);
    printf(fails ? "FAIL\n" : "ALL PASS\n");
    return fails ? 1 : 0;
}
