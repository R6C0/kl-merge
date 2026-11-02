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
    CHECK(kcr_pt_usable(0x100a)); CHECK(kcr_pt_usable(0x1012)); CHECK(kcr_pt_usable(0x140a)); CHECK(!kcr_pt_usable(0x1400));   /* CR5 real ring flags (bit 2) */
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
    /* ClientRewrite (CR6) */
    CHECK(kcr_rw_pre_ok(1, 1, 8)); CHECK(kcr_rw_pre_ok(1, 1, 1)); CHECK(!kcr_rw_pre_ok(0, 1, 8)); CHECK(!kcr_rw_pre_ok(1, 0, 8)); CHECK(!kcr_rw_pre_ok(1, 1, 0)); CHECK(!kcr_rw_pre_ok(1, 1, 9));
    CHECK(kcr_rw_trigger(1, 0, 0, 0xfffffffful) == KCR_RW_STATE); CHECK(kcr_rw_trigger(0, 8, 0, 0xfffffffful) == KCR_RW_NONE);   /* spares alone never trigger the first call */
    CHECK(kcr_rw_trigger(1, 8, 1, 1499) == KCR_RW_NONE); CHECK(kcr_rw_trigger(1, 8, 1, 1500) == KCR_RW_SPARE); CHECK(kcr_rw_trigger(1, 0, 1, 9999) == KCR_RW_NONE);
    CHECK(kcr_rw_trigger(1, 8, KCR_RW_MAXTRY, 99999) == KCR_RW_NONE);
    CHECK(kcr_rw_trigger(0, 8, 2, 14999) == KCR_RW_NONE); CHECK(kcr_rw_trigger(0, 8, 2, 15000) == KCR_RW_SPARE); CHECK(kcr_rw_trigger(0, 0, 2, 99999) == KCR_RW_NONE);
    CHECK(kcr_rw_gate(1, 1, 1, 0x19)); CHECK(!kcr_rw_gate(0, 1, 1, 0x19)); CHECK(!kcr_rw_gate(1, 0, 1, 0x19)); CHECK(!kcr_rw_gate(1, 1, 0, 0x19)); CHECK(!kcr_rw_gate(1, 1, 1, 0x1a));
    CHECK(kcr_rw_after_ok(556, 556, 1)); CHECK(!kcr_rw_after_ok(556, 564, 1)); CHECK(!kcr_rw_after_ok(556, 556, 0));
    /* ClientRingSync (CR8) */
    {
        struct kcr_rhdr h, h2; struct kcr_rpt a[8], b[8]; unsigned char pk[KCR_RS_HDR + 8 * KCR_RS_REC + 8]; int i, k, len; unsigned long own[8] = { 556, 557, 558, 559, 560, 561, 562, 563 };
        memset(a, 0, sizeof a);
        for (i = 0; i < 8; i++) { a[i].idx = 556 + i; a[i].flags = (i & 1) ? 0x1412 : 0x140a; a[i].pos[0] = 3000.5f + i; a[i].pos[1] = -1230.25f; a[i].pos[2] = 12.0f; for (k = 0; k < 9; k++) a[i].blk[k] = 0x01020304ul * (unsigned long)(k + i); a[i].f24 = 0xdeadbeeful; }
        h.T = 123456789ul; h.seq = 7; h.ord = 3; h.n = 8;
        len = kcr_ring_pack(pk, sizeof pk, &h, a);
        CHECK(len == KCR_RS_HDR + 8 * KCR_RS_REC); CHECK(len <= 1472);
        CHECK(kcr_ring_unpack(pk, len, &h2, b) == 8);
        CHECK(h2.T == h.T && h2.seq == 7 && h2.ord == 3 && h2.n == 8);
        for (i = 0; i < 8; i++) { CHECK(b[i].idx == a[i].idx && b[i].flags == a[i].flags && b[i].f24 == a[i].f24 && b[i].pos[0] == a[i].pos[0] && b[i].pos[1] == a[i].pos[1] && b[i].pos[2] == a[i].pos[2]); for (k = 0; k < 9; k++) CHECK(b[i].blk[k] == a[i].blk[k]); }
        CHECK(kcr_ring_pack(pk, len - 1, &h, a) == 0);                                    /* cap too small */
        h.n = 0; CHECK(kcr_ring_pack(pk, sizeof pk, &h, a) == 0); h.n = 9; CHECK(kcr_ring_pack(pk, sizeof pk, &h, a) == 0); h.n = 8;
        h.seq = 0; CHECK(kcr_ring_pack(pk, sizeof pk, &h, a) == 0); h.seq = 7;
        a[2].idx = KCR_RS_MAXIDX; CHECK(kcr_ring_pack(pk, sizeof pk, &h, a) == 0); a[2].idx = 558;
        len = kcr_ring_pack(pk, sizeof pk, &h, a);
        pk[4] = 'X'; CHECK(kcr_ring_unpack(pk, len, &h2, b) == 0); pk[4] = 'R';              /* bad magic */
        pk[14] = 2; CHECK(kcr_ring_unpack(pk, len, &h2, b) == 0); pk[14] = 1;               /* bad version */
        CHECK(kcr_ring_unpack(pk, len - 1, &h2, b) == 0); CHECK(kcr_ring_unpack(pk, len + 1, &h2, b) == 0); CHECK(kcr_ring_unpack(pk, 10, &h2, b) == 0);   /* short / long */
        pk[15] = 9; CHECK(kcr_ring_unpack(pk, len, &h2, b) == 0); pk[15] = 0; CHECK(kcr_ring_unpack(pk, len, &h2, b) == 0); pk[15] = 8;
        pk[18] = 1; CHECK(kcr_ring_unpack(pk, len, &h2, b) == 0); pk[18] = 0;
        pk[KCR_RS_HDR + 3] = 0xff; CHECK(kcr_ring_unpack(pk, len, &h2, b) == 0); pk[KCR_RS_HDR + 3] = 0;            /* index out of range (idx >= 100000 after the high byte is set) */
        CHECK(kcr_ring_unpack(pk, len, &h2, b) == 8);
        CHECK(kcr_ring_unpack(0, len, &h2, b) == 0);
        /* apply decision: host usable + client spare = write; already usable = skip; host spare = skip */
        CHECK(kcr_ring_apply_decision(0x400, 0x140a)); CHECK(kcr_ring_apply_decision(0x400, 0x1012)); CHECK(kcr_ring_apply_decision(0, 0x200));
        CHECK(!kcr_ring_apply_decision(0x100a, 0x140a)); CHECK(!kcr_ring_apply_decision(0x1012, 0x1012));      /* client usable: never overwritten */
        CHECK(!kcr_ring_apply_decision(0x400, 0x400)); CHECK(!kcr_ring_apply_decision(0x100a, 0x400)); CHECK(!kcr_ring_apply_decision(0, 0));   /* host spare */
        /* ownership and bounds */
        CHECK(kcr_rs_idx_owned(own, 8, 556, 1580)); CHECK(kcr_rs_idx_owned(own, 8, 563, 1580)); CHECK(!kcr_rs_idx_owned(own, 8, 564, 1580));
        CHECK(!kcr_rs_idx_owned(own, 8, 560, 560)); CHECK(!kcr_rs_idx_owned(own, 4, 560, 1580)); CHECK(!kcr_rs_idx_owned(0, 8, 556, 1580));
        CHECK(kcr_rs_car_sendable(1, 8, own, 1580)); CHECK(!kcr_rs_car_sendable(0, 8, own, 1580)); CHECK(!kcr_rs_car_sendable(1, 0, own, 1580)); CHECK(!kcr_rs_car_sendable(1, 9, own, 1580)); CHECK(!kcr_rs_car_sendable(1, 8, own, 560));
        { float p1[3] = { 0, 0, 0 }, p2[3] = { 19, 0, 0 }, p3[3] = { 21, 0, 0 }; CHECK(!kcr_rs_moved(p1, p2)); CHECK(kcr_rs_moved(p1, p3)); }
        { volatile float z = 0.0f; float ok[3] = { 3425, -1230, 12 }, nan3[3] = { 0, 0, 0 }, big[3] = { 2e7f, 0, 0 }, inf3[3] = { 0, 0, 0 };
          nan3[1] = z / z; inf3[2] = 1.0f / z;
          CHECK(kcr_rs_pos_ok(ok)); CHECK(!kcr_rs_pos_ok(nan3)); CHECK(!kcr_rs_pos_ok(big)); CHECK(!kcr_rs_pos_ok(inf3)); }
        CHECK(kcr_rs_next_seq(1) == 2 && kcr_rs_next_seq(65535) == 1 && kcr_rs_next_seq(0) == 1);
    }
    printf("klcoverring_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
