# AI heisters that take cover, spread out and stay alive: what the engine offers

Agent b-dynamic, 2026-10-10 evening. RESEARCH ONLY: static reading of `kl2.exe` (base 0x400000) and
measurements on the 21 stock levels (F01 from `KL_PortBackup`) and on five builds, read only:
`<work>\build\y_loot2\M01 M02 M03 M06` and `<work>\build\rt_full4\retomoto_full`. **Nothing ran in
the game, nothing was built, installed or changed; this file is the only output.**

The owner, after playing with Risk=2: "the ai heisters just path the same then die so quick now ...
make them more dynamic give them a bit of personality so they can move a bit more like the bots to
the van to escape make them utilise cover and they know whos infront of them".

Status words: **read** = disassembled at the address given; **measured** = counted on level files
(scripts in section 9); **ASSUMPTION** / **GUESS** = inferred, not confirmed; **not read**.
Field numbers are 0-based positions in a controller's field list (`re/kl2.json`). Distances are
world units (100 = 1 m).

## 0. Short answers

1. **Cover is not a behaviour the level asks for; it is something every soldier does by itself
   when a cover is near the place it was told to hold.** Each soldier (AI heisters included) is
   given the same 25 tactics at creation (0x6ab250), among them `AttackFromCover`, `DefendCover`,
   `AttackFromCornerCover`, `AttackNoCover`, `CloseIn`. `DefendCover`'s test (0x84dc90) looks for a
   cover **within 500 of the soldier's defend position**. No cover there = the soldier fights
   standing in the open (`AttackNoCover`).
2. **The Dead Men maps DO have cover data, in Dog Days' own form.** Covers are not a file: at the
   load `CFFCoverList` (0x6d6a80) turns every object named `*coverbox*` into covers (`*coverboxh*`
   high, `*coverboxm*` / `*coverboxl*` low, `*coverboxcar*`; case ignored). The builds carry
   104 .. 480 such objects (stock Fragile Alliance: 153 .. 544), same class, each with a model.
   Nothing has to be generated.
3. **Why our bots die: their places are not at covers, they sprint, and all seven share one
   chain.** Measured: a stock bot's hold place is 165 .. 291 from the nearest cover box (median per
   level), 54 .. 94 % of the places within 2.5 m; ours are 384 .. 487 away and 9 .. 27 % within 2.5 m.
   Stock bots sprint on 92 of 1,100 steps, in 3 of 9 levels (63 of them on F02, the level whose
   bots are also furthest from cover); Retomoto's bots sprint on 63 of 70.
   Stock bots get 16 .. 85 s of "fight here" timers each and pick a random branch at 3 .. 9
   junctions; ours have 0 .. 10 s and no branch at all.
4. **Stock gives its bots no personality in numbers**: all 63 have one `ZSoldier` row (F05: a second
   one), one rifle, one squad setting. What makes them look different is (a) a `RandomTrigger` at
   every junction, drawn per bot per round, (b) a hold place of their own at each "pos" step,
   (c) waits on timers and on "these enemies are dead". All of it is level data we can author.
5. **Awareness**: `ZSoldier` field 15 is NOT the sight range (section 4): it is the radius at which
   an idle SQUAD is woken by a player; 1.0 on bots and on most campaign enemies is "only by
   script". Sight is a global tuning value times a per-squad factor (`SquadModifierBehaviour`
   field 14); fields 16 / 17 are the two sixth-sense ranges, used only when the squad modifier's
   field 16 says `eCSS_Enabled` - and the bots' row already holds 600000 there.
6. **Follow**: the campaign partner follows through `ZMercSquad` + team `Mercenary`, which a bot
   cannot be (a bot is a bot because its team is `Ally`). What a bot squad can run:
   `FollowBehaviourRout` naming an object (stock: always the player's; code also takes an actor =
   another bot) and `DefendPlayerPosBehaviourRout` = "go to where the nearest player is now"
   (266 stock uses, all on enemies). Both untested on an Ally squad.
7. Recipe, ranked: section 7. The first four steps need only what stock bots already use.

## 1. The behaviours a squad script can run

### 1.1 Classes and fields (read from the schema; enums from the exe)

A step is a `ZGROUP` child of the squad with one of these controllers; a trigger starts it by
naming the group. 26 `...BehaviourRout` classes are registered; counts are uses in the 9 Fragile
Alliance levels (F) and the 12 story levels (L), measured.

