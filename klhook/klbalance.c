/*
 * klbalance.c - one dial for how much a bullet costs whom in an Arcade round ([Balance] Risk=0..3).
 * The owner, 2026-10-10, after four Dead Men maps with AI heisters: 'they dont have much health when i shoot them
 * but when they shoot me i have a lot of health not proportional and the coppers dont seem too intimidating it
 * should be all the same kinda risk and how the traitors could be'.
 * Part of KLHook (included by klhook.c after klbot.c, SHIP and TEST alike). DATA WRITES ONLY: floats of two heap
 * objects (the tuning object, the local player's health object). No code byte, no call of a game function.
 * (The point-blank keys of 2 a4, when one is set, add one heap dword - the database object's vtable pointer, as
 * klchar.c does it for the option object - one heap float, and a wrapper that passes every call on to the game's own
 * routine. With no such key nothing of it exists in the process.)
 * Research and every number: re\balance.md. LIVE since 2026-10-10 in the owner's game (KLHook.log: 'the damage table
 * ... is what the game's code builds', 'Risk=2 written for 11 Arcade levels (39 value(s) changed', 'your health set:
 * maximum 401.5'): the six factors and the health part. NOT RUN: the seventh factor (CrewOffStage, 2 a2), the
 * point-blank keys (2 a4). Everything is OFF unless [Balance] Enable=1, and nothing is written outside an Arcade
 * session on a level that is not stock.
 *
 * 1. WHAT WAS MEASURED (kl2.exe build 0490, read 2026-10-10; EXE = in the disassembly)
 *    A bullet's damage is made in three steps.
 *    a. The gun: ZFFItemTemplateWeapon slot 0x2f0 = 0x46ef60(weapon, distance). Four damage numbers of the AMMO
 *       template (object +0x84..+0x90) are joined over the gun's four ranges (+0xd4..+0xe0), times the gun's
 *       +0xe4, times +0x13c when the shooter is a ZActor (an NPC: pistols 1.5, rifles 0.6..1.0, shotgun pellets
 *       0.4) or +0x140 when it is not and the session is multiplayer / Arcade (1.0 on every gun), times one of
 *       +0x144..+0x150 by range band in multiplayer / Arcade. Level data, the same in every level.
 *    b. The body part: 0x572f60(bone type), ten floats at 0xcdefe4..0xcdf008: head (types 2, 3) 10.0, 0.5 for
 *       types 4 and 7, 0.2 for 6 and 9, else 1.0. An NPC victim takes it whole (0x61acb8). The PLAYER as victim
 *       takes min(m, 4) softened to 1 + (m - 1) / 4 (0x4db7ff..0x4db83d): a head shot costs him 1.75, not 10.
 *       And a ZActor shooter never gets the head factor at all (0x61ac87, 0x4db7e7: bone type 2 / 3 -> 1).
 *    c. WHO SHOOTS WHOM, Arcade only: one float of the per-level record R = [0x168d7c0] + 0x6ac + L * 0x70
 *       (L = the Arcade level, byte [[rules+0x5f8]+0x45] clamped to 1..11; the record klbot.c's Tune writes its
 *       +0x18 / +0x20 / +0x6c of). With the local player not a policeman ([player+0x2723] == 0):
 *         +0x00  an NPC that is not team Ally -> an NPC        0x591b60   (police hitting the AI heisters)
 *         +0x04  an Ally NPC -> an NPC                         0x591b60   (AI heisters hitting police)
 *         +0x08  an NPC that is not Ally -> the player         0x8b8050   (police hitting YOU)
 *         +0x0c  the player -> an NPC that is not Ally         0x7c1ba0   (YOU hitting police)
 *         +0x10  an Ally NPC -> the player                     0x8b8050   (a heister - a traitor - hitting YOU)
 *         +0x14  the player -> an Ally NPC                     0x7c1ba0   (YOU hitting a heister / a traitor)
 *         +0x1c  TIMES THIS, on top of +0x04, when the shooter is an Ally NPC at another heist stage than the local
 *                player (0x591be0..0x591c24, re-read whole 2026-10-11; re\balance.md 10). The routine's first argument
 *                is the ATTACKER: 0x61a980 (ZFFActor's hit routine, the victim is `this`) keeps [hit+0xc] when it is a
 *                ZFFActor and pushes it at 0x61ad15. Only when [player+0x2723] == 0 and the attacker's team is Ally:
 *                0x78f470 looks the attacker up as a crew record (in use, mask 1 'an AI member', its actor), 0x6c7700
 *                gives the local player's (record 0 in Arcade); stage bytes [record+0x78] differ -> fmul [R+0x1c].
 *                So: an AI heister that is not at YOUR stage hits every NPC - police, guards, civilians - at 0.5 .. 0.1
 *                of his damage. Not for what a heister TAKES, not for the player's hits or the hits on him, not for a
 *                police player, not in the traitor rules: 0x591c1d is the ONLY reader of the float in the exe (three
 *                sweeps of every use of the tuning pointer; the pointer never leaves the function that loads it).
 *                Until 2026-10-11 this line had shooter and victim swapped (re\boardall_review_exe.md 1).
 *       As the tuning object's constructor writes them (0x524050, emulated: re\balance.md 2):
 *         level        1     2     3     4     5     6     7     8     9    10    11
 *         +0x00     0.01  0.05   0.1  0.15   0.2  0.25   0.3  0.35   0.4  0.45   0.5
 *         +0x04      3.0   2.6   2.2   1.9   1.6   1.3   1.0   0.8   0.4   0.2   0.1
 *         +0x08      0.1   0.2   0.4   0.8   1.0   1.3   1.6   1.9   2.2   2.6   3.0
 *         +0x0c      2.0  1.75   1.5  1.25   1.0   0.9   0.8   0.7   0.6   0.5   0.3
 *         +0x10      0.1   0.2   0.4   0.8   1.0   1.1   1.2   1.3   1.4   1.5   1.7
 *         +0x14     0.25   0.5   1.0   0.9   0.8   0.7   0.6   0.5   0.4   0.3   0.1
 *         +0x1c      0.5   0.5   0.5   0.4   0.3   0.3   0.2   0.2   0.2   0.1   0.1     (0x52b84d.. : read again 2026-10-11)
 *       THIS IS WHAT THE OWNER FELT. On Arcade level 1 - every test round so far - a policeman's bullet costs the
 *       player a TENTH, the player's costs the policeman DOUBLE, a policeman's costs an AI heister a HUNDREDTH and
 *       a heister's costs a policeman three times. It is the stock game's own ramp (even at level 5, reversed by
 *       11), on the stock maps too; the Dead Men maps did not cause it.
 *    Health. The player: 0x410781 gives him, in multiplayer / Arcade, float [P+0x10] of the tuning object's player
 *    block P (0x4206f0: Arcade P = tuning+0x604, online +0x5c4, story +0x5e4) plus 0 / 20 / 40 / 60 of armour
 *    (0xbd22c8): Arcade 550 (story: 100 times 11 / 5 / 2.25 / 0.85 by difficulty). It comes back by itself:
 *    [P+0x08] seconds after the last hit (Arcade 4), all of it within [P+0x0c] seconds (Arcade 4) - the health
 *    object's +0x14 / +0x18, used by 0x419570. An NPC: its ZSoldier health (65..175 police, 280 AI heisters) times
 *    0.5 / 0.9 / 1.15 / 1.3 by the campaign difficulty [0x156b5f0] (0x8fbac0 through 0x831f00: Arcade is not
 *    'online', so it takes the STORY rows, and nothing in the Arcade menu sets that option - ASSUMPTION: it is
 *    what the profile last played the campaign on; the log line below says what it is).
 *
 * 2. WHAT THE HOOK DOES
 *    a. THE SIX FACTORS. While an Arcade session is up on a level that is not stock, the six floats +0x00..+0x14
 *       of all eleven records are written; the values found first are kept and written back when the session is
 *       no longer Arcade or the level is stock. Risk picks the row, each factor has its own key:
 *                      CopToCrew CrewToCop CopToYou YouToCop CrewToYou YouToCrew   PlayerHealth  RegenDelay RegenTime
 *         Risk=0         (nothing is written: the stock ramp)
 *         Risk=1           0.5      1.5      0.5      1.5      0.5      1.0        1.0 (550)     stock      stock
 *         Risk=2           1.0      1.0      1.0      1.0      1.0      1.0        0.73 (400)    8 s        8 s
 *         Risk=3           1.0      1.0      1.0      1.0      1.0      1.0        0.51 (280)    8 s        8 s
 *       Risk=2 is the owner's rule: the same gun at the same range costs everybody the same. 8 s / 8 s is what a
 *       stock SWAT man and an AI heister have (ZSoldier field 8 = 50: 0x8fbbff). 280 is an AI heister's health.
 *       Ramp=1 (default): the stock ramp still counts where it is HARDER than the dial - damage you and your crew
 *       take is max(dial, stock), damage dealt to the police is min(dial, stock) - so a late Arcade level is never
 *       easier than stock. Ramp=0: the dial's numbers on every level. YouToCrew is always the dial's number.
 *       NOT written: +0x18 (klbot.c's Retaliate).
 *    a2. THE SEVENTH, CrewOffStage (2026-10-11; NOT RUN IN THE GAME): the float +0x1c of the same eleven records, in
 *       the same pass and under the same conditions as the six, the stock values kept and put back with theirs.
 *       With you outside and the crew inside (stage 0 against 1) 'CrewToCop 1.0' was really 0.5.
 *         CrewOffStage=1.0   an AI heister hits police the same wherever you are      -1 = the game's own (not written)
 *         Risk=0  not written
 *         Risk=1  0.75   a GUESS as Risk=1's other numbers are: halfway from stock's 0.5 to none, as they are halfway to 1.0
 *         Risk=2  1.0    'the same gun at the same range costs everybody the same' cannot depend on where YOU stand
 *         Risk=3  1.0    the same
 *       Ramp=1: stock's number is at most 0.5, so 'stock stays where it is harder' taken per factor would never let the
 *       key do anything. What a heister at another stage really deals is CrewToCop x CrewOffStage, so the rule is put
 *       on that PRODUCT: it is at most stock's own product on the level (levels 1..11: 1.5 1.3 1.1 0.76 0.48 0.39 0.2
 *       0.16 0.08 0.02 0.01). Risk=2 therefore writes 1.0 on levels 1-3 (1.0 x 1.0 is under stock's 3.0 x 0.5), 0.76 /
 *       0.48 / 0.39 on 4-6 and leaves 7-11; Risk=1 writes 0.75 0.75 0.73 0.51 0.32 and leaves 6-11. A late Arcade level
 *       is never easier than stock in this either. With CrewToCop left at stock, Ramp=1 holds the key at stock on every
 *       level (a line says so) - as it holds CopToYou=0.05. Ramp=0: the number as given, on every level.
 *       Written only when the eleven values found are the row of section 1 (klr_code_off): another build's object is
 *       not written into; one line says so, the six are not affected.
 *       THE KEY'S TEXT (review N1 / N2): one number and nothing else, 0 .. 20 (a ';' comment may follow). '0,75' or
 *       '1.0abc' is NOT taken as its leading number (strtod would make the first 0 - an off-stage heister doing no
 *       damage at all): the key is ignored, the dial's number stands and one line says so; the same for a number
 *       over 20. Negative = the game's own; '-0' is 0.
 *       OVER 1 (review N3): the key may be set up to 20, and beside a low CrewToCop the product rule then lets a
 *       heister at ANOTHER stage hit harder than one at yours (CrewToCop=0.1 CrewOffStage=20 under Ramp=1: x 15 on
 *       level 1, against 0.1 at your stage). Not capped: it happens only on request (the dial's own numbers never pass
 *       1.0), and the live check that is to SHOW the factor uses 20 on purpose (re\balance.md 10.9, run O3).
 *       While the table fails klr_table's shape test nothing is written and nothing is put back, the seventh included
 *       (as the six always did); it goes back on the first pass the test holds again (review N5).
 *    a3. A POLICE PLAYER (klfed.c's fed; key FedMirror, default 1; 2026-10-11). The three routines of 1 c each read
 *       the local player's police byte [player+0x2723] and, when it is set, take the OTHER float of their pair
 *       (0x591bbe, 0x8b80a0 / 0x8b80ad, 0x7c1bf0 / 0x7c1bfd; re-read 2026-10-11): the table is really 'your enemies ->
 *       your side, your side -> your enemies, an enemy -> you, you -> an enemy, a friend -> you, you -> a friend', and
 *       the six keys are named for a criminal player. LIVE, run PT_DM03_die_r2 (the bank, CopToCrew 0.05, CrewToCop
 *       1.0): the human came back as police and all seven AI heisters were dead 15 .. 47 s later - they had lost the
 *       0.05 that kept them alive against the police and hit the police at 0.05 themselves. FedMirror=1: while the
 *       local player is police the three pairs are WRITTEN EXCHANGED (+0x00 <-> +0x04, +0x08 <-> +0x10, +0x0c <->
 *       +0x14), so that every key keeps the meaning of its name whichever side the human is on: CopToCrew stays what
 *       a policeman's bullet costs a heister, CrewToYou what a heister's costs you. Each value is the one the
 *       criminal row has (Ramp and all), only its place changes; the table goes back to the ordinary order the pass
 *       after the byte clears (the next round's hero). FedMirror=0: the game's own swap. The seventh factor is never
 *       applied for a police player (0x591be0) and is not touched by this. A pair of which NO key is set is left to
 *       the game's own swap (review M1). Reviewed: re\balance_fedmirror_review.md (the exe reading and klr_mir hold).
 *       WHAT IT MEANS IN PLAY, the owner's ini (Risk=2, CopToCrew=0.05, Arcade level 1): a police AI's bullet costs a
 *       heister x 0.05 as before (without the mirror x 1.00, stock x 3.00), a heister's a police AI x 1.00, a
 *       heister's costs the fed x 1.00 and the fed's a heister x 1.00: the police AI cannot finish the crew, the fed
 *       has to. The player pairs are mirrored too so that CrewToYou / YouToCrew stay 'a heister's bullet on you /
 *       yours on a heister' on either side (review S1: a choice; under Risk=2 / 3 they are all 1.0 anyway).
 *    a5. YouToCrew AS THE 'BULLET SPONGE' KEY, AND FedToCrew (2026-10-11, track O; NOT RUN IN THE GAME; re\bots_fight.md 1).
 *       The owner: the AI heisters 'feel a bit one sided so the player could just easily turn on them'. YouToCrew is
 *       already exactly the float for that: +0x14 is read by 0x7c1ba0 for the PLAYER's bullet on an Ally NPC and by
 *       nothing else - not by the police's hits on the crew (+0x00, CopToCrew), so a lower YouToCrew makes the crew
 *       tougher against YOU and against nobody else. It is also what your bullet costs a heister who has TURNED (he
 *       stays team Ally), and Ramp never touches it. Under Risk=2 today: your Zastava's 58.5 a bullet at 10 m against
 *       a heister's 252 = 5 body hits; his 47 against your 401.5 = 9. YouToCrew=0.5 makes it 9 against 9, 0.4 = 11.
 *       What he hits YOU with, turned or not, is CrewToYou (+0x10): no Ally NPC shoots at you unless he has turned.
 *       A POLICE player (the fed): under FedMirror=1 the key keeps its meaning, so the fed's bullet on a heister would
 *       be x 0.4 too. FedToCrew=<n> is that number while you are police: it is written into the slot a police
 *       player's bullet on an Ally NPC reads (+0x0c, 0x7c1bf0) in place of YouToCrew's, in the same pass and only while
 *       the three pairs stand exchanged. No key = YouToCrew's number. Not under Ramp (as YouToCrew). FedMirror=0: the
 *       key does nothing (a line says so).
 *    a6. YouToCrewFar: THE SPONGE BY RANGE (2026-10-11, track O, fix round; NOT RUN IN THE GAME; re\bots_fight.md 1).
 *       The owner: 'i probably meant more bullet spongey at longer ranges i feel like compared to the bot'.
 *       READ: the gun already loses damage with distance, for both sides alike (0x46ef60: the crew's Zastava and yours
 *       are one template - 72 / 64 / 52 / 37 from you, 58 / 51 / 42 / 30 from a heister at 5 / 15 / 30 / 50 m), so in
 *       damage you need half the hits he needs AT EVERY RANGE; what differs far away is who HITS (your aim is exact and
 *       a head shot is x 10 on an NPC at any range; a heister's accuracy is 50 %, his spread by range NOT READ).
 *       A TRUE per-hit factor cannot be had inside the hook's rules: the hit is priced in the victim's own routine
 *       (ZFFActor slot 423 = 0x61a980, the factor from 0x7c1ba0), reached through the ACTOR's vtable only - a private
 *       vtable copy on each AI heister would change the first dword every part of this hook (and klbot.c's own
 *       KLB_ACTOR_VT test) knows a ZFFActor by; the health object [actor+0x5fc] is written directly (0x61f032), it has
 *       no virtual in that path. So this is an APPROXIMATION BY DATA: the one float +0x14 is re-written every pass
 *       (50 ms) for the heister you are most likely shooting at:
 *         1. the crew member your last counted hit was on, for YouToCrewHold seconds after it (the game's own sum of
 *            your hits on him, [rules+0xac4+0x30*victim], rose: 0x4d17f0);
 *         2. else the nearest heister in play that carries the traitor mask (his hits are not always counted);
 *         3. else the FARTHEST heister in play - so the first bullet of a fight is priced for the far side.
 *       factor = YouToCrew x (1 at YouToCrewNearAt metres or nearer .. YouToCrewFar at YouToCrewFarAt or farther,
 *       linear between, in steps of 0.02). So hit n is priced by where hit n - 1's victim stands: wrong for one bullet
 *       when you change targets between a near and a far one. NOT for a police player (FedToCrew is his number), not
 *       while YOU are the traitor (the game counts no hits then: flat YouToCrew). The stock values come back as the
 *       table's other values do. Log=2: a line when the target or the factor changes (one a second at most).
 *    a7. Tough: EVERYBODY A BIT MORE HEALTH (2026-10-11, track X2; NOT RUN IN THE GAME; re\balance.md 11).
 *       The owner, after a round as a fed: 'they die really quick, like i was saying everyone should have a bit more hp'.
 *       Tough=<f> (0.25 .. 10; 1 or no key = nothing) is ONE factor on every maximum health of the round, the damage
 *       factors left alone - so who needs how many hits against whom keeps its RATIO and every fight lasts f times as long:
 *         - every NPC (police, guards, AI heisters, civilians): its health is made by ZSoldier@CPPScript slot 44 = 0x8fbac0
 *           as  lerp(tuning+0x364, +0x368; ZSoldier field 7) x ROW[+8] x field 9..12  and stored through the actor's slots
 *           +0x674 / +0x670 (0x8fbb5b fld [eax+8]; the other script class's 0x74d960 does the same with [script+0x558],
 *           0x74d99c). ROW = 0x831f00(tuning): in Arcade [tuning + 0x594 + 4 * option Difficulty] = one of the four story
 *           rows tuning+0x42c / +0x450 / +0x474 / +0x498 (+8 = 0.5 / 0.9 / 1.15 / 1.3, the 'NPC health x' of the first log
 *           line). Those two instructions are the ONLY readers of ROW+8 (all eleven callers of 0x831f00 looked at). The
 *           hook writes the four floats x f in the pass that arms the dial - the pass after the level's archive is opened
 *           (KLHook.log: 40 ms after it at 19:39:49.810 / .851, about 200 ms in the later loads, 20:52:21.178 / .374 and
 *           20:57:19.422 / .623; the rules object exists before the archive is opened, the player's health object
 *           appears 1.6 .. 2 s after the pass) - and
 *           puts them back with the table. ASSUMED, NOT READ: that slot 44 runs for every actor AFTER that pass (who calls
 *           the slot was not found: it is virtual). The line 'Tough: the AI heisters' maximum health' 2 s into every round
 *           says whether it did: 378.0 at Tough 1.5 on a level-1 heister (252.0 on ALL of them = it did not; one odd
 *           record = the actor [gamedata+0x4cf0], who takes ROW[+0], 0x8fbb29 / 0x6fd7c0).
 *           Written only when the four pointers at tuning+0x594 name those four rows and the four floats are the code's.
 *         - the human, heister or fed: the live health object, on top of PlayerHealth (maximum = the game's x
 *           PlayerHealth x Tough); a full health is raised with the maximum (the game sets both before the hook sees the
 *           object: without that a new round would start at 550 of 825, under the 0.9 x maximum 0x46f210 asks about).
 *       [Bots] CrewHealth (klgrudge.c) comes ON TOP for the AI heisters: it scales the maximum it finds.
 *       NOT changed by it, so 'every ratio stays' has EXCEPTIONS (review X2 S3) - everything that is an ABSOLUTE number
 *       of health: the knock-down's trigger (kldown.c DownHealth: 80 of 550 = 14.5 %, of 825 = 9.7 %; set DownHealth x
 *       Tough by hand, 120 at 1.5) and kldown's MinHit / Burst, the point-blank step (a hundred bullets), every blast of
 *       a fixed damage, the damage the van's departure deals the crew left behind (1,000,000). kldown.c's HealthPct is a
 *       share of the maximum and follows. The game's own tally of your hits on a crew
 *       member is in per cent of HIS maximum (0x4d17f0): the yellow card and Retaliate / Grudge come f times later.
 *    a8. THE FED IS NOT A ONE-MAN ARMY: CrewToFed, FedHeadShot / HeadShot (2026-10-11, track X2; NOT RUN IN THE GAME).
 *       The owner: 'especially when im a fed im dealing wayy too much damage and they do nothing to me'. Measured
 *       (re\balance.md 11.1): under his Risk=1 the fed's bullet costs a heister x 1.00 (YouToCrew) and a head shot x 10,
 *       a heister's costs the fed x 0.50 (CrewToYou) of 550 that are whole again 8 s after the last hit: 4 body hits or
 *       ONE head shot against 22 hits from a man who misses every second shot. By the EXE READING a police player is a
 *       candidate target for a team-Ally soldier and for nobody else (0x8824e7; 0x8826fb: scored, not a friend) - but
 *       NO LOG OF ANY RUN HOLDS ONE HIT OF A HEISTER ON A FED (review X2 M1: the only Log=2 fed run, FD3_DM03_die, has
 *       a 27.5-health fed alive 145 s beside five heisters and no 'you lost' line; the owner's two deaths as a fed name
 *       no killer), and how a soldier RANKS him among the police AI was not read. So 'it is the numbers' is the
 *       reading, NOT a seen fact: live check TH (re\balance.md 11.7) decides it before these keys are the answer.
 *       CrewToFed=<n>: a heister's bullet on you while you are police, written into the slot a police player's victim
 *         routine reads for an Ally attacker (+0x08, 0x8b80a0) in place of CrewToYou's, as FedToCrew is at +0x0c: same
 *         pass, only while the three pairs stand exchanged (FedMirror=1), not under Ramp. No key = CrewToYou's number.
 *       FedHeadShot=<x> / HeadShot=<x>: the body-part factor of a head (bone types 2 / 3) while you are police / while
 *         you are a heister; the game's is 10. The two floats are .data globals 0xcdeffc / 0xcdf000 that 0x572f60 hands
 *         out (its two callers: 0x61acb8 an NPC victim, 0x4db7ff the player as victim); 0x45c490 fills all ten from
 *         tuning+0x404 .. +0x428 (+0x41c / +0x420 the two heads: read as 'the game's own', never written). An NPC
 *         shooter turns a head into a body hit before the table is asked (0x61ac87, 0x4db7e7), so in Arcade - one human -
 *         the two globals are 'the HUMAN's head shot on any NPC', police AI and heisters alike. Written every pass while
 *         the dial acts, the tuning's values back otherwise; a value found there that is neither is left alone.
 *       [Fed] Hunted (asked for in case the AI heisters did not treat a police human as an enemy): NOT BUILT - by the
 *         reading they do; it is OWED if TH shows no 'you lost' line within 30 s in sight of live heisters.
 *    a9. LOGGING THE CREW'S HITS, key LogCrewHits=1 (2026-10-18; NOT RUN; default 0 = no pass, no line, nothing; needs
 *       Enable=1 like the rest). Why: re\hotcoffee2_losses.md / re\crew_hits.md - what kills the AI heisters at the Hot
 *       Coffee II diner (police, a blast or friendly fire)? A READING, not a wrapper: every 50 ms, in any Arcade round (stock
 *       level or not: nothing is written), the health object of each AI heister ([actor+0x5fc]: current [+4], maximum
 *       [+8], owner [+0x24]) is compared with the last pass. A drop is one line: record, actor, stage, health before ->
 *       after, place, your distance and the
 *       nearest other heister's, down or not, then WHO COULD HAVE DONE IT (a9b below). The killing blow is listed and a death (status 7) gets a line with the last drop and its 'who'. NO health-object ticks or [actor+0x600] are logged: the ticks are a clock minus a delay and +0x600 is the head-hit sum klcensor pre-arms. At
 *       most 6 lines a second and 400 a round, the rest counted; a sum line (drops, lost per record) when the round ends.
 *       LogCrewHitsBig=N (2026-10-19, default 0 = off; NOT RUN): a drop of N or more in one pass is listed past both limits,
 *       tagged BIG (L93 hit the 400 at 00:20:24.9, so rec 1's 340 one-shot at 00:22:17 had only its DIED line).
 *       A rise (regeneration, a get-up) and a change of the maximum (Tough, FedHealth) are no hit. WHAT IT CANNOT SAY:
 *       the attacker, the weapon or the damage kind, and two hits within one pass are one line. The route to those -
 *       ZSoldier slot 96 (0x8473a0), hit record +0x00 attacker, +0x08 kind, +0x28 amount - needs a private soldier vtable,
 *       and seven modules (kladren, klbotdown, kldown, klescort, klhop, klgrudge, klmove) know a crew soldier by the
 *       stock one: it is NOT built (re\crew_hits.md 5, option A).
 *    a9b. WHO COULD HAVE DONE IT (2026-10-18; NOT RUN; still zero writes, no wrapper). A soldier's CURRENT TARGET is [soldier+0xac]
 *       (a pointer to the target's object; for a man it is his ZFFActor), valid while [soldier+0xb0] (a dword, 'has a target') is
 *       not 0: kl2 0x8c62ec `cmp [eax+0xb0],0` returns at once, 0x8c630c / 0x8c6334 read [S+0xac] as the thing whose distance is
 *       taken and whose vtable +0x120 receives the ProjectileHit (CERTAIN, re\melee_damage.md 2; klr_pb_step uses +0xac the same
 *       way). klbotdown.c NoFire clears +0xb0, so +0xac may be STALE then: it is only read while +0xb0 is set. When a drop is
 *       seen, ONE walk of the entity table (klcensus.c's: 64 slots a read) lists the living soldiers (actor, team, place, target);
 *       cost only in a pass that wrote a line or saw a death. The line then says: how many soldiers aim at the victim and the
 *       nearest four (crew record / TRAITOR from the crew record's flag bit 2, Enemy = team 1 'police / guard', distance in
 *       metres = units / 100), the nearest living non-Ally soldier and whom he aims at, and the nearest Ally aiming at the
 *       victim (a FRIENDLY-FIRE CANDIDATE). No aimer and more than KLR_CH_BIG (25 %) of the maximum lost in one pass gets
 *       'NO AIMER ... blast / fall / script?'. GUESSES: that a soldier aiming at the victim is the one who hit him (a soldier
 *       may aim and not fire, or miss, or the bullet may be a stray from someone aiming at another man); that team 1 is
 *       police AND guards (no other team separates them); that +0xac is cleared when the soldier loses the target (stale
 *       values may name a victim for an instant); that the YOU shooter, grenades, fire, vehicles and the helicopter are not
 *       soldiers and so show only as 'no aimer'. The human (ZFFPlayer) is never listed.
 *
 *    a4. THE POINT-BLANK RULE, keys PointBlankToYou / PointBlankToCrew / PointBlankToCop (2026-10-11; NOT RUN IN THE
 *       GAME; re\melee_damage.md has the reading and every address). What looks like a guard's melee is a rule of the
 *       soldier's FIRE TASK (kl2 0x8c62e0, called at every step of a burst, 0.1 .. 0.2 s): while his target is within
 *       160 units (1.6 m, node to node, height counts) he sends it a 'ProjectileHit' of his own gun with the hit
 *       record's scale [hit+0x18] = 100.0 (0x8c63a1 fld [0xb5c050] / 0x8c63aa) and the head bone, which an NPC shooter
 *       turns into a body hit. The victim's ordinary bullet routine multiplies by that float (0x4db8a2 the player,
 *       0x61acc6 an NPC) AND by the six factors above, so the dial does scale it - it is one bullet x 100: a Type 79
 *       guard costs 72.0 x 1.05 x 100 x CopToYou = 151.2 a step at 0.02 (the three 'you lost 151.2' of run
 *       K2b_DM03_wall_log), 7,560 at Risk=2's 1.0, and an AI heister 72.0 x 1.2 x 100 x CopToCrew.
 *       No float that only this hit reads exists as data: the 100.0 is a constant in hashed .rdata with 138 users, and
 *       the record's copy is written anew at every call. But between that store and the send the routine makes a
 *       VIRTUAL call on a heap object: the name look-up of 'ProjectileHit', slot 19 (+0x4c, 0x698840: thiscall, four
 *       arguments, ret 0x10) of the one ZEngineDataBase [[0xdd2640]+0xac] (0x8c63fc .. 0x8c641c), with the record's
 *       address already pushed for the send (0x8c63f4) right above the look-up's four arguments. So, as klchar.c does
 *       for the option object: a private copy of the 74-slot vtable 0xb8fa04 (RTTI locator in front) with slot 19
 *       wrapped, its address written into the object's first dword. The wrapper compares its return address with
 *       0x8c641e - every other of the game's about 450 call sites of that slot is passed straight on - and there
 *       checks the record (file argument 0xb22648, [rec] == rec + 0x20, bone id 7 at rec + 0x48, scale exactly 100.0,
 *       attacker == the soldier's actor) and writes the key's number over the 100.0, by the VICTIM:
 *         PointBlankToYou    the target is a ZFFPlayer (you, on either side)
 *         PointBlankToCrew   the target is a ZFFActor of team Ally (an AI heister; a traitor is still Ally)
 *         PointBlankToCop    the target is any other ZFFActor (police, guards, civilians: an AI heister's own steps)
 *       The number is how many ordinary bullets of his gun one step is worth: 100 = the game's own (the steps are then
 *       seen and logged, nothing is written: the dry run), 1 = one bullet, 0 = none; no key or a negative number = that
 *       victim is left alone. NOT part of the Risk dial: no Risk sets a value (the game's rule is the same in every
 *       mode and on every Arcade level, so Ramp has nothing to hold either) - whether Risk=2 should imply one is the
 *       owner's call. Nothing has to be put back in a record: 0x8c63aa writes 100.0 again at the next step.
 *       WHEN: the copy is written into the object only while the dial acts (an Arcade session, a level that is not
 *       stock), from the game's own thread; the game's vtable pointer goes back the first pass after (any thread: one
 *       aligned dword, both tables are valid for ever), and a flag makes the wrapper pass everything on from the moment
 *       the dial stops acting. The copy is made ONCE per process and never changed afterwards (a TEST build's klauto.c
 *       pokes entry 8 of the stock table at start-up under policy 'direct': it is in the copy).
 *       RISKS, all unseen: hook code now runs inside a call the game makes from about 450 places (it is one compare
 *       and the game's own routine); the record is found one dword above the look-up's arguments, which holds for
 *       build 0490 only (klr_tick does nothing on another exe) and is why five things are checked before the write;
 *       ASSUMED that nothing compares the object's first dword with 0xb8fa04 (the address stands in the image twice,
 *       in the constructor's and the destructor's stamp) and that the fire task runs on the main loop's thread (the
 *       first step's log line says which thread it was). Needs [KLHook] Tick=1 (the default).
 *    b. THE PLAYER'S HEALTH. The tuning block is read when the player object is made, before this hook knows the
 *       level; so the LIVE health object is written instead: H = [player+0xa48] of the local player (ZFFPlayer,
 *       vtable 0xbb45f4; [H+0x24] is the player again, 0x4aadaf), from the game's own thread only:
 *       [H+0x08] maximum = (the maximum the game gave) * PlayerHealth, [H+0x04] lowered to it when above,
 *       [H+0x14] / [H+0x18] the two regeneration times. When the game writes a new maximum (a new round, armour),
 *       that becomes the base and is scaled again. A player who is a policeman ([player+0x2723], klfed.c's fed) is
 *       under the same dial while FedMirror=1 and left alone with FedMirror=0 (until 2026-10-11: always left alone -
 *       550 and 4 s / 4 s beside a hero of 401.5 and 8 s / 8 s). Each object has its own record (klr_pl): the hero is
 *       the local player again in the round after a fed round and must not be taken for a new object.
 *       The game's values go back when the hook stops acting while the object still lives.
 *       ASSUMPTION: nothing but 0x8ab200 / the HUD derives anything from the maximum that a smaller one breaks;
 *       the 16-bit copy at [player+0x274c] (what a session peer would be sent, 0x6443b8) is NOT written - Arcade
 *       has no peer.
 *    c. THE LOG (Log=1, on any level): once per round object the Arcade level, the campaign difficulty, the seven
 *       stock factors of every level ('... crew off your stage x 0.50'), the three player blocks and the player's
 *       health object as found - the first live run thereby checks every number of section 1. Log=2 adds a line for
 *       every loss of health of the player ('you lost 6.1'): with one policeman shooting, that IS gun damage times
 *       CopToYou. Nothing logs what a heister's bullet costs a policeman: the seventh shows in its lines only.
 *       With a point-blank key (2 a4), at any Log level: one line when the copy of the vtable goes in and one when the
 *       game's own is back, with the steps counted by victim; Log=2 adds a line for every step seen ('point-blank
 *       step: ... the hit's scale 100 -> 2.00'), the first 200 of an arming.
 *
 * 3. NOT DONE HERE
 *    NPC health per class (level data: kl_map_ai's rows; Tough, 2 a7, is one factor for all of them), accuracy (ZSoldier field 4: 100 on M01 / M02 / M03, 55 in stock -
 *    with CopToYou 1.0 that may be too much; re\balance.md 6 has the level-side answer), the campaign difficulty
 *    global (written by the option system and saved to the profile: only read here), the body part table but for the
 *    two head floats (2 a8).
 *
 * WIRING (klhook.c; nothing else of the hook changes)
 *   #include "klbalance.c"       after  #include "klbot.c"      (it uses klb_level, the 'not the stock level' test)
 *   klr_tick(game_thread);       in klh_tick, after  klb_tick(game_thread);
 *   klr_init();                  in the init list, after  klb_init();
 * KLHook.ini: section [Balance] (sample at the end of re\balance.md).
 */
