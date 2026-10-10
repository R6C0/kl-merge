# AI heisters on the Dead Men maps: what was built, the routes, the owner's four behaviours

2026-10-10, agent b-build. Tool: `tools/kl_fa_bots.py` (its docstring is the spec of the data). Built on
`re/bots_squad.md`, `re/bots_behaviour.md`, `re/bots_voice.md`. **OFFLINE: the game was not started, nothing was
installed, nothing was written into the Dog Days folder.** Every statement about what a bot DOES is read in kl2.exe
by those notes or is an ASSUMPTION marked as such; no bot of these builds has been seen in the game.

Owner, 2026-10-10: *'continue the ai heisters ... make sure the voicelines for the characters are there too and the ai
have better interactions because in the current game they arent the best, want them to be able to backstab you and
also pay the driver and leave without you or blow the van up or help you up'*.

**2026-10-10 evening: section 12 supersedes parts of sections 0, 3, 6.2 and 11** (the owner played the four maps
with the bots: the cases on Late Night Opening, the warehouse people on the diner, the bank's wall, the park). The
builds to load are `<work>\build\y_loot2\M01 M02 M03 M06`; sections 0 - 11 describe `b_bots` / `u_maps`.

## 0. Short answers

1. **Four builds with a squad of seven AI heisters each, all checks passed**: `<work>\build\b_bots\M01`, `M02`,
   `M06`, `M03` (made from `<work>\build\z_maps\<map>`, which are untouched). `kl_fa_bots.py check` PASS,
   `kl_fa_bots.py diff` 'only the squad was added', `kl_maps.py preflight` 0 CRASH, `kl_maps.py audit` PASS on all four.
   `kl_fa.check` no longer says 'no bot squads' (7 on each).
2. **Nothing was added to the four large blocks**: `.prm`, `.ANM`, `.fxc`, `.WAV` have the same size before and after
   on every build (table in 3). No model (a bot wears the model of `Heroes!Hero_0N`), no animation, no sound, no
   shader. The `.prm` changes in content only: 983 .. 2,487 four-byte record offsets (section 2.3).
3. **The heisters' lines are reachable for every bot**: group names `Glazer_Bodyguard_02..08` kept, so the seven
   speak with voices C2..C8; `kl_voice.py heisters` on each build: AI heisters by character index 1..7, one each,
   0 findings. Lines exist for backstab, driver bribe, left behind and van destroyed (`re/bots_voice.md` 0); they play
   when the rules fire the event. **Barks** (shouts in a fight) are NOT added: stock Arcade bots have none either,
   and giving them some grows the sound bank past anything that ran live (section 5.5).
4. **The owner's four behaviours** (section 5):

   | wish | what these builds do | what is still needed |
   |---|---|---|
   | backstab | the stock rule can now run: every route passes the map's stage triggers (stage 3 on M01 M02 M06; **M03 only reaches stage 2**) | the stock table allows 0 traitors on Arcade levels 1-3: hook part H1 (data writes) or H2 (one bit) |
   | bot turns on you when you shoot it | stock, works as soon as bots exist (`re/bots_behaviour.md` 1.4) | nothing; H1 can tune the limit |
   | pay the driver and leave without you | nothing by data: the exe has no AI caller of the bribe | hook part H3 (one game call) or H4 (data write) |
   | the vehicle leaves without you | stock: it waits its time and goes; bots board by themselves | - |
   | blow the van up | nothing by data: no Ally soldier targets the vehicle, and a Dead Men spline car / helicopter has no damage path at all | hook part H5 (one game call), NOT established for a spline car |
   | help you up | option `--heal` (one ZSoldier field): builds each bot's `ZHealTactic`. **ASSUMPTION that it does anything useful**; off in the delivered builds | one live run of a `--heal` build (check B8); else hook research |

5. **M03 (the bank): the bots stay on their side of the yard wall.** The navigation mesh does not cross it; the two
   parts were NOT joined (what that needs: 6.2). The bots end in the yard corner nearest the van, inside an
   `AllyEscapeBox`, and board from there when the van is there - they vanish in the yard, they do not walk to the van.
6. **Retomoto: analysis only, nothing built** (6.3). A route from the balcony to the floor in front of the tower car
   exists on the tower's mesh part; the street half is out of reach for a bot.

## 1. Commands

    python tools\kl_fa_bots.py build <work>\build\z_maps\M01 <work>\build\b_bots\M01      plan + write + check (15 s)
    python tools\kl_fa_bots.py check <folder>            every check of section 4; exit 1 on a FAIL
    python tools\kl_fa_bots.py diff  <source> <folder>   what the step changed, by file; exit 1 if more than the squad
    python tools\kl_fa_bots.py plan  <source> [options]  the stations and places without writing anything
    python tools\kl_fa_bots.py stock                     the control: the nine stock squads through the same reading
    python tools\kl_fa_bots.py sizes <folder> ...        .prm .ANM .fxc .WAV
    python tools\kl_maps.py preflight <folder>  /  audit <folder>     as for every map build

Options (each off / automatic by default; none is used by a delivered build except where the table says so):
`--ally-box auto|on|off`, `--wait-guards`, `--loot-seconds N`, `--start-delay N`, `--heal`, `--no-tree`,
`--no-stage`, `--park x,y,z`. The docstring says what each does and which stock level shows the form.

Install one (THE LEAD'S STEP; the game closed):

    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\b_bots\M01" F01
    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\b_bots\M02" F01
    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\b_bots\M06" F01
    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\b_bots\M03" F01

Each folder holds the archive, the 18 files beside it and `KLWardrobe.ini` (all byte for byte the source's), plus
`bots.txt` / `bots.json` (plan, places of all seven bots, the check), `steps.json` (with a `bots` entry),
`preflight.*`, `audit.*`.

## 2. What is placed

### 2.1 The squad (per map: 148 .. 211 entities; `re/bots_squad.md` 8 is the recipe)

Every node is a CLONE of a stock node (F07's squad, read from the stock archive; the `AllyEscapeBox` from F02), with
only the fields below rewritten:

| node | class + controller | rewritten |
|---|---|---|
| `Gameplay!merc_bot_squad!Timer_start_bots` | ZBoxPrimitive + TriggerDelay2 | field 4 = the first step of the seven squads. Named by `Gameplay!AIMonitor` list 2 (appended; the one edit of an existing node) |
| `Gameplay!merc_bot_squad!Squad#0N`, N = 2..8 | ZGROUP + ZSquadScript (eStayBack, eHeistOnly ...) | place (origin) |
| `...\Glazer_Bodyguard_0N` | ZGROUP (pool group 2, flags and aux as F07) | place on the mesh, facing as the START points face |
| `...\Glazer_Bodyguard_0N\Ground` | ZFFActor + ZSoldier, F07's own Squad#0N actor: team Ally, `Rifle_zastavam85` of the systems part, `Kane_NPC` / `Lynch_NPC`, `FACharacters/C<N>` | model (`.prp` ZGEOM[4] and `.gms` record) = the build's `Heroes!Hero_0N\Ground` (9341 .. 9982 on these builds); ZLNKOBJ[1], ZLNKWHANDS[5] = that hero's |
| `...\01x_DefendBehaviour_to_loot`, `03x_DefendBehaviour_out` + `Pos#01..03` | ZGROUP + DefendBehaviourRout; plain ZBoxPrimitive 10 x 10 x 10 | field 1 = its boxes, 7 = the next node, 4 = `eDMS_Sprint` on the way out (stock: 92 of 1,100 steps sprint; ASSUMPTION that it suits); the boxes' places |
| `...\020_Timer_done_looting` | ZBoxPrimitive + TriggerLootDepleted | 0 = the map's loot objects of the richest area (2 / 21 / 1 / 11), 1 = 20 s, 4 = next |
| `...\040_SquadModifier_tight_defense_van` | ZGROUP + SquadModifierBehaviour | 0 = `eLM_Leash`, 9 = `eDM_Tight`, 26 = [] (the last step of F01 F03 F04 F07) |
| `Gameplay!merc_bot_squad!AllyEscapeBox` (M06, M03) | ZBoxPrimitive + AllyEscapeBox, F02's `BoardingTrigger_Heli02_incoming_A` without its PlayerAction | place, size 350 x 416 x 350, NOT hidden (F02's is created hidden and switched on when its helicopter comes; ASSUMPTION that a box that is never hidden ticks from the start - kl2 0x907a50 has no flag of its own and boards only in vehicle state 3 / 4) |

All groups made here stand at the origin, unturned, so a box's `.prp` place IS its world place; `.gms` record and
`.prp` carry the same place, rotation and model (F07's own squad has its 10,000 offset in the group's record and
in the step's property - same sum; the loader reads neither from the record, `tools/kl_scene.py`).

References out of the squad (measured by `check`, per build): `ZFFActor[1]` x 7 into the systems part (the rifle);
`TriggerLootDepleted[0]` into the map's loot (14 / 147 / 7 / 77 = objects x 7 squads). Nothing else; nothing of F07's map.

### 2.2 How a route is planned

- The level's mesh (`kl_pf4` arrays 3, 9, 6) is read as polygons with the neighbour across each edge. Control
  (`kl_fa_bots.py stock` and every `plan`): with edge k running from vertex k to k + 1 the named neighbour shares
  both ends of the edge in **100 % of the edges of all nine stock levels (744 .. 2,478 each) and of the four maps
  (906, 2,060, 2,220, 1,506)**.
- Stations in order: START row -> ENTERS_BANK box (stage 1) -> the loot -> EXITS_BANK box (stage 2) -> level exit box
  (stage 3) -> the boarding place; a station every 18 m of path between them (GUESS: `SPACING`). The path is the
  shortest over the polygons through the middles of shared edges (Dijkstra). Where a map has several boxes of a kind
  the one on the shortest way is taken (M01: `LeavingHeist_01` of three, `CallExitVehicle_02` of two). **The order
  of loot and way out is the shorter of the two** - on M01 the richest loot (the Senator and his flank, behind the
  diner) lies BEYOND the EXITS_BANK doors: 193 m against 216 m.
- A place is put only on a polygon of the START row's connected part, at the polygon's height, inside the box when
  the station is a trigger (within 0.45 of its three size values: inside whether they are half or full extents),
  `CLEAR` = 60 from the nearest edge without a neighbour where the mesh allows it. **Measured: the mesh is already
  drawn in from the walls** - M01's diner doors are strips 43 .. 50 wide - so a doorway gives 13 .. 20 and all seven
  bots share its one place; such a place never ends a step (they would hold in the doorway).
- Each bot has its own place per station, 110 apart (90 inside the AllyEscapeBox), as stock; the seven stand
  110 .. 268 from the nearest START point, 144 apart, on the mesh, START points 75 .. 101 above their feet (M06, a
  sloped garden: -34 .. 152).
- The loot: `OnlineMoneyCtrl` objects that are not of a DROP type and within 4 m of the START row's mesh part,
  grouped when nearer than 9 m; the richest group (field 1 added up) is the bots' loot place. **Measured, and not
  what `re/bots_squad.md` 7 counts**: of the 306 / 363 / 340 / 307 money objects only 6 / 44 / 24 / 4 are loot; the
  rest are the pool of stacks a player drops. On M01 and M06 the loot is ON PEOPLE (the Senator 400,000 and his
  flank; the boss): the bots' 'loot place' is where those stand at the start.

What `stock` says about 'as stock' (the nine levels' own squads through the same reading): a stock route box is on
the START row's mesh part in 71 .. 100 % of cases (F01: 49 of 168 are off the mesh, F07 42 of 329), at the mesh's
height (middle 0 in F07, -17 in F01), clearance least 4 .. 24, middle 58 .. 157; the bots' feet are at the mesh's
height in F01 F03 F07; and **every one of the nine has route boxes inside its level exit box (7 .. 112)** - the
control of this module's box reading (frames, half extents). So these routes are stricter than stock, not looser.

### 2.3 What is written, and the proof that nothing else changed

`.prp` (the subtrees appended, AIMonitor list 2), `.gms` + `.buf` (entities, cluster table, type table, names),
`.oct` / `.rmi` / `.rmc`, `.prm`:

- **Slot ids.** Appending top-level groups grows the root's first pool, so every later entity's slot moves:
  14,827 .. 21,712 ids. The room trees of the `.oct` and the boxes of `.rmi` / `.rmc` are renumbered
  (`kl_octree.remap_ids`); `diff` proves by ENTITY that every item and box names what it named.
- **The root's group tree.** Stock F07 lists its squad groups and its step groups (those with boxes) in the scene
  root's tree 3 with the box of their places +- 10 (measured; the actor groups, the boxes and the SquadModifier
  steps are not listed). The new groups are listed the same way (42 or 56 items). ASSUMPTION that it matters; what
  the engine asks that tree for is not established. `--no-tree` leaves it out.
- **`.prm`.** That tree grows, the collision records behind the room trees move, and the model roots name their
  record by file offset: 983 .. 2,487 roots get their new offset in place (4 bytes each at +0x1c; `kl_graft.build`
  does the same for S's records). Size, chunk table and every other byte equal (`diff`). With `--no-tree` the `.prm`
  is byte for byte the source's.
- `python tools\kl_fa_bots.py diff <source> <folder>` on the four: all old entities equal (record, parent, light
  lists), all old top-level subtrees equal but `Gameplay!AIMonitor`, scene property block equal, `.buf` head /
  surface table / navigation mesh / dynamic list / heap budget equal, the other 20 members and the 19 files beside
  the archive byte for byte. RESULT: 'only the squad was added', four of four.

## 3. The four builds

Sizes of the four blocks a level reads in one piece (bytes; before = `z_maps\<map>`, after = `b_bots\<map>`):

| build | .prm | .ANM | .fxc | .WAV | squad entities | chunk-table entries |
|---|---:|---:|---:|---:|---:|---:|
| M01 | 55,088,000 -> 55,088,000 | 22,061,764 -> same | 17,760,648 -> same | 21,722,704 -> same | 148 | 50,042 (unchanged) |
| M02 | 54,619,216 -> 54,619,216 | 22,202,472 -> same | 17,760,648 -> same | 22,527,568 -> same | 211 | 58,371 |
| M06 | 49,585,744 -> 49,585,744 | 21,642,576 -> same | 17,760,648 -> same | 21,775,744 -> same | 163 | 46,902 |
| M03 | 60,469,040 -> 60,469,040 | 22,202,616 -> same | 17,760,648 -> same | 22,716,752 -> same | 163 | 62,680 |

Routes as coordinates (x, y up, z; 100 = 1 m). The table gives Squad#02's places; the other six are in each
folder's `bots.json` (`plan.bots.<N>.places`), 110 apart from these.

### M01 (M01_FA_A)

- mesh: 393 polygons in 6 parts, the START row on a part of 371; path length of the anchors 19348 (193 m)
- added: 148 entities (ZGROUP 56, ZFFActor 7, ZBoxPrimitive 85); controllers ZSquadScript 7, ZSoldier 7, DefendBehaviourRout 35, SquadModifierBehaviour 7, TriggerLootDepleted 7, TriggerDelay2 1; REF ids 25880..26027
- bots stand 110..268 from the nearest START point, at least 144 apart; START points 75..78 above their feet
- bots at: #2 (1632, 0, 30643), #3 (1552, 0, 30523), #4 (1712, 0, 30523), #5 (1712, 0, 30763), #6 (1792, 0, 30643), #7 (1432, 0, 30763), #8 (1632, 0, 30403)
- loot wait: 2 objects named, 20 s; AllyEscapeBox: none; vehicle ZHavokCar (OnlineEscHavokCar); boarding action Triggers!BoardingTrigger_Car at (5884, 181, 20448)
- references out of the squad: `{'ZFFActor[1] -> AllLevels': 7, 'ZTriggerLootDepleted[0] -> AI_Enemies': 14}`

| # | step | station | Squad#02's place | distinct places of 7 |
|---|---|---|---|---:|
| 1 | `010_DefendBehaviour_to_loot` | on the way to enter | (810, 0, 28971) | 7 |
| 2 | `010_DefendBehaviour_to_loot` | on the way to enter | (1317, 0, 27432) | 7 |
| 3 | `010_DefendBehaviour_to_loot` | on the way to enter | (2725, 0, 26394) | 7 |
| 4 | `011_DefendBehaviour_to_loot` | on the way to enter | (3583, 0, 25130) | 7 |
| 5 | `011_DefendBehaviour_to_loot` | on the way to enter | (4771, 0, 23910) | 7 |
| 6 | `012_DefendBehaviour_to_loot` | ENTERS_BANK Triggers!EnterHeist_01 (stage 1) | (6101, 0, 23060) | 1 |
| 7 | `012_DefendBehaviour_to_loot` | on the way to exit | (5076, 0, 22188) | 7 |
| 8 | `013_DefendBehaviour_to_loot` | EXITS_BANK Triggers!LeavingHeist_01 (stage 2) | (4096, 0, 21883) | 1 |
| 9 | `013_DefendBehaviour_to_loot` | the loot (2 objects) | (3384, 0, 19894) | 7 |
| 10 | `030_DefendBehaviour_out` | level exit Triggers!CallExitVehicle_02 (stage 3; it calls the vehicle as a player enters it - ASSUMPTION) | (4734, 0, 20701) | 7 |
| 11 | `030_DefendBehaviour_out` | the boarding place (150..400 from the boarding action) | (5724, 0, 20448) | 7 |

- check: Squad#02 192 m, least clearance 20, Squad#03 191 m, least clearance 20, Squad#04 197 m, least clearance 20, Squad#05 193 m, least clearance 20, Squad#06 194 m, least clearance 20, Squad#07 190 m, least clearance 20, Squad#08 194 m, least clearance 20

### M02 (M02_FA_A)

- mesh: 908 polygons in 18 parts, the START row on a part of 859; path length of the anchors 30577 (306 m)
- added: 211 entities (ZGROUP 70, ZFFActor 7, ZBoxPrimitive 134); controllers ZSquadScript 7, ZSoldier 7, DefendBehaviourRout 49, SquadModifierBehaviour 7, TriggerLootDepleted 7, TriggerDelay2 1; REF ids 32815..33025
- bots stand 124..251 from the nearest START point, at least 144 apart; START points 90..92 above their feet
- bots at: #2 (1490, 1000, -3342), #3 (1570, 1000, -3462), #4 (1570, 1000, -3222), #5 (1410, 1000, -3462), #6 (1410, 1000, -3222), #7 (1650, 1000, -3342), #8 (1330, 1000, -3342)
- loot wait: 21 objects named, 20 s; AllyEscapeBox: none; vehicle ZHavokCar (OnlineEscHavokCar); boarding action Triggers!BoardingTrigger_Car at (-426, 136, -8627)
- references out of the squad: `{'ZFFActor[1] -> AllLevels': 7, 'ZTriggerLootDepleted[0] -> Locations': 140, 'ZTriggerLootDepleted[0] -> Civilians': 7}`

| # | step | station | Squad#02's place | distinct places of 7 |
|---|---|---|---|---:|
| 1 | `010_DefendBehaviour_to_loot` | on the way to enter | (1818, 1000, -1730) | 7 |
| 2 | `010_DefendBehaviour_to_loot` | on the way to enter | (2565, 1000, -213) | 7 |
| 3 | `010_DefendBehaviour_to_loot` | on the way to enter | (1451, 1000, 1136) | 7 |
| 4 | `011_DefendBehaviour_to_loot` | on the way to enter | (2380, 500, -166) | 7 |
| 5 | `011_DefendBehaviour_to_loot` | on the way to enter | (1358, 500, 1071) | 7 |
| 6 | `011_DefendBehaviour_to_loot` | on the way to enter | (549, 500, 2459) | 7 |
| 7 | `012_DefendBehaviour_to_loot` | ENTERS_BANK Triggers!EnterBankTrigger_01 (stage 1) | (1488, 500, 1879) | 7 |
| 8 | `012_DefendBehaviour_to_loot` | the loot (21 objects) | (1881, 500, 2254) | 7 |
| 9 | `030_DefendBehaviour_out` | on the way to exit | (617, 500, 2466) | 7 |
| 10 | `030_DefendBehaviour_out` | on the way to exit | (448, 500, 1229) | 7 |
| 11 | `030_DefendBehaviour_out` | on the way to exit | (1677, 15, 53) | 7 |
| 12 | `031_DefendBehaviour_out` | on the way to exit | (1125, 0, -1175) | 7 |
| 13 | `031_DefendBehaviour_out` | on the way to exit | (-20, 0, -2480) | 7 |
| 14 | `031_DefendBehaviour_out` | EXITS_BANK Triggers!ExitBankTrigger_01 (stage 2) | (-351, 0, -3717) | 7 |
| 15 | `032_DefendBehaviour_out` | on the way to level | (-240, 0, -5254) | 7 |
| 16 | `032_DefendBehaviour_out` | on the way to level | (413, 0, -6820) | 7 |
| 17 | `032_DefendBehaviour_out` | level exit Triggers!ExitTrigger_01 (stage 3; it calls the vehicle as a player enters it - ASSUMPTION) | (-503, 0, -8517) | 7 |
| 18 | `033_DefendBehaviour_out` | the boarding place (150..400 from the boarding action) | (-586, 0, -8627) | 7 |

- check: Squad#02 384 m, least clearance 73, Squad#03 388 m, least clearance 73, Squad#04 395 m, least clearance 71, Squad#05 318 m, least clearance 60, Squad#06 348 m, least clearance 37, Squad#07 333 m, least clearance 42, Squad#08 314 m, least clearance 51

### M06 (M06_FA_A)

- mesh: 954 polygons in 7 parts, the START row on a part of 936; path length of the anchors 20568 (206 m)
- added: 163 entities (ZGROUP 56, ZFFActor 7, ZBoxPrimitive 100); controllers ZSquadScript 7, ZSoldier 7, DefendBehaviourRout 35, SquadModifierBehaviour 7, TriggerLootDepleted 7, TriggerDelay2 1, AllyEscapeBox 1; REF ids 26480..26642
- bots stand 112..212 from the nearest START point, at least 144 apart; START points -34..152 above their feet
- bots at: #2 (5514, 342, 4550), #3 (5434, 323, 4430), #4 (5474, 374, 4710), #5 (5714, 311, 4510), #6 (5714, 339, 4670), #7 (5634, 285, 4310), #8 (5274, 279, 4430)
- loot wait: 1 objects named, 20 s; AllyEscapeBox: (-1687, 420, -6542); vehicle ZHeli (OnlineEscHavokCar); boarding action Triggers!BoardingTrigger_Heli at (-1687, 133, -6542)
- references out of the squad: `{'ZFFActor[1] -> AllLevels': 7, 'ZTriggerLootDepleted[0] -> AI_Enemies': 7}`

| # | step | station | Squad#02's place | distinct places of 7 |
|---|---|---|---|---:|
| 1 | `010_DefendBehaviour_to_loot` | on the way to enter | (4375, 316, 5568) | 7 |
| 2 | `010_DefendBehaviour_to_loot` | on the way to enter | (2970, 224, 6593) | 7 |
| 3 | `010_DefendBehaviour_to_loot` | on the way to enter | (1392, 217, 6590) | 7 |
| 4 | `011_DefendBehaviour_to_loot` | ENTERS_BANK Triggers!Enter_BridgeHouse_01 (stage 1) | (796, 303, 5808) | 7 |
| 5 | `011_DefendBehaviour_to_loot` | on the way to loot | (800, 564, 4028) | 7 |
| 6 | `011_DefendBehaviour_to_loot` | on the way to loot | (800, 635, 2230) | 7 |
| 7 | `012_DefendBehaviour_to_loot` | on the way to loot | (802, 540, 434) | 7 |
| 8 | `012_DefendBehaviour_to_loot` | on the way to loot | (800, 258, -1343) | 7 |
| 9 | `012_DefendBehaviour_to_loot` | the loot (1 objects) | (210, 220, -2276) | 7 |
| 10 | `030_DefendBehaviour_out` | on the way to level | (-548, 220, -3783) | 7 |
| 11 | `030_DefendBehaviour_out` | on the way to level | (-953, 220, -5192) | 7 |
| 12 | `030_DefendBehaviour_out` | level exit Triggers!Call_ExitChpooer_Trigger (stage 3; it calls the vehicle as a player enters it - ASSUMPTION) | (-1656, 220, -6634) | 7 |
| 13 | `031_DefendBehaviour_out` | the boarding place (inside the AllyEscapeBox) | (-1709, 220, -6564) | 7 |

- NOTE: EXITS_BANK Triggers!Call_ExitHeist_Trigger at (-341, 383, -1098): no place inside it on the START row's mesh part
- NOTE: no EXITS_BANK trigger on the route (stage 2 is skipped; stage 3 does not need it: 0x5dd890 only raises)
- check: Squad#02 206 m, least clearance 66, Squad#03 216 m, least clearance 73, Squad#04 211 m, least clearance 65, Squad#05 216 m, least clearance 67, Squad#06 207 m, least clearance 73, Squad#07 216 m, least clearance 40, Squad#08 225 m, least clearance 34

### M03 (M03_FA_A)

- mesh: 697 polygons in 9 parts, the START row on a part of 490; path length of the anchors 23716 (237 m)
- added: 163 entities (ZGROUP 56, ZFFActor 7, ZBoxPrimitive 100); controllers ZSquadScript 7, ZSoldier 7, DefendBehaviourRout 35, SquadModifierBehaviour 7, TriggerLootDepleted 7, TriggerDelay2 1, AllyEscapeBox 1; REF ids 30708..30870
- bots stand 126..184 from the nearest START point, at least 144 apart; START points 89..101 above their feet
- bots at: #2 (-1808, 700, -11838), #3 (-1928, 700, -11918), #4 (-1928, 700, -11758), #5 (-1728, 700, -11958), #6 (-1688, 700, -11758), #7 (-1608, 700, -11878), #8 (-1728, 700, -11598)
- loot wait: 11 objects named, 20 s; AllyEscapeBox: (1967, 420, -1073); vehicle ZHavokCar (OnlineEscHavokCar); boarding action Triggers!BoardingTrigger_Car at (3252, 133, -20)
- references out of the squad: `{'ZFFActor[1] -> AllLevels': 7, 'ZTriggerLootDepleted[0] -> Locations': 70, 'ZTriggerLootDepleted[0] -> Civilians': 7}`

| # | step | station | Squad#02's place | distinct places of 7 |
|---|---|---|---|---:|
| 1 | `010_DefendBehaviour_to_loot` | on the way to enter | (-406, 700, -10896) | 7 |
| 2 | `010_DefendBehaviour_to_loot` | ENTERS_BANK Triggers!EnterBankTrigger_01 (stage 1) | (291, 800, -9452) | 6 |
| 3 | `010_DefendBehaviour_to_loot` | on the way to loot | (-138, 800, -7808) | 7 |
| 4 | `011_DefendBehaviour_to_loot` | on the way to loot | (-664, 800, -6319) | 7 |
| 5 | `011_DefendBehaviour_to_loot` | on the way to loot | (-420, 401, -5927) | 6 |
| 6 | `011_DefendBehaviour_to_loot` | on the way to loot | (-734, 240, -7000) | 7 |
| 7 | `012_DefendBehaviour_to_loot` | the loot (11 objects) | (424, 225, -6154) | 7 |
| 8 | `030_DefendBehaviour_out` | on the way to exit | (-345, 240, -4930) | 7 |
| 9 | `030_DefendBehaviour_out` | EXITS_BANK Triggers!ExitBankTrigger_02 (stage 2) | (-1231, 231, -4751) | 1 |
| 10 | `030_DefendBehaviour_out` | on the way to park | (-1476, 220, -3091) | 7 |
| 11 | `031_DefendBehaviour_out` | on the way to park | (-1237, 220, -1504) | 7 |
| 12 | `031_DefendBehaviour_out` | on the way to park | (242, 220, -975) | 7 |
| 13 | `031_DefendBehaviour_out` | the boarding place (inside the AllyEscapeBox) | (1945, 220, -1096) | 7 |

- NOTE: SPLIT MESH: the boarding action Triggers!BoardingTrigger_Car at (3252, 132, -20) is on another part of 159 polygons; the START row's part ends 1661 from it at (1967, 220, -1073). A bot cannot path to the vehicle (ZBoardEscapeVehicleTactic's path test fails): the bots end on their side
- NOTE: level exit Triggers!ExitTrigger_01 at (407, 396, 460): no place inside it on the START row's mesh part
- NOTE: BOARDS Triggers!BoardingGameplayTrigger at (0, 0, 0): no place inside it on the START row's mesh part
- NOTE: EXITS_BANK Triggers!ExitBankTrigger_01 at (291, 399, -4668): no place inside it on the START row's mesh part
- NOTE: NO level exit or BOARDS trigger on the START row's mesh part: the bots never reach stage 3, so they do not board through the tactic (0x4faf60) and the stage term of the traitor rule stays at 2
- NOTE: the AllyEscapeBox stands at (1967, 420, -1073), 1661 from the boarding action: bots inside it board (kl2 0x907a50: no stage and no path test) when the vehicle is in state 3 / 4 - they vanish there, they do not walk to the vehicle
- check: Squad#02 238 m, least clearance 14, Squad#03 256 m, least clearance 14, Squad#04 256 m, least clearance 14, Squad#05 246 m, least clearance 14, Squad#06 256 m, least clearance 14, Squad#07 248 m, least clearance 13, Squad#08 241 m, least clearance 14

## 4. The checks (`python tools\kl_fa_bots.py check <folder>`)

FAIL = must be none before an install; NOTE = differs from stock, said aloud. On a finished folder, read anew:

1. exactly 7 `ZFFActor` of team Ally; each group name has a digit 1..8 at index 18 (else int3 at kl2 0x51ab2d when
   the bot speaks, `re/bots_voice.md` 7), digits 2..8 once each; its squad group has `ZSquadScript` field 1 = `eHeistOnly`.
2. each bot's model (`.prp` and `.gms`) = `Heroes!Hero_0N\Ground`'s (the game's body swap 0x8f5e90 finds a bot by that
   number); its two .SND offsets = that hero's; its animation set is in the `.ANM`; its weapon path resolves; `ZSoldier` there.
3. an `AIMonitor` list 2 names `Timer_start_bots`; the timer names one first step in each of the seven squads; every
   reference of the squad resolves; each chain is walked to its end (a step without a controller, a `DefendBehaviourRout`
   without a place, a `TriggerLootDepleted` naming something that is no money object, a `TriggerActorsDead` naming a
   group without an actor: FAIL).
4. every place and every bot is on a polygon within 15 of its height, on the START row's connected part, at least
   10 from an edge without a neighbour; a path on the mesh joins the bot and its places in order (**one navigation part**).
5. stage: a place inside an ENTERS_BANK box; a place inside the level exit or a BOARDS box, OR the last place inside
   an `AllyEscapeBox`; without the box the boarding action must be on the same mesh part.
6. start places: 60 .. 600 from the nearest START point, at least 80 apart.
7. classes: every class of the squad is in the stock systems level; every controller is registered in kl2.exe and
   used by the systems level - one that is not (`AllyEscapeBox`: stock F02 F06 F08, Arcade levels too) is a NOTE with
   the stock levels that run it. `kl_prpjoin.misfits` on the squad's nodes.
8. files: `kl_scene.check`; every slot id of the room trees and the room index names an entity of the right kind;
   `.gms` record and `.prp` agree on place and model for every squad node.
9. `kl_voice.heisters`: no CRASH. `kl_fa.check`: no CRASH / BROKEN, and the 'bots' finding is gone.

Results: M01 0 FAIL / 0 NOTE, M02 0 / 0, M06 0 / 1 (AllyEscapeBox), M03 0 / 8 (AllyEscapeBox; seven times 'stage 3
is never reached'). `kl_maps.py audit` on each: PASS, the same known findings as the source build
(1 / 6 / 6 / 0 materials without a shader); `kl_maps.py preflight`: 0 CRASH.

## 5. The owner's four behaviours

`re/bots_behaviour.md` has the reading of kl2.exe; here is what follows for these builds and, for the lead, the hook
parts in the words to write them from. **No hook code was written** (klhook is the lead's).

### 5.1 Backstab

Stock Dog Days has it for Arcade bots (`ZBecomeTraitorTactic`, evaluate 0x79b7c0): stage term + the bot's money term
+ the player's money term >= a limit, a random roll, and the per-level switch `+0x6c`. The level data's part is the
bot's **stage**, and that is what the routes give: every squad has a place inside ENTERS_BANK (1), EXITS_BANK where
one is on the mesh (2), and the level exit box (3). M01, M02, M06: stage 3. **M03: stage 2 at most** - its level exit
box (z from -540) begins beyond the yard wall (z -600), its BOARDS box is a 10-box at the origin; with the stock
terms (0 / 0 / 2 / 3) a bank bot has 1 point less.

Not possible by data: the switch `+0x6c` is 0 on Arcade levels 1-3, and the table is a heap object no file feeds.
For the lead (`re/bots_behaviour.md` 5):

- **H6 first (read only)**: per second, in an Arcade session: the level byte `[[rules+0x5f8]+0x45]`, each crew
  record's `+0x10`, `+0x78` (stage), `+0x79`, the money dword `[[rules+0x5f8]+0x150+i*4]`, `[rules+0x1dc]`,
  `[rules+0x1d8]`; rules = `[[0x168e9e4]+0x54]` while `[[0x168e598]+0x5c] == 4`; records at `[rules+0x348] + i*0x7c`,
  count `[rules+0x354]`. One round on a `b_bots` build with this log answers B3, B4 and B7 at once.
- **H1 (data writes, once after `[0x168d7c0]` is non-null)**: for L = 1..11 at `[0x168d7c0] + 0x6ac + L*0x70`:
  `+0x6c` (int) = 1 or more, `+0x20` (float) lower than 7.0 (suggested first: 5.0), optionally `+0x18` (float, the
  'you shot me' limit). An ini section per value.
- **H2 (one bit, on demand)**: `byte [[rules+0x348] + i*0x7c + 0x79] |= 2` for a record whose bit 1 (mask 1) is set.
  (The two research notes number the bits differently; read here at 0x907ab8: `test byte ptr [eax+0x79], 1` = 'is an
  AI crew member'. So mask 1 = bot, mask 2 = traitor.)

### 5.2 Pay the driver and leave without you

Bots board by themselves; the vehicle waits its time and leaves (a Dead Men spline car / helicopter takes the
times of the tuning object: +0x62c = 10 s waiting). The BRIBE is a player action; no AI code calls it, and no level
controller does. Nothing in these builds. For the lead:

- **H3 (one game call on the main thread)**: `rules->vtbl[149](i)` (= 0x757510, thiscall, one stack argument) when
  record i has mask 1, `+0x10 == 4` (aboard), the human's record has not, and `[rules+0x1dc]` is 3 or 4. NOT tried:
  that slot 129 inside it accepts a bot's index. The line `Driver_Bribe` then plays in that bot's voice
  (`re/bots_voice.md` 1.4: speaker = the briber).
- **H4 (data, if H3 misbehaves)**: `[rules+0x1d8] = 0.0f` while `[rules+0x1dc]` is 3 or 4, and halve the bot's money dword.

On M06 and M03 the bots board through the AllyEscapeBox; record `+0x10` becomes 4 the same way (slot 45, 0x6840a0).

### 5.3 Blow the van up

Not by data: stock vans are shot by the POLICE because their body carries a `FakeTarget` of team Mercenary; nothing
makes an Ally soldier shoot it, and the four maps' vehicles (`OnlineEscHavokCar`: spline car, helicopter) have no
`ZAnimatedVehicle`, no `RelayAnimatedVehicleHit`, no damage path at all. For the lead:

- **H5 (one game call)**: `rules->vtbl[94](2)` (grade 2 = destroyed; 1 = 'heavily damaged', drives off at once)
  when a traitor bot (mask 2) is in play, not aboard, and somebody is aboard. NOT established that the Arcade class's
  slot 94 (0x6a1100, not read line by line) does anything sane for a spline car: try it on Retomoto first (baked
  vans, the stock form), then on M01.

### 5.4 Help you up

Dog Days' downed state is self-service; a partner heal is in the exe (`ZHealTactic`, built at 0x6ab6a2 only when
`ZSoldier` field 2 is not `eNever`) and its animations are in the `.ANM`, but no stock level uses it.

- **Data, built behind an option**: `python tools\kl_fa_bots.py build <source> <out> --heal` writes `ZSoldier`
  field 2 = `eSometimes` on the seven bots (enum 0xcfc664: eNever 0, eSometimes 1, eAlways 2). ASSUMPTION
  throughout: what the tactic's evaluate (0x64ed60) wants was not read, nor the default of the tuning byte `+5`
  that also gates it. The option was built and checked on M01 (PASS, scratch folder, removed); no delivered build has it.
- Hook: `ZFFPlayer::Resurrect` is exported; arguments and expected state not read (`re/bots_behaviour.md` 4.3 B).
- Say to the owner: stock Dog Days has no help-up in any mode; `--heal` is a one-field experiment, not a feature.

### 5.5 Voices

- **Lines**: reachable on all four builds for all seven bots (`kl_voice.py heisters`: 0 CRASH, 0 SILENT, AI heisters
  1..7). On a Dead Men map 74 .. 78 of the per-character lines are Dead Men's one recording whoever speaks; the
  bribe / left-behind lines are in the speaker's own Dog Days voice (`re/bots_voice.md` 3).
- **Barks**: none, as stock (voice slots 0 0 0 on every stock Arcade bot). `re/bots_voice.md` 6.4 has the recipe
  (`squad` / `squad_02` from L02's bank, about 130 sounds and waves, nothing in the `.WAV`). NOT built here: it has
  never run, the bank's pool limits are not known (largest that ran live: 4,967 sounds / 4,816 waves; M02 has
  4,911 / 4,774 already), and it would be the first change of these builds that touches sound. One map, one live run, then decide.
- **The human's line voice with a Dead Men body** (`re/bots_voice.md` 6.6) now matters more: with bots present the
  game's own swap finds 'the bot that wears the model' for a Dog Days body and exchanges the two voice bytes; for a
  Dead Men body it finds nobody. The two-byte exchange for the hook is described there.

## 6. Not done, and why

### 6.1 Things the data cannot do

Pay the driver (5.2), blow the van up (5.3), a bot that plans a betrayal, a help-up with an animation (5.4): no
level controller or squad field was found for any of them. The hook parts are six small items, none a code patch.

### 6.2 M03: the two mesh parts are not joined

Measured: START row, hall, vault, garage and yard are one part of 490 polygons; the level exit, the boarding action
(3252, 133, -20) and the van's street another of 159. The wall between them (z -600) is the one Dead Men's PLAYERS
climbed; `kl_escape` sinks one piece of it (x -1900 .. -1100) for the Dog Days player, the mesh is as Dead Men had it.
What a join needs, and why it was not done blind: a new polygon (or two edited ones) across the opening means new
records in arrays 3, 9 and 6 AND in the two trees (arrays 0, 1, 2: floats whose meaning `kl_pf4` does not know), the
area record's counts and box, and the waypoint numbering - every part of the mesh the notes mark 'NOT established'.
The cheaper door, a LINK (array 7: Dead Men's own mesh had one of kind 6 at this map, dropped by the conversion
because no Dog Days level uses that kind), makes the AI play whatever kind 2 means in Dog Days (a ladder or vault) at
a place with no such object. Neither can be checked offline. So: **the bots stay in the yard**, at (1967, 220, -1073),
16.6 m from the boarding action, in an AllyEscapeBox; they board when the van is in state 3 / 4 (the human calls
it by crossing the level exit box). If a join is wanted later, `kl_fa_bots.Nav` reads both parts: at the opened piece the yard's mesh ends at z -693 .. -802
(y 220, polygon 527 of the built mesh), the street's begins at z -535 (y 150, polygon 687).

### 6.3 Retomoto (analysis only; `python tools\kl_fa_bots.py plan <work>\build\rt_ai\retomoto_ai [--park ...]`)

- Mesh: 2,241 polygons in 56 parts; the START row (the balcony) is on a part of 359 = the tower floors down to the
  tower car; the street with the level exit, the vans and their boarding action is a part of 1,615. The two are
  joined for the human by the hook's jump (`KLJoin.ini`), not in the mesh.
- 21 loot objects are in reach of the tower part, the richest area 6 objects (1,800,000) in the boardroom round
  (4670, 20995, -460); ENTERS_BANK (`FASpecials!PIP!EnterLootArea`) has places on the tower part (stage 1); EXITS_BANK,
  the level exit and the three BOARDS boxes do not (stage 1 at most: no betrayal by the stock rule).
- With `--park 2670,19600,950` (the middle of `KLJoin.retomoto.ini`'s box, the floor in front of the tower car) a
  route plans: balcony (6000, 21020, -280) -> boardroom -> stairs (20646 .. 19727) -> (2630, 19600, 950), 13
  stations, every place on the tower part; narrowest places 11 .. 14 on the stairs.
- What it would be: seven bots that fight and loot through the tower, wait at the tower car, and vanish from there
  when a van is in state 3 / 4 in the street (the human gets there by the jump). They never appear in the street.
  Whether that is wanted is the owner's call; a street presence needs the hook to move actors (not researched).
- Costs: the same as on the four maps (no large block grows; `rt_ai`: .prm 79,269,328, .ANM 21,642,904, .fxc
  17,760,648, .WAV 23,041,360). NOT built: the Retomoto build is another session's, and its bank was built with
  the voice repairs off (`re/bots_voice.md` 6.1) - rebuild that first.

## 7. Live checks (the lead's; in this order, one map first - M01 or M06)

| # | run | look for |
|---|---|---|
| B1 | load `b_bots\M01` (the 90 s load check) | it loads. A fault at 0x46fe87 / 0x8add12 (class) or 0x8adbba (empty pool) would be the new entities; a fault in a room / octree walk (0x719850, 0x719884, 0x48e910) the slot ids. Then build once with `--no-tree` and load that: if it loads, the group-tree listing or the moved records are the cause |
| B2 | Arcade round, stand still 15 s | seven heisters standing round the START row in the bodies of Hero_02..08, names on the score board; 10 s after GO they walk off toward the first station (section 3). Is the body you got missing among them (the game's swap, 0x8f5e90)? |
| B3 | follow them | do they pass the ENTERS_BANK place and then pick money up by themselves (H6: stage 1, money rising)? Do they stop in doorways (M01 stations 6 and 8: all seven share one place)? |
| B4 | call the vehicle | M01 / M02: do they run to the car and get in (H6: stage 3, status 4)? M06: are they taken from the box at the helicopter? Does the vehicle leave with / without them, and does the round end as on a stock map? |
| B5 | pick a Dog Days heister on the Heister page, then a Dead Men body | Dog Days body: the bot with that body takes another. Dead Men body: eight bodies and you (no swap): is a bot's body doubled? |
| B6 | listen | 'Kill him! What is his, is yours!', the bribe and left-behind lines: who speaks, in which voice |
| B7 | Arcade level 4 or later, or H1 / H2 | a bot that turns on you: is it announced, does it fight the other bots |
| B8 | a `--heal` build of the same map; go down beside a bot | anything at all |
| B9 | leave to the menu, load again, twice | the second and third load (the `.prm` block is the same size as before, the entity count is 148 .. 211 higher) |
| B10 | M03 | the bots wait in the yard corner (1967, 220, -1073) and are gone when the van stands in the street |

Leaderboard rule as for every grafted map (CLAUDE.md): the Steam write guard on, do not Quit inside a session.

## 8. ASSUMPTIONS and guesses of this build, in one place

- Everything `re/bots_squad.md` marks so: that trigger boxes report AI actors as activators (the bot's stage); that
  a `DefendBehaviourRout`'s NEXT list fires when its places are reached; that the level exit raises the stage of a
  bot and calls the vehicle for it; that a bot boards a Dead Men spline car as it boards a stock helicopter (same
  `OnlineEscHavokCar` branch; F03 is the stock level that relies on the tactic alone with that class).
- That the name the exe reads at 0x588980 is the actor's parent group (kept exactly as stock, so it holds either way).
- That an AllyEscapeBox which is never hidden ticks (2.1); that listing the groups in the root tree matters (2.3).
- `eDMS_Sprint` on the way out; `SPACING` 18 m; `CLEAR` 60; the loot wait of 20 s (F07's value; stock 15 .. 60);
  the cut-down chain itself (no `RandomTrigger`, no `TriggerActorsDead`: F08 / F09 have none, but no stock level has
  this exact combination).
- That the mesh's height is where feet stand on a Dead Men map (stock F01 F03 F07: the bots' feet are at the mesh's
  height; seen live for the road of Retomoto, `tools/kl_fa_street.py`).
- The heap budget (`.gms` header +0x1c) is left as it was for 148 .. 211 more entities (`kl_scene`: what it counts
  is not decoded; the loader takes at least 0x340000 and the builds' budget + 0x57800 is far below that).

## 9. Where this differs from the research notes (measured here)

- `re/bots_squad.md` 8.3 puts the loot before the way out; on M01 the loot lies beyond the way out (2.2).
- Its 'about 16 nodes per bot' is 21 .. 30 here: a station every 18 m, each of up to 3 boxes per step.
- Its table 7 counts all `OnlineMoneyCtrl` as loot (306 .. 363); 6 / 44 / 24 / 4 are (2.2).
- Its check 8.5.4 uses `kl_maps.NavParts.at`, which falls back to the nearest polygon's centre for a point off the
  mesh; this module's `Nav.at` returns nothing there, and the check wants every place ON a polygon.
- The two notes disagree on the bit names of record +0x79 (5.1); the masks are 1 (bot) and 2 (traitor).

## 10. Changes outside `tools/kl_fa_bots.py` and `re/bots.md`

- `tools/kl_maps.py`, `audit()`: two lines - when `steps.json` has a `bots` entry it prints 'then the AI heister
  squad (kl_fa_bots) changed ...'. Nothing else; `kl_fa.py`, `kl_escape.py`, `kl_graft.py` not touched.
- For the lead: `kl_maps.ready_one` could call `kl_fa_bots.build` as a fourth step (after the wardrobe) once B1 - B4
  have passed on one map; `kl_expansion.py` would then take `b_bots\<map>` in place of `z_maps\<map>`.

## 11. LIVE FINDING and its fix (2026-10-10): on M01 a bot called the escape vehicle on its way IN

Runs BOT1 / BOT2 of the lead on `b_bots\M01`: the seven bots appear, walk to the diner, loot and gather at the
escape; the round ended 152 .. 156 s after GO with the vehicle's countdown on the HUD - with the default squad
and with `--wait-guards --loot-seconds 120` alike. Worked out OFFLINE (files and kl2.exe; the lead's control
run without bots was not in when this was written):

- **Read, kl2.exe.** `ZOnlineExitLevelTrigger` slot 34 (0x6c3d50) hands ANY activator to the rules' slot 44 =
  `ZGameRulesHeist` 0x6cd8e0. That function takes a player (record 0) OR an object of the actor class (mask
  0x1547b24) that has a crew record (0x78f470); for a bot (record +0x79 bit 1) the one player test (0x6cd965)
  is skipped; with the record's status 0 and the vehicle state `[rules+0x1dc]` 0 it calls 0x8154f0 = the
  vehicle is called. **A bot inside a level exit box calls the vehicle exactly as the human does.**
- **Measured, the files.** M01's `Triggers!CallExitVehicle_02` is a box of half extents (2800, 200, 1400) round
  (5996, 160, 20490): z up to 21,890. The diner's door `Triggers!LeavingHeist_01` (EXITS_BANK) stands at
  z 21,883 - INSIDE it - and so do both rich loot people at their start places (`The_Senator` 1,250,000 in
  `_02`, `FBI-Agents_01` 400,000 in `CallExitVehicle_01`). The old plan took 'the way out before the loot'
  (the shorter order, section 2.2): every bot stepped into the box 139 .. 144 m after its start, on the way to
  station 9 (the loot). Nothing else on M01 names the car (searched: only the two boxes and the boarding
  action; no timer), and the round clock is 6 minutes.
- **The time fits.** The round gets 60 s once the first vehicle has left (seen live, re/retomoto_street.md);
  a Dead Men spline car takes the tuning object's 20 s in + 10 s waiting + 20 s out (re/bots_behaviour.md 2.2):
  call + 110 s. The bots start 10 s after the round-start event = about 2 s after GO; 139 .. 144 m at a run of
  about 3.3 m/s is 42 .. 44 s: 2 + 43 + 110 = 155 s. And the loot wait cannot change it: it comes after the box.
  (The 3.3 m/s is computed FROM this fit, not measured; the control run decides.)
- M02, M03, M06: no bot path enters a level exit box before the loot wait (measured the same way; M03's home
  mesh part does not touch its box at all).

**Changed in `tools/kl_fa_bots.py`** (plan and check; nothing else of the build step):

- `plan()`: unless `--early-call`, every polygon of the START row's mesh part that a level exit box touches is
  kept clear up to the loot wait: loot whose place is inside such a box is not the route's loot (a NOTE names
  it), the order of the stations must have a way to the loot outside the boxes (`Nav.path(..., ban)`), and
  the stations and the seven places before the loot wait are chosen outside them. The plan prints where each
  bot is first inside a box (`plan.vehicle_call` in `bots.json`).
- `check()`: walks each squad's places up to its first wait; a bot inside a level exit box there is a FAIL
  (a NOTE on an `--early-call` build). The old `b_bots\M01` FAILS it (seven times), the other three and all
  `u_maps` folders pass.
- `--early-call`: the plan as it was (for a comparison run).

M01's route now (`<work>\build\u_maps\M01`; Squad#02): five stations to the diner, ENTERS_BANK
`EnterHeist_01` (6101, 0, 23059), **the loot = the diner** (4 objects, 280,000: the waitress, the till, the two
gang members) round (6531, 0, 22970), wait 20 s or until it is empty, then (5642, 0, 22186), the door
`LeavingHeist_01` (stage 2 - and the vehicle call), `CallExitVehicle_02` (4733, 0, 20700), the boarding place.
First inside a level exit box after 155 .. 167 m of path, after the loot wait.

Not established, say it to the owner: (1) the bots' own `ZLootTactic` takes any money object the pathfinder
joins to the bot (re/bots_squad.md 4) - the Senator's 1,250,000 may still pull a bot into the box before the
wait is over; (2) the vehicle is still called as soon as the squad has looted: by the same arithmetic about
65 s after GO on M01 with the 20 s wait, the round over about 3 minutes after GO unless somebody boards.
`<work>\build\u_maps\M01_wait90` is the same build with `--loot-seconds 90` (the wait ends earlier when the
four objects are taken). A hold that does not depend on the loot would be a `TriggerDelay2` step before the
way out (stock squads have 16 .. 71 s of them, re/bots_review.md D1): not built.

The squad on the TUNED maps: `<work>\build\u_maps\M01 M02 M03 M06` = `kl_fa_bots.py build` on
`<work>\build\t_maps2\<map>` (guns + camera + enemies, re/map_tune.md 7); checks and sizes there.

## 12. After the owner's round with the bots (2026-10-10 evening, agent p-loot): loot stops, cases, the wall

Owner, after playing `u_maps\M01 M02 M03 M06`: *'the issue on late night is they dont shoot open the casing stuff bc
its glass and u need to shoot it to loot, the van is such a damn problem and they dont loot the warehouse people on
diner not sure about park, the bank they gotta vault on the garbage then over the wall'*.

**OFFLINE: nothing here ran in the game, nothing was installed, nothing was written into the Dog Days folder.**
Words: **read** = disassembled at the address given, **measured** = counted on the files, **ASSUMPTION**, **GUESS**.
Builds: `<work>\build\y_loot2\M01 M02 M03 M06`, made from `<work>\build\t_maps2\<map>` (complete builds: t_maps2 +
the squad) by `python tools\kl_fa_bots.py owner <work>\build\t_maps2 <work>\build\y_loot2` (log: `y_loot2\run.log`).

### 12.0 Short answers

| the owner said | what was found | what the build does now |
|---|---|---|
| Late Night: they do not shoot the cases open | 23 of the map's 26 money containers (1,940,000 of loot) open ONLY when their glass is shot; no AI code shoots at an object, and no stock level has such a case (12.1) | a route step breaks the glass (`'Activate'`, the routine a bullet ends in) and opens the container, case by case as the bots reach the store; then the watch shop as a second stop |
| diner: they do not loot the warehouse people | the Senator (1,250,000) and his man (400,000) stand INSIDE the two level exit boxes, and a crew member in such a box calls the car - bot or human, nothing in the exe gates it and no stock level gates it by data (12.2) | the two boxes are cut back to the car's end of the lot; the bots loot the diner, go out by the back door, fight and loot at the Senator, THEN walk on into the box (the car is called there) |
| not sure about park | the route named one of four people with money; the other three stand beside it (12.4) | four stops in path order: US boss 800,000, the woman on the island 500,000, the guard 250,000, Retomoto 1,800,000 |
| bank: vault on the garbage, over the wall | Dog Days' AI can cross by a mesh link; only the DROP kind has an animation in Dog Days' files - a climb UP has the code but no clip (12.3). The wall piece is already sunk for the player | one drop link at the sunk piece: the bots hop down the 70 into the street and run to the van; a gather place in front of it in an AllyEscapeBox is the fall-back |
| the van is such a damn problem | (the vehicle itself is another job's.) Measured: on the builds played, **all seven bots of Late Night Opening waited 7 .. 237 from the car's route - five of them within 120, in the road at the car's stop**; on the diner four of seven within 250 (12.5) | every place of the way out is at least 250 from the car's routes and on one side of the road |

Nothing was added to the four large blocks (12.6). All of it is level data; no hook part.

### 12.1 Late Night Opening: how a case works, and why a bot could not loot it

Measured on `t_maps2\M02` (the same objects as Dead Men's level):

- 26 `OnlineMoneyContainer`. Three are cash drawers of the stock form (the container has its own `TriggerBox2`
  {itself, 125, 'Open'}: somebody within reach opens it). **23 have no opener but their glass**: 11 in the jewel
  store (`SI0401_M02_FA_ShatterBox_3m_01 / _03 / _04`, `_10m_01`, `PC0402_M02_FA_ShatterBoxA..D_0n`), 12 in the watch
  store (`PC0406_M02_FA_WatchStore_Wallmontre_Glass_01..06`, `Glassmontre_Large / Small_Group_0n`).
- Such a case is three siblings in the room: `<case>!Whole_01` [ZSTDOBJ] + `HavokShatterGlass` + `RelayMessage`
  {'HavokShattered' -> 'Open', -> `<case>!MoneyContainer`}; `<case>!MoneyContainer` [ZBoxPrimitive 10 x 10 x 10] +
  `OnlineMoneyContainer` {0: the jewels, 1: 0, 4: 10, 5: [], 6: 'Activate'}; the jewels (`PC0402_M02_FA_Jewels*`,
  `PC0406_M02_FA_Watches_*`): ZSTDOBJ + `OnlineMoneyCtrl` type `ZMONEYCTRL_TYPE_CONTAINER` + its own `TriggerBox2`
  {itself, 45 .. 175, 'AI_TRIGGER_WITH_ACTIVATOR'}.

Read, kl2.exe (message ids are the dword at +8 of the static name objects built by 0x6fb080):

| object | slot 26 (messages) | what it does |
|---|---|---|
| `ZHavokShatterGlass` 0x471410 | 'ProjectileHit' -> 0x53f6d0 -> 0x4b9740; **'Activate' -> 0x8d1b60**; 'CanPenetrate' | both ways end in the same two routines, 0x67e6a0 and 0x79bd10 (the shatter), unless the glass is already broken (byte +0x30 bit 0). The shattered glass sends 'HavokShattered' to its own node (0x707c10) |
| `ZRelayMessage` 0x8f1680 | its in-message | sends its out-message to its target |
| `ZOnlineMoneyContainer` 0x419f80 | 'ProjectileHit' (only when its byte +0x38 is set; which field that is was not established), **'Open'** | 'Open' -> 0x766e50 unless the sender is a player in one particular state; no other test, a null sender is taken. It clears byte +0x4c (a second 'Open' returns at 0x419fb4), sends field 6 to field 5's nodes and starts a countdown of field 4 (10 in all 117 stock containers too; its unit was not established); at its end 0x868fb0 makes every object of field 0 ACTIVE (0x4fb580: byte +0x74) |
| `ZOnlineMoneyCtrl` 0x6cdb40 | 'AI_TRIGGER_WITH_ACTIVATOR' (the take) | ignored while byte +0x74 is clear (0x6cdb8f) - **an object in a shut container cannot be taken, by a player or by a bot** |
| `ZTriggerDelay2` 0x71e250, `ZRelayMessageList` 0x6e3cb0 | 'AITrigger' / its in-message | the timer arms; the list sends its out-message to every target (at once when its delay is 0) |

How stock Dog Days handles loot in containers (measured, F01 .. F09): **no stock level has a `HavokShatterGlass`
at all** (0 in 21 levels; `ShootAtTrigger` is a trigger that fires when shot, one use in L05; `FakeTarget` is what
makes the POLICE shoot the vans). All 117 stock containers (F01 58, F03 12, F08 47) open by a `TriggerBox2` 'Open' of
125 .. 150 when somebody stands there, and F01's squad opens its vault's cases by script: `KickDoorMonitor` ->
`RelayMessageList` {'AITrigger' -> 'DoorOpened', 8 / 10 cases}. Stock bots shoot at nothing; a case is told to open.

Built (`--cases glass`; per bot, clones of stock forms):

    ...\012_DefendBehaviour_to_loot  (the ENTERS_BANK place)  -> 018_Timer_at_cases
    018_Timer_at_cases   TriggerDelay2 {1.0 s} -> [013_DefendBehaviour_to_loot, 018_Relay_break_glass, 018_Relay_open_cases]
    018_Relay_break_glass  ZBoxPrimitive + RelayMessageList {'AITrigger' -> 'Activate', the glass of this bot's cases, 0.0}
    018_Relay_open_cases   ZBoxPrimitive + RelayMessageList {'AITrigger' -> 'Open', their MoneyContainers, 0.0}
    013_DefendBehaviour_to_loot  (the bot's place at 'its' jewel)  -> 020_Timer_done_looting {21 objects, 45 s}

- Transitions: `DefendBehaviourRout` -> `TriggerDelay2` 329 and `TriggerDelay2` -> `DefendBehaviourRout` 119 times
  in the nine stock squads; a `TriggerDelay2` naming a `RelayMessageList` is stock F02's (2); the relay node is a
  clone of F01's `Gameplay!merc_bot_squad!KickdoorMonitor!KickDoor_RelayList_Door08`. A timer with several targets
  is stock (`Timer_start_bots` has seven; sizes up to 18).
- Each case is named by the three bots whose loot places are nearest to it (`CASE_BOTS`; 2 .. 8 cases a bot in the
  jewel store, 3 .. 9 in the watch store): the glass goes as those bots come in, and two of the three may be dead.
  Glass and container are both told: if 'Activate' does not break the glass in the game, the case is open all the
  same (the jewels can then be taken through the intact pane - check L1 shows which).
- Loot wait 45 s a store (GUESS; it ends earlier when the store is empty). Second stop: the watch shop across the
  mall (18 objects, 535,000: 13 watches behind 12 panes, the drawer, the clerk).
- Checked on the files by a script that uses none of the tool's own logic (`verify.py`): 23 of 23 glass-only
  containers are named by an 'Open' relay and all their panes by an 'Activate' relay; every relay target is a node
  with `HavokShatterGlass` + `RelayMessage`, or with `OnlineMoneyContainer`; 684 references of the 288 new nodes,
  each `ROOT\`-prefixed and naming exactly one node.
- `kl_fa_bots.py check` now FAILs a loot wait that names loot in a glass-only case no step opens: the build the
  owner played, `u_maps\M02`, fails it seven times (11 cases) - the owner's finding, found by the checker.
- For the human nothing changes until a bot is in the store: an untouched case still has to be shot.

Not chosen: making a bot really fire at the glass. The exe has no behaviour for it; a `FakeTarget` of team Enemy
on the pane might draw the bots' fire (the police shoot the vans that way) but nothing would take it away once the
glass is gone. Not tried.

### 12.2 The diner: the warehouse people and the car

Measured (`t_maps2\M01`; a trigger box's three sizes are half extents - the fit of runs BOT1 / BOT2, section 11):

| | place | in |
|---|---|---|
| `Triggers!CallExitVehicle_01` | centre (1592, 160, 20978), half (1600, 200, 880): x -8 .. 3192, z 20098 .. 21858 | - |
| `Triggers!CallExitVehicle_02` | centre (5996, 160, 20490), half (2800, 200, 1400): x 3196 .. 8796, z 19090 .. 21890 | - |
| `AI_Enemies!TheBoss\The_Senator` 1,250,000 | (3384, 3, 19893) | box 02, 188 inside its west edge |
| `AI_Enemies!BossFlank_01\FBI-Agents_01` 400,000 | (3007, 2, 20222) | box 01 |
| `BossFlank_02`, `BossFlank_03` (his other two men) | (2791, 13, 20578), (3290, 4, 20240) | 01, 02 |
| back doors `LeavingHeist_01 / _02 / _03` (EXITS_BANK) | (4121, .., 21883), (2918, .., 21883), (1882, .., 22138) | 02 (7 inside its edge); 25 beyond box 01's edge; outside |
| boarding action `Triggers!BoardingTrigger_Car` | (5884, 181, 20448) | 02 |

- Read, 0x6c3d50 -> 0x6cd8e0 (`ZGameRulesHeist` slot 44): Arcade, the rules' byte +0xe8a clear, the activator a
  player or an actor with a crew record whose status is 0 (a human also: not in one particular state), the vehicle
  state `[rules+0x1dc]` 0 -> 0x8154f0. **No test of the heist stage, of money, of loot left.** The box test itself
  is the tick 0x65dd10 (shared with `ZOnlineBaseGamePlayTrigger`): no flag of the node is read there.
- Measured, stock F01 .. F09: nine `OnlineExitLevelTrigger`, every box shown (flags 0, `ZGEOM[3]` 0) and named by
  NOTHING. **No stock level gates its exit; the premise 'as stock levels gate their exits' does not hold.** So a
  human avoids calling the car only by not walking into the box - and on this map he cannot rob the Senator
  without walking into it. That is Dead Men's own design (the boxes and the people are where Dead Men put them; its
  exe was not read for a gate).
- Hiding the box until the loot is taken (flag 0x400 + an `ActivateGeom`) was NOT built: no stock level does it to
  this class, and whether a hidden node's tick is skipped was not read (the money object tests its own hide bit
  explicitly, 0x6cdb6e; this tick does not).

Built (`--exit-boxes cut`, table `EXIT_CUT`): two fields of each box - `ZGEOM[2].x` with the `.gms` place, and
`ZBoxPrimitive[0]`:

| | was | is |
|---|---|---|
| `CallExitVehicle_01` | x -8 .. 3192 (centre 1592, half 1600) | x -8 .. 2400 (centre 1196, half 1204) |
| `CallExitVehicle_02` | x 3196 .. 8796 (centre 5996, half 2800) | x 4600 .. 8796 (centre 6698, half 2098) |

Read back from the written files: no loot object and none of the three back doors is in a box; the boarding
action is in box 02. What it means for the HUMAN too: stepping out of the diner's back door or going for the
Senator no longer calls the car; walking on toward the car's stop (east of x 4600) or west along the lot (west of
x 2400) does. `--exit-boxes keep` builds the route without the cut (the warehouse is then left to the bots' own
loot tactic, as in `u_maps`).

The route now (Squad#02; `bots.json` has the other six, 110 apart):

| # | step | place | what |
|---|---|---|---|
| 1 - 5 | `010`, `011` | (810, 0, 28971) (1317, 0, 27432) (2725, 0, 26394) (3583, 0, 25130) (4771, 0, 23910) | from the START row to the diner |
| 6 | `012` | (6101, 0, 23060) | `EnterHeist_01`: stage 1 |
| 7 | `012` | (6532, 0, 22970) | stop 1, the diner: register 100,000, two gang members 80,000 + 60,000, the waitress 40,000 |
| | `020_Timer_done_looting` | | until the four are taken, at most 30 s |
| 8, 9 | `030` | (5642, 0, 22187), (4096, 0, 21883) | to the back door `LeavingHeist_01`: stage 2 (no box there any more) |
| 10 | `030` | (3384, 0, 19894) | stop 2: the Senator and `BossFlank_01` (1,650,000); the seven stand round them, 92 .. 224 from a wall |
| | `040_Timer_done_looting` | | until both are taken, at most 30 s |
| 11 | `050` (sprint) | (4444, 0, 20347) | east along the lot, outside the box |
| 12 | `050` | (5738, 0, 20020) | inside `CallExitVehicle_02`: stage 3, **the car is called here** - after 205 .. 216 m of path |
| 13 | `050` | (5844, 0, 20288) | the wait for the car, 303 .. 515 from its route, 150 .. 400 from the boarding action |

Not established: that the bots win the fight at the Senator inside 30 s (the tuned enemies are tougher,
re/map_tune.md); what a bot does there when the time is up and he lives (it runs on; the money stays).

### 12.3 The bank: over the wall

What Dog Days' AI can do at such a place - read:

- The navigation mesh has LINKS (array 7) between WAYPOINTS (array 5). The path search 0x5cdd70 treats a waypoint
  as a node of its own: at 0x5ce01a it walks the waypoint's link range, takes the target waypoint
  `area[5] + number`, skips a link whose switch is blocked, adds the link's cost and puts the link's kind into
  the path node.
- The mover is `ZFFSpecialLink@Locomotion` (vtable 0xb78dd4, slot 1 = 0x4a5160): it starts within 20 of the
  link's start (40 for the other kinds) and picks a clip from the table at 0x15489e8, filled at 0x579920:

  | kind | clip | chosen by |
  |---|---|---|
  | 1 | `/Movement/Climb/Up/Low`, `/Medium`, `/High` | the height to climb: up to 120, up to 170, more |
  | 2 | `/Movement/Fall/Fall_1m`, `/Fall_2m` | the height to drop: up to 160, more |
  | 3 | `/Movement/Leap/Forward` | - |

- Measured: stock Dog Days has 192 links in 12 levels (F02 9, F04 40, F05 5, F06 55, F07 26, seven campaign
  levels), **all of kind 2, all one way: the target is 44 .. 523 LOWER in 182, level in 10, never higher**; up to
  228 across; cost 0.58 .. 1.01 of the distance; each link has two waypoints of its own, on the border edges of
  their polygons. So stock bots hop down ledges, and that is all the links do in Dog Days.
- Measured, the `.ANM` of the builds and of stock F07: `Fall_1m` and `Fall_2m` are slots of `Kane_NPC` and
  `Lynch_NPC` (and Thug, Swat_02, Civilian, Police ...); **`/Movement/Climb/Up/*` and `/Movement/Leap/Forward` are
  no slots at all**. The climb code is in the exe, the clips are not in the game. A real vault UP onto the
  dumpster is therefore not available by data (it would need Dead Men's three climb clips joined into the
  Kane_NPC / Lynch_NPC sets - a growth of the `.ANM`, not tried; and the Dog Days PLAYER could still not follow).
- The place: `kl_escape.open_wall` sank `SO0101_M03_Wall_Low_8m_05` (x -1900 .. -1100) to yard height, which is
  how the human gets out (re/escape.md). The yard's mesh ends on the edge (-3645, 220, -693) .. (-704, 220, -802)
  of polygon 527; the street's on z -535 from x -2559 to x -1487 (polygon 687, y 150). Neither polygon had a
  waypoint. The dumpster stands on the street side of the piece's east third (x -1454 .. -1200).

Built (`--drop`, table `DROPS`; `add_drop()` in the tool): ONE link of kind 2 and its two waypoints.

    waypoint 83  x -1704.3  y 220.0  z -765.6   polygon 527 (area 38)   link 0: cost 242, kind 2, switch -1
    waypoint 94  x -1700.0  y 150.0  z -533.5   polygon 687 (area 48)   232 across, 70 down -> Fall_1m

- Renumbered with it: 'waypoints before' of the later polygons, the two areas' waypoint counts and the later
  areas' first waypoint, array 10, every waypoint's link range. Trees, polygons, vertices, edges and area boxes
  are byte for byte (`diff`). `kl_pf4.check` and `kl_maps.nav_facts` (every rule the 21 stock meshes obey) hold.
- My own flood over the written mesh (edges + the link, one way): from the START row's polygon 649 polygons are
  reached, the boarding action's polygon among them; from the boarding action back to the START row: no. The mesh
  is 8 parts now (was 9); the bots' part has 649 polygons (490 + 159).
- 232 across is at the stock maximum (228): the mesh is drawn in from the wall on both sides. ASSUMPTION that the
  mover carries a bot 2.3 m forward during a 1 m fall clip as it does for stock's widest links.
- In front of the link the seven gather round (-1706, 220, -899), a step ends there, inside an `AllyEscapeBox`
  (350 x 416 x 350 round (-1706, 420, -899)). If the AI does not take the link they stand there and are taken
  aboard from there once the car waits (the behaviour of `u_maps\M03`, 16 m further west); if it does, they call
  the car themselves in the street and board through the tactic. A bot that reaches the box while the car
  already waits is taken from the box and does not cross.
- No kind-1 link was written (no clip). No dumpster is climbed: the bots cross where the player crosses.

The route now (Squad#02):

| # | step | place | what |
|---|---|---|---|
| 1 - 6 | `010`, `011` | (-406, 700, -10896) (291, 800, -9452) (-138, 800, -7808) (-664, 800, -6319) (-420, 401, -5927) (-734, 240, -7000) | plaza, `EnterBankTrigger_01` (stage 1), hall, stairs, garage |
| 7 | `012` | (424, 225, -6154) | the loot: the garage's money boxes (11 objects, 2,120,000), at most 20 s |
| 8 - 11 | `030`, `031` (sprint) | (-345, 240, -4930) (-1231, 231, -4751) (-1476, 220, -3091) (-1237, 220, -1504) | west door `ExitBankTrigger_02` (stage 2), the yard |
| 12 | `031` | (-1729, 220, -922) | **in front of the drop** (the fall-back box) |
| | | (-1704, 220, -766) -> (-1700, 150, -534) | the link: 70 down into the street = inside `ExitTrigger_01` (z from -540): stage 3, **the car is called** - after 216 .. 234 m of path |
| 13 - 15 | `032` | (-1651, 150, -130) (-81, 109, -171) (854, 71, -155) | east along the street on its SOUTH side (the car comes from behind along z 22 .. 130) |
| 16 | `033` | (3092, 0, -220) | the wait, 252 .. 412 from the car's route; boarding action at (3252, 133, -20) |

For the lead, if check L3 shows that the AI does not take the link: the honest alternative is the teleport
`klcrew_rt.c` already has (`0x62a900(actor, rot[9], pos[3], 1, 1)` from the game's thread, with its assert guard):
a `[CrewDrop]` section in a `KLJoin.ini` beside the archive with From = the gather box round (-1706, 220, -899),
radius 350, To = seven places round (-1651, 150, -130), done once per bot that stands in the box with the vehicle
state 0. Not written: the link is the game's own means and has to be seen failing first.

### 12.4 The park

Measured: four people carry money - `AI_Enemies!US_Boss\US_Boss` 800,000 at (867, 158, 6410),
`US_DrugSquad_Secure_Boss\Drug_Faction_2_Female_01` 500,000 at (625, 626, 2441),
`JPN_DrugSquad_Secure_Chopper_01\Secure_JPN_Guards_01` 250,000 at (511, 434, -397), `JPN_Boss\Retomoto` 1,800,000 at
(210, 170, -2275). None is in the level exit box; all four lie along the old route, which waited at Retomoto only.
Now (`--stops 4`): `Enter_BridgeHouse_01` (796, 303, 5808) first (a bot loots from stage 1 on only), then

| stop | place of Squad#02 | wait |
|---|---|---|
| US boss | (828, 234, 6410) | 20 s or taken |
| the woman on the island | (800, 498, 4648) -> (625, 635, 2401) | 20 s |
| the guard | (801, 564, 673) -> (511, 430, -397) | 20 s |
| Retomoto | (210, 220, -2276) | 20 s |

then (-548, 220, -3783), (-953, 220, -5192), the level exit box at (-1656, 220, -6634) (the helicopter is called),
the AllyEscapeBox at the helicopter (-1709, 220, -6564). No case, no box cut, no link on this map.

### 12.5 The car's road (found while placing the way out; the vehicle itself is not this job's)

Measured with a script of its own (`lanes.py`: the two `ZEditorSpline` routes of `OnlineEscHavokCar` and the
stretch from where the car stops to where its drive away begins), distance in the plan from each bot's LAST place
- where it stands and waits for the car - to that road:

| build | M01 | M02 | M03 |
|---|---|---|---|
| `u_maps` (played) | 42, 69, 184, 218, 307, 333, 360 | **7, 44, 64, 74, 119, 226, 237** | 1122 .. 1308 (never left the yard) |
| `y_loot2` | 303 .. 515 | 256 .. 449 | 252 .. 412 |
| way-out places nearer than 250, old -> new | 10 of 28 -> 0 of 21 | 12 of 70 -> 0 of 63 | 0 -> 0 of 63 |

The car is a Havok physics car, 2 m wide. On Late Night Opening five of the seven bots stood within 1.2 m of the
line it drives, at its stop. **ASSUMPTION that this is part of 'the van is weird / a damn problem'** - it is the
one thing in the files that differs between a round with bots and one without; it was not seen. Built
(`--lane`): on the way out every place keeps `LANE_CLEAR` = 250 (GUESS) from the routes and stays on the side
the bots come from; the stage place uses the whole exit box instead of its middle (the middle is the road).
A baked van (another job is laying F07's key-framed van on these maps) has no spline: `lanes()` then finds no
route and the places are chosen as before - tell this job, or give `lanes()` the van's keys.
(DONE 2026-10-10 night, section 13: `lanes()` reads the van's position keys.)

### 12.6 The builds, the budget, the checks

Bytes; before = `t_maps2\<map>`, after = `y_loot2\<map>`:

| | .prm | .ANM | .fxc | F01_Main.WAV | chunk-table entries (limit 69,632) | entities | archive sha1 |
|---|---|---|---|---|---|---|---|
| M01 | 55,917,968 = | 22,061,764 = | 17,760,648 = | 21,722,704 = | 50,254 = | 14,999 -> 15,168 (+169) | `915e24d5f24c` |
| M02 | 55,449,184 = | 22,202,472 = | 17,760,648 = | 22,527,568 = | 58,583 = | 21,934 -> 22,222 (+288) | `c8060a6a0729` |
| M03 | 61,299,008 = | 22,202,616 = | 17,760,648 = | 22,716,752 = | 62,892 = | 19,827 -> 20,025 (+198) | `e4bc7bdb19a6` |
| M06 | 50,415,712 = | 21,642,576 = | 17,760,648 = | 21,775,744 = | 47,114 = | 15,599 -> 15,804 (+205) | `042c10e62cf5` |

(`=`: the same size before and after. The `.prm` differs in content only as before: 4 bytes in each model root
that names an `.oct` record. `u_maps` had +148 / +211 / +163 / +163 entities.)

| check, on each of the four | result |
|---|---|
| `kl_fa_bots.py check` | PASS: 0 FAIL; NOTEs 0 / 1 / 1 / 1 (a controller the host level F07 does not use: `RelayMessageList` - stock F01 F02 F03 F05 run it; `AllyEscapeBox` - F02 F06 F08) |
| `kl_fa_bots.py diff t_maps2 y_loot2` | only the squad was added (+ M01: 2 level exit boxes cut, x and first size; + M03: 1 drop link in the mesh) |
| `kl_maps.py audit` | PASS (1 / 6 / 0 / 6 known, as the source builds) |
| `kl_map_guns.py check` | problems: 0 |
| `kl_impact.py` | problems: 0 |
| `kl_map_escape.py check` | 0 faults |
| `kl_maps.py preflight` | CRASH 0; RISK 0 / 3 / 0 / 2 (the source builds' own lines) |
| `debug\check.py` | 0 records with a layout Dog Days never stores |
| `verify.py` (own reading, 12.1 - 12.3) | 196 / 684 / 259 / 217 references of the new nodes, all `ROOT\` + exactly one node; `.gms` and `.prp` agree on the cut boxes |

- **Nothing of before changed by default**: `kl_fa_bots.py build <t_maps2\M01> <x>` without the new options writes
  an archive with the sha1 of `u_maps\M01` (`4ea0322d59cf`), and `kl_fa_bots_rt.py`'s plan of Retomoto is equal
  with the module of this morning and with this one (JSON and log compared).
- `KLGuns.ini`: `kl_map_guns.py check` and klgun.c want a line `Entries=<chunk count of the .prm>` since this
  afternoon; `t_maps2` was built before that and FAILS the gun check for that alone. `build()` adds the line to
  the copy in its output folder (50254 / 58583 / 62892 / 47114); nothing else of the file changes.
- `kl_map_tune.py check` on these folders still has gap G1 of re/u_maps_review.md (it does not know the bot
  step); not this job's file.

### 12.7 Live checks, in this order (the lead's)

| # | run | what proves it |
|---|---|---|
| L0 | `y_loot2\M02`, the 90 s load, then a round start | loads; seven bots at the START row as on `u_maps\M02` |
| L1 | Late Night: follow the bots into the jewel store, do NOT shoot a case | about 1 s after a bot passes the store's door (1488, 500, 1879) the panes of its cases burst (sound, shards) and the jewels can be picked up; klbot's log: the bots' money rises. If the jewels can be taken but the glass stands: 'Activate' did nothing, 'Open' did (rebuild with `--cases all` is no help; tell this job). If neither: a pane you shoot yourself still opens its case? |
| L2 | same round | after at most 45 s they cross the mall to the watch shop (-1892, 500, 2593) and its panes go; then the way out; at the car they stand BESIDE its road, round (-506, 0, -8467) - picture when the car arrives: does it stop where it stopped without bots |
| L3 | `y_loot2\M03` | the bots run to the sunk wall piece, gather at (-1706, 220, -899), then hop down into the street one after another (a fall animation, about 2 m forward) and run east on the south side. FAIL = they stand at the gather place: then walk past them into the street - they must vanish when the car waits (the fall-back box). klbot: stage 3 for the bots only if they crossed |
| L4 | `y_loot2\M01` | after the diner (at most 30 s) the bots leave by the back door and go for the Senator at (3384, 0, 19894); **the car's countdown does NOT start when they or you step out of the back door**; it starts when the first of you passes x 4600 toward the car. klbot: money of the bots that stood at the Senator |
| L5 | `y_loot2\M06` | they stop at each of the four (US boss first, right after the bridge house trigger) and move on after at most 20 s each |
| L6 | every map | does a bot that is still at a loot place when the car waits get aboard (ZLootTactic stops at stage 3 + car there; a bot with stage 1 or 2 keeps looting) |

### 12.8 ASSUMPTIONS and guesses of this section

- That 'Activate' on a `HavokShatterGlass` looks like a shot pane (read: the same two routines; not seen), and
  that a relay's message from a `ZBoxPrimitive` of the squad reaches a ZSTDOBJ in a room (F01's relay reaches
  ZGROUP cases the same way).
- The unit of the container's countdown (field 4 = 10): if it is seconds, the first jewel can be taken 10 s after
  the glass - inside the 45 s.
- That a drop link of 232 across works as stock's widest (228); that a link written by hand needs nothing but the
  arrays the two parsers read (0x63e750) - the 21 stock meshes' rules hold, the game has not loaded it.
- That an AI actor triggers the level exit box as BOT1 / BOT2 showed on M01 - now relied on for M03's street too.
- GUESS values: `STOP_SHARE` 10 %, `STOP_MAX` 4, `CASE_BOTS` 3, `CASE_DELAY` 1.0 s, loot waits 30 / 45 / 20 / 20 s,
  `LANE_CLEAR` 250, `GATE_BACK` 140, the cut lines x 2400 / 4600.
- That fewer than seven bots at a stop do not matter to the others: every squad has its own chain and waits.

### 12.9 Changes in `tools/kl_fa_bots.py`

`Nav(links=)` (walks links one way), `border_points`, `add_drop`, `prepare` (the two edits of existing data, made
before the plan), `lanes` / `lane_dist`, `plan` (stops, the order of the stops and of EXITS_BANK among them, cases,
the gather place, the road), `make` (one chain for any number of stops), `check` (the last loot wait counts for
the early call; relays; the shut-case rule; `links`), `diff` (allows exactly the plan's cut boxes and drop link),
`guns_entries`, `owner`, options `--stops --cases --exit-boxes --drop --lane`. `EXIT_CUT`, `DROPS`, `RECIPE` are
the three tables a map is described by. No other file of the repository was changed.

Scripts of this section (`<work>\research\agent_scripts\p-loot\`; they read, they write nothing but their own
logs): `verify.py` (the builds read anew: references, chains, cases, exit boxes, the mesh and a flood over it),
`lanes.py` (12.5), `links*.py` / `wp.py` (the stock links and waypoints), `anm1.py` (the clips), `st*.py` (stock
containers, glass, exit triggers, timers, relays, squad transitions), `msgtab.py` (message names of kl2.exe),
`rt_compat.py` (Retomoto's plan with the old and the new module).

## 13. The bots and the key-framed van in one build (2026-10-10 night; defects D3, D4 of `re/play_fixes_review.md`)

OFFLINE; nothing installed, the game not started. Builds `<work>\build\z_final\M01 M02 M03` (van + guns + camera +
enemies + bots; M06 = `y_loot2\M06` unchanged). The van itself: `re/map_escape.md` part 3. **Not run in the game.**

### 13.1 What was wrong

- **D3.** `lanes()` read `OnlineEscHavokCar` splines only. On a van build it found nothing, `--lane` did nothing,
  and the note of the van job said `--park` = the van's boarding box at the stop - a point ON the van's line, 337
  behind its origin, where its nose (with a `KillBox`) passes on the way in. Bots stood 2 .. 25 from the line on
  all three maps and every checker passed.
- **D4.** With the bots ending in a box at the street, M03 lost its only fall-back box at the gather place in front
  of the drop. The drop link is one way and hand-written; whether the AI takes it was never seen.
- 12.2 'the boarding action is in box 02' and 12.5's table are about the SPLINE car. On a van build the boarding
  action (`...\V_Van_00\BoardingTrigger`) rides on the van and lies at the WAITING place in the file.

### 13.2 What `tools/kl_fa_bots.py` does now

- `van_drives(B)`: every `OnlineEscAnimatedVehicle` of the build, decoded with `kl_map_escape.VanKeys`: the line of
  its position keys from the first frame of the drive in to the last of the drive away (382 keys on these maps),
  the waiting place, the stop, the end, where the boarding box stands while the van is at the stop, the seconds.
- `lanes(B)`: that line for a van, the splines for a car (as before).
- `plan()`, a build with ONE van, no option needed: the lane is always kept; the boarding place of the plan is
  the box's place AT THE STOP; the bots end in an `AllyEscapeBox` whose middle is `PARK_SIDE` = 420 from the line,
  within `PARK_REACH` = 900 of that box and with `CLEAR` to the mesh's edges, chosen by 'path from the last loot
  stop + 3 x distance to the box' (the side the bots come from). The seven places inside the box keep
  `LANE_CLEAR` = 250 from the line (D3 b). Way-out places and the stage place are taken on the side of the road
  the bots are on when one exists there (new; also for a spline car with `--lane`). `--park x,y,z` still wins.
- D4: the gather place in front of every one-way drop gets a box of its own when the bots end in another box
  (`P['ally_more']`, node `Gameplay!merc_bot_squad!AllyEscapeBox_02`). Stock F02 / F06 have eight boxes each.
- `check()`:
  - FAIL: a place of the way out (after the last loot wait) or a last place nearer than `LANE_HALF` + `LANE_MAN`
    = 100 + 60 to the vehicle's line - van or spline car;
  - FAIL: a place beyond a one-way drop link whose place before it is in no `AllyEscapeBox` (when the build has one);
  - NOTE: two places that follow one another lie on different sides of the line (the bot has to cross);
  - printed, not a finding: the stand-in path (through the middles of polygon edges) touches the line between two
    places of the same side. Where the game's pathfinder walks between two places was not read.
- Controls (run; scratch folders, removed): the notes' recipe on `z_final\_van\M01` (`--park` = the box, no lane)
  -> **12 FAIL** (places 7 .. 107 from the line); M03 with the one box at the street -> **7 FAIL**;
  `t_maps2\M01` without options still gives the archive of `u_maps\M01` byte for byte (sha1 `4ea0322d59cf`) -
  and that played build now FAILS the check (6: places 4 .. 83 from the car's route; the bots in the road of 12.5).
  `y_loot2\M01..M06` and `v_rtbots\retomoto_bots` still PASS.

### 13.3 Where the bots stand and board (world units; the van's line = `van_drives`)

| | the bot that calls the van | the seven end at | from the van's line | from its boarding box at the stop | boxes |
|---|---|---|---|---|---|
| M01 | first into `Triggers!CallExitVehicle_02` (x 4600..8796 after the cut), stage place round (5738, 0, 20020) | round (6004, 0, 20211): x 5892..6072, z 20099..20279 | box middle 457; every way-out place 254 .. 420 | 505 from (6164, 0, 20691) | `AllyEscapeBox` (6004, 200, 20211) |
| M02 | first into `Triggers!ExitTrigger_01` (120 x 80 m round the car park), stage place round (-523, 0, -8437) | round (-821, 0, -8400): x -934..-754, z -8512..-8332 | 423; places 250 .. 402 | 377 from (-621, 0, -8719) | `AllyEscapeBox` (-821, 200, -8400) |
| M03 | first to land in the street: `Triggers!ExitTrigger_01` is 80 x 20 m and begins at z -540, the drop lands at (-1700, 150, -534); stage place round (854, 71, -155) | round (2210, 16, -320): x 2098..2278, z -388..-208, the south side of the street | 431; places 250 .. 339 | 840 from (2970, 0, 39): nothing nearer has 420 to the line on that side | `AllyEscapeBox` (2210, 216, -320) and `AllyEscapeBox_02` (-1707, 420, -900) at the gather place in the yard |

All boxes are 350 x 416 x 350 (half sizes), never hidden. Boarding: a bot with crew status 0 inside a box is
taken aboard while the vehicle is in state 3 / 4 = standing at the stop (kl2 0x907a50); **the bots vanish in the
box, they do not walk to the van's doors** (on `u_maps` M01 / M02 they walked to the car through the tactic).
Whether `ZBoardEscapeVehicleTactic` would take a boarding box that arrives with a van was not read.
M03: the van comes down the street from the west, BEHIND the bots that have dropped; they keep the south side
(250+). Bots still in the yard box when the van stands are taken aboard from the yard.

### 13.4 Sizes and checks

The bot step adds nothing to the four blocks (as before). Entities added: 170 / 289 / 199 (M03: one more box).
Tables of the final folders: `re/map_escape.md` 16. `kl_fa_bots.py diff z_final\_van\M0x z_final\M0x`: only the
squad was added (+ M01: 2 exit boxes cut; + M03: 1 drop link).

### 13.5 Live checks (the lead's; after L0..L5 of 12.7 and V0..V6 of `re/map_escape.md` 13)

| # | run | what proves it |
|---|---|---|
| J1 | `z_final\M02`, do nothing, watch the car park | the bots come out, gather round (-821, 0, -8400) west of where the van stops; the van arrives through nobody; the seven are gone when it stands |
| J2 | `z_final\M01` | the same round (6004, 0, 20211); the car's countdown still starts only past x 4600 (L4) |
| J3 | `z_final\M03` | L3 with the van: the bots hop down and run east on the south side to (2210, 16, -320). If they do NOT hop: they stand round (-1707, 220, -900) and must vanish when YOU have called the van and it stands |
| J4 | any | F4 of `re/map_escape.md` 18: left behind with the bots gone - the clock, the same van again |

### 13.6 ASSUMPTIONS and guesses of this section

- `LANE_MAN` 60, `PARK_SIDE` 420, `PARK_REACH` 900, `PARK_NEAR` 3: GUESSES.
- That a key-framed van hurts an actor it drives through (`KillBox` 'CheckInsideEnter', 'FA_DieFromSelf': not read
  for AI actors); the places are kept off the line either way.
- That an `AllyEscapeBox` 4 .. 8 m from the van takes bots aboard as F02's boxes at the helicopter do: 0x907a50 has
  no distance test (12.3 / `re/bots_behaviour.md` 2.3); the M06 and `u_maps\M03` boxes were built on the same reading.
- The round is short with bots: the first bot in an exit box calls the van; it stands 7.2 s later and leaves after
  8 s whether the human is there or not (`re/map_escape.md` 17). Not changed here.

### 13.7 Changes in `tools/kl_fa_bots.py`

`van_drives`, `lanes` (the van), `_crosses`, `plan` (the van's boarding place and park place, the lane for a van,
the same side of the road, `ally_more`), `make` (several boxes), `check` (the two FAILs, the NOTE, `facts['lane']`,
`facts['van']`), constants `LANE_HALF LANE_MAN PARK_SIDE PARK_REACH PARK_NEAR`. Also `tools/kl_escape.py`
(`cut_collision`: the smallest filler, packed; `smallest_static`, `pack_fillers`, `shares`) and
`tools/kl_map_escape.py` (`van_check`: the .HVK's size and shares). No other file of the repository was changed.
