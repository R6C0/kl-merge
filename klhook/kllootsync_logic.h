/* kllootsync_logic.h - the PURE parts of kllootsync.c ([BotFill] OnlineLootSync): the 'KLSYB' packet (the host's AI heister loot state -> every client), its strict decoder,
 * the stale-packet rule and the one-line HUD text. No game reads, no windows.h: kllootsync.c feeds it numbers. Checked off-game by kllootsync_test.c.
 *
 * KLSYB (little endian, UDP 27415 broadcast from the host, the same socket as KLSY2 / KLSYL; an old receiver skips any magic it does not know)
 *    0   8   "KLSYB\0\0\0"
 *    8   u32 T       the host's klsy_T() (ms modulo 1e9)
 *   12   u16 n       records, 0..8
 *   14   u8  ver = 1
 *   15   u8  flags   bit0 = the round's FINAL list (sent at the round summary)
 *   16   u32 round   the host's round counter (klbf_ot_rounds), 1..999999
 *   20   i32 carried the bots' loot still carried (alive, not aboard)
 *   24   i32 banked  the bots' loot aboard the van (the hook ledger's view)
 *   28   n x 8 { u8 digit (group digit '2'..'8' as 2..8, 0 = unknown), u8 slot (klbf_ob index 0..63), u8 state (0 carrying, 1 boarded, 2 dead), u8 0, i32 amount }
 * The format is a GUESS of this build (nothing else on the wire uses it). */
#ifndef KLLOOTSYNC_LOGIC_H
#define KLLOOTSYNC_LOGIC_H

#include <stdio.h>
#include <string.h>

#define KLLS_MAXN    8
#define KLLS_HDR     28
#define KLLS_REC     8
#define KLLS_MAXAMT  100000000
#define KLLS_ST_CARRY 0
#define KLLS_ST_BOARD 1
#define KLLS_ST_DEAD  2

struct klls_rec { int digit, slot, state, amt; };
struct klls_pk { unsigned T, round; int flags, n, carried, banked; struct klls_rec r[KLLS_MAXN]; };

static void klls_put32(unsigned char *p, unsigned v) { p[0] = (unsigned char)v; p[1] = (unsigned char)(v >> 8); p[2] = (unsigned char)(v >> 16); p[3] = (unsigned char)(v >> 24); }
static unsigned klls_get32(const unsigned char *p) { return (unsigned)p[0] | (unsigned)p[1] << 8 | (unsigned)p[2] << 16 | (unsigned)p[3] << 24; }

/* bytes written, 0 = refused (cap too small / n out of range) */
static int klls_encode(unsigned char *out, int cap, const struct klls_pk *k)
{
    int i, len;
    if (k->n < 0 || k->n > KLLS_MAXN) return 0;
    len = KLLS_HDR + k->n * KLLS_REC;
    if (cap < len) return 0;
    memset(out, 0, (size_t)len);
    memcpy(out, "KLSYB", 5);
    klls_put32(out + 8, k->T); out[12] = (unsigned char)k->n; out[13] = 0; out[14] = 1; out[15] = (unsigned char)k->flags;
    klls_put32(out + 16, k->round); klls_put32(out + 20, (unsigned)k->carried); klls_put32(out + 24, (unsigned)k->banked);
    for (i = 0; i < k->n; i++) {
        unsigned char *q = out + KLLS_HDR + i * KLLS_REC;
        q[0] = (unsigned char)k->r[i].digit; q[1] = (unsigned char)k->r[i].slot; q[2] = (unsigned char)k->r[i].state; q[3] = 0; klls_put32(q + 4, (unsigned)k->r[i].amt);
    }
    return len;
}

