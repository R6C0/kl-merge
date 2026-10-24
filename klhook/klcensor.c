/*
 * klcensor.c - [Censor] every killing head shot blows the head off (the pixelated censor), 2026-10-18. Part of KLHook
 * (included by klhook.c after klbot.c and klheliprobe.c: it uses klh_rd / klh_rd32 / klh_data / klb_level / KLE_ENTS /
 * kl_online). SHIP-SAFE: it writes HEAP DATA ONLY (one float per actor), no code, no constant (a ship build refuses those:
 * klh_may_write), no import slot. Since k31cen it also CALLS one game function (BlowHeadOff); a call writes nothing.
 *
 * WHY IT WORKS SOMETIMES (static read of kl2.exe build 0490, re\owner_feedback_1017.md item 9; nothing run):
 *   The kill handlers 0x5e54b9 and 0x7d08b0 (called at 0x8653bd) call BlowHeadOff (0x8d1380, the head-censor ring) only when
 *     [actor+0x600] >= vtable[0x678]() * 8.0        (the double at 0xb19588; for a ZFFActor vf678 = 0x574060 = [[actor+0x5fc]+8]
 *                                                    = the actor's MAXIMUM health, the same float klbalance.c's Tough scales)
 *   and the victim is not the local player (0x6fd7c0: actor == [[0xdd265c]+0x4cf0]). [actor+0x600] is the sum of the damage of
 *   head hits, added in the hit handler
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
 *   it reads like a head wound). Not covered by the pre-arm: the 800-unit range cutoff, the 17-slot ring and
 *   the on-screen test (x <= 0.995) of the render pass 0x7c3ce0.
 * k31cen (2026-10-24) LATE BLOW. The owner's play run: "works sometimes when they die / when down, but not when you check a dead body,
 *   not on the AI heisters, and it should happen to the player too". The pre-arm cannot reach those, because the kill check runs ONCE,
 *   at the death: a head shot on a CORPSE only adds to the sum and nothing ever reads it; the LOCAL PLAYER is skipped by the handlers
 *   (0x6fd7c0) and his sum is zeroed unread; a kill whose killer test (0x865380..0x86539b) fails never reaches the blow. So when a DEAD
 *   actor (health <= 0) has taken a head hit (its sum is neither 0, nor what we wrote, nor the last foreign value: the hit handler
 *   added to it) and its head is not blown yet (byte [actor+0x5cc], GUESS: BlowHeadOff stores 1 there first thing, 0x8d1383), the hook
 *   CALLS BlowHeadOff (0x8d1380, __thiscall actor) itself, 350 ms after it first saw the death so the game's own blow, made in the
 *   death's frame, goes first and is not doubled. For the player the head hit is remembered (lat) while he is alive, because the
 *   handler zeroes the sum at his death. Everything is the same on the stock FA maps (klb_level only gates on a stock LEVEL like the
 *   pre-arm did: a stock map stays untouched). GUESS: that 8689c0 still adds to the sum of a corpse ([actor+0x821] == 0); if it does
 *   not, a corpse shot is invisible to a heap-only hook and needs a hook on the hit (not ship-safe). Nothing here was run.
 * GUESS: that the sum is a float at +0x600 added by the head flag as above (the disassembly is read, the flag's meaning is
 *   not); that the check runs after the hit (if the kill check runs inside the same call as the hit, pre-arming is what makes
 *   it work, that is why the sum is armed BEFORE the hit and not after). That cops and civilians are ZFFActor 0xbb3bac (the
 *   only vtable klbot.c knows an actor by).
 * Online: the server decides (RMC), so the part is off in a network session unless [Censor] Online=1 (a test switch).
 * Keys: [Censor] Enable=1, Online=0, Log=0 (a line per armed count change, 'censor:'), Late=1 (corpse / player / missed kills),
 *   Player=1 (the late blow also on the local player).
 */
#define KLCN_ACTOR_VT 0x00bb3bac              /* ZFFActor */
#define KLCN_MAX      1024                    /* FA maps with many civilians + guards + cops can pass 256 actors (owner wants more civilians) */
#define KLCN_ARM      0.9995f

/* per actor memory. mine = the sum we wrote last; seen = the last foreign sum value (a head hit added to it);
   lat = a head hit was seen on this actor and no blow has happened since; ours = WE blew this head (until it is alive again);
   dead_at = tick when we first saw health <= 0 */
typedef struct { DWORD act; float mine, seen; DWORD dead_at; unsigned char lat, ours; } klcn_a;
static struct {
    int on, online, log, player, late, armed_now, told_lvl, lvl;
    klcn_a a[KLCN_MAX]; int n;
    DWORD scan_at, lvl_at, pass_at, said_at;
    int armed_total, blown_n, dead_fix_off;
} klcn;

