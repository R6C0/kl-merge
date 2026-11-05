/* klbotvoice_logic.h - the PURE parts of klbotvoice.c ([BotFill] OnlineVoice): the 'KLSYV' packet (host: "bot digit D said event E"), its strict decoder, the
 * sequence rule (drop repeats / stale), the gap limiter and the key builder. No game reads, no windows.h. Checked off-game by klbotvoice_test.c.
 * Spec: re/bot_voice_online_spec.md ("Corrected final spec").
 *
 * KLSYV (little endian, UDP 27415 broadcast from the host, the same socket as KLSYL / KLSYB; an old receiver skips any magic it does not know), 20 bytes
 *    0   8   "KLSYV\0\0\0"
 *    8   u32 T       the host's klsy_T() (ms modulo 1e9)
 *   12   u16 seq     a new value per event (1..65535, wraps past 65535 to 1); the client drops a repeated or older seq
 *   14   u8  ver = 1
 *   15   u8  event   1 = loot grab, 2 = boarded / escaped
 *   16   u8  digit   the bot's group digit 2..8 (klcrewlook.c's key)
 *   17   u8  variant 1..3 (v1 always 1)
 *   18   u16 0
 * The format is a GUESS of this build (nothing else on the wire uses it). */
#ifndef KLBOTVOICE_LOGIC_H
#define KLBOTVOICE_LOGIC_H

#include <stdio.h>
#include <string.h>

#define KLBV_LEN       20
#define KLBV_EV_LOOT   1
#define KLBV_EV_ESCAPE 2
#define KLBV_NEV       3          /* ids 0..2 index the gap table */
#define KLBV_PER_GAP   15000u     /* ms: per bot per event (the game's own group gap is 15 s) */
#define KLBV_GLOBAL_GAP 2000u     /* ms: between any two bot lines */

struct klbv_pk { unsigned T; int seq, ev, digit, var; };

static void klbv_put32(unsigned char *p, unsigned v) { p[0] = (unsigned char)v; p[1] = (unsigned char)(v >> 8); p[2] = (unsigned char)(v >> 16); p[3] = (unsigned char)(v >> 24); }
static unsigned klbv_get32(const unsigned char *p) { return (unsigned)p[0] | (unsigned)p[1] << 8 | (unsigned)p[2] << 16 | (unsigned)p[3] << 24; }

/* bytes written, 0 = refused (cap too small / a field out of range) */
static int klbv_encode(unsigned char *out, int cap, const struct klbv_pk *k)
{
    if (cap < KLBV_LEN || k->seq < 1 || k->seq > 65535 || k->ev < 1 || k->ev >= KLBV_NEV || k->digit < 2 || k->digit > 8 || k->var < 1 || k->var > 3) return 0;
    memset(out, 0, KLBV_LEN);
    memcpy(out, "KLSYV", 5);
    klbv_put32(out + 8, k->T); out[12] = (unsigned char)k->seq; out[13] = (unsigned char)(k->seq >> 8); out[14] = 1; out[15] = (unsigned char)k->ev; out[16] = (unsigned char)k->digit; out[17] = (unsigned char)k->var;
    return KLBV_LEN;
}

/* 1 = a whole, plausible packet; anything short / foreign / out of range gives 0 and *k is not to be used */
static int klbv_decode(const unsigned char *pk, int len, struct klbv_pk *k)
{
    if (!pk || !k || len < KLBV_LEN || memcmp(pk, "KLSYV\0\0\0", 8)) return 0;
    if (pk[14] != 1 || pk[18] || pk[19]) return 0;
    memset(k, 0, sizeof *k);
    k->T = klbv_get32(pk + 8); k->seq = pk[12] | pk[13] << 8; k->ev = pk[15]; k->digit = pk[16]; k->var = pk[17];
    if (k->T >= 1000000000u || k->seq < 1 || k->ev < 1 || k->ev >= KLBV_NEV || k->digit < 2 || k->digit > 8 || k->var < 1 || k->var > 3) return 0;
    return 1;
}

