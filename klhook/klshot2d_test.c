/* klshot2d_test.c - off-game harness for klshot2d_logic.h ([Sound] RemoteShot2DGate gate + RemoteShot2DLogAny slot-74 counter). No windows.h.
   Proves the gate table and the counter bookkeeping, NOT that a remote shot reaches slot 74 (that is the bench).
   Build: cl /nologo /W3 klshot2d_test.c /Fe:klshot2d_test.exe     Run: klshot2d_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "klshot2d_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    ks2_ctr_t c; int i;
    /* gate */
    CHECK(ks2_gate_ok(0, 0x4cca6dul) == 1 && ks2_gate_ok(1, 0x4cca6dul) == 1, "fire path passes in both gates");
    CHECK(ks2_gate_ok(0, 0x8c5680ul) == 0 && ks2_gate_ok(0, 0x8c56eful) == 0 && ks2_gate_ok(0, 0x8c583cul) == 0, "strict gate refuses the state callers");
    CHECK(ks2_gate_ok(1, 0x8c5680ul) == 1 && ks2_gate_ok(1, 0x8c56eful) == 1 && ks2_gate_ok(1, 0x8c583cul) == 1, "relaxed gate takes the state callers");
    CHECK(ks2_gate_ok(1, 0) == 0 && ks2_gate_ok(1, 0x503772ul) == 0 && ks2_gate_ok(0, 0x4cca68ul) == 0, "anything else refused");
    CHECK(ks2_gate_ok(2, 0x8c5680ul) == 0, "unknown gate value behaves strict");

    /* counter */
    ks2_ctr_reset(&c);
    CHECK(c.calls == 0 && c.n == 0 && !ks2_ctr_due(&c, 5000, 0), "empty counter is never due");
    ks2_ctr_add(&c, 0x467eb8ul, 1, 1); ks2_ctr_add(&c, 0x467eb8ul, 1, 0); ks2_ctr_add(&c, 0x90268dul, 0, 0);
    CHECK(c.calls == 3 && c.d3 == 2 && c.from503 == 1 && c.n == 2 && c.cnt[0] == 2 && c.cnt[1] == 1, "3 calls, 2 distinct callers");
    CHECK(!ks2_ctr_due(&c, 999, 0) && ks2_ctr_due(&c, 1000, 0), "due after a second");
    ks2_ctr_reset(&c);
    for (i = 0; i < 20; i++) ks2_ctr_add(&c, 0x1000ul + i, 0, 0);
    CHECK(c.calls == 20 && c.n == KS2_N && c.other == 20 - KS2_N, "table full: the rest counted as other");
    ks2_ctr_reset(&c);
    CHECK(c.calls == 0 && c.other == 0 && c.ret[0] == 0, "reset clears");
    /* stack walk with the words of the G1B host log: caller-frame ebp 368f4460, real shooter 35a20dc0, weapon 699eb480 */
    {
        unsigned long sp[0x30], sh = 0, wp = 0; int k;
        for (k = 0; k < 0x30; k++) sp[k] = 0;
        sp[0] = 0x467eb8ul; sp[0x2c / 4] = 0x902734ul; sp[0x88 / 4] = 0x503772ul; sp[0x8c / 4] = 4; sp[0x90 / 4] = 0x35a20d00ul;
        sp[0xa0 / 4] = 0x4cca6dul; sp[0x94 / 4] = 0x368f4460ul; sp[0x98 / 4] = 0x35a20dc0ul; sp[0x50 / 4] = 0x35a20dc0ul; sp[0x54 / 4] = 0x699eb480ul;
        CHECK(ks2_stack_shot(sp, 0, &sh, &wp) == KS2_SHOT_OK && sh == 0x35a20dc0ul && wp == 0x699eb480ul, "G1 shot accepted, shooter/weapon from sp[0x50]/[0x54] (got %lx/%lx)", sh, wp);
        sp[0x8c / 4] = 12; CHECK(ks2_stack_shot(sp, 0, &sh, &wp) == KS2_SHOT_SLOT, "other slot refused"); sp[0x8c / 4] = 4;
        sp[0x90 / 4] = 1; CHECK(ks2_stack_shot(sp, 0, &sh, &wp) == KS2_SHOT_FLAG, "2D flag refused"); sp[0x90 / 4] = 0;
        sp[0xa0 / 4] = 0x8c5680ul; CHECK(ks2_stack_shot(sp, 0, &sh, &wp) == KS2_SHOT_GATE && ks2_stack_shot(sp, 1, &sh, &wp) == KS2_SHOT_OK, "gate by caller word"); sp[0xa0 / 4] = 0x4cca6dul;
        sp[0x88 / 4] = 0x50378aul; CHECK(ks2_stack_shot(sp, 0, &sh, &wp) == KS2_SHOT_FROM, "npc path refused"); sp[0x88 / 4] = 0x503772ul;
        sp[0x2c / 4] = 0; CHECK(ks2_stack_shot(sp, 0, &sh, &wp) == KS2_SHOT_NOT3D, "not the 3D branch"); sp[0x2c / 4] = 0x902734ul;
        sp[0x50 / 4] = 0; CHECK(ks2_stack_shot(sp, 0, &sh, &wp) == KS2_SHOT_NOSHOOTER, "null shooter");
    }
    printf("klshot2d_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
