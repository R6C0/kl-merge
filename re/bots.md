# AI heisters on the Dead Men maps: what was built, the routes, the owner's four behaviours

2026-10-10, agent b-build. Tool: `tools/kl_fa_bots.py` (its docstring is the spec of the data). Built on
`re/bots_squad.md`, `re/bots_behaviour.md`, `re/bots_voice.md`. **OFFLINE: the game was not started, nothing was
installed, nothing was written into the Dog Days folder.** Every statement about what a bot DOES is read in kl2.exe
by those notes or is an ASSUMPTION marked as such; no bot of these builds has been seen in the game.

Owner, 2026-10-10: *'continue the ai heisters ... make sure the voicelines for the characters are there too and the ai
have better interactions because in the current game they arent the best, want them to be able to backstab you and
also pay the driver and leave without you or blow the van up or help you up'*.

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
