/* klbrain.c - [Brain] the Arcade AI brain on the online Fragile Alliance HOST (wk-brain-1102, plan: re/arcade_brain_online_1102.md section B stage 0 + 1a, 1b behind
   its own switch). HOST ONLY (net role 2), round state 0x19 only; a client (role 3) never builds or wraps anything. Every switch defaults 0:
     [Brain] Probe=0|1       (recommended off; a diagnostic) STAGE 0, read only: once a second on a host round, log [sm+0x54] role, [sm+0x5c] mode, [G+0x54], the answers of
                             the game's own getters 0x508ef0 / 0x7f6850, the thread id of this hook tick, and every Ally (team 2) soldier's +0x5f0 / +0x5f4 / +0x5f8 and vector sizes.
                             With Build=1 also the wrapper counters. ONE short live run of Probe=1 + Build=1 answers critic items 1, 3 and 4 of the plan (see "VERDICT" below).
     [Brain] Build=0|1       (recommended off until benched) STAGE 1a: for each Ally soldier whose +0x5f0 / +0x5f4 / +0x5f8 are all null, build the three tactics exactly as the ZSoldier ctor
                             0x6ab250 does when 0x7f6850() is true (which it is not on online roles 2 and 3), store them, put them in the AI vectors, and give each a DLL-owned vtable copy whose
                             slots 2, 3 and 11 are logging wrappers that call the originals (no frame swap, no behaviour change: an online evaluate answers 0.0 because 0x508ef0 answers NULL).
     [Brain] Loot=0|1        (recommended off; UNTESTED, needs Build=1) STAGE 1b: a zero-filled DLL-owned "shadow" rules block with a vtable copy of the Heist rules (0xbd3514) is swapped into [G+0x54]
                             and the role [sm+0x54] is set to 0 (so 0x7f6850 answers true) for the length of ONE ZLootTactic evaluate call (slot 11), host game thread only, re-entry guard, put back in a
                             __finally, the call itself under a fault guard. Loot RUN (slot 2) is NOT swapped (its argument bytes are unknown, a naked tail-jump cannot restore afterwards): it only logs.
                             The shadow carries no money, so this proves the swap path (item 2 of the critic list) and cannot yet make a bot loot. Startup logs "UNTESTED".
     [Brain] PuppetOff=0|1   (recommended off; needs Build=1 + Loot=1) klbotfill.c OnlineTactics (the puppeteer) skips its per-bot movement / loot / stack walk for a bot while that bot's REAL
                             Loot evaluate returned > 0 within PuppetWindowMs (default 5000): a bot whose brain wants nothing is still steered, it never stands idle. DropTake's action, OnlineBank,
                             OnlineTriggers and the van code are outside that loop and keep running.
     [Brain] PuppetWindowMs  (recommended 5000) 500..60000.

   WHAT WAS VERIFIED IN DISASSEMBLY (kl2.exe build 0490, 2026-11-02, debug/dasm.py, offline; CERTAIN = read in the bytes, GUESS = inferred):
   - 0x7f6850 (thiscall, ecx = [0x168e598] sm, no args, plain ret): role = [sm+0x54]; `cmp eax,3; ja -> 0x7f6865`; jump table at 0x7f6874 = { 0x7f6865, 0x7f6865, 0x7f686e, 0x7f686e }:
     roles 0 and 1 (and above 3) return `[sm+0x5c]==4`, roles 2 and 3 return false. CERTAIN. So on the host (role 2) it is false and the ctor builds nothing.
   - ZSoldier ctor 0x6ab250 branch 0x6ab56d..0x6ab66c: team = [[[soldier+0x40]+0x54]+4] in ebx; each tactic is built only when 0x7f6850() && (team == 0 || team == 2). CERTAIN.
       Loot   : 0x89e850(0x30) -> 0x68eab0(obj; arg soldier, thiscall, ret 4) -> [obj]=0xbd0d94, [obj+0x28]=[obj+0x2c]=0 -> [soldier+0x5f0]
       Board  : 0x89e850(0x14) -> 0x68eab0(obj, soldier) -> [obj]=0xbd0dd4 -> [soldier+0x5f4]
       Traitor: 0x89e850(0x20) -> eax = 0x51b7e0(obj, soldier) (sets its own vtable 0xbd13bc) -> [soldier+0x5f8]
     0x89e850 is a cdecl allocator (size on the stack, result in eax); 0x68eab0 stores the soldier at obj+4 and zeroes +8, +0xc, +0x10..0x12.
   - Vectors (CERTAIN): the ctor then fills members at soldier +0x604 (A), +0x610 (B), +0x61c (D), +0x628 (C), each = { begin, last, end-of-reserve } (three dwords; the push code is
     `cmp [v+4],[v+8]; je grow(0x403150); mov [last],val; add [v+4],4`). Each is first reserved to 10 elements (0x89e850(0x28), memmove, old buffer freed with 0x6ad680) when smaller. The
     tactics go into A, B and C - NOT D, and the plan's "+0x604 and +0x610" was short by C - in the order tabulated in klbrain_logic.h (Traitor then Board early, Loot LAST in each). D and the
     [[soldier+0x6d8]] == 6 branch (a different mode object; only a mode-6 member list) are not touched: the build REFUSES a soldier with mode 6.
   - ZDefendPosition 0x85f6c0 (walk at 0x85f8e2) loads begin/last of A / B / D and calls vtable slot 11 (`mov edx,[eax+0x2c]; call edx`, no argument pushed, result compared with a float by `fcomp`):
     slot 11 is evaluate, thiscall, NO arguments, float in st0. CERTAIN. Slots 2 (run) and 3 take an unknown number of stack bytes (the first `ret` of 0x7bc7d0 is plain but the
     disassembler window runs on into the next function) - hence the NAKED tail-jump stubs below, which are correct for any signature.
   - Vtables (read from the exe): Loot 0xbd0d94, Board 0xbd0dd4, Traitor 0xbd13bc, 15 slots each (slot 15 is already the next class's RTTI word). Slot 0 = 0x4fe6f0 in all three (the deleting
     destructor). Slot 2: 0x7bc7d0 / 0x82f970 / 0x488eb0; slot 3: 0x66b570 / 0x5478e0 / 0x66b570; slot 11: 0x451920 / 0x4faf60 / 0x79b7c0. CERTAIN.
   - 0x508ef0 (thiscall ecx = G = [0x168e9e4]): returns [G+0x54] only if [sm+0x5c] == 4 AND 0x7f6850() (see above); no class check. CERTAIN. Evaluate 0x451920 etc. begin by reading
     rules through it; with NULL rules they leave early with 0.0 (read for 0x451920, 0x4faf60, 0x79b7c0: first returns are plain rets; GUESS only for the paths after a non-null).
   - Destruction (CORRECTED by review 11-02): the soldier dtor chain 0x7f9de0 -> 0x740510 frees only the four vector buffers (0x6ad680); nothing reads +0x5f0..+0x5f8 there,
     so the game never deletes these tactics (Arcade leaks them too). No double free; a small leak per bot per round. We never free them, and every vtable copy keeps slot 0 = 0x4fe6f0. A vector buffer we regrow is allocated with 0x89e850 (the ctor's own pattern); the OLD buffer is leaked on purpose (40 bytes, an
     allocator mismatch on it would crash and nothing proves which allocator regrew it).
   - Hashing (plan section 4, CERTAIN from klhook.c notes): CEG hashes about 85 % of .text and 66 % of .rdata. This module writes NO code byte and NO .rdata: it writes game HEAP (the soldier's
     fields and vectors, the objects), the tactics' vtable pointer, and memory this DLL owns (VirtualAlloc: the vtable copies, the shadow block). Calls are to unhashed-by-call game routines.

   GUESS list (each also has a comment at its use): (1) the AI really walks A / B / C elements through slot 11 for a soldier that was built AFTER its ctor (item 4: the evaluate counter answers);
   (2) nothing compares an object's vtable pointer with 0xbd0d94 / 0xbd0dd4 / 0xbd13bc (a copy would then fail the test; the COL word [-1] IS copied so RTTI works); (3) the AI update that calls
   evaluate runs on the thread that calls this tick (item 3: the wrapper records every distinct thread id); (4) the tick runs between AI updates, so a vector edit is never seen half done;
   (5) a soldier of team 2 on an online host owns +0x5f0..+0x5f8 as null and +0x604.. as plain reserved vectors; (6) the shadow rules + role 0 satisfy 0x508ef0 (item 1/2: [sm+0x5c]
   must read 4 on the host; the probe prints it, the first swapped evaluates print 0x508ef0's answer).

   VERDICT lines (one per ~10 s while Build=1 or Probe=1): "brain: verdict: item1 ..." ([sm+0x5c] == 4 on the host?), "item3 ..." (every thread that called a wrapper vs the tick thread:
   SINGLE or OTHER), "item4 ..." (evaluate calls counted: >0 means the list walk reaches the pushed objects). A live test: the ini lines in the commit message; run ONE host round (DM01 or DD05)
   for 60 s with a bot or two; the log must show "brain: build:" per Ally soldier, then "brain: probe:" and "verdict" lines. */