/* the next seq after s (1..65535, 0 is never used) */
static int klbv_next_seq(int s) { return s >= 65535 || s < 1 ? 1 : s + 1; }

/* the client's seq book: held = the newest seq taken, have = 0 until the first. */
struct klbv_seqs { int have, held; unsigned taken, repeats, stale, lost; };

/* 1 = take it (newer than held in 16-bit wrap order, 1..32767 ahead), 0 = a repeat (same seq) or stale (behind). A gap (skipped seqs) adds to lost: the client missed those events. */
static int klbv_seq_take(struct klbv_seqs *q, int seq)
{
    int d;
    if (!q->have) { q->have = 1; q->held = seq; q->taken++; return 1; }
    d = ((seq - q->held) % 65535 + 65535) % 65535;      /* the seqs cycle 1..65535 (0 is never used): the forward distance */
    if (d == 0) { q->repeats++; return 0; }
    if (d >= 32768) { q->stale++; return 0; }
    if (d > 1) q->lost += (unsigned)(d - 1);
    q->held = seq; q->taken++;
    return 1;
}

/* the gap limiter: per (digit, event) and global, in ms of a wrapping 32-bit clock. 1 = may speak now (and records it). */
struct klbv_gaps { unsigned char seen[9][KLBV_NEV]; unsigned last[9][KLBV_NEV]; int gseen; unsigned glast; };

static int klbv_gap_ok(struct klbv_gaps *g, int digit, int ev, unsigned now)
{
    if (digit < 2 || digit > 8 || ev < 1 || ev >= KLBV_NEV) return 0;
    if (g->gseen && (unsigned)(now - g->glast) < KLBV_GLOBAL_GAP) return 0;
    if (g->seen[digit][ev] && (unsigned)(now - g->last[digit][ev]) < KLBV_PER_GAP) return 0;
    g->gseen = 1; g->glast = now; g->seen[digit][ev] = 1; g->last[digit][ev] = now;
    return 1;
}

/* the key from a template: "%L" = the level key (F01), "%D" = the digit. Anything else is copied; "%%" is a '%'. 1 = whole key written, 0 = cap too small. */
static int klbv_key(char *out, int cap, const char *tmpl, const char *level, int digit)
{
    int w = 0; const char *p;
    for (p = tmpl; *p; p++) {
        char tmp[16]; const char *s = tmp; int n;
        if (*p == '%' && p[1] == 'L') { s = level; p++; }
        else if (*p == '%' && p[1] == 'D') { snprintf(tmp, sizeof tmp, "%d", digit); p++; }
        else if (*p == '%' && p[1] == '%') { tmp[0] = '%'; tmp[1] = 0; p++; }
        else { tmp[0] = *p; tmp[1] = 0; }
        n = (int)strlen(s);
        if (w + n >= cap) { if (cap > 0) out[w < cap ? w : cap - 1] = 0; return 0; }
        memcpy(out + w, s, (size_t)n); w += n;
    }
    out[w] = 0;
    return 1;
}

/* OnlineVoiceLeafLoot / OnlineVoiceLeafEsc: the KLVoice leaf of the ByLook path. ovr = the ini text ("" = off). Returns the leaf to use in out (cap bytes):
 * the override when it is a plain leaf name (1..cap-1 chars, no '/', '\\', no control char or space, not edge-blank), else the derived leaf (the digit key minus folder and _C<n>, today's behaviour).
 * 0 = no leaf at all (both empty / too long). *used = 1 when the override won. A bad override is ignored (derived wins) so a typo never silences the line. */
static int klbv_pick_leaf(const char *ovr, const char *derived, char *out, int cap, int *used)
{
    int i, n, ok = 0;
    if (used) *used = 0;
    if (cap < 2) return 0;
    if (ovr && ovr[0]) {
        n = (int)strlen(ovr);
        ok = n < cap;
        for (i = 0; ok && i < n; i++) { unsigned char c = (unsigned char)ovr[i]; if (c <= ' ' || c == '/' || c == '\\' || c == 127) ok = 0; }
        if (ok) { memcpy(out, ovr, (size_t)n + 1); if (used) *used = 1; return 1; }
    }
    if (!derived || !derived[0] || (int)strlen(derived) >= cap) { out[0] = 0; return 0; }
    memcpy(out, derived, strlen(derived) + 1);
    return 1;
}

