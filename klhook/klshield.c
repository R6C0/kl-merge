/*
 * klshield.c - THE HUMAN SHIELD IS WORTH HOLDING ([Shield], track SH, 2026-10-24). Part of KLHook (included by klhook.c AFTER
 * klcardown.c, which it sits beside; it borrows klbd_bot_ok / klbd_callable / KLBD_CALL / klbd_rdf from klbotdown.c). SHIP-safe:
 * data writes and the one game call klbotdown.c already makes, no code byte is patched. NOT RUN IN THE GAME (the owner was playing).
 *
 * THE OWNER (2026-10-24): 'rework the human shield system since it seems useless in the base game: you die just as quick, and if you
 * take an AI heister hostage it is basically useless; make it so you can down them in that animation state instead of them just going
 * down and shooting you instantly.'
 *
 * WHAT THE GAME DOES (READ, kl2.exe 0490, nothing run):
 *   - The player's hold is begun by the ZFFPlayer routine 0x4d7b00 (this = the player; it returns at once unless the session state
 *     [session+0x70] is 0x19 = a round): [player+0xad0] = the VICTIM (its argument), [player+0xad4] = the CARRIER = the player himself.
 *     The same fields are what the break-free prompt (0x860dc0), the camera selection (0x778f50: 'shield [player+0xad4] self') and
 *     the close-combat test (0x612c20) read; 0x6d1410 / 0x7cb9d0 write both back to 0 when the hold ends (so ad4 == self AND ad0 != 0
 *     is 'I hold somebody'). The same routine also asks 0x8b1270 on the victim's side.
 *   - An AI holding another actor goes through the ZFFActor routine 0x7034a0 ([holder+0x76c] = the held, [held+0x770] = the holder),
 *     released by 0x74fad0. Whether the PLAYER's hold of an AI also writes these is NOT READ: this part reads both, ad0/ad4 first.
 *   - The damage to the carrier is not shared with the victim anywhere: every bullet goes through the player's own routine 0x458880
 *     at full price (re\player_down.md 'WHY HE IS INVULNERABLE'). That is the owner's 'you die just as quick'.
 *   - The soldier's down routine (slot 51 = 0x688190 -> 0x70e0e0, the one klbotdown.c calls) has no 'held as a shield' refusal: its
 *     b test 0x70f330 refuses a CARRIED man ([actor+0x774], not +0x770), a seated man, a running hit animation (re\bots_down.md 9).
 *     So asking the down of a held man is allowed by the game's own rule (UNPROVEN that his hold animation survives it).
 *
 * WHAT THIS PART DOES, while you hold an AI soldier (heister bot or police / guard: any ZFFActor with a ZSoldier) in a round:
 *   1. COVER (Absorb=0.65): the part of any health you lose between two ticks is given back to you, Absorb x the loss, and the victim
 *      pays for it (HostageTakes x the share of YOUR maximum that was given back, taken of HIS maximum, never below 1 health: he is
 *      downed, not killed, by his own cover duty). The hit cannot be told by direction (the shooter is not in the record the health
 *      change leaves), so the 'frontal arc' is flat: every hit counts as hitting the hostage first. Once he is down the cover is
 *      AbsorbDown (0.30) x; dead = none. A hit that kills in one tick (the game's death is in the same routine) cannot be refunded.
 *   2. THE HOSTAGE GOES DOWN (revivable), not shot into a standing fall: when his health drops to DownPct (35 %) of his maximum, the
 *      game's own down is asked (the call klbotdown.c makes; every 100 ms for Seconds while the game's hit animation refuses once).
 *      Heister bots lie 'down not dead' and the KLBotDown revive helpers apply; a cop lies 1.5 .. 3 s (the stock goal) and gets up.
 *   3. THE RELEASE (ReleaseDown=1): the pass that sees your hold gone (you let go, the hold's timer, the game freed him) asks the
 *      same down for the man who stood in it, if he is alive and up - so the man you let go does not turn round and shoot you at once;
 *      he lies, as a man you floored. Dead or down men are left alone.
 *   The hold itself (the animation, the break-free) is the game's: nothing here calls the release routine 0x74fad0 (a GUESS-heavy call
 *   on the player's action state); a downed hostage is therefore still in your arms until you let go.
 *
 * KEYS ([Shield]):  Enable=1  Dry=0 (1 = log only: nothing written, nothing called)  Log=1 (2 = every refund)
 *   Absorb=0.65   AbsorbDown=0.30   HostageTakes=2.0 (0 = the victim loses nothing)   DownPct=35   Seconds=2.5   ReleaseDown=1   Down=1
 *
 * UNPROVEN (nothing here ran): that [pl+0xad0] is the victim ACTOR for an AI victim (it is read and logged at every hold start with the
 * vtable, soldier and [+0x770]; if it is not an actor with a soldier nothing is done: safe), that a health write on the player is not
 * undone by the game's per-frame health block logic (klbalance.c writes the same cell, so it takes), that the numbers feel right.
 */
