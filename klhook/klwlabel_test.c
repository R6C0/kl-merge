/* klwlabel_test.c - OFF-GAME check of klwlabel_logic.h (wardrobe group tags, "n/N  GROUP > Name" labels, Shift wrap, group jumps).
 *   cl /nologo /W4 klwlabel_test.c      or      tools/run_harness_linux.sh klwlabel_test */
#include <stdio.h>
#include <string.h>
#include "klwlabel_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
#define SEQ(l, w, i, s) do { char b_[100]; kwl_label((w), (i), b_, sizeof b_); checks++; if (strcmp(b_, (s))) { fails++; printf("FAIL line %d: label %d/%d = '%s', want '%s'\n", __LINE__, (w), (i), b_, (s)); } } while (0)

/* tools\kl_chars.py outfit_name(0..23), generated 11-07 */
static const char *const want_outfit[24] = {
    "Plain clothes",
    "Light vest",
    "Tactical vest",
    "Heavy armour",
    "Plain clothes, black shirt",
    "Light vest, black shirt",
    "Tactical vest, black shirt",
    "Heavy armour, black shirt",
    "Plain clothes, dark balaclava",
    "Light vest, dark balaclava",
    "Tactical vest, dark balaclava",
    "Heavy armour, dark balaclava",
    "Plain clothes, black shirt, dark balaclava",
    "Light vest, black shirt, dark balaclava",
    "Tactical vest, black shirt, dark balaclava",
    "Heavy armour, black shirt, dark balaclava",
    "Plain clothes, black balaclava",
    "Light vest, black balaclava",
    "Tactical vest, black balaclava",
    "Heavy armour, black balaclava",
    "Plain clothes, black shirt, black balaclava",
    "Light vest, black shirt, black balaclava",
    "Tactical vest, black shirt, black balaclava",
    "Heavy armour, black shirt, black balaclava"
};

