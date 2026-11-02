/* klwaitvan_test.c - off-game harness for klwaitvan_logic.h ([BotFill] OnlineLegWaitVan pure decision; klbotfill.c includes the same header).
   Proves the decision, NOT that bots walk or survive (re/dm09_van_timing_1101.md). No windows.h.
   Build: cl /nologo /W3 klwaitvan_test.c /Fe:klwaitvan_test.exe     Run: klwaitvan_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "klwaitvan_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    /* van readiness */
    CHECK(kwv_van_ready(-1, 0) == 0 && kwv_van_ready(0, 0) == 0 && kwv_van_ready(1, 0) == 0, "states -1/0/1: not there");
    CHECK(kwv_van_ready(2, 0) == 1 && kwv_van_ready(4, 0) == 1 && kwv_van_ready(6, 0) == 1, "states 2/4/6: there");
    CHECK(kwv_van_ready(0, 1) == 1, "called by the hook: there");

    /* key off = never */
    CHECK(kwv_step(0, KWV_IDLE, 1, 1, 1, 0, 0, 0, 0) == KWV_NONE, "off: none");
    CHECK(kwv_step(0, KWV_WAITING, 1, 1, 1, 0, 0, 0, 0) == KWV_NONE, "off: none even when marked waiting");

    /* idle: only at the hold leg, only when the leg logic would advance, only without a van */
    CHECK(kwv_step(1, KWV_IDLE, 0, 1, 1, 0, 0, 0, 0) == KWV_NONE, "before the hold leg: none");
    CHECK(kwv_step(1, KWV_IDLE, 2, 1, 1, 0, 0, 0, 0) == KWV_NONE, "past the hold leg: none");
    CHECK(kwv_step(1, KWV_IDLE, 1, 1, 0, 0, 0, 0, 0) == KWV_NONE, "walking to the hold leg: none");
    CHECK(kwv_step(1, KWV_IDLE, 1, 1, 1, 0, 0, 0, 0) == KWV_START, "arrived, no van (state 0): start");
    CHECK(kwv_step(1, KWV_IDLE, 1, 1, 1, -1, 0, 0, 0) == KWV_START, "arrived, state unreadable: start");
    CHECK(kwv_step(1, KWV_IDLE, 1, 1, 1, 1, 0, 0, 0) == KWV_START, "arrived, state 1: start");
    CHECK(kwv_step(1, KWV_IDLE, 1, 1, 1, 2, 0, 0, 0) == KWV_NONE, "arrived, van already coming: run on");
    CHECK(kwv_step(1, KWV_IDLE, 1, 1, 1, 0, 1, 0, 0) == KWV_NONE, "arrived, van called: run on");
    CHECK(kwv_step(1, KWV_IDLE, 0, 0, 1, 0, 0, 0, 0) == KWV_START, "idx 0 works");

    /* waiting */
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 0, 0, 0, 5000, 0) == KWV_HOLD, "waiting, no van: hold (no cap)");
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 1, 0, 0, 900000, 0) == KWV_HOLD, "no cap = hold for ever, 15 minutes in");
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 1, 1, 0, 100000, 0) == KWV_HOLD, "state 1 still holds");
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 0, 2, 0, 5000, 0) == KWV_REL_VAN, "state 2: release");
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 0, 0, 1, 5000, 0) == KWV_REL_VAN, "called: release");
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 0, 0, 0, 59999, 60) == KWV_HOLD, "cap 60 s: 59.999 s holds");
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 0, 0, 0, 60000, 60) == KWV_REL_CAP, "cap 60 s: 60 s releases");
    CHECK(kwv_step(1, KWV_WAITING, 1, 1, 0, 3, 0, 90000, 60) == KWV_REL_VAN, "van wins over the cap");

    /* released: never again */
    CHECK(kwv_step(1, KWV_RELEASED, 1, 1, 1, 0, 0, 0, 0) == KWV_NONE, "released: none");

    /* stall cut */
    CHECK(kwv_nostall(0, 4, 0) == 0 && kwv_nostall(1, 0, 0) == 0 && kwv_nostall(1, 2, 0) == 1 && kwv_nostall(1, 0, 1) == 1, "no stall cut once the van is there");

    /* OnlineLegWaitCall */
    CHECK(kwv_call_ok(1, 1, 1, 1, 0, 0, 1, 1) == 1, "all set, one carrier waits: call");
    CHECK(kwv_call_ok(0, 1, 1, 1, 0, 0, 1, 1) == 0 && kwv_call_ok(1, 0, 1, 1, 0, 0, 1, 1) == 0 && kwv_call_ok(1, 1, 0, 1, 0, 0, 1, 1) == 0, "each of the three keys is needed");
    CHECK(kwv_call_ok(1, 1, 1, 0, 0, 0, 1, 1) == 0, "no trigger handle: no call");
    CHECK(kwv_call_ok(1, 1, 1, 1, 1, 0, 3, 1) == 0, "already called: no");
    CHECK(kwv_call_ok(1, 1, 1, 1, 0, 2, 3, 1) == 0 && kwv_call_ok(1, 1, 1, 1, 0, 6, 3, 1) == 0, "a vehicle is under way (the game's own): no call");
    CHECK(kwv_call_ok(1, 1, 1, 1, 0, 0, 0, 1) == 0, "nobody waits: no");
    CHECK(kwv_call_ok(1, 1, 1, 1, 0, 0, 2, 3) == 0 && kwv_call_ok(1, 1, 1, 1, 0, 0, 3, 3) == 1, "N = 3 needs three waiting carriers");
    CHECK(kwv_call_ok(1, 1, 1, 1, 0, 0, 1, 0) == 1, "N below 1 counts as 1");

    printf("klwaitvan_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
