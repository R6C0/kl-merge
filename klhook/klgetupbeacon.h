/* klgetupbeacon.h - [BotFill] OnlineGetUpBeacon, the PURE part (pack / unpack, dedupe, staleness, send schedule, seat check). No game memory, no log, no clock of its own,
   no windows.h. Included by klbotfill.c (host state), klgetupbeacon.c (sockets) and klgetupbeacon_test.c. Design: re/bot_getup_online.md section 7.
   Why: on the HOST a joiner's replica body never enters a down state (kldown.c's mirror refuses it), so klbf_gu_pass never saw "seat N IS DOWN" (bench GU3 10-28).
   The downed machine knows it is down: it tells the host in a tiny UDP packet (the KLSYB / KLSYV channel, port 27415, broadcast; magic 'KLSYD').

   Packet, 32 bytes, little endian:
     0  'K' 'L' 'S' 'Y' 'D'
     5  u8  version (1)
     6  u8  seat      = the sender's index in the session player table (klco_table; the table index is taken as equal on every peer, re/char_online.md 2)
     7  u8  flags     bit0 = down (1) / up (0)
     8  u32 seq       up beacons repeat their seq (3 sends), down beacons use a new seq each second; the host takes only a seq newer than the last of that seat
     12 u32 tag       hash of the scene name: a beacon of another level / a stale peer does not count
     16 u32 T         the sender's tick in ms (diagnostic: the gap to the sender's previous beacon)
     20 f32 x3        the sender's feet [pl+0x460] (cm) */
#ifndef KLGETUPBEACON_H
#define KLGETUPBEACON_H

#include <string.h>
#include <math.h>

#define KLGB_LEN        32
#define KLGB_VER        1
#define KLGB_MAX_SEATS  16
#define KLGB_PERIOD_MS  1000      /* a down beacon every second while down */
#define KLGB_UP_SENDS   3         /* the up beacon: sent 3 times ... */
#define KLGB_UP_GAP_MS  100       /* ... 100 ms apart */
#define KLGB_FRESH_MS   3000      /* the host trusts a down beacon this long after it arrived */
#define KLGB_MAP_TOL_CM 1500.0f   /* beacon vs the replica of the same table index: farther than this = the index does not name that body (GUESS threshold) */
#define KLGB_NEAR_CM    600.0f    /* the nearest-replica fallback accepts a replica this close to the beacon's place (GUESS) */

struct klgb_pk { unsigned char ver, seat, flags; unsigned seq, tag, T; float pos[3]; };

static int klgb_encode(unsigned char *b, int cap, const struct klgb_pk *k)
{
    if (cap < KLGB_LEN) return 0;
    memset(b, 0, KLGB_LEN); memcpy(b, "KLSYD", 5);
    b[5] = KLGB_VER; b[6] = k->seat; b[7] = k->flags;
    memcpy(b + 8, &k->seq, 4); memcpy(b + 12, &k->tag, 4); memcpy(b + 16, &k->T, 4); memcpy(b + 20, k->pos, 12);
    return KLGB_LEN;
}

/* 1 = a valid beacon (magic, length, version, seat in range, finite place) */
static int klgb_decode(const unsigned char *b, int len, struct klgb_pk *k)
{
    int i;
    if (len < KLGB_LEN || memcmp(b, "KLSYD", 5) || b[5] != KLGB_VER || b[6] >= KLGB_MAX_SEATS) return 0;
    k->ver = b[5]; k->seat = b[6]; k->flags = b[7];
    memcpy(&k->seq, b + 8, 4); memcpy(&k->tag, b + 12, 4); memcpy(&k->T, b + 16, 4); memcpy(k->pos, b + 20, 12);
    for (i = 0; i < 3; i++) if (!(fabs((double)k->pos[i]) < 1e7)) return 0;      /* NaN / inf / absurd */
    return 1;
}

/* FNV-1a of the scene name, lower-cased: both peers load the same level */
static unsigned klgb_tag(const char *s)
{
    unsigned h = 2166136261u;
    for (; *s; s++) { unsigned c = (unsigned char)*s; if (c >= 'A' && c <= 'Z') c += 32; h = (h ^ c) * 16777619u; }
    return h;
}

/* ---- the downed machine: the send schedule ---- */
struct klgb_tx { int down; unsigned seq; unsigned nextAt; int burst; };

/* One call per pass with this machine's own down state. 1 = send a packet now with (*outDown, *outSeq). Down: at once, then every KLGB_PERIOD_MS with a new seq.
   Getting up: ONE new seq, sent KLGB_UP_SENDS times KLGB_UP_GAP_MS apart. A down again during the burst cancels it. */
static int klgb_tx_step(struct klgb_tx *t, int down, unsigned now, int *outDown, unsigned *outSeq)
{
    if (down) {
        if (!t->down || (int)(now - t->nextAt) >= 0) { t->down = 1; t->burst = 0; t->seq++; t->nextAt = now + KLGB_PERIOD_MS; *outDown = 1; *outSeq = t->seq; return 1; }
        return 0;
    }
    if (t->down) { t->down = 0; t->seq++; t->burst = KLGB_UP_SENDS; t->nextAt = now; }
    if (t->burst > 0 && (int)(now - t->nextAt) >= 0) { t->burst--; t->nextAt = now + KLGB_UP_GAP_MS; *outDown = 0; *outSeq = t->seq; return 1; }
    return 0;
}

/* ---- the host: what each seat last told ---- */
struct klgb_seat { int have, down; unsigned seq, rxAt, lastT; float pos[3]; };

/* 0 dropped (repeat / older seq), 1 taken. *gap = ms since this seat's previous beacon on the SENDER's clock (0 for the first). */
static int klgb_take(struct klgb_seat *s, const struct klgb_pk *k, unsigned now, unsigned *gap)
{
    if (s->have && (int)(k->seq - s->seq) <= 0) return 0;
    *gap = s->have ? k->T - s->lastT : 0;
    s->have = 1; s->seq = k->seq; s->rxAt = now; s->lastT = k->T; s->down = k->flags & 1; memcpy(s->pos, k->pos, 12);
    return 1;
}

/* a fresh DOWN beacon (an up beacon clears it at once; an old one lapses) */
static int klgb_fresh_down(const struct klgb_seat *s, unsigned now)
{
    return s->have && s->down && (unsigned)(now - s->rxAt) < KLGB_FRESH_MS;
}

static float klgb_dist2d(const float *a, const float *b) { float dx = a[0] - b[0], dz = a[2] - b[2]; return (float)sqrt(dx * dx + dz * dz); }

/* Does table index `seat` name the body that sent the beacon? rok = the replica's place was read. Unreadable replica: trusted (nothing to compare). */
static int klgb_map_ok(const float *beacon, const float *replica, int rok)
{
    return !rok || klgb_dist2d(beacon, replica) <= KLGB_MAP_TOL_CM;
}

/* The fallback when the index does not fit: the replica nearest to the beacon's place within KLGB_NEAR_CM (skipping `skip`); -1 = none. rep[i] valid where rok[i]. */
static int klgb_nearest(const float *beacon, const float (*rep)[3], const int *rok, int n, int skip)
{
    int i, best = -1; float bd = 1e30f;
    for (i = 0; i < n; i++) if (i != skip && rok[i]) { float d = klgb_dist2d(beacon, rep[i]); if (d <= KLGB_NEAR_CM && d < bd) { bd = d; best = i; } }
    return best;
}

#endif /* KLGETUPBEACON_H */