#ifndef KLBALANCE_C
#define KLBALANCE_C

#define KLR_SESSION   0x0168e598              /* +0x54, +0x5c = mode (4 = Arcade), +0x70 = state */
#define KLR_SETTINGS  0x0168e9e4              /* +0x54 = the rules object */
#define KLR_TUNING    0x0168d7c0              /* the tuning object (heap, no vtable) */
#define KLR_GAMEDATA  0x00dd265c              /* +0x828 + 4 * i players, +0x898 the local player's index */
#define KLR_DIFF      0x0156b5f0              /* the option Difficulty, 0..3 (.bss; read only) */
#define KLR_RULES_VT  0x00bd3514              /* ZGameRulesHeist */
#define KLR_PLAYER_VT 0x00bb45f4              /* ZFFPlayer */
#define KLR_NLEVEL    11
#define KLR_NF        6                       /* the floats at R+0x00, +0x04 .. +0x14 */
#define KLR_OFF       0x1c                    /* the seventh: an Ally NPC shooter at another heist stage than the player */
#define KLR_ABS(x)    ((x) < 0 ? -(x) : (x))
/* Tough and the head factor (sections 2 a7 / a8; every address read 2026-10-11, re\balance.md 11) */
#define KLR_ROWS      0x42c                   /* tuning: the four story difficulty rows of 0x24 bytes; +8 = NPC health (0x8fbb5b, 0x74d99c) */
#define KLR_ROWPTR    0x594                   /* tuning: four pointers to them, picked by the option Difficulty (0x831f4b) */
#define KLR_HEAD_SRC  0x41c                   /* tuning: the body-part factors of bone types 2 / 3 as 0x45c490 copies them out (+0x41c, +0x420) */
#define KLR_HEAD_G2   0x00cdeffc              /* .data: bone type 2 (0x572fb9) */
#define KLR_HEAD_G3   0x00cdf000              /* .data: bone type 3 (0x572f71) */
/* the point-blank rule (section 2 a4; every address read 2026-10-11, re\melee_damage.md) */
#define KLR_ACTOR_VT  0x00bb3bac              /* ZFFActor */
#define KLR_DB_VT     0x00b8fa04              /* ZEngineDataBase; the one object is [[0xdd2640]+0xac] (0x8c63fc / 0x8c6401) */
#define KLR_DB_NSLOT  74
#define KLR_DB_SLOT   19                      /* +0x4c: name -> id; thiscall (name, id asked for, file, line), ret 0x10 */
#define KLR_DB_FN     0x00698840              /* the game's routine in that slot (no other pointer to it, no direct call) */
#define KLR_PB_RET    0x008c641e              /* where the fire task's call of the slot returns to (call edx at 0x8c641c) */
#define KLR_PB_FILE   0x00b22648              /* 'ff2\scripts\soldier\fireweapontask.cpp': pushed at 0x8c6410 and nowhere else */
#define KLR_PB_STOCK  100.0f                  /* 0x8c63a1 fld [0xb5c050] / 0x8c63aa fstp [task+0x30] = hit record +0x18 */
#define KLR_PB_NWHO   3
#define KLR_PB_LINES  200                     /* Log=2: steps listed per arming; the rest are counted only */
/* the crew-hit log (section 2 a9) */
#define KLR_SOLDIER_VT 0x00bd0954             /* ZSoldier: crew and police share it (klbotdown.c KLBD_SOLDIER_VT) */
#define KLR_CH_CLOCK  0x00dd2640              /* +0x48 the game's tick, 1/1024 s (klbotdown.c KLBD_CLOCK) */
#define KLR_CH_ROUND  0x19                    /* session state of a round in play (klbotdown.c KLBD_ROUND) */
#define KLR_CH_PERSEC 6                       /* lines a second */
#define KLR_CH_ROUND_MAX 400                  /* lines a round; the rest are counted only */
#define KLR_CH_SOLMAX 256                     /* living soldiers listed in a pass (Hasta's biggest rounds hold ~100 ZFFActors) */
#define KLR_CH_AIMERS 4                       /* aimers named in a line (the rest are counted) */
#define KLR_CH_BIG    0.25f                   /* a loss of this part of the maximum in one pass, with no aimer, gets the 'blast / fall / script?' tag */

