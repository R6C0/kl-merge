/* klreverbbox_test.c - off-game checks of klreverbbox_logic.h. Build: cl /nologo /W3 klreverbbox_test.c */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "klreverbbox_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static const char *TABLE =
    "; KLReverbBoxes.ini test\r\n"
    "[F01\\F01_Main]\r\n"
    "box 100 0 200  50 20 30  1 0 0 0 1 0 0 0 1  438992 60.0 ; Platform\r\n"
    "box 100 0 200  400 400 400  1 0 0 0 1 0 0 0 1  439488 30 ; outer street\r\n"
    "  box\t0 0 0 10 10 10 1 0 0 0 1 0 0 0 1 7 1.5\r\n"
    "box 1 2 3 only three\r\n"
    "boxes=3\r\n"
    "# the second map\r\n"
    "[dm02]\r\n"
    "[ dm05a ]\n"
    "box 0 0 0 100 10 100  0 0 1 0 1 0 -1 0 0  42 80\n";

int main(void)
{
    struct klrb_box b[8], one; char key[40]; int found, bad, n, i; float p[3]; struct klrb_st st;

    /* line parser */
    CHECK(klrb_parse_line("box 1 2 3 4 5 6 1 0 0 0 1 0 0 0 1 99 12.5 ; name", &one) == 1);
    CHECK(one.c[1] == 2 && one.h[2] == 6 && one.q[0] == 1 && one.q[4] == 1 && one.snd == 99 && one.prio == 12.5f);
    CHECK(klrb_parse_line("; box 1 2 3", &one) == 0); CHECK(klrb_parse_line("[x]", &one) == 0); CHECK(klrb_parse_line("boxes=2", &one) == 0); CHECK(klrb_parse_line("", &one) == 0);
    CHECK(klrb_parse_line("box 1 2 3", &one) == -1);                                          /* too few numbers */
    CHECK(klrb_parse_line("box 1 2 3 -4 5 6 1 0 0 0 1 0 0 0 1 99 12.5", &one) == -1);        /* negative half extent */
    CHECK(klrb_parse_line("box 1 2 3 4 5 6 1 0 0 0 1 0 0 0 1 -5 12.5", &one) == -1);         /* negative snd */
    CHECK(klrb_parse_line("box 1 2 3 4 5 6 1 0 0 0 1 0 0 0 1 x 12.5", &one) == -1);

    /* sections */
    CHECK(klrb_section("[F01\\F01_Main]\r", key, sizeof key) && !strcmp(key, "f01\\f01_main"));
    CHECK(klrb_section("  [ dm05a ]", key, sizeof key) && !strcmp(key, "dm05a"));
    CHECK(!klrb_section("box 1", key, sizeof key)); CHECK(!klrb_section("[unterminated", key, sizeof key));

    /* load: any case of the key, bad lines counted, other sections not mixed in */
    n = klrb_load(TABLE, "f01\\F01_MAIN", b, 8, &found, &bad);
    CHECK(n == 3 && found == 1 && bad == 1);
    CHECK(b[0].snd == 438992 && b[0].prio == 60.0f && b[1].snd == 439488 && b[2].snd == 7 && b[2].prio == 1.5f);
    n = klrb_load(TABLE, "dm02", b, 8, &found, &bad); CHECK(n == 0 && found == 1 && bad == 0);   /* a known map with no box */
    n = klrb_load(TABLE, "dm09", b, 8, &found, &bad); CHECK(n == 0 && found == 0);
    n = klrb_load(TABLE, "f01\\f01_main", b, 2, &found, &bad); CHECK(n == 2);                       /* cap */
    n = klrb_load("", "x", b, 8, &found, &bad); CHECK(n == 0 && found == 0);
    n = klrb_load("[a]\nbox 0 0 0 1 1 1 1 0 0 0 1 0 0 0 1 5 5", "a", b, 8, &found, &bad); CHECK(n == 1);   /* no final newline */
    { char longl[900]; memset(longl, 'x', 899); longl[899] = 0;
      n = klrb_load(longl, "a", b, 8, &found, &bad); CHECK(n == 0);                                 /* an over-long line does not hang or crash */ }

    /* inside: axis aligned, margins */
    n = klrb_load(TABLE, "f01\\f01_main", b, 8, &found, &bad);
    p[0] = 100; p[1] = 0; p[2] = 200; CHECK(klrb_inside(&b[0], p, 0));
    p[0] = 150; CHECK(klrb_inside(&b[0], p, 0));                                                   /* exactly on the face */
    p[0] = 150.5f; CHECK(!klrb_inside(&b[0], p, 0)); CHECK(klrb_inside(&b[0], p, 1.0f)); CHECK(!klrb_inside(&b[0], p, -1.0f));
    p[0] = 100; p[1] = 21; CHECK(!klrb_inside(&b[0], p, 0));
    p[1] = 0; p[2] = 200 - 29; CHECK(klrb_inside(&b[0], p, -0.5f));
    { float nan = (float)sqrt(-1.0); p[0] = nan; p[1] = 0; p[2] = 0; CHECK(!klrb_inside(&b[0], p, 0)); CHECK(!klrb_inside(&b[0], p, 5)); }
    p[0] = 100; p[1] = 0; p[2] = 200; CHECK(klrb_inside(&b[0], p, -1000.0f));                      /* a huge shrink stops at half the extent: the centre stays inside */
    p[0] = 100 + 26; CHECK(!klrb_inside(&b[0], p, -1000.0f));                                      /* ... and 26 > half of 50 */

    /* inside: a rotated box (the table's dm05a: local x = world -z, local z = world x ... q rows (0 0 1)(0 1 0)(-1 0 0)) */
    n = klrb_load(TABLE, "dm05a", b, 8, &found, &bad); CHECK(n == 1 && found == 1);
    /* world (z=90) -> local x = 90 (half 100: in); world (x=90) -> local z = -90?? q row 2 = (-1 0 0): local z = -x, half 100: in; world (x=0,z=150) -> local x=150: out */
    p[0] = 0; p[1] = 0; p[2] = 90; CHECK(klrb_inside(&b[0], p, 0));
    p[0] = 90; p[2] = 0; CHECK(klrb_inside(&b[0], p, 0));
    p[0] = 0; p[2] = 150; CHECK(!klrb_inside(&b[0], p, 0));
    p[0] = 0; p[1] = 11; p[2] = 0; CHECK(!klrb_inside(&b[0], p, 0));                               /* half y is only 10 */
    { struct klrb_box r; memset(&r, 0, sizeof r);                                                  /* 45 degrees about y: a long thin box along the diagonal */
      r.h[0] = 100; r.h[1] = 10; r.h[2] = 10; r.q[0] = 0.70710678f; r.q[2] = -0.70710678f; r.q[4] = 1; r.q[6] = 0.70710678f; r.q[8] = 0.70710678f;   /* local x = (dx - dz)/sqrt2 ... see below */
      p[0] = 50; p[1] = 0; p[2] = -50; CHECK(klrb_inside(&r, p, 0));                               /* local x = 70.7, local z = 0 */
      p[0] = 50; p[2] = 50; CHECK(!klrb_inside(&r, p, 0));                                         /* local x = 0, local z = 70.7 > 10 */
    }

    /* update: enter, leave, margin hysteresis, hold, nesting */
    n = klrb_load(TABLE, "f01\\f01_main", b, 8, &found, &bad); CHECK(n == 3);
    klrb_reset(&st);
    p[0] = 5000; p[1] = 5000; p[2] = 5000; CHECK(klrb_update(&st, b, 2, p, 1000, 20, 100, 0) == -1);
    p[0] = 100 + 200; p[1] = 0; p[2] = 200; CHECK(klrb_update(&st, b, 2, p, 1100, 20, 100, 0) == 1);          /* only the big street box */
    p[0] = 100; CHECK(klrb_update(&st, b, 2, p, 1200, 20, 100, 0) == 0);                                     /* nested: Platform (60) beats street (30) */
    /* edge of Platform (x = 150) with margin 20: enters inside 130, leaves outside 170; between, it keeps whatever it was */
    klrb_reset(&st);
    p[0] = 160; p[1] = 0; p[2] = 200; CHECK(klrb_update(&st, b, 2, p, 1000, 20, 0, 0) == 1);                 /* in the dead band, not yet in: street */
    p[0] = 125; CHECK(klrb_update(&st, b, 2, p, 1010, 20, 0, 0) == 0);                                       /* inside the shrunk box: Platform */
    p[0] = 160; CHECK(klrb_update(&st, b, 2, p, 1020, 20, 0, 0) == 0);                                       /* dead band, was in: stays */
    p[0] = 168; CHECK(klrb_update(&st, b, 2, p, 1030, 20, 0, 0) == 0);
    p[0] = 171; CHECK(klrb_update(&st, b, 2, p, 1040, 20, 0, 0) == 1);                                       /* outside the widened box: leaves */
    /* a 100 ms hold: a toggle right after a toggle is held back */
    klrb_reset(&st);
    p[0] = 100; CHECK(klrb_update(&st, b, 2, p, 5000, 20, 100, 0) == 0);                                     /* first look is never held */
    p[0] = 400; CHECK(klrb_update(&st, b, 2, p, 5050, 20, 100, 0) == 0);                                     /* would leave Platform, held 50 ms < 100 */
    CHECK(klrb_update(&st, b, 2, p, 5120, 20, 100, 0) == 1);                                                 /* 120 ms: leaves */
    /* usable[]: a box without an effect is never picked */
    { unsigned char u[3] = { 0, 1, 1 };
      klrb_reset(&st); p[0] = 100;
      CHECK(klrb_update(&st, b, 2, p, 9000, 20, 100, u) == 1); }
    /* equal priority: the current winner stays; a new one is the smaller box */
    { struct klrb_box e[3]; memset(e, 0, sizeof e);
      for (i = 0; i < 3; i++) { e[i].q[0] = e[i].q[4] = e[i].q[8] = 1; e[i].prio = 50; e[i].h[0] = e[i].h[1] = e[i].h[2] = 100.0f * (float)(3 - i); }   /* 0 biggest ... 2 smallest */
      klrb_reset(&st); p[0] = p[1] = p[2] = 0;
      CHECK(klrb_update(&st, e, 3, p, 100, 0, 0, 0) == 2);                                                 /* the smallest of equals */
      e[2].prio = 50; st.cur = 0; CHECK(klrb_update(&st, e, 3, p, 200, 0, 0, 0) == 0);                     /* the current winner stays on a tie */
      e[1].prio = 51; CHECK(klrb_update(&st, e, 3, p, 300, 0, 0, 0) == 1);                                 /* a higher priority takes over */
      CHECK(klrb_update(&st, e, 0, p, 400, 0, 0, 0) == -1);                                                /* no boxes */ }
    /* map id from the archive path */
    { char id[40];
      CHECK(klrb_map_id("C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Maps\\DM02\\F02_Main.zip", id, sizeof id) && !strcmp(id, "dm02"));
      CHECK(klrb_map_id("c:/x/KLExpansion/MAPS/DD10/F07_Main.zip", id, sizeof id) && !strcmp(id, "dd10"));
      CHECK(!klrb_map_id("C:\\Steam\\Dog Days\\Scenes\\Locations\\F02\\F02_Main.zip", id, sizeof id) && id[0] == 0);
      CHECK(!klrb_map_id("F02_Main.zip", id, sizeof id)); CHECK(!klrb_map_id("a\\Maps\\F02_Main.zip", id, sizeof id));
      CHECK(!klrb_map_id("x\\Maps\\toolongfolder\\F02_Main.zip", id, 8)); }
    /* ear height: a room box whose floor is the floor (Dead Men .rmi, RB_DM02) holds the raised point, never the feet, once the enter margin shrinks it */
    { struct klrb_box r; float f[3] = { 1694, 1002, -2967 }, ear[3];
      memset(&r, 0, sizeof r); r.q[0] = r.q[4] = r.q[8] = 1; r.c[0] = 0; r.c[1] = 1250; r.c[2] = -2500; r.h[0] = 2000; r.h[1] = 250; r.h[2] = 500;   /* dm02 KR014 Atrium_301a */
      CHECK(!klrb_inside(&r, f, -30.0f));
      klrb_ear(f, 100.0f, ear); CHECK(ear[0] == 1694 && ear[1] == 1102 && ear[2] == -2967); CHECK(klrb_inside(&r, ear, -30.0f));
      klrb_ear(f, 100.0f, f); CHECK(f[1] == 1102 && f[0] == 1694); }                                          /* in place, as klecho.c calls it */
    /* keys are never a pointer */
    CHECK(KLRB_KEY + KLRB_MAX < 0x10000u);
    printf("%s: %d checks, %d fails\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
