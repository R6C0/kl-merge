/* klpicown_test.c - off-game checks of klpicown_logic.h. Build: cl /nologo /W3 klpicown_test.c */
#include <stdio.h>
#include "klpicown_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    unsigned long all[2] = { 0, 0 }, none[2] = { 0, 0 }, some[2] = { 0, 0 };
    int i;
    for (i = 0; i < 200; i++) kpo_mask_set(all, i);                                  /* only the own indices set a bit */
    CHECK(all[0] == 0xfff0fffful && all[1] == 0xfful);                            /* bits for 100..115 and 120..139 */
    CHECK(kpo_is_own(100) && kpo_is_own(115) && kpo_is_own(120) && kpo_is_own(139));
    CHECK(!kpo_is_own(99) && !kpo_is_own(116) && !kpo_is_own(119) && !kpo_is_own(140) && !kpo_is_own(35) && !kpo_is_own(-1));
    kpo_mask_set(some, 102); kpo_mask_set(some, 125);
    CHECK(kpo_mask_has(some, 102) && kpo_mask_has(some, 125) && !kpo_mask_has(some, 103) && !kpo_mask_has(some, 5));
    /* hire page */
    CHECK(kpo_want(1, 3, 0, -1, all) == 102);
    CHECK(kpo_want(1, 16, 0, -1, all) == 115);
    CHECK(kpo_want(1, 0, 0, -1, all) == -1);                                         /* a row that is no heister */
    CHECK(kpo_want(1, 17, 0, -1, all) == -1);
    CHECK(kpo_want(1, 3, 0, -1, none) == -1);                                        /* map not baked: fail open */
    CHECK(kpo_want(1, 4, 0, -1, some) == -1);                                        /* its card missing */
    CHECK(kpo_want(1, 3, 0, -1, some) == 102);
    CHECK(kpo_want(0, 3, 0, -1, all) == -1);                                         /* BakedPics off / not the hire page */
    /* page II */
    CHECK(kpo_want(0, 0, 1, 5, all) == 125);
    CHECK(kpo_want(0, 0, 1, 19, all) == 139);
    CHECK(kpo_want(0, 0, 1, 20, all) == -1 && kpo_want(0, 0, 1, -1, all) == -1);
    CHECK(kpo_want(0, 0, 1, 5, none) == -1 && kpo_want(0, 0, 1, 6, some) == -1 && kpo_want(0, 0, 1, 5, some) == 125);
    CHECK(kpo_want(0, 0, 0, 5, all) == -1);                                          /* OwnPics off */
    CHECK(kpo_want(1, 3, 1, 5, all) == 102);                                         /* hire page wins (never both on screen in practice) */
    /* indices */
    CHECK(kpo_big_index(102, 2, 102) == 2);                                          /* the wanted card draws: shown row */
    CHECK(kpo_big_index(103, 2, 102) == -1);                                         /* another own card: stays unmatched (>= 100) */
    CHECK(kpo_big_index(14, 14, 125) == KPO_HIDE);                                   /* the carrier's stock card is hidden */
    CHECK(kpo_big_index(99, 14, 125) == -1);                                         /* already hidden */
    CHECK(kpo_big_index(14, 14, -1) == -1 && kpo_big_index(125, 14, -1) == -1);      /* nothing wanted: untouched */
    printf("klpicown_test: %d checks, %d fails\n", checks, fails);
    return fails ? 1 : 0;
}
