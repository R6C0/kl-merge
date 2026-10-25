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
 *   OnlineFill=0     0 = off (the game's own rule: no AI heisters online). 1 = plan + probe lines, Ready may start below the target
 */
#ifndef KLBOTFILL_C
#define KLBOTFILL_C

static int klbf_on;

static void klbf_init(void)
{
    klbf_on = GetPrivateProfileIntA("Bots", "OnlineFill", 0, klh_ini) != 0;
    if (klbf_on) klog("botfill: OnlineFill=1 - plan and probe lines for the empty lobby seats (read-only; Ready may start below the lobby target)");
}

static void klbf_tick(int game_thread)
{
    static DWORD last, scan, told_sm; DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, h, v, lo, hi, p, tab, i, blk[64 * 32]; BYTE cur = 0, mx = 0;
    int conn, target, n = 0, ally = 0, alive = 0, tact = 0, other = 0;
    if (!klbf_on || !game_thread || !klh_exe_ok || now - last < 500) return;
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
    if (state < 0x13 || now - scan < 5000) return;
    scan = now;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x10000 && n < 400; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], pr, team = 99, snd, t0 = 0, t1 = 0, t2 = 0, hp = 0; float hv[2] = { 0, 0 };
            if (o < 0x10000 || klh_rd32(o) != 0x00bb3bac) continue;       /* ZFFActor */
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
}

#endif /* KLBOTFILL_C */
