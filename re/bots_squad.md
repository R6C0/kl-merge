# The AI heister squad of stock Fragile Alliance (Arcade), and what a new map must supply

Written 2026-10-10 (agent b-squad). OFFLINE: static reading of `kl2.exe` and of the nine stock
levels F01 (from `KL_PortBackup`) .. F09, plus the five finished builds (`<work>\build\z_maps\M01
M02 M03 M06`, `<work>\build\rt_ai\retomoto_ai`), read only. **Nothing was built, installed or run.**
The four large blocks of every build are therefore unchanged (section 9).

Status words: **read** = disassembled at the address given; **measured** = counted on level files
with the scripts named in section 10; **ASSUMPTION** = inferred, not confirmed; **not established**.

Field numbers are 0-based positions in a controller's serialized field list, as in
`re/fa_gamemode.md`. Paths are without the leading `ROOT\`.

## 0. Short answers

1. **Most of what a bot does is code, not level data.** Looting, boarding the escape vehicle and
   turning traitor are three AI tactics inside the soldier script (`ZLootTactic`,
   `ZBoardEscapeVehicleTactic`, `ZBecomeTraitorTactic`, all `@CPPScript`) that ask
   `ZGameRulesHeist` what to do. The level's squad (`merc_bot_squad`) is only a ROUTE: a chain of
   "go and hold this place" steps with waits between them. It names no escape vehicle, no boarding
   box and no spawn point in any of the nine levels (measured).
2. **A bot is any `ZFFActor` whose team is `Ally`**, in Arcade only. `ZSessionHandlerSP` slot 45
   (0x8e5650) hands every actor with `[[actor+0x54]+4] == 2` to `ZGameRulesHeist` slot 198
   (0x588980), which gives it a crew record. Its name and voice variant come from the character at
   index 18 of its GROUP's name (`Glazer_Bodyguard_0N` -> N). Seven per level, `Squad#02..#08`.
3. **It loots by itself**, from every money object the level registered, once it has walked through
   an `OnlineGamePlayTrigger` of kind ENTERS_BANK (section 4). `TriggerLootDepleted` does not make
   it loot: it is a WAIT ("these objects are empty, or n seconds have passed") that releases the
   next route step.
4. **It boards by itself** when the vehicle is there, if (a) it has walked through a BOARDS trigger
   or through the `OnlineExitLevelTrigger` box, (b) the vehicle has a boarding box and (c) the
   navigation mesh connects the bot to that box (section 5). The same code serves Dog Days' baked
   vans (`OnlineEscAnimatedVehicle`) and the spline car / helicopter form the Dead Men maps have
   (`OnlineEscHavokCar`). Helicopter levels add `AllyEscapeBox`: a bot standing in one boards.
5. **Everything those tactics need is already in all five builds** (measured, section 7): the
   three trigger kinds, the exit trigger, a boarding box, 133..363 money objects, `Hero_02..08`'s
   models, the `Kane_NPC` / `Lynch_NPC` animation sets, the weapon template, `Gameplay!AIMonitor`.
   Missing is only the squad itself: 7 actors and a route.
6. **Smallest squad that follows the stock pattern: about 16 nodes per bot** (stock: 50..99),
   three references into the map's loot and none to actors. F08 and F09 show that actor-dead waits
   are optional (they have none). Recipe: section 8.
