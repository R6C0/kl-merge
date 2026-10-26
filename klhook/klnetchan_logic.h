/* klnetchan_logic.h - the PURE parts of klnetchan.c (the hook's shared peer-to-peer message channel, re/hook_netchannel.md):
 * packet text build / parse, the payload sanitiser, the (sender, seq) duplicate filter and the Steam member-data ring.
 * No game reads, no sockets: klnetchan.c feeds it strings. Checked off-game by klnc_test.c (tools/run_harness_linux.sh klnc_test).
 *
 * PACKET (one line of printable ASCII, at most KLNC_PKT_MAX bytes):
 *   KLNC1;<sid: 8 hex>;<role: 0..9>;<ent: -1..63>;<seq: decimal>;<type: 2..8 of A-Z 0-9>;<payload>
 *   sid  = a random number each process draws at start (tells two games on one PC apart; the duplicate key with seq)
 *   role = the sender's session role when it sent (2 host, 3 client: [session+0x54]); receivers trust 'from the host' by this
 *   ent  = the sender's own entry in the session player table (-1 = not known)
 *   seq  = the sender's message number (each message is sent several times with the same seq; receivers keep the first)
 *   payload = the rest of the line; may hold ';' ; never control bytes (they become ' ') nor KLNC_SEP '`' (becomes '\'') */
#ifndef KLNETCHAN_LOGIC_H
#define KLNETCHAN_LOGIC_H

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#define KLNC_PKT_MAX     200       /* a whole packet line */
#define KLNC_PAY_MAX     128       /* payload bytes kept (incl. the 0) */
#define KLNC_TYPE_MAX    9         /* type bytes kept (incl. the 0) */
#define KLNC_SEEN        64        /* (sid, seq) pairs remembered */
#define KLNC_RING        4         /* last messages kept in the Steam member-data value */
#define KLNC_SEP         '`'       /* joins the ring's lines (klh_rdstr refuses control bytes, so not '\n'); never inside a packet */

struct knc_msg { unsigned sid; int role, ent; unsigned seq; char type[KLNC_TYPE_MAX]; char payload[KLNC_PAY_MAX]; };

/* payload: printable ASCII only, length capped; returns the length written */
static int knc_sanitize(const char *in, char *out, int cap)
{
    int n = 0;
    if (cap <= 0) return 0;
    if (in) for (; *in && n < cap - 1; in++) { unsigned char c = (unsigned char)*in; out[n++] = c == (unsigned char)KLNC_SEP ? '\'' : (c >= 0x20 && c < 0x7f) ? (char)c : ' '; }
    out[n] = 0;
    return n;
}

static int knc_type_ok(const char *t)
{
    int n = 0;
    if (!t) return 0;
    for (; t[n]; n++) { char c = t[n]; if (!((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) || n >= KLNC_TYPE_MAX - 1) return 0; }
    return n >= 2;
}

/* -> length of the packet in out, 0 when the type is not valid or it does not fit */
static int knc_build(char *out, int cap, unsigned sid, int role, int ent, unsigned seq, const char *type, const char *payload)
{
    char pay[KLNC_PAY_MAX]; int n;
    if (!knc_type_ok(type) || role < 0 || role > 9) return 0;
    if (ent < -1 || ent > 63) ent = -1;
    knc_sanitize(payload, pay, sizeof pay);
    n = snprintf(out, cap, "KLNC1;%08x;%d;%d;%u;%s;%s", sid, role, ent, seq, type, pay);
    if (n <= 0 || n >= cap || n >= KLNC_PKT_MAX) { if (cap > 0) out[0] = 0; return 0; }
    return n;
}

/* -> 1 and *m filled for a valid packet line (len bytes, need not be 0-terminated); 0 for anything else */
static int knc_parse(const char *in, int len, struct knc_msg *m)
{
    char b[KLNC_PKT_MAX + 1], *f[6], *p; int i, k;
    unsigned long v;
    if (!in || len < 16 || len > KLNC_PKT_MAX) return 0;
    memcpy(b, in, (size_t)len); b[len] = 0;
    if (strncmp(b, "KLNC1;", 6)) return 0;
    p = b + 6;
    for (i = 0; i < 6; i++) {                                  /* six fields; the 6th (payload) is the rest of the line */
        f[i] = p;
        if (i == 5) break;
        while (*p && *p != ';') p++;
        if (*p != ';') return 0;
        *p++ = 0;
    }
    /* sid: exactly 8 hex */
    if (strlen(f[0]) != 8) return 0;
    for (k = 0; k < 8; k++) { char c = f[0][k]; if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) return 0; }
    v = strtoul(f[0], 0, 16); m->sid = (unsigned)v;
    if (strlen(f[1]) != 1 || f[1][0] < '0' || f[1][0] > '9') return 0;
    m->role = f[1][0] - '0';
    {   char *e; long x = strtol(f[2], &e, 10); if (e == f[2] || *e || x < -1 || x > 63) return 0; m->ent = (int)x; }
    {   char *e; unsigned long x; if (!f[3][0] || f[3][0] == '-') return 0; x = strtoul(f[3], &e, 10); if (*e) return 0; m->seq = (unsigned)x; }
    if (!knc_type_ok(f[4])) return 0;
    strcpy(m->type, f[4]);
    knc_sanitize(f[5], m->payload, sizeof m->payload);
    return 1;
}

