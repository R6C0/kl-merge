# The converter against the faults another porter found (2026-10-11, track C)

OFFLINE. Nothing was launched, nothing written into either game folder, no map on the tab rebuilt, nothing
committed. Read: `kaneandlynch.exe`, `kl2.exe`, the 20 + 21 stock levels, the six Dead Men source levels
(`M01_FA_A`, `M02_FA_A`, `M03_FA_A`, `M06_FA_A`, `M09_A`, `M09_B`) and the five builds on the tab
(`<work>\build\z_route3\M01`, `z_m02s1\M02`, `z_hop\M03`, `z_route\M06`, `rt_full7\retomoto_full` - the tab as it
stood when the audit began; 'the five builds' means these throughout. The tree in the game folder has moved on
since - section 7 - and every statement about the five was counted again on the builds it holds now).
Addresses are virtual addresses; `DM` = Dead Men, `DD` = Dog Days; a field number is the index within the
class level (the format of `kl_convert.LEVEL_MAPS`). NOTHING BELOW HAS RUN IN THE GAME.

The other porter's four faults, in one line each for OUR converter:

| | their fault | ours |
|---|---|---|
| 1 | trigger settings silently swapped | **FAULT, two places** - the same kind, found in `ZTriggerBox` (one bool) and in `ZSquadScript` (8 of its 12 event lists). Corrected in `kl_convert.py`. |
| 2 | grenade types mixed up | **CLEAN** - the rename table is exact, and no item enum of Dead Men reaches a build at all. |
| 3 | cars always blow up | **CLEAN** - the six values Dog Days added to the vehicle block are 1.0 / Dog Days' own; 'Definite' is Dead Men's own setting (and stock Dog Days'). |
| 4 | Dead Men numbers in the four new soldier values, one 0 | **CLEAN** - the four are 1.0 in the converter and in all 181 soldier rows of the five builds. (That exact fault WAS ours until the pairings fix of 2026-10-09.) |
| 5 | (unproven pairings) | three more settled by code (one of them wrong: `ZFFActor`), list in section 5. |
| 6 | (enum names) | **FAULT, small** - two renamed options fell to a default; one more class of 'same name, other meaning' found (Kane / Lynch). |

REVIEWED 2026-10-11 (`re/convert_audit_review.md`: every pairing re-derived, accepted with fixes). What the
review changed in THIS text: section 9 is new (what the corrections change IN PLAY - on the five tab builds the
moment at most, never a target - and why a live run cannot prove a pairing); the 'effect today' passage of 1.2,
the roll-out paragraph of 7 and the `ZFFActor` row of 5 are rewritten; the trigger table, the list of Dog
Days-only fields and the vehicle list are completed. A fault of the pairing is a fault of the converter whether
or not a map shows it: the verdicts above stand.

## 0. How a level stores an enum, and why a number cannot slip through

- Token `0e` + a 4-byte KEY INDEX (`tools/kl_prp.py`). The reader is `ZPackedInput` vtable slot 15: DD
  0x88c9f0, DM 0x451060, the same function. It has three paths by the stream's flag word `[reader+4]`: bit 2
  clear = four raw bytes (a number); bits 2 + 3 = key index -> string from the key table -> name look-up; bit 2
  only = an inline string -> name look-up. The flag word is the .prp header dword at 0x0f: **13 in all 20 DM
  levels, all 21 DD levels and all 5 builds** = bits 0, 2, 3 = the key-table path.
- The look-up (DD 0x847060, DM 0x4507a0) walks the `ZEnumInfo` entries `{next, value, name}` with a
  case-sensitive compare and returns the entry's value. **A name the enum does not have returns the default
  argument, 0 - no assert.** So an unknown name is silently the option numbered 0.
- `kl_convert.Converter.value` passes a 0e token on only if the name is an option of the Dog Days enum of the
  field it was paired with; otherwise `ENUM_RENAME` (new) or Dog Days' most common value. `verify_levels` checks
  every enum and flag name of the output. Two fields are paired only when their enum NAMES are equal
  (`label()`), except where `LEVEL_MAPS` says otherwise (checked: every `LEVEL_MAPS` pair has equal labels).
- 15 enums have a same-named option with ANOTHER NUMBER in the two exes (`ESoldierStyle` eGuard 2 -> 3,
  eSwatWithShield 3 -> 5; `ESPAWN_TYPE` START 4 -> 1, AFTER_DEATH 8 -> 2, TRAITOR 16 -> 4; `EIsMercenary`
  Merc_n +1; `ECOLLISIONTYPE` COLLIDE_NONE 2 -> 3; `EFMMode`; `EDefendMoveSet`; `EPatrolMoveset`;
  `EFollowModifier` Tight / Loose swapped; `ECoopPlayerSetting`, `EPlayerFilter`, `EFlashBackPlayer` Kane /
  Lynch swapped; `EHeliBoneType`; `WEAPONTYPE`; `eFF2Item`). All harmless as numbers because the name is what
  is stored. 107 enums are identical. (`enums.py` in the scratchpad prints the list.)
- Ints that might be enums in disguise, in the trigger classes: `ZTriggerBox[2]` (a count, 1), `[9]` (-1 or
  1 / 5 / 10), `ZTriggerDelay[0..2]`, `ZTriggerCounter[0..1]`, `ZTriggerBox2[6]`, `ZOnlineTriggerBox[5]`: counts
  and times by their values and readers. Raw blocks: only `ZROOM[6]` on the map side, and the converter DROPS
  it ('raw -> cont', 46 rooms): no enum inside survives. Not searched: enums inside the `.gms` raw data blocks.

## 1. Triggers - FAULT (two)

Every trigger-like controller of the six levels' map side (objects per level M01 / M02 / M03 / M06 / M09_A /
M09_B) and its layout in the two exes:

| controller | objects | layout DM -> DD | verdict |
|---|---|---|---|
| `TriggerBox2` (money) | 307 / 366 / 363 / 307 / 0 / 0 | 7 fields, identical types and offsets | CLEAN |
| `TriggerBox` | 8 / 2 / 13 / 3 / 26 / 35 | 14 -> 18: one bool among the seven event bools, a string, a bool, `EFAModePlayerSetting` | **FAULT** (1.1) |
| `ZSquadScript` | 16 / 10 / 15 / 11 / 43 / 57 | 17 -> 21: `EGameType`, three event lists | **FAULT** (1.2) |
| `TriggerDelay` | 3 / 2 / 5 / 6 / 46 / 52 | 4 -> 5: one bool, the only one | CLEAN |
| `TriggerCounter` | 0 / 1 / 1 / 3 / 7 / 17 | 4 -> 5: a second bool. DM bool `[x+0x44]` and DD `[x+0x44]` are read at the same place of slot 13 and slot 26 (DM 0x6a0843, 0x6a09f7; DD 0x6fcfb3, 0x541267); DD `[x+0x45]` is new (0x6fcff8) | CLEAN, was 'assumed' |
| `OnlineTriggerBox` | 1 / 2 / 4 / 0 | 6 fields, identical | CLEAN |
| `OnlineGamePlayTrigger` | 5 / 3 / 4 / 3 | 2 fields, identical; `EOGPTEvent` identical in both exes | CLEAN |
| `OnlineExitLevelTrigger` | 2 / 1 / 1 / 1 | 1 -> 6; DM0 -> DD2 (`LEVEL_MAPS`, by values; kl2 0x6c3d50 reads fields 2..5 as the vehicles, re/map_ai.md 5) | CLEAN |
| `OnlineEscCamTrigger` | 2 / 1 / 1 / 1 | 1 -> 2; DM0 -> DD1 by values | not read in code |
| `CheckInsideByType` | 1 / 0 / 0 / 0 / 0 / 1 | own level identical; base `CCheckInside` 10 -> 11: six bools at +0x38..+0x3d in both, the seventh at +0x3e (padding in DM) | by offsets; no reader found |
| `RelayMessage`, `RelayMessageList`, `MsgForward`, `LevelBound`, `NoCoverBox`, `GateGroup`, `GatePath`, `PathBlocker`, `AIDWrapper` | | identical | CLEAN |
| `CoverStateChanger` | 0 / 0 / 45 / 0 / 6 / 4 | 0 -> 6 fields (three `ETRIGGERTYPE`, bool, list, `EFILTER`) | CLEAN: DM hard-codes 'Activate' -> covers on (0x6b7db0, flag 1), 'Deactivate' -> off (0x6b7e20, flag 0); DD reads the action per message from fields 1 / 2 (0x62d745, 0x62d751) and the usual value we write is ActivateCovers / DeactivateCovers. Field 0 (on 'AITrigger', which DM does not handle) is ActivateCovers too: a difference, nothing sends it on these maps |
| `ShotActivate`, `SmashActivate`, `DeactivateGeom`, `ActivateGeom`, `OnlineSpeakTrigger`, `OnlineMoneyCtrl` | | fields appended behind another type | CLEAN (no same-typed neighbour) |
| behaviour routs (`Defend`, `Flanking`, `Hunt`, `Patrol`, `IdleWalkPath`, `MiniCutscene`, `Warn`, `SquadModifier`) | | base class: DM bool +0x32, DD +0x3e and a new +0x3f | CLEAN, was 'assumed': slot 26 tests DM `[x+0x36]` at 0x6ecf11 and DD `[x+0x42]` at 0x4ebf01, the same instruction of the same function; DD `[x+0x43]` is new (0x79112f) |
| `Filter` | 0 / 0 / 0 / 0 / 11 / 9 | 2 fields, identical | not in a build |
| `CoopGate` | 0 / 0 / 0 / 0 / 4 / 4 | 4 fields, identical | not in a build |
| `KaneLynchBox` | M09_B 2 | 6 fields, identical (a Kane / Lynch class: section 6) | not in a build |
| `Blocker`, `EndOfLevelTrigger`, `TriggerPsychoMode`, `SetPsychoModeDuration`, `SceneChanger`, `RappellingBox`, `RappelCheckPoint`, `AlteredVisionArea`, `WoundedFilter`, `ZMercSquad`, `ZFusionSquad` | M09_A / M09_B only (2 / 7, 1 / 1, 0 / 1, 1 / 3, 1 / 1, 1 / 0, 1 / 0, 0 / 1, 0 / 1, 8 / 4, 2 / 2) | identical | not in a build |
| `Action` | 0 / 0 / 0 / 4 / 1 / 0 | 11 fields, identical | 4 in the M06 build; no pairing to get wrong |
| `CCameraBox` | 3 / 2 / 2 / 3 / 14 / 0 | 17 fields, identical | 7 in the four Fragile Alliance builds; no Kane / Lynch option left on them (section 6) |
| `AIMonitor`, `Elevator` | M09_A 1 + 1, M09_B 2 + 0 | identical | 1 + 1 in the Retomoto build |
| `JumpPoint` | 0 / 0 / 0 / 0 / 6 / 2 | 0 -> 1 field (a reference list) | not in a build (the jump is the hook's, CLAUDE.md); the new list comes out empty, NOT read |
| `CheckPointSave` | 0 / 0 / 0 / 0 / 3 / 2 | 5 -> 7: two fields of a type Dead Men's level has none of, between the list and the last string | not in a build; no same-typed neighbour; the two new fields NOT read |
| `LookActivate` | M09_A 1 | 8 -> 10: a bool and a float before the list (`b f f f f s refs b` -> `b f f f f s b f refs b`) | not in a build; paired by ORDER (Dead Men's last bool -> the last): an ASSUMPTION, NOT read |
| `PsychoticController` | 0 / 0 / 0 / 0 / 3 / 4 | 4 -> 4, the last field (flags `EPsyType`) has another type handler in Dog Days | not in a build; NOT read |

The last eleven rows are the review's note 3, counted again here (`f7_census.py`: every controller name on the map
side of the six levels with its layout in both exes, and how many sit on a node of a build that is not a stock
F07 path). They matter for a CAMPAIGN port, not for a build of ours.

Is 'fires when everyone inside is dead' against 'fires when somebody enters' an enum, a bool or a class? In
both games it is a BOOL of `ZTriggerBox` per actor kind and direction (below); `ETrackGeomSetting` (eTGS_AllInside
/ AllOutside / AllDead, identical tables; all 87 boxes of the six levels are AllInside) only says how a tracked
object counts. And for squads it is which of the EVENT LISTS a reference stands in (1.2).

### 1.1 `ZTriggerBox`: the new bool is field 8, not field 7

A property record's offset is relative to `this - 4` of the controller's virtual functions.

| event (the box sends its lists when ...) | DM field, byte | DD field, byte |
|---|---|---|
| a player enters (count >= field 2) | 1, `[x+0x3d]` | 1, `[x+0x41]` |
| the players have left | 3, `[x+0x44]` | 3, `[x+0x48]` |
| an actor of team Mercenary (0) enters | 4, `[x+0x45]` | 4, `[x+0x49]` |
| the last Mercenary actor has left | 5, `[x+0x46]` | 5, `[x+0x4a]` |
| an actor of team Ally (2) enters | 6, `[x+0x47]` | 6, `[x+0x4b]` |
| any other actor (Enemy, Neutral ...) enters | **7**, `[x+0x48]` | **7**, `[x+0x4c]` |
| the last of those others has left | - | **8**, `[x+0x4d]` NEW |
| an EnemyVehicle (12) enters | **8**, `[x+0x49]` | **9**, `[x+0x4e]` |

Evidence: the update (vtable slot 25, DM 0x69fff0, DD 0x42afd0) builds five flags per pass from the actors in
the box - a player, team 0, team 2, team 12, other - compares each with the state of the last pass and tests one
bool for 'now true' and, where there is one, a second for 'now false': DM 0x6a0179 / 0x6a0191, 0x6a01a7 /
0x6a01bf, 0x6a01d5, 0x6a01eb, 0x6a0201; DD 0x42b381 / 0x42b394, 0x42b3aa / 0x42b3bd, 0x42b3d3, 0x42b3e9 /
**0x42b3fc**, 0x42b412. The 'other' group has ONE test in DM (enter) and TWO in DD (enter 0x42b3e9, leave
0x42b3fc). The init (slot 13) agrees: DM 0x69f4b7 puts bools 1, 3, 4, 5 on mask bit 1, bool 6 on 4, bool 7 on 2,
bool 8 on 0x1000; DD 0x49e583 puts 1, 3, 4, 5 on 1, 6 on 4, **7 and 8 together** on 0x12, 9 on 0x1000. The names
agree too: DM field 7 is set on `EnemyApproachesDaughter`, `TB_See_Guard_Die`, `TriggerBox_SWAT2`; DM field 8 on
`TriggerBox_GetAwayVan`, `Truck_Barricade01`, 22 `TriggerBox_Bomb_...`, `TriggerBox_LastCar`; DD field 7 on
`TB_GoonKicker`, `TriggerBox_Evade`; DD field 8 on nothing in 1,880 stock boxes.

- Until 2026-10-09 (difflib): DD7 <- DM7 (right), DD8 <- DM8 (a vehicle entering became 'the others have left').
- 2026-10-09 .. 11 (`re/pairings.md`, 'the extra je + call is DD byte +0x4c'): DD8 <- DM7, DD9 <- DM8. **'Somebody
  walks in' became 'everybody in here has left'** - the other porter's fault 1, mirrored. The reading took the
  changed code shape of the 'enter' test for the new member; the new member is the 'leave' test behind it.
- Now: `{7: 7, 9: 8}`, DD8 = Dog Days' usual value (0).

Objects it changes: **1** in the six levels - `M06_FA_A ROOT\Triggers!JPN_Boss_Start_WalkTo_USBoss` (fields 7,
8 = 0, 1 in the build `z_route\M06`; right is 1, 0). Both lists of that box are empty in Dead Men's own file and
nothing names it, so it does nothing either way. For a campaign conversion it is 101 boxes of the game: field 7
on 66 (M05_A 60, M13_A 3, M07_A 1, M08_A 1, this one), field 8 on 35 (M13_B 29, M07_A 4, M03_A 2).

### 1.2 `ZSquadScript`: which Dog Days list each Dead Men event list is

Dead Men has 12 lists (fields 3..14), Dog Days 15 (fields 4..18). `kl_convert.SQUAD_LISTS[k]` = the Dog Days
list of Dead Men list k.

| Dead Men list (field) | event | Dog Days list (field) | was | evidence |
|---|---|---|---|---|
| 0 (3) | the first member is dead (alive <= n - 1) | 0 (4) | 0 | update DM 0x6ee110 `[x+0x58]`, DD 0x47e440 -> 0x51c8e0 `[x+0x5c]` |
| - | EVERY death (a loop over the members lost since the last pass) | **1 (5) NEW** | | DD 0x47e47d..0x47e4bb `[x+0x78]` |
| 1 (4) | half the squad is dead (alive <= n / 2) | **2 (6)** | 1 | DM 0x6ee17f `[x+0x74]`, DD 0x649d30 `[x+0x94]` |
| 2 (5) | one member is left | **3 (7)** | 2 | DM 0x6ee1ad `[x+0x90]`, DD 0x86b470 `[x+0xb0]` |
| 3 (6) | nobody is left: wiped out | 4 (8) | 4 | DM 0x6ee1e0 `[x+0xac]`, DD 0x87ebf0 `[x+0xcc]` |
| - | sent from `CPPScript::ZIdleWalkGoal` slot 2 (0x4fc7e0, call 0x4fc859 -> helper 0x56d0b0); the condition was not read; no stock squad uses it | **5 (9) NEW** | | |
| 4 (7) | a member notices something (awareness result != 0) | 6 (10) | 6 | the same code calls both helpers: DM 0x72835d, DD 0x4881cf |
| 5 (8) | a member sees a hostile | 7 (11) | 7 | DM 0x728382, DD 0x4881f6 (next statement of the same function) |
| - | **a PLAYER starts close combat on a member** (READ after the review): helper 0x42dfa0 (`[squad+0x170]`) is called from 0x76eab0 for the squad of the actor passed in; 0x76eab0 is a routine of `ZFFActionCloseCombat` (the action the player's slot 225 creates for action number 0x21: 0x839c28 -> constructor 0x597550, vtable 0xbb4e98), called with the player's target `[player+0xd38]` from 0x612c20 (called by `ZFFPlayer` slot 87, 0x57fae0) and from 0x75e720, where the target arrives as a 16-bit reference (taken to be the same action started over the network). Which close-combat move it is (the state it sets is 3) was not followed; in Dog Days close combat on an enemy is the grab that makes a human shield. The six stock squads that use it fit (L03 `...Squad_Patrol\Gate_HS\Way#01`, L06 `Squad_CIV\Alert`, L10 three) | **8 (12) NEW** | | |
| 6 (9) | a member is attacked | **9 (13)** | 8 | DM 0x72493f + 0x725526, DD 0x5a82b3 + 0x8474df: identical callers (attacker stored, time + 0x2000; damage record type 1) |
| 7 (10) | not read | **10 (14)** | 9 | by order between 6 and 8, and by the save order below |
| 8 (11) | the message `VehicleDead` | **11 (15)** | 10 | controller's message handler DM 0x6edf90, DD 0x8a9a60 (message ids resolved to names) |
| 9 (12) | the message `DriverDead` | **12 (16)** | 11 | the same handlers |
| 10 (13) | not read | **13 (17)** | 12 | by order between 9 and 11, and by the save order |
| 11 (14) | sent once from DM 0x6f5021 / DD 0x7dbee1 (identical code, after a pass over the members with message 0x37) | **14 (18)** | 13 | the two callers |

The squad object (`CPPScript::ZSquad`, created in slot 13: DM 0x6eec20 -> 0x6ee300, DD 0x6316b0 -> 0x7696f0)
gets lists 4..11 (DM) / 5..14 (DD) as pointers at +0x154.. / +0x164.. and one 'sent' byte each at +0x149.. /
+0x159... Its save routine writes those bytes in this order: DM 0x6ede10: lists 4, 5, 7, 10, 6, 8, 9, 11; DD
0x44a1e0: lists 5, 6, 7, 8, 10, 13, 9, 11, 12, 14. Take the new 5 and 8 out of Dog Days' order and it is Dead
Men's order under the pairing above (6, 7, 10, 13, 9, 11, 12, 14) - that is the proof for lists 7 and 10, which
have no reader of their own in what was read.

So **eight of the twelve lists were paired with another event** since the first converter ('carried over from a
comparison of level values'): half dead -> every death, one left -> half dead, attacked -> list 8 (a player's
close combat, read after the review), and lists 7..11 one too low. `SQUAD_LISTS` is now `[0, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14]`.

Use of the lists: Dead Men (755 squads, 20 levels) 0: 39, 1: 22, 2: 6, 3: 132, 4: 69, 5: 33, 6: 57, 7: 3, 8: 6,
9: 46, 10: 0, 11: 2 squads; stock Dog Days (992 squads) 0: 46, 1: 191, 2: 18, 3: 36, 4: 461, 5: 0, 6: 68, 7: 19,
8: 6, 9: 104, 10: 1 (L04 `SQ_Sniper2`), 11: 1, 12 / 13 / 14: 0.
(Dead Men's 57 'attacked' lists against Dog Days' 6 in list 8 and 104 in list 9 fits the correction.)

The senders, all of them (after the review; `fdis.py dd callers 0x79d6d0`): lists 0..4 are members of the
controller (+0x5c, +0x78, +0x94, +0xb0, +0xcc, 0x1c apart) and go out through 0x77b820 (ecx = the controller,
argument = the list's address); lists 5..14 belong to the squad object (pointers at +0x164..+0x188) and go out
through 0x79d6d0 (ecx = the squad, argument = the list pointer) from nine places: 0x56d0b0 list 5, 0x6831f0 list 6,
0x720e70 list 7, 0x42dfa0 list 8, 0x7cc4a0 list 9, 0x6fd630 list 10 (called from 0x8e5600, an actor routine with
a 0x400-tick throttle: event not read), 0x75d370 list 11 and 0x6fc120 list 12 (both from the controller's message
handler 0x8a9a60), 0x551ab0 list 14 (from `CPPScript::ZWarnBehaviour` slot 2, 0x7dbee1). **List 13 has no sender
through that helper** - none was found for it. The network replay 0x6174f0 maps the numbers 5..10 to the same six
helpers in order (jump table 0x617544, decoded), and each helper hands its own number to the network call
(0x56d0b0 `push 5` .. 0x7cc4a0 `push 9`, 0x6fd630 `push 0xa`): a second, independent proof that 'attacked' is
list 9 and the close-combat event list 8.

WHO sends 'a member is attacked' - not the same in the two games:

| | Dead Men | Dog Days |
|---|---|---|
| the sender | 0x6edcd0 (`[squad+0x15c]`, once: byte +0x14b) | 0x7cc4a0 (`[squad+0x174]`, once: byte +0x15d; skipped when 0x4b0a40 says yes - the same test that makes the squad update replay events received over the network instead of sending its own, so: a client) |
| a SOLDIER | `CPPScript::ZSoldier` slot 75 (0x7247d0, call 0x72493f) on script event 0x1d (handler slot 1, 0x724fb0 -> virtual +0x12c), and slot 59 (0x7253f0, call 0x725526) | slot 105 (0x5a8140, call 0x5a82b3) on the same event 0x1d (handler 0x608050 -> virtual +0x1a4), and slot 96 (0x8473a0, call 0x8474df). 0x5a8140 first tests the attacker's team bit against a mask of the member's own team record (`[team+0xc]`, 0x5a8166..0x5a8180; taken to be 'hostile to', the mask itself was not followed): without the bit nothing is sent |
| a CIVILIAN | **never**: its handler of event 0x1d (slot 1, 0x7116f0, case 0x711718) only runs the flee routine 0x710f00; 0x6edcd0 has no other caller and no inlined copy (the only place that tests +0x14b and reads +0x15c is 0x6edcd3) | **yes**: its handler of event 0x1d (slot 1, 0x7b48f0, case 0x7b4918) calls 0x582fb0, which begins `mov ecx, [this+0x4f8]` (the squad) `; push 0; call 0x7cc4a0` - with NO test of who attacked |

So a Dead Men squad of civilians with an 'attacked' list (M01_FA_A has three: `Civilians!LeavingWoman`, `Waitress`,
`LeavingMan`) carries wiring that never fired in Dead Men and, paired right, can fire in Dog Days. The review
expected the opposite ('may never be sent, in either game'): it had not read the third caller, 0x582fc2.

Objects it changes, per level (Dead Men squads that have entries in a list whose pairing changed):

| level | squads | which |
|---|---:|---|
| M01_FA_A | 6 | 'attacked' (13 entries): `AI_Enemies!CheckFront`, `AI_Enemies!KitchenBoy`, `Civilians!LeavingWoman`, `Civilians!Waitress`, `Civilians!LeavingMan`, `Civilians!GangMembers` |
| M02_FA_A | 1 | 'attacked' (2): `AIEnemies!3rdFloor_Guard_01` |
| M03_FA_A | 0 | (its squads use lists 0 and 5 only) |
| M06_FA_A | 8 | 'attacked' (1 each): `AI_Enemies!US_DrugSquad_Secure_Boss`, `JPN_Boss`, `JPN_DrugSquad_Bridge_01`, `JPN_DrugSquad_Island_01`, `US_Boss`, `US_DrugSquad_Bridge_01`, `US_DrugSquad_Bridge_02`, `US_DrugSquad_Island_01` |
| M09_A | 2 | `010_Roof!01_Squad_Helipad` 'half dead' (was in 'every death'), `040_Atrium_3rd!Squad_AtrTop_Reception` 'attacked' |
| M09_B | 9 | 5 'attacked', 3 'one left' (were in 'half dead'), 1 list 7 |

In the builds on the tab the misplaced lists are still there (`python tools\kl_map_ai.py pairfix <build>` lists
them): M01 6 squads (21 entries with what later steps added), M02 1, M03 0, M06 8, Retomoto 2
(`Squad_AtrTop_Reception` 'attacked', `010_RetoBldFront!Squad_InFront` 'one left').

Effect today (REWRITTEN after the review, which was right that the first text overstated it; the squad-by-squad
account is section 9): Dead Men's 'attacked' wiring sits in Dog Days list 8 and is sent when a PLAYER starts
close combat on a member of the squad - not 'never'. And what that wiring starts is started anyway: on every one
of the five builds each target of a misplaced list is also named by a list that was always paired right - the
same squad's 'a hostile is seen' (M01 `CheckFront`, `KitchenBoy`; M02; five of M06's eight squads) or 'something
is noticed' list (Retomoto `Squad_AtrTop_Reception`), or another object (M06: the two 'under fire' counters count
to 1 and name each other, and seven of the eight squads have the US one in 'a hostile is seen'; M01: the gang's
timer and `FrontMall_01`'s flank are in `CheckFront`'s and `KitchenBoy`'s 'a hostile is seen', the timer also in
the box `Triggers!EnterDiner`). So the gangs' timers on M06 and the diner's chain on M01 DO start in the builds
that ran - at the first hostile seen instead of at the first hit. 33 entries are misplaced on the five builds;
18 are doubles of a right list of the same squad, the other 15 are named by another object, none by nothing else.
`SQUAD_DEAD = 8` of `kl_map_ai` / `kl_fa_author` / `kl_fa_street` / `kl_fa_fed` (Dog Days list 4)
is the wiped-out list - that ASSUMPTION is now read (it agrees with kl_fa_fed's note).

## 2. Grenades and items - CLEAN

- `kl_convert.ITEM_RENAME` against the templates each item is BOUND to in the two games' own levels
  (`InventoryBinding`, Dead Men M01_FA_A / Dog Days F07): Frag <- `Grenade_Fragmentation` in both, Gas <-
  `Grenade_TearGas` in both, Incendiary <- `Grenade_Incendiary`, Smoke <- `Grenade_Smoke`, GrenadeLauncher_Gas <-
  `Launcher_HK69A1_01TearGas`, _Flare <- `Launcher_HK69A1_01Flare`, RocketLauncher_Hind <- `RPG_7V_Hind`,
  `eFF2ItemGrenadeLauncher` <- `Launcher_HK69A1_01` and `eFF2ItemRocketLauncher` <- `RPG_7V` (those two names did
  not change). Dog Days kept Dead Men's order (Smoke, Gas, Frag, Incendiary = 29..32 / 55..58) and put an
  underscore in. No grenade or launcher kind is crossed. The gun renames (USP -> SigSauer226 ...) are stand-ins
  by class, as the table says; C4, Claymore, Pushblade, the inaccurate launcher -> NoItem.
- It does not matter for the builds: the graft drops Dead Men's systems subtree (item templates, bindings,
  weapon packs). All five builds have exactly stock F07's 65 item names in the key table, none of Dead Men's,
  and **no `eFF2Item` enum on any node that is not on a stock F07 path**. The table (and the `ZItemTemplateWeapon`
  / `ZItemTemplateAmmo` / `ZInventoryBinding` / `CExplode` pairings re/pairings.md calls high risk) only act in
  a whole-level conversion (`verify_levels`): 0 objects of those classes from Dead Men are in a build, except 2
  `Explode` controllers on Retomoto (`CExplode`: paired by the three legacy projectiles both games ship,
  re/pairings.md 'high' - not re-read here).
- What an NPC holds: Dead Men `ZFFActor` field 1 weapon, 3 second weapon, 4 / 5 grenades. In the sources only
  M09 has any of 3..5: 7 police with `Launcher_HK69A1_01TearGas`, 3 with `Grenade_TearGas` as second weapon, the
  mercenaries with frag / smoke / incendiary / gas. In the builds EVERY Dead Men actor has fields 3, 4, 5 empty
  (`kl_arms`), except one Retomoto machine-gunner with a pistol as second weapon. So nothing is crossed, and
  M09_B's tear-gas police have no gas (kl_arms' choice; the template names are the same in both games, so they
  could be carried by name).
