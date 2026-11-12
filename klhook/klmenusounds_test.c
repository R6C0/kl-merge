/* klmenusounds_test.c - OFF-GAME checks of klmenusounds_logic.h ([MenuSounds]: sidecar parse, pick resolution, in-memory .WHD patch).
 *   cl /nologo /W3 klmenusounds_test.c      or      gcc -m32 -I klhook/test_shim klmenusounds_test.c   (tools/kl_tests.py, kind 'logic') */
#include <stdio.h>
#include <string.h>
#include "klmenusounds_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

#define WHDLEN 512
static unsigned char whd[WHDLEN], keep[WHDLEN];
static char side[2048];

static unsigned long rd(const unsigned char *b, unsigned o) { return b[o] | ((unsigned long)b[o + 1] << 8) | ((unsigned long)b[o + 2] << 16) | ((unsigned long)b[o + 3] << 24); }

static void mkside(int wavlen, unsigned long hash)
{
    sprintf(side,
        "# test table\n KLMS 1\nWHD %d %lx\nWAV %d\n"
        "F pcm 16 size 20 samples 36 off 28 offhi 32\n"
        "E Navigate 40 Up_Down SFX/OSD/Up_Down.wav\n"
        "C Navigate Up_Down 6976 2048 3488 4096 0\n"
        "C Navigate off 1000 512 500 8192 0   # silent\n"
        "E Confirm 100 Select\n"
        "C Confirm Select 9000 3072 4500 12288 0\n"
        "C Confirm Menu 7000 2048 3500 16384 0\n"
        "E Back 200 dd\n",
        WHDLEN, hash, wavlen);
}

#define PARSE() klms_parse(side, strlen(side), &t, err, sizeof err)

