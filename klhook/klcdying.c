/*
 * klcdying.c - ALMOST DEAD = THE REVIVABLE FLOOR, FOR YOU AND THE AI HEISTERS (track dying-down, 2026-10-24; hook k31dyn).
 * Part of KLHook (included by klhook.c AFTER klcardown.c, whose KLCD_HUMAN_CALL it uses; its tick runs after klcd_tick).
 * SHIP-safe: data writes and game calls only, no code byte is patched. NOT RUN IN THE GAME (the owner was playing).
 *
 * THE OWNER (2026-10-24, after a play run): 'i think the cops when they do that down state but theyre almost dead but dont
 * shoot should happen to the player and ai heisters ... should happen to the player or just anyone that gets headshot' (the
 * head-shot censor is klcensor.c's, not touched here).
 *
 * WHAT THE GAME HAS (READ, kl2.exe 0490; re\player_down.md, re\bots_down.md): ONE near-death state, the 'down, not dead' goal
 * (ZDownNotDeadNPC@CPPScript, script 0x5f4ac0): the man lies, takes hits in full, comes up with health. A policeman gets it
 * at health 0 by the stock rule (0x70e0e0); he does not go on shooting. There is no second 'writhe' state: the Wounded clips
 * (ZWounded 0x865180) are the DEATH animations. So 'the cop state for you and the heisters' = this same down, entered BEFORE
 * the killing hit and with the gun held:
 *   AI HEISTERS  already enter it from klbotdown.c at DownPct of their health (live: 33 downs in the owner's run) - but
 *                [BotDown] NoFire defaulted 0, so a downed heister went on shooting from the floor (the owner's 'dont shoot').
 *                This part turns NoFire on (Bots=1, key BotNoFire; klbotdown's own pass clears the soldier's target
 *                [soldier+0xb0] each pass while he lies: ASSUMED safe, re\bots_down.md live check B3 is still open).
 *   YOU          already enter it from kldown.c, but only for a BURST (hits of 20+ health adding up to 120 within 1 s, at 40 %
 *                or less): a few big bullets, or a slow bleed, kill you straight from 'up'. This part asks the game's
 *                own trigger 0x8da3b0(D, record kind 9) - the call klcardown.c makes for a blast, exactly what the damage
 *                routine 0x458e7f makes - as soon as your health is at or under HumanPct per cent of the maximum, you are
 *                up, not police and the down cooldown [D+0x38] has run out. Kind 9 skips the health and burst tests
 *                (0x8da409). The fall costs nothing, the game gives at least [T+0x25c] health, kldown.c's NoFire holds the
 *                gun, the mash / helper get-up applies. Chance (per cent, one draw per episode) gates it.
 *   HEAD SHOTS  still kill: the ask comes from health, between two hits; a head hit x10 takes a man from above the threshold
 *                to 0 in ONE frame (re\bots_down.md: the 'traitor' kills), which no frame-rate ask can stop. Wanted: they kill.
 *
 * KEYS ([Dying]):  Enable=1 (a round, Arcade, a level that is not the stock one; [KLHook] AllMaps=1 counts the stock ones)
 *   Dry=0 (1 = log only, nothing called, nothing written)  Log=1 (2 = every attempt)
 *   Human=1  HumanPct=30 (health per cent of the maximum at or under which you are asked down)  Chance=100 (per cent of the
 *   episodes that become a down; the rest die as stock)  Seconds=2.5 (how long the ask is repeated, every 100 ms: the game
 *   refuses once while a hit animation plays)  Bots=1 (the heisters' gun is held on the floor: sets [BotDown] NoFire; applies even with Dry=1)
 *
 * GUESSES (nothing here ran): that trigger 0x8da3b0 accepts a zeroed record of kind 9 with no attacker when called from the
 * tick and not from inside the damage routine (klcardown.c's Dry=1 run has not shown it either); that [D+0x38] is a float
 * of seconds (kldown.c's header says 'seconds until he can go down again'); that the health object keeps the maximum at +8
 * (kldown.c reads it so). A refusal is logged and the ask is given up after Seconds: he then dies as stock.
 */
