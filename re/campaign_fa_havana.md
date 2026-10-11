# Havana (Dead Men chapters 11 + 12, M11_A + M11_B) as a Fragile Alliance map - study

2026-10-11, agent cfa-havana. OFFLINE study: nothing was installed, the game was not started, no
existing tool or note was edited. `<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`.
Scratch scripts (all read-only on the game files): `G:/kl_scratch/cfa_havana/*.py`, their outputs
beside them as `*.txt`. Trial builds (logs and result.json only; every archive was deleted again):
`<work>/build/cfa/havana/`. Pictures: `<work>/build/cfa/havana/pics/`.

NOTE (second agent, 2026-10-11): this report was checked by a second agent. Its numbers stand; its ROUND
(4.2) needs four changes - corrections are marked in place as 'corrected by the second agent' in 4.2, 5 and
6, and the last section 'Verification (second agent)' lists what was confirmed, corrected and left open.

Evidence labels: **MEASURED** = output I produced (command named), **READ** = code or an existing
note (file and place named), **ASSUMED** = fits the evidence, reason given, **GUESS** = a coordinate
or value I propose and did not measure. World units are centimetres (100 = 1 m); x right, z up in
the pictures, y is height.

    python tools/kl_maps.py what|sides|first M11_A|M11_B
    python tools/kl_maps.py one <work>/build/cfa/havana F07|F08|F05 M11_B --campaign      (and F07 M11_A)
    python tools/kl_maps.py chain <work>/build/cfa/havana F07 M11_B M11_A
    python G:/kl_scratch/cfa_havana/survey.py M11_B 2        tree, census, vehicles, squads, checkpoints, music
    python G:/kl_scratch/cfa_havana/navplot.py M11_B out.png mesh parts + picture ('both' = one world picture)
    python G:/kl_scratch/cfa_havana/routes.py M11_B st.json  stations on the mesh, leg lengths
    python G:/kl_scratch/cfa_havana/rooms_chunks.py M11_B    .prm chunks each room brings; scenarios.py = the sums
    python G:/kl_scratch/cfa_havana/squads.py M11_B          the squads by kl_fa_author.squad_plan's rule
    python G:/kl_scratch/cfa_havana/props2.py M11_B "<regex>" props by holder; ctrlvals.py = controller values
    python G:/kl_scratch/cfa_havana/leftovers.py M11_B       textures / waves / .LOC keys; music.py; hosts.py; factions.py
    python G:/kl_scratch/cfa_havana/hidden.py M11_B "<regex>" what is hidden at load; links.py M11_B = the mesh's links;
                                                             runs.py / inbox.py = the mesh and the objects along a line

---------------------------------------------------------------------------------------------------

## 0. Short answers

1. **The two chapters are ONE continuous piece of Havana in one world space** (MEASURED, picture
   `M11_AB_world.png`): M11_A = start apartment -> market square -> church -> big square -> the
   street north; M11_B takes over at the same street corner and goes rooftop -> Capitol square ->
   inside El Capitolio. No teleport join would be needed (unlike Retomoto).
2. **Both chapters in one map do not fit the game: the .prm chunk table.** MEASURED (chain): 111,853
   table entries against 73,728 slots; 83,464 of them are LIVE, so even a perfect clean-up cannot
   make the whole pair fit. A two-chapter Havana would need rooms cut out of both levels (a tool
   that does not exist) AND compaction: not recommended.
3. **One chapter fits, but not as kl_graft builds it today under F07**: F07 + M11_B = 74,454 entries
   (726 past the table, a certain crash at load), F07 + M11_A = 72,573 (inside the table, 2,941 over
   the tools' safety line). MEASURED ways out, no tool written or changed:
   F08 as the systems level -> **66,368** (verify: no chunk problem); F05 -> 56,953; compaction of
   the F07 build (`kl_chars.py compact`, exists, never loaded in the game) -> **46,081**, kl_impact
   0 problems; leaving out the rooftop / courtyard rooms -> 63,310 (needs a new pre-pass).
4. **The heist is El Capitolio (M11_B).** The presidential wing at its far end has 11 shoot-open
   glass display cases and 5 paintings, the hall has a sandbag bunker that the campaign blows up,
   the campaign's own tank-shot swaps open the way out to the square, and the whole route (hall ->
   wing -> back -> side stairs -> square) lies on ONE connected piece of the navigation mesh
   (606 polygons, 9,821 m2): the seven AI heisters can walk all of it. MEASURED.
5. **No leftover of the planned 'Havana' Fragile Alliance map** in either level: no spawn point, no
   OnlineMoney object, no PIP trigger, no texture or sound with FA / DL07 in its name beyond what
   every campaign level carries. MEASURED.
6. Nothing in the levels is an escape vehicle a crew could board: the vehicles are a Hind gunship,
   BTRs, a T-72 and two machine-gun jeeps, all enemy or scripted, and the ground vehicles' weapon
   and road controllers have no use in any Dog Days level. The escape has to be F07's key-framed
   van (as on Retomoto) on the Capitol square.
7. Verdict: **feasible-with-work** for a one-chapter map 'El Capitolio'; about 0.8 of the Retomoto
   effort; first step is not authoring but settling the chunk table (section 3.2).

---------------------------------------------------------------------------------------------------

## 1. What the place is

### 1.1 Rooms (MEASURED: `kl_maps.py what`; extents = entities with a model, so 0 often appears as
a minimum - many pieces are modelled in world space with their pivot at the origin)

M11_A, 14,504 entities, 15 rooms + backdrop, all outdoors but two small interiors:

| room | entities | where (x, z) | what |
|---|---:|---|---|
| `M11_A_Inside_Start_Appartment_01a` | 64 | x -1250..490, z -6890..0, y -300..1260 | the flat the chapter starts in |
| `M11_A_Outside_Market_Square_01a` | 670 | x -4990..4730, z -6530..8000 | market square, shelled by artillery |
| `M11_A_Outside_Market_Sidestreet_01a..04a` | 19 / 25 / 16 / 209 | round the market square | closed side streets |
| `M11_A_Outside_Church_01a` | 574 | x -10500..5240, z 0..15780 | stairs up to the church front, the street east |
| `M11_A_Outside_Church_Ruin_01a`, `M11_A_Inside_StreetCorner_01a` | 53 / 9 | x 0..3840, z 7900..11950 | ruin and corner house at the church |
| `M11_A_Outside_Big_Square_01a` | 910 | x 7000..20000, z 8000..16000 (mesh) | big square: two monuments, a pavilion, a ruin |
| `M11_A_Outside_Big_Square_SideStreet_01a / 02a` | 16 / 29 | | closed side streets |
| `M11_A_Outside_Corner_To_Capitolio_01a` (+ `_SMOKE_01a`) | 245 (+5) | x 16500..20100, z 16000..22700 (mesh) | the street north to the Capitol corner |
| `M11_A_Outside_Capitolio_01a` | 221 | far view | the Capitol and its square as backdrop geometry |

M11_B, 17,112 entities, 13 rooms + backdrop + three crowd 'rooms':

| room | entities | where | what |
|---|---:|---|---|
| `M11_B_Outside_Corner_To_Capitolio_01a` | 261 | x 18400..21800, z 20400..23700 | the same street corner M11_A ends at |
| `M11_B_Inside_Rooftop_Courtyard_Corridor_01a` (+ `_RoomA`, `_RoomB`, `_Exit`) | 1,232 (+29 +31 +23) | x 20100..25000, z 15400..20100, y -200..1600 | courtyard house: arcades, two floors of corridors |
| `M11_B_Inside_Rooftop_Stairs_01a` | 22 | | stair to the roof |
| `M11_B_Outside_Rooftop_01a` | 637 | x 24000..28100, z 18400..21200, y 1000 | the roof over the square (Hind and BTR fight) |
| `M11_B_Outside_Capitolio_SideStreet_01a` | 51 | x 32500..36200, z 15400..25500 | the street east of the square (BTRs, the tank's allies) |
| `M11_B_Outside_Capitolio_01a` | 1,350 | square x 21100..31500, z 21350..28000, y 20 (mesh); terrace y 800 | the Capitol square, barricades, the Capitol's front |
| `M11_B_Inside_Capitolio_Side_Entrance_01a` | 58 | x 26470..29600, z 28250..30300, y 0..2230 | side stair, y 200 -> 810 |
| `M11_B_Inside_Capitolio_Main_Hall_01a` | 724 | x 28200..40260, z 28850..32560, floor y 800..830 | the domed hall, 120 m long; bunker at x 38700 |
| `M11_B_Inside_Capitolio_End_Corridor_01a` | 302 | x 39300..41400, z 31000..32500 | presidential corridor: display cases, paintings |
| `M11_B_Inside_Capitolio_End_Room_01a` | 255 | x 41000..43600, z 30700..33300 | half-round end room: 4 display cases, a table |
| `Crowd!Crowd_Main / _Top / _Corner` | 7 each | | the loyalist crowd (human-flow objects) |

### 1.2 Top-level subtrees and the side the graft gives them (MEASURED: `kl_maps.py sides`)

| family | M11_A nodes | M11_B nodes | graft | campaign pre-pass |
|---|---:|---:|---|---|
| `Locations/*` | 4,034 | 5,693 | map | stays |
| `CloneGroup_Locations` (+ `CloneGroup_ROOT`) | 2,509 (+125) | 3,633 (+120) | map | stays (2,634 / 3,521 'without a template') |
| `CloneGroup_Effects` of the map | 363 | 468 | map | stays with its template (363 / 700 kept) |
| `010_MarketSquare!` `020_ChurchFront!` `030_BigSquare!` `040_BreatherBeforeChopper!` | 532 / 115 / 588 / 85 | - | map | DROPPED (5 marker boxes stay) |
| `040_AreaBeforeChopper!` `050_Rooftop!` `060_CapitolioSquare!` `070_CapitolioInside!` | - | 98 / 220 / 553 / 213 | map | DROPPED (2 marker boxes stay) |
| `Allies!` | 119 | 75 | map | DROPPED |
| `Special!` (checkpoints, objectives, bounds, cover boxes, jump points) | 143 | 159 | map | 94 / 92 passive markers stay, 49 / 67 dropped |
| `Effects!`, `SoundEffects!`, `COOP!`, `CutScenes/*`, `Crowd!`, `Ropes!`, `Camera01`, hero groups | 42, 4, 14, 12, -, -, 1, 12 | 45, -, 13, 49, 22, 10, 1, 12 | map | DROPPED |
| `Effects/Hind_Dammage_01.zip`, `Effects/AllocMany/M11/BTR_` / `Tank_Dammage_01.zip` | 21 + 12 | 21 + 12 | map | stays (effect templates) |
| `Locations/M11_A/M11A_Audio.zip!` (ambience) | 78 | (52, inside `Locations/*`) | map | stays |
| `AllLevels/mainsceneincludes.zip`, its `CloneGroup_Effects`, `CoverList`, `TrackLinkObjects`, `ZParticleController` | 2,491 + 3,199 + 3 | same | systems | replaced by the Dog Days level's |

Pre-pass totals: M11_A 440 subtrees / 1,568 nodes dropped, 7,243 stay; M11_B 369 / 1,376 dropped,
10,043 stay.

### 1.3 Pictures (MEASURED: `navplot.py`; the level's own navigation mesh, converted in memory
with `kl_pf4.convert`, polygons coloured by connected part, grid 50 m)

