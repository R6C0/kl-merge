/* klbottrait_test.c - off-game checks of klbottrait.h. Build: cl /nologo /W3 klbottrait_test.c */
#include <stdio.h>
#include <math.h>
#include "klbottrait.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
#define NEAR(a, b) (fabs((double)(a) - (double)(b)) < 1e-4)

int main(void)
{
    float nan = 0.0f; nan = nan / nan;
    /* clamp */
    CHECK(NEAR(kbt_clamp(1.0f, 0.25f), 1.0f));
    CHECK(NEAR(kbt_clamp(2.0f, 0.25f), 1.25f));
    CHECK(NEAR(kbt_clamp(0.1f, 0.25f), 0.75f));
    CHECK(NEAR(kbt_clamp(0.0f, 0.25f), 1.0f));
    CHECK(NEAR(kbt_clamp(-3.0f, 0.25f), 1.0f));
    CHECK(NEAR(kbt_clamp(nan, 0.25f), 1.0f));
    CHECK(NEAR(kbt_clamp(1.4f, 0.5f), 1.4f));
    CHECK(NEAR(kbt_clamp(1.4f, 0.0f), 1.0f));
    /* index */
    CHECK(kbt_index(0, 16) == -1);
    CHECK(kbt_index(1, 16) == 0);
    CHECK(kbt_index(16, 16) == 15);
    CHECK(kbt_index(17, 16) == -1);
    CHECK(kbt_index(3, 0) == -1);
    CHECK(kbt_index(-1, 16) == -1);
    /* hit multiplier: DamageIn / Health */
    CHECK(NEAR(kbt_hit_mult(1.0f, 1.0f), 1.0f));
    CHECK(NEAR(kbt_hit_mult(1.25f, 1.0f), 0.8f));               /* tougher: takes 0.8 of a hit */
    CHECK(NEAR(kbt_hit_mult(0.75f, 1.0f), 1.0f / 0.75f));       /* thin: takes more */
    CHECK(NEAR(kbt_hit_mult(1.0f, 1.25f), 1.25f));
    CHECK(NEAR(kbt_hit_mult(1.08f, 0.95f), 0.95f / 1.08f));
    CHECK(NEAR(kbt_hit_mult(0.0f, 1.0f), 1.0f));                /* nonsense = nothing */
    CHECK(NEAR(kbt_hit_mult(1.0f, 0.0f), 1.0f));
    /* the same as kltrait.c's effective health Health / DamageIn: hits to kill scale by 1 / mult */
    CHECK(NEAR(1.0f / kbt_hit_mult(1.15f, 0.95f), 1.15f / 0.95f));
    /* with Tough */
    CHECK(NEAR(kbt_total(1.5f, 1.0f, 1.0f), 1.0f / 1.5f));
    CHECK(NEAR(kbt_total(1.5f, 1.25f, 1.0f), 0.8f / 1.5f));
    CHECK(NEAR(kbt_total(0.0f, 1.25f, 1.0f), 0.8f));
    CHECK(NEAR(kbt_total(-1.0f, 1.0f, 1.0f), 1.0f));
    CHECK(NEAR(kbt_total(2.0f, 0.75f, 1.25f), 1.25f / 0.75f / 2.0f));
    /* lie seconds */
    CHECK(NEAR(kbt_lie(10.0f, 1.15f), 11.5f));
    CHECK(NEAR(kbt_lie(10.0f, 0.85f), 8.5f));
    CHECK(NEAR(kbt_lie(10.0f, 1.0f), 10.0f));
    CHECK(NEAR(kbt_lie(0.0f, 1.15f), 0.0f));                    /* LieSeconds 0 = path off, stays off */
    CHECK(NEAR(kbt_lie(10.0f, 0.0f), 10.0f));
    /* skipped hits */
    CHECK(kbt_skip_hit(0.0f, 100.0f) == 1);
    CHECK(kbt_skip_hit(-1.0f, 100.0f) == 1);
    CHECK(kbt_skip_hit(nan, 100.0f) == 1);
    CHECK(kbt_skip_hit(1.0f, 100.0f) == 0);
    CHECK(kbt_skip_hit(1.0001f, 100.0f) == 0);
    CHECK(kbt_skip_hit(5.0f, 100.0f) == 1);                     /* a point-blank step */
    CHECK(kbt_skip_hit(100.0f, 100.0f) == 1);
    CHECK(kbt_skip_hit(100.5f, 100.0f) == 0);                   /* above it: an ordinary scaled hit (as klr_cb_hit) */
    CHECK(kbt_skip_hit(5.0f, 0.0f) == 0);                       /* no point-blank configured */
    CHECK(kbt_skip_hit(0.3f, 100.0f) == 0);
    printf("klbottrait_test: %d checks, %d failures\n%s\n", checks, fails, fails ? "FAIL" : "ALL PASS");
    return fails ? 1 : 0;
}
