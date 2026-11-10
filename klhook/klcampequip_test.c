#include <stdio.h>
#include "klcampequip_logic.h"
static int bad;
#define CK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); bad++; } } while (0)
int main(void)
{
    CK(klce_mode("dm") == KLCE_DM && klce_mode("MINE") == KLCE_MINE && klce_mode("log") == KLCE_LOG && klce_mode("") == KLCE_OFF && klce_mode("x") == KLCE_OFF && klce_mode(0) == KLCE_OFF);
    CK(klce_level_no("m05a\\m05a_main") == 5 && klce_level_no("M09/x") == 9 && klce_level_no("m14\\m14_main") == 14);
    CK(klce_level_no("f01\\f01_main") == -1 && klce_level_no("m\\x") == -1 && klce_level_no("m05") == -1 && klce_level_no(0) == -1);
    CK(klce_pick(KLCE_OFF, 5, 0, 1) == 0 && klce_pick(KLCE_LOG, 5, 0, 1) == 0 && klce_pick(KLCE_DM, -1, 0, 1) == 0);
    CK(klce_pick(KLCE_DM, 1, 0, 1) == 0 && klce_pick(KLCE_DM, 3, 0, 1) == 0 && klce_pick(KLCE_DM, 3, 0, 0) == KLCE_ITEM_MP5);
    CK(klce_pick(KLCE_DM, 5, 0, 1) == 20 && klce_pick(KLCE_DM, 9, 0, 1) == 29 && klce_pick(KLCE_DM, 5, 30, 1) == 30 && klce_pick(KLCE_DM, 5, 99, 1) == 20);
    CK(klce_pick(KLCE_MINE, 5, 0, 1) == 29 && klce_pick(KLCE_MINE, 2, 0, 1) == 29);
    CK(klce_pool_ok(1, 2, 0) && !klce_pool_ok(0, 2, 0) && !klce_pool_ok(1, 1, 0) && !klce_pool_ok(1, 2, 1));
    printf(bad ? "klcampequip_test: %d FAIL\n" : "klcampequip_test: PASS\n", bad);
    return bad != 0;
}
