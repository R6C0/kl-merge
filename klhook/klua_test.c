/* klua_test.c - OFF-GAME check of klucc_aim_logic.h: the three slot-188 call sites, which actor teams are police, and the answer the
 * wrapper gives ([Ucc] PoliceAim). Pure numbers; the game reads, the thunk and the vtable patch are klucc_aim.c's (NOT run here).
 *   cl /nologo /W4 klua_test.c      or      tools/run_harness_linux.sh klua_test      or      gcc -Wall -o klua_test klua_test.c */
#ifdef _WIN32
#include <windows.h>
#endif
#include <stdio.h>
#include <string.h>
#include "klucc_aim_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    const unsigned long base = 0, moved = 0x10000;                 /* kl2.exe at 0x400000 (no ASLR), and once with the image moved */
    /* the sites: the instruction after each `call eax`, with and without a relocation delta */
    CHECK(klua_site(0x8824d5, base) == KLUA_SITE_SCORE);
    CHECK(klua_site(0x5708c4, base) == KLUA_SITE_LINE);
    CHECK(klua_site(0x51d9fb, base) == KLUA_SITE_CONE);
    CHECK(klua_site(0x51dac5, base) == KLUA_SITE_CONE);
    CHECK(klua_site(0x8824d5 + moved, moved) == KLUA_SITE_SCORE);
    CHECK(klua_site(0x8824d5, moved) == KLUA_SITE_NONE);           /* the raw address with a moved image is not the site */
    CHECK(klua_site(0x8824cd, base) == KLUA_SITE_NONE);            /* the call instruction itself, not the return address */
    CHECK(klua_site(0x418bfb, base) == KLUA_SITE_NONE);            /* 0x418b20's own slot 186/188 asks: never ours */
    CHECK(klua_site(0, base) == KLUA_SITE_NONE);
    /* teams: Enemy 1 and Enemy2 4 are the police; Mercenary 0 / Ally 2 the crew; 3 and the rest nothing */
    CHECK(klua_police_team(KLUA_TEAM_ENEMY)); CHECK(klua_police_team(KLUA_TEAM_ENEMY2));
    CHECK(!klua_police_team(KLUA_TEAM_MERC)); CHECK(!klua_police_team(KLUA_TEAM_ALLY)); CHECK(!klua_police_team(3));
    CHECK(!klua_police_team(-1)); CHECK(!klua_police_team(5)); CHECK(!klua_police_team(0x7fffffff));
    /* the answer: hostile only for a police asker, at a known site, about a hidden UCC, with the key on */
    CHECK(klua_answer(0, 1, KLUA_SITE_SCORE, 1, 1) == 1);
    CHECK(klua_answer(0, 1, KLUA_SITE_LINE, 1, 1) == 1);
    CHECK(klua_answer(0, 1, KLUA_SITE_CONE, 1, 1) == 1);
    CHECK(klua_answer(0, 1, KLUA_SITE_SCORE, 0, 1) == 0);          /* an AI heister asks: still a friend (no tell to the crew) */
    CHECK(klua_answer(0, 1, KLUA_SITE_SCORE, 1, 0) == 0);          /* revealed, or not the UCC: stock (police again) */
    CHECK(klua_answer(0, 1, KLUA_SITE_NONE, 1, 1) == 0);           /* a caller we do not know: stock */
    CHECK(klua_answer(0, 0, KLUA_SITE_SCORE, 1, 1) == 0);          /* key off */
    /* a stock 1 (the game exposed him: he shot a police NPC dead) is never undone, whoever asks */
    CHECK(klua_answer(1, 1, KLUA_SITE_SCORE, 0, 1) == 1);
    CHECK(klua_answer(1, 0, KLUA_SITE_NONE, 0, 0) == 1);
    CHECK(klua_answer(7, 0, KLUA_SITE_NONE, 0, 0) == 1);           /* any non-zero stock byte reads as 1 */
    printf("klua_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
