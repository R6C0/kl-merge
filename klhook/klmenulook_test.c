/* klmenulook_test.c - OFF-GAME checks of klmenulook_logic.h ([MenuLook] DeadMen: which menu files get their _deadmen sibling, and when not).
 *   cl /nologo /W3 klmenulook_test.c      or      gcc -m32 -I klhook/test_shim klmenulook_test.c   (tools/kl_tests.py, kind 'logic')
 * Written in the cloud 2026-11-09; run there with gcc -m32 (gcc-multilib) + AddressSanitizer on 2026-11-09 (scheduled check-in): 109 checks, 0 fails, no ASan report.
 * The first cut crashed 0xC0000409 under cl: the test's own out[260] was handed to klml_variant with cap 300 (section 9), fixed with a separate buffer. */
#include <stdio.h>
#include <string.h>
#include "klmenulook_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

/* the fake disk: the paths that "exist" (case-insensitive, as NTFS), and a count of probes so the no-probe rows can be checked */
static const char *disk[8]; static int ndisk, probes;
static int ieq(const char *a, const char *b)
{
    for (; *a && *b; a++, b++) if (klml_lc((unsigned char)*a) != klml_lc((unsigned char)*b)) return 0;
    return !*a && !*b;
}
static int fake_exists(const char *p)
{
    int i; probes++;
    for (i = 0; i < ndisk; i++) if (ieq(disk[i], p)) return 1;
    return 0;
}
static void have(const char *a, const char *b, const char *c, const char *d, const char *e)
{
    const char *all[5]; int i;
    all[0] = a; all[1] = b; all[2] = c; all[3] = d; all[4] = e;
    ndisk = 0; probes = 0;
    for (i = 0; i < 5; i++) if (all[i]) disk[ndisk++] = all[i];
}

#define OV  "C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Overlay\\"
#define GM  "C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\"

