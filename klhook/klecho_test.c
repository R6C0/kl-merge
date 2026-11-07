/* klecho_test.c - off-game checks of klecho_logic.h. Build: cl /nologo /W3 klecho_test.c */
#include <stdio.h>
#include <math.h>
#include "klecho_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
#define NEAR(a, b) (fabs((double)(a) - (double)(b)) < 1e-4)

/* run the 12 calls of one SetReverb the way the engine makes them; out[0..11] = the values our wrapper hands to the real alEffectf */
static void run(const struct klecho_cfg *c, const float *in, float *out)
{
    struct klecho_st st = { 0, 0, 0 }; int p;
    for (p = 1; p <= 12; p++) out[p - 1] = klecho_value(c, &st, p, in[p - 1]);
}
/* stock F02 effects as the engine converts them: density 1.0, diffusion 1.0, gain, gainhf, decay, hfratio, refl, refl delay, late, late delay, air, rolloff */
static const float OPEN[12]    = { 0.86f, 0.43f, 0.316f, 0.0224f, 1.49f, 0.54f, 0.052f, 0.162f, 0.794f, 0.1f, 0.994f, 0.0f };
static const float COVERED[12] = { 1.0f, 1.0f, 0.316f, 0.5f, 2.0f, 0.7f, 0.1f, 0.03f, 0.46f, 0.06f, 0.994f, 0.0f };
static const float TRAIN[12]   = { 0.56f, 0.56f, 0.0005f, 0.0001f, 0.1f, 0.5f, 0.00001f, 0.005f, 1.0f, 0.01f, 0.994f, 0.0f };

int main(void)
{
    struct klecho_cfg c = { 100, { 100, 100, 100, 100, 100 } }, off = { 0, { 100, 100, 100, 100, 100 } }, k0 = { 100, { 100, 0, 0, 0, 0 } };
    float o[12]; int p; struct klecho_st st;

    CHECK(klecho_kind(0.1f, 0, 0) == KLE_INDOOR); CHECK(klecho_kind(0.59f, 0, 0) == KLE_INDOOR); CHECK(klecho_kind(0.6f, 0.5f, 1) == KLE_STREET);
    CHECK(klecho_kind(1.49f, 0.052f, 1) == KLE_ROOF); CHECK(klecho_kind(2.0f, 0.1f, 1) == KLE_STREET); CHECK(klecho_kind(2.49f, 0.07f, 1) == KLE_ROOF);
    CHECK(klecho_kind(2.5f, 0.0f, 1) == KLE_HALL); CHECK(klecho_kind(8.0f, 0.5f, 1) == KLE_HALL);

    /* strength 0 = the engine's own values, every parameter, every stock effect */
    run(&off, OPEN, o); for (p = 0; p < 12; p++) CHECK(NEAR(o[p], OPEN[p]));
    run(&off, COVERED, o); for (p = 0; p < 12; p++) CHECK(NEAR(o[p], COVERED[p]));
    run(&off, TRAIN, o); for (p = 0; p < 12; p++) CHECK(NEAR(o[p], TRAIN[p]));
    /* a kind at 0 percent is the engine's value too */
    run(&k0, OPEN, o); for (p = 0; p < 12; p++) CHECK(NEAR(o[p], OPEN[p]));

    /* the three kinds differ: roof = long decay + one far slap + late tail started late; street = nearer slaps; indoor = tight but not dry */
    run(&c, OPEN, o);
    CHECK(o[4] > OPEN[4] * 1.5f && o[4] < 20.0f);               /* decay longer */
    CHECK(NEAR(o[7], 0.20f));                                   /* roof: one far slap */
    CHECK(o[6] >= 0.10f && o[6] > OPEN[6]);                     /* reflections lifted from near nothing */
    CHECK(o[8] > OPEN[8] && o[8] <= 10.0f);                     /* late tail up */
    CHECK(NEAR(o[9], 0.10f));                                   /* late delay at the AL maximum */
    CHECK(NEAR(o[0], OPEN[0]) && NEAR(o[1], OPEN[1]) && NEAR(o[2], OPEN[2]) && NEAR(o[3], OPEN[3]) && NEAR(o[5], OPEN[5]) && NEAR(o[10], OPEN[10]) && NEAR(o[11], OPEN[11]));
    run(&c, COVERED, o);
    CHECK(NEAR(o[4], 3.2f));                                    /* street: 2.0 x 1.6 */
    CHECK(NEAR(o[6], 0.30f));                                   /* 0.1 x 3 */
    CHECK(NEAR(o[7], 0.054f));                                  /* 0.03 x 1.8, under the 0.12 cap */
    CHECK(o[9] >= 0.06f && o[9] <= 0.1f);
    run(&c, TRAIN, o);
    CHECK(NEAR(o[4], 0.15f));                                   /* indoor: 0.1 x 1.5, still tight */
    CHECK(NEAR(o[6], 0.12f));                                   /* dry effect gets the floor, not 0 */
    CHECK(NEAR(o[7], TRAIN[7]));                                /* small room: delay untouched */
    CHECK(o[8] >= 1.0f);
    {   float a[12], b[12], d[12]; run(&c, OPEN, a); run(&c, COVERED, b); run(&c, TRAIN, d);
        CHECK(!NEAR(a[7], b[7]) && !NEAR(b[7], d[7]) && !NEAR(a[4], b[4]));   /* indoor, street, roof are three different answers */
    }
    /* clamps: a huge strength never leaves the AL ranges */
    { struct klecho_cfg h = { 300, { 100, 300, 300, 300, 300 } }; float in[12], r[12]; int i, k;
      static const float *src[3] = { OPEN, COVERED, TRAIN };
      for (k = 0; k < 3; k++) { for (i = 0; i < 12; i++) in[i] = src[k][i]; run(&h, in, r);
        CHECK(r[4] >= 0.1f && r[4] <= 20.0f); CHECK(r[6] >= 0 && r[6] <= 3.16f); CHECK(r[7] >= 0 && r[7] <= 0.3f); CHECK(r[8] >= 0 && r[8] <= 10.0f); CHECK(r[9] >= 0 && r[9] <= 0.1f); }
      in[4] = 19.0f; run(&h, in, r); CHECK(r[4] <= 20.0f); in[4] = 0.01f; run(&h, in, r); CHECK(r[4] >= 0.1f); }
    /* order: parameters before the decay are never touched; param 1 resets the state of the previous call */
    st.decay = 0; st.refl = 0; st.kind = KLE_NONE;
    CHECK(NEAR(klecho_value(&c, &st, 3, 0.7f), 0.7f)); CHECK(NEAR(klecho_value(&c, &st, 4, 0.7f), 0.7f)); CHECK(st.kind == KLE_NONE);
    klecho_value(&c, &st, 5, 2.0f); CHECK(st.kind == KLE_STREET);
    klecho_value(&c, &st, 1, 1.0f); CHECK(st.kind == KLE_NONE);
    CHECK(NEAR(klecho_value(&c, &st, 9, 0.5f), 0.5f));          /* a stray late gain without a decay: untouched */
    /* unknown parameter numbers pass through */
    CHECK(NEAR(klecho_value(&c, &st, 99, 0.25f), 0.25f)); CHECK(NEAR(klecho_value(&c, &st, 0, 0.25f), 0.25f));
    printf("%s: %d checks, %d fails\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
