/* klshot_test.c - OFF-GAME check of klshot_logic.h (back-buffer shot timing, cap, format, file name).
 *   cl /nologo /W4 klshot_test.c      or      tools/run_harness_linux.sh klshot_test */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "klshot_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    char p[128];
    CHECK(klshot_max(0) == 40); CHECK(klshot_max(-3) == 40); CHECK(klshot_max(15) == 15); CHECK(klshot_max(9999) == 400);
    CHECK(klshot_fmt(0) == 0); CHECK(klshot_fmt(1) == 1); CHECK(klshot_fmt(2) == 2); CHECK(klshot_fmt(7) == 0);
    CHECK(klshot_d3dx_fmt(0) == 1); CHECK(klshot_d3dx_fmt(1) == 3); CHECK(klshot_d3dx_fmt(2) == 0);
    CHECK(!strcmp(klshot_ext(0), "jpg")); CHECK(!strcmp(klshot_ext(1), "png")); CHECK(!strcmp(klshot_ext(2), "bmp"));
    /* timing: From 10 s, every 5 s */
    CHECK(klshot_due(5000, 0, 0, 10, 5, 0, 40) == 0);          /* before From */
    CHECK(klshot_due(10000, 0, 0, 10, 5, 0, 40) == 1);         /* arms */
    CHECK(klshot_due(12000, 10000, 0, 10, 5, 0, 40) == 0);
    CHECK(klshot_due(15000, 10000, 0, 10, 5, 0, 40) == 2);
    CHECK(klshot_due(15000, 10000, 0, 10, 5, 40, 40) == 0);    /* cap */
    CHECK(klshot_due(15000, 10000, 0, 10, 0, 0, 40) == 0);     /* off */
    CHECK(klshot_due(100, 0, 0, 0, 5, 0, 40) == 1);            /* From 0: arms at once */
    CHECK(klshot_due(0x10, 0xfffffff0ul, 0, 0, 5, 0, 40) == 0);/* tick wrap does not fire early: now-last is 0x20 ms */
    klshot_path(p, sizeof p, "C:\\a b", "inst1", 3, 1); CHECK(!strcmp(p, "C:\\a b\\KLShot_inst1_03.png"));
    klshot_path(p, sizeof p, "", "run", 0, 0); CHECK(!strcmp(p, "KLShot_run_00.jpg"));
    klshot_path(p, 12, "", "run", 0, 0); CHECK(strlen(p) == 11);   /* truncates, still terminated */
    printf("klshot_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
