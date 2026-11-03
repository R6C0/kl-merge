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
    return (unsigned long)(now - nz_at) <= win_ms;
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
    int b = board_on && built && kbr_board_state_ok(van) && board_nz_at && (unsigned long)(now - board_nz_at) <= board_win;
    int l = kbr_puppet_released(puppet_on, built, now, loot_nz_at, loot_win) && !kbr_board_state_ok(van);
    *board_real = b; *loot_real = b ? 0 : l;
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

#endif /* KLBRAIN_LOGIC_H */