- `<work>/build/cfa/havana/pics/M11_AB_world.png` - both levels in one picture, 1 px = 25 cm, origin
  x -11000 z -7500. Blue = M11_A's mesh, red = M11_B's. They meet at x 18,400..20,100, z 20,400..22,700.
- `<work>/build/cfa/havana/pics/M11_A_nav.png` - 1 px = 12.5 cm, origin x -7564 z -6588: bottom left
  the market square, above it the church front, right the big square, top right the street north.
- `<work>/build/cfa/havana/pics/M11_B_nav.png` - 1 px = 12.5 cm, origin x 16935 z 13935: blue =
  square + side stair + hall + presidential wing (ONE part); red = courtyard house and roof; tan =
  the street east of the square; pink = the strip between them.

### 1.4 The campaign's flow, rebuilt from its scripted objects (MEASURED: `survey.py`, `ctrlvals.py`;
objective texts READ from the English .LOC, `leftovers.py`)

M11_A 'Freedom Fighters':
1. Cut scene `CutScenes/M11/M11_Intro.zip`; Kane (`Hero_Suit_01\Ground`) at (-435, 260, -3637), Lynch
   at (-268, 274, -3644), in the start flat. Artillery falls on the market square from the first
   second: 8 repeating `Explode` boxes `010_MarketSquare!Artillery!BoomBox_Repeating*` (e.g.
   (-148, -337, 1025), (2197, -236, -118)) with `ShakeCamera`.
2. 'Regroup With Your Men' - the mercenaries wait below, `TriggerBox_GetMercs` (-919, -150, -4530).
3. Across the market square (17 enemy squads, 32 actors; two mounted machine guns at
   (1581, 22, 3911) and (-3145, -278, 3573)), up the stairs: `Trigger_ChurchStairStart` (-155, 205, 4021).
   Checkpoint 1 `CP_01` (-2648, 27, 6539).
4. 'Destroy The BTR' - `020_ChurchFront!BTR!BTR_Squad_01` starts at (5768, 27, 10386) and drives a
   `ZRoad`; 7 RPG-7, 2 HK69 and 5 AK-74 pickups lie at the church front. A Hind flies by
   (`020_ChurchFront!HindFlyBy!HindSquad`). Checkpoint 2 `CP_02` (2399, 25, 9989); 'Meet Up With The
   Other Men' (2509, 111, 10654) - five loyalist squads `Allies!AllySquad_*` join and follow.
5. The big square: 29 enemy squads / 50 actors in waves (`10FirstWave*` .. `50After2ndMonument*`),
   machine-gun nests at the monuments (7988, 221, 12887), (15411, 222, 13485), (9193, 221, 13475),
   the ruin (9706, 581, 9137), two UAZ jeeps with guns (17503, 18, 13184), (18025, 3, 8716), and the
   Hind attack `030_BigSquare!Helicopter!ChopperSquad` (9 RPG pickups on the square).
   Checkpoint 3 `CP_03` (17886, 1, 18617).
6. 'Proceed To El Capitolio' (18463, 0, 21463): a BTR is seen on the Capitol square
   (24062, 52, 22089). 'Get Inside The Building With All Men' (19825, 21, 20897).
   `EndOfLevelTrigger` (19528, 212, 20777) -> `SceneChanger` 'Locations\M11_B\M11B_Main.zip'.

M11_B 'El Capitol':
1. Start in the courtyard house: Kane (20316, 21, 21057), Lynch (20251, 20, 20962). 7 enemy squads /
   11 actors in the courtyard. 'Get To The Rooftop' (27627, 1070, 20919); checkpoint 1 on the top
   floor `CP_01` (24051, 1002, 19345); planks fall behind the players (`050_Rooftop!BlockEntrance!KaneLynchBox`).
2. On the roof: 'Take Out The BTRs' (two, at (31938, 9, 23032) and (31821, 27, 24025) in the street
   below; 16 RPG pickups and 6 RPG crates on the roof), then 'Take Out The Hind'
   (`050_Rooftop!Helicopter!HelicopterSquad`, the `ZHeli` waits at (45438, 1967, 36386)).
   Checkpoint 2 `CP_02` (26910, 1007, 20357).
3. Rappel down to the square: `050_Rooftop!RappelPoint!RappelBox#01` (27301, 1121, 21286).
4. 'Take El Capitolio' (27143, 160, 28815): the loyalist crowd (`Crowd!*`) and a T-72
   (`...Tank!T72!TankSquad_T72`, from (18037, 31, 20635) along its `ZRoad`) come onto the square;
   three tank shots swap geometry: `SO0201_M11_BarricadeXX_01` at (27170, 0, 28516) is taken away
   (the barricade at the foot of the side stair) and the Capitol's corner `SO0201_M11_Corner_01`
   (33320, 0, 28900) becomes `SO0201_M11_CornerBroken_01` (32000, 0, 28900).
   23 enemy squads / 37 actors hold the square, the side stair and the terrace, with nine
   machine-gun nests (e.g. (25397, 22, 28235), (29604, 23, 28030), (32503, 803, 28099)).
5. 'Get To Side Entrance' - checkpoint 3 `CP_03` (27899, 826, 29464), top of the side stair.
   'Get To Main Entrance' (32095, 888, 29022); 'entrance' (34188, 804, 30266); checkpoint 4 `CP_04`
   (33981, 808, 30387) under the dome (`070_CapitolioInside!Trigger_CapitolioInside_PastDome`).
6. 'Take Out The7 Members' (38899, 800, 30415): a sandbag bunker across the hall with two machine-gun
   nests at (38666, 909, 29945) and (38682, 907, 30896); 17 grenade pickups in the hall. When they
   are dead: `070_CapitolioInside!Enemies!BoomBoxDust` (an `Explode` at (38613, 902, 30398)), the
   emitters of `Capitolio_Explosion` (debris, fireballs, smoke at x 38710..39490), and after it
   `SI0100_M11_BarricadeB_01` (38697, 800, 30415) is swapped for `SI0100_M11_BarricadeB_Broken01`,
   two explosive barrels and a crate pile are removed. Checkpoint 5 `CP_05` (37671, 805, 30521).
7. 'Proceed To End Hall With All Men' (42179, 800, 31914): the presidential corridor and end room,
   cut scenes `M11_Break_Nose` (camera (39495, 822, 31396)), `M11_Carlos` (camera (42204, 1411, 31868)),
   `M11_Fuentes_Suicide`; the mercenaries complain about their pay (`...End!MercSquad_MoneyWhine`).
   `EndOfLevelTrigger` (42540, 1058, 31923) -> 'Locations\M12_A\M12A_Main.zip'.

### 1.5 The two armies (MEASURED: `squads.py`, `factions.py`)

Both sides are the same kind of object: a `ZFFActor` node 'Ground' with a `ZSoldier` controller
(type `eArmy`) under a character group, in a squad group with a `ZSquadScript` and behaviour routs
(`DefendBehaviourRout` 61 / 35, `FlankingBehaviourRout` 15 / 8, `HuntBehaviourRout` 0 / 2,
`FollowBehaviourRout` 5 / 4 in M11_A / M11_B). What makes the side is `ZFFActor` field 0:

| side | field 0 | character group | weapon templates | M11_A actors | M11_B actors |
|---|---|---|---|---:|---:|
| The7's soldiers (enemy) | `Enemy` | `JPN_Swat_01` (the group's NAME is reused from Tokyo; the model is its own) | `Rifle_M4A1_01`, `Mg_Minimi_SPW_01`, `RPG_7V`, `HG_HK_USP_01` | 82 | 60 |
| loyalists | `Ally` | `CUB_SoldierLoyal_01` | `Rifle_AK74_01` | 19 | 31 |
| Kane's mercenaries | `Mercenary` | `YourMerc03..05_Soldier`, `Little_Soldier_01` | | 4 | 4 |

Skill: enemy `eVeteran`, loyalist `eRegular` / `eN00b` (ZSoldier field 3).
By `kl_fa_author.squad_plan`'s rule (a squad stays when its subtree holds only squad objects, at
least one actor and one behaviour rout; mini-cutscene controllers are taken off):

| | squads | can stay | actors in those | left, and why |
|---|---:|---:|---:|---|
| M11_A market square, enemy | 17 | 13 | 25 | 2 mounted guns (`MountedWeapon`), 1 `GateGroup`, 1 no rout |
| M11_A big square, enemy | 29 | 13 | 25 | 11 hold `GateGroup` / `GatePath`, 1 has no rout, 2 jeeps, 2 mounted guns |
| M11_B courtyard + roof, enemy | 10 | 10 | 15 | - |
| M11_B Capitol square / stair / terrace, enemy (+ 1 `GainAccess` RPG squad, left) | 22 | 11 | 24 | 7 with mounted guns, 2 BTR, 2 scripted RPG squads without a rout |
| M11_B inside the Capitol, enemy | 5 | 2 | 3 | 2 bunker guns (`MountedWeapon`), 1 holds the geometry swap |
| loyalists (both levels) | 16 | 3 (M11_B `LoyalistChargeHide / HoldBack / Fight`) | 13 | the others follow the player (`FollowBehaviourRout`) or hold a `Blocker` |

Vehicles (all in dropped, scripted squads): `ZHeli` Hind x2 / x1 (`HeliScriptRout`, 3 `HeliWeapon`,
`HeliFlyBehaviourRout` - classes stock F02 F03 F06 F08 use); `ZHavokCar` BTR x2 / x2 (the node is
named `V_USA_Civilian_Suv_A_Group_00#01`, weapon `Btr_BTR-90`), UAZ jeep with gun x2 / 0
(`V_VEN_Uaz_A_Dynamic_00`), T-72 0 / x1 (`V_CUB_T72_Dynamic_00`); `ZHavokMountedWeapon` x6 / x13.
`VehicleWeapon`, `MountedWeapon`, `ZRoad`, `ZVehicleFireOnRoadBehaviourRout`,
`VehicleMoveOnRoadBehaviourRout`, `VehicleFireBehaviourRout` have **0 uses in any stock Dog Days
level** (MEASURED: `kl_maps.py first`).

---------------------------------------------------------------------------------------------------

## 2. Leftovers of a planned Fragile Alliance version

MEASURED (`survey.py`, `leftovers.py M11_A | M11_B`): none that belongs to these levels.
- Controllers `OnlineMoneyCtrl`, `OnlineMoneyContainer`, `OnlineSpawnpoint*`, PIP triggers: 0 in both
  levels. No `ZSpawnPoint`. No node name with `_FA`, `Online`, `DL0`, `Multiplayer` outside the
  shared systems subtree (the hits of '_fa' are 'Fabric' / 'Falling' effect names; 'Vault' is
  church / hall vaulting `SO0101_M11_VaultA`, `SI0100_M11_VaultRubble*`; 'Money' is the two
  mercenary dialogues about pay).
- Textures (1,193 / 1,267): `UserInterface/UI_FA_Respawn_pip_mask` in both (it is in the shared
  interface set: the control level M05_A has it too) and, in M11_B, `Locations/M02/Wood/Wood_Basic_02_M02_FA`
  (a wood texture borrowed from the jewel-shop map).
- Waves (.WHD 3,266 / 3,318 records): `Dialog/Multiplayer/FA_Menu/Fragile_Alliance_01..08.wav` in
  both - also in M05_A, so part of every level's bank, not a Havana leftover.
- .LOC (4,241 leaves, the same table in every level): `AllLevels/Menu/Online/Scenarios/BriefingDL07`
  = 'Briefing DL07 - Havana', `TitleDL07` = 'Title DL07': the placeholder and nothing else.
