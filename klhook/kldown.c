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
 *   health, in place of dying, unless the hit is worth 1,000 or more (500,000 only for the campaign's buddy, the one
 *   actor 0x6fd7c0 names - track R4; the 'left behind' kill is 1,000,000, a point-blank step 100 bullets), by the
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
 * DOG DAYS' OWN KNOCK-DOWN ([Down] Flop=1; default 0; track R3, re\player_down.md 10) - CORRECTS the block below
 *   The owner, with three pictures of stock footage: 'these kinda animations i meant for belly flop check the code for
 *   how they are in dog days' and 'the belly flop shouldnt be when im already dead'. READ + FILE (the clips' bone keys
 *   decoded as kl2 0x834170 reads them, on stock F01 / F07 and the five tab builds):
 *   - the pictures (flat on the belly; up over one knee; thrown by the hit) are the 'Wounded' family, slots
 *     /Damage/Wounded/...: ONE clip each = thrown down, lying on the belly (its event 7 to its event 8), up over a knee,
 *     on his feet. An NPC plays them as his DEATH (ZWounded@CPPScript 0x865180 picks by stance / side / 'Merc', state
 *     words +0x1e0 .. +0x1fe of 0x730be0, cut while he lies) and - /Damage/Impact/FB/Running/Front_Torso, the same
 *     animation - as a hit he LIVES through (ZGeneric slot 22, 0x4aba20): the whole clip, down and up again.
 *   - THE HUMAN'S OWN DEATH is one of them: ZFFPlayerMovementDie slot 20 (0x789b10) = /Damage/Wounded/Hero_Torso_F =
 *     'Hero_Torso_Back' (186 frames: thrown 0.55 m forward onto the belly by frame 40, lies to frame 116, kneels at
 *     ~170, stands) twice in its list and 'Hero_Torso_Front' (255 frames: onto his back) once; the game draws one by
 *     weight (0x7c6750: the low three bits of a pair's condition are weights, not conditions). So 'the belly flop' the
 *     owner knows is what he sees WHEN HE DIES - and what he asks for is that, on a man who lives.
 *   - the stock human's own fall ('the gun one') lies on his SIDE, head away; none of the Down_Not_Dead clips is prone.
 *     Die_Forward (the block below) does end chest down (full skeleton, review3 S3: the shoulders face the floor,
 *     the hips twisted) - but it is a DEATH of an actor without a ragdoll, with no rise of its own: nobody's knock-down.
 *   Flop=1: the three FALL words of the prone movement get the id of FlopFallSlot (/Damage/Wounded/Hero_Torso_F), the
 *   get-up words stay the game's, and kld_flop_one (its comment) lets the game's fall play the WHOLE clip, drives its
 *   speed by the mash from the landing on and ends the state by the movement's own 'done' value. The game's draw would
 *   put him on his BACK one time in two (weights 0.5 + 0.5 against 1.0): FlopBelly=1 (default) gives the list's other
 *   pair the belly clip's number while the part acts (kld_flop_belly; his death is then the forward one too). The
 *   whole knock-down costs no health.
 *   THIRD REVIEW (re\player_down_review3.md, applied): M1 - the end of the down state 0x7107b0 does not take the
 *   fall's input mask off (stock always passes 0x8ee220 or 0x8b1900 first), so at the state-5 write this part takes
 *   bits 1 and 0x10 off the input object's dword itself (kld_mask: 0x61ef90's lookup by reads; 0x787600's AND by data)
 *   and zeroes [D+0xf0] as 0x8ee2bb does; the mask is logged at the fall, at the end and at UP. M2 - one absolute
 *   bound from the first good read of the channel, tested before any write. S1 - a pair's clip number goes back only
 *   while a live player wears that pool and the pair reads as it was left.
 *   Flop=2 = the block below as it was (FlopFallSlot /Damage/Death/Die_Forward + FlopUpSlot, FlopTake).
 *
 * THE BELLY FLOP, FIRST FORM ([Down] Flop=2; track R2, re\player_down.md 9; its 'what the AI heisters do' is corrected above)
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
 * THE AI HEISTERS ([Down] Bots=1; default 0; its own switch, Enable=0 or 1; track R4, re\player_down.md 11)
 *   The owner after the live flop: 'do you not have the animations on the dog days npcs that are heisting??'. The
 *   game's NPC 'down not dead' (0x70e0e0 -> ZDownNotDeadNPC) has no test that excludes an AI heister, yet 267 of 267
 *   died in the live logs. WHY is not established (the level-wide pause is refuted as the whole cause; the two
 *   candidates that can be systematic - a hit animation playing, the 16 mesh probes - are in a test no key touches).
 *   kld_bots (its comment has the whole reading): prints at every AI heister's death the readable inputs of the game's
 *   test and his place, and - unless BotsDry - sets his modifier [soldier+0x124] to 1 (force), clears his 'was down
 *   once' byte BotsMax - 1 times, may set how long he lies and for how long no hit costs him. NOT SHOWN that Bots=1
 *   makes one go down: live check B1 decides. Their clip is the game's NPC one (the stock fall), not the belly flop.
 *   AND: the belly flop of Flop=1 (Hero_Torso_Back) IS DEAD MEN'S OWN knock-down - the same clip data, byte for
 *   byte, in kaneandlynch's M03_FA_A and in every Dog Days level.
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
 *   down: flop: THE KNOCK-DOWN: the fall is clip ...; the input mask a holds v      Flop=1: the fall is the slot's
 *   down: flop: the knock-down's clip is through ...: the fall's input mask a: v -> w, movement state 5 is written
 *   down: flop: UP after t s: ...; the input mask a holds v (the fall's bits 0x11 are off)
 *   down: flop: THE TIME BOUND (OF THE WHOLE KNOCK-DOWN) ...          the part gave the fall back to the game
 *   down: bots: on ...                                                 Bots=1, at start
 *   down: bots: record i (actor, soldier): health, modifier, chance, was down once; the level's pauses
 *   down: bots: record i: the modifier [soldier+0x124] 0 -> 1 (force ...)
 *   down: bots: record i DIED at health 0 without going down at (x, y, z) ... ONE PASS BEFORE: ... NOW: ... -> <which test, or 'g MAY have'>
 *   down: bots: record i IS DOWN, NOT DEAD (n of max) at (x, y, z): ...; he lies until ...; your word [score+0x1b8] ...
 *   down: bots: record i IS UP after t s at (x, y, z): health ..., heist stage, [soldier+0x4fc]
 *   down: bots: record i DIED ON THE FLOOR t s after he went down / WENT DOWN AND DIED ON THE FLOOR between two passes
 *   down: bots: record i: the 'no damage' bit is taken off (the vehicle drives out / out of play)      Log=2
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
    int belly;                                 /* Flop=1: FlopBelly (default 1) - the fall slot's pairs that are not thrown forward draw the belly clip (kld_flop_belly) */
    int flop; float fbase, fper, ftop, take, uppct; char fallslot[96], upslot[96];      /* the belly flop: 1 = Dog Days' own knock-down, ONE clip (track R3); 2 = track R2's two clips */
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
    DWORD cap0; int cap0set;                   /* Flop=1: the tick past which this part writes nothing more in this knock-down, whatever the clip's frame says (review3 M2) */
    int f7, f8, fdone, flost; DWORD fclip, t_land;      /* Flop=1: the fall clip's events 7 (he has landed) and 8 (he rises), 1 = this part ended the state / 2 = the time bound gave it back to the game, the game left the fall, the clip, GetTickCount at the landing */
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
    kld_s.f7 = kld_s.f8 = -1; kld_s.fdone = kld_s.flost = 0; kld_s.fclip = kld_s.t_land = 0; kld_s.cap0 = 0; kld_s.cap0set = 0;
}

/* THE FALL'S INPUT MASK (review3 M1; READ whole: 0x61ef90, 0x6feb90, 0x787600). The down state's start (0x76a450, at
   0x76a806 .. 0x76a834) sets bits 1 and 0x10 of a dword of the player's input object, and the game takes them off in
   three places only: 0x8ee220 (the fall is over: 0x10 at the event tick, both at D 2 -> 1), 0x8b1900 (the [D+0x21]
   request) and the reset 0x88a990. 0x7107b0 - the end of the down state - does NOT. The object, as 0x61ef90 finds it
   (a lookup: three reads, nothing written): T = [gamedata+0x1590], i = the signed byte [player+0x91e] (not -1), the
   record at T + 4 + 20 i = four pointers and a 'there' byte at +16; object = the first pointer when the byte is not 0;
   the mask = [[object+8]+0xed0] (0x6feb90 ORs into it, 0x787600 ANDs the complement). Reads only.
   i is taken as 0 .. 7 (the game tests only -1; the table's length was not read: a bound of this part's own).
   -> 1 = found (*at the dword's address, *val what it holds), 0 = none (then the game set no bit either: 0x76a825) */
#define KLD_MASK_FALL 0x11
static int kld_mask(DWORD pl, DWORD *at, DWORD *val)
{
    DWORD gd, tbl, obj, io; BYTE i = 0xff, there = 0;
    *at = 0; *val = 0;
    if (!pl || !(gd = klh_rd32((DWORD_PTR)KLH_VA(KLD_GAMEDATA))) || !(tbl = klh_rd32(gd + 0x1590)) || !klh_rd(pl + 0x91e, &i, 1) || i > 7) return 0;
    if (!klh_rd(tbl + 20 + 20 * (DWORD)i, &there, 1) || !there || !(obj = klh_rd32(tbl + 4 + 20 * (DWORD)i)) || !(io = klh_rd32(obj + 8))) return 0;
    if (!klh_rd(io + 0xed0, val, 4)) return 0;
    *at = io + 0xed0;
    return 1;
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
        if (kld.flop == 1 && (e == 7 || e == 8 || e == 31)) continue;      /* Flop=1: what the stock game's own clips of this family carry, and it plays them ON THE HUMAN itself:
                                                                               /Damage/Wounded/Hero_Torso_F is his death (ZFFPlayerMovementDie slot 20, 0x789b10). 7 and 8 go to 'nothing'
                                                                               in 0x637060; 31 goes to its case 2 (0x77ca60: an item of the action's) - ASSUMED harmless in the prone
                                                                               movement as it is in the die movement (the fall line prints the channel's event queue) */
        if (!klq_ev_to(e)) return -1;                                /* the game's tables cannot be read */
        if (klq_ev_acts(e)) { *id = e; *fr = *(WORD *)(ev + 4); return 1; }
    }
    return 0;
}

