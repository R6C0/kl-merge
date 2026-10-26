/* klsabot_test.c - OFF-GAME check of klsabotage_logic.h: the UCC host gate, who may press, the van hold arithmetic, the per-visit reset
 * and the key edge of [Sabotage] VanHold. Pure numbers; the game reads and the write are klsabotage.c's (NOT run here).
 *   cl /nologo /W4 klsabot_test.c      or      tools/run_harness_linux.sh klsabot_test */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "klsabotage_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
#define NEAR(a, b) ((a) - (b) < 0.001f && (b) - (a) < 0.001f)

int main(void)
{
    struct klsab_key k; float z = 0.0f;
    /* gate: host, game type 4, UCC sub-mode, in a round */
    CHECK(klsab_gate(2, 4, 0x19, 1, 0));
    CHECK(klsab_gate(2, 4, 0x13, 1, 0)); CHECK(klsab_gate(2, 4, 0x1f, 1, 0));
    CHECK(!klsab_gate(3, 4, 0x19, 1, 0));                 /* a client never writes */
    CHECK(!klsab_gate(0, 4, 0x19, 1, 0)); CHECK(!klsab_gate(1, 4, 0x19, 1, 0));
    CHECK(!klsab_gate(2, 3, 0x19, 1, 0));                 /* not game type 4 */
    CHECK(!klsab_gate(2, 4, 0x19, 0, 0));                 /* plain FA: off unless AnyMode */
    CHECK(!klsab_gate(2, 4, 0x19, 2, 0));                 /* C&R: off unless AnyMode */
    CHECK(klsab_gate(2, 4, 0x19, 0, 1)); CHECK(klsab_gate(2, 4, 0x19, 2, 1));
    CHECK(!klsab_gate(2, 4, 0x19, 3, 1));                 /* an unknown sub-mode never */
    CHECK(!klsab_gate(2, 4, 0x12, 1, 0)); CHECK(!klsab_gate(2, 4, 0x20, 1, 0));
    CHECK(!klsab_gate(3, 4, 0x19, 1, 1));                 /* AnyMode does not open the client */
    /* who may press */
    CHECK(klsab_may_press(1, 0, 0));
    CHECK(!klsab_may_press(0, 0, 0));                     /* a heister */
    CHECK(!klsab_may_press(1, 1, 0));                     /* a UCC who is police now */
    CHECK(!klsab_may_press(0, 1, 0));
    CHECK(klsab_may_press(0, 0, 1));                      /* AnyPlayer test key */
    /* hold: states 1..4 only */
    CHECK(NEAR(klsab_hold(3, 6.0f, 0, 8), 14.0f));
    CHECK(NEAR(klsab_hold(1, 5.0f, 0, 8), 13.0f));
    CHECK(NEAR(klsab_hold(2, 0.5f, 0, 8), 8.5f));
    CHECK(NEAR(klsab_hold(4, 0.0f, 0, 8), 8.0f));
    CHECK(klsab_hold(0, 6.0f, 0, 8) < 0); CHECK(klsab_hold(5, 6.0f, 0, 8) < 0);
    CHECK(klsab_hold(6, 6.0f, 0, 8) < 0); CHECK(klsab_hold(7, 6.0f, 0, 8) < 0);
    CHECK(klsab_hold(-1, 6.0f, 0, 8) < 0);
    CHECK(klsab_hold(3, 6.0f, 1, 8) < 0);                 /* once a visit */
    /* hold: clamps */
    CHECK(NEAR(klsab_hold(3, 6.0f, 0, 0), 7.0f));         /* 0 s -> 1 s minimum */
    CHECK(NEAR(klsab_hold(3, 6.0f, 0, 99), 26.0f));       /* 99 s -> 20 s maximum */
    CHECK(NEAR(klsab_hold(3, 30.0f, 0, 20), KLSAB_TIMER_CAP));
    CHECK(klsab_hold(3, KLSAB_TIMER_CAP, 0, 8) < 0);       /* already at the cap: nothing */
    CHECK(klsab_hold(3, 45.0f, 0, 8) < 0);                /* above the cap (someone else held it): never lowered */
    /* hold: bad reads */
    CHECK(klsab_hold(3, -1.0f, 0, 8) < 0);
    CHECK(klsab_hold(3, z / z, 0, 8) < 0);
    CHECK(klsab_hold(3, 5000.0f, 0, 8) < 0);
    /* new visit */
    CHECK(klsab_new_visit(5, 7)); CHECK(klsab_new_visit(6, 7)); CHECK(klsab_new_visit(7, 0)); CHECK(klsab_new_visit(3, 0));
    CHECK(!klsab_new_visit(0, 0)); CHECK(!klsab_new_visit(7, 7)); CHECK(!klsab_new_visit(1, 3)); CHECK(!klsab_new_visit(3, 5));
    /* clamp */
    CHECK(klsab_clamp_hold(-5) == 1); CHECK(klsab_clamp_hold(8) == 8); CHECK(klsab_clamp_hold(500) == 20);
    /* key edge */
    memset(&k, 0, sizeof k);
    CHECK(!klsab_edge(&k, 0, 1000));
    CHECK(klsab_edge(&k, 1, 1100));
    CHECK(!klsab_edge(&k, 1, 1200));                      /* held: no repeat */
    CHECK(!klsab_edge(&k, 0, 1210));
    CHECK(!klsab_edge(&k, 1, 1220));                      /* bounce inside 150 ms */
    CHECK(!klsab_edge(&k, 0, 1400));
    CHECK(klsab_edge(&k, 1, 1500));                       /* a real second press */
    memset(&k, 0, sizeof k);
    CHECK(klsab_edge(&k, 1, 0));                          /* tick 0 still fires once */
    CHECK(!klsab_edge(&k, 1, 10));
    printf("klsabot_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
