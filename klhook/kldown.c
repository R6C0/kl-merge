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
 * THE BELLY FLOP ([Down] Flop=1; default 0 = everything above and nothing of this; track R2, re\player_down.md 9)
 *   The owner on what is above: 'when i go down it does that gun one, i mean the other one where its like a full belly
 *   flop dive on the floor'. READ: 'the gun one' is the game's own fall, the slot /Damage/Down_Not_Dead/
 *   Down_Not_Dead_Get_Down (48 frames, the root goes 23 BACK: onto his back, gun up) - and an NPC's own down-not-dead
 *   (ZDownNotDeadNPC, 0x5f4ac0) plays the SAME clip data (the _RUN / _Walk slots are aliases of it in every stock file).
 *   What the AI heisters do when the police shoot them is their DEATH: in 235 of 235 'health 0' lines of the live logs
 *   the bot is dead in the next status line, none comes back; ZFFActor's death (0x72ab60) plays /Damage/Death/
 *   Die_Forward when the shot came from behind (50 frames, 2.0 s, the root goes 88 FORWARD: the dive on the belly),
 *   Die_Backwards from the front, Die_On_Spot without room. So 'like the bots' = that clip, on a man who lives.
 *   HOW, BY DATA ONLY. The prone movement M picks its two clips by SLOT ID from six words of its own, read by one
 *   routine (0x5d6060): the fall [M+0x8b0 + 2v], the get-up [M+0x898 + 2v], v = [M+0x8f0] (0 plain, 1 compact, 2 on the
 *   spot), filled once by its slot 20 (0x750900). While the player is UP this part writes the id of FlopFallSlot
 *   (/Damage/Death/Die_Forward) into the three fall words and the id of FlopUpSlot (/Movement/Rise/Rise_From_Stomach:
 *   202 frames, on the spot until frame 153, then 1.26 m forward on his feet) into the three get-up words - after it
 *   has found both names in the level's slot table and a full-body clip for each in THIS body's set (the game's own
 *   lookup 0x5c2f60 done by reads: [player+0x78] / [+0x7c], records at [[0x1546f6c]]). The game then plays them itself:
 *   trigger, health, camera, input mask, the end of the state are its own, untouched.
 *   During the dive (D state 2, M state 1) the 'event 2' tick [M+0x8e0] is held at the end tick [M+0x8dc]: stock would
 *   let a press cut the fall from half way (0x843fa0 -> 0x47cd80 -> 0x8b1900 stops the channel) - and until that tick
 *   the game's own trigger swallows every hit (0x8da4e0), so THE WHOLE DIVE COSTS NOTHING (stock: the first 0.72 s).
 *   No lying on the back in between: within two frames of the dive's end the part sets the game's own 'get-up asked'
 *   byte [D+0x21] (what a press sets, 0x7180b0) - the game stops the dive's channel and starts the get-up clip in that
 *   frame. The get-up is the mash of above with its own numbers: FlopBase / FlopPerPress / FlopTop.
 *   WHAT A BOT'S OWN RULE GIVES, AND THE KEYS FOR IT: an NPC that goes 'down not dead' is given 25 % of his health
 *   when he falls (0x7eaac0) and 75 % when he is up (0x5f4d2c). FlopUpPct = the second for the human (his health is
 *   raised to that share of his maximum when he stands; default 0 = not). FlopTake = the share of every loss DURING THE
 *   GET-UP that stays (1 = the game's; 0.25 = three quarters given back the next frame) - it cannot save him from a
 *   hit that takes all he has at once.
 *   SECOND REVIEW (re\player_down_review2.md, applied): a man who is dead OR out of play (crew status not 0 - with
 *   [Fed] Player=1 a dead human has status 1 for 5 s, not 7) is written nothing, for the rest of that down; the request
 *   while he lies only with M at 2; the get-up's numbers / FlopTake / FlopUpPct go by the get-up's CLIP; the six words
 *   are written only where they hold the game's own six names' ids (or none); a clip with an event the game's clip-event
 *   routine acts on (other than the stock fall's 2, 5, 6) is refused; the check is made again after a body swap; a
 *   request the game never took is taken back when D ends. KNOWN: beside a cover the game takes the request as 'get up
 *   into the cover' (0x47ce07): the down ends at the dive's end with no get-up clip and no mash - and the dive goes 88
 *   forward, at whatever he faced. FlopUpPct=75 makes the knock-down a HEAL (down at 40 % or less, up at 75 %): the
 *   owner's decision, not a default.
 *   NOT ESTABLISHED: how the two clips LOOK on the player (nothing here was run), whether Get_Up_From_Stomach starts in
 *   the pose Die_Forward ends in (two different sources: a death and the 'heal wounded' move), what a fall the game
 *   aligned to a place ([D+0xf4], made for a fall BACKWARD) does with a dive FORWARD (logged), what he does at a wall
 *   (the collision is on: he slides on the spot).
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
 *   down: DEAD / OUT OF PLAY WHILE FALLING / LYING / GETTING UP: ...   health 0 or crew status not 0 while D is not 0; once
 *   down: get-up: the time bound holds the end tick ...                the clip ran behind its slowest pace
 *   down: WOULD ...                                                    Dry=1
 *   down: flop: <slot> = id n, clip ... / no flop on this body: <why>  Flop=1, once per player object
 *   down: flop: the prone movement ... holds fall a/b/c get-up d/e/f: written n/n/n and m/m/m
 *   down: flop: THE BELLY FLOP: clip ... of n frames ...               the fall that plays is the flop's
 *   down: flop: the dive is over: the get-up is asked for              [D+0x21] written
 *   down: flop: up with x health (FlopUpPct) / given back ...          at the end
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
#define KLD_ANIM       0x01546f6c             /* the animation manager: [+0] the clip records (0x68 bytes each), [+4] their number (0x48bc90) */
#define KLD_MOVES      0x630                  /* [player + 0x630 + 4 n] = his movement number n (0x462420); the current one is at +0x6b4 */
#define KLD_M_FALL     0x8b0                  /* M: three slot ids of the fall (plain, compact, on the spot), 0x5d60a6 */
#define KLD_M_UP       0x898                  /* M: three slot ids of the get-up, 0x5d6072 */
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
    int flop; float fbase, fper, ftop, take, uppct; char fallslot[96], upslot[96];      /* the belly flop (Flop=1) */
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
    /* the belly flop. Per player object: fchk .. fput; per fall: fseen .. fgiven (kld_drop) */
    int fchk, fok, idf, idu, fhave, fput; DWORD fm; WORD forig[6];
    WORD fst[6];                               /* the ids of the game's own six names in this level's slot table (0xffff = no such name) */
    DWORD fset[3];                           /* [player+0x78], [+0x7c], [+0x80] the check was made on (review2 S3: a body swap keeps the object) */
    int fseen, fnow, fasked, fup; DWORD t_ask; float fhp, fgiven;
    int dead;                                  /* he died / left play while down: said once, and nothing is written until D is 0 again (kld_drop) */
} kld_s;

/* the names the game's filler 0x750900 looks up for the six words (0x752e5b .. 0x752f0b), in the order fall x 3, get-up x 3 */
static const char *const kld_stock[6] = {
    "/Damage/Down_Not_Dead/Down_Not_Dead_Get_Down", "/Damage/Down_Not_Dead/Compact_Down_Not_Dead_Get_Down", "/Damage/Down_Not_Dead/On_Spot_Down_Not_Dead_Get_Down",
    "/Damage/Down_Not_Dead/Down_Not_Dead_Get_Up",   "/Damage/Down_Not_Dead/Compact_Down_Not_Dead_Get_Up",   "/Damage/Down_Not_Dead/On_Spot_Down_Not_Dead_Get_Up",
};

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
    kld_s.fseen = kld_s.fnow = kld_s.fasked = kld_s.fup = 0; kld_s.t_ask = 0; kld_s.fhp = 0; kld_s.fgiven = 0; kld_s.dead = 0;
}

