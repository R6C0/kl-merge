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

static struct { DWORD actor, target; int phase, grabs, tally; DWORD since, ordered; int told; float best; DWORD bestAt; } klbf_ob[KLBF_OT_BOTS];
static DWORD klbf_ot_claimed[KLBF_OT_OBJ], klbf_ot_bad[KLBF_OT_OBJ]; static int klbf_ot_nclaim, klbf_ot_nbad, klbf_ot_rounds, klbf_ot_sm;
static DWORD klbf_ot_last;

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
    if (now - klbf_ot_last < 1000) return;
    klbf_ot_last = now;
    if (sm != (DWORD)klbf_ot_sm || !klbf_ot_in) {      /* a new session / round */
        if (klbf_ot_in) klbf_ot_summary();
        memset(klbf_ob, 0, sizeof klbf_ob); klbf_ot_nclaim = klbf_ot_nbad = 0; klbf_ot_sm = (int)sm; klbf_ot_in = 1; klbf_ot_rounds++;
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
            } else if (klh_avt(o) == 0x00bb3bac && nb < KLBF_OT_BOTS) {
                DWORD pr, team = 99, hp, snd; float hv[2] = { 0, 0 };
                if (!(pr = klh_rd32(o + 0x54)) || !klh_rd(pr + 4, &team, 4) || team != 2) continue;
                if (!(hp = klh_rd32(o + 0x5fc)) || !klh_rd(hp + 4, hv, 8) || !(hv[0] > 0)) continue;      /* alive */
                if (!(snd = klh_rd32(o + 0x77c)) || klh_rd32(snd) != KLE_SOLDIER_VT) continue;
                if (!klh_rd(o + 0x460, pos, 12) || !kle_ok3(pos)) continue;      /* feet, as klcrew_rt.c (ASSUMPTION: same base class as a player) */
                bots[nb].actor = o; bots[nb].soldier = snd; memcpy(bots[nb].pos, pos, 12); nb++;
            }
        }
    }
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
    if (!van) {   /* the van the FA rules name: rules = [[0x168e9e4]+0x54] when the session's game type [sm+0x5c] is 4 (0x7bb2a0, PROVEN; 0x508ef0 is
                     Arcade-only); [rules+0x1e4] = the escape vehicle (0x70f0a0, PROVEN), 0 until the game sets it up (GUESS: at the call) */
        DWORD s0 = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598)), hd, rules; struct kle_veh v; float vp[3];
        if (s0 && klh_rd32(s0 + 0x5c) == 4 && (hd = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4))) && (rules = klh_rd32(hd + 0x54))
            && kle_veh_read(rules, &v) == 1 && kle_node(klh_rd32(v.obj + 4), vp, 0) && (fabs(vp[0]) > 1 || fabs(vp[1]) > 1 || fabs(vp[2]) > 1)) { van = v.obj; memcpy(vpos, vp, 12); }
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
            for (j = 0; j < nm; j++) {
                float d;
                if (klbf_ot_has(klbf_ot_claimed, klbf_ot_nclaim, mo[j]) || klbf_ot_has(klbf_ot_bad, klbf_ot_nbad, mo[j])) continue;
                { int q, taken = 0; for (q = 0; q < KLBF_OT_BOTS; q++) if (q != s && klbf_ob[q].actor && klbf_ob[q].phase == 1 && klbf_ob[q].target == mo[j]) taken = 1; if (taken) continue; }
                d = kle_dist(bots[b].pos, mpos[j]);
                if (d < bd) { bd = d; best = j; }
            }
            if (klbf_ob[s].grabs < klbf_ot_carry && best >= 0) {
                klbf_ob[s].phase = 1; klbf_ob[s].target = mo[best]; klbf_ob[s].since = now; klbf_ob[s].ordered = 0; klbf_ob[s].bestAt = 0;
                memcpy(tgt, mpos[best], 12);
                klog("botfill: tactics: bot %d (actor %08lx soldier %08lx) -> stack %08lx (%d) at (%.0f, %.0f, %.0f), %.0f m away", s, a, bots[b].soldier, mo[best], mamt[best], tgt[0], tgt[1], tgt[2], bd / 100);
            } else if (klbf_ob[s].tally > 0) {      /* BO3: with nothing carried a bot waited at the van for nothing; it now waits for an armed stack */
                if (!van) { if (!(klbf_ob[s].told & 1) && (klbf_ob[s].told |= 1)) klog("botfill: tactics: bot %d (actor %08lx): wants the van but no ZAnimatedVehicle is in the entity table yet", s, a); continue; }
                klbf_ob[s].phase = 2; klbf_ob[s].since = now; klbf_ob[s].ordered = 0;
                klog("botfill: tactics: bot %d (actor %08lx) -> escape van %08lx at (%.0f, %.0f, %.0f) with tally %d (%d grab(s))", s, a, van, vpos[0], vpos[1], vpos[2], klbf_ob[s].tally, klbf_ob[s].grabs);
            }
        }
        if (klbf_ob[s].phase == 2) {
            float dd = (float)sqrt((bots[b].pos[0] - vpos[0]) * (bots[b].pos[0] - vpos[0]) + (bots[b].pos[2] - vpos[2]) * (bots[b].pos[2] - vpos[2]));
            if (van && dd <= 2 * klbf_ot_near) {
                klbf_ob[s].phase = 3;
                klog("botfill: tactics: bot %d (actor %08lx) BOARDED (hook tally only, nothing removed in the game): tally %d", s, a, klbf_ob[s].tally);
                continue;
            }
        }
        if ((klbf_ob[s].phase == 1 || klbf_ob[s].phase == 2) && (!klbf_ob[s].ordered || now - klbf_ob[s].ordered >= KLBF_OT_REORD)) {
            if (klbf_ob[s].phase == 1) {
                DWORD ent, node;
                if (!(ent = klh_rd32(klbf_ob[s].target + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, tgt, 0)) continue;
            } else { if (!van) continue; memcpy(tgt, vpos, 12); }      /* never order a walk to the (0,0,0) default */
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