static int klb_level(char why[200]);          /* klbot.c: 1 only on a level whose archive is NOT the stock one */
#define KLR_DOWN 2
static float kld_factor(int k); static int kld_moving(void); static float kld_pb(float want); static int kld_pb_key(void);       /* kldown.c (track R8) */

static const char *const klr_key[KLR_NF] = { "CopToCrew", "CrewToCop", "CopToYou", "YouToCop", "CrewToYou", "YouToCrew" };
static const int klr_kind[KLR_NF] = { 1, -1, 1, -1, 1, 0 };      /* Ramp: 1 = at least stock, -1 = at most stock, 0 = as given */
static const struct { float f[KLR_NF], health, delay, full, off; } klr_dial[4] = {       /* off = CrewOffStage, -1 = not written */
    { { -1, -1, -1, -1, -1, -1 }, 0, 0, 0, -1 },
    { { 0.5f, 1.5f, 0.5f, 1.5f, 0.5f, 1.0f }, 1.0f, 0, 0, 0.75f },                        /* 0.75: a GUESS, halfway from stock's 0.5 to none */
    { { 1, 1, 1, 1, 1, 1 }, 0.73f, 8, 8, 1 },
    { { 1, 1, 1, 1, 1, 1 }, 0.51f, 8, 8, 1 },
};
/* what 0x524050 writes (re\balance.md 2): only compared with what is found, for one log line */
static const float klr_code[KLR_NLEVEL + 1][KLR_NF] = {
    { 0 },
    { 0.01f, 3.0f, 0.1f, 2.0f,  0.1f, 0.25f }, { 0.05f, 2.6f, 0.2f, 1.75f, 0.2f, 0.5f }, { 0.1f,  2.2f, 0.4f, 1.5f,  0.4f, 1.0f },
    { 0.15f, 1.9f, 0.8f, 1.25f, 0.8f, 0.9f },  { 0.2f,  1.6f, 1.0f, 1.0f,  1.0f, 0.8f }, { 0.25f, 1.3f, 1.3f, 0.9f,  1.1f, 0.7f },
    { 0.3f,  1.0f, 1.6f, 0.8f,  1.2f, 0.6f },  { 0.35f, 0.8f, 1.9f, 0.7f,  1.3f, 0.5f }, { 0.4f,  0.4f, 2.2f, 0.6f,  1.4f, 0.4f },
    { 0.45f, 0.2f, 2.6f, 0.5f,  1.5f, 0.3f },  { 0.5f,  0.1f, 3.0f, 0.3f,  1.7f, 0.1f },
};
/* The float at +0x1c as 0x524050 writes it (0x52b84d for level 1; read 2026-10-11). Unlike klr_code this one GATES:
   the seventh factor is written only into a table whose eleven values are these. */
static const float klr_code_off[KLR_NLEVEL + 1] = { 0, 0.5f, 0.5f, 0.5f, 0.4f, 0.3f, 0.3f, 0.2f, 0.2f, 0.2f, 0.1f, 0.1f };

/* a police player reads the OTHER float of each pair (section 2 a3): slot k then holds the meaning of key klr_mir[k] */
static const int klr_mir[KLR_NF] = { 1, 0, 4, 5, 2, 3 };

static struct {
    int on, log, risk, ramp, any;
    int mirror;                               /* FedMirror: the pairs are written exchanged while the local player is police */
    float f[KLR_NF];                          /* < 0 = leave this factor as the game has it */
    float health, delay, full;                /* 0 = leave */
    float off;                                /* CrewOffStage; < 0 = leave +0x1c as the game has it */
    float fed;                                /* FedToCrew (2 a5); < 0 = a police player's bullet on a heister is YouToCrew's number */
    float tofed;                              /* CrewToFed (2 a8); < 0 = a heister's bullet on a police player is CrewToYou's number */
    float tough;                              /* Tough (2 a7); 0 = off */
    float head, fedhead;                      /* HeadShot / FedHeadShot (2 a8); < 0 = the game's own */
} klr;

struct klr_row { float f[KLR_NF]; float off; };           /* off = the float at +0x1c */
struct klr_val { float v0, wrote; };          /* v0 = what the game gave, wrote = what the hook put there (0 = nothing) */
/* One record per health object seen: a fed round has TWO local player objects in turn (the hero, then a police body) and
   the hero is the local one again in the next round, still holding what the hook wrote into it. A record found again
   is not 'fresh': its v0 is still what the GAME gave (review S3 of re\balance_fedmirror_review.md: taken as fresh, the
   hook's own 401.5 would have been scaled a second time until the game wrote a new maximum). rules = the round object
   the record was made under: another one is another level's objects, even at the same addresses. */
struct klr_pl { DWORD player, h, rules, used; struct klr_val max, delay, full; float seen;
                float clamp, clampto; };      /* a HURT man's health before this file lowered it to a smaller maximum, and that maximum
                                                 (review X2 S2: a put-back followed by a raise must not heal him); 0 = none */
static struct { int have; DWORD clock; struct klr_pl e[4]; } klr_p;

static int klr_finite(float f) { return f == f && f > -1e9f && f < 1e9f; }

/* -> 1 when an Arcade session with a ZGameRulesHeist object is up; state = [session+0x70], level = 1..11 */
static int klr_arcade(DWORD *rules, DWORD *state, int *level)
{
    DWORD sm, gs, score, sub = 0; BYTE b = 0;
    *rules = *state = 0; *level = 1;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLR_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x54, &sub, 4) || sub == 2 || sub == 3) return 0;
    if (!klh_rd(sm + 0x70, state, 4)) return 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLR_SETTINGS))) || !(*rules = klh_rd32(gs + 0x54)) || klh_rd32(*rules) != KLR_RULES_VT) return 0;
    if (!(score = klh_rd32(*rules + 0x5f8)) || !klh_rd(score + 0x45, &b, 1)) return 0;
    *level = (signed char)b < 1 ? 1 : b > KLR_NLEVEL ? KLR_NLEVEL : b;         /* the clamp every reader in the game applies */
    return 1;
}

/* The eleven records as they are now; 0 when the object does not hold the table where this build expects it (it
   has no vtable to check): six factors in 0..50 and the retaliation limit at +0x18 in 1..100000, per level.
   The float at +0x1c is taken along as found: it has its own, stricter test (klr_code_off) and does not change
   what the six need. */
static int klr_table(DWORD tun, struct klr_row out[KLR_NLEVEL + 1])
{
    int L, k;
    for (L = 1; L <= KLR_NLEVEL; L++) {
        float fv[0x20 / 4];
        if (!klh_rd(tun + 0x6ac + 0x70 * L, fv, sizeof fv)) return 0;
        for (k = 0; k < KLR_NF; k++) { if (!klr_finite(fv[k]) || fv[k] < 0 || fv[k] > 50) return 0; out[L].f[k] = fv[k]; }
        if (!klr_finite(fv[0x18 / 4]) || fv[0x18 / 4] < 1 || fv[0x18 / 4] > 100000) return 0;
        out[L].off = fv[KLR_OFF / 4];
    }
    return 1;
}

static float klr_want(int k, float stock)
{
    float v = klr.f[k];
    if (v < 0) return stock;
    if (klr.ramp && klr_kind[k] > 0 && stock > v) return stock;
    if (klr.ramp && klr_kind[k] < 0 && stock < v) return stock;
    return v;
}

/* The seventh factor for one level, s = the level's stock row. Ramp: an AI heister at another stage than the player
   deals crew->police x this factor (0x591bd4 fld [R+4] ... 0x591c20 fmul), so the six's rule 'damage dealt to the
   police is at most stock's' is applied to that PRODUCT: the factor is at most stock's product over the crew->police
   the dial leaves on the level. Where the dial does not lower crew->police that limit is stock's own factor, taken
   exactly (no arithmetic: the value must compare equal to what is in the table). A number BELOW the limit is the
   user's and is written as given. */
static float klr_want_off(const struct klr_row *s)
{
    float v = klr.off, c2c, lim;
    if (v < 0) return s->off;
    if (!klr.ramp) return v;
    c2c = klr_want(1, s->f[1]);
    if (c2c >= s->f[1]) lim = s->off;
    else if (c2c <= 0) return v;              /* crew->police 0: the product is 0 whatever stands here */
    else lim = s->off * (s->f[1] / c2c);
    return v < lim ? v : lim;
}

/* " 0.50 0.50 ..." of the eleven levels: what stands at +0x1c in stock (which 0) or what the dial wants there (1) */
static const char *klr_off_row(const struct klr_row stock[KLR_NLEVEL + 1], int which, char out[96])
{
    int L, n = 0;
    out[0] = 0;
    for (L = 1; L <= KLR_NLEVEL && n < 96 - 8; L++) n += snprintf(out + n, 96 - n, " %.2f", which ? klr_want_off(&stock[L]) : stock[L].off);
    return out;
}

/* 1 when the local player object is a ZFFPlayer whose police byte is set (klfed.c's fed); 0 also when anything of it
   cannot be read - the table then stays in the ordinary order. Reads only. */
static int klr_local_police(void)
{
    DWORD gd, pl; BYTE idx = 0xff, police = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLR_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || (signed char)idx < 0 || idx > 31 ||
        !(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_rd32(pl) != KLR_PLAYER_VT || !klh_rd(pl + 0x2723, &police, 1)) return 0;
    return police != 0;
}

/* ---------------------------------------------------------------- YouToCrewFar (section 2 a6) */

#define KLR_FAR_B     0xac4                   /* rules: float B[victim * 12 + attacker], the twin sum of 0x4d17f0 (klgrudge.c never writes it) */
static struct {
    float far_, near_at, far_at; DWORD hold;  /* far_ <= 0 = off; world units (100 = 1 m); ms */
    DWORD rules; char have[KLB_NREC]; float b[KLB_NREC]; DWORD actor[KLB_NREC];
    int tgt, why, said_tgt, said_why; DWORD hit_at, said_at; float mult, said_mult;
} klr_far;

/* -> what YouToCrew is multiplied with now: 1 = nothing (the key is off, no round runs, you are police / the traitor /
   out of play, nobody can be placed). Reads only; why: 1 your last hit, 2 a turned heister, 3 the farthest. */
static float klr_far_mult(DWORD now)
{
    struct klb_snap s; DWORD gd, pl, fl = 0; BYTE sel = 0xff, type = 0, police = 0, traitor = 0;
    float feet[3], bp[3], d, dsel = -1, dfar = -1, dturn = -1, dtgt = -1, m; int i, why = 0, who = -1, ifar = -1, iturn = -1;
    if (klr_far.far_ <= 0) return 1.0f;
    if (!klb_read(&s) || s.state != KLB_ROUND || s.human != 0) { klr_far.rules = 0; return klr_far.mult = 1.0f; }      /* 0x4d17f0 wires attacker 0 */
    if (s.rules != klr_far.rules) {
        float f = klr_far.far_, a = klr_far.near_at, b = klr_far.far_at; DWORD h = klr_far.hold;
        memset(&klr_far, 0, sizeof klr_far); klr_far.far_ = f; klr_far.near_at = a; klr_far.far_at = b; klr_far.hold = h;
        klr_far.rules = s.rules; klr_far.tgt = klr_far.said_tgt = -1; klr_far.mult = klr_far.said_mult = 1.0f;
    }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLR_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3 || !(pl = klh_rd32(gd + 0x828 + 4 * sel)) ||
        klh_rd32(pl) != KLR_PLAYER_VT || !klh_rd(pl + 0x273c, &type, 1) || type != 2 || !klh_rd(pl + 0x2723, &police, 1) || !klh_rd(pl + 0x2726, &traitor, 1) ||
        !klh_rd(pl + 0x460, feet, 12) || !klr_finite(feet[0]) || !klr_finite(feet[1]) || !klr_finite(feet[2])) return klr_far.mult = 1.0f;
    klh_rd(s.score + 0x1d4, &fl, 4);          /* your dword of the score table: bit 1 = you are the traitor (slot 114 = 0x771a10) */
    for (i = 0; i < s.n && i < 12; i++) {     /* the sums are rows of 12 */
        const struct klb_rec *r = &s.r[i]; float bsum = 0;
        if (!r->used || !(r->flags & 1) || !r->actor) { klr_far.have[i] = 0; if (klr_far.tgt == i) klr_far.tgt = -1; continue; }
        if (r->actor != klr_far.actor[i]) { klr_far.actor[i] = r->actor; klr_far.have[i] = 0; if (klr_far.tgt == i) klr_far.tgt = -1; }
        if (klh_rd(s.rules + KLR_FAR_B + 0x30 * i, &bsum, 4) && klr_finite(bsum)) {
            if (klr_far.have[i] && bsum > klr_far.b[i] + 0.001f) { klr_far.tgt = i; klr_far.hit_at = now ? now : 1; }      /* the game counted a hit of yours on him */
            klr_far.have[i] = 1; klr_far.b[i] = bsum;
        }
        if (r->status != 0 || klh_avt(r->actor) != KLR_ACTOR_VT || !kle_node(klh_rd32(r->actor + 4), bp, 0)) { if (klr_far.tgt == i) klr_far.tgt = -1; continue; }
        d = (float)sqrt((bp[0] - feet[0]) * (bp[0] - feet[0]) + (bp[1] - feet[1]) * (bp[1] - feet[1]) + (bp[2] - feet[2]) * (bp[2] - feet[2]));
        if (!klr_finite(d)) continue;
        if (d > dfar) { dfar = d; ifar = i; }
        if ((r->flags & 2) && (dturn < 0 || d < dturn)) { dturn = d; iturn = i; }
        if (klr_far.tgt == i) dtgt = d;
    }
    if (police || traitor || (fl & 1) || s.r[0].status != 0) return klr_far.mult = 1.0f;
    if (klr_far.tgt >= 0 && (now - klr_far.hit_at > klr_far.hold || dtgt < 0)) klr_far.tgt = -1;
    if (klr_far.tgt >= 0) { why = 1; who = klr_far.tgt; dsel = dtgt; }
    else if (iturn >= 0) { why = 2; who = iturn; dsel = dturn; }
    else if (ifar >= 0) { why = 3; who = ifar; dsel = dfar; }
    else return klr_far.mult = 1.0f;          /* no AI heister in play can be placed */
    m = dsel <= klr_far.near_at ? 1.0f : dsel >= klr_far.far_at ? klr_far.far_ : 1.0f + (klr_far.far_ - 1.0f) * (dsel - klr_far.near_at) / (klr_far.far_at - klr_far.near_at);
    m = (float)((int)(m * 50.0f + 0.5f)) / 50.0f;      /* steps of 0.02: the table is not written at every step he takes */
    if (klr.log >= 2 && (who != klr_far.said_tgt || why != klr_far.said_why || KLR_ABS(m - klr_far.said_mult) >= 0.1f) && now - klr_far.said_at >= 1000) {
        klr_far.said_tgt = who; klr_far.said_why = why; klr_far.said_mult = m; klr_far.said_at = now;
        klog("balance: far: your bullet on a heister is priced for record %d at %.1f m (%s): you->crew x %.2f (YouToCrewFar %.2f, from %.0f m to %.0f m)", who, dsel / 100,
             why == 1 ? "your last hit was on him" : why == 2 ? "no hit of yours in the hold time: the nearest heister that has turned" : "no hit of yours in the hold time: the farthest heister in play",
             m, klr_far.far_, klr_far.near_at / 100, klr_far.far_at / 100);
    }
    klr_far.why = why;
    return klr_far.mult = m;
}

/* ---------------------------------------------------------------- CopToYouFar (balance2, 2026-10-23)
   A range falloff for what a POLICEMAN's bullet costs the human: x 1 within NearAt, x CopToYouFar from FarAt on, linear
   between, priced for the distance to the man who fired the last bullet that hit you.
   GUESS 1: the game keeps the last attacker of the player at [player+0x2778] (kldown.c reads it the same way); it is set at
   the bullet, but whether before or after the hit reads the table is not known, so the FIRST bullet of a new attacker may
   be priced for the previous one. GUESS 2: team != 2 (Ally) = police / guard (kldown.c's reading). GUESS 3: one float
   (police->you) is shared by all police, so with several shooters the last one's distance prices all. Default: off. */
static struct { float far_, near_at, far_at; DWORD att; float mult, said; DWORD said_at; DWORD rules, t_hit, t_chg, cur; float hp; } klr_cf;      /* cur: the attacker the price in mult is for (att is the log's) */
#define KLR_CF_STALE 2000   /* ms without a health drop of the human: the last attacker is stale, price x 1 (review 4) */
#define KLR_CF_HOLD   300   /* ms a new shooter's range is held back against a flip between shooters (review 3) */

