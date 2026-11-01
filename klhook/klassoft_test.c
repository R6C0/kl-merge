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
    n = kas_parse("1,2,3,4", l, 2, &bad); CHECK(n == 2 && bad == 2);
    printf("klassoft_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
