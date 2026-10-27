/*
 * klmappool_ov.h - the PURE part of the map-pool lobby overlay (klmappool_ov.c): which map is NEXT / PLAYED / waiting, the grid layout, the
 * image file name, the lobby-state gate. No Windows, no game: tested off-game by klmappool_ov_test.c.
 */
#ifndef KLMAPPOOL_OV_H
#define KLMAPPOOL_OV_H

#include <string.h>

#define KMPO_WAIT 0          /* not played yet */
#define KMPO_PLAYED 1        /* already drawn in this cycle: dimmed */
#define KMPO_NEXT 2          /* the map the next round takes (the first unused of the permutation): highlighted */

/* st[i] for the i-th entry of the permutation (order[i] = pool entry index, used[entry] = 1 when played in this cycle).
 * -> the position of the NEXT entry, or -1 when every entry is used (the cycle is spent: the next load starts a new order, so nothing is
 * highlighted and every map shows as waiting - matches kmp_next_entry, which resets 'used' and reshuffles when all are used). */
static int kmpo_states(const int *order, const int *used, int norder, int *st)
{
    int i, next = -1, spent = 1;
    for (i = 0; i < norder; i++) if (!used[order[i]]) { spent = 0; break; }
    for (i = 0; i < norder; i++) {
        if (spent) st[i] = KMPO_WAIT;
        else if (used[order[i]]) st[i] = KMPO_PLAYED;
        else if (next < 0) { next = i; st[i] = KMPO_NEXT; }
        else st[i] = KMPO_WAIT;
    }
    return next;
}

static int kmpo_played(const int *st, int n) { int i, c = 0; for (i = 0; i < n; i++) if (st[i] == KMPO_PLAYED) c++; return c; }

/* columns of the strip: all in one row up to maxcols, then rows of maxcols */
static int kmpo_cols(int n, int maxcols)
{
    if (maxcols < 1) maxcols = 1;
    if (n < 1) return 1;
    return n < maxcols ? n : maxcols;
}
static int kmpo_rows(int n, int cols) { return n < 1 ? 0 : (n + cols - 1) / cols; }

/* top-left of cell i inside the grid (cell pitch = cw + gap, ch + gap) */
static void kmpo_cell(int i, int cols, float cw, float ch, float gap, float *x, float *y)
{
    *x = (float)(i % cols) * (cw + gap); *y = (float)(i / cols) * (ch + gap);
}

/* a pool entry's name -> its image file name: every character outside [A-Za-z0-9_.-] becomes '_' ('stock F03' -> 'stock_F03.kmi');
 * the same rule as tools/kl_mappool.py kmi_name. */
static void kmpo_file(const char *name, char *out, int cap)
{
    int i = 0;
    for (; name[i] && i < cap - 5; i++) {
        char c = name[i];
        out[i] = ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '.' || c == '-') ? c : '_';
    }
    strcpy(out + i, ".kmi");
}

/* the label of a pool; 0 = none */
static const char *kmpo_label(int pool)
{
    return pool == 1 ? "FULL DEAD MEN" : pool == 2 ? "FULL DOG DAYS" : pool == 3 ? "MIX" : "";
}

/* the lobby gate: the session manager's state (sm+0x70) is one of the states in the bit mask (bit n = state n; default 0xd = the lobby) */
static int kmpo_state_shown(unsigned mask, unsigned state) { return state < 32 && ((mask >> state) & 1u) != 0; }

/* the tint (ARGB) a thumbnail is drawn with */
static unsigned kmpo_tint(int st)
{
    return st == KMPO_PLAYED ? 0x80606060u : st == KMPO_NEXT ? 0xffffffffu : 0xffc8c8c8u;
}

/* the panel position: x / y are percent of the screen, clamped so the whole panel stays on the screen */
static void kmpo_place(int sw, int sh, float pw, float ph, int xpct, int ypct, float *ox, float *oy)
{
    float x = (float)sw * (float)xpct / 100.0f, y = (float)sh * (float)ypct / 100.0f;
    if (x + pw > (float)sw) x = (float)sw - pw;
    if (y + ph > (float)sh) y = (float)sh - ph;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    *ox = x; *oy = y;
}

#endif