#define KLSH_C

#define KLSH_PL_CARRIER 0xad4        /* [player+0xad4] == player while he holds somebody (0x4d7b71) */
#define KLSH_PL_VICTIM  0xad0        /* [player+0xad0] = the victim (0x4d7b6b) */
#define KLSH_ACT_HELD   0x76c        /* [actor+0x76c] = the held, set by 0x7034a0: the AI-holds-AI form (GUESS that the player's hold uses it too) */
#define KLSH_ACT_HOLDER 0x770        /* [victim+0x770] = the holder */

static struct {
    int on, dry, log, reldown, downhold; float absorb, absdown, takes, downpct, secs;
} klsh;

struct klsh_ask { int act; DWORD actor, soldier, t0, last; const char *why; };
static struct {
    DWORD rules, pl, victim, soldier, last_say;
    int holding, tries; float prev_hp, given, vgiven; DWORD t_hold;
    struct klsh_ask ask;
    int told_bad;
} klsh_g;

static int klsh_fin(float f) { return f == f && f > -1e9f && f < 1e9f; }

/* ---------------------------------------------------------------- pure arithmetic */

/* the health handed back for a loss d of a player whose maximum is mx: eff x d, never past the maximum */
static float klsh_refund(float hp_now, float d, float mx, float eff)
{
    float r = d * eff;
    if (!(r > 0)) return 0;
    if (hp_now + r > mx) r = mx - hp_now;
    return r > 0 ? r : 0;
}
/* the health the victim loses for a refund r of a player whose maximum is pmx: takes x (r / pmx) of HIS maximum vmx */
static float klsh_victim_loss(float r, float pmx, float vmx, float takes)
{
    if (!(pmx >= 1.0f) || !(r > 0) || !(takes > 0)) return 0;
    return takes * (r / pmx) * vmx;
}

/* ---------------------------------------------------------------- reading */

/* the victim of the local player's hold: 1 and actor / soldier, or 0 (nothing held, or what is held is not an AI soldier).
   ad4 == self and ad0 first (0x4d7b00); the ZFFActor form ([pl+0x76c], [held+0x770] == pl) as the fallback (GUESS). */
static int klsh_victim(DWORD pl, DWORD *actor, DWORD *soldier, DWORD *raw0, DWORD *raw4, DWORD *raw76c)
{
    DWORD car = klh_rd32(pl + KLSH_PL_CARRIER), v = klh_rd32(pl + KLSH_PL_VICTIM), s = 0, w = klh_rd32(pl + KLSH_ACT_HELD);
    *raw0 = v; *raw4 = car; *raw76c = w;
    if (car == pl && v && v != pl && klbd_bot_ok(v, &s)) { *actor = v; *soldier = s; return 1; }
    if (w && klbd_bot_ok(w, &s) && klh_rd32(w + KLSH_ACT_HOLDER) == pl) { *actor = w; *soldier = s; return 1; }
    return 0;
}

