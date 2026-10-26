/*
 * klbotfill.c - [Bots] OnlineFill: the PLAN and the PROBE for "AI heisters in the empty seats of an online FA lobby".
 * Part of KLHook (included by klhook.c after kllobby.c, SHIP and TEST alike). READ-ONLY apart from what kllobby.c already
 * writes: this module writes NOTHING to the game. re\bots_online_fill.md has the whole reading and the test plan.
 *
 * WHAT THE EXE SHOWS (kl2.exe 0490, read 2026-10-25; CERTAIN unless marked):
 *   - The map-authored heister squads (stock F01..F09 and every kl_fa_bots map) are ZSquadScript groups with EGameType
 *     eHeistOnly. ZSquadScript slot 14 (0x7b3790, collects the members) drops a member from play when
 *       networked (0x863a60: session role 2 / 3) && [0x168e59c] == 0 (FA) && !([squad+0x34] & 1)      0x7b37d1..0x7b37f0
 *     so online FA keeps a squad only if its mask has bit 1 (eFragileAllianceOnly / eAllTypes). Arcade (0x7f6850) keeps
 *     mask bits 1 and 8. No online squad of mask 8 exists: that is why a hosted round has no AI heisters.
 *   - Even a kept squad's Ally soldiers are only walkers online: CPPScript::ZSoldier's constructor (0x6ab250) builds the
 *     loot / board / traitor tactics ([soldier+0x5f0/0x5f4/0x5f8]) only when 0x7f6850 is true (roles 0 / 1), and the crew
 *     record (slot 198 = 0x588980) exists only on ZGameRulesHeist; the online rules classes have another slot 198 and a
 *     0x74-byte per-client table (re\netcode.md 10). So this module cannot ADD loot-taking heisters: that needs code.
 * WHAT IT DOES ([Bots] OnlineFill=1, default 0, "(recommended off)" until the live test passes):
 *   1. kllobby.c: the host's Ready may start the round with fewer than the lobby target (MinPlayers floor 1) and kllb_orig
 *      remembers the target the lobby had (6 for a full FA lobby): fill = kllb_orig - connected.
 *   2. Here: once per round, on the host AND on a client (both read the same way, so a later action can be deterministic),
 *      the plan line 'botfill: ...' = target, connected, fill; then every 5 s in a round the census of the Ally actors
 *      that survived the load (count, alive, their tactic fields) - the proof of what the squad filter did.
 * KLHook.ini
 *   [Bots]
 *   OnlineFillSquads=0  3. (needs OnlineFill=1; default off) before the round the first `fill` ZSquadScripts of mask eHeistOnly get bit 1 so the
 *                    online collect keeps them (walkers only, see 6. of the doc); 'botfill: squad pass:' lines show what was found and set
 *   OnlineFill=0     0 = off (the game's own rule: no AI heisters online). 1 = plan + probe lines, Ready may start below the target
 */
#ifndef KLBOTFILL_C
#define KLBOTFILL_C

static int klbf_oh;                /* [BotFill] OnlineHost (klsync.c reads it: bots are mirrored there) */
static int klbf_on, klbf_sq;      /* klbf_sq = [Bots] OnlineFillSquads (see the header, step 3) */
static int klbf_fill;              /* the plan's fill, for the squad pass */
static int klbf_ot, klbf_ot_carry = 2, klbf_ot_take; static float klbf_ot_near = 150.0f;
static int klbf_ot_in;         /* [BotFill] OnlineTactics state, see the puppeteer block below */
static int klbf_ot_vcall = 1;      /* [BotFill] OnlineVanCall */
static int klbf_ot_vstate = 1, klbf_ot_late = 75; static DWORD klbf_ot_calledAt;      /* [BotFill] OnlineVanState (BO9: the van node stays at the origin, so "van here" must come from [rules+0x1dc]), OnlineLateExit (s of clock left) */
static int klbf_ot_bwalk = 1, klbf_ot_board = 0, klbf_ot_bprobe = 1;      /* [BotFill] OnlineBoxWalk, OnlineBoard, OnlineBoxProbe (the ZAllyEscapeBox block below) */
static int klbf_ot_hmul = 5, klbf_ot_van = 1, klbf_ot_gtake = 0; static float klbf_ot_guard = 2500.0f;      /* OnlineHealthMul, OnlineTacticsVan, OnlineTacticsGuard (cm) */
static int klbf_ot_vgather = 1, klbf_ot_vhold = 1, klbf_ot_gmax = 25, klbf_ot_hmax = 15; static float klbf_ot_gm = 1200.0f, klbf_ot_hm = 3000.0f, klbf_ot_hnear = 1800.0f;      /* [BotFill] OnlineVanGather / OnlineGatherM (cm) / OnlineGatherMaxS, OnlineVanHold / OnlineHoldM (cm, shield) / OnlineHoldNearM (cm, timer) / OnlineHoldMaxS */
static int klbf_ot_door = 1;      /* [BotFill] OnlineSkipDoorStacks (BOS1): stock vault cases with ZOnlineMoneyCtrl +0x5c set wait behind kick doors (re/stock_map_bots.md) */
static int klbf_ot_bforce = 1, klbf_ot_recall = 1;static int klbf_ot_retry = 1, klbf_ot_idlevan = 1, klbf_ot_firestall = 1, klbf_ot_vidle; static int klbf_ot_retryS = 45, klbf_ot_idleS = 20; static float klbf_ot_exitdy = 800.0f; static float klbf_ot_bslack = 100.0f; static int klbf_ot_joincall = 1; static int klbf_ot_sprint = 1; static float klbf_ot_crowd = 1200.0f; static int klbf_ot_keepgo = 1, klbf_ot_etrace = 0;      /* [BotFill] OnlineExitKeepGoal / OnlineExitTrace (BOS_DD06s: bots ran ~5.9 m/s but stood ~70% of the exit walk; GUESS: the 6 s repeat order re-pushes the running Defend goal via 0x7bbf70) */      /* [BotFill] OnlineExitCrowd (cm; BOS_DD07: 3 bots 2-10 m off the trigger centre during the whole wait) */      /* [BotFill] OnlineExitSprint (BOS_DD06: 7 carriers WALKED 180 m to the exit at ~0.7 m/s, 0 boarded) */      /* [BotFill] OnlineJoinCalled (BOS_DD04: 4 carriers stood 100 m off while the van came for bot 5) */      /* [BotFill] OnlineBoxSlack (cm): BOS_DD02x2 bot 0 stood 0.5 m outside the box frame for the whole van wait (nav snap of the box centre) */      /* [BotFill] OnlineExitDy: height window round the exit trigger's node (BOS_DD02r: the bots stood on the trigger's own nav poly 6.2 m under DD02's centre y 6620, outside the old 400) */      /* [BotFill] OnlineGiveUpRetry / OnlineGiveUpRetryS, OnlineIdleVan / OnlineIdleVanS, OnlineFireStall (BO12); klbf_ot_vidle = a bot had nothing left to do last tick */
static DWORD klbf_sq_done;         /* the session object the squad pass finished for */

/* Step 3 (default off, SHIP-safe: one heap BYTE per squad). Squads are ZSquadScript entities (vtable 0xbcce3c); [squad+0x34] is the
   EGameType mask. The online collect (slot 14, 0x7b3790, test at 0x7b37e3) drops a member when the mask lacks bit 1; the first `fill`
   squads whose mask is exactly eHeistOnly (8) get bit 1 added (-> 9: kept online, by the unchanged game code). The order is the
   entity-table order = the load order, the same on every peer that loaded the same level. GUESS: the entity table already holds the
   squads when this tick runs; if the collect has run before, the write changes nothing (logged as 'late') and the census (step 2)
   shows 0 Ally. Returns the number of squads changed (>= 0) or -1 when the table is unreadable. */
static int klbf_squads(int fill)
{
    DWORD p, tab, i, blk[64 * 32]; int n = 0, sq = 0, set = 0, k8 = 0; char mk[96]; mk[0] = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return -1;
    for (i = 0; i < 0x10000 && n < 4000; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], m = 0; BYTE nm;
            if (o < 0x10000 || klh_rd32(o) != 0x00bcce3c) continue;       /* ZSquadScript */
            n++;
            if (!klh_rd(o + 0x34, &m, 4)) continue;
            sq++;
            if (sq <= 12 && strlen(mk) < 80) { char t[12]; snprintf(t, sizeof t, " %lx", (unsigned long)m); strcat(mk, t); }
            if ((m & 0xff) != 8) continue;
            k8++;
            if (k8 > fill) continue;
            nm = (BYTE)((m & 0xff) | 1);
            if (klh_data((void *)(DWORD_PTR)(o + 0x34), &nm, 1, "squad game-type mask (eHeistOnly -> +FA, OnlineFillSquads)")) set++;
        }
    }
    klog("botfill: squad pass: %d ZSquadScript, %d with mask 8 (heister squads), %d given bit 1 for fill %d; first masks:%s", sq, k8, set, fill, mk);
    return set;
}

/* The bot actors for klbalance.c's online point-blank wrapper (OnlinePointBlank): the puppeteer pass publishes the live team-2 Ally actors it found (human heisters are team 2 too, so the
   team alone cannot tell them apart; the puppeteer's list is the bots). Entries first, then the count; read on the game thread, fresh for 5 s. Needs OnlineTactics=1 (the census is its). */
#define KLBF_OT_BOTS_MAX 16      /* = KLBF_OT_BOTS (defined below) */
static int klbf_ot_way;      /* OnlineWaypoints toggle (read in the init, used by klbf_way_load below) */
static int klbf_ot_ramp, klbf_ot_rampdry;      /* OnlineRampFire / OnlineRampDry toggles (read in the init, used by klbf_ramp_* below) */
static DWORD klbf_pb_bots[KLBF_OT_BOTS_MAX]; static volatile LONG klbf_pb_n; static volatile DWORD klbf_pb_at;
static int klbf_pb_any(void) { return klbf_pb_n > 0 && GetTickCount() - klbf_pb_at < 5000u; }
static int klbf_pb_is_bot(DWORD a) { int i, n = klbf_pb_n; if (!a || !klbf_pb_any()) return 0; for (i = 0; i < n && i < KLBF_OT_BOTS_MAX; i++) if (klbf_pb_bots[i] == a) return 1; return 0; }

