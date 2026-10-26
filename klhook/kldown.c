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
 * ALL THE BELLY FALLS, A DIFFERENT ONE EACH TIME ([Down] Flop=3; default 0; track R6, re\player_down.md 12)
 *   The owner on the picture sheet G_zoom_belly.png: 'i think zoom belly is it' and 'but i like having them all they are
 *   all nice'. Flop=3 = Flop=1's whole machine (one whole clip in the game's fall, the mash from its landing, the end by
 *   movement state 5, the input mask, the bounds, the dead-man test, Dry) with the clip DRAWN BY THE HOOK from a list:
 *   kld_md[] - sheet numbers 41 (= 7 = 13), 12 (= 9), 10, 25, 42 and the stumble 43 (FlopMix = weights, FlopLight).
 *   HOW A CHOSEN CLIP IS PLAYED WITHOUT TOUCHING A BOT'S DRAW. The three fall words name the CARRIER slot
 *   /Damage/Wounded/Running/Torso/Merc_Back (FlopCarrier): in every set of F01, F07 and the five tab builds its list
 *   is ONE pair with condition word 0 = no draw. The clip NUMBER of that one pair, in the HUMAN's set, is rewritten to
 *   the chosen clip's (clip records are global: [[0x1546f6c]] + number x 0x68). The slot is an NPC death word
 *   (ZWounded 0x865180, 'Merc' x running x shot in the back): nothing plays it for a ZFFPlayer, and the AI heisters wear
 *   OTHER sets (Kane_NPC / Lynch_NPC: their own lists), so no bot's 60 / 20 / 20 draw of
 *   /Damage/Impact/FB/Running/Front_Torso and no death of anybody changes - the pairs the clips are FOUND in are only
 *   read. A body whose set has a list for /Damage/Hit/Front/Front (only the NPC sets have one: file) is refused.
 *   WHEN THE NEXT ONE IS WRITTEN (the game reads the list when the fall STARTS, 0x5d6060): in the pass that checks a
 *   player object (a new round, another level, a body swap) and in the pass that sees the down state back at 0 - the
 *   same pass, before the game's next frame. The check writes the first choice BEFORE the fall words are written in
 *   the same pass (kld_tick: kld_mix_check, then kld_flop_words), so the words never name the carrier while its pair
 *   holds a clip the list left out (the set's own #12 under a FlopMix / FlopReach without it) - that order is what
 *   makes 'whatever the pair holds is a clip of the list' true; a pair write that FAILS ends the list on that body
 *   (review6 S3). A fall that starts between two choices plays the last one, and it is identified by the clip the
 *   movement really plays ([M+0x8cc]), never by what was written. Never the same group twice in a row.
 *   #43 never lies: no mash, no speed write; the knock is over when the clip is (2.1 s, all of it free of damage).
 *   FlopReach (metres; DEFAULT 1.0 = ONLY #25 - review6 M1: the long dives are out until live checks W1 / W2 have
 *   shown them safe; the owner's 'all' is FlopReach=4.5): a clip whose own root goes further forward is left out. READ
 *   (re\climb.md 3): these clips have record flag 0x40, so the game's 'moved by animation' movement carries him and
 *   runs its physics step - the Havok character proxy - while his collision is on, and the prone start does not
 *   switch it off (LIVE: G1's Hero_Torso_Back; review6: prone slot 13, 0x7e4bc0, calls collision ON): a wall stops
 *   him like any step of his; an EDGE does not (ASSUMED: he goes over it as when he walks). The hook cannot test the
 *   way: live checks W1 / W2 of section 12 decide.
 *   THE GAME'S ALIGNMENT (review6 M2): when [D+0xf4] is set - it was in G1, in the open - the fall is aligned to the
 *   place at D+0x11c at frame 0.3 x (N - 1), which cancels the clip's travel up to there: 78 - 96 % of the long
 *   dives' (41 keeps 0.68 m, 12 0.12, 10 0.47, 42 0.75; the stumble 43 keeps 2.83 of 4.05). So a dive may be played
 *   ON THE SPOT or carried to the align place - NOT what the sheet shows - and 'he ended short' proves no wall. The
 *   KNOCK-DOWN lines print the collision byte and count, the align place, heading and what is expected; the UP line
 *   judges against that. Whether the owner gets the falls OF THE SHEET is live check L1's pictures to say.
 *   FIX ROUND (re\player_down_review6.md, applied): M1, M2 above; S3 a pair write that fails ends the list on that
 *   body; S4 the last sets' own carrier numbers are remembered (a body swap A -> B -> A); S5 the fall / get-up words
 *   are put back by what was WRITTEN (kld_s.fwf / fwu), not by the current ids.
 *   FlopUp=71 (default off): at the clip's event 8, when he lies on the belly there, the game's own 'get-up asked'
 *   byte [D+0x21] is set (Flop=2's path) and the get-up words hold /Movement/Rise/Rise_From_Stomach: the upright
 *   kneel of the owner's picture 2. COST: the get-up state takes FULL damage (the fall is free), and it is longer.
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
 *   - (DONE by track R7, [Down] Prompt: the game's own 'Tap Quickly' element, by data - the block before kld_tick_main.)
 *     The game's own GET UP prompt (user action 0xc / 0xd, offered by 0x5505c0 while [D+0x2c]) shows only while he
 *     LIES the stock way
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
 *   down: flop: list: sheet #n = clip N ... : IN / is OUT: <why>       Flop=3, once per player object and set (Dry too)
 *   down: flop: the carrier is <slot> = slot n, ONE pair {0, clip N} ...
 *   down: flop: the NEXT knock-down is clip N '...' (sheet #n) ... - <when>      the choice, when it is written
 *   down: flop: THE KNOCK-DOWN: clip N '...' (sheet #n), drawn a of b ...        Flop=3: which clip this fall plays
 *   down: flop: THE GAME ALIGNS THIS FALL ([D+0xf4]) to the place ..., heading, what is expected / does NOT align this fall
 *   down: flop: he stands x m from where he went down (by his node) ...; the clip alone goes y m; expected z m; collision
 *   down: flop: FlopUp: he lies ...: the get-up ... is asked for
 *   down: camera: Camera=.. CameraSide=.. prompt: Prompt=.. ...       at start (track R7)
 *   down: camera: the fall's LOOK bit of the input mask a is taken off t s after he went down: v -> w
 *   down: camera: the down start had put the camera on the LEFT shoulder; the side he had is back ...
 *   down: prompt: ON t s after he went down: the game's own tap prompt (ZMiniGameButtonMashingDisplay e ...)
 *   down: prompt: OFF after t s (<why>) / NOT SHOWN in this down: <why> / the game shows its own tap prompt ...
 *   down: rules: NoFire=.. Vulnerable=.. DownFromCop=.. DownFromCrew=..        at start (track R8)
 *   down: rules: DownPointBlank=.. CooldownCredit=.. NoThrow=..                at start (review 8's fix round)
 *   down: rules: Vulnerable: THE POINT-BLANK CAP DOES NOT / CANNOT STAND ...    once a down: hits stay swallowed, why
 *   down: rules: CooldownCredit: ... [D+0x38] a -> b s                          when he is up
 *   down: rules: NoThrow: the throw button was down ...                         a TEST key
 *   down: rules: NoFire: the input mask a: v -> w ... / off (<why>): v -> w    bits 0x400 / 0x200 set while he is down, taken off after
 *   down: rules: ... the damage table of Arcade level L holds police -> you a (x f ...) and crew -> you b ...   the factors stand
 *   down: rules: THE FACTORS DO NOT STAND ...                           1 s into a down without them (says why)
 *   down: rules: Vulnerable: ... switch [0xceb40c] 1 -> 0 ... EVERY HIT COSTS / ... is back at 1 after t s (<why>)
 *   down: rules: he lost x on the floor ...; the last BULLET's attacker ... is POLICE / an AI HEISTER ...      the first 8 a down (Log=2: all)
 *   down: rules: this knock-down is over after t s (<why>): n loss(es), x in all; hits could cost for y s; fire was masked
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
#define KLD_ONE        (kld.flop == 1 || kld.flop == 3)      /* one whole clip in the game's fall (kld_flop_one); 3 = the hook draws it from a list */
#define KLD_KEEPUP     (kld.flop == 1 || (kld.flop == 3 && kld_s.idu < 0))      /* the three get-up words stay the game's */

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
    int fmi; float p0[3];                      /* Flop=3: the list entry the fall plays (-1 = none); his feet when he went down */
    /* review6 (the fix round). fwf / fwu: Flop=3 - the slot id + 1 this part WROTE into the three fall / get-up words
       (0 = none): what is put back goes by what was written, not by idf / idu, which a later check sets to -1 (S5).
       pn: his NODE's place when he went down (klclimb.c: the floats at +0x460 stay at the navigation mesh's edge);
       fal / fap / fad: the game aligned this fall, to that place, that far from his feet (M2) */
    int fwf, fwu, pnok, fal; float pn[3], fap[3], fad;
} kld_s;

/* track R7 (the camera stays his; the game's own tap prompt - the block before kld_tick_main has the reading) */
static struct {
    int cam, side, prompt, style, pulse;     /* the keys: Camera, CameraSide, Prompt, PromptStyle, PromptPulse */
    int act; DWORD pl; float rate;           /* from kld_tick_main, this pass: the part acts for this local player; the clip speed last set */
    BYTE side0; int sidehave, lookn, siden, sidetold;      /* the camera: the side he had while up; writes in this down */
    DWORD elem; int ours, presses, refused; DWORD t_press, gtick, t_gtick, t_on;      /* the prompt */
    /* review 7: state = the session state of this pass ([session+0x70], from klr_arcade; S1); waswant = the prompt was
       wanted in the last pass (the pause test starts afresh, S7); t_lost = since when no player answers for a prompt
       that is still ours (S2); sidearm = a delayed side change was seen armed in this down (S5) */
    DWORD state, t_lost; int waswant, sidearm;
} kld_v;

/* track R8 (while knocked down: no shooting, not invulnerable, police hurt him little and heisters in full - the
   block before kld_tick_main has the reading). Declared here: kld_flop_one leaves its heartbeat in it. */
static struct {
    int nofire, hurt; float cop, crew;       /* the keys: NoFire (0 / 1 fire + aim / 2 fire only), Vulnerable, DownFromCop, DownFromCrew */
    DWORD pass, beat;                        /* kld_tick's pass counter; the pass in which kld_flop_one last wrote the fall's two ticks */
    int level;                               /* the Arcade level of this pass (kld_tick_main, from klr_arcade) */
    /* NoFire: the mask bits THIS part set, on which player object and at which address */
    DWORD mpl, mat, mbits, t_mlost; int mn, mtold;
    /* the factors: fon = wanted this pass (kld_factor answers by it); the table's two floats as they stood while he
       was up (police -> you +8, crew -> you +0x10 of the level's record); stand = the table holds them x the factors */
    int fon, stand, standtold, uphave, unverified; DWORD upR, t_fon, t_foff; float up[2];
    struct { DWORD at; float old, put; } w[2];      /* what this part wrote itself (only when klbalance.c does not own the table) */
    /* Vulnerable: sw = the game's 'down not dead' switch [0xceb40c] is 0 by this part's write */
    int sw, swn, swtold; DWORD t_sw, ms_hurt;
    /* the log of one knock-down */
    int was; DWORD t0; float hp0, hplast, lost; int nloss, nline;
    /* review 8. pb = DownPointBlank (how many bullets one point-blank step on him is worth while he is down; < 0 = the
       step is left alone); pbon = wanted this pass (kld_pb answers by it); npb = steps capped in this down (counted
       on whatever thread the soldier scripts run); pbtold = the 'cap does not stand' line of this down.
       cdfix = CooldownCredit; nothrow = NoThrow (a TEST key), nthrow = its writes in this down */
    float pb; volatile LONG pbon, npb; int pbtold;
    int cdfix, nothrow, nthrow;
} kld_r;

/* Flop=3 (track R6): the falls of the owner's sheet G_zoom_belly.png that throw a living man down and bring him up.
   sheet = the overview's number; group = clips with (nearly) the same keys - never two of one group in a row; slot /
   clip = where the clip is FOUND in this body's set (the slot's pairs are only read) and its name after '#';
   light = he never lies (no mash; over when the clip is); upcut = at its event 8 he lies chest down (FILE: the
   sheet's measured 'pose:' ranges), so FlopUp may cut there; w = the default weight (FlopMix).
   FILE (F07's table = the five tab builds'): frames / events / root forward -
     41 Running_torso_Front_3 216 fr, 7@43 31@43 8@72, 3.01 m (ends STANDING; 7 and 13 are the same dive, 206 fr,
        2.49 m, and end bent: 41 is the default of the group)        12 = 9 ..._Back_03 239 fr, 31@7 7@55 8@115, 3.28 m
     10 Run_Torso_Back_02 140 fr, 31@17 7@46 8@80, 3.41 m (a passing kneel)   25 Hero_Torso_Back 186 fr, 31@1 0@39
        7@46 8@116, 0.66 m        42 Running_Torso_Front_2 219 fr, 7@53 31@53 8@119, 3.63 m (back, side, belly)
     43 Run_Torso_Impact 53 fr, 31@18 7@47, no 8, 4.05 m (a stumble; he stays up)
   Of these events the game's clip-event routine 0x637060 acts only on 31 (the weapon item, case 0x637147); 0, 7, 8 go
   to 'nothing' (R5: its two tables). LIVE (G1, 2026-10-11 16:18): the prone fall's channel has NO event queue, so no
   event of the clip reaches an action at all - the KNOCK-DOWN line prints the queue every time.
   after (review6 M2; FILE, the review's reading of the GROUND keys - a number of the FILE, not read in the game):
   metres of forward travel the clip has LEFT after frame 0.3 x (N - 1), where the game's AlignTo has put him at the
   align place when it aligns the fall ([D+0xf4]) - all that is the clip's own of an aligned dive.
   Record flags (review6 S1 / S2; FILE): all nine have 0x40 ('moved by animation'); 7, 9 and 25 are 10c0, the other
   six c0. Bit 0x1000 = the record has four vectors at +0x30 .. +0x5c that 0x8b4200 reads (stock: Down_Not_Dead_Get_Down
   has them, ..._No_Weapon has not - that they are WEAPON data is a GUESS). #25 is the only clip seen on the player. */
#define KLD_NMIX 9
static const struct { int sheet, group; const char *slot, *clip; int light, upcut; float w, after; } kld_md[KLD_NMIX] = {
    { 41, 1, "/Damage/Impact/FB/Running/Front_Torso",       "Running_torso_Front_3",    0, 1, 2.0f, 0.68f },
    {  7, 1, "/Damage/Wounded/Running/Torso/Front_01",      "Run_Torso_Front_03",       0, 1, 0.0f, 0.16f },
    { 13, 1, "/Damage/Wounded/Running/Torso/Merc_Front",    "Merc_Run_Torso_Front_03",  0, 1, 0.0f, 0.16f },
    { 12, 2, "/Damage/Wounded/Running/Torso/Merc_Back",     "Merc_Run_Torso_Back_03",   0, 1, 2.0f, 0.12f },
    {  9, 2, "/Damage/Wounded/Running/Torso/Back_01",       "Run_Torso_Back_03",        0, 1, 0.0f, 0.12f },
    { 10, 3, "/Damage/Wounded/Running/Torso/Back_01",       "Run_Torso_Back_02",        0, 1, 1.0f, 0.47f },
    { 25, 4, "/Damage/Wounded/Hero_Torso_F",                "Hero_Torso_Back",          0, 1, 1.0f, 0.10f },
    { 42, 5, "/Damage/Impact/FB/Running/Front_Torso",       "Running_Torso_Front_2",    0, 0, 1.0f, 0.75f },      /* at its event 8 (119) he lies on his SIDE (40 - 135): no cut */
    { 43, 6, "/Damage/Impact/FB/Running/Front_Torso",       "Run_Torso_Impact",         1, 0, 1.0f, 2.83f },      /* the lead's GUESS: the rare 'nearly went down' (FlopLight) */
};
static struct {
    float w[KLD_NMIX], reach; int light, up;   /* the keys: FlopMix, FlopReach (metres; 0 = no limit), FlopLight, FlopUp=71 */
    int n, next, lastgroup, played, drawn[KLD_NMIX];      /* entries found on this body; the entry written for the next fall; counters of the process */
    struct { int def, frames, f7, f8; DWORD num, rec; float fwd; } e[KLD_NMIX];
} kld_mx;
static struct { DWORD at, old, put, pool; int have; } kld_cx;      /* the carrier's one pair: the address of its clip number, what the level had, what stands there now */
/* review6 S4: a body swap A -> B -> A. When A's pair could not be put back (nobody wore A's set any more) it keeps the
   last choice, and a later check of A would take that number for 'the level's own' and lose #12. So the last sets'
   {pair address, pool, the level's own number, what this part left there} are kept, WITH THE TWO CLIPS' NAMES: an entry
   is believed only while the pair reads {0, put} and both numbers still name those clips (another level at the same
   address reads otherwise and the entry is dropped). */
#define KLD_NCM 4
static struct { DWORD at, pool, old, put; char oldname[96], putname[96]; } kld_cm[KLD_NCM];
static int kld_cmi;
static DWORD kld_rng;

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
/* [Down] Floor=1 (2026-10-19, owner run 13:23:03: killed from 3 % by two hits in 4 s, no knock-down - the game's rule wants
   <= HealthPct AND a burst of Burst x MinHit hits inside Window, and the second hit came too late for it). The hook cannot
   see a hit before the game applies it (0x8da3b0 / 0x458e7f run inside the game's frame; no code byte is patched here), so
   the floor is the same thing the keys do, done in time: WHILE he is up, off cooldown and at or under FloorPct per cent of
   his maximum, the game's own three trigger numbers are written to 'any hit floors him' (HealthPct 100, Burst 1, MinHit 1)
   and put back the moment he is down, above the line or the part stops acting. The game's rule then runs unchanged and
   gives him at least DownHealth, as for any knock-down. kld_fl.armed is read by kld_tuning(). */
static struct { DWORD pl; int armed, was; float hp; DWORD t_arm, last; } kld_fl;
static int kld_floor_on; static float kld_floor_pct;

static void kld_tuning(int act, float max)      /* max: the player's maximum health, 0 = not known this pass */
{
    DWORD tun = klh_rd32((DWORD_PTR)KLH_VA(KLD_TUNING)); float cur[KLD_NT]; int k, ok = 1, n = 0; char a[200], b[200]; int na = 0, nb = 0;
    if (!kld.anykey && !kld_floor_on) return;
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
        if (act && kld_fl.armed && k <= 2) want = k == 0 ? 100.0f : 1.0f;      /* Floor: HealthPct, Burst, MinHit (GUESS: the low-health variant [T+0x27c] x MinHit = 4 x 1 is left as built) */
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
    kld_s.fmi = -1; kld_s.fal = 0; kld_s.fad = -1.0f;
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
        if (KLD_ONE && (e == 7 || e == 8 || e == 31)) continue;      /* Flop=1: what the stock game's own clips of this family carry, and it plays them ON THE HUMAN itself:
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

/* ---- Flop=3: the list (track R6) ------------------------------------------------------------------------------- */

/* The address of a slot's pair list in this body's set (kld_list's lookup; reads only). -> 0 = none / not readable */
static DWORD kld_listat(DWORD pl, int id, DWORD *recs, DWORD *cnt)
{
    DWORD pool = klh_rd32(pl + 0x78), tab = klh_rd32(pl + 0x7c), n = 0, off = 0xffffffff, mgr;
    *recs = 0; *cnt = 0;
    if (id < 0 || !pool || !tab || !klh_rd(tab, &n, 4) || n > 60000 || (DWORD)id >= n || !klh_rd(tab + 4 + 4 * (DWORD)id, &off, 4) || off == 0xffffffff) return 0;
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLD_ANIM))) || !(*recs = klh_rd32(mgr)) || !klh_rd(mgr + 4, cnt, 4)) return 0;
    return pool + off;
}

/* every event of a clip as 'id@frame,...' (the table as kld_badevent reads it) */
static void kld_evtext(DWORD clip, char *t, int cap)
{
    BYTE r[0x30], ev[8]; DWORD mgr, base; short n, i; int k = 0;
    snprintf(t, cap, "?");
    if (!clip || !klh_rd(clip, r, sizeof r)) return;
    n = *(short *)(r + 6);
    if (!n) { snprintf(t, cap, "none"); return; }
    if (n < 0 || n >= 64 || !(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLD_ANIM))) || !(base = klh_rd32(mgr + 0x10))) return;
    t[0] = 0;
    for (i = 0; i < n && k < cap - 16; i++) {
        if (!klh_rd(base + *(DWORD *)(r + 0x10) + 8 * i, ev, 8)) break;
        k += snprintf(t + k, cap - k, "%s%lu@%u", i ? "," : "", *(DWORD *)ev, (unsigned)*(WORD *)(ev + 4));
    }
}

static int kld_mix_find(DWORD clip)
{
    int i;
    for (i = 0; i < kld_mx.n; i++) if (kld_mx.e[i].rec == clip) return i;
    return -1;
}

/* The carrier's pair gets the level's own clip number back - only while a live player wears that pool and the pair
   reads {condition word 0, the number this part put} (kld_flop_belly's rule, review3 S1). Game thread only. */
static int kld_cm_find(DWORD at, DWORD pool)
{
    int i;
    for (i = 0; i < KLD_NCM; i++) if (kld_cm[i].at && kld_cm[i].at == at && kld_cm[i].pool == pool) return i;
    return -1;
}

/* review6 S4: what the carrier's pair holds now against the level's own, remembered (or forgotten when they are the
   same). Called after every write of the pair. Reads only. */
static void kld_cm_keep(void)
{
    DWORD mgr, recs = 0, cnt = 0, a4; int i = kld_cm_find(kld_cx.at, kld_cx.pool), a1, a2, a3;
    if (!kld_cx.have) return;
    if (kld_cx.put == kld_cx.old) { if (i >= 0) kld_cm[i].at = 0; return; }
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLD_ANIM))) || !(recs = klh_rd32(mgr)) || !klh_rd(mgr + 4, &cnt, 4) || kld_cx.old >= cnt || kld_cx.put >= cnt) { if (i >= 0) kld_cm[i].at = 0; return; }
    if (i < 0) { i = kld_cmi; kld_cmi = (kld_cmi + 1) % KLD_NCM; }
    kld_cm[i].at = kld_cx.at; kld_cm[i].pool = kld_cx.pool; kld_cm[i].old = kld_cx.old; kld_cm[i].put = kld_cx.put;
    kld_clipfacts(recs + kld_cx.old * 0x68, &a1, &a2, &a4, &a3, kld_cm[i].oldname, sizeof kld_cm[i].oldname);
    kld_clipfacts(recs + kld_cx.put * 0x68, &a1, &a2, &a4, &a3, kld_cm[i].putname, sizeof kld_cm[i].putname);
    if (!kld_cm[i].oldname[0] || !kld_cm[i].putname[0]) kld_cm[i].at = 0;      /* no name to know it again by: not remembered */
}