/* a health object {+4 now, +8 max, +0x24 owner}: 1 and the numbers */
static int klsh_health(DWORD owner, DWORD off, DWORD *obj, float *hp, float *mx)
{
    DWORD h = klh_rd32(owner + off); int ok = 1; float a, b;
    if (!h || klh_rd32(h + 0x24) != owner) return 0;
    a = klbd_rdf(h + 4, &ok); b = klbd_rdf(h + 8, &ok);
    if (!ok) return 0;
    *obj = h; *hp = a; *mx = b;
    return 1;
}

/* ---------------------------------------------------------------- the down */

static void klsh_ask_start(DWORD actor, DWORD soldier, const char *why, DWORD now)
{
    struct klsh_ask *a = &klsh_g.ask;
    if (a->act && a->actor == actor) return;
    memset(a, 0, sizeof *a);
    a->act = 1; a->actor = actor; a->soldier = soldier; a->t0 = a->last = now; a->why = why;
    klog("shield: the hostage %08lx is to be floored (%s)%s", (unsigned long)actor, why, klsh.dry ? " - Dry: nothing is called" : "");
}

static void klsh_ask_tick(DWORD now)
{
    struct klsh_ask *a = &klsh_g.ask; DWORD s = 0; BYTE dn = 0; float hp = 0; int ok = 1;
    if (!a->act) return;
    if ((long)(now - a->t0) > (long)(klsh.secs * 1000.0f)) { klog("shield: the down of %08lx was not given in %.1f s (%s) - stopped", (unsigned long)a->actor, klsh.secs, a->why); a->act = 0; return; }
    if (a->last != a->t0 && (long)(now - a->last) < 100) return;
    a->last = now;
    if (!klbd_bot_ok(a->actor, &s) || s != a->soldier) { a->act = 0; return; }
    { DWORD h = klh_rd32(a->actor + 0x5fc); if (h && klh_rd32(h + 0x24) == a->actor) hp = klbd_rdf(h + 4, &ok); }
    if (!ok || !(hp > 0.01f)) { klog("shield: %08lx is dead (health %.1f): no down to give", (unsigned long)a->actor, hp); a->act = 0; return; }
    klh_rd(a->actor + 0x64c, &dn, 1);
    if (dn) { klog("shield: %08lx is DOWN, NOT DEAD (health %.1f) - %s", (unsigned long)a->actor, hp, a->why); a->act = 0; return; }
    if (klsh.dry) { klog("shield: Dry - %08lx (health %.1f) WOULD be put down (%s)", (unsigned long)a->actor, hp, a->why); a->act = 0; return; }
    if (!klbd_callable()) { a->act = 0; return; }
    {
        BYTE r = (BYTE)KLBD_CALL(a->soldier);
        klh_rd(a->actor + 0x64c, &dn, 1);
        if (klsh.log >= 2 || (r && dn)) klog("shield: %08lx (health %.1f, %s): the game's down said %s (down byte %u)", (unsigned long)a->actor, hp, a->why, r ? "YES" : "NO, asked again", (unsigned)dn);
        if (r && dn) a->act = 0;
    }
}

/* ---------------------------------------------------------------- one pass */

static void klsh_forget(void) { memset(&klsh_g, 0, sizeof klsh_g); }