static float klr_cop_mult(DWORD now)
{
    struct klb_snap s; DWORD gd, pl, att, sc, team = 99; BYTE sel = 0xff, type = 0, police = 0, traitor = 0;
    float feet[3], bp[3], d, m; DWORD fl = 0;
    if (klr_cf.far_ <= 0) return 1.0f;
    if (!klb_read(&s) || s.state != KLB_ROUND || s.human != 0) { klr_cf.rules = 0; return klr_cf.mult = 1.0f; }
    if (s.rules != klr_cf.rules) { klr_cf.rules = s.rules; klr_cf.att = klr_cf.cur = 0; klr_cf.mult = 1.0f; klr_cf.said = 0; klr_cf.said_at = 0; klr_cf.hp = 0; klr_cf.t_hit = klr_cf.t_chg = 0; }      /* a new round: as klr_far (review 6) */
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLR_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3 || !(pl = klh_rd32(gd + 0x828 + 4 * sel)) ||
        klh_rd32(pl) != KLR_PLAYER_VT || !klh_rd(pl + 0x273c, &type, 1) || type != 2 || !klh_rd(pl + 0x2723, &police, 1) || !klh_rd(pl + 0x2726, &traitor, 1) ||
        !klh_rd(pl + 0x460, feet, 12) || !klr_finite(feet[0]) || !klr_finite(feet[1]) || !klr_finite(feet[2])) return klr_cf.mult = 1.0f;
    klh_rd(s.score + 0x1d4, &fl, 4);
    if (police || traitor || (fl & 1) || s.r[0].status != 0) return klr_cf.mult = 1.0f;
    {   /* review 4: a hit is a drop of his health ([pl+0xa48] -> health object, +4 = health, as kldown.c reads it). No drop for KLR_CF_STALE ms = the
           last attacker is old (melee, a blast, a path that does not set +0x2778): x 1. GUESS: every police bullet that hurts him shows as a drop here. */
        DWORD ho = klh_rd32(pl + 0xa48); float hp = 0;
        if (ho && klh_rd(ho + 4, &hp, 4) && klr_finite(hp)) {
            if (klr_cf.hp > 0 && hp < klr_cf.hp - 0.001f) klr_cf.t_hit = now;
            klr_cf.hp = hp;
            if (!klr_cf.t_hit) klr_cf.t_hit = now;                                 /* first sight: fresh */
            if (now - klr_cf.t_hit > KLR_CF_STALE) return klr_cf.mult = 1.0f;
        }
    }
    att = klh_rd32(pl + 0x2778);                                                   /* GUESS 1 */
    if (!att || klh_avt(att) != KLR_ACTOR_VT || !(sc = klh_rd32(att + 0x54)) || !klh_rd(sc + 4, &team, 4) || team == 2) return klr_cf.mult = 1.0f;    /* GUESS 2 */
    if (!kle_node(klh_rd32(att + 4), bp, 0)) return klr_cf.mult = 1.0f;
    d = (float)sqrt((bp[0] - feet[0]) * (bp[0] - feet[0]) + (bp[1] - feet[1]) * (bp[1] - feet[1]) + (bp[2] - feet[2]) * (bp[2] - feet[2]));
    if (!klr_finite(d)) return klr_cf.mult = 1.0f;
    m = d <= klr_cf.near_at ? 1.0f : d >= klr_cf.far_at ? klr_cf.far_ : 1.0f + (klr_cf.far_ - 1.0f) * (d - klr_cf.near_at) / (klr_cf.far_at - klr_cf.near_at);
    m = (float)((int)(m * 50.0f + 0.5f)) / 50.0f;                                  /* steps of 0.02: the table is not written at every step */
    /* review 3: a hold against flipping between shooters. A new attacker's price is taken up only KLR_CF_HOLD ms after the last change
       of the price; the first bullet of a new shooter is still priced for the old one (an approximation, said so in the notes). GUESS: 300 ms. */
    if (att != klr_cf.cur && klr_cf.cur && now - klr_cf.t_chg < KLR_CF_HOLD) return klr_cf.mult;
    if (m != klr_cf.mult || att != klr_cf.cur) klr_cf.t_chg = now;
    klr_cf.cur = att;
    if (klr.log >= 2 && (att != klr_cf.att || KLR_ABS(m - klr_cf.said) >= 0.1f) && now - klr_cf.said_at >= 500) {
        klr_cf.att = att; klr_cf.said = m; klr_cf.said_at = now;
        klog("balance: copfar: last bullet on you came from %08lx at %.1f m: police->you x %.2f (CopToYouFar %.2f, from %.0f m to %.0f m)", att, d / 100, m, klr_cf.far_, klr_cf.near_at / 100, klr_cf.far_at / 100);
    }
    return klr_cf.mult = m;
}

/* arcade: the table is looked at (and logged once, on any level); act: and the level is not stock - only then is
   anything written; otherwise what was written goes back. Data of a heap object; any thread (as klbot.c's Tune). */
static void klr_table_tick(int arcade, int act, int level)
{
    static DWORD tun0; static struct klr_row stock[KLR_NLEVEL + 1]; static int have, applied, toldbad;
    static int offok, toldoff;                /* the seventh: the stock row is the known one; its line was written */
    static int mirwas;                        /* the table stands in the police player's order (section 2 a3) */
    static float farwas = 1.0f;               /* YouToCrewFar (2 a6): the factor the table's +0x14 holds now */
    static float cfwas = 1.0f;                /* CopToYouFar: the factor on police->you now */
    struct klr_row cur[KLR_NLEVEL + 1]; DWORD tun; int L, k, n = 0, nfar = 0, off, mir; float offnow, farm = 1.0f, cfm = 1.0f;
    if (!(tun = klh_rd32((DWORD_PTR)KLH_VA(KLR_TUNING)))) return;
    if (tun != tun0) { tun0 = tun; have = applied = offok = toldoff = mirwas = 0; farwas = cfwas = 1.0f; }
    if (!act) toldoff = 0;                    /* the seventh's line is written once each time the dial starts to act */
    mir = act && klr.mirror && klr_local_police();
    if (!arcade && !applied) return;
    if (!klr_table(tun, cur)) {
        if (arcade && !toldbad++) klog("balance: the tuning object %08lx does not hold the damage table where this build expects it: nothing is written", tun);
        return;
    }
    if (!have) {                              /* first sight in this process: what the game has, before any write of ours */
        int same = 1, badoff = 0; float p[3][5]; DWORD diff = 99;
        have = 1; memcpy(stock, cur, sizeof stock);
        for (L = 1; L <= KLR_NLEVEL; L++) for (k = 0; k < KLR_NF; k++) if (KLR_ABS(cur[L].f[k] - klr_code[L][k]) > 0.001f) same = 0;
        for (L = KLR_NLEVEL; L >= 1; L--) if (!klr_finite(cur[L].off) || KLR_ABS(cur[L].off - klr_code_off[L]) > 0.001f) badoff = L;
        offok = !badoff;
        if (klr.log) {
            klh_rd((DWORD_PTR)KLH_VA(KLR_DIFF), &diff, 4);
            klog("balance: the damage table of the tuning object %08lx %s; campaign difficulty option %lu (0 easy .. 3 extreme: NPC health x 0.5 / 0.9 / 1.15 / 1.3)", tun,
                 same && offok ? "is what the game's code builds" : "DIFFERS from what the game's code builds (re\\balance.md 2) - the lines below are what this process has", diff);
            for (L = 1; L <= KLR_NLEVEL; L++)
                klog("balance: stock, Arcade level %2d: police->crew %.2f  crew->police %.2f  police->you %.2f  you->police %.2f  crew->you %.2f  you->crew %.2f  crew off your stage x %.2f",
                     L, cur[L].f[0], cur[L].f[1], cur[L].f[2], cur[L].f[3], cur[L].f[4], cur[L].f[5], klr_finite(cur[L].off) ? cur[L].off : -1.0f);
            if (klh_rd(tun + 0x5c4, p[0], sizeof p[0]) && klh_rd(tun + 0x5e4, p[1], sizeof p[1]) && klh_rd(tun + 0x604, p[2], sizeof p[2]))
                klog("balance: player blocks (health, s before it comes back, s to come back whole): online %.0f %.1f %.1f | story %.0f %.1f %.1f | Arcade %.0f %.1f %.1f",
                     p[0][4], p[0][2], p[0][3], p[1][4], p[1][2], p[1][3], p[2][4], p[2][2], p[2][3]);
        }
        if (!offok && klr.off >= 0)           /* a refusal is said at any Log level, as the table's own is */
            klog("balance: the float at +0x1c of the damage table is NOT the row this build's code writes (first at Arcade level %d: found %g, known %.2f): CrewOffStage %.2f is NOT written; the six factors are not affected",
                 badoff, klr_finite(cur[badoff].off) ? cur[badoff].off : -1.0, klr_code_off[badoff], klr.off);
    }
    if (!klr.any || (!act && !applied)) return;          /* nothing of ours is in the table: it is not compared and not written */
    off = klr.off >= 0 && offok;              /* the seventh is ours to write: asked for, and the game's row is the known one */
    /* 2 a6: the range factor on +0x14 - not in the pass that arms the dial (that pass's line counts the dial's own
       values), not for a police player (slot 5 then holds another key; FedToCrew is his number) */
    if (act && applied && !mir && klr_far.far_ > 0) farm = klr_far_mult(GetTickCount());
    if (act && applied && !mir && klr_cf.far_ > 0) {                                        /* CopToYouFar */
        /* review 1: kldown.c captures up[0] from this cell while he is up and compares the cell with up[0] x DownFromCop while he is down. So
           the range factor is FROZEN at what the table holds from the knock-down on (factor wanted, or 400 ms around it) and moves again
           only when he is up for good; otherwise `stand` goes 0 and the down-state switch is put back. */
        if (kld_factor(2) != 1.0f || kld_moving()) cfm = cfwas;
        else cfm = klr_cop_mult(GetTickCount());
    }
    for (L = 1; L <= KLR_NLEVEL; L++) {
        DWORD R = tun + 0x6ac + 0x70 * L;
        for (k = 0; k < KLR_NF; k++) {        /* mir: slot k gets the value the criminal row has for the key a police player reads there -
                                                 only for a pair of which a key is SET: a pair left to the game keeps the game's own swap
                                                 (review M1: with Risk=0 and one key the other 4 x 11 stock values must not move) */
            int kk = mir && (klr.f[k] >= 0 || klr.f[klr_mir[k]] >= 0) ? klr_mir[k] : k;
            float want = act ? klr_want(kk, stock[L].f[kk]) : stock[L].f[k];
            if (act && mir && k == 3 && klr.fed >= 0) want = klr.fed;       /* FedToCrew (2 a5): the float a police player's bullet on an Ally NPC reads (0x7c1bf0) */
            if (act && mir && k == 2 && klr.tofed >= 0) want = klr.tofed;   /* CrewToFed (2 a8): the float an Ally NPC's bullet on a police player reads (0x8b80a0) */
            if (k == 5 && farm != 1.0f) want *= farm;                      /* YouToCrewFar (2 a6) */
            if (k == 2 && cfm != 1.0f) want *= cfm;                        /* CopToYouFar (balance2) */
            if (act && !mir && (k == 2 || k == 4)) want *= kld_factor(k);     /* kldown.c: DownFromCop / DownFromCrew while he is knocked down */
            if (want != cur[L].f[k]) {
                int isfar = act && ((k == 5 && farm != farwas) || (k == 2 && cfm != cfwas) || (applied && !mir && (k == 2 || k == 4) && kld_moving()));               /* a change of the range factor is not the dial's line */
                int w = klh_data((void *)(DWORD_PTR)(R + 4 * k), &want, 4, isfar ? (k == 2 ? "police -> you damage factor by range (CopToYouFar)" : "you -> crew damage factor by range") : "damage factor per Arcade level");
                if (isfar) nfar += w; else n += w;
            }
        }
        if (off) {                            /* a computed number: compared with a margin, so one that is in the table is not written again */
            float want = act ? klr_want_off(&stock[L]) : stock[L].off;
            if (KLR_ABS(want - cur[L].off) > 0.000001f) n += klh_data((void *)(DWORD_PTR)(R + KLR_OFF), &want, 4, "off-stage damage factor per Arcade level");
        }
    }
    farwas = act ? farm : 1.0f; cfwas = act ? cfm : 1.0f;
    if (act && n) applied = 1;
    else if (act && !applied && !n && (klr_far.far_ > 0 || klr_cf.far_ > 0) && !nfar) applied = 1;      /* the dial's own values were in already: the range factor may start */
    if (act && n && mir == mirwas) {          /* a change of the order alone has its own line below (review S5) */
        offnow = off ? klr_want_off(&stock[level]) : klr_finite(stock[level].off) ? stock[level].off : -1.0f;      /* what stands at +0x1c of this level now */
        klog("balance: Risk=%d written for %d Arcade levels (%d value(s) changed, Ramp=%d); now on level %d: police->crew %.2f  crew->police %.2f  police->you %.2f  you->police %.2f  crew->you %.2f  you->crew %.2f  crew off your stage x %.2f - the stock values come back when the session is not Arcade or the level is stock",
             klr.risk, KLR_NLEVEL, n, klr.ramp, level, klr_want(0, stock[level].f[0]), klr_want(1, stock[level].f[1]), klr_want(2, stock[level].f[2]),
             klr_want(3, stock[level].f[3]), klr_want(4, stock[level].f[4]), klr_want(5, stock[level].f[5]), offnow);
    } else if (!act) {
        applied = 0;
        if (n) klog("balance: the stock damage table is back (%d value(s))", n);
    }
    if (!act) mirwas = 0;
    else if (mir != mirwas) {                 /* said at any Log level: it changes what every bullet of the round costs */
        mirwas = mir;
        if (mir) klog("balance: you are POLICE now: the game reads the other float of each pair for a police player, so the three pairs are written exchanged (%d value(s)) and every key keeps its meaning - on level %d a policeman's bullet still costs a heister x %.2f, a heister's a policeman x %.2f, a heister's costs you x %.2f, yours a heister x %.2f (FedMirror=0 = the game's own swap)",
                      n, level, klr_want(0, stock[level].f[0]), klr_want(1, stock[level].f[1]), klr.tofed >= 0 ? klr.tofed : klr_want(4, stock[level].f[4]), klr.fed >= 0 ? klr.fed : klr_want(5, stock[level].f[5]));
        else klog("balance: you are no longer police: the table is in the ordinary order again (%d value(s))", n);
    }
    if (act && off && !toldoff) {             /* once per arming: the seventh on all eleven levels, and what Ramp made of it */
        char a[96], b[96], h[128]; int chg = 0, held = 0; const char *why = "";
        toldoff = 1;
        for (L = 1; L <= KLR_NLEVEL; L++) {
            float w = klr_want_off(&stock[L]);
            if (KLR_ABS(w - stock[L].off) > 0.000001f) chg++;
            if (klr.off - w > 0.000001f) held++;             /* Ramp gave this level less than the number asked for */
        }
        /* no level differs: only Ramp=1 can do that (one number cannot be stock's on eleven levels) */
        if (!chg) why = " - it is NOT written on any level: with Ramp=1 an off-stage heister may not hit police harder than in stock (crew->police x this); a lower CrewToCop (Risk=2 has one) or Ramp=0 lets it through";
        else if (held) {                      /* said only where Ramp really limited something (review N4) */
            snprintf(h, sizeof h, " (Ramp=1 holds it under %.2f on %d level(s): crew->police x this is at most stock's own product there)", klr.off, held);
            why = h;
        }
        klog("balance: crew off your stage (an AI heister at another heist stage than you, his hits on police and every other NPC), Arcade levels 1..11: x%s; stock x%s; CrewOffStage %.2f, Ramp=%d: %d level(s) differ from stock%s",
             klr_off_row(stock, 1, a), klr_off_row(stock, 0, b), klr.off, klr.ramp, chg, why);
    }
}

/* ---------------------------------------------------------------- Tough, the head factor (sections 2 a7 / a8) */

/* what 0x524050 writes at +8 of the four story difficulty rows: this one GATES, as klr_code_off does */
static const float klr_code_npc[4] = { 0.5f, 0.9f, 1.15f, 1.3f };

/* Tough, the NPC half: the four floats 'NPC health x' of the campaign difficulty rows, x Tough while the dial acts and
   the code's own otherwise. Data of the tuning object; any thread (as the damage table). The object has no vtable: the
   four row pointers and the four values are the test that it is laid out as this build's. */
static void klr_tough_tick(int act)
{
    static DWORD tun0; static float stock[4]; static int have, bad, applied;
    DWORD tun, diff = 99; float cur[4], want; int k, n = 0;
    if (klr.tough <= 0 || !(tun = klh_rd32((DWORD_PTR)KLH_VA(KLR_TUNING)))) return;
    if (tun != tun0) { tun0 = tun; have = bad = applied = 0; }
    if ((!act && !applied) || bad) return;
    for (k = 0; k < 4; k++)
        if (klh_rd32(tun + KLR_ROWPTR + 4 * k) != tun + KLR_ROWS + 0x24 * k || !klh_rd(tun + KLR_ROWS + 0x24 * k + 8, &cur[k], 4) || !klr_finite(cur[k])) {
            if (!have) { bad = 1; klog("balance: Tough: the tuning object %08lx does not hold the four campaign difficulty rows where this build expects them (row %d): NPC health is NOT written; your own health still is", tun, k); }
            return;
        }
    if (!have) {                              /* first sight in this process, before any write of ours */
        for (k = 0; k < 4; k++) if (KLR_ABS(cur[k] - klr_code_npc[k]) > 0.001f) bad = 1;
        if (bad) {
            klog("balance: Tough: the 'NPC health x' of the four campaign difficulty rows is %.2f %.2f %.2f %.2f, not the 0.50 0.90 1.15 1.30 this build's code writes: NPC health is NOT written; your own health still is", cur[0], cur[1], cur[2], cur[3]);
            return;
        }
        have = 1; memcpy(stock, cur, sizeof stock);
    }
    for (k = 0; k < 4; k++) {
        want = act ? stock[k] * klr.tough : stock[k];
        if (KLR_ABS(want - cur[k]) > 0.000001f) n += klh_data((void *)(DWORD_PTR)(tun + KLR_ROWS + 0x24 * k + 8), &want, 4, "NPC health factor of a campaign difficulty row");
    }
    if (act && n) {
        applied = 1; klh_rd((DWORD_PTR)KLH_VA(KLR_DIFF), &diff, 4);
        klog("balance: Tough x %.2f: 'NPC health x' of the four campaign difficulty rows %.2f %.2f %.2f %.2f -> %.2f %.2f %.2f %.2f (%d value(s); this profile's option is %lu) - every NPC made from here on (police, guards, AI heisters, civilians) has that much more; the code's values come back when the session is not Arcade or the level is stock",
             klr.tough, stock[0], stock[1], stock[2], stock[3], stock[0] * klr.tough, stock[1] * klr.tough, stock[2] * klr.tough, stock[3] * klr.tough, n, diff);
    } else if (!act) {
        applied = 0;
        if (n) klog("balance: Tough: the code's 'NPC health x' is back in the campaign difficulty rows (%d value(s))", n);
    }
}