#ifndef KLBRAIN_C
#define KLBRAIN_C

#include "klbrain_logic.h"

#define KLBR_MAX 16                     /* soldiers tagged at once (the lobby caps the Ally bots well below this) */
#define KLBR_ADDR_ALLOC 0x0089e850      /* cdecl allocator of the game */
#define KLBR_ADDR_CTOR_TAC 0x0068eab0   /* thiscall(obj; soldier) ret 4: ZLootTactic / ZBoardEscapeVehicleTactic base ctor */
#define KLBR_ADDR_CTOR_TRAITOR 0x0051b7e0 /* thiscall(obj; soldier) ret 4: ZBecomeTraitorTactic ctor, returns obj */
#define KLBR_ADDR_GETRULES 0x00508ef0   /* thiscall(G): the Arcade rules getter */
#define KLBR_ADDR_ARCADEQ 0x007f6850    /* thiscall(sm): "Arcade-like role" question */
#define KLBR_GLOBAL_G 0x0168e9e4        /* [that] = G, the game object whose +0x54 is the rules pointer */
#define KLBR_NSLOT 15                   /* slots copied from each tactic vtable */
static const DWORD klbr_vt_va[3] = { 0x00bd0d94, 0x00bd0dd4, 0x00bd13bc };      /* Loot, Board, Traitor */
static const DWORD klbr_size[3] = { 0x30, 0x14, 0x20 };

static int klbr_probe, klbr_build, klbr_loot, klbr_puppet, klbr_on, klbr_win_ms = 5000;
static DWORD klbr_game_tid;             /* the thread of the hook tick (SteamAPI_RunCallbacks gameplay call) */
static int klbr_verdict_n;