/* Is the local player dead or out of play? His health at 0 - or his crew record's status is anything but 0 = in play
   (klbot.c's reading of the round, reads only): in run D1 the last health seen was 0.4 and the game then made the
   health object new ('the game gave 550') while D kept its state, so the health alone does not say it. The statuses
   SEEN: 7 dead (D1 / D2), 1 dead and waiting to come back as police ([Fed] Player=1: run PT_DM03_die_r2 - the 5 s
   before the police body; review2 M1), 4 aboard, 6 escaped. -> 0 in play, 1 dead, 2 out of play another way; *st */
static int kld_dead(int hpok, float hp, int *st)
{
    struct klb_snap sn;
    *st = -1;
    if (klb_read(&sn) && sn.human >= 0) *st = sn.r[sn.human].status;
    if ((hpok && hp <= 0.01f) || *st == 7 || *st == 1) return 1;
    return *st > 0 ? 2 : 0;
}

/* ---- the belly flop (Flop=1) ---------------------------------------------------------------------------------- */

/* His prone movement: the one of his movements ([player + 0x630 + 4 n], 0x462420) that is a ZFFPlayerMovementProne of
   his. [D+0xc] names it only once he has been down (0x57cfb2 makes D with 0 there). Reads only. -> 0 = none */
static DWORD kld_prone(DWORD pl)
{
    DWORD m; int n;
    for (n = 0; n < 33; n++)
        if ((m = klh_rd32(pl + KLD_MOVES + 4 * n)) != 0 && klh_rd32(m) == KLD_PRONE_VT && klh_rd32(m + 0x8d4) == pl) return m;
    return 0;
}

/* The clips this body's set holds for a slot id: the game's own lookup (0x59d550 -> 0x5c2f60 -> 0x876940, 0x7c6750,
   0x48bc90) done by reads - the table [player+0x7c] = {S, S x offset or -1}, the list at [player+0x78] + offset =
   {condition flags, clip number} pairs up to the pair with flags 0 (the default), the record = [[0x1546f6c]] + number
   x 0x68 when number < [[0x1546f6c] + 4]. The game picks one of them by his weapon condition and a random number; this
   only lists them. -> their number (at most cap), 0 = the set has no list for the slot, -1 = not readable */