#define KLDY_C

static struct {
    int on, dry, log, human, bots, chance_known;
    float human_pct, chance, secs;
} kldy;

static struct { DWORD rules, ep_start, last_try; int ep, tries, in_ep, rolled_yes, told_cool; DWORD player; } kldy_s;

/* the per cent a draw must land under: pure, tested off-game */
static int kldy_draw_yes(float chance_pct, unsigned r)
{
    if (chance_pct >= 100.0f) return 1;
    if (chance_pct <= 0.0f) return 0;
    return (float)(r % 10000u) < chance_pct * 100.0f;
}

static void kldy_forget(void) { memset(&kldy_s, 0, sizeof kldy_s); }

static void kldy_human(DWORD tick)
{
    DWORD pl = 0, D, ds = 0, ho; float feet[3], np[3], hp = 0, mx = 0, cool = 0; BYTE police = 0; int ok = 1;
    (void)tick;
    if (!kldy.human || !kle_human(&pl, feet, np) || !pl) return;
    if (pl != kldy_s.player) { kldy_s.player = pl; kldy_s.in_ep = 0; kldy_s.tries = 0; kldy_s.told_cool = 0; }
    if (!klh_rd(pl + 0x2723, &police, 1) || police) return;
    if (!(D = klh_rd32(pl + 0x2948)) || klh_rd32(D) != pl || !klh_rd(D + 4, &ds, 4)) return;
    if (!(ho = klh_rd32(pl + 0xa48))) return;
    hp = klbd_rdf(ho + 4, &ok); mx = klbd_rdf(ho + 8, &ok);
    if (!ok || mx < 1.0f || hp <= 0.01f) { kldy_s.in_ep = 0; return; }           /* dead or unreadable: nothing to save */
    if (ds != 0) { kldy_s.in_ep = 0; return; }                                    /* already down (his own trigger or ours) */
    if (hp > mx * (kldy.human_pct + 10.0f) / 100.0f) { kldy_s.in_ep = 0; kldy_s.told_cool = 0; return; }   /* healed: a new episode next time */
    if (hp > mx * kldy.human_pct / 100.0f) return;
    if (!kldy_s.in_ep) {                                                          /* a new episode: one draw */
        kldy_s.in_ep = 1; kldy_s.tries = 0; kldy_s.ep++; kldy_s.ep_start = GetTickCount();
        kldy_s.rolled_yes = kldy_draw_yes(kldy.chance, (unsigned)(GetTickCount() * 2654435761u >> 7));
        if (kldy.log) klog("dying: YOU are at %.1f of %.1f (<= %.0f %%): %s", hp, mx, kldy.human_pct,
                           kldy_s.rolled_yes ? "the game's down is asked (trigger 0x8da3b0, kind 9)" : "the draw says NO (Chance): you die as stock");
    }
    if (!kldy_s.rolled_yes) return;
    if ((long)(GetTickCount() - kldy_s.ep_start) > (long)(kldy.secs * 1000.0f)) return;      /* given up for this episode */
    if (GetTickCount() - kldy_s.last_try < 100) return;
    kldy_s.last_try = GetTickCount();
    klh_rd(D + 0x38, &cool, 4);                                                    /* GUESS: a float, seconds until he may go down again */
    if (klbd_fin(cool) && cool > 0.05f) {
        if (!kldy_s.told_cool) { kldy_s.told_cool = 1; klog("dying: you are at %.1f but the down cooldown [D+0x38] is %.1f s: the game would refuse (you can die)", hp, cool); }
        return;
    }
    if (kldy.dry) {
        if (!kldy_s.tries) klog("dying: Dry - you (health %.1f of %.1f) WOULD be floored by the game's trigger 0x8da3b0 (kind 9)", hp, mx);
        kldy_s.tries++; return;
    }
    {
        static BYTE rec[0x200]; BYTE yes; DWORD ds2 = 0;
        memset(rec, 0, sizeof rec); *(DWORD *)(rec + 8) = 9;                       /* GUESS: kind 9 = a blast (klcardown.c's reading); attacker 0 */
        yes = (BYTE)KLCD_HUMAN_CALL(D, rec);
        klh_rd(D + 4, &ds2, 4); kldy_s.tries++;
        if (kldy.log >= 2 || ds2 != 0 || kldy_s.tries == 1) klog("dying: you (health %.1f of %.1f), try %d: the game's trigger said %s, [D+4] %lu -> %lu", hp, mx, kldy_s.tries, yes ? "YES" : "NO", (unsigned long)ds, (unsigned long)ds2);
    }
}

