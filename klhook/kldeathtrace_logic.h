/* kldeathtrace_logic.h - the PURE part of [DeathTrace] (kldeathtrace.c, TEST builds only): a line cap, a sample ring, the 'is this stack word a return
 * address' test and the stack scan. No windows.h; the stack words and the code bytes arrive through arguments / a read callback. Checked off-game by
 * kldeathtrace_test.c. 2026-11-10. */
#ifndef KLDEATHTRACE_LOGIC_H
#define KLDEATHTRACE_LOGIC_H
#include <string.h>

#define KDT_RING 64                                   /* samples kept: 6.4 s at the default 100 ms */

/* a line cap: counts one more line, 1 while it is still within cap (cap <= 0 = none allowed) */
static int kdt_take(long *n, long cap) { if (*n >= cap) return 0; (*n)++; return 1; }

/* the period test, wrap-safe for a millisecond counter */
static int kdt_due(unsigned long now, unsigned long last, unsigned long period) { return (unsigned long)(now - last) >= period; }

typedef struct { float p[3], p100[3], v[3], hp; unsigned long t; int mov, box; } kdt_samp;       /* box: 0 outside, 1 inside, 2 inside but the look-ahead leaves */
typedef struct { kdt_samp s[KDT_RING]; int head, n; } kdt_ring;

static void kdt_ring_clear(kdt_ring *r) { r->head = 0; r->n = 0; }
static void kdt_ring_push(kdt_ring *r, const kdt_samp *s) { r->s[r->head] = *s; r->head = (r->head + 1) % KDT_RING; if (r->n < KDT_RING) r->n++; }
/* the k-th newest sample (0 = newest), 0 when there is none */
static const kdt_samp *kdt_ring_back(const kdt_ring *r, int k) { return (k < 0 || k >= r->n) ? 0 : &r->s[(r->head + KDT_RING - 1 - k) % KDT_RING]; }

/* b[0..5] = the six bytes that END at a stack word (b[5] is the byte right before it). Is that word the return address of a CALL?
   E8 rel32 (b[1]); FF /2 as call reg or call [reg] (2 bytes, b[4..5]); FF /2 + disp8 (3 bytes, b[3..5]), + SIB (3 bytes, b[3] with mod 0, or b[2] with
   mod 1); FF /2 + disp32 (6 bytes: call [abs] or call [reg+disp32], b[0..1]). A heuristic: a stack word can match by chance, so a hit is a candidate. */
static int kdt_is_call_ret(const unsigned char *b)
{
    unsigned m;
    if (b[1] == 0xe8) return 1;
    m = b[5];                                                              /* FF D0 = call eax; FF 12 = call [edx] */
    if (b[4] == 0xff && ((m >> 3) & 7) == 2 && ((m >> 6) == 3 || ((m >> 6) == 0 && (m & 7) != 4 && (m & 7) != 5))) return 1;
    m = b[4];                                                              /* FF 50 xx = call [eax+disp8] */
    if (b[3] == 0xff && ((m >> 3) & 7) == 2 && (m >> 6) == 1 && (m & 7) != 4) return 1;
    m = b[4];                                                              /* FF 14 SIB = call [base+idx*s] */
    if (b[3] == 0xff && ((m >> 3) & 7) == 2 && (m >> 6) == 0 && (m & 7) == 4) return 1;
    m = b[3];                                                              /* FF 54 SIB disp8 */
    if (b[2] == 0xff && ((m >> 3) & 7) == 2 && (m >> 6) == 1 && (m & 7) == 4) return 1;
    m = b[1];                                                              /* FF 15 abs32 / FF 90 disp32 */
    if (b[0] == 0xff && ((m >> 3) & 7) == 2 && ((m >> 6) == 2 || (m == 0x15)) && (m & 7) != 4) return 1;
    return 0;
}

/* the first 'max' return addresses on a stack: w[0] is [esp] at the site (the caller's own return address, taken without a test); every later word in
   [lo, hi) whose six preceding code bytes (rd(ra, six) fills them, 0 = unreadable) look like a call is one. Returns how many were found. */
static int kdt_scan_stack(const unsigned long *w, int nw, unsigned long lo, unsigned long hi,
                          int (*rd)(unsigned long ra, unsigned char *six, void *ctx), void *ctx, unsigned long *out, int max)
{
    int i, n = 0; unsigned char six[6];
    for (i = 0; i < nw && n < max; i++) {
        if (w[i] < lo || w[i] >= hi) continue;
        if (i == 0) { out[n++] = w[i]; continue; }
        if (rd(w[i], six, ctx) && kdt_is_call_ret(six)) out[n++] = w[i];
    }
    return n;
}

#endif