static void klsh_tick(int game_thread)
{
    struct klb_snap sn; DWORD rules, state, now, pl = 0, v = 0, s = 0, r0, r4, r76; float feet[3], np[3], hp = 0, mx = 0, vhp = 0, vmx = 0; int level, held, vok;
    DWORD ho = 0, vh = 0, D; BYTE vdn = 0; char why[200];
    if (!klsh.on || !game_thread || !klh_exe_ok) return;
    if (!(klr_arcade(&rules, &state, &level) && klb_level(why) && state == KLB_ROUND && klb_read(&sn) && sn.state == KLB_ROUND)) { if (klsh_g.rules) klsh_forget(); return; }
    if (sn.rules != klsh_g.rules) {
        klsh_forget(); klsh_g.rules = sn.rules;
        klog("shield: a round runs (%s): holding a hostage covers you (Absorb %.2f, down %.2f, victim pays x %.1f), he is floored at %.0f %% health and when let go (ReleaseDown %d)%s",
             why, klsh.absorb, klsh.absdown, klsh.takes, klsh.downpct, klsh.reldown, klsh.dry ? " - Dry: nothing is called, nothing is written" : "");
    }
    now = GetTickCount();
    klsh_ask_tick(now);
    if (!kle_human(&pl, feet, np) || !pl) { klsh_g.holding = 0; return; }
    held = klsh_victim(pl, &v, &s, &r0, &r4, &r76);
    if (!held) {
        if (klsh_g.holding) {                                        /* the hold has ended */
            DWORD ps = 0; float ph = 0; int ok = 1; BYTE dn = 0; DWORD h2;
            klog("shield: the hold is over after %.1f s (given back %.0f health to you, %.0f taken of the hostage %08lx)", (float)(now - klsh_g.t_hold) / 1000.0f, klsh_g.given, klsh_g.vgiven, (unsigned long)klsh_g.victim);
            if (klsh.reldown && klbd_bot_ok(klsh_g.victim, &ps) && ps == klsh_g.soldier) {
                h2 = klh_rd32(klsh_g.victim + 0x5fc);
                if (h2 && klh_rd32(h2 + 0x24) == klsh_g.victim) ph = klbd_rdf(h2 + 4, &ok); else ok = 0;
                klh_rd(klsh_g.victim + 0x64c, &dn, 1);
                if (ok && ph > 0.01f && !dn) klsh_ask_start(klsh_g.victim, klsh_g.soldier, "released", now);
            }
        }
        klsh_g.holding = 0; klsh_g.victim = 0;
        return;
    }
    if (!klsh_health(pl, 0xa48, &ho, &hp, &mx) || mx < 1.0f) return;
    vok = klsh_health(v, 0x5fc, &vh, &vhp, &vmx);
    klh_rd(v + 0x64c, &vdn, 1);
    D = klh_rd32(pl + 0x2948);
    if (!klsh_g.holding || klsh_g.victim != v) {                     /* a new hold */
        klsh_g.holding = 1; klsh_g.victim = v; klsh_g.soldier = s; klsh_g.pl = pl; klsh_g.prev_hp = hp; klsh_g.given = klsh_g.vgiven = 0; klsh_g.t_hold = now; klsh_g.tries = 0;
        klog("shield: YOU HOLD %08lx (raw [pl+0xad0] %08lx [pl+0xad4] %08lx (pl %08lx) [pl+0x76c] %08lx, [victim+0x770] %08lx; victim health %.0f of %.0f%s; your health %.0f of %.0f)",
             (unsigned long)v, (unsigned long)r0, (unsigned long)r4, (unsigned long)pl, (unsigned long)r76, (unsigned long)klh_rd32(v + KLSH_ACT_HOLDER), vhp, vmx, vdn ? ", already down" : "", hp, mx);
    }
    if (D && klh_rd32(D) == pl && klh_rd32(D + 4) != 0) { klsh_g.prev_hp = hp; return; }      /* you are down yourself: no cover to give */
    if (!vok) { klsh_g.prev_hp = hp; return; }
    {
        float eff = !(vhp > 0.01f) ? 0.0f : vdn ? klsh.absdown : klsh.absorb;
        float d = klsh_g.prev_hp - hp;
        if (hp > klsh_g.prev_hp) klsh_g.prev_hp = hp;
        else if (d > 0.05f && d < mx * 2.0f && eff > 0 && hp > 0.01f) {
            float rf = klsh_refund(hp, d, mx, eff), nh = hp + rf, loss = vdn ? 0.0f : klsh_victim_loss(rf, mx, vmx, klsh.takes), nv = vhp - loss;
            if (nv < 1.0f) nv = vhp > 1.0f ? 1.0f : vhp;
            if (rf > 0.01f) {
                if (klsh.dry) {
                    if (klsh.log >= 2 || now - klsh_g.last_say > 1000) { klsh_g.last_say = now; klog("shield: Dry - you lost %.1f (health %.1f): %.1f WOULD be given back, the hostage (health %.1f) WOULD lose %.1f", d, hp, rf, vhp, vhp - nv); }
                    klsh_g.prev_hp = hp;
                } else if (klh_data((void *)(DWORD_PTR)(ho + 4), &nh, 4, "the carrier's health: the part of a hit the human shield took (shield)")) {
                    klsh_g.given += rf; klsh_g.prev_hp = nh;
                    if (loss > 0 && nv != vhp && klh_data((void *)(DWORD_PTR)(vh + 4), &nv, 4, "the hostage's health: what he took of the carrier's hit (shield)")) { klsh_g.vgiven += vhp - nv; vhp = nv; }
                    if (klsh.log >= 2 || now - klsh_g.last_say > 1000) { klsh_g.last_say = now; klog("shield: hit of %.1f on you: %.1f given back (health %.1f -> %.1f), the hostage now %.1f of %.0f", d, rf, hp, nh, vhp, vmx); }
                } else klsh_g.prev_hp = hp;
            } else klsh_g.prev_hp = hp;
        } else klsh_g.prev_hp = hp;
    }
    if (klsh.downhold && !vdn && vhp > 0.01f && vhp <= (vmx * klsh.downpct / 100.0f > 1.0f ? vmx * klsh.downpct / 100.0f : 1.0f))
        klsh_ask_start(v, s, "his health reached the shield threshold", now);
    klsh_ask_tick(now);
}

