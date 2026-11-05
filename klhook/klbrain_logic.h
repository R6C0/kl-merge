/* klbrain_logic.h - [Brain] the PURE parts (no game memory, no log, no clock, no windows.h): where a hook-built tactic goes into a ZSoldier's
   AI vectors, the vector growth arithmetic, the key clamps and the "who is steered by the real brain" decision. Included by klbrain.c and klbrain_test.c.
   wk-brain-1102. Everything here comes from the ZSoldier ctor 0x6ab250 (read in disassembly 2026-11-02, see the block comment in klbrain.c):
   the ctor fills FOUR std::vector<ZTactic*>-like members (begin, last, end-of-capacity = three dwords) at soldier +0x604 (A), +0x610 (B), +0x61c (D)
   and +0x628 (C), each reserved to 10 elements first. The three tactic pointers (+0x5f8 Traitor, +0x5f4 Board, +0x5f0 Loot) are pushed into A, B and C
   (never D) between other members. ZDefendPosition (0x85f8e2) walks A / B / D and calls vtable slot 11 (evaluate) on every element.
   The order of the members in each vector, as the ctor pushes them (a member whose pointer is null is skipped by a test, the others are unconditional): */
#ifndef KLBRAIN_LOGIC_H
#define KLBRAIN_LOGIC_H

typedef unsigned long kbr_u32;
typedef unsigned short kbr_u16;

#define KBR_NVEC 3
#define KBR_VEC_A 0x604
#define KBR_VEC_B 0x610
#define KBR_VEC_C 0x628
#define KBR_F_LOOT 0x5f0
#define KBR_F_BOARD 0x5f4
#define KBR_F_TRAITOR 0x5f8

static const kbr_u16 kbr_ord_A[] = { 0x5ec, 0x5dc, 0x5f8, 0x5f4, 0x5ac, 0x5bc, 0x5b8, 0x590, 0x598, 0x59c, 0x5c0, 0x5b0, 0x5f0 };
static const kbr_u16 kbr_ord_B[] = { 0x5ec, 0x5dc, 0x5cc, 0x5f8, 0x5f4, 0x5ac, 0x5bc, 0x5b8, 0x594, 0x59c, 0x598, 0x5b0, 0x5c0, 0x5a0, 0x5f0 };
static const kbr_u16 kbr_ord_C[] = { 0x5dc, 0x5f8, 0x5f4, 0x5b8, 0x59c, 0x5c0, 0x5b0, 0x5f0 };
static const kbr_u16 *const kbr_ord[KBR_NVEC] = { kbr_ord_A, kbr_ord_B, kbr_ord_C };
static const int kbr_ordn[KBR_NVEC] = { (int)(sizeof kbr_ord_A / sizeof kbr_ord_A[0]), (int)(sizeof kbr_ord_B / sizeof kbr_ord_B[0]), (int)(sizeof kbr_ord_C / sizeof kbr_ord_C[0]) };
static const kbr_u16 kbr_vecoff[KBR_NVEC] = { KBR_VEC_A, KBR_VEC_B, KBR_VEC_C };

/* the members that come AFTER `field` in vector v's push order, offsets into out[]; returns how many (0 when field is not in that vector, or last) */
static int kbr_after(int v, kbr_u16 field, kbr_u16 *out, int cap)
{
    int i, n = kbr_ordn[v], k = -1, c = 0;
    for (i = 0; i < n; i++) if (kbr_ord[v][i] == field) { k = i; break; }
    if (k < 0) return 0;
    for (i = k + 1; i < n && c < cap; i++) out[c++] = kbr_ord[v][i];
    return c;
}

/* where to insert: the index of the FIRST element equal to any non-zero value of succ[] (the values of the members that follow in the ctor's order),
   else n (append). Elements already in the vector are compared by value, so a member the ctor skipped (null) simply matches nothing. */
static int kbr_insert_index(const kbr_u32 *el, int n, const kbr_u32 *succ, int ns)
{
    int i, j;
    for (i = 0; i < n; i++) for (j = 0; j < ns; j++) if (succ[j] && el[i] == succ[j]) return i;
    return n;
}

/* a vector header (begin, last, end) is plausible: aligned, ordered, non-empty reserve, at most 256 elements, last inside the reserve */
static int kbr_vec_ok(kbr_u32 b, kbr_u32 l, kbr_u32 e)
{
    if (!b || (b & 3) || (l & 3) || (e & 3)) return 0;
    if (l < b || e < l || e == b) return 0;
    if ((e - b) / 4 > 256) return 0;
    return 1;
}

/* the capacity (elements) a vector is regrown to when it is full: the ctor's own reserve is 10; double, at least 16, at most 256 (0 = refuse) */
static int kbr_grow_cap(int count)
{
    int c = count * 2;
    if (c < 16) c = 16;
    return c > 256 ? 0 : c;
}

/* insert v at idx of buf[0..n) (cap elements in the buffer); returns the new count, or -1 when idx > n or there is no room */
static int kbr_insert(kbr_u32 *buf, int n, int cap, int idx, kbr_u32 v)
{
    int i;
    if (idx < 0 || idx > n || n >= cap) return -1;
    for (i = n; i > idx; i--) buf[i] = buf[i - 1];
    buf[idx] = v;
    return n + 1;
}

/* the [Brain] switches after the dependencies: Loot needs Build, PuppetOff needs Loot (so Build); out[0..3] = Probe, Build, Loot, PuppetOff */
static void kbr_switches(int probe, int build, int loot, int puppet, int *out)
{
    out[0] = probe != 0; out[1] = build != 0; out[2] = out[1] && loot != 0; out[3] = out[2] && puppet != 0;
}

/* PuppetOff decision for one soldier: the puppeteer (klbotfill.c OnlineTactics) leaves it alone only while the REAL Loot tactic has shown it wants something:
   its evaluate returned > 0 within the last `win_ms` (0 = never). Without that the bot would stand idle, since an online evaluate answers 0 until the shadow
   rules carry money. now / at are GetTickCount values (unsigned wrap safe). */
static int kbr_puppet_released(int puppet_on, int built, unsigned long now, unsigned long nz_at, unsigned long win_ms)
{
    if (!puppet_on || !built || !nz_at) return 0;
    return (unsigned long)(now - (nz_at & ~1ul)) <= win_ms;      /* nz_at is stamped now|1: 1 ms ahead on an even tick would wrap (ce 95339b43f) */
}

/* ===== stage 2 / 3 (arcade-brain2-1103, design re/arcade_brain_stage2_1103.md): pure parts ======================================================================================== */

/* the full switch set after the dependencies. out[0..8] = Probe, Build, Loot, Bridge, Board, Traitor, PuppetOff, BoardReal, Cops.
   Board needs Build; Bridge needs Loot; Traitor needs Build + Bridge; PuppetOff needs Loot + Bridge (the money must count); BoardReal needs Board; Cops needs Bridge. */
#define KBR_S_PROBE 0
#define KBR_S_BUILD 1
#define KBR_S_LOOT 2
#define KBR_S_BRIDGE 3
#define KBR_S_BOARD 4
#define KBR_S_TRAITOR 5
#define KBR_S_PUPPET 6
#define KBR_S_BOARDREAL 7
#define KBR_S_COPS 8
#define KBR_NSW 9
static void kbr_switches2(int probe, int build, int loot, int bridge, int board, int traitor, int puppet, int boardreal, int cops, int *out)
{
    out[KBR_S_PROBE] = probe != 0; out[KBR_S_BUILD] = build != 0;
    out[KBR_S_LOOT] = out[KBR_S_BUILD] && loot != 0;
    out[KBR_S_BRIDGE] = out[KBR_S_LOOT] && bridge != 0;
    out[KBR_S_BOARD] = out[KBR_S_BUILD] && board != 0;
    out[KBR_S_TRAITOR] = out[KBR_S_BUILD] && out[KBR_S_BRIDGE] && traitor != 0;
    out[KBR_S_PUPPET] = out[KBR_S_LOOT] && out[KBR_S_BRIDGE] && puppet != 0;
    out[KBR_S_BOARDREAL] = out[KBR_S_BOARD] && boardreal != 0;
    out[KBR_S_COPS] = out[KBR_S_BRIDGE] && cops != 0;
}

/* re-entry: depth counter of the swap frame (game thread only). enter returns 1 for the OUTERMOST call (it swaps), 0 for a nested one (it must not swap again); leave returns 1 when the outermost ends */
static int kbr_frame_enter(int *depth) { return (*depth)++ == 0; }
static int kbr_frame_leave(int *depth) { if (*depth > 0) (*depth)--; return *depth == 0; }

/* the shadow data is stale (a sync is due) when older than age_ms; GetTickCount wrap safe; never synced = stale */
static int kbr_sync_stale(unsigned long now, unsigned long last, unsigned long age_ms) { return !last || (unsigned long)(now - last) > age_ms; }

/* money row of a shadow seat: the host ledger value clamped to a non-negative int (a bot that has no ledger slot reports -1 = 0) */
static long kbr_money_row(long ledger) { return ledger < 0 ? 0 : (ledger > 2000000000L ? 2000000000L : ledger); }

/* the Arcade level byte [S2+0x45] is clamped 1..11 (0x46d4d0 / 0x43ffb0) */
static int kbr_level_clamp(int lv) { return lv < 1 ? 1 : (lv > 11 ? 11 : lv); }

/* the van states the Board tactic walks in: 3 = waiting at the door, 4 = boarding (1 / 2 = called, not there yet) */
static int kbr_board_state_ok(int van) { return van == 3 || van == 4; }

/* grab precondition (0x6cdb40's own gates, bots_loot.md 66): record idle, session state 0x19, stack state 1, armed (+0x74), node not hidden, something left, our bit free, bot alive */
static int kbr_grab_ok(int rec_state, unsigned long round_state, int ctrl_state, int active, int hidden, long amount, int bit_free, int alive)
{
    return rec_state == 0 && round_state == 0x19ul && ctrl_state == 1 && active && !hidden && amount > 0 && bit_free && alive;
}

/* one grab tick. timer = seconds left for the current part; inside = the bot is in the ball; *outside = consecutive ticks outside (Arcade state-2 rule: one tick of grace).
   -> 0 keep, 1 pay a part (timer reached 0), 2 abort (taken / not state 1 / dead / left the ball for more than one tick) */
#define KBR_G_KEEP 0
#define KBR_G_PAY 1
#define KBR_G_ABORT 2
static int kbr_grab_step(float *timer, float dt, int inside, int *outside, int alive, int taken, int ctrl_state)
{
    if (taken || ctrl_state != 1 || !alive) return KBR_G_ABORT;
    if (!inside) { if (++*outside > 1) return KBR_G_ABORT; return KBR_G_KEEP; }
    *outside = 0;
    if (dt < 0) dt = 0;
    *timer -= dt;
    return *timer <= 0.0f ? KBR_G_PAY : KBR_G_KEEP;
}
/* part size of a grab: min(stack part size, what is left) and never negative */
static long kbr_part(long part, long remaining) { long p = part < remaining ? part : remaining; return p < 0 ? 0 : p; }

/* hand-off per tactic. loot_real: the real Loot tactic steers (PuppetOff semantics, kbr_puppet_released) and the van is not at 3 / 4 (Board owns the bot then);
   board_real: Board on, van in {3,4}, and a Board evaluate > 0 within board_win ms. At most one steerer: board_real wins over loot_real. */
