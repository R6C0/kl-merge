# Retomoto Tower: the Fragile Alliance layer

2026-10-09, agent f-retomoto. **Offline only**: nothing was installed, the game was not started.
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