/* ---------------------------------------------------------------- init */

static float klsh_inif(const char *key, const char *def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("Shield", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    if (!(v == v) || v < lo || v > hi) v = (float)atof(def);
    return v;
}

static void klsh_init(void)
{
    memset(&klsh, 0, sizeof klsh); klsh_forget();
    klsh.on = GetPrivateProfileIntA("Shield", "Enable", 1, klh_ini) != 0;
    if (!klsh.on) return;
    klsh.dry = GetPrivateProfileIntA("Shield", "Dry", 0, klh_ini) != 0;
    klsh.log = GetPrivateProfileIntA("Shield", "Log", 1, klh_ini);
    klsh.reldown = GetPrivateProfileIntA("Shield", "ReleaseDown", 1, klh_ini) != 0;
    klsh.downhold = GetPrivateProfileIntA("Shield", "Down", 1, klh_ini) != 0;
    klsh.absorb = klsh_inif("Absorb", "0.65", 0.0f, 0.95f);
    klsh.absdown = klsh_inif("AbsorbDown", "0.30", 0.0f, 0.95f);
    klsh.takes = klsh_inif("HostageTakes", "2.0", 0.0f, 20.0f);
    klsh.downpct = klsh_inif("DownPct", "35", 1.0f, 95.0f);
    klsh.secs = klsh_inif("Seconds", "2.5", 0.3f, 10.0f);
    klog("shield: on%s (Arcade round, a level that is not the stock one unless [KLHook] AllMaps=1): while you hold an AI soldier, %.0f %% of every hit on you is given back and he pays for it (x %.1f of his health); at %.0f %% health he is floored (revivable: Down %d); the man you let go is floored (ReleaseDown %d), %.1f s of asking",
         klsh.dry ? " (Dry=1: nothing is called, nothing is written)" : "", klsh.absorb * 100.0f, klsh.takes, klsh.downpct, klsh.downhold, klsh.reldown, klsh.secs);
}
