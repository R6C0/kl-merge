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
struct klbr_s { DWORD snd, actor, tac[3], seenAt, builtAt, nzAt, bnzAt, wSince, wUntil, s45At, pick, pickAt; float wpos[3]; int state, rec, traitor, flt, wHas, pendBoard, pendTurn, pendArc; };      /* rec: shadow crew record 1..11 (0 none); bnzAt: tick of the last Board evaluate > 0;
                                                                                                    wSince / wUntil / wpos: the hand-off stall watchdog (kbr_watch); flt: framed faults of this bot (2 = never handed again); pendBoard: slot 45 asked, the pump boards it */      /* state 0 free, 1 built by us, 2 refused (told once), 3 pending build */
static struct klbr_s klbr_t[KLBR_MAX];
static int klbr_nbuilt, klbr_nrefused, klbr_nvec_fail;
static DWORD klbr_sm_round;             /* the session object of the round the table belongs to */

/* ---- OnlineBrainTraitorTurn (2026-11-03; design scratchpad traitor_design.md + traitor_refute.md). The saved team state lives OUTSIDE klbr_t (index = the slot of klbr_t) so the round-change memset of klbr_t cannot lose it:
   every memset of klbr_t is preceded by klbr_tr_restore_all(). The mirror only sets e->pendTurn; the pump (game thread, depth 0) writes the team. ---------------------------------------------------------- */
static int klbr_trturn, klbr_trrow0, klbr_trkillmax = 2, klbr_trcap; static float klbr_trnear = 3000.0f;      /* TraitorTurn on; Row0 mode 0 host / 1 richest; TraitorKillMax (online key, 0 = no cap); [shadow+0x338] cap (0 = off); TraitorKillNear */
static struct { DWORD actor, info, team0; int on, kills, was_alive; float pos[3]; } klbr_tt[KLBR_MAX];      /* on: team Enemy written and not yet restored; kills: crew deaths booked to him; was_alive/pos: the death booking */
static int klbr_tt_turned, klbr_tt_back, klbr_tt_kills, klbr_tt_capped, klbr_tt_refused;      /* round-end counters: turned, restored, kills booked, capped by TraitorKillMax, refused swaps */
static int klbr_taon, klbr_ta_dis, klbr_ta_n, klbr_ta_flt, klbr_ta_sc_n, klbr_ta_made, klbr_ta_wlog;      /* OnlineBrainTraitorArcade (block below, before the Turn pump): on; off for the round after 3 faults; marks this round; faults; logged scores; table attempted; logged wraps */
static int klbr_hlon, klbr_dmon;      /* OnlineBrainTraitorHitLog / OnlineBrainTraitorDamage (the latter needs OnlineBrainTraitorArcade) */
static int klbr_tflmode;                /* OnlineBrainTraitorFireLine (needs OnlineBrainTraitorArcade): 0 off, 1 log only, 2 swap the shadow rules in around ZSoldier slots 113 / 114 */
static int klbr_dg0, klbr_dg1;         /* diagnostics under OnlineBrainTraitor: first 6 Traitor evaluates that returned 0 / nonzero per round */
static int klbr_row0_which = -2; static long klbr_row0_val;      /* row 0 source of the last sync (seat, money), logged on a change */
static int klbr_turned_actor(DWORD actor)      /* klbotfill.c: a bot whose team is Enemy now is not steered / escorted / boarded / banked */
{
    int i;
    if (!klbr_trturn || !actor) return 0;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_tt[i].on && klbr_tt[i].actor == actor) return 1;
    return 0;
}

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
    if (cls == 2 && klbr_trturn && e && e->traitor) return 0;      /* TraitorTurn: a marked bot is never evaluated again (no LCG roll wasted, one turn per bot per round); the caller answers 0.0 */
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
/* DIAGNOSTIC under OnlineBrainTraitor (11-03): the first 6 Traitor evaluates of a round that answered 0 and the first 6 that answered > 0, with every term the game sums. Read only, from our own shadow block and the
   tuning row (data reads, no game call). GUESS: the stage terms are floats at R+0x24+4*stage and the limit a float at R+0x20 (disassembly reading, bots_behaviour 1.3); our sum mirrors kbr_tr_sum, the game's own is the answer */
static void klbr_tr_diag(const struct klbr_s *e, float r)
{
    int *cnt = r > 0.0f ? &klbr_dg1 : &klbr_dg0; DWORD tun, R; float f[9]; int stage, L = kbr_level_clamp(klbr_level); long bot, pl;
    if (!e || e->rec <= 0 || !klbr_shadow || *cnt >= 6) return;
    if (!(tun = klh_rd32((DWORD_PTR)KLH_VA(0x0168d7c0))) || !klh_rd(R = tun + 0x6ac + 0x70 * (DWORD)L, f, sizeof f)) return;      /* f[8] = R+0x20 limit, then R+0x24.. needs more: read below */
    stage = KLBR_PB(KLBR_REC(e->rec) + 0x78); bot = (long)KLBR_P32(klbr_score + 0x150 + 4 * (DWORD)e->rec); pl = (long)KLBR_P32(klbr_score + 0x150);
    { float st[4] = { 0, 0, 0, 0 }; klh_rd(R + 0x24, st, sizeof st);
      if (!kbr_diag_take(cnt, 6)) return;
      klog("brain: traitor diag: evaluate %s %.3f: record %d actor %08lx stage byte %d, bot row $%ld, row 0 $%ld (seat %d), sum %.1f (stage term %.1f + bot %d + player %d) vs limit %.1f, level %d",
           r > 0.0f ? "NONZERO" : "zero", (double)r, e->rec, (unsigned long)e->actor, stage, bot, pl, klbr_row0_which, (double)kbr_tr_sum(st[stage & 3], bot, pl), (double)st[stage & 3], kbr_tr_bot_term(bot), kbr_tr_pl_term(pl), (double)f[8], L); }
}
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
    if (cls == 2 && e && !flt) klbr_tr_diag(e, r);
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
    if (klh_svt(snd) != KLE_SOLDIER_VT) { e->state = 2; return; }
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
            if (!(s = klh_rd32(o + 0x77c)) || klh_svt(s) != KLE_SOLDIER_VT) continue;
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

/* row 0 of the shadow money row = "the player" of Arcade's Traitor evaluate (0x6c7700 returns 0 while 0x7f6850 is true, refute 11-03). Online there is no single player: mode 0 = the host's money, 1 = the richest human
   (ini OnlineBrainTraitorRow0), read from the REAL rules' seat rows (free bytes [rules+0xc], DDL score [rules+0x2c], money = [score+0x224+4i] + [score+0x188+4i]; the same reading klbot.c's HUD crew uses, getters 55/56 =
   0x40b7e0 / 0x819aa0 checked). GUESS: seat 0 is the host on the Sv rules; that sum is the "carried money" an Arcade row 0 would hold. Data reads only; depth 0 only (the real rules are in [G+0x54]). */
static void klbr_row0_update(void)
{
    DWORD G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)), rules, vt, n = 0, fr, sc; long mo[16]; unsigned char us[16]; int i, which = -1; long v;
    memset(us, 0, sizeof us); memset(mo, 0, sizeof mo);
    if (G > 0xffff && (rules = klh_rd32(G + 0x54)) > 0xffff && rules != klbr_shadow && (vt = klh_rd32(rules)) != 0 && (KLH_RULES_SV_OK(vt) || KLH_RULES_CL_OK(vt)) &&
        klh_rd(rules + 0x14, &n, 4) && n >= 1 && n <= 16 && (fr = klh_rd32(rules + 0xc)) != 0 && (sc = klh_rd32(rules + 0x2c)) != 0 &&
        klh_rd32(vt + 4 * 55) == 0x40b7e0u + (DWORD)klh_delta && klh_rd32(vt + 4 * 56) == 0x819aa0u + (DWORD)klh_delta) {
        for (i = 0; i < (int)n; i++) { BYTE f = 1; DWORD m1 = 0, m2 = 0; if (!klh_rd(fr + (DWORD)i, &f, 1) || f) continue; klh_rd(sc + 0x224 + 4 * (DWORD)i, &m1, 4); klh_rd(sc + 0x188 + 4 * (DWORD)i, &m2, 4); us[i] = 1; mo[i] = (long)m1 + (long)m2; }
    }
    v = kbr_row0_money(klbr_trrow0, mo, us, 16, &which);
    KLBR_P32(klbr_score + 0x150) = (DWORD)v;
    if (which != klbr_row0_which) { klog("brain: traitor: row 0 (the 'player' of the Traitor evaluate) = %s seat %d, $%ld", klbr_trrow0 ? "richest human" : "host", which, v); klbr_row0_which = which; }
    klbr_row0_val = v;
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
    if (klbr_trturn && klbr_depth == 0) klbr_row0_update();
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
        if (klbr_taon) { klbr_ta_n++; e->pendArc = 1; }      /* OnlineBrainTraitorArcade: FLAG ONLY too, klbr_ta_pump wraps him on the game thread */
        if (klbr_trturn) e->pendTurn = 1;      /* FLAG ONLY: no game write inside the AI walk; klbr_tr_pump turns him on the game thread outside any frame */
        klog("brain: traitor: Traitor RUN marked record %d (actor %08lx, level %d, money row %ld) as a traitor. %s", e->rec, (unsigned long)e->actor, kbr_level_clamp(klbr_level), (long)KLBR_P32(klbr_score + 0x150 + 4 * (DWORD)e->rec),
             klbr_trturn ? "OnlineBrainTraitorTurn: the pump swaps his team to Enemy (pending)" : klbr_taon ? "OnlineBrainTraitorArcade: the pump wraps his target score (team stays Ally)" : "MIRROR ONLY (OnlineBrainTraitor, UNTESTED): the bot's team, hostility and the announce are NOT changed");
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
/* ---- OnlineBrainTraitorArcade (2026-11-03; re/arcade_traitor_consequence_1103.md) ------------------------------------------------------------------------------------------------------------
   Stock Arcade: the Traitor mark (rec+0x79 bit 2) changes no team; it only lets the marked ally score a HUMAN ZFFPlayer in ZSoldier slot 111 (0x882470, the target score). Online 0x7f6850 is false, so that
   function returns the 'no target' float for a human. The two call sites (0x8826ec, 0x5709c2) are in hashed code, so no byte is patched: the marked bot gets ONE shared private copy of the ZSoldier vtable
   (klh_soldier_priv; every 'vtable == ZSoldier' test reads through klh_svt) whose slot 111 (+0x1bc, 7 stack args, ret 0x1c, verified from 0x8824e4 / 0x882732 and the table dword) is klbr_w_score.
   For a ZFFPlayer candidate it runs the original with the shadow rules swapped in (klbr_swap_in: [G+0x54] = shadow, role 0 -> 0x7f6850 true, as in Arcade) so the original reads the mark from the shadow
   record. Everything else (other candidates, other bots, the cops) calls the original untouched. NOT reproduced: the fire-line friend list (0x570a12 inside 0x5706a0, hashed): a marked bot's line still
   lists humans as friends (documented gap). GUESS: swapping the rules around the whole call also changes whatever else the original reads from the rules (0x6a1c40 floats, level byte); the shadow block
   carries the same fields the Traitor evaluate reads, nothing more is known. The stock table is never written; a bot is put back on it on death, round end or a tag change. */
#define KLBR_TA_SLOT 111                /* ZSoldier slot 111 = vt + 0x1bc = 0x882470 (verified: the table dword at 0xbd0954 + 0x1bc) */
#define KLBR_TA_NSLOT 128               /* GUESS: the table has at least 118 code pointers (counted from the exe); 128 dwords are copied, only slot 111 is changed */
#define KLBR_TA_SOLDIER_VT 0x00bd0954
#define KLBR_TA_ORG 0x00882470
#define KLBR_TA_NOTARGET 0x00b5f1e0    /* the float 0x882726 loads for 'no target' */
static DWORD klbr_ta_org;
static struct { DWORD snd; int rec; int nlog[2]; } klbr_ta[KLBR_MAX];      /* OUTSIDE klbr_t (like klbr_tt): index = the slot of klbr_t; snd = the soldier we gave the private table; nlog = FireLine log lines of slot 113 / 114 this wrap */
static struct klbr_s *klbr_hl_body(DWORD body);      /* HitLog block below */
static struct klbr_s *klbr_hl_find(DWORD o);
static int klbr_hf_human_in_b(DWORD self);      /* HumanFirst block below */
/* OnlineBrainTraitorHumanOnly (2026-11-03, workflow wvf2fzwhg 'ally' trace, verified; UNTESTED, recommended off): slot 111 0x882470 has no human-vs-bot term, so near, seen, in-range ALLY bots
   (flags bit0 +100, 0x10, no visibility penalty) beat the far humans (bs21: holder = ally bot 76/86 on DM03). With this on, for a MARKED bot only and only while its list B holds a seen + in-range
   HUMAN (klbr_hf_human_in_b), a candidate that is a tagged bot's ZFFPlayer body (klbr_hl_body) gets the 'no target' float without calling the original; 0x767510 keeps the strict maximum from -1e38,
   so it can never win. GUESS: klbr_hl_body recognises every tagged bot body (crew seat == shadow rec); an unrecognised bot body is scored normally (shows as the 'passed' count). */
static int klbr_hoon; static long klbr_ho_null, klbr_ho_pass;
/* ---- OnlineBrainTraitorCandLog (2026-11-03; READ ONLY): who does a MARKED bot's slot 111 (0x882470, reached through slot 113) ever get as a candidate? Counted per class (ZFFPlayer / ZFFActor / ZSoldier / other, by vtable,
   klh_pvt / klh_avt / klh_svt), the first 6 distinct candidates per bot per round are logged with class and distance, one 'brain: traitor cands:' summary per round at the round end. Only klh_rd reads.
   Plus (once per 5 s) the size of the bot's known-entities list B = [soldier+0x698] (count dword at +0, 0x14-byte entries from +4, entity at entry+4, type at entry+8; read from 0x7bd770, research A/B)
   and how many type-2 entries are ZFFPlayer bodies. Needs OnlineBrainTraitorArcade (the census sits in the private slot 111). ---- */
static int klbr_clon;      /* OnlineBrainTraitorCandLog */
static struct { long cnt[KBR_CC_N]; DWORD seen[KBR_CC_SEEN]; int nseen; DWORD lat; long lmax, lmaxp; } klbr_cl[KLBR_MAX];      /* per bot (index of klbr_t): calls by class, distinct candidates logged, last list dump tick, largest list / most ZFFPlayer entries seen */
static long klbr_cl_calls;
static void klbr_cand_note(DWORD self, DWORD cand)      /* game thread only; called from klbr_w_score */
{
    struct klbr_s *e = klbr_find(self); int i, c, alive = 0; float bp[3], tp[3]; double dist = -1.0;
    if (!klbr_clon || !e || e->state != 1 || !e->traitor || cand < 0x10000) return;
    i = (int)(e - klbr_t);
    c = kbr_cand_class(klh_pvt(cand) == 0x00bb45f4u, klh_avt(cand) == 0x00bb3bacu, klh_svt(cand) == 0x00bd0954u);
    klbr_cl[i].cnt[c]++; klbr_cl_calls++;
    if (kbr_cand_note((kbr_u32 *)klbr_cl[i].seen, &klbr_cl[i].nseen, cand)) {
        if (klbr_bot_pos(e->actor, bp, &alive) && klh_rd(cand + 0x460, tp, 12) && kle_ok3(tp)) dist = kle_dist(bp, tp) / 100;
        klog("brain: traitor cand: bot %d (soldier %08lx, rec %d) candidate #%d %08lx class %s dist %.1f m (-1 = unknown)", i, (unsigned long)self, e->rec, klbr_cl[i].nseen, (unsigned long)cand, kbr_cand_name(c), dist);
    }
}
static void klbr_cl_list(DWORD now)      /* the known list of every wrapped marked bot, once per 5 s (game thread, depth 0) */
{
    int i;
    if (!klbr_clon) return;
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i]; DWORD B, cnt = 0; long ty[10]; int n, k, p2, pl = 0, a1 = 0;
        if (e->state != 1 || !e->traitor || !e->snd || !klbr_ta[i].snd) continue;
        if (!kbr_rate_ok(klbr_cl[i].lat, now, 5000ul)) continue;
        klbr_cl[i].lat = now | 1u;
        B = klh_rd32(e->snd + 0x698);
        if (B < 0x10000 || !klh_rd(B, &cnt, 4)) { klog("brain: traitor cand list: bot %d: known list [soldier+0x698] unreadable (%08lx)", i, (unsigned long)B); continue; }
        n = kbr_list_count((long)cnt);
        for (k = 0; k < n; k++) {
            DWORD en = B + 4 + 0x14 * (DWORD)k, t = 99, ent;
            ty[k] = klh_rd(en + 8, &t, 4) ? (long)t : 99;
            ent = klh_rd32(en + 4);
            if (ty[k] == 2 && ent > 0xffff && klh_pvt(ent) == 0x00bb45f4u) pl++;
            if (ty[k] == 1) a1++;
        }
        p2 = kbr_list_type2(ty, n);
        if ((long)cnt > klbr_cl[i].lmax && (long)cnt <= 10) klbr_cl[i].lmax = (long)cnt;
        if (pl > klbr_cl[i].lmaxp) klbr_cl[i].lmaxp = pl;
        klog("brain: traitor cand list: bot %d (soldier %08lx): known list %08lx count %lu%s, type-2 %d, type-1 %d, ZFFPlayer bodies among type-2 %d", i, (unsigned long)e->snd, (unsigned long)B, (unsigned long)cnt, n ? "" : " (0 or out of range)", p2, a1, pl);
    }
}
static void klbr_cand_summary(void)      /* round end, next to the 'traitor hits:' lines; clears the round */
{
    if (klbr_clon) {
        int i, any = 0;
        for (i = 0; i < KLBR_MAX; i++) {
            long t = klbr_cl[i].cnt[0] + klbr_cl[i].cnt[1] + klbr_cl[i].cnt[2] + klbr_cl[i].cnt[3];
            if (!t && !klbr_cl[i].lmax) continue;
            any = 1;
            klog("brain: traitor cands: bot %d: slot-111 calls %ld = ZFFPlayer %ld, ZFFActor %ld, ZSoldier %ld, other %ld; known list max count %ld, max ZFFPlayer entries %ld", i, t, klbr_cl[i].cnt[0], klbr_cl[i].cnt[1], klbr_cl[i].cnt[2], klbr_cl[i].cnt[3], klbr_cl[i].lmax, klbr_cl[i].lmaxp);
        }
        klog("brain: traitor cands: round total %ld marked-bot slot-111 call(s)%s", klbr_cl_calls, any ? "" : " (no marked bot called slot 111 or had a known list; 0 ZFFPlayer = the candidate list never held a human)");
    }
    memset(klbr_cl, 0, sizeof klbr_cl); klbr_cl_calls = 0;
}
/* ---- OnlineBrainTraitorSense (2026-11-03; UNTESTED, default 0): lever from research A/B. A human crew member never reaches a marked ally bot's known list B because 0x5a8140 / 0x608050 drop an entity
   whose team bit is not in [[bot team record]+0xc]. We call B::NoteEntity 0x7bd720 ourselves (thiscall: ecx = B = [soldier+0x698], one stack arg = the entity HANDLE, callee pops 4 = a fastcall with edx unused)
   for each live human ZFFPlayer body, every [Brain] OnlineBrainTraitorSenseMs (default 500) per wrapped marked bot. The handle is 0x6ece90(body) (fastcall, ecx = entity; the call klshop.c makes): 0x5a8140 hands its
   argument to 0x8ccde0 = handle -> entity, so NoteEntity takes a handle (read from code). A re-note of a known entity only refreshes its timestamp [entry+0xc] (0x7bd806, read from code): no duplicates.
   Human bodies: the crew records [rules+8] + 0x74*i, in use when byte [rules+0xc]+i == 0, client struct at +0, ZFFPlayer at [client+0x378] (bs15: +0x378 on the record itself is empty; GUESS that this holds for remote bodies on the host), minus tagged bots' bodies and police (+0x2723).
   UNDO: the only thing written is the game's own entries in B; feeding stops on unmark, death, round end, tag change (the klbr_ta_restore paths); the entries expire through the game's prune 0x51e480
   (GUESS: within seconds; cap 10 entries). Effects of NoteEntity beyond the list (byte [soldier+0x184], timestamps) were NOT traced: GUESS harmless. The rest of NoteEntity (past 0x7bd83c) was not read. ---- */
static int klbr_snon, klbr_snms = 500, klbr_sn_flt, klbr_sn_fed, klbr_sn_logged, klbr_sn_unfed, klbr_sn_dlog; static DWORD klbr_sn_dat;      /* + skip-reason log lines this round, last one's tick */      /* on; interval; faults this round (3 = off for the round); NoteEntity calls this round; log lines; entries taken back out */
static DWORD klbr_sn_at[KLBR_MAX];
static DWORD klbr_sn_fb[KLBR_MAX][KBR_SN_MAXFEED];      /* per bot: the human bodies we noted into its list (taken out again when the wrap ends) */
static int klbr_sn_nfb[KLBR_MAX];
static int klbr_hp_read(DWORD pl, float *hp);      /* defined with the HitLog block */
/* Review 11-03 (disassembly, kl2.exe 0490): (1) 0x7bd8db..0x7bd918 walks the ally list (count [B+0xcc], pointers from B+0xd0) after every NEW entry and calls each ally's vtable +0x1a0 = ZSoldier slot 104 0x730330 -> 0x425fa0
   (the same insert into the ALLY's list, no team test) plus an actor alert: a plain NoteEntity would hand the human to the whole squad. So B+0xcc is set to 0 for the duration of the call and put back at once (game thread, nothing runs in between).
   (2) The prune 0x51e480 keeps every type-2 entry whose entity is alive and non-null (bl = 1 at 0x51e4b0 -> 0x51e5b3), so the entries do NOT expire by time: they are removed here (game's own swap-remove 0x67df10, thiscall ret 4)
   when the wrap ends. (3) A full list (10) evicts the oldest entry whose flag bit0 is clear: at most KBR_SN_MAXFEED nearest humans are fed so the bot keeps its police entries. */
static int klbr_sn_seen;      /* OnlineBrainTraitorSenseSeen: 1 = B::MarkSeen 0x4880d0 instead of NoteEntity */
/* OnlineBrainTraitorSenseSeen (research re/traitor_slot111_gates_1103.md, verified; MarkSeen prologue/ret 4 and the game's caller 0x65fab8 (ecx = [..+0x698]) re-read 11-03):
   a NoteEntity entry has flags 0, and ZAttackTarget's fire test 0x616480 (0x4f493a) needs bit0 SET (plus 0x10 set, 0x4/0x200/0x40 clear), so a fed human could be targeted but never shot at.
   B::MarkSeen 0x4880d0 (thiscall, ecx = B, ONE arg = entity POINTER, ret 4) sets bit0 on an existing entry or adds a type-2 entry with bit0 set, sets B+0x184 (full rescan:
   loop 1 then computes 0x10 / 0x20 / 0x40 / friend bit 0x4) and also notifies the ally list B+0xd0 via vcall +0x1a0 (unless [soldier+0x88]==2): B+0xcc is parked as for NoteEntity.
   GUESS: who clears an entry's bit0 was not found, so it is repeated every SenseMs. MarkSeen also writes flag bit7 = byte [human+0x25c5] (slot 111: -100 / +150 terms). */
