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
static int klbf_ot_hmul = 5, klbf_ot_van = 1, klbf_ot_gtake = 0; static float klbf_ot_guard = 2500.0f;      /* OnlineHealthMul, OnlineTacticsVan, OnlineTacticsGuard (cm) */
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

static struct { DWORD actor, target; int phase, grabs, tally; DWORD since, ordered; int told; float best; DWORD bestAt, idleAt; } klbf_ob[KLBF_OT_BOTS];
static DWORD klbf_ot_claimed[KLBF_OT_OBJ], klbf_ot_bad[KLBF_OT_OBJ]; static int klbf_ot_nclaim, klbf_ot_nbad, klbf_ot_rounds, klbf_ot_sm;
static DWORD klbf_ot_last;

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

static int klbf_ot_has(const DWORD *a, int n, DWORD v) { int i; for (i = 0; i < n; i++) if (a[i] == v) return 1; return 0; }

static void klbf_ot_summary(void)
{
    int i, bots = 0, tot = 0, boarded = 0;
    for (i = 0; i < KLBF_OT_BOTS; i++) if (klbf_ob[i].actor) { bots++; tot += klbf_ob[i].tally; if (klbf_ob[i].phase == 3) boarded++; }
    klog("botfill: tactics: round summary: %d bot(s) given orders, %d stack(s) taken, %d total (hook tally, not the game's), %d boarded, %d stack(s) given up", bots, klbf_ot_nclaim, tot, boarded, klbf_ot_nbad);
    klbf_ot_in = 0;
}

