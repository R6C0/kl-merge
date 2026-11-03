/* klbrain_test.c - off-game harness for klbrain_logic.h ([Brain] vector insertion order, growth, switches, PuppetOff window). No windows.h.
   Build: cl /nologo /W3 klbrain_test.c /Fe:klbrain_test.exe     Run: klbrain_test.exe (exit 0 = all pass) */
#include <stdio.h>
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
        CHECK(kbr_bs_live(0, 1, 0, 5000, 0, 2500) && kbr_bs_live(0, 1, 0, 5000, 3001, 2500) && !kbr_bs_live(0, 1, 0, 5600, 3001, 2500), "grace: no evaluate yet waits grace_ms from the deferral start");
        CHECK(kbr_bs_live(0, 1, 0, 0x100ul, 0xfffffff1ul, 2500), "grace: tick wrap safe");
    }
    printf("klbrain_test: %d checks, %d FAIL\n", checks, fails);
    return fails ? 1 : 0;
}
