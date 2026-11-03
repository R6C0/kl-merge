/* klbrain.c - [Brain] the Arcade AI brain on the online Fragile Alliance HOST (wk-brain-1102, plan: re/arcade_brain_online_1102.md section B stage 0 + 1a, 1b behind
   its own switch). HOST ONLY (net role 2), round state 0x19 only; a client (role 3) never builds or wraps anything. Every switch defaults 0:
     [Brain] Probe=0|1       (recommended off; a diagnostic) STAGE 0, read only: once a second on a host round, log [sm+0x54] role, [sm+0x5c] mode, [G+0x54], the answers of
                             the game's own getters 0x508ef0 / 0x7f6850, the thread id of this hook tick, and every Ally (team 2) soldier's +0x5f0 / +0x5f4 / +0x5f8 and vector sizes.
                             With Build=1 also the wrapper counters. ONE short live run of Probe=1 + Build=1 answers critic items 1, 3 and 4 of the plan (see "VERDICT" below).
     [Brain] Build=0|1       (recommended off until benched) STAGE 1a: for each Ally soldier whose +0x5f0 / +0x5f4 / +0x5f8 are all null, build the three tactics exactly as the ZSoldier ctor
                             0x6ab250 does when 0x7f6850() is true (which it is not on online roles 2 and 3), store them, put them in the AI vectors, and give each a DLL-owned vtable copy whose
                             slots 2, 3 and 11 are logging wrappers that call the originals (no frame swap, no behaviour change: an online evaluate answers 0.0 because 0x508ef0 answers NULL).
     [Brain] Loot=0|1        (recommended off; UNTESTED, needs Build=1) STAGE 1b: a zero-filled DLL-owned "shadow" rules block with a vtable copy of the Heist rules (0xbd3514) is swapped into [G+0x54]
                             and the role [sm+0x54] is set to 0 (so 0x7f6850 answers true) for the length of ONE Loot tactic call (evaluate, run or exit: all plain `ret`, no stack argument),
                             host game thread only, depth-counted, put back in a __finally, the call itself under a fault guard. Without Bridge the shadow carries no money, so the
                             evaluate answers 0 and no bot loots; with Bridge it carries the crew table and the 5 nearest stacks (stage 2 below). Startup logs "UNTESTED".
     [Brain] PuppetOff=0|1   (recommended off; needs Build=1 + Loot=1) klbotfill.c OnlineTactics (the puppeteer) skips its per-bot movement / loot / stack walk for a bot while that bot's REAL
                             Loot evaluate returned > 0 within PuppetWindowMs (default 5000): a bot whose brain wants nothing is still steered, it never stands idle. DropTake's action, OnlineBank,
                             OnlineTriggers and the van code are outside that loop and keep running.
     [Brain] PuppetWindowMs  (recommended 5000) 500..60000.

   STAGE 2 / 3 (2026-11-03, wk brain2; design re/arcade_brain_stage2_1103.md; ALL UNTESTED live, every key defaults 0, no code byte patched):
     [Brain] OnlineBrainBridge=0|1  (recommended off; needs Build + Loot) the shadow rules W carries a crew table (record 0 = the host human, records 1.. = our bots), a score block (level byte,
                             money row = the host ledger, flag 0x2000 while grabbing) and the van state mirrored from the real rules; Heist slot 202 is a DLL stub giving the 5 nearest real money
                             controls; the grab itself is run by this DLL (klbr_pump, called from klbotfill.c), never by the Arcade tick 0x727cb0. Needs PuppetOff to hand a bot over.
     [Brain] OnlineBrainBoard=0|1   (recommended off; needs Build) the real Board tactic is evaluated/run in the frame; its answer reaches the AI only with BoardReal (otherwise a dry run).
     [Brain] OnlineBrainBoardReal=0|1 (recommended off; needs Board) Heist slot 45 (0x6840a0) is a DLL stub: boarding goes through the host ledger (phase 3) and OnlineBoard's squad removal.
     [Brain] OnlineBrainTraitor=0|1 (recommended off; needs Build + Bridge) the real Traitor roll runs in the frame; RUN's record bit is MIRRORED to the log only.
     [Brain] OnlineBrainCops=0|1    (recommended off; needs Bridge) research only: no behaviour.
     [Brain] OnlineBrainLevel=6     1..11, the Arcade level byte the Traitor roll reads.   LootWinMs=1500 / BoardWinMs=2000: how long after an evaluate > 0 the real tactic still owns the bot.
   COROUTINE RULE (bench bs1, 11-03: BS1B + BS1C host crash c0000029): Loot RUN 0x7bc7d0 and Board RUN 0x82f970 yield through 0x55b9f0 (setjmp + stack copy + longjmp to
   0x168e4c8). The DLL NEVER CALLS them itself (kbr_orig_ok) and, without RealRun, Loot / Board are never shown > 0 to the AI and PuppetOff / OnlineBrainBoardReal are forced off.
     [Brain] RealRun=0|1     (recommended off; UNTESTED; needs Build + Loot + Bridge; 2026-11-03 wk brain4) lets the REAL Loot / Board RUN run for our host bots: the DLL-owned vtable copies point
                             slot 2 (Loot, Board) and Board slot 3 (EXIT) STRAIGHT at the originals (no DLL frame, no __try across the yield, kbr_run_direct), and the exe's three msvcr90 longjmp
                             call sites (IAT 0xb10370) go through klbr_w_longjmp, a plain C thunk without any SEH: a RESUME (val 1 / 2) of one of OUR tactic coroutines (buf = live [tac+0xc])
                             swaps the shadow rules in ([G+0x54] := shadow, [sm+0x54] := 0, so 0x508ef0 answers W), the slice's exit longjmp(0x168e4c8, 1) swaps them back, then the real longjmp runs.
                             Safety nets: a leaked swap is put back at the next hook tick and in the vectored crash handler; the registry of our tactic objects is append-only and never cleared at round end
                             (the objects are never freed), so a coroutine alive across a round end still gets the shadow. With RealRun Loot is shown to the AI under the old PuppetOff rules and Board under
                             BoardReal + a van state (PuppetOff / BoardReal may be set again), a gated hand-off keeps the stall watchdog.
     [Brain] ArcadePick=0|1  (recommended off; needs Build + Loot + Bridge) the puppeteer walks a bot to the stack its real Loot evaluate chose ([tac+0x2c]) instead of its own nearest.
   One frame = one tactic call (evaluate, run or exit of Loot / Board / Traitor), depth-counted; the evaluates, Board EXIT (without RealRun) and Traitor RUN run under __try in a frame; Loot/Board RUN are never called by the DLL (RealRun points the vtable at them directly); [G+0x54] and [sm+0x54] restored in a __finally and verified. A tactic call that is not
   for one of our bots, or not on the host game thread in a host FA round, is answered INERT and the original is never called (Board EXIT 0x5478e0 would dereference the null 0x508ef0 answer).

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
static int klbr_apick; static volatile LONG klbr_run_skip[2], klbr_npick;      /* ArcadePick; Loot / Board RUN calls answered inert (coroutine rule) */
static int klbr_bhold, klbr_bnode, klbr_bs0, klbr_blog; static long klbr_bl_new, klbr_bl_rep, klbr_bl_gate, klbr_bl_sec; static int klbr_bn_ok, klbr_bn_told; static float klbr_bn_pos[3]; static DWORD klbr_bl_at[16];      /* wk-boardgap 11-03 (all default 0): BoardHold ms the real Board tactic keeps a bot after its last Board evaluate / RUN-resume stamp; BoardNode: the crowd test targets the boarding node; BoardStage0: stage 3 to a no-box crowd bot; BoardLog: diagnostics (line counters, per-bot 1 s clock), node place (bn_ok 1 in van state 3 / 4 when readable) */
static int klbr_bstage; static long klbr_bs_defer_n, klbr_bs_real, klbr_bs_fb;      /* BoardStage: on; bots whose hook boarding was deferred, boarded by the real Board tactic (slot 45), boarded by the fallback */
static int klbr_dropc; static long klbr_dc_offered, klbr_dc_grabs;      /* DropCands: slot 202 also offers valid type-1 drops; drops offered / drop grabs started */
static int klbf_brain_drop_ok(DWORD o);      /* klbotfill.c: a tracked drop that passes kdf_drop_ok (unhidden, armed after a real drain) */
static int klbf_brain_targeted(DWORD o);     /* klbotfill.c: a puppeteer bot (phase 1) walks to o */
/* DropCands GUESS (review 11-03): that Arcade's second slot-202 list (rules+0xdb8 / count +0xdac per bots_loot.md; hud_values.md says +0xda8) holds these type-1 drops is not verified. Arcade also applies
   windows (stacks 800 / dy 400, drops 400 / dy 200, tuning +0xc1c..+0xc28); this slot 202 applies none, for stacks as before and now for drops (cops carry the loot far from the bots on DD05 / DD09).
   The pump pays a drop in parts through 0x4e3f40 and does not return an emptied drop to the pool (0x57f320, stage-2 R9 unverified); an emptied drop stays registered with amount 0 (filtered out). */
static int klbr_claims; static DWORD klbr_cur_snd; static long klbr_claim_skip, klbr_claim_fb;      /* StackClaims; the soldier whose evaluate / RUN slice is running (game thread only); stacks skipped, fallbacks to grabs-only */
static int klbr_bridge, klbr_board, klbr_traitor, klbr_boardreal, klbr_cops, klbr_level = 6, klbr_lootwin = 1500, klbr_boardwin = 2000;      /* stage 2 / 3 switches (all default 0) */
static DWORD klbr_game_tid;             /* the thread of the hook tick (SteamAPI_RunCallbacks gameplay call) */
static int klbr_verdict_n;
static int klbr_realrun;                /* [Brain] RealRun (the longjmp thunk is installed), 0 unless init succeeded */

/* ---- the soldier tags ------------------------------------------------------------------------------------------------------------------------------------------------------------- */
struct klbr_s { DWORD snd, actor, tac[3], seenAt, builtAt, nzAt, bnzAt, wSince, wUntil, s45At, pick, pickAt; float wpos[3]; int state, rec, traitor, flt, wHas, pendBoard; };      /* rec: shadow crew record 1..11 (0 none); bnzAt: tick of the last Board evaluate > 0;
                                                                                                    wSince / wUntil / wpos: the hand-off stall watchdog (kbr_watch); flt: framed faults of this bot (2 = never handed again); pendBoard: slot 45 asked, the pump boards it */      /* state 0 free, 1 built by us, 2 refused (told once), 3 pending build */
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

/* ---- forward declarations (klbotfill.c is included AFTER this file; these are small ledger helpers defined there) ----------------------------------------------------------------- */
static struct klbr_s *klbr_find(DWORD snd);
static void klbr_sync(DWORD now);
static int klbf_ob_ledger(DWORD actor, int *aboard, long *tally);   /* klbotfill.c: the host ledger of one bot */
static int klbf_ob_called(DWORD actor);                             /* klbotfill.c: BoardStage, 1 when the bot is ordered to / inside the exit box or aboard (read only) */
static int klbf_brain_take(DWORD ctrl, int amt);        /* the game's 0x4e3f40 through the puppeteer's guard; -> the stack's amount left, -1 when refused */
static void klbf_brain_credit(DWORD actor, int amt, int done);    /* tally += amt; done: grabs++ and the loot voice */
static void klbf_brain_boarded(DWORD actor);            /* phase := 3 (aboard), as OnlineBoardAll does */
static int klbf_brain_board_call(DWORD actor);          /* the existing OnlineBoardAll squad-removal call (guarded there) */
static float klbf_brain_near(void);                     /* OnlineTacticsNear, cm */
static int klbf_bn_trig(float out[3]);                  /* klbotfill.c: BoardNode / BoardLog, the exit trigger's place (1 when known) */