/* ---- the soldier tags ------------------------------------------------------------------------------------------------------------------------------------------------------------- */
struct klbr_s { DWORD snd, actor, tac[3], seenAt, builtAt, nzAt; int state; };      /* state 0 free, 1 built by us, 2 refused (told once), 3 pending build */
static struct klbr_s klbr_t[KLBR_MAX];
static int klbr_nbuilt, klbr_nrefused, klbr_nvec_fail;
static DWORD klbr_sm_round;             /* the session object of the round the table belongs to */

/* ---- the feed from klbotfill.c's host scan (no second heavy scan) ------------------------------------------------------------------------------------------------------------------- */
static struct { DWORD actor, snd; } klbr_seen[KLBR_MAX]; static int klbr_nseen; static DWORD klbr_fed_at;
static void klbr_see(DWORD actor, DWORD snd, DWORD now)
{
    if (!klbr_on) return;
    if (now != klbr_fed_at) { klbr_nseen = 0; klbr_fed_at = now; }
    if (klbr_nseen < KLBR_MAX) { klbr_seen[klbr_nseen].actor = actor; klbr_seen[klbr_nseen].snd = snd; klbr_nseen++; }
}

/* ---- the wrappers ----------------------------------------------------------------------------------------------------------------------------------------------------------------- */
static DWORD klbr_org[9];               /* [class*3 + 0 slot 2, 1 slot 3, 2 slot 11] the originals */
static volatile LONG klbr_hits[9]; static DWORD klbr_tid[9][4]; static volatile LONG klbr_ntid[9];
static volatile LONG klbr_ev_nz[3], klbr_ev_flt[3]; static float klbr_ev_max[3], klbr_ev_last[3];
static DWORD klbr_vt_copy[3];           /* the DLL-owned vtable copies (pointer to slot 0) */
static int klbr_vt_ready;
static DWORD klbr_shadow, klbr_shadow_vt;   /* the shadow rules block + its vtable copy (Loot=1) */
static volatile LONG klbr_in_swap; static int klbr_sw_told, klbr_swaps, klbr_sw_flt;

static void __cdecl klbr_hit(int id)    /* any thread: counters only, no log */
{
    DWORD tid = GetCurrentThreadId(); LONG k, n = klbr_ntid[id];
    InterlockedIncrement(&klbr_hits[id]);
    for (k = 0; k < n && k < 4; k++) if (klbr_tid[id][k] == tid) return;
    if (n < 4) { klbr_tid[id][n] = tid; klbr_ntid[id] = n + 1; }
}

/* slots 2 and 3: count, note the thread, tail-jump to the original with every register and stack byte untouched (any signature) */
#define KLBR_STUB(nm, ix) static __declspec(naked) void nm(void) { \
    __asm push ecx __asm push edx __asm push ix __asm call klbr_hit __asm add esp, 4 __asm pop edx __asm pop ecx __asm jmp dword ptr [klbr_org + 4 * ix] }
KLBR_STUB(klbr_st_l2, 0) KLBR_STUB(klbr_st_l3, 1)
KLBR_STUB(klbr_st_b2, 3) KLBR_STUB(klbr_st_b3, 4)
KLBR_STUB(klbr_st_t2, 6) KLBR_STUB(klbr_st_t3, 7)

typedef float (__fastcall *klbr_evfn)(DWORD, DWORD);
static float klbr_call_ev(DWORD fn, DWORD self, int *flt)      /* the original evaluate under a fault guard */
{
    float r = 0.0f;
    __try { r = ((klbr_evfn)(DWORD_PTR)fn)(self, 0); }
    __except (EXCEPTION_EXECUTE_HANDLER) { *flt = 1; r = 0.0f; }
    return r;
}

static void klbr_swap_in(DWORD G, DWORD sm, DWORD *sv_rules, DWORD *sv_role)
{
    __try { *sv_rules = *(volatile DWORD *)(DWORD_PTR)(G + 0x54); *sv_role = *(volatile DWORD *)(DWORD_PTR)(sm + 0x54);
            *(volatile DWORD *)(DWORD_PTR)(G + 0x54) = klbr_shadow; *(volatile DWORD *)(DWORD_PTR)(sm + 0x54) = 0; }
    __except (EXCEPTION_EXECUTE_HANDLER) { klbr_sw_flt++; }
}
static void klbr_swap_out(DWORD G, DWORD sm, DWORD sv_rules, DWORD sv_role)
{
    __try { *(volatile DWORD *)(DWORD_PTR)(G + 0x54) = sv_rules; *(volatile DWORD *)(DWORD_PTR)(sm + 0x54) = sv_role; }
    __except (EXCEPTION_EXECUTE_HANDLER) { klbr_sw_flt++; }
}

