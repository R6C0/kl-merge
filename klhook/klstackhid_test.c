/* klstackhid_test.c - off-game harness for klstackhid_logic.h. No windows.h.
   Build: cl /nologo /W3 klstackhid_test.c /Fe:klstackhid_test.exe     Run: klstackhid_test.exe (exit 0 = all pass) */
#include <string.h>
#include "klstackdiag_logic.h"
#include "klstackhid_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    CHECK(ksh_clamp_s(-5) == 0 && ksh_clamp_s(0) == 0 && ksh_clamp_s(8) == 8 && ksh_clamp_s(60) == 60 && ksh_clamp_s(61) == 60 && ksh_clamp_s(9999) == 60, "clamp");
    CHECK(ksh_scan_drop(0, 1, 8, 3, 1, 0) == 0, "recheck off: never drops");
    /* Hid key off: identical to ksd_scan_drop */
    CHECK(ksh_scan_drop(1, 0, 8, 0, 1, 0) == 1, "hid key off: state 0 hidden 1 dropped at once (today)");
    CHECK(ksh_scan_drop(1, 0, 8, 2, 0, 0) == 1 && ksh_scan_drop(1, 0, 8, 0, 0, 0) == 0, "hid key off: 2 drops, 0/0 kept");
    /* Hid key on: state 0 + hidden 1 is kept before S s, dropped from S s on */
    CHECK(ksh_scan_drop(1, 1, 8, 0, 1, 0) == 0, "on: 0 s kept");
    CHECK(ksh_scan_drop(1, 1, 8, 0, 1, 7999) == 0, "on: 7.999 s kept");
    CHECK(ksh_scan_drop(1, 1, 8, 0, 1, 8000) == 1, "on: 8 s dropped (still hidden)");
    CHECK(ksh_scan_drop(1, 1, 8, 0, 1, 120000) == 1, "on: late dropped");
    /* state 2/3 always dropped, even early */
    CHECK(ksh_scan_drop(1, 1, 8, 2, 0, 0) == 1 && ksh_scan_drop(1, 1, 8, 3, 0, 0) == 1, "on: state 2/3 dropped early");
    CHECK(ksh_scan_drop(1, 1, 8, 3, 1, 0) == 1, "on: state 3 + hidden dropped early");
    /* other hidden states are not covered by the grace */
    CHECK(ksh_scan_drop(1, 1, 8, 1, 1, 0) == 1, "on: state 1 hidden dropped as before");
    CHECK(ksh_scan_drop(1, 1, 8, -1, 1, 0) == 1, "on: state unreadable + hidden dropped as before");
    CHECK(ksh_scan_drop(1, 1, 8, 0, 0, 0) == 0 && ksh_scan_drop(1, 1, 8, -1, -1, 0) == 0, "on: visible / unreadable kept");
    /* S = 0: no grace; S = 60 clamp; S above 60 behaves as 60 */
    CHECK(ksh_scan_drop(1, 1, 0, 0, 1, 0) == 1, "S 0: no grace");
    CHECK(ksh_scan_drop(1, 1, 99, 0, 1, 59999) == 0 && ksh_scan_drop(1, 1, 99, 0, 1, 60000) == 1, "S 99 = 60");
    printf("klstackhid_test: %d checks, %d fail\n", checks, fails);
    return fails ? 1 : 0;
}
