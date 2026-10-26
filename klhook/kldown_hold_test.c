/* kldown_hold_test.c - off-game harness for kldown_hold.h (the [Down] MashHold meter / hold decision; kldown.c includes the same header).
   Replays a fall, a lie with different mashing speeds, a hitch, a held key, the time bound, a death, a second down. NOT the game: it proves the
   decision, not that the game takes the get-up press the hold lets through (re\down_online_built.md has the live bench for that).
   Build (x86, from a VS prompt):  cl /nologo /W3 kldown_hold_test.c /Fe:kldown_hold_test.exe     Run: kldown_hold_test.exe  (exit 0 = all pass) */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "kldown_hold.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

/* mash at `rate` presses a second for `secs` of lying, frames of 1/60 s; returns the seconds until the hold went (or -1) */
static float mash(struct kldh *h, float rate, float secs, DWORD *clock, float need, float decay, int *npress)
{
    float t = 0, dt = 1.0f / 60.0f, ph = 0; int key = 0, hold = 1, e, n = 0;
    while (t < secs) {
        float ph2 = ph + rate * dt;
        key = rate > 0 && ((int)(ph2 * 2) != (int)(ph * 2)) ? !key : key;      /* a press = a down edge, a release between */
        ph = ph2;
        *clock += 16; hold = kldh_step(h, 1, key, dt, 1.0f, decay, need, *clock, 0, 1, &e); n += e;
        t += dt;
        if (!hold) { if (npress) *npress = n; return t; }
    }
    if (npress) *npress = n;
    return -1.0f;
}

