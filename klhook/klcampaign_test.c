/* klcampaign_test.c - off-game checks of klcampaign_logic.h. Build: cl /nologo /W3 klcampaign_test.c */
#include <stdio.h>
#include "klcampaign_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    CHECK(klcmp_key_is_campaign("m01\\m01_main"));
    CHECK(klcmp_key_is_campaign("m03b\\m03b_main"));
    CHECK(klcmp_key_is_campaign("m07f\\m07f_main"));
    CHECK(klcmp_key_is_campaign("m14\\m14_main"));
    CHECK(!klcmp_key_is_campaign("f01\\f01_main"));          /* FA slots, also the KLExpansion Dead Men FA maps */
    CHECK(!klcmp_key_is_campaign("l01\\l01_main"));          /* Dog Days story */
    CHECK(!klcmp_key_is_campaign("m1\\m1_main"));
    CHECK(!klcmp_key_is_campaign("m01"));                    /* no folder part */
    CHECK(!klcmp_key_is_campaign("m01abc\\x"));              /* at most two letters */
    CHECK(!klcmp_key_is_campaign("dm01\\dm01_main"));
    CHECK(!klcmp_key_is_campaign(""));
    CHECK(!klcmp_key_is_campaign(0));
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
