# What a bullet costs whom in an Arcade round: measured, and one dial to make it even

Agent p-balance, 2026-10-10. OFFLINE: nothing launched, nothing installed, nothing written into the Dog Days
folder, no level built. Files: `klhook/klbalance.c` (new; NOT wired, see 7), `tools/kl_map_ai.py` (new command
`balance`), this note, `re/map_ai.md` 13. NOTHING HERE HAS RUN IN THE GAME.

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
| R+0x1c | 0x591be4..0x591c1d | times this when the SHOOTER is an Ally NPC (an AI heister) whose heist stage (record +0x78) is not the player's: 0.5 .. 0.1. Corrected 2026-10-11: this row had shooter and victim swapped; the routine's argument is the one whose team picks R+0x00 / R+0x04 above, and it is that actor's crew record (0x78f470) whose stage is compared with the local player's (0x6c7700). So a crew that is inside while you are outside hits police at half strength on Arcade levels 1-3 |

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
- Not touched: R+0x18 (klbot.c's Retaliate) and R+0x1c; NPC health; the difficulty option; any code.
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
        table written (39 values, Ramp: level 11 keeps 3.0 / 0.3 / 1.7 / 0.1) while +0x18 / +0x1c stay; the
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
| B1 | + `Risk=2`, `u_maps\M02` | the same round | 'Risk=2 acts on this round', 'written for 11 Arcade levels (39 value(s) changed', 'your health set: maximum 401.5 (the game gave 550.0)'; 'you lost' is now about 60 for an AK-74 body hit; a guard takes 3 Zastava body hits instead of 2 |
| B2 | the same | quit to the menu, start stock Subway | 'the stock damage table is back (39 value(s))', 'your health put back' (if the object lived), then 'nothing is written here' on Subway |
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
