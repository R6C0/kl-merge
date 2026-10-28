/*
 * klbench_down.c - [Bench] SelfDownAt / SelfDownRound / SelfDownDamage / SelfDownKind / SelfDownDry: BENCH ONLY (2026-10-27, NOT RUN).
 * Part of KLHook (included by klhook.c AFTER klucc_down.c; ticked from the game thread). Default SelfDownAt=0 = nothing, nothing read.
 *
 * WHY: the two-instance scripted online benches never see a death, so the KILLED BY text ([HUD] OnlineKilledStock / OnlineKilled), the kill
 * feed and the 'names: KilledStock:' lines cannot be checked. This makes the LOCAL player's own body take one hit through the game's real path.
 *
 * THE PATH (READ in kl2.exe build 0490 with capstone, re/ucc_down_only.md section 2): ZFFPlayer vtable slot 422 (vt+0x698) = 0x7e1700,
 * thiscall(player, hit record*) ret 4 - the same entry an AI bullet on a human uses. For a victim that is local (vt+0x3d0 true, 0x7e1720) or
 * offline (0x863a60 false, 0x7e1712) it calls slot 423 (vt+0x69c) = 0x458880 = the damage routine: multipliers, the down trigger 0x8da3b0
 * (0x458e7f), then the health change 0x6e3400(victim, -damage, attacker), the death branch and the kill-feed / rules bookkeeping (0x5c2f00).
 * A NULL attacker [rec+0] is handled (0x7e1743 / 0x7e17f9), 0x458fcf onward tests ebp for 0. The game itself then replicates the health
 * (RMCUpdateHitPoints) and the death, and the stock panel text comes from the game.
 * RECORD (READ in the rebuild of RMCReceiveHit, 0x891490 0x8914f1..0x89157f): zero dword block, +0x00 attacker object (0 = none),
 * +0x08 kind (dword; 1 = bullet), +0x0c second object (0), +0x28 float damage, +0x2c float momentum (0), +0x30 byte headshot (0). I give it 0x80 zero bytes.
 * ATTACKER: 0 = the environment (no AI cop is looked up: no cop resolver exists in the hook that is safe to call from here; GUESS that the stock
 * panel then prints its no-killer text, which is what OnlineKilledStock is meant to show). Logged on the line.
 * The down trigger (0x8da3b0) swallows a hit when health <= 40 % under a burst or kind 9: DAMAGE default 10000 of kind 1 KILLS from full health
 * unless the trigger floors the player first (that too is a stock result and is logged as the health after).
 *
 * KEYS ([Bench]):  SelfDownAt=<seconds in state 0x19, 0 = off>  SelfDownRound=<n, default 1> (the n-th time this process sees session state 0x19;
 *   GUESS that this is the round number: a restart 0x19 -> 0x16 -> 0x19 counts again)  SelfDownDamage=<float, default 10000>
 *   SelfDownKind=<int, default 1>  SelfDownDry=1 (log only: the resolved function and the record, nothing called).
 * Once per run of that round (one-shot per 0x19 entry); __try around the call; only the local body (klh_slot_player_mine) of class ZFFPlayer.
 * LOG: "benchdown: ..." lines.
 */
#define KLBK_C
#define KLBK_SESSION   0x0168e598u       /* session manager pointer; [+0x70] = state (klauto.c: 0x19 = the round runs) */

static struct { int at, round, kind, dry, n19, done, inited, rep, gap, shots; float dmg; DWORD t0, last_st, lastlog, lastshot; } klbk;

