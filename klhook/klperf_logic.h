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
#endif