- Pickups (`ZFFItemWeapon`): M06 has four - `RPG_7V` x 3 (the same template name in Dog Days, kept) and
  `Mg_Minimi_SPW_01` -> `MG_GP_Type88` (a machine gun for a machine gun). M09_A's one is not in the build.

## 3. Vehicles that blow up - CLEAN

`ZVehicleEffects`, DM 35 -> DD 42 fields: six floats more in the first run, one more in the second. Every
pairing is now read in the code (the two that `LEVEL_MAPS` called guesses included); code offset = record + 4.

| DM | DD | what | reader DM | reader DD |
|---|---|---|---|---|
| 0, 1 | 0, 1 | | 0x689780, 0x68978f (x3) | 0x61c910, 0x61c91f (x3): the same function |
| 3 | 3 | **the vehicle's health** | init 0x688e01: `[v+0x5ec] = field 3` | init 0x42d6e0 |
| - | 4 | health when the session is team mode (`[0x168e59c] == 2`) NEW | | 0x42d6d8 |
| - | **5, 6, 7, 8** | **health factor per difficulty** (`[0x156b5f0]` 0..3) NEW | | 0x42d6ad, b5, bd, c5: health = field 3 x field 5 + difficulty |
| - | 9 | NEW, read in the blow-up routine | | 0x41263b |
| 4 | 10 | a threshold in the hit handler (slot 26) | 0x68d491 | 0x7a7285 |
| 5, 6 | 11, 12 | (6: slot 13) | 0x68be51 | 0x7c7011 |
| 7, 8 | 13, 14 | bools | 0x68bd93 | 0x7c6f03 |
| 9, 10 | 15, 16 | (10: `fsub` at the same place of the same function) | 0x68ab9f, 0x68b018 | 0x61782f, 0x582146 |
| 11, 12, 13 | 17, 18, 19 | three reads each, in the same pattern | 0x68c340 | 0x590480 |
| - | 20 | NEW (no reader within two calls of the vtable) | | |
| 14, 15 | 21, 22 | | 0x68c340, 0x689170 | 0x590480, 0x624a60 |
| 16 | 23 | `eVFX_BlowupChance`: `== 4` (Definite) | 0x68cc94 | 0x4127c3 |

