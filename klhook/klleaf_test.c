/* klleaf_test.c - OFF-GAME check of klleaf_logic.h (leaf probe sampling schedule, door-aware CarStall gate).
 *   cl /nologo /W4 klleaf_test.c      or      tools/run_harness_linux.sh klleaf_test */
#include <windows.h>
#include <stdio.h>
#include "klleaf_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    int n, last = 0, taken = 0; unsigned long t, acc = 1000;
    CHECK(klleaf_due(5000, 0, 0) == 0);                       /* no accept */
    CHECK(klleaf_due(1000, 1000, 0) == 1);                    /* first sample at the accept */
    CHECK(klleaf_due(1100, 1000, 1) == 0);                    /* too early for #2 */
    CHECK(klleaf_due(1250, 1000, 1) == 2);
    CHECK(klleaf_due(1200, 1000, 0) == 1);                    /* late first sample still number 1 */
    for (t = acc; t < acc + 9000; t += 10) { n = klleaf_due(t, acc, last); if (n) { last = n; taken++; } }
    CHECK(taken == 25); CHECK(last == 25);                    /* 0, 250 ... 6000 ms */
    CHECK(klleaf_due(acc + 6000, acc, 25) == 0);              /* cap */
    CHECK(klleaf_due(acc + 7000, acc, 3) == 0);               /* a long stall: series simply over */
    CHECK(klleaf_due(5, 0xfffffff0ul, 0) == 1);               /* tick wrap: 21 ms after the accept */
    CHECK(klleaf_due(0x10, 0xfffffff0ul, 1) == 0);
    /* stall gate */
    CHECK(!klleaf_stall_gated(2000, 0, 5000));                /* no accept seen (SHIP / probe off): never gated, CarStall as before */
    CHECK(!klleaf_stall_gated(4000, 3000, 0));                /* AfterDoorMs 0 = old behaviour */
    CHECK(klleaf_stall_gated(6000, 3000, 5000));              /* proxy accepted at 3000: gated until 8000 */
    CHECK(!klleaf_stall_gated(8000, 3000, 5000));
    CHECK(!klleaf_stall_gated(70000, 3000, 5000));            /* a stale accept (an earlier fire) does not gate */
    CHECK(klleaf_stall_gated(5, 0xfffffff0ul, 5000));         /* wrap */
    printf("klleaf_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
