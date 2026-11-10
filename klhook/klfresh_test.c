/* klfresh_test.c - klfresh_logic.h outside the game (pure logic, no Windows calls).
 *   cl /nologo /W3 klfresh_test.c /Fe:klfresh_test.exe        or      gcc -m32 -Wall klfresh_test.c -o klfresh_test
 * exit code 0 = every check passed. */
#include <stdio.h>
#include <string.h>
#include "klfresh_logic.h"

static int bad;
#define CHECK(c, ...) do { if (!(c)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

static struct klfh_cfg cfg(void) { struct klfh_cfg c = { 1, 2, 0, 200, 2500, 60000, 8 }; return c; }
static struct klfh_in idle(int levels)
{   /* an idle main menu, stable, old process, nothing pending, memory not measured */
    struct klfh_in s; memset(&s, 0, sizeof s);
    s.at_menu = 1; s.menu_ms = 5000; s.up_ms = 600000; s.levels = levels; s.largest_mb = s.free_mb = 0xffffffffu;
    return s;
}

int main(void)
{
    struct klfh_cfg c = cfg(); struct klfh_in s; int last = -1, lv = 0;

    /* the count rule: 2 levels = before the 3rd */
    s = idle(0); CHECK(klfh_decide(&c, &s) == KLFH_NO, "fresh process at the menu must not restart");
    s = idle(1); CHECK(klfh_decide(&c, &s) == KLFH_NO, "after 1 level (limit 2) no restart");
    s = idle(2); CHECK(klfh_decide(&c, &s) == KLFH_LEVELS, "after 2 levels restart");
    s = idle(5); CHECK(klfh_decide(&c, &s) == KLFH_LEVELS, "after 5 levels restart");
    c.every_levels = 1; s = idle(1); CHECK(klfh_decide(&c, &s) == KLFH_LEVELS, "FreshLevels=1: after every match");
    c.every_levels = 0; s = idle(9); CHECK(klfh_decide(&c, &s) == KLFH_NO, "FreshLevels=0: the count rule is off");

    /* the gate: every blocker alone stops a restart that would otherwise happen */
    c = cfg();
    s = idle(3); s.test_run = 1; CHECK(klfh_decide(&c, &s) == KLFH_NO, "scripted run never restarts");
    s = idle(3); s.online = 1; CHECK(klfh_decide(&c, &s) == KLFH_NO, "online session never restarts");
    s = idle(3); s.at_menu = 0; CHECK(klfh_decide(&c, &s) == KLFH_NO, "not at the menu (loading / in a level / shop)");
    s = idle(3); s.start_pending = 1; CHECK(klfh_decide(&c, &s) == KLFH_NO, "StartGame pending");
    s = idle(3); s.menu_ms = 1000; CHECK(klfh_decide(&c, &s) == KLFH_NO, "menu not stable yet");
    s = idle(3); s.up_ms = 30000; CHECK(klfh_decide(&c, &s) == KLFH_NO, "process too young");
    s = idle(3); s.chain = 8; CHECK(klfh_decide(&c, &s) == KLFH_NO, "chain limit reached");
    s = idle(3); s.chain = 7; CHECK(klfh_decide(&c, &s) == KLFH_LEVELS, "chain limit not yet reached");
    c.enable = 0; s = idle(3); CHECK(klfh_decide(&c, &s) == KLFH_NO, "FreshRestart=0");
    c = cfg(); c.max_chain = -1; s = idle(3); s.chain = 999; CHECK(klfh_decide(&c, &s) == KLFH_LEVELS, "FreshMax -1 = no limit");

    /* the memory rules (levels below the count limit) */
    c = cfg(); c.min_piece_mb = 64;
    s = idle(1); s.largest_mb = 24; s.free_mb = 476; CHECK(klfh_decide(&c, &s) == KLFH_PIECE, "piece 24 MB < 64");
    s = idle(1); s.largest_mb = 80; s.free_mb = 476; CHECK(klfh_decide(&c, &s) == KLFH_NO, "piece 80 MB ok");
    s = idle(1); s.largest_mb = 24; s.free_mb = 150; CHECK(klfh_decide(&c, &s) == KLFH_PIECE, "piece rule is checked first");
    c = cfg();
    s = idle(1); s.largest_mb = 24; s.free_mb = 150; CHECK(klfh_decide(&c, &s) == KLFH_FREE, "free 150 MB < 200");
    s = idle(1); s.largest_mb = 24; s.free_mb = 476; CHECK(klfh_decide(&c, &s) == KLFH_NO, "free 476 MB ok (the measured menu)");
    s = idle(0); s.largest_mb = 5; s.free_mb = 50; CHECK(klfh_decide(&c, &s) == KLFH_NO, "a fresh process is never restarted for memory (a restart cannot help)");
    s = idle(1); CHECK(klfh_decide(&c, &s) == KLFH_NO, "memory not measured = no memory rule");

    /* when the walk is worth doing */
    c = cfg(); s = idle(1); CHECK(klfh_needs_walk(&c, &s) == 1, "threshold set, below count: walk");
    s = idle(2); CHECK(klfh_needs_walk(&c, &s) == 0, "count rule already says yes: no walk");
    s = idle(1); s.online = 1; CHECK(klfh_needs_walk(&c, &s) == 0, "gate closed: no walk");
    c.min_free_mb = 0; s = idle(1); CHECK(klfh_needs_walk(&c, &s) == 0, "no threshold: no walk");

    /* the level counter: one count per entry into a level scene */
    CHECK(!klfh_count(&last, -1, &lv) && lv == 0, "unknown scene counts nothing");
    CHECK(!klfh_count(&last, 0, &lv) && lv == 0, "frontend counts nothing");
    CHECK(klfh_count(&last, 1, &lv) && lv == 1, "first level scene counts");
    CHECK(!klfh_count(&last, 1, &lv) && lv == 1, "same level every tick counts once");
    CHECK(!klfh_count(&last, -1, &lv) && last == 1, "a gap between scenes keeps the state");
    CHECK(!klfh_count(&last, 1, &lv) && lv == 1, "level -> gap -> same level: not a second load");
    CHECK(!klfh_count(&last, 0, &lv) && last == 0, "back to the frontend");
    CHECK(klfh_count(&last, 1, &lv) && lv == 2, "second level counts");

    /* the child's wait */
    CHECK(klfh_child_go(1, 1) == 1, "go + parent gone: start");
    CHECK(klfh_child_go(1, 0) == 1, "go: start (the caller still waits for the parent to end)");
    CHECK(klfh_child_go(0, 1) == 0, "parent gone WITHOUT go (player closed the game): the child quits");
    CHECK(klfh_child_go(0, 0) == -1, "nothing yet: keep waiting");

    /* the command line */
    CHECK(klfh_cmd_is_test("\"kl2.exe\" -dx10 -o DefaultScene=Locations/F01/F01_Main.gms -o AutoExit=120"), "autotest command line");
    CHECK(klfh_cmd_is_test("kl2.exe -o AUTOEXIT=5"), "case-insensitive");
    CHECK(klfh_cmd_is_test("kl2.exe -o DisableSplashScreens"), "no-profile run");
    CHECK(!klfh_cmd_is_test("\"kl2.exe\" -dx10"), "a normal launch");
    CHECK(!klfh_cmd_is_test("\"kl2.exe\""), "no arguments");
    CHECK(!klfh_cmd_is_test(0), "null");

    CHECK(!strcmp(klfh_why(KLFH_LEVELS), "enough level loads") && !strcmp(klfh_why(KLFH_NO), "no"), "reason texts");

    printf(bad ? "klfresh_test: %d FAIL\n" : "klfresh_test: all passed\n", bad);
    return bad != 0;
}