static void kbr_hand(int puppet_on, int built, int board_on, unsigned long now, unsigned long loot_nz_at, unsigned long board_nz_at, int van, unsigned long loot_win, unsigned long board_win, int *loot_real, int *board_real)
{
    int b = board_on && built && kbr_board_state_ok(van) && board_nz_at && (unsigned long)(now - (board_nz_at & ~1ul)) <= board_win;      /* |1 stamp, see kbr_puppet_released */
    int l = kbr_puppet_released(puppet_on, built, now, loot_nz_at, loot_win) && !kbr_board_state_ok(van);
    *board_real = b; *loot_real = b ? 0 : l;
}

/* hand-off stall watchdog (review 11-03): a bot handed to the real tactic must show progress (moved >= 1 m since the last progress, a grab on, a slot-45 call) within stall_ms,
   else the hand-off is revoked for revoke_ms and the puppeteer steers it again. since = start of the current stall (0 none), until = revoked until (0 none). -> 1 the hand-off may stand. */
static int kbr_watch(unsigned long now, int handed, int progress, unsigned long *since, unsigned long *until, unsigned long stall_ms, unsigned long revoke_ms)
{
    if (*until) { if ((long)(now - *until) < 0) { *since = 0; return 0; } *until = 0; }
    if (!handed || progress) { *since = 0; return handed; }
    if (!*since) *since = now | 1ul;
    if ((unsigned long)(now - (*since & ~1ul)) >= stall_ms) {      /* the |1 marker may sit 1 ms ahead of now */ *since = 0; *until = (now + revoke_ms) | 1ul; return 0; }
    return 1;
}

/* the slow-frame rule (review 11-03): only `need` CONSECUTIVE frames over limit_us trip it (one dump write or hitch does not) -> 1 trip now */
static int kbr_slow_rule(unsigned us, unsigned limit_us, int *run, int need)
{
    if (us <= limit_us) { *run = 0; return 0; }
    return ++*run >= need;
}

/* the Loot tactic's chosen stack (review 11-03, read at 0x451b8a..0x451b94): [tactic+0x2c] = index 0..4 into the candidate array at tactic+0x14; [tactic+0x28] is the TRIGGER BOX
   (from 0x454c20), not the money ctrl. cand = the 5 dwords at +0x14. -> the ctrl, 0 when the index is out of range */
static unsigned long kbr_chosen(const unsigned long *cand, unsigned long idx) { return idx < 5 ? cand[idx] : 0; }

/* COROUTINE RULE (bs1 11-03, BS1B + BS1C host crash c0000029 in ntdll): the Loot RUN 0x7bc7d0 and the Board RUN 0x82f970 are stack-copying coroutines. Their yield
   0x55b9f0 does _setjmp3 into [[tactic+0xc]+0xc], copies the stack image to [ctx+0x40] and longjmps (msvcr90) to the scheduler's jmp_buf 0x168e4c8; the resumer
   (0x63c8d1) copies it back and longjmps into the RUN. A DLL __try / __finally frame live across that yield makes longjmp's RtlUnwind fail (STATUS_INVALID_UNWIND_TARGET),
   and a resumed slice runs on the REAL online rules where 0x508ef0 answers 0 and 0x78f470(ecx = 0) faults. So the DLL never CALLS those two originals itself: 1 = may call.
   RealRun (UNTESTED) does not change this: with it the DLL-owned vtable copy points slot 2 (Loot, Board) and Board slot 3 (EXIT 0x5478e0, which always runs in a resumed slice too)
   STRAIGHT at the originals (kbr_run_direct), so the scheduler calls them with no DLL frame, and the swap rides on the msvcr90 longjmp IAT thunk (kbr_lj_decide). */
static int kbr_orig_ok(int cls, int slot) { return !(slot == 0 && (cls == 0 || cls == 1)); }
/* RealRun: does the vtable copy's slot go straight to the original (no DLL frame at all)? cls 0 Loot, 1 Board, 2 Traitor; slot 0 = RUN (vt slot 2), 1 = EXIT (vt slot 3). Only the coroutine bodies: Loot RUN, Board RUN, Board EXIT */
static int kbr_run_direct(int realrun, int cls, int slot) { return realrun && ((slot == 0 && (cls == 0 || cls == 1)) || (slot == 1 && cls == 1)); }

/* RealRun: the msvcr90 longjmp thunk (kl2.exe has 3 call sites: yield 0x55ba52 and goal end 0x65bc8a -> longjmp(sched_buf 0x168e4c8, 1); resume 0x63c8d1 -> longjmp(ctx = [goal+0xc], 1 | 2)).
   -> KBR_LJ_RESTORE: leaving a slice to the scheduler while the shadow is swapped in: put the real rules back first. KBR_LJ_SWAP: resuming one of OUR Loot / Board coroutines
   (val 1 = RUN, 2 = EXIT; match = buf is the live ctx of a tactic we built): swap the shadow in first, unless it already is. Anything else passes through untouched. */
#define KBR_LJ_PASS 0
#define KBR_LJ_SWAP 1
#define KBR_LJ_RESTORE 2
static int kbr_lj_decide(unsigned long buf, int val, unsigned long sched_buf, int swapped, int match)
{
    if (!buf) return KBR_LJ_PASS;
    if (buf == sched_buf) return swapped ? KBR_LJ_RESTORE : KBR_LJ_PASS;
    if (!swapped && match && (val == 1 || val == 2)) return KBR_LJ_SWAP;
    return KBR_LJ_PASS;
}
/* restore only what is still ours: [G+0x54] only when it still reads the shadow, [sm+0x54] only when it still reads 0 (the swapped role). Anything else changed under us: leave it, count it. bit0 = restore rules, bit1 = restore role */
static int kbr_lj_restore_mask(unsigned long cur_rules, unsigned long shadow, unsigned long cur_role)
{
    return (cur_rules == shadow ? 1 : 0) | (cur_role == 0 ? 2 : 0);
}

/* ArcadePick: the stack the real Loot evaluate chose (kbr_chosen) still counts this long after it was stamped (now|1 stamp: masked, see kbr_puppet_released) */
static int kbr_pick_live(unsigned long now, unsigned long at, unsigned long win) { return at && (unsigned long)(now - (at & ~1ul)) <= win; }

/* StackClaims (bs4 11-03: several bots got the same nearest stack from slot 202, one grabbed, the rest stood at it until the watchdog took them back): stack c is claimed by ANOTHER bot when a
   claim i has ctrl[i] == c, owner[i] != me, and is either a grab (at[i] == 0, always counts) or a pick stamped within win (now|1 stamp masked). Picks count only with picks != 0 and me != 0 (caller known) */
static int kbr_claimed(unsigned long c, unsigned long me, int picks, const unsigned long *ctrl, const unsigned long *owner, const unsigned long *at, int n, unsigned long now, unsigned long win)
{
    int i;
    for (i = 0; i < n; i++) {
        if (!c || ctrl[i] != c || owner[i] == me) continue;
        if (!at[i]) return 1;
        if (picks && me && (unsigned long)(now - (at[i] & ~1ul)) <= win) return 1;
    }
    return 0;
}

/* BoardStage: the crew-record stage byte [rec+0x78] the shadow shows the real Board tactic. 3 = aboard (as before); with board_stage ALSO 3 while the van is called / waiting (kbr_board_state_ok) and the bot
   carries loot (tally > 0) or is inside / ordered to the exit box (exit_ordered). Otherwise 2 carrying (tally > 0) / 1 looting. GUESS: the real Board evaluate is gated on stage 3 = "reached the exit / van called" (static reading only) */
static int kbr_stage_byte(int board_stage, int aboard, long tally, int van, int exit_ordered)
{
    if (aboard) return 3;
    if (board_stage && kbr_board_state_ok(van) && (tally > 0 || exit_ordered)) return 3;
    return tally > 0 ? 2 : 1;
}

/* OnlineBrainTraitorStage2Gate (11-04, UNTESTED): Arcade shows stage 2 to the Traitor evaluate only around the van call / exit trigger, online it was 2 from the first loot (score 7.0 at $1M, marks ~60-90 s in).
   gate 0 = the byte unchanged. gate 1 = a byte of 2 (carrying, not aboard) drops to 1 unless an opener holds: van called or gather running (open), bot ordered to the exit box (exit_ordered), or its tally has reached
   money_fb (> 0; 0 = no fallback). 0, 1 and 3 pass through untouched (stage 3 = aboard / board-ready, stage 0/1 = not carrying). */
static int kbr_stage_gate(int gate, int stage, long tally, int open, int exit_ordered, long money_fb)
{
    if (!gate || stage != 2) return stage;
    if (open || exit_ordered) return stage;
    if (money_fb > 0 && tally >= money_fb) return stage;
    return 1;
}

/* The whole stage-byte composition the sync uses (pure, so the wiring is testable): kbr_stage_byte, then (gate on) kbr_stage_gate. Opener = hook's van called / gather (hook_open) OR the REAL van state
   1..4 (a human's exit trigger sets no hook flag, Arcade opens on any trigger). ex = BoardStage's exit-ordered answer; without BoardStage the gate's own exit-box answer (ob_called) is used. */
static int kbr_stage_compose(int gate, int board_stage, int aboard, long tally, int van, int ob_called, int hook_open, long money_fb)
{
    int ex = board_stage ? ob_called : 0, st = kbr_stage_byte(board_stage, aboard, tally, van, ex);
    if (gate) st = kbr_stage_gate(1, st, tally, hook_open || (van >= 1 && van <= 4), ex || (!board_stage && ob_called), money_fb);
    return st;
}

/* OnlineBrainTraitorStage2MinS / MaxS (11-05, UNTESTED): a time window around the Stage2Gate. gate 0, or elapsed_s < 0 (round clock unknown), or both min_s and max_s 0 = kbr_stage_compose exactly.
   Otherwise, for a bot whose UNGATED byte is 2 (carrying, not aboard): elapsed < min_s (> 0) -> 1 whatever the openers say (money fallback, van call, exit box included); elapsed >= max_s (> 0, and
   not below min_s) -> 2 even with no opener (no-gather fallback); otherwise the gated byte. *ev (may be null): 1 = MinS held back a byte the gate would have shown as 2, 2 = MaxS opened a byte the gate
   would have shown as 1, else 0. Stage 0/1/3 pass through. The 150 / 240 s figures in KLHook.ini are a GUESS from Arcade's first traitor mark (150-240 s after round start). */
static int kbr_stage_compose_w(int gate, int board_stage, int aboard, long tally, int van, int ob_called, int hook_open, long money_fb, long elapsed_s, long min_s, long max_s, int *ev)
{
    int st = kbr_stage_compose(gate, board_stage, aboard, tally, van, ob_called, hook_open, money_fb);
    if (ev) *ev = 0;
    if (!gate || elapsed_s < 0 || (min_s <= 0 && max_s <= 0)) return st;
    if (kbr_stage_compose(0, board_stage, aboard, tally, van, ob_called, hook_open, money_fb) != 2) return st;
    if (min_s > 0 && elapsed_s < min_s) { if (st == 2 && ev) *ev = 1; return 1; }
    if (max_s > 0 && elapsed_s >= max_s) { if (st == 1 && ev) *ev = 2; return 2; }
    return st;
}

/* MinS mark hold (11-05, bs66): 1 = the Traitor evaluate answer must be held at 0 (no mark) now. Only with the gate on, min_s > 0 and a known round clock (elapsed_s >= 0) and elapsed_s < min_s;
   whatever the stage byte is (a board-ready bot shows byte 3, which the real Board tactic also reads, so the byte itself is not floored). gate 0 / min_s 0 / unknown clock = 0 = no change. */
static int kbr_mark_held(int gate, long elapsed_s, long min_s)
{
    return gate && min_s > 0 && elapsed_s >= 0 && elapsed_s < min_s;
}