static void kldy_tick(int game_thread)
{
    DWORD rules, state; int level; char why[200]; struct klb_snap sn;
    if (!kldy.on || !game_thread || !klh_exe_ok) return;
    if (!(klr_arcade(&rules, &state, &level) && klb_level(why) && state == KLB_ROUND && klb_read(&sn) && sn.state == KLB_ROUND)) { if (kldy_s.rules) kldy_forget(); return; }
    if (sn.rules != kldy_s.rules) {
        kldy_forget(); kldy_s.rules = sn.rules;
        klog("dying: a round runs (Arcade, not the stock level: %s); you are asked down at %.0f %% health (Human %d, Chance %.0f %%), the heisters' gun is held on the floor (Bots %d)%s",
             why, kldy.human_pct, kldy.human, kldy.chance, kldy.bots, kldy.dry ? " - Dry: nothing is called" : "");
    }
    kldy_human(0);
}

static float kldy_inif(const char *key, const char *def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("Dying", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    if (!(v == v) || v < lo || v > hi) v = (float)atof(def);
    return v;
}

/* after klbd_init and kld_init */
static void kldy_init(void)
{
    memset(&kldy, 0, sizeof kldy); kldy_forget();
    kldy.on = GetPrivateProfileIntA("Dying", "Enable", 1, klh_ini) != 0;
    if (!kldy.on) return;
    kldy.dry = GetPrivateProfileIntA("Dying", "Dry", 0, klh_ini) != 0;
    kldy.log = GetPrivateProfileIntA("Dying", "Log", 1, klh_ini);
    kldy.human = GetPrivateProfileIntA("Dying", "Human", 1, klh_ini) != 0;
    kldy.bots = GetPrivateProfileIntA("Dying", "Bots", 1, klh_ini) != 0;
    kldy.human_pct = kldy_inif("HumanPct", "30", 1.0f, 90.0f);
    kldy.chance = kldy_inif("Chance", "100", 0.0f, 100.0f);
    kldy.secs = kldy_inif("Seconds", "2.5", 0.3f, 10.0f);
    if (kldy.bots && klbd.on && !klbd.dry && !klbd.nofire) {      /* not gated by Dry: Dry covers the human call; this is a data flag of klbotdown.c, read by its own Dry */
        klbd.nofire = 1;
        klog("dying: [BotDown] NoFire forced to 1: a downed heister's target [soldier+0xb0] is cleared while he lies (like a policeman on the floor)");
    } else if (kldy.bots && !klbd.on) klog("dying: Bots=1 but [BotDown] is off: the heisters have no down to hold fire in");
    klog("dying: on%s: you are asked into the game's revivable down at %.0f %% health (one draw of %.0f %% per episode, %.1f s of asking), Human %d Bots %d; head shots still kill",
         kldy.dry ? " (Dry=1: nothing is called, nothing is written)" : "", kldy.human_pct, kldy.chance, kldy.secs, kldy.human, kldy.bots);
}
