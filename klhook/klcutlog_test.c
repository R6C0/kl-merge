/* klcutlog_test.c - OFF-GAME check of klcutlog_logic.h (rate limit, signal edges, actor delta, act/exec line text; the game reads are klcutlog.c's, NOT run here).
 *   cl /nologo /W4 klcutlog_test.c */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "klcutlog_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    kcut_rl r; kcut_sig a, b; kcut_actor x, y; char o[400], e[200]; unsigned inv[12]; int i, say = 0, cap = 0, skip = 0;

    /* clamps */
    CHECK(kcut_clamp_max(0) == 20); CHECK(kcut_clamp_max(600) == 600); CHECK(kcut_clamp_max(99999) == 20000); CHECK(kcut_clamp_max(-5) == 20);
    CHECK(kcut_clamp_rate(0) == 1); CHECK(kcut_clamp_rate(25) == 25); CHECK(kcut_clamp_rate(1000) == 200);

    /* rate limit: 3 per second */
    kcut_rl_init(&r, 600, 3);
    CHECK(kcut_rl_take(&r, 1000) == KCUT_SAY); CHECK(kcut_rl_take(&r, 1100) == KCUT_SAY); CHECK(kcut_rl_take(&r, 1200) == KCUT_SAY);
    CHECK(kcut_rl_take(&r, 1300) == KCUT_SKIP); CHECK(kcut_rl_take(&r, 1999) == KCUT_SKIP); CHECK(r.skipped == 2);
    CHECK(kcut_rl_take(&r, 2000) == KCUT_SAY);                       /* a new second */
    CHECK(kcut_rl_take(&r, 2000u + 5000u) == KCUT_SAY);
    /* tick counter wrap: 0xfffffff0 -> 0x00000100 is 0x110 ms later, still the same second */
    kcut_rl_init(&r, 600, 1);
    CHECK(kcut_rl_take(&r, 0xfffffff0u) == KCUT_SAY); CHECK(kcut_rl_take(&r, 0x100u) == KCUT_SKIP); CHECK(kcut_rl_take(&r, 0xfffffff0u + 1000u) == KCUT_SAY);
    /* per-level cap: 20 lines (the lowest allowed), one CAP notice, then silent; a new level resets */
    kcut_rl_init(&r, 20, 200);
    for (i = 0; i < 100; i++) { int t = kcut_rl_take(&r, 5000u + (unsigned)i); if (t == KCUT_SAY) say++; else if (t == KCUT_CAP) cap++; else skip++; }
    CHECK(say == 20); CHECK(cap == 1); CHECK(skip == 79); CHECK(r.count == 20);
    kcut_rl_level(&r);
    CHECK(kcut_rl_take(&r, 9000) == KCUT_SAY); CHECK(r.count == 1); CHECK(r.skipped == 0);
    CHECK(r.maxLines == 20 && r.perSec == 200);                      /* limits kept over a level change */

    /* the bound: never more than max lines however long it runs */
    kcut_rl_init(&r, 50, 200); say = 0;
    for (i = 0; i < 100000; i++) if (kcut_rl_take(&r, (unsigned)i * 7u) == KCUT_SAY) say++;
    CHECK(say == 50);

    /* safe copy / path test */
    CHECK(kcut_safe_copy(e, 8, (const unsigned char *)"ab\x01" "cd", 5) == 5); CHECK(!strcmp(e, "ab?cd"));
    CHECK(kcut_safe_copy(e, 4, (const unsigned char *)"abcdefg", 7) == 3); CHECK(!strcmp(e, "abc"));
    CHECK(kcut_safe_copy(e, 8, (const unsigned char *)"ab\0cd", 5) == 2);
    CHECK(kcut_safe_copy(e, 0, (const unsigned char *)"x", 1) == 0);
    CHECK(kcut_looks_like_path((const unsigned char *)"/Gesture/Unarmed/Wave\0", 22));
    CHECK(!kcut_looks_like_path((const unsigned char *)"Gesture/x\0\0\0\0", 12)); CHECK(!kcut_looks_like_path((const unsigned char *)"/ab\0\0\0\0\0", 8));
    CHECK(!kcut_looks_like_path((const unsigned char *)"/Gest\x03ure/xx", 12)); CHECK(!kcut_looks_like_path((const unsigned char *)"/Gesturexxxx", 12));   /* no NUL inside n */

    /* signal edges: only edge signals count, the GS counter is context */
    memset(&a, 0, sizeof a); b = a;
    CHECK(kcut_sig_edges(&a, &b, e, sizeof e) == 0); CHECK(e[0] == 0);
    b.v[KCUT_S_GS] = 77;
    CHECK(kcut_sig_edges(&a, &b, e, sizeof e) == 0);
    b.v[KCUT_S_BLK28] = 1; b.v[KCUT_S_CAMVT] = 0xbb76a4;
    CHECK(kcut_sig_edges(&a, &b, e, sizeof e) == 2); CHECK(!strcmp(e, "blk2728 0>1, camvt 0>bb76a4"));
    CHECK(kcut_sig_edges(&a, &b, e, 12) == 2); CHECK(strlen(e) <= 11);          /* a short buffer truncates, never overruns */
    kcut_sig_row(&b, o, sizeof o);
    CHECK(strstr(o, "blk2728=1") && strstr(o, "gs=4d") && strstr(o, "camvt=bb76a4") && !strchr(o, '\n'));
    kcut_sig_row(&b, e, 10); CHECK(strlen(e) <= 9);

    /* actor state */
    memset(&x, 0, sizeof x); y = x; x.body = y.body = 0x1000;
    CHECK(!kcut_holstered(&x)); CHECK(!kcut_actor_changed(&x, &y));
    y.bbc = 0x100;
    CHECK(kcut_holstered(&y)); CHECK(kcut_actor_changed(&x, &y));
    y.bbc = 0x300; CHECK(kcut_holstered(&y)); y.bbc = 0x200; CHECK(!kcut_holstered(&y));
    y = x; y.hand = 2; CHECK(kcut_actor_changed(&x, &y)); y = x; y.wpn = 0x5000; CHECK(kcut_actor_changed(&x, &y));
    x.bbc = 0; y = x; y.bbc = 0x100; kcut_fmt_actor_delta(e, sizeof e, &x, &y);
    CHECK(!strcmp(e, "bit100 0>1 bbc 00000000>00000100 hand 0>0 wpn 00000000>00000000"));

    /* hand pick (klauto's rule) */
    memset(inv, 0, sizeof inv);
    inv[0 * 4 + 0] = 1; inv[0 * 4 + 2] = 0xaaaa; inv[1 * 4 + 0] = 2; inv[1 * 4 + 2] = 0xbbbb; inv[2 * 4 + 0] = 5; inv[2 * 4 + 2] = 0xcccc;
    CHECK(kcut_hand_pick(0, 0, inv, 3) == 0); CHECK(kcut_hand_pick(64, 0, inv, 3) == 0); CHECK(kcut_hand_pick(1, 0, inv, 3) == 0xbbbb);
    CHECK(kcut_hand_pick(2, 0, inv, 3) == 0xcccc); CHECK(kcut_hand_pick(3, 0, inv, 3) == 0);
    CHECK(kcut_hand_pick(5, 1, inv, 3) == 0xcccc); CHECK(kcut_hand_pick(7, 1, inv, 3) == 0); CHECK(kcut_hand_pick(1, 1, inv, 3) == 0xaaaa);
    CHECK(kcut_hand_pick(1, 1, inv, 300) == 0); CHECK(kcut_hand_pick(1, 1, 0, 3) == 0);

    /* modes */
    CHECK(!strcmp(kcut_mode_name(1), "Holster")); CHECK(!strcmp(kcut_mode_name(2), "Unholster")); CHECK(!strcmp(kcut_mode_name(0), "none")); CHECK(!strcmp(kcut_mode_name(9), "unknown"));

    /* line text: EXEC with and without after, ACT, ACTOR, SIGNAL; every line one line, single-prefixed, no overrun in a small buffer */
    x.bbc = 0; y = x; y.bbc = 0x100;
    kcut_fmt_exec(o, sizeof o, 7, 12345ul, 0x2000, 0x1000, "Kane", 1, 0, &x, &y, 1, 0);
    CHECK(!strcmp(o, "cutlog: EXEC #7 t=12.345s wh=00002000 actor=00001000 'Kane' weaponhdl=1(Holster) prev=0 | bit100 0>1 bbc 00000000>00000100 hand 0>0 wpn 00000000>00000000"));
    kcut_fmt_exec(o, sizeof o, 8, 5ul, 0x2000, 0x1000, "", 2, 1, &y, &y, 0, 1);
    CHECK(strstr(o, "'?'") && strstr(o, "weaponhdl=2(Unholster) prev=1") && strstr(o, "(after: not hooked)") && strstr(o, "[direct]") && strstr(o, "t=0.005s"));
    kcut_fmt_act(o, sizeof o, 9, 61000ul, 0x3000, 0x4000, 12, 0xffff, "/Gesture/Unarmed/Wave_01", 0, 0x1000, "Lynch", &x, &x, 1);
    CHECK(strstr(o, "animid=-1") && strstr(o, "clip='/Gesture/Unarmed/Wave_01'") && strstr(o, "weaponhdl=0(none)") && strstr(o, "t=61.000s") && strstr(o, "'Lynch'"));
    kcut_fmt_act(o, sizeof o, 9, 1ul, 0x3000, 0x4000, 12, 5, 0, 0, 0, 0, &x, &x, 0);
    CHECK(strstr(o, "clip='?'") && strstr(o, "actor=00000000 '?'"));
    kcut_fmt_actor_edge(o, sizeof o, 3, 2500ul, 0x1000, "Kane", 1, &x, &y, "player=1 blk2728=1");
    CHECK(strstr(o, "ACTOR #3 t=2.500s player 00001000 'Kane' bit100 0>1") && strstr(o, "| player=1 blk2728=1"));
    kcut_fmt_sig_edge(o, sizeof o, 4, 90ul, "blk2728 0>1", "player=1");
    CHECK(!strcmp(o, "cutlog: SIGNAL #4 t=0.090s blk2728 0>1 | player=1"));
    memset(o, 'Z', sizeof o);
    kcut_fmt_act(o, 40, 9, 61000ul, 0x3000, 0x4000, 12, 5, "/Gesture/Unarmed/Wave_01", 1, 0x1000, "Lynch", &x, &y, 1);
    CHECK(strlen(o) == 39); CHECK(o[40] == 'Z');

    printf("klcutlog_test: %d checks, %d fails\n", checks, fails);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails ? 1 : 0;
}