/* Tough, the proof: 2 s into every round the maximum health of each AI heister as the game made it (read only). With
   the option Difficulty 1 a stock heister has 252.0 (280 x 0.9): 252 x Tough here = slot 44 ran after the hook's write. */
static void klr_tough_say(DWORD now)
{
    static DWORD rules0, since; static int said;
    struct klb_snap s; char t[320]; int i, n = 0, c = 0; float raw[0x28 / 4]; DWORD h;
    if (klr.tough <= 0 || !klr.log) return;
    if (!klb_read(&s) || s.state != KLB_ROUND) { rules0 = 0; return; }
    if (s.rules != rules0) { rules0 = s.rules; since = now; said = 0; }
    if (said || now - since < 2000) return;
    said = 1; t[0] = 0;
    for (i = 0; i < s.n && i < KLB_NREC && n < (int)sizeof t - 24; i++) {
        const struct klb_rec *r = &s.r[i];
        if (!r->used || !(r->flags & 1) || !r->actor || klh_avt(r->actor) != KLR_ACTOR_VT || !(h =klh_rd32(r->actor + 0x5fc)) ||
            !klh_rd(h, raw, sizeof raw) || ((DWORD *)raw)[0x24 / 4] != r->actor || !klr_finite(raw[2])) continue;
        n += snprintf(t + n, sizeof t - n, " %d: %.1f", i, raw[2]); c++;
    }
    klog("balance: Tough x %.2f: the AI heisters' maximum health this round, by crew record:%s%s (a stock heister has 280 x the difficulty's 0.5 / 0.9 / 1.15 / 1.3 = 140 / 252 / 322 / 364; ALL of them at that number = the game made them BEFORE the hook's write, or the write was refused; ONE odd record is the actor [gamedata+0x4cf0], who takes the row's +0 and not its +8 (0x8fbb29); [Bots] CrewHealth comes on top)",
         klr.tough, c ? t : " none could be read", "");
}

/* HeadShot / FedHeadShot: the two .data floats the body-part routine 0x572f60 hands out for a head. want = the key of
   the side the human is on while the dial acts, else what the tuning object has for them (0x45c490's source; never
   written here). One aligned float each; any thread. A value that is neither the tuning's nor the hook's own last
   write is somebody else's and is left alone (one line). */
static void klr_head_tick(int act)
{
    static const DWORD g[2] = { KLR_HEAD_G2, KLR_HEAD_G3 };
    static float mine[2]; static int told, was = -1;
    DWORD tun; int k, n = 0, police; float key, stock[2], cur, want = 0;
    if (klr.head < 0 && klr.fedhead < 0) return;
    if (!(tun = klh_rd32((DWORD_PTR)KLH_VA(KLR_TUNING))) || !klh_rd(tun + KLR_HEAD_SRC, stock, sizeof stock)) return;
    police = act && klr_local_police();
    key = !act ? -1.0f : police ? klr.fedhead : klr.head;
    for (k = 0; k < 2; k++) {
        if (!klr_finite(stock[k]) || stock[k] < 0.1f || stock[k] > 100 || !klh_rd((DWORD_PTR)KLH_VA(g[k]), &cur, 4)) return;
        want = key >= 0 ? key : stock[k];
        if (cur == want) { if (want == stock[k]) mine[k] = 0; continue; }
        if (cur != stock[k] && (mine[k] == 0 || cur != mine[k])) {
            if (!told++) klog("balance: head shots: the body-part factor at %08lx is %g - neither the tuning object's %g nor a number this hook wrote: HeadShot / FedHeadShot leave it alone", g[k], cur, stock[k]);
            continue;
        }
        if (klh_data((void *)KLH_VA(g[k]), &want, 4, "body-part damage factor of a head")) { n++; mine[k] = want == stock[k] ? 0 : want; }
    }
    if (n && klr.log && (key >= 0 || was >= 0))
        klog("balance: head shots: your bullet on an NPC's head now counts x %.1f (%s; the game's x %.1f / x %.1f for bone types 2 / 3; %d value(s))", want,
             key < 0 ? "the game's own again" : police ? "FedHeadShot: you are police" : "HeadShot: you are a heister", stock[0], stock[1], n);
    if (n) was = key >= 0 ? police : -1;
}

/* One tracked float of the health object: -> what the game gave it. A value that is neither the game's last nor
   ours is a new one of the game's (a new round, armour bought) and becomes the base. */
static float klr_track(struct klr_val *t, float cur, int fresh)
{
    if (fresh) { t->v0 = cur; t->wrote = 0; }
    else if (KLR_ABS(cur - t->v0) > 0.01f && (t->wrote == 0 || KLR_ABS(cur - t->wrote) > 0.01f)) { t->v0 = cur; t->wrote = 0; }
    return t->v0;
}

/* -> values changed. Only called on the game's thread. */
static int klr_put(struct klr_val *t, DWORD at, float cur, float want, const char *what)
{
    if (KLR_ABS(cur - want) <= 0.01f) return 0;
    if (!klh_data((void *)(DWORD_PTR)at, &want, 4, what)) return 0;
    t->wrote = KLR_ABS(want - t->v0) > 0.01f ? want : 0;
    return 1;
}

/* The local player's health object: logged as found, then scaled while act, put back when not. rules = the round
   object of the Arcade session, 0 when there is none (then only an object this file has a record of is looked at: its
   own values go back). A POLICE player (klfed.c's fed): under FedMirror=1 the same dial as the hero's - 'the same risk
   for everybody' (review S2: left alone he had the game's 550 and 4 s / 4 s beside a hero of 401.5 and 8 s / 8 s);
   FedMirror=0: left alone. */
static void klr_player_tick(int act, int game_thread, DWORD rules)
{
    DWORD gd, pl, h; BYTE idx = 0xff, police = 0; float raw[0x28 / 4]; int fresh, n = 0, i; struct klr_pl *p = 0;
    float cur, max, delay, full, max0, delay0, full0, wmax, wdelay, wfull, over = 0, to; int wasfull, samemax;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLR_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || idx == 0xff || (signed char)idx < 0 || idx > 31 ||
        !(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_rd32(pl) != KLR_PLAYER_VT || !(h = klh_rd32(pl + 0xa48)) ||
        !klh_rd(h, raw, sizeof raw) || ((DWORD *)raw)[0x24 / 4] != pl || !klh_rd(pl + 0x2723, &police, 1)) { return; }      /* review D1: a failed read must not make the next pass 'fresh' (it would take our own value as the game's) */
    cur = raw[1]; max = raw[2]; delay = raw[5]; full = raw[6];
    if (!klr_finite(cur) || !klr_finite(max) || !klr_finite(delay) || !klr_finite(full) || max < 1 || max > 100000 ||
        delay < 0 || delay > 3600 || full < 0 || full > 3600) { return; }
    for (i = 0; i < 4; i++) if (klr_p.e[i].used && klr_p.e[i].player == pl && klr_p.e[i].h == h) p = &klr_p.e[i];
    /* A health over the maximum is no health object of the game's - but for one case (review X2 S1): this file RAISED
       both (Tough, a PlayerHealth over 1) and the game has since written a maximum of its own and left the health. Then
       the health is at most what this file wrote as the maximum; it is taken as 'a new maximum of the game's' below
       (new base, scaled again, a line) instead of leaving the hook blind until he is hurt below the game's number. */
    if (cur > max * 1.01f + 1) {
        if (!p || p->max.wrote == 0 || cur > p->max.wrote * 1.01f + 1 || KLR_ABS(max - p->max.wrote) <= 0.01f) return;
        over = p->max.wrote;
    }
    if (!p && !rules) return;                 /* no session and no record of this object: nothing of ours is in it */
    fresh = !p;                               /* a record stays through a failed pass and through the other body's turn */
    if (p && rules && p->rules != rules) {    /* another round object = another level's objects, even at these addresses -
                                                 unless the object still holds what this file wrote into it */
        if (p->max.wrote != 0 && KLR_ABS(max - p->max.wrote) <= 0.01f) p->rules = rules; else fresh = 1;
    }
    if (!p) {                                 /* a free record, else the one not looked at for the longest */
        for (i = 0, p = &klr_p.e[0]; i < 4; i++) { if (!klr_p.e[i].used) { p = &klr_p.e[i]; break; } if (klr_p.e[i].used < p->used) p = &klr_p.e[i]; }
        memset(p, 0, sizeof *p);
    }
    if (fresh) { p->player = pl; p->h = h; p->rules = rules; p->clamp = p->clampto = 0; }
    if (p->clamp != 0 && KLR_ABS(cur - p->clampto) > 0.5f) p->clamp = p->clampto = 0;      /* hurt or refilled since: the note is void */
    p->used = ++klr_p.clock; klr_p.have = 1;
    max0 = klr_track(&p->max, max, fresh); delay0 = klr_track(&p->delay, delay, fresh); full0 = klr_track(&p->full, full, fresh);
    if (fresh) {
        p->seen = cur;
        if (klr.log) klog("balance: your health object %08lx (player %08lx%s): %.1f of %.1f; it starts to come back %.1f s after a hit and is whole %.1f s later", h, pl,
                          !police ? "" : klr.mirror ? ", a POLICEMAN: under the same dial as the hero (FedMirror=1)" : ", a POLICEMAN: left alone (FedMirror=0)", cur, max, delay, full);
    }
    if (klr.log >= 2 && cur < p->seen - 0.05f) klog("balance: you lost %.1f (%.1f of %.1f)", p->seen - cur, cur, max);
    p->seen = cur;
    if (police && !klr.mirror) act = 0;
    wmax = act && klr.health > 0 ? max0 * klr.health : max0;
    if (act && klr.tough > 0) wmax *= klr.tough;          /* Tough (2 a7): on top of PlayerHealth, hero and fed alike */
    if (act) wmax *= kltt_hp(-1);                          /* kltrait.c: Health / DamageIn of the character he wears (1.0 = none) */
    wasfull = cur >= (over > 0 ? over : max) - 0.5f;      /* whole before the write: a RAISED maximum takes a whole health up with it
                                                             (over: whole = at the maximum this file had written, not the game's new one) */
    wdelay = act && klr.delay > 0 ? klr.delay : delay0;
    wfull = act && klr.full > 0 ? klr.full : full0;
    if (act && kltt_get(-1, KLTT_REGEN) != 1.0f) { wdelay /= kltt_get(-1, KLTT_REGEN); wfull /= kltt_get(-1, KLTT_REGEN); }      /* kltrait.c Regen: >1 = he comes back sooner */
    samemax = KLR_ABS(max - wmax) <= 0.01f;
    if (samemax && !over && KLR_ABS(delay - wdelay) <= 0.01f && KLR_ABS(full - wfull) <= 0.01f) return;
    if (!game_thread) return;                 /* a live object of the round: only between two frames of the game itself */
    if (samemax && over > 0) p->max.wrote = 0;      /* the game's own maximum is the one wanted (the dial does not act): only the health this file raised is left to take down */
    if (klr_put(&p->max, h + 8, max, wmax, "the local player's maximum health") || (samemax && over > 0)) {
        n++;
        if (cur > wmax) {
            if (klh_data((void *)(DWORD_PTR)(h + 4), &wmax, 4, "the local player's health, down to the new maximum")) {
                if (!wasfull) { p->clamp = cur; p->clampto = wmax; }      /* a hurt man cut down: remembered, so that a raise gives him this back and no more */
                p->seen = wmax;
            }
        }
        /* Tough / a PlayerHealth over 1: the game filled the object to ITS maximum before the hook saw it; a man who was
           whole is whole under the new one too (never for a hurt man: no healing by a key - one whom this file itself cut
           down to a smaller maximum gets back what he had, review X2 S2). cur > 0: not a dead man's object. */
        else if (wmax > max + 0.01f && wasfull && cur > 0) {
            to = p->clamp != 0 && p->clamp < wmax ? p->clamp : wmax;
            if (to > cur + 0.01f && klh_data((void *)(DWORD_PTR)(h + 4), &to, 4, "the local player's whole health, up to the new maximum")) p->seen = to;
            p->clamp = p->clampto = 0;
        }
    }
    n += klr_put(&p->delay, h + 0x14, delay, wdelay, "the local player's regeneration delay");
    n += klr_put(&p->full, h + 0x18, full, wfull, "the local player's regeneration time");
    if (n && klr.log) klog("balance: your health %s%s: maximum %.1f (the game gave %.1f; PlayerHealth x %.2f, Tough x %.2f), comes back after %.1f s within %.1f s (the game: %.1f / %.1f)%s",
                           act ? "set" : "put back", police ? " (a policeman)" : "", wmax, max0, act && klr.health > 0 ? klr.health : 1.0f, act && klr.tough > 0 ? klr.tough : 1.0f, wdelay, wfull, delay0, full0,
                           over > 0 ? " - the game had written its own maximum again and left the health this hook raised" : "");
}

/* ---------------------------------------------------------------- the point-blank rule (section 2 a4) */

static const char *const klr_pb_key[KLR_PB_NWHO] = { "PointBlankToYou", "PointBlankToCrew", "PointBlankToCop" };
static const char *const klr_pb_who[KLR_PB_NWHO] = { "you", "an AI heister", "a policeman / another NPC" };
static struct {
    int any;                                  /* a key is set: the wrapper goes in while the dial acts */
    float want[KLR_PB_NWHO];                  /* what stands in for the game's 100.0, by victim; < 0 = that victim is left alone */
    volatile LONG act;                        /* 1 only while the dial acts: the wrapper looks at nothing otherwise */
    DWORD vt[KLR_DB_NSLOT + 1];               /* [0] RTTI locator, [1..] the slots; made once, never changed afterwards */
    int ready, told;
    DWORD tid, steptid;                       /* the thread the hook's game tick runs on; the thread the last step came on */
    volatile LONG seen[KLR_PB_NWHO], put[KLR_PB_NWHO], other, odd, lines, first;
} klr_pb;

/* "left at 100" or the key's number */
/* ONLINE point-blank (2026-10-26, BO6, [BotFill] OnlinePointBlank): online the host's Ally bots die to ONE cop step (~7560 hp: the police->crew factor 0x591b60 is skipped because
   0x7f6850 is false for roles 2/3). Same wrapper, mode 2: on the HOST of an online FA round while BotFill's puppeteer has bots, the step on a BOT scales to want bullets. The victim test is
   klbf_pb_is_bot (the actors klbotfill.c's census found in team 2 this second): human heisters are team 2 too and are NOT told apart by the team, so only listed bot actors are touched. */
static struct { float want; } klr_pbo;      /* bullets per step, 0 = off */
static int klbf_pb_is_bot(DWORD actor);
static int klbf_pb_any(void);

static const char *klr_pb_text(int who, char out[24])
{
    if (klr_pb.want[who] < 0) strcpy(out, "left at 100"); else snprintf(out, 24, "%.2f", klr_pb.want[who]);
    return out;
}

/* One step of a soldier's point-blank rule, seen from inside the name look-up the game makes between writing the hit
   record and sending it (0x8c63aa .. 0x8c642a). sp = the address of the wrapper's return address: sp[1..4] the
   look-up's arguments (name, 0, file, line 0x50), sp[5] the record's address pushed for the send at 0x8c63f4, sp[6] the
   send's 0. The record is the fire task's own memory - task + 0x18, the soldier at [task + 4], the trace block at
   task + 0x38 with the bone id at task + 0x60: +0x00 trace, +0x08 the gun, +0x0c the attacker's actor, +0x14 the
   distance, +0x18 the scale. Reads that cannot fault; ONE float written, and only when all of it is as expected. */
static void klr_pb_step(const DWORD *sp)
{
    DWORD rec = sp[5], r[7], seven = 0, sol = 0, tgt = 0, tvt = 0, info, team = 0xff, ateam = 0xff; float found, dist, want; int who, ok; LONG n; char note[80];
    memset(r, 0, sizeof r);
    ok = sp[3] == KLR_PB_FILE && klh_rd(rec, r, sizeof r) && r[0] == rec + 0x20 && klh_rd(rec + 0x48, &seven, 4) && seven == 7 &&
         (sol = klh_rd32(rec - 0x14)) != 0 && r[3] && klh_rd32(sol + 0x40) == r[3] && (tgt = klh_rd32(sol + 0xac)) != 0 && klh_rd(tgt, &tvt, 4) && ((tvt = ((klh_actor_priv && tvt == klh_actor_priv) || (klh_actor_priv2 && tvt == klh_actor_priv2)) ? KLR_ACTOR_VT : tvt), 1);
    memcpy(&dist, &r[5], 4); memcpy(&found, &r[6], 4);
    if (!ok || found != KLR_PB_STOCK) {       /* said at any Log level, three times an arming: it means this file's reading of the call is wrong */
        if (InterlockedIncrement(&klr_pb.odd) <= 3)
            klog("balance: point-blank: a call from %08lx whose record is NOT as expected - left alone (file argument %08lx, record %08lx: first dword %08lx, bone id %lu, scale %g, attacker %08lx, soldier %08lx, target %08lx)",
                 (DWORD)KLR_PB_RET, sp[3], rec, r[0], seven, found, r[3], sol, tgt);
        return;
    }
    if (tvt == KLR_PLAYER_VT) who = 0;
    else if (tvt == KLR_ACTOR_VT) who = (info = klh_rd32(tgt + 0x54)) != 0 && klh_rd(info + 4, &team, 4) && team == 2 ? 1 : 2;      /* team Ally, as 0x8b80a6 / 0x591bc3 test it */
    else {                                    /* a vehicle, a fake target ...: not ours */
        InterlockedIncrement(&klr_pb.other);
        if (klr.log >= 2 && InterlockedIncrement(&klr_pb.lines) <= KLR_PB_LINES)
            klog("balance: point-blank step: soldier %08lx on a target of another class %08lx (vtable %08lx) at %.0f units: left alone", sol, tgt, tvt, dist);
        return;
    }
    InterlockedIncrement(&klr_pb.seen[who]);
    klr_pb.steptid = GetCurrentThreadId();
    want = klr_pb.want[who];
    if (klr_pb.act == 2) want = who == 1 && klbf_pb_is_bot(tgt) ? klr_pbo.want : -1.0f;      /* online: bots only, no other key */
    else if (who == 0) want = kld_pb(want);         /* kldown.c: DownPointBlank while he is knocked down (review 8, M1) */
    if (want >= 0 && want != found && klh_data((void *)(DWORD_PTR)(rec + 0x18), &want, 4, "point-blank hit scale")) InterlockedIncrement(&klr_pb.put[who]);
    else want = found;
    if (klr.log < 2 || (n = InterlockedIncrement(&klr_pb.lines)) > KLR_PB_LINES + 1) return;
    if (n > KLR_PB_LINES) { klog("balance: point-blank: %d steps listed; further ones are counted only (the line that says the game's vtable is back has the sums)", KLR_PB_LINES); return; }
    note[0] = 0;
    if (!InterlockedExchange(&klr_pb.first, 1)) {      /* which thread runs the soldier scripts: ASSUMED the main loop's until this is seen */
        if (klr_pb.steptid == klr_pb.tid) strcpy(note, " [on the main loop's thread]"); else snprintf(note, sizeof note, " [on thread %lu, NOT the main loop's %lu]", klr_pb.steptid, klr_pb.tid);
    }
    if ((info = klh_rd32(r[3] + 0x54)) != 0) klh_rd(info + 4, &ateam, 4);
    klog("balance: point-blank step: soldier %08lx (actor %08lx, team %lu) on %s %08lx at %.0f units: the hit's scale %.0f -> %.2f%s%s", sol, r[3], ateam, klr_pb_who[who], tgt, dist, found, want,
         want != found ? "" : klr_pb.want[who] < 0 ? " (no key for this victim)" : " (the key is the game's own number, or the write was refused: logged only)", note);
}