static int kld_list(DWORD pl, int id, DWORD *clips, int cap)
{
    DWORD pool = klh_rd32(pl + 0x78), tab = klh_rd32(pl + 0x7c), n = 0, off = 0xffffffff, mgr, recs, cnt = 0, pr[2]; int k = 0, i;
    if (id < 0 || !pool || !tab || !klh_rd(tab, &n, 4) || n > 60000 || (DWORD)id >= n || !klh_rd(tab + 4 + 4 * (DWORD)id, &off, 4)) return -1;
    if (off == 0xffffffff) return 0;
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLD_ANIM))) || !(recs = klh_rd32(mgr)) || !klh_rd(mgr + 4, &cnt, 4)) return -1;
    for (i = 0; i < 16; i++) {
        if (!klh_rd(pool + off + 8 * i, pr, 8)) return -1;
        if (pr[1] < cnt && k < cap) clips[k++] = recs + pr[1] * 0x68;
        if (!pr[0]) return k;
    }
    return -1;                                 /* no default pair within 16: not the shape this was read on */
}

/* A clip record: frames (+2), events (+6), flags (+8), 'full-body' = byte +0x28 bit 0x10 clear (what Play turns into
   the channel flag 0x8000), its name (+0x64, set by the loader). Reads only. -> 0 = not readable / not a clip */
static int kld_clipfacts(DWORD clip, int *frames, int *events, DWORD *flags, int *full, char *name, int cap)
{
    BYTE r[0x68];
    name[0] = 0; *frames = *events = 0; *flags = 0; *full = 0;
    if (!clip || !klh_rd(clip, r, sizeof r)) return 0;
    *frames = *(short *)(r + 2); *events = *(short *)(r + 6); *flags = *(DWORD *)(r + 8); *full = !(r[0x28] & 0x10);
    if (*(DWORD *)(r + 0x64)) klh_rdstr(*(DWORD *)(r + 0x64), name, cap);
    return *frames >= 2 && *frames <= 5000 && *events >= 0 && *events < 64;
}

static int kld_inlist(DWORD pl, int id, DWORD clip)
{
    DWORD c[8]; int n = kld_list(pl, id, c, 8), i;
    for (i = 0; i < n; i++) if (c[i] == clip) return 1;
    return 0;
}

/* The first event of a clip that the game's clip-event routine 0x637060 would ACT on (klclimb.c's klq_ev_acts: the
   game's own switch tables, by reads) and that the stock fall does not carry itself (it has 5, 6 and 2: file). The
   event table as klclimb.c's klq_clip reads it: record +6 the number, +0x10 the offset into the block [[0x1546f6c]
   + 0x10], 8 bytes an event = {id, frame}. Review2 S2: FlopFallSlot / FlopUpSlot are free text, and an event on a
   clip its action was not made for is what faulted the first climb (re\climb_crash.md).
   -> 0 none, 1 = there is one (*id, *fr), -1 = the events cannot be read (such a clip is not used) */
static int kld_badevent(DWORD clip, DWORD *id, int *fr)
{
    BYTE r[0x30], ev[8]; DWORD mgr, base; short n, i;
    *id = 0; *fr = -1;
    if (!clip || !klh_rd(clip, r, sizeof r)) return -1;
    n = *(short *)(r + 6);
    if (n < 0 || n >= 64) return -1;
    if (!n) return 0;
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLD_ANIM))) || !(base = klh_rd32(mgr + 0x10))) return -1;
    for (i = 0; i < n; i++) {
        DWORD e;
        if (!klh_rd(base + *(DWORD *)(r + 0x10) + 8 * i, ev, 8)) return -1;
        e = *(DWORD *)ev;
        if (e == 2 || e == 5 || e == 6) continue;
        if (!klq_ev_to(e)) return -1;                                /* the game's tables cannot be read */
        if (klq_ev_acts(e)) { *id = e; *fr = *(WORD *)(ev + 4); return 1; }
    }
    return 0;
}

/* Once per player object: are both slots there for THIS body, and of the kind the prone movement plays? */
static void kld_flop_check(DWORD pl)
{
    const char *nm[2]; int id[2], k, n, i, be, bf; DWORD c[8], bid; char why[240], name[96]; int fr, ev, full; DWORD fl;
    nm[0] = kld.fallslot; nm[1] = kld.upslot;
    kld_s.fchk = 1; kld_s.fok = 0; kld_s.idf = kld_s.idu = -1; why[0] = 0;
    kld_s.fset[0] = klh_rd32(pl + 0x78); kld_s.fset[1] = klh_rd32(pl + 0x7c); kld_s.fset[2] = klh_rd32(pl + 0x80);
    for (k = 0; k < 6; k++) kld_s.fst[k] = (WORD)klq_slot(pl, kld_stock[k]);      /* -1 = no such name -> 0xffff, as the filler stores it */
    for (k = 0; k < 2 && !why[0]; k++) {
        id[k] = klq_slot(pl, nm[k]);                                 /* klclimb.c: the game's own binary search over [player+0x80], by reads */
        if (id[k] < 0 || id[k] > 0x7fff) { snprintf(why, sizeof why, "the level's slot table has no name %s", nm[k]); break; }
        n = kld_list(pl, id[k], c, 8);
        if (n <= 0) { snprintf(why, sizeof why, n ? "the set of this body cannot be read for %s (slot %d)" : "the set of this body has no clip for %s (slot %d)", nm[k], id[k]); break; }
        for (i = 0; i < n; i++) {
            if (!kld_clipfacts(c[i], &fr, &ev, &fl, &full, name, sizeof name)) { snprintf(why, sizeof why, "clip %08lx of %s cannot be read", c[i], nm[k]); break; }
            if (!full) { snprintf(why, sizeof why, "clip %08lx '%s' of %s is not a full-body clip (record +0x28 has bit 0x10): the prone movement plays full-body clips", c[i], name, nm[k]); break; }
            if ((be = kld_badevent(c[i], &bid, &bf)) != 0) {
                if (be > 0) snprintf(why, sizeof why, "clip %08lx '%s' of %s has event id %lu at frame %d, which the game's clip-event routine 0x637060 acts on and the stock fall does not carry (it has 2, 5, 6)", c[i], name, nm[k], bid, bf);
                else snprintf(why, sizeof why, "the %d event(s) of clip %08lx '%s' of %s cannot be read", ev, c[i], name, nm[k]);
                break;
            }
            klog("down: flop: %s %s = slot %d, clip %d of %d: %08lx '%s', %d frames (%.2f s at speed 1), %d event(s), record flags %lx",
                 k ? "the get-up" : "the fall", nm[k], id[k], i + 1, n, c[i], name, fr, (fr - 1) / 25.0f, ev, fl);
        }
    }
    if (why[0]) { klog("down: flop: NO BELLY FLOP on this body (player %08lx): %s. The game's own fall stays, the get-up is the mash of Base / PerPress / Top", pl, why); return; }
    kld_s.idf = id[0]; kld_s.idu = id[1]; kld_s.fok = 1;
}