- **The four values in the middle are Dog Days' own here too: fields 5..8, the health factor per difficulty.**
  The converter writes Dog Days' usual value, 1.0 (and 1000 / 1.0 / 1000 for fields 4, 9, 20). A Dead Men number
  there would be 0, 100, 100 ... - health 0 on one difficulty: that is 'cars always blow up'. Ours: all 97
  vehicle rows of the five builds have fields 5..8 = 1.0 and field 3 = Dead Men's health (500..3600).
- `eVFX_BlowupChance` has the same five names and numbers in both exes (None 0 .. Definite 4), and is the only
  field of its type, so it cannot shift.
- 'Definite' is Dead Men's own choice: 114 of the 118 vehicle controllers of the six source levels say
  `BlowupChanceDefinite`, 4 say None (M02 1, M03 2, M09_B 1) - and all 18 of stock Dog Days say Definite. Before
  -> after per map (rows equal but for the new fields): M01 9 Definite; M02 6 Definite + 1 None; M03 8 Definite
  + 2 None; M06 3 Definite; Retomoto 68 Definite. No row changed its setting.
- Every vehicle, by name (added after the review, note 9; `f11_vehicles.py`: each node with a `ZVehicleEffects`
  controller that is not on a stock F07 path, against the Dead Men object at the same path). On all 97 the
  setting and the health (the number in brackets) are Dead Men's own, and fields 5..8 are 1.0:
  - M01, 9, all Definite before and after: `Bentley_01` (1000), `Bentley_02` (1000), `Cement_Truck` (1000),
    `V_CUB_Buick_A_Static_00` (600), `V_USA_Bentley_A_Static_00` (700), `V_USA_Civilian_Suv_A_Static_00` (700),
    `V_USA_RamTruck_A_Dynamic_00` (1000), `V_USA_Sedan_A_Static_00` (700), `V_USA_SuperTruck_A_Static_00` (1000).
  - M02, 7. Definite: `PoliceCar_01`, `V_USA_Mpv_Static_01`, `_04`, `V_USA_Sedan_A_Static_01`, `_02`, `_04` (600
    each). None before and after: `V_USA_ArmoredTransport_A_Static_01` (1000).
  - M03, 10. Definite: `PoliceCar_Reinforcement_01` (two nodes: 3600 and 700), `PoliceCar_Reinforcement_02` (700),
    `V_USA_Civilian_Suv_A_Static_00` (700), `V_USA_Mpv_Static_00` (600), `V_USA_Sedan_A_Dynamic_00` (700),
    `V_USA_Sedan_A_Static_00` (700), `V_USA_SuperTruck_A_Static_01` (1000). None before and after: `Deliverycar_01`
    (1000), `V_USA_ArmoredTransport_A_Static_01` (1000).
  - M06, 3, all Definite: `Escape_Chopper` (2200), `Jpn_Boss_Chopper` (2000),
    `Traffic!V_JPN_GetawayVan_A_Static_00` (1000).
  - Retomoto, 68, all Definite: `V_JPN_RetoMoto_Helicopter_A_01` (1000); under `Vehicles_static!Police` eight
    `V_JPN_Civilian_B2_A_Group_00#01..#10`, `V_JPN_Police_A_Group_00#02_South`, `V_JPN_Police_RetoFront01`, `02`
    (500 each), `V_JPN_SWAT_North`, `V_JPN_SWAT_Van_South` (1000); under `Vehicles_static!Static_Busses` twenty
    `V_Bus_Japan_Static_01_00..#22` (1000); under `Vehicles_static` seventeen taxis (`Taxi_Classic_Green_01..06`,
    `Taxi_Classic_Red_01..08`), `V_Car01` and sixteen `V_JPN_Civilian_A / B / B2 / D / E` cars (600 each).
- `ZHavokCar[1]` `EVehicleType`, `HavokCarScriptRout[1]` `EPASSENGER_DEATH_ANIM_TYPE`, `OnlineEscVehicleController`
  (a list appended), `OnlineEscHavokCar`, `VehicleMoveBehaviourRout`: identical layouts or an unambiguous append.
  `VehicleExitBehaviourRout` is still removed by the converter (re/map_ai.md 4; kl_rtp's missing shape, not
  mine to change).

## 4. The soldier block - CLEAN (one scale that differs, two Dead Men fields with no home)

`ZSoldierRout`, DM 17 -> DD 23 fields. Slot 4 copies the properties into a block D of the rout (DM 0x724a60, DD
0x846340), slot 13 makes the soldier with a pointer to D (DM soldier+0x2d0, DD soldier+0x6d8). Readers were
found by that pointer in both exes (`readers.py`).

| DM field (D offset) | DD field (D offset) | what | reader DM | reader DD | paired |
|---|---|---|---|---|---|
| 0 style, 1, 2 features, 3 skill | 0..3 | enums by name (`ESoldierStyle` numbers differ: by name) | | | by type |
| 4 (+0x10), 5, 6 | 4, 5, 6 | accuracy %, aim, - | presets 0x724060 write 4, 5, 6 | presets 0x46e410 write 4, 5, 6: the same five rows 20/0/20, 35/20/10, 50/50/10, 60/60/5, 90/90/10 | proven |
| 7 (+0x1c) | 7 (+0x1c) | **health** | 0x722090: 'GodActors' or `< 0` = invulnerable; else `range(tuning+0x110, +0x114, field 7)`, x tuning+0xc for a mercenary -> actor virtuals +0x674, +0x66c | 0x8fbac0: the same function; `range(tuning+0x364, +0x368, field 7)` x difficulty row x **field 9 + difficulty** -> +0x674, +0x670 | proven |
| 8 (+0x20) | 8 (+0x20) | regeneration: the two numbers handed to the actor's virtual +0x67c | 0x722187, 0x7221b7 | 0x8fbbff, 0x8fbc2f; -1 = none (0x8fbbea) | proven |
| - | **9, 10, 11, 12** (+0x24..+0x30) | **health factor per difficulty - NEW** | | 0x8fbb6e..0x8fbb9c, chosen by `[0x156b5f0]` | fixed 1.0 |
| 9 (+0x24), 10 (+0x28) | 13 (+0x34), 14 (+0x38) | two tuning ranges | 0x721920: +0x144.. and +0x118 | 0x784330: +0x3c0 and +0x36c; presets write them in both exes | proven |
| 11 (+0x2c) | 15 (+0x3c) | a range x the squad's factor (+0x5c8) | 0x723d40 | 0x7842f0: byte for byte the same function | proven |
| 12 (+0x30) | - | ADDED to the alerted sense range (tuning +0x54, default 0) | 0x7222b0 -> 0x708d30 | - | dropped |
| - | 16 (+0x40), 17 (+0x44) | a range, idle / alerted - NEW; read only while the soldier's flag +0x6ac is set, which only 0x7837a0 sets, called for every member of a squad from 0x79c280 with the debug text 'CustomSixthSense: %s' (the squad modifier `ECustomSixthSenseMod` by that name; the modifier's own code was not read); else tuning +0xc4 / +0xd8 | | 0x452030, 0x4c132f; 0x5903a3 -> 0x4be110 (= DM 0x708d30) | fixed 800 (GUESS, unread on these maps) |
| 13 (+0x38) uint | - | a whole-number health that REPLACES field 7 when > 0 | 0x7220c9 | - | dropped |
| 14 name, 15 mercenary, 16 bool | 18, 19, 20 | | slot 4 | slot 4 | by type |
| - | 21 `ESRGameType`, 22 bool | NEW: the session modes the soldier exists in | | 0x622ba6 | usual value: eSR_AllTypes, 1 |

- **Fault 4 of the other porter is exactly DD fields 9..12**: health is multiplied by one of them by the
  difficulty. Dead Men's fields 9..12 there (campaign rows 50, 50, 5000, 0; the Fragile Alliance maps 20..30,
  50..65, 6000..10000, 700..1400) = health x 50, x 50, x 5000 and, with the campaign's 0, x 0 on the fourth
  difficulty. Our converter did that until 2026-10-09 (difflib paired DM9..12 with DD9..12; re/pairings.md
  table A); since then it writes 1.0, and the pairing 13 / 14 / 15 <- 9 / 10 / 11 that it rests on is now read
  in code for every field. Every build on the tab was made after that date.
- Dead Men field 13: -1 in 1,453 of the game's 1,455 soldiers; 200 and 250 on `M05_A Lynch` and `M14_A Jenny`.
  Not in our levels.
- Dead Men field 12: 700..1400 on all 54 soldiers of the four Fragile Alliance maps, 0 on M09. In Dead Men
  that IS their alerted range (the tuned part is 0), 400 when idle. Dog Days has no such field; without a squad
  modifier that enables the custom range a soldier uses the tuned 60000 / 60000 (as every stock soldier whose
  squad has no such modifier). To reproduce Dead Men one would write field 16 = 400, field 17 = Dead Men 12 and
  give the squad `eCSS_Enabled` - NOT done, not proven that it is the same range in feel.
