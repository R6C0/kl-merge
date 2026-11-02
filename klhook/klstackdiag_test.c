/* klstackdiag_test.c - off-game harness for klstackdiag_logic.h. No windows.h.
   Build: cl /nologo /W3 klstackdiag_test.c /Fe:klstackdiag_test.exe     Run: klstackdiag_test.exe (exit 0 = all pass) */
#include <string.h>
#include "klstackdiag_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    char b[96];
    ksd_fmt(b, sizeof b, 1, 40000, 0, 1, 0);
    CHECK(strcmp(b, "[+0x34]=40000 state 0 armed 1 hidden 0") == 0, "fmt: %s", b);
    ksd_fmt(b, sizeof b, 1, -1, -1, -1, -1);
    CHECK(strcmp(b, "[+0x34]=-1 state -1 armed -1 hidden -1") == 0, "fmt unreadable: %s", b);
    ksd_fmt(b, sizeof b, 0, 0, 0, 0, 1);
    CHECK(strstr(b, "NOT the money vtable") != 0, "fmt vtable: %s", b);
    ksd_fmt(b, 12, 1, 123456, 2, 1, 1);
    CHECK(strlen(b) == 11, "truncated and terminated: %d", (int)strlen(b));
    CHECK(ksd_scan_drop(0, 2, 1) == 0, "off: never");
    CHECK(ksd_scan_drop(1, 0, 0) == 0 && ksd_scan_drop(1, 1, 0) == 0 && ksd_scan_drop(1, 4, 0) == 0, "states 0/1/4: kept");
    CHECK(ksd_scan_drop(1, 2, 0) == 1 && ksd_scan_drop(1, 3, 0) == 1, "states 2/3: dropped");
    CHECK(ksd_scan_drop(1, 0, 1) == 1, "hidden: dropped");
    CHECK(ksd_scan_drop(1, -1, -1) == 0, "unreadable: kept");
    printf("klstackdiag_test: %d checks, %d fail\n", checks, fails);
    return fails ? 1 : 0;
}