/* the entity table's ZFFActors (the heli probe's walk: 64 slots a read, the object at slot+0x60) */
static void klcn_scan(void)
{
    DWORD p, tab, i, blk[64 * 32]; int n = 0, j;
    static klcn_a keep[KLCN_MAX];
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) { klcn.n = 0; return; }
    for (i = 0; i < 0x10000 && n < KLCN_MAX; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < KLCN_MAX; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4];
            if (o < 0x10000 || klh_rd32(o) != KLCN_ACTOR_VT) continue;
            memset(&keep[n], 0, sizeof keep[n]); keep[n].act = o;
            for (j = 0; j < klcn.n; j++) if (klcn.a[j].act == o) { keep[n] = klcn.a[j]; break; }     /* what we wrote last stays known */
            n++;
        }
    }
    memcpy(klcn.a, keep, n * sizeof keep[0]); klcn.n = n;
}

/* BlowHeadOff (0x8d1380, __thiscall actor, plain ret): the game's own head-censor call, the one the kill handlers make. It CALLS
   game code and writes nothing of ours, so a ship build may. A fault is caught and the late path is switched off for the session. */
static int klcn_blow(DWORD actor)
{
    int r = 0; WORD cw = 0;
    __asm fnstcw cw
    __try { ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(0x8d1380))((void *)(DWORD_PTR)actor, 0); }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        __asm fninit
        __asm fldcw cw
        r = -1;
    }
    if (r < 0) { klcn.dead_fix_off = 1; klog("censor: BlowHeadOff FAULTED at actor %08lx - the late blow is OFF for this session", (unsigned long)actor); return 0; }
    return 1;
}

static void klcn_tick(int game_thread)
{
    DWORD now = GetTickCount(), me = 0; int i, armed = 0; char why[200];
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
    { DWORD g = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c)); me = g ? klh_rd32(g + 0x4cf0) : 0; }   /* the local player's actor (0x6fd7c0 compares against it) */
    for (i = 0; i < klcn.n; i++) {
        klcn_a *c = &klcn.a[i];
        DWORD a = c->act, h; float cur, mx, want, hp[2]; int dead, head;
        if (klh_rd32(a) != KLCN_ACTOR_VT || !(h = klh_rd32(a + 0x5fc)) || !klh_rd(a + 0x600, &cur, 4) || !klh_rd(h + 4, hp, 8)) continue;
        mx = hp[1];
        if (!klb_finite(cur) || !klb_finite(mx) || mx < 1.0f || mx > 100000.0f) continue;
        want = (float)((double)mx * 8.0 * KLCN_ARM);
        dead = klb_finite(hp[0]) && hp[0] <= 0.0f;
        /* a head hit = the sum is neither 0 nor what we wrote nor the last foreign value (the hit handler 0x8689c0 added to it).
           For the local player the kill handler zeroes it at death, so the hit is remembered in lat while he is alive. */
        head = cur != 0.0f && cur != c->mine && cur != c->seen && cur != want;
        if (head) { c->seen = cur; c->lat = 1; }
        if (!dead) { c->dead_at = 0; c->ours = 0; }
        else if (!c->dead_at) c->dead_at = now ? now : 1;
        /* LATE BLOW: see the header. 350 ms after the death first showed. */
        if (dead && c->lat && !c->ours && !klcn.dead_fix_off && klcn.late && (a != me || klcn.player) && now - c->dead_at > 350) {
            BYTE fl = 0;
            if (klh_rd(a + 0x5cc, &fl, 1) && fl == 0 && klcn_blow(a)) {
                c->ours = 1; klcn.blown_n++;
                if (klcn.log || klcn.blown_n <= 40) klog("censor: late blow on actor %08lx (%s, head sum %.1f)", (unsigned long)a, a == me ? "the player" : "dead body", cur);
            }
            c->lat = 0;
            if (head && klh_data((void *)(DWORD_PTR)(a + 0x600), &want, 4, "head-hit damage sum re-armed after a late blow")) { c->mine = want; c->seen = want; }
            continue;
        }
        if (dead && c->lat && now - c->dead_at <= 350) continue;      /* give the game's own check its chance first */
        if (cur == want) { armed++; continue; }
        if (cur != 0.0f && cur != c->mine) continue;      /* a real head hit (or somebody else's number): leave it to the game */
        if (klh_data((void *)(DWORD_PTR)(a + 0x600), &want, 4, "head-hit damage sum, pre-armed so a killing head shot censors")) { c->mine = want; armed++; }
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
    klcn.late = GetPrivateProfileIntA("Censor", "Late", 1, klh_ini) != 0;       /* k31cen: corpse head shots, the player, missed kills */
    klcn.player = GetPrivateProfileIntA("Censor", "Player", 1, klh_ini) != 0;
    klog("censor: %s (a killing head shot blows the head off; heap data + one call of the game's BlowHeadOff for corpses; [Censor] Enable/Online/Log/Late/Player)", klcn.on ? "on" : "off");
}
