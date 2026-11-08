/* klshopset_test.c - off-game checks of klshopset.h (the page II set check: hash, SHPH payload, decision table).
 * Build: cl /nologo /W3 klshopset_test.c      Run: klshopset_test.exe
 * Optional (Windows only): klshopset_test.exe <KLShopPage.ini> <expected 8 hex>  reads the ini with the SAME API calls as klshoppage.c kspg_load
 * (GetPrivateProfileInt/String) and checks the hash and the Python twin's value, e.g. for the live <DD>\KLShopPage.ini.
 * The golden vectors below are the same ones tools/kl_fallback_guns_test.py checks against kl_fallback_guns.set_hash(). */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <limits.h>
#ifdef _WIN32
#include <windows.h>
#endif
#include "klshopset.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static void rows_clear(struct kss_row *r) { memset(r, 0, KSS_ROWS * sizeof *r); }
static void put(struct kss_row *r, int row, int item, int pic) { r[row].ok = 1; r[row].item = item; r[row].pic = pic; }

#ifdef _WIN32
static unsigned ini_hash(const char *file, int *n)
{
    struct kss_row r[KSS_ROWS]; char buf[520], key[16], nm[64]; int i, cnt;
    rows_clear(r);
    cnt = (int)GetPrivateProfileIntA("Pairs", "Count", 0, file);
    if (cnt < 0 || cnt > KSS_ROWS) cnt = 0;
    for (i = 0; i < cnt; i++) {
        int row = -1, item = 0, pic = -1, c = 0;
        sprintf(key, "P%d", i);
        GetPrivateProfileStringA("Pairs", key, "", buf, sizeof buf, file);
        if (sscanf(buf, "%d|%d|%d|%n", &row, &item, &pic, &c) < 3 || !c || row < 0 || row >= KSS_ROWS || item < 1 || item > 63) continue;
        put(r, row, item, pic);
    }
    GetPrivateProfileStringA("Set", "Name", "", nm, sizeof nm, file);
    *n = kss_count(r);
    return kss_hash(r, nm);
}
#endif

