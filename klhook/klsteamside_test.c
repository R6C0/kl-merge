/* klsteamside_test.c - OFF-GAME check of klsteamside.h (the [Net] SideChannelSteam probe's pure part: version fallback order, ISteamClient vtable offset,
 * peer-entry parse, table sanity, the once-a-minute / 20-line log budget). No windows.h, no Steam.
 *   cl /nologo /W4 klsteamside_test.c      or      tools/run_harness_linux.sh klsteamside_test */
#include <stdio.h>
#include <string.h>
#include "klsteamside.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    unsigned char e[16]; klss_peer p; int used, got, n;
    unsigned long now, last;

    /* version order: 005 first, 004 second, nothing else */
    CHECK(KLSS_NVER == 2);
    CHECK(!strcmp(klss_ver(0), "SteamNetworking005"));
    CHECK(!strcmp(klss_ver(1), "SteamNetworking004"));
    CHECK(klss_ver(2) == 0 && klss_ver(-1) == 0);
    CHECK(KLSS_GETNET_VOFF == 0x44 && KLSS_GETNET_VOFF / 4 == 17);

    /* peer entry: id u64 at +1 (unaligned), byte +9 */
    memset(e, 0xEE, sizeof e);
    e[0] = 0x01;
    e[1] = 0x78; e[2] = 0x56; e[3] = 0x34; e[4] = 0x12; e[5] = 0x01; e[6] = 0x00; e[7] = 0x10; e[8] = 0x01;
    e[9] = 1;
    CHECK(klss_peer_parse(e, &p));
    CHECK(p.id_lo == 0x12345678ul && p.id_hi == 0x01100001ul && p.flag9 == 1);
    e[9] = 0; CHECK(klss_peer_parse(e, &p) && p.flag9 == 0);
    memset(e, 0, sizeof e); CHECK(!klss_peer_parse(e, &p));         /* empty slot */
    CHECK(!klss_peer_parse(0, &p) && !klss_peer_parse(e, 0));

    /* table sanity */
    CHECK(klss_table_ok(0x1000, 1) && klss_table_ok(0x1000, 4096));
    CHECK(!klss_table_ok(0, 1) && !klss_table_ok(0x1000, 0) && !klss_table_ok(0x1000, 4097));

    /* budget: first dump at once, then one a minute, 20 lines a session, wrap-safe clock */
    used = 0; last = 0;
    got = klss_dump_budget(1000, 0, 0, used, 5); CHECK(got == 5); used += got; last = 1000;
    CHECK(klss_dump_budget(1000 + 59999ul, last, 1, used, 5) == 0);
    CHECK(klss_dump_budget(1000 + 60000ul, last, 1, used, 5) == 5);
    CHECK(klss_dump_budget(1000, 0, 0, 18, 5) == 2);               /* clipped to what is left */
    CHECK(klss_dump_budget(1000, 0, 0, 20, 5) == 0 && klss_dump_budget(1000, 0, 0, 25, 5) == 0);
    CHECK(klss_dump_budget(1000, 0, 0, 0, 0) == 0);
    last = 0xFFFFFF00ul; now = 0x00000100ul;                        /* GetTickCount wrap: 0x200 ms elapsed */
    CHECK(klss_dump_budget(now, last, 1, 0, 3) == 0);
    now = last + 60000ul; CHECK(klss_dump_budget(now, last, 1, 0, 3) == 3);
    /* simulate a 30-minute session with 4 lines a dump: stops at 20 lines (5 dumps) */
    used = 0; last = 0; n = 0;
    for (now = 0; now <= 1800000ul; now += 1000ul) {
        got = klss_dump_budget(now, last, n > 0, used, 4);
        if (got) { used += got; last = now; n++; }
    }
    CHECK(used == 20 && n == 5);

    printf("%d checks, %d failed\n%s\n", checks, fails, fails ? "FAIL" : "ALL PASS");
    return fails ? 1 : 0;
}