/* The frame of a clip's first event `id` (the table as kld_badevent reads it). -> -1 = none / not readable */
static int kld_evframe(DWORD clip, DWORD id)
{
    BYTE r[0x30], ev[8]; DWORD mgr, base; short n, i;
    if (!clip || !klh_rd(clip, r, sizeof r)) return -1;
    n = *(short *)(r + 6);
    if (n <= 0 || n >= 64 || !(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLD_ANIM))) || !(base = klh_rd32(mgr + 0x10))) return -1;
    for (i = 0; i < n; i++) {
        if (!klh_rd(base + *(DWORD *)(r + 0x10) + 8 * i, ev, 8)) return -1;
        if (*(DWORD *)ev == id) return *(WORD *)(ev + 4);
    }
    return -1;
}

/* Flop=1, FlopBelly=1 (default): ALWAYS THE BELLY. The slot's list in this body's set is {condition word, clip number}
   pairs and the game draws one by weight (0x7c6750: /Damage/Wounded/Hero_Torso_F = Hero_Torso_Back at 0.5 twice and
   Hero_Torso_Front - onto his BACK - at 1.0: one fall in two). Every pair whose clip is NOT thrown forward (the
   record's net root movement +0x18: z under -20 = forward; ASSUMED 'thrown forward = lands on the belly', true of the
   clips measured in re\player_down.md 10.1) gets the number of the list's first clip that is. Four bytes a pair, in the
   level's animation set (not in an object): the human's own DEATH draws from the same list (ZFFPlayerMovementDie,
   0x789b10) and is then the forward one too, for whoever wears that set; no NPC routine was found that names the slot.
   act = 0: each pair that still holds what was written gets its number back. Game thread only. */
static struct { DWORD at, old, put, pool, cond; } kld_bp[4]; static int kld_nbp;

/* Is this pair pool still some player's animation set? The remembered player object, or any of the 32 player
   places of the game data, is a ZFFPlayer whose [+0x78] is the pool. Reads only. */
static int kld_pool_live(DWORD pl, DWORD pool)
{
    DWORD gd, p; int i;
    if (!pool) return 0;
    if (pl && klh_rd32(pl) == KLD_PLAYER_VT && klh_rd32(pl + 0x78) == pool) return 1;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLD_GAMEDATA)))) return 0;
    for (i = 0; i < 32; i++)
        if ((p = klh_rd32(gd + 0x828 + 4 * i)) != 0 && klh_rd32(p) == KLD_PLAYER_VT && klh_rd32(p + 0x78) == pool) return 1;
    return 0;
}

static void kld_flop_belly(DWORD pl, int act)
{
    DWORD pool, tab, n = 0, off = 0xffffffff, mgr, recs, cnt = 0, pr[2], good = 0xffffffff, a4; float net[3]; int i, k = 0, lost = 0, a1, a2, a3; char bad[96], gname[96];
    if (!act) {
        /* review3 S1: the address is one in the level's animation data, and this runs when the part stops acting - often
           after that data was freed. A number goes back only when a live player still wears that pool AND the pair still
           reads {the condition word it had, the number this part put}; else the entry is dropped (the data is gone, or -
           after a body swap nobody else wears the old set - it keeps the belly clip to the level's end: only a human in
           that set draws from the list) */
        for (i = 0; i < kld_nbp; i++) {
            pr[0] = pr[1] = 0;
            if (kld_pool_live(pl, kld_bp[i].pool) && klh_rd(kld_bp[i].at - 4, pr, 8) && pr[0] == kld_bp[i].cond && pr[1] == kld_bp[i].put) {
                if (klh_data((void *)(DWORD_PTR)kld_bp[i].at, &kld_bp[i].old, 4, "the animation set: a pair's clip number, back as the level had it")) k++;
            } else lost++;
        }
        if (k) klog("down: flop: %d pair(s) of the fall slot's list have their own clip number again", k);
        if (lost) klog("down: flop: %d pair(s) this part had given the belly clip are NOT put back: no player wears that animation set any more, or the pair does not read as it was left (the level's data is gone, or a body swap left the set unworn)", lost);
        kld_nbp = 0;
        return;
    }
    if (kld.flop != 1 || !kld.belly || kld_nbp || kld_s.idf < 0) return;
    pool = klh_rd32(pl + 0x78); tab = klh_rd32(pl + 0x7c);
    if (!pool || !tab || !klh_rd(tab, &n, 4) || (DWORD)kld_s.idf >= n || !klh_rd(tab + 4 + 4 * (DWORD)kld_s.idf, &off, 4) || off == 0xffffffff) return;
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLD_ANIM))) || !(recs = klh_rd32(mgr)) || !klh_rd(mgr + 4, &cnt, 4)) return;
    for (i = 0; i < 16; i++) {                 /* the first clip of the list that is thrown forward */
        if (!klh_rd(pool + off + 8 * i, pr, 8) || pr[1] >= cnt) return;
        if (klh_rd(recs + pr[1] * 0x68 + 0x18, net, 12) && kld_fin(net[2]) && net[2] < -20.0f) { good = pr[1]; break; }
        if (!pr[0]) break;
    }
    if (good == 0xffffffff) { klog("down: flop: FlopBelly: no clip of %s is thrown forward in this set: the list stays as it is", kld.fallslot); return; }
    kld_clipfacts(recs + good * 0x68, &a1, &a2, &a4, &a3, gname, sizeof gname);
    for (i = 0; i < 16 && kld_nbp < 4; i++) {
        if (!klh_rd(pool + off + 8 * i, pr, 8) || pr[1] >= cnt) return;
        if (pr[1] != good && klh_rd(recs + pr[1] * 0x68 + 0x18, net, 12) && kld_fin(net[2]) && net[2] >= -20.0f) {
            kld_clipfacts(recs + pr[1] * 0x68, &a1, &a2, &a4, &a3, bad, sizeof bad);
            if (kld.dry) klog("down: flop: FlopBelly: pair %d of the list (condition word %lx) is clip %lu '%s', the root goes %.0f forward: Dry=1, it WOULD get clip %lu '%s'", i + 1, pr[0], pr[1], bad, -net[2], good, gname);
            else if (klh_data((void *)(DWORD_PTR)(pool + off + 8 * i + 4), &good, 4, "the animation set: the clip number of a pair of the fall slot, the belly clip's")) {
                kld_bp[kld_nbp].at = pool + off + 8 * i + 4; kld_bp[kld_nbp].old = pr[1]; kld_bp[kld_nbp].put = good; kld_bp[kld_nbp].pool = pool; kld_bp[kld_nbp].cond = pr[0]; kld_nbp++;
                klog("down: flop: FlopBelly: pair %d of the list (condition word %lx) was clip %lu '%s' (the root goes %.0f forward: not onto the belly): it is clip %lu '%s' now - every draw of the slot is the belly", i + 1, pr[0], pr[1], bad, -net[2], good, gname);
            }
        }
        if (!pr[0]) break;
    }
}

/* Once per player object: are both slots there for THIS body, and of the kind the prone movement plays? */
static void kld_flop_check(DWORD pl)
{
    const char *nm[2]; int id[2], k, n, i, be, bf; DWORD c[8], bid; char why[240], name[96]; int fr, ev, full; DWORD fl;
    nm[0] = kld.fallslot; nm[1] = kld.upslot;
    kld_flop_belly(pl, 0);                     /* a check made again (a body swap): what an earlier one wrote into a set goes back first */
    kld_s.fchk = 1; kld_s.fok = 0; kld_s.idf = kld_s.idu = -1; why[0] = 0;
    kld_s.fset[0] = klh_rd32(pl + 0x78); kld_s.fset[1] = klh_rd32(pl + 0x7c); kld_s.fset[2] = klh_rd32(pl + 0x80);
    for (k = 0; k < 6; k++) kld_s.fst[k] = (WORD)klq_slot(pl, kld_stock[k]);      /* -1 = no such name -> 0xffff, as the filler stores it */
    id[1] = -1;
    for (k = 0; k < (kld.flop == 1 ? 1 : 2) && !why[0]; k++) {      /* Flop=1 plays ONE clip: the get-up words stay the game's */
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
            {
                float net[3] = { 0, 0, 0 };
                klh_rd(c[i] + 0x18, net, 12);                        /* the record's net root movement; forward is -z (re\climb.md) */
                klog("down: flop: %s %s = slot %d, clip %d of %d (the game draws one by weight): %08lx '%s', %d frames (%.2f s at speed 1), %d event(s) - 7 at %d, 8 at %d (-1 = none) -, the root goes %.0f forward, record flags %lx",
                     k ? "the get-up" : "the fall", nm[k], id[k], i + 1, n, c[i], name, fr, (fr - 1) / 25.0f, ev, kld_evframe(c[i], 7), kld_evframe(c[i], 8), kld_fin(net[2]) ? -net[2] : 0.0f, fl);
            }
        }
    }
    if (why[0]) { klog("down: flop: NO BELLY FLOP on this body (player %08lx): %s. The game's own fall stays, the get-up is the mash of Base / PerPress / Top", pl, why); return; }
    kld_s.idf = id[0]; kld_s.idu = id[1]; kld_s.fok = 1;
    kld_flop_belly(pl, 1);
}