/* MinS van release (11-05, bs72): with van_release on, a called van (state 1..4, the same range that opens the stage gate) ends the MinS hold early. bs72 DM03: all 7 bots boarded at +131 s and the
   crew's evaluates stopped at +135 s, so MinS 150 left nothing to mark; Arcade DM03 marks +118..166 s, mostly around the van call. Needs NoBoard=2 (a bot marked before boarding was ghost-boarded, bs69). */
static int kbr_mark_held_v(int gate, long elapsed_s, long min_s, int van, int van_release)
{
    if (van_release && van >= 1 && van <= 4) return 0;
    return kbr_mark_held(gate, elapsed_s, min_s);
}

/* Mark spacing (11-05, bs71): 1 = hold the Traitor evaluate at 0 now because the previous mark of this round is less than gap_ms old. Arcade marks 1-5 traitors spaced >= ~0.5 s;
   the MinS hold released every waiting bot in one tick (bs71: 3 marks at once). last_ms 0 = no mark yet this round; gap_ms <= 0 = off. Unsigned tick math survives the 49-day wrap. */
static int kbr_mark_spaced(unsigned long now_ms, unsigned long last_ms, long gap_ms)
{
    return gap_ms > 0 && last_ms != 0 && (unsigned long)(now_ms - last_ms) < (unsigned long)gap_ms;
}

/* BoardStage: should the hook's own boarding path (klbotfill.c) wait for the real Board tactic? live = the real tactic holds the bot now (fresh Board evaluate > 0, not revoked). *since = tick the deferral
   began (0 none; |1 stamp). Defers up to max_ms per bot, then -> 0 (fall back, so no bot is stranded). A tactic that stops being live ends the deferral at once (-> 0); the clock is NOT reset by that, so the per-bot total stays capped. */
/* BoardStage grace (review 11-03 defect 1): a bot can stand in the box before its first nonzero Board evaluate (stage 3 is shown by the 1 s sync only). While the van waits (staged) and the bot has
   no Board evaluate yet, it counts as live for grace_ms from the start of its deferral, so the real tactic gets one chance. A bot the tactic already evaluated nonzero (has_bnz) gets no grace. */
static int kbr_bs_live(int live, int staged, int has_bnz, unsigned long now, unsigned long since, unsigned long grace_ms)
{
    if (live) return 1;
    if (!staged || has_bnz) return 0;
    return !since || (unsigned long)(now - (since & ~1ul)) < grace_ms;
}
/* BoardHold: the real Board tactic keeps a bot for hold_ms after its LAST nonzero Board evaluate or RUN-resume stamp (bnzAt, |1 stamped), not only BoardWinMs: bs6 DD05 / DM03 showed bots whose RUN was
   mid-walk with a bnzAt older than BoardWinMs (GUESS: the planner re-evaluates 0-2 times per second there). 0 hold_ms = off. Needs the van waiting (staged). */
static int kbr_bs_hold(unsigned long now, unsigned long bnz_at, int staged, unsigned long hold_ms)
{
    return hold_ms && staged && bnz_at && (unsigned long)(now - (bnz_at & ~1ul)) < hold_ms;
}
static int kbr_bs_defer(int on, int live, unsigned long now, unsigned long *since, unsigned long max_ms)
{
    if (!on || !live) return 0;
    if (!*since) *since = now | 1ul;
    return (unsigned long)(now - (*since & ~1ul)) < max_ms;
}

/* keep the cap nearest objects of obj[0..n) by squared distance d2 (ties: the lower index first), written to out[0..cap), tail zero-filled; returns how many were kept */
static int kbr_cand_sort(const unsigned long *obj, const float *d2, int n, unsigned long *out, int cap)
{
    float kd[16]; int i, k, c = 0;
    if (cap > 16) cap = 16;
    for (k = 0; k < cap; k++) out[k] = 0;
    for (i = 0; i < n; i++) {
        int at = c;
        if (!obj[i]) continue;
        for (k = 0; k < c; k++) if (d2[i] < kd[k]) { at = k; break; }      /* strict <: an equal distance goes behind the earlier index */
        if (at >= cap) continue;
        for (k = (c < cap ? c : cap - 1); k > at; k--) { out[k] = out[k - 1]; kd[k] = kd[k - 1]; }
        out[at] = obj[i]; kd[at] = d2[i]; if (c < cap) c++;
    }
    return c;
}

/* DropCands (bs4c DD05: cops carry the loot, every stack drains into a type-1 drop within ~20 s, slot 202 returned 0 candidates): may a type-1 drop be offered? Armed, amount left, node hidden bit clear
   (hidden: 0 = clear; 1 / -1 unreadable = no) and tracked_ok = the OnlineDropFollow rule (kdf_drop_ok: unhidden AND preceded by a real stack drain; klbotfill.c). A type-0/2 stack is never judged here */
static int kbr_drop_valid(int armed, long amt, int hidden, int tracked_ok)
{
    return armed && amt > 0 && hidden == 0 && tracked_ok;
}

/* ---- OnlineBrainTraitorTurn (2026-11-03; design re/ + scratchpad traitor_design.md / traitor_refute.md) -------------------------------------------------------------------------------- */
/* diagnostics: take one of the first `cap` log slots of a counter (1 = log this one) */
static int kbr_diag_take(int *n, int cap) { if (*n >= cap) return 0; (*n)++; return 1; }

/* row 0 of the shadow money row = "the player" of Arcade's Traitor evaluate. mode 0 = the host (seat 0; else the first used seat), 1 = the richest used human. money[i] / used[i] for seats 0..n-1;
   *which = the seat chosen (-1 none -> 0). Negative money counts as 0. GUESS: seat 0 is the host on the Sv rules */
static long kbr_row0_money(int mode, const long *money, const unsigned char *used, int n, int *which)
{
    int i, best = -1;
    for (i = 0; i < n; i++) {
        if (!used[i]) continue;
        if (best < 0) { best = i; if (mode == 0) break; continue; }
        if (mode == 1 && money[i] > money[best]) best = i;
    }
    *which = best;
    return best < 0 ? 0 : (money[best] < 0 ? 0 : money[best]);
}

/* the Traitor evaluate's score at level 6-8 as read in the disassembly (bots_behaviour 1.3): stage term (from the tuning row) + bot money term (0..3 against 750k / 1.0M / 1.25M) + player money term (3..0 against the
   same limits). GUESS: the comparisons are >= and the thresholds are the same at every level (only read for 6-8). Diagnostic only: the game computes its own */
static int kbr_tr_bot_term(long m) { return m >= 1250000L ? 3 : m >= 1000000L ? 2 : m >= 750000L ? 1 : 0; }
static int kbr_tr_pl_term(long m) { return 3 - kbr_tr_bot_term(m); }
static float kbr_tr_sum(float stage_term, long bot, long player) { return stage_term + (float)kbr_tr_bot_term(bot) + (float)kbr_tr_pl_term(player); }

/* why a turned bot goes back to his own team (priority order); 0 = stays turned. Inputs: dead, aboard, bot still tracked (klbr state 1), round still running (role 2, mode 4, state 0x19, same session), actor and team object unchanged */
#define KBR_TB_DEAD 1
#define KBR_TB_ABOARD 2
#define KBR_TB_STATE 3
#define KBR_TB_ROUND 4
#define KBR_TB_CHANGED 5
static const char *const kbr_tb_name[] = { "", "he is dead", "he is aboard", "the bot is no longer tracked", "the round is not running", "the actor or its team object changed" };
static int kbr_tr_back_why(int dead, int aboard, int tracked, int round_ok, int same)
{
    if (!round_ok) return KBR_TB_ROUND;
    if (!same) return KBR_TB_CHANGED;
    if (dead) return KBR_TB_DEAD;
    if (aboard) return KBR_TB_ABOARD;
    if (!tracked) return KBR_TB_STATE;
    return 0;
}

/* TraitorKillMax: a crew death is booked to the nearest live turned bot within `rng`; d[i] < 0 = unknown / not a candidate. -1 = none */
static int kbr_tr_nearest(const float *d, int n, float rng)
{
    int i, best = -1;
    for (i = 0; i < n; i++) if (d[i] >= 0.0f && d[i] <= rng && (best < 0 || d[i] < d[best])) best = i;
    return best;
}
/* kills booked to a turned bot after this death; 1 when the cap is reached (max <= 0 = no cap, never) */
static int kbr_tr_capped(int kills, int max) { return max > 0 && kills >= max; }

/* optional hard cap on turns per round through [shadow+0x338] (0x43ffb0 tests `[rules+0x338] < tuning[R+0x6c]`): 0 = leave (cap off or still room), 0x7fff = block every further roll once `turned` reached `cap` */
static unsigned long kbr_tr_cap_word(int turned, int cap) { return cap > 0 && turned >= cap ? 0x7ffful : 0ul; }

/* ArcadeDiag (read-only reference numbers from stock Arcade). The game's own money read, vt[0xe0] 0x6f86c0, answers -1 (0xffffffff) for an unused slot and the threshold compares are UNSIGNED (jae at 0x79b8e9..0x79b923,
   traitor_cap_1103.md refute item 6), so an unused slot scores own term 3 / other term 0. GUESS: the "unused" test is `free byte != 0 or slot >= count` as the shadow block assumes ([rules+0x34c] bytes, [rules+0x354] count) */
static int kbr_ad_slot_ok(unsigned long slot, unsigned long nrec) { return slot < nrec && slot < 64ul; }
static int kbr_ad_unused(unsigned freebyte, unsigned long slot, unsigned long nrec) { return slot >= nrec || freebyte != 0; }
static long kbr_ad_money(long raw, int unused) { return unused ? -1L : raw; }
static int kbr_ad_term_u(long m) { unsigned long u = (unsigned long)m; return u >= 1250000ul ? 3 : u >= 1000000ul ? 2 : u >= 750000ul ? 1 : 0; }
static int kbr_ad_stage_ix(int stage) { return stage >= 0 && stage <= 3 ? stage : 0; }      /* jump table 0x79b970: stage > 3 takes the stage-0 term (R+0x24) */
static float kbr_ad_sum(const float *st4, int stage, long bot, long player) { return st4[kbr_ad_stage_ix(stage)] + (float)kbr_ad_term_u(bot) + (float)(3 - kbr_ad_term_u(player)); }
/* the evaluate answers 1.0 iff sum >= limit (fcompp at 0x79b956: equal also passes, refute item 5) */
static int kbr_ad_pass(float sum, float limit) { return !(sum < limit); }
/* a Traitor mark: bit 1 of rec+0x79 rose since the last poll (seen = the last polled byte) */
static int kbr_ad_rose(unsigned seen, unsigned now_b) { return (now_b & 2u) && !(seen & 2u); }

/* OnlineBrainTraitorArcade (2026-11-03; re/arcade_traitor_consequence_1103.md): the wrapped ZSoldier slot 111 (target score 0x882470) of a bot the real Traitor RUN marked.
   ARCADE = run the original with the shadow rules swapped in (so 0x7f6850 and the record read at 0x8826b6 answer as in Arcade); PASS = call the original untouched. Only a marked bot of ours, in a host
   round, with the feature on, with OnlineBrainTraitorTurn off (exclusive: Arcade never swaps the team), against a readable ZFFPlayer body (vtable 0xbb45f4, read through klh_pvt). */
#define KBR_TA_PASS 0
#define KBR_TA_ARCADE 1
static int kbr_tarc_decide(int enabled, int marked, int shooterOurs, unsigned long targetVt, unsigned long playerVt, int targetReadable, int turnOn, int hostRound)
{
    if (!enabled || !hostRound || !marked || !shooterOurs || turnOn) return KBR_TA_PASS;
    if (!targetReadable || targetVt != playerVt) return KBR_TA_PASS;
    return KBR_TA_ARCADE;
}