static int klbr_sn_call(DWORD B, DWORD body)      /* 1 = called, 0 = no handle (not fed), -1 = fault */
{
    DWORD h = 0, ac = klh_rd32(B + 0xcc); int ok = 0, zeroed = 0;
    __try {
        h = klbr_sn_seen ? body : ((DWORD (__fastcall *)(DWORD))(DWORD_PTR)KLH_VA(0x6ece90))(body);
        if (h) {
            if (ac && ac <= 16) { *(volatile DWORD *)(DWORD_PTR)(B + 0xcc) = 0; zeroed = 1; }
            if (klbr_sn_seen) ((void (__fastcall *)(DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(0x4880d0))(B, 0, body);      /* MarkSeen: thiscall + 1 stack arg (pointer) */
            else ((void (__fastcall *)(DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(0x7bd720))(B, 0, h);
            if (zeroed) { *(volatile DWORD *)(DWORD_PTR)(B + 0xcc) = ac; zeroed = 0; }
            ok = 1;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        if (zeroed) { __try { *(volatile DWORD *)(DWORD_PTR)(B + 0xcc) = ac; } __except (EXCEPTION_EXECUTE_HANDLER) { } }
        klbr_sn_flt++; return -1;
    }
    return ok;
}
static void klbr_sn_unfeed(int i, DWORD snd)      /* wrap ends (klbr_ta_restore): take our type-2 entries out of the bot's list again; only while the soldier still carries our private table (a freed soldier is left alone) */
{
    DWORD B; int k = 0, removed = 0, guard = 0;
    if (!klbr_sn_nfb[i]) return;
    if (!klh_soldier_priv || klh_rd32(snd) != klh_soldier_priv || (B = klh_rd32(snd + 0x698)) < 0x10000) { klbr_sn_nfb[i] = 0; return; }
    __try {
        DWORD cnt = 0;
        while (guard++ < 40 && klh_rd(B, &cnt, 4) && cnt <= 10 && (DWORD)k < cnt) {
            DWORD en = B + 4 + 0x14 * (DWORD)k, ty = 0, ent = 0; int j, hit = 0;
            if (!klh_rd(en + 8, &ty, 4) || !klh_rd(en + 4, &ent, 4)) break;
            for (j = 0; ty == 2 && j < klbr_sn_nfb[i]; j++) if (klbr_sn_fb[i][j] == ent) hit = 1;
            if (hit) { ((void (__fastcall *)(DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(0x67df10))(B, 0, en); removed++; }      /* swap-remove: the last entry now sits at k, look at k again */
            else k++;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_sn_flt++; }
    klbr_sn_unfed += removed; klbr_sn_nfb[i] = 0;
    if (removed) klog("brain: traitor sense: bot %d (soldier %08lx): %d fed entr%s taken out of its known list again", i, (unsigned long)snd, removed, removed == 1 ? "y" : "ies");
}
static void klbr_sense_feed(int i, DWORD now)      /* game thread, depth 0, host round, bot i is wrapped (klbr_ta[i].snd) and alive */
{
    struct klbr_s *e = &klbr_t[i]; DWORD G, rules, recs = 0, freeb = 0, B = 0, hs[16], cnt = 0, vt = 0; float hd[16], bp[3]; int n = 0, k, nr = 0, pick[KBR_SN_MAXFEED], np, alive = 0, haveb, shadow = 0;
    int c_used = 0, c_null = 0, c_dead = 0, c_cls = 0, c_bot = 0, c_seat = 0, c_pol = 0, c_h0 = 0; const char *why = 0;      /* bs14: Sense never fed and logged nothing; these say which gate skips */
    if (!klbr_snon || klbr_sn_flt >= 3 || klbr_trturn || !e->traitor) return;
    if (!kbr_sense_decide(1, 1, 1, 1, 1, 0, 1, 0, 0, kbr_rate_ok(klbr_sn_at[i], now, (unsigned long)klbr_snms))) return;
    klbr_sn_at[i] = now | 1u;
    G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); rules = G > 0xffff ? klh_rd32(G + 0x54) : 0;
    if (rules && rules == klbr_shadow) { shadow = 1; rules = klbr_rr_sw ? klbr_rr_rules : 0; }      /* the shadow holds the BOTS' table (crew at +0x348), not the humans' records at +8 */
    if (rules >= 0x10000) vt = klh_rd32(rules);
    if (rules < 0x10000) why = shadow ? "rules = shadow, no saved real rules" : "no rules";
    else if (!KLH_RULES_SV_OK(vt) && !KLH_RULES_CL_OK(vt)) why = "rules vtable not Sv/Cl";
    else if (!klh_rd(rules + 0x14, &cnt, 4) || cnt > 16) why = "record count unreadable or > 16";
    else { recs = klh_rd32(rules + 8); freeb = klh_rd32(rules + 0xc); B = klh_rd32(e->snd + 0x698); if (!recs || !freeb) why = "no records / free bytes"; else if (B < 0x10000) why = "no known list"; }
    if (why) cnt = 0;
    haveb = klbr_bot_pos(e->actor, bp, &alive);
    for (k = 0; k < (int)cnt && n < 16; k++) {
        BYTE used = 1, pol = 0; DWORD p; float hp = 1.0f, tp[3];
        if (!klh_rd(freeb + k, &used, 1) || used) { c_used++; continue; }
        { DWORD cl = klh_rd32(recs + 0x74 * (DWORD)k); p = cl > 0xffff ? klh_rd32(cl + 0x378) : 0; }      /* bs15: the record holds the CLIENT struct, the ZFFPlayer is [client+0x378] (klonline_read.c G1, klroundkeep.c); rec+0x378 read empty for both humans */
        if (p < 0x10000) { c_null++; continue; }
        klh_rd(p + 0x2723, &pol, 1);
        if (klbr_hp_read(p, &hp) && hp <= 0.0f) { c_dead++; continue; }      /* a dead body is not fed (unreadable health = fed) */
        if (klh_pvt(p) != 0x00bb45f4u) { c_cls++; continue; }
        if (pol) { c_pol++; continue; }
        if (klbr_hl_body(p)) c_seat++;      /* counted only: klbr_hl_body matches the seat index against the SHADOW record index, so a human in real seat k collided with bot rec k (bs14 suspect). GUESS: the real records hold no bot bodies */
        if (kbr_sense_decide(1, 1, 1, 1, 1, 0, 1, klbr_hl_find(p) != 0, 0, 1) != KBR_SN_FEED) { c_bot++; continue; }
        hd[n] = (haveb && klh_rd(p + 0x460, tp, 12) && kle_ok3(tp)) ? (float)kle_dist(bp, tp) : 1.0e30f;
        hs[n++] = p;
    }
    np = kbr_sense_nearest(hd, n, KBR_SN_MAXFEED, pick);
    for (k = 0; k < np; k++) {
        int r = klbr_sn_call(B, hs[pick[k]]), j, have = 0;
        if (r > 0) {
            klbr_sn_fed++; nr++;
            for (j = 0; j < klbr_sn_nfb[i]; j++) if (klbr_sn_fb[i][j] == hs[pick[k]]) have = 1;
            if (!have && klbr_sn_nfb[i] < KBR_SN_MAXFEED) klbr_sn_fb[i][klbr_sn_nfb[i]++] = hs[pick[k]];
        }
        if (r == 0) c_h0++;
        if (r < 0) break;
    }
    if (!nr && !klbr_sn_flt && klbr_sn_dlog < 8 && now - klbr_sn_dat >= 5000) { klbr_sn_dlog++; klbr_sn_dat = now; klog("brain: traitor sense: bot %d fed nothing: %s; rules %08lx%s vt %08lx count %lu; records free %d, empty body %d, dead %d, not ZFFPlayer %d, police %d, bot %d (seat-match only, still fed %d), handle 0 %d; found %d", i, why ? why : "gates passed", (unsigned long)rules, shadow ? " (shadow was in)" : "", (unsigned long)vt, (unsigned long)cnt, c_used, c_null, c_dead, c_cls, c_pol, c_bot, c_seat, c_h0, n); }
    if (klbr_sn_logged < 12 && (nr || klbr_sn_flt)) { klbr_sn_logged++; klog("brain: traitor sense: bot %d (soldier %08lx) %s fed %d of %d human body(ies) found (nearest %d max; list %08lx, ally count %lu parked during the call); calls this round %d, faults %d%s", i, (unsigned long)e->snd, klbr_sn_seen ? "MarkSeen" : "NoteEntity", nr, n, KBR_SN_MAXFEED, (unsigned long)B, (unsigned long)klh_rd32(B + 0xcc), klbr_sn_fed, klbr_sn_flt, klbr_sn_flt >= 3 ? "; Sense off for this round" : ""); }
}
typedef float (__fastcall *klbr_scfn)(DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD);
/* bs17 (11-03): with FireLine=2 every slot-111 call of the marked bot came NESTED in slot 113's swap (klbr_depth > 0), so the score was never logged
   (88 human candidates, target stayed 0). READ ONLY: after the untouched original, log the score and slot 111's gate inputs (re/traitor_slot111_gates_1103.md
   items 6-11a): bit10 of [[cand+4]+0x3c], [cand+0x2721], [cand+0x2723], [cand+0x2728], [cand+0xad4]==cand, the cand's entry flags in B=[self+0x698], and
   the session's role [sm+0x54] / mode [sm+0x5c] (wwr26esf3: 11a's 0x7f6850 reads the SESSION [0x168e598], not the rules; inside the swap expect 0 / 4). Shares the 8-a-round budget. */
static void klbr_ta_gatelog(DWORD self, DWORD a1, float r, const char *path)
{
    DWORD G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)), rules = G > 0xffff ? klh_rd32(G + 0x54) : 0, sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)), B = klh_rd32(self + 0x698), w4 = klh_rd32(a1 + 4), f3c = 0, cnt = 0, fl = 0xffffffff, k;
    unsigned char b21 = 0xff, b23 = 0xff, b28 = 0xff; float nt = 0.0f;
    if (w4 > 0xffff) f3c = klh_rd32(w4 + 0x3c);
    klh_rd(a1 + 0x2721, &b21, 1); klh_rd(a1 + 0x2723, &b23, 1); klh_rd(a1 + 0x2728, &b28, 1);
    if (B > 0xffff && klh_rd(B, &cnt, 4) && cnt <= 10) for (k = 0; k < cnt; k++) if (klh_rd32(B + 4 + 0x14 * k + 4) == a1) { fl = klh_rd32(B + 4 + 0x14 * k); break; }
    klh_rd((DWORD_PTR)KLH_VA(KLBR_TA_NOTARGET), &nt, 4); klbr_ta_sc_n++;
    klog("brain: traitor arcade: marked soldier %08lx scored human %08lx: %.2f ('no target' = %.2f: %s; %s) gates: bit10 %d, +2721 %u, +2723 %u, +2728 %u, +ad4==cand %d, B entry flags %08lx (ffffffff = not in B, count %lu), shadow rules %08lx; session role %lu mode %lu (11a reads the SESSION [0x168e598]: needs role 0/1 and mode 4)",
         (unsigned long)self, (unsigned long)a1, (double)r, (double)nt, r == nt ? "refused" : "targetable", path, (int)((f3c >> 10) & 1), b21, b23, b28, klh_rd32(a1 + 0xad4) == a1,
         (unsigned long)fl, (unsigned long)cnt, (unsigned long)rules, sm > 0xffff ? (unsigned long)klh_rd32(sm + 0x54) : 0ul, sm > 0xffff ? (unsigned long)klh_rd32(sm + 0x5c) : 0ul);
}
static float __fastcall klbr_w_score(DWORD self, DWORD edx, DWORD a1, DWORD a2, DWORD a3, DWORD a4, DWORD a5, DWORD a6, DWORD a7)      /* thiscall + 7 stack args, ret 0x1c: a __fastcall has the same stack layout */
{
    klbr_scfn org = (klbr_scfn)(DWORD_PTR)klbr_ta_org; float r = 0.0f; DWORD G, sm, role = 0, mode = 0, state = 0, probe = 0; struct klbr_s *e; int host, dec, flt = 0;
    (void)edx;
    if (!org) return 0.0f;
    if (klbr_clon && a1 > 0xffff && GetCurrentThreadId() == klbr_game_tid) klbr_cand_note(self, a1);      /* OnlineBrainTraitorCandLog: read only, before every other path */
    if (a1 > 0xffff && (klbr_hlon || klbr_dmon) && GetCurrentThreadId() == klbr_game_tid) klbr_hl_body(a1);      /* learns the bodies of tagged bots (the candidates), read only */
    if (klbr_hoon && !klbr_ta_dis && a1 > 0xffff && GetCurrentThreadId() == klbr_game_tid && klh_pvt(a1) == 0x00bb45f4ul && (e = klbr_find(self)) != 0 && e->state == 1 && e->traitor) {      /* HumanOnly */
        float nt = 0.0f;
        if (klbr_hl_body(a1) && klbr_hf_human_in_b(self) && klh_rd((DWORD_PTR)KLH_VA(KLBR_TA_NOTARGET), &nt, 4)) { klbr_ho_null++; return nt; }
        klbr_ho_pass++;
    }
    if (klbr_taon && !klbr_ta_dis && (klbr_depth > 0 || klbr_rr_sw) && klbr_ta_sc_n < 8 && a1 > 0xffff && GetCurrentThreadId() == klbr_game_tid && klh_pvt(a1) == 0x00bb45f4ul && (e = klbr_find(self)) != 0 && e->state == 1 && e->traitor) {
        r = org(self, 0, a1, a2, a3, a4, a5, a6, a7); klbr_ta_gatelog(self, a1, r, klbr_depth > 0 ? "nested in a swap frame" : "thunk swap in"); return r;      /* bs17: read only, the original runs as before */
    }
    if (!klbr_taon || klbr_ta_dis || klbr_depth > 0 || klbr_rr_sw || GetCurrentThreadId() != klbr_game_tid) return org(self, 0, a1, a2, a3, a4, a5, a6, a7);      /* nested in a DLL frame / thunk slice: never swap twice */
    G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)); e = klbr_find(self);
    host = sm > 0xffff && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4) && role == 2 && mode == 4 && state == KLB_ROUND;
    dec = kbr_tarc_decide(1, e && e->state == 1 && e->traitor, e != 0, a1 > 0xffff ? klh_pvt(a1) : 0, 0x00bb45f4ul, a1 > 0xffff && klh_rd(a1, &probe, 4), klbr_trturn, host);      /* candidate = first stack arg ([ebp+8] -> esi at 0x882477) */
    if (dec != KBR_TA_ARCADE || G <= 0xffff || !klbr_shadow) return org(self, 0, a1, a2, a3, a4, a5, a6, a7);
    if (!kbr_frame_enter(&klbr_depth) || !klbr_swap_in(G, sm)) { kbr_frame_leave(&klbr_depth); return org(self, 0, a1, a2, a3, a4, a5, a6, a7); }
    __try { r = org(self, 0, a1, a2, a3, a4, a5, a6, a7); }
    __except (EXCEPTION_EXECUTE_HANDLER) { flt = 1; }      /* the veh restore hook may already have put the real rules back; swap_out below is idempotent */
    if (kbr_frame_leave(&klbr_depth)) klbr_swap_out();
    if (flt) {      /* GUESS: after a fault the x87 stack is left as it is; the stock 'no target' float is the answer and the feature goes off for the rest of the round after 3 faults */
        float nt = 0.0f; klh_rd((DWORD_PTR)KLH_VA(KLBR_TA_NOTARGET), &nt, 4); r = nt; klbr_ta_flt++;
        klog("brain: traitor arcade: fault %d in the swapped slot-111 call (soldier %08lx, candidate %08lx), 'no target' returned%s", klbr_ta_flt, (unsigned long)self, (unsigned long)a1, klbr_ta_flt >= 3 ? "; feature off for this round" : "");
        if (klbr_ta_flt >= 3) klbr_ta_dis = 1;
    } else if (klbr_ta_sc_n < 8) {
        klbr_ta_gatelog(self, a1, r, "own swap");
    }
    return r;
}
/* ---- OnlineBrainTraitorFireLine (2026-11-03; re/fireline_gap_1103.md H1): ZSoldier slots 113 / 114 on the SAME private table (heap, never the stock table 0xbd0954, no hashed byte touched). ----------
   Slot 113 (+0x1c4) = 0x47a0f0 -> 0x767510, thiscall, 1 stack arg, ret 4, return meaningless. Slot 114 (+0x1c8) = 0x6bc0a0 -> 0x51d6c0, thiscall, 4 stack args (2 dwords then 2 floats, passed through as
   raw dwords), ret 0x10, int in eax. Both lead to 0x5706a0 (the fire-line friend list; 0x5709c2 / 0x570a12 read the mark only with the Arcade gate).
   Mode 1 = LOG ONLY: the original runs untouched, the marked bot's slot / index / return are logged. Mode 2 = SWAP: the shadow rules are in around the original, as in klbr_w_score, so the marked bot's
   friend list skips the human. GUESS: the swap is held for the WHOLE of 0x51d6c0 / 0x767510 (every candidate, every role / mode read inside), see the doc's caution; a nested slot-111 call sees klbr_depth > 0 and skips its own swap. */
#define KLBR_TFL_S113 113               /* vt + 0x1c4; original 0x47a0f0 (verified from the doc: ptr at 0xbd0b18 = 0xbd0954 + 0x1c4) */
#define KLBR_TFL_S114 114               /* vt + 0x1c8; original 0x6bc0a0 (ptr at 0xbd0b1c) */
#define KLBR_TFL_ORG113 0x0047a0f0
#define KLBR_TFL_ORG114 0x006bc0a0
#define KLBR_TFL_LOGMAX 8               /* log lines per slot per bot per wrap */
static DWORD klbr_tfl_org113, klbr_tfl_org114;
typedef DWORD (__fastcall *klbr_fl113fn)(DWORD, DWORD, DWORD);
typedef DWORD (__fastcall *klbr_fl114fn)(DWORD, DWORD, DWORD, DWORD, DWORD, DWORD);
static int klbr_tfl_begin(DWORD self, int *swapped, struct klbr_s **pe)      /* 0 = pass untouched, 1 = log only, 2 = swapped in (the caller must call klbr_tfl_end) */
{
    DWORD G, sm, role = 0, mode = 0, state = 0; struct klbr_s *e; int host, dec;
    *swapped = 0; *pe = 0;
    if (!klbr_tflmode || !klbr_taon || klbr_ta_dis || klbr_depth > 0 || klbr_rr_sw || GetCurrentThreadId() != klbr_game_tid) return 0;      /* nested in a DLL frame / thunk slice: never swap twice */
    e = klbr_find(self);
    if (!(e && e->state == 1 && e->traitor)) return 0;      /* unmarked: kbr_tfl_decide passes anyway; skip the three reads on the AI hot path */
    G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION));
    host = sm > 0xffff && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4) && role == 2 && mode == 4 && state == KLB_ROUND;
    dec = kbr_tfl_decide(klbr_tflmode, 1, e && e->state == 1 && e->traitor, e != 0, klbr_trturn, host);
    if (dec == KBR_TFL_PASS) return 0;
    *pe = e;
    if (dec == KBR_TFL_LOG) return 1;
    if (G <= 0xffff || !klbr_shadow) return 1;      /* cannot swap: still log */
    if (!kbr_frame_enter(&klbr_depth) || !klbr_swap_in(G, sm)) { kbr_frame_leave(&klbr_depth); return 1; }
    *swapped = 1;
    return 2;
}
static int klbr_tfl_end(DWORD self, int swapped, int flt, int slot)      /* swap out; 1 = a fault was counted (the caller returns 0) */
{
    if (swapped && kbr_frame_leave(&klbr_depth)) klbr_swap_out();
    if (!flt) return 0;
    klbr_ta_flt++;      /* shared with slot 111: 3 faults switch the whole Arcade feature off for the round */
    klog("brain: traitor fireline: fault %d in the swapped slot-%d call (soldier %08lx)%s", klbr_ta_flt, slot, (unsigned long)self, klbr_ta_flt >= 3 ? "; feature off for this round" : "");
    if (klbr_ta_flt >= 3) klbr_ta_dis = 1;
    return 1;
}
static void klbr_tfl_log(struct klbr_s *e, DWORD self, int which, int mode, DWORD ret)
{
    int ix = e ? (int)(e - klbr_t) : -1;
    if (ix < 0 || ix >= KLBR_MAX || klbr_ta[ix].nlog[which] >= KLBR_TFL_LOGMAX) return;
    klbr_ta[ix].nlog[which]++;
    klog("brain: traitor fireline: slot %d bot %d soldier %08lx %s: returned %08lx%s", which ? KLBR_TFL_S114 : KLBR_TFL_S113, ix, (unsigned long)self, mode == 2 ? "SWAPPED" : "log only", (unsigned long)ret, which ? "" : " (meaningless for slot 113)");
}
/* ---- OnlineBrainTraitorHolderFix (2026-11-03, workflow w53r6g2xi, verified by its third pass; UNTESTED, default off). ----------------------------------------------------------------------------------
   The marked bot's shots come from its tasks, not 0x7088c0: ZRunToPosShootingTask 0x4a7e60 (0x4a84ff / 0x4a855d / 0x4a85a1) and ZAttackTarget (0x4f494f / 0x4f4db1) call the fire test 0x616480
   (thiscall ecx = &holder flags [s+0xa8]: bit0 AND 0x10 set, 0x4 / 0x40 / 0x200 clear) before the body shot [[s+0x40]+0x6e4](handle, 2, f). bs20: the human holder sat at 0x05 (0x4 set, 0x10 clear).
   0x4 comes from the same-team sweep in 0x5706a0 (a same-team alive body on the line blocks, and nothing excludes the target itself; the session swap cannot change that stage); slot 113's quick
   path rewrites 0x4 on every call (0x76762e), so the fix is reapplied after every call. 0x10 = dist < range strictly (0x767a9b), range = 0x71e050 (thiscall ecx = [s+0x6a0], no args, float in st0:
   2 x weapon template range, else 10000.0); we recompute it with the actors' +0x460 positions (GUESS: the engine measures eye y+170 to aim y+150, close enough for a cap) and set 0x10 only inside it.
   Data write to one flag dword of the marked bot only; no code patch, no call other than the pure read 0x71e050 under __try. */
#define KLBR_HX_RANGE 0x0071e050
typedef float (__fastcall *klbr_rangefn)(DWORD, DWORD);
static int klbr_hxon; static long klbr_hx_set, klbr_hx_far, klbr_hx_flt;
static void klbr_hx_apply(struct klbr_s *e, DWORD self)
{
    DWORD hf, hp, hh, f6a0; float bp[3], tp[3], range = -1.0f; int alive = 0; double d;
    if (!klbr_hxon || !e || klh_rd32(self + 0x698) <= 0xffff) return;
    hf = klh_rd32(self + 0xa8); hp = klh_rd32(self + 0xac); hh = klh_rd32(self + 0xb0);
    if (!hh || !(hf & 1) || hp <= 0xffff || klh_pvt(hp) != 0x00bb45f4u || klbr_hl_body(hp) || klbr_hl_find(hp)) return;      /* only a human ZFFPlayer in the holder */
    if (!klbr_bot_pos(e->actor, bp, &alive) || !klh_rd(hp + 0x460, tp, 12) || !kle_ok3(tp)) return;
    if ((f6a0 = klh_rd32(self + 0x6a0)) > 0xffff && klbr_hx_flt < 3) {
        __try { range = ((klbr_rangefn)(DWORD_PTR)KLH_VA(KLBR_HX_RANGE))(f6a0, 0); }
        __except (EXCEPTION_EXECUTE_HANDLER) { range = -1.0f; if (++klbr_hx_flt >= 3) klog("brain: traitor holderfix: 0x71e050 faulted 3 times: range read off (no 0x10 set)"); }
    }
    d = kle_dist(bp, tp);
    if (!(range > 0.0f && range < 1.0e7f) || !(d < range)) { klbr_hx_far++; hf &= ~0x4ul; }      /* out of range / unknown: only the self-block bit goes */
    else { klbr_hx_set++; hf = (hf & ~0x4ul) | 0x10ul; }
    KLBR_P32(self + 0xa8) = hf;      /* just read through klh_rd: the live soldier, on the game thread */
}
/* ---- OnlineBrainTraitorCoverFire (2026-11-03, workflow wvf2fzwhg 'tasks' trace + verifier; UNTESTED, recommended off). bs22: with HolderFix the human holder passes the fire test (0x11) but the
   marked bot's Idle goal is terminated (state 4) and Attack never starts (0), so no shooting task runs. Copy of the shipped call at 0x907c0f-0x907c46 (re-read 11-03): pos = 0x7b3020(ecx = [holder
   entity + 4], &pos), then soldier slot 83 (vt + 0x14c = 0x831850, thiscall (handle 0, &pos, 5.0f [0xbcb330]), ret 0xc). With handle 0 and [[s+0x5ac]+8] in {0, 4} slot 83 runs 0x717f90 (CoverFire
   SetPosition into +0x654) and 0x637800(CoverFire +0x654, prio 0xa0, clock + 0x800) + slot 20 (arbiter): CoverFire outranks Idle 0x64. When +0x5ac is in another state slot 83 takes a different path
   (0x4c53b0 / 0x809830), so we do not call it then. Host bots only (klbr_t), marked bot, human holder whose flags pass 0x616480 (bit0 + 0x10, no 0x4 / 0x40 / 0x200), at most once per 2 s per bot.
   That CoverFire then shoots the human is a GUESS (bench bs23). The call goes through the private table, so HitLog's log-only slot-83 wrapper sees it. 3 faults -> off for the round. */
/* OnlineBrainTraitorAttackHandle (11-03, workflow wee6blb1x tasks verifier; UNTESTED, recommended off): the same call with handle = holder handle [s+0xb0]. Slot 83 then sets ZAttackTarget +0x14 and AddGoal
   at 0x831986 (prio 0x96); ZAttackTarget's tick 0x4f4460 runs ZRunToPosShootingTask / ZTurnAndShootTask through fire test 0x616480 -> [[s+0x40]+0x6e4]. Shipped callers all pass 0 (unexercised path). */
