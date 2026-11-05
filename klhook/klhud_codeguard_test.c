/* klhud_codeguard_test.c - off-game checks of klhud_codeguard_logic.h. Build: cl /nologo /W3 klhud_codeguard_test.c */
#include <stdio.h>
#include "klhud_codeguard_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    static const unsigned char known[10] = { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00 };
    unsigned char jmp[10] = { 0xe9, 0x12, 0x34, 0x56, 0x00, 0x0d, 0x90, 0xff, 0xe0, 0x00 };
    unsigned char other[10] = { 0xcc, 0x44, 0x24, 0x04, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00 };
    CHECK(klcg_check(known, known, 10, 0) == KLCG_SAME);
    CHECK(klcg_check(known, known, 10, 1) == KLCG_SAME);
    CHECK(klcg_check(jmp, known, 10, 0) == KLCG_REFUSE);       /* default: the shipped behaviour, a detour is refused */
    CHECK(klcg_check(jmp, known, 10, 1) == KLCG_JMP);
    CHECK(klcg_check(other, known, 10, 1) == KLCG_REFUSE);     /* anything but E9 stays refused */
    CHECK(klcg_check(jmp, known, 4, 1) == KLCG_REFUSE);        /* too short to hold a jmp rel32 */
    CHECK(klcg_check(jmp, known, 0, 1) == KLCG_REFUSE);
    printf("%s: %d checks, %d fails\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
