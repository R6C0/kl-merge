/* klnc_test.c - OFF-GAME check of klnetchan_logic.h (the shared message channel's packet format, sanitiser, duplicate / replay filters,
 * Steam member-data ring) and klucc_logic.h ([Ucc] window, ping timing, aim pick, rate limits, names, texts). Pure code; no socket, no game.
 *   cl /nologo /W4 klnc_test.c      or      tools/run_harness_linux.sh klnc_test */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "klnetchan_logic.h"
#include "klucc_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static int split_n; static char split_last[KLNC_PKT_MAX + 1];
static void split_cb(const char *l, int n, void *ctx) { (void)ctx; split_n++; memcpy(split_last, l, (size_t)n); split_last[n] = 0; }

int main(void)
{
    char pkt[KLNC_PKT_MAX + 1], big[400], v[1024], nm[KLUC_NAME], t[KLUC_TEXT]; struct knc_msg m; int n, i, lo, hi, e;
    struct knc_seen seen; struct knc_hw hw; struct knc_ring ring; struct kluc_rl rl; struct kluc_key k; unsigned rng;

    /* ---- packet build / parse round trip */
    n = knc_build(pkt, sizeof pkt, 0x1a2b3c4du, 2, 5, 7, "UPING", "Someone saw Kane; talking");
    CHECK(n > 0); CHECK(!strcmp(pkt, "KLNC1;1a2b3c4d;2;5;7;UPING;Someone saw Kane; talking"));
    CHECK(knc_parse(pkt, n, &m));
    CHECK(m.sid == 0x1a2b3c4du && m.role == 2 && m.ent == 5 && m.seq == 7);
    CHECK(!strcmp(m.type, "UPING")); CHECK(!strcmp(m.payload, "Someone saw Kane; talking"));   /* ';' inside the payload survives */
    n = knc_build(pkt, sizeof pkt, 1, 3, -1, 4000000000u, "HELLO", "");
    CHECK(n > 0 && knc_parse(pkt, n, &m) && m.ent == -1 && m.seq == 4000000000u && m.payload[0] == 0 && m.sid == 1);
    /* bad types / roles refused at build */
    CHECK(!knc_build(pkt, sizeof pkt, 1, 2, 0, 1, "uping", "x"));         /* lower case */
    CHECK(!knc_build(pkt, sizeof pkt, 1, 2, 0, 1, "A", "x"));             /* too short */
    CHECK(!knc_build(pkt, sizeof pkt, 1, 2, 0, 1, "ABCDEFGHI", "x"));     /* too long (9) */
    CHECK(knc_build(pkt, sizeof pkt, 1, 2, 0, 1, "ABCDEFGH", "x") > 0);   /* 8 is the most */
    CHECK(!knc_build(pkt, sizeof pkt, 1, 2, 0, 1, "UP;NG", "x"));
    CHECK(!knc_build(pkt, sizeof pkt, 1, 10, 0, 1, "UPING", "x"));
    CHECK(!knc_build(pkt, sizeof pkt, 1, 2, 0, 1, 0, "x"));
    /* entity out of range becomes -1 */
    n = knc_build(pkt, sizeof pkt, 1, 2, 99, 1, "UACC", "a"); CHECK(n > 0 && knc_parse(pkt, n, &m) && m.ent == -1);
    /* payload: control bytes and the ring separator are replaced, length capped */
    n = knc_build(pkt, sizeof pkt, 1, 2, 0, 1, "UACC", "a\nb\rc`d\x01" "e\x80" "f");
    CHECK(n > 0 && knc_parse(pkt, n, &m)); CHECK(!strcmp(m.payload, "a b c'd e f"));
    CHECK(strchr(pkt, KLNC_SEP) == 0 && strchr(pkt, '\n') == 0);
    memset(big, 'x', sizeof big); big[sizeof big - 1] = 0;
    n = knc_build(pkt, sizeof pkt, 1, 2, 0, 1, "UACC", big); CHECK(n > 0 && n < KLNC_PKT_MAX && knc_parse(pkt, n, &m) && strlen(m.payload) == KLNC_PAY_MAX - 1);
    /* parse refuses garbage */
    CHECK(!knc_parse("KLCH1;i1c2m3o4", 14, &m));
    CHECK(!knc_parse("KLNC1;1a2b3c4d;2;5;7;UPING", 26, &m));            /* no payload field */
    CHECK(!knc_parse("KLNC1;1a2b3c4;2;5;7;UPING;x", 27, &m));           /* 7 hex */
    CHECK(!knc_parse("KLNC1;1a2b3c4g;2;5;7;UPING;x", 28, &m));          /* not hex */
    CHECK(!knc_parse("KLNC1;1a2b3c4d;22;5;7;UPING;x", 29, &m));         /* role 2 digits */
    CHECK(!knc_parse("KLNC1;1a2b3c4d;2;64;7;UPING;x", 29, &m));         /* ent 64 */
    CHECK(!knc_parse("KLNC1;1a2b3c4d;2;-2;7;UPING;x", 29, &m));
    CHECK(!knc_parse("KLNC1;1a2b3c4d;2;5;-7;UPING;x", 29, &m));         /* negative seq */
    CHECK(!knc_parse("KLNC1;1a2b3c4d;2;5;7x;UPING;x", 29, &m));
    CHECK(!knc_parse("KLNC1;1a2b3c4d;2;5;7;up;x", 25, &m));
    CHECK(!knc_parse("KLNC1;1a2b3c4d;2;;7;UPING;x", 27, &m));           /* empty ent */
    CHECK(!knc_parse(0, 10, &m)); CHECK(!knc_parse("KLNC1;", 6, &m));
    memset(big, 'A', 300); CHECK(!knc_parse(big, 300, &m));              /* over the packet size */
    /* parse uses len, not a terminator */
    n = knc_build(pkt, sizeof pkt, 0xdeadbeefu, 3, 2, 9, "UACC", "Bob suspects Al");
    pkt[n] = 'Z'; CHECK(knc_parse(pkt, n, &m) && !strcmp(m.payload, "Bob suspects Al")); pkt[n] = 0;

    /* ---- duplicate filter + replay guard */
    memset(&seen, 0, sizeof seen); memset(&hw, 0, sizeof hw);
    CHECK(knc_seen_new(&seen, 1, 1)); CHECK(!knc_seen_new(&seen, 1, 1)); CHECK(knc_seen_new(&seen, 2, 1)); CHECK(knc_seen_new(&seen, 1, 2));
    for (i = 0; i < KLNC_SEEN; i++) knc_seen_new(&seen, 9, 100 + i);   /* push (1,1) out of the ring */
    CHECK(knc_seen_new(&seen, 1, 1));                                    /* forgotten by the ring ... */
    CHECK(knc_hw_ok(&hw, 1, 20)); CHECK(knc_hw_ok(&hw, 1, 21)); CHECK(knc_hw_ok(&hw, 1, 14));   /* 14 + 8 > 21: still taken */
    CHECK(!knc_hw_ok(&hw, 1, 13));                                       /* ... but the replay guard stops it: 13 + 8 <= 21 */
    CHECK(knc_hw_ok(&hw, 2, 0)); CHECK(knc_hw_ok(&hw, 1, 30)); CHECK(!knc_hw_ok(&hw, 1, 21));
    for (i = 0; i < KLNC_HW + 4; i++) knc_hw_ok(&hw, 100 + i, 50);       /* table full: new senders pass unguarded */
    CHECK(knc_hw_ok(&hw, 999, 1)); CHECK(knc_hw_ok(&hw, 999, 0));

    /* ---- Steam ring */
    memset(&ring, 0, sizeof ring);
    CHECK(knc_ring_join(&ring, v, sizeof v) == 0 && v[0] == 0);
    for (i = 1; i <= 6; i++) { n = knc_build(pkt, sizeof pkt, 0xabcu, 2, 0, (unsigned)i, "UPING", "p"); knc_ring_push(&ring, pkt); }
    CHECK(ring.n == KLNC_RING);
    knc_ring_join(&ring, v, sizeof v);
    split_n = 0; CHECK(knc_ring_split(v, split_cb, 0) == 4); CHECK(split_n == 4);
    CHECK(knc_parse(split_last, (int)strlen(split_last), &m) && m.seq == 6);    /* newest last */
    split_n = 0; knc_ring_split(v, split_cb, 0);
    { const char *f = v; struct knc_msg m0; const char *e0 = strchr(f, KLNC_SEP); CHECK(e0 && knc_parse(f, (int)(e0 - f), &m0) && m0.seq == 3); }
    CHECK(knc_ring_join(&ring, v, 50) < 50);                             /* a short buffer: whole lines only */
    split_n = 0; CHECK(knc_ring_split("", split_cb, 0) == 0); CHECK(knc_ring_split("``a``", split_cb, 0) == 1);

    /* ---- UCC window */
    CHECK(kluc_gate(2, 4, 0x19, 1)); CHECK(kluc_gate(3, 4, 0x1e, 1));
    CHECK(!kluc_gate(2, 4, 0x18, 1)); CHECK(!kluc_gate(2, 4, 0x1f, 1));
    CHECK(!kluc_gate(2, 4, 0x19, 0)); CHECK(!kluc_gate(2, 4, 0x19, 2)); CHECK(!kluc_gate(0, 4, 0x19, 1)); CHECK(!kluc_gate(1, 4, 0x19, 1)); CHECK(!kluc_gate(2, 3, 0x19, 1));

    /* ---- ping timing and picks */
    kluc_ping_range(60, 120, &lo, &hi); CHECK(lo == 60 && hi == 120);
    kluc_ping_range(1, 5, &lo, &hi); CHECK(lo == 10 && hi == 10);
    kluc_ping_range(700, 2000, &lo, &hi); CHECK(lo == 600 && hi == 900);
    kluc_ping_range(90, 30, &lo, &hi); CHECK(lo == 90 && hi == 90);
    rng = 0; { int ok = 1, sawlo = 0, sawhi = 0; for (i = 0; i < 5000; i++) { unsigned long w = kluc_next_ms(&rng, 60, 120); if (w < 60000 || w > 120000) ok = 0; if (w < 61000) sawlo = 1; if (w > 119000) sawhi = 1; } CHECK(ok); CHECK(sawlo && sawhi); }
    CHECK(kluc_next_ms(&rng, 10, 10) == 10000);
    CHECK(rng != 0);
    rng = 12345; { int cnt[5] = { 0 }, ok = 1; for (i = 0; i < 5000; i++) { int p = kluc_pick(&rng, 5); if (p < 0 || p > 4) ok = 0; else cnt[p]++; } CHECK(ok); for (i = 0; i < 5; i++) CHECK(cnt[i] > 800); }
    CHECK(kluc_pick(&rng, 0) == -1); CHECK(kluc_pick(&rng, 1) == 0);

    /* ---- aim pick: eye at origin, looking down +z */
    {
        struct kluc_body b[4]; float eye[3] = { 0, 0, 0 }, aim[3] = { 0, 0, 1000 }, cos15 = (float)cos(15.0 * 3.14159265 / 180.0);
        b[0].ent = 3; b[0].p[0] = 0;    b[0].p[1] = 0; b[0].p[2] = 2000;   /* dead ahead, 20 m */
        b[1].ent = 7; b[1].p[0] = 200;  b[1].p[1] = 0; b[1].p[2] = 1000;   /* ~11 deg off, 10 m */
        b[2].ent = 9; b[2].p[0] = 1000; b[2].p[1] = 0; b[2].p[2] = 1000;   /* 45 deg */
        b[3].ent = 1; b[3].p[0] = 0;    b[3].p[1] = 0; b[3].p[2] = -500;   /* behind */
        CHECK(kluc_aim_pick(eye, aim, b, 4, cos15, 4000) == 0);
        CHECK(kluc_aim_pick(eye, aim, b, 4, cos15, 1500) == 1);            /* the straight one out of range: the 11 deg one */
        CHECK(kluc_aim_pick(eye, aim, b + 2, 2, cos15, 4000) == -1);       /* only 45 deg and behind: nobody */
        { float a2[3] = { 0, 0, 0.5f }; CHECK(kluc_aim_pick(eye, a2, b, 4, cos15, 4000) == -1); }   /* degenerate ray */
        { struct kluc_body c = b[0]; c.p[2] = 30; CHECK(kluc_aim_pick(eye, aim, &c, 1, cos15, 4000) == -1); }   /* too close (< 0.5 m) */
        { float z = 0; struct kluc_body c = b[0]; c.p[0] = z / z; CHECK(kluc_aim_pick(eye, aim, &c, 1, cos15, 4000) == -1); }   /* NaN body */
        CHECK(kluc_nearest(eye, b, 4, 4000) == 3);                         /* behind but nearest (5 m) */
        CHECK(kluc_nearest(eye, b, 4, 400) == -1);
        CHECK(kluc_nearest(eye, b, 0, 4000) == -1);
    }

    /* ---- rate limits */
    memset(&rl, 0, sizeof rl);
    CHECK(kluc_rl_ok(&rl, 0xa, 1000, 16000)); CHECK(!kluc_rl_ok(&rl, 0xa, 5000, 16000)); CHECK(kluc_rl_ok(&rl, 0xb, 5000, 16000));
    CHECK(!kluc_rl_ok(&rl, 0xa, 16999, 16000)); CHECK(kluc_rl_ok(&rl, 0xa, 17000, 16000)); CHECK(!kluc_rl_ok(&rl, 0xa, 17001, 16000));
    for (i = 0; i < KLUC_RL + 3; i++) kluc_rl_ok(&rl, 0x100 + i, 20000, 16000);    /* more senders than slots: the table cycles */
    CHECK(rl.n == KLUC_RL);
    CHECK(kluc_rl_ok(&rl, 0x5555, 0, 16000));                              /* now 0 is stored as 1 */
    CHECK(kluc_wait_left(0, 5000, 20000) == 0); CHECK(kluc_wait_left(1000, 5000, 20000) == 16000); CHECK(kluc_wait_left(1000, 21000, 20000) == 0);
    CHECK(kluc_wait_left(0xfffff000ul, 0x1000ul, 20000) == 20000 - 0x2000);   /* tick wrap */

    /* ---- key edge */
    memset(&k, 0, sizeof k);
    CHECK(!kluc_edge(&k, 0, 10)); CHECK(kluc_edge(&k, 1, 20)); CHECK(!kluc_edge(&k, 1, 40)); CHECK(!kluc_edge(&k, 0, 60));
    CHECK(!kluc_edge(&k, 1, 100)); CHECK(!kluc_edge(&k, 0, 120)); CHECK(kluc_edge(&k, 1, 400)); CHECK(!kluc_edge(&k, 1, 99999));

    /* ---- names */
    kluc_clean_name("  Josh|Pulse  ", 2, nm); CHECK(!strcmp(nm, "JoshPulse"));
    kluc_clean_name("", 2, nm); CHECK(!strcmp(nm, "Player 3"));
    kluc_clean_name("   ", 0, nm); CHECK(!strcmp(nm, "Player 1"));
    kluc_clean_name(0, 4, nm); CHECK(!strcmp(nm, "Player 5"));
    kluc_clean_name("\x01\x02", 1, nm); CHECK(!strcmp(nm, "Player 2"));
    kluc_clean_name("abcdefghijabcdefghijabcdefghijabcdefghij", 1, nm); CHECK(strlen(nm) == KLUC_NAME - 1);
    CHECK(kluc_hello_parse("3|Josh", &e, nm) && e == 3 && !strcmp(nm, "Josh"));
    CHECK(kluc_hello_parse("0|", &e, nm) && e == 0 && !strcmp(nm, "Player 1"));
    CHECK(!kluc_hello_parse("32|x", &e, nm)); CHECK(!kluc_hello_parse("-1|x", &e, nm)); CHECK(!kluc_hello_parse("3x", &e, nm)); CHECK(!kluc_hello_parse("|x", &e, nm)); CHECK(!kluc_hello_parse(0, &e, nm));

    /* ---- texts: every variant names the player, fits a packet's payload, variant wraps */
    for (i = -2; i < KLUC_PING_VARIANTS + 2; i++) { kluc_ping_text(i, "Josh", t, sizeof t); CHECK(strstr(t, "Josh") != 0); CHECK((int)strlen(t) < KLNC_PAY_MAX); }
    kluc_ping_text(0, "Josh", t, sizeof t); CHECK(!strcmp(t, "Word is Josh is working with the cops"));
    kluc_ping_text(KLUC_PING_VARIANTS, "Josh", t, sizeof t); CHECK(!strcmp(t, "Word is Josh is working with the cops"));
    kluc_accuse_text("Al", "Bob", t, sizeof t); CHECK(!strcmp(t, "Al suspects Bob"));
    {   /* two longest names still fit one packet */
        char a[KLUC_NAME], b2[KLUC_NAME]; memset(a, 'A', KLUC_NAME - 1); a[KLUC_NAME - 1] = 0; memset(b2, 'B', KLUC_NAME - 1); b2[KLUC_NAME - 1] = 0;
        kluc_accuse_text(a, b2, t, sizeof t);
        n = knc_build(pkt, sizeof pkt, 0xffffffffu, 3, 63, 4294967295u, "UACC", t);
        CHECK(n > 0 && knc_parse(pkt, n, &m) && !strcmp(m.payload, t));
        for (i = 0; i < KLUC_PING_VARIANTS; i++) { kluc_ping_text(i, a, t, sizeof t); n = knc_build(pkt, sizeof pkt, 0xffffffffu, 2, 63, 4294967295u, "UPING", t); CHECK(n > 0 && knc_parse(pkt, n, &m) && !strcmp(m.payload, t)); }
    }

    printf("%d checks, %d failed\n", checks, fails);
    printf(fails ? "FAIL\n" : "ALL PASS\n");
    return fails ? 1 : 0;
}
