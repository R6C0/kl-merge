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
    /* remote slots: only online, only with the key, never the local selectors, only 0..27 */
    CHECK(kldc_remote_slot(3, 0, 1, 1, 1));
    CHECK(!kldc_remote_slot(0, 0, 1, 1, 1));
    CHECK(!kldc_remote_slot(1, 0, 1, 1, 1));
    CHECK(!kldc_remote_slot(3, 0, 1, 0, 1));                  /* offline: never */
    CHECK(!kldc_remote_slot(3, 0, 1, 1, 0));                  /* key off: never */
    CHECK(!kldc_remote_slot(28, 0, 1, 1, 1) && !kldc_remote_slot(-1, 0, 1, 1, 1));
    CHECK(kldc_remote_slot(2, 0xff, 0xff, 1, 1));             /* no local player: all slots */
    /* slots: per proxy, an existing one is found again, finished ones are reused, a full table says -1 */
    CHECK(kldc_slot(t, 4, 0x100) == 0);                  /* empty table: first free */
    t[0].me = 0x100; t[0].done = 0;
    CHECK(kldc_slot(t, 4, 0x100) == 0);
    CHECK(kldc_slot(t, 4, 0x200) == 1);
    t[1].me = 0x200; t[2].me = 0x300; t[3].me = 0x400;
    CHECK(kldc_slot(t, 4, 0x500) == -1);                 /* all four open, none done */
    t[2].done = 1;
    CHECK(kldc_slot(t, 4, 0x500) == 2);                  /* a finished slot is reused */
    CHECK(kldc_slot(t, 4, 0x400) == 3);                  /* but an existing proxy keeps its own slot */
    CHECK(kldc_slot(t, 4, 0x300) == 2);
    /* newly found proxies never evict a followed (done) slot */
    t[3].done = 1;
    CHECK(kldc_slot_free(t, 4, 0x600) == -1);
    CHECK(kldc_slot_free(t, 4, 0x400) == 3);
    t[1].me = 0;
    CHECK(kldc_slot_free(t, 4, 0x600) == 1);
    /* unusable clock: open taken as now */
    CHECK(kldc_open_at(20000, 0, 4000) == 20000);
    CHECK(kldc_open_at(20000, 3000, 4000) == 20000);
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
    /* remote hold: a departed peer (frozen feet) stops holding after still_ms; a walking one holds; the max cap bounds jitter */
    { struct kldc_r r; float f[3] = { 100, 200, 0 }; unsigned long now; int held = 0, ok;
      memset(&r, 0, sizeof r);
      CHECK(kldc_rhold(&r, 1000, f, 1, 6000, 30000));              /* first look in the box: fresh */
      CHECK(kldc_rhold(&r, 6999, f, 1, 6000, 30000));              /* 5999 ms still: holds */
      CHECK(!kldc_rhold(&r, 7000, f, 1, 6000, 30000));             /* 6000 ms still: released (quit peer) */
      CHECK(!kldc_rhold(&r, 20000, f, 1, 6000, 30000));            /* stays released */
      f[0] += 40; CHECK(kldc_rhold(&r, 21000, f, 1, 6000, 30000)); /* he moves (stay still under max_ms): holds again */
      f[0] += 0.2f; CHECK(kldc_rhold(&r, 27500, f, 1, 6000, 30000) == 0);   /* sub-epsilon jitter is not movement */
      f[0] += 40; CHECK(!kldc_rhold(&r, 31000, f, 1, 6000, 30000)); /* moving, but 30000 ms in one stay: released until he leaves the box */
      CHECK(!kldc_rhold(&r, 99100, f, 0, 6000, 30000));            /* left the box: no hold, since reset */
      memset(&r, 0, sizeof r); ok = 1;
      for (now = 1000; now < 100000; now += 100) { f[1] += 5; held = kldc_rhold(&r, now, f, 1, 6000, 30000); if (now < 31000 && !held) ok = 0; if (now >= 31000 && held) ok = 0; }
      CHECK(ok);                                                   /* a moving entry holds exactly up to max_ms */
      f[1] += 5; CHECK(!kldc_rhold(&r, 100000, f, 1, 6000, 30000));
      CHECK(!kldc_rhold(&r, 100100, f, 0, 6000, 30000));
      f[1] += 5; CHECK(kldc_rhold(&r, 100200, f, 1, 6000, 30000)); /* re-armed after leaving the box */
      memset(&r, 0, sizeof r);
      CHECK(kldc_rhold(&r, 1000, f, 1, 0, 0) && kldc_rhold(&r, 900000, f, 1, 0, 0));   /* 0 = no limit */
      memset(&r, 0, sizeof r);
      CHECK(kldc_rhold(&r, 0xfffffff0ul, f, 1, 6000, 30000) && kldc_rhold(&r, 0xfffffff0ul + 5000, f, 1, 6000, 30000));   /* tick wrap */
    }
    printf("kldoorclose_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