/* ---- the shadow block layout (stage 2, design section 2) ----------------------------------------------------------------------------------------------------------------------- */
#define KLBR_W_SIZE 0xf30               /* the Heist rules size; the rules fields live in the first KLBR_W_SIZE bytes of the block */
#define KLBR_OFF_CREW 0x1000            /* 12 records x 0x7c */
#define KLBR_OFF_FREE 0x1700            /* 12 bytes: 0 live, nonzero skipped */
#define KLBR_OFF_SCORE 0x1800           /* S2, 0x400 bytes */
#define KLBR_OFF_CLI 0x1c00             /* 12 client dummies x 0x20 */
#define KLBR_BLOCK 0x2000
#define KLBR_NREC 12
#define KLBR_RSTRIDE 0x7c
#define KLBR_SLOT_BOARD 45              /* 0xb4 / 4 */
#define KLBR_SLOT_CAND 202              /* 0x328 / 4 */
#define KLBR_P32(a) (*(volatile DWORD *)(DWORD_PTR)(a))
#define KLBR_PB(a) (*(volatile BYTE *)(DWORD_PTR)(a))
#define KLBR_PF(a) (*(volatile float *)(DWORD_PTR)(a))
#define KLBR_REC(i) (klbr_crew + KLBR_RSTRIDE * (DWORD)(i))
#define KLBR_FLAGS(i) (klbr_score + 0x1d4 + 4 * (DWORD)(i))

/* ---- the wrappers ----------------------------------------------------------------------------------------------------------------------------------------------------------------- */
static DWORD klbr_org[9];               /* [class*3 + 0 slot 2, 1 slot 3, 2 slot 11] the originals */
static volatile LONG klbr_hits[9]; static DWORD klbr_tid[9][4]; static volatile LONG klbr_ntid[9];
static volatile LONG klbr_ev_nz[3], klbr_ev_flt[3], klbr_run_flt[3]; static float klbr_ev_max[3], klbr_ev_last[3];
static DWORD klbr_vt_copy[3];           /* the DLL-owned vtable copies (pointer to slot 0) */
static int klbr_vt_ready;
static DWORD klbr_shadow, klbr_shadow_vt, klbr_crew, klbr_free, klbr_score, klbr_cli;   /* the shadow rules block W and the parts of it */
static int klbr_sw_told, klbr_swaps, klbr_sw_flt, klbr_sw_bad, klbr_frames, klbr_slow, klbr_slow_run, klbr_nrevoke, klbr_crash_told; static unsigned klbr_us_max;
static int klbr_depth;                  /* swap frame nesting depth, game thread only (kbr_frame_enter / leave) */
static DWORD klbr_sv_G, klbr_sv_sm, klbr_sv_rules, klbr_sv_role;      /* what the OUTERMOST frame saved */
static DWORD klbr_sync_at; static int klbr_van = -1;      /* last sync tick; van state byte mirrored from the real rules (-1 never) */

static void __cdecl klbr_hit(int id)    /* any thread: counters only, no log */
{
    DWORD tid = GetCurrentThreadId(); LONG k, n = klbr_ntid[id];
    InterlockedIncrement(&klbr_hits[id]);
    for (k = 0; k < n && k < 4; k++) if (klbr_tid[id][k] == tid) return;
    if (n < 4) { klbr_tid[id][n] = tid; klbr_ntid[id] = n + 1; }
}

/* slot 3 of Loot and Traitor is 0x66b570, a bare `ret` (design 0.2): counted, then the tail-jump (any signature). Slot 3 of Board is a C wrapper (it needs the frame, design 0.3). */
#define KLBR_STUB(nm, ix) static __declspec(naked) void nm(void) { \
    __asm push ecx __asm push edx __asm push ix __asm call klbr_hit __asm add esp, 4 __asm pop edx __asm pop ecx __asm jmp dword ptr [klbr_org + 4 * ix] }
KLBR_STUB(klbr_st_l3, 1)
KLBR_STUB(klbr_st_t3, 7)

typedef float (__fastcall *klbr_evfn)(DWORD, DWORD);
typedef void (__fastcall *klbr_runfn)(DWORD, DWORD);
static float klbr_call_ev(DWORD fn, DWORD self, int *flt)      /* the original evaluate under a fault guard */
{
    float r = 0.0f;
    __try { r = ((klbr_evfn)(DWORD_PTR)fn)(self, 0); }
    __except (EXCEPTION_EXECUTE_HANDLER) { *flt = 1; r = 0.0f; }
    return r;
}
static void klbr_call_run(DWORD fn, DWORD self, int *flt)      /* run / exit: void-typed (design 0.1: no stack argument, plain ret), so no x87 result is popped */
{
    __try { ((klbr_runfn)(DWORD_PTR)fn)(self, 0); }
    __except (EXCEPTION_EXECUTE_HANDLER) { *flt = 1; }
}

static void klbr_swap_out(void)         /* restore what the outermost swap_in saved, then verify it (risk R4) */
{
    __try {
        KLBR_P32(klbr_sv_G + 0x54) = klbr_sv_rules; KLBR_P32(klbr_sv_sm + 0x54) = klbr_sv_role;
        if (KLBR_P32(klbr_sv_G + 0x54) != klbr_sv_rules || KLBR_P32(klbr_sv_sm + 0x54) != klbr_sv_role) { klbr_sw_bad++; KLBR_P32(klbr_sv_G + 0x54) = klbr_sv_rules; KLBR_P32(klbr_sv_sm + 0x54) = klbr_sv_role; }
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_sw_flt++; }
}
static int klbr_swap_in(DWORD G, DWORD sm)      /* 1 = swapped. Reads both first, so a failed read changes nothing */
{
    DWORD r = 0, o = 0;
    __try { r = KLBR_P32(G + 0x54); o = KLBR_P32(sm + 0x54); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_sw_flt++; return 0; }
    klbr_sv_G = G; klbr_sv_sm = sm; klbr_sv_rules = r; klbr_sv_role = o;
    __try { KLBR_P32(G + 0x54) = klbr_shadow; KLBR_P32(sm + 0x54) = 0; }
    __except (EXCEPTION_EXECUTE_HANDLER) { klbr_sw_flt++; klbr_swap_out(); return 0; }
    return 1;
}

/* ---- RealRun: the msvcr90 longjmp thunk (UNTESTED) ----------------------------------------------------------------------------------------------------------------------------------- */
/* Everything from here to klbr_w_longjmp is SEH-FREE on purpose: no __try / __except / __finally, no call into anything that has one. The reads are plain pointer reads of memory that is always
   valid: our own statics, the two exe globals (.data), the tactic objects WE built (leaked on purpose, never freed: the soldier dtor does not touch +0x5f0..+0x5f8, see the header), and G / sm
   (live game objects, nonzero-checked). klh_rd (ReadProcessMemory) is also SEH-free but is a syscall per read and not needed here. klog is avoided too (it is SEH-free but the first 8 swap-ins are queued
   in klbr_rr_first[] and written by the hook tick). A SEH-protected put-back (klbr_rr_fix) is only used from the tick and the vectored handler, never from the thunk. */
#define KLBR_RRT 256
#define KLBR_ADDR_SCHEDBUF 0x0168e4c8   /* the scheduler's jmp_buf every slice ends with (yield 0x55ba52, goal end 0x65bc8a) */
static DWORD klbr_rrt[KLBR_RRT]; static BYTE klbr_rrc[KLBR_RRT]; static volatile LONG klbr_rrn;      /* Loot / Board tactic objects we built (append-only ring); class 0 Loot, 1 Board */
static void (__cdecl *klbr_real_longjmp)(void *, int);
static volatile LONG klbr_rr_sw;        /* 1 = the thunk has the shadow swapped in (game thread only) */
static DWORD klbr_rr_G, klbr_rr_sm, klbr_rr_rules, klbr_rr_role;      /* what the thunk saved */
static volatile LONG klbr_rr_in, klbr_rr_out, klbr_rr_leak, klbr_rr_veh, klbr_rr_mis, klbr_rr_foreign, klbr_rr_nested, klbr_rr_val[3], klbr_rr_told, klbr_rr_leak_told, klbr_rr_mode, klbr_rr_t10, klbr_rr_hand_ev, klbr_rr_hand_run;
static struct { DWORD goal, ctx, val, snd, tid; int rec, cls; } klbr_rr_first[8];      /* the first swap-ins, logged by the tick */

static int klbr_rr_match(DWORD buf, DWORD *tac, int *cls)      /* buf is the live ctx [tac+0xc] of a Loot / Board tactic we built (read live: 0x63c75c frees and reuses the ctx) */
{
    LONG n = klbr_rrn; int i, m = n < KLBR_RRT ? (int)n : KLBR_RRT;
    for (i = 0; i < m; i++) { DWORD t = klbr_rrt[i]; if (t && *(volatile DWORD *)(DWORD_PTR)(t + 0xc) == buf) { *tac = t; *cls = klbr_rrc[i]; return 1; } }
    return 0;
}
static void klbr_rr_put_back(void)      /* PLAIN (no SEH): each field only while it still reads what the swap wrote, else counted as a mismatch and left */
{
    DWORD cr = *(volatile DWORD *)(DWORD_PTR)(klbr_rr_G + 0x54), cl = *(volatile DWORD *)(DWORD_PTR)(klbr_rr_sm + 0x54); int m = kbr_lj_restore_mask(cr, klbr_shadow, cl);
    if (m & 1) *(volatile DWORD *)(DWORD_PTR)(klbr_rr_G + 0x54) = klbr_rr_rules;
    if (m & 2) *(volatile DWORD *)(DWORD_PTR)(klbr_rr_sm + 0x54) = klbr_rr_role;
    if (m != 3) klbr_rr_mis++;
    klbr_rr_sw = 0; klbr_rr_out++; klbr_cur_snd = 0;
}
static void klbr_rr_swap_in(DWORD ctx, int val, DWORD tac, int cls)
{
    DWORD G = *(volatile DWORD *)(DWORD_PTR)KLH_VA(KLBR_GLOBAL_G), sm = *(volatile DWORD *)(DWORD_PTR)KLH_VA(KLNET_SESSION), rules, role, tid = GetCurrentThreadId(); LONG k;
    if (!klbr_shadow || !klbr_game_tid || tid != klbr_game_tid) { klbr_rr_foreign++; return; }      /* only the host game thread (its tick id); another thread resuming a goal of ours is counted and left alone */
    if (klbr_depth > 0) { klbr_rr_nested++; return; }      /* a DLL frame already has the shadow in */
    if (G <= 0xffff || sm <= 0xffff) return;
    if (*(volatile DWORD *)(DWORD_PTR)(sm + 0x5c) != 4) { klbr_rr_mode++; return; }      /* judge 11-03: 0x508ef0 hands out [G+0x54] only in session mode 4; any other mode the slice would read null rules, so leave it unswapped (RUN then exits on its own gate) */
    rules = *(volatile DWORD *)(DWORD_PTR)(G + 0x54); role = *(volatile DWORD *)(DWORD_PTR)(sm + 0x54);
    if (rules == klbr_shadow) { klbr_rr_nested++; return; }      /* never save the shadow as the "real" rules */
    klbr_rr_G = G; klbr_rr_sm = sm; klbr_rr_rules = rules; klbr_rr_role = role;
    *(volatile DWORD *)(DWORD_PTR)(G + 0x54) = klbr_shadow; *(volatile DWORD *)(DWORD_PTR)(sm + 0x54) = 0;
    klbr_rr_sw = 1; k = klbr_rr_in++; klbr_rr_val[val == 2 ? 2 : 1]++; klbr_cur_snd = *(volatile DWORD *)(DWORD_PTR)(tac + 4);      /* StackClaims: a slot 202 call inside this slice knows who asks */
    if (val == 1) { struct klbr_s *e = klbr_find(*(volatile DWORD *)(DWORD_PTR)(tac + 4)); if (e && e->state == 1) { if (cls == 0) e->nzAt = GetTickCount() | 1u; else e->bnzAt = GetTickCount() | 1u; klbr_rr_hand_run++; } }      /* bs3 judge: a live RUN slice keeps its bot handed over (own table only, no game call); the 8 s stall watchdog still takes a bot back that does not move */
    if (k < 8) { klbr_rr_first[k].goal = tac; klbr_rr_first[k].ctx = ctx; klbr_rr_first[k].val = (DWORD)val; klbr_rr_first[k].tid = tid; klbr_rr_first[k].cls = cls; klbr_rr_first[k].snd = *(volatile DWORD *)(DWORD_PTR)(tac + 4); }
}
static void __cdecl klbr_w_longjmp(void *buf, int val)      /* the exe's `call [0xb10370]` lands here with the real longjmp's arguments; the real one is ALWAYS called last and never returns */
{
    DWORD b = (DWORD)(DWORD_PTR)buf, tac = 0, sbuf = (DWORD)(DWORD_PTR)KLH_VA(KLBR_ADDR_SCHEDBUF); int match = 0, cls = 0, act;
    if (klbr_realrun) {
        if (b != sbuf && !klbr_rr_sw && (val == 1 || val == 2)) match = klbr_rr_match(b, &tac, &cls);
        act = kbr_lj_decide(b, val, sbuf, klbr_rr_sw != 0, match);
        if (act == KBR_LJ_RESTORE) { if (GetCurrentThreadId() == klbr_game_tid) klbr_rr_put_back(); else klbr_rr_foreign++; }      /* review 11-03: only the game thread that swapped may put back */
        else if (act == KBR_LJ_SWAP) klbr_rr_swap_in(b, val, tac, cls);
    }
    klbr_real_longjmp(buf, val);
}
static void klbr_rr_fix(void)           /* SEH-protected put-back for the tick and the vectored handler (the swapped addresses could in theory be stale by then) */
{
    __try { if (klbr_rr_sw) klbr_rr_put_back(); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_rr_sw = 0; klbr_sw_flt++; }
}
static void klbr_veh_restore(void)      /* called by the vectored handler (klhook.c) for a non-breakpoint fault in the exe: a fault with the shadow swapped in on the game thread puts the real rules back first */
{
    if (!klbr_rr_sw || GetCurrentThreadId() != klbr_game_tid) return;
    klbr_rr_fix(); klbr_rr_veh++;
    klog("brain: realrun: a fault happened with the shadow rules swapped in by the longjmp thunk: real rules put back (swap-ins %ld, out %ld)", (long)klbr_rr_in, (long)klbr_rr_out);
}