static float klbr_ev(int cls, DWORD self)
{
    float r = 0.0f; int flt = 0, id = cls * 3 + 2; DWORD G = 0, sm = 0, svr = 0, svo = 0;
    klbr_hit(id);
    if (cls == 0 && klbr_loot && klbr_shadow && GetCurrentThreadId() == klbr_game_tid && InterlockedCompareExchange(&klbr_in_swap, 1, 0) == 0) {
        G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION));
        if (G > 0xffff && sm > 0xffff) {
            DWORD got = 0; int told_now = klbr_sw_told < 6;      /* review fix: decide once, so swap 7+ neither calls nor logs */
            klbr_swap_in(G, sm, &svr, &svo);
            __try {
                if (told_now) { klbr_sw_told++; got = ((DWORD (__fastcall *)(DWORD, DWORD))KLH_VA(KLBR_ADDR_GETRULES))(G, 0); }      /* items 1 and 2: does the swap make the getter answer the shadow? */
                r = klbr_call_ev(klbr_org[id], self, &flt);
            } __finally {
                klbr_swap_out(G, sm, svr, svo);
            }
            klbr_swaps++;
            if (told_now && got) klog("brain: loot: swapped evaluate: 0x508ef0(G) answered %08lx (shadow %08lx, role was %lu, rules was %08lx): %s", (unsigned long)got, (unsigned long)klbr_shadow, (unsigned long)svo, (unsigned long)svr, got == klbr_shadow ? "the swap works" : "the swap does NOT reach the getter ([sm+0x5c] != 4? see the probe)");
            else if (told_now) klog("brain: loot: swapped evaluate: 0x508ef0(G) answered 0 (role was %lu, rules was %08lx): the getter refuses even with role 0 ([sm+0x5c] != 4?)", (unsigned long)svo, (unsigned long)svr);
        } else r = klbr_call_ev(klbr_org[id], self, &flt);
        InterlockedExchange(&klbr_in_swap, 0);
    } else r = klbr_call_ev(klbr_org[id], self, &flt);
    if (flt) InterlockedIncrement(&klbr_ev_flt[cls]);
    klbr_ev_last[cls] = r;
    if (r > 0.0f) {
        InterlockedIncrement(&klbr_ev_nz[cls]); if (r > klbr_ev_max[cls]) klbr_ev_max[cls] = r;
        if (cls == 0) { int i; for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && klbr_t[i].tac[0] == self) { klbr_t[i].nzAt = GetTickCount() | 1u; break; } }
    }
    return r;
}
static float __fastcall klbr_ev_l(DWORD self, DWORD d) { (void)d; return klbr_ev(0, self); }
static float __fastcall klbr_ev_b(DWORD self, DWORD d) { (void)d; return klbr_ev(1, self); }
static float __fastcall klbr_ev_t(DWORD self, DWORD d) { (void)d; return klbr_ev(2, self); }

/* the DLL-owned vtable copies (once): [-1] RTTI word + 15 slots, slots 2 / 3 / 11 replaced, slot 0 stays the game's destructor */
static int klbr_make_vtables(void)
{
    static const DWORD st2[3] = { (DWORD)(DWORD_PTR)klbr_st_l2, (DWORD)(DWORD_PTR)klbr_st_b2, (DWORD)(DWORD_PTR)klbr_st_t2 };
    static const DWORD st3[3] = { (DWORD)(DWORD_PTR)klbr_st_l3, (DWORD)(DWORD_PTR)klbr_st_b3, (DWORD)(DWORD_PTR)klbr_st_t3 };
    DWORD ev[3]; int c;
    if (klbr_vt_ready) return 1;
    ev[0] = (DWORD)(DWORD_PTR)klbr_ev_l; ev[1] = (DWORD)(DWORD_PTR)klbr_ev_b; ev[2] = (DWORD)(DWORD_PTR)klbr_ev_t;
    for (c = 0; c < 3; c++) {
        DWORD *blk, org[KLBR_NSLOT], va = klbr_vt_va[c] + (DWORD)klh_delta, col = 0;
        if (!klh_rd(va, org, sizeof org) || org[0] != 0x004fe6f0u + (DWORD)klh_delta) { klog("brain: build: vtable %08lx of class %d does not read as expected (slot 0 %08lx): no vtable copies, Build off", (unsigned long)va, c, (unsigned long)org[0]); return 0; }
        klh_rd(va - 4, &col, 4);
        blk = (DWORD *)VirtualAlloc(0, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
        if (!blk) return 0;
        blk[0] = col; memcpy(blk + 1, org, sizeof org);
        klbr_org[c * 3 + 0] = org[2]; klbr_org[c * 3 + 1] = org[3]; klbr_org[c * 3 + 2] = org[11];
        blk[1 + 2] = st2[c]; blk[1 + 3] = st3[c]; blk[1 + 11] = ev[c];
        klbr_vt_copy[c] = (DWORD)(DWORD_PTR)(blk + 1);
    }
    klbr_vt_ready = 1;
    klog("brain: build: vtable copies ready (Loot %08lx, Board %08lx, Traitor %08lx; slots 2 / 3 / 11 wrapped, slot 0 = the game's destructor)", (unsigned long)klbr_vt_copy[0], (unsigned long)klbr_vt_copy[1], (unsigned long)klbr_vt_copy[2]);
    return 1;
}

/* the shadow rules block (Loot=1): zero-filled 0xf30 bytes (the Heist class 0xbd3514 size, plan 1b) with a private copy of that vtable. UNTESTED: it carries no crew table and no money. */
static int klbr_make_shadow(void)
{
    DWORD *vt, org[256]; DWORD va = 0x00bd3514u + (DWORD)klh_delta;
    if (klbr_shadow) return 1;
    if (!klh_rd(va, org, sizeof org)) return 0;
    vt = (DWORD *)VirtualAlloc(0, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    klbr_shadow = (DWORD)(DWORD_PTR)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!vt || !klbr_shadow) { klbr_shadow = 0; return 0; }
    memcpy(vt, org, sizeof org);      /* the Heist methods as they are (GUESS: harmless on zero fields; the evaluate call is under a fault guard) */
    klbr_shadow_vt = (DWORD)(DWORD_PTR)vt; *(DWORD *)(DWORD_PTR)klbr_shadow = klbr_shadow_vt;
    return 1;
}

/* ---- construction ----------------------------------------------------------------------------------------------------------------------------------------------------------------- */
static DWORD klbr_alloc(DWORD n) { return ((DWORD (__cdecl *)(DWORD))KLH_VA(KLBR_ADDR_ALLOC))(n); }
static int klbr_w32(DWORD at, DWORD v) { __try { *(volatile DWORD *)(DWORD_PTR)at = v; return 1; } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; } }