So IO's 'Havana' map left no data in the PC files; whatever is built is new.

---------------------------------------------------------------------------------------------------

## 3. Can it be grafted

### 3.1 The trial grafts (MEASURED; each `result.json` / `log.txt` is in `<work>/build/cfa/havana/<name>/`)

| build | problems (verify) | **chunk-table entries** (table 73,728; tools allow 69,632) | entities | textures / 4096 | materials / 2048 | rooms | .prm MB | .TEX MB | .ANM MB | .fxc MB | sounds / waves | mesh bytes | archive MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| `F07+M11_A campaign` | 12 | **72,573** (1,155 free) | 16,388 | 1,773 | 1,150 | 18 | 67.7 | 397.7 | 21.6 | 17.8 | 4,705 / 4,561 | 493,456 | 335.8 |
| `F07+M11_B campaign` | 12 | **74,454** (726 OVER) | 19,188 | 1,835 | 1,178 | 16 | 69.0 | 433.3 | 21.6 | 17.8 | 4,742 / 4,599 | 290,516 | 362.0 |
| `F08+M11_B campaign` | 11 | 66,368 | 19,187 | 1,917 | 1,098 | 16 | 68.5 | 418.3 | 20.3 | 17.8 | 4,625 / 4,461 | 290,516 | 329.1 |
| `F05+M11_B campaign` | 11 | 56,953 | 19,188 | 1,697 | 876 | 16 | 90.0 | 448.6 | 20.2 | 17.8 | 4,979 / 4,679 | 290,516 | 391.5 |
| chain `R09+M11_A (R09 = F07+M11_B)` | 12 | **111,853** (38,125 OVER) | 25,927 | 1,969 | 1,323 | 32 | 115.2 | 454.7 | 21.6 | 17.8 | 4,878 / 4,726 | 783,916 | 403.0 |
| for scale: Retomoto chain, raw (READ re/maps.md 1) | 12 | 62,615 | 24,165 | 2,141 | 1,397 | 22 | 90 | | | | 4,801 / 4,635 | 603,332 | 314 |
| for scale: Retomoto as played (READ CLAUDE.md, re/prm_limit.md) | | 65,119 | 25,490 | 2,195 | 1,429 | 22 | 76 | 234 (slim) | 20.6 | 8.9 (slim) | 4,941 / 4,766 | | 212 |
| for scale: stock F07 (MEASURED `hosts.py`) | | 35,102 | | | | | 63.6 | 281.0 | 21.6 | 8.1 | | | |

The problems, the same in every build: 'sound: 7 stream clips are not in the merged stream file'
(the level's ambiences and effects: silent, not a fault) and the ten findings of a level without
a Fragile Alliance layer (1 CRASH: no settings object; 9 BROKEN: define, exit trigger, START and
AFTER_DEATH spawn points, three gameplay triggers, loot, squads). Under F07 the chunk table is the
twelfth. Nothing else: 0 dangling scene paths, 0 dangling particle templates, 0 misfits, textures
and materials at less than half of their limits, entities below what ran live (25,490).

### 3.2 The limit that decides: the .prm chunk table

READ (re/prm_limit.md): one pointer per chunk at kl2 0xeac7b0, 73,728 slots, shared with the chunks
the game makes while it runs (up to 713 seen); no loader tests the count; from entry 73,729 on the
loader writes over globals (run P4 crashed at 0x607272 with 80,628). The tools enforce 69,632.

MEASURED (logs): a graft's table = the host's whole table + the map's closure. F07 has 35,102
entries; of M11_B's 47,143 converted chunks 39,332 are appended ('verified: 46,080 reachable
chunks', so 28,374 entries of the build are F07's dead map); of M11_A's 45,330, 37,446.
Havana is simply chunk-heavy: its two halves bring 37,400 and 39,300 chunks where both halves of
Retomoto together brought about 27,500 (62,615 - 35,102).

What the chunks are (MEASURED: `rooms_chunks.py`, the level converted in memory as kl_graft does):

| M11_B group | nodes | chunks | only this group's | | M11_A group | nodes | chunks | only this group's |
|---|---:|---:|---:|---|---|---:|---:|---:|
| `Outside_Capitolio_01a` | 1,350 | 11,169 | 8,024 | | `Outside_Big_Square_01a` | 910 | 12,109 | 8,655 |
| clone groups without a template | 3,521 | 10,535 | 141 | | `Outside_Church_01a` | 574 | 9,216 | 3,943 |
| `Inside_Rooftop_Courtyard_Corridor_01a` | 1,232 | 9,460 | 6,508 | | `Outside_Market_Square_01a` | 670 | 7,669 | 5,249 |
| `Outside_Rooftop_01a` | 637 | 7,150 | 2,898 | | clone groups without a template | 2,634 | 5,697 | 142 |
| `Outside_Corner_To_Capitolio_01a` | 261 | 4,170 | 1,983 | | `Outside_Corner_To_Capitolio_01a` | 245 | 5,415 | 3,517 |
| `Inside_Capitolio_Main_Hall_01a` | 724 | 3,221 | 3,116 | | `Outside_Market_Sidestreet_04a` | 209 | 2,571 | 338 |
| End corridor + end room + side entrance | 615 | 2,238 | 2,130 | | `Outside_Capitolio_01a` (far view) | 221 | 1,368 | 1,065 |
| whole kept map | 10,044 | 39,330 | | | whole kept map | 7,244 | 37,444 | |