/* may this tactic call run in a frame? Only for one of OUR assigned bots, on the host game thread, in a host FA round (role 2, mode 4, state 0x19), with the tactic's switch on. A nested call
   (inside a frame the role reads 0) is wanted when its soldier is ours. Not wanted -> the caller returns the inert answer and NEVER calls the original (design 4, risk R2). */
static int klbr_wanted(int cls, DWORD self, struct klbr_s **pe)
{
    DWORD sm, role = 0, mode = 0, state = 0, snd; struct klbr_s *e; int on = cls == 0 ? klbr_loot : cls == 1 ? klbr_board : klbr_traitor;
    if (!on || !klbr_shadow || GetCurrentThreadId() != klbr_game_tid || self < 0x10000) return 0;
    if (!(snd = klh_rd32(self + 4)) || snd < 0x10000) return 0;
    e = klbr_find(snd);
    if (klbr_depth > 0 || klbr_rr_sw) { if (!e || e->state != 1 || e->rec <= 0) return 0; *pe = e; return 1; }      /* nested: inside a DLL frame or a thunk-swapped slice the shadow is already in (a role read there is 0) */
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return 0;
    if (role != 2 || mode != 4 || state != KLB_ROUND) return 0;
    if (!e || e->state != 1) return 0;
    if (e->rec <= 0 || kbr_sync_stale(GetTickCount(), klbr_sync_at, 250)) klbr_sync(GetTickCount());      /* data only: no game call */
    if (e->rec <= 0) return 0;
    *pe = e; return 1;
}

/* ONE original tactic call inside the frame. Outermost call: swap, call, restore in __finally. Nested call: just call (already swapped). isfloat: evaluate (st0), else run / exit (void). */
static float klbr_framed(int id, DWORD self, int isfloat, int *flt)
{
    float r = 0.0f; DWORD G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)), sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)); LARGE_INTEGER t0, t1, fq; int outer;
    if (G <= 0xffff || sm <= 0xffff || !klbr_org[id]) return 0.0f;
    if (klbr_rr_sw) { if (isfloat) r = klbr_call_ev(klbr_org[id], self, flt); else klbr_call_run(klbr_org[id], self, flt); return r; }      /* RealRun slice: the thunk owns the swap; never swap (it would save the shadow as the real rules) */
    outer = kbr_frame_enter(&klbr_depth);
    if (outer) {
        if (!klbr_crash_told) { klbr_crash_told = 1; klog("brain: frame: first framed tactic call. A fault inside a frame is caught here, but the hook's vectored handler logs it first as CRASH (and may write a dump): a CRASH line followed by 'brain: fault' is a GUARDED fault, not a game crash"); }
        QueryPerformanceCounter(&t0);
        if (!klbr_swap_in(G, sm)) { kbr_frame_leave(&klbr_depth); return 0.0f; }
    }
    __try {
        if (isfloat) r = klbr_call_ev(klbr_org[id], self, flt); else klbr_call_run(klbr_org[id], self, flt);
    } __finally {
        if (kbr_frame_leave(&klbr_depth)) klbr_swap_out();
    }
    if (outer) {
        unsigned us; QueryPerformanceCounter(&t1); QueryPerformanceFrequency(&fq);
        us = fq.QuadPart ? (unsigned)(((t1.QuadPart - t0.QuadPart) * 1000000) / fq.QuadPart) : 0;
        klbr_swaps++; klbr_frames++; if (us > klbr_us_max) klbr_us_max = us;
        if (us > 50000u) klbr_slow++;
        if (kbr_slow_rule(us, 50000u, &klbr_slow_run, 3)) {      /* risk R6: a frame this long is visible to other threads. Review 11-03: 50 ms and three CONSECUTIVE (pathfinding in RUN or one hitch must not trip it) */
            klog("brain: frame took over 50 ms three times in a row (last %u us, wall time): Loot / Board / Traitor frames switched OFF for the rest of the session", us);
            klbr_loot = klbr_board = klbr_traitor = 0;
        }
    }
    return r;
}

static void klbr_traitor_mirror(struct klbr_s *e);
static const char *const klbr_cls_nm[3] = { "Loot", "Board", "Traitor" };
/* a framed fault (review 11-03): the bot is never handed over again after 2, the class is switched off for the session after 2 in total (a deterministic fault would repeat every AI tick) */
static void klbr_fault(int cls, struct klbr_s *e, const char *what)
{
    long n = klbr_ev_flt[cls] + klbr_run_flt[cls]; int *sw = cls == 0 ? &klbr_loot : cls == 1 ? &klbr_board : &klbr_traitor;
    if (e) e->flt++;
    if (n <= 4) klog("brain: fault: %s %s faulted inside the frame (guarded; class faults %ld, bot record %d faults %d)", klbr_cls_nm[cls], what, n, e ? e->rec : -1, e ? e->flt : 0);
    if (n >= 2 && *sw) { *sw = 0; klog("brain: fault: %s faulted twice: its frames are switched OFF for the rest of the session (the puppeteer steers these bots again)", klbr_cls_nm[cls]); }
}
static int klbr_revoked(const struct klbr_s *e, DWORD now) { return e->flt >= 2 || (e->wUntil && (long)(now - e->wUntil) < 0); }
static float klbr_ev(int cls, DWORD self)
{
    float r = 0.0f; int flt = 0, id = cls * 3 + 2, stamped = 0; struct klbr_s *e = 0;
    klbr_hit(id);
    if (klbr_wanted(cls, self, &e)) {
        int told_now = klbr_sw_told < 4 && cls == 0;
        { DWORD was = klbr_cur_snd; klbr_cur_snd = e->snd; r = klbr_framed(id, self, 1, &flt); klbr_cur_snd = was; }      /* StackClaims: slot 202 inside this evaluate knows who asks */
        if (told_now) { klbr_sw_told++; klog("brain: frame: %s evaluate under the shadow returned %.3f (frames %d, max %u us, rec %d)", "Loot", (double)r, klbr_frames, klbr_us_max, e->rec); }
    }
    if (flt) { InterlockedIncrement(&klbr_ev_flt[cls]); klbr_fault(cls, e, "evaluate"); r = 0.0f; }      /* a faulted answer is never trusted and never refreshes the hand-off */
    klbr_ev_last[cls] = r;
    if (r > 0.0f) {
        InterlockedIncrement(&klbr_ev_nz[cls]); if (r > klbr_ev_max[cls]) klbr_ev_max[cls] = r;
        if (e) {
            DWORD pc[5], pk0 = 0;
            if (cls == 0 && klbr_realrun && klh_rd(self + 0x14, pc, sizeof pc)) pk0 = (DWORD)kbr_chosen(pc, klh_rd32(self + 0x2c));
            if (cls == 0 && (!klbr_bridge || klh_rd32(self + 0x28))) { e->nzAt = GetTickCount() | 1u; stamped = 1; }      /* [tactic+0x28] = the chosen TRIGGER BOX (review 11-03, 0x451b8a): non-zero = the walk has a goal */
            else if (cls == 0 && pk0) { e->nzAt = GetTickCount() | 1u; stamped = 1; klbr_rr_hand_ev++; }      /* bs3 11-03: under RealRun the scene-query branch returns 1.0 with a chosen stack (+0x2c) but +0x28 = 0, so the hand-off never opened and the puppeteer + real RUN steered the same bot (0 grabs, 0 boarded); the chosen stack opens it */
            else if (cls == 0) { static int told; DWORD cand[5]; if (told < 6 && klh_rd(self + 0x14, cand, sizeof cand) && kbr_chosen(cand, klh_rd32(self + 0x2c))) { told++; klog("brain: gate: Loot evaluate %.3f with a chosen stack %08lx but trigger box +0x28 = 0: NOT handed over (if bots never grab, the gate should use the chosen stack)", (double)r, (unsigned long)kbr_chosen(cand, klh_rd32(self + 0x2c))); } }      /* DIAGNOSTIC (review 11-03, unconfirmed concern) */
            if (cls == 1) e->bnzAt = GetTickCount() | 1u;
            if (cls == 0) { DWORD cand[5], pk; if (klh_rd(self + 0x14, cand, sizeof cand) && (pk = (DWORD)kbr_chosen(cand, klh_rd32(self + 0x2c))) != 0) { e->pick = pk; e->pickAt = GetTickCount() | 1u; } }      /* ArcadePick: the Arcade evaluate's own choice, read for the puppeteer */
        }
    }
    if (!e) return r;      /* not wanted: r is 0.0 and the original was not called */
    if (cls != 2 && klbr_revoked(e, GetTickCount())) return 0.0f;      /* the stall watchdog gave this bot back to the puppeteer: the AI must not steer it too */
    /* what the AI sees: Loot and Board NEVER (bs1 11-03: once the AI picks them it calls their RUN, a coroutine the DLL cannot run online, see kbr_orig_ok); the evaluate still
       runs in the frame and ArcadePick hands its choice to the puppeteer. Traitor always (its RUN only flips a bit and does not yield) */
    if (klbr_realrun) {      /* RealRun: the pre-f5f0ccd3e rules; the AI's RUN call lands on the original through the vtable copy, the thunk swaps the shadow for each slice */
        int van_ok = kbr_board_state_ok(klbr_van), vis = cls == 0 ? (klbr_puppet && !(klbr_boardreal && van_ok) && stamped) : cls == 1 ? (klbr_boardreal && van_ok) : 1;      /* bs3: Loot is shown only with the hand-off stamped on this call, so the puppeteer never steers a bot the real RUN steers */
        return vis ? r : 0.0f;
    }
    return cls == 2 ? r : 0.0f;
}
static float __fastcall klbr_ev_l(DWORD self, DWORD d) { (void)d; return klbr_ev(0, self); }
static float __fastcall klbr_ev_b(DWORD self, DWORD d) { (void)d; return klbr_ev(1, self); }
static float __fastcall klbr_ev_t(DWORD self, DWORD d) { (void)d; return klbr_ev(2, self); }

static void klbr_run(int cls, int slot, DWORD self)      /* slot 0 = RUN (slot 2 of the vtable), 1 = EXIT (slot 3) */
{
    int flt = 0, id = cls * 3 + slot; struct klbr_s *e = 0;
    klbr_hit(id);
    if (!kbr_orig_ok(cls, slot)) {      /* coroutine rule: Loot / Board RUN are never called (inert return = the goal ends; the AI re-plans, the puppeteer steers) */
        if (InterlockedIncrement(&klbr_run_skip[cls]) == 1) klog("brain: run: the AI asked for the %s RUN: answered inert. It is a setjmp coroutine (yield 0x55b9f0) that crashed the host in bs1 (c0000029); the DLL never runs it online", klbr_cls_nm[cls]);
        return;
    }
    if (klbr_wanted(cls, self, &e)) {
        klbr_framed(id, self, 0, &flt);
        if (cls == 2 && slot == 0 && !flt) klbr_traitor_mirror(e);
    }
    if (flt) { InterlockedIncrement(&klbr_run_flt[cls]); klbr_fault(cls, e, slot ? "exit" : "run"); }
}
static void __fastcall klbr_run_l(DWORD self, DWORD d) { (void)d; klbr_run(0, 0, self); }
static void __fastcall klbr_run_b(DWORD self, DWORD d) { (void)d; klbr_run(1, 0, self); }
static void __fastcall klbr_exit_b(DWORD self, DWORD d) { (void)d; klbr_run(1, 1, self); }      /* 0x5478e0 needs 0x508ef0 non-null (design 0.3): frame or nothing */
static void __fastcall klbr_run_t(DWORD self, DWORD d) { (void)d; klbr_run(2, 0, self); }

