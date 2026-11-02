/*
 * klslot_rand_logic.h - the PURE part of klslot.c's random online map (OnlineSet=9): the seed mix, the choice, and the round-counter rule.
 * No windows.h, no game access, so klslot_rand_test.c can prove it off-game (2026-11-02, names-lobby-1102).
 *
 * WHY IT IS A HEADER: the real pick (kls_rand_pick, at a level load) and the lobby's title lookup (kllocname.c, kls_rand_peek) must agree
 * bit for bit, or the lobby names a map that is not the one that loads. Both therefore call these three functions; the pick on the live
 * state, the peek on a COPY of it (kls_rnd_advance is the only one that moves state, and it only moves what it is handed).
 */
#ifndef KLSLOT_RAND_LOGIC_H
#define KLSLOT_RAND_LOGIC_H

typedef unsigned long long kls_u64;

/* the mixed seed of slot number `num` (1..9) in lobby (lob0 = low dword, lob1 = high dword of the 8 bytes at svc+0x35e).
   use_round: the round number joins the seed (OnlineRandomRound=1, or no lobby id = System Link). */
static kls_u64 kls_rand_mix(unsigned lob0, unsigned lob1, int num, unsigned round, int use_round)
{
    kls_u64 x = ((kls_u64)lob1 << 32 | lob0) ^ ((kls_u64)(num + 1) * 0x9E3779B97F4A7C15ULL);
    if (use_round) x ^= (kls_u64)round * 0xD6E8FEB86659FD93ULL;
    x ^= x >> 30; x *= 0xBF58476D1CE4E5B9ULL; x ^= x >> 27; x *= 0x94D049BB133111EBULL; x ^= x >> 31;
    return x;
}

/* the index into the candidate list (n >= 1) */
static int kls_rand_index(kls_u64 x, int n) { return n < 1 ? 0 : (int)(x % (unsigned)n); }

/* the round counter at a level load (the first open of a slot archive), exactly the three rules klslot.c always had:
     - a different lobby id (src = a lobby id was read): the count starts again (round 0, last 0) before the next rule;
     - no lobby id and 30 min since the last load: a new session (round 0);
     - no previous load, or more than 60 s since it: a new round (round + 1);
   then `last` = now (never 0 once a load happened). now/last are GetTickCount() values; unsigned subtraction handles the wrap. */
static void kls_rnd_advance(unsigned *round, unsigned *last, unsigned now, int src, int lobby_changed)
{
    if (src && lobby_changed) { *round = 0; *last = 0; }
    if (!src && *last && now - *last > 1800000u) *round = 0;
    if (!*last || now - *last > 60000u) (*round)++;
    *last = now ? now : 1;
}

#endif /* KLSLOT_RAND_LOGIC_H */