static DWORD klbf_pb_get(int i) { return i >= 0 && i < klbf_pb_n && i < KLBF_OT_BOTS_MAX && klbf_pb_any() ? klbf_pb_bots[i] : 0; }      /* OnlineCopToBot installs its table on these */
static void klbf_ot_summary(void);
static void klbf_init(void)
{
    klbf_on = GetPrivateProfileIntA("Bots", "OnlineFill", 0, klh_ini) != 0;
    klbf_sq = klbf_on && GetPrivateProfileIntA("Bots", "OnlineFillSquads", 0, klh_ini) != 0;      /* TEST first: the squads of the first `fill` heister slots are kept online */
    klbf_oh = GetPrivateProfileIntA("BotFill", "OnlineHost", 0, klh_ini) != 0;
    klbf_ot = klbf_oh && GetPrivateProfileIntA("BotFill", "OnlineTactics", 0, klh_ini) != 0;      /* (recommended off) */
    klbf_ot_carry = (int)GetPrivateProfileIntA("BotFill", "OnlineTacticsCarry", 2, klh_ini); if (klbf_ot_carry < 1) klbf_ot_carry = 1;
    klbf_ot_near = (float)GetPrivateProfileIntA("BotFill", "OnlineTacticsNear", 150, klh_ini); if (klbf_ot_near < 20) klbf_ot_near = 20;
    klbf_ot_take = GetPrivateProfileIntA("BotFill", "OnlineTacticsTake", 0, klh_ini) != 0;
    klbf_ot_hmul = (int)GetPrivateProfileIntA("BotFill", "OnlineHealthMul", 5, klh_ini); if (klbf_ot_hmul < 1) klbf_ot_hmul = 1; if (klbf_ot_hmul > 20) klbf_ot_hmul = 20;
    klbf_ot_gtake = GetPrivateProfileIntA("BotFill", "OnlineGuardTake", 0, klh_ini) != 0;      /* BO8c: the 30 s fallback sent all 5 holding bots into the squads at once; all 7 died within 71 s */
    klbf_ot_guard = 100.0f * (float)GetPrivateProfileIntA("BotFill", "OnlineTacticsGuard", 25, klh_ini); if (klbf_ot_guard < 0) klbf_ot_guard = 0;
    klbf_ot_van = GetPrivateProfileIntA("BotFill", "OnlineTacticsVan", 1, klh_ini) != 0;
    klbf_ot_vcall = GetPrivateProfileIntA("BotFill", "OnlineVanCall", 1, klh_ini) != 0;      /* (recommended on) */
    klbf_ot_vstate = GetPrivateProfileIntA("BotFill", "OnlineVanState", 1, klh_ini) != 0;      /* (recommended on) */
    klbf_ot_late = (int)GetPrivateProfileIntA("BotFill", "OnlineLateExit", 75, klh_ini); if (klbf_ot_late < 0) klbf_ot_late = 0; if (klbf_ot_late > 200) klbf_ot_late = 200;      /* (recommended on) GUESS 75 s: 30 s door cutoff + 25 s walk + 20 s slack */
    klbf_ot_bwalk = GetPrivateProfileIntA("BotFill", "OnlineBoxWalk", 1, klh_ini) != 0;      /* (recommended on) */
    klbf_ot_board = GetPrivateProfileIntA("BotFill", "OnlineBoard", 0, klh_ini) != 0;      /* (recommended off until a live run shows the bot vanishes on every screen) */
    klbf_ot_bprobe = GetPrivateProfileIntA("BotFill", "OnlineBoxProbe", 1, klh_ini) != 0;      /* (recommended on: log only) */
    klbf_ot_vgather = GetPrivateProfileIntA("BotFill", "OnlineVanGather", 1, klh_ini) != 0;      /* (recommended on) */
    klbf_ot_gm = 100.0f * (float)GetPrivateProfileIntA("BotFill", "OnlineGatherM", 12, klh_ini); if (klbf_ot_gm < 200.0f) klbf_ot_gm = 200.0f;      /* GUESS 12 m */
    klbf_ot_gmax = (int)GetPrivateProfileIntA("BotFill", "OnlineGatherMaxS", 25, klh_ini); if (klbf_ot_gmax < 1) klbf_ot_gmax = 1; if (klbf_ot_gmax > 120) klbf_ot_gmax = 120;      /* GUESS 25 s */
    klbf_ot_vhold = GetPrivateProfileIntA("BotFill", "OnlineVanHold", 1, klh_ini) != 0;      /* (recommended on) */
    klbf_ot_hm = 100.0f * (float)GetPrivateProfileIntA("BotFill", "OnlineHoldM", 30, klh_ini); if (klbf_ot_hm < 500.0f) klbf_ot_hm = 500.0f;      /* GUESS 30 m (re/van_hold_online.md) */
    klbf_ot_hnear = 100.0f * (float)GetPrivateProfileIntA("BotFill", "OnlineHoldNearM", 18, klh_ini); if (klbf_ot_hnear < 500.0f) klbf_ot_hnear = 500.0f;      /* GUESS 18 m (research: 15-20 m) */
    klbf_ot_hmax = (int)GetPrivateProfileIntA("BotFill", "OnlineHoldMaxS", 15, klh_ini); if (klbf_ot_hmax < 1) klbf_ot_hmax = 1; if (klbf_ot_hmax > 30) klbf_ot_hmax = 30;      /* GUESS 15 s (research: cap 15-20 s; N1 saw a van held 15 s destroyed unshielded) */
    klbf_ot_retry = GetPrivateProfileIntA("BotFill", "OnlineGiveUpRetry", 1, klh_ini) != 0;      /* (recommended on) BO12: 4 given-up stacks stayed blacklisted for the whole round and the bots idled for 3 min */
    klbf_ot_retryS = (int)GetPrivateProfileIntA("BotFill", "OnlineGiveUpRetryS", 45, klh_ini); if (klbf_ot_retryS < 5) klbf_ot_retryS = 5; if (klbf_ot_retryS > 600) klbf_ot_retryS = 600;      /* GUESS 45 s */
    klbf_ot_idlevan = GetPrivateProfileIntA("BotFill", "OnlineIdleVan", 1, klh_ini) != 0;      /* (recommended on) BO12: 0 grabs = nobody ever called the van */
    klbf_ot_idleS = (int)GetPrivateProfileIntA("BotFill", "OnlineIdleVanS", 20, klh_ini); if (klbf_ot_idleS < 5) klbf_ot_idleS = 5; if (klbf_ot_idleS > 300) klbf_ot_idleS = 300;      /* GUESS 20 s with no stack left at all */
    klbf_ot_firestall = GetPrivateProfileIntA("BotFill", "OnlineFireStall", 1, klh_ini) != 0;      /* (recommended on) BO12: bots pinned down by cops were counted as stalled after 12 s */
    klbf_ot_bforce = GetPrivateProfileIntA("BotFill", "OnlineBoxForce", 1, klh_ini) != 0;      /* (recommended on) BO13: the carrier stood at the exit trigger, 3 m outside the box, for the whole van wait (state 3) and never boarded */
    if (klbf_ot) klog("botfill: OnlineTactics box force: OnlineBoxForce=%d (recommended on)", klbf_ot_bforce);
    klbf_ot_bslack = (float)GetPrivateProfileIntA("BotFill", "OnlineBoxSlack", 100, klh_ini);      /* (recommended 100) cm outside the box frame that still count as inside after 8 s of van wait; 0 = off */
    if (klbf_ot_bslack < 0) klbf_ot_bslack = 0;
    klbf_ot_joincall = GetPrivateProfileIntA("BotFill", "OnlineJoinCalled", 1, klh_ini) != 0;      /* (recommended on) */
    if (klbf_ot) klog("botfill: OnlineTactics join called van: OnlineJoinCalled=%d (recommended on)", klbf_ot_joincall);
    klbf_ot_sprint = GetPrivateProfileIntA("BotFill", "OnlineExitSprint", 1, klh_ini) != 0;      /* (recommended on) */
    klbf_ot_crowd = (float)GetPrivateProfileIntA("BotFill", "OnlineExitCrowd", 1200, klh_ini);      /* (recommended 1200) cm round the exit trigger that count as aboard after 5 s of van wait; 0 = off */
    if (klbf_ot_crowd < 0) klbf_ot_crowd = 0;
    klbf_ot_keepgo = GetPrivateProfileIntA("BotFill", "OnlineExitKeepGoal", 1, klh_ini) != 0;      /* (recommended on) */
    klbf_ot_etrace = GetPrivateProfileIntA("BotFill", "OnlineExitTrace", 0, klh_ini) != 0;      /* (recommended off) */
    if (klbf_ot) klog("botfill: OnlineTactics exit keep goal: OnlineExitKeepGoal=%d (recommended on): no 6 s repeat of the exit order while the bot's Defend goal still runs toward it; OnlineExitTrace=%d (recommended off)", klbf_ot_keepgo, klbf_ot_etrace);
    if (klbf_ot) klog("botfill: OnlineTactics exit crowd: OnlineExitCrowd=%.0f cm after 5 s of van wait (recommended 1200, 0 = off)", klbf_ot_crowd);
    if (klbf_ot) klog("botfill: OnlineTactics exit sprint: OnlineExitSprint=%d (recommended on): a bot walking to the exit / box gets the Defend move style Sprint, as stock levels give the last dash to the vehicle", klbf_ot_sprint);
    if (klbf_ot) klog("botfill: OnlineTactics box slack: OnlineBoxSlack=%.0f cm after 8 s of van wait (recommended 100, 0 = off)", klbf_ot_bslack);
    klbf_ot_exitdy = (float)GetPrivateProfileIntA("BotFill", "OnlineExitDy", 800, klh_ini);      /* GUESS: 800 covers a trigger centre floating ~6 m over its floor (DD02 610) without taking a bot on a floor 8 m below */
    if (klbf_ot) klog("botfill: OnlineTactics exit height window: OnlineExitDy=%.0f (recommended 800; was 400 before BOS_DD02r)", klbf_ot_exitdy);
    klbf_ot_recall = GetPrivateProfileIntA("BotFill", "OnlineVanRecall", 1, klh_ini) != 0;      /* (recommended on) BO14: a bot grabbed 800k 3 s after the call and was left behind when the van went */
    if (klbf_ot) klog("botfill: OnlineTactics van recall: OnlineVanRecall=%d (recommended on)", klbf_ot_recall);
    klbf_ot_way = GetPrivateProfileIntA("BotFill", "OnlineWaypoints", 1, klh_ini) != 0;      /* (recommended on) BOS_DD02: 7 bots stalled 139-166 m short of the exit trigger; a [BotFillWay_<SLOT>] route walks them round it */
    if (klbf_ot) klog("botfill: OnlineTactics waypoints: OnlineWaypoints=%d (recommended on; needs a [BotFillWay_<SLOT>] section)", klbf_ot_way);
    klbf_ot_ramp = GetPrivateProfileIntA("BotFill", "OnlineRampFire", 1, klh_ini) != 0;      /* (recommended on) DD02: the ramp trigger never fires online because bots are not counted */
    klbf_ot_rampdry = GetPrivateProfileIntA("BotFill", "OnlineRampDry", 1, klh_ini) != 0;      /* default 1: log only until proven live */
    if (klbf_ot) klog("botfill: ramp: OnlineRampFire=%d (recommended on), OnlineRampDry=%d (log only; needs a [BotFillRamp_<SLOT>] section)", klbf_ot_ramp, klbf_ot_rampdry);
    klbf_ot_door = GetPrivateProfileIntA("BotFill", "OnlineSkipDoorStacks", 1, klh_ini) != 0;      /* (recommended on) BOS1: DD01's 58 vault cases sit behind kick doors; ordered straight at them the bots stalled and took 0 */
    if (klbf_ot) klog("botfill: OnlineTactics BOS1: OnlineSkipDoorStacks=%d (recommended on)", klbf_ot_door);
    if (klbf_ot) klog("botfill: OnlineTactics BO12 fixes: OnlineGiveUpRetry=%d (recommended on, %d s), OnlineIdleVan=%d (recommended on, %d s), OnlineFireStall=%d (recommended on)", klbf_ot_retry, klbf_ot_retryS, klbf_ot_idlevan, klbf_ot_idleS, klbf_ot_firestall);
    if (klbf_ot) klog("botfill: OnlineTactics van gather/hold: OnlineVanGather=%d (recommended on; GatherM %.0f m, GatherMaxS %d s), OnlineVanHold=%d (recommended on; HoldM %.0f m shield, HoldNearM %.0f m timer, HoldMaxS %d s)", klbf_ot_vgather, klbf_ot_gm / 100, klbf_ot_gmax, klbf_ot_vhold, klbf_ot_hm / 100, klbf_ot_hnear / 100, klbf_ot_hmax);
    if (klbf_ot) klog("botfill: OnlineTactics box: OnlineBoxWalk=%d (recommended on), OnlineBoard=%d (recommended off until tested), OnlineBoxProbe=%d (log only)", klbf_ot_bwalk, klbf_ot_board, klbf_ot_bprobe);
    if (klbf_ot) klog("botfill: OnlineTactics van/late: OnlineVanState=%d (recommended on), OnlineLateExit=%d s (recommended 75; 0 = off)", klbf_ot_vstate, klbf_ot_late);
    if (klbf_ot) klog("botfill: OnlineTactics extras: OnlineHealthMul=%d (recommended 5 with OnlineCopToBot 5 = stock Arcade level 1 survival; 1 = off), OnlineTacticsGuard=%.0f m (recommended 25; 0 = off), OnlineTacticsVan=%d (recommended on)",
                      klbf_ot_hmul, klbf_ot_guard / 100, klbf_ot_van);
    if (klbf_ot) klog("botfill: OnlineTactics=1 - the HOST gives the Ally bots loot/van orders itself (puppeteer, host tally only; Carry %d, Near %.0f, Take %d)", klbf_ot_carry, klbf_ot_near, klbf_ot_take);
    else if (GetPrivateProfileIntA("BotFill", "OnlineTactics", 0, klh_ini)) klog("botfill: OnlineTactics=1 ignored: it needs [BotFill] OnlineHost=1");
    if (klbf_oh) klog("botfill: OnlineHost=1 - the HOST is the only authority over the Ally bots: it shares their places (klsync.c Share), a client mirrors them (Puppet, team 2) and owns none; it activates NOTHING (the level must keep the squads online: tools/kl_botsonline.py zip)");
    if (klbf_on) klog("botfill: OnlineFill=1 - plan and probe lines for the empty lobby seats (read-only; Ready may start below the lobby target)");
}

/* ------------------------------------------------------------------------------------------------------------------------------
 * [BotFill] OnlineTactics=1 (default 0): THE PUPPETEER. HOST only (session role 2, Arcade-like round state 0x19); a client never runs it.
 * Online the game builds no ZLootTactic / ZBoardEscapeVehicleTactic / ZBecomeTraitorTactic for the Ally bots (0x7f6850 is false for roles
 * 2/3) and has no ZGameRulesHeist, so no crew record. This module gives them orders instead, with the soldier's own order routine
 * 0x760e50 (klescort.c's kle_order2; a temporary entry with rec -1, so the OrderGap debounce never applies), and keeps its OWN tally:
 *   phase 0 pick the nearest unclaimed ZOnlineMoneyCtrl (vtable 0xbc874c, from the game's object registry 0xe09e38: online there is no rules list, and BO4 found none in the entity table) -> phase 1
 *   phase 1 walk there; within Near (horizontal; |dy| <= 400) = grabbed: tally += [obj+0x34]; the object is claimed (no other bot picks it)
 *   after Carry grabs, or when no stack is left, -> phase 2: walk to the escape van (ZAnimatedVehicle 0xbcc0b4, its node's place)
 *   phase 3 within 2*Near of the van = 'boarded' (log only; NOTHING is removed or credited in the game)
 * NOT done (GUESS/open): nothing is replicated to clients (UDP 27415 events are not sent), the stock round money / score / end screen are
 * not touched, a boarded bot stays a plain actor. TakeWrite ([BotFill] OnlineTacticsTake=1, GUESS): also writes 0 to [obj+0x34] on the host.
 * Log: 'botfill: tactics: bot N ...' once per bot at its first order, one line per grab / boarding / timeout, and a round summary.
 * ---------------------------------------------------------------------------------------------------------------------------- */
#define KLBF_OT_BOTS   16
#define KLBF_OT_OBJ    256
#define KLBF_OT_STALL  12000      /* ms without 2 m of progress toward its stack before a bot gives it up (BO5: a fixed 25 s gave up 5 of 6 walks of 90-110 m that were still closing) */
#define KLBF_OT_STALLMAX 90000    /* ms a bot may take for one stack at most, progress or not */
#define KLBF_OT_REORD  6000       /* ms between repeats of the same order (the game's chain may overwrite it) */
#define KLBF_OT_GUARDWAIT 30000   /* ms a bot holds while every free stack is guarded (OnlineTacticsGuard) before it takes the nearest guarded one */

static struct { DWORD actor, target; int phase, grabs, tally; DWORD since, ordered; int told; float best; DWORD bestAt, idleAt, pAt, vidleAt, outAt, nearAt; int leg; DWORD legAt; } klbf_ob[KLBF_OT_BOTS];
static DWORD klbf_ot_claimed[KLBF_OT_OBJ], klbf_ot_bad[KLBF_OT_OBJ], klbf_ot_badAt[KLBF_OT_OBJ]; static int klbf_ot_nclaim, klbf_ot_nbad, klbf_ot_rounds, klbf_ot_sm;
static DWORD klbf_ot_last;
/* OnlineWaypoints (recommended on): [BotFillWay_<SLOT>] P1..P8 = "x y z" (floats, y = height). The phase-2 exit walk (the exit-trigger goal only, not van/box walks) goes through these in order.
   <SLOT> = the slot name from the engine's scene path (klh_scene -> klh_level_key: 'f02\f02_main' -> F02). That is what the hook reliably knows: a stock map installed through KLExpansion
   plays as its slot (DD02 as F02), so the key is the slot, not the map's own name. GUESS: two expansion maps sharing a slot share a section; the section is only used for the one that needs it. */