/* OnlineBrainTraitorFireLine (2026-11-03; re/fireline_gap_1103.md H1): ZSoldier slots 113 / 114 (the fire-line friend list callers) of a marked bot.
   mode 0 = off, 1 = LOG ONLY (original untouched), 2 = SWAP (original with the shadow rules in, as slot 111). Needs OnlineBrainTraitorArcade on (taOn), a marked bot of ours, a host round and
   Turn off (exclusive, like slot 111). */
#define KBR_TFL_PASS 0
#define KBR_TFL_LOG 1
#define KBR_TFL_SWAP 2
static int kbr_tfl_decide(int mode, int taOn, int marked, int shooterOurs, int turnOn, int hostRound)
{
    if (mode < 1 || !taOn || !hostRound || !marked || !shooterOurs || turnOn) return KBR_TFL_PASS;
    return mode >= 2 ? KBR_TFL_SWAP : KBR_TFL_LOG;
}

/* ---- OnlineBrainTraitorHitLog probe + OnlineBrainTraitorDamage (2026-11-03; re/fireline_goal_path_1103.md section D / Verification 2). Pure decisions, no game access. ---- */
#define KBR_TG_NONE 0
#define KBR_TG_HUMAN 1
#define KBR_TG_BOT 2
#define KBR_TG_COP 3
#define KBR_TG_OTHER 4
/* the soldier's target field is valid while the game clock [[0xdd2640]+0x48] < [soldier+0x70c] (0x5da810, signed compare jge) */
static int kbr_tgt_valid(long clock, long stamp) { return clock < stamp; }
/* have: valid and non-null; player: the object is a ZFFPlayer body; taggedBot: it maps to a tagged bot (klbr_hl_body / klbr_hl_find); police: body byte +0x2723; ai: ZFFActor / ZSoldier object */
static int kbr_tgt_class(int have, int player, int taggedBot, int police, int ai)
{
    if (!have) return KBR_TG_NONE;
    if (taggedBot) return KBR_TG_BOT;
    if (player) return police ? KBR_TG_COP : KBR_TG_HUMAN;
    return ai ? KBR_TG_COP : KBR_TG_OTHER;      /* GUESS: a non-player AI target is a cop (or an untagged bot) */
}
static const char *kbr_tgt_name(int c) { return c == KBR_TG_HUMAN ? "human" : c == KBR_TG_BOT ? "tagged bot" : c == KBR_TG_COP ? "cop" : c == KBR_TG_OTHER ? "other" : "none"; }
/* a once-per-gap limiter; last 0 = never; unsigned wrap safe */
static int kbr_rate_ok(unsigned long last, unsigned long now, unsigned long gap) { return !last || (unsigned long)(now - last) >= gap; }
/* health drop between two reads (positive = lost health) */
static float kbr_hp_drop(float before, float after) { return before - after; }
/* OnlineBrainTraitorDamage: what to do with the marked bot body's +0x2726 byte before a hit */
#define KBR_DM_SKIP 0
#define KBR_DM_SET 1
#define KBR_DM_HAVE 2
static int kbr_dm_decide(int on, int marked, int bodyOk, int cur)
{
    if (!on || !marked || !bodyOk || cur < 0) return KBR_DM_SKIP;
    return cur != 0 ? KBR_DM_HAVE : KBR_DM_SET;      /* any nonzero byte already passes 0x6e3400's cmp byte,0: nothing to write, remember or restore */
}
/* restore only a byte that still holds our 1 (never overwrite what someone else wrote since) */
static int kbr_dm_restore_ok(int cur) { return cur == 1; }


/* OnlineBrainTraitorCandLog / OnlineBrainTraitorSense (2026-11-03; re/traitor_candidates_1103.md, re/traitor_senses_1103.md). Pure parts only. */
#define KBR_CC_PLAYER 0
#define KBR_CC_ACTOR 1
#define KBR_CC_SOLDIER 2
#define KBR_CC_OTHER 3
#define KBR_CC_N 4
#define KBR_CC_SEEN 6
/* candidate class from three vtable tests (ZFFPlayer 0xbb45f4, ZFFActor 0xbb3bac, ZSoldier 0xbd0954): player first */
static int kbr_cand_class(int isPlayer, int isActor, int isSoldier) { return isPlayer ? KBR_CC_PLAYER : isActor ? KBR_CC_ACTOR : isSoldier ? KBR_CC_SOLDIER : KBR_CC_OTHER; }
static const char *kbr_cand_name(int c) { return c == KBR_CC_PLAYER ? "ZFFPlayer" : c == KBR_CC_ACTOR ? "ZFFActor" : c == KBR_CC_SOLDIER ? "ZSoldier" : "other"; }
/* remember a distinct candidate: 1 = new and stored (at most KBR_CC_SEEN), 0 = already known, full or null */
static int kbr_cand_note(kbr_u32 *seen, int *n, kbr_u32 cand)
{
    int i;
    if (!cand) return 0;
    for (i = 0; i < *n; i++) if (seen[i] == cand) return 0;
    if (*n >= KBR_CC_SEEN) return 0;
    seen[(*n)++] = cand; return 1;
}
/* known-entities list B = [soldier+0x698] (count dword at +0, 0x14-byte entries from +4, entity at entry+4, type dword at entry+8 = the jump index at 0x7bd770, timestamp at +0xc; offsets read from 0x7bd770..0x7bd789, that 'type 2' is ZFFPlayer is research A's reading, count capped at 10):
   how many entries of type 2 (ZFFPlayer per research A); count is clamped to 0..10, a negative or absurd count counts as 0 */
static int kbr_list_count(long count) { return count < 0 || count > 10 ? 0 : (int)count; }
static int kbr_list_type2(const long *types, int n) { int i, c = 0; for (i = 0; i < n && i < 10; i++) if (types[i] == 2) c++; return c; }
/* OnlineBrainTraitorSense: feed a human body into a marked bot's known list (B::NoteEntity 0x7bd720). Everything must hold. */
#define KBR_SN_SKIP 0
#define KBR_SN_FEED 1
static int kbr_sense_decide(int enabled, int hostRound, int marked, int wrapped, int alive, int turnOn, int bodyIsPlayer, int bodyIsTaggedBot, int police, int rateOk)
{
    if (!enabled || !hostRound || !marked || !wrapped || !alive || turnOn || !rateOk) return KBR_SN_SKIP;
    if (!bodyIsPlayer || bodyIsTaggedBot || police) return KBR_SN_SKIP;
    return KBR_SN_FEED;
}
/* at most this many humans are fed per bot: the known list holds 10 and a full list evicts the oldest entry (review 11-03) */
#define KBR_SN_MAXFEED 4
/* indexes (into d[0..n-1]) of the up-to-maxn smallest distances, nearest first; ties keep list order; returns the count */
static int kbr_sense_nearest(const float *d, int n, int maxn, int *out)
{
    int c = 0, i, j;
    for (i = 0; i < n; i++) {
        for (j = c; j > 0 && d[out[j - 1]] > d[i]; j--) if (j < maxn) out[j] = out[j - 1];
        if (j < maxn) { out[j] = i; if (c < maxn) c++; }
    }
    return c;
}
/* the feed key clamp: interval in ms, 200..5000, default 500 */
static int kbr_sense_ms(long v) { return v < 200 || v > 5000 ? 500 : (int)v; }

/* OnlineBrainTraitorFireProbe3 (11-04): a counting detour on a game function. The stub at 'at' (the address it will run from) saves the registers in pushad + pushfd order, calls
   handler(id, regs) (cdecl), restores them, runs the 'len' stolen prologue bytes and jumps back to 'back'. Returns the bytes written (17 + len + 5). The stolen bytes must
   hold no relative operand (the caller checks them with the disassembler). Layout: 60 9C 54 6A id B8 handler FF D0 83 C4 08 9D 61 <stolen> E9 rel32. */
#define KBR_F3_MAXSTUB 40
static int kbr_f3_emit(unsigned char *p, kbr_u32 at, int id, kbr_u32 handler, const unsigned char *stolen, int len, kbr_u32 back)
{
    static const unsigned char pre[5] = { 0x60, 0x9c, 0x54, 0x6a, 0 }; int n = 0, i; kbr_u32 rel;
    if (len < 5 || len > 10) return 0;
    for (i = 0; i < 5; i++) p[n++] = pre[i];
    p[4] = (unsigned char)id;
    p[n++] = 0xb8; for (i = 0; i < 4; i++) p[n++] = (unsigned char)(handler >> (8 * i));
    p[n++] = 0xff; p[n++] = 0xd0; p[n++] = 0x83; p[n++] = 0xc4; p[n++] = 0x08; p[n++] = 0x9d; p[n++] = 0x61;
    for (i = 0; i < len; i++) p[n++] = stolen[i];
    rel = back - (at + (kbr_u32)n + 5);
    p[n++] = 0xe9; for (i = 0; i < 4; i++) p[n++] = (unsigned char)(rel >> (8 * i));
    return n;
}
/* the jump written over the function's first 'len' bytes: E9 rel32 (to the stub) then NOPs */
static void kbr_f3_jmp(unsigned char *out, kbr_u32 fn, kbr_u32 stub, int len)
{
    int i; kbr_u32 rel = stub - (fn + 5);
    out[0] = 0xe9; for (i = 0; i < 4; i++) out[1 + i] = (unsigned char)(rel >> (8 * i));
    for (i = 5; i < len; i++) out[i] = 0x90;
}
/* per-round histogram of return addresses: counts one more call from 'ra'; returns 1 when it was a new address, 0 when known or the table (cap entries) is full (the count of 'lost' is the caller's) */
static int kbr_f3_ra_add(kbr_u32 *ra, long *cnt, int *n, int cap, kbr_u32 r)
{
    int i;
    for (i = 0; i < *n; i++) if (ra[i] == r) { cnt[i]++; return 0; }
    if (*n >= cap) return 0;
    ra[*n] = r; cnt[*n] = 1; (*n)++;
    return 1;
}
/* ammo word of an item: stored xor 0xbeebbeeb (verify note 11-04) */
static kbr_u32 kbr_f3_ammo(kbr_u32 raw) { return raw ^ 0xbeebbeebUL; }

/* OnlineBrainTraitorFireProbe5 (11-04): the victim hit routing of the ZFFPlayer router, slot 422 = 0x7e1700 (this = victim V, one stack arg = record R, [R] = attacker A), read from the disassembly (not a trace):
     1. 0x863a60([sm]) = (role [sm+0x54] is 2 or 3); false -> 0x7e181f: vt+0x69c(R) = APPLY (route 0)
     2. V vt+0x3d0 (0x4cee60) = bit 18 of [V+0x438]; true -> vt+0x69c(R) = APPLY (route 1)
     3. A non-null and A's class mask test passes (0x7e1750: (A vt+0x30)() & [0x1548c80] == [0x1548c7c]; GUESS: that is 'A is a ZFFPlayer', the caller passes att_player) ->
        0x7de570([A+0x274c]) true -> return, DROP (route 2); false -> the send block 0x7a8410, no direct apply (route 3)
     4. else (A null, or not that class) 0x7de570([V+0x274c]) true -> return, DROP (route 4); false -> vt+0x69c(R) = APPLY (route 5)
   0x7de570(st) = st != 0 && !0x9425a0(st);  0x9425a0(st) = [st+0x14] != 0 && (local == 0 || [st+0x14] == local), local = [0x168fd00] (0x94bc10 with 0x744a40() == 0, always). So remote(st) =
   st set && (id == 0 || (local != 0 && id != local)). */