static void klbk_init(void)
{
    char t[40];
    memset(&klbk, 0, sizeof klbk);
    klbk.at = GetPrivateProfileIntA("Bench", "SelfDownAt", 0, klh_ini);
    klbk.round = GetPrivateProfileIntA("Bench", "SelfDownRound", 1, klh_ini);
    klbk.kind = GetPrivateProfileIntA("Bench", "SelfDownKind", 1, klh_ini);
    klbk.dry = GetPrivateProfileIntA("Bench", "SelfDownDry", 0, klh_ini) != 0;
    GetPrivateProfileStringA("Bench", "SelfDownDamage", "10000", t, sizeof t, klh_ini);
    klbk.dmg = (float)atof(t);
    /* SelfDownRepeat=<shots, default 1>, SelfDownGap=<ms between shots, default 1500>: the down trigger needs health <= 40 % BEFORE the hit
     * (GU2 10-28: one 70 hit took 550 -> 480 and nothing more), so a bench gives a first hit that leaves < 40 % and a second that floors */
    klbk.rep = GetPrivateProfileIntA("Bench", "SelfDownRepeat", 1, klh_ini);
    klbk.gap = GetPrivateProfileIntA("Bench", "SelfDownGap", 1500, klh_ini);
    if (klbk.rep < 1 || klbk.rep > 20) klbk.rep = 1;
    if (klbk.gap < 100 || klbk.gap > 60000) klbk.gap = 1500;
    if (klbk.at < 0 || klbk.at > 36000) klbk.at = 0;
    if (klbk.round < 1 || klbk.round > 99) klbk.round = 1;
    if (klbk.kind < 0 || klbk.kind > 20) klbk.kind = 1;
    if (!(klbk.dmg == klbk.dmg) || klbk.dmg < 0.0f || klbk.dmg > 1e6f) klbk.dmg = 10000.0f;
    klbk.last_st = 0xffffffffu;
    klbk.inited = 1;
    if (klbk.at) klog("benchdown: SelfDownAt=%d s, round %d, damage %.1f, kind %d, %s, attacker 0 (the environment) (bench only)", klbk.at, klbk.round, klbk.dmg, klbk.kind, klbk.dry ? "DRY (log only)" : "LIVE");
}

static void klbk_tick(int game_thread)
{
    DWORD sm, st, pl, vt, fn, now;
    BYTE rec[0x80];
    if (!klbk.inited || !klbk.at || !game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLBK_SESSION)))) return;
    if (!klh_rd(sm + 0x70, &st, 4)) return;
    if (st != klbk.last_st) {                         /* a state change: entering 0x19 starts the clock of a round */
        if (st == 0x19) { klbk.n19++; klbk.t0 = now; klbk.done = 0; klbk.shots = 0; klog("benchdown: session state 0x19 entered (the %d. time)", klbk.n19); }
        klbk.last_st = st;
    }
    if (st != 0x19 || klbk.done || klbk.n19 != klbk.round) return;
    if (now - klbk.t0 < (DWORD)klbk.at * 1000u) return;
    if (klbk.shots && now - klbk.lastshot < (DWORD)klbk.gap) return;
    if (!(pl = klh_slot_player_mine()) || klh_pvt(pl) != 0x00bb45f4u) {
        if (now - klbk.lastlog >= 5000) { klbk.lastlog = now; klog("benchdown: waiting, no local ZFFPlayer body yet (slot %08lx)", pl); }
        return;
    }
    vt = klh_rd32(pl); fn = klh_rd32(vt + 0x698);     /* a private copy of the vtable (NetSmooth) keeps the stock slot: read from the body */
    if (fn < (DWORD)(DWORD_PTR)KLH_VA(0x401000) || fn > (DWORD)(DWORD_PTR)KLH_VA(0xb00000)) { klbk.done = 1; klog("benchdown: REFUSED, slot 422 of %08lx is %08lx (not in the code)", pl, fn); return; }
    memset(rec, 0, sizeof rec);
    *(DWORD *)(rec + 0x08) = (DWORD)klbk.kind;
    *(float *)(rec + 0x28) = klbk.dmg;
    klbk.lastshot = now;
    if (++klbk.shots >= klbk.rep) klbk.done = 1;      /* SelfDownRepeat shots per round */
    {
        float h0 = 0, h1 = 0; DWORD ho = klh_rd32(pl + 0xa48), hv = 0;
        if (ho) { hv = klh_rd32(ho + 4); h0 = *(float *)&hv; }
        klog("benchdown: %s at %d s into round %d: player %08lx slot 422 = %08lx (stock 0x7e1700 = %08lx), record kind %d damage %.1f attacker 0, health %.1f before",
             klbk.dry ? "DRY" : "CALL", klbk.at, klbk.round, pl, fn, (DWORD)(DWORD_PTR)KLH_VA(0x7e1700), klbk.kind, klbk.dmg, h0);
        if (klbk.dry) return;
        __try { ((void (__fastcall *)(void *, void *, void *))(DWORD_PTR)fn)((void *)(DWORD_PTR)pl, 0, rec); }
        __except (EXCEPTION_EXECUTE_HANDLER) { klbk.done = 1; klog("benchdown: the call FAULTED (caught); nothing more is done"); return; }
        if (ho) { hv = klh_rd32(ho + 4); h1 = *(float *)&hv; }
        klog("benchdown: shot %d of %d returned, health %.1f after (<= 0 = dead; the stock text / feed / 'names: KilledStock:' lines follow)", klbk.shots, klbk.rep, h1);
    }
}
