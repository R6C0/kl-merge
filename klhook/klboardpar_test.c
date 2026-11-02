/* klboardpar_test.c - off-game harness for klboardpar_logic.h ([BotFill] OnlineBoardAllNear pure decision). No windows.h.
   Build: cl /nologo /W3 klboardpar_test.c /Fe:klboardpar_test.exe     Run: klboardpar_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "klboardpar_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    CHECK(kbp_near_clamp(0) == 0.0f, "0 off");
    CHECK(kbp_near_clamp(-5) == 0.0f, "negative off");
    CHECK(kbp_near_clamp(30) == 100.0f, "min 100");
    CHECK(kbp_near_clamp(300) == 300.0f, "300 kept");
    CHECK(kbp_near_clamp(99999) == 30000.0f, "max 30000");
    CHECK(kbp_limit(6000, 0) == 6000, "off = M");
    CHECK(kbp_limit(6000, 300) == 300, "near narrows");
    CHECK(kbp_limit(500, 3000) == 500, "near never widens");
    /* off: today's behaviour */
    CHECK(kbp_decide(0, 6000, 0) == 1, "off at box");
    CHECK(kbp_decide(5999, 6000, 0) == 1, "off 59 m counted (today)");
    CHECK(kbp_decide(6001, 6000, 0) == 0, "off beyond M");
    /* on: 300 cm */
    CHECK(kbp_decide(0, 6000, 300) == 1, "on at box");
    CHECK(kbp_decide(300, 6000, 300) == 1, "on at edge");
    CHECK(kbp_decide(301, 6000, 300) == 2, "on just beyond: left out, logged");
    CHECK(kbp_decide(5000, 6000, 300) == 2, "on 50 m: left out");
    CHECK(kbp_decide(6001, 6000, 300) == 0, "on beyond M: not a candidate");
    CHECK(kbp_decide(1000, 500, 3000) == 0, "near wider than M: M rules");
    printf("klboardpar_test: %d checks, %d FAIL\n", checks, fails);
    return fails ? 1 : 0;
}