static int kbr_f5_remote(int st_set, kbr_u32 id, kbr_u32 local) { return st_set && (id == 0 || (local != 0 && id != local)); }
static int kbr_f5_route(kbr_u32 role, int bit18, int att_set, int att_player, int att_st_set, kbr_u32 att_id, int vst_set, kbr_u32 vid, kbr_u32 local)
{
    if (role != 2 && role != 3) return 0;
    if (bit18) return 1;
    if (att_set && att_player) return kbr_f5_remote(att_st_set, att_id, local) ? 2 : 3;
    return kbr_f5_remote(vst_set, vid, local) ? 4 : 5;
}
static int kbr_f5_applies(int route) { return route == 0 || route == 1 || route == 5; }
static const char *kbr_f5_route_name(int r)
{
    return r == 0 ? "apply (session not networked)" : r == 1 ? "apply (victim bit 18)" : r == 2 ? "DROP (attacker is a player on a remote station)" : r == 3 ? "send block (attacker is a locally owned player; no direct apply)" :
           r == 4 ? "DROP (victim station remote: id 0 or not the local id)" : r == 5 ? "apply (victim station local or null)" : "unknown";
}
/* is [va, va+len) inside any of n ranges [lo, hi)? (the klh_is_hashed rule, as a pure helper for the test: FireProbe5 refuses a hashed site) */
static int kbr_f5_in_ranges(const kbr_u32 (*r)[2], int n, kbr_u32 va, kbr_u32 len)
{
    int i;
    for (i = 0; i < n; i++) if (va < r[i][1] && va + len > r[i][0]) return 1;
    return 0;
}
/* the gate byte [esp+0x1f] counted per round: kind 0 marked pass, 1 marked fail, 2 other pass, 3 other fail */
static int kbr_f5_kind(int marked, unsigned gate) { return (marked ? 0 : 2) + (gate ? 0 : 1); }

/* OnlineBrainTraitorFireProbe4 (11-04): pure helpers. bit n of a dword; delta of a counter against its previous sample (first sample = 0, a counter that went down = 0); the route of a hit by a BOT (not a ZFFPlayer)
   on a human ZFFPlayer, now exact (FireProbe5's reading of 0x7e1700, kbr_f5_route with a non-player attacker): 0 apply-local (victim+0x438 bit 18 set), 1 drop (victim station remote), 2 apply (station local or null),
   3 apply (session not networked) */
static int kbr_f4_bit(kbr_u32 v, int n) { return (int)((v >> n) & 1u); }
static kbr_u32 kbr_f4_delta(int have_prev, kbr_u32 prev, kbr_u32 cur) { return (have_prev && cur >= prev) ? cur - prev : 0; }
static int kbr_f4_route(kbr_u32 role, int bit18, int station_set, kbr_u32 station_id, kbr_u32 local)
{
    switch (kbr_f5_route(role, bit18, 1, 0, 0, 0, station_set, station_id, local)) { case 0: return 3; case 1: return 0; case 4: return 1; default: return 2; }
}
static const char *kbr_f4_route_name(int r) { return r == 0 ? "apply-local (bit18)" : r == 1 ? "drop (bot attacker, victim station remote: id 0 or not the local id)" : r == 2 ? "apply (station local or null)" : r == 3 ? "apply (session not networked)" : "unknown"; }

/* OnlineBrainTraitorGateForce (11-04): pure decision of the class-getter wrapper. The game's per-shot routine 0x4cb7a0 calls the owner's vt+0x30 at 0x4cb819 (return address 0x4cb81b) and, when
   (result & [0x153a89c]) == [0x153a898] (the ZLNKOBJ test, 0xfff / 0x77c), forces its gate byte to 1 itself. Returns the value to hand back (cls_val, which passes that test) or 0 = leave the real answer.
   Only for that one return address, for a marked bot (or, with 'all', any bot on the OnlineCopToBot table), and only when cls_val is a subset of the mask (else the forced value could not pass). */
static kbr_u32 kbr_gf_force(int on, int all, int marked, int isbot, kbr_u32 ra, kbr_u32 want_ra, kbr_u32 cls_val, kbr_u32 cls_mask)
{
    if (!on || ra != want_ra || !cls_val || (cls_val & cls_mask) != cls_val) return 0;
    return (marked || (all && isbot)) ? cls_val : 0;
}


/* OnlineBrainTraitorFireProbe6 (11-04, after bs34): pure helpers. No libm (the self-test links without it): own sqrt (Newton) and acos (Abramowitz-Stegun 4.4.45, error < 7e-5 rad).
   Geometry is plain float vec3 (the unit is whatever the caller feeds; the probe feeds the game's own numbers and says which is which). */
