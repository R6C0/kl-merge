/* klgetupbeacon_test.c - off-game harness for klgetupbeacon.h ([BotFill] OnlineGetUpBeacon pure part).
   Proves pack/unpack, dedupe, staleness, the send schedule and the seat check - NOT that the game's table index is equal on both peers (re/bot_getup_online.md section 7 lists that as a GUESS).
   Build: cl /nologo /W3 klgetupbeacon_test.c /Fe:klgetupbeacon_test.exe     Run: exit 0 = all pass */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klgetupbeacon.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    unsigned char b[64]; struct klgb_pk k, r; struct klgb_tx t; struct klgb_seat s; unsigned gap, now, seq; int d, sends, i;

    /* pack / unpack round trip */
    memset(&k, 0, sizeof k); k.ver = KLGB_VER; k.seat = 3; k.flags = 1; k.seq = 77; k.tag = klgb_tag("Locations/F04/F04_Main.gms"); k.T = 123456; k.pos[0] = -1234.5f; k.pos[1] = 50.25f; k.pos[2] = 9876.0f;
    CHECK(klgb_encode(b, sizeof b, &k) == KLGB_LEN, "encode length");
    CHECK(klgb_encode(b, 31, &k) == 0, "short buffer refused");
    CHECK(klgb_decode(b, KLGB_LEN, &r) && r.seat == 3 && r.flags == 1 && r.seq == 77 && r.tag == k.tag && r.T == 123456 && r.pos[0] == -1234.5f && r.pos[2] == 9876.0f, "round trip");
    CHECK(!klgb_decode(b, KLGB_LEN - 1, &r), "short packet refused");
    b[0] = 'X'; CHECK(!klgb_decode(b, KLGB_LEN, &r), "bad magic refused"); b[0] = 'K';
    b[5] = 2; CHECK(!klgb_decode(b, KLGB_LEN, &r), "bad version refused"); b[5] = KLGB_VER;
    b[6] = 16; CHECK(!klgb_decode(b, KLGB_LEN, &r), "seat out of range refused"); b[6] = 3;
    { float nan = (float)sqrt(-1.0); memcpy(b + 20, &nan, 4); CHECK(!klgb_decode(b, KLGB_LEN, &r), "NaN place refused"); }
    CHECK(klgb_tag("F04/x") == klgb_tag("f04/X") && klgb_tag("F04") != klgb_tag("F05"), "tag: case-blind, level-specific");

    /* send schedule: down at once, then once a second, new seq each */
    memset(&t, 0, sizeof t); now = 1000; sends = 0;
    CHECK(!klgb_tx_step(&t, 0, now, &d, &seq), "up and idle: nothing");
    CHECK(klgb_tx_step(&t, 1, now, &d, &seq) && d == 1 && seq == 1, "down edge sends at once");
    CHECK(!klgb_tx_step(&t, 1, now + 500, &d, &seq), "no second packet at 0.5 s");
    CHECK(klgb_tx_step(&t, 1, now + 1000, &d, &seq) && d == 1 && seq == 2, "next at 1.0 s with a new seq");
    CHECK(!klgb_tx_step(&t, 1, now + 1999, &d, &seq) && klgb_tx_step(&t, 1, now + 2000, &d, &seq) && seq == 3, "and at 2.0 s");
    /* getting up: 3 sends of ONE seq 100 ms apart, nothing after */
    now += 2300; sends = 0;
    for (i = 0; i < 100; i++, now += 10) if (klgb_tx_step(&t, 0, now, &d, &seq)) { sends++; CHECK(d == 0 && seq == 4, "up burst seq/flag (seq %u)", seq); }
    CHECK(sends == 3, "up burst is 3 sends, got %d", sends);
    CHECK(!klgb_tx_step(&t, 0, now + 5000, &d, &seq), "idle after the burst");
    /* down again during an up burst cancels the burst */
    memset(&t, 0, sizeof t); now = 50000;
    klgb_tx_step(&t, 1, now, &d, &seq); klgb_tx_step(&t, 0, now + 10, &d, &seq);
    CHECK(klgb_tx_step(&t, 1, now + 20, &d, &seq) && d == 1, "down again: a down packet");
    CHECK(!klgb_tx_step(&t, 1, now + 120, &d, &seq), "and no stale up repeat");
    /* tick wrap */
    memset(&t, 0, sizeof t); now = 0xffffff00u;
    CHECK(klgb_tx_step(&t, 1, now, &d, &seq) && !klgb_tx_step(&t, 1, now + 900, &d, &seq) && klgb_tx_step(&t, 1, now + 1000, &d, &seq), "schedule survives the tick wrap");

    /* host: dedupe + staleness */
    memset(&s, 0, sizeof s); k.seq = 10; k.T = 1000; k.flags = 1;
    CHECK(klgb_take(&s, &k, 5000, &gap) && gap == 0 && s.down, "first beacon taken");
    CHECK(!klgb_take(&s, &k, 5000, &gap), "same seq is a repeat");
    k.seq = 9; CHECK(!klgb_take(&s, &k, 5001, &gap), "older seq dropped");
    k.seq = 11; k.T = 2000; CHECK(klgb_take(&s, &k, 6000, &gap) && gap == 1000, "newer seq taken, sender gap 1000");
    CHECK(klgb_fresh_down(&s, 6000) && klgb_fresh_down(&s, 6000 + KLGB_FRESH_MS - 1), "fresh within 3 s");
    CHECK(!klgb_fresh_down(&s, 6000 + KLGB_FRESH_MS), "lapses at 3 s");
    k.seq = 12; k.flags = 0; k.T = 2500; CHECK(klgb_take(&s, &k, 6500, &gap) && !klgb_fresh_down(&s, 6500), "up beacon clears at once");
    k.seq = 12; k.flags = 1; CHECK(!klgb_take(&s, &k, 6600, &gap) && !klgb_fresh_down(&s, 6600), "a late repeat of an old down cannot re-down (same seq)");
    { struct klgb_seat z; memset(&z, 0, sizeof z); CHECK(!klgb_fresh_down(&z, 1), "no beacon: not down"); }
    memset(&s, 0, sizeof s); k.seq = 0xfffffffeu; klgb_take(&s, &k, 1, &gap); k.seq = 1; k.flags = 1;
    CHECK(klgb_take(&s, &k, 2, &gap), "seq wrap: 1 is newer than 0xfffffffe");

    /* seat check + nearest-replica fallback */
    {
        float bp[3] = { 1000, 0, 1000 }, rep[4][3] = { { 9000, 0, 9000 }, { 1100, 0, 1050 }, { 5000, 0, 0 }, { 1300, 0, 1000 } }; int rok[4] = { 1, 1, 1, 1 };
        CHECK(klgb_map_ok(bp, rep[1], 1) && !klgb_map_ok(bp, rep[0], 1) && klgb_map_ok(bp, rep[0], 0), "map ok: near yes, far no, unreadable trusted");
        CHECK(klgb_nearest(bp, (const float (*)[3])rep, rok, 4, 0) == 1, "nearest replica is 1");
        CHECK(klgb_nearest(bp, (const float (*)[3])rep, rok, 4, 1) == 3, "skipping 1: 3 (300 cm)");
        { float nb[3] = { 1000, 0, 1000 }, nr[3] = { 1000, 0, 1900 }, hi[3] = { 1000, 800, 1000 }; CHECK(!klgb_map_ok(nb, nr, 1), "a neighbour 9 m away does not pass (review: was 15 m)"); CHECK(!klgb_map_ok(nb, hi, 1), "another floor does not pass"); }
        rok[1] = rok[3] = 0; CHECK(klgb_nearest(bp, (const float (*)[3])rep, rok, 4, -1) == -1, "none within 600 cm");
    }

    printf("klgetupbeacon_test: %d checks, %d fail\n", checks, fails);
    return fails ? 1 : 0;
}