- **Same number, other scale (not a pairing fault, but it is why 'health 100' is not the same man).** The
  tuning object's constructor sets the ranges (DM 0x6e9210, DD 0x5220e0; found by the variable registration
  loop at their ends):

  | | Dead Men | Dog Days |
  |---|---|---|
  | health at field 7 = 0 .. 100 | 50 .. 175 hit points (x 8.5 for a mercenary) | 0 .. 100 (x 0.5 / 0.9 / 1.15 / 1.3 by difficulty: re/balance.md) |
  | regeneration at field 8 = 0 .. 100 (the two numbers of virtual +0x67c; re/balance.md: seconds to wait, seconds to refill) | 3 .. 1 and 5 .. 2 | 15 .. 1 and 15 .. 1 |
  | field 9 -> 13 | 1.5 .. 3.0 and 0.3 .. 1.7 | 0 .. 0 as far as the constructor's stores were followed |
  | field 10 -> 14 | 0.8 .. 1.2 | 0.8 .. 1.2 |

  These are the constructors' defaults; nothing else that writes them was looked for. A Dead Men guard with
  '100' had 175 hit points in Dead Men and has 100 in Dog Days; '50 = regenerates' was 2 / 3.5 and is 8 / 8.
  The converter carries the numbers. `kl_map_ai`'s floors (100 / 125 / 150 / 175 by
  weapon class) already lift the four maps; `50 + 1.25 x field 7` would be Dead Men's hit points exactly (the
  bullets are Dog Days' own, so 'exactly' is only the number). NOT changed: it is the owner's balance.
- The scan (every `ZSoldier` row of the five builds against the 1,413 stock rows of 21 levels):

  | build | soldiers | from Dead Men / kl_arms | AI heisters, stock rows | health min..max | accuracy min..max | fields 9..12 | health <= 0 | any float < 0 | outside stock min..max (field: rows) |
  |---|---:|---:|---:|---|---|---|---:|---:|---|
  | M01 | 20 | 13 | 7 | 100..280 | 50..100 | 1 / 1 / 1 / 1 x 20 | 0 | 0 | 4: 13, 5: 13, 6: 13 |
  | M02 | 19 | 12 | 7 | 100..280 | 50..100 | 1 / 1 / 1 / 1 x 19 | 0 | 0 | 4: 12, 5: 12, 6: 12 |
  | M03 | 22 | 15 | 7 | 100..280 | 50..100 | 1 / 1 / 1 / 1 x 22 | 0 | 0 | 4: 15, 5: 15, 6: 15 |
  | M06 | 21 | 14 | 7 | 125..280 | 50..90 | 1 / 1 / 1 / 1 x 21 | 0 | 0 | 5: 13, 6: 14, 8: 2 |
  | Retomoto | 99 | 91 | 8 | 80..300 | 30..85 | 1 / 1 / 1 / 1 x 99 | 0 | 0 | 4: 1, 6: 1, 14: 1 |

  Stock ranges: field 4 50..90, 5 40..82, 6 45..82, 7 1..1e12, 8 -1..50, 9..12 1 (one row 12 / 8 / 6 / 5), 13
  10..50, 14 50..100, 15 1..100000, 16 / 17 10 (0)..600000. What is outside is Dead Men's own design carried
  over, none of it 0 or negative: accuracy / aim 95..100 (stock tops at 90 / 82), field 6 = 10 (stock 45..82 -
  but 10 is what the preset of `eRegular` writes), M06 regeneration 100 on two rows, one Retomoto row 30 / 50 /
  30 with field 14 = 25. No row has a Dog Days-only value other than 1.0 (9..12), 800 or 600000 (16, 17),
  `eSR_AllTypes` / `eSR_FragileAllianceOnly` / `eSR_FragileAllianceUCC` (21), 1 (22).
