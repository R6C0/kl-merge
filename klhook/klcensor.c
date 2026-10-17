/*
 * klcensor.c - [Censor] every killing head shot blows the head off (the pixelated censor), 2026-10-18. Part of KLHook
 * (included by klhook.c after klbot.c and klheliprobe.c: it uses klh_rd / klh_rd32 / klh_data / klb_level / KLE_ENTS /
 * kl_online). SHIP-SAFE: it writes HEAP DATA ONLY (one float per actor), no code, no constant (a ship build refuses those:
 * klh_may_write), no import slot.
 *
 * WHY IT WORKS SOMETIMES (static read of kl2.exe build 0490, re\owner_feedback_1017.md item 9; nothing run):
 *   The kill handlers 0x5e54b9 and 0x7d08b0 (called at 0x8653bd) call BlowHeadOff (0x8d1380, the head-censor ring) only when
 *     [actor+0x600] >= vtable[0x678]() * 8.0        (the double at 0xb19588; for a ZFFActor vf678 = 0x574060 = [[actor+0x5fc]+8]
 *                                                    = the actor's MAXIMUM health, the same float klbalance.c's Tough scales)
 *   and the victim is not the local player. [actor+0x600] is the sum of the damage of head hits, added in the hit handler
 *   0x8689c0 (0x868d9c..0x868db2) only if the hit carries the flag [ebp+0x30] (GUESS: the head-shot flag), the attacker exists,
 *   0x6db900 is false (GUESS: server side) and the squared distance is <= 640000 (800 units). It is cleared to 0 at every check.
 *   So a head kill censors only when the head damage reached 8 x maximum health: a strong gun or a weak victim. A raised
 *   Tough, a lowered HeadShot / FedHeadShot ([Balance]) or a weak gun make it rare.
 *   The 8.0 at 0xb19588 is SHARED (over 20 other readers), so it must not be patched; the gate cannot be patched in a ship build.
 * WHAT THIS DOES: the sum is PRE-ARMED. Each pass, for every ZFFActor in the scene whose [actor+0x600] is 0 (or is the value
 *   this file wrote last), it writes 0.9995 x (8 x max health). A body hit adds nothing, so a body kill still reads below the
 *   threshold and censors nothing; any head hit that carries the flag adds more than the remaining 0.05 % (about 1.5 health
 *   points at the most) and the kill check passes. The game clears the sum after each check; the next pass arms it again.
 *   A head hit that does NOT kill leaves the sum armed too, so a later BODY kill of that actor also blows the head (accepted;
 *   it reads like a head wound). Not covered (needs code): the 800-unit range cutoff, the local player, the 17-slot ring and
 *   the on-screen test (x <= 0.995) of the render pass 0x7c3ce0.
 * GUESS: that the sum is a float at +0x600 added by the head flag as above (the disassembly is read, the flag's meaning is
 *   not); that the check runs after the hit (if the kill check runs inside the same call as the hit, pre-arming is what makes
 *   it work, that is why the sum is armed BEFORE the hit and not after). That cops and civilians are ZFFActor 0xbb3bac (the
 *   only vtable klbot.c knows an actor by).
 * Online: the server decides (RMC), so the part is off in a network session unless [Censor] Online=1 (a test switch).
 * Keys: [Censor] Enable=1, Online=0, Log=0 (a line per armed count change, 'censor:').
 */
#define KLCN_ACTOR_VT 0x00bb3bac              /* ZFFActor */
#define KLCN_MAX      256
#define KLCN_ARM      0.9995f

static struct {
    int on, online, log, armed_now, told_lvl, lvl;
    DWORD act[KLCN_MAX]; float mine[KLCN_MAX]; int n;
    DWORD scan_at, lvl_at, pass_at, said_at;
    int armed_total;
} klcn;

/* the entity table's ZFFActors (the heli probe's walk: 64 slots a read, the object at slot+0x60) */
static void klcn_scan(void)
{
    DWORD p, tab, i, blk[64 * 32]; int n = 0, j;
    DWORD keep[KLCN_MAX]; float keepf[KLCN_MAX];
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) { klcn.n = 0; return; }
    for (i = 0; i < 0x10000 && n < KLCN_MAX; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < KLCN_MAX; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4];
            if (o < 0x10000 || klh_rd32(o) != KLCN_ACTOR_VT) continue;
            keep[n] = o; keepf[n] = 0;
            for (j = 0; j < klcn.n; j++) if (klcn.act[j] == o) { keepf[n] = klcn.mine[j]; break; }     /* what we wrote last stays known */
            n++;
        }
    }
    memcpy(klcn.act, keep, n * sizeof keep[0]); memcpy(klcn.mine, keepf, n * sizeof keepf[0]); klcn.n = n;
}

static void klcn_tick(int game_thread)
{
    DWORD now = GetTickCount(); int i, armed = 0; char why[200];
    if (!klcn.on || !game_thread) return;
    if (now - klcn.pass_at < 50) return;
    klcn.pass_at = now;
    if (!klx_on) return;
    if (now - klcn.lvl_at > 1000 || !klcn.lvl_at) {          /* the level verdict once a second: a stock level is never touched */
        klcn.lvl_at = now; klcn.lvl = klb_level(why);
        if (klcn.lvl != klcn.told_lvl) { klcn.told_lvl = klcn.lvl; klog("censor: %s: %s", klcn.lvl ? "on" : "idle", why); }
    }
    if (!klcn.lvl) { klcn.n = 0; return; }
    if (!klcn.online && kl_online()) return;
    if (!klcn.scan_at || now - klcn.scan_at > 1500) { klcn.scan_at = now; klcn_scan(); }
    for (i = 0; i < klcn.n; i++) {
        DWORD a = klcn.act[i], h; float cur, mx, want;
        if (klh_rd32(a) != KLCN_ACTOR_VT || !(h = klh_rd32(a + 0x5fc)) || !klh_rd(a + 0x600, &cur, 4) || !klh_rd(h + 8, &mx, 4)) continue;
        if (!klb_finite(cur) || !klb_finite(mx) || mx < 1.0f || mx > 100000.0f) continue;
        want = (float)((double)mx * 8.0 * KLCN_ARM);
        if (cur == want) { armed++; continue; }
        if (cur != 0.0f && cur != klcn.mine[i]) continue;      /* a real head hit (or somebody else's number): leave it to the game */
        if (klh_data((void *)(DWORD_PTR)(a + 0x600), &want, 4, "head-hit damage sum, pre-armed so a killing head shot censors")) { klcn.mine[i] = want; armed++; }
    }
    klcn.armed_now = armed;
    if (klcn.log && armed != klcn.armed_total && now - klcn.said_at > 2000) {
        klcn.said_at = now; klcn.armed_total = armed;
        klog("censor: %d of %d actors armed (the head-hit sum [actor+0x600] stands at 0.9995 x 8 x max health)", armed, klcn.n);
    }
}

static void klcn_init(void)
{
    klcn.on = GetPrivateProfileIntA("Censor", "Enable", 1, klh_ini) != 0;
    klcn.online = GetPrivateProfileIntA("Censor", "Online", 0, klh_ini) != 0;
    klcn.log = GetPrivateProfileIntA("Censor", "Log", 0, klh_ini) != 0;
    klog("censor: %s (a killing head shot blows the head off; heap data only; [Censor] Enable/Online/Log)", klcn.on ? "on" : "off");
}
