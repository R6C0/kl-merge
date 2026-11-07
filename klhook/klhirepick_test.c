/* klhirepick_test.c - OFF-GAME check of klhire_pick.h ([Hire] PickDefault: the unhired round's body; the online saved-Char rule).
 *   cl /nologo /W4 /D_CRT_SECURE_NO_WARNINGS klhirepick_test.c     (run from the klhook folder) */
#include <stdio.h>
#include "klhire_pick.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    int w = -1, r, ch;
    /* PickDefault=1: the pick in every unhired round */
    CHECK(klhp_default(1, 1, 13, 1, &w) == 13 && w == KLHP_USE);              /* the owner's case: Red (13) picked, round 1 */
    CHECK(klhp_default(1, 2, 13, 1, &w) == 13 && w == KLHP_USE);
    CHECK(klhp_default(1, 7, 3, 1, &w) == 3 && w == KLHP_USE);
    for (ch = 1; ch <= 16; ch++) CHECK(klhp_default(1, 1, ch, 1, 0) == ((ch == 9 || ch == 10) ? 0 : ch));
    /* fall back to random */
    CHECK(klhp_default(1, 1, 0, 1, &w) == 0 && w == KLHP_NONE);
    CHECK(klhp_default(1, 1, 9, 1, &w) == 0 && w == KLHP_HIREONLY);          /* Kane stays hire-only */
    CHECK(klhp_default(1, 1, 10, 1, &w) == 0 && w == KLHP_HIREONLY);         /* Lynch */
    CHECK(klhp_default(1, 1, 13, 0, &w) == 0 && w == KLHP_NOBODY);           /* a Dead Men pick on a stock DD map without wardrobe */
    CHECK(klhp_default(1, 1, 3, 0, &w) == 0 && w == KLHP_NOBODY);
    CHECK(klhp_default(1, 1, 17, 1, &w) == 0 && w == KLHP_RANGE);
    CHECK(klhp_default(1, 1, -1, 1, &w) == 0 && w == KLHP_RANGE);
    /* PickDefault=2: round 1 only */
    CHECK(klhp_default(2, 1, 13, 1, &w) == 13 && w == KLHP_USE);
    CHECK(klhp_default(2, 2, 13, 1, &w) == 0 && w == KLHP_LATER);
    /* PickDefault=0 or a bad value: the old random default */
    CHECK(klhp_default(0, 1, 13, 1, &w) == 0 && w == KLHP_OFF);
    CHECK(klhp_default(3, 1, 13, 1, &w) == 0 && w == KLHP_OFF);
    CHECK(klhp_default(-1, 1, 13, 1, &w) == 0 && w == KLHP_OFF);
    r = klhp_default(1, 1, 4, 1, 0); CHECK(r == 4);                           /* why may be 0 */
    for (w = KLHP_USE; w <= KLHP_LATER; w++) CHECK(klhp_why[w] && klhp_why[w][0]);
    /* online: zero the saved Char only with hire on + OnlineIgnoreChar, and then only PickDefault=0 or Kane / Lynch */
    CHECK(klhp_online_zero(1, 1, 0, 13) == 1);                                /* the 10-27 G1 behaviour, unchanged with the key off */
    CHECK(klhp_online_zero(1, 1, 1, 13) == 0);                                /* the owner's case: kept */
    CHECK(klhp_online_zero(1, 1, 2, 13) == 0);
    CHECK(klhp_online_zero(1, 1, 1, 9) == 1 && klhp_online_zero(1, 1, 1, 10) == 1);
    CHECK(klhp_online_zero(0, 1, 0, 13) == 0);                                /* hire off: never */
    CHECK(klhp_online_zero(1, 0, 0, 13) == 0);                                /* OnlineIgnoreChar=0: never */
    CHECK(klhp_online_zero(1, 1, 0, 0) == 0);                                 /* nothing to zero */
    printf("klhirepick_test: %d checks, %d failed\n", checks, fails);
    return fails != 0;
}
