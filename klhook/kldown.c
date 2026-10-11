/*
 * kldown.c - THE PLAYER GOES DOWN LIKE THE AI HEISTERS DO, AND MASHES HIS WAY BACK UP ([Down] Enable=1; default OFF).
 * The owner, 2026-10-11: 'i want a down mechanic, as in you know how the ai heisters like flop to the floor being shot
 * by the feds, want the same mechanic on the actual player and they have to spam like theyre breaking out from a human
 * shield to get up so the animation is slow, gets faster whilst you spam the break out button'.
 * Part of KLHook (included by klhook.c after klfed.c, SHIP and TEST alike). DATA WRITES ONLY: no call of a game routine,
 * no patch, no vtable copy. Acts only in an Arcade session on a level that is NOT stock (klbalance.c's own two tests),
 * only for a local player who is not police, writes only from the game's own thread. NOTHING HERE HAS RUN IN THE GAME.
 * The whole reading with the code places: re\player_down.md.
 *
 * WHAT THE GAME ALREADY DOES (kl2.exe build 0490; read in the disassembly, and SEEN in the owner's own rounds of
 * 2026-10-10 19:50 - 20:47: ten times on all five maps, klshoulder.c's log)
 *   The human HAS a down state in Arcade: 'down not dead'. D = [player+0x2948] (made by 0x57cf90, [D] = the player):
 *     [D+4]   0 up, 2 going down (the fall; 0.73 s in the log, input bits 1 and 0x10 masked), 1 lying (he can crawl and
 *             shoot), 3 getting up (0.80 s in the log, every time)
 *     [D+8]   bit 0 = down           [D+0x38] seconds until he can go down again
 *     [D+0xc] M, his ZFFPlayerMovementProne (vtable 0xbb5d64): [M+0x8ec] 1 falling, 2 lying, 4 getting up, 5 done;
 *             [M+0x8d0] the animation channel of the fall / the get-up; [M+0x8d8] tick it began, [M+0x8dc] tick it
 *             is over (0x640c35: state 4 and now >= this -> 5 -> D ends, 0x7107b0), [M+0x8e0] tick from which a push
 *             of the stick ends it early (0x69a440 + 0x8ee550)
 *     [D+0x2b] the GET UP button as the game's own input computed it this frame (ZGameplayInput slot 12, 0x808966:
 *             0x84dda0(player, byte [input+0x2d3]) - the Cover action, C / pad A unless rebound)
 *   HE GOES DOWN at a hit (0x8da3b0, called by the player's damage routine 0x458e7f BEFORE the health changes; the hit
 *   that does it costs nothing) when: he is up, [D+0x38] has run out, his health is at or under [T+0x268] per cent
 *   (T = the tuning object [0x168d7c0]; 40 as built), and the hits of at least [T+0x274] (20) health each that he took
 *   in the last [T+0x26c] seconds (1.0) add up to [T+0x278] x [T+0x274] (6 x 20 = 120) - or to [T+0x27c] x [T+0x274]
 *   (80) with his health under [T+0x280] per cent (20); a blast (hit kind 9) always counts. Going down (0x76a450) gives
 *   him at least [T+0x25c] health (80) and [D+0x38] = [T+0x264] s (10; [T+0x260] = 20 outside Arcade / multiplayer).
 *   HE GETS UP at ONE press of the button while he lies (0x47cd80 -> 0x7180b0 -> 0x478270(M, 4, fast)): the get-up
 *   clip is played at speed 1.0 (2.5 when [D+0x29], the game's own 'fast' flag) - Play's last argument, stored in the
 *   channel as frames a second (0x4da57d: [channel+0x10] = speed x 25; the update 0x50af2c adds dt x that).
 *   AN AI HEISTER goes down another way (0x70e0e0, from his damage routine 0x847968): at the hit that takes his LAST
 *   health, in place of dying, unless the hit is worth 500,000 or more (the 'left behind' kill is 1,000,000), by the
 *   squad's EDownNotDeadModifier, a level-wide pause since the last man went down ([T+0x54] / [T+0x58]) and his own
 *   chance [actor+0x804] per cent.
 *
 * WHAT THIS PART DOES
 *   1. THE MASH. While he gets up ([D+4] == 3, [M+0x8ec] == 4, the channel [M+0x8d0] is one of his sixteen) the
 *      channel's speed is written every frame: Base (slow) + PerPress x the mash meter, at most Top. The meter gains 1
 *      at every press of the game's own GET UP button ([D+0x2b] going 0 -> 1: whatever key or pad button the owner has
 *      bound) and loses Decay a second. The two ticks the game ends the get-up by are moved with it ([M+0x8dc] and
 *      [M+0x8e0] = now + the frames still to play / the speed), so the state ends when the clip does, as in stock.
 *      A get-up the game itself started fast (speed 2.5) is left alone; so is a channel whose clip is not [M+0x8cc].
 *      THE TIME BOUND: no end tick is ever written after 'first frame + the whole clip at Base speed + 0.25 s', so the
 *      state ends even when the clip's frame stands still (stock's own bound is the tick fixed at the clip's start).
 *      WHAT IT COSTS: lying and getting up he takes FULL damage (0x8da4c2: only the fall is free; a blast that floors
 *      him costs health too, 0x458e8f); Base 0.5 doubles the 0.8 s he is exposed - hence DownHealth=200 in the sample.
 *      While he is down the presses do nothing else (0x84dda0 zeroes the Cover byte); the first press AFTER he stands
 *      is an ordinary Cover press.
 *   2. THE TRIGGER. The numbers of the game's own rule, each only when its key is set: HealthPct -> [T+0x268],
 *      Burst -> [T+0x278], MinHit -> [T+0x274], Window -> [T+0x26c], Cooldown -> [T+0x264], DownHealth -> [T+0x25c].
 *      What stood there is kept and put back when the part stops acting (stock level, no Arcade session, a police
 *      player, the tuning object gone). Burst=1 is the nearest the game's rule comes to the AI's ('the hit that would
 *      finish a hurt man floors him'): one hit of MinHit at or under HealthPct.
 *   3. Dry=1: NOTHING is written. Every real fall and get-up is logged, the speed the mash WOULD have set, and - an
 *      ESTIMATE from the steps of his health, one step a frame taken as one hit - where the keys' trigger WOULD have
 *      floored him.
 *   Reset: the record is per player object; a new player object (a new round, a level change, the fed's body), [D+4]
 *   back at 0 or a death drop everything of the mash. Nothing of this part is left in a player object but the speed of
 *   a channel that has ended.
 *
 * NOT DONE HERE, AND WHY (re\player_down.md 4)
 *   - the same trigger as the AI's exactly (down at the killing hit): that needs the player's damage routine, code
 *   - a prompt 'tap to get up faster' while he gets up: the game's own GET UP prompt (user action 0xc / 0xd, offered by
 *     0x5505c0 while [D+0x2c]) shows only while he LIES; text during the get-up is klhud.c's
 *   - a guard that stands over him still kills him (the point-blank step is 100 bullets: re\melee_damage.md);
 *     [Balance] PointBlankToYou is the key for that
 *
 * LOG (prefix 'down:')
 *   down: on; ...                                                      at start
 *   down: <why>: the part acts / does nothing here                     once per round object and verdict
 *   down: the game's rule as found: ...; written: ...                  when the trigger numbers are written / put back
 *   down: YOU ARE DOWN (n) at (x, y, z): health a of b ...             [D+4] 0 -> 2 (or -> 1)
 *   down: lying after t s                                              2 -> 1
 *   down: GETTING UP: clip of n frames at speed s ...                  -> 3 with a channel
 *   down: get-up: frame f of n, speed s, meter m, presses p            Log=2, four times a second
 *   down: UP after t s on the floor, get-up u s (stock 0.80), p presses, mean speed s, health lost in it
 *   down: DEAD WHILE GETTING UP: ...                                   3 -> 0 with no health
 *   down: get-up: the time bound holds the end tick ...                the clip ran behind its slowest pace
 *   down: WOULD ...                                                    Dry=1
 *
 * WIRING (klhook.c; nothing else of the hook changes)
 *   #include "kldown.c"          after  #include "klfed.c"
 *   kld_init();                  in the init list, after  klp_init();
 *   kld_tick(game_thread);       in klh_tick, after  klp_tick(game_thread);
 * KLHook.ini: the [Down] section of the sample.
 */