/* the DLL-owned vtable copies (once): [-1] RTTI word + 15 slots, slots 2 / 3 / 11 replaced, slot 0 stays the game's destructor */
static int klbr_make_vtables(void)
{
    static const DWORD st2[3] = { (DWORD)(DWORD_PTR)klbr_run_l, (DWORD)(DWORD_PTR)klbr_run_b, (DWORD)(DWORD_PTR)klbr_run_t };
    static const DWORD st3[3] = { (DWORD)(DWORD_PTR)klbr_st_l3, (DWORD)(DWORD_PTR)klbr_exit_b, (DWORD)(DWORD_PTR)klbr_st_t3 };
    DWORD ev[3]; int c;
    if (klbr_vt_ready) return 1;
    if (klbr_realrun) {      /* RealRun: slots 2 / 3 go straight to the originals; a stack mismatch is not caught by anything, so every entry is checked FIRST and all-or-nothing */
        static const DWORD want[3] = { 0x007bc7d0u, 0x0082f970u, 0x005478e0u }; DWORD l[KLBR_NSLOT], b[KLBR_NSLOT];
        if (!klh_rd(klbr_vt_va[0] + (DWORD)klh_delta, l, sizeof l) || !klh_rd(klbr_vt_va[1] + (DWORD)klh_delta, b, sizeof b) || l[2] != want[0] + (DWORD)klh_delta || b[2] != want[1] + (DWORD)klh_delta || b[3] != want[2] + (DWORD)klh_delta) {
            klog("brain: realrun: the Loot / Board vtable slots do not read as RUN 0x7bc7d0 / 0x82f970 / EXIT 0x5478e0: RealRun off (no vtable pointed at an original), PuppetOff / BoardReal forced off too"); klbr_realrun = 0; klbr_puppet = klbr_boardreal = 0;
        }
    }
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
        if (klbr_realrun) {      /* RealRun: the coroutine bodies are reached with NO DLL frame (the entries were verified above, before any copy) */
            if (kbr_run_direct(1, c, 0)) blk[1 + 2] = org[2];
            if (kbr_run_direct(1, c, 1)) blk[1 + 3] = org[3];
        }
        klbr_vt_copy[c] = (DWORD)(DWORD_PTR)(blk + 1);
    }
    klbr_vt_ready = 1;
    klog("brain: build: vtable copies ready (Loot %08lx, Board %08lx, Traitor %08lx; slots 2 / 3 / 11 wrapped, slot 0 = the game's destructor)", (unsigned long)klbr_vt_copy[0], (unsigned long)klbr_vt_copy[1], (unsigned long)klbr_vt_copy[2]);
    return 1;
}

/* ---- the grab table (stage 2 bridge, design 5.3): per shadow seat, DLL-owned ---------------------------------------------------------------------------------------------------------- */
static struct { DWORD ctrl, last; float timer; int outside, on; } klbr_gr[KLBR_NREC];
static int klbr_ngrab, klbr_npay, klbr_nabort, klbr_nstart; static long klbr_paid;
static int klbr_s202_n, klbr_s202_told, klbr_s45_n, klbr_ntraitor;

static void __fastcall klbr_s45(DWORD rules, DWORD edx, DWORD actor, DWORD arg2);
static DWORD __fastcall klbr_s202(DWORD rules, DWORD edx, const float *pos, DWORD *out);

static void klbr_shadow_reset(void)      /* zero the crew table, flags and grab table; re-point the rules fields. Own memory only. */
{
    int i;
    if (!klbr_shadow) return;
    memset((void *)(DWORD_PTR)(klbr_shadow + 4), 0, KLBR_BLOCK - 4);      /* slot 0 (the vtable pointer) stays */
    memset(klbr_gr, 0, sizeof klbr_gr);
    klbr_crew = klbr_shadow + KLBR_OFF_CREW; klbr_free = klbr_shadow + KLBR_OFF_FREE; klbr_score = klbr_shadow + KLBR_OFF_SCORE; klbr_cli = klbr_shadow + KLBR_OFF_CLI;
    KLBR_P32(klbr_shadow + 0x348) = klbr_crew; KLBR_P32(klbr_shadow + 0x34c) = klbr_free; KLBR_P32(klbr_shadow + 0x350) = KLBR_NREC - 1; KLBR_P32(klbr_shadow + 0x354) = KLBR_NREC; KLBR_P32(klbr_shadow + 0x5f8) = klbr_score;
    for (i = 0; i < KLBR_NREC; i++) { KLBR_PB(klbr_free + i) = 1; KLBR_P32(KLBR_REC(i)) = klbr_cli + 0x20 * (DWORD)i; KLBR_PB(klbr_cli + 0x20 * (DWORD)i + 1) = (BYTE)i; }
    KLBR_PB(klbr_free + 0) = 0;      /* record 0 = the host human, live (GUESS: +4 stays 0 = "no actor", the Loot RUN null-actor query lands on it) */
    KLBR_PB(klbr_score + 0x45) = (BYTE)kbr_level_clamp(klbr_level);
    klbr_van = -1;
}

/* the shadow rules block: zero-filled 0xf30 bytes + crew table + score block + client dummies, with a private copy of the Heist vtable 0xbd3514 (slots 45 / 202 replaced by DLL stubs).
   UNTESTED live. */
