/* klassoft_test.c - off-game checks of klassoft_logic.h. Build: cl /nologo /W3 klassoft_test.c */
#include <stdio.h>
#include "klassoft_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    unsigned long l[KAS_MAX]; int n, bad;
    n = kas_parse("0x6567e8,0x845a8b,51d049,0X555900, 4ede1b", l, KAS_MAX, &bad);
    CHECK(n == 5 && bad == 0); CHECK(l[0] == 0x6567e8 && l[1] == 0x845a8b && l[2] == 0x51d049 && l[3] == 0x555900 && l[4] == 0x4ede1b);
    CHECK(kas_find(l, n, 0x555900) == 3); CHECK(kas_find(l, n, 0x555901) == -1); CHECK(kas_find(l, 0, 0x6567e8) == -1);
    n = kas_parse("", l, KAS_MAX, &bad); CHECK(n == 0 && bad == 0);
    n = kas_parse(0, l, KAS_MAX, &bad); CHECK(n == 0);
    n = kas_parse(" ,; ", l, KAS_MAX, &bad); CHECK(n == 0 && bad == 0);
    n = kas_parse("zz,0x,6567e8,12345678901,0x6567e8", l, KAS_MAX, &bad); CHECK(n == 1 && l[0] == 0x6567e8 && bad == 3);
    n = kas_parse("0x4000000", l, KAS_MAX, &bad); CHECK(n == 0 && bad == 1);
    n = kas_parse("400001,400002,400003,400004", l, 2, &bad); CHECK(n == 2 && bad == 2);
    n = kas_parse("2567e8,0x445a8b,0x6567e8", l, KAS_MAX, &bad); CHECK(n == 2 && bad == 1 && l[0] == 0x445a8b && l[1] == 0x6567e8);      /* AS1: an offset under 0x400000 is refused; 0x445a8b is a valid VA */
    n = kas_parse("0x3fffff,0x400000", l, KAS_MAX, &bad); CHECK(n == 1 && bad == 1 && l[0] == 0x400000);
    /* AssertSoftGuard table + pool test */
    CHECK(KAS_NSITES == 5);
    CHECK(kas_site_where(0x6567e8) == KAS_REC_EDI && kas_site_where(0x845a8b) == KAS_REC_ESI && kas_site_where(0x51d049) == KAS_IDX_ESI4);
    CHECK(kas_site_where(0x555900) == KAS_REC_EDI && kas_site_where(0x4ede1b) == KAS_REC_ESI && kas_site_where(0x123456) == KAS_REC_NONE);
    CHECK(kas_guard_ok(KAS_REC_NONE, 0, 0, 0) == 1);
    CHECK(kas_guard_ok(KAS_REC_EDI, 0, 0x1000, 0) == 0);                                   /* pool unreadable */
    CHECK(kas_guard_ok(KAS_REC_EDI, 0x2000000, 0x2000000, 0) == 1);                        /* first record */
    CHECK(kas_guard_ok(KAS_REC_ESI, 0x2000000, 0x2000000 + 347 * 0x7c, 0) == 1);          /* DM01 ram truck point 347 */
    CHECK(kas_guard_ok(KAS_REC_ESI, 0x2000000, 0x2000000 + 0x1787 * 0x7c, 0) == 1);       /* last record */
    CHECK(kas_guard_ok(KAS_REC_ESI, 0x2000000, 0x2000000 + 0x1788 * 0x7c, 0) == 0);       /* one past the end */
    CHECK(kas_guard_ok(KAS_REC_EDI, 0x2000000, 0x1fffffc, 0) == 0);                       /* before the pool */
    CHECK(kas_guard_ok(KAS_REC_EDI, 0x2000000, 0x2000000 + 0x7d, 0) == 0);                /* not on a record boundary */
    CHECK(kas_guard_ok(KAS_IDX_ESI4, 0x2000000, 0, 0x1787) == 1 && kas_guard_ok(KAS_IDX_ESI4, 0x2000000, 0, 0x1788) == 0);
    CHECK(kas_guard_ok(KAS_IDX_ESI4, 0x2000000, 0, 0xfffffffful) == 0);                   /* a negative index (the game tests only jl in places) */
    printf("klassoft_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
