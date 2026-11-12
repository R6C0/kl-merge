/* klcampgive_test.c - OFF-GAME check of klcampgive_logic.h.  cl /nologo /W4 klcampgive_test.c */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "klcampgive_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    int ids[8], n; struct klcgv_in in; volatile float zero = 0.0f;
    CHECK(klcgv_slot_of(0) == 3); CHECK(klcgv_slot_of(1) == 0); CHECK(klcgv_slot_of(2) == 1); CHECK(klcgv_slot_of(3) == 2); CHECK(klcgv_slot_of(4) == -1); CHECK(klcgv_slot_of(-1) == -1);
    CHECK(klcgv_clamp_range(300.0f) == 300.0f); CHECK(klcgv_clamp_range(0.0f) == 300.0f); CHECK(klcgv_clamp_range(-5.0f) == 300.0f); CHECK(klcgv_clamp_range(9000.0f) == 300.0f); CHECK(klcgv_clamp_range(zero / zero) == 300.0f); CHECK(klcgv_clamp_range(150.0f) == 150.0f);
    CHECK(klcgv_types_ok(6, 1) && klcgv_types_ok(6, 2) && !klcgv_types_ok(6, 0) && !klcgv_types_ok(6, 3) && !klcgv_types_ok(6, -1) && !klcgv_types_ok(0xffffffffu, 32));
    n = klcgv_parse_ids("50,51 53;54", ids, 8); CHECK(n == 4 && ids[0] == 50 && ids[3] == 54);
    n = klcgv_parse_ids("99,7,abc,63,64", ids, 8); CHECK(n == 2 && ids[0] == 7 && ids[1] == 63);
    n = klcgv_parse_ids("1,2,3,4,5", ids, 3); CHECK(n == 3); CHECK(klcgv_parse_ids(0, ids, 8) == 0); CHECK(klcgv_parse_ids("", ids, 8) == 0);
    CHECK(klcgv_parse_ids("99999999999999", ids, 8) == 0);
    CHECK(klcgv_refused(ids, 0, 5) == 0); ids[0] = 50; ids[1] = 54; CHECK(klcgv_refused(ids, 2, 54) && !klcgv_refused(ids, 2, 53));
    CHECK(klcgv_swap_res(40, 30, 0) == -1); CHECK(klcgv_swap_res(40, 30, 2) == 40); CHECK(klcgv_swap_res(999, 30, 2) == 60); CHECK(klcgv_swap_res(-1, 0, 1) == 30); CHECK(klcgv_swap_res(0, 30, 2) == 0);
    memset(&in, 0, sizeof in); ids[0] = 50; ids[1] = 51; ids[2] = 53; ids[3] = 54;
    in.haveBody = 1; in.alive = 1; in.haveItem = 1; in.isWeapon = 1; in.id = 10; in.type = 1; in.dist = 100; in.range = 300; in.types = 6; in.refuse = ids; in.nrefuse = 4; in.swap = 1;
    CHECK(klcgv_decide(&in) == KLCGV_OK);
    in.haveOld = 1; CHECK(klcgv_decide(&in) == KLCGV_OK); in.swap = 0; CHECK(klcgv_decide(&in) == KLCGV_HASOLD); in.swap = 1; in.oldIsItem = 1; CHECK(klcgv_decide(&in) == KLCGV_SAME); in.haveOld = in.oldIsItem = 0;
    in.id = 53; CHECK(klcgv_decide(&in) == KLCGV_REFUSED); in.id = 64; CHECK(klcgv_decide(&in) == KLCGV_UNBOUND); in.id = 10;
    in.type = 0; CHECK(klcgv_decide(&in) == KLCGV_TYPE); in.type = 9; CHECK(klcgv_decide(&in) == KLCGV_UNBOUND); in.type = 2;
    in.dist = 301; CHECK(klcgv_decide(&in) == KLCGV_FAR); in.dist = zero / zero; CHECK(klcgv_decide(&in) == KLCGV_FAR); in.dist = 10;
    in.isWeapon = 0; CHECK(klcgv_decide(&in) == KLCGV_NOTGUN); in.isWeapon = 1; in.haveItem = 0; CHECK(klcgv_decide(&in) == KLCGV_NOITEM); in.haveItem = 1;
    in.alive = 0; CHECK(klcgv_decide(&in) == KLCGV_DEAD); in.alive = 1; in.haveBody = 0; CHECK(klcgv_decide(&in) == KLCGV_NOTARGET);
    CHECK(!klcgv_giveback_due(KLCGV_S_NONE)); CHECK(klcgv_giveback_due(KLCGV_S_REMOVED)); CHECK(klcgv_giveback_due(KLCGV_S_PARENT)); CHECK(!klcgv_giveback_due(KLCGV_S_OWNED));
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails ? 1 : 0;
}