/* The six id words of M: kept as found, ours written while he is UP (the fall reads them when it starts, the get-up
   when it starts: 0x5d6060 - never between). act = 0: what was found goes back. Game thread only. */
static void kld_flop_words(DWORD pl, DWORD ds, int act)
{
    DWORD m; WORD w[6], want; int k, n = 0, ok = 1;
    if (!act) {
        if (!kld_s.fhave || !kld_s.fput) return;
        m = kld_s.fm;
        if (klh_rd32(pl) != KLD_PLAYER_VT || klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != pl) { kld_s.fhave = kld_s.fput = 0; return; }      /* the object is gone: nothing of ours is anywhere */
        for (k = 0; k < 6; k++) {
            DWORD at = m + (k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3));
            want = (WORD)(k < 3 ? kld_s.idf : kld_s.idu);
            if (klh_rd(at, &w[k], 2) && w[k] == want && want != kld_s.forig[k] && klh_data((void *)(DWORD_PTR)at, &kld_s.forig[k], 2, "the prone movement: a clip slot id, back as the game had it")) n++;
        }
        kld_s.fput = 0;
        if (n) klog("down: flop: the prone movement %08lx has its own %d slot id(s) again (fall %u/%u/%u, get-up %u/%u/%u)", m, n,
                    kld_s.forig[0], kld_s.forig[1], kld_s.forig[2], kld_s.forig[3], kld_s.forig[4], kld_s.forig[5]);
        return;
    }
    if (!kld_s.fok || ds != 0) return;
    if (!(m = kld_prone(pl))) return;                                /* made with the player (0x5bd530): expected at once; no line a frame */
    for (k = 0; k < 6; k++) ok &= klh_rd(m + (k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3)), &w[k], 2);
    if (!ok) return;
    /* Review2 S1: before a word is written, what stands there must be what the game's filler puts there - the id of its
       own name in the level's slot table (klq_slot: the same table 0x770ba0 is ASSUMED to search), or 0xffff = none -
       or ours. Anything else: these are not the six words on this build / level / body, and nothing is written. */
    for (k = 0; k < 6; k++) {
        WORD st = kld_s.fst[k];                                      /* looked up with the check (kld_flop_check) */
        want = (WORD)(k < 3 ? kld_s.idf : kld_s.idu);
        if (w[k] == want || w[k] == st || w[k] == 0xffff) continue;
        klog("down: flop: NO BELLY FLOP: word %d of the prone movement %08lx (+0x%x) holds %u, and %s is slot %u (65535 = none) in this level: not the words this part was read on - nothing is written, the game's own fall stays",
             k, m, (unsigned)(k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3)), w[k], kld_stock[k], st);
        kld_s.fok = 0;                                               /* the tick puts back what was written before, if anything */
        return;
    }
    if (!kld_s.fhave || m != kld_s.fm) { kld_s.fhave = 1; kld_s.fm = m; kld_s.fput = 0; memcpy(kld_s.forig, w, sizeof w); }
    for (k = 0; k < 6; k++) {
        DWORD at = m + (k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3));
        want = (WORD)(k < 3 ? kld_s.idf : kld_s.idu);
        if (w[k] == want) continue;
        if (kld_s.fput) kld_s.forig[k] = w[k];                       /* the game filled its table again (0x750900): that is the new 'found' */
        if (kld.dry) { n++; continue; }
        if (klh_data((void *)(DWORD_PTR)at, &want, 2, "the prone movement: the slot id of the fall / the get-up")) n++;
    }
    if (n && !kld_s.fput) {
        kld_s.fput = 1;
        klog("down: flop: the prone movement %08lx holds fall %u/%u/%u get-up %u/%u/%u (plain / compact / on the spot; 65535 = none): %s %d/%d/%d and %d/%d/%d",
             m, kld_s.forig[0], kld_s.forig[1], kld_s.forig[2], kld_s.forig[3], kld_s.forig[4], kld_s.forig[5],
             kld.dry ? "Dry=1, it WOULD be written" : "written", kld_s.idf, kld_s.idf, kld_s.idf, kld_s.idu, kld_s.idu, kld_s.idu);
    }
}

