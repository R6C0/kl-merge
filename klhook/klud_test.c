/* klud_test.c - OFF-GAME check of klucc_down_logic.h: the Undercover Cop gate, who counts as the UCC / a heister, the hidden mask,
 * the damage clamp of [Ucc] DownOnly and the rules-vtable plan. Pure numbers; the game reads and the wrapper are klucc_down.c's (NOT run here).
 *   cl /nologo /W4 klud_test.c      or      tools/run_harness_linux.sh klud_test */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "klucc_down_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
static int klud_approx(float a, float b) { float d = a - b; return d < 0.001f && d > -0.001f; }

int main(void)
{
    float z = 0.0f, nan = z / z;
    /* gate: FA family, Undercover Cop sub-mode only */
    CHECK(klud_gate(4, 1));
    CHECK(!klud_gate(4, 0)); CHECK(!klud_gate(4, 2)); CHECK(!klud_gate(3, 1)); CHECK(!klud_gate(0, 1));
    /* the UCC: any one mark */
    CHECK(klud_is_ucc(1, 0, 0)); CHECK(klud_is_ucc(0, KLUD_NF_UCC, 0)); CHECK(klud_is_ucc(0, 0, KLUD_F_UCC));
    CHECK(!klud_is_ucc(0, 0, 0)); CHECK(!klud_is_ucc(0, 0x0001 | 0x0010, KLUD_F_POLICE));
    /* a heister: no police / UCC / dirty / dead / waiting mark */
    CHECK(klud_is_heister(0, 0, 0, 0));
    CHECK(klud_is_heister(0, 0, 0x0001, 0x20));                /* aboard bit 0x20 and other net bits do not matter */
    CHECK(klud_is_heister(0, 0, 0, 0x1));                      /* a traitor heister is still a heister */
    CHECK(!klud_is_heister(1, 0, 0, 0));                       /* police byte */
    CHECK(!klud_is_heister(0, 1, 0, 0));                       /* UCC / dirty byte */
    CHECK(!klud_is_heister(0, 0, KLUD_NF_UCC, 0));
    CHECK(!klud_is_heister(0, 0, 0, KLUD_F_POLICE)); CHECK(!klud_is_heister(0, 0, 0, KLUD_F_UCC));
    CHECK(!klud_is_heister(0, 0, 0, KLUD_F_DIRTYCOP)); CHECK(!klud_is_heister(0, 0, 0, KLUD_F_DEAD)); CHECK(!klud_is_heister(0, 0, 0, KLUD_F_WAITING));
    /* hidden */
    CHECK(klud_hidden(0, 0)); CHECK(klud_hidden(5, 0)); CHECK(!klud_hidden(5, 1ul << 5)); CHECK(klud_hidden(4, 1ul << 5));
    CHECK(klud_hidden(-1, 0xffffffffu)); CHECK(klud_hidden(40, 0xffffffffu));
    /* the clamp: floor 1 */
    CHECK(klud_approx(klud_clamp(-50.0f, 550.0f, 1.0f), -50.0f));     /* a plain hit passes */
    CHECK(klud_approx(klud_clamp(-549.0f, 550.0f, 1.0f), -549.0f));   /* leaves exactly the floor */
    CHECK(klud_approx(klud_clamp(-600.0f, 550.0f, 1.0f), -549.0f));   /* a killing hit leaves the floor */
    CHECK(klud_approx(klud_clamp(-1000000.0f, 80.0f, 1.0f), -79.0f)); /* a downed man (80) under a huge hit */
    CHECK(klud_approx(klud_clamp(-20.0f, 1.0f, 1.0f), 0.0f));         /* at the floor: costs nothing */
    CHECK(klud_approx(klud_clamp(-20.0f, 0.5f, 1.0f), 0.0f));         /* under the floor: costs nothing, never heals */
    CHECK(klud_approx(klud_clamp(30.0f, 10.0f, 1.0f), 30.0f));        /* a heal passes */
    CHECK(klud_approx(klud_clamp(0.0f, 10.0f, 1.0f), 0.0f));
    CHECK(klud_approx(klud_clamp(-75.0f, 120.0f, 80.0f), -40.0f));    /* floor 80 */
    CHECK(klud_clamp(nan, 100.0f, 1.0f) != klud_clamp(nan, 100.0f, 1.0f));   /* NaN delta passes as NaN */
    CHECK(klud_approx(klud_clamp(-10.0f, nan, 1.0f), -10.0f));        /* unreadable health: unchanged */
    /* whatever the game multiplies after the clamp (0.5 friendly fire, 0 cop-on-cop: 0x6e34b3 / 0x6e35ee) only shrinks it: still alive */
    CHECK(550.0f + 0.5f * klud_clamp(-600.0f, 550.0f, 1.0f) >= 1.0f);
    /* lethal */
    CHECK(klud_lethal(-600.0f, 550.0f, 1.0f)); CHECK(klud_lethal(-549.0f, 550.0f, 1.0f));
    CHECK(!klud_lethal(-548.0f, 550.0f, 1.0f)); CHECK(!klud_lethal(5.0f, 1.0f, 1.0f)); CHECK(!klud_lethal(nan, 1.0f, 1.0f));
    /* the vtable plan */
    {
        unsigned long SV = 0xbd2eb4, CL = 0xbd31e4, RK = 0x10001000, MS = 0x10002000, MC = 0x10003000;
        CHECK(klud_vt_plan(0, SV, CL, RK, MS, MC, 0, 0) == KLUD_VT_NONE);
        CHECK(klud_vt_plan(0xbd3514, SV, CL, RK, MS, MC, 0, 0) == KLUD_VT_NONE);          /* Arcade's Heist rules: never */
        CHECK(klud_vt_plan(MS, SV, CL, RK, MS, MC, 1, 0) == KLUD_VT_HAVE);
        CHECK(klud_vt_plan(MC, SV, CL, RK, MS, MC, 0, 0) == KLUD_VT_HAVE);
        CHECK(klud_vt_plan(RK, SV, CL, RK, MS, MC, 1, 0) == KLUD_VT_RK);
        CHECK(klud_vt_plan(SV, SV, CL, RK, MS, MC, 1, 0) == KLUD_VT_WAIT);                /* klroundkeep goes first */
        CHECK(klud_vt_plan(SV, SV, CL, RK, MS, MC, 1, KLUD_RK_WAIT_MS) == KLUD_VT_SV);    /* ... but not for ever */
        CHECK(klud_vt_plan(SV, SV, CL, RK, MS, MC, 0, 0) == KLUD_VT_SV);
        CHECK(klud_vt_plan(SV, SV, CL, 0, MS, MC, 0, 0) == KLUD_VT_SV);
        CHECK(klud_vt_plan(CL, SV, CL, RK, MS, MC, 1, 0) == KLUD_VT_CL);                  /* a client: klroundkeep never wraps Cl */
        CHECK(klud_vt_plan(0x12345678, SV, CL, 0, MS, MC, 0, 0) == KLUD_VT_NONE);         /* someone else's copy: left alone */
    }
    printf("%d checks, %d failed\n", checks, fails);
    return fails != 0;
}
