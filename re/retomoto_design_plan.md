# Retomoto Tower level design: the plan for the next session (blueprint)

2026-10-09, cloud session (no game files; branch `claude/charming-johnson-xblvr1`, level with `rtp-schemas`
at 0191832). The owner asked for the Retomoto Tower level design from the concept in CLAUDE.md ("Owner's
design for it"). A multi-agent workflow was started and then STOPPED after a few minutes at the owner's
request (usage window). Nothing of it reached a result: two of six readers had begun, none had returned.
This file is what the next session needs to continue without re-deriving anything.

## 1. What already exists (read before designing)

| what | where | state |
|---|---|---|
| survey of M09_A (tower) and M09_B (lobby, street) with coordinates, rooms, statues, squads, music | `re/retomoto.md` (906 lines) | offline, verified on the files |
| first-pass FA layer: spawn row at the window, blast at round start, 15 statue stacks + 6 boardroom stacks gated on two squads, JumpPoint join tower car -> lobby car, 10 B squads start at the entrance, F07's three vans re-laid on the road, bounds | `tools/kl_fa_author.py` + `re/retomoto_fa.md` | built offline, `verify` 2 known problems, `kl_fa.check` 0 CRASH / 0 BROKEN; NEVER run in the game |
| the two-part build (F07 + M09_B + M09_A), nav_join, name clashes, world positions | `re/maps.md` section 5, 6 | offline |
| what a round needs, how F01 paces its waves, "loot when a group is dead" | `re/fa_gamemode.md` 2, 4, 5 | read from stock |
| what the live bank round proved (loot by E, clock, score page, round 2; escape not reached) | `re/fa_round.md` 6 | LIVE |

## 2. The gaps between the owner's concept and the layer as built

1. **The street is not "Heat" yet.** Only the campaign's 10 B squads (20 police) start, all at once, when a
   criminal passes the entrance. No waves along the road, none of F07's 14 police squads is used
   (`re/retomoto_fa.md` section 5 "Not built"). Next step named there: F07's `Gameplay!020_Loot!*` squads
   moved as rigid groups to the first road block (z 3602..3911), actors on campaign actor positions, started
   by MERCONLY trigger boxes as the criminals advance down the road (the F01 idiom, `re/fa_gamemode.md` 2:
   `tbPlatform#01_MercOnly` -> `10_Defend` routs; `tbStreet_RespawnOnly` for the police side).
2. **The tower fight is one wave.** All 23 kept A squads (43 actors) are started by the blast timer. The
   owner's "fight through" reads better as staged: boardroom door -> reception -> atrium 3rd -> stairs ->
   2nd -> 1st -> elevator lobby, each started by a trigger box at the step (room bounds in
   `re/retomoto.md` 1.3, stairs in the table after it).
3. **Music is silent.** The 7 clips `Music/InHouse/Japan/M09_A/*` are not in the merged `PC_Def.str`:
   `kl_audio.merge` takes `FA_FILTER` only (`tools/kl_audio.py` line ~157; patch 3 in `re/maps.md` 7).
   Also missing: `Bomb_WarmUp`, A's ambience beds, the Japanese guard / police lines (`re/retomoto_fa.md` 6).
   Two routes to play it: `Music!PlayMusic_TokyoAction` sent 'AITrigger' at the blast (built; no FA level
   has a PlayMusic: LIVE) or settings field 157 = the clip's .SND offset (needs the offset after
   `graft_audio`: three lines in kl_graft).
4. **The join is a mechanism, not yet a designed beat.** JumpPoint fired by a box in the tower car
   (`re/retomoto_fa.md` 3): instant, no fade known; who is moved online is one of three cases (3.3).
   Design to write: doors open at the blast or when the room is cleared, a delay, police following,
   AFTER_DEATH points moving from tower to street.
5. **Bounds / kill**: the window drop (the tower hangs at y 19,600 over B's square bound at y 10,373), the
   atrium void, the roof (rappel-only in the campaign), the open west side of the street (overpass, bus
   terminal). All GUESS slabs today.

## 2a. Sketch of the Heat street (for the designer; every number below is from `re/retomoto.md` 1.4 / 3.4
unless marked GUESS; nothing is built)

