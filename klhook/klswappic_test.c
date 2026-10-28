/* klswappic_test.c - off-game checks of klswappic.h. Build: cl /nologo /W3 klswappic_test.c */
#include <stdio.h>
#include "klswappic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    /* look-alikes */
    CHECK(ksp_lookalike(52) == 14);
    CHECK(ksp_lookalike(33) == 30);
    CHECK(ksp_lookalike(49) == 32);
    CHECK(ksp_lookalike(47) == 32);
    CHECK(ksp_lookalike(0) == -1);
    CHECK(ksp_lookalike(7) == -1);
    /* default carriers on an unbaked map, pool handed ours */
    CHECK(ksp_pic_row(1, 1, 13, 2, 52, 1) == 14);
    CHECK(ksp_pic_row(1, 1, 16, 2, 33, 1) == 30);
    CHECK(ksp_pic_row(1, 1, 32, 2, 49, 1) == -1);      /* P == R */
    CHECK(ksp_pic_row(1, 1, 35, 2, 47, 1) == 32);
    CHECK(ksp_pic_row(1, 0, 13, 2, 52, 1) == 14);      /* Arcade too */
    /* off / baked / not ours / not a swap row */
    CHECK(ksp_pic_row(0, 1, 13, 2, 52, 1) == -1);
    CHECK(ksp_pic_row(1, 1, 13, 2, 52, 0) == -1);      /* baked or not asked yet */
    CHECK(ksp_pic_row(1, 1, 13, 3, 52, 1) == -1);      /* decided stock */
    CHECK(ksp_pic_row(1, 1, 13, 1, 52, 1) == -1);      /* undecided */
    CHECK(ksp_pic_row(1, 1, 13, 0, 0, 1) == -1);
    CHECK(ksp_pic_row(1, 1, 14, 2, 52, 1) == -1);
    CHECK(ksp_pic_row(1, 1, -1, 2, 52, 1) == -1);
    CHECK(ksp_pic_row(1, 1, 13, 2, 99, 1) == -1);      /* unknown item */
    /* index swap */
    CHECK(ksp_new_index(13, 13, 14) == 14);
    CHECK(ksp_new_index(14, 13, 14) == 13);
    CHECK(ksp_new_index(5, 13, 14) == 5);
    CHECK(ksp_new_index(13, 13, -1) == 13);
    /* swapping twice restores */
    CHECK(ksp_new_index(ksp_new_index(13, 13, 14), 13, 14) == 13);
    printf("klswappic_test: %d checks, %d fails\n", checks, fails);
    return fails ? 1 : 0;
}
