/* klperf_logic.h - pure parts of the [Perf] toggles (no windows.h): OSD scan back-off, online cache validity, fast-read range test.
   Tested by klperf_test.c. */
#ifndef KLPERF_LOGIC_H
#define KLPERF_LOGIC_H

/* klhud.c klu_find_osd: ms to wait before the next scan after 'fails' empty scans. on=0: the old 2 s / 15 s steps. */
static unsigned klperf_osd_interval(int fails, int on)
{
    if (!on) return fails < 3 ? 2000u : 15000u;
    return fails < 3 ? 2000u : fails < 6 ? 15000u : 60000u;
}

/* klhud.c klu_find_osd, [Perf] OsdScanSlice: ms one call may scan before it stops and resumes on the next tick; 0 = the whole
   address space in one call (the old way). n9_1106 11-06: 9 seats on one PC, one-call scans of 50 657 / 84 719 ms after the round
   load, the [Auto] watchdog killed 3 seats at 120 s (DD09 inst9, DM03 inst3, DM01B inst4). */
static unsigned klperf_osd_slice_ms(int on)
{
    return on ? 24u : 0u;     /* klu_tick runs every 100 ms: ~25 % of the wall time while a pass runs (8 ms = ~10 %, review 11-06) */
}

/* [Perf] ScanMinFrames: may a wall-clock-timed table walk (klsync Compare / Apply / Puppet / Probe, klor_bots, botfill's census) run again? since_ms /
   since_frames = wall time and game frames since its last run, ms = its interval. on=0: the old ms-only gate. on=1: it also waits ms*20/1000 frames
   (rounded up), so a seat at 20 fps or faster runs it exactly as before, and a starved seat (below ~2 fps every ms gate fired on EVERY frame, each a
   ~2-20k-read walk; study 11-06) runs it at most once per that many frames. */
static int klperf_due(unsigned since_ms, unsigned since_frames, unsigned ms, int on)
{
    if (since_ms < ms) return 0;
    return !on || since_frames >= (ms * 20u + 999u) / 1000u;
}

/* has a sliced scan used up its budget? slice 0 never stops; elapsed = GetTickCount() - the call's start (unsigned, wraps fine) */
static int klperf_slice_over(unsigned slice, unsigned elapsed)
{
    return slice != 0 && elapsed >= slice;
}

/* kl_online() cache: may the last answer be reused? have = a value is cached; game_thread = caller is the main loop's thread;
   same_tick = klh_ticks has not changed since it was stored; age_ms = GetTickCount() - stored time (unsigned, wraps fine). */
static int klperf_cache_ok(int have, int game_thread, int same_tick, unsigned age_ms)
{
    if (!have) return 0;
    if (game_thread) return same_tick;
    return age_ms < 50u;
}

/* klh_rd fast path: is [p, p+n) wholly inside [lo, hi) (no overflow)? */
static int klperf_in_range(unsigned long p, unsigned long n, unsigned long lo, unsigned long hi)
{
    return n != 0 && p >= lo && p < hi && n <= hi - p;
}

/* [Perf] QuietProbes: the TEST build turns the four read-only probes (BotDeathProbe, CoverDump, CoverRing, MFProbe) on by default; with QuietProbes=1 their
   DEFAULT is off (a key written in the ini still wins). SHIP builds default off already. test_build = KLHOOK_TEST, quiet = the [Perf] key. */
static int klperf_probe_default(int test_build, int quiet)
{
    return test_build && !quiet;
}

/* [Perf] TickProfile: indexes of the k largest v[0..n-1] (descending, ties keep the lower index first), out[] gets min(k, n) entries; returns that count.
   Entries with v <= 0 are skipped (a part that cost nothing is not listed). */
static int klperf_pick_top(const double *v, int n, int *out, int k)
{
    int i, j, m = 0;
    for (i = 0; i < n; i++) {
        if (!(v[i] > 0.0)) continue;
        for (j = m; j > 0 && v[out[j - 1]] < v[i]; j--) { if (j < k) out[j] = out[j - 1]; }
        if (j < k) { out[j] = i; if (m < k) m++; }
    }
    return m;
}
#endif