The light-map bake (`--ao 0.5`, kl_graft's default for Dead Men maps) clones 1,427 (M11_B) /
1,506 (M11_A) vertex chunks: without it the F07 builds would be 73,027 / 71,067 - still over the
tools' line (MEASURED: the 'baked AO' log line; the subtraction is mine).

Ways under the limit for ONE chapter, all MEASURED, none needing a tool that does not exist except (d):

| way | M11_B entries | M11_A entries | state |
|---|---:|---:|---|
| (a) F08 as the systems level | **66,368** (built, verify: no chunk problem) | 64,480 (sum, not built) | F08 has never been the systems level of a map that ran live; its escape is a helicopter, and every authoring tool names F07's objects |
| (b) F05 as the systems level | 56,953 (built) | 55,065 (sum) | as (a); F05 has vans; its .prm came out 90.0 MB (no trim below kl_graft's 90 MB line), bank 4,979 / 4,679 |
| (c) F07, then `python tools/kl_chars.py compact <lightened build> <out>` | **46,081**, .prm 69.0 -> 67.2 MB, its own check 'problems: 0', `kl_impact.py`: 0 problems | not run | the command exists and proves itself offline; NOT LOADED LIVE on any map (READ re/prm_limit.md 'Compaction') |
| (d) F07 without the rooftop / courtyard rooms | 63,310 (sum from the per-room closures; clone groups counted whole) | 65,223 without the market square | needs a new 'leave these rooms out' pre-pass (.gms, .oct trees, .rmi / .rmc, gates, mesh areas, Havok placements) |

BOTH chapters: 111,853 as built; the live part alone is 83,464 ('verified: ... 83464 reachable
chunks'), so compaction cannot save it. Cut down to M11_A's big square + corner and M11_B without
rooftop / courtyard the map side is still 52,692 chunks: F07 87,834, F08 79,748, F05 70,333 (sums,
`scenarios.py`) - over the line under every host; it would need (d) AND (c) together. **A two-chapter
Havana is blocked by this limit** as long as neither exists and is proven.

A wardrobe (READ re/prm_limit.md 'Results': 15,509 chunk indices, about +16 MB of .prm on Retomoto)
goes into dead indices where there are any: under (a) and (d) the count stays about where it is,
under (c) it comes on top: about 61,600. ASSUMED from Retomoto's numbers; not built here.

### 3.3 The large blocks of a level load (CLAUDE.md 'BUDGET for the builders')

MEASURED on the kept `F07+M11_B` build before it was deleted (`kl_graft.py lighten <build> <out>
--load trim,slim,fxc`; file sizes):

| block | F07 + M11_B as built | after lighten (trim, slim, fxc) | Retomoto as played | stock F07 |
|---|---:|---:|---:|---:|
| .prm (+ 0x60000) | 69.0 MB | 69.0 MB (67.2 compacted) | 76 MB (with wardrobe) | 63.6 |
| .fxc (+ 0x60000) | 17.8 MB | **8.63 MB** (242 -> 123 entries) | 8.9 | 8.1 |
| .ANM (+ 0x60000) | 21.6 MB | 21.6 MB | 20.6 | 21.6 |
| the whole .WAV beside the archive | 21.7 MB (21,668,176 bytes) | same | 27.8 | 18.3 |
| .TEX (not one block, but the address space) | 433.3 MB | **242.9 MB** (464 dead textures, 192.1 MB, shrunk) | 234 | 281.0 |
| archive | 362.0 MB | 223.2 MB | 212 | |

So lightened, Havana's blocks are Retomoto's size or smaller, except the .prm: with a wardrobe it
would be about 85 MB (ASSUMED: 69.0 + the 16.2 MB the wardrobe added to Retomoto), larger than any
.prm that has loaded (76.0 MB). klmem's reserve is 128 MB (READ klhook/klmem.c line 263), enough for
the block itself; what is left for the other refused blocks shrinks. Building the map with `--ao 0`
saves 5.4 MB of it and 1,427 chunks; the price is flatter light (the bake is what darkens corners).
The .ANM did not grow because the pre-pass leaves no animated campaign object in: 'clips +0'.

### 3.4 The navigation mesh

MEASURED (`navplot.py`, the build logs, `kl_maps.py preflight` on the kept build):
- kl_pf4 converts both meshes, no refusal, `kl_pf4.check` passes: M11_B 163 areas, 1,015 polygons,
  326 waypoints; M11_A 258 areas, 1,696 polygons, 766 waypoints. Links: M11_B has 13 (kinds 1 x6,
  2 x6, 6 x1) - the 6 of kind 2 stay, 7 are dropped; M11_A has 4, all kind 3, all dropped.
- M11_A: 44 connected parts, but ONE holds 1,585 of the 1,696 polygons and 18,524 m2: x -6064..20064,
  z -5076..22664 - market square, church, big square and the street north in one piece. The start
  flat is its own part of 24 polygons; its way down to the square was two kind-3 links from
  (-835, 222, -4990) to (-699, -103, -4905) (`links.py`), which the converter drops. The other two
  come down from the ruin at the church front (3010, 590, 10645) -> (3009, 20, 10399).
- M11_B: 17 parts with the kept links walked (19 without). Part 1: 606 polygons, **9,821 m2**,
  x 18435..43224, y 13..904, z 20460..33297 = the corner, the whole Capitol square, the side stair,
  the gallery, the hall, the bunker, the presidential corridor and the end room. Part 0: 313 polygons,
  1,238 m2 = courtyard house and roof. Part 13: 15 polygons, 2,283 m2 = the street east of the
  square. Part 9: 197 m2 between them. All 13 links of the level are at the roof's edge
  (`links.py`): six pairs up and down the parapet (kinds 1 and 2, x 27,096..27,480, y 1000 <-> 1060,
  z 21,064..21,255) and ONE of kind 6, cost 980, from the ledge (27703, 1000, 21267) down to the
  square (27703, 19, 21317) - the rappel. The converter drops kinds 1 and 6, so in a build the roof
  and the square are not joined for the AI. Round A (4.2) never leaves part 1 and does not need them.
- On the mesh, the only way between the square (y 20) and the Capitol's floor (y 800..840) is the
  side stair at x 26,700..27,600, z 29,300..30,250 (`routes.py`: main terrace -> square centre is
  165.3 m, via (28380, 840, 29370) -> (27540, 470, 30193) -> (27168, 200, 29095) -> (26667, 20, 27758)).
  The foot of that stair is where the campaign's barricade `SO0201_M11_BarricadeXX_01` stands until
  the tank removes it (1.4 step 4): its state at load decides whether anybody can use the stair.
- A two-chapter map would have both meshes in one (`kl_maps.nav_join`, 783,916 bytes, check passes)
  with no polygon joining them although they overlap on the ground; a hand-written link would be
  needed (the form `kl_fa_bots.add_drop` writes; READ CLAUDE.md: seen live on the bank, run H0_DM03).

### 3.5 What these levels have that no map which ran live has (MEASURED: `kl_maps.py first`, `preflight`)

`first` lists 53 (M11_A) / 58 (M11_B) classes and controllers. The ones with NO use in any stock Dog
Days level: `ZHavokMountedWeapon` + `MountedWeapon` (6 / 13), `ZRoad` (3 / 3), `VehicleWeapon` (4 / 3),
`ZVehicleFireOnRoadBehaviourRout` (4 / 7), `VehicleMoveOnRoadBehaviourRout` (2 / 2),
`VehicleFireBehaviourRout` (1 / 2), `PassengerAnimPosAdditionel` (6 / 0), `PsychoticController`,
`SmallTalkCtrl`, `WoundedFilter`, `SetPsychoModeDuration`, `TriggerPsychoMode`, `KaneLynchBox`,
`RappellingBox`, and in M11_B the crowd and the ropes: `ZHFlowLnkObj` 7, `ZHFlowFF2M11` 3, `ZRopeLnkObj` 5.
`MapControl` and `ObjectiveReminder` are not registered by kl2.exe (the converter drops them).
**All of them sit in subtrees the campaign pre-pass drops**: preflight on the kept F07 + M11_B build
reports each as 'in the build: 0'; what the build keeps beyond proven maps is `MatPosAnimProxy` x2
(falling planks of the courtyard house) and `BarrelEffects` x2, both used by every stock level.
Preflight's other checks on that build: 52 KEYS chunks all found, no controller outside its class,
0 torn stream records, lights nothing, 0 of 1,178 materials without a compiled shader, 16 rooms /
54 gates / 20 neighbour lists followed, .sgd sections present, 13 post-filter sets inside the palette.
M11_A was not kept and so not put through preflight; its pre-pass keeps only marker boxes and the
ambience group (1.2). One M11_A difference READ in tools/kl_prm.py (line 128, 163): the level has one
water object (lType 11; the build log says 'water': 1), which the converter replaces by an empty
mesh - a pool or fountain surface will be missing.

### 3.6 Crash classes of CLAUDE.md this map is exposed to

| class | exposed? |
|---|---|
| chunk table past 73,728 (globals overwritten, 0x607272) | YES under F07 as built (74,454); gone with 3.2 (a) / (b) / (c) |
| a large block that finds no address space (0x8e5bbd) | more than any map so far once a wardrobe is on (.prm about 85 MB); lighten is mandatory, `--ao 0` worth weighing |
| no settings object -> death camera (0x500990, 0x728ba3); exit trigger without monitor (0x6276fc) | until the layer is authored (the CRASH finding); `kl_fa.host_keep` keeps F07's monitor |
| bone ids of Dead Men people (0x4c34b3, a shot in a guard) | as soon as campaign soldiers are kept: `kl_impact` must stay at 0 (the build renumbered 4 of 4 skeletons) |
| squad behaviours (0x686a66, ZDefendBehaviourRout's member loop; cause open, re/crash_686a66.md) | as every map with the route bots |
| a relay naming its own node + 'GetMatPosAnim' (stack overflow 0x796ff4 at load) | an authoring risk if the swaps are wired through relays |
| JumpPoint fired for a Fragile Alliance player (0x8f40c9) | NO - one level, no join |
| unregistered class / empty pool / room fix-up (0x46fe87, 0x8adbba, 0x48e910, 0x719884) | verify passes: 19,188 entities, 16 room sets, 328 gate / list cells, 0 misfits |
| classes Dog Days never ran (mounted guns, vehicles on roads, crowd, ropes) | only if the author puts those squads back |
| the human-shield execution (0x4098a1) | repaired by the build ('ExecutionBloodSpatter' line in log.txt) |

---------------------------------------------------------------------------------------------------

## 4. The round

### 4.1 Three candidates

**A. 'El Capitolio' (M11_B alone): the crew is inside the Capitol when the round starts, loots the
presidential wing, fights its way out over the square to a van.** Section 4.2.

**B. 'Freedom Fighters' (M11_A alone): a street battle from the church to the Capitol corner.**
Start at the church front (`CP_02` (2399, 25, 9989), on the mesh), across the big square under its
monuments and pavilion, north up the street, van at the corner (18463, 51, 21463). MEASURED walk
387 m on one mesh part (`routes.py st_A.json`). Up to 26 squads / 50 actors can stay; the Hind's attack
would be the beat (its classes are stock Fragile Alliance classes: F02 F03 F06 F08 have police
helicopters). What it lacks: **loot that fits** - the level has no interior and no prop of value
(MEASURED `props2.py`: crates are 'Collapsed_Crates' rubble, the 'vaults' are church stonework; the
only carriers are the two gun jeeps and the BTR, which are classes Dog Days never ran). The loot
would be bags on a square. It is a good Heat-style shoot-out and a weak heist.

**C. 'Road to El Capitolio' (both chapters): big square -> street -> Capitol square -> Capitol.**
The geography allows it without a join (0.1). It is blocked by the chunk table (3.2), it would be
over 700 m of walking, and the two levels both model the Capitol square (M11_A as a far view,
M11_B in full), so rooms would have to be cut for that reason too.

### 4.2 Recommendation: A, 'El Capitolio'

All coordinates below are either campaign objects' own positions (MEASURED, named) or marked GUESS.
'On the mesh' = `routes.py` found a polygon of part 1 under the point.

**Start - in the middle of it.** The eight heisters stand under the dome of the main hall, where the
campaign's checkpoint 4 puts Kane and Lynch: `Special!Checkpoints!CP_04_PosP1` (33981, 808, 30387) and
`CP_04_PosP2` (33987, 808, 30165), both on the mesh (floor 829). START row: x 33,900..34,000,
z 29,900..30,900, facing +x down the hall (GUESS: the row; the two checkpoint places are proven
standing places of the campaign). Ahead, 47 m away, is the sandbag bunker with The7's last guards;
behind them the square is full of shooting. As on Subway and Retomoto the round opens with a
blast on a timer from the round-start event (which blast: next paragraph).

**The beat.** The campaign's bunker blast, all single objects, the same pattern as Retomoto's
window (READ re/retomoto_fa.md 2 'CAMPAIGN_KEEP'): `070_CapitolioInside!Enemies!BoomBoxDust`
(`Explode` + `AIDWrapper` 'Activate', at (38613, 902, 30398)), `...GeomActivatorDustExplosion` (the
`Capitolio_Explosion` emitters), `...Timer_SandbagsDeactive` -> `GeomActivatorSandbagsRemains` +
`GeomDeactivatorSandbags` (`SI0100_M11_BarricadeB_01` -> `..._Broken01` at (38697, 800, 30415)) +
`GeomDeactivatorExplosiveStuff` (two barrels (39140, 801, 30303), (39086, 801, 30509), a crate pile).
(corrected by the second agent: the list is one object short and one pair short. MEASURED, `refs.py` /
`geomsw.py M11_B` in G:/kl_scratch/cfa_havana/skeptic: `GeomDeactivatorSandbags` also takes away
`M11B_OYCHECK_BEFORE01` and `GeomActivatorSandbagsRemains` also brings `M11B_OYCHECK_AFTER01` - the two states
of the arch in front of the bunker, x 37,870..38,580, both flagged visible at load like the barricade pair;
and the doorway behind the bunker into the presidential corridor is shut by an INVISIBLE collision block
`...End_Corridor_01a\ColiObj_Obj_Roadblock_01` (x 39,458..39,754, y 800..1,500, z 31,295..31,374) which only
`070_CapitolioInside!Enemies!CapitolioInsideSoldiers_LastSeven_01\GeomDeactivator_Coli` removes. Blowing the
bunker does NOT open the wing: that fourth node has to be kept and fired too. See 'Verification'.)
Two places it can sit in the round: (1) at the start, as the opening blast (the crew then storms a
broken bunker), or (2) in the middle - the bunker is whole and manned, and it blows when its squads
are dead ('wiped out' list -> counter -> the blast; READ re/fa_gamemode.md 0.6), which opens the wing
with the loot. I recommend (2) with the opening blast taken from the square instead: the tank's
shots at the Capitol corner (`...Tank!T72!Destruction!GeomActivator_CapEntranceCorner` /
`GeomDeactivator_CapEntranceCorner`, the corner at (32000..33320, 0, 28900), 15 m from the START row
through the wall). (corrected by the second agent: (1) those two numbers are the pieces' PIVOTS; the corner's
collision and model box are x 31,432..32,350, z 28,500..29,616 (`objs.py`), 16 m from the row's near end.
(2) There is no blast there to take: `...T72!Destruction!*` holds five timers, the three swaps and a path
blocker - no `Explode`, no emitter, no `ShakeCamera` (`objs.py M11_B "T72!Destruction" --vals`, `near.py`).
In the campaign the bang, flash and shake are the tank's SHELL, `Rocket_T-72` in Dead Men's own
`mainsceneincludes.zip` (an `Explode` + `ShakeCamera` 'EXPLODE_Explode_Impact'), fired by a `VehicleWeapon`:
systems the graft replaces and a class Dog Days never ran. Fired alone the swap is a wall that changes
silently; the opening blast has to be borrowed from F07 as Retomoto's was. Only the two ambience sound
objects `Sound!Ram!Outside!Capatulio_Explodes` (at the corner and at the stair barricade) are the level's.
(3) The corner swap is not a choice of blast: it is needed for the escape, see 'Escape' below.) The state at load, MEASURED (`hidden.py`: .gms flag 0x400 + ZGEOM[3], the rule of
re/retomoto_fa.md 2): the side-stair barricade `SO0201_M11_BarricadeXX_01` is SHOWN; the corner
`SO0201_M11_Corner_01` is shown and `..._CornerBroken_01` hidden (flags 0x2205f2, ZGEOM[3] = 1), so
the corner is whole; of the bunker's barricade BOTH `SI0100_M11_BarricadeB_01` and `..._Broken01`
are flagged visible (the campaign must hide one by script at its start: not found, not established).

**Loot - props of the place** (MEASURED: `props2.py M11_B "Shop_Montre|Painting|SupplyCrate|Table_A"`):
- 11 glass display cases in the presidential wing: `PC0200_CUB_Shop_Montre_A_01..04` in the end
  room at (42631, 878, 32550), (42610, 878, 31249), (42020, 878, 31445), (42020, 878, 32405);
  `..._Montre_B_02 / 05 / 06 / 07 / 08` in the corridor at (39358, 936, 31012), (40797, 936, 32157),
  (40803, 936, 31673), (40197, 936, 32467), (40203, 936, 31363); `..._Montre_C_01` (39550, 800, 31915);
  `..._MontreLow_A_01` (39722, 810, 31537). A case (`ctrlvals.py M11_B "Shop_Montre_B_02"`) is four
  to six groups `Montre_Shotactivate_NN`, each a pane `Glass_NN` with a `ShotActivate` controller
  that fires debris, glass smoke and splinter emitters and `Glass_Break_Sound` (51 such groups in
  the level), round 11..24 `ZHavokRigidBody` pieces: shoot the glass and the contents fall out.
  The level's effect set holds `Template_Samurai_Montre` (glass smoke, splinters, debris), the very
  template M09_A's effect set has for Retomoto's samurai cases (MEASURED: the node and its three
  children are in both levels) - the same family of prop the owner already accepted as loot there.
- 5 paintings on the corridor walls: `PC0200_CUB_Painting_A_02` (41400, 800, 31615), `_B_01`
  (39900, 800, 31015), `_B_03` (40500, 800, 31465), `_B_04` (41400, 800, 32215), `_C_02` (40500, 800, 32365).
- The end room's table `PC0200_CUB_Table_A_01` (42650, 802, 31915): the big prize (briefcases, as
  on Retomoto's boardroom table).
- For the way out: 8 army supply crates on the terrace at the main barricade,
  `PC1106_VEN_SupplyCrate_A_02 / 03 / 09 / 10 / 11 / 12` and `..._Grenades_01 / 02`,
  (32684..34673, 800..851, 28143..29044).
The loot objects themselves are F07's pool stacks moved to these places (15 + 6 were enough for
Retomoto; F07 has 108 + 25: READ re/retomoto_fa.md 2), dressed by `kl_fa_loot` as on Retomoto
(briefcase on the table; a fitting piece at each case). Money prop: Dog Days' own stacks / bags;
Dead Men's `Jewelbag` (M02_FA_A) would suit the cases best but is another level's model. Suggested
values GUESS: 11 x 150,000 + 5 x 100,000 + table 6 x 300,000 = 3,950,000 (Retomoto: 4,050,000).
The four cases tested and the table are 1.5..4.6 m from the middle of a mesh polygon of part 1
(`routes.py`): reachable.

**Enemies.** Guards = The7's soldiers, the campaign's own squads kept by squad_plan's rule (1.5):
inside `CapitolioInsideSoldiers_LastRoomFight_01` (2, at (41983, 807, 30822)) and `_02` (1, at
(41851, 804, 33118)) in the wing; the bunker's `SevenDudes_01 / _02` and `LastSeven_01` once their
`MountedWeapon` / geometry controllers are taken off (3 more; the two machine-gun nests themselves
are a class Dog Days never ran: leave the guns out, GUESS that riflemen behind sandbags are enough).
'Police' = the same army coming back at the crew: the 11 squads / 24 actors of the terrace, the
side stair and the square that can stay as they are (`RebelSideBarricadeSideEntrance_01 / _02`,
`SideBarricadeTopFloor_01 / _02` at the stair top (27600..27800, 802, 29190..29385),
`MainBarricadeEntrance_01` and `GotoHole` on the terrace (33400..33928, 803..827, 28842),
`RebelSideBarricade_01` (6), `_Guard` (2), `SideEngage_01 / _02` (4 + 4) at the stair's foot
(26612..27383, 163..211, 29153..29756)). 27 actors with M4s, Minimis, pistols and one RPG, against
14..20 on Dead Men's own Fragile Alliance maps and 63 on Retomoto (READ re/fa_gamemode.md 1.1,
re/retomoto_fa.md 0): the courtyard's 10 squads / 15 actors can be re-placed onto the square if it
is too thin. They are held (`eStayBack` / not started) until a criminal leaves the wing with loot
(the Retomoto street pattern: a trigger box starts them), and they come from where the crew has to
go: the terrace and the side stair. Police players respawn (AFTER_DEATH) at places campaign actors
stand on (all on mesh part 1): stair top (27797, 803, 29385), terrace (32822, 802, 28359), the
stair's foot (26972, 208, 29431), (26612, 163, 29756). Not at the loyalists' corner
(21992, 32, 21100): it lies behind the campaign's level bound, a police player would have to walk
round the slab's east end (x 22,407).
kl_arms gives them Dog Days weapons by class, kl_map_ai's lesson applies (skill `eCustom` or the
numbers are overwritten: READ CLAUDE.md 2026-10-10 13:25).
The loyalists: leave them out of the first build. They are `Ally`, the faction of the seven AI
heisters in every stock level (MEASURED `factions.py`: 7 `Ally` in each of F01..F09), so three
loyalist squads charging the square beside the crew is a real option for the mood of a civil war -
but what the round's rules make of thirteen more allies (traitors, the police player, the score) is
LIVE only. The crowd, the tank, the BTRs and the Hind stay out (classes of 3.5); the Hind as a
later extra is the least risky of them (stock helicopter classes).

**Escape.** F07's key-framed van (`Animation/F07/F07_Escape_Vehicle_01.zip`; re-laid by
`tools/kl_fa_van.py` as on Retomoto, READ re/retomoto_ai.md / CLAUDE.md 'Van'), on the Capitol
square. The crew leaves the hall by the gallery, goes down the side stair and crosses the square
to its south side. The stair's foot is barred at load: `SO0201_M11_BarricadeXX_01` stands at
(27170, 0, 28516), shown (MEASURED), exactly on the mesh's only way down ((27175, 160, 28510) is a
point of the measured path; the campaign keeps a `PathBlocker` box at (27173, 153, 28520) until the
tank has shot). So the campaign's `...T72!Destruction!GeomDeactivator_Barricade` has to be kept and
fired at round start. Fired at run time rather than hidden at build: on Retomoto the campaign's
own `DeactivateGeom` took the window glass and its collision away (READ CLAUDE.md 2026-10-09 21:25, run P3s: 'glass goes at the blast');
whether a build-time hidden flag also removes a static Havok shape is not established.
(corrected by the second agent: the barricade is not the only thing in the way. MEASURED, `walk2.py` /
`walk3.py M11_B`, the mesh and the .HVK static collision together: with the barricade gone the crew still
cannot get from the hall to the side stair - the gallery and the hall's front door / terrace are joined only
THROUGH the Capitol's corner, and `SO0201_M11_Corner_01` (whole at load) fills that place (5 blocked cells,
x 31,887..32,312, z 28,837..29,212). With `GeomDeactivator_CapEntranceCorner` + `GeomActivator_CapEntranceCorner`
fired as well the leg is free. Both tank swaps are mandatory.)
Van line GUESS: straight along z 22,600 from the street east of the square (x 35,500) westwards,
waiting out of sight at x 34,000, stop at x 27,000, away to x 22,000 (130 m; F07's drives are
121..152 m). MEASURED for that line (`runs.py`, `inbox.py`): mesh part 1 runs unbroken along
z 22,600 from x 21,950 to x 31,100 (91 m of open square; along z 22,000 from x 21,100 to x 31,500,
104 m; along x 27,000 from z 21,350 to z 28,000), the street east is mesh from x 32,550 to
x 35,250 (part 13), and between them the square's east edge is a row of six concrete road blocks
`PC0800_CUB_Roadblock_Concrete` at x 31,870 (two must be hidden, as one barricade was on Retomoto).
A wrecked car stands at (29444, 1, 21826); the campaign's BTR start (31938, 9, 23032) is empty once
its squad is dropped. Boarding point and exit box at the stop (27000, 19, 22600): the place is a
GUESS, that it is on the mesh is MEASURED. The far end of the map from the loot: 330 m on foot.
(corrected by the second agent: 'unbroken mesh' is not 'a line a van can take'. MEASURED from the collision,
`vanline.py`, `column.py`, `ground.py`, `vanscan.py` in G:/kl_scratch/cfa_havana/skeptic: the mesh is one flat
sheet at y 20; the road is y 0 and has shell craters the mesh spans. On z 22,600 the ground is at -150..-177
from x 29,650 to x 30,450 (on the way in from the east) and at -80..-113 from x 22,450 to x 23,450 (on the
way out); the clear straight run on that line is x 23,500..29,600, 61 m, and the stop x 27,000 lies in it.
The longest clear straight run anywhere on the square is 73 m (z 21,800..22,000, x 21,850..29,150); F07's
drives are 121..152 m. The road blocks are not 'six at x 31,870': they stand between x 31,350 and
x 32,100 depending on z, and with them stands an invisible, unscripted wall along the whole east edge
(`ColiObj_Obj_Roadblock_20`, collision x 31,200..31,995, z 21,400..25,671, 15 m high, continued north by
`ColiObj_Obj_Roadblock_19` to z 28,271); the west end is shut the same way (`PC0300_M11_RubblePiles02`
x 21,450..21,750, `ColiObj_Obj_Roadblock_30`, collision x 20,944..21,864, z 21,259..23,414). So the van can stop where proposed, but it cannot be seen to arrive from a street or to
'drive off down the road': both happen inside a closed square, in view, unless craters are crossed and
pieces hidden. The van line is open design work, not a table entry.)
A helicopter from the square (F08's, if F08 becomes the host for the chunk table's sake) is the
alternative; it would suit a war, but there is one helicopter map already (A Walk in the Park).