/* ZEngineDataBase slot 19 as the game calls it (thiscall: edx is no argument). Every name look-up of the game comes
   through here while the copy is in the object: one compare, then the game's own routine with the same arguments.
   Its result is handed back untouched (the id is in ax). */
static DWORD __fastcall klr_pb_name(void *self, void *edx, DWORD name, DWORD id, DWORD file, DWORD line)
{
    (void)edx;
    if ((DWORD_PTR)_ReturnAddress() == (DWORD_PTR)KLH_VA(KLR_PB_RET) && klr_pb.act) klr_pb_step((const DWORD *)_AddressOfReturnAddress());
    return ((DWORD (__fastcall *)(void *, void *, DWORD, DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLR_DB_FN))(self, 0, name, id, file, line);
}

/* act = the dial acts (klr_tick's own test: an Arcade session on a level that is not stock). The copy goes into the
   database object on the game's thread only; the flag and the way back work from any thread (one aligned dword each,
   and both tables stay valid for the life of the process). The game's pointer is written back only where the hook's
   own still stands. */
static void klr_pb_tick(int act, int game_thread)      /* act: 0 off, 1 Arcade dial, 2 online host with bots */
{
    DWORD sys, db, cur = 0, mine = (DWORD)(DWORD_PTR)&klr_pb.vt[1], stock = KLR_DB_VT; int k; char a[24], b[24], c[24], th[96];
    if (act == 1 && !klr_pb.any) return;      /* Arcade with no PointBlank key: untouched; mode 0 must reach the restore branch */
    if (game_thread) klr_pb.tid = GetCurrentThreadId();
    InterlockedExchange(&klr_pb.act, act);
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(db = klh_rd32(sys + 0xac)) || !klh_rd(db, &cur, 4)) return;
    if (!act) {
        if (cur == mine && klh_data((void *)(DWORD_PTR)db, &stock, 4, "database object: the game's own vtable back")) {
            th[0] = 0;
            if (klr_pb.steptid && klr_pb.steptid == klr_pb.tid) strcpy(th, "; the steps came on the main loop's thread");
            else if (klr_pb.steptid) snprintf(th, sizeof th, "; the steps came on thread %lu, NOT the main loop's %lu", klr_pb.steptid, klr_pb.tid);
            klog("balance: point-blank: the game's own vtable %08lx is back in the database object %08lx; steps seen while the hook's copy was in: on you %ld (%ld re-scaled), on AI heisters %ld (%ld), on police / other NPCs %ld (%ld), on other kinds of target %ld, records that were not as expected %ld%s",
                 stock, db, klr_pb.seen[0], klr_pb.put[0], klr_pb.seen[1], klr_pb.put[1], klr_pb.seen[2], klr_pb.put[2], klr_pb.other, klr_pb.odd, th);
        }
        return;
    }
    if (cur == mine || !game_thread) return;
    if (cur != KLR_DB_VT) {
        if (!klr_pb.told++) klog("balance: point-blank: the database object %08lx has vtable %08lx, not ZEngineDataBase's %08lx: the PointBlank keys do nothing", db, cur, (DWORD)KLR_DB_VT);
        return;
    }
    if (!klr_pb.ready) {                      /* once per process: the 74 slots as they stand, the locator in front, slot 19 ours */
        if (!klh_rd((DWORD_PTR)KLH_VA(KLR_DB_VT - 4), klr_pb.vt, sizeof klr_pb.vt)) return;
        if (klr_pb.vt[1 + KLR_DB_SLOT] != KLR_DB_FN) {
            if (!klr_pb.told++) klog("balance: point-blank: slot %d of the database's vtable is %08lx, not %08lx: the PointBlank keys do nothing", KLR_DB_SLOT, klr_pb.vt[1 + KLR_DB_SLOT], (DWORD)KLR_DB_FN);
            return;
        }
        klr_pb.vt[1 + KLR_DB_SLOT] = (DWORD)(DWORD_PTR)klr_pb_name;
        klr_pb.ready = 1;
    }
    for (k = 0; k < KLR_PB_NWHO; k++) { InterlockedExchange(&klr_pb.seen[k], 0); InterlockedExchange(&klr_pb.put[k], 0); }
    InterlockedExchange(&klr_pb.other, 0); InterlockedExchange(&klr_pb.odd, 0); InterlockedExchange(&klr_pb.lines, 0); InterlockedExchange(&klr_pb.first, 0);
    klr_pb.steptid = 0;
    if (act == 2) {
        if (klh_data((void *)(DWORD_PTR)db, &mine, 4, "database object: the hook's copy of its vtable (online point-blank)")) klog("botfill: online point-blank step x%g bullets on (database object %08lx, copy %08lx; BOT victims only, the host's puppeteer census)", klr_pbo.want, db, mine);
    } else if (klh_data((void *)(DWORD_PTR)db, &mine, 4, "database object: the hook's copy of its vtable (slot 19 wrapped)"))
        klog("balance: point-blank: the database object %08lx now has the hook's copy %08lx of its vtable %08lx (slot 19, the name look-up %08lx, wrapped): a soldier's step at arm's length - his gun's hit x 100, sent while the target is within 160 units - gets, in place of the 100: %s on you, %s on an AI heister, %s on a policeman / another NPC; the game's own vtable comes back when the session is not Arcade or the level is stock",
             db, mine, stock, (DWORD)KLR_DB_FN, klr_pb_text(0, a), klr_pb_text(1, b), klr_pb_text(2, c));
}

/* ---------------------------------------------------------------- ONLINE cop -> bot damage factor */
/* [BotFill] OnlineCopToBot (2026-10-26, BO8c + re\online_bot_damage.md): Arcade multiplies every cop hit on an AI heister by the "police -> crew" float (0x591b60, R+0x00: 0.01 at level 1, 0.05 owner)
   inside 0x61a980 (ZFFActor slot 423, ProjectileHit). Online 0x7f6850 is false for roles 2/3 (and the rules getter 0x508ef0 returns NULL), so a bot takes the full ~65 hp per bullet and a squad kills a
   5600-hp bot in 3.5 s. MECHANISM (data only, SHIP-safe, the same technique as klsync.c's puppet): each listed bot (klbf_pb_is_bot, the puppeteer census) gets a PRIVATE COPY of the ZFFActor vtable
   (the first dword of the actor) whose slot 423 is klr_cb_hit: for a hit whose attacker [hit+0xc] is a ZFFActor of a team other than 2 it writes [hit+0x18] (the scale 0x61acc6 multiplies; 1.00 on ordinary
   hits) x K, calls the game's 0x61a980, writes the scale back. Humans (ZFFPlayer, another vtable), bot-vs-bot and Arcade are never reached; the table is taken off when the round / host state ends.
   klh_actor_priv2 makes klh_avt() and klsync.c see through it. A hit scale > 1 is a point-blank write (OnlinePointBlank already chose it): left alone. The dispatch is virtual ([esi]+0x69c at 0x605103,
   read 2026-10-26). GUESS: explosions / melee reach slot 423 too (if a bot dies with another caller in the bd: ring, extend). GUESS: nothing in the game keeps the hit record past the call. */
#define KLR_CB_HIT    0x0061a980
#define KLR_CB_SLOT   423
#define KLR_CB_NSLOT  512
#define KLR_CB_MAX    16
static struct {
    float k; int pct, ready, told;
    DWORD blk[KLR_CB_NSLOT + 1];              /* [0] RTTI locator, then 512 slots, slot 423 ours; made once */
    DWORD inst[KLR_CB_MAX];                   /* actors that carry the table now */
    volatile LONG hits, scaled, pbleft, other, fail, lost_m, would_m, tot_scaled, tot_lost_m;      /* 5 s window and totals; hp in milli-hp */
    DWORD sum_at;
} klr_cb;
#define klr_cb_vt (klr_cb.blk + 1)
static int klbf_pb_is_bot(DWORD actor);
static DWORD klbf_pb_get(int i);

static float klr_cb_hp(DWORD a) { DWORD h = klh_rd32(a + 0x5fc); float v = -1; if (!h || !klh_rd(h + 4, &v, 4) || v != v) return -1; return v; }
static int klr_cb_count(void) { int i, c = 0; for (i = 0; i < KLR_CB_MAX; i++) c += klr_cb.inst[i] != 0; return c; }

static void __fastcall klr_cb_hit(void *self, void *edx, DWORD hit)      /* thiscall, one stack argument, ret 4 */
{
    void (__fastcall *orig)(void *, void *, DWORD) = (void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLR_CB_HIT);
    DWORD a = (DWORD)(DWORD_PTR)self, att = 0, sc, team = 0; float f = 0, nf, h0, h1;
    (void)edx;
    if (hit && klr_cb.k > 0 && klbf_pb_is_bot(a) && klh_rd(hit + 0xc, &att, 4) && att > 0x10000 && att != a && klh_avt(att) == KLR_ACTOR_VT &&
        (sc = klh_rd32(att + 0x54)) != 0 && klh_rd(sc + 4, &team, 4) && team != 2 && klh_rd(hit + 0x18, &f, 4) && f == f && f > 0) {
        InterlockedIncrement(&klr_cb.hits);
        if (f > 1.0001f && f <= klr_pbo.want + 0.001f) { InterlockedIncrement(&klr_cb.pbleft); orig(self, 0, hit); return; }      /* point-blank: OnlinePointBlank's number stands */
        nf = f * klr_cb.k;      /* a scale above OnlinePointBlank's (stock point-blank 100: its write missed, BO8c HIT #21 dmg 21389) is scaled too, as Arcade's float scales every cop hit */
        if (!klh_data((void *)(DWORD_PTR)(hit + 0x18), &nf, 4, "cop->bot hit scale (OnlineCopToBot)")) { InterlockedIncrement(&klr_cb.fail); orig(self, 0, hit); return; }
        h0 = klr_cb_hp(a);
        orig(self, 0, hit);
        klh_data((void *)(DWORD_PTR)(hit + 0x18), &f, 4, "cop->bot hit scale back (OnlineCopToBot)");
        h1 = klr_cb_hp(a);
        InterlockedIncrement(&klr_cb.scaled); InterlockedIncrement(&klr_cb.tot_scaled);
        if (h0 > h1 && h1 >= 0) {      /* would = lost / K: linear in the scale (a kill clamps at 0, so it under-reads) */
            LONG l = (LONG)((h0 - h1) * 1000.0f);
            InterlockedExchangeAdd(&klr_cb.lost_m, l); InterlockedExchangeAdd(&klr_cb.tot_lost_m, l); InterlockedExchangeAdd(&klr_cb.would_m, (LONG)((double)l / klr_cb.k));
        }
        return;
    }
    if (hit && klbf_pb_is_bot(a)) InterlockedIncrement(&klr_cb.other);      /* a hit on a bot from a human / bot / non-actor: untouched */
    orig(self, 0, hit);
}

/* on = this is the online HOST with bots (klr_online_host) and OnlineCopToBot > 0. Only the game thread writes; on = 0 takes the table off the bots. */
static void klr_cb_tick(int on, int game_thread)
{
    int i, q, n = 0; DWORD stock = KLR_ACTOR_VT, mine = (DWORD)(DWORD_PTR)klr_cb_vt, now = GetTickCount();
    if (!game_thread) return;
    if (!on) {
        for (i = 0; i < KLR_CB_MAX; i++) if (klr_cb.inst[i]) {
            if (klh_rd32(klr_cb.inst[i]) == mine) { klh_data((void *)(DWORD_PTR)klr_cb.inst[i], &stock, 4, "ZFFActor vtable pointer back (OnlineCopToBot)"); n++; }
            klr_cb.inst[i] = 0;
        }
        if (n) klog("botfill: cop->bot factor: %d bot(s) back on the game's own ZFFActor table (round / host state ended); totals: %ld hits scaled, bot hp lost %.0f", n, klr_cb.tot_scaled, klr_cb.tot_lost_m / 1000.0);
        return;
    }
    if (!klr_cb.ready) {
        if (!klh_rd((DWORD_PTR)KLH_VA(KLR_ACTOR_VT) - 4, klr_cb.blk, sizeof klr_cb.blk) || klr_cb_vt[KLR_CB_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(KLR_CB_HIT)) {
            if (!klr_cb.told++) klog("botfill: cop->bot factor: ZFFActor slot %d is %08lx, not %08lx: this build is not the one read - OnlineCopToBot does nothing", KLR_CB_SLOT, (unsigned long)klr_cb_vt[KLR_CB_SLOT], (unsigned long)KLR_CB_HIT);
            return;
        }
        klr_cb_vt[KLR_CB_SLOT] = (DWORD)(DWORD_PTR)klr_cb_hit; klr_cb.ready = 1; klh_actor_priv2 = mine;
        klog("botfill: cop->bot factor ARMED: OnlineCopToBot=%d%% (x%.3f on every ordinary hit of a non-Ally actor on a listed bot: the Arcade police->crew float that online is skipped); private ZFFActor table %08lx, slot %d wrapped; bots only (humans, bot-vs-bot, point-blank untouched)", klr_cb.pct, klr_cb.k, mine, KLR_CB_SLOT);
    }
    for (q = 0; q < 16; q++) {
        DWORD a = klbf_pb_get(q);
        if (!a || klh_rd32(a) != stock) continue;
        for (i = 0; i < KLR_CB_MAX && klr_cb.inst[i]; i++) ;
        if (i == KLR_CB_MAX) break;
        if (klh_data((void *)(DWORD_PTR)a, &mine, 4, "ZFFActor vtable pointer (OnlineCopToBot bot)")) { klr_cb.inst[i] = a; klog("botfill: cop->bot factor: bot actor %08lx now on the private table (x%.3f on cop hits, health %.0f)", a, klr_cb.k, klr_cb_hp(a)); }
    }
    if (now - klr_cb.sum_at >= 5000u) {
        klr_cb.sum_at = now;
        if (klr_cb.hits || klr_cb.other) {
            klog("botfill: cop->bot factor 5 s: %ld cop hits on bots (%ld scaled x%.3f, %ld point-blank left alone, %ld write refused), %ld other hits on bots untouched; bot hp lost %.0f (without the factor ~%.0f); %d bots on the table",
                 klr_cb.hits, klr_cb.scaled, klr_cb.k, klr_cb.pbleft, klr_cb.fail, klr_cb.other, klr_cb.lost_m / 1000.0, klr_cb.would_m / 1000.0, klr_cb_count());
            InterlockedExchange(&klr_cb.hits, 0); InterlockedExchange(&klr_cb.scaled, 0); InterlockedExchange(&klr_cb.pbleft, 0); InterlockedExchange(&klr_cb.other, 0);
            InterlockedExchange(&klr_cb.fail, 0); InterlockedExchange(&klr_cb.lost_m, 0); InterlockedExchange(&klr_cb.would_m, 0);
        }
    }
}

/* ---------------------------------------------------------------- the crew-hit log (section 2 a9) */

static struct {
    int on;                                   /* [Balance] LogCrewHits=1 */
    int big;                                  /* [Balance] LogCrewHitsBig=N (default 0 = off): a drop of N or more is listed past both rate limits */
    DWORD rules;                             /* the round being watched (0 = none) */
    DWORD sec0; int secn;                     /* the one-second window of the rate limit and the lines written in it */
    LONG drops, listed, skipped, deaths;      /* this round */
    float lost[KLB_NREC];                     /* health lost by record, this round */
    struct { DWORD actor; float hp, hmax; BYTE dead; DWORD ltick; float ldelta, ldist; int lmate; char lwho[640]; } r[KLB_NREC];   /* lwho: the last drop's 'who could have' text, for the DIED line */
    /* the soldiers of ONE pass, built only when a drop was seen in it (klr_ch_sold); nsol < 0 = not built yet this pass */
    int nsol;
    struct { DWORD actor, tgt; DWORD team; int rec; BYTE traitor; float pos[3]; } sol[KLR_CH_SOLMAX];
} klr_ch;

/* the sum line, when the round ends or the session is left (said only when the log was armed in a round) */
static void klr_ch_sum(const char *why)
{
    char by[300]; int i, n = 0;
    if (!klr_ch.rules) return;
    by[0] = 0;
    for (i = 0; i < KLB_NREC && n < 270; i++)
        if (klr_ch.lost[i] > 0.0f) n += snprintf(by + n, sizeof by - n, "%s record %d %.0f", n ? "," : "", i, klr_ch.lost[i]);
    klog("balance: crew hits: %s: %ld drop(s) of an AI heister's health seen, %ld listed, %ld not listed (rate limit), %ld death(s); lost by record:%s",
         why, klr_ch.drops, klr_ch.listed, klr_ch.skipped, klr_ch.deaths, by[0] ? by : " none");
    klr_ch.rules = 0;
}

static float klr_ch_dist(const float a[3], const float b[3])
{
    return sqrtf((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
}

/* append to a text, never past its end (_vsnprintf does not terminate a cut text) */
static void klr_ch_cat(char *o, int sz, const char *fmt, ...)
{
    int n = (int)strlen(o); va_list a;
    if (n >= sz - 1) return;
    va_start(a, fmt); _vsnprintf(o + n, (size_t)(sz - n - 1), fmt, a); va_end(a);
    o[sz - 1] = 0;
}

/* The living soldiers of the scene, once per pass that saw a drop (2 a9b). The entity-table walk of klcensus.c /
   klcensor.c (64 slots a read, the object at slot+0x60, vtable ZFFActor), then the soldier [actor+0x77c] (vtable
   0xbd0954, [soldier+0x40] == the actor), alive = health [h+4] > 0. His target: [soldier+0xac] counts only while the
   'has a target' dword [soldier+0xb0] is not 0 (kl2 0x8c62ec / 0x8c630c: the fire task returns at once without it, and
   klbotdown.c NoFire clears +0xb0 but leaves +0xac stale). The human is a ZFFPlayer, NOT a soldier: never listed. */
static void klr_ch_sold(const struct klb_snap *sn)
{
    DWORD p, tab, i, blk[64 * 32]; int j;
    klr_ch.nsol = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x10000 && klr_ch.nsol < KLR_CH_SOLMAX; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && klr_ch.nsol < KLR_CH_SOLMAX; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], s, h, info, team = 0xff; float hp = 0;
            if (o < 0x10000 || klh_avt(o) != KLR_ACTOR_VT) continue;
            if (!(s = klh_rd32(o + 0x77c)) || klh_rd32(s) != KLR_SOLDIER_VT || klh_rd32(s + 0x40) != o) continue;
            if (!(h = klh_rd32(o + 0x5fc)) || !klh_rd(h + 4, &hp, 4) || !klr_finite(hp) || hp <= 0.0f) continue;      /* living only */
            if (!(info = klh_rd32(o + 0x54)) || !klh_rd(info + 4, &team, 4)) continue;
            if (!kle_node(klh_rd32(o + 4), klr_ch.sol[klr_ch.nsol].pos, 0)) continue;
            klr_ch.sol[klr_ch.nsol].actor = o; klr_ch.sol[klr_ch.nsol].team = team;
            klr_ch.sol[klr_ch.nsol].tgt = klh_rd32(s + 0xb0) ? klh_rd32(s + 0xac) : 0;
            klr_ch.sol[klr_ch.nsol].rec = -1; klr_ch.sol[klr_ch.nsol].traitor = 0;
            for (j = 0; j < sn->n && j < KLB_NREC; j++)
                if (sn->r[j].used && sn->r[j].actor == o) { klr_ch.sol[klr_ch.nsol].rec = j; klr_ch.sol[klr_ch.nsol].traitor = (sn->r[j].flags & 2) != 0; }
            klr_ch.nsol++;
        }
    }
}

