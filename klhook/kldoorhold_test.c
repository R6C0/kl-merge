/* kldoorhold_test.c - off-game harness for kldoorhold_logic.h ([BotFill] OnlineDoorHold pure decision; klbotfill.c includes the same header). No windows.h.
   Build: cl /nologo /W3 kldoorhold_test.c /Fe:kldoorhold_test.exe     Run: kldoorhold_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include "kldoorhold_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    struct kdh_st h; unsigned t0 = 1000;
    memset(&h, 0, sizeof h);
    CHECK(kdh_step(&h, 0, 90, t0 + 1000, t0, 48, 10, 0) == 0 && h.state == 0, "off: never holds");
    CHECK(kdh_step(&h, 1, 90, t0 + 1000, t0, 0, 10, 0) == 0 && h.state == 0 && h.ev == 0, "no shut doors: no hold, nothing latched");
    CHECK(kdh_step(&h, 1, 90, t0 + 2000, t0, 48, 0, 0) == 1 && h.ev == 1, "shut doors: hold starts, event 1");
    h.ev = 0;
    CHECK(kdh_applies(1, 0) == 1 && kdh_applies(1, 500) == 0 && kdh_applies(0, 0) == 0, "tally > 0 is not held");
    CHECK(kdh_step(&h, 1, 90, t0 + 3000, t0, 48, 0, 0) == 1 && h.ev == 0, "still holding, no second start event");
    /* all open */
    CHECK(kdh_step(&h, 1, 90, t0 + 40000, t0, 0, 20, 0) == 1 && h.state == 1 && h.ev == 0, "one zero tick does not latch");
    CHECK(kdh_step(&h, 1, 90, t0 + 40000, t0, 0, 20, 0) == 1 && h.state == 1, "same tick again (second bot) is still one tick");
    CHECK(kdh_step(&h, 1, 90, t0 + 40500, t0, 5, 20, 0) == 1 && h.zero_n == 0, "a nonzero count resets the zero run");
    CHECK(kdh_step(&h, 1, 90, t0 + 41000, t0, 0, 20, 0) == 1 && h.state == 1, "zero, one tick again");
    CHECK(kdh_step(&h, 1, 90, t0 + 41500, t0, 0, 20, 0) == 0 && h.state == 2 && h.reason == KDH_OPEN && h.ev == 2, "two zero ticks in a row: all doors open ends it");
    CHECK(kdh_step(&h, 1, 90, t0 + 41000, t0, 5, 20, 0) == 0, "latched for the round");

    /* timer */
    memset(&h, 0, sizeof h);
    CHECK(kdh_step(&h, 1, 90, t0 + 10000, t0, 30, 0, 0) == 1, "timer: holding");
    CHECK(kdh_step(&h, 1, 90, t0 + 89999, t0, 29, 0, 0) == 1, "timer: 1 ms before 90 s");
    CHECK(kdh_step(&h, 1, 90, t0 + 90000, t0, 29, 0, 0) == 0 && h.reason == KDH_TIMER, "timer expiry at 90 s");

    /* stall: armed at +38 s with 48 shut, flat for 25 s */
    memset(&h, 0, sizeof h);
    CHECK(kdh_step(&h, 1, 150, t0 + 30000, t0, 58, 0, 0) == 1, "stall: holding before armed");
    CHECK(kdh_step(&h, 1, 150, t0 + 38000, t0, 48, 10, 0) == 1 && h.armed, "stall: first armed stack");
    CHECK(kdh_step(&h, 1, 150, t0 + 50000, t0, 40, 10, 0) == 1 && h.min_shut == 40 && h.min_at == t0 + 50000, "count falls: stall clock restarts");
    CHECK(kdh_step(&h, 1, 150, t0 + 74999, t0, 40, 10, 0) == 1, "24.999 s flat: still holding");
    CHECK(kdh_step(&h, 1, 150, t0 + 75000, t0, 40, 10, 0) == 0 && h.reason == KDH_STALL, "25 s flat: stall release");
    /* stall clock does not run before the first armed stack */
    memset(&h, 0, sizeof h);
    CHECK(kdh_step(&h, 1, 150, t0 + 1000, t0, 58, 0, 0) == 1 && kdh_step(&h, 1, 150, t0 + 60000, t0, 58, 0, 0) == 1, "no armed stack yet: no stall");
    /* late clock */
    memset(&h, 0, sizeof h);
    kdh_step(&h, 1, 90, t0 + 1000, t0, 10, 0, 0);
    CHECK(kdh_step(&h, 1, 90, t0 + 2000, t0, 10, 0, 1) == 0 && h.reason == KDH_LATE, "low clock ends the hold");

    /* clamp */
    CHECK(kdh_clamp(0) == 20 && kdh_clamp(19) == 20 && kdh_clamp(20) == 20 && kdh_clamp(90) == 90 && kdh_clamp(150) == 150 && kdh_clamp(151) == 150 && kdh_clamp(-5) == 20 && kdh_clamp(9999) == 150, "clamp 20..150");
    memset(&h, 0, sizeof h);
    kdh_step(&h, 1, 5, t0, t0, 10, 0, 0);
    CHECK(kdh_step(&h, 1, 5, t0 + 19999, t0, 10, 0, 0) == 1 && kdh_step(&h, 1, 5, t0 + 20000, t0, 10, 0, 0) == 0, "hold_s 5 acts as 20");
    memset(&h, 0, sizeof h);
    kdh_step(&h, 1, 999, t0, t0, 10, 0, 0);
    CHECK(kdh_step(&h, 1, 999, t0 + 149999, t0, 10, 0, 0) == 1 && kdh_step(&h, 1, 999, t0 + 150000, t0, 10, 0, 0) == 0, "hold_s 999 acts as 150");

    printf("kldoorhold_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