#define KLBR_CF_POS 0x007b3020
#define KLBR_CF_F5 0x00bcb330
#define KLBR_CF_LOGMAX 10
typedef DWORD (__fastcall *klbr_cfposfn)(DWORD, DWORD, DWORD);
typedef DWORD (__fastcall *klbr_cfatkfn)(DWORD, DWORD, DWORD, DWORD, DWORD);
#define KLBR_CF_REF 0x008ccde0      /* cdecl (handle) -> entity, generation-checked: a stale handle gives 0 (wedrgngwi, bytes 0x40a880) */
typedef DWORD (__cdecl *klbr_cfrefn)(DWORD);
static int klbr_cfon, klbr_cfh, klbr_cf_n, klbr_cf_flt; static long klbr_cf_calls, klbr_cf_skip, klbr_cf_stale; static DWORD klbr_cf_at[KLBR_MAX];
/* OnlineBrainTraitorRestart (11-03, workflow wuwffuc4b trace + verifier; UNTESTED, recommended off; needs AttackHandle). Nothing in kl2 resets a goal's state: the scheduler 0x63c5c0 re-runs a
   stack-top goal in state 0 / 4 from scratch (Run 0x65bbf0). A goal gets back on the stack only through the arbiter 0x81eb90's switch path, which is skipped (early return 0x81ec18) when the winner
   is already [s+0x74]. After a ZAttackTarget run ends, the scheduler pops it but [s+0x74] stays = the goal and its list entry (prio 0x96, never expires) stays: the bot is left with an empty stack that
   Idle (0x64) cannot win back. Restart: before our slot-83 call, when [s+0x74] is the +0x658 goal, write 0 there (the engine's own pattern at 0x651d5b), so slot 83's arbiter call switches and pushes it.
   Unfreeze: when the +0x658 goal is terminated (4), the stack is empty and [s+0x74] is that goal, call vt+0x1b4 (0x6e49b0, thiscall no args, plain ret: drops the prio-0x96 entries; checked equal
   before the call), write [s+0x74] = 0 and call the arbiter (thiscall (1), ret 4, as slot 83's vt+0x50 thunk 0x5f0cb0 does) so Idle wins and runs again.
   That Idle's list entry is still there at that point is a GUESS (the verifier saw Idle in state 4 on every bs25 line). */
#define KLBR_RS_DROP96 0x006e49b0
#define KLBR_RS_ARB 0x0081eb90
#define KLBR_RS_LOGMAX 10
typedef DWORD (__fastcall *klbr_rs0fn)(DWORD, DWORD);
typedef DWORD (__fastcall *klbr_rs1fn)(DWORD, DWORD, DWORD);
static int klbr_rson, klbr_rs_n, klbr_rs_flt; static long klbr_rs_clr, klbr_rs_unf, klbr_rs_unfskip;
/* CoverFire health readout (READ ONLY, bs24): the human holder's health at the call, +300 ms and +2 s, with the CoverFire goal state at each read. A drop can also come from cops or other bots,
   so it is evidence, not proof, that CoverFire shot; a flat line over many calls says it did not. */
static int klud_idx(DWORD p);      /* klucc_down.c (included after this file) */
#define KLBR_CF_HPLOGMAX 24
static struct { DWORD victim, t0, g; float hp0; int step; } klbr_cf_hp[KLBR_MAX];
static int klbr_cf_hpn; static long klbr_cf_hpdrop, klbr_cf_hpflat; static double klbr_cf_hpsum;
/* OnlineBrainTraitorFireProbe (11-03, workflow wqb7g1pxd follow-up; READ ONLY, recommended off; needs AttackHandle). After every slot-113 call of a marked bot: is ZRunToPosShootingTask (vt 0xbd0ba4) on the goal
   stack [s+4..s+8) and for how long, does ZFireWeaponTask (vt 0xbd0bd4, tick 0x7c02b0) ever appear there, and the gate inputs of the burst path (wqb7g1pxd): body = [s+0x40]; [body+0x544] = aim target HANDLE
   (0x62a540 compares it with its handle argument at 0x62a5b1: verified), [body+0x68c] prio, [body+0x690] expiry (read at the same function's tail, not re-disassembled: GUESS dword), byte [body+0x576] (must be 1
   at 0x62a581: verified), byte [body+0x57d] & 0x10 (GUESS: from the trace notes, not re-verified), brain [s+0x5a8] / [s+0x700] (GUESS gates from the trace), mode dword [[s+0x6d8]] (5 / 6 block: verified 6 at 0x62a553),
   holder [s+0xa8] flags / [s+0xac] / [s+0xb0], tuning floats [[0x168d7c0]+0x38c / 0x394 / 0x3a4 / 0x3ac] (0x394 / 0x3ac verified read at 0x8b8500-0x8b8514; 0x38c / 0x3a4 from the trace) once per bot per round,
   and the bot-to-holder distance. NOT done: counting calls of body vt+0x6e4 (0x62a540) and its return value: that needs a DLL-owned copy of the ZFFActor vtable (vt 0xbb3bac), which the codebase only has for the
   soldier (klbr_make_vtables); a body vtable swap would also touch every ZFFActor and the log would need a return hook, so it is skipped. Log lines: "traitor fireprobe:" (per-bot cap KLBR_FP_LOGMAX per round)
   plus one round total; faults of the 0x8ccde0 lookup switch it off after 3. */
#define KLBR_FP_RUN_VT 0x00bd0ba4
#define KLBR_FP_FIRE_VT 0x00bd0bd4
#define KLBR_FP_ZAT_VT 0x00bd1104
#define KLBR_FP_TUNE 0x0168d7c0
#define KLBR_FP_LOGMAX 10      /* episode-end lines per bot per round */
#define KLBR_FP_SMPMAX 6      /* sample lines per bot per round (separate counter, so they cannot starve the episode-end lines) */
static int klbr_fpon, klbr_fp_flt;
static struct { DWORD rt, ft, rf, rl, ff, fl, lastlog, t0; int n, en, atk, tuned; long calls, rcalls, fcalls, eps, fireeps; DWORD maxep; DWORD s0, sl, e0, bs0, bsl; int shv, chf; long chcalls, cheps, shep; } klbr_fp[KLBR_MAX];
/* FireProbe extension (11-03, workflow w6wznnvc5; still READ ONLY). Shot counter: 0x6c81a0 (disassembled: thiscall, ecx = weapon controller F, [F] = the owner body, arg1 = count, arg2 = item) does
   [[F]+0x550] += count (0x6c81f3-0x6c81f8, VERIFIED), so the counter lives on the BODY [F+0] (verifier right; the tracer's 's' was wrong). We read [body+0x550] with body = [s+0x40] (the same object IF [F] == [s+0x40]:
   GUESS, so [F+0] is logged too) and, labelled, [s+0x550] as the tracer would have it. Per episode (run task seen -> gone) delta, per round first->last delta and the sum of the episode deltas. Child: the run task's running
   child [[run+0xc]+0x50] (VERIFIED: RunChild 0x521350 stores its argument there) and whether its vtable is 0xbd0bd4 (ZFireWeaponTask). Weapon controller F = [s+0x6a0]: dwords [F+8] flags, [F+0x20], [F+0x24], item [F+4], [item+0xf8]
   (types GUESS: raw hex, plus the float reading of +0x20 / +0x24). Victim-gate globals once per sample: session sm = [0x168e598] (+0x70 state: 0x4db58c calls 0x8e6a20 = mov eax,[ecx+0x70] (cmp eax,0x28 at 0x4db591) and drops at >= 0x28, VERIFIED;
   +0x54 role, +0x5c type: 0x4 = FA family, 0x6e347c VERIFIED), [0x1535a2c] (0x6e35fc: 1 skips the health write, 2 = 0.01, VERIFIED), sub-mode [0x168e59c] (0x6e3486, 0: FA, VERIFIED),
   rules byte: 0x7bb2a0 returns [[0x168e9e4]+0x54] when [sm+0x5c] == 4, its vt+0x2f4 is 0x4ee010 = mov al,[ecx+0x285] (VERIFIED). Body class: vtable 0xbb45f4 ZFFPlayer / 0xbb3bac ZFFActor and bytes +0x2723 / +0x2726.
   The human holder's hp is NOT repeated here: OnlineBrainTraitorCoverFire's health readout and the HitLog 'hit health' lines carry it. Line prefix of the new sample line: "brain: traitor fireprobe ext:". */
#define KLBR_RDG(a) klh_rd32((DWORD_PTR)KLH_VA(a))
static double klbr_fp_f(DWORD v) { float f; memcpy(&f, &v, 4); return (double)f; }
static void klbr_fp_ext(int ix, DWORD self, DWORD body, DWORD run, DWORD sc)      /* one extra sample line, read only */
{
    DWORD F = klh_rd32(self + 0x6a0), item = F > 0xffff ? klh_rd32(F + 4) : 0, sm = KLBR_RDG(0x168e598), rl = 0, ch = 0, chv = 0, c0, bvt = 0; BYTE b23 = 0, b26 = 0, b285 = 0xff; int sm5c = -1;
    if (run > 0xffff && (c0 = klh_rd32(run + 0xc)) > 0xffff) { ch = klh_rd32(c0 + 0x50); if (ch > 0xffff) chv = klh_pvt(ch); }
    if (body > 0xffff) { bvt = klh_pvt(body); if (bvt != 0x00bb45f4u && klh_avt(body) == 0x00bb3bacu) bvt = 0x00bb3bacu; klh_rd(body + 0x2723, &b23, 1); klh_rd(body + 0x2726, &b26, 1); }
    if (sm > 0xffff) sm5c = (int)klh_rd32(sm + 0x5c);
    if (sm5c == 4) { DWORD g = KLBR_RDG(0x168e9e4); if (g > 0xffff && (rl = klh_rd32(g + 0x54)) > 0xffff) klh_rd(rl + 0x285, &b285, 1); }      /* 0x7bb2a0: [rules+0x54] only when the type is 4 */
    klog("brain: traitor fireprobe ext: bot %d shots [body+0x550] %lu ([F+0] %08lx %s [s+0x40]; [s+0x550] = %lu) [s+0x98] %08lx; run child %08lx vt %08lx %s; F %08lx flags[+8] %08lx [+0x20] %08lx (%.2f) [+0x24] %08lx (%.2f) item %08lx [item+0xf8] %08lx; "
         "session %08lx state[+0x70] %ld (drop at >= 40) role[+0x54] %ld type[+0x5c] %d [0x1535a2c] %lu submode[0x168e59c] %ld rules %08lx +0x285 %02x; body class %s +0x2723 %d +0x2726 %d",
         ix, (unsigned long)sc, (unsigned long)(F > 0xffff ? klh_rd32(F) : 0), (F > 0xffff && klh_rd32(F) == body) ? "==" : "!=", (unsigned long)(self ? klh_rd32(self + 0x550) : 0), (unsigned long)klh_rd32(self + 0x98), (unsigned long)ch, (unsigned long)chv,
         chv == KLBR_FP_FIRE_VT ? "= ZFireWeaponTask" : "(not ZFireWeaponTask)", (unsigned long)F, (unsigned long)(F > 0xffff ? klh_rd32(F + 8) : 0), (unsigned long)(F > 0xffff ? klh_rd32(F + 0x20) : 0), klbr_fp_f(F > 0xffff ? klh_rd32(F + 0x20) : 0),
         (unsigned long)(F > 0xffff ? klh_rd32(F + 0x24) : 0), klbr_fp_f(F > 0xffff ? klh_rd32(F + 0x24) : 0), (unsigned long)item, (unsigned long)(item > 0xffff ? klh_rd32(item + 0xf8) : 0),
         (unsigned long)sm, (long)(sm > 0xffff ? (int)klh_rd32(sm + 0x70) : -1), (long)(sm > 0xffff ? (int)klh_rd32(sm + 0x54) : -1), sm5c, (unsigned long)KLBR_RDG(0x1535a2c), (long)(int)KLBR_RDG(0x168e59c), (unsigned long)rl, (unsigned)b285,
         bvt == 0x00bb45f4u ? "ZFFPlayer" : bvt == 0x00bb3bacu ? "ZFFActor" : "other/unreadable", (int)b23, (int)b26);
}
/* OnlineBrainTraitorHoldFire (11-03; UNTESTED, recommended off, CHANGES behaviour; needs AttackHandle). klbr_cf_apply (our slot-83 order, with Restart's [s+0x74] clear) is skipped for a bot while its ZAttackTarget
   goal [s+0x658] is in state 1-3, or a ZRunToPosShootingTask / ZFireWeaponTask on its stack is in state 1-3 (GUESS: the task's state is at +8 like every goal; the extra task test is broader than the goal test
   because cf_apply's own gate already skips goal states 1-3), for at most KLBR_HF_MAXMS from the first held call; then one call is allowed (so a stuck bot is not frozen) and the window restarts at the next hold.
   Hypothesis (GUESS, wqb7g1pxd): our re-runs end the child before ZFireWeaponTask fires. Skips are counted in the round total. No engine call, no write. */
