/* klogrudge_test.c - off-game harness for klogrudge_logic.h. Build: cl /nologo /W3 klogrudge_test.c /Fe:klogrudge_test.exe   Run: exit 0 = all pass */
#include <stdio.h>
#include "klogrudge_logic.h"
static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)
int main(void)
{
    CHECK(kgo_fresh(100, 200), "clock before stamp = fresh");
    CHECK(!kgo_fresh(200, 200), "clock at stamp = stale");
    CHECK(!kgo_fresh(300, 200), "past stamp = stale");
    CHECK(!kgo_fresh(0, 0), "no stamp = stale");
    CHECK(kgo_eligible(0, 0), "plain heister");
    CHECK(kgo_eligible(3, 0x20), "other bits do not bar");
    CHECK(!kgo_eligible(-1, 0), "no index");
    CHECK(!kgo_eligible(16, 0), "index out of range");
    CHECK(!kgo_eligible(1, KGO_F_TRAITOR), "already traitor");
    CHECK(!kgo_eligible(1, KGO_F_DEAD), "dead killer");
    CHECK(!kgo_eligible(1, KGO_F_POLICE), "police seat");
    CHECK(!kgo_eligible(1, KGO_F_ESCAPED), "escaped");
    CHECK(!kgo_eligible(1, KGO_F_UNDERCOVER), "undercover cop (stock js at 0x794a9b)");
    CHECK(!kgo_eligible(1, 0x80u | 0x20u), "undercover with other bits");
    CHECK(kgo_victim(2, 0) == 0, "ally bot, never a traitor: counts");
    CHECK(kgo_victim(1, 0) == 1, "enemy team (police / turned) does not count");
    CHECK(kgo_victim(3, 0) == 1, "other team does not count");
    CHECK(kgo_victim(2, 1) == 2, "marked / turned traitor does not count");
    CHECK(kgo_victim(1, 1) == 1, "turned traitor on team Enemy: team first");
    {
        int how = 0;
        CHECK(kgo_decide(3, 100, -1, -1, KGO_NEVER, &how) == 3 && how == 1, "lethal blow by human 3 wins");
        CHECK(kgo_decide(3, KGO_LETHAL_MS + 1, -1, -1, KGO_NEVER, &how) == -1 && how == 4, "old lethal blow, no stamp: nobody");
        CHECK(kgo_decide(3, 100, -1, 5, 10, &how) == 3 && how == 1, "lethal blow beats stamp and a non-human hit");
        CHECK(kgo_decide(-2, 100, -1, 5, KGO_NEVER, &how) == -1 && how == 3, "lethal blow by a cop: the stale human stamp is refused");
        CHECK(kgo_decide(-2, KGO_LETHAL_MS + 1, -1, 5, KGO_NEVER, &how) == 5 && how == 6, "old non-human lethal blow does not veto a stamp");
        CHECK(kgo_decide(-1, 0, -1, -1, KGO_NEVER, &how) == -1 && how == 4, "nothing");
        CHECK(kgo_decide(-1, 0, 2, 2, KGO_NEVER, &how) == 2 && how == 6, "stamp at death, same as the latch");
        CHECK(kgo_decide(-1, 0, -1, 4, KGO_NEVER, &how) == 4 && how == 6, "stamp at death, no latch");
        CHECK(kgo_decide(-1, 0, 2, 4, KGO_NEVER, &how) == -1 && how == 5, "stamp changed since the last poll");
        CHECK(kgo_decide(-1, 0, 2, 2, 1000, &how) == -1 && how == 2, "a cop hit the bot in the window: refused");
        CHECK(kgo_decide(-1, 0, 2, 2, KGO_WINDOW_MS + 1, &how) == 2 && how == 6, "old non-human hit does not veto");
        CHECK(kgo_decide(-1, 0, 2, -1, KGO_NEVER, &how) == -1 && how == 4, "latch alone is NOT a killer (stale human after a cop took over)");
    }
    CHECK(kgo_step(0, 0, 1) == 1 && kgo_step(0, 0, 0) == 1, "alive: poll");
    CHECK(kgo_step(1, 0, 0) == 2, "dead first time after seen alive: fire");
    CHECK(kgo_step(1, 0, 1) == 3, "first seen already dead: booked, never fires");
    CHECK(kgo_step(1, 1, 0) == 0, "dead already booked: nothing");
    {
        unsigned long d[KGO_NDONE]; int n = 0, i;
        CHECK(!kgo_done_has(d, n, 0x1000), "empty set");
        kgo_done_add(d, &n, 0x1000); kgo_done_add(d, &n, 0x1000);
        CHECK(n == 1 && kgo_done_has(d, n, 0x1000), "added once");
        CHECK(!kgo_done_has(d, n, 0x2000), "other actor not in");
        for (i = 0; i < KGO_NDONE + 5; i++) kgo_done_add(d, &n, 0x10000ul + (unsigned long)i);
        CHECK(kgo_done_has(d, n, 0x10000ul + KGO_NDONE + 4), "newest kept after the ring wraps");
        CHECK(!kgo_done_has(d, n, 0x1000), "oldest evicted by the ring");
    }
    CHECK(kgo_after_hit(-1, 1, 3, 1) == 3, "lethal human hit names the human");
    CHECK(kgo_after_hit(3, 0, -1, 1) == -2, "lethal cop hit after a human's: the cop");
    CHECK(kgo_after_hit(-1, 1, -1, 1) == -2, "lethal 'human' without an index counts as non-human");
    CHECK(kgo_after_hit(3, 0, -1, 0) == -1, "non-lethal predicted: a later cop hit clears the human's predicted blow");
    CHECK(kgo_after_hit(-2, 0, -1, 0) == -2, "non-lethal cop hit keeps a cop's lethal blow");
    CHECK(kgo_after_hit(3, 1, 4, 0) == 3, "non-lethal human hit keeps the earlier lethal human");
    CHECK(kgo_after_hit(-1, 0, -1, 0) == -1, "nothing stays nothing");
    {   /* cop kills after a human tag: the human's predicted lethal blow, the bot lives, a cop's hit, then the death with the human stamp still fresh */
        int how = 0, lw = kgo_after_hit(-1, 1, 2, 1);
        lw = kgo_after_hit(lw, 0, -1, 0);
        CHECK(kgo_decide(lw, 200, 2, 2, 50, &how) == -1 && how == 2, "cop kills after a human tag: no mark (how %d)", how);
    }
    CHECK(kgo_submode_ok(0), "FA sub-mode");
    CHECK(!kgo_submode_ok(1), "Undercover Cop: off");
    CHECK(!kgo_submode_ok(2), "Cops and Robbers: off");
    printf("klogrudge_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
