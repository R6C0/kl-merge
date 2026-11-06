/* klnamesprobe_logic.h - the PURE part of klnamesprobe.c ([BotFill] OnlineNamesProbe, LOG ONLY): the per-seat "who is bot digit D" table, an order-independent
 * digest of it, and the log line. No game reads, no windows.h. Checked off-game by klnamesprobe_test.c. Spec: re/parity_gaps_7_8_11_1106.md (section 4).
 *
 * WHY: every online name the owner sees on a bot (HUD crew list, tags over the head, scoreboard AI rows, "KILLED BY") is DERIVED LOCALLY by each peer from the model
 * the bot wears (klonline_read.c klor_char: model root -> the level's wardrobe -> character name). So "do both peers show the same name for bot 5?" is
 * "do both peers hold the same model root for digit 5?", and a 9-seat bench can answer it from the logs alone: the line carries one digest that must be EQUAL on
 * the host and on every client once OnlineLooks=1 has applied. The digest is keyed by the group digit (2..8), not by census order (the order is a GUESS).
 */
#ifndef KLNAMESPROBE_LOGIC_H
#define KLNAMESPROBE_LOGIC_H

#include <stdio.h>
#include <string.h>

#define KLNP_MAXE 16

/* one bot as this peer sees it. digit 0 = unreadable group name; model = the model root ([[actor+4]+0x68]); name = the wardrobe character ("" = none/unknown) */
struct klnp_e { int digit; unsigned long model; char name[32]; };

/* FNV-1a over (digit, model, name) of every entry, entries ORDERED BY DIGIT (then model) first, so two peers that see the same bots in another census order
   get the same value. n <= 0 or e == NULL -> the empty digest 0. A digit-0 entry (unreadable) is included: the digests then differ, which is the point. */
static unsigned long klnp_digest(const struct klnp_e *e, int n)
{
    int idx[KLNP_MAXE], i, j, k; unsigned long h = 2166136261ul;
    if (!e || n <= 0) return 0;
    if (n > KLNP_MAXE) n = KLNP_MAXE;
    for (i = 0; i < n; i++) idx[i] = i;
    for (i = 1; i < n; i++) {      /* insertion sort: digit, then model, then name */
        int t = idx[i];
        for (j = i - 1; j >= 0; j--) {
            const struct klnp_e *a = &e[idx[j]], *b = &e[t];
            int gt = a->digit != b->digit ? a->digit > b->digit : a->model != b->model ? a->model > b->model : strcmp(a->name, b->name) > 0;
            if (!gt) break;
            idx[j + 1] = idx[j];
        }
        idx[j + 1] = t;
    }
    for (i = 0; i < n; i++) {
        const struct klnp_e *p = &e[idx[i]]; const unsigned char *s;
        unsigned long m = p->model;
        h = (h ^ (unsigned long)(p->digit & 0xff)) * 16777619ul;
        for (k = 0; k < 4; k++) { h = (h ^ (m & 0xff)) * 16777619ul; m >>= 8; }
        for (s = (const unsigned char *)p->name; *s; s++) h = (h ^ *s) * 16777619ul;
        h = (h ^ 0xffu) * 16777619ul;      /* name terminator: "ab","c" differs from "a","bc" */
    }
    return h;
}

/* the log text "2=Kane 3=Liam 4=? ..." ordered by digit (unreadable digit prints as '?', no name as '-'). -> bytes written (excluding NUL), always NUL-terminated for cap >= 1 */
static int klnp_list(char *out, int cap, const struct klnp_e *e, int n)
{
    int idx[KLNP_MAXE], i, j, o = 0;
    if (cap < 1) return 0;
    out[0] = 0;
    if (!e || n <= 0) return 0;
    if (n > KLNP_MAXE) n = KLNP_MAXE;
    for (i = 0; i < n; i++) idx[i] = i;
    for (i = 1; i < n; i++) {
        int t = idx[i];
        for (j = i - 1; j >= 0; j--) {
            const struct klnp_e *a = &e[idx[j]], *b = &e[t];
            int gt = a->digit != b->digit ? a->digit > b->digit : a->model > b->model;
            if (!gt) break;
            idx[j + 1] = idx[j];
        }
        idx[j + 1] = t;
    }
    for (i = 0; i < n; i++) {
        const struct klnp_e *p = &e[idx[i]]; char d[4]; int w;
        if (p->digit >= 1 && p->digit <= 9) { d[0] = (char)('0' + p->digit); d[1] = 0; } else { d[0] = '?'; d[1] = 0; }
        w = snprintf(out + o, (size_t)(cap - o), "%s%s=%s", i ? " " : "", d, p->name[0] ? p->name : "-");
        if (w < 0 || w >= cap - o) { out[cap - 1] = 0; return cap - 1; }
        o += w;
    }
    return o;
}

/* when to log: the first time; when the digest changed (a look landed, a bot left the census, a new round) but never twice within `minms`; and a heartbeat every `gap` ms
   so a late-joining reader of the log still finds a line. Wrapping-safe. last_sig/last_at are the caller's state (a change inside `minms` leaves the state alone, so it fires
   later). Returns 1 = log now (and updates the state). *first = 1 until the first line. */
static int klnp_due(unsigned long now, unsigned long sig, unsigned long *last_sig, unsigned long *last_at, int *first, unsigned long minms, unsigned long gap)
{
    long dt;
    if (!last_sig || !last_at || !first) return 0;
    dt = (long)(now - *last_at);
    if (*first || (sig != *last_sig && dt >= (long)minms) || dt >= (long)gap) { *first = 0; *last_sig = sig; *last_at = now ? now : 1; return 1; }
    return 0;
}

#endif /* KLNAMESPROBE_LOGIC_H */
