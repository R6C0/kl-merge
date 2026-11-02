/* klslot_rand_test.c - OFF-GAME check of klslot_rand_logic.h (the random online map: seed mix, choice, round rule).
 * Proves the lobby peek and the real pick cannot disagree: the peek runs the same functions on a COPY of the state.
 *   Windows: cl /nologo /W3 klslot_rand_test.c     else: gcc -m32 -I test_shim klslot_rand_test.c */
#include <stdio.h>
#include <string.h>
#include "klslot_rand_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

/* a transcript of the ORIGINAL kls_rand_pick arithmetic (klslot.c before names-lobby-1102), kept verbatim as the reference */
static int orig_pick(unsigned lob0, unsigned lob1, int src, int num, unsigned *round, unsigned *last, unsigned now, int round_on, int n, unsigned *lobs)
{
    kls_u64 x;
    if (src) { if (lob0 != lobs[0] || lob1 != lobs[1]) { lobs[0] = lob0; lobs[1] = lob1; *round = 0; *last = 0; } }
    else lob0 = lob1 = 0;
    if (!src && *last && now - *last > 1800000u) *round = 0;
    if (!*last || now - *last > 60000u) (*round)++;
    *last = now ? now : 1;
    x = ((kls_u64)lob1 << 32 | lob0) ^ ((kls_u64)(num + 1) * 0x9E3779B97F4A7C15ULL);
    if (round_on || !src) x ^= (kls_u64)(*round) * 0xD6E8FEB86659FD93ULL;
    x ^= x >> 30; x *= 0xBF58476D1CE4E5B9ULL; x ^= x >> 27; x *= 0x94D049BB133111EBULL; x ^= x >> 31;
    return (int)(x % (unsigned)n);
}

/* the new pick, as klslot.c composes it from the header */
static int new_pick(unsigned lob0, unsigned lob1, int src, int num, unsigned *round, unsigned *last, unsigned now, int round_on, int n, unsigned *lobs)
{
    if (src) { int ch = lob0 != lobs[0] || lob1 != lobs[1]; if (ch) { lobs[0] = lob0; lobs[1] = lob1; } kls_rnd_advance(round, last, now, 1, ch); }
    else { lob0 = lob1 = 0; kls_rnd_advance(round, last, now, 0, 0); }
    return kls_rand_index(kls_rand_mix(lob0, lob1, num, *round, round_on || !src), n);
}

int main(void)
{
    unsigned r1 = 0, l1 = 0, b1[2] = { 0, 0 }, r2 = 0, l2 = 0, b2[2] = { 0, 0 }, t = 1000, i, lob0, lob1;
    int num, src, ron, hist[3] = { 0, 0, 0 }, a, b;
    /* 1. the refactored pick equals the original over many rounds, lobbies, slots, both seed modes, with a tick wrap */
    for (i = 0; i < 4000; i++) {
        lob0 = 0x1000193u * (i / 7 + 1); lob1 = 0x01100000u + (i / 50);
        src = (i % 11) != 0; ron = (i / 3) & 1; num = 1 + (int)(i % 9);
        t += (i % 5 == 0) ? 90000u : 3000u;                          /* some loads 90 s apart (new round), some within a load */
        if (i == 2000) t = 0xFFFFFF00u;                              /* GetTickCount wrap */
        if (i == 2001) t = 5000u;
        a = orig_pick(lob0, lob1, src, num, &r1, &l1, t, ron, 3, b1);
        b = new_pick(lob0, lob1, src, num, &r2, &l2, t, ron, 3, b2);
        CHECK(a == b && r1 == r2 && l1 == l2);
        if (a >= 0 && a < 3) hist[a]++;
    }
    CHECK(hist[0] > 500 && hist[1] > 500 && hist[2] > 500);          /* every candidate reachable */
    /* 2. the peek (header functions on COPIES) gives the answer the next pick gives, and moves nothing */
    r1 = 3; l1 = 100000; b1[0] = 0xabc; b1[1] = 0xdef;
    { unsigned pr = r1, pl = l1, pr2, pl2, now = l1 + 200000u; int lobchg = 0;
      pr2 = pr; pl2 = pl; kls_rnd_advance(&pr2, &pl2, now, 1, lobchg);                 /* the peek */
      CHECK(r1 == 3 && l1 == 100000);                                                  /* the live state is untouched */
      CHECK(pr2 == 4);                                                                 /* next round */
      a = kls_rand_index(kls_rand_mix(0xabc, 0xdef, 4, pr2, 1), 3);
      b = new_pick(0xabc, 0xdef, 1, 4, &r1, &l1, now, 1, 3, b1);                       /* the real load */
      CHECK(a == b && r1 == 4); }
    /* 3. round rule corners */
    { unsigned r = 5, l = 1000;
      kls_rnd_advance(&r, &l, 1000 + 60000u, 1, 0); CHECK(r == 5);                     /* exactly 60 s: still the same load */
      kls_rnd_advance(&r, &l, 1000 + 60000u + 60001u, 1, 0); CHECK(r == 6);            /* more than 60 s */
      kls_rnd_advance(&r, &l, l + 10, 1, 1); CHECK(r == 1);                            /* a new lobby: round 1 */
      r = 7; l = 10; kls_rnd_advance(&r, &l, 10 + 1800001u, 0, 0); CHECK(r == 1);      /* no lobby id, 30 min: new session */
      r = 0; l = 0; kls_rnd_advance(&r, &l, 0, 1, 0); CHECK(r == 1 && l == 1);         /* tick 0 never stored as 0 */ }
    /* 4. without the round in the seed the answer is a pure function of (lobby, slot, n): the lobby peek is exact */
    CHECK(kls_rand_mix(1, 2, 3, 0, 0) == kls_rand_mix(1, 2, 3, 99, 0));
    CHECK(kls_rand_mix(1, 2, 3, 0, 1) != kls_rand_mix(1, 2, 3, 99, 1));
    CHECK(kls_rand_index(kls_rand_mix(1, 2, 3, 0, 0), 1) == 0);
    printf("klslot_rand_test: %d checks, %d fails\n", checks, fails);
    return fails ? 1 : 0;
}