#define KLBF_WAY_MAX 8
#define KLBF_WAY_NEAR 300.0f      /* horizontal units (3 m) within which a leg point counts as reached (owner spec) */
#define KLBF_WAY_LEGMS 15000      /* ms per leg at most (owner spec) */
static float klbf_way_p[KLBF_WAY_MAX][3]; static int klbf_way_n; static char klbf_way_sec[40];
static void klbf_way_load(void)
{
    char scene[200], key[120], line[120], nm[8]; int i;
    klbf_way_n = 0; klbf_way_sec[0] = 0;
    if (!klbf_ot_way || !klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    strcpy(klbf_way_sec, "BotFillWay_");
    for (i = 0; key[i] && key[i] != 0x5c && i < 20; i++) klbf_way_sec[11 + i] = (char)(key[i] >= 'a' && key[i] <= 'z' ? key[i] - 32 : key[i]);
    klbf_way_sec[11 + i] = 0;
    for (i = 1; i <= KLBF_WAY_MAX; i++) {
        char *c; float x, y, z;
        snprintf(nm, sizeof nm, "P%d", i);
        line[0] = 0; GetPrivateProfileStringA(klbf_way_sec, nm, "", line, sizeof line, klh_ini);
        for (c = line; *c; c++) if (*c == ',' || *c == ';' || *c == '(' || *c == ')') *c = ' ';
        if (sscanf(line, "%f %f %f", &x, &y, &z) != 3) break;      /* the first missing / bad key ends the list */
        klbf_way_p[klbf_way_n][0] = x; klbf_way_p[klbf_way_n][1] = y; klbf_way_p[klbf_way_n][2] = z; klbf_way_n++;
    }
    if (klbf_way_n) {
        klog("botfill: tactics: OnlineWaypoints: [%s] has %d point(s) for the exit walk (slot key '%s')", klbf_way_sec, klbf_way_n, key);
        for (i = 0; i < klbf_way_n; i++) klog("botfill: tactics: OnlineWaypoints: leg %d = (%.0f, %.0f, %.0f)", i + 1, klbf_way_p[i][0], klbf_way_p[i][1], klbf_way_p[i][2]);
    } else klog("botfill: tactics: OnlineWaypoints: no [%s] section for this level: exit walk unchanged", klbf_way_sec);
}
/* first leg still AHEAD of a bot at p (BOS_DD02c: after a give-up on the deck the re-order began again at leg 1 and walked the bots back down the ramp): the first point
   that lies nearer the exit box (horizontally) than the bot does by more than KLBF_WAY_NEAR; klbf_way_n (= no legs left) when the bot is past them all.
   GUESS: the legs run toward the exit, each nearer to it than the one before (true for the DD02 route; a winding route would need a smarter test) */
static int klbf_way_start(const float p[3], const float exitp[3])
{
    float bd = (p[0] - exitp[0]) * (p[0] - exitp[0]) + (p[2] - exitp[2]) * (p[2] - exitp[2]), wd; int i;
    bd = (float)sqrt(bd) - KLBF_WAY_NEAR;
    for (i = 0; i < klbf_way_n; i++) {
        wd = (float)sqrt((klbf_way_p[i][0] - exitp[0]) * (klbf_way_p[i][0] - exitp[0]) + (klbf_way_p[i][2] - exitp[2]) * (klbf_way_p[i][2] - exitp[2]));
        if (wd < bd) return i;
    }
    return klbf_way_n;
}

/* OnlineRampFire (recommended on; OnlineRampDry=1 default = log only until proven live). 2026-10-26, stock DD02 (slot F02): TriggerBox_make_the_ramp (node 15776, one-shot, centre (3,5846,-10822),
   half (2400,1200,10809)) builds the ramp when a COUNTED player is inside; online bots are not counted (rule 0x7f6850 false online), so it never fires unless a human goes there. In Arcade the first
   bot above y 4646 fires it. Here the host does what Arcade's rule would: when an online bot stands inside the box, call the trigger's fire routine 0x45f5d0 (ZTriggerBox vtable 0xbc232c slot 34,
   thiscall, 0 stack args, exactly klclubholster.c) ONCE. Section [BotFillRamp_<SLOT>]: Name (substring, default make_the_ramp), Centre "x y z", Half "x y z". No section = nothing happens (logged once).
   UNSYNCED: 0x45f5d0 runs on the host only; clients may not see the ramp build (GUESS, unproven; 0x6ae730, the sync path, is NOT used: unproven). Log lines start 'botfill: ramp:'. */
#define KLBF_RAMP_VT   0x00bc232c
#define KLBF_RAMP_FIRE 0x0045f5d0
#define KLBF_RAMP_PROBEMS 5000      /* ms after the round's first tick before the first private-memory probe (then every 20 s, 3 a round, until a candidate) */
#define KLBF_RAMP_CAND 4
static struct { int loaded, have, probed, fired, ncand; DWORD t0, cand[KLBF_RAMP_CAND]; float c[3], h[3]; char name[48], sec[40]; } klbf_rp;
static int klbf_rp_best;
static void klbf_ramp_load(void)
{
    char scene[200], key[120], line[120], *c; int i; float v[3];
    memset(&klbf_rp, 0, sizeof klbf_rp); klbf_rp_best = 0;      /* t0 = 0: set by the first klbf_ramp_tick of the round */
    if (!klbf_ot_ramp || !klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    strcpy(klbf_rp.sec, "BotFillRamp_");
    for (i = 0; key[i] && key[i] != 0x5c && i < 20; i++) klbf_rp.sec[12 + i] = (char)(key[i] >= 'a' && key[i] <= 'z' ? key[i] - 32 : key[i]);
    klbf_rp.sec[12 + i] = 0;
    GetPrivateProfileStringA(klbf_rp.sec, "Name", "make_the_ramp", klbf_rp.name, sizeof klbf_rp.name, klh_ini);
    line[0] = 0; GetPrivateProfileStringA(klbf_rp.sec, "Centre", "", line, sizeof line, klh_ini);
    for (c = line; *c; c++) if (*c == ',' || *c == ';' || *c == '(' || *c == ')') *c = ' ';
    if (sscanf(line, "%f %f %f", &v[0], &v[1], &v[2]) != 3) { klog("botfill: ramp: no usable Centre in [%s] (slot key '%s'): ramp fire does nothing on this map", klbf_rp.sec, key); return; }
    memcpy(klbf_rp.c, v, 12);
    line[0] = 0; GetPrivateProfileStringA(klbf_rp.sec, "Half", "", line, sizeof line, klh_ini);
    for (c = line; *c; c++) if (*c == ',' || *c == ';' || *c == '(' || *c == ')') *c = ' ';
    if (sscanf(line, "%f %f %f", &v[0], &v[1], &v[2]) != 3 || v[0] <= 0 || v[1] <= 0 || v[2] <= 0) { klog("botfill: ramp: no usable Half in [%s]: ramp fire does nothing on this map", klbf_rp.sec); return; }
    memcpy(klbf_rp.h, v, 12);
    klbf_rp.have = 1;
    klog("botfill: ramp: [%s] name '%s' centre (%.0f, %.0f, %.0f) half (%.0f, %.0f, %.0f), %s", klbf_rp.sec, klbf_rp.name, klbf_rp.c[0], klbf_rp.c[1], klbf_rp.c[2], klbf_rp.h[0], klbf_rp.h[1], klbf_rp.h[2], klbf_ot_rampdry ? "DRY (log only)" : "LIVE");
}

/* the entity name path [[obj+4]+0x6c] (a C string): klclubholster.c's GUESS, never proven for ZTriggerBox; b gets "" when unreadable */
static void klbf_ramp_name(DWORD obj, char b[40])
{
    DWORD n = klh_rd32(obj + 4), s; int i;
    b[0] = 0;
    if (!n || !(s = klh_rd32(n + 0x6c)) || s < 0x10000) return;
    for (i = 0; i < 39; i++) { if (!klh_rd(s + i, b + i, 1)) { b[0] = 0; return; } if (!b[i]) return; }
    b[39] = 0;
}

/* ~5 s after the first tick of the round (also when Dry; BOS_DD02r: the entity-table walk klch_panic uses found 0 ZTriggerBox, so this is now klmove.c's PROVEN
   exit-trigger method): scan the private RW memory for the ZTriggerBox vtable, keep objects whose +0x24 entity has a vtable in the image, and read the box place
   from that entity's node (kle_node) as klbotfill does for the exit trigger. GUESS: ZTriggerBox keeps its entity at +0x24 like ZOnlineExitLevelTrigger (a trigger
   subclass). A candidate = node within 50 units of Centre, or the name GUESS [[obj+4]+0x6c] contains Name. A miss is retried 20 s later, 3 probes a round. */
static void klbf_ramp_probe(void)
{
    static BYTE buf[0x10000]; MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; DWORD total = 0, withent = 0, byname = 0, bycent = 0, t0 = GetTickCount();
    klbf_rp.probed++; klbf_rp.ncand = 0; klbf_rp_best = 0;
    while ((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            SIZE_T o, j;
            for (o = 0; o < mbi.RegionSize; o += sizeof buf) {
                SIZE_T n = mbi.RegionSize - o < sizeof buf ? mbi.RegionSize - o : sizeof buf;
                if (!klh_rd((DWORD_PTR)mbi.BaseAddress + o, buf, n)) continue;
                for (j = 0; j + 4 <= n; j += 4) {
                    DWORD at, ent, evt, node; float np[3] = {0, 0, 0}; char nm[40]; int nmatch, cen;
                    if (*(DWORD *)(buf + j) != (DWORD)KLBF_RAMP_VT) continue;
                    at = (DWORD)((DWORD_PTR)mbi.BaseAddress + o + j); total++;
                    if (!(ent = klh_rd32(at + 0x24)) || !(evt = klh_rd32(ent)) || evt < img_lo || evt >= img_hi) continue;      /* an object of the game with an entity (klmv_exit_vehicle's test) */
                    withent++;
                    cen = (node = klh_rd32(ent + 4)) && kle_node(node, np, 0) && fabsf(np[0] - klbf_rp.c[0]) <= 50.0f && fabsf(np[1] - klbf_rp.c[1]) <= 50.0f && fabsf(np[2] - klbf_rp.c[2]) <= 50.0f;
                    klbf_ramp_name(at, nm);
                    nmatch = nm[0] && klbf_rp.name[0] && strstr(nm, klbf_rp.name) != 0;
                    if (nmatch) byname++;
                    if (cen) bycent++;
                    if (nmatch || cen) {      /* rank: name+centre 3 > centre 2 > name 1; cand[0] is always the best seen, the log is capped */
                        int sc = nmatch && cen ? 3 : cen ? 2 : 1;
                        if (!klbf_rp.ncand || sc > klbf_rp_best) { klbf_rp.cand[0] = at; klbf_rp_best = sc; }
                        if (klbf_rp.ncand < KLBF_RAMP_CAND) {
                            if (klbf_rp.ncand) klbf_rp.cand[klbf_rp.ncand] = at;
                            klog("botfill: ramp: candidate %d: obj %08lx entity %08lx node at (%.0f, %.0f, %.0f) name '%s'%s%s, [+0x38]=%08lx [+0x40]=%08lx [+0x6c]=%08lx", klbf_rp.ncand, (unsigned long)at, (unsigned long)ent, np[0], np[1], np[2], nm,
                                 nmatch ? " (NAME MATCH)" : "", cen ? " (CENTRE MATCH)" : "", (unsigned long)klh_rd32(at + 0x38), (unsigned long)klh_rd32(at + 0x40), (unsigned long)klh_rd32(at + 0x6c));
                        }
                        klbf_rp.ncand++;
                    }
                }
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    klog("botfill: ramp: probe %d: %lu ZTriggerBox vtable hit(s) in private memory, %lu with a game entity, %lu match name '%s', %lu match centre (node within 50 units), %d candidate(s), %lu ms%s", klbf_rp.probed,
         (unsigned long)total, (unsigned long)withent, (unsigned long)byname, klbf_rp.name, (unsigned long)bycent, klbf_rp.ncand, GetTickCount() - t0, klbf_rp.ncand ? "" : klbf_rp.probed < 3 ? " - nothing to fire yet, probed again in 20 s" : " - NOTHING TO FIRE this round");
}

/* host, in a round (state 0x19), game thread, once a second: bp = the live Ally bots' feet (nb of them) */
static void klbf_ramp_tick(DWORD now, float bp[][3], int nb)
{
    int b;
    if (!klbf_ot_ramp || !klbf_rp.have || klbf_rp.fired) return;
    if (!klbf_rp.t0) klbf_rp.t0 = now;      /* BOS_DD02r: the load stamp came from the level load, so the probe ran 12 ms into the round; the clock now starts at the first tick */
    if (!klbf_rp.ncand) { if (klbf_rp.probed < 3 && now - klbf_rp.t0 >= KLBF_RAMP_PROBEMS + (DWORD)klbf_rp.probed * 20000) klbf_ramp_probe(); return; }
    for (b = 0; b < nb; b++) {
        float *q = bp[b];
        if (fabsf(q[0] - klbf_rp.c[0]) > klbf_rp.h[0] || fabsf(q[1] - klbf_rp.c[1]) > klbf_rp.h[1] || fabsf(q[2] - klbf_rp.c[2]) > klbf_rp.h[2]) continue;
        {   DWORD o = klbf_rp.cand[0];
            klbf_rp.fired = 1;      /* once per round, also when Dry */
            if (klh_rd32(o) != (DWORD)KLBF_RAMP_VT) { klog("botfill: ramp: bot %d at (%.0f, %.0f, %.0f) is inside the box but candidate %08lx is no ZTriggerBox any more: nothing fired", b, q[0], q[1], q[2], (unsigned long)o); return; }
            /* GUESS: no safe test on [obj+0x40] (meaning unknown; it is only logged); the one-shot is our own 'fired' flag */
            if (klbf_ot_rampdry) { klog("botfill: ramp: DRY would fire 0x45f5d0 on %08lx ([+0x40]=%08lx): bot %d at (%.0f, %.0f, %.0f) is inside the box", (unsigned long)o, (unsigned long)klh_rd32(o + 0x40), b, q[0], q[1], q[2]); return; }
            klog("botfill: ramp: FIRE 0x45f5d0 on %08lx ([+0x40]=%08lx): bot %d at (%.0f, %.0f, %.0f) is inside the box (host only: clients may not see the ramp build, GUESS)", (unsigned long)o, (unsigned long)klh_rd32(o + 0x40), b, q[0], q[1], q[2]);
            KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLBF_RAMP_FIRE)(o, 0);
            return;
        }
    }
}

/* OnlineHealthMul (2026-10-26, workflow wg4n9od9h, BO5): online the cops' damage on the Ally bots skips Arcade's damage table. 0x61a980 (ZFFActor hit)
   calls 0x7f6850 at 0x61acf1, which is false for session roles 2/3, so 0x591b60's police->crew factor (stock level 1: 0.01; the owner's klbalance
   CopToCrew 0.05) is never applied, and BO5's bots went 280 -> 0 inside one 3 s sync window. The game call can't be reached online (0x591b60 reads
   Heist-only rules fields), so each bot's health object [actor+0x5fc] gets max and current x K once (klgrudge.c kly_health's checks): data writes only.
   Side effect: the human's damage on a bot is divided by K too (Arcade has YouToCrew 0.25). Host only; whether a client's puppet follows is NOT known. */
#define KLBF_OT_HP 32
static struct { DWORD h, actor; float orig, wrote; } klbf_hp[KLBF_OT_HP];
static void klbf_ot_health(DWORD a, DWORD h, const float hv[2])
{
    int i, f = -1; float nv[2];
    if (klbf_ot_hmul <= 1) return;
    for (i = 0; i < KLBF_OT_HP; i++) if (klbf_hp[i].h == h && klbf_hp[i].actor == a) break;
    if (i < KLBF_OT_HP && hv[1] == klbf_hp[i].wrote) return;      /* ours, still in place */
    if (klh_rd32(h + 0x24) != a || !klb_finite(hv[0]) || !klb_finite(hv[1]) || hv[1] < 1.0f || hv[1] > 100000.0f || hv[0] > hv[1] * 1.01f + 1.0f || !(hv[0] > 0)) return;
    if (i == KLBF_OT_HP) {      /* a new object, or a maximum that is not ours: taken as the game's. Review wp16tqkg2: a full table reuses only a slot that is no longer ours, else skips */
        float m = 0;
        for (i = 0; i < KLBF_OT_HP && klbf_hp[i].h; i++) ;
        for (f = 0; i == KLBF_OT_HP && f < KLBF_OT_HP; f++) if (klh_rd32(klbf_hp[f].h + 0x24) != klbf_hp[f].actor || !klh_rd(klbf_hp[f].h + 8, &m, 4) || m != klbf_hp[f].wrote) i = f;
        if (i == KLBF_OT_HP) return;
    }
    f = i; nv[0] = hv[0] * klbf_ot_hmul; nv[1] = hv[1] * klbf_ot_hmul;
    klh_data((void *)(DWORD_PTR)(h + 8), &nv[1], 4, "bot health max (OnlineHealthMul)");
    klh_data((void *)(DWORD_PTR)(h + 4), &nv[0], 4, "bot health (OnlineHealthMul)");
    klbf_hp[f].h = h; klbf_hp[f].actor = a; klbf_hp[f].orig = hv[1]; klbf_hp[f].wrote = nv[1];
    klog("botfill: tactics: bot actor %08lx health %.0f/%.0f -> %.0f/%.0f (OnlineHealthMul %d: Arcade's police->crew damage factor is not applied online)", a, hv[0], hv[1], nv[0], nv[1], klbf_ot_hmul);
}

/* OnlineTacticsVan (2026-10-26, workflow wg4n9od9h, verified in disassembly by a second pass): online the exit box (ZOnlineExitLevelTrigger 0x6c3d50)
   hands its vehicle to rules slot 44, which on the host's ZGameRulesFragileAllianceSv (vtable 0xbd2eb4) is 0x4d85e0: it takes PLAYERS only (type test
   0x4d8610..1e, exit 0x4d86ce), so a bot in the box never calls the van, and BO5's van stayed at the origin all round. 0x4d85e0 then calls
   0x71e180(rules, vehicle, 0) - the Sv twin of Arcade's 0x8154f0 - and this makes that same call for the bots, once a round, when a bot with
   money stands within 2*Near of the exit trigger. Preconditions as 0x4d85e0 / 0x6c3d50: Sv vtable, [rules+0x1dc] 0 (no vehicle under way),
   [rules+0x372] 0 (last not flagged), [rules+0x1ee] 0. NOT done: 0x4d85e0's player-only side effects ([rec+0x390] |= 4, 0x8b6c60). GUESS: the
   trigger's node is its box (the walk goal); the vehicle handle is the trigger's first field of +0x48..+0x54 (klmove.c klmv_exit_vehicle). */
#define KLBF_SV_VT     0x00bd2eb4
#define KLBF_SV_CALLVEH 0x0071e180
static DWORD klbf_ot_trig, klbf_ot_tvt, klbf_ot_vh, klbf_ot_lookAt; static int klbf_ot_trig_looked, klbf_ot_called, klbf_ot_looks; static float klbf_ot_tpos[3];
static int klbf_ot_call_van(DWORD rules, int who)
{
    static const BYTE head[16] = { 0x56, 0x8b, 0xf1, 0x80, 0xbe, 0xdc, 0x01, 0x00, 0x00, 0x00, 0x0f, 0x85, 0xb7, 0x00, 0x00, 0x00 };      /* 0x71e180 */
    static DWORD tried; static int told;
    BYTE veh = 1, last = 1, hold = 1; float clk = 0, tp[3]; DWORD ent, node, now = GetTickCount();
    if (klbf_ot_called) return 0;
    if (tried && now - tried < 5000) return 0;      /* review wp16tqkg2: a refusal (vehicle under way, hold) is retried every 5 s, not spent for the round */
    tried = now;
    /* OnlineVanCall (BO8c): klroundkeep.c swaps in a private heap vtable copy (slots 42/193 only; slot 44 and 0x71e180 stay stock), so the strict 0xbd2eb4 compare failed and spent the call. Accept the copy (KLH_RULES_SV_OK); a mismatch is logged once and retried, never spent. */
    { DWORD vt = klh_rd32(rules); int vok = klbf_ot_vcall ? KLH_RULES_SV_OK(vt) : vt == (DWORD)(DWORD_PTR)KLH_VA(KLBF_SV_VT);
      if (!vok || !klb_same_code(KLBF_SV_CALLVEH, head, sizeof head)) { static int vtold; if (!vtold++) klog("botfill: tactics: van: the rules object (vtable %08lx, vok %d) or 0x71e180 is not the one this build knows: not called, retried every 5 s", vt, vok); return 0; } }
    /* the trigger is a private-memory scan hit: it must still be the same trigger, with its entity and node, right before its handle is used */
    if (klh_rd32(klbf_ot_trig) != klbf_ot_tvt || !(ent = klh_rd32(klbf_ot_trig + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, tp, 0) || !klbf_ot_vh) {
        klog("botfill: tactics: van: exit trigger %08lx is no longer valid (vtable %08lx, handle %08lx): looked up again", klbf_ot_trig, klh_rd32(klbf_ot_trig), klbf_ot_vh);
        klbf_ot_vh = 0; klbf_ot_trig_looked = 0; return 0;
    }
    if (!klh_rd(rules + 0x1dc, &veh, 1) || !klh_rd(rules + 0x372, &last, 1) || !klh_rd(rules + 0x1ee, &hold, 1) || !klh_rd32(rules + 0x2c)) return 0;
    /* review wp16tqkg2: 0x71e180 with flag 0 flags the vehicle LAST when the clock [rules+0x4c] is near its end (0x71e1d0..213), which ends the round for humans not aboard: same 20 s gate as klmv_bot_van */
    if (!klh_rd(rules + 0x4c, &clk, 4) || !klb_finite(clk) || clk < 20.0f) { klbf_ot_called = 1; klog("botfill: tactics: van: bot %d is at the exit but the clock is %.1f s (< 20 s): not called, so the round's end stays the humans'", who, clk); return 0; }
    if (veh || last || hold) { if (!told++) klog("botfill: tactics: van: bot %d is at the exit, but a vehicle is under way or held (state %u, last %u, hold %u): not called yet, retried every 5 s", who, veh, last, hold); return 0; }
    klbf_ot_called = 1; klbf_ot_calledAt = now; told = 0;
    ((void (__fastcall *)(void *, void *, DWORD, int))(DWORD_PTR)KLH_VA(KLBF_SV_CALLVEH))((void *)(DWORD_PTR)rules, 0, klbf_ot_vh, 0);
    veh = last = 0; klh_rd(rules + 0x1dc, &veh, 1); klh_rd(rules + 0x372, &last, 1);
    klog("botfill: tactics: van: bot %d is at the exit trigger %08lx with money: vehicle %08lx CALLED (0x71e180, as rules slot 44 does for a player; clock %.1f): state now %u, last %u, [rules+0x1e4] %08lx",
         who, klbf_ot_trig, klbf_ot_vh, clk, veh, last, klh_rd32(rules + 0x1e4));
    return 1;
}

/* OnlineBoxWalk / OnlineBoard (2026-10-26, from the 1026za research, static reading of kl2.exe; NOT run live). Arcade bots board through ZAllyEscapeBox
   (vtable 0xbc7f6c, update 0x907a50): box + crew record + rules slot 45, all gated on Arcade state (0x7f6850 false for session roles 2/3, 0x508ef0 null, Sv slot 45
   0x6c6c10 takes players only), so no stock hop can run online. What CAN be done with game calls and data: (1) walk the bots to the BOX (not the exit trigger, which
   lies ~570 cm from the DM01 box, BO9 vs build/r_tab/DM01/bots.txt) once the van is called; (2) decide inside = the game's own 0x758cb0(box, actor) (klmove.c KLMV_INSIDE,
   geometry only, ret 4); (3) OnlineBoard: call 0x89c890(actor) (__thiscall, no args, plain ret) = what 0x907a50 does for a boarded bot: 0x8d2e20(squad, 0) on the bot's one-man
   squad hides/removes it. No role gate in either (read). NOT done: [actor+0x8f0] (squad living count, fed/hunt only), crew records, money (the host tally stays the tally).
   GUESS ~60%: 0x89c890 behaves online on the host; GUESS ~35%: the clients' puppets vanish too (KLSY2 records may keep it standing). Read-only scan of the private memory for
   the stock vtable (nothing is wrapped: klmove.c's BoardNear is Arcade-only). */
#define KLBF_BX_MAX 8
#define KLBF_BX_BOARD 0x0089c890      /* void __thiscall (actor): squad removal for an escaped bot */
#define KLBF_BX_SQUAD 0x008d2e20      /* its callee, head checked only */
static struct { DWORD at, ent; } klbf_bx[KLBF_BX_MAX]; static int klbf_ot_nbx, klbf_ot_bxlooks, klbf_ot_bxbest = -1; static DWORD klbf_ot_bxAt;
/* the frame of box i (re-read each time; the object is checked to still be the box we found) */
static int klbf_ot_box_frame(int i, struct klmv_fr *f)
{
    if (i < 0 || i >= klbf_ot_nbx || !klbf_bx[i].at || klh_rd32(klbf_bx[i].at) != KLMV_ALLY_VT || klh_rd32(klbf_bx[i].at + 0x24) != klbf_bx[i].ent) return 0;
    return klmv_frame(klbf_bx[i].ent, f);
}
static void klbf_ot_boxscan(DWORD now)
{
    static BYTE buf[0x10000]; MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; DWORD t0 = GetTickCount(); int i; float bd = 1e30f;
    klbf_ot_bxAt = now; klbf_ot_bxlooks++; klbf_ot_nbx = 0; klbf_ot_bxbest = -1;
    while ((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            SIZE_T o, j;
            for (o = 0; o < mbi.RegionSize; o += sizeof buf) {
                SIZE_T n = mbi.RegionSize - o < sizeof buf ? mbi.RegionSize - o : sizeof buf;
                if (!klh_rd((DWORD_PTR)mbi.BaseAddress + o, buf, n)) continue;
                for (j = 0; j + 4 <= n; j += 4) {
                    DWORD at, ent, evt, node; float p[3];
                    if (*(DWORD *)(buf + j) != KLMV_ALLY_VT || klbf_ot_nbx >= KLBF_BX_MAX) continue;
                    at = (DWORD)((DWORD_PTR)mbi.BaseAddress + o + j);
                    if (!(ent = klh_rd32(at + 0x24)) || !(evt = klh_rd32(ent)) || evt < img_lo || evt >= img_hi || !(node = klh_rd32(ent + 4)) || !kle_node(node, p, 0)) continue;      /* as klmv_scan: a real one has its entity at +0x24 */
                    klbf_bx[klbf_ot_nbx].at = at; klbf_bx[klbf_ot_nbx].ent = ent; klbf_ot_nbx++;
                }
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    for (i = 0; i < klbf_ot_nbx; i++) {      /* the box the bots walk to: the one nearest the exit trigger (GUESS: the van's boarding box is beside the trigger; any box takes a bot aboard in the stock rule) */
        struct klmv_fr f; float d;
        if (!klbf_ot_box_frame(i, &f)) continue;
        d = klbf_ot_vh ? kle_dist(f.T, klbf_ot_tpos) : 0;
        klog("botfill: tactics: box %d: ZAllyEscapeBox %08lx entity %08lx centre (%.0f, %.0f, %.0f), %s half (%.0f, %.0f, %.0f), %.0f m from the exit trigger", i, klbf_bx[i].at, klbf_bx[i].ent, f.T[0], f.T[1], f.T[2], f.box ? "BOX" : "POINT (no box primitive)", f.half[0], f.half[1], f.half[2], d / 100);
        if (d < bd) { bd = d; klbf_ot_bxbest = i; }
    }
    klog("botfill: tactics: box scan: %d ZAllyEscapeBox object(s) in %lu ms, bots will walk to box %d%s", klbf_ot_nbx, GetTickCount() - t0, klbf_ot_bxbest, klbf_ot_nbx ? "" : " (none: the bots stay at the exit trigger as before; retried 3 more times)");
}
/* is the bot inside the box: the game's own test 0x758cb0 when its head is the one read, else the frame's distance */
static int klbf_ot_inside(int bi, const struct klmv_fr *f, DWORD actor, const float pos[3], int *byGame)
{
    static const BYTE head[16] = { 0x83, 0xec, 0x10, 0xd9, 0xee, 0x56, 0x57, 0xd9, 0x54, 0x24, 0x14, 0x8b, 0x7c, 0x24, 0x1c, 0xd9 };      /* 0x758cb0 */
    if (klb_same_code(KLMV_INSIDE, head, sizeof head)) { *byGame = 1; return ((char (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLMV_INSIDE))((void *)(DWORD_PTR)klbf_bx[bi].at, 0, actor) != 0; }
    *byGame = 0; return f->box && klmv_fr_dist(f, pos) <= 0;
}
/* OnlineBoard: 0x907a50's own removal of a boarded bot, nothing else of it. 1 = called. */
static int klbf_ot_board_call(DWORD actor)
{
    static const BYTE h1[16] = { 0x81, 0xec, 0x80, 0x00, 0x00, 0x00, 0x56, 0x8b, 0xf1, 0x8b, 0x86, 0x7c, 0x07, 0x00, 0x00, 0x85 };      /* 0x89c890 */
    static const BYTE h2[16] = { 0x55, 0x8b, 0xec, 0x51, 0x53, 0x56, 0x57, 0x8b, 0xf9, 0x8b, 0x8f, 0xa4, 0x01, 0x00, 0x00, 0x85 };      /* 0x8d2e20 */
    DWORD sol;
    if (!klb_same_code(KLBF_BX_BOARD, h1, sizeof h1) || !klb_same_code(KLBF_BX_SQUAD, h2, sizeof h2) || klh_avt(actor) != 0x00bb3bac) return 0;
    if (!(sol = klh_rd32(actor + 0x77c)) && !(sol = klh_rd32(actor + 0x780))) return 0;      /* 0x89c890 would int3 on both null (0x89c8b7) */
    if (!klh_rd32(sol + 0x4f4)) return 0;      /* no squad: it does nothing */
    ((void (__fastcall *)(void *))(DWORD_PTR)KLH_VA(KLBF_BX_BOARD))((void *)(DWORD_PTR)actor);
    return 1;
}

static int klbf_ot_has(const DWORD *a, int n, DWORD v) { int i; for (i = 0; i < n; i++) if (a[i] == v) return 1; return 0; }
/* a given-up stack: blacklisted for the round (OnlineGiveUpRetry off) or for OnlineGiveUpRetryS seconds from the give-up (on) */
static int klbf_ot_isbad(DWORD v, DWORD now) { int i; for (i = 0; i < klbf_ot_nbad; i++) if (klbf_ot_bad[i] == v && (!klbf_ot_retry || now - klbf_ot_badAt[i] < (DWORD)klbf_ot_retryS * 1000u)) return 1; return 0; }

/* OnlineBoxProbe (log only): where the van really is, for the next BO run. BO9: the ZAnimatedVehicle node stays at (0,0,0); GUESS: its group [rules+0x1e4] or the boarding object [rules+0x1e0] carries the place */
static void klbf_ot_vprobe(DWORD rules, int vstate)
{
    DWORD g = klh_rd32(rules + 0x1e4), bo = klh_rd32(rules + 0x1e0), n; float gp[3] = { 0, 0, 0 }, bp[3] = { 0, 0, 0 }; int gv = 0, bv = 0; struct klmv_fr f; float bd = -1;
    if (g && (n = klh_rd32(g + 4))) gv = kle_node(n, gp, 0);
    if (bo && (n = klh_rd32(bo + 4))) bv = kle_node(n, bp, 0);
    if (bv && klbf_ot_box_frame(klbf_ot_bxbest, &f)) bd = kle_dist(f.T, bp);
    klog("botfill: tactics: van probe: state %d, group [+0x1e4] %08lx at %s(%.0f, %.0f, %.0f), boarding object [+0x1e0] %08lx at %s(%.0f, %.0f, %.0f), %.0f m from the chosen box centre (-1 = unknown)", vstate, g, gv ? "" : "NONE ", gp[0], gp[1], gp[2], bo, bv ? "" : "NONE ", bp[0], bp[1], bp[2], bd < 0 ? -1.0f : bd / 100);
}

/* OnlineVanGather (2026-10-26, BO11): the carrier reached the exit and called the van at once; the other bots were 28-41 m from the box and none boarded. Now the first bot at the exit only
   STARTS the gather: every living bot walks to the box (also the ones still on a stack), and the van is called when all walking bots are within GatherM of the box centre, or GatherMaxS
   seconds have passed, or the clock is at or below OnlineLateExit + 20 s. Calls and orders only (the call is klbf_ot_call_van's, unchanged). */
static int klbf_ot_gat, klbf_ot_gcar, klbf_ot_gtold; static DWORD klbf_ot_gatAt;
static void klbf_ot_arrive(DWORD rules, int s, DWORD now)
{
    if (!klbf_ot_vgather) { klbf_ot_call_van(rules, s); return; }
    if (klbf_ot_gat) return;
    klbf_ot_gat = 1; klbf_ot_gatAt = now; klbf_ot_gcar = s; klbf_ot_gtold = 0;
    klog("botfill: tactics: van: gather: bot %d reached the exit trigger %08lx; every living bot walks to the box now and the van is called when all are within %.0f m of it, after %d s at the latest (OnlineVanGather)", s, klbf_ot_trig, klbf_ot_gm / 100, klbf_ot_gmax);
}
/* the walk goal: the chosen box's centre (OnlineBoxWalk), else the exit trigger's place */
static int klbf_ot_goal(float c[3])
{
    struct klmv_fr f;
    if (klbf_ot_bwalk && klbf_ot_box_frame(klbf_ot_bxbest, &f)) { memcpy(c, f.T, 12); return 1; }
    if (klbf_ot_vh) { memcpy(c, klbf_ot_tpos, 12); return 1; }
    return 0;
}

/* OnlineVanHold (2026-10-26, research re/van_hold_online.md, static; NOT run live). BO11: the van waited in state 3, then went 6 after 1 s: it was shot while empty (health 2730, 976, 0; the AI heisters
   are no [rules+8] records online, so the box looks empty to the game) and [VanBlow] EmptyDelay blows an empty van on purpose. While [rules+0x1dc] is 3 and a walking bot is within HoldM of the box:
   the van's 'Invulnerable' byte (+0x21, klescort.c KLE_VEH_INV) is set to 1 and VanBlow's empty clock is paused (kle_vh_hold); within HoldNearM the state timer [rules+0x1d8] is kept at 3.0 s or more.
   The hold is capped at HoldMaxS seconds in total per visit (then it lets go and the van leaves/blows as the game decides) and is never held when the clock is below 20 s. +0x1ee is never written (it is the
   last vehicle called). Data writes only. GUESS: the timer counts DOWN in state 3 (klescort.c's holds write it the same way), 3.0 s is enough for the walkers' last metres. */
static struct { DWORD obj, rules, startAt, last; int capped, told, tmr; } klbf_vh;
static void klbf_vh_off(const char *why, DWORD now)
{
    DWORD o = klbf_vh.obj; BYTE b = 0;
    kle_vh_hold = 0;
    if (!o) return;
    klbf_vh.obj = 0;
    if (klh_rd32(o) != KLE_VEH_VT || !klh_rd(o + KLE_VEH_INV, &b, 1)) { klog("botfill: tactics: van: hold off (%s): the vehicle object %08lx can no longer be read: nothing written back", why, o); return; }
    if (b != 1) { klog("botfill: tactics: van: hold off (%s): the 'Invulnerable' byte of %08lx is %u, not the 1 written here: left alone", why, o, b); return; }
    if (klb_put8(o + KLE_VEH_INV, 0, "escape vehicle: Vulnerable again (OnlineVanHold ends)")) klog("botfill: tactics: van: hold off (%s): 'Invulnerable' [%08lx+0x%x] 1 -> 0 after %.1f s", why, o, KLE_VEH_INV, klbf_vh.startAt ? (now - klbf_vh.startAt) / 1000.0 : 0.0);
    else klog("botfill: tactics: van: hold off (%s): the 'Invulnerable' byte of %08lx could NOT be written back: THE VAN STAYS INVULNERABLE", why, o);
}
/* once per tick of klbf_ot_run: vstate = [rules+0x1dc], dmin = horizontal cm of the nearest walking bot to the goal (1e30 = none) */
static void klbf_vh_pass(DWORD rules, int vstate, float left, float dmin, DWORD now)
{
    struct kle_veh v; float tm = 0, want = 3.0f; int near18;
    if (!klbf_ot_vhold) return;
    if (klbf_vh.rules != rules) { klbf_vh_off("another round object", now); memset(&klbf_vh, 0, sizeof klbf_vh); klbf_vh.rules = rules; }
    if (vstate != 3) {
        if (klbf_vh.obj || kle_vh_hold) klbf_vh_off(vstate < 0 ? "state unreadable" : "the van state changed", now);
        if (vstate != 4) { if (klbf_vh.startAt && klbf_vh.capped) klog("botfill: tactics: van: hold: visit over (state %d), the cap rearms for the next call", vstate); klbf_vh.startAt = 0; klbf_vh.capped = klbf_vh.told = klbf_vh.tmr = 0; }
        return;
    }
    if (klbf_vh.capped) return;
    if (!(left >= 20.0f)) { if (klbf_vh.obj || kle_vh_hold) klbf_vh_off("clock below 20 s", now); return; }
    if (dmin > klbf_ot_hm) { if (klbf_vh.obj || kle_vh_hold) klbf_vh_off("no walking bot within HoldM", now); return; }      /* the cap's clock keeps running (startAt), so stepping out and in again does not buy more */
    if (!klbf_vh.startAt) { klbf_vh.startAt = now; klog("botfill: tactics: van: hold: state 3 and a walking bot %.0f m from the box (HoldM %.0f): holding, at most %d s (clock left %.0f s)", dmin / 100, klbf_ot_hm / 100, klbf_ot_hmax, left); }
    if (now - klbf_vh.startAt > (DWORD)klbf_ot_hmax * 1000u) {
        klbf_vh.capped = 1; klbf_vh_off("cap", now);
        klog("botfill: tactics: van: hold: cap of %d s reached (nearest walker %.0f m): the van goes as the game decides", klbf_ot_hmax, dmin / 100);
        return;
    }
    kle_vh_hold = 1;
    if (kle_veh_read(rules, &v) == 1 && v.hp > 0) {
        if (!klbf_vh.obj) {
            if (v.inv) { if (!(klbf_vh.told & 1) && (klbf_vh.told |= 1)) klog("botfill: tactics: van: hold: the van is Invulnerable already (byte %u): left as it is", v.inv); }
            else if (klb_put8(v.obj + KLE_VEH_INV, 1, "escape vehicle: Invulnerable while the AI heisters walk to the box (OnlineVanHold)")) { klbf_vh.obj = v.obj; klog("botfill: tactics: van: hold: 'Invulnerable' [%08lx+0x%x] 0 -> 1 (health %.0f of %.0f), VanBlow's empty clock paused", v.obj, KLE_VEH_INV, v.hp, v.max); }
            else if (!(klbf_vh.told & 2) && (klbf_vh.told |= 2)) klog("botfill: tactics: van: hold: the 'Invulnerable' byte of %08lx could NOT be written", v.obj);
        } else if (!v.inv) klb_put8(klbf_vh.obj + KLE_VEH_INV, 1, "escape vehicle: Invulnerable (OnlineVanHold, set again)");      /* the level's own 'Vulnerable' */
    } else if (!(klbf_vh.told & 4) && (klbf_vh.told |= 4)) klog("botfill: tactics: van: hold: the van's health object cannot be read (%s) or its health is 0: only the timer is held", kle_veh_err);
    near18 = dmin <= klbf_ot_hnear;
    if (near18 && klh_rd(rules + 0x1d8, &tm, 4) && klb_finite(tm) && tm >= 0 && tm < want) {
        if (klh_data((void *)(DWORD_PTR)(rules + 0x1d8), &want, 4, "rules: escape vehicle state timer held (OnlineVanHold)")) { if (!klbf_vh.tmr++) klog("botfill: tactics: van: hold: timer [rules+0x1d8] %.1f -> %.1f s (a walker %.0f m from the box; said once, %d s cap)", tm, want, dmin / 100, klbf_ot_hmax); }
        else if (!(klbf_vh.told & 8) && (klbf_vh.told |= 8)) klog("botfill: tactics: van: hold: [rules+0x1d8] could NOT be written");
    }
}

static void klbf_ot_summary(void)
{
    int i, bots = 0, tot = 0, boarded = 0;
    klbf_vh_off("round summary", GetTickCount());
    for (i = 0; i < KLBF_OT_BOTS; i++) if (klbf_ob[i].actor) { bots++; tot += klbf_ob[i].tally; if (klbf_ob[i].phase == 3) boarded++; }
    klog("botfill: tactics: round summary: %d bot(s) given orders, %d stack(s) taken, %d total (hook tally, not the game's), %d boarded, %d stack(s) given up", bots, klbf_ot_nclaim, tot, boarded, klbf_ot_nbad);
    klbf_ot_in = 0;
}

/* host, in a round, once a second. sm_state: caller checked role 2, mode 4 */
static void klbf_ot_run(DWORD now, DWORD sm)
{
    DWORD p, tab, i, blk[64 * 32], mo[KLBF_OT_OBJ], van = 0; float mpos[KLBF_OT_OBJ][3], vpos[3] = { 0, 0, 0 }; int mamt[KLBF_OT_OBJ], nm = 0, n = 0, b, nmoney = 0, nvan = 0, ndoor = 0;
    struct { DWORD actor, soldier; float pos[3]; } bots[KLBF_OT_BOTS]; int nb = 0; char why[100];
    static float cops[256][3]; int ncop = 0, vnew; DWORD rules = 0; int vstate = -1; float left = 1e9f;
    if (now - klbf_ot_last < 1000) return;
    klbf_ot_last = now;
    if (sm != (DWORD)klbf_ot_sm || !klbf_ot_in) {      /* a new session / round */
        if (klbf_ot_in) klbf_ot_summary();
        memset(klbf_ob, 0, sizeof klbf_ob); klbf_ot_nclaim = klbf_ot_nbad = 0; klbf_ot_vidle = 0; klbf_ot_sm = (int)sm; klbf_ot_in = 1; klbf_ot_rounds++;
        klbf_ot_trig = klbf_ot_tvt = klbf_ot_vh = klbf_ot_lookAt = 0; klbf_ot_trig_looked = klbf_ot_called = klbf_ot_looks = 0; klbf_ot_calledAt = 0; klbf_ot_nbx = klbf_ot_bxlooks = 0; klbf_ot_bxbest = -1; klbf_ot_bxAt = 0;
        klbf_ot_gat = klbf_ot_gcar = klbf_ot_gtold = 0; klbf_ot_gatAt = 0; memset(&klbf_vh, 0, sizeof klbf_vh);
        klbf_way_load(); klbf_ramp_load();
        klog("botfill: tactics: round %d starts (Carry %d, Near %.0f, Take %d): the host orders the Ally bots itself", klbf_ot_rounds, klbf_ot_carry, klbf_ot_near, klbf_ot_take);
    }
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x10000; i += 64) {      /* the whole table: BO2 (DM01) capped at 4000 objects never reached the Ally actors */
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], vt; float pos[3];
            if (o < 0x10000 || !(vt = klh_rd32(o))) continue;
            n++;
            if (vt == KLE_VEH_VT) {
                DWORD node = klh_rd32(o + 4);
                nvan++;
                if (!van && node && kle_node(node, vpos, 0) && (fabs(vpos[0]) > 1 || fabs(vpos[1]) > 1 || fabs(vpos[2]) > 1)) van = o;      /* BO3: the van stood at (0,0,0) at the round start = not here / not called yet; wait for a real place */      /* GUESS: the vehicle object's node is where the van stands (its boarding place is 500 along x, klescort.c kle_boarding; not used) */
            } else if (klh_avt(o) == 0x00bb3bac) {
                DWORD pr, team = 99, hp, snd; float hv[2] = { 0, 0 };
                if (!(pr = klh_rd32(o + 0x54)) || !klh_rd(pr + 4, &team, 4)) continue;
                if (team == 1) {      /* a live cop: OnlineTacticsGuard keeps bots off stacks it stands on */
                    if (ncop < 256 && (hp = klh_rd32(o + 0x5fc)) && klh_rd(hp + 4, hv, 4) && hv[0] > 0 && klh_rd(o + 0x460, pos, 12) && kle_ok3(pos)) memcpy(cops[ncop++], pos, 12);
                    continue;
                }
                if (team != 2 || nb >= KLBF_OT_BOTS) continue;      /* review: the bot cap no longer hides the cops */
                if (!(hp = klh_rd32(o + 0x5fc)) || !klh_rd(hp + 4, hv, 8) || !(hv[0] > 0)) continue;      /* alive */
                klbf_ot_health(o, hp, hv);
                if (!(snd = klh_rd32(o + 0x77c)) || klh_rd32(snd) != KLE_SOLDIER_VT) continue;
                if (!klh_rd(o + 0x460, pos, 12) || !kle_ok3(pos)) continue;      /* feet, as klcrew_rt.c (ASSUMPTION: same base class as a player) */
                bots[nb].actor = o; bots[nb].soldier = snd; memcpy(bots[nb].pos, pos, 12); nb++;
            }
        }
    }
    {   int q; for (q = 0; q < nb && q < KLBF_OT_BOTS_MAX; q++) klbf_pb_bots[q] = bots[q].actor; klbf_pb_n = nb < KLBF_OT_BOTS_MAX ? nb : KLBF_OT_BOTS_MAX; klbf_pb_at = GetTickCount(); }      /* OnlinePointBlank's bot list */
    {   float bp[KLBF_OT_BOTS][3]; int q; for (q = 0; q < nb; q++) memcpy(bp[q], bots[q].pos, 12); klbf_ramp_tick(now, bp, nb); }      /* OnlineRampFire */
    {   /* the money: BO4 (DM01) found 0 ZOnlineMoneyCtrl in the entity table - they are controllers, not table objects. Workflow wo8upp5vd
           (verified in disassembly): the ctor 0x9012a0 (0x901323..33) appends every one to the game's object registry via 0x826990: pointers
           at 0xe09e38, count 0xe0e63c (cap 0x1000). Types at +0x38: 0 normal, 1 DROP (the pool a player drops; skipped), 2 container.
           GUESS: no unregister path was found, so an entry may be stale - each is re-checked by vtable and read safely. */
        DWORD rn = klh_rd32((DWORD_PTR)KLH_VA(0x00e0e63c)), reg[0x400], q, j;
        if (rn > 0x1000) rn = 0x1000;
        for (q = 0; q < rn; q += 0x400) {
            DWORD m = rn - q < 0x400 ? rn - q : 0x400;
            if (!klh_rd((DWORD_PTR)KLH_VA(0x00e09e38) + 4 * q, reg, 4 * m)) break;
            for (j = 0; j < m; j++) {
                DWORD o = reg[j], ent, node, type = 0; int amt = 0; BYTE act = 0; float pos[3];
                if (o < 0x10000 || klh_rd32(o) != KLMV_MONEY_VT) continue;
                nmoney++;
                if (nm >= KLBF_OT_OBJ || !klh_rd(o + 0x38, &type, 4) || type == 1 || !klh_rd(o + 0x34, &amt, 4) || amt <= 0 || !klh_rd(o + 0x6c, &act, 1) || !act) continue;      /* drop pool, taken, or not armed (+0x6c, klmove.c 2) */
                if (klbf_ot_door) { BYTE shut = 0; if (klh_rd(o + 0x5c, &shut, 1) && shut) { ndoor++; continue; } }      /* field 11 "behind a door" (re/bots_loot.md): cleared by the door's 'DoorOpened' relay; ZLootTactic 0x451920 skips these too */
                if (!(ent = klh_rd32(o + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, pos, 0)) continue;
                mo[nm] = o; mamt[nm] = amt; memcpy(mpos[nm], pos, 12); nm++;
            }
        }
    }
    {   /* the FA rules: [[0x168e9e4]+0x54] when the session's game type [sm+0x5c] is 4 (0x7bb2a0, PROVEN; 0x508ef0 is Arcade-only) */
        DWORD s0 = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598)), hd;
        if (s0 && klh_rd32(s0 + 0x5c) == 4 && (hd = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4)))) rules = klh_rd32(hd + 0x54);
    }
    if (rules) {      /* BO9: vstate = the escape vehicle's state [rules+0x1dc] (1/2 coming, 3/4 waiting, 5 leaving, 7 gone, 0 idle; re/retomoto_street.md 6); left = the round clock [rules+0x4c] */
        static BYTE lastv = 0xff; static int lastr; BYTE v = 0; float c = 0;
        if (klh_rd(rules + 0x1dc, &v, 1)) vstate = v;
        if (klh_rd(rules + 0x4c, &c, 4) && klb_finite(c) && c >= 0 && c < 100000.0f) left = c;
        if (lastr != klbf_ot_rounds) { lastr = klbf_ot_rounds; lastv = 0xff; }
        if (vstate >= 0 && vstate != lastv) {
            static int nrecall, rcr;
            if (rcr != klbf_ot_rounds) { rcr = klbf_ot_rounds; nrecall = 0; }
            if (lastv != 0xff) klog("botfill: tactics: van state %u -> %d (clock left %.1f s, called %d, +%lu s since the call)", lastv, vstate, left, klbf_ot_called, klbf_ot_calledAt ? (unsigned long)((now - klbf_ot_calledAt) / 1000) : 0);
            /* OnlineVanRecall (BO14): the van left (7 -> 0) with a live bot still out carrying money (it grabbed 800k 3 s after the call): the call is freed so that bot calls it again. Max 2 per round; the < 20 s clock gate in klbf_ot_call_van still holds. GUESS: a second 0x71e180 call behaves like the first once the state is back to 0 */
            if (klbf_ot_recall && lastv == 7 && vstate == 0 && klbf_ot_called && nrecall < 2 && left >= 40.0f) {
                int q, nout = 0;
                for (q = 0; q < KLBF_OT_BOTS; q++) if (klbf_ob[q].actor && klbf_ob[q].phase != 3 && klbf_ob[q].tally > 0) nout++;
                if (nout) {
                    nrecall++; klbf_ot_called = 0; klbf_ot_calledAt = 0; klbf_ot_gat = 0;
                    for (q = 0; q < KLBF_OT_BOTS; q++) if (klbf_ob[q].actor && klbf_ob[q].phase != 3) { klbf_ob[q].told &= ~(1 | 32 | 256); klbf_ob[q].ordered = 0; klbf_ob[q].outAt = 0; }
                    klog("botfill: tactics: van: back to idle with %d bot(s) still out carrying money (clock left %.0f s): the call is free again, recall %d of 2 (OnlineVanRecall)", nout, left, nrecall);
                }
            }
            lastv = (BYTE)vstate; if (klbf_ot_bprobe) klbf_ot_vprobe(rules, vstate);
        }
    }
    if (!van && rules) {   /* [rules+0x1e4] = the escape vehicle (0x70f0a0, PROVEN), 0 until the vehicle is called (0x71e180 -> 0x84f030 fills the list slot 89 reads) */
        struct kle_veh v; float vp[3];
        if (kle_veh_read(rules, &v) == 1 && kle_node(klh_rd32(v.obj + 4), vp, 0) && (fabs(vp[0]) > 1 || fabs(vp[1]) > 1 || fabs(vp[2]) > 1)) { van = v.obj; memcpy(vpos, vp, 12); }
    }
    if (!van && klbf_ot_van && rules && !klbf_ot_trig_looked && klbf_ot_looks < 6 && (!klbf_ot_lookAt || now - klbf_ot_lookAt >= 20000)) {      /* the exit trigger: when the first bot carries money (a private-memory scan, klmove.c); a miss is retried every 20 s, 6 times a round */
        int q; for (q = 0; q < KLBF_OT_BOTS && !(klbf_ob[q].actor && klbf_ob[q].tally > 0); q++) ;
        if (q == KLBF_OT_BOTS && klbf_ot_idlevan && klbf_ot_vidle) q = 0;      /* OnlineIdleVan: a bot with nothing left to do needs the trigger too */
        if (q < KLBF_OT_BOTS) {
            DWORD t0 = GetTickCount(), ent, node;
            klbf_ot_lookAt = now; klbf_ot_looks++;
            klbf_ot_vh = klmv_exit_vehicle2(&klbf_ot_trig, 1);      /* BOS_DD02x: skip husk triggers whose node reads (0, 0, 0) */
            klbf_ot_tvt = klbf_ot_trig ? klh_rd32(klbf_ot_trig) : 0;
            if (klbf_ot_vh && (!(ent = klh_rd32(klbf_ot_trig + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, klbf_ot_tpos, 0) || !kle_ok3(klbf_ot_tpos)
                || (fabsf(klbf_ot_tpos[0]) <= 1 && fabsf(klbf_ot_tpos[1]) <= 1 && fabsf(klbf_ot_tpos[2]) <= 1))) klbf_ot_vh = 0;      /* review wf_1d705c3d: klmv_exit_vehicle2's fallback may still be a husk at (0, 0, 0): not found, retried in 20 s */
            klog("botfill: tactics: van: exit trigger %08lx, vehicle field %08lx (kind %u), its place (%.0f, %.0f, %.0f) - found in %lu ms%s", klbf_ot_trig, klbf_ot_vh, klh_rd32(rules + 0x1ec) & 0xff,
                 klbf_ot_tpos[0], klbf_ot_tpos[1], klbf_ot_tpos[2], GetTickCount() - t0, klbf_ot_vh ? "" : ": none usable yet, looked again in 20 s");
            if (klbf_ot_vh) klbf_ot_trig_looked = 1;
        }
    }
    if (klbf_ot_bwalk && klbf_ot_vh && !klbf_ot_nbx && klbf_ot_bxlooks < 4 && (!klbf_ot_bxAt || now - klbf_ot_bxAt >= 20000)) klbf_ot_boxscan(now);      /* once the trigger is known (a bot carries money), the boxes; a miss is retried every 20 s, 4 looks a round */
    {   /* once per round, and again whenever the bot count changes: what the scan saw (BO2 gave no order and no clue why) */
        static int seen_round, seen_nb = -1, seen_nm = -1, seen_nd = -1; static DWORD seen_van = 1;
        if (seen_round != klbf_ot_rounds || seen_nb != nb || seen_nm != nm || seen_van != van || seen_nd != ndoor) { seen_round = klbf_ot_rounds; seen_nb = nb; seen_nm = nm; seen_van = van; seen_nd = ndoor; klog("botfill: tactics: scan: %d objects, %d live Ally bot(s), %d armed stack(s) (+%d behind a shut door) of %d money object(s), van %08lx (%d vehicle(s); one at the origin = not here yet)", n, nb, nm, ndoor, nmoney, van, nvan); }
    }
    {   /* free the slot of a bot that is dead / gone (else its target stack stays "taken" and the 16 slots run out); boarded bots (phase 3) keep theirs for the summary */
        int q, r;
        for (q = 0; q < KLBF_OT_BOTS; q++) {
            if (!klbf_ob[q].actor || klbf_ob[q].phase == 3) continue;
            for (r = 0; r < nb && bots[r].actor != klbf_ob[q].actor; r++) ;
            if (r == nb) { klog("botfill: tactics: bot %d (actor %08lx) is dead or gone: slot freed (phase %d, tally %d)", q, klbf_ob[q].actor, klbf_ob[q].phase, klbf_ob[q].tally); memset(&klbf_ob[q], 0, sizeof klbf_ob[q]); }
        }
    }
    vnew = 0;
    for (b = 0; b < nb; b++) {
        int s, j, best = -1; float bd = 1e30f, tgt[3], got[3]; struct kle_e t; struct klmv_fr t_bf; DWORD a = bots[b].actor;
        for (s = 0; s < KLBF_OT_BOTS && klbf_ob[s].actor != a; s++) ;
        if (s == KLBF_OT_BOTS) { for (s = 0; s < KLBF_OT_BOTS && klbf_ob[s].actor; s++) ; if (s == KLBF_OT_BOTS) continue; klbf_ob[s].actor = a; }
        if (klbf_ob[s].phase == 3) continue;
        if (klbf_ot_gat && !klbf_ot_called && klbf_ob[s].phase < 2) {      /* OnlineVanGather: the carrier is at the exit, every living bot goes to the box now (a walk to a stack is dropped; the stack stays unclaimed) */
            if (!(klbf_ob[s].told & 64) && (klbf_ob[s].told |= 64)) klog("botfill: tactics: bot %d (actor %08lx): van gather: leaves phase %d (tally %d, %d grab(s)) and walks to the box", s, a, klbf_ob[s].phase, klbf_ob[s].tally, klbf_ob[s].grabs);
            klbf_ob[s].phase = 2; klbf_ob[s].since = now; klbf_ob[s].ordered = 0; klbf_ob[s].bestAt = 0; klbf_ob[s].idleAt = 0; klbf_ob[s].told &= ~8; klbf_ob[s].leg = klbf_way_start(bots[b].pos, klbf_ot_tpos); klbf_ob[s].legAt = 0;
        }
        if (klbf_ob[s].phase == 1) {      /* walking to a stack: reached? gone? stalled? */
            DWORD o = klbf_ob[s].target; int amt = 0; BYTE act = 0; DWORD ent, node; float mp[3], dh = 0;
            if (klh_rd32(o) != KLMV_MONEY_VT || !klh_rd(o + 0x34, &amt, 4) || amt <= 0 || !klh_rd(o + 0x6c, &act, 1) || !act || !(ent = klh_rd32(o + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, mp, 0)) {
                klog("botfill: tactics: bot %d (actor %08lx): stack %08lx is gone before it got there (taken by someone else?)", s, a, o); klbf_ob[s].phase = 0;
            } else if ((dh = (float)sqrt((bots[b].pos[0] - mp[0]) * (bots[b].pos[0] - mp[0]) + (bots[b].pos[2] - mp[2]) * (bots[b].pos[2] - mp[2]))) <= klbf_ot_near && fabs(bots[b].pos[1] - mp[1]) <= 400.0f) {
                klbf_ob[s].tally += amt; klbf_ob[s].grabs++;
                if (klbf_ot_nclaim < KLBF_OT_OBJ) klbf_ot_claimed[klbf_ot_nclaim++] = o;
                if (klbf_ot_take) { int z = 0; klh_data((void *)(DWORD_PTR)(o + 0x34), &z, 4, "money amount (OnlineTacticsTake, GUESS)"); }
                klog("botfill: tactics: bot %d (actor %08lx) GRABBED stack %08lx = %d; its tally %d after %d grab(s)%s", s, a, o, amt, klbf_ob[s].tally, klbf_ob[s].grabs, klbf_ot_take ? " (amount zeroed on the host)" : " (host tally only)");
                klbf_ob[s].phase = 0;
            } else {
                if (!klbf_ob[s].bestAt || dh < klbf_ob[s].best - 200.0f) { klbf_ob[s].best = dh; klbf_ob[s].bestAt = now; }      /* 2 m closer = progress */
                if (klbf_ot_firestall && klbf_ob[s].bestAt) {      /* OnlineFireStall: a bot with a live cop near is pinned down by the game's own combat, not stuck: the 12 s clock pauses (the 90 s cap still runs) */
                    float fr = klbf_ot_guard > 0 ? klbf_ot_guard : 2500.0f; int c;
                    for (c = 0; c < ncop; c++) if (kle_dist(cops[c], bots[b].pos) <= fr) { klbf_ob[s].bestAt = now; break; }
                }
                if (now - klbf_ob[s].bestAt > KLBF_OT_STALL || now - klbf_ob[s].since > KLBF_OT_STALLMAX) {
                    int copAtStack = 0;
                    if (klbf_ot_retry && klbf_ot_guard > 0) { int c; for (c = 0; c < ncop; c++) if (kle_dist(cops[c], mp) <= klbf_ot_guard) { copAtStack = 1; break; } }      /* OnlineGiveUpRetry: a cop on the stack = the guard rule holds the bots off it, no blacklist */
                    if (!copAtStack && klbf_ot_nbad < KLBF_OT_OBJ) { klbf_ot_badAt[klbf_ot_nbad] = now; klbf_ot_bad[klbf_ot_nbad++] = o; }
                    klog("botfill: tactics: bot %d (actor %08lx) did not reach stack %08lx (%.0f m left, %lu s walking, no 2 m of progress for %lu s): given up on it", s, a, o, dh / 100, (unsigned long)((now - klbf_ob[s].since) / 1000), (unsigned long)((now - klbf_ob[s].bestAt) / 1000)); klbf_ob[s].phase = 0;
                }
            }
        }
        if (klbf_ob[s].phase == 0) {
            int nguard = 0, gbest = -1, idleVan = 0, nhold = 0; float gbd = 1e30f;
            for (j = 0; j < nm; j++) {
                float d; int c, guarded = 0;
                if (klbf_ot_has(klbf_ot_claimed, klbf_ot_nclaim, mo[j])) continue;
                if (klbf_ot_isbad(mo[j], now)) { nhold++; continue; }      /* review: a stack that is only blacklisted for now still counts as a stack left (OnlineIdleVan) */
                { int q, taken = 0; for (q = 0; q < KLBF_OT_BOTS; q++) if (q != s && klbf_ob[q].actor && klbf_ob[q].phase == 1 && klbf_ob[q].target == mo[j]) taken = 1; if (taken) { nhold++; continue; } }
                d = kle_dist(bots[b].pos, mpos[j]);
                /* OnlineTacticsGuard: BO5's guard cops stood ON the stacks (slots 706/711/851/852 within 3 m of 4 targets) and every bot walked alone into them */
                if (klbf_ot_guard > 0) for (c = 0; c < ncop && !guarded; c++) if (kle_dist(cops[c], mpos[j]) <= klbf_ot_guard) guarded = 1;
                if (guarded) { nguard++; if (d < gbd) { gbd = d; gbest = j; } continue; }
                if (d < bd) { bd = d; best = j; }
            }
            if (best < 0 && gbest >= 0) { if (!klbf_ob[s].idleAt) klbf_ob[s].idleAt = now; } else klbf_ob[s].idleAt = 0;      /* review: idleAt = since when only guarded stacks are left */
            if (klbf_ot_gtake && best < 0 && gbest >= 0 && now - klbf_ob[s].idleAt >= KLBF_OT_GUARDWAIT) {      /* nothing unguarded for 30 s: take the nearest guarded one (Arcade bots fight for loot too) */
                best = gbest; bd = gbd;
                klog("botfill: tactics: bot %d (actor %08lx): every free stack has had a live cop within %.0f m for %lu s: taking the nearest guarded one", s, a, klbf_ot_guard / 100, (unsigned long)((now - klbf_ob[s].idleAt) / 1000));
            } else if (best < 0 && gbest >= 0 && klbf_ob[s].tally == 0 && !(klbf_ob[s].told & 4) && (klbf_ob[s].told |= 4))      /* a bot with money goes to the van instead */
                klog("botfill: tactics: bot %d (actor %08lx): %d free stack(s), all with a live cop within %.0f m: it holds (%s) while they are cleared", s, a, nguard, klbf_ot_guard / 100, klbf_ot_gtake ? "up to 30 s, OnlineGuardTake=1" : "until a stack is clear, OnlineGuardTake=0");
            {   /* OnlineIdleVan: no stack for this bot (blacklisted, taken, none armed) and nothing carried: after OnlineIdleVanS with no stack left at all, or with the clock low, it goes to the exit and the van is called (BO12: 0 grabs, nobody called it) */
                int nostack = best < 0 && !(klbf_ot_gtake && gbest >= 0);
                if (klbf_ot_idlevan && nostack && klbf_ob[s].tally == 0) {
                    if (!klbf_ob[s].vidleAt) klbf_ob[s].vidleAt = now;
                    if ((gbest < 0 && !nhold && !ndoor && now -klbf_ob[s].vidleAt >= (DWORD)klbf_ot_idleS * 1000u) || (klbf_ot_late && left <= (float)(klbf_ot_late + 20))) {
                        idleVan = 1; vnew = 1;
                        if (!(klbf_ob[s].told & 128) && (klbf_ob[s].told |= 128)) klog("botfill: tactics: bot %d (actor %08lx): no stack to take (%d guarded, %lu s idle, clock left %.0f s) and nothing carried: goes to the exit to call the van (OnlineIdleVan)", s, a, nguard, (unsigned long)((now - klbf_ob[s].vidleAt) / 1000), left);
                    }
                } else klbf_ob[s].vidleAt = 0;
            }
            if (klbf_ot_late && klbf_ob[s].tally > 0 && left <= (float)klbf_ot_late && best >= 0) {      /* OnlineLateExit (BO9 rules A/B): a carrier takes no new stack late in the round, it heads for the van */
                if (!(klbf_ob[s].told & 16) && (klbf_ob[s].told |= 16)) klog("botfill: tactics: bot %d (actor %08lx): clock left %.0f s <= OnlineLateExit %d: no new stack, tally %d goes to the van", s, a, left, klbf_ot_late, klbf_ob[s].tally);
                best = -1;
            }
            if (klbf_ob[s].grabs < klbf_ot_carry && best >= 0) {
                klbf_ob[s].phase = 1; klbf_ob[s].target = mo[best]; klbf_ob[s].since = now; klbf_ob[s].ordered = 0; klbf_ob[s].bestAt = 0; klbf_ob[s].idleAt = 0; klbf_ob[s].told &= ~4;
                memcpy(tgt, mpos[best], 12);
                klog("botfill: tactics: bot %d (actor %08lx soldier %08lx) -> stack %08lx (%d) at (%.0f, %.0f, %.0f), %.0f m away", s, a, bots[b].soldier, mo[best], mamt[best], tgt[0], tgt[1], tgt[2], bd / 100);
            } else if (klbf_ob[s].tally > 0 || idleVan) {      /* BO3: with nothing carried a bot waited at the van for nothing; it now waits for an armed stack */
                if (!van && !(klbf_ot_vh && !klbf_ot_called) && !(klbf_ot_joincall && klbf_ot_vh && klbf_ot_called && vstate >= 1 && vstate <= 4 && klbf_ot_calledAt && now - klbf_ot_calledAt <= 60000)) {      /* OnlineJoinCalled (BOS_DD04): a carrier whose van another bot called walks to it while it comes or waits (1-4), instead of standing 100 m off for the whole visit */ if (!(klbf_ob[s].told & 1) && (klbf_ob[s].told |= 1)) klog("botfill: tactics: bot %d (actor %08lx): wants the van but it is not here and %s", s, a, klbf_ot_called ? "it was called already" : "no exit trigger was found to call it from"); continue; }
                klbf_ob[s].phase = 2; klbf_ob[s].nearAt = klbf_ob[s].outAt = 0; klbf_ob[s].since = now; klbf_ob[s].ordered = 0; klbf_ob[s].bestAt = 0; klbf_ob[s].idleAt = 0; klbf_ob[s].leg = klbf_way_start(bots[b].pos, klbf_ot_tpos); klbf_ob[s].legAt = 0;      /* OnlineWaypoints: resume at the first leg ahead, never back down */
                if (van) klog("botfill: tactics: bot %d (actor %08lx) -> escape van %08lx at (%.0f, %.0f, %.0f) with tally %d (%d grab(s))", s, a, van, vpos[0], vpos[1], vpos[2], klbf_ob[s].tally, klbf_ob[s].grabs);
                else klog("botfill: tactics: bot %d (actor %08lx) -> exit trigger %08lx at (%.0f, %.0f, %.0f) to call the van, with tally %d (%d grab(s))", s, a, klbf_ot_trig, klbf_ot_tpos[0], klbf_ot_tpos[1], klbf_ot_tpos[2], klbf_ob[s].tally, klbf_ob[s].grabs);
            }
        }
        if (klbf_ob[s].phase == 2) {
            int legsLeft; struct klmv_fr bf; int bxOn = klbf_ot_bwalk && (klbf_ot_called || klbf_ot_gat) && klbf_ot_box_frame(klbf_ot_bxbest, &bf);      /* OnlineBoxWalk: once the van is called (or the OnlineVanGather starts) the goal is the ZAllyEscapeBox, not the trigger */
            const float *g = bxOn ? bf.T : van ? vpos : klbf_ot_tpos;
            float dd = (float)sqrt((bots[b].pos[0] - g[0]) * (bots[b].pos[0] - g[0]) + (bots[b].pos[2] - g[2]) * (bots[b].pos[2] - g[2]));
            if (bxOn && !(klbf_ob[s].told & 32)) { klbf_ob[s].told |= 32; klbf_ob[s].ordered = 0; klog("botfill: tactics: bot %d (actor %08lx): %s, walks to the escape box %d at (%.0f, %.0f, %.0f), %.0f m away", s, a, klbf_ot_called ? "van called" : "van gather", klbf_ot_bxbest, bf.T[0], bf.T[1], bf.T[2], dd / 100); }
            if (bxOn && (!klbf_ot_vstate || vstate == 3 || vstate == 4 || klbf_ot_bprobe)) {
                int byGame = 0, in = klbf_ot_inside(klbf_ot_bxbest, &bf, a, bots[b].pos, &byGame);
                if (klbf_ot_bforce && vstate == 3 && !in) {      /* OnlineBoxForce (BO13): van waiting and this bot is outside the box: after 4 s, and every 4 s, an order straight to the box centre (inside by construction), bypassing the 6 s repeat timer; one log line per bot. GUESS: the earlier order was lost to the game's chain / nav snap at the trigger */
                    if (!klbf_ob[s].outAt) klbf_ob[s].outAt = now;
                    else if (now - klbf_ob[s].outAt >= 4000) {
                        memset(&t, 0, sizeof t); t.rec = -1; t.actor = a; t.soldier = bots[b].soldier; t.told_soft = 1; why[0] = 0; memcpy(tgt, bf.T, 12);
                        if (kle_order2(&t, tgt, got, why, 0) == 1) klbf_ob[s].ordered = now;
                        klbf_ob[s].outAt = now;
                        if (!(klbf_ob[s].told & 256) && (klbf_ob[s].told |= 256)) klog("botfill: tactics: bot %d (actor %08lx): van waiting (state 3) and this bot is still outside the escape box (%.1f m from its centre, frame distance %.1f m, +%lu s since the call): re-ordered to the box centre (%.0f, %.0f, %.0f)%s%s (OnlineBoxForce, said once)", s, a, dd / 100, klmv_fr_dist(&bf, bots[b].pos) / 100, klbf_ot_calledAt ? (unsigned long)((now - klbf_ot_calledAt) / 1000) : 0, tgt[0], tgt[1], tgt[2], why[0] ? "; order refused: " : "", why);
                    }
                } else klbf_ob[s].outAt = 0;
                if (!in && klbf_ot_bslack > 0 && vstate == 3 && bf.box && klmv_fr_dist(&bf, bots[b].pos) <= klbf_ot_bslack) {      /* OnlineBoxSlack (BOS_DD02x2): parked just outside the frame while the van waits; after 8 s there it counts as inside. GUESS: the game's own nav snap keeps it from the centre */
                    if (!klbf_ob[s].nearAt) klbf_ob[s].nearAt = now;
                    else if (now - klbf_ob[s].nearAt >= 8000) {
                        in = 1;
                        if (!(klbf_ob[s].told & 1024) && (klbf_ob[s].told |= 1024)) klog("botfill: tactics: bot %d (actor %08lx): %.1f m outside the escape box frame for %lu s of van wait: counts as inside (OnlineBoxSlack %.0f cm)", s, a, klmv_fr_dist(&bf, bots[b].pos) / 100, (unsigned long)((now - klbf_ob[s].nearAt) / 1000), klbf_ot_bslack);
                    }
                } else if (!in) klbf_ob[s].nearAt = 0;
                if (klbf_ot_bprobe && now - klbf_ob[s].pAt >= 5000) { klbf_ob[s].pAt = now; klog("botfill: tactics: box probe: bot %d (actor %08lx) %.1f m from the box centre (frame distance %.1f m), inside %d (%s), van state %d, +%lu s since the call", s, a, dd / 100, klmv_fr_dist(&bf, bots[b].pos) / 100, in, byGame ? "game 0x758cb0" : "frame", vstate, klbf_ot_calledAt ? (unsigned long)((now - klbf_ot_calledAt) / 1000) : 0); }
                if (in && (vstate == 3 || vstate == 4 || (!klbf_ot_vstate && van))) {      /* OnlineVanState off: the old rule, the van's node known and the bot at it */
                    klbf_ob[s].phase = 3;
                    klog("botfill: tactics: bot %d (actor %08lx) BOARDED in the escape box (van state %d, inside by %s): tally %d; OnlineBoard %s", s, a, vstate, byGame ? "0x758cb0" : "the frame", klbf_ob[s].tally,
                         !klbf_ot_board ? "off (host tally only, bot stays)" : klbf_ot_board_call(a) ? "-> 0x89c890 called (squad removal; watch the census and the clients)" : "-> refused (code head / actor / squad check): host tally only");
                    continue;
                }
            }
            if (van && !bxOn && dd <= 2 * klbf_ot_near) {
                klbf_ob[s].phase = 3;
                klog("botfill: tactics: bot %d (actor %08lx) BOARDED (hook tally only, nothing removed in the game): tally %d", s, a, klbf_ob[s].tally);
                continue;
            }
            if (!van && !bxOn && klbf_ot_vstate && klbf_ot_called && (vstate == 3 || vstate == 4) && dd <= 2 * klbf_ot_near && fabs(bots[b].pos[1] - g[1]) <= klbf_ot_exitdy) {      /* OnlineVanState: BO9's van node stayed at the origin, so the waiting state + the bot at the exit box counts as aboard */      /* GUESS: the exit trigger's box is where the van's boarding box is */
                klbf_ob[s].phase = 3;
                klog("botfill: tactics: bot %d (actor %08lx) BOARDED by van state %d (OnlineVanState; hook tally only, %.0f m from the exit trigger): tally %d", s, a, vstate, dd / 100, klbf_ob[s].tally);
                continue;
            }
            if (!van && !bxOn && klbf_ot_crowd > 0 && klbf_ot_vstate && klbf_ot_called && (vstate == 3 || vstate == 4) && dd <= klbf_ot_crowd && fabs(bots[b].pos[1] - g[1]) <= klbf_ot_exitdy) {      /* OnlineExitCrowd (BOS_DD07): 7 sprinting bots crowd the trigger; 3 stood 2-10 m off its centre for the whole 19 s wait and missed the 3 m (2*Near) test. GUESS: the game's van takes a crew member standing at the trigger's edge (the stall call already trusts 15 m) */
                if (!klbf_ob[s].nearAt) klbf_ob[s].nearAt = now;
                else if (now - klbf_ob[s].nearAt >= 5000) {
                    klbf_ob[s].phase = 3;
                    klog("botfill: tactics: bot %d (actor %08lx) BOARDED by van state %d (OnlineExitCrowd %.0f cm: %.1f m from the exit trigger for %lu s of van wait; hook tally only): tally %d", s, a, vstate, klbf_ot_crowd, dd / 100, (unsigned long)((now - klbf_ob[s].nearAt) / 1000), klbf_ob[s].tally);
                    continue;
                }
            } else if (!bxOn) klbf_ob[s].nearAt = 0;
            legsLeft = !van && !bxOn && klbf_ot_vh && !klbf_ot_called && klbf_way_n > 0 && klbf_ob[s].leg < klbf_way_n;
            if (legsLeft) {      /* OnlineWaypoints: reached (300 units horizontally) or 15 s on this leg -> next; the stall / give-up clocks below do not run while legs remain (the 15 s per leg is their clock) */
                const float *wp = klbf_way_p[klbf_ob[s].leg]; float wd = (float)sqrt((bots[b].pos[0] - wp[0]) * (bots[b].pos[0] - wp[0]) + (bots[b].pos[2] - wp[2]) * (bots[b].pos[2] - wp[2]));
                if (!klbf_ob[s].legAt) klbf_ob[s].legAt = now;
                if (wd <= KLBF_WAY_NEAR || now - klbf_ob[s].legAt >= KLBF_WAY_LEGMS) {
                    klog("botfill: tactics: bot %d (actor %08lx): waypoint leg %d of %d %s (%.0f m from (%.0f, %.0f, %.0f), %lu s on the leg)%s", s, a, klbf_ob[s].leg + 1, klbf_way_n, wd <= KLBF_WAY_NEAR ? "reached" : "timed out", wd / 100, wp[0], wp[1], wp[2], (unsigned long)((now - klbf_ob[s].legAt) / 1000), klbf_ob[s].leg + 1 >= klbf_way_n ? ": on to the exit trigger" : "");
                    klbf_ob[s].leg++; klbf_ob[s].legAt = now; klbf_ob[s].ordered = 0; klbf_ob[s].bestAt = 0;
                    if (klbf_ob[s].leg >= klbf_way_n) klbf_ob[s].since = now;      /* the 90 s cap counts from the last leg */
                    legsLeft = klbf_ob[s].leg < klbf_way_n;
                }
            }
            if (!van && !legsLeft && klbf_ot_vh && !klbf_ot_called && dd <= 2 * klbf_ot_near && fabs(bots[b].pos[1] - g[1]) <= klbf_ot_exitdy) klbf_ot_arrive(rules, s, now);
            if (!van && !legsLeft) {      /* review wp16tqkg2: phase 2 had no stall test; the trigger's node (its box centre, GUESS) may be out of the nav's reach */
                if (!klbf_ob[s].bestAt || dd < klbf_ob[s].best - 200.0f) { klbf_ob[s].best = dd; klbf_ob[s].bestAt = now; }
                if (klbf_ot_vh && !klbf_ot_called && now - klbf_ob[s].bestAt > KLBF_OT_STALL && dd <= 1500.0f && fabs(bots[b].pos[1] - g[1]) <= klbf_ot_exitdy) {
                    if (!(klbf_ob[s].told & 8) && (klbf_ob[s].told |= 8)) klog("botfill: tactics: bot %d (actor %08lx) stopped %.0f m from the exit trigger's centre: calls the van from there (GUESS: the box is wider than 2*Near)", s, a, dd / 100);
                    klbf_ot_arrive(rules, s, now);
                } else if (klbf_ot_vstate && klbf_ot_called ? (now - klbf_ot_calledAt > 60000 || vstate == 7 || (vstate == 0 && now - klbf_ot_calledAt > 5000)) : now - klbf_ob[s].since > (DWORD)(klbf_ot_called ? 60000 : KLBF_OT_STALLMAX)) {      /* OnlineVanState: the 60 s count from the CALL (BO9 counted from phase 2, 15 s earlier), and a van that left (7 / back to 0) ends the wait */
                    klog("botfill: tactics: bot %d (actor %08lx): %s after %lu s (%.0f m from the trigger, bot at (%.0f, %.0f, %.0f)): back to idle", s, a, klbf_ot_called ? "the van was called but this bot was not at the exit while it waited" : "did not reach the exit trigger", (unsigned long)((now - klbf_ob[s].since) / 1000), dd / 100, bots[b].pos[0], bots[b].pos[1], bots[b].pos[2]);      /* BOS_DD02: the full position tells the wagon level (y ~4500) from the ramp foot (y 5150-5500) */
                    if (klbf_ob[s].told & 2048) {      /* OnlineExitSprint undone: 'style given' 0 again, so the loot / hold walks after this go at the chain's own style (GUESS: a sprinting soldier does not shoot) */
                        DWORD blk = klh_rd32(bots[b].soldier + 0x64c); BYTE zero = 0;
                        if (blk && klh_rd32(blk + 0x14) == bots[b].soldier) klh_data((void *)(DWORD_PTR)(blk + 0x10), &zero, 1, "defend block style given (OnlineExitSprint undone)");
                    }
                    klbf_ob[s].phase = 0; klbf_ob[s].told &= ~(8 | 512 | 2048); klbf_ob[s].leg = 0; klbf_ob[s].legAt = 0;
                    continue;
                }
            }
        }
        if ((klbf_ob[s].phase == 1 || klbf_ob[s].phase == 2) && (!klbf_ob[s].ordered || now - klbf_ob[s].ordered >= KLBF_OT_REORD)) {
            if (klbf_ob[s].phase == 1) {
                DWORD ent, node;
                if (!(ent = klh_rd32(klbf_ob[s].target + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, tgt, 0)) continue;
            } else if (klbf_ot_bwalk && (klbf_ot_called || klbf_ot_gat) && klbf_ot_box_frame(klbf_ot_bxbest, &t_bf)) memcpy(tgt, t_bf.T, 12);      /* OnlineBoxWalk (and the OnlineVanGather walk) */
            else if (van) memcpy(tgt, vpos, 12);
            else if (klbf_ot_vh) memcpy(tgt, klbf_ob[s].phase == 2 && !klbf_ot_called && klbf_ob[s].leg < klbf_way_n ? klbf_way_p[klbf_ob[s].leg] : klbf_ot_tpos, 12);      /* OnlineWaypoints: the current leg point while legs remain (klbf_way_n is 0 without a section) */      /* OnlineTacticsVan: to the exit box first, where the call is made */
            else continue;      /* never order a walk to the (0,0,0) default */
            memset(&t, 0, sizeof t); t.rec = -1; t.actor = a; t.soldier = bots[b].soldier; t.told_soft = 1;
            why[0] = 0;
            if (klbf_ot_sprint && klbf_ob[s].phase == 2) {      /* OnlineExitSprint: what the Defend goal does before its own order (0x686b96: block +0xc = the step's move style dword, +0x10 = 1 'style given'), with eDMS_Sprint */
                DWORD blk = klh_rd32(bots[b].soldier + 0x64c), sp = 2, cur = 0; BYTE one = 1;      /* eDMS_Sprint = 2: kl2.exe ZEnumInfo entry 0xcfccb8 (NotSet -1, Run 0, Walk 1, Sprint 2, Sneak 3, Relaxed 5, SneakRun 11) */
                if (blk && klh_rd32(blk + 0x14) == bots[b].soldier && klh_rd(blk + 0xc, &cur, 4) && (cur == sp || (klh_data((void *)(DWORD_PTR)(blk + 0xc), &sp, 4, "defend block move style (OnlineExitSprint)") && klh_data((void *)(DWORD_PTR)(blk + 0x10), &one, 1, "defend block style given (OnlineExitSprint)")))) {
                    if (!(klbf_ob[s].told & 2048) && (klbf_ob[s].told |= 2048)) klog("botfill: tactics: bot %d (actor %08lx): exit walk at Sprint (defend block %08lx move style was %lu)", s, a, blk, (unsigned long)cur);
                }
            }
            if (klbf_ob[s].phase == 2 && (klbf_ot_keepgo || klbf_ot_etrace)) {      /* OnlineExitKeepGoal: 0x760e50 with soft 0 on a RUNNING goal ([[soldier+0x648]+8] not 0 / 4) calls 0x7bbf70, which re-pushes it (0x760f25..0x760f2b) */
                DWORD gl = klh_rd32(bots[b].soldier + 0x648), gst = gl ? klh_rd32(gl + 8) : 0, blk = klh_rd32(bots[b].soldier + 0x64c); BYTE pend = 0, s4fc = 0; float bp[3];
                int haveBp = kle_block(bots[b].soldier, bp), onIt = gl && gst != 0 && gst != 4 && haveBp && (bp[0] - tgt[0]) * (bp[0] - tgt[0]) + (bp[2] - tgt[2]) * (bp[2] - tgt[2]) <= 1000.0f * 1000.0f;      /* GUESS: 10 m covers the place's nav snap */
                if (klbf_ot_etrace) {
                    if (blk) klh_rd(blk + 0x11, &pend, 1);
                    klh_rd(bots[b].soldier + 0x4fc, &s4fc, 1);
                    klog("botfill: tactics: exit trace bot %d (actor %08lx): at (%.0f, %.0f, %.0f) %.0f m to go, goal state %lu, block place (%.0f, %.0f, %.0f) pending %d, +0x4fc %d, +0x720 %lu, %s", s, a, bots[b].pos[0], bots[b].pos[1], bots[b].pos[2], (float)sqrt((bots[b].pos[0] - tgt[0]) * (bots[b].pos[0] - tgt[0]) + (bots[b].pos[2] - tgt[2]) * (bots[b].pos[2] - tgt[2])) / 100, (unsigned long)gst, haveBp ? bp[0] : 0, haveBp ? bp[1] : 0, haveBp ? bp[2] : 0, pend, s4fc, (unsigned long)klh_rd32(bots[b].soldier + 0x720), klbf_ot_keepgo && onIt && klbf_ob[s].ordered ? "goal still on it: no repeat" : "order");
                }
                if (klbf_ot_keepgo && onIt && klbf_ob[s].ordered) { klbf_ob[s].ordered = now; continue; }
            }
            if (kle_order2(&t, tgt, got, why, 0) == 1) {
                klbf_ob[s].ordered = now;
                if (klbf_ob[s].phase == 2 && !(klbf_ob[s].told & 512) && (klbf_ob[s].told |= 512)) klog("botfill: tactics: bot %d (actor %08lx): exit walk from (%.0f, %.0f, %.0f) to (%.0f, %.0f, %.0f), snapped goal (%.0f, %.0f, %.0f) (said once per trip)", s, a, bots[b].pos[0], bots[b].pos[1], bots[b].pos[2], tgt[0], tgt[1], tgt[2], got[0], got[1], got[2]);
            }
            else if (why[0] && !(klbf_ob[s].told & 2) && (klbf_ob[s].told |= 2)) klog("botfill: tactics: bot %d (actor %08lx): order refused: %s", s, a, why);
        }
    }
    klbf_ot_vidle = vnew;
    {   /* OnlineVanGather decision + OnlineVanHold pass: the walking bots' (phase 2) horizontal distance to the goal (box centre, else the exit trigger) */
        float gc[3], dmin = 1e30f, dmax = 0; int np = 0, q, r, have = klbf_ot_goal(gc);
        for (q = 0; have && q < nb; q++) {
            for (r = 0; r < KLBF_OT_BOTS && klbf_ob[r].actor != bots[q].actor; r++) ;
            if (r < KLBF_OT_BOTS && klbf_ob[r].phase == 2) {
                float d = (float)sqrt((bots[q].pos[0] - gc[0]) * (bots[q].pos[0] - gc[0]) + (bots[q].pos[2] - gc[2]) * (bots[q].pos[2] - gc[2]));
                np++; if (d < dmin) dmin = d; if (d > dmax) dmax = d;
            }
        }
        if (klbf_ot_gat && !klbf_ot_called && rules) {
            const char *rs = 0;
            if (!np) { klog("botfill: tactics: van: gather: no bot is walking to the box any more (all dead or gone): cancelled, the next bot at the exit starts it again"); klbf_ot_gat = 0; }
            else if (dmax <= klbf_ot_gm) rs = "all walking bots are in range";
            else if (now - klbf_ot_gatAt >= (DWORD)klbf_ot_gmax * 1000u) rs = "the wait ran out";
            else if (klbf_ot_late && left <= (float)(klbf_ot_late + 20)) rs = "the clock is low (OnlineLateExit + 20 s)";
            if (rs) {
                if (!klbf_ot_gtold++) klog("botfill: tactics: van: gather: calling the van (%s): %d bot(s) walking, the farthest %.0f m from the box (limit %.0f m), +%lu s since the first bot reached the exit, clock left %.0f s", rs, np, dmax / 100, klbf_ot_gm / 100, (unsigned long)((now - klbf_ot_gatAt) / 1000), left);
                klbf_ot_call_van(rules, klbf_ot_gcar);
            }
        }
        if (rules) klbf_vh_pass(rules, vstate, left, np ? dmin : 1e30f, now);
    }
}

static void klbf_tick(int game_thread)
{
    static DWORD last, scan, told_sm; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, h, v, lo, hi, p, tab, i, blk[64 * 32]; BYTE cur = 0, mx = 0;
    int conn, target, n = 0, ally = 0, alive = 0, tact = 0, other = 0;
    if (!(klbf_on || klbf_oh || klbf_ot) || !game_thread || !klh_exe_ok || now - last < 500) return;      /* OnlineHost alone only runs the census below (no lobby change: kllobby.c reads OnlineFill itself) */
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4) || !klh_rd(sm + 0xb9, &cur, 1) || !klh_rd(sm + 0xb8, &mx, 1)) return;
    if ((role != 2 && role != 3) || mode != 4) { if (state < 0xd) told_sm = 0; if (klbf_ot_in) klbf_ot_summary(); return; }
    if (state < 0xd || state > 0x1f) { if (state < 0xd) told_sm = 0; if (klbf_ot_in) klbf_ot_summary(); return; }
    if (klbf_ot && role == 2) {      /* HOST only */
        if (state == KLB_ROUND) klbf_ot_run(now, sm);
        else if (klbf_ot_in && (state >= 0x1f || state < KLB_ROUND)) klbf_ot_summary();      /* also when a restart/abort never reaches 0x1f, so the next round starts clean */
    }
    if (!(h = klh_rd32(sm + 4)) || !(v = klh_rd32(h + 8))) return;
    lo = klh_rd32(v + 8); hi = klh_rd32(v + 0xc);
    if (!lo || hi < lo || hi - lo > 16) return;
    conn = (int)(hi - lo);
    target = role == 2 && kllb_orig ? (int)kllb_orig : (int)cur;      /* host: the target before kllobby.c lowered it; a client sees the replicated one (GUESS: not lowered there) */
    if (told_sm != sm) {
        klog("botfill: role %lu state 0x%lx: lobby target %d (now [sm+0xb9] %u, max [sm+0xb8] %u), connected %d -> fill %d AI heister seat(s) wanted (NOT acted on: no code path adds a loot-taking heister online)",
             (unsigned long)role, (unsigned long)state, target, cur, mx, conn, target > conn ? target - conn : 0);
        told_sm = sm;
    }
    klbf_fill = target > conn ? target - conn : 0;
    if (klbf_sq && klbf_fill > 0 && klbf_sq_done != sm && state < KLB_ROUND) {      /* before the round: the squads are collected at the load */
        static DWORD sqlast; static int tries;
        if (now - sqlast >= 1000) { sqlast = now; if (klbf_squads(klbf_fill) > 0 || ++tries >= 8) { klbf_sq_done = sm; tries = 0; } }
    }
    if (state < 0x13 || now - scan < 5000) return;
    scan = now;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x10000 && n < 400; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], pr, team = 99, snd, t0 = 0, t1 = 0, t2 = 0, hp = 0; float hv[2] = { 0, 0 };
            if (o < 0x10000 || klh_avt(o) != 0x00bb3bac) continue;       /* ZFFActor */
            n++;
            if (!(pr = klh_rd32(o + 0x54)) || !klh_rd(pr + 4, &team, 4)) continue;
            if (team != 2) { other++; continue; }
            ally++;
            hp = klh_rd32(o + 0x5fc);
            if (hp && klh_rd(hp + 4, hv, 8) && hv[0] > 0) alive++;
            snd = klh_rd32(o + 0x77c);
            if (snd) { t0 = klh_rd32(snd + 0x5f0); t1 = klh_rd32(snd + 0x5f4); t2 = klh_rd32(snd + 0x5f8); }
            if (t0 || t1 || t2) tact++;
            if (ally <= 8) klog("botfill: Ally actor %08lx soldier %08lx tactics %08lx %08lx %08lx health %.1f", (unsigned long)o, (unsigned long)snd, (unsigned long)t0, (unsigned long)t1, (unsigned long)t2, hv[0]);
        }
    }
    klog("botfill: round census: %d ZFFActor, %d team Ally (%d alive, %d with tactics), %d other teams", n, ally, alive, tact, other);
    if (klbf_oh) klog("botfill: OnlineHost %s: %d Ally bot(s) in this peer's world, %d alive; %s", role == 2 ? "HOST (authority, shares their places)" : "CLIENT (mirror only, steered toward the host's places)", ally, alive,
                      role == 2 ? "their places go out as KLSY2 on UDP 27415" : "see 'sync: puppet:' lines with t=2 for the mirroring");
}

#endif /* KLBOTFILL_C */