int main(void)
{
    klms_tab t; char err[200]; int i, ch[KLMS_MAXEV], why, n; unsigned long h;
    const char *p[KLMS_MAXEV];
    for (i = 0; i < WHDLEN; i++) whd[i] = (unsigned char)(i * 7 + 3);
    memcpy(keep, whd, WHDLEN);
    h = klms_fnv(whd, WHDLEN, KLMS_FNV0);
    CHECK(klms_fnv((const unsigned char *)"a", 1, KLMS_FNV0) == 0xe40c292cUL);       /* FNV-1a 32 of "a" */

    /* parse */
    mkside(20000, h);
    CHECK(PARSE());
    if (fails) printf("parse error: %s\n", err);
    CHECK(t.nev == 3 && t.nch == 4 && t.fo[0] == 16 && t.fo[3] == 28 && t.fo[4] == 32 && t.whdlen == WHDLEN && t.wavlen == 20000 && t.whdhash == h);
    CHECK(t.e[0].rec == 0x40 && !strcmp(t.e[0].dflt, "Up_Down") && !strcmp(t.e[0].recname, "SFX/OSD/Up_Down.wav") && t.e[1].rec == 0x100);
    CHECK(klms_find_ev(&t, "confirm") == 1 && klms_find_ev(&t, "nope") == -1 && klms_find_ch(&t, 1, "MENU") == 3);

    /* resolve */
    CHECK(klms_resolve(&t, 0, "dd", &why) == -1 && why == KLMS_STOCK);
    CHECK(klms_resolve(&t, 0, "", &why) == -1 && why == KLMS_STOCK);
    CHECK(klms_resolve(&t, 0, 0, &why) == -1 && why == KLMS_STOCK);
    CHECK(klms_resolve(&t, 0, " DM", &why) == 0 && why == KLMS_CHOICE);
    CHECK(klms_resolve(&t, 0, "off", &why) == 1 && why == KLMS_CHOICE);
    CHECK(klms_resolve(&t, 1, "off", &why) == -1 && why == KLMS_UNKNOWN);
    CHECK(klms_resolve(&t, 1, "menu", &why) == 3 && why == KLMS_CHOICE);
    CHECK(klms_resolve(&t, 1, "Bogus", &why) == -1 && why == KLMS_UNKNOWN);
    CHECK(klms_resolve(&t, 2, "dm", &why) == -1 && why == KLMS_STOCK);               /* default dd = nothing to apply */
    CHECK(klms_resolve(&t, 9, "dm", &why) == -1 && why == KLMS_STOCK);

    /* apply: all dd = nothing changes */
    for (i = 0; i < KLMS_MAXEV; i++) p[i] = "dd";
    n = klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err);
    CHECK(n == 0 && !memcmp(whd, keep, WHDLEN));
    /* Navigate=dm, Confirm=Menu: exactly the five dwords of two records change */
    p[0] = "dm"; p[1] = "Menu"; p[2] = "dm";
    n = klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err);
    CHECK(n == 2 && ch[0] == 0 && ch[1] == 3 && ch[2] == -1);
    CHECK(rd(whd, 0x40 + 16) == 6976 && rd(whd, 0x40 + 20) == 2048 && rd(whd, 0x40 + 36) == 3488 && rd(whd, 0x40 + 28) == 4096 && rd(whd, 0x40 + 32) == 0);
    CHECK(rd(whd, 0x100 + 16) == 7000 && rd(whd, 0x100 + 28) == 16384);
    {
        int bad = 0;
        for (i = 0; i < WHDLEN; i++) {
            int in = 0, r, f; unsigned fo[5]; fo[0] = 16; fo[1] = 20; fo[2] = 36; fo[3] = 28; fo[4] = 32;
            for (r = 0; r < 2; r++) for (f = 0; f < 5; f++) { unsigned base = r ? 0x100 : 0x40; if ((unsigned)i >= base + fo[f] && (unsigned)i < base + fo[f] + 4) in = 1; }
            if (!in && whd[i] != keep[i]) bad++;
        }
        CHECK(bad == 0);
    }
    /* the choice hash: same choices -> same, other choices -> other */
    {
        unsigned long a = klms_choice_hash(&t, ch); int ch2[KLMS_MAXEV];
        for (i = 0; i < KLMS_MAXEV; i++) ch2[i] = ch[i];
        CHECK(klms_choice_hash(&t, ch2) == a);
        ch2[0] = 1; CHECK(klms_choice_hash(&t, ch2) != a);
        ch2[0] = ch[0]; ch2[1] = -1; CHECK(klms_choice_hash(&t, ch2) != a);
    }
    /* an unknown pick stays stock and is not an error */
    memcpy(whd, keep, WHDLEN); p[0] = "Bogus"; p[1] = "dd"; p[2] = "dd";
    CHECK(klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err) == 0 && !memcmp(whd, keep, WHDLEN) && ch[0] == -1);

    /* refusals leave everything untouched */
    p[0] = "dm"; p[1] = "dm"; p[2] = "dd";
    CHECK(klms_apply(whd, WHDLEN - 4, &t, p, ch, err, sizeof err) == -1 && strstr(err, "bytes"));
    whd[5] ^= 1; CHECK(klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err) == -1 && strstr(err, "hash")); whd[5] ^= 1;
    CHECK(!memcmp(whd, keep, WHDLEN));
    mkside(5000, h); PARSE();                                                              /* Select data 12288+3072 leaves a 5000-byte .WAV */
    CHECK(klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err) == -1 && strstr(err, "leaves the .WAV") && !memcmp(whd, keep, WHDLEN));
    p[1] = "dd"; p[0] = "off"; mkside(20000, h); PARSE();
    CHECK(klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err) == 1);                       /* 'off' is a real, non-empty clip */
    memcpy(whd, keep, WHDLEN);
    t.e[0].rec = WHDLEN - 8;                                                               /* record outside the .WHD */
    p[0] = "dm"; CHECK(klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err) == -1 && strstr(err, "outside") && !memcmp(whd, keep, WHDLEN));
    mkside(20000, h); PARSE();
    t.c[0].v[1] = 0; CHECK(klms_apply(whd, WHDLEN, &t, p, ch, err, sizeof err) == -1 && strstr(err, "0") && !memcmp(whd, keep, WHDLEN));   /* a zero size is never written */

    /* parse refusals */
    CHECK(!PARSE() || 1);
    CHECK(!klms_parse("", 0, &t, err, sizeof err));
    CHECK(!klms_parse("WHD 1 1\n", 8, &t, err, sizeof err) && strstr(err, "header"));
    mkside(20000, h); strcat(side, "C Back dm 1 2 3 4 0\n"); CHECK(!PARSE() && strstr(err, "reserved"));
    mkside(20000, h); strcat(side, "C Nope x 1 2 3 4 0\n"); CHECK(!PARSE() && strstr(err, "unknown event"));
    mkside(20000, h); strcat(side, "C Back x 1 2 3 4 0\nC back X 1 2 3 4 0\n"); CHECK(!PARSE() && strstr(err, "twice"));
    mkside(20000, h); strcat(side, "Z what\n"); CHECK(!PARSE() && strstr(err, "unknown line"));
    mkside(20000, h); strcat(side, "E Back 300 dd\n"); CHECK(!PARSE() && strstr(err, "twice"));
    mkside(20000, h); strcat(side, "C Back x 1 2 zz 4 0\n"); CHECK(!PARSE() && strstr(err, "number"));
    sprintf(side, "KLMS 1\nWHD 1 1\nWAV 1\nF pcm 16 size 20 samples 36 off 28 offhi 33\nE A 1 dd\n");
    CHECK(!PARSE() && strstr(err, "F field"));                                             /* offset not a multiple of 4 */
    sprintf(side, "KLMS 1\nWHD 1 1\nWAV 1\nF pcm 16 size 20 samples 36 off 28 offhi 32\nE A 1 Missing\n");
    CHECK(!PARSE() && strstr(err, "default choice"));
    sprintf(side, "KLMS 1\nWHD 1 1\nWAV 1\nE A 1 dd\n"); CHECK(!PARSE() && strstr(err, "missing"));
    {
        char big[700]; memset(big, 'a', sizeof big - 1); big[sizeof big - 1] = 0; mkside(20000, h);
        strcat(side, big); strcat(side, "\n"); CHECK(!PARSE());
    }
    /* CRLF lines, no trailing newline */
    sprintf(side, "KLMS 1\r\nWHD 512 %lx\r\nWAV 100\r\nF pcm 16 size 20 samples 36 off 28 offhi 32\r\nE A 40 dd", h);
    CHECK(PARSE() && t.nev == 1);

    printf("%s: %d checks, %d failed\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails ? 1 : 0;
}