Geometry: the front door is at x 2600, z -7300..-5700 (centre z -6490), the forecourt runs x -50..2650,
the road is straight along z at x -5700..-300 (centre x -3000), 54 m wide, from the south bound
(z -11400..-12700) to the north bound at z 13418: 250 m of street. Cover on it today: static police cars
`V_JPN_Police_RetoFront01/02` at (38 21 -7382) / (147 21 -6408) right at the forecourt, the SWAT van
`V_JPN_SWAT_Van_South` (-2208 0 -12506), the first road block (3 cars, z 3602..3911, x -4090..-1901),
the SWAT truck `V_JPN_SWAT_North` (-3588 2 10886), the far block (4 cars, z 13131..14404). Vans stop at
z 9300 / 8500 / 7700 (GUESS, `kl_fa_author.VAN_STOP_Z`).

Zones, south to north (each a MERCONLY trigger box the criminals cross; the police side gets the same
routs from a RESPAWNONLY twin, the F01 idiom):

| zone | box centre / half (GUESS) | what starts | from where |
|---|---|---|---|
| Z0 door | (2900 400 -6500) / (300 400 800) - exists: `tbExitFinancialAlley` | the campaign's `Enemies!010_RetoBldFront!` (18 police) | forecourt, the two police cars |
| Z1 forecourt -> road | (-300 300 -6500) / (300 400 2500) | `Enemies!020_Street!` south half | the SWAT van (-2208 0 -12506), south end |
| Z2 road, z -3000 | (-3000 300 -3000) / (2700 400 400) | `Enemies!020_Street!` north half + the first F07 squads moved to the first road block (z 3602..3911) | behind the three cars, defend boxes on the car line |
| Z3 road, z 2000 | (-3000 300 2000) / (2700 400 400) | F07's remaining police squads at the SWAT truck (z 10886) and the far block | long sight line down the road: the Heat moment |
| exit | (-3000 500 7800) / (2700 900 3500) - exists: `otrExitLevel` | the van | stops 150-165 m from the door |

F07's squads: `re/retomoto_fa.md` 5 says 14 police squads tied to its alleys and the bot crew
`merc_bot_squad` (8 x 99 nodes). Keep them with `KEEP` (pattern `Gameplay!020_Loot!*` / whatever the
reader finds their names are), move each squad's top node with `place()` (rigid: its defend `Pos#nn`
boxes and actor groups are children), put the actors on the campaign's static-car line. What must be
checked first (LIVE or by reading the stock .prp on the PC): that F07's squads are top-level nodes whose
parents are identity at the origin (place() precondition), and that their routs reference nothing of
F07's map (kl_fa.repair's prune would cut it). Sirens: B's map ambience already has police megaphone
lines and a siren (`re/retomoto.md` 6). Street police respawn: move the 7 AFTER_DEATH points to the
square once the elevator trigger has fired (an `OnlineSpawnpointTrigger` only moves TEAM stages; for
Arcade / FA the points are fixed - 2 of 7 are on the square already).

## 2c. Sketch of the staged tower fight (numbers from `re/retomoto.md` 1.3 and 5; boxes GUESS)

Today all 23 kept A squads start at the blast. Staged instead, one MERCONLY box per descent step, each
starting the squads of the NEXT area so the heisters always walk into a defended room:

| step | box centre / half (GUESS) | starts (campaign area, actors kept) | room |
|---|---|---|---|
| blast | - (`AIMonitor` list 2 -> blast timer, exists) | `020_Office` (boardroom, 7 kept) + `030_Reception` (12) | Office_301, floor y 20996 |
| T1 boardroom door | (3430 21200 -100) / (60 250 300) (= `SpawnpointTrigger_010_B`) | `040_Atrium_3rd` (15) | Reception_301 -> Atrium_301 |
| T2 top stairs | (-1200 21200 -1600) / (1000 300 500) at StairsTop_A (-2210..-259, z -2582..-631) | `050_Atrium_2nd` (7) | Atrium_301 |
| T3 2nd floor | (-1200 20500 1300) / (1000 300 500) at Stairs_D foot (z 731..1956) | `060_Atrium_1st` (8) | Atrium_201 |
| T4 1st floor | (-1200 19800 -1600) / (1000 300 500) at Stairs_A foot | `070_Elevators` (11, minus the arriving ones) | Atrium_101 |
| T5 elevator lobby | (2200 19800 -100) / (1000 250 1700) (= `SpawnpointTrigger_020_C`) | nothing new; the car's doors are already open | Elevators_101 |