static int klbr_make_shadow(void)
{
    DWORD *vt, org[256]; DWORD va = 0x00bd3514u + (DWORD)klh_delta; BYTE *blk;
    if (klbr_shadow) return 1;
    if (!klh_rd(va, org, sizeof org)) return 0;
    vt = (DWORD *)VirtualAlloc(0, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    blk = (BYTE *)VirtualAlloc(0, KLBR_BLOCK, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!vt || !blk) return 0;
    memcpy(vt, org, sizeof org);      /* the Heist methods as they are (GUESS: harmless on the mirrored fields); the tactic calls are under a fault guard */
    /* the two stubs are thiscall with 2 stack args (ret 8). Verified 11-03 in disassembly: 0x6840a0 returns with `ret 8` at 0x6841bd / 0x6841fa / 0x68428c, 0x8b94d0 with `ret 8` at 0x8b9898;
       callers: 0x74d7f0 pushes (actor, 0) for slot 45, 0x451a32 pushes (pos, out) for slot 202. A stack mismatch is NOT caught by __try, so a slot is replaced ONLY when the exe's own entry is
       that exact function (same build as the one read); otherwise the game's own method stays and this is logged. */
    if (klbr_board) { if (org[KLBR_SLOT_BOARD] == 0x006840a0u + (DWORD)klh_delta) vt[KLBR_SLOT_BOARD] = (DWORD)(DWORD_PTR)klbr_s45; else { klog("brain: board: Heist slot 45 reads %08lx, not 0x6840a0: stub NOT installed, Board / BoardReal off", (unsigned long)org[KLBR_SLOT_BOARD]); klbr_board = klbr_boardreal = 0; } }
    if (klbr_bridge) { if (org[KLBR_SLOT_CAND] == 0x008b94d0u + (DWORD)klh_delta) vt[KLBR_SLOT_CAND] = (DWORD)(DWORD_PTR)klbr_s202; else { klog("brain: bridge: Heist slot 202 reads %08lx, not 0x8b94d0: stub NOT installed, Bridge off", (unsigned long)org[KLBR_SLOT_CAND]); klbr_bridge = klbr_puppet = klbr_traitor = 0; } }
    klbr_shadow_vt = (DWORD)(DWORD_PTR)vt; klbr_shadow = (DWORD)(DWORD_PTR)blk; KLBR_P32(klbr_shadow) = klbr_shadow_vt;
    klbr_shadow_reset();
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
    if (klbr_realrun) {      /* RealRun registry: append-only, survives the round-end table clear (objects are never freed) */
        int c; for (c = 0; c < 2; c++) {
            BYTE t10 = 1; LONG k;
            if (!klh_rd(o[c] + 0x10, &t10, 1) || t10) { klbr_rr_t10++; klog("brain: realrun: %s %08lx has [tac+0x10]=%u: the first slice (0x65bbf0 slot 6) would skip the yield and run RUN unswapped, so it is NOT registered", c ? "Board" : "Loot", (unsigned long)o[c], (unsigned)t10); continue; }      /* judge 11-03 */
            k = (InterlockedIncrement(&klbr_rrn) - 1) % KLBR_RRT; klbr_rrc[k] = (BYTE)c; klbr_rrt[k] = o[c];
        }
    }
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

/* ---- the real money controls (registry 0xe09e38, count 0xe0e63c) as slot 202 and the grab see them ------------------------------------------------------------------------------- */
#define KLBR_NSCAN 128
#define KLBR_CLAIM_MS 4000u            /* StackClaims: a peer's Loot-evaluate pick keeps its stack off my candidate list this long (GUESS, bs4 11-03: re-evaluates come every few 100 ms) */
static int klbr_money_ex(DWORD o, int *amt, float pos[3], int *isdrop)        /* a takeable stack: vtable, not a drop (type 1; with DropCands a valid drop passes, *isdrop = 1), something left, armed, not behind a door, a node with a place */
{
    DWORD type = 0, ent, node, fl = 0; BYTE act = 0, shut = 0; int a = 0;
    if (isdrop) *isdrop = 0;
    if (o < 0x10000 || klh_rd32(o) != KLMV_MONEY_VT) return 0;
    if (!klh_rd(o + 0x38, &type, 4) || (type == 1 && !(klbr_dropc && isdrop)) || !klh_rd(o + 0x34, &a, 4) || a <= 0 || !klh_rd(o + 0x6c, &act, 1) || !act) return 0;
    if (klh_rd(o + 0x5c, &shut, 1) && shut) return 0;      /* GUESS: +0x5c = "behind a door" (the puppeteer's OnlineDoor test reads it so; Arcade's evaluate tests it too) */
    if (!(ent = klh_rd32(o + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, pos, 0)) return 0;
    if (type == 1) {      /* DropCands: the OnlineDropFollow rule (tracked in klbotfill.c: unhidden AND preceded by a real drain), plus the node's hidden bit read here */
        int hid = klh_rd(node + 0x3c, &fl, 4) ? ((fl & 0x400) ? 1 : 0) : -1;
        if (!kbr_drop_valid(act != 0, a, hid, klbf_brain_drop_ok(o))) return 0;
        *isdrop = 1;
    }
    *amt = a; return 1;
}
static int klbr_money_ok(DWORD o, int *amt, float pos[3]) { return klbr_money_ex(o, amt, pos, 0); }      /* stacks only (the original rule) */
static int klbr_money_cand(DWORD o, int *amt, float pos[3])      /* the pump's re-check: a stack, or with DropCands a valid drop */
{
    int dr = 0; return klbr_money_ex(o, amt, pos, klbr_dropc ? &dr : 0);
}
static int klbr_money_near(const float p[3], unsigned long *out, int cap, DWORD me)      /* me = the asking soldier (0 = unknown): with StackClaims a stack another bot grabs or freshly picked is skipped */
{
    DWORD rn = klh_rd32((DWORD_PTR)KLH_VA(0x00e0e63c)), reg[0x400], q, j, now = GetTickCount(); unsigned long obj[KLBR_NSCAN], cc[2 * KLBR_MAX], co[2 * KLBR_MAX], ca[2 * KLBR_MAX]; unsigned char isd[KLBR_NSCAN]; float d2[KLBR_NSCAN]; int n = 0, nc = 0, i, pass, r;
    if (klbr_claims) for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i];
        if (e->state != 1) continue;
        if (e->rec > 0 && e->rec < KLBR_NREC && klbr_gr[e->rec].on) { cc[nc] = klbr_gr[e->rec].ctrl; co[nc] = e->snd; ca[nc] = 0; nc++; }
        if (e->pick && e->pickAt) { cc[nc] = e->pick; co[nc] = e->snd; ca[nc] = e->pickAt; nc++; }
    }
    for (pass = 0; pass < 2; pass++) {      /* pass 1: every stack is claimed by peer PICKS -> grabs-only (the bot still gets a stack nobody is grabbing) */
    n = 0;
    if (rn > 0x1000) rn = 0x1000;
    for (q = 0; q < rn && n < KLBR_NSCAN; q += 0x400) {
        DWORD m = rn - q < 0x400 ? rn - q : 0x400;
        if (!klh_rd((DWORD_PTR)KLH_VA(0x00e09e38) + 4 * q, reg, 4 * m)) break;
        for (j = 0; j < m && n < KLBR_NSCAN; j++) {
            float mp[3]; int amt, dr = 0;
            if (!klbr_money_ex(reg[j], &amt, mp, klbr_dropc ? &dr : 0)) continue;
            if (nc && kbr_claimed(reg[j], me, !pass, cc, co, ca, nc, now, KLBR_CLAIM_MS)) { if (!pass) klbr_claim_skip++; continue; }
            obj[n] = reg[j]; isd[n] = (unsigned char)dr; d2[n] = (mp[0] - p[0]) * (mp[0] - p[0]) + (mp[1] - p[1]) * (mp[1] - p[1]) + (mp[2] - p[2]) * (mp[2] - p[2]); n++;
        }
    }
    if (n || !nc || !me) break;
    klbr_claim_fb++;
    }
    r = kbr_cand_sort(obj, d2, n, out, cap);      /* DropCands review 11-03: Arcade's slot 202 (0x8b94d0) sorts the survivors of BOTH lists together by distance (bots_loot.md:177-186), so stacks and drops are merged */
    if (!klbr_dropc) return r;
    for (i = 0; i < r; i++) { int k; for (k = 0; k < n; k++) if (obj[k] == out[i]) { if (isd[k]) klbr_dc_offered++; break; } }
    return r;
}

/* ---- the sync: the host ledger -> the shadow crew table / score block / van state (DATA ONLY: no game call, safe inside an AI wrapper) ------------------------------------------------ */
static void klbr_sync(DWORD now)
{
    int i, k, used[KLBR_NREC]; DWORD G, real = 0;
    if (!klbr_shadow) return;
    memset(used, 0, sizeof used); used[0] = 1;
    for (i = 0; i < KLBR_MAX; i++) { struct klbr_s *e = &klbr_t[i]; if (e->state != 1) { e->rec = 0; continue; } if (e->rec > 0 && e->rec < KLBR_NREC && !used[e->rec]) used[e->rec] = 1; else e->rec = 0; }
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i];
        if (e->state != 1 || e->rec > 0) continue;
        for (k = 1; k < KLBR_NREC && used[k]; k++) ;
        if (k >= KLBR_NREC) continue;      /* 11 bots at most (the lobby caps the Ally bots below this) */
        used[k] = 1; e->rec = k; memset((void *)(DWORD_PTR)(KLBR_REC(k) + 4), 0, KLBR_RSTRIDE - 4); memset(&klbr_gr[k], 0, sizeof klbr_gr[k]);
    }
    /* review 11-03: the van state first, so the stage bytes below see this sync's van (was one sync late) */
    if (klbr_depth == 0 && (G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G))) > 0xffff && (real = klh_rd32(G + 0x54)) > 0xffff && real != klbr_shadow) {      /* the van state the Board / Loot code reads */
        DWORD vt = klh_rd32(real);
        if (KLH_RULES_SV_OK(vt) || KLH_RULES_CL_OK(vt)) {      /* review 11-03: online the rules vtable is often a private copy (klroundkeep.c / klucc_down.c); the exact-address test missed it and left the van at -1 */
            BYTE vb = 0; DWORD f1 = 0, f2 = 0, f3 = 0;
            if (klh_rd(real + 0x1dc, &vb, 1) && klh_rd(real + 0x1d8, &f1, 4) && klh_rd(real + 0x1e0, &f2, 4) && klh_rd(real + 0x1e4, &f3, 4)) {
                DWORD nd = f2 > 0xffff ? klh_rd32(f2 + 4) : 0; BYTE t4[12];
                int nok = nd > 0xffff && klh_rd(nd + 0x18, t4, 4) && klh_rd(nd + 0x24, t4, 12) && klh_rd(nd + 0x50, t4, 4);      /* judge 11-03: Board RUN (0x5aeb00 / 0x6be1c0) reads [[+0x1e0]+4]+0x18/+0x24/+0x50 unchecked; an unreadable van node gets 0 (RUN then returns) */
                KLBR_PB(klbr_shadow + 0x1dc) = vb; KLBR_P32(klbr_shadow + 0x1d8) = f1; KLBR_P32(klbr_shadow + 0x1e0) = nok ? f2 : 0; KLBR_P32(klbr_shadow + 0x1e4) = nok ? f3 : 0; klbr_van = vb;
            }
        }
    }
    for (k = 0; k < KLBR_NREC; k++) { KLBR_PB(klbr_free + (DWORD)k) = used[k] ? 0 : 1; if (!used[k]) { KLBR_P32(KLBR_REC(k) + 4) = 0; KLBR_PB(KLBR_REC(k) + 0x79) = 0; } }
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i]; int aboard = 0; long tally = -1; DWORD r;
        if (e->state != 1 || e->rec <= 0) continue;
        r = KLBR_REC(e->rec);
        klbf_ob_ledger(e->actor, &aboard, &tally);      /* the host puppeteer's books: tally -1 stays when the bot has no slot yet */
        KLBR_P32(r + 4) = e->actor;
        KLBR_PB(r + 0x78) = (BYTE)kbr_stage_byte(klbr_bstage, aboard, tally, klbr_van, klbr_bstage ? klbf_ob_called(e->actor) : 0);      /* BoardStage: ALSO 3 while the van waits and the bot carries loot / is ordered to the box; GUESS (static reading only): the real Board evaluate is gated on stage 3 = reached the exit / van called. Below: GUESS: [rec+0x78] is a byte stage 1 looting / 2 carrying / 3 aboard, as klbf_ob_stage() and the Loot EVAL notes read it; +0x79 is its neighbour byte */
        KLBR_PB(r + 0x79) = (BYTE)((KLBR_PB(r + 0x79) & 2) | 1);      /* bit 0 = AI record; bit 1 (traitor) is kept: Traitor RUN sets it */
        if (aboard) KLBR_P32(r + 0x10) = 4;      /* review 11-03: only RAISED on the aboard transition; the Board tactic keeps its own progress in +0x10 between syncs (cleared only when the record is assigned) */
        /* +0x15 (grab state) is NOT rewritten here (review 11-03: the Loot code may write it itself); the grab start / end write it once, and the grab gate uses klbr_gr[].on */
        KLBR_P32(klbr_score + 0x150 + 4 * (DWORD)e->rec) = (DWORD)kbr_money_row(tally);
        KLBR_P32(KLBR_FLAGS(e->rec)) = klbr_gr[e->rec].on ? 0x2000u : 0u;
    }
    KLBR_PB(klbr_score + 0x45) = (BYTE)kbr_level_clamp(klbr_level);
    klbr_sync_at = now ? now : 1;
}

/* ---- the two replaced Heist rules slots -------------------------------------------------------------------------------------------------------------------------------------------- */
/* slot 202 (0x328), thiscall(rules; pos, out) ret 8: the loot candidates. GUESS (read in disassembly of the caller only): pos = a float[3] of the bot, out = DWORD[5] (the tactic's +0x14..+0x24); the answer in eax = how many. If pos does not read as three finite floats nothing is written and 0 is answered. */
static DWORD __fastcall klbr_s202(DWORD rules, DWORD edx, const float *pos, DWORD *out)
{
    unsigned long best[5]; float p[3]; int n, i; (void)rules; (void)edx;
    klbr_s202_n++;
    if (!out || !pos || !klh_rd((DWORD_PTR)pos, p, 12) || !kle_ok3(p)) { if (klbr_s202_told++ < 3) klog("brain: bridge: slot 202 called with pos %08lx out %08lx: pos does not read as 3 finite floats (GUESS of the argument layout wrong?): no candidates", (unsigned long)(DWORD_PTR)pos, (unsigned long)(DWORD_PTR)out); return 0; }
    n = klbr_money_near(p, best, 5, klbr_cur_snd);
    __try { for (i = 0; i < 5; i++) out[i] = (DWORD)best[i]; } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    if (klbr_s202_told++ < 4) klog("brain: bridge: slot 202: %d candidate(s) from the real money controls near (%.0f, %.0f, %.0f); nearest %08lx", n, (double)p[0], (double)p[1], (double)p[2], best[0]);
    return (DWORD)n;
}

/* slot 45 (0xb4), thiscall(rules; actor, arg2) ret 8: the Board tactic's "this bot boards". The first argument is the actor (found by the stage 2 reading; the design guessed a seat index, so a small value is looked up as a record too). */
static void __fastcall klbr_s45(DWORD rules, DWORD edx, DWORD actor, DWORD arg2)
{
    struct klbr_s *e = 0; int i; (void)rules; (void)edx;
    klbr_s45_n++;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && ((klbr_t[i].actor == actor && actor > 0xffff) || (actor < KLBR_NREC && klbr_t[i].rec == (int)actor && actor > 0))) e = &klbr_t[i];
    if (klbr_s45_n <= 8) klog("brain: board: the Board tactic called slot 45 (actor %08lx, arg2 %08lx): %s", (unsigned long)actor, (unsigned long)arg2, !e ? "not one of our bots, ignored" : klbr_boardreal ? "boarding queued for the pump (OnlineBrainBoardReal)" : "DRY (OnlineBrainBoardReal is off): log only");
    if (e) e->s45At = GetTickCount() | 1u;
    if (klbr_blog && e) { int ab = 0; long ty = 0; if (klbf_ob_ledger(e->actor, &ab, &ty) && ab) klbr_bl_rep++; else klbr_bl_new++; }      /* BoardLog: slot-45 calls for a bot not aboard yet (real) vs one already aboard (repeat); GUESS: the ledger flips on the pump, so a few same-tick repeats count as real */
    if (e && klbr_boardreal) e->pendBoard = 1;      /* review 11-03: NO game call here (we are inside the AI walk and the frame); klbr_pump boards it on the game thread outside any frame */
}

/* Traitor RUN only flips rec+0x79 bit 1 (CERTAIN, 0x488ecd). Stage 3a MIRRORS it: log, count, nothing else changes for the bot (no team change, no announce: the puppeteer has no traitor path to call). */
static void klbr_traitor_mirror(struct klbr_s *e)
{
    if (!e || e->rec <= 0 || e->traitor) return;
    if (KLBR_PB(KLBR_REC(e->rec) + 0x79) & 2) {
        e->traitor = 1; klbr_ntraitor++;
        klog("brain: traitor: Traitor RUN marked record %d (actor %08lx, level %d, money row %ld) as a traitor. MIRROR ONLY (OnlineBrainTraitor, UNTESTED): the bot's team, hostility and the announce are NOT changed", e->rec, (unsigned long)e->actor, kbr_level_clamp(klbr_level), (long)KLBR_P32(klbr_score + 0x150 + 4 * (DWORD)e->rec));
    }
}

/* ---- PuppetOff / hand-off ------------------------------------------------------------------------------------------------------------------------------------------------------- */
static int klbr_bot_pos(DWORD actor, float pos[3], int *alive);
#define KLBR_STALL_MS 8000u             /* review 11-03: a handed-off bot must move 1 m, start a grab or call slot 45 within this, else ... */
#define KLBR_REVOKE_MS 10000u           /* ... the puppeteer steers it again for this long */
static int klbr_puppet_off(DWORD snd)
{
    struct klbr_s *e; int lr = 0, br = 0, handed, progress = 0, alive = 0, ok; DWORD now = GetTickCount(); float p[3];
    if ((!klbr_puppet && !klbr_boardreal) || !snd) return 0;
    e = klbr_find(snd);
    if (!e || e->state != 1 || e->flt >= 2) return 0;
    kbr_hand(klbr_puppet && klbr_loot, 1, klbr_boardreal && klbr_board, now, e->nzAt, e->bnzAt, klbr_van, (unsigned long)(klbr_bridge ? klbr_lootwin : klbr_win_ms), (unsigned long)klbr_boardwin, &lr, &br);
    handed = lr || br;
    if (klbr_bot_pos(e->actor, p, &alive)) {      /* progress: 1 m from the last checkpoint (horizontal), a grab on, or a slot-45 call within the stall window */
        if (!e->wHas || (p[0] - e->wpos[0]) * (p[0] - e->wpos[0]) + (p[2] - e->wpos[2]) * (p[2] - e->wpos[2]) >= 100.0f * 100.0f) { if (e->wHas) progress = 1; memcpy(e->wpos, p, 12); e->wHas = 1; }
    }
    if (e->rec > 0 && klbr_gr[e->rec].on) progress = 1;
    if (e->s45At && now - (e->s45At & ~1u) < KLBR_STALL_MS) progress = 1;      /* |1 stamp: mask it or an even tick wraps */
    { DWORD was = e->wUntil; ok = kbr_watch(now, handed, progress, &e->wSince, &e->wUntil, KLBR_STALL_MS, KLBR_REVOKE_MS); progress = !was && e->wUntil; }      /* progress now = "revoked on this call" */
    if (progress) { klbr_nrevoke++; if (klbr_nrevoke <= 12) klog("brain: watchdog: record %d (actor %08lx) was handed to the real %s tactic for %u s without moving 1 m or grabbing: the puppeteer steers it again for %u s", e->rec, (unsigned long)e->actor, br ? "Board" : "Loot", KLBR_STALL_MS / 1000u, KLBR_REVOKE_MS / 1000u); }
    return ok;
}