#define KLBR_HF_MAXMS 6000
static int klbr_hfion; static long klbr_hfi_skip, klbr_hfi_allow; static DWORD klbr_hfi_at[KLBR_MAX], klbr_hfi_seen;      /* at = hold window start; seen = bitmask of bots whose raw task/goal states were logged */
static int klbr_fp_scan(DWORD self, DWORD *run, DWORD *fire)      /* read only: first ZRunToPosShootingTask / ZFireWeaponTask on the goal stack; returns the stack depth (-1 unreadable) */
{
    DWORD sb = klh_rd32(self + 4), se = klh_rd32(self + 8), p; *run = *fire = 0;
    if (sb <= 0xffff || se < sb || se - sb > 64 * 4) return -1;
    for (p = sb; p < se; p += 4) {
        DWORD t = klh_rd32(p), v;
        if (t <= 0xffff) continue;
        v = klh_pvt(t);
        if (v == KLBR_FP_RUN_VT && !*run) *run = t;
        else if (v == KLBR_FP_FIRE_VT && !*fire) *fire = t;
    }
    return (int)((se - sb) / 4);
}
static int klbr_hfi_hold(int ix, DWORD self, DWORD now)      /* 1 = skip this order; 0 with klbr_hfi_at[ix] set = release due (cleared by the caller only when the order is really sent) */
{
    DWORD run, fire, g, gs = 0xffffffff, rs = 0xffffffff, fs = 0xffffffff; int busy;
    if (!klbr_hfion || ix < 0 || ix >= KLBR_MAX) return 0;
    klbr_fp_scan(self, &run, &fire);
    g = klh_rd32(self + 0x658); if (g > 0xffff && klh_pvt(g) == KLBR_FP_ZAT_VT) gs = klh_rd32(g + 8);
    if (run) rs = klh_rd32(run + 8);      /* GUESS: task state at +8 like every goal */
    if (fire) fs = klh_rd32(fire + 8);
    if ((run || fire) && !(klbr_hfi_seen & (1u << ix))) { klbr_hfi_seen |= 1u << ix; klog("brain: traitor holdfire: bot %d first task seen: run %08lx state %08lx fire %08lx state %08lx ZAttackTarget goal state %08lx (offset +8 is a GUESS: 0xffffffff = absent)", ix, (unsigned long)run, (unsigned long)rs, (unsigned long)fire, (unsigned long)fs, (unsigned long)gs); }
    busy = (run && rs >= 1 && rs <= 3) || (fire && fs >= 1 && fs <= 3) || ((run || fire) && gs >= 1 && gs <= 3);      /* either task running, or a goal in state 1-3 with a shooting task on the stack */
    if (!busy) { klbr_hfi_at[ix] = 0; return 0; }
    if (!klbr_hfi_at[ix]) klbr_hfi_at[ix] = now;
    if (now - klbr_hfi_at[ix] < KLBR_HF_MAXMS) { klbr_hfi_skip++; return 1; }
    return 0;      /* window over: the order may go; the window is cleared and 'allowed' counted only when it is sent */
}
static DWORD klbr_fp_gt(void)      /* GUESS: game time tick = [[0xdd2640]+0x48] (from the 0x62a5eb disassembly notes), 0 if unreadable */
{
    DWORD g = klh_rd32((DWORD)(DWORD_PTR)KLH_VA(0xdd2640)); return g > 0xffff ? klh_rd32(g + 0x48) : 0;
}
static void klbr_fp_epend(int ix, const char *how)      /* closes the open ZRunToPosShootingTask episode (gone, or replaced by another task pointer) */
{
    klbr_fp[ix].shep += (long)(klbr_fp[ix].sl - klbr_fp[ix].e0);
    if (klbr_fp[ix].en < KLBR_FP_LOGMAX) { klbr_fp[ix].en++; klog("brain: traitor fireprobe: bot %d episode shots [body+0x550] %lu -> %lu (+%ld), fire task seen as the run task's child: %s", ix, (unsigned long)klbr_fp[ix].e0, (unsigned long)klbr_fp[ix].sl, (long)(klbr_fp[ix].sl - klbr_fp[ix].e0), klbr_fp[ix].chf ? "yes" : "no"); klog("brain: traitor fireprobe: bot %d ZRunToPosShootingTask %08lx %s after %lu ms (seen %lu..%lu ms after the bot's first call, ZAttackTarget current at start: %s); ZFireWeaponTask on the soldier goal stack [s+4..s+8) in this episode: %s (it may be owned by the run task instead: 'no' is not conclusive)",
        ix, (unsigned long)klbr_fp[ix].rt, how, (unsigned long)(klbr_fp[ix].rl - klbr_fp[ix].rf), (unsigned long)(klbr_fp[ix].rf - klbr_fp[ix].t0), (unsigned long)(klbr_fp[ix].rl - klbr_fp[ix].t0), klbr_fp[ix].atk ? "yes" : "no", klbr_fp[ix].ff ? "yes" : "no"); }
    klbr_fp[ix].chf = 0;
}
static void klbr_fp_apply(struct klbr_s *e, DWORD self)      /* game thread, after the slot-113 call; read only */
{
    DWORD now = GetTickCount(), run, fire, body, hp, hh, tgt, mode, p6, depth; int ix, d; float dist = -1.0f, bp[3], tp[3]; int alive = 0;
    if (!klbr_fpon || klbr_fp_flt >= 3 || !klbr_cfh || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    d = klbr_fp_scan(self, &run, &fire); depth = (DWORD)d;
    klbr_fp[ix].calls++; if (!klbr_fp[ix].t0) klbr_fp[ix].t0 = now;
    body = klh_rd32(self + 0x40); { DWORD sc = body > 0xffff ? klh_rd32(body + 0x550) : 0, bs = klh_rd32(self + 0x550); if (body > 0xffff) { if (!klbr_fp[ix].shv) { klbr_fp[ix].shv = 1; klbr_fp[ix].s0 = sc; klbr_fp[ix].bs0 = bs; } klbr_fp[ix].sl = sc; klbr_fp[ix].bsl = bs; } }      /* shot counter (0x6c81a0 adds to [body+0x550]) and the [s+0x550] reading: first / latest value per round */
    if (run) {
        klbr_fp[ix].rcalls++;
        if (run != klbr_fp[ix].rt && klbr_fp[ix].rt) klbr_fp_epend(ix, "replaced by another task");      /* no empty call in between: close the old episode before the new one starts */
        { DWORD c0 = klh_rd32(run + 0xc), ch = c0 > 0xffff ? klh_rd32(c0 + 0x50) : 0; if (ch > 0xffff && klh_pvt(ch) == KLBR_FP_FIRE_VT) { klbr_fp[ix].chcalls++; if (!klbr_fp[ix].chf) { klbr_fp[ix].chf = 1; klbr_fp[ix].cheps++; } } }      /* the run task's child [[run+0xc]+0x50] (RunChild 0x521350, VERIFIED) is a ZFireWeaponTask */
        if (run != klbr_fp[ix].rt) { klbr_fp[ix].rt = run; klbr_fp[ix].rf = now; klbr_fp[ix].eps++; klbr_fp[ix].ff = 0; klbr_fp[ix].e0 = klbr_fp[ix].sl; { DWORD a = klh_rd32(self + 0x658); klbr_fp[ix].atk = (a > 0xffff && klh_pvt(a) == KLBR_FP_ZAT_VT && klh_rd32(self + 0x74) == a); } }
        klbr_fp[ix].rl = now;
        if (now - klbr_fp[ix].rf > klbr_fp[ix].maxep) klbr_fp[ix].maxep = now - klbr_fp[ix].rf;
    } else if (klbr_fp[ix].rt) {      /* episode over */
        klbr_fp_epend(ix, "gone");
        klbr_fp[ix].rt = 0;
    }
    if (fire) {
        klbr_fp[ix].fcalls++;
        if (fire != klbr_fp[ix].ft) { klbr_fp[ix].ft = fire; klbr_fp[ix].fireeps++; }
        if (!klbr_fp[ix].ff) klbr_fp[ix].ff = now;
        klbr_fp[ix].fl = now;
    } else klbr_fp[ix].ft = 0;
    if (!run && !fire) return;
    if (klbr_fp[ix].n >= KLBR_FP_SMPMAX || (now - klbr_fp[ix].lastlog < 1000 && !(fire && klbr_fp[ix].ff == now))) return;
    klbr_fp[ix].lastlog = now; klbr_fp[ix].n++;
    hp = klh_rd32(self + 0xac); hh = klh_rd32(self + 0xb0); tgt = 0; mode = 0xffffffff;
    if (body > 0xffff) {
        DWORD h = klh_rd32(body + 0x544);      /* aim target handle */
        if (h) { __try { tgt = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { tgt = 0; if (++klbr_fp_flt >= 3) klog("brain: traitor fireprobe: 0x8ccde0 faulted 3 times: off"); } }
    }
    p6 = klh_rd32(self + 0x6d8); if (p6 > 0xffff) mode = klh_rd32(p6);
    if (hp > 0xffff && klh_pvt(hp) == 0x00bb45f4u && klbr_bot_pos(e->actor, bp, &alive) && klh_rd(hp + 0x460, tp, 12) && kle_ok3(tp)) dist = (float)kle_dist(bp, tp);
    { BYTE b576 = 0, b57d = 0; if (body > 0xffff) { klh_rd(body + 0x576, &b576, 1); klh_rd(body + 0x57d, &b57d, 1); }
      klog("brain: traitor fireprobe: bot %d t+%lu ms stack %ld run %08lx (%lu ms) fire %08lx; body %08lx aim %08lx%s prio %ld expiry %lu (game time %lu, GUESS [[0xdd2640]+0x48]) b576 %02x b57d&10 %d; brain +5a8 %08lx +700 %08lx mode %ld; holder %08lx flags %03lx handle %08lx dist %.1f m",
           ix, (unsigned long)(now - klbr_fp[ix].t0), (long)(int)depth, (unsigned long)run, (unsigned long)(run ? now - klbr_fp[ix].rf : 0), (unsigned long)fire, (unsigned long)body, (unsigned long)tgt, (tgt && tgt == hp) ? " (= holder)" : "",
           (long)(int)(body > 0xffff ? klh_rd32(body + 0x68c) : 0), (unsigned long)(body > 0xffff ? klh_rd32(body + 0x690) : 0), (unsigned long)klbr_fp_gt(), (unsigned)b576, (b57d & 0x10) ? 1 : 0,
           (unsigned long)klh_rd32(self + 0x5a8), (unsigned long)klh_rd32(self + 0x700), (long)(int)mode, (unsigned long)hp, (unsigned long)klh_rd32(self + 0xa8), (unsigned long)hh, (double)(dist >= 0.0f ? dist / 100.0f : dist)); }
    klbr_fp_ext(ix, self, body, run, klbr_fp[ix].sl);
    if (!klbr_fp[ix].tuned) {
        DWORD tp0 = 0, f[4] = { 0, 0, 0, 0 }; float v[4]; static const DWORD off[4] = { 0x38c, 0x394, 0x3a4, 0x3ac }; int k, ok = 1;
        klbr_fp[ix].tuned = 1;
        if (!klh_rd((DWORD_PTR)KLH_VA(KLBR_FP_TUNE), &tp0, 4) || tp0 <= 0xffff) return;
        for (k = 0; k < 4; k++) { if (!klh_rd(tp0 + off[k], &f[k], 4)) ok = 0; memcpy(&v[k], &f[k], 4); }
        if (ok) klog("brain: traitor fireprobe: bot %d tuning floats [[0x168d7c0]+0x38c/0x394/0x3a4/0x3ac] = %.1f %.1f %.1f %.1f (0x8b84b0 distance gate; distance to the holder above)", ix, (double)v[0], (double)v[1], (double)v[2], (double)v[3]);
    }
}
/* OnlineBrainTraitorTraitorByte (11-03, workflow w6wznnvc5; UNTESTED, recommended off, CHANGES behaviour; needs AttackHandle). 0x6e3400 (victim = ecx/esi, arg1 = the damage float, arg2 = the attacker object; disassembled): edi = arg2 only when
   its class test (vt+0x30 & [0x1548c80] == [0x1548c7c], GUESS: ZFFPlayer-class membership) passes, else 0 and every filter is skipped (je 0x6e35fc: full damage). In sub-mode 0 (FA, [0x168e59c], type 4) an attacker edi that is
   not police ([edi+0x2723]) and not a traitor ([edi+0x2726], 0x6e356f jne 0x6e35ab) against a victim that is neither (0x6e3578 / 0x6e3581) gets its delta zeroed unless rules vt+0x2f4 ([rules+0x285]) is true (0x6e358a-0x6e35a5): VERIFIED.
   The byte read is the ATTACKER's, i.e. the bot's own ZFFPlayer body; so while a bot is marked and its body [s+0x40] is a ZFFPlayer we set [body+0x2726] = 1 (through klh_data, as OnlineBrainTraitorDamage and kladren.c do; the
   sense-manager call 0x4801a0 of the game's setter is skipped: same ASSUMED-harmless caveat; other bots may treat that body as hostile). Remembered old byte + seat (klud_idx) + body; put back at unmark / round end / round change, only
   while the body is still that seat's ZFFPlayer and the byte still holds our 1. A ZFFActor body is not affected by the filter (edi = 0 there, GUESS from the class test), so nothing is written: logged once per bot per round.
   If the byte is already nonzero (the game or OnlineBrainTraitorDamage set it) nothing is written or restored. No game call, so no fault counter. Log: "brain: traitor traitorbyte:". ---- */
static int klbr_tbon; static struct { DWORD body; int set, seat; BYTE old; } klbr_tb[KLBR_MAX]; static DWORD klbr_tb_told;
static long klbr_tb_reset, klbr_tb_set, klbr_tb_rest, klbr_tb_lost, klbr_tb_have, klbr_tb_actor, klbr_tb_other, klbr_tb_refused;
static void klbr_tb_restore(int i, const char *why)
{
    DWORD body; BYTE b = 0, old; int cur = -1;
    if (i < 0 || i >= KLBR_MAX || !klbr_tb[i].set) return;
    body = klbr_tb[i].body; old = klbr_tb[i].old; klbr_tb[i].set = 0;
    if (body > 0xffff && klh_pvt(body) == 0x00bb45f4u && klud_idx(body) == klbr_tb[i].seat && klh_rd(body + 0x2726, &b, 1)) cur = b;
    if (cur == 1) {
        if (klh_data((void *)(DWORD_PTR)(body + 0x2726), &old, 1, "player: the traitor byte back (OnlineBrainTraitorTraitorByte)")) { klbr_tb_rest++; klog("brain: traitor traitorbyte: bot %d body %08lx +0x2726 restored to %d (%s)", i, (unsigned long)body, (int)old, why); }
        else { klbr_tb_lost++; klog("brain: traitor traitorbyte: bot %d body %08lx +0x2726 restore REFUSED (%s)", i, (unsigned long)body, why); }
    } else { klbr_tb_lost++; klog("brain: traitor traitorbyte: bot %d body %08lx +0x2726 NOT written back (%s): %s", i, (unsigned long)body, why, cur < 0 ? "the body is gone or is another seat now" : "the byte no longer holds our 1"); }
    klbr_tb[i].body = 0;
}
static void klbr_tb_apply(struct klbr_s *e, DWORD self)      /* game thread, after every slot-113 call of a bot (host only) */
{
    DWORD body; BYTE b = 0, one = 1; int ix;
    if (!klbr_tbon || !klbr_cfh || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    if (e->state != 1 || !e->traitor) { klbr_tb_restore(ix, "the mark is gone"); return; }
    body = klh_rd32(self + 0x40);
    if (body <= 0xffff) return;
    if (klbr_tb[ix].set && klbr_tb[ix].body != body) klbr_tb_restore(ix, "the body pointer changed");      /* a restore with a NULL e (no ix) cannot happen here: such a bot keeps the byte until round end / round change (klbr_tb_restore_all) */
    if (klbr_tb[ix].set) {      /* 0x6ef624-0x6ef670 (player reset, writes +0x2726 at 0x6ef64e) may zero the byte on a respawn of the same body: write our 1 again, keep the saved original */
        if (klh_rd(body + 0x2726, &b, 1) && b == 0) { if (klh_data((void *)(DWORD_PTR)(body + 0x2726), &one, 1, "player: the traitor byte again after a reset (OnlineBrainTraitorTraitorByte)")) { klbr_tb_reset++; if (klbr_tb_reset <= 5) klog("brain: traitor traitorbyte: bot %d body %08lx +0x2726 had been zeroed (respawn / player reset, GUESS): set to 1 again", ix, (unsigned long)body); } else if (klbr_tb_refused++ < 5) klog("brain: traitor traitorbyte: bot %d body %08lx: the +0x2726 re-write was refused", ix, (unsigned long)body); }
        return;
    }
    if (klh_pvt(body) != 0x00bb45f4u) {
        if (klh_avt(body) == 0x00bb3bacu) klbr_tb_actor++; else klbr_tb_other++;
        if (!(klbr_tb_told & (1u << ix))) { klbr_tb_told |= 1u << ix; klog("brain: traitor traitorbyte: bot %d body %08lx is %s, not a ZFFPlayer: the byte does not apply (0x6e3400 drops a non-player attacker before its same-side filter, GUESS), nothing written", ix, (unsigned long)body, klh_avt(body) == 0x00bb3bacu ? "a ZFFActor" : "another class"); }
        return;
    }
    if (!klh_rd(body + 0x2726, &b, 1)) return;
    if (b) { klbr_tb_have++; return; }      /* already a traitor byte (the game's, or OnlineBrainTraitorDamage's): neither written nor restored */
    if (!klh_data((void *)(DWORD_PTR)(body + 0x2726), &one, 1, "player: the traitor byte of a marked bot (OnlineBrainTraitorTraitorByte)")) { if (klbr_tb_refused++ < 5) klog("brain: traitor traitorbyte: bot %d body %08lx: the +0x2726 write was refused", ix, (unsigned long)body); return; }
    klbr_tb[ix].body = body; klbr_tb[ix].set = 1; klbr_tb[ix].seat = klud_idx(body); klbr_tb[ix].old = b; klbr_tb_set++;
    klog("brain: traitor traitorbyte: set: bot %d body %08lx (crew seat %d) +0x2726 %d -> 1 (0x6e3400 then keeps the bot's hits on plain heisters; other bots may treat him as hostile)", ix, (unsigned long)body, klbr_tb[ix].seat, (int)b);
}
static void klbr_tb_restore_all(const char *why) { int i; for (i = 0; i < KLBR_MAX; i++) klbr_tb_restore(i, why); klbr_tb_told = 0; }      /* told: once per bot per round, also when no summary runs */
static void klbr_fp_summary(void)
{
    int i;
    klbr_tb_restore_all("round end");      /* OnlineBrainTraitorTraitorByte: before the counts, while klbr_t is still intact */
    if (klbr_tbon) klog("brain: traitor traitorbyte: round total: byte set %ld, restored %ld, not restored (body gone / byte changed / refused) %ld, re-set after a reset %ld, slot-113 calls: byte already nonzero %ld, with a ZFFActor body (not applicable) %ld, other class %ld; refused writes %ld", klbr_tb_set, klbr_tb_rest, klbr_tb_lost, klbr_tb_reset, klbr_tb_have, klbr_tb_actor, klbr_tb_other, klbr_tb_refused);
    klbr_tb_set = klbr_tb_reset = klbr_tb_rest = klbr_tb_lost = klbr_tb_have = klbr_tb_actor = klbr_tb_other = klbr_tb_refused = 0; klbr_tb_told = 0; memset(klbr_tb, 0, sizeof klbr_tb);
    if (klbr_fpon) for (i = 0; i < KLBR_MAX; i++) if (klbr_fp[i].calls)
        klog("brain: traitor fireprobe: round total: bot %d slot-113 calls %ld, with ZRunToPosShootingTask %ld (%ld episodes, longest %lu ms), with ZFireWeaponTask %ld (%ld episodes)%s", i, klbr_fp[i].calls, klbr_fp[i].rcalls, klbr_fp[i].eps, (unsigned long)klbr_fp[i].maxep, klbr_fp[i].fcalls, klbr_fp[i].fireeps, klbr_fp[i].fcalls ? "" : " (ZFireWeaponTask never on the stack)");
    if (klbr_fpon) for (i = 0; i < KLBR_MAX; i++) if (klbr_fp[i].rt) klog("brain: traitor fireprobe: bot %d episode still open at round end: ZRunToPosShootingTask %08lx, ZFireWeaponTask on the stack %s", i, (unsigned long)klbr_fp[i].rt, klbr_fp[i].ff ? "yes" : "no");
    if (klbr_fpon) for (i = 0; i < KLBR_MAX; i++) if (klbr_fp[i].shv)
        klog("brain: traitor fireprobe: round total: bot %d shots [body+0x550] %lu -> %lu (+%ld in the round, +%ld inside closed ZRunToPosShootingTask episodes; [s+0x550] %lu -> %lu), ZFireWeaponTask seen as the run task's child on %ld calls (%ld episodes)%s", i,
            (unsigned long)klbr_fp[i].s0, (unsigned long)klbr_fp[i].sl, (long)(klbr_fp[i].sl - klbr_fp[i].s0), klbr_fp[i].shep, (unsigned long)klbr_fp[i].bs0, (unsigned long)klbr_fp[i].bsl, klbr_fp[i].chcalls, klbr_fp[i].cheps, klbr_fp[i].sl == klbr_fp[i].s0 ? " (the shot counter never moved)" : "");
    if (klbr_fpon) klog("brain: traitor fireprobe: round total: faults %d", klbr_fp_flt);
    if (klbr_hfion) klog("brain: traitor holdfire: round total: orders skipped %ld, allowed after %d ms %ld", klbr_hfi_skip, KLBR_HF_MAXMS, klbr_hfi_allow);
    memset(klbr_fp, 0, sizeof klbr_fp); klbr_fp_flt = 0; klbr_hfi_skip = klbr_hfi_allow = 0; memset(klbr_hfi_at, 0, sizeof klbr_hfi_at); klbr_hfi_seen = 0;
}
static void klbr_cf_apply(struct klbr_s *e, DWORD self)
{
    DWORD hf, hp, hh, node, s5, st, vt, fn, f5 = 0, g, g0s = 0xffffffff, g1s = 0xffffffff, cur0, cur1, now = GetTickCount(); float p[3] = { 0, 0, 0 }; int ix, ok = 0;
    if (!klbr_cfon || klbr_cf_flt >= 3 || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    hf = klh_rd32(self + 0xa8); hp = klh_rd32(self + 0xac); hh = klh_rd32(self + 0xb0);
    if (!hh || (hf & 0x11) != 0x11 || (hf & 0x244) || hp <= 0xffff || klh_pvt(hp) != 0x00bb45f4u || klbr_hl_body(hp) || klbr_hl_find(hp)) { klbr_hfi_at[ix] = 0; return; }      /* human holder that passes the fire test; else a HoldFire window is stale */
    if (klbr_cf_at[ix] && now - klbr_cf_at[ix] < 2000) return;
    if (klbr_cfh && klbr_hfi_hold(ix, self, now)) return;      /* OnlineBrainTraitorHoldFire: let a running shooting task finish */
    if ((s5 = klh_rd32(self + 0x5ac)) <= 0xffff || ((st = klh_rd32(s5 + 8)) != 0 && st != 4)) { klbr_cf_skip++; return; }
    if ((node = klh_rd32(hp + 4)) <= 0xffff || (vt = klh_rd32(self)) <= 0xffff || (fn = klh_rd32(vt + 0x14c)) <= 0xffff || !klh_rd((DWORD_PTR)KLH_VA(KLBR_CF_F5), &f5, 4)) return;
    if (klbr_cfh) {      /* wedrgngwi guards: the tick derefs 0x8ccde0([goal+0x14]) unchecked (0x4f44a7), so the handle must still resolve to this human; slot 83 rewrites +0x14 before its state test, so +0x658 must be idle */
        DWORD r = 0, ga = klh_rd32(self + 0x658), gs;
        if (ga <= 0xffff || ((gs = klh_rd32(ga + 8)) != 0 && gs != 4)) { klbr_cf_skip++; return; }
        __try { r = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(hh); } __except (EXCEPTION_EXECUTE_HANDLER) { r = 0; }
        if (r != hp) { klbr_cf_stale++; klbr_cf_skip++; return; }
    }
    klbr_cf_at[ix] = now;
    if (klbr_hfi_at[ix]) { klbr_hfi_at[ix] = 0; klbr_hfi_allow++; }      /* HoldFire: a window still open here was released (expired), and the order is now really sent */
    g = klh_rd32(self + (klbr_cfh ? 0x658 : 0x654)); if (g > 0xffff) g0s = klh_rd32(g + 8); cur0 = klh_rd32(self + 0x74);      /* AttackHandle: ZAttackTarget +0x658 (prio 0x96), else CoverFire +0x654 */
    __try {
        ((klbr_cfposfn)(DWORD_PTR)KLH_VA(KLBR_CF_POS))(node, 0, (DWORD)(DWORD_PTR)p);
        if (kle_ok3(p) && klbr_rson && cur0 == g && g > 0xffff) { KLBR_P32(self + 0x74) = 0; klbr_rs_clr++; }      /* OnlineBrainTraitorRestart: the arbiter in slot 83 then switches to g */
        if (kle_ok3(p)) { ((klbr_cfatkfn)(DWORD_PTR)fn)(self, 0, klbr_cfh ? hh : 0, (DWORD)(DWORD_PTR)p, f5); ok = 1; }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) { if (++klbr_cf_flt >= 3) klog("brain: traitor coverfire: 3 faults: off for the round"); return; }
    if (!ok) return;
    klbr_cf_calls++;
    { float h0 = 0.0f; if (!klbr_cf_hp[ix].victim && klbr_hp_read(hp, &h0)) { klbr_cf_hp[ix].victim = hp; klbr_cf_hp[ix].hp0 = h0; klbr_cf_hp[ix].t0 = now; klbr_cf_hp[ix].g = g; klbr_cf_hp[ix].step = 0; } }
    if (klbr_cf_n < KLBR_CF_LOGMAX) {
        if (g > 0xffff) g1s = klh_rd32(g + 8); cur1 = klh_rd32(self + 0x74); klbr_cf_n++;
        {   /* wee6blb1x step 0 (read only): goal stack [s+4..s+8) top-runs, +0x88 mode, +0x6e8 (0x82cae0 branch) */
            DWORD sb = klh_rd32(self + 4), se = klh_rd32(self + 8), top = 0; long n = (sb > 0xffff && se >= sb) ? (long)((se - sb) / 4) : -1;
            if (n > 0 && n < 64) top = klh_rd32(se - 4);
            klog("brain: traitor coverfire: bot %d soldier %08lx -> %s at human %08lx handle %08lx (%.0f %.0f %.0f), holder flags %03lx; goal %08lx state %ld -> %ld; current goal %08lx -> %08lx%s; stack %ld top %08lx state %ld; +0x88 %ld +0x6e8 %08lx Idle state %ld",
                 ix, (unsigned long)self, klbr_cfh ? "ZAttackTarget" : "CoverFire", (unsigned long)hp, (unsigned long)(klbr_cfh ? hh : 0), (double)p[0], (double)p[1], (double)p[2], (unsigned long)hf, (unsigned long)g, (long)g0s, (long)g1s, (unsigned long)cur0, (unsigned long)cur1, cur1 == g ? " (it is current)" : "",
                 n, (unsigned long)top, top > 0xffff ? (long)klh_rd32(top + 8) : -1L, (long)klh_rd32(self + 0x88), (unsigned long)klh_rd32(self + 0x6e8), klh_rd32(self + 0x634) > 0xffff ? (long)klh_rd32(klh_rd32(self + 0x634) + 8) : -1L);
        }
    }
}
static void klbr_cf_pump(DWORD now)      /* game thread, depth 0 (klbr_pump) */
{
    int i;
    if (!klbr_cfon) return;
    for (i = 0; i < KLBR_MAX; i++) {
        DWORD v = klbr_cf_hp[i].victim, dt, g = klbr_cf_hp[i].g; float h1 = 0.0f, d;
        if (!v) continue;
        dt = now - klbr_cf_hp[i].t0;
        if (dt < (klbr_cf_hp[i].step ? 2000u : 300u)) continue;
        if (klh_pvt(v) != 0x00bb45f4u || !klbr_hp_read(v, &h1)) { klbr_cf_hp[i].victim = 0; continue; }
        d = kbr_hp_drop(klbr_cf_hp[i].hp0, h1);
        if (klbr_cf_hpn < KLBR_CF_HPLOGMAX) {
            klbr_cf_hpn++;
            klog("brain: traitor coverfire health: bot %d human %08lx (crew seat %d) hp %.1f -> %.1f, drop %.1f +%lu ms; goal %08lx state %ld",
                 i, (unsigned long)v, klud_idx(v), (double)klbr_cf_hp[i].hp0, (double)h1, (double)d, (unsigned long)dt, (unsigned long)g, g > 0xffff ? (long)klh_rd32(g + 8) : -1L);
        }
        if (klbr_cf_hp[i].step == 0) { klbr_cf_hp[i].step = 1; continue; }
        if (d > 0.0f) { klbr_cf_hpdrop++; klbr_cf_hpsum += d; } else klbr_cf_hpflat++;
        klbr_cf_hp[i].victim = 0;
    }
}
/* ---- OnlineBrainTraitorEntryFix (11-03, workflow w0bnwus0v trace + verifier; UNTESTED, recommended off; needs AttackHandle). For a ZFFPlayer target the ZAttackTarget tick 0x4f4460 captures the
   flags of the bot's known-list entry for the human (0x4f45d2) and tests them with 0x616480 at 0x4f4db1 (fail -> the goal ends); at 0x4f4ccd it copies them (| 1) into the holder. An entry made by
   0x425fa0 has flags 0. B = [s+0x698]: [B] count (max 10), entries at B+4 stride 0x14 {+0 flags, +4 entity pointer, +8 kind (2 = player), +0xc clock, +0x10 team object}. Slot 113's full update
   recomputes 0x4 / 0x10 / 0x20 / 0x40 / 0x2 only for entries with bit0 set and never sets 0x200 (stub 0x655a40), so we OR 0x11 and clear 0x244 after every slot-113 call while the marked bot's CURRENT
   goal is ZAttackTarget (vt 0xbd1104, state 0-2) on a human that 0x8ccde0 still resolves. Only the flags dword is written; no engine call except the pure lookup 0x8ccde0.
   Read-only child watch (with AttackHandle): counts slot-113 calls where the goal stack holds ZRunToPosShootingTask (vt 0xbd0ba4), the only task that shoots a human (via the HOLDER flags). */
#define KLBR_EF_ZAT_VT 0x00bd1104
#define KLBR_EF_RUN_VT 0x00bd0ba4
#define KLBR_EF_LOGMAX 12
static int klbr_efon, klbr_ef_n, klbr_ef_cn, klbr_ef_gn; static DWORD klbr_ef_lastt; static long klbr_ef_set, klbr_ef_keep, klbr_ef_miss, klbr_ef_stale, klbr_ef_child, klbr_ef_childh;
static void klbr_ef_apply(struct klbr_s *e, DWORD self)
{
    DWORD sb, se, g, gs, h, H = 0, B, cnt = 0, k; int ix;
    if (!klbr_cfh || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    sb = klh_rd32(self + 4); se = klh_rd32(self + 8);
    if (sb > 0xffff && se > sb && se - sb <= 64 * 4) {      /* child watch, read only */
        DWORD p;
        for (p = sb; p < se; p += 4) {
            DWORD t = klh_rd32(p);
            if (t > 0xffff && klh_pvt(t) == KLBR_EF_RUN_VT) {
                DWORD hp = klh_rd32(self + 0xac); int hum = hp > 0xffff && klh_pvt(hp) == 0x00bb45f4u && !klbr_hl_body(hp) && !klbr_hl_find(hp);
                klbr_ef_child++; if (hum) klbr_ef_childh++;
                if (klbr_ef_cn < KLBR_EF_LOGMAX) { klbr_ef_cn++; klog("brain: traitor entryfix: bot %d ZRunToPosShootingTask %08lx state %ld on the stack; holder %08lx flags %03lx%s", ix, (unsigned long)t, (long)klh_rd32(t + 8), (unsigned long)hp, (unsigned long)klh_rd32(self + 0xa8), hum ? " (a human)" : ""); }
                if (klbr_ef_gn < 6 && t != klbr_ef_lastt) {      /* one line per new child task */
                    klbr_ef_lastt = t;      /* bs26: EntryFix's gate never passed (all counts 0) while this ran at a human: dump the gate inputs, the stack and the B list once per run (read only) */
                    DWORD g2 = klh_rd32(self + 0x658), B2 = klh_rd32(self + 0x698), c2 = 0, q2, k2; char sbuf[400], bbuf[400]; int o = 0, ob = 0;
                    klbr_ef_gn++;
                    for (q2 = sb; q2 < se && o < 330; q2 += 4) { DWORD x = klh_rd32(q2); o += _snprintf(sbuf + o, sizeof sbuf - o, " %08lx/vt %08lx/st %ld", (unsigned long)x, (unsigned long)(x > 0xffff ? klh_pvt(x) : 0), x > 0xffff ? (long)klh_rd32(x + 8) : -1L); }
                    sbuf[o < (int)sizeof sbuf ? (o < 0 ? 0 : o) : (int)sizeof sbuf - 1] = 0;
                    if (B2 > 0xffff && klh_rd(B2, &c2, 4) && c2 <= 10)
                        for (k2 = 0; k2 < c2 && ob < 330; k2++) { q2 = B2 + 4 + 0x14 * k2; ob += _snprintf(bbuf + ob, sizeof bbuf - ob, " [%lu] fl %03lx ent %08lx kind %ld", (unsigned long)k2, (unsigned long)klh_rd32(q2), (unsigned long)klh_rd32(q2 + 4), (long)klh_rd32(q2 + 8)); }
                    bbuf[ob < (int)sizeof bbuf ? (ob < 0 ? 0 : ob) : (int)sizeof bbuf - 1] = 0;
                    klog("brain: traitor entryfix gate: bot %d +0x658 %08lx vt %08lx state %ld handle %08lx; current goal %08lx; stack%s; B %08lx count %lu:%s", ix, (unsigned long)g2,
                         (unsigned long)(g2 > 0xffff ? klh_pvt(g2) : 0), g2 > 0xffff ? (long)klh_rd32(g2 + 8) : -1L, (unsigned long)(g2 > 0xffff ? klh_rd32(g2 + 0x14) : 0), (unsigned long)klh_rd32(self + 0x74), sbuf, (unsigned long)B2, (unsigned long)c2, bbuf);
                }
                break;
            }
        }
    }
    if (!klbr_efon) return;
    if ((g = klh_rd32(self + 0x658)) <= 0xffff || klh_pvt(g) != KLBR_EF_ZAT_VT || klh_rd32(self + 0x74) != g || (gs = klh_rd32(g + 8)) > 2 || !(h = klh_rd32(g + 0x14))) return;
    __try { H = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { H = 0; }
    if (H <= 0xffff) { klbr_ef_stale++; return; }      /* the tick would AV at 0x4f44a7: counted, nothing written (GUESS: no safe way found yet to end the goal from here) */
    if (klh_pvt(H) != 0x00bb45f4u || klbr_hl_body(H) || klbr_hl_find(H)) return;
    if ((B = klh_rd32(self + 0x698)) <= 0xffff || !klh_rd(B, &cnt, 4) || cnt > 10) return;
    for (k = 0; k < cnt; k++) {
        DWORD q = B + 4 + 0x14 * k, fl, nf;
        if (klh_rd32(q + 4) != H || klh_rd32(q + 8) != 2) continue;
        fl = klh_rd32(q); nf = (fl | 0x11ul) & ~0x244ul;
        if (nf == fl) { klbr_ef_keep++; return; }
        __try { KLBR_P32(q) = nf; } __except (EXCEPTION_EXECUTE_HANDLER) { return; }
        klbr_ef_set++;
        if (klbr_ef_n < KLBR_EF_LOGMAX) { klbr_ef_n++; klog("brain: traitor entryfix: bot %d entry %lu of %lu for human %08lx: flags %03lx -> %03lx; ZAttackTarget %08lx state %ld; holder %08lx flags %03lx", ix, (unsigned long)k, (unsigned long)cnt, (unsigned long)H, (unsigned long)fl, (unsigned long)nf, (unsigned long)g, (long)gs, (unsigned long)klh_rd32(self + 0xac), (unsigned long)klh_rd32(self + 0xa8)); }
        return;
    }
    klbr_ef_miss++;
}
/* w4em63f8z review: the arbiter has no empty-list check (0x81ebe6-0x81ec11 reads [begin] even when begin == end, then pushes it), so before switching we need Idle's entry in the list
   [s+0x48..s+0x4c) (stride 0x10, goal at +0; vt+0x1b4 only drops prio-0x96 entries of 11 slots, not Idle +0x634) and, after the drop, no entry left for g. Returns 1 when it switched. */
static int klbr_rs_inlist(DWORD self, DWORD goal)
{
    DWORD b = klh_rd32(self + 0x48), en = klh_rd32(self + 0x4c), q;
    if (b <= 0xffff || en <= b || en - b > 0x10 * 64) return 0;
    for (q = b; q < en; q += 0x10) if (klh_rd32(q) == goal) return 1;
    return 0;
}
static int klbr_rs_toidle(DWORD self, DWORD g)
{
    DWORD vt, fn, idle = klh_rd32(self + 0x634);
    if ((vt = klh_rd32(self)) <= 0xffff || (fn = klh_rd32(vt + 0x1b4)) != (DWORD)(DWORD_PTR)KLH_VA(KLBR_RS_DROP96)) return 0;
    if (idle <= 0xffff || !klbr_rs_inlist(self, idle)) return 0;
    __try {
        ((klbr_rs0fn)(DWORD_PTR)fn)(self, 0);
        if (klbr_rs_inlist(self, g) || !klbr_rs_inlist(self, idle)) return 0;      /* [s+0x74] untouched: no switch */
        KLBR_P32(self + 0x74) = 0;
        ((klbr_rs1fn)(DWORD_PTR)KLH_VA(KLBR_RS_ARB))(self, 0, 1);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) { if (++klbr_rs_flt >= 3) klog("brain: traitor restart: 3 faults: off for the round"); return 0; }
    return 1;
}
static long klbr_rs_abort;
static void klbr_rs_apply(struct klbr_s *e, DWORD self)      /* OnlineBrainTraitorRestart unfreeze (see above); game thread, after the slot-113 call */
{
    DWORD g, gs, sb, se, top = 0; int ix;
    if (!klbr_rson || klbr_rs_flt >= 3 || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    if ((g = klh_rd32(self + 0x658)) <= 0xffff || klh_pvt(g) != KLBR_EF_ZAT_VT || klh_rd32(self + 0x74) != g) return;
    sb = klh_rd32(self + 4); se = klh_rd32(self + 8); gs = klh_rd32(g + 8);
    if (gs >= 1 && gs <= 3) {      /* w4em63f8z: a restarted goal is live most of the time; if its human handle went stale the tick AVs at 0x4f44a7, so switch to Idle (the arbiter pops it into the
                                      abort queue 0x5ca0b0; that abort mode skips the tick body is a GUESS) */
        DWORD h = klh_rd32(g + 0x14), H = 0;
        if (!h) return;
        __try { H = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { H = 0; }
        if (H > 0xffff) return;
        if (!klbr_rs_toidle(self, g)) { klbr_rs_unfskip++; return; }
        klbr_rs_abort++;
        if (klbr_rs_n < KLBR_RS_LOGMAX) { klbr_rs_n++; klog("brain: traitor restart: bot %d ZAttackTarget %08lx state %ld lost its target (handle %08lx stale): switched to Idle, current goal now %08lx", ix, (unsigned long)g, (long)gs, (unsigned long)h, (unsigned long)klh_rd32(self + 0x74)); }
        return;
    }
    if (gs != 4 || sb <= 0xffff || se != sb) return;      /* only the frozen case: no goal on the stack (a just-pushed g is still on it until the scheduler runs) */
    if (!klbr_rs_toidle(self, g)) { klbr_rs_unfskip++; return; }
    klbr_rs_unf++;
    sb = klh_rd32(self + 4); se = klh_rd32(self + 8); if (sb > 0xffff && se > sb && se - sb <= 64 * 4) top = klh_rd32(se - 4);
    if (klbr_rs_n < KLBR_RS_LOGMAX) {
        klbr_rs_n++;
        klog("brain: traitor restart: bot %d unfrozen: ZAttackTarget %08lx done, current goal now %08lx, stack %ld top %08lx (Idle %08lx state %ld)", ix, (unsigned long)g, (unsigned long)klh_rd32(self + 0x74),
             (sb > 0xffff && se >= sb) ? (long)((se - sb) / 4) : -1L, (unsigned long)top, (unsigned long)klh_rd32(self + 0x634), klh_rd32(self + 0x634) > 0xffff ? (long)klh_rd32(klh_rd32(self + 0x634) + 8) : -1L);
    }
}
static DWORD __fastcall klbr_w_fl113(DWORD self, DWORD edx, DWORD a1)      /* thiscall + 1 stack arg, ret 4 */
{
    klbr_fl113fn org = (klbr_fl113fn)(DWORD_PTR)klbr_tfl_org113; DWORD r = 0; int sw = 0, m, flt = 0; struct klbr_s *e;
    (void)edx;
    if (!org) return 0;
    if (!(m = klbr_tfl_begin(self, &sw, &e))) return org(self, 0, a1);
    if (!sw) r = org(self, 0, a1);      /* log only / not swapped: state-neutral, no SEH, no shared fault count */
    else {
        __try { r = org(self, 0, a1); }
        __except (EXCEPTION_EXECUTE_HANDLER) { flt = 1; }      /* GUESS: x87 stack left as is after a fault (no _fpreset: it would also reset the game's control word) */
    }
    if (klbr_tfl_end(self, sw, flt, KLBR_TFL_S113)) return 0;
    klbr_hx_apply(e, self);      /* OnlineBrainTraitorHolderFix: after the swap is out, so the engine's own holder write stands and only our bits change */
    klbr_ef_apply(e, self);      /* OnlineBrainTraitorEntryFix + the read-only child watch: after the full update recomputed the entries */
    klbr_tb_apply(e, self);     /* OnlineBrainTraitorTraitorByte: the bot's own traitor byte, before the probe so the probe shows the live value */
    klbr_fp_apply(e, self);     /* OnlineBrainTraitorFireProbe (read only): sees the stack as the scheduler left it, before our own order below */
    klbr_cf_apply(e, self);     /* OnlineBrainTraitorCoverFire: after HolderFix, so it sees the fixed flags */
    klbr_rs_apply(e, self);     /* OnlineBrainTraitorRestart unfreeze: after the call, so a goal it just pushed is still on the stack and is left alone */
    klbr_tfl_log(e, self, 0, m, r);
    return r;
}
static DWORD __fastcall klbr_w_fl114(DWORD self, DWORD edx, DWORD a1, DWORD a2, DWORD a3, DWORD a4)      /* thiscall + 4 stack args (2 dwords, 2 floats), ret 0x10, int in eax */
{
    klbr_fl114fn org = (klbr_fl114fn)(DWORD_PTR)klbr_tfl_org114; DWORD r = 0; int sw = 0, m, flt = 0; struct klbr_s *e;
    (void)edx;
    if (!org) return 0;
    if (!(m = klbr_tfl_begin(self, &sw, &e))) return org(self, 0, a1, a2, a3, a4);
    if (!sw) r = org(self, 0, a1, a2, a3, a4);      /* log only / not swapped: state-neutral, no SEH, no shared fault count */
    else {
        __try { r = org(self, 0, a1, a2, a3, a4); }
        __except (EXCEPTION_EXECUTE_HANDLER) { flt = 1; }      /* GUESS: x87 stack left as is after a fault (slot 114 uses fld/fstp); no _fpreset, it would also reset the game's control word */
    }
    if (klbr_tfl_end(self, sw, flt, KLBR_TFL_S114)) return 0;      /* GUESS: 0 = no candidate (0x51d6c0 initialises its result to 0) */
    klbr_tfl_log(e, self, 1, m, r);
    return r;
}
/* ---- HitLog part A.4 (2026-11-03, w9ady1fn9; READ ONLY): ZSoldier slot 83 = Attack 0x831850 (vt + 0x14c, verified: the table dword at 0xbd0aa0) on the SAME private table, log only.
   thiscall (handle, pos *, float), ret 0xc; the return value is passed through (GUESS: none is used). Only a nonzero handle sets the ZAttackTarget goal [[soldier+0x658]+0x14] (0x8318e8), and only
   while [[soldier+0x5ac]+8] is 0 or 4; the five static callers (0x907c46 leap-frog, 0x59b9a7, 0x60ff69 ambush, 0x748e8e follow, 0x49a676) all pass handle 0 = a POSITION goal. Logged per
   marked bot: handle, the return address (which caller), the position, the state, the goal handle before / after, [soldier+0x720]. 12 lines per bot per round. */
#define KLBR_ATK_SLOT 83
#define KLBR_ATK_ORG 0x00831850
#define KLBR_ATK_LOGMAX 12
static DWORD klbr_atk_org; static int klbr_atk_n[KLBR_MAX]; static long klbr_atk_calls[KLBR_MAX], klbr_atk_nz[KLBR_MAX];
typedef DWORD (__fastcall *klbr_atkfn)(DWORD, DWORD, DWORD, DWORD, DWORD);
static DWORD __fastcall klbr_w_atk(DWORD self, DWORD edx, DWORD h, DWORD pos, DWORD f)      /* thiscall + 3 stack args, ret 0xc */
{
    klbr_atkfn org = (klbr_atkfn)(DWORD_PTR)klbr_atk_org; DWORD r, ra = (DWORD)(DWORD_PTR)_ReturnAddress(), g = 0, gh0 = 0, gh1 = 0, s5 = 0, st = 0xffffffff; float p[3] = { 0, 0, 0 }; struct klbr_s *e = 0; int ix = -1;
    (void)edx;
    if (!org) return 0;
    if (klbr_hlon && GetCurrentThreadId() == klbr_game_tid && (e = klbr_find(self)) != 0 && e->state == 1 && e->traitor) {
        ix = (int)(e - klbr_t);
        if ((g = klh_rd32(self + 0x658)) > 0xffff) gh0 = klh_rd32(g + 0x14);
        if ((s5 = klh_rd32(self + 0x5ac)) > 0xffff) st = klh_rd32(s5 + 8);
        if (pos > 0xffff) klh_rd(pos, p, 12);
    }
    r = org(self, 0, h, pos, f);
    if (ix >= 0 && ix < KLBR_MAX) {
        klbr_atk_calls[ix]++; if (h) klbr_atk_nz[ix]++;
        if (klbr_atk_n[ix] < KLBR_ATK_LOGMAX) {
            DWORD p720 = klh_rd32(self + 0x720); int pl = p720 > 0xffff && klh_pvt(p720) == 0x00bb45f4u;
            klbr_atk_n[ix]++; if (g > 0xffff) gh1 = klh_rd32(g + 0x14);
            klog("brain: traitor attack: bot %d soldier %08lx Attack(handle %08lx, pos %.0f %.0f %.0f) from %08lx; state [[+0x5ac]+8] %ld (goal set only at 0 / 4); goal %08lx handle %08lx -> %08lx; +0x720 %08lx%s",
                 ix, (unsigned long)self, (unsigned long)h, (double)p[0], (double)p[1], (double)p[2], (unsigned long)(ra - (DWORD)klh_delta), (long)st, (unsigned long)g, (unsigned long)gh0, (unsigned long)gh1,
                 (unsigned long)p720, pl ? " (a ZFFPlayer)" : "");
        }
    }
    return r;
}
/* ---- OnlineBrainTraitorHumanFirst (2026-11-03, waeaosjjr; UNTESTED, recommended off): ZSoldier slot 110 = 0x7ffd20 (vt + 0x1b8) scores type-1 (police) entries of the known list, slot 111 the humans.
   0x767510 keeps the STRICT maximum (start -1e38, no threshold), and the human score falls 0.09 per cm past 4 m (bs18: -500..-800 at range) while a near / locked cop scores up to +10000, so the
   marked bot never picks a human. With this on, for a MARKED bot only, slot 110 still runs (it stores [cand+0x71c]) but returns the 'no target' float while its list B holds a ZFFPlayer entry
   with bit0 (seen) and 0x10 (in range) set: the human is then the only finite score and 0x8bd420 holds it. Cops are scored normally again as soon as no such human is in B.
   GUESS: slot 110 has the same 7-arg / ret 0x1c shape as slot 111 (read by the workflow from the call sites 0x767a6a-0x767bfc, not checked live). Table dword checked against 0x7ffd20 first. */
#define KLBR_HF_SLOT 110
#define KLBR_HF_ORG 0x007ffd20
static int klbr_hfon; static DWORD klbr_hf_org; static long klbr_hf_null, klbr_hf_pass;
static int klbr_hf_human_in_b(DWORD self)
{
    DWORD B = klh_rd32(self + 0x698), cnt = 0, k;
    if (B <= 0xffff || !klh_rd(B, &cnt, 4) || cnt > 16) return 0;
    for (k = 0; k < cnt; k++) { DWORD q = B + 4 + 0x14 * k, fl = klh_rd32(q), ent = klh_rd32(q + 4); if ((fl & 0x11) == 0x11 && ent > 0xffff && klh_pvt(ent) == 0x00bb45f4u && !klbr_hl_body(ent)) return 1; }      /* bs22: a tagged bot's body is a ZFFPlayer too: humans only */
    return 0;
}
static float __fastcall klbr_w_cop(DWORD self, DWORD edx, DWORD a1, DWORD a2, DWORD a3, DWORD a4, DWORD a5, DWORD a6, DWORD a7)      /* thiscall + 7 stack args, ret 0x1c (GUESS, see above) */
{
    klbr_scfn org = (klbr_scfn)(DWORD_PTR)klbr_hf_org; float r; struct klbr_s *e;
    (void)edx;
    if (!org) return 0.0f;
    r = org(self, 0, a1, a2, a3, a4, a5, a6, a7);
    if (klbr_hfon && !klbr_ta_dis && GetCurrentThreadId() == klbr_game_tid && (e = klbr_find(self)) != 0 && e->state == 1 && e->traitor) {
        if (klbr_hf_human_in_b(self)) { float nt = 0.0f; if (klh_rd((DWORD_PTR)KLH_VA(KLBR_TA_NOTARGET), &nt, 4)) { klbr_hf_null++; return nt; } }
        klbr_hf_pass++;
    }
    return r;
}
/* ---- OnlineBrainTraitorHitLog (2026-11-03; READ ONLY): does a marked bot really DAMAGE humans? Observation point = the rules' damage hook (slot 15, klucc_down.c's klud_w15: victim, float *delta, attacker),
   the same call OnlinePreScale and DownOnly use; klucc_down.c calls klbr_hitlog FIRST, before any other filter prices the delta. No new patch, nothing is written, no game call is made (klh_rd / class reads only).
   A hit = delta < 0 (damage = -delta, pre-apply). Attacker bot = a tagged soldier of klbr_t (state 1) matched by its actor OR its soldier pointer (GUESS: the attacker argument of slot 15 is the ZFFActor; the
   soldier match is a fallback). Victim human = ZFFPlayer (klh_pvt, also NetSmooth's private copy). Marked = e->traitor at the moment of the hit. Hits by a ZFFActor / ZSoldier attacker that klbr_t does
   not know are counted apart (unk) so a wrong attacker GUESS shows in the log instead of as a silent zero. Printed at the round end by klbr_summary. */
static int klud_idx(DWORD p);      /* klucc_down.c (included after this file): the crew index of a player, -1 none */
static volatile LONG klbr_hl_s15;      /* entries of the slot-15 wrapper that reached klbr_hitlog (non-null victim / delta / attacker) this round: proves or refutes 'slot 15 was reached' */
#define KLBR_HL_PROBE_MAX 120          /* target lines per round (all bots; rate-limited per bot, see klbr_hl_pump) */
static struct { int mh, uh, mb, ub, unk, pl, nlog, nplog; float md, ud; DWORD t0;
    int tn[KLBR_MAX]; int tlog, plog, hlog, dmlog; DWORD tat[KLBR_MAX]; unsigned long pkey;      /* probe: logged target lines, rules-probe lines, health lines, OnlineBrainTraitorDamage set lines; last target-line tick per bot; last rules-probe key (0 = none yet) */
    struct { DWORD victim; float hp0, att; DWORD t0; int step, seat; } hp[5];      /* pending health reads after a counted marked hit on a human (step 0: next pump tick, 1: after 500 ms) */
} klbr_hl;
/* OnlineBrainTraitorDamage (indexed like klbr_t): body = the marked bot's ZFFPlayer body (also a cache of the last body klbr_hl_body matched to that bot), set = we raised its +0x2726 byte, rec = crew seat it must still have, old = the byte before we wrote 1.
   set: we wrote 1 (old = what was there); rec: the shadow record = crew seat the body must still have when we write back. */
static struct { DWORD body; int set, rec; BYTE old; } klbr_dm[KLBR_MAX];
static struct klbr_s *klbr_hl_find(DWORD o)
{
    int i;
    if (o < 0x10000) return 0;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && (klbr_t[i].actor == o || klbr_t[i].snd == o)) return &klbr_t[i];
    return 0;
}
/* slot 15 treats attacker and victim as crew ZFFPlayer bodies (disassembly 0x425320: class-mask test, [body+0x2748] -> crew index), so a bot arrives as its player body, not its actor / soldier.
   GUESS (not traced): a tagged bot's crew seat equals its shadow record e->rec (the money rows at score+0x150+4*rec are indexed by crew seat). A wrong guess shows as the 'pl' counter + seat log. */
static struct klbr_s *klbr_hl_body(DWORD body)
{
    int i, seat;
    if (klh_pvt(body) != 0x00bb45f4u || (seat = klud_idx(body)) <= 0) return 0;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && klbr_t[i].rec == seat) { if (!klbr_dm[i].set) klbr_dm[i].body = body; return &klbr_t[i]; }      /* remember the body of this bot: the probe reads its bytes, OnlineBrainTraitorDamage restores it */
    return 0;
}
static int klbr_hp_read(DWORD pl, float *hp)      /* a player's health: health object [pl+0xa48], float at +4 (kldown.c / klucc_down.c) */
{
    DWORD ho = klh_rd32(pl + 0xa48);
    return ho > 0xffff && klh_rd(ho + 4, hp, 4) && *hp == *hp;
}
static void klbr_hitlog(DWORD victim, float *pdelta, DWORD attacker)
{
    float d = 0.0f; struct klbr_s *a, *v; int human, marked; DWORD now;
    if (klbr_hlon) InterlockedIncrement(&klbr_hl_s15);
    if (!klbr_game_tid || GetCurrentThreadId() != klbr_game_tid) return;      /* klbr_t / klbr_hl are game-thread data */
    if (!klbr_hlon || victim < 0x10000 || attacker < 0x10000 || attacker == victim) return;
    if (!klh_rd((DWORD_PTR)pdelta, &d, 4) || !(d < 0.0f)) return;      /* a heal, a zero or a NaN is no hit */
    v = klbr_hl_find(victim); if (!v) v = klbr_hl_body(victim);
    human = !v && klh_pvt(victim) == 0x00bb45f4u;
    if (!human && !v) return;      /* neither a human nor a tagged bot: not counted */
    a = klbr_hl_find(attacker); if (!a) a = klbr_hl_body(attacker);
    if (!a) {
        if (human && klh_pvt(attacker) == 0x00bb45f4u) {
            klbr_hl.pl++;
            if (klbr_hl.nplog < 5) { klbr_hl.nplog++; klog("brain: traitor hit: player-body attacker %08lx (crew seat %d) on human %08lx matches no tagged bot (rec of bots: see 'brain: traitor:' lines)", (unsigned long)attacker, klud_idx(attacker), (unsigned long)victim); }
        } else if (human && (klh_avt(attacker) == 0x00bb3bacu || klh_svt(attacker) == 0x00bd0954u)) klbr_hl.unk++;
        return;
    }
    marked = a->traitor != 0; now = GetTickCount();
    if (!klbr_hl.t0) klbr_hl.t0 = now;
    if (human) {
        if (marked) {
            klbr_hl.mh++; klbr_hl.md -= d;
            if (klbr_hl.hlog < 8) {      /* A.3: the victim's health on the next pump tick and after 500 ms (attempted vs landed) */
                int k; float h0 = 0.0f;
                for (k = 0; k < 5; k++) if (!klbr_hl.hp[k].victim) {
                    if (klbr_hp_read(victim, &h0)) { klbr_hl.hp[k].victim = victim; klbr_hl.hp[k].hp0 = h0; klbr_hl.hp[k].att = -d; klbr_hl.hp[k].t0 = now; klbr_hl.hp[k].step = 0; klbr_hl.hp[k].seat = klud_idx(victim); }
                    break;
                }
            }
            if (klbr_hl.nlog < 5) { klbr_hl.nlog++; klog("brain: traitor hit %d: t=%.1f s bot %d (soldier %08lx actor %08lx) hit human %08lx (crew seat %d) for %.1f", klbr_hl.nlog, (now - klbr_hl.t0) / 1000.0, (int)(a - klbr_t), (unsigned long)a->snd, (unsigned long)a->actor, (unsigned long)victim, klud_idx(victim), (double)-d); }
        } else { klbr_hl.uh++; klbr_hl.ud -= d; }
    } else if (marked) klbr_hl.mb++;
    else klbr_hl.ub++;
}
static void klbr_hitlog_summary(void)
{
    if (klbr_hlon) {
        klog("brain: traitor hits: slot-15 wrapper entries this round: %ld (0 = the rules' damage hook was never reached on this machine)", (long)klbr_hl_s15);
        klog("brain: traitor hits: ATTEMPTED (counted before the game's own self / team filters, so an upper bound): marked %d (dmg %.1f) on humans, unmarked %d (dmg %.1f) on humans, marked %d on bots", klbr_hl.mh, (double)klbr_hl.md, klbr_hl.uh, (double)klbr_hl.ud, klbr_hl.mb);
        if (klbr_hl.unk || klbr_hl.ub || klbr_hl.pl) klog("brain: traitor hits: (not in the line above) %d hit(s) on humans by an actor / soldier klbr_t does not tag, %d by a player body matching no tagged bot (seat GUESS check), %d unmarked-bot hit(s) on bots", klbr_hl.unk, klbr_hl.pl, klbr_hl.ub);
    }
    if (klbr_hlon) { int j; for (j = 0; j < KLBR_MAX; j++) if (klbr_atk_calls[j]) klog("brain: traitor attack: bot %d round total: Attack (slot 83) called %ld time(s), %ld with a nonzero handle", j, klbr_atk_calls[j], klbr_atk_nz[j]); }
    if (klbr_hfon) klog("brain: traitor humanfirst: round total: police scores nulled %ld (a seen human was in the list), passed %ld", klbr_hf_null, klbr_hf_pass);
    if (klbr_hoon) klog("brain: traitor humanonly: round total: ally-bot scores nulled %ld (a seen human was in the list), other ZFFPlayer candidates passed %ld", klbr_ho_null, klbr_ho_pass);
    if (klbr_cfon) klog("brain: traitor coverfire: round total: CoverFire calls %ld, skipped (busy / stale) %ld, stale handle %ld, faults %d; holder health 2 s later: dropped %ld (total %.1f), flat %ld", klbr_cf_calls, klbr_cf_skip, klbr_cf_stale, klbr_cf_flt, klbr_cf_hpdrop, klbr_cf_hpsum, klbr_cf_hpflat);
    if (klbr_cfh) klog("brain: traitor entryfix: round total: entry flags set %ld, already set %ld, no entry %ld, stale target handle under a live goal %ld; ZRunToPosShootingTask seen on %ld slot-113 calls (%ld with a human holder)%s",
                       klbr_ef_set, klbr_ef_keep, klbr_ef_miss, klbr_ef_stale, klbr_ef_child, klbr_ef_childh, klbr_efon ? "" : " (EntryFix off: watch only)");
    klbr_ef_set = klbr_ef_keep = klbr_ef_miss = klbr_ef_stale = klbr_ef_child = klbr_ef_childh = 0; klbr_ef_n = klbr_ef_cn = klbr_ef_gn = 0;
    if (klbr_rson) klog("brain: traitor restart: round total: current goal cleared before the call %ld, unfrozen %ld, aborted on a stale target %ld, switch skipped (vt+0x1b4 not 0x6e49b0 / no Idle entry / g entry left) %ld, faults %d", klbr_rs_clr, klbr_rs_unf, klbr_rs_abort, klbr_rs_unfskip, klbr_rs_flt);
    klbr_rs_clr = klbr_rs_unf = klbr_rs_abort = klbr_rs_unfskip = 0; klbr_rs_n = klbr_rs_flt = 0;
    klbr_fp_summary();
    if (klbr_hxon) klog("brain: traitor holderfix: round total: human holder flags fixed in range (0x4 cleared, 0x10 set) %ld, out of range / range unknown (0x4 cleared only) %ld, range faults %ld", klbr_hx_set, klbr_hx_far, klbr_hx_flt);
    klbr_hf_null = klbr_hf_pass = 0; klbr_hx_set = klbr_hx_far = 0; klbr_ho_null = klbr_ho_pass = 0; klbr_cf_calls = klbr_cf_skip = klbr_cf_stale = 0; klbr_cf_flt = klbr_cf_n = 0; memset(klbr_cf_at, 0, sizeof klbr_cf_at);
    memset(klbr_cf_hp, 0, sizeof klbr_cf_hp); klbr_cf_hpn = 0; klbr_cf_hpdrop = klbr_cf_hpflat = 0; klbr_cf_hpsum = 0.0;
    memset(klbr_atk_n, 0, sizeof klbr_atk_n); memset(klbr_atk_calls, 0, sizeof klbr_atk_calls); memset(klbr_atk_nz, 0, sizeof klbr_atk_nz);
    memset(&klbr_hl, 0, sizeof klbr_hl); klbr_hl_s15 = 0;
}
/* ---- HitLog probe (A.1 / A.2 / A.3), READ ONLY, game thread at depth 0 (called from klbr_pump) -------------------------------------------------------------------------------------------------
   A.1 once per second per marked bot: its current target. GUESS (read from 0x882470 / 0x5da810, not traced live): the soldier's current target is [soldier+0x708] while the game clock
   [[0xdd2640]+0x48] < [soldier+0x70c] (0x5da810 = the 'current target' getter slot 111 compares its candidate with at 0x882542); the target is a ZFFPlayer body (the candidate type) or, for a cop, an
   actor / soldier. Class: human = ZFFPlayer body that is no tagged bot's body and has police byte +0x2723 == 0; GUESS: a ZFFPlayer with +0x2723 != 0 or a non-player AI object is a cop.
   The bot's own player body is only known once klbr_hl_body matched it (a hit, or the bot's slot-111 candidate list) - GUESS mapping crew seat == shadow rec - until then the bytes print -1.
   A.2 rules byte +0x285 ('looting started', re/fireline_goal_path_1103.md D step 4; GUESS it is that byte of the REAL rules object [[0x168e9e4]+0x54]) and the gate [[0x168e9e4]+0x58] that lets
   0x83ad70 forward to slot 15, on change; also whether the rules' vtable slot 15 is our wrapper. A.3 health before / after a counted marked hit on a human. ---- */
static DWORD __fastcall klud_w15(void *self, void *edx, DWORD victim, float *pdelta, DWORD attacker);      /* klucc_down.c (included after this file) */
static void klbr_hl_pump(DWORD now)
{
    DWORD sm = 0, role = 0, mode = 0, state = 0, G, rules = 0, vt = 0, s15 = 0, clk = 0, obj; BYTE b285 = 0xff, gate8 = 0; int i, k, rok; unsigned long key;
    if (!klbr_hlon) return;
    rok = (sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) && sm == klbr_sm_round && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4) && role == 2 && mode == 4 && state == KLB_ROUND;
    if (!rok) return;
    G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G));
    if (G > 0xffff) { klh_rd(G + 0x58, &gate8, 1);      /* the game tests ONE byte: cmp byte ptr [ecx+0x58],0 at 0x83ad70 */ rules = klh_rd32(G + 0x54); }
    if (rules > 0xffff) { klh_rd(rules + 0x285, &b285, 1); if ((vt = klh_rd32(rules)) > 0xffff) s15 = klh_rd32(vt + 0x3c); }
    key = (unsigned long)b285 | (gate8 ? 0x100ul : 0ul) | (s15 == (DWORD)(DWORD_PTR)klud_w15 ? 0x200ul : 0ul) | 0x10000ul;
    if (key != klbr_hl.pkey && klbr_hl.plog < 20) {      /* A.2: once per round and on every change (the +0x285 flip = the first loot event) */
        klbr_hl.pkey = key; klbr_hl.plog++;
        klog("brain: traitor probe: rules %08lx looting-started byte +0x285 = %d (255 = unreadable); slot-15 gate byte [[0x168e9e4]+0x58] = %02x (%s); rules vtable %08lx slot 15 = %08lx (%s); slot-15 wrapper entries so far %ld",
             (unsigned long)rules, (int)b285, (unsigned long)gate8, gate8 ? "set: 0x83ad70 forwards to slot 15" : "ZERO: 0x83ad70 returns before slot 15, the wrapper cannot run", (unsigned long)vt, (unsigned long)s15,
             s15 == (DWORD)(DWORD_PTR)klud_w15 ? "OUR wrapper" : s15 ? "not our wrapper" : "unreadable", (long)klbr_hl_s15);
    }
    obj = klh_rd32((DWORD_PTR)KLH_VA(0xdd2640)); if (obj > 0xffff) klh_rd(obj + 0x48, &clk, 4);
    for (i = 0; i < KLBR_MAX; i++) {      /* A.1 */
        struct klbr_s *e = &klbr_t[i]; DWORD tgt = 0, stamp = 0, body; float bp[3], tp[3]; int alive = 0, have, player, ai, cls, tagged, bok, b23 = -1, b26 = -1; BYTE pol = 0, x = 0; double dist = -1.0;
        if (e->state != 1 || !e->traitor || !e->snd) continue;
        if (klbr_hl.tlog >= KLBR_HL_PROBE_MAX) break;
        if (!kbr_rate_ok(klbr_hl.tat[i], now, klbr_hl.tn[i] < 10 ? 1000ul : 5000ul)) continue;      /* per bot: 1 line/s for its first 10, then 1 per 5 s, so later phases (after the first loot event) still get lines */
        klbr_hl.tat[i] = now | 1u; klbr_hl.tn[i]++; klbr_hl.tlog++;
        klh_rd(e->snd + 0x708, &tgt, 4); klh_rd(e->snd + 0x70c, &stamp, 4);
        have = obj > 0xffff && tgt > 0xffff && kbr_tgt_valid((long)clk, (long)stamp);
        player = have && klh_pvt(tgt) == 0x00bb45f4u;
        tagged = have && (klbr_hl_body(tgt) != 0 || klbr_hl_find(tgt) != 0);
        ai = have && !player && (klh_avt(tgt) == 0x00bb3bacu || klh_svt(tgt) == 0x00bd0954u);
        if (player) klh_rd(tgt + 0x2723, &pol, 1);
        cls = kbr_tgt_class(have, player, tagged, pol != 0, ai);
        if (have && klbr_bot_pos(e->actor, bp, &alive) && klh_rd(tgt + 0x460, tp, 12) && kle_ok3(tp)) dist = kle_dist(bp, tp) / 100;
        body = klbr_dm[i].body; bok = body > 0xffff && klh_pvt(body) == 0x00bb45f4u && klud_idx(body) == e->rec;
        if (bok) { if (klh_rd(body + 0x2723, &x, 1)) b23 = x; if (klh_rd(body + 0x2726, &x, 1)) b26 = x; }
        klog("brain: traitor target: bot %d (soldier %08lx, rec %d) last aggressor %08lx (raw %08lx) class %s dist %.1f m (clock %ld stamp %ld valid %d); own body %08lx +0x2723 %d +0x2726 %d (-1 = body unknown / unreadable)",
             i, (unsigned long)e->snd, e->rec, (unsigned long)(have ? tgt : 0), (unsigned long)tgt, kbr_tgt_name(cls), dist, (long)clk, (long)stamp, have, (unsigned long)(bok ? body : 0), b23, b26);
        {   /* wwr26esf3 (capstone, 11-03): +0x708/+0x70c is the LAST AGGRESSOR (0x506f50), not the selection. 0x767510 (entered via thunk 0x47a0f0, edi = B = [soldier+0x698])
               stores its pick with 0x8bd420 at 0x767eee into the holder H = [B+0x154]+0xa8 (= soldier+0xa8 if [B+0x154] == soldier): +0 flags, +4 entity ptr (GUESS, only +8 is
               confirmed by cmp [H+8],0 at 0x767555), +8 handle, soldier+0xbc entry time; 0x767f77 clears it when nothing wins. [soldier+0x658] = ZAttackTarget goal (ctor 0x6ab81b),
               fires on its own handle [goal+0x14], set by Attack slot 83 0x831850 only when [[soldier+0x5ac]+8] is 0 or 4. B+0x180 rescan time, +0x184 force flag, +0x18c hold time. */
            DWORD B = klh_rd32(e->snd + 0x698), so = B > 0xffff ? klh_rd32(B + 0x154) : 0, hf = 0, hp = 0, hh = 0, ht = 0, g = 0, gh = 0, s5ac = 0, st = 0xffffffff, b180 = 0, b184 = 0, b18c = 0;
            int hpl, htag, hai, hcls; BYTE hpol = 0;
            if (so > 0xffff) { hf = klh_rd32(so + 0xa8); hp = klh_rd32(so + 0xac); hh = klh_rd32(so + 0xb0); ht = klh_rd32(so + 0xbc); }
            if ((g = klh_rd32(e->snd + 0x658)) > 0xffff) gh = klh_rd32(g + 0x14);
            if ((s5ac = klh_rd32(e->snd + 0x5ac)) > 0xffff) st = klh_rd32(s5ac + 8);
            if (B > 0xffff) { b180 = klh_rd32(B + 0x180); b184 = klh_rd32(B + 0x184); b18c = klh_rd32(B + 0x18c); }
            hpl = hp > 0xffff && klh_pvt(hp) == 0x00bb45f4u;
            htag = hp > 0xffff && (klbr_hl_body(hp) != 0 || klbr_hl_find(hp) != 0);
            hai = hp > 0xffff && !hpl && (klh_avt(hp) == 0x00bb3bacu || klh_svt(hp) == 0x00bd0954u);
            if (hpl) klh_rd(hp + 0x2723, &hpol, 1);
            hcls = kbr_tgt_class(hp > 0xffff, hpl, htag, hpol != 0, hai);
            klog("brain: traitor target: bot %d HOLDER (B %08lx, [B+0x154] %08lx %s soldier) flags %08lx ptr %08lx class %s handle %08lx entry %ld; goal %08lx handle %08lx; state [[+0x5ac]+8] %ld (Attack sets the goal only at 0 / 4); +0x654 %08lx +0x720 %08lx; B rescan %ld force %lu hold %ld",
                 i, (unsigned long)B, (unsigned long)so, so == e->snd ? "==" : "!=", (unsigned long)hf, (unsigned long)hp, kbr_tgt_name(hcls), (unsigned long)hh, (long)ht, (unsigned long)g, (unsigned long)gh,
                 (long)st, (unsigned long)klh_rd32(e->snd + 0x654), (unsigned long)klh_rd32(e->snd + 0x720), (long)b180, (unsigned long)b184, (long)b18c);
            if (B > 0xffff) {      /* w9ady1fn9 lever 1: every B entry (flags / type / class / last-seen); fire test 0x616480 wants bit0 + 0x10 set, 0x4 / 0x40 / 0x200 clear */
                char buf[700]; int n = 0, k2; DWORD cnt = 0;
                if (klh_rd(B, &cnt, 4) && cnt <= 16) for (k2 = 0; k2 < (int)cnt && n < (int)sizeof buf - 64; k2++) {
                    DWORD q = B + 4 + 0x14 * k2, fl = klh_rd32(q), ent = klh_rd32(q + 4), ty = klh_rd32(q + 8), ts = klh_rd32(q + 0xc);
                    int ep = ent > 0xffff && klh_pvt(ent) == 0x00bb45f4u, ea = ent > 0xffff && !ep && klh_avt(ent) == 0x00bb3bacu, es = ent > 0xffff && !ep && !ea && klh_svt(ent) == 0x00bd0954u;
                    double ed = -1.0; float ep3[3]; int ebot = ep && (klbr_hl_body(ent) != 0 || klbr_hl_find(ent) != 0);      /* w53r6g2xi: 0x10 = in range, 0x4 = fire line blocked (same-team entity in the line) */
                    if (ep && klbr_bot_pos(e->actor, bp, &alive) && klh_rd(ent + 0x460, ep3, 12) && kle_ok3(ep3)) ed = kle_dist(bp, ep3) / 100;
                    n += _snprintf(buf + n, sizeof buf - n, " [%d %08lx f%03lx t%lu %s%s%s %.0fm t%ld]", k2, (unsigned long)ent, (unsigned long)fl, (unsigned long)ty, ep ? "ZFFPlayer" : ea ? "ZFFActor" : es ? "ZSoldier" : "other",
                                   ep ? (ebot ? "/bot" : "/human") : "", (ent == hp && hp) ? " PICK" : "", ed, (long)ts);
                }
                buf[sizeof buf - 1] = 0;
                klog("brain: traitor target: bot %d B list (%lu):%s", i, (unsigned long)cnt, n > 0 ? buf : " (empty / unreadable)");
            }
            {   /* w0g1x0zbt (verified, 11-03; READ ONLY): the shot is ZSoldier method 0x7088c0 (thiscall ecx = soldier, one float, ret 4) -> [[[s+0x40]]+0x6e4](holder handle, 2, f) at 0x708991.
                   Its gates, all pure reads here: [s+0x72c] != clock (once a frame); [s+0x88] == 2; team [[[s+0x40]+0x54]+4] != 0; float arg > 0 (Idle 0x77bbd0 passes 0.0 = never fires, the
                   positive callers are 0x5d7db9 / 0x6082c6 / 0x608476 / 0x7303f6, w53r6g2xi); [[s+0x678]+8] in {0,4}; 0x658050: o = [[s+0x40]+0x88c] blocks when o && [o+0x18] && ![o+0x40];
                   0x8eb610: p = [s+0x4a8] blocks when [p+8] not in {0,4}; holder handle != 0 and bit0 (bit7 clear for Idle site 1). Goal objects (GUESS from ctors): +0x634 Idle, +0x638 Attack, state [g+8]. */
                DWORD body = klh_rd32(e->snd + 0x40), p54 = body > 0xffff ? klh_rd32(body + 0x54) : 0, team = p54 > 0xffff ? klh_rd32(p54 + 4) : 0xffffffff;
                DWORD g678 = klh_rd32(e->snd + 0x678), o = body > 0xffff ? klh_rd32(body + 0x88c) : 0, p4a8 = klh_rd32(e->snd + 0x4a8), gi = klh_rd32(e->snd + 0x634), ga = klh_rd32(e->snd + 0x638);
                long s678 = g678 > 0xffff ? (long)klh_rd32(g678 + 8) : -1, v4a8 = p4a8 > 0xffff ? (long)klh_rd32(p4a8 + 8) : 0;
                int b658 = o > 0xffff && klh_rd32(o + 0x18) != 0 && klh_rd32(o + 0x40) == 0;
                klog("brain: traitor target: bot %d GATES (0x7088c0): +0x72c %ld clock %ld; +0x88 %lu (want 2); team %ld (want !=0); [[+0x678]+8] %ld (want 0/4); 0x658050 %s; [[+0x4a8]+8] %ld (%s); holder handle %08lx bit0 %lu bit7 %lu; Idle %08lx state %ld, Attack %08lx state %ld",
                     i, (long)klh_rd32(e->snd + 0x72c), (long)clk, (unsigned long)klh_rd32(e->snd + 0x88), (long)team, s678, b658 ? "BLOCKS" : "ok", v4a8, (v4a8 != 0 && v4a8 != 4) ? "BLOCKS" : "ok",
                     (unsigned long)hh, (unsigned long)(hf & 1), (unsigned long)((hf >> 7) & 1), (unsigned long)gi, gi > 0xffff ? (long)klh_rd32(gi + 8) : -1L, (unsigned long)ga, ga > 0xffff ? (long)klh_rd32(ga + 8) : -1L);
                if (hp > 0xffff) {      /* w53r6g2xi: the 0x5706a0 sweep lists E when [[E+0x54]+4] == the bot's team and byte [E+0x576] == 1 (the target blocks itself); fire test 0x616480 wants 0x11 with 0x4/0x40/0x200 clear */
                    DWORD h54 = klh_rd32(hp + 0x54); BYTE a576 = 0xff;
                    klh_rd(hp + 0x576, &a576, 1);
                    klog("brain: traitor target: bot %d TEAMS bot %ld holder %ld (%s) holder +0x576 %d +0x774 %08lx [0xce89b0] %08lx; fire test 0x616480 on holder flags %03lx: %s",
                         i, (long)team, h54 > 0xffff ? (long)klh_rd32(h54 + 4) : -1L, (h54 > 0xffff && klh_rd32(h54 + 4) == team) ? "SAME: the sweep lists the target" : "differ", (int)a576,
                         (unsigned long)klh_rd32(hp + 0x774), (unsigned long)klh_rd32((DWORD_PTR)KLH_VA(0xce89b0)), (unsigned long)(hf & 0x3ff), ((hf & 0x11) == 0x11 && !(hf & 0x244)) ? "PASS" : "FAIL");
                }
            }
        }
    }
    for (k = 0; k < 5; k++) {      /* A.3 */
        float h1 = 0.0f; DWORD v = klbr_hl.hp[k].victim, dt;
        if (!v) continue;
        dt = now - klbr_hl.hp[k].t0;
        if (klbr_hl.hp[k].step == 1 && dt < 500u) continue;
        if (klh_pvt(v) != 0x00bb45f4u || !klbr_hp_read(v, &h1)) { klbr_hl.hp[k].victim = 0; continue; }
        if (klbr_hl.hlog < 12) { klbr_hl.hlog++; klog("brain: traitor hit health: human %08lx (crew seat %d) hp %.1f -> %.1f, drop %.1f (attempted %.1f) +%lu ms (%s)", (unsigned long)v, klbr_hl.hp[k].seat, (double)klbr_hl.hp[k].hp0, (double)h1, (double)kbr_hp_drop(klbr_hl.hp[k].hp0, h1), (double)klbr_hl.hp[k].att, (unsigned long)dt, klbr_hl.hp[k].step ? "after 500 ms" : "next tick"); }
        if (klbr_hl.hp[k].step == 0) klbr_hl.hp[k].step = 1; else klbr_hl.hp[k].victim = 0;
    }
}
/* ---- OnlineBrainTraitorDamage (2026-11-03; re/fireline_goal_path_1103.md D step 4 + Verification 2 #16): 0x6e3400 zeroes the delta of a hit between two plain heisters unless a body carries +0x2726 (traitor) or
   +0x2723; a marked bot's mark lives only in the shadow record, so its hit on a human is neutralised before the first loot event. klud_w15 (slot 15 runs inside 0x6e3400 BEFORE that filter) calls klbr_dm_hit:
   the attacker body of a MARKED bot gets +0x2726 = 1 through klh_data (same write kladren.c makes for the local human; same ASSUMED-harmless caveat: the sense-manager call 0x4801a0 that the game's own
   setter makes is skipped). NOTE: other bots may now treat that body as hostile (their friend tests 0x882708 / 0x5709af read the byte) = the Arcade meaning of the mark; verify in the bench.
   Every changed byte is put back (only while it still holds our 1) at round end, round change, mark clear, death / tag change. ---- */
static void klbr_dm_restore(int i, const char *why)
{
    DWORD body; BYTE old, b = 0; int cur = -1;
    if (i < 0 || i >= KLBR_MAX) return;
    if (!klbr_dm[i].set) { klbr_dm[i].body = 0; return; }
    body = klbr_dm[i].body; old = klbr_dm[i].old; klbr_dm[i].set = 0;
    if (body > 0xffff && klh_pvt(body) == 0x00bb45f4u && klud_idx(body) == klbr_dm[i].rec && klh_rd(body + 0x2726, &b, 1)) cur = b;
    if (cur >= 0 && kbr_dm_restore_ok(cur)) {
        if (klh_data((void *)(DWORD_PTR)(body + 0x2726), &old, 1, "player: the traitor byte back (OnlineBrainTraitorDamage)")) klog("brain: traitor damage: bot %d body %08lx +0x2726 restored to %d (%s)", i, (unsigned long)body, (int)old, why);
        else klog("brain: traitor damage: bot %d body %08lx +0x2726 restore REFUSED (%s)", i, (unsigned long)body, why);
    } else klog("brain: traitor damage: bot %d body %08lx +0x2726 NOT written back (%s): %s", i, (unsigned long)body, why, cur < 0 ? "the body is gone or is another seat now" : "the byte no longer holds our 1");
    klbr_dm[i].body = 0;
}
static void klbr_dm_hit(DWORD victim, DWORD attacker)      /* game thread, inside the game's 0x6e3400 via klud_w15, BEFORE the original slot 15 */
{
    struct klbr_s *a; int i, cur; BYTE b = 0, one = 1;
    if (!klbr_dmon || !klbr_taon || klbr_ta_dis || !klbr_game_tid || GetCurrentThreadId() != klbr_game_tid || attacker < 0x10000 || attacker == victim) return;
    if (!(a = klbr_hl_body(attacker))) return;      /* only a ZFFPlayer body carries the byte; an actor / soldier attacker (class test fails, edi = 0 in 0x6e3400) already does full damage */
    if (a->state != 1 || !a->traitor) return;
    i = (int)(a - klbr_t);
    if (klbr_dm[i].set && klbr_dm[i].body != attacker) klbr_dm_restore(i, "the body pointer changed");
    if (klbr_dm[i].set) return;
    cur = klh_rd(attacker + 0x2726, &b, 1) ? (int)b : -1;
    if (kbr_dm_decide(1, 1, 1, cur) != KBR_DM_SET) return;
    if (!klh_data((void *)(DWORD_PTR)(attacker + 0x2726), &one, 1, "player: the traitor byte of a marked bot (OnlineBrainTraitorDamage)")) { if (klbr_hl.dmlog++ < 5) klog("brain: traitor damage: bot %d body %08lx: the +0x2726 write was refused", i, (unsigned long)attacker); return; }
    klbr_dm[i].body = attacker; klbr_dm[i].set = 1; klbr_dm[i].rec = a->rec; klbr_dm[i].old = (BYTE)cur;
    if (klbr_hl.dmlog++ < 5) klog("brain: traitor damage: set %d: bot %d (rec %d) body %08lx +0x2726 %d -> 1 before a hit on %08lx (the Arcade meaning of the mark; other bots may now treat him as hostile)", klbr_hl.dmlog, i, a->rec, (unsigned long)attacker, cur, (unsigned long)victim);
}
static int klbr_ta_make(void)      /* the shared private ZSoldier table, made once; 0 = not possible (feature off) */
{
    DWORD org[KLBR_TA_NSLOT], *blk, va = KLBR_TA_SOLDIER_VT + (DWORD)klh_delta, col = 0;
    if (klh_soldier_priv) return 1;
    if (klbr_ta_made) return 0;
    klbr_ta_made = 1;
    if (!klh_rd(va, org, sizeof org) || org[KLBR_TA_SLOT] != KLBR_TA_ORG + (DWORD)klh_delta) { klog("brain: traitor arcade: ZSoldier slot %d does not read as 0x882470: OnlineBrainTraitorArcade off", KLBR_TA_SLOT); return 0; }
    klh_rd(va - 4, &col, 4);      /* slot -1 = the RTTI locator, copied like the tactic tables above */
    if (!(blk = (DWORD *)VirtualAlloc(0, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE))) return 0;
    blk[0] = col; memcpy(blk + 1, org, sizeof org);
    klbr_ta_org = org[KLBR_TA_SLOT]; blk[1 + KLBR_TA_SLOT] = (DWORD)(DWORD_PTR)klbr_w_score;
    if (klbr_hfon) {      /* HumanFirst: slot 110 (police score), only when it reads as 0x7ffd20 */
        if (org[KLBR_HF_SLOT] == KLBR_HF_ORG + (DWORD)klh_delta) { klbr_hf_org = org[KLBR_HF_SLOT]; blk[1 + KLBR_HF_SLOT] = (DWORD)(DWORD_PTR)klbr_w_cop; klog("brain: traitor humanfirst: slot %d (police score) wrapped on the private table", KLBR_HF_SLOT); }
        else { klog("brain: traitor humanfirst: ZSoldier slot %d reads %08lx, not 0x7ffd20: OnlineBrainTraitorHumanFirst off", KLBR_HF_SLOT, (unsigned long)org[KLBR_HF_SLOT]); klbr_hfon = 0; }
    }
    if (klbr_hlon) {      /* HitLog A.4: Attack slot 83 log-only, only when it reads as the documented original */
        if (org[KLBR_ATK_SLOT] == KLBR_ATK_ORG + (DWORD)klh_delta) { klbr_atk_org = org[KLBR_ATK_SLOT]; blk[1 + KLBR_ATK_SLOT] = (DWORD)(DWORD_PTR)klbr_w_atk; klog("brain: traitor attack: slot %d (Attack) wrapped log-only on the private table", KLBR_ATK_SLOT); }
        else klog("brain: traitor attack: ZSoldier slot %d reads %08lx, not 0x831850: not wrapped", KLBR_ATK_SLOT, (unsigned long)org[KLBR_ATK_SLOT]);
    }
    klh_soldier_priv = (DWORD)(DWORD_PTR)(blk + 1);
    if (klbr_tflmode) {      /* FireLine: only when both slots read as the documented originals, else neither is wrapped */
        if (org[KLBR_TFL_S113] == KLBR_TFL_ORG113 + (DWORD)klh_delta && org[KLBR_TFL_S114] == KLBR_TFL_ORG114 + (DWORD)klh_delta) {
            klbr_tfl_org113 = org[KLBR_TFL_S113]; klbr_tfl_org114 = org[KLBR_TFL_S114];
            blk[1 + KLBR_TFL_S113] = (DWORD)(DWORD_PTR)klbr_w_fl113; blk[1 + KLBR_TFL_S114] = (DWORD)(DWORD_PTR)klbr_w_fl114;
            klog("brain: traitor fireline: slots %d / %d wrapped on the private table (mode %d)", KLBR_TFL_S113, KLBR_TFL_S114, klbr_tflmode);
        } else { klog("brain: traitor fireline: ZSoldier slots %d / %d read %08lx / %08lx, not 0x47a0f0 / 0x6bc0a0: OnlineBrainTraitorFireLine off", KLBR_TFL_S113, KLBR_TFL_S114, (unsigned long)org[KLBR_TFL_S113], (unsigned long)org[KLBR_TFL_S114]); klbr_tflmode = 0; }
    }
    klog("brain: traitor arcade: private ZSoldier table %08lx made (slot %d wrapped, %d slots copied)", (unsigned long)klh_soldier_priv, KLBR_TA_SLOT, KLBR_TA_NSLOT);
    return 1;
}
static void klbr_ta_restore(int i, int clearbit, const char *why)      /* the stock table back (only where it is still ours); clearbit: also rec+0x79 &= ~2 (only for a record this DLL saw marked) */
{
    DWORD snd = klbr_ta[i].snd, stock = KLBR_TA_SOLDIER_VT + (DWORD)klh_delta; int rec = klbr_ta[i].rec;
    klbr_dm_restore(i, why);      /* OnlineBrainTraitorDamage: the body byte back with the table */
    if (!snd) return;
    klbr_sn_unfeed(i, snd); klbr_ta[i].snd = 0; klbr_ta[i].rec = 0; klbr_ta[i].nlog[0] = klbr_ta[i].nlog[1] = 0; klbr_sn_at[i] = 0; klbr_cl[i].lat = 0;      /* OnlineBrainTraitorSense: feeding stops with the wrap */
    if (klh_soldier_priv && klh_rd32(snd) == klh_soldier_priv) klh_data((void *)(DWORD_PTR)snd, &stock, 4, "ZSoldier vtable pointer back (OnlineBrainTraitorArcade)");
    if (clearbit && rec > 0 && klbr_shadow) { __try { KLBR_PB(KLBR_REC(rec) + 0x79) &= (BYTE)~2; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_sw_flt++; } }
    klog("brain: traitor arcade: slot %d soldier %08lx back on the stock table (%s)", i, (unsigned long)snd, why);
}
static void klbr_ta_restore_all(const char *why)      /* before every memset of klbr_t (called from klbr_tr_restore_all) */
{
    int i, n = 0;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_ta[i].snd) { klbr_ta_restore(i, 1, why); n++; }
    for (i = 0; i < KLBR_MAX; i++) klbr_dm_restore(i, why);      /* a marked bot that was never wrapped may still carry our byte */
    klbr_tb_restore_all(why);      /* OnlineBrainTraitorTraitorByte: also on 'the session is gone' / 'round change' paths that skip the summary */
    memset(klbr_dm, 0, sizeof klbr_dm);
    klbr_sn_flt = 0; klbr_sn_fed = 0; klbr_sn_logged = 0; klbr_sn_unfed = 0; klbr_sn_dlog = 0; klbr_sn_dat = 0;      /* OnlineBrainTraitorSense: the round's counters */
    if (n) klog("brain: traitor arcade: %s: %d wrapped bot(s) cleared", why, n);
}
static void klbr_ta_pump(void)      /* game thread, depth 0, outside the AI walk: give a freshly marked bot the table; take it away on death / tag change / round end */
{
    DWORD sm = 0, role = 0, mode = 0, state = 0; int i, rok;
    rok = (sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) && sm == klbr_sm_round && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4) && role == 2 && mode == 4 && state == KLB_ROUND;
    if (!klbr_taon || klbr_ta_dis) { for (i = 0; i < KLBR_MAX; i++) if (klbr_dm[i].set) klbr_dm_restore(i, "Arcade off or disabled after faults"); }      /* every exit path puts the byte back, also when klbr_ta_make failed mid-round */
    if (!klbr_taon) return;
    if (klbr_trcap > 0 && klbr_shadow) KLBR_P32(klbr_shadow + 0x338) = kbr_tr_cap_word(klbr_ta_n, klbr_trcap);      /* same cap word as Turn: marks (not turns) count; OnlineBrainTraitorMax 0 = stock behaviour */
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i]; float pos[3]; int alive = 0;
        if (klbr_dm[i].set && (!rok || e->state != 1 || !e->traitor)) klbr_dm_restore(i, !rok ? "round or state ended" : "the mark is gone");
        if (klbr_ta[i].snd) {
            if (!rok || e->state != 1 || e->snd != klbr_ta[i].snd || !e->actor || !klbr_bot_pos(e->actor, pos, &alive) || !alive) klbr_ta_restore(i, 0, !rok ? "round or state ended" : "dead, gone or the tag changed");
            else klbr_sense_feed(i, GetTickCount());      /* OnlineBrainTraitorSense (off unless set) */
            continue;
        }
        if (!e->pendArc) continue;
        e->pendArc = 0;
        if (!rok || e->state != 1 || !e->snd || e->rec <= 0) { klog("brain: traitor arcade: slot %d: the mark is not wrapped (round or tag gone)", i); continue; }
        if (!klbr_bot_pos(e->actor, pos, &alive) || !alive) { klog("brain: traitor arcade: slot %d: not wrapped (the bot is dead)", i); continue; }
        if (!klbr_ta_make()) { klbr_taon = 0; return; }
        if (klh_rd32(e->snd) != KLBR_TA_SOLDIER_VT + (DWORD)klh_delta) { klog("brain: traitor arcade: slot %d soldier %08lx has vtable %08lx, not the stock ZSoldier one: not wrapped", i, (unsigned long)e->snd, (unsigned long)klh_rd32(e->snd)); continue; }
        if (!klh_data((void *)(DWORD_PTR)e->snd, &klh_soldier_priv, 4, "ZSoldier vtable pointer (OnlineBrainTraitorArcade)")) { klog("brain: traitor arcade: slot %d: the vtable write was refused", i); continue; }
        klbr_ta[i].snd = e->snd; klbr_ta[i].rec = e->rec;
        if (++klbr_ta_wlog <= 8) klog("brain: traitor arcade: bot %d wrapped (soldier %08lx, actor %08lx, rec %d): it may now target human players as in Arcade; team stays Ally", i, (unsigned long)e->snd, (unsigned long)e->actor, e->rec);
    }
}

