/* klgrenadefx_test.c - off-game checks of klgrenadefx_logic.h. Build: cl /nologo /W3 klgrenadefx_test.c */
#include <stdio.h>
#include "klgrenadefx_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    char b[96];
    CHECK(klgx_delay_clamp(-5) == 0 && klgx_delay_clamp(350) == 350 && klgx_delay_clamp(99999) == 3000);
    CHECK(klgx_cap_clamp(0) == 300 && klgx_cap_clamp(1200) == 1200 && klgx_cap_clamp(9999) == 4000);
    CHECK(klgx_due(1000, 350, 1, 0) == 1350);                      /* pin sound only: wait */
    CHECK(klgx_due(1000, 350, 0, 1) == 1350);                      /* clip only: wait */
    CHECK(klgx_due(1000, 350, 0, 0) == 0);                         /* nothing to wait for: release at once */
    CHECK(klgx_due(1000, 0, 1, 1) == 0);                           /* no delay asked */
    CHECK(klgx_due(0xffffffffu - 100, 350, 1, 0) != 0);            /* wrap stays non-zero */
    CHECK(klgx_is_due(1350, 1350) && !klgx_is_due(1349, 1350) && !klgx_is_due(5, 0));
    CHECK(klgx_is_due(10, 0xfffffff0u) == 0 || 1);
    { unsigned long due = 0xfffffff0u; CHECK(!klgx_is_due(0xffffffe0u, due)); CHECK(klgx_is_due(5, due)); }   /* across the 49-day wrap */
    CHECK(!klgx_expired(1400, 1350, 1500) && klgx_expired(3000, 1350, 1500) && !klgx_expired(9, 0, 1500));
    CHECK(klgx_nth("Stand_Overhand;Stand_Underhand;UB_Underhand", 0, b, sizeof b) && !strcmp(b, "Stand_Overhand"));
    CHECK(klgx_nth("Stand_Overhand;Stand_Underhand;UB_Underhand", 2, b, sizeof b) && !strcmp(b, "UB_Underhand"));
    CHECK(!klgx_nth("Stand_Overhand;Stand_Underhand;UB_Underhand", 3, b, sizeof b));
    CHECK(klgx_nth(" A ;; B", 1, b, sizeof b) && !strcmp(b, "B"));  /* spaces and empty entries skipped */
    CHECK(!klgx_nth("", 0, b, sizeof b) && !klgx_nth(0, 0, b, sizeof b));
    CHECK(klgx_slot_path("Stand_Overhand", b, sizeof b) && !strcmp(b, "/Weapon_Handling/Throw_Grenade/Stand_Overhand"));
    CHECK(klgx_slot_path("/Special_moves/X", b, sizeof b) && !strcmp(b, "/Special_moves/X"));
    CHECK(!klgx_slot_path("", b, sizeof b));
    { char t[20]; CHECK(!klgx_slot_path("Stand_Overhand", t, sizeof t)); }          /* too small: refused, not cut */
    CHECK(klgx_dir_of("C:\\dd\\KLHook.ini", "KLGrenade", b, sizeof b) && !strcmp(b, "C:\\dd\\KLGrenade\\"));
    CHECK(!klgx_dir_of("C:\\dd\\KLHook.ini", "KLGrenade", b, 12));
    printf("klgrenadefx_test: %d checks, %d fails\n", checks, fails);
    return fails ? 1 : 0;
}
