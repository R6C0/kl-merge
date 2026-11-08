/*
 * klreverbbox_logic.h - pure part of [Echo] RoomBoxes (klecho.c, 2026-11-08): the table of reverb boxes of one map, "is the hero inside this
 * oriented box", and which box wins. No windows.h. Off-game self-test: klreverbbox_test.c (picked up by tools/kl_tests.py).
 *
 * WHY: in Fragile Alliance every stock CCheckInside reverb box ends itself at load (re/reverb_path_1108.md), so the engine's reverb stack stays
 * empty. klhook tests the local hero against the boxes of the map itself and pushes / removes ONE stack entry (the winner) through the
 * engine's own AUD::Push / AUD::Remove (klecho.c does the calls; this file only decides).
 *
 * TABLE (KLReverbBoxes.ini, written by tools/kl_reverb_boxes.py; text, one file for every map):
 *     ; comment (also '#')
 *     [f01\f01_main]                        section = the map: a stock level's scene key (lower case, as klh_level_key), or the lower-case
 *                                           folder of an expansion map (KLExpansion\Maps\DM02\ -> [dm02])
 *     box cx cy cz hx hy hz q0 q1 q2 q3 q4 q5 q6 q7 q8 snd prio  ; box name
 * cx..cz = the box centre in world units, hx..hz = half extents along the box's own axes, q = the 3x3 world->local rotation, row-major
 * (local_i = sum_j q[3i+j] * (p_j - c_j); identity for an axis-aligned box), snd = the SND offset of the roomeffect (Audio_ReverbActivater
 * field 0, valid only for that map's .SND), prio = Audio_ReverbActivater field 3 (the engine's stack top is the HIGHEST priority).
 * A section with no 'box' line is a map that is known to have none.
 */
#ifndef KLREVERBBOX_LOGIC_H
#define KLREVERBBOX_LOGIC_H

#include <stdlib.h>
#include <string.h>

#define KLRB_MAX 96                                    /* boxes per map (the stock maps have 16..19; a 20-entry stack in the engine) */
#define KLRB_KEY 0x4b00u                               /* our stack keys are KLRB_KEY + index: below 0x10000, so never a real object pointer (stock keys are the box's pointer) */

struct klrb_box { float c[3], h[3], q[9]; unsigned snd; float prio; };

static int klrb_lc(int ch) { return ch >= 'A' && ch <= 'Z' ? ch + 32 : ch; }

/* up to n numbers from s (skipping blanks); returns how many were read, *end = where it stopped */
static int klrb_nums(const char *s, double *v, int n, const char **end)
{
    int k = 0; char *e;
    while (k < n) {
        while (*s == ' ' || *s == '\t') s++;
        if (!*s || *s == ';' || *s == '#' || *s == '\r' || *s == '\n') break;
        v[k] = strtod(s, &e);
        if (e == s) break;
        k++; s = e;
    }
    *end = s;
    return k;
}

/* one line: 1 = a 'box' line parsed into *b, 0 = anything else (a comment, a header, a bad line: bad = -1) */
static int klrb_parse_line(const char *line, struct klrb_box *b)
{
    double v[17]; const char *e; int i;
    while (*line == ' ' || *line == '\t') line++;
    if (strncmp(line, "box", 3) || (line[3] != ' ' && line[3] != '\t')) return 0;
    if (klrb_nums(line + 3, v, 17, &e) != 17) return -1;
    for (i = 0; i < 3; i++) { b->c[i] = (float)v[i]; b->h[i] = (float)v[3 + i]; }
    for (i = 0; i < 9; i++) b->q[i] = (float)v[6 + i];
    if (v[15] < 0 || v[15] > 4294967295.0) return -1;
    b->snd = (unsigned)v[15]; b->prio = (float)v[16];
    for (i = 0; i < 3; i++) if (!(b->h[i] >= 0.0f)) return -1;   /* also rejects NaN */
    return 1;
}

/* '[key]' -> 1 and key lower-cased (blanks inside the brackets cut); else 0 */
static int klrb_section(const char *line, char *key, int cap)
{
    int n = 0;
    while (*line == ' ' || *line == '\t') line++;
    if (*line != '[') return 0;
    line++;
    while (*line == ' ' || *line == '	') line++;
    while (*line && *line != ']' && *line != '\r' && *line != '\n' && n < cap - 1) key[n++] = (char)klrb_lc((unsigned char)*line++);
    if (*line != ']') return 0;
    while (n > 0 && (key[n - 1] == ' ' || key[n - 1] == '\t')) n--;
    key[n] = 0;
    return 1;
}

