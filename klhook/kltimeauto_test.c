/* kltimeauto_test.c - off-game harness for kltimeauto_logic.h ([Lobby] TimeAuto clamp / when to apply). No windows.h.
   Build: cl /nologo /W3 kltimeauto_test.c /Fe:kltimeauto_test.exe     Run: kltimeauto_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "kltimeauto_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    CHECK(kta_target(0, 0, 10, 4) == 0, "off");
    CHECK(kta_target(-3, 0, 10, 4) == 0 && kta_target(21, 0, 30, 4) == 0, "out of 1..20 is ignored");
    CHECK(kta_target(6, 10, 10, 4) == 6 && kta_target(6, 0, 10, 4) == 6, "6 with TimeMax 10");
    CHECK(kta_target(6, 0, 0, 4) == 5, "6 without TimeMax clamps to stock 5");
    CHECK(kta_target(10, 0, 8, 4) == 8, "clamped to TimeMax");
    CHECK(kta_target(1, 0, 10, 4) == 3, "1 without TimeMin clamps to 3");
    CHECK(kta_target(1, 2, 10, 4) == 2 && kta_target(2, 2, 0, 4) == 2, "TimeMin 2 lets 2 through, 1 clamps to 2");
    CHECK(kta_target(4, 0, 0, 4) == 0, "already at the value: nothing to do");
    CHECK(kta_target(6, 0, 10, 6) == 0, "already 6");
    CHECK(kta_target(5, 0, 0, 4) == 5 && kta_target(3, 0, 0, 4) == 3, "stock range");
    CHECK(kta_target(20, 0, 20, 5) == 20, "20");
    CHECK(kta_target(9, 0, 5, 4) == 5 && kta_target(9, 0, 3, 4) == 5, "TimeMax below 6 is stock 5");
    printf("kltimeauto_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