/* make sure vector `vec` (address of its three dwords) has room for `extra` more elements; regrown like the ctor's own reserve (new buffer from 0x89e850, copy, header rewritten) */
static int klbr_room(DWORD vec, int extra)
{
    DWORD b = klh_rd32(vec), l = klh_rd32(vec + 4), e = klh_rd32(vec + 8), nb; int n, ncap;
    if (!kbr_vec_ok(b, l, e)) return 0;
    n = (int)((l - b) / 4);
    if ((int)((e - l) / 4) >= extra) return 1;
    if (!(ncap = kbr_grow_cap(n + extra))) return 0;
    __try {
        if (!(nb = klbr_alloc((DWORD)ncap * 4))) return 0;
        memcpy((void *)(DWORD_PTR)nb, (void *)(DWORD_PTR)b, (size_t)n * 4);
        *(volatile DWORD *)(DWORD_PTR)vec = nb; *(volatile DWORD *)(DWORD_PTR)(vec + 4) = nb + (DWORD)n * 4; *(volatile DWORD *)(DWORD_PTR)(vec + 8) = nb + (DWORD)ncap * 4;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    return 1;
}

/* put `val` (the member `field` of the soldier) into vector v at the ctor's place: before the first element equal to a later member's value, else at the end */
static int klbr_push(DWORD snd, int v, kbr_u16 field, DWORD val)
{
    DWORD vec = snd + kbr_vecoff[v], b = klh_rd32(vec), l = klh_rd32(vec + 4), e = klh_rd32(vec + 8), el[256], succ[16]; kbr_u16 so[16]; int n, ns, k, idx, got;
    if (!kbr_vec_ok(b, l, e)) return 0;
    n = (int)((l - b) / 4); if (n >= 255 || l >= e) return 0;
    if (n && !klh_rd(b, el, (SIZE_T)n * 4)) return 0;
    ns = kbr_after(v, field, so, 16);
    for (k = 0; k < ns; k++) succ[k] = klh_rd32(snd + so[k]);
    idx = kbr_insert_index(el, n, succ, ns);
    got = kbr_insert(el, n, 256, idx, val);
    if (got != n + 1) return 0;
    __try {      /* only the moved tail + the new slot are written, then `last` moves */
        int i; for (i = idx; i < got; i++) *(volatile DWORD *)(DWORD_PTR)(b + (DWORD)i * 4) = el[i];
        *(volatile DWORD *)(DWORD_PTR)(vec + 4) = l + 4;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    return 1;
}

static int klbr_vcount(DWORD snd, int v) { DWORD b = klh_rd32(snd + kbr_vecoff[v]), l = klh_rd32(snd + kbr_vecoff[v] + 4); return l >= b ? (int)((l - b) / 4) : -1; }

static void klbr_build_one(struct klbr_s *e, DWORD now)
{
    DWORD snd = e->snd, mo, o[3] = { 0, 0, 0 }; int v, before[KBR_NVEC], failed = 0;
    if (klh_rd32(snd) != KLE_SOLDIER_VT) { e->state = 2; return; }
    if (klh_rd32(snd + 0x5f0) || klh_rd32(snd + 0x5f4) || klh_rd32(snd + 0x5f8)) {      /* GUESS fields; someone (the game, or us earlier) already built: never double-tag */
        e->state = 2; klbr_nrefused++;
        klog("brain: build: soldier %08lx already has tactics (%08lx %08lx %08lx): left alone", (unsigned long)snd, (unsigned long)klh_rd32(snd + 0x5f0), (unsigned long)klh_rd32(snd + 0x5f4), (unsigned long)klh_rd32(snd + 0x5f8));
        return;
    }
    if (!(mo = klh_rd32(snd + 0x6d8)) || klh_rd32(mo) == 6) { e->state = 2; klbr_nrefused++; klog("brain: build: soldier %08lx: mode object %08lx reads %lu (6 = the mode-6 member list, not handled): left alone", (unsigned long)snd, (unsigned long)mo, (unsigned long)klh_rd32(mo)); return; }
    for (v = 0; v < KBR_NVEC; v++) {
        before[v] = klbr_vcount(snd, v);
        if (!kbr_vec_ok(klh_rd32(snd + kbr_vecoff[v]), klh_rd32(snd + kbr_vecoff[v] + 4), klh_rd32(snd + kbr_vecoff[v] + 8)) || !klbr_room(snd + kbr_vecoff[v], 3)) {
            e->state = 2; klbr_nvec_fail++; klog("brain: build: soldier %08lx: AI vector at +0x%x does not look like {begin,last,end} (%08lx %08lx %08lx) or cannot grow: left alone (GUESS layout wrong?)", (unsigned long)snd, kbr_vecoff[v], (unsigned long)klh_rd32(snd + kbr_vecoff[v]), (unsigned long)klh_rd32(snd + kbr_vecoff[v] + 4), (unsigned long)klh_rd32(snd + kbr_vecoff[v] + 8));
            return;
        }
    }
    if (!klbr_make_vtables()) { e->state = 2; return; }
    __try {
        typedef void (__fastcall *ctor_t)(DWORD, DWORD, DWORD); typedef DWORD (__fastcall *ctor_r)(DWORD, DWORD, DWORD);
        if (!(o[0] = klbr_alloc(klbr_size[0])) || !(o[1] = klbr_alloc(klbr_size[1])) || !(o[2] = klbr_alloc(klbr_size[2]))) failed = 1;
        else {
            ((ctor_t)KLH_VA(KLBR_ADDR_CTOR_TAC))(o[0], 0, snd);  *(DWORD *)(DWORD_PTR)o[0] = klbr_vt_copy[0]; *(DWORD *)(DWORD_PTR)(o[0] + 0x28) = 0; *(DWORD *)(DWORD_PTR)(o[0] + 0x2c) = 0;
            ((ctor_t)KLH_VA(KLBR_ADDR_CTOR_TAC))(o[1], 0, snd);  *(DWORD *)(DWORD_PTR)o[1] = klbr_vt_copy[1];
            o[2] = ((ctor_r)KLH_VA(KLBR_ADDR_CTOR_TRAITOR))(o[2], 0, snd); if (o[2] > 0xffff) *(DWORD *)(DWORD_PTR)o[2] = klbr_vt_copy[2]; else failed = 1;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { failed = 1; }
    if (failed) { e->state = 2; klbr_nrefused++; klog("brain: build: soldier %08lx: allocation or a tactic ctor failed (%08lx %08lx %08lx): nothing stored (the objects, if any, leak)", (unsigned long)snd, (unsigned long)o[0], (unsigned long)o[1], (unsigned long)o[2]); return; }
    /* store, then vectors in the ctor's member order (Traitor, Board, Loot) */
    if (!klbr_w32(snd + 0x5f0, o[0]) || !klbr_w32(snd + 0x5f4, o[1]) || !klbr_w32(snd + 0x5f8, o[2])) { e->state = 2; return; }
    for (v = 0; v < KBR_NVEC; v++) {
        int ok = klbr_push(snd, v, KBR_F_TRAITOR, o[2]) & klbr_push(snd, v, KBR_F_BOARD, o[1]) & klbr_push(snd, v, KBR_F_LOOT, o[0]);
        if (!ok) { klbr_nvec_fail++; klog("brain: build: soldier %08lx: vector +0x%x insert failed part way (count %d -> %d)", (unsigned long)snd, kbr_vecoff[v], before[v], klbr_vcount(snd, v)); }
    }
    e->tac[0] = o[0]; e->tac[1] = o[1]; e->tac[2] = o[2]; e->state = 1; e->builtAt = now; klbr_nbuilt++;
    klog("brain: build: soldier %08lx (actor %08lx): Loot %08lx Board %08lx Traitor %08lx stored at +0x5f0/+0x5f4/+0x5f8; vectors A %d->%d B %d->%d C %d->%d (+3 each wanted); vtable copies %08lx %08lx %08lx",
         (unsigned long)snd, (unsigned long)e->actor, (unsigned long)o[0], (unsigned long)o[1], (unsigned long)o[2], before[0], klbr_vcount(snd, 0), before[1], klbr_vcount(snd, 1), before[2], klbr_vcount(snd, 2),
         (unsigned long)klbr_vt_copy[0], (unsigned long)klbr_vt_copy[1], (unsigned long)klbr_vt_copy[2]);
}

/* ---- the host scan when klbotfill.c's OnlineTactics scan is not feeding us ------------------------------------------------------------------------------------------------------------- */
static int klbr_scan(DWORD *actor, DWORD *snd, int cap)
{
    DWORD p, tab, i, blk[64 * 32]; int n = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return 0;
    for (i = 0; i < 0x10000 && n < cap; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < cap; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], pr, team = 99, s, hp; float hv[2] = { 0, 0 };
            if (o < 0x10000 || klh_avt(o) != 0x00bb3bac) continue;      /* ZFFActor */
            if (!(pr = klh_rd32(o + 0x54)) || !klh_rd(pr + 4, &team, 4) || team != 2) continue;
            if (!(hp = klh_rd32(o + 0x5fc)) || !klh_rd(hp + 4, hv, 8) || !(hv[0] > 0)) continue;
            if (!(s = klh_rd32(o + 0x77c)) || klh_rd32(s) != KLE_SOLDIER_VT) continue;
            actor[n] = o; snd[n] = s; n++;
        }
    }
    return n;
}

static struct klbr_s *klbr_find(DWORD snd) { int i; for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state && klbr_t[i].snd == snd) return &klbr_t[i]; return 0; }
static struct klbr_s *klbr_new(DWORD snd, DWORD actor, DWORD now)
{
    int i, old = -1;
    for (i = 0; i < KLBR_MAX; i++) if (!klbr_t[i].state) break;
    if (i == KLBR_MAX) { for (i = 0; i < KLBR_MAX; i++) if (now - klbr_t[i].seenAt > 20000u && (old < 0 || klbr_t[i].seenAt < klbr_t[old].seenAt)) old = i; if (old < 0) return 0; i = old; }
    memset(&klbr_t[i], 0, sizeof klbr_t[i]); klbr_t[i].snd = snd; klbr_t[i].actor = actor; klbr_t[i].seenAt = now; klbr_t[i].state = 3;      /* 3 = pending build */
    return &klbr_t[i];
}

/* PuppetOff: klbotfill.c asks, per bot, whether its OnlineTactics steering is skipped this tick */
static int klbr_puppet_off(DWORD snd)
{
    struct klbr_s *e;
    if (!klbr_puppet || !snd) return 0;
    e = klbr_find(snd);
    return e && kbr_puppet_released(1, e->state == 1, GetTickCount(), e->nzAt, (unsigned long)klbr_win_ms);
}

static void klbr_summary(void)
{
    if (klbr_sm_round) klog("brain: round end: built %d soldier(s) (%d refused, %d vector failure(s)); loot swaps %d (%d fault(s)); evaluate calls loot %ld board %ld traitor %ld, nonzero %ld/%ld/%ld, faults %ld/%ld/%ld",
        klbr_nbuilt, klbr_nrefused, klbr_nvec_fail, klbr_swaps, klbr_sw_flt, (long)klbr_hits[2], (long)klbr_hits[5], (long)klbr_hits[8], (long)klbr_ev_nz[0], (long)klbr_ev_nz[1], (long)klbr_ev_nz[2],
        (long)klbr_ev_flt[0], (long)klbr_ev_flt[1], (long)klbr_ev_flt[2]);
    klbr_sm_round = 0;
}

static void klbr_probe_log(DWORD now, DWORD sm, DWORD role, DWORD mode, DWORD state, DWORD *actor, DWORD *snd, int n)
{
    DWORD G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)), rules = G > 0xffff ? klh_rd32(G + 0x54) : 0, ans = 0xdeadbeef; int aq = -1, i, c, other = 0; DWORD tids[4 * 3];
    __try {      /* the game's own getters, read-only questions (no argument, no write); they are answered for the REAL role */
        ans = G > 0xffff ? ((DWORD (__fastcall *)(DWORD, DWORD))KLH_VA(KLBR_ADDR_GETRULES))(G, 0) : 0;
        aq = ((BYTE (__fastcall *)(DWORD, DWORD))KLH_VA(KLBR_ADDR_ARCADEQ))(sm, 0) & 0xff;
    } __except (EXCEPTION_EXECUTE_HANDLER) { }
    klog("brain: probe: sm %08lx role [sm+0x54]=%lu mode [sm+0x5c]=%lu state [sm+0x70]=0x%lx; G %08lx [G+0x54]=%08lx 0x508ef0(G)=%08lx 0x7f6850()=%d; hook-tick thread %lu; %d Ally soldier(s)",
         (unsigned long)sm, (unsigned long)role, (unsigned long)mode, (unsigned long)state, (unsigned long)G, (unsigned long)rules, (unsigned long)ans, aq, (unsigned long)klbr_game_tid, n);
    for (i = 0; i < n && i < 8; i++)
        klog("brain: probe:  soldier %08lx actor %08lx +0x5f0 %08lx +0x5f4 %08lx +0x5f8 %08lx; vectors A %d B %d C %d D %d; tag %s", (unsigned long)snd[i], (unsigned long)actor[i], (unsigned long)klh_rd32(snd[i] + 0x5f0), (unsigned long)klh_rd32(snd[i] + 0x5f4),
             (unsigned long)klh_rd32(snd[i] + 0x5f8), klbr_vcount(snd[i], 0), klbr_vcount(snd[i], 1), klbr_vcount(snd[i], 2), (int)((klh_rd32(snd[i] + 0x61c + 4) - klh_rd32(snd[i] + 0x61c)) / 4),
             klbr_find(snd[i]) ? (klbr_find(snd[i])->state == 1 ? "ours" : "refused") : "none");
    if (klbr_build) {
        klog("brain: wrap: evaluate calls loot %ld (nonzero %ld, max %.3f, last %.3f) board %ld (nz %ld) traitor %ld (nz %ld); run calls loot %ld board %ld traitor %ld; slot3 calls %ld %ld %ld; evaluate faults %ld %ld %ld",
             (long)klbr_hits[2], (long)klbr_ev_nz[0], (double)klbr_ev_max[0], (double)klbr_ev_last[0], (long)klbr_hits[5], (long)klbr_ev_nz[1], (long)klbr_hits[8], (long)klbr_ev_nz[2],
             (long)klbr_hits[0], (long)klbr_hits[3], (long)klbr_hits[6], (long)klbr_hits[1], (long)klbr_hits[4], (long)klbr_hits[7], (long)klbr_ev_flt[0], (long)klbr_ev_flt[1], (long)klbr_ev_flt[2]);
        for (c = 0; c < 9; c++) { int k; for (k = 0; k < klbr_ntid[c] && k < 4; k++) { int j, seen = 0; for (j = 0; j < other; j++) if (tids[j] == klbr_tid[c][k]) seen = 1; if (!seen && other < 12) tids[other++] = klbr_tid[c][k]; } }
        if (!(klbr_verdict_n++ % 10)) {      /* ~ every 10 s */
            long evt = (long)(klbr_hits[2] + klbr_hits[5] + klbr_hits[8]); int foreign = 0;
            for (i = 0; i < other; i++) if (tids[i] != klbr_game_tid) foreign = 1;
            klog("brain: verdict: item1 [sm+0x5c]=%lu on this host (the getter needs 4): %s; item3 %d distinct wrapper thread(s), hook-tick thread %lu: %s; item4 %ld evaluate call(s) so far: %s",
                 (unsigned long)mode, mode == 4 ? "OK" : "NOT 4 (a swap must also write it)", other, (unsigned long)klbr_game_tid, !other ? "no wrapper call yet" : foreign ? "OTHER thread calls the tactics (a global swap would race)" : "SINGLE (same thread as the tick)",
                 evt, evt > 0 ? "the AI list walk reaches the pushed objects" : "NOT YET (the vectors may not be what the AI walks)");
        }
    }
}

