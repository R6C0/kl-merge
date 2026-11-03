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
    CHECK(kpq_should_queue(1, 0x1f, 0, 0) == 1, "the scoreboard: queued too (review 11-02)");
    CHECK(kpq_should_queue(1, 0x16, 0, 0) == 0 && kpq_should_queue(1, 0x19, 0, 0) == 0 && kpq_should_queue(1, 0x23, 0, 0) == 0, "only states 0x1f / 0x20");
    CHECK(kpq_should_queue(1, 0x20, 0, 1) == 0, "same key already queued: not queued twice");
    CHECK(kpq_cancels(1, 0x20, 0, 1, 1) == 1, "second press of the same key cancels");
    CHECK(kpq_cancels(1, 0x20, 0, 1, 0) == 0 && kpq_cancels(1, 0x20, 0, 0, 0) == 0, "an old early press or nothing pending is not cancelled here");
    CHECK(kpq_cancels(0, 0x20, 0, 1, 1) == 0 && kpq_cancels(1, 0x20, 2, 1, 1) == 0 && kpq_cancels(1, 0x19, 0, 1, 1) == 0, "off / list open / wrong state: no cancel");
    CHECK(kpq_cancels(1, 0x1f, 0, 1, 1) == 1, "a second press on the scoreboard cancels");

    /* the hold of a queued press */
    CHECK(kpq_age(1000u, 1000u | 1u) == 0u && kpq_age(1016u, 1001u) == 15u && kpq_age(5u, 0xfffffff1u) == 20u, "kpq_age: a stamp of now | 1 in the same ms is 0 (pq2), tick wrap");
    CHECK(kpq_step(1, 0, 0x1f, 0, 0, kpq_age(1000u, 1000u | 1u)) == KPQ_WAIT && kpq_step(0, 1, 0x20, 2, 0, kpq_age(1000u, 1000u | 1u)) == KPQ_WAIT,
          "the tick right after the press (same ms): queued and early presses both wait (they lapsed in pq2)");
    CHECK(kpq_step(1, 1, 0x20, 0, 0, 0) == KPQ_WAIT, "fresh: wait");
    CHECK(kpq_step(1, 1, 0x20, 0, 0, 20000) == KPQ_WAIT, "20 s on, list still closed: still waits (the old hold lapsed at 3 s)");
    CHECK(kpq_step(1, 1, 0x20, 0, 0, 60000) == KPQ_WAIT && kpq_step(1, 1, 0x20, 0, 0, 60001) == KPQ_LAPSE, "the cap is 60 s");
    CHECK(kpq_step(1, 1, 0x20, 2, 0, 100) == KPQ_WAIT, "list open, selector not wrapped yet: wait (the mode-2 check is deferred to now)");
    CHECK(kpq_step(1, 1, 0x20, 2, 1, 100) == KPQ_APPLY, "list open and selector wrapped: the page shows");
    CHECK(kpq_step(1, 1, 0x20, 2, 1, 29000) == KPQ_APPLY, "after a long wait the list opens: still applied");
    CHECK(kpq_step(1, 1, 0x20, 2, 0, 61000) == KPQ_LAPSE, "list open but the selector never wrapped before the cap");
    CHECK(kpq_step(1, 1, 0x23, 0, 0, 100) == KPQ_LAPSE && kpq_step(1, 1, 0x19, 2, 1, 100) == KPQ_LAPSE , "the state left 0x20: dropped");
    CHECK(kpq_step(1, 0, 0x1f, 0, 0, 0) == KPQ_WAIT && kpq_step(1, 0, 0x1f, 0, 0, 59000) == KPQ_WAIT, "queued on the scoreboard: waits with the shop gate shut");
    CHECK(kpq_step(1, 0, 0x1f, 0, 0, 60001) == KPQ_LAPSE, "scoreboard: the cap");
    CHECK(kpq_step(1, 1, 0x20, 2, 1, 8000) == KPQ_APPLY, "scoreboard press, then 0x20 and the list opens: applied");
    CHECK(kpq_step(0, 0, 0x1f, 2, 1, 10) == KPQ_LAPSE, "old press on the scoreboard: lapses (old rules)");
    CHECK(kpq_step(1, 0, 0x20, 2, 1, 100) == KPQ_WAIT, "the shop gate reads shut on 0x20 (stale 0x1f hpre, pq1 DM06 11-03): waits, never applies");
    CHECK(kpq_step(1, 0, 0x20, 0, 0, 5) == KPQ_WAIT && kpq_step(1, 1, 0x20, 2, 1, 5500) == KPQ_APPLY, "the 0x1f -> 0x20 edge with the gate stale: kept, applied once open");
    CHECK(kpq_step(1, 0, 0x20, 2, 1, 60001) == KPQ_LAPSE && kpq_step(1, 0, 0x23, 0, 0, 10) == KPQ_LAPSE, "gate shut: the cap and the state change still drop it");
    CHECK(kpq_step(1, 1, 0x20, 1, 1, 100) == KPQ_WAIT, "list mode 1 (category) is not the weapon list: wait");

    /* PageQueue=0: queued 0 is exactly the old rules */
    CHECK(kpq_step(0, 1, 0x20, 2, 0, 0) == KPQ_WAIT && kpq_step(0, 1, 0x20, 2, 1, 0) == KPQ_APPLY, "old: list open, wait for the selector, apply");
    CHECK(kpq_step(0, 1, 0x20, 2, 0, 3000) == KPQ_WAIT && kpq_step(0, 1, 0x20, 2, 0, 3001) == KPQ_LAPSE, "old: lapses after 3 s");
    CHECK(kpq_step(0, 1, 0x20, 0, 1, 10) == KPQ_LAPSE, "old: the list closed = lapse (mode must be 2 all the time)");
    CHECK(kpq_step(0, 0, 0x16, 2, 1, 10) == KPQ_LAPSE && kpq_step(0, 1, 0x16, 2, 1, 10) == KPQ_APPLY, "old: no state test (the first shop)");

    /* AutoOpen */
    CHECK(kpq_autoopen_due(1, 1, 1, 0x20, 0, 800, 0, 0) == 1 && kpq_autoopen_due(1, 1, 1, 0x20, 1, 5000, 0, 0) == 1, "settled 0x20, list closed, queued: send");
    CHECK(kpq_autoopen_due(0, 1, 1, 0x20, 0, 5000, 0, 0) == 0, "AutoOpen=0: never");
    CHECK(kpq_autoopen_due(1, 0, 1, 0x20, 0, 5000, 0, 0) == 0, "AutoOpen alone (PageQueue=0): nothing");
    CHECK(kpq_autoopen_due(1, 1, 0, 0x20, 0, 5000, 0, 0) == 0, "nothing queued / lapsed / cancelled / old early press: no send");
    CHECK(kpq_autoopen_due(1, 1, 1, 0x20, 0, 799, 0, 0) == 0, "page up < 800 ms: wait");
    CHECK(kpq_autoopen_due(1, 1, 1, 0x20, 2, 5000, 0, 0) == 0, "list open: no send");
    CHECK(kpq_autoopen_due(1, 1, 1, 0x1f, 0, 5000, 0, 0) == 0 && kpq_autoopen_due(1, 1, 1, 0x19, 0, 5000, 0, 0) == 0 && kpq_autoopen_due(1, 1, 1, 0x23, 0, 5000, 0, 0) == 0 && kpq_autoopen_due(1, 1, 1, 0x24, 0, 5000, 0, 0) == 0, "only state 0x20");
    CHECK(kpq_autoopen_due(1, 1, 1, 0x20, 0, 5000, 1, 1499) == 0 && kpq_autoopen_due(1, 1, 1, 0x20, 0, 5000, 1, 1500) == 1, "retry after 1500 ms");
    CHECK(kpq_autoopen_due(1, 1, 1, 0x20, 0, 5000, 2, 1500) == 1 && kpq_autoopen_due(1, 1, 1, 0x20, 0, 5000, 3, 9999) == 0, "at most 3 sends");
    CHECK(kpq_ready_name_ok("MercsFAStatusReadyHeistStatus") && kpq_ready_name_ok("MercsFAStatusReadyHeistLBStatus") && kpq_ready_name_ok("MercsFAStatusReadyFAStatus") && kpq_ready_name_ok("MercsFAStatusReadyFAStatusTeam"), "the four page elements");
    CHECK(!kpq_ready_name_ok("MercsFAStatusReadyHeistStatus_EndGame") && !kpq_ready_name_ok("MercsFAStatusReadyHeistLBStatus_EndGame") && !kpq_ready_name_ok("MercsFAStatusReadyFAStatus_Endgame") && !kpq_ready_name_ok("MercsFAStatusReadyFAStatus_Team_Endgame"), "game over variants refused");
    CHECK(!kpq_ready_name_ok(0) && !kpq_ready_name_ok("") && !kpq_ready_name_ok("MercsFAStatusReadyFAStatu"), "null / empty / prefix refused");

    /* hint every shop */
    CHECK(kpq_hint_done_after_close(0, 1) == 1 && kpq_hint_done_after_close(0, 0) == 0, "off: once per session (done stays)");
    CHECK(kpq_hint_done_after_close(1, 1) == 0 && kpq_hint_done_after_close(1, 0) == 0, "on: re-armed when the shop closes");

    /* the board line */
    CHECK(kpq_board_hint(t, sizeof t, 0, "F2", "F3", "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F2] MORE PAGES  [F3] HEISTERS"), "'%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, 0, "", "F3", "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F3] HEISTERS  [F6] PAGE II"), "cycle key off: hire + page II: '%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, 0, "F2", "", "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F2] MORE PAGES"), "'%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, 0, 0, 0, "F6") == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F6] PAGE II"), "page II alone: '%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, 0, "End", "num1", 0) == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [END] MORE PAGES  [NUM1] HEISTERS"), "key names upper-cased: '%s'", t);
    CHECK(kpq_board_hint(t, sizeof t, 1, "F2", "F3", 0) == 1 && !strcmp(t, "PRESS NOW: [F2] MORE PAGES  [F3] HEISTERS"), "PageQueue on: '%s'", t);
    strcpy(t, "junk"); CHECK(kpq_board_hint(t, sizeof t, 0, "", 0, "") == 0 && t[0] == 0, "no page feature on: no line, buffer emptied");
    CHECK(kpq_board_hint(t, 40, 0, "F2", "F3", 0) == 1 && !strcmp(t, "NEXT: BUY WEAPONS, THEN [F2] MORE PAGES") && strlen(t) < 40, "cut at a whole entry: '%s'", t);
    CHECK(kpq_board_hint(t, 20, 0, "F2", "F3", 0) == 0 && t[0] == 0, "too small for the first entry: nothing");
    CHECK(kpq_board_hint(0, 96, 0, "F2", 0, 0) == 0 && kpq_board_hint(t, 4, 0, "F2", 0, 0) == 0, "bad buffer");
    CHECK(strlen("NEXT: BUY WEAPONS, THEN [PAGEUP] MORE PAGES  [NUM1] HEISTERS") < 96, "the longest realistic line fits the 96-byte buffer klhud_board2.c uses");

    /* AutoOpenSteps */
    CHECK(kpq_top_kind("FABuyWeaponsNew") == KPQ_TOP_NEW && kpq_top_kind("FABuyWeaponsNewCategory") == KPQ_TOP_CAT && kpq_top_kind("FABuyWeaponsNewWeapon") == KPQ_TOP_WPN, "window names");
    CHECK(kpq_top_kind("FABuyWeaponsNewX") == KPQ_TOP_OTHER && kpq_top_kind("FAStatus") == KPQ_TOP_OTHER && kpq_top_kind("") == KPQ_TOP_OTHER && kpq_top_kind(0) == KPQ_TOP_OTHER, "other names");
    CHECK(kpq_aostep(0, KPQ_TOP_OTHER, 0, -6, -4, 0, 1000, 5000) == KPQ_AS_WAIT, "step 0: Buy Weapons not up yet: wait");
    CHECK(kpq_aostep(0, KPQ_TOP_NEW, 0, -6, -4, 0, 1300, 100) == KPQ_AS_WAIT, "step 0: just on top: settle");
    CHECK(kpq_aostep(0, KPQ_TOP_NEW, 0, -6, -4, 1, 1600, 400) == KPQ_AS_WAIT, "step 0: window system busy: wait");
    CHECK(kpq_aostep(0, KPQ_TOP_NEW, 0, -5, -4, 0, 1600, 400) == KPQ_AS_WAIT, "step 0: Secondary focused: never step");
    CHECK(kpq_aostep(0, KPQ_TOP_NEW, 0, -6, -4, 0, 1600, 400) == KPQ_AS_OPENCAT, "step 0: open Category");
    CHECK(kpq_aostep(0, KPQ_TOP_CAT, 1, -6, -4, 0, 1600, 400) == KPQ_AS_ABORT, "step 0: the player walked on: abort");
    CHECK(kpq_aostep(0, KPQ_TOP_OTHER, 0, -6, -4, 0, 5001, 0) == KPQ_AS_ABORT, "step 0: timeout");
    CHECK(kpq_aostep(1, KPQ_TOP_NEW, 0, -6, -4, 1, 50, 0) == KPQ_AS_WAIT, "step 1: request queued: wait");
    CHECK(kpq_aostep(1, KPQ_TOP_CAT, 1, -6, -4, 0, 400, 100) == KPQ_AS_WAIT, "step 1: settle");
    CHECK(kpq_aostep(1, KPQ_TOP_CAT, 0, -6, -4, 0, 400, 400) == KPQ_AS_WAIT, "step 1: mode not 1 yet");
    CHECK(kpq_aostep(1, KPQ_TOP_CAT, 1, -6, -4, 0, 400, 400) == KPQ_AS_OPENWPN, "step 1: open Weapon");
    CHECK(kpq_aostep(1, KPQ_TOP_CAT, 1, -6, -6, 0, 400, 400) == KPQ_AS_ABORT, "step 1: category rewritten: abort");
    CHECK(kpq_aostep(1, KPQ_TOP_OTHER, 0, -6, -4, 0, 400, 400) == KPQ_AS_ABORT, "step 1: shop closed: abort");
    CHECK(kpq_aostep(1, KPQ_TOP_CAT, 1, -6, -4, 1, 2501, 400) == KPQ_AS_ABORT, "step 1: timeout");
    CHECK(kpq_aostep(2, KPQ_TOP_CAT, 1, -6, -4, 1, 100, 400) == KPQ_AS_WAIT && kpq_aostep(2, KPQ_TOP_WPN, 1, -6, -4, 0, 100, 10) == KPQ_AS_WAIT, "step 2: waiting for mode 2");
    CHECK(kpq_aostep(2, KPQ_TOP_WPN, 2, -6, -4, 0, 100, 10) == KPQ_AS_DONE && kpq_aostep(0, KPQ_TOP_WPN, 2, -6, -4, 0, 100, 10) == KPQ_AS_DONE, "mode 2: done");
    CHECK(kpq_aostep(2, KPQ_TOP_OTHER, 0, -6, -4, 0, 100, 10) == KPQ_AS_ABORT && kpq_aostep(2, KPQ_TOP_WPN, 1, -6, -4, 0, 2501, 10) == KPQ_AS_ABORT, "step 2: closed / timeout");
    CHECK(kpq_aostep(3, KPQ_TOP_NEW, 0, -6, -4, 0, 0, 999) == KPQ_AS_ABORT, "unknown step");

    printf("klpagequeue_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
