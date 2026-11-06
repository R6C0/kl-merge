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
    CHECK(klperf_osd_slice_ms(0) == 0u); CHECK(klperf_osd_slice_ms(1) == 24u);
    CHECK(!klperf_slice_over(0, 0xffffffffu)); CHECK(!klperf_slice_over(8u, 7u)); CHECK(klperf_slice_over(8u, 8u)); CHECK(klperf_slice_over(8u, 84719u));
    CHECK(!klperf_cache_ok(0, 1, 1, 0));
    CHECK(klperf_cache_ok(1, 1, 1, 100000u)); CHECK(!klperf_cache_ok(1, 1, 0, 0));
    CHECK(klperf_cache_ok(1, 0, 0, 49u)); CHECK(!klperf_cache_ok(1, 0, 1, 50u));
    CHECK(klperf_in_range(0x400000, 4, 0x400000, 0x1734000)); CHECK(!klperf_in_range(0x3ffffc, 4, 0x400000, 0x1734000));
    CHECK(klperf_in_range(0x1733ffc, 4, 0x400000, 0x1734000)); CHECK(!klperf_in_range(0x1733ffd, 4, 0x400000, 0x1734000));
    CHECK(!klperf_in_range(0x500000, 0, 0x400000, 0x1734000)); CHECK(!klperf_in_range(0x500000, 0xffffffffUL, 0x400000, 0x1734000));
    CHECK(klperf_probe_default(1, 0) == 1); CHECK(klperf_probe_default(1, 1) == 0);
    CHECK(klperf_probe_default(0, 0) == 0); CHECK(klperf_probe_default(0, 1) == 0);
    {   double v[6] = { 0.5, 3.0, 0.0, 3.0, 9.0, -1.0 }; int o[8], n;
        n = klperf_pick_top(v, 6, o, 3); CHECK(n == 3 && o[0] == 4 && o[1] == 1 && o[2] == 3);
        n = klperf_pick_top(v, 6, o, 8); CHECK(n == 4 && o[0] == 4 && o[1] == 1 && o[2] == 3 && o[3] == 0);
        n = klperf_pick_top(v, 6, o, 1); CHECK(n == 1 && o[0] == 4);
        n = klperf_pick_top(v, 0, o, 3); CHECK(n == 0);
        { double z[3] = { 0.0, 0.0, 0.0 }; n = klperf_pick_top(z, 3, o, 3); CHECK(n == 0); }
        { double a[5] = { 1, 2, 3, 4, 5 }; n = klperf_pick_top(a, 5, o, 2); CHECK(n == 2 && o[0] == 4 && o[1] == 3); }
    }
    printf("%s: %d checks, %d fails\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
