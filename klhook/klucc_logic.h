/* klucc_logic.h - the PURE parts of klucc.c ([Ucc] suspicion messages in Undercover Cop: the host's random fake pings and the heisters'
 * accuse key; re/ucc_design.md P5 + OWNER DECISIONS 6). No game reads: klucc.c feeds it numbers. Checked off-game by klnc_test.c.
 * Units: game units (100 = 1 m, Y up: re/climb.md 302), times ms (GetTickCount). */
#ifndef KLUCC_LOGIC_H
#define KLUCC_LOGIC_H

#include <string.h>
#include <stdio.h>
#include <math.h>

#define KLUC_N        32           /* session player table entries considered (klcharonline.c KLCO_N) */
#define KLUC_NAME     32           /* a player's name, incl. the 0 */
#define KLUC_TEXT     120          /* one shown line, incl. the 0 */
#define KLUC_RL       16           /* senders remembered by the accusation rate limit */
#define KLUC_KEY_DEBOUNCE 150

/* The window: a network session (role 2 host or 3 client) of game type 4 whose sub-mode word [0x168e59c] is 1 (Undercover Cop), in the
   PLAY part of a round: state 0x19 (GO, re/open_work_log 2026-10-23) up to but not 0x1f (round over). GUESS: 0x19..0x1e is play (B2: rounds
   ran 'from state 25 to 31'). */
static int kluc_gate(unsigned long role, unsigned long mode, unsigned long state, unsigned long submode)
{
    return (role == 2 || role == 3) && mode == 4 && submode == 1 && state >= 0x19 && state < 0x1f;
}

/* xorshift32; a zero state is replaced so it never sticks at 0 */
static unsigned kluc_rand(unsigned *s)
{
    unsigned x = *s ? *s : 0x9e3779b9u;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    *s = x;
    return x;
}

/* ini seconds -> the clamped pair: min 10..600, max min..900 */
static void kluc_ping_range(int minS, int maxS, int *lo, int *hi)
{
    if (minS < 10) minS = 10; if (minS > 600) minS = 600;
    if (maxS < minS) maxS = minS; if (maxS > 900) maxS = 900;
    *lo = minS; *hi = maxS;
}
/* the wait before the next ping, ms, uniform in [lo, hi] seconds */
static unsigned long kluc_next_ms(unsigned *rng, int lo, int hi)
{
    unsigned span = (unsigned)(hi - lo) * 1000u + 1u;
    return (unsigned long)lo * 1000ul + (unsigned long)(kluc_rand(rng) % span);
}
/* one of n (n >= 1), -1 for n <= 0 */
static int kluc_pick(unsigned *rng, int n) { return n <= 0 ? -1 : (int)(kluc_rand(rng) % (unsigned)n); }

/* A candidate body for the accuse key: its table index and its CHEST (feet + KLUC_CHEST in y) */
#define KLUC_CHEST 130.0f
#define KLUC_EYE   160.0f
struct kluc_body { int ent; float p[3]; };

/* The aimed body: among bodies within maxRange of the eye (and farther than 0.5 m), the one with the smallest angle between the ray
   eye->aim and eye->body, if that angle's cosine is >= cosCone. -> index into b[], or -1. A ray shorter than 1 unit or a NaN = -1. */
static int kluc_aim_pick(const float eye[3], const float aim[3], const struct kluc_body *b, int n, float cosCone, float maxRange)
{
    float d[3], dl, best = -2.0f; int i, k = -1;
    d[0] = aim[0] - eye[0]; d[1] = aim[1] - eye[1]; d[2] = aim[2] - eye[2];
    dl = (float)sqrt((double)(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]));
    if (!(dl >= 1.0f)) return -1;
    for (i = 0; i < n; i++) {
        float v[3], vl, c;
        v[0] = b[i].p[0] - eye[0]; v[1] = b[i].p[1] - eye[1]; v[2] = b[i].p[2] - eye[2];
        vl = (float)sqrt((double)(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]));
        if (!(vl >= 50.0f) || vl > maxRange) continue;
        c = (d[0] * v[0] + d[1] * v[1] + d[2] * v[2]) / (dl * vl);
        if (c >= cosCone && c > best) { best = c; k = i; }
    }
    return k;
}
/* The nearest body within maxRange (no aim point known). -> index or -1 */
static int kluc_nearest(const float eye[3], const struct kluc_body *b, int n, float maxRange)
{
    int i, k = -1; float best = 0;
    for (i = 0; i < n; i++) {
        float v0 = b[i].p[0] - eye[0], v1 = b[i].p[1] - eye[1], v2 = b[i].p[2] - eye[2], d2 = v0 * v0 + v1 * v1 + v2 * v2;
        if (!(d2 >= 0) || d2 > maxRange * maxRange) continue;
        if (k < 0 || d2 < best) { best = d2; k = i; }
    }
    return k;
}