static void klbr_tick(int game_thread)
{
    static DWORD last, told; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, actor[KLBR_MAX], snd[KLBR_MAX]; int n = 0, i, built = 0;
    if (!klbr_on || !game_thread || !klh_exe_ok || now - last < 1000) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if (role != 2 || mode != 4 || state != KLB_ROUND) {      /* HOST Fragile Alliance round only; a client / other mode / lobby does nothing */
        if (klbr_sm_round && (state < KLB_ROUND || state >= 0x1f || role != 2)) { klbr_summary(); memset(klbr_t, 0, sizeof klbr_t); klbr_verdict_n = 0; }
        return;
    }
    klbr_game_tid = GetCurrentThreadId();
    if (klbr_sm_round != sm) { if (klbr_sm_round) klbr_summary(); memset(klbr_t, 0, sizeof klbr_t); klbr_sm_round = sm; klbr_nbuilt = klbr_nrefused = klbr_nvec_fail = klbr_swaps = 0; klbr_verdict_n = 0;
        klog("brain: round starts on the host (Probe %d, Build %d, Loot %d, PuppetOff %d)", klbr_probe, klbr_build, klbr_loot, klbr_puppet); }
    if (klbr_fed_at && now - klbr_fed_at < 2500u) { for (i = 0; i < klbr_nseen && n < KLBR_MAX; i++) { actor[n] = klbr_seen[i].actor; snd[n] = klbr_seen[i].snd; n++; } }
    else n = klbr_scan(actor, snd, KLBR_MAX);
    if (klbr_build) {
        for (i = 0; i < n; i++) {
            struct klbr_s *e = klbr_find(snd[i]);
            if (!e) { e = klbr_new(snd[i], actor[i], now); if (!e) continue; }
            e->seenAt = now;
            if (e->state == 3 && built < 2) { klbr_build_one(e, now); built++; }      /* at most two a tick */
            else if (e->state == 1 && klh_rd32(snd[i] + 0x5f0) != e->tac[0]) { klog("brain: soldier %08lx no longer holds our Loot tactic (%08lx vs %08lx): tag dropped, nothing freed by us", (unsigned long)snd[i], (unsigned long)klh_rd32(snd[i] + 0x5f0), (unsigned long)e->tac[0]); e->state = 2; }
        }
        for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && now - klbr_t[i].seenAt > 15000u && klh_rd32(klbr_t[i].snd) != KLE_SOLDIER_VT) { klog("brain: soldier %08lx is gone (dead or despawned); the game's destructor does NOT free its tactics (about 0x64 bytes leak per bot per round, accepted); we free nothing", (unsigned long)klbr_t[i].snd); klbr_t[i].state = 0; }
    }
    if (klbr_probe || klbr_build) { if (!told || klbr_probe || klbr_build) klbr_probe_log(now, sm, role, mode, state, actor, snd, n); told = 1; }
}