/* the boxes of section 'key' (any case) in the table text; returns the count (at most cap), *found = 1 when the section exists, *bad = lines that did not parse */
static int klrb_load(const char *text, const char *key, struct klrb_box *out, int cap, int *found, int *bad)
{
    char want[160], sec[160], line[400]; int n = 0, in = 0, i, r;
    for (i = 0; key[i] && i < (int)sizeof want - 1; i++) want[i] = (char)klrb_lc((unsigned char)key[i]);
    want[i] = 0;
    *found = 0; *bad = 0;
    while (*text) {
        int len = 0;
        while (text[len] && text[len] != '\n') len++;
        if (len >= (int)sizeof line) len = (int)sizeof line - 1;   /* an over-long line is cut (and then fails to parse) */
        memcpy(line, text, (size_t)len); line[len] = 0;
        text += len; while (*text && *text != '\n') text++;       /* skip the rest of a cut line */
        if (*text == '\n') text++;
        if (klrb_section(line, sec, sizeof sec)) { in = !strcmp(sec, want); if (in) *found = 1; continue; }
        if (!in) continue;
        if (n < cap) {
            r = klrb_parse_line(line, &out[n]);
            if (r == 1) n++; else if (r < 0) (*bad)++;
        }
    }
    return n;
}

/* is p inside the oriented box? margin > 0 widens every half extent, margin < 0 shrinks it (at most to half of it) */
static int klrb_inside(const struct klrb_box *b, const float p[3], float margin)
{
    float d[3], l, e; int i;
    for (i = 0; i < 3; i++) d[i] = p[i] - b->c[i];
    for (i = 0; i < 3; i++) {
        l = b->q[3 * i] * d[0] + b->q[3 * i + 1] * d[1] + b->q[3 * i + 2] * d[2];
        e = b->h[i] + margin;
        if (margin < 0 && e < 0.5f * b->h[i]) e = 0.5f * b->h[i];
        if (!(l <= e && l >= -e)) return 0;                 /* NaN is outside */
    }
    return 1;
}

struct klrb_st { unsigned char in[KLRB_MAX], tog[KLRB_MAX]; unsigned long chg[KLRB_MAX]; int cur; };

static void klrb_reset(struct klrb_st *s) { memset(s, 0, sizeof *s); s->cur = -1; }

static float klrb_vol(const struct klrb_box *b) { return b->h[0] * b->h[1] * b->h[2]; }

/* One look at the hero's place. Per box: enter when inside the box shrunk by 'margin', leave when outside the box widened by 'margin', and after
   a change that box holds its state for hold_ms (a box edge never flaps). usable[i] == 0 takes box i out (no effect to push). Returns the WINNER:
   the highest priority among the boxes the hero is in; equal priority keeps the current winner, else the smaller box (the more specific room),
   else the lower index; -1 = in none. s->cur is the winner after the call. */
static int klrb_update(struct klrb_st *s, const struct klrb_box *b, int n, const float p[3], unsigned long now, float margin, unsigned long hold_ms,
                       const unsigned char *usable)
{
    int i, best = -1;
    if (n > KLRB_MAX) n = KLRB_MAX;
    for (i = 0; i < n; i++) {
        int want;
        if (usable && !usable[i]) { s->in[i] = 0; continue; }
        want = klrb_inside(&b[i], p, s->in[i] ? margin : -margin);
        if (want != s->in[i] && (!s->tog[i] || now - s->chg[i] >= hold_ms)) { s->in[i] = (unsigned char)want; s->tog[i] = 1; s->chg[i] = now; }
    }
    for (i = 0; i < n; i++) {
        if (!s->in[i]) continue;
        if (best < 0 || b[i].prio > b[best].prio) { best = i; continue; }
        if (b[i].prio == b[best].prio) {
            if (best == s->cur) continue;
            if (i == s->cur || klrb_vol(&b[i]) < klrb_vol(&b[best])) best = i;
        }
    }
    s->cur = best;
    return best;
}

/* The map id of a level archive path: "...\Maps\DM02\F02_Main.zip" (either slash, any case) -> "dm02" (1); a stock "...\Scenes\Locations\F02\F02_Main.zip" -> "" (0:
   the table is then keyed by the scene key instead). Only the folder two levels up is checked to be 'maps', so [Expansion] Root can be renamed. */
static int klrb_map_id(const char *path, char *id, int cap)
{
    const char *s[3] = { 0, 0, 0 }, *p; int k, n, len;
    id[0] = 0;
    for (p = path; *p; p++) if (*p == '\\' || *p == '/') { s[0] = s[1]; s[1] = s[2]; s[2] = p; }   /* the last three separators */
    if (!s[0] || !s[1] || !s[2]) return 0;
    len = (int)(s[2] - s[1]) - 1;                                  /* folder = between separators 2 and 3 */
    if (len <= 0 || len >= cap || (int)(s[1] - s[0]) - 1 != 4) return 0;
    for (k = 0, n = 0; k < 4; k++) n += klrb_lc((unsigned char)s[0][1 + k]) == "maps"[k];
    if (n != 4) return 0;
    for (k = 0; k < len; k++) id[k] = (char)klrb_lc((unsigned char)s[1][1 + k]);
    id[len] = 0;
    return 1;
}

#endif /* KLREVERBBOX_LOGIC_H */