Implementation: F07's stage triggers `SpawnpointTrigger_010_B/020_C` are `OnlineSpawnpointTrigger`
objects, not `TriggerBox`es - the wave boxes need stock F07 `TriggerBox` objects with a spare role
(the reader lists them; `tbExitFinancialAlley` is the pattern: field 14 ECPS_FA_MERCONLY, field 17 the
routs). The blast timer's field 4 then keeps only the two boardroom-side areas. Floors: 3rd y 21000,
2nd 20300, 1st 19600; stairs A/B join 1st-2nd, C/D 2nd-3rd (x -2163..-259). Police AFTER_DEATH points
(5 in the tower) are already in the elevator lobby and at the atrium lift.

## 2b. Done in this session (code)
- `tools/kl_audio.py`: `MERGE_FILTER = FA_FILTER + RETOMOTO_FILTER` is the default of `merge()`: music,
  explosion, ambience and Japanese voice prefixes. UNTESTED; check the prefixes with
  `python kl_audio.py list <DM PC_Def.str> Japan` on the PC, rebuild `PC_Def.str`, reinstall it.

## 3. How to continue: the saved workflow

`.claude/workflows/retomoto-level-design.js` is the whole plan as a Workflow script (run with
`Workflow({name: "retomoto-level-design"})` in a session where ultracode / workflows are allowed):

| phase | agents | what |
|---|---|---|
| Understand | 6 readers in parallel | fa-layer (F07's gameplay layer and how kl_fa_author keeps / moves subtrees), street-atlas (M09_B coordinates for the shoot-out zones), tower-atlas (M09_A route and trigger-box places), mechanics (field lists of every pacing controller from `re/kl2.json` + proof state), audio-music (the `kl_audio.py` patch for the 7 clips), join-net (JumpPoint, police respawn, vans, ordered live tests) |
| Design | 3 designers | the same brief from three angles: stock-faithful, cinematic / Heat, risk-first; fixed 12-section structure (0 timeline .. 11 risks), every number sourced or GUESS |
| Judge | 3 judges (owner, engineer, tester lenses) | scores, factual errors, ideas to graft |
| Synthesize | 1 | writes `re/retomoto_design.md` in the house style; section 9 = the implementation spec |
| Implement | 1 | edits `tools/kl_fa_author.py` (+ `kl_audio.py`); no new entity / controller; py_compile only |
| Review | 3 lenses x up to 2 rounds + fixer | API correctness (field indices, names), geometry (on a floor, in the room, on the road), build (verify / check still pass) |
| Critique | 1 | completeness against the owner's four bullets |

It runs with NO game files (everything from `re/*.md` and `tools/*.py`); the result still has to be built and
tested on the PC: `python tools/kl_fa_author.py test <out>` then `re/retomoto_fa.md` section 8's live order.
Without workflows: do the phases by hand in that order; the prompts in the script are the briefs.

## 4. Design decisions already taken (do not reopen without the owner)

- Both parts stay in their own coordinates (nothing re-baked); the join is the campaign's own escape
  elevator car (2974, 19600, 909) -> lobby car (6272, 560, -6305), B - A = (3298, -19040, -7214).
- No new entity and no new controller: every object is a stock F07 one re-placed and re-wired, or a kept
  campaign object (`CAMPAIGN_KEEP`).
- Host = F07 (three animated vans, `ZAnimatedVehicle`), tested slot F01, build by `kl_maps.chain`.
- Loot: statues 15 x 150,000 (GUESS), boardroom 6 x 300,000 hidden until its squads' field-8 lists have
  fired twice into a `TriggerCounter` (ASSUMPTION that field 8 is 'wiped out').

## 5. Live order that unlocks everything (from `re/retomoto_fa.md` 8, unchanged)

1 chain loads (direct boot) -> 2 boardroom state at load -> 3 hidden things have no collision -> 4 round
start blast -> 5 guards react -> 6 statue loot -> 7 main room -> 8 the join -> 9 street police and bounds
-> 10 vans -> 11 death -> police -> 12 round end. Each step's fail action is written there.