/* "crew record 3", "crew record 3 TRAITOR", "Enemy" ... (team enum: Mercenary 0, Enemy 1, Ally 2, Enemy2 4: re/balance.md) */
static const char *klr_ch_tm(int k, char t[40])
{
    DWORD team = klr_ch.sol[k].team;
    if (klr_ch.sol[k].rec >= 0) {      /* any soldier with a crew record, whatever his team now (a TraitorFoe traitor is team 1 in play) */
        if (team == 2) snprintf(t, 40, "crew record %d%s", klr_ch.sol[k].rec, klr_ch.sol[k].traitor ? " TRAITOR" : "");
        else snprintf(t, 40, "crew %d%s t%lu", klr_ch.sol[k].rec, klr_ch.sol[k].traitor ? " TRAITOR" : "", (unsigned long)team);
    }
    else if (team == 2) strcpy(t, "Ally, no crew record");
    else if (team == 1) strcpy(t, "Enemy (police/guard)");
    else if (team == 4) strcpy(t, "Enemy2");
    else if (team == 0) strcpy(t, "Mercenary");
    else snprintf(t, 40, "team %lu", (unsigned long)team);
    return t;
}

/* The 'who could have done it' text of one drop of the victim actor at pos (d lost of hmax); the soldier list is built. */
static void klr_ch_who(char *out, int sz, DWORD victim, const float pos[3], float d, float hmax, int fatal)
{
    int top[KLR_CH_AIMERS], nt = 0, na = 0, k, m, nn = -1, nal = -1, crew; float topd[KLR_CH_AIMERS], q, dn = 0, dal = 0; char t[40];
    out[0] = 0;
    for (k = 0; k < klr_ch.nsol; k++) {
        if (klr_ch.sol[k].actor == victim) continue;
        q = klr_ch_dist(pos, klr_ch.sol[k].pos);
        crew = klr_ch.sol[k].team == 2 || klr_ch.sol[k].rec >= 0;      /* a TraitorFoe traitor (team 1 in play) is still crew */
        if (!crew && (nn < 0 || q < dn)) { nn = k; dn = q; }
        if (klr_ch.sol[k].tgt != victim) continue;
        na++;
        if (crew && (nal < 0 || q < dal)) { nal = k; dal = q; }
        if (nt == KLR_CH_AIMERS && q >= topd[KLR_CH_AIMERS - 1]) continue;      /* the nearest few are named */
        for (m = nt < KLR_CH_AIMERS ? nt : KLR_CH_AIMERS - 1; m > 0 && topd[m - 1] > q; m--) { top[m] = top[m - 1]; topd[m] = topd[m - 1]; }
        top[m] = k; topd[m] = q; if (nt < KLR_CH_AIMERS) nt++;
    }
    /* the friendly-fire clause goes FIRST so a cut of the text never loses it */
    if (nal >= 0) klr_ch_cat(out, sz, "friendly-fire candidate (nearest crew with him as fire-task target): %s %.1f m; ", klr_ch_tm(nal, t), dal / 100.0f);
    else klr_ch_cat(out, sz, "no crew has him as fire-task target; ");
    if (!na) klr_ch_cat(out, sz, "no soldier has him as target (fire-task field +0xac, a GUESS that it is the gun target)");
    else {
        klr_ch_cat(out, sz, "%d soldier(s) have him as target:", na);
        for (m = 0; m < nt; m++) klr_ch_cat(out, sz, " [%s %.1f m]", klr_ch_tm(top[m], t), topd[m] / 100.0f);
        if (na > nt) klr_ch_cat(out, sz, " +%d more", na - nt);
    }
    if (nn >= 0) klr_ch_cat(out, sz, "; nearest living non-crew: %s %.1f m, aims at %s", klr_ch_tm(nn, t), dn / 100.0f,
                            klr_ch.sol[nn].tgt == victim ? "him" : klr_ch.sol[nn].tgt ? "someone else" : "nobody");
    else klr_ch_cat(out, sz, "; no living non-Ally soldier in the scene");
    if (!na && fatal) klr_ch_cat(out, sz, " -- fatal hit with no target left at the sample (the killer may have just dropped him as target; blast / fall / YOUR shots also fit)");
    else if (!na && d > KLR_CH_BIG * hmax) klr_ch_cat(out, sz, " -- NO TARGETER and a big loss (%.0f%% of his maximum in one pass): blast / fall / script? (or YOUR shots: the human is not scanned)", 100.0f * d / hmax);
}

/* the death line: the last drop seen (this pass's own when the killing blow fell in it) */
static void klr_ch_died(int i, const struct klb_rec *r, DWORD tick, float hp, float hmax)
{
    klr_ch.r[i].dead = 1; InterlockedIncrement(&klr_ch.deaths);
    if (!klr_ch.r[i].ltick) {
        klog("balance: crew hit: record %d (actor %08lx) DIED at tick %lu, health %.1f of %.1f; no drop of his health was seen before", i, (unsigned long)r->actor, (unsigned long)tick, hp, hmax);
        return;
    }
    klog("balance: crew hit: record %d (actor %08lx) DIED at tick %lu, health %.1f of %.1f; his last drop was %.1f, %.2f s before, you %.0f units away then, nearest other heister record %d; who could have done it then: %s",
         i, (unsigned long)r->actor, (unsigned long)tick, hp, hmax, klr_ch.r[i].ldelta, (float)(long)(tick - klr_ch.r[i].ltick) / 1024.0f, klr_ch.r[i].ldist, klr_ch.r[i].lmate, klr_ch.r[i].lwho);
}

/* One pass of the log, on the game's thread (the caller's 50 ms). Reads only: nothing is written, nothing is called, no
   code and no vtable is touched, so the hit cannot change. The damage routine itself is NOT wrapped (2 a9). A drop of
   an AI heister's current health between two passes is a hit; two hits within one pass are one line. */