/* 1 = a whole, plausible packet. Every field is range-checked; a short / long / foreign / out-of-range packet gives 0 and *k is left half-written (do not use it). */
static int klls_decode(const unsigned char *pk, int len, struct klls_pk *k)
{
    int i, n; long sum = 0;
    if (!pk || !k || len < KLLS_HDR || memcmp(pk, "KLSYB\0\0\0", 8)) return 0;
    n = pk[12] | pk[13] << 8;
    if (pk[14] != 1 || n > KLLS_MAXN || len < KLLS_HDR + n * KLLS_REC || (pk[15] & ~1)) return 0;
    memset(k, 0, sizeof *k);
    k->T = klls_get32(pk + 8); k->round = klls_get32(pk + 16); k->flags = pk[15]; k->n = n;
    k->carried = (int)klls_get32(pk + 20); k->banked = (int)klls_get32(pk + 24);
    if (k->T >= 1000000000u || k->round < 1 || k->round > 999999u) return 0;      /* klsy_T() never reaches 1e9 */
    if (k->carried < 0 || k->carried > KLLS_MAXAMT * KLLS_MAXN || k->banked < 0 || k->banked > KLLS_MAXAMT * KLLS_MAXN) return 0;
    for (i = 0; i < n; i++) {
        const unsigned char *q = pk + KLLS_HDR + i * KLLS_REC;
        k->r[i].digit = q[0]; k->r[i].slot = q[1]; k->r[i].state = q[2]; k->r[i].amt = (int)klls_get32(q + 4);
        if (k->r[i].digit > 9 || k->r[i].slot > 63 || k->r[i].state > KLLS_ST_DEAD || q[3] || k->r[i].amt < 0 || k->r[i].amt > KLLS_MAXAMT) return 0;
        sum += k->r[i].amt;
    }
    (void)sum;
    return 1;
}

/* 1 = (round, T) is newer than what is held (round 0 = nothing held). Same round: T forward by 1 .. 5e8-1 ms modulo 1e9 (the clock wraps), anything else is an old packet that came late. A final list (flags bit0) of the held T is also newer once. */
static int klls_newer(unsigned round, unsigned T, unsigned held_round, unsigned held_T)
{
    unsigned fwd;
    if (!held_round || round > held_round) return 1;
    if (round < held_round) return 0;
    fwd = (T + 1000000000u - held_T % 1000000000u) % 1000000000u;
    return fwd != 0 && fwd < 500000000u;
}

/* "$1,250,000" into out */
static void klls_money(char *out, int cap, int v)
{
    if (v >= 1000000) snprintf(out, (size_t)cap, "$%d,%03d,%03d", v / 1000000, v / 1000 % 1000, v % 1000);
    else if (v >= 1000) snprintf(out, (size_t)cap, "$%d,%03d", v / 1000, v % 1000);
    else snprintf(out, (size_t)cap, "$%d", v);
}

/* the one HUD line: "BOTS carry $350,000 | banked $0 | 2:$100,000 3:$250,000 (aboard) 4:$0 (down)"; bots with nothing and nothing to say are left out. Returns the length. */
static int klls_text(char *out, int cap, const struct klls_pk *k)
{
    char a[24], b[24], m[24]; int i, w;
    klls_money(a, sizeof a, k->carried); klls_money(b, sizeof b, k->banked);
    w = snprintf(out, (size_t)cap, "BOTS carry %s | banked %s |", a, b);
    if (w < 0 || w >= cap) { if (cap > 0) out[cap - 1] = 0; return cap > 0 ? (int)strlen(out) : 0; }
    for (i = 0; i < k->n; i++) {
        const struct klls_rec *r = &k->r[i]; int got;
        if (!r->amt && r->state == KLLS_ST_CARRY) continue;
        klls_money(m, sizeof m, r->amt);
        if (r->digit) got = snprintf(out + w, (size_t)(cap - w), " %d:%s%s", r->digit, m, r->state == KLLS_ST_BOARD ? " aboard" : r->state == KLLS_ST_DEAD ? " down" : "");
        else got = snprintf(out + w, (size_t)(cap - w), " #%d:%s%s", r->slot, m, r->state == KLLS_ST_BOARD ? " aboard" : r->state == KLLS_ST_DEAD ? " down" : "");
        if (got < 0 || got >= cap - w) { out[w] = 0; break; }      /* no room: the whole record is dropped, never cut in the middle */
        w += got;
    }
    return (int)strlen(out);
}

#endif /* KLLOOTSYNC_LOGIC_H */