#define KLBR_BS_MS 6000ul              /* BoardStage: how long the hook's own boarding waits for the real Board tactic, per bot (GUESS: a walk from the box edge plus the RUN's own approach) */
/* BoardStage: does the real Board tactic hold this bot right now (Board evaluate > 0 within BoardWinMs, van 3 / 4, not revoked by the watchdog)? Read only. */
#define KLBR_BS_GRACE_MS 2500ul        /* BoardStage: a bot in the box with no Board evaluate yet waits this long for one (review 11-03 defect 1; GUESS: two 1 s syncs + an AI tick) */
static int klbr_board_live(DWORD actor, DWORD since)
{
    int i, lr = 0, br = 0; DWORD now = GetTickCount();
    if (!klbr_bstage || !klbr_boardreal || !klbr_board || !actor) return 0;
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i];
        if (e->state != 1 || e->actor != actor || e->flt >= 2) continue;
        if (e->wUntil && (long)(now - e->wUntil) < 0) return 0;      /* revoked by the stall watchdog */
        kbr_hand(0, 1, 1, now, 0, e->bnzAt, klbr_van, 0, (unsigned long)klbr_boardwin, &lr, &br);
        if (!br && kbr_bs_hold(now, e->bnzAt, kbr_board_state_ok(klbr_van), (unsigned long)klbr_bhold)) br = 1;      /* BoardHold: the last evaluate / RUN-resume stamp still counts for BoardHoldMs */
        if (klbr_blog && since != 0xffffffffu && klbr_bl_gate < 80) { klbr_bl_gate++; klog("brain: boardlog: gate: actor %08lx live %d has_bnz %d bnzAt age %ld ms since %ld ms (van %d)", (unsigned long)actor, br, e->bnzAt != 0, e->bnzAt ? (long)(now - (e->bnzAt & ~1u)) : -1L, since ? (long)(now - (since & ~1u)) : -1L, klbr_van); }
        return kbr_bs_live(br, kbr_board_state_ok(klbr_van), e->bnzAt != 0, now, since, KLBR_BS_GRACE_MS);
    }
    return 0;
}
/* BoardNode: is this bot held by the real Board tactic by a REAL signal (evaluate / RUN-resume stamp within BoardWinMs or BoardHoldMs, van 3 / 4, not revoked), no grace? Read only. */
static int klbr_board_handed(DWORD actor)
{
    int i, lr = 0, br = 0; DWORD now = GetTickCount();
    if (!klbr_bnode || !klbr_bn_ok || !klbr_boardreal || !klbr_board || !actor) return 0;
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i];
        if (e->state != 1 || e->actor != actor || e->flt >= 2) continue;
        if (e->wUntil && (long)(now - e->wUntil) < 0) return 0;
        kbr_hand(0, 1, 1, now, 0, e->bnzAt, klbr_van, 0, (unsigned long)klbr_boardwin, &lr, &br);
        return br || kbr_bs_hold(now, e->bnzAt, kbr_board_state_ok(klbr_van), (unsigned long)klbr_bhold);
    }
    return 0;
}
/* BoardNode / BoardLog: once per tick from klbotfill.c; the boarding node of the parked van (state 3 / 4), read through kle_boarding (node + 500 along its x axis). GUESS: that is the position 0x5aeb00 returns (Vault 11-03 reading: it adds a bounding extent; same place as OnlineVanBoPos); not verified against the Board RUN's own compare. Logs the place once per round. */
static void klbr_bn_tick(DWORD rules, int vstate, const float trig[3])
{
    float p[3];
    klbr_bn_ok = 0;
    if ((!klbr_bnode && !klbr_blog) || !rules || vstate < 3 || vstate > 4) return;
    if (!kle_boarding(rules, p)) return;
    memcpy(klbr_bn_pos, p, 12); klbr_bn_ok = 1;
    if (!klbr_bn_told) { klbr_bn_told = 1; klog("brain: boardnode: van state %d, board node (%.0f, %.0f, %.0f), exit trigger (%.0f, %.0f, %.0f), %.1f m apart (BoardNode %d: crowd test against the node for bots the real Board tactic holds; BoardLog %d)", vstate, p[0], p[1], p[2], trig ? trig[0] : 0.0f, trig ? trig[1] : 0.0f, trig ? trig[2] : 0.0f, trig ? kle_dist(p, trig) / 100 : -1.0f, klbr_bnode, klbr_blog); }
}
/* BoardStage gate for klbotfill.c's own boarding of one bot: 1 = wait (the real Board tactic has it, at most KLBR_BS_MS), 0 = board it now; a 0 counts as a fallback boarding. *since is that bot's deferral clock. */
static int klbr_bs_gate(DWORD actor, DWORD *since)
{
    DWORD was = *since; int d;
    if (!klbr_bstage) return 0;
    d = kbr_bs_defer(1, klbr_board_live(actor, was), GetTickCount(), (unsigned long *)since, KLBR_BS_MS);
    if (d && !was) klbr_bs_defer_n++;
    if (!d) klbr_bs_fb++;
    return d;
}

#define KLBR_PICK_MS 15000u           /* a pick is only read when the puppeteer chooses a NEW stack, and that stack is re-checked there (free, unguarded, armed) */
/* ArcadePick (klbotfill.c OnlineTactics, stack choice): the money ctrl the real Loot evaluate of this soldier chose within LootWinMs, 0 = none (the puppeteer's own nearest pick stands) */
static DWORD klbr_pick(DWORD snd)
{
    struct klbr_s *e;
    if (!klbr_apick || !klbr_loot || !snd || !(e = klbr_find(snd)) || e->state != 1 || e->flt >= 2) return 0;
    return kbr_pick_live(GetTickCount(), e->pickAt, KLBR_PICK_MS) ? e->pick : 0;
}

/* ---- the bridge grab (design 5.3): the DLL owns the grab table; the Arcade tick 0x727cb0 is never run (HUD calls, reads the local player) -------------------------------------------------- */
static int klbr_bot_pos(DWORD actor, float pos[3], int *alive)
{
    DWORD hp; float hv[2] = { 0, 0 };
    if (!klh_rd(actor + 0x460, pos, 12) || !kle_ok3(pos)) return 0;
    *alive = (hp = klh_rd32(actor + 0x5fc)) && klh_rd(hp + 4, hv, 8) && hv[0] > 0;
    return 1;
}
static void klbr_grab_end(struct klbr_s *e, const char *why, int done)
{
    int k = e->rec;
    if (k <= 0) return;
    if (klbr_gr[k].on && klbr_ngrab < 400) klog("brain: grab: record %d (actor %08lx) %s stack %08lx: %s", k, (unsigned long)e->actor, done ? "finished" : "stopped", (unsigned long)klbr_gr[k].ctrl, why);
    if (!done) klbr_nabort++;
    klbr_gr[k].on = 0; klbr_gr[k].outside = 0; KLBR_PB(KLBR_REC(k) + 0x15) = 0; KLBR_P32(KLBR_FLAGS(k)) = 0;
}
/* BoardLog: per bot per second while the van waits (state 3 / 4): bnzAt age, distance to the board node and to the exit trigger, the crew record's stage byte. Max 240 lines per round (7 bots x 16 s = 112 typical). */
static void klbr_boardlog(DWORD now)
{
    int i; float tp[3]; int tv;
    if (!klbr_blog || !klbr_bn_ok || klbr_bl_sec >= 240) return;
    tv = klbf_bn_trig(tp);
    for (i = 0; i < KLBR_MAX && i < 16; i++) {
        struct klbr_s *e = &klbr_t[i]; float p[3]; int alive = 0;
        if (e->state != 1 || e->rec <= 0 || (klbr_bl_at[i] && now - klbr_bl_at[i] < 1000u)) continue;
        if (!klbr_bot_pos(e->actor, p, &alive)) continue;
        klbr_bl_at[i] = now | 1u; klbr_bl_sec++;
        klog("brain: boardlog: bot %08lx rec %d van %d alive %d bnzAt age %ld ms node %.1f m trigger %.1f m stage %u s45 age %ld ms", (unsigned long)e->actor, e->rec, klbr_van, alive, e->bnzAt ? (long)(now - (e->bnzAt & ~1u)) : -1L, kle_dist(p, klbr_bn_pos) / 100, tv ? kle_dist(p, tp) / 100 : -1.0f, (unsigned)KLBR_PB(KLBR_REC(e->rec) + 0x78), e->s45At ? (long)(now - (e->s45At & ~1u)) : -1L);
    }
}
static void klbr_pump(DWORD now)       /* game thread, from klbotfill.c's OnlineTactics tick (and nothing else): game calls (0x4e3f40) are made HERE, never inside an AI wrapper */
{
    static DWORD last; int i; float dt; DWORD sm, st = 0;
    if (!klbr_shadow || !klbr_sm_round || GetCurrentThreadId() != klbr_game_tid || klbr_depth != 0 || klbr_rr_sw) return;
    for (i = 0; i < KLBR_MAX; i++) {      /* boarding asked by slot 45 inside the AI walk (review 11-03): done here, outside any frame */
        struct klbr_s *e = &klbr_t[i];
        if (!e->pendBoard) continue;
        e->pendBoard = 0;
        if (e->state == 1 && klbr_boardreal) {
            if (klbr_bstage) { int ab = 0; long ty = 0; if (klbf_ob_ledger(e->actor, &ab, &ty) && !ab) klbr_bs_real++; }      /* BoardStage: only a bot the hook path tracks and has not already boarded counts as the real tactic's (review 11-03 defect 3: an untracked bot is not counted) */
            klbf_brain_boarded(e->actor); klbf_brain_board_call(e->actor);
        }
    }
    klbr_boardlog(now);
    if (!klbr_bridge || !klbr_puppet) return;
    dt = last ? (float)(now - last) / 1000.0f : 0.1f; last = now; if (dt > 1.0f) dt = 1.0f;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x70, &st, 4)) return;
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i]; int k = e->rec, alive = 0, amt = 0, ctrlst = 0, inside; float pos[3], mp[3]; DWORD c; BYTE st64 = 0xff;
        if (e->state != 1 || k <= 0) continue;
        if (!klbr_bot_pos(e->actor, pos, &alive)) continue;
        if (!klbr_gr[k].on) {
            DWORD node, ent, fl = 0; int hid = 0, j, free_ = 1; BYTE act = 0;
            if (!klbr_puppet_off(e->snd)) continue;      /* only a bot the REAL Loot tactic steers right now */
            {   DWORD cand[5]; if (!klh_rd(e->tac[0] + 0x14, cand, sizeof cand)) continue; c = (DWORD)kbr_chosen(cand, klh_rd32(e->tac[0] + 0x2c)); }      /* review 11-03 (0x451b8a): +0x2c = index into the 5 candidates at +0x14; +0x28 is the trigger box */
            if (!c || !klbr_money_cand(c, &amt, mp)) continue;      /* DropCands: a valid drop passes here too (only then); otherwise the pump never grabs a drop */
            if (!klh_rd(c + 0x64, &st64, 1)) continue;
            ctrlst = st64; klh_rd(c + 0x6c, &act, 1);
            ent = klh_rd32(c + 0x24); node = ent ? klh_rd32(ent + 4) : 0; if (node && klh_rd(node + 0x3c, &fl, 4)) hid = (fl & 0x400) != 0;
            for (j = 0; j < KLBR_NREC; j++) if (j != k && klbr_gr[j].on && klbr_gr[j].ctrl == c) free_ = 0;
            if (klbr_dropc && klbf_brain_targeted(c)) { DWORD ty = 0; if (klh_rd(c + 0x38, &ty, 4) && ty == 1) free_ = 0; }      /* DropCands review 11-03: a drop a puppeteer bot walks to is not started (both would take it) */
            inside = (float)sqrt((pos[0] - mp[0]) * (pos[0] - mp[0]) + (pos[2] - mp[2]) * (pos[2] - mp[2])) <= klbf_brain_near() && fabs(pos[1] - mp[1]) <= 400.0f;
            if (!inside || !kbr_grab_ok(klbr_gr[k].on ? 1 : 0, st, ctrlst, act != 0, hid, amt, free_, alive)) continue;      /* our own busy flag, not rec+0x15 (review 11-03) */
            {   int part = 0; float sec = 0;
                if (!(klh_rd(c + 0x40, &part, 4) && klh_rd(c + 0x44, &sec, 4) && part >= 1 && sec >= 0.05f && sec <= 10.0f)) { part = amt; sec = 0.7f; }      /* GUESS: +0x40 part size, +0x44 seconds per part (re/bots_loot.md; the puppeteer's OnlineLootParts reads the same) */
                klbr_gr[k].ctrl = c; klbr_gr[k].timer = sec; klbr_gr[k].last = (DWORD)part; klbr_gr[k].outside = 0; klbr_gr[k].on = 1; klbr_nstart++;
                if (klbr_dropc) { DWORD ty = 0; if (klh_rd(c + 0x38, &ty, 4) && ty == 1) klbr_dc_grabs++; }
                KLBR_PB(KLBR_REC(k) + 0x15) = 1; KLBR_P32(KLBR_FLAGS(k)) = 0x2000;
                if (klbr_ngrab++ < 400) klog("brain: grab: record %d (actor %08lx) starts stack %08lx (amt %d, part %d, %.2f s/part), %.1f m from it", k, (unsigned long)e->actor, (unsigned long)c, amt, part, (double)sec, (double)(sqrt((pos[0] - mp[0]) * (pos[0] - mp[0]) + (pos[2] - mp[2]) * (pos[2] - mp[2])) / 100.0));
            }
            continue;
        }
        c = klbr_gr[k].ctrl;
        {   int taken = !klbr_money_cand(c, &amt, mp), r;      /* DropCands: a drop being grabbed stays "not taken" while it is still valid */
            if (!taken) { inside = (float)sqrt((pos[0] - mp[0]) * (pos[0] - mp[0]) + (pos[2] - mp[2]) * (pos[2] - mp[2])) <= klbf_brain_near() && fabs(pos[1] - mp[1]) <= 400.0f; klh_rd(c + 0x64, &st64, 1); ctrlst = st64; }
            else { inside = 0; ctrlst = 0; }
            r = kbr_grab_step(&klbr_gr[k].timer, dt, inside, &klbr_gr[k].outside, alive, taken, ctrlst);
            if (r == KBR_G_ABORT) { klbr_grab_end(e, taken ? "taken or hidden" : !alive ? "the bot died" : ctrlst != 1 ? "stack changed state" : "left the ball", 0); continue; }
            if (r == KBR_G_PAY) {
                int part = (int)kbr_part((long)klbr_gr[k].last, (long)amt), left = 0, give;
                klbr_gr[k].timer += 0.7f;      /* re-armed below from the stack's own seconds when readable */
                { float sec = 0; if (klh_rd(c + 0x44, &sec, 4) && sec >= 0.05f && sec <= 10.0f) klbr_gr[k].timer = sec; }
                left = klbf_brain_take(c, part);      /* the game's own 0x4e3f40 through the puppeteer's guarded call; -1 = refused (OnlineTacticsTake is not 2) */
                if (left < 0) { klbr_grab_end(e, "OnlineTacticsTake is not 2: the bridge cannot deplete the stack", 0); continue; }
                give = amt - left; if (give > 0) { klbf_brain_credit(e->actor, give, left <= 0); klbr_paid += give; klbr_npay++; }
                if (left <= 0) { klbr_grab_end(e, "emptied", 1); }
            }
        }
    }
}


