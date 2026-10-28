/* kldoorclose_test.c - OFF-GAME check of kldoorclose_logic.h (DoorCloseMs: open detection, timer, busy postpone, stale give-up, per-proxy slots).
 *   cl /nologo /W4 kldoorclose_test.c      or      tools/run_harness_linux.sh kldoorclose_test */
#include <windows.h>
#include <stdio.h>
#include "kldoorclose_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    struct kldc_p t[KLDC_N]; int i, f;
    memset(t, 0, sizeof t);
    /* open detection: the handler wrote the proxy's own first/last (0/75) and a new start */
    CHECK(kldc_is_open(0, 5000, 1, 0, 75, 0, 75));
    CHECK(!kldc_is_open(5000, 5000, 1, 0, 75, 0, 75));        /* same start as seen: not a new open */
    CHECK(!kldc_is_open(0, 0, 1, 0, 75, 0, 75));              /* never started */
    CHECK(!kldc_is_open(0, 5000, 0, 0, 75, 0, 75));           /* leaf not playing */
    CHECK(!kldc_is_open(0, 5000, 1, 75, 160, 0, 75));         /* our own close (75/160) is not an open */
    CHECK(!kldc_is_open(0, 5000, 1, 0, 0, 0, 0));             /* proxy with no last: nothing handler-written */
    CHECK(!kldc_is_open(0, 5000, 1, 0, 75, 0, 80));           /* ints differ from the proxy's fields (at-load play, not the handler) */
    /* open tick from the game clock: found late, still exact */
    CHECK(kldc_open_at(20000, 9000, 4000) == 15000);
    CHECK(kldc_open_at(3, 100, 90) == (unsigned long)(3ul - 10ul));   /* tick wrap: unsigned difference */
    CHECK(kldc_open_at(10, 10, 10) == 10);
    CHECK(kldc_open_at(5, 105, 5) != 0);                      /* never 0 (0 = none) */
    /* timer */
    CHECK(kldc_step(1000, 1000, 12000, 0) == 0);
    CHECK(kldc_step(12999, 1000, 12000, 0) == 0);
    CHECK(kldc_step(13000, 1000, 12000, 0) == 1);             /* due */
    CHECK(kldc_step(13000, 1000, 12000, 1) == 3);             /* due, player at the car: postponed */
    CHECK(kldc_step(20000, 1000, 12000, 1) == 3);             /* still postponed */
    CHECK(kldc_step(20000, 1000, 12000, 0) == 1);             /* he left: closes */
    CHECK(kldc_step(1000 + 12000 + KLDC_STALE_MS, 1000, 12000, 0) == 1);       /* exactly at the limit: still ok */
    CHECK(kldc_step(1000 + 12000 + KLDC_STALE_MS + 1, 1000, 12000, 0) == 2);   /* stale: give up */
    CHECK(kldc_step(1000 + 12000 + KLDC_STALE_MS + 1, 1000, 12000, 1) == 2);   /* stale beats busy */
    CHECK(kldc_step(99999, 1000, 0, 0) == 0);                 /* DoorCloseMs 0 = off */
    CHECK(kldc_step(5, 0xfffffff0ul, 12000, 0) == 0);         /* wrap: 21 ms after the open */
    CHECK(kldc_step(12000 - 16 + 5, 0xfffffff0ul, 12000, 0) == 1);
    /* slots: per proxy, an existing one is found again, finished ones are reused, a full table says -1 */
    CHECK(kldc_slot(t, KLDC_N, 0x100) == 0);                  /* empty table: first free */
    t[0].me = 0x100; t[0].done = 0;
    CHECK(kldc_slot(t, KLDC_N, 0x100) == 0);
    CHECK(kldc_slot(t, KLDC_N, 0x200) == 1);
    t[1].me = 0x200; t[2].me = 0x300; t[3].me = 0x400;
    CHECK(kldc_slot(t, KLDC_N, 0x500) == -1);                 /* all four open, none done */
    t[2].done = 1;
    CHECK(kldc_slot(t, KLDC_N, 0x500) == 2);                  /* a finished slot is reused */
    CHECK(kldc_slot(t, KLDC_N, 0x400) == 3);                  /* but an existing proxy keeps its own slot */
    CHECK(kldc_slot(t, KLDC_N, 0x300) == 2);
    /* two proxies close independently: one close each (done is per slot) */
    memset(t, 0, sizeof t);
    t[0].me = 0x100; t[0].at = 1000; t[1].me = 0x200; t[1].at = 1500;
    { int closed = 0; unsigned long now;
      for (now = 1000; now < 30000; now += 10)
          for (i = 0; i < 2; i++) {
              if (t[i].done) continue;
              f = kldc_step(now, t[i].at, 12000, 0);
              if (f == 1) { t[i].done = 1; closed++; }
          }
      CHECK(closed == 2); }
    printf("kldoorclose_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