static void kld_mix_back(DWORD pl)
{
    DWORD pr[2] = { 1, 0 }; int i;
    if (!kld_cx.have) return;
    kld_cx.have = 0;
    if (kld_cx.put == kld_cx.old) return;
    if (kld_pool_live(pl, kld_cx.pool) && klh_rd(kld_cx.at - 4, pr, 8) && pr[0] == 0 && pr[1] == kld_cx.put) {
        if (klh_data((void *)(DWORD_PTR)kld_cx.at, &kld_cx.old, 4, "the animation set: the carrier pair's clip number, back as the level had it")) {
            klog("down: flop: the carrier pair of %s holds its own clip %lu again (it held %lu)", kld.fallslot, kld_cx.old, kld_cx.put);
            if ((i = kld_cm_find(kld_cx.at, kld_cx.pool)) >= 0) kld_cm[i].at = 0;
        }
    } else klog("down: flop: the carrier pair of %s (clip %lu put for %lu) is NOT put back: no player wears that animation set any more, or the pair does not read as it was left (the level's data is gone, or a body swap left the set unworn); remembered: a later check of that set takes clip %lu as its own again while the pair still reads as left", kld.fallslot, kld_cx.put, kld_cx.old, kld_cx.old);
}

/* The clip of the NEXT knock-down: one of the entries by weight, not of the group played last (unless there is no
   other), its clip number written into the carrier's pair. Called in the pass that checked the body and in the pass
   that saw the down state back at 0. Dry: said, not written. Game thread only. */
static void kld_mix_next(DWORD pl, const char *why)
{
    float sum = 0, r; int i, pick = -1, others = 0; DWORD pr[2] = { 1, 0 }, num; char name[96]; int a1, a2, a3; DWORD a4;
    if (kld.flop != 3 || !kld_s.fok || kld_mx.n <= 0 || !kld_cx.have) return;
    for (i = 0; i < kld_mx.n; i++) if (kld_md[kld_mx.e[i].def].group != kld_mx.lastgroup) others++;
    for (i = 0; i < kld_mx.n; i++) if (!others || kld_md[kld_mx.e[i].def].group != kld_mx.lastgroup) sum += kld_mx.w[kld_mx.e[i].def];
    kld_rng ^= GetTickCount() * 2654435761u; if (!kld_rng) kld_rng = 0x1234567;
    kld_rng ^= kld_rng << 13; kld_rng ^= kld_rng >> 17; kld_rng ^= kld_rng << 5;
    r = (float)(kld_rng >> 8) / 16777216.0f * sum;
    for (i = 0; i < kld_mx.n; i++) {
        if (others && kld_md[kld_mx.e[i].def].group == kld_mx.lastgroup) continue;
        pick = i;
        if ((r -= kld_mx.w[kld_mx.e[i].def]) < 0) break;
    }
    if (pick < 0) return;
    num = kld_mx.e[pick].num;
    if (!klh_rd(kld_cx.at - 4, pr, 8) || pr[0] != 0 || pr[1] != kld_cx.put) {
        klog("down: flop: the carrier pair of %s reads {%lx, %lu} and this part left {0, %lu}: not the pair any more - NO KNOCK-DOWN LIST from here on this body (the game's own fall comes back)", kld.fallslot, pr[0], pr[1], kld_cx.put);
        kld_s.fok = 0;                         /* the tick puts the fall words back; kld_mix_back finds the pair changed and leaves it */
        return;
    }
    kld_mx.next = pick;
    kld_clipfacts(kld_mx.e[pick].rec, &a1, &a2, &a4, &a3, name, sizeof name);
    if (kld.dry) { klog("down: flop: the NEXT knock-down WOULD be clip %lu '%s' (sheet #%d) - %s; Dry=1: the carrier pair keeps clip %lu", num, name, kld_md[kld_mx.e[pick].def].sheet, why, pr[1]); return; }
    if (num != pr[1] && !klh_data((void *)(DWORD_PTR)kld_cx.at, &num, 4, "the animation set: the carrier pair's clip number = the clip of the next knock-down")) {
        /* review6 S3: the pair keeps what it held - the last choice or the set's own #12, which FlopMix / FlopReach
           may have left OUT of the list. The fall words must not go on naming the carrier then: no list from here on
           (the tick puts the game's own ids back in its next pass while he is up). */
        kld_mx.next = -1; kld_s.fok = 0;
        klog("down: flop: the carrier pair of %s could not be written (it keeps clip %lu): NO KNOCK-DOWN LIST from here on this body - the fall words get the game's own ids back, the game's own fall plays", kld.fallslot, pr[1]);
        return;
    }
    kld_cx.put = num; kld_cm_keep();
    if (kld.log) klog("down: flop: the NEXT knock-down is clip %lu '%s' (sheet #%d%s), written into the one pair of %s (it held %lu; the level's own is %lu) - %s", num, name, kld_md[kld_mx.e[pick].def].sheet,
                      kld_md[kld_mx.e[pick].def].light ? ", the stumble: he stays up" : "", kld.fallslot, pr[1], kld_cx.old, why);
}

/* Once per player object and set (Flop=3): the carrier and every entry of the list, on THIS body. */
static void kld_mix_check(DWORD pl)
{
    DWORD recs = 0, cnt = 0, at, pr[2], bid, fl, c[8], cnum, own; int id, i, k, n, be, bf, fr, ev, full; char name[96], evs[96]; const char *hash; float net[3];
    kld_mix_back(pl);                          /* a check made again (a body swap): what an earlier one put into a set goes back first */
    kld_s.fchk = 1; kld_s.fok = 0; kld_s.idf = kld_s.idu = -1; kld_mx.n = 0; kld_mx.next = -1;
    kld_s.fset[0] = klh_rd32(pl + 0x78); kld_s.fset[1] = klh_rd32(pl + 0x7c); kld_s.fset[2] = klh_rd32(pl + 0x80);
    for (k = 0; k < 6; k++) kld_s.fst[k] = (WORD)klq_slot(pl, kld_stock[k]);
    /* the bots' draw: only the NPC sets have a list for /Damage/Hit/Front/Front (FILE: F01, F07, the five tab builds).
       A human in such a set would share the carrier's pair with every AI heister of that set: refused. */
    id = klq_slot(pl, "/Damage/Hit/Front/Front");
    if (id >= 0 && kld_list(pl, id, c, 8) > 0) {
        klog("down: flop: NO KNOCK-DOWN LIST on this body (player %08lx): its animation set has a clip for /Damage/Hit/Front/Front = an AI heister's set, and a pair rewritten in it would change the bots' own deaths. The game's own fall stays", pl);
        return;
    }
    id = klq_slot(pl, kld.fallslot);
    at = id >= 0 && id <= 0x7fff ? kld_listat(pl, id, &recs, &cnt) : 0;
    pr[0] = 1; pr[1] = 0;
    if (!at || !klh_rd(at, pr, 8) || pr[0] != 0 || pr[1] >= cnt) {
        klog("down: flop: NO KNOCK-DOWN LIST on this body (player %08lx): the carrier %s (slot %d) %s. The game's own fall stays", pl, kld.fallslot, id,
             !at ? "has no list in this set" : "is not a list of ONE pair with condition word 0 (a list the game draws from cannot carry a chosen clip)");
        return;
    }
    cnum = own = pr[1];
    /* review6 S4: a set this part left with a choice in its pair (a body swap away from it, nobody wore it then) and
       that is worn again: the level's own number is the remembered one, not what the pair reads. */
    if ((i = kld_cm_find(at + 4, klh_rd32(pl + 0x78))) >= 0) {
        char n1[96], n2[96];
        if (cnum == kld_cm[i].put && kld_cm[i].old < cnt && kld_clipfacts(recs + kld_cm[i].old * 0x68, &fr, &ev, &fl, &full, n1, sizeof n1) && !strcmp(n1, kld_cm[i].oldname)
            && kld_clipfacts(recs + cnum * 0x68, &fr, &ev, &fl, &full, n2, sizeof n2) && !strcmp(n2, kld_cm[i].putname)) {
            own = kld_cm[i].old;
            klog("down: flop: the carrier's pair in this set still holds clip %lu '%s', an earlier choice of this part that could not be put back (a body swap): the level's own is clip %lu '%s', as remembered", cnum, n2, own, n1);
        } else kld_cm[i].at = 0;                /* not as it was left (another level's data at that address): forgotten */
    }
    for (k = 0; k < KLD_NMIX; k++) {
        DWORD lat, rec = 0, num = 0; int sid, pair = -1; float fwd;
        if (kld_mx.w[k] <= 0) continue;
        if (kld_md[k].light && !kld_mx.light) { klog("down: flop: list: sheet #%d '%s' (the stumble: he stays up) is OUT by FlopLight=0", kld_md[k].sheet, kld_md[k].clip); continue; }
        sid = klq_slot(pl, kld_md[k].slot);
        lat = sid >= 0 ? kld_listat(pl, sid, &recs, &cnt) : 0;
        for (i = 0; lat && i < 16; i++) {
            if (!klh_rd(lat + 8 * i, pr, 8)) break;
            if (pr[1] < cnt && kld_clipfacts(recs + pr[1] * 0x68, &fr, &ev, &fl, &full, name, sizeof name) && (hash = strrchr(name, '#')) != 0 && !strcmp(hash + 1, kld_md[k].clip)) { rec = recs + pr[1] * 0x68; num = pr[1]; pair = i; break; }
            if (!pr[0]) break;
        }
        /* review6 S4: the carrier's own clip (#12) when its pair holds an earlier choice - by the remembered number */
        if (!rec && sid == id && own != cnum && own < cnt && kld_clipfacts(recs + own * 0x68, &fr, &ev, &fl, &full, name, sizeof name) && (hash = strrchr(name, '#')) != 0 && !strcmp(hash + 1, kld_md[k].clip)) { rec = recs + own * 0x68; num = own; pair = 0; }
        if (!rec) { klog("down: flop: list: sheet #%d '%s' is OUT: %s (slot %d) %s in this body's set", kld_md[k].sheet, kld_md[k].clip, kld_md[k].slot, sid, lat ? "has no pair with a clip of that name" : "has no list"); continue; }
        kld_evtext(rec, evs, sizeof evs);
        net[0] = net[1] = net[2] = 0; klh_rd(rec + 0x18, net, 12); fwd = kld_fin(net[2]) ? -net[2] : 0.0f;      /* the record's net root movement; forward is -z */
        if (!full) { klog("down: flop: list: sheet #%d clip %lu '%s' is OUT: not a full-body clip (record +0x28 bit 0x10)", kld_md[k].sheet, num, name); continue; }
        if ((be = kld_badevent(rec, &bid, &bf)) != 0) {
            if (be > 0) klog("down: flop: list: sheet #%d clip %lu '%s' is OUT: event id %lu at frame %d, which the game's clip-event routine 0x637060 acts on (events %s)", kld_md[k].sheet, num, name, bid, bf, evs);
            else klog("down: flop: list: sheet #%d clip %lu '%s' is OUT: its events cannot be read", kld_md[k].sheet, num, name);
            continue;
        }
        if (kld_mx.reach > 0 && fwd > kld_mx.reach * 100.0f) {
            klog("down: flop: list: sheet #%d clip %lu '%s' is OUT by FlopReach=%.2f: its root goes %.2f m forward (%d frames, events %s)", kld_md[k].sheet, num, name, kld_mx.reach, fwd / 100.0f, fr, evs);
            continue;
        }
        n = kld_mx.n++;
        kld_mx.e[n].def = k; kld_mx.e[n].frames = fr; kld_mx.e[n].num = num; kld_mx.e[n].rec = rec; kld_mx.e[n].fwd = fwd;
        kld_mx.e[n].f7 = kld_evframe(rec, 7); kld_mx.e[n].f8 = kld_evframe(rec, 8);
        klog("down: flop: list: sheet #%d = clip %lu %08lx '%s' (pair %d of %s, slot %d - only read), %d frames (%.2f s at speed 1), events %s (lands at %d, rises from %d; -1 = none), the root goes %.2f m forward (%.2f m of it after the align frame %.1f: FILE), record flags %lx (0x40 moved by animation: %s; 0x1000 the four extra vectors of 0x8b4200: %s), weight %.1f%s%s: IN",
             kld_md[k].sheet, num, rec, name, pair + 1, kld_md[k].slot, sid, fr, (fr - 1) / 25.0f, evs, kld_mx.e[n].f7, kld_mx.e[n].f8, fwd / 100.0f, kld_md[k].after, 0.3f * (fr - 1), fl,
             (fl & 0x40) ? "yes" : "NO - not the kind this was read on: tell the track", (fl & 0x1000) ? "yes" : "no", kld_mx.w[k],
             kld_md[k].light ? "; HE STAYS UP: no mash, over when the clip is" : "", kld_mx.up && kld_md[k].upcut && kld_mx.e[n].f8 >= 0 ? "; FlopUp cuts it at its event 8" : "");
    }
    if (!kld_mx.n) { klog("down: flop: NO KNOCK-DOWN LIST on this body (player %08lx): no clip of FlopMix is usable here. The game's own fall stays", pl); return; }
    if (kld_mx.up) {                           /* FlopUp=71: the get-up words get FlopUpSlot - checked as Flop=2 checks its get-up */
        int idu = klq_slot(pl, kld.upslot), ok = idu >= 0 && idu <= 0x7fff && (n = kld_list(pl, idu, c, 8)) > 0;
        for (i = 0; ok && i < n; i++) ok = kld_clipfacts(c[i], &fr, &ev, &fl, &full, name, sizeof name) && full && kld_badevent(c[i], &bid, &bf) == 0;
        if (ok) { kld_s.idu = idu; klog("down: flop: FlopUp (A TEST KEY until live check U1): the get-up is %s = slot %d, '%s' of %d frames: asked for at a belly clip's event 8 by the game's own byte [D+0x21]; THE GET-UP STATE TAKES FULL DAMAGE; the three get-up words are this slot for EVERY down while the key stands - also after #42, after the stumble #43 if the game ever takes it to lying, and after a fall a time bound handed back to the game", kld.upslot, idu, name, fr); }
        else klog("down: flop: FlopUp: %s is not usable on this body (no such slot, no clip, not full-body or an event the game acts on): every clip is played whole", kld.upslot);
    }
    kld_s.idf = id; kld_s.fok = 1;
    kld_cx.at = at + 4; kld_cx.old = own; kld_cx.put = cnum; kld_cx.pool = klh_rd32(pl + 0x78); kld_cx.have = 1;
    klog("down: flop: the carrier is %s = slot %d, ONE pair {0, clip %lu} at %08lx in this body's set (pool %08lx; the level's own clip is %lu); %d clip(s) in the list", kld.fallslot, id, cnum, at, kld_cx.pool, own, kld_mx.n);
    kld_mix_next(pl, "the first choice on this body (a new round, another level or a body swap)");
}

