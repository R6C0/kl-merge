/* klshopui_test.c - off-game harness for klshopui_logic.h ([ShopPage] TidyPage2 / [Hire] TidyPage). No windows.h.
   Proves every string the player sees fits the klfit_logic.h widths (row 16, tab 14, caption budget, first description line 40) - widths are GUESSES, NOT RUN IN THE GAME.
   Build: cl /nologo /W3 klshopui_test.c /Fe:klshopui_test.exe     Run: klshopui_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include "klshopui_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

static size_t l1len(const char *s) { const char *nl = strchr(s, '\n'); return nl ? (size_t)(nl - s) : strlen(s); }

int main(void)
{
    char o[600], b[600], m[32];
    int t, st, gate, conf, i, ty;
    /* the 13 live PD2 names (KLShopPage.ini) and the Dead Men names */
    static const char *const pd2[] = { "CHIMANO 88 SHIELD", "BERNETTI 9 SHIELD", "GL40 FLARE", "GL40 GAS", "GL40", "HRL-7", "PAR", "RPK", "MG42", "AK.762", "LITTLE FRIEND 7.62", "JP36", "R700" };
    static const char *const heis[] = { "J.C.", "Tommy", "Pierre", "Liam", "Mitchel", "Ashkanan", "Hutchison", "Lynch", "Standen", "Kane", "Zoran Bogdanovic" };
    static const long prices[] = { 45000, 90000, 180000, 225000, 270000, 450000, 540000, 1250000, 45500, 0 };
    size_t k, p;

    /* money */
    ksu_money_short(m, sizeof m, 45000); CHECK(!strcmp(m, "$45K"), "'%s'", m);
    ksu_money_short(m, sizeof m, 540000); CHECK(!strcmp(m, "$540K"), "'%s'", m);
    ksu_money_short(m, sizeof m, 1250000); CHECK(!strcmp(m, "$1,250,000"), "'%s'", m);
    ksu_money_short(m, sizeof m, 45500); CHECK(!strcmp(m, "$45,500"), "'%s'", m);
    ksu_money_full(m, sizeof m, 45000); CHECK(!strcmp(m, "$45,000"), "'%s'", m);
    ksu_money_full(m, sizeof m, 0); CHECK(!strcmp(m, "$0"), "'%s'", m);
    ksu_money_short(m, 4, 45000); CHECK(m[0] == 0, "tiny buffer: empty");

    /* set labels, caption */
    CHECK(!strcmp(ksu_set_caption(0), "PD2 GUNS") && !strcmp(ksu_set_caption(1), "DEAD MEN GUNS") && !strcmp(ksu_set_caption(2), "PAGE II") && !strcmp(ksu_set_caption(3), "PAGE II"), "set captions");
    ksu_p2_tag(m, sizeof m, 13); CHECK(!strcmp(m, "(13 NEW)"), "'%s'", m);
    ksu_p2_tag(m, sizeof m, 0); CHECK(m[0] == 0, "no tag at 0");
    for (ty = 0; ty < 4; ty++) {   /* the whole page II caption stays inside the budget at every shrink, for the real key names */
        const char *save = kfit_pname[1]; static const char *const keys[] = { "F2", "Ctrl+Delete" };
        for (k = 0; k < 2; k++) {
            ksu_p2_tag(m, sizeof m, 13);
            kfit_pname[1] = ksu_set_caption(ty);
            kfit_caption(o, sizeof o, "Buy weapons", 1, 2, 5, m, keys[k], 2, "", "", kfit_budget(KFIT_CAPTION_DEFAULT, 11));
            kfit_pname[1] = save;
            CHECK(strlen(o) - 11 <= (size_t)KFIT_CAPTION_DEFAULT && strstr(o, keys[k]), "caption type %d key %s: '%s'", ty, keys[k], o);
            if (ty == 0 && k == 0) CHECK(strstr(o, "PD2 GUNS (13 NEW)") && strstr(o, "[F2]"), "pd2 caption keeps name + key: '%s'", o);
        }
    }

    /* page II names */
    for (p = 0; p < sizeof pd2 / sizeof *pd2; p++) {
        ksu_p2_name(o, sizeof o, pd2[p], 0, KFIT_ROW_MAX);
        CHECK(strlen(o) <= KFIT_ROW_MAX && !strncmp(o, "PD2 ", 4), "name '%s' -> '%s'", pd2[p], o);
    }
    ksu_p2_name(o, sizeof o, "PAR", 0, KFIT_ROW_MAX); CHECK(!strcmp(o, "PD2 PAR"), "'%s'", o);
    ksu_p2_name(o, sizeof o, "PD2 PAR", 0, KFIT_ROW_MAX); CHECK(!strcmp(o, "PD2 PAR"), "no double tag: '%s'", o);
    ksu_p2_name(o, sizeof o, "CHIMANO 88 SHIELD", 0, KFIT_ROW_MAX); CHECK(!strcmp(o, "PD2 CHIMANO 88.."), "'%s'", o);
    ksu_p2_name(o, sizeof o, "MP5", 1, KFIT_ROW_MAX); CHECK(!strcmp(o, "DM MP5"), "'%s'", o);
    ksu_p2_name(o, sizeof o, "MP5", 2, KFIT_ROW_MAX); CHECK(!strcmp(o, "MP5"), "stock set: no tag: '%s'", o);

    /* tabs */
    for (t = 0; t < 4; t++) {
        CHECK(strlen(ksu_tab_default(0, t)) > 0 && strlen(ksu_tab_default(0, t)) <= KFIT_TAB_MAX, "tab %d '%s'", t, ksu_tab_default(0, t));
        CHECK(ksu_tab_default(1, t)[0] == 0 && ksu_tab_default(2, t)[0] == 0 && ksu_tab_default(3, t)[0] == 0, "other sets keep the stock tab");
    }
    CHECK(ksu_tab_default(0, 4)[0] == 0 && ksu_tab_default(0, -1)[0] == 0, "tab index out of range");

    /* page II descriptions */
    ksu_p2_desc(o, sizeof o, "Police reg.: 2040-II40\nLight machine gun. PD2 PAR. Page II: sold in the TYPE 05 row, same price, same rank.", 0);
    CHECK(!strncmp(o, "PD2 GUN: price + rank of the stock gun\n", 39), "line 1 useful: '%s'", o);
    CHECK(l1len(o) <= KSU_LINE1_MAX, "line 1 %u", (unsigned)l1len(o));
    CHECK(strstr(o, "Light machine gun") && strstr(o, "Police reg.: 2040-II40") && strstr(o, "TYPE 05"), "nothing lost: '%s'", o);
    CHECK(strstr(o, "Police reg") > strstr(o, "TYPE 05"), "reg line moved to the end");
    ksu_p2_desc(o, sizeof o, "Police reg.: 1", 1); CHECK(!strcmp(o, "DM GUN: price + rank of the stock gun\nPolice reg.: 1") && l1len(o) <= KSU_LINE1_MAX, "reg only: '%s'", o);
    ksu_p2_desc(o, sizeof o, "POLICE REG.: 1\nbody", 2); CHECK(!strncmp(o, "NEW GUN:", 8), "case-insensitive: '%s'", o);
    ksu_p2_desc(o, sizeof o, "A real first line\nmore", 0); CHECK(!strcmp(o, "A real first line\nmore"), "author's own line 1 kept: '%s'", o);
    ksu_p2_desc(o, 20, "Police reg.: 2040-II40\nLight machine gun. PD2 PAR.", 0); CHECK(strlen(o) < 20, "small buffer cut, terminated");
    ksu_online_desc(o, sizeof o, "Gun line\nrest of it", "VIEW ONLY online: buy it in Arcade.");
    CHECK(!strcmp(o, "Gun line\nVIEW ONLY online: buy it in Arcade.\nrest of it"), "'%s'", o);
    ksu_online_desc(o, sizeof o, "Only one line", "NOTE"); CHECK(!strcmp(o, "Only one line\nNOTE"), "'%s'", o);
    CHECK(strlen("VIEW ONLY online: buy it in Arcade.") <= KSU_LINE1_MAX, "online note fits a line");
    CHECK(strlen("ONLINE: buys this row's stock gun.") <= KSU_LINE1_MAX, "online2 note fits a line");

    /* hire rows: every heister x price x state fits the row width */
    for (k = 0; k < sizeof heis / sizeof *heis; k++)
        for (p = 0; p < sizeof prices / sizeof *prices; p++)
            for (st = 0; st < 3; st++) {
                ksu_hire_row(o, sizeof o, heis[k], prices[p], st, KFIT_ROW_MAX);
                CHECK(strlen(o) <= KFIT_ROW_MAX && o[0], "row '%s' %ld st %d -> '%s'", heis[k], prices[p], st, o);
            }
    ksu_hire_row(o, sizeof o, "Pierre", 45000, KSU_ROW_PRICE, KFIT_ROW_MAX); CHECK(!strcmp(o, "Pierre  $45K"), "'%s'", o);
    ksu_hire_row(o, sizeof o, "Ashkanan", 180000, KSU_ROW_PRICE, KFIT_ROW_MAX); CHECK(!strcmp(o, "Ashkanan  $180K"), "price kept on the long rows: '%s'", o);
    ksu_hire_row(o, sizeof o, "Hutchison", 270000, KSU_ROW_PRICE, KFIT_ROW_MAX); CHECK(!strcmp(o, "Hutchison  $270K"), "'%s'", o);
    ksu_hire_row(o, sizeof o, "Pierre", 45000, KSU_ROW_HIRED, KFIT_ROW_MAX); CHECK(!strcmp(o, "Pierre  HIRED"), "'%s'", o);
    ksu_hire_row(o, sizeof o, "Hutchison", 270000, KSU_ROW_HIRED, KFIT_ROW_MAX); CHECK(!strcmp(o, "Hutchison  HIRED"), "'%s'", o);
    ksu_hire_row(o, sizeof o, "Liam", 45000, KSU_ROW_NA, KFIT_ROW_MAX); CHECK(!strcmp(o, "Liam  n/a"), "'%s'", o);
    ksu_hire_row(o, sizeof o, "Lynch", -1, KSU_ROW_PRICE, KFIT_ROW_MAX); CHECK(!strcmp(o, "Lynch"), "no price: '%s'", o);
    ksu_hire_row(o, sizeof o, "Zoran Bogdanovic", 45000, KSU_ROW_HIRED, KFIT_ROW_MAX); CHECK(strlen(o) <= KFIT_ROW_MAX && strstr(o, "HIRED"), "long name hired keeps HIRED: '%s'", o);
    ksu_hire_row(o, sizeof o, "Zoran Bogdanovic", 45000, KSU_ROW_NA, KFIT_ROW_MAX); CHECK(strlen(o) <= KFIT_ROW_MAX && strstr(o, "n/a"), "long name n/a keeps n/a: '%s'", o);

    /* hire line 1: every state, with and without gate / confirm, at the largest price and rank */
    for (st = KSU_H_READY; st <= KSU_H_LOWRANK; st++)
        for (gate = 0; gate < 2; gate++)
            for (conf = 0; conf < 2; conf++) {
                ksu_hire_line1(o, sizeof o, st, 1250000, 10, gate, conf, "Hutchison", "not enough money for him at all");
                CHECK(strlen(o) <= KSU_LINE1_MAX && o[0] && !strchr(o, '\n'), "state %d gate %d conf %d: '%s' (%u)", st, gate, conf, o, (unsigned)strlen(o));
            }
    ksu_hire_line1(o, sizeof o, KSU_H_READY, 45000, 1, 0, 1, "", ""); CHECK(!strcmp(o, "$45,000 - BUY twice to hire"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_READY, 45000, 3, 1, 1, "", ""); CHECK(!strcmp(o, "$45,000, rank 3 - BUY twice"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_READY, 45000, 1, 0, 0, "", ""); CHECK(!strcmp(o, "$45,000 - press BUY to hire"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_ARM, 45000, 1, 0, 1, "", ""); CHECK(!strcmp(o, "BUY AGAIN to hire: $45,000"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_HIRED, 45000, 1, 0, 1, "", ""); CHECK(!strcmp(o, "HIRED for the next round"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_OTHER, 45000, 1, 0, 1, "Pierre", ""); CHECK(!strcmp(o, "You hired Pierre: one per round"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_LOWRANK, 45000, 4, 1, 1, "", ""); CHECK(!strcmp(o, "RANK TOO LOW: needs rank 4"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_REFUSED, 45000, 1, 0, 1, "", "no money"); CHECK(!strcmp(o, "REFUSED: no money"), "'%s'", o);
    ksu_hire_line1(o, sizeof o, KSU_H_NOMAP, 45000, 1, 0, 1, "", ""); CHECK(strstr(o, "NOT ON THIS MAP"), "'%s'", o);

    /* the whole hire description */
    ksu_hire_line1(b, sizeof b, KSU_H_READY, 45000, 1, 0, 1, "", "");
    ksu_hire_desc(o, sizeof o, b, "Dog Days crew. Hired for one round.", 1, 0, "no rank gate");
    CHECK(!strcmp(o, "$45,000 - BUY twice to hire\nDog Days crew. Hired for one round.") && l1len(o) <= KSU_LINE1_MAX, "desc, no gate: no facts line: '%s'", o);
    CHECK(!strstr(o, "stock gun") && !strstr(o, "lock shown"), "no stock-gun remarks");
    ksu_hire_line1(b, sizeof b, KSU_H_READY, 45000, 3, 1, 1, "", "");
    ksu_hire_desc(o, sizeof o, b, "Dog Days crew.", 3, 1, "your rank 8");
    CHECK(!strcmp(o, "$45,000, rank 3 - BUY twice\nDog Days crew.\nNeeds rank 3 (your rank 8).") && !strstr(o + 30, "$"), "desc, gate: rank facts, price once: '%s'", o);

    /* stars / lock */
    CHECK(ksu_star_idx(1, 0, 0, 3) == 99 && ksu_star_idx(1, 0, 5, 3) == 99, "no gate + tidy: stars hidden");
    CHECK(ksu_star_idx(1, 1, 0, 3) == -1 && ksu_star_idx(1, 1, 3, 3) == 99 && ksu_star_idx(1, 1, -1, 3) == 99, "gate + tidy: the need");
    for (i = 0; i < 8; i++) CHECK(ksu_star_idx(0, i & 1, i % 4, 2) == (((i % 4) < 2) ? -1 : 99), "tidy off = today's rule");
    CHECK(ksu_lock_hidden(0, 0, 0) == 1 && ksu_lock_hidden(0, 0, 1) == 0 && ksu_lock_hidden(0, 1, 1) == 1 && ksu_lock_hidden(1, 0, 1) == 1, "lock rule");

    printf("klshopui_test: %d checks, %d failures\n", checks, fails);
    printf(fails ? "RESULT: FAIL\n" : "RESULT: PASS\n");
    return fails ? 1 : 0;
}
