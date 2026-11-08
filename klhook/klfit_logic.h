/* klfit_logic.h - [Keys] CaptionTidy / CaptionMax / RowFit: the PURE text-fitting rules of the shop pages (no game memory, no log, no windows.h).
   Included by klshoppage.c and klfit_test.c. Written 2026-11-07 for the owner's ask 'make the UI more neater, text and stuff overlaps on the menu dropdown and it still seems a bit
   confusing to someone who wouldnt know' (NOT RUN IN THE GAME; every width below is a GUESS read off the 640x480 SHOTS1 screenshots, to be calibrated live).
   The shop's caption (key BuyWeapons_Title) is ONE line: our text, then the game's own ' | RANK n: NAME' (17 to 24 characters), and 'TOTAL: $...' right-aligned in the same bar.
   Before: up to four appended segments ('[P] page II', '[F3] hire', '[F2] next: Page II', 'HIRE HEISTER  [F3] stock') with guards of 420 / 440 characters, five names for the same pages.
   Now: base + at most CaptionMax added characters, one page-name table, a 'PAGE n/N' position, the next page; the lowest-priority piece is dropped first. */
#ifndef KLFIT_LOGIC_H
#define KLFIT_LOGIC_H

#include <stddef.h>
#include <stdio.h>
#include <string.h>

#define KFIT_CAPTION_TOTAL   56        /* GUESS: about 80 characters fit the caption box (SHOTS1) minus the game's ' | RANK 10: DESPERADO' suffix (24): base + added stay under this */
#define KFIT_CAPTION_DEFAULT 40        /* GUESS: [Keys] CaptionMax default when the ini key is missing (the 5.2 px / capital estimate leaves 40 to 45 characters) */
#define KFIT_ROW_MAX         16        /* GUESS: row width in characters (SHOTS3 11-01: 25 characters hid behind the highlight bar, 15 fit) */
#define KFIT_TAB_MAX         14        /* GUESS: category tab width */
#define KFIT_NPAGE           5

/* the ONE page-name table, in the cycle key's page ids (kspg_cur): 0 stock / set A, 1 page II (set B), 2 hire, 3 controls, 4 bots and modes */
static const char *kfit_pname[KFIT_NPAGE]   /* not const: klshoppage.c TidyPage2 swaps entry 1 for the set label around one caption build */ = { "STOCK", "PD2 GUNS", "HIRE", "CONTROLS", "MODES" };

/* cut buf to at most maxch characters at a whole word, '..' appended ONLY when something was cut (so the result never exceeds maxch and a second cut changes nothing).
   A single word longer than maxch is cut hard. maxch < 3 cuts hard without dots. cap = the buffer size. -> 1 = cut, 0 = untouched */
static int kfit_cut(char *buf, size_t cap, size_t maxch)
{
    size_t n, keep, k;
    if (!buf || !cap) return 0;
    if (maxch >= cap) maxch = cap - 1;
    n = strlen(buf);
    if (n <= maxch) return 0;
    if (maxch < 3) { buf[maxch] = 0; return 1; }
    keep = maxch - 2;                                   /* room for '..' */
    for (k = keep; k > 0 && buf[k] != ' '; k--) ;       /* the last space at or before the cut: buf[k] == ' ' means buf[0..k-1] is whole words */
    if (k > 0) keep = k;
    while (keep > 0 && buf[keep - 1] == ' ') keep--;
    buf[keep] = '.'; buf[keep + 1] = '.'; buf[keep + 2] = 0;
    return 1;
}

/* the added-characters budget of one caption: min(CaptionMax, what is left after the base inside KFIT_CAPTION_TOTAL); never below 8 */
static size_t kfit_budget(int captionMax, size_t baseLen)
{
    long m = captionMax > 0 ? captionMax : KFIT_CAPTION_DEFAULT, left = (long)KFIT_CAPTION_TOTAL - (long)baseLen;
    if (left < m) m = left;
    return m < 8 ? 8u : (size_t)m;
}