- Retomoto (re-rowed by `kl_arms`, not mine): 91 rows with stock police numbers; the 8 `eArmy eRegular 85 / 82
  / 82 / 150` rows are overwritten by the preset as re/map_ai.md 10.2 says (stock's own 28 are too); regeneration
  0 on 35 rows (= 15 / 15, not 'none').
- `ZFFActor` (the soldier's node), `ZCivilianRout`, `SquadModifierBehaviour`: section 5.

## 5. Pairings that are not by type alone: what is settled now, what is still assumed

Counted on the map side of the six source levels (what a build can contain; the systems side is dropped by the
graft). 'offsets' = the member offsets of the paired fields come in the same order in both exes
(`order.py`: all 3,638 pairs of every class the maps use, 0 violations except the two moves `LEVEL_MAPS`
already knows, `ZParticleEmitter` and `ZBarrelEffects`) - that excludes a swap or a move, it does NOT say which
of two same-typed neighbours is the new one.

Settled by this audit (code):

| class level | objects | result |
|---|---:|---|
| `ZSquadScript` | 152 | **WRONG, corrected** (1.2) |
| `ZTriggerBox` | 87 | **WRONG, corrected** (1.1) |
| `ZFFActor` | 301 | **WRONG, corrected**: Dead Men's last bool (DM8, `[actor+0x680]`) is DD18 (`[actor+0x820]`), not DD19: the same function reads both (DM 0x5dda00, DD 0x869b50) and four more readers match slot for slot (DM slots 57, 58, 88, 18>, 86>; DD 56, 57, 87, 18>, 85>). DD19 (`[actor+0x821]`) is new. re/pairings.md had chosen DD19 'by values' (Dog Days never sets DD18, sets DD19 on 127 of its 1,696 actors). Objects: 57 civilians of M09_A / M09_B (none in a build); every Fragile Alliance actor has it 0 (Dead Men sets its field 8 on 197 of 1,668 actors: M01_A 4, M03_A 22, M03_B 41, M05_A 17, M08_A 56, M09_A 21, M09_B 36). **NOT RUN, NO STOCK PRECEDENT** (review, defect 3): DD18 is 0 on 1,696 of 1,696 stock actors, so a converted civilian with DD18 = 1 takes a path no shipped Dog Days level takes. What that path is, read after the review: `ZFFActor` slot 57 (0x869b50) is a hit / collision filter - with the bool clear it is one mask test; with it set (0x869b79) it compares the entities of the two players with the object passed in (`[arg+0x60]`), then the same kind of mask test. Dead Men's 0x5dda28 is that branch step for step (players through 0x66fbd0, the same compare, the same masks), so it is code Dead Men ran on those 197 actors - which is the argument for letting the value through, unlike the helicopter's 'attack without a weapon' (section 6), where nothing was read. DD19 stays 0 on a converted civilian although some stock actors carry it: its readers are `ZFFActor` slots 364, 400, 406, 407, 408, 421, 422, 423 and, through the accessor 0x5e1250, the scripts `ZLieWounded`, `ZWounded`, `ZHitAnimTask` and the session handlers (slots 406 / 407 return 0.0 instead of a random number for an actor without it unless a session test, 0x6db900, says otherwise; in `ZWounded` slot 2, 0x8652ec, the flag exempts the actor from a branch taken while another session test, 0x863a60, holds) - so it has to do with the wounded states in some session kind, but what it switches is NOT established. Read it before a build carries Dead Men civilians |
| `ZSoldierRout` | 233 | right, now read for every field (4) |
| `ZVehicleEffects` | 118 | right, now read for every field, the two guesses included (3) |
| `ZTriggerCounter` | 29 | right (1) |
| behaviour base (`ZDefend-` 60, `ZFlanking-` 55, `ZHunt-` 20, `ZPatrol-` 6, `ZIdleWalkPath-` 5, `ZMiniCutscene-` 93, `ZWarn-` 2, `ZSquadModifier-` 86) | 327 | right (1) |
| `ZCoverStateChanger` | 55 | not a pairing: Dog Days' usual values reproduce Dead Men's hard-coded behaviour (1) |

Still not read in code, ranked by what a wrong pairing would do:

| # | class level | objects M01 / M02 / M03 / M06 / M09_A / M09_B (map side) | how paired | worst plausible effect if shifted |
|---|---|---|---|---|
| 1 | `ZHeliFlyBehaviourRout` | 0 / 0 / 0 / 4 / 0 / 0 | `LEVEL_MAPS`: speed, list, enum; Dead Men's three bools (0, 1, 0) are NOT paired and Dog Days' two `EHeliFacingMode` take the usual `FACE_SPLINE`, `FACE_TARGET_90DEG_CW` | M06's two helicopters hover turned 90 degrees or fly otherwise than in Dead Men; could be seen in a round. The one class where a known Dead Men value is knowingly lost |
| 2 | `ZHavokRigidBody` | 40 / 80 / 179 / 16 / 8 / 28 | `LEVEL_MAPS`: the new float is DD7, by values (0 in 578 of 578) | one physics float of each loose prop off by one (mass / damping / a limit): props fly or stick. The readers could not be told apart (the properties sit in a struct, not the node) |
| 3 | `ZParticleEmitter` | 2872 / 3494 / 3535 / 2688 / 643 / 3180 | `LEVEL_MAPS`: 190 of 194 same-named emitters agree; struct layout | visual only: an effect's size, rate or direction |
| 4 | `ZCivilianRout` | 3 / 3 / 5 / 0 / 21 / 36 | 1 float -> 9 fields: DM0 -> DD0 (both 5000), the rest usual values (0, 5, 10, 1 x 5) | a civilian's flee range in one of eight new numbers; the five 1.0 look like the difficulty factors again (not read) |
| 5 | `ZHavokShatter` | 10 / 59 / 198 / 42 / 302 / 29 | difflib: f, b, f, f appended behind 44 fields; types differ member / accessor | glass and debris: when a pane breaks, how far it flies |
| 6 | `ZOnlineEscCamTrigger`, `ZOnlineExitLevelTrigger`, `ZPlayerAction` | 5 / 5 / 5 | `LEVEL_MAPS` by values; kl_fa repairs / re-writes them anyway | the escape camera or the boarding action not found: seen at once (and they work live) |
| 7 | `ZSoundLimiterFade` 133, `ZParticleTemplate` 147, `ZTrafficFlow` 21, `ZHeli` 2, `CCheckInside` 2, `ZCloth` 106, `ZLNKWHANDS` 305 | | one field appended or offsets | sound fades, a traffic flow's flag, a hand slot; `ZLNKWHANDS` DD0 is 'medium' in re/pairings.md and both are sound offsets the graft rewrites |
| 8 | `ZOnlineFragileAllianceSettings` | 1 / 1 / 1 / 1 | `LEVEL_MAPS`: 173 strings by event name; the graft keeps F07's settings and takes sounds from them (`kl_fa.settings_from_host`) | a wrong voice line at an event |
| 9 | `ZPatrolBehaviourRout` (added after the review, note 4) | 0 / 3 / 0 / 2 / 0 / 1; 5 in the builds (M02 3, M06 2) | by type and order: `e refs b e refs b` -> `e refs b e` **`b f b f`** `refs b` + the base's new bool. The four in the middle are Dog Days' usual values 1, 50.0, 1, 200.0 (stock: 1 x 17; 50 x 9, 30 x 6, 500 x 2; 1 x 17; 200 x 11, 1000 x 6) | a patrol that waits or turns back at another distance than Dog Days' own patrols; the four were NOT read |
| 10 | `ZIdleWalkPathRout` (note 4) | 2 / 0 / 3 / 0 / 0 / 0; 5 in the builds | the level itself is unchanged; the base's new bool comes out 0. No stock Dog Days level has the class at all, so 0 is the blank default, not a usual value | an idle walker of M01 / M03 behaves otherwise at the end of its path; NOT read |
| 11 | `ZMatPosAnimProxy` (found by the census after the review) | 0 / 0 / 0 / 0 / 11 / 2; 2 in the Retomoto build | by order: `I I I refs refs` -> `I I I refs` **`b`** `refs` **`s b`**; the three new ones take 0, 'AITrigger', 0 (stock: 0 x 673 of 713; 'AITrigger' x 549; 0 x 713) | a proxied animation (a door, a lift part) that does not answer its message; NOT read, not seen at fault in the Retomoto runs |
| 12 | `ZLightFlicker` 1 (M03), `ZGEOM` (every geometry node), `ZSNDOBJ` (every sound node) | | one bool appended behind another type; 0 = Dog Days' usual value (stock 0 x 290 of 466; 0 x 511,914 of 511,915; 0 x 6,912 of 7,007) | none expected: an append cannot shift |
| - | `ZItemTemplateWeapon`, `ZItemTemplateAmmo`, `ZInventoryBinding`, `CExplode` (2 on Retomoto), `ZKillBox`, `ZBarrelEffects`, monitors | 0 in a build | | only a whole-level conversion |

CLAUDE.md names four as worst: `ZParticleEmitter` (visual; strong evidence by names), `ZOnlineFragileAllianceSettings`
(strings by name), `ZFFActor` (settled: one field wrong, corrected), `ZItemTemplateWeapon` (not in any build).

Dog Days-only fields that take the usual value, checked for a 0 where a factor is expected: `ZSoldierRout` 9..12
= 1 (fixed), `ZVehicleEffects` 5..9 = 1, `ZCivilianRout` 4..8 = 1, `ZSquadModifierBehaviour`: every new modifier
enum `..._NotSet` (EDamageModifier, EHealthModifier, EVisibilityModifier, EDownNotDeadModifier,
ECustomSixthSenseMod, EBlindfireProbabilityModifier, ECastShadow, EMarkDead, EAggroModifier), `EShotCollision`
eSC_Enabled, float 1.0; `ZFFActor` 6, 7 = -1, 10 = 10, 13 = 1, 15 = 50; `ZTriggerBox` 15 = 0, 16 =
EFAMPS_ALL_MODES; `ZHavokRigidBody` 7 = 0. None is a 0 in a multiplier that was read.
Added after the review (note 4; `f8_changed.py` lists all 41 class levels that differ between the exes and
have objects on a Dead Men node of a build, `f9_newfields.py` what the builds hold): `ZPatrolBehaviourRout` 4..7
= 1, 50.0, 1, 200.0 and 10 = 0 (5 objects), `ZIdleWalkPathRout` 6 = 0 (5), `ZMatPosAnimProxy` 4 = 0, 6 =
'AITrigger', 7 = 0 (2), `ZLightFlicker` 7 = 0 (1), the new bool of the behaviour base on `ZDefend-` /
`ZFlanking-` / `ZHuntBehaviourRout` = 0 (stock 0 on 1,616 of 1,630, 34 of 34, 5 of 5), `ZGEOM` 5 = 0, `ZSNDOBJ`
1 = 0. No float among them is 0; what the two floats of the patrol rout scale was NOT read.

## 6. Enum names - FAULT (small), and names that mean something else

Dead Men option names that Dog Days' enum of the paired field does not have, on the map side (the converter
used to write Dog Days' most common value and log the name only; it now logs the value written too):

| enum, Dead Men option | objects | became | now |
|---|---|---|---|
| `ECOLLISIONPRIORITY` PRIORITY_NORMAL | 40 / 80 / 178 / 16 / 8 / 28 | COLLISION_PRIORITY_NORMAL (the default happened to be the rename) | renamed (`ENUM_RENAME`) |
| `ECOLLISIONPRIORITY` PRIORITY_CRITICAL | M03: 1 (`...M03_FAA_Outside_01A\PC0300_USA_Foam_B_01`) | **COLLISION_PRIORITY_NORMAL** | COLLISION_PRIORITY_CRITICAL |
| `EHeliAttackMode` FRONT_GUN | M06: 2 (`BossChopper!Helicopter!Helicopter\ApproachEvacPoint`, `\Evacuate`) | **NO_ATTACK** | GUN_ATTACK in the converter - and back to NO_ATTACK in every graft (`kl_fa.heli_attack`), see below |
| `EHeliBoneType` FRONT_BARREL, FRONT_TURRET | M06: 1 + 1 (the escape helicopter's `HeliWeapon`) | GUN_BARREL3, GUN_TURRET3 | unchanged. GUN_BARREL1 / GUN_TURRET1 would be the guess; the bone tables were not read, and that helicopter's weapon is emptied by the graft and its routs say NO_ATTACK |
| `ESPAWN_TYPE` eSPAWN_TYPE_COMUNISTS | M02: 1 (`SpawnPoint!SpawnPoint_Start_02`) | eSPAWN_TYPE_FRAGILE_ALLIANCE_START | unchanged. Dead Men's own file has a start point with a campaign type (dead there); as a START it is what its name says. Note it: Late Night Opening has one start position more than in Dead Men |
| `EVisionModifier` eVIM_DoubleRange 7, _NormalRange 7, _HalfRange 1, _QuarterRange 1 | M09_B: 16 squad modifiers (5 of them in the Retomoto build by path) | eVIM_NotSet (the modifier does nothing to the range) | unchanged. By the names: Factor_2_0, 1_0, 0_5, 0_2 or 0_3 - NOT read in either exe (no table found; a switch). One line in `ENUM_RENAME` when somebody has |

`ECOLLISIONPRIORITY` and `EHeliAttackMode` are the same lists under other names in the two exes (2 options 0 / 1;
3 options 0 / 1 / 2): renamed. Systems side (dropped by the graft): the 32 item names of `ITEM_RENAME`, nothing
else. Dead Men-only modifier enums of `SquadModifierBehaviour` (EFrightFactorModifier, EAttackPoseModifier,
EHealableModifier, EMercControlMod, EMustSurviveMod, EAutoHealInEasyModeMod, EAmbushTargetMod, EBlindFireMod,
EWeaponSharing) have no Dog Days field: dropped with whatever they said.

**The helicopter.** Dead Men's M06 gives its BOSS helicopter (no `HeliWeapon` controller) two routs with
FRONT_GUN; the escape helicopter has the gun and says NO_ATTACK. So in Dead Men the setting did nothing. Stock
Dog Days: 49 routs say GUN_ATTACK, every one under a helicopter with a `HeliWeapon`; 65 are under one without and
all say NO_ATTACK. 'Attack' without a weapon was never run by Dog Days and its code for it was not read, so the
correct rename is not let through on M06: `kl_fa.heli_attack` (in `kl_fa.repair`) writes NO_ATTACK where the
helicopter of the rout's group carries no weapon - which is what every build that ran had. Tested: 0 changes
on the 21 stock levels, L09's 40 GUN_ATTACK routs untouched, M06's set back.

**Names that exist in both games but mean something else** (the known case: `eFMM_LookFromPosFA`):

- NEW, the Kane / Lynch enums - `ECoopPlayerSetting` (ECPS_KANEONLY / ECPS_LYNCHONLY), `EPlayerFilter`
  (eONLY_KANE / eONLY_LYNCH), `EFlashBackPlayer`. Dog Days swapped the NUMBERS of the two names (KANEONLY 1 -> 2,
  LYNCHONLY 2 -> 1; eONLY_KANE 0 -> 1, eONLY_LYNCH 1 -> 0), because the number is the player's SLOT in both
  exes and the lead character changed: in `ZTriggerBox`'s update value 1 is 'the first player' and value 2 is
  taken only in co-op, in DM (0x6a00dc..0x6a00f6: 1 -> player 0, 2 -> player 1 if co-op) and in DD
  (0x42b231..0x42b25b: 2 -> needs the co-op flag, 1 -> 0x432a20). **A converter that keeps the NAME hands a
  Dead Men 'first player only' object to the second player.** It has already bitten once: Dead Men's boarding
  action says eONLY_KANE, came out as eONLY_KANE, and the van could not be boarded (run ESC2) until
  `kl_fa.boarding` wrote eBOTH_PLAYERS; stock Dog Days never has eONLY_KANE on a boarding action (24 both, 12
  eONLY_LYNCH). In the five builds no such value is left on a Dead Men object (M09's co-op boxes and cameras are
  not in the build). For a CAMPAIGN port (the contact's) every Kane-only / Lynch-only box, camera box, objective
  and action is affected: swap the two names. Not put into the converter: only `ECoopPlayerSetting` is read in
  code, and nothing of ours needs it.
- `ESoldierStyle`, `ESPAWN_TYPE`, `EIsMercenary`, `EFollowModifier`: other numbers, the same meaning by name as
  far as read (style: the presets and readers compare with Dog Days' numbers; spawn: `kl_fa` and live rounds).
- Health / regeneration: the same number on another scale (section 4) - the non-enum case of the same thing.
- Not compared in code: `EDefendMoveSet`, `EPatrolMoveset`, `EAttitude`, `EIdleAlertness`, the squad modifier
  enums that both games have (their option lists are identical).

## 7. What was changed

| file | change |
|---|---|
| `tools/kl_convert.py` | `SQUAD_LISTS = [0, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14]` (1.2). `LEVEL_MAPS['ZTriggerBox']`: DD7 <- DM7, DD9 <- DM8, DD8 new (1.1). `LEVEL_MAPS['ZFFActor']`: DD18 <- DM8 (5). `ENUM_RENAME` (new) for `ECOLLISIONPRIORITY` and `EHeliAttackMode`, applied in `Converter.value`; the log line 'enum value replaced' now says what was written. Comments of `ZSoldierRout` / `ZVehicleEffects` say what is proven. |
| `tools/kl_fa.py` | `heli_attack()` in `repair()` (6). |
| `tools/kl_map_ai.py` | `pairfix` (below); comments of `SQUAD_DEAD` and of the health line. |
| `re/pairings.md` | the three rows and the paste block corrected, a dated note on top. |
| after the review | `kl_convert.py`: comments only - `ZFFActor` says 'NOT RUN, no stock precedent' and what was read of DD18 / DD19; `SQUAD_LISTS` says who sends 'attacked' in each game, what Dog Days list 8 is, and that the tab maps cannot show the pairing. `kl_map_ai.py` `pairfix`: a block 'in play' (per moved list: how many targets are also in a list of the same squad that never moved, how many more another object names, how many nothing else names), a class 'right already' so that a second run on its own output no longer prints 'left as they are' for what it moved (review note 7), and two neighbouring lists that are both in place are no longer refused as a clash. `re/pairings.md`: the two stale comments of the paste block (note 5). No pairing, no value and no check was changed after the review. |

`python tools\verify_levels.py` (from the work folder): `problems: 0` on M01_FA_A, M02_FA_A, M03_FA_A, M06_FA_A;
the same check on M09_A and M09_B in memory: 0. (Run again after the review's edits, with the same lines; and
`t_convert.py` converts the six levels with the working tree's converter and with the one committed at HEAD -
the latter on its own copy of the cache - and compares every object by name: the list below, to the number.)
The converter's output differs from this morning's in exactly:
M01_FA_A 6 `ZSquadScript`; M02_FA_A 1; M03_FA_A 1 `ZHavokRigidBody`; M06_FA_A 8 `ZSquadScript`, 1 `TriggerBox`, 2
`HeliFlyBehaviourRout` (set back by kl_fa in a graft); M09_A 2 `ZSquadScript`, 21 `ZFFActor`; M09_B 9
`ZSquadScript`, 36 `ZFFActor`. `<work>\dd_typical.json` (the cache of usual values) was rebuilt by the first run
because two fields changed sides; kl_rtp was not touched. (Review note 8: the cache now holds the corrected
converter's field set. A session that still runs a `kl_convert.py` from before 2026-10-11 04:41 against the same
work folder rebuilds it - 44 archives - and writes it back; two at once can read a half-written file. Other
sessions must take the corrected file before they convert.)

**`kl_convert.py` is in the shared tree: any `kl_graft.py build` from 2026-10-11 04:41 on converts with the
corrected pairings.** No existing build was touched. Every build that exists still has the old ones (review
note 6: the first list here was already old the same night). Counted again at 05:50 (`f12_installed.py`, read
only): the tree in the game folder is DM01 = `z_route3\M01` (member for member also `z_route4\M01`), DM02 =
`z_m02s1\M02` (= `z_route4\M02`), DM03 = `z_cover3\M03`, DM06 = `z_route\M06` (= `z_loot3\M06`, `z_route4\M06`),
DM09 = `z_route7\retomoto_full`; and all 18 builds looked at - those five, `z_hop\M03`, `rt_full7\retomoto_full`,
`z_loot3\M01..M06`, `z_route4\M01..M06`, `z_route4\retomoto_full`, `retomoto_full_r2`, `retomoto_tab_fix` - give the
same pairfix lines per map as below. None was made by a fresh graft, so none has silently taken the new
pairings; **the first fresh `kl_graft.py build` will differ from every build that ran** (in the objects of the
table below and in nothing else of the conversion).
The scans of sections 2 - 4 on the two installed builds the audit did not name (`f13_scan.py`, which also gives
the audit's own 181 soldier rows and 97 vehicles on the five): `z_cover3\M03` 22 soldier rows and 10 vehicles,
`z_route7\retomoto_full` 99 and 68 - every health factor 1.0 (soldier fields 9..12, vehicle fields 5..8), no
health <= 0 (100..280 and 80..300), blow-up settings as in Dead Men (8 Definite + 2 None; 68 Definite), no actor
with a grenade (one machine-gunner with a second weapon, as before), none with field 18 or 19 set, no `eFF2Item`
option and no Kane-only / Lynch-only option on a node that is not a stock F07 path.

Putting a build right without re-making it - `python tools\kl_map_ai.py pairfix <build folder> [<out folder>]`
(without an out folder it only lists). It moves, on objects that have the scene path of a Dead Men object and
still hold what the old converter wrote: the squad event lists, the trigger-box bool, the rigid body's enum. Only
the `.prp` member changes; `steps.json` gets `pairfix`. What it lists, per map (the same on every build of that
map named above), with what the move changes in play (section 9):

| map | squads (lists moved) | boxes | enums | entries moved: also in a right list of the same squad / also named by another object / named by nothing else |
|---|---|---|---|---|
| M01 | 6 ('attacked', fields 12 -> 13) | 0 | 0 | 21: 10 / 11 / 0 |
| M02 | 1 | 0 | 0 | 2: 2 / 0 / 0 |
| M03 | 0 | 0 | 1 (the foam prop) | - |
| M06 | 8 | 1 (both lists empty, nothing names it) | 0 (2 helicopter routs left at NO_ATTACK on purpose) | 8: 5 / 3 / 0 |
| Retomoto | 2 (`Squad_AtrTop_Reception` 'attacked'; `Squad_InFront` 'one left', fields 6 -> 7) | 0 | 0 | 2: 1 / 1 / 0 (and the squad of 3 sends 'half dead' and 'one left' in the same update) |

Tested offline, again after the review's changes to `pairfix` (`t_pairfix.py`: each of the five builds named in
the header written into the scratchpad, checked, deleted): only `F01_Main.prp` differs by CRC, beside the archive
only `steps.json`; 0 objects that do not fit, 0 dead scene paths, `kl_map_ai.faults` 0, `kl_fa.check` the same
findings as the source; BY NAME every Dead Men entry that was in the old field (13 + 2 + 0 + 8 + 2) is in the
field of its own event and gone from the old one (control: 0 of them are there in the source build); no object
outside the ones pairfix lists differs by a token (control: every listed one does); a second run on the output
moves nothing and lists what the first moved as 'right already'. The chains no build has (two neighbouring Dead
Men lists on one squad: 5 -> 6 -> 7, 12 -> 13 -> 14) were run in memory (`t_chain.py`: old layout, the same target
in both lists, a build converted with the corrected pairing): right fields after one run, nothing moved by a second.
To re-make a build from scratch instead: `python tools\kl_graft.py build F07 <M0x_FA_A>` (Retomoto: the
`kl_maps.py chain ... --author` of re/maps.md) and then the steps its `steps.json` records, in that order.

HOW MUCH THIS CHANGES THE MAPS IN PLAY (rewritten after the review, defect 2; the first text said 'a change of
how the maps PLAY' on M01, M02, M06 and judged by object counts): next to nothing, and on no map a new target.
Section 9 has it squad by squad. The risk to the difficulty the owner likes is small; there is no reason to roll
the correction out one map at a time, and no reason to hurry it either - it can ride on the next build of each
map that is made for another reason (pairfix as the last step, or a fresh graft). The one thing that is new
against Dead Men itself: on M01 three squads of ONE CIVILIAN each get a live 'attacked' list (section 1.2).

## 8. Not done

- No live run. None of the corrected pairings was seen in the game; `pairfix` output was never loaded. A run of
  the tab maps could not show a pairing anyway (section 9): no hook log line for squad events was written (the
  hook is not this track's; the exact request is in 9.4) and no probe build was made.
- Dog Days squad list 8 is read now (a player's close combat, 1.2). Still not read: the condition of list 5
  (sender found), the events of Dead Men lists 7 and 10 = Dog Days 10 and 13 (list 10's sender found, list 13 has
  none through the common helper), the state value 3 that `ZFFActionCloseCombat` sets when it sends list 8.
- `ZHavokRigidBody`'s new float, `ZHeliFlyBehaviourRout`'s three Dead Men bools, `ZCivilianRout`'s eight new
  numbers, `ZHavokShatter`, `CCheckInside`, `ZPatrolBehaviourRout`'s four new values, `ZMatPosAnimProxy`'s three:
  not read in code (section 5). `ZFFActor` DD19: readers found, meaning not established.
- The three M01 squads of one civilian whose 'attacked' list becomes live with the corrected pairing: left as
  Dead Men wired them (9.5); not decided for the owner.
- `EVisionModifier`, `EHeliBoneType`, the Kane / Lynch role swap: found, not changed (section 6).
- Health and regeneration scales: found, not changed (section 4).
- `VehicleExitBehaviourRout` (kl_rtp type 54) and kl_arms' emptied grenades: other owners.
- Enums or ids inside `.gms` raw data blocks, `.buf`, and the classes only the systems side uses: not looked at.

## 9. After the review: what the corrections change in play, and what a live run can and cannot show

The review (`re/convert_audit_review.md`) accepted every pairing and found three things to put right, all in
what the lead is told: the live checks proposed with the first report cannot tell a right pairing from a wrong
one (S1), the effect on the maps was overstated (S2), and `ZFFActor` DD18 is let through without a stock
precedent and without saying so (S3, now in the code comment and in section 5). This section is the answer to
S1 and S2, from this pass's own readings (scratchpad `CF\`); two of the review's side remarks do not hold and
are corrected here.

### 9.1 Squad by squad (the same on every build of the map that exists, section 7)

'Right list' = a list whose pairing never changed: first dead, wiped out, something noticed, a hostile seen.

| map | squad (members in the level file) | list moved | what it names | where else the same targets are named | change in play |
|---|---|---|---|---|---|
| M01 | `AI_Enemies!CheckFront` (1 soldier) | 'attacked', 5 | its own flank rout, `FrontMall_01` / `_02` flank routs and their two `VehicleExitBehaviour` nodes (plain groups since the converter drops that rout: nothing to start) | all 5 in the squad's own 'a hostile is seen' | the moment only: hit before he has seen a hostile |
| M01 | `AI_Enemies!KitchenBoy` (1 soldier) | 'attacked', 5 | the same shape | all 5 in its own 'a hostile is seen' | the moment only |
| M01 | `Civilians!LeavingWoman`, `Civilians!LeavingMan` (1 CIVILIAN each) | 'attacked', 3 each | `FrontMall_01\FlankingBehaviour`, `Civilians!GangMembers\GangStartTimer` (3 s, then the gang's flank rout), `FrontMall_01\VehicleExitBehaviour` | all three in `CheckFront`'s and `KitchenBoy`'s 'a hostile is seen'; the timer also in the box `Triggers!EnterDiner` (a player enters) | the moment only - and it fires at all, which it never did in Dead Men (1.2: Dead Men's civilian does not send the event, Dog Days' does, whoever hit her) |
| M01 | `Civilians!Waitress` (1 CIVILIAN) | 'attacked', 2 | `FrontMall_01`'s flank rout and exit node | as above | as above |
| M01 | `Civilians!GangMembers` (2 soldiers) | 'attacked', 3 | as `LeavingWoman` | as above | the moment only |
| M02 | `AIEnemies!3rdFloor_Guard_01` (1 soldier) | 'attacked', 2 | `2ndFloor_Guards\FlankingBehaviour`, its own flank rout | both in its own 'a hostile is seen' | the moment only |
| M06 | `US_DrugSquad_Secure_Boss`, `US_Boss`, `US_DrugSquad_Bridge_01`, `_Bridge_02`, `_Island_01` (1, 1, 2, 1, 2 soldiers) | 'attacked', 1 each | `Triggers!US_UnderFire_Counter` | each squad's own 'a hostile is seen' names the same counter | the moment only |
| M06 | `JPN_Boss`, `JPN_DrugSquad_Bridge_01`, `_Island_01` (1, 2, 2 soldiers) | 'attacked', 1 each | `Triggers!JPN_UnderFire_Counter` | the US counter names it (both count to 1 and name each other); the US counter is in 'a hostile is seen' of seven squads, the two Japanese ones among them | the moment only: both counters fire, the flank routs start and both boss timers (20 s, 50 s; the hunts hang on them) start running at the first hostile ANY of the seven sees - before and after |
| M06 | box `Triggers!JPN_Boss_Start_WalkTo_USBoss` | bool 8 -> 7 | - | both lists empty, nothing names it | none |
| M03 | `PC0300_USA_Foam_B_01` | collision priority NORMAL -> CRITICAL | - | - | one loose prop; what the priority does was not read; nothing to watch for |
| Retomoto | `040_Atrium_3rd!Squad_AtrTop_Reception` (2 soldiers) | 'attacked', 1 | its own `03_HuntBehaviour` | its own 'something is noticed' | the moment only |
| Retomoto | `010_RetoBldFront!Squad_InFront` (3 soldiers) | 'one left', 1 (was in 'half dead') | its own `Regroup` (a defend rout) | `Mercenaries!TriggerBox_1_LeaveElevator` names it too | NONE: 'half dead' is alive <= members / 2 in whole numbers (kl2 0x47e4d8: `cdq; sub eax, edx; sar eax, 1`; members = `[x+0x48]`, counted up once per member in slot 14, 0x7b3907) and 'one left' is alive <= 1 (0x47e4f4), tested in the same update: with 3 (or 2) members both go out together |

Totals: 33 entries moved on the five builds; 18 are doubles of a right list of the same squad, 15 are named by
another object, 0 by nothing else. `python tools\kl_map_ai.py pairfix <build>` prints this per list ('in play')
for any build, so it can be read off a new build without this table.

Against the review: (a) it expected that a civilian's squad 'may never' send 'attacked' and so that
`Civilians!GangMembers` is the one squad of the four maps where the correction can be SEEN. The first half is
the other way round (1.2: the unread third caller is the civilian's), and the second does not hold either: the
gang's three targets start at the first hostile `CheckFront` or `KitchenBoy` sees, and its timer when a player
walks into the diner. (b) It lists `Squad_InFront` 'regroups at one man left instead of at half' and
`Squad_AtrTop_Reception` 'hunts when attacked' as real changes: the first is the same update for a squad of
three, the second is already in that squad's 'something is noticed' list. Its main point stands, more strongly
than it put it: **no build of ours has a squad on which the corrected pairing can be seen.**

### 9.2 What the old pairing does today

On every build that exists Dead Men's 'attacked' wiring sits in Dog Days list 8, which is sent when a PLAYER
starts close combat on a member of the squad (1.2). An AI heister never does (they are `ZFFActor`; the routine is
called from `ZFFPlayer` slot 87 and its remote twin only). So today: grab one of M06's gang members and both
counters fire - which the first hostile seen has done long before. Nothing of that is a fault a player meets.

### 9.3 Live checks: REGRESSION ONLY (this replaces P1 - P3 of the first report)

A run of a pairfix build can show that the build loads and plays as the same map did before. It CANNOT show
that a pairing is right: nothing on these maps reacts differently (9.1) and KLHook.log has no line for a squad
event. **Do not write 'pairing seen live' after such a run.** The proof of the pairings is the code of both
exes (sections 1, 3, 4, 5, re-derived by the reviewer).

- R0 (no game): `python tools\kl_map_ai.py pairfix "<work>\build\<build>"` - the squads / boxes / enums of the
  table in section 7 for that map, `named by nothing else` 0, `faults ... 0 before, 0 after`.
- R1 (owner away, TEST hook, one map a run; M06 first because it has the most changed objects): `python
  tools\kl_map_ai.py pairfix "<work>\build\z_route\M06" "<work>\build\c_pairfix\M06"`, the build into the test slot
  the usual way, `kl_autotest`. PASS = the lines the same map gave before: level loaded, the round reaches GO
  (session state 0x19), `RESULT:` clean exit, no fault line; with the bot log the same order of stages and the
  helicopter's trips. EXPECT NO DIFFERENCE TO SEE - a difference would be a finding, not the proof.
- R2..R5: the same for M01, M02, M03 (one enum on one prop), Retomoto (the build that is on the tab then).
- If a run faults at the load: the build it was made from is untouched; report the address. The converter
  change is independent of pairfix.
- Next fresh graft of M06 (`python tools\kl_graft.py build F07 M06_FA_A`): the log must show `kl_fa: 2 helicopter
  fly rout(s) said attack on a helicopter without a weapon: NO_ATTACK` and verify must say `problems: 0`.

### 9.4 What WOULD prove it live (not done: neither is this track's to make)

1. A log line in the hook (klhook's owner; TEST build only, read-only detours at function entries):
   - the EVENT helpers, each called when its event happens whether or not the list has entries. `ecx` = the
     squad object (`CPPScript::ZSquad`; its controller is `[squad+0x19c]`, the controller's entity
     `[controller+0x24]` for the name), one stack byte (1 = replayed from the network): list 5 0x56d0b0, 6
     0x6831f0, 7 0x720e70, **8 0x42dfa0, 9 0x7cc4a0**, 10 0x6fd630. `ecx` = the `ZSquadScript` controller, no
     argument: list 0 0x51c8e0, 2 0x649d30, 3 0x86b470, 4 0x87ebf0 (the squad update 0x47e440 calls each once,
     at its condition).
   - or, with two detours only, the two routines every list goes OUT through - but they see a list only when it
     has entries (except 9 and 14, which are handed on even when empty): kl2 0x79d6d0 (`ecx` = the squad object, `[esp+4]` =
     the list; number = 5 + its position among the ten dwords `[squad+0x164]` .. `[squad+0x188]`; entry count =
     the list's virtual +0x14) and kl2 0x77b820 (`ecx` = the controller, `[esp+4]` = the address of the list;
     number = (address - (`ecx` + 0x5c)) / 0x1c, 0 .. 4; list 1, 'every death', has no helper and shows only here).
   - line: `squad <name>: list <n>`.
   With it ANY map proves the numbering in one scripted run with the bots and an idle player - no pairfix build
   is needed: `list 9` comes for a squad once (sent byte +0x15d) and only after one of its men was hit; `list 0`
   at a squad's first death, `list 2` at the death that leaves members / 2 or fewer alive, `list 3` at one left,
   `list 4` at none - all checkable against the bot log's deaths; `list 8` needs a human who grabs an enemy.
   That is a test that can FAIL: a `list 8` line when a man is merely shot, `list 9` for a squad nobody hit, or a
   `list 2` at every death would refute section 1.2.
2. A probe build: a copy of a build WITHOUT the seven bots, one squad of soldiers whose field 13 ('attacked')
   alone names an object that nothing else names and whose start cannot be mistaken, and field 12 another. Not
   built: it needs a human to shoot a chosen man unseen, and the hook line is cheaper and proves more.

### 9.5 The one decision the correction asks for

With the corrected pairing the three M01 squads of one civilian (`LeavingWoman`, `LeavingMan`, `Waitress`) have
a LIVE 'attacked' list for the first time in either game: a hit on one of them - by anybody, the civilian's
handler does not ask who - starts `FrontMall_01`'s flank and, for two of them, the gang's 3 s timer. Dead Men's
designers wired exactly that, Dead Men's code never sent it. It is left as wired (the same targets start at the
first hostile seen anyway, so a round can hardly differ). If the owner ever finds the diner's police come too
early on a pairfix build: empty field 13 of those three squads (one `kl_map_ai.put` each) - that restores what
Dead Men did, not what its level file says. NOT RUN.

Scripts of this pass: scratchpad `CF\` (`flib.py`; `fdis.py` disassembly, callers, vtable slots; `f1_delta.py`
squad by squad; `f2_switch.py` the event switches; `f3_lists.py` who names what; `f5_disp.py` readers of a
member; `f4_writes.py` writers of a member; `f6_actors.py`; `f7_census.py`; `f8_changed.py`; `f9_newfields.py`;
`f10_use.py`; `f11_vehicles.py`; `f12_installed.py`; `f13_scan.py` the audit's scans on any build; `t_convert.py`
the conversion against HEAD's; `t_heli.py`; `t_pairfix.py`, `t_chain.py` the pairfix tests). They are not part of
the repo.

Scripts behind every number of sections 0 - 8: scratchpad `C\` (`lib.py`, `refl.py` records with offsets and accessors, `members.py`
/ `listing.py` / `readers.py` / `xref.py` / `msgid.py` code readers, `diff.py` / `after.py` before -> after of the
conversion, `soldiers.py`, `vehicles.py`, `squads.py`, `tbox.py`, `actors.py`, `items.py`, `players.py`,
`heli.py`, `tuning.py`, `order.py`, `layouts.py`, `match.py`). They are not part of the repo.