#ifndef KLDOWN_C
#define KLDOWN_C

#define KLD_GAMEDATA   0x00dd265c             /* +0x828 + 4 * i players, +0x898 the local player's index */
#define KLD_TUNING     0x0168d7c0             /* the tuning object (heap, no vtable) */
#define KLD_CLOCK      0x00dd2640             /* +0x48 the game's tick (1/1024 s), +0x50 the frame's seconds */
#define KLD_PLAYER_VT  0x00bb45f4             /* ZFFPlayer */
#define KLD_PRONE_VT   0x00bb5d64             /* ZFFPlayerMovementProne */
#define KLD_NT         6
#define KLD_ABS(x)     ((x) < 0 ? -(x) : (x))

/* the trigger numbers of the tuning object: offset, the value the tuning constructor stores (0x526cfe .. 0x526f48), limits */
static const struct { const char *key; DWORD off; float built, lo, hi; const char *what; } kld_t[KLD_NT] = {
    { "HealthPct",  0x268, 40.0f, 1.0f, 100.0f,  "health per cent at or under which he can go down" },
    { "Burst",      0x278, 6.0f,  0.5f, 50.0f,   "hits of MinHit the window must hold" },
    { "MinHit",     0x274, 20.0f, 1.0f, 1000.0f, "the least health a hit must cost to count" },
    { "Window",     0x26c, 1.0f,  0.1f, 10.0f,   "seconds a counted hit of an NPC stays in the window" },
    { "Cooldown",   0x264, 10.0f, 0.0f, 600.0f,  "seconds before he can go down again" },
    { "DownHealth", 0x25c, 80.0f, 1.0f, 10000.0f, "the least health he has when he goes down; written as his maximum at most" },
};