static void klbr_summary(void)
{
    if (klbr_sm_round) {
        klog("brain: round end: built %d soldier(s) (%d refused, %d vector failure(s)); frames %d (%d fault(s), %d restore mismatch(es), max %u us); evaluate calls loot %ld board %ld traitor %ld, nonzero %ld/%ld/%ld, faults %ld/%ld/%ld; run faults %ld/%ld/%ld",
            klbr_nbuilt, klbr_nrefused, klbr_nvec_fail, klbr_frames, klbr_sw_flt, klbr_sw_bad, klbr_us_max, (long)klbr_hits[2], (long)klbr_hits[5], (long)klbr_hits[8], (long)klbr_ev_nz[0], (long)klbr_ev_nz[1], (long)klbr_ev_nz[2],
            (long)klbr_ev_flt[0], (long)klbr_ev_flt[1], (long)klbr_ev_flt[2], (long)klbr_run_flt[0], (long)klbr_run_flt[1], (long)klbr_run_flt[2]);
        if (klbr_bridge || klbr_board || klbr_traitor)
            klog("brain: round end: bridge: %d grab(s) started, %d part(s) paid ($%ld), %d stopped; slot 202 calls %d, slot 45 calls %d; traitor mirrors %d; Board run/exit calls %ld/%ld",
                klbr_nstart, klbr_npay, klbr_paid, klbr_nabort, klbr_s202_n, klbr_s45_n, klbr_ntraitor, (long)klbr_hits[3], (long)klbr_hits[4]);
        if (klbr_claims) klog("brain: round end: StackClaims: %ld stack(s) kept off a bot's candidate list (a peer grabs it or picked it within %u ms), %ld fallback(s) to grabs-only (every stack picked by a peer)", klbr_claim_skip, KLBR_CLAIM_MS, klbr_claim_fb);
        if (klbr_dropc) klog("brain: round end: DropCands: %ld drop(s) offered in slot 202 candidate lists (counted per call), %ld drop grab(s) started by the pump", klbr_dc_offered, klbr_dc_grabs);
        if (klbr_bstage) klog("brain: round end: BoardStage: %ld boarded by the real Board tactic (slot 45), %ld by the fallback (the hook's own path after at most %lu ms of waiting); %ld bot(s) had their hook boarding deferred", klbr_bs_real, klbr_bs_fb, KLBR_BS_MS, klbr_bs_defer_n);
        if (klbr_blog) klog("brain: round end: BoardLog: slot 45 calls for a bot not aboard yet %ld, repeats for an aboard bot %ld (total %ld)", klbr_bl_new, klbr_bl_rep, (long)klbr_s45_n);
        if (klbr_realrun)
            klog("brain: round end: realrun: swap-ins %ld (RUN %ld, EXIT %ld), swap-outs %ld, leaks %ld, veh restores %ld, mismatches %ld, foreign-thread %ld, nested %ld, mode!=4 %ld, unregistered [tac+0x10] %ld, hand-off stamps evaluate-pick %ld / resume %ld; %ld tactic(s) in the registry (kept across rounds: a coroutine alive past the round end still gets the shadow)", (long)klbr_rr_in, (long)klbr_rr_val[1], (long)klbr_rr_val[2], (long)klbr_rr_out, (long)klbr_rr_leak, (long)klbr_rr_veh, (long)klbr_rr_mis, (long)klbr_rr_foreign, (long)klbr_rr_nested, (long)klbr_rr_mode, (long)klbr_rr_t10, (long)klbr_rr_hand_ev, (long)klbr_rr_hand_run, (long)klbr_rrn);
        if (klbr_puppet || klbr_boardreal)
            klog("brain: round end: watchdog took %d stalled bot(s) back from the real tactics; %d slow frame(s) (3 in a row switch the tactics off)", klbr_nrevoke, klbr_slow);
    }
    klbr_sm_round = 0;
}

static int klbr_nused(void) { int i, n = 0; for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && klbr_t[i].rec > 0) n++; return n; }
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
    if (klbr_shadow) klog("brain: shadow: depth %d, frames %d (max %u us, %d slow), restore mismatches %d, faults %d; van state %d; crew records in use %d; bridge: slot 202 calls %d, grabs started %d paid %d; board: slot 45 calls %d; traitor marks %d",
        klbr_depth, klbr_frames, klbr_us_max, klbr_slow, klbr_sw_bad, klbr_sw_flt, klbr_van, klbr_nused(), klbr_s202_n, klbr_nstart, klbr_npay, klbr_s45_n, klbr_ntraitor);
    if (klbr_build) {
        klog("brain: wrap: evaluate calls loot %ld (nonzero %ld, max %.3f, last %.3f) board %ld (nz %ld) traitor %ld (nz %ld); run calls loot %ld board %ld traitor %ld; slot3 calls %ld %ld %ld; evaluate faults %ld %ld %ld; RUN answered inert loot %ld board %ld; ArcadePick orders %ld; RealRun %d: swap-ins %ld (RUN resumes %ld, EXIT resumes %ld) swap-outs %ld leaks %ld veh %ld mismatches %ld foreign %ld nested %ld tactics %ld",
             (long)klbr_hits[2], (long)klbr_ev_nz[0], (double)klbr_ev_max[0], (double)klbr_ev_last[0], (long)klbr_hits[5], (long)klbr_ev_nz[1], (long)klbr_hits[8], (long)klbr_ev_nz[2],
             (long)klbr_hits[0], (long)klbr_hits[3], (long)klbr_hits[6], (long)klbr_hits[1], (long)klbr_hits[4], (long)klbr_hits[7], (long)klbr_ev_flt[0], (long)klbr_ev_flt[1], (long)klbr_ev_flt[2], (long)klbr_run_skip[0], (long)klbr_run_skip[1], (long)klbr_npick,
             klbr_realrun, (long)klbr_rr_in, (long)klbr_rr_val[1], (long)klbr_rr_val[2], (long)klbr_rr_out, (long)klbr_rr_leak, (long)klbr_rr_veh, (long)klbr_rr_mis, (long)klbr_rr_foreign, (long)klbr_rr_nested, (long)klbr_rrn);
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
    if (klbr_rr_sw && game_thread) {      /* RealRun safety net, BEFORE any gate: the tick never runs inside a slice, so a swap still in is a leak (a slice that did not end in longjmp(0x168e4c8)) */
        klbr_rr_fix(); klbr_rr_leak++;
        if (klbr_rr_leak_told++ < 4) klog("brain: realrun: LEAK %ld: the shadow rules were still swapped in at the hook tick; real rules put back (swap-ins %ld, out %ld, mismatches %ld)", (long)klbr_rr_leak, (long)klbr_rr_in, (long)klbr_rr_out, (long)klbr_rr_mis);
    }
    while (klbr_rr_told < 8 && klbr_rr_told < klbr_rr_in && game_thread) {      /* the first swap-ins, queued by the thunk (which never logs) */
        int k = (int)klbr_rr_told++;
        klog("brain: realrun: swap-in #%d: goal(tactic) %08lx class %s ctx %08lx val %lu soldier %08lx thread %lu rec %d", k + 1, (unsigned long)klbr_rr_first[k].goal, klbr_cls_nm[klbr_rr_first[k].cls], (unsigned long)klbr_rr_first[k].ctx, (unsigned long)klbr_rr_first[k].val, (unsigned long)klbr_rr_first[k].snd, (unsigned long)klbr_rr_first[k].tid, klbr_find(klbr_rr_first[k].snd) ? klbr_find(klbr_rr_first[k].snd)->rec : -1);
    }
    if (!klbr_on || !game_thread || !klh_exe_ok || now - last < 1000) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if (role != 2 || mode != 4 || state != KLB_ROUND) {      /* HOST Fragile Alliance round only; a client / other mode / lobby does nothing */
        if (klbr_sm_round && (state < KLB_ROUND || state >= 0x1f || role != 2)) { klbr_summary(); memset(klbr_t, 0, sizeof klbr_t); klbr_shadow_reset(); klbr_verdict_n = 0; }
        return;
    }
    klbr_game_tid = GetCurrentThreadId();
    if (klbr_sm_round != sm) { if (klbr_sm_round) klbr_summary(); memset(klbr_t, 0, sizeof klbr_t); klbr_sm_round = sm; klbr_nbuilt = klbr_nrefused = klbr_nvec_fail = klbr_swaps = klbr_frames = klbr_sw_flt = klbr_sw_bad = klbr_slow = klbr_slow_run = klbr_nrevoke = klbr_crash_told = 0; klbr_us_max = 0; klbr_ngrab = klbr_npay = klbr_nabort = klbr_nstart = klbr_s202_n = klbr_s202_told = klbr_s45_n = klbr_ntraitor = 0; klbr_paid = 0; klbr_claim_skip = klbr_claim_fb = 0; klbr_dc_offered = klbr_dc_grabs = 0; klbr_bs_defer_n = klbr_bs_real = klbr_bs_fb = 0; klbr_bl_new = klbr_bl_rep = klbr_bl_gate = klbr_bl_sec = 0; klbr_bn_told = klbr_bn_ok = 0; memset(klbr_bl_at, 0, sizeof klbr_bl_at); klbr_sync_at = 0; klbr_depth = 0; klbr_shadow_reset(); klbr_verdict_n = 0;
        klog("brain: round starts on the host (Probe %d, Build %d, Loot %d, Bridge %d, Board %d/%d, Traitor %d, PuppetOff %d, Cops %d)", klbr_probe, klbr_build, klbr_loot, klbr_bridge, klbr_board, klbr_boardreal, klbr_traitor, klbr_puppet, klbr_cops); }
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
    if (klbr_shadow) klbr_sync(now);
    if (klbr_probe || klbr_build) { if (!told || klbr_probe || klbr_build) klbr_probe_log(now, sm, role, mode, state, actor, snd, n); told = 1; }
}

