/* klpd2_test.c - off-game harness for klpd2_logic.h ([Payday2] Enable). cl /nologo /W4 klpd2_test.c  (exit 0 = all pass) */
#include <stdio.h>
#include "klpd2_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    int v, i;
    CHECK(kp2_enabled(-1) == 1 && kp2_enabled(1) == 1 && kp2_enabled(0) == 0 && kp2_enabled(5) == 1);   /* missing = on */
    for (v = 0; v <= 13; v++) { CHECK(kp2_mask_eff(v, 1) == v); CHECK(kp2_mask_eff(v, 0) == (v >= 10 ? 0 : v)); }
    CHECK(kp2_mask_menu(9, 10, 0) == 0 && kp2_mask_menu(0, 13, 0) == 9 && kp2_mask_menu(5, 7, 0) == 7 && kp2_mask_menu(9, 10, 1) == 10);
    /* F11 over the 14 values 0..13: up from 9 wraps to 0, down from 0 lands on 9, never on a plate while off */
    CHECK(kp2_mask_key(10, 1, 14, 0) == 0 && kp2_mask_key(13, -1, 14, 0) == 9 && kp2_mask_key(13, 1, 14, 0) == 0 && kp2_mask_key(10, -1, 14, 0) == 9);
    CHECK(kp2_mask_key(10, 1, 14, 1) == 10 && kp2_mask_key(4, 1, 14, 0) == 4);
    for (i = -14; i < 40; i++) { int w = ((i % 14) + 14) % 14; CHECK(!kp2_is_mask(kp2_mask_key(w, i & 1 ? 1 : -1, 14, 0))); }
    CHECK(kp2_set_is_pd2("") && kp2_set_is_pd2("pd2") && kp2_set_is_pd2("PD2 guns") && !kp2_set_is_pd2("dm") && !kp2_set_is_pd2("pd23") && kp2_set_is_pd2(0));
    CHECK(kp2_page2_on(1, 1, "") == 1 && kp2_page2_on(1, 0, "") == 0 && kp2_page2_on(1, 0, "dm") == 1 && kp2_page2_on(0, 1, "") == 0);
    CHECK(kp2_music_on(1, 1) == 1 && kp2_music_on(1, 0) == 0 && kp2_music_on(0, 1) == 0);
    printf("klpd2_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