int main(void)
{
    char out[260]; int why, i;
    const char *menu[5]     = { OV "Patch01.zip", OV "Patch01_rows12.zip", OV "Scenes\\kaneandlynch.zip", OV "Scenes\\kaneandlynch.WHD", OV "Scenes\\kaneandlynch.WAV" };
    const char *themed[5]   = { OV "Patch01_deadmen.zip", OV "Patch01_rows12_deadmen.zip", OV "Scenes\\kaneandlynch_deadmen.zip", OV "Scenes\\kaneandlynch_deadmen.WHD", OV "Scenes\\kaneandlynch_deadmen.WAV" };
    const char *other[8]    = { GM "Scenes\\Locations\\F01\\F01_Main.zip", GM "Scenes\\kaneandlynch.SND", GM "Patch02.zip", GM "kl2.exe", GM "Scenes\\kaneandlynch", GM "Scenes\\.zip",
                                GM "Scenes\\xkaneandlynch.zip", GM "Scenes\\kaneandlynch.zip.bak" };

    /* 1. ON, every themed copy there: each of the five menu files -> its sibling, case of dir/stem kept, extension as given */
    have(themed[0], themed[1], themed[2], themed[3], themed[4]);
    for (i = 0; i < 5; i++) {
        out[0] = 0; why = -1;
        CHECK(klml_variant(menu[i], 1, fake_exists, out, sizeof out, &why) == 1);
        CHECK(why == KLML_USED);
        CHECK(!strcmp(out, themed[i]));
    }
    CHECK(probes == 5);                                                                     /* exactly one probe per menu file */

    /* 2. OFF: nothing swapped, nothing probed, whatever is on disk */
    have(themed[0], themed[1], themed[2], themed[3], themed[4]);
    for (i = 0; i < 5; i++) { why = -1; CHECK(klml_variant(menu[i], 0, fake_exists, out, sizeof out, &why) == 0); CHECK(why == KLML_OFF); }
    CHECK(probes == 0);

    /* 3. ON, no themed copy: stock look, why = MISSING, out names the sibling that was looked for (the log line) */
    have(0, 0, 0, 0, 0);
    for (i = 0; i < 5; i++) {
        out[0] = 0; why = -1;
        CHECK(klml_variant(menu[i], 1, fake_exists, out, sizeof out, &why) == 0);
        CHECK(why == KLML_MISSING);
        CHECK(!strcmp(out, themed[i]));
    }
    CHECK(probes == 5);

    /* 4. the .WHD / .WAV pair: only one of the two themed = only that one swaps (the stage tool writes both; the decision is per file) */
    have(themed[3], 0, 0, 0, 0);
    CHECK(klml_variant(menu[3], 1, fake_exists, out, sizeof out, &why) == 1 && why == KLML_USED);
    CHECK(klml_variant(menu[4], 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_MISSING);

    /* 5. rows12 variant: Patch01_rows12.zip -> Patch01_rows12_deadmen.zip (not Patch01_deadmen.zip) */
    have(themed[0], 0, 0, 0, 0);                                                            /* only the plain themed patch exists */
    CHECK(klml_variant(menu[1], 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_MISSING && !strcmp(out, themed[1]));
    have(themed[1], 0, 0, 0, 0);
    CHECK(klml_variant(menu[1], 1, fake_exists, out, sizeof out, &why) == 1 && !strcmp(out, themed[1]));
    CHECK(klml_variant(menu[0], 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_MISSING);
    /* a MountFirst alias with another Patch01_<x>.zip name is a menu file too */
    have("D:\\x\\Patch01_test_deadmen.zip", 0, 0, 0, 0);
    CHECK(klml_variant("D:\\x\\Patch01_test.zip", 1, fake_exists, out, sizeof out, &why) == 1 && !strcmp(out, "D:\\x\\Patch01_test_deadmen.zip"));

    /* 6. non-menu files: never a probe, why = NOT_MENU (level archive, .SND, Patch02, the exe, no extension, empty stem, prefix / suffix noise) */
    have(themed[0], themed[1], themed[2], themed[3], themed[4]);
    for (i = 0; i < 8; i++) { why = -1; CHECK(klml_variant(other[i], 1, fake_exists, out, sizeof out, &why) == 0); CHECK(why == KLML_NOT_MENU); }
    CHECK(probes == 0);
    /* a FindFirstFile pattern, an empty path, a NULL path, a bare directory */
    CHECK(klml_variant(GM "Scenes\\*.zip", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_NOT_MENU);
    CHECK(klml_variant(GM "Patch01?.zip", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_NOT_MENU);
    CHECK(klml_variant("", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_NOT_MENU);
    CHECK(klml_variant(0, 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_NOT_MENU);
    CHECK(klml_variant(GM "Scenes\\", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_NOT_MENU);
    CHECK(probes == 0);

    /* 7. mixed case: the NAME test ignores case; dir and stem keep their case in out, the suffix is lower case, the extension as given */
    have("c:\\dd\\overlay\\PATCH01_ROWS12_deadmen.ZIP", "c:\\dd\\overlay\\scenes\\KaneAndLynch_deadmen.Whd", 0, 0, 0);
    CHECK(klml_variant("c:\\dd\\overlay\\PATCH01_ROWS12.ZIP", 1, fake_exists, out, sizeof out, &why) == 1 && !strcmp(out, "c:\\dd\\overlay\\PATCH01_ROWS12_deadmen.ZIP"));
    CHECK(klml_variant("c:\\dd\\overlay\\scenes\\KaneAndLynch.Whd", 1, fake_exists, out, sizeof out, &why) == 1 && !strcmp(out, "c:\\dd\\overlay\\scenes\\KaneAndLynch_deadmen.Whd"));
    /* forward slashes end the directory too; a bare file name (no directory) works */
    have("x/y/patch01_deadmen.zip", "kaneandlynch_deadmen.wav", 0, 0, 0);
    CHECK(klml_variant("x/y/patch01.zip", 1, fake_exists, out, sizeof out, &why) == 1 && !strcmp(out, "x/y/patch01_deadmen.zip"));
    CHECK(klml_variant("kaneandlynch.wav", 1, fake_exists, out, sizeof out, &why) == 1 && !strcmp(out, "kaneandlynch_deadmen.wav"));

    /* 8. already the themed copy: no double suffix, no probe */
    have(themed[0], themed[1], themed[2], themed[3], themed[4]);
    for (i = 0; i < 5; i++) { why = -1; CHECK(klml_variant(themed[i], 1, fake_exists, out, sizeof out, &why) == 0); CHECK(why == KLML_ALREADY); }
    CHECK(klml_variant(OV "PATCH01_DEADMEN.ZIP", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLML_ALREADY);
    CHECK(probes == 0);

    /* 9. overlong: the sibling must fit cap (with its NUL); the row is refused BEFORE any write into out, nothing probed.
       The cap-300 / cap-268 checks below write a 267-char sibling: they get their own 320-byte buffer. (2026-11-09 scheduled
       check-in: they used out[260] with cap 300 -> stack overrun = the 0xC0000409 under cl and 3 fails under gcc -m32; the
       logic header itself was right, it refused cap 260 before any write.) */
    {
        char longp[300], big[320]; size_t n;
        memset(longp, 'a', sizeof longp); memcpy(longp, "C:\\", 3);
        n = 247;
        memcpy(longp + n, "\\Patch01.zip", 13);                /* 247 'a's of directory, then "\Patch01.zip": 259 chars, fits MAX_PATH itself */
        /* its sibling would be 259 + 8 = 267 chars: too long for cap 260 */
        have(0, 0, 0, 0, 0);
        memset(out, 'Z', sizeof out); why = -1;
        CHECK(klml_variant(longp, 1, fake_exists, out, 260, &why) == 0);
        CHECK(why == KLML_TOO_LONG);
        CHECK(out[0] == 'Z');                                  /* untouched */
        CHECK(probes == 0);
        /* the same path with a big enough cap works and is exactly strlen + 8 */
        memset(big, 0, sizeof big);
        CHECK(klml_variant(longp, 1, fake_exists, big, 300, &why) == 0 && why == KLML_MISSING && strlen(big) == strlen(longp) + 8);
        CHECK(!strcmp(big + strlen(big) - 20, "\\Patch01_deadmen.zip"));
        CHECK(probes == 1);                                    /* the sibling was looked for exactly once */
        /* the boundary: cap = strlen + 8 + 1 fits, cap = strlen + 8 does not (and writes nothing) */
        CHECK(klml_variant(longp, 1, fake_exists, big, strlen(longp) + 9, &why) == 0 && why == KLML_MISSING);
        memset(big, 'Z', sizeof big);
        CHECK(klml_variant(longp, 1, fake_exists, big, strlen(longp) + 8, &why) == 0 && why == KLML_TOO_LONG);
        CHECK(big[0] == 'Z' && big[sizeof big - 1] == 'Z');
        CHECK(klml_variant("Patch01.zip", 1, fake_exists, out, 1, &why) == 0 && why == KLML_NOT_MENU);        /* cap < 2: refused at once */
    }

    /* 10. no exists callback = treated as missing (never swapped); why texts exist for every row */
    CHECK(klml_variant(menu[0], 1, 0, out, sizeof out, &why) == 0 && why == KLML_MISSING);
    for (i = KLML_OFF; i <= KLML_USED; i++) CHECK(strcmp(klml_why_text(i), "?") != 0);
    CHECK(!strcmp(klml_why_text(99), "?"));
    /* why may be NULL */
    have(themed[0], 0, 0, 0, 0);
    CHECK(klml_variant(menu[0], 1, fake_exists, out, sizeof out, 0) == 1 && !strcmp(out, themed[0]));
    CHECK(klml_variant(menu[0], 0, fake_exists, out, sizeof out, 0) == 0);

    printf("klmenulook_test: %d checks, %d fails\n", checks, fails);
    return fails ? 1 : 0;
}