static int klbr_key(const char *k) { return GetPrivateProfileIntA("Brain", k, 0, klh_ini) != 0; }
static void klbr_init(void)
{
    int sw[KBR_NSW];
    kbr_switches2(klbr_key("Probe"), klbr_key("Build"), klbr_key("Loot"), klbr_key("OnlineBrainBridge"), klbr_key("OnlineBrainBoard"), klbr_key("OnlineBrainTraitor"), klbr_key("PuppetOff"), klbr_key("OnlineBrainBoardReal"), klbr_key("OnlineBrainCops"), sw);
    klbr_probe = sw[KBR_S_PROBE]; klbr_build = sw[KBR_S_BUILD]; klbr_loot = sw[KBR_S_LOOT]; klbr_bridge = sw[KBR_S_BRIDGE]; klbr_board = sw[KBR_S_BOARD]; klbr_traitor = sw[KBR_S_TRAITOR]; klbr_puppet = sw[KBR_S_PUPPET]; klbr_boardreal = sw[KBR_S_BOARDREAL]; klbr_cops = sw[KBR_S_COPS];
    klbr_win_ms = (int)GetPrivateProfileIntA("Brain", "PuppetWindowMs", 5000, klh_ini); if (klbr_win_ms < 500) klbr_win_ms = 500; if (klbr_win_ms > 60000) klbr_win_ms = 60000;
    klbr_lootwin = (int)GetPrivateProfileIntA("Brain", "LootWinMs", 1500, klh_ini); if (klbr_lootwin < 500) klbr_lootwin = 500; if (klbr_lootwin > 60000) klbr_lootwin = 60000;
    klbr_boardwin = (int)GetPrivateProfileIntA("Brain", "BoardWinMs", 2000, klh_ini); if (klbr_boardwin < 500) klbr_boardwin = 500; if (klbr_boardwin > 60000) klbr_boardwin = 60000;
    klbr_level = kbr_level_clamp((int)GetPrivateProfileIntA("Brain", "OnlineBrainLevel", 6, klh_ini));
    klbr_on = klbr_probe || klbr_build;
    if (klbr_key("Loot") && !klbr_build) klog("brain: Loot needs Build=1: off");
    if (klbr_key("OnlineBrainBridge") && !klbr_loot) klog("brain: OnlineBrainBridge needs Build=1 and Loot=1: off");
    if (klbr_key("OnlineBrainBoard") && !klbr_build) klog("brain: OnlineBrainBoard needs Build=1: off");
    if (klbr_key("OnlineBrainBoardReal") && !klbr_board) klog("brain: OnlineBrainBoardReal needs OnlineBrainBoard=1: off");
    if (klbr_key("OnlineBrainTraitor") && !klbr_traitor) klog("brain: OnlineBrainTraitor needs Build=1 and OnlineBrainBridge=1: off");
    if (klbr_key("PuppetOff") && !klbr_puppet) klog("brain: PuppetOff needs Build=1, Loot=1 and OnlineBrainBridge=1: off");
    if (klbr_key("OnlineBrainCops") && !klbr_cops) klog("brain: OnlineBrainCops needs OnlineBrainBridge=1: off");
    klbr_apick = klbr_bridge && klbr_key("ArcadePick");
    klbr_claims = klbr_bridge && klbr_key("StackClaims");
    if (klbr_key("StackClaims") && !klbr_claims) klog("brain: StackClaims needs Build=1, Loot=1 and OnlineBrainBridge=1: off");
    if (klbr_claims) klog("brain: StackClaims=1 UNTESTED: the loot candidates (slot 202) skip a stack another bot grabs or picked within %u ms, so each bot walks to its own stack (bs4: 12 watchdog take-backs from shared stacks)", KLBR_CLAIM_MS);
    klbr_dropc = klbr_bridge && klbr_key("DropCands");
    if (klbr_key("DropCands") && !klbr_dropc) klog("brain: DropCands needs Build=1, Loot=1 and OnlineBrainBridge=1: off");
    if (klbr_dropc) klog("brain: DropCands=1 UNTESTED: slot 202 also offers valid type-1 drops (armed, amount left, unhidden, preceded by a real stack drain, a node with a place), merged with the stacks by distance as Arcade; the pump grabs a chosen drop (bs4c DD05: cops drain every stack into a drop in ~20 s, 0 candidates after)");
    if (klbr_key("ArcadePick") && !klbr_apick) klog("brain: ArcadePick needs Build=1, Loot=1 and OnlineBrainBridge=1: off");
    if (klbr_apick) klog("brain: ArcadePick=1 UNTESTED: the puppeteer walks a bot to the stack its real Loot evaluate chose (within %u ms), else to its own nearest stack", KLBR_PICK_MS);
    if (klbr_on) klog("brain: Probe %d, Build %d (recommended off until benched), Loot %d, Bridge %d, Board %d, BoardReal %d, Traitor %d, PuppetOff %d, Cops %d, Level %d; HOST round only, no code byte is patched", klbr_probe, klbr_build, klbr_loot, klbr_bridge, klbr_board, klbr_boardreal, klbr_traitor, klbr_puppet, klbr_cops, klbr_level);
    if (klbr_loot || klbr_board) {
        klog("brain: Loot / Board = 1 is UNTESTED: a DLL-owned shadow rules block (crew table, score block, van state mirrored from the host ledger) is swapped into [G+0x54] around ONE tactic call (host game thread, fault-guarded, restored in a __finally and verified)");
        if (!klbr_make_shadow()) { klog("brain: shadow rules block could not be made: Loot / Board / Traitor / Bridge off"); klbr_loot = klbr_board = klbr_traitor = klbr_bridge = klbr_boardreal = klbr_puppet = 0; }
    }
    if (klbr_key("RealRun") && !(klbr_bridge && klbr_shadow && klh_exe_ok)) klog("brain: RealRun needs Build=1, Loot=1, OnlineBrainBridge=1, the shadow block and the known kl2.exe: off");
    else if (klbr_key("RealRun")) {      /* the longjmp thunk: ONE IAT slot, MSVCR90.longjmp, 0xb10370 in the known exe */
        DWORD slot = (DWORD)(DWORD_PTR)KLH_VA(0x00b10370); int n = klh_iat("MSVCR90.dll", "longjmp", (void *)klbr_w_longjmp, (void **)&klbr_real_longjmp);
        if (n < 1 || !klbr_real_longjmp || klh_rd32(slot) != (DWORD)(DWORD_PTR)klbr_w_longjmp) klog("brain: RealRun: the MSVCR90 longjmp import slot could not be wrapped (entries changed %d, real %p, slot 0x%08lx reads %08lx): RealRun off", n, (void *)klbr_real_longjmp, (unsigned long)slot, (unsigned long)klh_rd32(slot));
        else {
            klbr_realrun = 1;
            klog("brain: RealRun=1 UNTESTED: msvcr90 longjmp import slot %08lx (= 0xb10370 + delta, %d slot(s) changed) now points at the DLL thunk %p (real longjmp %p). Loot RUN / Board RUN / Board EXIT go straight to the originals; the shadow rules are swapped in per resumed slice", (unsigned long)slot, n, (void *)klbr_w_longjmp, (void *)klbr_real_longjmp);
        }
    }
    if (!klbr_realrun && (klbr_puppet || klbr_boardreal)) { klog("brain: PuppetOff / OnlineBrainBoardReal hand a bot to the real Loot / Board RUN, a setjmp coroutine that crashed the host in bench bs1 (c0000029, 11-03): forced OFF without RealRun=1. Use ArcadePick=1"); klbr_puppet = klbr_boardreal = 0; }
    klbr_bstage = klbr_realrun && klbr_boardreal && klbr_board && klbr_key("BoardStage");
    klbr_bhold = klbr_bstage && klbr_key("BoardHold") ? (int)GetPrivateProfileIntA("Brain", "BoardHoldMs", 4500, klh_ini) : 0; if (klbr_bhold && klbr_bhold < 500) klbr_bhold = 500; if (klbr_bhold > 60000) klbr_bhold = 60000;
    klbr_bnode = klbr_bstage && klbr_key("BoardNode"); klbr_bs0 = klbr_bstage && klbr_key("BoardStage0"); klbr_blog = klbr_bstage && klbr_key("BoardLog");
    if (klbr_bhold) klog("brain: BoardHold=1 UNTESTED: a bot stays held by the real Board tactic for %d ms after its last Board evaluate / RUN-resume stamp (BoardWinMs %d otherwise)", klbr_bhold, klbr_boardwin);
    if (klbr_bnode) klog("brain: BoardNode=1 UNTESTED: on maps without an escape box the OnlineExitCrowd test of a bot the real Board tactic holds is against the boarding node, not the exit trigger");
    if (klbr_bs0) klog("brain: BoardStage0=1 UNTESTED: on maps without an escape box a bot in the exit crowd shows stage 3 even with tally 0");
    if (klbr_blog) klog("brain: BoardLog=1: per bot per second in van state 3 / 4 (max 240 lines per round), per gate call (max 80), slot-45 real / repeat counts at the round end");
    if ((klbr_key("BoardHold") || klbr_key("BoardNode") || klbr_key("BoardStage0") || klbr_key("BoardLog")) && !klbr_bstage) klog("brain: BoardHold / BoardNode / BoardStage0 / BoardLog need BoardStage=1: off");
    if (klbr_key("BoardStage") && !klbr_bstage) klog("brain: BoardStage needs RealRun=1 and OnlineBrainBoardReal=1 (with OnlineBrainBoard=1): off");
    if (klbr_bstage) klog("brain: BoardStage=1 UNTESTED: the crew-record stage byte shows 3 while the van waits and the bot carries loot / is ordered to the exit box, so the real Board tactic (slot 45) can board it; the hook's own boarding waits up to %lu ms per bot for it, then boards as before", KLBR_BS_MS);
    if (klbr_bridge) klog("brain: OnlineBrainBridge=1 UNTESTED: loot candidates come from the real money controls (slot 202); the grab is run by this DLL (pump), %d ms window", klbr_lootwin);
    if (klbr_board) klog("brain: OnlineBrainBoard=1 UNTESTED: the real Board tactic is evaluated in the frame%s; its answer reaches the AI only with BoardReal", klbr_boardreal ? "; BoardReal=1: boarding through slot 45 and the host ledger" : " (dry: log only)");
    if (klbr_traitor) klog("brain: OnlineBrainTraitor=1 UNTESTED: MIRROR ONLY, the real Traitor roll runs and its record bit is logged; nothing changes for the bot");
    if (klbr_cops) klog("brain: OnlineBrainCops=1: research only (design 8.2): no behaviour is implemented, this line is the whole effect");
    if (klbr_puppet) klog("brain: PuppetOff=1 UNTESTED: OnlineTactics steering is skipped for a bot only within %d ms of its real Loot evaluate returning > 0 (Board: %d ms)", klbr_bridge ? klbr_lootwin : klbr_win_ms, klbr_boardwin);
}

#endif /* KLBRAIN_C */