/* The six id words of M: kept as found, ours written while he is UP (the fall reads them when it starts, the get-up
   when it starts: 0x5d6060 - never between). act = 0: what was found goes back. Game thread only. */
static void kld_flop_words(DWORD pl, DWORD ds, int act)
{
    DWORD m; WORD w[6], want; int k, n = 0, ok = 1;
    if (!act) {
        kld_flop_belly(pl, 0);
        if (!kld_s.fhave || !kld_s.fput) return;
        m = kld_s.fm;
        if (klh_rd32(pl) != KLD_PLAYER_VT || klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != pl) { kld_s.fhave = kld_s.fput = 0; return; }      /* the object is gone: nothing of ours is anywhere */
        for (k = 0; k < 6; k++) {
            DWORD at = m + (k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3));
            want = (WORD)(k < 3 ? kld_s.idf : kld_s.idu);
            if (k >= 3 && kld.flop == 1) continue;                   /* Flop=1 never wrote the get-up words */
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
        want = (WORD)(k < 3 || kld.flop != 1 ? k < 3 ? kld_s.idf : kld_s.idu : st);
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
        if (k >= 3 && kld.flop == 1) continue;                       /* Flop=1: the get-up words are the game's own */
        if (w[k] == want) continue;
        if (kld_s.fput) kld_s.forig[k] = w[k];                       /* the game filled its table again (0x750900): that is the new 'found' */
        if (kld.dry) { n++; continue; }
        if (klh_data((void *)(DWORD_PTR)at, &want, 2, "the prone movement: the slot id of the fall / the get-up")) n++;
    }
    if (n && !kld_s.fput) {
        kld_s.fput = 1;
        klog("down: flop: the prone movement %08lx holds fall %u/%u/%u get-up %u/%u/%u (plain / compact / on the spot; 65535 = none): %s %d/%d/%d and %d/%d/%d%s",
             m, kld_s.forig[0], kld_s.forig[1], kld_s.forig[2], kld_s.forig[3], kld_s.forig[4], kld_s.forig[5],
             kld.dry ? "Dry=1, it WOULD be written" : "written", kld_s.idf, kld_s.idf, kld_s.idf,
             kld.flop == 1 ? kld_s.forig[3] : kld_s.idu, kld.flop == 1 ? kld_s.forig[4] : kld_s.idu, kld.flop == 1 ? kld_s.forig[5] : kld_s.idu,
             kld.flop == 1 ? " (Flop=1: the three get-up words are left as they are)" : "");
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

/* Flop=1 (track R3): DOG DAYS' OWN KNOCK-DOWN, ONE CLIP. The clips of the owner's pictures are the 'Wounded' family
   (/Damage/Wounded/...): ONE clip holds the whole thing - thrown down onto the belly, lying (from its event 7 to its
   event 8), up over one knee, on his feet. The game plays it as the FALL of its own down state (the fall words name
   the slot); this part, while D is 2 and M is 1 and the channel plays that clip:
     - holds both ticks of the fall ([M+0x8dc] the end, [M+0x8e0] the event tick) 2 s behind where the clip will end:
       the game neither ends the fall itself, nor lets a press cut it, nor shows its prompt - and its own trigger
       swallows every hit until the event tick (0x843fa0), so THE WHOLE KNOCK-DOWN COSTS NOTHING (a blast does);
     - from the landing (event 7) on writes the channel's frames a second: FlopBase + FlopPerPress x the mash meter, at
       most FlopTop (the meter: the game's own GET UP button [D+0x2b], which its input writes whenever he is down);
     - when the clip is through writes [M+0x8ec] = 5 - the value the movement's own frame writes when it is done
       (0x640c60; from ANY state when [D+0x20] is set, so 1 -> 5 is a step the game makes itself) - and the game's own
       frame ends the down state by its own path (0x47cf0f -> 0x8eea90, 0x7107b0). 0x7107b0 leaves the fall's input
       mask on him (review3 M1), so the two bits are taken off with that write (see THE END below).
   THE BOUNDS: one for the whole knock-down from its first good frame (review3 M2: to the landing at the game's pace +
   the rest at FlopBase + 1 s), and 'the rest of the clip at FlopBase + 0.5 s' after the landing; past either this
   part stops writing, the fall ends at the tick last written (2 s at most) by the game's own 2 -> 1 and its own
   lying / GET UP take over.
   Nothing here is written in a Dry run, for a dead man (the caller), or when the fall that plays is not the slot's. */
static void kld_flop_one(DWORD pl, DWORD d, DWORD ds, DWORD now, float hp)
{
    DWORD m, ms = 0, clip, h, chans, clock, tick = 0, fl, q = 0, five = 5, ma = 0, mv = 0; float frame, to, fps, dt, rate, left, land; int ok = 1, i, fr, ev, full, mk; char name[96]; long ne; BYTE al = 0;
    if (!(m = klh_rd32(d + 0xc)) || klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != pl || !klh_rd(m + 0x8ec, &ms, 4)) return;
    if (!kld_s.fseen) {
        clip = klh_rd32(m + 0x8cc);
        if (ds == 2 && (ms != 1 || !clip)) return;                   /* the fall has not begun in M yet: look again next tick */
        kld_s.fseen = 1;
        if (ds != 2) { klog("down: flop: first seen in down state %lu (the fall was over within one tick): this down is the game's own", ds); return; }
        kld_s.fnow = kld_s.fok && !kld.dry && kld_inlist(pl, kld_s.idf, clip);
        kld_clipfacts(clip, &fr, &ev, &fl, &full, name, sizeof name); klh_rd(d + 0xf4, &al, 1);
        kld_s.fclip = clip; kld_s.f7 = kld_evframe(clip, 7); kld_s.f8 = kld_evframe(clip, 8);
        if ((h = klh_rd32(m + 0x8d0)) != 0) klh_rd(h + 0x34, &q, 4);
        mk = kld_mask(pl, &ma, &mv);                                 /* the fall's two bits must read set here: the proof of the lookup (a Dry run prints it too) */
        if (kld_s.fnow) klog("down: flop: THE KNOCK-DOWN: the fall is clip %08lx '%s' of %d frames (%.2f s at speed 1): he has landed at frame %d (its event 7), rises from frame %d (event 8; -1 = none); the whole clip is played in the fall - no press cuts it, every hit of it is swallowed by the game's own trigger; from the landing on FlopBase %.2f + FlopPerPress %.2f a press, at most FlopTop %.2f; the channel's event queue is %08lx; the input mask %08lx holds %08lx (%s; bits 0x11 are the fall's)%s",
                             clip, name, fr, (fr - 1) / 25.0f, kld_s.f7, kld_s.f8, kld.fbase, kld.fper, kld.ftop, q, ma, mv, mk ? "found" : "NO INPUT OBJECT: the game set no bit either", al ? "; THE GAME ALIGNS THIS FALL TO A PLACE ([D+0xf4]): look at it" : "");
        else klog("down: flop: this fall is the game's own (clip %08lx '%s' of %d frames, %d event(s), the channel's event queue %08lx; the input mask %08lx holds %08lx - %s; bits 0x11 are the fall's): %s", clip, name, fr, ev, q, ma, mv, mk ? "found" : "NO INPUT OBJECT",
                  kld.dry ? "Dry=1, nothing was written" : !kld_s.fok ? "no flop on this body" : "the slot ids were not in place when it began (he went down within a frame of the write, or the game filled its table again)");
        kld_s.meter = 0; kld_s.presses = 0; kld_s.sumr = 0; kld_s.nr = 0; kld_s.cap = 0; kld_s.lastline = now;
    }
    if (!kld_s.fnow || kld_s.fdone) return;
    if (ds != 2 || ms != 1) {                  /* a cover ([D+0x20]), a reset: the game's own states go on */
        if (!kld_s.flost) { kld_s.flost = 1; klog("down: flop: the game left the fall %.2f s into the knock-down (down state %lu, movement state %lu): its own states go on from here", (now - kld_s.t_down) / 1000.0f, ds, ms); }
        return;
    }
    if (!(h = klh_rd32(m + 0x8d0)) || !(chans = klh_rd32(pl + 0x70))) return;
    for (i = 0; i < 16; i++) if (h == chans + 0x1c + 0x38 * i) break;
    if (i == 16 || klh_rd32(h) != kld_s.fclip || klh_rd32(m + 0x8cc) != kld_s.fclip) {
        kld_s.fdone = 2; klog("down: flop: the fall's channel %08lx does not play the knock-down's clip %08lx any more: left to the game", h, kld_s.fclip);
        return;
    }
    if (!(clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    dt = kld_rdf(clock + 0x50, &ok); fl = klh_rd32(h + 0x14);
    frame = kld_rdf(h + 4, &ok); to = kld_rdf(h + 0xc, &ok); fps = kld_rdf(h + 0x10, &ok);
    if (!ok || to < 2 || to > 5000 || frame < 0 || frame > to + 1 || fps < 0.5f || fps > 250 || dt < 0 || dt > 0.5f) return;
    kld_s.lastf = frame; kld_s.endf = to;
    left = to - frame;
    land = kld_s.f7 >= 0 ? (float)kld_s.f7 : 0.3f * to;              /* no event 7: where the game takes a fall's 'event 6' without one (0x478270) - a GUESS for such a clip */
    /* THE ABSOLUTE BOUND (review3 M2), in the game's own ticks (they stand still in a pause), set at the first good
       read of the channel and tested BEFORE ANY WRITE of this pass: the way to the landing at the pace the game gave
       the clip + the rest at FlopBase + 1 s. The bound after the landing (below) only starts at the landing: a channel
       whose frame stands still BEFORE it, or a stopped one that reads frame 0 .. 2, would have its two ticks pushed
       2 s ahead for ever - floored, masked and immune for good. Past this tick the part writes nothing more in this
       knock-down: the fall ends at the tick last written (2 s at most) by the game's own 2 -> 1 (0x8ee220: the mask
       comes off there), he lies the game's way and its GET UP gets him up. (Every `return` above writes nothing, so
       a channel that cannot be read ends the same way.) */
    if (!kld_s.cap0set) {
        float way = land > frame ? (land - frame) / fps : 0.0f, rest = (to - (land > frame ? land : frame)) / (kld.fbase * 25.0f);
        kld_s.cap0set = 1; kld_s.cap0 = tick + (DWORD)((way + rest) * 1024.0f + 0.5f) + 1024;
    }
    if ((long)(tick - kld_s.cap0) > 0) {
        kld_s.fdone = 2;
        klog("down: flop: THE TIME BOUND OF THE WHOLE KNOCK-DOWN (frame %.1f of %.0f, %.2f s after he went down, channel flags %lx): this part stops writing - the game ends the fall at the tick last written and its own lying / GET UP take over; say so to the lead", frame, to, (now - kld_s.t_down) / 1000.0f, fl);
        return;
    }
    if (left <= 0.5f || (frame > 2.0f && ((fl & 7) == 0 || (fl & 7) == 4))) {      /* the clip is through (or its channel has stopped - state 0 / 4, as the get-up below reads it): the state is over */
        /* THE END (review3 M1). Stock ends a down state through 0x8ee220 or 0x8b1900 first - both take the fall's input
           mask off (bits 1 and 0x10) - and only then reaches 0x7107b0, which does not touch it. This form goes from the
           fall straight to 0x7107b0 (M = 5 while D is 2), so the two bits are taken off HERE, by data, as 0x787600 does
           (an AND on the dword kld_mask finds), and [D+0xf0] ('who floored him', a plain pointer the game zeroes at
           0x8ee2bb when a fall is over) is zeroed with it. Order: the mask first; when its write is refused the state 5
           is NOT written - the part stops and the game ends the fall its own way (which clears the mask). */
        DWORD nv, zero = 0;
        mk = kld_mask(pl, &ma, &mv); nv = mv & ~(DWORD)KLD_MASK_FALL;
        if (mk && nv != mv && !klh_data((void *)(DWORD_PTR)ma, &nv, 4, "the player's input object: the fall's two mask bits (1, 0x10) off, as the game's own end of a fall takes them off (0x8ee220)")) {
            kld_s.fdone = 2;
            klog("down: flop: the clip is through but the fall's input mask %08lx (%08lx) could not be written: state 5 is NOT written - the game ends the fall at the tick last written and its own lying / GET UP take over", ma, mv);
            return;
        }
        if (klh_data((void *)(DWORD_PTR)(m + 0x8ec), &five, 4, "the prone movement: its state, 5 = done (what its own frame writes, 0x640c60)")) {
            kld_s.fdone = 1;
            klh_data((void *)(DWORD_PTR)(d + 0xf0), &zero, 4, "down-not-dead: who floored him, cleared as the game does when a fall is over (0x8ee2bb)");
            klog("down: flop: the knock-down's clip is through (frame %.1f of %.0f, %.2f s after he went down): the fall's input mask %08lx: %08lx -> %08lx (%s), movement state 5 is written - the game ends the down state in its next frame", frame, to, (now - kld_s.t_down) / 1000.0f,
                 ma, mv, mk ? nv : 0, mk ? "bits 0x11 off" : "NO INPUT OBJECT: nothing to take off");
        } else if (mk && nv != mv) klh_data((void *)(DWORD_PTR)ma, &mv, 4, "the player's input object: the fall's mask bits back (the state write was refused: the fall goes on)");
        return;
    }
    if (frame >= land) {
        float B = kld.fbase, P = kld.fper, T = kld.ftop;
        if (!kld_s.t_land) {
            kld_s.t_land = now; kld_s.hp_up = hp;
            kld_s.cap = tick + (DWORD)(left / (B * 25.0f) * 1024.0f + 0.5f) + 512;
            if (kld.log) klog("down: flop: he has landed %.2f s after he went down (frame %.1f of %.0f): from here FlopBase %.2f + the mash; over in %.2f s at the latest", (now - kld_s.t_down) / 1000.0f, frame, to, B, (float)(long)(kld_s.cap - tick) / 1024.0f);
        }
        if ((long)(tick - kld_s.cap) > 0) {                          /* the bound: the clip's frame stood still or ran behind its slowest pace */
            kld_s.fdone = 2;
            klog("down: flop: THE TIME BOUND (frame %.1f of %.0f, %.2f s after the landing): this part stops writing - the game ends the fall at the tick last written and its own lying / GET UP take over; say so to the lead", frame, to, (now - kld_s.t_land) / 1000.0f);
            return;
        }
        kld_s.meter -= kld.decay * dt; if (kld_s.meter < 0) kld_s.meter = 0;
        rate = B + P * kld_s.meter; if (rate > T) rate = T; if (rate < 0.05f) rate = 0.05f;
        kld_s.sumr += rate; kld_s.nr++;
        if (kld.log >= 2 && now - kld_s.lastline >= 250) { kld_s.lastline = now; klog("down: flop: frame %.1f of %.0f (%s), speed %.2f, meter %.2f, %d press(es)", frame, to, kld_s.f8 >= 0 && frame < kld_s.f8 ? "he lies" : "he rises", rate, kld_s.meter, kld_s.presses); }
        fps = rate * 25.0f;
        if (!klh_data((void *)(DWORD_PTR)(h + 0x10), &fps, 4, "the knock-down clip's channel: frames a second")) return;
    }
    /* the two ticks: always 2 s behind where the clip will be through at the pace it has now */
    ne = (long)tick + (long)(left / fps * 1024.0f + 0.5f) + 2048;
    klh_data((void *)(DWORD_PTR)(m + 0x8dc), &ne, 4, "the prone movement: the tick the fall is over, held behind the clip's end");
    klh_data((void *)(DWORD_PTR)(m + 0x8e0), &ne, 4, "the prone movement: the fall's event tick, held with its end");
}

/* ---- the AI heisters ([Down] Bots=1; track R4, re\player_down.md 11) ------------------------------------------- */
/* READ (kl2 0x8473a0, 0x688190, 0x70e0e0, 0x70f330, 0x7ea990, 0x5f4ac0, 0x803530; all whole):
   An NPC's damage routine asks, at the hit that takes his last health (0x847937 .. 0x847968; not asked while word
   [[actor+0x54]+0x3a] is not 0 = he takes no damage at all, 0x8477ae), soldier slot 51 (0x688190: never for a dog) ->
   0x70e0e0. YES = he goes 'down not dead' instead of dying. It says NO when
     a. byte [actor+0x64c] is set (he is down already), or his ZWounded state [[soldier+0x4b4]+8] is not 0 / 4
     b. 0x70f330 (his ZDownNotDeadNPC = [soldier+0x4b8]) refuses, in this order:
          - 0x619d10: his bone 2 is within 20 of [actor+0x46c] (node flag 0x1000)
          - [actor+0x774] is not 0: somebody holds him
          - 0x75a2e0: he sits in a seat - THREE parts: [actor+0x88c] and [seat+0x18] not 0 and [seat+0x40] == 0
          - 0x4a05f0: the task at [soldier+0xa4] runs (its state +8 is not 0 / 4). That object is his ZHitAnimTask
            (vtable 0xbcf87c, made by the constructor at 0x7cfc79): NO DOWN WHILE A HIT ANIMATION PLAYS
          - 0x86a150 / 0x86f0c0: the object he is attached to, [actor+0x5b4], is a ZLNKOBJ (type pair 0x153a898) AND a
            ZHavokLnkObj (type pair 0x168cddc) - both by its vtable slot 12, so the hook can only print the vtable
          - 16 probes of 100 units around him on the navigation mesh (PF4::ZData slot 41, 0x4dd5f0): ALL must pass =
            one metre of mesh free in every direction
     c. byte [actor+0x5cb] is set = HE WAS DOWN ONCE (set by the down's script at its start, 0x5f4b56; never cleared)
     d. the hit was in the head (bone body part 2 / 3 -> record +0x30, 0x61a9f0) from nearer than [T+0x5c] = 1500
     e. the hit's damage [rec+0x28] is MORE THAN 1,000 (0x70e1c7 jumps on C0 only: exactly 1,000 passes)
     f. his EDownNotDeadModifier [soldier+0x124] is 2 (prevent) - 1 (force) says YES here, whatever g says. It is 0 from
        the constructor (0x7cfb3b) and written only by a SquadModifierBehaviour's field 13 (0x803530: 1, 2, 3 -> 0)
     g. modifier 0 (0x70e206 .. 0x70e29c; [gamedata+0x4d04] = the tick of the level's last NPC down, set by every
        down's start 0x7eaab9, a policeman's too; 0 = none yet skips the first test):
          last down less than [T+0x54] = 5 s ago   -> NO
          last down less than [T+0x58] = 20 s ago  -> yes only by his chance [actor+0x804] per cent (= ZFFActor's
                                                      level field 15: 50.0 on every AI heister, stock and ours)
          later                                    -> YES, no draw
        So g CANNOT refuse every time: the first heister at health 0 after 20 quiet seconds goes down if a .. e pass.
   No test of the team, of Arcade, of the squad's kind: by the code an AI heister CAN go down.
   LOG: 267 of 267 AI heisters at health 0 in the live logs are dead (177 of them by an ordinary bullet; 7 of 7 on
   the stock Subway copy). WHICH test said no each time is NOT ESTABLISHED. g is refuted as the whole cause (above);
   the two that CAN be systematic are both in b and NEITHER IS PROVEN: the ZHitAnimTask (a heister dies under some
   hundred small hits at about 3 a second) and the 16 mesh probes (the bots stand at cover, walls, corridors). No key
   here touches b. The 'DIED ...' line prints the readable inputs and his place; it CANNOT tell g from b / d / e
   (the game asks a .. e first) - the run that decides is the one with the modifier forced (B1): a death that still
   says 'the modifier was 1' is b / d / e.
   THE DOWN ITSELF (0x7ea990, 0x5f4ac0): he lies [T+0x4c] .. [T+0x50] = 1.5 .. 3.0 s by a random number (the tick is
   [dnd+0x14]), is given 25 % of his maximum if he has less, fires from the floor at his target (the soldier's own
   slots +0x1c4 / +0x164), takes hits in full (a second health 0 kills: a), then 75 % of his maximum, state Stand.
   The clips: the state graph 0x730be0's DownNotDead state = /Damage/Down_Not_Dead/... - the stock human's own fall
   ('the gun one'), NOT the belly flop.
   WHEN HE IS UP, in Arcade, for team Ally / Mercenary (0x5f4dd8 .. 0x5f4dfc): byte [soldier+0x4fc] = 1. That byte
   makes his squad's ZDefendBehaviourRout count him as ARRIVED (0x686c77; re\boardall_review_code.md): the Defend
   step his chain is WAITING in ends and its NEXT fires although he did not reach the place; his next order puts the
   byte back (0x760efe). So every down can SKIP one step of his route - a hold, a loot stop, a Retomoto gate. Not a
   write of this part: the game's own. The 'IS UP' line prints the byte; the live check is his stage 1 -> 2 -> 3.
   A HUMAN WHO FLOORS HIM: at health 0 with a player attacker the damage routine calls rules slot 131 (0x8477fd ->
   0x7cc270, read whole: the attacker's word [score+0x1b8+2*index] += word [T+0x700] or [T+0x6fc] by slot 107's
   answer) BEFORE the down is asked - so it is added at the floor AND again at the real kill. What that word shows
   was not read; the 'IS DOWN' line prints it for the human (now and one pass before).
   WHAT THIS PART WRITES (data, per AI crew record in play; each only by its key):
     Bots=1       [soldier+0x124] 0 -> 1 (force): tests f / g answer yes; a .. e stay the game's. Put back to 0.
     BotsMax=n    (default 2; the game's own is 1) byte [actor+0x5cb] 1 -> 0 once he is up again, n - 1 times
     BotsLie=s    (default 0 = the game's 1.5 .. 3.0) [dnd+0x14] = the down's first tick + s
     BotsFree=s   (default 0.75 = the stock human's free fall) for s seconds of a down bit 0x800 of the word
                  [[actor+0x54]+0x3a] is held set - the bit the game itself sets for 0.1 s at a down's start (0x70e2d7 ->
                  0x6c75c0) and for 7 s on the campaign's buddy (0x5f4d82): while the word is not 0 no hit costs him -
                  NO hit: the health is not written (0x8477ae) and the death is skipped (0x847945), so the game's kill
                  of the crew left behind (1,000,000 a step while the vehicle drives out) and a point-blank step are
                  swallowed too. Therefore the bit is never held once the vehicle's state is 5 or more, and a long
                  BotsFree is a long immortality: keep it short.
                  ASSUMED harmless for the word's other readers (20 `cmp word [+0x3a]`; read: 0x8477ae, 0x847945,
                  0x828735, 0x4d83bb; the other 16 NOT read: re\player_down_review4.md S2) for those seconds - the
                  FIRST live run goes without it (BotsFree=0). 0 = none. The game takes a timed bit off by its own mask
                  [+0x40] at the tick [+0x3c] and then zeroes both (0x638e2e .. 0x638e5c), and the down's script clears
                  0x800 once at its start (0x5f4bb5 -> 0x6f48a9): this part sets the bit again in its next pass
     BotsUpPct=p  (default 0 = the game's 75) his health when he is up, per cent of the maximum that stands in his
                  health object - klgrudge.c's ([Bots] CrewHealth) if that part wrote one. No fight between the two:
                  klgrudge writes the health only when it changes the MAXIMUM, and then keeps his share
     BotsNear=d   (default: not written) [T+0x5c]: 0 = a head hit from near floors him too. EVERY NPC of the level.
   BotsDry=1 (or Dry=1): nothing is written, the lines say what would be. No call, no patch. */
#define KLD_SOLDIER_VT 0x00bd0954             /* CPPScript::ZSoldier (its only vtable; klescort.c) */
static struct {
    int on, dry, force, max; float lie, freet, uppct, near_;
} kld_bk;
static struct kld_bot {
    DWORD actor, soldier, t_down, tick_down, lie_tick; float hp, hmax; BYTE down, cnt, put124, shield, said, dead;
    DWORD age; float chance; DWORD mod, ws, as, holder, seat, seat18, seat40, att, attvt; WORD inv; BYTE was;      /* the readable inputs of 0x70e0e0 as they stood one pass before */
} kld_b[KLB_NREC];
static DWORD kld_brules; static float kld_near0; static int kld_nearput;
static WORD kld_kw; static int kld_kwok;      /* the human's word [score+0x1b8+2*index] one pass before (rules slot 131 adds to it when he takes an NPC's last health) */

static int kld_bot_ok(DWORD actor, DWORD *soldier)
{
    DWORD s;
    if (!actor || klh_rd32(actor) != KLB_ACTOR_VT) return 0;
    if (!(s = klh_rd32(actor + 0x77c)) || klh_rd32(s) != KLD_SOLDIER_VT || klh_rd32(s + 0x40) != actor) return 0;
    *soldier = s;
    return 1;
}

/* the bit of BotsFree: on = hold 0x800 set, off = take it off if it stands (never the word's other bits) */
static void kld_bot_shield(struct kld_bot *b, int on)
{
    DWORD o = klh_rd32(b->actor + 0x54); WORD w = 0, n;
    if (!o || !klh_rd(o + 0x3a, &w, 2)) return;
    n = on ? (WORD)(w | 0x800) : (WORD)(w & ~0x800);
    if (n != w && !klh_data((void *)(DWORD_PTR)(o + 0x3a), &n, 2, "an AI heister's 'takes no damage' word: the down-not-dead bit 0x800")) return;
    b->shield = (BYTE)on;
}

/* everything of ours off one bot (he is gone, the part stops, another round) */
static void kld_bot_back(struct kld_bot *b, const char *why, int i)
{
    DWORD s = 0, m = 0, zero = 0;
    if (b->actor && kld_bot_ok(b->actor, &s) && s == b->soldier) {
        if (b->shield) kld_bot_shield(b, 0);
        if (b->put124 && klh_rd(s + 0x124, &m, 4) && m == 1 && klh_data((void *)(DWORD_PTR)(s + 0x124), &zero, 4, "an AI heister's EDownNotDeadModifier: back to 0"))
            { if (kld.log >= 2) klog("down: bots: record %d: the modifier [soldier+0x124] is 0 again (%s)", i, why); }
    }
    memset(b, 0, sizeof *b);
}

static void kld_bots(int act, DWORD now)
{
    struct klb_snap sn; DWORD gd, clock, tun, tick = 0, last = 0; float t54 = 5.0f, t58 = 20.0f, t5c = 1500.0f; int i, ok = 1, wr, kwok = 0; WORD kw = 0;
    if (!kld_bk.on) return;
    if (act) act = klb_read(&sn) && sn.state == KLB_ROUND;
    if (!act || sn.rules != kld_brules) {      /* the round is over / another rules object: nothing of ours stays in a live soldier */
        for (i = 0; i < KLB_NREC; i++) if (kld_b[i].actor) kld_bot_back(&kld_b[i], "the round is over", i);
        if (kld_nearput && (tun = klh_rd32((DWORD_PTR)KLH_VA(KLD_TUNING))) != 0 && klh_data((void *)(DWORD_PTR)(tun + 0x5c), &kld_near0, 4, "tuning: the distance under which a head hit kills an NPC outright, back"))
            klog("down: bots: BotsNear: [T+0x5c] is %.0f again", kld_near0);
        kld_nearput = 0; kld_kwok = 0;
        kld_brules = act ? sn.rules : 0;
        if (!act) return;
    }
    wr = !kld.dry && !kld_bk.dry;
    if (sn.human >= 0 && sn.human < KLB_NREC && klh_rd(sn.score + 0x1b8 + 2 * sn.human, &kw, 2)) kwok = 1;
    if (!kld_kwok) kld_kw = kw;                /* first pass of the round: no 'before' yet */
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLD_GAMEDATA))) || !(clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4) || !klh_rd(gd + 0x4d04, &last, 4)) return;
    if ((tun = klh_rd32((DWORD_PTR)KLH_VA(KLD_TUNING))) != 0) {
        float a = kld_rdf(tun + 0x54, &ok), b = kld_rdf(tun + 0x58, &ok), c = kld_rdf(tun + 0x5c, &ok);
        if (ok && a >= 0 && a < 1000 && b >= 0 && b < 1000 && c >= 0 && c < 1e6f) {
            t54 = a; t58 = b; t5c = c;
            if (kld_bk.near_ >= 0 && wr && !kld_nearput && KLD_ABS(c - kld_bk.near_) > 0.01f) {
                kld_near0 = c;
                if (klh_data((void *)(DWORD_PTR)(tun + 0x5c), &kld_bk.near_, 4, "tuning: the distance under which a head hit kills an NPC outright")) {
                    kld_nearput = 1; klog("down: bots: BotsNear: [T+0x5c] %.0f -> %.0f (a head hit from nearer than this kills an NPC outright - EVERY NPC of the level, the police too)", c, kld_bk.near_);
                }
            }
        }
    }
    for (i = 0; i < sn.n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &sn.r[i]; struct kld_bot *b = &kld_b[i];
        DWORD s = 0, h, mod = 0, wo, ao, ws = 0, as = 0, dnd, holder = 0, seat = 0, seat18 = 0, seat40 = 0, att = 0, attvt = 0, o54; BYTE dn = 0, was = 0; WORD inv = 0; float hp, hmax, chance, pos[3] = { 0, 0, 0 }; int hok = 1;
        if (!r->used || !(r->flags & 1) || !kld_bot_ok(r->actor, &s)) { if (b->actor) kld_bot_back(b, "its record is gone", i); continue; }
        if (b->actor != r->actor || b->soldier != s) { if (b->actor) kld_bot_back(b, "another actor in its record", i); b->actor = r->actor; b->soldier = s; }
        if (!(h = klh_rd32(r->actor + 0x5fc)) || klh_rd32(h + 0x24) != r->actor) continue;
        hp = kld_rdf(h + 4, &hok); hmax = kld_rdf(h + 8, &hok);
        if (!hok || hmax < 1 || !klh_rd(r->actor + 0x64c, &dn, 1) || !klh_rd(r->actor + 0x5cb, &was, 1) || !klh_rd(s + 0x124, &mod, 4) || mod > 3) continue;
        chance = kld_rdf(r->actor + 0x804, &hok);
        if ((wo = klh_rd32(s + 0x4b4)) != 0) klh_rd(wo + 8, &ws, 4);
        if ((ao = klh_rd32(s + 0xa4)) != 0) klh_rd(ao + 8, &as, 4);
        klh_rd(r->actor + 0x774, &holder, 4); klh_rd(r->actor + 0x88c, &seat, 4);
        if (seat) { klh_rd(seat + 0x18, &seat18, 4); klh_rd(seat + 0x40, &seat40, 4); }      /* 0x75a2e0: seated = all three */
        if (klh_rd(r->actor + 0x5b4, &att, 4) && att) klh_rd(att, &attvt, 4);                 /* b's fifth test: what he is attached to (its class only by the vtable) */
        if ((o54 = klh_rd32(r->actor + 0x54)) != 0) klh_rd(o54 + 0x3a, &inv, 2);
        dnd = klh_rd32(s + 0x4b8);
        if (b->dead && r->status == 0 && hp > 0.01f && !dn) {      /* the same actor lives again (another round on the same rules object): a new count */
            if (kld.log >= 2) klog("down: bots: record %d lives again (health %.1f): its downs are counted anew", i, hp);
            b->dead = 0; b->down = 0; b->cnt = 0; b->hp = hp;
        }
        if (!b->said) {
            b->said = 1; b->hp = hp; b->down = dn;
            if (r->status == 7 || hp <= 0.01f) b->dead = 1;        /* first seen dead: nothing to say about how */
            if (kld.log) klog("down: bots: record %d (actor %08lx, soldier %08lx): health %.1f of %.1f, modifier [soldier+0x124] %lu (0 not set, 1 force, 2 prevent), his chance [actor+0x804] %.0f %%, was down once [actor+0x5cb] %u; the level's pauses [T+0x54] %.1f s / [T+0x58] %.1f s, head-hit distance [T+0x5c] %.0f",
                              i, r->actor, s, hp, hmax, mod, chance, was, t54, t58, t5c);
        }
        /* --- he is dead: at health 0 with the 'down' byte clear the game's test said NO (or was not asked) */
        if (!b->dead && (r->status == 7 || (hp <= 0.01f && !dn && b->hp > 0.01f))) {
            b->dead = 1;
            kle_node(klh_rd32(r->actor + 4), pos, 0);
            if (b->down) klog("down: bots: record %d DIED ON THE FLOOR %.2f s after he went down (down %u of %d) at (%.0f, %.0f, %.0f): a second health 0 kills (0x70e0f8); down byte now %u, crew status %u; your word [score+0x1b8] %u (one pass before %u)", i, (now - b->t_down) / 1000.0f, b->cnt, kld_bk.max, pos[0], pos[1], pos[2], dn, r->status, kw, kld_kw);
            else if (dn) {                         /* the down byte and the death arrived in ONE pass: the game's test said YES - not a refusal */
                b->cnt++;
                klog("down: bots: record %d WENT DOWN AND DIED ON THE FLOOR between two passes of the hook (down %u of %d) at (%.0f, %.0f, %.0f): the down byte [actor+0x64c] is %u now and was 0 one pass before, health %.1f -> %.1f, crew status %u - the game's test said YES; count it as a down, not as a refusal",
                     i, b->cnt, kld_bk.max, pos[0], pos[1], pos[2], dn, b->hp, hp, r->status);
            } else if (kld.log) {
                /* the inputs as they stood ONE PASS BEFORE (the hit came between two passes), named in the GAME's order a, b, c, f, g.
                   d / e (the hit record) and three of b's tests (bone 2, the attachment's class, the 16 mesh probes) cannot be read
                   from here, and they are asked BEFORE f / g: a 'g' below is never more than 'g may have' */
                float age = b->age ? (float)(long)(tick - b->age) / 1024.0f : -1.0f; int seated = b->seat && b->seat18 && !b->seat40; const char *no =
                    b->inv ? "he took no damage at all ([+0x3a] not 0): the test was not asked" :
                    b->ws != 0 && b->ws != 4 ? "a: his ZWounded state ran" :
                    b->holder ? "b: somebody held him" : seated ? "b: he sat in a seat ([actor+0x88c], [seat+0x18] set, [seat+0x40] 0)" :
                    b->as != 0 && b->as != 4 ? "b: HIS ZHitAnimTask RAN ([soldier+0xa4], state not 0 / 4): a hit animation was playing one pass before - no down while it plays (0x4a05f0)" :
                    b->was ? "c: HE WAS DOWN ONCE ([actor+0x5cb])" :
                    b->mod == 2 ? "f: the modifier is 2 (prevent) - unless b / d / e refused first" :
                    b->mod == 1 ? "NOT f / g (the modifier was 1 = force) and none of the readable a / b / c: so b's unreadable part (a hit animation started by this very hit, the 16 probes of 1 m on the mesh, his bone 2 low, attached to a ZHavokLnkObj) or the hit itself (d: the head from nearer than [T+0x5c]; e: more than 1,000). Lay his place on the mesh - say so to the track" :
                    age >= 0 && age < t54 ? "g MAY have refused (an NPC - a policeman counts - went down less than [T+0x54] s ago), BUT a .. e are asked first and are NOT excluded (b's hit animation / mesh probes, d the head, e): this line does not decide - the run with the modifier forced does" :
                    age >= 0 && age < t58 ? "g MAY have refused by his chance (an NPC went down less than [T+0x58] s ago), BUT a .. e are asked first and are NOT excluded: this line does not decide - the run with the modifier forced does" :
                    "NOT g (no NPC went down in the last [T+0x58] s: g says yes without a draw) and none of the readable a / b / c / f: so b's unreadable part (a hit animation started by this very hit, the 16 mesh probes, bone 2, a ZHavokLnkObj) or the hit itself (d / e). Lay his place on the mesh - say so to the track";
                klog("down: bots: record %d DIED at health 0 without going down at (%.0f, %.0f, %.0f) (lost %.1f; crew status %u; down byte [actor+0x64c] now %u). ONE PASS BEFORE: modifier %lu, was down once %u, the last NPC of the level went down %s%.1f s ago, his chance %.0f %%, ZWounded state %lu, ZHitAnimTask [soldier+0xa4] state %lu, holder %08lx, seat %08lx ([+0x18] %08lx, [+0x40] %08lx), attached to [actor+0x5b4] %08lx (vtable %08lx: refused if that class is a ZHavokLnkObj), word [+0x3a] %04x. NOW: ZWounded %lu, ZHitAnimTask %lu, word %04x -> %s",
                     i, pos[0], pos[1], pos[2], b->hp, r->status, dn, b->mod, b->was, b->age ? "" : "never / ", age < 0 ? 0.0f : age, b->chance, b->ws, b->as, b->holder, b->seat, b->seat18, b->seat40, b->att, b->attvt, b->inv, ws, as, inv, no);
            }
            if (b->shield) kld_bot_shield(b, 0);
        }
        /* the 'no damage' bit swallows EVERY kill (0x8477ae, 0x847945): never held while the vehicle drives out (state 5 on: the
           game's own kill of the crew left behind, re\bots_follow_out.md) or on a record that is no longer in play */
        if (b->shield && (sn.veh >= 5 || r->status != 0)) {
            kld_bot_shield(b, 0);
            if (kld.log >= 2) klog("down: bots: record %d: the 'no damage' bit is taken off (%s)", i, sn.veh >= 5 ? "the vehicle drives out: the game's kill of those left behind must reach him" : "its record is out of play");
        }
        /* --- he goes down / he is up */
        if (!b->dead && dn && !b->down) {
            b->down = 1; b->cnt++; b->t_down = now; b->tick_down = tick; b->lie_tick = 0;
            kle_node(klh_rd32(r->actor + 4), pos, 0);
            klog("down: bots: record %d IS DOWN, NOT DEAD (%u of %d this round) at (%.0f, %.0f, %.0f): health %.1f of %.1f (the game gives him 25 %% if he has less), modifier %lu; he lies until tick %ld = %.2f s from now (the game's 1.5 .. 3.0 s by a random number); your word [score+0x1b8] %u (one pass before %u: a step = rules slot 131 counted this floor for you, and will count his real death again)%s",
                 i, b->cnt, kld_bk.max, pos[0], pos[1], pos[2], hp, hmax, mod, dnd ? (long)klh_rd32(dnd + 0x14) : 0L, dnd ? (float)(long)(klh_rd32(dnd + 0x14) - tick) / 1024.0f : 0.0f, kw, kld_kw, wr ? "" : " (Dry: nothing is written for him)");
        } else if (!b->dead && !dn && b->down) {
            BYTE arr = 0;
            b->down = 0;
            if (b->shield) kld_bot_shield(b, 0);
            klh_rd(s + 0x4fc, &arr, 1);
            kle_node(klh_rd32(r->actor + 4), pos, 0);
            klog("down: bots: record %d IS UP after %.2f s at (%.0f, %.0f, %.0f): health %.1f of %.1f (the game's script gives 75 %%), was-down byte %u, heist stage %u; [soldier+0x4fc] %u (1 = the game's own get-up line 0x5f4dfc: his squad's waiting Defend step counts him as ARRIVED and its next step fires - watch his stage go on to 3)", i, (now - b->t_down) / 1000.0f, pos[0], pos[1], pos[2], hp, hmax, was, r->stage, arr);
            if (wr && kld_bk.uppct > 0 && hp > 0.01f && KLD_ABS(hp - hmax * kld_bk.uppct / 100.0f) > 0.5f) {
                float nh = hmax * kld_bk.uppct / 100.0f;
                if (klh_data((void *)(DWORD_PTR)(h + 4), &nh, 4, "an AI heister's health: what he has when he is up from his down (BotsUpPct)")) { klog("down: bots: record %d: up with %.1f of %.1f health (BotsUpPct=%.0f; the game gave %.1f)", i, nh, hmax, kld_bk.uppct, hp); hp = nh; }
            }
        }
        if (!b->dead && wr && r->status == 0) {
            if (b->down) {
                /* BotsLie: the tick his script waits for. Slot 1 of his down (0x7ea990) writes its own when the goal starts - a frame
                   or more after 0x70e0e0 set the byte we saw - so ours is written until it stands (a fixed tick: bounded) */
                if (kld_bk.lie > 0 && dnd) {
                    DWORD cur = klh_rd32(dnd + 0x14);
                    if (!b->lie_tick) b->lie_tick = b->tick_down + (DWORD)(kld_bk.lie * 1024.0f);
                    if (cur != b->lie_tick && (long)(b->lie_tick - tick) > 0 && klh_rd32(dnd + 4) == s &&
                        klh_data((void *)(DWORD_PTR)(dnd + 0x14), &b->lie_tick, 4, "an AI heister's down-not-dead: the tick he lies until (BotsLie)") && kld.log >= 2)
                        klog("down: bots: record %d: he lies until tick %ld (BotsLie=%.1f; the game had %ld)", i, (long)b->lie_tick, kld_bk.lie, (long)cur);
                }
                /* BotsFree: no hit costs him for the first seconds of the down */
                if (kld_bk.freet > 0 && sn.veh < 5 && (long)(tick - b->tick_down) < (long)(kld_bk.freet * 1024.0f)) kld_bot_shield(b, 1);
                else if (b->shield) kld_bot_shield(b, 0);
            } else {
                /* BotsMax: the game's own limit is one down a life (c). He may go down again while he has downs left */
                if (was && b->cnt && b->cnt < kld_bk.max && hp > 0.01f) {
                    BYTE zero = 0;
                    if (klh_data((void *)(DWORD_PTR)(r->actor + 0x5cb), &zero, 1, "an AI heister's 'was down once' byte (BotsMax)") && kld.log >= 2) klog("down: bots: record %d: the 'was down once' byte is cleared (down %u of %d)", i, b->cnt, kld_bk.max);
                    was = 0;
                }
                /* Bots: the squad's modifier as its SquadModifierBehaviour would write 'force' (0x8035d5) */
                if (kld_bk.force && mod == 0) {
                    DWORD one = 1;
                    if (klh_data((void *)(DWORD_PTR)(s + 0x124), &one, 4, "an AI heister's EDownNotDeadModifier: 1 = force")) {
                        b->put124 = 1; mod = 1;
                        if (kld.log) klog("down: bots: record %d: the modifier [soldier+0x124] 0 -> 1 (force: the level-wide pause and his chance no longer say no)", i);
                    }
                }
            }
        }
        b->hp = hp; b->hmax = hmax; b->age = last; b->chance = chance; b->mod = mod; b->ws = ws; b->as = as; b->holder = holder; b->seat = seat; b->seat18 = seat18; b->seat40 = seat40; b->att = att; b->attvt = attvt; b->inv = inv; b->was = was;
    }
    kld_kw = kw; kld_kwok = kwok;
}