/* host, in a round, once a second. sm_state: caller checked role 2, mode 4 */
static void klbf_ot_run(DWORD now, DWORD sm)
{
    DWORD p, tab, i, blk[64 * 32], mo[KLBF_OT_OBJ], van = 0; float mpos[KLBF_OT_OBJ][3], vpos[3] = { 0, 0, 0 }; int mamt[KLBF_OT_OBJ], nm = 0, n = 0, b, nmoney = 0, nvan = 0;
    struct { DWORD actor, soldier; float pos[3]; } bots[KLBF_OT_BOTS]; int nb = 0; char why[100];
    static float cops[256][3]; int ncop = 0; DWORD rules = 0; int vstate = -1; float left = 1e9f;
    if (now - klbf_ot_last < 1000) return;
    klbf_ot_last = now;
    if (sm != (DWORD)klbf_ot_sm || !klbf_ot_in) {      /* a new session / round */
        if (klbf_ot_in) klbf_ot_summary();
        memset(klbf_ob, 0, sizeof klbf_ob); klbf_ot_nclaim = klbf_ot_nbad = 0; klbf_ot_sm = (int)sm; klbf_ot_in = 1; klbf_ot_rounds++;
        klbf_ot_trig = klbf_ot_tvt = klbf_ot_vh = klbf_ot_lookAt = 0; klbf_ot_trig_looked = klbf_ot_called = klbf_ot_looks = 0; klbf_ot_calledAt = 0;
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
        if (vstate >= 0 && vstate != lastv) { if (lastv != 0xff) klog("botfill: tactics: van state %u -> %d (clock left %.1f s, called %d, +%lu s since the call)", lastv, vstate, left, klbf_ot_called, klbf_ot_calledAt ? (unsigned long)((now - klbf_ot_calledAt) / 1000) : 0); lastv = (BYTE)vstate; }
    }
    if (!van && rules) {   /* [rules+0x1e4] = the escape vehicle (0x70f0a0, PROVEN), 0 until the vehicle is called (0x71e180 -> 0x84f030 fills the list slot 89 reads) */
        struct kle_veh v; float vp[3];
        if (kle_veh_read(rules, &v) == 1 && kle_node(klh_rd32(v.obj + 4), vp, 0) && (fabs(vp[0]) > 1 || fabs(vp[1]) > 1 || fabs(vp[2]) > 1)) { van = v.obj; memcpy(vpos, vp, 12); }
    }
    if (!van && klbf_ot_van && rules && !klbf_ot_trig_looked && klbf_ot_looks < 6 && (!klbf_ot_lookAt || now - klbf_ot_lookAt >= 20000)) {      /* the exit trigger: when the first bot carries money (a private-memory scan, klmove.c); a miss is retried every 20 s, 6 times a round */
        int q; for (q = 0; q < KLBF_OT_BOTS && !(klbf_ob[q].actor && klbf_ob[q].tally > 0); q++) ;
        if (q < KLBF_OT_BOTS) {
            DWORD t0 = GetTickCount(), ent, node;
            klbf_ot_lookAt = now; klbf_ot_looks++;
            klbf_ot_vh = klmv_exit_vehicle(&klbf_ot_trig);
            klbf_ot_tvt = klbf_ot_trig ? klh_rd32(klbf_ot_trig) : 0;
            if (klbf_ot_vh && (!(ent = klh_rd32(klbf_ot_trig + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, klbf_ot_tpos, 0) || !kle_ok3(klbf_ot_tpos))) klbf_ot_vh = 0;
            klog("botfill: tactics: van: exit trigger %08lx, vehicle field %08lx (kind %u), its place (%.0f, %.0f, %.0f) - found in %lu ms%s", klbf_ot_trig, klbf_ot_vh, klh_rd32(rules + 0x1ec) & 0xff,
                 klbf_ot_tpos[0], klbf_ot_tpos[1], klbf_ot_tpos[2], GetTickCount() - t0, klbf_ot_vh ? "" : ": none usable yet, looked again in 20 s");
            if (klbf_ot_vh) klbf_ot_trig_looked = 1;
        }
    }
    {   /* once per round, and again whenever the bot count changes: what the scan saw (BO2 gave no order and no clue why) */
        static int seen_round, seen_nb = -1, seen_nm = -1; static DWORD seen_van = 1;
        if (seen_round != klbf_ot_rounds || seen_nb != nb || seen_nm != nm || seen_van != van) { seen_round = klbf_ot_rounds; seen_nb = nb; seen_nm = nm; seen_van = van; klog("botfill: tactics: scan: %d objects, %d live Ally bot(s), %d armed stack(s) of %d money object(s), van %08lx (%d vehicle(s); one at the origin = not here yet)", n, nb, nm, nmoney, van, nvan); }
    }
    {   /* free the slot of a bot that is dead / gone (else its target stack stays "taken" and the 16 slots run out); boarded bots (phase 3) keep theirs for the summary */
        int q, r;
        for (q = 0; q < KLBF_OT_BOTS; q++) {
            if (!klbf_ob[q].actor || klbf_ob[q].phase == 3) continue;
            for (r = 0; r < nb && bots[r].actor != klbf_ob[q].actor; r++) ;
            if (r == nb) { klog("botfill: tactics: bot %d (actor %08lx) is dead or gone: slot freed (phase %d, tally %d)", q, klbf_ob[q].actor, klbf_ob[q].phase, klbf_ob[q].tally); memset(&klbf_ob[q], 0, sizeof klbf_ob[q]); }
        }
    }
    for (b = 0; b < nb; b++) {
        int s, j, best = -1; float bd = 1e30f, tgt[3], got[3]; struct kle_e t; DWORD a = bots[b].actor;
        for (s = 0; s < KLBF_OT_BOTS && klbf_ob[s].actor != a; s++) ;
        if (s == KLBF_OT_BOTS) { for (s = 0; s < KLBF_OT_BOTS && klbf_ob[s].actor; s++) ; if (s == KLBF_OT_BOTS) continue; klbf_ob[s].actor = a; }
        if (klbf_ob[s].phase == 3) continue;
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
                if (now - klbf_ob[s].bestAt > KLBF_OT_STALL || now - klbf_ob[s].since > KLBF_OT_STALLMAX) {
                    if (klbf_ot_nbad < KLBF_OT_OBJ) klbf_ot_bad[klbf_ot_nbad++] = o;
                    klog("botfill: tactics: bot %d (actor %08lx) did not reach stack %08lx (%.0f m left, %lu s walking, no 2 m of progress for %lu s): given up on it", s, a, o, dh / 100, (unsigned long)((now - klbf_ob[s].since) / 1000), (unsigned long)((now - klbf_ob[s].bestAt) / 1000)); klbf_ob[s].phase = 0;
                }
            }
        }
        if (klbf_ob[s].phase == 0) {
            int nguard = 0, gbest = -1; float gbd = 1e30f;
            for (j = 0; j < nm; j++) {
                float d; int c, guarded = 0;
                if (klbf_ot_has(klbf_ot_claimed, klbf_ot_nclaim, mo[j]) || klbf_ot_has(klbf_ot_bad, klbf_ot_nbad, mo[j])) continue;
                { int q, taken = 0; for (q = 0; q < KLBF_OT_BOTS; q++) if (q != s && klbf_ob[q].actor && klbf_ob[q].phase == 1 && klbf_ob[q].target == mo[j]) taken = 1; if (taken) continue; }
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
            if (klbf_ot_late && klbf_ob[s].tally > 0 && left <= (float)klbf_ot_late && best >= 0) {      /* OnlineLateExit (BO9 rules A/B): a carrier takes no new stack late in the round, it heads for the van */
                if (!(klbf_ob[s].told & 16) && (klbf_ob[s].told |= 16)) klog("botfill: tactics: bot %d (actor %08lx): clock left %.0f s <= OnlineLateExit %d: no new stack, tally %d goes to the van", s, a, left, klbf_ot_late, klbf_ob[s].tally);
                best = -1;
            }
            if (klbf_ob[s].grabs < klbf_ot_carry && best >= 0) {
                klbf_ob[s].phase = 1; klbf_ob[s].target = mo[best]; klbf_ob[s].since = now; klbf_ob[s].ordered = 0; klbf_ob[s].bestAt = 0; klbf_ob[s].idleAt = 0; klbf_ob[s].told &= ~4;
                memcpy(tgt, mpos[best], 12);
                klog("botfill: tactics: bot %d (actor %08lx soldier %08lx) -> stack %08lx (%d) at (%.0f, %.0f, %.0f), %.0f m away", s, a, bots[b].soldier, mo[best], mamt[best], tgt[0], tgt[1], tgt[2], bd / 100);
            } else if (klbf_ob[s].tally > 0) {      /* BO3: with nothing carried a bot waited at the van for nothing; it now waits for an armed stack */
                if (!van && !(klbf_ot_vh && !klbf_ot_called)) { if (!(klbf_ob[s].told & 1) && (klbf_ob[s].told |= 1)) klog("botfill: tactics: bot %d (actor %08lx): wants the van but it is not here and %s", s, a, klbf_ot_called ? "it was called already" : "no exit trigger was found to call it from"); continue; }
                klbf_ob[s].phase = 2; klbf_ob[s].since = now; klbf_ob[s].ordered = 0; klbf_ob[s].bestAt = 0; klbf_ob[s].idleAt = 0;
                if (van) klog("botfill: tactics: bot %d (actor %08lx) -> escape van %08lx at (%.0f, %.0f, %.0f) with tally %d (%d grab(s))", s, a, van, vpos[0], vpos[1], vpos[2], klbf_ob[s].tally, klbf_ob[s].grabs);
                else klog("botfill: tactics: bot %d (actor %08lx) -> exit trigger %08lx at (%.0f, %.0f, %.0f) to call the van, with tally %d (%d grab(s))", s, a, klbf_ot_trig, klbf_ot_tpos[0], klbf_ot_tpos[1], klbf_ot_tpos[2], klbf_ob[s].tally, klbf_ob[s].grabs);
            }
        }
        if (klbf_ob[s].phase == 2) {
            const float *g = van ? vpos : klbf_ot_tpos;
            float dd = (float)sqrt((bots[b].pos[0] - g[0]) * (bots[b].pos[0] - g[0]) + (bots[b].pos[2] - g[2]) * (bots[b].pos[2] - g[2]));
            if (van && dd <= 2 * klbf_ot_near) {
                klbf_ob[s].phase = 3;
                klog("botfill: tactics: bot %d (actor %08lx) BOARDED (hook tally only, nothing removed in the game): tally %d", s, a, klbf_ob[s].tally);
                continue;
            }
            if (!van && klbf_ot_vstate && klbf_ot_called && (vstate == 3 || vstate == 4) && dd <= 2 * klbf_ot_near && fabs(bots[b].pos[1] - g[1]) <= 400.0f) {      /* OnlineVanState: BO9's van node stayed at the origin, so the waiting state + the bot at the exit box counts as aboard */      /* GUESS: the exit trigger's box is where the van's boarding box is */
                klbf_ob[s].phase = 3;
                klog("botfill: tactics: bot %d (actor %08lx) BOARDED by van state %d (OnlineVanState; hook tally only, %.0f m from the exit trigger): tally %d", s, a, vstate, dd / 100, klbf_ob[s].tally);
                continue;
            }
            if (!van && klbf_ot_vh && !klbf_ot_called && dd <= 2 * klbf_ot_near && fabs(bots[b].pos[1] - g[1]) <= 400.0f) klbf_ot_call_van(rules, s);
            if (!van) {      /* review wp16tqkg2: phase 2 had no stall test; the trigger's node (its box centre, GUESS) may be out of the nav's reach */
                if (!klbf_ob[s].bestAt || dd < klbf_ob[s].best - 200.0f) { klbf_ob[s].best = dd; klbf_ob[s].bestAt = now; }
                if (klbf_ot_vh && !klbf_ot_called && now - klbf_ob[s].bestAt > KLBF_OT_STALL && dd <= 1500.0f && fabs(bots[b].pos[1] - g[1]) <= 400.0f) {
                    if (!(klbf_ob[s].told & 8) && (klbf_ob[s].told |= 8)) klog("botfill: tactics: bot %d (actor %08lx) stopped %.0f m from the exit trigger's centre: calls the van from there (GUESS: the box is wider than 2*Near)", s, a, dd / 100);
                    klbf_ot_call_van(rules, s);
                } else if (klbf_ot_vstate && klbf_ot_called ? (now - klbf_ot_calledAt > 60000 || vstate == 7 || (vstate == 0 && now - klbf_ot_calledAt > 5000)) : now - klbf_ob[s].since > (DWORD)(klbf_ot_called ? 60000 : KLBF_OT_STALLMAX)) {      /* OnlineVanState: the 60 s count from the CALL (BO9 counted from phase 2, 15 s earlier), and a van that left (7 / back to 0) ends the wait */
                    klog("botfill: tactics: bot %d (actor %08lx): %s after %lu s (%.0f m from the trigger): back to idle", s, a, klbf_ot_called ? "the van was called but this bot was not at the exit while it waited" : "did not reach the exit trigger", (unsigned long)((now - klbf_ob[s].since) / 1000), dd / 100);
                    klbf_ob[s].phase = 0; klbf_ob[s].told &= ~8;
                    continue;
                }
            }
        }
        if ((klbf_ob[s].phase == 1 || klbf_ob[s].phase == 2) && (!klbf_ob[s].ordered || now - klbf_ob[s].ordered >= KLBF_OT_REORD)) {
            if (klbf_ob[s].phase == 1) {
                DWORD ent, node;
                if (!(ent = klh_rd32(klbf_ob[s].target + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, tgt, 0)) continue;
            } else if (van) memcpy(tgt, vpos, 12);
            else if (klbf_ot_vh) memcpy(tgt, klbf_ot_tpos, 12);      /* OnlineTacticsVan: to the exit box first, where the call is made */
            else continue;      /* never order a walk to the (0,0,0) default */
            memset(&t, 0, sizeof t); t.rec = -1; t.actor = a; t.soldier = bots[b].soldier; t.told_soft = 1;
            why[0] = 0;
            if (kle_order2(&t, tgt, got, why, 0) == 1) klbf_ob[s].ordered = now;
            else if (why[0] && !(klbf_ob[s].told & 2) && (klbf_ob[s].told |= 2)) klog("botfill: tactics: bot %d (actor %08lx): order refused: %s", s, a, why);
        }
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
