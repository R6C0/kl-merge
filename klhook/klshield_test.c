/* klshield_test.c - OFF-GAME check of klshield_logic.h (refund clamps, NaN, victim floor, threshold, Online world gate). */
#include <stdio.h>
#include "klshield_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    volatile float z = 0.0f; float nan = z / z;
    CHECK(klsh_refund(50, 20, 100, 0.65f) > 12.99f && klsh_refund(50, 20, 100, 0.65f) < 13.01f);
    CHECK(klsh_refund(95, 20, 100, 0.65f) == 5.0f);               /* capped at the maximum */
    CHECK(klsh_refund(100, 20, 100, 0.65f) == 0.0f);
    CHECK(klsh_refund(120, 20, 100, 0.65f) == 0.0f);              /* over max: never negative */
    CHECK(klsh_refund(50, -5, 100, 0.65f) == 0.0f);
    CHECK(klsh_refund(50, 20, 100, 0.0f) == 0.0f);
    CHECK(klsh_refund(nan, 20, 100, 0.65f) == 0.0f);
    CHECK(klsh_refund(50, nan, 100, 0.65f) == 0.0f);
    CHECK(klsh_refund(50, 20, nan, 0.65f) == 0.0f);
    CHECK(klsh_victim_loss(10, 100, 100, 2.0f) == 20.0f);
    CHECK(klsh_victim_loss(10, 0.5f, 100, 2.0f) == 0.0f);        /* player max < 1 */
    CHECK(klsh_victim_loss(0, 100, 100, 2.0f) == 0.0f);
    CHECK(klsh_victim_loss(10, 100, 100, 0.0f) == 0.0f);
    CHECK(klsh_victim_loss(10, 100, nan, 2.0f) == 0.0f);
    CHECK(klsh_victim_after(50, 20) == 30.0f);
    CHECK(klsh_victim_after(50, 80) == 1.0f);                    /* never below 1 */
    CHECK(klsh_victim_after(1.0f, 5) == 1.0f);
    CHECK(klsh_victim_after(0.5f, 5) == 0.5f);                   /* already under 1: untouched, not raised */
    CHECK(klsh_down_threshold(100, 35) == 35.0f);
    CHECK(klsh_down_threshold(1, 35) == 1.0f);
    CHECK(klsh_world(1, 1, 0, 0) == KLSH_W_ARC);
    CHECK(klsh_world(1, 1, 2, 1) == KLSH_W_ARC);                 /* Arcade wins */
    CHECK(klsh_world(1, 0, 0, 1) == KLSH_W_FORGET);              /* Online off: never online */
    CHECK(klsh_world(1, 0, 1, 1) == KLSH_W_ONLINE);
    CHECK(klsh_world(0, 0, 2, 1) == KLSH_W_ONLINE);              /* Enable=0 but Online on */
    CHECK(klsh_world(0, 1, 1, 1) == KLSH_W_ONLINE);              /* Arcade part off: online still decides */
    CHECK(klsh_world(1, 0, 1, -1) == KLSH_W_SKIP);
    CHECK(klsh_world(1, 0, 1, 0) == KLSH_W_FORGET);              /* client / not a round */
    CHECK(klsh_world(1, 0, 3, 1) == KLSH_W_FORGET);              /* bad config */
    printf("klshield_test: %d checks, %d fail\n", checks, fails);
    return fails ? 1 : 0;
}