static void kld_tick(int game_thread)
{
    static DWORD toldrules; static char toldwhy[200];
    DWORD gd, pl, d, m, h, ho = 0, rules, state, now, tick = 0, clock, chans; int level, act, ok = 1, hpok, i = 0, st = -1;
    BYTE idx = 0xff, police = 0, flag = 0, btn = 0; DWORD ds = 0, ms = 0; float hp = 0, max = 0, pos[3] = { 0, 0, 0 }, dt = 0; char why[200];
    if ((!kld.on && !kld_bk.on) || !klh_exe_ok) return;
    if (!game_thread) return;                  /* every write here is a live object of the round: only between two frames of the game.
                                                  The mash is counted by frames too: nothing of this part runs on the fallback thread */
    now = GetTickCount();
    act = klr_arcade(&rules, &state, &level);
    if (act) {
        act = klb_level(why);                  /* asked every pass: the verdict changes when the archive is opened */
        if (rules != toldrules || strcmp(why, toldwhy)) {
            toldrules = rules; strcpy(toldwhy, why);
            klog("down: %s: %s", why, !act ? "nothing is written here (the part acts only on a level that is not stock)" :
                 !kld.on ? (kld_bk.dry ? "Enable=0, Bots=1, BotsDry=1 - only the AI heisters' part runs this round, and it only logs" : "Enable=0, Bots=1 - only the AI heisters' part acts on this round") :
                 kld.dry ? "Dry=1 - the part only logs this round" : "the part acts on this round");
        }
    }
    kld_bots(act, now);                        /* the AI heisters: whatever the human is (alive, dead, police) */
    if (!kld.on) return;
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
        } else if (ds == 1 && kld_s.dstate == 2) {
            kld_s.t_lie = now;
            if (kld.log) {                                           /* track R3: WHICH clips - the lying one is the channel the movement holds now, if it holds one */
                DWORD lm = klh_rd32(d + 0xc), lc = lm ? klh_rd32(lm + 0x8cc) : 0, ma = 0, mv = 0; int a1, a2, a3; DWORD a4; char ln[96];
                ln[0] = 0; if (lc) kld_clipfacts(lc, &a1, &a2, &a4, &a3, ln, sizeof ln);
                kld_mask(pl, &ma, &mv);                              /* the game's own 2 -> 1 has taken the fall's bits off (0x8ee31e): the control for review3 M1 */
                klog("down: lying after %.2f s (he can crawl and shoot; one press of the game's GET UP button starts the get-up); the movement's clip word [M+0x8cc] is %08lx '%s'; the input mask %08lx holds %08lx (bits 0x11 = the fall's: off here in stock)", (now - kld_s.t_down) / 1000.0f, lc, ln, ma, mv);
            }
        }
        else if (ds == 3) kld_s.t_up = now;
        else if (ds == 0) {
            if (kld_s.dead) { if (kld.log) klog("down: the down state of the man who died in it is cleared %.2f s after he went down (a new round, a reset): not an UP", (now - kld_s.t_down) / 1000.0f); }
            else if (kld_s.up && (!ok || hp <= 0.01f))                    /* a death clears D too (0x88a990): that is not an 'UP' (review S4) */
                klog("down: DEAD WHILE GETTING UP: %.2f s on the floor, %.2f s into the get-up (frame %.1f of %.1f), %d press(es), mean speed %.2f; he had %.1f health when the get-up began",
                     (now - kld_s.t_down) / 1000.0f, (now - kld_s.t_up) / 1000.0f, kld_s.lastf, kld_s.endf, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, kld_s.hp_up);
            else if (kld_s.up) klog("down: UP after %.2f s on the floor, the get-up took %.2f s (stock: 0.80; from [D+4] = 3, a press late in the fall counts the rest of the fall in), %d press(es) in it, mean speed %.2f, %.1f health lost in it (%.1f -> %.1f)%s%s",
                               (now - kld_s.t_down) / 1000.0f, (now - kld_s.t_up) / 1000.0f, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, kld_s.hp_up - hp, kld_s.hp_up, hp,
                               kld_s.capped ? "; ENDED BY THE TIME BOUND, not by the clip (its frame stood still or ran behind: say so to the lead)" : "", kld.dry ? " (Dry=1: the game's own 1.00 was played)" : "");
            else if (kld.flop == 1 && kld_s.fnow && kld_s.fdone == 1 && hp > 0.01f) {
                DWORD ma = 0, mv = 0; int mk = kld_mask(pl, &ma, &mv);      /* review3 M1: he must stand UNMASKED */
                klog("down: flop: UP after %.2f s: the dive took %.2f s, lying and rising %.2f s, %d press(es) in it, mean speed %.2f; health %.1f (%.1f at the landing); the input mask %08lx holds %08lx%s",
                     (now - kld_s.t_down) / 1000.0f, ((kld_s.t_land ? kld_s.t_land : now) - kld_s.t_down) / 1000.0f, kld_s.t_land ? (now - kld_s.t_land) / 1000.0f : 0.0f, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, hp, kld_s.hp_up,
                     ma, mv, !mk ? " (no input object)" : (mv & KLD_MASK_FALL) ? " - THE FALL'S BITS (0x11) ARE SET ON A MAN WHO IS UP: he cannot do what the fall forbade; say so to the lead (nothing more is written)" : " (the fall's bits 0x11 are off)");
            }
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
                if ((kld_s.up || kld_s.fdone == 1) && !kld.dry && kld.uppct > 0 && ho && hp < max * kld.uppct / 100.0f) {
                    float nh = max * kld.uppct / 100.0f;
                    if (klh_data((void *)(DWORD_PTR)(ho + 4), &nh, 4, "the local player's health: what a man who got up from the flop is given"))
                        klog("down: flop: up with %.1f of %.1f health (FlopUpPct=%.0f; he had %.1f) - an NPC that gets up from its own down state is given 75 %% (0x5f4d2c)", nh, max, kld.uppct, hp);
                }
            }
            kld_drop();
        }
        kld_s.dstate = ds;
    }
    if (btn && !kld_s.btn && (kld_s.up || (kld.flop == 1 && kld_s.fnow && kld_s.t_land && !kld_s.fdone))) { kld_s.meter += 1.0f; kld_s.presses++; }
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
    if (kld.flop == 1 && ds != 0) kld_flop_one(pl, d, ds, now, hp);
    else if (kld.flop && ds != 0) kld_flop_down(pl, d, ho, ds, now, &hp, max, hpok);
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
            if (kld.log) { int a1, a2, a3; DWORD a4; char gn[96]; kld_clipfacts(clip, &a1, &a2, &a4, &a3, gn, sizeof gn); klog("down: the get-up's clip %08lx is '%s' (%d frames, %d event(s))", clip, gn, a1, a2); }
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
    /* Flop: 1 = Dog Days' own knock-down, one clip (track R3: the owner's pictures); 2 = track R2's pair (a death clip
       + the rise from the stomach); anything else = off. Mode 1's numbers drive the clip from the landing to its end
       (Hero_Torso_Back: 140 frames = 5.6 s at speed 1); mode 2's the 202-frame get-up. All GUESSES for the owner's eyes */
    kld.flop = GetPrivateProfileIntA("Down", "Flop", 0, klh_ini);
    if (kld.flop != 1 && kld.flop != 2) kld.flop = 0;
    kld.belly = GetPrivateProfileIntA("Down", "FlopBelly", 1, klh_ini) != 0;
    {
        const char *fall = kld.flop == 2 ? "/Damage/Death/Die_Forward" : "/Damage/Wounded/Hero_Torso_F";
        float b0 = kld.flop == 2 ? 1.5f : 0.8f, p0 = kld.flop == 2 ? 0.6f : 0.5f, t0 = kld.flop == 2 ? 5.0f : 3.5f;
        kld.fbase = kld_inif("FlopBase", "-1"); kld.fper = kld_inif("FlopPerPress", "-1"); kld.ftop = kld_inif("FlopTop", "-1");
        kld.take = kld_inif("FlopTake", "1.0"); kld.uppct = kld_inif("FlopUpPct", "0");
        if (!kld_fin(kld.fbase) || kld.fbase < 0.25f || kld.fbase > 6.0f) kld.fbase = b0;    /* under 0.25 a clip of 200 frames would take over 32 s */
        if (!kld_fin(kld.ftop) || kld.ftop < kld.fbase || kld.ftop > 10.0f) kld.ftop = kld.fbase > t0 ? kld.fbase : t0;
        if (!kld_fin(kld.fper) || kld.fper < 0 || kld.fper > 10.0f) kld.fper = p0;
        if (!kld_fin(kld.take) || kld.take < 0 || kld.take > 1.0f) kld.take = 1.0f;
        if (!kld_fin(kld.uppct) || kld.uppct < 0 || kld.uppct > 100.0f) kld.uppct = 0;
        GetPrivateProfileStringA("Down", "FlopFallSlot", fall, kld.fallslot, sizeof kld.fallslot, klh_ini);
        GetPrivateProfileStringA("Down", "FlopUpSlot", "/Movement/Rise/Rise_From_Stomach", kld.upslot, sizeof kld.upslot, klh_ini);
        if (kld.fallslot[0] != '/') strcpy(kld.fallslot, fall);
        if (kld.upslot[0] != '/') strcpy(kld.upslot, "/Movement/Rise/Rise_From_Stomach");
    }
    t[0] = 0;
    for (k = 0; k < KLD_NT; k++) {
        kld.want[k] = -1.0f;
        v = kld_inif(kld_t[k].key, "-1");
        if (kld_fin(v) && v >= kld_t[k].lo && v <= kld_t[k].hi) { kld.want[k] = v; kld.anykey = 1; if (n < (int)sizeof t - 32) n += snprintf(t + n, sizeof t - n, " %s=%.1f", kld_t[k].key, v); }
        else if (kld_fin(v) && v >= 0 && kld.on) klog("down: %s=%.2f is outside %.1f .. %.1f (%s): the game's own number stays", kld_t[k].key, v, kld_t[k].lo, kld_t[k].hi, kld_t[k].what);
    }
    if (kld.on) klog("down: on%s; the get-up is played at Base %.2f + PerPress %.2f x the mash meter (one a press of the game's own GET UP button, - Decay %.1f a second), at most Top %.2f; the trigger:%s; Log=%d. Arcade on a level that is not stock, not for a police player; data writes only (re\\player_down.md)",
                     kld.dry ? " (Dry=1: NOTHING is written, the log says what would be)" : "", kld.base, kld.per, kld.decay, kld.top, n ? t : " the game's own (no key set)", kld.log);
    /* the AI heisters (track R4): its own switch - works with Enable=0 too */
    memset(kld_b, 0, sizeof kld_b); kld_brules = 0; kld_nearput = 0;
    kld_bk.on = GetPrivateProfileIntA("Down", "Bots", 0, klh_ini) != 0;
    kld_bk.dry = GetPrivateProfileIntA("Down", "BotsDry", 0, klh_ini) != 0;
    kld_bk.force = GetPrivateProfileIntA("Down", "BotsForce", 1, klh_ini) != 0;
    kld_bk.max = (int)GetPrivateProfileIntA("Down", "BotsMax", 2, klh_ini);       /* 2: the task's GUESS; the game's own is 1 */
    if (kld_bk.max < 1) kld_bk.max = 1; if (kld_bk.max > 20) kld_bk.max = 20;
    kld_bk.lie = kld_inif("BotsLie", "0"); kld_bk.freet = kld_inif("BotsFree", "0.75"); kld_bk.uppct = kld_inif("BotsUpPct", "0"); kld_bk.near_ = kld_inif("BotsNear", "-1");
    if (!kld_fin(kld_bk.lie) || kld_bk.lie < 0.5f || kld_bk.lie > 15.0f) kld_bk.lie = 0;      /* 15 s: klescort.c's BoardAll takes a bot that stood 15 s for 'held' */
    if (!kld_fin(kld_bk.freet) || kld_bk.freet < 0 || kld_bk.freet > 15.0f) kld_bk.freet = 0.75f;
    if (!kld_fin(kld_bk.uppct) || kld_bk.uppct < 1 || kld_bk.uppct > 100.0f) kld_bk.uppct = 0;
    if (!kld_fin(kld_bk.near_) || kld_bk.near_ < 0 || kld_bk.near_ > 100000.0f) kld_bk.near_ = -1.0f;
    if (kld_bk.on) klog("down: bots: on%s - the AI heisters' 'down, not dead' by the game's own NPC rule (0x70e0e0; NOT SHOWN that it makes one go down: only tests f / g are taken away, a .. e stay the game's): BotsForce=%d (1 = each one's modifier [soldier+0x124] 0 -> 1: the level-wide pause and his 50 %% chance no longer refuse), BotsMax=%d downs a bot a round (the game's own: 1), BotsLie=%.1f s (0 = the game's 1.5 .. 3.0), BotsFree=%.2f s without damage from the down's start, BotsUpPct=%.0f (0 = the game's 75), BotsNear=%.0f (-1 = [T+0x5c] not written). Arcade, a level that is not stock, the round running; data writes only (re\\player_down.md 11)",
                        kld.dry || kld_bk.dry ? " (Dry: NOTHING is written; every AI heister's death prints the readable inputs of the game's test and his place)" : "", kld_bk.force, kld_bk.max, kld_bk.lie, kld_bk.freet, kld_bk.uppct, kld_bk.near_);
    if (kld.on && kld.flop == 1) klog("down: flop: Flop=1 - DOG DAYS' OWN KNOCK-DOWN, ONE CLIP: he goes down by %s (thrown down, lying, up over a knee: the whole clip is played in the game's fall; no press cuts it, no hit of it costs), from the landing on at FlopBase %.2f + FlopPerPress %.2f x the mash meter, at most FlopTop %.2f; FlopBelly=%d (1 = every draw of the slot is the clip thrown forward, onto the belly); FlopUpPct=%.0f (health he is given when up; 0 = none). Flop=2 = the earlier pair (a death clip + the rise from the stomach)",
                                      kld.fallslot, kld.fbase, kld.fper, kld.ftop, kld.belly, kld.uppct);
    if (kld.on && kld.flop == 2) klog("down: flop: Flop=2 - THE BELLY FLOP, two clips: he goes down by %s and gets up by %s (slot ids written into his prone movement while he is up; the game plays them itself), the get-up at FlopBase %.2f + FlopPerPress %.2f x the meter, at most FlopTop %.2f; FlopTake=%.2f (the share of a loss in the get-up that stays), FlopUpPct=%.0f (health he is given when up; 0 = none)",
                                 kld.fallslot, kld.upslot, kld.fbase, kld.fper, kld.ftop, kld.take, kld.uppct);
}

#endif /* KLDOWN_C */
