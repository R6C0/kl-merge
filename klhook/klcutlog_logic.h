/* klcutlog_logic.h - pure logic of [Campaign] CutsceneLog (klcutlog.c): rate limit, signal-edge text, actor-state text, act line text.
 * No game memory, no windows.h: klcutlog_test.c compiles it alone. Everything here only FORMATS what klcutlog.c read.
 * READ-ONLY diagnostic: nothing in this file (or in klcutlog.c) writes into the game.
 */
#ifndef KLCUTLOG_LOGIC_H
#define KLCUTLOG_LOGIC_H
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

/* snprintf that always NUL-terminates; returns the length it wanted (or -1 when the C runtime says truncated) */
static int kcut_f(char *o, int cap, const char *fmt, ...)
{
    va_list a; int k;
    if (cap < 1) return -1;
    va_start(a, fmt); k = vsnprintf(o, (size_t)cap, fmt, a); va_end(a);
    o[cap - 1] = 0;
    return k;
}

/* ---------------------------------------------------------------- rate limit: at most max lines per level, at most perSec per second */
typedef struct { unsigned maxLines, perSec, count, winStart, winCount, skipped; int started, capTold; } kcut_rl;
enum { KCUT_SKIP = 0, KCUT_SAY = 1, KCUT_CAP = 2 };

static int kcut_clamp_max(int v)  { return v < 20 ? 20 : v > 20000 ? 20000 : v; }
static int kcut_clamp_rate(int v) { return v < 1 ? 1 : v > 200 ? 200 : v; }

static void kcut_rl_init(kcut_rl *r, int maxLines, int perSec)
{
    memset(r, 0, sizeof *r);
    r->maxLines = (unsigned)kcut_clamp_max(maxLines); r->perSec = (unsigned)kcut_clamp_rate(perSec);
}
/* a new level: counters back to zero (the limits stay) */
static void kcut_rl_level(kcut_rl *r) { r->count = r->winCount = r->winStart = r->skipped = 0; r->started = r->capTold = 0; }

/* KCUT_SAY: print it. KCUT_CAP: the per-level cap was just reached: print ONE notice (does not use up a line). KCUT_SKIP: silent (counted). */
static int kcut_rl_take(kcut_rl *r, unsigned now)
{
    if (r->count >= r->maxLines) {
        if (!r->capTold) { r->capTold = 1; return KCUT_CAP; }
        r->skipped++; return KCUT_SKIP;
    }
    if (!r->started || now - r->winStart >= 1000u) { r->started = 1; r->winStart = now; r->winCount = 0; }
    if (r->winCount >= r->perSec) { r->skipped++; return KCUT_SKIP; }
    r->winCount++; r->count++;
    return KCUT_SAY;
}

/* ---------------------------------------------------------------- printable copy of a game string (never copies a control or high byte) */
static int kcut_safe_copy(char *dst, int cap, const unsigned char *src, int n)
{
    int i, o = 0;
    if (cap < 1) return 0;
    for (i = 0; i < n && o < cap - 1; i++) {
        if (!src[i]) break;
        dst[o++] = (src[i] >= 0x20 && src[i] < 0x7f) ? (char)src[i] : '?';
    }
    dst[o] = 0;
    return o;
}
/* a path-looking string: starts with '/', at least 4 printable chars before the NUL, no control byte */
static int kcut_looks_like_path(const unsigned char *s, int n)
{
    int i;
    if (n < 5 || s[0] != '/') return 0;
    for (i = 0; i < n; i++) {
        if (!s[i]) return i >= 4;
        if (s[i] < 0x20 || s[i] >= 0x7f) return 0;
    }
    return 0;
}

