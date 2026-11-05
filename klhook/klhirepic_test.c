/* klhirepic_test.c - OFF-GAME check of klhirepic.h (row -> heister, file name, picture box, gate, image header).
 *   cl /nologo /W4 /D_CRT_SECURE_NO_WARNINGS klhirepic_test.c     (run from the klhook folder) */
#include <stdio.h>
#include <string.h>
#include "klhirepic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    int r, n = 0; char f[16]; float x, y, w, h; unsigned char img[12 + 2 * 3 * 4]; unsigned iw = 0, ih = 0;
    /* rows: 0..7 -> 1..8, 17..24 -> 9..16, the rest none (the same table as klshoppage.c kspg_h_ch) */
    CHECK(khp_char_of_row(0) == 1 && khp_char_of_row(7) == 8 && khp_char_of_row(17) == 9 && khp_char_of_row(24) == 16);
    CHECK(khp_char_of_row(8) == 0 && khp_char_of_row(16) == 0 && khp_char_of_row(25) == 0 && khp_char_of_row(35) == 0 && khp_char_of_row(-1) == 0 && khp_char_of_row(99) == 0);
    for (r = -2; r < 40; r++) if (khp_char_of_row(r)) n++;
    CHECK(n == 16);
    khp_file(1, f, sizeof f); CHECK(!strcmp(f, "char_01.kmi"));
    khp_file(9, f, sizeof f); CHECK(!strcmp(f, "char_09.kmi"));
    khp_file(16, f, sizeof f); CHECK(!strcmp(f, "char_16.kmi"));
    khp_file(0, f, sizeof f); CHECK(!strcmp(f, "char_01.kmi"));              /* clamped, never a bad name */
    khp_file(99, f, sizeof f); CHECK(!strcmp(f, "char_16.kmi"));
    khp_file(5, f, 8); CHECK(f[0] == 0);                                     /* too small a buffer: empty, no overrun */
    /* box: 640 x 480 measured on research/shots/SHOP1_386s.png: x 344..567, y 88..228 */
    khp_box(640, 480, &x, &y, &w, &h);
    CHECK(x == 344.0f && w == 222.5f && y == 88.0f && h == 140.0f);
    khp_box(1280, 720, &x, &y, &w, &h); CHECK(x == 688.0f && y == 132.0f && w == 445.0f && h == 210.0f);
    khp_box(2560, 1440, &x, &y, &w, &h); CHECK(x == 1376.0f && y == 264.0f && w == 890.0f && h == 420.0f);
    /* gate */
    CHECK(khp_want(1, 0, 1, 2, 0) == 1 && khp_want(1, 0, 1, 2, 20) == 12);
    CHECK(khp_want(0, 0, 1, 2, 0) == 0);                                    /* not the hire page */
    CHECK(khp_want(1, 1, 1, 2, 0) == 0);                                    /* the controls page */
    CHECK(khp_want(1, 0, 0, 2, 0) == 0);                                    /* the shop gate is closed */
    CHECK(khp_want(1, 0, 1, 1, 0) == 0 && khp_want(1, 0, 1, 0, 0) == 0);   /* the tab list, not the weapon list */
    CHECK(khp_want(1, 0, 1, 2, 10) == 0);                                   /* a row without a heister ('-') */
    CHECK(khp_fresh(1000, 900, 600) && !khp_fresh(2000, 900, 600) && !khp_fresh(1000, 0, 600) && khp_fresh(5, 0xfffffff0u, 600));
    /* image header */
    memcpy(img, "KMI1", 4); memset(img + 4, 0, 8); img[4] = 2; img[8] = 3; memset(img + 12, 7, 24);
    CHECK(khp_kmi_ok(img, sizeof img, &iw, &ih) && iw == 2 && ih == 3);
    CHECK(!khp_kmi_ok(img, sizeof img - 1, 0, 0) && !khp_kmi_ok(img, 11, 0, 0));
    img[0] = 'X'; CHECK(!khp_kmi_ok(img, sizeof img, 0, 0)); img[0] = 'K';
    img[4] = 0; CHECK(!khp_kmi_ok(img, sizeof img, 0, 0)); img[4] = 0; img[5] = 3;     /* 768 wide: over 512 */
    CHECK(!khp_kmi_ok(img, sizeof img, 0, 0));
    printf("%d checks, %d failures\n", checks, fails);
    return fails != 0;
}
