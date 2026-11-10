/* kldifficulty_test.c - off-game checks of kldifficulty_logic.h. Build: cl /nologo /W3 kldifficulty_test.c   (or gcc -m32) */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "kldifficulty_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    float f[KDF_NF] = { -1, -1, -1, 2.0f, -1, 1.0f }; int i; char t[96];
    /* steps: at least 4 each, a stock step, strictly ordered */
    CHECK(KDF_AI_N >= 4 && KDF_YOU_N >= 4);
    CHECK(!strcmp(kdf_ai[0].name, "STOCK") && !strcmp(kdf_you[0].name, "STOCK"));
    CHECK(kdf_ai[0].taken == 0.01f && kdf_ai[0].dealt == 3.0f);                  /* = klbalance.c klr_code level 1 */
    CHECK(kdf_you[0].cop == 0.10f && kdf_you[0].crew == 0.10f);
    for (i = 1; i < KDF_AI_N; i++) CHECK(kdf_ai[i].taken > kdf_ai[i - 1].taken && kdf_ai[i].dealt <= kdf_ai[i - 1].dealt);
    for (i = 1; i < KDF_YOU_N; i++) CHECK(kdf_you[i].cop > kdf_you[i - 1].cop && kdf_you[i].crew > kdf_you[i - 1].crew);
    /* the recommended default: a police bullet on an AI heister = on you (the owner's complaint: 1 percent bullet sponge) */
    CHECK(kdf_ai[KDF_AI_DEF].taken == kdf_you[KDF_YOU_DEF].cop);
    CHECK(kdf_ai[KDF_AI_DEF].taken >= 0.5f);
    CHECK(kdf_you[KDF_YOU_DEF].cop == 0.70f && kdf_you[KDF_YOU_DEF].crew == 0.60f);   /* the live ini: the player's side does not change */
    /* apply: only the four owned floats */
    kdf_apply(f, KDF_AI_DEF, KDF_YOU_DEF);
    CHECK(f[0] == 0.70f && f[1] == 1.0f && f[2] == 0.70f && f[4] == 0.60f && f[3] == 2.0f && f[5] == 1.0f);
    kdf_apply(f, 0, -1);
    CHECK(f[0] == 0.01f && f[1] == 3.0f && f[2] == 0.70f);
    kdf_apply(f, -1, 0);
    CHECK(f[2] == 0.10f && f[4] == 0.10f && f[0] == 0.01f);
    kdf_apply(f, 99, -5);                                                         /* clamped, negative = leave */
    CHECK(f[0] == kdf_ai[KDF_AI_N - 1].taken && f[2] == 0.10f);
    /* recognise */
    for (i = 0; i < KDF_AI_N; i++) CHECK(kdf_ai_of(kdf_ai[i].taken, kdf_ai[i].dealt) == i);
    for (i = 0; i < KDF_YOU_N; i++) CHECK(kdf_you_of(kdf_you[i].cop, kdf_you[i].crew) == i);
    CHECK(kdf_ai_of(0.05f, 1.0f) == -1 && kdf_you_of(0.7f, 1.0f) == -1);
    CHECK(kdf_ai_of(0.7001f, 1.0f) == 2);                                         /* a %.2f round trip */
    { char n[16]; float v; kdf_num(n, sizeof n, 0.70f); CHECK(!strcmp(n, "0.70")); v = (float)atof(n); CHECK(kdf_close(v, 0.70f)); }
    /* cycling wraps both ways; custom enters at the ends */
    CHECK(kdf_next(0, KDF_AI_N, 1) == 1 && kdf_next(KDF_AI_N - 1, KDF_AI_N, 1) == 0);
    CHECK(kdf_next(0, KDF_AI_N, -1) == KDF_AI_N - 1 && kdf_next(2, KDF_YOU_N, -1) == 1);
    CHECK(kdf_next(-1, KDF_YOU_N, 1) == 0 && kdf_next(-1, KDF_YOU_N, -1) == KDF_YOU_N - 1);
    { int s = 0, n = 0; do { s = kdf_next(s, KDF_YOU_N, 1); n++; } while (s != 0 && n < 20); CHECK(n == KDF_YOU_N); }
    /* text */
    kdf_say_ai(2, t, sizeof t); CHECK(!strcmp(t, "AI HEISTERS FAIR: hit x0.70, deal x1.0") && strlen(t) < 48);
    kdf_say_you(4, t, sizeof t); CHECK(!strcmp(t, "YOUR DAMAGE BRUTAL: police x1.40, crew x1.20") && strlen(t) < 48);
    kdf_say_ai(-3, t, sizeof t); CHECK(!strncmp(t, "AI HEISTERS STOCK", 17));
    /* ini read */
    CHECK(kdf_read_step(-1, 4) == -1 && kdf_read_step(0, 4) == 0 && kdf_read_step(3, 4) == 3 && kdf_read_step(4, 4) == -2 && kdf_read_step(-7, 4) == -2);
    printf("kldifficulty_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
