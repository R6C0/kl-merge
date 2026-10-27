/* klmappool_ov_test.c - OFF-GAME check of klmappool_ov.h (next / played states, grid, file names, gate, placement).
 *   cl /nologo /W4 /D_CRT_SECURE_NO_WARNINGS klmappool_ov_test.c     (run from the klhook folder) */
#include <stdio.h>
#include <string.h>
#include "klmappool_ov.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    int order[5] = { 3, 0, 4, 1, 2 }, used[5] = { 0, 0, 0, 0, 0 }, st[5], nx, i; char f[64]; float x, y, ox, oy;
    nx = kmpo_states(order, used, 5, st);                                   /* nothing played: the first of the permutation is next */
    CHECK(nx == 0 && st[0] == KMPO_NEXT && st[1] == KMPO_WAIT && st[4] == KMPO_WAIT && kmpo_played(st, 5) == 0);
    used[3] = 1;                                                             /* entry 3 (position 0) played */
    nx = kmpo_states(order, used, 5, st);
    CHECK(nx == 1 && st[0] == KMPO_PLAYED && st[1] == KMPO_NEXT && st[2] == KMPO_WAIT && kmpo_played(st, 5) == 1);
    used[0] = 1; used[4] = 1;
    nx = kmpo_states(order, used, 5, st);
    CHECK(nx == 3 && st[2] == KMPO_PLAYED && st[3] == KMPO_NEXT && st[4] == KMPO_WAIT && kmpo_played(st, 5) == 3);
    used[2] = 1;                                                             /* a used mark out of permutation order still counts */
    nx = kmpo_states(order, used, 5, st);
    CHECK(nx == 3 && st[4] == KMPO_PLAYED);
    used[1] = 1;                                                             /* all used: the cycle is spent, nothing highlighted, nothing dimmed */
    nx = kmpo_states(order, used, 5, st);
    CHECK(nx == -1); for (i = 0; i < 5; i++) CHECK(st[i] == KMPO_WAIT);
    CHECK(kmpo_states(order, used, 0, st) == -1);                            /* empty pool */
    { int one[1] = { 0 }, u1[1] = { 0 }, s1[1]; CHECK(kmpo_states(one, u1, 1, s1) == 0 && s1[0] == KMPO_NEXT); }
    /* grid */
    CHECK(kmpo_cols(0, 8) == 1 && kmpo_cols(3, 8) == 3 && kmpo_cols(8, 8) == 8 && kmpo_cols(21, 8) == 8 && kmpo_cols(5, 0) == 1);
    CHECK(kmpo_rows(0, 8) == 0 && kmpo_rows(8, 8) == 1 && kmpo_rows(9, 8) == 2 && kmpo_rows(21, 8) == 3);
    kmpo_cell(0, 8, 72, 56, 6, &x, &y); CHECK(x == 0 && y == 0);
    kmpo_cell(9, 8, 72, 56, 6, &x, &y); CHECK(x == 78 && y == 62);
    kmpo_cell(7, 8, 72, 56, 6, &x, &y); CHECK(x == 7 * 78 && y == 0);
    /* names */
    kmpo_file("DM01B", f, sizeof f); CHECK(!strcmp(f, "DM01B.kmi"));
    kmpo_file("stock F03", f, sizeof f); CHECK(!strcmp(f, "stock_F03.kmi"));
    kmpo_file("a/b\\c:d", f, sizeof f); CHECK(!strcmp(f, "a_b_c_d.kmi"));             /* no path characters survive */
    kmpo_file("0123456789012345678901234567890123456789", f, 16); CHECK(strlen(f) <= 15 && !strcmp(f + strlen(f) - 4, ".kmi"));
    CHECK(!strcmp(kmpo_label(1), "FULL DEAD MEN") && !strcmp(kmpo_label(2), "FULL DOG DAYS") && !strcmp(kmpo_label(3), "MIX") && !kmpo_label(0)[0] && !kmpo_label(9)[0]);
    /* gate */
    CHECK(kmpo_state_shown(0x2000, 0xd) && !kmpo_state_shown(0x2000, 0x19) && !kmpo_state_shown(0x2000, 0) && !kmpo_state_shown(0x2000, 32) && !kmpo_state_shown(0, 0xd));
    CHECK(kmpo_state_shown(0x2000 | 1, 0) && kmpo_state_shown(0x80000000u, 31));
    /* tint, placement */
    CHECK(kmpo_tint(KMPO_NEXT) == 0xffffffffu && (kmpo_tint(KMPO_PLAYED) >> 24) < (kmpo_tint(KMPO_WAIT) >> 24));
    kmpo_place(1280, 720, 400, 200, 2, 74, &ox, &oy); CHECK(ox == 25.6f && oy + 200 <= 720);       /* clamped to the bottom edge */
    kmpo_place(1280, 720, 1400, 200, 50, 10, &ox, &oy); CHECK(ox == 0);                          /* wider than the screen: left edge */
    kmpo_place(1280, 720, 100, 100, 10, 10, &ox, &oy); CHECK(ox == 128 && oy == 72);
    printf("%d checks, %d failures\n", checks, fails);
    return fails != 0;
}
