/* kldroptable_test.c - off-game harness for kldroptable_logic.h ([BotFill] drop table eviction; klbotfill.c includes the same header). No windows.h.
   Build: cl /nologo /W3 kldroptable_test.c /Fe:kldroptable_test.exe     Run: kldroptable_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include "kldroptable_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

static struct kdtb_ent mk(int used, int hid, int drn, int target, unsigned int age)
{
    struct kdtb_ent e; e.used = used; e.hid = hid; e.drn = drn; e.target = target; e.age = age; return e;
}

int main(void)
{
    struct kdtb_ent t[6]; int i;
    for (i = 0; i < 6; i++) t[i] = mk(1, 1, 0, 0, 1000u + 10u * i);
    CHECK(kdtb_evict(t, 6, 0) == 5, "full of hidden pool objects, real drop: the oldest (largest age) goes");
    CHECK(kdtb_evict(t, 6, -1) == 5, "unreadable hidden bit is a real candidate");
    CHECK(kdtb_evict(t, 6, 1) == -1, "a hidden pool candidate never replaces anything");
    CHECK(kdtb_evict(t, 0, 0) == -1, "empty list");

    t[5].target = 1;
    CHECK(kdtb_evict(t, 6, 0) == 4, "the oldest is a bot's target: next oldest");
    t[4].drn = 1;
    CHECK(kdtb_evict(t, 6, 0) == 3, "a drained entry is kept");
    t[3].hid = 0;
    CHECK(kdtb_evict(t, 6, 0) == 2, "an unhidden entry is kept");
    t[2].hid = -1;
    CHECK(kdtb_evict(t, 6, 0) == 1, "an unreadable entry is kept");
    t[1].used = 0;
    CHECK(kdtb_evict(t, 6, 0) == 0, "an unused slot is not a victim (the caller takes free slots first)");
    t[0].target = 1;
    CHECK(kdtb_evict(t, 6, 0) == -1, "no victim: the table stays, the candidate is not tracked");

    for (i = 0; i < 4; i++) t[i] = mk(1, 1, 0, 0, 500u);
    CHECK(kdtb_evict(t, 4, 0) == 0, "equal ages: the lowest index");
    t[3].age = 0xfffffff0u;
    CHECK(kdtb_evict(t, 4, 0) == 3, "age is already now - first (unsigned), larger = older");

    printf("kldroptable_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