/* one caption piece list at a given shrink level: 0 = everything, 1 = 'next:' dropped, 2 = 'PAGE n/N' dropped too, 3 = page name dropped too (keys only). add receives the text after the base */
static void kfit_pieces(char *add, size_t cap, int level, int page, int pos, int npages, const char *tag,
                        const char *cycKey, int nextPage, const char *p2Key, const char *hireKey)
{
    size_t l = 0;
    int hasCyc = cycKey && cycKey[0] && nextPage >= 0 && nextPage < KFIT_NPAGE && nextPage != page;
    add[0] = 0;
    if (level < 2 && npages > 1 && pos > 0) l += (size_t)snprintf(add + l, cap - l, "  PAGE %d/%d", pos, npages);
    if (level < 3 && page >= 0 && page < KFIT_NPAGE) l += (size_t)snprintf(add + l, cap - l, "  %s%s%s", kfit_pname[page], tag && tag[0] ? " " : "", tag && tag[0] ? tag : "");
    if (hasCyc) l += (size_t)snprintf(add + l, cap - l, level < 1 ? "  [%s] next: %s" : "  [%s] %s", cycKey, kfit_pname[nextPage]);
    else {   /* no cycle key: the old one-key hints, with the same names: [P] on the stock page goes to page II, on page II back to stock, [hire key] to hire / back to stock */
        if (p2Key && p2Key[0] && page <= 1) l += (size_t)snprintf(add + l, cap - l, "  [%s] %s", p2Key, kfit_pname[page == 0 ? 1 : 0]);
        if (hireKey && hireKey[0] && page != 3 && page != 4) l += (size_t)snprintf(add + l, cap - l, "  [%s] %s", hireKey, page == 2 ? kfit_pname[0] : kfit_pname[2]);
    }
}

/* the whole caption: base + pieces, at most maxAdd added characters (kfit_budget). tag = '(VIEW ONLY)' etc. after the page name (may be ''). cycKey '' = cycle key off.
   -> 1 = something was dropped or cut to fit, 0 = full text. The base itself is never cut (it is the game's 'BUY WEAPONS'). */
static int kfit_caption(char *out, size_t cap, const char *base, int page, int pos, int npages, const char *tag,
                        const char *cycKey, int nextPage, const char *p2Key, const char *hireKey, size_t maxAdd)
{
    char add[160]; int level, shrunk = 0; size_t bl;
    if (!out || cap < 2) return 0;
    snprintf(out, cap, "%s", base ? base : "");
    bl = strlen(out);
    for (level = 0; level < 4; level++) {
        kfit_pieces(add, sizeof add, level, page, pos, npages, tag, cycKey, nextPage, p2Key, hireKey);
        if (strlen(add) <= maxAdd) break;
        shrunk = 1;
    }
    if (level == 4) { level = 3; kfit_pieces(add, sizeof add, 3, page, pos, npages, tag, cycKey, nextPage, p2Key, hireKey); }
    if (strlen(add) > maxAdd) {                          /* even the keys alone are too long: cut them whole-word (the leading two spaces are kept out of the count) */
        char *a = add + 2; if (strlen(add) < 2) a = add;
        kfit_cut(a, sizeof add - (size_t)(a - add), maxAdd > 2 ? maxAdd - 2 : 0);
        shrunk = 1;
    }
    if (bl + strlen(add) >= cap) { add[cap - 1 - bl] = 0; shrunk = 1; }
    memcpy(out + bl, add, strlen(add) + 1);
    return shrunk;
}

/* a hire row: 'NAME  $90,000  [HIRED]' that fits maxch. Over the width the ' [HIRED]' words become a '*' marker, then the price goes, then the name is cut. price < 0 = no price shown */
static void kfit_hire_row(char *out, size_t cap, const char *name, long price, int hired, size_t maxch)
{
    char pr[24], t[96]; int n, i, k = 0;
    pr[0] = 0;
    if (price >= 0) {
        char d[24]; snprintf(d, sizeof d, "%ld", price); n = (int)strlen(d);
        pr[k++] = '$'; for (i = 0; i < n; i++) { if (i && (n - i) % 3 == 0) pr[k++] = ','; pr[k++] = d[i]; } pr[k] = 0;
    }
    snprintf(t, sizeof t, "%s%s%s%s", name, pr[0] ? "  " : "", pr, hired ? "  [HIRED]" : "");
    if (strlen(t) > maxch) snprintf(t, sizeof t, "%s%s%s%s", name, pr[0] ? " " : "", pr, hired ? " *" : "");
    if (strlen(t) > maxch && pr[0]) snprintf(t, sizeof t, "%s%s", name, hired ? " *" : "");
    kfit_cut(t, sizeof t, maxch);
    snprintf(out, cap, "%s", t);
}

/* the description of a controls row with the useful part FIRST (the pane shows 1 to 2 lines, then '...'): 'Key: F3.  Now: ON.' / what it does / where it works / how to move the key */
static void kfit_desc_ctl(char *out, size_t cap, const char *desc, const char *keyName, int on, const char *scope, const char *iniName)
{
    snprintf(out, cap, "Key: %s.  Now: %s.\n%s\nWorks in: %s.%s\nMove the key: [Keys] %s= in KLHook.ini.  Info page: BUY does nothing.",
             keyName, on ? "ON" : "OFF", desc, scope, on ? "" : "  Switched OFF: the key does nothing until it is on in Mod Options.", iniName);
}

#endif /* KLFIT_LOGIC_H */