/* OnlineVoiceProbe (log only; klbotvoice.c): pure helpers for the 0x58a070 speech-group probe. */
#define KLBV_PROBE_CAP 200      /* log lines per round */
/* the speech manager keeps its groups 0x18 apart from mgr+0 (re/bots_voice.md 1.1: lists at +0x00 .. +0x8b8); -1 = group is not at such an offset (then log the raw pointer only) */
static int klbv_probe_group_idx(unsigned long group, unsigned long mgr)
{
    unsigned long off;
    if (!group || !mgr || group < mgr) return -1;
    off = group - mgr;
    if (off >= 0x1000ul || off % 0x18ul) return -1;
    return (int)(off / 0x18ul);
}
/* the speaker byte (third pushed argument): 0..7 a player slot, -2 crew, -6 Glazer; -3 police, -4 driver, -5 undercover are the ASSUMPTION of re/bots_voice.md 1.2. A slot does NOT say bot or human (GUESS: it needs the rules player list). */
static const char *klbv_probe_spk(unsigned long raw)
{
    int b = (int)(signed char)(raw & 0xffu);
    if (b >= 0 && b <= 7) return "slot";
    switch (b) { case -2: return "crew"; case -3: return "police"; case -4: return "driver"; case -5: return "undercover"; case -6: return "glazer"; default: return "?"; }
}
/* the per-round line cap: 1 and count it while *n < cap, else 0 (the call is still counted by the caller) */
static int klbv_probe_take(int *n, int cap)
{
    if (*n < 0 || *n >= cap) return 0;
    (*n)++;
    return 1;
}

/* OnlineVoiceProbe=2: the POLLED, READ-ONLY sampler (klbotvoice.c). Layout from the disassembly of 0x58a070 (11-05): the manager [0x168e958] embeds 94 list objects 0x18 apart (+0x000 .. +0x8b8;
   the 25 single lines start at +0x8d0); a list: +4 count, +0x10 data (array of entry pointers), +0x14 float last-said (game clock, written only when a line really plays; the stock gate is 15.0 s). */
#define KLBV_POLL_GROUPS 94
#define KLBV_POLL_MS 150u      /* poll period (GUESS: 100..250 ms asked; the stock gate is 15 s, so a group changes at most once per 15 s) */
/* a group counts as 'said' when its last-said time changed and is a real time (> 0, not NaN); the baseline sample of a round never counts */
static int klbv_poll_changed(float prev, float cur)
{
    if (cur != cur || prev != prev) return 0;
    return cur > 0.0f && cur != prev;
}
/* a key string copied bounded and printable-only (the key is a char* in the line object, entry +0x18; GUESS: a persistent literal); returns the length */
static int klbv_poll_clean(const char *src, int srclen, char *out, int cap)
{
    int i, n = 0;
    if (cap < 1) return 0;
    for (i = 0; src && i < srclen && n < cap - 1 && src[i]; i++) out[n++] = (src[i] >= 32 && src[i] < 127) ? src[i] : '?';
    out[n] = 0;
    return n;
}
/* the end-of-round summary "idx:count idx:count ..." of the groups with a count; returns the number of groups listed (a cut-off ends with "...") */
static int klbv_poll_summary(char *out, int cap, const int *counts, int n)
{
    int i, len = 0, listed = 0, w;
    if (cap < 8) { if (cap > 0) out[0] = 0; return 0; }
    out[0] = 0;
    for (i = 0; i < n; i++) {
        char tmp[24];
        if (counts[i] <= 0) continue;
        w = sprintf(tmp, "%s%d:%d", len ? " " : "", i, counts[i]);
        if (len + w > cap - 5) { strcpy(out + len, "..."); return listed; }
        memcpy(out + len, tmp, (size_t)w + 1); len += w; listed++;
    }
    return listed;
}

#endif /* KLBOTVOICE_LOGIC_H */