static float kbr_f6_sqrt(float x)
{
    float g; int i;
    if (!(x > 0.0f)) return 0.0f;
    g = x > 1.0f ? x * 0.5f : 1.0f;
    for (i = 0; i < 40; i++) g = 0.5f * (g + x / g);
    return g;
}
static float kbr_f6_acos_deg(float c)
{
    float a, r;
    if (c > 1.0f) c = 1.0f;
    if (c < -1.0f) c = -1.0f;
    a = c < 0.0f ? -c : c;
    r = kbr_f6_sqrt(1.0f - a) * (1.5707288f + a * (-0.2121144f + a * (0.0742610f + a * -0.0187293f)));
    if (c < 0.0f) r = 3.14159265f - r;
    return r * 57.2957795f;
}
static float kbr_f6_len(const float *v) { return kbr_f6_sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]); }
static float kbr_f6_dist(const float *a, const float *b) { float d[3]; d[0] = a[0] - b[0]; d[1] = a[1] - b[1]; d[2] = a[2] - b[2]; return kbr_f6_len(d); }
/* angle in degrees between the directions (p - o) and (q - o); -1 when either is (nearly) zero */
static float kbr_f6_ang(const float *o, const float *p, const float *q)
{
    float a[3], b[3], la, lb;
    a[0] = p[0] - o[0]; a[1] = p[1] - o[1]; a[2] = p[2] - o[2]; b[0] = q[0] - o[0]; b[1] = q[1] - o[1]; b[2] = q[2] - o[2];
    la = kbr_f6_len(a); lb = kbr_f6_len(b);
    if (la < 1.0e-4f || lb < 1.0e-4f) return -1.0f;
    return kbr_f6_acos_deg((a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / (la * lb));
}
/* angle between a DIRECTION d and the direction o -> q */
static float kbr_f6_ang_dir(const float *d, const float *o, const float *q)
{
    float b[3], ld, lb;
    b[0] = q[0] - o[0]; b[1] = q[1] - o[1]; b[2] = q[2] - o[2];
    ld = kbr_f6_len(d); lb = kbr_f6_len(b);
    if (ld < 1.0e-4f || lb < 1.0e-4f) return -1.0f;
    return kbr_f6_acos_deg((d[0] * b[0] + d[1] * b[1] + d[2] * b[2]) / (ld * lb));
}
/* error bucket of an angle: 0 under 5 deg, 1 under 15, 2 under 45, 3 45 or more, 4 unknown (negative) */
static int kbr_f6_bucket(float deg) { return deg < 0.0f ? 4 : deg < 5.0f ? 0 : deg < 15.0f ? 1 : deg < 45.0f ? 2 : 3; }
/* is the 3x3 float block (9 floats) the identity matrix (within 1e-4)? is the vec3 all zero? */
static int kbr_f6_is_ident(const float *m)
{
    static const float id[9] = { 1, 0, 0, 0, 1, 0, 0, 0, 1 }; int i;
    for (i = 0; i < 9; i++) { float d = m[i] - id[i]; if (d > 1.0e-4f || d < -1.0e-4f) return 0; }
    return 1;
}
static int kbr_f6_is_zero3(const float *v) { return v[0] > -1.0e-4f && v[0] < 1.0e-4f && v[1] > -1.0e-4f && v[1] < 1.0e-4f && v[2] > -1.0e-4f && v[2] < 1.0e-4f; }
/* which branch of the shared muzzle transform 0x7cb080 (item vt+0x250, a thunk to it; branch B tail-jumps to the node vt+0x254) a call takes, read from its disassembly (11-04); inputs are the reads the probe makes (not the call):
     bit21   = bit 21 of [[item+4]+0x3c];  have_h = [item+0x5c] != 0;  owner_ok = 0x8ccde0([item+0x5c]) != 0;  owner_cls = (owner vt+0x30 & [0x1535228]) == [0x1535224] (the 'redirect to its own owner' test)
     node_ok = 0x598460([item+4]) != 0 where 0x598460(n) = [[n+0x50]+0x60] (GUESS: read from 0x598460's code, the probe reads it instead of calling it);  node_cls = the same class test on that node
   1 A0: bit21, no handle or no owner: returns with the outputs UNTOUCHED     2 A1: bit21, owner is used directly (vt+0x268 then 0x8c51b0)
   3 A2: bit21, owner passes the class test, so its own owner is used         4 B: bit21 clear, node passes the class test: tail-jump to the node's vt+0x254
   5 C: bit21 clear, node null or fails the class test: 0x857110 identity fallback (identity matrix, position zeroed) */
static int kbr_f6_branch(int bit21, int have_h, int owner_ok, int owner_cls, int node_ok, int node_cls)
{
    if (bit21) return (!have_h || !owner_ok) ? 1 : owner_cls ? 3 : 2;
    return (node_ok && node_cls) ? 4 : 5;
}
static const char *kbr_f6_branch_name(int b)
{
    return b == 1 ? "A0 (bit21, no owner: outputs untouched)" : b == 2 ? "A1 (bit21, owner direct)" : b == 3 ? "A2 (bit21, owner's owner)" : b == 4 ? "B (node vt+0x254)" : b == 5 ? "C (0x857110 identity fallback)" : "unknown";
}
/* is a value inside the exe's code range (the probe only calls a class getter whose address is there) */
static int kbr_f6_incode(kbr_u32 a) { return a >= 0x401000u && a < 0xb00000u; }

/* OnlineBrainTraitorFireProbe7 / OnlineBrainTraitorRayAim (11-04, after bs35): pure helpers for the ray-matrix rewrite. A 3x3 matrix is 9 floats, ROW-major, rows at 0 / 3 / 6 (the game's layout, research wgqnxsl7e / A).
   Which row is the forward axis is a GUESS (row 2, the pellet loop reads it); the bench tries 0..2 with +1 / -1. Nothing here touches the game. */
static int kbr_ra_finite(const float *v, int n) { int i; for (i = 0; i < n; i++) if (!(v[i] > -1.0e9f && v[i] < 1.0e9f)) return 0; return 1; }
static float kbr_ra_dot(const float *a, const float *b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
static void kbr_ra_cross(const float *a, const float *b, float *o) { o[0] = a[1] * b[2] - a[2] * b[1]; o[1] = a[2] * b[0] - a[0] * b[2]; o[2] = a[0] * b[1] - a[1] * b[0]; }
static int kbr_ra_unit(float *v)      /* normalise in place; 0 when (nearly) zero or not finite */
{
    float l;
    if (!kbr_ra_finite(v, 3)) return 0;
    l = kbr_f6_len(v);
    if (l < 1.0e-6f) return 0;
    v[0] /= l; v[1] /= l; v[2] /= l;
    return 1;
}
static float kbr_ra_det(const float *m) { float c[3]; kbr_ra_cross(m + 3, m + 6, c); return kbr_ra_dot(m, c); }
/* a usable rotation: finite, every row length 0.9..1.1, |det| 0.8..1.2 (a scaled or garbage matrix is never rewritten) */
static int kbr_ra_valid(const float *m)
{
    int k; float d;
    if (!kbr_ra_finite(m, 9)) return 0;
    for (k = 0; k < 3; k++) { float l = kbr_f6_len(m + 3 * k); if (l < 0.9f || l > 1.1f) return 0; }
    d = kbr_ra_det(m);
    return (d > 0.8f && d < 1.2f) || (d < -0.8f && d > -1.2f);
}
/* configured forward row: -1 (auto) or out of range -> 2 (GUESS), else 0..2 */
static int kbr_ra_row(int cfg) { return (cfg >= 0 && cfg <= 2) ? cfg : 2; }
static int kbr_ra_sign(int cfg) { return cfg < 0 ? -1 : 1; }
/* Build an orthonormal matrix out[9] from the old one: row `row` = sign * fwd (unit), the other two rows keep the old 'up' (the one with the larger |y|, projected off fwd) and its cross product,
   handedness (sign of det) as the old matrix. Returns 0 and leaves out untouched when the old matrix is not a valid rotation or fwd is degenerate. */
static int kbr_ra_build(const float *old, const float *fwd, int row, int sgn, float *out)
{
    float f[3], u[3], s[3], t[9], det0; int a, b, ui, si, k;
    if (row < 0 || row > 2 || !kbr_ra_finite(fwd, 3) || !kbr_ra_valid(old)) return 0;
    f[0] = fwd[0] * (float)(sgn < 0 ? -1 : 1); f[1] = fwd[1] * (float)(sgn < 0 ? -1 : 1); f[2] = fwd[2] * (float)(sgn < 0 ? -1 : 1);
    if (!kbr_ra_unit(f)) return 0;
    det0 = kbr_ra_det(old);
    a = (row + 1) % 3; b = (row + 2) % 3;
    { float ya = old[3 * a + 1], yb = old[3 * b + 1]; if (ya < 0.0f) ya = -ya; if (yb < 0.0f) yb = -yb; ui = ya >= yb ? a : b; si = ui == a ? b : a; }
    for (k = 0; k < 3; k++) u[k] = old[3 * ui + k];
    { float d = kbr_ra_dot(u, f); u[0] -= d * f[0]; u[1] -= d * f[1]; u[2] -= d * f[2]; }
    if (!kbr_ra_unit(u)) {
        u[0] = 0.0f; u[1] = 1.0f; u[2] = 0.0f; { float d = kbr_ra_dot(u, f); u[0] -= d * f[0]; u[1] -= d * f[1]; u[2] -= d * f[2]; }
        if (!kbr_ra_unit(u)) { u[0] = 1.0f; u[1] = 0.0f; u[2] = 0.0f; { float d = kbr_ra_dot(u, f); u[0] -= d * f[0]; u[1] -= d * f[1]; u[2] -= d * f[2]; } if (!kbr_ra_unit(u)) return 0; }
    }
    kbr_ra_cross(u, f, s);
    for (k = 0; k < 3; k++) { t[3 * row + k] = f[k]; t[3 * ui + k] = u[k]; t[3 * si + k] = s[k]; }
    if ((kbr_ra_det(t) < 0.0f) != (det0 < 0.0f)) for (k = 0; k < 3; k++) t[3 * si + k] = -s[k];
    for (k = 0; k < 9; k++) out[k] = t[k];
    return 1;
}
/* xorshift32 -> float in [0,1) (state must be nonzero) */
static float kbr_ra_rng(kbr_u32 *st)
{
    kbr_u32 x = *st ? *st : 0x9e3779b9u;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5; *st = x;
    return (float)(x >> 8) * (1.0f / 16777216.0f);
}
/* a direction at most `deg` degrees (capped to 0..30) off the unit-ish direction f: a point of the unit disc (a square sample clamped to the disc) times tan(deg), added to f at right angles; u1 / u2 in [0,1) */
static int kbr_ra_cone(const float *f, int deg, float u1, float u2, float *out)
{
    float d[3], a[3], e1[3], e2[3], x, y, r2, t, tn; int k;
    for (k = 0; k < 3; k++) d[k] = f[k];
    if (!kbr_ra_unit(d)) return 0;
    if (deg > 30) deg = 30;
    if (deg <= 0) { for (k = 0; k < 3; k++) out[k] = d[k]; return 1; }
    a[0] = 0.0f; a[1] = 1.0f; a[2] = 0.0f;
    if (d[1] > 0.9f || d[1] < -0.9f) { a[0] = 1.0f; a[1] = 0.0f; }
    kbr_ra_cross(d, a, e1); if (!kbr_ra_unit(e1)) return 0;
    kbr_ra_cross(d, e1, e2);
    x = 2.0f * u1 - 1.0f; y = 2.0f * u2 - 1.0f; r2 = x * x + y * y;
    if (r2 > 1.0f) { float r = kbr_f6_sqrt(r2); x /= r; y /= r; }
    t = (float)deg * 0.01745329f; tn = t + t * t * t * (1.0f / 3.0f) + t * t * t * t * t * (2.0f / 15.0f);      /* tan(t), 3 terms */
    for (k = 0; k < 3; k++) out[k] = d[k] + tn * (x * e1[k] + y * e2[k]);
    return kbr_ra_unit(out);
}
/* the unit direction origin -> target and its length; 0 (out untouched) when degenerate, not finite, or farther than maxd (maxd <= 0 = no limit) */
static int kbr_ra_dir(const float *o, const float *tg, float maxd, float *dir, float *dist)
{
    float d[3];
    if (!kbr_ra_finite(o, 3) || !kbr_ra_finite(tg, 3)) return 0;
    d[0] = tg[0] - o[0]; d[1] = tg[1] - o[1]; d[2] = tg[2] - o[2];
    *dist = kbr_f6_len(d);
    if (*dist < 1.0f || (maxd > 0.0f && *dist > maxd)) return 0;
    dir[0] = d[0] / *dist; dir[1] = d[1] / *dist; dir[2] = d[2] / *dist;
    return 1;
}
/* may the rewrite run at all: switch on, the game thread, a LIVE marked traitor shot, the shot record valid, geometry readable (not branch A0), a target position known */
static int kbr_ra_gate(int on, int game_thread, int marked_live, int valid, int geo, int have_target) { return on && game_thread && marked_live && valid && geo && have_target; }

/* RayAim site bit 2 (item aim point [item+0xc8..0xd0]): the point origin + dir * dist; 0 (out untouched) when dist is negative or anything is not finite */
static int kbr_ra_point(const float *o, const float *dir, float dist, float *out)
{
    float p[3];
    if (!(dist >= 0.0f) || !kbr_ra_finite(o, 3) || !kbr_ra_finite(dir, 3)) return 0;
    p[0] = o[0] + dir[0] * dist; p[1] = o[1] + dir[1] * dist; p[2] = o[2] + dir[2] * dist;
    if (!kbr_ra_finite(p, 3)) return 0;
    out[0] = p[0]; out[1] = p[1]; out[2] = p[2];
    return 1;
}
/* OnlineBrainTraitorRayAimSite: bits 1 (T), 2 (item aim point), 4 (M); nothing valid set -> 5 (the default) */
static int kbr_ra_sitemask(int v) { int m = v & 7; return m ? m : 5; }
/* distance bucket for the FireProbe7 aim-point lines: 0 under 1000 units, 1 under 3000, 2 under 6000, 3 more, 4 unknown (negative) */
static int kbr_f7_dbucket(float d) { return d < 0.0f ? 4 : d < 1000.0f ? 0 : d < 3000.0f ? 1 : d < 6000.0f ? 2 : 3; }

/* OnlineBrainTraitorFireProbe8 (11-04): pure helpers of the pellet / hit funnel counters.
   near: was 'last' (a GetTickCount of a marked shot, 0 = none yet) within win ms before 'now' (unsigned wrap safe; a last in the future counts as not near) */
static int kbr_f8_near(unsigned long now, unsigned long last, unsigned long win)
{
    unsigned long d;
    if (!last) return 0;
    d = (now - last) & 0xffffffffUL;
    return d <= win;
}
/* is v (non-zero) one of the n entries of set (the marked bots' shooter handles) */
static int kbr_f8_in_set(const kbr_u32 *set, int n, kbr_u32 v)
{
    int i;
    if (!v) return 0;
    for (i = 0; i < n; i++) if (set[i] == v) return 1;
    return 0;
}
/* null pellets of a funnel: loop iterations minus the non-null ones (never negative) */
static long kbr_f8_nulls(long iter, long ok) { return iter > ok ? iter - ok : 0; }

/* OnlineBrainTraitorLosGate / LosProbe (11-04): the stock clear-line test 0x4e1750 builds its physics query like this (disassembled 11-04, 0x4e1831..0x4e18f5):
   buf+0 = start point (arg1 = the SHOOTER-side point, y + 150 [0xb31878]); buf+0xc = delta = arg2 (the target point) - start; when |delta| > 500 [0xb64e20] the delta is scaled by (|delta| - 200 [0xb2d8e8]) / |delta|
   (the ray stops 200 short of the target, arg2). Call as kbr_los_delta(shooter_side, target, ...). Returns 1 and fills delta[3] (and *len = the original length) for a usable segment, 0 for non-finite input or a zero-length segment (out untouched). */
static int kbr_los_delta(const float *start, const float *end, float *delta, float *len)
{
    float d[3], l, k; int i;
    for (i = 0; i < 3; i++) {
        d[i] = end[i] - start[i];
        if (!(d[i] > -1.0e7f && d[i] < 1.0e7f) || !(start[i] > -1.0e7f && start[i] < 1.0e7f)) return 0;
    }
    l = kbr_f6_len(d);
    if (!(l > 0.001f)) return 0;
    k = l > 500.0f ? (l - 200.0f) / l : 1.0f;
    delta[0] = d[0] * k; delta[1] = d[1] * k; delta[2] = d[2] * k;
    if (len) *len = l;
    return 1;
}
/* the physics call answers 'hit' (al != 0) -> the line is BLOCKED; al == 0 -> clear (0x4e1750 returns sete al). ok < 0 = the query could not be made: 2 */
static int kbr_los_class(int ok, unsigned int al) { return ok < 0 ? 2 : (al & 0xffu) ? 1 : 0; }      /* 0 clear, 1 blocked, 2 error */

/* OnlineBrainTraitorModeBProbe (11-04): pure helpers. State words of the goals are 0 new, 1 starting, 2 running, 3 exiting, 4 terminated; -1 = unreadable.
   free: a goal in state 0 or 4 can be (re)started. branch of ZSoldier slot 83 0x831850 (ecx = soldier S) from the states read at entry (disassembled 0x831870..0x831994):
   0 handle 0, [[S+0x5ac]+8] busy: the 0x8318c2 path; 1 handle 0, free: CoverFire; 2 handle != 0, +0x5ac busy: stores [S+0x720] only;
   3 handle != 0, +0x5ac free, +0x658 free: AddGoal ZAttackTarget (create); 4 same but +0x658 running: retarget via 0x68fd70, no re-add; 5 unreadable state. */
static int kbr_mb_free(int st) { return st == 0 || st == 4; }
static int kbr_mb_branch(int s5ac, int s658, unsigned long handle)
{
    if (s5ac < 0) return 5;
    if (!handle) return kbr_mb_free(s5ac) ? 1 : 0;
    if (!kbr_mb_free(s5ac)) return 2;
    if (s658 < 0) return 5;
    return kbr_mb_free(s658) ? 3 : 4;
}
/* the candidate firing points of the ZAttackTarget mode-B search are vec3s at [ebp - 0xbc + 12 * index] (0x4f4bf3..0x4f4bf9); 0 for a bad index (10 candidates at most) */
static kbr_u32 kbr_mb_cand_addr(kbr_u32 ebp, long idx) { return idx < 0 || idx > 14 ? 0 : ebp - 0xbc + (kbr_u32)(12 * idx); }
/* in the observation window [t0, t0 + len] (wrap safe); due: now reached next (wrap safe) */
static int kbr_mb_inwin(unsigned long now, unsigned long t0, unsigned long len) { unsigned long d; if (!t0) return 0; d = (now - t0) & 0xffffffffUL; return d <= len; }
static int kbr_mb_due(unsigned long now, unsigned long next) { return ((now - next) & 0xffffffffUL) < 0x80000000UL; }
/* ModeBProbe data2 (11-04, read only): the vtable of the current goal [S+0x74] (unrebased), classes 0 none, 1 ZSoldierAttack 0xbd0f14, 2 ZAttackTarget 0xbd1104 (both from re/traitor_fire_1103.md / attack_goal_1104.md), 3 any other (logged as hex) */
static int kbr_mb_vtclass(kbr_u32 vt) { return !vt ? 0 : vt == 0x00bd0f14u ? 1 : vt == 0x00bd1104u ? 2 : 3; }
static const char *kbr_mb_vtname(kbr_u32 vt) { switch (kbr_mb_vtclass(vt)) { case 0: return "none"; case 1: return "ZSoldierAttack"; case 2: return "ZAttackTarget"; default: return "other"; } }
/* [S+0x88] mode histogram slot: 0..4 as is, anything else 5 */
static int kbr_mb_modeslot(kbr_u32 m) { return m <= 4 ? (int)m : 5; }
/* which of n goal pointers (loaded from S+offsets) equals the current goal: its index, -1 for none / a null current goal (a null pointer in the list never matches) */
static int kbr_mb_match(kbr_u32 cur, const kbr_u32 *ptrs, int n) { int i; if (cur <= 0xffffu) return -1; for (i = 0; i < n; i++) if (ptrs[i] == cur) return i; return -1; }
/* small tally of distinct keys: the slot of key (existing or new), -1 when the table is full or key is 0 */
static int kbr_mb_tally(kbr_u32 *keys, long *cnt, int cap, kbr_u32 key)
{
    int i; if (!key) return -1;
    for (i = 0; i < cap; i++) if (keys[i] == key) { cnt[i]++; return i; }
    for (i = 0; i < cap; i++) if (!keys[i]) { keys[i] = key; cnt[i] = 1; return i; }
    return -1;
}
/* Arcade sampling pick: trait[i] -1 = not a candidate, 0 = candidate without the Traitor mark (rec+0x79 bit 1), 1 = marked. sel[i] = 1 for every marked candidate; when none is marked, for the first ctl candidates (controls). Returns how many are selected. */
static int kbr_mb_arc_pick(const int *trait, int n, int *sel, int ctl)
{
    int i, m = 0, c = 0;
    for (i = 0; i < n; i++) { sel[i] = 0; if (trait[i] == 1) { sel[i] = 1; m++; } }
    if (m) return m;
    for (i = 0; i < n && c < ctl; i++) if (trait[i] == 0) { sel[i] = 1; c++; }
    return c;
}

/* OnlineBrainTraitorCloseInProbe / OnlineBrainTraitorCombatFlag (11-04, re/approach_lever_1104.md Verifier; pure helpers).
   A tactic list is a vector of 4-byte tactic pointers: begin at [S+0x604 / 0x610 / 0x61c], end at +4 (the Defend tick 0x85f8e2..0x85f90c loops edi = [ebx] until edi == [ebx+4], step 4: read from the disassembly; the third dword
   (capacity) is not read there: GUESS that it follows). Count, or -1 for a null / misaligned / backwards / more than 64 entries. */
static int kbr_ci_list_n(kbr_u32 begin, kbr_u32 end)
{
    kbr_u32 d;
    if (begin <= 0xffffu || end < begin) return -1;
    d = end - begin;
    if ((d & 3u) || d > 64u * 4u) return -1;
    return (int)(d >> 2);
}
/* which list the Defend tick walks (0x85f896..0x85f8bc, 0x85f8d9): 0 = A [S+0x604] when [S+0x4fc] != 0 AND [S+0x6fc] != 0 (cmp byte [eax+0x6fc],0 then 'mov byte [ebp-1],1; jne keep'), else 1 = B [S+0x610];
   2 = C [S+0x61c] when the body test [[S+0x40]+0x5c8] != 0 and 0x575100 is false (c_active). NOTE the verifier text said '6fc == 0'; the disassembly reads '6fc != 0' (jne taken keeps the 1): the logged data settles it. */
static int kbr_ci_list_pick(int b4fc, int b6fc, int c_active) { return c_active ? 2 : (b4fc && b6fc) ? 0 : 1; }
/* the ZCloseIn eval gate 1 (0x672505 cmp edx,[edi]; jl -> return 0.0): the clock [[0xdd2640]+0x48] against the tactic timer [this+0x14], signed; milliseconds still to wait, 0 when the gate is open */
static long kbr_ci_timer_left(long timer, long clock) { return clock < timer ? timer - clock : 0; }
/* percent of whole, rounded down; -1 when whole <= 0 */
static int kbr_ci_pct(long part, long whole) { return whole <= 0 ? -1 : (int)((part * 100L) / whole); }
/* tally of distinct names (cap slots of 32 bytes); the slot, -1 when full or the name is empty */
static int kbr_ci_name_tally(char names[][32], long *cnt, int cap, const char *name)
{
    int i;
    if (!name || !name[0]) return -1;
    for (i = 0; i < cap; i++) if (names[i][0] && !strncmp(names[i], name, 31)) { cnt[i]++; return i; }
    for (i = 0; i < cap; i++) if (!names[i][0]) { strncpy(names[i], name, 31); names[i][31] = 0; cnt[i] = 1; return i; }
    return -1;
}
/* CombatFlag decision. mode 1 = as specified (write only while [S+0x6fc] == 0), mode 2 = as the disassembly reads (write only while [S+0x6fc] != 0, so the Defend tick really picks list A), mode 3 = as 2 but 6fc is written 1 by the caller when 0 (write whenever 4fc or 6fc is missing). Codes:
   0 write, 1 no fresh LosGate pass, 2 skip: a human is clear / unknown, 3 skip: the 6fc condition fails, 4 already set, 5 off / not alive. */
static int kbr_cb_decide(int mode, int alive, int pass_fresh, int n_blocked, int n_open, int b6fc, int b4fc)
{
    if (mode < 1 || mode > 3) return 5;
    if (!alive) return 5;
    if (!pass_fresh || n_blocked <= 0) return 1;
    if (n_open > 0) return 2;
    if (mode == 3) return (b4fc && b6fc) ? 4 : 0;      /* mode 3 writes 6fc itself (when 0), so it never fails the 6fc condition; nothing left to write once both are nonzero */
    if (mode == 1 ? (b6fc != 0) : (b6fc == 0)) return 3;
    return b4fc ? 4 : 0;
}
/* HolderSet (OnlineBrainTraitorHolderSet): the flags dword written into the holder. 1 -> 0x01 (what every stock one-shot setter leaves: bit0 only, so bit 0x10 is missing and the fire test 0x616480 fails);
   2 -> 0x15 (bit0 + 0x10 + 0x4: bit 0x4 set also fails the fire test, and it is the 'friend in the line, hold fire' shape the Arcade bots alternate through); 0 for off / unknown. CloseIn 0x6724e0 reads no flags. */
static unsigned long kbr_hs_flags(int mode) { return mode == 1 ? 0x01ul : mode == 2 ? 0x15ul : 0ul; }
/* the fire test 0x616480 as read in the disassembly: bit0 AND bit 0x10 set, bits 0x4 / 0x40 / 0x200 clear (1 = the bot may shoot) */
static int kbr_hs_fires(unsigned long fl) { return (fl & 1ul) && (fl & 0x10ul) && !(fl & 0x244ul); }
/* HolderSet decision. Codes: 0 write allowed, 1 no fresh pass / nobody evaluated, 2 skip: a human is clear / unknown, 3 no human body found, 5 off / not alive. */
static int kbr_hs_decide(int mode, int alive, int pass_fresh, int n_blocked, int n_open, int have_human)
{
    if (mode != 1 && mode != 2) return 5;
    if (!alive) return 5;
    if (!pass_fresh || n_blocked <= 0) return 1;
    if (n_open > 0) return 2;
    return have_human ? 0 : 3;
}
/* 1 = the holder must be (re)written: handle or flags differ from what we would write (no churn when equal) */
static int kbr_hs_need(unsigned long cur_handle, unsigned long cur_flags, unsigned long new_handle, unsigned long new_flags) { return cur_handle != new_handle || cur_flags != new_flags; }

/* OnlineBrainTraitorDefendProbe (11-04; pure helpers). (b) list C as the Defend tick reads it (0x85f8c2..0x85f8e2): C is walked when the byte [[S+0x40]+0x5c8] != 0 AND the getter 0x575100 (ecx = body; pure: eax = [body+0x77c]; 0 -> false; else [[eax+0x6d8]] == 6; read in the disassembly, no calls, no writes) is false. */
static int kbr_dp_c_active(int b5c8, int getter) { return b5c8 != 0 && !getter; }
/* the getter 0x575100 on already-read data: p = [body+0x77c], v = [[p+0x6d8]] (only meaningful when p != 0) */
static int kbr_dp_getter(kbr_u32 p, kbr_u32 v) { return p != 0 && v == 6; }
/* index of tactic pointer t in the list [begin, begin+4n) given as an array, or -1 */
static int kbr_dp_index(const kbr_u32 *l, int n, kbr_u32 t) { int i; if (!t) return -1; for (i = 0; i < n; i++) if (l[i] == t) return i; return -1; }
/* ZCloseIn 0.0 attribution. Counted directly: g[0..7] = zeros taken at P1 timer, P2 holder, P3 smoothed value, P4 distance, P5 time since event, P6 reachable, P7 squad count, P4b second distance test (0x672691, after P7 / the bl shortcut);
   p8pass = times 0x6726b3 was reached (P8 class mask passed); ones = 1.0 returns; zeros_total = 0.0 returns. DERIVED: P9 (nav path, falls through 0x672718) = p8pass - ones; P8 (class mask, rel8 je 0x6726b1: not retargetable) = zeros_total - sum(g) - P9.
   Negatives (calls in flight at a round edge) clamp to 0; the return value is the unattributed residual = zeros_total - sum(g) - p8 - p9 (0 when the counters agree). */
static long kbr_dp_split(long zeros_total, const long *g, int ng, long p8pass, long ones, long *p8, long *p9)
{
    long s = 0, a, b; int i;
    for (i = 0; i < ng; i++) s += g[i];
    a = p8pass - ones; if (a < 0) a = 0;
    b = zeros_total - s - a; if (b < 0) b = 0;
    *p9 = a; *p8 = b;
    return zeros_total - s - a - b;
}
/* the taken-branch stub: pushad, pushfd, push esp, push id, call handler(id, regs) (cdecl), popfd, popad, jmp back (no stolen bytes: the stub is the TARGET of a retargeted jcc rel32 and continues to the original target 'back'). Layout: 60 9C 54 6A id B8 handler FF D0 83 C4 08 9D 61 E9 rel32 (22 bytes). */
static int kbr_dp_taken_emit(unsigned char *p, kbr_u32 at, int id, kbr_u32 handler, kbr_u32 back)
{
    static const unsigned char pre[5] = { 0x60, 0x9c, 0x54, 0x6a, 0 }; int n = 0, i; kbr_u32 rel;
    for (i = 0; i < 5; i++) p[n++] = pre[i];
    p[4] = (unsigned char)id;
    p[n++] = 0xb8; for (i = 0; i < 4; i++) p[n++] = (unsigned char)(handler >> (8 * i));
    p[n++] = 0xff; p[n++] = 0xd0; p[n++] = 0x83; p[n++] = 0xc4; p[n++] = 0x08; p[n++] = 0x9d; p[n++] = 0x61;
    rel = back - (at + (kbr_u32)n + 5);
    p[n++] = 0xe9; for (i = 0; i < 4; i++) p[n++] = (unsigned char)(rel >> (8 * i));
    return n;
}
/* the 6 bytes written over a near conditional jump (0F cc rel32) at 'site': the same condition code, retargeted to 'stub'. Returns 0 when 'orig' is not a 0F 8x rel32 jump. */
static int kbr_dp_jcc(unsigned char *out, const unsigned char *orig, kbr_u32 site, kbr_u32 stub)
{
    kbr_u32 rel = stub - (site + 6); int i;
    if (orig[0] != 0x0f || (orig[1] & 0xf0) != 0x80) return 0;
    out[0] = 0x0f; out[1] = orig[1];
    for (i = 0; i < 4; i++) out[2 + i] = (unsigned char)(rel >> (8 * i));
    return 1;
}
/* the absolute target of a 0F 8x rel32 jump at 'site' (to check that every retargeted jcc really goes to the 0.0 tail), 0 when it is not one */
static kbr_u32 kbr_dp_jcc_target(const unsigned char *b, kbr_u32 site)
{
    kbr_u32 rel; if (b[0] != 0x0f || (b[1] & 0xf0) != 0x80) return 0;
    rel = (kbr_u32)b[2] | ((kbr_u32)b[3] << 8) | ((kbr_u32)b[4] << 16) | ((kbr_u32)b[5] << 24);
    return site + 6 + rel;
}

/* OnlineBrainTraitorRunProbe (11-04; pure helpers). A ZCloseIn win (1.0 return) is followed over time: the bot-to-human distance is taken at the first sample (d0), at +5 s (d5) and at +15 s (d15).
   Phases: 0 = d0 not taken yet, 1 = waiting for +5 s, 2 = waiting for +15 s, 3 = done. Times are unsigned 32-bit millisecond ticks (wrap safe: a 'negative' difference counts as 0). */
static unsigned long kbr_rp_elapsed(unsigned long now, unsigned long t0) { unsigned long d = (now - t0) & 0xfffffffful; return d > 0x7ffffffful ? 0ul : d; }
/* the next phase for a win in 'ph' at 'elapsed' ms since the win: 0 -> 1 at once (the first sample takes d0), 1 -> 2 from 5000 ms, 2 -> 3 from 15000 ms (the one-step-per-sample rule: the caller takes the matching distance when the phase changes) */
static int kbr_rp_next(int ph, unsigned long elapsed)
{
    if (ph == 0) return 1;
    if (ph == 1) return elapsed >= 5000ul ? 2 : 1;
    if (ph == 2) return elapsed >= 15000ul ? 3 : 2;
    return 3;
}
/* a win 'closed' the distance when both distances are valid (>= 0; -1 = unknown) and d15 < d0 */
static int kbr_rp_closed(double d0, double d15) { return d0 >= 0.0 && d15 >= 0.0 && d15 < d0; }

/* OnlineBrainTraitorNoBoard (11-04; pure). Does the DLL skip a bot on 'path'? path 0 = puppeteer (steering, escort, exit walk, fallback boarding, van / box orders), 1 = BoardAll count, 2 = the pendBoard hook boarding after slot 45.
   mode 0 off; 1 = paths 0 and 1; 2 = all three. Needs the Arcade marking (arcade) and not the team swap (trturn: that bot is a TraitorTurn bot already); 'marked' = alive bot with the mark this round (the caller). */
static int kbr_nb_skip(int mode, int path, int arcade, int trturn, int marked)
{
    if (mode < 1 || mode > 2 || !arcade || trturn || !marked) return 0;
    if (path == 0 || path == 1) return 1;
    return path == 2 && mode == 2;
}

/* OnlineBrainTraitorAfcProbe (11-04; pure; re/attackfromcover_1104.md Q1 + Verifier). Predicted outcome of the ZAttackFromCover eval 0x680b20 from its read inputs:
   1 = gate 1 fails ([S+0x108] use-covers byte 0; the level-wide ban 0x72bc70 is not read, so a pass here is only 'not known to fail'), 2 = holder [S+0xb0] 0, 3 = body byte [[S+0x40]+0x5c8] nonzero,
   4 = cover state [S+0xec] 0 (gate 4: the cover search 0x807c60 runs INSIDE the eval and may fill [S+0xec], so this is where the sample is at its least certain: GUESS that the sampled value is the one the eval saw),
   5 = pass (all four gates look open). Order as the code: 1, 2, 3, 4. */
static int kbr_af_gate(unsigned long b108, unsigned long holder, unsigned long c5, unsigned long ec)
{
    if (!(b108 & 0xfful)) return 1;
    if (!holder) return 2;
    if (c5 & 0xfful) return 3;
    if (!ec) return 4;
    return 5;
}


/* OnlineBrainTraitorDriftProbe / DefendPull (11-04; pure; re/traitor_drift_1104.md). Class of the Defend winner by its RTTI name (substring, GUESS that the names contain CloseIn / Board / Loot): 0 other or none (Defend current, no owning tactic), 1 CloseIn, 2 Board, 3 Loot, 4 Defend not the current goal. */
static int kbr_win_class(const char *n)
{
    if (!n) return 0;
    if (!n[0] || !strcmp(n, "-")) return 4;      /* Defend is not the current goal: nobody known to own the block, the pull must not write (review fix) */
    if (strstr(n, "CloseIn")) return 1;
    if (strstr(n, "Board")) return 2;
    if (strstr(n, "Loot")) return 3;
    return 0;
}
/* the defend block moved: squared distance > limit^2 (cm) */
static int kbr_drift_moved(const float *a, const float *b, float limit)
{
    float dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
    return dx * dx + dy * dy + dz * dz > limit * limit;
}
/* DefendPull gate (lever L-A). 0 = write; 1 block missing or not ours (blk+0x14 != S); 2 bot dead; 3 no living human known; 4 block within 2500 cm of a human (dblk_cm; negative = unknown = no human);
   5 the current winner owns the block (CloseIn 1, Board 2, Loot 3: class != 0); 6 rate limit (since_ms < 250). Order as listed. */
static int kbr_pull_skip(int own_blk, int alive, int hum_known, long dblk_cm, int wclass, unsigned long since_ms)
{
    if (!own_blk) return 1;
    if (!alive) return 2;
    if (!hum_known || dblk_cm < 0) return 3;
    if (dblk_cm <= 2500L) return 4;
    if (wclass != 0) return 5;
    if (since_ms < 250ul) return 6;
    return 0;
}
/* DefendPull mode 2 (11-04): stock ZCloseIn stops 550 cm (= [S+0x6a8] 1100 * 0.5) short of the holder. Straight-line approximation (the stock cut runs along the nav path, GUESS that this is close enough).
   out = h + norm(bot - h) * 550. DEVIATION from the task text ("keep h.z"): the game's up axis is y (kle_place in klescort.c steps in x and z), so the offset is HORIZONTAL (x, z) and the HEIGHT h.y is kept.
   Returns 0 ok, 7 = skip: horizontal |bot-h| <= 550 cm, or not finite. */
#define KBR_PULL2_STOP_CM 550.0f
static int kbr_pull2_target(const float *h, const float *bot, float *out)
{
    float dx = bot[0] - h[0], dz = bot[2] - h[2], l2 = dx * dx + dz * dz, l;
    if (!(l2 == l2) || l2 > 1e12f || l2 <= KBR_PULL2_STOP_CM * KBR_PULL2_STOP_CM) return 7;
    l = kbr_f6_sqrt(l2);
    out[0] = h[0] + dx / l * KBR_PULL2_STOP_CM; out[1] = h[1]; out[2] = h[2] + dz / l * KBR_PULL2_STOP_CM;
    return 0;
}
/* Alive test for the drift/pull sample (11-04, bs50 DD05: 'dead 719 of 719'). src 1 = NPC health object [body+0x5fc] (owner [h+0x24] == body, as klbot.c / klbr_bot_pos),
   src 2 = player health object [body+0xa48] (only when the body has the ZFFPlayer vtable), src 0 = unreadable = alive. *alive out. Returns src. hp is the value used (0 for src 0). */
static int kbr_alive_pick(int npc_ok, float npc_hp, int pl_ok, float pl_hp, float *hp, int *alive)
{
    if (npc_ok) { *hp = npc_hp; *alive = npc_hp > 0.0f; return 1; }
    if (pl_ok) { *hp = pl_hp; *alive = pl_hp > 0.0f; return 2; }
    *hp = 0.0f; *alive = 1; return 0;
}
static int kbr_pull_ok(int own_blk, int alive, int hum_known, long dblk_cm, int wclass, unsigned long since_ms) { return kbr_pull_skip(own_blk, alive, hum_known, dblk_cm, wclass, since_ms) == 0; }
/* ---- [Brain] BoardProbe (log only, default 0; 11-04). Pure decisions, no game reads. ---- */
/* A vehicle VISIT starts when the van state (byte [rules+0x1dc]) enters 1..4 (called / arriving / parked) from outside that range (0 idle, 5 gone, -1 unknown). Returns the new visit counter. */
static int kbr_bp_van_visit(int prev, int cur, int vis)
{
    int in_prev = prev >= 1 && prev <= 4, in_cur = cur >= 1 && cur <= 4;
    return (in_cur && !in_prev) ? vis + 1 : vis;
}
/* BoardLog slot-45 accounting: 0 = new (bot not aboard in the hook ledger), 1 = repeat (aboard, boarded in THIS visit or its visit is unknown, bvis 0), 2 = stale ledger (aboard since an EARLIER visit: bvis < cur_vis). */
static int kbr_bp_s45_class(int aboard, int bvis, int cur_vis)
{
    if (!aboard) return 0;
    return (bvis > 0 && bvis < cur_vis) ? 2 : 1;
}
/* The per-bot visit stamp of the 1 s sync: the first sync that sees the bot aboard stamps the CURRENT visit (lower bound for 'stale'); kept afterwards. on = BoardLog active. */
static int kbr_bp_stamp(int on, int aboard, int bvis, int vis) { return (on && aboard && !bvis) ? vis : bvis; }
/* Rules probe: log when the van/heli is first called (state 1..5 seen, first_done 0) and whenever the state changes afterwards. */
static int kbr_bp_rules_due(int first_done, int prev, int cur)
{
    if (cur < 1 || cur > 5) return 0;
    return !first_done || cur != prev;
}
/* Per-bot 1 s line clock (last is a |1 tick stamp, 0 = never) and the per-round line cap. */
static int kbr_bp_bot_due(unsigned long now, unsigned long last, unsigned long period_ms)
{
    return !last || (unsigned long)(now - (last & ~1ul)) >= period_ms;
}
static int kbr_bp_cap_ok(long lines, long cap) { return lines < cap; }
/* Per-bot waiting line gate: the vehicle waits (state 3 / 4), the bot is not a traitor and not aboard yet. */
static int kbr_bp_bot_wanted(int van, int traitor, int aboard) { return (van == 3 || van == 4) && !traitor && !aboard; }
#endif /* KLBRAIN_LOGIC_H */
