/* klcoverring_test.c - off-game checks of klcoverring_logic.h. Build: cl /nologo /W3 klcoverring_test.c */
#include <stdio.h>
#include "klcoverring_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    unsigned long s1, s2, s3;
    /* schedule */
    CHECK(kcr_due(0, 0xfffffffful));                      /* never polled: due */
    CHECK(kcr_due(10, 0));                                /* fast window: every tick */
    CHECK(kcr_due(KCR_FAST_MS - 1, 0));
    CHECK(!kcr_due(KCR_FAST_MS, 4999));                   /* slow window: 5 s apart */
    CHECK(kcr_due(KCR_FAST_MS, 5000));
    CHECK(kcr_due(500000ul, 12000));
    CHECK(!kcr_due(500000ul, 1));
    /* change detection */
    CHECK(kcr_changed(0, 0, 0, 0, 0));                    /* first sample always logs */
    CHECK(!kcr_changed(1, 347, 347, 5, 5));
    CHECK(kcr_changed(1, 347, 355, 5, 5));
    CHECK(kcr_changed(1, 347, 347, 5, 6));
    /* signature: order and flag sensitive */
    s1 = kcr_sig_add(kcr_sig_add(0, 0x1000, 0x2000, 8, 1, 1), 0x3000, 0x4000, 0, 0, 0);
    s2 = kcr_sig_add(kcr_sig_add(0, 0x3000, 0x4000, 0, 0, 0), 0x1000, 0x2000, 8, 1, 1);
    s3 = kcr_sig_add(kcr_sig_add(0, 0x1000, 0x2000, 8, 0, 1), 0x3000, 0x4000, 0, 0, 0);
    CHECK(s1 != s2); CHECK(s1 != s3);
    CHECK(kcr_sig_add(0, 1, 2, 3, 0x101, 0) == kcr_sig_add(0, 1, 2, 3, 1, 0));   /* flags are bytes */
    /* sanity helpers */
    CHECK(kcr_count_sane(355)); CHECK(!kcr_count_sane(0xdeadbeef));
    CHECK(kcr_script_matches(0x1234, 0x1234)); CHECK(!kcr_script_matches(0x1234, 0x1235)); CHECK(!kcr_script_matches(0, 0));
    CHECK(kcr_idx_shown(3) == 3 && kcr_idx_shown(8) == 8 && kcr_idx_shown(99) == 8);
    CHECK(kcr_surplus(347 + 16, 347, 2) == 0); CHECK(kcr_surplus(347, 347, 1) == -8); CHECK(kcr_surplus(363, 347, 1) == 8);
    /* ClientBuild gate */
    CHECK(kcr_cb_role_ok(3, 4, 0)); CHECK(!kcr_cb_role_ok(2, 4, 0)); CHECK(!kcr_cb_role_ok(0, 0, 0)); CHECK(!kcr_cb_role_ok(3, 1, 0));
    CHECK(kcr_cb_fits(347, 4, 1371)); CHECK(kcr_cb_fits(556, 5, 1580)); CHECK(kcr_cb_fits(8, 1, 16)); CHECK(!kcr_cb_fits(9, 1, 16)); CHECK(!kcr_cb_fits(0, 1, 0));
    CHECK(kcr_pt_usable(0x368)); CHECK(kcr_pt_usable(0x200)); CHECK(!kcr_pt_usable(0x400)); CHECK(!kcr_pt_usable(0));
    CHECK(kcr_cb_role_ok(3, 4, 1)); CHECK(kcr_cb_role_ok(2, 4, 1)); CHECK(!kcr_cb_role_ok(2, 1, 1)); CHECK(!kcr_cb_role_ok(0, 4, 1));
    CHECK(kcr_cb_map_listed("F01,F03", "f01\\f01_main")); CHECK(kcr_cb_map_listed("F01,F03", "F03/F03_Main")); CHECK(kcr_cb_map_listed("f01 f03", "f03"));
    CHECK(!kcr_cb_map_listed("F01,F03", "f02\\f02_main")); CHECK(!kcr_cb_map_listed("F01,F03", "f011\\x")); CHECK(!kcr_cb_map_listed("F01", "f0\\x"));
    CHECK(!kcr_cb_map_listed("", "f01\\f01_main")); CHECK(!kcr_cb_map_listed("F01", "")); CHECK(!kcr_cb_map_listed(0, "f01")); CHECK(kcr_cb_map_listed(" ; F09 ,F01", "f01\\f01_main"));
    CHECK(kcr_cb_car_ok(1, 0, 0)); CHECK(!kcr_cb_car_ok(0, 0, 0)); CHECK(!kcr_cb_car_ok(1, 1, 0)); CHECK(!kcr_cb_car_ok(1, 0, 1)); CHECK(kcr_cb_car_ok(1, 0x100, 0x200));
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x16, 1, 5, 3000, 1000) == KCR_CB_GO);
    CHECK(kcr_cb_gate(0, 1, 1, 0, 0x16, 1, 5, 3000, 1000) == KCR_CB_OFF);
    CHECK(kcr_cb_gate(1, 1, 0, 0, 0x16, 1, 5, 3000, 1000) == KCR_CB_OFF);
    CHECK(kcr_cb_gate(1, 0, 1, 0, 0x16, 1, 5, 3000, 1000) == KCR_CB_NOT_CLIENT);       /* host never builds */
    CHECK(kcr_cb_gate(1, 1, 1, 1, 0x16, 1, 5, 3000, 1000) == KCR_CB_DONE);             /* once per load */
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x1a, 1, 5, 3000, 1000) == KCR_CB_STATE);
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x19, 1, 5, 3000, 1000) == KCR_CB_GO);
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x16, 0, 0, 3000, 0) == KCR_CB_WAIT_LIST);
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x16, 1, 0, 3000, 5000) == KCR_CB_WAIT_CARS);
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x16, 1, 5, 3000, 999) == KCR_CB_WAIT_STABLE);
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x16, 0, 0, KCR_CB_GIVEUP_MS, 0) == KCR_CB_GAVE_UP);
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x16, 1, 0, KCR_CB_GIVEUP_MS, 5000) == KCR_CB_GAVE_UP);
    CHECK(kcr_cb_gate(1, 1, 1, 0, 0x16, 1, 3, KCR_CB_GIVEUP_MS, 5000) == KCR_CB_GO);   /* cars and list present: late is still fine */
    printf("klcoverring_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
