/* klcampui_test.c - OFF-GAME checks of klcampui_logic.h ([CampaignUI] Menu: which archives get their _campui sibling, and when not).
 *   cl /nologo /W3 klcampui_test.c      or      gcc -m32 -I klhook/test_shim klcampui_test.c   (tools/kl_tests.py, kind 'logic') */
#include <stdio.h>
#include <string.h>
#include "klcampui_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static const char *disk[8]; static int ndisk, probes;
static int fake_exists(const char *p)
{
    int i; probes++;
    for (i = 0; i < ndisk; i++) if (strlen(disk[i]) == strlen(p) && klcu_ieq(disk[i], p, strlen(p))) return 1;
    return 0;
}
static void have(const char *a, const char *b, const char *c, const char *d)
{
    ndisk = 0; probes = 0;
    if (a) disk[ndisk++] = a;
    if (b) disk[ndisk++] = b;
    if (c) disk[ndisk++] = c;
    if (d) disk[ndisk++] = d;
}

#define OV "C:\\Steam\\Dog Days\\KLExpansion\\Overlay\\"

int main(void)
{
    char out[320]; char small[20]; int why, i;
    const char *base[4] = { OV "Patch01.zip", OV "Patch01_deadmen.zip", OV "Patch01_rows12.zip", OV "Patch01_rows12_deadmen.zip" };
    const char *camp[4] = { OV "Patch01_campui.zip", OV "Patch01_deadmen_campui.zip", OV "Patch01_rows12_campui.zip", OV "Patch01_rows12_deadmen_campui.zip" };
    const char *other[9] = { OV "Scenes\\kaneandlynch.zip", OV "Scenes\\kaneandlynch.WHD", "C:\\g\\Scenes\\Locations\\M01\\M01_Main.zip", "C:\\g\\Patch02.zip",
                             "C:\\g\\xPatch01.zip", "C:\\g\\Patch01.zip.bak", "C:\\g\\Patch0.zip", "C:\\g\\Patch01", "C:\\g\\Patch01.*" };

    /* 1. gate */
    CHECK(klcu_gate(1, 1) == 1); CHECK(klcu_gate(1, 0) == 0); CHECK(klcu_gate(0, 1) == 0); CHECK(klcu_gate(0, 0) == 0);

    /* 2. on, every sibling there: each patch archive -> its _campui copy */
    have(camp[0], camp[1], camp[2], camp[3]);
    for (i = 0; i < 4; i++) {
        out[0] = 0; why = -1;
        CHECK(klcu_variant(base[i], 1, fake_exists, out, sizeof out, &why) == 1);
        CHECK(why == KLCU_USED); CHECK(!strcmp(out, camp[i]));
    }
    /* case of dir/stem kept, extension as given */
    CHECK(klcu_variant("c:\\x\\PATCH01.ZIP", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_MISSING && !strcmp(out, "c:\\x\\PATCH01_campui.ZIP"));
    /* forward slashes */
    have("C:/g/Patch01_campui.zip", 0, 0, 0);
    CHECK(klcu_variant("C:/g/Patch01.zip", 1, fake_exists, out, sizeof out, &why) == 1 && why == KLCU_USED && !strcmp(out, "C:/g/Patch01_campui.zip"));

    /* 3. off: nothing probed, out untouched */
    have(camp[0], 0, 0, 0); strcpy(out, "keep");
    for (i = 0; i < 4; i++) { CHECK(klcu_variant(base[i], 0, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_OFF); }
    CHECK(probes == 0 && !strcmp(out, "keep"));

    /* 4. not patch archives: no probe */
    have(camp[0], camp[1], 0, 0);
    for (i = 0; i < 9; i++) { CHECK(klcu_variant(other[i], 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_NOT_MENU); }
    CHECK(klcu_variant("", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_NOT_MENU);
    CHECK(klcu_variant(0, 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_NOT_MENU);
    CHECK(klcu_variant("C:\\g\\", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_NOT_MENU);
    CHECK(klcu_variant("C:\\g\\.zip", 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_NOT_MENU);
    CHECK(klcu_variant(OV "Patch01.zip", 1, fake_exists, 0, sizeof out, &why) == 0);
    CHECK(klcu_variant(OV "Patch01.zip", 1, fake_exists, out, 1, &why) == 0);
    CHECK(probes == 0);

    /* 5. already a campaign copy: never a double suffix, no probe */
    CHECK(klcu_variant(camp[1], 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_ALREADY && probes == 0);

    /* 6. missing sibling: stock menu */
    have(0, 0, 0, 0);
    CHECK(klcu_variant(base[0], 1, fake_exists, out, sizeof out, &why) == 0 && why == KLCU_MISSING && probes == 1);

    /* 7. bounded: too small a buffer is refused, out untouched; exact fit works */
    strcpy(small, "xx");
    CHECK(klcu_variant("C:\\a\\Patch01.zip", 1, fake_exists, small, sizeof small, &why) == 0 && why == KLCU_TOO_LONG && !strcmp(small, "xx"));
    have("Patch01_campui.zip", 0, 0, 0);
    CHECK(klcu_variant("Patch01.zip", 1, fake_exists, small, 19, &why) == 1 && !strcmp(small, "Patch01_campui.zip"));
    CHECK(klcu_variant("Patch01.zip", 1, fake_exists, small, 18, &why) == 0 && why == KLCU_TOO_LONG);

    /* 8. chain with the MenuLook name: Patch01_deadmen.zip is a patch archive too */
    have(camp[1], 0, 0, 0);
    CHECK(klcu_variant(base[1], 1, fake_exists, out, sizeof out, &why) == 1 && !strcmp(out, camp[1]));
    CHECK(klcu_why_text(KLCU_USED)[0] && klcu_why_text(99)[0] == '?');

    printf("klcampui_test: %d checks, %d fails\n", checks, fails);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails ? 1 : 0;
}