static struct {
    int on, dry, log; float base, per, top, decay; float want[KLD_NT]; int anykey;
} kld;

static struct {
    DWORD player, tun; int tunhave, tunput; float tun0[KLD_NT], tunw[KLD_NT];
    /* the fall */
    DWORD dstate, t_down, t_lie, t_up; int downs; BYTE btn;
    /* the get-up */
    DWORD chan, clip; int up, presses; float meter, r0, endf, evf, sumr; int nr; DWORD lastline;
    DWORD cap; int capped; float lastf, hp_up;    /* cap: the tick no end tick is ever written after (review M1) */
    /* Dry: the trigger as an estimate */
    float hp; struct { DWORD until; float d; } win[20]; int nwin; DWORD cool;
} kld_s;

static int kld_fin(float f) { return f == f && f > -1e9f && f < 1e9f; }

static float kld_rdf(DWORD_PTR at, int *ok)
{
    float f = 0;
    if (!klh_rd(at, &f, 4) || !kld_fin(f)) { *ok = 0; return 0; }
    return f;
}

static float kld_inif(const char *key, const char *def)
{
    char t[32];
    GetPrivateProfileStringA("Down", key, def, t, sizeof t, klh_ini);
    return (float)atof(t);
}

/* The trigger numbers: kept as found, written while act, put back when not. Game thread only. */
static void kld_tuning(int act, float max)      /* max: the player's maximum health, 0 = not known this pass */
{
    DWORD tun = klh_rd32((DWORD_PTR)KLH_VA(KLD_TUNING)); float cur[KLD_NT]; int k, ok = 1, n = 0; char a[200], b[200]; int na = 0, nb = 0;
    if (!kld.anykey) return;
    if (!tun) { kld_s.tun = 0; kld_s.tunhave = kld_s.tunput = 0; return; }
    for (k = 0; k < KLD_NT; k++) cur[k] = kld_rdf(tun + kld_t[k].off, &ok);
    if (!ok) return;
    if (tun != kld_s.tun || !kld_s.tunhave) {                       /* another tuning object, or the first look */
        for (k = 0; k < KLD_NT; k++) if (cur[k] < 0 || cur[k] > 100000) return;      /* not the block this build expects: leave it */
        kld_s.tun = tun; kld_s.tunhave = 1; kld_s.tunput = 0;
        memcpy(kld_s.tun0, cur, sizeof cur); memset(kld_s.tunw, 0, sizeof kld_s.tunw);
        a[0] = 0;
        for (k = 0; k < KLD_NT && na < (int)sizeof a - 32; k++) na += snprintf(a + na, sizeof a - na, " %s %.1f%s", kld_t[k].key, cur[k], KLD_ABS(cur[k] - kld_t[k].built) > 0.01f ? " (not the built-in)" : "");
        klog("down: the game's own rule as found in the tuning object %08lx:%s", tun, a);
    } else for (k = 0; k < KLD_NT; k++)                              /* the game (a level's tuning) changed one: that is the new 'found' */
        if (KLD_ABS(cur[k] - kld_s.tun0[k]) > 0.001f && (kld_s.tunw[k] == 0 || KLD_ABS(cur[k] - kld_s.tunw[k]) > 0.001f)) { kld_s.tun0[k] = cur[k]; kld_s.tunw[k] = 0; }
    a[0] = b[0] = 0;
    for (k = 0; k < KLD_NT; k++) {
        float want = act && kld.want[k] >= 0 ? kld.want[k] : kld_s.tun0[k];
        if (act && k == 5 && kld.want[k] >= 0) {                    /* DownHealth: never over his maximum (0x76a75b hands it to 0x61efd0,
                                                                       which was not read for a clamp; klbalance.c sets the maximum) */
            if (max < 1.0f) continue;                               /* maximum not known this pass: what stands there stays */
            if (want > max) want = max;
        }
        if (KLD_ABS(cur[k] - want) <= 0.001f) continue;
        if (kld.dry) { if (nb < (int)sizeof b - 40) nb += snprintf(b + nb, sizeof b - nb, " %s %.1f -> %.1f", kld_t[k].key, cur[k], want); n++; continue; }
        if (!klh_data((void *)(DWORD_PTR)(tun + kld_t[k].off), &want, 4, "tuning: a number of the down-not-dead rule")) continue;
        kld_s.tunw[k] = KLD_ABS(want - kld_s.tun0[k]) > 0.001f ? want : 0;
        if (nb < (int)sizeof b - 40) nb += snprintf(b + nb, sizeof b - nb, " %s %.1f -> %.1f", kld_t[k].key, cur[k], want);
        n++;
    }
    if (n && kld.dry) { if (!kld_s.tunput && act) { kld_s.tunput = 1; klog("down: WOULD write the trigger (Dry=1: nothing is written):%s", b); } }
    else if (n) { kld_s.tunput = act; klog("down: the trigger %s (%d number(s)):%s", act ? "is written" : "is back as the game had it", n, b); }
}