7. Two maps need more than a route: **M03** (the mesh is in two parts; a bot cannot path to the
   van) and **Retomoto** (two halves joined for the player by the hook's jump). Section 8.4.

## 1. Who starts the squad

Measured, identical in 9 of 9 levels:

- One `AIMonitor` (F01 F04 F05 F07 F09 `Gameplay!AIMonitor`, F02 F06 `Scripting!AIMonitor`, F03 F08
  `Gameplay!AIDstuff!AIMonitor`). Its list 2 (the round-start event, `re/fa_gamemode.md` 3) names
  `<prefix>!merc_bot_squad!Timer_start_bots`; that is the ONLY reference into the squad from
  outside it.
- `Timer_start_bots` = `ZBoxPrimitive` + `TriggerDelay2` {0: 10.0, 1: 0.0, 2: -1.0, 3: 0,
  4: [first step of each of the seven squads]} (F05: eight targets, one extra wait).
  So the bots stand still for 10 s after the round starts, then all get their first step.
- Every squad group is `ZGROUP` + `ZSquadScript` {0: `eStayBack` (F08: `eUnleashed`),
  1: **`eHeistOnly`**, 2: `eNormalAlertness`, 3: 1, 4..18: empty lists, 19: 0, 20: 0xffffffff}.
  `EGameType` `eHeistOnly` = 8: the squad exists in Arcade only (in the enum table of kl2.exe:
  FragileAllianceOnly 1, TeamModeOnly 2, CampaignOnly 4, HeistOnly 8, UCCOnly 16). 63 of 63.

The graft already keeps `Gameplay!AIMonitor` of the host (`kl_fa.host_keep`); in the four z_maps
builds its list 2 holds `FASpecials!Timer_MissionBriefing` only (measured).

## 2. The squad as data: per level

`prefix` is the folder of the top-level names; "nodes" counts all of `*merc_bot_squad*`.

| | F01 | F02 | F03 | F04 | F05 | F06 | F07 | F08 | F09 |
|---|---|---|---|---|---|---|---|---|---|
| prefix | Gameplay | AI_Players | FASpecials | Gameplay | Gameplay | AI_Players | Gameplay | Gameplay | Gameplay |
| top-level subtrees | 20 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 12 |
| nodes | 393 | 380 | 351 | 428 | 429 | 456 | 694 | 540 | 552 |
| nodes per squad | 54 / 56 | 54 / 55 | 50 | 61 | 61 / 62 | 65 | 99 | 77 | 78 |
| behaviour steps per squad | 11 | 18 | 14 | 15 | 16 | 22 | 28 | 22 | 23 |
| `DefendBehaviourRout` | 70 | 119 | 70 | 91 | 112 | 126 | 196 | 154 | 162 |
| `KickDoorBehaviourRout` (+ PosInfo) | 7 | . | 28 | . | . | 21 | . | . | . |
| `RunToCoverBehaviourRout` (+ PosInfo) | . | 7 | . | 14 | . | 7 | . | . | . |
| `SquadModifierBehaviour` | 14 | 21 | 21 | 21 | 21 | 21 | 21 | . | 3 (shared, `TOOLBOX!`) |
| `MiniCutsceneRout` | 7 | . | . | . | . | . | . | . | . |
| `GatePath` / `GateGroup` | . | . | . | . | 28 / 14 | . | . | . | . |
| `RandomTrigger` | 22 | 28 | 21 | 35 | 35 | 28 | 63 | 56 | 56 |
| `TriggerDelay2` | 30 | 50 | 22 | 29 | 57 | 22 | 29 | 36 | 29 |
| `TriggerActorsDead` | 21 | 1 | 7 | 28 | 15 | 21 | 28 | **0** | **0** |
| `TriggerLootDepleted` | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| its field 0 (objects) / field 1 | 10 or 8 / 15 | 16 / 20 | 12 / 20 | 10 / 20 | 6 / 20 | 8 / 20 | 5 / 20 (one squad 0) | 38 / 15 | 6 / 60 |
| plain position boxes | 168 | 119 | 126 | 168 | 119 | 154 | 329 | 266 | 274 |
| extras | 6 `KickDoorMonitor` + 6 `RelayMessageList` (door -> cases) | | | | | | | | 4 shared `TOOLBOX!` steps |
| chain ends in | `110_SquadModifier_tight_defense_van` | 8 x `move_to_chopper_A..H` | `100_SquadModifier_tight_defense_chopper` | `100_SquadModifier_tight_defense_van` | `80_move_to_van_A` | 8 x `move_to_chopper_A..H` | `100_SquadModifier_tight_defense_van` | `120_move_to_chopper_A` | `90_DefendBehaviour_RunToEscapeVan` |
| escape vehicle | van (animated) | helicopter | helicopter | van | van | helicopter | van | helicopter | van |
| `AllyEscapeBox` in the level | . | 8 | . | . | . | 8 | . | 1 | . |

References OUT of the squad (all of them; target side from `kl_prpjoin.sides`):

| reference | F01 | F02 | F03 | F04 | F05 | F06 | F07 | F08 | F09 | target |
|---|---|---|---|---|---|---|---|---|---|---|
| `TriggerLootDepleted[0]` | 68 | 112 | 84 | 70 | 42 | 56 | 35 | 266 | 42 | MAP: loot objects (`OnlineMoneyContainer` case groups in F01 F03 F08; `ZSTDOBJ` / `ZGROUP` with `OnlineMoneyCtrl` + `TriggerBox2` in F02 F05 F06 F07 F09; in F04 groups without a money controller of their own) |
| `TriggerActorsDead[0]` | 94 | . | 35 | 98 | 83 | 147 | 175 | . | . | MAP / layer: the ACTOR GROUPS (`ZGROUP` parents of `ZFFActor`) of police, guards, rival mercs; in F05 F07 also 6 / 35 money objects |
| `DefendBehaviourRout[0]` | . | . | . | . | 7 | . | 7 | . | 7 | MAP: a money object used as the place to hold ("on top of loot") |
| `KickDoorBehaviour_PosInfo[1]` | 7 | . | 28 | . | . | 21 | . | . | . | MAP: the door group (F03: one `KickDoor` box) |
| `KickDoorMonitor[7]`, `RelayMessageList[2]` | 6, 58 | . | . | . | . | . | . | . | . | MAP: glass doors, money cases |
| `ZFFActor[1]` (weapon) | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | SYSTEMS: `AllLevels/mainsceneincludes_multiplayer.zip\AllLevels/equipment.zip\Weapon\Rifle_zastavam85` |

So what the squad names in the kept SYSTEMS part is one weapon template; everything else it names
outside itself is in its own level's map or layer. No squad names a spawn point, a gameplay
trigger, the exit trigger, the escape vehicle, a boarding box or an `AllyEscapeBox`.

## 3. The parts of a squad

### 3.1 The actor (measured on F03 and F07 in full, the fields below on all nine)

`<prefix>!merc_bot_squad!Squad#0N\Glazer_Bodyguard_0N` [`ZGROUP`, placed] `\Ground` [`ZFFActor` at
the group's origin] + `ZSoldier`. Against the level's other actors:

| property | bot | others |
|---|---|---|
| `ZFFActor[0]` team | **`Ally`** (7 of 7 in every level; no other actor has it) | `Enemy`, `Neutral` |
| `ZGEOM[4]` model | **the model number of `Heroes!Hero_0N\Ground`** (63 of 63: same number) | |
| `ZLNKOBJ[2]` animation set | `anmcol:animationdatabase#Lynch_NPC` (N = 2 4 6 8) / `#Kane_NPC` (3 5 7) | the heroes: `#Lynch` / `#Kane` |
| `ZLNKOBJ[1]`, `ZLNKWHANDS[5]` (offsets into the level's .SND) | the values of the level's other actors (F07: 241120, 265616) | |
| `ZLNKWHANDS[0..2]` (voice sets) | 0, 0, 0 | set on police |
| `ZFFActor[1]` weapon | `...equipment.zip\Weapon\Rifle_zastavam85` (63 of 63) | |
| `ZFFActor[2]` | 1 | 0 / 1 |
| `ZFFActor[16]` | `AllLevels/Interface/FACharacters/C2` .. `C8` (N) | `.../Online/Kill/FA_Police` ... |
| `ZSoldier` 0 / 3 | `eThug` / `eCustom` | |
| `ZSoldier` 4 5 6 7 8 | 50 50 50 **280** 50 | 7 = 30..175 |
| `ZSoldier` 15 / 16 / 17 | **1.0 / 600000 / 600000** | 5000 / 800 / 800 |
| `ZSoldier` 19 / 21 / 22 | `No_Mercenary` / `eSR_AllTypes` / 1 | |

The squad is seven squads of ONE actor each; the seven share nothing but `Timer_start_bots`.

Read in kl2.exe:

- `ZSessionHandlerSP` slot 45 (0x8e5650): in Arcade (0x7f6850), `if [[actor+0x54]+4] == 2` it calls
  `ZGameRulesHeist` slot 198. ASSUMPTION that this dword is the team (2 = `Ally` in enum `TEAM`
  0xd06c34: Mercenary 0, Enemy 1, Ally 2; only the bots are `Ally`). Who calls slot 45: not found.
- `ZGameRulesHeist` slot 198 (0x588980): builds a crew record (constructor 0x549030, 0x7c bytes) in
  the table at rules+0x348 (in-use bytes rules+0x34c, capacity rules+0x354), sets record +0x79 bit 0
  ("is an AI actor") and +4 = the actor; character index = `name[0x12] - '1'` of the actor's group
  (`Glazer_Bodyguard_0N`: the digit is at index 18), stored at rules+0x33e and turned into the name
  text `AllLevels/Interface/FACharacters/C1..C9` by 0x478df0 (as `re/characters.md` found).
  **The group name must keep that form.**
- Slot 197 (0x42bc80) registers the human at record 0. The hero the human gets is random 0..7
  (0x835837) and the bot that had that hero is swapped (`re/menus.md` 4; partly decoded).

### 3.2 A route step

A step is a child `ZGROUP` of the squad carrying one behaviour controller; a trigger starts it by
naming the step group (the 'AITrigger' message). Kinds used by bots:

| controller | fields that matter (measured over 1,100 / 56 / 28 / 143 uses) | what it does |
|---|---|---|
| `DefendBehaviourRout` | 0: one place (a child box `Pos#nn`, or a map object) - 603 uses; OR 1: a list of 1..3 child boxes walked in order - 497 uses (never both); 2: 1 (0 in 14); 4: `eDMS_NotSet` 1008 / `eDMS_Sprint` 92; 5: `eDF_NotSet`; 7: list of 0 or 1 NEXT object; 8: 1 | go to the place(s), hold there fighting |
| `KickDoorBehaviourRout` | 0: [next]; 1: 1; child box + `KickDoorBehaviour_PosInfo` {0: the actor GROUP, 1: the door} | kick that door |
| `RunToCoverBehaviourRout` | 0: [next]; child + `RunToCoverPosInfoRout` {5: place} | run to cover at a place |
| `SquadModifierBehaviour` | 0: `eLM_NotSet` / `eLM_Leash`; 9: `eDM_Tight` / `eDM_Loose`; 22: `eSC_Enabled`; 24: 1.0; 26: [next]; 27: 1; every other enum `..._NotSet` | change how the squad fights ("tight defense" on the loot and at the vehicle, "loose" between) |

The controller that walks a step is the squad's `ZSquadScript` through the behaviour goal of the
same name (`ZDefendBehaviourGoal`, `ZKickDoorBehaviourGoal`, `ZRunToCoverBehaviourGoal`,
`ZSquadModBehaviourGoal` exist as `@CPPScript` classes). ASSUMPTION, by the numbering of the names
in all nine levels (010 -> 020 -> ...) and not read in code: the NEXT list is sent when the step is
done (place reached / door kicked / modifier applied).

**The position boxes** are plain `ZBoxPrimitive` children named `Pos#01..` (10 x 10 x 10,
`BOUNDING_Static`, no controller): they are nothing but the places fields 0 / 1 name. 119..329 a
level because each of the seven bots has its own slightly different place per step.

### 3.3 The waits between steps

| controller | fields | read in kl2.exe |
|---|---|---|
| `TriggerDelay2` | 0: seconds (1..20), 1: 0.0, 2: -1.0, 4: [next] | not read (values only) |
| `RandomTrigger` | 0: 1; 1..4: weights (3 / 3 = even, 33 / 33 / 34 ...); 5..8: one target list per weight | not read. Gives each bot a different way: "stair left / middle / right", "threeway_stair_choice" |
| `TriggerActorsDead` | 0: actor GROUPS (2..9); 1: 0; 2: [next] | not read. Names: `WaitForAllNPCDead`, `TriggerActorsDead_Lootarea` |
| `TriggerLootDepleted` | 0: loot objects (5..38); 1: seconds (15, 20, 60; one 0); 2: 0; 3: 0; 4: [next] | slots 13, 25, 26 below |

`ZTriggerLootDepleted` (vtable 0xbcabf4; members +0x38 targets, +0x3c loot list, +0x40 field 1,
+0x44 field 2, +0x49 armed, +0x4a fired, +0x4c deadline):

- slot 26 (0x60f1f0), on the trigger message: arms itself; if field 1 is not 0 the deadline is
  now + (field 1 + random x field 2) x 1024 ticks, i.e. **field 1 is seconds**.
- slot 25 (0x811fb0), every tick while armed (Arcade only: game type 0x19): walks the loot list
  with 0x79f390 - an object counts as empty when its `OnlineMoneyCtrl` says taken (0x4536e0), and
  a group counts as empty when all its children do (recursion over the child list). When ALL are
  empty, **or the deadline has passed**, it sends the trigger message to its targets and stops.
- It never touches an actor. A list entry that is not a money object and has no children counts
  as empty at once.

So "loot depleted" = "leave the loot area when it is empty or after 15..60 s". With field 1 = 0
there is no deadline (F07 has one such squad).

## 4. How a bot takes loot

All read. `ZLootTactic@CPPScript` (soldier tactic):

- slot 11 (0x451920, the test): Arcade only. Finds its crew record (0x78f470: the record whose
  +0x79 bit 0 is set and +4 is this actor). **Record +0x78 must be >= 1**; if it is 3 and the
  escape vehicle's state (rules slot 75, vtable +0x12c) is 3 or 4 it stops looting. Asks rules
  slot 202 for up to five money objects and keeps those the pathfinder (`[[0xdd2640]+0xac]+0xc`,
  virtual +0x7c twice and +0x60) connects to the bot with a path of more than one node.
- `ZGameRulesHeist` slot 202 (0x8b94d0): goes through the rules' own two lists of money objects
  (rules+0xdcc / count +0xdc0, and rules+0xdb8 / count +0xdac), drops the taken ones (0x4536e0)
  and those outside a distance window, sorts by distance to the bot, returns the first five.
  **No list of the level is involved: every registered `OnlineMoneyCtrl` is a candidate.**
- slot 2 (0x7bc7d0, the action): run to the chosen object (0x8997a0).
- Arriving, the bot fires the object's `TriggerBox2`; `ZOnlineMoneyCtrl` slot 26 (0x6cdb40) calls
  `ZGameRulesHeist` slot 201 (0x56f6e0): for an actor that is alive and has a crew record it calls
  0x8e8750(record index, money object): record +0x15 = 1 (looting), +0x1c = the object,
  +0x18 = the object's float +0x44 x a factor of the settings manager (0x4f3e50): the time the
  grab takes. Flag 0x2000 of the bot's status word marks "busy looting".
- **How much**: the object it stands in, one at a time. ASSUMPTION that it gets the object's whole
  amount; the completion (rules virtual +0x198) and any carry limit were not read.

Record +0x78 is the bot's **stage**, raised (never lowered) by 0x5dd890(activator, n), which has
one branch for players and one for actors with a crew record:

| who calls 0x5dd890 | n |
|---|---|
| `ZOnlineGamePlayTrigger` slot 34 (0x8d2740), kind `eOGPT_PLAYER_ENTERS_BANK` | 1 |
| ..., kind `eOGPT_PLAYER_EXITS_BANK` | 2 |
| ..., kind `eOGPT_PLAYER_BOARDS` | 3 |
| `ZOnlineExitLevelTrigger` slot 34 (0x6c3d50) | 3 |

Reset to 0 with the rest of the record at a round start (0x817d20). ASSUMPTION: the trigger boxes
report AI actors as activators (the actor branch of 0x5dd890 would be dead code otherwise; the
boxes' own filter was not read).

Measured: in 9 of 9 levels every squad has route places inside the `OnlineExitLevelTrigger` box; an
ENTERS_BANK box holds a route place of every squad in F01 F03 F04 (thin boxes across a doorway in
the others: crossed, not stood in).

## 5. How and when a bot goes to the vehicle and boards

All read.

**The vehicle's state** is the byte rules+0x1dc, set by `ZGameRulesHeist` slot 194 (0x8fa6d0):
0 none, 1 / 2 called and on its way, 3 / 4 there (boarding open), 5 leaving, 6, 7 reset (the names
are ASSUMPTION from what each branch does). rules+0x1e4 = the vehicle's controller object;
rules+0x1e0 = **the boarding box**: for a baked van `OnlineEscAnimatedVehicle` member +0x40, else
`OnlineEscHavokCar` member +0x38 = its field 2, the box with `PlayerAction` 'EnterVehicle'
(0x8fae92..0x8faecc; `re/maps.md` 14.4 has the member offsets).

1. When the state changes to 1, 2, 5 or 6 (table 0x8fb0a0), slot 194's tail goes through the crew
   records: each AI record that is in play and has **stage >= 3** gets a move order to the boarding
   box's position (the soldier object at actor+0x77c, virtuals +0x1b4 and +0x13c).
2. `ZBoardEscapeVehicleTactic` slot 11 (0x4faf60, the test): Arcade; state 1 / 2: only when the
   rules' countdown (virtual +0x130) is under 2.0; state 3 / 4: needs a boarding position
   (0x5aeb00: rules+0x1e4 and +0x1e0 both set), **stage >= 3**, and a pathfinder path of more than
   one node from the bot to it.
3. slot 2 (0x82f970, the action): runs there (0x8997a0); once within reach calls 0x74d7f0 ->
   `ZGameRulesHeist` slot 45 (0x6840a0): Arcade, state 3 or 4 (or 5 inside a short grace time):
   record +0x10 = 4 (escaped), the actor is taken out of play (0x89c890, actor+0x8f0 = 1), and
   0x4906b0 counts who is still to come.
4. `ZAllyEscapeBox` slot 25 (0x907a50), every tick in Arcade: each AI crew member in play
   (record +0x10 == 0) whose actor is inside the box (0x758cb0) is boarded through the same slot
   45. **No stage test and no path test** - only slot 45's own "the vehicle is there".
   Measured: F02 and F06 have eight (`Escape!EscapeHelicopter_01\Incoming_A..H\
   BoardingTrigger_Heli0n_incoming_X`, about 350 x 416 x 350, created hidden, switched on by
   `ActivateGeom` boxes named `..._activate_only_this_boarding_trigger_02_X`), F08 one; controller
   fields {0: [], 1: 1, 2: 0, 3: 0, 4: 'Activate', 5: 0}. In these three levels every squad's last
   step (`move_to_chopper_X`) has its place inside an `AllyEscapeBox`. F03 (helicopter) has none
   and relies on the tactic.

What the route contributes to boarding: it brings the bot through the exit trigger (stage 3) and
parks it near the vehicle's stop under a `SquadModifierBehaviour` with `eLM_Leash` + `eDM_Tight`
("tight_defense_van / chopper") - the last step of F01 F03 F04 F07.

**Traitor** (`ZBecomeTraitorTactic` slot 11, 0x79b7c0; for whoever does the interactions): a random
draw against thresholds from a table at `[0x168d7c0] + 0x6ac + round x 0x70` (round = the byte
`[rules+0x5f8]+0x45`, clamped 1..11), chosen by the bot's stage, the bot's own money (+0x34 / +0x38 /
+0x3c) and the human's money (+0x50 / +0x54 / +0x58). Record +0x79 bit 1 = is a traitor. The same
object holds the vehicle's phase times (+0x628, +0x62c, +0x630). It is a global KLHook could tune.

## 6. Where the bots stand at the start, how many, their looks

- **Seven bots beside one human**: `Squad#02..#08` = characters C2..C8 (Tommy .. Mitchel), the
  human is record 0. The crew table has eight places (`re/characters.md`).
- A bot is an actor placed in the level, not spawned at a spawn point. Measured against the eight
  `eSPAWN_TYPE_FRAGILE_ALLIANCE_START` points:

| | F01 | F02 | F03 | F04 | F05 | F06 | F07 | F08 | F09 |
|---|---|---|---|---|---|---|---|---|---|
| bot to nearest START point, horizontal | 126..396 | 122..194 | 146..244 | 89..267 | 110..155 | 82..275 | 125..436 | 112..261 | 109..189 |
| START points above the bots' feet | 123..126 | 99..129 | 92..109 | 96..118 | 94..114 | 93..112 | 103..106 | 97..123 (one 15) | 107..137 |
| middle of the bots from the middle of the START points | 96 | 140 | 246 | 204 | 89 | 136 | 321 | 69 | 114 |

  So: the seven stand ON THE GROUND in the same patch as the START row, each 80..440 from the
  nearest point, never on one; a START point floats about 100 above the floor.
- Looks: the model of `Hero_0N` (same model chunk, so a bot costs no model of its own), animation
  set `Kane_NPC` / `Lynch_NPC`, name `FACharacters/C<N>`, rifle `Rifle_zastavam85` for all.
  Mask / outfit: rules slot 34 (0x4b5b20) sets the variant per hero (`re/menus.md`); whether it
  reaches the bots' actors was not read.
- What the round end needs of them: **not established** (the rules' update, slot 7 at 0x74b6d0,
  532 instructions, was not read). Known: boarding sets record +0x10 = 4 and removes the actor; a
  vehicle leaves on its own timer (slot 194), so a bot that never boards does not hold it.

## 7. What the five finished builds already have (measured, `built.py`)

| | M01 | M02 | M03 | M06 | Retomoto (`rt_ai`) |
|---|---|---|---|---|---|
| `Gameplay!AIMonitor` (list 2) | 1 (briefing timer) | 1 | 1 | 1 | 1 (+ 2 rival-van timers); a second monitor from M09_B |
| ENTERS_BANK / EXITS_BANK / BOARDS triggers | 1 / 3 / 1 | 1 / 1 / 1 | 1 / 2 / 1 (BOARDS is 10 x 10 x 10 at the origin) | 1 / 1 / 1 | 1 / 1 / 3 |
| `OnlineExitLevelTrigger` (size) | 2 (1600 x 200 x 880, 2800 x 200 x 1400) | 1 (6000 x 200 x 4000) | 1 (4000 x 400 x 1000) | 1 (3443 x 150 x 2908) | 1 (2700 x 900 x 2250) |
| vehicle form | `OnlineEscHavokCar` | same | same | same (helicopter) | 3 `OnlineEscAnimatedVehicle` |
| `OnlineMoneyCtrl` | 306 | 363 | 340 | 307 | 133 |
| actors by team | Enemy 13, Neutral 3 | 12, 3 | 15, 5 | 14 | Enemy 92 |
| `Heroes!Hero_02..08` models | 9341 9451 9552 9655 9760 9871 9982 | same | same | same | 9599 9709 9812 9921 10031 10142 10254 |
| `Kane_NPC`, `Lynch_NPC` in the .ANM | yes (M01 looked at) | not looked at | not looked at | not looked at | not looked at |
| `...equipment.zip\Weapon\Rifle_zastavam85` | yes | (host part, same) | | | |
| kept actors' `ZLNKOBJ[1]` / `ZLNKWHANDS[5]` (`Hero_02`) | 241120 / 265616 = stock F07's | | | | |
| mesh: START, loot, exit, boarding box on one part (`re/maps.md` 14.5) | yes (371) | yes (859) | **no** (490 + 159) | yes (936) | two halves, joined by the hook for the player only |

## 8. Recipe: the smallest squad for a new map

Stock evidence for "smallest": F08 and F09 run with no `TriggerActorsDead`, no door kicks, no
squad references to actors at all; F03's squad is 50 nodes. Every link below is used by a stock
level; the cut-down COMBINATION is not, and nothing here has run.

### 8.1 Keep from the host (F07), unchanged

- `Gameplay!AIMonitor` (kept today) - add `Gameplay!merc_bot_squad!Timer_start_bots` to its list 2.
- `Gameplay!merc_bot_squad!Timer_start_bots` (`TriggerDelay2` 10.0; field 4 re-written, 8.3).
- For N = 2..8 `Gameplay!merc_bot_squad!Squad#0N` [`ZGROUP` + `ZSquadScript`, all fields as stock]
  and its `Glazer_Bodyguard_0N` \ `Ground` [`ZFFActor` + `ZSoldier`] with every field as stock:
  team, weapon reference (systems, stays valid), animation set, `FACharacters/C<N>`, the two .SND
  offsets (they are the host's and equal those of the kept `Heroes!`), `ZSoldier` values.
  **Names stay exactly `Glazer_Bodyguard_0N`** (3.1).
- `ZGEOM[4]` of each bot must equal the model number of the BUILT level's `Heroes!Hero_0N\Ground`
  (it does in stock; after `kl_chars` / the wardrobe step renumber the heroes it must be re-read
  from them - section 7 shows the numbers moved from 1749.. to 9341..).

### 8.2 Place (7 things, per map)

- The seven `Glazer_Bodyguard_0N` groups (`ZGEOM[2]` of the group; the actor stays at 0,0,0 in
  it; the `.gms` record too, as `kl_escape.place_entities` does for the boarding box): on the
  floor, on the navigation-mesh part of the START row, 100..400 from the START points and at least
  100 from each other, facing the way the heisters face.

### 8.3 The route (per bot: 4 step groups, 2 wait boxes, 4..8 position boxes = 12..16 nodes with
the squad group, actor group and actor)

Clone the node forms from the host's squad (a step group with `DefendBehaviourRout`, a 10 x 10 x 10
`Pos#nn` box, a `ZBoxPrimitive` with `TriggerLootDepleted`, one with `TriggerDelay2`, a step group
with `SquadModifierBehaviour`); only the fields named here change.

| # | node (child of `Squad#0N`) | fields | re-pointed to |
|---|---|---|---|
| - | `Timer_start_bots` field 4 | the seven `Squad#0N\010_...` | own squad |
| 010 | `010_DefendBehaviour_to_loot` + `Pos#01..03` | 1: [Pos#01, Pos#02, Pos#03]; 0: ''; 4: `eDMS_NotSet`; 7: [`020_...`] | boxes PLACED: the way from the start INTO the loot area, at least one of them past the ENTERS_BANK trigger (stage 1), the last one beside the loot. Per bot spread by 100..200 |
| 020 | `020_Timer_done_looting` (`TriggerLootDepleted`) | 0: the map's loot near that place; 1: 20; 4: [`030_...`] | **loot objects of the map**: `OnlineMoneyCtrl` objects or the `OnlineMoneyContainer` groups (5..38 in stock). An empty list fires at once: then use `TriggerDelay2` 20.0 instead - ASSUMPTION that looting during a `DefendBehaviourRout` hold needs no more than the stage |
| 030 | `030_DefendBehaviour_out` + `Pos#01..03` | 1: [..]; 4: `eDMS_Sprint`; 7: [`040_...`] | boxes PLACED: through the EXITS_BANK trigger, then INSIDE the `OnlineExitLevelTrigger` box (stage 3; it also calls the vehicle as a player's entry does - ASSUMPTION, the actor branch of slot 34 past 0x6c3da3 was not read to the end), the last one 150..400 from the boarding box, on the mesh |
| 040 | `040_SquadModifier_tight_defense_van` | 0: `eLM_Leash`; 9: `eDM_Tight`; 26: [] | - |

From there `ZBoardEscapeVehicleTactic` takes the bot to the boarding box when the vehicle is there.
No `TriggerActorsDead` (optional by F08 / F09). If the bots should wait for the guards as in F01 /
F07: one `TriggerActorsDead` {0: the map's guard ACTOR GROUPS (the `ZGROUP` parents of the
`ZFFActor`s, never the actors), 2: [next]} between 010 and 020.

Everything else of the host's squad (its other 20-odd steps, 9 `RandomTrigger`, 4
`TriggerActorsDead` per bot) is dropped. If dropping nodes inside a kept subtree is awkward in
`kl_graft`, keeping them is harmless only if nothing names them and their references into F07's
map are cut (`kl_fa.prune` does that): a `TriggerActorsDead` or `TriggerLootDepleted` left with an
empty list but never triggered does nothing (it arms on a message only: 0x60f1f0).

### 8.4 Per map

| map | besides 8.1 - 8.3 |
|---|---|
| M01, M02, M06 | nothing known. M01 has two exit triggers and three EXITS boxes: pick one way. M06's vehicle is a helicopter: add one `AllyEscapeBox` (350 x 416 x 350 as F02's) at the boarding place as F02 F06 F08 do, with the last route place inside it |
| M03 | the bot's mesh part (490 polygons) does not contain the boarding box (part of 159): the board tactic's path test fails. Either join the two parts in the mesh where `kl_escape` opened the wall, or put an `AllyEscapeBox` on the bots' side of the wall with their last place inside it (boards without a path; the bots then "vanish into the van" at the wall). Its BOARDS trigger is a 10-box at the origin, so stage 3 must come from the exit trigger (4000 x 400 x 1000) - which is on the far part too. With an `AllyEscapeBox` no stage is needed |
| Retomoto | the two halves are separate mesh parts and the join is a jump the hook does for the human. Bots cannot follow. Cheapest: bots loot the tower and end in an `AllyEscapeBox` at the tower car's floor (the join box); they board when the van is "there" (state 3 / 4), which the human causes in the street. Not designed further here |

### 8.5 Checks an implementer can code (all offline)

1. exactly 7 `ZFFActor` with team `Ally`, their groups named `Glazer_Bodyguard_02..08`, each in a
   `ZSquadScript` group with field 1 = `eHeistOnly`.
2. each bot's `ZGEOM[4]` == `Heroes!Hero_0N\Ground`'s; `ZLNKOBJ[2]` set present in the .ANM.
3. `AIMonitor[2]` names `Timer_start_bots`; `Timer_start_bots[4]` names 7 existing steps; every
   NEXT list resolves; no reference out of the squad dangles.
4. every placed box and every bot is on the mesh part of the START row (`kl_maps.NavParts.at`).
5. per squad: some route place inside an ENTERS_BANK box, some inside the exit trigger or a BOARDS
   box (half extents = the box's three size values), or the last place inside an `AllyEscapeBox`.
6. the boarding box (`OnlineEscHavokCar[2]`; for a baked van `OnlineEscAnimatedVehicle[0]` -
   ASSUMPTION that field 0 is member +0x40) is on the same mesh
   part as the last route place, unless an `AllyEscapeBox` is used.
7. `kl_fa.check` then reports 7 bot squads (it counts `TriggerLootDepleted`).

## 9. Budget

Nothing was built. Per build, as measured on the finished folders: `.prm` / `.ANM` / `.fxc` MB =
M01 55.1 / 22.1 / 17.8, M02 54.6 / 22.2 / 17.8, M03 60.5 / 22.2 / 17.8, M06 49.6 / 21.6 / 17.8,
Retomoto `rt_ai` 79.3 / 21.6 / 17.8; `.WAV` beside the archive as `re/maps.md` 14.1 lists it
(21.7 .. 22.7 MB). A squad after this recipe adds **no model** (the bots use `Hero_02..08`'s
chunks), **no animation** (the two NPC sets are the host's and are in the joined .ANM: seen in
M01's), **no sound and no shader**; it adds about 110 entities and 7 actors to the scene. Chunk
table entries: none.

## 10. Not established, and how this was produced

- Nothing here ran. The cut-down route is a combination no stock level has.
- Whether gameplay trigger boxes report AI actors (4); who calls `ZSessionHandlerSP` slot 45; the
  NEXT list's exact "done" condition (3.2); `TriggerDelay2`, `RandomTrigger`, `TriggerActorsDead`
  in code; how much a bot carries and what ends its grab; what a dead bot does (respawn, lives);
  what the round end needs of the bots; whether the mask / outfit variant reaches bots.
- Whether a bot boards a Dead Men spline car as it boards a stock helicopter: the code path is the
  same `OnlineEscHavokCar` branch (0x8faebc), the vehicle state machine for it was not followed.

Scripts (scratchpad `...\1e45a579-...\scratchpad\bs\`): `lib.py` (loader on `kl_fa.load` +
`kl_scene` + `kl_maps.world`), `tops.py`, `dump.py <level> <name part>` (a subtree with every
field), `actor.py`, `census.py` (section 2), `route.py` (places inside trigger boxes), `last.py`
(section 6), `built.py` (section 7), `misc.py` (field statistics); exe: `fn.py <address>` (a whole
function with strings), `vtdiff.py`, `callers.py`, `scan.py`, `wr*.py` (writers of the crew record).