int main(int argc, char **argv)
{
    struct kss_row r[KSS_ROWS]; struct kss_msg m; struct kss_peers pe; char b[KSS_CANON_MAX + 8], nm[KSS_NAME_MAX], pay[64]; int i, k;

    /* FNV-1a 32 reference vectors */
    CHECK(kss_fnv("", 0) == 0x811c9dc5u); CHECK(kss_fnv("a", 1) == 0xe40c292cu); CHECK(kss_fnv("foobar", 6) == 0xbf9cf968u);

    /* name normalisation: token, lower case, comment cut, default pd2 */
    kss_name("dm", nm); CHECK(!strcmp(nm, "dm"));
    kss_name("  DM ; pd2|dm|stock", nm); CHECK(!strcmp(nm, "dm"));
    kss_name("PD2 ; comment", nm); CHECK(!strcmp(nm, "pd2"));
    kss_name("", nm); CHECK(!strcmp(nm, "pd2")); kss_name(0, nm); CHECK(!strcmp(nm, "pd2"));
    kss_name(";x", nm); CHECK(!strcmp(nm, "pd2")); kss_name("my set", nm); CHECK(!strcmp(nm, "my"));
    kss_name("abcdefghijklmnopqrstuvwxyz", nm); CHECK(!strcmp(nm, "abcdefghijklmno") && strlen(nm) == 15);
    CHECK(kss_type("dm") == 1 && kss_type("PD2") == 0 && kss_type("stock") == 2 && kss_type("other") == 3 && kss_type("") == 0);

    /* golden canonical strings + hashes (same as tools/kl_fallback_guns_test.py) */
    rows_clear(r); put(r, 0, 62, 3); put(r, 10, 63, 5);
    CHECK(kss_canon(r, "dm", b, sizeof b) == (int)strlen("KLSET1\n0|62|3\n10|63|5\nS=dm\n") && !strcmp(b, "KLSET1\n0|62|3\n10|63|5\nS=dm\n"));
    CHECK(kss_hash(r, "dm") == 0x6fde7f5cu);
    CHECK(kss_hash(r, "PD2 ; comment") == 0x94f99dd5u); CHECK(kss_hash(r, 0) == 0x94f99dd5u); CHECK(kss_hash(r, "") == 0x94f99dd5u);
    CHECK(kss_count(r) == 2);
    rows_clear(r); put(r, 0, 40, 7); put(r, 10, 63, 5);
    CHECK(kss_hash(r, "") == 0xd8103e59u);
    rows_clear(r); CHECK(kss_hash(r, "") == 0x9b4c41d5u); CHECK(kss_count(r) == 0);
    /* names, descriptions are not an input; the hash differs by item, pic, row and set name */
    rows_clear(r); put(r, 0, 62, 3); put(r, 10, 63, 5);
    { unsigned base = kss_hash(r, "dm"); r[0].item = 61; CHECK(kss_hash(r, "dm") != base); r[0].item = 62; r[0].pic = 4; CHECK(kss_hash(r, "dm") != base); r[0].pic = 3; CHECK(kss_hash(r, "dm") == base);
      CHECK(kss_hash(r, "stock") != base); r[0].ok = 0; r[1].ok = 1; r[1].item = 62; r[1].pic = 3; CHECK(kss_hash(r, "dm") != base); }
    /* every row used still fits the canonical buffer */
    rows_clear(r); for (i = 0; i < KSS_ROWS; i++) put(r, i, 63, 99999);
    CHECK(kss_canon(r, "abcdefghijklmnopqrstuvwxyz", b, sizeof b) > 0);
    CHECK(kss_canon(r, "x", b, 10) == 0 && kss_canon(0, "x", b, sizeof b) == 0);
    /* review #1: INT_MIN / INT_MAX pic, bad items, worst case against an EXACT KSS_CANON_MAX buffer with guard bytes (no overflow, no negative snprintf size) */
    { char g[KSS_CANON_MAX + 16]; int len, j; unsigned h1;
      rows_clear(r); for (i = 0; i < KSS_ROWS; i++) put(r, i, 63, i & 1 ? INT_MIN : INT_MAX);
      memset(g, 0x5a, sizeof g);
      len = kss_canon(r, "abcdefghijklmnopqrstuvwxyz", g, KSS_CANON_MAX);
      CHECK(len > 0 && len < KSS_CANON_MAX);
      for (j = KSS_CANON_MAX; j < (int)sizeof g; j++) CHECK((unsigned char)g[j] == 0x5a);
      CHECK(strstr(g, "1|63|-99999\n") && strstr(g, "0|63|99999\n") && !strstr(g, "2147483"));
      rows_clear(r); put(r, 0, 62, INT_MIN); put(r, 10, 63, INT_MAX); h1 = kss_hash(r, "dm");
      rows_clear(r); put(r, 0, 62, -99999); put(r, 10, 63, 99999);
      CHECK(h1 && h1 == kss_hash(r, "dm") && h1 == 0x429ef2c5u);          /* the Python twin's value for the same clamp */
      rows_clear(r); for (i = 0; i < KSS_ROWS; i++) put(r, i, i & 1 ? 0 : 64 + i, INT_MIN);   /* every item out of range: skipped, canonical string is just the frame */
      CHECK(kss_canon(r, "", g, KSS_CANON_MAX) == (int)strlen("KLSET1\nS=pd2\n") && !strcmp(g, "KLSET1\nS=pd2\n"));
      rows_clear(r); put(r, 5, INT_MAX, 1); CHECK(kss_hash(r, "") == 0x9b4c41d5u);   /* item INT_MAX: skipped like an empty set */
      CHECK(kss_canon(r, "x", g, KSS_CANON_MAX - 1) == 0 && kss_canon(r, "x", g, INT_MIN) == 0 && kss_canon(r, "x", g, -1) == 0); }

    /* SHPH encode / parse */
    CHECK(kss_encode(pay, sizeof pay, 1, 0x1a2b3c4du, 13, 0) == 18 && !strcmp(pay, "v1s1h1a2b3c4dn13t0"));
    CHECK(kss_parse(pay, &m) && m.seat == 1 && m.hash == 0x1a2b3c4du && m.pairs == 13 && m.type == 0);
    CHECK(kss_encode(pay, sizeof pay, 15, 0xffffffffu, 36, 3) > 0 && kss_parse(pay, &m) && m.seat == 15 && m.hash == 0xffffffffu && m.pairs == 36 && m.type == 3);
    CHECK(kss_encode(pay, sizeof pay, 0, 0, 0, 0) > 0 && kss_parse(pay, &m) && m.seat == 0 && m.hash == 0 && m.pairs == 0);
    CHECK(!kss_encode(pay, sizeof pay, 16, 1, 1, 0) && !kss_encode(pay, sizeof pay, -1, 1, 1, 0) && !kss_encode(pay, sizeof pay, 1, 1, 37, 0) && !kss_encode(pay, sizeof pay, 1, 1, 1, 4) && !kss_encode(pay, 10, 1, 1, 1, 0));
    CHECK(kss_parse("v1s1H1A2B3C4Dn13t0", &m) == 0);                /* 'H' is not the field letter */
    CHECK(kss_parse("v1s1h1A2B3C4Dn13t0", &m) && m.hash == 0x1a2b3c4du);   /* upper-case hex is read */
    CHECK(!kss_parse("v2s1h1a2b3c4dn13t0", &m));                    /* bad version */
    CHECK(!kss_parse("v1s16h1a2b3c4dn13t0", &m));                   /* seat out of range */
    CHECK(!kss_parse("v1s1h1a2b3c4n13t0", &m));                     /* short hex */
    CHECK(!kss_parse("v1s1h1a2b3c4d5n13t0", &m));                   /* long hex */
    CHECK(!kss_parse("v1s1h1a2b3c4gn13t0", &m));                    /* bad hex digit */
    CHECK(!kss_parse("v1s1h1a2b3c4dn37t0", &m));                    /* pair count out of range */
    CHECK(!kss_parse("v1s1h1a2b3c4dn13t4", &m));                    /* set type out of range */
    CHECK(!kss_parse("v1s1h1a2b3c4dn13t0x", &m));                   /* trailing junk */
    CHECK(!kss_parse("v1s1h1a2b3c4dn13t", &m));                     /* truncated */
    CHECK(!kss_parse("v1s1h1a2b3c4dn13", &m));
    CHECK(!kss_parse("v1s1h1a2b3c4d", &m));
    CHECK(!kss_parse("", &m) && !kss_parse(0, &m) && !kss_parse(pay, 0));
    CHECK(!kss_parse("v1s-1h1a2b3c4dn13t0", &m));                   /* sign */
    CHECK(!kss_parse("v1s001h1a2b3c4dn13t0", &m));                  /* too many digits */
    { char big[200]; memset(big, '1', sizeof big); big[199] = 0; memcpy(big, "v1s1h1a2b3c4dn13t0", 18); CHECK(!kss_parse(big, &m));        /* oversized (no NUL within 40) */
      memset(big, 'v', 100); big[100] = 0; CHECK(!kss_parse(big, &m)); }
    /* fuzz: random bytes and random mutations of a valid payload never crash and never give out-of-range fields */
    srand(12345);
    for (k = 0; k < 20000; k++) {
        char f[48]; int len = rand() % 46;
        for (i = 0; i < len; i++) f[i] = (char)(rand() % 256);
        f[len] = 0;
        if (kss_parse(f, &m)) CHECK(m.seat >= 0 && m.seat < KSS_SEATS && m.pairs >= 0 && m.pairs <= KSS_ROWS && m.type >= 0 && m.type <= 3);
        strcpy(f, "v1s12h1a2b3c4dn13t0"); f[rand() % 19] = (char)(rand() % 256);
        if (kss_parse(f, &m)) CHECK(m.seat >= 0 && m.seat < KSS_SEATS && m.pairs >= 0 && m.pairs <= KSS_ROWS && m.type >= 0 && m.type <= 3);
    }

    /* decision table: check x strict x state */
    for (i = 0; i < 3; i++) {
        CHECK(kss_decide(0, 0, i) == KSS_ALLOW && kss_decide(0, 1, i) == KSS_ALLOW);        /* SetCheck 0 = today's behaviour exactly */
    }
    CHECK(kss_decide(1, 0, KSS_MATCH) == KSS_ALLOW && kss_decide(1, 1, KSS_MATCH) == KSS_ALLOW);
    CHECK(kss_decide(1, 0, KSS_MISMATCH) == KSS_ALLOW_WARN && kss_decide(1, 0, KSS_UNKNOWN) == KSS_ALLOW_WARN);
    CHECK(kss_decide(1, 1, KSS_MISMATCH) == KSS_REFUSE && kss_decide(1, 1, KSS_UNKNOWN) == KSS_REFUSE);

    /* state + sequence: unknown -> match -> mismatch -> match; the state follows the last message and does not stick */
    kss_reset(&pe);
    CHECK(kss_state_host(&pe, 1, 5) == KSS_UNKNOWN && kss_state_seat(&pe, 3, 1, 5) == KSS_UNKNOWN);
    m.seat = 3; m.hash = 5; m.pairs = 13; m.type = 0;
    CHECK(kss_note(&pe, 3, &m) == 1 && kss_state_seat(&pe, 3, 1, 5) == KSS_MATCH && kss_state_host(&pe, 1, 5) == KSS_UNKNOWN);
    CHECK(kss_note(&pe, 3, &m) == 0);                                   /* a repeat changes nothing */
    m.hash = 6; CHECK(kss_note(&pe, 3, &m) == 1 && kss_state_seat(&pe, 3, 1, 5) == KSS_MISMATCH);
    m.hash = 5; CHECK(kss_note(&pe, 3, &m) == 1 && kss_state_seat(&pe, 3, 1, 5) == KSS_MATCH);
    CHECK(kss_state_seat(&pe, 4, 1, 5) == KSS_UNKNOWN && kss_state_seat(&pe, -1, 1, 5) == KSS_UNKNOWN && kss_state_seat(&pe, 16, 1, 5) == KSS_UNKNOWN);
    m.hash = 9; CHECK(kss_note(&pe, 2, &m) == 1 && kss_state_host(&pe, 1, 5) == KSS_MISMATCH && kss_state_seat(&pe, 3, 1, 5) == KSS_MATCH);   /* host and seat 3 are separate */
    CHECK(kss_note(&pe, 0, &m) == 0 && kss_note(&pe, 9, &m) == 0);   /* a role that is neither host nor client is ignored */
    m.seat = 99; CHECK(kss_note(&pe, 3, &m) == 0);                    /* out-of-range seat is never indexed */
    CHECK(kss_state_host(&pe, 0, 5) == KSS_UNKNOWN);                  /* my own set unknown -> unknown, never a false mismatch */
    kss_reset(&pe); CHECK(kss_state_host(&pe, 1, 9) == KSS_UNKNOWN && kss_state_seat(&pe, 3, 1, 5) == KSS_UNKNOWN);

    /* review #3: a seat whose player changes is forgotten (an older build taking it is UNKNOWN); first sight of a seat keeps an entry heard before it */
    m.seat = 4; m.hash = 5; m.pairs = 13; m.type = 0;
    CHECK(kss_note(&pe, 3, &m) == 1 && kss_seat_ident(&pe, 4, 0x1000, 100) == 0 && kss_state_seat(&pe, 4, 1, 5) == KSS_MATCH);   /* first sight (ident 0 -> X): kept */
    CHECK(kss_seat_ident(&pe, 4, 0x1000, 100) == 0 && kss_state_seat(&pe, 4, 1, 5) == KSS_MATCH);                                  /* same occupant: kept */
    CHECK(kss_seat_ident(&pe, 4, 0x2000, 200) == 1 && kss_state_seat(&pe, 4, 1, 5) == KSS_UNKNOWN);                                /* new occupant: dropped */
    CHECK(kss_note(&pe, 3, &m) == 1 && kss_state_seat(&pe, 4, 1, 5) == KSS_MATCH);                                            /* ... until it announces */
    CHECK(kss_seat_ident(&pe, 4, 0, 300) == 1 && kss_state_seat(&pe, 4, 1, 5) == KSS_UNKNOWN);                                     /* seat emptied: dropped */
    CHECK(kss_seat_ident(&pe, 4, 0, 300) == 0 && kss_seat_ident(&pe, -1, 1, 0) == 0 && kss_seat_ident(&pe, 16, 1, 0) == 0 && kss_seat_ident(0, 1, 1, 0) == 0);

    /* review 1108 #2: a new occupant's announce that lands BEFORE the 0.5 s watch sees the seat change is kept (it is the new occupant's), not wiped */
    kss_reset(&pe); m.seat = 5; m.hash = 5;
    CHECK(kss_note_from(&pe, 3, &m, 0xA, 1000) == 1 && kss_seat_ident(&pe, 5, 0x1000, 1000) == 0);                       /* A announces, watch sees A */
    m.hash = 6; CHECK(kss_note_from(&pe, 3, &m, 0xB, 5000) == 1 && pe.fresh[5] == 1);                                       /* A left, B (other sid) announces first */
    CHECK(kss_seat_ident(&pe, 5, 0x2000, 5400) == 0 && kss_state_seat(&pe, 5, 1, 6) == KSS_MATCH && pe.fresh[5] == 0);      /* watch sees B: B's entry kept */
    CHECK(kss_seat_ident(&pe, 5, 0x3000, 9000) == 1 && kss_state_seat(&pe, 5, 1, 6) == KSS_UNKNOWN);                        /* C (old build, silent) takes it: dropped */
    m.hash = 5; CHECK(kss_note_from(&pe, 3, &m, 0xD, 10000) == 1 && pe.fresh[5] == 0);                                      /* sid bound was cleared: no false 'fresh' */
    CHECK(kss_note_from(&pe, 3, &m, 0xE, 20000) == 1 && pe.fresh[5] == 1);                                                  /* another sender, but the occupant never changes ... */
    CHECK(kss_seat_ident(&pe, 5, 0x3000, 20400) == 0 && pe.fresh[5] == 1);                                                  /* ... same ident: nothing dropped */
    CHECK(kss_seat_ident(&pe, 5, 0x4000, 30000) == 1 && kss_state_seat(&pe, 5, 1, 5) == KSS_UNKNOWN);                       /* a stale 'fresh' (> 3 s) does not save the next occupant */
    CHECK(kss_note_from(&pe, 3, &m, 0xF, 31000) == 1 && kss_seat_ident(&pe, 5, 0, 31200) == 1);                             /* seat emptied right after an announce: ident 0 never keeps */
    m.seat = 4;
    kss_reset(&pe); CHECK(pe.ident[4] == 0);

#ifdef _WIN32
    if (argc >= 3) {
        int n = 0; unsigned want = (unsigned)strtoul(argv[2], 0, 16), got = ini_hash(argv[1], &n);
        printf("ini %s: %d pairs, hash %08x (expected %08x)\n", argv[1], n, got, want);
        CHECK(got == want);
    }
#else
    (void)argc; (void)argv;
#endif
    printf("%s: %d checks, %d failed\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails ? 1 : 0;
}