static void klr_ch_tick(int arcade, int game_thread)
{
    struct klb_snap sn; DWORD clock, tick = 0, now = GetTickCount(); int i; char why[200];
    if (!klr_ch.on || !game_thread) return;
    if (!arcade || !klb_read(&sn) || sn.state != KLR_CH_ROUND) {      /* the lobby or the session is gone: the round's sums go out */
        klr_ch_sum("the round is over (or left)");
        memset(klr_ch.r, 0, sizeof klr_ch.r);
        return;
    }
    if (!(clock = klh_rd32((DWORD_PTR)KLH_VA(KLR_CH_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    if (sn.rules != klr_ch.rules) {               /* a new round: forget everything of the last */
        klr_ch_sum("a new round starts");
        klb_level(why);                           /* only for the text of this line: stock or not, the log runs (it writes nothing to the game) */
        klr_ch.rules = sn.rules; klr_ch.drops = klr_ch.listed = klr_ch.skipped = klr_ch.deaths = 0;
        memset(klr_ch.lost, 0, sizeof klr_ch.lost); memset(klr_ch.r, 0, sizeof klr_ch.r);
        klog("balance: crew hits: a round runs (%s; the log runs on stock levels too): every drop of an AI heister's health is listed, at most %d lines a second and %d a round; each line says who COULD have done it (the soldiers whose target is the victim, the nearest non-Ally, the nearest Ally aiming at him), not who did", why, KLR_CH_PERSEC, KLR_CH_ROUND_MAX);
    }
    klr_ch.nsol = -1;                             /* the soldier list of this pass: built at the first drop that needs it */
    for (i = 0; i < sn.n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &sn.r[i];
        DWORD h, s; float hp = 0, hmax = 0, pos[3] = { 0, 0, 0 }, hpos[3], p2[3], d, q, dh = -1.0f, dm = -1.0f; int have, j, mate = -1, list, fatal; BYTE dn = 0;
        if (!r->used || !(r->flags & 1) || !r->actor || klh_avt(r->actor) != KLR_ACTOR_VT || !(s =klh_rd32(r->actor + 0x77c)) || klh_rd32(s) != KLR_SOLDIER_VT) { klr_ch.r[i].actor = 0; continue; }
        if (!(h = klh_rd32(r->actor + 0x5fc)) || klh_rd32(h + 0x24) != r->actor) continue;
        if (!klh_rd(h + 4, &hp, 4) || !klh_rd(h + 8, &hmax, 4) || !klr_finite(hp) || !klr_finite(hmax) || hmax < 1.0f || hmax > 100000.0f) continue;
        if (klr_ch.r[i].actor != r->actor) {      /* a new man in this record (or the first pass): the baseline, no line */
            memset(&klr_ch.r[i], 0, sizeof klr_ch.r[i]);
            klr_ch.r[i].actor = r->actor; klr_ch.r[i].hp = hp; klr_ch.r[i].hmax = hmax;
            continue;
        }
        if (r->status != 7) klr_ch.r[i].dead = 0;      /* a record that lives again (the same address reused) may die again */
        if (hmax != klr_ch.r[i].hmax || (r->status != 0 && r->status != 7)) { klr_ch.r[i].hp = hp; klr_ch.r[i].hmax = hmax; continue; }      /* not in play; or the maximum moved (Tough / FedHealth write it with the health): not a hit */
        if (hp >= klr_ch.r[i].hp - 0.001f) {      /* the same, or healed / regenerated */
            klr_ch.r[i].hp = hp;
            if (r->status == 7 && !klr_ch.r[i].dead) klr_ch_died(i, r, tick, hp, hmax);
            continue;
        }
        d = klr_ch.r[i].hp - hp;
        fatal = !klr_ch.r[i].dead && (hp <= 0.0f || r->status == 7);      /* the hit that takes him down, not a later one on a dead record */
        InterlockedIncrement(&klr_ch.drops); klr_ch.lost[i] += d;
        /* who stands near: you, and the nearest other heister (friendly fire?) - a distance, not an attacker (a policeman is NOT scanned: the log cannot tell friendly fire from police, only where the crew stood) */
        have = kle_node(klh_rd32(r->actor + 4), pos, 0);
        if (have && sn.human >= 0 && sn.r[sn.human].actor && kle_node(klh_rd32(sn.r[sn.human].actor + 4), hpos, 0)) dh = klr_ch_dist(pos, hpos);
        for (j = 0; have && j < sn.n && j < KLB_NREC; j++) {
            if (j == i || !sn.r[j].used || sn.r[j].status != 0 || !sn.r[j].actor || !kle_node(klh_rd32(sn.r[j].actor + 4), p2, 0)) continue;
            q = klr_ch_dist(pos, p2);
            if (dm < 0 || q < dm) { dm = q; mate = j; }
        }
        klr_ch.r[i].ltick = tick; klr_ch.r[i].ldelta = d; klr_ch.r[i].ldist = dh; klr_ch.r[i].lmate = mate;
        if (now - klr_ch.sec0 >= 1000u) { klr_ch.sec0 = now; klr_ch.secn = 0; }
        list = !(klr_ch.secn >= KLR_CH_PERSEC || klr_ch.listed >= KLR_CH_ROUND_MAX);
        if (!list && klr_ch.big > 0 && d >= (float)klr_ch.big) list = 2;      /* LogCrewHitsBig: a big drop is never lost to the limits (L93: rec 1's 340 one-shot fell after the round's 400) */
        /* who could have done it (2 a9b): the soldier list is built ONCE this pass, and only for a line that is written or a death (a rate-limited drop costs nothing) */
        if (!have) strcpy(klr_ch.r[i].lwho, "his place is unknown, so nobody was looked for");
        else if (list || fatal) {
            if (klr_ch.nsol < 0) klr_ch_sold(&sn);
            klr_ch_who(klr_ch.r[i].lwho, sizeof klr_ch.r[i].lwho, r->actor, pos, d, hmax, fatal);
        } else strcpy(klr_ch.r[i].lwho, "not looked for (rate limit)");
        if (!list) InterlockedIncrement(&klr_ch.skipped);
        else {
            klr_ch.secn++; InterlockedIncrement(&klr_ch.listed);
            klh_rd(r->actor + 0x64c, &dn, 1);
            klog("balance: crew hit%s: record %d (actor %08lx, stage %u%s) health %.1f -> %.1f (-%.1f of %.1f) at (%.0f, %.0f, %.0f), tick %lu; you %.0f units away, nearest other heister record %d at %.0f; %s%s; who could have: %s",
                 list == 2 ? " (BIG, past the rate limit)" : "", i, (unsigned long)r->actor, (unsigned)r->stage, (r->flags & 2) ? ", TRAITOR" : "", klr_ch.r[i].hp, hp, d, hmax, have ? pos[0] : 0, have ? pos[1] : 0, have ? pos[2] : 0, (unsigned long)tick,
                 dh, mate, dm, dn ? "he is down" : "on his feet", fatal ? ", THIS HIT KILLED HIM" : "", klr_ch.r[i].lwho);
        }
        klr_ch.r[i].hp = hp;
        if (r->status == 7 && !klr_ch.r[i].dead) klr_ch_died(i, r, tick, hp, hmax);
    }
}

/* 2 = this is the HOST (role 2) of an online FA round (game type 4, state 0x13..0x1f) and klbotfill.c's census has seen bots in the last 5 s and OnlinePointBlank > 0; else 0 */
static int klr_online_host(void)
{
    DWORD sm, role = 0, st = 0;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLR_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x54, &role, 4) || role != 2 || !klh_rd(sm + 0x70, &st, 4) || st < 0x13 || st > 0x1f) return 0;
    return klbf_pb_any() ? 2 : 0;
}
static int klr_pbo_host(void) { return klr_pbo.want > 0 ? klr_online_host() : 0; }

static void klr_tick(int game_thread)
{
    static DWORD last, toldrules; static char toldwhy[200];
    DWORD now = GetTickCount(), rules, state; int arcade, act = 0, level; char why[200];
    if ((!klr.on && !(klr_pbo.want > 0) && !(klr_cb.k > 0)) || !klh_exe_ok || now - last < (game_thread ? 50u : 100u)) return;
    last = now;
    if (!klr.on) { klr_pb_tick(klr_pbo_host(), game_thread); klr_cb_tick(klr_cb.k > 0 && klr_online_host(), game_thread); return; }      /* [Balance] off: only the online point-blank part runs */
    arcade = klr_arcade(&rules, &state, &level);
    if (arcade && (klr.any || klr_pb.any)) {
        act = klb_level(why);                 /* asked every pass: the verdict changes when the archive is opened */
        if (rules != toldrules || strcmp(why, toldwhy)) {
            toldrules = rules; strcpy(toldwhy, why);
            if (act && !klr.any) klog("balance: %s: the point-blank keys act on this round (Arcade level %d; no Risk, no factor, no health key is set); the Steam guard blocks every write of it", why, level);
            else if (act) klog("balance: %s: Risk=%d acts on this round (Arcade level %d); the Steam guard blocks every write of it", why, klr.risk, level);
            else klog("balance: %s: nothing is written here (the dial acts only on a level that is not stock); the log runs", why);
        }
    }
    klr_table_tick(arcade, act, level);
    klr_tough_tick(act);                      /* Tough (2 a7): 'NPC health x' of the four difficulty rows; back when the dial stops acting */
    klr_head_tick(act);                       /* HeadShot / FedHeadShot (2 a8): the two head floats; the tuning's own back otherwise */
    if (arcade && act) klr_tough_say(now);    /* the proof line: what the game made the AI heisters' health */
    klr_pb_tick(act ? 1 : klr_pbo_host(), game_thread);      /* the point-blank keys: in while the dial acts (1) or the online host has bots (2), the game's own vtable back otherwise */
    klr_cb_tick(klr_cb.k > 0 && klr_online_host(), game_thread);      /* OnlineCopToBot: the bots' private table in while this is the online host with bots, the game's own back otherwise */
    klr_ch_tick(arcade, game_thread);        /* LogCrewHits: reads only; any Arcade round, stock level or not */
    if (arcade) klr_player_tick(act, game_thread, rules);
    else if (klr_p.have) klr_player_tick(0, game_thread, 0);      /* the session ended with the object alive: its own values go back */
}

static float klr_inif(const char *key, const char *def)
{
    char t[32];
    GetPrivateProfileStringA("Balance", key, def, t, sizeof t, klh_ini);
    return (float)atof(t);
}

/* -> 1 and *d when the text is ONE number and nothing else; blanks or a ';' comment may follow. strtod alone takes the
   leading number of any text: '0,75' would be 0 (review N1). */
static int klr_number(const char *t, double *d)
{
    char *e;
    *d = strtod(t, &e);
    if (e == t || *d != *d) return 0;
    while (*e == ' ' || *e == '\t') e++;
    return *e == 0 || *e == ';';
}

static void klr_init(void)
{
    int k, offbad = 0, pbsaid = 0, fedbad = 0, farbad = 0, tofedbad = 0, toughbad = 0, headbad = 0; float v; char t[32], p[32], a[24], b[24], c[24], fedt[32], fart[32], cft[32]; double d; int cfbad = 0;
    char tofedt[32], tought[32], headt[2][32];
    {   /* [BotFill] OnlinePointBlank: bullets per cop step on a bot (default 2 = GUESS: ~200-260 of 5600 hp with OnlineHealthMul 20; 0 = off), read even with [Balance] off */
        char q[32]; double e = 2.0;
        GetPrivateProfileStringA("BotFill", "OnlinePointBlank", "2", q, sizeof q, klh_ini);
        if (!klr_number(q, &e) || e < 0 || e > 100) { klog("botfill: OnlinePointBlank=%s is IGNORED: it must be one number of 0 .. 100 (bullets per cop point-blank step on a bot; 0 = off); 2 stands", q); e = 2.0; }
        klr_pbo.want = (float)e;
        klog("botfill: OnlinePointBlank=%g (recommended on: 2; 0 = off); acts only on the host of an online FA round with OnlineHost=1 and OnlineTactics=1 (the puppeteer bot list)", e);
    }
    {   /* [BotFill] OnlineCopToBot: percent of a cop's ordinary hit that a bot takes online (default 5 = the owner's CopToCrew 0.05 = Arcade level 2; stock Arcade level 1 = 1; 0 = off), read even with [Balance] off */
        int pc = (int)GetPrivateProfileIntA("BotFill", "OnlineCopToBot", 5, klh_ini);
        if (pc < 0 || pc > 100) { klog("botfill: OnlineCopToBot=%d is IGNORED: it must be 0 .. 100 (percent; 0 = off); 5 stands", pc); pc = 5; }
        klr_cb.pct = pc; klr_cb.k = pc / 100.0f;
        klog("botfill: OnlineCopToBot=%d (recommended on: 5; 1 = stock Arcade level 1; 0 = off); acts only on the host of an online FA round with OnlineHost=1 and OnlineTactics=1 (the puppeteer bot list); with it on, OnlineHealthMul can come down (5 with 5%% = stock-Arcade survival)", pc);
    }
    klr.on = GetPrivateProfileIntA("Balance", "Enable", 0, klh_ini) != 0;
    if (!klr.on) return;
    klr.log = (int)GetPrivateProfileIntA("Balance", "Log", 1, klh_ini); if (klr.log < 0) klr.log = 0; if (klr.log > 2) klr.log = 2;
    klr.risk = (int)GetPrivateProfileIntA("Balance", "Risk", 0, klh_ini); if (klr.risk < 0) klr.risk = 0; if (klr.risk > 3) klr.risk = 3;
    klr.ramp = GetPrivateProfileIntA("Balance", "Ramp", 1, klh_ini) != 0;
    klr.mirror = GetPrivateProfileIntA("Balance", "FedMirror", 1, klh_ini) != 0;
    for (k = 0; k < KLR_NF; k++) {
        klr.f[k] = klr_dial[klr.risk].f[k];
        v = klr_inif(klr_key[k], "-1"); if (klr_finite(v) && v >= 0 && v <= 20) klr.f[k] = v;
        if (klr.f[k] >= 0) klr.any = 1;
    }
    /* the seventh: no key = the dial's; a negative number = leave the game's own, also under a Risk; a text that is
       not one number and nothing else, or a number over 20, is ignored and said so below (the six take such a text
       as its leading number, '0,05' as 0: not copied, and not changed for them) */
    klr.off = klr_dial[klr.risk].off;
    GetPrivateProfileStringA("Balance", "CrewOffStage", "", t, sizeof t, klh_ini);
    if (t[0]) {
        if (!klr_number(t, &d) || d > 20) offbad = 1;
        else klr.off = d < 0 ? -1.0f : d > 0 ? (float)d : 0.0f;      /* '-0' is 0, not -0.0 */
    }
    if (klr.off >= 0) klr.any = 1;
    /* FedToCrew (2 a5): no key = YouToCrew's number also for a police player. One number of 0 .. 20 and nothing else. It
       is written only while the pairs stand exchanged (FedMirror=1 and the local player is police); alone it writes
       nothing for a criminal player, so it does not set klr.any unless FedMirror is on. */
    klr.fed = -1.0f; fedt[0] = 0;
    GetPrivateProfileStringA("Balance", "FedToCrew", "", fedt, sizeof fedt, klh_ini);
    if (fedt[0]) {
        if (!klr_number(fedt, &d) || d < 0 || d > 20) fedbad = 1;
        else { klr.fed = d > 0 ? (float)d : 0.0f; if (klr.mirror) klr.any = 1; }
    }
    /* YouToCrewFar (2 a6): one number of 0.05 .. 1 and nothing else; 1 or no key = off. NearAt / FarAt in metres. */
    klr_far.far_ = 0; klr_far.near_at = 800; klr_far.far_at = 3500; klr_far.hold = 4000; fart[0] = 0;
    GetPrivateProfileStringA("Balance", "YouToCrewFar", "", fart, sizeof fart, klh_ini);
    if (fart[0]) {
        double na = 8, fa = 35, hs = 4; char u[32];
        if (!klr_number(fart, &d) || d < 0.05 || d > 1) farbad = 1;
        else if (d < 1) {
            klr_far.far_ = (float)d; klr.any = 1;
            GetPrivateProfileStringA("Balance", "YouToCrewNearAt", "8", u, sizeof u, klh_ini); if (!klr_number(u, &na) || na < 0 || na > 500) { na = 8; farbad = 2; }
            GetPrivateProfileStringA("Balance", "YouToCrewFarAt", "35", u, sizeof u, klh_ini); if (!klr_number(u, &fa) || fa < 1 || fa > 1000) { fa = 35; farbad = 2; }
            GetPrivateProfileStringA("Balance", "YouToCrewHold", "4", u, sizeof u, klh_ini); if (!klr_number(u, &hs) || hs < 0.2 || hs > 60) { hs = 4; farbad = 2; }
            if (fa < na + 1) { na = 8; fa = 35; farbad = 2; }
            klr_far.near_at = (float)(na * 100); klr_far.far_at = (float)(fa * 100); klr_far.hold = (DWORD)(hs * 1000);
        }
    }
    /* CopToYouFar (balance2): one number of 0.2 .. 1 and nothing else; 1 or no key = off (the old behaviour). NearAt / FarAt in metres. */
    memset(&klr_cf, 0, sizeof klr_cf); klr_cf.near_at = 1200; klr_cf.far_at = 4000; cft[0] = 0;
    GetPrivateProfileStringA("Balance", "CopToYouFar", "", cft, sizeof cft, klh_ini);
    if (cft[0]) {
        double na = 12, fa = 40; char u[32];
        if (!klr_number(cft, &d) || d < 0.2 || d > 1) cfbad = 1;
        else if (d < 1) {
            klr_cf.far_ = (float)d; klr.any = 1;
            GetPrivateProfileStringA("Balance", "CopToYouNearAt", "12", u, sizeof u, klh_ini); if (!klr_number(u, &na) || na < 0 || na > 500) { na = 12; cfbad = 2; }
            GetPrivateProfileStringA("Balance", "CopToYouFarAt", "40", u, sizeof u, klh_ini); if (!klr_number(u, &fa) || fa < 1 || fa > 1000) { fa = 40; cfbad = 2; }
            if (fa < na + 1) { na = 12; fa = 40; cfbad = 2; }
            klr_cf.near_at = (float)(na * 100); klr_cf.far_at = (float)(fa * 100);
        }
    }
    /* CrewToFed (2 a8): as FedToCrew - one number of 0 .. 20, written only while the pairs stand exchanged */
    klr.tofed = -1.0f; tofedt[0] = 0;
    GetPrivateProfileStringA("Balance", "CrewToFed", "", tofedt, sizeof tofedt, klh_ini);
    if (tofedt[0]) {
        if (!klr_number(tofedt, &d) || d < 0 || d > 20) tofedbad = 1;
        else { klr.tofed = d > 0 ? (float)d : 0.0f; if (klr.mirror) klr.any = 1; }
    }
    /* Tough (2 a7): one number of 0.25 .. 10; 1 or no key = off. No Risk sets one. */
    klr.tough = 0; tought[0] = 0;
    GetPrivateProfileStringA("Balance", "Tough", "", tought, sizeof tought, klh_ini);
    if (tought[0]) {
        if (!klr_number(tought, &d) || d < 0.25 || d > 10) toughbad = 1;
        else if (d != 1.0) { klr.tough = (float)d; klr.any = 1; }
    }
    /* HeadShot / FedHeadShot (2 a8): one number of 1 .. 10 (under 1 a head would cost less than a body: refused); no
       key = the game's own for that side */
    klr.head = klr.fedhead = -1.0f; headt[0][0] = headt[1][0] = 0;
    for (k = 0; k < 2; k++) {
        GetPrivateProfileStringA("Balance", k ? "FedHeadShot" : "HeadShot", "", headt[k], sizeof headt[k], klh_ini);
        if (!headt[k][0]) continue;
        if (!klr_number(headt[k], &d) || d < 1 || d > 10) headbad |= 1 << k;
        else { if (k) klr.fedhead = (float)d; else klr.head = (float)d; klr.any = 1; }
    }
    klr.health = klr_dial[klr.risk].health; v = klr_inif("PlayerHealth", "0"); if (klr_finite(v) && v >= 0.05f && v <= 10) klr.health = v;
    klr.delay = klr_dial[klr.risk].delay; v = klr_inif("RegenDelay", "0"); if (klr_finite(v) && v >= 0.1f && v <= 600) klr.delay = v;
    klr.full = klr_dial[klr.risk].full; v = klr_inif("RegenTime", "0"); if (klr_finite(v) && v >= 0.1f && v <= 600) klr.full = v;
    if (klr.health == 1.0f) klr.health = 0;                   /* times one = leave */
    if (klr.health > 0 || klr.delay > 0 || klr.full > 0) klr.any = 1;
    klog("balance: on; Log=%d Risk=%d Ramp=%d FedMirror=%d; factors (-1 = stock) police->crew %.2f crew->police %.2f police->you %.2f you->police %.2f crew->you %.2f you->crew %.2f, crew off your stage x %.2f; your health x %.2f (0 = stock), comes back after %.1f s within %.1f s (0 = stock); Arcade only, written only on a level that is not stock",
         klr.log, klr.risk, klr.ramp, klr.mirror, klr.f[0], klr.f[1], klr.f[2], klr.f[3], klr.f[4], klr.f[5], klr.off, klr.health, klr.delay, klr.full);
    if (fedbad) klog("balance: FedToCrew=%s is IGNORED: it must be one number of 0 .. 20 with a decimal point; a police player's bullet on a heister stays YouToCrew's number", fedt);
    else if (klr.fed >= 0)                    /* said only when the key is set: a hook without it starts with the lines it had */
        klog("balance: FedToCrew=%.2f: while YOU are police (and FedMirror=1) your bullet costs an AI heister x %.2f instead of YouToCrew's %.2f%s", klr.fed, klr.fed, klr.f[5],
             klr.mirror ? "" : " - FedMirror=0: the key does NOTHING (the game's own swap stands)");
    /* track X2's keys: each line only when its key is set - a hook without them starts with the lines it had */
    if (tofedbad) klog("balance: CrewToFed=%s is IGNORED: it must be one number of 0 .. 20 with a decimal point; a heister's bullet on a police player stays CrewToYou's number", tofedt);
    else if (klr.tofed >= 0)
        klog("balance: CrewToFed=%.2f: while YOU are police (and FedMirror=1) an AI heister's bullet costs you x %.2f instead of CrewToYou's %.2f%s", klr.tofed, klr.tofed, klr.f[4],
             klr.mirror ? "" : " - FedMirror=0: the key does NOTHING (the game's own swap stands)");
    if (toughbad) klog("balance: Tough=%s is IGNORED: it must be one number of 0.25 .. 10 with a decimal point (1 = nothing)", tought);
    else if (klr.tough > 0)
        klog("balance: Tough=%.2f: every maximum health of an Arcade round on a level that is not stock x %.2f - every NPC through the campaign difficulty rows' 'NPC health x' (police, guards, AI heisters, civilians), you (hero or fed) through your health object, on top of PlayerHealth; no damage factor is changed, so every fight takes %.2f times the hits; not the escape vehicle, not what a point-blank step or the departure kill deals",
             klr.tough, klr.tough, klr.tough);
    if (klr.tough > 0 && !klr.mirror)
        klog("balance: Tough with FedMirror=0: a POLICE player's health object is left alone by this part, so as a fed you alone have NO Tough (every NPC still has it)");
    for (k = 0; k < 2; k++) {
        if (headbad & (1 << k)) klog("balance: %s=%s is IGNORED: it must be one number of 1 .. 10 with a decimal point (the game's is 10)", k ? "FedHeadShot" : "HeadShot", headt[k]);
        else if ((k ? klr.fedhead : klr.head) >= 0)
            klog("balance: %s=%.1f: while you are %s your bullet on an NPC's head counts x %.1f instead of the game's 10 (an NPC's bullet never gets a head factor); the game's own while you are %s%s", k ? "FedHeadShot" : "HeadShot",
                 k ? klr.fedhead : klr.head, k ? "police" : "a heister", k ? klr.fedhead : klr.head, k ? "a heister" : "police", (k ? klr.head : klr.fedhead) >= 0 ? " (that side has its own key)" : "");
    }
    if (farbad == 1) klog("balance: YouToCrewFar=%s is IGNORED: it must be one number of 0.05 .. 1 with a decimal point (what YouToCrew is multiplied with far away; 1 = off)", fart);
    else if (klr_far.far_ > 0)                /* said only when the key is set */
        klog("balance: YouToCrewFar=%.2f: your bullet on an AI heister costs him YouToCrew x 1 within %.0f m, x %.2f from %.0f m on, linear between - priced for the heister your last hit was on (for %.1f s), else the nearest that has turned, else the farthest in play; one float for all of them, re-written every pass (an approximation: re\\bots_fight.md 1); not for a police player, not while you are the traitor%s",
             klr_far.far_, klr_far.near_at / 100, klr_far.far_, klr_far.far_at / 100, klr_far.hold / 1000.0, farbad ? " - a NearAt / FarAt / Hold value was not one number in its range (FarAt at least 1 m over NearAt): 8 / 35 / 4 stand for what was wrong" : "");
    if (cfbad == 1) klog("balance: CopToYouFar=%s is IGNORED: it must be one number of 0.2 .. 1 (text or a comma decimal reads as 0 and is refused; what a policeman's bullet on you is multiplied with far away; 1 = off)", cft);
    else if (klr_cf.far_ > 0)
        klog("balance: CopToYouFar=%.2f: a policeman's bullet on you costs police->you x 1 within %.0f m, x %.2f from %.0f m on, linear between - priced for the man who fired the last bullet that hit you ([player+0x2778], a GUESS: the first bullet of a new shooter may use the last one's range); one float for all police, re-written every pass; not for a police player, not while you are the traitor%s",
             klr_cf.far_, klr_cf.near_at / 100, klr_cf.far_, klr_cf.far_at / 100, cfbad ? " - a NearAt / FarAt value was not one number in its range (FarAt at least 1 m over NearAt): 12 / 40 stand for what was wrong" : "");
    if (offbad)                               /* said at any Log level: the user asked for something and does not get it */
        klog("balance: CrewOffStage=%s is IGNORED: it must be one number of 0 .. 20 with a decimal point (0.75, not 0,75), or a negative one for the game's own; what stands is the dial's %.2f (-1 = the game's own)", t, klr.off);
    /* the point-blank keys (section 2 a4): no key or a negative number = that victim is left alone. As the seventh's:
       one number and nothing else, here 0 .. 100 (100 = the game's own: the steps are then only seen and logged).
       They do not set klr.any: with them alone the table and the health object are not touched. Without a key no
       line is written and klr_pb_tick returns at once: the hook is then what it was. */
    for (k = 0; k < KLR_PB_NWHO; k++) {
        klr_pb.want[k] = -1.0f;
        GetPrivateProfileStringA("Balance", klr_pb_key[k], "", p, sizeof p, klh_ini);
        if (!p[0]) continue;
        pbsaid = 1;
        if (!klr_number(p, &d) || d > 100)
            klog("balance: %s=%s is IGNORED: it must be one number of 0 .. 100 with a decimal point (how many ordinary bullets of his gun one point-blank step is worth; 100 = the game's own), or a negative one to leave that victim alone", klr_pb_key[k], p);
        else if (d >= 0) { klr_pb.want[k] = d > 0 ? (float)d : 0.0f; klr_pb.any = 1; }      /* '-0' is 0 */
    }
    klr_ch.on = GetPrivateProfileIntA("Balance", "LogCrewHits", 0, klh_ini) != 0;      /* no key: no line, no pass (the hook is what it was) */
    klr_ch.big = (int)GetPrivateProfileIntA("Balance", "LogCrewHitsBig", 0, klh_ini); if (klr_ch.big < 0 || klr_ch.big > 100000) klr_ch.big = 0;
    if (klr_ch.on && klr_ch.big) klog("balance: LogCrewHitsBig=%d: a drop of that much or more in one 50 ms pass is listed past the %d-a-second and %d-a-round limits (tagged BIG)", klr_ch.big, KLR_CH_PERSEC, KLR_CH_ROUND_MAX);
    if (klr_ch.on) klog("balance: LogCrewHits=1: every drop of an AI heister's health in an Arcade round is logged (a sample of his health object every 50 ms, reads only; at most %d lines a second, %d a round, then a sum): who could have shot (the soldiers aiming at him, read from their target field), not who did - the damage routine is not wrapped", KLR_CH_PERSEC, KLR_CH_ROUND_MAX);
    if (kld_pb_key()) klr_pb.any = 1;         /* kldown.c: [Down] DownPointBlank needs the wrapper although no PointBlank key is set */
    if (pbsaid)
        klog("balance: point-blank keys (in place of the game's 100 in the hit a soldier sends at every burst step while his target is within 160 units): %s on you, %s on an AI heister, %s on a policeman / another NPC%s",
             klr_pb_text(0, a), klr_pb_text(1, b), klr_pb_text(2, c), klr_pb.any ? "; Arcade only, only on a level that is not stock" : ": no key acts, nothing of it is put into the game");
}

#endif /* KLBALANCE_C */
