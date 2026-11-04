/* klbrain_test.c - off-game harness for klbrain_logic.h ([Brain] vector insertion order, growth, switches, PuppetOff window). No windows.h.
   Build: cl /nologo /W3 klbrain_test.c /Fe:klbrain_test.exe     Run: klbrain_test.exe (exit 0 = all pass) */
#include <stdio.h>
#include <string.h>
#include "klbrain_logic.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main(void)
{
    kbr_u16 out[16]; int n, v, o[4]; kbr_u32 el[16], succ[4];
    /* orders: Loot is last in each vector, Traitor before Board, vectors C has 8 members */
    CHECK(kbr_ordn[0] == 13 && kbr_ordn[1] == 15 && kbr_ordn[2] == 8, "order sizes %d %d %d", kbr_ordn[0], kbr_ordn[1], kbr_ordn[2]);
    for (v = 0; v < KBR_NVEC; v++) {
        CHECK(kbr_after(v, KBR_F_LOOT, out, 16) == 0, "Loot is last in vector %d", v);
        n = kbr_after(v, KBR_F_TRAITOR, out, 16);
        CHECK(n > 0 && out[0] == KBR_F_BOARD, "Board follows Traitor in vector %d", v);
        CHECK(kbr_after(v, 0x123, out, 16) == 0, "unknown field");
    }
    CHECK(kbr_after(0, KBR_F_BOARD, out, 2) == 2, "cap respected");
    /* insertion index: first element equal to a non-zero successor, else append */
    el[0] = 10; el[1] = 20; el[2] = 30;
    succ[0] = 30; succ[1] = 0;
    CHECK(kbr_insert_index(el, 3, succ, 2) == 2, "before successor");
    succ[0] = 0; succ[1] = 0;
    CHECK(kbr_insert_index(el, 3, succ, 2) == 3, "null successors append");
    succ[0] = 20; succ[1] = 10;
    CHECK(kbr_insert_index(el, 3, succ, 2) == 0, "earliest hit wins");
    CHECK(kbr_insert_index(el, 0, succ, 2) == 0, "empty vector");
    /* vector header plausibility */
    CHECK(kbr_vec_ok(0x1000, 0x1010, 0x1028), "good vector");
    CHECK(kbr_vec_ok(0x1000, 0x1000, 0x1028), "empty vector with reserve");
    CHECK(!kbr_vec_ok(0, 0, 0), "null");
    CHECK(!kbr_vec_ok(0x1002, 0x1010, 0x1028), "misaligned");
    CHECK(!kbr_vec_ok(0x1000, 0x1030, 0x1028), "last past end");
    CHECK(!kbr_vec_ok(0x1000, 0x1000, 0x1000), "no reserve");
    CHECK(!kbr_vec_ok(0x1000, 0x1000, 0x1000 + 4 * 300), "huge");
    /* growth */
    CHECK(kbr_grow_cap(3) == 16, "min 16");
    CHECK(kbr_grow_cap(20) == 40, "double");
    CHECK(kbr_grow_cap(200) == 0, "refuse over 256");
    /* insert */
    el[0] = 1; el[1] = 2; el[2] = 3;
    CHECK(kbr_insert(el, 3, 16, 1, 99) == 4 && el[0] == 1 && el[1] == 99 && el[2] == 2 && el[3] == 3, "insert middle");
    CHECK(kbr_insert(el, 4, 16, 4, 7) == 5 && el[4] == 7, "insert end");
    CHECK(kbr_insert(el, 5, 5, 0, 7) == -1, "full");
    CHECK(kbr_insert(el, 5, 16, 6, 7) == -1, "idx past end");
    CHECK(kbr_insert(el, 5, 16, -1, 7) == -1, "negative idx");
    /* the real ctor order reproduced: vector A with other members, push Traitor, Board, Loot into it */
    {
        kbr_u32 vec[16]; int cnt = 0, idx; kbr_u32 other_after = 777;
        vec[cnt++] = 5; vec[cnt++] = other_after;      /* 5 = an earlier member; 777 = a LATER member (0x5ac) */
        succ[0] = other_after;                         /* successor of Traitor: contains the later member */
        idx = kbr_insert_index(vec, cnt, succ, 1);
        cnt = kbr_insert(vec, cnt, 16, idx, 111);
        CHECK(cnt == 3 && vec[1] == 111 && vec[2] == 777, "Traitor lands before the later member");
        idx = kbr_insert_index(vec, cnt, succ, 0);     /* Loot: no successors -> append */
        cnt = kbr_insert(vec, cnt, 16, idx, 333);
        CHECK(cnt == 4 && vec[3] == 333, "Loot appended");
    }
    /* switches */
    kbr_switches(1, 0, 1, 1, o);
    CHECK(o[0] == 1 && o[1] == 0 && o[2] == 0 && o[3] == 0, "Loot / PuppetOff need Build");
    kbr_switches(0, 1, 0, 1, o);
    CHECK(o[1] == 1 && o[2] == 0 && o[3] == 0, "PuppetOff needs Loot");
    kbr_switches(0, 1, 1, 1, o);
    CHECK(o[1] == 1 && o[2] == 1 && o[3] == 1, "all on");
    kbr_switches(0, 0, 0, 0, o);
    CHECK(!o[0] && !o[1] && !o[2] && !o[3], "all off");
    /* puppet window */
    CHECK(!kbr_puppet_released(0, 1, 1000, 900, 5000), "off");
    CHECK(!kbr_puppet_released(1, 0, 1000, 900, 5000), "not built");
    CHECK(!kbr_puppet_released(1, 1, 1000, 0, 5000), "never nonzero");
    CHECK(kbr_puppet_released(1, 1, 1000, 900, 5000), "recent");
    CHECK(!kbr_puppet_released(1, 1, 9000, 900, 5000), "stale");
    CHECK(kbr_puppet_released(1, 1, 100, 0xfffffff0ul, 5000), "wrap safe");
    /* ---- stage 2 / 3 ---- */
    {
        int sw[KBR_NSW], depth = 0, out_i = 0, i; float tm, d2[8]; unsigned long ob[8], res[5];
        kbr_switches2(1, 0, 1, 1, 1, 1, 1, 1, 1, sw);
        CHECK(sw[KBR_S_PROBE] && !sw[KBR_S_BUILD] && !sw[KBR_S_LOOT] && !sw[KBR_S_BRIDGE] && !sw[KBR_S_BOARD] && !sw[KBR_S_TRAITOR] && !sw[KBR_S_PUPPET] && !sw[KBR_S_BOARDREAL] && !sw[KBR_S_COPS], "no Build: only Probe");
        kbr_switches2(0, 1, 0, 1, 0, 1, 1, 1, 1, sw);
        CHECK(sw[KBR_S_BUILD] && !sw[KBR_S_LOOT] && !sw[KBR_S_BRIDGE] && !sw[KBR_S_TRAITOR] && !sw[KBR_S_PUPPET] && !sw[KBR_S_COPS], "Bridge/Traitor/Puppet/Cops need Loot");
        kbr_switches2(0, 1, 1, 0, 1, 1, 1, 1, 1, sw);
        CHECK(sw[KBR_S_LOOT] && !sw[KBR_S_BRIDGE] && !sw[KBR_S_TRAITOR] && !sw[KBR_S_PUPPET] && !sw[KBR_S_COPS] && sw[KBR_S_BOARD] && sw[KBR_S_BOARDREAL], "no Bridge: Traitor/Puppet/Cops off, Board stays");
        kbr_switches2(0, 1, 1, 1, 0, 1, 1, 1, 1, sw);
        CHECK(sw[KBR_S_BRIDGE] && sw[KBR_S_TRAITOR] && sw[KBR_S_PUPPET] && sw[KBR_S_COPS] && !sw[KBR_S_BOARD] && !sw[KBR_S_BOARDREAL], "BoardReal needs Board");
        kbr_switches2(0, 0, 0, 0, 0, 0, 0, 0, 0, sw);
        { int any = 0; for (i = 0; i < KBR_NSW; i++) any |= sw[i]; CHECK(!any, "all off"); }
        /* frame depth */
        CHECK(kbr_frame_enter(&depth) == 1 && kbr_frame_enter(&depth) == 0 && depth == 2, "outermost then nested");
        CHECK(kbr_frame_leave(&depth) == 0 && kbr_frame_leave(&depth) == 1 && depth == 0 && kbr_frame_leave(&depth) == 1 && depth == 0, "leave never goes negative");
        /* sync staleness incl. wrap */
        CHECK(kbr_sync_stale(1000, 0, 250) && !kbr_sync_stale(1100, 1000, 250) && kbr_sync_stale(1300, 1000, 250) && !kbr_sync_stale(100, 0xfffffff0ul, 250), "stale: never / fresh / old / wrap");
        /* money, level, board state */
        CHECK(kbr_money_row(-1) == 0 && kbr_money_row(5000) == 5000 && kbr_money_row(2100000000L) == 2000000000L, "money row");
        CHECK(kbr_level_clamp(0) == 1 && kbr_level_clamp(6) == 6 && kbr_level_clamp(99) == 11 && kbr_level_clamp(-3) == 1, "level clamp");
        CHECK(!kbr_board_state_ok(0) && !kbr_board_state_ok(2) && kbr_board_state_ok(3) && kbr_board_state_ok(4) && !kbr_board_state_ok(5), "board states");
        /* grab_ok */
        CHECK(kbr_grab_ok(0, 0x19, 1, 1, 0, 100, 1, 1), "grab ok");
        CHECK(!kbr_grab_ok(1, 0x19, 1, 1, 0, 100, 1, 1), "already grabbing");
        CHECK(!kbr_grab_ok(0, 0x1a, 1, 1, 0, 100, 1, 1), "not in round");
        CHECK(!kbr_grab_ok(0, 0x19, 2, 1, 0, 100, 1, 1) && !kbr_grab_ok(0, 0x19, 3, 1, 0, 100, 1, 1), "stack state 2 / 3");
        CHECK(!kbr_grab_ok(0, 0x19, 1, 0, 0, 100, 1, 1) && !kbr_grab_ok(0, 0x19, 1, 1, 1, 100, 1, 1) && !kbr_grab_ok(0, 0x19, 1, 1, 0, 0, 1, 1) && !kbr_grab_ok(0, 0x19, 1, 1, 0, 100, 0, 1) && !kbr_grab_ok(0, 0x19, 1, 1, 0, 100, 1, 0), "inactive / hidden / empty / bit taken / dead");
        /* grab_step */
        tm = 1.0f; out_i = 0;
        CHECK(kbr_grab_step(&tm, 0.4f, 1, &out_i, 1, 0, 1) == KBR_G_KEEP && tm > 0.59f && tm < 0.61f, "timer runs");
        CHECK(kbr_grab_step(&tm, 0.7f, 1, &out_i, 1, 0, 1) == KBR_G_PAY && tm <= 0.0f, "pay at zero");
        tm = 1.0f; out_i = 0;
        CHECK(kbr_grab_step(&tm, 0.4f, 0, &out_i, 1, 0, 1) == KBR_G_KEEP && tm == 1.0f, "one tick outside: grace, timer frozen");
        CHECK(kbr_grab_step(&tm, 0.4f, 1, &out_i, 1, 0, 1) == KBR_G_KEEP && out_i == 0, "back inside resets");
        CHECK(kbr_grab_step(&tm, 0.1f, 0, &out_i, 1, 0, 1) == KBR_G_KEEP && kbr_grab_step(&tm, 0.1f, 0, &out_i, 1, 0, 1) == KBR_G_ABORT, "two ticks outside: abort");
        tm = 1.0f; out_i = 0;
        CHECK(kbr_grab_step(&tm, 0.1f, 1, &out_i, 0, 0, 1) == KBR_G_ABORT, "dead");
        CHECK(kbr_grab_step(&tm, 0.1f, 1, &out_i, 1, 1, 1) == KBR_G_ABORT, "taken");
        CHECK(kbr_grab_step(&tm, 0.1f, 1, &out_i, 1, 0, 2) == KBR_G_ABORT, "state 2");
        tm = 1.0f; out_i = 0;
        CHECK(kbr_grab_step(&tm, -5.0f, 1, &out_i, 1, 0, 1) == KBR_G_KEEP && tm == 1.0f, "negative dt does not add time");
        /* part */
        CHECK(kbr_part(50000, 120000) == 50000 && kbr_part(50000, 20000) == 20000 && kbr_part(50000, -5) == 0, "part = min, never negative");
        /* hand-off */
        {
            int lr, br;
            kbr_hand(1, 1, 1, 10000, 9000, 0, 0, 1500, 2000, &lr, &br);
            CHECK(lr == 1 && br == 0, "loot steers, van idle");
            kbr_hand(1, 1, 1, 10000, 9000, 0, 3, 1500, 2000, &lr, &br);
            CHECK(lr == 0 && br == 0, "van waiting but Board never nonzero: nobody steers (puppeteer takes back)");
            kbr_hand(1, 1, 1, 10000, 9000, 9500, 3, 1500, 2000, &lr, &br);
            CHECK(lr == 0 && br == 1, "board steers at van 3");
            kbr_hand(1, 1, 0, 10000, 9000, 9500, 4, 1500, 2000, &lr, &br);
            CHECK(lr == 0 && br == 0, "Board off");
            kbr_hand(1, 1, 1, 10000, 5000, 0, 0, 1500, 2000, &lr, &br);
            CHECK(lr == 0 && br == 0, "loot window expired");
            kbr_hand(1, 1, 1, 100, 0xfffffff0ul, 0, 0, 1500, 2000, &lr, &br);
            CHECK(lr == 1, "GetTickCount wrap");
            kbr_hand(1, 1, 1, 100, 0, 0xfffffff0ul, 4, 1500, 2000, &lr, &br);
            CHECK(br == 1, "board wrap");
            kbr_hand(0, 1, 1, 10000, 9000, 0, 0, 1500, 2000, &lr, &br);
            CHECK(lr == 0, "PuppetOff off: never released");
            kbr_hand(1, 1, 1, 10000, 0, 10000ul | 1ul, 4, 1500, 2000, &lr, &br);
            CHECK(br == 1, "board: a now|1 stamp read in the same even ms still counts (no wrap)");
            kbr_hand(1, 1, 1, 10000, 10000ul | 1ul, 0, 0, 1500, 2000, &lr, &br);
            CHECK(lr == 1 && br == 0, "loot: a now|1 stamp read in the same even ms still counts (no wrap)");
        }
        /* coroutine rule (bs1 c0000029): Loot / Board RUN are never called; their evaluates, Board EXIT and the Traitor are */
        CHECK(!kbr_orig_ok(0, 0) && !kbr_orig_ok(1, 0), "coroutine rule: Loot RUN and Board RUN are never called");
        CHECK(kbr_orig_ok(1, 1) && kbr_orig_ok(2, 0) && kbr_orig_ok(0, 1), "coroutine rule: Board EXIT, Traitor RUN and Loot EXIT may be called");
        /* RealRun: vtable slots straight at the originals, and the longjmp thunk decision */
        CHECK(kbr_run_direct(1, 0, 0) && kbr_run_direct(1, 1, 0) && kbr_run_direct(1, 1, 1), "realrun: Loot RUN, Board RUN, Board EXIT go straight to the original");
        CHECK(!kbr_run_direct(1, 0, 1) && !kbr_run_direct(1, 2, 0) && !kbr_run_direct(1, 2, 1) && !kbr_run_direct(0, 0, 0) && !kbr_run_direct(0, 1, 0) && !kbr_run_direct(0, 1, 1), "realrun: nothing else, and nothing with RealRun off");
        CHECK(!kbr_orig_ok(0, 0) && !kbr_orig_ok(1, 0), "realrun does not let the DLL call a yielding RUN itself");
        CHECK(kbr_lj_decide(0x1000, 1, 0x168e4c8, 0, 1) == KBR_LJ_SWAP && kbr_lj_decide(0x1000, 2, 0x168e4c8, 0, 1) == KBR_LJ_SWAP, "longjmp: a resume (val 1 / 2) of our tactic swaps");
        CHECK(kbr_lj_decide(0x1000, 1, 0x168e4c8, 0, 0) == KBR_LJ_PASS, "longjmp: a foreign goal passes");
        CHECK(kbr_lj_decide(0x1000, 0, 0x168e4c8, 0, 1) == KBR_LJ_PASS && kbr_lj_decide(0x1000, 3, 0x168e4c8, 0, 1) == KBR_LJ_PASS, "longjmp: only val 1 / 2 resume a goal");
        CHECK(kbr_lj_decide(0x1000, 1, 0x168e4c8, 1, 1) == KBR_LJ_PASS, "longjmp: already swapped, no second swap (would overwrite the saved real rules)");
        CHECK(kbr_lj_decide(0x168e4c8, 1, 0x168e4c8, 1, 0) == KBR_LJ_RESTORE, "longjmp: the slice leaves to the scheduler while swapped -> restore");
        CHECK(kbr_lj_decide(0x168e4c8, 1, 0x168e4c8, 0, 0) == KBR_LJ_PASS, "longjmp: a foreign slice ends, nothing swapped");
        CHECK(kbr_lj_decide(0x168e4c8, 1, 0x168e4c8, 0, 1) == KBR_LJ_PASS && kbr_lj_decide(0, 1, 0x168e4c8, 1, 1) == KBR_LJ_PASS, "longjmp: the scheduler buf never swaps in; a null buf passes");
        CHECK(kbr_lj_restore_mask(0x500, 0x500, 0) == 3 && kbr_lj_restore_mask(0x600, 0x500, 0) == 2 && kbr_lj_restore_mask(0x500, 0x500, 2) == 1 && kbr_lj_restore_mask(0x600, 0x500, 3) == 0, "restore mask: each field only when it still reads what we wrote");
        /* ArcadePick window */
        CHECK(kbr_pick_live(20000, 10001, 15000) && !kbr_pick_live(30000, 10001, 15000) && !kbr_pick_live(20000, 0, 15000), "pick: live inside the window, stale after, never stamped = none");
        CHECK(kbr_pick_live(10000, 10000ul | 1ul, 15000), "pick: a now|1 stamp read in the same even ms still counts (no wrap)");
        /* stall watchdog */
        {
            unsigned long since = 0, until = 0, cc[5] = { 11, 22, 33, 44, 55 }; int run = 0;
            CHECK(kbr_watch(1000, 1, 0, &since, &until, 8000, 10000) == 1 && since == (1000ul | 1ul), "stall starts, hand-off stands");
            CHECK(kbr_watch(5000, 1, 1, &since, &until, 8000, 10000) == 1 && since == 0, "progress clears the stall");
            CHECK(kbr_watch(6000, 1, 0, &since, &until, 8000, 10000) == 1, "new stall");
            CHECK(kbr_watch(13999, 1, 0, &since, &until, 8000, 10000) == 1, "just under the limit");
            CHECK(kbr_watch(14000, 1, 0, &since, &until, 8000, 10000) == 0 && until != 0, "stall limit: revoked");
            CHECK(kbr_watch(20000, 1, 1, &since, &until, 8000, 10000) == 0, "revoked even with progress");
            CHECK(kbr_watch(24001, 1, 0, &since, &until, 8000, 10000) == 1 && until == 0, "revoke ends, hand-off again");
            CHECK(kbr_watch(25000, 0, 0, &since, &until, 8000, 10000) == 0 && since == 0, "not handed: nothing to watch");
            since = 0; until = 0;
            CHECK(kbr_watch(0xfffff000ul, 1, 0, &since, &until, 8000, 10000) == 1, "wrap: stall starts");
            CHECK(kbr_watch(0x00001000ul + 0x1000ul, 1, 0, &since, &until, 8000, 10000) == 0, "wrap: limit reached across 0");
            CHECK(kbr_watch(0x00001000ul + 0x2000ul, 1, 0, &since, &until, 8000, 10000) == 0, "wrap: still revoked");
            /* slow rule */
            CHECK(!kbr_slow_rule(60000, 50000, &run, 3) && !kbr_slow_rule(60000, 50000, &run, 3) && kbr_slow_rule(60000, 50000, &run, 3), "three consecutive slow frames trip");
            run = 0;
            CHECK(!kbr_slow_rule(60000, 50000, &run, 3) && !kbr_slow_rule(60000, 50000, &run, 3) && !kbr_slow_rule(100, 50000, &run, 3) && !kbr_slow_rule(60000, 50000, &run, 3), "a fast frame resets the run");
            /* chosen stack */
            CHECK(kbr_chosen(cc, 0) == 11 && kbr_chosen(cc, 4) == 55 && kbr_chosen(cc, 5) == 0 && kbr_chosen(cc, 0xffffffffu) == 0, "chosen = cand[idx], range checked");
        }
        /* cand_sort */
        ob[0] = 11; ob[1] = 22; ob[2] = 33; ob[3] = 44; ob[4] = 55; ob[5] = 66; ob[6] = 77; ob[7] = 0;
        d2[0] = 50; d2[1] = 10; d2[2] = 30; d2[3] = 20; d2[4] = 40; d2[5] = 5; d2[6] = 60; d2[7] = 1;
        CHECK(kbr_cand_sort(ob, d2, 8, res, 5) == 5 && res[0] == 66 && res[1] == 22 && res[2] == 44 && res[3] == 33 && res[4] == 55, "5 nearest in order, null skipped");
        for (i = 0; i < 7; i++) d2[i] = 10;
        CHECK(kbr_cand_sort(ob, d2, 7, res, 5) == 5 && res[0] == 11 && res[1] == 22 && res[2] == 33 && res[3] == 44 && res[4] == 55, "ties keep index order");
        CHECK(kbr_cand_sort(ob, d2, 2, res, 5) == 2 && res[0] == 11 && res[1] == 22 && res[2] == 0 && res[4] == 0, "fewer than 5: tail zero");
        CHECK(kbr_cand_sort(ob, d2, 0, res, 5) == 0 && res[0] == 0, "empty");
    }
    {   /* StackClaims: a peer's grab always, a peer's fresh pick within the window, never my own */
        unsigned long ct[3] = { 100, 200, 300 }, ow[3] = { 1, 2, 3 }, at[3] = { 0, 10001, 2001 };
        CHECK(kbr_claimed(100, 2, 1, ct, ow, at, 3, 12000, 4000) && !kbr_claimed(100, 1, 1, ct, ow, at, 3, 12000, 4000), "claims: a peer's grab is claimed, my own grab is not");
        CHECK(kbr_claimed(200, 1, 1, ct, ow, at, 3, 12000, 4000) && !kbr_claimed(200, 2, 1, ct, ow, at, 3, 12000, 4000), "claims: a peer's fresh pick is claimed, my own pick is not");
        CHECK(!kbr_claimed(300, 1, 1, ct, ow, at, 3, 12000, 4000), "claims: a stale pick (10 s old, window 4 s) is free");
        CHECK(kbr_claimed(100, 0, 1, ct, ow, at, 3, 12000, 4000) && !kbr_claimed(200, 0, 1, ct, ow, at, 3, 12000, 4000), "claims: unknown caller sees grabs only");
        CHECK(!kbr_claimed(100, 1, 0, ct, ow, at, 3, 12000, 4000) && kbr_claimed(100, 2, 0, ct, ow, at, 3, 12000, 4000) && !kbr_claimed(200, 1, 0, ct, ow, at, 3, 12000, 4000), "claims: picks off = grabs only, my own grab still mine");
        CHECK(!kbr_claimed(400, 1, 1, ct, ow, at, 3, 12000, 4000) && !kbr_claimed(0, 1, 1, ct, ow, at, 3, 12000, 4000), "claims: unclaimed / null stack free");
    }
    {   /* DropCands: drop validity (the ranking is the shared kbr_cand_sort: stacks and drops merged by distance, as Arcade) */
        CHECK(kbr_drop_valid(1, 100, 0, 1) && !kbr_drop_valid(0, 100, 0, 1) && !kbr_drop_valid(1, 0, 0, 1) && !kbr_drop_valid(1, -5, 0, 1), "drop: armed with an amount left is valid");
        CHECK(!kbr_drop_valid(1, 100, 1, 1) && !kbr_drop_valid(1, 100, -1, 1) && !kbr_drop_valid(1, 100, 0, 0), "drop: hidden / unreadable node / not tracked-ok (no real drain) is not valid");
    }
    {   /* BoardStage: stage byte and the deferral clock */
        unsigned long since = 0;
        CHECK(kbr_stage_byte(0, 0, 5, 3, 1) == 2 && kbr_stage_byte(0, 0, 0, 3, 1) == 1 && kbr_stage_byte(0, 1, 0, 0, 0) == 3, "stage: off = the old 1 / 2 / 3 (aboard only)");
        CHECK(kbr_stage_byte(1, 0, 5, 3, 0) == 3 && kbr_stage_byte(1, 0, 5, 4, 0) == 3 && kbr_stage_byte(1, 0, 0, 3, 1) == 3, "stage: van waiting + loot or ordered to the box = 3");
        CHECK(kbr_stage_byte(1, 0, 5, 2, 1) == 2 && kbr_stage_byte(1, 0, 5, 0, 1) == 2 && kbr_stage_byte(1, 0, 0, 3, 0) == 1 && kbr_stage_byte(1, 0, -1, 3, 0) == 1, "stage: van not called / nothing carried or ordered = 2 / 1");
        CHECK(kbr_stage_byte(1, 1, 0, 0, 0) == 3, "stage: aboard is 3 whatever the van says");
        CHECK(!kbr_bs_defer(0, 1, 1000, &since, 6000) && since == 0 && !kbr_bs_defer(1, 0, 1000, &since, 6000) && since == 0, "defer: off or not live = no deferral, no clock");
        CHECK(kbr_bs_defer(1, 1, 1000, &since, 6000) && since && kbr_bs_defer(1, 1, 6900, &since, 6000) && !kbr_bs_defer(1, 1, 7001, &since, 6000), "defer: live defers up to max_ms, then falls back");
        since = 0; CHECK(kbr_bs_defer(1, 1, 0xfffffff0ul, &since, 6000) && kbr_bs_defer(1, 1, 0x1000ul, &since, 6000) && !kbr_bs_defer(1, 1, 0x2000ul, &since, 6000), "defer: tick wrap safe");
        CHECK(kbr_bs_live(1, 0, 1, 5000, 1, 2500) && !kbr_bs_live(0, 0, 0, 5000, 0, 2500) && !kbr_bs_live(0, 1, 1, 5000, 0, 2500), "grace: live passes; no van wait or an earlier Board evaluate = no grace");
        CHECK(kbr_bs_hold(5000, 2001, 1, 4500) && kbr_bs_hold(6400, 2001, 1, 4500) && !kbr_bs_hold(6500, 2001, 1, 4500), "hold: live for hold_ms after bnzAt (|1 stamp masked)");
        CHECK(!kbr_bs_hold(5000, 2001, 0, 4500) && !kbr_bs_hold(5000, 0, 1, 4500) && !kbr_bs_hold(5000, 2001, 1, 0), "hold: off without van wait, without a stamp, or hold 0");
        CHECK(kbr_bs_hold(0x100ul, 0xfffffff1ul, 1, 4500) && !kbr_bs_hold(0x2000ul, 0xfffffff1ul, 1, 4500), "hold: tick wrap safe");
        CHECK(kbr_bs_live(0, 1, 0, 5000, 0, 2500) && kbr_bs_live(0, 1, 0, 5000, 3001, 2500) && !kbr_bs_live(0, 1, 0, 5600, 3001, 2500), "grace: no evaluate yet waits grace_ms from the deferral start");
        CHECK(kbr_bs_live(0, 1, 0, 0x100ul, 0xfffffff1ul, 2500), "grace: tick wrap safe");
    }
    {   /* OnlineBrainTraitorTurn: diagnostics counter, row 0, score terms, back reasons, kill booking, cap word */
        int dn = 0, w = -9, i; long m[4] = { 100, 900000, 5, 2000000 }; unsigned char u[4] = { 1, 1, 0, 1 }; float d[4];
        for (i = 0; i < 6; i++) CHECK(kbr_diag_take(&dn, 6), "diag: slot %d of 6", i);
        CHECK(!kbr_diag_take(&dn, 6) && dn == 6, "diag: the 7th is refused, counter stays 6");
        CHECK(kbr_row0_money(0, m, u, 4, &w) == 100 && w == 0, "row0: host mode = seat 0");
        CHECK(kbr_row0_money(1, m, u, 4, &w) == 2000000 && w == 3, "row0: richest mode = seat 3");
        u[0] = 0; CHECK(kbr_row0_money(0, m, u, 4, &w) == 900000 && w == 1, "row0: host mode with seat 0 unused = first used seat");
        m[1] = -5; CHECK(kbr_row0_money(0, m, u, 4, &w) == 0 && w == 1, "row0: negative money counts as 0");
        u[1] = u[3] = 0; CHECK(kbr_row0_money(1, m, u, 4, &w) == 0 && w == -1, "row0: no used seat -> 0, which -1");
        CHECK(kbr_tr_bot_term(0) == 0 && kbr_tr_bot_term(749999) == 0 && kbr_tr_bot_term(750000) == 1 && kbr_tr_bot_term(1000000) == 2 && kbr_tr_bot_term(1250000) == 3, "terms: bot money 0/1/2/3 at 750k / 1.0M / 1.25M");
        CHECK(kbr_tr_pl_term(0) == 3 && kbr_tr_pl_term(1000000) == 1 && kbr_tr_pl_term(9000000) == 0, "terms: player money 3..0");
        CHECK(kbr_tr_sum(3.0f, 800000, 0) == 7.0f && kbr_tr_sum(2.0f, 1000000, 0) == 7.0f && kbr_tr_sum(3.0f, 700000, 0) == 6.0f, "sum: the reachable level-6 sums (3+1+3, 2+2+3 pass 7; 3+0+3 does not)");
        CHECK(kbr_tr_back_why(0, 0, 1, 1, 1) == 0, "back: nothing wrong stays turned");
        CHECK(kbr_tr_back_why(1, 0, 1, 1, 1) == KBR_TB_DEAD && kbr_tr_back_why(0, 1, 1, 1, 1) == KBR_TB_ABOARD && kbr_tr_back_why(0, 0, 0, 1, 1) == KBR_TB_STATE, "back: dead / aboard / untracked");
        CHECK(kbr_tr_back_why(1, 1, 0, 0, 0) == KBR_TB_ROUND && kbr_tr_back_why(1, 1, 0, 1, 0) == KBR_TB_CHANGED && kbr_tr_back_why(1, 1, 0, 1, 1) == KBR_TB_DEAD, "back: priority round > changed > dead > aboard > state");
        CHECK(kbr_tb_name[KBR_TB_ROUND][0] && kbr_tb_name[KBR_TB_CHANGED][0], "back: names");
        d[0] = 5000; d[1] = 2500; d[2] = -1; d[3] = 3000;
        CHECK(kbr_tr_nearest(d, 4, 3000) == 1, "nearest: the closest within range wins");
        d[1] = 3500; CHECK(kbr_tr_nearest(d, 4, 3000) == 3, "nearest: out-of-range and unknown skipped");
        d[3] = 4000; CHECK(kbr_tr_nearest(d, 4, 3000) == -1 && kbr_tr_nearest(d, 0, 3000) == -1, "nearest: none in range / empty");
        CHECK(!kbr_tr_capped(1, 2) && kbr_tr_capped(2, 2) && kbr_tr_capped(5, 2) && !kbr_tr_capped(9, 0), "cap: reached at max, never with max 0");
        CHECK(kbr_tr_cap_word(1, 2) == 0 && kbr_tr_cap_word(2, 2) == 0x7ffful && kbr_tr_cap_word(9, 0) == 0, "cap word: 0 below the cap or off, 0x7fff at the cap");
    }
    {   /* ArcadeDiag helpers */
        float st[4] = { 0, 0, 2, 3 };
        CHECK(kbr_ad_slot_ok(0, 12) && kbr_ad_slot_ok(11, 12) && !kbr_ad_slot_ok(12, 12) && !kbr_ad_slot_ok(0, 0), "ad: slot range");
        CHECK(!kbr_ad_unused(0, 3, 12) && kbr_ad_unused(1, 3, 12) && kbr_ad_unused(0, 12, 12), "ad: unused = free byte set or slot >= count");
        CHECK(kbr_ad_money(500, 0) == 500 && kbr_ad_money(500, 1) == -1, "ad: unused slot reads -1");
        CHECK(kbr_ad_term_u(-1) == 3 && kbr_ad_term_u(0) == 0 && kbr_ad_term_u(750000) == 1 && kbr_ad_term_u(1250000) == 3, "ad: unsigned terms, -1 = 3");
        CHECK(kbr_ad_stage_ix(3) == 3 && kbr_ad_stage_ix(4) == 0 && kbr_ad_stage_ix(-1) == 0, "ad: stage > 3 -> index 0");
        CHECK(kbr_ad_sum(st, 3, 800000, 0) == 7.0f && kbr_ad_sum(st, 3, -1, 0) == 9.0f && kbr_ad_sum(st, 3, 0, -1) == 3.0f && kbr_ad_sum(st, 9, 0, 0) == 3.0f, "ad: sums incl. -1 rows");
        CHECK(kbr_ad_pass(7.0f, 7.0f) && !kbr_ad_pass(6.9f, 7.0f) && kbr_ad_pass(9.0f, 7.0f), "ad: pass is >= the limit");
        CHECK(kbr_ad_rose(0, 2) && !kbr_ad_rose(2, 3) && !kbr_ad_rose(1, 1) && kbr_ad_rose(1, 3), "ad: mark = bit 1 rising");
    }
    {   /* OnlineBrainTraitorArcade decision */
        const unsigned long PL = 0xbb45f4ul;
        CHECK(kbr_tarc_decide(1, 1, 1, PL, PL, 1, 0, 1) == KBR_TA_ARCADE, "tarc: every condition met = ARCADE");
        CHECK(kbr_tarc_decide(0, 1, 1, PL, PL, 1, 0, 1) == KBR_TA_PASS, "tarc: key off = PASS");
        CHECK(kbr_tarc_decide(1, 0, 1, PL, PL, 1, 0, 1) == KBR_TA_PASS, "tarc: unmarked = PASS");
        CHECK(kbr_tarc_decide(1, 1, 0, PL, PL, 1, 0, 1) == KBR_TA_PASS, "tarc: shooter not ours = PASS");
        CHECK(kbr_tarc_decide(1, 1, 1, PL, PL, 1, 1, 1) == KBR_TA_PASS, "tarc: Turn on = PASS (exclusive)");
        CHECK(kbr_tarc_decide(1, 1, 1, PL, PL, 1, 0, 0) == KBR_TA_PASS, "tarc: not a host round = PASS");
        CHECK(kbr_tarc_decide(1, 1, 1, PL, PL, 0, 0, 1) == KBR_TA_PASS, "tarc: unreadable target = PASS");
        CHECK(kbr_tarc_decide(1, 1, 1, 0xbb3bacul, PL, 1, 0, 1) == KBR_TA_PASS && kbr_tarc_decide(1, 1, 1, 0xbd0954ul, PL, 1, 0, 1) == KBR_TA_PASS, "tarc: a ZFFActor / ZSoldier target = PASS (bots untouched)");
    }
    {   /* OnlineBrainTraitorFireLine decision */
        CHECK(kbr_tfl_decide(1, 1, 1, 1, 0, 1) == KBR_TFL_LOG && kbr_tfl_decide(2, 1, 1, 1, 0, 1) == KBR_TFL_SWAP, "tfl: 1 = LOG, 2 = SWAP");
        CHECK(kbr_tfl_decide(0, 1, 1, 1, 0, 1) == KBR_TFL_PASS && kbr_tfl_decide(-1, 1, 1, 1, 0, 1) == KBR_TFL_PASS, "tfl: key 0 / negative = PASS");
        CHECK(kbr_tfl_decide(3, 1, 1, 1, 0, 1) == KBR_TFL_SWAP, "tfl: a value above 2 acts as SWAP");
        CHECK(kbr_tfl_decide(2, 0, 1, 1, 0, 1) == KBR_TFL_PASS, "tfl: Arcade off = PASS");
        CHECK(kbr_tfl_decide(2, 1, 0, 1, 0, 1) == KBR_TFL_PASS, "tfl: unmarked = PASS");
        CHECK(kbr_tfl_decide(2, 1, 1, 0, 0, 1) == KBR_TFL_PASS, "tfl: shooter not ours = PASS");
        CHECK(kbr_tfl_decide(2, 1, 1, 1, 1, 1) == KBR_TFL_PASS, "tfl: Turn on = PASS");
        CHECK(kbr_tfl_decide(2, 1, 1, 1, 0, 0) == KBR_TFL_PASS, "tfl: not a host round = PASS");
    }
    {   /* HitLog probe + OnlineBrainTraitorDamage decisions */
        CHECK(kbr_tgt_valid(100, 101) && !kbr_tgt_valid(101, 101) && !kbr_tgt_valid(200, 101), "tgt: valid while clock < stamp");
        CHECK(kbr_tgt_class(0, 1, 0, 0, 0) == KBR_TG_NONE, "tgt: no target = none");
        CHECK(kbr_tgt_class(1, 1, 0, 0, 0) == KBR_TG_HUMAN, "tgt: plain player body = human");
        CHECK(kbr_tgt_class(1, 1, 1, 0, 0) == KBR_TG_BOT, "tgt: tagged bot body = bot, not human");
        CHECK(kbr_tgt_class(1, 1, 0, 1, 0) == KBR_TG_COP, "tgt: police byte = cop");
        CHECK(kbr_tgt_class(1, 0, 0, 0, 1) == KBR_TG_COP && kbr_tgt_class(1, 0, 1, 0, 1) == KBR_TG_BOT && kbr_tgt_class(1, 0, 0, 0, 0) == KBR_TG_OTHER, "tgt: AI object = cop, tagged = bot, unknown = other");
        CHECK(!strcmp(kbr_tgt_name(KBR_TG_HUMAN), "human") && !strcmp(kbr_tgt_name(99), "none"), "tgt: names");
        CHECK(kbr_rate_ok(0, 5, 1000) && !kbr_rate_ok(5000, 5999, 1000) && kbr_rate_ok(5000, 6000, 1000), "rate: gap");
        CHECK(kbr_rate_ok(0xfffffff0ul, 0x00000400ul, 1000), "rate: wraps");
        CHECK(kbr_hp_drop(550.0f, 530.0f) == 20.0f && kbr_hp_drop(5.0f, 5.0f) == 0.0f, "hp drop");
        CHECK(kbr_dm_decide(1, 1, 1, 0) == KBR_DM_SET && kbr_dm_decide(1, 1, 1, 7) == KBR_DM_HAVE && kbr_dm_decide(1, 1, 1, 2) == KBR_DM_HAVE, "dm: byte 0 = SET, any nonzero = HAVE");
        CHECK(kbr_dm_decide(1, 1, 1, 1) == KBR_DM_HAVE, "dm: already 1 = HAVE (not ours to restore)");
        CHECK(kbr_dm_decide(0, 1, 1, 0) == KBR_DM_SKIP && kbr_dm_decide(1, 0, 1, 0) == KBR_DM_SKIP && kbr_dm_decide(1, 1, 0, 0) == KBR_DM_SKIP && kbr_dm_decide(1, 1, 1, -1) == KBR_DM_SKIP, "dm: off / unmarked / no body / unreadable = SKIP");
        CHECK(kbr_dm_restore_ok(1) && !kbr_dm_restore_ok(0) && !kbr_dm_restore_ok(2), "dm: restore only our 1");
    }
    {   /* CandLog / Sense */
        kbr_u32 seen[KBR_CC_SEEN]; int n = 0, k; long ty[4] = { 2, 1, 2, 0 };
        CHECK(kbr_cand_class(1, 1, 1) == KBR_CC_PLAYER && kbr_cand_class(0, 1, 1) == KBR_CC_ACTOR && kbr_cand_class(0, 0, 1) == KBR_CC_SOLDIER && kbr_cand_class(0, 0, 0) == KBR_CC_OTHER, "cc: class order");
        CHECK(!strcmp(kbr_cand_name(0), "ZFFPlayer") && !strcmp(kbr_cand_name(9), "other"), "cc: names");
        CHECK(kbr_cand_note(seen, &n, 0x100) == 1 && kbr_cand_note(seen, &n, 0x100) == 0 && kbr_cand_note(seen, &n, 0) == 0 && n == 1, "cc: distinct, null refused");
        for (k = 1; k <= 10; k++) kbr_cand_note(seen, &n, 0x100 + k);
        CHECK(n == KBR_CC_SEEN && kbr_cand_note(seen, &n, 0x999) == 0, "cc: capped at 6");
        CHECK(kbr_list_count(3) == 3 && kbr_list_count(-1) == 0 && kbr_list_count(11) == 0 && kbr_list_count(10) == 10, "list: count clamp");
        CHECK(kbr_list_type2(ty, 4) == 2 && kbr_list_type2(ty, 0) == 0 && kbr_list_type2(ty, 2) == 1, "list: type 2 count");
        CHECK(kbr_sense_decide(1, 1, 1, 1, 1, 0, 1, 0, 0, 1) == KBR_SN_FEED, "sense: all hold = FEED");
        CHECK(kbr_sense_decide(0, 1, 1, 1, 1, 0, 1, 0, 0, 1) == KBR_SN_SKIP && kbr_sense_decide(1, 0, 1, 1, 1, 0, 1, 0, 0, 1) == KBR_SN_SKIP, "sense: off / not host round = SKIP");
        CHECK(kbr_sense_decide(1, 1, 0, 1, 1, 0, 1, 0, 0, 1) == KBR_SN_SKIP && kbr_sense_decide(1, 1, 1, 0, 1, 0, 1, 0, 0, 1) == KBR_SN_SKIP && kbr_sense_decide(1, 1, 1, 1, 0, 0, 1, 0, 0, 1) == KBR_SN_SKIP, "sense: unmarked / unwrapped / dead = SKIP");
        CHECK(kbr_sense_decide(1, 1, 1, 1, 1, 1, 1, 0, 0, 1) == KBR_SN_SKIP && kbr_sense_decide(1, 1, 1, 1, 1, 0, 1, 0, 0, 0) == KBR_SN_SKIP, "sense: Turn on / rate = SKIP");
        CHECK(kbr_sense_decide(1, 1, 1, 1, 1, 0, 0, 0, 0, 1) == KBR_SN_SKIP && kbr_sense_decide(1, 1, 1, 1, 1, 0, 1, 1, 0, 1) == KBR_SN_SKIP && kbr_sense_decide(1, 1, 1, 1, 1, 0, 1, 0, 1, 1) == KBR_SN_SKIP, "sense: not a player / tagged bot / cop body = SKIP");
        {   float d[6] = { 9.0f, 1.0f, 5.0f, 1.0f, 7.0f, 2.0f }; int o[4], c = kbr_sense_nearest(d, 6, KBR_SN_MAXFEED, o);
            CHECK(c == 4 && o[0] == 1 && o[1] == 3 && o[2] == 5 && o[3] == 2, "sense: nearest 4 of 6, ties in list order");
            c = kbr_sense_nearest(d, 2, KBR_SN_MAXFEED, o); CHECK(c == 2 && o[0] == 1 && o[1] == 0, "sense: fewer than max");
            CHECK(kbr_sense_nearest(d, 0, KBR_SN_MAXFEED, o) == 0, "sense: none"); }
        CHECK(kbr_sense_ms(500) == 500 && kbr_sense_ms(0) == 500 && kbr_sense_ms(100) == 500 && kbr_sense_ms(200) == 200 && kbr_sense_ms(9000) == 500, "sense: interval clamp");
        {   /* FireProbe3 stub / jump / histogram */
            unsigned char b[64], j[10], st[6] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x1c }; kbr_u32 ra[3], r; long cnt[3]; int na = 0, k;
            k = kbr_f3_emit(b, 0x10000, 1, 0x12345678UL, st, 6, 0x8c1836UL);
            CHECK(k == 17 + 6 + 5 && k <= KBR_F3_MAXSTUB, "f3: stub size %d", k);
            CHECK(b[0] == 0x60 && b[1] == 0x9c && b[2] == 0x54 && b[3] == 0x6a && b[4] == 1 && b[5] == 0xb8 && b[6] == 0x78 && b[9] == 0x12 && b[10] == 0xff && b[11] == 0xd0 && b[14] == 0x08 && b[15] == 0x9d && b[16] == 0x61, "f3: stub prologue bytes");
            CHECK(memcmp(b + 17, st, 6) == 0 && b[23] == 0xe9, "f3: stolen bytes then jmp");
            r = (kbr_u32)b[24] | (kbr_u32)b[25] << 8 | (kbr_u32)b[26] << 16 | (kbr_u32)b[27] << 24; CHECK((kbr_u32)(0x10000 + 23 + 5 + r) == 0x8c1836UL, "f3: return jump lands after the stolen bytes");
            CHECK(kbr_f3_emit(b, 0, 0, 0, st, 4, 0) == 0 && kbr_f3_emit(b, 0, 0, 0, st, 11, 0) == 0, "f3: bad stolen length refused");
            kbr_f3_jmp(j, 0x8c1830UL, 0x20000UL, 6);
            r = (kbr_u32)j[1] | (kbr_u32)j[2] << 8 | (kbr_u32)j[3] << 16 | (kbr_u32)j[4] << 24; CHECK(j[0] == 0xe9 && j[5] == 0x90 && (kbr_u32)(0x8c1830UL + 5 + r) == 0x20000UL, "f3: patch jmp + nop");
            CHECK(kbr_f3_ra_add(ra, cnt, &na, 3, 0x5000) == 1 && kbr_f3_ra_add(ra, cnt, &na, 3, 0x5000) == 0 && cnt[0] == 2 && na == 1, "f3: histogram counts a known address");
            kbr_f3_ra_add(ra, cnt, &na, 3, 0x6000); kbr_f3_ra_add(ra, cnt, &na, 3, 0x7000);
            CHECK(kbr_f3_ra_add(ra, cnt, &na, 3, 0x8000) == 0 && na == 3, "f3: histogram full");
            CHECK(kbr_f3_ammo(0xbeebbeebUL) == 0 && kbr_f3_ammo(0xbeebbeeaUL) == 1, "f3: ammo xor");
        }
        CHECK(kbr_f4_bit(0x1000, 12) == 1 && kbr_f4_bit(0x1000, 11) == 0 && kbr_f4_bit(0x40000, 18) == 1 && kbr_f4_bit(0xffffffffUL, 31) == 1, "f4: bit");
        CHECK(kbr_f4_delta(0, 5, 9) == 0 && kbr_f4_delta(1, 5, 9) == 4 && kbr_f4_delta(1, 9, 5) == 0 && kbr_f4_delta(1, 7, 7) == 0, "f4: delta");
        CHECK(kbr_f4_route(0, 0, 0, 0, 0) == 3 && kbr_f4_route(2, 1, 0, 0, 0) == 0 && kbr_f4_route(2, 0, 1, 0, 5) == 1 && kbr_f4_route(2, 0, 1, 5, 5) == 2 && kbr_f4_route(3, 0, 0, 0, 5) == 2 && kbr_f4_route(2, 0, 1, 7, 5) == 1, "f4: route");
        CHECK(strcmp(kbr_f4_route_name(1), "drop (bot attacker, victim station remote: id 0 or not the local id)") == 0 && kbr_f4_route_name(9)[0] == 'u', "f4: route name");
        CHECK(kbr_f5_route(1, 0, 0, 0, 0, 0, 0, 0, 0) == 0 && kbr_f5_route(2, 1, 1, 1, 1, 9, 1, 9, 5) == 1 && kbr_f5_route(2, 0, 1, 1, 1, 9, 0, 0, 5) == 2 && kbr_f5_route(2, 0, 1, 1, 1, 5, 0, 0, 5) == 3 && kbr_f5_route(3, 0, 1, 0, 0, 0, 1, 0, 5) == 4 && kbr_f5_route(2, 0, 0, 0, 0, 0, 1, 5, 0) == 5 && kbr_f5_route(2, 0, 0, 0, 0, 0, 0, 0, 5) == 5, "f5: route");
        CHECK(kbr_f5_remote(1, 0, 0) == 1 && kbr_f5_remote(1, 7, 5) == 1 && kbr_f5_remote(1, 5, 5) == 0 && kbr_f5_remote(0, 0, 5) == 0 && kbr_f5_remote(1, 7, 0) == 0, "f5: remote");
        CHECK(kbr_f5_applies(0) && kbr_f5_applies(1) && kbr_f5_applies(5) && !kbr_f5_applies(2) && !kbr_f5_applies(3) && !kbr_f5_applies(4) && kbr_f5_route_name(2)[0] != 0, "f5: applies");
        { static const kbr_u32 rg[2][2] = { { 0x4c5000u, 0x4ca000u }, { 0x4cd000u, 0x4cf000u } };      /* the ranges around 0x4cc389 (klranges.h) */
          CHECK(!kbr_f5_in_ranges(rg, 2, 0x4cc389u, 11) && kbr_f5_in_ranges(rg, 2, 0x4c9ffcu, 11) && kbr_f5_in_ranges(rg, 2, 0x4cd000u, 1) && !kbr_f5_in_ranges(rg, 2, 0x4ca000u, 0x1000), "f5: in_ranges"); }
        CHECK(kbr_f5_kind(1, 1) == 0 && kbr_f5_kind(1, 0) == 1 && kbr_f5_kind(0, 1) == 2 && kbr_f5_kind(0, 0) == 3 && kbr_f5_kind(1, 0x80) == 0, "f5: kind");
        CHECK(kbr_gf_force(1, 0, 1, 1, 0x4cb81b, 0x4cb81b, 0x77c, 0xfff) == 0x77c && kbr_gf_force(1, 0, 1, 1, 0x4cb81c, 0x4cb81b, 0x77c, 0xfff) == 0 && kbr_gf_force(0, 0, 1, 1, 0x4cb81b, 0x4cb81b, 0x77c, 0xfff) == 0, "gf: marked, right return address only, on only");
        CHECK(kbr_gf_force(1, 0, 0, 1, 0x4cb81b, 0x4cb81b, 0x77c, 0xfff) == 0 && kbr_gf_force(1, 1, 0, 1, 0x4cb81b, 0x4cb81b, 0x77c, 0xfff) == 0x77c && kbr_gf_force(1, 1, 0, 0, 0x4cb81b, 0x4cb81b, 0x77c, 0xfff) == 0, "gf: unmarked needs 'all' and a bot");
        CHECK(kbr_gf_force(1, 1, 1, 1, 0x4cb81b, 0x4cb81b, 0, 0xfff) == 0 && kbr_gf_force(1, 1, 1, 1, 0x4cb81b, 0x4cb81b, 0x1000, 0xfff) == 0, "gf: a value the test cannot pass is never forced");
    }
    /* FireProbe6 helpers */
    {
        float o[3] = { 0, 0, 0 }, p[3] = { 10, 0, 0 }, q[3] = { 0, 10, 0 }, r[3] = { 10, 1, 0 }, d[3] = { 1, 0, 0 }, m[9] = { 1, 0, 0, 0, 1, 0, 0, 0, 1 }, m2[9] = { 1, 0, 0, 0, 1, 0, 0, 0, 0.5f }, z[3] = { 0, 0, 0 }, z2[3] = { 0, 0.5f, 0 };
        CHECK(kbr_f6_sqrt(4.0f) > 1.9999f && kbr_f6_sqrt(4.0f) < 2.0001f, "f6 sqrt 4");
        CHECK(kbr_f6_sqrt(-1.0f) == 0.0f && kbr_f6_sqrt(0.0f) == 0.0f, "f6 sqrt non-positive");
        CHECK(kbr_f6_acos_deg(1.0f) < 0.01f && kbr_f6_acos_deg(0.0f) > 89.99f && kbr_f6_acos_deg(0.0f) < 90.01f, "f6 acos 1 and 0");
        CHECK(kbr_f6_acos_deg(-1.0f) > 179.9f && kbr_f6_acos_deg(0.5f) > 59.9f && kbr_f6_acos_deg(0.5f) < 60.1f, "f6 acos -1 and 0.5");
        CHECK(kbr_f6_acos_deg(2.0f) < 0.01f && kbr_f6_acos_deg(-2.0f) > 179.9f, "f6 acos clamps");
        CHECK(kbr_f6_ang(o, p, q) > 89.9f && kbr_f6_ang(o, p, q) < 90.1f, "f6 ang 90");
        CHECK(kbr_f6_ang(o, p, p) < 0.01f, "f6 ang same direction");
        CHECK(kbr_f6_ang(o, p, r) > 5.6f && kbr_f6_ang(o, p, r) < 5.8f, "f6 ang 5.7 deg");
        CHECK(kbr_f6_ang(o, o, p) < 0.0f, "f6 ang degenerate = -1");
        CHECK(kbr_f6_ang_dir(d, o, q) > 89.9f && kbr_f6_ang_dir(d, o, q) < 90.1f && kbr_f6_ang_dir(z, o, q) < 0.0f, "f6 ang_dir");
        CHECK(kbr_f6_dist(o, p) > 9.999f && kbr_f6_dist(o, p) < 10.001f && kbr_f6_len(p) > 9.999f, "f6 dist and len");
        CHECK(kbr_f6_bucket(0.0f) == 0 && kbr_f6_bucket(4.9f) == 0 && kbr_f6_bucket(5.0f) == 1 && kbr_f6_bucket(14.9f) == 1 && kbr_f6_bucket(15.0f) == 2 && kbr_f6_bucket(44.9f) == 2 && kbr_f6_bucket(45.0f) == 3 && kbr_f6_bucket(-1.0f) == 4, "f6 bucket edges");
        CHECK(kbr_f6_is_ident(m) && !kbr_f6_is_ident(m2), "f6 identity test");
        CHECK(kbr_f6_is_zero3(z) && !kbr_f6_is_zero3(z2) && !kbr_f6_is_zero3(p), "f6 zero test");
    }
    CHECK(kbr_f6_branch(1, 0, 0, 0, 0, 0) == 1 && kbr_f6_branch(1, 1, 0, 0, 1, 1) == 1, "f6 branch A0: no handle or no owner");
    CHECK(kbr_f6_branch(1, 1, 1, 0, 0, 0) == 2 && kbr_f6_branch(1, 1, 1, 1, 0, 0) == 3, "f6 branch A1 / A2");
    CHECK(kbr_f6_branch(0, 0, 0, 0, 1, 1) == 4 && kbr_f6_branch(0, 1, 1, 1, 1, 1) == 4, "f6 branch B ignores the owner inputs");
    CHECK(kbr_f6_branch(0, 1, 1, 1, 0, 1) == 5 && kbr_f6_branch(0, 0, 0, 0, 1, 0) == 5 && kbr_f6_branch(0, 0, 0, 0, 0, 0) == 5, "f6 branch C: node null or class miss");
    CHECK(strstr(kbr_f6_branch_name(5), "identity") && strstr(kbr_f6_branch_name(1), "untouched") && strstr(kbr_f6_branch_name(9), "unknown"), "f6 branch names");
    CHECK(kbr_f6_incode(0x4cb8b9) && !kbr_f6_incode(0x50700c14) && !kbr_f6_incode(0x10), "f6 incode");
    {   /* the stubs for the Probe6 sites: a 6-byte stolen prologue (inc dword [esi+0x138]) and a 7-byte one (lea ecx,[esp+0xf4]) fit kbr_f3_emit; the jump covers exactly the stolen bytes */
        static const unsigned char inc6[6] = { 0xff, 0x86, 0x38, 0x01, 0x00, 0x00 }, lea7[7] = { 0x8d, 0x8c, 0x24, 0xf4, 0x00, 0x00, 0x00 };
        unsigned char st[KBR_F3_MAXSTUB + 8], jm[7]; int n;
        n = kbr_f3_emit(st, 0x30000000u, 6, 0x12345678u, inc6, 6, 0x4cb8bfu);
        CHECK(n == 17 + 6 + 5 && st[n - 5] == 0xe9 && st[4] == 6, "f6 stub with 6 stolen bytes");
        n = kbr_f3_emit(st, 0x30000000u, 7, 0x12345678u, lea7, 7, 0x4cc447u);
        CHECK(n == 17 + 7 + 5 && n <= KBR_F3_MAXSTUB, "f6 stub with 7 stolen bytes fits the stub cap");
        kbr_f3_jmp(jm, 0x4cc440u, 0x30000000u, 7);
        CHECK(jm[0] == 0xe9 && jm[5] == 0x90 && jm[6] == 0x90, "f6 jump padded with nops to 7 bytes");
    }
    /* RayAim / FireProbe7 helpers */
    {
        float id3[9] = { 1, 0, 0, 0, 1, 0, 0, 0, 1 }, old[9] = { 0, 0, 1, 0, 1, 0, -1, 0, 0 }, out[9], fw[3] = { 0.6f, 0.3f, 0.7416198f }, o[3] = { 0, 100, 0 }, tg[3] = { 300, 100, 400 }, dir[3], dist, c[3], sc[9] = { 2, 0, 0, 0, 1, 0, 0, 0, 1 };
        int row, k, ok = 1; kbr_u32 st = 12345u; float mx = 0.0f;
        CHECK(kbr_ra_valid(id3) && kbr_ra_valid(old) && !kbr_ra_valid(sc), "ra valid: rotations yes, scaled no");
        for (row = 0; row < 3; row++) {
            int sg;
            for (sg = -1; sg <= 1; sg += 2) {
                float *r0, *r1, *r2, f[3]; int j;
                CHECK(kbr_ra_build(old, fw, row, sg, out), "ra build ok");
                r0 = out; r1 = out + 3; r2 = out + 6;
                CHECK(kbr_ra_valid(out) && kbr_ra_dot(r0, r1) < 1e-4f && kbr_ra_dot(r0, r1) > -1e-4f && kbr_ra_dot(r0, r2) < 1e-4f && kbr_ra_dot(r0, r2) > -1e-4f && kbr_ra_dot(r1, r2) < 1e-4f && kbr_ra_dot(r1, r2) > -1e-4f, "ra build: orthonormal");
                for (j = 0; j < 3; j++) f[j] = out[3 * row + j] * (float)sg;
                CHECK(kbr_ra_dot(f, fw) > 0.9999f, "ra build: the chosen row is sign * fwd");
                CHECK((kbr_ra_det(out) > 0.0f) == (kbr_ra_det(old) > 0.0f), "ra build: handedness kept");
            }
        }
        { float neg[9] = { 0, 0, 1, 0, 1, 0, 1, 0, 0 }; CHECK(kbr_ra_det(neg) < 0.0f && kbr_ra_build(neg, fw, 2, 1, out) && kbr_ra_det(out) < 0.0f && kbr_ra_valid(out), "ra build: a left-handed old matrix stays left-handed"); }
        { float up[3] = { 0, 1, 0 }, v[3] = { 0, 0, 1 }; CHECK(kbr_ra_build(old, up, 2, 1, out) && kbr_ra_valid(out) && out[7] > 0.9999f, "ra build: fwd parallel to up is handled"); CHECK(kbr_ra_build(old, v, 0, 1, out) && kbr_ra_valid(out), "ra build: other row"); }
        { float z[3] = { 0, 0, 0 }, nan[3]; unsigned int q = 0x7fc00000u; memcpy(nan, &q, 4); nan[1] = nan[2] = 0; out[0] = 77.0f;
          CHECK(!kbr_ra_build(old, z, 2, 1, out) && !kbr_ra_build(old, nan, 2, 1, out) && !kbr_ra_build(sc, fw, 2, 1, out) && !kbr_ra_build(old, fw, 3, 1, out) && out[0] == 77.0f, "ra build: degenerate fwd / NaN / scaled old / bad row refused, out untouched"); }
        CHECK(kbr_ra_row(-1) == 2 && kbr_ra_row(0) == 0 && kbr_ra_row(1) == 1 && kbr_ra_row(2) == 2 && kbr_ra_row(7) == 2 && kbr_ra_sign(-1) == -1 && kbr_ra_sign(1) == 1 && kbr_ra_sign(0) == 1, "ra row / sign config");
        CHECK(kbr_ra_dir(o, tg, 6000.0f, dir, &dist) && dist > 499.9f && dist < 500.1f && dir[0] > 0.599f && dir[0] < 0.601f && dir[2] > 0.799f, "ra dir 500 units");
        CHECK(!kbr_ra_dir(o, tg, 400.0f, dir, &dist) && kbr_ra_dir(o, tg, 0.0f, dir, &dist) && !kbr_ra_dir(o, o, 0.0f, dir, &dist), "ra dir: max distance, 0 = unlimited, degenerate refused");
        for (k = 0; k < 2000; k++) {
            float a = kbr_ra_rng(&st), b = kbr_ra_rng(&st), e;
            if (a < 0.0f || a >= 1.0f || b < 0.0f || b >= 1.0f) ok = 0;
            CHECK(kbr_ra_cone(fw, 3, a, b, c), "ra cone ok");
            e = kbr_f6_acos_deg(kbr_ra_dot(c, fw) / kbr_f6_len(fw));
            if (e > mx) mx = e;
        }
        CHECK(ok, "ra rng in [0,1)");
        CHECK(mx <= 3.05f && mx > 1.0f, "ra cone: error never above the spread, and it does spread (max %.3f)", (double)mx);
        CHECK(kbr_ra_cone(fw, 0, 0.9f, 0.1f, c) && kbr_f6_acos_deg(kbr_ra_dot(c, fw) / kbr_f6_len(fw)) < 0.05f, "ra cone: 0 deg = exact");
        { float cc[3], f2[3] = { 0, 1, 0 }; CHECK(kbr_ra_cone(f2, 30, 0.0f, 1.0f, cc) && kbr_f6_acos_deg(kbr_ra_dot(cc, f2)) <= 30.2f, "ra cone: capped at 30 deg, vertical fwd ok"); CHECK(kbr_ra_cone(f2, 500, 0.99f, 0.99f, cc) && kbr_f6_acos_deg(kbr_ra_dot(cc, f2)) <= 30.2f, "ra cone: 500 deg request capped"); }
        CHECK(kbr_ra_gate(1, 1, 1, 1, 1, 1) && !kbr_ra_gate(0, 1, 1, 1, 1, 1) && !kbr_ra_gate(1, 0, 1, 1, 1, 1) && !kbr_ra_gate(1, 1, 0, 1, 1, 1) && !kbr_ra_gate(1, 1, 1, 0, 1, 1) && !kbr_ra_gate(1, 1, 1, 1, 0, 1) && !kbr_ra_gate(1, 1, 1, 1, 1, 0), "ra gate: every condition is needed (on, game thread, live marked, valid, geo, target)");
    }
    /* RayAim site bit 2 / FireProbe7 aim-point helpers */
    {
        float o[3] = { 10, 100, -5 }, d[3] = { 0.6f, 0.0f, 0.8f }, p[3] = { 7, 7, 7 }, inf[3], big;
        unsigned int q = 0x7f800000u; memcpy(&big, &q, 4); inf[0] = big; inf[1] = 0; inf[2] = 0;
        CHECK(kbr_ra_point(o, d, 500.0f, p) && p[0] > 309.9f && p[0] < 310.1f && p[1] > 99.9f && p[1] < 100.1f && p[2] > 394.9f && p[2] < 395.1f, "ra point: origin + dir * dist");
        CHECK(kbr_ra_point(o, d, 0.0f, p) && p[0] == 10.0f && p[2] == -5.0f, "ra point: dist 0 = origin");
        p[0] = 7.0f;
        CHECK(!kbr_ra_point(o, d, -1.0f, p) && !kbr_ra_point(o, inf, 5.0f, p) && !kbr_ra_point(inf, d, 5.0f, p) && !kbr_ra_point(o, d, big, p) && p[0] == 7.0f, "ra point: negative dist / non-finite refused, out untouched");
        CHECK(kbr_ra_sitemask(5) == 5 && kbr_ra_sitemask(7) == 7 && kbr_ra_sitemask(2) == 2 && kbr_ra_sitemask(3) == 3 && kbr_ra_sitemask(0) == 5 && kbr_ra_sitemask(8) == 5 && kbr_ra_sitemask(-1) == 7 && kbr_ra_sitemask(15) == 7, "ra sitemask: bits 1/2/4, empty -> 5");
        CHECK(kbr_f7_dbucket(-1.0f) == 4 && kbr_f7_dbucket(0.0f) == 0 && kbr_f7_dbucket(999.0f) == 0 && kbr_f7_dbucket(1000.0f) == 1 && kbr_f7_dbucket(2999.0f) == 1 && kbr_f7_dbucket(3000.0f) == 2 && kbr_f7_dbucket(5999.0f) == 2 && kbr_f7_dbucket(6000.0f) == 3 && kbr_f7_dbucket(9e6f) == 3, "f7 dbucket edges");
    }
    /* FireProbe8 helpers */
    {
        kbr_u32 set[3] = { 0x11, 0, 0x33 };
        CHECK(kbr_f8_near(5000, 3500, 2000) && kbr_f8_near(5000, 3000, 2000) && !kbr_f8_near(5000, 2999, 2000) && !kbr_f8_near(5000, 0, 2000) && kbr_f8_near(100, 0xfffffff0UL, 2000) && !kbr_f8_near(100, 5000, 2000), "f8 near: window edge, none, wrap, future");
        CHECK(kbr_f8_in_set(set, 3, 0x11) && kbr_f8_in_set(set, 3, 0x33) && !kbr_f8_in_set(set, 3, 0x22) && !kbr_f8_in_set(set, 3, 0) && !kbr_f8_in_set(set, 0, 0x11), "f8 in set: zero never matches");
        CHECK(kbr_f8_nulls(10, 7) == 3 && kbr_f8_nulls(5, 5) == 0 && kbr_f8_nulls(3, 4) == 0, "f8 nulls");
    }
    /* ModeBProbe helpers */
    {
        CHECK(kbr_mb_branch(0, 0, 5) == 3 && kbr_mb_branch(4, 4, 5) == 3 && kbr_mb_branch(0, 2, 5) == 4 && kbr_mb_branch(4, 1, 5) == 4, "mb branch: handle, +0x5ac free: create when +0x658 free, else retarget");
        CHECK(kbr_mb_branch(2, 0, 5) == 2 && kbr_mb_branch(1, 4, 5) == 2 && kbr_mb_branch(3, 0, 5) == 2, "mb branch: +0x5ac busy -> store720 only");
        CHECK(kbr_mb_branch(0, 0, 0) == 1 && kbr_mb_branch(4, 2, 0) == 1 && kbr_mb_branch(2, 0, 0) == 0, "mb branch: handle 0 -> CoverFire when free, else the 0x8318c2 path");
        CHECK(kbr_mb_branch(-1, 0, 5) == 5 && kbr_mb_branch(0, -1, 5) == 5 && kbr_mb_branch(2, -1, 5) == 2 && kbr_mb_branch(-1, -1, 0) == 5, "mb branch: unreadable state");
        CHECK(kbr_mb_cand_addr(0x1000, 0) == 0x1000 - 0xbc && kbr_mb_cand_addr(0x1000, 3) == 0x1000 - 0xbc + 36 && !kbr_mb_cand_addr(0x1000, -1) && !kbr_mb_cand_addr(0x1000, 16), "mb cand addr");
        CHECK(kbr_mb_inwin(1500, 1000, 10000) && kbr_mb_inwin(11000, 1000, 10000) && !kbr_mb_inwin(11001, 1000, 10000) && !kbr_mb_inwin(5, 0, 10000) && !kbr_mb_inwin(500, 1000, 10000) && kbr_mb_inwin(100, 0xfffffff0UL, 10000), "mb window: edges, none, before, wrap");
        CHECK(kbr_mb_due(1000, 1000) && kbr_mb_due(1500, 1000) && !kbr_mb_due(999, 1000) && kbr_mb_due(10, 0xfffffff0UL), "mb due: wrap safe");
        {
            kbr_u32 keys[3] = { 0, 0, 0 }; long cnt[3] = { 0, 0, 0 }; kbr_u32 ptrs[4] = { 0, 0x100000, 0x200000, 0x200000 }; int tr[5] = { 0, -1, 0, 0, 0 }, sel[5], tr2[5] = { 0, 1, -1, 1, 0 };
            CHECK(kbr_mb_vtclass(0) == 0 && kbr_mb_vtclass(0xbd0f14u) == 1 && kbr_mb_vtclass(0xbd1104u) == 2 && kbr_mb_vtclass(0xbd0954u) == 3, "mb vt class");
            CHECK(!strcmp(kbr_mb_vtname(0xbd0f14u), "ZSoldierAttack") && !strcmp(kbr_mb_vtname(0xbd1104u), "ZAttackTarget") && !strcmp(kbr_mb_vtname(0), "none") && !strcmp(kbr_mb_vtname(7), "other"), "mb vt name");
            CHECK(kbr_mb_modeslot(0) == 0 && kbr_mb_modeslot(4) == 4 && kbr_mb_modeslot(5) == 5 && kbr_mb_modeslot(0xffffffffu) == 5, "mb mode slot");
            CHECK(kbr_mb_match(0x200000, ptrs, 4) == 2 && kbr_mb_match(0x100000, ptrs, 4) == 1 && kbr_mb_match(0x300000, ptrs, 4) == -1 && kbr_mb_match(0, ptrs, 4) == -1 && kbr_mb_match(0x20, ptrs, 4) == -1, "mb match: first hit, none, null current");
            CHECK(kbr_mb_tally(keys, cnt, 3, 0x11) == 0 && kbr_mb_tally(keys, cnt, 3, 0x22) == 1 && kbr_mb_tally(keys, cnt, 3, 0x11) == 0 && cnt[0] == 2 && cnt[1] == 1 && kbr_mb_tally(keys, cnt, 3, 0x33) == 2 && kbr_mb_tally(keys, cnt, 3, 0x44) == -1 && kbr_mb_tally(keys, cnt, 3, 0) == -1, "mb tally: new, repeat, full, zero key");
            CHECK(kbr_mb_arc_pick(tr, 5, sel, 2) == 2 && sel[0] == 1 && sel[1] == 0 && sel[2] == 1 && sel[3] == 0 && sel[4] == 0, "mb arc pick: no mark -> first 2 candidates");
            CHECK(kbr_mb_arc_pick(tr2, 5, sel, 2) == 2 && !sel[0] && sel[1] && !sel[2] && sel[3] && !sel[4], "mb arc pick: marked only");
            CHECK(kbr_mb_arc_pick(tr, 0, sel, 2) == 0, "mb arc pick: empty");
        }
    }
    /* CloseInProbe / CombatFlag helpers */
    {
        char nm[3][32]; long nc[3];
        memset(nm, 0, sizeof nm); memset(nc, 0, sizeof nc);
        CHECK(kbr_ci_list_n(0x101000, 0x101000) == 0 && kbr_ci_list_n(0x101000, 0x101010) == 4 && kbr_ci_list_n(0x101000, 0x101100) == 64, "ci list: empty, 4 entries, 64 (the cap)");
        CHECK(kbr_ci_list_n(0, 0x10) == -1 && kbr_ci_list_n(0x101000, 0x100ff0) == -1 && kbr_ci_list_n(0x101000, 0x101002) == -1 && kbr_ci_list_n(0x101000, 0x101104) == -1 && kbr_ci_list_n(0x20, 0x30) == -1, "ci list: null, backwards, misaligned, too long, tiny pointer");
        CHECK(kbr_ci_list_pick(1, 1, 0) == 0 && kbr_ci_list_pick(1, 0, 0) == 1 && kbr_ci_list_pick(0, 1, 0) == 1 && kbr_ci_list_pick(0, 0, 0) == 1 && kbr_ci_list_pick(1, 1, 1) == 2 && kbr_ci_list_pick(0, 0, 1) == 2, "ci list pick: A needs 4fc AND 6fc, C wins when active, else B");
        CHECK(kbr_ci_timer_left(1000, 400) == 600 && kbr_ci_timer_left(1000, 1000) == 0 && kbr_ci_timer_left(1000, 1500) == 0 && kbr_ci_timer_left(5, -10) == 15 && kbr_ci_timer_left(-5, 10) == 0, "ci timer: signed compare, open at equal");
        CHECK(kbr_ci_pct(1, 4) == 25 && kbr_ci_pct(0, 9) == 0 && kbr_ci_pct(9, 9) == 100 && kbr_ci_pct(5, 0) == -1 && kbr_ci_pct(1, 3) == 33, "ci pct");
        CHECK(kbr_ci_name_tally(nm, nc, 3, "ZDefend") == 0 && kbr_ci_name_tally(nm, nc, 3, "ZFollow") == 1 && kbr_ci_name_tally(nm, nc, 3, "ZDefend") == 0 && nc[0] == 2 && nc[1] == 1, "ci name tally: new, repeat");
        CHECK(kbr_ci_name_tally(nm, nc, 3, "A") == 2 && kbr_ci_name_tally(nm, nc, 3, "B") == -1 && kbr_ci_name_tally(nm, nc, 3, "") == -1 && kbr_ci_name_tally(nm, nc, 3, 0) == -1, "ci name tally: full, empty, null");
        CHECK(kbr_cb_decide(1, 1, 1, 2, 0, 0, 0) == 0 && kbr_cb_decide(2, 1, 1, 1, 0, 1, 0) == 0, "cb: write (mode 1 needs 6fc 0, mode 2 needs 6fc nonzero)");
        CHECK(kbr_cb_decide(1, 1, 1, 2, 0, 1, 0) == 3 && kbr_cb_decide(2, 1, 1, 2, 0, 0, 0) == 3, "cb: 6fc condition fails");
        CHECK(kbr_cb_decide(1, 1, 1, 2, 1, 0, 0) == 2 && kbr_cb_decide(2, 1, 1, 1, 3, 1, 0) == 2, "cb: a clear human = never write");
        CHECK(kbr_cb_decide(1, 1, 0, 2, 0, 0, 0) == 1 && kbr_cb_decide(1, 1, 1, 0, 0, 0, 0) == 1, "cb: no fresh pass / nobody evaluated");
        CHECK(kbr_cb_decide(1, 1, 1, 2, 0, 0, 1) == 4 && kbr_cb_decide(1, 0, 1, 2, 0, 0, 0) == 5 && kbr_cb_decide(0, 1, 1, 2, 0, 0, 0) == 5 && kbr_cb_decide(4, 1, 1, 2, 0, 0, 0) == 5, "cb: already set, dead, mode off / unknown");
        CHECK(kbr_cb_decide(3, 1, 1, 2, 0, 0, 0) == 0 && kbr_cb_decide(3, 1, 1, 2, 0, 1, 0) == 0 && kbr_cb_decide(3, 1, 1, 2, 0, 0, 1) == 0, "cb3: write while 4fc or 6fc is missing, whatever 6fc was");
        CHECK(kbr_cb_decide(3, 1, 1, 2, 0, 1, 1) == 4 && kbr_cb_decide(3, 1, 1, 2, 1, 0, 0) == 2 && kbr_cb_decide(3, 1, 0, 2, 0, 0, 0) == 1 && kbr_cb_decide(3, 1, 1, 0, 0, 0, 0) == 1 && kbr_cb_decide(3, 0, 1, 2, 0, 0, 0) == 5, "cb3: both set = already, clear human, no pass, nobody blocked, dead");
        CHECK(kbr_hs_flags(1) == 0x01ul && kbr_hs_flags(2) == 0x15ul && kbr_hs_flags(0) == 0ul && kbr_hs_flags(3) == 0ul, "hs: flags per mode");
        CHECK(!kbr_hs_fires(kbr_hs_flags(1)) && !kbr_hs_fires(kbr_hs_flags(2)), "hs: neither value passes the fire test 0x616480");
        CHECK(kbr_hs_fires(0x11ul) && !kbr_hs_fires(0x15ul) && !kbr_hs_fires(0x251ul) && !kbr_hs_fires(0x211ul) && !kbr_hs_fires(0x51ul) && !kbr_hs_fires(0x10ul), "hs: fire test reference (0x11 passes; 0x4 / 0x40 / 0x200 or a missing bit fail)");
        CHECK(kbr_hs_decide(1, 1, 1, 2, 0, 1) == 0 && kbr_hs_decide(2, 1, 1, 1, 0, 1) == 0, "hs: write when all blocked and a human exists");
        CHECK(kbr_hs_decide(1, 1, 1, 2, 1, 1) == 2 && kbr_hs_decide(2, 1, 1, 0, 3, 1) == 1, "hs: a clear human = skip (nobody evaluated = no pass)");
        CHECK(kbr_hs_decide(1, 1, 0, 2, 0, 1) == 1 && kbr_hs_decide(1, 1, 1, 2, 0, 0) == 3 && kbr_hs_decide(1, 0, 1, 2, 0, 1) == 5 && kbr_hs_decide(0, 1, 1, 2, 0, 1) == 5 && kbr_hs_decide(3, 1, 1, 2, 0, 1) == 5, "hs: stale pass, no human, dead, off / unknown");
        CHECK(!kbr_hs_need(7, 1, 7, 1) && kbr_hs_need(0, 1, 7, 1) && kbr_hs_need(7, 0x201, 7, 1) && kbr_hs_need(8, 1, 7, 1), "hs: write only when handle or flags differ");
    }
    /* DefendProbe helpers */
    {
        long g[8] = { 3, 2, 0, 1, 0, 0, 4, 0 }, p8, p9, res; unsigned char st[40], o[6], nw[6]; kbr_u32 t[4] = { 0x1000, 0x2000, 0x3000, 0x4000 };
        const unsigned char jl[6] = { 0x0f, 0x8c, 0x15, 0x02, 0x00, 0x00 };
        CHECK(kbr_dp_c_active(1, 0) && !kbr_dp_c_active(1, 1) && !kbr_dp_c_active(0, 0) && !kbr_dp_c_active(0, 1), "dp: list C = byte set AND getter false");
        CHECK(kbr_dp_getter(0, 6) == 0 && kbr_dp_getter(0x1000, 6) == 1 && kbr_dp_getter(0x1000, 5) == 0, "dp: getter 0x575100 on data");
        CHECK(kbr_dp_index(t, 4, 0x3000) == 2 && kbr_dp_index(t, 4, 0x5000) == -1 && kbr_dp_index(t, 4, 0) == -1 && kbr_dp_index(t, 0, 0x1000) == -1, "dp: index of a tactic in a list");
        res = kbr_dp_split(20, g, 8, 9, 4, &p8, &p9);      /* sum(g) = 10, P9 = 9 - 4 = 5, P8 = 20 - 10 - 5 = 5 */
        CHECK(res == 0 && p9 == 5 && p8 == 5, "dp split: P9 from p8pass - ones, P8 = the rest");
        res = kbr_dp_split(10, g, 8, 2, 3, &p8, &p9);      /* ones > p8pass: P9 clamps to 0, P8 = 0 */
        CHECK(res == 0 && p9 == 0 && p8 == 0, "dp split: clamp, balanced");
        res = kbr_dp_split(8, g, 8, 0, 0, &p8, &p9);      /* sum 10 > 8 total (a call in flight): P8 clamps, residual negative */
        CHECK(res == -2 && p8 == 0 && p9 == 0, "dp split: residual shows an inconsistent count");
        CHECK(kbr_dp_taken_emit(st, 0x500000, 51, 0x401000, 0x672722) == 22, "dp taken stub: 22 bytes");
        CHECK(st[0] == 0x60 && st[1] == 0x9c && st[2] == 0x54 && st[3] == 0x6a && st[4] == 51 && st[5] == 0xb8 && st[6] == 0x00 && st[7] == 0x10 && st[8] == 0x40 && st[9] == 0 && st[10] == 0xff && st[11] == 0xd0 && st[12] == 0x83 && st[13] == 0xc4 && st[14] == 8 && st[15] == 0x9d && st[16] == 0x61 && st[17] == 0xe9, "dp taken stub: pushad pushfd push esp push id call popfd popad jmp");
        CHECK((kbr_u32)(0x500000 + 22 + (kbr_u32)(st[18] | (st[19] << 8) | (st[20] << 16) | ((kbr_u32)st[21] << 24))) == 0x672722u, "dp taken stub: jumps to the original target");
        memcpy(o, jl, 6);
        CHECK(kbr_dp_jcc_target(o, 0x672507) == 0x672722u, "dp jcc: original target of 0x672507 is the 0.0 tail");
        CHECK(kbr_dp_jcc(nw, o, 0x672507, 0x700000) == 1 && nw[0] == 0x0f && nw[1] == 0x8c && kbr_dp_jcc_target(nw, 0x672507) == 0x700000u, "dp jcc: same condition, retargeted to the stub");
        o[0] = 0x74; CHECK(!kbr_dp_jcc(nw, o, 0x6726b1, 0x700000) && kbr_dp_jcc_target(o, 0x6726b1) == 0, "dp jcc: a short jump (rel8) is refused");
    }
    /* RunProbe helpers */
    {
        CHECK(kbr_rp_elapsed(5000ul, 1000ul) == 4000ul && kbr_rp_elapsed(10ul, 0xfffffff0ul) == 26ul && kbr_rp_elapsed(1000ul, 5000ul) == 0ul && kbr_rp_elapsed(7ul, 7ul) == 0ul, "rp elapsed: plain, wrap, backwards = 0");
        CHECK(kbr_rp_next(0, 0) == 1 && kbr_rp_next(0, 99999) == 1, "rp next: phase 0 -> 1 at once");
        CHECK(kbr_rp_next(1, 4999) == 1 && kbr_rp_next(1, 5000) == 2 && kbr_rp_next(1, 20000) == 2, "rp next: +5 s");
        CHECK(kbr_rp_next(2, 14999) == 2 && kbr_rp_next(2, 15000) == 3 && kbr_rp_next(3, 0) == 3, "rp next: +15 s, done stays done");
        CHECK(kbr_rp_closed(500.0, 300.0) && !kbr_rp_closed(500.0, 500.0) && !kbr_rp_closed(500.0, 900.0) && !kbr_rp_closed(-1.0, 300.0) && !kbr_rp_closed(500.0, -1.0), "rp closed: d15 < d0, both known");
    }
    /* LOS helpers */
    {
        float a[3] = { 0, 150, 0 }, b[3] = { 300, 150, 400 }, c[3] = { 0, 150, 1000 }, dl[3] = { 9, 9, 9 }, ln = 0, nan3[3];
        unsigned int q = 0x7fc00000u; memcpy(&nan3[0], &q, 4); nan3[1] = 0; nan3[2] = 0;
        CHECK(kbr_los_delta(a, b, dl, &ln) && dl[0] == 300.0f && dl[2] == 400.0f && dl[1] == 0.0f && ln > 499.9f && ln < 500.1f, "los delta: length 500 is not shortened");
        CHECK(kbr_los_delta(a, c, dl, &ln) && dl[2] > 799.9f && dl[2] < 800.1f && dl[0] == 0.0f && ln > 999.9f && ln < 1000.1f, "los delta: 1000 -> 800 (stops 200 short)");
        dl[0] = 9;
        CHECK(!kbr_los_delta(a, a, dl, &ln) && !kbr_los_delta(a, nan3, dl, &ln) && !kbr_los_delta(nan3, a, dl, &ln) && dl[0] == 9.0f, "los delta: zero length / NaN refused, out untouched");
        CHECK(kbr_los_class(0, 0) == 0 && kbr_los_class(0, 1) == 1 && kbr_los_class(0, 0xffffff00u) == 0 && kbr_los_class(0, 0x80u) == 1 && kbr_los_class(-1, 1) == 2, "los class: al only, error 2");
    }
    /* OnlineBrainTraitorNoBoard */
    {
        CHECK(!kbr_nb_skip(0, 0, 1, 0, 1) && !kbr_nb_skip(3, 0, 1, 0, 1) && !kbr_nb_skip(-1, 0, 1, 0, 1), "noboard: mode 0 / out of range never skips");
        CHECK(kbr_nb_skip(1, 0, 1, 0, 1) && kbr_nb_skip(1, 1, 1, 0, 1) && !kbr_nb_skip(1, 2, 1, 0, 1), "noboard: mode 1 skips puppeteer and boardall, not pendBoard");
        CHECK(kbr_nb_skip(2, 0, 1, 0, 1) && kbr_nb_skip(2, 1, 1, 0, 1) && kbr_nb_skip(2, 2, 1, 0, 1) && !kbr_nb_skip(2, 3, 1, 0, 1), "noboard: mode 2 skips all three paths only");
        CHECK(!kbr_nb_skip(2, 0, 0, 0, 1) && !kbr_nb_skip(2, 0, 1, 1, 1) && !kbr_nb_skip(2, 0, 1, 0, 0), "noboard: needs Arcade, no TraitorTurn, a marked bot");
    }
    printf("klbrain_test: %d checks, %d FAIL\n", checks, fails);
    return fails ? 1 : 0;
}