/* the duplicate filter: -> 1 the first time a (sid, seq) pair is offered, 0 after (a ring of the last KLNC_SEEN pairs) */
struct knc_seen { unsigned sid[KLNC_SEEN], seq[KLNC_SEEN]; int n, at; };
static int knc_seen_new(struct knc_seen *s, unsigned sid, unsigned seq)
{
    int i;
    for (i = 0; i < s->n; i++) if (s->sid[i] == sid && s->seq[i] == seq) return 0;
    s->sid[s->at] = sid; s->seq[s->at] = seq;
    s->at = (s->at + 1) % KLNC_SEEN; if (s->n < KLNC_SEEN) s->n++;
    return 1;
}

/* the replay guard: a sender's highest seq so far; a message more than KLNC_BACK below it is old (a Steam member-data value is read
   again and again and its lines outlive the duplicate ring). -> 1 = take it. Senders past KLNC_HW are not guarded (the ring still is). */
#define KLNC_HW   16
#define KLNC_BACK 8
struct knc_hw { unsigned sid[KLNC_HW], hi[KLNC_HW]; int n; };
static int knc_hw_ok(struct knc_hw *h, unsigned sid, unsigned seq)
{
    int i;
    for (i = 0; i < h->n; i++) if (h->sid[i] == sid) {
        if (seq + KLNC_BACK <= h->hi[i]) return 0;
        if (seq > h->hi[i]) h->hi[i] = seq;
        return 1;
    }
    if (h->n < KLNC_HW) { h->sid[h->n] = sid; h->hi[h->n] = seq; h->n++; }
    return 1;
}

/* the Steam member-data value: the last KLNC_RING packet lines, newest last, joined by KLNC_SEP */
struct knc_ring { char line[KLNC_RING][KLNC_PKT_MAX + 1]; int n; };
static void knc_ring_push(struct knc_ring *r, const char *pkt)
{
    int i;
    if (r->n == KLNC_RING) { for (i = 1; i < KLNC_RING; i++) strcpy(r->line[i - 1], r->line[i]); r->n--; }
    strncpy(r->line[r->n], pkt, KLNC_PKT_MAX); r->line[r->n][KLNC_PKT_MAX] = 0; r->n++;
}
static int knc_ring_join(const struct knc_ring *r, char *out, int cap)
{
    int i, n = 0;
    if (cap <= 0) return 0;
    out[0] = 0;
    for (i = 0; i < r->n; i++) {
        int l = (int)strlen(r->line[i]);
        if (n + l + 2 > cap) break;
        if (n) out[n++] = KLNC_SEP;
        memcpy(out + n, r->line[i], (size_t)l); n += l; out[n] = 0;
    }
    return n;
}
/* split a joined value: calls fn(line, len, ctx) for each line; -> lines seen */
static int knc_ring_split(const char *v, void (*fn)(const char *, int, void *), void *ctx)
{
    int c = 0;
    while (v && *v) {
        const char *e = v; while (*e && *e != KLNC_SEP) e++;
        if (e > v) { fn(v, (int)(e - v), ctx); c++; }
        v = *e ? e + 1 : e;
    }
    return c;
}

#endif
