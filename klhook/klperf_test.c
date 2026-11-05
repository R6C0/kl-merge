/* klperf_test.c - off-game checks of klperf_logic.h. Build: cl /nologo /W3 klperf_test.c */
#include <stdio.h>
#include "klperf_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    CHECK(klperf_osd_interval(0, 1) == 2000u); CHECK(klperf_osd_interval(2, 1) == 2000u);
    CHECK(klperf_osd_interval(3, 1) == 15000u); CHECK(klperf_osd_interval(5, 1) == 15000u);
    CHECK(klperf_osd_interval(6, 1) == 60000u); CHECK(klperf_osd_interval(99, 1) == 60000u);
    CHECK(klperf_osd_interval(5, 0) == 15000u); CHECK(klperf_osd_interval(99, 0) == 15000u); CHECK(klperf_osd_interval(1, 0) == 2000u);
    CHECK(!klperf_cache_ok(0, 1, 1, 0));
    CHECK(klperf_cache_ok(1, 1, 1, 100000u)); CHECK(!klperf_cache_ok(1, 1, 0, 0));
    CHECK(klperf_cache_ok(1, 0, 0, 49u)); CHECK(!klperf_cache_ok(1, 0, 1, 50u));
    CHECK(klperf_in_range(0x400000, 4, 0x400000, 0x1734000)); CHECK(!klperf_in_range(0x3ffffc, 4, 0x400000, 0x1734000));
    CHECK(klperf_in_range(0x1733ffc, 4, 0x400000, 0x1734000)); CHECK(!klperf_in_range(0x1733ffd, 4, 0x400000, 0x1734000));
    CHECK(!klperf_in_range(0x500000, 0, 0x400000, 0x1734000)); CHECK(!klperf_in_range(0x500000, 0xffffffffUL, 0x400000, 0x1734000));
    printf("%s: %d checks, %d fails\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
