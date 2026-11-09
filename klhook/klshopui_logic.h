/* klshopui_logic.h - [ShopPage] TidyPage2 / [Hire] TidyPage: the PURE text and decision rules that make page II and the HIRE page easier to read and navigate.
   Included by klshoppage.c and klshopui_test.c. No game memory, no log, no windows.h. Written 2026-11-08 for the owner's ask 'make the store ui nicer for page 2 and heisters
   to hire, it still looks somewhat bad to navigate'. NOT RUN IN THE GAME: every width is the klfit_logic.h GUESS (row 16, tab 14) plus one more GUESS below.
   The description pane shows the name, ONE body line, then '...' (SHOTS3 11-01): so the FIRST line of every description built here is the useful one (KSU_LINE1_MAX characters,
   GUESS: about 40 fit the pane at 640x480; 'DOG DAYS CREW. HIRED FOR ONE ROUND.' = 35 did). Everything else follows after a newline.
   Page II before: rows named like stock, line 1 'Police reg.: 2062-II62', tabs 'PISTOLS II'.  After: 'PD2 PAR', line 1 'PD2 GUN: same price and rank', tabs named for the content.
   Hire before: line 1 a 58-character instruction, 'Ashkanan' (price dropped), stars = rank need although nothing is gated.  After: line 1 '$45,000 - BUY twice to hire', rows 'Name  $45K'. */
#ifndef KLSHOPUI_LOGIC_H
#define KLSHOPUI_LOGIC_H

#include <ctype.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "klfit_logic.h"

#define KSU_LINE1_MAX 40   /* GUESS: characters of the first description line that show before the '...' */

/* the set types of klshopset.h kss_type: 0 pd2, 1 dm, 2 stock, 3 other */
static const char *ksu_set_caption(int type)       /* the page II name in the caption (replaces the hard-coded 'PD2 GUNS') */
{
    return type == 0 ? "PD2 GUNS" : type == 1 ? "DEAD MEN GUNS" : "PAGE II";
}
static const char *ksu_gun_tag(int type)           /* the prefix of a new gun's row name */
{
    return type == 0 ? "PD2 " : type == 1 ? "DM " : "";
}

/* caption tag after the page name, offline: '(13 NEW)'. n <= 0 = no tag */
static void ksu_p2_tag(char *out, size_t cap, int n)
{
    if (!cap) return;
    if (n > 0) snprintf(out, cap, "(%d NEW)", n); else out[0] = 0;
}

/* a page II row name of a replaced row: 'PD2 PAR'; cut to maxch at a whole word (KFIT_ROW_MAX) */
static void ksu_p2_name(char *out, size_t cap, const char *name, int type, size_t maxch)
{
    const char *tag = ksu_gun_tag(type);
    size_t tl = strlen(tag);
    if (!cap) return;
    if (tl && strncmp(name, tag, tl) == 0) snprintf(out, cap, "%s", name);   /* already tagged by the ini author: never 'PD2 PD2 PAR' */
    else snprintf(out, cap, "%s%s", tag, name);
    kfit_cut(out, cap, maxch);
}

/* tab names of page II for the PD2 set, used only when KLShopPage.ini [Tabs] has none (GUESS: the headline keys are re-asked after the toggle; 11-01 shots show them unchanged, so this
   may be invisible - harmless then). '' = keep the stock text + ' II'. t = 0 pistol, 1 shotgun, 2 smg, 3 rifle; every name <= KFIT_TAB_MAX */
static const char *ksu_tab_default(int type, int t)
{
    static const char *const pd2[4] = { "PISTOLS+SHIELD", "SHOTGUN+LAUNCH", "SMG+LMG", "RIFLE+SNIPER" };
    return (type == 0 && t >= 0 && t < 4) ? pd2[t] : "";
}

/* split off the first line of s: line 1 -> l1 (cap), returns the rest (after the newline, or "" ) */
static const char *ksu_line1(const char *s, char *l1, size_t cap)
{
    const char *nl = strchr(s, '\n');
    size_t n = nl ? (size_t)(nl - s) : strlen(s);
    if (!cap) return nl ? nl + 1 : s + n;
    if (n >= cap) n = cap - 1;
    memcpy(l1, s, n); l1[n] = 0;
    return nl ? nl + 1 : s + strlen(s);
}

static int ksu_starts_ci(const char *s, const char *pre)
{
    for (; *pre; s++, pre++) if (tolower((unsigned char)*s) != tolower((unsigned char)*pre)) return 0;
    return 1;
}

/* a page II description: the fake 'Police reg.: ...' first line (the only line that showed) moves to the end, a useful line goes first.
   A description whose line 1 is not a registration line was written with a real first line: kept as it is. */
static void ksu_p2_desc(char *out, size_t cap, const char *desc, int type)
{
    char l1[160]; const char *rest;
    if (!cap) return;
    rest = ksu_line1(desc, l1, sizeof l1);
    if (!ksu_starts_ci(l1, "police reg")) { snprintf(out, cap, "%s", desc); return; }
    snprintf(out, cap, "%s: price + rank of the stock gun%s%s%s%s", type == 0 ? "PD2 GUN" : type == 1 ? "DM GUN" : "NEW GUN",
             *rest ? "\n" : "", rest, "\n", l1);
}

/* the online page II description: gun first, then the short note, then the rest of the body (RowFit/Tidy; the pane shows one line) */
static void ksu_online_desc(char *out, size_t cap, const char *body, const char *note)
{
    char l1[160]; const char *rest;
    if (!cap) return;
    rest = ksu_line1(body, l1, sizeof l1);
    snprintf(out, cap, "%s\n%s%s%s", l1, note, *rest ? "\n" : "", rest);
}

/* ---------------------------------------------------------------- HIRE PAGE */

