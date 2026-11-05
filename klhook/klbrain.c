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
static int klbr_bhold, klbr_bnode, klbr_bs0, klbr_blog; static long klbr_bl_new, klbr_bl_rep, klbr_bl_gate, klbr_bl_sec; static int klbr_bn_ok, klbr_bn_told; static float klbr_bn_pos[3]; static int klbr_bprobe, klbr_vis; static long klbr_bl_stale, klbr_bp_lines;      /* BoardProbe (default 0, log only): on; vehicle visit counter (kbr_bp_van_visit); BoardLog stale-ledger count; per-bot waiting lines this round */ static DWORD klbr_bl_at[16];      /* wk-boardgap 11-03 (all default 0): BoardHold ms the real Board tactic keeps a bot after its last Board evaluate / RUN-resume stamp; BoardNode: the crowd test targets the boarding node; BoardStage0: stage 3 to a no-box crowd bot; BoardLog: diagnostics (line counters, per-bot 1 s clock), node place (bn_ok 1 in van state 3 / 4 when readable) */
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
struct klbr_s { DWORD snd, actor, tac[3], seenAt, builtAt, nzAt, bnzAt, wSince, wUntil, s45At, pick, pickAt; float wpos[3]; int state, rec, traitor, flt, wHas, pendBoard, pendTurn, pendArc, bVis, bStgPrev; DWORD bLastAt, bpAt, bStgAt; float bLast; };      /* BoardProbe: bStgPrev = stage byte before the last change + 1 (0 = no change seen), bStgAt = |1 tick stamp of that change */      /* rec: shadow crew record 1..11 (0 none); bnzAt: tick of the last Board evaluate > 0;
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
/* ---- OnlineBrainTraitorNoBoard (11-04; re/traitor_board_1104.md, verifier endorsed lever C narrowed; UNTESTED, default off). DLL-owned code and data only: NO detour.
   A bot marked by OnlineBrainTraitorArcade (e->traitor, team stays Ally) is treated like a TraitorTurn bot by the puppeteer (klbf_brain_turned) so the hook never steers, escorts, boards or banks-by-fallback it.
   Mode 1: puppeteer + BoardAll skip. Mode 2: also the pendBoard hook boarding after slot 45. The stage byte [rec+0x78], the real Board tactic and the grab path are NOT touched. Host only (only the host's Brain marks). ---- */
static int klbr_nbmode;                 /* 0 off, 1, 2 */
static long klbr_nb_skip[3];            /* round: skips per path 0 puppeteer / 1 BoardAll / 2 pendBoard (every skipping call counts) */
static unsigned char klbr_nb_seen[KLBR_MAX];      /* round: bit per path already logged for this klbr_t slot (the first skip per bot and path is logged) */
static int klbr_nb_lines; static DWORD klbr_nb_at[KLBR_MAX]; static long klbr_nb_ev0[KLBR_MAX]; static int klbr_nb_drop;      /* round: 'brain: traitor board:' lines (budget 120), last line tick per slot, the ZCloseIn eval counter at the last line, orders dropped */
static const char *const klbr_nb_pname[3] = { "puppeteer", "boardall", "pendboard" };
static int klbr_nb_slot(DWORD actor)    /* klbr_t slot of a live marked bot (Arcade marking, no team swap), -1 otherwise */
{
    int i;
    if (klbr_nbmode < 1 || !klbr_taon || klbr_ta_dis || klbr_trturn || !actor) return -1;      /* ta_dis: Arcade disabled after faults, the marks no longer mean a wrapped bot */
    for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && klbr_t[i].traitor && klbr_t[i].actor == actor) return i;
    return -1;
}
static int klbr_noboard_actor(DWORD actor) { return kbr_nb_skip(klbr_nbmode, 0, klbr_taon, klbr_trturn, klbr_nb_slot(actor) >= 0); }
static int klbr_marked_actor(DWORD actor)      /* klbotfill.c OnlineVanGatherSkipTraitor: read only, 1 = a live bot with this actor is marked (e->traitor), whatever the NoBoard / Turn mode; plain int reads like klbr_nb_slot */
{
    int i;
    if (!actor) return 0;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_t[i].state == 1 && klbr_t[i].traitor && klbr_t[i].actor == actor) return 1;
    return 0;
}
static void klbr_nb_note(DWORD actor, int path, int phase)     /* a skip happened on 'path' (0..2); phase = the ledger phase (-1 untracked) */
{
    int ix = klbr_nb_slot(actor);
    if (ix < 0 || path < 0 || path > 2 || !kbr_nb_skip(klbr_nbmode, path, klbr_taon, klbr_trturn, 1)) return;
    klbr_nb_skip[path]++;
    if (!(klbr_nb_seen[ix] & (1u << path))) {
        klbr_nb_seen[ix] |= (unsigned char)(1u << path);
        klog("brain: traitor noboard: rec %d (actor %08lx) skipped by the %s path (OnlineBrainTraitorNoBoard %d), ledger phase %d", klbr_t[ix].rec, (unsigned long)actor, klbr_nb_pname[path], klbr_nbmode, phase);
    }
}
static void klbr_nb_summary(void)      /* round end (called by klbr_summary before the memsets); clears the round */
{
    int i, bots = 0;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_nb_seen[i]) bots++;
    if (klbr_nbmode > 0 && (bots || klbr_nb_skip[0] || klbr_nb_skip[1] || klbr_nb_skip[2] || klbr_nb_lines))
        klog("brain: traitor noboard: round end: skips puppeteer %ld, boardall %ld, pendboard %ld; bots affected %d; ledger orders dropped %d; board lines %d", klbr_nb_skip[0], klbr_nb_skip[1], klbr_nb_skip[2], bots, klbr_nb_drop, klbr_nb_lines);
    klbr_nb_skip[0] = klbr_nb_skip[1] = klbr_nb_skip[2] = 0; memset(klbr_nb_seen, 0, sizeof klbr_nb_seen); memset(klbr_nb_at, 0, sizeof klbr_nb_at); memset(klbr_nb_ev0, 0, sizeof klbr_nb_ev0); klbr_nb_lines = klbr_nb_drop = 0;
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
static int klbf_ob_phase(DWORD actor);                              /* klbotfill.c: the ledger phase of one bot (0 idle, 1 walking to a stack, 2 exit walk, 3 aboard, 4 looting), -1 when untracked (read only) */
static int klbf_ob_called(DWORD actor);                             /* klbotfill.c: BoardStage, 1 when the bot is ordered to / inside the exit box or aboard (read only) */
static int klbf_ot_s2open(void);                                    /* klbotfill.c: van called or gather running (read only) */
static int klbr_s2vrel; static volatile LONG klbr_s2vrel_logged;      /* [Brain] OnlineBrainTraitorMinSVanRelease (0 = off) and its once-per-round log */
static long klbr_mkgap; static DWORD klbr_mk_last; static volatile LONG klbr_mkgap_logged;      /* [Brain] OnlineBrainTraitorMarkGapMs (0 = off), tick of this round's last mark (0 = none), once-per-round log */
static long klbr_s2min, klbr_s2max; static volatile LONG klbr_s2min_logged, klbr_s2max_logged, klbr_s2hold_logged;    /* [Brain] OnlineBrainTraitorStage2MinS / MaxS (seconds after round start, 0 = off; UNTESTED) and the once-per-round log flags */
static int klbr_s2gate; static long klbr_s2money = 1250000;        /* [Brain] OnlineBrainTraitorStage2Gate / OnlineBrainTraitorStage2Money (UNTESTED, default off) */
static DWORD klbr_trr_t0, klbr_trr_pass1, klbr_trr_mark1; static long klbr_trr_pass, klbr_trr_marks;      /* TraitorRoll log: round start tick, first pass / first mark tick (|1), passed evaluates of unmarked bots, marks */
static int klbf_brain_take(DWORD ctrl, int amt);      /* the game's 0x4e3f40 through the puppeteer's guard; -> the stack's amount left, -1 when refused */
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
/* TraitorRoll (11-04; lines only with OnlineBrainTraitorStage2Gate or OnlineBrainTraitorHitLog on): a Traitor evaluate that answered > 0 means the score passed the limit (the diag's NONZERO); the real RUN then
   rolls (p 0.05 .. 0.40 by level) and either marks (klbr_traitor_mirror) or not. GUESS: refused = passes of not-yet-marked bots minus marks (each mark consumes one pass; a pass of a bot whose RUN
   never ran before the round ended also counts as refused). Round-clock seconds count from the host round start (klbr_trr_t0). */
static void klbr_trr_eval(const struct klbr_s *e, float r)
{
    DWORD now = GetTickCount();
    if (!e || r <= 0.0f || e->traitor || !(klbr_s2gate || klbr_hlon)) return;
    InterlockedIncrement(&klbr_trr_pass);
    if (!klbr_trr_pass1) {
        long bot = klbr_shadow ? (long)KLBR_P32(klbr_score + 0x150 + 4 * (DWORD)e->rec) : -1; int stage = klbr_shadow ? KLBR_PB(KLBR_REC(e->rec) + 0x78) : -1;
        if (InterlockedCompareExchange((volatile LONG *)&klbr_trr_pass1, (LONG)(now | 1u), 0) != 0) return;      /* another thread logged the first pass */
        klog("brain: traitor roll: first pass of the score at +%ld s of the round: record %d actor %08lx stage byte %d, own money $%ld, evaluate %.3f (Stage2Gate %d)", (long)((now - klbr_trr_t0) / 1000), e->rec, (unsigned long)e->actor, stage, bot, (double)r, klbr_s2gate);
    }
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
    if (klbr_bprobe && cls == 1 && e) { e->bLast = r; e->bLastAt = GetTickCount() | 1u; }      /* BoardProbe: the last Board evaluate answer of this bot (0 when faulted) */
    if (klbr_s2vrel && cls == 2 && e && !flt && r > 0.0f && !e->traitor && !InterlockedCompareExchange(&klbr_s2vrel_logged, 0, 0) && klbr_trr_t0 && kbr_mark_held(klbr_s2gate, (long)((GetTickCount() - klbr_trr_t0) / 1000), klbr_s2min) && !kbr_mark_held_v(klbr_s2gate, (long)((GetTickCount() - klbr_trr_t0) / 1000), klbr_s2min, klbr_van, 1)
        && !InterlockedExchange(&klbr_s2vrel_logged, 1)) klog("brain: MinSVanRelease: van state %d released the MinS hold at +%ld s (MinS %ld): record %d evaluate %.3f may mark now", klbr_van, (long)((GetTickCount() - klbr_trr_t0) / 1000), klbr_s2min, e->rec, (double)r);
    if (cls == 2 && e && !flt && r > 0.0f && !e->traitor && kbr_mark_held_v(klbr_s2gate, klbr_trr_t0 ? (long)((GetTickCount() - klbr_trr_t0) / 1000) : -1L, klbr_s2min, klbr_van, klbr_s2vrel)) {
        /* OnlineBrainTraitorStage2MinS (11-05, bs66): the stage BYTE cannot carry this floor for a board-ready bot (byte 3 is also read by the real Board tactic, lowering it would stop boarding), so the
           MARK itself waits: the Traitor evaluate answers 0 before MinS, the AI never picks the Traitor RUN, nothing else is touched. Needs gate on and MinS > 0 and a known round clock (else unchanged).
           Runs BEFORE the diag / roll counters (review 11-05) so a held evaluate is not logged as NONZERO nor counted as a refused roll, and klbr_ev_last / klbr_ev_nz stay honest. */
        if (!InterlockedExchange(&klbr_s2hold_logged, 1)) klog("brain: Stage2Gate: MinS holds the Traitor evaluate (%.3f -> 0) at +%ld s of the round (MinS %ld): record %d, stage byte %d, cannot be marked yet (GUESS: Arcade's first traitor is 150-240 s in)", (double)r, (long)((GetTickCount() - klbr_trr_t0) / 1000), klbr_s2min, e->rec, klbr_shadow ? KLBR_PB(KLBR_REC(e->rec) + 0x78) : -1);
        klbr_ev_last[cls] = 0.0f;
        return 0.0f;
    }
    if (cls == 2 && e && !flt && r > 0.0f && !e->traitor && kbr_mark_spaced(GetTickCount(), klbr_mk_last, klbr_mkgap)) {
        /* OnlineBrainTraitorMarkGapMs (11-05, bs71): after a mark the next one waits gap ms, like Arcade's spaced marks; the MinS hold alone releases every waiting bot in one tick. Same rule as above: before the counters, byte untouched. */
        if (!InterlockedExchange(&klbr_mkgap_logged, 1)) klog("brain: MarkGap: Traitor evaluate of record %d held (%.3f -> 0), the last mark was %lu ms ago (gap %ld ms)", e->rec, (double)r, (unsigned long)(GetTickCount() - klbr_mk_last), klbr_mkgap);
        klbr_ev_last[cls] = 0.0f;
        return 0.0f;
    }
    if (cls == 2 && e && !flt) { klbr_tr_diag(e, r); klbr_trr_eval(e, r); }
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

/* BoardProbe's per-visit line budget needs the visit it was last reset for (reset with the other probe counters at round change / round end). */
static int klbr_bp_lvis;
/* ---- BoardProbe (default 0; LOG ONLY, UNTESTED). Reads the REAL rules object's boarding fields so a bench can compare online DD03 (heli, [+0x1e0] = 0 in bs53) with Arcade (ARC bench: src 1, called
   from klmove.c's tick). Fields: [rules+0x1dc] state byte, [+0x1d8] timer (float), [+0x1e0] boarding object, [+0x1e4] group (both raw + readable), the chain 0x5aeb00 reads ([[+0x1e0]+4]+0x18, per the comment at
   klbr_sync / BoardNode: GUESS that it is exactly that chain; not disassembled), [+0x1ec] kind byte (botfill.c uses it as the vehicle kind). One line when the vehicle is first called (state 1..5) and at each
   state change, 24 lines per rules object; the budget is also zeroed explicitly at round change / round end (the rules pointer or vtable copy may be reused across rounds online, klroundkeep.c). src 0 = online host (caller checked the rules vtable), 1 = Arcade (needs ZGameRulesHeist's vtable 0xbd3514). */
static struct { DWORD rules; int prev, first; long lines; } klbr_bp_st[2];
static void klbr_bp_rules(DWORD rules, int src)
{
    {
        BYTE vb = 0, kind = 0; DWORD f2 = 0, f3 = 0, x = 0, n1 = 0, c18 = 0; float tm = 0.0f; int r2, r3, g2 = 0, g3 = 0, n1ok = 0, cok = 0, due;
        if (!rules || (src != 0 && src != 1)) return;
        if (src == 1 && klh_rd32(rules) != (DWORD)(DWORD_PTR)KLH_VA(0xbd3514)) return;      /* Arcade: ZGameRulesHeist only (online rules have their own vtables) */
        if (rules != klbr_bp_st[src].rules) { memset(&klbr_bp_st[src], 0, sizeof klbr_bp_st[src]); klbr_bp_st[src].rules = rules; klbr_bp_st[src].prev = -1; }
        if (!klh_rd(rules + 0x1dc, &vb, 1)) return;
        due = kbr_bp_rules_due(klbr_bp_st[src].first, klbr_bp_st[src].prev, (int)vb);
        klbr_bp_st[src].prev = (int)vb;
        if (!due || !kbr_bp_cap_ok(klbr_bp_st[src].lines, 24)) return;
        klbr_bp_st[src].first = 1; klbr_bp_st[src].lines++;
        klh_rd(rules + 0x1d8, &tm, 4); klh_rd(rules + 0x1ec, &kind, 1);      /* GUESS: +0x1ec byte = vehicle kind (as the botfill 'heli: ... kind=' log reads it) */
        r2 = klh_rd(rules + 0x1e0, &f2, 4); r3 = klh_rd(rules + 0x1e4, &f3, 4);
        g2 = r2 && f2 > 0xffff && klh_rd(f2, &x, 4); g3 = r3 && f3 > 0xffff && klh_rd(f3, &x, 4);
        if (g2) { n1ok = klh_rd(f2 + 4, &n1, 4) && n1 > 0xffff; if (n1ok) cok = klh_rd(n1 + 0x18, &c18, 4); }
        klog("brain: boardprobe: %s rules %08lx state %u timer %.1f kind %u: [+0x1e0] %08lx %s, [+0x1e4] %08lx %s, chain [[+0x1e0]+4] %08lx %s, [that+0x18] %s%08lx (as float %.2f)",
             src ? "ARCADE" : "online host", (unsigned long)rules, (unsigned)vb, (double)tm, (unsigned)kind, (unsigned long)f2, g2 ? "readable" : (r2 ? "NOT readable" : "read failed"), (unsigned long)f3, g3 ? "readable" : (r3 ? "NOT readable" : "read failed"),
             (unsigned long)n1, n1ok ? "readable" : "NOT readable", cok ? "" : "unread ", (unsigned long)c18, cok ? (double)*(float *)&c18 : 0.0);
    }
}

/* The stage byte [rec+0x78] the sync writes for one bot, computed ONCE per bot per sync (the BoardProbe line used to recompute it). OnlineBrainTraitorStage2Gate off = kbr_stage_byte exactly.
   Readers of the byte: the real Traitor / Board / Loot evaluates (the point of the gate) and the log lines; klbalance.c's off-stage damage factor reads it too (see the 11-04 note); klbf_ob_stage (CrewHop) and
   the hook's own boarding read the LEDGER (phase / tally), not this byte, so they are unaffected. */
static int klbr_stage_now(const struct klbr_s *e, int aboard, long tally)
{
    int ev = 0, st;
    long el = (klbr_s2gate && klbr_trr_t0) ? (long)((GetTickCount() - klbr_trr_t0) / 1000) : -1L;      /* round clock = the TraitorRoll one (set at the round change); unknown (-1) = no window */
    st = kbr_stage_compose_w(klbr_s2gate, klbr_bstage, aboard, tally, klbr_van, klbf_ob_called(e->actor), klbr_s2gate ? klbf_ot_s2open() : 0, klbr_s2money, el, klbr_s2min, klbr_s2max, &ev);      /* pure composition in klbrain_logic.h; the real van state 1..4 also opens the gate */
    if (ev == 1 && !InterlockedExchange(&klbr_s2min_logged, 1)) klog("brain: Stage2Gate: MinS holds back an open gate at +%ld s of the round (MinS %ld): record %d shows stage 1 instead of 2 (GUESS: Arcade's first traitor is 150-240 s in)", el, klbr_s2min, e->rec);
    if (ev == 2 && !InterlockedExchange(&klbr_s2max_logged, 1)) klog("brain: Stage2Gate: MaxS opens the gate at +%ld s of the round (MaxS %ld) with the gate closed (no opener now: no van call / gather / exit box at this moment): record %d shows stage 2", el, klbr_s2max, e->rec);
    return st;
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
            if (klbr_bprobe) klbr_bp_rules(real, 0);      /* BoardProbe: log only, reads the REAL rules */
            if (klh_rd(real + 0x1dc, &vb, 1) && klh_rd(real + 0x1d8, &f1, 4) && klh_rd(real + 0x1e0, &f2, 4) && klh_rd(real + 0x1e4, &f3, 4)) {
                DWORD nd = f2 > 0xffff ? klh_rd32(f2 + 4) : 0; BYTE t4[12];
                int nok = nd > 0xffff && klh_rd(nd + 0x18, t4, 4) && klh_rd(nd + 0x24, t4, 12) && klh_rd(nd + 0x50, t4, 4);      /* judge 11-03: Board RUN (0x5aeb00 / 0x6be1c0) reads [[+0x1e0]+4]+0x18/+0x24/+0x50 unchecked; an unreadable van node gets 0 (RUN then returns) */
                KLBR_PB(klbr_shadow + 0x1dc) = vb; KLBR_P32(klbr_shadow + 0x1d8) = f1; KLBR_P32(klbr_shadow + 0x1e0) = nok ? f2 : 0; KLBR_P32(klbr_shadow + 0x1e4) = nok ? f3 : 0; if (klbr_blog || klbr_bprobe) klbr_vis = kbr_bp_van_visit(klbr_van, (int)vb, klbr_vis); klbr_van = vb;
            }
        }
    }
    for (k = 0; k < KLBR_NREC; k++) { KLBR_PB(klbr_free + (DWORD)k) = used[k] ? 0 : 1; if (!used[k]) { KLBR_P32(KLBR_REC(k) + 4) = 0; KLBR_PB(KLBR_REC(k) + 0x79) = 0; } }
    for (i = 0; i < KLBR_MAX; i++) {
        struct klbr_s *e = &klbr_t[i]; int aboard = 0; long tally = -1; DWORD r; BYTE stg;
        if (e->state != 1 || e->rec <= 0) continue;
        r = KLBR_REC(e->rec);
        klbf_ob_ledger(e->actor, &aboard, &tally);      /* the host puppeteer's books: tally -1 stays when the bot has no slot yet */
        e->bVis = kbr_bp_stamp(klbr_blog, aboard, e->bVis, klbr_vis);      /* BoardLog stale-ledger count: the visit in which the 1 s sync FIRST sees the ledger aboard. LOWER BOUND for 'stale': a bot boarded in the last second of visit N and first seen after visit N+1 began is stamped N+1 and its later call counts 'repeat' (0 = no visit yet) */
        stg = (BYTE)klbr_stage_now(e, aboard, tally);      /* once per bot per sync: the probe and the write below share it */
        if (klbr_bprobe) { BYTE ns = stg, os = KLBR_PB(r + 0x78); if (ns != os) { e->bStgPrev = (int)os + 1; e->bStgAt = now | 1u; } }      /* BoardProbe: remember the stage byte's last change (same value the write below stores) */
        KLBR_P32(r + 4) = e->actor;
        KLBR_PB(r + 0x78) = stg;    /* BoardStage: ALSO 3 while the van waits and the bot carries loot / is ordered to the box; GUESS (static reading only): the real Board evaluate is gated on stage 3 = reached the exit / van called. Below: GUESS: [rec+0x78] is a byte stage 1 looting / 2 carrying / 3 aboard, as klbf_ob_stage() and the Loot EVAL notes read it; +0x79 is its neighbour byte */
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
    if (klbr_blog && e) { int ab = 0; long ty = 0; if (klbf_ob_ledger(e->actor, &ab, &ty) && ab) { if (kbr_bp_s45_class(1, e->bVis, klbr_vis) == 2) klbr_bl_stale++; else klbr_bl_rep++; } else klbr_bl_new++; }      /* stale = aboard since an EARLIER vehicle visit (the ledger was never cleared between visits), not a same-visit repeat */      /* BoardLog: slot-45 calls for a bot not aboard yet (real) vs one already aboard (repeat); GUESS: the ledger flips on the pump, so a few same-tick repeats count as real */
    if (e && klbr_boardreal) e->pendBoard = 1;      /* review 11-03: NO game call here (we are inside the AI walk and the frame); klbr_pump boards it on the game thread outside any frame */
}

/* Traitor RUN only flips rec+0x79 bit 1 (CERTAIN, 0x488ecd). Stage 3a MIRRORS it: log, count, nothing else changes for the bot (no team change, no announce: the puppeteer has no traitor path to call). */
static void klbr_traitor_mirror(struct klbr_s *e)
{
    if (!e || e->rec <= 0 || e->traitor) return;
    if (KLBR_PB(KLBR_REC(e->rec) + 0x79) & 2) {
        e->traitor = 1; klbr_ntraitor++; InterlockedIncrement(&klbr_trr_marks); if (!klbr_trr_mark1) klbr_trr_mark1 = GetTickCount() | 1u; klbr_mk_last = GetTickCount() | 1u;
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
    if ((!klbr_bnode && !klbr_blog && !klbr_bprobe) || !rules || vstate < 3 || vstate > 4) return;
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
/* ---- OnlineBrainTraitorLosGate / OnlineBrainTraitorLosProbe (2026-11-04, after bs38: the marked traitor's pellets all hit level objects between bot and human = it fires without a line of sight; UNTESTED, default off). ---------
   The stock clear-line test is ZAttackTarget's 0x4e1750 (thiscall ecx = the task, ret 8, only caller 0x4f4b92). We do NOT call it (needs a live ZAttackTarget, overwrites its arg 1); we repeat its last step, the physics line test
   (re-read with debug/dasm.py 11-04, 0x4e1831..0x4e1928, and the same call shape at 0x518ec1..0x518f00 in the spawn height probe):
     obj = [[[0xdd2640] + 0xac] + 0x8c]           (the collision world; ecx)
     call [[obj] + 0x264] with the stack args, FIRST argument first: the pushes are ebx(-1), 1, 1, ebx(-1), 0x10, 0, buf (0x4e1911..0x4e1921), so the call is f(buf, 0, 0x10, -1, 1, 1, -1). No add esp follows the call at 0x4e1922
     or 0x518efe and the next instructions read esp-relative slots, so the callee pops its 7 args (ret 0x1c; the callee itself was not located statically): the __fastcall type below (ecx, edx unused, 7 stack dwords) is the same convention.
     result al: 0x4e1750 ends 'test al,al / sete al' = CLEAR when the test finds NO hit. 0x518f00 'test al,al / je' (no hit) is the same meaning.
   buf is 0x6c bytes on the caller's stack (ebp-0xb0; the next local sits at ebp-0x40): 0x427100 (thiscall ecx = buf, plain ret) sets buf+0x24 = 1.0f, +0x3c = 0, byte +0x64 = 1, +0x68 = 0 and nothing else (the rest is stack garbage in the
   game; ours is zeroed: GUESS that zero is harmless). Then buf+0 = start xyz (arg1 = edi = the SHOOTER-side candidate point from the array at [ebp-0xbc], index 0 = the bot's own position, navmesh-snapped, y + 150 [0xb31878]; verified by disassembly 0x4f4b8b..0x4f4b92, the 11-04 first version had start and end swapped) and buf+0xc = delta xyz = arg2 (the TARGET point, [ebp-0x20]) - start, scaled by (len - 200) / len when len > 500
   (so the ray stops 200 short of the TARGET; kbr_los_delta, tested; the constants are the doubles at 0xb2d8e8 = 200 and 0xb64e20 = 500). The third argument 0x10 is the layer mask (0x20 in the spawn height probe, 6 in the projectile sweep 0x4cd400): GUESS what the bits mean; 0x10 is what the AI uses.
   The query buffer is ours; the world is only read. Our heights are GUESSes in the same convention as HolderFix: bot eye = +0x460 position y + 170, human chest = y + 150. Game thread, __try, 3 faults switch it off for the run. */
#define KLBR_LOS_CTX  0x00dd2640
#define KLBR_LOS_INIT 0x00427100
#define KLBR_LOS_MASK 0x10
#define KLBR_LOS_EYE  170.0f      /* GUESS: bot eye above the +0x460 position */
#define KLBR_LOS_CHEST 150.0f     /* GUESS: human chest above the +0x460 position (the engine's own +150 in 0x4e1750) */
typedef BYTE (__fastcall *klbr_losfn)(DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD);
static int klbr_loson, klbr_losprobe, klbr_los_flt;
static long klbr_los_n[KLBR_MAX][3];      /* per bot: clear / blocked / error (gate decisions) */
static long klbr_los_skip_sn, klbr_los_skip_hx, klbr_los_cache;
static int klbr_los_nlog;
static DWORD klbr_los_ca_at[KLBR_MAX], klbr_los_ca_h[KLBR_MAX]; static int klbr_los_ca_r[KLBR_MAX];
/* from = the bot eye, to = the human chest (both already raised). Returns 1 = clear, 0 = blocked; *ok = 0 when the query could not be made (return 0 then). */
static int klbr_los_ray(const float *from, const float *dl, int *ok);
static int klbr_los_clear(const float *from, const float *to, int *ok)
{
    float dl[3], len = 0.0f;
    *ok = 0;
    if (klbr_los_flt >= 3 || !klh_exe_ok) return 0;
    if (!kbr_los_delta(from, to, dl, &len)) return 0;     /* start = the SHOOTER-side point (arg1 of 0x4e1750 = edi, from the candidate array [ebp-0xbc]; index 0 = the bot's own position), delta toward the target (arg2 = [ebp-0x20]); fixed 11-04, was reversed */
    if (len > 80.0f && len <= 500.0f) { float k = (len - 40.0f) / len; dl[0] *= k; dl[1] *= k; dl[2] *= k; }      /* GUESS: the stock ray (len <= 500) runs the full way to arg2; we stop 40 short at the TARGET end so the human's own collision (if the line test sees characters) cannot give a false BLOCKED at close range. Not in the stock code. */
    return klbr_los_ray(from, dl, ok);
}
/* the raw physics line test: segment from + dl (no scaling). 1 = clear, 0 = blocked; *ok = 0 when the query could not be made. Also used by the LOS control rays. */
static int klbr_los_ray(const float *from, const float *dl, int *ok)
{
    DWORD buf[64], ctx, w, obj, vt, fn; BYTE al = 0;
    *ok = 0;
    if (klbr_los_flt >= 3 || !klh_exe_ok) return 0;
    ctx = klh_rd32((DWORD_PTR)KLH_VA(KLBR_LOS_CTX)); w = ctx > 0xffff ? klh_rd32(ctx + 0xac) : 0; obj = w > 0xffff ? klh_rd32(w + 0x8c) : 0; vt = obj > 0xffff ? klh_rd32(obj) : 0; fn = vt > 0xffff ? klh_rd32(vt + 0x264) : 0;
    if (fn < (DWORD)(DWORD_PTR)KLH_VA(0x401000) || fn >= (DWORD)(DWORD_PTR)KLH_VA(0xb00000)) return 0;      /* not a code pointer of the exe */
    memset(buf, 0, sizeof buf);
    __try {
        ((void (__fastcall *)(DWORD))(DWORD_PTR)KLH_VA(KLBR_LOS_INIT))((DWORD)(DWORD_PTR)buf);
        memcpy(&buf[0], from, 12); memcpy(&buf[3], dl, 12);
        al = ((klbr_losfn)(DWORD_PTR)fn)(obj, 0, (DWORD)(DWORD_PTR)buf, 0, KLBR_LOS_MASK, (DWORD)-1, 1, 1, (DWORD)-1);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        if (++klbr_los_flt >= 3) klog("brain: traitor losgate: the physics line test faulted 3 times: LOS off for the run");
        return 0;
    }
    *ok = 1;
    return kbr_los_class(0, al) == 0;
}
/* LOS control (11-04, once per round; reset with the round summary): from the bot eye six short rays (up 50, up 300, +x 100, -x 100, +z 100, -z 100) and one must-block ray (down 400).
   If the physics query is sound, at least one short ray is CLEAR and the down ray hits the floor (BLOCKED). All CLEAR/BLOCKED answers use the raw segment (no 200/500 scaling, no 40-short GUESS).
   'reversed' = the same +x 100 segment run from its far end back to the eye (direction test). Same fault handling as klbr_los_clear (shared klbr_los_flt, 3 faults = off). */
static int klbr_los_ctl_done;
static void klbr_los_control(int bot, const float *eye)
{
    static const struct { const char *nm; float d[3]; } rays[7] = {
        { "up50", { 0, 50, 0 } }, { "up300", { 0, 300, 0 } }, { "+x100", { 100, 0, 0 } }, { "-x100", { -100, 0, 0 } }, { "+z100", { 0, 0, 100 } }, { "-z100", { 0, 0, -100 } }, { "down400", { 0, -400, 0 } } };
    int k, ok, cl, nclear = 0, dblocked = -1, dfail = 0;
    if (klbr_los_ctl_done || klbr_los_flt >= 3 || !(eye[0] > -1.0e7f && eye[0] < 1.0e7f && eye[1] > -1.0e7f && eye[1] < 1.0e7f && eye[2] > -1.0e7f && eye[2] < 1.0e7f)) return;
    klbr_los_ctl_done = 1;
    for (k = 0; k < 7; k++) {
        ok = 0; cl = klbr_los_ray(eye, rays[k].d, &ok);
        klog("brain: traitor losgate CONTROL %s: %s (bot %d eye %.0f %.0f %.0f)", rays[k].nm, !ok ? "QUERY FAILED" : cl ? "CLEAR" : "BLOCKED", bot, (double)eye[0], (double)eye[1], (double)eye[2]);
        if (k < 6) { if (ok && cl) nclear++; } else { if (!ok) dfail = 1; else dblocked = cl ? 0 : 1; }
    }
    klog("brain: traitor losgate CONTROL summary: %d of 6 short rays clear; down400 %s (test works iff N>=1 and down400 BLOCKED): %s", nclear, dfail ? "QUERY FAILED" : dblocked ? "BLOCKED" : "CLEAR", (!dfail && nclear >= 1 && dblocked == 1) ? "WORKS" : "DOES NOT WORK / UNPROVEN");
    { float far_[3], back[3] = { -100, 0, 0 }; int ok2 = 0, cl2; far_[0] = eye[0] + 100.0f; far_[1] = eye[1]; far_[2] = eye[2];
      cl2 = klbr_los_ray(far_, back, &ok2);
      klog("brain: traitor losgate CONTROL reversed: eye+x100 -> eye: %s (forward eye -> eye+x100 was above)", !ok2 ? "QUERY FAILED" : cl2 ? "CLEAR" : "BLOCKED"); }
}
/* 1 = this human is BLOCKED from bot i (skip it), 0 = clear or unknown (fail open). Cached 250 ms per bot and human. bp / tp = the +0x460 positions. */
static int klbr_los_blocked(int i, DWORD human, const float *bp, const float *tp, DWORD now)
{
    float a[3], b[3]; int ok = 0, clear;
    if (!klbr_loson || i < 0 || i >= KLBR_MAX) return 0;
    if (klbr_los_ca_h[i] == human && klbr_los_ca_at[i] && now - klbr_los_ca_at[i] < 250u) { klbr_los_cache++; return klbr_los_ca_r[i] == 1; }
    a[0] = bp[0]; a[1] = bp[1] + KLBR_LOS_EYE; a[2] = bp[2];
    b[0] = tp[0]; b[1] = tp[1] + KLBR_LOS_CHEST; b[2] = tp[2];
    klbr_los_control(i, a);
    clear = klbr_los_clear(a, b, &ok);
    klbr_los_ca_h[i] = human; klbr_los_ca_at[i] = now | 1u; klbr_los_ca_r[i] = ok ? (clear ? 0 : 1) : 2;
    klbr_los_n[i][klbr_los_ca_r[i]]++;
    if (klbr_los_nlog < 8) { klbr_los_nlog++; klog("brain: traitor losgate: bot %d human %08lx: %s (eye %.0f %.0f %.0f -> chest %.0f %.0f %.0f, %.1f m)", i, (unsigned long)human, !ok ? "QUERY FAILED (fail open)" : clear ? "CLEAR" : "BLOCKED", (double)a[0], (double)a[1], (double)a[2], (double)b[0], (double)b[1], (double)b[2], (double)kle_dist(a, b) / 100.0); }
    return klbr_los_ca_r[i] == 1;
}
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
typedef struct { DWORD at; int blocked, open; } KLBR_CBP;      /* OnlineBrainTraitorCombatFlag: the last Sense pass of a bot: when, humans skipped as BLOCKED by LosGate, humans fed (not blocked) */
static KLBR_CBP klbr_cb_pass[KLBR_MAX];
static int klbr_cbmode, klbr_cb_flt, klbr_cb_nolog, klbr_cb_first[KLBR_MAX], klbr_cb_set[KLBR_MAX], klbr_cb_set6[KLBR_MAX]; static long klbr_cb_undo; static DWORD klbr_cb_next[KLBR_MAX];      /* mode 0 off, 1 / 2 / 3 see kbr_cb_decide; set6 = WE wrote [S+0x6fc] = 1 (mode 3) */
static long klbr_cb_w6, klbr_cb_r6, klbr_cb_nz6, klbr_cb_w, klbr_cb_sk_clear, klbr_cb_sk_6fc, klbr_cb_sk_nopass, klbr_cb_already, klbr_cb_b0null;
static int klbr_hsmode, klbr_hs_flt;      /* OnlineBrainTraitorHolderSet: 0 off, 1 flags 0x01, 2 flags 0x15 (see klbr_hs_apply) */
static int klbr_pass_all_blocked(int i, DWORD now)      /* the per-bot Sense / LosGate pass record is fresh, at least one human was skipped as BLOCKED and none is open (CombatFlag's and HolderSet's input) */
{
    return i >= 0 && i < KLBR_MAX && klbr_cb_pass[i].at && (int)(now - klbr_cb_pass[i].at) <= 2 * klbr_snms + 1000 && klbr_cb_pass[i].blocked > 0 && klbr_cb_pass[i].open == 0;
}
static void klbr_sense_feed(int i, DWORD now)      /* game thread, depth 0, host round, bot i is wrapped (klbr_ta[i].snd) and alive */
{
    struct klbr_s *e = &klbr_t[i]; DWORD G, rules, recs = 0, freeb = 0, B = 0, hs[16], cnt = 0, vt = 0; float hd[16], bp[3]; int n = 0, k, nr = 0, pick[KBR_SN_MAXFEED], np, alive = 0, haveb, shadow = 0;
    int c_used = 0, c_null = 0, c_dead = 0, c_cls = 0, c_bot = 0, c_seat = 0, c_pol = 0, c_h0 = 0, c_los = 0; const char *why = 0;      /* bs14: Sense never fed and logged nothing; these say which gate skips */
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
        if (klbr_loson && haveb && hd[n] < 1.0e29f && klbr_los_blocked(i, p, bp, tp, now)) { klbr_los_skip_sn++; c_los++; continue; }      /* OnlineBrainTraitorLosGate: a human behind geometry is not fed (unknown = fed) */
        hs[n++] = p;
    }
    klbr_cb_pass[i].at = now | 1u; klbr_cb_pass[i].blocked = c_los; klbr_cb_pass[i].open = n;      /* CombatFlag input (data only) */
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
    if (!nr && !klbr_sn_flt && klbr_sn_dlog < 8 && now - klbr_sn_dat >= 5000) { klbr_sn_dlog++; klbr_sn_dat = now; klog("brain: traitor sense: bot %d fed nothing: %s; rules %08lx%s vt %08lx count %lu; records free %d, empty body %d, dead %d, not ZFFPlayer %d, police %d, bot %d (seat-match only, still fed %d), handle 0 %d, no line of sight %d; found %d", i, why ? why : "gates passed", (unsigned long)rules, shadow ? " (shadow was in)" : "", (unsigned long)vt, (unsigned long)cnt, c_used, c_null, c_dead, c_cls, c_pol, c_bot, c_seat, c_h0, c_los, n); }
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
    if (klbr_hsmode && klbr_hs_flt < 3 && klbr_pass_all_blocked((int)(e - klbr_t), GetTickCount())) return;      /* OnlineBrainTraitorHolderSet wins while every human is BLOCKED: the holder it wrote (flags 0x01 / 0x15) must NOT be turned into 0x11 here, that passes the fire test through the wall. Order: slot 113 (HolderFix, this) runs in the AI walk, HolderSet in the pump; this early return makes the result independent of that order */
    if (!klbr_bot_pos(e->actor, bp, &alive) || !klh_rd(hp + 0x460, tp, 12) || !kle_ok3(tp)) return;
    if ((f6a0 = klh_rd32(self + 0x6a0)) > 0xffff && klbr_hx_flt < 3) {
        __try { range = ((klbr_rangefn)(DWORD_PTR)KLH_VA(KLBR_HX_RANGE))(f6a0, 0); }
        __except (EXCEPTION_EXECUTE_HANDLER) { range = -1.0f; if (++klbr_hx_flt >= 3) klog("brain: traitor holderfix: 0x71e050 faulted 3 times: range read off (no 0x10 set)"); }
    }
    if (klbr_loson && klbr_los_blocked((int)(e - klbr_t), hp, bp, tp, GetTickCount())) { klbr_los_skip_hx++; return; }      /* OnlineBrainTraitorLosGate: no line of sight = the engine's own flags stand (no 0x10 set, no 0x4 clear) */
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
static struct { DWORD rt, ft, rf, rl, ff, fl, lastlog, t0; int n, en, atk, tuned; long calls, rcalls, fcalls, eps, fireeps; DWORD maxep; DWORD s0, sl, e0, bs0, bsl; int shv, chf; long chcalls, cheps, shep; long c5z, c5nz; } klbr_fp[KLBR_MAX];      /* c5z / c5nz: slot-113 calls with byte [body+0x5c8] == 0 / != 0 (workflow wdntba8eu) */
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
/* FireProbe ext2 (11-03, workflow wdntba8eu; READ ONLY). Why the burst path never reaches SetAttackTarget: SKIP1 0x6d9eb0 = [s+0x700]==0 && (mode==6 || byte [body+0x5c8]==0); [body+0x5c8] is set to 1 by the body ctor
   0x83043e and cleared only by SelectWeapon 0x511450 on a real weapon switch (0x511536) or in mode 6 (0x51149b). All offsets below come from that workflow's trace; types are GUESS (dwords unless a byte is said), logged raw hex.
   rec = [body+0x54]. Line prefix: "brain: traitor fireprobe ext2:". */
static void klbr_fp_ext2(int ix, DWORD self, DWORD body)      /* one more sample line, read only */
{
    DWORD rec = body > 0xffff ? klh_rd32(body + 0x54) : 0; BYTE b5c8 = 0xff; WORD w3a = 0;
    if (body > 0xffff) klh_rd(body + 0x5c8, &b5c8, 1);
    if (rec > 0xffff) klh_rd(rec + 0x3a, &w3a, 2);
    klog("brain: traitor fireprobe ext2: bot %d [body+0x5c8] %02x [body+0x860] %08lx [body+0x70] %08lx [body+0x76c] %08lx [body+0x770] %08lx [body+0x550] %lu; [s+0x88] %08lx [s+0x5a8] %08lx [s+0x5dc] %08lx [s+0x98] %08lx [s+0x6a0] %08lx; rec %08lx [rec+0x30] %08lx [rec+0x34] %08lx word[rec+0x3a] %04x (all GUESS types)",
         ix, (unsigned)b5c8, (unsigned long)(body > 0xffff ? klh_rd32(body + 0x860) : 0), (unsigned long)(body > 0xffff ? klh_rd32(body + 0x70) : 0), (unsigned long)(body > 0xffff ? klh_rd32(body + 0x76c) : 0),
         (unsigned long)(body > 0xffff ? klh_rd32(body + 0x770) : 0), (unsigned long)(body > 0xffff ? klh_rd32(body + 0x550) : 0), (unsigned long)klh_rd32(self + 0x88), (unsigned long)klh_rd32(self + 0x5a8),
         (unsigned long)klh_rd32(self + 0x5dc), (unsigned long)klh_rd32(self + 0x98), (unsigned long)klh_rd32(self + 0x6a0), (unsigned long)rec, (unsigned long)(rec > 0xffff ? klh_rd32(rec + 0x30) : 0),
         (unsigned long)(rec > 0xffff ? klh_rd32(rec + 0x34) : 0), (unsigned)w3a);
}
static void klbr_fp_epstart(int ix, struct klbr_s *e, DWORD run)      /* once per ZRunToPosShootingTask episode, read only: destination, distance bot -> destination, task fields */
{
    DWORD d[3]; float f[3], bp[3]; int alive = 0, ok = klh_rd(run + 0x14, d, 12); BYTE b24 = 0xff; double dist = -1.0;
    if (!ok) return;
    memcpy(f, d, 12); klh_rd(run + 0x24, &b24, 1);
    /* GUESS: the destination is three floats at task+0x14..0x1c in the same world units as the entity positions (the 0x4a7e60 distance test compares d > 300); the bot position is the actor position as in the main sample */
    if (kle_ok3(f) && klbr_bot_pos(e->actor, bp, &alive)) dist = kle_dist(bp, f);
    klog("brain: traitor fireprobe ext2: bot %d episode start: task %08lx dest [+0x14..0x1c] %08lx %08lx %08lx (%.1f %.1f %.1f, GUESS floats) d to the bot %.1f units (%.1f m; -1 = unknown; the task compares d > 300) [task+0x20] %08lx byte[task+0x24] %02x [task+0x28] %08lx",
         ix, (unsigned long)run, (unsigned long)d[0], (unsigned long)d[1], (unsigned long)d[2], (double)f[0], (double)f[1], (double)f[2], dist, dist >= 0.0 ? dist / 100.0 : dist,
         (unsigned long)klh_rd32(run + 0x20), (unsigned)b24, (unsigned long)klh_rd32(run + 0x28));
}
/* OnlineBrainTraitorFireProbe3 (11-04, workflow wgby0tb0u follow-up; READ ONLY toward the game: no game-state write; recommended off; needs FireProbe, so AttackHandle + CoverFire). What the static trace (re/traitor_fire_1103.md,
   bs28..bs30) could not settle: where the chain from the run task to a shot stops once SKIP1 is open. Three parts.
   1. CALL COUNTERS by a counting detour (klbr_f3_install): ONLY two of the twelve wanted functions can be hooked without breaking the anti-tamper rules (klh_may_write: a TEST build, SessionSafe=1, may write code only outside the ranges
      kl2.exe's integrity checks hash, klranges.h; a SHIP build refuses all code writes and the detour is then simply not installed, logged). Checked 11-04 against klranges.h (first 16 bytes of each):
        0x8c1830 weapon controller tick   UNHASHED  prologue 55 8b ec 83 ec 1c (6 bytes, no relative operand) -> hooked, ecx = the controller [s+0x6a0], so FILTERED to the marked bots' controllers
        0x5faeb0 run-task arg setter      UNHASHED  prologue 55 8b ec 51 8b 45 08 (7 bytes, no relative operand) -> hooked. Disassembly: it stores [ecx+0x14..0x1c] = *arg1 (dest), [ecx+0x20] = arg3, byte [ecx+0x24] = arg4: so ecx is the
                                                    ZRunToPosShootingTask itself (the prompt called it 'soldier vt+0x74'); its owner is not known, so the filter is 'ecx is one of the last 4 run tasks FireProbe saw on a marked bot's goal stack'. A task armed
                                                    for the first time before FireProbe sees it counts as 'other' (GLOBAL, all soldiers); the caller histogram of 'other' shows whether those are the same callers.
        0x7c02b0 ZFireWeaponTask tick, 0x8cb920 brain vt+0x164, 0x8dc6a0, 0x8b84b0, 0x6c81a0, 0x432440 ZFFActor::FireWeapon, 0x8a3510 item fire, 0x7d3360, 0x6e3400, 0x7e1700: all HASHED -> NOT hooked (a detour
        in a hashed page would end the session; no guess). Their effect is read off DATA instead, per sample (part 3): [body+0x550] shots (FireProbe ext), [item+0xe8] (0x7d3360 stores the shot count there), [item+0xdc] ammo,
        [item+0xf8] / [item+0xfc] (0x8c1a43 plan flags), latches +0xed / +0xee / +0xef, [body+0x50c] / [body+0x824] / [body+0x654] (0x432440's gates), [s+0x570] (0x8cb920's task) and the 2R-versus-distance range hold of 0x8c1985.
      The patch is made at the first marked-bot call (game thread, jmp + nops; bytes verified first by klh_poke) and left in place (a counting stub is harmless once the toggle is off: it returns at once).
      Log: the first 3 matched controller ticks ("brain: traitor fireprobe3 hit:"), a round total "brain: traitor fireprobe3 counts:".
   2. RE-ARM CALLER: every matched 0x5faeb0 call: return address (minus the load delta), dest, the other args, ms since the previous matched call of that bot (first 40 per round), then per distinct return address counts at round end.
   3. SAMPLE (piggybacks FireProbe's sample point, so at most KLBR_FP_SMPMAX per bot per round): the numbers asked for, raw hex plus float / double readings where the type is a GUESS. Unreadable = 0 / ff. */
#define KLBR_F3_LOGMAX 40
#define KLBR_F3_RAMAX 12
typedef struct { DWORD efl, edi, esi, ebp, esp, ebx, edx, ecx, eax; } KLBR_F3REGS;      /* stub = pushad, pushfd, push esp: the pointer addresses the saved EFLAGS (lowest), then pushad's edi..eax (kbr_f3_emit) */
typedef char klbr_f3_chk_ecx[(offsetof(KLBR_F3REGS, ecx) == 28) ? 1 : -1];
typedef char klbr_f3_chk_esp[(offsetof(KLBR_F3REGS, esp) == 16) ? 1 : -1];
static const struct { DWORD va; BYTE len; BYTE bytes[8]; const char *what; } klbr_f3_sites[2] = {
    { 0x8c1830, 6, { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x1c }, "weapon controller tick (0x8c1830)" },
    { 0x5faeb0, 7, { 0x55, 0x8b, 0xec, 0x51, 0x8b, 0x45, 0x08 }, "run-task arg setter (0x5faeb0)" },
};
static int klbr_f3on, klbr_f3_state[2];      /* per site: 0 not tried, 1 installed, -1 refused / bytes differ */
static BYTE *klbr_f3_stub;
static DWORD klbr_f3_F[KLBR_MAX], klbr_f3_tk[KLBR_MAX][4], klbr_f3_last[KLBR_MAX]; static BYTE klbr_f3_tkn[KLBR_MAX];
static long klbr_f3_ctrl_m, klbr_f3_ctrl_o, klbr_f3_re_m, klbr_f3_re_o, klbr_f3_ra_lost;
static DWORD klbr_f3_ram[KLBR_F3_RAMAX], klbr_f3_rao[KLBR_F3_RAMAX]; static long klbr_f3_cm[KLBR_F3_RAMAX], klbr_f3_co[KLBR_F3_RAMAX]; static int klbr_f3_nm, klbr_f3_no;
static void __cdecl klbr_f3_hit(int id, KLBR_F3REGS *r)      /* called by the stub on the game thread; reads only */
{
    DWORD ret, ecx, now = GetTickCount(); int i, k, ix = -1;
    if (!klbr_f3on || !r) return;
    ret = klh_rd32(r->esp); ecx = r->ecx;
    if (id == 0) {      /* weapon controller tick: ecx = the controller */
        for (i = 0; i < KLBR_MAX; i++) if (klbr_f3_F[i] && klbr_f3_F[i] == ecx) { ix = i; break; }
        if (ix < 0) { klbr_f3_ctrl_o++; return; }
        klbr_f3_ctrl_m++;
        if (klbr_f3_ctrl_m <= 3) { DWORD item = klh_rd32(ecx + 4);
            klog("brain: traitor fireprobe3 hit: bot %d 0x8c1830 #%ld ret %08lx ecx(F) %08lx [F+4](item) %08lx [F+8] %08lx [F+0x20] %08lx [F+0x24] %08lx [F+0x34] %08lx item vt %08lx", ix, klbr_f3_ctrl_m, (unsigned long)(ret - (DWORD)klh_delta), (unsigned long)ecx, (unsigned long)item, (unsigned long)klh_rd32(ecx + 8),
                 (unsigned long)klh_rd32(ecx + 0x20), (unsigned long)klh_rd32(ecx + 0x24), (unsigned long)klh_rd32(ecx + 0x34), (unsigned long)(item > 0xffff ? klh_rd32(item) : 0)); }
        return;
    }
    for (i = 0; i < KLBR_MAX && ix < 0; i++) for (k = 0; k < 4; k++) if (klbr_f3_tk[i][k] && klbr_f3_tk[i][k] == ecx) { ix = i; break; }      /* 0x5faeb0 */
    if (ix < 0) {
        klbr_f3_re_o++;
        if (!kbr_f3_ra_add(klbr_f3_rao, klbr_f3_co, &klbr_f3_no, KLBR_F3_RAMAX, ret) && klbr_f3_no >= KLBR_F3_RAMAX) klbr_f3_ra_lost++;
        return;
    }
    klbr_f3_re_m++;
    if (!kbr_f3_ra_add(klbr_f3_ram, klbr_f3_cm, &klbr_f3_nm, KLBR_F3_RAMAX, ret) && klbr_f3_nm >= KLBR_F3_RAMAX) klbr_f3_ra_lost++;
    if (klbr_f3_re_m <= KLBR_F3_LOGMAX) {
        DWORD a1 = klh_rd32(r->esp + 4), a2 = klh_rd32(r->esp + 8), a3 = klh_rd32(r->esp + 12), d[3] = { 0, 0, 0 }; float f[3]; BYTE a4 = 0xff;
        klh_rd(a1, d, 12); memcpy(f, d, 12); klh_rd(r->esp + 16, &a4, 1);
        klog("brain: traitor fireprobe3 rearm: bot %d #%ld ret %08lx task %08lx dest %.1f %.1f %.1f (arg1 %08lx; GUESS: 3 floats) arg2 %08lx (%.2f) arg3 %08lx (%.2f) byte arg4 %02x; %ld ms since this bot's previous re-arm (-1 = first)",
             ix, klbr_f3_re_m, (unsigned long)(ret - (DWORD)klh_delta), (unsigned long)ecx, (double)f[0], (double)f[1], (double)f[2], (unsigned long)a1, (unsigned long)a2, klbr_fp_f(a2), (unsigned long)a3, klbr_fp_f(a3), (unsigned)a4,
             klbr_f3_last[ix] ? (long)(now - klbr_f3_last[ix]) : -1L);
    }
    klbr_f3_last[ix] = now;
}
static void klbr_f3_install(void)      /* once per site, at the first marked-bot call (game thread); a refusal is final for this run */
{
    int i;
    for (i = 0; i < 2; i++) {
        BYTE *at, jmp[10]; DWORD stub;
        if (klbr_f3_state[i]) continue;
        klbr_f3_state[i] = -1;
        if (!klbr_f3_stub && !(klbr_f3_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: traitor fireprobe3: no memory for the stubs: counters off"); return; }
        at = KLH_VA(klbr_f3_sites[i].va); stub = (DWORD)(DWORD_PTR)(klbr_f3_stub + 64 * i);
        if (!kbr_f3_emit(klbr_f3_stub + 64 * i, stub, i, (DWORD)(DWORD_PTR)klbr_f3_hit, klbr_f3_sites[i].bytes, klbr_f3_sites[i].len, (DWORD)(DWORD_PTR)(at + klbr_f3_sites[i].len))) continue;
        kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, klbr_f3_sites[i].len);
        if (klh_poke(at, klbr_f3_sites[i].bytes, klbr_f3_sites[i].len, jmp, klbr_f3_sites[i].len, "brain: FireProbe3 counting detour")) {
            klbr_f3_state[i] = 1; klog("brain: traitor fireprobe3: detour on %s installed", klbr_f3_sites[i].what);
        } else klog("brain: traitor fireprobe3: detour on %s NOT installed (refused by the patch guard - a SHIP build writes no code, a hashed range is refused - or the bytes differ): its counter stays 0", klbr_f3_sites[i].what);
    }
}
static void klbr_f3_track(int ix, DWORD self, DWORD run)      /* every slot-113 call of a bot FireProbe sees: remember its controller and its recent run tasks (the detours filter on them) */
{
    int k;
    if (!klbr_f3on || ix < 0 || ix >= KLBR_MAX) return;
    klbr_f3_install();
    klbr_f3_F[ix] = klh_rd32(self + 0x6a0);
    if (run) { for (k = 0; k < 4; k++) if (klbr_f3_tk[ix][k] == run) return; klbr_f3_tk[ix][klbr_f3_tkn[ix]++ & 3] = run; }
}
static DWORD klbr_f3_d(DWORD p) { return p > 0xffff ? klh_rd32(p) : 0; }
static BYTE klbr_f3_b(DWORD p) { BYTE b = 0xff; if (p > 0xffff) klh_rd(p, &b, 1); return b; }
static void klbr_f3_sample(int ix, struct klbr_s *e, DWORD self, DWORD body)      /* two lines, read only */
{
    DWORD t = klbr_f3_d(self + 0x570), F = klbr_f3_d(self + 0x6a0), item = F > 0xffff ? klbr_f3_d(F + 4) : 0, tpl = item > 0xffff ? klbr_f3_d(item + 0xc4) : 0, hp = klh_rd32(self + 0xac), d654[2] = { 0, 0 };
    float bp[3], tp[3], R = 0.0f; double dist = -1.0, v654; int alive = 0; char ammo[16];
    if (!klbr_f3on) return;
    if (item > 0xffff) _snprintf(ammo, sizeof ammo, "%lu", (unsigned long)kbr_f3_ammo(klbr_f3_d(item + 0xdc))); else strcpy(ammo, "unreadable");
    if (body > 0xffff) klh_rd(body + 0x654, d654, 8);
    memcpy(&v654, d654, 8);
    if (tpl > 0xffff) { DWORD rr = klh_rd32(tpl + 0xe0); memcpy(&R, &rr, 4); }
    if (hp > 0xffff && klbr_bot_pos(e->actor, bp, &alive) && klh_rd(hp + 0x460, tp, 12) && kle_ok3(tp)) dist = kle_dist(bp, tp);      /* same positions and unit (cm) as the main sample */
    klog("brain: traitor fireprobe3 sample: bot %d [s+0x570](fire task) %08lx byte+0x14 %02x; holder [s+0xa8] %08lx [s+0xac] %08lx [s+0xb0] %08lx; ctrl F %08lx [F+4] %08lx [F+8] %08lx [F+0x20] %08lx [F+0x24] %08lx [F+0x34] %08lx; "
         "item [+0x50] %08lx ammo [+0xdc]^beebbeeb %s [+0xe8] %08lx [+0xf8] %08lx [+0xfc] %08lx bytes +0xed/+0xee/+0xef %02x %02x %02x; template [item+0xc4] %08lx range R [+0xe0] %.1f (2R %.1f) bytes +0xf0 %02x +0xac %02x; dist bot->holder %.1f cm (%s)",
         ix, (unsigned long)t, (unsigned)klbr_f3_b(t + 0x14), (unsigned long)klh_rd32(self + 0xa8), (unsigned long)hp, (unsigned long)klh_rd32(self + 0xb0), (unsigned long)F, (unsigned long)item, (unsigned long)klbr_f3_d(F + 8), (unsigned long)klbr_f3_d(F + 0x20),
         (unsigned long)klbr_f3_d(F + 0x24), (unsigned long)klbr_f3_d(F + 0x34), (unsigned long)klbr_f3_d(item + 0x50), ammo, (unsigned long)klbr_f3_d(item + 0xe8), (unsigned long)klbr_f3_d(item + 0xf8), (unsigned long)klbr_f3_d(item + 0xfc),
         (unsigned)klbr_f3_b(item + 0xed), (unsigned)klbr_f3_b(item + 0xee), (unsigned)klbr_f3_b(item + 0xef), (unsigned long)tpl, (double)R, (double)(2.0f * R), (unsigned)klbr_f3_b(tpl + 0xf0), (unsigned)klbr_f3_b(tpl + 0xac), dist,
         dist < 0.0 ? "unknown" : (R > 0.0f ? (2.0 * R >= dist ? "2R >= d: range hold passes" : "2R < d: HOLDS FIRE at 0x8c1985 (GUESS: R is a float at template+0xe0)") : "R unreadable"));
    klog("brain: traitor fireprobe3 body: bot %d body %08lx [+0x5c4] %08lx [+0x68c] %08lx byte[+0x576] %02x [+0x654] %08lx %08lx (as double %.4f; 0x4d2750 compares it with the double at 0xb1cd40, GUESS type) [+0x42c] %08lx [+0x50c] %08lx [+0x824] %08lx",
         ix, (unsigned long)body, (unsigned long)klbr_f3_d(body + 0x5c4), (unsigned long)klbr_f3_d(body + 0x68c), (unsigned)klbr_f3_b(body + 0x576), (unsigned long)d654[0], (unsigned long)d654[1], v654, (unsigned long)klbr_f3_d(body + 0x42c), (unsigned long)klbr_f3_d(body + 0x50c), (unsigned long)klbr_f3_d(body + 0x824));
}
static void klbr_f3_summary(void)      /* at round end, before the arrays are cleared */
{
    int i;
    if (klbr_f3on) {
        klog("brain: traitor fireprobe3 counts: 0x8c1830 weapon controller tick: marked bots' controllers %ld, other controllers %ld (detour %s); 0x5faeb0 run-task arg setter: recent run tasks of marked bots %ld, other tasks (all soldiers, GLOBAL) %ld (detour %s); "
             "NOT counted, hashed (read off data in the sample lines): 0x7c02b0 0x8cb920 0x8dc6a0 0x8b84b0 0x6c81a0 0x432440 0x8a3510 0x7d3360 0x6e3400 0x7e1700; distinct callers lost to the table cap %ld",
             klbr_f3_ctrl_m, klbr_f3_ctrl_o, klbr_f3_state[0] > 0 ? "on" : "NOT installed", klbr_f3_re_m, klbr_f3_re_o, klbr_f3_state[1] > 0 ? "on" : "NOT installed", klbr_f3_ra_lost);
        for (i = 0; i < klbr_f3_nm; i++) klog("brain: traitor fireprobe3 rearm callers (marked): return address %08lx x %ld", (unsigned long)(klbr_f3_ram[i] - (DWORD)klh_delta), klbr_f3_cm[i]);
        for (i = 0; i < klbr_f3_no; i++) klog("brain: traitor fireprobe3 rearm callers (other tasks): return address %08lx x %ld", (unsigned long)(klbr_f3_rao[i] - (DWORD)klh_delta), klbr_f3_co[i]);
    }
    klbr_f3_ctrl_m = klbr_f3_ctrl_o = klbr_f3_re_m = klbr_f3_re_o = klbr_f3_ra_lost = 0; klbr_f3_nm = klbr_f3_no = 0;
    memset(klbr_f3_F, 0, sizeof klbr_f3_F); memset(klbr_f3_tk, 0, sizeof klbr_f3_tk); memset(klbr_f3_last, 0, sizeof klbr_f3_last); memset(klbr_f3_tkn, 0, sizeof klbr_f3_tkn);
}
/* OnlineBrainTraitorFireProbe4 (11-04, workflow w8tlxwm93 "bullet -> victim hp"; DATA READS ONLY: no hook, no game-state write; recommended off; needs FireProbe, so AttackHandle). Piggybacks FireProbe's sample point. Two kinds of line,
   at most KLBR_F4_LOGMAX per round each, and a round total "brain: traitor fireprobe4 round:".
   1. "fireprobe4 item:" for the marked bot's item = [[s+0x6a0]+4]: [+0x138] (calls into the per-shot routine 0x4cb7a0, ++ at 0x4cb8b9), [+0xe8] pending shots, [+0xe4], bytes +0xed +0xef +0x136 +0x137, float +0xf0, [+0x104], [+0x160]
      against [[0xdd2640]+0x44] (GUESS: the game-time word the shot loop compares), and the deltas of +0x138 and +0xe8 since the previous sample of this bot. The owner handle [item+0x5c] is resolved with 0x8ccde0, the SAME pure
      handle -> entity lookup FireProbe already calls on [body+0x544] (read from code at 0x4f44a7 / 0x4cb7a0: a table lookup, no side effect), on the game thread (we are inside the slot-113 call of the soldier) and under __try; it is
      NOT called once FireProbe's lookup has faulted 3 times. For the owner (the bot body if unresolved): bit 12 of [[owner+4]+0x3c] (0x4cb7a0's 'may shoot' byte, with the ZLNKOBJ type test as the other way in), the owner's vtable (class by
      vtable compare, as everywhere in this file; vt+0x30 is NOT called), the masks [0x153a898] / [0x153a89c] raw, and [0x1535230] against [[0xdd265c]+0x8b4] (the per-frame cap of the item tick 0x488ad0, GUESS types: unsigned compare).
   2. "fireprobe4 victim:" for the holder [s+0xac] when it is a ZFFPlayer (the only human the probe finds without a new scan): [+0x438] bit 18, [+0x274c] and dword [[+0x274c]+0x14], word [[+0x54]+0x3a] (0x458880 skips everything
      when non-zero), hp (klbr_hp_read), [+0x774]; the bot's [body+0x274c] / [+0x774]; the session [sm+0x54] / [+0x5c] / [+0x70] (sm = [0x168e598]); [0x1535a2c]. The predicted route of a bot's hit (GUESS, from the 0x7e1700
      trace: kbr_f4_route in klbrain_logic.h; whether the station is 'remote' (0x7de570) is not read, so a set station with a non-zero id is 'undetermined'). */
#define KLBR_F4_LOGMAX 60
static int klbr_f4on;
static DWORD klbr_f4_p138[KLBR_MAX], klbr_f4_pe8[KLBR_MAX]; static BYTE klbr_f4_have[KLBR_MAX];
static long klbr_f4_ni, klbr_f4_nv, klbr_f4_samples, klbr_f4_d138, klbr_f4_de8, klbr_f4_unres, klbr_f4_b12, klbr_f4_route[4];
static DWORD klbr_f5_f4own[KLBR_MAX];      /* FireProbe5: what FireProbe4 resolved as the owner of the item (0x8ccde0 of [item+0x5c]) at its last sample, per bot */
static void klbr_f4_sample(int ix, struct klbr_s *e, DWORD self, DWORD body)      /* game thread, read only */
{
    DWORD F, item, h, owner = 0, o4 = 0, o3c = 0, ovt = 0, c138, ce8, d138 = 0, de8 = 0, g160, g44, p2640, p265c, cap, fcnt, m98, m9c;
    DWORD hp, sm, st = 0, st14 = 0, bst = 0; WORD w3a = 0; BYTE bits[4]; int b12, hpok, route, hum;
    float hpv = 0.0f;
    (void)e;
    if (!klbr_f4on || ix < 0 || ix >= KLBR_MAX) return;
    klbr_f4_samples++;
    F = klbr_f3_d(self + 0x6a0); item = F > 0xffff ? klbr_f3_d(F + 4) : 0;
    if (item > 0xffff) {      /* counts and deltas on every sample; only the line printing is capped */
        DWORD sub, a3c, a40; BYTE b4 = 0xff;
        h = klh_rd32(item + 0x5c);
        if (h && klbr_fp_flt < 3) { __try { owner = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { owner = 0; klbr_fp_flt++; } }
        if (owner <= 0xffff) klbr_f4_unres++;
        klbr_f5_f4own[ix] = owner;
        sub = owner > 0xffff ? owner : body;
        o4 = sub > 0xffff ? klh_rd32(sub + 4) : 0; o3c = o4 > 0xffff ? klh_rd32(o4 + 0x3c) : 0; ovt = sub > 0xffff ? klh_rd32(sub) : 0;
        b12 = kbr_f4_bit(o3c, 12); if (b12) klbr_f4_b12++;
        c138 = klh_rd32(item + 0x138); ce8 = klh_rd32(item + 0xe8);
        d138 = kbr_f4_delta(klbr_f4_have[ix], klbr_f4_p138[ix], c138); de8 = kbr_f4_delta(klbr_f4_have[ix], ce8, klbr_f4_pe8[ix]);      /* +0xe8 falls as shots are taken: delta = previous - current */
        klbr_f4_d138 += (long)d138; klbr_f4_de8 += (long)de8;
        g160 = klh_rd32(item + 0x160); p2640 = KLBR_RDG(0xdd2640); g44 = p2640 > 0xffff ? klh_rd32(p2640 + 0x44) : 0;
        p265c = KLBR_RDG(0xdd265c); cap = p265c > 0xffff ? klh_rd32(p265c + 0x8b4) : 0; fcnt = KLBR_RDG(0x1535230); m98 = KLBR_RDG(0x153a898); m9c = KLBR_RDG(0x153a89c);
        bits[0] = bits[1] = bits[2] = bits[3] = 0xff;
        a3c = KLBR_RDG(0x1535a3c); a40 = KLBR_RDG(0x1535a40); klh_rd(item + 0xe4, &b4, 1);
        if (klbr_f4_ni < KLBR_F4_LOGMAX) {
        klh_rd(item + 0xed, &bits[0], 1); klh_rd(item + 0xef, &bits[1], 1); klh_rd(item + 0x136, &bits[2], 1); klh_rd(item + 0x137, &bits[3], 1);
        klog("brain: traitor fireprobe4 item: bot %d item %08lx [+0x138](0x4cb7a0 calls) %lu (+%lu since the last sample) [+0xe8](pending) %lu (-%lu) byte[+0xe4] %02x bytes +0xed %02x +0xef %02x +0x136 %02x +0x137 %02x float+0xf0 %.3f [+0x104] %08lx [+0x160] %08lx vs [[0xdd2640]+0x44] %08lx (%s, GUESS unsigned compare); "
             "owner handle [+0x5c] %08lx -> %s %08lx (vt %08lx) [owner+4] %08lx [[owner+4]+0x3c] %08lx bit12 %d (0 = 0x4cb7a0 fires nothing unless the ZLNKOBJ type test passes: masks [0x153a898] %08lx [0x153a89c] %08lx, vt+0x30 not called); [0x1535230] %lu vs [[0xdd265c]+0x8b4] %lu (%s, GUESS; 0x488ad0 bypasses the cap via the pair [0x1535a40] %08lx / [0x1535a3c] %08lx)",
             ix, (unsigned long)item, (unsigned long)c138, (unsigned long)d138, (unsigned long)ce8, (unsigned long)de8, (unsigned)b4, (unsigned)bits[0], (unsigned)bits[1], (unsigned)bits[2], (unsigned)bits[3], klbr_fp_f(klh_rd32(item + 0xf0)), (unsigned long)klh_rd32(item + 0x104),
             (unsigned long)g160, (unsigned long)g44, g160 >= g44 ? ">=" : "<", (unsigned long)h, owner > 0xffff ? "owner" : "UNRESOLVED, using the bot body", (unsigned long)sub, (unsigned long)ovt, (unsigned long)o4, (unsigned long)o3c, b12,
             (unsigned long)m98, (unsigned long)m9c, (unsigned long)fcnt, (unsigned long)cap, fcnt < cap ? "below the cap" : "AT/OVER the cap", (unsigned long)a40, (unsigned long)a3c);
        klbr_f4_ni++;
        }
        klbr_f4_p138[ix] = c138; klbr_f4_pe8[ix] = ce8; klbr_f4_have[ix] = 1;
    }
    hp = klbr_f3_d(self + 0xac); hum = hp > 0xffff && klh_pvt(hp) == 0x00bb45f4u;
    if (hum && klbr_f4_nv < KLBR_F4_LOGMAX) {
        DWORD p54 = klh_rd32(hp + 0x54), b438 = klh_rd32(hp + 0x438); int bit18 = kbr_f4_bit(b438, 18);
        st = klh_rd32(hp + 0x274c); st14 = st > 0xffff ? klh_rd32(st + 0x14) : 0; if (p54 > 0xffff) klh_rd(p54 + 0x3a, &w3a, 2);
        hpok = klbr_hp_read(hp, &hpv);
        bst = body > 0xffff ? klh_rd32(body + 0x274c) : 0; sm = KLBR_RDG(0x168e598);
        route = kbr_f4_route(sm > 0xffff ? klh_rd32(sm + 0x54) : 0, bit18, st > 0xffff, st14, KLBR_RDG(0x168fd00)); klbr_f4_route[route]++;      /* exact since FireProbe5: 0x7e1700 / 0x7de570 / 0x9425a0 read from the disassembly (kbr_f5_route); local station id = [0x168fd00] (0x94bc10 with 0x744a40() == 0) */
        klog("brain: traitor fireprobe4 victim: bot %d holder %08lx (ZFFPlayer) [+0x438] %08lx bit18 %d [+0x274c] %08lx [[+0x274c]+0x14] %08lx [+0x54] %08lx word[[+0x54]+0x3a] %04x (non-zero = 0x458880 skips the hit) hp %.1f%s [+0x774] %08lx; bot [body+0x274c] %08lx [body+0x774] %08lx; "
             "session sm %08lx [+0x54] %08lx [+0x5c] %08lx [+0x70] %08lx; [0x1535a2c] %08lx; local station id [0x168fd00] %08lx; route 0x7e1700 -> 0x7de570 -> 0x9425a0 (exact for a bot attacker): %s",
             ix, (unsigned long)hp, (unsigned long)b438, bit18, (unsigned long)st, (unsigned long)st14, (unsigned long)p54, (unsigned)w3a, (double)hpv, hpok ? "" : " (unreadable)", (unsigned long)klh_rd32(hp + 0x774), (unsigned long)bst, (unsigned long)(body > 0xffff ? klh_rd32(body + 0x774) : 0),
             (unsigned long)sm, (unsigned long)(sm > 0xffff ? klh_rd32(sm + 0x54) : 0), (unsigned long)(sm > 0xffff ? klh_rd32(sm + 0x5c) : 0), (unsigned long)(sm > 0xffff ? klh_rd32(sm + 0x70) : 0), (unsigned long)KLBR_RDG(0x1535a2c), (unsigned long)KLBR_RDG(0x168fd00), kbr_f4_route_name(route));
        klbr_f4_nv++;
    }
}
static void klbr_f4_summary(void)      /* at round end */
{
    if (klbr_f4on)
        klog("brain: traitor fireprobe4 round: samples %ld item lines %ld victim lines %ld; item [+0x138] (0x4cb7a0 calls) rose by %ld, [+0xe8] fell by %ld between samples; owner unresolved %ld, bit 12 set %ld; victim routes (exact for a bot attacker): apply-local (bit 18) %ld, drop (station remote) %ld, apply %ld, apply (session not networked) %ld",
             klbr_f4_samples, klbr_f4_ni, klbr_f4_nv, klbr_f4_d138, klbr_f4_de8, klbr_f4_unres, klbr_f4_b12, klbr_f4_route[0], klbr_f4_route[1], klbr_f4_route[2], klbr_f4_route[3]);
    klbr_f4_ni = klbr_f4_nv = klbr_f4_samples = klbr_f4_d138 = klbr_f4_de8 = klbr_f4_unres = klbr_f4_b12 = 0; memset(klbr_f4_route, 0, sizeof klbr_f4_route);
    memset(klbr_f4_have, 0, sizeof klbr_f4_have);
}
/* OnlineBrainTraitorFireProbe5 (11-04, after bs32: FireProbe4's owner resolution looked wrong; TEST build only for part 1; recommended off; needs FireProbe, so AttackHandle; host only). Measures from the game's own registers
   instead of re-deriving. Part 3 (FireProbe4's victim line) is above. SITE CHECK 11-04 against kl2.exe build 0490: 0x4cc389 is in 0x4cb7a0 (the per-shot routine, called on the item), after the ray/projectile choice (byte [esp+0x17]) at 0x4cc377..0x4cc384:
       4cc389: cmp byte ptr [esp+0x1f], 0   (80 7c 24 1f 00)     4cc38e: je 0x4cc9d2 (0f 84 3e 06 00 00)     then 4cc394 mov eax, [esp+0x54] (the owner, so [esp+0x54] is the owner at this site)
   The 11 bytes are exactly 80 7c 24 1f 00 0f 84 3e 06 00 00 (read from the exe, and checked again at run time before patching). 0x4cc389 lies between the hashed ranges [0x4c5000,0x4ca000) and [0x4cd000,0x4cf000): UNHASHED
   (klh_is_hashed and the test below). The frame is the same as at 0x4cb7c5 (mov [esp+0x54], edi: owner = 0x6ee930(item), which is 0x6ee930(item) = [item+0x5c] then 0x8ccde0 (entry+0x60), so the register owner and a fresh lookup agree by construction; 'differs' would mean FireProbe4's item ([[s+0x6a0]+4]) is not the this of 0x4cb7a0) and 0x4cb815 (mov [esp+0x1f], bl: the gate; 0x4cb829 sets it to 1 when the
   class mask matches): no push/pop is outstanding on the path (the same [esp+0x1f] / [esp+0x17] offsets are used before and after), and esi is only ever written by 'mov esi, ecx' at 0x4cb7a9, so ESI = the item.
   1. GATE COUNTER: ONE detour at 0x4cc389 steals only the 5-byte cmp (the je after it has a relative operand and is NOT stolen: the stub jumps back to 0x4cc38e). The stub (kbr_f3_emit) saves flags and registers around the handler,
      so the cmp is re-executed with fresh flags before the je. Handler: owner = [esp+0x54], item = ESI, gate = byte [esp+0x1f] (esp = the saved original ESP of the stub registers). Per round: gate pass / fail for a MARKED traitor
      bot (owner is a marked body, or item is a marked bot's item) versus all others. The first few samples log owner / item / [item+0x5c], 0x8ccde0([item+0x5c]) re-resolved now (the same pure lookup FireProbe4 calls) and
      compared with the register, what FireProbe4 resolved at its last sample, the owner's vtable, the ADDRESS of its vt+0x30 slot and the value stored there (read, NOT called), [owner+4], [[owner+4]+0x3c] and bit 12.
   2. SLOT 422 COUNTER: klnetsmooth.c's private ZFFPlayer vtable (klbr_f5_attach): if slot 422 holds 0x7e1700 and [NetSmooth] is on, a wrapper counts every victim hit and calls the original unchanged (arguments and result untouched).
      LIMIT: the private table is given to REMOTE players only, so only hits on remote-seat humans are seen (the host-local human is never swapped). Per call: attacker class, marked or not, bit 18, station and its id, local id, role,
      the predicted route (kbr_f5_route) and the victim's health before and after the original. Else logged once as inert.
   Log: "fireprobe5 gate:" / "fireprobe5 hit:" lines (capped per round) and "fireprobe5 round:". */
#define KLBR_F5_SITE 0x4cc389
#define KLBR_F5_LOGMAX 30
static const BYTE klbr_f5_bytes[11] = { 0x80, 0x7c, 0x24, 0x1f, 0x00, 0x0f, 0x84, 0x3e, 0x06, 0x00, 0x00 };
static int klbr_f5on, klbr_f5_state, klbr_f5_wrapped;      /* state: 0 not tried, 1 detour installed, -1 refused / bytes differ; wrapped: slot 422 of the private table is ours */
static BYTE *klbr_f5_stub;
static DWORD klbr_f5_soldier[KLBR_MAX];
static long klbr_f5_gate_unread, klbr_f5_nla;      /* gate byte unreadable (not counted as pass or fail); unmatched samples whose owner has the ZFFActor vtable (logged so the register is visible even when marking misses) */
static DWORD klbr_f5_body[KLBR_MAX], klbr_f5_item[KLBR_MAX];     /* the marked bots' bodies ([soldier+0x40]) and items ([[soldier+0x6a0]+4]) as of their last slot-113 call */
static long klbr_f5_gate[4], klbr_f5_by_owner, klbr_f5_by_item, klbr_f5_nlm, klbr_f5_nlo, klbr_f5_res_same, klbr_f5_res_diff, klbr_f5_res_none;
static void __cdecl klbr_f5_gatehit(int id, KLBR_F3REGS *r)      /* called by the stub on the game thread; reads only (the lookup 0x8ccde0 is the one pure call, under __try) */
{
    DWORD sp, owner, item, h, res = 0, vt, slot, o4, o3c; BYTE gate = 0xff; int i, bo = 0, bi = 0, marked, ix = -1, kind, gok, actor;
    (void)id;
    if (!klbr_f5on || !r) return;
    sp = r->esp; owner = klh_rd32(sp + 0x54); item = r->esi; gok = klh_rd(sp + 0x1f, &gate, 1);
    for (i = 0; i < KLBR_MAX; i++) {
        if (klbr_f5_body[i] && klbr_f5_body[i] == owner) { bo = 1; ix = i; }
        if (klbr_f5_item[i] && klbr_f5_item[i] == item) { bi = 1; if (ix < 0) ix = i; }
    }
    marked = bo || bi; kind = kbr_f5_kind(marked, gate);
    if (gok) klbr_f5_gate[kind]++; else klbr_f5_gate_unread++;
    if (bo) klbr_f5_by_owner++; if (bi) klbr_f5_by_item++;
    actor = !marked && owner > 0xffff && klh_pvt(owner) == 0x00bb3bacu;      /* an unmatched ZFFActor owner may still be a traitor body (marking missed) */
    if (marked ? klbr_f5_nlm >= 6 : actor ? klbr_f5_nla >= 6 : klbr_f5_nlo >= 3) return;
    if (marked) klbr_f5_nlm++; else if (actor) klbr_f5_nla++; else klbr_f5_nlo++;
    h = item > 0xffff ? klh_rd32(item + 0x5c) : 0;
    if (h && klbr_fp_flt < 3) { __try { res = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { res = 0; klbr_fp_flt++; } }
    if (h && owner == res) klbr_f5_res_same++; else if (h && res) klbr_f5_res_diff++; else klbr_f5_res_none++;
    vt = owner > 0xffff ? klh_rd32(owner) : 0; slot = vt > 0xffff ? vt + 0x30 : 0; o4 = owner > 0xffff ? klh_rd32(owner + 4) : 0; o3c = o4 > 0xffff ? klh_rd32(o4 + 0x3c) : 0;
    klog("brain: traitor fireprobe5 gate: %s bot %d (by owner %d, by item %d) byte[esp+0x1f] %02x (%s) owner [esp+0x54] %08lx item(esi) %08lx [item+0x5c] %08lx 0x8ccde0 now %08lx (%s) FireProbe4's last owner %08lx; owner [owner] %08lx slot vt+0x30 at %08lx = %08lx (not called) [owner+4] %08lx [[owner+4]+0x3c] %08lx bit12 %d; esp %08lx [esp+0x17](ray=1) %02x",
         marked ? "MARKED" : actor ? "other(ZFFActor owner)" : "other", ix, bo, bi, (unsigned)gate, gate ? "pass: shot fires" : "FAIL: sound + message only", (unsigned long)owner, (unsigned long)item, (unsigned long)h, (unsigned long)res,
         !h ? "no handle" : owner == res ? "same as the register" : res ? "DIFFERS from the register" : "lookup gave 0", (unsigned long)(ix >= 0 ? klbr_f5_f4own[ix] : 0), (unsigned long)vt, (unsigned long)slot,
         (unsigned long)(slot ? klh_rd32(slot) : 0), (unsigned long)o4, (unsigned long)o3c, kbr_f4_bit(o3c, 12), (unsigned long)sp, (unsigned)klbr_f3_b(sp + 0x17));
}
static void klbr_f5_install(void)      /* once, at the first marked-bot call (game thread); a refusal is final for this run */
{
    BYTE cur[11] = { 0 }, jmp[5]; BYTE *at; DWORD stub; int n;
    if (klbr_f5_state) return;
    klbr_f5_state = -1;
    at = KLH_VA(KLBR_F5_SITE);
    if (klh_is_hashed(KLBR_F5_SITE, 11)) { klog("brain: traitor fireprobe5: 0x4cc389 is inside a hashed range: gate counter NOT installed"); return; }
    if (!klh_rd((DWORD_PTR)at, cur, 11) || memcmp(cur, klbr_f5_bytes, 11)) { klog("brain: traitor fireprobe5: the 11 bytes at 0x4cc389 are not 80 7c 24 1f 00 0f 84 3e 06 00 00 (got %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x): gate counter NOT installed",
        cur[0], cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7], cur[8], cur[9], cur[10]); return; }
    if (!klbr_f5_stub && !(klbr_f5_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: traitor fireprobe5: no memory for the stub: gate counter off"); return; }
    stub = (DWORD)(DWORD_PTR)klbr_f5_stub;
    n = kbr_f3_emit(klbr_f5_stub, stub, 2, (DWORD)(DWORD_PTR)klbr_f5_gatehit, klbr_f5_bytes, 5, (DWORD)(DWORD_PTR)(at + 5));      /* only the cmp is stolen: back to the je at 0x4cc38e */
    if (!n) return;
    kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, 5);
    if (klh_poke(at, klbr_f5_bytes, 5, jmp, 5, "brain: FireProbe5 gate counter")) { klbr_f5_state = 1; klog("brain: traitor fireprobe5: gate counter on 0x4cc389 (cmp byte [esp+0x1f],0) installed, stub %d bytes", n); }
    else klog("brain: traitor fireprobe5: gate counter NOT installed (refused by the patch guard - a SHIP build writes no code - or the bytes differ)");
}
static void klbr_f5_track(int ix, DWORD self, DWORD body)      /* every slot-113 call of a marked bot FireProbe sees: remember its body and item (the counters filter on them) and install the detour once */
{
    DWORD F;
    if (!klbr_f5on || ix < 0 || ix >= KLBR_MAX) return;
    klbr_f5_install();
    klbr_f5_body[ix] = body > 0xffff ? body : 0; klbr_f5_soldier[ix] = self > 0xffff ? self : 0;
    F = klh_rd32(self + 0x6a0); klbr_f5_item[ix] = F > 0xffff ? klh_rd32(F + 4) : 0;
}

typedef void (__fastcall *klbr_f5_fn)(void *self, void *edx, DWORD rec);
static klbr_f5_fn klbr_f5_orig;
typedef struct { DWORD V, A, role, b438, vst, vid, ast, aid, local, sm, rec; int bit18, aset, aplayer, aclass, marked, route, hp0ok; float hp0; } KLBR_F5H;
static long klbr_f5_hit_n, klbr_f5_hit_m, klbr_f5_rt[6], klbr_f5_rtm[6], klbr_f5_cls[4], klbr_f5_drop, klbr_f5_same, klbr_f5_unread, klbr_f5_mis_a, klbr_f5_mis_d, klbr_f5_nlog, klbr_f5_nlogo, klbr_f5_flt;
static void klbr_f5_pre(void *self, DWORD rec, KLBR_F5H *k)      /* reads only; every read is klh_rd (safe), so no fault is expected - the caller still wraps it in __try */
{
    int i; DWORD vt;
    memset(k, 0, sizeof *k);
    k->V = (DWORD)(DWORD_PTR)self; k->rec = rec;
    k->sm = KLBR_RDG(0x168e598); k->role = k->sm > 0xffff ? klh_rd32(k->sm + 0x54) : 0;
    k->b438 = klh_rd32(k->V + 0x438); k->bit18 = kbr_f4_bit(k->b438, 18);
    k->vst = klh_rd32(k->V + 0x274c); k->vid = k->vst > 0xffff ? klh_rd32(k->vst + 0x14) : 0;
    k->local = KLBR_RDG(0x168fd00);
    k->A = rec > 0xffff ? klh_rd32(rec) : 0; k->aset = k->A > 0xffff;
    if (k->aset) {
        vt = klh_pvt(k->A);
        k->aplayer = vt == 0x00bb45f4u;      /* GUESS: 0x7e1750's class-mask test (vt+0x30 & [0x1548c80] == [0x1548c7c]) is 'a ZFFPlayer'; the vtable is compared instead of calling it */
        k->aclass = k->aplayer ? 1 : vt == 0x00bb3bacu ? 2 : 3;      /* 1 ZFFPlayer, 2 ZFFActor (the bots' bodies, vt 0xbb3bac), 3 other; 0 = no attacker */
        k->ast = klh_rd32(k->A + 0x274c); k->aid = k->ast > 0xffff ? klh_rd32(k->ast + 0x14) : 0;
        for (i = 0; i < KLBR_MAX; i++) if ((klbr_f5_body[i] && klbr_f5_body[i] == k->A) || (klbr_f5_soldier[i] && klbr_f5_soldier[i] == k->A)) k->marked = 1;      /* also the soldier itself (GUESS: a record may name the soldier, not its body) */
    }
    k->route = kbr_f5_route(k->role, k->bit18, k->aset, k->aplayer, k->ast > 0xffff, k->aid, k->vst > 0xffff, k->vid, k->local);
    k->hp0ok = klbr_hp_read(k->V, &k->hp0);
}
static void __fastcall klbr_f5_hit(void *self, void *edx, DWORD rec)      /* slot 422 of the private ZFFPlayer vtable: count, call the original UNCHANGED, read the health after */
{
    KLBR_F5H k; float hp1 = 0.0f; int ok = 0, have = 0, hp1ok;
    memset(&k, 0, sizeof k);
    if (klbr_f5on && klbr_f5_flt < 3) { __try { klbr_f5_pre(self, rec, &k); have = 1; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f5_flt++; have = 0; } }
    klbr_f5_orig(self, edx, rec);      /* arguments and result are never changed */
    if (!have) return;
    __try {
        hp1ok = klbr_hp_read(k.V, &hp1); ok = k.hp0ok && hp1ok;
        klbr_f5_hit_n++; klbr_f5_rt[k.route]++; klbr_f5_cls[k.aclass]++;
        if (k.marked) {
            int drop = ok && hp1 < k.hp0 - 0.001f;
            klbr_f5_hit_m++; klbr_f5_rtm[k.route]++;
            if (!ok) klbr_f5_unread++; else if (drop) klbr_f5_drop++; else klbr_f5_same++;
            if (ok && k.route != 3 && kbr_f5_applies(k.route) && !drop) klbr_f5_mis_a++;      /* predicted to apply, health unchanged: another gate (0x458880 / 0x6e3400 ...) or a later write; route 3 (send block) is 'unknown', never counted */
            if (ok && k.route != 3 && !kbr_f5_applies(k.route) && drop) klbr_f5_mis_d++;     /* predicted to drop, health fell: the route model is wrong */
        }
        if (k.marked ? klbr_f5_nlog < KLBR_F5_LOGMAX : klbr_f5_nlogo < 6) {
            if (k.marked) klbr_f5_nlog++; else klbr_f5_nlogo++;
            klog("brain: traitor fireprobe5 hit: %s attacker %08lx (class %s, vt %08lx) victim %08lx role %lu [victim+0x438] %08lx bit18 %d victim station %08lx id %08lx; attacker station %08lx id %08lx; local id [0x168fd00] %08lx; predicted route %d = %s; victim hp %.1f -> %.1f%s%s",
                 k.marked ? "MARKED" : "other", (unsigned long)k.A, k.aclass == 1 ? "ZFFPlayer" : k.aclass == 2 ? "ZFFActor" : k.aclass == 3 ? "other" : "none", (unsigned long)(k.aset ? klh_rd32(k.A) : 0), (unsigned long)k.V, (unsigned long)k.role, (unsigned long)k.b438, k.bit18, (unsigned long)k.vst, (unsigned long)k.vid,
                 (unsigned long)k.ast, (unsigned long)k.aid, (unsigned long)k.local, k.route, kbr_f5_route_name(k.route), (double)k.hp0, (double)hp1, ok ? "" : " (unreadable)",
                 !ok ? "" : k.route == 3 ? (hp1 < k.hp0 - 0.001f ? " (send block: hp fell by another path)" : " (send block: hp unchanged)") : kbr_f5_applies(k.route) ? (hp1 < k.hp0 - 0.001f ? " (applied, hp fell)" : " (predicted apply, hp UNCHANGED)") : (hp1 < k.hp0 - 0.001f ? " (predicted DROP but hp FELL: model wrong)" : " (dropped, hp unchanged)"));
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f5_flt++; }
}
static void klbr_f5_attach(DWORD *vt)      /* klnetsmooth.c, before any object points at the private table (game thread): wrap slot 422 */
{
    if (!klbr_f5on) return;
    if (vt[422] != (DWORD)(DWORD_PTR)KLH_VA(0x7e1700)) { klog("brain: traitor fireprobe5: part 2 inert: private ZFFPlayer slot 422 holds %08lx, not 0x7e1700", (unsigned long)vt[422]); return; }
    klbr_f5_orig = (klbr_f5_fn)(DWORD_PTR)vt[422]; vt[422] = (DWORD)(DWORD_PTR)klbr_f5_hit; klbr_f5_wrapped = 1;
    klog("brain: traitor fireprobe5: slot 422 (0x7e1700) of the private ZFFPlayer vtable wrapped (counting only; remote-seat victims only)");
}
static void klbr_f5_netsmooth_init(int ns_on)      /* klnetsmooth_init, once: part 2 needs [NetSmooth] Enable=1 */
{
    if (klbr_f5on && !ns_on) klog("brain: traitor fireprobe5: part 2 (slot 422 counter) inert: [NetSmooth] Enable is off (no private ZFFPlayer vtable)");
}
static void klbr_f5_summary(void)      /* at round end */
{
    if (klbr_f5on) {
        klog("brain: traitor fireprobe5 round: gate byte [esp+0x1f] at 0x4cc389 (detour %s): MARKED pass %ld fail %ld, other pass %ld fail %ld, gate unreadable %ld (matched by owner %ld, by item %ld); owner register vs a fresh 0x8ccde0([item+0x5c]) in the logged samples: same %ld, differs %ld, none %ld",
             klbr_f5_state > 0 ? "on" : "NOT installed", klbr_f5_gate[0], klbr_f5_gate[1], klbr_f5_gate[2], klbr_f5_gate[3], klbr_f5_gate_unread, klbr_f5_by_owner, klbr_f5_by_item, klbr_f5_res_same, klbr_f5_res_diff, klbr_f5_res_none);
        klog("brain: traitor fireprobe5 round: slot 422 %s: hits %ld (marked %ld); attacker class none %ld ZFFPlayer %ld ZFFActor %ld other %ld; routes (all) apply-nonet %ld apply-bit18 %ld drop-att %ld send %ld drop-victim %ld apply %ld; routes (marked) %ld %ld %ld %ld %ld %ld; marked hp fell %ld, unchanged %ld, unreadable %ld; predicted apply but hp unchanged %ld, predicted drop but hp fell %ld; faults %ld",
             klbr_f5_wrapped ? "wrapped" : "inert", klbr_f5_hit_n, klbr_f5_hit_m, klbr_f5_cls[0], klbr_f5_cls[1], klbr_f5_cls[2], klbr_f5_cls[3],
             klbr_f5_rt[0], klbr_f5_rt[1], klbr_f5_rt[2], klbr_f5_rt[3], klbr_f5_rt[4], klbr_f5_rt[5], klbr_f5_rtm[0], klbr_f5_rtm[1], klbr_f5_rtm[2], klbr_f5_rtm[3], klbr_f5_rtm[4], klbr_f5_rtm[5],
             klbr_f5_drop, klbr_f5_same, klbr_f5_unread, klbr_f5_mis_a, klbr_f5_mis_d, klbr_f5_flt);
    }
    memset(klbr_f5_gate, 0, sizeof klbr_f5_gate); klbr_f5_gate_unread = klbr_f5_nla = 0; memset(klbr_f5_soldier, 0, sizeof klbr_f5_soldier); klbr_f5_by_owner = klbr_f5_by_item = klbr_f5_nlm = klbr_f5_nlo = klbr_f5_res_same = klbr_f5_res_diff = klbr_f5_res_none = 0;
    klbr_f5_hit_n = klbr_f5_hit_m = klbr_f5_drop = klbr_f5_same = klbr_f5_unread = klbr_f5_mis_a = klbr_f5_mis_d = klbr_f5_nlog = klbr_f5_nlogo = 0;
    memset(klbr_f5_rt, 0, sizeof klbr_f5_rt); memset(klbr_f5_rtm, 0, sizeof klbr_f5_rtm); memset(klbr_f5_cls, 0, sizeof klbr_f5_cls);
    memset(klbr_f5_body, 0, sizeof klbr_f5_body); memset(klbr_f5_item, 0, sizeof klbr_f5_item); memset(klbr_f5_f4own, 0, sizeof klbr_f5_f4own);
}
/* OnlineBrainTraitorGateForce (11-04, after bs33; UNTESTED, recommended off, CHANGES behaviour; needs AttackHandle; host only, online only; needs [BotFill] OnlineCopToBot, whose private ZFFActor table it uses).
   bs33: every host-side AI shot fails the per-shot gate 0x4cc389 ([esp+0x1f] = 0: sound + message only, no ray, no projectile). The byte is set at 0x4cb802..0x4cb815 from bit 12 of [[owner+4]+0x3c] (GUESS: 'the node has
   a live render-geometry entry', 0 for the host's online bots), and 0x4cb819 then calls the owner's vt+0x30 (a ZFFActor class getter, stock 0x557ba0 = mov eax,[0x1547b24]; ret): if (result & [0x153a89c]) == [0x153a898]
   (the ZLNKOBJ test, 0xfff / 0x77c) the game ITSELF writes the gate byte 1 (0x4cb829) and takes the muzzle path 0x4cb838, which the later re-tests (0x4cb970, 0x4cc655) agree with. So the fix is a DATA write, no code patch and
   no node flag, and it ships (a SHIP build writes no code, klh_poke refuses): slot 12 (vt+0x30) of the ONE private ZFFActor table klbalance.c OnlineCopToBot made (klr_cb_vt, our own memory) is wrapped. The wrapper calls the real
   getter and changes the answer ONLY when its return address is 0x4cb81b (that one call), the owner is a marked traitor bot or, with OnlineBrainTraitorGateForceAll=1, any bot on that table (klr_cb.inst), and the host is online.
   Every other caller of vt+0x30 (class tests everywhere) gets the real value. Needs the bot to be on the private table (a bot on the stock table 0xbb3bac cannot be reached without a code patch: counted as 'stock', logged);
   the stock table is never written. GUESS: nothing else on 0x4cb7a0's path reads the class id of the owner. Damage then goes the host's ordinary ray route (0x713e80 -> victim chain); a double hit on the client is not
   expected (bench: hp on both seats). Review 11-04 limits: the forced branch (0x4cb838, item vt+0x250 muzzle) is NOT verified safe for a node with bit 12 = 0 (UNTESTED; watch for faults/garbage origins); a remote-seat victim still drops the hit
   (kbr_f4_route 1), so expect only the host seat's hp to fall; forced only on the game thread, never for cops (klr_bo_is_cop), the marked entry must still be live; the wrapper does not check the session itself (klr_cb_tick
   only builds the table online on the host); GateForceAll changes AI-heister balance (they start hurting cops/humans). Log: "brain: traitor gateforce:" (install, first 6 forced calls) and a round total (calls at the site, forced, not marked, other bots, stock table). */
#define KLBR_GF_SLOT 12
#define KLBR_GF_GETTER 0x557ba0u
#define KLBR_GF_RET 0x4cb81bu
static int klbr_gfon, klbr_gfall, klbr_gf_state;      /* state: 0 not tried, 1 slot wrapped, -1 refused */
typedef DWORD (__fastcall *klbr_gf_fn)(DWORD self, DWORD edx);
static klbr_gf_fn klbr_gf_org;
static DWORD klbr_gf_body[KLBR_MAX];      /* the marked bots' bodies ([soldier+0x40]) as of their last slot-113 call */
static volatile LONG klbr_gf_site, klbr_gf_forced, klbr_gf_unmarked, klbr_gf_otherbot, klbr_gf_offthread, klbr_gf_noval;
static long klbr_gf_stock, klbr_gf_calls, klbr_gf_tracked;
static DWORD __fastcall klbr_gf_cls(DWORD self, DWORD edx)      /* slot 12 of the private ZFFActor table (vt+0x30): the real getter first, always */
{
    DWORD r = klbr_gf_org(self, edx), ra = (DWORD)(DWORD_PTR)_ReturnAddress(), val, mask, f; int i, marked = 0, isbot = 0;
    if (ra != (DWORD)(DWORD_PTR)KLH_VA(KLBR_GF_RET) || !klbr_gfon) return r;      /* every other caller: untouched */
    InterlockedIncrement(&klbr_gf_site);
    val = KLBR_RDG(0x153a898); mask = KLBR_RDG(0x153a89c);
    if (klbr_game_tid && GetCurrentThreadId() != klbr_game_tid) { InterlockedIncrement(&klbr_gf_offthread); return r; }      /* review 11-04: never force off the game thread (the muzzle computation would race the scene) */
    if (klr_bo_is_cop(self)) { InterlockedIncrement(&klbr_gf_unmarked); return r; }      /* review 11-04: cops share the private table; never touched */
    for (i = 0; i < KLBR_MAX; i++) if (klbr_gf_body[i] && klbr_gf_body[i] == self && klbr_t[i].state == 1 && klbr_t[i].traitor) marked = 1;      /* review 11-04: the entry must still be a live marked bot (a stale body address reused by another actor is not forced) */
    for (i = 0; i < KLR_CB_MAX; i++) if (klr_cb.inst[i] && klr_cb.inst[i] == self) isbot = 1;
    f = kbr_gf_force(1, klbr_gfall, marked, isbot, ra, ra, val, mask);
    if (!f) {
        if (!val || (val & mask) != val) InterlockedIncrement(&klbr_gf_noval);
        else if (isbot && !marked) InterlockedIncrement(&klbr_gf_otherbot);
        else if (!marked) InterlockedIncrement(&klbr_gf_unmarked);
        return r;
    }
    if (InterlockedIncrement(&klbr_gf_forced) <= 6) klog("brain: traitor gateforce: owner %08lx (%s) vt+0x30 at the 0x4cb819 call: real answer %08lx -> %08lx (ZLNKOBJ value; the game sets its gate byte to 1 and fires)", (unsigned long)self, marked ? "marked traitor bot" : "bot on the private table (All)", (unsigned long)r, (unsigned long)f);
    return f;
}
static void klbr_gf_apply(struct klbr_s *e, DWORD self)      /* game thread, after every slot-113 call of a bot (host only): remember a marked bot's body, wrap slot 12 once */
{
    int ix; DWORD body;
    if (!klbr_gfon || !klbr_cfh || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    if (e->state != 1 || !e->traitor) { klbr_gf_body[ix] = 0; return; }      /* review 11-04: unmarked / dead / reset: the body is forgotten at once */
    klbr_gf_calls++;
    body = klh_rd32(self + 0x40);
    if (body <= 0xffff) return;
    if (klbr_gf_body[ix] != body) klbr_gf_tracked++;
    klbr_gf_body[ix] = body;
    if (klh_rd32(body) != (DWORD)(DWORD_PTR)klr_cb_vt) { klbr_gf_stock++; if (klbr_gf_stock <= 3) klog("brain: traitor gateforce: bot %d body %08lx vtable %08lx is NOT the private ZFFActor table %08lx of OnlineCopToBot (ready %d; stock table is 0xbb3bac, anything else is another private table, e.g. a heap copy): this bot cannot be reached (the stock table needs a code patch; not done)", ix, (unsigned long)body, (unsigned long)klh_rd32(body), (unsigned long)(DWORD_PTR)klr_cb_vt, klr_cb.ready); }
    if (klbr_gf_state) return;
    if (!klr_cb.ready) return;      /* the private table is made by klbalance.c's tick: try again at the next call */
    klbr_gf_state = -1;
    if (klr_cb_vt[KLBR_GF_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(KLBR_GF_GETTER)) { klog("brain: traitor gateforce: private ZFFActor slot %d holds %08lx, not 0x557ba0: OnlineBrainTraitorGateForce does nothing", KLBR_GF_SLOT, (unsigned long)klr_cb_vt[KLBR_GF_SLOT]); return; }
    klbr_gf_org = (klbr_gf_fn)(DWORD_PTR)klr_cb_vt[KLBR_GF_SLOT];
    _ReadWriteBarrier();      /* klbr_gf_org must be visible before the wrapper can be called */
    klr_cb_vt[KLBR_GF_SLOT] = (DWORD)(DWORD_PTR)klbr_gf_cls; klbr_gf_state = 1;      /* our own memory (klr_cb.blk), no game byte written */
    klog("brain: traitor gateforce: slot %d (vt+0x30, 0x557ba0) of the private ZFFActor table %08lx wrapped; the answer changes only for the call at 0x4cb819 (host, %s)", KLBR_GF_SLOT, (unsigned long)(DWORD_PTR)klr_cb_vt, klbr_gfall ? "marked bots and every bot on the table" : "marked traitor bots only");
}
static void klbr_gf_summary(void)      /* at round end: the counts, then the per-round state cleared (the wrapper stays in the table, inert without bodies) */
{
    if (klbr_gfon) klog("brain: traitor gateforce round: slot %s; marked-bot slot-113 calls %ld, bodies tracked %ld, marked bots not on the private table (stock) %ld; the 0x4cb819 call seen %ld times: forced %ld (off-thread %ld), owner not a bot %ld, other bot (no All) %ld, no usable ZLNKOBJ value %ld",
        klbr_gf_state > 0 ? "wrapped" : "NOT wrapped", klbr_gf_calls, klbr_gf_tracked, klbr_gf_stock, (long)klbr_gf_site, (long)klbr_gf_forced, (long)klbr_gf_offthread, (long)klbr_gf_unmarked, (long)klbr_gf_otherbot, (long)klbr_gf_noval);
    memset(klbr_gf_body, 0, sizeof klbr_gf_body); klbr_gf_site = klbr_gf_forced = klbr_gf_unmarked = klbr_gf_otherbot = klbr_gf_offthread = klbr_gf_noval = 0; klbr_gf_calls = klbr_gf_tracked = klbr_gf_stock = 0;
}
/* OnlineBrainTraitorFireProbe6 (11-04, after bs34; TEST build only, UNTESTED, recommended off; READ ONLY toward the game: no game byte is written, the only game calls are the pure lookups 0x8ccde0 and a class getter vt+0x30, under __try).
   bs34: with GateForce every marked traitor shot passes the gate 0x4cc389 and the forced muzzle path does not crash, but the human's hp stays flat and the aim target [body+0x544] is 0 (holder ~53 m). Where does the shot GO?
   Independent of FireProbe / AttackHandle / GateForce, so it also covers Arcade (a non-networked session): every shot of every shooter is counted per round, tagged networked yes/no (role [sm+0x54] 2 or 3 = yes) and marked
   (a marked traitor bot, tracked from the slot-113 calls: needs the bot stack, i.e. online host; in Arcade 'marked' is always no) yes/no. Per shot (detail lines for marked shooters and for every Arcade shooter, the first KLBR_F6_LOGMAX per combination):
   SITES (all inside the per-shot routine 0x4cb7a0, unhashed range 0x4ca000-0x4cd000, bytes read from kl2.exe build 0490 and checked again at run time before any patch; the jump is padded with nops over the stolen bytes; no stolen byte has a relative operand and
   no jump of the routine targets the inside of a stolen range - checked against the disassembly 11-04). One stub per site (kbr_f3_emit: pushad, pushfd, handler(id, regs), popfd, popad, stolen bytes, jmp back); regs->esp is the ORIGINAL esp of the site.
     S1 id 1 0x4cb8b9  inc dword [esi+0x138]            (ff 86 38 01 00 00)  the join of both muzzle paths (0x4cb851 jmp here after the vt+0x250 call; the bl=0 path 0x4cb853 falls in): the muzzle transform is DONE.
        esi = item, [esp+0x54] = owner (set at 0x4cb7c5), bl = ebx&0xff = 'forced / muzzle path' (the test at 0x4cb834), muzzle position at [esp+0x60] (vec3) and orientation at [esp+0xc4] (3x3, 9 floats): the exact args of the call
        at 0x4cb83a..0x4cb84f (arg1 = esp+0xc4 pushed after one push, arg2 = esp+0x60; read from the disassembly). The 0x7cb080 branch is classified from READS (kbr_f6_branch) because 0x7cb080 itself is a hashed-range call target we do not hook.
     S2 id 2 0x4cc3a0  cmp byte [esp+0x17], 0           (80 7c 24 17 00)     right after 'call 0x4a30e0' (a relative call, so the NEXT instruction is stolen): eax = the 0x4a30e0 return (the shot descriptor), [esp+0x17] = ray flag (1 = ray 0x713e80, 0 = projectile 0x4cc655).
        Reached only when the gate passed (the je at 0x4cc38e jumps to 0x4cc9d2 otherwise), so S2 counts 'passed'.
     S4 id 4 0x4cc440  lea ecx, [esp+0xf4]               (8d 8c 24 f4 00 00 00)  just before 'call 0x713e80' (thiscall ecx=ebp, args pushed: edi, esp+0xf4 (-> vecA), eax (-> vecB), 0, 1): at this site esp is 12 below the frame base E that 0x4cc437
        uses, so vecA = [esp+0xf4], vecB = *eax, descriptor = edi. 0x713e80 takes arg2 = vecA as its FIRST parameter and arg3 = vecB as its second: A is probably the start and B the end (GUESS, review 11-04).
     S5 id 5 0x4cc450  mov ecx, esi ; mov [esp+0x18], eax (8b ce 89 44 24 18)  right after the call: eax = the REQUEST OBJECT taken from the ring buffer at [ebp+0x68] (review 11-04: NOT a hit entity; vt+0x78 is called on it at 0x4cc638 and the entity comes back in [esp+0x10]).
     S7 id 7 0x4cc644  mov ecx,[esp+0x10] ; test ecx,ecx (8b 4c 24 10 85 c9)  right after 'call [req vt+0x78]' (esp = E; no jump targets 0x4cc644 / 0x4cc648, checked 11-04): [esp+0x10] = the entity the ray hit (0 = no hit). The shot line is written here.
     S6 id 6 0x4cc65d  cmp dword [esi+0x114], 0          (83 be 14 01 00 00 00) the projectile path (0x4cc655: test ebx, ebx; je 0x4cc891; then this): counted, and the shot line written without a ray result.
        A projectile-path shot with ebx == 0 leaves at 0x4cc891 without S4 / S6: it counts as 'passed' only (the summary prints it as 'passed but neither ray nor projectile').
   Branch classes are only meaningful for bl = 1 shots (vt+0x250 is called only then; bl = 0 takes 0x4cb853: 0x7f07a0 then 0x8c51b0): those shots are class 0 'not via vt+0x250'.
   Only the game thread is handled (the tick records its id); the 5-7 byte code writes at install time cannot be made thread-safe (same exposure as FireProbe5). */
#define KLBR_F6_LOGMAX 8
#define KLBR_F6_NSITE 6      /* the FireProbe6 / RayAim sites; FireProbe7 adds a 7th (AimAt 0x70f130) */
#define KLBR_F6_NSITE_ALL 7
static int klbr_f6on, klbr_f6_state, klbr_f6_flt; static DWORD klbr_f6_tid;      /* tid: the game thread (set by the tick; the stub handler ignores every other thread) */      /* state: 0 not tried, 1 every site installed, 2 some sites, -1 none */
static int klbr_f6act, klbr_f7on, klbr_raon, klbr_f7_flt, klbr_ra_flt, klbr_ra_rowcfg = -1, klbr_ra_signcfg = 1, klbr_ra_spread = 3, klbr_ra_maxd = 6000, klbr_ra_site = 5, klbr_ra_chest = 130;      /* f6act: any of FireProbe6 / 7 / RayAim wants the sites */
static kbr_u32 klbr_ra_seed = 0x2545f491u;
static BYTE *klbr_f6_stub;
static DWORD klbr_f6_sold[KLBR_MAX];      /* the marked bots' soldier objects (FireProbe7: fire task fields) */
static DWORD klbr_f6_body[KLBR_MAX], klbr_f6_item[KLBR_MAX], klbr_f6_hold[KLBR_MAX];
typedef struct { DWORD site; int len; BYTE b[8]; int id; } KLBR_F6SITE;
static const KLBR_F6SITE klbr_f6_sites[KLBR_F6_NSITE_ALL] = {
    { 0x4cb8b9, 6, { 0xff, 0x86, 0x38, 0x01, 0x00, 0x00 }, 1 },
    { 0x4cc3a0, 5, { 0x80, 0x7c, 0x24, 0x17, 0x00 }, 2 },
    { 0x4cc440, 7, { 0x8d, 0x8c, 0x24, 0xf4, 0x00, 0x00, 0x00 }, 4 },
    { 0x4cc450, 6, { 0x8b, 0xce, 0x89, 0x44, 0x24, 0x18 }, 5 },
    { 0x4cc65d, 7, { 0x83, 0xbe, 0x14, 0x01, 0x00, 0x00, 0x00 }, 6 },
    { 0x4cc644, 6, { 0x8b, 0x4c, 0x24, 0x10, 0x85, 0xc9 }, 7 },
    { 0x70f130, 5, { 0x56, 0x8b, 0xf1, 0x8b, 0x06 }, 8 } };      /* FireProbe7 only: AimAt entry (push esi; mov esi,ecx; mov eax,[esi]): ecx = body, [esp+4] = target, no relative operand, no jump into the 5 bytes (dasm 11-04) */
typedef struct { long shots, forced, br[6], ident, pass, d0, ray, proj, rnull, rhit, rhuman, rplayer, rowb[5], rayAb[5], rayBb[5], nlm, nls; } KLBR_F6C;
static KLBR_F6C klbr_f6_c[2][2];      /* [networked][marked] */
static struct { int valid, net, marked, ix, bl, branch, known, bit21, pass, ray, haveh, ownok, geo; DWORD item, owner, human, desc, req, ret; float pos[3], mat[9], va[3], vb[3], hp[3], bp[3], m4[9], ra_dir[3], rng; int havehp, havebp, havem4, havevb, ra_have; } klbr_f6_cur;      /* m4: the ray matrix at S4 before RayAim writes; ra_dir: the direction RayAim chose at S1; rng: template range [[item+0xc4]+0xe0] (GUESS cm) */
static DWORD klbr_f6_last, klbr_f6_lastshots;
static int klud_local(DWORD *me);      /* klucc_down.c (included after this file) */
static int klud_is_player(DWORD p);
typedef DWORD (__fastcall *klbr_f6_getfn)(DWORD self, DWORD edx);
static int klbr_f6_clsgate(DWORD obj, int *known)      /* the 0x7cb080 class test on obj: (obj vt+0x30 & [0x1535228]) == [0x1535224]; the getter is called only when its address is in the exe's code or is our own GateForce wrapper (a pure getter, under the caller's __try) */
{
    DWORD vt = obj > 0xffff ? klh_rd32(obj) : 0, slot = vt > 0xffff ? klh_rd32(vt + 0x30) : 0, v;
    *known = 0;
    if (!slot || !(kbr_f6_incode(slot) || slot == (DWORD)(DWORD_PTR)klbr_gf_cls)) return 0;
    v = ((klbr_f6_getfn)(DWORD_PTR)slot)(obj, 0); *known = 1;
    return (v & KLBR_RDG(0x1535228)) == KLBR_RDG(0x1535224);
}
static int klbr_f6_human(int ix, DWORD *h, float hp[3])      /* the marked bot's holder when it is a player, else the local player; position [body+0x460] (cm) */
{
    DWORD c = ix >= 0 ? klbr_f6_hold[ix] : 0, me = 0;
    if (!(c > 0xffff && klud_is_player(c))) { klud_local(&me); c = me; }
    *h = c;
    return c > 0xffff && klh_rd(c + 0x460, hp, 12) && kle_ok3(hp);
}
static float klbr_f6_row_err(const float *m, const float *o, const float *q)      /* smallest angle of the 3 matrix rows (either sign) to the direction o -> q: the forward axis row is a GUESS, so every row is tried */
{
    int k; float best = 1.0e9f;
    for (k = 0; k < 3; k++) { float a = kbr_f6_ang_dir(m + 3 * k, o, q), b; if (a < 0.0f) return -1.0f; b = 180.0f - a; if (b < a) a = b; if (a < best) best = a; }
    return best;
}
/* OnlineBrainTraitorFireProbe7 (11-04, after bs35; TEST build only, UNTESTED, recommended off; READ ONLY toward the game: no game byte is written, only reads under __try, own fault counter klbr_f7_flt; game thread only).
   bs35: marked traitor shots take the Arcade path (gate passed, A1 muzzle, ray, request) but the weapon bone does not point at the human (2..52 deg), hp flat. Research B (wgqnxsl7e + 11-04): the AI aims through ZFireWeaponTask -> 0x574af0 -> body AimAt 0x70f130
   ([body+0x824]=mode 1 entity / 2 position, [+0x828] target pointer, [+0x82c..0x834] offset, [+0x838] bone byte, [+0x83c] float, [+0x68c]=5 priority, byte [+0x64c] = 'busy' flag that makes AimAt a silent no-op). Per MARKED shot (sampled lines, first KLBR_F6_LOGMAX per round, a running total every
   30 s with the FireProbe6 clock, round totals) this logs those fields at S1 (0x4cb8b9, same stub as FireProbe6), who [body+0x828] / the holder [soldier+0xac] / the fire task's [task+0x28] (GUESS: a target pointer or handle) is (the host-local human = the shot's target, another seat's player, other),
   whether AimAt ran in the last second (SEVENTH site 0x70f130, 5 bytes push esi; mov esi,ecx; mov eax,[esi] - a counting detour like the other six, installed only with this key: ecx = body, [esp+4] = target), and at S4 (0x4cc440) the three rows of the ray matrix M = [esp+0xf4] with their
   SIGNED angle to the direction ray start (*eax, GUESS = P) -> the human's chest (feet [human+0x460] + OnlineBrainTraitorRayAimChest, GUESS), counting rows within 15 deg of +dir and -dir; the template range R = [[item+0xc4]+0xe0] (GUESS cm, as FireProbe3) against the bot -> human distance. */
typedef struct { long shots, modeN[4], tgtHuman, tgtSeat, tgtPlayer, tgtOther, tgtNone, holdHuman, taskHuman, b64c, aimRecent, aimNot, outRange, inRange, mN, mPos[3], mNeg[3], nl,
    aimBad, aimZero, aimDb[5], aimEb[5], b0f8, d0fc, childN, childNull, cpNull, cpHuman, cpSeat, cpPlayer, cpOther, cvtExe, cvtHeap, c6cNZ; } KLBR_F7C;      /* aim*: item aim point [item+0xc8..0xd0] at S1 (distance / angle-error buckets); child*: the first ray entity at site 7 */
static KLBR_F7C klbr_f7_c;
static struct { int valid, ix, who_tgt, seat_tgt, who_hold, seat_hold, who_task, seat_task, aimN; long aimAge; DWORD body, sold, pbody, mode, tgt, hold, task, ttgt, b544, pri; BYTE b64c, b840, bone, t14, t15; float off[3], f83c, R;
    int havea, childset, who_cp, seat_cp, who_ent, seat_ent; BYTE b0f8; DWORD d0fc, ent, cp, cvt, c6c; float ap[3], aimD, aimE, chestD; } klbr_f7_cur;      /* havea..chestD: item aim point at S1 (before any RayAim write); ent..c6c: first child at site 7 */
static int klbr_f7_site8;      /* 1 when the AimAt detour (site 8) went in; else the aim-recency lines are meaningless */
static long klbr_f7_aim_n[KLBR_MAX]; static DWORD klbr_f7_aim_t[KLBR_MAX], klbr_f7_aim_tg[KLBR_MAX];
static int klbr_f7_who(DWORD p, DWORD human, int *seat)      /* 0 none, 1 the shot's target human, 2 another seat's player, 3 another player object, 4 something else; seat = the index in [[0xdd265c]+0x828..] or -1 */
{
    DWORD gd; int i;
    *seat = -1;
    if (p <= 0xffff) return 0;
    gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c));
    for (i = 0; i < 28 && gd > 0xffff; i++) if (klh_rd32(gd + 0x828 + 4 * i) == p && klud_is_player(p)) { *seat = i; break; }
    if (p == human) return 1;
    if (*seat >= 0) return 2;
    return klud_is_player(p) ? 3 : 4;
}
static int klbr_ra_chest_pt(float *tg);
static const char *klbr_f7_whoname(int w) { return w == 0 ? "none" : w == 1 ? "THE HUMAN" : w == 2 ? "another seat's player" : w == 3 ? "another player object" : "something else"; }
static void klbr_f7_aimat(KLBR_F3REGS *r)      /* site 8: AimAt entry (game thread): ecx = body, [esp+4] = the target; remembered per marked body */
{
    int i;
    if (!klbr_f7on || klbr_f7_flt >= 3) return;
    for (i = 0; i < KLBR_MAX; i++) if (klbr_f6_body[i] && klbr_f6_body[i] == r->ecx) { klbr_f7_aim_n[i]++; klbr_f7_aim_t[i] = GetTickCount(); klbr_f7_aim_tg[i] = klh_rd32(r->esp + 4); }
}
static void klbr_f7_capture(int ix, DWORD sp, DWORD item)      /* S1 of a MARKED shot (game thread): the aim state of the body */
{
    DWORD B = klbr_f6_body[ix], S = klbr_f6_sold[ix], task = 0, tpl, now = GetTickCount(); KLBR_F7C *c = &klbr_f7_c; int sh;
    memset(&klbr_f7_cur, 0, sizeof klbr_f7_cur);
    if (!klbr_f7on || klbr_f7_flt >= 3 || B <= 0xffff) return;
    __try {
        klbr_f7_cur.ix = ix; klbr_f7_cur.body = B; klbr_f7_cur.sold = S; klbr_f7_cur.pbody = klh_rd32(sp + 0x6c);
        klbr_f7_cur.mode = klh_rd32(B + 0x824); klbr_f7_cur.tgt = klh_rd32(B + 0x828); klh_rd(B + 0x82c, klbr_f7_cur.off, 12); klh_rd(B + 0x838, &klbr_f7_cur.bone, 1); klh_rd(B + 0x83c, &klbr_f7_cur.f83c, 4);
        klbr_f7_cur.pri = klh_rd32(B + 0x68c); klh_rd(B + 0x64c, &klbr_f7_cur.b64c, 1); klh_rd(B + 0x840, &klbr_f7_cur.b840, 1); klbr_f7_cur.b544 = klh_rd32(B + 0x544);
        klbr_f7_cur.hold = S > 0xffff ? klh_rd32(S + 0xac) : klbr_f6_hold[ix];
        task = S > 0xffff ? klh_rd32(S + 0x570) : 0; klbr_f7_cur.task = task;
        if (task > 0xffff) { klh_rd(task + 0x14, &klbr_f7_cur.t14, 1); klh_rd(task + 0x15, &klbr_f7_cur.t15, 1); klbr_f7_cur.ttgt = klh_rd32(task + 0x28); }      /* GUESS: +0x28 is a target pointer / handle (research B) */
        klbr_f7_cur.who_tgt = klbr_f7_who(klbr_f7_cur.tgt, klbr_f6_cur.human, &klbr_f7_cur.seat_tgt);
        klbr_f7_cur.who_hold = klbr_f7_who(klbr_f7_cur.hold, klbr_f6_cur.human, &klbr_f7_cur.seat_hold);
        klbr_f7_cur.who_task = klbr_f7_who(klbr_f7_cur.ttgt, klbr_f6_cur.human, &klbr_f7_cur.seat_task);
        tpl = item > 0xffff ? klh_rd32(item + 0xc4) : 0;
        if (tpl > 0xffff) { DWORD rr = klh_rd32(tpl + 0xe0); memcpy(&klbr_f7_cur.R, &rr, 4); }
        klbr_f6_cur.rng = klbr_f7_cur.R;
        klbr_f7_cur.aimN = (int)klbr_f7_aim_n[ix];
        klbr_f7_cur.aimAge = klbr_f7_aim_n[ix] ? (long)(now - klbr_f7_aim_t[ix]) : -1;
        klbr_f7_cur.aimD = klbr_f7_cur.aimE = klbr_f7_cur.chestD = -1.0f;
        if (item > 0xffff) { klbr_f7_cur.havea = klh_rd(item + 0xc8, klbr_f7_cur.ap, 12); klh_rd(item + 0xf8, &klbr_f7_cur.b0f8, 1); klbr_f7_cur.d0fc = klh_rd32(item + 0xfc); }      /* the item aim point (research 11-04: the pellets fly toward it); read BEFORE RayAim bit 2 writes it */
        klbr_f7_cur.valid = 1;
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f7_flt++; klbr_f7_cur.valid = 0; klog("brain: traitor fireprobe7: fault reading the aim state (%d of 3 allowed)", klbr_f7_flt); return; }
    c->shots++; sh = klbr_f7_cur.mode < 3 ? (int)klbr_f7_cur.mode : 3; c->modeN[sh]++;
    switch (klbr_f7_cur.who_tgt) { case 0: c->tgtNone++; break; case 1: c->tgtHuman++; break; case 2: c->tgtSeat++; break; case 3: c->tgtPlayer++; break; default: c->tgtOther++; }
    if (klbr_f7_cur.who_hold == 1) c->holdHuman++;
    if (klbr_f7_cur.who_task == 1) c->taskHuman++;
    if (klbr_f7_cur.b64c) c->b64c++;
    if (klbr_f7_cur.aimAge >= 0 && klbr_f7_cur.aimAge <= 1000) c->aimRecent++; else c->aimNot++;
    if (klbr_f6_cur.geo && klbr_f6_cur.havehp && klbr_f7_cur.R > 0.0f) { if (kbr_f6_dist(klbr_f6_cur.pos, klbr_f6_cur.hp) > klbr_f7_cur.R) c->outRange++; else c->inRange++; }
    {      /* the item aim point against the muzzle origin and the human chest */
        float tg[3];
        if (klbr_f7_cur.b0f8) c->b0f8++;
        if (klbr_f7_cur.d0fc) c->d0fc++;
        if (!klbr_f7_cur.havea || !kbr_ra_finite(klbr_f7_cur.ap, 3)) c->aimBad++;
        else {
            if (kbr_f6_is_zero3(klbr_f7_cur.ap)) c->aimZero++;
            if (klbr_f6_cur.geo && !kbr_f6_is_zero3(klbr_f6_cur.pos)) {
                klbr_f7_cur.aimD = kbr_f6_dist(klbr_f6_cur.pos, klbr_f7_cur.ap);
                if (klbr_ra_chest_pt(tg)) { klbr_f7_cur.aimE = kbr_f6_ang(klbr_f6_cur.pos, klbr_f7_cur.ap, tg); klbr_f7_cur.chestD = kbr_f6_dist(klbr_f6_cur.pos, tg); }
            }
        }
        c->aimDb[kbr_f7_dbucket(klbr_f7_cur.aimD)]++; c->aimEb[kbr_f6_bucket(klbr_f7_cur.aimE)]++;
    }
}
static void klbr_f7_child(DWORD ent)      /* site 7 (read only, no game call): the first ray entity (child of the pooled bullet group): [child+0x60], its vtable, [[child+0x60]+0x6c] */
{
    KLBR_F7C *c = &klbr_f7_c;
    if (!klbr_f7on || klbr_f7_flt >= 3 || !klbr_f7_cur.valid) return;
    c->childN++; klbr_f7_cur.childset = 1; klbr_f7_cur.ent = ent;
    if (ent <= 0xffff) { c->childNull++; return; }
    klbr_f7_cur.cp = klh_rd32(ent + 0x60);
    if (klbr_f7_cur.cp > 0xffff) { klbr_f7_cur.cvt = klh_rd32(klbr_f7_cur.cp); klbr_f7_cur.c6c = klh_rd32(klbr_f7_cur.cp + 0x6c); }
    klbr_f7_cur.who_cp = klbr_f7_who(klbr_f7_cur.cp, klbr_f6_cur.human, &klbr_f7_cur.seat_cp);
    klbr_f7_cur.who_ent = klbr_f7_who(ent, klbr_f6_cur.human, &klbr_f7_cur.seat_ent);
    switch (klbr_f7_cur.who_cp) { case 0: c->cpNull++; break; case 1: c->cpHuman++; break; case 2: c->cpSeat++; break; case 3: c->cpPlayer++; break; default: c->cpOther++; }
    if (klbr_f7_cur.cvt > 0xffff) { if (klbr_f7_cur.cvt >= 0x400000 && klbr_f7_cur.cvt < 0x1800000) c->cvtExe++; else c->cvtHeap++; }
    if (klbr_f7_cur.c6c) c->c6cNZ++;
}
static int klbr_ra_chest_pt(float *tg)      /* the aim point: the shot's target human's feet [human+0x460] + OnlineBrainTraitorRayAimChest in y (y is up; GUESS: +0x460 is the feet and ~130 is a chest) */
{
    if (!klbr_f6_cur.havehp) return 0;
    tg[0] = klbr_f6_cur.hp[0]; tg[1] = klbr_f6_cur.hp[1] + (float)klbr_ra_chest; tg[2] = klbr_f6_cur.hp[2];
    return kbr_ra_finite(tg, 3);
}
static void klbr_f7_at_s4(void)      /* S4 (read only): the signed angle of each ray-matrix row to ray start -> chest */
{
    float tg[3], e[3] = { -1.0f, -1.0f, -1.0f }; int k;
    if (!klbr_f7_cur.valid || !klbr_f6_cur.havem4 || !klbr_ra_chest_pt(tg)) return;
    klbr_f7_c.mN++;
    for (k = 0; k < 3; k++) {
        e[k] = kbr_f6_ang_dir(klbr_f6_cur.m4 + 3 * k, klbr_f6_cur.vb, tg);
        if (e[k] >= 0.0f && e[k] < 15.0f) klbr_f7_c.mPos[k]++; else if (e[k] >= 0.0f && 180.0f - e[k] < 15.0f) klbr_f7_c.mNeg[k]++;
    }
}
static void klbr_f7_line(void)      /* the sampled line of one marked shot (at the ray result / projectile site) */
{
    KLBR_F7C *c = &klbr_f7_c; float tg[3], e[3] = { -1.0f, -1.0f, -1.0f }, d = -1.0f, dr = -1.0f; int k, haveg;
    if (!klbr_f7_cur.valid) return;
    klbr_f7_cur.valid = 0;
    if (c->nl >= KLBR_F6_LOGMAX) return;
    c->nl++;
    haveg = klbr_ra_chest_pt(tg);
    if (klbr_f6_cur.geo && klbr_f6_cur.havehp) d = kbr_f6_dist(klbr_f6_cur.pos, klbr_f6_cur.hp);
    if (klbr_f6_cur.havem4 && haveg) { for (k = 0; k < 3; k++) e[k] = kbr_f6_ang_dir(klbr_f6_cur.m4 + 3 * k, klbr_f6_cur.vb, tg); dr = kbr_f6_dist(klbr_f6_cur.vb, tg); }
    klog("brain: traitor fireprobe7 shot: bot %d body %08lx soldier %08lx (item vt+0x2c8 obj [esp+0x6c] %08lx): AimAt mode [+0x824] %lu, target [+0x828] %08lx = %s%s, offset (%.1f %.1f %.1f) bone %02x f[+0x83c] %.2f, priority [+0x68c] %lu, byte [+0x64c] (busy; AimAt is a no-op when set) %02x, byte [+0x840] %02x, [+0x544] %08lx; "
         "holder [soldier+0xac] %08lx = %s; fire task [soldier+0x570] %08lx bytes +0x14 %02x +0x15 %02x, [task+0x28] (GUESS: target) %08lx = %s; AimAt (0x70f130) calls so far %d%s, last %s (%ld ms ago); human (the shot's target) %08lx; |origin-human| %.1f, template range R %.1f (GUESS cm); "
         "ray matrix M at S4 (before RayAim) %s: signed angle of rows 0/1/2 to ray start -> chest %.1f %.1f %.1f deg (near 0 = that row points at the human, near 180 = away), |ray start - chest| %.1f",
         klbr_f7_cur.ix, (unsigned long)klbr_f7_cur.body, (unsigned long)klbr_f7_cur.sold, (unsigned long)klbr_f7_cur.pbody, (unsigned long)klbr_f7_cur.mode, (unsigned long)klbr_f7_cur.tgt,
         klbr_f7_cur.who_tgt == 0 ? "none" : klbr_f7_cur.who_tgt == 1 ? "THE HUMAN" : klbr_f7_cur.who_tgt == 2 ? "another seat's player" : klbr_f7_cur.who_tgt == 3 ? "another player object" : "something else", klbr_f7_cur.seat_tgt >= 0 ? " (a seat)" : "",
         (double)klbr_f7_cur.off[0], (double)klbr_f7_cur.off[1], (double)klbr_f7_cur.off[2], klbr_f7_cur.bone, (double)klbr_f7_cur.f83c, (unsigned long)klbr_f7_cur.pri, klbr_f7_cur.b64c, klbr_f7_cur.b840, (unsigned long)klbr_f7_cur.b544,
         (unsigned long)klbr_f7_cur.hold, klbr_f7_cur.who_hold == 0 ? "none" : klbr_f7_cur.who_hold == 1 ? "THE HUMAN" : klbr_f7_cur.who_hold == 2 ? "another seat's player" : klbr_f7_cur.who_hold == 3 ? "another player object" : "something else",
         (unsigned long)klbr_f7_cur.task, klbr_f7_cur.t14, klbr_f7_cur.t15, (unsigned long)klbr_f7_cur.ttgt, klbr_f7_cur.who_task == 0 ? "none" : klbr_f7_cur.who_task == 1 ? "THE HUMAN" : klbr_f7_cur.who_task == 2 ? "another seat's player" : klbr_f7_cur.who_task == 3 ? "another player object" : "something else",
         klbr_f7_cur.aimN, klbr_f7_site8 ? "" : " (SITE 8 NOT INSTALLED: no AimAt data)", klbr_f7_cur.aimAge < 0 ? "never" : klbr_f7_cur.aimAge <= 1000 ? "WITHIN 1 s" : "older than 1 s", klbr_f7_cur.aimAge, (unsigned long)klbr_f6_cur.human, (double)d, (double)klbr_f7_cur.R,
         klbr_f6_cur.havem4 ? "read" : "NOT read", (double)e[0], (double)e[1], (double)e[2], (double)dr);
    klog("brain: traitor fireprobe7 aim: bot %d item %08lx: item aim point [item+0xc8..0xd0] (before any RayAim write) %s(%.1f %.1f %.1f) |origin-aim| %.1f, angle error (origin -> aim point vs origin -> chest) %.2f deg, |origin-chest| %.1f; byte [item+0xf8] %02x, dword [item+0xfc] %08lx; "
         "first child [esp+0x10] %s%08lx%s: [child+0x60] %08lx = %s%s, its vtable %08lx (%s), [[child+0x60]+0x6c] %08lx",
         klbr_f7_cur.ix, (unsigned long)klbr_f6_cur.item, klbr_f7_cur.havea ? "" : "UNREADABLE ", (double)klbr_f7_cur.ap[0], (double)klbr_f7_cur.ap[1], (double)klbr_f7_cur.ap[2], (double)klbr_f7_cur.aimD, (double)klbr_f7_cur.aimE, (double)klbr_f7_cur.chestD, klbr_f7_cur.b0f8, (unsigned long)klbr_f7_cur.d0fc,
         klbr_f7_cur.childset ? "" : "n/a (projectile path, no ray result) ", (unsigned long)klbr_f7_cur.ent, klbr_f7_cur.childset && !klbr_f7_cur.ent ? " (null: no hit)" : klbr_f7_cur.childset && klbr_f7_cur.who_ent == 1 ? " (THE HUMAN itself)" : "",
         (unsigned long)klbr_f7_cur.cp, klbr_f7_whoname(klbr_f7_cur.who_cp), klbr_f7_cur.seat_cp >= 0 ? " (a seat)" : "",
         (unsigned long)klbr_f7_cur.cvt, klbr_f7_cur.cvt <= 0xffff ? "none" : (klbr_f7_cur.cvt >= 0x400000 && klbr_f7_cur.cvt < 0x1800000) ? "in the exe image" : "heap / dll copy", (unsigned long)klbr_f7_cur.c6c);
}
static void klbr_f7_summary(const char *why)
{
    KLBR_F7C *c = &klbr_f7_c;
    if (!klbr_f7on || !c->shots) return;
    klog("brain: traitor fireprobe7 %s: marked shots %ld; AimAt mode [+0x824] 0/1/2/other %ld %ld %ld %ld; target [+0x828]: the human %ld, another seat %ld, another player %ld, something else %ld, none %ld; holder [soldier+0xac] = the human %ld; fire task [task+0x28] = the human %ld; byte [+0x64c] set %ld; AimAt called within 1 s %ld, not %ld; "
         "human beyond the template range R %ld, within %ld; ray matrix samples (S4, before RayAim) %ld: rows 0/1/2 within 15 deg of the human direction %ld %ld %ld, of the opposite %ld %ld %ld; faults %d",
         why, c->shots, c->modeN[0], c->modeN[1], c->modeN[2], c->modeN[3], c->tgtHuman, c->tgtSeat, c->tgtPlayer, c->tgtOther, c->tgtNone, c->holdHuman, c->taskHuman, c->b64c, c->aimRecent, c->aimNot, c->outRange, c->inRange, c->mN, c->mPos[0], c->mPos[1], c->mPos[2], c->mNeg[0], c->mNeg[1], c->mNeg[2], klbr_f7_flt);
    klog("brain: traitor fireprobe7 %s aim: marked shots %ld; item aim point [item+0xc8..0xd0] unreadable or not finite %ld, all zero %ld; |origin-aim| buckets (<1000 <3000 <6000 >=6000 unknown units) %ld %ld %ld %ld %ld; angle error to the chest (<5 <15 <45 >=45 unknown deg) %ld %ld %ld %ld %ld; byte [item+0xf8] set %ld, dword [item+0xfc] set %ld; "
         "first child at site 7: ray results %ld (entity null %ld); [child+0x60] null %ld, the human %ld, another seat %ld, another player %ld, other %ld; its vtable in the exe image %ld, elsewhere %ld; [[child+0x60]+0x6c] nonzero %ld",
         why, c->shots, c->aimBad, c->aimZero, c->aimDb[0], c->aimDb[1], c->aimDb[2], c->aimDb[3], c->aimDb[4], c->aimEb[0], c->aimEb[1], c->aimEb[2], c->aimEb[3], c->aimEb[4], c->b0f8, c->d0fc,
         c->childN, c->childNull, c->cpNull, c->cpHuman, c->cpSeat, c->cpPlayer, c->cpOther, c->cvtExe, c->cvtHeap, c->c6cNZ);
}
/* OnlineBrainTraitorRayAim (11-04, after bs35; TEST build only, UNTESTED, recommended off; CHANGES the game: writes 36 bytes of the game thread's own STACK frame in the per-shot routine, no code and no heap byte; game thread only, own fault counter klbr_ra_flt).
   Research A (11-04): the real bullet is built from the muzzle transform T (3x3 at E0+0xc4) and position V (E0+0x60) right after the vt+0x250 call; the ray 0x713e80 at 0x4cc44b only places a muzzle-effect group with the matrix M (E0+0xe8) = node matrix composed with T (0x60ad10) and the position P (E0+0x28).
   So two writes, each only for a LIVE MARKED traitor shot (the same marked test as GateForce: body of an armed klbr_t entry with state 1 and the traitor flag), the shot record valid, the muzzle outputs read (not branch A0), a target position known, and the target within OnlineBrainTraitorRayAimMaxDist (GUESS 6000):
     S1 (site bit 1): T at [esp+0xc4] at 0x4cb8b9 (esp = E0). The forward row (OnlineBrainTraitorRayAimRow, auto = 2: GUESS, the pellet loop reads T row 2) is replaced by the direction origin(V) -> chest (+ a random cone error, GUESS 3 deg, so it is not an aimbot), the other two rows are rebuilt orthonormal (kbr_ra_build),
         handedness of the old matrix kept; refused when the old T is not a valid rotation. This steers the bullet (research A, medium confidence) and, through 0x60ad10, the flash.
     S4 (site bit 4): M at [esp+0xf4] at 0x4cc440 (esp = E0-12), the same rewrite with the S1 direction when S1 wrote, else with a fresh one from the ray start P = *eax. This steers the pooled ray / flash group only (research A: not a hit by itself).
   The target is the shot's human (the marked bot's holder when it is a player, else the local player) at feet [human+0x460] + OnlineBrainTraitorRayAimChest (GUESS 130 units). The forward SIGN is OnlineBrainTraitorRayAimSign. */
static struct { long s1, s4, w1, w4, nogate, farc, bad, noP, flt, rab[5], s2, w2, nogate2, farc2, bad2, ref2, rab2[5]; } klbr_ra_c;      /* s2..rab2: site bit 2 (item aim point) */
static int klbr_ra_live(int ix) { return ix >= 0 && ix < KLBR_MAX && klbr_t[ix].state == 1 && klbr_t[ix].traitor && klbr_f6_body[ix] > 0xffff; }
static int klbr_ra_write(DWORD addr, const float *m)      /* 9 floats into the game thread's own stack frame; 0 on a fault */
{
    __try { memcpy((void *)(DWORD_PTR)addr, m, 36); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_ra_flt++; klbr_ra_c.flt++; return 0; }
    return 1;
}
static void klbr_ra_apply(int which, DWORD sp, const float *o, DWORD matAddr)      /* which 1 = S1 (T), 4 = S4 (M); o = the ray origin (V at S1, P at S4); matAddr = the 3x3 */
{
    float tg[3], dir[3], fd[3], nt[9], oldm[9], dist = 0.0f, u1, u2, eold, enew, econe; int row = kbr_ra_row(klbr_ra_rowcfg), sg = kbr_ra_sign(klbr_ra_signcfg), k, haveg;
    (void)sp;
    if (which == 1) klbr_ra_c.s1++; else klbr_ra_c.s4++;
    if (klbr_ra_flt >= 3) return;
    haveg = klbr_ra_chest_pt(tg);
    if (!kbr_ra_gate(klbr_raon, GetCurrentThreadId() == klbr_f6_tid, klbr_f6_cur.marked && klbr_ra_live(klbr_f6_cur.ix), klbr_f6_cur.valid, klbr_f6_cur.geo && klbr_f6_cur.bl, haveg)) { klbr_ra_c.nogate++; return; }      /* review 11-04: only shots that took the vt+0x250 muzzle path (bl = 1, the researched one); the bl = 0 path fills T / V by other code */
    if (kbr_f6_is_zero3(o)) { klbr_ra_c.bad++; return; }      /* review 11-04: a zero origin is the 0x857110 fallback or a failed read, not a muzzle */
    if (!klh_rd(matAddr, oldm, 36)) { klbr_ra_c.bad++; return; }
    if (which == 4 && klbr_f6_cur.ra_have) { for (k = 0; k < 3; k++) fd[k] = klbr_f6_cur.ra_dir[k]; if (!kbr_ra_dir(o, tg, 0.0f, dir, &dist)) { klbr_ra_c.farc++; return; } }      /* S4 follows the S1 choice (the cone draw is per shot) */
    else {
        if (!kbr_ra_dir(o, tg, (float)klbr_ra_maxd, dir, &dist)) { klbr_ra_c.farc++; return; }
        u1 = kbr_ra_rng(&klbr_ra_seed); u2 = kbr_ra_rng(&klbr_ra_seed);
        if (!kbr_ra_cone(dir, klbr_ra_spread, u1, u2, fd)) { klbr_ra_c.bad++; return; }
    }
    if (!kbr_ra_build(oldm, fd, row, sg, nt)) { klbr_ra_c.bad++; return; }
    { float od[3]; for (k = 0; k < 3; k++) od[k] = oldm[3 * row + k] * (float)sg; eold = kbr_f6_ang_dir(od, o, tg); klbr_ra_c.rab[kbr_f6_bucket(eold)]++; }
    if (!klbr_ra_write(matAddr, nt)) return;
    { float nd[3]; for (k = 0; k < 3; k++) nd[k] = nt[3 * row + k] * (float)sg; enew = kbr_f6_ang_dir(nd, o, tg); econe = kbr_f6_ang_dir(fd, o, tg); }
    if (which == 1) {
        klbr_ra_c.w1++; for (k = 0; k < 3; k++) klbr_f6_cur.ra_dir[k] = fd[k];
        klbr_f6_cur.ra_have = 1;
    } else klbr_ra_c.w4++;
    if (klbr_ra_c.w1 + klbr_ra_c.w4 <= 8 || ((klbr_ra_c.w1 + klbr_ra_c.w4) % 64) == 0)
        klog("brain: traitor rayaim write: site %s (%s) bot %d: origin (%.1f %.1f %.1f) chest target (%.1f %.1f %.1f) dist %.1f (max %d); row %d%s sign %d, cone %d deg: old forward-row error to the exact line %.1f deg -> new %.2f deg (the cone draw itself %.2f deg off); matrix %s",
             which == 1 ? "S1 0x4cb8b9" : "S4 0x4cc440", which == 1 ? "muzzle T, steers the bullet" : "ray matrix M, steers the flash/ray group", klbr_f6_cur.ix, (double)o[0], (double)o[1], (double)o[2], (double)tg[0], (double)tg[1], (double)tg[2], (double)dist, klbr_ra_maxd,
             row, klbr_ra_rowcfg < 0 ? " (auto: GUESS 2)" : "", sg, klbr_ra_spread, (double)eold, (double)enew, (double)econe, "rewritten orthonormal");
}
/* RayAim site bit 2 (11-04, workflow wljmhfnun, UNTESTED, recommended off; CHANGES the game: 12 bytes of the shot's item, heap memory, through klh_data = VirtualQuery-checked memcpy; game thread only, own fault counter).
   Static research: the pellet bullets of 0x4cb7a0 are built by the descriptor ctor 0x748900 whose arg8 is the item aim point [item+0xc8..0xd0] (item vt+0x2d4 = lea eax,[ecx+0xc8]); the pellets fly toward it, NOT along T. The point is refreshed inside 0x4cb7a0
   only for bl = 0 (0x4cbe4b / 0x4cbe5c, skipped by the test bl,bl / jne at 0x4cbe47); S1 0x4cb8b9 runs before 0x4cbe4b and 0x4cc15a (checked in the disassembly), and the gate below needs bl = 1, so a write at S1 survives to the descriptor (disassembly 0x4cb8b9..0x4cc15a, review 11-04: no direct store to +0xc8; the only writer is the vt+0x2cc call at 0x4cbefb, reached when the soldier state [[esp+0x24]+0xac] == 0xe, any bl: it reads the point back through vt+0x2d4 (0x4cbeae) and stores a DERIVED point, so our value is the input there - GUESS that this is an offset/recoil step).
   Same gate and the same cone draw as the T rewrite (the S1 draw when bit 1 wrote, else a fresh one); the written point is origin + drawn direction * distance to the chest (the chest itself when the spread is 0). */
static void klbr_ra_aim(DWORD item, const float *o)
{
    float tg[3], dir[3], fd[3], np[3], oldp[3], dist = 0.0f, u1, u2, eold = -1.0f, enew, econe; int k, haveg, haveold, ok = 0;
    klbr_ra_c.s2++;
    if (klbr_ra_flt >= 3) return;
    haveg = klbr_ra_chest_pt(tg);
    if (!kbr_ra_gate(klbr_raon, GetCurrentThreadId() == klbr_f6_tid, klbr_f6_cur.marked && klbr_ra_live(klbr_f6_cur.ix), klbr_f6_cur.valid, klbr_f6_cur.geo && klbr_f6_cur.bl, haveg)) { klbr_ra_c.nogate2++; return; }
    if (item <= 0xffff || kbr_f6_is_zero3(o)) { klbr_ra_c.bad2++; return; }
    if (!kbr_ra_dir(o, tg, (float)klbr_ra_maxd, dir, &dist)) { klbr_ra_c.farc2++; return; }
    if (klbr_f6_cur.ra_have) { for (k = 0; k < 3; k++) fd[k] = klbr_f6_cur.ra_dir[k]; }
    else { u1 = kbr_ra_rng(&klbr_ra_seed); u2 = kbr_ra_rng(&klbr_ra_seed); if (!kbr_ra_cone(dir, klbr_ra_spread, u1, u2, fd)) { klbr_ra_c.bad2++; return; } }
    if (!kbr_ra_point(o, fd, dist, np)) { klbr_ra_c.bad2++; return; }
    haveold = klh_rd(item + 0xc8, oldp, 12) && kbr_ra_finite(oldp, 3);
    if (haveold) eold = kbr_f6_ang(o, oldp, tg);
    klbr_ra_c.rab2[kbr_f6_bucket(eold)]++;
    __try { ok = klh_data((void *)(DWORD_PTR)(item + 0xc8), np, 12, "RayAim item aim point"); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_ra_flt++; klbr_ra_c.flt++; ok = 0; }
    if (!ok) { klbr_ra_c.ref2++; return; }
    enew = kbr_f6_ang(o, np, tg); econe = kbr_f6_ang_dir(fd, o, tg);
    klbr_ra_c.w2++;
    if (klbr_ra_c.w2 <= 8 || (klbr_ra_c.w2 % 64) == 0)
        klog("brain: traitor rayaim write: site A2 (S1 0x4cb8b9) (item aim point [item+0xc8..0xd0], steers the pellets) bot %d item %08lx: origin (%.1f %.1f %.1f) chest target (%.1f %.1f %.1f) dist %.1f (max %d); cone %d deg: old aim point %s(%.1f %.1f %.1f) error to the exact line %.1f deg -> new aim point (%.1f %.1f %.1f) error %.2f deg (the cone draw itself %.2f deg off); %s",
             klbr_f6_cur.ix, (unsigned long)item, (double)o[0], (double)o[1], (double)o[2], (double)tg[0], (double)tg[1], (double)tg[2], (double)dist, klbr_ra_maxd, klbr_ra_spread,
             haveold ? "" : "UNREADABLE/not finite ", (double)oldp[0], (double)oldp[1], (double)oldp[2], (double)eold, (double)np[0], (double)np[1], (double)np[2], (double)enew, (double)econe, klbr_f6_cur.ra_have ? "direction shared with the T rewrite" : "own cone draw");
}
static void klbr_ra_summary(const char *why)
{
    if (!klbr_raon || !(klbr_ra_c.s1 || klbr_ra_c.s4 || klbr_ra_c.s2)) return;
    klog("brain: traitor rayaim %s: S1 seen %ld written %ld, S4 seen %ld written %ld; not written: gate (not a live marked shot / no target / no geometry) %ld, target beyond %d units or degenerate %ld, matrix not a valid rotation or read failed %ld; old forward-row error before the write (<5 <15 <45 >=45 unknown deg) %ld %ld %ld %ld %ld; faults %ld (row %d%s, sign %d, spread %d deg, site mask %d, chest %d)",
         why, klbr_ra_c.s1, klbr_ra_c.w1, klbr_ra_c.s4, klbr_ra_c.w4, klbr_ra_c.nogate, klbr_ra_maxd, klbr_ra_c.farc, klbr_ra_c.bad, klbr_ra_c.rab[0], klbr_ra_c.rab[1], klbr_ra_c.rab[2], klbr_ra_c.rab[3], klbr_ra_c.rab[4], klbr_ra_c.flt, kbr_ra_row(klbr_ra_rowcfg), klbr_ra_rowcfg < 0 ? " (auto: GUESS 2)" : "", kbr_ra_sign(klbr_ra_signcfg), klbr_ra_spread, klbr_ra_site, klbr_ra_chest);
    if (klbr_ra_site & 2) klog("brain: traitor rayaim %s aim point (site bit 2, item [item+0xc8..0xd0]): S1 seen %ld written %ld; not written: gate %ld, no item / zero origin / bad cone %ld, target beyond %d units or degenerate %ld, write refused or faulted %ld; old aim-point error to the chest line before the write (<5 <15 <45 >=45 unknown deg) %ld %ld %ld %ld %ld",
         why, klbr_ra_c.s2, klbr_ra_c.w2, klbr_ra_c.nogate2, klbr_ra_c.bad2, klbr_ra_maxd, klbr_ra_c.farc2, klbr_ra_c.ref2, klbr_ra_c.rab2[0], klbr_ra_c.rab2[1], klbr_ra_c.rab2[2], klbr_ra_c.rab2[3], klbr_ra_c.rab2[4]);
}
static void klbr_f6_shotline(KLBR_F6C *c)      /* the combined line of one shot (muzzle + ray) */
{
    float dm_h = -1, dm_b = -1, db_h = -1, mA = -1, mB = -1, eA = -1, eB = -1, er = -1;
    const float *o = klbr_f6_cur.pos;
    if (c->nls >= KLBR_F6_LOGMAX) return;
    c->nls++;
    if (klbr_f6_cur.geo && klbr_f6_cur.havehp) { dm_h = kbr_f6_dist(o, klbr_f6_cur.hp); er = klbr_f6_row_err(klbr_f6_cur.mat, o, klbr_f6_cur.hp); }
    if (klbr_f6_cur.geo && klbr_f6_cur.havebp) dm_b = kbr_f6_dist(o, klbr_f6_cur.bp);
    if (klbr_f6_cur.havehp && klbr_f6_cur.havebp) db_h = kbr_f6_dist(klbr_f6_cur.bp, klbr_f6_cur.hp);
    if (klbr_f6_cur.ray && klbr_f6_cur.geo) {
        mA = kbr_f6_dist(o, klbr_f6_cur.va); mB = kbr_f6_dist(o, klbr_f6_cur.vb);
        if (klbr_f6_cur.havehp) { eA = kbr_f6_ang(o, klbr_f6_cur.va, klbr_f6_cur.hp); eB = kbr_f6_ang(o, klbr_f6_cur.vb, klbr_f6_cur.hp); }
    }
    klog("brain: traitor fireprobe6 shot: networked %s %s bot %d item %08lx owner %08lx: path %s; branch %s%s; muzzle origin (%.1f %.1f %.1f)%s, bot (%.1f %.1f %.1f), human %08lx (%.1f %.1f %.1f); |origin-bot| %.1f |origin-human| %.1f |bot-human| %.1f (muzzle unit is a GUESS: cm); best matrix-row error to the human %.1f deg (forward row unknown, rows tried: %.2f %.2f %.2f / %.2f %.2f %.2f / %.2f %.2f %.2f); 0x4a30e0 -> %08lx; "
         "ray 0x713e80: %s; vecA (%.1f %.1f %.1f) |origin-A| %.1f err(origin; A,human) %.1f deg; vecB (%.1f %.1f %.1f) |origin-B| %.1f err(origin; B,human) %.1f deg (A = [esp+0xf4] = the first vector argument, probably the start; B = *eax = the second, probably the end: GUESS); request object %08lx, hit entity [esp+0x10] after vt+0x78: %08lx (%s)%s",
         klbr_f6_cur.net ? "yes" : "no", klbr_f6_cur.marked ? "MARKED" : "other", klbr_f6_cur.ix, (unsigned long)klbr_f6_cur.item, (unsigned long)klbr_f6_cur.owner, klbr_f6_cur.ray ? "ray (0x713e80)" : "projectile (0x4cc655)", kbr_f6_branch_name(klbr_f6_cur.branch), klbr_f6_cur.known ? "" : " (class test unreadable: GUESS no)",
         (double)o[0], (double)o[1], (double)o[2], kbr_f6_is_zero3(o) ? " ZERO" : "", (double)klbr_f6_cur.bp[0], (double)klbr_f6_cur.bp[1], (double)klbr_f6_cur.bp[2], (unsigned long)klbr_f6_cur.human, (double)klbr_f6_cur.hp[0], (double)klbr_f6_cur.hp[1], (double)klbr_f6_cur.hp[2],
         (double)dm_b, (double)dm_h, (double)db_h, (double)er, (double)klbr_f6_cur.mat[0], (double)klbr_f6_cur.mat[1], (double)klbr_f6_cur.mat[2], (double)klbr_f6_cur.mat[3], (double)klbr_f6_cur.mat[4], (double)klbr_f6_cur.mat[5], (double)klbr_f6_cur.mat[6], (double)klbr_f6_cur.mat[7], (double)klbr_f6_cur.mat[8],
         (unsigned long)klbr_f6_cur.desc, klbr_f6_cur.ray ? "called" : "not called",
         (double)klbr_f6_cur.va[0], (double)klbr_f6_cur.va[1], (double)klbr_f6_cur.va[2], (double)mA, (double)eA, (double)klbr_f6_cur.vb[0], (double)klbr_f6_cur.vb[1], (double)klbr_f6_cur.vb[2], (double)mB, (double)eB,
         (unsigned long)klbr_f6_cur.req, (unsigned long)klbr_f6_cur.ret, !klbr_f6_cur.ray ? "n/a" : !klbr_f6_cur.ret ? "null: no hit" : klbr_f6_cur.ret == klbr_f6_cur.human ? "THE HUMAN (GUESS: same object)" : klud_is_player(klbr_f6_cur.ret) ? "another player" : "an entity / object", "");
}
static void klbr_f6_body_fn(int id, KLBR_F3REGS *r)      /* the stub handler's work (game thread); reads only */
{
    DWORD sp = r->esp; int net, i, ix = -1; KLBR_F6C *c; DWORD sm, role = 0;
    if (id == 8) { klbr_f7_aimat(r); return; }      /* FireProbe7: the AimAt entry */
    sm = KLBR_RDG(0x168e598); if (sm > 0xffff) role = klh_rd32(sm + 0x54);
    net = role == 2 || role == 3;
    if (id == 1) {
        DWORD item = r->esi, owner = klh_rd32(sp + 0x54), node, flags, h, own = 0, nn = 0, n1; int forced = (int)(r->ebx & 0xff), oc = 0, nc = 0, okn = 1, okm = 1, bit21, haveh;
        for (i = 0; i < KLBR_MAX; i++) if ((klbr_f6_body[i] && klbr_f6_body[i] == owner) || (klbr_f6_item[i] && klbr_f6_item[i] == item)) ix = i;
        c = &klbr_f6_c[net][ix >= 0];
        c->shots++; if (forced) c->forced++;
        memset(&klbr_f6_cur, 0, sizeof klbr_f6_cur);
        if (net && ix < 0) return;      /* online, an unmarked shooter: counted only */
        klbr_f6_cur.valid = 1; klbr_f6_cur.net = net; klbr_f6_cur.marked = ix >= 0; klbr_f6_cur.ix = ix; klbr_f6_cur.bl = forced; klbr_f6_cur.item = item; klbr_f6_cur.owner = owner;
        node = item > 0xffff ? klh_rd32(item + 4) : 0; flags = node > 0xffff ? klh_rd32(node + 0x3c) : 0; bit21 = kbr_f4_bit(flags, 21); klbr_f6_cur.bit21 = bit21;
        h = item > 0xffff ? klh_rd32(item + 0x5c) : 0; haveh = h != 0;
        if (forced && h && klbr_f6_flt < 3) { __try { own = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { own = 0; klbr_f6_flt++; } }
        n1 = node > 0xffff ? klh_rd32(node + 0x50) : 0; nn = n1 > 0xffff ? klh_rd32(n1 + 0x60) : 0;      /* GUESS: 0x598460(node) = [[node+0x50]+0x60] (read from its code) */
        __try { if (!forced) { okn = okm = 1; } else if (bit21 && own > 0xffff) oc = klbr_f6_clsgate(own, &okn); else if (!bit21 && nn > 0xffff) nc = klbr_f6_clsgate(nn, &okm); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; okn = okm = 0; }
        klbr_f6_cur.known = bit21 ? okn : okm; klbr_f6_cur.haveh = haveh; klbr_f6_cur.ownok = own > 0xffff;
        klbr_f6_cur.branch = forced ? kbr_f6_branch(bit21, haveh, own > 0xffff, oc, nn > 0xffff, nc) : 0;      /* 0 = vt+0x250 / 0x7cb080 not called (bl = 0) */
        c->br[klbr_f6_cur.branch]++;
        klbr_f6_cur.geo = klbr_f6_cur.branch != 1;      /* branch A0 leaves the outputs untouched: stack garbage, no geometry is derived from it */
        if (klbr_f6_cur.geo) { klh_rd(sp + 0x60, klbr_f6_cur.pos, 12); klh_rd(sp + 0xc4, klbr_f6_cur.mat, 36); }      /* the muzzle outputs: position [esp+0x60], 3x3 [esp+0xc4] (the args of the 0x4cb83a call) */
        if (klbr_f6_cur.geo && kbr_f6_is_ident(klbr_f6_cur.mat) && kbr_f6_is_zero3(klbr_f6_cur.pos)) { c->ident++; }
        klbr_f6_cur.havebp = owner > 0xffff && klh_rd(owner + 0x460, klbr_f6_cur.bp, 12) && kle_ok3(klbr_f6_cur.bp);
        klbr_f6_cur.havehp = klbr_f6_human(ix, &klbr_f6_cur.human, klbr_f6_cur.hp);
        if (ix >= 0 && klbr_f7on) klbr_f7_capture(ix, sp, item);      /* FireProbe7: read only, BEFORE RayAim rewrites T */
        if (klbr_raon && (klbr_ra_site & 1) && klbr_f6_cur.geo) klbr_ra_apply(1, sp, klbr_f6_cur.pos, sp + 0xc4);      /* RayAim S1: T at [esp+0xc4], origin V = klbr_f6_cur.pos */
        if (klbr_raon && (klbr_ra_site & 2) && klbr_f6_cur.geo) klbr_ra_aim(item, klbr_f6_cur.pos);      /* RayAim bit 2: the item aim point [item+0xc8..0xd0] (after bit 1 so the cone draw is shared) */
        if (klbr_f6on && c->nlm < KLBR_F6_LOGMAX) {
            c->nlm++;
            klog("brain: traitor fireprobe6 muzzle: networked %s %s bot %d item %08lx owner(esp+0x54) %08lx bl (muzzle path via vt+0x250) %d: [[item+4]+0x3c] %08lx bit21 %d, [item+0x5c] %08lx 0x8ccde0 -> %08lx, class test owner %d node [[node+0x50]+0x60] %08lx %d (%s); branch %s; outputs origin (%.1f %.1f %.1f) %s, matrix %s%s; 0x857110 identity fallback %s",
                 net ? "yes" : "no", ix >= 0 ? "MARKED" : "other", ix, (unsigned long)item, (unsigned long)owner, forced, (unsigned long)flags, bit21, (unsigned long)h, (unsigned long)own, oc, (unsigned long)nn, nc, klbr_f6_cur.known ? "class getter called" : "class test NOT run (no usable getter): GUESS miss",
                 kbr_f6_branch_name(klbr_f6_cur.branch), (double)klbr_f6_cur.pos[0], (double)klbr_f6_cur.pos[1], (double)klbr_f6_cur.pos[2], kbr_f6_is_zero3(klbr_f6_cur.pos) ? "ZERO" : "non-zero", kbr_f6_is_ident(klbr_f6_cur.mat) ? "IDENTITY" : "not identity", klbr_f6_cur.geo ? "" : " (A0: outputs untouched, not read)",
                 klbr_f6_cur.branch == 5 ? "RAN (predicted)" : "not predicted");
        }
        return;
    }
    if (!klbr_f6_cur.valid || klbr_f6_cur.item != r->esi) return;      /* a shot we did not record at S1 (online unmarked) */
    c = &klbr_f6_c[klbr_f6_cur.net][klbr_f6_cur.marked];
    if (id == 2) {
        BYTE ray = 0xff; klh_rd(sp + 0x17, &ray, 1);
        klbr_f6_cur.pass = 1; klbr_f6_cur.desc = r->eax; c->pass++; if (!r->eax) c->d0++;
        if (klbr_f6_cur.geo && klbr_f6_cur.havehp) { float e = klbr_f6_row_err(klbr_f6_cur.mat, klbr_f6_cur.pos, klbr_f6_cur.hp); c->rowb[kbr_f6_bucket(e)]++; }      /* passed shots only */
        klbr_f6_cur.ray = ray != 0 && ray != 0xff;      /* 1 = ray path */
        return;
    }
    if (id == 4) {
        klbr_f6_cur.ray = 1; c->ray++;
        klh_rd(sp + 0xf4, klbr_f6_cur.va, 12);      /* GUESS: the second pushed argument (lea ecx,[esp+0xf4]) */
        klbr_f6_cur.havevb = klh_rd(r->eax, klbr_f6_cur.vb, 12);      /* GUESS: the third pushed argument (eax = lea [esp+0x34 at the call]) */
        klbr_f6_cur.havem4 = klh_rd(sp + 0xf4, klbr_f6_cur.m4, 36);      /* the ray matrix M (9 floats at the site esp+0xf4), BEFORE RayAim writes it */
        if (klbr_f7on) klbr_f7_at_s4();
        if (klbr_raon && (klbr_ra_site & 4) && klbr_f6_cur.havevb && kbr_ra_finite(klbr_f6_cur.vb, 3)) klbr_ra_apply(4, sp, klbr_f6_cur.vb, sp + 0xf4);      /* RayAim S4: the ray start P = *eax is the origin */
        if (klbr_f6_cur.geo && klbr_f6_cur.havehp) { c->rayAb[kbr_f6_bucket(kbr_f6_ang(klbr_f6_cur.pos, klbr_f6_cur.va, klbr_f6_cur.hp))]++; c->rayBb[kbr_f6_bucket(kbr_f6_ang(klbr_f6_cur.pos, klbr_f6_cur.vb, klbr_f6_cur.hp))]++; }
        return;
    }
    if (id == 5) { klbr_f6_cur.req = r->eax; return; }      /* the request object, not a hit (review 11-04) */
    if (id == 7) {
        DWORD ent = klh_rd32(sp + 0x10);      /* the entity written by 'call [req vt+0x78]' (esp = E at 0x4cc644) */
        klbr_f6_cur.ret = ent;
        if (!ent) c->rnull++; else { c->rhit++; if (ent == klbr_f6_cur.human) c->rhuman++; else if (klud_is_player(ent)) c->rplayer++; }      /* GUESS: the hit entity is the player object itself (not a collision child) when it is the human */
        if (klbr_f7on) { klbr_f7_child(ent); klbr_f7_line(); }
        if (klbr_f6on) klbr_f6_shotline(c);
        klbr_f6_cur.valid = 0;
        return;
    }
    if (id == 6) { c->proj++; klbr_f6_cur.ray = 0; if (klbr_f7on) klbr_f7_line(); if (klbr_f6on) klbr_f6_shotline(c); klbr_f6_cur.valid = 0; return; }
}
static void __cdecl klbr_f6_hit(int id, KLBR_F3REGS *r)      /* called by the stubs on the game thread */
{
    if (!klbr_f6act || !r || klbr_f6_flt >= 3 || !klbr_f6_tid || GetCurrentThreadId() != klbr_f6_tid) return;      /* game thread only */
    __try { klbr_f6_body_fn(id, r); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_f6_cur.valid = 0; if (klbr_f6_flt <= 3) klog("brain: traitor fireprobe6: fault in the handler (site id %d): %d of 3 allowed", id, klbr_f6_flt); }
}
/* OnlineBrainTraitorFireProbe8 (11-04, after bs36/bs37; TEST build only, UNTESTED, recommended off; READ ONLY toward the game: no game byte is written except the 5-10 byte counting detours at install, the only game call is the pure handle lookup 0x8ccde0 under __try; game thread only; shares the FireProbe6 fault counter klbr_f6_flt).
   bs36/bs37: the traitor aims at the human (aim point within 0.1 deg of the chest, ~5800 of range 6000) and hp stays 550. Research wmcd2s92o: the damage carriers are the pellet bullets built in the loop 0x4cc1c0..0x4cc317 of 0x4cb7a0 (BEFORE the gate 0x4cc389), descriptor built at 0x4cc1a1
   by ctor 0x748900 (desc+0 = shooter handle 0x6ece90(0x6ee930(item)), +4 item handle, +8/+0xc floats), per pellet a pooled entity from template vt+0x2bc (null skips), ZProjectile (vtable 0xba925c) Activate slot 35 0x900d80 copies the descriptor, hit callback slot 36 0x6f7950 ([comp+0x34] shooter handle,
   victim = 0x8ccde0([hit+0x3c]); a null victim drops at 0x6f7a86), the send at 0x6f7c6e, the victim side slot 424 0x4db580. A counting funnel; every site was disassembled 11-04 (debug/dasm.py): whole instructions, no relative operand, no jump of the routine into the stolen range:
     S1a id 11 0x4cc1c0 (6)  8b 4c 24 6c 8b 11            mov ecx,[esp+0x6c] ; mov edx,[ecx]   the pellet loop head (the only jumps to it: 0x4cc1b6 and the loop's jb 0x4cc31c). Same esp as the descriptor call: [esp+0x58] = pellet count ([ebp vt+0x2a0] result stored at 0x4cb8cc), [esp+0x24] = the object
        from item vt+0x2ec (stored at 0x4cb8e2; its +0x1a4 is the dword 0x4cb8dc loads - the 'template' of the task text), descriptor at esp+0x164, ebx = pellet index, esi = item. Counts iterations; at ebx == 0 logs the shot and remembers desc+0 (the shooter handle) as the marked bot's handle.
     S1b id 12 0x4cc1d8 (8)  8b 17 8b 92 88 00 00 00      mov edx,[edi] ; mov edx,[edx+0x88]   the non-null pellet path (the je at 0x4cc1d2 skips it): edi = the pooled entity. null pellets = iterations - non-null.
     S2  id 13 0x900d80 (6)  56 57 8b 7c 24 0c            push esi ; push edi ; mov edi,[esp+0xc]   ZProjectile Activate (slot 35): ecx = component, [esp+4] = descriptor. HASHED range 0x900000-0x906000: refused unless [KLHook] SessionSafe=0.
     S3  id 14 0x8ccde0 (10) 8b 44 24 04 8b 0d 90 ff e0 00 mov eax,[esp+4] ; mov ecx,[0xe0ff90]   the handle -> entity lookup (UNHASHED, hot): used as a PROXY for the hashed hit callback 0x6f7950 (0x6e8000-0x6f9000): the handler returns at once unless the return address is 0x6f796c (the FIRST lookup
        of the callback, [hit+0x3c] = the victim handle, esi = component, edi = hit). Counts the callback entries that reach it; [comp+0x34] = shooter handle, [comp+0x38], victim, [comp+0x54], [comp+0xb8], [comp+0x90] are logged.
     S4  id 15 0x596fc0 (5)  56 8b 74 24 08               push esi ; mov esi,[esp+8]   (UNHASHED) the proxy for the send: called at 0x6f7c37 (return 0x6f7c3c) with ecx = component and the victim as the only argument, a SingleDoor/MultiDoor class check on the victim (vt+0xfc); both branches reach a vt+0x128 send, so s4 = the hit reached the door check (not dropped earlier), NOT proof it was not dropped later.
     S5  id 16 0x4db580 (6)  83 ec 40 56 8b f1            sub esp,0x40 ; push esi ; mov esi,ecx   the victim side (slot 424): ecx = victim. HASHED (0x4db000-0x4dd000): refused unless SessionSafe=0. Counts entries whose victim is the host-local human and how many happened within 2 s of a marked pellet loop.
   Only marked bots count for s1..s4 (S1a needs the FireProbe6 S1 shot record: klbr_f6_cur is valid, marked, same item; the other filters compare the shooter handle with the handles S1a remembered). Baselines (not filtered by mark): s2 by shooter class (player / other), s3all, s5all. The hashed sites are skipped with a log line under SessionSafe=1 (the default). */
#define KLBR_F8_LOGMAX 8
#define KLBR_F8_LOSVMAX 24      /* losvar lines per round (every 32nd blocked marked shot) */
#define KLBR_F8_NSITE 6
#define KLBR_F8_NEARMS 2000
static int klbr_f8on, klbr_f8_state, klbr_f8_flt, klbr_f8_nok;
static BYTE *klbr_f8_stub;
static DWORD klbr_f8_lastmark;      /* GetTickCount of the last marked pellet-loop iteration (0 = none this round) */
typedef struct { DWORD site; int len; BYTE b[10]; int id; } KLBR_F8SITE;
static const KLBR_F8SITE klbr_f8_sites[KLBR_F8_NSITE] = {
    { 0x4cc1c0, 6, { 0x8b, 0x4c, 0x24, 0x6c, 0x8b, 0x11 }, 11 },
    { 0x4cc1d8, 8, { 0x8b, 0x17, 0x8b, 0x92, 0x88, 0x00, 0x00, 0x00 }, 12 },
    { 0x900d80, 6, { 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c }, 13 },
    { 0x8ccde0, 10, { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00 }, 14 },
    { 0x596fc0, 5, { 0x56, 0x8b, 0x74, 0x24, 0x08 }, 15 },
    { 0x4db580, 6, { 0x83, 0xec, 0x40, 0x56, 0x8b, 0xf1 }, 16 } };
typedef struct { long shots, iter, ok, pelsum, s2, s2player, s2other, s3, s3all, s3null, s3human, s3obj, s4, s4human, s5all, s5human, s5near, nl1, nl1p, nl2, nl3, nl4, nl5, los[3], eye[3], nlos, nlosv, ahTot, ahLt5, ahNone, ahIsHuman, ahHumLt5, nlh; } KLBR_F8C;      /* los / eye: clear, blocked, error per marked shot from the muzzle origin / the bot eye (LosProbe) */
static KLBR_F8C klbr_f8_c;
static DWORD klbr_f8_hand[KLBR_MAX];      /* the marked bots' shooter handles (desc+0 of their last pellet loop) */
static void klbr_f8_rtti(DWORD obj, char *out, int cap)      /* class name of a C++ object (copy of klauto.c kla_rtti: vtable[-1] -> locator -> type descriptor + 8); every read guarded, "" on any failure */
{
    char raw[96]; DWORD vt, col, td, p; int n = 0, end = 0, i;
    out[0] = 0;
    if (obj <= 0xffff || (vt = klh_rd32(obj)) <= 0xffff || !(col = klh_rd32(vt - 4)) || klh_rd32(col) != 0 || !(td = klh_rd32(col + 12))) return;
    p = td + 8;
    while (!end && n < (int)sizeof raw - 1) {
        int room = 0x1000 - (int)((p + n) & 0xfff), want = (int)sizeof raw - 1 - n;
        if (want > room) want = room;
        if (!klh_rd(p + n, raw + n, want)) break;
        for (i = 0; i < want && raw[n + i]; i++) if ((BYTE)raw[n + i] < 0x20 || (BYTE)raw[n + i] > 0x7e) raw[n + i] = '?';
        end = i < want; n += i;
    }
    raw[n] = 0;
    if (strncmp(raw, ".?A", 3) || !raw[3]) return;
    { char *e = strstr(raw, "@@"); if (e) *e = 0; }
    _snprintf(out, cap, "%s", raw + 4); out[cap - 1] = 0;
}
static float klbr_f8_fl(DWORD v) { float f; memcpy(&f, &v, 4); return f; }
static DWORD klbr_f8_ref(DWORD h)      /* handle -> entity (the game's lookup, pure), 0 on any fault */
{
    DWORD o = 0;
    __try { o = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { o = 0; klbr_f6_flt++; klbr_f8_flt++; }
    return o;
}
static int klbr_f8_marked_shot(const KLBR_F3REGS *r) { return klbr_f6_cur.valid && klbr_f6_cur.marked && klbr_f6_cur.ix >= 0 && klbr_f6_cur.item == r->esi; }
static int klbr_f8_is_marked_handle(DWORD h) { return kbr_f8_in_set((const kbr_u32 *)klbr_f8_hand, KLBR_MAX, h); }
static int klbr_f8_shooter_marked(DWORD h, DWORD *obj)      /* the shooter handle is a remembered one, or resolves to a marked body / soldier */
{
    int i; DWORD o;
    *obj = 0;
    if (klbr_f8_is_marked_handle(h)) return 1;
    o = h ? klbr_f8_ref(h) : 0; *obj = o;
    if (o > 0xffff) for (i = 0; i < KLBR_MAX; i++) if ((klbr_f6_body[i] && klbr_f6_body[i] == o) || (klbr_f6_sold[i] && klbr_f6_sold[i] == o)) return 2;
    return 0;
}
static void klbr_f8_body_fn(int id, KLBR_F3REGS *r)
{
    DWORD sp = r->esp, now = GetTickCount(); KLBR_F8C *c = &klbr_f8_c;
    if (id == 11) {
        DWORD d[16], npel, obj, t1a4, k; int ix;
        if (!klbr_f8_marked_shot(r)) return;
        ix = klbr_f6_cur.ix; c->iter++; klbr_f8_lastmark = now ? now : 1;
        if (r->ebx != 0) return;      /* first pellet of the shot: the descriptor and counts */
        c->shots++;
        memset(d, 0, sizeof d); klh_rd(sp + 0x164, d, 0x40);
        npel = klh_rd32(sp + 0x58); obj = klh_rd32(sp + 0x24); t1a4 = obj > 0xffff ? klh_rd32(obj + 0x1a4) : 0; c->pelsum += (long)npel;
        klbr_f8_hand[ix] = d[0];
        {      /* Task C (read only): angle between the item aim point direction (origin -> [item+0xc8..0xd0]) and the direction origin -> the current HOLDER entity, beside the human angle.
                  HOLDER = the B-list holder of the 'traitor target ... HOLDER' line: B = [soldier+0x698], so = [B+0x154], holder entity pointer = [so+0xac] (the +4 of the holder record at so+0xa8: that offset is a GUESS, only +8 is confirmed).
                  Holder point = [holder+0x460] + KLBR_LOS_CHEST in y (GUESS: same convention as the human chest). Aim point: FireProbe7's read of this shot when FireProbe7 ran (before any RayAim write), else a live read of [item+0xc8] now (may already be rewritten by RayAim bit 2). */
            DWORD S = klbr_f6_sold[ix], Bq = S > 0xffff ? klh_rd32(S + 0x698) : 0, so = Bq > 0xffff ? klh_rd32(Bq + 0x154) : 0, hent = so > 0xffff ? klh_rd32(so + 0xac) : 0;
            float ap[3], hpnt[3], hpos[3], ah = -1.0f, ahum = -1.0f; int haveap = 0, haveh = 0, live = 0; char hcls[80];
            hcls[0] = 0;
            if (klbr_f7_cur.valid && klbr_f7_cur.ix == ix && klbr_f7_cur.havea) { memcpy(ap, klbr_f7_cur.ap, 12); haveap = 1; }
            else if (klbr_f6_cur.item > 0xffff && klh_rd(klbr_f6_cur.item + 0xc8, ap, 12)) { haveap = 1; live = 1; }
            if (haveap && !kbr_ra_finite(ap, 3)) haveap = 0;
            if (hent > 0xffff && klh_rd(hent + 0x460, hpos, 12) && kle_ok3(hpos)) { hpnt[0] = hpos[0]; hpnt[1] = hpos[1] + KLBR_LOS_CHEST; hpnt[2] = hpos[2]; haveh = 1; klbr_f8_rtti(hent, hcls, sizeof hcls); }
            c->ahTot++;
            if (haveap && haveh && klbr_f6_cur.geo && !kbr_f6_is_zero3(klbr_f6_cur.pos)) {
                float ch2[3];
                ah = kbr_f6_ang(klbr_f6_cur.pos, ap, hpnt);
                if (ah >= 0.0f && ah < 5.0f) c->ahLt5++;
                if (klbr_f6_cur.havehp) { ch2[0] = klbr_f6_cur.hp[0]; ch2[1] = klbr_f6_cur.hp[1] + KLBR_LOS_CHEST; ch2[2] = klbr_f6_cur.hp[2]; ahum = kbr_f6_ang(klbr_f6_cur.pos, ap, ch2); if (ahum >= 0.0f && ahum < 5.0f) c->ahHumLt5++; }
            } else c->ahNone++;
            if (hent > 0xffff && klbr_f6_cur.human == hent) c->ahIsHuman++;
            if (c->nlh < KLBR_F8_LOGMAX) {
                c->nlh++;
                klog("brain: fireprobe8 aimholder: bot %d shot %ld: aim point %s; HOLDER entity %08lx class %s%s: angle aim->holder %.2f deg (-1 = unknown), aim->human chest %.2f deg (-1 = unknown)",
                     ix, c->shots, !haveap ? "unreadable" : live ? "live read (may be RayAim-rewritten)" : "FireProbe7 read", (unsigned long)hent, hcls[0] ? hcls : "?", (hent > 0xffff && klbr_f6_cur.human == hent) ? " (= the shot's human)" : "", (double)ah, (double)ahum);
            }
        }
        if (klbr_losprobe && klbr_f6_cur.havehp) {      /* OnlineBrainTraitorLosProbe: the game's physics line test, muzzle origin and bot eye to the human chest (our own buffer; reads the collision world only) */
            float ch[3], eye[3]; int ok1 = 0, ok2 = 0, cl1 = 0, cl2 = 0, fl0 = klbr_los_flt, haveo = klbr_f6_cur.geo && !kbr_f6_is_zero3(klbr_f6_cur.pos), havee = klbr_f6_cur.havebp;
            ch[0] = klbr_f6_cur.hp[0]; ch[1] = klbr_f6_cur.hp[1] + KLBR_LOS_CHEST; ch[2] = klbr_f6_cur.hp[2];
            eye[0] = klbr_f6_cur.bp[0]; eye[1] = klbr_f6_cur.bp[1] + KLBR_LOS_EYE; eye[2] = klbr_f6_cur.bp[2];
            if (havee) klbr_los_control(ix, eye);
            if (haveo) { cl1 = klbr_los_clear(klbr_f6_cur.pos, ch, &ok1); c->los[ok1 ? (cl1 ? 0 : 1) : 2]++; }
            if (havee) { cl2 = klbr_los_clear(eye, ch, &ok2); c->eye[ok2 ? (cl2 ? 0 : 1) : 2]++; }
            if (klbr_los_flt != fl0) { klbr_f6_flt++; klbr_f8_flt++; }      /* a fault in the query counts against the shared limit */
            if (c->nlos < KLBR_F8_LOGMAX) {
                c->nlos++;
                klog("brain: fireprobe8 los: bot %d shot %ld: muzzle %.0f %.0f %.0f -> human chest %.0f %.0f %.0f (%.1f m): %s; bot eye -> chest (%.1f m): %s",
                     ix, c->shots, (double)klbr_f6_cur.pos[0], (double)klbr_f6_cur.pos[1], (double)klbr_f6_cur.pos[2], (double)ch[0], (double)ch[1], (double)ch[2], haveo ? (double)kbr_f6_dist(klbr_f6_cur.pos, ch) / 100.0 : -1.0, !haveo ? "no muzzle origin" : !ok1 ? "QUERY FAILED" : cl1 ? "CLEAR" : "BLOCKED",
                     havee ? (double)kbr_f6_dist(eye, ch) / 100.0 : -1.0, !havee ? "no bot position" : !ok2 ? "QUERY FAILED" : cl2 ? "CLEAR" : "BLOCKED");
            } else if (haveo && ok1 && !cl1 && c->nlosv < KLBR_F8_LOSVMAX && (c->shots & 31) == 0) {
                /* 11-05 bs73 DD03: muzzle blocked 726/758 while the eye was clear 714, and the 8 lines above all came from the first spot. Which variant clears tells low cover (raised muzzle),
                   a muzzle inside a wall (muzzle pushed 50 toward the chest) or a blocker near the target (none). Sampled every 32nd shot after the first 8, blocked shots only. */
                static const char *vn[3] = { "muzzle+60y", "muzzle+100y", "muzzle+50fwd" };
                char vr[3][16]; float o[3], dd = kbr_f6_dist(klbr_f6_cur.pos, ch); int v, okv, clv;
                c->nlosv++;
                for (v = 0; v < 3; v++) {
                    o[0] = klbr_f6_cur.pos[0]; o[1] = klbr_f6_cur.pos[1]; o[2] = klbr_f6_cur.pos[2];
                    if (v == 0) o[1] += 60.0f; else if (v == 1) o[1] += 100.0f;
                    else if (dd > 100.0f) { o[0] += (ch[0] - o[0]) * 50.0f / dd; o[1] += (ch[1] - o[1]) * 50.0f / dd; o[2] += (ch[2] - o[2]) * 50.0f / dd; }
                    okv = 0; clv = klbr_los_clear(o, ch, &okv);
                    strcpy(vr[v], !okv ? "QUERY FAILED" : clv ? "CLEAR" : "BLOCKED");
                }
                if (klbr_los_flt != fl0) { klbr_f6_flt++; klbr_f8_flt++; }
                klog("brain: fireprobe8 losvar: bot %d shot %ld: bot %.0f %.0f %.0f muzzle %.0f %.0f %.0f (muzzle-bot y %.0f) -> chest %.0f %.0f %.0f (%.1f m): muzzle BLOCKED, %s %s, %s %s, %s %s, bot eye %s",
                     ix, c->shots, havee ? (double)klbr_f6_cur.bp[0] : 0.0, havee ? (double)klbr_f6_cur.bp[1] : 0.0, havee ? (double)klbr_f6_cur.bp[2] : 0.0,
                     (double)klbr_f6_cur.pos[0], (double)klbr_f6_cur.pos[1], (double)klbr_f6_cur.pos[2], havee ? (double)(klbr_f6_cur.pos[1] - klbr_f6_cur.bp[1]) : -1.0,
                     (double)ch[0], (double)ch[1], (double)ch[2], (double)dd / 100.0, vn[0], vr[0], vn[1], vr[1], vn[2], vr[2], !havee ? "n/a" : !ok2 ? "QUERY FAILED" : cl2 ? "CLEAR" : "BLOCKED");
            }
        }
        if (c->nl1 < KLBR_F8_LOGMAX) {
            c->nl1++; k = (DWORD)ix;
            klog("brain: fireprobe8 s1 shot: bot %lu item %08lx: pellet count [esp+0x58] %lu, [esp+0x24] %08lx -> [+0x1a4] %08lx; descriptor (esp+0x164): +0 shooter handle %08lx +4 item handle %08lx +8 %.3f +0xc %.3f +0x10 %08lx +0x14 %08lx +0x18 %08lx +0x1c %08lx +0x2c %.3f +0x30 %.3f +0x34 %.3f +0x38 %.3f +0x3c %08lx",
                 (unsigned long)k, (unsigned long)r->esi, (unsigned long)npel, (unsigned long)obj, (unsigned long)t1a4, (unsigned long)d[0], (unsigned long)d[1], (double)klbr_f8_fl(d[2]), (double)klbr_f8_fl(d[3]), (unsigned long)d[4], (unsigned long)d[5], (unsigned long)d[6], (unsigned long)d[7],
                 (double)klbr_f8_fl(d[11]), (double)klbr_f8_fl(d[12]), (double)klbr_f8_fl(d[13]), (double)klbr_f8_fl(d[14]), (unsigned long)d[15]);
        }
        return;
    }
    if (id == 12) {
        DWORD ent = r->edi;
        if (!klbr_f8_marked_shot(r)) return;
        c->ok++;
        if (c->nl1p < KLBR_F8_LOGMAX) { c->nl1p++; klog("brain: fireprobe8 s1 pellet: bot %d item %08lx pellet index %lu: pooled entity edi %08lx vtable %08lx (non-null)", klbr_f6_cur.ix, (unsigned long)r->esi, (unsigned long)r->ebx, (unsigned long)ent, (unsigned long)klh_rd32(ent)); }
        return;
    }
    if (id == 13) {
        DWORD desc = klh_rd32(sp + 4), h = desc > 0xffff ? klh_rd32(desc) : 0, comp = r->ecx, obj = 0; int mk = h ? klbr_f8_shooter_marked(h, &obj) : 0, pl;
        if (obj == 0 && h) obj = klbr_f8_ref(h);
        pl = obj > 0xffff && klud_is_player(obj);
        if (pl) c->s2player++; else c->s2other++;      /* baseline: every ZProjectile Activate, by the shooter's class */
        if (!mk) return;
        c->s2++;
        if (c->nl2 < KLBR_F8_LOGMAX) {
            DWORD d[16]; c->nl2++; memset(d, 0, sizeof d); klh_rd(desc, d, 0x40);
            klog("brain: fireprobe8 s2 activate: component %08lx descriptor %08lx: +0 %08lx (shooter obj %08lx) +4 %08lx +8 %.3f +0xc %.3f +0x14 %08lx +0x18 %08lx +0x1c %08lx +0x3c %08lx; [comp+0x24] %08lx",
                 (unsigned long)comp, (unsigned long)desc, (unsigned long)d[0], (unsigned long)obj, (unsigned long)d[1], (double)klbr_f8_fl(d[2]), (double)klbr_f8_fl(d[3]), (unsigned long)d[5], (unsigned long)d[6], (unsigned long)d[7], (unsigned long)d[15], (unsigned long)klh_rd32(comp + 0x24));
        }
        return;
    }
    if (id == 14) {      /* proxy for 0x6f7950: the first lookup, return address 0x6f796c (filtered in the stub handler) */
        DWORD comp = r->esi, hit = r->edi, vh = klh_rd32(sp + 4), sh = klh_rd32(comp + 0x34), vic, me = 0, sobj = 0; int mk, human; char vcls[80], vtxt[96];
        c->s3all++;
        mk = klbr_f8_shooter_marked(sh, &sobj);
        if (!mk) return;
        c->s3++; if (mk == 2) c->s3obj++;
        vic = klbr_f8_ref(vh); klud_local(&me);
        human = vic > 0xffff && vic == me;
        if (vic <= 0xffff) c->s3null++;
        if (human) c->s3human++;
        if (c->nl3 < KLBR_F8_LOGMAX) {
            c->nl3++; klbr_f8_rtti(vic, vcls, sizeof vcls); _snprintf(vtxt, sizeof vtxt, vcls[0] ? " class %s" : " class ?", vcls); vtxt[sizeof vtxt - 1] = 0;
            klog("brain: fireprobe8 s3 hit callback: component %08lx hit %08lx: shooter handle [comp+0x34] %08lx (%s), weapon [comp+0x38] %08lx, victim handle [hit+0x3c] %08lx -> %08lx %s%s; [comp+0x54] %08lx [comp+0xb8] %08lx (%.3f) [comp+0x90] %08lx (%.3f) [comp+0xb7] %02lx [comp+0x24] %08lx",
                 (unsigned long)comp, (unsigned long)hit, (unsigned long)sh, mk == 1 ? "remembered handle" : "resolves to a marked body", (unsigned long)klh_rd32(comp + 0x38), (unsigned long)vh, (unsigned long)vic, vic <= 0xffff ? "NULL VICTIM (the callback drops at 0x6f7a86)" : human ? "= THE HOST-LOCAL HUMAN" : klud_is_player(vic) ? "another player" : "not a player", vtxt,
                 (unsigned long)klh_rd32(comp + 0x54), (unsigned long)klh_rd32(comp + 0xb8), (double)klbr_f8_fl(klh_rd32(comp + 0xb8)), (unsigned long)klh_rd32(comp + 0x90), (double)klbr_f8_fl(klh_rd32(comp + 0x90)), (unsigned long)(klh_rd32(comp + 0xb4) >> 24), (unsigned long)klh_rd32(comp + 0x24));
        }
        return;
    }
    if (id == 15) {      /* proxy for the send: 0x596fc0 called at 0x6f7c37 (filtered in the stub handler) */
        DWORD comp = r->ecx, vic = klh_rd32(sp + 4), sh = klh_rd32(comp + 0x34), sobj = 0, me = 0; int mk = klbr_f8_shooter_marked(sh, &sobj), human;
        if (!mk) return;
        klud_local(&me); human = vic > 0xffff && vic == me;
        c->s4++; if (human) c->s4human++;
        if (c->nl4 < KLBR_F8_LOGMAX) { c->nl4++; klog("brain: fireprobe8 s4 send path: component %08lx shooter handle %08lx victim (arg) %08lx %s: this hit reached the door-class check before the send (a later drop is not excluded) (vt+0x128 of [comp+0x24] %08lx)", (unsigned long)comp, (unsigned long)sh, (unsigned long)vic, human ? "= THE HOST-LOCAL HUMAN" : klud_is_player(vic) ? "another player" : "not a player", (unsigned long)klh_rd32(comp + 0x24)); }
        return;
    }
    if (id == 16) {
        DWORD vic = r->ecx, me = 0; int near_;
        c->s5all++;
        klud_local(&me);
        if (!(vic > 0xffff && vic == me)) return;
        c->s5human++; near_ = kbr_f8_near(now, klbr_f8_lastmark, KLBR_F8_NEARMS);
        if (near_) c->s5near++;
        if (c->nl5 < KLBR_F8_LOGMAX) { c->nl5++; klog("brain: fireprobe8 s5 victim entry: victim %08lx = the host-local human; %s a marked pellet loop (last %lu ms ago); arg1 %08lx", (unsigned long)vic, near_ ? "WITHIN 2 s of" : "not within 2 s of", klbr_f8_lastmark ? (unsigned long)(now - klbr_f8_lastmark) : 0UL, (unsigned long)klh_rd32(sp + 4)); }
        return;
    }
}
static void __cdecl klbr_f8_hit(int id, KLBR_F3REGS *r)      /* called by the stubs on the game thread */
{
    if (!klbr_f8on || !r) return;
    if (id == 14 || id == 15) {      /* hot functions: leave at once unless the caller is the hit callback (return address 0x6f796c / 0x6f7c3c) */
        DWORD ra = 0;
        __try { ra = *(volatile DWORD *)(DWORD_PTR)r->esp; } __except (EXCEPTION_EXECUTE_HANDLER) { return; }
        if (ra != (DWORD)(DWORD_PTR)KLH_VA(id == 14 ? 0x6f796c : 0x6f7c3c)) return;
    }
    if (klbr_f6_flt >= 3 || !klbr_f6_tid || GetCurrentThreadId() != klbr_f6_tid) return;      /* game thread only, shared fault limit */
    __try { klbr_f8_body_fn(id, r); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_f8_flt++; if (klbr_f8_flt <= 3) klog("brain: fireprobe8: fault in the handler (site id %d): %d of 3 allowed", id, klbr_f6_flt); }
}
static void klbr_f8_install(void)      /* once (game thread) after the FireProbe6 sites; a refusal is final for the run */
{
    int s, ok = 0; BYTE cur[16], jmp[16]; DWORD stub;
    if (klbr_f8_state) return;
    klbr_f8_state = -1;
    if (!klbr_f8_stub && !(klbr_f8_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: fireprobe8: no memory for the stubs: off"); return; }
    for (s = 0; s < KLBR_F8_NSITE; s++) {
        const KLBR_F8SITE *k = &klbr_f8_sites[s]; BYTE *at = KLH_VA(k->site); int n;
        memset(cur, 0, sizeof cur);
        if (klh_is_hashed(k->site, k->len)) { klog("brain: fireprobe8: site %d 0x%x is inside a hashed range: NOT installed (SessionSafe=0 is needed, a direct-boot run only)%s", k->id, (unsigned)k->site, klh_policy == KLH_DIRECT ? " - policy 'direct': trying" : ""); if (klh_policy != KLH_DIRECT) continue; }
        if (!klh_rd((DWORD_PTR)at, cur, k->len) || memcmp(cur, k->b, k->len)) { klog("brain: fireprobe8: site %d 0x%x bytes differ from the expected %d (got %02x %02x %02x %02x %02x %02x %02x %02x): NOT installed", k->id, (unsigned)k->site, k->len, cur[0], cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7]); continue; }
        stub = (DWORD)(DWORD_PTR)(klbr_f8_stub + s * 0x40);
        n = kbr_f3_emit(klbr_f8_stub + s * 0x40, stub, k->id, (DWORD)(DWORD_PTR)klbr_f8_hit, k->b, k->len, (DWORD)(DWORD_PTR)(at + k->len));
        if (!n) { klog("brain: fireprobe8: site %d: stub not built", k->id); continue; }
        kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, k->len);
        if (klh_poke(at, k->b, k->len, jmp, k->len, "brain: FireProbe8 counting detour")) { ok++; klog("brain: fireprobe8: site %d 0x%x (%d bytes stolen) installed, stub %d bytes", k->id, (unsigned)k->site, k->len, n); }
        else klog("brain: fireprobe8: site %d 0x%x NOT installed (refused by the patch guard - a SHIP build writes no code - or the bytes differ)", k->id, (unsigned)k->site);
    }
    klbr_f8_nok = ok; klbr_f8_state = ok == KLBR_F8_NSITE ? 1 : ok ? 2 : -1;
    klog("brain: fireprobe8: %d of %d sites installed (state %d)", ok, KLBR_F8_NSITE, klbr_f8_state);
}
static void klbr_f8_summary(const char *why)
{
    KLBR_F8C *c = &klbr_f8_c; char losx[160];
    if (!klbr_f8on) return;
    losx[0] = 0;
    if (klbr_losprobe) _snprintf(losx, sizeof losx, "; los clear=%ld blocked=%ld err=%ld (from the bot eye: clear=%ld blocked=%ld err=%ld)", c->los[0], c->los[1], c->los[2], c->eye[0], c->eye[1], c->eye[2]);
    losx[sizeof losx - 1] = 0;
    if (c->ahTot) klog("brain: fireprobe8 %s aimholder: marked shots %ld; aim->holder <5deg= %ld (unknown %ld, holder is the shot's human %ld); aim->human chest <5deg= %ld", why, c->ahTot, c->ahLt5, c->ahNone, c->ahIsHuman, c->ahHumLt5);
    if (!c->iter && !c->s2player && !c->s2other && !c->s3all && !c->s5all) return;
    klog("brain: fireprobe8 %s: shots %ld pellet-count-sum %ld s1null=%ld s1ok=%ld s2=%ld (baseline s2 shooter player %ld other %ld) s3=%ld (s3 by body %ld, victim null %ld, all callbacks %ld) s3human=%ld s4=%ld s4human=%ld s5all=%ld s5human=%ld s5near=%ld (sites installed %d of %d; faults %d, shared %d)%s",
         why, c->shots, c->pelsum, kbr_f8_nulls(c->iter, c->ok), c->ok, c->s2, c->s2player, c->s2other, c->s3, c->s3obj, c->s3null, c->s3all, c->s3human, c->s4, c->s4human, c->s5all, c->s5human, c->s5near, klbr_f8_nok, KLBR_F8_NSITE, klbr_f8_flt, klbr_f6_flt, losx);
}
/* OnlineBrainTraitorModeBProbe (11-04; TEST build only, UNTESTED, recommended off; READ ONLY toward the game: no game byte is written except the 5-10 byte counting detours at install; game thread only; every read under __try; shares the FireProbe6 fault counter klbr_f6_flt, limit 3).
   Question (research w4funhvyl, verified): does a marked online traitor bot ever run the stock ZAttackTarget mode-B firing-position search (tick 0x4f4460; candidates 0x4f4b5f..0x4f4ba7, clear-line test 0x4e1750 at 0x4f4b92, RunChild at 0x4f4bed), and if not, where does the chain stop
   (slot 83 0x831850 never creates the goal / only stores [S+0x720] / only retargets; the goal never ticks; no candidate is clear; ...). All sites were disassembled 11-04 (debug/dasm.py): whole instructions, no relative operand, no jump of the routine targets the inside of a stolen range (the only jumps into the routine's
   stolen starts are 0x4f4b6b jle -> 0x4f4ba9 and 0x4f4b99 jne -> 0x4f4bd1, both at the first byte). Hash status (klranges.h, 11-04): 0x831850 and 0x800650 unhashed, the six 0x4f4xxx sites hashed ([0x4f0000,0x4f6000)); all go through klh_poke, so SessionSafe=1 installs the two and the guard refuses the rest, SessionSafe=0 installs all:
     m1 id 21 0x831850 (5) 55 8b ec 51 53                          slot 83 entry: ecx = soldier S, [esp+4] = handle (arg1), [esp] = return. [[S+0x5ac]+8] and [[S+0x658]+8] -> branch (kbr_mb_branch), no write.
     m2 id 22 0x4f4460 (9) 55 8b ec 81 ec bc 00 00 00              ZAttackTarget tick head: ecx = goal g, [g+4] = soldier (the tick loads [[g+4]+0x40] = body, and uses [g+4] for +0x4fc / +0xe4 / vt calls: H), [g+8] state, [g+0x14] target handle.
     m3 id 23 0x4f4b5f (10) 8b 5d f8 c7 45 ec 00 00 00 00          candidate count [ebp-8] (stored by 0x42ba10 just before), esi = goal.
     m4 id 24 0x4f4b9b (7) 8b 45 ec 40 83 c7 0c                    the NOT clear branch after call 0x4e1750 (al == 0 at 0x4f4b97, the jne at 0x4f4b99 fell through): index [ebp-0x14]. Stolen instead of 0x4f4b97 itself because the following jne has a relative operand.
     m5 id 25 0x4f4bd1 (9) 8b 4e 04 81 c1 e4 00 00 00              the CLEAR branch (al != 0, jne taken): index [ebp-0x14]; index 0 = the bot stays, index > 0 = RunChild follows. 'stockclear': al != 0 means clear HERE, the opposite polarity of klbr_los_clear (al == 0 = clear for the raw physics call).
     m6 id 26 0x4f4ba9 (5) 8b 4e 04 8b 01                          the no-clear tail (also reached by the jle at 0x4f4b6b when the candidate count is <= 0): sets [body+0x4fc] = 1 and calls vt+0x13c.
     m7 id 27 0x4f4bed (9) 8b 40 74 6a 01 51 8d 14 5b              RunChild: ecx = soldier, ebx = index, the point is the vec3 at ebp - 0xbc + 12 * ebx (0x4f4bf3..0x4f4bf9).
     m8 id 28 0x800650 (6) 8b 86 6c 05 00 00                       the instruction after 'call 0x5faeb0' in soldier vt+0x74 (0x800630): esi = soldier, the run-task re-arm (the only caller of 0x5faeb0).
   From m7 on, the existing brain tick samples the bot-to-point distance every 500 ms for 10 s (body+0x460 position; GUESS: same field the FireProbe lines use as the bot position). Only marked bots (klbr_f6_sold, set by the slot-113 wrapper) count; needs the FireProbe keys' wrapper like FireProbe8.
   Lines 'brain: modeb s83/tick/cand/notclear/clear/none/runchild/rearm/dist ...' (first 8 each per round, dist at most 200) and 'brain: modeb round: ...'. */
#define KLBR_MB_LOGMAX 8
#define KLBR_MB_NSITE 8
#define KLBR_MB_WINMS 10000
#define KLBR_MB_STEPMS 500
static int klbr_mbon, klbr_mb_state, klbr_mb_flt, klbr_mb_nok;
static BYTE *klbr_mb_stub;
typedef struct { DWORD site; int len; BYTE b[10]; int id; } KLBR_MBSITE;
static const KLBR_MBSITE klbr_mb_sites[KLBR_MB_NSITE] = {
    { 0x831850, 5, { 0x55, 0x8b, 0xec, 0x51, 0x53 }, 21 },
    { 0x4f4460, 9, { 0x55, 0x8b, 0xec, 0x81, 0xec, 0xbc, 0x00, 0x00, 0x00 }, 22 },
    { 0x4f4b5f, 10, { 0x8b, 0x5d, 0xf8, 0xc7, 0x45, 0xec, 0x00, 0x00, 0x00, 0x00 }, 23 },
    { 0x4f4b9b, 7, { 0x8b, 0x45, 0xec, 0x40, 0x83, 0xc7, 0x0c }, 24 },
    { 0x4f4bd1, 9, { 0x8b, 0x4e, 0x04, 0x81, 0xc1, 0xe4, 0x00, 0x00, 0x00 }, 25 },
    { 0x4f4ba9, 5, { 0x8b, 0x4e, 0x04, 0x8b, 0x01 }, 26 },
    { 0x4f4bed, 9, { 0x8b, 0x40, 0x74, 0x6a, 0x01, 0x51, 0x8d, 0x14, 0x5b }, 27 },
    { 0x800650, 6, { 0x8b, 0x86, 0x6c, 0x05, 0x00, 0x00 }, 28 } };
typedef struct { long s83[6], ticks, cand, candsum, notclear, clear0, clearN, none, none0, runchild, rearm, rearm_win, dist, nl[9], dsamp, datk, ahist[5], aother, anull, dnocl, dtrans, dlog, vth[4], modeh[6], holdh[10], d2samp; DWORD ovtk[8]; long ovtn[8], ovtfull; } KLBR_MBC;      /* s83: other, cover0, store720, create, retarget, unknown; d*: DATA-side samples every 250 ms per marked bot (dsamp samples, datk = [S+0x74] == [S+0x658], ahist = state [g+8] of the ZAttackTarget goal 0..4, aother = other value, anull = no goal, dnocl = byte [S+0x4fc] set, dtrans = state transitions seen, dlog = lines logged) */
static KLBR_MBC klbr_mb_c;
typedef struct { int g, gst, iscur, curnz, st654, nocl, st56c, st5ac, st638, st634, st648, st65c, st63c, hold; DWORD pri, tgt, last, curvt, mode, fa8, fb0; int have; } KLBR_MBSIG;
static KLBR_MBSIG klbr_mb_sig[KLBR_MAX]; static DWORD klbr_mb_dnext[KLBR_MAX];
#define KLBR_MB_DSTEP 250
#define KLBR_MB_DLOGMAX 120
#define KLBR_MB_DLOGGAP 500
static DWORD klbr_mb_t0[KLBR_MAX], klbr_mb_next[KLBR_MAX]; static float klbr_mb_pt[KLBR_MAX][3], klbr_mb_d0[KLBR_MAX], klbr_mb_dmin[KLBR_MAX];
static int klbr_mb_arc; static DWORD klbr_mb_arules, klbr_mb_asold[KLBR_MAX], klbr_mb_ascan; static int klbr_mb_akind[KLBR_MAX];      /* Arcade source (offline): the sampled bots' soldiers, kind 1 = Traitor-marked, 0 = control */
static DWORD klbr_mb_src(int i) { return klbr_mb_arc ? klbr_mb_asold[i] : klbr_f6_sold[i]; }
static int klbr_mb_ix(DWORD S) { int i; if (S <= 0xffff) return -1; for (i = 0; i < KLBR_MAX; i++) if (klbr_mb_src(i) == S) return i; return -1; }
static int klbr_mb_state_of(DWORD S, DWORD off)      /* [[S+off]+8], -1 when the pointer is not readable */
{
    DWORD p = klh_rd32(S + off);
    return p > 0xffff ? (int)klh_rd32(p + 8) : -1;
}
static void klbr_mb_body_fn(int id, KLBR_F3REGS *r)
{
    KLBR_MBC *c = &klbr_mb_c; DWORD now = GetTickCount(); int ix;
    static const char *const bn[6] = { "other (handle 0, +0x5ac busy: the 0x8318c2 path)", "CoverFire (handle 0)", "store720 only (+0x5ac busy, handle != 0)", "CREATE (AddGoal ZAttackTarget)", "RETARGET (+0x658 already running, no re-add)", "unknown (state unreadable)" };
    if (id == 21) {
        DWORD S = r->ecx, h = klh_rd32(r->esp + 4); int s5, s6, br;
        if ((ix = klbr_mb_ix(S)) < 0) return;
        s5 = klbr_mb_state_of(S, 0x5ac); s6 = klbr_mb_state_of(S, 0x658); br = kbr_mb_branch(s5, s6, h);
        c->s83[br]++;
        if (c->nl[0] < KLBR_MB_LOGMAX) { c->nl[0]++; klog("brain: modeb s83: bot %d soldier %08lx handle %08lx [[S+0x5ac]+8]=%d [[S+0x658]+8]=%d -> %s; return %08lx", ix, (unsigned long)S, (unsigned long)h, s5, s6, bn[br], (unsigned long)klh_rd32(r->esp)); }
        return;
    }
    if (id == 22) {
        DWORD g = r->ecx, S = klh_rd32(g + 4);
        if ((ix = klbr_mb_ix(S)) < 0) return;
        c->ticks++;
        if (c->nl[1] < KLBR_MB_LOGMAX) { c->nl[1]++; klog("brain: modeb tick: bot %d goal %08lx (owner [g+4] = the marked soldier %08lx) state [g+8]=%ld target handle [g+0x14]=%08lx", ix, (unsigned long)g, (unsigned long)S, (long)klh_rd32(g + 8), (unsigned long)klh_rd32(g + 0x14)); }
        return;
    }
    if (id >= 23 && id <= 26) {
        DWORD g = r->esi, S = klh_rd32(g + 4); long cnt, idx;
        if ((ix = klbr_mb_ix(S)) < 0) return;
        cnt = (long)klh_rd32(r->ebp - 8); idx = (long)klh_rd32(r->ebp - 0x14);
        if (id == 23) { c->cand++; c->candsum += cnt; if (c->nl[2] < KLBR_MB_LOGMAX) { c->nl[2]++; klog("brain: modeb cand: bot %d candidate count [ebp-8]=%ld (point 0 is the bot's own position)", ix, cnt); } }
        else if (id == 24) { c->notclear++; if (c->nl[3] < KLBR_MB_LOGMAX) { c->nl[3]++; klog("brain: modeb notclear: bot %d candidate %ld of %ld: stockclear=0 (0x4e1750 al==0)", ix, idx, cnt); } }
        else if (id == 25) {
            if (idx == 0) c->clear0++; else c->clearN++;
            if (c->nl[4] < KLBR_MB_LOGMAX) { c->nl[4]++; klog("brain: modeb clear: bot %d candidate %ld of %ld: stockclear=1 (0x4e1750 al!=0; opposite polarity to klbr_los_clear) -> %s", ix, idx, cnt, idx == 0 ? "index 0, the bot stays and shoots" : "first clear index, RunChild follows"); }
        } else {
            c->none++; if (cnt <= 0) c->none0++;
            if (c->nl[5] < KLBR_MB_LOGMAX) { c->nl[5]++; klog("brain: modeb none: bot %d no clear candidate (count %ld%s): the tick sets [body+0x4fc]=1 and calls vt+0x13c", ix, cnt, cnt <= 0 ? ", no candidates at all" : ""); }
        }
        return;
    }
    if (id == 27) {
        /* NOTE: at this site the game's x87 stack holds the fldz value (a later fstp [esp] pops it); this handler uses float math and %f logging, which is balanced by the compiler (push/pop pairs), so the stack depth is unchanged on return. */
        DWORD S = r->ecx; long idx = (long)r->ebx; DWORD a = kbr_mb_cand_addr(r->ebp, idx); float pt[3], bp[3]; int havebp;
        if ((ix = klbr_mb_ix(S)) < 0 || !a || !klh_rd(a, pt, 12)) return;
        c->runchild++;
        havebp = klbr_f6_body[ix] > 0xffff && klh_rd(klbr_f6_body[ix] + 0x460, bp, 12) && kle_ok3(bp);
        memcpy(klbr_mb_pt[ix], pt, 12); klbr_mb_t0[ix] = now ? now : 1; klbr_mb_next[ix] = now + KLBR_MB_STEPMS;
        klbr_mb_d0[ix] = klbr_mb_dmin[ix] = havebp ? kbr_f6_dist(bp, pt) : -1.0f;
        if (c->nl[6] < KLBR_MB_LOGMAX) { c->nl[6]++; klog("brain: modeb runchild: bot %d candidate index %ld point %.1f %.1f %.1f; bot now %.1f %.1f %.1f, distance %.1f", ix, idx, (double)pt[0], (double)pt[1], (double)pt[2], havebp ? (double)bp[0] : 0.0, havebp ? (double)bp[1] : 0.0, havebp ? (double)bp[2] : 0.0, (double)klbr_mb_d0[ix]); }
        return;
    }
    if (id == 28) {
        DWORD S = r->esi; int win;
        if ((ix = klbr_mb_ix(S)) < 0) return;
        win = kbr_mb_inwin(now, klbr_mb_t0[ix], KLBR_MB_WINMS);
        c->rearm++; if (win) c->rearm_win++;
        if (c->nl[7] < KLBR_MB_LOGMAX) { c->nl[7]++; klog("brain: modeb rearm: bot %d run-task re-arm 0x800650; %s (last RunChild %lu ms ago)", ix, win ? "WITHIN 10 s of a stock RunChild" : "no stock RunChild in the last 10 s", klbr_mb_t0[ix] ? (unsigned long)(now - klbr_mb_t0[ix]) : 0UL); }
        return;
    }
}
static void __cdecl klbr_mb_hit(int id, KLBR_F3REGS *r)      /* called by the stubs on the game thread */
{
    if (!klbr_mbon || !r || klbr_f6_flt >= 3 || !klbr_f6_tid || GetCurrentThreadId() != klbr_f6_tid) return;
    __try { klbr_mb_body_fn(id, r); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_mb_flt++; if (klbr_mb_flt <= 3) klog("brain: modeb: fault in the handler (site id %d): %d of 3 allowed", id, klbr_f6_flt); }
}
static void klbr_mb_install(void)      /* once (game thread); a refusal is final for the run */
{
    int s, ok = 0, nlist = 0; BYTE cur[16], jmp[16]; DWORD stub; char list[96];
    list[0] = 0;
    if (klbr_mb_state) return;
    klbr_mb_state = -1;
    /* 11-04: no blanket SessionSafe gate. Per klranges.h 0x831850 (slot 83) and 0x800650 (re-arm) are UNHASHED, the six 0x4f4xxx sites are inside the hashed range [0x4f0000,0x4f6000): every site goes through klh_poke, so under SessionSafe=1
       the two unhashed sites install and the guard refuses the hashed ones ("patch REFUSED"); under SessionSafe=0 all install. */
    if (!klbr_mb_stub && !(klbr_mb_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: modeb: no memory for the stubs: off"); return; }
    for (s = 0; s < KLBR_MB_NSITE; s++) {
        const KLBR_MBSITE *k = &klbr_mb_sites[s]; BYTE *at = KLH_VA(k->site); int n;
        memset(cur, 0, sizeof cur);
        if (!klh_rd((DWORD_PTR)at, cur, k->len) || memcmp(cur, k->b, k->len)) { klog("brain: modeb: site %d 0x%x bytes differ from the expected %d (got %02x %02x %02x %02x %02x %02x %02x %02x): NOT installed", k->id, (unsigned)k->site, k->len, cur[0], cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7]); continue; }
        stub = (DWORD)(DWORD_PTR)(klbr_mb_stub + s * 0x40);
        n = kbr_f3_emit(klbr_mb_stub + s * 0x40, stub, k->id, (DWORD)(DWORD_PTR)klbr_mb_hit, k->b, k->len, (DWORD)(DWORD_PTR)(at + k->len));
        if (!n) { klog("brain: modeb: site %d: stub not built", k->id); continue; }
        kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, k->len);
        if (klh_poke(at, k->b, k->len, jmp, k->len, "brain: ModeBProbe counting detour")) { ok++; if (nlist < (int)sizeof list - 8) nlist += _snprintf(list + nlist, sizeof list - nlist, " %d", k->id); klog("brain: modeb: site %d 0x%x (%d bytes stolen) installed, stub %d bytes", k->id, (unsigned)k->site, k->len, n); }
        else klog("brain: modeb: site %d 0x%x NOT installed (refused by the patch guard or the bytes differ)", k->id, (unsigned)k->site);
    }
    klbr_mb_nok = ok; klbr_mb_state = ok == KLBR_MB_NSITE ? 1 : ok ? 2 : -1;
    list[sizeof list - 1] = 0;
    klog("brain: modeb: %d of %d sites installed (state %d; policy %s); installed site ids:%s%s", ok, KLBR_MB_NSITE, klbr_mb_state, klh_policy == KLH_DIRECT ? "direct" : "session/ship", nlist ? list : " none", ok < KLBR_MB_NSITE ? " (the others refused by the patch guard or differ: counts from those sites stay 0, the DATA-side samples still run)" : "");
}
/* OnlineBrainTraitorCloseInProbe (11-04; TEST build only, UNTESTED, recommended off; READ ONLY toward the game: the only game bytes touched are the counting detours at install; game thread only; every read under __try; shares the fault counter klbr_f6_flt, limit 3).
   Question (re/approach_lever_1104.md Verifier): is the ZCloseIn tactic [S+0x590] ever evaluated for a sampled bot, what does its eval answer, which tactic list does the Defend tick walk, and which gate fails.
   Sampled bots = the ModeBProbe sources (online marked bots of the slot-113 wrapper, offline Arcade role 0/1 mode 4); the sampling loop runs when either key is set.
   Sites (all UNHASHED per klranges.h, so all five install under SessionSafe=1; whole instructions, no relative operand, no jump into the stolen ranges: checked on 0x6724e0..0x672779):
     c1 id 31 0x6724e0 (8) 55 8b ec 83 ec 7c 53 56   ZCloseIn eval entry (thiscall, ecx = tactic, plain ret, float result in st0): bot found by [S+0x590] == ecx. Count only.
     c2 id 32 0x672722 (7) d9 ee 5f 5e 5b 8b e5       the 'return 0.0' tail (fldz; esi = tactic): counted BEFORE the fldz runs.
     c3 id 33 0x672770 (7) d9 e8 5f 5e 5b 8b e5       the 'return 1.0' tail (fld1).
     c4 id 34 0x4a7e60 (8) 55 8b ec 83 ec 38 53 56   run-task tick (ecx = task): bot found by [S+0x56c] == ecx, else by the owner [task+4] (GUESS: [task+4] is the soldier).
     c5 id 35 0x800630 (6) 55 8b ec 8b 45 10          soldier vt+0x74 'arm' (thiscall ecx = S, pos*, float, byte, ret 0xc): args stored RAW (no float math in the handler), logged by the tick.
   DEVIATION from a naked eval wrapper: the eval is counted at entry (c1) and its result at the two return tails (c2 = 0.0, c3 = 1.0) before fldz / fld1, so st0 is never touched and no naked code is needed. calls - ones - zeros = other (a fault or a call not yet returned).
   The handlers use integer code only (the caller's x87 stack is live at c1 / c4). Lines: 'brain: closein data:' (on change, <= 500 ms apart per bot), 'brain: closein lists:' (once per bot per round and on change), 'brain: closein arm:' (<= 8 per bot per round), 'brain: closein round (<online|arcade>) <why>:'; 120 data / list / arm lines per round shared. */
#define KLBR_CI_NSITE 5
#define KLBR_CI_LOGMAX 120
#define KLBR_CI_GAP 500
#define KLBR_CI_ARMMAX 8
static int klbr_dpon, klbr_cion, klbr_rpon, klbr_ci_state, klbr_ci_flt, klbr_ci_nok, klbr_ci_okmask;
static void klbr_rp_win(int ix);      /* OnlineBrainTraitorRunProbe: a ZCloseIn 1.0 return (integer code only) */
static BYTE *klbr_ci_stub;
static const KLBR_MBSITE klbr_ci_sites[KLBR_CI_NSITE] = {
    { 0x6724e0, 8, { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x7c, 0x53, 0x56 }, 31 },
    { 0x672722, 7, { 0xd9, 0xee, 0x5f, 0x5e, 0x5b, 0x8b, 0xe5 }, 32 },
    { 0x672770, 7, { 0xd9, 0xe8, 0x5f, 0x5e, 0x5b, 0x8b, 0xe5 }, 33 },
    { 0x4a7e60, 8, { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x38, 0x53, 0x56 }, 34 },
    { 0x800630, 6, { 0x55, 0x8b, 0xec, 0x8b, 0x45, 0x10 }, 35 } };
typedef struct {
    long ev, ev1, ev0, rt, arm, armlog, armdrop, samp, s4, s6;
    DWORD armat, armv[5]; int armpend;      /* armv: pos x y z (raw float bits), float arg (raw), byte arg */
    int have, c4, c6, b0nz, acnz, destnz, wait; DWORD curvt, d6a8, last; char cur[32];      /* the on-change signature */
    int lhave, ln[3]; DWORD lvt[3][8]; long lnlog;      /* tactic lists A / B / C: counts and the first 8 tactic vtables */
} KLBR_CIB;
static KLBR_CIB klbr_ci_b[KLBR_MAX];
static long klbr_ci_nlog, klbr_ci_unm, klbr_ci_nogoal, klbr_ci_gc[8]; static char klbr_ci_gn[8][32]; static char klbr_ci_la[220];      /* round: lines logged, hits on a soldier we do not sample, none-goal samples, goal-name histogram, list A order of the first bot */
static void klbr_ci_reset(void) { memset(klbr_ci_b, 0, sizeof klbr_ci_b); klbr_ci_nlog = klbr_ci_unm = klbr_ci_nogoal = 0; memset(klbr_ci_gn, 0, sizeof klbr_ci_gn); memset(klbr_ci_gc, 0, sizeof klbr_ci_gc); klbr_ci_la[0] = 0; }
static int klbr_ci_by(DWORD t, DWORD off)      /* the sampled bot whose [S+off] is t, -1 */
{
    int i;
    if (t <= 0xffff) return -1;
    for (i = 0; i < KLBR_MAX; i++) { DWORD S = klbr_mb_src(i); if (S > 0xffff && klh_rd32(S + off) == t) return i; }
    return -1;
}
static void klbr_ci_body(int id, KLBR_F3REGS *r)      /* integer code only (see the block comment) */
{
    int ix; KLBR_CIB *b; DWORD now;
    if (id >= 31 && id <= 33) {
        DWORD t = id == 31 ? r->ecx : r->esi;
        if ((ix = klbr_ci_by(t, 0x590)) < 0) { klbr_ci_unm++; return; }
        b = &klbr_ci_b[ix]; if (id == 31) b->ev++; else if (id == 32) b->ev0++; else { b->ev1++; if (klbr_rpon) klbr_rp_win(ix); }
        return;
    }
    if (id == 34) {
        if ((ix = klbr_ci_by(r->ecx, 0x56c)) < 0) ix = klbr_mb_ix(klh_rd32(r->ecx + 4));
        if (ix < 0) { klbr_ci_unm++; return; }
        klbr_ci_b[ix].rt++;
        return;
    }
    if (id == 35) {
        DWORD S = r->ecx, pp = klh_rd32(r->esp + 4);
        if ((ix = klbr_mb_ix(S)) < 0) return;
        b = &klbr_ci_b[ix]; b->arm++; now = GetTickCount();
        if (b->armlog >= KLBR_CI_ARMMAX || b->armpend || (b->armat && !kbr_mb_due(now, b->armat + KLBR_CI_GAP))) { b->armdrop++; return; }
        if (!klh_rd(pp, b->armv, 12)) memset(b->armv, 0, 12);
        b->armv[3] = klh_rd32(r->esp + 8); b->armv[4] = klh_rd32(r->esp + 12) & 0xffu;
        b->armat = now ? now : 1; b->armpend = 1;
        return;
    }
}
static void __cdecl klbr_ci_hit(int id, KLBR_F3REGS *r)      /* called by the stubs on the game thread */
{
    if (!klbr_cion || !r || klbr_f6_flt >= 3 || !klbr_f6_tid || GetCurrentThreadId() != klbr_f6_tid) return;
    __try { klbr_ci_body(id, r); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_ci_flt++; if (klbr_ci_flt <= 3) klog("brain: closein: fault in the handler (site id %d): %d of 3 allowed", id, klbr_f6_flt); }
}
static void klbr_ci_install(void)      /* once (game thread); a refusal is final for the run */
{
    int s, ok = 0, nlist = 0; BYTE cur[16], jmp[16]; DWORD stub; char list[96];
    list[0] = 0;
    if (klbr_ci_state) return;
    klbr_ci_state = -1;
    if (!klbr_ci_stub && !(klbr_ci_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: closein: no memory for the stubs: off"); return; }
    for (s = 0; s < KLBR_CI_NSITE; s++) {
        const KLBR_MBSITE *k = &klbr_ci_sites[s]; BYTE *at = KLH_VA(k->site); int n;
        memset(cur, 0, sizeof cur);
        if (!klh_rd((DWORD_PTR)at, cur, k->len) || memcmp(cur, k->b, k->len)) { klog("brain: closein: site %d 0x%x bytes differ from the expected %d (got %02x %02x %02x %02x %02x %02x %02x %02x): NOT installed", k->id, (unsigned)k->site, k->len, cur[0], cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7]); continue; }
        stub = (DWORD)(DWORD_PTR)(klbr_ci_stub + s * 0x40);
        n = kbr_f3_emit(klbr_ci_stub + s * 0x40, stub, k->id, (DWORD)(DWORD_PTR)klbr_ci_hit, k->b, k->len, (DWORD)(DWORD_PTR)(at + k->len));
        if (!n) { klog("brain: closein: site %d: stub not built", k->id); continue; }
        kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, k->len);
        if (klh_poke(at, k->b, k->len, jmp, k->len, "brain: CloseInProbe counting detour")) { ok++; klbr_ci_okmask |= 1 << s; if (nlist < (int)sizeof list - 8) nlist += _snprintf(list + nlist, sizeof list - nlist, " %d", k->id); klog("brain: closein: site %d 0x%x (%d bytes stolen) installed, stub %d bytes", k->id, (unsigned)k->site, k->len, n); }
        else klog("brain: closein: site %d 0x%x NOT installed (refused by the patch guard or the bytes differ)", k->id, (unsigned)k->site);
    }
    klbr_ci_nok = ok; klbr_ci_state = ok == KLBR_CI_NSITE ? 1 : ok ? 2 : -1;
    list[sizeof list - 1] = 0;
    klog("brain: closein: %d of %d sites installed (state %d; policy %s); installed site ids:%s%s", ok, KLBR_CI_NSITE, klbr_ci_state, klh_policy == KLH_DIRECT ? "direct" : "session/ship", nlist ? list : " none", ok < KLBR_CI_NSITE ? " (the others refused or differ: those counts stay 0, the DATA-side samples still run)" : "");
}
/* nearest live human ZFFPlayer from the rules' record list (the Sense enumeration: record = client struct at recs + 0x74 * k, player = [client + 0x378]); 1 = found. Offline Arcade has no such list (the rules vtable test fails): the caller then falls back to the holder [S+0xac] when that is a ZFFPlayer (GUESS that offline Arcade's human is the holder). */
/* Offline fallback (11-04, DriftProbe baseline on Arcade; used ONLY when kl_online() == 0 and the record walk is unavailable, so online behaviour is unchanged). Source: klh_slot_player_mine() = the game's own local player
   [[0xdd265c]+0x828+4*(sel<28)], sel = byte [gd+0x898] (klbot.c / klchar.c / klauto.c kla_local_player; offline it returns the slot as is). Offline Arcade has exactly one human, the local player, so he is THE human.
   Tests as in the record walk: ZFFPlayer vtable 0xbb45f4 (klh_pvt), not a tagged bot (klbr_hl_find), health not <= 0, feet [+0x460] sane. GUESS: nothing else is a human offline (no split screen; the other 27 slots are not read). Returns 0 when no such body exists. */
static int klbr_hn_local(const float *bp, double *dist, DWORD *who)
{
    DWORD p = klh_slot_player_mine(); float hp = 1.0f, tp[3];
    if (p < 0x10000 || klh_pvt(p) != 0x00bb45f4u || klbr_hl_find(p) || (klbr_hp_read(p, &hp) && hp <= 0.0f) || !klh_rd(p + 0x460, tp, 12) || !kle_ok3(tp)) return 0;
    *dist = kle_dist(bp, tp); if (who) *who = p;
    return 1;
}
static int klbr_human_near(const float *bp, double *dist, DWORD *who)      /* nearest live human ZFFPlayer body (entity pointer into *who when given); same walk as before, shared with HolderSet */
{
    DWORD G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)), rules = G > 0xffff ? klh_rd32(G + 0x54) : 0, vt, recs, freeb, cnt = 0; int k, found = 0;
    if (rules && rules == klbr_shadow) rules = klbr_rr_sw ? klbr_rr_rules : 0;
    if (rules < 0x10000) return kl_online() ? 0 : klbr_hn_local(bp, dist, who);
    vt = klh_rd32(rules);
    if ((!KLH_RULES_SV_OK(vt) && !KLH_RULES_CL_OK(vt)) || !klh_rd(rules + 0x14, &cnt, 4) || cnt > 16) return kl_online() ? 0 : klbr_hn_local(bp, dist, who);
    recs = klh_rd32(rules + 8); freeb = klh_rd32(rules + 0xc);
    if (!recs || !freeb) return kl_online() ? 0 : klbr_hn_local(bp, dist, who);
    for (k = 0; k < (int)cnt; k++) {
        BYTE used = 1; DWORD cl, p; float hp = 1.0f, tp[3]; double d;
        if (!klh_rd(freeb + k, &used, 1) || used) continue;
        cl = klh_rd32(recs + 0x74 * (DWORD)k); p = cl > 0xffff ? klh_rd32(cl + 0x378) : 0;
        if (p < 0x10000 || klh_pvt(p) != 0x00bb45f4u || klbr_hl_find(p) || (klbr_hp_read(p, &hp) && hp <= 0.0f) || !klh_rd(p + 0x460, tp, 12) || !kle_ok3(tp)) continue;
        d = kle_dist(bp, tp);
        if (!found || d < *dist) { *dist = d; found = 1; if (who) *who = p; }
    }
    return found;
}
/* 11-05 (klbotfill OnlineEscort, ES4): is body P the player of a used rules record (a session seat = a human)? 1 yes, 0 no, -1 walk unavailable; *nused = used records.
   Same walk and shadow handling as klbr_human_near (SB74C DD05: 12 slots, 10 free = the 2 human seats; AI heisters have no record). GUESS: [cl+0x378] is the same pointer as the session player-table entry on the host for remote seats too (the caller falls back when no entry matches). */
static int klbr_rec_member(DWORD P, int *nused)
{
    DWORD G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)), rules = G > 0xffff ? klh_rd32(G + 0x54) : 0, vt, recs, freeb, cnt = 0; int k, found = 0, nu = 0;
    if (nused) *nused = 0;
    if (rules && rules == klbr_shadow) rules = klbr_rr_sw ? klbr_rr_rules : 0;
    if (rules < 0x10000) return -1;
    vt = klh_rd32(rules);
    if ((!KLH_RULES_SV_OK(vt) && !KLH_RULES_CL_OK(vt)) || !klh_rd(rules + 0x14, &cnt, 4) || cnt > 16) return -1;
    recs = klh_rd32(rules + 8); freeb = klh_rd32(rules + 0xc);
    if (!recs || !freeb) return -1;
    for (k = 0; k < (int)cnt; k++) {
        BYTE used = 1; DWORD cl;
        if (!klh_rd(freeb + k, &used, 1) || used) continue;
        nu++; cl = klh_rd32(recs + 0x74 * (DWORD)k);
        if (cl > 0xffff && klh_rd32(cl + 0x378) == P) found = 1;
    }
    if (nused) *nused = nu;
    return found;
}
static int klbr_ci_human(const float *bp, double *dist) { return klbr_human_near(bp, dist, 0); }
static void klbr_ci_lists(int i, DWORD S, const char *kind, KLBR_CIB *b)      /* tactic lists A / B / C: logged once per bot per round and when they change */
{
    static const DWORD loff[3] = { 0x604, 0x610, 0x61c }; static const char lname[3] = { 'A', 'B', 'C' };
    DWORD vts[3][8]; int ln[3], k, e, chg = 0;
    memset(vts, 0, sizeof vts);
    for (k = 0; k < 3; k++) {
        DWORD bg = klh_rd32(S + loff[k]), en = klh_rd32(S + loff[k] + 4); ln[k] = kbr_ci_list_n(bg, en);
        for (e = 0; e < ln[k] && e < 8; e++) { DWORD t = klh_rd32(bg + 4 * (DWORD)e); vts[k][e] = t > 0xffff ? klh_rd32(t) : 0; }
        if (!b->lhave || ln[k] != b->ln[k] || memcmp(vts[k], b->lvt[k], sizeof vts[k])) chg = 1;
    }
    if (!chg) return;
    if (klbr_ci_nlog < KLBR_CI_LOGMAX && b->lnlog < 6) {
        char line[420]; int n = 0, na = 0;
        line[0] = 0;
        for (k = 0; k < 3; k++) {
            DWORD bg = klh_rd32(S + loff[k]);
            n += _snprintf(line + n, sizeof line - n, "%s%c[%d]:", k ? "; " : "", lname[k], ln[k]);
            for (e = 0; e < ln[k] && e < 8 && n < (int)sizeof line - 40; e++) { char nm[32]; DWORD t = klh_rd32(bg + 4 * (DWORD)e); klbr_f8_rtti(t, nm, sizeof nm); n += _snprintf(line + n, sizeof line - n, " %s", nm[0] ? nm : "?"); }
            if (k == 0) na = n;
        }
        line[sizeof line - 1] = 0;
        if (!klbr_ci_la[0] && na > 0) { _snprintf(klbr_ci_la, sizeof klbr_ci_la, "%.*s", na < (int)sizeof klbr_ci_la - 1 ? na : (int)sizeof klbr_ci_la - 1, line); klbr_ci_la[sizeof klbr_ci_la - 1] = 0; }
        klbr_ci_nlog++; b->lnlog++;
        klog("brain: closein lists: %s bot %d S %08lx: %s (tactic pointers, 4 bytes each, first 8 per list shown; layout GUESS: vector begin / end pairs at S+0x604 / 0x610 / 0x61c)%s", kind, i, (unsigned long)S, line, b->lhave ? "; CHANGED" : "");
    }
    for (k = 0; k < 3; k++) { b->ln[k] = ln[k]; memcpy(b->lvt[k], vts[k], sizeof vts[k]); }
    b->lhave = 1;
}
static void klbr_ci_sample(int i, DWORD S, DWORD now)      /* every 250 ms per sampled bot (called by klbr_mb_sample after its own due test) */
{
    KLBR_CIB *b = &klbr_ci_b[i]; DWORD cur, ci, g, clk = 0, tim = 0, dst[3], fa8, fb0, fac, d6, d6a8, body; BYTE b4 = 0, b6 = 0; char nm[32]; int c4, c6, haveb = 0, hum = 0, rev = -1; long left;
    float bp[3], f6a8, dx[3]; double dh = -1.0; const char *kind = klbr_mb_arc ? (klbr_mb_akind[i] ? "arcade traitor" : "arcade control") : "online marked";
    nm[0] = 0;
    __try {
        cur = klh_rd32(S + 0x74); if (cur > 0xffff) klbr_f8_rtti(cur, nm, sizeof nm);
        klh_rd(S + 0x4fc, &b4, 1); d6 = klh_rd32(S + 0x6fc); b6 = (BYTE)d6; ci = klh_rd32(S + 0x590);
        g = klh_rd32((DWORD_PTR)KLH_VA(0xdd2640)); if (g > 0xffff) clk = klh_rd32(g + 0x48);
        memset(dst, 0, sizeof dst);
        if (ci > 0xffff) { tim = klh_rd32(ci + 0x14); dst[0] = klh_rd32(ci + 0x18); dst[1] = klh_rd32(ci + 0x1c); dst[2] = klh_rd32(ci + 0x20); }
        d6a8 = klh_rd32(S + 0x6a8); fa8 = klh_rd32(S + 0xa8); fb0 = klh_rd32(S + 0xb0); fac = klh_rd32(S + 0xac);
        rev = fb0 ? (int)(((DWORD (__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(0x8ccde0))(fb0) == fac) : -1;      /* read only: the game's own reverse lookup (cdecl, unhashed) of the handle; -1 = no handle */
        body = klh_rd32(S + 0x40);
        haveb = body > 0xffff && klh_rd(body + 0x460, bp, 12) && kle_ok3(bp);
        if (haveb) { hum = klbr_ci_human(bp, &dh); if (!hum && fac > 0xffff && klh_pvt(fac) == 0x00bb45f4u && klh_rd(fac + 0x460, dx, 12) && kle_ok3(dx)) { dh = kle_dist(bp, dx); hum = 2; } }
        klbr_ci_lists(i, S, kind, b);
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_ci_flt++; return; }
    c4 = b4 != 0; c6 = b6 != 0; left = kbr_ci_timer_left((long)tim, (long)clk);
    b->samp++; if (c4) b->s4++; if (c6) b->s6++;
    if (cur > 0xffff && nm[0]) kbr_ci_name_tally(klbr_ci_gn, klbr_ci_gc, 8, nm); else klbr_ci_nogoal++;
    {
        int dnz = dst[0] || dst[1] || dst[2], wait = left > 0, b0nz = fb0 != 0, acnz = fac != 0;
        if (!b->have || b->c4 != c4 || b->c6 != c6 || b->b0nz != b0nz || b->acnz != acnz || b->destnz != dnz || b->wait != wait || b->curvt != cur || strcmp(b->cur, nm) || b->d6a8 != d6a8) {
            if (klbr_ci_nlog < KLBR_CI_LOGMAX && (!b->last || kbr_mb_due(now, b->last + KLBR_CI_GAP))) {
                memcpy(&f6a8, &d6a8, 4); memcpy(dx, dst, 12);
                klbr_ci_nlog++; b->last = now ? now : 1;
                klog("brain: closein data: %s bot %d S %08lx: current goal %s (obj %08lx); [S+0x4fc] %d [S+0x6fc] %08lx; Defend would walk list %c (C condition not evaluated); ZCloseIn %08lx timer %ld clock %ld (%ld ms to wait), dest %.1f %.1f %.1f; preferred distance [S+0x6a8] %.1f; [S+0xac] %08lx [S+0xb0] %08lx [S+0xa8] %08lx (0x8ccde0([S+0xb0]) == [S+0xac]: %s); "
                     "distance to the %s %.1f; so far eval %ld (1.0 x%ld, 0.0 x%ld), run-task ticks %ld, arm %ld%s",
                     kind, i, (unsigned long)S, nm[0] ? nm : cur > 0xffff ? "?" : "none", (unsigned long)cur, c4, (unsigned long)d6, "ABC"[kbr_ci_list_pick(c4, c6, 0)], (unsigned long)ci, (long)tim, (long)clk, left, (double)dx[0], (double)dx[1], (double)dx[2], (double)f6a8,
                     (unsigned long)fac, (unsigned long)fb0, (unsigned long)fa8, rev < 0 ? "no handle" : rev ? "yes" : "NO", hum == 1 ? "nearest human" : hum == 2 ? "holder (a ZFFPlayer)" : "human (none found)", dh, b->ev, b->ev1, b->ev0, b->rt, b->arm, b->have ? "" : " (first sample)");
            }
            b->c4 = c4; b->c6 = c6; b->b0nz = b0nz; b->acnz = acnz; b->destnz = dnz; b->wait = wait; b->curvt = cur; b->d6a8 = d6a8; _snprintf(b->cur, sizeof b->cur, "%s", nm); b->cur[sizeof b->cur - 1] = 0; b->have = 1;
        }
    }
    if (b->armpend) {      /* the 0x800630 args stored by the handler: distances to the bot and to the nearest human (float math here, not in the stub) */
        float pos[3], fa; double db = -1.0, dhu = -1.0, dh2 = 0.0;
        memcpy(pos, b->armv, 12); memcpy(&fa, &b->armv[3], 4);
        if (haveb && kle_ok3(pos)) { db = kle_dist(bp, pos); __try { if (klbr_ci_human(pos, &dh2)) dhu = dh2; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_ci_flt++; } }
        if (klbr_ci_nlog < KLBR_CI_LOGMAX) {
            klbr_ci_nlog++;
            klog("brain: closein arm: %s bot %d S %08lx: 0x800630 args pos %.1f %.1f %.1f, float %.2f, byte %lu; distance pos->bot %.1f, pos->nearest human %.1f; arm calls so far %ld (args logged %ld, dropped by the rate cap %ld)", kind, i, (unsigned long)S, (double)pos[0], (double)pos[1], (double)pos[2], (double)fa, (unsigned long)b->armv[4], db, dhu, b->arm, b->armlog + 1, b->armdrop);
        }
        b->armlog++; b->armpend = 0;
    }
}
static void klbr_ci_summary(const char *why)      /* the round line; printed when anything was sampled or counted */
{
    long ev = 0, e1 = 0, e0 = 0, rt = 0, arm = 0, al = 0, ad = 0, sm = 0, s4 = 0, s6 = 0; int i, n = 0; char gh[300]; gh[0] = 0;
    if (!klbr_cion) return;
    for (i = 0; i < KLBR_MAX; i++) { KLBR_CIB *b = &klbr_ci_b[i]; ev += b->ev; e1 += b->ev1; e0 += b->ev0; rt += b->rt; arm += b->arm; al += b->armlog; ad += b->armdrop; sm += b->samp; s4 += b->s4; s6 += b->s6; }
    if (!sm && !ev && !e1 && !e0 && !rt && !arm) return;
    for (i = 0; i < 8; i++) if (klbr_ci_gc[i] && n < (int)sizeof gh - 48) n += _snprintf(gh + n, sizeof gh - n, " %s x%ld", klbr_ci_gn[i], klbr_ci_gc[i]);
    if (klbr_ci_nogoal && n < (int)sizeof gh - 24) n += _snprintf(gh + n, sizeof gh - n, " none x%ld", klbr_ci_nogoal);
    gh[sizeof gh - 1] = 0;
    klog("brain: closein round (%s) %s: samples %ld, [S+0x4fc] set %d%%, [S+0x6fc] nonzero %d%%; ZCloseIn eval calls %ld, ones %ld, zeros %ld, other %ld (hits on soldiers not sampled %ld); run-task ticks %ld; arm calls %ld (args logged %ld, dropped by the rate cap %ld); current-goal histogram:%s; list A at the first sight: %s; sites installed %d of %d; faults %d, shared %d",
         klbr_mb_arc ? "arcade" : "online", why, sm, kbr_ci_pct(s4, sm), kbr_ci_pct(s6, sm), ev, e1, e0, ev - e1 - e0, klbr_ci_unm, rt, arm, al, ad, n ? gh : " -", klbr_ci_la[0] ? klbr_ci_la : "-", klbr_ci_nok, KLBR_CI_NSITE, klbr_ci_flt, klbr_f6_flt);
}
/* OnlineBrainTraitorDefendProbe (11-04; TEST build only, UNTESTED, recommended off; READ ONLY toward the game: the only game bytes touched are the detours at install; game thread only; every read under __try; shares the fault counter klbr_f6_flt, limit 3).
   Extends the CloseInProbe (re/closein_gates_1104.md Verifier, ENDORSED NEXT LEVER). Works online (marked bots) and in Arcade like the CloseInProbe; implies the CloseInProbe's five counting sites (ZCloseIn eval entry / 0.0 tail / 1.0 tail are the base of the gate trace) but NOT its log lines.
   (a) WHICH LIST-A TACTIC WINS. The Defend tick 0x85f6c0 (loop 0x85f8f0..0x85f924: vcall +0x2c on each tactic of the chosen list, 'fcomp [0xb69b98]; test ah,0x41; je 0x85f910' takes the FIRST tactic whose eval is above the threshold, stores it in [goal+0x14] at 0x85f915, runs it 0x521350) is in a HASHED
       range ({0x85e000,0x862000}), and so are the evals of nearly every list-A tactic (resolved from the vtables 11-04 by the ctor stores of 0x6ab250; vt+0x2c): ZReactToHumanShield 0x8785b0, ZFakeCloseCombat 0x8ab2b0, ZBecomeTraitor 0x79b7c0, ZAttackMountedWeapon 0x68ee30, ZCloseAttack 0x49b070, ZSwatCloseIn 0x7e56d0,
       ZAttackFromCover 0x680b20, ZAttackNoCover 0x85ece0, Loot 0x451920, BoardEscapeVehicle 0x4faf60 (all hashed: NO detour). UNHASHED are ZCloseIn 0x6724e0 (the CloseInProbe c1), ZGraceShot 0x41a5b0 (list A order ... [+0x590] ZCloseIn, [+0x598] SwatCloseIn, [+0x59c] FromCover, [+0x5c0] GraceShot, [+0x5b0] NoCover, [+0x5f0] Loot) and the dog tactics (not used by soldiers).
       So: id 60 = count at the GraceShot eval entry (reached = every earlier list-A tactic, ZCloseIn among them, answered at or below the threshold in that tick; NoCover is next), and the WINNER is DATA: [goal+0x14] of the current Defend goal ([S+0x74] == [S+0x648]) read every 250 ms, its RTTI name tallied and its index in the picked list.
       GUESS: that [Defend goal + 0x14] still holds the winner when sampled (the store at 0x85f915 is cleared at 0x85f92c when the done-check 0x55b9f0 is false), that a Defend tick runs several times per second.
   (b) LIST C. The byte [[S+0x40]+0x5c8] is read as data every sample and the getter 0x575100 is REPLICATED on data, not called (disassembly: eax = [ecx+0x77c]; 0 -> false; else [[eax+0x6d8]] == 6; no call, no write, so replicating it is exact). List C is active when the byte is nonzero AND the getter is false (0x85f8c5..0x85f8e2), kbr_dp_c_active.
   (c) ZCLOSEIN GATE TRACE. Each gate that returns 0.0 branches to the tail 0x672722 with a near jcc (0F 8x rel32, 6 bytes, whole instruction, checked to target 0x672722). Each such jcc is RETARGETED to its own 22-byte stub (kbr_dp_taken_emit: pushad, pushfd, handler(id, regs), popfd, popad, jmp 0x672722): when the branch is not taken nothing runs, the stolen instruction is not
       copied (no relative operand to relocate), the condition code is unchanged, the x87 stack is never touched (integer handler). Sites (gate, id, bytes verified against the exe with debug/dasm.py 11-04):
         P1 timer           id 51 0x672507 0f 8c 15 02 00 00  jl  0x672722   (cmp edx,[edi])
         P2 no holder       id 52 0x6725a1 0f 84 7b 01 00 00  je  0x672722   (cmp [ecx+0xb0],0)
         P3 smoothed value  id 53 0x6725c9 0f 8b 53 01 00 00  jnp 0x672722   (fcompp; test ah,5)
         P4 distance        id 54 0x6725f4 0f 84 28 01 00 00  je  0x672722   (fcompp; test ah,0x41; [S+0x6a8] vs 0x4087f0)
         P5 time since evt  id 55 0x67261e 0f 84 fe 00 00 00  je  0x672722   (0x8a2e50 vs 0.3 / 5.0)
         P6 reachability    id 56 0x67264e 0f 8b ce 00 00 00  jnp 0x672722   (0x651060 false and 0x8a2e50 < 10.0)
         P7 squad count     id 57 0x672678 0f 8f a4 00 00 00  jg  0x672722   (0x76ca60 > 1)
         P4b distance again id 58 0x672691 0f 8a 8b 00 00 00  jp  0x672722   (second [S+0x6a8] compare, 0x67267e)
       P8 (class mask 0x4ea3b0 / 0x7aace0, 0x6726b1 is a SHORT jump 74 6f: not retargetable) and P9 (nav path, falls through 0x672718 'jg 0x67272b' = 7f 11) are DERIVED (kbr_dp_split): id 59 counts 0x6726b3 (8b 0d 40 26 dd 00, mov ecx,[0xdd2640], 6 bytes stolen, absolute operand only; reached = P8 passed):
         P9 = reached(0x6726b3) - ones; P8 = zeros_total - sum(P1..P7, P4b) - P9; the residual (should be 0) is printed.
       id 60 0x41a5b0 (7 stolen) 55 8b ec 51 56 8b f1  ZGraceShot eval entry, ecx = tactic (bot found by [S+0x5c0]); the bytes 8b 4e 04 after it are not stolen. The hit finds the bot by esi (ids 51..59, esi = tactic in the whole eval: set at 0x6724e8, never changed) / ecx (id 60).
   Lines: 'brain: defendprobe data:' (on change of list pick / C inputs / winner, <= 500 ms apart per bot, 80 per round), 'brain: defendprobe round (<online|arcade>) <why>:'. A site whose bytes differ is NOT installed and listed in the round line. */
#define KLBR_DP_NSITE 10
#define KLBR_DP_LOGMAX 80
#define KLBR_DP_GAP 500
#define KLBR_DP_LMAX 24
#define KLBR_DP_TAIL0 0x672722u
typedef struct { DWORD site; int len; BYTE b[10]; int id; int kind; } KLBR_DPSITE;      /* kind 0 = near jcc retargeted to its stub, 1 = stolen bytes + jump */
static const KLBR_DPSITE klbr_dp_sites[KLBR_DP_NSITE] = {
    { 0x672507, 6, { 0x0f, 0x8c, 0x15, 0x02, 0x00, 0x00 }, 51, 0 },
    { 0x6725a1, 6, { 0x0f, 0x84, 0x7b, 0x01, 0x00, 0x00 }, 52, 0 },
    { 0x6725c9, 6, { 0x0f, 0x8b, 0x53, 0x01, 0x00, 0x00 }, 53, 0 },
    { 0x6725f4, 6, { 0x0f, 0x84, 0x28, 0x01, 0x00, 0x00 }, 54, 0 },
    { 0x67261e, 6, { 0x0f, 0x84, 0xfe, 0x00, 0x00, 0x00 }, 55, 0 },
    { 0x67264e, 6, { 0x0f, 0x8b, 0xce, 0x00, 0x00, 0x00 }, 56, 0 },
    { 0x672678, 6, { 0x0f, 0x8f, 0xa4, 0x00, 0x00, 0x00 }, 57, 0 },
    { 0x672691, 6, { 0x0f, 0x8a, 0x8b, 0x00, 0x00, 0x00 }, 58, 0 },
    { 0x6726b3, 6, { 0x8b, 0x0d, 0x40, 0x26, 0xdd, 0x00 }, 59, 1 },
    { 0x41a5b0, 7, { 0x55, 0x8b, 0xec, 0x51, 0x56, 0x8b, 0xf1 }, 60, 1 } };
static int klbr_dp_flt, klbr_dp_nok, klbr_dp_state, klbr_dp_okmask;
static BYTE *klbr_dp_stub;
typedef struct {
    long gz[8], p8pass, gs, samp, defend, pick[3], c5nz, getter, cact, wnone, wout; DWORD last; int have, lpick, lc5, lget; char lwin[32];
} KLBR_DPB;
static KLBR_DPB klbr_dp_b[KLBR_MAX];
static long klbr_dp_nlog, klbr_dp_unm; static char klbr_dp_wn[12][32]; static long klbr_dp_wc[12];
static void klbr_dp_reset(void) { memset(klbr_dp_b, 0, sizeof klbr_dp_b); klbr_dp_nlog = klbr_dp_unm = 0; memset(klbr_dp_wn, 0, sizeof klbr_dp_wn); memset(klbr_dp_wc, 0, sizeof klbr_dp_wc); }
static void klbr_dp_body(int id, KLBR_F3REGS *r)      /* integer code only (the caller's x87 stack is live at the tail sites) */
{
    int ix; KLBR_DPB *b;
    if ((ix = klbr_ci_by(id == 60 ? r->ecx : r->esi, id == 60 ? 0x5c0 : 0x590)) < 0) { klbr_dp_unm++; return; }
    b = &klbr_dp_b[ix];
    if (id >= 51 && id <= 58) b->gz[id - 51]++; else if (id == 59) b->p8pass++; else if (id == 60) b->gs++;
}
static void __cdecl klbr_dp_hit(int id, KLBR_F3REGS *r)      /* called by the stubs on the game thread */
{
    if (!klbr_dpon || !r || klbr_f6_flt >= 3 || !klbr_f6_tid || GetCurrentThreadId() != klbr_f6_tid) return;
    __try { klbr_dp_body(id, r); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_dp_flt++; if (klbr_dp_flt <= 3) klog("brain: defendprobe: fault in the handler (site id %d): %d of 3 allowed", id, klbr_f6_flt); }
}
static void klbr_dp_install(void)      /* once (game thread); a refusal is final for the run */
{
    int s, ok = 0; BYTE cur[16], jmp[16]; DWORD stub;
    if (klbr_dp_state) return;
    klbr_dp_state = -1;
    if (!klbr_dp_stub && !(klbr_dp_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: defendprobe: no memory for the stubs: off"); return; }
    for (s = 0; s < KLBR_DP_NSITE; s++) {
        const KLBR_DPSITE *k = &klbr_dp_sites[s]; BYTE *at = KLH_VA(k->site); int n;
        memset(cur, 0, sizeof cur);
        if (!klh_rd((DWORD_PTR)at, cur, k->len) || memcmp(cur, k->b, k->len)) { klog("brain: defendprobe: site %d 0x%x bytes differ from the expected %d (got %02x %02x %02x %02x %02x %02x %02x %02x): NOT installed", k->id, (unsigned)k->site, k->len, cur[0], cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7]); continue; }
        stub = (DWORD)(DWORD_PTR)(klbr_dp_stub + s * 0x40);
        if (k->kind == 0) {
            if (kbr_dp_jcc_target(cur, k->site) != KLBR_DP_TAIL0) { klog("brain: defendprobe: site %d 0x%x does not branch to 0x%x: NOT installed", k->id, (unsigned)k->site, KLBR_DP_TAIL0); continue; }
            n = kbr_dp_taken_emit(klbr_dp_stub + s * 0x40, stub, k->id, (DWORD)(DWORD_PTR)klbr_dp_hit, KLBR_DP_TAIL0);
            if (!n || !kbr_dp_jcc(jmp, cur, k->site, stub)) { klog("brain: defendprobe: site %d: stub not built", k->id); continue; }
        } else {
            n = kbr_f3_emit(klbr_dp_stub + s * 0x40, stub, k->id, (DWORD)(DWORD_PTR)klbr_dp_hit, k->b, k->len, (DWORD)(DWORD_PTR)(at + k->len));
            if (!n) { klog("brain: defendprobe: site %d: stub not built", k->id); continue; }
            kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, k->len);
        }
        if (klh_poke(at, k->b, k->len, jmp, k->len, "brain: DefendProbe detour")) { ok++; klbr_dp_okmask |= 1 << s; klog("brain: defendprobe: site %d 0x%x (%s, %d bytes) installed, stub %d bytes", k->id, (unsigned)k->site, k->kind ? "stolen bytes" : "jcc retargeted", k->len, n); }
        else klog("brain: defendprobe: site %d 0x%x NOT installed (refused by the patch guard or the bytes differ)", k->id, (unsigned)k->site);
    }
    klbr_dp_nok = ok; klbr_dp_state = ok == KLBR_DP_NSITE ? 1 : ok ? 2 : -1;
    klog("brain: defendprobe: %d of %d sites installed (state %d; policy %s)%s", ok, KLBR_DP_NSITE, klbr_dp_state, klh_policy == KLH_DIRECT ? "direct" : "session/ship", ok < KLBR_DP_NSITE ? " (the others refused or differ: those counts stay 0, the DATA-side samples still run)" : "");
}
static void klbr_dp_sample(int i, DWORD S, DWORD now)      /* every 250 ms per sampled bot (called by klbr_mb_sample after its own due test) */
{
    KLBR_DPB *b = &klbr_dp_b[i]; DWORD cur = 0, dg, body, p = 0, pp, v = 0xffffffffu, win = 0, bg, en, l[KLBR_DP_LMAX]; BYTE b4 = 0, b6 = 0, c5 = 0; char wn[32]; int isdef = 0, getter = 0, cact = 0, pick = 1, n = 0, idx = -1, k, c5nz = 0;
    const char *kind = klbr_mb_arc ? (klbr_mb_akind[i] ? "arcade traitor" : "arcade control") : "online marked"; static const DWORD loff[3] = { 0x604, 0x610, 0x61c };
    char wtxt[32];
    wn[0] = 0;
    __try {
        cur = klh_rd32(S + 0x74); dg = klh_rd32(S + 0x648); isdef = cur > 0xffff && cur == dg;
        klh_rd(S + 0x4fc, &b4, 1); b6 = (BYTE)klh_rd32(S + 0x6fc);
        body = klh_rd32(S + 0x40);
        if (body > 0xffff) { klh_rd(body + 0x5c8, &c5, 1); p = klh_rd32(body + 0x77c); if (p > 0xffff && (pp = klh_rd32(p + 0x6d8)) > 0xffff) v = klh_rd32(pp); }
        getter = kbr_dp_getter(p > 0xffff ? p : 0, v); c5nz = c5 != 0; cact = kbr_dp_c_active(c5nz, getter);
        pick = kbr_ci_list_pick(b4 != 0, b6 != 0, cact);
        bg = klh_rd32(S + loff[pick]); en = klh_rd32(S + loff[pick] + 4); n = kbr_ci_list_n(bg, en);
        if (n > KLBR_DP_LMAX) n = KLBR_DP_LMAX;
        for (k = 0; k < n; k++) l[k] = klh_rd32(bg + 4 * (DWORD)k);
        if (isdef) { win = klh_rd32(cur + 0x14); if (win > 0xffff) { klbr_f8_rtti(win, wn, sizeof wn); idx = kbr_dp_index(l, n < 0 ? 0 : n, win); } }
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_dp_flt++; return; }
    _snprintf(wtxt, sizeof wtxt, "%s", !isdef ? "-" : win <= 0xffff ? "none" : wn[0] ? wn : "?"); wtxt[sizeof wtxt - 1] = 0;
    b->samp++; b->pick[pick]++; if (c5nz) b->c5nz++; if (getter) b->getter++; if (cact) b->cact++;
    if (isdef) {
        b->defend++;
        if (win > 0xffff) { kbr_ci_name_tally(klbr_dp_wn, klbr_dp_wc, 12, wtxt); if (idx < 0) b->wout++; } else b->wnone++;
    }
    if (!b->have || b->lpick != pick || b->lc5 != c5nz || b->lget != getter || strcmp(b->lwin, wtxt)) {
        if (klbr_dp_nlog < KLBR_DP_LOGMAX && (!b->last || kbr_mb_due(now, b->last + KLBR_DP_GAP))) {
            klbr_dp_nlog++; b->last = now ? now : 1;
            klog("brain: defendprobe data: %s bot %d S %08lx: current goal %s; [S+0x4fc] %d [S+0x6fc] %d; [[S+0x40]+0x5c8] %d, getter 0x575100 %d => list C %s; Defend walks list %c (%d tactics); Defend [goal+0x14] %s %08lx, index in that list %d; so far ZCloseIn eval %ld (1.0 x%ld, 0.0 x%ld), gate zeros %ld/%ld/%ld/%ld/%ld/%ld/%ld/%ld (P1..P7,P4b), reached 0x6726b3 %ld, reached GraceShot %ld%s",
                 kind, i, (unsigned long)S, isdef ? "Defend" : cur > 0xffff ? "other" : "none", b4 != 0, b6 != 0, c5nz, getter, cact ? "ACTIVE" : "no", "ABC"[pick], n, wtxt, (unsigned long)win, idx,
                 klbr_ci_b[i].ev, klbr_ci_b[i].ev1, klbr_ci_b[i].ev0, b->gz[0], b->gz[1], b->gz[2], b->gz[3], b->gz[4], b->gz[5], b->gz[6], b->gz[7], b->p8pass, b->gs, b->have ? "" : " (first sample)");
        }
        b->have = 1; b->lpick = pick; b->lc5 = c5nz; b->lget = getter; memcpy(b->lwin, wtxt, sizeof b->lwin);
    }
}
static void klbr_dp_summary(const char *why)      /* the round line; printed when anything was sampled or counted */
{
    long g[8], sm = 0, df = 0, pk[3], c5 = 0, gt = 0, ca = 0, wn = 0, wo = 0, p8pass = 0, gs = 0, ev = 0, e1 = 0, e0 = 0, p8, p9, res; int i, k, n = 0; char wh[400], miss[96];
    if (!klbr_dpon) return;
    memset(g, 0, sizeof g); memset(pk, 0, sizeof pk); wh[0] = 0; miss[0] = 0;
    for (i = 0; i < KLBR_MAX; i++) {
        KLBR_DPB *b = &klbr_dp_b[i]; sm += b->samp; df += b->defend; c5 += b->c5nz; gt += b->getter; ca += b->cact; wn += b->wnone; wo += b->wout; p8pass += b->p8pass; gs += b->gs;
        for (k = 0; k < 8; k++) g[k] += b->gz[k];
        for (k = 0; k < 3; k++) pk[k] += b->pick[k];
        ev += klbr_ci_b[i].ev; e1 += klbr_ci_b[i].ev1; e0 += klbr_ci_b[i].ev0;
    }
    if (!sm && !ev && !gs && !p8pass) return;
    for (i = 0; i < 12; i++) if (klbr_dp_wc[i] && n < (int)sizeof wh - 48) n += _snprintf(wh + n, sizeof wh - n, " %s x%ld", klbr_dp_wn[i], klbr_dp_wc[i]);
    wh[sizeof wh - 1] = 0;
    res = kbr_dp_split(e0, g, 8, p8pass, e1, &p8, &p9);
    for (i = 0, k = 0; i < KLBR_DP_NSITE; i++) if (!(klbr_dp_okmask & (1 << i)) && k < (int)sizeof miss - 12) k += _snprintf(miss + k, sizeof miss - k, " %d", klbr_dp_sites[i].id);
    miss[sizeof miss - 1] = 0;
    klog("brain: defendprobe round (%s) %s: samples %ld, goal is Defend %ld; list picks A %ld B %ld C %ld; Defend current tactic ([goal+0x14] RTTI) histogram:%s (none %ld, not in the picked list %ld); [[S+0x40]+0x5c8] nonzero %ld, getter 0x575100 true %ld, list C active %ld; "
         "ZCloseIn eval calls %ld, ones %ld, zeros %ld; closein gate zeros P1 %ld P2 %ld P3 %ld P4 %ld P5 %ld P6 %ld P7 %ld P8 %ld (derived) P9 %ld (derived) P4b %ld, unattributed %ld; reached GraceShot (all list-A tactics before it answered no, ZCloseIn among them; NoCover is next) %ld; reached 0x6726b3 (P8 passed) %ld; hits on soldiers not sampled %ld; "
         "sites installed %d of %d%s%s; faults %d, shared %d",
         klbr_mb_arc ? "arcade" : "online", why, sm, df, pk[0], pk[1], pk[2], n ? wh : " -", wn, wo, c5, gt, ca, ev, e1, e0, g[0], g[1], g[2], g[3], g[4], g[5], g[6], p8, p9, g[7], res, gs, p8pass, klbr_dp_unm, klbr_dp_nok, KLBR_DP_NSITE,
         miss[0] ? "; NOT hooked (those counts are 0 / skipped), site ids:" : "", miss, klbr_dp_flt, klbr_f6_flt);
}
/* OnlineBrainTraitorRunProbe (11-04; TEST build only, UNTESTED, recommended off; READ ONLY toward the game: the only game bytes touched are the detours at install; game thread only; every read under __try; shares the fault counter klbr_f6_flt, limit 3).
   Question (re/closein_run_1104.md, Verifier 'Endorsed next step'): after ZCloseIn eval 0x6724e0 answers 1.0, does the run body 0x76e8c0 run, which branch, does 0x800630 / the run task 0x4a7e60 follow, and does the bot get closer to the human. Forces the DefendProbe and the CloseInProbe on. Sampled bots = the ones the DefendProbe samples (online marked bots, Arcade traitor-marked / control soldiers).
   (1) RUN BODY 0x76e8c0 (vt+8 of the ZCloseIn tactic, unhashed). The two branches are decided by SHORT jumps (0x76e8d6 'je 0x76e8ed' = 74 15 and 0x76e8eb 'jge 0x76e935' = 7d 48): not retargetable, so the first suitable instructions of the two TARGETS are counted instead (documented deviation):
         id 61 0x76e8c0  (7) 55 8b ec 83 ec 18 56                   run body entry (ecx = tactic)           push ebp / mov ebp,esp / sub esp,0x18 / push esi
         id 62 0x76e8ed  (9) 8b 4e 04 81 c1 e4 00 00 00             DIRECT branch (esi = tactic)            mov ecx,[esi+4] / add ecx,0xe4 (reached from the je AND by falling through the not-taken jge)
         id 63 0x76e935 (10) 8b 4e 04 57 81 c1 e4 00 00 00          COVER branch (esi = tactic, edi = cover index)   mov ecx,[esi+4] / push edi / add ecx,0xe4
       All stolen ranges are whole instructions without a relative operand (python debug/dasm.py 11-04 + a scan of the whole .text: no jump or call from outside lands inside a stolen interior; the only references to 0x76e8ed / 0x76e935 are the two short jumps above). Unhashed per klranges.h (checked with a script, the whole stolen spans).
   (2) 0x800630 (soldier vt+0x74, arms the ZRunToPosShootingTask) and 0x4a7e60 (the run task's run body) are the CloseInProbe's sites c5 / c4 (ids 35 / 34): re-checked unhashed; their counts are reused ('arm800630', 'runtask').
   (3) WINS. The success tail 0x672763 is 'call 0x5caf90' (rel32; not stealable), so the win is taken at the CloseInProbe's c3 (id 33, 0x672770 'fld1' tail, unhashed, esi = tactic), which is on the same path right after the point and the timestamp are written. The handler is integer only (the caller's x87 stack is live): it stores the tick, the game clock, the bot position (raw dwords) and [S+0x98] [S+0x4e8] [S+0x700] [S+0x108]. The 250 ms sampler then takes d0 = the nearest human to the STORED bot position (position helper klbr_human_near, the one the CloseInProbe uses; up to 250 ms after the win), remembers that human, and logs the distance bot (now) -> the same human at the first sample >= +5 s and >= +15 s. Up to 16 wins per round; the rest are only counted.
   (4) DATA every 250 ms per sampled bot: run task [S+0x56c]: [t+8] state (GUESS: same goal layout as the other goals), +0x14..+0x1c dest, +0x20 radius, byte +0x24 shoot flag (field offsets read in 0x5faeb0 in the research, not re-read at run time); movement component [S+0x4a4]: [m+0x14] mode, [m+0x18] speed, [m+0x24..0x2c] target (GUESS: from the research reading of 0x46ce40); [S+0x98] [S+0x4e8] [S+0x700] read as dwords and [S+0x108] as a byte (GUESS: widths). Own budget: 80 lines per round, on change, <= 500 ms apart per bot.
   Lines: 'brain: runprobe win #k t=.. d0=.. d5=.. d15=.. 98=.. 4e8=.. 700=.. 108=..' (-1.0 = unknown), 'brain: runprobe data: ...', 'brain: runprobe round (<online|arcade>) <why>: runbody N direct N cover N arm800630 N runtask N wins N closed(d15<d0) N ...' with the sites not installed. */
#define KLBR_RP_NSITE 3
#define KLBR_RP_NWIN 16
#define KLBR_RP_LOGMAX 80
#define KLBR_RP_GAP 500
static const KLBR_DPSITE klbr_rp_sites[KLBR_RP_NSITE] = {
    { 0x76e8c0, 7, { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x18, 0x56 }, 61, 1 },
    { 0x76e8ed, 9, { 0x8b, 0x4e, 0x04, 0x81, 0xc1, 0xe4, 0x00, 0x00, 0x00 }, 62, 1 },
    { 0x76e935, 10, { 0x8b, 0x4e, 0x04, 0x57, 0x81, 0xc1, 0xe4, 0x00, 0x00, 0x00 }, 63, 1 } };
static int klbr_rp_state, klbr_rp_nok, klbr_rp_okmask, klbr_rp_flt, klbr_rp_nw;
static BYTE *klbr_rp_stub;
typedef struct { long rb, direct, cover, wins, samp; DWORD last; int have; DWORD sig[17]; } KLBR_RPB;
typedef struct { int ix, ph, k, h0; DWORD t0, clk, pos[3], who, f98, f4e8, f700, f108; double d0, d5, d15; } KLBR_RPW;      /* h0: d0 was taken */
static KLBR_RPB klbr_rp_b[KLBR_MAX];
static KLBR_RPW klbr_rp_w[KLBR_RP_NWIN];
static long klbr_rp_unm, klbr_rp_wins, klbr_rp_wdrop, klbr_rp_done, klbr_rp_closed, klbr_rp_nlog;
static void klbr_rp_reset(void) { memset(klbr_rp_b, 0, sizeof klbr_rp_b); memset(klbr_rp_w, 0, sizeof klbr_rp_w); klbr_rp_nw = 0; klbr_rp_unm = klbr_rp_wins = klbr_rp_wdrop = klbr_rp_done = klbr_rp_closed = klbr_rp_nlog = 0; }
static void klbr_rp_win(int ix)      /* a ZCloseIn 1.0 return, inside the CloseInProbe handler (integer code only, no float math: st0 is live) */
{
    DWORD S = klbr_mb_src(ix), body, g; KLBR_RPW *w;
    klbr_rp_b[ix].wins++; klbr_rp_wins++;
    if (klbr_rp_nw >= KLBR_RP_NWIN) { klbr_rp_wdrop++; return; }
    w = &klbr_rp_w[klbr_rp_nw]; memset(w, 0, sizeof *w);
    w->ix = ix; w->k = ++klbr_rp_nw; w->t0 = GetTickCount(); if (!w->t0) w->t0 = 1;
    g = klh_rd32((DWORD_PTR)KLH_VA(0xdd2640)); w->clk = g > 0xffff ? klh_rd32(g + 0x48) : 0;
    body = klh_rd32(S + 0x40); if (body > 0xffff) klh_rd(body + 0x460, w->pos, 12);
    w->f98 = klh_rd32(S + 0x98); w->f4e8 = klh_rd32(S + 0x4e8); w->f700 = klh_rd32(S + 0x700); w->f108 = klh_rd32(S + 0x108) & 0xffu;      /* GUESS: widths */
}
static void __cdecl klbr_rp_hit(int id, KLBR_F3REGS *r)      /* called by the stubs on the game thread */
{
    if (!klbr_rpon || !r || klbr_f6_flt >= 3 || !klbr_f6_tid || GetCurrentThreadId() != klbr_f6_tid) return;
    __try {
        int ix = klbr_ci_by(id == 61 ? r->ecx : r->esi, 0x590);
        if (ix < 0) { klbr_rp_unm++; return; }
        if (id == 61) klbr_rp_b[ix].rb++; else if (id == 62) klbr_rp_b[ix].direct++; else if (id == 63) klbr_rp_b[ix].cover++;
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_rp_flt++; if (klbr_rp_flt <= 3) klog("brain: runprobe: fault in the handler (site id %d): %d of 3 allowed", id, klbr_f6_flt); }
}
static void klbr_rp_install(void)      /* once (game thread); a refusal is final for the run */
{
    int s, ok = 0; BYTE cur[16], jmp[16]; DWORD stub;
    if (klbr_rp_state) return;
    klbr_rp_state = -1;
    if (!klbr_rp_stub && !(klbr_rp_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: runprobe: no memory for the stubs: off"); return; }
    for (s = 0; s < KLBR_RP_NSITE; s++) {
        const KLBR_DPSITE *k = &klbr_rp_sites[s]; BYTE *at = KLH_VA(k->site); int n;
        memset(cur, 0, sizeof cur);
        if (!klh_rd((DWORD_PTR)at, cur, k->len) || memcmp(cur, k->b, k->len)) { klog("brain: runprobe: site %d 0x%x bytes differ from the expected %d (got %02x %02x %02x %02x %02x %02x %02x %02x): NOT installed", k->id, (unsigned)k->site, k->len, cur[0], cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7]); continue; }
        stub = (DWORD)(DWORD_PTR)(klbr_rp_stub + s * 0x40);
        n = kbr_f3_emit(klbr_rp_stub + s * 0x40, stub, k->id, (DWORD)(DWORD_PTR)klbr_rp_hit, k->b, k->len, (DWORD)(DWORD_PTR)(at + k->len));
        if (!n) { klog("brain: runprobe: site %d: stub not built", k->id); continue; }
        kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, k->len);
        if (klh_poke(at, k->b, k->len, jmp, k->len, "brain: RunProbe counting detour")) { ok++; klbr_rp_okmask |= 1 << s; klog("brain: runprobe: site %d 0x%x (%d bytes stolen) installed, stub %d bytes", k->id, (unsigned)k->site, k->len, n); }
        else klog("brain: runprobe: site %d 0x%x NOT installed (refused by the patch guard or the bytes differ)", k->id, (unsigned)k->site);
    }
    klbr_rp_nok = ok; klbr_rp_state = ok == KLBR_RP_NSITE ? 1 : ok ? 2 : -1;
    klog("brain: runprobe: %d of %d sites installed (state %d; policy %s)%s", ok, KLBR_RP_NSITE, klbr_rp_state, klh_policy == KLH_DIRECT ? "direct" : "session/ship", ok < KLBR_RP_NSITE ? " (the others refused or differ: those counts stay 0, the DATA-side samples still run)" : "");
}
static int klbr_rp_hpos(DWORD who, float *tp) { return who > 0xffff && klh_pvt(who) == 0x00bb45f4u && klh_rd(who + 0x460, tp, 12) && kle_ok3(tp); }      /* position of a human ZFFPlayer body (the same type test as klbr_human_near) */
static void klbr_rp_wlog(const KLBR_RPW *w, const char *kind, const char *tail)
{
    klog("brain: runprobe win #%d t=%ld d0=%.1f d5=%.1f d15=%.1f 98=%lx 4e8=%lx 700=%lx 108=%lx (%s bot %d; t = game clock ms at the win%s%s)",
         w->k, (long)w->clk, w->h0 ? w->d0 : -1.0, w->ph >= 2 ? w->d5 : -1.0, w->ph >= 3 ? w->d15 : -1.0, (unsigned long)w->f98, (unsigned long)w->f4e8, (unsigned long)w->f700, (unsigned long)w->f108, kind, w->ix, tail && tail[0] ? "; " : "", tail ? tail : "");
}
static void klbr_rp_steps(int i, const float *bp, int haveb, DWORD now, const char *kind)      /* advance the pending wins of bot i (float math allowed here) */
{
    int k;
    for (k = 0; k < klbr_rp_nw; k++) {
        KLBR_RPW *w = &klbr_rp_w[k]; float tp[3], pos[3]; double d = -1.0; int np;
        if (w->ix != i || w->ph >= 3) continue;
        np = kbr_rp_next(w->ph, kbr_rp_elapsed(now, w->t0));
        if (np == w->ph) continue;
        if (w->ph == 0) {
            double dd = 0.0; DWORD who = 0;
            memcpy(pos, w->pos, 12);
            if (kle_ok3(pos) && klbr_human_near(pos, &dd, &who)) { d = dd; w->who = who; }
            w->d0 = d; w->h0 = 1;
        } else {
            if (haveb && klbr_rp_hpos(w->who, tp)) d = kle_dist(bp, tp);
            if (w->ph == 1) w->d5 = d; else w->d15 = d;
        }
        w->ph = np;
        if (np == 3) {
            int cl = kbr_rp_closed(w->d0, w->d15);
            klbr_rp_done++; if (cl) klbr_rp_closed++;
            klbr_rp_wlog(w, kind, cl ? "CLOSED (d15 < d0)" : "");
        }
    }
}
static void klbr_rp_sample(int i, DWORD S, DWORD now)      /* every 250 ms per sampled bot (called by klbr_mb_sample after its own due test) */
{
    KLBR_RPB *b = &klbr_rp_b[i]; DWORD body, t = 0, m = 0, sig[17]; float bp[3], dv[3], tv[3], rad, spd; int haveb = 0, chg;
    const char *kind = klbr_mb_arc ? (klbr_mb_akind[i] ? "arcade traitor" : "arcade control") : "online marked";
    memset(sig, 0, sizeof sig);
    __try {
        body = klh_rd32(S + 0x40); haveb = body > 0xffff && klh_rd(body + 0x460, bp, 12) && kle_ok3(bp);
        t = klh_rd32(S + 0x56c); m = klh_rd32(S + 0x4a4);
        sig[0] = t;
        if (t > 0xffff) { sig[1] = klh_rd32(t + 8); sig[2] = klh_rd32(t + 0x14); sig[3] = klh_rd32(t + 0x18); sig[4] = klh_rd32(t + 0x1c); sig[5] = klh_rd32(t + 0x20); sig[6] = klh_rd32(t + 0x24) & 0xffu; }
        sig[7] = m;
        if (m > 0xffff) { sig[8] = klh_rd32(m + 0x14); sig[9] = klh_rd32(m + 0x18); sig[10] = klh_rd32(m + 0x24); sig[11] = klh_rd32(m + 0x28); sig[12] = klh_rd32(m + 0x2c); }
        sig[13] = klh_rd32(S + 0x98); sig[14] = klh_rd32(S + 0x4e8); sig[15] = klh_rd32(S + 0x700); sig[16] = klh_rd32(S + 0x108) & 0xffu;      /* GUESS: widths */
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_rp_flt++; return; }
    __try { klbr_rp_steps(i, bp, haveb, now, kind); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_rp_flt++; return; }
    b->samp++;
    chg = !b->have || memcmp(sig, b->sig, sizeof sig);
    if (!chg) return;
    if (klbr_rp_nlog < KLBR_RP_LOGMAX && (!b->last || kbr_mb_due(now, b->last + KLBR_RP_GAP))) {
        memcpy(dv, &sig[2], 12); memcpy(&rad, &sig[5], 4); memcpy(&spd, &sig[9], 4); memcpy(tv, &sig[10], 12);
        klbr_rp_nlog++; b->last = now ? now : 1;
        klog("brain: runprobe data: %s bot %d S %08lx: run task [S+0x56c] %08lx state [t+8] %lu, dest %.1f %.1f %.1f, radius %.1f, shoot byte %lu; movement [S+0x4a4] %08lx mode %lu speed %.2f target %.1f %.1f %.1f (GUESS: [m+0x14] mode, +0x18 speed, +0x24..+0x2c target); [S+0x98] %lx [S+0x4e8] %lx [S+0x700] %lx [S+0x108] %lx; so far runbody %ld direct %ld cover %ld arm800630 %ld runtask %ld wins %ld%s",
             kind, i, (unsigned long)S, (unsigned long)t, (unsigned long)sig[1], (double)dv[0], (double)dv[1], (double)dv[2], (double)rad, (unsigned long)sig[6], (unsigned long)m, (unsigned long)sig[8], (double)spd, (double)tv[0], (double)tv[1], (double)tv[2],
             (unsigned long)sig[13], (unsigned long)sig[14], (unsigned long)sig[15], (unsigned long)sig[16], b->rb, b->direct, b->cover, klbr_ci_b[i].arm, klbr_ci_b[i].rt, b->wins, b->have ? "" : " (first sample)");
    }
    memcpy(b->sig, sig, sizeof sig); b->have = 1;
}
static void klbr_rp_summary(const char *why)      /* the round line; printed when anything was sampled or counted */
{
    long rb = 0, dr = 0, cv = 0, sm = 0, arm = 0, rt = 0; int i, k, n = 0; char miss[96];
    if (!klbr_rpon) return;
    for (i = 0; i < KLBR_MAX; i++) { rb += klbr_rp_b[i].rb; dr += klbr_rp_b[i].direct; cv += klbr_rp_b[i].cover; sm += klbr_rp_b[i].samp; arm += klbr_ci_b[i].arm; rt += klbr_ci_b[i].rt; }
    if (!sm && !rb && !klbr_rp_wins && !arm && !rt) return;
    /* the 30 s 'running total' summary must NOT close pending wins (they would be cut short at <15 s): only round edges do */
    for (k = 0; k < klbr_rp_nw; k++) if (klbr_rp_w[k].ph < 3 && strcmp(why, "running total")) { klbr_rp_wlog(&klbr_rp_w[k], klbr_mb_arc ? "arcade" : "online", "INCOMPLETE at the round edge, unknown values are -1.0"); klbr_rp_w[k].ph = 4; }
    miss[0] = 0;
    for (i = 0; i < KLBR_RP_NSITE; i++) if (!(klbr_rp_okmask & (1 << i)) && n < (int)sizeof miss - 12) n += _snprintf(miss + n, sizeof miss - n, " %d", klbr_rp_sites[i].id);
    for (i = 2; i < 5; i++) if (!(klbr_ci_okmask & (1 << i)) && n < (int)sizeof miss - 12) n += _snprintf(miss + n, sizeof miss - n, " %d", 31 + i);      /* CloseInProbe c3 (win), c4 (runtask), c5 (arm800630) */
    miss[sizeof miss - 1] = 0;
    klog("brain: runprobe round (%s) %s: runbody %ld direct %ld cover %ld arm800630 %ld runtask %ld wins %ld closed(d15<d0) %ld; wins completed %ld, recorded %d of %d (rest only counted: %ld), samples %ld, hits on soldiers not sampled %ld; sites not installed:%s; faults %d, shared %d",
         klbr_mb_arc ? "arcade" : "online", why, rb, dr, cv, arm, rt, klbr_rp_wins, klbr_rp_closed, klbr_rp_done, klbr_rp_nw, KLBR_RP_NWIN, klbr_rp_wdrop, sm, klbr_rp_unm, miss[0] ? miss : " none", klbr_rp_flt, klbr_f6_flt);
}
/* OnlineBrainTraitorAfcProbe (11-04; TEST build only, UNTESTED, recommended off; READ ONLY, NO detour: plain data reads on the game thread from klbr_mb_sample's tick, every read under __try, shares the fault counter klbr_f6_flt (limit 3)).
   Question (re/attackfromcover_1104.md, Verifier 'Endorsed next step' 2): which gate of the ZAttackFromCover eval 0x680b20 fails for the marked traitor, and is the bot farther than 10 m from its defend place ([S+0x64c] block). Once a second per MARKED bot
   (online: the wrapped Arcade-marked bots of the host, so OnlineBrainTraitorArcade=1 is what makes them exist; Arcade offline: the traitor-marked soldiers the DefendProbe samples, 'arcade control' soldiers are skipped), 120 lines per round.
   Fields as the report: b0 = holder [S+0xb0], 5c8 = byte [[S+0x40]+0x5c8], ec = cover state [S+0xec], 88 = mode [S+0x88], 4fc / 6fc = bytes, 6a8 = float [S+0x6a8], 108 = byte, ov = [[[S+0x40]+0x54]+4] (meaning UNREAD, dword width GUESS).
   ddef = cm from the bot ([body+0x460]) to the defend place. GUESS: the block [S+0x64c] stores its position as three floats at +0..+8 (re/attackfromcover_1104.md says 0x40b540 builds it that way; klbotfill.c klbf_gu_style reads the same block and checks [blk+0x14] == soldier, so the same check is used here and ddef is -1 when it fails).
   win = RTTI of [[S+0x648]+0x14] when the Defend goal is the current goal [S+0x74] (the DefendProbe's read, done here directly so the DefendProbe need not be on), else '-'. pred = kbr_af_gate (klbrain_logic.h). */
#define KLBR_AF_LOGMAX 120
static int klbr_afon, klbr_af_nlog, klbr_af_flt; static DWORD klbr_af_at[KLBR_MAX];
static long klbr_af_g[6], klbr_af_far, klbr_af_n, klbr_af_noddef;      /* round: samples per predicted gate (index 1..5), samples with ddef > 1000, all samples, samples without a defend place distance */
static void klbr_af_reset(void) { klbr_af_nlog = 0; memset(klbr_af_at, 0, sizeof klbr_af_at); memset(klbr_af_g, 0, sizeof klbr_af_g); klbr_af_far = klbr_af_n = klbr_af_noddef = 0; }
static void klbr_af_sample(int i, DWORD S, DWORD now)      /* called by klbr_mb_sample after its own due test; throttled to 1 s per bot here */
{
    DWORD body = 0, b0 = 0, ec = 0, m88 = 0, ov = 0, cur = 0, win = 0, blk = 0, p54 = 0; BYTE c5 = 0, f4 = 0, f6 = 0, b108 = 0; float s6a8 = 0, bp[3], dp[3], dd = -1.0f; double dh = -1.0; int haveb = 0, haved = 0, havh = 0, g;
    char wn[32], ddt[24], dht[24]; const char *kind;
    if (!klbr_afon || klbr_f6_flt >= 3) return;
    if (klbr_mb_arc && !klbr_mb_akind[i]) return;      /* Arcade: only the traitor-marked soldier, not the controls */
    if (klbr_af_at[i] && now - klbr_af_at[i] < 1000u) return;      /* the line budget caps only the log; the round counts keep going */
    kind = klbr_mb_arc ? "arcade traitor" : "online marked"; wn[0] = 0;
    __try {
        body = klh_rd32(S + 0x40);
        b0 = klh_rd32(S + 0xb0); ec = klh_rd32(S + 0xec); m88 = klh_rd32(S + 0x88);
        klh_rd(S + 0x4fc, &f4, 1); klh_rd(S + 0x6fc, &f6, 1); klh_rd(S + 0x108, &b108, 1); klh_rd(S + 0x6a8, &s6a8, 4);
        if (body > 0xffff) {
            klh_rd(body + 0x5c8, &c5, 1);
            haveb = klh_rd(body + 0x460, bp, 12) && kle_ok3(bp);
            p54 = klh_rd32(body + 0x54); if (p54 > 0xffff) ov = klh_rd32(p54 + 4);
        }
        blk = klh_rd32(S + 0x64c);
        if (blk > 0xffff && klh_rd32(blk + 0x14) == S && klh_rd(blk, dp, 12) && kle_ok3(dp)) haved = 1;
        if (haveb && haved) dd = kle_dist(bp, dp);
        cur = klh_rd32(S + 0x74);
        if (cur > 0xffff && cur == klh_rd32(S + 0x648)) { win = klh_rd32(cur + 0x14); if (win > 0xffff) klbr_f8_rtti(win, wn, sizeof wn); else _snprintf(wn, sizeof wn, "none"); }
        if (haveb) havh = klbr_human_near(bp, &dh, 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_af_flt++; return; }
    wn[sizeof wn - 1] = 0; if (!wn[0]) _snprintf(wn, sizeof wn, "-");
    klbr_af_at[i] = now | 1u;
    g = kbr_af_gate(b108, b0, c5, ec);
    klbr_af_n++; klbr_af_g[g]++; if (haved && haveb && dd > 1000.0f) klbr_af_far++; if (!(haved && haveb)) klbr_af_noddef++;
    if (haved && haveb) _snprintf(ddt, sizeof ddt, "%.0f", (double)dd); else _snprintf(ddt, sizeof ddt, "n/a"); ddt[sizeof ddt - 1] = 0;
    if (havh) _snprintf(dht, sizeof dht, "%.0f", dh); else _snprintf(dht, sizeof dht, "none"); dht[sizeof dht - 1] = 0;
    if (klbr_af_nlog >= KLBR_AF_LOGMAX) return;
    klbr_af_nlog++;
    klog("brain: afc: rec %d b0 %08lx 5c8 %u ec %lu 88 %lu 4fc %u 6fc %u 6a8 %.1f 108 %u ov %lu ddef %s dhum %s win %s pred %s (%s S %08lx)", i, (unsigned long)b0, (unsigned)c5, (unsigned long)ec, (unsigned long)m88, (unsigned)f4, (unsigned)f6, (double)s6a8, (unsigned)b108, (unsigned long)ov,
         ddt, dht, wn, g == 1 ? "g1 (108 0)" : g == 2 ? "g2 (holder 0)" : g == 3 ? "g3 (5c8 != 0)" : g == 4 ? "g4? (ec 0)" : "pass (ec != 0)", kind, (unsigned long)S);
}
static void klbr_af_summary(const char *why)      /* round edges only (not the 30 s running total); the counters are cleared by klbr_af_reset at the caller's reset */
{
    if (!klbr_afon || !klbr_af_n || !strcmp(why, "running total")) return;
    klog("brain: afc round (%s) %s: samples %ld; predicted g1 (108 0) %ld, g2 (holder 0) %ld, g3 (5c8 != 0) %ld, g4? (ec 0) %ld, pass (ec != 0) %ld; ddef > 1000 cm %ld, ddef unknown %ld; lines %d of %d; faults %d, shared %d",
         klbr_mb_arc ? "arcade" : "online", why, klbr_af_n, klbr_af_g[1], klbr_af_g[2], klbr_af_g[3], klbr_af_g[4], klbr_af_g[5], klbr_af_far, klbr_af_noddef, klbr_af_nlog, KLBR_AF_LOGMAX, klbr_af_flt, klbr_f6_flt);
}
/* OnlineBrainTraitorDriftProbe (READ ONLY) and OnlineBrainTraitorDefendPull (lever L-A, WRITES; 11-04; TEST build only, UNTESTED, recommended off). Research: re/traitor_drift_1104.md (verifier wehl2438m wins where they differ).
   NO detour, no call into a hashed range; plain data on the game thread from klbr_mb_sample's tick (every 250 ms per sampled bot), same targeting as the AfcProbe (online: the host's Arcade-marked wrapped bots, needs OnlineBrainTraitorArcade=1; Arcade offline: the traitor-marked soldier). Every access under __try; a fault bumps the shared klbr_f6_flt AND switches BOTH features off (klbr_df_dead), logged once.
   Block = [S+0x64c], 0x1c bytes (verifier): +0..8 xyz floats, +0x10/+0x11/+0x12 bytes, +0x14 owner soldier (must be S). GUESS: +0x11 is a 'changed' flag the Defend loop reads on its next eval; the pull does NOT touch +0x10/+0x11/+0x12 (side effects unread).
   Holder: [S+0xb0] is resolved as a HANDLE with the pure lookup 0x8ccde0 (unhashed, as the other probes use it; GUESS that b0 is the handle and ac / a8 are other words of the holder record, so ac and a8 are only printed); human = a ZFFPlayer body (vtable 0xbb45f4) that is not a tagged bot.
   Drift line once a second per bot (120/round); EVENT 'drift chg' (cap 60/round, outside the line budget) when the block xyz moves > 300 cm since the last sample (x y z old -> new, winner, [S+0x4fc] byte, [S+0x720]: dword width GUESS).
   Pull: every 250 ms at most per bot, when kbr_pull_ok: the block is ours, the bot is alive (body health unreadable = alive), a living human exists, the block is > 2500 cm from the NEAREST human to the block, and the Defend winner is not ZCloseIn / Board / Loot: block xyz := position of the human nearest to the BOT (GUESS: the right chase target). */
#define KLBR_DF_LOGMAX 120
#define KLBR_DF_CHGMAX 60
#define KLBR_PL_LOGMAX 60
static int klbr_dfon, klbr_plon, klbr_df_dead, klbr_df_nlog, klbr_df_nchg, klbr_pl_nlog, klbr_df_have[KLBR_MAX]; static DWORD klbr_df_at[KLBR_MAX], klbr_pl_at[KLBR_MAX]; static float klbr_df_last[KLBR_MAX][3];
static int klbr_nb_probe_on(void) { return (klbr_dfon || klbr_rpon) && !klbr_df_dead && klbr_f6_flt < 3; }      /* klbotfill.c klbf_nb_drop: DriftProbe or RunProbe on (read-only log gate) */
static int klbr_plmode; static long klbr_pl2_noop, klbr_pl2_snap, klbr_pl2_hold;      /* DefendPull mode (0 off, 1 raw xyz store, 2 stock order 0x760e50); mode 2 counters: silent no-ops (block unchanged), snapped (block != target), holder used as the target base */
static long klbr_df_n, klbr_df_far, klbr_df_hh, klbr_df_chg, klbr_pl_w, klbr_pl_sk[9], klbr_pl_n; static char klbr_df_cn[12][32]; static long klbr_df_cc[12];
static void klbr_df_reset(void) { klbr_df_nlog = klbr_df_nchg = klbr_pl_nlog = 0; memset(klbr_df_have, 0, sizeof klbr_df_have); memset(klbr_df_at, 0, sizeof klbr_df_at); memset(klbr_pl_at, 0, sizeof klbr_pl_at); memset(klbr_df_last, 0, sizeof klbr_df_last); klbr_df_n = klbr_df_far = klbr_df_hh = klbr_df_chg = klbr_pl_w = klbr_pl_n = 0; klbr_pl2_noop = klbr_pl2_snap = klbr_pl2_hold = 0; memset(klbr_pl_sk, 0, sizeof klbr_pl_sk); memset(klbr_df_cn, 0, sizeof klbr_df_cn); memset(klbr_df_cc, 0, sizeof klbr_df_cc); }
static void klbr_df_win(DWORD S, char *wn, int cap)      /* Defend winner RTTI when the Defend goal is current, else "-"; call under __try */
{
    DWORD cur = klh_rd32(S + 0x74), win; wn[0] = 0;
    if (cur > 0xffff && cur == klh_rd32(S + 0x648)) { win = klh_rd32(cur + 0x14); if (win > 0xffff) klbr_f8_rtti(win, wn, cap); else _snprintf(wn, cap, "none"); }
    if (!wn[0]) _snprintf(wn, cap, "-");
    wn[cap - 1] = 0;
}
static void klbr_df_sample(int i, DWORD S, DWORD now)      /* called by klbr_mb_sample after its own 250 ms due test */
{
    DWORD body = 0, blk = 0, b0 = 0, ac = 0, a8 = 0, H = 0, who = 0, whoblk = 0; BYTE b10 = 0, b11 = 0, b12 = 0, f4 = 0; float hp = 1.0f, bp[3], bx[3], hx[3], hbx[3], hh[3], hold[3], dbl = -1.0f; double dbh = -1.0, dhb = -1.0, dhh = -1.0, dd; DWORD v720 = 0;
    int haveb = 0, haveblk = 0, own = 0, alive = 1, humb = 0, humbot = 0, hhum = 0, hhpos = 0, wc = 0, dolog, moved = 0, dopull = 0, sk = 0, p2 = 0, p2hold = 0, p2snap = 0, p2noop = 0, hpsrc = 0; float hp_a48 = -999.0f, p2t[3], p2h[3], p2a[3]; char wn[32], t1[24], t2[24], t3[24], t4[24]; float old[3];
    if ((!klbr_dfon && !klbr_plon) || klbr_df_dead || klbr_f6_flt >= 3) return;
    if (klbr_mb_arc && !klbr_mb_akind[i]) return;      /* Arcade: only the traitor-marked soldier */
    dolog = klbr_dfon && (!klbr_df_at[i] || now - klbr_df_at[i] >= 1000u);
    wn[0] = 0; memset(hbx, 0, sizeof hbx); memset(hh, 0, sizeof hh); memset(hx, 0, sizeof hx); memset(old, 0, sizeof old);
    __try {
        body = klh_rd32(S + 0x40);
        blk = klh_rd32(S + 0x64c);
        if (blk > 0xffff) {
            own = klh_rd32(blk + 0x14) == S;
            haveblk = klh_rd(blk, bx, 12) && kle_ok3(bx);
            klh_rd(blk + 0x10, &b10, 1); klh_rd(blk + 0x11, &b11, 1); klh_rd(blk + 0x12, &b12, 1);
        }
        if (body > 0xffff) {
            haveb = klh_rd(body + 0x460, bp, 12) && kle_ok3(bp);
            {   /* GUESS (root cause): a bot body keeps its health at [body+0x5fc] (NPC object, klbot.c), not at the player's [+0xa48], where +4 read <= 0 every tick */
                DWORD nh = klh_rd32(body + 0x5fc); float nv[2] = { 0, 0 }, pv = 0.0f; int nok = 0, pok = 0;
                if (nh > 0xffff && klh_rd32(nh + 0x24) == body && klh_rd(nh + 4, nv, 8) && nv[0] == nv[0]) nok = 1;
                if (!nok && klh_pvt(body) == 0x00bb45f4u && klbr_hp_read(body, &pv)) pok = 1;
                hpsrc = kbr_alive_pick(nok, nv[0], pok, pv, &hp, &alive);
                { float pv2 = 0.0f; hp_a48 = klbr_hp_read(body, &pv2) ? pv2 : -999.0f; }      /* diagnostic only: what the old test read */
            }
        }
        if (haveblk) {      /* EVENT: the block moved more than 300 cm since the last sample (also feeds the pull's own bookkeeping) */
            if (klbr_dfon && klbr_df_have[i] && kbr_drift_moved(klbr_df_last[i], bx, 300.0f)) {
                moved = 1; memcpy(old, klbr_df_last[i], 12);
                klbr_df_win(S, wn, sizeof wn); klh_rd(S + 0x4fc, &f4, 1); v720 = klh_rd32(S + 0x720);
            }
            humb = klbr_human_near(bx, &dhb, &whoblk);
        }
        if (dolog || klbr_plon) {
            if (haveb) humbot = klbr_human_near(bp, &dbh, &who);
            if (humbot && klbr_rp_hpos(who, hx)) {} else humbot = 0;
        }
        if (dolog) {
            if (!wn[0]) klbr_df_win(S, wn, sizeof wn);
            if (!moved) klh_rd(S + 0x4fc, &f4, 1);
            a8 = klh_rd32(S + 0xa8); ac = klh_rd32(S + 0xac); b0 = klh_rd32(S + 0xb0);
            if (ac > 0xffff && klh_pvt(ac) == 0x00bb45f4u) H = ac;      /* review fix: [S+0xac] is the holder POINTER in the fireprobe code (hp = [self+0xac] tested for the ZFFPlayer vtable); b0 is the handle, resolved only when ac is not a player body */
            else if (b0 > 0xffff) H = ((klbr_cfrefn)(DWORD_PTR)KLH_VA(KLBR_CF_REF))(b0);
            if (H > 0xffff) {
                hhum = klh_pvt(H) == 0x00bb45f4u && !klbr_hl_find(H);
                hhpos = klh_rd(H + 0x460, hold, 12) && kle_ok3(hold);
                if (hhpos && klbr_human_near(hold, &dhh, 0)) {} else dhh = -1.0;
            }
        }
        if (klbr_plon) {
            klbr_pl_n++;
            if (!wn[0]) klbr_df_win(S, wn, sizeof wn);
            wc = kbr_win_class(wn);
            dbl = (humb && haveblk) ? (float)dhb : -1.0f;
            sk = kbr_pull_skip(own && haveblk, alive, humb && humbot, (long)dbl, wc, klbr_pl_at[i] ? (unsigned long)(now - klbr_pl_at[i]) : 100000ul);
            if (!sk && klbr_plmode == 2) {      /* mode 2: the stock order 0x760e50 to a place 550 cm short of the holder (else the nearest human), reset 0; mode 1 below is unchanged */
                DWORD ac2 = klh_rd32(S + 0xac), hw = 0; double dh2 = 0; struct kle_e te; float got2[3]; char why2[100];
                memset(p2t, 0, sizeof p2t); memset(p2a, 0, sizeof p2a); why2[0] = 0;
                memcpy(p2h, hx, 12);
                if (ac2 > 0xffff && klh_pvt(ac2) == 0x00bb45f4u && !klbr_hl_find(ac2) && klh_rd(ac2 + 0x460, hold, 12) && kle_ok3(hold) && klbr_human_near(hold, &dh2, &hw) && hw == ac2) { memcpy(p2h, hold, 12); p2hold = 1; }      /* holder [S+0xac] is a living human */
                if (!haveb) sk = 8;
                else if (kbr_pull2_target(p2h, bp, p2t)) sk = 7;
                else {
                    memset(&te, 0, sizeof te); te.rec = -1; te.soldier = S; te.told_soft = 1;      /* temporary entry, rec -1: no OrderGap debounce (as klbotfill.c:412 / :1292) */
                    if (!kle_callable(why2)) sk = 8;
                    else if (kle_order3(&te, p2t, got2, why2, 0) != 1) sk = 8;
                    else {
                        if (!kle_block(S, p2a)) memcpy(p2a, bx, 12);
                        p2 = 1; p2noop = kle_dist(p2a, bx) < 1.0f; p2snap = kle_dist(p2a, p2t) > 1.0f;
                    }
                }
                if (sk) klbr_pl_sk[sk]++;
                else { memcpy(old, bx, 12); dopull = 1; }
            }
            else if (sk) klbr_pl_sk[sk]++;
            else {
                memcpy(old, bx, 12); dopull = 1;
                *(volatile float *)(DWORD_PTR)(blk + 0) = hx[0]; *(volatile float *)(DWORD_PTR)(blk + 4) = hx[1]; *(volatile float *)(DWORD_PTR)(blk + 8) = hx[2];      /* only xyz: +0x10 / +0x11 / +0x12 untouched */
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        klbr_f6_flt++; klbr_df_dead = 1;
        klog("brain: drift/pull: fault at the game data (shared fault counter now %d): DriftProbe AND DefendPull are OFF for the rest of the session", klbr_f6_flt);
        return;
    }
    if (haveblk) {
        if (moved) {
            klbr_df_chg++; kbr_ci_name_tally(klbr_df_cn, klbr_df_cc, 12, wn);
            if (klbr_df_nchg < KLBR_DF_CHGMAX) {
                klbr_df_nchg++;
                klog("brain: drift chg: rec %d block (%.0f %.0f %.0f) -> (%.0f %.0f %.0f), moved %.0f cm; winner %s, 4fc %u, 720 %lu (S %08lx)", i, (double)old[0], (double)old[1], (double)old[2], (double)bx[0], (double)bx[1], (double)bx[2],
                     kle_dist(old, bx) + 0.0, wn, (unsigned)f4, (unsigned long)v720, (unsigned long)S);
            }
        }
        if (dopull) {
            klbr_pl_w++; klbr_pl_at[i] = now | 1u;
            if (p2) {
                klbr_pl2_noop += p2noop; klbr_pl2_snap += p2snap; klbr_pl2_hold += p2hold;
                if (klbr_pl_nlog < KLBR_PL_LOGMAX) { klbr_pl_nlog++; klog("brain: pull2: rec %d block before (%.0f %.0f %.0f) after (%.0f %.0f %.0f), target (%.0f %.0f %.0f) base %s (%.0f %.0f %.0f) bot (%.0f %.0f %.0f), snapped %d, silent no-op %d (no-ops so far %ld; block was %.0f cm from the nearest human; winner %s; S %08lx)",
                    i, (double)old[0], (double)old[1], (double)old[2], (double)p2a[0], (double)p2a[1], (double)p2a[2], (double)p2t[0], (double)p2t[1], (double)p2t[2], p2hold ? "holder" : "nearest human", (double)p2h[0], (double)p2h[1], (double)p2h[2],
                    (double)bp[0], (double)bp[1], (double)bp[2], p2snap, p2noop, klbr_pl2_noop, (double)dbl, wn, (unsigned long)S); }
                memcpy(klbr_df_last[i], p2a, 12); klbr_df_have[i] = 1;
            } else {
            if (klbr_pl_nlog < KLBR_PL_LOGMAX) { klbr_pl_nlog++; klog("brain: pull: rec %d from (%.0f %.0f %.0f) to (%.0f %.0f %.0f) dhum %.0f (block was %.0f cm from the nearest human; winner %s; S %08lx)", i, (double)old[0], (double)old[1], (double)old[2], (double)hx[0], (double)hx[1], (double)hx[2], dbh, (double)dbl, wn, (unsigned long)S); }
            memcpy(klbr_df_last[i], hx, 12); klbr_df_have[i] = 1;      /* our own write is not a 'chg' event */
            }
        } else { memcpy(klbr_df_last[i], bx, 12); klbr_df_have[i] = 1; }
    } else klbr_df_have[i] = 0;
    if (!dolog) return;
    klbr_df_at[i] = now | 1u;
    klbr_df_n++; if (haveblk && humb && dhb > 2500.0) klbr_df_far++; if (hhum) klbr_df_hh++;
    if (klbr_df_nlog >= KLBR_DF_LOGMAX) return;
    klbr_df_nlog++;
    dd = (haveb && haveblk) ? kle_dist(bp, bx) : -1.0;
    _snprintf(t1, sizeof t1, "%.0f", (haveblk && humb) ? dhb : -1.0); _snprintf(t2, sizeof t2, "%.0f", (haveb && humbot) ? dbh : -1.0); _snprintf(t3, sizeof t3, "%.0f", dd); _snprintf(t4, sizeof t4, "%.0f", H > 0xffff && hhpos ? dhh : -1.0);
    t1[sizeof t1 - 1] = t2[sizeof t2 - 1] = t3[sizeof t3 - 1] = t4[sizeof t4 - 1] = 0;
    klog("brain: drift: rec %d blk %08lx xyz %.0f %.0f %.0f own==S %d b10 %u b11 %u b12 %u dblk_hum %s dbot_hum %s dbot_blk %s hold ac %08lx b0 %08lx a8 %08lx hold_human %d dhold_hum %s win %s 4fc %u hp %.1f src %s alive %d a48 %.1f (%s S %08lx)",
         i, (unsigned long)blk, haveblk ? (double)bx[0] : 0.0, haveblk ? (double)bx[1] : 0.0, haveblk ? (double)bx[2] : 0.0, own, (unsigned)b10, (unsigned)b11, (unsigned)b12, t1, t2, t3, (unsigned long)ac, (unsigned long)b0, (unsigned long)a8, hhum, t4, wn, (unsigned)f4,
         (double)hp, hpsrc == 1 ? "npc5fc" : hpsrc == 2 ? "player" : "none", alive, (double)hp_a48,
         klbr_mb_arc ? "arcade traitor" : "online marked", (unsigned long)S);
}
static void klbr_df_summary(const char *why)      /* round edges only; counters cleared by klbr_df_reset */
{
    int k; char tl[200]; int n = 0;
    if (!strcmp(why, "running total")) return;
    if (klbr_dfon && (klbr_df_n || klbr_df_chg)) {
        tl[0] = 0;
        for (k = 0; k < 12 && klbr_df_cn[k][0] && n < (int)sizeof tl - 40; k++) n += _snprintf(tl + n, sizeof tl - n, " %s x%ld", klbr_df_cn[k], klbr_df_cc[k]);
        tl[sizeof tl - 1] = 0;
        klog("brain: drift round (%s) %s: samples %ld; dblk_hum > 2500 cm %d%%; holder human %d%%; block moves > 300 cm %ld (by winner:%s); chg lines %d of %d, drift lines %d of %d; dead %d, shared faults %d",
             klbr_mb_arc ? "arcade" : "online", why, klbr_df_n, kbr_ci_pct(klbr_df_far, klbr_df_n), kbr_ci_pct(klbr_df_hh, klbr_df_n), klbr_df_chg, tl[0] ? tl : " none", klbr_df_nchg, KLBR_DF_CHGMAX, klbr_df_nlog, KLBR_DF_LOGMAX, klbr_df_dead, klbr_f6_flt);
    }
    if (klbr_plon && klbr_pl_n)
        klog("brain: pull round (%s) %s: ticks %ld, pulls written %ld, skipped: not ours/no block %ld, dead %ld, no human %ld, block near a human %ld, winner owns the block or Defend not current (CloseIn/Board/Loot/-) %ld, rate %ld, mode 2 only: bot within 550 cm of the holder %ld, order refused / no bot position %ld; lines %d of %d; dead %d; mode %d (mode 2: orders %ld, silent no-ops %ld, snapped %ld, holder base %ld)",
             klbr_mb_arc ? "arcade" : "online", why, klbr_pl_n, klbr_pl_w, klbr_pl_sk[1], klbr_pl_sk[2], klbr_pl_sk[3], klbr_pl_sk[4], klbr_pl_sk[5], klbr_pl_sk[6], klbr_pl_sk[7], klbr_pl_sk[8], klbr_pl_nlog, KLBR_PL_LOGMAX, klbr_df_dead,
             klbr_plmode, klbr_plmode == 2 ? klbr_pl_w : 0L, klbr_pl2_noop, klbr_pl2_snap, klbr_pl2_hold);
}
/* OnlineBrainTraitorCombatFlag (11-04; TEST build only, UNTESTED, recommended off; CHANGES the game: ONE data byte, [S+0x4fc], and only under the gates below). Lever from re/approach_lever_1104.md: the Defend tick 0x85f6c0 walks tactic list A (with ZCloseIn) only while [S+0x4fc] != 0 AND a [S+0x6fc] condition holds.
   Value 1 = the spec of the verifier text (write only while [S+0x6fc] == 0); value 2 = the disassembly (write only while [S+0x6fc] != 0). RE-READ 11-04 at 0x85f896: cmp [eax+4fc],0 / je -> flag 0; cmp [eax+6fc],0 / mov flag,1 / jne keep / else flag 0: list A needs BOTH bytes nonzero, so the verifier text is wrong and 2 is the useful mode; 1 is kept only to be able to test the claim. Once a human is clear again the byte WE set is written back to 0 (stock firing needs it 0). Host game thread, online marked bots only, every 250 ms per wrapped bot.
   Value 3 (UNTESTED, GUESS that it makes ZCloseIn run): same gates, writes 4fc = 1 AND, if [S+0x6fc] == 0, 6fc = 1 (klbr_cb_set6 remembers it was OURS); both undone when a human turns clear / the pass goes stale, 6fc only if still 1 (stock writers 0x7b3991, 0x578d3b/0x578d93, 0x5a3a03 are never clobbered). Unwrap / round end only forget (the memory may be gone).
   Gates (kbr_cb_decide): the bot is wrapped and alive; LosGate AND Sense are on (the per-bot Sense pass record says how many humans were skipped as BLOCKED and how many were fed/open); at least one human is blocked and NONE is open; byte 4fc not already 1. Never written while any human is clear. Faults: 3 = off. */
static void klbr_cb_reset(void) { klbr_cb_undo = 0; klbr_cb_w6 = klbr_cb_r6 = klbr_cb_nz6 = 0; memset(klbr_cb_set, 0, sizeof klbr_cb_set); memset(klbr_cb_set6, 0, sizeof klbr_cb_set6); klbr_cb_w = klbr_cb_sk_clear = klbr_cb_sk_6fc = klbr_cb_sk_nopass = klbr_cb_already = klbr_cb_b0null = 0; memset(klbr_cb_first, 0, sizeof klbr_cb_first); memset(klbr_cb_next, 0, sizeof klbr_cb_next); memset(klbr_cb_pass, 0, sizeof klbr_cb_pass); }
static void klbr_cb_summary(const char *why)
{
    if (!klbr_cbmode) return;
    if (!klbr_cb_w && !klbr_cb_w6 && !klbr_cb_r6 && !klbr_cb_nz6 && !klbr_cb_sk_clear && !klbr_cb_sk_6fc && !klbr_cb_sk_nopass && !klbr_cb_already && !klbr_cb_undo && !klbr_cb_flt) return;
    klog("brain: combatflag round %s: writes %ld (of those [S+0xb0] was null %ld), skipped (clear human) %ld, skipped (6fc) %ld, skipped (no fresh pass or nobody blocked) %ld, already set %ld, undone when a human turned clear %ld, faults %d; 6fc (mode 3) written by us %ld, restored to 0 %ld, already nonzero (left alone) %ld; mode %d", why, klbr_cb_w, klbr_cb_b0null, klbr_cb_sk_clear, klbr_cb_sk_6fc, klbr_cb_sk_nopass, klbr_cb_already, klbr_cb_undo, klbr_cb_flt, klbr_cb_w6, klbr_cb_r6, klbr_cb_nz6, klbr_cbmode);
    klbr_cb_w = klbr_cb_sk_clear = klbr_cb_sk_6fc = klbr_cb_sk_nopass = klbr_cb_already = klbr_cb_b0null = klbr_cb_undo = klbr_cb_w6 = klbr_cb_r6 = klbr_cb_nz6 = 0;
}
/* OnlineBrainTraitorHolderSet (11-04; TEST build only, UNTESTED, recommended off; CHANGES the game: re-writes the marked bot's target holder [S+0xa8..] through the game's own setter). Lever from re/holder_b0_1104.md (Verifier, 'Endorsed lever'):
   ZCloseIn 0x6724e0 and the fire clause 0x85ece0 both bail on [S+0xb0] == 0, and online the stock target scan 0x767510 clears it (SetHolder(0) at 0x767f8a, no winner) because LosGate keeps every blocked human out of the known list.
   While EVERY human is LOS-BLOCKED for the bot (the fresh Sense / LosGate pass record, as CombatFlag), the holder is pointed at the nearest live human body H: handle = 0x6ece90 (thiscall, ecx = H, no stack args, plain ret; disassembled 11-04), required to round-trip through
   0x8ccde0 (cdecl, 1 arg, plain ret; the same lookup SetHolder runs internally and then dereferences without a null test, hence the check); then SetHolder 0x8bd420 (thiscall, ecx = S+0xa8, stack args (handle, DWORD* flagsptr), ret 8; refcount of the old / new [ent+0x54] is balanced inside, so repeating the call is safe).
   Flags: mode 1 = 0x01 (bit0 only: what every stock one-shot setter leaves; bit 0x10 missing, so the fire test 0x616480 [bit0 AND 0x10 set, 0x4 / 0x40 / 0x200 clear] FAILS and the bot cannot shoot through the wall, while ZCloseIn, which reads no flags, passes);
   mode 2 = 0x15 (bit0 + 0x10 + 0x4: bit 0x4 is the 'friend in the line' hold-fire bit Arcade bots alternate through, so the fire test also FAILS; chosen to see whether anything else wants 0x10). 0x11 is NOT used: it passes the fire test. Both values are checked against that mask in klbrain_test.c.
   The next full scan of 0x767510 (>= 0x400 ms, or right after a MarkSeen) wipes the write, so it is re-applied every pump tick (throttled to 100 ms per bot) and only when the handle or the flags dword differ (no churn: 'kept'). The quick path between scans keeps handle and flags (0x200 may be re-computed: then the flags differ and are rewritten).
   When a human turns CLEAR the lever stops writing and does NOT clear: the stock scan / HolderFix take over (HolderFix skips the bot while the lever is active, so it never turns our 0x01 into a firing 0x11 for a blocked human; once a human is clear it works as before).
   Gates: host game thread (the pump), online marked wrapped bots, LosGate AND Sense on (else nothing is written, one line), 3 faults (__try around the calls) = off for the round. GUESS: that the nearest human is the right target (blocked humans are all equal for the lever's purpose; klbr_human_near skips tagged bots and the dead), that [S+0x4fc]/[S+0x6fc]/[S+0x590] are right for ZCloseIn to run (use CombatFlag=2 for that). */
static int klbr_hs_nolog, klbr_hs_first[KLBR_MAX]; static DWORD klbr_hs_next[KLBR_MAX];
static long klbr_hs_w, klbr_hs_kept, klbr_hs_sk_clear, klbr_hs_mismatch, klbr_hs_nohuman, klbr_hs_nopass;
static void klbr_hs_reset(void) { klbr_hs_flt = 0; klbr_hs_w = klbr_hs_kept = klbr_hs_sk_clear = klbr_hs_mismatch = klbr_hs_nohuman = klbr_hs_nopass = 0; memset(klbr_hs_first, 0, sizeof klbr_hs_first); memset(klbr_hs_next, 0, sizeof klbr_hs_next); }
static void klbr_hs_summary(const char *why)
{
    if (!klbr_hsmode) return;
    if (!klbr_hs_w && !klbr_hs_kept && !klbr_hs_sk_clear && !klbr_hs_mismatch && !klbr_hs_nohuman && !klbr_hs_nopass && !klbr_hs_flt) return;
    klog("brain: holderset round %s: writes %ld, kept %ld, skipped clear %ld, lookup-mismatch %ld, no-human %ld, no-pass %ld, faults %d; flags 0x%lx (mode %d)", why, klbr_hs_w, klbr_hs_kept, klbr_hs_sk_clear, klbr_hs_mismatch, klbr_hs_nohuman, klbr_hs_nopass, klbr_hs_flt, kbr_hs_flags(klbr_hsmode), klbr_hsmode);
    klbr_hs_w = klbr_hs_kept = klbr_hs_sk_clear = klbr_hs_mismatch = klbr_hs_nohuman = klbr_hs_nopass = 0;
}
/* DATA-side sampling (11-04, Task D), every 250 ms per marked traitor bot, reads only, all in __try, independent of whether the code sites installed. Offsets checked against the disassembly (debug/dasm.py 11-04):
     [S+0x658] ZAttackTarget goal g: 0x8318e8 (slot 83) loads it, 0x831952 reads [edi+8] of the result; state [g+8], target handle [g+0x14] and owner [g+4] = S from the tick head 0x4f448b / 0x4f446d (esi = g).               VERIFIED
     [S+0x654] CoverFire goal: 0x831930 / 0x83193f load it, 0x831952 reads its [+8] state.                                                                                                                           VERIFIED
     [S+0x5ac] state [[S+0x5ac]+8]: 0x83185f / 0x83186c.                                                                                                                                                             VERIFIED
     [S+0x4fc] BYTE: slot 83 clears it at entry (0x831865 mov byte [esi+0x4fc],0); the mode-B no-clear tail 0x4f4ba9 sets it to 1 at 0x4f4bc3 with ecx = [g+4] = S.                                                           VERIFIED
     [S+0x56c] run task: 0x800645 / 0x800650 (soldier vt+0x74 = 0x800630) load it and call 0x5faeb0 on it.  Its state at [t+8]: GUESS (same goal base layout as the other goals; not read from 0x5faeb0).
     [S+0x74] current goal, [S+0x78] its priority: 0x81eb90 (goal chooser; callers 0x5f0cb2, 0x6353b9, 0x651d62) stores the chosen entry's [+0] to [this+0x74] and [+4] to [this+0x78] (0x81ec54 / 0x81ec5a) and
              compares them (0x81ec13 / 0x81ec29). That THIS is the ZSoldier S of slot 83 (and not a base sub-object at the same address) is a GUESS: the data will show (current == [S+0x658] while it attacks).
   Only transitions of the tuple (g state, current == attack goal, attack goal null, CoverFire state, 4fc, run-task state, 5ac state, priority, target handle) are logged, at most one line per bot per 500 ms and 60 per round. */
static const DWORD klbr_mb_hoff[9] = { 0x638, 0x634, 0x648, 0x65c, 0x63c, 0x658, 0x654, 0x56c, 0x5ac };
static const char *const klbr_mb_hname[10] = { "Attack+638", "Idle+634", "Defend+648", "StayInCover+65c", "Follow+63c", "AttackTarget+658", "CoverFire+654", "RunTask+56c", "+5ac", "none of those" };
/* data2 (11-04b, read only, same key; the verifier of attack_goal_1104.md asked which goal holds the bot at priority 0x96): per sample also the vtable of the current goal [S+0x74] (ZSoldierAttack 0xbd0f14 / ZAttackTarget 0xbd1104, else hex), which of the soldier's goal slots
   (+0x638 Attack, +0x634 Idle, +0x648 Defend, +0x65c StayInCover, +0x63c Follow, +0x658 AttackTarget, +0x654 CoverFire, +0x56c run task, +0x5ac) holds that same pointer, the states of 638 / 634 / 648 / 65c / 63c, the dword mode [S+0x88] (Arcade 2, online bot 1 per attack_goal_1104.md; GUESS that the field is a dword on every bot) and the two dwords [S+0xa8] / [S+0xb0] (the task calls them holder flags; GUESS: raw dwords, no meaning assumed).
   Round histograms: current-goal vtable class, other vtables (up to 8), [S+0x88], holder slot. Source: online = the marked bots of the slot-113 wrapper (klbr_f6_sold); Arcade (offline; role 0 / 1, mode 4, real rules: the ArcadeDiag test) = every Ally soldier whose record has rec+0x79 bit 1 (the Traitor mark), else the first 2 Ally soldiers as controls ('arcade control'), rescanned every 3 s. */
static void klbr_mb_sample(DWORD now)
{
    int i; KLBR_MBC *c = &klbr_mb_c;
    for (i = 0; i < KLBR_MAX; i++) {
        DWORD S = klbr_mb_src(i), g, cur, hp[9]; KLBR_MBSIG n, *o = &klbr_mb_sig[i]; BYTE b4 = 0; int k;
        if (S <= 0xffff) { o->have = 0; continue; }
        if (klbr_mb_dnext[i] && !kbr_mb_due(now, klbr_mb_dnext[i])) continue;
        klbr_mb_dnext[i] = now + KLBR_MB_DSTEP; if (!klbr_mb_dnext[i]) klbr_mb_dnext[i] = 1;
        if (klbr_cion) klbr_ci_sample(i, S, now); if (klbr_dpon) klbr_dp_sample(i, S, now); if (klbr_rpon) klbr_rp_sample(i, S, now); if (klbr_afon) klbr_af_sample(i, S, now); if (klbr_dfon || klbr_plon) klbr_df_sample(i, S, now);      /* OnlineBrainTraitorCloseInProbe */
        if (!klbr_mbon) continue;
        memset(&n, 0, sizeof n);
        __try {
            g = klh_rd32(S + 0x658); cur = klh_rd32(S + 0x74);
            n.g = g > 0xffff; n.gst = n.g ? (int)klh_rd32(g + 8) : -1; n.tgt = n.g ? klh_rd32(g + 0x14) : 0;
            n.iscur = n.g && cur == g; n.curnz = cur > 0xffff; n.pri = klh_rd32(S + 0x78);
            n.st654 = klbr_mb_state_of(S, 0x654); n.st56c = klbr_mb_state_of(S, 0x56c); n.st5ac = klbr_mb_state_of(S, 0x5ac);
            klh_rd(S + 0x4fc, &b4, 1); n.nocl = b4 != 0;
            n.curvt = n.curnz ? klh_rd32(cur) : 0; if (n.curvt) n.curvt -= (DWORD)klh_delta;      /* unrebased, as the notes quote it */
            for (k = 0; k < 9; k++) hp[k] = klh_rd32(S + klbr_mb_hoff[k]);
            n.hold = kbr_mb_match(cur, hp, 9);
            n.st638 = klbr_mb_state_of(S, 0x638); n.st634 = klbr_mb_state_of(S, 0x634); n.st648 = klbr_mb_state_of(S, 0x648); n.st65c = klbr_mb_state_of(S, 0x65c); n.st63c = klbr_mb_state_of(S, 0x63c);
            n.mode = klh_rd32(S + 0x88); n.fa8 = klh_rd32(S + 0xa8); n.fb0 = klh_rd32(S + 0xb0);
        } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_mb_flt++; continue; }
        c->dsamp++; c->d2samp++; if (n.iscur) c->datk++; if (n.nocl) c->dnocl++;
        if (!n.g) c->anull++; else if (n.gst >= 0 && n.gst <= 4) c->ahist[n.gst]++; else c->aother++;
        c->vth[kbr_mb_vtclass(n.curvt)]++; c->modeh[kbr_mb_modeslot(n.mode)]++;
        if (kbr_mb_vtclass(n.curvt) == 3 && kbr_mb_tally(c->ovtk, c->ovtn, 8, n.curvt) < 0) c->ovtfull++;
        if (n.curnz) c->holdh[n.hold >= 0 ? n.hold : 9]++;
        if (!o->have || o->g != n.g || o->gst != n.gst || o->iscur != n.iscur || o->curnz != n.curnz || o->st654 != n.st654 || o->nocl != n.nocl || o->st56c != n.st56c || o->st5ac != n.st5ac || o->pri != n.pri || o->tgt != n.tgt
            || o->curvt != n.curvt || o->hold != n.hold || o->st638 != n.st638 || o->st634 != n.st634 || o->st648 != n.st648 || o->st65c != n.st65c || o->st63c != n.st63c || o->mode != n.mode || o->fa8 != n.fa8 || o->fb0 != n.fb0) {
            if (o->have) c->dtrans++;
            if (c->dlog < KLBR_MB_DLOGMAX && (!o->last || (now - o->last) >= KLBR_MB_DLOGGAP)) {
                char vtx[24];
                c->dlog++; n.last = now ? now : 1;
                if (kbr_mb_vtclass(n.curvt) == 3) _snprintf(vtx, sizeof vtx, "other %08lx", (unsigned long)n.curvt); else _snprintf(vtx, sizeof vtx, "%s", kbr_mb_vtname(n.curvt));
                vtx[sizeof vtx - 1] = 0;
                klog("brain: modeb data: %s bot %d S %08lx: attack goal %s state %d target %08lx; current goal %s attack goal, priority %lu; CoverFire state %d; [S+0x4fc] %d; run task state %d; [S+0x5ac] state %d%s; "
                     "data2: current goal vtable %s, held by slot %s; states Attack(638) %d Idle(634) %d Defend(648) %d StayInCover(65c) %d Follow(63c) %d; mode [S+0x88] %lu; [S+0xa8] %08lx [S+0xb0] %08lx",
                     klbr_mb_arc ? (klbr_mb_akind[i] ? "arcade traitor" : "arcade control") : "online marked", i, (unsigned long)S, n.g ? "set" : "NULL", n.gst, (unsigned long)n.tgt, !n.curnz ? "none (!=)" : n.iscur ? "==" : "!=", (unsigned long)n.pri, n.st654, n.nocl, n.st56c, n.st5ac, o->have ? "" : " (first sample)",
                     vtx, n.curnz ? klbr_mb_hname[n.hold >= 0 ? n.hold : 9] : "-", n.st638, n.st634, n.st648, n.st65c, n.st63c, (unsigned long)n.mode, (unsigned long)n.fa8, (unsigned long)n.fb0);
            } else n.last = o->last;
        } else n.last = o->last;
        n.have = 1; *o = n;
    }
}
static int klbr_mb_arcade(DWORD *rules)      /* the ArcadeDiag test: role 0 / 1, mode 4, real rules present (CERTAIN for the question; GUESS that offline Arcade reads role 0 / 1 and mode 4 here) */
{
    DWORD sm, role = 0, mode = 0, G, r = 0;
    G = klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); if (G > 0xffff) r = klh_rd32(G + 0x54);
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION));
    *rules = r;
    return sm > 0xffff && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && role <= 1 && mode == 4 && r > 0xffff && r != klbr_shadow;
}
static void klbr_mb_arc_scan(DWORD now, DWORD rules)      /* every 3 s in Arcade: pick the soldiers to sample (marked, else 2 controls) */
{
    DWORD actor[KLBR_MAX], snd[KLBR_MAX], crew = klh_rd32(rules + 0x348), nrec = klh_rd32(rules + 0x354), nw[KLBR_MAX]; int n, i, k, trait[KLBR_MAX], sel[KLBR_MAX], nk[KLBR_MAX];
    klbr_mb_ascan = now ? now : 1;
    n = klbr_scan(actor, snd, KLBR_MAX);
    memset(nw, 0, sizeof nw); memset(nk, 0, sizeof nk);
    for (i = 0; i < n; i++) {
        BYTE b = 0; trait[i] = 0;
        if (crew > 0xffff && nrec <= 12)
            for (k = 0; k < (int)nrec; k++) if (klh_rd32(crew + 0x7c * (DWORD)k + 4) == actor[i] && klh_rd(crew + 0x7c * (DWORD)k + 0x79, &b, 1)) { trait[i] = (b & 2) ? 1 : 0; break; }
    }
    kbr_mb_arc_pick(trait, n, sel, 2);
    for (i = 0, k = 0; i < n && k < KLBR_MAX; i++) if (sel[i]) { nw[k] = snd[i]; nk[k] = trait[i]; k++; }
    for (i = 0; i < KLBR_MAX; i++) {      /* compared by index: a slot whose soldier changed starts over */
        if (nw[i] != klbr_mb_asold[i]) { memset(&klbr_mb_sig[i], 0, sizeof klbr_mb_sig[i]); klbr_mb_dnext[i] = 0; klbr_mb_t0[i] = 0; memset(&klbr_ci_b[i], 0, sizeof klbr_ci_b[i]); }
        klbr_mb_asold[i] = nw[i]; klbr_mb_akind[i] = nk[i];
    }
}
static void klbr_mb_summary(const char *why);
static void klbr_mb_tick(DWORD now)      /* game thread: the bot-to-point distance every 500 ms for 10 s after a stock RunChild */
{
    int i;
    if ((!klbr_mbon && !klbr_cion && !klbr_dpon && !klbr_afon && !klbr_dfon && !klbr_plon) || klbr_f6_flt >= 3) return;
    {
        DWORD rules = 0; int arc;
        __try { arc = klbr_mb_arcade(&rules); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_mb_flt++; arc = 0; }
        if (arc && rules != klbr_mb_arules) {      /* a new Arcade round (new rules object): the last one's summary, then fresh counters */
            if (klbr_mb_arules) { klbr_mb_summary("arcade round change"); klbr_ci_summary("arcade round change"); klbr_dp_summary("arcade round change"); klbr_rp_summary("arcade round change"); klbr_af_summary("arcade round change"); klbr_df_summary("arcade round change"); }
            memset(&klbr_mb_c, 0, sizeof klbr_mb_c); memset(klbr_mb_sig, 0, sizeof klbr_mb_sig); memset(klbr_mb_dnext, 0, sizeof klbr_mb_dnext); memset(klbr_mb_t0, 0, sizeof klbr_mb_t0); memset(klbr_mb_asold, 0, sizeof klbr_mb_asold); klbr_ci_reset(); klbr_dp_reset(); klbr_rp_reset(); klbr_af_reset(); klbr_df_reset(); klbr_mb_ascan = 0;
            klbr_mb_arules = rules; klbr_mb_arc = 1;
            klog("brain: modeb data: Arcade round starts (read only sampling of the Traitor-marked Ally soldiers, else 2 controls): rules %08lx", (unsigned long)rules);
        } else if (!arc && klbr_mb_arc) {
            klbr_mb_summary("arcade round end"); klbr_ci_summary("arcade round end"); klbr_dp_summary("arcade round end"); klbr_rp_summary("arcade round end"); klbr_af_summary("arcade round end"); klbr_df_summary("arcade round end"); klbr_mb_arc = 0; klbr_mb_arules = 0;
            memset(&klbr_mb_c, 0, sizeof klbr_mb_c); memset(klbr_mb_sig, 0, sizeof klbr_mb_sig); memset(klbr_mb_dnext, 0, sizeof klbr_mb_dnext); memset(klbr_mb_t0, 0, sizeof klbr_mb_t0); memset(klbr_mb_asold, 0, sizeof klbr_mb_asold); klbr_ci_reset(); klbr_dp_reset(); klbr_rp_reset(); klbr_af_reset(); klbr_df_reset();
        }
        if (arc && (!klbr_mb_ascan || now - klbr_mb_ascan >= 3000u)) { __try { klbr_mb_arc_scan(now, rules); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_mb_flt++; } }
    }
    klbr_mb_sample(now);
    for (i = 0; i < KLBR_MAX; i++) {
        float bp[3], d, pt[3];
        if (!klbr_mb_t0[i]) continue;
        if (!kbr_mb_inwin(now, klbr_mb_t0[i], KLBR_MB_WINMS)) {
            klog("brain: modeb dist end: bot %d window over: distance at the RunChild %.1f, minimum %.1f", i, (double)klbr_mb_d0[i], (double)klbr_mb_dmin[i]);
            klbr_mb_t0[i] = 0; continue;
        }
        if (!kbr_mb_due(now, klbr_mb_next[i])) continue;
        klbr_mb_next[i] = now + KLBR_MB_STEPMS;
        if (klbr_mb_c.dist >= 200) continue;
        __try {
            if ((klbr_f6_body[i] > 0xffff || klbr_mb_arc) && klh_rd((klbr_f6_body[i] > 0xffff ? klbr_f6_body[i] : klh_rd32(klbr_mb_src(i) + 0x40)) + 0x460, bp, 12) && kle_ok3(bp)) {
                memcpy(pt, klbr_mb_pt[i], 12); d = kbr_f6_dist(bp, pt); klbr_mb_c.dist++;
                if (klbr_mb_dmin[i] < 0.0f || d < klbr_mb_dmin[i]) klbr_mb_dmin[i] = d;
                klog("brain: modeb dist: bot %d t+%lu ms distance to the RunChild point %.1f (at the RunChild %.1f)", i, (unsigned long)(now - klbr_mb_t0[i]), (double)d, (double)klbr_mb_d0[i]);
            }
        } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_f6_flt++; klbr_mb_flt++; }
    }
}
static void klbr_mb_summary(const char *why)
{
    KLBR_MBC *c = &klbr_mb_c;
    if (!klbr_mbon) return;
    if (c->dsamp) klog("brain: modeb data %s: samples %ld, 'atk current' ([S+0x74] == attack goal) %ld, atk state hist 0..4 = %ld %ld %ld %ld %ld (other value %ld, no goal %ld), nocl(4fc) set %ld, transitions %ld, lines logged %ld", why, c->dsamp, c->datk, c->ahist[0], c->ahist[1], c->ahist[2], c->ahist[3], c->ahist[4], c->aother, c->anull, c->dnocl, c->dtrans, c->dlog);
    if (c->d2samp) {
        char ov[200]; int k, nv = 0; ov[0] = 0;
        for (k = 0; k < 8; k++) if (c->ovtk[k] && nv < (int)sizeof ov - 24) nv += _snprintf(ov + nv, sizeof ov - nv, " %08lx x%ld", (unsigned long)c->ovtk[k], c->ovtn[k]);
        klog("brain: modeb data2 %s (%s): samples %ld; current-goal vtable none %ld ZSoldierAttack %ld ZAttackTarget %ld other %ld (other vtables:%s%s); mode [S+0x88] hist 0..4 = %ld %ld %ld %ld %ld, other %ld; goal held by slot Attack638 %ld Idle634 %ld Defend648 %ld StayInCover65c %ld Follow63c %ld AttackTarget658 %ld CoverFire654 %ld RunTask56c %ld slot5ac %ld none-of-those %ld",
             why, klbr_mb_arc ? "arcade" : "online", c->d2samp, c->vth[0], c->vth[1], c->vth[2], c->vth[3], nv ? ov : " -", c->ovtfull ? " (table full, more not listed)" : "", c->modeh[0], c->modeh[1], c->modeh[2], c->modeh[3], c->modeh[4], c->modeh[5],
             c->holdh[0], c->holdh[1], c->holdh[2], c->holdh[3], c->holdh[4], c->holdh[5], c->holdh[6], c->holdh[7], c->holdh[8], c->holdh[9]);
    }
    if (!c->s83[0] && !c->s83[1] && !c->s83[2] && !c->s83[3] && !c->s83[4] && !c->s83[5] && !c->ticks && !c->cand && !c->none && !c->runchild && !c->rearm) return;
    klog("brain: modeb %s: slot83 create=%ld retarget=%ld store720=%ld ticks=%ld cand=%ld clear0=%ld clearN=%ld none=%ld runchild=%ld rearm=%ld (slot83 cover0=%ld other=%ld unknown=%ld; candidate-count-sum=%ld notclear=%ld none-with-0-candidates=%ld rearm-within-10s-of-runchild=%ld; sites installed %d of %d; faults %d, shared %d)",
         why, c->s83[3], c->s83[4], c->s83[2], c->ticks, c->cand, c->clear0, c->clearN, c->none, c->runchild, c->rearm, c->s83[1], c->s83[0], c->s83[5], c->candsum, c->notclear, c->none0, c->rearm_win, klbr_mb_nok, KLBR_MB_NSITE, klbr_mb_flt, klbr_f6_flt);
}
static void klbr_f6_install(void)      /* once (game thread); a refusal is final for the run */
{
    int s, ok = 0, nwant = klbr_f7on ? KLBR_F6_NSITE_ALL : KLBR_F6_NSITE; BYTE cur[8], jmp[8]; DWORD stub;
    if (klbr_f6_state) return;
    klbr_f6_state = -1;
    if (!klbr_f6_stub && !(klbr_f6_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("brain: traitor fireprobe6: no memory for the stubs: off"); return; }
    for (s = 0; s < nwant; s++) {
        const KLBR_F6SITE *k = &klbr_f6_sites[s]; BYTE *at = KLH_VA(k->site); int n;
        memset(cur, 0, sizeof cur);
        if (klh_is_hashed(k->site, k->len)) { klog("brain: traitor fireprobe6: site %d 0x%x is inside a hashed range: NOT installed", k->id, (unsigned)k->site); continue; }
        if (!klh_rd((DWORD_PTR)at, cur, k->len) || memcmp(cur, k->b, k->len)) { klog("brain: traitor fireprobe6: site %d 0x%x bytes differ from the expected %d (got %02x %02x %02x %02x %02x %02x %02x): NOT installed", k->id, (unsigned)k->site, k->len, cur[0], cur[1], cur[2], cur[3], cur[4], cur[5], cur[6]); continue; }
        stub = (DWORD)(DWORD_PTR)(klbr_f6_stub + s * 0x40);
        n = kbr_f3_emit(klbr_f6_stub + s * 0x40, stub, k->id, (DWORD)(DWORD_PTR)klbr_f6_hit, k->b, k->len, (DWORD)(DWORD_PTR)(at + k->len));
        if (!n) { klog("brain: traitor fireprobe6: site %d: stub not built", k->id); continue; }
        kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, k->len);
        if (klh_poke(at, k->b, k->len, jmp, k->len, "brain: FireProbe6 counting detour")) { ok++; if (k->id == 8) klbr_f7_site8 = 1; klog("brain: traitor fireprobe6: site %d 0x%x (%d bytes stolen) installed, stub %d bytes", k->id, (unsigned)k->site, k->len, n); }
        else klog("brain: traitor fireprobe6: site %d 0x%x NOT installed (refused by the patch guard - a SHIP build writes no code - or the bytes differ)", k->id, (unsigned)k->site);
    }
    klbr_f6_state = ok == nwant ? 1 : ok ? 2 : -1;
    klog("brain: traitor fireprobe6: %d of %d sites installed (FireProbe6 %d, FireProbe7 %d, RayAim %d)", ok, nwant, klbr_f6on, klbr_f7on, klbr_raon);
}
static void klbr_f6_track(struct klbr_s *e, DWORD self)      /* every slot-113 call of a bot (game thread): a marked traitor's body / item / holder (read only) */
{
    int ix; DWORD F;
    if (!klbr_f6act || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    if (e->state != 1 || !e->traitor) { klbr_f6_body[ix] = klbr_f6_item[ix] = klbr_f6_hold[ix] = klbr_f6_sold[ix] = 0; klbr_f7_aim_n[ix] = 0; klbr_f7_aim_t[ix] = klbr_f7_aim_tg[ix] = 0; return; }
    klbr_f6_sold[ix] = self;
    klbr_f6_body[ix] = klh_rd32(self + 0x40); if (klbr_f6_body[ix] <= 0xffff) klbr_f6_body[ix] = 0;
    F = klh_rd32(self + 0x6a0); klbr_f6_item[ix] = F > 0xffff ? klh_rd32(F + 4) : 0;
    klbr_f6_hold[ix] = klh_rd32(self + 0xac);      /* the holder the FireProbe lines use ([soldier+0xac]) */
}
static void klbr_f6_summary(const char *why)
{
    int n, m;
    klbr_f7_summary(why); klbr_ra_summary(why); klbr_f8_summary(why); klbr_mb_summary(why); klbr_ci_summary(why); klbr_dp_summary(why); klbr_rp_summary(why); klbr_af_summary(why); klbr_df_summary(why); klbr_cb_summary(why); klbr_hs_summary(why);
    if (!klbr_f6on) return;
    for (n = 0; n < 2; n++) for (m = 0; m < 2; m++) {
        KLBR_F6C *c = &klbr_f6_c[n][m];
        if (!c->shots) continue;
        klog("brain: traitor fireprobe6 %s: networked %s %s shooters (sites %s): shots %ld (muzzle path bl=1 %ld); 0x7cb080 branch (bl=1 shots only; bl=0, not via vt+0x250: %ld) A0 %ld A1 %ld A2 %ld B %ld C(identity fallback) %ld, outputs identity+zero %ld; passed the gate %ld (0x4a30e0 null %ld); ray %ld (entity null %ld, hit %ld, hit = the human %ld, another player %ld), projectile %ld, passed but neither ray nor projectile %ld; "
             "error buckets (<5 <15 <45 >=45 unknown) matrix-row vs human %ld %ld %ld %ld %ld, ray A %ld %ld %ld %ld %ld, ray B %ld %ld %ld %ld %ld; faults %d",
             why, n ? "yes" : "no", m ? "MARKED" : "other", klbr_f6_state == 1 ? "all" : klbr_f6_state == 2 ? "partial" : "none", c->shots, c->forced, c->br[0], c->br[1], c->br[2], c->br[3], c->br[4], c->br[5], c->ident, c->pass, c->d0, c->ray, c->rnull, c->rhit, c->rhuman, c->rplayer, c->proj, c->pass - c->ray - c->proj,
             c->rowb[0], c->rowb[1], c->rowb[2], c->rowb[3], c->rowb[4], c->rayAb[0], c->rayAb[1], c->rayAb[2], c->rayAb[3], c->rayAb[4], c->rayBb[0], c->rayBb[1], c->rayBb[2], c->rayBb[3], c->rayBb[4], klbr_f6_flt);
    }
}
static long klbr_f6_total(void) { int n, m; long t = 0; for (n = 0; n < 2; n++) for (m = 0; m < 2; m++) t += klbr_f6_c[n][m].shots; return t; }
static void klbr_f6_round_end(void)      /* round end (klbr_fp_summary): the totals, then the counters cleared (the detours stay in) */
{
    klbr_f6_summary("round");
    memset(klbr_f6_c, 0, sizeof klbr_f6_c); memset(klbr_f6_body, 0, sizeof klbr_f6_body); memset(klbr_f6_item, 0, sizeof klbr_f6_item); memset(klbr_f6_hold, 0, sizeof klbr_f6_hold); memset(klbr_f6_sold, 0, sizeof klbr_f6_sold); memset(&klbr_f7_c, 0, sizeof klbr_f7_c); memset(klbr_f7_aim_n, 0, sizeof klbr_f7_aim_n); memset(klbr_f7_aim_t, 0, sizeof klbr_f7_aim_t); memset(klbr_f7_aim_tg, 0, sizeof klbr_f7_aim_tg); memset(&klbr_ra_c, 0, sizeof klbr_ra_c); memset(&klbr_f8_c, 0, sizeof klbr_f8_c); memset(klbr_f8_hand, 0, sizeof klbr_f8_hand); klbr_f8_lastmark = 0; memset(&klbr_mb_c, 0, sizeof klbr_mb_c); memset(klbr_mb_sig, 0, sizeof klbr_mb_sig); memset(klbr_mb_dnext, 0, sizeof klbr_mb_dnext); memset(klbr_mb_t0, 0, sizeof klbr_mb_t0); memset(klbr_mb_asold, 0, sizeof klbr_mb_asold); klbr_ci_reset(); klbr_dp_reset(); klbr_rp_reset(); klbr_af_reset(); klbr_df_reset(); klbr_f7_cur.valid = 0; klbr_f6_cur.valid = 0; klbr_f6_lastshots = 0; klbr_cb_reset(); klbr_hs_reset();
}
static void klbr_f6_tick(int game_thread, DWORD now)      /* klbr_tick, before the host-round gate (so Arcade is covered): install once, a running total every 30 s when shots were seen */
{
    long t;
    if (!klbr_f6act || !game_thread || !klh_exe_ok) return;
    klbr_f6_tid = GetCurrentThreadId();
    if (!klbr_f6_state && (klbr_f6on || klbr_f7on || klbr_raon || klbr_f8on || klbr_mbon || klbr_cion || klbr_dpon)) klbr_f6_install();      /* AfcProbe alone installs nothing (no detour) */
    if (klbr_f8on && !klbr_f8_state) klbr_f8_install();
    if (klbr_mbon && !klbr_mb_state) klbr_mb_install();
    if (klbr_cion && !klbr_ci_state) klbr_ci_install(); if (klbr_dpon && !klbr_dp_state) klbr_dp_install(); if (klbr_rpon && !klbr_rp_state) klbr_rp_install();
    klbr_mb_tick(now);
    if (now - klbr_f6_last < 30000u) return;
    klbr_f6_last = now;
    t = klbr_f6_total();
    if (t != (long)klbr_f6_lastshots) { klbr_f6_lastshots = (DWORD)t; klbr_f6_summary("running total"); }
}
/* OnlineBrainTraitorWeaponReady (11-03, workflow wdntba8eu; UNTESTED, recommended off, CHANGES behaviour; needs AttackHandle; host only). For a MARKED bot after every slot-113 call: byte [body+0x5c8] != 0 (SKIP1 of the
   shooting task would loop forever), [body+0x860] == 0, [body+0x70] != 0 and [s+0x6a0] != 0 (weapon controller present) -> write byte 0 through klh_data. NOT restored on purpose: the game's own SelectWeapon 0x511450
   clears the byte on a real weapon switch anyway, so 0 is the state the game reaches by itself; a pre-installed weapon (vt+0x6b8) just never got that switch. The gate offsets are GUESS (workflow trace, not re-disassembled here).
   Log: first 5 writes per round and a "brain: traitor weaponready:" round total with the gate-failure counts. */
static int klbr_wron; static long klbr_wr_clr, klbr_wr_already, klbr_wr_g860, klbr_wr_g70, klbr_wr_g6a0, klbr_wr_nobody, klbr_wr_refused;
static void klbr_wr_apply(struct klbr_s *e, DWORD self)      /* game thread, after every slot-113 call of a bot (host only) */
{
    DWORD body; BYTE b = 0, zero = 0; int ix;
    if (!klbr_wron || !klbr_cfh || !e || (ix = (int)(e - klbr_t)) < 0 || ix >= KLBR_MAX) return;
    if (e->state != 1 || !e->traitor) return;      /* marked bots only (not counted) */
    body = klh_rd32(self + 0x40);
    if (body <= 0xffff || !klh_rd(body + 0x5c8, &b, 1)) { klbr_wr_nobody++; return; }
    if (!b) { klbr_wr_already++; return; }
    if (klh_rd32(body + 0x860) != 0) { klbr_wr_g860++; return; }
    if (klh_rd32(body + 0x70) == 0) { klbr_wr_g70++; return; }
    if (klh_rd32(self + 0x6a0) == 0) { klbr_wr_g6a0++; return; }
    if (!klh_data((void *)(DWORD_PTR)(body + 0x5c8), &zero, 1, "brain: weapon-ready byte of a marked bot (OnlineBrainTraitorWeaponReady)")) { if (klbr_wr_refused++ < 5) klog("brain: traitor weaponready: bot %d body %08lx: the +0x5c8 write was refused", ix, (unsigned long)body); return; }
    klbr_wr_clr++;
    if (klbr_wr_clr <= 5) klog("brain: traitor weaponready: bot %d body %08lx [body+0x5c8] %02x -> 0 ([body+0x860] 0, [body+0x70] %08lx, [s+0x6a0] %08lx, body vt %08lx)", ix, (unsigned long)body, (unsigned)b, (unsigned long)klh_rd32(body + 0x70), (unsigned long)klh_rd32(self + 0x6a0), (unsigned long)klh_rd32(body));
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
    klbr_f3_track(ix, self, run);      /* OnlineBrainTraitorFireProbe3: controller / run-task bookkeeping for the detours (read only) */
    klbr_fp[ix].calls++; if (!klbr_fp[ix].t0) klbr_fp[ix].t0 = now;
    /* shot counter (0x6c81a0 adds to [body+0x550]) and the [s+0x550] reading: first / latest value per round */
    body = klh_rd32(self + 0x40); klbr_f5_track(ix, self, body);      /* OnlineBrainTraitorFireProbe5 (no-op unless on) */
    { DWORD sc = body > 0xffff ? klh_rd32(body + 0x550) : 0, bs = klh_rd32(self + 0x550); if (body > 0xffff) { if (!klbr_fp[ix].shv) { klbr_fp[ix].shv = 1; klbr_fp[ix].s0 = sc; klbr_fp[ix].bs0 = bs; } klbr_fp[ix].sl = sc; klbr_fp[ix].bsl = bs; } }
    if (body > 0xffff) { BYTE c5 = 0xff; if (klh_rd(body + 0x5c8, &c5, 1)) { if (c5) klbr_fp[ix].c5nz++; else klbr_fp[ix].c5z++; } }      /* every slot-113 call: byte [body+0x5c8] zero / nonzero (SKIP1 of the shooting task) */
    if (run) {
        klbr_fp[ix].rcalls++;
        if (run != klbr_fp[ix].rt && klbr_fp[ix].rt) klbr_fp_epend(ix, "replaced by another task");      /* no empty call in between: close the old episode before the new one starts */
        { DWORD c0 = klh_rd32(run + 0xc), ch = c0 > 0xffff ? klh_rd32(c0 + 0x50) : 0; if (ch > 0xffff && klh_pvt(ch) == KLBR_FP_FIRE_VT) { klbr_fp[ix].chcalls++; if (!klbr_fp[ix].chf) { klbr_fp[ix].chf = 1; klbr_fp[ix].cheps++; } } }      /* the run task's child [[run+0xc]+0x50] (RunChild 0x521350, VERIFIED) is a ZFireWeaponTask */
        if (run != klbr_fp[ix].rt) { klbr_fp[ix].rt = run; klbr_fp[ix].rf = now; klbr_fp[ix].eps++; klbr_fp[ix].ff = 0; klbr_fp[ix].e0 = klbr_fp[ix].sl; { DWORD a = klh_rd32(self + 0x658); klbr_fp[ix].atk = (a > 0xffff && klh_pvt(a) == KLBR_FP_ZAT_VT && klh_rd32(self + 0x74) == a); } if (klbr_fp[ix].eps <= KLBR_FP_LOGMAX) klbr_fp_epstart(ix, e, run); }
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
    klbr_fp_ext2(ix, self, body);
    klbr_f3_sample(ix, e, self, body);      /* OnlineBrainTraitorFireProbe3 (no-op unless on) */
    klbr_f4_sample(ix, e, self, body);      /* OnlineBrainTraitorFireProbe4 (no-op unless on) */
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
    klbr_f3_summary();      /* OnlineBrainTraitorFireProbe3 round counts (before klbr_fp is cleared below) */
    klbr_f4_summary();      /* OnlineBrainTraitorFireProbe4 round total */
    klbr_f5_summary();      /* OnlineBrainTraitorFireProbe5 round counts */
    klbr_gf_summary();      /* OnlineBrainTraitorGateForce round counts */
    klbr_f6_round_end();      /* OnlineBrainTraitorFireProbe6 round counts */
    if (klbr_tbon) klog("brain: traitor traitorbyte: round total: byte set %ld, restored %ld, not restored (body gone / byte changed / refused) %ld, re-set after a reset %ld, slot-113 calls: byte already nonzero %ld, with a ZFFActor body (not applicable) %ld, other class %ld; refused writes %ld", klbr_tb_set, klbr_tb_rest, klbr_tb_lost, klbr_tb_reset, klbr_tb_have, klbr_tb_actor, klbr_tb_other, klbr_tb_refused);
    klbr_tb_set = klbr_tb_reset = klbr_tb_rest = klbr_tb_lost = klbr_tb_have = klbr_tb_actor = klbr_tb_other = klbr_tb_refused = 0; klbr_tb_told = 0; memset(klbr_tb, 0, sizeof klbr_tb);
    if (klbr_fpon) for (i = 0; i < KLBR_MAX; i++) if (klbr_fp[i].calls)
        klog("brain: traitor fireprobe: round total: bot %d slot-113 calls %ld, with ZRunToPosShootingTask %ld (%ld episodes, longest %lu ms), with ZFireWeaponTask %ld (%ld episodes)%s", i, klbr_fp[i].calls, klbr_fp[i].rcalls, klbr_fp[i].eps, (unsigned long)klbr_fp[i].maxep, klbr_fp[i].fcalls, klbr_fp[i].fireeps, klbr_fp[i].fcalls ? "" : " (ZFireWeaponTask never on the stack)");
    if (klbr_fpon) for (i = 0; i < KLBR_MAX; i++) if (klbr_fp[i].rt) klog("brain: traitor fireprobe: bot %d episode still open at round end: ZRunToPosShootingTask %08lx, ZFireWeaponTask on the stack %s", i, (unsigned long)klbr_fp[i].rt, klbr_fp[i].ff ? "yes" : "no");
    if (klbr_fpon) for (i = 0; i < KLBR_MAX; i++) if (klbr_fp[i].shv)
        klog("brain: traitor fireprobe: round total: bot %d shots [body+0x550] %lu -> %lu (+%ld in the round, +%ld inside closed ZRunToPosShootingTask episodes; [s+0x550] %lu -> %lu), ZFireWeaponTask seen as the run task's child on %ld calls (%ld episodes)%s", i,
            (unsigned long)klbr_fp[i].s0, (unsigned long)klbr_fp[i].sl, (long)(klbr_fp[i].sl - klbr_fp[i].s0), klbr_fp[i].shep, (unsigned long)klbr_fp[i].bs0, (unsigned long)klbr_fp[i].bsl, klbr_fp[i].chcalls, klbr_fp[i].cheps, klbr_fp[i].sl == klbr_fp[i].s0 ? " (the shot counter never moved)" : "");
    if (klbr_fpon) for (i = 0; i < KLBR_MAX; i++) if (klbr_fp[i].c5z || klbr_fp[i].c5nz)
        klog("brain: traitor fireprobe: round total: bot %d slot-113 calls with byte [body+0x5c8] == 0: %ld, != 0: %ld%s", i, klbr_fp[i].c5z, klbr_fp[i].c5nz, klbr_fp[i].c5z ? "" : " (never zero: SKIP1 of the shooting task never opens, unless mode 6)");
    if (klbr_fpon) klog("brain: traitor fireprobe: round total: faults %d", klbr_fp_flt);
    if (klbr_wron) klog("brain: traitor weaponready: round total: [body+0x5c8] cleared %ld; skipped: already 0 %ld, [body+0x860] != 0 %ld, [body+0x70] == 0 %ld, [s+0x6a0] == 0 %ld, no readable body %ld; refused writes %ld", klbr_wr_clr, klbr_wr_already, klbr_wr_g860, klbr_wr_g70, klbr_wr_g6a0, klbr_wr_nobody, klbr_wr_refused);
    klbr_wr_clr = klbr_wr_already = klbr_wr_g860 = klbr_wr_g70 = klbr_wr_g6a0 = klbr_wr_nobody = klbr_wr_refused = 0;
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
    klbr_gf_apply(e, self);     /* OnlineBrainTraitorGateForce: the marked body set + the one-time slot wrap */
    klbr_f6_track(e, self);     /* OnlineBrainTraitorFireProbe6: the marked body / item / holder (read only) */
    klbr_wr_apply(e, self);     /* OnlineBrainTraitorWeaponReady: after the probe, so the probe shows the game's own [body+0x5c8] */
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
    if (klbr_loson) { int j; long tc = 0, tb = 0, te = 0; for (j = 0; j < KLBR_MAX; j++) { tc += klbr_los_n[j][0]; tb += klbr_los_n[j][1]; te += klbr_los_n[j][2]; }
        klog("brain: traitor losgate: round total: clear=%ld blocked=%ld err=%ld (cached answers %ld); Sense skipped %ld blocked human(s), HolderFix skipped %ld; physics faults %d", tc, tb, te, klbr_los_cache, klbr_los_skip_sn, klbr_los_skip_hx, klbr_los_flt);
        for (j = 0; j < KLBR_MAX; j++) if (klbr_los_n[j][0] || klbr_los_n[j][1] || klbr_los_n[j][2]) klog("brain: traitor losgate: bot %d clear=%ld blocked=%ld err=%ld", j, klbr_los_n[j][0], klbr_los_n[j][1], klbr_los_n[j][2]);
        memset(klbr_los_n, 0, sizeof klbr_los_n); memset(klbr_los_ca_at, 0, sizeof klbr_los_ca_at); memset(klbr_los_ca_h, 0, sizeof klbr_los_ca_h); klbr_los_skip_sn = klbr_los_skip_hx = klbr_los_cache = 0; klbr_los_nlog = 0; }
    klbr_los_ctl_done = 0;
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
    klbr_sn_unfeed(i, snd); klbr_ta[i].snd = 0; klbr_ta[i].rec = 0; klbr_ta[i].nlog[0] = klbr_ta[i].nlog[1] = 0; klbr_sn_at[i] = 0; klbr_cl[i].lat = 0; klbr_cb_pass[i].at = 0; klbr_cb_next[i] = 0; klbr_cb_set[i] = 0; klbr_cb_set6[i] = 0;      /* OnlineBrainTraitorSense: feeding stops with the wrap */
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
static void klbr_cb_restore6(int i, DWORD S, DWORD d6)      /* mode 3: [S+0x6fc] back to 0, only if WE set it and it is still 1 (a changed byte is a stock write: left alone); d6 = the dword read this tick */
{
    if (!klbr_cb_set6[i]) return;
    klbr_cb_set6[i] = 0;
    if ((d6 & 0xffu) != 1) return;
    __try { *(volatile BYTE *)(DWORD_PTR)(S + 0x6fc) = 0; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_cb_flt++; klog("brain: combatflag: fault at the 6fc undo (%d of 3 allowed)", klbr_cb_flt); return; }
    klbr_cb_r6++;
}
static void klbr_cb_apply(int i, DWORD now)      /* OnlineBrainTraitorCombatFlag: game thread, depth 0, bot i is wrapped and alive (the pump just checked); the one game write is the byte [S+0x4fc] = 1 */
{
    DWORD S = klbr_ta[i].snd, d6 = 0, fb0 = 0; BYTE b4 = 0; int dec, fresh;
    if (!klbr_cbmode || klbr_cb_flt >= 3 || S <= 0xffff) return;
    if (!klbr_loson || !klbr_snon) { if (!klbr_cb_nolog) { klbr_cb_nolog = 1; klog("brain: combatflag: needs OnlineBrainTraitorLosGate=1 and OnlineBrainTraitorSense=1 (LosGate %d, Sense %d): nothing is written", klbr_loson, klbr_snon); } return; }
    if (klbr_cb_next[i] && !kbr_mb_due(now, klbr_cb_next[i])) return;
    klbr_cb_next[i] = now + 250; if (!klbr_cb_next[i]) klbr_cb_next[i] = 1;
    fresh = klbr_cb_pass[i].at && (int)(now - klbr_cb_pass[i].at) <= 2 * klbr_snms + 1000;      /* signed: the record stamp is now|1, up to 1 ms ahead */
    __try { klh_rd(S + 0x4fc, &b4, 1); d6 = klh_rd32(S + 0x6fc); } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_cb_flt++; return; }
    dec = kbr_cb_decide(klbr_cbmode, 1, fresh, klbr_cb_pass[i].blocked, klbr_cb_pass[i].open, (d6 & 0xffu) != 0, b4 != 0);
    if (dec == 1 || dec == 2) klbr_cb_restore6(i, S, d6);      /* mode 3: no longer eligible (stale pass / nobody blocked) or a human is clear: put back the 6fc byte WE wrote */
    if (dec == 1) { klbr_cb_sk_nopass++; return; }
    if (dec == 2) {      /* a human is clear again: give the stock firing clause (needs [S+0x4fc] == 0) back its state, but only the byte WE wrote (it was 0 before) */
        klbr_cb_sk_clear++;
        if (klbr_cb_set[i] && b4) { __try { *(volatile BYTE *)(DWORD_PTR)(S + 0x4fc) = 0; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_cb_flt++; klog("brain: combatflag: fault at the undo (%d of 3 allowed)", klbr_cb_flt); } klbr_cb_undo++; }
        klbr_cb_set[i] = 0; return;
    }
    if (dec == 3) { klbr_cb_sk_6fc++; return; }
    if (dec == 4) { klbr_cb_already++; return; }
    if (dec != 0) return;
    if (klbr_cbmode == 3) {      /* 6fc: set to 1 only when it is 0 (then remembered as ours); a nonzero byte is a stock write and is never touched */
        if (!(d6 & 0xffu)) { __try { *(volatile BYTE *)(DWORD_PTR)(S + 0x6fc) = 1; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_cb_flt++; klog("brain: combatflag: fault at the 6fc write (%d of 3 allowed)", klbr_cb_flt); return; } klbr_cb_set6[i] = 1; klbr_cb_w6++; }
        else if (!klbr_cb_set6[i]) klbr_cb_nz6++;
        if (b4) return;      /* 4fc already 1 (ours or stock): only 6fc was missing */
    }
    __try { fb0 = klh_rd32(S + 0xb0); *(volatile BYTE *)(DWORD_PTR)(S + 0x4fc) = 1; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_cb_flt++; klog("brain: combatflag: fault at the write (%d of 3 allowed)", klbr_cb_flt); return; }
    klbr_cb_w++; klbr_cb_set[i] = 1; if (!fb0) klbr_cb_b0null++;
    if (!klbr_cb_first[i]) { klbr_cb_first[i] = 1; klog("brain: combatflag: bot %d S %08lx: [S+0x4fc] written 1 (all %d human(s) blocked, none open; [S+0x6fc] %08lx; [S+0xb0] %08lx%s); mode %d (UNTESTED)", i, (unsigned long)S, klbr_cb_pass[i].blocked, (unsigned long)d6, (unsigned long)fb0, fb0 ? "" : " NULL", klbr_cbmode); }
}
typedef DWORD (__fastcall *klbr_hs_handlefn)(DWORD ecx, DWORD edx);      /* 0x6ece90: thiscall ecx = entity, no stack args, plain ret */
typedef DWORD (__cdecl *klbr_hs_lookupfn)(DWORD handle);      /* 0x8ccde0: cdecl, one arg, plain ret */
typedef void (__fastcall *klbr_hs_setfn)(DWORD ecx, DWORD edx, DWORD handle, DWORD *flagsptr);      /* 0x8bd420: thiscall ecx = S+0xa8, two stack args, ret 8 (callee pops: same as __fastcall with the first two in ecx / edx) */
static void klbr_hs_apply(int i, DWORD now)      /* OnlineBrainTraitorHolderSet: game thread, depth 0, bot i is wrapped and alive (the pump just checked); the one game write is SetHolder on S+0xa8 */
{
    struct klbr_s *e = &klbr_t[i]; DWORD S = klbr_ta[i].snd, H = 0, handle, cur_h, cur_f, fl; float bp[3]; double dh = 0.0; int dec, alive = 0, fresh, have = 0;
    if (!klbr_hsmode || klbr_hs_flt >= 3 || S <= 0xffff) return;
    if (!klbr_loson || !klbr_snon) { if (!klbr_hs_nolog) { klbr_hs_nolog = 1; klog("brain: holderset: needs OnlineBrainTraitorLosGate=1 and OnlineBrainTraitorSense=1 (LosGate %d, Sense %d): nothing is written", klbr_loson, klbr_snon); } return; }
    if (klbr_hs_next[i] && !kbr_mb_due(now, klbr_hs_next[i])) return;
    klbr_hs_next[i] = now + 100; if (!klbr_hs_next[i]) klbr_hs_next[i] = 1;
    fresh = klbr_cb_pass[i].at && (int)(now - klbr_cb_pass[i].at) <= 2 * klbr_snms + 1000;
    if (fresh && klbr_cb_pass[i].blocked > 0 && klbr_cb_pass[i].open == 0) {      /* the human search is only worth its reads when the pass already allows a write */
        __try { have = klbr_bot_pos(e->actor, bp, &alive) && alive && klbr_human_near(bp, &dh, &H) && H > 0xffff; } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_hs_flt++; klog("brain: holderset: fault in the human search (%d of 3 allowed)", klbr_hs_flt); return; }
    }
    dec = kbr_hs_decide(klbr_hsmode, 1, fresh, klbr_cb_pass[i].blocked, klbr_cb_pass[i].open, have);
    if (dec == 1) { klbr_hs_nopass++; return; }
    if (dec == 2) { klbr_hs_sk_clear++; return; }      /* a human is clear: stop writing, do not clear (the stock scan / HolderFix take over) */
    if (dec == 3) { klbr_hs_nohuman++; return; }
    if (dec != 0) return;
    fl = kbr_hs_flags(klbr_hsmode);
    __try {
        handle = ((klbr_hs_handlefn)(DWORD_PTR)KLH_VA(0x6ece90))(H, 0);
        if (!handle || ((klbr_hs_lookupfn)(DWORD_PTR)KLH_VA(0x8ccde0))(handle) != H) { klbr_hs_mismatch++; return; }
        cur_h = klh_rd32(S + 0xb0); cur_f = klh_rd32(S + 0xa8);
        if (!kbr_hs_need(cur_h, cur_f, handle, fl)) { klbr_hs_kept++; return; }
        ((klbr_hs_setfn)(DWORD_PTR)KLH_VA(0x8bd420))(S + 0xa8, 0, handle, &fl);
    } __except (EXCEPTION_EXECUTE_HANDLER) { klbr_hs_flt++; klog("brain: holderset: fault at the lookup / SetHolder call (%d of 3 allowed)%s", klbr_hs_flt, klbr_hs_flt >= 3 ? "; off for the round" : ""); return; }
    klbr_hs_w++;
    if (!klbr_hs_first[i]) { klbr_hs_first[i] = 1; klog("brain: holderset: bot %d S %08lx: holder set to human %08lx (handle %08lx, flags 0x%lx, was handle %08lx flags %08lx; %d human(s) blocked, none open; nearest %.1f); mode %d (UNTESTED)", i, (unsigned long)S, (unsigned long)H, (unsigned long)handle, (unsigned long)fl, (unsigned long)cur_h, (unsigned long)cur_f, klbr_cb_pass[i].blocked, dh, klbr_hsmode); }
    else if (klbr_hs_w <= 40 && (klbr_hs_w % 8) == 0) klog("brain: holderset: bot %d: write #%ld (handle %08lx, flags 0x%lx, was handle %08lx flags %08lx)", i, klbr_hs_w, (unsigned long)handle, (unsigned long)fl, (unsigned long)cur_h, (unsigned long)cur_f);
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
            else { klbr_sense_feed(i, GetTickCount()); klbr_cb_apply(i, GetTickCount()); klbr_hs_apply(i, GetTickCount()); }      /* OnlineBrainTraitorSense (off unless set), then OnlineBrainTraitorCombatFlag, then OnlineBrainTraitorHolderSet */
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
/* BoardProbe (log only): while the vehicle waits (state 3 / 4), one line per second per loyal bot that is not aboard yet, 80 lines per round. Fields: actor / rec, stage byte [rec+0x78], vehicle state, vehicle timer
   [rules+0x1d8] (read live from the real rules), the last Board evaluate answer of this bot and its age (wrapper stamp, e->bLast), metres to the boarding node (-1 = unreadable) and the bot's current AI goal:
   [S+0x74] pointer plus its RTTI name through klbr_f8_rtti (both offsets are the ones klbr_nb_lines_pump already reads; no new offset). The goal id is the pointer, NOT a numeric order id: no numeric order id is read anywhere in the existing code (omitted). */
static void klbr_bp_bots(DWORD now)
{
    int i; float timer = -1.0f; DWORD G, real;
    if (!klbr_bprobe || (klbr_van != 3 && klbr_van != 4)) return;
    if (klbr_vis != klbr_bp_lvis) { klbr_bp_lvis = klbr_vis; klbr_bp_lines = 0; }      /* 80 lines per vehicle VISIT (a short visit 1 must not starve visit 2) */
    if (!kbr_bp_cap_ok(klbr_bp_lines, 80)) return;
    G =klh_rd32((DWORD_PTR)KLH_VA(KLBR_GLOBAL_G)); real = G > 0xffff ? klh_rd32(G + 0x54) : 0;
    if (real > 0xffff) { float t = 0.0f; if (klh_rd(real + 0x1d8, &t, 4)) timer = t; }
    for (i = 0; i < KLBR_MAX && i < 16 && kbr_bp_cap_ok(klbr_bp_lines, 80); i++) {
        struct klbr_s *e = &klbr_t[i]; float p[3]; int alive = 0, ab = 0; long ty = 0; DWORD S = e->snd, cur = 0; char gn[32]; float dn = -1.0f;
        if (e->state != 1 || e->rec <= 0 || !kbr_bp_bot_due(now, e->bpAt, 1000u)) continue;
        if (!klbf_ob_ledger(e->actor, &ab, &ty)) ab = 0;      /* untracked bots count as not aboard */
        if (!kbr_bp_bot_wanted(klbr_van, e->traitor, ab)) continue;
        e->bpAt = now | 1u; klbr_bp_lines++;
        gn[0] = 0;
        if (S > 0xffff) { cur = klh_rd32(S + 0x74); if (cur > 0xffff) klbr_f8_rtti(cur, gn, sizeof gn); }
        if (!gn[0]) _snprintf(gn, sizeof gn, cur > 0xffff ? "?" : "none"); gn[sizeof gn - 1] = 0;
        if (klbr_bot_pos(e->actor, p, &alive) && klbr_bn_ok) dn = kle_dist(p, klbr_bn_pos) / 100;
        klog("brain: boardprobe: bot %08lx rec %d stage %u (prev %d, changed %ld ms ago; -1 = no change seen) van %d visit %d timer %.1f s board-eval last %s%.3f age %ld ms node %.1f m goal %08lx %s", (unsigned long)e->actor, e->rec, (unsigned)KLBR_PB(KLBR_REC(e->rec) + 0x78),
             e->bStgPrev - 1, e->bStgAt ? (long)(now - (e->bStgAt & ~1u)) : -1L, klbr_van, klbr_vis, (double)timer,
             e->bLastAt ? "" : "never ", (double)e->bLast, e->bLastAt ? (long)(now - (e->bLastAt & ~1u)) : -1L, (double)dn, (unsigned long)cur, gn);
    }
}
/* OnlineBrainTraitorNoBoard / RunProbe: a read-only line per marked bot per second, 120 lines per round (re/traitor_board_1104.md Q4 + verifier additions). Game thread, outside any AI frame (called from klbr_pump). Every game read is guarded.
   Fields: stage [rec+0x78] and rec10 [rec+0x10] (BYTE width GUESS), the ledger phase / aboard (klbotfill.c), the van state, the Defend child ([goal+0x14] RTTI when the current goal [S+0x74] is the Defend goal [S+0x648], else '-'; GUESS that
   [goal+0x14] is not stale, the verifier doubted it), the ZCloseIn eval counter delta since the last line (needs the CloseInProbe sites, else n/a; GUESS that the klbr_ci_b index is the klbr_t slot) and the distance to the nearest human. */
static void klbr_nb_lines_pump(DWORD now)
{
    int i;
    if ((klbr_nbmode < 1 && !klbr_rpon) || klbr_nb_lines >= 120) return;
    for (i = 0; i < KLBR_MAX && klbr_nb_lines < 120; i++) {
        struct klbr_s *e = &klbr_t[i]; float p[3]; int alive = 0, ph, ab = 0, havd = 0; long tl = 0, dev = -1; double dh = -1.0; DWORD S = e->snd, cur = 0, win = 0; BYTE st, r10; char wn[32], dtxt[16], etxt[16];
        if (e->state != 1 || e->rec <= 0 || !e->traitor || (klbr_nb_at[i] && now - klbr_nb_at[i] < 1000u)) continue;
        if (!klbr_bot_pos(e->actor, p, &alive) || !alive) continue;
        klbr_nb_at[i] = now | 1u; klbr_nb_lines++;
        st = KLBR_PB(KLBR_REC(e->rec) + 0x78); r10 = KLBR_PB(KLBR_REC(e->rec) + 0x10);
        ph = klbf_ob_ledger(e->actor, &ab, &tl) ? klbf_ob_phase(e->actor) : -1;
        wn[0] = 0;
        if (S > 0xffff) {
            __try { cur = klh_rd32(S + 0x74); if (cur > 0xffff && cur == klh_rd32(S + 0x648)) { win = klh_rd32(cur + 0x14); if (win > 0xffff) klbr_f8_rtti(win, wn, sizeof wn); else _snprintf(wn, sizeof wn, "none"); } } __except (EXCEPTION_EXECUTE_HANDLER) { wn[0] = 0; }
        }
        if (!wn[0]) _snprintf(wn, sizeof wn, cur > 0xffff ? "-" : "?"); wn[sizeof wn - 1] = 0;
        if (klbr_cion && klbr_ci_state > 0) { dev = klbr_ci_b[i].ev - klbr_nb_ev0[i]; klbr_nb_ev0[i] = klbr_ci_b[i].ev; }
        havd = klbr_human_near(p, &dh, 0);
        if (dev >= 0) _snprintf(etxt, sizeof etxt, "%ld", dev); else _snprintf(etxt, sizeof etxt, "n/a"); etxt[sizeof etxt - 1] = 0;
        if (havd) _snprintf(dtxt, sizeof dtxt, "%.1f m", dh / 100); else _snprintf(dtxt, sizeof dtxt, "none"); dtxt[sizeof dtxt - 1] = 0;
        klog("brain: traitor board: rec %d stage [rec+0x78] %u rec10 [rec+0x10] %u ledger phase %d aboard %d van %d defend-child %s closein-eval-delta %s dist-to-nearest-human %s", e->rec, (unsigned)st, (unsigned)r10, ph, ab, klbr_van, wn, etxt, dtxt);
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
        if (e->state == 1 && klbr_boardreal && !klbr_turned_actor(e->actor) && !(kbr_nb_skip(klbr_nbmode, 2, klbr_taon, klbr_trturn, klbr_nb_slot(e->actor) >= 0) && (klbr_nb_note(e->actor, 2, klbf_ob_phase(e->actor)), 1))) {      /* TraitorTurn: a turned bot does not board; OnlineBrainTraitorNoBoard 2: neither does a marked Arcade traitor (the real Board tactic may still walk it to the van) */
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
    if (klbr_bprobe) klbr_bp_bots(now);      /* BoardProbe: log only */
    klbr_nb_lines_pump(now);      /* OnlineBrainTraitorNoBoard / RunProbe: read only */
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
    klbr_nb_summary();      /* OnlineBrainTraitorNoBoard: the round's skips (silent unless on) */
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
        if (klbr_blog) klog("brain: round end: BoardLog: slot 45 calls for a bot not aboard yet %ld, repeats for an aboard bot %ld, stale ledger (aboard since an earlier vehicle visit) %ld (total %ld; %d visit(s))", klbr_bl_new, klbr_bl_rep, klbr_bl_stale, (long)klbr_s45_n, klbr_vis);
        if (klbr_s2gate || klbr_hlon) {
            long refused = klbr_trr_pass - klbr_trr_marks; if (refused < 0) refused = 0;
            klog("brain: round end: TraitorRoll: score passed on %ld evaluate(s) of unmarked bots, %ld mark(s), %ld pass(es) with no mark (roll refused, GUESS); first pass %s%ld s, first mark %s%ld s into the round (-1 = none); Stage2Gate %d, money fallback $%ld, MinS %ld, MaxS %ld",
                 klbr_trr_pass, klbr_trr_marks, refused, "+", klbr_trr_pass1 ? (long)((klbr_trr_pass1 - klbr_trr_t0) / 1000) : -1L, "+", klbr_trr_mark1 ? (long)((klbr_trr_mark1 - klbr_trr_t0) / 1000) : -1L, klbr_s2gate, klbr_s2money, klbr_s2min, klbr_s2max);
        }
        klbr_s2min_logged = klbr_s2max_logged = klbr_s2hold_logged = klbr_s2vrel_logged = 0;
        klbr_trr_pass = klbr_trr_marks = 0; klbr_trr_pass1 = klbr_trr_mark1 = 0; klbr_mk_last = 0; klbr_mkgap_logged = 0;
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
    klbr_f6_tick(game_thread, now);      /* OnlineBrainTraitorFireProbe6: installs once, running total every 30 s (also in Arcade) */
    if (!klbr_on || !game_thread || !klh_exe_ok || now - last < 1000) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) { klbr_tr_restore_all("the session is gone"); return; }
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if (role != 2 || mode != 4 || state != KLB_ROUND) {      /* HOST Fragile Alliance round only; a client / other mode / lobby does nothing */
        klbr_tr_restore_all("the round is not running");      /* a team-1 actor must never outlive the round, and never the table that tracks it */
        if (klbr_sm_round && (state < KLB_ROUND || state >= 0x1f || role != 2)) { klbr_summary(); klbr_tr_restore_all("round end"); memset(klbr_t, 0, sizeof klbr_t); memset(klbr_tt, 0, sizeof klbr_tt); klbr_tt_turned = klbr_tt_back = klbr_tt_kills = klbr_tt_capped = klbr_tt_refused = klbr_dg0 = klbr_dg1 = 0; klbr_row0_which = -2; klbr_shadow_reset(); klbr_verdict_n = 0; klbr_vis = 0; klbr_bl_stale = klbr_bp_lines = 0; klbr_bp_lvis = 0; memset(klbr_bp_st, 0, sizeof klbr_bp_st); }      /* BoardProbe/BoardLog diagnostics restart with the round (klbr_van is -1 after the shadow reset: a state flicker must not count a spurious visit) */
        return;
    }
    klbr_game_tid = GetCurrentThreadId();
    if (klbr_sm_round != sm) { if (klbr_sm_round) klbr_summary(); klbr_tr_restore_all("round change"); memset(klbr_t, 0, sizeof klbr_t); memset(klbr_tt, 0, sizeof klbr_tt); klbr_tt_turned = klbr_tt_back = klbr_tt_kills = klbr_tt_capped = klbr_tt_refused = klbr_dg0 = klbr_dg1 = 0; klbr_trr_t0 = GetTickCount(); klbr_trr_pass = klbr_trr_marks = 0; klbr_trr_pass1 = klbr_trr_mark1 = 0; klbr_mk_last = 0; klbr_mkgap_logged = 0; klbr_row0_which = -2; memset(&klbr_hl, 0, sizeof klbr_hl); klbr_hl_s15 = 0; klbr_sm_round = sm; klbr_nbuilt = klbr_nrefused = klbr_nvec_fail = klbr_swaps = klbr_frames = klbr_sw_flt = klbr_sw_bad = klbr_slow = klbr_slow_run = klbr_nrevoke = klbr_crash_told = 0; klbr_us_max = 0; klbr_ngrab = klbr_npay = klbr_nabort = klbr_nstart = klbr_s202_n = klbr_s202_told = klbr_s45_n = klbr_ntraitor = 0; klbr_ta_n = klbr_ta_flt = klbr_ta_sc_n = klbr_ta_wlog = 0; klbr_ta_dis = 0; memset(klbr_ta, 0, sizeof klbr_ta); klbr_paid = 0; klbr_claim_skip = klbr_claim_fb = 0; klbr_dc_offered = klbr_dc_grabs = 0; klbr_bs_defer_n = klbr_bs_real = klbr_bs_fb = 0; klbr_bl_new = klbr_bl_rep = klbr_bl_gate = klbr_bl_sec = 0; klbr_bl_stale = klbr_bp_lines = 0; klbr_bp_lvis = 0; memset(klbr_bp_st, 0, sizeof klbr_bp_st); klbr_vis = 0; klbr_bn_told = klbr_bn_ok = 0; memset(klbr_bl_at, 0, sizeof klbr_bl_at); klbr_sync_at = 0; klbr_depth = 0; klbr_shadow_reset(); klbr_verdict_n = 0;
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
static int klbr_keyi(const char *k, int def)      /* a signed integer key (GetPrivateProfileInt cannot return a negative value) */
{
    char b[32];
    b[0] = 0; GetPrivateProfileStringA("Brain", k, "", b, (DWORD)sizeof b, klh_ini);
    return b[0] ? atoi(b) : def;
}
static void klbr_init(void)
{
    int sw[KBR_NSW];
    klbr_bprobe = klbr_key("BoardProbe");      /* log only, independent of the other Board keys (also read offline: the Arcade baseline in klmove.c) */
    if (klbr_bprobe) klog("brain: BoardProbe=1 (UNTESTED, log only): real rules boarding fields at each vehicle state change (online host and Arcade), per-bot waiting lines in van state 3 / 4 (max 80 per round), stale-ledger count in BoardLog");
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
    klbr_s2gate = klbr_traitor && klbr_key("OnlineBrainTraitorStage2Gate");      /* UNTESTED, default off; the stage byte only reaches the real Traitor evaluate when the Brain's shadow runs */
    { long m = GetPrivateProfileIntA("Brain", "OnlineBrainTraitorStage2Money", 1250000, klh_ini); klbr_s2money = m < 0 ? 0 : m > 100000000 ? 100000000 : m; }
    { long a = GetPrivateProfileIntA("Brain", "OnlineBrainTraitorStage2MinS", 0, klh_ini), b = GetPrivateProfileIntA("Brain", "OnlineBrainTraitorStage2MaxS", 0, klh_ini);
      klbr_s2min = a < 0 ? 0 : a > 3600 ? 3600 : a; klbr_s2max = b < 0 ? 0 : b > 3600 ? 3600 : b;
      if (klbr_s2gate && (klbr_s2min || klbr_s2max)) klog("brain: OnlineBrainTraitorStage2MinS=%ld / MaxS=%ld (UNTESTED): the gate never opens before MinS seconds into the round, and opens at MaxS even with no van call (0 = off)", klbr_s2min, klbr_s2max);
      else if (!klbr_s2gate && (a || b)) klog("brain: OnlineBrainTraitorStage2MinS / MaxS need OnlineBrainTraitorStage2Gate=1: off"); }
    klbr_s2vrel = klbr_s2gate && klbr_s2min && GetPrivateProfileIntA("Brain", "OnlineBrainTraitorMinSVanRelease", 0, klh_ini) != 0;      /* (recommended on, with NoBoard=2) UNTESTED */
    if (klbr_s2vrel) klog("brain: OnlineBrainTraitorMinSVanRelease=1 (UNTESTED): MinS no longer holds the Traitor evaluate once the van is called (state 1..4), like Arcade's window; use with OnlineBrainTraitorNoBoard=2");
    { long g = GetPrivateProfileIntA("Brain", "OnlineBrainTraitorMarkGapMs", 0, klh_ini); klbr_mkgap = !klbr_traitor || g < 0 ? 0 : g > 60000 ? 60000 : g;      /* (recommended on: 500) UNTESTED */
      if (klbr_mkgap) klog("brain: OnlineBrainTraitorMarkGapMs=%ld (UNTESTED): a Traitor mark waits this long after the previous mark of the round (Arcade spaces its marks >= ~0.5 s)", klbr_mkgap); }
    if (klbr_key("OnlineBrainTraitorStage2Gate") && !klbr_s2gate) klog("brain: OnlineBrainTraitorStage2Gate needs OnlineBrainTraitor=1: off");
    if (klbr_s2gate) klog("brain: OnlineBrainTraitorStage2Gate=1 (UNTESTED): a carrying bot shows stage 1 to the Traitor evaluate until the van is called / the gather runs / it is ordered to the exit box%s", klbr_s2money ? " or it holds the money fallback" : " (no money fallback)");
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
    klbr_loson = klbr_key("OnlineBrainTraitorLosGate");
    if (klbr_loson) klog("brain: OnlineBrainTraitorLosGate=1 UNTESTED (recommended off): a marked bot's Sense / MarkSeen feed skips a human whose line (bot eye +%d to human chest +%d: GUESS heights) the game's physics line test (vt+0x264 of [[[0xdd2640]+0xac]+0x8c], mask 0x10, as in 0x4e1750) reports blocked, and HolderFix leaves the flags of a blocked human alone; an unanswered query fails open", (int)KLBR_LOS_EYE, (int)KLBR_LOS_CHEST);
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
    klbr_f3on = klbr_fpon && klbr_key("OnlineBrainTraitorFireProbe3");
    if (klbr_key("OnlineBrainTraitorFireProbe3") && !klbr_f3on) klog("brain: OnlineBrainTraitorFireProbe3 needs OnlineBrainTraitorFireProbe: off");
    if (klbr_f3on) klog("brain: OnlineBrainTraitorFireProbe3=1 UNTESTED (recommended off): READ ONLY toward the game state; counting detours on 0x8c1830 and 0x5faeb0 (TEST build only, unhashed code), per-sample item / template / body numbers, round counts (host only)");
    klbr_f4on = klbr_fpon && klbr_key("OnlineBrainTraitorFireProbe4");
    if (klbr_key("OnlineBrainTraitorFireProbe4") && !klbr_f4on) klog("brain: OnlineBrainTraitorFireProbe4 needs OnlineBrainTraitorFireProbe: off");
    klbr_f5on = klbr_fpon && klbr_key("OnlineBrainTraitorFireProbe5");
    if (klbr_key("OnlineBrainTraitorFireProbe5") && !klbr_f5on) klog("brain: OnlineBrainTraitorFireProbe5 needs OnlineBrainTraitorFireProbe: off");
    if (klbr_f5on) klog("brain: OnlineBrainTraitorFireProbe5=1 UNTESTED (recommended off): READ ONLY toward the game state; a counting detour on 0x4cc389 (the per-shot gate byte, TEST build only, unhashed code) and a counting wrapper on slot 422 (0x7e1700, victim hit routing; needs [NetSmooth] Enable=1, remote-seat victims only) (host only)");
    if (klbr_f4on) klog("brain: OnlineBrainTraitorFireProbe4=1 UNTESTED (recommended off): DATA READS ONLY, no hook, no write; item shot counters / owner gate bit / victim gates / predicted victim route per FireProbe sample (host only)");
    klbr_f6on = klbr_key("OnlineBrainTraitorFireProbe6");      /* independent of AttackHandle / FireProbe: also Arcade; marking of online traitor bots needs the slot-113 wrapper (the FireProbe keys) */
    if (klbr_f6on) klog("brain: OnlineBrainTraitorFireProbe6=1 UNTESTED (recommended off): READ ONLY toward the game state; counting detours on 0x4cb8b9, 0x4cc3a0, 0x4cc440, 0x4cc450, 0x4cc644, 0x4cc65d (TEST build only, unhashed code 0x4ca000-0x4cd000): per shot the muzzle origin / matrix, the 0x7cb080 branch, the ray from / to and its return, tagged networked yes/no (host and Arcade)");
    klbr_f7on = klbr_key("OnlineBrainTraitorFireProbe7");
    klbr_raon = klbr_key("OnlineBrainTraitorRayAim");
    klbr_ra_rowcfg = klbr_keyi("OnlineBrainTraitorRayAimRow", -1); klbr_ra_signcfg = klbr_keyi("OnlineBrainTraitorRayAimSign", 1);
    klbr_ra_spread = klbr_keyi("OnlineBrainTraitorRayAimSpreadDeg", 3); if (klbr_ra_spread < 0) klbr_ra_spread = 0; if (klbr_ra_spread > 30) klbr_ra_spread = 30;
    klbr_ra_maxd = klbr_keyi("OnlineBrainTraitorRayAimMaxDist", 6000); if (klbr_ra_maxd < 0) klbr_ra_maxd = 0;
    klbr_ra_site = kbr_ra_sitemask(klbr_keyi("OnlineBrainTraitorRayAimSite", 5));      /* bits 1 T, 2 item aim point, 4 M; default 5 (bit 2 is opt-in) */
    klbr_ra_chest = klbr_keyi("OnlineBrainTraitorRayAimChest", 130);
    klbr_ra_seed = (kbr_u32)GetTickCount() * 2654435761u | 1u;
    klbr_f8on = klbr_key("OnlineBrainTraitorFireProbe8");
    klbr_losprobe = klbr_f8on && klbr_key("OnlineBrainTraitorLosProbe");
    if (klbr_key("OnlineBrainTraitorLosProbe") && !klbr_losprobe) klog("brain: OnlineBrainTraitorLosProbe needs OnlineBrainTraitorFireProbe8: off");
    if (klbr_losprobe) klog("brain: OnlineBrainTraitorLosProbe=1 UNTESTED (recommended off): FireProbe8 also runs the game's physics line test (a pure query into our own buffer; reads the collision world, writes no game memory) per marked shot, from the muzzle origin and from the bot eye to the human chest");
    klbr_mbon = klbr_key("OnlineBrainTraitorModeBProbe");
    klbr_cion = klbr_key("OnlineBrainTraitorCloseInProbe");
    klbr_dpon = klbr_key("OnlineBrainTraitorDefendProbe"); if (klbr_dpon) { klbr_cion = 1; klog("brain: OnlineBrainTraitorDefendProbe=1 UNTESTED (recommended off): READ ONLY toward the game state (TEST build only; implies the CloseInProbe counting sites; adds counting detours on the ZCloseIn gate branches 0x672507 0x6725a1 0x6725c9 0x6725f4 0x67261e 0x67264e 0x672678 0x672691, 0x6726b3 and the ZGraceShot eval 0x41a5b0, plus data reads of the Defend winner [goal+0x14] and the list C inputs); lines: brain: defendprobe data / round"); }
    klbr_rpon = klbr_key("OnlineBrainTraitorRunProbe"); if (klbr_rpon) { klbr_dpon = 1; klbr_cion = 1; klog("brain: OnlineBrainTraitorRunProbe=1 UNTESTED (recommended off): READ ONLY toward the game state (TEST build only; forces DefendProbe and CloseInProbe on; adds counting detours on the ZCloseIn run body 0x76e8c0 and its two branch targets 0x76e8ed (direct) / 0x76e935 (cover), all unhashed; reuses the CloseInProbe sites 0x4a7e60 (run task), 0x800630 (arm) and 0x672770 (1.0 tail, for the wins); data reads of the run task [S+0x56c] and the movement component [S+0x4a4]); lines: brain: runprobe win / data / round"); }
    klbr_cbmode = klbr_keyi("OnlineBrainTraitorCombatFlag", 0); if (klbr_cbmode < 1 || klbr_cbmode > 3) klbr_cbmode = 0;
    klbr_nbmode = klbr_keyi("OnlineBrainTraitorNoBoard", 0); if (klbr_nbmode < 1 || klbr_nbmode > 2) klbr_nbmode = 0;
    if (klbr_nbmode && !klbr_taon) { klog("brain: OnlineBrainTraitorNoBoard %d ignored: needs OnlineBrainTraitorArcade=1 (Arcade=1 turns OnlineBrainTraitorTurn off later in init, so only the Arcade key is tested here)", klbr_nbmode); klbr_nbmode = 0; }
    if (klbr_nbmode) klog("brain: OnlineBrainTraitorNoBoard=%d UNTESTED (recommended off): host only; a bot marked by OnlineBrainTraitorArcade is skipped by the puppeteer like a TraitorTurn bot (no steering, escort, exit walk, fallback boarding, van / box orders, BoardAll count)%s; its ledger order is dropped once; the stage byte, the real Board tactic and the grab path are untouched; no detour; lines: brain: traitor noboard / traitor board", klbr_nbmode, klbr_nbmode == 2 ? " and the slot-45 pendBoard hook boarding" : "");
    klbr_hsmode = klbr_keyi("OnlineBrainTraitorHolderSet", 0); if (klbr_hsmode != 1 && klbr_hsmode != 2) klbr_hsmode = 0;
    if (klbr_hsmode) klog("brain: OnlineBrainTraitorHolderSet=%d UNTESTED (recommended off): CHANGES the game (TEST build only, host only, online marked bots only): while OnlineBrainTraitorLosGate and OnlineBrainTraitorSense report every human BLOCKED for the bot, points its holder [S+0xa8..] at the nearest live human (0x6ece90 handle, 0x8ccde0 round-trip check, SetHolder 0x8bd420, flags 0x%lx: the fire test 0x616480 fails with it, ZCloseIn passes); re-applied every 100 ms (the next 0x767510 scan wipes it); stops writing when a human is clear; HolderFix yields to it while blocked; 3 faults = off for the round", klbr_hsmode, kbr_hs_flags(klbr_hsmode));
    klbr_afon = klbr_key("OnlineBrainTraitorAfcProbe");
    if (klbr_afon) klog("brain: OnlineBrainTraitorAfcProbe=1 UNTESTED (recommended off): READ ONLY, no detour (TEST build only); once a second per marked bot (online: the host's Arcade-marked wrapped bots, needs OnlineBrainTraitorArcade=1; Arcade offline: the traitor-marked soldier) reads the ZAttackFromCover eval inputs and the distance to the defend place [S+0x64c] (position layout GUESS); lines: brain: afc / afc round");
    klbr_dfon = klbr_key("OnlineBrainTraitorDriftProbe");
    if (klbr_dfon) klog("brain: OnlineBrainTraitorDriftProbe=1 UNTESTED (recommended off): READ ONLY, no detour (TEST build only); once a second per marked bot (online: needs OnlineBrainTraitorArcade=1; Arcade offline: the traitor-marked soldier) logs the defend block [S+0x64c] and the holder; EVENT lines 'brain: drift chg' when the block moves > 300 cm; lines: brain: drift / drift chg / drift round");
    klbr_plmode = klbr_keyi("OnlineBrainTraitorDefendPull", 0); if (klbr_plmode < 0 || klbr_plmode > 2) klbr_plmode = 1;      /* any other nonzero value = 1 as before */
    klbr_plon = klbr_plmode != 0;
    if (klbr_plmode == 2) klog("brain: OnlineBrainTraitorDefendPull=2 UNTESTED (recommended off): CHANGES the game: instead of the raw xyz store the stock order 0x760e50 (soft 0, reset 0, via kle_order3) is given to a place 550 cm short of the holder [S+0xac] (living human) else the nearest human, same gates as mode 1; side effects of the order (GUESS): [block+0x11]=1, [S+0x4fc], a go-to 0x6cabf0 that may fight Defend; lines: brain: pull2 / pull round");
    else if (klbr_plon) klog("brain: OnlineBrainTraitorDefendPull=1 UNTESTED (recommended off): CHANGES the game (TEST build only, marked traitor only): writes the defend block xyz [[S+0x64c]+0..8] (nothing else) toward the nearest living human when the block is > 2500 cm from every human, never while the Defend winner is ZCloseIn / Board / Loot, at most every 250 ms per bot; lines: brain: pull / pull round");
    klbr_f6act = klbr_f6on || klbr_f7on || klbr_raon || klbr_f8on || klbr_mbon || klbr_cion || klbr_dpon || klbr_afon || klbr_dfon || klbr_plon;
    if (klbr_cion) klog("brain: OnlineBrainTraitorCloseInProbe=1 UNTESTED (recommended off): READ ONLY toward the game state (TEST build only; counting detours on the ZCloseIn eval 0x6724e0 and its two return tails 0x672722 / 0x672770, the run-task tick 0x4a7e60 and the soldier arm 0x800630, all unhashed so they also install under SessionSafe=1; plus 250 ms DATA-side sampling of the current goal, the tactic lists, [S+0x4fc] / [S+0x6fc] and the ZCloseIn timer / destination); needs the slot-113 wrapper (the FireProbe keys) to mark the online bot; offline Arcade is sampled like ModeBProbe");
    if (klbr_cbmode) klog("brain: OnlineBrainTraitorCombatFlag=%d UNTESTED (recommended off): CHANGES the game (TEST build only, host only, online marked bots only): writes the byte [S+0x4fc] = 1 every 250 ms, only while OnlineBrainTraitorLosGate and OnlineBrainTraitorSense report every human BLOCKED for the bot (none clear) and [S+0x6fc] is %s (value 1 = the verifier text, which the disassembly REFUTES; 3 = as 2 but it also writes [S+0x6fc] = 1 itself while that byte is 0 and puts it back to 0 afterwards, GUESS that this makes ZCloseIn run; 2 = the Defend tick 0x85f896..0x85f8bc as re-read in debug/dasm.py 11-04: list A needs [S+0x4fc] != 0 AND [S+0x6fc] != 0, so 2 is the one that can work); it never writes while a human is clear; 3 faults = off", klbr_cbmode, klbr_cbmode == 1 ? "0" : klbr_cbmode == 3 ? "0 or nonzero (mode 3 sets it to 1 when 0)" : "nonzero");
    if (klbr_mbon) klog("brain: OnlineBrainTraitorModeBProbe=1 UNTESTED (recommended off): READ ONLY toward the game state (TEST build only; counting detours on slot 83 0x831850, the ZAttackTarget tick 0x4f4460 and its mode-B search 0x4f4b5f / 0x4f4b9b / 0x4f4bd1 / 0x4f4ba9 / 0x4f4bed, the run-task re-arm 0x800650; installed through the patch guard: under SessionSafe=1 only the unhashed 0x831850 and 0x800650 go in, the hashed 0x4f4xxx ones are refused; plus 250 ms DATA-side goal sampling that needs no site); needs the slot-113 wrapper (the FireProbe keys) to mark the bot");
    if (klbr_f8on) klog("brain: OnlineBrainTraitorFireProbe8=1 UNTESTED (recommended off): READ ONLY toward the game state (TEST build only; counting detours: pellet loop 0x4cc1c0 / 0x4cc1d8, ZProjectile Activate 0x900d80, hit callback via the 0x8ccde0 lookup, send via 0x596fc0, victim entry 0x4db580; the sites in hashed ranges install only with SessionSafe=0); needs the slot-113 wrapper (the FireProbe keys) to mark the bot");
    if (klbr_f7on) klog("brain: OnlineBrainTraitorFireProbe7=1 UNTESTED (recommended off): READ ONLY toward the game state (TEST build only: the FireProbe6 counting detours plus a seventh on AimAt 0x70f130, unhashed code); per marked shot the AimAt fields [body+0x824..0x83c], [+0x68c], [+0x64c], who the target / holder / fire task target is, AimAt called in the last second, the ray matrix rows against the human, the template range (host only; needs the slot-113 wrapper to mark the bot: the FireProbe keys)");
    if (klbr_raon) klog("brain: OnlineBrainTraitorRayAim=1 UNTESTED (recommended off): CHANGES the game (TEST build only, host only, marked traitor shots only): the muzzle matrix T at 0x4cb8b9 (site bit 1) and the ray matrix M at 0x4cc440 (site bit 4) are rewritten in the game thread's own stack so the forward row (row %d%s, sign %d: GUESS) points at the human's chest (feet + %d: GUESS) with a random cone error of %d deg (GUESS), target within %d units (GUESS), site mask %d", kbr_ra_row(klbr_ra_rowcfg), klbr_ra_rowcfg < 0 ? " auto" : "", kbr_ra_sign(klbr_ra_signcfg), klbr_ra_chest, klbr_ra_spread, klbr_ra_maxd, klbr_ra_site);
    klbr_wron = klbr_cfh && klbr_key("OnlineBrainTraitorWeaponReady");
    if (klbr_key("OnlineBrainTraitorWeaponReady") && !klbr_wron) klog("brain: OnlineBrainTraitorWeaponReady needs OnlineBrainTraitorAttackHandle: off");
    if (klbr_wron) klog("brain: OnlineBrainTraitorWeaponReady=1 UNTESTED (recommended off): a marked bot's byte [body+0x5c8] (weapon not ready, blocks the shooting task) is cleared to 0 when its weapon controller exists (host only; not put back)");
    klbr_gfon = klbr_cfh && klbr_key("OnlineBrainTraitorGateForce"); klbr_gfall = klbr_gfon && klbr_key("OnlineBrainTraitorGateForceAll");
    if (klbr_key("OnlineBrainTraitorGateForce") && !klbr_gfon) klog("brain: OnlineBrainTraitorGateForce needs OnlineBrainTraitorAttackHandle: off");
    if (klbr_key("OnlineBrainTraitorGateForceAll") && !klbr_gfon) klog("brain: OnlineBrainTraitorGateForceAll needs OnlineBrainTraitorGateForce: off");
    if (klbr_gfon) klog("brain: OnlineBrainTraitorGateForce=1 UNTESTED (recommended off): the per-shot gate 0x4cc389 fails for the host's online bots (bs33); slot 12 (vt+0x30) of the private OnlineCopToBot ZFFActor table is wrapped so the game's own ZLNKOBJ test at 0x4cb819 passes for %s (data write, ships; needs [BotFill] OnlineCopToBot; host only)", klbr_gfall ? "marked bots AND every bot on the table (GateForceAll)" : "marked traitor bots");
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