/* ---- OnlineBrainTraitorTurn: turn / back / booking, all on the game thread at depth 0 (the pump) ------------------------------------------------------------------------------------------------- */
static void klbr_tr_restore(int i, const char *why)
{
    if (!klbr_tt[i].on) return;
    klbr_tt[i].on = 0; klbr_tt[i].was_alive = 0;      /* his own death is not a crew death */
    if (klb_foe_unturn_actor(klbr_tt[i].actor, klbr_tt[i].info, klbr_tt[i].team0)) { klbr_tt_back++; klog("brain: traitor: slot %d (actor %08lx) team %lu back (%s); %d crew death(s) booked to him", i, (unsigned long)klbr_tt[i].actor, (unsigned long)klbr_tt[i].team0, why, klbr_tt[i].kills); }
    else klog("brain: traitor: slot %d (actor %08lx) team NOT written back (%s): the actor or its team object changed or is gone (team object %08lx, nothing is written to a changed object)", i, (unsigned long)klbr_tt[i].actor, why, (unsigned long)klbr_tt[i].info);
}
static void klbr_tr_restore_all(const char *why)      /* before every memset of klbr_t, at the round end and in the not-a-round branch of the tick */
{
    int i;
    klbr_ta_restore_all(why);      /* OnlineBrainTraitorArcade: the stock ZSoldier tables back and the marks cleared BEFORE the tags are wiped */
    for (i = 0; i < KLBR_MAX; i++) klbr_tr_restore(i, why);
}
static void klbr_tr_pump(void)
{
    DWORD sm = 0, role = 0, mode = 0, state = 0; int i, j, rok; float d[KLBR_MAX];
    if (!klbr_trturn) return;
    rok = (sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) && sm == klbr_sm_round && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4) && role == 2 && mode == 4 && state == KLB_ROUND;
    if (klbr_trcap > 0) KLBR_P32(klbr_shadow + 0x338) = kbr_tr_cap_word(klbr_tt_turned, klbr_trcap);      /* optional hard cap, a 0 / 0x7fff block switch (not a count): 0x43ffb0 tests [rules+0x338] < tuning[R+0x6c] (0/1/2/3/4 by level, 2 at level 6). Static check 11-03 (scratchpad traitor_cap.md): in Arcade the word stays 0 all round (ctor 0x835771 and round reset 0x8c7abe zero it; the only inc, 0x432310 in 0x4322f0, is dead code), so Arcade has no working count cap: its ~1 traitor comes from the evaluate's score >= 7.0 gate. Max=0 is the Arcade behaviour */
    for (i = 0; i < KLBR_MAX; i++) {      /* 1. back-conditions and the death booking, every pump */
        struct klbr_s *e = &klbr_t[i]; float pos[3]; int alive = 0, have = e->state == 1 && e->actor && klbr_bot_pos(e->actor, pos, &alive), ab = 0; long ty = 0;
        if (klbr_tt[i].on) {
            int why = kbr_tr_back_why(have && !alive, klbf_ob_ledger(klbr_tt[i].actor, &ab, &ty) && ab, e->state == 1, rok, e->state == 1 && e->actor == klbr_tt[i].actor && klh_rd32(klbr_tt[i].actor + 0x54) == klbr_tt[i].info);
            if (why) { klbr_tr_restore(i, kbr_tb_name[why]); continue; }
            if (have) { memcpy(klbr_tt[i].pos, pos, 12); klbr_tt[i].was_alive = 1; }
            continue;
        }
        if (!have) continue;
        if (klbr_tt[i].was_alive && !alive && !(klbf_ob_ledger(e->actor, &ab, &ty) && ab)) {      /* a bot that boarded may read as not alive: not a crew death */      /* a crew bot died: booked to the nearest live turned bot within TraitorKillNear (the killer is not read; policemen's kills count too, as in Arcade). GUESS: a dead actor's +0x460 still reads */
            int best;
            for (j = 0; j < KLBR_MAX; j++) { d[j] = -1.0f; if (klbr_tt[j].on) { float dx = pos[0] - klbr_tt[j].pos[0], dy = pos[1] - klbr_tt[j].pos[1], dz = pos[2] - klbr_tt[j].pos[2]; d[j] = (float)sqrt(dx * dx + dy * dy + dz * dz); } }
            if ((best = kbr_tr_nearest(d, KLBR_MAX, klbr_trnear)) >= 0) {
                klbr_tt[best].kills++; klbr_tt_kills++;
                klog("brain: traitor: crew bot slot %d died %.1f m from the traitor in slot %d: booked (%d of %d)", i, (double)(d[best] / 100.0f), best, klbr_tt[best].kills, klbr_trkillmax);
                if (kbr_tr_capped(klbr_tt[best].kills, klbr_trkillmax)) { klbr_tt_capped++; klog("brain: traitor: TRAITOR CAP: slot %d is booked with %d crew death(s) (TraitorKillMax=%d): team Ally again", best, klbr_tt[best].kills, klbr_trkillmax); klbr_tr_restore(best, "TraitorKillMax reached"); }
            }
        }
        klbr_tt[i].was_alive = alive; memcpy(klbr_tt[i].pos, pos, 12);
    }
    for (i = 0; i < KLBR_MAX; i++) {      /* 2. apply a pending turn */
        struct klbr_s *e = &klbr_t[i]; DWORD oth[KLBR_MAX], info = 0, t0 = 0; float pos[3]; int alive = 0, ab = 0; long ty = 0; char why[120];
        if (!e->pendTurn) continue;
        e->pendTurn = 0;
        if (!rok || e->state != 1 || !e->actor) { klog("brain: traitor: slot %d: the turn is dropped (round or tag gone)", i); continue; }
        if (!klbr_bot_pos(e->actor, pos, &alive) || !alive) { klog("brain: traitor: slot %d: the turn is dropped (the bot is dead)", i); continue; }
        if (klbf_ob_ledger(e->actor, &ab, &ty) && ab) { klog("brain: traitor: slot %d: the turn is dropped (the bot is aboard)", i); continue; }
        for (j = 0; j < KLBR_MAX; j++) oth[j] = (j != i && klbr_t[j].state == 1) ? klbr_t[j].actor : 0;
        if (!klb_foe_turn_actor(e->actor, oth, KLBR_MAX, 32, &info, &t0, why, sizeof why)) { klbr_tt_refused++; klog("brain: traitor: slot %d (actor %08lx) stays team Ally: %s - nothing written", i, (unsigned long)e->actor, why); continue; }
        klbr_tt[i].actor = e->actor; klbr_tt[i].info = info; klbr_tt[i].team0 = t0; klbr_tt[i].on = 1; klbr_tt[i].kills = 0; klbr_tt[i].was_alive = 1; memcpy(klbr_tt[i].pos, pos, 12); klbr_tt_turned++;
        klog("brain: traitor: TURNED slot %d (actor %08lx, record %d, tally $%ld, team object %08lx: %lu -> 1 Enemy): the crew and the escort should shoot him; clients keep the replicated team (GUESS)", i, (unsigned long)e->actor, e->rec, ty, (unsigned long)info, (unsigned long)t0);
    }
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
        if (e->state == 1 && klbr_boardreal && !klbr_turned_actor(e->actor)) {      /* TraitorTurn: a turned bot does not board */
            if (klbr_bstage) { int ab = 0; long ty = 0; if (klbf_ob_ledger(e->actor, &ab, &ty) && !ab) klbr_bs_real++; }      /* BoardStage: only a bot the hook path tracks and has not already boarded counts as the real tactic's (review 11-03 defect 3: an untracked bot is not counted) */
            klbf_brain_boarded(e->actor); klbf_brain_board_call(e->actor);
        }
    }
    klbr_ta_pump();      /* OnlineBrainTraitorArcade */
    klbr_hl_pump(now);      /* OnlineBrainTraitorHitLog probe (read only) */
    klbr_cf_pump(now);      /* OnlineBrainTraitorCoverFire health readout (read only) */
    klbr_cl_list(now);      /* OnlineBrainTraitorCandLog: known-list size (read only) */
    klbr_tr_pump();      /* OnlineBrainTraitorTurn: before the bridge / puppet early return, so it also runs without them */
    klbr_boardlog(now);
    if (!klbr_bridge || !klbr_puppet) return;
    dt = last ? (float)(now - last) / 1000.0f : 0.1f; last = now; if (dt > 1.0f) dt = 1.0f;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x70, &st, 4)) return;
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i]; int k = e->rec, alive = 0, amt = 0, ctrlst = 0, inside; float pos[3], mp[3]; DWORD c; BYTE st64 = 0xff;
        if (e->state != 1 || k <= 0) continue;
        if (!klbr_bot_pos(e->actor, pos, &alive)) continue;
        if (klbr_turned_actor(e->actor)) { if (klbr_gr[k].on) klbr_grab_end(e, "the bot turned traitor", 0); continue; }      /* GUESS: a team-1 bot cannot loot; the DLL does not start or pay a grab for him */
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
    klbr_tr_restore_all("round end");      /* before the caller's memset of klbr_t */
    if (klbr_sm_round) {
        klbr_hitlog_summary();      /* OnlineBrainTraitorHitLog (a no-op line unless on); clears the round's counters */
        klbr_cand_summary();      /* OnlineBrainTraitorCandLog (silent unless on); clears the round */
        if (klbr_trturn) klog("brain: round end: traitor turn: turned %d, restored %d, kills %d, capped %d (%d turn(s) refused)", klbr_tt_turned, klbr_tt_back, klbr_tt_kills, klbr_tt_capped, klbr_tt_refused);
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

/* ---- ArcadeDiag (2026-11-03, [Brain] ArcadeDiag, default 0, test runs only) -------------------------------------------------------------------------------------------------------------------------
   READ-ONLY reference numbers from STOCK ARCADE for the Traitor evaluate, to compare with the online 'traitor diag' lines. Offline (role 0 / 1, session mode 4), no host round, no shadow rules, no rules swap.
   MECHANISM (the same one the online wrap uses, a vtable pointer on the object, because no code or .rdata byte may be written): the wrap in klbrain.c is NOT installed in Arcade (klbr_make_vtables runs only for
   Build=1 and acts only on the host round, klbr_wanted needs role 2). Here a SEPARATE DLL-owned copy of the Traitor vtable 0xbd13bc is made (slot 2 RUN = a counting tail-jump stub, slot 11 evaluate = an observer that
   calls the original straight (no swap, no fault guard, so a fault behaves exactly as stock) and then reads), and the tick writes that copy's address into [tactic] of each Arcade Ally soldier's Traitor tactic
   ([soldier+0x5f8], built by the game's own ctor). THE ONLY GAME-MEMORY WRITE IS THAT ONE DWORD PER TACTIC OBJECT (its vtable pointer; the copy differs only in the two slots, which call the originals with the same
   arguments). Everything else is data reads. GUESS: nothing compares the object's vtable pointer to 0xbd13bc (same GUESS as the online wrap); evaluate is thiscall with no stack argument (CERTAIN, 0x85f8e2). */
static int klbr_adiag;
static DWORD klbr_ad_vt, klbr_ad_ev_org, klbr_ad_run_org;      /* the vtable copy (pointer to slot 0) and the two originals */
static volatile LONG klbr_ad_on, klbr_ad_ev_n, klbr_ad_ev_nz, klbr_ad_run_n, klbr_ad_marks, klbr_ad_wrapped, klbr_ad_unused_n, klbr_ad_smp, klbr_ad_smp_pass, klbr_ad_zero_pass, klbr_ad_nz_fail, klbr_ad_bad;
static volatile LONG klbr_ad_slotmask;
static int klbr_ad_dg0, klbr_ad_dg1, klbr_ad_told;
static DWORD klbr_ad_rules, klbr_ad_t0, klbr_ad_last, klbr_ad_scan_at, klbr_ad_hb_at, klbr_ad_slot_at[12]; static LONG klbr_ad_hb_ev;
static BYTE klbr_ad_seen[12]; static int klbr_ad_seeded, klbr_ad_hbn;      /* seeded: the first mark poll of a round only records the bytes; hbn: capped heartbeat lines */
static struct { DWORD obj, snd; } klbr_ad_o[32]; static int klbr_ad_no;
static long klbr_ad_row0; static int klbr_ad_row0_un = -1, klbr_ad_lvl; static float klbr_ad_limit; static long klbr_ad_cap = -9;      /* last readings, for the summary after the rules are gone */

static void __cdecl klbr_ad_hit(void) { InterlockedIncrement(&klbr_ad_run_n); }
static __declspec(naked) void klbr_ad_run_stub(void) { __asm push ecx __asm push edx __asm call klbr_ad_hit __asm pop edx __asm pop ecx __asm jmp dword ptr [klbr_ad_run_org] }      /* any signature: counted, then the original */

/* what the Arcade evaluate sees for this tactic, from the REAL rules: data reads only. Offsets as the shadow block mirrors the Heist rules (crew [+0x348] stride 0x7c, free bytes [+0x34c], count [+0x354], score block
   [+0x5f8] with money rows at +0x150 + 4*slot and the level byte at +0x45; tuning row R = [0x168d7c0] + 0x6ac + 0x70*L: limit R+0x20, stage terms R+0x24.., cap R+0x6c); GUESS: the REAL Arcade rules have these same
   offsets and the slot is [tactic+0x14] (set by 0x78f470 before the cap/score steps, so on an early return of the evaluate it may be stale) */
static void klbr_ad_note(DWORD self, float r)
{
    int nz = r > 0.0f, take; int *cnt = nz ? &klbr_ad_dg1 : &klbr_ad_dg0; DWORD G, rules, slot, nrec, crew, fr, score, tun, R, now = GetTickCount(); BYTE sb = 0, fb = 0, f0 = 0, lv = 0; float f[9], st[4] = { 0, 0, 0, 0 };
    int unused, unused0, L, pass; long own, row0, own_g, row0_g; float sum, sum0;
    InterlockedIncrement(&klbr_ad_ev_n); if (nz) InterlockedIncrement(&klbr_ad_ev_nz);
    G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); rules = G > 0xffff ? klh_rd32(G + 0x54) : 0;
    if (rules <= 0xffff || rules != klbr_ad_rules) return;
    slot = klh_rd32(self + 0x14);
    if (slot < 12) InterlockedOr(&klbr_ad_slotmask, 1L << slot);
    take = *cnt < 6;
    if (!take) { if (slot >= 12 || (int)(now - klbr_ad_slot_at[slot]) < 1000) return; klbr_ad_slot_at[slot] = now; }      /* counters: one model sample per slot and second */
    nrec = klh_rd32(rules + 0x354); crew = klh_rd32(rules + 0x348); fr = klh_rd32(rules + 0x34c); score = klh_rd32(rules + 0x5f8);
    if (!kbr_ad_slot_ok(slot, nrec) || crew <= 0xffff || fr <= 0xffff || score <= 0xffff) { InterlockedIncrement(&klbr_ad_bad); if (klbr_ad_told++ < 3) klog("brain: arcade diag: evaluate %.3f but the slot/crew/score read badly (slot %lu, count %lu, crew %08lx, free %08lx, score %08lx): the GUESSed offsets may not fit the real Arcade rules", (double)r, (unsigned long)slot, (unsigned long)nrec, (unsigned long)crew, (unsigned long)fr, (unsigned long)score); return; }
    klh_rd(crew + 0x7c * slot + 0x78, &sb, 1); klh_rd(fr + slot, &fb, 1); klh_rd(fr, &f0, 1); klh_rd(score + 0x45, &lv, 1);
    L = kbr_level_clamp(lv); unused = kbr_ad_unused(fb, slot, nrec); unused0 = kbr_ad_unused(f0, 0, nrec);
    own = (long)klh_rd32(score + 0x150 + 4 * slot); row0 = (long)klh_rd32(score + 0x150);
    own_g = kbr_ad_money(own, unused); row0_g = kbr_ad_money(row0, unused0);
    if (!(tun = klh_rd32((DWORD_PTR)KLH_VA(0x0168d7c0))) || !klh_rd(R = tun + 0x6ac + 0x70 * (DWORD)L, f, sizeof f) || !klh_rd(R + 0x24, st, sizeof st)) return;
    sum = kbr_ad_sum(st, sb, own_g, row0_g); sum0 = kbr_ad_sum(st, sb, own_g, 0); pass = kbr_ad_pass(sum, f[8]);
    klbr_ad_row0 = row0; klbr_ad_row0_un = unused0; klbr_ad_lvl = L; klbr_ad_limit = f[8]; klbr_ad_cap = (long)klh_rd32(R + 0x6c);
    if (unused) InterlockedIncrement(&klbr_ad_unused_n);
    InterlockedIncrement(&klbr_ad_smp); if (pass) InterlockedIncrement(&klbr_ad_smp_pass);
    if (!nz && pass) InterlockedIncrement(&klbr_ad_zero_pass);
    if (nz && !pass) InterlockedIncrement(&klbr_ad_nz_fail);
    if (take && kbr_diag_take(cnt, 6))
        klog("brain: arcade diag: evaluate %s %.3f: slot %lu soldier %08lx stage byte %d, bot row $%ld%s, row 0 $%ld%s (real rules), sum %.1f (stage term %.1f + bot %d + player %d) vs limit %.1f -> score %s; sum with row 0 = 0 would be %.1f; level %d, tuning cap %ld",
             nz ? "NONZERO" : "zero", (double)r, (unsigned long)slot, (unsigned long)klh_rd32(self + 4), (int)sb, own_g, unused ? " (unused slot, game reads -1)" : "", row0_g, unused0 ? " (unused slot, game reads -1)" : "", (double)sum, (double)st[kbr_ad_stage_ix(sb)],
             kbr_ad_term_u(own_g), 3 - kbr_ad_term_u(row0_g), (double)f[8], pass ? "PASSES" : "fails", (double)sum0, L, (long)klh_rd32(R + 0x6c));
}
static float __fastcall klbr_ad_ev(DWORD self, DWORD d)
{
    float r = ((klbr_evfn)(DWORD_PTR)klbr_ad_ev_org)(self, 0);      /* the original FIRST and unguarded: identical to stock, then read-only bookkeeping */
    (void)d;
    if (klbr_ad_on) klbr_ad_note(self, r);
    return r;
}
static int klbr_ad_make_vt(void)
{
    DWORD org[KLBR_NSLOT], va = klbr_vt_va[2] + (DWORD)klh_delta, col = 0, *blk;
    if (klbr_ad_vt) return 1;
    if (!klh_rd(va, org, sizeof org) || org[0] != 0x004fe6f0u + (DWORD)klh_delta || org[2] != 0x00488eb0u + (DWORD)klh_delta || org[11] != 0x0079b7c0u + (DWORD)klh_delta) { klog("brain: arcade diag: the Traitor vtable %08lx does not read as {0x4fe6f0, run 0x488eb0, evaluate 0x79b7c0} (slots %08lx %08lx %08lx): ArcadeDiag off", (unsigned long)va, (unsigned long)org[0], (unsigned long)org[2], (unsigned long)org[11]); klbr_adiag = 0; return 0; }
    klh_rd(va - 4, &col, 4);
    if (!(blk = (DWORD *)VirtualAlloc(0, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE))) { klbr_adiag = 0; return 0; }
    blk[0] = col; memcpy(blk + 1, org, sizeof org);
    klbr_ad_run_org = org[2]; klbr_ad_ev_org = org[11]; blk[1 + 2] = (DWORD)(DWORD_PTR)klbr_ad_run_stub; blk[1 + 11] = (DWORD)(DWORD_PTR)klbr_ad_ev;
    klbr_ad_vt = (DWORD)(DWORD_PTR)(blk + 1);
    klog("brain: arcade diag: observer vtable copy %08lx made (slot 2 run -> counting stub -> %08lx, slot 11 evaluate -> observer -> %08lx; slot 0 = the game's destructor)", (unsigned long)klbr_ad_vt, (unsigned long)klbr_ad_run_org, (unsigned long)klbr_ad_ev_org);
    return 1;
}
static void klbr_ad_summary(const char *why, DWORD now)
{
    int ns = 0, i; LONG m = klbr_ad_slotmask;
    for (i = 0; i < 12; i++) if (m & (1L << i)) ns++;
    klog("brain: arcade diag: round summary (%s, %lu s): rules %08lx level %d limit %.1f tuning cap %ld; Traitor tactics wrapped %ld; evaluate calls %ld (nonzero %ld, distinct slots %d); model samples %ld: score passes %ld, zero-although-score-passes (0.30 roll / cap / timer refused) %ld, nonzero-although-score-fails (model contradicted) %ld, unused-slot reads %ld, bad reads %ld; Traitor RUN calls %ld, marks (rec+0x79 bit 2 rose) %ld; real rules row 0 money $%ld (%s)",
         why, (unsigned long)((now - klbr_ad_t0) / 1000u), (unsigned long)klbr_ad_rules, klbr_ad_lvl, (double)klbr_ad_limit, klbr_ad_cap, (long)klbr_ad_wrapped, (long)klbr_ad_ev_n, (long)klbr_ad_ev_nz, ns, (long)klbr_ad_smp, (long)klbr_ad_smp_pass, (long)klbr_ad_zero_pass, (long)klbr_ad_nz_fail, (long)klbr_ad_unused_n, (long)klbr_ad_bad,
         (long)klbr_ad_run_n, (long)klbr_ad_marks, klbr_ad_row0, klbr_ad_row0_un < 0 ? "never read" : klbr_ad_row0_un ? "unused slot, the game reads -1" : "used slot");
}
static void klbr_ad_tick(int game_thread, DWORD now)
{
    DWORD sm, role = 0, mode = 0, G, rules = 0; int arcade, i;
    if (!klbr_adiag || !game_thread || !klh_exe_ok || now - klbr_ad_last < 250u) return;
    klbr_ad_last = now;
    G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); if (G > 0xffff) rules = klh_rd32(G + 0x54);
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION));
    /* Arcade = the Arcade-like roles of 0x7f6850 (role 0 / 1, mode 4; CERTAIN for the question, GUESS that offline Arcade really reads role 0 / 1 and mode 4 here) with real rules present */
    arcade = sm > 0xffff && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && role <= 1 && mode == 4 && rules > 0xffff && rules != klbr_shadow;
    if (!arcade) {
        if (klbr_ad_rules) { klbr_ad_on = 0; klbr_ad_summary("round end", now); klbr_ad_rules = 0; klbr_ad_no = 0; memset(klbr_ad_seen, 0, sizeof klbr_ad_seen); }
        return;
    }
    if (rules != klbr_ad_rules) {      /* a new rules object = a new round */
        if (klbr_ad_rules) { klbr_ad_on = 0; klbr_ad_summary("round change", now); }
        klbr_ad_ev_n = klbr_ad_ev_nz = klbr_ad_run_n = klbr_ad_marks = klbr_ad_wrapped = klbr_ad_unused_n = klbr_ad_smp = klbr_ad_smp_pass = klbr_ad_zero_pass = klbr_ad_nz_fail = klbr_ad_bad = klbr_ad_slotmask = 0;
        klbr_ad_dg0 = klbr_ad_dg1 = klbr_ad_told = klbr_ad_no = klbr_ad_seeded = klbr_ad_hbn = 0; klbr_ad_row0 = 0; klbr_ad_row0_un = -1; klbr_ad_lvl = 0; klbr_ad_limit = 0; klbr_ad_cap = -9;
        memset(klbr_ad_seen, 0, sizeof klbr_ad_seen); memset(klbr_ad_slot_at, 0, sizeof klbr_ad_slot_at); memset(klbr_ad_o, 0, sizeof klbr_ad_o);
        klbr_ad_rules = rules; klbr_ad_t0 = klbr_ad_scan_at = klbr_ad_hb_at = now; klbr_ad_hb_ev = 0;
        if (!klbr_ad_make_vt()) { klbr_ad_rules = 0; return; }
        klog("brain: arcade diag: Arcade round starts (read only): role %lu mode %lu rules %08lx (vtable %08lx), no state is written except the vtable dword of each Traitor tactic", (unsigned long)role, (unsigned long)mode, (unsigned long)rules, (unsigned long)klh_rd32(rules));
        klbr_ad_on = 1;
    }
    if (now - klbr_ad_scan_at >= 2000u && klbr_ad_vt) {      /* bots spawn over time: look for new Ally soldiers every 2 s */
        DWORD actor[KLBR_MAX], snd[KLBR_MAX]; int n = klbr_scan(actor, snd, KLBR_MAX);      /* team 2 (Ally) only, as the online scan; GUESS: Arcade crew bots are team 2 (the ctor builds the tactics for teams 0 and 2 only) */
        klbr_ad_scan_at = now;
        for (i = 0; i < n; i++) {
            DWORD obj = klh_rd32(snd[i] + 0x5f8), v; int k, known = 0;
            if (obj < 0x10000) continue;
            for (k = 0; k < klbr_ad_no; k++) if (klbr_ad_o[k].obj == obj) known = 1;
            if (known || klbr_ad_no >= 32) continue;
            v = klh_rd32(obj);
            if (v != klbr_vt_va[2] + (DWORD)klh_delta) continue;      /* not (yet) a stock Traitor tactic */
            if (!klbr_w32(obj, klbr_ad_vt)) continue;
            klbr_ad_o[klbr_ad_no].obj = obj; klbr_ad_o[klbr_ad_no].snd = snd[i]; klbr_ad_no++; klbr_ad_wrapped++;
            if (klbr_ad_wrapped <= 6) klog("brain: arcade diag: wrapped the Traitor tactic %08lx of soldier %08lx (actor %08lx)", (unsigned long)obj, (unsigned long)snd[i], (unsigned long)actor[i]);
        }
    }
    if (klbr_ad_on) {      /* marks: bit 1 (value 2) of rec+0x79 rising */
        DWORD crew = klh_rd32(rules + 0x348), nrec = klh_rd32(rules + 0x354);
        if (crew > 0xffff && nrec <= 12)
            for (i = 0; i < (int)nrec; i++) {
                BYTE b = 0;
                if (!klh_rd(crew + 0x7c * (DWORD)i + 0x79, &b, 1)) continue;
                if (klbr_ad_seeded && kbr_ad_rose(klbr_ad_seen[i], b)) { klbr_ad_marks++; if (klbr_ad_marks <= 12) klog("brain: arcade diag: Traitor MARK %ld: slot %d (actor %08lx) rec+0x79 %02x, %lu s into the round, evaluate calls so far %ld", (long)klbr_ad_marks, i, (unsigned long)klh_rd32(crew + 0x7c * (DWORD)i + 4), (unsigned)b, (unsigned long)((now - klbr_ad_t0) / 1000u), (long)klbr_ad_ev_n); }
                klbr_ad_seen[i] = b;
            }
        if (crew > 0xffff && nrec <= 12) klbr_ad_seeded = 1;
        if (now - klbr_ad_hb_at >= 30000u) { klbr_ad_hb_at = now; if ((LONG)klbr_ad_ev_n != klbr_ad_hb_ev && klbr_ad_hbn < 20) { klbr_ad_hbn++; klbr_ad_hb_ev = klbr_ad_ev_n; klbr_ad_summary("running", now); } }
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
    klbr_ad_tick(game_thread, now);      /* ArcadeDiag: read only, its own 250 ms clock, before the host-round gate */
    if (!klbr_on || !game_thread || !klh_exe_ok || now - last < 1000) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) { klbr_tr_restore_all("the session is gone"); return; }
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if (role != 2 || mode != 4 || state != KLB_ROUND) {      /* HOST Fragile Alliance round only; a client / other mode / lobby does nothing */
        klbr_tr_restore_all("the round is not running");      /* a team-1 actor must never outlive the round, and never the table that tracks it */
        if (klbr_sm_round && (state < KLB_ROUND || state >= 0x1f || role != 2)) { klbr_summary(); klbr_tr_restore_all("round end"); memset(klbr_t, 0, sizeof klbr_t); memset(klbr_tt, 0, sizeof klbr_tt); klbr_tt_turned = klbr_tt_back = klbr_tt_kills = klbr_tt_capped = klbr_tt_refused = klbr_dg0 = klbr_dg1 = 0; klbr_row0_which = -2; klbr_shadow_reset(); klbr_verdict_n = 0; }
        return;
    }
    klbr_game_tid = GetCurrentThreadId();
    if (klbr_sm_round != sm) { if (klbr_sm_round) klbr_summary(); klbr_tr_restore_all("round change"); memset(klbr_t, 0, sizeof klbr_t); memset(klbr_tt, 0, sizeof klbr_tt); klbr_tt_turned = klbr_tt_back = klbr_tt_kills = klbr_tt_capped = klbr_tt_refused = klbr_dg0 = klbr_dg1 = 0; klbr_row0_which = -2; memset(&klbr_hl, 0, sizeof klbr_hl); klbr_hl_s15 = 0; klbr_sm_round = sm; klbr_nbuilt = klbr_nrefused = klbr_nvec_fail = klbr_swaps = klbr_frames = klbr_sw_flt = klbr_sw_bad = klbr_slow = klbr_slow_run = klbr_nrevoke = klbr_crash_told = 0; klbr_us_max = 0; klbr_ngrab = klbr_npay = klbr_nabort = klbr_nstart = klbr_s202_n = klbr_s202_told = klbr_s45_n = klbr_ntraitor = 0; klbr_ta_n = klbr_ta_flt = klbr_ta_sc_n = klbr_ta_wlog = 0; klbr_ta_dis = 0; memset(klbr_ta, 0, sizeof klbr_ta); klbr_paid = 0; klbr_claim_skip = klbr_claim_fb = 0; klbr_dc_offered = klbr_dc_grabs = 0; klbr_bs_defer_n = klbr_bs_real = klbr_bs_fb = 0; klbr_bl_new = klbr_bl_rep = klbr_bl_gate = klbr_bl_sec = 0; klbr_bn_told = klbr_bn_ok = 0; memset(klbr_bl_at, 0, sizeof klbr_bl_at); klbr_sync_at = 0; klbr_depth = 0; klbr_shadow_reset(); klbr_verdict_n = 0;
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
        for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && now - klbr_t[i].seenAt > 15000u && klh_svt(klbr_t[i].snd) != KLE_SOLDIER_VT) { klog("brain: soldier %08lx is gone (dead or despawned); the game's destructor does NOT free its tactics (about 0x64 bytes leak per bot per round, accepted); we free nothing", (unsigned long)klbr_t[i].snd); klbr_t[i].state = 0; }
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
    klbr_adiag = klbr_key("ArcadeDiag");
    if (klbr_adiag) klog("brain: ArcadeDiag=1 (recommended off; test runs only): in an OFFLINE Arcade round the real Traitor evaluate / RUN are observed (counts, marks, first 6 zero + 6 nonzero answers with their score terms); the only write is the vtable dword of each Arcade Traitor tactic, pointing at a DLL copy that calls the originals");
    if (klbr_key("Loot") && !klbr_build) klog("brain: Loot needs Build=1: off");
    if (klbr_key("OnlineBrainBridge") && !klbr_loot) klog("brain: OnlineBrainBridge needs Build=1 and Loot=1: off");
    if (klbr_key("OnlineBrainBoard") && !klbr_build) klog("brain: OnlineBrainBoard needs Build=1: off");
    if (klbr_key("OnlineBrainBoardReal") && !klbr_board) klog("brain: OnlineBrainBoardReal needs OnlineBrainBoard=1: off");
    if (klbr_key("OnlineBrainTraitor") && !klbr_traitor) klog("brain: OnlineBrainTraitor needs Build=1 and OnlineBrainBridge=1: off");
    klbr_trturn = klbr_traitor && klbr_key("OnlineBrainTraitorTurn");
    klbr_trrow0 = GetPrivateProfileIntA("Brain", "OnlineBrainTraitorRow0", 0, klh_ini) == 1;
    klbr_trkillmax = (int)GetPrivateProfileIntA("Brain", "OnlineBrainTraitorKillMax", 2, klh_ini); if (klbr_trkillmax < 0) klbr_trkillmax = 0; if (klbr_trkillmax > 32) klbr_trkillmax = 32;
    klbr_trcap = (int)GetPrivateProfileIntA("Brain", "OnlineBrainTraitorMax", 0, klh_ini); if (klbr_trcap < 0) klbr_trcap = 0; if (klbr_trcap > 16) klbr_trcap = 16;
    { int nr = (int)GetPrivateProfileIntA("Brain", "OnlineBrainTraitorKillNear", 3000, klh_ini); klbr_trnear = (nr >= 100 && nr <= 100000) ? (float)nr : 3000.0f; }
    if (klbr_key("OnlineBrainTraitorTurn") && !klbr_trturn) klog("brain: OnlineBrainTraitorTurn needs OnlineBrainTraitor=1: off");
    klbr_taon = klbr_traitor && klbr_key("OnlineBrainTraitorArcade");
    if (klbr_key("OnlineBrainTraitorArcade") && !klbr_taon) klog("brain: OnlineBrainTraitorArcade needs OnlineBrainTraitor=1: off");
    klbr_tflmode = (int)GetPrivateProfileIntA("Brain", "OnlineBrainTraitorFireLine", 0, klh_ini); if (klbr_tflmode < 0) klbr_tflmode = 0; if (klbr_tflmode > 2) klbr_tflmode = 2;
    if (klbr_tflmode && !klbr_taon) { klog("brain: OnlineBrainTraitorFireLine needs OnlineBrainTraitorArcade=1: off"); klbr_tflmode = 0; }
    if (klbr_tflmode) klog("brain: OnlineBrainTraitorFireLine=%d UNTESTED (recommended off): a marked bot's ZSoldier slots 113 / 114 (fire-line friend list) are wrapped on the private table: %s", klbr_tflmode, klbr_tflmode == 1 ? "LOG ONLY, the original runs untouched" : "the Arcade rules are swapped in around the original so the human is not a friend");
    klbr_hlon = klbr_on && klbr_key("OnlineBrainTraitorHitLog");
    if (klbr_key("OnlineBrainTraitorHitLog") && !klbr_hlon) klog("brain: OnlineBrainTraitorHitLog needs the Brain on: off");
    klbr_hfon = klbr_taon && klbr_key("OnlineBrainTraitorHumanFirst");
    if (klbr_key("OnlineBrainTraitorHumanFirst") && !klbr_hfon) klog("brain: OnlineBrainTraitorHumanFirst needs OnlineBrainTraitorArcade: off");
    klbr_hxon = klbr_tflmode && klbr_key("OnlineBrainTraitorHolderFix");
    if (klbr_key("OnlineBrainTraitorHolderFix") && !klbr_hxon) klog("brain: OnlineBrainTraitorHolderFix needs OnlineBrainTraitorFireLine (slot 113 wrapped): off");
    if (klbr_hxon) klog("brain: OnlineBrainTraitorHolderFix=1 UNTESTED (recommended off): after a marked bot's slot 113, a human holder loses the self-block bit 0x4 and gains 0x10 inside the engine's weapon range (0x71e050)");
    klbr_hoon = klbr_taon && klbr_key("OnlineBrainTraitorHumanOnly");
    if (klbr_key("OnlineBrainTraitorHumanOnly") && !klbr_hoon) klog("brain: OnlineBrainTraitorHumanOnly needs OnlineBrainTraitorArcade: off");
    if (klbr_hoon) klog("brain: OnlineBrainTraitorHumanOnly=1 UNTESTED (recommended off): a marked bot scores no ally-bot body while a seen, in-range human is in its list");
    klbr_cfon = klbr_tflmode && klbr_key("OnlineBrainTraitorCoverFire");
    if (klbr_key("OnlineBrainTraitorCoverFire") && !klbr_cfon) klog("brain: OnlineBrainTraitorCoverFire needs OnlineBrainTraitorFireLine (slot 113 wrapped): off");
    klbr_cfh = klbr_cfon && klbr_key("OnlineBrainTraitorAttackHandle");
    if (klbr_key("OnlineBrainTraitorAttackHandle") && !klbr_cfh) klog("brain: OnlineBrainTraitorAttackHandle needs OnlineBrainTraitorCoverFire: off");
    if (klbr_cfh) klog("brain: OnlineBrainTraitorAttackHandle=1 UNTESTED (recommended off): the CoverFire call passes the human's handle, so slot 83 adds ZAttackTarget (+0x658, prio 0x96, runs the shooting tasks) instead of CoverFire; shipped DD never passes a nonzero handle (host only)");
    klbr_efon = klbr_cfh && klbr_key("OnlineBrainTraitorEntryFix");
    if (klbr_key("OnlineBrainTraitorEntryFix") && !klbr_efon) klog("brain: OnlineBrainTraitorEntryFix needs OnlineBrainTraitorAttackHandle: off");
    klbr_rson = klbr_cfh && klbr_key("OnlineBrainTraitorRestart");
    if (klbr_key("OnlineBrainTraitorRestart") && !klbr_rson) klog("brain: OnlineBrainTraitorRestart needs OnlineBrainTraitorAttackHandle: off");
    if (klbr_rson) klog("brain: OnlineBrainTraitorRestart=1 UNTESTED (recommended off): the marked bot's attack goal is re-run on every order (current-goal pointer cleared first), and a finished one that left the bot with no goal is dropped so Idle runs again (host only)");
    klbr_fpon = klbr_cfh && klbr_key("OnlineBrainTraitorFireProbe");
    if (klbr_key("OnlineBrainTraitorFireProbe") && !klbr_fpon) klog("brain: OnlineBrainTraitorFireProbe needs OnlineBrainTraitorAttackHandle: off");
    if (klbr_fpon) klog("brain: OnlineBrainTraitorFireProbe=1 UNTESTED (recommended off): READ ONLY, logs ZRunToPosShootingTask / ZFireWeaponTask on the marked bot's goal stack, the body aim target and gates, the tuning floats and the distance to the holder (host only)");
    klbr_tbon = klbr_cfh && klbr_key("OnlineBrainTraitorTraitorByte");
    if (klbr_key("OnlineBrainTraitorTraitorByte") && !klbr_tbon) klog("brain: OnlineBrainTraitorTraitorByte needs OnlineBrainTraitorAttackHandle: off");
    if (klbr_tbon) klog("brain: OnlineBrainTraitorTraitorByte=1 UNTESTED (recommended off): while a bot is marked and its body is a ZFFPlayer, its traitor byte +0x2726 is set to 1 so the game's friendly-fire filter 0x6e3400 does not zero its hits on heisters; put back at unmark / round end (host only). Other bots may treat that body as hostile");
    klbr_hfion = klbr_cfh && klbr_key("OnlineBrainTraitorHoldFire");
    if (klbr_key("OnlineBrainTraitorHoldFire") && !klbr_hfion) klog("brain: OnlineBrainTraitorHoldFire needs OnlineBrainTraitorAttackHandle: off");
    if (klbr_hfion) klog("brain: OnlineBrainTraitorHoldFire=1 UNTESTED (recommended off): our slot-83 attack order is skipped while the marked bot's ZAttackTarget goal or its shooting task is running (state 1-3), for at most %d ms (host only)", KLBR_HF_MAXMS);
    if (klbr_efon) klog("brain: OnlineBrainTraitorEntryFix=1 UNTESTED (recommended off): while the marked bot's current goal is ZAttackTarget on a human, its known-list entry for that human gets 0x11 set and 0x244 cleared after every slot-113 call (host only)");
    if (klbr_cfon) klog("brain: OnlineBrainTraitorCoverFire=1 UNTESTED (recommended off): a marked bot whose holder is a human passing the fire test gets the shipped CoverFire goal (slot 83, handle 0) at that human, at most every 2 s");
    if (klbr_hlon) klog("brain: OnlineBrainTraitorHitLog=1 (recommended off): READ ONLY, counts hits of tagged bots (marked traitor vs other) on humans in the rules' damage hook (slot 15); one 'traitor hits:' line per round end");
    klbr_clon = klbr_taon && klbr_key("OnlineBrainTraitorCandLog");
    if (klbr_key("OnlineBrainTraitorCandLog") && !klbr_clon) klog("brain: OnlineBrainTraitorCandLog needs OnlineBrainTraitorArcade=1 (the census sits in the private slot 111): off");
    if (klbr_clon) klog("brain: OnlineBrainTraitorCandLog=1 (recommended off): READ ONLY, counts a marked bot's slot-111 candidates by class, logs the first 6 distinct per round, dumps its known-entities list size every 5 s, one 'traitor cands:' summary per round end");
    klbr_snon = klbr_taon && klbr_key("OnlineBrainTraitorSense");
    if (klbr_key("OnlineBrainTraitorSense") && !klbr_snon) klog("brain: OnlineBrainTraitorSense needs OnlineBrainTraitorArcade=1: off");
    klbr_snms = kbr_sense_ms((long)GetPrivateProfileIntA("Brain", "OnlineBrainTraitorSenseMs", 500, klh_ini));
    klbr_sn_seen = klbr_snon && klbr_key("OnlineBrainTraitorSenseSeen");
    if (klbr_sn_seen) klog("brain: OnlineBrainTraitorSenseSeen=1 UNTESTED (recommended off): the Sense feed calls B::MarkSeen 0x4880d0 (entry bit0 set, which ZAttackTarget's fire test 0x616480 needs) instead of NoteEntity");
    if (klbr_snon) klog("brain: OnlineBrainTraitorSense=1 UNTESTED (recommended off): every %d ms the game's B::NoteEntity (0x7bd720) is called for each live human body on a wrapped marked bot's known list, so slot 111 can see humans; stops with the wrap (unmark, death, round end); 3 faults = off for the round", klbr_snms);
    klbr_dmon = klbr_taon && klbr_key("OnlineBrainTraitorDamage");
    if (klbr_key("OnlineBrainTraitorDamage") && !klbr_dmon) klog("brain: OnlineBrainTraitorDamage needs OnlineBrainTraitorArcade=1 (and the Brain on): off");
    if (klbr_dmon) klog("brain: OnlineBrainTraitorDamage=1 UNTESTED (recommended off): in the rules' damage hook (slot 15) the body of a MARKED bot gets +0x2726 = 1 before its hit (so 0x6e3400 does not zero the delta on a human); put back at round end / mark clear / death. Other bots may treat that body as hostile");
    if (klbr_taon && klbr_trturn) { klog("brain: traitor arcade: OnlineBrainTraitorTurn ignored (Arcade=1: no team swap)"); klbr_trturn = 0; }
    if (klbr_taon) klog("brain: OnlineBrainTraitorArcade=1 UNTESTED (recommended off): a bot the real Traitor tactic marks stays team Ally but may target and shoot HUMAN players (ZSoldier slot 111 on a private table, the Arcade gate swapped in for that call); OnlineBrainTraitorMax %d; friend-list gap (no hook): the fire line of a marked bot still lists humans as friends", klbr_trcap);
    if (klbr_trturn) klog("brain: OnlineBrainTraitorTurn=1 UNTESTED (recommended off): a bot the real Traitor tactic marks goes team Enemy (the Arcade team swap, pump-applied) and back on death / aboard / the round end; row 0 = %s; TraitorKillMax %d within %.0f m (0 = no cap; stock Arcade killed 5 crewmates in 22 s uncapped), turn cap %d (0 = off)",
                          klbr_trrow0 ? "the richest human" : "the host", klbr_trkillmax, (double)(klbr_trnear / 100.0f), klbr_trcap);
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
        if (!klbr_make_shadow()) { klog("brain: shadow rules block could not be made: Loot / Board / Traitor / Bridge off"); klbr_trturn = klbr_taon = klbr_dmon = 0; klbr_loot = klbr_board = klbr_traitor = klbr_bridge = klbr_boardreal = klbr_puppet = 0; }
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
    if (klbr_traitor) klog("brain: OnlineBrainTraitor=1 UNTESTED: %s", klbr_trturn ? "the real Traitor roll runs; the team swap follows (TraitorTurn); the first 6 zero and 6 nonzero evaluates are logged as 'traitor diag'" : "MIRROR ONLY, the real Traitor roll runs and its record bit is logged (first 6 zero and 6 nonzero evaluates as 'traitor diag'); nothing changes for the bot");
    if (klbr_cops) klog("brain: OnlineBrainCops=1: research only (design 8.2): no behaviour is implemented, this line is the whole effect");
    if (klbr_puppet) klog("brain: PuppetOff=1 UNTESTED: OnlineTactics steering is skipped for a bot only within %d ms of its real Loot evaluate returning > 0 (Board: %d ms)", klbr_bridge ? klbr_lootwin : klbr_win_ms, klbr_boardwin);
}

#endif /* KLBRAIN_C */
