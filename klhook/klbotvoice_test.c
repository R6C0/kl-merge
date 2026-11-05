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
    printf("klbotvoice_test:%d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
