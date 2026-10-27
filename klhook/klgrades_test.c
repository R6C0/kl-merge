/* off-game check of klgrades.h's pure rules: cl /nologo klgrades_test.c  (then klgrades_test.exe) */
#include <stdio.h>
#include <string.h>
#include "klgrades.h"
static int f;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); f++; } } while (0)
int main(void)
{
    struct klgrd_cfg c; struct klgrd_in p; char b[24];
    klgrd_defaults(&c);
    CHECK(klgrd_rank_of_xp(&c, 0) == 0); CHECK(klgrd_rank_of_xp(&c, 24) == 0); CHECK(klgrd_rank_of_xp(&c, 25) == 1); CHECK(klgrd_rank_of_xp(&c, 99) == 1);
    CHECK(klgrd_rank_of_xp(&c, 100) == 2); CHECK(klgrd_rank_of_xp(&c, 2799) == 6); CHECK(klgrd_rank_of_xp(&c, 2800) == 7); CHECK(klgrd_rank_of_xp(&c, 99999) == 7); CHECK(klgrd_rank_of_xp(&c, -5) == 0);
    CHECK(klgrd_rankup(2, 3) == 1); CHECK(klgrd_rankup(3, 3) == 0); CHECK(klgrd_rankup(-1, 3) == 0); CHECK(klgrd_rankup(3, 8) == 0); CHECK(klgrd_rankup(7, 7) == 0);
    memset(&p, 0, sizeof p);
    CHECK(klgrd_letter_of(&c, klgrd_points(&c, &p)) == 'D');                       /* nothing done */
    p.dead = 1; CHECK(klgrd_points(&c, &p) == -3);
    memset(&p, 0, sizeof p); p.escaped = 1; p.loot = 100000; p.kills = 2;      /* 6 + 2 + 4 = 12 -> A */
    CHECK(klgrd_points(&c, &p) == 12); CHECK(klgrd_letter_of(&c, 12) == 'A');
    p.kills = 4; p.loot = 400000; p.rewards = 100000;                          /* 6 + 8 + 8 + 4 = 26 -> S */
    CHECK(klgrd_letter_of(&c, klgrd_points(&c, &p)) == 'S');
    memset(&p, 0, sizeof p); p.escaped = 1; p.traitor = 1; p.loot = 50000;     /* 6 - 4 + 1 = 3 -> C */
    CHECK(klgrd_points(&c, &p) == 3); CHECK(klgrd_letter_of(&c, 3) == 'C');
    memset(&p, 0, sizeof p); p.loot = 99999999L; p.kills = 500;                /* capped: 12 + 80 */
    CHECK(klgrd_points(&c, &p) == 92);
    CHECK(klgrd_letter_of(&c, 14) == 'S'); CHECK(klgrd_letter_of(&c, 13) == 'A'); CHECK(klgrd_letter_of(&c, 10) == 'A'); CHECK(klgrd_letter_of(&c, 9) == 'B');
    CHECK(klgrd_letter_of(&c, 6) == 'B'); CHECK(klgrd_letter_of(&c, 5) == 'C'); CHECK(klgrd_letter_of(&c, 3) == 'C'); CHECK(klgrd_letter_of(&c, 2) == 'D');
    klgrd_badge_text(b, sizeof b, 0, 0, 7); CHECK(!strcmp(b, "R1")); klgrd_badge_text(b, sizeof b, 0, 0, 0); CHECK(!strcmp(b, "R8"));
    klgrd_badge_text(b, sizeof b, 0, 1, 3); CHECK(!strcmp(b, "[THUG]")); klgrd_badge_text(b, sizeof b, 1, 1, 7); CHECK(!strcmp(b, "[KANE]"));
    klgrd_badge_text(b, 6, 0, 1, 2); CHECK(!strcmp(b, "[HIR]"));                 /* truncated, still closed */
    klgrd_badge_text(b, sizeof b, 0, 0, 9); CHECK(b[0] == 0);
    CHECK(!strcmp(klgrd_name_of(0, 7), "Mastermind")); CHECK(!strcmp(klgrd_name_of(1, 0), "Hutchison")); CHECK(!klgrd_name_of(0, 8)[0]);
    printf("klgrades_test: %s\n", f ? "FAIL" : "ok"); return f;
}
