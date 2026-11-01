/* klhud_boardbots_test.c - off-game checks of klhud_boardbots_logic.h ([HUD] OnlineBoardBots). Build: cl /nologo /W3 klhud_boardbots_test.c */
#include <stdio.h>
#include "klhud_boardbots_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    struct kbb_tab t; long v = -1; int i, nd, ne, nl, na, nled;
    kbb_reset(&t);
    /* tick 1: four bots alive */
    kbb_begin(&t);
    kbb_note(&t, 0x1000, "Kane", 1); kbb_note(&t, 0x2000, "Lynch", 1); kbb_note(&t, 0x3000, "Shiv", 1); kbb_note(&t, 0x4000, "Hex", 1);
    CHECK(t.n == 4); CHECK(kbb_note(&t, 0, "x", 1) == -1);
    /* tick 2: Lynch dies (body stays), Shiv vanishes (boarded or despawned), Hex stays */
    kbb_begin(&t);
    kbb_note(&t, 0x1000, "Kane", 1); kbb_note(&t, 0x2000, "Lynch", 0); kbb_note(&t, 0x4000, "Hex", 1);
    CHECK(t.n == 4 && t.l[1].seen_dead && t.l[1].seen_alive && t.l[1].alive_now == 0);
    /* CLIENT (no ledger): van not yet at last call -> the vanished one is unknown, not ESCAPED */
    CHECK(kbb_fate(&t.l[0], 0) == KBB_FATE_LEFT);
    CHECK(kbb_fate(&t.l[1], 0) == KBB_FATE_DEAD);
    CHECK(kbb_fate(&t.l[2], 0) == KBB_FATE_AI);
    CHECK(kbb_fate(&t.l[2], 3) == KBB_FATE_AI);
    CHECK(kbb_fate(&t.l[2], KBB_VAN_LASTCALL) == KBB_FATE_ESCAPED);
    CHECK(kbb_fate(&t.l[2], 7) == KBB_FATE_ESCAPED);
    CHECK(kbb_money(&t.l[2], KBB_FATE_ESCAPED, &v) == 0 && v == -1);          /* client: payout unknown, never invented */
    CHECK(kbb_money(&t.l[0], KBB_FATE_LEFT, &v) == 0);
    /* a corpse that despawned after being seen dead stays DEAD, never ESCAPED */
    kbb_begin(&t);
    kbb_note(&t, 0x1000, "Kane", 1); kbb_note(&t, 0x4000, "Hex", 1);
    CHECK(kbb_fate(&t.l[1], 7) == KBB_FATE_DEAD);                             /* seen dead, body gone: DEAD, never ESCAPED */
    CHECK(t.l[1].seen_dead);
    /* HOST: the ledger says Shiv boarded with 250000, Hex carried 100000 but never boarded */
    kbb_ledger(&t, 2, 1, 1, 250000); kbb_ledger(&t, 3, 1, 0, 100000); kbb_ledger(&t, 0, 0, 0, 0); kbb_ledger(&t, 9, 1, 1, 5); kbb_ledger(&t, 1, 1, 0, 0);
    CHECK(kbb_fate(&t.l[2], 0) == KBB_FATE_ESCAPED);
    CHECK(kbb_money(&t.l[2], KBB_FATE_ESCAPED, &v) == 1 && v == 250000);
    CHECK(kbb_fate(&t.l[3], 7) == KBB_FATE_LEFT);
    CHECK(kbb_money(&t.l[3], KBB_FATE_LEFT, &v) == 1 && v == 0);              /* host: left behind pays 0 */
    CHECK(t.l[0].ledger == 0);                                                /* untracked actor stays unknown */
    /* the aboard latch is sticky and the tally keeps its largest value (the ledger resets when the round ends) */
    kbb_ledger(&t, 2, 1, 0, 0);
    CHECK(t.l[2].aboard == 1 && t.l[2].tally == 250000);
    kbb_summary(&t, 7, &nd, &ne, &nl, &na, &nled);
    CHECK(nd + ne + nl + na == t.n); CHECK(ne == 1 && nl == 2 && na == 0 && nd == 1 && nled == 3);
    /* table cap */
    kbb_reset(&t);
    for (i = 0; i < KBB_MAX + 3; i++) kbb_note(&t, 0x100ul + (unsigned long)i, "b", 1);
    CHECK(t.n == KBB_MAX); CHECK(kbb_note(&t, 0x100, "b", 1) == 0);
    CHECK(kbb_note(&t, 0x999, "b", 1) == -1);
    printf("klhud_boardbots_test: %d checks, %d fail\n", checks, fails);
    return fails ? 1 : 0;
}
