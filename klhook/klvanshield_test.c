/* klvanshield_test.c - off-game harness for klvanshield_logic.h. Build: cl /nologo /W3 klvanshield_test.c /Fe:klvanshield_test.exe */
#include <stdio.h>
#include "klvanshield_logic.h"
static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)
int main(void)
{
    CHECK(kvs_rec_can(1, 0, 0) == 1, "in play");
    CHECK(kvs_rec_can(1, 0, 1) == 1, "loyal AI");
    CHECK(kvs_rec_can(1, 0, 2) == 0, "traitor");
    CHECK(kvs_rec_can(1, 7, 0) == 0, "dead");
    CHECK(kvs_rec_can(1, 4, 0) == 0, "aboard already");
    CHECK(kvs_rec_can(0, 0, 0) == 0, "unused");
    CHECK(kvs_keep(0, 0, 3, 0, 20000) == 0, "key off");
    CHECK(kvs_keep(1, 0, 3, 5000, 20000) == 1, "crew could board: keep");
    CHECK(kvs_keep(1, 0, 0, 5000, 20000) == 0, "nobody could board: release");
    CHECK(kvs_keep(1, 2, 3, 5000, 20000) == 0, "somebody aboard: old rule");
    CHECK(kvs_keep(1, 0, 3, 20000, 20000) == 0, "cap reached");
    CHECK(kvs_keep(1, 0, 3, 19999, 20000) == 1, "just under cap");
    CHECK(kvs_heal(0, 10, 3000) == 0, "floor 0 off");
    CHECK(kvs_heal(90, 68, 3000) == 1, "68/3000 healed");
    CHECK(kvs_heal(90, 2800, 3000) == 0, "93 pct not healed");
    CHECK(kvs_heal(90, 0, 3000) == 0, "dead not raised");
    CHECK(kvs_heal(90, 100, 0) == 0, "no max");
    CHECK(kvs_wait_shield(1, 3, 0, 0, 0, 0) == 1, "waiting, no driver: shielded");
    CHECK(kvs_wait_shield(1, 4, 0, 0, 9000, 0) == 1, "state 4 empty, no cap: shielded");
    CHECK(kvs_wait_shield(1, 3, 1, 0, 100, 0) == 0, "boarded: ends");
    CHECK(kvs_wait_shield(1, 5, 0, 0, 100, 0) == 0, "leaving: ends");
    CHECK(kvs_wait_shield(1, 2, 0, 0, 100, 0) == 0, "still driving in: not this key");
    CHECK(kvs_wait_shield(1, 3, 0, 0, 19999, 20000) == 1, "just under cap");
    CHECK(kvs_wait_shield(1, 3, 0, 0, 20000, 20000) == 0, "cap expiry");
    CHECK(kvs_wait_shield(0, 3, 0, 0, 0, 0) == 0, "toggle off: no change");
    CHECK(kvs_wait_shield(1, 3, 0, 1, 0, 0) == 0, "round over");
    CHECK(kvs_wait_shield(1, 6, 0, 1, 0, 0) == 0, "destroyed");
    CHECK(kvs_drivein_shield(1, 2) == 1, "driving in: shielded");
    CHECK(kvs_drivein_shield(0, 2) == 0, "drive-in key off");
    CHECK(kvs_drivein_shield(1, 0) == 0, "no vehicle called");
    CHECK(kvs_drivein_shield(1, 1) == 0, "state 1 left out (GUESS)");
    CHECK(kvs_drivein_shield(1, 3) == 0, "waiting: the wait keys' business");
    CHECK(kvs_drivein_shield(1, 6) == 0, "destroyed");
    printf("%s: %d checks, %d failed\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
