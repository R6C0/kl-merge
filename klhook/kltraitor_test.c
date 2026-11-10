/* kltraitor_test.c - off-game harness for kltraitor_logic.h. Build: cl /nologo /W3 kltraitor_test.c /Fe:kltraitor_test.exe   Run: exit 0 = all pass */
#include <stdio.h>
#include "kltraitor_logic.h"
static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)
int main(void)
{
    CHECK(kltr_reveal(1000, 1100, 0, 0, 25000) == KLTR_REV_NONE, "fresh mask stays hidden");
    CHECK(kltr_reveal(1000, 1100, 1, 0, 25000) == KLTR_REV_SHOT, "his shot reveals");
    CHECK(kltr_reveal(1000, 1100, 0, 1, 25000) == KLTR_REV_KILL, "a crew death near him reveals");
    CHECK(kltr_reveal(1000, 1100, 1, 1, 25000) == KLTR_REV_SHOT, "shot first");
    CHECK(kltr_reveal(1000, 26000, 0, 0, 25000) == KLTR_REV_TIMEOUT, "timeout at exactly 25 s");
    CHECK(kltr_reveal(1000, 25999, 0, 0, 25000) == KLTR_REV_NONE, "1 ms before the timeout");
    CHECK(kltr_reveal(1000, 99999999, 0, 0, 0) == KLTR_REV_NONE, "timeout 0 = never");
    CHECK(kltr_reveal(0xfffffff0ul, 0x20, 0, 0, 25) == KLTR_REV_TIMEOUT, "clock wrap: 0x30 ms >= 25");
    CHECK(kltr_reveal(0xfffffff0ul, 0x04, 0, 0, 25) == KLTR_REV_NONE, "clock wrap: 0x14 ms < 25");
    CHECK(kltr_hurt(100, 90), "drop");
    CHECK(!kltr_hurt(100, 100), "same");
    CHECK(!kltr_hurt(90, 100), "heal");
    CHECK(!kltr_hurt(0, 0), "no previous");
    CHECK(!kltr_hurt(100, 99.9995f), "noise");
    CHECK(kltr_attacker_ok(1, 0), "bot in play");
    CHECK(!kltr_attacker_ok(0, 0), "human");
    CHECK(!kltr_attacker_ok(1, 7), "dead bot");
    CHECK(!kltr_attacker_ok(3, 4), "aboard");
    CHECK(kltr_defend(100, 99, 0, 2), "100% always");
    CHECK(!kltr_defend(0, 0, 0, 2), "0% never");
    CHECK(kltr_defend(35, 34, 0, 2), "roll 34 < 35");
    CHECK(!kltr_defend(35, 35, 0, 2), "roll 35 not < 35");
    CHECK(!kltr_defend(100, 0, 2, 2), "at the max: no third defended attacker");
    CHECK(kltr_defend(100, 0, 1, 2), "below the max");
    CHECK(!kltr_defend(100, 0, 0, 0), "max 0 = off");
    CHECK(!kltr_defend(50, -1, 0, 2), "bad roll");
    CHECK(kltr_expired(0, 5), "no stamp = expired");
    CHECK(!kltr_expired(100, 99), "before");
    CHECK(kltr_expired(100, 100), "at");
    CHECK(!kltr_expired(0x10, 0xfffffff0ul), "wrap: until is in the future");
    CHECK(kltr_expired(0xfffffff0ul, 0x10), "wrap: until is in the past");
    CHECK(kltr_turn_ok(0, 1), "first turn");
    CHECK(!kltr_turn_ok(1, 1), "second refused at 1");
    CHECK(kltr_turn_ok(1, 2), "second ok at 2");
    CHECK(!kltr_turn_ok(2, 2), "third refused at 2");
    CHECK(kltr_turn_ok(9, 0), "0 = no cap");
    CHECK(kltr_mask_flags(0x5, 1) == 0x4, "hidden: bit 1 off, others kept");
    CHECK(kltr_mask_flags(0x5, 0) == 0x5, "shown: unchanged");
    printf("%s: %d checks, %d fails\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails ? 1 : 0;
}
