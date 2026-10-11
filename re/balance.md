# What a bullet costs whom in an Arcade round: measured, and one dial to make it even

Agent p-balance, 2026-10-10. OFFLINE: nothing launched, nothing installed, nothing written into the Dog Days
folder, no level built. Files: `klhook/klbalance.c` (new; NOT wired, see 7), `tools/kl_map_ai.py` (new command
`balance`), this note, `re/map_ai.md` 13. NOTHING HERE HAS RUN IN THE GAME.

**Since then** (2026-10-11, track E): the file is wired and the dial HAS run in the owner's game since 2026-10-10
(`KLHook.log` 18:38: 'the damage table ... is what the game's code builds', 'campaign difficulty option 1',
'Risk=2 written for 11 Arcade levels (39 value(s) changed', 'your health set: maximum 401.5 (the game gave
550.0)' - sections 1 d, 2 and check B0 / B1 hold). **Section 10 is new: the seventh factor R+0x1c and its key
`CrewOffStage`** (built, NOT run). Where sections 5 and 9 say '+0x1c is not touched', section 10 replaces them.
Section 10 was reviewed the same day (`re/balance_offstage_review.md`: ACCEPT WITH FIXES) and finished after it:
10.6 says how the bots really go down (the first version had it wrong), 10.9's run that is to SHOW the effect is
replaced (O3a / O3b / O4), the key's text is read strictly, and the two hooks were built again (10.8, 10.11).

The owner, after four Dead Men maps with AI heisters: "they dont have much health when i shoot them but when
they shoot me i have a llot of health not proportional and the coppers dont seem too intimidating it should be
all the same kinda risk and how the traitors could be".

## 0. Short answers

1. **It is not the Dead Men maps and not their soldier rows. It is the stock game's Arcade level 1.** Dog Days
   multiplies every hit in an Arcade round by one of six numbers chosen by WHO shoots WHOM, from a table with
   one row per Arcade level (section 2). On level 1: a policeman's bullet costs the player **a tenth**, the
   player's bullet costs a policeman **double**, a policeman's bullet costs an AI heister **a hundredth**, an AI
   heister's costs a policeman **three times**. The rows meet at level 5 (all about 1.0) and are reversed by
   level 11 (police 3.0 on you, you 0.3 on them).
2. **The Arcade level is 1 + the rounds of this session you ESCAPED from** (`inc byte [score+0x45]` at 0x74bcf0,
   only when crew record 0 has status 6; set to 1 with three lives at 0x56955a). Every test round so far was
   level 1, a few level 2 - on maps where the van is the problem, nobody got further.
3. **In hits** (`python tools\kl_map_ai.py balance <build>`, body shots at 10 m, median of the level's police;
   section 4): on Late Night Opening today a policeman needs **91** hits to kill you (and your health comes back
   after 4 s) while you need **2** for him; police need **417** hits for an AI heister, a heister needs **2** for a
   policeman. Stock Subway on level 1: the same 91 / 2 / 417 / 2. So stock Arcade IS meant to start like this;
   what stock adds is three times the police, in waves (re/map_ai.md 2).
4. **Decision: the hook, not the level.** The six numbers and the player's health are run-time data of two heap
   objects; no level file holds them. `klbalance.c` writes them: `[Balance] Risk=0..3`, default OFF. Risk=2 is
   the owner's rule (every factor 1.0, your health 550 -> 400, health comes back as slowly as a SWAT man's).
   **No level data changes, so nothing was rebuilt** and bots / guns need not be re-applied.
5. **One level-side thing the dial exposes** (section 6): M01 / M02 / M03's guards never miss (accuracy 100,
   stock 55) and an NPC's PISTOL is the hardest-hitting gun of the game per bullet (162..295 at 10 m against a
   rifle's 47..80). With police->you at 1.0 that is 2..3 hits to kill from a man who does not miss. Not changed
   here - it needs a played round (check B6) before anyone lowers what the owner called 'not too intimidating'.

## 1. How a hit is priced (kl2.exe build 0490; EXE = read in the disassembly, 2026-10-10)

**a. The gun** - `ZFFItemTemplateWeapon` slot 0x2f0 = **0x46ef60**(weapon, distance), read to its `ret`:

    damage = lerp of the AMMO template's four damages   object +0x84 +0x88 +0x8c +0x90   (ZFFItemTemplateAmmo fields 17..20)
             over the gun's four ranges                 object +0xd4 +0xd8 +0xdc +0xe0   (weapon fields 21..24)
           * gun +0xe4                                   field 25 (1.0; the sniper rifle 2.5)
           * gun +0x13c  if the shooter is a ZActor      field 37: pistols 1.5 (MP45 1.7), rifles 0.6..1.0, SMG 0.8..1.0,
                                                         shotgun pellet 0.35..0.4     (not for the campaign's buddy)
             gun +0x140  if he is not, in mode 4         field 38: 1.0 on every gun
           * gun +0x144 / +0x144 / +0x148 / +0x14c / +0x150 by range band, in mode 4     fields 39 39 40 41 42

  A property record's offset + 4 = the object offset (proved on the three bools at records 0xec..0xee, read by
  getters at +0xf0..+0xf2). The owner test is `[weapon+0x5c]` against the type id of **ZActor** (0x150cce0; its
  getter 0x7abda0 is ZActor's vtable slot 12). Mode 4 = `[session+0x5c] == 4` = Arcade. Field 26 (30..120),
  which looks like 'damage', is NOT the damage: slot 0x2f4 (0x405d10) uses it for a second number, times tuning
  +0x28, that goes to the hit reaction. ASSUMPTION: the hit's distance and the ranges are the same unit (the
  ranges are 3..100, so metres; 0x4db847 compares the same distance with 300.0, which would be 300 m - the
  template may be scaled at load; not read). `kl_map_ai.bullet()` is this function.

**b. The body part** - **0x572f60**(bone type), ten floats at 0xcdefe4..0xcdf008 (.data):

| bone type (byte +0x3f of the 0x40-byte bone record) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| factor | 1 | 1 | **10** | **10** | 0.5 | 1 | 0.2 | 0.5 | 1 | 0.2 |

  An NPC victim takes it whole (0x61acb8). **The player as victim takes min(m, 4), softened to 1 + (m - 1) / 4**
  (0x4db7ff..0x4db83d): a head shot costs him 1.75 times, the 0.5 parts 0.875. And when the SHOOTER is a ZActor,
  bone types 2 / 3 are turned into 1 first (0x61ac87, 0x4db7e7): an NPC never gets a head shot on anybody.

**c. Who shoots whom** - Arcade only (`0x7f6850`), record R = `[0x168d7c0] + 0x6ac + L * 0x70`, L = byte
`[[rules+0x5f8]+0x45]` clamped to 1..11 by every reader. With the local player not a policeman
(`[player+0x2723] == 0`; for a policeman the two team cases swap):