/* While he is down. d = D, pl = the player, ho = his health object (0 = not read), *hp = his health (changed when some
   is given back). Game thread only. */
static void kld_flop_down(DWORD pl, DWORD d, DWORD ho, DWORD ds, DWORD now, float *hp, float max, int hpok)
{
    DWORD m, ms = 0, clip, clock, tick = 0, te = 0, tv = 0; float dt = 0.02f; int e = 1, fr, ev, full; DWORD fl; char name[96]; BYTE one = 1, al = 0;
    if (!(m = klh_rd32(d + 0xc)) || klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != pl || !klh_rd(m + 0x8ec, &ms, 4)) return;
    if (!kld_s.fseen) {                                              /* which fall plays? (the movement starts it in his frame: not always in the tick of 0 -> 2) */
        clip = klh_rd32(m + 0x8cc);
        if (ds == 2 && (ms != 1 || !clip)) return;                   /* the fall has not begun in M yet: look again next tick */
        if (ds == 3 || !clip) { kld_s.fseen = 1; kld_s.fhp = *hp; return; }      /* first seen in the get-up: [M+0x8cc] is the get-up's clip - the get-up goes by its own clip (below) */
        /* first seen LYING (D 1, the fall was over within one tick of ours): ASSUMED that [M+0x8cc] still names the
           fall's clip while M is 2 (its other writers were not searched); if it does not, this down is 'the game's own'
           and the get-up still takes the flop's numbers by its clip (review2 M3) */
        kld_s.fseen = 1; kld_s.fnow = kld_s.fok && !kld.dry && kld_inlist(pl, kld_s.idf, clip);
        kld_clipfacts(clip, &fr, &ev, &fl, &full, name, sizeof name); klh_rd(d + 0xf4, &al, 1);
        if (kld_s.fnow) klog("down: flop: THE BELLY FLOP: the fall is clip %08lx '%s' of %d frames (%.2f s); no press cuts it and every hit of it is swallowed by the game's own trigger (the fall's event tick is held at its end)%s",
                             clip, name, fr, (fr - 1) / 25.0f, al ? "; THE GAME ALIGNS THIS FALL TO A PLACE ([D+0xf4], made for a fall backward): look at it" : "");
        else klog("down: flop: this fall is the game's own (clip %08lx '%s' of %d frames): %s", clip, name, fr,
                  kld.dry ? "Dry=1, nothing was written" : !kld_s.fok ? "no flop on this body" : "the slot ids were not in place when it began (he went down within a frame of the write, or the game filled its table again)");
        kld_s.fhp = *hp;
    }
    if (kld_s.fnow && (clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) != 0 && klh_rd(clock + 0x48, &tick, 4)) {
    dt = kld_rdf(clock + 0x50, &e); if (!e || dt <= 0 || dt > 0.5f) dt = 0.02f;
    if (ds == 2 && ms == 1 && klh_rd(m + 0x8dc, &te, 4) && klh_rd(m + 0x8e0, &tv, 4)) {
        if (tv != te) klh_data((void *)(DWORD_PTR)(m + 0x8e0), &te, 4, "the prone movement: the fall's event tick, held at its end");
        if (!kld_s.fasked && (long)(te - tick) <= (long)(dt * 2048.0f) + 8) {      /* two frames before the end: the game's own cut (0x8b1900) then is the end */
            if (klh_data((void *)(DWORD_PTR)(d + 0x21), &one, 1, "down-not-dead: the get-up is asked for")) {
                kld_s.fasked = 1; kld_s.t_ask = now;
                if (kld.log) klog("down: flop: the dive is over (%.2f s, %ld tick(s) left): the get-up is asked for by the game's own byte [D+0x21]", (now - kld_s.t_down) / 1000.0f, (long)(te - tick));
            }
        }
    } else if (ds == 1 && ms == 2 && (!kld_s.fasked || now - kld_s.t_ask > 300)) {      /* he lies after all (the fall ended another way): ask again, at most three times a second.
                                                                    ONLY WITH M AT 2 (review2 M2): the game itself sets the byte only then (0x47cddb .. 0x47ce2a) and
                                                                    0x6373e0 starts the get-up clip only then - D 1 with another M would go to D 3 with nothing playing */
        if (klh_data((void *)(DWORD_PTR)(d + 0x21), &one, 1, "down-not-dead: the get-up is asked for")) {
            if (kld.log) klog("down: flop: he lies (%s): the get-up is asked for by [D+0x21]", kld_s.fasked ? "the first request was not taken" : "the fall ended before the request");
            kld_s.fasked = 1; kld_s.t_ask = now;
        }
    }
    }
    /* FlopTake: of what he loses lying after a dive and getting up by the flop's clip, this share stays; the rest goes
       back the next frame. By the CLIP of the get-up, not only by 'this fall was seen as a flop' (review2 M3). */
    if (!kld.dry && hpok && ho && ((ds == 1 && kld_s.fnow) || (ds == 3 && (kld_s.fnow || kld_s.fup))) && kld.take < 0.999f && kld_s.fhp > 0 && *hp > 0.01f && *hp < kld_s.fhp - 0.01f) {
        float nh = *hp + (kld_s.fhp - *hp) * (1.0f - kld.take);
        if (nh > max) nh = max;
        if (nh > *hp && klh_data((void *)(DWORD_PTR)(ho + 4), &nh, 4, "the local player's health: part of a loss in the flop's get-up, given back")) { kld_s.fgiven += nh - *hp; *hp = nh; }
    }
    if (hpok) kld_s.fhp = *hp;
}

