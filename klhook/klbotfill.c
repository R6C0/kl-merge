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

static void klbf_init(void)
{
    klbf_on = GetPrivateProfileIntA("Bots", "OnlineFill", 0, klh_ini) != 0;
    klbf_sq = klbf_on && GetPrivateProfileIntA("Bots", "OnlineFillSquads", 0, klh_ini) != 0;      /* TEST first: the squads of the first `fill` heister slots are kept online */
    klbf_oh = GetPrivateProfileIntA("BotFill", "OnlineHost", 0, klh_ini) != 0;
    if (klbf_oh) klog("botfill: OnlineHost=1 - the HOST is the only authority over the Ally bots: it shares their places (klsync.c Share), a client mirrors them (Puppet, team 2) and owns none; it activates NOTHING (the level must keep the squads online: tools/kl_botsonline.py zip)");
    if (klbf_on) klog("botfill: OnlineFill=1 - plan and probe lines for the empty lobby seats (read-only; Ready may start below the lobby target)");
}

static void klbf_tick(int game_thread)
{
    static DWORD last, scan, told_sm; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, h, v, lo, hi, p, tab, i, blk[64 * 32]; BYTE cur = 0, mx = 0;
    int conn, target, n = 0, ally = 0, alive = 0, tact = 0, other = 0;
    if (!(klbf_on || klbf_oh) || !game_thread || !klh_exe_ok || now - last < 500) return;      /* OnlineHost alone only runs the census below (no lobby change: kllobby.c reads OnlineFill itself) */
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4) || !klh_rd(sm + 0xb9, &cur, 1) || !klh_rd(sm + 0xb8, &mx, 1)) return;
    if ((role != 2 && role != 3) || mode != 4) { if (state < 0xd) told_sm = 0; return; }
    if (state < 0xd || state > 0x1f) { if (state < 0xd) told_sm = 0; return; }
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