| float | used by | when |
|---|---|---|
| R+0x00 | 0x591b60 (from the NPC's hit routine 0x61ad18) | an NPC that is not team Ally hits an NPC: **police -> AI heister** |
| R+0x04 | 0x591b60 | an Ally NPC hits an NPC: **AI heister -> police** |
| R+0x08 | 0x8b8050 (from the player's 0x4db9d1, 0x743455) | an NPC that is not Ally hits the player: **police -> you** |
| R+0x0c | 0x7c1ba0 (0x61ae18) | the player hits an NPC that is not Ally: **you -> police** |
| R+0x10 | 0x8b8050 | an Ally NPC hits the player: **heister / traitor -> you** |
| R+0x14 | 0x7c1ba0 | the player hits an Ally NPC: **you -> heister / traitor** |
| R+0x18 | 0x6a1c40 | damage you may do to a bot before it turns on you (klbot.c's Retaliate) |
| R+0x1c | 0x591be0..0x591c24 (the only reader: section 10) | **times this, on top of R+0x04**, when the SHOOTER is an Ally NPC (an AI heister) whose heist stage (record +0x78) is not the player's: 0.5 .. 0.1. Corrected 2026-10-11: this row had shooter and victim swapped; the routine's argument is the one whose team picks R+0x00 / R+0x04 above, and it is that actor's crew record (0x78f470) whose stage is compared with the local player's (0x6c7700). So a crew that is inside while you are outside hits police at half strength on Arcade levels 1-3. Key `CrewOffStage`, section 10 |

  Team = `[[actor+0x54]+4]`, enum TEAM: Mercenary 0, Enemy 1, **Ally 2**, Enemy2 4. A traitor bot stays team Ally,
  so R+0x10 / R+0x14 are also 'a traitor on you' and 'you on a traitor'.
  Beside it, per soldier: `[soldier+0x704]`, 1.0 from the constructor (0x761b1e), set by a script controller
  (0x7e25c0) and for the campaign's buddy (0x4bcc95) - not used by any Fragile Alliance level as far as read.
  The player's own extras: x 2.0 while `[[player+0x26f4]] != 0` (0x9018e0), x 1.3 with `[player+0x2f3c]`
  (0x61adb2); on the receiving side x 0.2 with `[player+0x2f3c]`, x 1.3 in movement state 0x12 (tuning +0x1fc),
  x 10 with `[player+0xd5c]`. What those states are was not read.

**d. Health**
- The player: `[player+0xa48]` = a 0x28-byte object (constructor 0x4aad80): +0x04 health, +0x08 maximum, +0x14
  seconds after the last hit before it comes back, +0x18 seconds in which ALL of it comes back (0x419570:
  `health += dt * maximum / [+0x18]`), +0x24 the owner. Filled from the tuning object's player block P
  (0x4206f0): **Arcade P = tuning+0x604, online +0x5c4, story +0x5e4**; `[P+0x10]` health, `[P+0x08]` /
  `[P+0x0c]` the two times. In mode 4 the spawn routine 0x410781 gives `[P+0x10]` + armour 0 / 20 / 40 / 60
  (0xbd22c8) and 0x644310 does NOT apply the difficulty factor. Code values: **Arcade 550, 4 s, 4 s**; online
  550, 5 s, 3 s; story 100 (times 11 / 5 / 2.25 / 0.85 by difficulty), 5 s, 2 s.
- An NPC: `[actor+0x5fc]`, the same class. 0x8fbac0: ZSoldier field 7 (it IS hit points: the range 0..100 at
  field 7 per cent, tuning +0x364 / +0x368) times a factor of the difficulty row (0x831f00), times field
  9..12. **Arcade takes the STORY rows** (0x863a60 'online' is false in Arcade): **0.5 / 0.9 / 1.15 / 1.3** for
  the difficulty option `[0x156b5f0]` = 0..3 (9 / 6 / 3 / 1.5 only for the campaign's buddy,
  `[gamedata+0x4cf0]`). ZSoldier **field 8 is regeneration**: both times = 15 s .. 1 s at field 8 per cent
  (tuning +0x3c8..+0x3d4); -1 = none. Stock SWAT and the AI heisters have 50 = 8 s / 8 s; street cops 0 = 15 s.
- ASSUMPTION: `[0x156b5f0]` in Arcade is what the profile last played the campaign on. Its only writer is the
  option handler (0x472d50, option 'Difficulty'); the Arcade menu has no such option (frontend.xml), the
  session copies the global in and out (0x4b5fdd, 0x4920a0). klbalance.c logs it.

## 2. The numbers of the tuning object (constructor 0x524050, emulated)

The object `[0x168d7c0]` (0xc38 bytes, made at 0x929d80) is filled by 0x524050: 786 blocks of 'allocate a
12-byte descriptor, store the address of the variable, store the default in both'. The names are empty strings
in retail, so nothing can be set by name; the values below are the defaults read out of that code (a sweep that
splits at each call of 0x89e850 and takes the `lea reg, [edi + off]` and the value stored at `[eax+8]`: 599
floats, 136 ints, 51 bools, 0 blocks left unread). Whether anything overwrites them later was NOT established -
klbalance.c's first log lines print what the running game has and say whether it matches.

| Arcade level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| +0x00 police -> crew | 0.01 | 0.05 | 0.1 | 0.15 | 0.2 | 0.25 | 0.3 | 0.35 | 0.4 | 0.45 | 0.5 |
| +0x04 crew -> police | 3.0 | 2.6 | 2.2 | 1.9 | 1.6 | 1.3 | 1.0 | 0.8 | 0.4 | 0.2 | 0.1 |
| +0x08 police -> you | 0.1 | 0.2 | 0.4 | 0.8 | 1.0 | 1.3 | 1.6 | 1.9 | 2.2 | 2.6 | 3.0 |
| +0x0c you -> police | 2.0 | 1.75 | 1.5 | 1.25 | 1.0 | 0.9 | 0.8 | 0.7 | 0.6 | 0.5 | 0.3 |
| +0x10 crew -> you | 0.1 | 0.2 | 0.4 | 0.8 | 1.0 | 1.1 | 1.2 | 1.3 | 1.4 | 1.5 | 1.7 |
| +0x14 you -> crew | 0.25 | 0.5 | 1.0 | 0.9 | 0.8 | 0.7 | 0.6 | 0.5 | 0.4 | 0.3 | 0.1 |
| +0x18 retaliation | 100 | 90 | 80 | 70 | 60 | 40 | 25 | 25 | 25 | 25 | 25 |
| +0x1c other stage | 0.5 | 0.5 | 0.5 | 0.4 | 0.3 | 0.3 | 0.2 | 0.2 | 0.2 | 0.1 | 0.1 |

Difficulty rows (nine floats each; story 0..3 at +0x42c / +0x450 / +0x474 / +0x498, co-op at +0x4bc.., online
+0x54c / +0x570): `[0]` buddy health 9 / 6 / 3 / 1.5, `[1]` player health 11 / 5 / 2.25 / 0.85 (not in mode 4),
`[2]` NPC health 0.5 / 0.9 / 1.15 / 1.3, `[3]` spread of a team-Enemy shooter 1.0 (0x4cc04c), `[7]` 1.2 / 1.4 /
1.6 / 1.7 (a hit reaction, 0x6e3a8c).

## 3. Guns, as the levels have them (the same 61 templates in every Fragile Alliance level)

One bullet at 10 m in Arcade, before 1 b / 1 c, from an NPC / from the player:

| | NPC | player | | NPC | player |
|---|---:|---:|---|---:|---:|
| HG_SW_MP45 | 295 | 173 | Rifle_AK74 | 60 | 76 |
| HG_SigSauer226 | 233 | 155 | Rifle_FN_SCAR | 52 | 86 |
| HG_M9Beretta | 162 | 108 | Rifle_Type81 | 80 | 80 |
| HG_M-77B | 125 | 84 | Rifle_zastavam85 (the crew's) | 47 | 58 |
| SMG_Type05 | 68 | 80 | SMG_Type79 / SMG_HK_sp89 / SMG_MPi69 / SMG_MAC_10 | 53 / 50 / 42 / 36 | 53 / 63 / 53 / 45 |

Pistols are the heavy hitters per bullet by design (field 37 = 1.5 and the multiplayer band factor 2.2..2.5
against a rifle's 0.8 and 0.9); a rifle makes it up in rate of fire (650 a minute against 300..390).

## 4. Hits to kill, before and after

`python tools\kl_map_ai.py balance <build folder | stock level> [--dist=10] [--diff=1]`: body shots, no
regeneration counted, NPC health x 0.9 (difficulty option 1 - ASSUMED, see 1 d), the player with the crew's
Zastava (58.5 a bullet), median of the level's armed police (lowest - highest), shotguns left out (a shell is
several pellets; their number was not read).

| Late Night Opening (`u_maps\M02`: 11 counted, health 100..175, 7 heisters of 280) | your health | police kill you | you kill a policeman | police kill a heister | a heister kills police | a heister / traitor kills you | you kill a heister |
|---|---:|---|---|---|---|---:|---:|
| **today = stock, Arcade level 1** | 550 | **91** (34-131) | **2** (1-2) | **417** (156-597) | **2** (1-2) | 118 | 18 |
| stock, level 3 | 550 | 23 (9-33) | 2 | 42 (16-60) | 2 (1-2) | 30 | 5 |
| stock, level 5 | 550 | 10 (4-14) | 3 (2-3) | 21 (8-30) | 3 (2-3) | 12 | 6 |
| stock, level 8 | 550 | 5 (2-7) | 4 (3-4) | 12 (5-18) | 5 (3-5) | 10 | 9 |
| stock, level 11 | 550 | 4 (2-5) | 9 (6-9) | 9 (4-12) | 34 (20-34) | 7 | 44 |
| Risk=1, level 1 | 550 | 19 (7-27) | 2 | 9 (4-12) | 3 (2-3) | 24 | 5 |
| **Risk=2, level 1** | 402 | **7** (3-10) | **3** (2-3) | **5** (2-6) | **4** (2-4) | 9 | 5 |
| Risk=2, level 11 (Ramp) | 402 | 3 (1-4) | 9 (6-9) | 5 (2-6) | 34 (20-34) | 6 | 5 |
| Risk=3, level 1 | 280 | 5 (2-7) | 3 (2-3) | 5 (2-6) | 4 (2-4) | 6 | 5 |

Level 1 today / Risk=2 level 1, the same four columns, the other levels:

| | police kill you | you kill a policeman | police kill a heister | a heister kills police |
|---|---|---|---|---|
| M01 diner (11 counted) | 82 (19-107) / 6 (2-8) | 1 (1-2) / 2 (2-3) | 373 (86-487) / 4 (1-5) | 1 (1-2) / 3 (2-4) |
| M03 bank (14) | 91 (19-107) / 7 (2-8) | 2 (1-2) / 3 (2-3) | 417 (86-487) / 5 (1-5) | 2 (1-2) / 4 (2-4) |
| M06 park (13) | 105 (70-154) / 8 (6-12) | 1 (1-2) / 2 (2-3) | 480 (317-704) / 5 (4-8) | 1 (1-2) / 3 (3-4) |
| Retomoto (`v_rtbots\retomoto_bots`, 82) | 82 (19-154) / 6 (2-12) | 2 (1-3) / 3 (2-5) | 373 (86-704) / 4 (1-8) | 2 (1-2) / 4 (2-6) |
| stock F01 Subway (28) | 91 (44-105) / 7 (4-8) | 2 (1-2) / 3 (1-3) | 417 (201-480) / 5 (3-5) | 2 (1-2) / 4 (2-4) |
| stock F07 (33) | 91 (19-117) / 7 (2-9) | 2 (1-2) / 3 (1-3) | 417 (86-534) / 5 (1-6) | 2 (1-2) / 4 (1-4) |

Read with it: the player's 550 comes back whole within 8 s of the last hit (4 + 4) - at 6 damage a hit he is
never in danger; a head shot from the player kills any of these men (x 10), a head shot ON the player is never
given (1 b). Under Risk=2 a heister's 280 x 0.9 = 252 against a policeman's 90..158 and the player's 402.

## 5. The dial (`klhook/klbalance.c`, section [Balance] of KLHook.ini)

| | CopToCrew | CrewToCop | CopToYou | YouToCop | CrewToYou | YouToCrew | PlayerHealth | RegenDelay / RegenTime |
|---|---:|---:|---:|---:|---:|---:|---|---|
| table float | R+0x00 | R+0x04 | R+0x08 | R+0x0c | R+0x10 | R+0x14 | `[H+0x08]` | `[H+0x14]` / `[H+0x18]` |
| Risk=0 | stock | | | | | | stock | stock |
| Risk=1 'less lopsided' | 0.5 | 1.5 | 0.5 | 1.5 | 0.5 | 1.0 | x 1.0 (550) | stock (4 s / 4 s) |
| **Risk=2 'the same risk'** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | x 0.73 (400) | 8 s / 8 s |
| Risk=3 'no favours' | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | x 0.51 (280) | 8 s / 8 s |

- Why these: 1.0 everywhere IS 'the same gun at the same range costs everybody the same' - player, police,
  heisters and traitors alike. 8 s / 8 s is the regeneration of a stock SWAT man and of an AI heister. 280 is
  an AI heister's health; 400 is a GUESS between that and stock's 550 for one human against a dozen guns.
  Risk=1's numbers are GUESSES (halfway from level 1 to level 5, roughly stock's level 3-4).
- **Ramp=1** (default): where stock's own row is HARDER than the dial it stays - CopToCrew, CopToYou,
  CrewToYou = max(dial, stock), CrewToCop, YouToCop = min(dial, stock). A late Arcade level is never easier
  than stock. Ramp=0 = the dial's numbers on every level. YouToCrew is always the dial's.
- Every number has its own key and beats the dial: `CopToYou=0.6` with `Risk=2`, `PlayerHealth=0.6`, ...
- What is written, when: section 2 of the file's head. The six floats of all eleven records, on any thread
  (as klbot.c's Tune), only while an Arcade session runs on a level that is NOT stock (`klb_level` = the Steam
  write guard's verdict 2), and put back otherwise. The player's health object, from the game's own thread
  only, as a factor of the maximum the game gave (so armour and a new round are scaled again), never for a
  player who is a policeman, and put back when the hook stops acting.
- Not touched: R+0x18 (klbot.c's Retaliate); NPC health; the difficulty option; any code. R+0x1c is the seventh
  factor since 2026-10-11: key `CrewOffStage`, Risk=1 -> 0.75, Risk=2 / 3 -> 1.0, its own Ramp rule - section 10.
- With klfed.c: as a fed you are a policeman - your health is left alone, and the game swaps the team cases
  (1 c). Under Risk=2 / 3 all six are 1.0, so nothing changes; under Risk=1 a fed would shoot heisters at
  CopTo..'s 0.5 and be shot at 1.5. Use Risk=2 with the fed part.

    [Balance]
    Enable=0
    ; 0 = no log, 1 = once per round object: the stock table, the player blocks, your health object, what was
    ; written; 2 = also a line for every loss of health ('you lost 6.1')
    ;Log=1
    ; 0 = stock (level 1: a policeman's bullet costs you a tenth, yours costs him double), 1 = less lopsided,
    ; 2 = the same for everybody + your health 550 -> 400, 3 = the same + your health 280 (an AI heister's)
    ;Risk=2
    ; 1 = a later Arcade level is never easier than stock, 0 = the dial's numbers on every level
    ;Ramp=1
    ; single numbers, each beats the dial: damage factors ...
    ;CopToYou=1.0
    ;YouToCop=1.0
    ;CopToCrew=1.0
    ;CrewToCop=1.0
    ;CrewToYou=1.0
    ;YouToCrew=1.0
    ; ... and what is LEFT of an AI heister's hits on police while he is at another heist stage than you
    ; (section 10; -1 = the game's own, also under a Risk; the full comment is in klhook\KLHook.ini)
    ;CrewOffStage=1.0
    ; ... your health as a factor of what the game gives (550 + armour), and how it comes back (seconds)
    ;PlayerHealth=0.73
    ;RegenDelay=8
    ;RegenTime=8

## 6. What stays on the level side (not built)

| | today | stock | with Risk=2 |
|---|---|---|---|
| accuracy as used, M01 / M02 / M03 | 100 (they never miss: miss share = 1 - accuracy / 100) | 55 (SWAT, cops, guards) | every shot of a pistol guard costs 125..295 of your 402 |
| accuracy, M06 | 66..99 | | |
| accuracy, Retomoto | 55 (82 on five riflemen) | | as stock's level 5 |
| police health | 100..175 (`kl_map_ai` floors) | 65..175 | 2..3 Zastava hits each |
| heister health | 280, regeneration 8 s / 8 s (stock's row) | 280 | 5 police hits |

If B6 says the three accuracy-100 maps are too deadly at Risk=2, the level-side answer is to give the PISTOL
carriers stock's guard row (`eGuard eRegular` = accuracy 55) and leave the riflemen - `kl_map_ai.STRENGTH`'s
pistol floor is `eRegular` already; what is missing is a CAP, about ten lines in `strength()`. Until then the
hook-side answer is `CopToYou=0.6` beside `Risk=2` on those three maps. Not done now: nobody has seen Risk=2.

Nothing was built, so the four blocks are what `u_maps` has (before = after):

| | .prm | .ANM | .fxc | F01_Main.WAV | (.TEX) | archive sha1 |
|---|---:|---:|---:|---:|---:|---|
| M01 | 55,917,968 | 22,061,764 | 17,760,648 | 21,722,704 | 242,724,752 | 4ea0322d |
| M02 | 55,449,184 | 22,202,472 | 17,760,648 | 22,527,568 | 224,349,952 | 0ef2e7e2 |
| M03 | 61,299,008 | 22,202,616 | 17,760,648 | 22,716,752 | 225,939,136 | 284b1f8a |
| M06 | 50,415,712 | 21,642,576 | 17,760,648 | 21,775,744 | 212,826,208 | d3a2e83a |

## 7. Tests run, and the wiring

    python tools\kl_map_ai.py balance F01 F07 <work>\build\u_maps\M01 .. M06 <work>\build\v_rtbots\retomoto_bots     section 4
    python tools\kl_maps.py audit <work>\build\u_maps\M02      RESULT: PASS (0 must-be-0, 6 known) - the tool chain after the edit
    scratch copy of klhook with the three lines below: build.bat -> dinput8.dll (SHIP), build_auto.bat -> (TEST),
        both without a warning at /W3
    klbalance_test.c (scratch, off-game: a made-up session / rules / tuning / player in the test's own memory,
        the hook's helpers stubbed): RESULT: PASS for Risk=2 and Risk=1 - nothing written on a stock level; the
        table written (39 values, Ramp: level 11 keeps 3.0 / 0.3 / 1.7 / 0.1) while +0x18 / +0x1c stay (the file
        of 2026-10-10; since 2026-10-11 +0x1c is the seventh factor and is written too: section 10.7); the
        health object only from the game's thread (550 -> 401.5, 4 / 4 -> 8 / 8), scaled again after a new
        maximum (610 -> 445.3) and after a new round; a policeman put back; everything back when the session is
        not Arcade; nothing written into a table that fails the shape check.
    kl_fa_bots.py check / kl_map_guns.py check / kl_impact.py: not run - no level was built or changed.

The three lines for `klhook.c` (the file uses `klb_level` of klbot.c, so it goes after it):

    #include "klbalance.c"            after   #include "klbot.c"
    klr_tick(game_thread);            in klh_tick, after   klb_tick(game_thread);
    klr_init();                       in the init list, after   klb_init();

and the `[Balance]` block of section 5 into `klhook\KLHook.ini`. Prefix `klr_` (free in the hook today).

## 8. Live checks, in order (one variable a run; the lead runs them)

| run | ini | do | proves |
|---|---|---|---|
| B0 | `[Balance] Enable=1`, `Log=2`, no Risk; any map, also stock Subway (nothing is written) | start an Arcade round, let ONE policeman shoot you, shoot a guard in the body | the log: 'the damage table ... is what the game's code builds' + eleven stock lines = section 2; 'player blocks ... Arcade 550 4.0 4.0' and 'your health object: 550.0 of 550.0 ... 4.0 s ... 4.0 s' = 1 d; 'campaign difficulty option N' = which health factor; 'you lost 6.x' per AK-74 hit = 60 x 0.1 (1 a x 1 c). If the table DIFFERS or the health is not 550, section 4 is recomputed from the logged numbers before anything is switched on |
| B1 | + `Risk=2`, `u_maps\M02` | the same round | 'Risk=2 acts on this round', 'written for 11 Arcade levels (39 value(s) changed', 'your health set: maximum 401.5 (the game gave 550.0)'; 'you lost' is now about 60 for an AK-74 body hit; a guard takes 3 Zastava body hits instead of 2. SEEN 2026-10-10. With the hook of section 10 the count is **45** (39 + 6 of the seventh factor; **35** with the owner's `CopToCrew=0.05`), and 39 / 29 again with `CrewOffStage=-1` |
| B2 | the same | quit to the menu, start stock Subway | 'the stock damage table is back (39 value(s))' (45 / 35 with the hook of section 10: as many as were written), 'your health put back' (if the object lived), then 'nothing is written here' on Subway |
| B3 | + `[Bots] Enable=1 Log=1` | a round with the AI heisters | bots reach status dead in the crew log (417 hits made that impossible before); do they still get to the van |
| B4 | the same | escape, play the next round (Arcade level 2) | the health line again with 'the game gave 550.0'; Ramp: level 2's police->you stays 1.0 |
| B5 | the same | buy armour between rounds | 'the game gave 570 / 590 / 610' and the scaled maximum |
| B6 | `Risk=2` | one round each on M01, M03, Retomoto | the FEEL: are the never-missing pistol guards of M01 / M03 too much (section 6) against Retomoto's stock accuracy |
| B7 | + klfed.c's keys | die, come back as a fed | 'a POLICEMAN: left alone'; the fed's health is the game's |

## 9. Not known

Whether anything overwrites the tuning defaults after 0x524050 (B0 answers); the campaign difficulty option in
the owner's profile (B0); the unit of the hit distance against the gun's ranges; how many pellets a shell has;
the AI's burst lengths (so hits a second, not hits to kill, could not be computed); what `[player+0x26f4]`,
`[player+0x2f3c]`, `[player+0xd5c]` and movement state 0x12 are; whether a smaller health maximum upsets the
HUD or what 0x6e36ac starts when health is under 0.9 x maximum (0x46f210, not read); who else reads R+0x00..+0x14
(the twenty places that form the record's address were listed, the six floats were found in three readers).
SETTLED 2026-10-11 (section 10.2): the record address is formed in SEVEN functions, and every field has one
reader - +0x00 / +0x04 / +0x1c in 0x591b60, +0x08 / +0x10 in 0x8b8050, +0x0c / +0x14 in 0x7c1ba0, +0x18 in
0x6a1c40, +0x20 in 0x46d4d0, +0x24..+0x68 in 0x79b7c0, +0x6c in 0x43ffb0. The campaign difficulty option is 1 in
the owner's profile (his log), so section 4's 'NPC health x 0.9' is his.

## 10. The seventh factor: an AI heister at another heist stage than you (R+0x1c), key `CrewOffStage`

Track E, 2026-10-11. OFFLINE: nothing launched, nothing installed, nothing written into the Dog Days folder (its
`kl2.exe`, `KLHook.log` and dumps were READ). Files: `klhook/klbalance.c`, the `[Balance]` block of
`klhook/KLHook.ini` (the sample had none until now), this section. **BUILT, NOT RUN IN THE GAME.**

### 10.0 Short answers

1. **What it is.** When an AI heister (an NPC of team Ally) hits any NPC and his heist stage is not the human's,
   the game multiplies the hit once more, by the float at R+0x1c: **0.5 on Arcade levels 1-3, down to 0.1 on
   10-11**. It sits on top of `CrewToCop`. Nothing else in the exe reads the float (10.2).
2. **What the dial did without it.** `Risk=2` wrote CrewToCop 1.0 and left this at 0.5: a heister who was not at
   your stage hit police at 0.5 - a third of stock's own 3.0 x 0.5 = 1.5 on level 1.
3. **What was built.** Key `CrewOffStage`; Risk=1 -> 0.75 (a GUESS), Risk=2 / 3 -> 1.0, Risk=0 -> not written;
   `CrewOffStage=-1` keeps the game's own under any Risk. Ramp=1 holds the PRODUCT CrewToCop x CrewOffStage at
   most at stock's (10.4). Same care as the six: stock kept, checked against the exe's row (and REFUSED if it is
   not that row), written only in Arcade on a level that is not stock, put back otherwise, in the same log lines.
4. **How much it matters - known for the exposure, NOT known for the outcome.** In the owner's own played
   sessions (2026-10-10, before `[Bots] BoardAll` existed) the AI heisters were at another stage than him for
   **11 %** of their time in play; in the scripted test runs, where the 'player' stands still at stage 0, for
   **75 %** (10.6). So this factor halved the crew's fire in most of every scripted run - those runs showed a crew
   at about 0.63 of its strength. It does not change what a heister TAKES at all.
   How the bots go DOWN is logged for scripted runs only (10.6a): **35 of 41 by sustained ordinary fire, 26 of the
   27 that carry the stage at stage 1 with the human at 0** - under this very factor; 6 by one step over 100. So
   in those runs how fast the crew kills is part of whether it lives, and the factor is in that chain. Whether a
   factor of two is ENOUGH to change the end there is not known, and one run in the log argues for caution: with
   crew->police at 3.0 (1.5 off stage, three times every other run) all seven bots of the Retomoto room still
   went down. For the owner's PLAYED rounds nothing is logged about how his crew dies (`[Bots] Log=1` has no
   'lost' lines). Hence the live plan of 10.9: first a near-binary pair (20 against 0.01), then 1.0 against -1.

### 10.1 The reading (kl2.exe build 0490, every line below read 2026-10-11)

The caller is **0x61a980 = `ZFFActor` vtable slot 423** (0xbb4248): `this` (esi) is the NPC that is HIT, the
argument (ebx) the hit record.

    0x61aa0b  attacker = [hit+0xc]; kept at [esp+0x18] when it is a ZFFPlayer (class id [0x1548c7c]),
              at [esp+0x14] when it is a ZFFActor ([0x1547b24])
    0x61aac1  victim Ally / Mercenary AND the attacker an Ally / Mercenary NPC: the hit is DROPPED unless Arcade,
              [victim+0x774] != 0 and the local player's traitor byte [player+0x2726] != 0     (..0x61ab17)
    0x61ac98  damage = gun (slot 0x2f0) x body part (0x572f60) x [hit+0x18]
    0x61accd  attacker a ZFFActor with a soldier [attacker+0x77c]:  x [soldier+0x704]
    0x61acf1  Arcade (0x7f6850) and a rules object (0x508ef0):
    0x61ad14  push esi (the victim) / push ebx (THE ATTACKER) / ecx = rules / call 0x591b60 / fmul

**0x591b60**(rules; attacker, victim), `ret 8`, whole. The second argument is never read. One caller, no pointer
to the routine anywhere in the image.

    0x591b65  bl = byte [[rules+0x5f8]+0x45]                       the Arcade level
    0x591b76  player = 0x660b00(gamedata, 0)                       the local player; none -> return 1.0
    0x591b89  bl clamped to 1..11;  ebp = R = [0x168d7c0] + 0x6ac + bl * 0x70
    0x591b9f  al = byte [player+0x2723]                            the local player is police
    0x591bbc  al == 0:  attacker's team [[attacker+0x54]+4] == 2 (Ally) -> fld [R+4]   else fld [R+0]
              al != 0:  Ally -> fld [R+0]   else fld [R+4]         (the two cases swap for a police player)
    0x591be0  al != 0 -> return.    attacker not Ally -> return.
    0x591bec  i = 0x78f470(rules, attacker)      the crew record in use with [rec+4] == attacker and mask 1; none: 0xff
    0x591c00  bl = byte [[rules+0x348] + (char)i * 0x7c + 0x78]    the ATTACKER's heist stage
    0x591c06  j = 0x6c7700(player)               0 in Arcade (0x7f6850), else from [player+0x2748]
    0x591c17  cmp byte [[rules+0x348] + (char)j * 0x7c + 0x78], bl / je return
    0x591c1d  fld [R+0x1c] / fmul / fstp                           the only use of the float

**So the factor is applied exactly when** the session is Arcade, there is a local player and he is not police,
the attacker is an NPC of team Ally (with a soldier), the victim is an NPC that takes the hit at all - police,
guards, civilians; a fellow heister only in the traitor case of 0x61aac1 - and the stage byte of the attacker's
crew record differs from that of crew record 0. Then: hit x CrewToCop x [R+0x1c].

- **Not** for what a heister TAKES (a shooter that is not Ally returns before the test), **not** for the player's
  hits (0x7c1ba0) or the hits on him (0x8b8050: neither has a stage term), **not** in the traitor rule (0x79b7c0
  reads +0x24..+0x68).
- **A dead human**: the compare takes crew record 0's byte, which only the round reset (0x817d20) clears and only
  the trigger boxes raise (0x5dd890). A human who dies at stage 1 leaves the crew 'off stage' as soon as it moves
  on, for the rest of the round. READ, not seen (it assumes the dead human stays the local player object; with no
  local player the routine returns 1.0 - no factor at all, not even +0x00 / +0x04).
- **A police player** (klfed.c, `[player+0x2723]`): the stage term is never applied. But the base case swaps: an
  AI heister then shoots with R+0x00, the 'police -> crew' number - with the owner's `CopToCrew=0.05` at 0.05 -
  and the police with R+0x04. That is the game's own swap (section 5's fed note), NOT changed here; it wants a
  decision before `[Fed] Player=1` is played with a CopToCrew under 1.
- **An Ally NPC with no crew record**: 0x78f470 answers 0xff, the index becomes -1 and the byte 4 bytes BEFORE the
  record table is taken as his stage - not a record. It only chooses between x 1 and x [R+0x1c]. ASSUMED that no
  such NPC shoots in a Fragile Alliance level (every Ally NPC there is a crew member; not checked on the maps).
- **klescort.c's BoardAll** raises a bot's stage byte to 3 while the vehicle waits: until the human reaches stage
  3 himself that bot is 'at another stage' (re/boardall_review_exe.md N1). Where the seventh is 1.0 that side
  effect is gone.

### 10.2 Every other reader of R+0x1c: none

Three sweeps of `.text` (capstone, linear with resynchronisation; 2.54 million instructions; the scripts were
scratch, the method is this paragraph):

1. `imul r, r/m, 0x70`: 26 places. Eight of them, in seven functions, form R from the tuning pointer; the other
   18 index other tables (none takes `[0x168d7c0]`).
2. The address 0x168d7c0 occurs 401 times, all in `.text`: 398 loads into a register, one compare, the
   constructor's store (0x530c33) and the clear at 0x5d1e18. Each loaded register was followed until overwritten
   (a call clobbers eax / ecx / edx): **no access with a fixed displacement into tuning+0x71c..+0xbeb** (the
   eleven records) exists anywhere; indexed accesses (displacement 0x6ac + field) only in the seven functions.
3. The pointer never leaves the function that loads it: nothing returns it (the small routines that end with it
   in eax return floats), nothing stores it, nothing passes it on (the ten `push` hits are `push ecx` used as a
   stack slot, and one `cdq`); the only member routines called on it are 0x4206f0 (player block) and 0x831f00
   (difficulty row). The 786 descriptors of the constructor (variable address + default) are all FREED at its end
   (0x530c0e..0x530c31, 0x6ad680): nothing keeps the addresses, so nothing can reset or load the values by list.

| field | reader | |
|---|---|---|
| +0x00, +0x04, **+0x1c** | 0x591b60 (0x591bd9, 0x591bd4, **0x591c1d**) | NPC hits NPC |
| +0x08, +0x10 | 0x8b8050 | an NPC hits the player |
| +0x0c, +0x14 | 0x7c1ba0 | the player hits an NPC |
| +0x18 | 0x6a1c40 | klbot.c's Retaliate |
| +0x20 | 0x46d4d0 | traitor limit |
| +0x24 .. +0x68 | 0x79b7c0 | traitor terms |
| +0x6c | 0x43ffb0 | traitors allowed |

The only WRITER is the constructor (level 1: `0x52b84d fld [0xba312c] / 0x52b853 lea ecx, [edi+0x738] / fstp
[ecx]`). LIMIT: a linear sweep; an access through a pointer made in a way it does not model would be missed
(no whole-object copy was found: no `push 0xc38`, no `mov ecx, 0x30e` before a `rep movs`).

### 10.3 The stock row

Read out of the constructor again (all 786 blocks split at the calls of 0x89e850; 785 defaults read):

| Arcade level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| +0x1c | 0.5 | 0.5 | 0.5 | 0.4 | 0.3 | 0.3 | 0.2 | 0.2 | 0.2 | 0.1 | 0.1 |
| +0x04 x +0x1c = what an off-stage heister deals, stock | 1.5 | 1.3 | 1.1 | 0.76 | 0.48 | 0.39 | 0.2 | 0.16 | 0.08 | 0.02 | 0.01 |

= section 2's row and `klr_code_off` in klbalance.c. The same sweep gives the six rows of `klr_code` and +0x18,
and the owner's game has confirmed those six ('is what the game's code builds', his log of 2026-10-10 18:38).
**The +0x1c row has NOT been seen in the running game**: the hook did not log it until now, and the hook's dumps
do not hold the tuning object. The new 'balance: stock, Arcade level N: ...' lines end with it, and the hook
writes the seventh ONLY if all eleven values are this row.

### 10.4 The dial

| | CrewOffStage | why |
|---|---|---|
| Risk=0 | not written | the game's own |
| Risk=1 'less lopsided' | 0.75 | a GUESS as Risk=1's other numbers are: they go about halfway from level 1's value to 1.0, this goes halfway from 0.5 to none |
| Risk=2 'the same risk' | 1.0 | the dial's own definition: 'the same gun at the same range costs everybody the same' cannot depend on where the HUMAN stands |
| Risk=3 'no favours' | 1.0 | the same |
| `CrewOffStage=<n>` | n, 0 .. 20 | beats the dial; a negative number = the game's own, also under a Risk. The text must be ONE number and nothing else (blanks or a `;` comment may follow): `0,75`, `1.0abc`, `abc` and a number over 20 are IGNORED - the dial's number stands and the log says 'CrewOffStage=0,75 is IGNORED: ...'. (Review N1: `strtod` alone read `0,75` as 0 and wrote 0 on eleven levels. The six older keys still take the leading number of such a text - `CopToCrew=0,05` is 0 - as they always did: not changed here.) `-0` is 0 |

The measurements do not argue against 1.0 for Risk=2 / 3: with it a heister's bullet costs a policeman the same
46.8 wherever the human stands, which is what the row promises. They do argue about the SIZE of the gain (10.0
point 4, 10.6).

**Ramp.** The six's rule is 'where stock is HARDER for the player's side than the dial, stock stays'. Stock's
number here is at most 0.5 - always the 'harder' one - so that rule taken per factor would never let the key do
anything. What an off-stage heister really deals is the product CrewToCop x CrewOffStage, so Ramp=1 is put on the
product: **CrewOffStage is lowered until CrewToCop x CrewOffStage is at most stock's own product on the level**
(the row above), and never below stock's factor. A number the user sets BELOW that is written as given.

| Arcade level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Risk=2 / 3, Ramp=1: CrewToCop | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0.8 | 0.4 | 0.2 | 0.1 |
| Risk=2 / 3, Ramp=1: **CrewOffStage written** | **1.00** | **1.00** | **1.00** | **0.76** | **0.48** | **0.39** | stock | stock | stock | stock | stock |
| Risk=1, Ramp=1: CrewToCop | 1.5 | 1.5 | 1.5 | 1.5 | 1.5 | 1.3 | 1 | 0.8 | 0.4 | 0.2 | 0.1 |
| Risk=1, Ramp=1: **CrewOffStage written** | **0.75** | **0.75** | **0.73** | **0.51** | **0.32** | stock | stock | stock | stock | stock | stock |
| Ramp=0 | the number on all eleven levels | | | | | | | | | | |

- So under the default Ramp=1 a later Arcade level is never easier than stock in this either: on levels 4-6 the
  off-stage heister deals exactly stock's 0.76 / 0.48 / 0.39 (the dial had him at 0.4 / 0.3 / 0.3).
- **Set alone** (`Risk=0`, no lower CrewToCop) with Ramp=1 the key writes NOTHING: with stock's CrewToCop 3.0 a
  factor over 0.5 would make an off-stage heister stronger than in the stock game. One line says so
  ('... it is NOT written on any level ... Ramp=0 lets it through') - as `CopToYou=0.05` alone is held by Ramp.
  This is a DECISION (the product rule), not a measurement; the alternative 'Ramp does not touch this key' would
  be one line in `klr_want_off`.
- **A key over 1** (review N3): allowed up to 20 as the six are. Beside a low CrewToCop the product rule then
  makes a heister at ANOTHER stage stronger than one at yours (`Risk=2 CrewToCop=0.1 CrewOffStage=20`, Ramp=1:
  x 15 at +0x1c on level 1, so 0.1 at your stage against 1.5 off it). Left as it is, not capped: it happens only
  on request, the dial's own numbers never pass 1.0, and live check O3a uses 20 on purpose.
- The line once per arming ends '(Ramp=1 holds it under N on M level(s): ...)' only when Ramp really gave some
  level less than the number asked for (review N4; `CrewOffStage=0.05` alone: no such remark. The review's own
  example, 0.25 alone, IS limited - on levels 7-11, where stock's 0.2 / 0.1 is under it - and says '5 level(s)').
- While the table fails the hook's shape test nothing is written and nothing is put back, the seventh included -
  the six's old behaviour; everything goes back on the first pass the test holds again (review N5, seen in its
  harness).
- What is written, when: with the six, in the same loop - only while an Arcade session runs on a level that is
  not stock, all eleven levels at once, put back with them. The stock row is read before any write and must be
  the row of 10.3 (within 0.001, all eleven); if not: 'balance: the float at +0x1c of the damage table is NOT the
  row this build's code writes (first at Arcade level N: found x, known y): CrewOffStage z is NOT written; the
  six factors are not affected'.

### 10.5 Police a heister kills, before and after (Arcade level 1)

`z_final\M02` (Late Night Opening): 11 armed police counted, health x 0.9 = 90 / 112.5 / 157.5 (median 157.5); 7 AI
heisters with the Rifle_zastavam85. COMPUTED with section 1 and 4's arithmetic (`kl_map_ai.bullet`): one NPC
bullet at 10 m = 46.8, x CrewToCop, x the factor; body shots; no regeneration. ASSUMED: 'per magazine' = 30
rounds (ZFFItemTemplateAmmo field 15 of the Zastava's ammo is 30 - taken as the magazine, the code that reads it
was not read) x the heister's accuracy as used 55 / 100 = 16.5 hits, all of them on one policeman after another;
the AI's burst length is not known, so this is 'per 30 rounds fired', not per second.

| Arcade level 1 | CrewToCop | x off stage | a body hit | hits to kill a policeman | police per magazine |
|---|---:|---:|---:|---|---:|
| stock, the heister at YOUR stage | 3.00 | - | 140.4 | 2 (1-2) | 8 |
| stock, at another stage | 3.00 | 0.50 | 70.2 | 3 (2-3) | 5 |
| Risk=1, at your stage | 1.50 | - | 70.2 | 3 (2-3) | 5 |
| Risk=1, another stage, BEFORE | 1.50 | 0.50 | 35.1 | 5 (3-5) | 3 |
| **Risk=1, another stage, AFTER** | 1.50 | 0.75 | 52.6 | 3 (2-3) | 5 |
| Risk=2 / 3, at your stage | 1.00 | - | 46.8 | 4 (2-4) | 4 |
| Risk=2 / 3, another stage, BEFORE | 1.00 | 0.50 | 23.4 | 7 (4-7) | 2 |
| **Risk=2 / 3, another stage, AFTER** | 1.00 | 1.00 | 46.8 | 4 (2-4) | 4 |

Hits to kill the median policeman on the later levels (Risk=2, Ramp=1):

| Arcade level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stock, your stage | 2 | 2 | 2 | 2 | 3 | 3 | 4 | 5 | 9 | 17 | 34 |
| stock, another stage | 3 | 3 | 4 | 5 | 8 | 9 | 17 | 22 | 43 | 169 | 337 |
| Risk=2, your stage | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 5 | 9 | 17 | 34 |
| Risk=2, another stage, BEFORE | 7 | 7 | 7 | 9 | 12 | 12 | 17 | 22 | 43 | 169 | 337 |
| **Risk=2, another stage, AFTER** | 4 | 4 | 4 | 5 | 8 | 9 | 17 | 22 | 43 | 169 | 337 |
| the same with Ramp=0 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |

(`tools/kl_map_ai.py balance` does not know the seventh factor: its ARCADE / RISK tables are the six. Not changed
- the file is not this track's.)

### 10.6 How often a heister IS at another stage (measured, the owner's own log)

`KLHook.log` of 2026-10-10 13:47 .. 2026-10-11 05:35, the crew lines of klbot.c ('bots: L1 s19 ... | 0 you in-play
g0 | 1 bot in-play g1 ...'), each line weighted by the time to the next (at most 10 s); a bot counts while it and
the human are 'in-play' in session state 19. 'Scripted' = a process whose log has the test rig's 'klauto:' line
(in all of them the human's stage stays 0); 'playing' = the others (his stage moves 0..3; the log has no dates -
the days are taken from CLAUDE.md's notes of when the crew log began and when the owner played):

| | processes | bot-seconds in play | at another stage than the human | |
|---|---:|---:|---:|---|
| the owner PLAYING (2026-10-10 16:59 .. 20:23) | 7 | 17,653 | 1,936 = **11 %** | 3 .. 16 % a process; bots ahead of him 1,078 s, he ahead of them 858 s |
| scripted runs, the 'player' standing at stage 0 | 38 | 43,620 | 32,582 = **75 %** | 41 .. 92 % (one run 0 %: nobody went in) |

If a heister's fire is spread evenly over his time in play, the factor at 0.5 cost the crew 5.5 % of its damage
on police in the played rounds and 37 % in the scripted ones; 1.0 gives that back (+6 % and +60 %). So: every
scripted balance / survival run so far measured a crew that fought at about 0.63 of its strength, and 'the bots
lose every fight they are in alone' was partly the test's own standing player. For the owner's rounds the
EXPOSURE is small (11 %); what that means for whether his crew lives is not known (10.6a).

**Recount and BoardAll** (finishing pass, own script, log snapshot 2026-10-11 06:04 = 264 processes): played 7
processes, 17,655 bot-seconds, 1,935 off stage = **11.0 %** (3 .. 16 %) - the table's numbers hold; scripted
without BoardAll 40 processes, 44,583 / 33,605 = 75 %; scripted with BoardAll's stage write 2 processes (03:22
has no crew time; 05:27 Late Night Opening 71 %, 06:00 the bank 63 %).
The seven played processes are all OLDER than `[Bots] BoardAll` (first in the log 2026-10-11 03:22), and BoardAll
writes stage 3 into a held bot's record while the vehicle waits (10.1). The review took the 11 % for a FLOOR once
BoardAll is on. Checked on the played sessions' own lines, that does not follow - BoardAll moves the figure both
ways: a bot at stage 1 / 2 at the human's own stage becomes 'off stage' (time gained), a bot at 1 / 2 while the
human is already at 3 becomes 'on stage' (time cleared). In those sessions the vehicle waited (state 3) for 227
of the 17,655 bot-seconds (1.3 %): 1 s of the first kind, 70 s of the second. Upper bounds of the direct effect
(the 15 s 'held still' condition ignored): **between 10.6 % and 11.0 %**. NOT in that bound: what the bots then
do differently (they board instead of staying). So: measured before BoardAll, not shown to rise with it, and
**not measured with it - no played session with BoardAll is in the log yet. Recount after the owner's next
played sessions** (the method is this section's first paragraph).

### 10.6a How the bots go DOWN (the same log; corrected after the review, defect M1)

The first version of this section said 'what kills his crew is what they TAKE ... and the one-step kills', and
10.9 told the reader not to judge by bots 'dead' because 'what kills them are the ONE STEP losses, which no
damage factor touches'. **That was wrong**; the log refutes it. Own count (finishing pass) on the snapshot of
2026-10-11 06:04: every 'bots: record N (bot): lost X (A of M) ... - DOWN' line, traced back through that
record's losses to the last time its health was whole:

| | DOWN | |
|---|---:|---|
| all | **41** | in 7 processes, every one scripted, `[Bots] Log=2`, police->crew 0.03 .. 0.15, the human at stage 0 throughout |
| by ordinary losses only (no step over 100 anywhere in the descent) | **35** | 14 .. 80 losses (median 41) within 3 .. 40 s (median 14 s) of the first |
| the last step over 100 (the hook's own 'ONE STEP' rule) | **6** | 2 are marked by the newer hook (236, 208); 4 are in the two oldest processes, whose hook did not print the mark (202, 115, 246, 120). The review counted 39 / 2: it took the marked lines only |
| lines that carry the stage | 27 | **26 at stage 1** (the human at 0: under the seventh factor), 1 at stage 0 (a step) |

Ordinary losses at police->crew 0.05: 1,217 lines, median 5, nine in ten at 12 or less (0.03: median 4; 0.15:
median 10). So a bot is not killed by one freak hit: it is worn down by 40-odd hits in a quarter of a minute,
which is many guns at once - and how many guns are still firing is what the crew's own damage decides. In these
runs that damage was halved by the seventh factor (26 of 27).

**Played rounds: nothing is known.** 9 processes have bot loss lines at all and none is a played one (the
owner's ini has `[Bots] Log=1`). `[Bots] Log=2` in his ini would show how HIS crew goes down - the lead's call.

**The 'before' side that is already in the log** - Retomoto Tower through the tab, the scripted standing player,
the owner's `[Balance] Enable=1 Risk=2 CopToCrew=0.05`, the factor at the game's 0.5 (seconds after GO = the
first crew line in session state 19; the first bot is at another stage than the human at GO + 18 .. 19 in all):

| hook start | Retomoto build (archive bytes, directory hash) | DOWN of 7 | first DOWN | sixth DOWN | losses up to GO + 90 s: lines / sum |
|---|---|---:|---:|---:|---:|
| 05:11 | an earlier build: 218,932,836 d9728fde | 6 | 73 (a step; by fire 85) | 114 | 133 / 1,023 |
| 05:37 (the lead's R7a) | `z_route7\retomoto_full`: 218,973,508 ffd5e544 | 6 | 85 | 113 | 105 / 590 |
| 05:45 (R7b) | the same | 6 | 92 | 121 | 80 / 487 |
| 05:53 (R7c) | the same | 6 | 77 | 108 | 146 / 854 |

(R7a .. R7c are CLAUDE.md's note of 2026-10-11 05:38-06:08: TEST hook test_board4, idle player, Escort=1,
BoardAll off, 'six of seven die GO+77..122 s at the reception fight each time, 246..268 bullet hits, no one-step
kill' - the same lines, counted there by the lead.)

Read from it: (1) the DOWN count and the DOWN times repeat closely from run to run (6 / 6 / 6 / 6; first DOWN by
fire 77 .. 92, sixth DOWN 108 .. 121), so they can carry a comparison; (2) the first version's metric - the
number and the sum of 'lost' lines up to a fixed time - does NOT: cut at GO + 90 s it gives 590 / 487 / 854 on
the three runs of ONE build and script (a factor of 1.75; 1,023 on the fourth), and cut at GO + 120 s or later
it gives 1,748 / 1,600 / 1,605 only because six bots are then dead in every run (six times 252 and what came
back in between) - it is noisy early and saturated late, so it could not have shown a factor of two. The
review's S1 is right about it.
And one caution: at 02:27 (another build, 218,932,948 63be7616) a run had `CopToCrew=0.03 CrewToCop=3.0`, so
crew->police 3.00 and 1.5 off stage - THREE times the 0.5 of the four runs above - and all seven bots still went
DOWN (first by fire at GO + 118, last at GO + 192; the 02:16 run on that build with 0.15 / 1.0: seven DOWN by
GO + 85). Two keys differ between those two runs, so it isolates nothing; but it says a factor of two in the
crew's fire need not change how the Retomoto room ends.

### 10.7 Proof that nothing changes without the dial

Off-game harness (scratch; a made-up session / rules / tuning / player in the test's own memory, the hook's
helpers stubbed, every write printed): the COMMITTED klbalance.c (`git show HEAD:`) and the working one are built
into two programs and run through the same nine situations (stock level, not stock off / on the game's thread,
another Arcade level, session end, Arcade again, stock again, a police player, session end). Compared: every
write (address, value, order), the table after three of the steps, the end state.

    A. identical write traces, old against new                                      writes   at +0x1c
       Enable=0                                                                        0        0
       Enable=1 (Risk 0, no key)        also with Log=2, with CrewOffStage=abc / 99 / -1    0        0
       Enable=1 Risk=0 CopToYou=0.6 PlayerHealth=0.8                                   23        0
       Enable=1 Risk=0 CopToCrew=0.05 CrewToCop=1.0 Ramp=0                            120        0
       Enable=1 Risk=0 RegenDelay=8 RegenTime=8                                         8        0
       old Risk=2            = new Risk=2 CrewOffStage=-1                              247        0
       old Risk=1            = new Risk=1 CrewOffStage=-1                              198        0
       old Risk=3 Ramp=0     = new Risk=3 Ramp=0 CrewOffStage=-1                       379        0
       old Risk=2 CopToCrew=0.05 Log=1 (the owner's)  = new + CrewOffStage=-1          187        0
       a table whose +0x1c is not the known row (0.45 on level 4; not a number on 2):
           old Risk=2 = new Risk=2 (the seventh REFUSED, the six as before)            247        0
       a table that fails the shape test: old = new (the health object only)            13        0
    B. the seventh
       Risk=2 (Ramp=1): +0x1c of levels 1-6 = 1.0 1.0 1.0 0.76 0.48 0.39; 45 values in the first pass (39 + 6);
           the same 45 put back at the session end; the 88 floats bit for bit stock at the end; nothing written
           again on later passes or when the Arcade level changes; its line once per arming
       Risk=3 Ramp=0: 1.0 on eleven levels.   Risk=1: 0.75 0.75 0.733 0.507 0.32.   Risk=1 Ramp=0: 0.75 x 11
       CrewOffStage=1.0 alone: 0 writes and the line that says why;  with Ramp=0: eleven writes, all at +0x1c
       Risk=2 CrewOffStage=0.2: 0.2 on levels 1-6 (below stock: as given), stock from 7
       Risk=2 CrewToCop=3: nothing at +0x1c (the product would pass stock's)
       the owner's ini (Risk=2 CopToCrew=0.05): 35 values in the first pass (29 + 6)
    RESULT: PASS (18 + 19 checks)

So with `Enable=0`, or `Risk=0` and no `CrewOffStage`, not one byte more is written than by the committed file;
and `CrewOffStage=-1` under any Risk is the committed file's behaviour exactly. In the code: `klr_init` returns
before anything when Enable is 0; `klr.off` is -1 at Risk=0 without the key and then neither sets `klr.any` nor
passes the `off` test in front of the one new write; `klr_table`'s test for the six is unchanged (the +0x1c float
is only carried along).

**After the review** (the file as built in 10.8; the same harness, the working file compiled at /W4 without a
warning; the list above run again: PASS, 37 checks) - a second script, 61 checks, RESULT: PASS:

    C. the key's text, under Risk=2 (+0x1c of levels 1-6, or all eleven)
       0,75  1.0abc  abc  99  20.0001  1e400  nan  inf  '0.75 0.5'    IGNORED, the line 'CrewOffStage=0,75 is IGNORED:
           it must be one number of 0 .. 20 with a decimal point ...'; the dial's 1.0 stands (1 1 1 0.76 0.48 0.39)
       0.75   '0.75 ; three quarters'   '  0.75  '   .75   7.5e-1       0.75 0.75 0.75 0.75 0.48 0.39
       20                                                              1.5 1.3 1.1 0.76 0.48 0.39 (Ramp=1: the product)
       0   -0   -0.0                                                   0 on eleven levels, printed 'x 0.00'
       -1   -0.5   -inf                                                not written ('x -1.00')
       Risk=2 with the key ignored = Risk=2 without the key: the same trace;  no Risk, the key ignored: no write
    D. the once-per-arming line
       CrewOffStage=0.05 alone: eleven levels as given, no Ramp remark;   0.25 alone: levels 1-6 as given, 'Ramp=1
       holds it under 0.25 on 5 level(s)';   Risk=2: '... on 8 level(s)';   Risk=2 Ramp=0: no remark;
       1.0 alone: 'it is NOT written on any level ...'
    E. the live checks' inis (the owner's Enable=1 Risk=2 CopToCrew=0.05 Log=1 + ...)       values written / put back
       O0, O4 side A   (as it is)                       +0x1c 1 1 1 0.76 0.48 0.39, stock from 7        35 / 35
       O2, O4 side B   + CrewOffStage=-1                +0x1c stock, no seventh line                    29 / 29
       O3a             + Ramp=0 CrewOffStage=20         +0x1c 20 on eleven levels                       71 / 71
       O3b             + Ramp=0 CrewOffStage=0.01       +0x1c 0.01 on eleven levels                     71 / 71
       O3a against O3b: the six factors and +0x18 equal on all eleven levels - the two runs differ in +0x1c ONLY;
       Arcade level 1: the six of O3a / O3b (Ramp=0) = the owner's own (Ramp=1): 0.05 1 1 1 1 1;
       O4: side A against side B: the six equal on all levels; the table stock at the end of every one
    F. old against new once more, three tables each (stock, +0x1c not the known row, the shape test failing):
       Enable=0 (new: + CrewOffStage=20);  Enable=1;  Enable=1 + CrewOffStage=0,75;  + CrewOffStage=-0.0001;
       the owner's ini against + CrewOffStage=-1;  Risk=2 Ramp=0 CopToCrew=0.05 against + 'CrewOffStage=-1 ; the
       game's own';  Risk=1 and Risk=3 against + CrewOffStage=-1:    24 pairs, identical write traces, 0 at +0x1c

### 10.8 Builds

BUILT AGAIN AFTER THE REVIEW (2026-10-11 06:20), both without a warning at /W3: `klhook\build.bat` (SHIP) and
`klhook\build_auto.bat` (TEST) into the new folder `G:\kl_scratch\offstage2`, copied OVER the two folders of
`<work>\build\klhook\`. Sources: the hook as committed - the last commit that touches `klhook\` is 703d007, the
same files at 4d9a91d, 2a8b461 and 0ffad60 (the head at build time; review N8) - plus this track's klbalance.c
(sha1 52d26de3). So klhud.c is in both, off unless `[HUD] Enable=1`; the untracked `klhook\klclimb.c` of another
track is NOT (klhook.c does not include it).

    ship_bal2\dinput8.dll   SHIP   357,376 bytes   sha1 8953a2d26c3b662f9deaa12c259dc506bd011a45
    ship_bal2\KLHook.ini    the sample             sha1 8b620ef0caca9bc739b97ecd551e203c5761462a
    test_bal2\dinput8.dll   TEST   406,528 bytes   sha1 6d35d3cf06c502fb3faa261c9fd0ee5f2afc5e00

(The first pair, of 05:38 - b1e8ca48 / 26bb4e9e, the one the review read - is still in `G:\kl_scratch\offstage1`.
Against it the new pair differs by the three small things of 10.11: the key's text, one remark of one log line,
comments.)

NOTHING INSTALLED. With the owner's ini unchanged (`Risk=2`) this hook DOES change his game: the seventh factor
becomes 1.0 on Arcade levels 1-3 (0.76 / 0.48 / 0.39 on 4-6). `CrewOffStage=-1` keeps it as it was. That belongs
in CLAUDE.md when the hook is installed (the lead's file).

### 10.9 Live checks (the lead / the game holder; one variable a run)

| run | ini | do | must appear in KLHook.log |
|---|---|---|---|
| O0 | the owner's as it is (`[Balance] Enable=1 Risk=2 CopToCrew=0.05 Log=1`), hook ship_bal2, a Dead Men map | start a round | `balance: on; ... you->crew 1.00, crew off your stage x 1.00; ...` - `the damage table ... is what the game's code builds` - eleven `balance: stock, Arcade level N: ... crew off your stage x` with **0.50 0.50 0.50 0.40 0.30 0.30 0.20 0.20 0.20 0.10 0.10** (the first LIVE sight of the row) - `Risk=2 written for 11 Arcade levels (35 value(s) changed, Ramp=1); now on level 1: ... crew off your stage x 1.00` (45 without the CopToCrew key; it was 29 / 39) - `balance: crew off your stage (...), Arcade levels 1..11: x 1.00 1.00 1.00 0.76 0.48 0.39 0.20 0.20 0.20 0.10 0.10; stock x 0.50 ...; CrewOffStage 1.00, Ramp=1: 6 level(s) differ from stock (Ramp=1 holds it under 1.00 on 8 level(s): ...)` |
| | | if instead | `DIFFERS ...` and `the float at +0x1c ... is NOT the row ...: CrewOffStage 1.00 is NOT written`: 10.3 is wrong for the running game; the six still work; send the eleven stock lines |
| O1 | the same | quit to the menu, or start stock Subway | `the stock damage table is back (35 value(s))` |
| O2 | + `CrewOffStage=-1` | a round | `crew off your stage x -1.00` in the 'on' line, `29 value(s) changed`, no `crew off your stage (` line: the hook as it was |
| O3a | TEST hook test_bal2, Retomoto Tower through the tab exactly as the lead's runs R7a .. R7c (10.6a: `z_route7\retomoto_full`, idle player, Escort=1, BoardAll off), `[Bots] Enable=1 Log=2`, the owner's `[Balance]` + `Ramp=0` + **`CrewOffStage=20`** | one run to GO + 270 s | `balance: on; ... Ramp=0; ... crew off your stage x 20.00` - `Risk=2 written for 11 Arcade levels (71 value(s) changed, Ramp=0); now on level 1: police->crew 0.05  crew->police 1.00 ... crew off your stage x 20.00` - `balance: crew off your stage (...), Arcade levels 1..11: x 20.00` eleven times `...: 11 level(s) differ from stock`. Then the OUTCOME, below |
| O3b | the same, only **`CrewOffStage=0.01`** | one run | the same three lines with `0.01`; the outcome, below |
| O4 | the same map, script and hook; side A = the owner's `[Balance]` as it is (35 values, the seventh 1.00 on level 1), side B = + `CrewOffStage=-1` (29 values, no `crew off your stage (` line) | three runs a side; B first, once | DOWN count, the first DOWN by fire and the sixth DOWN, in seconds after GO - below |

**What can be measured.** Nothing in the hook logs what a policeman loses: `[Bots] Log=2` logs what a BOT loses
('bots: record 3 (bot): lost 0.6 ... g1 at x y z'), `[Balance] Log=2` what YOU lose. So:
- the VALUE in force is in the lines of O0, and the game reads the float anew at every hit (0x591c1d; no copy
  is kept anywhere, 10.2) - with the value in the table the effect follows from the code;
- the EXPOSURE is in the crew lines as they are: a bot whose `g` is not record 0's `g` is under the factor
  (10.6's count can be repeated on any log);
- the EFFECT shows only in outcomes, and the outcome that repeats from run to run is **bots DOWN and when**
  (10.6a: 6 of 7 DOWN in four runs of four, the sixth at GO + 108 .. 121) - not the number or the sum of the
  'lost' lines, which the first version of this section proposed and which is noisy when cut early (a factor of
  1.75 between three runs of one build and script) and saturated when cut late. (That version also said 'do NOT
  judge by bots dead ... what kills them are the ONE STEP losses': refuted, 10.6a.)
- a DIRECT number (23.4 -> 46.8 a hit) would need a read-only line per loss of a policeman's health object
  (`[actor+0x5fc]`, as klbot.c's `klb_health_tick` does for bots) - and a list of the level's police actors,
  which no part of the hook has. Not written.

**O3a against O3b: is the factor in force at all? (review S1.)** The first version's O3 compared 1.0 with 0.5 -
a factor of two, by a metric that cannot carry it. This pair compares 20 with 0.01 - a factor of 2,000 - and
differs in ONE key: under `Ramp=0` the six factors are the same in both on all eleven levels, and on Arcade
level 1 they are exactly the owner's own (0.05 1.00 1.00 1.00 1.00 1.00; proved off-game, 10.7 E). In these
runs the human stays at stage 0 and the first bot is at stage 1 from GO + 18, so nearly every shot a bot fires
is under the factor.
- **20**: one body hit of a heister kills any man of the level (Zastava 46.8 x 1.0 x 20 = 936; the toughest of
  the 82 counted on `v_rtbots\retomoto_bots` has at most 281 - `kl_map_ai.py balance`: 6 hits of 46.8; the tab's
  build of the day was not measured; even a limb hit, x 0.2, costs 187). The guards that wore six bots down
  between GO + 73 and GO + 121 in every one of the four runs should be dead long before: expect clearly FEWER
  than 6 DOWN, and bots that get past stage 1 with their loot.
- **0.01**: a hit costs a guard 0.47 - over 300 hits for the median policeman, who also heals - so no guard falls
  to a bot inside: expect 6 or 7 DOWN, no later than the four runs.
- **The same DOWN count and DOWN times in both** (the sixth inside GO + 108 .. 121 in both): the factor is NOT
  in force where 10.1 reads it. Stop, change nothing else, send both logs. **A gross difference**: the whole
  chain - the key, the value in the table, the game's use of it at a hit - is shown in two runs.
- 0.01 and not the review's 0: 0.01 is a number the game's own table holds for a damage factor (police -> crew on
  Arcade level 1), while a damage of exactly 0 is something the stock table never produces; and 936 a hit is
  inside what the game does itself (the player's head shot on level 1: 58.5 x 10 x 2.0 = 1,170). GUESS that
  this is the safer of the two; neither has run. Bots still at stage 0 (the first 18 s) are at the human's stage
  and outside the factor in both runs.

**O4: does 1.0 change the fight? - only after O3 showed a difference.** Side B has four runs in the log already
(10.6a's table), but under the older hook and on two builds of the map (three on ffd5e544, one on d9728fde); so
one B run with THIS hook and the tree as it then is comes first and must give the known picture (6 DOWN, the
sixth at GO + 108 .. 121) - otherwise the 'before' side has moved and is run three times too. Then three A runs.
- all three A runs outside B's range - fewer than 6 DOWN, or the sixth DOWN later than about GO + 135 (B's
  latest plus B's whole spread): the factor of two changes this fight;
- all three inside: no visible effect at this size on this fight (10.6a's caution: with three times the crew's
  fire all seven still went down). Then it is what the bots TAKE that decides here, and the factor's gain is the
  arithmetic of 10.5 and no more;
- mixed: more runs, the same two measures.
The DOWN lines are counted as 10.6a does: last step over 100 = a step, else fire; seconds after the first crew
line in session state 19. For the owner's own rounds the measure is the recount of 10.6 after he has played, and
`[Bots] Log=2` in his ini if the lead wants to know how HIS crew goes down.

### 10.10 Assumed, and not known

ASSUMED: Risk=1's 0.75; the product rule for Ramp (a design decision); the arithmetic of 10.5 (10 m, body shots,
no regeneration, 30-round magazine, accuracy 55 as the hit share, even spread of fire over time in 10.6); that a
dead human stays the local player object; that no Ally NPC without a crew record shoots; that 0.01 is a safer
'nothing' than 0 for run O3b (a GUESS); the police health behind O3a's 'one body hit kills' is `v_rtbots`', not
the tab's build of the day; the 'scripted' / 'played' split of the log (a `klauto:` or `script N:` line).
NOT KNOWN: the +0x1c row in the running game (O0); whether the game uses the value where 10.1 reads it (O3a /
O3b); whether a factor of two changes the Retomoto fight at all (O4; 10.6a's caution); how the owner's crew goes
down when HE plays (no 'lost' lines in a played session); the exposure in played sessions with BoardAll on;
what `[actor+0x774]` is; when the local player's index is 0xff during a round; whether a traitor bot's hits on
other bots ever pass 0x61aac1 (they would be scaled by this too).
NOT DONE: `tools/kl_map_ai.py balance` (the seventh factor in its tables), `klhook.c`'s head comment (it lists
neither klbalance.c nor [Balance]), CLAUDE.md (none of the three is this track's file); a police-health log;
anything about the fed swap of 10.1 (as a fed with `CopToCrew=0.05` an AI heister shoots police at 0.05 and is
shot at CrewToCop: the lead decides before `[Fed] Player=1` is played with a CopToCrew under 1); the six older
keys still read `0,05` as 0 (their old behaviour; only the seventh's text is strict).

### 10.11 After the review (`re/balance_offstage_review.md`, ACCEPT WITH FIXES), 2026-10-11

| defect | what was done | evidence (own; scripts are scratch, the method is in the section named) |
|---|---|---|
| M1 must: 'what kills them are the ONE STEP losses' | **Confirmed wrong, text corrected**: 10.0 point 4, 10.6's last paragraph, 10.6a (new), 10.9 | 41 DOWN lines traced back: 35 by ordinary losses only, 6 with a last step over 100 (the review's 39 / 2 took only the lines the newer hook marks); 26 of the 27 with a stage at stage 1, the human at 0 |
| S1 should: the run that is to show the effect is too weak | **Fixed**: O3 replaced by O3a / O3b (20 against 0.01: one key differs, a factor of 2,000) and O4 (1.0 against -1 by DOWN count and DOWN times, three runs a side, after one run that re-checks the 'before' side) | the old metric is noisy cut early (sum of losses up to GO + 90 s: 590 / 487 / 854 on three runs of one build and script) and saturated cut late, the new one repeats (6 / 6 / 6 / 6 DOWN, the sixth at GO + 108 .. 121); off-game: the pair's inis write 20 / 0.01 on eleven levels and differ in +0x1c only (10.7 E). Changed against the review's proposal: 0.01 instead of 0, `Ramp=0` on BOTH runs |
| S2 should: the 11 % is older than BoardAll and 'a floor' with it | **Fixed in part, refuted in part**: 10.6 now says when it was measured and that a recount with BoardAll is owed; 'a floor' does not follow | recount 17,655 / 1,935 = 11.0 %; in those sessions the vehicle waited for 227 bot-seconds, in which BoardAll's stage write could add at most 1 s off stage and clear at most 70 s: 10.6 .. 11.0 % |
| N1, N2 notes: `0,75` read as 0; a key over 20 dropped silently; `-0` | fixed in the code: the text must be one number and nothing else, an ignored key is said in the log, `-0` is 0 | 10.7 C |
| N4 note: the Ramp remark printed when Ramp limited nothing | fixed in the code (and the review's example turned out to BE limited, on levels 7-11) | 10.7 D |
| N3, N5 notes | left as they are, said in the code's head comment and in 10.4 | |
| N7, N8 notes | section 7 / check B1 / B2 and 10.8 put right here; `kl_map_ai.py`, `klhook.c`'s head comment and CLAUDE.md are not this track's files | |
| N6 note: the fed swap | not this track's; in 10.1 and 10.10 for the lead | |
