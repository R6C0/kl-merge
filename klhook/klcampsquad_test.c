/* klcampsquad_test.c - OFF-GAME check of klcampsquad_logic.h (pure numbers; the game reads and calls are klcampsquad.c's, NOT run here).
 *   cl /nologo /W4 klcampsquad_test.c */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "klcampsquad_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    struct klcsq_k k; struct klcsq_rec_in r; int was = 0; volatile float zero = 0.0f;
    /* clamps */
    CHECK(klcsq_clamp_attack_t(3.0f) == 3.0f); CHECK(klcsq_clamp_attack_t(0.0f) == 5.0f); CHECK(klcsq_clamp_attack_t(-1.0f) == 5.0f);
    CHECK(klcsq_clamp_attack_t(120.0f) == 5.0f); CHECK(klcsq_clamp_attack_t(zero / zero) == 5.0f);
    CHECK(klcsq_clamp_settle_ms(0.0f) == 0); CHECK(klcsq_clamp_settle_ms(1.5f) == 1500); CHECK(klcsq_clamp_settle_ms(31.0f) == 2000); CHECK(klcsq_clamp_settle_ms(-1.0f) == 2000);
    CHECK(klcsq_recmode("off") == KLCSQ_REC_OFF); CHECK(klcsq_recmode("start") == KLCSQ_REC_START); CHECK(klcsq_recmode("always") == KLCSQ_REC_ALWAYS);
    CHECK(klcsq_recmode("0") == KLCSQ_REC_OFF); CHECK(klcsq_recmode("1") == KLCSQ_REC_ALWAYS); CHECK(klcsq_recmode("2") == KLCSQ_REC_START); CHECK(klcsq_recmode("junk") == -1); CHECK(klcsq_recmode(0) == -1);
    /* M01 refusal */
    CHECK(klcsq_is_m01("m01\\m01_main")); CHECK(klcsq_is_m01("m01a\\m01a_main")); CHECK(!klcsq_is_m01("m02\\m02_main")); CHECK(!klcsq_is_m01("f01\\f01_main")); CHECK(!klcsq_is_m01(0));
    CHECK(klcsq_refuse_rule(-1, "m01\\m01_main")); CHECK(!klcsq_refuse_rule(-1, "m02\\m02_main")); CHECK(klcsq_refuse_rule(1, "m02\\m02_main")); CHECK(!klcsq_refuse_rule(0, "m01\\m01_main"));
    /* tap: press and release inside 250 ms */
    memset(&k, 0, sizeof k);
    CHECK(klcsq_key_step(&k, 1, 1000) == 0); CHECK(klcsq_key_step(&k, 1, 1100) == 0); CHECK(klcsq_key_step(&k, 0, 1150) == 2); CHECK(klcsq_key_step(&k, 0, 1200) == 0);
    /* hold: fires once at 250 ms, release afterwards is NOT a tap */
    CHECK(klcsq_key_step(&k, 1, 2000) == 0); CHECK(klcsq_key_step(&k, 1, 2249) == 0); CHECK(klcsq_key_step(&k, 1, 2250) == 1); CHECK(klcsq_key_step(&k, 1, 3000) == 0); CHECK(klcsq_key_step(&k, 0, 3100) == 0);
    /* a new press starts over */
    CHECK(klcsq_key_step(&k, 1, 4000) == 0); CHECK(klcsq_key_step(&k, 0, 4010) == 2);
    /* edge */
    CHECK(!klcsq_edge(&was, 0)); CHECK(klcsq_edge(&was, 1)); CHECK(!klcsq_edge(&was, 1)); CHECK(!klcsq_edge(&was, 0)); CHECK(klcsq_edge(&was, 1));
    /* recruit classifier: start mode */
    memset(&r, 0, sizeof r); r.mode = KLCSQ_REC_START; r.able = 1; r.sq = 0x5000; r.P = 0x6000; r.settleMs = 2000; r.sinceQ = 5000; r.sinceTry = -1; r.adopt = 1;
    CHECK(klcsq_recruit_class(&r) == KLCSQ_R_RECRUIT);                       /* free (+0x4f4 == 0), settled */
    r.sinceQ = 100; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_SETTLE); r.sinceQ = 5000;
    r.gateClosed = 1; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_WAIT); r.gateClosed = 0;
    r.able = 0; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_SKIP); r.able = 1;
    r.nodeOff = 1; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_SKIP); r.nodeOff = 0;
    r.q = 0x7000; r.own = 0; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_ADOPT);   /* held by a level squad, no owner */
    r.own = 0x8000; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_LEAVE);
    r.own = 0; r.adopt = 0; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_LEAVE); r.adopt = 1;
    r.q = r.sq; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_ADDRECV);              /* in the player squad, not a receiver */
    r.squadBusy = 1; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_WAIT); r.squadBusy = 0;
    r.q = 0; r.tries = 8; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_GIVEUP); r.tries = 0;
    r.sinceTry = 1000; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_SKIP); r.sinceTry = 3000; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_RECRUIT);
    r.mode = KLCSQ_REC_OFF; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_SKIP);
    /* always mode: ignores level squads and the settle time */
    r.mode = KLCSQ_REC_ALWAYS; r.q = 0x7000; r.sinceQ = 0; r.sinceTry = -1; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_RECRUIT);
    r.q = r.sq; r.own = r.P; CHECK(klcsq_recruit_class(&r) == KLCSQ_R_SKIP);
    /* critical */
    CHECK(klcsq_crit_needs_clear(1)); CHECK(!klcsq_crit_needs_clear(0));
    CHECK(klcsq_crit_due(1, 5, 6, 0, 0)); CHECK(!klcsq_crit_due(1, 5, 5, 0, 5000)); CHECK(klcsq_crit_due(1, 5, 5, 1, 1000)); CHECK(!klcsq_crit_due(1, 5, 5, 1, 999)); CHECK(!klcsq_crit_due(0, 5, 6, 0, 0));
    /* list helpers */
    CHECK(klcsq_nrecv(3) == 3); CHECK(klcsq_nrecv(17) == 16); CHECK(klcsq_nrecv(0xffffffffu) == 16);
    CHECK(klcsq_cur_idx(0x1020, 0x1000, 4) == 8 || klcsq_cur_idx(0x1020, 0x1000, 4) == -1);
    CHECK(klcsq_cur_idx(0x1008, 0x1000, 4) == 2); CHECK(klcsq_cur_idx(0x1010, 0x1000, 4) == -1); CHECK(klcsq_cur_idx(0xfff, 0x1000, 4) == -1); CHECK(klcsq_cur_idx(0x1002, 0x1000, 4) == -1);
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails ? 1 : 0;
}
