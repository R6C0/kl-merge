# Campaign levels as Fragile Alliance maps: what the TOOLS can do today

2026-10-11, agent `tooling` of the campaign-FA study (the owner: "look into making the specific campaign maps
more FA orientated from dead men: the bank map but the campaign way, the club map, hasta / cuba & probably
walk in the park perhaps prison too"). Five other agents study the five places; this file is what they share:
how a campaign level becomes a Fragile Alliance map with the tools of this repo, and what is missing to do it
five times without writing five Retomotos.

OFFLINE. Nothing was installed, the game was not started, no existing file was edited, nothing was committed.
Scratch scripts and their outputs: `G:/kl_scratch/cfa_tooling/`. Trial builds (result.json + log.txt kept, every
archive deleted): `<work>/build/cfa/tooling/`.

Evidence labels: **MEASURED** = output I produced (command or script named), **READ** = code or a note (file and
place), **ASSUMED** = says why. **GUESS** = a value nobody measured. Line numbers are of the working tree at
2026-10-11 06:10; three other sessions were editing tools/ while this was written (kl_fa_bots_dyn.py moved by 320
lines between two of my greps), so go by the quoted names.

## 0. Short answers

1. **Verdict: feasible-with-work. The tools are NOT ready to author a new campaign map without new tool code.**
   What exists is a complete, live-proven pipeline for ONE campaign map (Retomoto) plus generic finishing steps.
   The authoring step itself is 3,400 lines in four modules that are Retomoto from the first constant
   (`kl_fa_author.py` 1,160, `kl_fa_street.py` 1,161, `kl_fa_blast.py` 780, `kl_fa_van.py` 289), wired into
   `kl_graft.build` and `kl_maps.one` by name. (READ, section 1.)
2. **Four tool faults stop campaign levels BEFORE any authoring** (MEASURED, section 7):
   - **the .prm chunk table.** `kl_graft` appends the map's chunks behind F07's 35,101. The game's table has
     73,728 entries, the tools allow 69,632. F07 + M08_A = 79,005, F07 + M11_B = 74,454, F07 + M11_A = 72,573,
     the two Havana levels in one map = 111,853, the two bank levels = 79,344 (sum of two measured builds).
     Only M03_A (64,871), M06_A (53,960), M03_B (49,645) and M05_A (52,935) fit as built.
     `kl_chars.py compact` (exists, proven offline, NEVER LOADED IN THE GAME) takes the prison from 79,005 to
     50,617 with `kl_impact` 0 problems; it cannot save Havana A + B in one map (about 83,500 live entries).
     F07 is also the largest systems level there is (35,102 entries; F05 17,601, F08 27,016): another host is
     a further way out, but every authoring tool names F07's objects (5.1).
   - **the club does not convert at all**: `kl_mat.convert_mat_full` refuses M05_A (`TEXT/TILU value
     b'MIRRORED' never occurs in Dog Days`, tools/kl_mat.py 396-397). Six materials; of the 20 Dead Men levels
     only M01_A and M05_A have it. (corrected by the second agent: it is ONE material - slot 538
     `Concrete_Walkway_01a_M05`, three texture stages; M01_A also one. MEASURED `G:/kl_scratch/cfa_tooling_v2/mat3.py`;
     section 11.2.)
   - **the campaign pre-pass throws the cover list away on M03_A and M06_A** (it lives in a campaign subtree
     there: `Special!CoverList`, `Specials!CoverPoints!CoverControl`). The built F07 + M06_A has 0
     `FFCoverList` and 225 cover boxes that nothing registers; `kl_graft.verify` does not notice (it only
     fails on MORE than one).
   - **the navigation converter drops every link that is not a drop** (kinds 1, 3, 6): 16 of M03_A's 30 links,
     42 of M08_A's 80, 36 of M06_A's 67. On M03_A and M11_B two large parts of the mesh are then joined by
     nothing, for the police, the guards and the seven AI heisters alike (Retomoto's tower has the same split
     and its round simply stays on one part). (added by the second agent: on all three it is the campaign's
     RAPPEL - kind 6, 10 - 44 m straight down - that joins the parts; no climb or leap link joins two large
     parts anywhere. MEASURED `nav3.py`; see 5.3.)
3. **What IS generic and has run in the game** (READ CLAUDE.md 'Open work') and needs only data: the graft
   itself, the campaign pre-pass, two levels in one map (`chain`), `lighten`, the wardrobe, gun looks, the AI
   heisters (`kl_fa_bots` - it derives its whole route from the level's own trigger boxes and navigation mesh -
   and `kl_fa_bots_dyn`), Bain, the hook's side files KLJoin.ini [Join], KLTalk.ini, KLGuns.ini,
   KLWardrobe.ini, the menu page latch (page 2). Generic but NOT yet seen working live: `kl_fa_cover`,
   [CrewJoin] (bots through a join), [CrewHop], pages 3..9.
4. **The one new tool** (section 3) is smaller than it sounds because the two hard pieces exist: a writer that
   CLONES stock objects into a finished build (`kl_fa_bots.Maker` + `apply`, live on five maps) and a van
   whose drive can be laid on any curve (`kl_map_escape.van_prepare`; seen driving on Hot Coffee and on
   Withdrawal). What has to be
   written is the layer between: one data file per map, a generic `prepare_host` / `wire` that reads it, and a
   van plan from designer way points (today the plan is read off a Dead Men FA spline car, which no campaign
   level has).
5. **Slots**: page 2 has one free entry (F07); five more maps need page 3. The hook (pages 2..9) and
   `mkoverlay.py` (pages 2..5) take a third page as ini data, but the Arcade page has room for FOUR added
   buttons and Heister + Guns + page 2 use three: page 3 is the last that fits. `kl_expansion.py` has ONE page
   hard-coded (`PAGE = 2`, a dozen uses): tool work, no hook work. Dead Men's menu scene holds a picture for every
   campaign chapter (`LevelPicture_M03A M03B M05 M06 M08 M11A M11B`): pictures are data.
6. **Effort relative to Retomoto (= 1.0)**: the tool work that makes the next maps data-driven is about 0.6 of
   a Retomoto, once. After it a single-level map is about 0.25 - 0.4 each (data file + live rounds), a
   two-part map 0.5. Without it every map is 0.7 - 1.0. Why: section 6.

## 1. The Retomoto pipeline as it is built today

MEASURED from the build that is on the owner's tab: `<work>/build/rt_full7_bots.log` ("kl_fa_bots_rt build
.../rt_full6/1_guns -> .../rt_full7/2_bots"), `rt_full7_talk.log` ("written .../rt_full7/3_talk"),
`rt_full7_bain.log` ("kl_bain: .../3_talk -> .../retomoto_full"), and the folder `rt_full7/retomoto_full`
(F01_Main.zip 218.9 MB, KLJoin.ini, KLTalk.ini, KLGuns.ini, KLWardrobe.ini). The rest is READ from the code.

| # | step | command / entry point | what is Retomoto-specific | what is generic |
|---|---|---|---|---|
| 1 | two campaign archives -> one level | `kl_maps.py chain <out> F07 M09_B M09_A --author` -> `kl_maps.chain` (474-488), `one` (359-471), `kl_graft.build` twice | the pseudo level name `R09` (kl_maps 478-481); `HERO_AT` holds markers for M09_A / M09_B only (103-104), so `--heroes` does nothing on any other level; `one()` imports `kl_fa_author` when `author` is set (439-442) | `campaign_drop` (122-153: no level name in it), `redirect`, `nav_join` (238-289), all of `kl_graft.build` |
| 2 | the graft takes an authored layer | `kl_graft.build(author=True)` (1044-1045) | `import kl_fa_author as au` and five calls by name: `au.prepare_host(S)` if `s_name == au.HOST`, `au.strip(M)`, `au.KEEP` / `au.DROP` into the selection, `au.layer_names`, `au.wire(Jn)` once `au.complete(Jn)` (1075-1080, 1087-1090, 1173-1175) | the hook POINTS are right for any map: before `picks_of` (place and value edits on the stock S), per Dead Men part before the join (strip), after `kl_fa.repair` on the joined scene (wire) |
| 3 | the layer: tower | `tools/kl_fa_author.py` | `HOST, PART_B, PART_A` (79); every table: `START TRAITOR POLICE STAGE_B/C/D SPAWN STATUES MAIN_ROOM` (112-151), `PLACE` 39 entries (194-246), `PARKED`, `ROLE` = 14 F07 objects given a new job (251-262), `BLAST STEPS CAMPAIGN_KEEP QUIET WINDOW_PRE SQUADS ROOM_*` (310-398), `JOIN_BOX JOIN_ENTRY VAN_STOP_Z ROAD_X` (176-190); `wire()` (668-826) is one script of this level's lists; `ledge()` (890-979) | `rot9 look9 node_of setv ctrl_of place` (404-478); `van_path van_fit` (481-518); the spawn-point loop by kind (549-566) and the pool-stack -> loot conversion (567-590) inside `prepare_host`; `squad_plan` (608-642, but for the `SQUADS` prefix table); `strip` (829-845); `layer_names`; `inventory` (981-1051); `move_hero` (1053-1078) |
| 4 | the layer: street | `tools/kl_fa_street.py`, patched into kl_fa_author by `hook()` (790-818) | `SQUADS` (98-120: 14 F07 police squads -> anchors on M09_B's road), `RING`, `BOXES` (143-), `DYN_PLACE`, `COVER_PLACE`, `BOUNDS` (303-), `ROAD LANE DOOR PLAY START` (78-83), `ELEVATOR` | `Nav` (311-415: polygons, neighbours, `floor`, `put`, `nearest`, `reach` - but its `PLAY` filter is the road's box); `placed` / `layout` / `starters` / `relay` (429-532: move ONE F07 police squad rigidly to an anchor and put every point on the map's mesh); `put_world` (689-724) |
| 5 | the layer: van | `tools/kl_fa_van.py` `straighten` (100-181), `clear_props` (183) | one straight line north: `LANE_X STOP_Z WAIT_Z END_Z` (52-67), `PROPS_OFF` (two named M09_B objects) | nothing a curved road can use: every rotation key becomes the identity. The generic form is `kl_map_escape.van_prepare` (row 12) |
| 6 | the layer: opening | `tools/kl_fa_blast.py`, `hook()` (398-415) | `PLAN` (141-148: six spare F07 boxes at the window), `GLASS_X BAY`, `BOMB INVISIBOMB` | the idea and the forms: `Explode` + `ShakeCamera` cloned token for token from F07's rocket, `DocuCamControl 'OnExplosion'` (stock F01's), the systems' explosion clusters; `dress docucam scrub selftest` |
| 7 | loot props (on the WRITTEN level) | `kl_fa_loot.finish` through `kl_fa_author.FINISH` (969-981) | `TABLE = 'PC0200_M09_ConferenceTable_A_01'` (446), `STATUE` / `SUIT` (456-458), `TOWER WALKED` (246-251) | `survey` (268: can every loot object be reached - the pick-up test read at kl2 0x783e60), `Floors`, `Edit`, `case_model` (639: a prop model of ANOTHER level into dead chunk indices: `CASES` 432), `picture`, `props` |
| 8 | weight | `kl_graft.relight(folder, out, 'trim,slim')` = `kl_graft.py lighten` (680-716) | - | all of it. MEASURED on the prison trial: .TEX 421.4 -> 231.1 MB, archive 329.3 -> 192.4 MB |
| 9 | the wardrobe | `kl_chars.py wardrobe <light> <final> [--plates=...]` (958-1105) -> KLWardrobe.ini | - | all of it (it takes the Dead Men heroes from M01_FA_A, `level='M01_FA_A'`) |
| - | rows 1 - 9 in one command | `python tools/kl_fa_loot.py test <out>` (983-1012: `kl_fa_blast.test` -> `relight` -> wardrobe -> `final_checks`; it copies `klhook/KLJoin.retomoto.ini`) | the command | - |
| 10 | weapons and soldier rows | inside `kl_graft.build` (`arms=True`, 1165-1168) -> `kl_arms.arm` | `LEVEL_DEPTH` (121), `FORCE` (126-131: six tower squads by name), **`SKILL_LEVELS = ('M09_A', 'M09_B')` (161): the stock soldier rows ("why do I survive being shot so much") are written on these two levels only** | the class -> pool table, `MIX`, `ROWS`; a map that is not listed gets `DEPTH_DEFAULT` and Dead Men's own soldier numbers |
| 11 | gun looks | `kl_map_guns.py build <folder> <out>` (858) -> KLGuns.ini | - | all of it (`BUILDS`, line 83, only feeds the `all` command) |
| 12 | (the four FA maps only, not Retomoto) escape van, cameras | `kl_map_escape.py van` (`van_plan` 1064, `van_prepare` 1309, `van_wire` 1439, `van_hvk` 1483, `van_check` 1571) | `VAN_TAGS = ('M01', 'M02', 'M03')` (686); **`van_plan` needs ONE Dead Men escape car with two spline routes (1075-1077) - the road Dead Men's designers drew** | `van_prepare(S, P)`: F07's first van laid on ANY plan P (position and rotation keys rewritten in place, boarding box, cameras, path blocker); `lane` (collision in the van's way), `Ground`, `van_check` |
| 13 | (the four FA maps only) enemies | `kl_map_ai.py apply` (781) | `TAGS` (112) | **`PLANS` (166-287) is already a per-map DATA table** (arms / unleash / timers / counters / start / chains / escape) with a generic applier and its own fault rules; `apply` raises for a map without a plan (787-788) |
| 14 | AI heisters | `kl_fa_bots_rt.py build <folder> <out>` (two-part map) on top of `kl_fa_bots.plan / make / apply` (1312, 2091, 2226) | `kl_fa_bots_rt` imports `kl_fa_author`, `kl_fa_van`, `kl_fa_street` and takes `JOIN_NAME BLAST_TIMER ROOM_COUNTER` from `au.ROLE` (61-80); it writes [CrewJoin] | **`kl_fa_bots` itself is generic**: stations = START row -> ENTERS_BANK box -> loot -> EXITS_BANK -> level exit -> boarding, found in the level and joined over its navigation mesh (docstring 'HOW THE ROUTE IS PLANNED'). Per-map tables: `RECIPE` (258), `EXIT_CUT` (223), `DROPS` (233), keyed by level name, with defaults |
| 15 | dynamic bots, cover, routes | `kl_fa_cover.py build`, then `kl_fa_bots_dyn.py build` | - (corrected by the second agent: on a map whose bots have two chains - any two-part map - `kl_fa_bots_dyn` imports `kl_fa_bots_rt` for 'its lane, its checks' (READ kl_fa_bots_dyn.py, `self.rt = RT` in the planner's `__init__`), and that module is Retomoto's: so for a two-part bank this row is NOT generic) | all of it; `OWNER` / `ROUTE` only name the delivered folders |
| 16 | talk | `kl_fa_talk.py build <folder> <out> --map retomoto` (564) -> KLTalk.ini, .SND/.WAV/.LOC | `SCRIPTS['retomoto']` (83-: 13 scenes with boxes `RT_ROOM RT_RECEPTION RT_STREET RT_ROAD`), `BLAST_TIMER` | **`SCRIPTS` is a per-map data table** (source level, scenes: when / needs / lines); entries exist for M01 M02 M03 M06 from the campaign levels M01_A M02_A M03_A M06_A; the chatter `POOLS` (160-) are map-free |
| 17 | Bain | `kl_bain.py build <src> <dst>` (651) -> its own PC_Def.str | default folders (74-75) | all of it: `TABLE` (91-) maps settings FIELDS to Bain clips |
| 18 | stream file | `kl_str.py build [levels]` / `kl_fa_talk.py stream` / `kl_bain` | `LEVELS` (116: the six maps), `MUSIC` (636-645: M09_A, M09_B) | `need`, `merge` (append only), `set_fa_music` (665: settings field 157) |
| 19 | the tab | `kl_expansion.py build --prebuilt DM09=<folder>` -> `adopt` (319-361) renames the archive to its slot; `install` | `MAPS` (118-137: five entries), `PAGE = 2` (90), `JOIN_NAME`, `join_ini()` (223-244) imports `kl_fa_author` | `adopt`, `SIDE` (94), `map_pictures` (811), `install` / `uninstall` |
| 20 | the hook's side files | beside the archive: KLJoin.ini (`kljoin.c` [Join], up to 8 boxes; `klcrew_rt.c` [CrewJoin]; `klhop.c` [CrewHop]), KLTalk.ini (`kltalk.c`), KLGuns.ini (`klgun.c`), KLWardrobe.ini (`klchar.c`) | the VALUES | every reader takes whatever level the file lies beside (READ klhook/kljoin.c 1-75: "A box is only active on its own level"; kl_expansion.SIDE) |

What the table says: **rows 1, 8, 9, 11, 14 (without `_rt`), 15, 17, 20 run on a new map as they are; rows 10,
13, 16, 18, 19 need an ENTRY in a table that sits inside a tool; rows 2 - 7 and 12's plan are the authoring and
are Retomoto.** `kl_fa_author`'s own rule "no new entity, no new controller - every object is a stock one,
re-placed and re-wired" (READ kl_fa_author.py 42) is what made it a one-off: the layer is written around
which fourteen F07 objects happened to be free (`ROLE`: the bomb's timer is F07's `RivalMercVan!TimerVanGo`).
Since then `kl_fa_bots` appends entities to finished builds (row 14) and those builds loaded and played on all
five maps (READ CLAUDE.md, 'LOADS + ROUNDS: all five route builds load and play 4 min'), so that rule is no
longer needed.

## 2. What a Fragile Alliance layer needs

To LOAD (a direct boot) a campaign graft needs nothing of the layer: READ re/maps.md 4.4, and seen live on
M09_A / M09_B. For a ROUND, from `kl_fa.check` (tools/kl_fa.py 185-416), re/fa_gamemode.md 3 and the census of
stock F07 (MEASURED: `G:/kl_scratch/cfa_tooling/globals.txt`, 'STOCK F07: the layer by top-level family'):

| # | object | class + controller, the fields that matter | without it (kl_fa.check) | where it comes from |
|---|---|---|---|---|
| 1 | settings | `ZOnlineGameplaySettings` + `OnlineFragileAllianceSettings`, 340 fields; per map: 17..20 briefing, 127 / 130 reach / leave loot, 136 / 137 reminder, 157 music (a sound of the merged bank) | CRASH `settings` (kl2 0x500990, 0x728ba3) | **S brings it**: `FASpecials!Settings!GameSettings`; keep by name. Values per map are data |
| 2 | multiplayer define | `ZSetZDefine` 'IsMultiplayerLevel' | BROKEN `define` | **S brings it**: `FASpecials!Settings!IsMultiplayerLevel` |
| 3 | 16 players | `ZFFPlayer` `Heroes!Hero_01..08`, `Heroes!Henchmen_01..08` (ZGEOM[1] by `look9`: a player looks along local -Z) | BROKEN `players` | S brings them always (systems side); **must be placed** (a direct boot starts at Hero_01) |
| 4 | spawn points | `ZSpawnPoint`, property 8 = kind; 8 START, 7 AFTER_DEATH, 4 TRAITOR (F07 also 44 of the UCC / TEAM kinds); ZGEOM[1] by `rot9` (+Z) | BROKEN `spawn` (START < 8, no AFTER_DEATH); DEGRADED without TRAITOR / the other modes | S brings 63 (`FASpecials!SpawnPoint!*`); **must be placed per map** |
| 5 | stage triggers | `OnlineGamePlayTrigger` on a `ZBoxPrimitive` (half extents): `eOGPT_PLAYER_ENTERS_BANK`, `..._EXITS_BANK`, `..._BOARDS` | BROKEN `gameplay-trigger`; and the AI heisters get their heist stage from standing INSIDE these boxes (READ kl_fa_bots.py docstring) | S brings ENTERS / EXITS (`FASpecials!PIP!*`), **place per map**; BOARDS rides in each van |
| 6 | loot | `OnlineMoneyCtrl` (0 game mode, 1 value, 2 `ZMONEYCTRL_TYPE_NORMAL` / `_CONTAINER`) + `TriggerBox2` on the same node (field 2 = reach; pick-up at radius + 40) | BROKEN `money` | F07's five NORMAL objects leave with its map. **Per map**: pool stacks re-typed and placed (kl_fa_author 567-590) or cloned; props by `kl_fa_loot` |
| 7 | drop pool | `OnlineMoneyCtrl` `ZMONEYCTRL_TYPE_DROP` x 108 + 25 | BROKEN `money` (no DROP) | **S brings it** (`FASpecials!DropMoney!*`), position-free |
| 8 | exit trigger | `OnlineExitLevelTrigger` on a box; fields 2..5 = up to four vehicles (all empty = a hang at kl2 0x6c3f90) | BROKEN `exit-trigger`; CRASH if all four are empty | S brings `Gameplay!EscapeSetup!otrExitLevel`; **place and wire per map** |
| 9 | vehicle monitor | `OnlineEscVehicleMonitor`, exactly one | CRASH `monitor` (kl2 0x6276fc) | **S brings it** (`kl_fa.host_keep`) |
| 10 | escape vehicle | `Animation/F07/F07_Escape_Vehicle_0n.zip`: `ZAnimatedVehicle` + `OnlineEscAnimatedVehicle`, boarding `PlayerAction`, BOARDS trigger, cameras, `KillBox`, `PathBlocker` (223 entities each) | BROKEN `vehicle` | S brings three; **the drive must be laid on the map** (its keys rewritten) and the exit trigger pointed at it |
| 11 | round-start hub | `AIMonitor` list 2 | DEGRADED `ai-monitor` | **S brings it** (`Gameplay!AIMonitor`, host_keep); **wire per map** (opening, squads, bots, music) |
| 12 | briefing, speakers | `FAMissionBriefingTrigger` + its timer; `ZSpeakerDriver / TeamCriminals / TeamPolice` | DEGRADED | **S brings them** (host_keep) |
| 13 | enemies | `ZGROUP` + `ZSquadScript` (field 0 attitude, 3 active from the start, 8 'wiped out' list), actors `ZFFActor` + `ZSoldier`, behaviour routs; something must NAME a rout to start a squad | BROKEN `squads` (none); DEGRADED (squads nothing names) | **per map**: the campaign's own squads (`squad_plan`) and / or F07's 14 police squads re-laid (`kl_fa_street.relay`); starters wired per map |
| 14 | level bounds | `LevelBound` box + two warn boxes | DEGRADED `bounds` | the campaign's own stay when they are script-free (pre-pass `PASSIVE`); S has 6 to **place** |
| 15 | cover list | `FFCoverList` on a `ZLIST`, EXACTLY one (a second asserts at kl2 0x6682c5); every `*coverbox*` object becomes a cover at load | **nothing reports a level with none** (section 5.5) | the map's top-level `CoverList`, or S's `Specials!CoverPoints!CoverControl` when the map has none |
| 16 | HUD markers | 2 `PointOfInterest` + `ActivateGameplayTrackerDisplay`, their trigger boxes (`FASpecials!POI!*`, 14 nodes) | DEGRADED `markers` | S brings; **place** |
| 17 | spawn cameras, team stages | `CCameraBox` under `ZSetZDefine MercSpawnCam*`; `OnlineSpawnpointTrigger` x3 | NOTE / DEGRADED (other modes) | S brings; **place** (all GUESSES on Retomoto) |
| 18 | join of two parts | `JumpPoint` entries + the hook's box (KLJoin.ini); **no object may name a JumpPoint** | CRASH `jump-point` (kl2 0x8f40c9) | S brings 6 JumpPoints to place; the box is data for the hook |
| 19 | AI heisters | `Gameplay!merc_bot_squad!*` (7 squads of one `ZFFActor`), `TriggerLootDepleted` | DEGRADED `bots` | **derived by `kl_fa_bots`** from rows 4, 5, 6, 8, 10 and the mesh |

So of 19 rows S (F07) brings fifteen as objects; what a map needs is PLACES for them (rows 3, 4, 5, 8, 10, 14,
16, 17), loot (6), enemies and their starters (13, 11) and the one decision of row 15. That is the data file.

## 3. One data-driven authoring tool: `tools/kl_fa_campaign.py` (specification; not written)

### 3.1 Shape

Three passes; the first two stand at points the graft already has (section 1 row 2):

- **before the graft, on the stock S** (`prepare(S, data)`): everything F07 already owns and only has to stand
  somewhere - the players, the 63 spawn points, ENTERS / EXITS boxes, the exit box, POI, bounds, cameras, jump
  points, the pool stacks that become loot, the van's drive. This is `kl_fa_author.place()` driven by tables.
- **after the last join, on the joined scene** (`wire(Jn, data)`): reference lists only (`kl_fa.edit`).
- **on the written level** (`finish(folder, data)`): what needs chunk numbers or new entities - loot props
  (`kl_fa_loot.Edit`), and every object S has NO spare of, cloned from a stock form with `kl_fa_bots.Maker`
  and appended with the body of `kl_fa_bots.apply` (entities, cluster table, .oct / .rmi / .rmc slot ids,
  the root's group tree, the .prm record offsets). Then the checks.

`kl_graft.build(author=...)` takes the DATA (or a module with `prepare / strip / keep / drop / wire /
complete`) instead of importing `kl_fa_author`; `kl_maps.one` takes `HERO_AT` from the same data. Those are
the only edits to existing tools that the design forces.

S's objects are found by what they are - a `ZSpawnPoint` of a kind, the node with `OnlineExitLevelTrigger`,
the `ZMONEYCTRL_TYPE_DROP` stacks, the groups with `OnlineEscAnimatedVehicle`, top-level police squads - not
by F07's names, the way `kl_fa.host_keep` finds its seven (kl_fa.py 601-628). Then the systems level is a
line of the data file, which matters for the chunk table (5.1: F07 is the largest base there is).

### 3.2 The per-map data file

A Python literal module (as `kl_map_ai.PLANS`, `kl_fa_talk.SCRIPTS`, `kl_expansion.MAPS` already are), one per
map, e.g. `tools/fa_maps/dm09.py`. Every number carries its source, as `PLACE` does today. Sections:

```python
MAP = dict(id='DM09', title='Retomoto Tower', host='F07', parts=['M09_B', 'M09_A'],   # graft order: street first
           slot='F06', page=2, picture='LevelPicture_M09A')

START = dict(                           # the round starts in the middle of the action
    area='nav',                         # derive: the mesh polygons inside `box`; else an explicit list
    box=((5894, 6102), (21011, 21011), (-975, 780)),          # the balcony's nav area (measured)
    rows=[dict(x=6000, z=(-930, -850, -770, -690, 530, 610, 690, 770))],      # or n=8 and the tool spreads them
    face=(-1, 0), traitor_back=70, keep_out=[((5867, 21094, -66), 600), ((5685, 20997, -394), 300)],
    heroes='start')                     # the 16 player groups: on the START row (a direct boot starts at Hero_01);
                                        # or a campaign marker by name, as kl_maps.HERO_AT has them
POLICE = [(1904, 19601, 818), ...]      # AFTER_DEATH points; or 'actors:<dropped campaign squad>' = its actors' places
OTHER_MODES = dict(team_stages=[..3 lists..], ucc='start+70x')      # optional; default: beside START / POLICE

LOOT = [dict(at='objects:*Samurai*_Whole', value=150000, reach=150, prop=dict(kind='own-mesh', materials=('Fabric_Samurai', 'Textureless'))),
        dict(at='table:PC0200_M09_ConferenceTable_A_01', n=6, rim=33, value=300000, reach=125,
             prop=dict(kind='model', level='M01_FA_A', root=6380, scale=1.25),
             hidden_until=dict(squads_dead='AI_Players!Enemies!020_Office!*'))]
STAGES = dict(enter=dict(box=((5700, 21100, -100), (50, 200, 1250))), leave=dict(box=((5600, 600, -6500), (100, 500, 1650))),
              poi_loot=(4600, 21060, -100))

OPENING = dict(delay=12.5,              # seconds after the round-start event (it comes 8.4 - 8.8 s before GO)
    keep=['WindowBlowup!BombWindow03', 'WindowBlowup!InvisiBomb', ...],         # campaign nodes that stay
    fire=[('Activate', 'WindowBlowup!BombWindow03')], after=4.0,
    then=['AI_Players!Enemies!020_Office!GeomActivator_ChairPost', ..., 'Music!PlayMusic_TokyoAction'],
    force=[('ForceTriggerShotActivate', '<the intact window>')],
    effects=dict(shake=(3.0, 8000), docucam='OnExplosion', clusters=[('FX_Grenade_RPG_01', (5650, 21000, 150)), ...]))

ENEMIES = dict(
    campaign=dict(prefixes={'M09_A': ['AI_Players!Enemies!020_Office!', ...], 'M09_B': ['Enemies!010_RetoBldFront!', 'Enemies!020_Street!']},
                  not_named=('Arriving', 'TakingElevator', 'VSquad'), wait=['AI_Players!Enemies!020_Office!*']),
    steps=['AI_Players!Enemies!040_Atrium_3rd!TriggerBox_EnterAtrium', ...],   # the campaign's own boxes, made ECPS_FA_MERCONLY
    new_steps=[dict(box=((4200, 21200, -100), (60, 250, 1200)), starts='area:AI_Players!Enemies!030_Reception!')],
    host_police=[dict(squad='Gameplay!020_Loot!020_FinancialAlley_LeftParking', wave=1, anchor=(-4100, -2700), face=(0, -1)), ...],
    waves=[dict(box=..., who='ECPS_BOTH', wave=1), ...],
    arms=dict(depth={'M09_A': (0.0, 0.6), 'M09_B': (0.6, 1.0)}, force={...}, rows=True),      # kl_arms
    plan=dict(unleash=[], timers={}, counters={}, start=[], chains={}, escape=[]))            # kl_map_ai.PLANS form

ESCAPE = dict(van=dict(path=[(-1850, 8700), (-1850, 10800), (-1850, 21000)], stop=1, wait=0),  # way points on the road
              exit_box=dict(before=2500, after=2000), props_off=['...PoliceBarricade_02', '...Cars_Qeue_A_01'], one_van=True)
BOUNDS = [dict(box=((6790, 17600, -100), (560, 5700, 2400)), warn=50), ...]     # besides the campaign's own that stay
JOIN = [dict(box=((2550, 2790), (19500, 19800), (800, 1100)), to=(6272, 563, -6305), face=(-1, 0), name='06_Exit',
             open=['AI_Players!Enemies!070_Elevators!AnimProxy_OpenEscapeElevator', 'Mercenaries!VideoProxy!MatPosAnimProxy'],
             on_step='AI_Players!Enemies!070_Elevators!TriggerBox_OpenExitElevator')]
MUSIC = dict(objects=['levelsetup/level/m09_a/music/tokyoaction_v3_44_layer1_loop', ...], start='opening')   # or 'load' = settings 157
LINES = {17: 'Multiplayer/F05/MissionBriefing_03_R', ...}                       # settings field -> key (RT_LINES)
TALK = dict(source='M09_A', scenes=[...])                                       # kl_fa_talk.SCRIPTS form
BOTS = dict(loot_seconds=30, room_first=True, room_wait=75, street_hold=10)     # kl_fa_bots.RECIPE / kl_fa_bots_rt.DEFAULTS form
COVER = 'map'                           # 'map' = the map's own FFCoverList, 'host' = F07's (a map that has none)
```

**The test that the tool reproduces Retomoto**: built from this file it must give the level
`python tools/kl_fa_loot.py test` gives today - compared with `kl_fa_bots.diff`'s method (every node with its
strings spelled out, the scene block, the members' CRC), allowing only the entity order of cloned objects.
Every value above is one of the existing constants (kl_fa_author 79-398, kl_fa_street 78-262, kl_fa_van 50-70,
kl_fa_blast 95-160, kl_fa_loot 432-458, kl_arms 121-131, kl_fa_talk 83-, kl_str 636-645); nothing in it is new.

(corrected by the second agent: the converse does not hold, so the sketch above CANNOT pass that test as it
stands. MEASURED by importing the two modules and counting their tables: these have no section in it -
(a) map nodes re-placed in world space: `ROOM_PLACE` 6, `DYN_PLACE` 15, `COVER_PLACE` 7 (parked buses moved up as
cover), `TRUCK` 3, `BACK_2` 4, `RING` 13 = 48 authored places; (b) free field edits on kept nodes: `QUIET` 2 nodes'
lists emptied, the bomb's two radii (`BLAST_HARMLESS`), `ROOM_RUSH / ROOM_HOLD / ROOM_HIDE` (a modifier set to
eLM_Unleash with its list emptied, one to eDM_Tight, one squad to eStayBack - `plan.unleash` only writes
eUnleashed on a squad) and the campaign timer that is given a NEW target list (`ROOM_TIMER`; `plan.timers` only
sets seconds); (c) 26 of `PLACE`'s 39 entries: 12 spawn cameras, 3 team-mode trigger boxes, 6 jump
points, 5 POI nodes, and the 12 `PARKED` host nodes. Two generic sections close it - `PLACE_MAP = {path: world
place}` (what `kl_fa_street.put_world` does) and `EDIT = [(path, controller, {field: value})]` (what `kl_fa.edit`
does) - but with them the data file is a script in table form, and section 6's 0.6 was estimated without them.
Section 11.3.)

### 3.3 What the tool derives by itself (each from code that exists)

| derived | from | existing code |
|---|---|---|
| spawn points on the mesh, facing, clear of walls, one connected part; the 44 points of the other modes beside them | `START`, the map's converted mesh | `kl_fa_bots.Nav.at / spots / clearance` (357-578), `kl_fa_author.ledge_facts` (869-887) as the pattern of the test |
| every round station on ONE mesh part, in order, one-way drops respected | START, STAGES, LOOT, ESCAPE | `kl_fa_bots.Nav(links=True)` (357-374: array-7 links walked one way; off by default), `stations` (868), `plan` (1312), `kl_maps.stations` |
| can each loot object be picked up (a place to stand within reach) | LOOT + collision | `kl_fa_loot.survey` (268), `Floors` (146) |
| the van's plan from way points: lane free of collision, road height, boarding box, camera sight | `ESCAPE.van.path` | `kl_map_escape.curve / lane / Ground` (773-835), then `van_prepare` (1309) **- `van_plan` itself must be given a second front end (way points instead of a Dead Men car)** |
| which campaign squads can stay, their starter, what to strip | `ENEMIES.campaign` | `kl_fa_author.squad_plan` (608-642), `strip` (829) |
| F07 police on anchors: every cover point and actor on the map's mesh | `ENEMIES.host_police` | `kl_fa_street.relay` (486-532), `Nav.put` |
| cover boxes where a bot wants to hold; the bots' squad, holds, forks | the finished level | `kl_fa_cover`, `kl_fa_bots`, `kl_fa_bots_dyn` as they are |
| HUD markers, exit box round the stop, escape marker | LOOT centroid, the van's stop | kl_fa_author 591-600, kl_fa_street `place_escape` (562) |
| a kill slab / bound where the map is open, and "no spawn point inside a bound" | BOUNDS + START | `kl_map_escape.level_bounds` (356), `ledge_facts` |
| KLJoin.ini [Join] and, for a two-part map, [CrewJoin] | JOIN | `kl_expansion.join_ini` (223), `kl_fa_bots_rt` |
| the inventory and the same RESULT line | the written level | `kl_fa_author.inventory` (981), `kl_fa.check`, `kl_maps.preflight / audit` |

### 3.4 What is lifted unchanged, what is new

- **Unchanged**: `kl_fa_author`: `rot9 look9 node_of setv ctrl_of place`, the spawn loop, the loot conversion,
  `squad_plan`, `strip`, `layer_names`, `inventory`, `move_hero`. `kl_fa_street`: `Nav` (its `PLAY` box becomes
  an argument), `placed layout starters put_world`, and `relay` once the tables it reads as globals (`SQUADS
  LANE BACK_1 BACK_2 TRUCK`) are arguments. `kl_fa_bots`: `Built Nav Maker apply` (apply's body without its two
  squad-specific parts: the `Timer_start_bots` entry in the AIMonitor's list and the group-tree boxes taken
  from `Pos#` children). `kl_map_escape`: `Level Ground Poly curve lane van_prepare van_wire van_hvk van_check`.
  `kl_fa_loot`: `Built Floors survey Edit case_model`. `kl_fa_blast`: `docucam dress scrub` and the three
  cloned controller forms.
- **New code** (in order of size): (1) the interpreter of the data file for `prepare` and `wire` - `wire()` of
  kl_fa_author is 160 lines of one map's lists and has to become rules ("opening fires X", "step box starts the
  squads of area Y", "these squads' wiped-out list -> counter -> hidden loot"); (2) the clone path: an object
  the data asks for and F07 has no spare of (a trigger box, a timer, a counter, an `ActivateGeom`, a kill box,
  a `DocuCamControl`) made with `Maker.clone` and appended; (3) `van_plan` from way points; (4) the checks of
  3.3 as one command; (5) the reproduction test.
- **Edits to existing tools the design forces**: `kl_graft.build` (the five `au.` calls), `kl_maps.one` /
  `HERO_AT`, `kl_fa_bots_rt` (its three `au.ROLE` names), `kl_expansion.join_ini`, and the table entries of
  section 1 rows 10, 13, 16, 18, 19 (or those tools read the data file).

### 3.5 The chain for a new map, and where `compact` has to stand

1. `kl_fa_campaign.py build <out> <id>` = the graft (one level or a chain) with the layer; `verify` problems 0
   (or the chunk-table line alone where 5.1 applies: the build is written all the same).
2. `kl_graft.py lighten <folder> <out> --load trim,slim` - FIRST: it finds the dead textures through the dead
   model roots (READ re/prm_limit.md 'Order matters').
3. only when the chunk table needs it (5.1): `kl_chars.py compact`. It must come BEFORE `kl_map_guns`
   (KLGuns.ini names chunk indices and compact does not rewrite that file; it does rewrite KLWardrobe.ini:
   READ kl_chars.py 562-571 and the command at 1710-1722).
4. `kl_chars.py wardrobe` (15,509 chunks: READ re/maps.md 14.1; into dead indices where there are any, else
   appended). Arithmetic on the measured counts: the prison 50,617 + 15,509 = 66,126; the two-part bank about
   51,000 + 15,509 = 66,500; one Havana chapter about 59,700 / 61,600 - all under 69,632, the first two by
   about 3,300 only, before gun looks (59 - 94 chunks) and loot props (about 20).
   (corrected after the critic, MEASURED in section 12: run the wardrobe BEFORE `compact` - 2,598 entries fewer
   than this arithmetic; the wardrobe with the four mask plates takes 20,989 indices, not 15,509; the gun looks add
   503 entries to a compacted build and 212 to any other. Finished - the round's squads, the host's police / bots /
   vans and the gun looks in - the prison has 65,509 entries with 8 masks and 70,925 with 12 (OVER the tools' line),
   Havana's M11_B 60,902 / 66,318: 12.2 - 12.4.)
5. `kl_map_guns.py build`, `kl_fa_bots.py build` (or the two-part form), `kl_fa_cover.py build`,
   `kl_fa_bots_dyn.py build`, `kl_fa_talk.py build`, `kl_bain.py build` - as on the five maps of the tab.
6. `kl_expansion.py build --prebuilt <id>=<folder>`.

## 4. Slots and the menu

READ klhook/klslot.c, klhook/mkoverlay.py, tools/kl_expansion.py; MEASURED where marked.
MEASURED (the installed `<DD>/KLExpansion/Overlay/Patch01.zip`, read only): the Arcade page has the five stock
buttons + 'Heister' + 'Guns' + 'Dead Men maps' (-> `HeistPlayMenu2`); map pages in the file: `HeistPlayMenu`,
`HeistPlayMenu2`; of mkoverlay's four spare icons `Icon_Options` is the one not yet used.

- **Entries**: entry k of a map page loads slot `{F01, F02, F03, F04, F06, F07, F05, F08, F09}[k]` (kl2
  0x746570; kl_expansion.py 88). F05, F08, F09 are the DLC slots and are never redirected (89). So a page has
  SIX free entries. Page 2 holds DM01 DM02 DM03 DM06 DM09 in F01 F02 F03 F04 F06 (`MAPS`, 118-137): **one entry,
  F07, is free**.
- **The hook takes pages 2..9 as data**: a window named `HeistPlayMenu<N>` on the menu's window stack latches
  page N (klslot.c 234-238: N = '2'..'9'); `[Redirect.N] F0x=<folder under Maps>` is read for every N below
  `KLS_PAGES` = 10 (158, 578-583), at most 64 lines and 16 different slots in all (156-157, 516-527). A second
  page can use F01..F04, F06, F07 again: the redirect is per page and per slot. No hook work for page 3.
  (LIVE so far: page 2 only, slots F01 F02 F03 F04 F06 - READ CLAUDE.md 'TAB_PAGE, TAB_DM09, TAB_DM03 all PASS'
  and the owner's rounds on the tab's five maps.)
- **The menu page is data for `mkoverlay.py`** - it copies the stock window `HeistPlayMenu` once per
  `[Redirect.N]` section, N in 2..5 (122), renames every element with `_P<N>`, sets the titles from
  `[Page.N] F0x=<title>` and the pictures from `F0x.Picture=` (337-347). **But the Arcade page has room for four
  added buttons** (`len(rows) > len(ICONS)` -> exit, 385-386; four spare icons, 100) and three are in use:
  Heister, Guns, 'Dead Men maps'. **Page 3 is the last button that fits.** 6 + 6 entries = twelve maps; a
  thirteenth needs the Arcade page laid out again (or Heister / Guns moved into one page).
- **`kl_expansion.py` knows one page**: `PAGE = 2` (90) is used in `ini_block` (657-669), `menu_check` (709,
  764-771), `overlay_kept` (393-405), `map_pictures` (924), the manifest and the selftest; a `MAPS` entry has
  no page. A second page = a `page` key in `MAPS` and those functions looping over pages. Tool work, no hook
  work.
- **Titles**: literal text on the page (`[Page.N] F0x=`). **Pictures**: `kl_expansion.map_pictures` (811) adds
  one picture entity per map to a copy of the menu scene from Dead Men's own menu picture, named by the `MAPS`
  key `picture`. MEASURED (`globals.py`): Dead Men's frontend scene has 20 `LevelPicture_*` entities, among
  them `LevelPicture_M03A M03B M05 M06 M08 M11A M11B` - every place of this study has one. Data.
- **Briefing**: the page's briefing element is removed from the copy (mkoverlay 341-342: it would print the
  stock map's text); a map page shows NO briefing text. The spoken briefing in the round is settings fields
  17..20 (`RT_LINES` on Retomoto: keys of other stock levels). **Loading screen, lobby title, score-page
  title and the Steam board are the stock slot's** (READ klslot.c 76-81, re/expansion.md 464, 807); the
  hook blocks the upload. Not changeable by data.
- **A map is built for a slot by renaming**: `kl_expansion.adopt` (319-361) writes a finished F01-named build
  under the slot's name, member names and file names only.

## 5. Limits every campaign map meets

### 5.1 The .prm chunk table (the first wall)

READ re/prm_limit.md: one pointer per chunk index in a fixed table of 73,728 entries (kl2 0xeac7b0), shared
with up to 713 run-time chunks seen; the tools enforce 69,632 (`kl_impact.CHUNK_SAFE`); `kl_graft.verify`
calls `kl_impact.chunk_limit` (kl_graft.py 1621).
MEASURED (trial builds, section 7): `kl_graft` appends the map's reachable chunks behind ALL of F07's 35,101
(log line ".prm: N of M chunks of <L> appended to 35101"):

| level | chunks appended | table entries as built | fits 69,632? | after `kl_chars.py compact` |
|---|---:|---:|---|---|
| M09_B + M09_A (Retomoto, for scale) | 17,195 + 10,318 (READ re/maps.md 5.2) | 62,615 as the plain chain; 65,119 with the authored layer's squads (READ re/prm_limit.md); 65,331 on the tab with the gun looks (MEASURED, `rt_full7`) | yes | 50,703 (READ re/prm_limit.md) |
| M03_B | 14,543 | 49,645 | yes | - |
| M05_A (material check bypassed, 7.2) | 17,803 | 52,935 | yes | - |
| M06_A | 18,848 | 53,960 | yes | - |
| M03_A | 29,699 | 64,871 | yes (4,761 spare) | - |
| M11_A | 37,446 | 72,573 ("leave 1155 of the table's 73728 slots") | **no** | about 44,000 (ASSUMED: 28,388 dead as on the prison) |
| M11_B | 39,332 | 74,454 | **no, past the table** | about 46,000 (ASSUMED likewise) |
| M08_A | 43,848 | 79,005 | **no, past the table** | **50,617, MEASURED**, `kl_impact` 0 problems |
| M03_A + M03_B | 44,242 | 79,344 (sum of two builds; the bank agent's chain build: 79,408, READ re/campaign_fa_bank.md) | **no** | about 51,000 (ASSUMED) |
| M11_B + M11_A | 76,706 | **111,853** (chain built) | **no** | about 83,500: **still past the table** |

So: `compact` (`kl_chars.compact_level`, kl_chars.py 562-621) is the step that makes the prison, either Havana
level alone and the two-part bank possible - and it has never been loaded in the game (READ re/prm_limit.md
'Compaction ... offline only, NOT LOADED LIVE': it renumbers the systems level's LIVE chunks, which no build
that ran has done). The alternative named there - the graft itself filling F07's dead indices - is not written.
(corrected after the critic, section 12.2: the 'after compact' column is for BARE levels - no enemy, no wardrobe,
none of F07's police or vans, which compaction drops when no entity names them (+ 1,103 entries once a layer keeps
them). The whole chain was run on prison, Havana and park with their squads: prison 65,509 (8 masks) / 70,925 (12
masks: over the tools' line), Havana M11_B 60,902 / 66,318, park 54,263 without compaction. And the install gate
needs three small fixes before a compacted, twice-lightened folder can pass it: 12.7.)
Havana as ONE map of both chapters is out by this limit alone, whatever else is done, unless half its geometry
is cut; and `Select` cuts whole top-level subtrees only (the map is one: `Locations/M11_B/M11B_Locations.zip`).

**A third way out: another systems level.** MEASURED (`hosts.py`, the stock .prm headers): F07 is the LARGEST
base of the six levels that can be S - chunk-table entries F05 17,601, F08 27,016, F04 30,299, F09 30,453,
F06 31,413, **F07 35,102** (F01 - F03 cannot be S: READ re/maps.md 3.1). Arithmetic on the appended counts
above: under F05 the prison would have 61,450 entries, M11_B 56,934, M11_A 55,048, the two-part bank 61,844 -
all inside 69,632 without `compact`; the Havana pair 94,308, still out. The Havana agent built two of these
(READ re/campaign_fa_havana.md 3.2: F08 + M11_B 66,368, F05 + M11_B 56,953, 'verify: no chunk problem').
What it costs in tools: no Dead Men map has run under another S (READ re/maps.md 3.3, 10), F05's .prm came
out at 90.0 MB there (under the trim line), and everything in section 1 rows 2 - 7, 12, 14 names F07's objects
(`kl_fa_author.HOST`, `ROLE`, `PLACE`; `kl_fa_street.SQUADS` = F07's fourteen police squads;
`kl_map_escape.VAN_HOST / VAN_TOP`; `kl_expansion.SYSTEMS`). So the data-driven tool should find S's objects
by what they ARE (class, controller, spawn kind - as `kl_fa.host_keep` already does, kl_fa.py 601-628), not
by F07's names: then `host` is one more line of a map's data.

### 5.2 The five large blocks of a level load

READ CLAUDE.md 'BUDGET for the builders': 32.0 MB scratch, .fxc + 0x60000, .prm + 0x60000, .ANM + 0x60000 and
the whole `<level>.WAV`; the hook's reserve serves the .prm and any refused block of 1 MB or more.
MEASURED as built (before `lighten`; `result.json` of each trial; .WAV from the two kept builds):

| build | .prm MB | .TEX MB | .ANM MB | .fxc MB | .WAV MB | archive MB |
|---|---:|---:|---:|---:|---:|---:|
| stock F07 (READ re/maps.md 14.0; .ANM / .fxc / .WAV: stock F01, READ CLAUDE.md) | 63 | 281 | 19.8 | 5.9 | 14.7 | 200 |
| (corrected by the second agent: stock F07 itself, MEASURED `hosts2.py`; the row above mixes F01's figures in MiB into a table of MB) | 63.6 | 281.0 | 21.6 | 8.1 | 18.3 | - |
| Retomoto on the tab (`rt_full7`, MEASURED) | 79.9 | 264.9 | 21.6 | 17.8 | 27.8 | 218.9 |
| F07 + M03_A | 85.7 | 373.9 | 21.6 | 17.8 | - | 310.2 |
| F07 + M03_B | 51.4 (trimmed from 92.9) | 363.0 | 21.6 | 17.8 | - | 298.5 |
| F07 + M05_A (bypass) | 78.9 | 342.3 | 21.7 | 17.8 | - | 284.4 |
| F07 + M06_A | 79.5 | 392.7 | 21.6 | 17.8 | 20.1 | 326.8 |
| F07 + M08_A | 64.2 (trimmed from 105.2) | 421.4 | 21.6 | 17.8 | 21.6 | 329.3 |
| F07 + M08_A after `lighten trim,slim` | 64.2 | 231.1 | 21.6 | 17.8 | 21.6 | 192.4 |
| F07 + M11_A | 67.7 (trimmed from 108.8) | 397.7 | 21.6 | 17.8 | - | 335.8 |
| F07 + M11_B | 69.0 (trimmed from 110.1) | 433.3 | 21.6 | 17.8 | - | 362.0 |
| F07 + M11_B + M11_A | **115.2** (nothing left to trim) | 454.7 | 21.6 | 17.8 | - | 403.0 |

- The .prm: a build past 90 MB is trimmed by `kl_graft` itself (`PRM_LIMIT`, kl_graft.py 372, 1327-1338: F07's
  8,650 dead vertex / index chunks become stubs, about 41 MB). The largest .prm that has LOADED is 96.5 MB,
  once (READ CLAUDE.md 'WARDROBE LIVE ... the 96.5 MB bank .prm loads'); 100.9 MB was refused (run RT1).
  The wardrobe adds about 15.5 MB (READ re/maps.md 14.0). So single levels are inside what has run
  (M03_A: 85.7 -> about 45 after the trim - the same 8,650 chunks took 41 MB off four builds here - and about
  60 with the wardrobe: arithmetic, not built); **the Havana pair at 115 MB is past everything that has
  loaded**. (corrected by the second agent: 'past what has loaded' is right, 'blocked' - as the tables of
  section 6 and the summary have it - is too strong. Both measured limits predate the hook's memory reserve: RT1's
  100.9 MB was refused under the original hook (READ kl_graft.py 304-305), the reserve came at 21:49 that day
  (`git log -- klhook/klmem.c`). Since then the .prm is always served from a 128 MiB reserve (READ klhook/klmem.c
  17-45, KLHook.ini [Memory] ReserveMB=128, up to 512): 115.2 MB + 0x60000 = 110.2 MiB fits it by size. What does
  not fit beside it are the other large blocks the reserve catches from the second load on (20.6 + 25.9 MiB on
  Retomoto). So: untested and tight, not impossible. The Havana pair is stopped by the chunk table alone.)
- .ANM: the joined file is F07's own 21.57 MB in five of six trials ("clips +0"; M05_A + 2 clips, 80,752
  bytes). .fxc 17.8 MB is F07's cache (corrected by the second agent: it is NOT F07's - stock F07's is 8.1 MB;
  the build's is S's merged with `<work>/build/shared/union.fxc`, READ kl_graft.py 1493-1494);
  `lighten --load fxc` halves it (READ CLAUDE.md, not loaded live).
- .WAV: 20 - 22 MB with the map's in-memory sounds; talk adds 0.6 MB on Retomoto (MEASURED rt_full7_talk.log).

### 5.3 The navigation mesh

READ tools/kl_pf4.py: `convert` (121-149) refuses a mesh whose arrays 8, 11 or 12 are not empty (none of 41 stock
meshes has one) and DROPS every link whose kind is not 2 (`DD_LINK_KINDS = (2,)`, 69; Dog Days levels use kind 2
only; what its AI does with another kind was not read).
MEASURED (`measure.py` -> `nav`): **no campaign level of this study is refused.** But:

| level | polygons | parts (edges + shared way points) | largest parts | links by kind | dropped | largest parts with kind-2 links / with all links |
|---|---:|---:|---|---|---|---|
| M03_A | 902 | 30 | 566, 149, 112 | 1: 14, 2: 14, 6: 2 | 16 | 567 + 283 / **850** |
| M03_B | 785 | 29 | 215, 173, 170, 109, 47 | none | 0 | the same: five separate stretches |
| M05_A | 437 | 11 | 401 | 1: 2, 2: 4 | 2 | 402 / 402 |
| M06_A | 913 | 25 | 584, 135 | 1: 27, 2: 31, 3: 9 | 36 | 732 / 732 |
| M08_A | 1,298 | 55 | 528, 502, 103 | 1: 38, 2: 38, 6: 4 | 42 | 1,170 / 1,170 |
| M11_A | 1,696 | 43 | 1,589 | 3: 4 | 4 | 1,589 / 1,620 |
| M11_B | 1,015 | 19 | 606, 311 | 1: 6, 2: 6, 6: 1 | 7 | 606 + 313 / **919** |

(The last column counts links as two-way. A kind-2 link is a DROP and one-way in the game: READ kl_fa_bots.py
docstring, '--drop ... one link of kind 2 (a drop, the only kind stock Dog Days has)', 'a one-way drop'. Kinds
1 and 2 come in equal numbers on three levels (14 / 14, 38 / 38, 6 / 6) - ASSUMED: kind 1 is the climb back
up the same ledge. Control, same script: M09_A 359 + 105 polygons joined only by kinds 1 / 6 (465 with all
links), M09_B 1,615 in one part - and Retomoto plays: its round stays on the 359.)
- **M03_A and M11_B**: two large parts of the play space are joined ONLY by links that are dropped. Police,
  guards and bots stay on their part; whether the ROUND has to cross is the place's question (Retomoto's
  does not cross its 105). The answers that exist are per place: a kind-2 link written into the mesh
  (`kl_fa_bots.add_drop`, 609; `DROPS` table) where a walk-down is right, and the hook's hop (`klhop.c`,
  [CrewHop]) for the bots; nothing exists for a climb.
  (corrected by the second agent, MEASURED `G:/kl_scratch/cfa_tooling_v2/nav3.py`: what joins the two large parts
  is not a climb but the campaign's RAPPEL - kind 6, one way, straight down: M03_A two links from height 1,435
  to 200 (12.4 m), M11_B one from 1,000 to 20 (9.8 m); the control M09_A has five from the roof at 25,454 to the
  balcony at 21,020. No link of kind 1 or 3 joins two parts of 100 polygons or more on ANY of the seven levels.
  Kind 1 is measured to be the way back UP the ledges kind 2 goes down (the rises mirror: M03_A -184..-120 /
  +120..+184, M08_A -161..-80 / +80..+161, M11_B -60 / +60), which the report had as an assumption. So losing
  kinds 1 and 3 costs shortcuts, not the map; the split is 'above the rappel / below it', and whether a round
  needs the top at all is the place's question. And 'nothing exists for a climb' was overtaken while this was
  written: READ re/bots.md 12.3 - kl2.exe still has the movers for kind 1 (three climb clips) and kind 3 (a leap),
  only the clips are missing from every Dog Days .ANM - and `tools/kl_fa_climb.py` + `klhook/klclimb.c` (another
  session, 2026-10-11 06:07, untracked, 'NOTHING OF IT HAS RUN') put those clips into a build. No mover for kind 6
  is in that table.)
- **M08_A, M06_A**: the parts hang together through drops only: which way round the round may run is decided
  by them (the tool must test stations in order, section 3.3).
- **M03_B** (the chase) is five stretches of mesh along 1.8 km with nothing between: not a walking map.
- Size: 233 - 493 KB converted. Loaded so far: 603 KB (Retomoto's joined mesh), 259 KB single (M06_FA_A).
- A two-part map's meshes are concatenated by `kl_maps.nav_join` (live on Retomoto); no link joins the parts.

### 5.4 Actors, police bodies, entities

- MEASURED (`globals.py`): stock Fragile Alliance levels have 35..57 `ZFFActor` and 20..36 squads; stock story
  levels up to 148 actors and 90 squads (L07). Retomoto on the tab: 99 actors, 55 squads, 26,039 entities
  (26,991 with the random routes), and it plays. The campaign squads that would stay by `squad_plan`'s rule:
  4 (M05_A) .. 78 actors (M08_A). With F07's 43 + 7 bots that stays under 148. A fixed actor pool was NOT
  looked for in the exe by anybody (no note names one); the counts above are the evidence.
- **The run-time heaps are F07's.** MEASURED (`dyn.py`): the .gms dynamic list of F07 is `ZFFItemWeapon` 162,
  `ZSTDOBJ` 1,536, `ZLNKOBJ` 308, `ZFFItemTemplateWeapon` 142, `ZBoxPrimitive` 20, `ZFFItemAmmo` 108,
  `ZFFItemTemplateAmmo` 108, `ZCHAROBJ` 400 - made for 43 actors and 16 players. Every Dead Men level lists 12
  classes, so `kl_graft` keeps F07's list as it is ("dynamic lists name different classes; kept F07's" in
  every trial log; kl_graft.py 1142-1146). Stock L07, with 148 actors, has `ZFFItemWeapon` 205. Retomoto's
  99 actors + 16 players run on the 162 (1.4 a person, L07's ratio); F07's 43 police + the prison's 78
  campaign actors + 7 bots + 16 players would be 144 people on the same 162. What happens when such a heap is
  full is NOT established (READ re/maps.md 1: "What a Dead Men map then lacks at run time is NOT ESTABLISHED";
  kl_scene's notes call the list 'pre-sizes heaps'). Until it is, **keep a map's people near Retomoto's 99**.
  (corrected by the second agent: the stock levels do NOT support a weapons-per-person ratio, so the 162 is no
  evidence of a people limit either way. MEASURED `G:/kl_scratch/cfa_tooling_v2/actors2.py`: L03 has 140 actors
  on `ZFFItemWeapon` 135, L04 140 on 136, L02 124 on 113, L11 139 on 153 - under one a person - while F05 has
  35 actors on 157 and F02 38 on 150. L07's 148 / 205 is one level, not a rule. 'More people than 99 is untested'
  stands; 'the heap is made for 43 + 16' does not follow from the files.)
- READ re/fed_respawn.md 52-55, 151: a level holds 8 police player objects (`Heroes!Henchmen_01..08`, type 3),
  Arcade never gives one back, and with none free the game stops on an `int3` (kl2 0x4b2984). Same for every
  map: it is S's. The same note (152) reads how a police body is placed: a RANDOM free AFTER_DEATH point, one
  whose node has flag 0x400 is skipped - so "police follow the crew" in a two-part map can be done by hiding
  the first part's points (kl_fa_author's `POLICE_FOLLOW` guess is supported by that reading; not run).
- Entities: the largest stock level has 42,915; the largest trial here 26,106 (M05_A), 25,927 (Havana pair).
  Rooms: 61 on M08_A - the most that ran live is 32 (M02_FA_A); stock L-levels were not counted here.
  (added by the second agent, MEASURED `rooms2.py`: stock L03 has 61 ZROOM entities, F09 42, F08 35; the tab's
  Late Night Opening 31, Retomoto 21. So 61 rooms is a first for a GRAFT, not for the engine. Likewise entities:
  `<work>/build/z_route/retomoto_full`, which loaded and played, has 26,991 - more than M05_A's 26,106 as built.)
- The .HVK of the Havana pair is 9.2 MB; the largest that has loaded and played is 5.0 MB
  (READ kl_map_escape.py 705-706, `HVK_MAX`). `verify` does not test it; `van-check` does.
  (added by the second agent: the TWO-PART BANK is over that line too - .HVK 6.9 MB in the bank agent's chain build,
  READ `<work>/build/cfa/bank/R09+M03_A (R09 = F07+M03_B)/result.json`; `van_check` faults above 5,002,128 bytes,
  READ kl_map_escape.py 1753-1755. The single levels are under it: 3.0, 3.9, 1.6, 2.2, 4.3, 4.0, 4.3 MB.)

### 5.5 The cover list (a fault of the pre-pass)

MEASURED (`cover.py`; kept build of F07 + M06_A read back by `keptfacts.py`):

| level | its `FFCoverList` | after `--campaign` | cover boxes kept / dropped |
|---|---|---|---|
| M03_A | `Special!CoverList` (a campaign subtree) | **dropped: the level has none** | 118 / 20 |
| M06_A | `Specials!CoverPoints!CoverControl` | **dropped: 0 `FFCoverList`, 225 cover boxes (read from the built archive)** | 225 / 15 |
| M03_B | top-level `CoverList` | kept | 12 / **268** (its boxes sit in `Specials!` and `CoverBoxes!`) |
| M05_A, M08_A, M11_A, M11_B, M09_A, M09_B | top-level `CoverList` | kept | 175 / 2, 114 / 0, 630 / 0, 261 / 1, 88 / 0, 392 / 44 |

`campaign_drop` keeps a campaign subtree only when all its controllers are in `PASSIVE = {PlayerCoverCollision,
NoCoverBox, LevelBound}` (kl_maps.py 98, 133); `FFCoverList` is not in it. `kl_graft.verify` counts cover
lists and fails only on more than one (kl_graft.py 1743-1745); `kl_fa.check` does not look. Without a list no
cover box becomes a cover (READ kl_fa_cover.py docstring: `CFFCoverList` slot 13 makes them at load) - for the
police, the bots (`kl_fa_bots_dyn` holds at cover boxes) and the player alike. Fix, small: `FFCoverList` into
`PASSIVE` (it has no fields and names nothing), or keep F07's `Specials!CoverPoints!CoverControl` when the map
side has none, and a line in `verify` for zero.

### 5.6 What leaves with the campaign: animations, doors, switches

- READ re/anmjoin.md 6: the .ANM animates SKELETONS only (characters, weapons, `ZHavokCar`). Doors, lifts and
  props move by `MatPosAnim` / `VertAnim` key data in the .buf, which the graft carries (KEYS blocks). MEASURED:
  the joined .ANM takes nothing from the campaign levels once the campaign is dropped ("clips +0" in five of six
  trials). Lost with the campaign: every `/Level_Specific/<level>` clip (the mini-cutscenes: 38 - 120
  `MiniCutsceneRout` per level, all on the dropped side) and the vehicles' door / passenger clips, because the
  vehicles themselves are campaign (`ZHavokCar`: 0 kept on every level; 3 - 58 on the dropped side of five
  levels, none at all in M05_A and M08_A; `ZHeli` 1 - 2 dropped on five levels).
- Campaign squads that are KEPT bring no animation either: their Dead Men character sets become copies of Dog
  Days sets (`kl_anmjoin.STAND_IN`, a GUESS by role: READ re/anmjoin.md 4) and their mini-cutscene controllers
  are taken off (`kl_fa_author.STRIP`; 45 on Retomoto: READ re/retomoto_fa.md 5). The tab's Retomoto .ANM is
  21,642,904 bytes against F07's 21,570,860 (MEASURED: rt_full7_talk.log, trial logs).
- **The keys stay, their triggers go.** MEASURED (`measure.py`: kept nodes that only dropped campaign nodes name):
  M08_A 294 (108 `RelayMessageList`, 76 `RelayMessage`: the prison's doors and alarms; `MatPosAnimProxy` 25 and
  `AIDWrapper` 31 are on the dropped side), M03_A 141 (21 `MatPosAnim` objects, 13 relay lists: the vault and
  garage doors; 30 of its 31 `MatPosAnimProxy` are dropped), M05_A 96 (39 + 12 lights and the booths the crowd
  `ZHFlowRout` used; `Doors!` with 4 `DoorCtrl` is dropped), M11_B 67, M03_B 47, M06_A 25, M11_A 11.
  Each such object keeps its LOAD-TIME state: 259 - 1,789 kept entities per level are hidden at load (flag 0x400:
  the 'after' halves of paired states). What Retomoto did about it is the pattern: name the campaign's own
  single nodes to keep (`CAMPAIGN_KEEP`: two door proxies, four geometry swaps, two sound activators) and fire
  them from the layer. That is `OPENING.keep` / `JOIN.open` in the data file; finding WHICH nodes is the
  place's design work (`python tools/kl_whoref.py` answers "what names this object").
- Campaign squads: `squad_plan`'s rule (only squad objects, an actor, a rout), applied to every top-level squad
  without its name table (`measure.py`; control: M09_A 26 squads / 52 actors and M09_B 13 / 32 by this count,
  24 / 45 and 10 / 20 by `kl_fa_author.py plan` with its `SQUADS` prefixes - so these are upper bounds),
  keeps 22 of 49 (M03_A), 12 of 53
  (M03_B), **2 of 36 (M05_A)**, 4 of 20 (M06_A), 29 of 65 (M08_A), 26 of 57 (M11_A), 26 of 50 (M11_B).
  What disqualifies the rest: vehicles (`VehicleEffects`, `HavokCarScriptRout`, `PassengerAnimPos`,
  `VehicleMoveOnRoadBehaviourRout`), `ZCivilian`, and on the club `AttachGeomToBone` (14 squads: registered in
  kl2.exe, 0 uses in 21 stock levels). On the club the enemies have to come from F07's police squads
  (`relay`) or the rule has to be widened and proven.

### 5.7 Music and the stream file

- MEASURED (`python tools/kl_str.py need <levels>`): what the graft of a campaign level takes from Dead Men's
  PC_Def.str when "map side" means all of the campaign (kl_str's rule for a story level, READ kl_str.py
  103-108): M03_A 110.7 MB, M03_B 95.9, M05_A 130.1, M06_A 86.3, M08_A 158.0, M11_A 98.6, M11_B 110.0; the
  seven together 459.4 MB (1,105 blocks); the six maps the file is built for today 351.3 MB; all thirteen
  735.8 MB - **the seven add 384.5 MB**.
- MEASURED (`measure.py`, same closure, other roots): what the level needs once the campaign is dropped: 1.7 MB
  (M06_A) .. 15.4 MB, but 85.1 MB on M05_A (the club's music is the map's own sound); the seven together
  130.4 MB (50 blocks). The MUSIC objects alone (`levelsetup/level/<L>/music/*`): M03_A 55.7 MB, M03_B 20.7,
  M05_A 78.2, M06_A 32.8, M08_A 91.7, M11_A = M11_B 29.8; **308.8 MB for all** (10 blocks: each level's layers
  are one or two interleaved sets).
- MEASURED (`streamsum.py`): what each map adds to the file that is not among the six maps' clips already,
  taking the pre-pass side + its music: M03_A 55.8 MB, M03_B 36.1, M05_A 85.1, M06_A 31.4, M08_A 100.2, M11_A
  35.3, M11_B 38.3 (the two share their music); all seven 352.5 MB.
- The installed file is 1,694,610,488 bytes (stock 1,217,890,070). With that lean need of all seven it would be
  2,064,219,448 bytes, with every campaign clip 2,097,787,960 - 83 and 50 MB under 2^31 (2,147,483,648), before
  any talk or Bain clip. Dog Days' .WHD record has a 64-bit stream offset (`off`, `offhi`: READ kl_whd.py
  14-15), but **no stream file past 2 GB has been tried and where the engine seeks was not read**: take the
  music of the maps that ship, not all at once.
- How the music gets played: (a) the campaign's own `PlayMusic` object kept and sent 'AITrigger' by the
  opening - the owner HEARD that on Retomoto (READ CLAUDE.md 'OWNER, 17:35, BY EAR: the Retomoto MUSIC plays');
  44 of M03_A's 46 music nodes are `PlayMusicLayerFade` (layer changes by place: campaign boxes, dropped);
  (b) settings field 157 by `kl_str.set_fa_music` (665): starts at the level LOAD as a 2-D sound, replaced by
  field 158 when the local player turns traitor (READ its docstring; not heard). M05_A has no `PlayMusic`
  node at all (MEASURED: 0): its music needs (b) or the club's own sound objects.
- `kl_str.LEVELS` (116) and `MUSIC` (636) are tables of six / two levels; `kl_fa_talk.SCRIPTS` has the talk of
  M03_A and M06_A already (for the FA siblings) and none for M05_A, M08_A, M11.

### 5.8 Smaller things found on the way

- Materials without a compiled shader (not drawn): M05_A `StripeLight_01a_Blue_M05`, `ObjectLight_01_White_M05`,
  `CeilingLight_01b_White_M05`, `MobilePhone_Front_01a` - the club's own lights; M06_A the paper lantern
  (as on M06_FA_A). MEASURED: trial build notes.
- Classes / controllers on the KEPT side that no Dead Men map which ran live has (`measure.py`, base = the four
  FA maps and Retomoto as built): M03_A `LightToggle` 22; M05_A `ZIKLNKOBJ` 2, `PositionLightControl` 7,
  `ShotActivateDamage` 5, `StartAnim` 2, `KillBox` 60; M06_A `ZCubeGridParticles`, `ZParticleBox`,
  `DiscoMove` 76, `LightToggle` 2; M08_A `EffectDmgBox` 15, `LightToggle` 7, `AnimSequence` 5,
  `ZHingeConstraint` 1, `PlayAudio` 4; M11_A / M11_B `BarrelEffects` 2. Of these `LightToggle`,
  `PositionLightControl`, `ShotActivateDamage`, `StartAnim`, `EffectDmgBox`, `AnimSequence`, `ZHingeConstraint`,
  `ZIKLNKOBJ`, `ZCubeGridParticles`, `ZParticleBox` are registered by kl2.exe and used by NO stock level: code
  the retail game never runs (`kl_maps.py preflight` lists them as RISK; `--flat` / dropping the controller is
  the existing answer).
- Other notes of the trial builds (MEASURED, each `log.txt`): `.hrd` left out on M03_B, M05_A and both chain
  steps ("the rigid bodies do not all come from one level" - as on Retomoto, which plays without one);
  environments "in no stock form" on M03_B (`Sun`, three) and M05_A (`Environment_background`): a matter of
  look, `kl_light.check` does not fail on them; the post-filter palette grows from 39 to 53 - 66 curves.
- Fragile Alliance leftovers in the campaign files: `IngameFragileAllianceKILLERCamera` (a key in all seven);
  M03_A holds 20+ objects named `SO0304_M03_FA_*` (signs, storeys, pillars: the FA bank's street dressing) and
  M06_A two `..._Pavilion_BridgePart_B__FA_0n` - geometry shared with the FA siblings. No spawn point of any
  kind, no `OnlineMoney*`, no PIP trigger, no 'DL0' or 'Multiplayer' object in any of the seven (MEASURED,
  `measure.py` -> `fa_leftovers`).

## 6. Cost model: the five places against the steps of section 1

From the level files only (`kl_maps.py what | sides | first` on the seven levels: outputs in
`G:/kl_scratch/cfa_tooling/{what,sides,first}_<L>.txt`; `measure.py`; the trial builds). "ok" = runs as it is;
"data" = an entry in the data file / a table; "TOOL" = new tool code. Coordinates are the place agents' business.

| step (section 1) | bank M03_A | bank M03_A + M03_B | club M05_A | park M06_A | prison M08_A | Havana M11_A or M11_B | Havana A + B |
|---|---|---|---|---|---|---|---|
| converts (`DeadMen`) | ok | ok | **TOOL: kl_mat `MIRRORED` on U** | ok | ok | ok | ok |
| chunk table (5.1) | ok (64,871) | **unproven: compact, or another host** (79,344; under F05 61,844) | ok (52,935) | ok (53,960) | **compact** (79,005 -> 50,617) **or another host** (F05: 61,450) | **compact or another host** (72,573 / 74,454; F05: 55,048 / 56,934) | **blocked** (111,853; about 83,500 compacted; 94,308 under F05) |
| .prm block (5.2) | ok | ok after trim | ok | ok | ok | ok | **blocked** (115 MB) (corrected by the second agent: untested, not blocked - it fits the hook's 128 MiB reserve by size; see 5.2) |
| pre-pass (`--campaign`) | **TOOL: cover list** | the same | ok | **TOOL: cover list** | ok | ok | ok |
| `chain` / `nav_join` / `--heroes` | `HERO_AT` data | chain ok (name `R09` fixed); `.hrd` left out | `HERO_AT` data | `HERO_AT` data | `HERO_AT` data | `HERO_AT` data | chain builds (MEASURED) |
| mesh for the AI (5.3) | **two large parts (567 + 283) joined only by links of kinds 1 / 6** -> if the round crosses: drop link data + hop | + five loose stretches of M03_B | one part (401 of 437) | drops decide the direction | drops decide the direction | A: one part (1,589); B: **two large parts (606 + 313)** | - |
| layer: places (rows 3 - 5, 8, 14 - 17 of section 2) | TOOL once, then data | data | data | data | data | data | - |
| enemies | 22 campaign squads stay (53 actors) + F07 police: data | + 12 (35) | **2 squads stay: F07 police only, or TOOL (widen `squad_plan`)** | 4 stay (11) + F07 police | 29 stay (78), the richest | 26 stay (50 / 55) | - |
| soldier rows / arms (`kl_arms`, `kl_map_ai.PLANS`) | data (2 table entries) | data | data | data | data | data | - |
| opening beat | data + campaign nodes to keep (141 orphaned switches to choose from) | data | data (96) | data (25) | data (294: doors, alarms) | data (11 / 67) | - |
| loot props | data (`case_model`, own-mesh roots) | data | data | data | data | data | - |
| escape van | **TOOL once: van plan from way points**; then data | data | data; no vehicle or road object in the level at all (0 `ZHavokCar`, `Traffic!` 9 nodes) - the place agent must find a road | data | data | data | - |
| join of two parts | - | data (KLJoin.ini [Join] + [CrewJoin]); `kl_fa_bots_rt` TOOL (generalise) | - | - | - | - | - |
| lighten, wardrobe, guns | ok | ok | ok | ok | ok (MEASURED: lighten) | ok | - |
| AI heisters (`kl_fa_bots`, `_dyn`, `_cover`) | ok once the layer and the mesh links are right | `_rt` generalised | ok | ok | ok | ok | - |
| talk | `SCRIPTS['M03']` exists (source M03_A) | data | data (no script yet) | `SCRIPTS['M06']` exists | data (no script yet) | data (no script yet) | - |
| Bain, balance, crew, escort (hook) | ok | ok | ok | ok | ok | ok | - |
| music (5.7) | data; 55.7 MB | + 20.7 MB | data; 78.2 MB, no `PlayMusic` node: settings 157 | data; 32.8 MB (the FA sibling already uses one of its loops) | data; 91.7 MB | data; 29.8 MB | - |
| stream file | `kl_str.LEVELS` entry | entry | entry | entry | entry | entry | - |
| tab entry | page 2's last entry or page 3: **TOOL once: `kl_expansion` pages** | | | | | | |
| first-time engine code (5.8) | `LightToggle` 22 | + chase classes all dropped | 4 controllers no stock level runs, 4 club-light materials undrawn | 3, lantern undrawn | 5 | `BarrelEffects` only | - |
| size against what has run | inside | 12,764 + 19,675 entities: inside (corrected by the second agent: NOT inside for the .HVK - 6.9 MB in the chain build, the largest that loaded is 5.0 MB and `van_check` faults above it; 44 rooms) | 26,106 entities (Retomoto 26,039) (corrected by the second agent: inside - Retomoto with the random routes has 26,991 and ran) | inside | 61 rooms (ran: 32), mesh 355 KB (added by the second agent: stock L03 has 61 rooms) | mesh 493 KB (A) | - |

Reading it:
- **Tool work that every place needs, once**: the data-driven layer (3.4), the van plan from way points, the
  cover-list rule, `kl_expansion` pages. That is the 0.6 of section 0 (an ESTIMATE, not a measurement): it is
  turning `prepare_host` and the 160 lines of `wire()` into rules over tables and proving them by rebuilding
  Retomoto to the same level. No reverse engineering is left in it - and that was most of what Retomoto cost
  (which way a spawn point faces, that a JumpPoint may not be named, when the round-start event comes, the
  pick-up reach, the van's key tables were each found by reading kl2.exe or by a live run:
  READ re/retomoto_fa.md 9 - 12). A map after that is its data file and its live rounds: 0.25 - 0.4; a two-part
  map adds the join and the bots' second leg: 0.5.
- **Tool work one place forces**: the club - the material rule and a decision on enemies; the prison and
  Havana - `compact` in the chain (it exists; what it lacks is a live load) or a smaller systems level (which
  the tools cannot author on today); the bank - mesh links between its two large parts if the round crosses;
  a two-part bank - `kl_fa_bots_rt` without its Retomoto names.
- **Not possible with any of it**: both Havana chapters in one map.
- **Cheapest first**, by tools alone: the park (M06_A: everything fits, mesh in one direction, small music) and
  the bank's first chapter (M03_A) - both have an FA sibling on the tab, so the place agents decide whether
  they are worth having next to it; then the prison (most enemies ready, needs `compact` proven); then one
  Havana chapter; the club last (two tool faults and no squads).

## 7. The trial builds

All with `python tools/kl_maps.py one|chain "<work>/build/cfa/tooling" F07 <L> --campaign`; numbers from each
folder's `result.json` / `log.txt`. Every build's `verify` problems are the missing Fragile Alliance layer
(1 CRASH `settings`, 9 BROKEN) plus what the row names - "exactly as it should be for a level that has none"
(READ re/maps.md 4.2).

### 7.1 Table

| build | problems | entities | chunk-table entries | .prm / .TEX / .ANM MB | textures / materials | rooms | navigation mesh | stream clips missing | seconds |
|---|---:|---:|---:|---|---|---:|---|---:|---:|
| F07 + M03_A | 11 | 19,675 | 64,871 | 85.7 / 373.9 / 21.6 | 1,866 / 1,221 | 28 | 232,480 B, converts | 1 | 70 |
| F07 + M03_B | 11 | 12,764 | 49,645 | 51.4 / 363.0 / 21.6 | 1,621 / 881 | 17 | 203,412 B | 6 | 33 |
| F07 + M05_A | **does not build** (`kl_mat`) | | | | | | | | 12 |
| F07 + M05_A, check bypassed (7.2) | 11 | 26,106 | 52,935 | 78.9 / 342.3 / 21.7 | 1,676 / 1,135 | 20 | 119,236 B | 5 | 37 |
| F07 + M06_A | 10 | 19,157 | 53,960 | 79.5 / 392.7 / 21.6 | 1,589 / 1,002 | 7 | 258,988 B | 0 | 35 |
| F07 + M08_A | 12 (**chunk table**) | 23,307 | **79,005** | 64.2 / 421.4 / 21.6 | 1,964 / 1,286 | 61 | 354,868 B | 11 | 40 |
| F07 + M11_A | 12 (**chunk table**: 1,155 slots left, 4,096 wanted) | 16,388 | **72,573** | 67.7 / 397.7 / 21.6 | 1,773 / 1,150 | 18 | 493,456 B | 7 | 49 |
| F07 + M11_B (chain, step 1) | 12 (**chunk table**) | 19,188 | **74,454** | 69.0 / 433.3 / 21.6 | 1,835 / 1,178 | 16 | 290,516 B | 7 | 63 |
| F07 + M11_B + M11_A (chain) | 12 (**chunk table**) | 25,927 | **111,853** | 115.2 / 454.7 / 21.6 | 1,969 / 1,323 | 32 | 783,916 B (`nav_join`) | 7 | 40 |

Limits: textures 4,096, materials 2,048 (no build is near). The chain needs no change for another pair of
levels: it built M11_B + M11_A with the fixed pseudo name `R09`, `nav_join` passed `kl_pf4.check`, `.hrd` was
left out ("the rigid bodies do not all come from one level"), as on Retomoto.

### 7.2 The club's material check

`python tools/kl_maps.py one ... F07 M05_A --campaign` ends in 12 s:
`ValueError: material 538 (Locations/M05/Concrete/Concrete_Walkway_01a_M05): TEXT/TILU value b'MIRRORED' never
occurs in Dog Days` (kl_mat.py 397, from `kl_graft.DeadMen.__init__` 823). `matscan.py` (the same test made to
record instead of raise, in its own process) over all 20 Dead Men levels: only **M05_A (6 materials) and M01_A
(2)** have it (corrected by the second agent: the 6 and 2 count how often the test ran, twice per texture stage -
M05_A has it in ONE material on three stages, M01_A in one material on one stage: section 11.2); Dog Days knows `TILU` in {'', NONE, TILED} and `TILV` in {'', MIRRORED, NONE, TILED}. So the
value is a Dog Days value on the other axis. The measurement build of the row above told the reference that
MIRRORED is known on U (`one_bypass.py`; in that process only, no file edited): the rest of the pipeline then
has nothing against the club. What the engine draws with MIRRORED on U is NOT established - the rule to write
into `kl_mat` is a decision (accept, or write TILED), not a measurement.

### 7.3 The prison through the tools that exist (kept build, then deleted)

`prison_chain.sh`: build `--keep` -> `kl_maps.py preflight` -> `kl_graft.py lighten ... --load trim,slim` ->
`kl_chars.py compact` -> `kl_impact.py`.
- preflight: CRASH 2 (both are the missing layer: verify's 12 problems, no settings object), RISK 14 (9 of the
  layer; `EffectDmgBox` 15, `LightToggle` 7, `AnimSequence` 5, `ZHingeConstraint` 1 = code no stock level runs;
  one `CCheckInside` bool value stock never stores), NOTE 66; KEYS 210 chunks all found; 61 rooms, 242 gates;
  `.sgd` both octrees; FDX 1 record. "larger than any Dead Men build that ran live: entities 23307 (19827),
  rooms 61 (20), nav_bytes 354868 (186672)" - its `LIVE` table (kl_maps.py 110) predates Retomoto.
- lighten: .prm 64.2 -> 64.2 MB (already trimmed by the build), .TEX 421.4 -> 231.1 MB (464 of 1,964 textures
  only dead materials name), archive 329.3 -> 192.4 MB.
- compact: **79,005 -> 50,617 chunk-table entries**, .prm 64.2 -> 62.4 MB; 13,430 .gms and 15,165 .prp
  references rewritten, 3,495 of 4,518 .oct records kept; its own check `problems: 0`.
- `kl_impact.py` on the lightened folder: 1 problem (the chunk table); on the compacted folder: **0**.

## 8. What only a run in the game can settle

1. `kl_chars.py compact` on any level: it moves the systems level's live chunks (HUD, fonts, effects, post
   filters must look right). Without it the prison, a Havana chapter and the two-part bank cannot ship.
2. A cloned player-fired TRIGGER BOX, counter or `ActivateGeom` appended to a finished build does its job -
   the clone writer has carried the bots' squads, their steps, timers and random triggers (live) and cover
   boxes (not loaded) so far.
3. F07's van on a plan made from way points on a map with no Dead Men road (the lane test is offline; the
   drive, the boarding and the escape camera are not).
4. A third menu page: `HeistPlayMenu3` latched, `[Redirect.3]`, the stock page and page 2 after it in one process.
5. A map page entry in slot F07 (never loaded from a page) and a level in a slot from page 3.
6. `MIRRORED` on the U axis of six club materials (corrected by the second agent: of ONE club material, the
   walkway concrete), the club's four undrawn light materials, and the ten
   controllers of 5.8 that the retail game never runs.
7. Levels larger than anything that ran: 61 rooms (M08_A), a 493 KB mesh (M11_A), 26,106 entities (M05_A).
8. Whether a level with no `FFCoverList` loads at all (today's pre-pass makes one of M03_A and M06_A).
9. A stream file near or past 2 GB.
10. Field 157 as the music of a round (starts at the load, not at GO).
11. More people in a level than Retomoto's 99 actors on F07's run-time heaps (5.4).

## 9. Claims the conclusions rest on

| # | claim | check |
|---|---|---|
| 1 | the authored layer is wired into the graft by module name | `grep -n "kl_fa_author" tools/kl_graft.py tools/kl_maps.py`: kl_graft.py 1075-1080, 1087-1090, 1173-1175; kl_maps.py 439-442 |
| 2 | every position of the Retomoto layer is a constant of four modules | tools/kl_fa_author.py 79-398 (`HOST PART_B PART_A`, `PLACE`, `ROLE`, `CAMPAIGN_KEEP`), kl_fa_street.py 78-262, kl_fa_van.py 50-70, kl_fa_blast.py 95-160 |
| 3 | `--heroes` works for M09_A / M09_B only | tools/kl_maps.py 103-104 (`HERO_AT`), 397 (`HERO_AT.get(name, {})`) |
| 4 | new entities can be appended to a finished build, and such builds played | tools/kl_fa_bots.py 2002-2088 (`Maker`), 2226-2382 (`apply`); CLAUDE.md 'LOADS + ROUNDS: all five route builds load and play 4 min' |
| 5 | the AI heisters' route is derived from the level, not authored | tools/kl_fa_bots.py docstring 'HOW THE ROUTE IS PLANNED', `stations` 868, `plan` 1312; per-map options only in `RECIPE` 258 |
| 6 | the generic van needs a Dead Men spline car to plan from | tools/kl_map_escape.py 1075-1077 (`len(cars) != 1` -> fault), `van_prepare(S, P)` 1309 takes any plan |
| 7 | M05_A does not convert | `python tools/kl_maps.py one <out> F07 M05_A --campaign` -> ValueError at kl_mat.py 397; `python G:/kl_scratch/cfa_tooling/matscan.py` |
| 8 | the chunk table stops M08_A, M11_A, M11_B and both two-part maps as built | `<work>/build/cfa/tooling/*/result.json` `problems[0]`, `log.txt` '.prm: N of M chunks ... appended to 35101'; kl_impact.py 61 (`CHUNK_SAFE`) |
| 9 | `compact` brings the prison under the table with 0 `kl_impact` problems, and has never been loaded | `G:/kl_scratch/cfa_tooling/p4_compact.log`, `p6_impact_compact.log`; re/prm_limit.md 'Compaction ... NOT LOADED LIVE' |
| 10 | the pre-pass removes the cover list of M03_A and M06_A and nothing reports it | `python G:/kl_scratch/cfa_tooling/cover.py M03_A M06_A`; `p9_keptfacts_M06.log` ('FFCoverList controllers: 0; cover boxes ...: 225'); kl_maps.py 98, kl_graft.py 1743-1745 |
| 11 | the mesh converter drops links of kinds 1, 3, 6; on M03_A and M11_B two large parts are then joined by nothing | tools/kl_pf4.py 69, 121-149; `python G:/kl_scratch/cfa_tooling/measure.py` -> `out/measure_<L>.json` key `nav` |
| 12 | no campaign mesh of the study is refused | the same key: `convert: ok` on all seven |
| 13 | the hook takes pages 2..9 and a redirect per page as data | klhook/klslot.c 156-158, 234-238, 509-538, 578-583 |
| 14 | the Arcade page has room for one more page button, and kl_expansion knows one page | klhook/mkoverlay.py 100, 122, 385-386; tools/kl_expansion.py 90, 657-669 |
| 15 | Dead Men ships a menu picture for every campaign chapter of the study | `python G:/kl_scratch/cfa_tooling/globals.py` -> 'DEAD MEN FRONTEND SCENE: picture entities' |
| 16 | the stock soldier rows are written on M09_A / M09_B only; the four FA maps get theirs from a per-map plan table | tools/kl_arms.py 161 (`SKILL_LEVELS`); tools/kl_map_ai.py 166-287 (`PLANS`), 787-788 |
| 17 | the seven campaign levels add 384.5 MB of stream clips if the whole campaign side is taken, 352.5 MB with the pre-pass side + music (the music objects alone are 308.8 MB); the file would stand 50 - 83 MB under 2^31 | `python tools/kl_str.py need` (six) = 351.3 MB, with the seven = 735.8 MB; `python G:/kl_scratch/cfa_tooling/streamsum.py` |
| 19 | F07 is the largest base for the chunk table (35,102 entries; F05 17,601, F08 27,016) | `python G:/kl_scratch/cfa_tooling/hosts.py`; re/campaign_fa_havana.md 3.2 (F08 / F05 + M11_B built) |
| 18 | actors: stock up to 148, Retomoto 99, police bodies 8; the run-time heaps of every graft are F07's (162 weapon items) | `globals.py` 'STOCK DOG DAYS LEVELS' / 'OUR BUILDS'; `dyn.py`; kl_graft.py 1142-1146; re/fed_respawn.md 52-55, 151 |

## 10. Scratch files (all under G:/kl_scratch/cfa_tooling/)

`measure.py` (per level: sizes, the pre-pass, first-timers on the kept side, squads by `squad_plan`'s rule,
orphaned switches, navigation parts and links, stream need, music) -> `out/measure_<L>.json`, `show.py` prints
them (`show_all.txt`, `show_all2.txt`); `out_ctl/` the same for M09_A / M09_B; `globals.py` -> `globals.txt`
(actors per stock level, the F07 layer by family, picture entities); `cover.py` -> `cover.txt`; `matscan.py`
-> `matscan.txt`; `one_bypass.py`; `keptfacts.py`; `prison_chain.sh` -> `p1..p9_*.log`; `need_*.txt`
(`kl_str.py need`); `streamsum.py` -> `streamsum.txt`; `dyn.py` -> `dyn.txt`; `hosts.py` -> `hosts.txt`; `what_ / sides_ / first_<L>.txt`;
`build_*.log`.

## 11. Verification (second agent)

2026-10-11, the skeptic of this report. OFFLINE; no existing tool edited; nothing installed. My scripts and their
outputs: `G:/kl_scratch/cfa_tooling_v2/` (each written independently of the first agent's - none imports
`measure.py` / `globals.py`). My trial builds: `<work>/build/cfa/tooling/v2/` (result.json + log.txt kept, the
kept archives deleted). Corrections are also marked in place above ('corrected by the second agent' / 'added by
the second agent'). **My verdict after the checks: feasible-with-work - the same as the first agent's.** Every
measured number I re-derived came out as written or within a few units; what I corrected is one count (six
materials -> one), four statements that overstate a limit (the 115 MB .prm 'blocked', the weapon heap, 61
rooms, the mesh 'split' that is a rappel), two that understate one (the two-part bank's .HVK, the data sketch's
coverage of Retomoto) and two labels (.fxc, a table row). The order of work the report ends on stands.

### 11.1 Confirmed (first pass)

- **Authoring is wired in by module name** (claim 1). MEASURED: `grep -n kl_fa_author tools/kl_graft.py tools/kl_maps.py`
  -> kl_graft.py 1075-1080, 1089-1090, 1173-1175; kl_maps.py 439-442. Line counts 1,160 + 1,161 + 780 + 289 (`wc -l`).
- **The club does not convert** (claim 7). MEASURED: `python tools/kl_maps.py one <work>/build/cfa/tooling/v2 F07 M05_A
  --campaign` -> `ValueError: material 538 (...Concrete_Walkway_01a_M05): TEXT/TILU value b'MIRRORED' never occurs in
  Dog Days` at kl_mat.py 397 (`build_M05_A.log`). Dog Days' own TILU values {'', NONE, TILED}, TILV {'', MIRRORED,
  NONE, TILED} (`mat2.py`, read from `kl_mat.dd_reference()`).
- **The trial builds' numbers** (7.1). READ every `result.json` / `log.txt` under `<work>/build/cfa/tooling`
  (`readres.py` -> `readres.txt`): problems, entities, chunk counts, member sizes, mesh bytes, `clips +0`, the
  'dynamic lists ... kept F07's' note all as the table has them. MEASURED again by my own build of F07 + M06_A
  (`--campaign --keep`, `build_M06_A.log`, `built2.py`): problems 10, 19,157 entities, .prm header count 53,960,
  .prm 79.5 / .TEX 392.7 / .ANM 21.6 / .fxc 17.8 MB, .WAV 20.1 MB, mesh 258,988 bytes.
- **The pre-pass drops the cover list of M03_A and M06_A** (claim 10). MEASURED (`cover2.py`): the only `FFCoverList`
  of M03_A is `Special!CoverList`, of M06_A `Specials!CoverPoints!CoverControl`; `kl_maps.campaign_drop` names both
  tops; the five other campaign levels (and M09_A / M09_B, M03_FA_A, M06_FA_A) hold it in a top-level `CoverList`
  that stays. Read back from my own kept F07 + M06_A archive: **0 `FFCoverList` controllers, 225 ZSTDOBJ named
  \*coverbox\***. READ kl_graft.py 1743-1745: `verify` only fails on more than one.
- **The mesh converter** (claims 11, 12). MEASURED (`nav2.py`, the Dead Men mesh read from .gms +0x34, connectivity by
  my own union-find over array-9 edges and array-7 links): none of the seven is refused; links by kind and the
  number dropped agree on all seven (M03_A 1:14 2:14 6:2, 16 dropped; M06_A 36; M08_A 42; M05_A 2; M11_A 4; M11_B 7;
  M03_B none); parts: M03_A 566 / 149 / 112, with kind-2 links 567 + 283, with all links 850; M11_B 606 / 311,
  606 + 313, 919; M08_A 1,170; M06_A 732; M05_A 401 -> 402; M03_B 215 / 173 / 170 / 109 / 47; control M09_A
  359 + 105 -> 465. (M11_A: I get 1,585 and 1,616 where the table has 1,589 and 1,620 - I do not join by 'shared way
  points'; the conclusion is the same.) READ kl_pf4.py 69 (`DD_LINK_KINDS = (2,)`), 121-149.
- **F07 is the largest base** (claim 19). MEASURED (`hosts2.py`, u32 at .prm +4 of every stock archive): F04 30,299,
  F05 17,601, F06 31,413, F07 35,102, F08 27,016, F09 30,453 (the largest stock level of all: L10 36,778).
- **`compact` on the prison** (claim 9). READ the logs of two agents who each ran it (`G:/kl_scratch/cfa_tooling/
  p4_compact.log`, `<work>/build/cfa/prison/compact/log.txt`): 79,005 -> 50,617, problems 0; `kl_impact` 0 problems
  on the compacted folder, 1 on the lightened one. Not re-run by me. 'Never loaded': READ re/prm_limit.md
  ('Compaction ... NOT LOADED LIVE') and `grep -i compact CLAUDE.md re/*.md` - no live run is recorded anywhere.
  NEW from the trial logs: every build's `verified: ... N reachable chunks` line already IS the compacted size
  minus one (M08_A 50,616; M11_A 44,198; M11_B 46,080; the Havana pair 83,464; M03_A 36,483; M03_B 21,283) - so
  the table's 'about 44,000 / 46,000 / 83,500 (ASSUMED)' are in fact MEASURED by the builds themselves, and the
  two-part bank is about 36,483 + 21,283 - 6,800 (F07's own live chunks: 46,080 + 44,198 - 83,464) = about 51,000.
- **The stream file** (claim 17). MEASURED: `python tools/kl_str.py need M03_A M03_B M05_A M06_A M08_A M11_A M11_B`
  -> 1,105 blocks, 459.4 MB; `need` (the six) -> 892 blocks, 351.3 MB (`need_seven.txt`, `need_six.txt`). File sizes
  by `stat`: installed and `<work>/build/v_bain/over_talk/PC_Def.str` 1,694,610,488, stock 1,217,890,070 bytes.
  The 13-level union (735.8) and `streamsum.py`'s split I read, not re-ran. kl_str's 'MB' are MiB (the byte sums
  only come out that way).
- **Slots and pages** (claims 13, 14; section 4). READ klhook/klslot.c: `KLS_SLOTS 16`, `KLS_RULES 64`,
  `KLS_PAGES 10` (156-158), `kls_map_page_of` accepts 'HeistPlayMenu' + one digit 2..9 (234-238), `kls_rules(page)`
  reads `[Redirect.N]` and keeps one rule per (slot, page) (509-538), the loop over all pages (578-583).
  READ klhook/mkoverlay.py: `ICONS` four entries (100), `for n in range(2, 6)` (122), `len(rows) > len(ICONS)` ->
  exit with rows = Heister + Guns + one per page (385-386). READ tools/kl_expansion.py: `ORDER`, `DLC = (5, 8, 9)`,
  `PAGE = 2` (88-90), `MAPS` five entries in F01 F02 F03 F04 F06.
- **A menu picture for every chapter of the study** (claim 15). MEASURED (`pics2.py`, the names of Dead Men's
  `Scenes/KaneAndLynch.zip`): 20 `LevelPicture_*`, among them M03A M03B M05 M06 M08 M11A M11B.
- **Soldier rows and plans are per-map tables** (claim 16). READ kl_arms.py 161 and 416 (`m_name in SKILL_LEVELS`),
  kl_map_ai.py 171-270 (four `PLANS`), 793 (raises without one).
- **The van plan needs a Dead Men spline car** (claim 6). READ kl_map_escape.py `van_plan` (1064-1077) and
  `van_prepare(S, P)` (1309).
- **The clone path** (claim 4). READ kl_fa_bots.py `Maker` (2002-2088) and `apply` (2226-2382). MEASURED
  (`<work>/build/z_route/M01/bots.json`, `dyn.json`: the build that is on the tab): 170 entities appended by
  `kl_fa_bots`, then 126 taken out and 663 put in by `kl_fa_bots_dyn` - through the writer went ZBoxPrimitive
  107 + 405, ZGROUP 56 + 258, ZFFActor 7 - with `DefendBehaviourRout`, `SquadModifierBehaviour`,
  `TriggerDelay2`, `RandomTrigger`, `TriggerLootDepleted`, `AllyEscapeBox`, `ZSoldier`, `ZSquadScript`. NEW
  (`boxes2.py`): `Node` gives every clone model 0, and that is right for what section 3.4 wants to clone - all 876
  ZBoxPrimitive and all 988 ZGROUP of stock F07 have no model (trigger boxes, timers, counters, `ActivateGeom`,
  `KillBox`, `LevelBound`, `Explode` on a ZGROUP, `ShakeCamera`); it is NOT enough for loot (133 of F07's 138
  `OnlineMoneyCtrl` sit on a ZSTDOBJ with a model), which is why the pool stacks have to be re-typed, not cloned.

### 11.2 Corrected (the places are also marked in the text above)

- **'Six materials' of the club is ONE material.** MEASURED (`mat3.py M05_A M01_A`): M05_A has `TEXT/TILU = MIRRORED`
  in one material instance of 690 - slot 538 `Locations/M05/Concrete/Concrete_Walkway_01a_M05`, on its three
  texture stages (mapDiffuse, mapNormal, mapSpecularMask); M01_A in one of 1,014 (`Vechicles/Civil_USA_01/
  V_Civ_USA_01_02`, one stage). `matscan.py`'s 'x6' / 'x2' count how often the test ran (twice per stage), not
  materials. The build still stops there, so the tool fault stands; what shrinks is the risk of the rule: one
  walkway concrete.
- **'.fxc 17.8 MB is F07's cache' is wrong.** MEASURED (`hosts2.py`): stock F07's .fxc is 8.1 MB. READ kl_graft.py
  1493-1494: the build's cache is `merge_fxc(S's, <work>/build/shared/union.fxc)` because Dead Men has none. The
  number 17.8 MB is right, and `lighten --load fxc` brings it to about 8.7 MB (READ the prison agent's
  `<work>/build/cfa/prison/light/log.txt`: 242 -> 119 entries, 16.94 -> 8.28 MiB).
- **The table row 'stock F07' of 5.2 mixes two levels and two units.** MEASURED (`hosts2.py`): stock F07 is .prm
  63.6, .TEX 281.0, .ANM 21.6, .fxc 8.1 MB (.WAV 18.3 MB by the first agent's `hosts.txt`). The 19.8 / 5.9 / 14.7
  are CLAUDE.md's figures for F01 in MiB.
- **'The Havana pair's .prm (115 MB) is blocked' overstates it** (5.2, the table of section 6, blocker 3 of the
  summary). Both measured limits - 96.5 MB loaded, 100.9 MB refused - are from before the hook's memory reserve
  existed (READ kl_graft.py 304-305: RT1 ran under 'the original hook'; `git log -- klhook/klmem.c`: first commit
  2026-10-09 21:49). Today the .prm always goes into a reserve of 128 MiB (READ klhook/klmem.c 17-45, klhook/KLHook.ini
  [Memory]); 115.2 MB + 0x60000 is 110.2 MiB. It is untested and leaves no room there for the other large blocks
  of a later load, but it is not a wall. The pair is stopped by the chunk table (83,464 live chunks, MEASURED by its
  own `verified:` line) and that alone.
- **'The run-time heaps are made for 43 actors + 16 players' and the ratio '1.4 a person' are not what the files
  say** (5.4, blocker 10). MEASURED (`actors2.py`, every stock level's dynamic list): `ZFFItemWeapon` is 135 for
  L03's 140 actors, 136 for L04's 140, 113 for L02's 124 - under one a person - and 157 for F05's 35, 150 for F02's
  38. The list does not scale with people. 'More than Retomoto's 99 actors is untested' stands as a plain
  statement; the rule 'keep a map's people near 99' has no evidence behind it either way.
- **'61 rooms: larger than anything that ran' is true of a graft only.** MEASURED (`rooms2.py`): stock L03 has 61
  ZROOM entities, F09 42, F08 35. And **M05_A's 26,106 entities are not past what ran**: `<work>/build/z_route/
  retomoto_full` has 26,991 (MEASURED `built2.py`) and is one of the five route builds that loaded and played.
- **The two-part bank is missing a limit.** READ `<work>/build/cfa/bank/R09+M03_A (R09 = F07+M03_B)/result.json`
  (`readres.py` on that folder): .HVK 6.9 MB, 44 rooms, mesh 435,836 bytes. The largest .HVK that has loaded is
  5.0 MB and `kl_map_escape.van_check` faults above 5,002,128 bytes (READ 1753-1755): the tools as they are
  refuse that map at the van step. Section 6's column says 'inside'.
- **The mesh split of M03_A and M11_B is a rappel, not a missing climb** (5.3, blocker 6). MEASURED (`nav3.py`:
  parts from edges + kind-2 links, then every other link whose ends lie in different parts): the 283-polygon part
  of M03_A reaches the 567 only by two kind-6 links that go from height 1,435 to 200; M11_B's 313 reaches the
  606 by one from 1,000 to 20; M09_A's 106 the 359 by five from 25,454 to 21,020 (the roof to the balcony the
  heisters now start on). No kind-1 or kind-3 link joins two parts of 100+ polygons on any of the seven levels
  (M11_A: two kind-3 links bring a 24-polygon islet down 3.2 m). Kind 1 = the climb back up a kind-2 drop: no
  longer an assumption, the rises mirror exactly on M03_A, M08_A, M11_B, M09_A. And READ re/bots.md 12.3 (older
  than this report): kl2.exe has movers for kinds 1, 2, 3; `kl_pf4.convert(link_kinds=...)` can keep them; the
  clips are what is missing, and `tools/kl_fa_climb.py` (written by another session at 06:07, not run) adds them.
  So blocker 6 shrinks to: 'the top of a rappel is a part of its own, as on Retomoto'.
- **'All of it generic' for the dynamic bots is true of one-part maps only** (section 1 row 15): with two chains
  `kl_fa_bots_dyn` imports `kl_fa_bots_rt`, which imports `kl_fa_author`, `kl_fa_van` and `kl_fa_street`.
  Likewise `kl_fa_loot.survey` (row 7, 'generic') on a built level calls `walk()`, whose default starts are
  `kl_fa_author.START` and whose switched objects are found through `kl_fa_author.ROLE['blast timer']` (READ
  kl_fa_loot.py `blast_state`, `walk`): usable for another map only with `starts` and `box` passed in. And
  `kl_map_escape.van_prepare` imports `kl_fa_author` for `node_of`.

### 11.3 Confirmed (second pass)

- **Squads that pass `squad_plan`'s rule** (5.6, blocker 10). MEASURED (`squads2.py`: `kl_fa_author.squad_plan`
  itself, its prefix table replaced in memory by ('',)): M03_A 22 of 49 (53 actors), M03_B 12 of 53 (35), M05_A
  2 of 36 (4; `AttachGeomToBone` on 14, `ZCivilian` 7), M06_A 4 of 20 (11), M08_A 29 of 65 (78), M11_A 26 of 57
  (50), M11_B 26 of 50 (55); controls M09_A 26 / 52, M09_B 13 / 32. Every figure as the report has it.
- **Kept nodes that only dropped campaign nodes name** (5.6). MEASURED (`orph2.py`, my own definition: every
  referrer by path lies in a dropped subtree): M08_A 290 (report 294), M03_A 141, M05_A 97 (96), M06_A 25, M11_A 11,
  M11_B 67, M03_B 47; M03_A's are 21 `MatPosAnim` and 13 relay lists, M08_A's 124 + 83 relay controllers.
- **Actors, squads, the dynamic list** (claim 18). MEASURED (`actors2.py`): stock F levels 35..57 `ZFFActor` and
  20..36 squads, story levels up to 148 / 90 (L07); F07's list 162 / 1,536 / 308 / 142 / 20 / 108 / 108 / 400;
  F07 has 63 spawn points (8 START, 7 AFTER_DEATH, 4 TRAITOR, 44 of the other modes), 5 NORMAL + 108 + 25 DROP
  money objects, 234 `FASpecials!` and 32 `Specials!` subtrees. The tab's Retomoto (`built2.py` on `rt_full7`):
  26,039 entities, 99 actors, 55 squads, chunk table 65,331, .prm 79.9 / .TEX 264.9 / .HVK 5.0 MB, .WAV 27.8 MB,
  mesh 603,332 bytes, ONE `FFCoverList` (`ROOT\CoverList`), F07's dynamic list unchanged.
- **Fragile Alliance leftovers** (5.8). MEASURED (`left2.py`): no ZSpawnPoint, no `Online*` / money controller in
  any of the seven; `IngameFragileAllianceKILLERCamera` in all; `SO0304_M03_FA_*` geometry in M03_A.
- **First-time engine code on the prison** (5.8). MEASURED (`python tools/kl_maps.py first M08_A`): `EffectDmgBox`
  15, `LightToggle` 7, `AnimSequence` 5, `ZHingeConstraint` 1, each 'stock Dog Days: 0 in NO LEVEL'.
- **The menu as installed** (section 4). MEASURED (`menu2.py` on `<work>/build/w_tabN/KLExpansion/Overlay/
  Patch01.zip` against the stock Patch01.zip): Arcade page buttons Heister, Guns, 'Dead Men maps'; three of
  mkoverlay's four icons in use; map pages `HeistPlayMenu`, `HeistPlayMenu2`; a map page is 64 tags (41
  GuiElement), the whole overlay adds 275 tags to the stock 5,661. `PAGE` occurs 12 times in kl_expansion.py.
- **The tables of the Retomoto layer** (claim 2). MEASURED by importing them: `PLACE` 39, `ROLE` 14, 14 police
  squads, `STEPS` 12, `CAMPAIGN_KEEP` 27 + 1. READ kl_fa_van.py 48-70, kl_fa_blast.py 93-150.
- **The bots' route is derived** (claim 5). READ kl_fa_bots.py 'HOW THE ROUTE IS PLANNED', `RECIPE`, `EXIT_CUT`,
  `DROPS` (keyed by level, with defaults), `add_drop`; the level names in it are those three tables.
- **The proposed cover-list fix is as small as claimed and works offline.** MEASURED (`coverfix.py`: `kl_maps.PASSIVE`
  given 'FFCoverList' in memory only, then the build kept and read back): F07 + M06_A has exactly one
  `FFCoverList` (`Specials!CoverPoints!CoverControl`), 225 cover boxes, problems 10 as before; F07 + M03_A one
  (`Special!CoverList`), 118 boxes, problems 11 as before. No name of F07's layer meets a kept top-level name of
  any of the seven levels (`clash2.py`); M06_A's list has the same NAME as F07's, which only matters for a layer
  that keeps F07's `Specials!` - it must drop F07's list, as `kl_fa_author.DROP` does.

### 11.4 The design, attacked

1. **Does the data file of 3.2 cover what `kl_fa_author` does?** Five things taken, each looked for:
   (1) spawn points by kind with their shifts and the sixteen player groups - FOUND (`START`, `POLICE`,
   `OTHER_MODES`); (2) loot from pool stacks with value, reach and 'hidden until the room is dead' - FOUND (`LOOT`);
   (3) the opening chain: round-start list -> timer -> bomb -> fuse -> the campaign's own nodes - FOUND
   (`OPENING`), but not the bomb's edited radii; (4) the staged fight: campaign boxes made criminal-only, squads
   that wait - FOUND (`ENEMIES.steps`, `.wait`), but NOT the emptied lists of `QUIET`, the moved flank points of
   `ROOM_PLACE`, the three squad / modifier values that make 'the guards run, the pistols rush'; (5) the join -
   FOUND (`JOIN`). Outside the five: 48 world places of map nodes in `kl_fa_street` and 26 of `PLACE`'s 39
   entries have no section. So the skeleton of a round is covered; exactly the parts the owner asked for by name
   on Retomoto (the room that runs, police that fall back, buses as cover, wave 3 out of the truck) are not. The
   repair is two generic sections (marked at 3.2). The proof 'rebuild Retomoto to the same level' is therefore
   harder than 3.2 says, and its reference has to be pinned: the build on the tab was not made by
   `kl_fa_loot.py test` alone (it went through another session's option set, `lighten`, plates, guns, bots, talk,
   Bain: READ CLAUDE.md), and `kl_fa_author.py` / `kl_fa_street.py` / `kl_fa_van.py` / `kl_arms.py` are tuned
   by another session from day to day (READ CLAUDE.md 'kl-merge-b6 ... owns').
2. **A cheaper first step exists and the report names it only in a bracket.** `kl_graft.build` and `kl_maps.one`
   use nine names of the authoring module and nothing else: `HOST`, `prepare_host`, `strip`, `KEEP`, `DROP`,
   `layer_names`, `complete`, `wire`, `campaign_names` (READ kl_graft.py 1075-1090, 1173-1175; kl_maps.py 439-442).
   Letting `author=` take a module is a change of a few lines and leaves Retomoto byte for byte as it is. The
   first new map can then be a second module that imports `kl_fa_author`'s and `kl_fa_street`'s helpers, and
   the data-driven tool is cut from two examples instead of one. 'Without the tool every map is 0.7 - 1.0' counts
   the helpers as not reusable; they are importable today. (ASSUMED: my reading of the cost, not a measurement.)
3. **The slot / page plan is true to klslot.c and mkoverlay.py** (11.1). Two things it does not say: the menu
   system has a hard cap of 5,096 objects with unknown headroom (READ re/menus.md 2.5; a page is 64 tags, the
   overlay that runs adds 275) - a small risk, and the test is an `int3`; and DLC slots F05 / F08 / F09 are left
   out by the TOOL's choice (`DLC = (5, 8, 9)`, 'never redirected here'; mkoverlay accepts F01..F09), not by the
   hook (ASSUMED consequence, not tried: a page could hold nine maps where the three DLC maps are owned; for
   anybody else those entries stay locked, which is why the tool leaves them alone).
4. **'Another host is one more line of data' (5.1) does not hold for the van.** MEASURED (`vans2.py`): F06 and F08
   have helicopters and no animated van at all; F04, F05, F09 have the same van template as F07 but
   `van_prepare` looks its nodes up by F07's names (`F07_Escape_Vehicle_01` is not in F05's file) and its
   constants (`BOARD_BACK` 337, the leg frames) were measured on F07's keys only. Under F08 - the host the
   Havana agent built - there is no van to lay; under F05 the van code needs its names and measurements redone.
   So the third way out of the chunk table costs the escape as well.
5. **Is a 'generic' step tied to M09 names?** Yes in four places, all small: `kl_fa_bots_dyn` (two chains ->
   `kl_fa_bots_rt`), `kl_fa_loot.survey` / `walk` (defaults from `kl_fa_author`), `kl_map_escape.van_prepare`
   (imports `kl_fa_author`), `kl_fa_talk.BLAST_TIMER` (F07's `RivalMercVan!Timer` by name). `kl_fa_bots`,
   `kl_fa_cover`, `kl_map_guns`, `kl_chars`, `lighten` hold no map name outside their option tables (grep).
6. **The clone path is sounder than the report could show** (11.1: no ZBoxPrimitive or ZGROUP of F07 has a model,
   and several hundred such clones are in each build on the tab). What has not run is a clone the PLAYER fires
   (`TriggerBox`, `OnlineGamePlayTrigger`, `KillBox`, `LevelBound`): the report says so.

### 11.5 Could not be verified

- **A level with no `FFCoverList`.** READ kl2.exe (`cov15a0.py`, `cov_callers.py`): the pointer is game data
  +0x15a0, cleared by the constructor (0x553de4), set at 0x668346; the getter 0x713130 has 108 direct callers,
  40 of which test the result within four instructions and 68 do not (some of those are guarded by a cover
  index of -1, e.g. 0x784460; others call list methods on the result at once, e.g. 0x45feac, 0x6b74b6). Whether
  one of the unguarded paths is reached without a list was NOT established by reading. The fix of 5.5 makes the
  question moot.
- **`kl_chars.py compact` in the game** - nobody has loaded one; and whether a hook file besides KLWardrobe.ini
  and KLGuns.ini holds a chunk index was not read.
- **The effort figures** (0.6, 0.25 - 0.4, 0.5): estimates. One reason to doubt the low end: Retomoto's log in
  CLAUDE.md is mostly LIVE iteration with the owner (the blast delay three times, the loot's reach, the van's
  lane twice, guards that hit during the countdown, bots that die in the boardroom), and that recurs per place
  whatever the tool looks like.
- **`kl_str.py need` for all thirteen levels (735.8) and `streamsum.py`'s 352.5** - read from the first agent's
  outputs; my two runs (459.4 and 351.3) are consistent with them. Where the engine seeks in a stream file past
  2 GB: not read by anybody.
- **`measure.py`'s 'first-timers on the kept side' for the six levels other than M08_A**, the undrawn materials
  and the environment notes of 5.8: read from the trial logs, not re-derived.
- **Menu headroom under the 5,096 cap**, and everything the report itself lists in section 8.

### 11.6 Scratch files of this section (G:/kl_scratch/cfa_tooling_v2/)

`readres.py` (-> `readres.txt`), `cover2.py`, `nav2.py`, `nav3.py`, `mat2.py`, `mat3.py`, `hosts2.py`, `built2.py`,
`actors2.py`, `squads2.py`, `orph2.py`, `left2.py`, `rooms2.py`, `menu2.py`, `pics2.py`, `boxes2.py`, `vans2.py`,
`clash2.py`, `coverfix.py`, `cov15a0.py`, `cov_callers.py`, each with its `.txt` output; `build_M05_A.log`,
`build_M06_A.log`, `coverfix_M06_A.log`, `coverfix_M03_A.log`, `need_seven.txt`, `need_six.txt`. Builds:
`<work>/build/cfa/tooling/v2/` (four folders, result.json + log.txt + graft.txt; no archive left).

## 12. Gap closed: the finishing chain past compaction (2026-10-11, agent cfa-fill3)

The critic's gap: the finishing chain had never been run past compaction, three places had never been built with
their enemies, the install gate (`kl_maps.audit`) could not pass a compacted build, and the second shader-cache
pass was unrun everywhere. This section runs the whole chain on prison, Havana and park: thirteen chains, and
the gate twice on a map of the tab.
OFFLINE: nothing was loaded in the game, no tool file was edited (every change to a tool's behaviour is a wrapper
in my own process), nothing installed, nothing committed. `<s>` = `G:/kl_scratch/cfa_fill3`, `<b>` =
`<work>/build/cfa/fill3` (result.json / log.txt left in each folder; every archive deleted: MEASURED
`find <b> -type f -size +1M` prints nothing). Labels as in the rest of the report.

### 12.0 Short answers

1. **The chain runs to its end on all three places, with their enemies in**: build -> `lighten trim,slim,fxc` ->
   wardrobe -> `compact` -> gun looks -> `lighten --load fxc` (-> `--load wav`). No tool faults on a compacted
   build; `kl_impact`, `kl_map_guns.py check`, `kl_chars.py check` and `kl_maps.py preflight` all run on it.
2. **The prison fits the chunk table only with the 8-mask wardrobe** (what the tab's four Dead Men maps have):
   65,509 entries, 4,123 under the tools' line. With the four Payday 2 plates (12 masks, what the tab's Retomoto
   has) it ends at **70,925: 1,293 OVER the tools' 69,632** (2,803 under the game's 73,728). Two plates fit
   (68,217); three leave 61 entries. The '63,528' this study planned with had no plate, no enemy and none of F07's
   police in it (12.2, 12.3).
3. **Havana (M11_B) fits both ways**: 60,902 (8 masks) / 66,318 (12 masks, 3,314 spare). It has the heaviest
   model file of anything built so far: 91.6 / 93.0 MB (the tab's Retomoto: 79.9).
4. **The park needs no compaction**: 54,263 entries with everything on it, .prm 58.0 MB (8 masks) / 59.2 (12) -
   not the 'about 52 MB' the study assumed.
5. **Head count** with the place's own squads + F07's 14 police squads + the seven AI heisters, counted in the
   built scenes: prison 59, Havana 61, park 45 (Retomoto on the tab: 99, by the same script). The prison with ALL
   29 squads that pass the keep rule: 112.
6. **The install gate has three holes on this chain, not one** (12.7): the first build's chunk line in
   result.json (copied by `audit` AND by `preflight`), and steps.json, which neither `kl_chars.py compact` nor
   `kl_graft.py lighten` brings up to date. With each one closed from outside, a compacted, gun-looked, twice-
   lightened build of a map that was READY before passes `kl_maps.audit` at every step (control: the tab's bank).
7. **Gun looks cost 503 entries on a compacted build and 212 on any other** - not '59 - 94'. Compaction has to come
   first for a second reason nobody had met: on a build past the game's table `kl_map_guns` stops with an
   exception (12.4).
8. **The second shader-cache pass works**: 242 -> 121..125 entries, 17.76 -> 8.80..9.17 MB, the .fxc is the only
   member that differs, no material loses an effect. With it the five load blocks are 166 (prison), 171 (Havana)
   and 137 MiB (park) against Retomoto's 173.4 as installed and stock F01's 137.0; without it prison and Havana
   stand at 175 and 179 (12.5).

### 12.1 What was built, and how

- `<s>/keep_build.py <out> <level> A|B [--all-squads]` = the outside patch of
  `G:/kl_scratch/cfa_bank/skeptic/build_squads.py` made general (READ that file): `kl_maps.campaign_drop` leaves
  the named squads on the map side, `kl_graft.DeadMen` runs `kl_fa_author.strip` on them, then `kl_maps.one(...,
  campaign=True, keep=True)`. The squads are the place reports' own: prison 7 squads / 25 actors (prison 4.3:
  `06_CellblockB!Squad_Upper_Walkways`, `Squad_Walkways01`, `Squad_Walkways02`, `Squad_SWAT_StormBlockB`,
  `07_Birdcage!Squad_Birdcage_Ledge#02`, `Squad_ExitTower`, `08_Escape!Squad_Ground#01`), Havana 13 / 27
  (`060_CapitolioSquare!Enemies!*` 11 / 24 + `070_CapitolioInside!Enemies!*` 2 / 3), park 4 / 11
  (`Gameplay!Enemy!*`). MEASURED `python <s>/plans.py M08_A M11_B M06_A` (`plans.txt`): those are exactly the squads
  of these prefixes that pass `kl_fa_author.squad_plan`'s rule; 29 / 78, 26 / 55 and 4 / 11 pass it on the whole level.
- **Variant A** = those squads only (what the bank's and the club's second agents measured). **Variant B** = A +
  the HOST side of a Fragile Alliance layer as Retomoto keeps it, wrapped into `kl_fa.host_keep`: `kl_fa_author.KEEP`
  (FASpecials!, Specials!, the escape setup, the three vans, the ROLE objects), `kl_fa_street.KEEP` (F07's 14
  police squads = 27 actors, the wave boxes), F07's seven AI-heister squads (`Gameplay!merc_bot_squad!*`), minus
  `kl_fa_author.DROP`; and fix A (the cover list) in memory. MEASURED (`s1_build.log` of every B chain): 'host
  side: kl_fa.host_keep 7 names + 312 of F07 ... (1836 nodes)'. NOTHING is re-placed or wired: the host objects stand
  at F07's coordinates. B exists because **compaction drops what no entity names**: without F07's police, vans and
  spawn objects in the scene their models are dead and leave the count (12.2). B is the number to plan with.
- The chain: `sh <s>/chain.sh` / `chain2.sh <key> <level> <A|B> [noplates] [nocompact] [gunsfirst] [allsquads]`
  (READ the files: each step is the stock command; after each step `<s>/measure.py` reads the WRITTEN archive -
  member sizes, the .prm header's count, the .WAV beside it, and with `--scene` the classes of the built scene).
  Control of the measuring script: the tab's Retomoto `<work>/build/z_route/retomoto_full` gives 65,331 entries,
  26,991 entities, 99 actors (65 campaign + 27 F07 police + 7 bots), 55 squads - the figures this report already
  has (5.1, 5.4).
- Every build: 0 dangling paths. `verify` problems of a B build: the chunk line (prison, Havana), 'N stream clips
  are not in the merged stream file' (prison 20, Havana 7, park 0) and 'no loot' - nothing else; an A build adds
  the nine findings of a level without a layer (MEASURED, `s1_build.log`).

### 12.2 The chunk table, step by step

MEASURED (`<s>/table.txt` TABLE 1 and 3, written by `python <s>/table.py` from each chain's `results.jsonl`).
'12 masks' = `kl_chars.py wardrobe --plates=wolf,dallas,chains,hoxton`, '8 masks' = without `--plates`. On the tab
only Retomoto has 12 (MEASURED `grep Masks <work>/build/z_route/*/KLWardrobe.ini`: M01 M02 M03 M06 `Masks=8`,
retomoto_full `Masks=12`).

| chain | kept | actors in the scene | entities | as built | after compact | after gun looks | against 69,632 |
|---|---|---:|---:|---:|---:|---:|---|
| prison A, 8 masks | 7 squads | 25 | 23,392 | 79,385 | 63,903 | 64,406 | fits, 5,226 spare |
| prison A, 12 masks | 7 squads | 25 | 23,392 | 79,385 | 69,319 | 69,822 | **over by 190** |
| **prison B, 8 masks** | 7 squads + host layer | 59 | 25,228 | 79,385 | 65,006 | **65,509** | fits, 4,123 spare |
| **prison B, 12 masks** | 7 squads + host layer | 59 | 25,228 | 79,385 | 70,422 | **70,925** | **over by 1,293** |
| prison B, 8 masks, all squads | 29 squads + host layer | 112 | 25,476 | 79,616 | 65,226 | 65,729 | fits, 3,903 spare |
| Havana A, 12 masks | 13 squads | 27 | 19,331 | 74,763 | 64,712 | 65,215 | fits, 4,417 spare |
| **Havana B, 8 masks** | 13 squads + host layer | 61 | 21,167 | 74,763 | 60,399 | **60,902** | fits, 8,730 spare |
| **Havana B, 12 masks** | 13 squads + host layer | 61 | 21,167 | 74,763 | 65,815 | **66,318** | fits, 3,314 spare |
| park A, 12 masks | 4 squads | 11 | 19,229 | 54,051 | 44,002 | 44,505 | fits |
| park B, 12 masks | 4 squads + host layer | 45 | 21,066 | 54,051 | 45,105 | 45,608 | fits |
| **park B, 12 masks, NOT compacted** | 4 squads + host layer | 45 | 21,066 | 54,051 | - | **54,263** | fits, 15,369 spare |
| **park B, 8 masks, NOT compacted** | 4 squads + host layer | 45 | 21,066 | 54,051 | - | **54,263** | fits, 15,369 spare |

What the parts cost (all differences of rows above or of this report's earlier numbers):
- **Campaign squads are cheap.** As built: prison + 380 entries / + 3.6 MB of .prm (79,385 / 67.8 MB against the
  critic's bare 79,005 / 64.2), Havana + 309 / + 3.0 MB (74,763 / 72.0 against 74,454 / 69.0 of 5.1, 5.2), park
  + 91 / + 0.5 MB (54,051 / 80.0 against 53,960 / 79.5). All 29 prison squads instead of 7: + 231 as built, + 220 at
  the end, + 1.5 MB. The earlier assumption 'a few hundred entries and 4 - 8 MB each' holds for the entries and
  is high for the megabytes.
- **The host's layer costs nothing as built and 1,103 entries once the build is compacted** - the same on all
  three (70,422 - 69,319; 65,815 - 64,712; 45,105 - 44,002), + 3.2 MB of .prm (71.0 against 67.8 lightened: F07's
  police, dog, vans are no longer emptied by the trim) and + 18.7 MB of .TEX after `slim` (254.3 against 235.6).
  Every compacted number measured before today is too low by this (the critic's 63,528, the synthesis' 58,992).
- **The four plates cost 5,416 entries** (12.3): on an uncompacted build they vanish into dead indices (the
  park: 54,051 before and after either wardrobe); on a compacted one they are all in the count.
- The wardrobe step exits 1 on prison and Havana (its only PROBLEM is the chunk line of the still uncompacted
  file) and writes the build all the same; `compact` exits 1 on the park for a known lamp material of the MAP
  ('material 910 ... asks for a shader the .fxc lacks: glow30.fx MESH_WEIGHTED', 'the base's own included'). A script
  that stops on a non-zero exit stops at both.

### 12.3 The wardrobe's parts, in entries (prison B)

MEASURED (`python <s>/wardvar.py <lightened prison B>` -> `wardvar_prison_B.txt`: `kl_chars.wardrobe` then
`kl_chars.compact_level` in memory per variant, + 503 for the gun looks of 12.4):

| plates | armour levels | indices the wardrobe takes | compacted | + gun looks | against 69,632 | .prm MB compacted |
|---:|---|---:|---:|---:|---|---:|
| 0 | 0,1,2,3 | 15,509 | 65,006 | 65,509 | fits, 4,123 spare | 86.5 |
| 1 | 0,1,2,3 | 16,879 | 66,360 | 66,863 | fits, 2,769 | 86.8 |
| 2 | 0,1,2,3 | 18,249 | 67,714 | 68,217 | fits, 1,415 | 87.1 |
| 3 | 0,1,2,3 | 19,619 | 69,068 | 69,571 | fits, **61** | 87.5 |
| 4 | 0,1,2,3 | 20,989 | 70,422 | 70,925 | **over by 1,293** | 87.9 |
| 4 | 0,3 | 20,688 | 70,127 | 70,630 | over by 998 | 81.3 |
| 4 | 0 | 20,328 | 69,767 | 70,270 | over by 638 | 75.9 |
| 0 | 0,3 | 15,224 | 64,727 | 65,230 | fits, 4,402 | 79.9 |
| 0 | 0 | 14,872 | 64,375 | 64,878 | fits, 4,754 | 74.5 |

- A plate = 1,354 entries (1,334 of them mesh objects: 'plate 1 Wolf: ... 4 geometry sets, 1334 objects' in
  `s3_ward.log`). The chain-built 4-plate build and this table's row agree (70,422 / 70,925).
- `--armour` is a lever for the megabytes, not for the table: leaving two armour levels out saves 295 entries and
  6.6 MB, leaving three out 655 and 12.0 MB.
- So for the prison: **8 masks, or two plates at most**. Three plates leave 61 entries before loot props (about 20
  chunks: 3.5) and whatever a later step adds. 'Over the tools' line' is not 'over the game's table': 70,925 leaves
  2,803 slots and the most run-time chunks ever seen is 713 (READ re/prm_limit.md) - but the 4,096 is the
  margin every build that ran has kept, and nothing bounds the run-time chunks. Not a place to be first.

### 12.4 Gun looks on a compacted build, and why the order cannot be turned

- MEASURED on every compacted chain (`s5_guns.log`): '.prm: 0 of N chunks are dead', then **+ 503 entries**, + 0.9
  to 1.0 MB of .prm, + 8.1 MB of .TEX; .ANM, .fxc, .WAV unchanged; `kl_map_guns.py check` 0 problems, `kl_impact`
  0 problems wherever the count fits. The critic's numbers, reproduced on ten builds.
- MEASURED on the two uncompacted park chains: **+ 212** (54,051 -> 54,263; '5028 of 54050 chunks are dead'), and
  the tab's Retomoto has the same 212 (65,331 against 65,119). The '59 - 94 chunks' of 3.5 step 4 is the first
  version of the tool, before the looks were turned into the Dog Days hold (READ tools/kl_map_guns.py docstring,
  'SECOND PASS': '3 chunks a part'). Use 212 for the bank and the club, 503 for prison and Havana.
- **Guns first, then compact** (`chain2.sh prison M08_A B noplates gunsfirst`): on the uncompacted prison
  (79,597 entries with the looks) `kl_map_guns.py build` stops with `ValueError: KLGuns.ini: 79597 is not a chunk
  count the game's table holds` (READ tools/kl_map_guns.py 698-699: `if not 0 < entries <= 0x12000`) AFTER it has
  written the archive and BEFORE KLGuns.ini, guns.json and map_guns.json: a folder with gun models and no gun file.
  Compacting that archive gives 65,217 - **292 fewer than compact-then-guns (65,509)**, the six stock gun models
  the looks replaced being dead by then. So the order of 3.5 is forced twice over (the tool refuses a count past the
  table; `compact` does not rewrite KLGuns.ini), it costs 292 entries, and turning it round would not rescue the
  12-mask prison either (70,925 - 292 = 70,633).
- Which per-level files of the hook hold a chunk index (11.5 left this unread) - READ klhook/klchar.c 211,
  klhook/klgun.c 189-200, klhook/kljoin.c 105-127, and a written `KLTalk.ini`: KLWardrobe.ini (`Root=`, rewritten by
  `compact`) and KLGuns.ini (`Root=`, `Entries=`, written after it). KLJoin.ini (box, entry, name, tolerance) and
  KLTalk.ini (character numbers, .LOC keys, times) hold none.

### 12.5 Weights: the finished folders and the five load blocks

MEASURED (`table.txt` TABLE 2; the blocks as CLAUDE.md 'BUDGET for the builders' counts them: 32.0 MiB scratch,
.fxc + 0x60000, .prm + 0x60000, .ANM + 0x60000, the whole .WAV; MiB). 'Final' = after the second shader-cache pass.

| folder | archive MB | .prm MB (MiB) | .TEX MB | .fxc MiB | .ANM MiB | .WAV MiB | five blocks MiB | with `--load wav` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prison B, 8 masks | 238.1 | 87.5 (83.4) | 283.3 | 8.39 | 20.61 | 20.68 | **166.2** | 156.7 |
| prison B, 12 masks | 240.8 | 88.9 (84.8) | 286.1 | 8.39 | 20.61 | 20.68 | 167.6 | - |
| prison B, 8 masks, all 29 squads | 240.1 | 89.0 (84.8) | 284.7 | 8.39 | 20.90 | 20.68 | 167.9 | 158.4 |
| Havana B, 8 masks | 270.3 | 91.6 (87.4) | 295.4 | 8.74 | 20.61 | 20.78 | **170.6** | 161.1 |
| Havana B, 12 masks | 273.1 | 93.0 (88.7) | 298.2 | 8.74 | 20.61 | 20.78 | 172.0 | - |
| park B, 8 masks, not compacted | 213.7 | 58.0 (55.3) | 253.9 | 8.49 | 20.57 | 19.43 | **136.9** | 127.3 |
| park B, 12 masks, not compacted | 216.4 | 59.2 (56.5) | 256.7 | 8.49 | 20.57 | 19.43 | 138.1 | - |
| for scale: Retomoto as installed on the tab | 219.0 | 79.9 (76.2) | 264.9 | 16.94 | 20.64 | 26.51 | 173.4 | - |
| for scale: the Fragile Alliance bank on the tab (`z_route/M03`) | 200.8 | 62.6 (59.7) | 237.6 | 16.94 | 21.17 | 21.62 | 152.5 | - |
| for scale: stock F01 / F07 / L10 (`stock_blocks.py`) | 217.5 / 200.2 / 260.4 | 66.6 / 63.6 / 66.8 | 288.4 / 281.0 / 391.4 | 5.92 / 7.70 / 6.41 | 19.75 / 20.57 / 22.83 | 14.68 / 17.45 / 10.60 | 137.0 / 139.5 / 136.6 | - |

- In large blocks every one of the three is at or under the tab's Retomoto - **but only with the shader cache cut**,
  which no installed build has (both tab builds above carry the whole 16.94 MiB cache). Without the second pass
  the sums are 174.8 (prison B, 8 masks) and 180.2 MiB (Havana B, 12 masks): 1.4 and 6.8 over Retomoto.
- **The model file is the heavy block**: prison 87.5, Havana 91.6 - 93.0 MB. The tab's heaviest is 79.9; 96.5 MB
  loaded once, before the hook's reserve (5.2). Per step (TABLE 3): the wardrobe adds 16.3 MB (8 masks) / 17.7 (12),
  compaction takes 0.8 off, the gun looks add 1.0. The lever that exists is `--armour` (12.3): `--armour=0,3` would
  put the prison at about 81 and Havana at about 85 MB (ARITHMETIC on 12.3's 6.6 MB; not built for Havana).
- .TEX: prison 283 MB, Havana 295 - 298 MB - at stock F07's 281 and above the tab's 205 - 265 (the host's layer keeps
  18.7 MB of F07's textures whole; the gun looks add 8.1; the wardrobe 21 - 24). CLAUDE.md asks for 'near the stock
  290 MB': Havana is 5 - 8 over.
- `lighten --load wav` (`kl_wavslim`): '967 in-memory clips, 349 reached; 151 dropped (10.0 MB)', .WAV 21.7 -> 11.7 MB
  on the prison, 21.8 -> 11.8 on Havana, 20.4 -> 10.4 on the park (`s8_wav.log`); `kl_snd.verify` inside the audit
  passes on such a file in the control of 12.7. NOT LOADED LIVE, as the tool says.
- Entities 25,228 (prison B) are under the 26,991 that ran; its 61 rooms are a first for a graft, as 5.4 has
  it. `kl_maps.py preflight` on the final prison folder: RISK = the four controller kinds no stock level
  runs (`EffectDmgBox` x15, `LightToggle` x7, `AnimSequence` x5, `ZHingeConstraint` x1), one `CCheckInside` value
  and 'no loot'; NOTE 'larger than any Dead Men build that ran live: entities 25228 (19827), rooms 61 (20),
  nav_bytes 354868 (186672)' (`prison_B_np/s7_preflight.log`).

### 12.6 The head count

MEASURED (`measure.py --scene`, the `ZFFActor` nodes of the built scene by the subtree they stand in):

| place | campaign squads kept | F07 police (14 squads) | AI heisters | actors | squads | players |
|---|---:|---:|---:|---:|---:|---:|
| prison, the round's 7 squads | 25 | 27 | 7 | **59** | 28 | 16 |
| prison, all 29 squads that pass the rule | 78 | 27 | 7 | **112** | 50 | 16 |
| Havana (M11_B), 13 squads | 27 | 27 | 7 | **61** | 34 | 16 |
| park, 4 squads | 11 | 27 | 7 | **45** | 25 | 16 |
| Retomoto on the tab (ran live) | 65 | 27 | 7 | 99 | 55 | 16 |

- The police a layer keeps are 27 actors, not F07's 43 (MEASURED `python <s>/host.py` -> `host.txt`: F07's 43 are 27
  in the 14 squads of `kl_fa_street.SQUADS`, 7 rival mercenaries, 7 AI heisters, 2 civilians). So 5.4's '43 police
  + 78 + 7 + 16 players = 144 people' is 112 actors + 16 players = 128 for the prison at its fullest, and **59
  for the round the prison report describes**. All three rounds are well under Retomoto's 99; only 'every squad
  the rule lets through' on the prison goes past it.
- NOT in these counts: squads a place wants AFTER a tool change (rule G of the synthesis: the prison's 15 without
  a rout, Havana's bunker and loyalists, the park's ring police and five garden squads). The park at its fullest
  plan (25 yakuza + 15 police / SWAT: park 4.2) would be 40 + 27 + 7 = 74 (ARITHMETIC).

### 12.7 The install gate

READ tools/kl_maps.py: `audit` copies result.json's `problems` into its 'bad' list as 'verify: ...' (1333-1337);
`preflight` turns the same list into 'CRASH verify kl_graft.verify reported N problems (result.json)' (622-623), and
`audit` counts a preflight CRASH as bad (1449); `audit` refuses a folder whose members differ from steps.json's
'final' (1338-1350). result.json and steps.json travel with every step (`kl_chars.Lv.side`, kl_chars.py 372-374,
416-418; `kl_graft.relight`, kl_graft.py 699-702). `kl_map_guns._steps` (811-828) is the only step after the
wardrobe that records itself.

MEASURED (`<s>/audit_fix.py <folder>`: the audit as the tools have it, then with the first build's chunk line
re-evaluated by `kl_impact.chunk_limit` on the .prm in the archive NOW and written into result.json;
`<key>/s5_audit.log`, `table.txt` TABLE 4):

| chain | as the tools have it | chunk line re-evaluated | what is left |
|---|---|---|---|
| prison B, 8 masks | FAIL 4, one of them '79385 chunk-table entries, the game's table has 73728' on a file that has 65,509 | FAIL 3 | 'sound: 20 stream clips are not in the merged stream file' (of the first build), 'no loot' twice (first build + fresh) |
| prison B, 12 masks | FAIL 5 | FAIL 5 | as above + the chunk line twice, now TRUE (70,925; once re-evaluated, once from `kl_impact.check`) |
| Havana B, 8 or 12 masks | FAIL 4, incl. '74763 ...' on a file that has 60,902 / 66,318 | FAIL 3 | '7 stream clips', 'no loot' twice |
| park B, with or without compaction | FAIL 2 | FAIL 2 | 'no loot' twice (never over the table: no stale line) |
| any A build | FAIL 18 - 21 | FAIL 18 - 21 (one fewer where the count now fits) | the nine findings of a level without a layer, twice, + the lines above |

So after the re-evaluation nothing compaction made is left: what remains is the stream file (work K) and the loot
(the layer). That the gate can then really PASS was shown on a map that passed before (`sh <s>/gate.sh`,
`gate2.sh`; control = `<work>/build/z_maps/M03`, the Fragile Alliance bank of re/maps.md 14, READ only; outputs
`<b>/m03gate*`, logs `<s>/gate.out`, `gate2.out`):

| step on the READY folder | `kl_maps.audit` as the tools have it | with the step recorded in steps.json (`<s>/steps_fix.py`, the logic of `_steps`) |
|---|---|---|
| `kl_chars.py compact` (62,680 -> 47,163 entries) | **FAIL**: 'steps: the archive or a file beside it changed after the steps were recorded' | PASS, 0 known |
| `kl_map_guns.py build` (47,666) | PASS - its `_steps` takes compaction's changes for its own ('guns: .MAT .TEX .gms .oct .prm .prp') | PASS |
| `kl_graft.py lighten --load fxc` | **FAIL**: the same 'steps:' line | PASS |
| `kl_graft.py lighten --load wav` | **FAIL**: the same | PASS (`kl_snd.verify` 0 on the slimmed bank) |

The control ends at 47,666 entries, .prm 60.6 MB, five blocks 133.0 MiB (as installed: 152.5) with every checker
of the audit at 0: no checker finds anything wrong with a compacted level. (Whether the GAME does is work I.)

**The three holes, and the fix for whoever holds the files (NOT applied; each is what my wrappers do):**
1. `tools/kl_chars.py`, the `compact` command (1710-1723), after `lv.write`: rewrite the chunk line of the carried
   result.json - `res['problems'] = [x for x in res['problems'] if not (str(x).startswith('.prm:') and
   'chunk-table entries' in str(x))] + kl_impact.chunk_limit(lv['.prm'])`. This one line of data cures `audit`'s
   'verify:' line AND `preflight`'s CRASH; making `audit` skip the line instead (the other fix the critic named)
   leaves `preflight`'s count wrong.
2. the same command: record the step in steps.json when the folder has one (`kl_map_guns._steps` is the pattern;
   it belongs in `kl_maps` next to `member_ids` so that three tools can call it).
3. `tools/kl_graft.py relight` (680-712): the same call - today the LAST step of the chain (`--load fxc`, `--load
   wav`) makes a READY folder fail the gate, compaction or not. Nobody had met it because no finished folder has
   been through the second pass.
Not a hole but worth knowing: 'verify: sound: N stream clips ...' is also a first-build line; it goes only with a
rebuild after the stream file has the clips (work K before the build, not after).

### 12.8 The second shader-cache pass

READ tools/kl_chars.py 738-741 (`put`: `fxc = T.merge_fxc(fxc, union.fxc)`): the wardrobe merges the shared cache
back so that the heroes' materials find their effects - MEASURED on every chain: .fxc 8.80 MB after the first
`lighten ...,fxc`, 17.76 MB after the wardrobe. MEASURED (`<s>/fxc_check.py <before> <after>` on the final step of
13 chains, `<key>/s6_fxccheck.log`): `lighten --load fxc` on the build WITH wardrobe and gun looks -> 242 -> 121
entries / 8.80 MB (prison), 125 / 9.17 MB (Havana), 122 / 8.90 MB (park); the .fxc is the only one of 31 members
whose CRC or size differs, the 18 files beside the archive, KLWardrobe.ini and KLGuns.ini are byte for byte the
same; `kl_light.missing_shaders` names the same materials before and after (0 on prison and Havana; 1 on the park,
the map's own rice lantern, in both); `kl_chars.py check`, `kl_impact`, `kl_map_guns.py check` say after it what
they said before. On the prison and Havana the second pass keeps exactly the effects the first one kept (120 for
1,294 materials then, 120 for 1,325 - 1,329 now; Havana 124 / 124); on the park it keeps THREE MORE (119 -> 122
effects, 8.72 -> 8.90 MB): there the wardrobe or the gun looks ask for effects the map did not, which is what the
wardrobe's merge is for - so the order 'cut, wardrobe, gun looks, cut again' is the right one and the first cut is
only there to weigh the intermediate steps. NOT LOADED LIVE (no build with a cut cache has run: READ kl_graft.py
490-492).

### 12.9 What this corrects

In this report:
- **3.5 step 3 / 4**: the order that was measured, and the better one, is wardrobe THEN compact: 63,528 against
  the 66,126 of step 4's arithmetic. The 2,598 between them are the eight stock heister models the wardrobe
  re-points away from, dead by the time compaction runs (MEASURED on the uncompacted park B, 8 masks:
  `park_B_np_nc/s3_ward.log` '7846 still free' after the wardrobe, `s5_guns.log` '10444 of 54050 chunks are dead'
  one step later); `compact` rewrites KLWardrobe.ini either way. Step 4's 'gun looks (59 - 94 chunks)' is 212 on an uncompacted
  build and 503 on a compacted one; '15,509 chunks' is the 8-mask wardrobe, the 12-mask one takes 20,989.
- **3.5 step 5 / 6**: after the gun looks comes `lighten --load fxc` (and `wav` if wanted), and after it the gate
  fails until the step is recorded (12.7).
- **5.1 table, 'after compact'**: the prison's 50,617 and Havana's 'about 46,000' are bare levels. Finished, with
  the round's squads, the host's layer and gun looks: prison 65,509 (8 masks) / 70,925 (12), Havana 60,902 /
  66,318.
- **5.2**: 'the wardrobe adds about 15.5 MB' is 16.3 (8 masks) / 17.7 MB (12) here; the single levels' finished .prm
  is 87.5 - 93.0 MB for prison and Havana, not 'about 60'.
- **5.4**: the police a layer keeps are 27, not 43 (12.6).
- **11.5** 'whether a hook file besides KLWardrobe.ini and KLGuns.ini holds a chunk index was not read': read,
  none does (12.4).
In re/campaign_fa.md (marked there 'corrected after the critic'): the prison, Havana and park rows of the table in
section 1, 2.1 item 10, 3.3 steps 7, 11 and 12, section 5 items 10 and 11.

### 12.10 Still not known

- Everything here is offline. A compacted level has not loaded (work I); a cut shader cache and a slimmed .WAV
  have not loaded; a .prm of 87 - 93 MB has not loaded with the reserve (96.5 MB did once without it).
- The steps AFTER the gun looks on the tab's maps - AI heisters, cover boxes, routes, talk, Bain, loot props - were
  not run on a compacted build: they need a placed layer. They add nodes, and a few chunks (loot props about 20:
  3.5); the cover step's borrowed box is the model of an entity of the build (READ tools/kl_fa_cover.py 521-558),
  so it survives compaction. ASSUMED small; the prison's 4,123 spare entries (8 masks) cover it, the 61 of a
  3-plate wardrobe do not.
- Variant B's host objects stand at F07's coordinates: its `kl_fa.check` verdict ('no loot' only) says the objects
  are THERE, nothing about the round. Squads the places want after tool work G are not in the weights.
- How many chunks the game makes at run time with 59 - 112 actors: the 713 seen are from maps of 27 - 99 actors
  (READ re/prm_limit.md); the tools' 4,096 is a margin, not a bound.

### 12.11 Scratch files (`G:/kl_scratch/cfa_fill3/`)

`keep_build.py` (the squad-keeping build, variants A / B), `chain.sh`, `chain2.sh` (the chain; `chain2` adds
preflight and the .WAV pass), `batch1.sh`, `batch2.sh`, `measure.py`, `table.py` -> `table.txt`, `audit_fix.py`,
`audit_only.py`, `steps_fix.py`, `gate.sh`, `gate2.sh` -> `gate.out`, `gate2.out`, `fxc_check.py`, `wardvar.py`
-> `wardvar_prison_B.txt`, `plans.py` -> `plans.txt`, `host.py` -> `host.txt`, `stock_blocks.py` ->
`stock_blocks.txt`, `reference.jsonl`; per chain `<key>_<variant>[_np][_nc][_gf][_all].out` and a folder of the
same name with `s1_build.log` .. `s8_wav.log`, `s5_audit.log / .json`, `s6_audit.log / .json`, `results.jsonl`.
Chains: `prison_A`, `prison_A_np`, `prison_B`, `prison_B_np`, `prison_B_np_gf`, `prison_B_np_all`, `havana_A`,
`havana_B`, `havana_B_np`, `park_A`, `park_B`, `park_B_nc`, `park_B_np_nc` (`np` = 8 masks, `nc` = not compacted,
`gf` = guns first, `all` = every squad the rule passes), `m03gate`, `m03gate2`, `wardsrc_prison`.
