/* klfit_test.c - off-game harness for klfit_logic.h ([Keys] CaptionTidy / CaptionMax / RowFit). No windows.h.
   Proves the text rules (word cuts, budgets, the one page-name table), NOT that the strings fit the game's caption box (the 80 / 16 / 14 character widths are GUESSES, NOT RUN IN THE GAME).
   Build: cl /nologo /W3 klfit_test.c /Fe:klfit_test.exe     Run: klfit_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include "klfit_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    char b[200], o[200];
    int page, npages, cyc, hire, p2, ok;
    static const char *const keys[] = { "F2", "F9", "P", "Num1", "PageUp", "Ctrl+Delete", "Ctrl+Backspace" };
    static const char *const tags[] = { "", "(VIEW ONLY)", "(STOCK GUN)" };
    static const char *const names[] = { "KANE", "LYNCH", "MITCHEL", "SHOTGUN SHELLS", "A VERY LONG HEISTER NAME" };
    size_t i, k;

    /* kfit_cut */
    strcpy(b, "short"); CHECK(kfit_cut(b, sizeof b, 16) == 0 && !strcmp(b, "short"), "untouched when it fits: '%s'", b);
    strcpy(b, "exactly sixteen!"); CHECK(strlen(b) == 16 && kfit_cut(b, sizeof b, 16) == 0 && !strcmp(b, "exactly sixteen!"), "exactly maxch: untouched");
    strcpy(b, "COP SQUAD FOLLOW NUM1 OFF"); CHECK(kfit_cut(b, sizeof b, 16) == 1 && !strcmp(b, "COP SQUAD..") && strlen(b) <= 16, "cut at a whole word: '%s'", b);
    strcpy(b, "ASSAULT RIFLE MK TWO"); kfit_cut(b, sizeof b, 18); CHECK(!strcmp(b, "ASSAULT RIFLE MK.."), "'%s'", b);
    strcpy(b, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"); CHECK(kfit_cut(b, sizeof b, 10) == 1 && !strcmp(b, "ABCDEFGH.."), "one long word: cut hard: '%s'", b);
    strcpy(b, "AB CD EFGH"); kfit_cut(b, sizeof b, 7); CHECK(!strcmp(b, "AB CD.."), "a word ending exactly at the cut stays whole: '%s'", b);
    strcpy(b, "ONE TWO THREE FOUR"); kfit_cut(b, sizeof b, 3); CHECK(!strcmp(b, "O.."), "'%s'", b);
    strcpy(b, "ONE TWO"); kfit_cut(b, sizeof b, 2); CHECK(!strcmp(b, "ON"), "maxch < 3: hard cut without dots: '%s'", b);
    strcpy(b, "ONE TWO THREE FOUR FIVE SIX SEVEN"); ok = 1;
    for (i = 3; i < 34; i++) {
        char c[200]; strcpy(c, b);
        kfit_cut(c, sizeof c, i);
        if (strlen(c) > i) ok = 0;
        { char d[200]; int again; strcpy(d, c); again = kfit_cut(d, sizeof d, i); if (again || strcmp(c, d)) ok = 0; }          /* idempotent */
        if (strlen(c) < strlen(b) && strcmp(c + strlen(c) - 2, "..")) ok = 0;                                                   /* '..' only when cut ... */
        if (strlen(c) == strlen(b) && strcmp(c, b)) ok = 0;
        if (strlen(c) < strlen(b)) { size_t m = strlen(c) - 2; if (m > 0 && m < strlen(b) && b[m] != ' ' && c[m - 1] != ' ' && strchr(c, ' ') && b[m - 1] != ' ') { /* a word split: the char before '..' must end a word of b */ if (b[m] != ' ') ok = 0; } }
    }
    CHECK(ok, "kfit_cut: never longer than maxch, idempotent, '..' only on a cut, never splits a word (when a space exists)");
    strcpy(b, "no change"); CHECK(kfit_cut(b, 5, 99) == 1 && strlen(b) <= 4, "maxch clamped to the buffer: '%s'", b);
    CHECK(kfit_cut(0, 10, 5) == 0 && kfit_cut(b, 0, 5) == 0, "bad buffer");

    /* the one page-name table */
    CHECK(!strcmp(kfit_pname[0], "STOCK") && !strcmp(kfit_pname[1], "PD2 GUNS") && !strcmp(kfit_pname[2], "HIRE") && !strcmp(kfit_pname[3], "CONTROLS") && !strcmp(kfit_pname[4], "MODES"), "the five names");

    /* the budget */
    CHECK(kfit_budget(40, 11) == 40 && kfit_budget(0, 11) == 40 && kfit_budget(100, 11) == 45 && kfit_budget(100, 80) == 8 && kfit_budget(3, 11) == 8, "budget = min(CaptionMax, total - base), at least 8: %u %u %u", (unsigned)kfit_budget(100, 11), (unsigned)kfit_budget(100, 80), (unsigned)kfit_budget(3, 11));

    /* the caption, the owner's example */
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 1, 2, 4, "", "F2", 2, "", "", 40) == 0 && !strcmp(o, "BUY WEAPONS  PAGE 2/4  PD2 GUNS  [F2] next: HIRE"), "'%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 0, 1, 4, "", "F2", 1, "", "", 40) == 0 && !strcmp(o, "BUY WEAPONS  PAGE 1/4  STOCK  [F2] next: PD2 GUNS"), "'%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 2, 3, 4, "", "F2", 3, "", "", 40) == 0 && !strcmp(o, "BUY WEAPONS  PAGE 3/4  HIRE  [F2] next: CONTROLS"), "'%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 1, 2, 4, "(VIEW ONLY)", "F2", 2, "", "", 80) == 0 && !strcmp(o, "BUY WEAPONS  PAGE 2/4  PD2 GUNS (VIEW ONLY)  [F2] next: HIRE"), "tag: '%s'", o);
    /* no cycle key: the one-key hints with the same names */
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 0, 1, 3, "", "", -1, "P", "F3", 60) == 0 && !strcmp(o, "BUY WEAPONS  PAGE 1/3  STOCK  [P] PD2 GUNS  [F3] HIRE"), "no cycle key: '%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 1, 2, 3, "", "", -1, "P", "F3", 60) == 0 && !strcmp(o, "BUY WEAPONS  PAGE 2/3  PD2 GUNS  [P] STOCK  [F3] HIRE"), "page II: '%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 0, 1, 3, "", "", -1, "P", "F3", 40) == 1 && !strcmp(o, "BUY WEAPONS  STOCK  [P] PD2 GUNS  [F3] HIRE"), "over 40: PAGE n/N dropped first: '%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 2, 3, 3, "", "", -1, "", "F3", 40) == 0 && !strcmp(o, "BUY WEAPONS  PAGE 3/3  HIRE  [F3] STOCK"), "hire page: '%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 0, 1, 1, "", "", -1, "", "", 40) == 0 && !strcmp(o, "BUY WEAPONS  STOCK"), "one page only: no 'PAGE 1/1': '%s'", o);

    /* every page, key and tag combination stays inside the budget; the cycle key survives every shrink */
    ok = 1;
    for (page = 0; page < KFIT_NPAGE; page++) for (npages = 1; npages <= 5; npages++) for (cyc = 0; cyc < 2; cyc++) for (hire = 0; hire < 2; hire++) for (p2 = 0; p2 < 2; p2++) for (k = 0; k < sizeof keys / sizeof *keys; k++) for (i = 0; i < 3; i++) {
        size_t bud = kfit_budget(40, 11), bl = strlen("BUY WEAPONS"), n; int nxt = (page + 1) % KFIT_NPAGE;
        kfit_caption(o, sizeof o, "BUY WEAPONS", page, page < npages ? page + 1 : npages, npages, tags[i], cyc ? keys[k] : "", cyc ? nxt : -1, p2 ? keys[(k + 2) % 7] : "", hire ? keys[(k + 1) % 7] : "", bud);
        n = strlen(o);
        if (n > bl + bud) { ok = 0; printf("  over budget (%u > %u): '%s'\n", (unsigned)(n - bl), (unsigned)bud, o); }
        if (strncmp(o, "BUY WEAPONS", bl)) ok = 0;                                      /* the game's own text is never cut */
        if (cyc && strstr(o, keys[k]) == 0) { ok = 0; printf("  cycle key lost: '%s'\n", o); }
        if (n + 24 + 1 > (size_t)(KFIT_CAPTION_TOTAL + 24)) ok = 0;                    /* with ' | RANK 10: DESPERADO' the line stays within the box estimate */
    }
    CHECK(ok, "caption: inside the CaptionMax budget for every page / key / tag, base intact, cycle key kept");
    /* shrink ladder: a long key name drops 'next:' first, then 'PAGE n/N', then the page name */
    kfit_caption(o, sizeof o, "BUY WEAPONS", 4, 5, 5, "", "Ctrl+Backspace", 0, "", "", 40);
    CHECK(strstr(o, "[Ctrl+Backspace]") != 0 && strlen(o) <= 11 + 40, "worst key name: '%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 3, 4, 5, "", "F2", 4, "", "", 24) == 1 && strlen(o) <= 11 + 24 && strstr(o, "[F2]") != 0 && strstr(o, "next:") == 0, "tight budget: 'next:' goes first: '%s'", o);
    CHECK(kfit_caption(o, sizeof o, "BUY WEAPONS", 3, 4, 5, "", "F2", 4, "", "", 12) == 1 && strlen(o) <= 11 + 12 && strstr(o, "[F2]") != 0, "very tight: keys only: '%s'", o);
    CHECK(kfit_caption(o, 20, "BUY WEAPONS", 1, 2, 4, "", "F2", 2, "", "", 40) == 1 && strlen(o) < 20 && !strncmp(o, "BUY WEAPONS", 11), "small output buffer: cut, terminated: '%s'", o);
    CHECK(kfit_caption(0, 20, "X", 0, 1, 1, "", "", -1, "", "", 40) == 0, "bad buffer");

    /* hire rows */
    ok = 1;
    for (i = 0; i < sizeof names / sizeof *names; i++) for (k = 0; k < 2; k++) {
        kfit_hire_row(o, sizeof o, names[i], 90000, (int)k, KFIT_ROW_MAX);
        if (strlen(o) > KFIT_ROW_MAX) { ok = 0; printf("  hire row too wide: '%s'\n", o); }
        kfit_hire_row(o, sizeof o, names[i], -1, (int)k, KFIT_ROW_MAX);
        if (strlen(o) > KFIT_ROW_MAX) { ok = 0; printf("  hire row too wide: '%s'\n", o); }
    }
    CHECK(ok, "hire rows fit the row width with and without price / HIRED");
    kfit_hire_row(o, sizeof o, "KANE", 90000, 0, 16); CHECK(!strcmp(o, "KANE  $90,000"), "'%s'", o);
    kfit_hire_row(o, sizeof o, "KANE", 90000, 1, 16); CHECK(!strcmp(o, "KANE $90,000 *"), "' [HIRED]' became a marker: '%s'", o);
    kfit_hire_row(o, sizeof o, "MITCHEL", 100000, 1, 16); CHECK(strlen(o) <= 16 && strstr(o, "*") != 0, "'%s'", o);
    kfit_hire_row(o, sizeof o, "KANE", 90000, 1, 40); CHECK(!strcmp(o, "KANE  $90,000  [HIRED]"), "wide enough: the old text: '%s'", o);

    /* control descriptions: the key and 'Now:' come first */
    kfit_desc_ctl(o, sizeof o, "Cop squad follows you.", "Num1", 0, "in round", "CopFollow");
    CHECK(!strncmp(o, "Key: Num1.  Now: OFF.\n", 22) && strstr(o, "Switched OFF") != 0 && strstr(o, "[Keys] CopFollow=") != 0, "'%s'", o);
    kfit_desc_ctl(o, sizeof o, "Cop squad follows you.", "Num1", 1, "in round", "CopFollow");
    CHECK(!strncmp(o, "Key: Num1.  Now: ON.\n", 21) && strstr(o, "Switched OFF") == 0, "'%s'", o);
    kfit_desc_ctl(o, 30, "Cop squad follows you.", "Num1", 1, "in round", "CopFollow"); CHECK(strlen(o) < 30, "snprintf-bounded");

    printf("klfit_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