static void kld_tick(int game_thread)
{
    static DWORD toldrules; static char toldwhy[200];
    DWORD gd, pl, d, m, h, ho = 0, rules, state, now, tick = 0, clock, chans; int level, act, ok = 1, hpok, i = 0, st = -1;
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
    if (pl && (h = klh_rd32(pl + 0xa48)) != 0) { ho = h; hp = kld_rdf(h + 4, &ok); max = kld_rdf(h + 8, &ok); } else ok = 0;
    hpok = ok && max >= 1.0f;
    kld_tuning(act, ok ? max : 0.0f);
    if (!act || !pl) {
        if (kld_s.player) {
            if (kld.flop) kld_flop_words(kld_s.player, 0, 0);       /* the slot ids of the object we wrote go back while it still lives */
            kld_s.player = 0; kld_drop(); kld_s.dstate = 0; kld_s.nwin = 0; kld_s.fchk = kld_s.fok = kld_s.fhave = kld_s.fput = 0;
        }
        return;
    }
    if (!(d = klh_rd32(pl + 0x2948)) || klh_rd32(d) != pl || !klh_rd(d + 4, &ds, 4) || !klh_rd(d + 8, &flag, 1) || !klh_rd(d + 0x2b, &btn, 1)) return;
    if (pl != kld_s.player) {                  /* a new round, another level, another body: nothing is carried over */
        if (kld_s.player && kld_s.up) klog("down: the player object changed %.2f s into a get-up this part drove (a death, a new round, another body): not an UP", (now - kld_s.t_up) / 1000.0f);
        if (kld.flop && kld_s.player) kld_flop_words(kld_s.player, 0, 0);
        kld_s.player = pl; kld_drop(); kld_s.dstate = ds; kld_s.btn = btn; kld_s.hp = hp; kld_s.nwin = 0; kld_s.cool = 0; kld_s.downs = 0;
        kld_s.t_down = kld_s.t_lie = kld_s.t_up = now;
        kld_s.fchk = kld_s.fok = kld_s.fhave = kld_s.fput = 0;
    }
    if (kld.flop) {                            /* the belly flop: his prone movement's slot ids, while he is up */
        /* review2 S3: klchar.c's body swap keeps the player object and gives it another set - the verdict (full-body, the
           events) is of the set it was made on. Looked at again while he is up when one of the three pointers changed */
        if (kld_s.fchk && ds == 0 && (klh_rd32(pl + 0x78) != kld_s.fset[0] || klh_rd32(pl + 0x7c) != kld_s.fset[1] || klh_rd32(pl + 0x80) != kld_s.fset[2])) {
            klog("down: flop: the player %08lx has another animation set / slot table than the flop was checked on (a body swap): checked again", pl);
            kld_s.fchk = 0;
        }
        if (!kld_s.fchk) kld_flop_check(pl);
        kld_flop_words(pl, ds, 1);
        if (!kld_s.fok && kld_s.fput && ds == 0) kld_flop_words(pl, 0, 0);      /* no flop any more on this body: the game's own ids go back */
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
            if (kld_s.dead) { if (kld.log) klog("down: the down state of the man who died in it is cleared %.2f s after he went down (a new round, a reset): not an UP", (now - kld_s.t_down) / 1000.0f); }
            else if (kld_s.up && (!ok || hp <= 0.01f))                    /* a death clears D too (0x88a990): that is not an 'UP' (review S4) */
                klog("down: DEAD WHILE GETTING UP: %.2f s on the floor, %.2f s into the get-up (frame %.1f of %.1f), %d press(es), mean speed %.2f; he had %.1f health when the get-up began",
                     (now - kld_s.t_down) / 1000.0f, (now - kld_s.t_up) / 1000.0f, kld_s.lastf, kld_s.endf, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, kld_s.hp_up);
            else if (kld_s.up) klog("down: UP after %.2f s on the floor, the get-up took %.2f s (stock: 0.80; from [D+4] = 3, a press late in the fall counts the rest of the fall in), %d press(es) in it, mean speed %.2f, %.1f health lost in it (%.1f -> %.1f)%s%s",
                               (now - kld_s.t_down) / 1000.0f, (now - kld_s.t_up) / 1000.0f, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, kld_s.hp_up - hp, kld_s.hp_up, hp,
                               kld_s.capped ? "; ENDED BY THE TIME BOUND, not by the clip (its frame stood still or ran behind: say so to the lead)" : "", kld.dry ? " (Dry=1: the game's own 1.00 was played)" : "");
            else klog("down: the down state is over after %.2f s (from state %lu) without a get-up this part drove: %s", (now - kld_s.t_down) / 1000.0f, kld_s.dstate,
                      hp <= 0.01f ? "he is dead" : kld_s.dstate == 3 ? "the game's own get-up (into a cover, or its fast one)" : "ended by the game (a reset, a death, a vehicle)");
            if (kld_s.fasked) {                                      /* review2 S4: the game consumes [D+0x21] in its own frame (0x47ce56); a request of ours it
                                                                        never took (D ended first: 0x47cd80 returns at once while D is 0) would cut the NEXT fall in its first frame */
                BYTE b = 0, zero = 0;
                if (klh_rd(d + 0x21, &b, 1) && b && klh_data((void *)(DWORD_PTR)(d + 0x21), &zero, 1, "down-not-dead: a get-up request of this part the game did not take, taken back"))
                    klog("down: flop: the down state ended with this part's get-up request [D+0x21] still standing: taken back (it would have cut the next fall)");
            }
            if ((kld_s.fnow || kld_s.fup) && !kld_s.dead && hpok && hp > 0.01f) {      /* the flop's end, for a man who lives (never for one flagged dead in this down: review2 M1) */
                if (kld_s.fgiven > 0.05f) klog("down: flop: %.1f health was given back while he got up (FlopTake=%.2f: that share of every loss stays)", kld_s.fgiven, kld.take);
                if (kld_s.up && !kld.dry && kld.uppct > 0 && ho && hp < max * kld.uppct / 100.0f) {
                    float nh = max * kld.uppct / 100.0f;
                    if (klh_data((void *)(DWORD_PTR)(ho + 4), &nh, 4, "the local player's health: what a man who got up from the flop is given"))
                        klog("down: flop: up with %.1f of %.1f health (FlopUpPct=%.0f; he had %.1f) - an NPC that gets up from its own down state is given 75 %% (0x5f4d2c)", nh, max, kld.uppct, hp);
                }
            }
            kld_drop();
        }
        kld_s.dstate = ds;
    }
    if (btn && !kld_s.btn && kld_s.up) { kld_s.meter += 1.0f; kld_s.presses++; }
    kld_s.btn = btn;
    if (ds != 0 && (kld_s.dead || (i = kld_dead(hpok, hp, &st)) != 0)) {
        /* SEEN LIVE (runs D1 / D2, 2026-10-11): a death does NOT clear D - its state stays 1 / 3 to the round's end, so
           the 3 -> 0 line above never comes for a man shot while he gets up. NOTHING IS WRITTEN for a man who is dead or
           out of play, and nothing more in this down once that was seen (the flag goes with D at 0): with [Fed] Player=1
           the dead human has status 1 for the 5 s before his police body, not 7 (review2 M1) */
        if (!kld_s.dead) {
            BYTE b = 0, zero = 0;
            kld_s.dead = 1;
            klog("down: %s WHILE %s: %.2f s after he went down%s, %d press(es); he had %.1f health when the get-up began%s; crew status %d, health %.1f - nothing more is written in this down",
                 i == 1 ? "DEAD" : "OUT OF PLAY", ds == 2 ? "FALLING" : ds == 1 ? "LYING" : "GETTING UP", (now - kld_s.t_down) / 1000.0f, kld_s.fnow || kld_s.fup ? " in the belly flop" : "", kld_s.presses, kld_s.hp_up,
                 kld_s.fgiven > 0.05f ? " (FlopTake had given some back)" : "", st, hp);
            if (kld_s.fasked && klh_rd(d + 0x21, &b, 1) && b && klh_data((void *)(DWORD_PTR)(d + 0x21), &zero, 1, "down-not-dead: a get-up request of this part the game did not take, taken back"))
                klog("down: flop: this part's get-up request [D+0x21] was still standing: taken back");      /* the one write for him: our own byte, off */
        }
        return;
    }
    if (kld.flop && ds != 0) kld_flop_down(pl, d, ho, ds, now, &hp, max, hpok);
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
        float B = kld_s.fup ? kld.fbase : kld.base, P = kld_s.fup ? kld.fper : kld.per, T = kld_s.fup ? kld.ftop : kld.top;
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
            /* the flop's get-up clip: its own three numbers - BY THE CLIP ALONE (review2 M3): the get-up words are the flop's
               whenever they were written, also after a fall this part did not see as a flop; 202 frames at Base 0.5 = 16 s */
            kld_s.fup = kld.flop && kld_s.fok && kld_inlist(pl, kld_s.idu, clip);
            if (kld_s.fnow && !kld_s.fup) klog("down: flop: the get-up clip %08lx is not one of %s: it is played by Base / PerPress / Top", clip, kld.upslot);
            if (kld_s.fup && !kld_s.fnow) klog("down: flop: the fall was not seen as a flop, but the get-up clip %08lx is one of %s: FlopBase / FlopPerPress / FlopTop, FlopTake and FlopUpPct apply", clip, kld.upslot);
            B = kld_s.fup ? kld.fbase : kld.base; P = kld_s.fup ? kld.fper : kld.per; T = kld_s.fup ? kld.ftop : kld.top;
            /* THE TIME BOUND (review M1). Stock fixes the end tick when the clip starts; this part moves it with the clip's
               frame, and a frame that stands still (the player's animation update skipped: 0x74efc0's three gates; channel
               flag 0x100000: 0x50af15) would move it ahead for ever. So: the whole clip at Base speed from now + 0.25 s is
               the latest end this part ever writes - the slowest get-up is the Base one, and the state always ends. */
            kld_s.cap = tick + (DWORD)(endf / (B * 25.0f) * 1024.0f + 0.5f) + 256;
            kld_s.capped = 0; kld_s.lastf = frame; kld_s.hp_up = hp;
            klog("down: GETTING UP after %.2f s on the floor: channel %d, clip %08lx of %.0f frames, the game's speed %.2f, over at frame %.1f, the stick may end it from frame %.1f; %s %s %.2f + %.2f a press (meter - %.1f a second), at most %.2f; over in %.2f s at the latest; health %.1f of %.1f",
                 (now - kld_s.t_down) / 1000.0f, i, clip, to, r0, endf, evf, kld.dry ? "Dry=1, it WOULD be played at" : "it is played at", kld_s.fup ? "THE FLOP'S FlopBase" : "Base", B, P, kld.decay, T,
                 (float)(long)(kld_s.cap - tick) / 1024.0f, hp, max);
        }
        kld_s.lastf = frame;
        kld_s.meter -= kld.decay * dt; if (kld_s.meter < 0) kld_s.meter = 0;
        rate = B + P * kld_s.meter; if (rate > T) rate = T; if (rate < 0.05f) rate = 0.05f;
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
    /* the belly flop: its get-up clip is 202 frames (8 s at speed 1), so its three numbers are its own. All GUESSES for the owner's eyes */
    kld.flop = GetPrivateProfileIntA("Down", "Flop", 0, klh_ini) != 0;
    kld.fbase = kld_inif("FlopBase", "1.5"); kld.fper = kld_inif("FlopPerPress", "0.6"); kld.ftop = kld_inif("FlopTop", "5.0");
    kld.take = kld_inif("FlopTake", "1.0"); kld.uppct = kld_inif("FlopUpPct", "0");
    if (!kld_fin(kld.fbase) || kld.fbase < 0.25f || kld.fbase > 6.0f) kld.fbase = 1.5f;  /* under 0.25 the 202 frames would take over 32 s */
    if (!kld_fin(kld.ftop) || kld.ftop < kld.fbase || kld.ftop > 10.0f) kld.ftop = kld.fbase > 5.0f ? kld.fbase : 5.0f;
    if (!kld_fin(kld.fper) || kld.fper < 0 || kld.fper > 10.0f) kld.fper = 0.6f;
    if (!kld_fin(kld.take) || kld.take < 0 || kld.take > 1.0f) kld.take = 1.0f;
    if (!kld_fin(kld.uppct) || kld.uppct < 0 || kld.uppct > 100.0f) kld.uppct = 0;
    GetPrivateProfileStringA("Down", "FlopFallSlot", "/Damage/Death/Die_Forward", kld.fallslot, sizeof kld.fallslot, klh_ini);
    GetPrivateProfileStringA("Down", "FlopUpSlot", "/Movement/Rise/Rise_From_Stomach", kld.upslot, sizeof kld.upslot, klh_ini);
    if (kld.fallslot[0] != '/') strcpy(kld.fallslot, "/Damage/Death/Die_Forward");
    if (kld.upslot[0] != '/') strcpy(kld.upslot, "/Movement/Rise/Rise_From_Stomach");
    t[0] = 0;
    for (k = 0; k < KLD_NT; k++) {
        kld.want[k] = -1.0f;
        v = kld_inif(kld_t[k].key, "-1");
        if (kld_fin(v) && v >= kld_t[k].lo && v <= kld_t[k].hi) { kld.want[k] = v; kld.anykey = 1; if (n < (int)sizeof t - 32) n += snprintf(t + n, sizeof t - n, " %s=%.1f", kld_t[k].key, v); }
        else if (kld_fin(v) && v >= 0 && kld.on) klog("down: %s=%.2f is outside %.1f .. %.1f (%s): the game's own number stays", kld_t[k].key, v, kld_t[k].lo, kld_t[k].hi, kld_t[k].what);
    }
    if (kld.on) klog("down: on%s; the get-up is played at Base %.2f + PerPress %.2f x the mash meter (one a press of the game's own GET UP button, - Decay %.1f a second), at most Top %.2f; the trigger:%s; Log=%d. Arcade on a level that is not stock, not for a police player; data writes only (re\\player_down.md)",
                     kld.dry ? " (Dry=1: NOTHING is written, the log says what would be)" : "", kld.base, kld.per, kld.decay, kld.top, n ? t : " the game's own (no key set)", kld.log);
    if (kld.on && kld.flop) klog("down: flop: Flop=1 - THE BELLY FLOP: he goes down by %s and gets up by %s (slot ids written into his prone movement while he is up; the game plays them itself), the get-up at FlopBase %.2f + FlopPerPress %.2f x the meter, at most FlopTop %.2f; FlopTake=%.2f (the share of a loss in the get-up that stays), FlopUpPct=%.0f (health he is given when up; 0 = none)",
                                 kld.fallslot, kld.upslot, kld.fbase, kld.fper, kld.ftop, kld.take, kld.uppct);
}

#endif /* KLDOWN_C */
