/* klcamppick_test.c - pure-C test of klcamppick_logic.h. cl /nologo klcamppick_test.c ; run. */
#include <stdio.h>
#include "klcamppick_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    klcp_state s; int i; const char *r; char nm[16];
    CHECK(klcp_go_index("KLCampGo01") == 1 && klcp_go_index("KLCampGo16") == 16 && klcp_go_index("KLCampGo09") == 9);
    CHECK(!klcp_go_index("KLCampGo00") && !klcp_go_index("KLCampGo17") && !klcp_go_index("KLCampGo1") && !klcp_go_index("KLCampGo001") && !klcp_go_index("KLCampPick") && !klcp_go_index(""));
    CHECK(!klcp_go_index("klcampgo01") && !klcp_go_index("HeistPlayMenu2") && !klcp_go_index("KLCampGo1x"));
    for (i = 0; i < KLCP_N; i++) { klcp_go_name(i, nm); CHECK(klcp_go_index(nm) == i + 1); CHECK(klcp_id[i][0] == 'M' && klcp_name[i][0] && strlen(klcp_name[i]) <= 20); }
    CHECK(!strcmp(klcp_id[3], "M03B") && !strcmp(klcp_id[15], "M14") && !strcmp(klcp_name[8], "Retomoto Tower"));
    memset(&s, 0, sizeof s);
    CHECK(!klcp_step(&s, "MainMenu"));
    CHECK(!klcp_step(&s, "KLCampPick"));
    r = klcp_step(&s, "KLCampGo10"); CHECK(r && !strcmp(r, "M09B"));
    CHECK(!klcp_step(&s, "KLCampGo10"));                      /* once while the window stays */
    CHECK(!klcp_step(&s, "KLCampGo11"));                      /* still armed: a different go window without a gap does not start */
    CHECK(!klcp_step(&s, "KLCampPick"));                      /* back on the list: re-armed */
    r = klcp_step(&s, "KLCampGo01"); CHECK(r && !strcmp(r, "M01"));
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails ? 1 : 0;
}