/* '45000' -> '$45,000' */
static void ksu_money_full(char *out, size_t cap, long v)
{
    char d[24]; int n, i, k = 0;
    if (cap < 20) { if (cap) out[0] = 0; return; }
    if (v < 0) v = 0;
    snprintf(d, sizeof d, "%ld", v); n = (int)strlen(d);
    out[k++] = '$';
    for (i = 0; i < n; i++) { if (i && (n - i) % 3 == 0) out[k++] = ','; out[k++] = d[i]; }
    out[k] = 0;
}
/* '$45K' for a whole thousand below a million, else the full '$45,500' */
static void ksu_money_short(char *out, size_t cap, long v)
{
    if (cap < 20) { if (cap) out[0] = 0; return; }
    if (v >= 1000 && v % 1000 == 0 && v < 1000000L) snprintf(out, cap, "$%ldK", v / 1000);
    else ksu_money_full(out, cap, v);
}

enum { KSU_ROW_PRICE = 0, KSU_ROW_HIRED = 1, KSU_ROW_NA = 2 };

/* a hire row at maxch: 'NAME  $45K' / 'NAME  HIRED' / 'NAME  n/a'. Too wide: one space, then the state word alone (price dropped), then a whole-word cut.
   price < 0 = no price shown ([Hire] PagePrice=0). */
static void ksu_hire_row(char *out, size_t cap, const char *name, long price, int state, size_t maxch)
{
    char w[24], t[96];
    if (!cap) return;
    w[0] = 0;
    if (state == KSU_ROW_HIRED) strcpy(w, "HIRED");
    else if (state == KSU_ROW_NA) strcpy(w, "n/a");
    else if (price >= 0) ksu_money_short(w, sizeof w, price);
    snprintf(t, sizeof t, "%s%s%s", name, w[0] ? "  " : "", w);
    if (strlen(t) > maxch) snprintf(t, sizeof t, "%s%s%s", name, w[0] ? " " : "", w);
    if (strlen(t) > maxch && state == KSU_ROW_PRICE) snprintf(t, sizeof t, "%s", name);
    if (strlen(t) > maxch && state != KSU_ROW_PRICE && maxch > strlen(w) + 3) {   /* keep the state word: cut the name, then ' HIRED' / ' n/a' */
        char nm[96]; snprintf(nm, sizeof nm, "%s", name); kfit_cut(nm, sizeof nm, maxch - strlen(w) - 1);
        snprintf(t, sizeof t, "%s %s", nm, w);
    }
    kfit_cut(t, sizeof t, maxch);
    snprintf(out, cap, "%s", t);
}

enum { KSU_H_READY = 0, KSU_H_HIRED, KSU_H_OTHER, KSU_H_NOMAP, KSU_H_WAIT, KSU_H_ARM, KSU_H_REFUSED, KSU_H_LOWRANK };

/* the first description line of a hire row (<= KSU_LINE1_MAX): the state, with the price where it helps. other = the heister already hired, msg = the last refusal */
static void ksu_hire_line1(char *out, size_t cap, int state, long price, int need, int gate, int confirm, const char *other, const char *msg)
{
    char m[24], t[160];
    ksu_money_full(m, sizeof m, price);
    switch (state) {
    case KSU_H_HIRED:   snprintf(t, sizeof t, "HIRED for the next round"); break;
    case KSU_H_OTHER:   snprintf(t, sizeof t, "You hired %s: one per round", other ? other : "another"); break;
    case KSU_H_NOMAP:   snprintf(t, sizeof t, "NOT ON THIS MAP (no wardrobe)"); break;
    case KSU_H_WAIT:    snprintf(t, sizeof t, "WAITING for the host..."); break;
    case KSU_H_ARM:     snprintf(t, sizeof t, "BUY AGAIN to hire: %s", m); break;
    case KSU_H_REFUSED: snprintf(t, sizeof t, "REFUSED: %s", msg ? msg : "no"); break;
    case KSU_H_LOWRANK: snprintf(t, sizeof t, "RANK TOO LOW: needs rank %d", need); break;
    default:
        if (gate) snprintf(t, sizeof t, "%s, rank %d - %s", m, need, confirm ? "BUY twice" : "BUY to hire");
        else snprintf(t, sizeof t, "%s - %s", m, confirm ? "BUY twice to hire" : "press BUY to hire");
    }
    kfit_cut(t, sizeof t, KSU_LINE1_MAX);
    snprintf(out, cap, "%s", t);
}

/* the whole hire description: line 1, the bio, then the rank facts only with a rank gate (line 1 already carries the price;
   the 11-09 look bench showed 'Price $90,000, rank 2 needed (no rank gate)' repeating it). rankText = 'your rank 2' / 'your rank unknown' */
static void ksu_hire_desc(char *out, size_t cap, const char *line1, const char *bio, int need, int gate, const char *rankText)
{
    if (gate) snprintf(out, cap, "%s\n%s\nNeeds rank %d (%s).", line1, bio, need, rankText);
    else snprintf(out, cap, "%s\n%s", line1, bio);
}

/* the stars of a hire row: with no rank gate they would show a rank need that is not enforced: hidden (idx 99). Gate on: the need (-1 lit / 99 dim), as before.
   tidy = [Hire] TidyPage. Returns the PlayerIndex to write. */
static long ksu_star_idx(int tidy, int gate, long idx, int need)
{
    if (tidy && !gate) return 99;
    return (idx >= 0 && idx < need) ? -1L : 99L;
}
/* lock icons of the hire page are the carrier GUN's: with TidyPage always hidden; before only without a gate or on the controls page */
static int ksu_lock_hidden(int tidy, int ctl, int gate)
{
    return ctl || !gate || tidy;
}

#endif /* KLSHOPUI_LOGIC_H */