int main(void)
{
    struct kldh h; DWORD clk = 1000; int e, np = 0; float t; int i;
    memset(&h, 0, sizeof h);

    /* 1. up: nothing is held, nothing counts */
    CHECK(kldh_step(&h, 0, 1, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e) == 0 && e == 0 && h.meter == 0, "up must not hold");
    /* 2. falling: held, presses do not charge */
    for (i = 0; i < 30; i++) { clk += 16; CHECK(kldh_step(&h, 2, i & 1, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e) == 1 && e == 0, "a fall is held and counts no press"); }
    CHECK(h.meter == 0 && h.presses == 0, "the fall stored %.2f", h.meter);
    /* 3. lying, no presses: held for ever (no time bound) */
    for (i = 0; i < 600; i++) { clk += 16; if (!kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e)) { CHECK(0, "released with no press"); break; } }
    CHECK(h.latched == 0, "latched without presses");
    /* 4. mash 6 / s: let go in about 1.8 s */
    memset(&h, 0, sizeof h); clk = 5000;
    t = mash(&h, 6.0f, 10.0f, &clk, 8.0f, 1.5f, &np);
    CHECK(t > 1.2f && t < 2.6f, "6 presses a second: let go after %.2f s (wanted ~1.8)", t);
    CHECK(np >= 8 && np <= 14, "6 presses a second: %d presses counted", np);
    /* 5. after the latch the hold stays off while he lies (the stock press is coming), presses count no more */
    for (i = 0; i < 20; i++) { clk += 16; CHECK(kldh_step(&h, 1, i & 1, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e) == 0 && e == 0, "latched: hold must stay off"); }
    /* 6. the stock get-up starts (ds 3): not held, everything reset for the next down */
    CHECK(kldh_step(&h, 3, 1, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e) == 0 && !h.latched && h.meter == 0, "get-up (3) resets");
    CHECK(kldh_step(&h, 0, 0, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e) == 0, "up again");
    /* 7. mash 3 / s: about 5 s */
    memset(&h, 0, sizeof h); clk = 9000;
    t = mash(&h, 3.0f, 30.0f, &clk, 8.0f, 1.5f, &np);
    CHECK(t > 3.5f && t < 8.0f, "3 presses a second: let go after %.2f s (wanted ~5)", t);
    /* 8. mash 1 / s, under the decay: never */
    memset(&h, 0, sizeof h); clk = 20000;
    t = mash(&h, 1.0f, 40.0f, &clk, 8.0f, 1.5f, &np);
    CHECK(t < 0, "1 press a second must never fill the meter (let go at %.2f s)", t);
    /* 9. a held key counts once */
    memset(&h, 0, sizeof h); clk = 30000; kldh_step(&h, 1, 0, 0.016f, 1, 0, 8, clk, 0, 1, &e);
    for (i = 0; i < 200; i++) { clk += 16; kldh_step(&h, 1, 1, 0.016f, 1, 0, 8, clk, 0, 1, &e); }
    CHECK(h.presses == 1 && h.meter < 1.01f, "a held key: %d presses, meter %.2f", h.presses, h.meter);
    /* 10. a key already down when he lands does not count as a press until released and pressed again */
    memset(&h, 0, sizeof h); clk = 40000;
    for (i = 0; i < 10; i++) { clk += 16; kldh_step(&h, 2, 1, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e); }
    clk += 16; kldh_step(&h, 1, 1, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e);
    CHECK(h.presses == 0, "a key held through the landing counted (%d)", h.presses);
    /* 11. a hitch (dt 2 s) neither empties nor fills the meter by itself: clamped to 0.25 s */
    memset(&h, 0, sizeof h); clk = 50000;
    for (i = 0; i < 4; i++) { clk += 100; kldh_step(&h, 1, i & 1, 0.1f, 1, 1.5f, 8, clk, 0, 1, &e); kldh_step(&h, 1, 0, 0.1f, 1, 1.5f, 8, clk, 0, 1, &e); }
    { float m0 = h.meter; clk += 2000; kldh_step(&h, 1, 0, 2.0f, 1, 1.5f, 8, clk, 0, 1, &e); CHECK(m0 - h.meter < 0.40f && m0 - h.meter > 0.30f, "hitch took %.2f of the meter (clamp: 0.375)", m0 - h.meter); }
    /* 12. the time bound lets go after maxlie even with no press, and says so */
    memset(&h, 0, sizeof h); clk = 60000;
    for (i = 0; i < 4000; i++) { clk += 16; if (!kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, clk, 25000, 1, &e)) break; }
    CHECK(h.latched && h.timeout && (clk - h.t_lie) >= 25000 && (clk - h.t_lie) < 25100, "time bound: latched %d timeout %d after %lu ms", h.latched, h.timeout, (unsigned long)(clk - h.t_lie));
    /* 13. death / round over while lying: no hold, reset */
    memset(&h, 0, sizeof h); clk = 90000;
    kldh_step(&h, 1, 1, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e); clk += 16; kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e);
    CHECK(kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, clk, 0, 0, &e) == 0 && h.meter == 0 && !h.t_lie, "not alive: no hold, reset");
    /* 14. a second down starts from zero: the meter of the first is not carried */
    memset(&h, 0, sizeof h); clk = 100000;
    t = mash(&h, 8.0f, 10.0f, &clk, 8.0f, 1.5f, &np); CHECK(t > 0, "first down");
    kldh_step(&h, 3, 0, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e); kldh_step(&h, 0, 0, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e);
    kldh_step(&h, 2, 0, 0.016f, 1, 1.5f, 8, clk, 0, 1, &e);
    CHECK(kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, clk + 16, 0, 1, &e) == 1 && h.meter == 0, "second down: held, meter %.2f", h.meter);
    /* 15. the lying tick bound on a clock that wraps */
    memset(&h, 0, sizeof h);
    kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, 0xfffffff0u, 1000, 1, &e);
    CHECK(kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, 0x00000100u, 1000, 1, &e) == 1, "wrapped clock: 272 ms is not 1000");
    CHECK(kldh_step(&h, 1, 0, 0.016f, 1, 1.5f, 8, 0x00000500u, 1000, 1, &e) == 0, "wrapped clock: 1296 ms is over 1000");
    /* 16. NaN dt */
    memset(&h, 0, sizeof h);
    { float nan = (float)sqrt(-1.0); kldh_step(&h, 1, 1, nan, 1, 1.5f, 8, 1, 0, 1, &e); CHECK(h.meter == h.meter && h.meter >= 0, "NaN dt must not poison the meter"); }

    /* 17. the Cover-key filter (MashHoldHow=2): drops only the Cover scan code, press and release, keeps the order of the rest, fixes the count */
    {
        struct kldh_kf k; struct kldh_ev ev[8]; DWORD n; int j;
        memset(&k, 0, sizeof k);
        for (j = 0; j < 6; j++) { memset(&ev[j], 0, sizeof ev[j]); ev[j].seq = j; }
        ev[0].ofs = 0x11; ev[0].data = 0x80;          /* W down */
        ev[1].ofs = 0x2e; ev[1].data = 0x80;          /* C down  (Cover) */
        ev[2].ofs = 0x1e; ev[2].data = 0x80;          /* A down */
        ev[3].ofs = 0x2e; ev[3].data = 0;             /* C up */
        ev[4].ofs = 0x11; ev[4].data = 0;             /* W up */
        ev[5].ofs = 0x2e; ev[5].data = 0x80;          /* C down again */
        n = kldh_filter_events(&k, ev, 6, 0x2e, 1);
        CHECK(n == 3, "filter: count %lu, wanted 3", (unsigned long)n);
        CHECK(ev[0].seq == 0 && ev[1].seq == 2 && ev[2].seq == 4, "filter: order of the kept events: %lu %lu %lu", (unsigned long)ev[0].seq, (unsigned long)ev[1].seq, (unsigned long)ev[2].seq);
        CHECK(k.dropped_down == 1, "filter: the last C press was dropped, its release is owed");
        /* its release arrives in a later read, the filter now OFF: still dropped (the game never saw the press) */
        memset(ev, 0, sizeof ev); ev[0].ofs = 0x2e; ev[0].data = 0; ev[1].ofs = 0x2e; ev[1].data = 0x80; ev[1].seq = 9;
        n = kldh_filter_events(&k, ev, 2, 0x2e, 0);
        CHECK(n == 1 && ev[0].seq == 9 && k.dropped_down == 0, "filter off: the owed release goes, the new press passes (n %lu)", (unsigned long)n);
        /* a stale owed release (the press was dropped, its release never came): the next press passes with the filter off and its release must NOT be eaten */
        memset(&k, 0, sizeof k); k.dropped_down = 1; memset(ev, 0, sizeof ev); ev[0].ofs = 0x2e; ev[0].data = 0x80; ev[1].ofs = 0x2e; ev[1].data = 0;
        n = kldh_filter_events(&k, ev, 2, 0x2e, 0);
        CHECK(n == 2 && k.dropped_down == 0, "stale owed release must not eat the release of a press that passed (n %lu)", (unsigned long)n);
        /* a key already down when the hold begins: its release is KEPT */
        memset(&k, 0, sizeof k); memset(ev, 0, sizeof ev); ev[0].ofs = 0x2e; ev[0].data = 0;
        n = kldh_filter_events(&k, ev, 1, 0x2e, 1);
        CHECK(n == 1, "filter: the release of a key held before the hold is kept (n %lu)", (unsigned long)n);
        /* off: nothing changes; scan 0: nothing matches; empty buffer */
        memset(&k, 0, sizeof k); for (j = 0; j < 3; j++) { memset(&ev[j], 0, sizeof ev[j]); ev[j].ofs = 0x2e; ev[j].data = j & 1 ? 0 : 0x80; }
        CHECK(kldh_filter_events(&k, ev, 3, 0x2e, 0) == 3 && k.dropped_down == 0, "filter off must be a no-op");
        CHECK(kldh_filter_events(&k, ev, 3, 0, 1) == 3, "scan 0 must match nothing");
        CHECK(kldh_filter_events(&k, ev, 0, 0x2e, 1) == 0, "empty buffer");
        /* a buffer of only Cover events empties */
        memset(&k, 0, sizeof k); for (j = 0; j < 4; j++) { memset(&ev[j], 0, sizeof ev[j]); ev[j].ofs = 0x2e; ev[j].data = j & 1 ? 0 : 0x80; }
        CHECK(kldh_filter_events(&k, ev, 4, 0x2e, 1) == 0 && k.dropped_down == 0, "all-Cover buffer empties, pairs complete");
        CHECK(sizeof(struct kldh_ev) == 20, "kldh_ev must be DIDEVICEOBJECTDATA's 20 bytes (is %u)", (unsigned)sizeof(struct kldh_ev));
    }
    {   /* GetDeviceState */
        BYTE st[256]; memset(st, 0, sizeof st); st[0x2e] = 0x80; st[0x11] = 0x80;
        kldh_filter_state(st, 256, 0x2e, 0); CHECK(st[0x2e] == 0x80, "state filter off must not touch");
        kldh_filter_state(st, 256, 0x2e, 1); CHECK(st[0x2e] == 0 && st[0x11] == 0x80, "state filter: only Cover cleared");
        kldh_filter_state(st, 256, 0, 1); kldh_filter_state(st, 16, 0x2e, 1); CHECK(st[0x11] == 0x80, "state filter: scan 0 / short buffer safe");
    }

    /* GIVE-BACK (OnlineFactors / OnlineFreeFall): tonight's online log. One police hit of 111.9 on a man with 120: 120 -> 8.1, DownFromCop 0.15 gives 95.1 back */
    {
        int lt = 9; float nh, nan = 0.0f; nan = nan / nan;
        nh = kldh_giveback(8.1f, 120.0f, 120.0f, 0.15f, &lt); CHECK(lt == 0 && fabs(nh - (8.1f + 111.9f * 0.85f)) < 0.01f && nh < 120.0f, "111.9 hit at 0.15: %.2f", nh);
        nh = kldh_giveback(8.1f, 120.0f, 120.0f, 0.0f, &lt); CHECK(fabs(nh - 120.0f) < 0.01f, "free fall gives it all back, never above what he had: %.2f", nh);
        nh = kldh_giveback(48.4f, 198.7f, 120.0f, 0.1f, &lt); CHECK(nh <= 120.0f && nh > 48.4f, "never above max: %.2f", nh);
        nh = kldh_giveback(0.0f, 120.0f, 120.0f, 0.1f, &lt); CHECK(lt == 1 && nh == 0.0f, "a hit bigger than his health is LETHAL, nothing is given back");
        nh = kldh_giveback(-5.0f, 120.0f, 120.0f, 0.1f, &lt); CHECK(lt == 1 && nh == -5.0f, "dead stays dead");
        nh = kldh_giveback(60.0f, 120.0f, 120.0f, 1.0f, &lt); CHECK(lt == 0 && nh == 60.0f, "factor 1: the hit stays at the game's price");
        nh = kldh_giveback(60.0f, 120.0f, 120.0f, 2.0f, &lt); CHECK(nh == 60.0f, "factor above 1: nothing back");
        nh = kldh_giveback(60.0f, 120.0f, 120.0f, -1.0f, &lt); CHECK(nh == 60.0f, "negative factor: nothing back");
        nh = kldh_giveback(60.0f, 120.0f, 120.0f, nan, &lt); CHECK(nh == 60.0f, "NaN factor: nothing back");
        nh = kldh_giveback(100.0f, 90.0f, 120.0f, 0.1f, &lt); CHECK(nh == 100.0f, "no loss (healed): nothing back");
        nh = kldh_giveback(60.0f, 120.0f, 120.0f, 0.5f, &lt); CHECK(fabs(nh - 90.0f) < 0.01f, "half price: %.2f", nh);
    }

    printf("kldown_hold_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
