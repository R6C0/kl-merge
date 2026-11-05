/* klbotvoice_test.c - off-game checks of klbotvoice_logic.h. Build: cl /nologo /W3 klbotvoice_test.c */
#include "klbotvoice_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    unsigned char b[KLBV_LEN + 8], c[KLBV_LEN + 8]; struct klbv_pk k, d; struct klbv_seqs q; struct klbv_gaps g; char key[64]; int len, i;
    memset(&k, 0, sizeof k); k.T = 123456789u; k.seq = 4660; k.ev = KLBV_EV_ESCAPE; k.digit = 5; k.var = 1;
    len = klbv_encode(b, sizeof b, &k);
    CHECK(len == KLBV_LEN); CHECK(!memcmp(b, "KLSYV\0\0\0", 8)); CHECK(b[12] == 0x34 && b[13] == 0x12);
    CHECK(klbv_decode(b, len, &d)); CHECK(d.T == k.T && d.seq == k.seq && d.ev == k.ev && d.digit == k.digit && d.var == k.var);
    CHECK(klbv_decode(b, len + 5, &d));                      /* trailing bytes are fine */
    CHECK(!klbv_decode(b, len - 1, &d)); CHECK(!klbv_decode(b, 0, &d)); CHECK(!klbv_decode(0, 40, &d));
    memcpy(c, b, len); c[0] = 'X'; CHECK(!klbv_decode(c, len, &d));
    memcpy(c, b, len); c[14] = 2; CHECK(!klbv_decode(c, len, &d));      /* version */
    memcpy(c, b, len); c[15] = 0; CHECK(!klbv_decode(c, len, &d));      /* event 0 */
    memcpy(c, b, len); c[15] = 3; CHECK(!klbv_decode(c, len, &d));      /* unknown event */
    memcpy(c, b, len); c[16] = 1; CHECK(!klbv_decode(c, len, &d));      /* digit 1 */
    memcpy(c, b, len); c[16] = 9; CHECK(!klbv_decode(c, len, &d));      /* digit 9 */
    memcpy(c, b, len); c[17] = 0; CHECK(!klbv_decode(c, len, &d));      /* variant 0 */
    memcpy(c, b, len); c[17] = 4; CHECK(!klbv_decode(c, len, &d));
    memcpy(c, b, len); c[18] = 1; CHECK(!klbv_decode(c, len, &d));      /* reserved */
    memcpy(c, b, len); c[12] = 0; c[13] = 0; CHECK(!klbv_decode(c, len, &d));      /* seq 0 */
    memcpy(c, b, len); klbv_put32(c + 8, 1000000000u); CHECK(!klbv_decode(c, len, &d));      /* T not a klsy_T() */
    k.digit = 1; CHECK(!klbv_encode(b, sizeof b, &k)); k.digit = 5; k.seq = 0; CHECK(!klbv_encode(b, sizeof b, &k)); k.seq = 1; CHECK(klbv_encode(b, KLBV_LEN - 1, &k) == 0);
    /* seq dedupe: the three sends of one event are one take; a gap is counted; stale is dropped; the wrap 65535 -> 1 is no gap */
    memset(&q, 0, sizeof q);
    CHECK(klbv_seq_take(&q, 10)); CHECK(!klbv_seq_take(&q, 10)); CHECK(!klbv_seq_take(&q, 10));
    CHECK(q.taken == 1 && q.repeats == 2 && q.lost == 0);
    CHECK(klbv_seq_take(&q, 11)); CHECK(q.lost == 0);
    CHECK(klbv_seq_take(&q, 14)); CHECK(q.lost == 2);              /* 12 and 13 never came */
    CHECK(!klbv_seq_take(&q, 12)); CHECK(q.stale == 1);            /* late: dropped, not counted twice */
    CHECK(!klbv_seq_take(&q, 14)); CHECK(q.held == 14);
    memset(&q, 0, sizeof q); CHECK(klbv_seq_take(&q, 65534)); CHECK(klbv_seq_take(&q, 65535)); CHECK(klbv_seq_take(&q, 1)); CHECK(q.lost == 0); CHECK(klbv_seq_take(&q, 2)); CHECK(q.lost == 0);
    CHECK(klbv_seq_take(&q, 4)); CHECK(q.lost == 1);
    CHECK(klbv_next_seq(1) == 2 && klbv_next_seq(65535) == 1 && klbv_next_seq(0) == 1);
    for (i = 1, k.seq = 1; i < 70000; i++) { int n = klbv_next_seq(k.seq); CHECK(n >= 1 && n <= 65535); k.seq = n; if (fails) break; }
    /* gaps: 15 s per bot and event, 2 s between any two, wrapping clock, bad args refused */
    memset(&g, 0, sizeof g);
    CHECK(klbv_gap_ok(&g, 3, KLBV_EV_LOOT, 1000)); CHECK(!klbv_gap_ok(&g, 4, KLBV_EV_LOOT, 2500)); CHECK(klbv_gap_ok(&g, 4, KLBV_EV_LOOT, 3000));
    CHECK(!klbv_gap_ok(&g, 3, KLBV_EV_LOOT, 15999)); CHECK(klbv_gap_ok(&g, 3, KLBV_EV_ESCAPE, 6000)); CHECK(klbv_gap_ok(&g, 3, KLBV_EV_LOOT, 16001));
    CHECK(!klbv_gap_ok(&g, 1, KLBV_EV_LOOT, 90000)); CHECK(!klbv_gap_ok(&g, 3, 0, 90000)); CHECK(!klbv_gap_ok(&g, 3, KLBV_NEV, 90000));
    memset(&g, 0, sizeof g);
    CHECK(klbv_gap_ok(&g, 2, KLBV_EV_LOOT, 0xfffffff0u)); CHECK(!klbv_gap_ok(&g, 2, KLBV_EV_LOOT, 5)); CHECK(klbv_gap_ok(&g, 2, KLBV_EV_LOOT, 20000));      /* across the 32-bit wrap */
    /* keys */
    CHECK(klbv_key(key, sizeof key, "Multiplayer/%L/ReachlootArea_01_C%D", "F06", 3) && !strcmp(key, "Multiplayer/F06/ReachlootArea_01_C3"));
    CHECK(klbv_key(key, sizeof key, "100%%/%X", "F06", 3) && !strcmp(key, "100%/%X"));
    CHECK(!klbv_key(key, 8, "Multiplayer/%L/x", "F06", 3)); CHECK(strlen(key) < 8);
    /* OnlineVoiceClientRetry park queue */
    { struct klbv_park q; int sq[4], n;
      memset(&q, 0, sizeof q);
      CHECK(klbv_park_add(&q, 2, 3, 9, 1000)); CHECK(!klbv_park_add(&q, 2, 3, 9, 1100)); CHECK(q.n == 1);      /* same seq twice = once */
      CHECK(!klbv_park_add(&q, 0, 3, 10, 1000)); CHECK(!klbv_park_add(&q, 3, 3, 10, 1000)); CHECK(!klbv_park_add(&q, 1, 1, 10, 1000)); CHECK(!klbv_park_add(&q, 1, 9, 10, 1000)); CHECK(q.n == 1);
      CHECK(klbv_park_add(&q, 1, 4, 10, 2000)); CHECK(klbv_park_add(&q, 1, 5, 11, 3000)); CHECK(klbv_park_add(&q, 1, 6, 12, 4000)); CHECK(q.n == 4);
      CHECK(!klbv_park_add(&q, 1, 7, 13, 4000)); CHECK(q.n == 4);                                                  /* full */
      CHECK(klbv_park_expire(&q, 7000, KLBV_PARK_MAXAGE, sq, 4) == 0 && q.n == 4);                                 /* age 6000 is not older than 6000 */
      n = klbv_park_expire(&q, 8001, KLBV_PARK_MAXAGE, sq, 4); CHECK(n == 2 && q.n == 2 && sq[0] == 9 && sq[1] == 10);
      CHECK(q.e[0].seq == 11 && q.e[1].seq == 12);                                                                   /* order kept */
      klbv_park_del(&q, 0); CHECK(q.n == 1 && q.e[0].seq == 12); klbv_park_del(&q, 5); klbv_park_del(&q, -1); CHECK(q.n == 1);
      n = klbv_park_expire(&q, 20000, KLBV_PARK_MAXAGE, 0, 0); CHECK(n == 1 && q.n == 0);
      memset(&q, 0, sizeof q); CHECK(klbv_park_add(&q, 2, 3, 1, 0xfffffff0u)); CHECK(klbv_park_expire(&q, 5, KLBV_PARK_MAXAGE, 0, 0) == 0);      /* across the 32-bit wrap */
      CHECK(klbv_park_expire(&q, 7000, KLBV_PARK_MAXAGE, 0, 0) == 1); }
    /* leaf override */
    { char lf[64]; int u;
      CHECK(klbv_pick_leaf("", "JackPot_01", lf, sizeof lf, &u) && !strcmp(lf, "JackPot_01") && !u);
      CHECK(klbv_pick_leaf(0, "JackPot_01", lf, sizeof lf, &u) && !strcmp(lf, "JackPot_01") && !u);
      CHECK(klbv_pick_leaf("JackPot_03", "JackPot_01", lf, sizeof lf, &u) && !strcmp(lf, "JackPot_03") && u);
      CHECK(klbv_pick_leaf("FA_JackPot_04", "JackPot_01", lf, sizeof lf, &u) && !strcmp(lf, "FA_JackPot_04") && u);
      CHECK(klbv_pick_leaf("a/b", "JackPot_01", lf, sizeof lf, &u) && !strcmp(lf, "JackPot_01") && !u);      /* a path is not a leaf */
      CHECK(klbv_pick_leaf("a b", "JackPot_01", lf, sizeof lf, &u) && !strcmp(lf, "JackPot_01") && !u);
      CHECK(klbv_pick_leaf("a\\b", "JackPot_01", lf, sizeof lf, &u) && !u);
      CHECK(klbv_pick_leaf("abcdefgh", "X", lf, 8, &u) && !strcmp(lf, "X") && !u);                          /* override does not fit */
      CHECK(klbv_pick_leaf("YouEsc_01", 0, lf, sizeof lf, &u) && u);
      CHECK(!klbv_pick_leaf("", "", lf, sizeof lf, &u) && !lf[0]); CHECK(!klbv_pick_leaf("", 0, lf, sizeof lf, 0));
      CHECK(!klbv_pick_leaf("a/b", "TooLongDerived", lf, 8, &u)); CHECK(!klbv_pick_leaf("x", "y", lf, 1, &u)); }
    /* speech probe helpers */
    { int n = 0, k, got = 0;
      CHECK(klbv_probe_group_idx(0x1000, 0x1000) == 0 && klbv_probe_group_idx(0x1018, 0x1000) == 1 && klbv_probe_group_idx(0x1000 + 0x8b8, 0x1000) == 93);
      CHECK(klbv_probe_group_idx(0x1001, 0x1000) == -1 && klbv_probe_group_idx(0x0fff, 0x1000) == -1 && klbv_probe_group_idx(0x3000, 0x1000) == -1);
      CHECK(klbv_probe_group_idx(0, 0x1000) == -1 && klbv_probe_group_idx(0x1000, 0) == -1);
      CHECK(!strcmp(klbv_probe_spk(0), "slot") && !strcmp(klbv_probe_spk(7), "slot") && !strcmp(klbv_probe_spk(8), "?"));
      CHECK(!strcmp(klbv_probe_spk(0xfe), "crew") && !strcmp(klbv_probe_spk(0xfffffffeul), "crew") && !strcmp(klbv_probe_spk(0xfa), "glazer"));
      CHECK(!strcmp(klbv_probe_spk(0xfd), "police") && !strcmp(klbv_probe_spk(0xfc), "driver") && !strcmp(klbv_probe_spk(0xfb), "undercover") && !strcmp(klbv_probe_spk(0xff), "?"));
      for (k = 0; k < 500; k++) got += klbv_probe_take(&n, KLBV_PROBE_CAP);
      CHECK(got == KLBV_PROBE_CAP && n == KLBV_PROBE_CAP); n = -1; CHECK(!klbv_probe_take(&n, 5)); }
    /* poll helpers */
    { int cnt[8] = {0, 2, 0, 1, 0, 0, 0, 12}; char b[64], k[8]; int ls;
      CHECK(klbv_poll_changed(0.0f, 5.0f) && klbv_poll_changed(5.0f, 21.5f) && klbv_poll_changed(30.0f, 4.0f));
      CHECK(!klbv_poll_changed(5.0f, 5.0f) && !klbv_poll_changed(5.0f, 0.0f) && !klbv_poll_changed(5.0f, -1.0f));
      { float nan = 0.0f; nan = nan / nan; CHECK(!klbv_poll_changed(1.0f, nan) && !klbv_poll_changed(nan, 1.0f)); }
      CHECK(klbv_poll_summary(b, sizeof b, cnt, 8) == 3 && !strcmp(b, "1:2 3:1 7:12"));
      CHECK(klbv_poll_summary(b, 12, cnt, 8) == 2 && !strcmp(b, "1:2 3:1..."));
      CHECK(klbv_poll_summary(b, sizeof b, cnt, 0) == 0 && !b[0]); CHECK(klbv_poll_summary(b, 4, cnt, 8) == 0);
      CHECK(klbv_poll_clean("Multi/Key", 100, k, sizeof k) == 7 && !strcmp(k, "Multi/K"));
      ls = klbv_poll_clean("a\x01z", 3, k, sizeof k); CHECK(ls == 3 && !strcmp(k, "a?z"));
      CHECK(klbv_poll_clean(0, 5, k, sizeof k) == 0 && !k[0]); CHECK(klbv_poll_clean("abc", 2, k, sizeof k) == 2 && !strcmp(k, "ab")); }
    /* OnlineBanterBots: event 3 carries a key tag in the reserved field; old receivers reject it (event >= 3 / non-zero reserved) */
    {
        unsigned char e[KLBV_LEN + 8]; struct klbv_pk bk, bd;
        memset(&bk, 0, sizeof bk); bk.T = 5000u; bk.seq = 7; bk.ev = KLBV_EV_BANTER; bk.digit = 4; bk.var = 1; bk.tag = 0xBEEF;
        CHECK(klbv_encode(e, sizeof e, &bk) == KLBV_LEN); CHECK(e[18] == 0xEF && e[19] == 0xBE);
        CHECK(klbv_decode(e, KLBV_LEN, &bd)); CHECK(bd.ev == KLBV_EV_BANTER && bd.tag == 0xBEEF && bd.digit == 4 && bd.seq == 7);
        bk.tag = 0; CHECK(!klbv_encode(e, sizeof e, &bk)); bk.tag = 65536; CHECK(!klbv_encode(e, sizeof e, &bk));
        bk.tag = 1; bk.ev = KLBV_EV_LOOT; CHECK(!klbv_encode(e, sizeof e, &bk));      /* a tag on an old event is refused */
        bk.ev = KLBV_EV_BANTER; CHECK(klbv_encode(e, sizeof e, &bk) == KLBV_LEN); e[18] = 0; e[19] = 0; CHECK(!klbv_decode(e, KLBV_LEN, &bd));      /* tag 0 */
        bk.tag = 9; klbv_encode(e, sizeof e, &bk); e[15] = KLBV_EV_ESCAPE; CHECK(!klbv_decode(e, KLBV_LEN, &bd));      /* old event with a non-zero reserved field: still refused */
        /* an OLD decoder (KLBV_NEV 3, reserved must be 0) refuses an event-3 packet: modelled here by its two rules */
        bk.ev = KLBV_EV_BANTER; bk.tag = 9; bk.seq = 8; klbv_encode(e, sizeof e, &bk); CHECK(e[15] >= 3 && (e[18] || e[19]));
        /* gaps: banter only has the 2 s global gap, never the 15 s per bot */
        memset(&g, 0, sizeof g);
        CHECK(klbv_gap_ok(&g, 4, KLBV_EV_BANTER, 1000)); CHECK(!klbv_gap_ok(&g, 4, KLBV_EV_BANTER, 2500)); CHECK(klbv_gap_ok(&g, 4, KLBV_EV_BANTER, 3100));
        CHECK(klbv_gap_ok(&g, 4, KLBV_EV_BANTER, 5200)); CHECK(klbv_gap_ok(&g, 4, KLBV_EV_LOOT, 7500));      /* banter does not use the loot slot of the digit */
        CHECK(!klbv_gap_ok(&g, 9, KLBV_EV_BANTER, 20000));
        /* member records, room, voice, status */
        CHECK(klbv_bb_rec(0) == 16 && klbv_bb_rec(15) == 31 && klbv_bb_rec(16) == -1 && klbv_bb_rec(-1) == -1);
        CHECK(klbv_bb_room(0, 32) && klbv_bb_room(31, 32) && !klbv_bb_room(32, 32) && !klbv_bb_room(-1, 32));
        CHECK(klbv_bb_voice(2) == 1 && klbv_bb_voice(8) == 7 && klbv_bb_voice(1) == -1 && klbv_bb_voice(9) == -1);
        CHECK(klbv_bb_status(3) == 4 && klbv_bb_status(4) == 0 && klbv_bb_status(0) == 0);
        /* tags and the verdict */
        CHECK(klbv_tag16(0) == 1 && klbv_tag16(0x12340000ul) == 0x1234 && klbv_tag16(0x00010001ul) == 1 && klbv_tag16(0xffffffffu) == 1 && klbv_tag16(0x1234ul) == 0x1234);
        CHECK(klbv_bb_verdict(1) == 1 && klbv_bb_verdict(0) == 0 && klbv_bb_verdict(2) == 2 && klbv_bb_verdict(-1) == 0);
    }
    printf("klbotvoice_test:%d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