static void klbr_init(void)
{
    int sw[4];
    kbr_switches(GetPrivateProfileIntA("Brain", "Probe", 0, klh_ini) != 0, GetPrivateProfileIntA("Brain", "Build", 0, klh_ini) != 0, GetPrivateProfileIntA("Brain", "Loot", 0, klh_ini) != 0,
                 GetPrivateProfileIntA("Brain", "PuppetOff", 0, klh_ini) != 0, sw);
    klbr_probe = sw[0]; klbr_build = sw[1]; klbr_loot = sw[2]; klbr_puppet = sw[3];
    klbr_win_ms = (int)GetPrivateProfileIntA("Brain", "PuppetWindowMs", 5000, klh_ini); if (klbr_win_ms < 500) klbr_win_ms = 500; if (klbr_win_ms > 60000) klbr_win_ms = 60000;
    klbr_on = klbr_probe || klbr_build;
    if (GetPrivateProfileIntA("Brain", "Loot", 0, klh_ini) && !klbr_build) klog("brain: Loot needs Build=1: off");
    if (GetPrivateProfileIntA("Brain", "PuppetOff", 0, klh_ini) && !klbr_loot) klog("brain: PuppetOff needs Build=1 and Loot=1: off");
    if (klbr_on) klog("brain: Probe %d, Build %d (recommended off until benched), Loot %d, PuppetOff %d; HOST round only, no code byte is patched", klbr_probe, klbr_build, klbr_loot, klbr_puppet);
    if (klbr_loot) { klog("brain: Loot=1 is UNTESTED: a zero-filled shadow rules block is swapped in around ONE Loot evaluate call (host game thread, fault-guarded); it cannot make a bot loot yet and only proves the swap path"); if (!klbr_make_shadow()) { klog("brain: shadow rules block could not be made: Loot off"); klbr_loot = 0; klbr_puppet = 0; } }
    if (klbr_puppet) klog("brain: PuppetOff=1 UNTESTED: OnlineTactics steering is skipped for a bot only within %d ms of its real Loot evaluate returning > 0", klbr_win_ms);
}

#endif /* KLBRAIN_C */
