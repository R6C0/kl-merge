# Retomoto Tower: the Fragile Alliance layer

2026-10-09, agent f-retomoto. Sections 0 - 8 were written **offline** (nothing installed, the game not
started). **Section 9 is the live outcome** (agent h-live, same day): the level loads, a round starts on
it, and it corrects sections 2 - 4 where they were wrong (facing, the join, road height, the cover list).
**Section 11 (offline again) is the owner's new start: outside on the balcony, then the blast.** It replaces
the START row, the blast timing, the one-wave tower and the door timing of sections 1 - 6.
Tool: `tools/kl_fa_author.py`. Builds on `re/retomoto.md` (the survey), `re/maps.md` (the two-part
build), `re/fa_gamemode.md` / `re/fa_round.md` (what a round needs), `re/havok.md`, `re/netcode.md`.

Words: **read** = read off kl2.exe (address given) or the level files; **GUESS** = a value of mine,
not copied from a stock object; **ASSUMPTION** = fits the evidence, not proven; **LIVE** = only a
run in the game can settle it (section 8 orders them).

    python tools/kl_fa_author.py test <out> [--keep]   build F07 + M09_B + M09_A with the layer, verify,
                                                       kl_fa.check, print the inventory (80 s)
    python tools/kl_fa_author.py plan                  which campaign squads stay and why
    python tools/kl_fa_author.py vans                  the three baked van drives against the road
    python tools/kl_fa_author.py inventory <archive>   the inventory of a built level

## 0. Result

`test` (run twice, last 2026-10-09): one archive, **25,490 entities, 22 rooms, 2,195 textures, 1,429
materials, 4,941 sounds / 4,766 waves, 331 MB**, both navigation meshes, A's FDX block.
- `kl_graft.verify`: **2 problems, both known and not of this layer** (re/maps.md patches 2 and 3):
  "39 particle template names do not resolve (stock M09_A: 36)" (B's three `Impacts_Default_Smoke`
  emitters, a false count in a chain) and "15 stream clips are not in the merged stream file".
  Every other check passes: 0 dangling scene paths, 0 misfits, no top-level name twice.
- `kl_fa.check`: **0 CRASH, 0 BROKEN**, one DEGRADED (no bot squads). Before the layer: 1 CRASH, 9 BROKEN.
- Read back from the written archive: 8 START / 4 TRAITOR / 7 AFTER_DEATH (+ 19 UCC, 18 team-mode
  merc, 7 team police) spawn points at the table's coordinates with the facing in both the .prp and
  the .gms; 21 loot objects (15 visible, 6 with ZGEOM[3] = 1 and flag 0x400), 4,050,000; drop pools
  100 + 12; exit trigger fields 2..4 = the three vans; 33 squads / 63 actors, all named by a starter.

No entity and no controller is created: every object is a stock one that kl_graft keeps
(`Select(s_keep)`), re-placed and re-wired. That is why nothing in the id spaces had to be touched.

## 1. Design, as the owner gave it and as it is built

| owner | built |
|---|---|
| heisters already rappelled down at the main window | 8 START points in a row 2 m inside the window (x 5650, y 20996, z -700..700), facing into the boardroom. Inside, not on the rope: whether anything outside the glass can be stood on is not established |
| explosion as the round begins | round-start event -> 1 s -> the campaign's own bomb `WindowBlowup!BombWindow03` (its particles `AllocMany_BigWindow_M09`, its two sounds) + the window's own `ShotActivate` forced + the campaign's chair and door swaps |
| part 1: loot from the statues | one money stack at each of the 15 samurai cases, 150,000 each |
| ... and from the main room once everyone in it is dead | 6 stacks on the boardroom table, 300,000 each, hidden; the two boardroom squads' 'wiped out' lists -> counter (2) -> `ActivateGeom` |
| the join | the campaign's own escape elevator: a trigger box in the tower car fires a `JumpPoint` in the lobby car (section 3) |
| part 2: out through the front entrance, down the road to a van | street police start when a criminal passes the entrance; F07's three animated vans re-laid along the road, stops 150 - 165 m north of the door |
| its level music plays | the campaign's `Music!PlayMusic_TokyoAction` is kept and started with the blast; **silent until its two clips are in the merged PC_Def.str** (section 6) |

## 2. Inventory: what exists, what it is cloned from, what was changed

"Kept" = F07's own top-level object, kept by name. Positions: `kl_fa_author.PLACE` and the tables
above it; each entry names its source. `python kl_fa_author.py inventory <archive>` prints all of
it with coordinates read back from the level (about 300 lines; the lists below are the summary).

| what | stock object (F07 unless marked) | changed |
|---|---|---|
| settings | `FASpecials!Settings!GameSettings` (`ZOnlineGameplaySettings` + `OnlineFragileAllianceSettings`, 340 fields) | nothing: F07's lines, start windows `F07_FA_Start`, briefing `Multiplayer/F07/MissionBriefing_0n_R`. Field 157 (music) stays 0 |
| define | `FASpecials!Settings!IsMultiplayerLevel` (`ZSetZDefine`) | nothing |
| speakers, briefing, monitors | `FASpecials!Speakers!*`, `FAMissionBriefingTrigger`, `Timer_MissionBriefing`, `Gameplay!AIMonitor`, `Gameplay!EscapeSetup!OnlineEscapeVehicleMonitor` (what `kl_fa.host_keep` keeps anyway) | AIMonitor list 2 += the blast timer |
| 8 START | `FASpecials!SpawnPoint!SpawnPoint_Start_01..08` | (5650, 20996, z), z = -700, -500 .. 700; facing (-1, 0). GUESS: the row. Floor proven by the campaign (a guard at (5770, 21012, -347), `InvisiBomb` at (5685, 20997, -394)) |
| 4 TRAITOR | `..._Start_Traitor_01..04` | (5700, 20996, -600 / -200 / 200 / 600). GUESS |
| 7 AFTER_DEATH (police) | `SpawnPoint_Dead_01..07` | elevator lobby (1904 19601 818), (1800 19601 812), (1987 19601 973); atrium lift (-1764 19613 -61), (-1508 19613 -147); square (447 26 -7956), (-367 26 -7594): start positions of campaign actors that are NOT kept |
| UCC 8 + 7 + 4, team 6 + 4 + 4 + 4, team police 7 | `FASpecials!SpawnPoint!UCC!*`, `...TeamMode!*` | by kind (`SPAWN`): beside the rows above; team stages B / C / D = reception, elevator lobby, Retomoto lobby (campaign actor positions; two lobby points GUESS) |
| 16 player groups | `Heroes!Hero_01..08`, `Heroes!Henchmen_01..08` (systems) | the START row / the police points + 160 in z. A direct boot starts at Hero_01 |
| spawn cameras | `SpawnCam_000_A / 010_B / 020_C / 030_D / 100_Police / 000_Police_FA` (camera + look-at, `MercSpawnCam*` defines) | all GUESS |
| team-mode stage triggers | `SpawnpointTrigger_010_B / 020_C / 030_D` | boardroom door, elevator lobby, lobby. GUESS |
| loot marker, enter / exit | `FASpecials!POI!POI_TheLootArea`, `Trigger_POI_TheLootArea`, `PIP!EnterLootArea` (ENTERS_BANK), `PIP!ExitLootArea` (EXITS_BANK) | boardroom centre; box round the START row; a plane 3 m into the room; a plane across the lobby. GUESS |
| loot at the statues | 15 pool stacks `FASpecials!DropMoney!MoneyStack_101..108` + `TeamModeDropMoney!TM_MoneyStack_013..019` | at the 15 cases' own origins; `OnlineMoneyCtrl` = stock F02's bag values (ALL, NORMAL, VARIANT_NORMAL, 15000, 0.2, 1, 30, 800, 1000, 0, 0) with value 150,000; `TriggerBox2` radius 150 (GUESS; F02: 80) |
| loot of the main room | 6 pool stacks `TM_MoneyStack_020..025` | (4750 / 5000 / 5250, 21076, -120 / 20): GUESS, the table top. Same controller values, 300,000; ZGEOM[3] = 1 + flag 0x400 |
| 'room cleared' | `Gameplay!020_Loot!FollowPlayers!TriggerCounter`, `Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT` (`ActivateGeom`) | counter (2, -1, 1, 0, [the activator]); activator ('AITrigger', the 6 stacks) |
| level bounds, tower | `Specials!LevelBound!040_LevelBound_AlleyTop!Bound / Warn01 / Warn02` | a slab outside the blown window, x 6000..7300, y 17900..23100, z -2300..2100; warning from x 5880. GUESS |
| level bounds, street | the campaign's own (kept by `kl_maps.campaign_drop`): `Enemies!020_Street!LevelBound_North` (z 13418), `..._South` (four, z -11400..-12700), `Enemies!010_RetoBldFront!LevelBound` (x 7466, behind the lobby), three at the bus terminal; + `Specials!LevelBound!030_LevelBound_StreetLeft` at x -7800..-7000, z -2000..8000 | the west side (overpass, bus terminal) is open in the campaign: GUESS where the slab has to stand. F07's four other bounds are parked at y -60000 |
| round start | `Gameplay!010_FirstFight!RivalMercVan!Timer` (`TriggerDelay2`), `...Activator_VanSound`, `...Activator_OLD_VanGo` (`AIDWrapper`) | timer 1.0 s (GUESS) -> wrapper 'Activate' -> the bomb; wrapper 'ForceTriggerShotActivate' -> the intact window; + 7 campaign objects and 23 squad starters |
| street police starter | `Gameplay!030_AfterLoot!tbExitFinancialAlley` (`TriggerBox`, ECPS_FA_MERCONLY) | (2900, 400, -6500) half (300, 400, 800): inside the entrance; targets = 10 squad starters |
| the join | `Specials!LevelSpeak!TriggerBox` (+ its speech object), `Specials!JumpPoints!06_Exit` | section 3 |
| exit trigger | `Gameplay!EscapeSetup!otrExitLevel` (`OnlineExitLevelTrigger`) | (-3000, 500, 7800) half (2700, 900, 3500) (F07: 3542 x 953 x 3567, 16 m from its stops); fields 2..4 = the vans that fit |
| vans | `Animation/F07/F07_Escape_Vehicle_01..03.zip` (223 entities each: `ZAnimatedVehicle`, `OnlineEscAnimatedVehicle`, boarding `PlayerAction`, BOARDS trigger, cameras, kill box, path blocker) | the group `EscapeVehicle_Animation_F07` of each gets one rigid transform (section 4) |
| escape marker | `FASpecials!POI!POI_TheEscapeArea`, `Trigger_POI_TheEscapeArea*` | at the first van's stop; the triggers = the lobby's bound |
| jump points | `Specials!JumpPoints!01..05` | the START row and the campaign's `Markup!Jump_03..06` |
| escape music, sound relays, 'last van' message | `Specials!Audio!EscSoundHandling!*`, `Gameplay!EscapeSetup!*` | nothing |