/* ---------------------------------------------------------------- cutscene-candidate signals (read once per tick, all read-only) */
enum { KCUT_S_HASP, KCUT_S_BLK28, KCUT_S_BLK60, KCUT_S_G4CD8, KCUT_S_G48B0, KCUT_S_SYSBC, KCUT_S_CAMVT, KCUT_S_MOVE, KCUT_S_ABLE, KCUT_S_GS, KCUT_S_N };
typedef struct { unsigned v[KCUT_S_N]; } kcut_sig;
/* GS is a counter-like state (context only): its changes are NOT edges. */
static int kcut_sig_is_edge(int i) { return i != KCUT_S_GS; }
static const char *kcut_sig_name(int i)
{
    static const char *n[KCUT_S_N] = { "player", "blk2728", "blk2760", "gd4cd8", "gd48b0", "sysbc", "camvt", "move", "able", "gs" };
    return i >= 0 && i < KCUT_S_N ? n[i] : "?";
}
/* the changed signals as "name old>new, ..." (hex); returns how many changed (edges only) */
static int kcut_sig_edges(const kcut_sig *p, const kcut_sig *c, char *out, int cap)
{
    int i, n = 0, o = 0;
    if (cap > 0) out[0] = 0;
    for (i = 0; i < KCUT_S_N; i++) {
        if (!kcut_sig_is_edge(i) || p->v[i] == c->v[i]) continue;
        if (o < cap - 1) { int k = kcut_f(out + o, cap - o, "%s%s %x>%x", n ? ", " : "", kcut_sig_name(i), p->v[i], c->v[i]); if (k < 0 || k >= cap - o) { o = cap - 1; out[o] = 0; } else o += k; }
        n++;
    }
    return n;
}
/* the whole signal row as "name=val ..." (context on every line) */
static void kcut_sig_row(const kcut_sig *c, char *out, int cap)
{
    int i, o = 0;
    if (cap > 0) out[0] = 0;
    for (i = 0; i < KCUT_S_N && o < cap - 1; i++) {
        int k = kcut_f(out + o, cap - o, "%s%s=%x", i ? " " : "", kcut_sig_name(i), c->v[i]);
        if (k < 0 || k >= cap - o) { o = cap - 1; out[o] = 0; break; }
        o += k;
    }
}

/* ---------------------------------------------------------------- one actor's weapon/hand state */
typedef struct { unsigned body, bbc, hand, wpn; int ok; } kcut_actor;     /* bbc = [A+0xbbc] (bit 0x100 = holstered by a cutscene act), hand = [A+0x920], wpn = the inventory's weapon for it (0 = none) */
static int kcut_holstered(const kcut_actor *a) { return (a->bbc & 0x100u) != 0; }
static int kcut_actor_changed(const kcut_actor *a, const kcut_actor *b) { return a->bbc != b->bbc || a->hand != b->hand || a->wpn != b->wpn; }
static void kcut_fmt_actor_delta(char *out, int cap, const kcut_actor *a, const kcut_actor *b)
{
    kcut_f(out, cap, "bit100 %d>%d bbc %08x>%08x hand %u>%u wpn %08x>%08x", kcut_holstered(a), kcut_holstered(b), a->bbc, b->bbc, a->hand, b->hand, a->wpn, b->wpn);
}

/* the inventory's weapon for hand index 'hand' (klauto.c kla_hand_weapon, same rule): inv mode byte 0 = entry[hand], else the entry whose dword 0 == hand.
   e = count entries of 4 dwords; dword 2 is the weapon. Returns 0 when none. */
static unsigned kcut_hand_pick(unsigned hand, int invMode, const unsigned *e, unsigned count)
{
    unsigned i;
    if (!hand || hand >= 64 || !e || count > 256) return 0;
    if (!invMode) return hand < count ? e[4 * hand + 2] : 0;
    for (i = 0; i < count; i++) if (e[4 * i] == hand) return e[4 * i + 2];
    return 0;
}