/* Per-sender rate limit (the receivers' half; the sender keeps its own cooldown). -> 1 and the time noted when sid may speak now */
struct kluc_rl { unsigned sid[KLUC_RL]; unsigned long at[KLUC_RL]; int n, next; };
static int kluc_rl_ok(struct kluc_rl *r, unsigned sid, unsigned long now, unsigned long gap)
{
    int i;
    for (i = 0; i < r->n; i++) if (r->sid[i] == sid) {
        if (now - r->at[i] < gap) return 0;
        r->at[i] = now ? now : 1; return 1;
    }
    i = r->n < KLUC_RL ? r->n++ : (r->next++ % KLUC_RL);
    r->sid[i] = sid; r->at[i] = now ? now : 1;
    return 1;
}
/* the sender's own cooldown: -> ms still to wait (0 = may accuse now). last 0 = never */
static unsigned long kluc_wait_left(unsigned long last, unsigned long now, unsigned long gap)
{
    if (!last || now - last >= gap) return 0;
    return gap - (now - last);
}

/* key edge: once per press, no repeat while held, debounced */
struct kluc_key { int was_down; unsigned long at; };
static int kluc_edge(struct kluc_key *k, int down, unsigned long now)
{
    int fire = 0;
    if (down && !k->was_down && (!k->at || now - k->at >= KLUC_KEY_DEBOUNCE)) { fire = 1; k->at = now ? now : 1; }
    k->was_down = down ? 1 : 0;
    return fire;
}

/* a name fit to show: printable ASCII, no '|' (the HELLO separator), trimmed, at most KLUC_NAME-1; empty -> "Player <ent+1>" */
static void kluc_clean_name(const char *in, int ent, char *out)
{
    int n = 0, i;
    if (in) for (; *in && n < KLUC_NAME - 1; in++) { unsigned char c = (unsigned char)*in; if (c >= 0x20 && c < 0x7f && c != '|') out[n++] = (char)c; }
    while (n && out[n - 1] == ' ') n--;
    out[n] = 0;
    for (i = 0; out[i] == ' '; i++) ;
    if (i) memmove(out, out + i, (size_t)(n - i + 1));
    if (!out[0]) snprintf(out, KLUC_NAME, "Player %d", ent + 1);
}

/* HELLO payload "<ent>|<name>" */
static int kluc_hello_parse(const char *p, int *ent, char name[KLUC_NAME])
{
    int e = -1, used = 0;
    if (!p || sscanf(p, "%d%n", &e, &used) != 1 || p[used] != '|' || e < 0 || e >= KLUC_N) return 0;
    kluc_clean_name(p + used + 1, e, name);
    *ent = e;
    return 1;
}

/* the lines (the host picks the variant, every peer shows the host's finished text) */
#define KLUC_PING_VARIANTS 5
static void kluc_ping_text(int variant, const char *name, char *out, int cap)
{
    static const char *const f[KLUC_PING_VARIANTS] = {
        "Word is %s is working with the cops",
        "Someone saw %s talking into a radio",
        "%s is acting suspicious",
        "%s was seen near a police car",
        "Watch %s. Something is off",
    };
    snprintf(out, cap, f[((variant % KLUC_PING_VARIANTS) + KLUC_PING_VARIANTS) % KLUC_PING_VARIANTS], name);
}
static void kluc_accuse_text(const char *who, const char *whom, char *out, int cap) { snprintf(out, cap, "%s suspects %s", who, whom); }

#endif
