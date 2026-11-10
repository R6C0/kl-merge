/* klpagequeue_test.c - off-game harness for klpagequeue_logic.h ([ShopPage] PageQueue hold / expiry, HintEveryShop re-arm, [HUD] ScoreboardNextHint text). No windows.h.
   Proves the decisions, NOT that the round-over page or the board behave so in the game (NOT RUN IN THE GAME).
   Build: cl /nologo /W3 klpagequeue_test.c /Fe:klpagequeue_test.exe     Run: klpagequeue_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include "klpagequeue_logic.h"
#include "klmodestab_logic.h"
#include "klfit_logic.h"

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

    /* InShopSteps */
    CHECK(kpq_inshop_start(KPQ_TOP_NEW, 0) == 0 && kpq_inshop_start(KPQ_TOP_CAT, 1) == 1, "in the shop: start at Buy Weapons / Category");
    CHECK(kpq_inshop_start(KPQ_TOP_OTHER, 0) == -1 && kpq_inshop_start(KPQ_TOP_WPN, 2) == -1 && kpq_inshop_start(KPQ_TOP_CAT, 0) == -1 && kpq_inshop_start(KPQ_TOP_NEW, 1) == -1, "not in the shop / list open / mode lags: send path");
    CHECK(kpq_aostep(1, KPQ_TOP_CAT, 1, -6, -4, 0, 400, 400) == KPQ_AS_OPENWPN && kpq_aostep(1, KPQ_TOP_CAT, 1, -6, -2, 0, 400, 400) == KPQ_AS_ABORT, "start at 1: pistols opens the list, another category stops");


    /* ===== [ShopPage] PageIntent family (2026-11-07) ===== */
    /* regression guard: with every new flag at 0 the new functions give exactly today's answers */
    {
        int st, mode, top, step, slot, cat, busy, sent, seen, cycles, a, b;
        unsigned int age, tms;
        const int sts[] = { 0x16, 0x18, 0x19, 0x1f, 0x20, 0x23 }, cats[] = { -6, -4, -3, -2, -1, 0 }, tops[] = { KPQ_TOP_OTHER, KPQ_TOP_NEW, KPQ_TOP_CAT, KPQ_TOP_WPN };
        const unsigned int ages[] = { 0u, 299u, 400u, 2501u, 5001u, 70000u };
        int ok = 1;
        for (step = 0; step < 4 && ok; step++) for (top = 0; top < 4; top++) for (mode = 0; mode < 3; mode++) for (slot = -6; slot <= -5; slot++) for (cat = 0; cat < 6; cat++) for (busy = 0; busy < 2; busy++)
            for (a = 0; a < 6; a++) for (b = 0; b < 3; b++) {
                age = ages[a]; tms = ages[b + 1];
                if (kpq_aostep_x(0, step, tops[top], mode, slot, cats[cat], busy, age, tms) != kpq_aostep(step, tops[top], mode, slot, cats[cat], busy, age, tms)) ok = 0;
            }
        CHECK(ok, "IntentAnyCategory off: kpq_aostep_x(0, ...) equals kpq_aostep on the whole grid");
        for (sent = 0; sent < 2; sent++) for (seen = 0; seen < 2; seen++) CHECK(kpq_ao_hold(0, sent, seen) == (sent || seen), "PageIntent off: the old 'sent or seen' return (sent %d seen %d)", sent, seen);
        ok = 1;
        for (sent = 0; sent < 2; sent++) for (top = 0; top < 4; top++) for (mode = 0; mode < 3; mode++) for (a = 0; a < 6; a++) for (cycles = 0; cycles < 5; cycles++)
            if (kpq_intent_resend(0, sent, tops[top], mode, ages[a], cycles, 0)) ok = 0;
        CHECK(ok, "PageIntent off: never a re-armed send");
        ok = 1;
        for (st = 0; st < 6; st++) for (mode = 0; mode < 3; mode++) for (sent = 0; sent < 2; sent++) for (a = 0; a < 6; a++) {
            if (kpq_debounced(0, sts[st], mode, 1, 1, ages[a])) ok = 0;
            if (kpq_hint_wanted(0, sts[st])) ok = 0;
        }
        CHECK(ok, "QueueDebounce / IntentFallbackHint off: never ignore a repeat, never a hint (kpq_cancels is the old rule, untouched)");
        CHECK(kpq_cancels(1, 0x20, 0, 1, 1) == 1 && kpq_should_queue(1, 0x16, 0, 0) == 0 && kpq_should_queue(1, 0x18, 0, 0) == 0, "kpq_cancels / kpq_should_queue unchanged (IntentPreRound is not implemented: 0x16 / 0x18 never queue)");
    }
    /* PageIntent: the list seen earlier no longer blocks; a send in flight still does */
    CHECK(kpq_ao_hold(1, 0, 1) == 0 && kpq_ao_hold(1, 0, 0) == 0 && kpq_ao_hold(1, 1, 0) == 1 && kpq_ao_hold(1, 1, 1) == 1, "PageIntent: only a send in flight holds (shop opened, closed, press again: Ready is re-sent)");
    CHECK(kpq_autoopen_due(1, 1, 1, 0x20, 0, 5000, 0, 0) == 1, "...and the send itself is due again (list closed, queued, settled)");
    /* PageIntent: the send worked but no FABuyWeaponsNew window shows within 5 s: re-armed, max 3 cycles */
    CHECK(kpq_intent_resend(1, 1, KPQ_TOP_OTHER, 0, 5000, 0, 0) == 0 && kpq_intent_resend(1, 1, KPQ_TOP_OTHER, 0, 5001, 0, 0) == 1, "no shop window: re-armed after 5 s, not before");
    CHECK(kpq_intent_resend(1, 1, KPQ_TOP_OTHER, 0, 9000, 2, 0) == 1 && kpq_intent_resend(1, 1, KPQ_TOP_OTHER, 0, 9000, 3, 0) == 0, "3 cycles at most");
    CHECK(kpq_intent_resend(1, 1, KPQ_TOP_NEW, 0, 9000, 0, 0) == 0 && kpq_intent_resend(1, 1, KPQ_TOP_CAT, 1, 9000, 0, 0) == 0 && kpq_intent_resend(1, 1, KPQ_TOP_OTHER, 2, 9000, 0, 0) == 0, "a shop window up, or the list open: no re-send");
    CHECK(kpq_intent_resend(1, 0, KPQ_TOP_OTHER, 0, 9000, 0, 0) == 0, "no send made yet: nothing to re-arm");
    CHECK(kpq_intent_resend(1, 1, KPQ_TOP_OTHER, 0, 9000, 0, 1) == 0 && kpq_intent_resend(0, 1, KPQ_TOP_OTHER, 0, 9000, 0, 1) == 0, "the shop came up after the send and the player backed out: no re-send without a new press");
    /* IntentAnyCategory: the step 1 abort at category -1 / -2 / -3 */
    CHECK(kpq_aostep_x(0, 1, KPQ_TOP_CAT, 1, -6, -1, 0, 400, 400) == KPQ_AS_ABORT && kpq_aostep_x(0, 1, KPQ_TOP_CAT, 1, -6, -2, 0, 400, 400) == KPQ_AS_ABORT && kpq_aostep_x(0, 1, KPQ_TOP_CAT, 1, -6, -3, 0, 400, 400) == KPQ_AS_ABORT, "any-category off: -1 / -2 / -3 abort (the 11-07 log)");
    CHECK(kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -1, 0, 400, 400) == KPQ_AS_OPENWPN && kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -2, 0, 400, 400) == KPQ_AS_OPENWPN &&
          kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -3, 0, 400, 400) == KPQ_AS_OPENWPN && kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -4, 0, 400, 400) == KPQ_AS_OPENWPN, "any-category on: -4..-1 open the Weapon window");
    CHECK(kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -6, 0, 400, 400) == KPQ_AS_ABORT && kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, 0, 0, 400, 400) == KPQ_AS_ABORT, "any-category on: a value outside -4..-1 (a rewritten category) still aborts");
    CHECK(kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -2, 0, 2501, 400) == KPQ_AS_ABORT && kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -2, 1, 400, 400) == KPQ_AS_WAIT && kpq_aostep_x(1, 1, KPQ_TOP_CAT, 1, -6, -2, 0, 400, 100) == KPQ_AS_WAIT, "any-category on: timeout / busy / settle rules stay");
    /* QueueDebounce */
    CHECK(kpq_debounced(1, 0x20, 0, 1, 1, 0) == 1 && kpq_debounced(1, 0x20, 0, 1, 1, 1999) == 1 && kpq_debounced(1, 0x20, 0, 1, 1, 2000) == 0, "a repeat inside 2 s is ignored, after it the cancel rule takes over");
    CHECK(kpq_debounced(1, 0x1f, 0, 1, 1, 100) == 1, "also on the scoreboard");
    CHECK(kpq_debounced(1, 0x20, 0, 0, 0, 100) == 0 && kpq_debounced(1, 0x20, 0, 1, 0, 100) == 0 && kpq_debounced(1, 0x20, 2, 1, 1, 100) == 0 && kpq_debounced(1, 0x19, 0, 1, 1, 100) == 0, "nothing queued / early press / list open / wrong state: not a debounce");
    CHECK(kpq_cancels(1, 0x20, 0, 1, 1) == 1 && kpq_debounced(1, 0x20, 0, 1, 1, 2500) == 0, "after the window a second press still cancels");
    /* IntentFallbackHint */
    CHECK(kpq_hint_wanted(1, 0x20) == 1 && kpq_hint_wanted(1, 0x1f) == 1 && kpq_hint_wanted(1, 0x23) == 0 && kpq_hint_wanted(1, 0x19) == 0, "hint only while Buy Weapons can still be pressed");
    CHECK(kpq_fallback_hint(t, sizeof t, "F3") == 1 && !strcmp(t, "PRESS BUY WEAPONS, THEN [F3]"), "'%s'", t);
    CHECK(kpq_fallback_hint(t, sizeof t, "ctrl+delete") == 1 && !strcmp(t, "PRESS BUY WEAPONS, THEN [CTRL+DELETE]"), "key name upper-cased: '%s'", t);
    strcpy(t, "junk"); CHECK(kpq_fallback_hint(t, sizeof t, "") == 0 && t[0] == 0 && kpq_fallback_hint(t, sizeof t, 0) == 0, "no key name: no hint, buffer emptied");
    CHECK(kpq_fallback_hint(t, 20, "F3") == 0 && kpq_fallback_hint(0, 96, "F3") == 0 && kpq_fallback_hint(t, 8, "F3") == 0, "buffer too small / bad");
    /* IntentLog */
    CHECK(kpq_reject_why(0, 1, 1) == KPQ_REJ_GATE && kpq_reject_why(0, 0, 0) == KPQ_REJ_GATE, "gate first");
    CHECK(kpq_reject_why(1, 0, 0) == KPQ_REJ_DEBOUNCE && kpq_reject_why(1, 1, 0) == KPQ_REJ_FOREGROUND && kpq_reject_why(1, 1, 1) == KPQ_REJ_NONE, "then debounce, then foreground, else none");
    CHECK(strcmp(kpq_reject_name(KPQ_REJ_GATE), "gate shut") == 0 && strcmp(kpq_reject_name(KPQ_REJ_NONE), "none") == 0, "reject names");
    CHECK(kpq_log_due(1000, 0, 2000) == 1 && kpq_log_due(2999, 1001, 2000) == 0 && kpq_log_due(3001, 1001, 2000) == 1, "log at most once per 2 s");
    /* the 60 s timeout is still a lapse, and with a reason the caller can name (the hold's cap) */
    CHECK(kpq_step(1, 1, 0x20, 0, 0, 60001) == KPQ_LAPSE, "60 s: the queued press lapses (kspg_fb_show then asks kpq_hint_wanted)");

    /* SHOPCYCLE 11-10: a cycle press starts from the page the caption names; stale hire / controls flags with the list closed do not count */
    {
        int av[5] = { 1, 0, 1, 1, 1 }, p, n, pos;   /* offline: stock, (no page II), hire, controls, modes = the owner's 'PAGE n/4' */
        CHECK(kpq_press_page(2, 0, 0, 0, 0) == 0 && kpq_press_page(2, 0, 0, 1, 0) == 2 && kpq_press_page(2, 1, 0, 1, 0) == 3 && kpq_press_page(2, 1, 1, 0, 0) == 4 && kpq_press_page(2, 0, 0, 0, 1) == 1, "list open: the page that is up");
        CHECK(kpq_press_page(0, 0, 0, 1, 0) == 0 && kpq_press_page(1, 1, 0, 0, 0) == 0 && kpq_press_page(0, 1, 1, 1, 0) == 0, "list closed (round-over page): stale hire / controls = stock");
        CHECK(kpq_press_page(0, 0, 0, 1, 1) == 1, "list closed, page II up: page II");
        /* owner log 20:02:23: hire left behind, press on the round-over page: next of stock is HIRE (2/4), never CONTROLS */
        CHECK(kmt_next(kpq_press_page(0, 0, 0, 1, 0), av) == 2, "stale hire, list closed: the press opens the page after stock (hire), not controls");
        CHECK(kmt_next(kpq_press_page(0, 1, 1, 0, 0), av) == 2, "stale bots-and-modes, list closed: hire, not stock / not the next of modes");
        /* the caption's PAGE n/N and 'next: X' against the step: from every page one press = exactly the page named, N presses = round trip */
        for (n = 0, p = 0; p < 5; p++) n += av[p];
        for (p = 0, pos = 0; p < 5; p++) if (av[p]) {
            char add[160]; int nx = kmt_next(p, av); pos++;
            kfit_pieces(add, sizeof add, 0, p, pos, n, "", "F2", nx, "", "");
            { char want[40], pg[24]; snprintf(want, sizeof want, "PAGE %d/%d", pos, n); snprintf(pg, sizeof pg, "next: %s", kfit_pname[nx]);
              CHECK(strstr(add, want) && strstr(add, pg), "page %d caption '%s'", p, add); }
        }
        { int c = 0, k; for (k = 0; k < n; k++) c = kmt_next(c, av); CHECK(c == 0, "n presses from stock = back on stock"); }
    }

    printf("klpagequeue_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