int main(void)
{
    int i, g, w; char b[100], big[16];
    CHECK(kwl_span(KWL_CHAR) == 17); CHECK(kwl_span(KWL_MASK) == 14); CHECK(kwl_span(KWL_OUTFIT) == 24); CHECK(kwl_span(5) == 0);
    /* outfit names == kl_chars.outfit_name */
    for (i = 0; i < 24; i++) { kwl_name(KWL_OUTFIT, i, b, sizeof b); CHECK(!strcmp(b, want_outfit[i])); }
    /* characters: every one is tagged; Kane / Lynch are DEAD MEN (index 9, 10 -> counter 10/17, 11/17) */
    SEQ(l, KWL_CHAR, 0, "1/17  Game default");
    SEQ(l, KWL_CHAR, 1, "2/17  DOG DAYS > J.C.");
    SEQ(l, KWL_CHAR, 8, "9/17  DOG DAYS > Mitchel");
    SEQ(l, KWL_CHAR, 9, "10/17  DEAD MEN > Kane");
    SEQ(l, KWL_CHAR, 10, "11/17  DEAD MEN > Lynch");
    SEQ(l, KWL_CHAR, 16, "17/17  DEAD MEN > Hutchison");
    for (i = 1; i <= 8; i++) CHECK(kwl_group(KWL_CHAR, i) == KWL_G_DOGDAYS);
    for (i = 9; i <= 16; i++) CHECK(kwl_group(KWL_CHAR, i) == KWL_G_DEADMEN);
    /* masks */
    SEQ(l, KWL_MASK, 0, "1/14  Game option");
    SEQ(l, KWL_MASK, 1, "2/14  No mask");
    SEQ(l, KWL_MASK, 2, "3/14  DOG DAYS > Moustache (J.C.)");
    SEQ(l, KWL_MASK, 9, "10/14  DOG DAYS > Blue opera (Mitchel)");
    SEQ(l, KWL_MASK, 10, "11/14  PAYDAY 2 > Wolf");
    SEQ(l, KWL_MASK, 13, "14/14  PAYDAY 2 > Hoxton");
    /* outfits */
    SEQ(l, KWL_OUTFIT, 0, "1/24  DEAD MEN > Plain clothes");
    SEQ(l, KWL_OUTFIT, 23, "24/24  DEAD MEN > Heavy armour, black shirt, black balaclava");
    /* out of range never overruns and says so */
    SEQ(l, KWL_CHAR, -1, "?/17  ?"); SEQ(l, KWL_MASK, 14, "?/14  ?"); SEQ(l, KWL_OUTFIT, 99, "?/24  ?");
    kwl_label(KWL_OUTFIT, 23, big, sizeof big); CHECK(strlen(big) == 15);   /* truncated, terminated */
    kwl_label(KWL_OUTFIT, 23, big, 0);                                      /* cap 0: no write, no crash */
    /* every label fits the 96-character HUD buffer of klcharonline.c, with the hint */
    for (w = 0; w < 3; w++) for (i = 0; i < kwl_span(w); i++) { kwl_hud(w, i, b, sizeof b); CHECK(strlen(b) < 96); CHECK(strstr(b, "/") != NULL); }
    kwl_hud(KWL_CHAR, 9, b, sizeof b); CHECK(!strcmp(b, "HEISTER 10/17  DEAD MEN > Kane"));
    kwl_hud(KWL_MASK, 10, b, sizeof b); CHECK(!strcmp(b, "MASK 11/14  PAYDAY 2 > Wolf  (Ctrl+key: outfit)"));
    kwl_hud(KWL_OUTFIT, 4, b, sizeof b); CHECK(!strcmp(b, "OUTFIT 5/24  DEAD MEN > Plain clothes, black shirt  (key: mask)"));
    /* Shift: 22 steps back from 0 = 23; back from 0 wraps to the last */
    CHECK(kwl_wrap(0, -1, 24) == 23); CHECK(kwl_wrap(23, 1, 24) == 0); CHECK(kwl_wrap(0, -1, 17) == 16); CHECK(kwl_wrap(5, -1, 14) == 4);
    { int v = 0; for (i = 0; i < 22; i++) v = kwl_wrap(v, -1, 24); CHECK(v == 2); for (i = 0; i < 24; i++) v = kwl_wrap(v, -1, 24); CHECK(v == 2); }
    CHECK(kwl_wrap(0, -1, 0) == 0);
    /* group jumps, characters: DEFAULT(0) -> DOG DAYS(1) -> DEAD MEN(9) -> DEFAULT(0), and back */
    CHECK(kwl_next_group(KWL_CHAR, 0, 1) == 1); CHECK(kwl_next_group(KWL_CHAR, 1, 1) == 9); CHECK(kwl_next_group(KWL_CHAR, 5, 1) == 9);
    CHECK(kwl_next_group(KWL_CHAR, 9, 1) == 0); CHECK(kwl_next_group(KWL_CHAR, 16, 1) == 0);
    CHECK(kwl_next_group(KWL_CHAR, 0, -1) == 9); CHECK(kwl_next_group(KWL_CHAR, 9, -1) == 1); CHECK(kwl_next_group(KWL_CHAR, 12, -1) == 1);
    CHECK(kwl_next_group(KWL_CHAR, 1, -1) == 0); CHECK(kwl_next_group(KWL_CHAR, 8, -1) == 0);
    /* masks: DEFAULT(0..1) -> DOG DAYS(2) -> PAYDAY 2(10) -> 0 */
    CHECK(kwl_next_group(KWL_MASK, 0, 1) == 2); CHECK(kwl_next_group(KWL_MASK, 1, 1) == 2); CHECK(kwl_next_group(KWL_MASK, 2, 1) == 10);
    CHECK(kwl_next_group(KWL_MASK, 13, 1) == 0); CHECK(kwl_next_group(KWL_MASK, 0, -1) == 10); CHECK(kwl_next_group(KWL_MASK, 10, -1) == 2); CHECK(kwl_next_group(KWL_MASK, 2, -1) == 0);
    /* outfits: one group, the jump stays put; bad idx is treated as 0 */
    CHECK(kwl_next_group(KWL_OUTFIT, 7, 1) == 7); CHECK(kwl_next_group(KWL_OUTFIT, 7, -1) == 7);
    CHECK(kwl_next_group(KWL_CHAR, -5, 1) == 1); CHECK(kwl_next_group(7, 0, 1) == 0);
    /* a full forward lap of group jumps visits each group once and returns */
    for (w = 0; w < 2; w++) { int v = 0, n = 0; do { v = kwl_next_group(w, v, 1); n++; } while (v != 0 && n < 10); CHECK(v == 0); CHECK(n == 3); }
    (void)g;
    printf("%d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
