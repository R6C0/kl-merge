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

#endif /* KLBRAIN_LOGIC_H */
