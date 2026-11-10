/* klbotglass_test.c - off-game checks of klbotglass_logic.h. Build: cl /nologo /W3 klbotglass_test.c   (or gcc -m32) */
#include <stdio.h>
#include <string.h>
#include "klbotglass_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    struct klbg_pane p[2] = { { 23182, 970, 524, 2566, 0 }, { 24258, 1435, 519, 1670, 0 } };
    struct klbg_cfg c = { 250.0f, 30.0f, 1500, 1 };
    struct klbg_bot b; int rh[2] = { 0, 0 }; unsigned t;
    memset(&b, 0, sizeof b);
    b.x = 5000; b.z = 5000;
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 1000) == -1);                   /* far away */
    b.x = 1100; b.z = 2566;                                              /* 130 cm from pane 0, standing still */
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 2000) == -1);                   /* dwell starts */
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 3000) == -1);
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 3500) == 0);                    /* 1500 ms blocked -> pane 0 */
    p[0].broken = 1;
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 4000) == -1);                   /* broken never again */
    memset(&b, 0, sizeof b); b.x = 1100; b.z = 2566;                     /* walking past fast: never */
    for (t = 1000; t < 20000; t += 250) CHECK(klbg_step(&b, p, 2, &c, 300.0f, rh, t) == -1);
    memset(&b, 0, sizeof b); b.x = 1435; b.z = 1700; rh[1] = 1;          /* route leg runs through pane 1: at once */
    p[0].broken = 0;
    CHECK(klbg_step(&b, p, 2, &c, 300.0f, rh, 500) == 1);
    memset(&b, 0, sizeof b); b.x = 1100; b.z = 2566; rh[1] = 0;          /* leaving the range resets the dwell */
    klbg_step(&b, p, 2, &c, 0, rh, 1000); b.x = 3000; klbg_step(&b, p, 2, &c, 0, rh, 1500);
    b.x = 1100; CHECK(klbg_step(&b, p, 2, &c, 0, rh, 2000) == -1);       /* new dwell from 2000 */
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 3400) == -1);
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 3500) == 0);
    memset(&b, 0, sizeof b); b.x = 1100; b.z = 2566;                     /* now == 0 start still arms */
    CHECK(klbg_step(&b, p, 2, &c, 0, rh, 0) == -1 && b.t_near[0] == 1);
    { int fc[2] = { 0, 0 };                                              /* not facing: dwell runs, nothing fires; facing at once after */
      memset(&b, 0, sizeof b); b.x = 1100; b.z = 2566;
      CHECK(klbg_step_f(&b, p, 2, &c, 0, rh, fc, 1000) == -1);
      CHECK(klbg_step_f(&b, p, 2, &c, 0, rh, fc, 5000) == -1 && b.t_near[0] == 1000);
      fc[0] = 1; CHECK(klbg_step_f(&b, p, 2, &c, 0, rh, fc, 5100) == 0);
      CHECK(klbg_step_f(&b, p, 2, &c, 0, rh, 0, 5200) == 0); }
    printf("klbotglass_test: %d checks, %d fail\n", checks, fails); return fails != 0;
}
