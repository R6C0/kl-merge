/* klcoverring_logic.h - pure logic of klcoverring.c ([CoverRing] poll of the engine's REAL cover count [L+0x68] and the ZHavokCar scripts' ring state).
 * No windows.h: klcoverring_test.c checks it off-game. 2026-11-01.
 *   schedule : every tick for the first KCR_FAST_MS after a level load, then once per KCR_SLOW_MS.
 *   change   : a line is logged only when the count (or the car signature) differs from the last logged one.
 *   signature: a cheap order-sensitive hash of the car records, so a done-flag flip of one car is seen as a change.
 */
#ifndef KLCOVERRING_LOGIC_H
#define KLCOVERRING_LOGIC_H

#define KCR_FAST_MS 90000UL                 /* poll every tick this long after the load */
#define KCR_SLOW_MS 5000UL                  /* then every 5 s */
#define KCR_MAX_ENUM 60                     /* cap of car enumerations per load (log budget) */

/* is a poll due? since = ms since the load, last = ms since the last poll (0xffffffff = never). Unsigned, wrap safe. */
static int kcr_due(unsigned long since, unsigned long last)
{
    if (last == 0xfffffffful) return 1;
    if (since < KCR_FAST_MS) return 1;
    return last >= KCR_SLOW_MS;
}

/* did something change? have = 0 on the first sample of a load (that always logs: the 'at load' line) */
static int kcr_changed(int have, unsigned long prev_cnt, unsigned long cnt, unsigned long prev_sig, unsigned long sig)
{
    if (!have) return 1;
    return prev_cnt != cnt || prev_sig != sig;
}

/* fold one car's observable state into a signature */
static unsigned long kcr_sig_add(unsigned long sig, unsigned long car, unsigned long script, unsigned long n, unsigned long done, unsigned long rsv)
{
    sig = sig * 31ul + car;
    sig = sig * 31ul + script;
    sig = sig * 31ul + n;
    sig = sig * 31ul + (done & 0xfful);
    sig = sig * 31ul + (rsv & 0xfful);
    return sig;
}

/* a count a running level can show: the real list holds a few hundred points; anything huge is a misread */
static int kcr_count_sane(unsigned long cnt) { return cnt < 100000ul; }

/* does a car's script look like one: [script+0x40] must be the car, and the 8 ring indices are shown only up to n (max 8) */
static int kcr_script_matches(unsigned long car, unsigned long script_back) { return car != 0 && car == script_back; }
static unsigned long kcr_idx_shown(unsigned long n) { return n > 8ul ? 8ul : n; }

/* "does the host's real count equal base + 8 * (cars whose writer ran)?" - the GUESS of the c9 note, as a number: returns the surplus (cnt - base - 8*ran), 0 = equal */
static long kcr_surplus(unsigned long cnt, unsigned long base, unsigned long ran) { return (long)cnt - (long)base - 8L * (long)ran; }

#endif