**Level bounds.** The campaign's own, kept by the pre-pass: `Special!LevelBounds!CapitolioSquare!
LevelBound_Corner!Bound` (21235, 348, 22324), half (1172, 459, 108), closes the street back to M11_A;
`...LevelBound_Top!Bound` (22814, 348, 29859), half (3180, 459, 92), the square's north-west. To add
from F07's six (GUESS, places to be looked at): the square's east edge behind the road blocks
(x 32,300), the door of the courtyard house on the square's south side, and the hole in the Capitol
corner if it stays shut for players. (corrected by the second agent: the hole cannot stay shut - it is the
only way from the hall to the side stair, see 'Escape'. The square's east and west edges already carry
invisible walls for players, `ColiObj_Obj_Roadblock_20` and `_30`.)

**Music.** One clip set, the chapter's theme in three layers, shared by both levels (MEASURED
`music.py`, `kl_str.py list <Dead Men PC_Def.str> Havana`): set `LevelSetup/Level/M11_A/Music/M11_Havana_Layer`
= `Music/InHouse/M11AB/M11_Havana_Layer_A.wav`, `_B.wav`, `_C.wav`, PCM stereo 32 kHz, 162.6 s each,
31.2 MB in the stream file; sound objects `audio:levelsetup/level/m11_a/music/m11_havana_layer_a / _b / _c#sound`.
The campaign plays them through seven `PlayMusic` groups with `PlayMusicLayerFade` children
(`070_CapitolioInside!Music!PlayMusic_CapitolioInside`: layer C at -5 dB, A and B faded in over
120..140 s; `060_CapitolioSquare!Music!PlayMusic_CapitolioSqr`: layer A at -6 dB). Not in today's
merged PC_Def.str (0 clips named Havana): it needs one more extended merge by `kl_str.py`
(`MUSIC['M11_B']` = the three objects) and the owner's go-ahead for the stream file, as Retomoto
did. ASSUMED that a three-clip set merges like Retomoto's two-clip sets (the file format has one
record kind for both); to be heard LIVE. Started as on Retomoto: the inside `PlayMusic` group kept
and fired with the opening blast, the square one when the crew comes out.