/* Dry=1: where the keys' rule would have floored him, from the steps of his health (one step a frame = one hit). */
static void kld_estimate(float hp, float max, DWORD now, int up)
{
    float w[KLD_NT], d, sum = 0; int k, i, j;
    for (k = 0; k < KLD_NT; k++) w[k] = kld.want[k] >= 0 ? kld.want[k] : kld_s.tunhave ? kld_s.tun0[k] : kld_t[k].built;
    d = kld_s.hp - hp;
    for (i = j = 0; i < kld_s.nwin; i++) if ((int)(kld_s.win[i].until - now) > 0) kld_s.win[j++] = kld_s.win[i];
    kld_s.nwin = j;
    if (up && kld_s.hp > 0 && d >= w[2] && max >= 1) {
        float pct = kld_s.hp / max * 100.0f;                        /* the game tests his health BEFORE the hit */
        if (kld_s.nwin < 20) { kld_s.win[kld_s.nwin].until = now + (DWORD)(w[3] * 1000.0f); kld_s.win[kld_s.nwin].d = d; kld_s.nwin++; }
        for (i = 0; i < kld_s.nwin; i++) sum += kld_s.win[i].d;
        if ((int)(kld_s.cool - now) <= 0 && pct <= w[0] && sum >= w[1] * w[2]) {
            kld_s.cool = now + (DWORD)(w[4] * 1000.0f); kld_s.nwin = 0;
            klog("down: WOULD go down here by the keys (an ESTIMATE from his health, Dry=1): %.1f of %.1f (%.0f %%, limit %.0f) before a hit of %.1f, %.1f in the last %.1f s (needs %.1f); the game's own rule decides for itself",
                 kld_s.hp, max, pct, w[0], d, sum, w[3], w[1] * w[2]);
        }
    }
    kld_s.hp = hp;
}