| controller | F | L | fields (kind) | what it does |
|---|---:|---:|---|---|
| `DefendBehaviourRout` | 1,272 | 358 | 0 s (ONE place: a box or an object, even an actor), 1 refs (1..3 boxes walked in order), 2 b, 3 b, 4 `EDefendMoveSet` {NotSet, Run 0, Walk 1, Sprint 2, Sneak 3, Relaxed 5, SneakRun 11}, 5 `EDestinationFormation` {NotSet, Line}, 6 s, 7 refs (NEXT), 8 b, 9 b | go to the place(s); the last one becomes the soldier's DEFEND POSITION (soldier+0x64c: x y z, +0x18 distance factor - read 0x7acb30, 0x603710) |
| `RunToCoverBehaviourRout` + child `RunToCoverPosInfoRout` (`ZSTDOBJ`) | 143 + 290 | 792 + 1,169 | rout: 0 refs (NEXT), 1 b, 2 b. PosInfo: 0 b, 1 b, 2 b, 3 `ERunToCoverMoveSet` {NotSet, Run, Sprint, SneakRun}, 4 `EPreferredCoverUsage`, 5 s = the ACTOR GROUP that is to run there | each named member runs to cover at its PosInfo; **the step is done only when every one of them has arrived or is dead** (read 0x6fae80: waits for soldier+0x4fc), then NEXT |
| `SquadModifierBehaviour` | 247 | 953 | 29 fields, section 1.2 | changes how the squad fights; NEXT = field 26 |
| `KickDoorBehaviourRout` + `KickDoorBehaviour_PosInfo` | 56 | 29 | 0 refs, 1 b, 2 b; PosInfo 0 s actor group, 1 s door | kick that door |
| `HuntBehaviourRout` | 5 | 0 | 0 s (a `SearchBox` child), 1 b, 2 refs, 3 b, 4 b | search a box for the enemy (F02 1, F03 4 SWAT reinforcements) |
| `FlankingBehaviourRout` | 0 | 34 | 0 s `LeftFlank#1`, 1 s `RightFlank#1`, 2 refs, 3 b, 4 b | send the squad to two flank points (story police; NO Fragile Alliance level uses it) |
| `PatrolBehaviourRout` | 9 | 8 | 0 `EPatrolPath`, 1 refs, 3 `EPatrolMoveset`, 5 f 50, 7 f 200 ... | idle walk |
| `DefendPlayerPosBehaviourRout` | 0 | 266 | 0 refs (NEXT), 1 b, 2 b | every active member is ordered to the position of the NEAREST PLAYER (read 0x622c40 -> 0x7263d0: nearest of the player slots gamedata+0x828..; the order is the soldier's virtual +0x13c, the one the rules use for "go to the boarding box"). One order per trigger. Stock: enemy squads only |
| `DefendNPCPosBehaviourRout` | 0 | 37 | 0 refs, 1 b, 2 b, 3 f 1.0, 4 s (an actor) | the same for an actor's position |
| `DefendCurrentPosBehaviourRout` | 0 | 6 | 0 refs, 1 b, 2 b | hold where you stand |
| `FollowBehaviourRout` | 0 | 104 | 0 s = the object to follow, 1 refs, 2 b, 3 b | section 5 |
| `FollowPlayerBehaviourRout` | 0 | 0 | 0 refs, 1 b, 2 b | re-starts following the target a soldier ALREADY has (read 0x6698b0 -> 0x4be760 with 0: nothing if soldier+0x63c has no target) |
| `LeapFrogBehaviourRout`, `BloodLustBehaviourRout`, `CoveredMoveActRout`, `GrenadeAttackBehaviourRout`, `RunForHelpBehaviourRout`, `WarnBehaviourRout`, `KillCiviliansBehaviourRout`, `DownNotDeadBehaviourRout` (4, L10) | 0 | 0 (4) | - | registered, in no stock level (except the last): no evidence how they behave |
| `Vehicle...BehaviourRout` (9 kinds), `HeliFlyBehaviourRout` | 39 | 126 | - | vehicles |

Not behaviours but squad kinds: `ZSquadScript` (the squad of every Fragile Alliance actor),
`ZMercSquad` {4 x `EIsMercenary`} (211, story only: the partner's squads), `ZFusionSquad` (86,
story cut scenes).

`ZSquadScript` (21 fields): 0 `EAttitude` {eStayBack, eUnleashed}, 1 `EGameType`, 2
`EIdleAlertness` {Normal, Slow}, 3 b, 4..18 reference lists (events), 19 b, 20 I.

### 1.2 `SquadModifierBehaviour`: every switch, what it sets, who uses it

Read: `ZSquadModBehaviourGoal` slot 2 (0x578ce0) goes through the modifier object (field n at
+0x48 + 4n) and calls one setter per field; the retail exe still holds the log texts, which name
them. "F / L" = uses with a value other than NotSet (measured, all 21 levels).

| field | enum | setter (text in the exe) | F | L | on stock bots |
|---|---|---|---:|---:|---|
| 0 | `ELeashModifier` Leash / Unleash | soldier+0x6fc = 0 / 1 ("SquadModifier: Leash / Unleash") | 46 / 37 | 14 / 167 | Leash 14 (F03 F05), Unleash 9 (F05 F09) |
| 1 | `EDamageModifier` 0..100 % | 0x7e25c0 | 0 | 154 | - |
| 2 | `EHealthModifier` 10..100 % | 0x5676e0 ("Setting %i number of hitpoints") | 0 | 36 | - |
| 3 | `ECommandModifier` FollowP1 / P2 | 0x6b01e0: only members ALREADY under that player's command (soldier+0x69c == player and +0x6a4) | 0 | 0 | - (no use for a bot) |
| 4 | `EActivationModifier` | Activate / Deactivate the actors | 19 | 176 | - |
| 5 | `EEngageModifier` HoldFire / FireAtWill | 0x722ed0 | 6 | 61 | - |
| 6 | `EAlertModifier` | 0x532930 / 0x7ed6f0 | 11 | 169 | - |
| 7 | `EVulnerabilityModifier` | 0x5e0070 .. | 0 | 46 | - |
| 8 | `EFollowModifier` Normal..Tightest | soldier+0x6dc ("Setting follow distance factor %.2f") | 3 | 5 | - |
| **9** | `EDefendModifier` Normal / Tight / Loose | defend position +0x18 = **1.0 / 0.5 / 1.5** ("Setting defend distance factor %.2f", 0x603710) | 176 | 44 | Tight 100, Loose 43: the only field stock bots use besides 0 |
| 10 | `EBloodlustModifier` | 0x5cad40 ("Bloodlust %s") | 0 | 9 | - |
| 11 | `EVisionModeModifier` | lock / unlock the view direction | 0 | 2 | - |
| 12 | `EVisibilityModifier` | 0x7e7d30 ("SetVisibility %s"): invisible to others | 0 | 22 | - (story: the partner while "stealthy") |
| 13 | `EDownNotDeadModifier` | 0x803530 | 4 | 93 | - |
| **14** | `EVisionModifier` x 0.1 .. x 4.0 | 0x634700 -> soldier+0x74c ("SetVisionRangeFactor %.2f") | 16 (x 2: 6, x 4: 10) | 72 | - (Fragile Alliance POLICE: F02 F03 F04 F06 F07 F08) |
| **15** | `ECoverModifier` UseCovers / DontUseCovers | soldier+0x108 ("SetUseCovers %s", 0x54abe0) | 8 / 5 | 22 / 87 | - |
| **16** | `ECustomSixthSenseMod` | soldier+0x6ac ("CustomSixthSense: %s", 0x79c280 -> 0x7837a0) | 0 | 8 / 2 | - |
| 17 | `EDefendMoveSetMod` | 0x614e20 ("SetDefendMoveSet %i"): the squad's default move style | 0 | 34 | - |
| 18 | `ESpecialTargetMod` HighPrio / Normal | 0x7dade0 / 0x78bf10 ("SetSpecialTarget %s") | 0 | 5 | - |
| 19 | `EBlindfireProbabilityModifier` | 0x7f9210 ("BlindfireProbabilityModifier %5.2f") | 0 | 27 | - |
| 22 | `EShotCollision` | 0x4f32d0 | all | all | Enabled |
| 23 + 24 | `EAggroModifier` Default / Custom + float | soldier+0x744 = -1.0 / field 24 ("AggroFactor %5.2f", 0x71eda0) | 0 | 5 (0.0 four times, 0.5 once) | - (story: invulnerable friends get 0.0) |

Where the aggro factor is used in target choice: **not read**. ASSUMPTION from the story levels'
use (0.0 on friends who must not draw fire): it scales how much enemies want this man as a target.

### 1.3 What a soldier does by itself: the tactics

Read: `ZSoldier@CPPScript` slot 17 (0x6ab250, 1,818 instructions) creates, for EVERY soldier, among
others: `CloseIn`, `SwatCloseIn`, **`AttackFromCover`**, `AttackFromCornerCover`, **`DefendCover`**,
`AttackMountedWeapon`, **`AttackNoCover`**, `AttackInCrowd`, `CloseAttack`, `Loot`,
`BoardEscapeVehicle`, `BecomeTraitor`, `GraceShot`, `Heal`, `Follow`, `FollowIdle`,
`DefendPosition`, `HoldPosition`, `CoverFire`, `AttackTarget`, `StayInCover`, `GrenadeAttack`,
`EvadeDangerPoint`, `EvadeTearGas`, `Protect`, `Checkup`, `CloseInOnTarget`, `ReactToHumanShield`.
Only the dog (style 6) is set apart: soldier+0x108 (use covers) = 0 at 0x6ab290. So **an AI heister
has the whole cover repertoire of a policeman**; nothing has to be switched on. The names are the
tactics' own (slot 7 returns the text).

The tests (slot 11; 1.0 = wanted), read:

- `AttackFromCover` (0x680b20): the soldier may use covers (its virtual +0x7c, 0x543f20:
  soldier+0x108 set and not 0x72bc70), has a target (+0xb0), its actor is not locked
  (actor+0x5c8), and after the search 0x807c60 **a cover is held** (soldier+0xec).
- `DefendCover` (0x84dc90): may act (0x6d9eb0), has a target, may use covers; when it holds no
  cover it asks for one **around the defend position, radius 500.0** (0x7acb30 -> 0x6e65f0 ->
  soldier virtual +0x190 = 0x7f71e0, which needs the level's cover list: gamedata 0x713130).
  Wanted when a cover came back. So: *defend position within 5 m of a cover -> the man is in it*.
- `AttackNoCover` (0x85ece0): wanted when the soldier has arrived (soldier+0x4fc) and the target
  flags (+0xa8) say "known, in view" - the stand-and-shoot fallback.
- Leash (soldier+0x6fc) is read by `AttackNoCover` (0x7b1565), `SwatCloseIn` (0x7e576a), the cover
  search (0x807de8) and `DefendPosition` (0x85f89f): unleashed = no longer tied to the defend
  position. What each branch does with it in detail: **not read**.

A text in the exe for the failure: "TakeCover -> HoldUp. Can't find a cover." (`ZFlee`, 0x45b5a8)
and "ERROR: No coverlist. Can't take cover." (0x45b0d3).

## 2. How stock Dog Days uses them

### 2.1 Its own AI heisters (63 bots, 9 levels; measured)

| | F01 | F02 | F03 | F04 | F05 | F06 | F07 | F08 | F09 |
|---|---|---|---|---|---|---|---|---|---|
| Defend steps per bot | 10 | 17 | 10 | 13 | 16 | 18 | 28 | 22 | 23 |
| of them `eDMS_Sprint` | 21 of 70 | **63 of 119** | 8 of 70 | 0 | 0 | 0 | 0 | 0 | 0 |
| `RunToCoverBehaviourRout` per bot | - | 1 | - | 2 | - | 1 | - | - | - |
| `RandomTrigger` per bot | 3 | 4 | 3 | 5 | 5 | 4 | 9 | 8 | 8 |
| `TriggerActorsDead` per bot | 3 | (1) | 1 | 4 | 2 | 3 | 4 | 0 | 0 |
| sum of `TriggerDelay2` seconds per bot | 43 / 63 | 42 | 21 | 20 | 71 / 85 | 16 | 36 | 50 | 46 |
| `SquadModifierBehaviour` per bot | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 0 | 3 shared |
| squad attitude | StayBack | StayBack | StayBack | StayBack | StayBack | StayBack | StayBack | **Unleashed** | StayBack |
| hold places: median distance to the nearest cover box | 196 | 446 | 197 | 212 | 165 | 291 | 227 | 202 | 204 |
| ... within 5 m / within 2.5 m | 86 / 62 % | 61 / 31 | 79 / 65 | 100 / 54 | 99 / 94 | 73 / 32 | 85 / 56 | 97 / 64 | 100 / 60 |
| RunToCover points: median distance to a cover box | - | 92 | - | 169 | - | 158 | - | - | - |

How a stock route is built (F07 looked at node by node, `sp2.py F07`):

- The seven squads are COPIES: the same step names, and on the "rout" steps (two way points) the
  same coordinates for all seven (`020_DefendBehaviour_rout_merc_fight_left`: (9845, 440, 2761)
  then (9663, 0, 4356) for each of the seven).
- At every junction a `RandomTrigger` {0: 1; weights 3 / 3 (/ 3) or 33 / 33 (/ 34); one target
  list per weight} sends THIS bot left, right or through the middle:
  `010_RandomTrigger_rival_merc_fight` -> left / right / middle, `040_..._out_of_loot_area`,
  `051_..._junction_garage`, `060_..._BeforeStreet`, `066_..._to_the_street`,
  `071_..._middle_of_street`, `080_..._escape_area_left / right` (four ways each). Nine per bot.
  The draw is per bot and per round: that is why seven identical squads do not walk as one.
- The "pos" steps (hold) have a place per bot: `020_DefendBehaviour_pos_merc_fight_middle` x =
  10179, 10324, 10620, 10795, 10898, 10443, 10443 (z the same) - a line across the room.
- Between a hold and the next move there is a wait: `020_Timer_small_big_merc_fight` 12 s,
  `070_Timer_small_street_fight_left` 8 s, or `TriggerActorsDead` on the enemy groups of that
  room, or `TriggerLootDepleted` (15 .. 60 s) at the loot.
- Around them: `SquadModifierBehaviour` `eDM_Tight` at the loot and at the vehicle, `eDM_Loose`
  in between (5 of 9 levels), in F05 with `eLM_Unleash` / `eLM_Leash`.
- No bot has a modifier for vision, covers, sixth sense, aggro or blind fire; no bot squad uses a
  `ZSquadScript` event list.

Stock "personality" in numbers: **none**. `ZSoldier` is `eThug, eCustom, 50 50 50 280 50, 1.0,
600000, 600000` on 56 bots and `90 50 50 350 50` on F05's seven; the weapon is `Rifle_zastavam85`
on all 63 (`re/bots_squad.md` 3.1).

### 2.2 Its police (316 soldiers, 175 squads in F01..F09; measured)

- Routs: 115 `RunToCoverBehaviourRout` with 262 PosInfo (median 89 .. 238 from a cover box:
  the points ARE the covers; `eRMS_Run` 135, NotSet 87, `eRMS_Sprint` 34, `eRMS_SneakRun` 6),
  172 `DefendBehaviourRout` (NotSet 112, `eDMS_Sprint` 35 - 19 of them F08's, `eDMS_Run` 17,
  `eDMS_Relaxed` 4, `eDMS_SneakRun` 4), 5 `HuntBehaviourRout`, 9 patrols. **No `FlankingBehaviourRout` at all.**
  What looks like flanking in Fragile Alliance is several squads each run to covers on a
  different side, then unleashed.
- Modifiers (104): Deactivate 19 (parked until called), **Unleash 28**, Leash 32 (25 of them with
  `eDM_Tight`), vision x 4 on 10 and x 2 on 6 (6 of the 16 together with Unleash), Alert 11,
  FireAtWill 6, `eCOM_DontUseCovers` 5 (F03's SWAT while they storm, then `eCOM_UseCovers`, 8).
- Attitude: `eStayBack` 115 squads, `eUnleashed` 60.
- The usual wave (`re/retomoto_ai.md` 1.3): `10_RunToCover` or `20_RunToCover` by a RandomTrigger
  -> `30_smUnleash` -> `40_RunToEscape`.
- Rows: SWAT `eArmy eCustom 50 50 50 175 50`, street cops `... 100 0`, field 15 = 5000 and
  16 / 17 = 800 on every one of them.

So police are dangerous by RunToCover at real covers + unleash + far sight; they are not given a
smarter brain than the bots have.

## 3. Cover data

### 3.1 How covers come into being (read)

`CFFCoverList` is a controller with no fields on an empty `ZLIST` (`Specials!CoverPoints!
CoverControl` in stock, top-level `CoverList` in a Dead Men map; one per level - a second one is
the assert 0x6682c5 that Retomoto's run RT2 hit). Its slot 13 (0x6d6a80):

1. walks every geometry of the scene and keeps those whose NAME matches `*coverbox*` (0x8dfa90: a
   `*` pattern compared with `_memicmp`, so case does not matter) and whose class is one fixed
   class (mask test `[0x150c8a0]` / `[0x150c89c]`; ASSUMPTION `ZSTDOBJ` - every stock cover box
   is one), at most 5,000 (0x1388);
2. skips an object whose flag word (`[obj+4]+0x3c`) has bit 0x400;
3. `*coverboxcar*` -> 0x603830(obj, 0, 1, car); `*coverboxm*` or `*coverboxl*` -> low cover
   (obj, 0, 1, 0); `*coverboxh*` -> high cover (obj, 1, 1, 0); a 0x7c-byte record each, array
   reserved for 5,000 (0x975e0 bytes);
4. 0x603830 builds the cover from the object's box (four sides; 0x42a4d0 / 0x7b3020 x 4) and reads
   the optional controllers `PlayerCoverModifier` (96 `EMODIFIERSTATE` values: per side AUTO / ON /
   OFF / vault), `DynamicCover`, `DestructibleCover`, and the name suffix `*_depend_on_parent`.

The list is kept at gamedata+0x15a0 (`[0xdd265c]`), its records at list+0x50 (begin / end).
`CoverStateChanger` boxes switch covers on and off at run time (F 239, L 1,407 uses);
`NoCoverBox` and `PlayerCoverCollision` are the PLAYER's cover markers (Dead Men style; stock
Dog Days marks player cover with `PlayerCoverModifier` on the same boxes).

### 3.2 What the levels carry (measured, `cb.py`)

Objects named `*coverbox*` (H / M / car; "other" = `NoCoverBox` and the like, which are
`ZBoxPrimitive` and therefore not covers):

| level | H | M | car | all covers | | build | H | M | all covers |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|
| F01 | 166 | 129 | 11 | 306 | | `y_loot2\M01` | 64 | 76 | **140** |
| F02 | 72 | 57 | 24 | 153 | | `y_loot2\M02` | 133 | 49 | **182** |
| F03 | 294 | 165 | 3 | 462 | | `y_loot2\M03` | 59 | 45 | **104** |
| F04 | 247 | 168 | 1 | 416 | | `y_loot2\M06` | 174 | 86 | **260** |
| F05 | 444 | 100 | 0 | 544 | | `rt_full4\retomoto_full` | 314 | 185 | **499** (480 `ZSTDOBJ`) |
| F06 | 265 | 204 | 7 | 476 | | | | | |
| F07 | 291 | 84 | 5 | 380 | | | | | |
| F08 | 219 | 173 | 0 | 392 | | | | | |
| F09 | 303 | 120 | 3 | 426 | | | | | |

Story levels: 338 (L09) .. 1,398 (L04). Every level and every build has exactly one `FFCoverList`.

The Dead Men boxes are the same thing as stock's: `ZSTDOBJ`, 8 properties, a model number each
(M01: 61 different models on 140 boxes; F07: 122 on 380), children of rooms (119 of 140) or of
props / cars (`AI_Enemies!FrontMall_02\Bentley_02\CoverBoxH_01`). Dead Men used the same naming, so
the graft carried them over without anyone asking. They have no `PlayerCoverModifier` (0 in the
builds, 50 .. 349 per stock level): every side is on AUTO.

**Not established (cannot be, offline):** that the game builds a cover from each of them - the
class mask and the flag bit of step 1 / 2 are run-time values. A live check that only READS data:
log `(end - begin) / 0x7c` of the vector at `[[0xdd265c]+0x15a0]+0x50` after the load; it should be
near the table's numbers (stock Subway: about 306). Owner's own observation on Retomoto ("you see
them run away and they hide for cover", `re/retomoto_ai.md`) fits covers working there.

### 3.3 If a map had none

Not needed today. For the record: a cover is only a NAMED BOX with a model, so covers can be
authored by cloning an existing `CoverBoxM_nn` / `CoverBoxH_nn` object (model chunk reused, so no
`.prm` growth) to a new place and rotation - beside a pillar, a car, a counter. Deriving places
from navigation-mesh edges (array 6 of `kl_pf4`: edge vertex + 2-D normal) is possible in
principle but was not tried; cloning beside known props is the smaller step.

### 3.4 Our routes against the covers (measured, `dist.py`)

Distance from each place a bot's `DefendBehaviourRout` names to the nearest cover box:

| | places | median | within 5 m | within 2.5 m |
|---|---:|---:|---:|---:|
| stock F01..F09 bots | 112 .. 322 | 165 .. 291 (F02: 446) | 61 .. 100 % | 31 .. 94 % |
| `y_loot2\M01` | 91 | 473 | 54 % | 27 % |
| `y_loot2\M02` | 140 | 449 | 62 % | 13 % |
| `y_loot2\M03` | 112 | 487 | 54 % | 25 % |
| `y_loot2\M06` | 98 | 384 | 77 % | 23 % |
| Retomoto `rt_full4` | 182 | 445 | 60 % | 9 % |

And the police points we moved: Retomoto's 35 `RunToCoverPosInfoRout` (F07's squads, re-placed on
the street by guess) lie 420 from a cover box at the median, 29 % within 2.5 m (stock: 89 .. 238,
50 .. 100 %). They are "run to cover" orders that mostly point at open road.

## 4. Awareness, targets, health

`ZSoldier` (23 fields; D = the data block at soldier+0x6d8; `re/map_ai.md` 1 has fields 0 .. 14).
New here, all read:

| field | what it is | evidence |
|---|---|---|
| **15** | **the squad's wake-up radius, not sight.** `ZSquadScript` slot 25 (0x47e440, tail at 0x47e64c): while the squad is not yet woken (squad+0x20c == 0) it takes a random member, its position and `field 15 x the vision factor` (soldier virtual +0x130 = 0x7842f0) and asks the object at gamedata+0x15bc (0x4e71e0); a result over 1.0 sets +0x20c and sends the squad message 0x3d | police 5000 = they come alive when a player is within 50 m; bots 1.0 and 1,000 + story enemies 1.0 = "only when the script says". ASSUMPTION: what 0x4e71e0 counts (players in the radius) |
| **16, 17** | **sixth-sense range**, idle (0x4c12e0) and alerted (0x590320), used ONLY when soldier+0x6ac (custom sixth sense) is set; else the tuning table's `[0x168d7c0]+0xc4` / its alerted pair. Handed to the sense manager `[0x1535c70]` (0x833e20) | soldier+0x6ac is cleared at creation (0x615cdb) and set only by `SquadModifierBehaviour` field 16 (0x79c280 -> 0x7837a0, which re-runs both). Police 800 / 800, **bots 600000 / 600000**, never switched on for them. ASSUMPTION that the value is "notices anyone within this distance without seeing him"; the name is the exe's |
| sight | not a `ZSoldier` field: `soldier+0x74c x [0x168d7c0]+0xc0` (idle) or `x +0xd4` (alerted), through 0x7846d0 to the sense manager (0x7575f0). +0x74c is the squad modifier's vision factor (field 14, default 1.0) | so every soldier sees equally far unless its squad got a factor: Fragile Alliance police squads get x 2 or x 4 when unleashed (16 uses), no bot does |
| 19 | `EIsMercenary`: soldier+0x6e8 (0x622b3d); for team `Mercenary` 0 becomes 13. Non-zero = one of the PLAYER's men: joins the player's squad list (0x908040), follows the player from the start (0x615f86) | story partner: `eArmy eCustom 50 50 50 100 0`, field 19 = `Kane`, team `Mercenary` (11 actors in L01..L11) |
| 7, 8 | health and regeneration: `re/balance.md` (bots 280, field 8 = 50 -> 8 s after the last hit, whole in 8 s) | under Risk=2 about 5 police hits kill a bot; it heals only if nothing hits it for 8 s - which standing in the open it never gets |

Friend and enemy: the team is `[[actor+0x54]+4]` (0 Mercenary, 1 Enemy, 2 Ally; `re/bots_squad.md`).
0x451f30 (a per-soldier scan of the player slots gamedata+0x828..) returns at once for team 2 and
for mercenaries: bots do not run the "a player is near" reaction. How an Ally picks between
several enemies (`ZAttackTarget`, the target flags at soldier+0xa8, the aggro factor +0x744):
**not read**.

Why a bot runs past police: three things in our data, none of them a missing sense.
(a) `eDMS_Sprint` on the step (GUESS: a sprinting soldier does not shoot; six stock levels have
no sprinting bot, F01 / F03 a few dashes, only F02 - open ground to a helicopter - much); (b) the NEXT step is triggered the moment the place is reached - no
timer, no "those are dead" wait - so the defend position moves on before `DefendCover` /
`AttackFromCover` can settle; (c) attitude `eStayBack` + leash ties the man to a defend position
that is already the next way point.

## 5. Following

- **The partner of the story** (Kane beside Lynch): team `Mercenary`, `ZSoldier` field 19 `Kane`, in
  a `ZMercSquad` {0: Kane} group, steps `FollowBehaviourRout` {0: the path of the player's object,
  `AI!Friendly!Lynch...`} (104, 93 of them under `AI!Friendly!`), with `SquadModifierBehaviour`
  `eFM_Tight / Tightest` (follow distance), `eVISM_InvisibleToOthers`, `eEM_HoldFire`. None of that
  can be a Fragile Alliance bot: the crew record, loot and boarding all hang on team == `Ally`
  (0x8e5650), and `ECommandModifier` (0x6b01e0) and `FollowPlayerBehaviourRout` (0x6698b0) only
  act on men already assigned to a player.
- **`FollowBehaviourRout` on an ordinary squad** (read: rout slot 14 0x4cf010, goal slot 2
  0x4deed0): field 0 is resolved to an object when the level starts (0x8ccde0 + 0x4fe480; **no
  object = no goal, the step does nothing**). Each member then gets `SetFollow(object)` (soldier
  virtual +0x140, 0x4be760 -> follow control soldier+0x63c, source `ff2\characters\
  followcontrol.cpp`). If the object is an ACTOR (class test `[0x1547b24]`, then actor+0x77c = its
  soldier) the pair (squad, leader) is entered in a table of 8 (0x168dfc8..). Stock: two uses on
  `ZSquadScript` squads with team `Ally` (L02 `AI!Friendly!Glazer04_DemolishedHouse#01\
  050_FollowBehaviour`), all 104 name the player's object; following an actor is in the code and
  in no stock level.
  For bots that gives "who it follows": a follower's step names another bot's group
  (`...Squad#03\Glazer_Bodyguard_03`). UNTESTED. Following the HUMAN this way needs the path of
  the human's player object, and which of the 16 `ZFFPlayer` objects of a Fragile Alliance level
  that is in Arcade was not established here (`re/menus.md` 4: the hero is drawn at random).
- **`DefendPlayerPosBehaviourRout`**: needs no name - "go to where the nearest player stands now"
  (0x7263d0), then the usual defend there. One order per trigger; a `TriggerDelay2` that fires it
  again every few seconds would make an escort. ASSUMPTION that in Arcade the only active player
  slot is the human (the scan skips objects with flag bit 0x400). Stock uses it on enemies only.

## 6. What can differ per bot

All data, no code; "proven" = some stock actor has it in a Fragile Alliance level.

| what | where | stock evidence | note |
|---|---|---|---|
| which way it goes | `RandomTrigger` per junction | every stock bot, 3 .. 9 each | the cheapest "not all the same" |
| where it stands | own `Pos#nn` per hold step, AT a cover | every stock bot | section 3.4 |
| how long it fights at a stop | `TriggerDelay2` 8 / 12 s, `TriggerActorsDead` on the room's enemy groups | 7 of 9 levels | F08 / F09 use timers only |
| how long it loots | `TriggerLootDepleted` field 1: 15, 20, 60 | all | a greedy one 60, a nervous one 15 |
| waits for the others or runs | a `TriggerActorsDead` / timer before the exit step, or none | F01 F07 wait, F08 F09 do not | |
| move style | `DefendBehaviourRout` 4: NotSet / Run / Sprint / SneakRun / Sneak | bots: NotSet 1,008, Sprint 92; police: Run 17, SneakRun 4 too | SneakRun = the careful one |
| attitude | `ZSquadScript` 0: `eStayBack` / `eUnleashed` | F08's seven are Unleashed | the "rusher" |
| leash and spacing | `SquadModifierBehaviour` 0 and 9 | bots in 7 levels | Tight 0.5 / Loose 1.5 of the defend distance |
| accuracy, health, regeneration | `ZSoldier` 4, 7, 8 (`eCustom` only) | F05's bots 90 / 350 | the balance dial owns field 7 (`re/balance.md`) |
| weapon | `ZFFActor[1]` | all bots the same rifle; police carry 6 templates | a shotgun for the rusher, a rifle for the rear guard; `kl_arms` pools |
| sees further | modifier 14 `eVIM_Factor_2_0` | police only | |
| senses all round | modifier 16 `eCSS_Enabled` (ranges = the bot row's own 600000) | story enemies only (L03, L06) | the nearest thing to "knows who is in front"; ASSUMPTION |
| draws less fire | modifier 23 `eAGM_Custom` + 24 = 0.5 | story friends only | effect not read |
| blind fire from cover | modifier 19 | story only | |
| who it follows | `FollowBehaviourRout` 0 = another bot | code only | section 5 |

## 7. Recipe, ranked by what stock proves

"Cover data" = the map's `CoverBox` objects (all five builds have them).

| # | change | proven by | needs cover data | risk |
|---|---|---|---|---|
| **1** | **Put every HOLD place at a cover.** For each "pos" step: choose a `CoverBoxH/M` `ZSTDOBJ` on the bot's mesh part near the intended spot and set the `Pos#nn` box 100 .. 250 from its centre, on the side away from where the enemy comes (GUESS for the side; the engine chooses the side of the box itself, the place only has to be within 500: 0x84dc90). One box per bot per step. Report the share within 2.5 m; stock is 54 .. 94 % | 9 of 9 levels (section 2.1) | yes | none new: positions only |
| **2** | **No sprint except the last dash.** `eDMS_NotSet` on every step; `eDMS_Sprint` at most on the run from the last cover to the vehicle (F01 / F03 use it for a few steps). Retomoto has 63 of 70 on Sprint | 6 of 9 levels have none; F02 is the exception (63 of 119) | no | none |
| **3** | **Move, then hold, then wait.** Split each leg into a "rout" step (1 .. 3 way points, field 1) and a "pos" step (field 1 = one place at a cover), and put a wait before the next leg: `TriggerDelay2` 8 .. 12 s, or `TriggerActorsDead` {0: the ACTOR GROUPS of the enemies that guard this leg, 2: next} where the map has such groups. Stock: 16 .. 85 s of timers per bot; ours 0 .. 10 | 9 of 9 (timers), 7 of 9 (actors dead) | no | a bot that waits on enemies nobody kills stands for ever: always pair `TriggerActorsDead` with a timer to the same next step (F07 does: `070_Timer_small_...`) |
| **4** | **A random branch at every junction.** Two or three alternative legs (left / right / middle - through different doors, along different walls), chosen by `RandomTrigger` {0: 1, 1..3: 3 / 3 / 3, 5..7: one target list each}. All seven squads may stay copies of one another, as stock's are | 9 of 9, 22 .. 63 per level | no (but each branch's hold places as in 1) | every branch must end in the same stage triggers (ENTERS_BANK, exit box) - `kl_fa_bots`' check per chain |
| 5 | **Sub-groups and a rear guard by timing.** Loot wait 15 / 20 / 60 s (stock's three values) for three groups; the last group gets one more hold near the way out with `eDM_Tight` and 8 .. 12 s. Start: stock starts all seven 10 s after the round start; staggering `Timer_start_bots` into three `TriggerDelay2` (10 / 13 / 17 s) is a GUESS that uses only stock nodes | values proven, the grouping is ours | no | low |
| 6 | **`RunToCoverBehaviourRout` between holds** on the dangerous legs (street, forecourt): child `RunToPosInfo#01` [`ZSTDOBJ` + `RunToCoverPosInfoRout` {0, 1, 0, `eRMS_Run` or NotSet, `ePCU_NotSet`, the bot's ACTOR GROUP path}] placed ON a cover box (stock: 90 .. 170 away), rout {0: [next], 1: 1, 2: 0}. The chain goes on only when the bot is IN the cover (0x6fae80), so two in a row = bounding from cover to cover | bots: F02 (7), F04 (14), F06 (7) - one or two per bot; police: 115 | yes | a point with no reachable cover: the bot may never "arrive" - what the step does then was not read. Keep a `TriggerDelay2` to the same next step as a way out |
| 7 | **`SquadModifierBehaviour` per bot**: `eDM_Loose` while moving, `eDM_Tight` at loot and vehicle (stock bots); for the "rusher" `ZSquadScript` 0 = `eUnleashed` (F08) | bots in 7 levels; F08 | no | low |
| 8 | **Awareness**: on every bot one modifier fired with the first step: 14 = `eVIM_Factor_2_0`, 16 = `eCSS_Enabled` | field 14: Fragile Alliance police; field 16: story enemies. Never on an Ally | no | medium: unseen on bots; with a 6 km sixth sense a bot may turn to fight police far behind it instead of walking on - try 14 alone first |
| 9 | **Per-bot rows and weapons** (section 6): accuracy 40 .. 75, one shotgun rusher, one careful `eDMS_SneakRun` man | F05's row; police weapons | no | the balance dial must keep owning health |
| 10 | **Draw less fire**: modifier 23 `eAGM_Custom`, 24 = 0.5 | story friends | no | effect not read |
| 11 | **Followers**: two or three bots whose step is `FollowBehaviourRout` {0: another bot's group path} instead of a route of their own; the leader has the route. Stage triggers (ENTERS_BANK, exit box) must still be crossed by the follower itself | code only (0x4cf010) | no | high: no stock level follows an actor; a dead leader's followers - not read |
| 12 | **Escort the human**: `DefendPlayerPosBehaviourRout` {0: [a `TriggerDelay2` 5 s that names this step again]} for one or two bots after the loot | 266 stock uses on enemies; loop is ours | no | high: untested on Ally; a bot glued to the human may never cross its stage triggers and so never board - give it an `AllyEscapeBox` at the vehicle or a normal last leg |

Steps 1 - 4 together are simply "build the route the way stock builds it". They need no hook, no
new class, no model, sound or animation: the four budget sizes of every build stay as they are.

What NOT to do: `eCM_FollowP1`, `FollowPlayerBehaviourRout`, `ZMercSquad`, team `Mercenary` or
`ZSoldier` field 19 on a bot (section 5); a second `FFCoverList`; `FlankingBehaviourRout` for bots
(story police only; `re/retomoto_ai.md` D3 saw guards stand still when its points were off the mesh).

Also worth doing on the way (police, not bots): move Retomoto's 35 re-placed `RunToPosInfo` points
onto cover boxes (section 3.4) - the same nearest-cover search as step 1.

## 8. Checks an implementer can code (offline)

1. per build: number of `ZSTDOBJ` named `*coverbox[hml]*` and `*coverboxcar*` (section 3.2).
2. per bot hold place: distance to the nearest cover box on the same mesh part; report median and
   the share within 250 and 500; target = stock's (>= 55 % within 250, >= 85 % within 500).
3. no two bots share a cover box at the same step.
4. `eDMS_Sprint` steps per bot <= 1.
5. per bot: >= 3 `RandomTrigger`, every target list non-empty for a non-zero weight, every branch
   reaches the same stage triggers and the last step (the existing `kl_fa_bots` chain check, per
   branch).
6. sum of `TriggerDelay2` seconds per bot between 16 and 85; every `TriggerActorsDead` has a
   timer beside it to the same next step.
7. every `RunToCoverPosInfoRout` field 5 names an existing actor GROUP of the same squad, its node
   is a `ZSTDOBJ` child of the step, and it lies within 250 of a cover box.

Live, read-only: the cover count of 3.2; then by eye (`tools/kl_watch.py`): do bots crouch behind
boxes at a hold, do the seven leave the loot by different doors.

## 9. Not established, and how this was produced

- Nothing ran. That the Dead Men cover boxes become covers in the game (class mask, flag bit 0x400).
- Inside the cover search: how a side of a box is chosen, whether two soldiers can hold one cover,
  the role of the navigation mesh; what `eStayBack` / `eUnleashed` and Leash change inside
  `DefendPosition` and `AttackNoCover`; whether a sprinting soldier shoots; what a `RunToCover`
  step does when no cover can be reached.
- Target choice of an Ally, the aggro factor's use, what 0x4e71e0 counts, the exact meaning of
  "sixth sense".
- Which `ZFFPlayer` object is the human in Arcade (for a follow by name).
- `DefendBehaviourRout` fields 2, 3, 6, 8, 9 and `RunToCoverPosInfoRout` fields 0, 1, 2, 4: keep
  stock's values (2 = 1, 8 = 1; PosInfo 0, 1, 0, .., `ePCU_NotSet`).

Scripts (scratchpad `...\1e45a579-...\scratchpad\bd\`): `ext.py` (every AI controller of the 21
levels and 5 builds -> `<level>.json`), `c1.py` (census), `c2.py` (bot / enemy field values,
F01..F09), `c3.py` `c4.py` `c5.py` (story partner, squad kinds, modifier fields, teams), `cb.py`
`cb2.py` (cover boxes), `dist.py` (places against covers), `spread.py` `sp2.py` (route shape),
`lib2.py` (loader with world positions, on `kl_fa.load` + `kl_maps.world`); exe: `fn.py <address>`,
`vt.py <class>` (vtable slots with sizes), `rt.py <pattern>` (RTTI names), `sref.py <text>` (who
uses a string), `wr.py <offset> wb,rb,wd,rd` (who reads / writes a member), `strs.txt` (843 AI
texts still in the retail exe - the log lines "SquadModifier: ..." name most setters).
