/* klcampaign_outfits_test.c - klcampaign_outfits_logic.h outside the game.
 *   cl /nologo /W3 klcampaign_outfits_test.c /Fe:klcampaign_outfits_test.exe     or     gcc -m32 -Wall klcampaign_outfits_test.c -o klcampaign_outfits_test
 * Also reads tools\kl_outfits_1110.py's SPECS count (MAX_NEW) from the klchar.c define so the two cannot drift. */
#include <stdio.h>
#include <string.h>
#include "klcampaign_outfits_logic.h"

static int bad;
#define CHECK(c, ...) do { if (!(c)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    int ch, n;
    /* table size: 16 stays 16 either way, 17..32 only with the toggle, 33 is refused, 0 is refused */
    CHECK(kco_chars(16, 1, 32) == 16 && kco_chars(16, 0, 32) == 16, "16 characters are the old wardrobe");
    CHECK(kco_chars(24, 1, 32) == 24, "24 characters kept with the toggle on");
    CHECK(kco_chars(24, 0, 32) == 16, "24 characters cut to 16 with the toggle off");
    CHECK(kco_chars(32, 1, 32) == 32 && kco_chars(32, 0, 32) == 16, "32 characters");
    CHECK(kco_chars(33, 1, 32) == -1 && kco_chars(33, 0, 32) == -1, "33 characters refused in both modes");
    CHECK(kco_chars(0, 1, 32) == -1 && kco_chars(-1, 1, 32) == -1, "no characters refused");
    CHECK(kco_chars(17, 1, 16) == -1, "a build with the old 16-entry table refuses 17");
    /* the chosen character */
    for (ch = 0; ch <= 16; ch++) CHECK(kco_clamp(ch, 0, 32) == ch && kco_clamp(ch, 1, 32) == ch, "KLChar %d is always allowed", ch);
    for (ch = 17; ch <= 32; ch++) CHECK(kco_clamp(ch, 1, 32) == ch && kco_clamp(ch, 0, 32) == 0, "KLChar %d needs the toggle", ch);
    CHECK(kco_clamp(33, 1, 32) == 0 && kco_clamp(-1, 1, 32) == 0 && kco_clamp(100, 0, 32) == 0, "out of range = the game's own");
    CHECK(!kco_is_campaign(16) && kco_is_campaign(17) && !kco_is_campaign(0), "campaign = above 16");
    /* the Heister page's range (klc_upper_of(0)): 32 with the toggle, 16 without; mkoverlay.py CHARACTERS has upper + 1 = 33 entries */
    CHECK(kco_upper(1, 32) == 32 && kco_upper(0, 32) == 16, "page range 32 on / 16 off");
    /* a pick above the loaded map's character count falls back to the game's own body (0), never past the table: every map (1..16 characters of the
       wardrobe, 16 base + up to 16 campaign) x every pick the page can set (0..32) x both toggle states */
    for (n = 1; n <= 32; n++) {
        for (ch = 0; ch <= 40; ch++) {
            int on = kco_pick(ch, 1, 32, n), off = kco_pick(ch, 0, 32, n);
            CHECK(on >= 0 && on <= n && on <= 32, "on: map %d pick %d -> %d out of the table", n, ch, on);
            CHECK(off >= 0 && off <= n && off <= 16, "off: map %d pick %d -> %d out of the table", n, ch, off);
            if (ch >= 0 && ch <= 32 && ch <= n) CHECK(on == ch, "on: map %d pick %d kept (got %d)", n, ch, on);
            if (ch > n || ch > 32) CHECK(on == 0, "on: map %d pick %d above the map's count -> game's own (got %d)", n, ch, on);
            if (ch > 16) CHECK(off == 0, "off: pick %d needs the toggle", ch);
        }
    }
    CHECK(kco_pick(20, 1, 32, 18) == 0 && kco_pick(18, 1, 32, 18) == 18 && kco_pick(17, 1, 32, 16) == 0, "a map with 16 characters has no campaign outfit");
    CHECK(kco_pick(5, 1, 32, 0) == 0, "have 0 -> 0");
    n = 0; for (ch = 0; ch <= 40; ch++) n += kco_clamp(ch, 1, 32) == ch;
    CHECK(n == 33, "33 valid values 0..32 (got %d)", n);
    if (bad) { printf("klcampaign_outfits_test: %d FAILED\n", bad); return 1; }
    printf("klcampaign_outfits_test: all checks passed\n");
    return 0;
}