static void kld_drop(void)
{
    kld_s.up = 0; kld_s.chan = kld_s.clip = 0; kld_s.meter = 0; kld_s.presses = 0; kld_s.sumr = 0; kld_s.nr = 0;
    kld_s.cap = 0; kld_s.capped = 0; kld_s.lastf = 0; kld_s.hp_up = 0;
}

static void kld_tick(int game_thread)
{
    static DWORD toldrules; static char toldwhy[200];
    DWORD gd, pl, d, m, h, rules, state, now, tick = 0, clock, chans; int level, act, ok = 1, i;
    BYTE idx = 0xff, police = 0, flag = 0, btn = 0; DWORD ds = 0, ms = 0; float hp = 0, max = 0, pos[3] = { 0, 0, 0 }, dt = 0; char why[200];
    if (!kld.on || !klh_exe_ok) return;
    if (!game_thread) return;                  /* every write here is a live object of the round: only between two frames of the game.
                                                  The mash is counted by frames too: nothing of this part runs on the fallback thread */
    now = GetTickCount();
    act = klr_arcade(&rules, &state, &level);
    if (act) {
        act = klb_level(why);                  /* asked every pass: the verdict changes when the archive is opened */
        if (rules != toldrules || strcmp(why, toldwhy)) {
            toldrules = rules; strcpy(toldwhy, why);
            klog("down: %s: %s", why, act ? kld.dry ? "Dry=1 - the part only logs this round" : "the part acts on this round" : "nothing is written here (the part acts only on a level that is not stock)");
        }
    }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLD_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || (signed char)idx < 0 || idx > 31 ||
        !(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_rd32(pl) != KLD_PLAYER_VT || !klh_rd(pl + 0x2723, &police, 1)) pl = 0;
    if (!pl || police) act = 0;                /* a fed is left to the game */
    if (pl && (h = klh_rd32(pl + 0xa48)) != 0) { hp = kld_rdf(h + 4, &ok); max = kld_rdf(h + 8, &ok); } else ok = 0;
    kld_tuning(act, ok ? max : 0.0f);
    if (!act || !pl) { if (kld_s.player) { kld_s.player = 0; kld_drop(); kld_s.dstate = 0; kld_s.nwin = 0; } return; }
    if (!(d = klh_rd32(pl + 0x2948)) || klh_rd32(d) != pl || !klh_rd(d + 4, &ds, 4) || !klh_rd(d + 8, &flag, 1) || !klh_rd(d + 0x2b, &btn, 1)) return;
    if (pl != kld_s.player) {                  /* a new round, another level, another body: nothing is carried over */
        if (kld_s.player && kld_s.up) klog("down: the player object changed %.2f s into a get-up this part drove (a death, a new round, another body): not an UP", (now - kld_s.t_up) / 1000.0f);
        kld_s.player = pl; kld_drop(); kld_s.dstate = ds; kld_s.btn = btn; kld_s.hp = hp; kld_s.nwin = 0; kld_s.cool = 0; kld_s.downs = 0;
        kld_s.t_down = kld_s.t_lie = kld_s.t_up = now;
    }
    if (kld.dry && ok) kld_estimate(hp, max, now, ds == 0);
    if (ds != kld_s.dstate) {
        if (kld_s.dstate == 0) {
            kld_s.t_down = kld_s.t_lie = now; kld_s.downs++; kld_drop();
            klh_rd(pl + 0x460, pos, 12);                             /* his feet (kljoin.c) */
            klog("down: YOU ARE DOWN (%d this round object) at (%.0f, %.0f, %.0f): health %.1f of %.1f, down state %lu; the button is %s",
                 kld_s.downs, pos[0], pos[1], pos[2], hp, max, ds, btn ? "held" : "up");
        } else if (ds == 1 && kld_s.dstate == 2) { kld_s.t_lie = now; if (kld.log) klog("down: lying after %.2f s (he can crawl and shoot; one press of the game's GET UP button starts the get-up)", (now - kld_s.t_down) / 1000.0f); }
        else if (ds == 3) kld_s.t_up = now;
        else if (ds == 0) {
            if (kld_s.up && (!ok || hp <= 0.01f))                    /* a death clears D too (0x88a990): that is not an 'UP' (review S4) */
                klog("down: DEAD WHILE GETTING UP: %.2f s on the floor, %.2f s into the get-up (frame %.1f of %.1f), %d press(es), mean speed %.2f; he had %.1f health when the get-up began",
                     (now - kld_s.t_down) / 1000.0f, (now - kld_s.t_up) / 1000.0f, kld_s.lastf, kld_s.endf, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, kld_s.hp_up);
            else if (kld_s.up) klog("down: UP after %.2f s on the floor, the get-up took %.2f s (stock: 0.80; from [D+4] = 3, a press late in the fall counts the rest of the fall in), %d press(es) in it, mean speed %.2f, %.1f health lost in it (%.1f -> %.1f)%s%s",
                               (now - kld_s.t_down) / 1000.0f, (now - kld_s.t_up) / 1000.0f, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, kld_s.hp_up - hp, kld_s.hp_up, hp,
                               kld_s.capped ? "; ENDED BY THE TIME BOUND, not by the clip (its frame stood still or ran behind: say so to the lead)" : "", kld.dry ? " (Dry=1: the game's own 1.00 was played)" : "");
            else klog("down: the down state is over after %.2f s (from state %lu) without a get-up this part drove: %s", (now - kld_s.t_down) / 1000.0f, kld_s.dstate,
                      hp <= 0.01f ? "he is dead" : kld_s.dstate == 3 ? "the game's own get-up (into a cover, or its fast one)" : "ended by the game (a reset, a death, a vehicle)");
            kld_drop();
        }
        kld_s.dstate = ds;
    }
    if (btn && !kld_s.btn && kld_s.up) { kld_s.meter += 1.0f; kld_s.presses++; }
    kld_s.btn = btn;
    if (ds != 3) { if (kld_s.up) kld_drop(); return; }

    /* he gets up: the channel of the clip */
    if (!(m = klh_rd32(d + 0xc)) || klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != pl || !klh_rd(m + 0x8ec, &ms, 4) || ms != 4) return;
    if (!(h = klh_rd32(m + 0x8d0)) || !(chans = klh_rd32(pl + 0x70))) return;
    for (i = 0; i < 16; i++) if (h == chans + 0x1c + 0x38 * i) break;
    if (i == 16) return;                       /* not one of his sixteen channels: not the layout this was read on */
    if (!(clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    dt = kld_rdf(clock + 0x50, &ok);
    {
        DWORD clip = klh_rd32(h), fl = klh_rd32(h + 0x14); DWORD t0 = klh_rd32(m + 0x8d8), te = klh_rd32(m + 0x8dc), tv = klh_rd32(m + 0x8e0);
        float frame = kld_rdf(h + 4, &ok), to = kld_rdf(h + 0xc, &ok), fps = kld_rdf(h + 0x10, &ok), rate, left; long ne, nv;
        if (!ok || !clip || (fl & 7) == 4 || (fl & 7) == 0 || to < 2 || to > 5000 || frame < 0 || frame > to + 1 || fps < 0.5f || fps > 250 || dt < 0 || dt > 0.5f) return;
        if (!kld_s.up || h != kld_s.chan || clip != kld_s.clip) {    /* the first frame of this get-up: what the game set */
            float r0 = fps / 25.0f, endf, evf;
            if (kld_s.up) return;                                    /* another clip on the channel while state 3 lasts: not ours any more */
            if (clip != klh_rd32(m + 0x8cc)) {                       /* [M+0x8cc] = the clip 0x478270 handed to Play (0x4782a8); a channel that was
                                                                        stopped is reused and [M+0x8d0] is not cleared: not M's clip -> not ours (review S1) */
                if (kld_s.lastline != t0) { kld_s.lastline = t0; klog("down: GETTING UP, but the channel plays clip %08lx and the prone movement's clip is %08lx: left alone", clip, klh_rd32(m + 0x8cc)); }
                return;
            }
            endf =(float)(long)(te - t0) * 25.0f * r0 / 1024.0f;    /* 0x478346 .. 0x478368: te = t0 + frames / 25 / speed x 1024 */
            evf = (float)(long)(tv - t0) * 25.0f * r0 / 1024.0f;
            if (KLD_ABS(r0 - 1.0f) > 0.02f) {                        /* 2.5 = the game's own fast get-up ([D+0x29]): its business */
                if (kld_s.lastline != t0) { kld_s.lastline = t0; klog("down: GETTING UP at the game's own speed %.2f (not 1.00: its fast get-up): left alone", r0); }
                return;
            }
            if (endf < 2 || endf > to + 2 || (long)(te - t0) <= 0) {
                if (kld_s.lastline != t0) { kld_s.lastline = t0; klog("down: GETTING UP, but the end tick does not fit the clip (end frame %.1f of %.0f, ticks %ld): left alone", endf, to, (long)(te - t0)); }
                return;
            }
            if (evf < 0 || evf > endf) evf = endf;                   /* no such event in the clip: the game copies the end tick */
            kld_s.up = 1; kld_s.chan = h; kld_s.clip = clip; kld_s.r0 = r0; kld_s.endf = endf; kld_s.evf = evf;
            kld_s.meter = 0; kld_s.presses = 0; kld_s.sumr = 0; kld_s.nr = 0; kld_s.lastline = now;
            /* THE TIME BOUND (review M1). Stock fixes the end tick when the clip starts; this part moves it with the clip's
               frame, and a frame that stands still (the player's animation update skipped: 0x74efc0's three gates; channel
               flag 0x100000: 0x50af15) would move it ahead for ever. So: the whole clip at Base speed from now + 0.25 s is
               the latest end this part ever writes - the slowest get-up is the Base one, and the state always ends. */
            kld_s.cap = tick + (DWORD)(endf / (kld.base * 25.0f) * 1024.0f + 0.5f) + 256;
            kld_s.capped = 0; kld_s.lastf = frame; kld_s.hp_up = hp;
            klog("down: GETTING UP after %.2f s on the floor: channel %d, clip %08lx of %.0f frames, the game's speed %.2f, over at frame %.1f, the stick may end it from frame %.1f; %s Base %.2f + %.2f a press (meter - %.1f a second), at most %.2f; over in %.2f s at the latest; health %.1f of %.1f",
                 (now - kld_s.t_down) / 1000.0f, i, clip, to, r0, endf, evf, kld.dry ? "Dry=1, it WOULD be played at" : "it is played at", kld.base, kld.per, kld.decay, kld.top,
                 (float)(long)(kld_s.cap - tick) / 1024.0f, hp, max);
        }
        kld_s.lastf = frame;
        kld_s.meter -= kld.decay * dt; if (kld_s.meter < 0) kld_s.meter = 0;
        rate = kld.base + kld.per * kld_s.meter; if (rate > kld.top) rate = kld.top; if (rate < 0.05f) rate = 0.05f;
        kld_s.sumr += rate; kld_s.nr++;
        if (kld.log >= 2 && now - kld_s.lastline >= 250) { kld_s.lastline = now; klog("down: get-up: frame %.1f of %.1f, speed %.2f, meter %.2f, %d press(es)", frame, kld_s.endf, rate, kld_s.meter, kld_s.presses); }
        if (kld.dry) return;
        /* the three writes: the channel's frames a second, and the two ticks the game ends the state by */
        fps = rate * 25.0f;
        if (!klh_data((void *)(DWORD_PTR)(h + 0x10), &fps, 4, "the get-up clip's channel: frames a second")) return;
        left = kld_s.endf - frame; if (left < 0) left = 0;
        ne = (long)tick + (long)(left / fps * 1024.0f + 0.5f);
        if ((long)((DWORD)ne - kld_s.cap) > 0) {                     /* never after the bound: the game then ends the state at the cap */
            ne = (long)kld_s.cap;
            if (left > 1.5f && !kld_s.capped) { kld_s.capped = 1; klog("down: get-up: the time bound holds the end tick (frame %.1f of %.1f, %.2f s left to the bound): the clip is behind its slowest pace", frame, kld_s.endf, (float)(long)(kld_s.cap - tick) / 1024.0f); }
        }
        klh_data((void *)(DWORD_PTR)(m + 0x8dc), &ne, 4, "the prone movement: the tick the get-up is over");
        if (frame < kld_s.evf) nv = (long)tick + (long)((kld_s.evf - frame) / fps * 1024.0f + 0.5f); else nv = (long)tick < ne ? (long)tick : ne;
        if (nv > ne) nv = ne;                                        /* 0x69a4c3: the game's other branch (start + 0.7 x length) is for an event AFTER the end */
        klh_data((void *)(DWORD_PTR)(m + 0x8e0), &nv, 4, "the prone movement: the tick from which the stick ends the get-up");
    }
}

static void kld_init(void)
{
    int k; float v; char t[220]; int n = 0;
    memset(&kld_s, 0, sizeof kld_s);
    kld.on = GetPrivateProfileIntA("Down", "Enable", 0, klh_ini) != 0;
    kld.dry = GetPrivateProfileIntA("Down", "Dry", 0, klh_ini) != 0;
    kld.log = GetPrivateProfileIntA("Down", "Log", 1, klh_ini);
    kld.base = kld_inif("Base", "0.5"); kld.per = kld_inif("PerPress", "0.3"); kld.top = kld_inif("Top", "2.0"); kld.decay = kld_inif("Decay", "2.0");
    if (!kld_fin(kld.base) || kld.base < 0.1f || kld.base > 3.0f) kld.base = 0.5f;      /* under 0.1 a get-up would take over 8 s: a stuck player to anybody watching */
    if (!kld_fin(kld.top) || kld.top < kld.base || kld.top > 4.0f) kld.top = kld.base > 2.0f ? kld.base : 2.0f;
    if (!kld_fin(kld.per) || kld.per < 0 || kld.per > 4.0f) kld.per = 0.3f;
    if (!kld_fin(kld.decay) || kld.decay < 0 || kld.decay > 50.0f) kld.decay = 2.0f;
    t[0] = 0;
    for (k = 0; k < KLD_NT; k++) {
        kld.want[k] = -1.0f;
        v = kld_inif(kld_t[k].key, "-1");
        if (kld_fin(v) && v >= kld_t[k].lo && v <= kld_t[k].hi) { kld.want[k] = v; kld.anykey = 1; if (n < (int)sizeof t - 32) n += snprintf(t + n, sizeof t - n, " %s=%.1f", kld_t[k].key, v); }
        else if (kld_fin(v) && v >= 0 && kld.on) klog("down: %s=%.2f is outside %.1f .. %.1f (%s): the game's own number stays", kld_t[k].key, v, kld_t[k].lo, kld_t[k].hi, kld_t[k].what);
    }
    if (kld.on) klog("down: on%s; the get-up is played at Base %.2f + PerPress %.2f x the mash meter (one a press of the game's own GET UP button, - Decay %.1f a second), at most Top %.2f; the trigger:%s; Log=%d. Arcade on a level that is not stock, not for a police player; data writes only (re\\player_down.md)",
                     kld.dry ? " (Dry=1: NOTHING is written, the log says what would be)" : "", kld.base, kld.per, kld.decay, kld.top, n ? t : " the game's own (no key set)", kld.log);
}

#endif /* KLDOWN_C */
