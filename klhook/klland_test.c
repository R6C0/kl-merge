/* klland_test.c - OFF-GAME check of klland_logic.h ([Join] Land=: when the landing move is made, when Land= is refused).
 *   cl /nologo /W4 klland_test.c      or      tools/run_harness_linux.sh klland_test */
#include <stdio.h>
#include <string.h>
#include "klland_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    const float entry[3] = { 8300, 0, 1100 }, south[3] = { 8300, 0, 780 }, far_[3] = { 0, 0, 0 }, up[3] = { 8300, 3000, 1100 };
    const float ledge[3] = { 6513, 1194, 2573 }, onit[3] = { 8301, 0, 1099 };
    float nan_[3]; const char *why = 0; volatile float zero = 0.0f;
    nan_[0] = zero / zero; nan_[1] = 0; nan_[2] = 780;
    /* Land= checks */
    CHECK(klland_ok(south, entry));                            /* DD10: 320 south of 06_Exit */
    CHECK(!klland_ok(far_, entry));                            /* 8370 away: refused */
    CHECK(!klland_ok(up, entry));                              /* 3000 up: refused */
    CHECK(!klland_ok(nan_, entry));
    /* the step */
    CHECK(klland_step(1100, 1000, 1, onit, entry, 0, &why) == 0);          /* too early */
    CHECK(klland_step(1300, 1000, 1, onit, entry, 0, &why) == 1);          /* at the entry, 300 ms: move */
    CHECK(klland_step(1500, 1000, 1, ledge, entry, 0, &why) == 0);         /* still on the ledge: wait for the jump */
    CHECK(klland_step(1500, 1000, 0, onit, entry, 0, &why) == 0);          /* feet unreadable: wait */
    CHECK(klland_step(1500, 1000, 1, onit, entry, 1, &why) == 0);          /* busy: wait */
    why = 0; CHECK(klland_step(4001, 1000, 1, ledge, entry, 0, &why) == -1 && why && strstr(why, "not at the jump point"));   /* never arrived */
    why = 0; CHECK(klland_step(4001, 1000, 1, onit, entry, 1, &why) == -1 && why && strstr(why, "busy"));                  /* stayed busy */
    why = 0; CHECK(klland_step(4001, 1000, 0, onit, entry, 0, &why) == -1 && why && strstr(why, "cannot be read"));        /* unreadable */
    CHECK(klland_step(4000, 1000, 1, onit, entry, 0, &why) == 1);          /* the last tick still moves */
    CHECK(klland_step(0x10, 0xffffff00ul, 1, onit, entry, 0, &why) == 0);  /* tick wrap: 272 ms after the request... */
    CHECK(klland_step(0x130, 0xffffff00ul, 1, onit, entry, 0, &why) == 1); /* ...560 ms: move */
    printf("klland_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