/* The six id words of M: kept as found, ours written while he is UP (the fall reads them when it starts, the get-up
   when it starts: 0x5d6060 - never between). act = 0: what was found goes back. Game thread only. */
static void kld_flop_words(DWORD pl, DWORD ds, int act)
{
    DWORD m; WORD w[6], want; int k, n = 0, ok = 1, back = 0;
    if (!act) {
        kld_flop_belly(pl, 0); kld_mix_back(pl);
        if (!kld_s.fhave || !kld_s.fput) return;
        m = kld_s.fm;
        if (klh_rd32(pl) != KLD_PLAYER_VT || klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != pl) { kld_s.fhave = kld_s.fput = 0; kld_s.fwf = kld_s.fwu = 0; return; }      /* the object is gone: nothing of ours is anywhere */
        for (k = 0; k < 6; k++) {
            DWORD at = m + (k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3));
            want = (WORD)(k < 3 ? kld_s.idf : kld_s.idu);
            if (kld.flop == 3) {                                  /* review6 S5: by what was WRITTEN - a check made again has set idf / idu to -1 by now */
                int wr = k < 3 ? kld_s.fwf : kld_s.fwu;
                if (!wr) continue;
                want = (WORD)(wr - 1);
            } else if (k >= 3 && KLD_KEEPUP) continue;            /* Flop=1 never wrote the get-up words */
            if (klh_rd(at, &w[k], 2) && w[k] == want && want != kld_s.forig[k] && klh_data((void *)(DWORD_PTR)at, &kld_s.forig[k], 2, "the prone movement: a clip slot id, back as the game had it")) n++;
        }
        kld_s.fput = 0; kld_s.fwf = kld_s.fwu = 0;
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
        want = (WORD)(k < 3 || !KLD_KEEPUP ? k < 3 ? kld_s.idf : kld_s.idu : st);
        if (w[k] == want || w[k] == st || w[k] == 0xffff) continue;
        if (kld.flop == 3 && m == kld_s.fm && (k < 3 ? kld_s.fwf : kld_s.fwu) && w[k] == (WORD)((k < 3 ? kld_s.fwf : kld_s.fwu) - 1)) continue;      /* review6 S5: this part's own earlier write (the get-up words of a FlopUp that a later check lost): dealt with below */
        klog("down: flop: NO BELLY FLOP: word %d of the prone movement %08lx (+0x%x) holds %u, and %s is slot %u (65535 = none) in this level: not the words this part was read on - nothing is written, the game's own fall stays",
             k, m, (unsigned)(k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3)), w[k], kld_stock[k], st);
        kld_s.fok = 0;                                               /* the tick puts back what was written before, if anything */
        return;
    }
    if (!kld_s.fhave || m != kld_s.fm) { kld_s.fhave = 1; kld_s.fm = m; kld_s.fput = 0; kld_s.fwf = kld_s.fwu = 0; memcpy(kld_s.forig, w, sizeof w); }
    for (k = 0; k < 6; k++) {
        DWORD at = m + (k < 3 ? KLD_M_FALL + 2 * k : KLD_M_UP + 2 * (k - 3));
        want = (WORD)(k < 3 ? kld_s.idf : kld_s.idu);
        if (k >= 3 && KLD_KEEPUP) {                               /* Flop=1: the get-up words are the game's own */
            /* review6 S5: Flop=3 with FlopUp wrote them, and a check made again (a body swap) found the get-up slot
               not usable: they go back to what the game had, here, while he is up */
            if (kld.flop == 3 && kld_s.fwu && w[k] == (WORD)(kld_s.fwu - 1) && w[k] != kld_s.forig[k] && klh_data((void *)(DWORD_PTR)at, &kld_s.forig[k], 2, "the prone movement: a get-up slot id of FlopUp, back as the game had it (the get-up slot is not usable on this body)")) back++;
            if (k == 5 && kld.flop == 3 && kld_s.fwu) {
                kld_s.fwu = 0;
                klog("down: flop: FlopUp: the get-up words of the prone movement %08lx held this part's slot from an earlier body: %d of them are back as the game had them (%u/%u/%u)", m, back, kld_s.forig[3], kld_s.forig[4], kld_s.forig[5]);
            }
            continue;
        }
        if (w[k] == want) continue;
        if (kld_s.fput && !(kld.flop == 3 && (k < 3 ? kld_s.fwf : kld_s.fwu) && w[k] == (WORD)((k < 3 ? kld_s.fwf : kld_s.fwu) - 1)))
            kld_s.forig[k] = w[k];                                   /* the game filled its table again (0x750900): that is the new 'found' */
        if (kld.dry) { n++; continue; }
        if (klh_data((void *)(DWORD_PTR)at, &want, 2, "the prone movement: the slot id of the fall / the get-up")) {
            n++;
            if (kld.flop == 3) { if (k < 3) kld_s.fwf = want + 1; else kld_s.fwu = want + 1; }
        }
    }
    if (n && !kld_s.fput) {
        kld_s.fput = 1;
        klog("down: flop: the prone movement %08lx holds fall %u/%u/%u get-up %u/%u/%u (plain / compact / on the spot; 65535 = none): %s %d/%d/%d and %d/%d/%d%s",
             m, kld_s.forig[0], kld_s.forig[1], kld_s.forig[2], kld_s.forig[3], kld_s.forig[4], kld_s.forig[5],
             kld.dry ? "Dry=1, it WOULD be written" : "written", kld_s.idf, kld_s.idf, kld_s.idf,
             KLD_KEEPUP ? kld_s.forig[3] : kld_s.idu, KLD_KEEPUP ? kld_s.forig[4] : kld_s.idu, KLD_KEEPUP ? kld_s.forig[5] : kld_s.idu,
             KLD_KEEPUP ? " (one whole clip in the fall: the three get-up words are left as they are)" : "");
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
    DWORD m, ms = 0, clip, h, chans, clock, tick = 0, fl, q = 0, five = 5, ma = 0, mv = 0; float frame, to, fps, dt, rate, left, land; int ok = 1, i, fr, ev, full, mk, light; char name[96]; long ne; BYTE al = 0;
    if (!(m = klh_rd32(d + 0xc)) || klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != pl || !klh_rd(m + 0x8ec, &ms, 4)) return;
    if (!kld_s.fseen) {
        clip = klh_rd32(m + 0x8cc);
        if (ds == 2 && (ms != 1 || !clip)) return;                   /* the fall has not begun in M yet: look again next tick */
        kld_s.fseen = 1;
        if (ds != 2) { klog("down: flop: first seen in down state %lu (the fall was over within one tick): this down is the game's own", ds); return; }
        /* Flop=3: by the clip the movement REALLY plays (record addresses are global), not by what was written last */
        kld_s.fmi = kld.flop == 3 ? kld_mix_find(clip) : -1;
        kld_s.fnow = kld_s.fok && !kld.dry && (kld.flop == 3 ? kld_s.fmi >= 0 : kld_inlist(pl, kld_s.idf, clip));
        kld_clipfacts(clip, &fr, &ev, &fl, &full, name, sizeof name); klh_rd(d + 0xf4, &al, 1);
        if (kld.flop == 3 && kld_s.fmi >= 0) {
            /* review6 M2 (log only: reads). The game's alignment of the fall decides how far a dive really goes: by
               AlignTo (0x80fdc0, re\climb.md 3) he is AT the align place at frame 0.3 x (N - 1), whatever the clip's
               root did up to there; only the travel after that frame is the clip's own (kld_md's `after`: FILE).
               His place is his NODE's (klclimb.c: the floats at +0x460 stay at the navigation mesh's edge); the align
               heading is row 0 of the rotation at D+0xf8 = where the back points, as klclimb.c reads a rotation
               (ASSUMED the same form here: who fills D+0xf8 was not read). Collision: byte [player+0x7a5] (1 = on:
               ZMovementAnimation then runs the physics step, 0x53986f) and the off count [player+0x7b4]. */
            int df = kld_mx.e[kld_s.fmi].def; float pa[3] = { 0, 0, 0 }, ad = -1.0f, rot[9], nd[3], bk[3], deg = 999.0f; BYTE con = 0xff; DWORD coff = 0xffffffff; const float *from = kld_s.pnok ? kld_s.pn : kld_s.p0;
            int nok = klq_node(klh_rd32(pl + 4), nd, bk);
            klh_rd(pl + 0x7a5, &con, 1); klh_rd(pl + 0x7b4, &coff, 4);
            if (al && klh_rd(d + 0x11c, pa, 12) && kld_fin(pa[0]) && kld_fin(pa[2])) ad = (float)sqrt((pa[0] - from[0]) * (pa[0] - from[0]) + (pa[2] - from[2]) * (pa[2] - from[2]));
            if (al && nok && klh_rd(d + 0xf8, rot, sizeof rot) && kld_fin(rot[0]) && kld_fin(rot[2]) && (rot[0] * rot[0] + rot[2] * rot[2]) > 0.01f && (bk[0] * bk[0] + bk[2] * bk[2]) > 0.01f)
                deg = (float)(atan2(rot[0] * bk[2] - rot[2] * bk[0], rot[0] * bk[0] + rot[2] * bk[2]) * 57.29577951);
            kld_s.fal = al && ad >= 0; kld_s.fad = ad; kld_s.fap[0] = pa[0]; kld_s.fap[1] = pa[1]; kld_s.fap[2] = pa[2];
            if (kld_s.fnow) { kld_mx.lastgroup = kld_md[df].group; kld_mx.played++; kld_mx.drawn[df]++; }
            klog("down: flop: THE KNOCK-DOWN: clip %lu '%s' (sheet #%d), drawn %d of %d%s; the clip alone carries him %.2f m forward; %s%s; his collision [player+0x7a5] is %u (1 = on: the physics step runs in the fall), the off count [player+0x7b4] %lu%s",
                 kld_mx.e[kld_s.fmi].num, name, kld_md[df].sheet, kld_mx.drawn[df], kld_mx.played, kld_s.fnow ? "" : " (NOT counted: Dry=1 or no list - the game plays it its own way)", kld_mx.e[kld_s.fmi].fwd / 100.0f,
                 kld_md[df].light ? "HE STAYS UP: no mash, the knock is over when the clip is" : "the mash runs from its landing",
                 kld_s.fmi != kld_mx.next ? "; NOT the clip written for this fall (it began before the choice was in the pair): played all the same" : "",
                 (unsigned)con, coff, con == 1 && coff == 0 ? "" : " - HIS COLLISION IS NOT ON IN THIS FALL: nothing stops the clip's root at a wall; say so to the lead (FlopReach=1)");
            if (al && ad >= 0) klog("down: flop: THE GAME ALIGNS THIS FALL ([D+0xf4]) to the place (%.0f, %.0f, %.0f), %.2f m from where he went down; the align heading is %.0f degrees off his own (999 = not readable; 0 = he keeps his heading); by AlignTo he is at that place at frame %.1f (0.3 x the last frame) whatever the clip's root did - of its %.2f m only %.2f m come after that frame (FILE): he should end about %.2f m from where he went down%s",
                                    pa[0], pa[1], pa[2], ad / 100.0f, deg, 0.3f * (fr - 1), kld_mx.e[kld_s.fmi].fwd / 100.0f, kld_md[df].after, ad / 100.0f + kld_md[df].after,
                                    kld_mx.e[kld_s.fmi].fwd > 200.0f && ad < 100.0f && !kld_md[df].light ? " - THE ALIGN PLACE IS AT HIS FEET: THIS DIVE IS PLAYED (NEARLY) ON THE SPOT, the body held back under the clip - look at the pictures: is it the fall of the sheet?" : "");
            else klog("down: flop: the game does NOT align this fall ([D+0xf4] is %u): the whole %.2f m are the clip's own, unless something stops him", (unsigned)al, kld_mx.e[kld_s.fmi].fwd / 100.0f);
        }
        kld_s.fclip = clip; kld_s.f7 = kld_evframe(clip, 7); kld_s.f8 = kld_evframe(clip, 8);
        if ((h = klh_rd32(m + 0x8d0)) != 0) klh_rd(h + 0x34, &q, 4);
        mk = kld_mask(pl, &ma, &mv);                                 /* the fall's two bits must read set here: the proof of the lookup (a Dry run prints it too) */
        if (kld_s.fnow) klog("down: flop: THE KNOCK-DOWN: the fall is clip %08lx '%s' of %d frames (%.2f s at speed 1): he has landed at frame %d (its event 7), rises from frame %d (event 8; -1 = none); the whole clip is played in the fall - no press cuts it; a hit of it is swallowed by the game's own trigger UNLESS the 'rules:' lines say the switch is off (Vulnerable, track R8); from the landing on FlopBase %.2f + FlopPerPress %.2f a press, at most FlopTop %.2f; the channel's event queue is %08lx; the input mask %08lx holds %08lx (%s; bits 0x11 are the fall's)%s",
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
    light = kld.flop == 3 && kld_s.fmi >= 0 && kld_s.fmi < kld_mx.n && kld_md[kld_mx.e[kld_s.fmi].def].light;      /* #43: he never lies - the game's pace to the end */
    if (!kld_s.cap0set) {
        float way = land > frame ? (land - frame) / fps : 0.0f, rest = (to - (land > frame ? land : frame)) / (light ? fps : kld.fbase * 25.0f);
        kld_s.cap0set = 1; kld_s.cap0 = tick + (DWORD)((way + rest) * 1024.0f + 0.5f) + 1024;
    }
    if ((long)(tick - kld_s.cap0) > 0) {
        kld_s.fdone = 2;
        klog("down: flop: THE TIME BOUND OF THE WHOLE KNOCK-DOWN (frame %.1f of %.0f, %.2f s after he went down, channel flags %lx): this part stops writing - the game ends the fall at the tick last written and its own lying / GET UP take over; say so to the lead", frame, to, (now - kld_s.t_down) / 1000.0f, fl);
        return;
    }
    /* FlopUp=71 (Flop=3; kld_s.idu is the get-up slot only then): at the clip's event 8, when he lies chest down there
       (kld_md's upcut), the game's own 'get-up asked' byte - what a press sets (0x7180b0), acted on whenever it stands
       (0x47ce56 -> 0x8b1900: while D is 2 the fall's channel is stopped, M = 2, THE INPUT MASK COMES OFF, D = 3 and
       0x478270(M, 4) starts the get-up words' clip in that frame; re\player_down.md 9.2). From there the get-up is the
       game's state with this file's mash (FlopBase / FlopPerPress / FlopTop by the clip). Nothing more is written to the
       fall; a request the game does not take is taken back when D ends, and the fall ends by the game's own tick. */
    if (kld.flop == 3 && kld_s.idu >= 0 && kld_s.fmi >= 0 && kld_s.fmi < kld_mx.n && kld_md[kld_mx.e[kld_s.fmi].def].upcut && kld_s.f8 >= 0 && frame >= (float)kld_s.f8) {
        BYTE one = 1;
        if (klh_data((void *)(DWORD_PTR)(d + 0x21), &one, 1, "down-not-dead: the get-up is asked for (FlopUp)")) {
            kld_s.fasked = 1; kld_s.t_ask = now; kld_s.fdone = 3;
            klog("down: flop: FlopUp: he lies (frame %.1f of %.0f, the clip's event 8 at %d, %.2f s after he went down): the get-up %s is asked for by the game's own byte [D+0x21] - FROM HERE EVERY HIT COSTS", frame, to, kld_s.f8, (now - kld_s.t_down) / 1000.0f, kld.upslot);
        } else kld_s.fdone = 2;
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
    if (frame >= land && !light) {
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
        rate = B + P * kld_s.meter; if (rate > T) rate = T; rate /= kltt_get(-1, KLTT_REVIVE); if (rate < 0.05f) rate = 0.05f;      /* kltrait.c ReviveTime: x time to get up */
        kld_s.sumr += rate; kld_s.nr++; kld_v.rate = rate;
        if (kld.log >= 2 && now - kld_s.lastline >= 250) { kld_s.lastline = now; klog("down: flop: frame %.1f of %.0f (%s), speed %.2f, meter %.2f, %d press(es)", frame, to, kld_s.f8 >= 0 && frame < kld_s.f8 ? "he lies" : "he rises", rate, kld_s.meter, kld_s.presses); }
        fps = rate * 25.0f;
        if (!klh_data((void *)(DWORD_PTR)(h + 0x10), &fps, 4, "the knock-down clip's channel: frames a second")) return;
    }
    /* the two ticks: always 2 s behind where the clip will be through at the pace it has now */
    ne = (long)tick + (long)(left / fps * 1024.0f + 0.5f) + 2048;
    klh_data((void *)(DWORD_PTR)(m + 0x8dc), &ne, 4, "the prone movement: the tick the fall is over, held behind the clip's end");
    klh_data((void *)(DWORD_PTR)(m + 0x8e0), &ne, 4, "the prone movement: the fall's event tick, held with its end");
    kld_r.beat = kld_r.pass;                   /* track R8: THIS pass held the fall (D 2, M 1, the clip on its channel, inside both bounds) - only then may the game's switch be off (kld_rules) */
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

/* ---- the camera stays the player's, and the game's own TAP QUICKLY prompt ([Down] Camera, Prompt; track R7) -------
   The owner, 2026-10-11 19:10: 'for the animation should try and keep the camera like normal i think its fixes down
   when it happen ... but make sure theres an prompt that lookls very similar to the break free from human shield in FA
   or even campaign'. re\player_down.md 13 has the whole reading. NOTHING OF THIS HAS RUN IN THE GAME.

   THE CAMERA (READ whole: 0x4844e0, 0x417310, 0x76fd40, 0x4d9ec0, 0x87d930, 0x8a4fa0, 0x8ee220, 0x74a120, 0x4719f0).
   The four tests of the input mask [player+0xed0] (the dword kld_mask finds) all sit in ZGameplayInputWintel's
   per-frame read 0x4844e0: the MOUSE's two look sums [input+0x3e0] (turn) and [input+0x3e4] (up / down) are zeroed
   while the mask has bits 0x30 / 0x50 (0x4d9ec0, 0x87d930), the two MOVE axes [input+0x310] / [+0x314] while it has
   bits 5 / 3 (0x417310, 0x76fd40). So of the fall's two bits (0x76a827 .. 0x76a834), 1 = NO MOVE and 0x10 = NO LOOK:
   the look sums are what 0x8a4fa0 hands to the player's camera rig ([player+0xbd4], slots +0x1c / +0x20) every frame.
   Stock gives the look back in the middle of the fall - 0x8ee25c takes bit 0x10 off as soon as 0x843fa0 is true (the
   tick [M+0x8e0], 0.72 s in) - and the move at its end. THE FLOP HOLDS THAT TICK BEHIND THE CLIP'S END (kld_flop_one;
   Flop=2 holds it at the end tick), so 0x843fa0 is never true and the mouse is dead for the whole knock-down, 2 - 9 s:
   that is 'it fixes'. Nothing else of the camera is forced: no profile of the camera's selection 0x778f50 tests this
   down state (only a human-shield carrier's, state 0x12), the follow camera takes its place from the player's rig as
   ever (LIVE, run G1's pictures: it is low and close behind the lying body, by itself).
   Camera=1: while a fall this part drives plays (kld_s.fnow, D state 2), bit 0x10 of that dword is taken off - the
   game's own AND (0x787600), the game's own state from 0.72 s on in every stock fall - once, in the first pass. Bit 1
   stays: he cannot walk. The pad's look stick ([input+0x3e8] / [+0x3ec]) is not gated by the mask in 0x4844e0.
   CameraSide=1: the down start forces the camera to the LEFT shoulder (0x76a889 -> 0x74a120: left while [D+8] bit 0
   and [D+4] != 3 - made for the stock pose, on his left side, head propped). For the flop the side he had is put back
   by the setter's own writes done as data (0x74a1a8 .. 0x74a1cb, read whole): byte [player+0x280c], bit 0x400 of
   [player+0x818], and - as the setter does when the side changes - [player+0x2f80] = float [0xb4c788] and float
   [[player+0xbd8]+0x5a0] = 0 (0x4719f0: the camera's blend; written only when that object is a ZFFCamera1). The
   The setter's direct form also writes dword [player+0xb8c] = 0 (0x74a1a8: no delayed change armed; review 7, S5) -
   after the down start's own call it IS 0, so the data form does not write it: it is read into the side line, and a
   value armed later in the fall (the timer form 0x74a15f) stops this part's side writes for that down. The
   camera walks its side spline by itself when the byte differs from its own copy (0x9088c0). The blend is thus
   restarted twice in two frames (the down start's, then ours: review 7, S6 - a twitch is possible; CameraSide=0). The game's end of the
   down state puts its kept side back as ever (0x71089a). At most three times a down: a caller that forces it again
   wins. NOT sent: the RMC SetLeftShoulder the key's handler sends (Arcade has no peer).

   THE PROMPT (READ whole: ZMiniGameButtonMashingDisplay, vtable 0xbbe8f0 - slot 2 Render 0x48f4b0, slot 5 Tick
   0x8ac680, slot 6 layout 0x4a8d40; 0x869fd0, 0x47e230, 0x4424f0, 0x588680, 0x4ddae0).
   The game has ONE 'tap' prompt for all its mash games, the HUD element at [osd+0x10fc]: the text '{Tap<button>}' +
   the level's own string AllLevels/Interface/TapQuickly ('Tap Quickly' - the token becomes the picture of the key or
   pad button bound to it, 0x7bb920 by the player's controller [player+0x91e]) over a bar that FILLS: a white frame
   (the OSD's picture [osd+0x7ec], layer 9) and a fill ([osd+0x888], layer 0xb, colour [E+0x114]) 177 wide x value /
   max, below the middle of the screen (0x4a8d40's constants -61 .. 190). EVERY user of it in the exe drives it by
   plain writes of four fields: byte [E+0x50] = shown, float [E+0x54] = value, float [E+0x58] = max, byte [E+0x5c] =
   which button (0 {TapCover}, 1 {TapUse}, 2 {TapCycleWeapon}, 3 {TapCloseCombat}: the Tick's table 0x8ac8b8 - and
   0x4424f0 pairs 0 with the Cover byte [player+0xeb4], the very input [D+0x2b] is fed from), and the fill's colour by
   0x47e230 (white [0xbbe490], or red [0xbbe498] in the 'help him up' game 0x769630).
   THIS ELEMENT IS THE HUMAN-SHIELD BREAK-FREE PROMPT - READ, not assumed (review 7, M1; the first form of this
   comment filed these routines under 'the rise after a ragdoll throw': wrong). 0x860dc0 has ONE caller, 0x7fa515,
   inside the human-shield part of the player's frame 0x7f9eb0; it works on the carrier [player+0xad4], the victim
   [player+0xad0] and the two tap floats [+0xae4] / [+0xae8] (the fTaps of RMCSetHumanShieldPvPTaps..):
   - the CARRIER's branch (0x860ddb): 0x4424f0 draws one of the four buttons at random, writes it into [E+0x5c] and
     returns that button's input byte; +1 a press, a share off each frame, the value into [E+0x54];
   - the VICTIM's branch (0x860ed3 .. 0x861075) = the break-free: 0x860f36 sets [E+0x50] = 1, [E+0x58] = his goal,
     [E+0x5c] = 1 = {TapUse}; a press of Use adds 1 to [+0xae8], each frame takes a share off, the value goes to
     [E+0x54] (0x860ffa); free at the goal, 0x861071 clears [E+0x50]. The colour is never touched there: WHITE.
   So the game's break-free shows: the USE key's picture + 'Tap Quickly' + a WHITE bar that is his own tap METER and
   falls back when he stops. 0x8d6628 (in 0x8d64f0, shown + max; it sets the same mask bits 1 / 0x200 / 0x400 as
   the struggle - the start of a hold by the look of it; its caller 0x4d7b00 was NOT read), 0x451197 / 0x7cba04 /
   0x7fa69a: the hold's other on / off writes. The other users: the campaign's button-mash action
   (ZFFActionMiniGameButtonMashing 0x7fbf10, ZMiniGameButtonMashing 0x6ffab0 / 0x5d18c0), the downed-buddy game
   (0x5fe270: 0x769630, 0x7371f0, 0x77d3a0, 0x7b6780) and the Fragile Alliance rules' reset (0x708500, slot 4: off).
   No path clears the element every frame (the review looked at all 30 functions that load [osd+0x10fc]).
   OURS AGAINST THE GAME'S: the same element, text and bar, drawn by the game. Different on purpose: the picture is
   the COVER / GET UP key (button 0), not Use - it is the key the mash reads ([D+0x2b]); PromptStyle 1 (default) is
   a progress bar, the hook's own design; PromptStyle=2 with PromptPulse=0 is the game's own behaviour (a meter,
   white). The owner picks after seeing both (live checks C1 / C3).
   Prompt=1: from the landing of a knock-down this part drives (Flop=1 / 3) and during a get-up it drives (Flop=0 / 2)
   the same four fields are written each pass: shown 1, button 0 = {TapCover} = the game's GET UP button, max 1.0,
   value = PromptStyle 1 (default): how far he is up (the clip's frame from the landing to its end) - the bar fills
   as he rises, faster while he taps; PromptStyle 2: the mash meter's speed between FlopBase and FlopTop (it falls
   back when he stops). PromptPulse=1 (default 0 since review 7: the game's break-free bar stays white): the fill is
   the game's red [0xbbe498] for 0.12 s after each press - the hook's own touch, the two colours are the game's. No
   call, no vtable copy, no text made: the element's own Tick builds the text and the bar, its own Render draws
   them. [HUD] Enable=0 changes nothing here: klhud.c is not used.
   OFF again (shown 0, value 0, white - what 0x7cba04 writes): when he is up, dead or out of play (kld_s.dead), when
   the part stops acting (a stock level, no Arcade session, a police body, another player object), when the round
   does not run any more (the session state [session+0x70] is not 0x19: review 7, S1), when the clip is
   through, and while the game's tick stands still for half a second (the pause menu - ASSUMED that the tick
   stands there, as the rest of this file assumes). The OFF is written only to the element the local player's OSD
   leads to in that pass (review 7, S2). NEVER TAKEN while the game shows it itself ([E+0x50] already set
   by somebody else - by the reading only a shield hold, the campaign's mash entity or the buddy game, none of which
   is expected in a one-human Arcade round: a GUESS, not read); the element must be a
   ZMiniGameButtonMashingDisplay whose player [E+0x10] is the local one.
   NOT SHOWN: in a Dry run, for the stumble #43 (he never lies), while he lies the stock way (the game's own
   '{TapCover} Get Up' use action shows there, 0x5505c0). */
#define KLD_MASH_VT   0x00bbe8f0             /* ZMiniGameButtonMashingDisplay */
#define KLD_CAM_VT    0x00bb76a4             /* ZFFCamera1 */
#define KLD_OSD_MASH  0x10fc                 /* [osd + this] = the element (the OSD's constructor 0x42ec1d) */
#define KLD_MASK_LOOK 0x10                   /* the mouse look: 0x4d9ec0 (0x30), 0x87d930 (0x50) */
#define KLD_ROUND     0x19                   /* [session+0x70]: a round that runs (klbot.c's KLB_ROUND, klfed.c's KLP_ROUND) */
/* (the block's state, kld_v, is declared beside kld_s: kld_flop_one leaves the clip speed in it) */

/* The local player's mash element, as the game finds it (0x4ce73f .. 0x4ce753: 0x588680 = [gamedata+0x15dc], then
   0x4ddae0(that, [player+0x91e]) = the OSD when the index is 0 / 1 and its byte is not 0xff). Reads only. -> 0 + why */
/* own = 1: the element's player [E+0x10] must be pl (to SHOW it); own = 0: the element of pl's OSD whoever it names
   (to switch OFF what is ours: review 7, S2). *posd = that OSD (review 7, S4: its 'HUD off' byte is logged). */
static DWORD kld_mash_elem(DWORD pl, int own, DWORD *posd, const char **why)
{
    DWORD gd, mgr, osd, e; BYTE i = 0xff, there = 0xff;
    if (posd) *posd = 0;
    *why = "no OSD for this player ([gamedata+0x15dc], index [player+0x91e])";
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLD_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x15dc)) || !klh_rd(pl + 0x91e, &i, 1) || i > 1) return 0;
    if (!klh_rd(mgr + 8 * (DWORD)i + 4, &there, 1) || there == 0xff || !(osd = klh_rd32(mgr + 8 * (DWORD)i))) return 0;
    if (posd) *posd = osd;
    *why = "[osd+0x10fc] is not a ZMiniGameButtonMashingDisplay (vtable 0xbbe8f0)";
    if (!(e = klh_rd32(osd + KLD_OSD_MASH)) || klh_rd32(e) != KLD_MASH_VT) return 0;
    *why = "the element's player [E+0x10] is not the local player";
    if (own && klh_rd32(e + 0x10) != pl) return 0;
    *why = "";
    return e;
}

/* Review 7, S2: the remembered pointer is NOT trusted by its vtable alone (freed memory keeps its bytes). The OFF is
   written only when the local player object of THIS pass (kld_v.pl: gamedata's own table, vtable checked by
   kld_tick_main) leads through its OSD to the very element we switched on. No player this pass: tried again for 3 s,
   then dropped unwritten (the element died with its level). */
static void kld_prompt_off(const char *why, DWORD now)
{
    BYTE zero = 0; float fz = 0; DWORD white = klh_rd32((DWORD_PTR)KLH_VA(0xbbe490)), e; const char *w2 = "";
    if (!kld_v.ours) return;
    if (!kld_v.pl) {
        if (!kld_v.t_lost) kld_v.t_lost = now;
        if (now - kld_v.t_lost < 3000) return;
        kld_v.ours = 0; kld_v.t_lost = 0;
        klog("down: prompt: over (%s) - no local player object for 3 s: the element %08lx is taken as gone with its level, nothing is written", why, kld_v.elem);
        kld_v.elem = 0; return;
    }
    kld_v.ours = 0; kld_v.t_lost = 0;
    if (!kld_v.elem || (e = kld_mash_elem(kld_v.pl, 0, NULL, &w2)) != kld_v.elem) { klog("down: prompt: over (%s) - the local player's OSD does not lead to the element %08lx any more (%s): it is gone with its level, nothing is written", why, kld_v.elem, w2[0] ? w2 : "another element is there"); kld_v.elem = 0; return; }
    klh_data((void *)(DWORD_PTR)(kld_v.elem + 0x50), &zero, 1, "the tap prompt: not shown (as the game's own users switch it off, 0x7cba0c)");
    klh_data((void *)(DWORD_PTR)(kld_v.elem + 0x54), &fz, 4, "the tap prompt: its bar's value, 0 (0x7cba16)");
    if (white) klh_data((void *)(DWORD_PTR)(kld_v.elem + 0x114), &white, 4, "the tap prompt: its bar's colour, the game's white (0x47e245)");
    klog("down: prompt: OFF after %.2f s (%s): [E+0x50] = 0, the bar 0", (now - kld_v.t_on) / 1000.0f, why);
    kld_v.elem = 0;
}

static void kld_camera(DWORD pl, DWORD ds, DWORD now)
{
    DWORD ma = 0, mv = 0, nv, f818 = 0; BYTE side = 0xff;
    if (!kld_v.cam) return;
    if (ds == 0) {                             /* up: the side he has is the side to keep */
        if (klh_rd(pl + 0x280c, &side, 1) && side <= 1) { kld_v.side0 = side; kld_v.sidehave = 1; }
        kld_v.lookn = kld_v.siden = kld_v.sidetold = kld_v.sidearm = 0;
        return;
    }
    if (ds != 2 || !kld_s.fnow || kld_s.dead) return;      /* only a fall this part drives (never in a Dry run: fnow is 0 there), never for a dead man */
    /* review 7, S5: the setter's DELAYED form (0x74a15f .. 0x74a170: timer [player+0xb88], dword [player+0xb8c] = +1 /
       -1; its direct form writes that dword 0, 0x74a1a8). The down start's own direct call leaves it 0, so a value
       here was armed IN the fall by somebody else (the shoulder key? - not read): that side is theirs, this part
       writes no side any more in this down. Which sign is which side is a GUESS from 0x74a167 (+1 = right). */
    if (kld_v.side && !kld_v.sidearm) {
        DWORD arm = 0;
        if (klh_rd(pl + 0xb8c, &arm, 4) && arm != 0) {
            kld_v.sidearm = 1;
            klog("down: camera: a delayed side change is armed in this fall ([player+0xb8c] = %ld, the setter's timer form 0x74a15f; +1 = to the right - a GUESS): the side it sets is left alone, CameraSide writes nothing more in this down", (long)arm);
        }
    }
    if (kld_mask(pl, &ma, &mv) && (mv & KLD_MASK_LOOK) && kld_v.lookn < 3) {
        nv = mv & ~(DWORD)KLD_MASK_LOOK;
        if (klh_data((void *)(DWORD_PTR)ma, &nv, 4, "the player's input object: the fall's LOOK bit (0x10) off, as the game takes it off at the fall's event tick (0x8ee25c)")) {
            kld_v.lookn++;
            klog("down: camera: the fall's LOOK bit of the input mask %08lx is taken off %.2f s after he went down: %08lx -> %08lx (bit 0x10 zeroes the mouse's two look sums, 0x4d9ec0 / 0x87d930; stock takes it off 0.72 s into its fall, the flop holds that tick) - the camera is his for the whole knock-down; bit 1 (no move) stays%s",
                 ma, (now - kld_s.t_down) / 1000.0f, mv, nv, kld_v.lookn > 1 ? " - AGAIN in this down: somebody set it once more" : "");
        }
    }
    if (kld_v.side && !kld_v.sidearm && kld_v.sidehave && klh_rd(pl + 0x280c, &side, 1) && side <= 1 && side != kld_v.side0 && klh_rd(pl + 0x818, &f818, 4)) {
        if (kld_v.siden >= 3) {
            if (!kld_v.sidetold) { kld_v.sidetold = 1; klog("down: camera: the game put the camera on the %s shoulder again after this part's third write in this down: left to the game", side ? "left" : "right"); }
        } else {
            DWORD nf = kld_v.side0 ? (f818 | 0x400) : (f818 & ~(DWORD)0x400), cam = klh_rd32(pl + 0xbd8); float blend = 0, fz = 0; int camok = cam && klh_rd32(cam) == KLD_CAM_VT;
            if (klh_data((void *)(DWORD_PTR)(pl + 0x280c), &kld_v.side0, 1, "the player's camera side byte, the side he had (the setter's own write, 0x74a1b2)") &&
                klh_data((void *)(DWORD_PTR)(pl + 0x818), &nf, 4, "the player's flags: bit 0x400 = the camera on the left shoulder (0x74a1bc / 0x74a1cb)")) {
                if (camok && klh_rd((DWORD_PTR)KLH_VA(0xb4c788), &blend, 4) && kld_fin(blend)) {      /* 0x74a197 .. 0x74a1a3, as the setter does when the side changes */
                    klh_data((void *)(DWORD_PTR)(pl + 0x2f80), &blend, 4, "the player's side-change time (0x74a19d)");
                    klh_data((void *)(DWORD_PTR)(cam + 0x5a0), &fz, 4, "the camera's blend, restarted (0x4719f0)");
                }
                kld_v.siden++;
                klog("down: camera: the down start had put the camera on the %s shoulder; the side he had is back (%s): byte [player+0x280c] %u -> %u, flags [player+0x818] %08lx -> %08lx%s; the delayed-change word [player+0xb8c] reads %ld (0 = none armed: the setter's own state after its direct form) (write %d of 3 in this down; the game's own end of the down state sets its kept side as ever)",
                     side ? "LEFT" : "RIGHT", kld_v.side0 ? "left" : "right", (unsigned)side, (unsigned)kld_v.side0, f818, nf, camok ? ", the camera's blend restarted" : "; [player+0xbd8] is not a ZFFCamera1: its blend is left alone", (long)klh_rd32(pl + 0xb8c), kld_v.siden);
            }
        }
    }
}

static void kld_prompt(DWORD pl, DWORD ds, DWORD now)
{
    int want = 0; float v = 0, lo = 0, hi = 1, one = 1.0f; DWORD e, osd = 0, clock, tick = 0, col; BYTE b = 0, on = 1, btn0 = 0; const char *why = "", *off = "he is up";
    int paused = 0, inround = kld_v.state == KLD_ROUND;    /* review 7, S1: a round that runs; the score page (0x1f) and every other state = no prompt */
    if (ds == 0) kld_v.refused = 0;
    if (kld_v.prompt && kld_v.act && pl && !kld_s.dead && !kld.dry && inround) {
        if (KLD_ONE && ds == 2 && kld_s.fnow && !kld_s.fdone && kld_s.t_land && kld_s.endf > 1.0f) {      /* a knock-down this part drives, from its landing (never the stumble: no landing is set for it) */
            float land = kld_s.f7 >= 0 ? (float)kld_s.f7 : 0.3f * kld_s.endf;
            want = 1; lo = kld.fbase; hi = kld.ftop;
            v = kld_s.endf > land + 1.0f ? (kld_s.lastf - land) / (kld_s.endf - land) : 1.0f;
        } else if (ds == 3 && kld_s.up && kld_s.endf > 1.0f) {                                            /* a get-up this part drives */
            want = 1; lo = kld_s.fup ? kld.fbase : kld.base; hi = kld_s.fup ? kld.ftop : kld.top;
            v = kld_s.lastf / kld_s.endf;
        }
        if (want && kld_v.style == 2) v = hi > lo + 0.01f ? (kld_v.rate - lo) / (hi - lo) : 0.0f;
    }
    if (kld_s.dead) off = "he is dead or out of play"; else if (!kld_v.act || !pl) off = "the part does not act here (a stock level, no Arcade session, a police body, no player)"; else if (!inround) off = "the round does not run any more (the session state is not 0x19: the round's end, the score page)"; else if (ds != 0) off = "the clip is through, or the game took the state over";
    /* the pause menu: the game's tick stands (ASSUMED; live check C4). Review 7, S7: the clock of the test starts
       afresh in the first pass the prompt is wanted (no stale tick of the last down), and the bound is 500 ms - one
       long frame (a hitch, a streamed load) is not a pause */
    if (want && (clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) != 0 && klh_rd(clock + 0x48, &tick, 4)) {
        if (!kld_v.waswant || tick != kld_v.gtick) { kld_v.gtick = tick; kld_v.t_gtick = now; }
        else if (now - kld_v.t_gtick > 500) { want = 0; paused = 1; off = "the game's tick stands still (the pause menu)"; }
    }
    kld_v.waswant = want || paused;            /* in a pause the test goes on from its own clock */
    if (!want) { kld_prompt_off(off, now); return; }
    if (!(e = kld_mash_elem(pl, 1, &osd, &why))) {
        kld_prompt_off("the element is not there any more", now);
        if (!kld_v.refused) { kld_v.refused = 1; klog("down: prompt: NOT SHOWN in this down: %s", why); }
        return;
    }
    if (kld_v.ours && e != kld_v.elem) kld_prompt_off("another element belongs to the player now", now);
    if (!kld_v.ours) {
        if (!klh_rd(e + 0x50, &b, 1)) return;
        if (b) { if (!kld_v.refused) { kld_v.refused = 1; klog("down: prompt: the game shows its own tap prompt (element %08lx, [E+0x50] = %u, button %d): left alone in this down", e, (unsigned)b, (int)(signed char)klh_rd32(e + 0x5c)); } return; }
        if (kld_v.refused) return;
        kld_v.ours = 1; kld_v.elem = e; kld_v.presses = kld_s.presses; kld_v.t_press = 0; kld_v.t_on = now; kld_v.t_lost = 0;
        klog("down: prompt: ON %.2f s after he went down: the game's own tap prompt (ZMiniGameButtonMashingDisplay %08lx: '{TapCover}' + the level's 'Tap Quickly' over its bar) - [E+0x50] = 1, button [E+0x5c] = 0 (the Cover / GET UP button), the bar [E+0x54] / [E+0x58] = %s; PromptPulse=%d",
             (now - kld_s.t_down) / 1000.0f, e, kld_v.style == 2 ? "the mash's speed between its base and its top (PromptStyle=2: the game's own break-free bar is such a meter)" : "how far he is up, 0 at the landing .. 1 on his feet (PromptStyle=1)", kld_v.pulse);
        {   /* review 7, S4: what decides whether the element's Render draws (reads only): its own two bytes, and the OSD's
               'HUD off' byte - while that is set the loop 0x8bf583 .. 0x8bf5cd draws the mash element only when
               [[player+0x2940]+0x24] is 2 .. 0xd (the game's own mash states), which a knock-down of ours is not */
            BYTE e24 = 0xee, e25 = 0xee, hudoff = 0xee; DWORD p2940 = klh_rd32(pl + 0x2940), st24 = 0xeeeeeeee;
            klh_rd(e + 0x24, &e24, 1); klh_rd(e + 0x25, &e25, 1); klh_rd(osd + 0x1225, &hudoff, 1); if (p2940) klh_rd(p2940 + 0x24, &st24, 4);
            klog("down: prompt: draw state: [E+0x24] = %02x (Render wants it not 0), [E+0x25] = %02x (the hide byte), the OSD's HUD-off byte [osd+0x1225] = %02x, [[player+0x2940]+0x24] = %lx%s (ee = not readable)",
                 (unsigned)e24, (unsigned)e25, (unsigned)hudoff, st24,
                 e24 == 0 ? " - [E+0x24] IS 0: THE ELEMENT WILL NOT DRAW" : (hudoff != 0 && hudoff != 0xee && !(st24 >= 2 && st24 <= 0xd)) ? " - THE HUD IS OFF AND THIS IS NOT ONE OF THE GAME'S MASH STATES: THE ELEMENT WILL NOT DRAW" : "");
        }
    }
    if (kld_s.presses != kld_v.presses) { kld_v.presses = kld_s.presses; kld_v.t_press = now; }
    if (!kld_fin(v) || v < 0) v = 0; if (v > 1.0f) v = 1.0f;
    col = klh_rd32((DWORD_PTR)KLH_VA(kld_v.pulse && kld_v.t_press && now - kld_v.t_press < 120 ? 0xbbe498 : 0xbbe490));
    if (!klh_data((void *)(DWORD_PTR)(e + 0x5c), &btn0, 1, "the tap prompt: which button, 0 = {TapCover} (the Tick's table 0x8ac8b8)") ||
        !klh_data((void *)(DWORD_PTR)(e + 0x58), &one, 4, "the tap prompt: its bar's maximum") ||
        !klh_data((void *)(DWORD_PTR)(e + 0x54), &v, 4, "the tap prompt: its bar's value") ||
        !klh_data((void *)(DWORD_PTR)(e + 0x50), &on, 1, "the tap prompt: shown (as the game's own users switch it on, 0x8d6628)")) { kld_prompt_off("a write was refused", now); kld_v.refused = 1; return; }
    if (col) klh_data((void *)(DWORD_PTR)(e + 0x114), &col, 4, "the tap prompt: the bar's colour, one of the game's two (0x47e230)");
}

/* ---- track R8: while knocked down - NO SHOOTING, NOT INVULNERABLE, police hurt him little, heisters in full -------- */
/* The owner, 2026-10-11 20:45, after playing Flop=3 with Camera / Prompt: 'you can shoot people whilst being downed
   like that, should not be the case, and you are invulnerable, it should take a lot more shots from police but the
   heisters should have the option to shoot you normal health and kill you (gonna apply this to online later on so
   groundwork)'. NOTHING HERE HAS RUN IN THE GAME. READ = kl2.exe build 0490, each routine named read whole unless
   said; re\player_down.md 14 has the tables.

   WHY HE CAN SHOOT (READ). The buttons are read by ZGameplayInput slot 7 = 0x5fbfa0 (called by the Wintel class's
   0x484a0e; the action objects are named by the constructor 0x8bbd70 from the pointer table 0xceba78 ..):
     TapFire [H+0xa4] -> byte [H+0x2cd], HoldFire [H+0xb0] -> [H+0x2ce]: only while mask bits 0x80 AND 0x400 are clear
     Tap / HoldPrecisionAim (and the '2' pair) [H+0x74 .. +0x98] -> [H+0x2c8 .. +0x2cb]: bits 0x80 and 0x200 clear
     every other button (TapCover -> [H+0x2d3] = the GET UP / mash button, Use, Grenade, CloseCombat ...): bit 0x80
     TapReload [H+0x188] -> [H+0x2e9]: no bit at all
   and handed to the player by slot 12 (0x808bde: HoldFire -> 0x589d30 = bit 2 of [player+0xb90]; 0x808bee: TapFire
   -> 0x5e9530 = bit 1). The mask is the dword [player+0xed0] kld_mask finds. THE FALL SETS BITS 1 AND 0x10 ONLY
   (0x76a827 / 0x76a830: no move, no mouse look) - fire was never gated by it. Stock hides that: its fall is 0.72 s
   and its lying state is MEANT to shoot (0x8ee283: a fire flag late in the fall cuts it to lying). The flop made the
   fall 2 - 10 s long with fire open the whole time; R7's Camera gave him the aim back, it did not open the fire (one
   bit does not gate both: look is 0x10 / 0x20 / 0x40, fire 0x400). Section 10.2's 'he cannot shoot' was an
   ASSUMPTION of that track, never read.
   THE GAME'S OWN 'MAY NOT FIRE' is exactly these two bits: the victim of a human-shield hold gets mask bits 1, 0x200
   and 0x400 (0x860f7b / 0x860f87 / 0x860f93; taken off at 0x861099 ..) and keeps Use for his break-free.
   NoFire=1 (default 1 when Flop is set): while he is down in ANY state of the down ([D+4] not 0: the fall, lying the
   stock way after a time bound, a get-up) and alive and the round runs, bits 0x400 and 0x200 are set in that dword
   (one DWORD write; NoFire=2 = 0x400 alone: he may aim, not fire); the bits THIS part set are taken off in the pass
   that sees him up, dead, out of play, a fed, or the round over. Bits found set already are not ours and stay.
   MELEE / A HUMAN SHIELD: the close-combat target is looked for by 0x612c20 in the player's frame (0x57fc0e), and
   that routine leaves at once while [D+8] bit 0 is set (0x612d07 .. 0x612d11): a downed man starts no close combat -
   the game's own rule, nothing written. A THROW (HoldGrenade -> [H+0x2d2] -> 0x4aa410) and Use have no bit but 0x80,
   which would take the mash button too: NOT gated here. Whether a throw can start in the prone movement was NOT
   READ (live check N3 presses it); a reload hurts nobody.

   WHY HE IS INVULNERABLE (READ). The player's damage routine (slot +0x69c = 0x458880; every kind of hit ends there)
   asks 0x8da3b0(D, record) at 0x458e7f before the health changes; TRUE = the hit costs nothing (0x458e93), unless
   the hit's kind [rec+8] is 9 (a blast) or the routine's own flag byte is set (0x585de0: only with word
   [player+0xa54] bit 2 and the attacker in a narrow angle - not our state). In D state 2 the answer is 'NOT
   0x843fa0' = swallowed until the tick [M+0x8e0] has passed - and kld_flop_one holds that tick 2 s behind the clip's
   end, so the whole knock-down is free. THE TICK CANNOT BE GIVEN BACK: the same test (0x843fa0) is what lets a fire
   flag cut the fall to lying (0x8ee278 .. 0x8ee2d0) and a press of GET UP - the mash button - start the stock
   get-up in the middle of the clip (0x47cde7 .. 0x47ce4d). A per-hit wrapper needs the PLAYER's vtable (slots 72 /
   89 / 424 / +0x69c are all his), and a private vtable copy on the player changes the first dword every part of
   this hook knows a ZFFPlayer by: not done (the same finding as klbalance.c 2 a6 for the AI heisters).
   THE HANDLE THAT IS DATA: the trigger's first test is the game's own switch, dword [0xceb40c] (.data, 1 in the
   image, not in a hashed range): 0 -> 0x8da3b0 returns 0 at once = every hit goes on to the health. Its eleven
   readers, all read: 0x8da3b0 (the trigger), 0x658700 (the other starters: nothing while 0 - he is down already),
   0x724420 (D's FRAME: returns at once while 0), 0x76a450 x 2 (the down start), 0x7107b0 x 2 (the end of the state),
   0x8ee220 (2 -> 1, inside the frame), and the three state setters 0x5491d0 / 0x62db70 / 0x8c8150. So with the
   switch at 0 the down state of EVERY player of this process stands still - which is all the flop asks of the game
   while it plays its clip: kld_flop_one holds both ticks so that the frame does nothing, and ends the state itself
   by movement state 5. What still runs with the switch at 0: the prone movement's own frame (the clip), the input's
   write of the GET UP button [D+0x2b] (0x84dda0: tests only [D+8] bit 0), the damage, a death (the reset 0x88a990
   does not read the switch). What does NOT: the pause before the next down [D+0x38] is not counted down (0x724432) -
   the Cooldown seconds start when he is UP, not when he went down - and a second player's down state (none in an
   Arcade round).
   Vulnerable=1 (default 1 with Flop=1 / 3; no effect in Flop=0 / 2, whose falls the GAME ends by its frame): the
   switch is written 0 ONLY in a pass in which kld_flop_one held the fall (its heartbeat kld_r.beat: D 2, M 1, the
   clip on its channel, inside both time bounds, not dead, the round running, not Dry) AND the two factors below
   stand in the table; in every other pass it is written back to 1 FIRST THING - the pass that writes state 5 (the
   game's frame must run to end the state), a time bound, a read that failed, a death, the round's end, a police
   body, no player. So the worst a missed pass costs is one frame of the old rule. A value found there that is
   neither 1 nor this part's 0 is left alone.

   WHO HURTS HIM HOW MUCH - 'by the attacker's side', read from the hit by the game itself (READ: 0x8b8050 whole).
   A bullet's price on the player is made in his bullet routine 0x4db580: gun x body part x the record's scale x the
   attacker's soldier factor x 0x8b8050(rules, ATTACKER) (0x4db9d1). 0x8b8050 takes the Arcade level's record R =
   tuning + 0x6ac + 0x70 x level and the ATTACKER's team [[attacker+0x54]+4]: 2 (Ally: an AI heister, a traitor is
   still Ally) -> float R+0x10, anything else (police, guards) -> R+0x08; the two exchanged while player 0 is police.
   These are klbalance.c's CrewToYou and CopToYou. So the two factors are two floats:
     DownFromCop  (default 0.15 with a Flop - a GUESS, 0.25 before review 8; 1 = as if he stood)  x R+0x08 while he is down
     DownFromCrew (default 1.0 = 'normal health': a heister can finish him)  x R+0x10 while he is down
   for the whole knock-down ([D+4] not 0, alive, the round running) in every Flop mode. THE POINT-BLANK STEP (a
   guard within 1.6 m: a hundred bullets in one hit record, re\melee_damage.md) is priced by the same float, so the
   cop factor applies to it - and a hundred bullets x 0.15 still kill: under Risk=1 one step is 72 x 1.05 x 100 x
   0.5 x 0.15 = 567 of his 550. REVIEW 8, M1: so the hundred itself is capped while he is down - DownPointBlank
   (kld_pb above; default half a bullet a step = 2.8 at those numbers), written into the hit record by klbalance.c's
   wrapper (hand-over lines 4 / 5), and the switch below does not go off before that cap STANDS. A BLAST (kind 9)
   costs what it always cost in a fall (it was never swallowed; whether a blast's price reads the table was NOT
   READ). ANYTHING ELSE that reaches 0x458880 without the bullet routine (a fall, the flat 50 of close combat
   0x499570) was swallowed in the fall and now costs in full, no factor - not read which of them can reach a lying
   man; the loss line marks a loss of exactly 50.
   THE SECOND CALLER OF 0x8b8050 (review 8, S3; READ): inside the damage routine, 0x458946 (Arcade, an attacker of
   one class mask) takes the same float x 10.0 [0xb5cde8] as a THRESHOLD in place of the plain 10.0 [0xb3ef8c]: a
   hit whose damage [rec+0x28] is at least that pushes the tick [player+0x84c] on (0x458990 ..; what that tick
   times was not read - it is not the health, which is taken further down). The hit's damage carries the same
   float already (0x4db9d1), so damage and threshold move together under the down factor: which bullets cross it
   does not change. A flat hit (close combat's 50) crosses a threshold that is lower while he is down.
   WHO WRITES THE TABLE. klbalance.c compares its eleven records every 50 ms and writes back whatever differs while
   one of its keys is set (klr_table_tick) - and logs a line each time. So:
     - klbalance.c OWNS the table ([Balance] Enable=1 with Risk or a factor key - the owner's game): this part writes
       NOTHING there; klbalance.c multiplies by kld_factor() once it has the three hand-over lines, which define
       KLR_DOWN (re\player_down.md 14.5). This part then only READS the level's two floats and waits until they are
       'what they were while he was up x the factors' before the switch goes off. WITHOUT those lines (KLR_DOWN not
       defined in this build) the factors cannot stand: said at start, and the switch then stays ON - hits stay
       swallowed as before, rather than a floored man at the full price - unless both factors are 1.
     - nobody owns it: this part writes the level's two floats itself and puts back what stood there.
   ONLINE (groundwork, nothing acts there: klr_arcade): the rule is two numbers picked by the attacker's side at
   the hit, which is how it has to be online too - but the table is Arcade's (0x7f6850) and only NPC attackers are
   priced by it; a human attacker's bullet has no such float, the switch is one dword for all players of a process,
   and who prices a hit between two machines is not read (re\netcode_fa.md 8). re\player_down.md 14.6 says what a
   host-side form needs. */
#define KLD_SWITCH    0x00ceb40c             /* .data: the game's 'down not dead' switch, 1 in the image (its eleven readers: above) */
#define KLD_TABLE     0x6ac                  /* tuning: the Arcade damage records, 0x70 bytes a level (0x8b8093); +8 police -> you, +0x10 crew -> you */
#define KLD_ACTOR_VT  0x00bb3bac             /* ZFFActor */
#define KLD_MASK_FIRE 0x400                  /* TapFire / HoldFire (0x5fc02c, 0x5fc068) */
#define KLD_MASK_AIM  0x200                  /* the four precision-aim actions (0x5fc2cd .. 0x5fc37e) */

/* klbalance.c calls this from klr_table_tick once it has the hand-over lines (it declares it ahead): what the
   table's slot k is multiplied with now. Any thread: one int and two floats that never change after kld_init. */
static float kld_factor(int k)
{
    if (!kld_r.fon) return 1.0f;
    return k == 2 ? kld_r.cop : k == 4 ? kld_r.crew : 1.0f;
}

/* review 8, S6 (hand-over line 3): the down factor has just come or gone - klbalance.c counts the table writes of
   these 400 ms apart from the dial's own, so that its 'Risk=.. written' line is not printed twice a knock-down. */
static int kld_moving(void)
{
    DWORD now = GetTickCount();
    return (kld_r.t_fon && now - kld_r.t_fon < 400) || (kld_r.t_foff && now - kld_r.t_foff < 400);
}

/* review 8, M1. THE POINT-BLANK STEP ON A FLOORED MAN. A soldier whose target is within 160 units sends, at every
   burst step, ONE hit worth a hundred bullets of his gun (kl2 0x8c62e0, re\melee_damage.md). The cop factor prices
   it, and a hundred bullets x 0.15 still kill a man who lies with 80 .. 220: before Vulnerable the fall swallowed
   that step, with it he would be dead at once beside any guard. DownPointBlank=N (default 0.5 with a Flop - a GUESS:
   the guard beside him is a guard who fires - a step comes every 0.12 .. 0.19 s, about twice his gun's own rate, so
   half a bullet a step at the floor's price; a negative number = the step is left alone) is what the hundred becomes ON THE PLAYER while he is down. The hit record is klbalance.c's to
   write (its wrapper of the database's name look-up, section 2 a4 there): hand-over line 4 asks kld_pb() for the
   scale of a step on a ZFFPlayer, line 5 puts the wrapper in although no [Balance] PointBlank key is set. A
   PointBlankToYou that is smaller stays. Called from inside the game's fire task (ASSUMED the main loop's thread,
   as klbalance.c assumes; one int and one float of this part's own are read, one counter is added to). */
static float kld_pb(float want)
{
    if (!kld_r.pbon || kld_r.pb < 0) return want;
    if (want >= 0 && want <= kld_r.pb) return want;
    InterlockedIncrement(&kld_r.npb);
    return kld_r.pb;
}

/* The key as kld_init reads it, straight from the ini: klbalance.c's init asks before this part's own has run
   (hand-over line 5). < 0 = no cap. */
static float kld_pb_ini(void)
{
    int flop = (int)GetPrivateProfileIntA("Down", "Flop", 0, klh_ini); char t[32]; float v;
    if (!GetPrivateProfileIntA("Down", "Enable", 0, klh_ini)) return -1.0f;
    GetPrivateProfileStringA("Down", "DownPointBlank", flop >= 1 && flop <= 3 ? "0.5" : "-1", t, sizeof t, klh_ini);
    v = (float)atof(t);
    return v != v || v < 0 ? -1.0f : v > 100.0f ? 100.0f : v;
}
static int kld_pb_key(void) { return kld_pb_ini() >= 0; }

/* The cap can act NOW: this build's klbalance.c has lines 4 / 5 (KLR_DOWN 2), its wrapper is armed and its copy of
   the vtable is the one in the game's database object (klr_pb_tick's own reads). */
static int kld_pb_stands(void)
{
#if defined(KLR_DOWN) && KLR_DOWN >= 2
    DWORD sys, db;
    return klr.on && klr_pb.any && klr_pb.ready && klr_pb.act && (sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) != 0 && (db = klh_rd32(sys + 0xac)) != 0 &&
           klh_rd32(db) == (DWORD)(DWORD_PTR)&klr_pb.vt[1];
#else
    return 0;
#endif
}

/* klbalance.c compares and rewrites the table while it is on with a key set (klr_tick, klr_table_tick): read only */
static int kld_owned(void) { return klr.on && klr.any; }

/* The switch back to the image's 1. The game thread's passes; and the fallback thread when the game thread has made
   no pass for 500 ms (review 8, S1: the factors and the cap are dropped there, so the switch must not stay off
   behind them - one aligned dword of .data that the game only compares). */
static void kld_sw_back(DWORD now, const char *why)
{
    DWORD sw = 0xffffffff, one = 1;
    if (!kld_r.sw) return;
    if (klh_rd((DWORD_PTR)KLH_VA(KLD_SWITCH), &sw, 4) && sw == 0) klh_data((void *)KLH_VA(KLD_SWITCH), &one, 4, "the game's 'down not dead' switch, back to the image's 1");
    kld_r.sw = 0; kld_r.ms_hurt += now - kld_r.t_sw;
    if (kld_r.swn <= 3 || kld.log >= 2) klog("down: rules: the game's 'down not dead' switch [0xceb40c] is back at 1 after %.2f s (%s; it read %lu) - from here the game's own rules of the down state run again", (now - kld_r.t_sw) / 1000.0f, why, sw);
}

static int kld_near(float a, float b) { return KLD_ABS(a - b) <= 0.0005f * (1.0f + KLD_ABS(b)); }

/* One pass, after kld_tick_main (which left act / pl / state in kld_v, the level and kld_flop_one's heartbeat in
   kld_r, the dead flag and the fall's flags in kld_s). Game thread only. */
static void kld_rules(DWORD now)
{
    static const DWORD off[2] = { 8, 0x10 };
    DWORD pl = kld_v.act ? kld_v.pl : 0, d = 0, ds = 0, ho = 0, tun, R = 0, sw = 0xffffffff, zero = 0;
    float hp = 0, max = 0, cur[2] = { 0, 0 }, want[2]; int down, hpok = 0, need, tok = 0, k, owned = kld_owned(), hurtw, held, pbok; const char *why = "";
    if (!kld.on || !klh_exe_ok) return;
    need = kld_r.cop != 1.0f || kld_r.crew != 1.0f;
    if (!kld_r.nofire && !kld_r.hurt && !need && !kld_r.mbits && !kld_r.sw && !kld_r.fon && !kld_r.w[0].at && !kld_r.w[1].at && !kld_r.was && kld_r.pb < 0 && !kld_r.pbon && !kld_r.nothrow) return;
    if (pl && (!(d = klh_rd32(pl + 0x2948)) || klh_rd32(d) != pl || !klh_rd(d + 4, &ds, 4))) pl = 0;
    down = pl && ds != 0 && !kld_s.dead && !kld.dry && kld_v.state == KLD_ROUND;
    if (pl && (ho = klh_rd32(pl + 0xa48)) != 0) { int ok = 1; hp = kld_rdf(ho + 4, &ok); max = kld_rdf(ho + 8, &ok); hpok = ok; }
    if (!pl || ds == 0) kld_r.beat = 0;        /* no heartbeat of an earlier down counts */
    why = !pl ? "the part does not act here (no player, a police body, a stock level, no Arcade session)" : ds == 0 ? "he is up" : kld_s.dead ? "he is dead or out of play" :
          kld_v.state != KLD_ROUND ? "the round does not run any more" : kld.dry ? "Dry=1" : "";

    /* 3. VULNERABLE, the half that must never be late: the switch back to 1 before anything else of this pass */
    /* review 8, M1: the point-blank cap is wanted for the whole down (before the switch can go off below), and
       Vulnerable waits for it to STAND - a floored man without it is dead at one step of a guard beside him */
    InterlockedExchange(&kld_r.pbon, down && kld_r.pb >= 0 ? 1 : 0);
    pbok = kld_r.pb < 0 || kld_pb_stands();
    held = kld_r.hurt && down && KLD_ONE && ds == 2 && kld_s.fnow && !kld_s.fdone && !kld_s.flost && kld_r.beat && kld_r.beat == kld_r.pass;
    hurtw = held && pbok;
    if (kld_r.sw && (!hurtw || (need && !kld_r.stand)))
        kld_sw_back(now, why[0] ? why : kld_s.fdone == 1 ? "the clip is through and movement state 5 is written: the game's own frame must run to end the down state" :
                         kld_s.fdone ? "this part gave the fall back to the game (a time bound, FlopUp, the channel)" : kld_s.flost ? "the game left the fall" :
                         held && !pbok ? "the point-blank cap does not stand any more (klbalance.c's wrapper is out)" :
                         need && !kld_r.stand ? "the two factors do not stand in the table any more" : "this pass did not hold the fall (a read of the channel failed, or it is not a fall this part drives)");
    if (held && !pbok && !kld_r.pbtold) {
        kld_r.pbtold = 1;
#if defined(KLR_DOWN) && KLR_DOWN >= 2
        klog("down: rules: Vulnerable: THE POINT-BLANK CAP DOES NOT STAND (DownPointBlank=%.2f; klbalance.c's wrapper of the database object is %s): hits stay SWALLOWED in this fall, as before review 8 - a guard within 1.6 m would take the lying man in one step. It needs [Balance] Enable=1 on this round; DownPointBlank=-1 = let him be hurt without the cap",
             kld_r.pb, !klr.on ? "off ([Balance] Enable=0)" : !klr_pb.any ? "not asked for (hand-over line 5 did not see the key)" : !klr_pb.ready || !klr_pb.act ? "not in yet (does the dial act on this level?)" : "not the vtable in the object");
#else
        klog("down: rules: Vulnerable: THE POINT-BLANK CAP CANNOT STAND (DownPointBlank=%.2f): this build's klbalance.c has not got hand-over lines 4 / 5 (KLR_DOWN 2, re\\player_down.md 14.5): hits stay SWALLOWED in this fall, as before review 8. DownPointBlank=-1 = let him be hurt without the cap", kld_r.pb);
#endif
    }

    /* the log of one knock-down: its start */
    if (down && !kld_r.was) {
        kld_r.was = 1; kld_r.t0 = now; kld_r.hp0 = kld_r.hplast = hp; kld_r.lost = 0; kld_r.nloss = kld_r.nline = 0; kld_r.swn = 0; kld_r.ms_hurt = 0; kld_r.swtold = 0; kld_r.mn = 0; kld_r.mtold = 0;
        kld_r.pbtold = 0; kld_r.nthrow = 0; InterlockedExchange(&kld_r.npb, 0);
    }

    /* review 8, S2 - NoThrow, a TEST key (default 0). The throw button reaches the player as bit 0x40 of
       [player+0xb90] and is copied to bit 0x800 of his action word [player+0x818] by 0x544780 (READ); the game takes
       both off when the button is up (0x4aa417, 0x544805). WHERE a throw starts from that bit was NOT FOUND (no
       reader by byte scan), so whether one can start in the prone movement is not read - live check N3. This key
       writes the 'button up' form of both in every pass while he is down. ASSUMED that this hook's tick comes
       between the input read and the routine that starts the throw; if N3b still throws, it does not. */
    if (kld_r.nothrow && down) {
        DWORD b = 0, a = 0, nb, na;
        if (klh_rd(pl + 0xb90, &b, 4) && klh_rd(pl + 0x818, &a, 4) && ((b & 0x40) || (a & 0x800))) {
            nb = b & ~0x40u; na = a & ~0x800u;
            if ((nb == b || klh_data((void *)(DWORD_PTR)(pl + 0xb90), &nb, 4, "the player's buttons: the throw button is up while he is knocked down (NoThrow; as 0x4aa417)")) &&
                (na == a || klh_data((void *)(DWORD_PTR)(pl + 0x818), &na, 4, "the player's action word: no throw asked while he is knocked down (NoThrow; as 0x544805)")) && !kld_r.nthrow++)
                klog("down: rules: NoThrow: the throw button was down %.2f s after he went down: buttons [player+0xb90] %08lx -> %08lx, action word [player+0x818] %08lx -> %08lx (and in every pass of this down in which it is found again) - a TEST key: does anything fly?", (now - kld_r.t0) / 1000.0f, b, nb, a, na);
        }
    }

    /* 1. NO FIRE: the game's own two bits of a man who may not shoot (0x860f87 / 0x860f93), while he is down */
    {
        DWORD ma = 0, mv = 0, nv, bits = kld_r.nofire == 2 ? KLD_MASK_FIRE : (KLD_MASK_FIRE | KLD_MASK_AIM);
        if (kld_r.nofire && down) {
            if (!kld_mask(pl, &ma, &mv)) { if (!kld_r.mtold) { kld_r.mtold = 1; klog("down: rules: NoFire: NO INPUT OBJECT for this player (the lookup of 0x61ef90 finds none): nothing is masked - he can fire in this down"); } }
            else {
                if (kld_r.mbits && (kld_r.mpl != pl || kld_r.mat != ma)) { klog("down: rules: NoFire: the bits %lx this part set on player %08lx (mask %08lx) are another object's now: dropped unwritten", kld_r.mbits, kld_r.mpl, kld_r.mat); kld_r.mbits = 0; }
                if ((mv & bits) != bits) {
                    if (kld_r.mbits && kld_r.mn >= 6) { if (!kld_r.mtold) { kld_r.mtold = 1; klog("down: rules: NoFire: somebody takes the bits off the input mask %08lx again and again (%d times in this down): left to them - he can fire", ma, kld_r.mn); } }
                    else {
                        nv = mv | bits;
                        if (klh_data((void *)(DWORD_PTR)ma, &nv, 4, "the player's input object: the game's own 'no fire' / 'no aim' mask bits (0x400, 0x200: what a human-shield hold sets on its victim, 0x860f87)")) {
                            kld_r.mbits |= bits & ~mv; kld_r.mpl = pl; kld_r.mat = ma; kld_r.mn++; kld_r.t_mlost = 0;
                            if (kld_r.mn == 1 || kld.log >= 2) klog("down: rules: NoFire: the input mask %08lx: %08lx -> %08lx %.2f s after he went down (bit 0x400 = TapFire / HoldFire are not read, 0x5fc02c / 0x5fc068%s; the GET UP button, Use and the look stay) - until he is up%s",
                                                                     ma, mv, nv, (now - kld_r.t0) / 1000.0f, bits & KLD_MASK_AIM ? "; bit 0x200 = the precision aim is not read" : "; NoFire=2: he may aim", kld_r.mn > 1 ? " - SET AGAIN in this down: somebody had taken it off" : "");
                        }
                    }
                }
            }
        } else if (kld_r.mbits) {              /* ours come off: he is up / dead / out of play / a fed / the round is over */
            if (!kld_v.pl) {                   /* no local player object this pass (a load, the menu): tried for 3 s, then the object is taken as gone */
                if (!kld_r.t_mlost) kld_r.t_mlost = now;
                if (now - kld_r.t_mlost >= 3000) { klog("down: rules: NoFire: no local player object for 3 s: the bits %lx on player %08lx are dropped unwritten (the object went with its level)", kld_r.mbits, kld_r.mpl); kld_r.mbits = 0; kld_r.t_mlost = 0; }
            } else if (kld_v.pl != kld_r.mpl || !kld_mask(kld_r.mpl, &ma, &mv) || ma != kld_r.mat) {
                klog("down: rules: NoFire: the local player is %08lx now, the bits %lx were set on %08lx (mask %08lx): dropped unwritten (another object, or another input object for it: this part writes only where it set them)", kld_v.pl, kld_r.mbits, kld_r.mpl, kld_r.mat);
                kld_r.mbits = 0; kld_r.t_mlost = 0;
            } else {
                nv = mv & ~kld_r.mbits;
                if (nv == mv || klh_data((void *)(DWORD_PTR)ma, &nv, 4, "the player's input object: this part's 'no fire' / 'no aim' bits off (as the game takes them off a freed shield victim, 0x861099)"))
                    klog("down: rules: NoFire: off (%s): the input mask %08lx: %08lx -> %08lx%s", why[0] ? why : "the down is over", ma, mv, nv, (nv & (KLD_MASK_FIRE | KLD_MASK_AIM)) ? " - BITS 0x600 STILL STAND: they were set before this part's write and are somebody else's" : "");
                kld_r.mbits = 0; kld_r.t_mlost = 0;
            }
        }
    }

    /* 2. THE FACTORS: the level's police -> you (+8) and crew -> you (+0x10) while he is down */
    if ((tun = klh_rd32((DWORD_PTR)KLH_VA(KLD_TUNING))) != 0 && kld_r.level >= 1 && kld_r.level <= 11) {
        R = tun + KLD_TABLE + 0x70 * (DWORD)kld_r.level;
        tok = klh_rd(R + 8, &cur[0], 4) && klh_rd(R + 0x10, &cur[1], 4) && kld_fin(cur[0]) && kld_fin(cur[1]) && cur[0] >= 0 && cur[0] <= 50 && cur[1] >= 0 && cur[1] <= 50;      /* klbalance.c's own test of a factor */
    }
    if (!down || !need) {
        int nb = 0, nl = 0;
        if (kld_r.fon) { kld_r.fon = 0; kld_r.t_foff = now; }
        for (k = 0; k < 2; k++) if (kld_r.w[k].at) {      /* what this part wrote itself goes back - only while it still reads as written */
            float c = 0;
            if (klh_rd(kld_r.w[k].at, &c, 4) && c == kld_r.w[k].put && klh_data((void *)(DWORD_PTR)kld_r.w[k].at, &kld_r.w[k].old, 4, "the Arcade damage table: a factor on the player, as it stood before he went down")) nb++; else nl++;
            kld_r.w[k].at = 0;
        }
        if (nb || nl) klog("down: rules: the damage table has its own police -> you / crew -> you again (%d value(s) put back%s)", nb, nl ? "; one did not read as this part left it and was LEFT ALONE" : "");
        if (pl && ds == 0 && tok && (!kld_r.t_foff || now - kld_r.t_foff >= 300)) { kld_r.up[0] = cur[0]; kld_r.up[1] = cur[1]; kld_r.upR = R; kld_r.uphave = 1; }      /* 300 ms: klbalance.c's own put-back is 50 ms + a frame behind */
        kld_r.stand = 0; kld_r.standtold = 0; kld_r.unverified = 0;
    } else {
        if (!kld_r.fon) {
            kld_r.fon = 1; kld_r.t_fon = now; kld_r.stand = 0; kld_r.standtold = 0; kld_r.unverified = 0;
            if (!kld_r.uphave || kld_r.upR != R) {       /* he went down before the table was seen with him up (the first passes of a round) */
                kld_r.uphave = 0;
                if (!owned && tok) {                     /* nobody else writes it: what stands there now is the level's own - unless it is still ours */
                    for (k = 0; k < 2; k++) kld_r.up[k] = kld_r.w[k].at == R + off[k] && cur[k] == kld_r.w[k].put ? kld_r.w[k].old : cur[k];
                    kld_r.upR = R; kld_r.uphave = 1;
                }
            }
        }
        want[0] = kld_r.up[0] * kld_r.cop; want[1] = kld_r.up[1] * kld_r.crew;
        if (!owned) {
            int bad = !tok || !kld_r.uphave;
            for (k = 0; k < 2 && !bad; k++) {
                if (kld_near(cur[k], want[k])) continue;
                if (!klh_data((void *)(DWORD_PTR)(R + off[k]), &want[k], 4, k ? "the Arcade damage table: crew -> you while he is knocked down (DownFromCrew)" : "the Arcade damage table: police -> you while he is knocked down (DownFromCop)")) { bad = 1; break; }
                if (kld_r.w[k].at != R + off[k]) { kld_r.w[k].at = R + off[k]; kld_r.w[k].old = kld_r.up[k]; }
                kld_r.w[k].put = want[k];
            }
            kld_r.stand = !bad;
        } else {
#ifdef KLR_DOWN
            if (tok && kld_r.uphave) kld_r.stand = kld_near(cur[0], want[0]) && kld_near(cur[1], want[1]);
            else if (now - kld_r.t_fon >= 200) { kld_r.stand = 1; kld_r.unverified = 1; }      /* nothing to compare with: klbalance.c has had four of its passes */
#else
            kld_r.stand = 0;                   /* klbalance.c owns the table and this build's has not got the hand-over lines: said at start */
#endif
        }
        if (kld_r.stand && kld_r.standtold != 1) {
            kld_r.standtold = 1;
            klog("down: rules: %.2f s after he went down the damage table of Arcade level %d holds police -> you %.3f (x %.2f DownFromCop of the %.3f it held while he was up) and crew -> you %.3f (x %.2f DownFromCrew of %.3f) - %s%s; the game picks one of the two by the ATTACKER's team at every bullet (0x8b8050), a point-blank step is a hundred bullets at that price",
                 (now - kld_r.t0) / 1000.0f, kld_r.level, cur[0], kld_r.cop, kld_r.up[0], cur[1], kld_r.crew, kld_r.up[1],
                 owned ? "written by klbalance.c (its keys own the table; kld_factor)" : "written by this part (no [Balance] key owns the table)", kld_r.unverified ? " - NOT VERIFIED: the table was never seen with him up on this level, the numbers are what stands there now" : "");
        } else if (!kld_r.stand && !kld_r.standtold && now - kld_r.t_fon >= 1000) {
#ifdef KLR_DOWN
            const char *ow = "klbalance.c owns the table and has not written them (does its dial act on this level?)";
#else
            const char *ow = "klbalance.c owns the table ([Balance] keys) and THIS BUILD'S klbalance.c HAS NOT GOT THE THREE HAND-OVER LINES (KLR_DOWN, re\\player_down.md 14.5)";
#endif
            kld_r.standtold = 2;
            klog("down: rules: THE FACTORS DO NOT STAND 1 s after he went down: Arcade level %d holds police -> you %.3f, crew -> you %.3f; wanted %.3f (x %.2f) and %.3f (x %.2f) - %s. Hits stay SWALLOWED in the fall (the switch is not taken off), and lying the stock way he pays the full price",
                 kld_r.level, cur[0], cur[1], want[0], kld_r.cop, want[1], kld_r.crew,
                 !tok ? "the table cannot be read where this build expects it" : owned ? ow : !kld_r.uphave ? "the table was never seen with him up" : "this part's write was refused");
        }
    }

    /* review 8, S1: 'stand' is this pass's now - the test at the top had last pass's. A switch that is off while the
       table has lost the factors (klbalance.c wrote the standing price back on the fallback thread) goes back here */
    if (kld_r.sw && need && !kld_r.stand) kld_sw_back(now, "the two factors do not stand in the table any more (seen after this pass's read of it)");

    /* 3. VULNERABLE, the other half: the switch off - only in a pass that held the fall, with the factors in place */
    if (hurtw && (!need || kld_r.stand) && !kld_r.sw) {
        if (!klh_rd((DWORD_PTR)KLH_VA(KLD_SWITCH), &sw, 4) || sw != 1) {
            if (!kld_r.swtold) { kld_r.swtold = 1; klog("down: rules: Vulnerable: the game's switch [0xceb40c] reads %lu, not the image's 1: left alone - hits stay swallowed in this fall", sw); }
        } else if (klh_data((void *)KLH_VA(KLD_SWITCH), &zero, 4, "the game's 'down not dead' switch: 0 while this part holds the fall, so that its trigger swallows no hit (0x8da3bd)")) {
            kld_r.sw = 1; kld_r.t_sw = now; kld_r.swn++;
            if (kld_r.swn <= 3 || kld.log >= 2) klog("down: rules: Vulnerable: %.2f s after he went down the game's 'down not dead' switch [0xceb40c] 1 -> 0%s: the trigger 0x8da3b0 swallows nothing, EVERY HIT COSTS from here (health %.1f of %.1f); the down state's own frame stands still while this part plays the clip, and the switch goes back in the pass that ends it",
                                                     (now - kld_r.t0) / 1000.0f, kld_r.swn > 1 ? " (again in this down)" : "", hp, max);
        }
    }

    /* the log of one knock-down: what he lost and to whom, its end */
    if (down && hpok) {
        if (hp < kld_r.hplast - 0.05f) {
            float dl = kld_r.hplast - hp; kld_r.lost += dl; kld_r.nloss++;
            if (kld.log >= 2 || kld_r.nline < 8) {
                DWORD att = klh_rd32(pl + 0x2778), avt = att ? klh_avt(att) : 0, team = 99, sc; const char *who = "nobody yet / not readable";
                kld_r.nline++;
                if (avt == KLD_ACTOR_VT) { if ((sc = klh_rd32(att + 0x54)) != 0) klh_rd(sc + 4, &team, 4); who = team == 2 ? "an AI HEISTER (team Ally: the crew -> you float, DownFromCrew)" : "POLICE / a guard (not team Ally: the police -> you float, DownFromCop)"; }
                else if (avt == KLD_PLAYER_VT) who = "a human player (no float of the table prices him)";
                klog("down: rules: he lost %.1f on the floor (%.1f of %.1f; down state %lu, %.2f s after he went down); the last BULLET's attacker [player+0x2778] = %08lx is %s (team %lu); the table holds police -> you %.3f, crew -> you %.3f; the switch is %s; %ld point-blank step(s) capped so far%s%s",
                     dl, hp, max, ds, (now - kld_r.t0) / 1000.0f, att, who, team, cur[0], cur[1], kld_r.sw ? "off (hits cost)" : "on", (long)kld_r.npb,
                     KLD_ABS(dl - 50.0f) < 0.11f ? " - EXACTLY 50: the flat price of close combat (0x499570), which no factor of this part scales (review 8, S7: is the attacker beside him and not firing?)" : "",
                     kld_r.nline == 8 && kld.log < 2 ? " - further losses of this down are only counted (Log=2 lists them)" : "");
            }
        }
        kld_r.hplast = hp;
    }
    if (!down && kld_r.was) {
        kld_r.was = 0;
        klog("down: rules: this knock-down is over after %.2f s (%s): %d loss(es) of health, %.1f in all (%.1f when he went down, %.1f now); hits could cost for %.2f s of it (the switch was taken off %d time(s)); %ld point-blank step(s) on him were capped to %.2f bullet(s); fire %s",
             (now - kld_r.t0) / 1000.0f, why[0] ? why : "over", kld_r.nloss, kld_r.lost, kld_r.hp0, hp, kld_r.ms_hurt / 1000.0f, kld_r.swn, (long)kld_r.npb, kld_r.pb, kld_r.nofire ? "was masked" : "was open (NoFire=0)");
        /* review 8, S5 - CooldownCredit (default 1). The pause before the next down is the float [D+0x38], counted
           down by D's frame (0x724432: minus the frame's seconds, not below 0) - which stood still while the switch
           was off, so the pause would start when he is UP and a man who stands hurt could not be floored again for
           the whole Cooldown. The seconds the switch was off are taken from it here, once, when he is up: the pause
           then runs from the knock-down's start as it did before Vulnerable. One float of his down object. */
        if (kld_r.cdfix && pl && ds == 0 && !kld_s.dead && kld_r.ms_hurt) {
            int ok = 1; float c = kld_rdf(d + 0x38, &ok), n = c - kld_r.ms_hurt / 1000.0f;
            if (ok && kld_fin(c) && c > 0 && c <= 600.0f) {
                if (n < 0) n = 0;
                if (klh_data((void *)(DWORD_PTR)(d + 0x38), &n, 4, "the down state: the pause before the next down, less the seconds its frame stood still (CooldownCredit)"))
                    klog("down: rules: CooldownCredit: the pause before the next down [D+0x38] %.2f -> %.2f s (the %.2f s the down state's frame stood still in this knock-down are taken off: the pause counts from when he went down, as before Vulnerable)", c, n, kld_r.ms_hurt / 1000.0f);
            }
        }
    }
}

/* [Down] Floor=1: arm / disarm the floor (see kld_fl) and log every step of his health that is a hit while it matters.
   Called once a pass with a valid player object d. The ATTACKER'S TEAM IS NOT LOGGED: the hit record is only reachable
   through a soldier vtable wrapper (klbalance.c's note on slot 96), which this file does not install. */
static void kld_floor(DWORD pl, DWORD d, DWORD ds, float hp, float max, int hpok, DWORD now)
{
    float cd = 0; int ok = 1, want, avail;
    if (!kld_floor_on) return;
    if (kld_fl.pl != pl) { memset(&kld_fl, 0, sizeof kld_fl); kld_fl.pl = pl; kld_fl.hp = hp; }
    cd = kld_rdf(d + 0x38, &ok);
    avail = ok && cd <= 0.0f;                                       /* [D+0x38] has run out = off cooldown (the game's own test, 0x8da3b0) */
    want = hpok && ds == 0 && avail && hp > 0.01f && hp / max * 100.0f <= kld_floor_pct;
    if (hpok && kld_fl.hp - hp >= 1.0f && (kld_fl.armed || want || hp <= 0.01f || kld_fl.was))
        klog("down: floor: a hit of %.1f health (%.1f -> %.1f of %.1f), %s, cooldown %s%s, down state %lu; the attacker is not known to this part%s",
             kld_fl.hp - hp, kld_fl.hp, hp, max, kld_fl.armed ? "the floor was armed" : "the floor was NOT armed", ok ? (avail ? "over" : "running") : "unreadable",
             ok ? "" : " (the pause [D+0x38] could not be read)", ds, hp <= 0.01f && ds == 0 ? ": THIS HIT KILLED HIM without a knock-down" : "");
    if (want != kld_fl.armed) {
        kld_fl.armed = want; kld_fl.t_arm = now;
        klog("down: floor: %s (health %.1f of %.1f, line %.0f %%): %s", want ? "ARMED" : "off", hp, max, kld_floor_pct,
             want ? "the next hit floors him (HealthPct 100, Burst 1, MinHit 1 written by the tuning pass)" : "the game's trigger numbers go back");
    }
    kld_fl.was = want; kld_fl.hp = hp; kld_fl.last = now;
}

static void kld_tick_main(int game_thread)
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
    kld_v.act = act; kld_v.pl = pl; kld_v.state = state;      /* track R7: for the camera / prompt pass (kld_tick) */
    kld_r.level = level;                       /* track R8: the level's record of the damage table (kld_rules) */
    if (pl && (h = klh_rd32(pl + 0xa48)) != 0) { ho = h; hp = kld_rdf(h + 4, &ok); max = kld_rdf(h + 8, &ok); } else ok = 0;
    hpok = ok && max >= 1.0f;
    kld_tuning(act, ok ? max : 0.0f);
    if (!act || !pl) {
        kld_fl.armed = 0; kld_fl.pl = 0;                            /* Floor: the numbers go back in the next tuning pass */
        if (kld_s.player) {
            if (kld.flop) kld_flop_words(kld_s.player, 0, 0);       /* the slot ids of the object we wrote go back while it still lives */
            kld_s.player = 0; kld_drop(); kld_s.dstate = 0; kld_s.nwin = 0; kld_s.fchk = kld_s.fok = kld_s.fhave = kld_s.fput = 0; kld_s.fwf = kld_s.fwu = 0;
        }
        return;
    }
    if (!(d = klh_rd32(pl + 0x2948)) || klh_rd32(d) != pl || !klh_rd(d + 4, &ds, 4) || !klh_rd(d + 8, &flag, 1) || !klh_rd(d + 0x2b, &btn, 1)) return;
    if (pl != kld_s.player) {                  /* a new round, another level, another body: nothing is carried over */
        if (kld_s.player && kld_s.up) klog("down: the player object changed %.2f s into a get-up this part drove (a death, a new round, another body): not an UP", (now - kld_s.t_up) / 1000.0f);
        if (kld.flop && kld_s.player) kld_flop_words(kld_s.player, 0, 0);
        kld_s.player = pl; kld_drop(); kld_s.dstate = ds; kld_s.btn = btn; kld_s.hp = hp; kld_s.nwin = 0; kld_s.cool = 0; kld_s.downs = 0;
        kld_s.t_down = kld_s.t_lie = kld_s.t_up = now;
        kld_s.fchk = kld_s.fok = kld_s.fhave = kld_s.fput = 0; kld_s.fwf = kld_s.fwu = 0;
    }
    kld_floor(pl, d, ds, hp, max, hpok, now);
    if (kld.flop) {                            /* the belly flop: his prone movement's slot ids, while he is up */
        /* review2 S3: klchar.c's body swap keeps the player object and gives it another set - the verdict (full-body, the
           events) is of the set it was made on. Looked at again while he is up when one of the three pointers changed */
        if (kld_s.fchk && ds == 0 && (klh_rd32(pl + 0x78) != kld_s.fset[0] || klh_rd32(pl + 0x7c) != kld_s.fset[1] || klh_rd32(pl + 0x80) != kld_s.fset[2])) {
            klog("down: flop: the player %08lx has another animation set / slot table than the flop was checked on (a body swap): checked again", pl);
            kld_s.fchk = 0;
        }
        if (!kld_s.fchk) { if (kld.flop == 3) kld_mix_check(pl); else kld_flop_check(pl); }
        kld_flop_words(pl, ds, 1);
        if (!kld_s.fok && kld_s.fput && ds == 0) kld_flop_words(pl, 0, 0);      /* no flop any more on this body: the game's own ids go back */
    }
    if (kld.dry && ok) kld_estimate(hp, max, now, ds == 0);
    if (ds != kld_s.dstate) {
        if (kld_s.dstate == 0) {
            kld_s.t_down = kld_s.t_lie = now; kld_s.downs++; kld_drop();
            klh_rd(pl + 0x460, pos, 12);                             /* his feet (kljoin.c) */
            kld_s.p0[0] = pos[0]; kld_s.p0[1] = pos[1]; kld_s.p0[2] = pos[2];
            { float bk[3]; kld_s.pnok = kld.flop == 3 && klq_node(klh_rd32(pl + 4), kld_s.pn, bk); }      /* review6 M2: his node's place (reads) */
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
            else if (KLD_ONE && kld_s.fnow && kld_s.fdone == 1 && hp > 0.01f) {
                DWORD ma = 0, mv = 0; int mk = kld_mask(pl, &ma, &mv);      /* review3 M1: he must stand UNMASKED */
                klog("down: flop: UP after %.2f s: the dive took %.2f s, lying and rising %.2f s, %d press(es) in it, mean speed %.2f; health %.1f (%.1f at the landing); the input mask %08lx holds %08lx%s",
                     (now - kld_s.t_down) / 1000.0f, ((kld_s.t_land ? kld_s.t_land : now) - kld_s.t_down) / 1000.0f, kld_s.t_land ? (now - kld_s.t_land) / 1000.0f : 0.0f, kld_s.presses, kld_s.nr ? kld_s.sumr / kld_s.nr : 0.0f, hp, kld_s.hp_up,
                     ma, mv, !mk ? " (no input object)" : (mv & KLD_MASK_FALL) ? " - THE FALL'S BITS (0x11) ARE SET ON A MAN WHO IS UP: he cannot do what the fall forbade; say so to the lead (nothing more is written)" : " (the fall's bits 0x11 are off)");
                if (kld.flop == 3 && kld_s.fmi >= 0 && kld_s.fmi < kld_mx.n && klh_rd(pl + 0x460, pos, 12)) {      /* track R6: where the clip's root put him - the measure for 'a wall stops it' */
                    /* review6 M2: by his NODE when both ends were read (the floats at +0x460 are printed beside it),
                       and against what the game's ALIGNMENT alone makes of the clip - an aligned dive is short in the
                       open too, so 'shorter than the clip' says nothing about a wall there. The 0.5 m margin is a GUESS. */
                    float nd[3], bk[3]; int nok = kld_s.pnok && klq_node(klh_rd32(pl + 4), nd, bk); const float *a = nok ? kld_s.pn : kld_s.p0, *b = nok ? nd : pos;
                    float dx = b[0] - a[0], dz = b[2] - a[2], dy = b[1] - a[1], mv2 = (float)sqrt(dx * dx + dz * dz), own = kld_mx.e[kld_s.fmi].fwd;
                    float fx = pos[0] - kld_s.p0[0], fz = pos[2] - kld_s.p0[2], mvf = (float)sqrt(fx * fx + fz * fz);
                    float want = kld_s.fal ? kld_s.fad + kld_md[kld_mx.e[kld_s.fmi].def].after * 100.0f : own; BYTE con = 0xff; DWORD coff = 0xffffffff;
                    klh_rd(pl + 0x7a5, &con, 1); klh_rd(pl + 0x7b4, &coff, 4);
                    klog("down: flop: he stands %.2f m from where he went down (%.2f m %s; %s; the floats at +0x460 say %.2f m); the clip alone goes %.2f m forward; %s %.2f m%s%s; his collision [player+0x7a5] is %u, the off count %lu",
                         mv2 / 100.0f, KLD_ABS(dy) / 100.0f, dy < 0 ? "lower" : "higher", nok ? "by his node" : "by the floats at +0x460: his node was not readable", mvf / 100.0f, own / 100.0f,
                         kld_s.fal ? "THE GAME ALIGNED THIS FALL: the align place + the clip's travel after the align frame =" : "not aligned: expected the clip's own", want / 100.0f,
                         mv2 < want - 50.0f ? (kld_s.fal ? " - SHORTER THAN THE ALIGNMENT EXPLAINS: something stopped him (a wall, a prop) - or the align place was not reached" : " - SHORTER: something stopped him (a wall, a prop)")
                                            : (kld_s.fal && own > 100.0f && mv2 < 0.6f * own ? " - shorter than the clip, AS THE ALIGNMENT ALONE EXPLAINS: this line says nothing about a wall (compare the same clip in the open: W1)" : ""),
                         dy < -100.0f ? " - HE WENT DOWN OVER AN EDGE: say so to the lead (FlopReach)" : "",
                         (unsigned)con, coff);
                }
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
            kld_mix_next(pl, "the down state is over: he is up");   /* Flop=3: the next fall's clip, in the pass that saw him up */
        }
        kld_s.dstate = ds;
    }
    if (btn && !kld_s.btn && (kld_s.up || (KLD_ONE && kld_s.fnow && kld_s.t_land && !kld_s.fdone))) { kld_s.meter += 1.0f; kld_s.presses++; }
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
    if (KLD_ONE && ds != 0) kld_flop_one(pl, d, ds, now, hp);
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
        rate = B + P * kld_s.meter; if (rate > T) rate = T; rate /= kltt_get(-1, KLTT_REVIVE); if (rate < 0.05f) rate = 0.05f;      /* kltrait.c ReviveTime: x time to get up */
        kld_s.sumr += rate; kld_s.nr++; kld_v.rate = rate;
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

/* The part's tick (klhook.c calls this): everything above, then the camera and the prompt (track R7) from what that
   pass left in kld_s - one place, after every early return of kld_tick_main, so the prompt goes off whatever way a
   down ends. Game thread only, as every write of this file. */
static void kld_tick(int game_thread)
{
    DWORD pl, d, ds = 0, now;
    if (!game_thread) {                        /* the fallback thread (no frame for 500 ms: a load, a stall). Track R8: klbalance.c may tick there and
                                                  asks kld_factor() - a factor must not outlive the passes that keep it (one int of this part's own) */
        /* review 8, S1: the switch first - with the factors and the cap dropped here, a first frame after the stall
           would otherwise price him in full (and a point-blank step at a hundred bullets) with the switch still off.
           The one write of this file off the game thread: an aligned dword of .data the game only compares, made
           only when the game thread has not ticked for 500 ms. */
        if (kld_r.sw) kld_sw_back(GetTickCount(), "the game thread has made no pass for 500 ms (a stall, a load): written from the fallback thread, before the factors and the point-blank cap are dropped");
        if (kld_r.fon) { kld_r.fon = 0; kld_r.t_foff = GetTickCount(); }
        InterlockedExchange(&kld_r.pbon, 0);
        return;
    }
    kld_v.act = 0; kld_v.pl = 0; kld_v.state = 0;
    if (!++kld_r.pass) kld_r.pass = 1;         /* track R8: kld_flop_one's heartbeat is 'this pass' */
    kld_tick_main(game_thread);
    kld_rules(GetTickCount());                 /* track R8: after every early return of kld_tick_main, before the camera / prompt's own */
    if (!kld.on || !klh_exe_ok || (!kld_v.cam && !kld_v.prompt && !kld_v.ours)) return;
    now = GetTickCount(); pl = kld_v.act ? kld_v.pl : 0;
    if (!pl || !(d = klh_rd32(pl + 0x2948)) || klh_rd32(d) != pl || !klh_rd(d + 4, &ds, 4)) { kld_v.act = 0; kld_prompt(0, 0, now); return; }
    kld_camera(pl, ds, now);
    kld_prompt(pl, ds, now);
}

static void kld_init(void)
{
    int k; float v; char t[220]; int n = 0;
    memset(&kld_s, 0, sizeof kld_s);
    kld.on = GetPrivateProfileIntA("Down", "Enable", 0, klh_ini) != 0;
    kld.dry = GetPrivateProfileIntA("Down", "Dry", 0, klh_ini) != 0;
    kld.log = GetPrivateProfileIntA("Down", "Log", 1, klh_ini);
    kld_floor_on = GetPrivateProfileIntA("Down", "Floor", 0, klh_ini) != 0;      /* opt-in: 0 = the game's own rule alone, as before */
    kld_floor_pct = kld_inif("FloorPct", "50"); if (!kld_fin(kld_floor_pct) || kld_floor_pct < 1.0f || kld_floor_pct > 100.0f) kld_floor_pct = 50.0f;      /* GUESS: where a single hit can kill him */
    memset(&kld_fl, 0, sizeof kld_fl);
    if (kld_floor_on && kld.on) klog("down: floor: on (Floor=1, FloorPct=%.0f): at or under that health, while up and off cooldown, any hit floors him; logs every hit then", kld_floor_pct);
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
    if (kld.flop != 1 && kld.flop != 2 && kld.flop != 3) kld.flop = 0;
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
        if (kld.flop == 3) fall = "/Damage/Wounded/Running/Torso/Merc_Back";      /* Flop=3: the CARRIER (its own key: FlopFallSlot is modes 1 / 2's) */
        GetPrivateProfileStringA("Down", kld.flop == 3 ? "FlopCarrier" : "FlopFallSlot", fall, kld.fallslot, sizeof kld.fallslot, klh_ini);
        GetPrivateProfileStringA("Down", "FlopUpSlot", "/Movement/Rise/Rise_From_Stomach", kld.upslot, sizeof kld.upslot, klh_ini);
        if (kld.fallslot[0] != '/') strcpy(kld.fallslot, fall);
        if (kld.upslot[0] != '/') strcpy(kld.upslot, "/Movement/Rise/Rise_From_Stomach");
    }
    /* Flop=3 (track R6): the list. FlopMix = '<sheet number or clip name>:<weight>,...' - only the clips of kld_md[]
       (41 7 13 12 9 10 25 42 43); a clip the key does not name is out; no key = the table's weights = the owner's 'all'
       (41:2,12:2,10:1,25:1,42:1,43:1). FlopLight=0 takes the stumble #43 out. FlopReach = metres of forward root motion
       a clip may have. Its DEFAULT IS 1.0 = ONLY #25 (review6 M1; the task's rule: a clip that can carry him through a
       wall or off a ledge is OUT until shown safe, and the hook cannot test the way). The owner's 'all' is
       FlopReach=4.5 - the lead's runs L1 / W1 / W2 set it, his ini gets the value those runs allow. 0 = no limit.
       FlopUp=71 = cut into Rise_From_Stomach (a test key). */
    memset(&kld_mx, 0, sizeof kld_mx); memset(&kld_cx, 0, sizeof kld_cx); kld_mx.next = -1;
    kld_rng = GetTickCount() ^ (DWORD)GetCurrentProcessId() * 2246822519u;
    {
        char mix[400], *p, *q, *c; int any = 0;
        for (k = 0; k < KLD_NMIX; k++) kld_mx.w[k] = kld_md[k].w;
        GetPrivateProfileStringA("Down", "FlopMix", "", mix, sizeof mix, klh_ini);
        for (p = mix; kld.flop == 3 && *p; p = q) {
            float w = 1.0f; int hit = -1;
            for (q = p; *q && *q != ','; q++) ;
            if (*q) *q++ = 0;
            while (*p == ' ') p++;
            if ((c = strchr(p, ':')) != 0) { *c = 0; w = (float)atof(c + 1); }
            for (c = p + strlen(p); c > p && c[-1] == ' '; ) *--c = 0;
            if (!*p) continue;
            for (k = 0; k < KLD_NMIX; k++) if (atoi(p) == kld_md[k].sheet || !_stricmp(p, kld_md[k].clip)) hit = k;
            if (hit < 0 || !kld_fin(w) || w < 0 || w > 100.0f) { if (kld.on) klog("down: flop: FlopMix: '%s' is not a clip of the list (41 7 13 12 9 10 25 42 43, or the clip's name after '#') or its weight is not 0 .. 100: left out", p); continue; }
            if (!any) { any = 1; for (k = 0; k < KLD_NMIX; k++) kld_mx.w[k] = 0; }
            kld_mx.w[hit] = w;
        }
        kld_mx.light = GetPrivateProfileIntA("Down", "FlopLight", 1, klh_ini) != 0;
        kld_mx.reach = kld_inif("FlopReach", "1.0");
        if (!kld_fin(kld_mx.reach) || kld_mx.reach < 0 || kld_mx.reach > 50.0f) kld_mx.reach = 1.0f;
        kld_mx.up = kld.flop == 3 && GetPrivateProfileIntA("Down", "FlopUp", 0, klh_ini) == 71;
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
    if (kld.on && kld.flop == 1) klog("down: flop: Flop=1 - DOG DAYS' OWN KNOCK-DOWN, ONE CLIP: he goes down by %s (thrown down, lying, up over a knee: the whole clip is played in the game's fall; no press cuts it; a hit of it costs only with Vulnerable=1 - the 'rules:' line), from the landing on at FlopBase %.2f + FlopPerPress %.2f x the mash meter, at most FlopTop %.2f; FlopBelly=%d (1 = every draw of the slot is the clip thrown forward, onto the belly); FlopUpPct=%.0f (health he is given when up; 0 = none). Flop=2 = the earlier pair (a death clip + the rise from the stomach)",
                                      kld.fallslot, kld.fbase, kld.fper, kld.ftop, kld.belly, kld.uppct);
    if (kld.on && kld.flop == 3) {
        char m[300]; int nm = 0;
        m[0] = 0;
        for (k = 0; k < KLD_NMIX; k++) if (kld_mx.w[k] > 0 && nm < (int)sizeof m - 24) nm += snprintf(m + nm, sizeof m - nm, " #%d:%.1f", kld_md[k].sheet, kld_mx.w[k]);
        klog("down: flop: Flop=3 - ALL THE BELLY FALLS, A DIFFERENT ONE EACH TIME: the hook draws one whole clip a knock-down from the list (sheet numbers of G_zoom_belly.png : weight)%s, never one group twice in a row, and writes its number into the one pair of the carrier %s in the human's own set (no bot's draw, nobody's death changes); FlopLight=%d (the stumble #43: he stays up, no mash), FlopReach=%.2f m (a clip whose root goes further forward is left out; the default 1.0 = ONLY #25 until live checks W1 / W2 have shown the long dives safe at a wall and an edge - ALL the falls of the sheet need FlopReach=4.5; 0 = no limit), FlopUp=%s; from the landing on FlopBase %.2f + FlopPerPress %.2f x the mash meter, at most FlopTop %.2f; FlopUpPct=%.0f. Everything else is Flop=1's (re\\player_down.md 12)",
             m[0] ? m : " (EMPTY)", kld.fallslot, kld_mx.light, kld_mx.reach, kld_mx.up ? "71 (A TEST KEY: at a belly clip's event 8 the game's get-up state plays Rise_From_Stomach: FULL damage from there, and the get-up words are that slot for every down)" : "0 (every clip is played whole)", kld.fbase, kld.fper, kld.ftop, kld.uppct);
    }
    /* track R7: the camera stays his, and the game's own tap prompt. Both default to 1 when Flop is set, else 0 */
    memset(&kld_v, 0, sizeof kld_v);
    kld_v.cam = GetPrivateProfileIntA("Down", "Camera", kld.flop != 0, klh_ini) != 0;
    kld_v.side = GetPrivateProfileIntA("Down", "CameraSide", 1, klh_ini) != 0;
    kld_v.prompt = GetPrivateProfileIntA("Down", "Prompt", kld.flop != 0, klh_ini) != 0;
    kld_v.style = GetPrivateProfileIntA("Down", "PromptStyle", 1, klh_ini) == 2 ? 2 : 1;
    kld_v.pulse = GetPrivateProfileIntA("Down", "PromptPulse", 0, klh_ini) != 0;      /* review 7, S3: default 0 - the game's own break-free bar stays white */
    if (kld.on) klog("down: camera: Camera=%d (1 = in a fall this part drives the fall's LOOK bit 0x10 of the input mask [player+0xed0] is taken off at once - stock takes it off 0.72 s into its own fall, the flop holds that tick for the whole clip, so the mouse was dead for the whole knock-down; the move bit 1 stays), CameraSide=%d (1 = the shoulder side he had is put back: the down start forces the left one). prompt: Prompt=%d (1 = the game's own 'Tap Quickly' prompt - the element at [osd+0x10fc], the one its human-shield break-free shows (0x860ed3), here with '{TapCover}' + its bar - is shown by four data fields from the landing of a knock-down / during a get-up this part drives, only while the round runs), PromptStyle=%d (1 = the bar is how far he is up - the hook's design; 2 = the mash's speed - a meter as the game's break-free bar is), PromptPulse=%d (1 = the bar is the game's red for 0.12 s after a press; 0 = always white, as the game's). Camera and Prompt default to 1 when Flop is set. Data writes only (re\\player_down.md 13)",
                     kld_v.cam, kld_v.side, kld_v.prompt, kld_v.style, kld_v.pulse);
    /* track R8: while knocked down - no shooting, not invulnerable, police little, heisters in full (the block before
       kld_tick_main). NoFire and DownFromCop default to their values only with a Flop: with Flop=0 the stock down
       ('he can crawl and shoot', full price) stays what it was unless a key is set. */
    memset(&kld_r, 0, sizeof kld_r);
    kld_r.nofire = (int)GetPrivateProfileIntA("Down", "NoFire", kld.flop != 0, klh_ini);
    if (kld_r.nofire < 0 || kld_r.nofire > 2) kld_r.nofire = kld.flop != 0;
    kld_r.hurt = GetPrivateProfileIntA("Down", "Vulnerable", KLD_ONE, klh_ini) != 0;
    /* review 8, S4: 0.15, not 0.25 - most guards of the Dead Men maps carry pistols, which at 0.25 finish a man who
       lies with 80 .. 220 in 2 .. 8 bullets (re\player_down.md 14.4); still a GUESS */
    kld_r.cop = kld_inif("DownFromCop", kld.flop ? "0.15" : "1"); kld_r.crew = kld_inif("DownFromCrew", "1");
    if (!kld_fin(kld_r.cop) || kld_r.cop < 0 || kld_r.cop > 4.0f) kld_r.cop = kld.flop ? 0.15f : 1.0f;
    if (!kld_fin(kld_r.crew) || kld_r.crew < 0 || kld_r.crew > 4.0f) kld_r.crew = 1.0f;
    kld_r.pb = kld.on ? kld_pb_ini() : -1.0f;                                 /* review 8, M1: DownPointBlank (kld_pb) */
    kld_r.cdfix = GetPrivateProfileIntA("Down", "CooldownCredit", 1, klh_ini) != 0;      /* S5 */
    kld_r.nothrow = GetPrivateProfileIntA("Down", "NoThrow", 0, klh_ini) != 0;           /* S2: a TEST key */
    if (kld.on) {
#if defined(KLR_DOWN) && KLR_DOWN >= 2
        const char *ho = "this build's klbalance.c HAS the hand-over lines (KLR_DOWN 2: the factors AND the point-blank cap): while [Balance] keys own the damage table klbalance.c multiplies it by kld_factor(), and its point-blank wrapper asks kld_pb()";
#elif defined(KLR_DOWN)
        const char *ho = "THIS BUILD'S klbalance.c HAS ONLY THE FIRST THREE HAND-OVER LINES (KLR_DOWN 1): the factors stand, THE POINT-BLANK CAP CANNOT";
#else
        const char *ho = "THIS BUILD'S klbalance.c HAS NOT GOT THE HAND-OVER LINES (KLR_DOWN): while [Balance] keys own the damage table the two factors CANNOT STAND, nor can the point-blank cap";
#endif
        int owned = kld_owned(), need = kld_r.cop != 1.0f || kld_r.crew != 1.0f, dead_end = 0;
#ifndef KLR_DOWN
        dead_end = owned && need;
#endif
#if !defined(KLR_DOWN) || KLR_DOWN < 2
        if (kld_r.pb >= 0) dead_end = 1;
#else
        if (kld_r.pb >= 0 && !klr.on) dead_end = 1;      /* klbalance.c's wrapper only goes in with [Balance] Enable=1 */
#endif
        klog("down: rules: DownPointBlank=%.2f (review 8: what the hundred bullets of a point-blank step - a soldier firing within 1.6 m, kl2 0x8c62e0 - become ON HIM while he is down, written into the hit record by klbalance.c's wrapper through kld_pb(); a negative number = the step is left alone; Vulnerable WAITS until the cap stands - it needs [Balance] Enable=1 (now %d) and hand-over lines 4 / 5), CooldownCredit=%d (1 = when he is up, the seconds the down state's frame stood still are taken off the pause before the next down [D+0x38]), NoThrow=%d (a TEST key: the throw button is written 'up' in every pass while he is down)",
             kld_r.pb, klr.on, kld_r.cdfix, kld_r.nothrow);
        klog("down: rules: NoFire=%d (1 = while he is down the game's own 'no fire' + 'no aim' bits 0x400 / 0x200 of the input mask [player+0xed0] are set - what a human-shield hold sets on its victim; 2 = fire only; the look, the GET UP button and Use stay; melee is off for a downed man by the game itself, 0x612d07), Vulnerable=%d (1 = in a knock-down of Flop=1 / 3 the game's 'down not dead' switch [0xceb40c] is 0 while this part holds the fall: its trigger swallows no hit; no effect in Flop=0 / 2), DownFromCop=%.2f (x the level's police -> you while he is down), DownFromCrew=%.2f (x crew -> you: 1 = a heister hurts him as if he stood); the game picks the float by the ATTACKER's team at every bullet (0x8b8050). The damage table is %s; %s%s. Arcade on a level that is not stock, not for a police player; data writes only (re\\player_down.md 14)",
             kld_r.nofire, kld_r.hurt, kld_r.cop, kld_r.crew, owned ? "klbalance.c's ([Balance] Enable=1 with a key)" : "nobody's (no [Balance] key): this part writes the level's two floats itself and puts them back", ho,
             dead_end ? " - SO Vulnerable DOES NOTHING IN THIS PROCESS: hits stay swallowed in the knock-down as before (a floored man at the full police price, or beside a guard without the point-blank cap, would be worse); give klbalance.c the five lines and [Balance] Enable=1, or set both factors to 1 and DownPointBlank=-1" : "");
        if (kld_r.hurt && !KLD_ONE) klog("down: rules: Vulnerable=1 does nothing with Flop=%d: only the falls of Flop=1 / 3 are ended by this part - a stock fall (0.7 s free, then full price lying) and Flop=2's are ended by the game's own frame, which the switch would stop", kld.flop);
    }
    if (kld.on && kld.flop == 2) klog("down: flop: Flop=2 - THE BELLY FLOP, two clips: he goes down by %s and gets up by %s (slot ids written into his prone movement while he is up; the game plays them itself), the get-up at FlopBase %.2f + FlopPerPress %.2f x the meter, at most FlopTop %.2f; FlopTake=%.2f (the share of a loss in the get-up that stays), FlopUpPct=%.0f (health he is given when up; 0 = none)",
                                 kld.fallslot, kld.upslot, kld.fbase, kld.fper, kld.ftop, kld.take, kld.uppct);
}

#endif /* KLDOWN_C */