Kept from the campaign levels beyond `kl_maps.campaign_drop` (`CAMPAIGN_KEEP`, all single nodes):
M09_A `WindowBlowup!BombWindow03`, `AI_Players!Enemies!020_Office!GeomActivator_ChairPost`,
`GeomDeactivator_ChairsPre`, `GeomActivator_BrokenDoors`, `GeomDeactivator_Doors`,
`AI_Players!Enemies!070_Elevators!AnimProxy_OpenEscapeElevator`, `Music!PlayMusic_TokyoAction`;
M09_B `Mercenaries!VideoProxy!MatPosAnimProxy` (the lobby car's doors); and the squads of section 5.

Facts the tables rest on (read from the files):
- **Rotation**: ZGEOM[1] = [third, second, first column] of the local matrix; facing (dx, dz) is
  [dx 0 dz, 0 1 0, dz 0 -dx]. That facing = local +Z is an ASSUMPTION (F07's START points are
  identity = +z, the way to its loot; M09_A's `Markup!Jump_02` outside the window holds (-1, 0)).
- **Boxes**: ZBoxPrimitive[0..2] are half extents (F07 `040_LevelBound_AlleyTop`: bound centre + half
  = 26154.06, warn centre + half = 26153.9).
- **Hidden at load**: ZGEOM[3] = 1 with .gms flag 0x400. F02's eight late money bags (0x2205f2 against
  0x2201f2), and in M09_A the blown window `..._Geom_Post_00`, `Chairs_Post!*`, `DDoor_Broken_01`.
  So at load M09_A shows the INTACT window, chairs at the table and a CLOSED boardroom door; the
  campaign's own activators (kept, fired at the blast) put the room into its blown state. Without
  them the heisters could not leave the boardroom.
- **Pool stacks** have no Havok shape (F07's .HVK: 0 placements under `FASpecials!`), so moving them
  touches no other file. GUESS: that the pool model (chunk 1802) serves as loot that lies still.
  F07 has 108 + 25 pool stacks, six stock levels have 100 + 25; 100 + 12 are left.
- `ShotActivate` field 10 is the message that forces it: 'ForceTriggerShotActivate' on every one of
  M09_A's (the window chain Pre -> A -> B -> C -> Post and its sounds hang on it).

## 3. The join between tower (y 19,600) and lobby (y 560)

### 3.1 The candidates

| candidate | evidence | verdict |
|---|---|---|
| **`JumpPoint` fired by a trigger box** | **read, new**: `ZJumpPoint` (vtable 0xbc268c) registers the message 'AITrigger' (0x74a8de, "ff2\levelsetup\jumppoint.cpp", id at 0x1689020). Init (slot 13, 0x6e6620) enters the node's name, position and matrix in the game data's jump list (0x6c0730; 32-byte entries at gamedata+0x8c4). Its message handler (slot 26, 0x491e20): on 'AITrigger' `gamedata+0x8d4 = own index`, `[0x156b35c] = 1`. `ZFFGameData`'s update (0x4bca90) calls 0x57e110 every frame (0x4bd124, unconditional): with the request set it takes the entry and calls **0x8f3fa0(matrix, position, flag)**, which loops over local player 0 and 1 (0x660b00: `gamedata+0x828[byte gamedata+0x898+i]`), skips a player that is not active (flag bit 10 of its entity, or +0xd44 set), sets its transform through its position object (vtable +0x8c) and resets its movement state; with the flag also the members of the player's crew (+0xcd0 -> +0xa4 list, 0x62a900). Then 0x72e0f0 sends 'AITrigger' to the jump point's own reference list (Dog Days field 0). The debug request `[0x156b358]` has no writer left in retail; the message path is intact | **recommended, implemented** |
| `TeleportList` (`CTelePortList`, on a ZLIST; an int and a string) | read: Init (0x711c20) only registers the object under the name "rTeleportList" with a manager (`[0xdd2640]+0xac`, vtable +0x40); slot 26 returns 0 (no message). 0 uses in 21 Dog Days and 20 Dead Men levels | not a mover by anything read; dropped |
| `MoveTo` (`ZMoveTo`, one string) | 20 - 129 per stock level, on sound objects and pickups, always naming a ROOM | assigns an object to a room; not a teleport |
| `Elevator` (`ZElevator`) | 1 use in either game (M09_A's atrium lift); moves a car inside one shaft | not between two places |
| `OnlineSpawnpointTrigger` | 2 - 5 per stock FA level; (bool, spawn type, team) | moves the team-mode RESPAWN stage, not the living. Used for exactly that (stage B / C / D) |
| lower the tower onto the lobby | B = A + (3298, -19040, -7214) joins the two cars (same model, same rotation). Cost of moving A: every baked file in world space - .oct trees and records, .rmi / .rmc boxes, 24 gates, navigation mesh, every static Havok placement with its MOPP code and the list codes (re/havok.md rule 7: all world-space; the builder in kl2 is stripped of its save step), FDX, lights; and the plans do not register (A's interior is 8800 long against a 7020 shell, its main window would be on the back face - re/retomoto.md 2.2), and 186 m of floors between are not modelled | no |
| fade + reposition from KLHook | works without level data | not a level feature; a code patch kills a real round (re/fa_round.md 5.3) |

Stock use of `JumpPoint`: 3 - 6 in every FA level and in ten story levels (L01..L08, L10, L11);
**none is named by any object** (21 levels searched) (they are the developers' jump list; the story ones carry lists that fire the triggers a
jump skips). So the code path is stock, its use from a trigger is new: LIVE.

### 3.2 What is built

- `Specials!LevelSpeak!TriggerBox` -> centre (2972, 19730, 909), half (170, 130, 120): the inside of
  the campaign's escape car `SI0101_JPN_Elevator_Int_A_03` (box (2756 19600 756)-(3189 19873 1062)).
  Field 14 = `ECPS_BOTH` (police have to come down too; stock: MERCONLY), field 17 = the jump point
  and F07's 'exit heist' line. Fields 0..2 = 1, 1, 1 and 10 = -1 as stock (ASSUMPTION: it fires
  every time somebody enters).
- `Specials!JumpPoints!06_Exit` -> (6272, 563, -6305), facing (-1, 0): the campaign's arrival car
  `..._Int_A_00` in `M09_B_Lobby_RetoMoto_Elevators_01a`, door at x 6112.
- Both cars' doors are opened at the blast by the campaign's own proxies (`MatPosAnimProxy` frames
  0..75 on `Ext_A_03 / Int_A_03` and on `Ext_A_00 / Int_A_00`). Opened at round start and not when
  the room is cleared: if the 'wiped out' list does not fire, nobody may be locked in the tower.
- No navigation link joins the parts (`kl_maps.nav_join`): AI stays on its side. Police who respawn in
  the tower ride the same car; 2 of the 7 AFTER_DEATH points are on the square already.

### 3.3 What multiplayer makes of it (not established; LIVE)

0x8f3fa0 moves the LOCAL players of the machine that handles the message. Arcade has one human:
that works by what was read. Online it depends on where a `TriggerBox` raises 'AITrigger':
- on every machine (the box is evaluated for every player everywhere): everybody jumps when the
  first heister enters the car - police and heisters still at the statues too. Acceptable as "the
  elevator leaves", but a policeman standing in the lobby would be thrown into the car as well;
- only on the machine of the player who entered: exactly right;
- only on the server: only the host is ever moved. Then the hand-over has to be spawn-side
  (AFTER_DEATH in the street only) or the round split into two maps (re/maps.md 5.6).
Player movement is owner-authoritative (re/netcode.md 8.1), so a local jump replicates as a position.

## 4. The escape van

`python kl_fa_author.py vans`. F07's vans are `ZGROUP 'V_Van_00'` + `MatPosAnim`; the drive is key
data in the .buf: the group's KEYS chunk names six tracks, the last a table of positions in the
order they are driven (563 / 469 / 534 positions; pieces = the drive in and away, then the crash
variants). **The path is baked, but in the node's LOCAL space**: every parent of the van is
identity at the origin in stock, which is why the table reads as F07 world coordinates (first
entry = the node's own ZGEOM[2]). The four bit-packed index tracks (frame -> key) are not decoded.

So the drive can be re-laid by one rigid transform of a parent. Applied to `EscapeVehicle_Animation_F07`
(everything with a place is below it: van, boarding box, BOARDS trigger, cameras, path blocker,
door trigger), not to the top-level group: its other child `V_Van_Reflection` has **9 static
Havok placements per van at F07's origin** ((-4.5, 0, 0) m), which stay in the MOPP whatever the
entity does.

| van | drive | bend | fitted across the road (x -5400..-600) | stop | waits at | drives z |
|---|---|---|---|---|---|---|
| 01 | 121 m | L-shaped in F07 | 37.3 m wide, x -4866..-1133 | (-1567, 5, 9300) | (-4866, 5, 6688) | 6368..13928 |
| 02 | 138 m | 36 degrees | 28.7 m, x -4433..-1566 | (-1562, 5, 8500) | (-3227, 5, 3432) | 3431..14205 |
| 03 | 152 m | 51 degrees | 28.1 m, x -4405..-1594 | (-4164, 5, 7700) | (-1594, 5, 1101) | 1057..12269 |

All three fit the 54 m carriageway (the crash pieces reach x -5766). What the fit cannot know:
- the vans stand in sight on the road from the start (in F07 they wait in side streets), and their
  drives pass through the campaign's static police cars (first road block z 3602..3911, far block
  z 13131..14404) and through the north level bound (z 13418) on the way out: they are key-framed,
  nothing stops them. Whether that reads as "ramming the cordon" or as a fault is for the eye;
- road height: y 5 at the stops is the y of the campaign's static cars (GUESS; actors there stand
  at y 3..14);
- the stops (z 9300 / 8500 / 7700) are GUESSES: 150 - 165 m from the front entrance;
- the 9 + 9 + 9 static van shapes at world (-450, 0, 0): in F07 that is outside the map; in Retomoto
  it is the east edge of the road at z 0. **An invisible van-sized obstacle may stand there** (LIVE).
  Fix if so: `kl_hvk.join` drops static placements of S whose entity is `V_Van_Reflection\*`
  (rule 4 of re/havok.md), or S's static part is left out altogether;
- the key-framed bodies' placements in the .HVK hold F07 positions in metres (59, -2, 256); a
  key-framed body follows its entity (re/havok.md type 4), ASSUMPTION that the first frame corrects it.

Alternatives, if the baked van fails on this road: (1) one van only (set fields 3 / 4 of the exit
trigger to '' in `prepare_host`); (2) a helicopter from F08 as S (`ZHeli` + `OnlineEscHavokCar` +
fly routs, re/maps.md 3.2) - but the owner asked for a van; (3) Dead Men's spline car
(`ZHavokCar` + `OnlineVehicleOnSpline`), unproven in Dog Days and M09_B has no FA spline; (4) the
campaign's own `V_USA_GetawayVan_Chase_00` as static scenery at the stop with the F07 van hidden.

## 5. AI

`python kl_fa_author.py plan`. Rule (`squad_plan`): a campaign squad stays when its subtree holds
only squad objects (`ZSquadScript`, `ZSoldier`, behaviour routs, `SquadModifierBehaviour`, and
trigger / delay / counter boxes), at least one actor and one behaviour rout; the campaign's
mini-cutscene controllers (`MiniCutsceneRout`, `MiniCutSlot`, `MiniCutPosObject`, `MiniCutSignal`,
`MiniCutItemProxy`) are taken off it before the join (45 controllers). Its starter = the
lowest-named behaviour rout the campaign's own triggers name.

| part | stay | actors | start | do not stay |
|---|---:|---:|---|---|
| M09_A | 23 squads | 43 | at the blast (the blast timer names each rout) | 9: `Squad_AroundTable`, `Squad_Retomoto`, `Guards_Inside_04`, reception MG (mini-cutscene only, no rout left), `Squad_StormOffice` (`Cage`), the three that arrive by elevator, `Guards_Inside_01` (stands where the heisters spawn; the campaign kills him with the blast) |
| M09_B | 10 squads | 20 | when a criminal passes the front entrance | 24: every `VSquad_*` (police cars on roads, `ZHavokCar`), squads with `Blocker` / `GateGroup` / `AttachGeomToBone` / `WarnBehaviourRout`, mini-cutscene-only ones |

- **Main room**: the boardroom keeps `Squad_Guards_Inside_02` (4) and `_03` (3), who stand at its door
  end (x 3596..4101). Their `ZSquadScript` field 8 -> the counter. That field 8 is the 'wiped out'
  list is now better than a name guess: after conversion the campaign's own squads hold exactly
  their 'all dead' counters there (`TrC_AllDead`, `TriggerCounter_AllDeadElevator`,
  `TriggerCounter_Office_Squads_Die`). The code that sends it was still not read.
- The actors are Dead Men's (yakuza guards in the tower, Japanese police and SWAT in the street) with
  their own models; converted actors fought in the live bank round (re/fa_round.md 5.4). Weapons
  re-pointed by `kl_graft.dm_rename` (guesses there: `HG_HK_USP_01` -> `HG_M9Beretta_Human_Shield`,
  `Mg_Minimi_SPW_01` -> `Mg_Minimi_SPW_L10_Heli`); animation set 'Bouncer' is a copy of 'Thug'
  (kl_anmjoin's guess); material `Characters/_JPN/JPN_Police_LOD3` has no compiled shader.
- **Police respawn**: a dead criminal gets the first free type-3 `ZFFPlayer` (kl2 0x6ee860,
  re/netcode.md 10): F07's eight `Heroes!Henchmen_0n`, kept and placed at the police points.
- Not built: Fragile Alliance waves (F07's 14 police squads are tied to its alleys; re-placing a
  squad means re-placing each defend box and cover position), heist-only extra squads, the bot crew
  (`merc_bot_squad`, 8 x 99 nodes tied to F07's doors): Arcade is one player against the 63.
  Next step for waves: F07's `Gameplay!020_Loot!*` squads moved as rigid groups to the first road
  block, their actors on campaign actor positions.

## 6. Window, music, sound

- The blast: `AIMonitor` list 2 -> `TriggerDelay2` 1.0 s -> (a) `AIDWrapper` 'Activate' ->
  `WindowBlowup!BombWindow03` (`Explode`: particle group, sounds `Bomb_WarmUp` + `M09_Explosion_Window_Office_01`);
  (b) `AIDWrapper` 'ForceTriggerShotActivate' -> the intact window (swaps to the blown state, plays
  `Glass_Break_Big`); (c) the chair and door swaps; (d) both elevator door proxies; (e) the music;
  (f) the tower squads. The same idiom as stock F01's `Gameplay!Blowout!` (re/fa_gamemode.md 4).
- **GUESS**: the bomb's `CExplode` fields 0 / 1 (600, 400) are set to 1: the heisters stand 2 m from
  it (the campaign's 'kill the player at the bomb' box has 80, 80 there). Fields 2..4 (200, 2000,
  3000) are untouched; what each is, is not established. `BLAST_HARMLESS = False` leaves the bomb as it is.
- The bomb's model is hidden at load (ZGEOM[3] = 1) and its material `Weapons/BombWindow_02` has no
  compiled shader: it is not drawn either way.
- **Music**: `Music!PlayMusic_TokyoAction` (`PlayMusic`, layers `TakyoAction_V3_44_Layer1_Loop` +
  `TakyoAction_Layer2_TAmbient_Loop`: the theme the campaign starts at this very blast) is kept;
  its sound fields ride through `kl_snd.graft_audio` like any map node's. It is sent 'AITrigger' by
  the blast timer - ASSUMPTION that this starts it (the campaign starts it from a `TriggerDelay`,
  `Music!06_Explosion`). No FA level of either game has a `PlayMusic`: LIVE. The other route,
  settings field 157, needs the clip's offset in the final .SND, which only exists after
  `graft_audio`: a job for kl_graft, three lines once the clip is in the bank.
- **Stream clips the merged PC_Def.str lacks** (verify's second problem; a wave without its clip is
  dropped, so the object is silent, not broken): the two music layers, `Bomb_WarmUp`, A's three
  ambience beds, the emergency announcement, two guard shouts, eight Japanese guard / police lines;
  in B five police warnings, two coughs, four ambience beds. `kl_audio.merge` patch 3 of re/maps.md
  covers them when `Music/InHouse/Japan/M09_A/` and `Dialog/AllLevels/Oneliners/Japanese/` are added.
  The window explosion clip itself is NOT among the missing.

## 7. For the lead: integration, and what other files need

`authoring()` patches five names from outside for the length of a build (`kl_graft.Level`,
`kl_graft.DeadMen`, `kl_graft.Select`, `kl_fa.repair`, `kl_maps.campaign_drop`) and restores them.
Native, in `kl_graft.build`:

    S = Level(s_name);  if retomoto: kl_fa_author.prepare_host(S, log)          # before picks_of
    sel = Select(..., s_keep=tuple(sel.s_keep) + kl_fa_author.KEEP)
    kl_fa.repair(Jn, kept + kept names of the layer, log);  kl_fa_author.wire(Jn, log)   # after the last join

and in `kl_maps.campaign_drop`: leave `kl_fa_author.campaign_names(level)`; in `DeadMen.__init__`:
take the `STRIP` controllers off the squads `kl_fa_author.plan(level)[0]` names.

- `kl_fa.repair`'s `prune` cuts references that do not resolve YET: in a chain everything that
  names the second map has to be written after the second join. `wire()` does that.
- `kl_fa.controllers(sc, 'AIMonitor')[0]` is not the host's monitor once a map brings one (M09_B's
  map has an `AIMonitor`): go by node.
- Other agents' files, not touched: re/maps.md patches 2 (particle baseline) and 3 (stream clips)
  remove the two remaining problems; `kl_hvk.join` and the vans' static shapes (section 4).
- re/retomoto.md 2.4 says "no teleport is proven": `JumpPoint` is the one the exe supports (3.1).
- re/fa_gamemode.md 1.1 calls `JumpPoint` "debug teleports (ASSUMPTION)": read now, see 3.1.

## 8. What only a live run can settle, in the order to test

(Outcome of steps 1, 2, 4 (start only), 5, 8, 9 (walk only): section 9.)

Each step needs the one before. A direct boot (`-o DefaultScene`) shows 1 - 3; the rest needs a
round from the menu (klhook\KLHook.round.ini).

1. **The chain loads at all** (re/maps.md 6.3: three static Havok parts, `nav_join`, no .hrd) - direct
   boot. With this layer the player must stand at (5650, 20996, -700) in the boardroom, facing the
   table. Facing the window instead = the facing assumption is wrong: negate `IN` and the others.
2. **The boardroom at load**: intact window, chairs at the table, closed door (no round-start event
   in a direct boot, so nothing blows). Money stacks visible at the samurai cases? (walk: reception
   -> atrium is closed until the door swap, so this may need the round.)
3. **Hidden things have no collision** (the hidden six stacks, the hidden broken door) - walk the table.
4. **Round start** (menu route): does the blast come 1 s in - particles, glass sound, window gone,
   chairs thrown, door broken open? Is anyone hurt by it? Does `PlayMusic` start (after the clips
   are merged)? Briefing voice is F07's.
5. **Guards**: do the 43 tower guards react when their rout is named at the blast, and do the 7 in
   the boardroom come at the player?
6. **Statue loot**: can a stack at a case be taken (through or after breaking the glass; radius 150)?
   Does the bag fill, does 'Looting has started' come up at the ENTERS_BANK plane?
7. **Main room**: kill the 7; do the six stacks appear on the table? If not: `GATE_MAIN_ROOM = False`
   and read `ZSquadScript`'s sender for field 8. Are they ON the table (y 21076)?
8. **The join**: walk into the open escape car at (2972, 19600, 909). Are its doors open? Does the
   player stand in the lobby car a frame later, doors open, facing out? Does it fire again for a
   second entry? (Online: section 3.3, with two machines.)
9. **Street**: do the 20 police start at the entrance; level-bound warnings north / south / west;
   is the west slab (x -7800..-7000) where the play space should end?
10. **Vans**: where do the three stand at round start; does entering the exit box (z 4300..11300 on
    the road) call one; does it drive along the road, stop at its path blocker, open, take the
    player, leave? Invisible obstacle at (-450, 0, 0)? Escape camera, 'last van' message.
11. **Death -> police**: respawn at a police point (5 in the tower, 2 on the square) as a Henchmen
    body; can a policeman reach the heisters (tower car)? In Arcade the round ends at the first
    death (re/fa_round.md 5.4), so this needs a second player or the team modes.
12. **Round end and score page**; then Cops & Robbers / Undercover Cop spawn sets, spawn cameras
    (all GUESS positions), 12 team-mode drop stacks instead of 25.

## 9. Live outcome (2026-10-09, agent h-live; runs RT1 - RT6 in `tools/kl_graft.py`'s run log)

Build: `python tools/kl_fa_author.py test <out> --keep` (now native: `kl_graft.build(author=True)`,
`kl_maps.py chain ... --author`; the monkey-patching of section 7 is gone). `--no-ai` builds the level
without the campaign squads for scripted walks. Verify: the same **2 known problems** remain
("39 particle template names do not resolve (stock M09_A: 36)", "13 stream clips are not in the merged
stream file"); nothing else. Final build: 25,489 entities, .prm 60.3 MB.
Pictures: `<work>\research\shots\RT*.png`; logs / inis: `<work>\build\klhook\live\RT*.*`.

### 9.1 What it took to load (three tool faults, all fixed in the tools)

| run | seen | cause | fix |
|---|---|---|---|
| RT1 | crash kl2 0x8e5bbd 15 s into the load (write to 0) | the loader reads the whole .prm into one heap block (0x82049b: size + 0x60000 through 0x89e850 -> `ZWin32Allocator` 0x7bb2c0 -> HeapAlloc); 100.9 MB was refused. Stock maximum 69 MB; the bank's 86.5 MB loads | `kl_graft.PRM_LIMIT`: past 90 MB the vertex / index chunks of S's map models that no root reaches become 16-byte stubs (indices stay): 99.5 -> 60.3 MB |
| RT1b / RT1c | 'Buffering 69 %' for ever; main thread in 0x55f5a0 from `ZActor` slot 82 | `kl_maps.nav_join` shifted the children of tree 1. That tree is one small tree PER POLYGON and a child is relative to the polygon's root (0x55f5c7 `add edx, edi`); read absolute, 340 of F07's 940 trees overlap | children left alone, leaves (array-2 records) shifted; new rule in `nav_facts`, held by all 21 stock meshes and the three trial joins |
| RT2 | assert kl2 0x6682c5, then no frame | two `FFCoverList`: Dead Men's top-level `CoverList` and F07's `Specials!CoverPoints!CoverControl`, which the layer's `Specials!` kept (`CFFCoverList` slot 13 finds the game data's list at +0x15a0 set) | `kl_fa_author.DROP`; `kl_graft.verify` counts cover lists |

Then (RT2b) **the chain loads**: three static Havok parts in one .HVK, the joined navigation mesh, no
.hrd - none of them a fault. The load takes 200 s to the first frame (the bank: about 100 s).

### 9.2 Where the player stands, what the boardroom looks like (section 8 steps 1, 2)

- Direct boot: the player stands at **(5650, 20996, -700)**, the table's value. With the table's facing
  he looked OUT of the main window at the skyline (RT2b_204s.png): **a player group (`Heroes!*`) looks
  along local -Z** (`look9`). **A `ZSpawnPoint` looks along local +Z** (`rot9`): with `look9` on the START
  points the round's player faced the window too (RT5), with `rot9` he faces the room (RT6_277s.png).
  A jump-list entry holds -Z as its direction (read from memory, RT4): `look9`.
- At load the window is intact (frame, blinds), chairs stand at the table, glass cases and the red
  pillars are drawn, lit and textured (RT2b_236s.png, RT4_206s.png, RT4_212s.png).
- **The boardroom door does not stop the player on a direct boot** (x 3690 -> 3422 in 0.5 s, RT3 / RT4):
  whether it is drawn closed was not looked at; the walk needs no round start to leave the room.
- The 7 boardroom guards attack at once, round or not: a standing player is dead in 10 - 15 s (RT2b: a
  reload every 10 s; RT5 / RT6: hit during the 8 s countdown, 'Killed by: The police' 15 s after GO).
  **The heisters start in sight of them and cannot move during the countdown** - for the owner to judge;
  moving `Squad_Guards_Inside_02 / _03` behind the door, or the START row, would change it.

### 9.3 The walk (`--no-ai` build, RT3 / RT4; way points = the joined navigation mesh)

Start -> round the table -> door (3420, -101) -> reception (3132, 20996, -1063) -> the atrium's two
flights of stairs (y 21000 -> 20300 -> 19600) -> elevator lobby (2497, 19601, 1063): 193 m in 33 s, every
way point reached, nothing in the way. Atrium, rock garden, maple trees and the samurai cases on the
gallery are drawn (RT3_220s.png, RT3_227s.png). The money stacks at the cases were not looked for.
After the jump (9.4): out of the lobby car (its door does not stop the player either), along the
landing (y 570), down to the lobby floor (y 160), front entrance (2376, 51, -6590), square
(439, **-50**, -7861), road (y **-47 .. -40**), north to van stop 1 (-1629, -40, 9231) and van stop 3
(-4082, -40, 7741): 300 m in 70 s, every way point reached (RT4_248s .. RT4_356s.png: lobby, street,
police cars, 'Escape area' marker on the HUD, a red van at stop 3).
Corrected in `kl_fa_author`: `ROAD_Y` 5 -> -40, the two police points on the square y 26 -> -50.
Not looked at: whether the vans drive (a direct boot calls none), the level bounds, the invisible
obstacle at (-450, 0, 0) (the walk did not pass it).

### 9.4 The join: NOT by a message, by the game's debug request (section 3 corrected)

- The trigger box works: the moment the player stepped into the tower car the `JumpPoint` got its
  'AITrigger' - and the game crashed, **kl2 0x8f40c9 reading 0xa4** (RT3). 0x57e110 passes flag 1 when
  the request came by message (`[0x156b35c]`), and 0x8f3fa0 then walks the player's crew,
  `[player + 0xcd0] + 0xa4`. `ZFFPlayer` slot 82 (0x89ca94) creates that crew object only for player
  types 0 and 1 (`[player + 0x273c] <= 1`: the story's two); a Fragile Alliance player has none.
  0x8f3fa0 has one caller. **So no level object can fire a JumpPoint in Fragile Alliance.**
  `kl_fa.check` now reports any object that names a JumpPoint as CRASH 'jump-point'.
- The debug request is the same code with flag 0: `gamedata + 0x8d4 = entry`, `[0x156b358] = 1`
  (gamedata = `[0xdd265c]`; entries of 32 bytes from `[gamedata + 0x8c4]`: name, position, -Z direction,
  object). Written from OUTSIDE the process in RT4 (scratch `jt.py`, WriteProcessMemory, when the feet
  were in a box in front of the car): **(2721, 19601, 1100) -> (6400, 570, -6254) within 0.25 s**, in the
  lobby car, no fault, the walk went on. Entry 5 = `Specials!JumpPoints!06_Exit` (entries 0..4 = the
  five other jump points, in scene order). The player landed 128 off the entry's x: he was running.
- **For the hook (h-hook; two data writes, no code byte):** while the level is Retomoto, when a local
  player's feet (`[gamedata + 0x828 + 4 * byte[gamedata + 0x898 + i]] + 0x460`) are inside
  `kl_fa_author.JOIN_BOX` = x 2802..3142, y 19560..19860, z 789..1029, write `JOIN_ENTRY` (5) and the
  request. The level keeps the box (it only plays F07's line now) and the jump point.
  Online: each machine moves its own local players, which is the right behaviour (section 3.3).
- Without the hook the two parts are not connected: the round can be played in the tower only.

### 9.5 A round (RT5, RT6: one Arcade round each from the menu, standing still, ended by `pass`)

'FRAGILE ALLIANCE ARCADE - ROUND 1', three lives, 'HEIST STARTS IN 8 SEC', 'GO!', HUD with score,
round and a clock from 06:00, the 'Loot area' marker; the player spawns at a START point (z 300 in
RT5, 700 in RT6), is shot by the guards, 'ROUND OVER - All the criminals died', score page $0, two
lives left. No assert, no fault. The process was ended at the score page, so the session never ended
(re/leaderboard.md 4.1): nothing was uploaded.
**Not established:** whether the window blows 1 s after GO (the player faced the room in RT6 and the
window in RT5, where the view already had no blinds before GO), the blast's damage (he was being shot
anyway), the music, loot at the cases, the main-room gate, the vans. These need a player who survives.

### 9.6 Still open, in order

1. The hook's join write (9.4). 2. A played round: blast, cases, table stacks, the car, the street
police, the exit box and the vans (their height is now the road's). 3. The start under fire (9.2).
4. The stream clips (music) - needs the merged PC_Def.str installed, the owner's decision.

## 10. The join by the hook, a round through both parts, and the start problem (2026-10-09, agent i-live; runs J1 - J3, S2, GW1, GW2, N0, N0b)

Builds: `<work>\build\i_rt` (full), `i_rt_noai` (`--no-ai`, zip sha1 ac047766), `i_rt_gw`
(`--guards-wait`), `i_rt_gw9` (`--guards-wait --blast-delay 9`); all with the tools as committed,
`kl_fa_author.py test` RESULT as in section 9 (the two known verify problems). Hook: i-hook's TEST
builds (every Steam write blocked; re/fa_round.md 8).

### 10.1 The join

- `JOIN_BOX` is now the floor IN FRONT of the tower car: x 2550..2790, y 19500..19800, z 800..1100.
  The box inside the car (x 2802..3142, section 9.4) is never reached: the car's doors are shut and
  stop the player at x 2727 (run J1, 15 s of pushing). `klhook\KLJoin.retomoto.ini` holds the same
  box; it goes beside the level archive as `KLJoin.ini` (`kl_graft.py install` copies one from the
  build's folder and REMOVES the slot's when the build has none).
- The hook's write works from inside the process, on a direct boot (J1b) and in a real Arcade
  session (J2, J3, N0, N0b): `join: player 0 entered box 9 at (2718..2720, 19601, 1099): jump to
  entry 5 'Specials!JumpPoints!06_Exit' requested`, `player 0 is at (6408..6411, 570, -6221) 500 ms
  after the request`. Five times out of five; no integrity exit in up to 4.5 minutes afterwards.
- In the lobby car the walker pushes at (6208, 570, -6221) for 15 s (the script's first way point
  after the jump is one of the tower's), then walks out: the lobby car's doors do not hold him.

### 10.2 One Arcade round through both parts (N0b, the `--no-ai` build; pictures N0b_<s>s.png)

Round 1 starts at 15:52:31; times below are seconds after that.
- 0 - 10: countdown in the boardroom, a lit glass case with a statue beside the player (shot 71).
- 13 - 44: boardroom door, reception, atrium stairs down to y 19601, the lift lobby (74, 80).
- 45: the jump (107, 110: inside the lobby car). 46 - 79: landing, lobby floor, entrance
  (2364, 51, -6590) (137, 140).
- 84 - 92: the square and the road: 'BOSHIN' shop fronts, traffic, a police car driving (146, 170).
- 128: van stop 1 (-1616, -40, 9214). 138: van stop 3 (-4078, -40, 7744), where a red van
  stands (191, 203, 215). The script taps and holds E at both stops, six times each. The HUD clock
  is red at 00:07 in shot 248.
- 196: **`ROUND OVER - Time ran out. You didn't escape. You lose a life.`** Round score $0, two
  lives left (N0b_257s.png); score page 'Subway Round 1', Ready (269).
So: the whole route is walkable in a session and the escape area is reached, but **the van was not
boarded** and the clock ended the round 3 min 16 s after it began - although the HUD clock starts
at 06:00. In J2 (two minutes lost on the road) the round ended after 5:12, in J3 after 4:29, in N0
and N0b after 3:16: the end follows the arrival at the escape area, not the round clock. Read: the
van's leaving time (kl_fa_author's van timer) runs out because nobody boards. NOT established:
where the boarding box is relative to the red van (the bank needed the SOUTH side of the box,
re/fa_round.md 7), and whether E does anything there. This is the next thing to script or play.
- In J2 the walker lost two minutes on the road at z 2400..3100 (ten way points 'NOT reached');
  in J1b, J3, N0 and N0b the same points were passed in seconds. Traffic, not the map.
- Nothing was heard or seen of: the window blast (the countdown pictures show the room, not the
  window), the statues' loot (no E at a case), the main-room gate, street police.

### 10.3 The start: seven guards fire during the countdown - what was tried

Seen (S2, standing still, full build): red screen at 'HEIST STARTS IN 1 SEC', dead 21 - 26 s
after the round state begins, three times.
What the campaign does: the boardroom guards sit in a mini-cutscene until the window blows; the FA
layer strips that cutscene, so nothing holds them. In the level, `ZSquadScript` field 3 is 1 on
exactly three squads (the two boardroom squads and one street squad) and 0 on the other 28, which
do nothing until one of their behaviour routs is named - the tower's by the blast timer.
ASSUMPTION that field 3 means 'active from the start' (no name in the exe; 14 of stock F01's 30
squads have 0, the ones that arrive later).

| option | build | run | seen |
|---|---|---|---|
| A. as built (the owner has seen this) | `i_rt` | S2 | hit during the countdown, dead 21 - 26 s after the round state begins |
| B. `--guards-wait`: the two room squads get field 3 = 0 and start at the blast like the rest of the tower (their flanking routs are in the blast timer's list already) | `i_rt_gw` | GW1 | NO better: red screen from the middle of the countdown (GW1_274s.png). The blast timer (`BLAST_DELAY` 1.0 s) counts from the round-start EVENT, which comes when the countdown begins, not at 'GO!' - so the blast, and with it the guards, come 1 s into the countdown |
| C. B plus `--blast-delay 9`: the blast at 'GO!' (the countdown is 8 s) | `i_rt_gw9` | GW2 | **Countdown clean** (GW2_268s, _272s: no red, the guards sit); the first hit at 'GO!' (GW2_276s); the round is over about 20 s after GO - 30 s after the round state begins, against 21 - 26 in A (one run each, and the walker moves in GW1 / GW2 but stood still in S2: the times are not a measure) |
| D. move the START row out of sight of the room | - | not built | changes the owner's design ('already at the main window') - listed only for completeness |

C is the owner's own description - 'the explosion as the round begins ... straight into action as
the main window blows' - made true for the guards as well: nobody fires before the blast, and the
blast is at GO. It costs two table values and nothing else. It is NOT the default: `ROOM_WAITS =
False`, `BLAST_DELAY = 1.0` in kl_fa_author.py; `kl_fa_author.py test <out> --guards-wait
--blast-delay 9` builds it. Whether the blast itself is seen and heard at GO is not established
in any option. The owner decides between A and C.
(Superseded the same day: the owner moved the start outside. Section 11.)

## 11. The start on the ledge, the sequence, the staged tower fight, the join as a beat (2026-10-09 17:00, agent k-tower; OFFLINE)

The owner, after seeing the tower in the game: the heisters start OUTSIDE, on the ledge before the glass
of the main window, THEN the blow-up sequence happens and they go in. This replaces the START row in the
boardroom (section 1, row 1) and the start options A / C of 10.3. Nothing below was run in the game: the
owner was playing. Everything is read from the level files and kl2.exe, built, and tested by tools.

    python tools/kl_fa_author.py test <out> --keep      the build with this section's layer (defaults below)
    python tools/kl_fa_author.py ledge <archive>        the ledge test alone, 7 s

### 11.0 Result

Build `<work>\build\k_rt\R09+M09_A (R09 = F07+M09_B)\F01_Main.zip` (312,377,815 bytes, sha1 d97f3e63...),
log `<work>\build\k_rt\test.log`: **RESULT: PASS**. 25,529 entities (40 more than section 9: the campaign
objects of 11.3 / 11.4 and one more squad), 22 rooms.
- `kl_graft.verify`: 1 problem, known ("39 particle template names do not resolve (stock M09_A: 36)"). The
  second known one (stream clips) did not come up in this build.
- `kl_fa.check`: 0 CRASH, 0 BROKEN, 1 DEGRADED (no bot squads), as before.
- ledge test: ok (11.1, 11.2). Inventory read back from the archive: every list of 11.2 - 11.4 resolves,
  no 'NOT IN THE LEVEL'.
- Not installed anywhere. Nothing was written into the Dog Days folder.

### 11.1 The ledge exists: M09_A has a balcony outside the main window

It is where the campaign's Kane lands from the rope and plants the bomb (`Pos_PlaceBomb` (5910, 21017, -80),
`Markup!Jump_02` (5947, 21015, 79)). Nothing had to be authored, cloned or added to the .HVK.
All boxes are world boxes of the static (type 1) collision of the built level's .HVK, in units (x 100 of the
file's metres); `ledge` prints them.

| what | object (room `M09_A_Out_CityScapeFront` unless marked) | box / faces | collision flags |
|---|---|---|---|
| **slab** | `SO0200_M09_FrontTopWindows_01` (one mesh of 38 triangles, has a model: it is drawn) | top face **y 21011, x 5826..6164, z -1087..898**; slanted underside down to y 20742; outer face x 6164 | 0x72 |
| canopy and side walls | the same object | underside y 21695 over x 5826..6007; walls z -1012 and z 818 for x 5826..5926 | 0x72 |
| **glass, intact** | `...Office_301\SI0200_M09_Window_Glass_A_02!SI0200_M09_Window_Glass_Geom_Pre_00` | two walls x 5840 and x 5860, **y 21020..21660, z -990..790** (4 triangles) | 0x72 |
| half pillars | `S00200_M09_Balkon_HalfPillar_A_01..04` | x 5850..5895, y 21010..21694; z -558..-466, -1046..-953, 265..358, 753..845 | 0x72 |
| **rail**, invisible | `ColiObj_Plane01` (10 triangles, no model) | y 21004..21204: outer wall **x 6151**, z -1070..872; end walls z -1070 and z 872, x 5891..6151; two inner returns x 5888 for z -1070..-547 and z 346..872 | 0x108 |
| room side | `SI0200_M09_Office_Wooden_*` (deck, top y 21010, x 5704..5842), `..._Office_Floor_25x20_A_01` (y 20990, to x 5887) | the way in is level: slab 21011 -> deck 21010 -> floor 20990 | 0x72 |
| camera only | `ColiObj_Obj_Camera_Blocker_01 / _02` | x 5802..5885 | 0x40 |

- **Usable standing area**: x 5895..6151 (pillar fronts to the rail) = 2.56 m deep, z -1070..872 = 19.4 m wide.
  The way to the glass is the middle only, z -547..346 (between the inner returns and pillars 2 / 3).
- **Navigation mesh**: two of M09_A's own areas lie out there (joined mesh of the level, area boxes):
  (5894 20920 -975)-(6102 21120 780), 2 polygons = the balcony; (5871 20920 -432)-(5896 21125 232),
  1 polygon = through the window. `LEDGE` in the tool is the first one: every criminal point stands in it.
- **The rail is a player's wall in Dog Days by its flags**: 76 static placements of stock F01 / F07 / L03
  have 0x108 as their whole flag word; all 76 are named `ColiObj_*`, 73 of them hero / block / hack / fix
  (`ColiObj_HERO_HACK` 14, `ColiObj_BlockHouse` 11, `ColiObj_HeroBlocker` 5, `ColiObj_InvisibleWallToSmallCY`,
  `ColiObj_player_fix` ...; scratch `inv7.py`), and 367 more sub-parts carry it inside other objects.
  (Dead Men's own `ColiObj_Hero`, 97 shapes with flags 0x20, has no Dog Days namesake with that word; those
  are the pillars' inner faces here, not the rail.) The rail is 1.93 m high above the slab.
- **Walk test** (`kl_escape.Walk` on the built .HVK, shapes with a player's bits 0x20 / 0x08 only, hidden
  entities left out), from START point (6000, 21011, -930):
  - as the level loads: **1,205 cells of 20 x 20, x 5870..6130, z -1050..850, floor y 21010 only**. Bounded by
    the rail, the four pillars, the intact glass and the slab's own walls. The glass keeps the walk out,
    the rail keeps it on.
  - after the blast (intact window off, blown window and first cracked pane on): 12,977 cells, x 3450..6130:
    the whole boardroom down to its door.

Top view (x to the right = away from the tower, z up; one column about 26 units, one row about 100):

```
   z                       glass        slab top y 21011                 rail   slab
                           5840-60      (FrontTopWindows_01)             6151   edge 6164
  898 . . . . . . . . . . . + - - - - - - - - - - - - - - - - - - - - - - - - - +
  872   room wall x 5829 -> | ===================== rail z 872 =============+  |
  845                       |##|                                            :  |
  753                       |##| pillar 4      R4 (6000, 770)   T (6070,730)  :  |     bound: warning from
        cracked glass after |  :               R3 (6000, 690)                 :  |     x 6180, bound from
  550   the blast (state A) |  : inner         R2 (6000, 610)   T (6070,570)  :  |     x 6230 to 7350,
        z 350..790          |  : return        R1 (6000, 530)                 :  |     y 11900..23300
  358                       |##| x 5888                                       :  |
  265                       |##| pillar 3                                     :  |
                            |                                                 :  |
        THE WAY IN          |        way through, nav area                    :  |
        z -547..346    <====|        x 5871..5896, z -432..232                :  |
        (no glass after     * bomb (5867, 21094, -66)                         :  |
        the blast)          |                      nav area of the balcony    :  |
                            |                      x 5894..6102, z -975..780  :  |
 -466                       |##|                                            :  |
 -558                       |##| pillar 2                                     :  |
        cracked glass after |  : inner         L4 (6000, -690)                :  |
        the blast           |  : return        L3 (6000, -770)  T (6070,-730) :  |
        z -990..-550        |  : x 5888        L2 (6000, -850)                :  |
 -953                       |##|               L1 (6000, -930)  T (6070,-890) :  |
-1046                       |##| pillar 1                                     :  |
-1070                       | ===================== rail z -1070 ===========+  |
-1087 . . . . . . . . . . . + - - - - - - - - - - - - - - - - - - - - - - - - - +
                         5826  5895                 6000        6102      6151 6164
   inside: wooden deck x 5704..5842 (y 21010), then the boardroom floor (y 20990), guard 'Inside_01' at (5770, -347),
   InvisiBomb at (5685, 20997, -394)                            L / R = the two START stacks, T = TRAITOR points
```

**Falling.** What holds a player on the balcony is the rail, and only the rail - as in the campaign: M09_A
and M09_B have no `KillBox` at all. The layer's tower bound (`Specials!LevelBound!040_LevelBound_AlleyTop`)
now begins OUTSIDE the rail (warning from x 6180, bound x 6230..7350, y 11900..23300, z -2500..2300); before
this section its warning began at x 5880 and would have covered the heisters' start.
What `ZLevelBound` does, read (vtable 0xbc57d4, update slot 25 = 0x62e1b0): it collects the players inside its
box (0x5891f0), speaks 'AllLevels/Oneliners/LevelBounds/%s_Warnings%s/...' with '1st' / '2nd' (the two warning
boxes) and keeps a per-player count at player + 0x2760 that 0x907930 releases. **No call that kills was
identified in it**: whether a bound kills, turns the player round or only warns is not established. A real kill
needs a `KillBox` ('FA_DieFromSelf'), and none can be kept under the rules of this layer: F07's one free
kill box is a CHILD of its map's top node (`Locations/F07/F07_Locations.zip\KillBox`), the other three ride
in the vans. **For the lead (kl_graft, not my file):** a way to keep one child node of a dropped subtree
(or `kl_scene.graft` of that single node) would give the kill slab: x 5900..7300, y 12000..20900, z -2500..2300.
Kl2 also has a `ZSafetyNetPhantom` in the Havok world (re/havok.md); what it does with a falling player was
not read.

**How a new static collision placement could be added (asked; not needed here).** Established on the stock
files (19 levels of both games, `<work>\research\agent_scripts\k-tower\inv6.py`): of 23,012 pairs of static
placements of ONE shape with the same rotation, 15,862 have byte-identical MOPP code and a code offset that
differs by exactly the placements' distance; in none is the code the same with any other offset (the other
7,150 have other code bytes - the builder's rounding - and, in the six printed, the same offset rule). So a static placement's code is
relative to its record's offset: **a copy of a static placement moved by a pure translation is valid with
the same code bytes and the offset moved by the same vector** (not with another rotation or scale). What
is NOT available is the second half: the list code of its 510-block has to return the new child for the
new volume, and list codes cannot be written without interpreting MOPP (the smallest last list of those 19
levels has 13 children, L05; the builder in kl2 is stripped of its save step, re/havok.md). A new standing
surface would therefore be a KEY-FRAMED (type 4) shape, which has no code in the file and follows the
entity its REF names - and that needs an entity, i.e. a clone, which this layer does not make.

### 11.2 The sequence

Seconds from the round-start event (= the moment the 8 s countdown begins: seen live, GW1 / GW2):

| t | what | by |
|---|---|---|
| 0 | the heisters stand in two stacks of four on the balcony, left (z -930..-690) and right (z 530..770) of the bay that blows, x 6000, facing the glass. The window is intact: nobody sees in or out | START points (`rot9`), player groups (`look9`), as seen live in section 9.2 |
| 0.5 | briefing voice (F07's) | host |
| 8 | 'GO!' | game |
| **9** | the bomb gets 'Activate': its warm-up | `AIMonitor` list 2 -> arm timer (`TriggerDelay2`, `BLAST_DELAY` 9.0) -> `AIDWrapper` -> `WindowBlowup!BombWindow03` |
| **13** | the bomb goes off by itself (its fuse, 4.0): particle group `Particles_M09_BigWindow`, explosion sound | the bomb's `Explode` |
| 13 | glass: the intact window off, the blown window `..._Geom_Post_00` and the cracked side panes `SI0200_M09_GlassWindow_00_A` on, `Glass_Break_Big` | blast timer (`TriggerDelay2`, 9.0 + 4.0) -> `AIDWrapper` 'ForceTriggerShotActivate' -> the window's own `ShotActivate` |
| 13 | chairs thrown, the boardroom door broken open, the level's music | blast timer -> the campaign's four geometry swaps, `Music!PlayMusic_TokyoAction` |
| 13 | the guard standing at the glass dies | blast timer -> `WindowBlowup!Activator_KillGuyNearWindow` -> `WindowBlowup!InvisiBomb` (the campaign's own beat; both kept now) |
| 13 | the three room squads wake (7 + 2 guards; one of the 2 is the dead one) | blast timer -> their flanking routs; `ZSquadScript` field 3 = 0 until then |
| 13+ | the heisters walk in through z -547..346; 5 s after the first one crosses the window a pillar comes down | `WindowBlowup!TriggerBox_FallingDebris` (armed by the blast timer) -> `WindowBlowup!Timer` -> `Activator_FallingDebris` (campaign's, kept) |

Read, and what each step rests on:
- **The fuse.** Dog Days `Explode` field 9 (Dead Men 7) is 4.0 on `BombWindow03` and 0.0 on the campaign's two
  instant bombs and on all 14 `Explode` of stock F01 and F07 (rockets, gas tanks, car explosions). In the
  campaign the plant animation hands the bomb over (`MiniCutItemProxy`) and at the same moment starts
  `Squad_Guards_Inside_01\Timer_ExplosionDelay_Kane`, a `TriggerDelay` of 4 that fires everything else of the
  blast (chairs, music, InvisiBomb, debris box). ASSUMPTION that field 9 is the fuse and that the first of
  the bomb's two sounds (`Bomb_WarmUp`) fills it. **The layer before this section fired the glass, the
  swaps and the squads together with 'Activate' - by this reading 4 s before the explosion.** `--fuse S`
  writes another value into field 9 and moves the blast timer with it.
- **The glass before the blast.** The intact window is a double wall with flags 0x72, the flags of every
  wall of the level; it starts 9 units above the slab. The blown window, the three glass states A / B / C
  and the bomb's model are hidden at load (ZGEOM[3] = 1, .gms 0x400).
- **What the forced `ShotActivate` does** (the window's own lists, Dog Days field 3 on / 4 off): on =
  `..._Geom_Post_00`, `SI0200_M09_GlassWindow_00_A`, `Window_Shatter_Sound`; off = the intact window. State A
  has collision only at z -990..-550 and z 350..790 (flags 0x62): the two side bays keep cracked glass, **the
  middle bay z -550..350 has none from the first moment**. A breaks to B (`Window_Crackle_Sound`), B to C
  (no collision) when shot or damaged (their own `ShotActivate`, thresholds 500 / 520 and 700 / 0).
- **Is the blown window passable on foot?** Yes by its collision (173 vertices): 34 flat triangles at y 20993
  (glass on the floor, 3 above it), and ten thin frame stubs at x 5811..5855: four hang from the top
  (y 21373..21658), two stand on the sill at z -301..-286 and z 72..101, 87 high and 10 wide. The walk test
  crosses it (11.1).
- **Hidden geometry has no collision: ASSUMPTION**, the one this whole swap rests on in the campaign too.
  Support from stock: F07 has a static plane `BlockVisionPlane` whose only flag bit is 0x10, and removes it 23 s
  into the round with a `DeactivateGeom` (`Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!*`) - a
  static placement that stops acting when its entity is switched off is stock Fragile Alliance. Live step 3.
- **AI sight and glass.** By that same object bit 0x10 is what blocks AI sight: it is F07's vision blocker's
  only bit, every wall and floor has it (0x72), and glass does not (stock F01 / F07 / L03, static sub-parts
  of objects named glass / window: 0x66 on 227, 0x62 on 11, and 0x72 on 275 - frames and solid ones like
  this window; this window's states A and B: 0x62). So Dog Days' AI sees THROUGH glass
  panes, but **not through this window while it is intact**: its collision is a wall (0x72), not glass.
  ASSUMPTION on the bit; the consumer in kl2 was not read.
- **Guards unaware until the blast.** The three boardroom squads get `ZSquadScript` field 3 = 0 (`ROOM_WAITS`,
  the default now) and are started by the blast timer; seen live with two of them in run GW2 (they sat
  through the countdown with the player in the room). `--guards-awake` leaves the campaign's 1.
  `Squad_Guards_Inside_01` stays now (it was left out because its guard stood where the heisters spawned):
  one man at the glass, (5770, 21012, -347), 98 from the InvisiBomb; one at the table.
- **The heisters and the two bombs.** By placement: the nearest START point is 616 from the bomb (its first
  radius is 600) and 432 from the InvisiBomb (300); `ledge_facts()` tests every criminal point of every mode.
  By radius as well (`BLAST_HARMLESS`, default, GUESS that fields 0 / 1 are the bomb's reach; stock values:
  rocket 500 / 150, gas tank 600 / 400): the bomb's two radii are 1, so that a heister who walks to the
  middle during the warm-up is not killed either. `--blast-real` leaves 600 / 400. The InvisiBomb keeps its
  values: it has to kill the guard.
- **During the 5 s between GO and the blast** the heisters can move along the balcony and shoot. Whether
  bullets break the intact window early (its `ShotActivate` thresholds are 350 / 320) is LIVE; if they do,
  the guards still sleep until the timer.

### 11.3 The staged tower fight

The campaign already has the stages, as trigger boxes its designers placed; they were dropped with the
campaign scripting. Twelve of them are kept now as they are (`STEPS`, single top-level nodes, their own
positions and lists; what a list names of the dropped campaign is cut by `kl_fa.repair`), and made
`ECPS_FA_MERCONLY` - the idiom of stock F01's `tbPlatform#01_MercOnly`. Three squads no campaign box starts
(the campaign started them from a cutscene) get one of two F07 boxes in the boardroom. Read back from
the built level:

| step | box (centre) half | who | starts |
|---|---|---|---|
| blast | - | blast timer | `020_Office!Squad_Guards_Inside_01 / _02 / _03` (9 actors) |
| 1 past the table | F07 `tb_LEFT_TheySpotYou` (4200 21200 -100) half (60 250 1200). GUESS: x of `Markup!Jump_03` | authored | `030_Reception!Squad_Hallway`, `Squad_Hallway#01`, `Squad_ShootBeforeStorm` (5): they come to the door the heisters are fighting towards |
| 2 boardroom door | F07 `tb_RIGHT_TheySpotYou` (3430 21200 -100) half (60 250 300) | authored | `040_Atrium_3rd!Squad_AtrTop_Reception` (2) |
| 3 reception -> atrium, 3rd floor | `040_Atrium_3rd!TriggerBox_EnterAtrium` (1535 21176 -94) half (100 250 1200) | campaign | three `Atrium_3rd_Recep*Charge` squads' modifiers, `Timer_CoverDefense` (3 s -> the two `RecepSneakup` squads), `050_Atrium_2nd!...LeftCharge` |
| 3b | `040_Atrium_3rd!TriggerBox_EnterAtriumFurther` (673 21236 -94) half (100 250 1600) | campaign | `050_Atrium_2nd!...RightCharge` |
| 3c gallery sides | `Trigger_RecepLeftGoRight` (265 21243 1174), `Trigger_RecepRightGoLeft` (304 21242 -1351), half (450 250 50) | campaign | the charge squads change side |
| 4 top stairs | `050_Atrium_2nd!Trigger_2ndFloorStairs` (-928 21218 -94) half (50 300 2000) | campaign | `...RecepRCharge_Squad_01#01` goes downstairs, the two `BehindStairs` squads |
| 4b 2nd floor sides | `Trigger_2ndLeftGoRight` (-1005 20454 1408), `Trigger_2ndRightGoLeft` (-981 20435 -1683) | campaign | the `BehindStairs` squads change side |
| 5 2nd floor, foot of stairs C / D | `050_Atrium_2nd!Trigger_2ndFloorStairEnd` (-1899 20581 -121) half (200 300 2000) | campaign | four `060_Atrium_1st` squads (7) |
| 6 1st floor, foot of stairs A / B | `050_Atrium_2nd!Trigger_1stFloorStairEnd` (-1730 19884 -121) half (200 300 2000) | campaign | `070_Elevators!010_Squad_Elevators` (3) |
| 6b across the atrium floor | `070_Elevators!TriggerBox_PreLastTrigger` (164 19742 -169) half (200 150 2000) | campaign | `060_Atrium_1st!Squad_MG-Guy`, `070_Elevators!010_Squad_Elevators_GuardingElevator` |
| 7 elevator lobby | `070_Elevators!TriggerBox_OpenExitElevator` (2049 19741 -110) half (100 150 1400) | campaign + added | 11.4, and `070_Elevators!020_Squad_Elevators_Last_Stand_02` (2) |

24 squads / 45 actors in the tower (one squad, two actors more than before). `--one-wave` builds the old
behaviour (everything at the blast, the boxes emptied except the lobby's doors). Loot is as it was: 15
stacks at the samurai cases, 6 on the table once the room's squads are dead - the counter now counts 3.
Two boxes inside `Squad_Guards_Inside_01` whose targets were only its stripped cutscene groups are emptied
(`QUIET`; one of them stands on the balcony).

### 11.4 The join as a beat

The mechanism stays the hook's box on the floor in front of the tower car (`JOIN_BOX`, 9.4 / 10.1). What the
player gets around it, from level objects only:

1. **The car is closed while the tower is fought.** The two door proxies are no longer fired at the blast.
2. **Entering the elevator lobby opens it**, as in the campaign: the campaign's own box across the lobby's
   entrance (x 2049, 7 m before the car) fires `AnimProxy_OpenEscapeElevator` (frames 0..75 on the tower car's
   `Ext_A_03` / `Int_A_03`) and the campaign's `ElevatorDing` and `ElevatorOpen` sounds
   (`Audiotriggers!GeomActivator_*`, kept; their sound objects are part of the map). Added to its list: the
   lobby car's doors in part B (`Mercenaries!VideoProxy!MatPosAnimProxy`), so the arrival finds them open,
   and the lobby's last squad. A criminal only (MERCONLY): three police points stand in that lobby.
3. **The wait.** With `JOIN_BOX` in front of the car the jump comes while the doors are still opening
   (7 m at a run is under 2 s; the doors take 75 frames). A wait that is real needs the box INSIDE the car,
   `JOIN_BOX_CAR` = x 2802..3142, y 19560..19860, z 789..1029 (the first box of section 9.4, unreachable then
   because the doors were shut). **For the hook's ini (not my file): switch `KLJoin.retomoto.ini` to
   `JOIN_BOX_CAR` once a live run has seen the doors open** (live step 8); until then the front box works.
   No level object can delay or fade the jump: the hook makes it.
4. **Arrival**: lobby car at (6272, 563, -6305), doors (opened at step 2) at x 6112, facing out.
5. **Police.** The 7 AFTER_DEATH points are fixed objects: 3 in the elevator lobby, 2 at the atrium lift, 2
   on the square. Nothing stock moves them in plain Fragile Alliance (`OnlineSpawnpointTrigger` holds a spawn
   type and a team, 'eMerc' on all 5 of F01 / F07: the team modes' criminal stages). How the game picks
   among the 7 was not read. A policeman who comes back in the tower after the heisters have left rides the
   same car (the hook's box is for any local player). OPTION `--police-follow` (default off, nothing stock
   does it): the street's entrance box also fires a `DeactivateGeom` on the five tower points, GUESS that
   the spawn choice skips a switched-off point.

### 11.5 For the lead and for k-street

- Nothing outside `tools/kl_fa_author.py` and this file was changed. `kl_graft.build(author=True)` /
  `kl_maps.py chain --author` build the same level (the options are globals of the module, set by `test`).
- `kl_fa_author.KEEP` is now served by a module `__getattr__` (it adds k-street's names); inside the module
  the tuple is `_KEEP`.
- **Interface for part B** (`tools/kl_fa_street.py` did not exist while this was written): if that module
  has a dict `HOOKS`, its keys are used - `'keep'` (more F07 top-level names), `'campaign_keep'`
  ({level: single campaign nodes}), `'prepare_host'` (fn(S, log), after mine: it may re-place anything of
  part B), `'wire'` (fn(sc, log), after mine, on the joined scene). Without it part B is sections 2 - 4.
  F07 objects this file takes: the fourteen in `ROLE`. Free F07 trigger boxes: `Gameplay!020_Loot!tbExitLoot`,
  `...FollowPlayers!tbCountPlayers`, `Gameplay!040_Escape!tbEscapeAI`, `Gameplay!RunToEscape!tbRunToEscape`,
  `...!tbRunToEscape1Player`. The campaign's own trigger boxes of M09_B can be kept the way `STEPS` keeps A's.
- Wanted from kl_graft (11.1): keeping one child node of a dropped subtree, for a `KillBox` under the balcony.
- Wanted from the hook's ini (11.4): `JOIN_BOX_CAR` after live step 8.
- CLAUDE.md "Owner's end goal": 'whether any walkable geometry / collision exists there is NOT known' is
  answered - the balcony, 11.1.

### 11.6 Every GUESS and ASSUMPTION of this section

| what | value | kind |
|---|---|---|
| the two START stacks | x 6000, z -930 -850 -770 -690 / 530 610 690 770 (80 apart; F07's own row was not measured against) | GUESS (the area is measured) |
| TRAITOR points, the other modes' criminal points | x 6070 / 5950 / 5940, same z | GUESS |
| warm-up a beat after GO | `BLAST_DELAY` 9.0 = countdown 8 + 1 | GUESS |
| Explode field 9 = fuse, warm-up sound fills it | 4.0 | ASSUMPTION |
| Explode fields 0 / 1 = reach | set to 1 | GUESS (was there before) |
| hidden static geometry does not collide or block sight | - | ASSUMPTION (stock F07 does the same) |
| collision bit 0x10 = blocks AI sight; 0x20 / 0x08 = a player's | - | ASSUMPTION (names and census; code not read) |
| `ZSquadScript` field 3 = active from the start | 0 on the room squads | ASSUMPTION, seen once (GW2) |
| a `TriggerBox` with field 0 = 0 waits to be named | F07's two boxes set to 1; `TriggerBox_FallingDebris` left 0 | ASSUMPTION (re/fa_gamemode.md 4) |
| step 1 box | x 4200 | GUESS |
| tower bound | warning from x 6180, bound from 6230, 110 m down | GUESS; what a bound does to a player is not established |
| spawn camera A | (6500, 21300, 500) looking at (5950, 21080, -100) | GUESS |
| 'ENTERS_BANK' plane | x 5700, 1.5 m inside the glass | GUESS |
| `--police-follow` | off | GUESS |

### 11.7 What could not be done offline

- Seeing any of it: the blast, the fuse, the glass swap, whether the rail holds a Dog Days player, whether
  the guards stay asleep with eight heisters 2 m outside the glass.
- A kill box under the balcony (no keepable one; 11.1). What a level bound does to a player in the air.
- A new standing surface would have needed an entity; it was not needed.
- A wait at the car that the level enforces (11.4, 3): the hook's box decides.
- How the game chooses among the police points.
- Team modes: the criminal points of Cops & Robbers / Undercover Cop stand on the balcony too; their
  stage triggers B / C / D are where they were.

### 11.8 Live order (one variable per run; each needs the one before)

Build once (`test <out> --keep`), install into the F01 slot with its `KLJoin.ini` as in section 10.

1. **Direct boot, no round**: the player stands on the balcony at (6000, 21011, -930) facing the glass
   (shots). Push -x for 5 s: stopped at x about 5890 by the glass. Push +x for 5 s: stopped at about 6120 by
   the rail. Walk z -930 -> 770 along x 6000: nothing in the way. FAIL at the rail (falls): the level must
   not ship before a kill box or a real rail exists - tell the lead (11.5). FAIL at the glass (walks in):
   the hidden / intact assumption is wrong, read which entity collides.
2. **Arcade round, stand still**: countdown clean (no red), guards do not react. Shots at 8, 9, 13, 14 s
   after the round state begins: at 9 a sound (warm-up), at 13 particles + explosion + glass gone in the
   middle bay, cracked panes at the sides, chairs thrown. Not hurt. If the glass goes at 13 but the
   explosion came at 9: field 9 is not a fuse -> `--fuse 0 --blast-delay 13`.
3. **Walk in** at z -100 after the blast: over the deck onto the floor; a dead guard at (5770, -347); the
   others fire; 5 s later the pillar falls. Stuck at the sill: read the stubs (11.2).
4. **`--blast-real`** (only after 2): the stacks survive the full bomb at 616.
5. **Step 1 / 2**: cross x 4200 -> reception squads come through the door; cross the door -> the two of
   `AtrTop_Reception`. Compare with `--one-wave` if the tower feels empty or late.
6. **Steps 3 - 6**: each campaign box in turn (EnterAtrium, 2ndFloorStairs, 2ndFloorStairEnd,
   1stFloorStairEnd, PreLast): squads appear as the table of 11.3 says.
7. Statue loot and the table's six stacks after the 9 of the room are dead (section 8, steps 6 / 7; the
   counter is 3 now).
8. **Elevator lobby**: crossing x 2049 - ding, the car's doors open (shots of the car from x 2300). Then the
   jump as before, and the lobby car's doors are open on arrival. Doors seen open -> the ini gets
   `JOIN_BOX_CAR` and this step is run again.
9. The tower bound: not reachable if the rail holds; with a debug jump to (6300, 21100, 0) see what the
   bound does (warn, kill, nothing).
10. `--police-follow` with a second player, after everything else.
Part B from the lobby on: k-street's file.

## 12. The loot's props and reach (2026-10-09 22:00, agent y-loot; OFFLINE) -> re/retomoto_loot.md

Owner after playing: bags everywhere, briefcases wanted in the start room, the left row on the table cannot
be taken, a fitting prop for the statue loot. `tools/kl_fa_loot.py` works on the WRITTEN level, through
`kl_fa_author.FINISH` (run by `kl_fa_author.test` and `kl_fa_blast.test`; `--loot-bags` = as before):
- the table's row at z -120 (LEFT from the balcony: facing -x, left is -z) was 190 from the nearest place
  to stand with reach 120 (the pick-up test read at kl2 0x783e60: horizontal distance <= radius + 40). All
  six now lie 33 in from the table top's two long rims, radius 125, and show Dead Men's Fragile Alliance
  briefcase (M01_FA_A, 18 chunks in dead indices);
- the 15 at the samurai cases show the case's own armour (a new root over the case model's two armour
  meshes; the case keeps frame and glass): taken = the case is empty;
- `MAIN_ROOM` / `STATUES` here are where the loot STARTS; the 'GUESS: the table top is 80 above the floor'
  and 'GUESS: that a stack inside the glass can be reached' of section 2 are measured now (top y 21070;
  every case has a place to stand 91..98 away, reach 190).
Section 8's steps 6 / 7 (statue loot, the table's six) are to be looked at with re/retomoto_loot.md 6.
