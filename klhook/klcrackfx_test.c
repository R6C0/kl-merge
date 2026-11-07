/* klcrackfx_test.c - OFF-GAME check of klcrackfx_logic.h (the cracked lens' heal fade and KL_CrackFX age).
 *   cl /nologo /W4 /D_CRT_SECURE_NO_WARNINGS klcrackfx_test.c     (run from the klhook folder) */
#include <stdio.h>
#include <math.h>
#include "klcrackfx_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
#define NEAR(a, b) (fabs((double)(a) - (double)(b)) < 1e-4)
int main(void)
{
    float nan = 0.0f; nan = nan / nan;
    /* fade off = the old crack, exactly */
    CHECK(klcf_heal(0.8f, 0.3f, 1.0f, 0.0f) == 0.8f);
    CHECK(klcf_heal(0.8f, 0.3f, 1.0f, -1.0f) == 0.8f);
    /* at birth: full */
    CHECK(NEAR(klcf_heal(0.8f, 0.3f, 0.3f, 0.5f), 0.8f));
    /* health fell further: still full */
    CHECK(NEAR(klcf_heal(0.8f, 0.3f, 0.1f, 0.5f), 0.8f));
    /* half way back: 1 - 0.5 * 0.5 */
    CHECK(NEAR(klcf_heal(0.8f, 0.4f, 0.7f, 0.5f), 0.8f * 0.75f));
    /* full health: half strength, never 0 at the recommended fade */
    CHECK(NEAR(klcf_heal(0.8f, 0.3f, 1.0f, 0.5f), 0.4f));
    CHECK(klcf_heal(0.8f, 0.3f, 1.0f, 0.5f) > 0.0f);
    /* fade clamped to 1; health over 1 clamped */
    CHECK(NEAR(klcf_heal(0.8f, 0.3f, 1.0f, 3.0f), 0.0f));
    CHECK(NEAR(klcf_heal(0.8f, 0.3f, 1.5f, 0.5f), 0.4f));
    /* made at 0 health: rec = health now; a negative birth health (should not happen) is still clamped to 0..1 */
    CHECK(NEAR(klcf_heal(0.8f, 0.0f, 0.5f, 0.5f), 0.8f * 0.75f));
    CHECK(NEAR(klcf_heal(0.8f, 0.0f, 1.0f, 0.5f), 0.4f));
    CHECK(NEAR(klcf_heal(0.8f, -0.5f, -0.5f, 0.5f), 0.8f));
    CHECK(NEAR(klcf_heal(0.8f, -0.5f, 1.0f, 0.5f), 0.4f));
    /* the dll passes h_now = h_birth when the health read failed: unchanged */
    CHECK(NEAR(klcf_heal(0.8f, 0.3f, 0.3f, 1.0f), 0.8f));
    /* made at full health: no fade; NaN in: unchanged */
    CHECK(klcf_heal(0.8f, 1.0f, 1.0f, 0.5f) == 0.8f);
    CHECK(klcf_heal(0.8f, nan, 1.0f, 0.5f) == 0.8f);
    CHECK(klcf_heal(0.8f, 0.3f, nan, 0.5f) == 0.8f);
    /* age: 0 = no crack; 1 + seconds; capped; GetTickCount wrap */
    CHECK(klcf_age(5000, 1000, 0) == 0.0f);
    CHECK(NEAR(klcf_age(1000, 1000, 1), 1.0f));
    CHECK(NEAR(klcf_age(1250, 1000, 2), 1.25f));
    CHECK(NEAR(klcf_age(999999, 1000, 1), 61.0f));
    CHECK(NEAR(klcf_age(100, 0xffffff00u, 1), 1.0f + 356.0f / 1000.0f));
    printf("klcrackfx_test: %d checks, %d failed\n", checks, fails);
    return fails != 0;
}
