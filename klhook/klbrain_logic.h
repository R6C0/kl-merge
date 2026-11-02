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

#endif /* KLBRAIN_LOGIC_H */
