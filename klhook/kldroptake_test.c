/* kldroptake_test.c - off-game harness for kldroptake_logic.h ([BotFill] OnlineDropTake pure decision; klbotfill.c includes the same header). No windows.h.
   Build: cl /nologo /W3 kldroptake_test.c /Fe:kldroptake_test.exe     Run: kldroptake_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "kldroptake_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

static struct kdt_cand mk(int hid, int drn, int amt, int taken, int bad, float dist)
{
    struct kdt_cand c; c.hid = hid; c.drn = drn; c.amt = amt; c.posok = 1; c.taken = taken; c.bad = bad; c.dist = dist; return c;
}

int main(void)
{
    struct kdt_cand a[4]; int ex;
    CHECK(kdt_wanted(1, -1, 0, 0, 2) == 1, "wanted: nothing to take, empty hands");
    CHECK(kdt_wanted(0, -1, 0, 0, 2) == 0, "off");
    CHECK(kdt_wanted(1, 3, 0, 0, 2) == 0, "a stack exists: not wanted");
    CHECK(kdt_wanted(1, -1, 500, 1, 2) == 0, "carrying: not wanted");
    CHECK(kdt_wanted(1, -1, 0, 2, 2) == 0, "grab cap reached: not wanted");

    CHECK(kdt_pick(a, 0, 8000, &ex) == -1 && ex == 0, "empty list");
    a[0] = mk(0, 1, 100, 0, 0, 500);
    CHECK(kdt_pick(a, 1, 0, &ex) == -1 && ex == 0, "max 0 = off");
    CHECK(kdt_pick(a, 1, 8000, NULL) == 0, "NULL exists ok");

    a[0] = mk(1, 1, 100, 0, 0, 500);
    CHECK(kdt_pick(a, 1, 8000, &ex) == -1 && ex == 0, "hidden pool drop never");
    a[0] = mk(-1, 1, 100, 0, 0, 500);
    CHECK(kdt_pick(a, 1, 8000, &ex) == -1 && ex == 0, "hidden unreadable never");
    a[0] = mk(0, 0, 100, 0, 0, 500);
    CHECK(kdt_pick(a, 1, 8000, &ex) == -1 && ex == 0, "no preceding drain never");
    a[0] = mk(0, 1, 0, 0, 0, 500);
    CHECK(kdt_pick(a, 1, 8000, &ex) == -1 && ex == 0, "amount 0 never");
    a[0] = mk(0, 1, 100, 0, 1, 500);
    CHECK(kdt_pick(a, 1, 8000, &ex) == -1 && ex == 0, "blacklisted never, and does not hold the van");
    a[0] = mk(0, 1, 100, 0, 0, 500); a[0].posok = 0;
    CHECK(kdt_pick(a, 1, 8000, &ex) == -1 && ex == 0, "position unreadable never");
    a[0] = mk(0, 1, 100, 0, 0, 8001);
    CHECK(kdt_pick(a, 1, 8000, &ex) == -1 && ex == 0, "too far");
    a[0] = mk(0, 1, 100, 0, 0, 8000);
    CHECK(kdt_pick(a, 1, 8000, &ex) == 0 && ex == 1, "exactly at the limit");

    a[0] = mk(0, 1, 100, 0, 0, 3000); a[1] = mk(0, 1, 200, 0, 0, 1000); a[2] = mk(1, 1, 300, 0, 0, 10); a[3] = mk(0, 1, 50, 1, 0, 100);
    CHECK(kdt_pick(a, 4, 8000, &ex) == 1 && ex == 1, "nearest free ok drop (hidden and taken ones skipped)");
    a[1].taken = 1; a[0].taken = 1;
    CHECK(kdt_pick(a, 4, 8000, &ex) == -1 && ex == 1, "all taken: no pick but the van stays held");

    printf("kldroptake_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
