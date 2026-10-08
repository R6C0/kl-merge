# What makes a level a working Fragile Alliance round

Specification for the graft. Written 2026-10-09 from static reading only: the nine stock Dog Days (DD)
FA levels (F01 from `KL_PortBackup`, F02..F09), the four Dead Men (DM) FA maps, twelve DD story
levels where a comparison was needed, and `kl2.exe`. Nothing here was tried in the running game.

Status words used below:
- **seen** - counted or read in level files / the exe; the command is reproducible.
- **ASSUMPTION** - inferred from names, values or position; not confirmed in code.
- **not established** - looked for, no answer.

Method: every `.prp` node was paired with its `.gms` entity (name from the `.buf`, class from the type
id) and decoded with the exact schemas (`tools/kl_rtp.py`); references are property strings equal to
another node's scene path. "Layer" = everything outside `Locations/`, `CloneGroup_*`, `AllLevels/`,
`gamemenu.zip`. Field numbers are 0-based positions in the controller's serialized field list
(`Schema.fields(class)`); node properties are numbered the same way. Scratch scripts (loader, tables,
reverse-reference search, exe cross-reference classifier) are in
`%TEMP%\claude\c--kl-merge-kl-merge\1e45a579-...\scratchpad\agents\track-gamemode\` (`load.py`,
`ctab.py`, `cv.py`, `who.py`, `tgt.py`, `sett.py`, `cmp.py`, `gw.py`, `xr.py`).

## 0. The findings that change the plan

1. **A converted Dead Men exit trigger hangs or crashes Dog Days.** DD `OnlineExitLevelTrigger` has 6
   fields (bool, 5 strings) against DM's 1 string. In DD the vehicle is chosen by
   `ZOnlineExitLevelTrigger` vtable slot 34 (kl2 0x6c3d50): a random pick among members +0x48..+0x54
   (fields 2..5), **retried in a loop until a non-empty one is hit** (0x6c3f90..0x6c4039) - with all
   four empty it never leaves the loop. Type pairing puts DM's vehicle into field 1 (+0x44), which is
   only used once and only when field 0 (+0x41) is true. The DM vehicle must go to **field 2**.
   Member offsets are from the property records at 0xd0f074 (+0x10 of each record, plus 4).
2. **`OnlineExitLevelTrigger` needs an `OnlineEscVehicleMonitor`, and DM maps have none.** After the
   pick, slot 34 tail-calls 0x6276e0 with `ecx = [0x168cc00]` (the monitor singleton, written by
   `ZOnlineEscVehicleMonitor` slot 13, 0x8d2b60) and that function reads `[ecx+0x48]` with no null
   test. All nine DD levels have exactly one monitor; DM's exe has no such controller.
3. **The settings object is mandatory at the latest when somebody dies.** `[0x168c630]` (current
   gameplay settings, written by `ZOnlineFragileAllianceSettings` slot 16, 0x88d7c1) is dereferenced
   without a null test at 0x500990 ("FA_DieFrom%s", called from `ZFADeathCamDisplay` slot 11 and
   `ZMercsShowInfoFA` slot 8) and at 0x728ba3 ("YouRespawnAs%s", `ZFADeathCamDisplay` slot 5).
4. **Dog Days vans are baked animations, not driven cars.** The five DD levels with a van (F01, F04,
   F05, F07, F09) use three `ZAnimatedVehicle` + `OnlineEscAnimatedVehicle` groups under `Animation/Fxx/`
   whose path is a `MatPosAnimProxy` frame range per phase. The four others use a helicopter
   (`ZHeli` + `OnlineEscHavokCar` + `OnlineEscVehicleController` + fly routs). **No DD FA level has a
   ground vehicle that drives a route**; DM's (`ZHavokCar` on a spline, `OnlineVehicleOnSpline`,
   `VehicleMoveBehaviourRout`) exists in DD's exe with the same layouts but 0 uses in DD FA levels.
   "Van down the road" for Retomoto is therefore either a new baked animation or the untested DM
   spline car. Owner's design depends on this; see section 4.
5. **Dead Men's level music sits in the settings object; Dog Days still reads that slot.** Settings
   integer fields are offsets of sound definitions in the level's `.SND` (seen: resolved for F01-F03
   and all four DM maps). DM field 149 = the level's music loop (M06: `levelsetup/level/m06_a/music/
   retomotoaction_ambient_v2_loop`), 150 = `fa_all/music/fa_slashmixprison`. Their positional DD
   counterparts are 157 / 158; 157 is 0 in all nine DD levels, but DD's Init still takes it (member
   +0x2a0, 0x88edba), stores it at `[0x168e958]+0x944` and forwards it to 0x8ce720. Whether that
   plays it is **not established** - but it is the first place to try for "its level music plays".
6. **"Squad wiped out" has a stock output.** `ZSquadScript` field 8 (the fifth of its 15 reference
   lists) is used 461 times in 21 DD levels and its targets are called `TC_AllDead` (30),
   `TrC_AllDead` (25), `TC_DeadSquads` (13), `TC_EncounterDone` (71). See section 5.
7. **The Dog Days systems reference the map.** In F01 44 properties of `AllLevels/...equipment.zip\Ammo\*`
   (`ZFFItemTemplateAmmo`) point at `Locations/F01/F01_Locations.zip\Locations/F01/F01_LOC_Inside.zip\
   Effects/ParticleTemplates.zip\Cartridge_Templates_*`. In F02 the group is under `F02_LOC_Outside.zip`,
   in F05 under `AllLevels/.../equipment.zip`. A graft that drops the host's `Locations/` must keep
   that group at the same path. (Outside this track; reported because it was found here.)

## 1. Inventory

Counts over the whole level (layer + map + systems). `.` = none. Columns F01..F09 = DD, M01/M02/M03/M06 =
DM `M0x_FA_A`. Produced by `ctab.py ctrl all` / `ctab.py cls all`.

### 1.1 Present in all nine Dog Days levels

| object (controller unless marked class) | F01 F02 F03 F04 F05 F06 F07 F08 F09 | M01 M02 M03 M06 | role |
|---|---|---|---|
| class `ZOnlineGameplaySettings` + `OnlineFragileAllianceSettings` | 1 each | 1 each | settings, 340 fields (DM 188) |
| `ZSetZDefine` 'IsMultiplayerLevel' | 1 each | 1 each | |
| class `ZSpawnPoint` | 45 55 51 62 58 56 63 45 62 | 21 19 21 18 | see 1.3 |
| class `ZFFPlayer` (`Heroes!Hero_01..08`, `Heroes!RespawnPolice#01..08`) | 16 each | 16 each | player slots |
| `AIMonitor` | 1 each | . | round-start hub (section 2) |
| `FAMissionBriefingTrigger` | 1 each | . | |
| `OnlineExitLevelTrigger` | 1 each | 2 1 1 1 | calls the escape vehicle |
| `OnlineEscVehicleMonitor` | 1 each | . | singleton |
| `OnlineEscCamTrigger` | 9 3 3 6 6 3 6 3 6 | 2 1 1 1 | escape cameras |
| `OnlineGamePlayTrigger` | 6 3 3 6 6 3 5 3 6 | 5 3 4 3 | ENTERS_BANK 1, EXITS_BANK 1, BOARDS 1..4 per DD level |
| `OnlineMoneyCtrl` (+ `TriggerBox2` on the same node) | 183 149 137 135 139 133 138 172 139 | 306 363 340 307 | see 1.4 |
| `TriggerLootDepleted` | 7 each | . | bots only (one per bot squad) |
| `LevelBound` | 6 4 2 5 2 6 6 1 5 | 3 3 5 3 | box + 2 warning boxes |
| `OnlineSpawnpointTrigger` | 2 3 5 3 2 3 3 2 3 | . | team mode: moves the respawn stage |
| `JumpPoint` | 4 3 3 6 5 3 6 6 3 | . | debug teleports (ASSUMPTION) |
| `PointOfInterest` + `ActivateGameplayTrackerDisplay` | 2 each | . | FA_LOOT and FA_ESCAPE markers |
| `CheckMultiplayerTutorial`, `OnscreenMessage` | 2, 3 each | . | tutorial texts, "last van" |
| classes `ZSpeakerDriver`, `ZSpeakerTeamCriminals`, `ZSpeakerTeamPolice` | 1 each | . (not in DM's exe) | prop 18 = 'Driver' / 'TeamCriminals' / 'TeamPolice' |
| `CCameraBox` | 14 9 12 12 11 10 12 8 13 | 3 2 3 3 | spawn cameras, escape cameras |
| `ZSetZDefine` 'MercSpawnCam0','1','2', 'MercSpawnCamPoliceFA' | 1 each | . | spawn cameras found by name |
| `ZSquadScript` / `ZSoldier` / class `ZFFActor` | 30 26 26 36 20 20 29 23 28 / 36..52 / 35..57 | 16 10 15 11 / 12..15 / 14..20 | AI |
| `FFCoverList` (`ZLIST`), `SelectNotify`, `ActionController`, `CheckVisible` | 1 each | 1 each | |
| `TriggerDelay2`, `RandomTrigger` | 44..79, 22..70 | . (not in DM's exe) | scripting glue |

### 1.2 Present in some Dog Days levels (so optional by the stock evidence)

| object | F01 F02 F03 F04 F05 F06 F07 F08 F09 | M01 M02 M03 M06 |
|---|---|---|
| `KillBox` | 9 3 4 4 4 5 4 1 4 | . |
| `OnlineMoneyContainer` | 58 . 12 . . . . 47 . | 1 26 12 . |
| `TriggerActorsDead` | 21 1 7 28 15 21 28 . . | . (not in DM's exe) |
| `TriggerCounter` | 2 . 1 2 1 1 2 2 1 | . 1 1 3 |
| `OnlineEscAnimatedVehicle` + class `ZAnimatedVehicle` + 3x `RelayAnimatedVehicleHit` each | 3 . . 3 3 . 3 . 3 | . (not in DM's exe) |
| `OnlineEscHavokCar` + `OnlineEscVehicleController` | . 1 1 . . 1 . 1 . | 1 1 1 1 |
| `OnlineEscVehicleTime` | . 8 8 . . 8 . 5 . | . |
| `AllyEscapeBox` (heli boarding boxes) | . 8 . . . 8 . 1 . | . |
| `OnlineResetAnimation` | . 1 1 . . 1 . 1 . | . |
| class `ZHeli` | . 3 1 . . 2 . 2 . | . . . 2 |
| `OnlineSpeakPlayer` | 1 1 1 1 . 1 1 . . | . . . 1 |
| `DocuCamControl` | 3 1 1 1 . 2 . 1 . | . |
| `KickDoorMonitor` | 6 . 3 . . . . . . | . |
| `ZCivilian` | 13 10 2 5 . . 2 4 4 | 3 3 5 . |
| class `ZOnlinePIPCameraPoint` | . . . 3 . . . . . | 3 3 9 3 |
| `OnlineCleanUpBox` | . 1 . . . . . . . | . |

Dead Men only: `MapControl` 15 each, `Ingamemap` 2 5 2 2, `IngamemapLoot` 1 5 5 0, `ShowPipCam` 0 0 0 1
(none of the four registered by kl2.exe); `NoCoverBox` 21 91 40 31, `PlayerCoverCollision` 27 2 2 3,
`OnlineVehicleOnSpline` 4 3 4 0, `OnlineTriggerBox` 1 2 4 0, `HavokCarScriptRout` 5 2 6 0,
`VehicleMoveBehaviourRout` 4 3 4 0, `PassengerAnimPos` 16 8 24 0, class `ZHavokCar` 5 2 6 0 (all still
registered by kl2.exe, 0 uses in DD FA levels).

### 1.3 Spawn points (class `ZSpawnPoint`; type = DD prop 8 / DM prop 7, an enum stored by name)

| eSPAWN_TYPE_... | F01 F02 F03 F04 F05 F06 F07 F08 F09 | M01 M02 M03 M06 |
|---|---|---|
| FRAGILE_ALLIANCE_START (criminals) | 8 8 8 8 8 8 8 8 8 | 8 7 8 8 |
| FRAGILE_ALLIANCE_AFTER_DEATH (police respawn) | 7 8 7 7 7 8 7 7 7 | 7 7 7 5 |
| FRAGILE_ALLIANCE_TRAITOR | 4 6 4 4 4 6 4 4 4 | 6 4 6 5 |
| FRAGILE_ALLIANCE_TEAM_MERC | 6 8 6 6 6 6 6 6 6 | DD only |
| ..._TEAM_MERC1 / MERC2 / MERC3 / MERC4 | 3 3 3 4 4 4 4 3 4 / same / . 3 3 4 . 4 4 . 4 / only F03 (3) | DD only |
| FRAGILE_ALLIANCE_TEAM_POLICE | 6 8 6 6 6 8 7 6 6 | DD only |
| FRAGILE_ALLIANCE_UCC_MERC (F07: ..._UCC) | 8 8 8 8 8 8 8 8 8 | DD only |
| ..._UCC_POLICE / ..._UCC_TRAITOR | only F04 F05 F07 F09 (7 / 4) | DD only |
| COMUNISTS | . | . 1 . . |

DM's enum is {ALLIES, COMUNISTS, FA_START, FA_AFTER_DEATH, FA_TRAITOR, ANY}; DD's has no ALLIES /
COMUNISTS. M02 has one `eSPAWN_TYPE_COMUNISTS` spawn where an eighth START is expected: a name DD's
enum table does not hold. DD `ZSpawnPoint` has one more string (prop 9): 'A' on TEAM_MERC, 'B' on
TEAM_MERC1, 'C' on TEAM_MERC2 in F01, empty on the FA types.
What happens when a spawn type has no point: **not established**.

### 1.4 Money (`OnlineMoneyCtrl`, DD fields: 0 game mode, 1 value, 2 type, 3 variant, 4 I, 5 f, 6 b, 7..9 f, 10 I, 11 b)

| game mode / type | F01 F02 F03 F04 F05 F06 F07 F08 F09 | DM (no game-mode field) M01 M02 M03 M06 |
|---|---|---|
| ALL / DROP (pool of dropped stacks, `FASpecials!DropMoney!...`) | 100 100 100 100 108 100 108 100 108 | 300 319 316 303 |
| TM_ONLY / DROP (`...!TeamModeDropMoney!TM_MoneyStack_nnn`) | 25 each | - |
| ALL / CONTAINER (child of an `OnlineMoneyContainer` case) | 58 . 12 . . . . 47 . | 1 38 22 . |
| ALL / NORMAL (loot lying in the map) | . 24 . 10 6 8 5 . 6 | 5 6 2 4 |

So the loot proper is 58 containers in F01, 24 money bags in F02, 5..12 objects in the others; the
100/108 + 25 DROP objects are the pre-allocated pool for money that players drop. Every money object is a
`ZSTDOBJ` with `OnlineMoneyCtrl` and a `TriggerBox2` whose field 0 lists the object itself and field 5 is
'AI_TRIGGER_WITH_ACTIVATOR' (the pick-up trigger).

A container (F01 `...DL10_CtrlRoom\PC0800_F01_Alu_Case_1_01`, `ZGROUP`): `OnlineMoneyContainer`
{0: [`...\Attach_loot_A_00`] (child with `OnlineMoneyCtrl` TYPE_CONTAINER, value 68000), 4: 10,
5: [`...\Box_proxy_for_checkpoints`], 6: 'Activate'} + `TriggerBox2` {0: itself, 2: 125.0, 5: 'Open'} +
two `RelayMessage` ('DoorClosed'->'DoorClosed', 'DoorOpened'->'DoorOpened' to the loot child). Lid and
lock are children with `MatPosAnim` 'Activate', driven through a `MatPosAnimProxy` box.

## 2. Wiring of stock F01 (Subway): start -> loot -> squads -> escape -> end

Real object names; `ROOT\` and the two long prefixes are abbreviated: `<IN>` =
`Locations/F01/F01_Locations.zip\Locations/F01/F01_LOC_Inside.zip`, `<EV1>` =
`Animation/F01/Escape_Vehicle_01.zip\EscapeVehicle_Animation_F01` (02, 03 alike).
`->` = "names it in a reference list" (seen); the meaning of a link is by controller name unless a code
address is given.

```
START   (nothing references these by path; the engine finds them itself)
  FASpecials!Settings!GameSettings [ZOnlineGameplaySettings] @OnlineFragileAllianceSettings
  FASpecials!SpawnPoint!SpawnPoint_FA_Merc_01..08          8 x START      (criminals)
  FASpecials!SpawnPoint!SpawnPoint_FA_Afterdeath_01..07    7 x AFTER_DEATH (police)
  FASpecials!SpawnPoint!SpawnPoint_FA_Traitor_01..04
  FASpecials!SpawnPoint!TeamMode!SpawnCam_000_Startup!Camera_000_Startup
        @ZSetZDefine 'MercSpawnCam0' + @CCameraBox(9 -> ...CameraLookAt_000_Startup, eFMM_LookFromPosFA)
  Gameplay!AIMonitor @AIMonitor list 2 ->
        Gameplay!Blowout!tdExplosion               (the opening, section 4)
        Gameplay!Blowout!tdCivilians               @TriggerDelay 1 -> 9 civilian ...\MiniCutScene
        Gameplay!Timer_MissionBriefing             @TriggerDelay2 0.5 -> Gameplay!FAMissionBriefingTrigger
        Gameplay!PointOfIntrest!Timer_POI_TheLootArea  @TriggerDelay2 11.0 ->
              ...!POI_TheLootArea (@PointOfInterest FA_LOOT + tracker), ...!CheckMPTutorialOption#01
        Gameplay!SecurityGuards#02\00_MiniCutScene_OnFloor   (two guards play /Damage/Death/Die_Forward)
        Gameplay!merc_bot_squad!Timer_start_bots   @TriggerDelay2 10.0 -> Squad#02..08\010_RandomTrigger_...
        Gameplay!MovingTrainSides!tdTrainSides, Gameplay!MovingTrainMiddle!...\Way#01   (set dressing)

LOOT
  Gameplay!otrEnterLootArea  @OnlineGamePlayTrigger eOGPT_PLAYER_ENTERS_BANK   (box 876 x 200 x 156)
  Gameplay!tbEnterVault      @TriggerBox MERCONLY -> Gameplay!tdSwats -> tdSwats#01, #02 (police waves)
  <IN>\DL10_CtrlRoom\PC0800_F01_Alu_Case_c_nn  x58   @OnlineMoneyContainer -> ...\Attach_loot_A_00 @OnlineMoneyCtrl
  Gameplay!TriggerBox_GeomActivator @TriggerBox MERCONLY -> Gameplay!GeomActivator_otrExitLootArea
        @ActivateGeom -> Gameplay!otrExitLootArea  @OnlineGamePlayTrigger eOGPT_PLAYER_EXITS_BANK
        (the exit box starts hidden: node prop 3 = 1; it exists only after somebody went in)
  Gameplay!PointOfIntrest!TriggerBox_POI_EnterLootarea -> Timer_Activate_EscapePOI 3.0 ->
        Gate_POI_Escapearea\Way#01 @GatePath -> POI_TheEscapeArea (@PointOfInterest FA_ESCAPE)

SQUADS  (30 x ZSquadScript: 11 eAllTypes, 8 eFragileAllianceUCC, 11 eHeistOnly)
  Gameplay!tbNearVault_MercOnly  -> Gameplay!SGuard#01\Way#01, SGuard#02\Way#01      (security guards)
  Gameplay!tbPlatform#01_MercOnly-> PlayerCount!tcPlayers#01, PoliceDogs#01\10_Defend,
        PolicePlatform#01\10_Defend, #02\10_Defend, SwatExit#01\11_RunToCover, #02\11_RunToCover, tdSwats_HEIST#01
  Gameplay!tbPlatform#02_MercOnly-> tcPlayers#02, SwatExit#01\20_smUnleash, SwatExit#02\30_smUnleash, ...
  Gameplay!tbExitStairs_MercOnly -> SwatStreet#01\10_Defend, SwatStreet#02\10_Defend
  Gameplay!tbStreet_RespawnOnly  (ECPS_FA_RESPAWNONLY) -> the same routs, for the police side
  Gameplay!PlayerCount!tbPlayerCount__MercOnly (field 2 = 6) -> tcPlayers#01/#02 @TriggerCounter(2)
        -> tdPolice -> PolicePlatform#03\10_Defend     (extra police when many criminals are in)
  A squad = ZGROUP @ZSquadScript, children: behaviour routs (10_Defend @DefendBehaviourRout with Pos#nn
  boxes, 11_RunToCover @RunToCoverBehaviourRout + RunToPosInfo, 30_smUnleash @SquadModifierBehaviour) and
  actor groups (SWAT#01 [ZGROUP] \ Ground [ZFFActor] @ZSoldier). A trigger starts a squad by naming a rout.
  Bots: Gameplay!merc_bot_squad!Squad#02..08, chained by @RandomTrigger, @TriggerActorsDead
        (020_WaitForAllNPCDead: guards -> 020_KickDoorBehaviourRout_loot_room_01#nn) and
        @TriggerLootDepleted (050_Timer_done_looting: 8 cases, 1 = 15 -> 050_SquadModifier_Tight_defense);
        ...!KickdoorMonitor!KickDoorMonitor_Door01..08 @KickDoorMonitor(7 -> <IN>\...Glas_Doors_0n,
        6 -> KickDoor_RelayList_Door0n @RelayMessageList 'AITrigger' -> 'DoorOpened' to that room's cases)

ESCAPE
  Gameplay!otrEnterEscapeArea    @OnlineGamePlayTrigger eOGPT_PLAYER_BOARDS  (+ one per van: <EVn>\Escape_Vehicle_0n\BoardingCar)
  Gameplay!EscapeVan_Anim!otrExitLevel  @OnlineExitLevelTrigger (box 4509 x 187 x 2371)
        0 = false, 1 = '', 2 -> <EV1>, 3 -> <EV2>, 4 -> <EV3>, 5 = ''      (random pick, kl2 0x6c3f90)
  Gameplay!EscapeVan_Anim!EscMonitor    @OnlineEscVehicleMonitor
        3 -> RelayDestroyedEsc_01..03 (@RelayMessage 'AITrigger' -> 'Deactivate' on <EVn>\...\V_Ambulance_00\Audio_Idle)
        8 -> OnScreenMSG_LastEscapeVan ('AllLevels/Interface/Online/Objectives/LastVan'), Timer_OSM_LastEscape
  <EVn> [ZGROUP] @OnlineEscAnimatedVehicle
        0 -> ...\V_Ambulance_00\BoardingTrigger  (@PlayerAction 'EnterVehicle', eOnly_Mercs)
        1..6 = 'Activate_Enter', 'Activate_Exit', 'Activate_Crash_01..04'   (messages)
        7..10 = 181, 332, 426, 466 (frames, EV1)   11 -> ...\Escape_Vehicle_01   12 -> ...\V_Ambulance_00
        13 -> <EVn>\F01_EscapeVan_0n [ZAnimatedVehicle]     14..17 = 11.28, 8.0, 5.84, 4.0
     ...\Escape_Vehicle_01 carries six @MatPosAnimProxy, one per message: Activate_Enter frames 50..332,
        Activate_Exit 358..504, Activate_Crash_01..04 550..603 / 650..689 / 700..771 / 800..851
        (crash ones end in Relay_VanExplotion -> FX0900_ALL_Explosion_Gas_S_01 @Explode)
     ...\V_Ambulance_00\Body\Body_Main, Door_Back_Left, Door_Back_Right  @RelayAnimatedVehicleHit -> the ZAnimatedVehicle
        (Body_Main also @FakeTarget 'Mercenary'), ...\KillBox 'FA_KilledByEscapeVehicle', PathBlockerVan_block
     <EVn>\EscCamera_01\CameraTrigger01, 02, _InVan  @OnlineEscCamTrigger(0 -> the ZAnimatedVehicle, 1 -> a @CCameraBox)

END     no object: the round ends in the game rules (ZGameRulesFragileAlliance[Sv|Cl]) when the criminals
        have left or died or the time is up. Settings fields 143..148, 167..172 are the speech for it.
        Which call ends it: not established.

ALWAYS  Specials!LevelBound!SubwayUpper!Bound#01 @LevelBound(0 -> Warn01#01, 1 -> Warn02#01)   x6
        Specials!CoverPoints!CoverControl [ZLIST] @FFCoverList
        <IN>\...Train_0n\KillBox, Locations/F01/F01_Locations.zip\KillBox (7956 x 1107 x 10903, 'FA_DieFromSelf')
        FASpecials!Speakers!SpeakerDriver / SpeakerTeamCriminals / SpeakerTeamPolice
        FASpecials!DropMoney!...  125 pool stacks
```

Cross-subtree references in F01 (count of reference strings): layer -> map 172 (TriggerLootDepleted 68,
RelayMessageList 58, AIDWrapper 8, ActivateGeom 8, KickDoor* 13, MatPosAnimProxy 6, TriggerBox 6,
DeactivateGeom 3, props 2); layer -> systems 35 (all `ZFFActor` -> `AllLevels/...equipment.zip\Weapon\*`);
systems -> map 44 (finding 7). F02: layer -> map 401. These are what a graft has to re-point or drop.

`OnlineGamePlayTrigger`, `TriggerBox` (`@TriggerBox` field 14 = who may fire it: ECPS_FA_MERCONLY 49,
ECPS_BOTH 141, ECPS_FA_MERC_UCC 19, ECPS_FA_RESPAWNONLY 8, ECPS_FA_UCCONLY 5, ECPS_CP_OFFENSEONLY 4 over
the nine levels; field 16 = game modes, EFAMPS_ALL_MODES 200 of 226; field 17 = targets).

## 3. What is mandatory

Established in code:

| object | evidence | verdict |
|---|---|---|
| `OnlineFragileAllianceSettings` | singleton `[0x168c630]`; unchecked virtual call (+0x90, arg 0xb) at 0x500990 and 0x728ba3 (death cam / respawn text). Init (slot 16, 0x88d780) pushes the values into the managers at `[0x168e958]`, `[0x168e9e4]`, `[0x168e598]` | **mandatory** (crash at the first death at the latest) |
| `OnlineEscVehicleMonitor` | singleton `[0x168cc00]`; `this` not tested in 0x6276e0, reached from `ZOnlineExitLevelTrigger` slot 34 at 0x6c3fc5 / 0x6c3ff8 / 0x6c402b / 0x6c405a. A second monitor deletes the first (0x8d2b63..0x8d2b79) | **mandatory if an exit trigger exists**; exactly one |
| `OnlineExitLevelTrigger` | at least one of fields 2..5 must name a vehicle (loop 0x6c3f90); field 0 = "use field 1 once" (0x6c3f64..0x6c3f86 clears +0x41 afterwards) | without it nothing calls the vehicle; **whether a round can end without one is not established** |
| `AIMonitor` | registered in a table of at most 8 (`[0x168a254]` count, `0x168a258` entries, slot 13 at 0x509ba0; a ninth is silently ignored). 0x8b5f60(event 0/1/2) sends list 0/1/2 of every registered monitor once; with none registered the loop body is skipped | **optional** for the engine; event 2 is raised from `ZFFGameData` slot 10 (0x705309) and 0x46d370. All 30 used lists in 21 DD levels are list 2 |
| unknown controller names | skipped cleanly (0x4f9800, CLAUDE.md) | DM-only controllers can stay or go |

Not established in code (no singleton write found in the class's own vtable functions with `gw.py`;
they register through calls that were not followed): spawn points, `FAMissionBriefingTrigger`,
`OnlineGamePlayTrigger`, `LevelBound`, `PointOfInterest`, the three speaker classes, `JumpPoint`,
`OnlineSpawnpointTrigger`, the `MercSpawnCam*` defines, `OnlineMoneyCtrl`, `Heroes!` players.
For these the only evidence is the census:

- in 9 of 9 DD levels **and** 4 of 4 DM maps: settings, 8 START / 5..8 AFTER_DEATH / 4..6 TRAITOR spawns,
  16 `ZFFPlayer`, `OnlineExitLevelTrigger`, `OnlineEscCamTrigger`, three `OnlineGamePlayTrigger` kinds,
  `LevelBound`, `OnlineMoneyCtrl` pool, `FFCoverList` -> treat as required;
- in 9 of 9 DD levels, in no DM map: `AIMonitor`, `FAMissionBriefingTrigger`, `OnlineEscVehicleMonitor`,
  speakers, `PointOfInterest` x2, `OnscreenMessage` x3, `CheckMultiplayerTutorial` x2, TEAM / UCC spawns,
  `OnlineSpawnpointTrigger`, `JumpPoint`, spawn-camera defines -> DD additions; keep the host's when
  grafting (the monitor is proven needed, the rest is ASSUMPTION);
- missing in some DD level, so optional: `KillBox` (F08 has 1, in the map), `OnlineMoneyContainer`,
  `TriggerActorsDead` (none in F08, F09), `TriggerCounter` (none in F02), `OnlineSpeakPlayer`,
  `DocuCamControl`, `ZCivilian`, either escape-vehicle family.

Safest graft rule that follows: keep the host level's `FASpecials!` / `Specials!` / settings / speakers /
POI / monitor objects, move the positional ones (spawn points, cameras, bounds, trigger boxes, money) into
the new map, and rebuild the squads and the map references.

## 4. How Subway opens "mid-job" (and how to copy it)

All **seen** in F01's objects; the timing semantics are ASSUMPTION (integer field 0 of `TriggerDelay`,
float field 0 of `TriggerDelay2` read as seconds).

- **Where**: the eight START spawn points are top-level nodes at about (7..751, -1714, 13336..13701):
  inside the station, next to the wall that blows. There is no rappel, cutscene or intro animation
  object in the level's start list; `MiniCutsceneRout` is only used for NPCs.
- **Camera**: the spawn camera is the `CCameraBox` under `ZSetZDefine 'MercSpawnCam0'`
  (`FASpecials!SpawnPoint!TeamMode!SpawnCam_000_Startup!Camera_000_Startup`, field 11
  'eFMM_LookFromPosFA', looking at `CameraLookAt_000_Startup`); `MercSpawnCam1/2` (loot, exit) and
  `MercSpawnCamPoliceFA` are the later stages. Start text: settings fields 12 / 13 =
  'AllLevels/Interface/Online/GameStart/F01_FA_Start' (a window in the DD systems, one per stock level).
- **The explosion** (`Gameplay!Blowout!`), started by `AIMonitor` list 2:
  `tdExplosion` @TriggerDelay(3) ->
  - `TriggerBox_DocuCam_Explotion_Mercs` (ECPS_FA_MERCONLY) and `..._UCC` (ECPS_FA_UCCONLY): boxes of
    1860 x 171 x 1221 around the spawn, field 0 = 0 unlike the 1 of ordinary trigger boxes
    (ASSUMPTION: created disabled, enabled by the delay) -> `DocuCam_Explotion`
    (@DocuCamControl 'AITrigger', 'OnExplosion': the hand-held camera's explosion jolt) and
    `awSoundAndSmokeEFX` (@AIDWrapper, message 'Activate', to 3 emitters
    `<IN>\DL10_Platform\Particle_Blowout_01\BlowOut_Emitter_01, _01_stair2, _02` and 4 sounds
    `Locations/F01/F01_Audio.zip\Audio!SFX!Wall_Explosion_Sound, #01, #02, #03` [ZSNDOBJ]);
  - `mpaBombFlash` @MatPosAnimProxy(3 -> `<IN>\DL10_Spawn\Flash_FX`, 5 -> `dgBombFlash`)
    -> @DeactivateGeom `<IN>\DL10_Spawn\BombFlash` [ZOMNILIGHT] (the flash light is switched off after).
  `scExplosion` (@ShakeCamera 3.0, 'Activate', 8000.0) sits in the same group; no object names it.
- **Dressing**: `tdCivilians` (1) starts nine civilian mini-cutscenes (running, screaming, wounded);
  `SecurityGuards#02\00_MiniCutScene_OnFloor` makes two guards play a death animation at start; the
  briefing speech follows 0.5 after start, the loot marker 11 after, the bots 10 after.
- F02 does the same with a train (`Scripting!AIMonitor` -> `Timer_explosion#01`, `GeomActivator_traincrash`,
  `mpap_make_train_arrive#01`, `Group_camera_shake!02_Timer_explosion_shake_delay` 1.5 ->
  trigger boxes -> `03_Box_camera_shake_explosion` @DocuCamControl 'OnExplosion'). Same idiom, 2 of 2
  levels read in detail.

Recipe for a new map, stock objects only: 8 START spawns at the window; one `AIMonitor` whose list 2
names a `TriggerDelay`; that delay names (a) an `AIDWrapper` 'Activate' on the explosion `ZSNDOBJ` +
glass / smoke emitters, (b) a trigger box around the spawn -> `DocuCamControl` 'OnExplosion', (c) an
`ActivateGeom` / `DeactivateGeom` pair swapping intact and broken window. The sound object has to exist
in the level's `.SND` (the map's or the host's): which, is the sound track's question.

## 5. "Loot becomes available when a group of enemies is dead"

No stock FA level does exactly this (seen: all 121 `TriggerActorsDead` in F01..F07 sit in
`merc_bot_squad` and target bot routs, `RandomTrigger`, `SquadModifierBehaviour` or `GatePath`). The parts
exist and each is stock:

**Detecting the deaths** - three ways:
1. `ZSquadScript` field 8 (reference list). ASSUMPTION by names and use, not read in code: fires when the
   squad is wiped out. Stock FA examples: F03 `Gameplay!40_SWAT_Reinforcement_04` field 8 ->
   `Gameplay!40_SWAT_Reinforcement_01\DefendBehaviour` (each reinforcement squad's death starts the
   next); F03 `10_AirportSecurityGuards01` -> `AIDstuff!Gate_CallGuards\Way#01`; F09
   `10_LargeHall!10_Friendly_GetsKilledFirst` -> three `...\Timer` @TriggerDelay2. Story idiom (L01):
   four squads' field 8 -> `Dialogue!Dialogue_SubMarket\TrC_AllDead02` @TriggerCounter(0 = 4) -> a
   checkpoint counter, a `GatePath`, a `MiniCutsceneRout`. Several squads + one `TriggerCounter` whose
   field 0 is the number of squads = "everyone in the room is dead".
2. `TriggerActorsDead` {0: actor groups (the `ZGROUP` parents of the `ZFFActor`s, e.g.
   `Gameplay!SecurityGuards#01\Security_Skyscraber_02`), 1: bool, 2: targets}. Used for actors of
   several squads at once (F01 `Squad#08\100_Left_WaitForAllNPCDead_Left`: 5 actors of 2 squads).
   Not in DM's exe.
3. `TriggerBox` field 13 has the value 'eTGS_AllDead' next to 'eTGS_AllInside' (field 12 = tracked
   objects). **Never used**: 1880 of 1880 trigger boxes in 21 DD levels are eTGS_AllInside. Avoid.

**Releasing the loot** - two stock ways:
- F02: the money objects are switched off at round start and on later. `Scripting!AIMonitor` list 2 ->
  `Scripting!GeomDeactivator_level_start_get_rid_of_ai_relevant_stuff` @DeactivateGeom(1 -> money bags and
  train parts); `Scripting!Timer_swap_the_trains` (12) -> `Scripting!GeomActivator_static_train`
  @ActivateGeom(1 -> `...\Bridge_Train_Tracks_01\PC02_F02_Money_Bags_A_17`.. [ZSTDOBJ @OnlineMoneyCtrl
  ALL/NORMAL 205000]). Those bags have node prop 3 = 1 (start hidden, ASSUMPTION: same flag as
  `otrExitLootArea` in F01); they are the only money objects with it (8 in F02, 0 in the other eight levels).
- F01: containers get 'DoorOpened' from `KickDoor_RelayList_Door0n` when the room's glass door is kicked
  in. Whether a container refuses to open before that message is **not established** (it may only
  inform the bots).

**Proposed wiring** (each link stock, the combination untested): guards' `ZSquadScript` field 8 ->
`TriggerCounter` (field 0 = number of squads) -> a box with `ActivateGeom` {0: 'AITrigger', 1: the loot
objects}, loot objects created hidden or deactivated from `AIMonitor` list 2 as F02 does. `TriggerBox` ->
`ActivateGeom` box -> hidden object is stock in F01 (`TriggerBox_GeomActivator` ->
`GeomActivator_otrExitLootArea` -> `otrExitLootArea`); `TriggerCounter` -> arbitrary targets is stock in
F01 (`tcPlayers#01` -> `tdPolice`).
The statues as loot: a `ZSTDOBJ` with `OnlineMoneyCtrl` ALL/NORMAL + `TriggerBox2` (as F02's bags), the
controller pair added to the statue's node; no stock precedent on a map object from another game.

## 6. Dead Men FA maps -> Dog Days

Layer of a DM FA map (M01): `SpawnPoint!` 21, `DropMoney!` 300 (M06: `Money!` 303), `Triggers!` 16,
`LevelBounds!` 9, `Escape!` 36 (escape car + splines), `EscCameraSetup!` 7, `AI_Enemies!` 175,
`Civilians!` 35, `CivilianCars!` 79, `Player_Cover!` 27, `NoCover!` 20, `CivilFleePoints!` 7,
`Settings!` 6, `Heroes!` 32. No `AIMonitor`, no briefing trigger, no monitor, no speakers, no POI.
Escape in M01: `Triggers!CallExitVehicle_01`, `_02` @OnlineExitLevelTrigger(0 -> `Escape!EscapeCars\EscapeCar`);
`EscapeCar` [ZGROUP] @OnlineEscHavokCar(0 -> `...\VehicleMoveBehaviour_Incomming`, 1 -> `..._Escaping`,
2 -> `Triggers!BoardingTrigger_Car`, 3 -> `...\EscapeCar_OnMap`) + @OnlineEscVehicleController(1 -> an
explosion effect, 2 = a sound offset); the two move routs carry `OnlineVehicleOnSpline`; settings fields
180 / 181 name the same two routs (M06: `EscapeSetup!EscapeChopper\Incomming` / `Escaping`).

Layouts compared field by field with the two schemas (`cmp.py`; kind + enum name per field).

| DM object | DD | what to do |
|---|---|---|
| `TriggerBox2`, `OnlineGamePlayTrigger`, `LevelBound`, `CCameraBox`, `ZSetZDefine`, `OnlineEscHavokCar`, `OnlineMoneyContainer`, `OnlineTriggerBox`, `OnlineVehicleOnSpline`, `VehicleMoveBehaviourRout`, `HavokCarScriptRout`, `PassengerAnimPos`, `NoCoverBox`, `PlayerCoverCollision`, `GatePath`, `GateGroup`, `RelayMessage(List)`, `AIDWrapper`, `MatPosAnim`, `OnlineSpeakPlayer`, `FFCoverList` | same name, same layout | keep as is |
| `OnlineMoneyCtrl` | 10 -> 12: + field 0 enum EZMoneyCtrlGameMode, + field 11 bool | new field 0 = 'ZMONEYCTRL_GAMEMODE_ALL', 11 = false (DD: true on F01's 58 container loot objects only, false on the other 1267) |
| `OnlineExitLevelTrigger` | 1 -> 6 | **vehicle -> field 2, field 0 = false** (finding 1); add a monitor (finding 2) |
| `OnlineEscVehicleController` | 3 -> 4: + reference list | empty list (F02, F06, F08 have 0) |
| `OnlineEscCamTrigger` | 1 -> 2: + string | DM's string is the camera (seen, 5 of 5: `EscCameraSetup!EscCamera01`) -> **DD field 1**; DD field 0 = the `ZAnimatedVehicle` in van levels and empty in helicopter levels (F02: 3 of 3), so leave it empty. Type pairing would put the camera into field 0 |
| `TriggerBox` | 14 -> 18: + bool at 9, + string at 11, + bool 15, + enum EFAModePlayerSetting 16 | new 16 = 'EFAMPS_ALL_MODES', 15 = false; DM's ECoopPlayerSetting value carries over by name |
| `TriggerDelay`, `TriggerCounter`, `ActivateGeom`, `DeactivateGeom`, `DefendBehaviourRout`, `HuntBehaviourRout`, `FlankingBehaviourRout`, `IdleWalkPathRout` | + 1 bool each | false |
| `ZSquadScript` | 17 -> 21: + enum EGameType at 1, + 3 reference lists before the last two | 1 = 'eAllTypes' (or 'eFragileAllianceOnly'); DM list k (fields 3..14) = DD list k (fields 4..15) is the natural pairing, so DM's "all dead" list would be DM field 7: ASSUMPTION |
| `ZSoldier` | 17 -> 23: one I becomes five f, + enum ESRGameType, + bool | AI tuning differs: rebuild actors from a DD squad rather than convert |
| `ZCivilian` | 1 -> 9 | same |
| `SquadModifierBehaviour` | 26 -> 29, enums added and removed | same |
| `PatrolBehaviourRout`, `HeliFlyBehaviourRout`, `VehicleEffects`, `PlayerAction`, `OnlineSpeakTrigger` | changed (+5, +6, +7, +5, +1) | convert by schema; pairings ASSUMED |
| `MapControl`, `Ingamemap`, `IngamemapLoot`, `ShowPipCam` | not registered by kl2.exe | drop (DD has no in-game map) |
| class `ZSpawnPoint` | 8 -> 10: + bool at 5 (every class), + string | types carry over by name; fix M02's COMUNISTS; TEAM / UCC points do not exist in DM and must be authored if those modes are wanted |
| class `ZFFActor` | 23 -> 39 | rebuild from DD |
| class `ZHavokCar`, `ZHeli`, `ZOnlinePIPCameraPoint`, `ZTrafficFlow`, `ZEditorSpline` | + the common bool at 5 (`ZHeli` + 10 more) | convertible; `ZHavokCar` unused by DD FA levels (finding 4) |
| - | `AIMonitor`, `FAMissionBriefingTrigger`, `OnlineEscVehicleMonitor`, 3 speakers, 2 POI + tracker, tutorial messages, `OnlineSpawnpointTrigger`, spawn-camera defines, `TriggerLootDepleted` / bot squads | DD only: take from the host level |

Bottom line: a DM map's positional layer (spawn points, bounds, money, trigger boxes, escape cameras,
gates) converts; its AI (actors, soldiers, squad modifiers) and its escape (exit trigger, monitor, vehicle
family) have to be put into DD's form; its in-game map objects go.

## 7. `ZOnlineFragileAllianceSettings`: Dead Men field -> Dog Days field

Paired by the VALUES of all 4 DM and all 9 DD levels (`sett.py`; both games keep the same order, DD
inserted blocks). Kinds: DM 167 s, 10 f, 7 I, 2 c, 2 refs; DD 316 s, 13 f, 7 I, 2 c, 2 refs.
The integer fields are sound-definition offsets in the level's own `.SND` (finding 5), so they never
carry over as numbers.

| DM | DD | content (DM value -> DD value) | confidence |
|---|---|---|---|
| 0, 1 | 0, 1 | chars 4, 8 in all 13 levels | high (type-exact, same values) |
| 2 | 2 | I, 0 in all 13 | high |
| 3, 4, 5 | 3, 4, 5 | sounds: `take_money`, `take_money_end`, `take_money_police` -> `new_loot/loot_loop`, `new_loot/loot_end`, `grab_loot/car_police_siren_die` (F03: `grab_loot_new/...` x2) | high for 3, 4; medium for 5 |
| 6..11 | 6..11 | floats 0.05, 0.25, 1.0, 0.05, 0.25, 1.0 in all 13 | high |
| - | 12..16 | DD only: start windows `AllLevels/Interface/Online/GameStart/Fxx_FA_Start` (x2), `Fxx_Team_B_Start`, `Fxx_UCC_Start`, `UCC_Start_AsUCC` | - |
| 12..15 | 17..20 | mission briefing (`FA_1time_MissionBriefing<Map>_01_R`, `FA_MissionBriefing<Map>_01..03_R` -> `Multiplayer/Fxx/MissionBriefing_0n_R`) | high |
| 16 | 21 | police briefing | high |
| 17, 18 | 22, 23 | empty in all 13 | medium |
| - | 24..26 | DD only: UCC briefing | - |
| 19..164 | 27..172 (DM index + 8) | 146 fields in identical order, checked group by group: backstab, backstab reply (_R and plain), revenge, personal revenge, rejected, police reward, alliance reminder, shoot-off-money, drop cash (DD: empty in all 9), call escape (+police, +response), shoot escape, heavily damaged, destroyed, boarding, last transport, 3 empty, cash majority, dirty money, jackpot, hitting the score -> reach loot area, exit level -> exit loot area, police kill police, mission reminder, one / two left, you escaped, level bounds (+police), 2 empty, **3 I**, 1 empty, time reminders, time out, all escaped, all dead, player escaped | high for the run as a whole (every non-empty group lines up with the same topic and the three I fields land on the three I fields); medium for single empty fields inside it |
| 149, 150, 151 (inside the run) | 157, 158, 159 | sounds: level music loop, `fa_slashmixprison`, 0 -> 0, `traitorsounds#set` (F02 only, else 0), `traitorsound_01` (0 in F03) | medium: types and position exact; the contents differ (DD has no music), see finding 5 |
| 165..175 | none | 11 tutorial lines `Multiplayer/Tutor/FA_Tutor_*_R`; DD has no such values anywhere in 173..323 | drop (DD shows tutorials as `OnscreenMessage`) |
| - | 173..323 | DD only (151 fields): `HoldEscapeVehicle`, escape-and-player-dead, boarding end, driver bribe / traitor, UCC and team-mode speech; 311..323 empty in all 9 | - |
| 176..179 | four of 324..330 | DM floats differ per map (9/12/10/13, 8/8/12/8, 21/14/10/14, 5/10/12/8); DD 324..328 differ per level (8..15, 8..15, 8..20, 2 or 11, 14..20), 329 = 330 = 10.0 everywhere | **low**: 4 into 7, no value evidence for which |
| 180, 181 | 331, 332 | reference lists: DM = the escape vehicle's incoming / escaping routs; DD = empty in all 9 levels | high for position (the only two lists); DD apparently no longer uses them: leave empty |
| 182..187 | 333..338 | objective texts `Multiplayer/Objectives/LootMoney, Extract, EscapeCar, PoliceKill, CashReward, PoliceCash` -> `AllLevels/Interface/Online/Objectives/Loot, Extract, EscapeCar, PoliceKill, CashReward, PoliceCash` | high |
| - | 339 | DD only: 'Police' in all 9 (the string the death-cam code asks for with index 0xb is in this object; which field: not established) | - |

Use: the pairing shows where each DM value would go, but the values are names of DM speech and GUI
entries that DD's data does not have. For the graft, **start from the host level's settings object** and
change only what is map-specific: 12..15 (start windows), 17..21 (briefing), 127 / 130 (reach / exit loot
area), 136 / 137 (mission reminder), 287 (team police mission), the sound offsets 3..5, 157..159
(re-resolved against the final `.SND`), and the floats 324..328. Fields that differ between DD levels at
all: 3-5, 12-15, 17-21, 27-35, 39-41, 51-53, 60-71, 78-83, 86-94, 96-100, 102-104, 108, 109, 121-127,
130, 133-137, 139-148, 158, 159, 161-164, 167-172, 185-190, 230-232, 278-281, 284, 287, 305, 308,
324-328; most of those are only a different pick among numbered variants of the same line.

## 8. Open

- What ends a round and what a missing spawn type does (game rules, not followed).
- Whether DD plays settings field 157 (0x8ce720).
- Whether a container needs 'DoorOpened' before it can be looted.
- Meaning of `OnlineEscVehicleMonitor` fields 0..8 beyond the names of their targets (0: ladder / door
  animation, 2 and 3: clean-up lists, 8: "last vehicle" message) and of its four float + list pairs
  (9..16, -1.0 and empty everywhere).
- `AIMonitor` events 0 and 1 (callers 0x490840, 0x708a69): no stock level uses them.
- Whether the DM spline car works in DD (finding 4), and where a `ZAnimatedVehicle`'s frames are stored.
- The start windows `Fxx_FA_Start` are per stock level: a new map reuses one or needs a new window in
  the systems.
