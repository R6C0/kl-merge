/* klcensus_test.c - off-game harness for klcensus_logic.h (OnlineTriggersCensus new-cop set; klbotfill.c includes the same header). No windows.h.
   Build: cl /nologo /W3 klcensus_test.c /Fe:klcensus_test.exe     Run: klcensus_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "klcensus_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    static struct kcs_set b; struct kcs_tally t; unsigned long i;
    kcs_clear(&b);
    CHECK(b.n == 0 && !b.over, "clear");
    CHECK(kcs_add(&b, 0x1000) == 1 && kcs_add(&b, 0x1000) == 0 && b.n == 1, "dedupe");
    CHECK(kcs_add(&b, 0) == 0 && b.n == 1, "null ignored");
    kcs_add(&b, 0x2000); kcs_add(&b, 0x3000);
    /* +10 s: 0x1000 died, 0x2000 and 0x3000 alive, 0x4000 and 0x5000 arrived */
    kcs_tally_clear(&t);
    kcs_tally_cop(&t, &b, 0x2000); kcs_tally_cop(&t, &b, 0x3000); kcs_tally_cop(&t, &b, 0x4000); kcs_tally_cop(&t, &b, 0x5000);
    CHECK(t.live == 4 && t.fresh == 2 && t.kept == 2, "tally %d %d %d", t.live, t.fresh, t.kept);
    CHECK(kcs_gone(&b, &t) == 1, "gone 1");
    /* only kills, no wave: new 0 though the count fell */
    kcs_tally_clear(&t); kcs_tally_cop(&t, &b, 0x3000);
    CHECK(t.fresh == 0 && kcs_gone(&b, &t) == 2, "kills only");
    /* empty scan */
    kcs_tally_clear(&t);
    CHECK(kcs_gone(&b, &t) == 3 && t.live == 0, "all gone");
    /* empty base: every live cop is new */
    kcs_clear(&b); kcs_tally_clear(&t); kcs_tally_cop(&t, &b, 0x10);
    CHECK(t.fresh == 1 && kcs_gone(&b, &t) == 0, "empty base");
    /* bounded */
    kcs_clear(&b);
    for (i = 1; i <= KCS_MAX + 10; i++) kcs_add(&b, i * 16);
    CHECK(b.n == KCS_MAX && b.over, "capped n=%d over=%d", b.n, b.over);
    CHECK(kcs_add(&b, 16) == 0, "member re-add at cap");
    kcs_clear(&b);
    CHECK(b.n == 0 && !b.over, "reset clears over");
    printf("klcensus_test: %d checks, %d fails\n", checks, fails);
    return fails ? 1 : 0;
}