/* ---------------------------------------------------------------- the act executor's weaponhdl modes (0x4d5c20 jump table 0x4d5d64: 1..4) */
static const char *kcut_mode_name(unsigned m)
{
    switch (m) {
    case 0: return "none";
    case 1: return "Holster";            /* 0x4d5c80: 0x5e7c60(A, 1, 0x100): bit 0x100 set */
    case 2: return "Unholster";          /* 0x4d5c95: bit cleared, then the stashed item is selected (klclubholster.c) */
    case 3: return "Mode3";              /* 0x4d5cd6: clears the bit only when 0x566f20(1) finds an item (GUESS: UnholsterSec) */
    case 4: return "Mode4";              /* 0x4d5d1c: clears the bit only when 0x566f20(0) finds an item (GUESS) */
    default: return "unknown";
    }
}

/* EXEC line (0x4d5c20 call): who, which mode, before / after state. has_after = 0 when the return was not hooked. */
static void kcut_fmt_exec(char *out, int cap, unsigned seq, unsigned long tms, unsigned O, unsigned actor, const char *aname,
                          unsigned mode, unsigned lastMode, const kcut_actor *before, const kcut_actor *after, int has_after, int policy_note)
{
    char d[160];
    if (has_after) kcut_fmt_actor_delta(d, sizeof d, before, after);
    else kcut_f(d, sizeof d, "bit100 %d bbc %08x hand %u wpn %08x (after: not hooked)", kcut_holstered(before), before->bbc, before->hand, before->wpn);
    kcut_f(out, cap, "cutlog: EXEC #%u t=%lu.%03lus wh=%08x actor=%08x '%s' weaponhdl=%u(%s) prev=%u | %s%s", seq, tms / 1000ul, tms % 1000ul, O, actor,
                aname && aname[0] ? aname : "?", mode, kcut_mode_name(mode), lastMode, d, policy_note ? " [direct]" : "");
}
/* ACT line (0x4db080 call): the act with its anim id and clip path (path = "" when none could be read) */
static void kcut_fmt_act(char *out, int cap, unsigned seq, unsigned long tms, unsigned act, unsigned owner, unsigned actorId, unsigned animId,
                         const char *clip, unsigned mode, unsigned actor, const char *aname, const kcut_actor *before, const kcut_actor *after, int has_after)
{
    char d[160];
    if (has_after) kcut_fmt_actor_delta(d, sizeof d, before, after);
    else kcut_f(d, sizeof d, "bit100 %d bbc %08x hand %u wpn %08x (after: not hooked)", kcut_holstered(before), before->bbc, before->hand, before->wpn);
    kcut_f(out, cap, "cutlog: ACT #%u t=%lu.%03lus act=%08x owner=%08x id=%u actor=%08x '%s' animid=%d clip='%s' weaponhdl=%u(%s) | %s", seq, tms / 1000ul, tms % 1000ul, act, owner,
                actorId, actor, aname && aname[0] ? aname : "?", (int)(short)animId, clip && clip[0] ? clip : "?", mode, kcut_mode_name(mode), d);
}
/* ACTOR line (polled: an actor's holster bit / hand changed between two ticks) */
static void kcut_fmt_actor_edge(char *out, int cap, unsigned seq, unsigned long tms, unsigned body, const char *aname, int isPlayer,
                                const kcut_actor *a, const kcut_actor *b, const char *row)
{
    char d[160];
    kcut_fmt_actor_delta(d, sizeof d, a, b);
    kcut_f(out, cap, "cutlog: ACTOR #%u t=%lu.%03lus %s%08x '%s' %s | %s", seq, tms / 1000ul, tms % 1000ul, isPlayer ? "player " : "", body, aname && aname[0] ? aname : "?", d, row);
}
static void kcut_fmt_sig_edge(char *out, int cap, unsigned seq, unsigned long tms, const char *edges, const char *row)
{
    kcut_f(out, cap, "cutlog: SIGNAL #%u t=%lu.%03lus %s | %s", seq, tms / 1000ul, tms % 1000ul, edges, row);
}

#endif
