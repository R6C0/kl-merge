/* klbrain_test.c - off-game harness for klbrain_logic.h ([Brain] vector insertion order, growth, switches, PuppetOff window). No windows.h.
   Build: cl /nologo /W3 klbrain_test.c /Fe:klbrain_test.exe     Run: klbrain_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "klbrain_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    kbr_u16 out[16]; int n, v, o[4]; kbr_u32 el[16], succ[4];
    /* orders: Loot is last in each vector, Traitor before Board, vectors C has 8 members */
    CHECK(kbr_ordn[0] == 13 && kbr_ordn[1] == 15 && kbr_ordn[2] == 8, "order sizes %d %d %d", kbr_ordn[0], kbr_ordn[1], kbr_ordn[2]);
    for (v = 0; v < KBR_NVEC; v++) {
        CHECK(kbr_after(v, KBR_F_LOOT, out, 16) == 0, "Loot is last in vector %d", v);
        n = kbr_after(v, KBR_F_TRAITOR, out, 16);
        CHECK(n > 0 && out[0] == KBR_F_BOARD, "Board follows Traitor in vector %d", v);
        CHECK(kbr_after(v, 0x123, out, 16) == 0, "unknown field");
    }
    CHECK(kbr_after(0, KBR_F_BOARD, out, 2) == 2, "cap respected");
    /* insertion index: first element equal to a non-zero successor, else append */
    el[0] = 10; el[1] = 20; el[2] = 30;
    succ[0] = 30; succ[1] = 0;
    CHECK(kbr_insert_index(el, 3, succ, 2) == 2, "before successor");
    succ[0] = 0; succ[1] = 0;
    CHECK(kbr_insert_index(el, 3, succ, 2) == 3, "null successors append");
    succ[0] = 20; succ[1] = 10;
    CHECK(kbr_insert_index(el, 3, succ, 2) == 0, "earliest hit wins");
    CHECK(kbr_insert_index(el, 0, succ, 2) == 0, "empty vector");
    /* vector header plausibility */
    CHECK(kbr_vec_ok(0x1000, 0x1010, 0x1028), "good vector");
    CHECK(kbr_vec_ok(0x1000, 0x1000, 0x1028), "empty vector with reserve");
    CHECK(!kbr_vec_ok(0, 0, 0), "null");
    CHECK(!kbr_vec_ok(0x1002, 0x1010, 0x1028), "misaligned");
    CHECK(!kbr_vec_ok(0x1000, 0x1030, 0x1028), "last past end");
    CHECK(!kbr_vec_ok(0x1000, 0x1000, 0x1000), "no reserve");
    CHECK(!kbr_vec_ok(0x1000, 0x1000, 0x1000 + 4 * 300), "huge");
    /* growth */
    CHECK(kbr_grow_cap(3) == 16, "min 16");
    CHECK(kbr_grow_cap(20) == 40, "double");
    CHECK(kbr_grow_cap(200) == 0, "refuse over 256");
    /* insert */
    el[0] = 1; el[1] = 2; el[2] = 3;
    CHECK(kbr_insert(el, 3, 16, 1, 99) == 4 && el[0] == 1 && el[1] == 99 && el[2] == 2 && el[3] == 3, "insert middle");
    CHECK(kbr_insert(el, 4, 16, 4, 7) == 5 && el[4] == 7, "insert end");
    CHECK(kbr_insert(el, 5, 5, 0, 7) == -1, "full");
    CHECK(kbr_insert(el, 5, 16, 6, 7) == -1, "idx past end");
    CHECK(kbr_insert(el, 5, 16, -1, 7) == -1, "negative idx");
    /* the real ctor order reproduced: vector A with other members, push Traitor, Board, Loot into it */
    {
        kbr_u32 vec[16]; int cnt = 0, idx; kbr_u32 other_after = 777;
        vec[cnt++] = 5; vec[cnt++] = other_after;      /* 5 = an earlier member; 777 = a LATER member (0x5ac) */
        succ[0] = other_after;                         /* successor of Traitor: contains the later member */
        idx = kbr_insert_index(vec, cnt, succ, 1);
        cnt = kbr_insert(vec, cnt, 16, idx, 111);
        CHECK(cnt == 3 && vec[1] == 111 && vec[2] == 777, "Traitor lands before the later member");
        idx = kbr_insert_index(vec, cnt, succ, 0);     /* Loot: no successors -> append */
        cnt = kbr_insert(vec, cnt, 16, idx, 333);
        CHECK(cnt == 4 && vec[3] == 333, "Loot appended");
    }
    /* switches */
    kbr_switches(1, 0, 1, 1, o);
    CHECK(o[0] == 1 && o[1] == 0 && o[2] == 0 && o[3] == 0, "Loot / PuppetOff need Build");
    kbr_switches(0, 1, 0, 1, o);
    CHECK(o[1] == 1 && o[2] == 0 && o[3] == 0, "PuppetOff needs Loot");
    kbr_switches(0, 1, 1, 1, o);
    CHECK(o[1] == 1 && o[2] == 1 && o[3] == 1, "all on");
    kbr_switches(0, 0, 0, 0, o);
    CHECK(!o[0] && !o[1] && !o[2] && !o[3], "all off");
    /* puppet window */
    CHECK(!kbr_puppet_released(0, 1, 1000, 900, 5000), "off");
    CHECK(!kbr_puppet_released(1, 0, 1000, 900, 5000), "not built");
    CHECK(!kbr_puppet_released(1, 1, 1000, 0, 5000), "never nonzero");
    CHECK(kbr_puppet_released(1, 1, 1000, 900, 5000), "recent");
    CHECK(!kbr_puppet_released(1, 1, 9000, 900, 5000), "stale");
    CHECK(kbr_puppet_released(1, 1, 100, 0xfffffff0ul, 5000), "wrap safe");
    printf("klbrain_test: %d checks, %d FAIL\n", checks, fails);
    return fails ? 1 : 0;
}
