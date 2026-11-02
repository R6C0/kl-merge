/* klpagequeue_test.c - off-game harness for klpagequeue_logic.h ([ShopPage] PageQueue hold / expiry, HintEveryShop re-arm, [HUD] ScoreboardNextHint text). No windows.h.
   Proves the decisions, NOT that the round-over page or the board behave so in the game (NOT RUN IN THE GAME).
   Build: cl /nologo /W3 klpagequeue_test.c /Fe:klpagequeue_test.exe     Run: klpagequeue_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include "klpagequeue_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    char t[96];

    /* queue or not */
    CHECK(kpq_should_queue(1, 0x20, 0, 0) == 1 && kpq_should_queue(1, 0x20, 1, 0) == 1, "queued on the round-over page with the list closed (mode 0 / 1)");
    CHECK(kpq_should_queue(0, 0x20, 0, 0) == 0, "PageQueue=0: never (the old behaviour)");
    CHECK(kpq_should_queue(1, 0x20, 2, 0) == 0, "the list is open: the key acts at once, nothing to queue");
    CHECK(kpq_should_queue(1, 0x1f, 0, 0) == 0 && kpq_should_queue(1, 0x16, 0, 0) == 0 && kpq_should_queue(1, 0x19, 0, 0) == 0, "only state 0x20");
    CHECK(kpq_should_queue(1, 0x20, 0, 1) == 0, "same key already queued: not queued twice");
    CHECK(kpq_cancels(1, 0x20, 0, 1, 1) == 1, "second press of the same key cancels");
    CHECK(kpq_cancels(1, 0x20, 0, 1, 0) == 0 && kpq_cancels(1, 0x20, 0, 0, 0) == 0, "an old early press or nothing pending is not cancelled here");
    CHECK(kpq_cancels(0, 0x20, 0, 1, 1) == 0 && kpq_cancels(1, 0x20, 2, 1, 1) == 0 && kpq_cancels(1, 0x1f, 0, 1, 1) == 0, "off / list open / wrong state: no cancel");

    /* the hold of a queued press */
    CHECK(kpq_step(1, 1, 0x20, 0, 0, 0) == KPQ_WAIT, "fresh: wait");
    CHECK(kpq_step(1, 1, 0x20, 0, 0, 20000) == KPQ_WAIT, "20 s on, list still closed: still waits (the old hold lapsed at 3 s)");
    CHECK(kpq_step(1, 1, 0x20, 0, 0, 35000) == KPQ_WAIT && kpq_step(1, 1, 0x20, 0, 0, 35001) == KPQ_LAPSE, "the cap is 35 s");
    CHECK(kpq_step(1, 1, 0x20, 2, 0, 100) == KPQ_WAIT, "list open, selector not wrapped yet: wait (the mode-2 check is deferred to now)");
    CHECK(kpq_step(1, 1, 0x20, 2, 1, 100) == KPQ_APPLY, "list open and selector wrapped: the page shows");
    CHECK(kpq_step(1, 1, 0x20, 2, 1, 29000) == KPQ_APPLY, "after a long wait the list opens: still applied");
    CHECK(kpq_step(1, 1, 0x20, 2, 0, 36000) == KPQ_LAPSE, "list open but the selector never wrapped before the cap");
    CHECK(kpq_step(1, 1, 0x23, 0, 0, 100) == KPQ_LAPSE && kpq_step(1, 1, 0x19, 2, 1, 100) == KPQ_LAPSE && kpq_step(1, 1, 0x1f, 0, 0, 0) == KPQ_LAPSE, "the state left 0x20: dropped");
    CHECK(kpq_step(1, 0, 0x20, 2, 1, 100) == KPQ_LAPSE, "the shop gate closed: dropped");
    CHECK(kpq_step(1, 1, 0x20, 1, 1, 100) == KPQ_WAIT, "list mode 1 (category) is not the weapon list: wait");

    /* PageQueue=0: queued 0 is exactly the old rules */
    CHECK(kpq_step(0, 1, 0x20, 2, 0, 0) == KPQ_WAIT && kpq_step(0, 1, 0x20, 2, 1, 0) == KPQ_APPLY, "old: list open, wait for the selector, apply");
    CHECK(kpq_step(0, 1, 0x20, 2, 0, 3000) == KPQ_WAIT && kpq_step(0, 1, 0x20, 2, 0, 3001) == KPQ_LAPSE, "old: lapses after 3 s");
    CHECK(kpq_step(0, 1, 0x20, 0, 1, 10) == KPQ_LAPSE, "old: the list closed = lapse (mode must be 2 all the time)");
    CHECK(kpq_step(0, 0, 0x16, 2, 1, 10) == KPQ_LAPSE && kpq_step(0, 1, 0x16, 2, 1, 10) == KPQ_APPLY, "old: no state test (the first shop)");

    /* hint every shop */
    CHECK(kpq_hint_done_after_close(0, 1) == 1 && kpq_hint_done_after_close(0, 0) == 0, "off: once per session (done stays)");
    CHECK(kpq_hint_done_after_close(1, 1) == 0 && kpq_hint_done_after_close(1, 0) == 0, "on: re-armed when the shop closes");

    /* the board line */
    CHECK(kpq_board_hint(t, sizeof t, "F2", "F3", "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F2] MORE PAGES  [F3] HEISTERS"), "'%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, "", "F3", "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F3] HEISTERS  [F6] PAGE II"), "cycle key off: hire + page II: '%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, "F2", "", "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F2] MORE PAGES"), "'%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, 0, 0, "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F6] PAGE II"), "page II alone: '%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, "End", "num1", 0) == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [END] MORE PAGES  [NUM1] HEISTERS"), "key names upper-cased: '%s'", t);
    strcpy(t, "junk"); CHECK(kpq_board_hint(t, sizeof t, "", 0, "") == 0 && t[0] == 0, "no page feature on: no line, buffer emptied");
    CHECK(kpq_board_hint(t, 40, "F2", "F3", 0) == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F2] MORE PAGES") && strlen(t) < 40, "cut at a whole entry: '%s'", t);
    CHECK(kpq_board_hint(t, 20, "F2", "F3", 0) == 0 && t[0] == 0, "too small for the first entry: nothing");
    CHECK(kpq_board_hint(0, 96, "F2", 0, 0) == 0 && kpq_board_hint(t, 4, "F2", 0, 0) == 0, "bad buffer");
    CHECK(strlen("NEXT: BUY WEAPONS, THEN [PAGEUP] MORE PAGES  [NUM1] HEISTERS") < 96, "the longest realistic line fits the 96-byte buffer klhud_board2.c uses");

    printf("klpagequeue_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
