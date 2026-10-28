/* klbalonline_test.c - off-game checks of klbalonline.h. Build: cl /nologo /W3 klbalonline_test.c */
#include <stdio.h>
#include <math.h>
#include "klbalonline.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
#define NEAR(a, b) (fabs((double)(a) - (double)(b)) < 1e-4)

int main(void)
{
    float d;
    /* factor matrix */
    CHECK(kbo_factor(KBO_A_NPC, KBO_V_BOT, 1) == KBO_F_COP2CREW);
    CHECK(kbo_factor(KBO_A_HUMAN, KBO_V_BOT, 1) == KBO_F_YOU2CREW);
    CHECK(kbo_factor(KBO_A_HUMANCOP, KBO_V_BOT, 1) == KBO_F_FED2CREW);
    CHECK(kbo_factor(KBO_A_HUMANCOP, KBO_V_BOT, 0) == KBO_F_YOU2COP);
    CHECK(kbo_factor(KBO_A_BOT, KBO_V_BOT, 1) == KBO_F_NONE);
    CHECK(kbo_factor(KBO_A_NONE, KBO_V_BOT, 1) == KBO_F_NONE);
    CHECK(kbo_factor(KBO_A_BOT, KBO_V_NPC, 1) == KBO_F_CREW2COP);
    CHECK(kbo_factor(KBO_A_HUMAN, KBO_V_NPC, 1) == KBO_F_NONE);
    CHECK(kbo_factor(KBO_A_NPC, KBO_V_NPC, 1) == KBO_F_NONE);
    CHECK(kbo_factor(KBO_A_BOT, KBO_V_NONE, 1) == KBO_F_NONE);
    /* kinds */
    CHECK(kbo_kind(0) == 1 && kbo_kind(1) == -1 && kbo_kind(3) == -1 && kbo_kind(5) == 0 && kbo_kind(6) == 0);
    /* want + Ramp */
    CHECK(kbo_want(0, -1.0f, 1, 0.5f) < 0);                         /* not set */
    CHECK(NEAR(kbo_want(0, 0.05f, 1, 0.5f), 0.5f));                 /* kind 1: stock above dial held */
    CHECK(NEAR(kbo_want(0, 2.0f, 1, 0.5f), 2.0f));                  /* dial above stock kept */
    CHECK(NEAR(kbo_want(0, 0.05f, 0, 0.5f), 0.05f));                /* Ramp off: as given */
    CHECK(NEAR(kbo_want(1, 2.0f, 1, 0.5f), 0.5f));                  /* kind -1: stock below dial held */
    CHECK(NEAR(kbo_want(1, 0.2f, 1, 0.5f), 0.2f));
    CHECK(NEAR(kbo_want(3, 3.0f, 1, 1.0f), 1.0f));
    CHECK(NEAR(kbo_want(5, 0.5f, 1, 2.0f), 0.5f));                  /* kind 0: never held */
    CHECK(NEAR(kbo_want(5, 5.0f, 1, 0.1f), 5.0f));
    /* range */
    CHECK(NEAR(kbo_range(100, 0.5f, 800, 3500), 1.0f));
    CHECK(NEAR(kbo_range(800, 0.5f, 800, 3500), 1.0f));
    CHECK(NEAR(kbo_range(3500, 0.5f, 800, 3500), 0.5f));
    CHECK(NEAR(kbo_range(99999, 0.5f, 800, 3500), 0.5f));
    d = kbo_range(1475, 0.5f, 800, 3500); CHECK(NEAR(d, 0.88f));   /* 0.875 rounds to the 0.02 step 0.88 */
    d = kbo_range(2150, 0.5f, 800, 3500); CHECK(NEAR(d, 0.74f) || NEAR(d, 0.76f));   /* 0.75 sits between two steps */
    CHECK(NEAR(kbo_range(1000, 0.0f, 800, 3500), 1.0f));            /* off */
    CHECK(NEAR(kbo_range(1000, 0.5f, 3500, 800), 1.0f));            /* bad window */
    { float z = 0.0f, nan_ = z / z; CHECK(NEAR(kbo_range(nan_, 0.5f, 800, 3500), 1.0f)); }
    d = kbo_range(1234, 0.37f, 800, 3500); CHECK(NEAR(d * 50.0f, floor(d * 50.0f + 0.5f)));   /* 0.02 steps */
    /* tough + scale */
    CHECK(NEAR(kbo_tough(KBO_V_BOT, 2.0f), 2.0f));
    CHECK(NEAR(kbo_tough(KBO_V_NPC, 2.0f), 1.0f));
    CHECK(NEAR(kbo_tough(KBO_V_BOT, 0.0f), 1.0f));
    CHECK(NEAR(kbo_scale(0.5f, 0.5f, 2.0f), 0.125f));
    CHECK(NEAR(kbo_scale(-1.0f, 1.0f, 1.0f), 1.0f));                /* unset = 1 */
    CHECK(NEAR(kbo_scale(0.0f, 1.0f, 1.0f), KBO_TOKEN));            /* 0 = token */
    CHECK(NEAR(kbo_scale(2.0f, 0.0f, 0.0f), 2.0f));                 /* bad range / tough ignored */
    /* cop k */
    CHECK(NEAR(kbo_cop_k(0.05f, 0.0f, 0.0f), 0.05f));
    CHECK(NEAR(kbo_cop_k(0.0f, 0.05f, 0.0f), KBO_TOKEN));
    CHECK(NEAR(kbo_cop_k(-1.0f, 0.05f, 0.0f), 0.05f));
    CHECK(NEAR(kbo_cop_k(-1.0f, 0.05f, 2.0f), 0.025f));
    CHECK(NEAR(kbo_cop_k(-1.0f, 0.0f, 2.0f), 0.5f));                /* only Tough: k 1 / tough */
    CHECK(NEAR(kbo_cop_k(-1.0f, 0.0f, 0.0f), 0.0f));                /* nothing: path off */
    CHECK(NEAR(kbo_cop_k(-1.0f, 0.0f, 1.0f), 0.0f));
    printf("klbalonline_test: %d checks, %d fails\n", checks, fails);
    return fails ? 1 : 0;
}