**Voice.** `Dialog/M11/Dialogue`: 107 situation lines and 19 one-liners in the level's bank
(126 sound objects; 156 clips in Dead Men's stream file). Worth carrying for the talk system
(`kl_fa_talk`): `M11_StormingElCap_010 / 020 / 040_Hero` (Kane storming the Capitol - the round
start), `M11_EntranceSquare02_*`, `M11_NearSquare_010_Hero`, `M11_FightLibrary_*` (with a Spanish
opponent line), `M11_MercBoss_*` and the 'MoneyWhine' exchange (mercenaries demanding their pay:
made for a game about splitting loot), `M11_ChopperAproach / Close / Dead_*` if the Hind ever
comes. The soldiers' barks are `AllLevels/Oneliners/SpanishOneLiners` (56 .LOC keys) - the guards'
language, as the Japanese lines are on Retomoto (kl_voice's repeat fix applies).

**The seven AI heisters' route** - every station on mesh part 1 (MEASURED `routes.py`; lengths are
shortest paths over the polygons):

| # | station | place | leg |
|---|---|---|---:|
| 1 | START row, the hall under the dome | (33981, 829, 30387) | - |
| 2 | ENTERS_BANK plane across the hall (stage 1) | x 36,000 GUESS | |
| 3 | hold before the bunker until it blows | (37671, 805, 30521) = `CP_05` | 47.3 m |
| 4 | through the bunker | (38899, 829, 30415) | 11.1 m |
| 5 | loot stops at the cases (they must shoot the glass: the Late Night Opening recipe, READ re/bots.md 12.1) | (39550, 800, 31915) -> (40203, 800, 31363) -> (40797, 800, 32157) -> (42020, 800, 31445) | 23.8 + 7.0 + 8.3 + 17.5 m |
| 6 | the table | (42650, 802, 31915) | 11.1 m |
| 7 | back through the hall | (33981, 829, 30387) | 108.5 m |
| 8 | terrace, gallery west, EXITS_BANK plane at the stair top (stage 2) | (32822, 839, 28359) -> (28380, 840, 29370) -> (27770, 810, 29370) | 26.7 m + |
| 9 | down the side stair, foot of the stair | (27540, 470, 30193) -> (27168, 200, 29095) -> (26667, 20, 27758) | |
| 10 | rally on the square, outside the exit box | (25000, 20, 24500) | 165.3 m from the terrace |
| 11 | exit box (stage 3, the van is called), beside the stop | (26500, 19, 21900) | 34.1 m |

About 460 m for a bot, against 455..496 m on Retomoto (READ re/bots_retomoto.md 1). One mesh part,
no jump, no hook teleport, no hand-written link: simpler than Retomoto's bots.

### 4.3 Against a sibling

Havana has no Fragile Alliance sibling. Next to the five maps on the tab it is the only daylight
war zone, the only state building, the only one whose enemies are an army with RPGs, and - if the
loyalists are let in - the only one with a third party on the field.

---------------------------------------------------------------------------------------------------

## 5. What has to be authored

The kinds are Retomoto's (READ tools/kl_fa_author.py head and tables; re/retomoto_fa.md 2). 'Has' =
the level or F07 already holds the object; everything is re-placed and re-wired, nothing is created.

| what | from | M11_B has | work |
|---|---|---|---|
| settings, define, speakers, briefing, round-start hub, escape monitor | F07, kept by name | no | none (as Retomoto) |
| 8 START, 4 TRAITOR, 7 AFTER_DEATH, UCC / team points, 16 player groups | F07's 63 spawn points, `Heroes!*` | 10 checkpoint places `CP_01..05_PosP1/P2`, 7 jump points as proven standing places | a table of places |
| spawn cameras, team stage triggers | F07 | no | places (GUESS, as Retomoto) |
| loot marker, ENTERS / EXITS planes, escape marker | F07 `FASpecials!POI!*`, `PIP!*` | no | places |
| loot: 22 stacks at cases, paintings, table | F07 pool stacks; `kl_fa_loot` for the dress | the props (4.2) | a table; the case glass for the bots |
| 'bunker cleared' -> blast -> wing opens | F07 counter + activator | the blast and both geometry states (4.2) | wiring; campaign single nodes kept (the `CAMPAIGN_KEEP` list) |
| the way out: side-stair barricade (shown at load: it bars the only way down), Capitol corner (whole at load) | - | `...T72!Destruction!GeomDeactivator_Barricade`, `GeomActivator / Deactivator_CapEntranceCorner` and both states | keep and fire at round start (4.2 'Escape') |
| (added by the second agent) the door of the loot wing: an invisible collision block, there at load | - | `...CapitolioInsideSoldiers_LastSeven_01\GeomDeactivator_Coli` -> `...End_Corridor_01a\ColiObj_Obj_Roadblock_01` | keep and fire with the bunker blast; without it no loot can be reached |
| level bounds | F07's six | 2 (4.2) | 3 places |
| exit trigger, van(s), boarding, cameras | F07 `Gameplay!EscapeSetup!*`, `Animation/F07/F07_Escape_Vehicle_0n.zip`, `kl_fa_van` | nothing | the van's line on the square, two road blocks hidden |
| guards and police | `squad_plan` rule with M11_B's prefixes (the SQUADS table), kl_arms | 13 squads / 27 actors ready, 5 more after a strip | prefixes, starters, the trigger box; mounted guns off |
| music | `kl_str.MUSIC`, a kept `PlayMusic` | the clips | one entry + a stream merge |
| AI heisters | `kl_fa_bots` plan / make, the dynamic and route steps | one mesh part | stations (4.2); no join part |
| talk, Bain, wardrobe, gun looks, lighten | the existing steps | - | as every map |
| **the chunk table** | 3.2 (a), (b) or (c) | - | **before anything else** |

Size of the work: **about 0.8 of Retomoto** (Retomoto = 1.0). Cheaper than Retomoto: one level instead
of two (no chain, no nav_join, no elevator join, no KLJoin hook part, no two-part bot squad - those
were the join's cost in re/retomoto_fa.md 3 and re/bots_retomoto.md 2); the standing places, the
blast, both wall swaps and the loot props exist as campaign objects; the route is one mesh part.
Dearer: the chunk table has to be settled first, with a path that has not run live (0.15); the van
needs a line on a plaza instead of a road; the authoring tool's tables are Retomoto's own, so a
second set (or a small generalisation of `kl_fa_author.py`) has to be written; the level's state at
load (which 'Collapsed' / 'Broken' pieces show) has to be established before places are trusted.
The two-chapter map C would be above 1.6 and is blocked.

Order of steps to a first load (nothing here is started by this study):
1. Chunk table. Cheapest proof: load the compacted Retomoto experiment that already exists
   (`<work>/build/x_chunks/retomoto_wardrobe_compact`, READ re/prm_limit.md) once - if HUD, fonts and
   effects are right, compaction is proven for every map and F07 stays the host. Else host F08.
2. Bare first load: `kl_maps.py one <out> F07 M11_B --campaign --heroes --keep` with a `HERO_AT`
   entry for M11_B (`Special!Checkpoints!CP_04_PosP1 / _PosP2`; two lines in kl_maps.py, its
   owner's edit), lighten, compact, direct boot: does it load, is the hall lit and textured, where
   can the scripted walker go (the bunker, the side stair's foot, the corner).
3. The layer: places, loot, swaps, bounds, exit trigger, one van; `kl_fa.check` to 0 CRASH / BROKEN.
4. Squads and arms; a round from the tab (slot F07, the sixth and last free one: the other campaign
   candidates of this study compete for it).
5. Bots, dynamic step, loot dress, music (stream merge), talk, wardrobe.

---------------------------------------------------------------------------------------------------

## 6. Risks, and what only a live run can settle

- **Compaction has never loaded** (or: F08 / F05 have never been the systems level of a live map).
  One of the two has to be seen working before any Havana authoring is worth doing.
- The .prm will be the largest yet with a wardrobe (about 85 MB): the 0x8e5bbd class on a second or
  third load of one process. Measure with klmem's log lines.
- The level's state at load is half known (4.2): the side-stair barricade stands, the corner is
  whole; whether the bunker can be walked through before its blast, and which of its two barricade
  models shows, has to be seen. If the stair's barricade does not go when its `DeactivateGeom` is
  fired, nobody leaves the Capitol: the first thing to test in a direct boot.
- Whether Dog Days plays the bunker's `Explode` + emitter chain and the tank-shot swaps as Dead Men
  does (Retomoto's window did: LIVE precedent, same controllers).
- Light: the hall is lit by 110 map lights and a baked light map; under a Dog Days host with the
  bake at 0.5 it may be dark or flat. The four FA maps and Retomoto needed looking at for this.
- The van on a plaza: height (the square is y 19..20 by the mesh - corrected by the second agent: that is
  the mesh; the road is y 0 with craters down to -177, see 4.2 'Escape'), the road blocks, the wreck;
  whether the crew's last 100 m over open ground is playable against 20 rifles and an RPG.
- Three-layer music set through the stream merge; which layer mix sounds right.
- Loyalists as `Ally` actors in an Arcade round; the Hind as a police helicopter: both untried ideas.
- Soldiers' models at a distance (the 'invisible police' fault of Retomoto was a far-detail shader:
  READ CLAUDE.md 2026-10-09 18:20) and their Spanish barks repeating.
- Not established offline: what stands in the display cases (their rigid pieces were not rendered),
  the exact door through which the hall meets the terrace, the 'hole' the tank makes as a second way.
  (corrected by the second agent: established - the hall meets the terrace through its front wall
  `SI0100_M11_WallFrontDoor_A_01` (free at load, 22 m from the START), and the tank's hole is not a second
  way but the ONLY way on from there to the gallery and the side stair: 'Verification', corrected 2.)
- M11_A only: one water object is replaced by an empty mesh; preflight was not run on it.

---------------------------------------------------------------------------------------------------

## 7. Verdict: feasible-with-work

Havana can become a Fragile Alliance map, as ONE chapter: 'El Capitolio', the storming of the
Capitol turned inside out - the crew starts under the dome, blows The7's bunker, empties the
president's display cases and has to get back out across the square to a van while the army closes
in. Everything that makes such a round is already in the level as campaign pieces (standing places,
the explosion, the walls that open, the glass cases, soldiers who can stay, the theme music), the
whole route is one walkable piece for the AI heisters, and there is no join to build. It is not
ready to author today for one reason: the level has more model pieces than the game's table holds
when it is built the usual way, so the first job is to prove one of two existing answers in the
game (a clean-up of the model file that has never been loaded, or another Dog Days level as the
base). Both chapters as one long map - the street battle AND the Capitol - do not fit the game at
all and should not be tried. The street chapter alone would work too, but it has nothing worth
stealing in it.

---------------------------------------------------------------------------------------------------

## Verification (second agent)

2026-10-11, agent cfa-havana-skeptic. OFFLINE; nothing installed, the game not started, no tool edited.
My own scripts (independent of the first agent's; read-only on the game files) and their outputs:
`G:/kl_scratch/cfa_havana/skeptic/` - `sk.py` (the Dead Men mesh read raw with struct, adjacency by the
neighbour field AND by shared edge geometry), `nav1.py`, `objs.py` (object -> class, .gms flags, model
box in the world, .HVK shapes), `refs.py` / `geomsw.py` (who names an object; every ActivateGeom /
DeactivateGeom), `walk.py` + `walk2.py` (the mesh AND the .HVK static collision together on 25 cm cells:
can a person walk from A to B, and which entity stands in the thinnest place), `vanline.py`, `column.py`,
`ground.py` (the ground of the square from the collision, not from the mesh). Trial builds re-run into
`<work>/build/cfa/havana/skeptic/` (result.json / log.txt kept, every archive deleted).

More scripts there: `walk3.py` (which campaign removals the route needs), `vanscan.py` (clear straight lines on
the square), `facts.py`, `montre.py`, `links.py`, `dups.py`, `near.py`, `ctl.py`, `row.py`, `poly.py`.

**Outcome.** Every number of the report that I re-ran came out the same to the digit (builds,
compaction, lighten, mesh, music, squads, cases). What it gets wrong is the ROUND: as written nobody can reach
the loot and nobody can leave the Capitol with only the swaps it plans, the opening blast it names does not
exist as an object, and the van line it guesses runs through two shell craters with both ends walled off.
None of that blocks the map; all of it is more authoring than section 5 counts. My verdict stays
**feasible-with-work**, effort about 1.0 of Retomoto (0.8..1.2) instead of 0.8, and the chunk table is still
the first job.

How the walk test works, because three corrections rest on it (`walk.py`): every 25 cm cell whose middle lies
in a polygon of the level's own navigation mesh gets the collision floor under it (the up-facing .HVK triangle
nearest to the mesh height) and the set of entities whose STATIC / key-framed collision passes within 30 cm of
its middle at 50, 100 or 150 over that floor; entities with the hidden flag 0x400 are left out. A way is a
chain of free neighbouring cells; `walk2.py` finds the crossing with the fewest blocked cells and names what
blocks them. It reproduces the two gates the report already treats as gates (stair barricade, bunker wall:
blocked at load, free once the campaign's own `DeactivateGeom` target is taken out) - and finds two it does
not (the Capitol's corner, the door of the wing). Limits: loose
props (RIGID shapes) are not counted, 30 cm is my figure for a person, and 8,104 of 221,919 cells found no
collision floor within reach and use the mesh height.

### Corrected

1. **The loot wing is behind a scripted INVISIBLE WALL at load** (not in the report). MEASURED
   (`walk2.py M11_B`, `objs.py M11_B "ColiObj_Obj_Roadblock_01$" --vals`, `refs.py`): the only doorway from
   the hall's east end into the presidential corridor is closed by
   `...M11_B_Inside_Capitolio_End_Corridor_01a\ColiObj_Obj_Roadblock_01` - a STATIC collision shape,
   x 39,458..39,754, y 800..1,500, z 31,295..31,374, .gms flags 0x200308 (not hidden). Its collision
   sub-parts carry the flags 0x108 and nothing else, where a wall has 0x72: that is the flag set of the
   levels' HERO blockers in BOTH games (`flagnames.py M11_B F07 F03 L03`: 0x108 alone is on `ColiObj_Hero`,
   `ColiObj_BlockHero`, `ColiObj_Obj_Roadblock` in M11_B and on `ColiObj_HERO_hack`, `ColiObj_HeroBlocker`,
   `ColiObj_DD_Hero` in stock Dog Days) - a wall for the player's character; that it is not drawn is ASSUMED
   from the name, it was not rendered; whether it also stops an AI heister is not established (the campaign
   does not rely on it: see the path blocker). The campaign takes it away with
   `070_CapitolioInside!Enemies!CapitolioInsideSoldiers_LastSeven_01\GeomDeactivator_Coli` (a `DeactivateGeom`,
   in a subtree the pre-pass drops) and keeps a `PathBlocker_LastGuys_01` at (39597, 802, 31215) on the same
   doorway until then (`ctl.py M11_B PathBlocker`). All 11 display cases, the 5 paintings and the table are
   behind it (`walk3.py`: START -> table is BLOCKED by it alone once the bunker is open; free, 90 m of cells,
   when it is gone). One more campaign node to keep and fire - but as the round is written in 4.2 ('the bunker
   blows ... and opens the wing') nobody reaches the loot. The report's own squad table had the hint: the
   squad 'that holds the geometry swap' is this one.
2. **The Capitol's corner is not 'a second way': it is ON the only way out.** MEASURED (`walk2.py`): between
   the hall's front door / terrace (x > 32,350) and the gallery that leads to the side stair (x < 31,430)
   the mesh's only connection runs through `SO0201_M11_Corner_01`'s collision (5 blocked cells at
   x 31,887..32,312, z 28,837..29,212, floor 800); with `Corner_01` gone and `CornerBroken_01` there the same
   leg is free (46 m). The campaign's objective marker 'Get To Main Entrance' (32095, 888, 29022) stands in
   that hole. So the escape needs BOTH tank swaps (corner AND stair barricade), not the barricade alone.
3. **The van line of 4.2 (z 22,600) is not level ground.** MEASURED (`vanline.py M11_B 22600 35500 20500`,
   `column.py`, `ground.py`): the navigation mesh is a flat sheet at y 20 over the whole square, the road
   itself is y 0 (`SO0202_M11_RoadSection_40x40m_*`), and the road sections have shell craters the mesh
   spans: on z 22,600 the ground is at -150..-177 from x 29,650 to x 30,450 (between the east edge and the
   proposed stop) and at -67..-113 from x 22,450 to x 23,450 (on the leave leg). 'the square is y 19..20 by
   the mesh' is the mesh's height, not the ground's. Both ends of the line are shut: east by the concrete
   road blocks (they stand between x 31,350 and x 32,100 depending on z, not 'six at x 31,870') AND an
   invisible wall `ColiObj_Obj_Roadblock_20` (collision x 31,200..31,995, z 21,400..25,671, 15 m high, hero
   blocker flags 0x108, named by no script; `ColiObj_Obj_Roadblock_19` carries it on to z 28,271), west by
   `PC0300_M11_RubblePiles02` (x 21,450..21,750) and the invisible wall `ColiObj_Obj_Roadblock_30`
   (x 21,700..21,800): 'away to x 22,000' ends 2.5 m in front of a rubble pile, in full view.
   What IS there (`vanscan.py M11_B 21400 27800 200 20000 36400`: ground within 25 of the road over 2.4 m of
   width and no static collision at 40..160 over it): on z 22,200..22,600 a clear run x 23,500..29,600, 61 m,
   the proposed stop x 27,000 in its middle; the longest on the square is 73 m (z 21,800..22,000,
   x 21,850..29,150, ended by a car wreck in the east and a crater in the west). F07's drives are 121..152 m
   (READ, the report). Five craters deeper than 1.2 m lie on the square and the east street (`ground.py`, 2 m
   grid; the part deeper than 1.2 m is at x 22,600..23,400 z 22,800..23,600; x 25,600..26,000 z 23,200..23,800;
   x 29,800..30,600 z 22,400..23,200; x 30,800..31,200 z 26,800..27,400; x 34,800..35,200 z 22,800..23,400;
   each has a shallower rim of 2..4 m round it). So the van can STOP where the
   report puts it; what cannot be had without more work is an arrival from out of sight and a leave leg that
   'drives off down the road the whole time' (the owner's words about Retomoto's van, CLAUDE.md
   2026-10-10 12:30): on this square both would begin and end in view, 30 m from the stop.
4. **'The round opens with a blast (the tank's shot at the Capitol corner)': there is no such blast object.**
   MEASURED (`objs.py M11_B "T72!Destruction" --vals`, `near.py`, `refs.py`, `ctl.py M11_B Explode ShakeCamera`):
   `060_CapitolioSquare!Friendlies!Tank!T72!Destruction!*` is nine nodes - five `TriggerDelay`, the corner pair,
   the barricade deactivator, a collision-hack deactivator, one `PathBlocker`. The level's only two scripted
   `Explode` objects are `070_CapitolioInside!Enemies!BoomBoxDust` (the bunker) and `050_Rooftop!BlockEntrance!
   BoomBox` (the courtyard door); its only scripted `ShakeCamera` is the Hind's. What the player sees and
   hears at the corner in the campaign is the T-72's shell, `...equipment.zip\Projectile\Projectiles_01\
   Rocket_T-72` (`Explode` + `ShakeCamera`, effect `FX_Grenade_T72_01/02`) - Dead Men systems, fired by a
   `VehicleWeapon`; neither comes through a graft. The bunker blast is real (confirmed below); the opening one
   has to be F07's blast layer moved here, as on Retomoto (READ CLAUDE.md 2026-10-09 18:40 'more VOLATILE').
5. **Smaller ones.**
   - 'the corner at (32000..33320, 0, 28900)' are two pivots; the piece is x 31,432..32,350, z 28,500..29,616.
   - 'A case is four to six groups ... round 11..24 rigid pieces': `PC0200_CUB_Shop_MontreLow_A_01` has two
     `ShotActivate` panes and no rigid piece at all (`montre.py`); the other ten are as said (A: 6 panes / 11
     pieces, B: 4 / 12, C: 5 / 24).
   - 'absent from today's merged PC_Def.str' was tested on `<work>/build/PC_Def.str`, which is the PREVIOUS
     merged file; the one installed is `<work>/build/v_bain/over_talk/PC_Def.str` (READ CLAUDE.md
     2026-10-10 19:15). `kl_str.py list <that file> Havana`: 0 lines too - the statement holds.
   - 'no clean-up can bring the pair under 73,728' is true of dead entries (83,464 live, re-measured) but not
     of duplicates: 6,015 of M11_A's 43,767 chunks (19.9 MB) are byte-identical with a chunk of M11_B
     (`dups.py`), and the chain appends them again (37,374 of 37,446) while it does share textures (+134
     instead of +585) and materials (+145 instead of +450). A de-duplicating append does not exist; with it
     the pair would land near the table's end, not safely under it (ASSUMED, my estimate: 6,015 equal
     chunks and the parents that become equal, taken from 83,464). The conclusion (do not try both
     chapters) stands.
   - A host the report did not try: `kl_maps.py one <out> F09 M11_B --campaign` -> **69,805** entries (3,923
     slots free; the tools want 4,096), 12 problems, .prm 69.0 MB, .TEX 438.0 MB, bank 4,548 / 4,420. F09 has
     three key-framed vans like F07 (READ re/maps.md table at line 188) and is of F07's grading family;
     without the light-map bake it would be 68,378 (sum, not built: `kl_maps one` does not pass `--ao`).
     Like F08 and F05 it has never been the systems level of a map that ran, and the tools name F07's vans.
   - The 'police' squads that 'can stay as they are' are not out of sight at the start:
     `RebelMainBarricadeEntrance_01` (2, at (33928, 827, 28842)) and `RebelGotoHole` (1, at (33400, 803, 28848))
     stand about 11 m from the START row, outside the front wall's door (`facts.py squads`). Held or not, they are
     the first thing the crew sees; they need other places, like every 'present from the load' squad
     (READ CLAUDE.md 2026-10-10 13:25).
   - The AI heisters' pathfinder gets no warning of any of the four gates: the campaign's ten
     `Special!RemovePathfinder!*` path blockers (bunker slot (38660, 802, 30401), wing door, bunker back door ..)
     are dropped by the pre-pass (`campaign_drop('M11_B')`), and the mesh runs through the standing bunker
     wall in a slot 79 cm wide (polygons 132 / 169 / 87 / 88 / 89, z 30,385..30,464, `nav1.py`). The bots' holds
     of 4.2 (stations 3, 5, 8, 9) are therefore not optional, each needs its trigger.

### The round as a design, attacked

| question | answer | how |
|---|---|---|
| Is the START on ground and not inside geometry? | YES. 33 of 33 places of the row x 33,900..34,000, z 29,900..30,900 are free cells; collision floor y 800 (`Collapsed_Centre_001`), the mesh floats 30 above (830), the dome is 60 m overhead | MEASURED `row.py`, `column.py M11_B 33981 30387` |
| Is every loot place reachable? | Only after TWO removals: the bunker wall (with `M11B_OYCHECK_BEFORE01`) and the invisible door block (corrected 1). Then yes: a free standing cell lies 64..173 cm from each of the 11 cases, 5 paintings and the table | MEASURED `walk3.py`, `row.py` |
| Is the escape one connected walkable way from the start? | On the mesh yes (one part). On the mesh AND the collision only after FOUR campaign removals: wing door block, bunker swap, corner swap, stair barricade. With all four: START -> table and table -> van stop are free; take any one away and the leg it guards is blocked by exactly that piece | MEASURED `walk3.py` (five scenarios) |
| Does a scripted door, lift or cut scene stand in the way? | No door, lift or gate class exists on the map side (0 nodes). The four gates above are static pieces switched by `DeactivateGeom` / `ActivateGeom` in subtrees the pre-pass DROPS: each needs a `CAMPAIGN_KEEP` entry. Stock precedent that a static placement stops acting when its entity is switched off: F07's `BlockVisionPlane`, and Retomoto's window live (READ re/retomoto_fa.md lines 95..98 and 630..633) | MEASURED `facts.py doors`, `geomsw.py`; READ |
| Do the swaps leave the right picture? | Not established: `SI0100_M11_BarricadeB_Broken01` and `M11B_OYCHECK_AFTER01` are NOT hidden at load (flags 0x2201f2 / 0x2201ea, ZGEOM[3] = 0) although the level hides every other 'after' piece by flag (corner, barrel remains, door rubble, planks, emitters). Their only referrer is the `ActivateGeom` itself. Either Dead Men's `ActivateGeom` hides its targets when it starts, or wall and rubble stand in one another before the blast. In the build they will (the controller is dropped). For walking it makes no difference: the rubble does not close the slot | MEASURED `objs.py`, `refs.py`, `walk2.py` |
| Does the escape vehicle exist, and does it move without Dead Men's .ANM? | Yes: F07's `Animation/F07/F07_Escape_Vehicle_0n.zip` and its keys are the HOST's (log: '.ANM joined: 21.6 MB (S 21.6 MB ...); clips +0'). No vehicle of the level is used. What is missing is a line for it (corrected 3) | MEASURED build log; READ re/retomoto_fa.md line 78 |
| Do the enemy numbers fit? | 27 kept actors against 63 on Retomoto, 19,188 entities against 25,490 that ran: far inside | MEASURED `facts.py squads`, result.json; READ the report's scale rows |
| Is it different from the Fragile Alliance map of the place? | There is none (Dead Men's PC maps are M01 / M02 / M03 / M06; 'Havana' is a text placeholder) | MEASURED `facts.py leftovers`; READ the task's scouting |
| Level bounds | The campaign's two are `ZBoxPrimitive` + `LevelBound` with two warning boxes each, the same form F07's six have; kept by the pre-pass. None lies on the route (assuming unrotated boxes: ASSUMED) | MEASURED `facts.py bounds`, `campaign_drop('M11_B')` |

### Confirmed (re-derived by me; same result)

1. One world space, the join: M11_A `EndOfLevelTrigger` at (19528, 212, 20777), `SceneChanger` to
   'Locations\M11_B\M11B_Main.zip'; M11_B's players at (20316, 21, 21057) and (20251, 20, 20962); the largest
   mesh parts overlap at x 18,435..20,064, z 20,460..22,664. `facts.py join`, `links.py M11_B M11_A`.
2. F07 + M11_B = 74,454 chunk-table entries (726 over), 12 problems, entities 19,188, rooms 16, textures 1,835,
   materials 1,178, .prm 69.0, .TEX 433.3, .ANM 21.6, .fxc 17.8 MB, bank 4,742 / 4,599, mesh 290,516 bytes,
   archive 362.0 MB, .WAV 21,668,176 bytes; log '39332 of 47143 chunks of M11_B appended to 35101'.
   Re-built: `kl_maps.py one <work>/build/cfa/havana/skeptic F07 M11_B --campaign --keep` (38 s).
3. F07 + M11_A = 72,573 (1,155 free), 12 problems, 16,388 entities, 37,446 chunks appended. Re-built.
4. F08 + M11_B = 66,368, 11 problems (no chunk problem); F05 + M11_B = 56,953, 11 problems, .prm 90.0 MB.
   Re-built both. Host tables 35,102 / 27,016 / 17,601 (the first agent's `hosts.py`, a ten-line header read).
5. Both chapters: 111,853 entries, 83,464 reachable, 25,927 entities, 1,969 textures, 1,323 materials, mesh
   783,916 bytes, 403.0 MB. Re-built: `kl_maps.py chain <skeptic>/chain F07 M11_B M11_A`.
6. Lighten: .TEX 433.3 -> 242.9 MB, .fxc 16.94 -> 8.63 MB, archive 362.0 -> 223.2 MB. Re-run on my kept build.
7. Compaction: 74,454 -> 46,081 entries, .prm 69.0 -> 67.2 MB, 'problems: 0'; `kl_impact.py <compact>`:
   'problems: 0 in 1 levels'. Re-run. Never loaded in the game: READ re/prm_limit.md 'Compaction', and no
   note written since says otherwise (`grep -i compact re/*.md CLAUDE.md`).
8. Preflight on the kept build: every class / controller no Dog Days level uses is 'in the build: 0'; only
   `MatPosAnimProxy` x2 and `BarrelEffects` x2 are in. Re-run (`skeptic/preflight.txt`).
9. The mesh: 1,015 polygons, 163 areas, 326 waypoints, 13 links of kinds 1 x6, 2 x6, 6 x1; kl_pf4 converts it
   (6 kept, 7 dropped), check passes, 290,516 bytes. ONE part of 606 polygons / 9,821 m2,
   x 18,435..43,224, z 20,460..33,297 - found twice, by the neighbour field and by shared edge geometry (the
   two agree on 1,015 of 1,015 polygons), without walking any link. M11_A: 1,696 polygons, largest part 1,585
   / 18,524 m2, 4 links of kind 3 all dropped. `nav1.py M11_B`, `links.py`.
10. Every station of 4.2 lies on that part (START, CP_05, bunker, terrace, gallery, stair top / middle / foot,
    rally, exit box, van stop, the four police places); the walk adds up to about 470 m by my coarser measure
    (the report: 460). `nav1.py`.
11. The side stair is the only mesh way between floor and square: the part's polygons at heights 120..700 are
    61 of the stair and 7 of a ramp at the south-west corner that ends at y 508; ban the 61 alone and
    terrace -> rally has no way; no polygon at y > 700 touches one at y < 120. `nav1.py`, `stair_only.py`.
12. State at load: `SO0201_M11_BarricadeXX_01` shown (flags 0x2201f2), its collision x 26,875..27,540,
    y 160..443, z 28,481..28,580 across the mesh's 2.4 m gap (polygons 573 / 574); `SO0201_M11_Corner_01`
    shown, `..._CornerBroken_01` hidden (0x2205f2, ZGEOM[3] = 1); both bunker barricades flagged visible.
    The deactivators and their targets as named. `objs.py --vals`, `geomsw.py`, `poly.py M11_B 573 574`.
13. The bunker blast's objects: `BoomBoxDust` (`Explode` + `AIDWrapper`) at (38613, 902, 30398);
    `GeomActivatorDustExplosion` -> 18 `Capitolio_Explosion` emitters and a light, all hidden at load;
    `Timer_SandbagsDeactive` -> the swap; `GeomDeactivatorExplosiveStuff` -> two barrels and
    `Collapsed_Crates_003`. `objs.py`, `geomsw.py`.
14. Loot props: 11 cases (A x4, B x5, C x1, Low x1) at the places given, 5 paintings, the table;
    `Template_Samurai_Montre` with the same three children in M11_B and in M09_A. `montre.py`, `facts.py cases`.
15. Squads: Enemy 60, Ally 31 actors under `ZSquadScript`; the named stay-squads hold 24 (terrace, stair,
    square) + 3 (wing) = 27 actors with the weapons given; every stock F01..F09 has exactly 7 `Ally` actors.
    `facts.py squads`, `facts.py factions`. (The squad_plan rule itself I did not re-implement.)
16. No leftover of a 'Havana' map: 0 controllers and 0 classes with Online / PIP / Spawn / Money in the name
    in either level, 0 map-side node names with FA / Online / DL0n / Multiplayer. `facts.py leftovers`.
17. Music: three PCM stereo layers of 162.6 s at 32 kHz, `Music/InHouse/M11AB/M11_Havana_Layer_A/B/C.wav`,
    set `LevelSetup/Level/M11_A/Music/M11_Havana_Layer` (0x1dc4f3c bytes = 31.2 MB); in neither merged file.
    `kl_str.py list` on the three stream files.
18. No vehicle of the level can carry a crew: `ZHavokCar` x3 (two BTRs, the T-72) and one `ZHeli`, all in
    dropped squads with `VehicleWeapon` / road routs. `objs.py`, the survey's class rows via preflight.
19. klmem's reserve default 128 MB: READ klhook/klmem.c line 263.

### Could not be verified (by me, offline)

- The per-room chunk sums of 3.2 (`rooms_chunks.py`, `scenarios.py`): way (d) 63,310 and the cut two-chapter
  figures 87,834 / 79,748 / 70,333. Sums over closures that share chunks; nothing was built; no tool cuts
  rooms. Not re-derived.
- 'With a wardrobe the .prm would be about 85 MB' and 'about 61,600 entries after compaction': ASSUMED from
  Retomoto in the report, not built by either of us.
- That Dog Days' `DeactivateGeom` removes the collision of THESE four static pieces. The precedent is good
  (Retomoto's window, F07's vision plane) but each of the four is on the only way: a first direct boot has to
  show all four go. LIVE.
- Whether Dead Men's `ActivateGeom` hides its targets at start (the bunker's 'after' pieces): not read in
  either exe. LIVE or a reading job.
- That the `ColiObj_` pieces are not drawn: by name only; not rendered. That they stop the player's character
  is MEASURED only as far as the flag census goes (0x108 = the 'hero' blockers of both games); which bits
  stop an AI heister was not read in kl2.exe. The walk test counts every static shape alike.
- Level-bound boxes: I read centre and half extents, not their rotation.
- Voice line counts, the .LOC and texture leftovers (`UI_FA_Respawn_pip_mask`, `FA_Menu` waves), the
  campaign flow of M11_A (1.4) and candidate B's 387 m: not re-derived; none of them carries the verdict.
- Everything the report itself lists as live-only (light under a Dog Days host, the `Explode` + emitter chain
  in Dog Days, the three-layer music set after a merge, loyalists as `Ally`, the far-detail shader).

### Verdict after the checks: feasible-with-work

The level, the numbers and the tools are as the report says, and 'El Capitolio' is the right chapter. The
plan has to change in four places before it is authored: (1) the chunk table first, as the report says -
compaction, or a smaller host (F08 66,368, F09 69,805, F05 56,953), each unproven in the game; (2) FOUR
campaign geometry events kept and fired, not two - wing door block and bunker swap for the loot, corner swap
and stair barricade for the way out - and all four seen to work in a first direct boot before any table is
written; (3) an opening blast borrowed from F07 (the corner has none of its own); (4) the van: a stop at
about (27000, 0, 22600) works, a 61 m clear straight run is there, an arrival and a leave leg out of sight are
not - that needs craters avoided and pieces hidden, or a decision that the van is simply there. Effort about
1.0 of Retomoto (0.8..1.2): the join it saves is paid back by the gates, the blast and the van.

