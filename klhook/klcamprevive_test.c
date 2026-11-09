/* klcamprevive_test.c - off-game checks of klcamprevive_logic.h. Build: cl /nologo /W3 klcamprevive_test.c */
#include <stdio.h>
#include "klcamprevive_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    CHECK(kcv_bleed_sec(0) == 60 && kcv_bleed_sec(1) == 45 && kcv_bleed_sec(2) == 30 && kcv_bleed_sec(3) == 30);
    CHECK(kcv_bleed_sec(-1) == 30 && kcv_bleed_sec(9) == 30);
    CHECK(kcv_deadline(1000, 0) == 61000);
    CHECK(kcv_deadline(0, 2) == 30000);
    CHECK(kcv_backoff(0) == 10000 && kcv_backoff(1) == 20000 && kcv_backoff(2) == 40000);
    CHECK(kcv_backoff(3) == 80000 && kcv_backoff(4) == 160000 && kcv_backoff(5) == 160000 && kcv_backoff(40) == 160000);
    CHECK(kcv_hp_at_floor(25, 100));
    CHECK(kcv_hp_at_floor(10, 100));
    CHECK(!kcv_hp_at_floor(26, 100));
    CHECK(!kcv_hp_at_floor(0, 0));
    CHECK(!kcv_hp_at_floor(-1, -1));
    CHECK(kcv_gate_wstand(KCV_G_NOTASK) && kcv_gate_wstand(KCV_G_ROOM) && kcv_gate_wstand(KCV_G_REFUSED) && kcv_gate_wstand(KCV_G_NOSTART));
    CHECK(!kcv_gate_wstand(KCV_G_ISDOWN) && !kcv_gate_wstand(KCV_G_DYING) && !kcv_gate_wstand(KCV_G_VEHICLE));
    CHECK(kcv_prompt_ok(KCV_DOWN, 150, 10));
    CHECK(kcv_prompt_ok(KCV_DOWN, 200, -50));
    CHECK(!kcv_prompt_ok(KCV_DOWN, 201, 0));
    CHECK(!kcv_prompt_ok(KCV_DOWN, 100, 51));
    CHECK(!kcv_prompt_ok(KCV_NORMAL, 100, 0));
    CHECK(!kcv_bled_out(100, 0));
    CHECK(!kcv_bled_out(999, 1000));
    CHECK(kcv_bled_out(1000, 1000));
    CHECK(kcv_bled_out(2000, 1000));
    CHECK(kcv_observe_state(1, 1, 1) == KCV_DOWN);
    CHECK(kcv_observe_state(1, 1, 0) == KCV_NORMAL);
    CHECK(kcv_observe_state(1, 0, 1) == KCV_NORMAL);
    CHECK(kcv_observe_state(0, 1, 1) == KCV_DEAD);
    CHECK(kcv_observe_state(2, 0, 0) == KCV_DEAD);
    CHECK(kcv_idle(0, 1, 0) && kcv_idle(1, 0, 0) && kcv_idle(1, 1, 1) && !kcv_idle(1, 1, 0));
    CHECK(kcv_merc_id_ok(1) && kcv_merc_id_ok(13) && !kcv_merc_id_ok(0) && !kcv_merc_id_ok(14));
    CHECK(KCV_MASK == 0x4000);
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
