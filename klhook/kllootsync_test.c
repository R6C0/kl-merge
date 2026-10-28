/* kllootsync_test.c - off-game checks of kllootsync_logic.h. Build: cl /nologo /W3 kllootsync_test.c */
#include "kllootsync_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    unsigned char b[KLLS_HDR + KLLS_MAXN * KLLS_REC + 16]; struct klls_pk k, d; char t[300]; int len, i;
    memset(&k, 0, sizeof k);
    k.T = 123456789u; k.round = 3; k.flags = 1; k.n = 3; k.carried = 350000; k.banked = 250000;
    k.r[0].digit = 2; k.r[0].slot = 0; k.r[0].state = KLLS_ST_CARRY; k.r[0].amt = 100000;
    k.r[1].digit = 3; k.r[1].slot = 1; k.r[1].state = KLLS_ST_BOARD; k.r[1].amt = 250000;
    k.r[2].digit = 0; k.r[2].slot = 5; k.r[2].state = KLLS_ST_DEAD; k.r[2].amt = 250000;
    len = klls_encode(b, sizeof b, &k);
    CHECK(len == KLLS_HDR + 3 * KLLS_REC); CHECK(!memcmp(b, "KLSYB\0\0\0", 8));
    CHECK(klls_decode(b, len, &d)); CHECK(d.T == k.T && d.round == 3 && d.flags == 1 && d.n == 3 && d.carried == 350000 && d.banked == 250000);
    for (i = 0; i < 3; i++) CHECK(d.r[i].digit == k.r[i].digit && d.r[i].slot == k.r[i].slot && d.r[i].state == k.r[i].state && d.r[i].amt == k.r[i].amt);
    CHECK(klls_decode(b, len + 9, &d));                         /* trailing bytes are fine */
    /* strictness */
    CHECK(!klls_decode(b, len - 1, &d)); CHECK(!klls_decode(b, KLLS_HDR - 1, &d)); CHECK(!klls_decode(b, 0, &d)); CHECK(!klls_decode(0, 40, &d));
    { unsigned char c[sizeof b]; memcpy(c, b, len); c[0] = 'X'; CHECK(!klls_decode(c, len, &d));
      memcpy(c, b, len); c[14] = 2; CHECK(!klls_decode(c, len, &d));                  /* version */
      memcpy(c, b, len); c[12] = KLLS_MAXN + 1; CHECK(!klls_decode(c, len + 200, &d));             /* n > max */
      memcpy(c, b, len); c[15] = 2; CHECK(!klls_decode(c, len, &d));                  /* unknown flag */
      memcpy(c, b, len); klls_put32(c + 8, 1000000000u); CHECK(!klls_decode(c, len, &d));      /* T not a klsy_T() */
      memcpy(c, b, len); klls_put32(c + 16, 0); CHECK(!klls_decode(c, len, &d));       /* round 0 */
      memcpy(c, b, len); klls_put32(c + 20, (unsigned)-5); CHECK(!klls_decode(c, len, &d));    /* negative total */
      memcpy(c, b, len); c[KLLS_HDR + 2] = 3; CHECK(!klls_decode(c, len, &d));         /* state 3 */
      memcpy(c, b, len); c[KLLS_HDR + 1] = 64; CHECK(!klls_decode(c, len, &d));        /* slot 64 */
      memcpy(c, b, len); c[KLLS_HDR] = 10; CHECK(!klls_decode(c, len, &d));            /* digit 10 */
      memcpy(c, b, len); c[KLLS_HDR + 3] = 1; CHECK(!klls_decode(c, len, &d));         /* reserved byte */
      memcpy(c, b, len); klls_put32(c + KLLS_HDR + 4, KLLS_MAXAMT + 1); CHECK(!klls_decode(c, len, &d)); }
    k.n = KLLS_MAXN + 1; CHECK(!klls_encode(b, sizeof b, &k)); k.n = 3; CHECK(!klls_encode(b, 20, &k));
    /* stale rule: (round, T, flags, held round, held T, held flags) */
    CHECK(klls_newer(1, 5, 0, 0, 0, 0)); CHECK(klls_newer(4, 1, 0, 3, 900, 0)); CHECK(!klls_newer(2, 900, 0, 3, 1, 0));
    CHECK(klls_newer(3, 2000, 0, 3, 1000, 0)); CHECK(!klls_newer(3, 1000, 0, 3, 1000, 0)); CHECK(!klls_newer(3, 1000, 0, 3, 2000, 0));
    CHECK(klls_newer(3, 500, 0, 3, 999999000u, 0));                    /* the 1e9 wrap */
    CHECK(!klls_newer(3, 999999000u, 0, 3, 500, 0));
    CHECK(klls_newer(3, 1000, 1, 3, 1000, 0)); CHECK(klls_newer(3, 900, 1, 3, 1000, 0));      /* FINAL beats a periodic packet of the same T / an older T */
    CHECK(!klls_newer(3, 5000, 0, 3, 1000, 1)); CHECK(!klls_newer(3, 1000, 1, 3, 1000, 1));      /* nothing replaces a held FINAL; a repeat FINAL is not new */
    CHECK(klls_newer(3, 2000, 1, 3, 1000, 1)); CHECK(!klls_newer(2, 9, 1, 3, 1000, 0));
    /* text */
    klls_text(t, sizeof t, &k);
    CHECK(!strcmp(t, "BOTS carry $350,000 | banked $250,000 | 2:$100,000 3:$250,000 aboard #5:$250,000 down"));
    klls_money(t, sizeof t, 1250000); CHECK(!strcmp(t, "$1,250,000")); klls_money(t, sizeof t, 5); CHECK(!strcmp(t, "$5")); klls_money(t, sizeof t, 1005); CHECK(!strcmp(t, "$1,005"));
    klls_text(t, 60, &k); CHECK(strlen(t) < 60); CHECK(!strstr(t, "#5:$25"));        /* a record is dropped whole, never cut */
    memset(&k, 0, sizeof k); k.n = 7; for (i = 0; i < 7; i++) { k.r[i].digit = 2 + i % 7; k.r[i].slot = i; k.r[i].amt = 1000; }
    klls_text(t, sizeof t, &k); CHECK(strstr(t, " +3 more")); CHECK(!strstr(t, "6:$1,000"));      /* at most 4 records, then the count */
    memset(&k, 0, sizeof k); k.round = 1; klls_text(t, sizeof t, &k); CHECK(!strcmp(t, "BOTS carry $0 | banked $0 |"));
    printf("kllootsync_test: %d checks, %d failed\n", checks, fails);
    printf(fails ? "FAIL\n" : "ALL PASS\n");
    return fails != 0;
}
