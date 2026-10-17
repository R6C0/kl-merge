# The club (Dead Men M05_A 'The Mizuki') as a Fragile Alliance map - build notes

Map 2 of the campaign places (map 1: re/bank_campaign.md, the worked example of every step). The study:
re/campaign_fa_club.md (its section 8 and the notes 'corrected after the critic' weigh more than the first text),
re/campaign_fa.md 4.2 and G1.3 / G1.8, re/campaign_fa_tooling.md 11 - 12. Each stage appends a section here.
`<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`.

**LATER (2026-10-12): the section 'Fix after runs C0-C2' at the END of this file supersedes D1's folders (new set `C:/kl_build/c_club2` and `c_club2_music`),
the seal clock (100 s) and the bots' loot wait (18 s); read it after DELIVERY.**

**START AT THE SECTION 'DELIVERY' just below (D0 what was built, D1 the folders and every checker, D2 the round as
built and the flags, D3 guesses by cost, D4 the live order, D5 packaging, D6 not done). The stage sections after it
(T, L1, L2, L3, F, review rounds 1 and 2) are the record.**

## DELIVERY (2026-10-11 night) - start here

Written by the workflow's last stage from the files as they lie; every checker was RE-RUN on the four delivered
folders for this section (D1; the archives' sha1 were the same after the run as before). Where a stage section below
disagrees with this one, this one is later: Stage F's sha1 `9972c87e` and hold of 92 s are SUPERSEDED by the review
rounds (club 1380209c, hold 83 s). NOTHING OF THIS MAP HAS EVER RUN IN THE GAME and no picture of it was ever rendered.
Nothing is installed. `<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`,
`<c_club>` = `<work>/build/c_club`, `<DD>` = `C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days`.
Authoring module `tools/kl_fa_club.py` (2,597 lines, last commit c6ebe6c); the converter case is `tools/kl_mat.py`
(f67d79c, Stage T).

### D0 What was built

1. A third map made from a Dead Men CAMPAIGN level: M05_A (chapter 5, 'The Mizuki', the Tokyo night club) alone under
   the Dog Days systems level F07, as a Fragile Alliance / Arcade map called 'Last Call' (`kl_fa_club.TITLE`).
2. The round: start shut in Yoko's office with the money -> out through the front office (her bodyguards) -> walkway
   -> dance floor 2 -> dance floor 1 -> stair landing -> wardrobe -> entrance hall -> the queue lane -> the pavement.
   THE BEAT 'exit blocked': the entrance is sealed from the round start (an invisible heroes-only wall) and opens when
   BOTH dance-floor squads are dead or after a clock (120 s from the round-start event, about 111 s after GO), and the
   hunters and F07's police come when it opens. Loot: 11 briefcases, 2.2 M (six in the office, three at dance floor 1's
   bar, one each at the coat check and the ticket counter). Escape: F07's key-framed van on a straight road along the
   pavement, stopping on the only collision floor outside, a 30 x 8.8 m slab.
3. 40 of the campaign's guards in 17 squads (staged: 7 squads in the world from the load, then front office, walkway,
   dance floors, the beat) + 10 of F07's police in 4 squads that arrive + 7 AI heisters = 57 soldiers in 28 squads +
   16 player bodies (live precedent 99 / 55).
4. The four office leaves are OPEN AT BUILD TIME (sunk 1,500, collision cut); only the entrance seal stands, with a
   guaranteed clock that removes it whatever else happens.
5. The three controller kinds no Dog Days level ever ran (7 `PositionLightControl`, 2 `StartAnim`, 5
   `ShotActivateDamage`) are DROPPED by default; each is a flag.
6. The club's two music tracks and five ambience beds are wired but SILENT: 12 clips are not in any stream file we
   have (D6). No dancing crowd, no roofs / helicopter stage.
7. Then the finishing chain other sessions' tools make: wardrobe (16 characters, 12 masks, the four Payday 2 plates),
   the seven AI heisters with a seal gate of their own, six gun looks, the cut shader cache, the dynamic bot step, the
   room-list seal: `<c_club>/chain.sh`. No talk step (kl_fa_talk has no M05 script).
8. FOUR FOLDERS are delivered (D1), all built for the F01 test slot / a test folder. Offline every checker passes
   except the ones that only repeat known findings (D1).
9. It is not on the menu: the 'Dead Men maps' page is full once The Vault takes F07; the packaging facts for a third
   page are in D5. `tools/kl_expansion.py` was not touched.
10. What decides whether it plays is the live order D4, safest first. Two reviewers' rounds (11 + 9 findings) are in;
    what they could not settle offline is in D3 / D6.

### D1 The delivered folders (`<c_club>/`, 0.81 GB) and every checker, re-run on them

| folder | what | F01_Main.zip sha1 | archive bytes | folder | chunk table | five large blocks |
|---|---|---|---|---|---|---|
| `club` | the finished map (guards, police, AI heisters, wardrobe, gun looks), sound bank whole | `1380209c12b4ad5578da4966c4afcf08cd4bb245` | 179,257,735 | 216 MB | 54,085 | 149.1 MB |
| `club_wavslim` | THE SAME ARCHIVE; only `F01_Main.WAV` (11,426,624 bytes, sha1 `bbf27c73...`; whole 21,441,280, `8ffa36f5...`) and `F01_Main.WHD` differ | `1380209c12b4ad5578da4966c4afcf08cd4bb245` | 179,257,735 | 207 MB | 54,085 | 139.1 MB |
| `club_noai` | the same chain on the `--no-ai` build: NO GUARDS, NO POLICE, but the seven AI heisters, wardrobe and gun looks are in | `bbfddbbd7d2bc73e98de953ef9b1d915e4e8e250` | 165,312,553 | 203 MB | 53,122 | 141.3 MB |
| `club_bare` | the map as `kl_fa_club.py test` leaves it, before the chain: guards, police, beat, loot, van; no AI heisters, no wardrobe, no gun looks, FULL shader cache | `a4d024f38ba279c7e5e8584f1fd880011505bd1d` | 150,074,895 | 188 MB | 53,873 | 138.8 MB |

Yardsticks (`<c_club>/blocks.txt`, made by `<c_club>/blocks.py`): chunk-table line of the tools 69,632; five blocks of
stock F07 144.7 MB, of the tab's Retomoto 180.3, the tab's Withdrawal 158.5 (both load live), the Vault 159.9.
Members of `club`: .prm 63.7, .fxc 9.1, .ANM 21.6, .TEX 210.5 MB, .WAV beside it 21.4 (`club_bare`: .prm 44.8,
.fxc 17.8, .TEX 179.7). Entities 26,824 (`club_noai` 26,593), 20 rooms; `result.json` of the three finished folders is
the BARE build's.
Beside each finished archive: `KLWardrobe.ini` (16 characters, 12 masks), `KLGuns.ini` (Version 2, 6 guns), `van.json`
(the van's plan, what was done to F07's van, the build FLAGS), `bots.json` / `bots.txt`, `dyn.json` / `dyn.txt` /
`dyn_map.png`, `audit.json`, `preflight.json`, `checks.txt` + `checks/`; NO `KLJoin.ini`, NO `KLTalk.ini`.
`club_bare` has only `van.json`, `result.json`, `graft.txt`, `log.txt`, `audit.*`, `preflight.*`, `checks/`.

THE RE-RUN (2026-10-11 night): `sh <c_club>/checks.sh <folder> C:/kl_scratch/club/deliver/out/<name>` on each of the
four, one after another (scratch outputs; the folders' own `checks/` and `checks.txt` are the earlier stage's run on
the same files and say the same).

| checker | `club` = `club_wavslim` | `club_noai` | `club_bare` |
|---|---|---|---|
| `kl_maps.py preflight` | FAIL (exit 1): 'preflight: CRASH 1, RISK 3, NOTE 64' | FAIL (exit 1): 'CRASH 1, RISK 3, NOTE 63' | FAIL (exit 1): 'CRASH 1, RISK 3, NOTE 65' |
| `kl_maps.py audit` | FAIL (exit 1): 'RESULT: FAIL (2 findings that must be 0, 4 known and accepted)' | FAIL (exit 1): '(3 findings that must be 0, 4 known and accepted)' | FAIL (exit 1): '(2 findings ..., 4 known)' |
| `kl_fa.py check` | PASS (exit 0): 1 DEGRADED '5 of 28 squads are named by no object' | PASS (exit 0): '26963 nodes; ... ZSquadScript 7' | PASS (exit 0): 1 DEGRADED '5 of 21 squads' |
| `kl_impact.py` | PASS: 'problems: 0 in 1 levels' | the same | the same |
| `kl_arms.py check` | PASS: '0 findings' | the same | the same |
| `kl_chars.py check` | FAIL (exit 1): material 1087 glow30.fx MESH_TWEENED (4 such, KNOWN) | the same (1060) | the same (1087) |
| `kl_map_guns.py check` | PASS: '6 guns with looks ... problems: 0' | the same | does not apply: no gun looks (raises FileNotFoundError guns.json, as it should) |
| `kl_map_guns.py sizes` | PASS: 'entries': 54085 | 53122 | 53873 |
| `kl_fa_club.py van-check` | PASS: '0 fault(s) on the drawn pavement' | the same | the same |
| `kl_map_escape.py check` | FAIL (exit 1): '217 fault(s)' = the plain tool without the drawn pavement, BY DESIGN (D3 A) | the same | the same |
| `kl_fa_bots_dyn.py check` | PASS: 'PASS (0 FAIL, 6 NOTE)' | the same | not run (no bot squad) |
| `kl_fa_club.py bots-check` | PASS: '7 squads, 7 with the seal gate (040_Timer_seal_opens, longest 83 s; seal clock 120 s; leaving 121..168 s)' | the same | not run |
| `kl_fa_bots_dyn.py fake-test` | PASS: '(grid control 1, parked control 1, lattice 3)' | the same | the same |
| cover lists (`covers.py`) | PASS: 'FFCoverList on ROOT\CoverList (ZLIST)' | the same | the same |
| `routes.py` (kl_route walk x2 + doors) | PASS: 'route_doors 0 | RESULT: 1 closures in 1 sets, 1 necessary'; built NOT FREE (HeroColi only), seal out FREE | the same | the same |
| `kl_fa_club.py reverify` | PASS: 'problems: 0' | the same | the same |
| `kl_fa_club.py check` | PASS: 'PASS' | the same | the same |

THE THREE THAT FAIL, said plainly: (1) `preflight` and `audit` repeat the build's `result.json`: 'sound: 5 stream clips are
not in the merged stream file (kl_audio.merge)' (= the 12 clip names of D6), and on `club_noai` also 'FA: BROKEN squads
no ZSquadScript: no police', which is what that build is. Inside the audit every checker of its own is at 0.
(2) `kl_chars.py check`: four materials ask for `glow30.fx` MESH_TWEENED / MESH_RIGID, which the shader cache has no
entry for (987 MobilePhone_Front_01a, 1040 StripeLight_01a_Blue_M05, 1073 ObjectLight_01_White_M05, 1087
CeilingLight_01b_White_M05; 1060 on the no-AI build) - the same case as Retomoto's BombWindow: those light strips and
the phone are not drawn. The audit lists them as known; they are in the bare graft too. (3) `kl_map_escape.py check`:
217 faults = the missing collision floor outside the slab (211 x 'drive key N: no ground under it', 5 x 'no road
within 25 of the drive's height', 1 x 'camera: the eye is outside the map'). WHOEVER GATES AN INSTALL ON `audit.json`
'bad' OR ON preflight's 'CRASH' MUST READ (1) AS KNOWN - or decide that the map waits for the stream file.
The bank regression (`kl_fa_bank.py check` on `c_bank/bank_vault`) was NOT re-run: no shared file was edited by any
stage (`kl_mat.py` changed once, Stage T, with 18 of 20 levels byte-identical before and after).

### D2 The round as BUILT (read back from the folders: `python tools/kl_fa_club.py inventory <folder>`, `check <folder>`)

Floors: office y 342; pavement slab y 30 (origin 32); queue lane y 20; entrance hall y 100. Rooms `M05_A_...`, 20.
Everything the crew and the guards walk is ONE part of the navigation mesh (401 polygons).

| step | what stands in the level | where |
|---|---|---|
| START | 8 START points in two rows of four in Yoko's office, 4 TRAITOR east of the desk, 16 player bodies; 7 AFTER_DEATH points + 8 police bodies on the slab | office x 2700..3050, z 2420 / 2560, y 342; traitors z 2290; police x 900..1500, z -2760 / -2830 |
| ENTERS box / stage 1 | round the START rows: all 8 START points and the 6 office cases inside | (2800, 450, 2450) half (450, 150, 320) |
| doors | four office leaves (`D1 D2` inner, `D04 D05` outer) sunk 1,500, 0 collision placements | `LEAVES` |
| load | 7 squads, 15 bouncers (ZSquadScript field 3 = 1) | their campaign places |
| office | 2 squads (Yoko's guards, 4 men) 10 s after the round-start event = GO + 1.2 .. 1.6 s | `RivalMercs!Timer`, `OFFICE_AT` 10.0 |
| walkway, floor | the inner-office-door box starts 2 squads (5 men), the walkway box 5 squads (13 men); both criminals-only, fire once | `WALK_BOX`, `FLOOR_BOX` |
| LOOT | office 6 x 300,000 (2 desk, 2 sofa table, 2 floor); bar 3 x 100,000 (top y 158); coat check 50,000 (y 284); ticket counter 50,000 (y 128); all on the PUBLIC edge, Dead Men's briefcase model, shown from the load. Least reach to spare 87 (the ticket counter) | `LOOT` |
| THE SEAL | `M05_A_Inside_Entrance_01a\HeroColi` stands (heroes-only collision, invisible, about 3 m before the lane's mouth); `Plane01` is sunk at build time; the clock `Gameplay!010_FirstFight!RivalMercVan!Timer` (120 s from the round-start event) AND the counter of 2 ('Dance#01 + Dance#02 wiped out') both send DeactivateGeom to it | `SEAL_AT` |
| the gate's effect | when it opens: the 3 hunters come from the second-floor lounge over the stairs (search box in the wardrobe) and F07's 4 police squads (10 men) come onto the slab's two ends | `GATE_WAYS`, `ARRIVE_SLAB` |
| the way out | stair landing -> wardrobe -> entrance hall (400, 100, -150) -> the queue lane (105, 20, -1500 .. -2600; 0.96 m of mesh, 12.5 m long, the only exit) -> slab | `ROUTE_OUT` |
| EXITS plane | behind the entrance door | (125, 120, -1440) |
| the exit box (calls the van) | the slab beyond the seal; holds the stop and the boarding place, not the lane's street end | (300, 200, -3050) half (1450, 250, 400) |
| escape marker | beside the boarding place, 300 from the drive | (-640, 30, -2800) |
| THE VAN | F07's first van only. Waits at (-5300, 32, -3100) 50 m west of the stop, OFF the mesh; arrives along the drawn pavement 50 m; stops (-300, 32, -3100), nose 168 short of the line out of the lane's mouth; leaves 70 m east to x 6700 into the glow plane that fakes the street's east end. Boarding place (rear doors) (-637, 30, -3100), van.json (-636, 32, -3094). Camera F07's own, mode eFMM_LookFromPos, eye (-2100, 360, -3100) | `ROAD` |
| police who come back | 7 AFTER_DEATH points + 8 bodies east of the stop (nearest 15.2 m from the rear doors) | x 900..1500 |
| AI heisters | 7 squads `Gameplay!merc_bot_squad!Squad#02..#08`: office loot (richest six cases, 1.8 M, 15 / 30 / 45 s loot wait), then the walk to the HOLD at the entrance hall (495, 122, -141): `040_Timer_seal_opens` 83 s from arrival, so the quickest leaves about 121 s and the slowest about 168 s after the round-start event; then the lane, the exit box, the AllyEscapeBox at (60, 19, -2850) | `bots.txt`, `dyn.txt` |
| texts | start windows `AllLevels/Interface/Online/GameStart/M05A_<mode>_Start` (`kl_fa_club.START_KEY`; FA, Team B, UCC); title `AllLevels/Menu/Online/Scenarios/TitleDL04` = 'Last Call', briefing `.../BriefingDL04` (Dead Men's unused 'Briefing DL04 - Tokyo' slot); 8 stock briefing / reminder lines; exit line `Multiplayer/F04/ExitHeist_01_R` | the level's .LOC, English in all 8 languages |

People: 50 men in 21 squads (40 guards in 17 squads: 23 x eCustom 50 / 175 ('swat'), 12 x 50 / 100 ('cop'), 5 x 75 / 175
('sharp'); 10 police in 4 F07 squads) + 7 AI heisters = 57 ZFFActor in 28 squads + 16 player bodies (the largest build
that ran live: 99 / 55).

THE FLAGS of `python tools/kl_fa_club.py test <out> [--keep] ...` (each is a module name; the delivered folders are all
DEFAULTS except `--no-ai` on `club_noai`; the flags are written to `van.json` and read back by `bots`, `bots-check`,
`check`, `finish`):

| flag | module name, default | what the flag does |
|---|---|---|
| `--no-ai` | `NO_AI = False` | no guard, no police; beat, seal clock, loot, van as with them (refused with `--squads-awake`, `--dead-men-rows`, `--office`) |
| `--squads-awake` | `SQUADS_AWAKE = False` | all 17 campaign squads in the world from the load (the fall-back if staging by `eAM_Activate` fails) |
| `--no-police` | `POLICE_ARRIVE = True` | none of F07's four arriving squads is kept |
| `--police-strip` | `POLICE_ON_SLAB = True` | the arriving police start on the pavement's mesh strip beyond the slab (out of sight, but no collision floor there); default: ON the slab, 2 men in sight when the seal opens; `--police-slab` is accepted and means the default |
| `--dead-men-rows` | `STOCK_ROWS = True` | the guards keep Dead Men's skill / health rows |
| `--office S` | `OFFICE_AT = 10.0` | seconds from the round-start event to the front office's four |
| `--seal S` | `SEAL_AT = 120.0` | seconds from the round-start event to the clock that removes the seal |
| `--seal-open` | `SEAL_OPEN = False` | no seal at all (both pieces sunk); the gate hold shortens to `GATE_MIN` 10 s |
| `--seal-plane` | `SEAL_PLANE = False` | both pieces stand and both are named (`Plane01` has no precedent for DeactivateGeom) |
| `--doors-animate` | `DOORS_ANIMATE = False` | the four leaves stay, store LAST 30 and get 'Activate' 10.4 s after the round-start event |
| `--light-show` / `--beat-anim` | `LIGHT_SHOW`, `BEAT_ANIM = False` | keep the 7 `PositionLightControl` / the 2 `StartAnim` (belong together) |
| `--fan-damage` | `FAN_DAMAGE = False` | keep the 5 `ShotActivateDamage` roof fans |
| `--loot-bags` | `CASE = 'dm'` | F07's money bags instead of the briefcase model |
| `--str FILE` | `STREAM = None` | resolve the clips against that stream file (`kl_fa_bank.use_stream`); the build for after the club's stream extension |
| `--plan FILE` | - | the van's plan from a kept `van.json` (60 s less) |

Rebuild any variant (about 2 min a build, 3.5 min the chain; ONE build at a time; C: has 39 GB, G: 17 GB):
```
python tools/kl_fa_club.py test <out> --keep [flags] --plan "<c_club>/club_bare/van.json"     -> "<out>/F07+M05_A campaign"  ('RESULT: PASS')
sh "<c_club>/chain.sh" "<out>/F07+M05_A campaign" <work dir> <log dir>                          -> <work dir>/fin and <work dir>/fin_wav  ('CHAIN DONE')
sh "<c_club>/checks.sh" <folder> <out dir>                                                      -> <out dir>/summary.txt
```
`chain.sh` stops with 'CHAIN STOPPED' when a step's exit code is not wanted; its gun step exits 1 on purpose (the known
verify findings only, tested by the script). `checks.sh` needs `routes.py` beside it and `C:/kl_scratch/bank/t1/s/covers.py`.
`python tools/kl_maps.py one ... --author kl_fa_club` alone does NOT build this map (prepare_host stops and says why:
the Boundaries drop, the Beat_M05 retype, the van's plan). Any tool that calls `kl_map_escape.van_check`, `check` or
`van_plan_points` on this map must do so inside `kl_fa_club.pavement()` (or call `kl_fa_club.py van-check`).

### D3 Everything that is GUESS or ASSUMED, sorted by what a wrong value would cost

Nothing below was seen in the game. 'Way out' = what to build or switch if it is wrong.

**A. Wrong = the level does not load, or faults (cost: no map until fixed)**

| # | what is assumed | evidence | way out |
|---|---|---|---|
| A1 | A Dead Men CAMPAIGN level grafted by the `--campaign` pre-pass loads: 26,824 entities, 20 rooms, its own CoverList kept. Only Retomoto and the Vault (bank M03_A, loaded through the test folder tonight, same recipe) have gone this way | offline: reverify 'problems: 0', exactly 1 FFCoverList | `club_bare` is this test (D4 L0) |
| A2 | The four leaves sunk 1,500 under their rooms do nothing to the rooms' draw lists or the room fix-up | read, not seen | `--doors-animate` (then A7) |
| A3 | The CUT shader cache (9.1 MB) loads and shows every material; the slim `.WAV` (11.4 MB) loads. Neither has loaded live on any map | offline: no effect asked for is missing but the four glow30.fx; kl_snd.verify 0 | `club_bare` (full cache), `club` (whole `.WAV`) |
| A4 | A key-framed van is drawn and drives where there is NO collision floor: 211 of the drive's 391 keys lie over the drawn pavement alone. The road's height (y 30) is DECLARED, measured from the models (drawn at 30.0 under every cell; nothing drawn in the van's body) | drawn.py raster, `drawn_lane` on every build; Retomoto's van once drove under its road | `ROAD` in `kl_fa_club` (a shorter drive needs a `kl_map_escape` change: the least drive is 20 + 30 m, the slab 30 m) |
| A5 | The one FakeTarget (the van's, at (-5316.6, 32.0, -3099.9)) is inside the vision grid at the load, at the stop and at the end of the drive (the 0x686a66 rule) | fake-test PASS; kl2's arithmetic redone offline | - |
| A6 | `ZEnvSampler` x3 and `SoundSpline` x1 load (no stock Dog Days level reaches their render routine) | ran live on Late Night Opening | `kl_maps` `--flat ZEnvSampler` |
| A7 | (flags only) Dead Men door animations, `PositionLightControl`, `StartAnim`, `ShotActivateDamage` run in Dog Days | none: first-timers | OFF by default for this reason; `PositionLightControl` has its own init (0x671cb0) and an ASSUMED step routine |
| A8 | Chunk table 54,085 of 69,632, five blocks 149.1 MB, 57 actors / 28 squads are inside what loads | Retomoto on the tab: 65,331 entries, 180.3 MB, 99 / 55 | `club_wavslim` (139.1 MB) |
| A9 | The 18 props (flashlights, the door bouncer's wand) and the squads' `MiniCutsceneRout` etc. taken off cause no dangling path | check(): 0 dangling, 5 message-list entries cut | - |
| A10 | Hunters' search box (a volume of the campaign's own) lies off the START's mesh part: no assert found in the hunt goal's update (0x61f0f0) and callees two levels down; what the path-finder (0x60b160) does with an off-mesh point was NOT read | static reading; stock F02 / F03 run the same rout | `--no-ai` build |

**B. Wrong = the round cannot be finished, or the crew is stuck (cost: a rebuild with a flag)**

| # | what is assumed | evidence | way out |
|---|---|---|---|
| B1 | A squad without a behaviour rout that is in the world fights whoever it sees (16 of the 17 kept squads are like that; the campaign's own form) | none | `--squads-awake` does not change it; only a live run settles it |
| B2 | `eAM_Activate` on a SquadModifierBehaviour brings a waiting squad into the world, also when a TriggerDelay2 sends it (the front office). Stock STORY levels do it 19 times from boxes / paths / counters; no build of ours has | census `out/amact.txt`, not read in kl2 | `--squads-awake` (all 17 from the load) |
| B3 | ZSquadScript field 8 is sent when the LAST man of a squad is dead (the fast way to open the seal); if never, the 120 s clock opens it | field 8 chains ran live on Retomoto's squads (ASSUMED the same here) | `--seal S` shorter |
| B4 | A STATIC body switched off by DeactivateGeom stops colliding (the seal's guarantee; the bank's vault door is key-framed) | the storage room's HeroColi has the same .gms flags and the campaign switches it off so | `--seal-open` (no gate; the crew then walks out at once) |
| B5 | Only the first of the gate's two paths passes (GateGroup not read in kl2.exe); if both, five routs are named twice | F07's own gate | - |
| B6 | An AI walks the navigation mesh where there is no collision floor. Not needed by default (police start ON the slab) | - | `--police-strip` is the test of it |
| B7 | The heroes-only seal (flags 0x108) stops a Fragile Alliance HUMAN; whether it stops an AI HEISTER or a policeman is NOT KNOWN (kl_route counts it for everybody). The AI heisters' hold (83 s from arrival) is what keeps them from reaching the lane before the clock; the early ones may meet a standing seal in a quick path | none | `--seal-open` |
| B8 | The bots' timers and the seal clock run from the same instant (both named by the same AIMonitor list 2) | check(): 'clocks: ... same AIMonitor list' | - |
| B9 | A player in the START room is not shot through the doorway: the front office comes at GO + 1.2 .. 1.6 s, 2 m behind the inner doorway, 7.8 m from the nearest START point; not measured for a sprinting human | geometry | `--office S` later |
| B10 | The exit box calls the van; a key-framed van moves with its entity; a human aboard is not ended by the level bound the drive passes 21 - 27 m after the stop | every one of 15 stock vans passes a bound; bots did it live on other maps | shorten `ROAD`'s leave leg |
| B11 | AI heisters are taken aboard from the AllyEscapeBox at (60, 19, -2850) (6.8 m from the boarding action) in vehicle state 3 / 4 without a distance test (kl2 0x907a50) | seen live on the tab's maps | the hook's [Bots] BoardAll |
| B12 | The queue lane is the ONLY exit (0.96 m of mesh): police or guards who stand in it kill the crew (the Vault's run V2). Police rows keep 12.0 m (nearest cover) and the arriving squads' cover points 11.2 m from its mouth | check() | - |

**C. Wrong = it looks, sounds or plays badly (cost: a value to turn)**

- THE GATE IS INVISIBLE: a wall of air about 3 m before the lane's mouth. The campaign's visible version (the entrance door
  shut by `Doors!Entrance!CloseEntranceDoor`, a MatPosAnimProxy over frames 0..50) needs a Dead Men door clip to play;
  not done. Players will see an open door and be stopped by nothing they can see.
- Two of the ten police stand IN SIGHT of the lane when the seal opens (the cost of the safe slab form); the waiting van
  is seen driving in from 46 m (a blind was not tried); the escape camera's eye is over the drawn pavement with no
  collision under it.
- 2 of 10 arriving police cover points lie south of the van's line: they cross the van's kill box (what it does to a
  policeman is not known). The east end of the drive ends 1.3 m from a glow plane.
- Four materials (light strips, a phone) are not drawn (glow30.fx missing from the cache).
- STRENGTH: 40 guards in 17 squads plus 10 police, stock rows by weapon class; the crew's chance with nobody helping
  was not measured (the Vault's 61 enemies killed its idle-player crew). Knobs: `--dead-men-rows`, `--no-police`, the
  hook's [Balance].
- The tiling of `Concrete_Walkway_01a_M05` (material 538, 5 uses): Dead Men mirrored it on U, Dog Days gets TILED
  (`kl_mat.STRING_MAP`, ASSUMED to draw as plain repetition).
- GUESS, placed and only measured 'on the mesh, on free floor, in no bound box': every spawn row, the team-mode stages
  and cameras and triggers (nothing of that mode or Undercover Cop was thought through), the loot's places, turns and
  values (2.2 M), `SEAL_AT` 120, `OFFICE_AT` 10, `DOORS_AT` 10.4, the exit and escape-area boxes, the marker, `VAN_WAIT`
  and the stop (x -300), `MOUTH_SIDE` 150, `BOARD_CLEAR` 500, `FED_CLEAR` 1000, the seven police points, the two moved
  cover points, every bound and kill box, every text wording, the choice of briefing lines.
- GUESS: `GATE_AT`, `GATE_SPEED` 400, `GATE_SLOW` 200, `GATE_LOOT_TYPICAL` 15 s, `GATE_LOOT_MIN` 5 s, `GATE_LATE` 50 s,
  `BOT_PARK` (60, 19, -2850), `PARK_POLICE_CLEAR` 10 m (achieved 10.1), `PARK_FED_CLEAR` 7 m (achieved 7.9): returning
  police cannot be 10 m from the bots' park north of the van's road. Only 11 of the 26 hold places found a cover box.
  The bots leave the hold spread over about 47 s because the timer starts on arrival (a join with the clock was not built).
- GUESS carried by `kl_anm`: bouncers play a copy of the 'Thug' animation set, 'Army' a copy of 'Swat_02' (the .ANM holds no Dead Men clip).
- ASSUMPTION (music): it plays from the load (nothing starts it) and 'Doors_Opening' un-muffles it; the suppress boxes are not hidden in the file.
- ASSUMED harmless: a piece sunk 1,500 under its room; AI walking through the bound boxes at the slab's ends.
- The gun options (`--start=1 --set=1`) are copied from the tab's maps; `tools/kl_chars.py` ran with another session's
  uncommitted change (a `plates` subcommand) in the tree.

### D4 THE LIVE ORDER, for the session that holds the game (safest first)

All through the TEST FOLDER `<DD>/KLExpansion/Maps/T01` and the menu page, as the Vault was loaded tonight (chain
`chain_p.py`, runner `live.py` of the lead's scratchpad; the recipe is below, nothing in `Scenes/Locations` is touched, so
nothing needs `slot.py` and no stock file moves):

1. Before any of it: the owner's word that they are away (a scripted run takes keyboard and mouse); `kl2.exe` closed; the
   hook pair and ini noted so that everything is put back afterwards; the installed tree is the one with the five
   maps (page 2). Never Quit inside a session on this map with an unguarded hook.
2. For each run: delete and re-create `Maps/T01` as a COPY of the folder (all files, `copytree`; it holds the archive,
   the side files and the `F01_Main_LS*` files), set `[Redirect.2] F01=T01` in the run's `KLHook.ini` (the line that now
   reads `F01=DM01`), start the game and take Arcade -> 'Dead Men maps' -> entry 1 (slot F01 = the first row) -> Accept.
   `live.py <tag> DM01 <tree> <seconds> <hook> --redirect "F01=T01" --bots ... --sec ...` does exactly this and puts
   the owner's pair back. Hook: the newest TEST hook (`test_w6` ran the Vault).
3. In every run's ini: `[Load] NudgeMs=1000`; `[KLHook] StallMs=30000`, `StallEndMs=0`; `[Vis] Log=1`; `[Bots] Log=2`.
   FAIL in every run: a `FATAL` line / a `KLHook_N.dmp` / kl_autotest's `RESULT: crash ...`, `RESULT: assert ...` or
   `RESULT: hung`; a 'stall watch:' line inside a level; then `python debug/triage.py --keep`. Addresses that would name a
   cause here: 0x686a66 (FakeTarget outside the vision space), 0x8e5bbd (a large block refused), 0x719884 / 0x48e910
   (room index / gates), 0x8adbba (empty pool), 0x46fe87 / 0x8add12 (unregistered type), 0x796ff4 (a relay naming itself),
   kl2+0x207280 (chunk table).

| run | folder | ini keys | look at | PASS / FAIL in the log |
|---|---|---|---|---|
| C0 | `club_bare` | `[Bots] Enable=0`, `[Character] Enable=0`, `[Crew] Random=0`; idle player; 150 s; pictures at 20, 60, 100, 140 s | does it load (the percentage it stops at if not); the office, lit and textured, the hero at about (2800, 342, 2450); the four doors an empty frame; guards at the dance floors, the front office's two bouncers at GO + 1.5 s | PASS: klauto 'level loaded and running', GO reached, `[Vis] Log=1` line 'record 0xff has never held 'no cell'' (FAIL: 'A TARGET OUTSIDE THE GRID WRITES THERE EVERY FRAME'). Answers A1, A2, A5, A6, A10 and (by sight) B1 / B2 |
| C1 | `club_noai` | `[Bots] Enable=1 Log=2 Escort=0 BoardAll=0 FollowOut=0 Tune=0 Backstab=0`, `[Character] Enable=1`, `[Crew] Random=0`, `[Vis] Log=1`; add the test-only position log (`live.py --poslog`: a KLJoin.ini with `[CrewHop] Enable=1 Dry=1 Log=2` beside the archive, removed afterwards); 300 s | no enemies; the seven AI heisters: the office loot, the hold at the entrance hall, THEN the lane at about 121 .. 168 s; pictures near the lane GO+60..120 s; the seal; the van | 'character: level ... has a wardrobe (version 2): 16 characters, 12 masks'; session state 0x19; 'bots: ... 7 AI'; 'record N (bot): heist stage 0 -> 1' within a minute, '-> 2' at the exit, '-> 3'; the 'bots:' line's 'van 3' then 5 -> 7; 'record N (bot): aboard'; 'over'. FAIL: bots at stage 0 (the ENTERS box), bots in the lane before GO+111 s (the seal does not stop AI: B7; then `--seal-open` is the true form), no van, nobody aboard, a bot standing at (60, 19, -2850) when the van is not there. First cut-cache load (A3): anything black that C0 showed = the cache |
| C2 | `club` | as C1 but `[Bots] Escort=1`, `[Balance] Log=1`; 330 s | the front office's four at GO + 1.5 s; the walkway and floor squads coming only after the boxes; hunters walking DOWN to the wardrobe after the seal opens; ten police on the slab ends (2 in sight); the van arrives and the crew is taken aboard | the same lines; `bots:` 'lost ...' lines show where the crew dies; seal: the first bot position in the lane (poslog) against the 120 s clock. Play it twice in one process (the second load is the memory test) |
| C3 | `club_wavslim` | as C2 | by ear: gunfire, footsteps, voices as in C2 | no new line; 'memory: at the level's largest block' shows 10 MB less asked. NEVER run this first |
| C4 | NEW build `test <out> --keep --police-strip --plan ...` then `chain.sh` | as C2 | do the ten police walk onto the slab from the strip, or stand | police seen on the slab within 30 s of the seal's opening = AI walks bare mesh; a fault or men standing in the road = keep the slab default |
| C5 | NEW build `--seal-open` (or `--seal 40`) | as C2 | whether the crew survives without a gate | the answer to B7 / B4 |
| C6 | NEW build `--squads-awake` (only if C2 shows just the 15 bouncers) | as C2 | | all 17 squads present at GO |
| C7 | NEW build `--doors-animate` (then `--light-show --beat-anim`, `--fan-damage` one at a time) | as C2 | doors swing or are ignored; a fault AT LOAD here = that controller kind: the default stays off for good | no fault at the load |

After C2: `--seal S`, `--office S`, `--dead-men-rows` are taste. `--str FILE` belongs to the build that follows the stream
file (D6), not to a test of its own.

### D5 Packaging facts for `tools/kl_expansion.py` (that file was NOT edited; it is another session's)

The Dead Men maps page (page 2) holds nine entries; five are the Fragile Alliance maps (F01 F02 F03 F04 F06), the sixth
is The Vault (EXTRA 'DM03A', F07); F05 F08 F09 are the paid DLC slots and stay stock. So 'Last Call' needs PAGE 3:
- **page**: `kl_expansion.PAGE` is ONE number (2). A third page needs the tool to carry a page per map; the docstring
  (lines 75 - 77) says mkoverlay.py has buttons for pages 2..5 (2..4 with the Heister button) and klslot.c reads
  `[Redirect.2]` .. `[Redirect.9]`. READ, not tried: a map on page 3 takes `[Redirect.3] F01=DM05A` and `[Page.3] F01=Last Call`
  (entry 1 of any page loads slot F01, kl2 0x746570 - ORDER), so the slot NAME repeats across pages and the stock
  Subway is not touched. The page-3 button's title and the overlay are the tool's; not designed here.
- **id**: `DM05A` is PROPOSED (ids so far: DM01 DM02 DM03 DM06 DM09, DM03A for the Vault).
- **title**: 'Last Call' (`kl_fa_club.TITLE`). **briefing**: `kl_fa_club.TEXTS` under `AllLevels/Menu/Online/Scenarios/BriefingDL04`
  (title under `TitleDL04`); both are in the level's .LOC, English in all 8 languages. The wording is a GUESS.
- **picture**: `LevelPicture_M05` - the entity exists in Dead Men's frontend scene (the Vault's note lists FA01 FA02 FA03
  FA06, M01, M02, M03A, M03B, M05 ... M14, read with `kl_expansion.front_scene('dm')`); it is the campaign chapter's picture.
  `kl_expansion.pictures()` has not been run on it.
- **sources**: `['M05_A']` under systems `F07`, with kl_maps' `campaign=True` (and `--m-drop "Boundaries!*"`).
- **build**: `build='prebuilt'`, like The Vault: the map is made by `kl_fa_club.build()` + `finish()` (the van's plan and
  `kl_map_escape.van_layer` round kl_maps.one) and then `<c_club>/chain.sh`. The tree takes a FINISHED FOLDER:
  `--prebuilt DM05A=<c_club>/club` (adopt() renames members and files F01 -> the slot's, bytes untouched). `result.json`
  and `audit.json` are in the folder (adopt() and `audit=True` want them).
- **'author' module**: `kl_fa_club`. **known**: `('stream clips are not in the merged stream file',)`;
  **known_re**: `(r'sound: (\d+) stream clips are not in the merged stream file \(kl_audio\.merge\)', 5)` (the line reads
  '5 stream clips' for the 12 clip names; PINNED at 5). The audit's other known lines are the four glow30.fx materials
  and `kl_map_escape.check`'s 217 faults is NOT part of the audit (checks.sh only).
- **side files** (kl_expansion.SIDE): `KLWardrobe.ini`, `KLGuns.ini`; NO `KLTalk.ini` (no talk step), NO `KLJoin.ini`
  (`join` unset). `van.json`, `bots.json`, `dyn.json`, `bots.txt`, `dyn.txt`, the pictures and notes go to
  `BuildInfo\DM05A` by adopt()'s rule; the folder's `checks/` is a subfolder and is skipped.
- **live**: nothing. `bones_live`: False (the build goes through kl_graft's defaults; never run).
- The hook's per-map behaviour ([Bots], [Crew], [Fed], the HUD look step, the fed's body line) is gated to non-stock levels
  by the hook; nothing of klhook/ was touched or needed. The HUD look (`kl_hud.py all --look deadmen`) and the fed's
  body line the other maps got are NOT applied to these folders: the tree's builder does them (re/expansion.md 11).
- Disk for a tree: the club adds 179 MB of archive + 21 MB `.WAV` + the `.LS` files (about 215 MB).

### D6 What was NOT done, and why

- **Music and ambience: SILENT.** Wired (the kept audio subtree's own stream objects `Locations/M05_A/M05A_Audio.zip!STREAMS!Inside!Music!Club_01_* / Club_02_*`;
  the host AIDWrapper sends 'Doors_Opening' at the round start), but 12 clips have no record in the built .WHD because
  neither the installed `PC_Def.str` nor `<work>/build/v_vault/PC_Def.str` (the Vault's extension, read only) holds them.
  The 12: `Music/InHouse/Japan/M05_A/M05_A_Club_Clean.wav`, `_Clean_3D`, `_Muffled`, `_Muffled_3D`,
  `M05_A_Club_2_Clean.wav`, `_2_Clean_3D`, `_2_Muffled` (the two interleaved four-layer sets 'M05_A_Club_Layers' 32.4 MB
  and 'M05_A_Club_2_Layers' 49.5 MB; the second set's fourth layer `_2_Muffled_3D` is named by no object, bring the sets
  whole) and `SFX/Ambiences/M05_A/Inside/Club_Entrance_Ambience.wav`, `.../Inside/M05_Club_Ambience_01.wav`,
  `.../Inside/Yoko_Office_Ambience.wav`, `.../Outside/Roftop/Ambience_Rooftop_M05_A.wav`, `.../Outside/Street/Street_01.wav`.
  (The owner said yes to a larger stream file; the club's extension is a later step: ~82 MB of music.) After it: rebuild
  with `--str <file>`, run the chain; preflight / audit then lose their one finding. check() prints the list from the built .WHD.
- **The dancing crowd** (the owner was told; he has not objected). **Stage two: the roofs and the helicopter.**
  The upstairs squads (Lounge#01 / #02, Rave#01 / #02, 10 men) are off the round's way and nothing leads the crew up;
  the upstairs bars' loot (four stacks) waits for the stairs to be proven. The three roof-fan controllers are off.
- **The visible gate** (the entrance door shutting) and a seal that is the beat's own EVENT for the bots (their hold is a clock).
- **No talk step**: `kl_fa_talk.SCRIPTS` has no M05 entry; no Kane countdown, no Bain lines.
- **No picture** of the map was rendered (`tools/kl_view.py` renders models; nobody looked); `drawn.py`'s map is a raster
  of models, not a view.
- **A blind for the waiting van** (it is seen from 46 m); a retreat when the van is called (the vehicle monitor's list 4
  is empty, as the bank's); F07's vans 2 and 3 (a van parked under the map is the 0x686a66 crash).
- **Team mode / Undercover Cop**: spawn sets are placed and on the mesh; nothing else was thought through.
- **kl_map_ai plan**, **kl_fa_cover**, **the fed's body line and the HUD look** for this map: not applied.
- **The bank regression** was not re-run (no shared file edited); **a true clock-joined release** for the bots (D3 C).
- **In shared files, left for their owners**: kl_maps.audit has no 'known' entry for a verify finding; `kl_graft.verify`
  has no line for zero cover lists; `kl_dmassets`'s log does not print `kl_mat`'s new 'strings' key; `kl_fa.py`'s
  'unnamed squads' heuristic does not read field 3 (the DEGRADED line).
- **Two slips of earlier stages**, recorded: scratch scripts written with shell heredocs (one ate a backslash; repaired with
  Edit); Stage F's sha1 `9972c87e` and the 92 s hold in its section are superseded by the review rounds.

(end of DELIVERY)

## Stage T - the converter case (tools/kl_mat.py: TEXT/TILU = MIRRORED)

STATE: DONE (2026-10-11 19:45). All checks pass; no archive is left (the builds ran without `--keep`). Kept in
C:/kl_scratch/club/t/ (0.2 MB): s/ (baseline.py, mirror.py, results.py), out/ (before.json, after.json, mirror.txt,
check.txt, bare.log, nobounds.log, results_*.txt) and result.json / log.txt / graft.txt of the two builds.
Offline only; nothing run in the game.

### T.0 Baseline, made BEFORE the edit (tree at 26ea22d, tools/kl_mat.py sha1 fa8db3da)

`python C:/kl_scratch/club/t/s/baseline.py C:/kl_scratch/club/t/out/before.json`: for ALL 20 Dead Men levels (not only
the seven that are built today) the sha1 of the converted .MAT, twice - 'plain' = `kl_mat.convert_mat_full(data)` with
every default, 'build' = `kl_dmassets.convert_level(level)` (the path a graft takes: the converted .prm and the .TEX's
ids handed in) - plus a hash of the converter's report. MEASURED: 18 levels convert, two are refused:
M05_A (`material 538 ... TEXT/TILU value b'MIRRORED' never occurs in Dog Days`) and M01_A (material 615, the same).
The 'build' hashes of the seven named levels: M01_FA_A 4acc31b5, M02_FA_A 0250c1f1, M03_FA_A 69052ef3, M06_FA_A
ef95b22e, M03_A 5890e380, M09_A 98d3e153, M09_B 988021ef (whole values in before.json).

### T.1 What was changed (one file, tools/kl_mat.py, +19 lines)

- NEW table `STRING_MAP = {('TEXT', 'TILU', b'MIRRORED'): b'TILED'}` beside CLASS_MAP, with the comment that says
  what Dog Days has instead and what the look difference is.
- In `convert_mat_full`'s string guard (was line 396-397): a value Dog Days never has on that (node, key) is looked
  up in STRING_MAP first; a hit whose target Dog Days does have is written (node count = length + 1, value) and
  counted in the report's NEW key `strings` {('slot node/key', old, new): n}; everything else raises as before.
  The table is consulted ONLY where the old code raised, so a level that converted before cannot change.
- Docstring: the report key, and point 2's 'every string value is the same in both games' gains 'but for
  STRING_MAP's one case'.
- NOT done, on purpose: the study's other proposal (accept MIRRORED on U because Dog Days has it on V). READ
  re/campaign_fa_club.md 8 'Not corrected, but weaker than it reads': how kl2.exe turns the value's name into an
  addressing mode was not found ('MIRR' is nowhere in the exe), so MIRRORED on U stays ASSUMED; TILED is the one
  value certain to be read there (27,965 stock bindings).

THE LOOK DIFFERENCE (MEASURED `python C:/kl_scratch/club/t/s/mirror.py M05_A M01_A` -> out/mirror.txt): the picture
repeats along U where Dead Men flipped every second repeat. Carried by
- M05_A slot 538 `Locations/M05/Concrete/Concrete_Walkway_01a_M05` (class Standard/Standard, 5 uses in the .prm): three
  stages - mapDiffuse (texture 941 `Locations/M05/Concrete/Concrete_Walkway_01_M05`), mapNormal (184
  `Locations/M05/Plaster/Plaster_Basic_01_M05`), mapSpecularMask (no texture). TILV is TILED on all three already.
  ONE material of the club: a concrete walkway surface. Where its five meshes stand was NOT looked up; if a seam
  shows on a walkway's concrete in the game, this is the cause.
- M01_A slot 615 `Vechicles/Civil_USA_01/V_Civ_USA_01_02` (2 uses): mapDiffuse only. Not this job's level; it now
  converts too.
No other Dead Men level has the value.

### T.2 Checks

1. **The baselines are byte-identical - PASS.** `python C:/kl_scratch/club/t/s/baseline.py .../out/after.json`, then
   the comparison of the two files: 'identical levels: 18 of 20' - for each of the 18 the 'plain' hash, the 'build'
   hash, both sizes AND the report's hash (without the new, empty `strings` key) are the same; the two that differ
   are the two that were refused: M05_A now 527,600 bytes (build e7efc9cd, `strings` {'538 TEXT/TILU -> MIRRORED ->
   TILED': 3}), M01_A 763,872 bytes (build 40e5e693, {'615 ...': 1}). So the bank (M03_A), Retomoto (M09_A / M09_B)
   and the four Fragile Alliance maps get the same .MAT as before; no rebuild of any of them was made or is needed.
2. **The written file reads back - PASS** (out/check.txt): M05_A `kl_mat.check` (690, 9), `kl_dmassets.cross_check`
   []; slot 538's three stages read TILU (6, b'TILED'); M01_A (1014, 9), [] and slot 615 the same.
3. **The stock command builds, with the study's numbers - PASS.**
   `python tools/kl_maps.py one "C:/kl_scratch/club/t/bare" F07 M05_A --campaign` (34 s; exit code 1 because verify's
   problems are not 0, as for every level without a layer) -> 'verify: problems: 11', 'built ... F01_Main.zip, 284
   MB, 30 members'. result.json: entities **26,106**, rooms 20, textures 1,676, materials 1,135, prm_chunks 52,934
   (= **52,935** chunk-table entries), dangling [], tops 395, ref_slots 36,987, archive 284.4 MB; problems **11** =
   1 sound ('5 stream clips are not in the merged stream file') + 1 CRASH (no OnlineFragileAllianceSettings) + 9
   BROKEN (define, exit trigger, START / AFTER_DEATH points, three gameplay triggers, loot, squads).
   `python s/results.py <mine> "<work>/build/cfa/club/patched/F07+M05_A campaign" ".../sk_patched/..."`: **0 of 34
   keys differ** from the first agent's and from the second agent's build made with the outside wrapper (every key
   of result.json but 'seconds').
4. **The variant without the campaign's bounds - PASS.**
   `python tools/kl_maps.py one "C:/kl_scratch/club/t/nobounds" F07 M05_A --campaign --m-drop "Boundaries!*"` ->
   'verify: problems: 11'; entities **26,091** (15 fewer), tops 380, ref_slots 36,972, dangling [], the rest as in 3;
   0 of 34 keys differ from `<work>/build/cfa/club/nobounds` and `.../sk_nobounds`.

### T.3 GUESS / ASSUMED

- ASSUMED: TILED on U is drawn as plain repetition in Dog Days (it is what 27,965 stock bindings have; not seen in
  the game for this material). The look difference itself is by definition, not measured on a picture.
- Not established (unchanged from the study): what Dog Days would draw for MIRRORED on U.

### T.4 For the next stages

- The bare build: `python tools/kl_maps.py one <out> F07 M05_A --campaign --m-drop "Boundaries!*"` (add `--keep` to
  read the archive back; the folder inside <out> is 'F07+M05_A campaign' with or without --m-drop, so two variants
  need two <out> folders). 34 s, 284 MB archive.
- No outside wrapper is needed any more: G:/kl_scratch/cfa_club/run_maps.py and the study's `build_open.py` patch of
  `TM.read_mat` give the same bytes as the stock tools now (check 3), but they substitute on TILV too and on every
  node - use the stock command.
- kl_whoref.py and every other tool that converts M05_A through kl_graft.DeadMen now runs on it (they died at the
  same line; not re-run here).
- The report key `strings` is new: `kl_dmassets`'s log line does not print it (that file is another session's).

### T.5 Open

- Whether the walkway material's five meshes are on the round's route (then the tiling is in sight) - not looked up.
- The bank's regression (`kl_fa_bank.py check` on `<work>/build/c_bank/bank_vault`) was NOT re-run: M03_A's converted
  .MAT is byte-identical (check 1) and that tree is not this stage's to touch.

## Stage L1 - the authoring module, first half: a round without enemies (NEW tools/kl_fa_club.py)

STATE: DONE (2026-10-11 20:30). `tools/kl_fa_club.py` (1,256 lines) holds the nine names of the interface and builds
F07 + M05_A with the first half of the layer; every check of the stage passes with TWO known findings, both justified
below (L1.3). NOTHING RAN IN THE GAME (another session holds it). Kept for the next stage:
`C:/kl_scratch/club/l1/build/F07+M05_A campaign/` (174 MB: F01_Main.zip 135,476,152 bytes, sha1 f109b3ca4bda..., lightened,
briefcases and texts in; result.json, log.txt, graft.txt, preflight.json). A second build of the same command gave the
same archive (`out/again.txt`). Scratch `C:/kl_scratch/club/l1/`: `s/` (b.py nodes of a built folder by regex, scan.py a
character map of mesh + free floor, floors.py the collision floors under points, vt.py / vt34.py vtables in kl2.exe),
`out/` (every output named below), `bare/` (result and log of the bare graft the places were measured on; its archive is
deleted - rebuild: T.4's command with `--keep`, 34 s). No other file of the repo was touched: kl_fa_author.py,
kl_fa_bank.py, kl_fa_loot.py, kl_route.py, kl_maps.py are only imported / run. No per-level table of another tool gained
an entry (kl_maps.FLAT is lent one class pair for the length of the build, in memory).

### L1.1 What the file is

Pattern: kl_fa_bank.py. Its generic parts are IMPORTED (`import kl_fa_bank as BK`: `Doors`' frame arithmetic and arm /
disarm, `put` / `values` / `facing` / `world_of`, `set_text`, `archive_of`, `read_built`, `lost_clips`, `reverify`,
`BOT_SQUAD`, `BLOCKS_LIVE`, `WARDROBE_CHUNKS`), none of its tables; kl_fa_author's small tools as there. No new entity,
no new controller. NOTE FOR WHOEVER EDITS kl_fa_bank.py: those names are now used from outside (another job was
changing that file while this stage ran; the builds before and after its change gave the same archive).

| part | where | what |
|---|---|---|
| the build's own arguments | `M_DROP IK NO_BUILD`, `build()` | `Boundaries!*` out; the two `Beat_M05` objects loaded as plain ZSTDOBJ (kl_maps' `flat`) |
| the measured club | `START TRAITOR POLICE BODIES STAGE_B/C/D SPAWN SLAB LANE_MOUTH DOOR_IN` | 8 START in two rows of four in Yoko's office (x 2700..3050, z 2420 / 2560, y 342), 4 TRAITOR east of the desk (z 2290), 7 AFTER_DEATH on the pavement slab (x -900..-600 and 1300..1500, z -2760), 8 police bodies beside them (z -2830), every other kind F07 has in rows of their own; 16 player groups |
| loot | `LOOT LOOT_REACH CASE CASE_SCALE` | 11 briefcases, 2,200,000: 6 x 300,000 in the office (2 on the desk, 2 on the sofa table, 2 on the floor), 3 x 100,000 on dance floor 1's bar (top y 158), 50,000 on the coat check's counter (y 284) and on the ticket counter's shelf (y 128) - each on the PUBLIC edge; shown from the load |
| doors and the seal | `LEAVES DOORS_ANIMATE DOOR_DY DOOR_LAST DOORS_AT SEAL SEAL_PLANE SEAL_OPEN SEAL_AT MUFFLE`, class `Doors`, `doors()`, `gate()` | four office leaves; the seal's two pieces `HeroColi` / `Plane01` |
| what never ran in Dog Days | `LIGHT_SHOW BEAT_ANIM FAN_DAMAGE BEAT NEVER_RAN`, `strip()`, `take_off()` | three flags, all OFF = dropped (L1.2 'The three kinds') |
| host layer | `PLACE BOUNDS PARKED KILL ROLE KEEP_MORE VAN VAN_GROUP VAN_WAIT ESCAPE _KEEP` -> `KEEP`, `DROP` | 41 re-placed objects (markers, planes, cameras, stage boxes, jump points, three bound trios), 9 parked bound boxes, 3 campaign kill boxes, 9 objects with a new job |
| texts, sound | `TITLE TEXTS START_KEY START_FIELDS LINES EXIT_LINE MUSIC_CLIPS AMBIENCE_CLIPS` | 5 .LOC keys of the level's own, 8 briefing / reminder lines, the exit line; the 12 clips the stream file lacks |
| the interface | `HOST prepare_host strip KEEP DROP layer_names complete wire campaign_names` | as kl_graft.build's docstring asks; `campaign_names` keeps the three kill boxes and no squad (`NO_AI = True`, fixed in this half) |
| the written level | `finish(folder)` | lighten (trim, slim) -> briefcase model into dead chunk indices -> texts |
| checks | `check(folder)`, `inventory(folder)`, `ROUTE_IN ROUTE_OUT LOOT_WALKS KNOWN` | L1.3 |
| commands | `test <out> [--keep] [flags]`, `finish`, `check`, `inventory`, `reverify` | `test` = build + finish + check in one process |

**The round as wired** (MEASURED: `python tools/kl_fa_club.py inventory <kept folder>` -> `out/inventory.txt`, check()'s
'chain' line):
- round start (AIMonitor list 2): F07's `FASpecials!Timer_MissionBriefing`, the seal's clock
  `Gameplay!010_FirstFight!RivalMercVan!Timer` (TriggerDelay2 `SEAL_AT` = 75 s) and `...!Activator_VanSound` (AIDWrapper
  'Doors_Opening' -> the music's two muffle switches `...Audio.zip!STREAMS!Inside!Music!GeomActivator_Door_01 / _02`).
  wire() WRITES that list (F07's own names five timers of its opening).
- the clock -> `...RivalMercVan!GeomDeactivator_DriveInVan` (DeactivateGeom) -> `M05_A_Inside_Entrance_01a\HeroColi`.
- `Specials!LevelSpeak!TriggerBox` in the wardrobe -> its speaker, line `Multiplayer/F04/ExitHeist_01_R`.
- ENTERS box ROUND the START rows (2800, 450, 2450) half (450, 150, 320): all 8 START points and the 6 office cases
  inside (check()); EXITS plane behind the entrance door (125, 120, -1440); loot marker over the desk, its 11 s box
  round the START rows; escape marker on the slab (300, 218, -2800); exit trigger `otrExitLevel` = the slab
  (300, 200, -3050) half (1450, 250, 400): x -1150..1750, z -3450..-2650, wholly beyond the seal's box.
- team mode: stages front office / wardrobe / entrance hall with their triggers at the inner office door, the stair
  landing and the hall's top (all GUESS; nothing of that mode was thought through).

**The doors** (the lead's default). `DOORS_ANIMATE = False`: the four office leaves `D1 D2` (inner) `D04 D05` (outer) are
SUNK 1,500 in world y and their key-framed placements cut, by `Doors` = `kl_fa_bank.Doors` with this level's nodes (the
three wrappers are this file's, about 60 lines the bank's class has bound to its own tables; the frame arithmetic and
arm / disarm are inherited). Build lines: '5 nodes sunk by 1500', '5 entities moved in the .gms (2 of them hold another
local place there than in the .prp; the world places agree)' - trap 2 of G1.1, the outer door - 'placements by shape type
{4: 4, 1: 1}; none is left'. `--doors-animate`: the leaves stay, store LAST 30 and get 'Activate' from
`...RivalMercVan!TimerVanGo` 10.4 s after the round-start event (GO + 2 s), the muffle switch with them.

**The seal - and one choice of mine the lead should see.** The stage asked for 'the entrance SEAL of the beat present
from the start with its guaranteed clock'. The seal is two STATIC, heroes-only objects, each alone enough to shut the
lane (MEASURED `out/bare_doors.txt`: 4 closures, 4 necessary). By default ONE of them stands: `HeroColi` (.gms flags
0x200308, the very form of the storage room's `HeroColi`, which the campaign itself switches off with a DeactivateGeom);
`Plane01` (flags 0x308, switched by nothing in the campaign: the study's open question whether DeactivateGeom frees it)
is taken out at build time with the leaves. So the seal is present, the clock opens it, and what opens it has the
campaign's own precedent. `--seal-plane` = both stand and both are named; `--seal-open` = neither (no gate).
NOT DONE and said plainly: the gate is INVISIBLE (a wall of air 3 m before the lane's mouth); the campaign's visible
version - the entrance door shut by `Doors!Entrance!CloseEntranceDoor` - needs a Dead Men door clip to play and is the
next stage's to decide (L1.6).

**The three kinds that never ran in Dog Days** (READ in kl2.exe: `python C:/kl_scratch/club/l1/s/vt.py <Class> <Base>`,
`vt34.py`; the reasoning stands at the flags in the file):

| kind | read | default | flag |
|---|---|---|---|
| `PositionLightControl` x 7 (the light show) | own init (slot 13, 0x671cb0, 244 instructions) and an own routine in slot 25 (0x72c400, 289: ASSUMED the per-frame step), own save / load; reads `Beat_M05\Ground_Beat05` and `Club_01_Clean_Music_01` | OFF: the controller comes off, the lights are static | `--light-show` |
| `ZIKLNKOBJ` + `StartAnim` x 2 (`Beat_M05`) | StartAnim: own init (0x8f6b90, 92), no step; it starts a Dead Men .ANM clip converted by kl_anm's GUESS | OFF: loaded as plain ZSTDOBJ, no model, hidden, no StartAnim; the .ANM then holds NO Dead Men clip ('.ANM joined: clips +0') | `--beat-anim` |
| `ShotActivateDamage` x 5 (roof fans) | differs from stock `ZShotActivate` (439 in this build) in ONE routine, slot 34 (0x4bb9b0, 132); its init is the base's (0x5aa380, 22 instructions, no call of slot 34). Where slot 34 is called from was NOT found | OFF: taken off (the fans cannot be shot to pieces); they stand on the roof, off this round | `--fan-damage` |

`--light-show` without `--beat-anim` reads a still object: the two belong together. With all three off preflight's 'first'
list is down to `ZEnvSampler` x 3 and `SoundSpline` x 1, both of which ran live on Late Night Opening / the park
(re/campaign_fa_club.md 3.5).

**Bounds.** The campaign's five go (`M_DROP`). Three of F07's bound trios stand outside the slab's open edges - Bound box
6 m deep from the edge outwards, warn boxes the same and 1.2 m onto the slab - the other three are parked; the campaign's
three single `Specials!KillBox` (kept by campaign_names, re-placed in strip) lie under the edges, tops y -100: west
x -4020..-1220, east x 1820..6020, kerb and road z -5350..-3450. They punish, they do not stop (GUESS, marked).

**The van.** F07's first van only, STANDING at `VAN_WAIT` (-3000, 32, -3100) with F07's own baked drive; the exit trigger
names it alone. A first-half state, as the bank's L1: the next stages replace `park_van` by `kl_map_escape.van_prepare`.

### L1.2 The build

```
python tools/kl_fa_club.py test C:/kl_scratch/club/l1/build --keep        (about 2 min; 'RESULT: PASS', exit 0: out/test2.txt)
python tools/kl_fa_club.py check "C:/kl_scratch/club/l1/build/F07+M05_A campaign"       (25 s, 'PASS': out/check.txt)
```
`python tools/kl_maps.py one ... --author kl_fa_club` alone does NOT build this map: prepare_host stops with a line that
says why (the build needs `M_DROP` and the retype). Lines of the build:
- 'kl_maps: --flat ZIKLNKOBJ: 0x200027 is loaded as 0x200002 in this build'; 'F07 systems (411 subtrees, 9636 nodes) +
  M05_A map (242 subtrees, 16950 nodes)'; 'verified: 26586 entities, 26587 nodes, 25102 reachable chunks, 21 room sets,
  566 gate / list REF cells, 1676 textures, 1134 materials'
- 'spawn points placed: START 8, TRAITOR 4, AFTER_DEATH 7, UCC 8, UCC_TRAITOR 4, UCC_POLICE 7, TEAM_MERC 6, TEAM_MERC1..3 4
  each, TEAM_POLICE 7' + 8 + 8 player groups; 'Heroes! groups placed where M05_A has them: 0'
- 'verify: problems: 2'; 'built ... F01_Main.zip, 284 MB, 30 members'
finish: 'load weight: 1346 dead model roots; .prm 78.9 -> 38.0 MB ...; .TEX 342.3 -> 163.9 MB'; 'briefcase M01_FA_A root
6380 (DropMoney!KillDrop!Suitcase) -> chunk 70: 18 chunks into dead indices, 0 at the end'; '11 briefcases (model 70,
x 1.25, its underside 0.3 over its origin); chunk table 52910 entries, as before'; '5 text keys in 8 languages'.

### L1.3 The checks (all on the kept, finished build; outputs in `C:/kl_scratch/club/l1/out/`)

| check | command | result |
|---|---|---|
| verify problems | the build's last lines; check()'s 'verify:' lines | **2, both KNOWN**: (1) 'sound: 5 stream clips are not in the merged stream file' = the club's music and ambience (L1.5 lists the 12 names); (2) 'FA: BROKEN squads no ZSquadScript: no police' = this half IS a round without enemies. The bare graft has 11 |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | **0 CRASH, 1 BROKEN** = the same 'no ZSquadScript'; 1 DEGRADED (no bot squads: a later stage). settings 1, exit trigger 1, monitor 1, animated vehicle 1, AIMonitor 1, OnlineMoneyCtrl 133 |
| cover list | check() | 'cover lists (FFCoverList): 1' (the club's own top-level `CoverList`; F07's is dropped) |
| doors and seal read back | check() | four leaves at their stock x / z, 1,500 lower, 0 placements; `HeroColi` at (131, 0, -2478) with 1; `Plane01` sunk, 0 |
| spawn points | check() (kl_route.stations, near 30, the gate taken out) | '79 places, 79 on the mesh part of the START (401 polygons) and on free floor within 30' = 63 ZSpawnPoint + 16 player groups; every one outside the building is on the slab |
| bounds, kill boxes | check() | '3 LevelBound in their place (18 bound and warn boxes with the parked ones), 3 kill boxes; 0 of the 93 spawn points, player groups and stations inside one'; at each of the slab's three edges a walker 1 m before it is in no bound, 1.2 m beyond it in one; kill boxes' tops 130 under the slab |
| loot | check() (kl_fa_loot's pick-up test as read at kl2 0x783e60, from floors a walk reaches) | '11 objects, 2200000; 11 can be taken', least 87 of reach to spare (the ticket shelf from (150, 19, -1250), 78 away, 107 up; the bar from 72 away, 137 up) |
| ... its standing places | `python tools/kl_route.py stations <folder> START=... desk=... bar_1=... --near 30` -> `stations_loot.txt` | 'RESULT: ALL REACHED', 10 of 11 on the mesh; the place before the coat check is 16 off it |
| the route as built | `python tools/kl_route.py walk <folder> --from START=2817,342,2420 --via ... --to pavement=300,30,-2800` (12 places) -> `route_built.txt` | 'NOT FREE': the leg queue lane -> street end 'BLOCKED - the thinnest crossing (11 m) goes through REF 23632 M05_A_Inside_Entrance_01a\HeroColi [STATIC mesh 0x108; stops heroes only]', nothing else |
| ... up to the seal | the same to `lane_club=105,20,-1500` -> `route_inside.txt` | 'RESULT: FREE; the mesh way: 716 samples, 1 with something in the body column' (the level's own stair `Si0102_M05_StairsA_01` beside the mesh line at (268, 40, 3150)); check(): 'FREE, 122 m' |
| ... the seal out | `... --open "M05_A_Inside_Entrance_01a\HeroColi"` -> `route_open.txt` | 'RESULT: FREE; the mesh way: 767 samples'; check(): 'FREE, 133 m' |
| doors | `python tools/kl_route.py doors <folder> ...` -> `route_doors.txt` | '1 closure(s) in 1 set(s); 1 necessary; with all of them out the way is FREE' (bare graft: 4 / 4, `bare_doors.txt`) |
| the chain | check() | 'round start -> [Timer_MissionBriefing, Timer, Activator_VanSound]; -> 75 s -> seal off [HeroColi]; doors: open at build time; the music's muffle switch Doors_Opening -> 2 objects' |
| never-run kinds | check() | PositionLightControl 0, StartAnim 0, ShotActivateDamage 0; the beat objects 'ZSTDOBJ, model none, hidden' |
| exit box, van, FakeTarget | check() | 'exit box x -1150..1750, z -3450..-2650: on the slab True; holds the pavement station True, the lane's street end False; it names [EscapeVehicle_Animation_F07]'; 'FakeTarget ... at (-2995, 31, -3084): inside the vision space, kl2's arithmetic gives a record' (vision space x -6725..10906, z -7074..6724) |
| chunk table, blocks | check() | 'chunk table: 52910 entries (the tools' line: 69632); .prm 37.3, .fxc 17.8, .ANM 21.6, .WAV 21.2 MB; the five load blocks 131 MB (...: 171)'; '23799 of its indices are dead (the wardrobe takes 20989)' |
| written level | check() / `kl_fa_club.py reverify` -> `reverify.txt` | 'problems: 0' (26,586 entities, 566 gate / list cells, 24 list entries parked on the free REF id 36975) |
| kl_impact | `python tools/kl_impact.py <archive>` -> `impact.txt` | 'problems: 0' |
| preflight | `python tools/kl_maps.py preflight <folder>` -> `preflight.txt` | 'preflight: CRASH 1, RISK 4, NOTE 64': CRASH = 'kl_graft.verify reported 2 problems' (the two above); RISK = 'fa:squads', `ZEnvSampler` x 3 (twice) and `SoundSpline` x 1 (both ran live on other maps). The bare graft: CRASH 2, RISK 16, NOTE 65 |
| the flags | `test <out> --doors-animate --seal-plane --fan-damage` -> `var_a.txt`; `test <out> --seal-open --light-show --beat-anim --loot-bags --seal 40` -> `var_b.txt` | a: PASS - four leaves stand with LAST 30, both seal pieces stand and are named, 'route with the 6 standing piece(s) out: FREE, 133 m', ShotActivateDamage 5. b: PASS - 6 nodes sunk ({4: 4, 1: 2}), 'route ... as built: FREE, 133 m', the clock names nothing, 7 PositionLightControl, the beat objects 'ZIKLNKOBJ with its StartAnim'. Both archives deleted |

The van's five key-framed bodies still stand at F07's place, 30,083 from their entities (check()'s notes; the next
stage's van_hvk); the nine static bits of `V_Van_Reflection` lie at F07's origin = under the coat check, y -183..-66,
below every floor (MEASURED inline, kl_route's grid): in nobody's way.

### L1.4 GUESS / ASSUMED (each marked in the file)

- GUESS: every spawn row (measured only: on the mesh, on free floor, in no bound or kill box), every camera, stage
  box and trigger of team mode, the loot's places, turns and values, `SEAL_AT` 75 s, `DOORS_AT` 10.4 s, the exit and
  escape-area boxes, `ESC_AT`, `VAN_WAIT`, the bound and kill boxes, every wording in `TEXTS`, the choice of `LINES`.
- ASSUMPTION: a body switched off by a DeactivateGeom at run time stops colliding - here a STATIC placement (the bank's
  vault door is key-framed); the campaign's own storage `HeroColi` is the precedent. If not: `--seal-open`.
- NOT KNOWN: whether 'heroes only' collision (flags 0x108) stops a Fragile Alliance player at all, and whether it stops
  an AI heister or a policeman. kl_route counts it for everybody. If it stops nobody, there is no gate and no harm.
- ASSUMPTION: the music plays from the load (nothing starts it); 'Doors_Opening' un-muffles it (from the names; the
  suppress boxes are not hidden in the file, so the message may change nothing).
- ASSUMPTION carried from the study: a piece sunk 1,500 under its room does nothing to the room's draw list (G1.6).
- GUESS: a level bound / a kill box does something useful to a player who steps off the slab; the kill boxes keep
  the campaign's field values ([1, 1, 0, 0, 'CheckInsideEnter', [], 0, 'FA_DieFromSelf', 'OFF', 'Placholder_Died', 1];
  F07's van has [1, 0, ..., 0]: fields 1 and 10 differ, their meaning was not read).
- ASSUMED from vtables only: which slot is a controller's init (13) and step (25) - consistent over the three kinds,
  not read further.
- Nothing was LOOKED AT: no picture of the briefcases on the counters was rendered.

### L1.5 For the next stage

- **Build with `python tools/kl_fa_club.py test <out> --keep`**; in a script `r, folder = kl_fa_club.build(out)`.
- **Squads** (L2): `campaign_names()` returns the kept squads beside `tuple(KILL)`; `NO_AI` becomes a real flag and
  `KNOWN_NO_AI` conditional as in the bank; the strip of `AttachGeomToBone` / `WarnBehaviourRout` goes into `strip()`.
  `YokoGuards` needs its 'active' flag in data, `Rave#01` stands off the mesh (club 8.2 item 5).
- **The beat's fast way**: the two dance-floor squads' field 8 -> a counter (free: `Gameplay!020_Loot!FollowPlayers!
  TriggerCounter`) -> `R + ROLE['seal off']`; the clock stays. A free-object list stands above `KEEP_MORE` in the file.
- **Police that arrive**: F07's squad groups re-placed on the pavement's mesh strip (x -3765..5786, z -3500..-2650; only
  x -1200..1800 has collision floor) as `kl_fa_bank.place_hall` does. LESSON OF THE BANK'S RUN V2 (re/bank_campaign.md,
  tonight): police standing in the mouth of the only exit killed the crew - the queue lane is 0.96 m of mesh and 12.5 m
  long. The west / east bound boxes begin at the slab's edges: squads come THROUGH them (ASSUMED harmless for AI).
- **The van** (L3): `park_van` -> `kl_map_escape.van_prepare`, wire -> `van_wire`, build inside `van_layer`; `_KEEP`
  holds the van already. The slab is 30 x 8 m: the police rows are at z -2760 / -2830 so that a lane along z -3100 has
  250 either side; the east bound begins 8.2 m after a stop at x 1000 (the bank's rule wants 10 m: move the stop or
  the bound). The boarding place must be on the slab; the road's height is a constant (no floor west of x -1200).
- **Music**: the build is complete without it. The stream file's extension must bring 12 clips (check() prints them from
  the built .WHD): `Music/InHouse/Japan/M05_A/M05_A_Club_Clean.wav`, `_Clean_3D`, `_Muffled`, `_Muffled_3D`,
  `M05_A_Club_2_Clean.wav`, `_2_Clean_3D`, `_2_Muffled` (the two interleaved four-layer sets 'M05_A_Club_Layers' 32.4 MB
  and 'M05_A_Club_2_Layers' 49.5 MB; the second set's fourth layer `_2_Muffled_3D` is named by no object) and
  `SFX/Ambiences/M05_A/Inside/Club_Entrance_Ambience.wav`, `.../Inside/M05_Club_Ambience_01.wav`,
  `.../Inside/Yoko_Office_Ambience.wav`, `.../Outside/Roftop/Ambience_Rooftop_M05_A.wav`, `.../Outside/Street/Street_01.wav`.
  Then `kl_fa_bank.use_stream(<file>)` before the build (the bank's `--str`; not yet a flag here).
- **finish()** is where anything goes that needs chunk numbers or the .LOC; check() takes no flag and reads what the
  build did off the level.

### L1.6 Open

- The 'no ZSquadScript' finding stands until the squads are in.
- The gate is invisible. Whether to shut the ENTRANCE DOOR as the campaign does (a visible 'exit blocked') is open: it
  needs `Doors!Entrance!CloseEntranceDoor` (a `MatPosAnimProxy`, frames 0..50) and a Dead Men door clip that plays.
- AI heisters walk the mesh: nothing holds a bot at the seal (the study's station 8, 'wardrobe: hold until the door
  goes', is the bots' stage's).
- Van: stands in sight 18 m west of the slab with F07's drive; vans 2 and 3 are dropped.
- The upstairs bars' loot (the study's four stacks) waits for the stairs to be proven.
- `ZEnvSampler` x 3 stays as on Late Night Opening; `flat` takes a second class with one word in build() if a load says so.
- Team mode / Undercover Cop: spawn sets placed and measured, nothing else thought through.
- Nothing ran in the game; no picture was rendered.

(end of Stage L1; committed as 95ff22a)

## Stage L2 - the enemies, the beat, the music (tools/kl_fa_club.py, second half)

STATE: DONE (2026-10-11 21:05; the stage was cut off once about 20:41 after its first passing build and continued from
the working tree - the second sitting re-ran every build and check below, corrected one claim (L2.1 'STAGED') and one
check (L2.3 'police-slab'), and added `--str`). `tools/kl_fa_club.py` keeps 40 of the campaign's guards in 17 squads,
staged, brings ten of F07's police onto the pavement when the seal opens, opens the seal by 'both dance-floor squads
wiped out' or the clock, and still builds the round without enemies (`--no-ai`). NOTHING RAN IN THE GAME. Kept:
`C:/kl_scratch/club/l2/build/F07+M05_A campaign/` (F01_Main.zip 150,086,073 bytes, sha1 b64b85eb2b8c...; three builds
of the same command gave that archive). l1's build is deleted (rebuild: `test <out> --no-ai`).
Scratch `C:/kl_scratch/club/l2/`: `s/` (sq.py squads of a level, sqnamed.py / amact.py / gates.py the stock censuses,
los.py / hidden.py / seen_strip.py / plan.py lines of sight, f07free.py free host objects), `out/` (every output named
below). No other file of the repo was edited; no per-level table of another tool gained an entry. kl_fa_bank.py has
another job's uncommitted changes in the tree: every `BK.` name this file uses is in the committed version too.

### L2.1 What was built into the module

| part | where | what |
|---|---|---|
| the squads that stay | `SQUADS E1 E2`, `squad_plan()`, `campaign_names()` | 17 squads, 40 men: the nine usable as they stand and eight 'first run' squads on the round's way. kl_fa_author's rule wants a behaviour rout; 16 of the 17 have none, so the rule is widened: only plain squad kinds and what `STRIP` takes off, a ZSoldier for every actor, a start child that holds a rout or a SquadModifierBehaviour |
| what comes off them | `STRIP MESSAGE_KINDS`, `strip_squads()` | MiniCutsceneRout 3, MiniCutSlot 3, MiniCutPosObject 7, AttachGeomToBone 18 (each prop hidden with its group), WarnBehaviourRout 1; 5 message-list entries that would name a node left without a controller are cut in wire() |
| men moved | `MEN MAN_OFF MAN_IN` | 7 by table (below), 3 who stood 19 - 30 beside the mesh put 15 inside it |
| stages | `SQUADS`' second column, `STAGED MOD_ACTIVE SQUAD_ACTIVE SQUADS_AWAKE OFFICE_AT WALK_BOX FLOOR_BOX`, ROLE 'office timer' / 'walk box' / 'floor box' | 'load' 7 squads (15 bouncers, ZSquadScript field 3 = 1); 'office' 2 (4 men) by F07's `RivalMercs!Timer` 10 s after the round-start event = GO + 1.2 .. 1.6 s; 'walk' 2 (5) by the box at the inner office door; 'floor' 5 (13) by the box on the walkway's upper half; 'open' 1 (the 3 hunters) by the beat's gate |
| rows | `STOCK_ROWS`, `BK.soldier_rows` | stock Fragile Alliance rows by weapon class: swat 23, cop 12, sharp 5 (read back: 23 x eCustom 50 / 175, 12 x eCustom 50 / 100, 5 x eCustom 75 / 175) |
| police that arrive | `ARRIVE ARRIVE_SLAB ARRIVE_START ARRIVE_Y POLICE_ARRIVE POLICE_ON_SLAB LANE_CLEAR`, `place_police()`, `police()` | four of F07's squads (`Gameplay!030_AfterLoot!030_FinancialAlleyExit_Left / _Right`, `...ExitStreet_Left / _Right`), ten men, on the pavement's mesh strip beyond the slab's two ends (x -2500..-2100 and 1950..2350, z -2750 / -2850), started by the gate naming their `10_RunToCover`; ten cover points at the slab's ends |
| the beat | `BEAT_SQUADS GATE_WAYS SEAL_AT`, ROLE 'floors counter' / 'gate' | `SecondRun!Dance#01` and `Dance#02`: field 8 ('wiped out') -> `Gameplay!020_Loot!FollowPlayers!TriggerCounter` (2) -> the seal's DeactivateGeom + the gate's `Way#01`; the clock (`SEAL_AT`) -> the same DeactivateGeom + `Way#02`; both ways name the hunters' `HuntBehaviour` and the four `10_RunToCover` |
| checks | `Sight`, `way_views()`, `LANE_VIEWS LATE_CLEAR POLICE_CLEAR ACTORS_LIVE`, check()'s 'enemies' block | L2.3 |
| flags | `--no-ai --squads-awake --no-police --police-strip --office S --dead-men-rows --str FILE` (`--police-slab` is an alias of the default since review round 1) | docstring |

**What differs from the stage's order, each on purpose - for the lead to confirm:**
- THE HUNTERS DO NOT COME INTO THE WORLD IN THE WARDROBE. The campaign has them there, 1.3 - 3 m from the round's own
  station (MEASURED `out/sight_neg.txt`: 'campaign hunter, wardrobe seen from 8 of 103' places of the way) - the bank's
  review finding 6 again. They are re-placed in the second floor's lounge over the stairs ('hunter as placed seen from
  0 of 103'), 21 - 27 m of mesh from the stair landing: they come DOWN to the wardrobe on foot. GUESS: the three places.
- `SEAL_AT` 75 -> 120 s (about 111 s after GO). With 40 guards on 80 m of way a clock of 66 s after GO would nearly
  always come before the two squads are dead, and the beat would be no beat. GUESS; `--seal S`.
- The front office comes at GO + 1.2 .. 1.6 s (`OFFICE_AT` 10.0), not + 2 s: the nearest START point is 7.8 m from
  the inner doorway and nobody is to stand in it when four men come into the world 2 m behind it. `--office S`.
- `YokoGuards`: its 'flag' is the STAGED value written into its `SquadModifier` child (below), and both men are moved
  2 m into the front office's south half - at the campaign's place one is seen through the inner doorway from a START
  point ('Yoko guard, campaign place seen from 1 of 8').
- `Rave#01`'s two men go from behind the rave bar (105 / 154 off the mesh) to its public side.

**STAGED - corrected in the second sitting.** 'office', 'walk' and 'floor' start a squad that has NO behaviour rout by
naming its SquadModifierBehaviour child whose field 4 (`EActivationModifier`) is `eAM_Activate` - the campaign's own
way (six 'Alert' children have the value; it is written into the three that lack it). The first sitting called this
'used by no stock Dog Days level'. MEASURED on all levels (`s/amact.py` -> `out/amact.txt`): no FRAGILE ALLIANCE level
has such a modifier, but the STORY levels have 19 (L02 8, L06 4, L09 2, L11 5), 16 of them on a squad with field 3 = 0,
named by a TriggerBox (6), a GatePath, a TriggerCounter, a CheckPointSave - and one (L11) on a squad without any rout,
from a TriggerBox, exactly this file's 'walk' / 'floor' case. So it is stock behaviour that no build of OURS has run.
Not in stock: the value named from a TriggerDelay2 (the 'office' stage; ASSUMPTION that the sender does not matter -
F07 names modifiers from a TriggerDelay2 18 times, with NotSet or Deactivate). If it fails, 22 men never come: `--squads-awake` (all 17 squads
in the world from the load).

**The gate** (`Gameplay!RunToEscape!RunToEscapeGate`, F07's own). MEASURED `s/gates.py` -> `out/gates.txt`: stock names
a GatePath from a TriggerCounter (F08) and from TriggerDelay2 (F05 F07 F08), and a GatePath names a DefendBehaviourRout
once (F01), else modifiers, timers and geom switches. ASSUMPTION (GateGroup not read in kl2.exe): only the first path
passes; if both do, the five routs are named twice. The SEAL does not hang on the gate.

**Music** (the stage's item 4). Nothing new had to be wired: the two tracks are the kept audio subtree's own layered
stream objects (`Locations/M05_A/M05A_Audio.zip!STREAMS!Inside!Music!Club_01_* / Club_02_*`, `out/music_nodes.txt`),
which nothing starts and nothing stops; L1's host AIDWrapper sends 'Doors_Opening' to `GeomActivator_Door_01 / _02`
at the round start (the doors are open from the load); with `--doors-animate` the door timer sends it. The light show
is OFF by default (L1.1; `--light-show --beat-anim`). check(): 'music: 0 of the 7 clips of the club's two tracks have a
record in the built .WHD'. THE 12 CLIPS THE STREAM FILE LACKS are L1.5's list, unchanged - and MEASURED against the
bank's extended file too: `test <out> --str <work>/build/v_vault/PC_Def.str` (read only) lists the same 12
(`out/var_a.txt` line 77). `--str FILE` is now a flag (kl_fa_bank.use_stream) for the build after the club's extension.

### L2.2 The build

```
python tools/kl_fa_club.py test C:/kl_scratch/club/l2/build --keep     (80 s; 'RESULT: PASS', exit 0: out/test3.txt)
python tools/kl_fa_club.py check "C:/kl_scratch/club/l2/build/F07+M05_A campaign"            ('PASS': out/check2.txt)
```
Lines: 'the police that arrive: 4 of F07's squads re-placed (10 men) on the pavement's mesh strip beyond the slab's two
ends, out of sight'; 'M05_A: 17 squads stay (40 men); taken off them: {MiniCutsceneRout 3, MiniCutSlot 3,
MiniCutPosObject 7, AttachGeomToBone 18, WarnBehaviourRout 1}; 18 props hidden'; '7 men re-placed (MEN)'; '3 men stood
beside the navigation mesh and were put on it: WaitingRoom\Guard#02 20 off, Dancefloor02a#02\Guard#03 30 off,
...\Guard#04 19 off'; 'enemies: 17 campaign squads (40 men): 7 in the world from the load; round start + 10 s -> 2
(front office); the box at the inner office door -> 2; the box on the walkway -> 5; the gate -> 1 hunt + 4 of F07's
police squads; 5 dead entries cut from the squads' message lists; soldier rows: {swat 23, sharp 5, cop 12}';
'.ANM joined: clips +0' with the guesses 'Bouncer plays copy of Thug', 'Army plays copy of Swat_02' (kl_anm STAND_IN);
'verify: problems: 1'; 26,824 entities.

### L2.3 The checks (all on the kept build; outputs in `C:/kl_scratch/club/l2/out/`)

| check | command | result |
|---|---|---|
| verify problems = KNOWN | check()'s 'verify:' lines | **1, known**: 'sound: 5 stream clips are not in the merged stream file' (the 12 clip names). L1's 'no ZSquadScript' is gone |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | **0 CRASH, 0 BROKEN**, exit 0, 'problems: 0'; 2 DEGRADED: no bot squads (a later stage); '5 of 21 squads are named by no object' = squads of the 'load' stage, which are in the world from the load (field 3 = 1) and need no start |
| one cover list | check() | 'cover lists (FFCoverList): 1' |
| route | check() | as built 'NOT free; crossed: [HeroColi]'; 'office -> queue lane, club end: FREE, 122 m'; 'with the 1 standing piece out: FREE, 133 m' |
| every man on the mesh | check() (kl_route.stations near 30, the seal out) | '17 campaign squads (40 men) + 4 of F07's police squads (10 men); 50 of the 50 men on the mesh part of the START and on free floor within 30 - 10 of them police on the mesh strip beside the slab, where there is NO collision floor (ASSUMPTION: an AI walks the mesh)' |
| the places their routs go by | check() | '19 places; 1 not on the START's mesh part': the hunters' `SearchBox` (546, 638, 740), a volume, the campaign's own. The police's ten cover points: all on that part and on free floor (else FAIL), 'the nearest 12.0 m from the lane's mouth; men and cover points 250 and more from the van's line' |
| no dropped node named | check(); result.json | 'dangling' [] ; no list of a squad node names a node that is not there or a node of its squad without a controller |
| behaviour kinds | check() | 'ZSquadScript 21, SquadModifierBehaviour 19, ZSoldier 50, TriggerBox 4, HuntBehaviourRout 1, DefendBehaviourRout 8, RunToCoverBehaviourRout 4, RunToCoverPosInfoRout 10': all in kl_fa_author.PLAIN / BEHAVE (ran live on Retomoto / the bank). The first for a build of ours is not a kind but a VALUE: 'started: {floor 5, office 2, walk 2, load 7, open 1}; 9 of them by a SquadModifierBehaviour with eAM_Activate' |
| squads start where they should | check() | each squad's field 3 against its stage, each start child named by its stage's object, the two boxes 'in use, once, criminals only' (TriggerBox fields 0 / 15 / 14 = 1 / 0 / ECPS_FA_MERCONLY: the bank's review finding 4), the gate's two paths name the same 5 objects |
| the beat | check() | 'Dance#01 + Dance#02 wiped out -> counter of 2 -> [GeomDeactivator_DriveInVan, Way#01]; the clock (120 s) -> the same'; chain 'round start -> [Timer_MissionBriefing, Timer, Timer, Activator_VanSound]' |
| nobody comes into the world in sight | check(): `Sight` (lines through kl_route's collision grid, eyes 160, head 160 / chest 90) from every place the crew can be before a stage | 'office 4 men / 39 places / nearest 430, walk 5 / 55 / 1367, floor 13 / 91 / 693, open 13 / 103 / 324 - nobody in sight of one'. The check does fail: `sight_neg.txt` (the campaign's places: seen) |
| police who come back | check() | '8 bodies, 7 AFTER_DEATH points; the nearest of the squads' men stands 450 from one'. Nothing adds a police body |
| actors against the limits | check() | 'people: 50 ZFFActor in 21 squads + 16 player bodies (ran live: 99 actors, 55 squads)' |
| chunk table, blocks | check() | 'chunk table: 53873 entries (the tools' line: 69632); .prm 44.8, .fxc 17.8, .ANM 21.6, .WAV 21.4 MB; the five load blocks 139 MB (...: 171)'; '23683 of its indices are dead (the wardrobe takes 20989)' - the study's 53,898 was with the wardrobe appended; here it goes into dead indices |
| written level | `kl_fa_club.py reverify` | 'problems: 0' (26,824 entities, 3,498 .HVK placements, 24 list entries parked) |
| kl_impact | `python tools/kl_impact.py <archive>` -> `impact.txt` | 'problems: 0 in 1 levels' |
| kl_arms | `python tools/kl_arms.py check <archive>` -> `arms.txt` | '0 findings' |
| preflight | `python tools/kl_maps.py preflight <folder>` -> `preflight.txt` | exit 1: **'CRASH 1, RISK 3, NOTE 65'**: CRASH = 'kl_graft.verify reported 1 problems' (the known one); RISK = `ZEnvSampler` x 3 (two lines) and `SoundSpline` x 1, as L1; 'fa:squads' is gone |
| NO_AI still builds | `test <out> --no-ai` -> `var_noai.txt` | 'RESULT: PASS': 26,593 entities, 'verify: problems: 2' both known (the clips; 'no ZSquadScript' = KNOWN_NO_AI), 'enemies: none (a build without squads); the seal opens by its clock'; the timer, both boxes and the counter name nothing (else FAIL) |
| the fall-backs | `test <out> --str <v_vault>/PC_Def.str --squads-awake --police-slab --dead-men-rows --office 12` -> `var_a.txt` (SUPERSEDED by review round 1: `--police-slab` is the default now, so this row no longer tests a distinct fall-back) | 'RESULT: PASS': all 17 squads in the world from the load, Dead Men's rows read back (18 x eRegular 50 / 50, 17 x eAmateur 50 / 50, ...), 'POLICE ON THE SLAB: 2 of the police come into the world IN SIGHT of a place in the queue lane (the cost of that fall-back)'. (The first sitting's check FAILED this variant on exactly those two men although the flag's text says 'in sight': check() now reads a police man ON the slab as that variant and says so; anybody else in sight still fails.) |
| the other flags | `test <out> --no-police --seal-open --doors-animate --light-show --beat-anim --fan-damage` -> `var_b.txt` | 'RESULT: PASS': 26,761 entities, the gate lets in 1 object (the hunt), four leaves stand ('with the 4 standing piece(s) out: FREE, 133 m'), the clock names no seal |

Variant archives are deleted; only the default build is kept.

### L2.4 GUESS / ASSUMED (each marked in the file)

- ASSUMPTION, the largest: a squad WITHOUT a behaviour rout that is in the world fights whoever it sees (16 of the 17;
  the campaign's own form; every Fragile Alliance squad of stock Dog Days has a rout; L11 has one such squad).
- ASSUMPTION: `eAM_Activate` brings a waiting squad into the world (STAGED above), also when a TriggerDelay2 sends it.
- ASSUMPTION: ZSquadScript field 8 is sent when the last man is dead (Retomoto's room counter hangs on it; not seen
  live for a squad that was started by a modifier). If never: the clock.
- ASSUMPTION: an AI character walks the navigation mesh where there is no collision floor (the ten police start on
  the strip beside the slab). If a man falls he falls into a kill box and the wave is thinner: that is what the DEFAULT now avoids (review round 1: the men start on the slab); `--police-strip` is this paragraph's form.
- ASSUMPTION: only the first of the gate's two paths passes (stock use; GateGroup not read).
- ASSUMPTION: the round-start event comes 8.4 - 8.8 s before GO here as on Retomoto (OFFICE_AT, SEAL_AT count from it).
- NOT KNOWN (L1): whether the heroes-only seal stops an AI at all - the three hunters and the police are let in by the
  gate, not by the seal, so they may walk through it either way; the bouncer in the lane stands inside it from the load.
- GUESS: the split into stages, both stage boxes, every place in `MEN` and `ARRIVE`, `LATE_CLEAR` 300, `Sight`'s three
  heights and its tolerance (a drawn wall without collision hides nobody for it; a window's collision does).
- GUESS carried by kl_anm: the bouncers play a copy of the 'Thug' set, 'Army' a copy of 'Swat_02'.
- ASSUMED harmless: the 18 props (flashlights, the wand) hidden with their groups; AI through the bound boxes at the
  slab's ends.

### L2.5 For the next stage

- **L3 (van)**: as L1.5. NEW: the police's cover points keep 250 from the line z -3100 (`LANE_CLEAR`; check() fails
  otherwise), and their men start at x -2500..-2100 / 1950..2350 on the strip - a drive along the strip passes
  THROUGH the west group's start places (z -2750 / -2850 against the lane's z -3100: 250 - 350 off the line) before the
  seal opens; they are not in the world then. `VAN_WAIT` (-3000, 32, -3100) is 500 west of them.
- **Bots (F)**: nothing holds an AI heister at the seal; a hold in the wardrobe until the seal's clock (the bank's
  `GATE_NAME` pattern) reads `SEAL_AT` off the built level. The 'walk' and 'floor' boxes are criminals-only and fire
  ONCE: the first bot through the inner office door starts the walkway's squads.
- **Stream stage**: the 12 clips of L1.5; then `test <out> --str <file>`; KNOWN's first entry goes away by itself
  (check() lists what the built .WHD lacks).
- **Live order** (owner away): `--no-ai` first (the seal, loot, exit box, bounds), then the default, then
  `--squads-awake` if the log shows no guard beyond the 15 bouncers, (SUPERSEDED by review round 1: the slab is the default; the form to try when no police reach the slab is `--police-strip`, whose question is whether an AI stands on bare mesh.)
  What to look for: do the bouncers fight; do four men appear in the front office just after GO; does the seal open
  when the six `Dance#01 / #02` men are dead; police from both sides of the pavement.

### L2.6 Open

- Nothing ran in the game; no picture was rendered.
- The gate is still invisible (L1.6); the entrance door is not shut.
- No dancing crowd, no civilians, no Yoko (the lead's order).
- The upstairs squads (`Lounge#01 / #02`, `Rave#01 / #02`, 10 men) are off the round's way: they are there for a crew
  that wanders, and nothing leads it up (no loot upstairs yet, L1.6).
- `kl_fa`'s DEGRADED line about 5 unnamed squads is its heuristic not reading field 3; kl_fa.py is not this stage's.
- The 'office' squads come 4.3 m and more from the nearest START point, behind a wall: a sprinting human reaches the
  inner doorway about when they appear. Measured as 'out of sight of every START point', not of a moving player.
- The bank's regression was not re-run: no shared file was edited.

(end of Stage L2)

## Stage L3 - the escape (tools/kl_fa_club.py: F07's van on a way-point plan along the pavement)

STATE: DONE (2026-10-11 21:50). `tools/kl_fa_club.py` lays F07's first key-framed van on a straight road along the
pavement, FROM THE WEST, and check() has a block 'the escape'; every check of the stage passes and all of L1's / L2's
still do ('RESULT: PASS', the same one known verify finding). NOTHING RAN IN THE GAME. Kept = 'THE BARE MAP' the
finishing stage starts from: `C:/kl_scratch/club/l3/build/F07+M05_A campaign/` (188 MB: F01_Main.zip 150,075,064 bytes,
sha1 2eb2edb526ff..., finished = lightened + briefcases + texts; result.json, log.txt, graft.txt, NEW van.json). A
second build with `--plan <its van.json>` gave the same archive and the same van.json. `C:/kl_scratch/club/l2/build`
is deleted. Scratch `C:/kl_scratch/club/l3/`: `s/` (drawn.py what the map DRAWS along the pavement, plan0.py the plan by
the unchanged tool, plan1.py the plan, rooms.py room boxes and the vision grid, dl.py drawn_lane with its negative
controls), `out/` (every output named below). No other file of the repo was edited: kl_map_escape.py is only called.
ONE THING IS NOT AS THE STAGE'S ORDER READS, and is said first (L3.1): 'van-check 0 faults' holds on the DRAWN
pavement, through a wrapper of this module; the plain `kl_map_escape.py van-check` has 217, every one the missing
collision floor outside the slab.

### L3.1 The hard part: a drive where nothing has collision - what was measured, and how the tool is used

- **The unchanged tool refuses every road that leaves the slab** (`python C:/kl_scratch/club/l3/s/plan0.py <bare graft>`
  -> `out/plan0.txt`): the planner holds each ray of the lane against 'the road under it', so the study's line gives
  'FAULT only -340 of clear lane before the stop (least 2000)', 'only 610 of clear lane after the stop (least 3000)';
  a drive that stays on the slab cannot be had either (the slab is 30 m, the least drive is 20 + 30 m: 'only -39 ...',
  'only 1099 ...'). van_check does the same per key ('drive key N: no ground under it').
- **What is DRAWN there was never looked at (the study's open point). It is now** (`python C:/kl_scratch/club/l3/s/drawn.py
  <bare graft>` -> `out/drawn.txt`: every mesh of every map entity that has a model, by kl_fa_loot.Assets, in world
  space, rastered from above into 20-unit cells over x -7200..7600, z -3700..-2500; 1,707 model roots read):
  - the pavement is drawn at **y 30.0 under every cell** of the eleven rows tested between z -3460 and -2620, from
    x -7200 to 7600: seven pieces `M05_A_Outside_Street_01a\SO0100_M05_Street_Wide_A_03, B_04, B_03, B_02, B_01, B_05,
    A_01` (sidewalk tiles `Stone_SidewalkTiles_07a_M05` + a dirt overlay; the asphalt of the road is y 10 beyond the
    kerb). So the collision slab (y 30) is one piece of a pavement 148 m long and 8.8 m deep that is drawn at the
    same height everywhere;
  - **nothing is drawn 25..220 over it between z -3280 and -2880** (the map at the end of `drawn.txt`): street lamps
    `PC0100_JPN_Metal_OldStreetLamp_B_Group_06 / 04 / 01 / 08` at x -3200, -1200, 800, 2800 and two bins
    `PC0100_JPN_Trashcan_B_02 / _01` at x -3000 and -520 stand at z -3300..-3400; the house fronts at z -2620
    (`SO0002_M05_Facade_K_Base_01`, `..._Facade_A_Base_01` glass x -1420..-400, `FrontBuilding`, a switch box at
    x 1680); four parked cars beyond the kerb (z -3520..-3750);
  - west of x -400 the fronts are modelled buildings; **east of x 2100 the street's north side is a glow plane**
    (`M05_A_Outside_Roof_01a\UNIQUE_StreetGLOW`, material `Effects_StreetGLOW_DistFADE`, z above -2860) - the faked
    far end of the street. Hence the side: the van COMES along the real fronts and LEAVES into the faked distance.
- **How the tool is used: the road's height is DECLARED** (`PAVEMENT`, class `Pavement`, `pavement()`).
  `Pavement` is kl_map_escape.Ground with one more floor: inside `PAVEMENT` = x -7200..7600, z -3460..-2580 a vertical
  line that meets no collision floor within the tool's own tolerance (25) of y 30 meets one at y 30, owned by the REF
  id -5 that no entity has. `pavement()` puts it in kl_map_escape.Ground's place for the length of the plan and of
  van_check (the idiom of kl_map_escape.van_layer, which swaps kl_hvk.join). Everything else is the tool's own:
  collision in the van's body, convex bodies, the four lengths, the bounds, the boxes at the stop, the camera's sight,
  the collision file. kl_map_escape.py IS NOT CHANGED (it is a finished file, and this is no bug of it: the study
  foresaw 'a road-height constant: small tool change' - it is done from outside instead).
  WHY THIS IS HONEST AND WHERE IT IS NOT: a key-framed van needs no floor (Retomoto's first drove 40 UNDER its road:
  re/retomoto_fa.md 9.3); what the height must be is what is DRAWN, and that is measured - by drawn.py once, and by
  check() on every build along the actual drive (`drawn_lane`, L3.3). NOT covered: what a key-framed van does to
  people in its lane where there is no floor, bodies and dropped money at the slab's rim, a model switched off or on
  at run time. The plain tool's verdict is printed beside the wrapper's on every check.

### L3.2 What was changed (one file, tools/kl_fa_club.py, 1,866 -> 2,332 lines)

| part | where | what |
|---|---|---|
| the road | `ROAD` (replaces `VAN_WAIT`) | `arrive` (-5300, 30, -3100), (-2800, 30, -3100); `stop` (-300, 30, -3100) at = origin; `leave` (3000, 30, -3100), (7300, 30, -3100); heading and camera not forced |
| the drawn road | `PAVEMENT`, `Pavement`, `pavement()` | L3.1 |
| the plan | `van_plan(src)`, `plan_of(file)`, `lay_van(P)`, `van_path()`, `PLAN NO_PLAN` | kl_fa_bank's four, with this file's ROAD; van_plan runs inside pavement() |
| the build | `build(out, log, plan=None)` | bare graft into `<out>/_bare` (35 s, 284 MB, deleted again; `kl_maps.one(..., m_drop=M_DROP)`) -> plan -> `with kl_map_escape.van_layer(plan), doors(): kl_maps.one(...)`; -> (result, folder, plan, what was done to the van) - FOUR values now, as kl_fa_bank.build |
| the layer | `prepare_host()` | `park_van()` is gone: `kl_map_escape.van_prepare(S, PLAN, log)`; the escape marker held against the plan's drive (`LANE_CLEAR`) |
| | `wire()` | `kl_map_escape.van_wire(sc, PLAN, log)` |
| places moved for the van | `ESC_AT`, `POLICE`, `BODIES`, `ARRIVE` | below |
| test | `test(out, keep, log, plan)`, `--plan FILE`; NEW command `van-check <folder>` | van.json beside the archive (kl_map_escape.van_build's form: tag, plan, van, wired, hvk, check) |
| check | check(): 'the escape'; NEW `drawn_lane()`, `van_check()`; `BOARD_NEAR BOUND_AFTER MOUTH_SIDE BOARD_CLEAR FED_CLEAR STREET_ROOM` | L3.3 |

**The plan** (MEASURED: `out/plan1.txt`, the build's lines in `out/test1.txt`, `van.json`): 0 faults, lane empty on the
first pass, no cut.
```
waits (-5300, 32, -3100) heading 90 -> 50.0 m in 7.2 s -> stops (-300, 32, -3100) heading 90 (rear box (-637, 30, -3100))
      -> 70.0 m in 8.48 s -> ends (6700, 32, -3100) heading 90;  600 path points, y 30.0 all the way
camera eye (-2100, 360, -3100) (cam_spot: 18 m BEHIND the standing van, 330 over the pavement; '15 of the 144 places
      tried see the stop and the drive 850 and 2500 after it; this one sees the end')
```
'kl_map_escape: ... 563 position and 550 rotation keys rewritten in place (391 of them the drive, stop at key 159);
drive in 5063 -> 5000 (x 0.99), away 7019 -> 6999 (x 1.00); crash pieces -120..120 to the side; 19 objects moved' -
**F07's own drive, unscaled, laid straight**. 'exit trigger Gameplay!EscapeSetup!otrExitLevel calls ...
EscapeVehicle_Animation_F07'; '.HVK: 9 static placements of the van's subtree cut, 5 key-framed placements of the van
put at its waiting place' (.HVK 1,910,256 bytes). F07's second and third van are NOT in the level (L1's decision,
kept): one `OnlineEscAnimatedVehicle`, one `FakeTarget`; check() fails any other count.

**Why from the west, why the stop at x -300** (GUESS as a design; each number below is MEASURED by check()):
- The van's nose (250 ahead of its origin) stops at x -50: **168 short of the line straight out of the lane's mouth
  (x 118)** - the arriving van sweeps the slab from x -1193 to -50 (11.4 m) and never passes before the door the crew
  comes out of. The study's road (stop x 1000) swept 22 m of slab in front of it; `MOUTH_SIDE` 150 is check()'s rule.
- The rear doors (the boarding box rides 337 behind the origin) are at (-637, 30, -3100): on the slab, 5.6 m inside
  its west edge, 3.5 m from the kerb's rim, 2.4 m from the nearest warn box (the kerb's), 8.9 m from the lane's
  mouth; 'queue lane, street end -> boarding place in the collision (the seal out): FREE, 7 m'.
- 50 m in and 70 m away are F07's own lengths. It waits at x -5300: where the pavement is drawn, 15 m west of the
  mesh strip's end (x -3765: it stands OFF the navigation mesh - the bank's van stood on it, L3.4 there) and 14 m
  inside the street room's west edge.
- It leaves east: over the rest of the slab with its passengers (the away leg must cross the slab either way) and
  through the east level bound 21.3 .. 26.8 m after the stop - the stock form (kl_fa_bank L3.3: stock vans pass one
  10.9 .. 105 m after their stops); the west bound 15.1 .. 9.3 m before the stop, empty.

**Places that moved for the van** (all in this file; each was a GUESS of L1 / L2 made before the stop was known):
- `ESC_AT` (300, 30, -2800) -> **(-640, 30, -2800)**: the escape marker (and jump point 06_Exit, and the route's last
  station) beside the lane, level with the rear doors - 300 from the drive, 295 from the boarding place, 7.8 m from
  the lane's mouth. NOT over the stop and not in the sweep (the bank's review finding).
- `POLICE` / `BODIES`: the four points and bodies that stood at x -900..-600 (ON the new marker, 3.4 m from the rear
  doors) are now east with the other three: x 900..1500, z -2760, the eighth body (1600, -2830). The nearest point of
  police who come back is 15.2 m from the boarding place (`FED_CLEAR` 10 m), 8 m from the lane's mouth; the nearest
  squad man 359 from one (was 450; `POLICE_CLEAR` 100).
- `ARRIVE`: two cover points of the WEST police squads, (-950, -3400) and (-800, -3400), stood 4.3 and 3.4 m from the
  rear doors of the standing van; now (-1160, -3410) and (-1000, -2680). The nearest cover point is 5.4 m from the
  boarding place (`BOARD_CLEAR` 5 m), 11.2 m from the lane's mouth (rule 10 m), 250 from the drive.

### L3.3 The checks (all on the kept build; outputs in `C:/kl_scratch/club/l3/out/`)

| check | command | result |
|---|---|---|
| build + finish + check | `python tools/kl_fa_club.py test C:/kl_scratch/club/l3/build --keep` -> `test1.txt` (112 s: bare graft, plan, build, finish, check; 84 s with `--plan`) | **'RESULT: PASS'**, exit 0; 26,824 entities, 20 rooms, 'verify: problems: 1' (the known stream clips) |
| the same archive again | `... test C:/kl_scratch/club/l3/again --keep --plan "<kept>/van.json"` -> `again.txt` | 'RESULT: PASS'; sha1 2eb2edb526ff... = the kept one; van.json byte-equal; deleted |
| check alone | `python tools/kl_fa_club.py check "<kept>"` -> `check.txt` | 'PASS', exit 0 |
| **van-check** | `python tools/kl_fa_club.py van-check "<kept>"` -> `van_check.txt`; inside check() with the plan | **'0 fault(s)' on the drawn pavement** (van_check and the escape cameras' table): 'keys 0.0 off the road height at most, largest step 58, nose up to 0.9 degrees off the tangent, crash pieces up to 120 to the side; lane (5 rays, every 20, 350 before and 600 beyond): clear'; 'boarding box at the stop: (-636, 32, -3094); key-framed placements 5, at most 1.1 from their entities'; wait / stop / end within 25 of the plan's. One note: 'no define FAEscCameraLAST' = the stock form |
| ... the plain tool | `python tools/kl_map_escape.py van-check "<kept>"` -> `van_check_plain.txt` | exit 1, **217 faults: 211 x 'drive key N: no ground under it', 5 x 'in the van's lane: no road within 25 of the drive's height' (one per ray), 1 x 'camera ...: the eye is outside the map: no collision above or below it'** - nothing else. check() counts them on every run and FAILS on any fault of another kind |
| what the van drives over | check() | 'of the 391 keys of the drive 180 have a collision floor under them (x -1193..1796: ColiObj_01), 211 the drawn pavement alone (PAVEMENT y 30); the stop: origin y 32.0, the floor under it y 30.0' (the stop must stand on real floor, else FAIL) |
| **the lane, drawn** | check(): `drawn_lane`; `python C:/kl_scratch/club/l3/s/dl.py <bare graft>` -> `dl_bare.txt` | 'DRAWN in its lane (the map's models, 128 triangles near it; 5 rays every 20, 350 before and 600 beyond): a surface within 25 of the road under 3240 of 3240 samples, y 30.0..30.0 (SO0100_M05_Street_Wide_B_04 x 500, B_03 x 500, B_02 x 500, B_01 x 500, B_05 x 500, A_01 x 375, A_03 x 365); in the van's body (25..220 over the road): nothing'. The test does fail: the same on the line z -3300 finds the four lamps and two bins, on z -2620 six pieces of the fronts and 214 samples without a surface, on z -3560 the four parked cars |
| the lane, collision | the plan's own test on the bare graft (`test1.txt`, 'van plan for ...') and van_check's on the finished build | both clear |
| **fake-test** | `python tools/kl_fa_bots_dyn.py fake-test <work>/build/z_route/M01 <work>/build/rt_full6/retomoto_full "<kept>"` -> `fake_test.txt` | **'RESULT (fake-test): PASS (grid control 1, parked control 1, lattice 3)'**; the club: 'FakeTarget Animation/F07/F07_Escape_Vehicle_01.zip at (-5316.6, 32.0, -3099.9): inside; kl2's arithmetic: cell (1, 0, 4) (a record)', the only FakeTarget of the level (vision space x -6725..10906, y -31..3000, z -7074..6724). check(): the same, and 'on the drive: at the stop inside; at the end of the drive inside' |
| the street's room | check(); `python C:/kl_scratch/club/l3/s/rooms.py <folder> wait=... stop=... end=... cam=...` -> `rooms.txt` | 'the room box of M05_A_Outside_Street_01a (1 record(s): x -6725..9274, y 20..3000, z -7074..-2489) holds: waits yes, stops yes, ends yes, the camera's eye yes' |
| **the boarding place** | check() (`kl_route.stations` near 30, `kl_route.route`); `python tools/kl_route.py stations "<kept>" START=2817,342,2420 "lane street end=105,20,-2600" "escape marker=-640,30,-2800" "boarding place=-637,30,-3100" "van stop=-300,32,-3100" "van waits=-5300,32,-3100" --near 30 --open "M05_A_Inside_Entrance_01a\HeroColi"` -> `route_stations.txt` | 'boarding place at the stop (-637, 32, -3095): on the slab True, mesh True, part 0 (the START's: 0), free floor within 30: True; the van's stop: mesh True, part 0'. stations: '5 of 6 places reached ... 5 of 6 on the mesh, on 1 part(s)'; the WAITING place is 'OFF the mesh by 1535 ... NOT reached' (exit 1 for that): as it should be |
| ... reached | `python tools/kl_route.py walk "<kept>" --from "lane street end=105,20,-2600" --to "boarding place=-637,30,-3100" --open ...HeroColi` -> `route_board.txt`; the whole round with 13 places -> `route_open.txt`; as built -> `route_built.txt` | 'FREE, 8 m of cells, floor y 30..30 ... the mesh way: 35 samples, all free'; the whole round 'RESULT: FREE'; as built 'NOT FREE', the leg through the seal alone |
| ... **the way an AI is given** | check() (`way_views` on kl_route's mesh model) | 'lane's street end -> boarding place: on the slab all the way; by way of the escape marker: 94 samples off the slab (as far as x -2326)' - L3.4 |
| the slab's rim against the bounds | check() | L1's three edge tests still pass (a walker 1 m before each open edge in no bound, 1.2 m beyond it in one); '3 LevelBound in their place ..., 3 kill boxes; 0 of the 93 spawn points, player groups and stations inside one'; neither the stop nor the boarding place in a bound, warn or kill box; the two bounds on the drive as above |
| path blocker | check() | 'PathBlockerVan at (-294, 147, -3096) half (101, 130, 250): the boarding place is outside it' |
| exit box | check() | 'exit box x -1150..1750, z -3450..-2650: on the slab True; holds the pavement station True, the lane's street end False'; 'holds the van's stop True, the boarding place True; drive in 7.2 s' (the stock form) |
| nobody in the lane | check() | 'the escape marker stands 300 from the drive, 295 from the boarding place'; 'of 52 spawn points, player bodies, men, cover points, the marker and stations on the pavement the nearest to the drive is FinancialAlleyExitStreet_Right\10_RunToCover\RunToPosInfo#02, 250 from it' (`LANE_CLEAR` 250) |
| the police and the rear doors | check() | 'the nearest cover point of the arriving squads 5.4 m (5 m wanted), the nearest point or body of police who come back 15.2 m (10 m wanted)' |
| **the camera** | check(); `kl_fa_club.py van-check` (kl_map_escape.check's table) | 'EscCamera01_01 ... mode eFMM_LookFromPos ... Dog Days' eye: (-2100, 360, -3100), 330 over [the pavement]; looks at the player' - F07's own camera, the mode that puts the eye at its place; 'the escape camera's eye: 330 over the road, 18 m from the stop, over the drawn pavement (no collision under it); between it and the van at the stop: nothing'. The in-van camera eFMM_LookAtPos as stock |
| is the waiting van in sight | check() | 'waits at (-5300, 32, -3100), 50 m from its stop, off the navigation mesh; from the queue lane before the seal: hidden by SI0101_WallB_Front_01; from the lane's mouth: hidden by SO0002_M05_Facade_A_Base_01...; from the escape marker: SEEN (46 m); from the boarding place: SEEN (46 m)' - L3.5 |
| L1's / L2's checks | check() on the kept build | all as L2.3: verify 1 known; 79 spawn places on the mesh; loot 11 / 2,200,000 takable; route as built crossed = the seal alone, 'office -> queue lane: FREE, 122 m', 'with the 1 standing piece out: FREE, 138 m' (the last station moved: was 133); 50 of 50 men on the mesh; staging; the beat's chain; nobody in sight; 50 actors in 21 squads; chunk table 53,873 entries, 23,683 dead; five load blocks 139 MB; written level 'problems: 0'; no collision placement off its entity (the van's five included now) |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | exit 0: 0 CRASH, 0 BROKEN, 2 DEGRADED (no bot squads; the heuristic's '5 of 21 squads named by no object') |
| kl_impact / kl_arms | `kl_impact.py <archive>`, `kl_arms.py check <archive>` -> `impact.txt`, `arms.txt` | 'problems: 0 in 1 levels'; '0 findings' |
| preflight | `python tools/kl_maps.py preflight "<kept>"` -> `preflight.txt` | exit 1: 'preflight: CRASH 1, RISK 3, NOTE 65' (CRASH = the known verify problem; RISK = ZEnvSampler x 3 twice, SoundSpline x 1): as L2 |
| the flags | `test <out> --no-ai --plan <van.json>` -> `var_noai.txt`; `... --squads-awake --police-slab --dead-men-rows --office 12 --plan ...` -> `var_a.txt` (SUPERSEDED by review round 1, see above); `... --no-police --seal-open --doors-animate --light-show --beat-anim --fan-damage --plan ...` -> `var_b.txt` | 'RESULT: PASS' three times, exit 0: no-ai 26,593 entities; (a) the ten police on the slab, 'POLICE ON THE SLAB: 2 of the police come into the world IN SIGHT' (that fall-back's cost, as L2); (b) four leaves standing, no seal, the three never-run kinds in. Archives deleted |

### L3.4 What the stage found beside laying the van

- **THE PAVEMENT'S NAVIGATION MESH LEADS OFF THE SLAB.** Its polygons run from x -3765 to 5786 and the slab is
  x -1200..1800. kl_route's model of the way an AI is given (through the middles of the polygons' shared edges) from
  the lane's street end STRAIGHT to the boarding place stays on the slab (35 samples, all with floor); from the
  escape marker (-640, -2800) to the boarding place (-637, -3100), 3 m apart, it goes **17 m west of the slab and
  back** (to x -2346; 50 of 86 samples without a floor: `route_open.txt`). The model's 'middle of the shared edge'
  is cruder than what the game's path-finder does (not read), but the polygons ARE that long, and L2's police already
  rest on 'an AI walks the mesh where there is no collision floor'. FOR THE BOTS' STAGE: the last stations are the
  lane's street end and then the boarding place, nothing between; check() fails a build in which that leg leaves the slab.
- **The whole drive lies in one room box and inside the vision grid** (`rooms.txt`): the wait place, the stop, the end
  and the camera's eye are inside `M05_A_Outside_Street_01a`'s box (x -6725..9274, y 20..3000). The road's y 30 is
  10 over that box's floor; a van at F07's own height (y -198) or 'under the map' would not be.
- **The escape marker and four police points stood where the van's rear doors now are** (L3.2).

### L3.5 GUESS / ASSUMED (each marked in the file), and what is not met

- **NOT MET, as on the bank: 'out of sight'.** The waiting van is hidden from the queue lane and from the lane's mouth
  (the house fronts), and SEEN from the pavement, 46 m up a straight street; the first criminal on the slab calls it,
  so it is seen driving in, not standing. Nothing hides a van on this street; nothing was tried.
- GUESS: the side it comes from, the stop, both lengths, `MOUTH_SIDE` 150, `BOARD_CLEAR` 500, `FED_CLEAR` 1000, the new
  places of the marker, the seven police points, the two cover points; the camera's eye (cam_spot's).
- ASSUMPTION, the stage's largest: **a key-framed van is drawn and drives where there is no collision floor** - and the
  van's own five key-framed bodies collide there with players' bullets and bodies as anywhere. Retomoto's van drove
  under its road; no van of ours has stood off every floor.
- ASSUMPTION: being inside a room's box matters for being drawn (STREET_ROOM); the van's and the camera's are.
- ASSUMPTION: the camera's eye over the drawn pavement, with no collision under it, is as good as one over a floor
  (kl_map_escape calls it 'outside the map'; its rule is there to keep an eye out of the void under a level). If the
  picture is wrong: `cam=(1500, 360, -3100)` in ROAD is an eye over the slab, ahead of the van (cam_spot's choice
  when only real floor counts: `out/plan0.txt`).
- NOT KNOWN: what the van's kill box does to a policeman who crosses its line - the west squads run to their cover
  from z -2750 / -2850 and three of their five points lie north of the line, two south (they cross it). Their men
  come into the world when the seal opens; the van comes 7.2 s after a criminal is on the slab.
- NOT KNOWN: what the passengers see of the east end - the drive ends at x 6700 beside the glow plane (z above
  -2860, 1.3 m from the van's flank).
- kl_map_escape's own (unchanged): a key-framed body moves with its entity; the engine interpolates rotation keys.
- A build made by `kl_maps.py one ... --author kl_fa_club` alone still stops in prepare_host (NO_BUILD, then NO_PLAN):
  READ, not run.

### L3.6 For the next stage

- **Build**: `python tools/kl_fa_club.py test <out> --keep [flags] [--plan "<kept>/van.json"]`; from Python
  `r, folder, plan, did = kl_fa_club.build(out)` (FOUR values now), then `finish(folder)`, `check(folder)`.
  `--plan` saves the bare graft (35 s) while ROAD is unchanged (plan_of refuses the plan of another road).
- **Whoever copies the build folder copies van.json with it**: check() holds the drive against its plan.
- **Any tool that calls kl_map_escape.van_check / check / van_plan_points on this map** (the finishing chain's bots,
  tune and talk tools read van.json and may call them) must do it inside `kl_fa_club.pavement()`, or it gets the 217
  floor faults. `kl_fa_club.van_check(folder, log, plan)` -> (report, Level, the plain tool's faults) is the ready call.
- **Bots**: the boarding place at the stop is (-636, 32, -3094) (`van.json` 'check' 'board'; the plan's (-637, 30,
  -3100)); in the FILE the box rides on the van at the waiting place (re/map_escape.md 12 / 15). Stations: ... queue
  lane, street end (105, 20, -2600) -> boarding place, NOT by the marker (L3.4). `ROUTE_OUT`'s last station is the
  marker's place (for the route test), not a bot's.
- **Anything a later stage puts on the pavement**: run check() again - `LANE_CLEAR` sees spawn points, player bodies,
  squads' men, the police's cover points, the marker and the stations of the way out; van_check's lane sees collision
  under 'Locations/' and convex bodies; `drawn_lane` sees the map's models (below 'Locations/'), not a layer's object.
- Still not wired (as the bank's L3.5): the vehicle monitor's list 4 is empty; nothing retreats when the van is called.
- **Live order** (owner away; after L2.5's): does the van show 50 m up the pavement when the slab is entered, and is
  it DRAWN all the way in (no floor under it until x -1200); 'Get in' at the rear doors at (-637, -3100); the in-van
  view, then the fixed camera from behind; the east bound 21 m into the drive away; the score page. If the van is not
  seen west of the slab, the cure is a shorter way in that starts on the slab's edge - which the tool's 20 m least
  drive does not allow from x -300 (the slab's edge is 9 m west): that would be a tool change.

### L3.7 Open

- Nothing ran in the game; no picture was rendered (drawn.py's map is a raster of the models, not a view).
- 'Out of sight' (L3.5).
- The gate is still invisible (L1.6); no dancing crowd; the upstairs squads lead nowhere (L2.6).
- What is drawn was tested for the map's static models with the 40-byte vertex; a model with another vertex form
  would be read wrong or not at all (219 entities of the band had no model root: lights, sprites, sound objects).
- The bank's regression was not re-run: no shared file was edited (kl_map_escape.py, kl_route.py, kl_fa_bank.py are
  only called; kl_fa_bank.py has another job's uncommitted changes in the tree, and every `BK.` name used here is in
  the committed version too).
- check()'s FakeTarget and room-box tests lean on kl_fa_bots / kl_fa_bots_dyn / kl_octree (another session's files; it
  prints 'NOT CHECKED' if their names change - then run the fake-test command of L3.3).

(end of Stage L3)


## Stage F - the finishing chain: wardrobe, the seven AI heisters (seal gate), gun looks, the load weight (tools/kl_fa_club.py: `bots`, `bots-check`, `strays`)

STATE: DONE (2026-10-11 ~22:00). Four folders are DELIVERED in `<work>/build/c_club/` (0.8 GB): `club` (finished, sound bank
whole), `club_wavslim` (same archive byte for byte, slim `.WAV` + `.WHD`: NEVER LOADED LIVE), `club_noai` (the same chain on the
NO_AI build), `club_bare` (L3's kept build before the chain, full shader cache). F01_Main.zip sha1: club and club_wavslim
9972c87e1389, club_noai 85afae2f3f6a, club_bare 2eb2edb526ff (= L3's, byte for byte). NOTHING RAN IN THE GAME. Every checker
passes on the finished folders EXCEPT those that only repeat the known findings (F.3). Scratch `C:/kl_scratch/club/f/`
(`s/` scripts, `out/` every output; intermediates deleted). Tools as run: the working tree with kl_chars.py and kl_fa_bank.py
carrying other sessions' uncommitted changes (kl_fa_bank.py was syntactically broken for a few minutes mid-stage by one of
them; the checks that hit it were re-run after it parsed again).

### F.1 What changed (one file, `tools/kl_fa_club.py`, +120 lines, nothing removed)
| part | what |
|---|---|
| `BOT_OPT` | kl_fa_bots has no M05_A row: `{'stops': 1, 'cases': 'glass', 'lane': True, 'window': True, 'loot_seconds': 30, 'park': ESC_AT + 80 in z}`. `park` is needed: kl_fa_bots wants the bots' AllyEscapeBox PARK_SIDE (420) beside the van's line and finds no such place on the 800-wide slab; the box stands at (-640, 219, -2720) |
| `bots_gate(B, P)`, `bots(src, dst)` | THE SEAL GATE. One loot stop (the office: the richest six cases, the bots start beside them). The way station nearest `GATE_AT` (entrance hall, (400, 100, -150); chosen (495, 122, -141)) becomes a hold of `040_Timer_seal_opens` = SEAL_AT 120 + GATE_MORE 5 - the start delay 10 - the fastest bot's straight way (9,068 / GATE_SPEED 400) = 92 s, a plain TriggerDelay2 (kl_fa_bank's two-stop form: stop 0 = office with the loot wait, stop 1 = the way to the hall + the hold, then the sprinting way out). Plan wrapped for the length of one `kl_fa_bots.build`, as kl_fa_bank.bots does |
| `bots_check(folder)`, command `bots-check` | seven squads each with ONE `040_Timer_seal_opens` of 10 s or more and not over SEAL_AT + 5, started by steps whose last place is within 600 of GATE_AT |
| command `strays <folder>` | = `kl_fa_bank.seal` (the room-list entries the squads' first new entity took; only `.buf` changes). Named `strays` because 'seal' is this level's entrance barrier |

No table of another tool got an entry. Talk: `kl_fa_talk.SCRIPTS` has no M05 key, so there is NO talk step (the club's lines are the campaign's own and the HUD texts of L1).

### F.2 The chain (`c_club/chain.sh`, 3.5 min a build) and every line changed against `c_bank/chain.sh`
`sh chain.sh "<L3 build>" <work dir> <log dir>`: 1 lighten trim,slim,fxc (cache 17.8 -> 9.1 MB) -> 2 wardrobe with the four plates ('problems: 0'; 20,989 of 23,683 dead indices taken, 2,694 free) -> 3 `kl_fa_club.py bots` ('RESULT: PASS (0 FAIL, 2 NOTE); 7 bots, 149 squad nodes') -> 4 gun looks (`--start=1 --set=1`, 6 guns, exit 1 = the known stream finding only, tested by the script) -> 6 fxc cut again -> 7 `kl_fa_bots_dyn.py build` LAST ('PASS (0 FAIL, 7 NOTE)') -> 8 `strays` (24 room-list entries moved) -> the same on the wav-slim copy ('.WAV 21.4 -> 11.4 MB').

Changed lines of chain.sh: (a) `kl_fa_bank.py bots` -> `kl_fa_club.py bots`; (b) `kl_fa_bank.py seal` -> `kl_fa_club.py strays` (twice); (c) the talk step with its `--map M03 --str ...` line and its `rm`, and the variable `$W`, are gone, the gun step's folder feeds step 6 directly; (d) step names 8_seal -> 8_strays.

Changed lines of checks.sh: `kl_fa_bank.py bots-check / reverify / check` -> `kl_fa_club.py`; `kl_map_escape.py van-check` -> `kl_fa_club.py van-check` (the plain one has 217 faults here by design, L3); the bank's three route lines and its talk line are replaced by `routes.py` (the club's 13 places: ROUTE_IN + the lane's street end -> boarding place (-637, 30, -3100); built / `--open HeroColi` / doors). The plain `kl_map_escape.py check` line stays and shows its 217 faults (every one the missing collision floor outside the slab).

### F.3 Checks on the delivered folders (`checks.txt`, `checks/` in each)
| checker | club / club_wavslim | club_noai | club_bare |
|---|---|---|---|
| kl_fa_club.check | PASS | PASS | PASS |
| reverify | problems: 0 | 0 | 0 |
| kl_impact / kl_arms | 0 / 0 | 0 / 0 | 0 / 0 |
| kl_fa.check | exit 0; ZSquadScript 28; 1 DEGRADED ('5 of 28 squads named by no object' = squads in the world from the load, L2) | exit 0, no finding, 7 squads | exit 0, same DEGRADED (5 of 21) |
| gun looks | 6 guns, problems: 0 | same | no KLGuns.ini: the checker raises, as it should |
| kl_fa_club van-check | 0 faults on the drawn pavement | same | same |
| kl_fa_bots_dyn.check | PASS (0 FAIL, 7 NOTE) | same | (no bots) |
| bots-check | 7 of 7 squads with the gate, longest 92 s: PASS | same | - |
| fake-test | PASS (grid 1, parked 1, lattice 3) -> no fake-fix | same | same |
| route as built | NOT FREE, crossed only by `HeroColi` | same | same |
| route, seal out / doors | FREE (777 samples) / 1 closure, 1 necessary | same | same |
| FFCoverList | 1 | 1 | 1 |
| kl_maps.preflight | exit 1 'CRASH 1, RISK 3, NOTE 64' (the CRASH repeats the known verify finding) | NOTE 63 | NOTE 65 |
| kl_maps.audit | 'FAIL (2 findings that must be 0, 4 known)' = the stream clips + preflight's echo; kl_snd.verify 0 (wavslim: 4,774 sounds, 4,625 waves) | 'FAIL (3 ...)': + 'no ZSquadScript: no police' (what the build is) | FAIL (2) |
| kl_chars.check | 4 'known' findings (below) | same | same |

KNOWN FINDING 1, the ONE verify finding (audit, preflight): 5 stream clips = the 12 clip names listed by check() (the club's two music sets and five ambience beds, MUSIC_CLIPS and AMBIENCE_CLIPS) are not in the installed `PC_Def.str` nor in `v_vault/PC_Def.str`: the club is silent in its music until the club's stream extension.
KNOWN FINDING 2, kl_chars.check (the audit lists them as known; they are in L1's bare graft too): glow30.fx MESH_TWEENED / MESH_RIGID asked by materials 987 (Items_Dynamic/MobilePhone_Front_01a), 1040 StripeLight_01a_Blue_M05, 1073 ObjectLight_01_White_M05, 1087 CeilingLight_01b_White_M05 (1060 on the no-AI build): the .fxc has no such effect, so those light strips and the phone are not drawn (Retomoto's BombWindow case).

Large blocks (`blocks.txt`; line 171 MB): club .prm 63.7, .fxc 9.1, .ANM 21.6, .WAV 21.4 -> five blocks 149.1 MB, chunk table 54,085 entries (line 69,632), archive 179.3 MB; wavslim 139.1 MB; noai 141.3 MB; bare 138.8 MB.

### F.4 The seven AI heisters (`bots.txt`, `dyn.txt`, `dyn_map.png`)
Plan: mesh 437 polygons, the START part 401; loot 11 objects in 4 areas, the richest the office's 6 (1.8 M); 17,200 - 18,950 of path a bot; stations: ENTERS box -> office loot -> walkway ... -> hall hold -> EXITS box (queue lane, 3 places, clearance 12..44: the narrow lane) -> level exit box (calls the van) -> the AllyEscapeBox at (-640, 219, -2720) beside the van's line (250 .. 358 from it). Dynamic step: 11 of 26 hold places found a cover box (10 'every box in reach refused', 5 none free), forks 1-2 a bot, starts +0 .. +8 s, 96 - 105 s of timers a bot (the 92 s gate included), loot seconds 15 / 30 / 45.

### F.5 GUESS / ASSUMED
- ASSUMPTION the gate rests on: nothing is known to stop an AI at the heroes-only seal (L1), so the hold is what keeps the crew from reaching the lane before the seal's clock; if the seal does stop them, the gate is harmless. A slow bot leaves the hall at about 180 s after the round-start event, the seal opens at 120 s (or earlier if both dance-floor squads die): the hold is conservative (the straight way is 55 % of the path), up to ~30 s too long for an average bot. GUESS: GATE_AT, GATE_MORE, GATE_SPEED, GATE_MIN, the park place.
- The bots start the beat's stage boxes (criminals only, fire once): the first bot through the inner office door starts the walkway's squads (L2).
- ASSUMED as in F of the bank: an AllyEscapeBox takes bots aboard in vehicle state 3 / 4 without a path test (kl2 0x907a50).
- The cut shader cache is NEVER LOADED LIVE (as the bank's); the full-cache twin is `club_bare` or the chain without its step 6.

### F.6 For the lead / the next stage
- First live order: `club_noai` -> `club` -> `club_wavslim` (the bank's order); install is the game holder's (`slot.py put <folder> F01`; the folders hold no KLJoin.ini).
- Rebuild: `python tools/kl_fa_club.py test <out> --keep [--no-ai] --plan "<c_club>/club_bare/van.json"`, then `sh <c_club>/chain.sh "<out>/F07+M05_A campaign" <work> <log>`, then `sh <c_club>/checks.sh <work>/fin <out dir>` (needs `routes.py` beside it and `C:/kl_scratch/bank/t1/s/covers.py`).
- OPEN: nothing ran in the game; only 11 of 26 hold places found cover; the bar's / ticket counter's / coat check's cases are no stop of the route (the loot tactic may take them); the gate is a clock, not the seal's event; no talk; the stream extension for the 12 clips; the bank regression (`kl_fa_bank.py check` on c_bank/bank_vault) was not re-run: kl_fa_bank.py was being edited by another session and no line of it was changed here.

(end of Stage F)

## Review round 1 - fixes after the reviewers' eleven findings (tools/kl_fa_club.py, c_club rebuilt)

Everything below was rebuilt (default, `--no-ai`) and the whole chain and every checker re-run; scratch C:/kl_scratch/club/fix_1 (deleted afterwards). Nothing ran in the game.

R.1 THE FINDINGS
- Police on mesh with no collision floor (two reviewers, 'round-broken' / 'wrong'): CONFIRMED AS A RISK, not provable offline. Fix: the DEFAULT is now the safe form, `POLICE_ON_SLAB = True`: the ten start ON the slab at its two ends (ARRIVE_SLAB). Cost, printed by check(): 2 of the 10 are in sight of the lane when the seal opens (that is also when they are put into the world, so nobody is shown a man out of nowhere before the seal). `--police-strip` = the old out-of-sight form (needs an AI to stand on bare mesh); `--police-slab` is accepted and means the default. The 7 police who come back already stood on the slab (x 900..1500). The two flags together are refused.
- Seal gate hold ignores the loot wait (four reviewers, one finding): CONFIRMED. The hold's timer starts when a bot ARRIVES, after the loot wait (up to 30 s) and a walk, so with 92 s the bots left about 130..177 s after the round-start event (clock 120). New arithmetic: hold = SEAL_AT + GATE_MORE - start - a typical loot wait (GATE_LOOT_TYPICAL 15 s, capped by the loot deadline) - straight / GATE_SPEED = 77 s (was 92). Not 'from the round-start event' (a join of "arrived" and "clock" needs a counter the recipe does not have; not attempted). bots_check now reads plan['gate'] from bots.json and computes the window in which a bot leaves: quickest (loot GATE_LOOT_MIN 5 s, 400 u/s) 115 s, slowest (loot deadline 30 s, 200 u/s) 162 s; FAIL if the quickest is before SEAL_AT - 2 GATE_MORE (110) or the slowest after SEAL_AT + GATE_MORE + GATE_LATE (170). Checked that the old 92 s would fail it (slowest 177). GATE_SLOW, GATE_LOOT_*, GATE_LATE are GUESSES. Still true: the bots leave spread over about 47 s; the early ones may stand at a standing seal (see below).
- Dependence on uncommitted edits (kl_fa_bank.py +768, kl_chars.py +8): CHECKED, no change. `git worktree` at HEAD + this kl_fa_club.py built the default archive with the SAME sha1 (a4d024f3...) as the working tree. The kl_chars diff only adds a `plates` subcommand, the wardrobe command is untouched. The chain's later steps were not re-run from HEAD.
- Nothing known to stop AI at the seal / bots' stage 2 box before it: LEFT, live check only (club_noai, then club; bot positions near the lane GO+60..120 s). Offline there is nothing to add; the hold now ends nearer the clock.
- Waiting van seen at 46 m, cover points 5.4 m from the boarding place (margin 0.4 m): LEFT. The west cover points are on the slab's rim (x -1100), the boarding place at x -637: 4.6 m in x alone, so the margin is the slab's width; moving them would mean leaving the floor. The live run with police on decides.
- Build flags not carried to bots / bots-check / check / finish: CONFIRMED, FIXED. test() writes the flags into van.json ('flags': FLAG_NAMES); load_flags() reads them back in those four commands (chain.sh needs no change: van.json travels). A folder without them is a default build.
- Contradictory flags accepted: CONFIRMED, FIXED. Refused: `--seal-open` with `--seal-plane` or `--seal S`; `--no-ai` with `--squads-awake` / `--dead-men-rows` / `--office S`; `--no-police` with `--police-strip`; `--police-slab` with `--police-strip`. A missing or malformed value after `--seal`, `--office`, `--str`, `--plan` gives a message. With `--seal-open` the gate hold is GATE_MIN (no seal to wait for).
- routes summary: CONFIRMED, FIXED. routes.py prints each RESULT line beside the exit code ('route_doors 0 | RESULT: 1 closures in 1 sets, 1 necessary'). checks.sh quotes "$S/routes.py" (the work path has spaces: the first re-run of it failed on that).

R.2 CHECKS (default build, club_wavslim has the same archive; club_noai) - all as in stage F except: bots_gate PASS 'longest 77 s; seal clock 120 s; leaving 115..162 s'; club_check PASS with 'POLICE ON THE SLAB: 2 ... IN SIGHT'; preflight CRASH 1 / audit FAIL 2 (3 on noai) = the one known stream-clip finding; chars = the known glow30.fx materials; escape 217 faults = the plain tool without the drawn pavement (van-check 0 on it); routes: built NOT FREE (HeroColi only), open FREE, doors 1 closure. New archives: club / club_wavslim a5d22942, club_bare a4d024f3, club_noai fb4ad6aa (all sha1 prefixes of F01_Main.zip). The bare folder has no guns.json (guns check fails there as before: no guns step).
R.3 NEXT: first live order unchanged (club_noai, club, club_wavslim), then one `--police-strip` build to learn whether AI stands on bare mesh.

## Review round 2 - fixes after the reviewers' nine findings (tools/kl_fa_club.py, c_club rebuilt)

Rebuilt (default, `--no-ai`), the whole chain re-run for both, and every checker re-run ON THE DELIVERED FOLDERS (club, club_wavslim, club_noai; their checks/ and checks.txt now cite the c_club paths, not scratch). The bare graft is unchanged (club_bare, a4d024f3, same sha1 from a rebuild). Scratch C:/kl_scratch/club/fix_2. Nothing ran in the game.

S.1 THE FINDINGS
- Hunters' SearchBox off the mesh: LEFT, not shown to crash. Read in kl2.exe: ZHuntBehaviourRout -> CPPScript::ZHuntBehaviourGoal, whose update (0x61f0f0) calls only 0x4d0780 and 0x60b160 after its set-up; those and their callees two levels down (0x7b3020, 0x6499b0, 0x6be1c0, 0x42a4d0, 0x455b40) hold no assert (no int3 inside a body), and stock F02 / F03 run the same rout. Not read: what the path-finder does with a point off the mesh behind 0x60b160. Watch the hunters in the first live run.
- Cut shader cache and slim .WAV never loaded: LEFT, live-only. Order of the live runs stays club_noai, club, club_wavslim; never club_wavslim first.
- Park place in the police's zone: CONFIRMED, FIXED. The bots' park (-640, -2720) was 3.6 m from the west cover point and 5 m from their men. The new `BOT_PARK` (60, 19, -2850) (on the lane's side of the van's road, 2.5 m = LANE_CLEAR from its line; the south side was tried first and made all seven squads cross the van's road and stood 0.8 m from the rim) is held by bots_check against every place of the arriving police (cover, defend, men: 28 places, nearest 10.1 m, 10 m wanted: `PARK_POLICE_CLEAR`) and every place police come back at (spawn points AFTER_DEATH / POLICE, team-mode police, bodies: 29, nearest 7.9 m, `PARK_FED_CLEAR` 7 m). 10 m from the returning ones is not possible north of the van's road: the west places end at x -950, the returning ones begin at x 850, and the road keeps z at -2850 or more. The old park fails the new rule (checked by the arithmetic: 3.6 m). Name note: the first try called the constant PARK, which clashes with the module's own PARK (the parked-object place) and broke the bound parking; bare archive hash caught it.
- Bot clocks from the same instant: CHECKED, they are. Timer_start_bots and the seal timer are both named by the same AIMonitor list 2 (the round-start event); bots_check now FAILS if no list names both and logs it otherwise. The bots' start delay of 10 s counts from that event, as SEAL_AT does; no offset of GO is needed.
- Seal fall-back clock the only guaranteed opening: LEFT, live-only (club_noai: read the log for HeroColi after 120 s; `--seal-open` ready as the fall-back).
- Returning police and a player who walks back to the office: no change needed offline (the reviewer's own verdict).
- Documentation of the old police default: CONFIRMED, FIXED. The flag table, the L2 / L3 live-order text and both var_a rows now say `--police-slab` is the default's alias and the fall-back to try is `--police-strip`; the two var_a rows are marked superseded.
- Delivered checks on scratch copies, `--str` not in van.json: CONFIRMED, FIXED. `STREAM` is a build flag now (written to van.json 'flags', read back by load_flags, which calls kl_fa_bank.use_stream; unit-tested with a made-up file). checks.sh re-run on the delivered folders: all summaries cite the c_club paths.
- Earliest bots leave before the seal's clock: CONFIRMED, FIXED. The hold is now made for the QUICKEST bot (start delay + GATE_LOOT_MIN 5 s + straight way / GATE_SPEED), `math.ceil`, with GATE_MORE 0: the quickest leaves at 121 s (clock 120), the slowest at 168 s (GATE_LATE 50 s after the clock; was 45 with a margin of 5). The hold went 77 -> 83 s. bots_check fails a quickest bot before SEAL_AT. Cost: a typical bot leaves about 10 s later than in round 1; bots_dyn prints 6 NOTEs 'N s of timers (stock bots: 16..85 s)' for the hold (86 .. 96 s), notes not failures. Still true: the bots leave spread out over 47 s because the hold's timer starts on arrival, and the early ones may meet a standing seal in the quick path.

S.2 CHECKS (delivered folders): club_check PASS x3, bots_gate PASS x3 ('leaving 121..168 s'; clocks line; park lines), reverify problems 0 x3, impact 0, bots_dyn PASS (0 FAIL, 6 NOTE), fake PASS, van 0 faults on the drawn pavement (escape 217 = the plain tool, by design), routes built NOT FREE / open FREE / doors 1 closure. Known: preflight CRASH 1 and audit FAIL 2 (3 on noai) = the stream-clip finding; chars = the glow30.fx materials; fa DEGRADED unnamed squads (heuristic). New archives (sha1 prefix of F01_Main.zip): club / club_wavslim 1380209c, club_noai bbfddbbd, club_bare a4d024f3 (unchanged). The bank regression was not re-run: no shared file was edited.
S.3 NEXT: live order unchanged (club_noai, club, club_wavslim, then one `--police-strip` build).

## Fix after runs C0-C2 (2026-10-12) - the front office, the van, round 2, the voice lines, the music file

Written by the fix workflow's builder. OFFLINE; nothing was installed, the game was not started, no file under the Dog Days
folder, KL_PortBackup, any `w_tab*` / `q_*` / `r_*` tree, `c_club`, `c_bank*` or `v_vault` was written. Files: `tools/kl_fa_club.py`
(2,597 -> about 2,800 lines), NEW `tools/kl_club_str.py`; nothing else of the repository was edited. The Vault's session was editing
`tools/kl_fa_bank.py` while this ran, so every build used a scratch copy of HEAD's `tools/` (`C:/kl_scratch/club_fix/h/tools`, HEAD
`kl_fa_bank.py` + this commit's `kl_fa_club.py` / `kl_club_str.py`, byte for byte) - `KL_TOOLS` in the re-pathed `chain.sh` / `checks.sh`.
`<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`. Labels: MEASURED = computed on the built level or
the live logs; READ = read in the logs / notes / exe notes; INFERRED = follows from those; ASSUMED / GUESS as everywhere in this file.

### X.1 The diagnosis of runs C0 - C2 (logs `<work>/build/klhook/live/C0_club_bare.log`, `C1_club_noai.log`, `C2_club_full.log`)

All three load and play with no fault. C1 (no enemies): all seven AI heisters escape with 60,000 .. 735,000 (the route, the seal's clock
and F07's van on the slab work). C2 (40 guards, then police, idle human, Risk=1 Tough=1.5, test hook without FollowOutShield):
1. FOUR heisters dead GO+33 .. 38 s (READ from the log; GO = 23:55:47.8): record 7 at the inner office door, records 4 and 3 each 'lost
   246.0 (0.0 of 252.0) ... ONE STEP' in the front office at (2137..2145, 444, 3358..3444), record 1 on the walkway. MEASURED against the
   built level: Yoko's two guards start at (2300, 361, 3200) and (2300, 361, 3300), the waiting-room pair at (2085, 354, 3178) and
   (1995, 362, 3464) - in a room 2.2 .. 3.2 m wide the crew's every line crosses; the guard at (2300, 361, 3300) is 10 .. 42 from
   every heister's line and has a clear 0x20 ray to the inner door (this file's `third_party/anp/scripts/hvk_ray.py`: 3 of the 4 old posts see
   the door, none sees a START place). INFERRED: the 246 is the point-blank rule of re/melee_damage.md (100 bullets x CopToCrew 0.05 x 1.2),
   the 85 / 88 hits are a guard in range; five bots entered the room within 3.6 s of each other (the single loot-depleted trigger).
2. TWO heisters dead in ONE tick (23:58:52.466) while ABOARD: the bots line goes 'van 3 3.0s' -> 'van 6'. READ in re/bots_behaviour.md and
   the N3 notes: state 6 = the vehicle DESTROYED (rules slot 94 grade 2), everybody aboard dies. Not read: who fired (the log has no shooter).
   MEASURED: the van carries ONE ZFakeTarget of faction 'Mercenary' (on its Body_Main; the level's only one), stood in the world from the
   load at x -5300 in sight of the west police 42 m away, and the ten arriving police stood 3 .. 5 m from its drive (the west six) and
   8 .. 30 m from its stop. The second visit of the same van (nobody aboard) was not shot - so the cause is not shown; the three layers
   below do not rely on one guess.
3. Round 2 (nobody ran one): the seal (`HeroColi`) is switched off by the clock or the counter and nothing switches it back; the owner
   reported it for the Vault ('after the first round the vault door is open'). The club has the same one-way switch. READ in
   re/fa_round.md 4, 6: a later round is not a level load.
4. The voice lines: 55 streamed single IMA ADPCM lines (police one-liners, the Japanese guards' hurt / grace / no-access lines, two coughs)
   in `club` / `club_wavslim` / `club_bare`, 1 in `club_noai` (MEASURED with kl_whd). Per re/luvsic_pass.md 1.1 Dog Days cannot read IMA
   ADPCM speech from the stream file (silent or noise); the in-memory form plays (kl_snd.merge `inmem`, kl_voice.stream_clip). The club's
   build never set `kl_snd.VOICE` (kl_maps.ready_one does for the READY maps).

### X.2 What changed in `tools/kl_fa_club.py` (flags, all ON by default; `--legacy` = the first delivery)

| flag (module name / command line) | what | where |
|---|---|---|
| `GUARDS_OFF` / `--no-guards-off` | the four front-office bodyguards (YokoGuards 2, WaitingRoom 2) stand on the upper deck of dance floor 2 west of the stairs, at (0, 364, 2050), (350, 362, 2050), (475, 363, 2275), (200, 368, 2250) (`FRONT_MEN`; `strip_squads` takes `men_table()`); nobody removed (40 guards in 17 squads) | strip |
| `POLICE_EAST` / `--no-police-east` | the ten arriving police start EAST of the van's stop (`ARRIVE_EAST`): a north row at z -2655 (the house fronts) and a south row at z -3400, x 1030 .. 1780, 150 .. 250 apart; the two west squads' cover and defend points move with them (x 1100 .. 1450) | place_police |
| `VAN_LATE` / `--no-van-late` | the van's group is HIDDEN from the load and its FakeTarget (the level's only one) is taken off; F07's own ActivateGeom 'van on' shows it `VAN_AFTER` 2 s after the seal opens (named by the seal's clock AND the beat's counter, through the timer 'van timer') and `VAN_EARLY` 1 s after the wardrobe's box (speak box, 'van timer b'). Nobody can call the van before the seal opens, so it is in the world before any call | prepare_host, wire |
| `RESET` / `--no-reset` | the round-start event (AIMonitor list 2) names, FIRST, 'reset show' (ActivateGeom: the seal again) and 'reset hide' (DeactivateGeom: the van's group again); both are no-ops in round 1 | wire |
| `VOICE` / `--no-voice` | `kl_snd.VOICE = True` around `kl_maps.one`: the streamed single ADPCM lines become records in the level's .WAV (LIP block skipped by `kl_voice.stream_clip`); cost +1.97 MB of .WAV (`club` .WAV 21.4 -> 22.6 MB, five blocks 149.1 -> 150.2 MB, under the 171 that loaded) | build |
| `LOOT_SECONDS` 18 (was 30), `SEAL_AT` 100 (was 120) | the AI heisters wait at most 18 s at the office loot and the gate hold before the lane shrinks from 83 to 63 s ('less standing still, that's a big one'). GUESS: both numbers | bots |
| `--legacy` | every flag above off, `LOOT_SECONDS` 30, `SEAL_AT` 120: the control | main |

Five F07 objects join `ROLE` while their flags are on (`ROLE_NEW`, `set_roles()`; kept by `KEEP` only then): `van on`
(Shutters/GeomActivator_TearGas_LEFT), `van timer` (RivalMercs/DisableVisionBlocker/Timer), `van timer b` (.../TimerInputAI), `reset show`
(Shutters/GeomActivator_TearGas_RIGHT), `reset hide` (.../DisableVisionBlocker/GeomDeactivator) - the same five objects The Vault uses for
its late van and reset; no entity was added. The flags travel in `van.json` ('flags'); a folder of the first delivery has none and is read
as `--legacy` (`load_flags`), so `check` / `bots-check` on an old folder judge it as built.

New rules in `check()` (`fix_check`, they FAIL what they guard; a folder built with a flag off is only reported):
- GUARDS: each of the four 'office' men at least `FRONT_CLEAR` 400 from the office doors, from every place of the way in (`way_views` of
  `ROUTE_IN`, every 100) and from every AI-heister place after the front office (bots.json), at least 250 apart; the other 36 campaign
  men near the way are COUNTED, not judged (12 of 36 within 250: the walkway's and the dance floors' guards stand on the way by the map's design).
- POLICE: no arriving man west of x 0, no two under 150 apart (the existing rules still hold: lane clear, 100 from a returning place,
  10 m from BOT_PARK, on the START's mesh part and free floor).
- VAN: group hidden at the load, 'van on' names only the van, the van's timer is named by the seal's clock and the counter (and nothing else),
  the early timer by the wardrobe's box alone, no FakeTarget (the old 'exactly one' rule now wants `0 if VAN_LATE`), no squad names the van.
- RESET: the round start's list begins with the reset objects; EVERY geometry switch of the layer (the ActivateGeom / DeactivateGeom of the ROLE
  nodes and of the kept squads' subtrees) is covered by them and by nothing else (a node that is switched and not reset FAILS); the rest is the
  list `RESET_CANNOT` (printed by check).
- VOICE: no streamed single IMA ADPCM line is left but `VOICE_KNOWN` (see X.6).

### X.3 Proofs

- Control: `python tools/kl_fa_club.py test <out> --legacy --keep --plan <c_club>/club_bare/van.json` gives `F01_Main.zip`
  sha1 `a4d024f38ba279c7e5e8584f1fd880011505bd1d` again (MEASURED; the delivered bare archive).
- `python tools/kl_fa_vaultfx.py check` on all 8 folders: PASS ('0 cloth blob(s)': the club has no cloth, so the Vault's crash cannot occur here).
- Guards, MEASURED with the 0x20 rule (hvk_ray, eye +160, on the built level): old posts - clear line to the inner door from 3 of 4, to no
  START place; new posts - clear line to NO START place and NOT to the inner door. check()'s own `Sight` also says 'nobody in sight' for the stage 'office'
  (4 men, nearest to a START place 2,177). The 4 posts: nearest door 1,437, nearest place of the way in 422, nearest AI-heister place 952 (400 wanted), 250 apart.
- Silent set `C:/kl_build/c_club2` and music set `C:/kl_build/c_club2_music`: `checks.sh` on all 8 folders. Every checker is as in D1 (the
  known three: `chars` glow30.fx, `escape` 217 = the plain tool without the drawn pavement, `guns` on club_bare = no gun looks there) except:
  the two sets' `club_check`, `reverify`, `bots-check` ('7 squads, 7 with the seal gate, longest 63 s; seal clock 100 s; leaving 101..136 s'), `vaultfx`,
  `voice` and `bots_dyn` PASS. WITH THE MUSIC FILE `preflight` is `CRASH 0` and `audit` `PASS (0 findings that must be 0, 4 known)` on `club_bare`,
  `club` and `club_wavslim` (the one finding of D1 is gone); `club_noai` keeps its 2 (= 'no police', what that build is).

### X.4 The delivered folders (checks in each folder's `checks/summary.txt`; `chain.sh` / `checks.sh` / `routes.py` / `blocks.py` beside them, KL_TOOLS-aware)

| folder | silent (`C:/kl_build/c_club2/`, against the installed stream file) | with the music (`C:/kl_build/c_club2_music/`, against `C:/kl_build/v_club/PC_Def.str`) |
|---|---|---|
| `club` | `896f493c592c2ebd7b83aa2bf8a4fd41157f2fd4` 179,258,996 | `0351dd76c6f367a60c071288a60038b2a99a4a7d` 179,259,528 |
| `club_wavslim` | the same archive; .WAV 12.5 MB (whole 22.6) | the same archive as `club` of that set |
| `club_noai` | `e7754c1f0a2330aa439c5a32a6c39be4545dfa47` 165,319,955 | `b1c31429f9b238ae5e8a0eab436a0855b11fd947` 165,320,461 |
| `club_bare` | `867a15ab50b5c3d4aa71abf5283af6fdce8b8a4c` 150,070,509 (the --crew-fix-style bare of the fix; the control is `--legacy`) | `3155984f067092f2b80bfe3993cc2eaba2401c11` 150,071,045 |

Five large blocks (blocks.py): club 150.2 MB, wavslim 140.2, noai 141.3, bare 139.9 (line 171; chunk tables 54,085 / 53,122 / 53,873).
The music set's folders carry `stream.json` (needs 1,840,263,056 bytes of the stream file).

### X.5 THE STREAM FILE `C:/kl_build/v_club/PC_Def.str` (NEW `tools/kl_club_str.py`; kl_vault_str.py was not edited)

`python tools/kl_club_str.py build <base> <out>` = `kl_vault_str.py`'s build with the club's level (`V.LEVEL = 'M05_A'`) and clip list:
7 Dead Men blocks = the two interleaved music sets (`M05_A_Club_Layers` 32,435,600 bytes, `M05_A_Club_2_Layers` 49,547,800 bytes; whole, with
the unnamed fourth layer `M05_A_Club_2_Muffled_3D`) + five ambience beds. Base = `<work>/build/v_vault/PC_Def.str` (READ ONLY, untouched).
RESULT (MEASURED, `proof` PASS): **1,841,996,798 bytes (1.715 GiB; 305,486,850 under 2 GB), sha1 `95040ec922bd9ec08836b99b0fa8213d92eaf759`**,
+88,526,853 bytes = 84.43 MB, 10,232 clips in 7,883 blocks; the data of the base (bytes 0x38 .. 0x68696900) is the same sha1
`1408dfb9...`; all 10,217 old index entries stand with the same id, name, offset, size, format, lip word, layer; all 2,086 old map entries
keep their offset; the .bain.json is carried byte for byte; account: every byte claimed. The Vault's four music folders
(`<work>/build/c_bank2_music_fx/*`) still resolve block for block (`kl_club_str.py tab`: 0 / 0 / 0 on all four) and so do the club's four; the club's
13 records name new blocks only; `kl_club_str.py levels` PASS (the 6 Dead Men levels the tab's maps are made from). `<v_club>/tab.txt`.
NEVER TRIED PAST 2 GB; this is 1.84 GB (the Vault's was 1.75). The previous files are untouched; `<work>/build/PC_Def.str` was not replaced.

INSTALL (game holder, game closed - same as re/bank_campaign.md M.3 / M.6, whose points 1, 3, 4b, 5 and 6 apply unchanged; the stream file BEFORE any music folder):
1. `python tools/kl_club_str.py installed "C:/kl_build/v_club/PC_Def.str" "<DD>"` (read only; kl_vault_str's, must end `INSTALLED: PASS` after step 2).
2. `python tools/kl_club_str.py put "C:/kl_build/v_club/PC_Def.str" "<DD>" --kept "<work>/build/v_vault/PC_Def.str"` (refuses while a kl2.exe has a thread,
   while an overlay copy is another file, when a sound bank under the game folder names a block the source lacks, with less than size + 1 GB free; copies beside, reads
   back size 1,841,996,798 and sha1 above, swaps by two renames; `--kept` only if `<DD>/PC_Def.str` IS the Vault's file, sha1 `80e53495...`). The club's file is a
   SUPERSET of the Vault's, so the Vault's folders and every tab map keep working. NEVER an overlay copy, NEVER `kl_expansion` without `--no-stream`.
3. Then the map from `C:/kl_build/c_club2_music/club_noai` first (both music sets and the beds, no guard lines), then `club`, then `club_wavslim`.
4. Back: `put` the Vault's file (`--kept` the club's); `put` refuses while a club music folder is anywhere under the game folder.

### X.6 GUESS / ASSUMED / NOT DONE (sorted by cost)

1. ASSUMED (the Vault's too): police aim at a van because of its FakeTarget; a hidden keyed vehicle runs its keys unseen and boards normally once shown. If the
   van is shot anyway, C3's `FollowOutShield=3` (hook ship_w10) is the second layer; the third (police 30 m from the van, out of its line of sight) is
   IMPOSSIBLE on a slab 8 m wide - the ten police stand 4.5 m (north row) and 3 m (south row) from the drive's line, 13 m and more east of the stop (the old west six stood in the van's path).
2. The police still come into the world IN SIGHT of the lane's mouth (the east row sees it; check counts it as the cost of the slab default) and the slab
   has no cover: 'strictly find cover' needs `--police-strip` (unproven: an AI on bare mesh) or cover objects the level does not have.
3. Not changed: the walkway's and the dance floors' guards stand on the way by the map's design (12 of 36 within 250 of a place of the way; the 'walk' squads' second
   death site, record 1 at the walkway, is theirs). The five-bots-in-3.6-s convoy is not staggered by data (the single loot-depleted trigger; kl_fa_bots_dyn's
   0 / 3 / 5 / 8 s stagger is at the START only): with the guards off the door the volley is no longer a point-blank one.
4. Holds: only the gate hold and the loot wait were shortened (X.2); the gate hold is a plain timer in the entrance hall (cover places of the dynamic step), 63 s
   for the quickest bot. The long way: `--seal-open` (no gate at all) is C5.
5. RESET cannot put back by data: the squads' in-the-world state, the floors counter and the two stage boxes, the GatePath lists, the van's key-framed
   animation, the loot (RESET_CANNOT, printed by check). ASSUMED re-armed by the rules' round start, as in the Vault; a hook would have to write the squads' flag.
6. VOICE_KNOWN: `CellPhoneChitChat_001_JapaneseMale` (a civilians' line, 663,552 bytes) stays streamed - 5 of its 648 blocks fail the ADPCM header test (step index 152 / 207 / 211 at blocks 160,
   161, ...), kl_voice.stream_clip refuses it (right: it would play noise). The club has no civilians. Everything else of the 55 is in the .WAV now.
7. The numbers FRONT_CLEAR 400, the four posts, ARRIVE_EAST, VAN_AFTER 2 / VAN_EARLY 1, LOOT_SECONDS 18, SEAL_AT 100 are GUESSES (MEASURED only against the mesh, the rays and the logs).
8. The hook was not touched: a van health line in C3's `[Bots]` log (who destroys the van) is a hook request, not done here.

### X.7 What the next live run must show (the order of D4; hook = the newest ship / test with `[Bots] FollowOutShield=3`)

C0 `club_bare` (load; the van is NOT in the picture at GO: a hidden group must not be seen from the slab or the lane), C1 `club_noai` (same as before: seven escape - NOW
also: the van appears 2 s after the seal opens (100 s after the round-start event, GO+91 s) or 1 s after a bot steps into the wardrobe's box; boards;
'vehicle state' 1 -> 3 -> 5 -> 7), C2 `club` with Escort=1: (a) no 'ONE STEP' in the first minute at (2137..2145, 444, 3358..3444); the front office EMPTY of guards at GO+2 s,
four men on the upper deck of dance floor 2 (they appear at GO+1.2 s, not in view of the START rows); (b) the van never leaves state 3 for 6; the police stand on the slab's east half;
(c) ROUND 2 IN THE SAME PROCESS: the seal stands at GO of round 2 (the first bot position in the lane before GO+91 s) and the van is away until the seal opens again. Then C3
`club_wavslim`, and the SAME order against `c_club2_music` after the stream file is installed (look for: the music at GO; 'stream' lines of the hook; the guard lines audible).


## Gates, after runs C3-C4 (2026-10-12) - the seven hold at cover in each room until its men are dead (tools/kl_fa_club.py, sets `C:/kl_build/c_club3` and `c_club3_music`)

Written by the gates workflow's builder. OFFLINE; nothing was installed, the game was not started, nothing under the Dog Days folder, KL_PortBackup, any `w_tab*` /
`q_*` tree, `c_club2*`, `v_club` or `c_bank*` was written. Files: `tools/kl_fa_club.py` (2,872 -> 3349 lines) and this note; `kl_fa_bots_rt.py`, `kl_fa_bots_dyn.py`, `kl_fa_bots.py` and
`kl_fa_bank.py` were IMPORTED and called, not edited. The Vault's session had `tools/kl_fa_bank.py` (and `kl_chars.py`) modified in the working tree, so every build used a scratch copy of
HEAD's `tools/` + this commit's `kl_fa_club.py` (`C:/kl_scratch/club_gates/h/tools`, `KL_TOOLS` in the re-pathed scripts). `<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`.
Labels: MEASURED = computed on the built level or read from the live logs; READ = read in logs / notes / the exe notes; ASSUMED / GUESS as everywhere in this file.

### G.1 What C4 showed (MEASURED, `<work>/build/klhook/live/C4_club_full.log`; GO = 01:51:34.5)

All seven AI heisters dead GO+27 .. 73 s, every one at heist stage 1 (nobody reached stage 2), 271 'lost' lines, no 'ONE STEP' (the office-door fix holds). Per bot, first hit .. last hit,
hits, where (x, z; floor in brackets):

| record | hit GO+ | hits | route of the hits | worst 5 s |
|---|---|---|---|---|
| 1 | 24.2 .. 27.1 | 18 | (1284, 3106) walkway top -> (735, 2697) the walkway's foot | 15 hits |
| 5 | 26.9 .. 34.2 | 11 | (1273, 3176) -> (798, 2671), stood there while 8 hits landed in 1 s | 8 |
| 2 | 27.3 .. 39.2 | 32 | (1111, 3138) -> (729, 2835) stood 3 s -> (470, 2217) dance floor 2 | 20 |
| 7 | 26.9 .. 51.7 | 53 | (736, 2825) -> (-904, 2418) -> (-978, 1673) dance floor 2 west / 1 north | 16 |
| 3 | 26.4 .. 60.5 | 50 | (1004, 2917) -> (-3, 3054) -> (122, 2715) -> (-441, 1713) -> (-102, 1612) | 22 |
| 6 | 27.2 .. 64.6 | 55 | (843, 2910) -> (-1152, 2805) -> (-1240, 2074) -> (179, 1411) -> (213, 1403) dance floor 1 | 35 (7 a second) |
| 4 | 26.3 .. 73.2 | 52 | (1229, 3276) -> (662, 3481) -> (-292, 1013) -> (510, 931) | 29 |

So all seven were first hit within 3 s of each other at the walkway (GO+24..27, the first men they see are the walkway's: Surprise2, FatBounceronWalkway, Dance#01's first man, all 6..12 m
from the path), and then ran the route through the 36 awake men without stopping - the last died on dance floor 1 (the south bar), nobody reached the stairs.

WHO STANDS WHERE in the built level (MEASURED, 21 squads: 17 campaign squads with 40 men + 4 arriving police squads; ZSquadScript field 3 = 1 'in the world from the load': FatBouncer,
Dancefloor02a#01/#02/#03, On_Dancefloor#02, SurpriseStairs, Entrance; staged by `tb_LEFT_TheySpotYou` = WALK_BOX (2380, 3320): Surprise2, Dance#01; by `tb_RIGHT_TheySpotYou` = FLOOR_BOX (1000, 2900):
Dance#02, Lounge#01/#02, Rave#01/#02; by the round's timer OFFICE_AT 10 s: YokoGuards, WaitingRoom (the four on the upper deck over dance floor 2's south wall, (0..475, 364, 2050..2275)); by the beat's
gate: Hunters). Not one of the 38 campaign squads' men has a rout: they STAND at their posts and fire (enemy_posts: 'start' only; the Hunters have a search box). By room, with the posts
before this stage:

| room | men | posts (x, y, z) |
|---|---|---|
| walkway (y 320..380) | 4 | Surprise2 (947, 381, 2740), (834, 381, 2866); FatBouncer (988, 382, 2916); Dance#01 #1 (623, 322, 2902) |
| dance floor 2 east | 5 | Dancefloor02a#03 (956, 42, 2643); Dancefloor02a#01 (-1099, 41, 2809), (-221, 42, 2784), (-722, 43, 3618); Dance#01 #2 (-340, 44, 2708) |
| dance floor 2 west / 1 north | 7 | the deck: YokoGuards (0, 364, 2050), (350, 362, 2050), WaitingRoom (475, 363, 2275), (200, 368, 2250); Dance#01 #3 (-1302, 26, 1868); On_Dancefloor#02 (448, 61, 1926); Dancefloor02a#02 (-1171, 40, 2012) |
| dance floor 1 | 5 | Dance#02 (-1323, 22, 1355), (-345, 22, 1089), (627, 63, 1148); On_Dancefloor#02 (23, 61, 1246); Dancefloor02a#02 (-1132, 25, 1176) |
| stair landing, wardrobe | 2 | On_Dancefloor#02 (488, 161, 582); Entrance (-106, 182, -386) |
| queue lane (beyond the seal) | 2 | Entrance (-65, 21, -1307), (134, 29, -2398) |
| overlooking (y 460 .. 866: lounge, rave bar, rave gallery, the stairs' balcony, the hunters' room) | 15 | Rave#01/#02, Lounge#01/#02, SurpriseStairs, Hunters |

WHAT THE SQUAD AS BUILT DID between the office and the first dance floor (MEASURED in the C3-delivered `c_club2/club`'s `dyn.txt`; READ in kl_fa_bots_dyn): after the 18 s loot wait it walked
2 way stations (1,840, 362, 3,339) -> (569, 40, 3,234) and on across dance floor 2 with holds of the DYNAMIC step: 0..6 per bot (4 s the point man, 6..12 s the others) at a cover box that step chose
by distance and side with NO knowledge of where the men stand; 63..84 s of timers in all (mostly the 63 s seal hold at the end); no wait on any fight and no stop that depended on the men. The
seal hold in the entrance hall, the only place the plan made on purpose, was never reached by anybody.

### G.2 What Retomoto's gates are (READ in `kl_fa_bots_rt.py`, `re/retomoto_bots_rooms.md`, its review), and how the bank's and the club's bot steps differ

Retomoto: `gates_plan` cuts the way from the table to the car into legs; each leg ends at a HOLD of seven places at cover boxes (`hold_spots`: 70..230 from a box, inside the gate's box, on a flat polygon of the
START part, 35 from a wall, in none of the trigger boxes that wake a LATER fight, 300 from every post of a man who may be alive), one step with ONE place (the pathfinder finds the way; no
way stations, no sprint), and `Street.gate_nodes` puts after every hold step a `TriggerActorsDead` cloned from stock F07's Squad#02 (`{0: the actor groups, 1: 0, 2: the next step}`). READ in kl2 (0x4afb80 / 0x8def80): it
sends its list when every named group is dead OR 0x7800 ticks = 30 s after the hold step called its place reached (within 10 m in 3D, 0x686c4c) - the clock is built in, which is why
a gate cannot leave a bot waiting for good (and why a group WITHOUT an actor has no clock: `kl_fa_bots.check` fails it). Review round: a hold must not lie in the box of a later fight (D3), a bot must not
walk past a man its gate waits for (D4), and the dynamic step must put no hold or timer between two gates (D1/D2; kl_fa_bots_dyn.last_loot_wait). The bank's step (kl_fa_bank.py) has the old shape: the seven walk
the way as stations with dyn holds and ONE seal-style hold; the club's was a copy of it (`bots_gate`: the seal hold of 63 s, `GATE_NAME`), and so had NO gate on any fight.

### G.3 What was built (flag `ROOM_GATES`, default on; `--no-gates`; `--legacy` and `--no-ai` switch it off)

1. THE PLANNER IS RETOMOTO'S, imported: `bots_gates(B, P)` calls `kl_fa_bots_rt.gates_plan` with this level's table inside `rt_for_club` (sets GATES, EN_, POST_KEEP 400 - the default of its `near_post` is bound at import, so
   that is wrapped too -, GATE_MAX, pick_holds, hold_spots, wake_map for the call and puts them back). The table `ROOMS` has five rooms in the order of the way: `walkway` (the front office's west end, box x 1350..2300 z 3000..3500, y 360),
   `floor2` (the walkway's foot, x 250..950 z 2950..3500, y 40; it crosses `tb_RIGHT_TheySpotYou`, which the stair ends in), `floor1n` (dance floor 2 west, x -1500..-500 z 2350..3000), `floor1s` (dance floor 1 north-west,
   x -1500..-600 z 1500..2000, y 20), `stairs` (dance floor 1 south, x -900..1000 z 400..1100, y 40, +-60). The seal hold of the entrance hall is the planner's last leg ('car'), the seal gate that was there
   (`040_Timer_seal_opens`, a plain timer from arrival) follows it unchanged, then exit, level-exit and park stations (`050_..._out`, sprinting as before).
2. THE MEN OF A ROOM are the men whose POST lies in it (`room_of`), named one by one (a squad spans rooms: Dance#01 stands on the walkway, dance floor 2 and dance floor 1): the TriggerActorsDead names their
   groups (4 / 5 / 7 / 5 / 2 groups, at most 9 a list). The upper floors (y >= 420: 15 men) and the lane (2 men) are waited for by NOBODY - they overlook or lie beyond the seal; the planner's `wake_map` is told that no squad is
   'known' (the club's 'load' squads are the fight, so its 'not woken by any box' notes are meaningless and not logged). The ways between the holds cross `tb_LEFT_TheySpotYou` (walkway) and `tb_RIGHT_TheySpotYou`
   (floor2, a stair ends in it): both wake squads of later rooms, as the campaign's own wiring does.
3. `pick_holds_club`: the planner's own pick packs a cover box's places along a line and gives up at the walkway's mouth, where ONE cover box has 24 places in a 4 m strip. The club's pick: seven places >= 80 apart
   (110, 100, 90, 80 asked in turn), as many different cover boxes as there are, behind the box and clearance as tie-breaks, 400 tries of a fixed seed.
4. `dyn` (new command, the chain's dynamic step): `kl_fa_bots_dyn.build` with `PERS.out_holds` False and `last_loot_wait` told the chain is cut off behind the table, for the call. WITHOUT this the step took the LAST TriggerActorsDead of the squad's last chain for 'the last
   loot wait' and put 31 .. 35 `Timer_hold` (4 .. 8 s) with covers of ITS choosing between the gates, 37 of them (first run of `rooms_check`: 37 FAILED). What it still adds behind the gates: the stagger at the start and the
   RandomTrigger forks (another corridor of the mesh between two places; a way, not a wait). `chain.sh` of the new sets calls `kl_fa_club.py dyn` in the two 7_dyn lines (the only other change).
5. MEN MOVED (`CLEAR_MEN`, 5): of the 15 men within 250 of a place the crew walks (holds, stations, the mesh path between them, every 50), the five that have a post in the SAME room, at cover (70..230 from a box), 4 m from every hold and
   station, 2.6 m from the path, on the START's mesh part: Surprise2 #2 (834, 2866) -> (634, 375, 2546); Dancefloor02a#01 #4 (-1099, 2809) -> (-1699, 40, 2569); Dancefloor02a#01 #3 (-221, 2784) -> (-21, 40, 2704);
   Dancefloor02a#02 #3 (-1171, 2012) -> (-611, 40, 2172); Dance#02 #9 (-345, 1089) -> (-905, 20, 809). The other TEN STAY (`ROOM_STAY`, printed by `rooms_check`): the walkway's four (the fight itself - the gate waits for them), Dance#01 #3
   (any post in dance floor 1's north is within 2.6 m of the way down), the stair landing's two (the landing is 3 m wide), Dance#01 #2, Dance#02 #10 and Dancefloor02a#02 #4 (the south bar: the way passes it), the queue lane's two (a 3 m corridor;
   they are the seal's other side). The other tries moved men to another room or onto the street (`C:/kl_scratch/club_gates/moves.py`): refused. GUARDS AWAKE ONLY WHEN THEIR ROOM'S GATE IS REACHED: not
   changed - the 'walk' and 'floor' squads (Surprise2, Dance#01, Dance#02, Lounge, Rave) already wake by the campaign's own Alert boxes at the walkway, and the 'load' squads have no child that could be sent a message (squad plan
   `SQUADS`: `None`), so there is nothing to wire a gate to; making them sleep would need new nodes (a SquadModifierBehaviour per squad) - not done.
6. TIMETABLE (`gates_timetable`, from the plan; GUESS: the speeds 400 / 200 units a second, 12 s a room for the quickest crew): the seal hold is made for the QUICKEST crew (every room won in 12 s) so that it leaves no sooner than the seal's clock
   (SEAL_AT 100 s): hold = max(10, ceil(100 - 10 - 5 - 7,283/400 - 5 x 12)) = 10 s (the minimum); the quickest crew leaves it at 103 s.

### G.4 The worst-case timetable (after the round-start event; GO is about 8.5 s later; every clock is the 30 s of the game's own TriggerActorsDead)

A crew that wins nothing: bots start +10 s (the stagger adds 0..8), loot wait <= 18 s -> 28; walk to the walkway hold 2,221 / 200 = 11 s -> 39 s there, the gate runs out -> 69; floor2: 2,686 -> 13 s, 82 -> 112; floor1n: 1,759 -> 9 s, 121 -> 151;
floor1s: 1,504 -> 8 s, 159 -> 189; stairs: 2,800 -> 14 s, 203 -> 233; the seal hold at about 241 s (+ the 10 s hold timer, the seal opened at 100 s long ago) leaves at 251; the walk out
3,659 x 1.3 / 200 = about 19 s -> the exit trigger (the van is called there) at 270 s of the round's 360: 90 s of margin for the van (7.2 s in, 8 s waiting, `ROOM_VAN_MARGIN` 75). `rooms_check` FAILS a build
whose worst case is later than 285 s or whose quickest crew would leave the seal hold before the clock. The quickest crew (every room won at once): at the walkway hold 28 + 11, ... seal hold about 93 s, leaves 103 s. The seal opens at 100 s by
its clock or earlier by the beat (both dance-floor squads dead: the floor2 / floor1 gates name those men too, so a crew that wins them opens the seal and the gates together).

### G.5 The checks (`rooms_check`, run by `bots-check`, so by `checks.sh` on every folder)

FAILS: a squad without a gate's TriggerActorsDead / one that names other groups than the plan / a group that does not exist or has no actor (no 30 s clock) / a man named by two gates (the second would wait for a man who is dead) /
TAD field 1 not 0 / more than 9 groups; the seven holds of a room not seven places 80 apart, a hold 60..240 from NO cover box, a hold equal to an earlier gate's; a hold or the loot place within 400 of a post of a man who may be alive (not named by an
EARLIER gate) on its floor; any TriggerDelay2 / loot wait between the first gate and the seal hold (a RandomTrigger fork is a way and passes); the quickest crew leaving the seal hold before the clock; a held-in-every-room crew at the exit trigger later than 285 s; a CLEAR_MEN man
not at his post. REPORTED per room: the men in the 0x20 line of sight of a hold (`Sight`: eye 160 to head or chest on the level's collision), the men of other rooms on that floor within 25 m that see a hold, the pairs hold / earlier-room man under 4 m (only if that gate ran out).
RESULT on the finished sets (`checks.sh` on all 8 folders, `summary.txt` in each): `rooms_check` / `bots-check` PASS on `club` and `club_wavslim` of both sets (5 rooms; seal hold 10 s, the quickest crew leaves it at 103 s; worst case at the exit trigger 270 s,
90 s of margin); `club_noai` and `club_bare` have no gates (`--no-ai` switches ROOM_GATES off; `club_bare` has no squad of AI heisters) - `club_noai` is byte for byte the c_club2 one (sha1 `e7754c1f...` / music `b1c31429...`).
Per room (`bots_gate.txt`): walkway 4 men, 2 in the 0x20 line of sight of a hold; floor2 5 of 5; floor1n 7, 4; floor1s 5, 4; stairs 2, 1. Every other checker as in c_club2: the known three (`chars` glow30.fx, `escape` 217 = the plain tool
without the drawn pavement, `guns` on `club_bare`), `preflight` / `audit` with their one known finding on the silent set and CRASH 0 / PASS on the music set (`club_noai` keeps its 2-3 = 'no police'); `club_check` (which carries
the existing GUARDS / VAN / RESET / voice rules and the Sight rules for the five moved men), `reverify`, `impact`, `vaultfx`, `van`, `fake`, `routes`, `voice`, `stream_whd` PASS. `bots_dyn` PASS with 6 NOTEs ('10 .. 15 s of timers (stock bots: 16 .. 85 s)')
- the dynamic step's holds are gone behind the loot, on purpose. The first run of `rooms_check` on a build WITHOUT the `dyn` command FAILED 37 times (the step's `Timer_hold`s between the gates): that rule is what found the need for it.

### G.6 GUESS / ASSUMED / NOT DONE

1. ASSUMED (Retomoto's, live there): a TriggerActorsDead in an 'in'-leg chain behaves as in the 'out' chain it was proven in; a gate arms when the hold step has called its place reached (within 10 m in 3D) - so a bot that never comes within 10 m of its hold has no clock.
2. The men who stand on the upper floors (15) overlook dance floor 1 and shoot down; nobody waits for them and the crew cannot reach them. Lounge#01's three stand 4.4 m over dance floor 1's east end and the south bar: expect hits from above in the `floor1s` and `stairs` rooms.
3. The walkway's hold does not see all of its men (the walkway's four, 2 in a straight line): the gate may run its 30 s; that is the cost of a hold 4 m from every post.
4. GUESS: every box and direction of ROOMS, ROOM_G_MIN 12, the speeds 400 / 200, CLEAR_MEN's posts, ROOM_POST_CLEAR 400. MEASURED: the holds (printed per room by the planner, kept in `bots.json` 'club_gates').
5. NOT OPTIMISED: 'out of the room's sight where the mesh allows'. The holds are chosen by cover, trigger boxes and posts, not by what sees them: `rooms_check` reports 2 / 1 / 7 / 6 / 7 men of other rooms on the same floor within 25 m that see a hold of
   walkway / floor2 / floor1n / floor1s / stairs (floor1n and stairs: the deck over the south wall and the south bar look into them). A view score in `pick_holds_club` is the next step if C5 shows bots dying at a hold.
6. NOT DONE: the 'hold' at the lane (two men beyond the seal stay as the campaign has them); sleeping squads that a gate wakes; the fed.

### G.7 What the next live run must show (hook = the newest ship / test; `[Bots] Log=2` MoveLog=1; settings of C4: FollowOut=1 FollowOutShield=3)

Per gate the time it OPENED and WHY: a bot's `MoveLog` position stops within 10 m of the room's hold place (listed in `bots.json` 'club_gates'; `show.py` prints them) and starts again - by the men's death (the 'lost'/'dead' lines of the men do not exist
in the log, so read it from the bot: the first movement after the stop is earlier than arrival + 30 s) or exactly arrival + 30 s +- 1 s (the clock). Nobody dead before which second: the idle-human C4 setting should give the first death after GO+60 s
(Retomoto's was GO+175 s, but its crew came to the first gate at GO+60); a death in the walkway room before its gate has opened = the hold is in the line of fire (look at the 'lost' positions against the hold places); every bot at the seal hold by GO+240 s and the van called by GO+270 s
(the worst case above, from the round-start event). ONE JOINED RUN is not needed (the club has no join). If the bots stand 30 s at the walkway and then die in dance floor 2: the rooms' men are not seen from the holds (see 'in the 0x20 line of sight' above) - move the holds nearer
(ROOM_POST_CLEAR 300).

### G.8 The delivered folders (checks in each folder's `checks/summary.txt`; `chain.sh` / `checks.sh` / `routes.py` / `blocks.py` beside them; KL_TOOLS-aware; `chain.sh` differs from c_club2's in the two 7_dyn lines only)

| folder | silent (`C:/kl_build/c_club3/`, against the installed stream file) | with the music (`C:/kl_build/c_club3_music/`, against `C:/kl_build/v_club/PC_Def.str`) |
|---|---|---|
| `club` | `09da62c45f905b1e983ffb566431ac622b7d1f1a` 179,257,632 | `3f13a27e21a4044b17dbba0c763a5444fe567e27` |
| `club_wavslim` | the same archive as `club`, slim .WAV | the same archive as `club` of that set |
| `club_noai` | `e7754c1f0a2330aa439c5a32a6c39be4545dfa47` 165,319,955 (= c_club2's) | `b1c31429f9b238ae5e8a0eab436a0855b11fd947` (= c_club2_music's) |
| `club_bare` | `b1e90c8dce0eb189ff2741f17b9d2f854f24c58a` 150,071,963 (the five men moved; the control is `--legacy`) | `366d0f1f7ed0cf7a173fc19d45b94bea76983162` |

`python tools/kl_fa_club.py test <out> --legacy --keep --plan <c_club2>/club_bare/van.json` gives `a4d024f38ba279c7e5e8584f1fd880011505bd1d` again (MEASURED, with this commit's file). `test --no-ai` builds and passes ('RESULT: PASS', 26,598 entities).
`python tools/kl_fa_vaultfx.py check` PASS on all 8 folders. Rebuild: `test <out> --keep [--str FILE] --plan <c_club2>/club_bare/van.json`, `sh <c_club3>/chain.sh`, `sh <c_club3>/checks.sh` (`STREAM_FILE` set for the music set); the music set's stream
file is the one of X.5 (nothing changed there). The Vault's session was editing `tools/kl_fa_bank.py`: the builds ran on a scratch copy of HEAD's `tools/` + this `kl_fa_club.py`.


## Gates, second fix (2026-10-12) - after the skeptic's four faults (tools/kl_fa_club.py; sets `C:/kl_build/c_club3` and `c_club3_music` REBUILT in place)

OFFLINE; nothing in the game, nothing under the Dog Days folder, KL_PortBackup, other trees, `c_club2*`, `v_club`, `c_bank*`. Builds ran on the scratch copy of HEAD's `tools/` + this `kl_fa_club.py`
(`C:/kl_scratch/club_gates/h/tools`; the Vault's session had `kl_fa_bank.py` / `kl_chars.py` modified in the working tree). Only `tools/kl_fa_club.py` and this note were edited. Labels as above.

### H.1 The four faults, reproduced (MEASURED on the first c_club3/club with `skeptic/ways.py`, `holds.py` and a new search)

1. FORKS (wrong): CONFIRMED. The dynamic step's RandomTrigger forks inside the gated legs put way places (`way_b` / `way_c`) on the deck 34 .. 145 from YokoGuards / WaitingRoom guards that no gate had
   named yet (the floor2 leg, via `031_RandomTrigger_way`), and 244 .. 246 from Dancefloor02a#02 Guard#03. `rooms_check` let a RandomTrigger pass ("a way, not a wait"). FIXED (H.2 a).
2. HOLDS NEXT TO SURVIVORS (wrong): CONFIRMED. The seven floor1s holds were 75 / 120 / 124 / 154 / 160 / 165 / 175 from Dance#01 Guard#10 (-1302, 26, 1868), a floor1n man; four stairs holds 145 .. 284 from
   Dance#02 Guard#10 (627, 63, 1148) and one 266 from Guard#09 (-905, 20, 809). The planner calls a squad an earlier gate waited for dead, but a squad spans rooms here and a gate runs out its 30 s with its men
   alive; the check assumed the same. FIXED (H.2 b, c).
3. GATES THAT WAIT FOR MEN NO HOLD CAN SEE (minor): CONFIRMED (the builder said so). FIXED as far as data goes (H.2 d).
4. THE TIMETABLE IS A MODEL (minor): CONFIRMED, the arithmetic is right (re-derived: bots start 10, loot 28, 5 x 30 s of gates, hold 10 s) but a bot that fights or never comes within 10 m of its hold has no bound.
   NOT CHANGED in the build: a level-wide timer behind the gates would be a timer between two gates (what rooms_check forbids and Retomoto's review asked for). C5 must log arrival / leave per bot (H.5).

### H.2 What changed in `tools/kl_fa_club.py`

a. `dyn()` now wraps `kl_fa_bots_dyn.Routes.forks` for the call: every fork mark in a leg after the table's loot wait and before the final leg (a leg = the Defend steps between two kept elements:
   the gates' TriggerActorsDead, the seal timer) is removed. The exit leg after the seal timer keeps its forks (as in c_club2). `rooms_check` now FAILS any RandomTrigger between the first gate and the seal hold
   and any place of any step there within `ROOM_STEP_CLEAR` (200) of a man on its floor. Result on the rebuilt `club`: no fork there, the holds are the only places.
b. `rt_for_club(gates, men)`: the hold finder's spots are filtered by `ROOM_AFTER_CLEAR` (300): no hold within 300 of a man whose post lies in an EARLIER room (`room_of`), whatever gate named him. The planner's
   own 400 from the men who may be alive stays. (A first try with every post of every squad as 'alive' at 400 left floor1s with no spot at all: 59 places, all within 250 of Dance#01 Guard#10, who stands in the
   way down; the planner's ways to the other places were refused because it takes a squad's start post for a man the gate waits for.)
c. `CLEAR_MEN` 5 -> 6 men: Dance#01 Guard#10 -> (-342, 40, 2148) (found by a nav-mesh search: floor1n, 70..230 from a cover box, 400 from every hold and station, 260 from the route, 250 from every other man)
   and Dance#02 Guard#09 -> (-1585, 21, 1129) (was (-905, 20, 809); without this move the stairs have 15 hold places and fail). Dance#02 Guard#10 (627, 63, 1148) stays: no post exists for him, and the stairs
   holds now lie at x -890 .. -325, z 645 .. 1070, 815+ from him. `rooms_check` fails a hold within 400 of any man (own and later rooms) or within 300 of a man of an earlier room. The closest earlier-room
   man is 301 from a stairs hold ((-850, 20, 1070) and Dancefloor02a#02 Guard#04). `ROOM_STAY` has 7 lines now.
d. `ROOM_NAME_SEEN` (default on): the room's TriggerActorsDead names only the men the 0x20 line of sight (`Sight`: eye 160 to head or chest) reaches from at least one of the seven holds; when no man of the
   room is seen all are named (the clock is then the gate). Named / of the room: walkway 2 / 4, floor2 5 / 5, floor1n 4 / 7, floor1s 4 / 5, stairs 2 / 2 (neither stairs man is seen: the landing men are at
   y 161 / 182, the holds at y 20). The unnamed men stay alive in `rooms_check`'s clearance rules. `bots.json` 'club_gates' carries `room_men` and `unnamed`. GUESS: that opening on the seen men is better
   than waiting 30 s for men nobody shoots; with the unseen men alive the crew meets them on the way, as before.

### H.3 The rebuilt timetable and checks (MEASURED, `bots_gate.txt`)

Worst case (every gate runs 30 s): the seal hold at 234 s, left at 244 s, at the exit trigger 262 s of the round's 360 (97 s of margin; the first build said 270). The quickest crew leaves the seal hold at 103 s
(clock 100). Per room (men named / of the room, named men in sight, other-room men on the floor within 25 m that see a hold): walkway 2/4, 2, 2; floor2 5/5, 5, 2; floor1n 4/7, 4, 8; floor1s 4/5, 4, 5; stairs 2/2, 0, 5.
`rooms_check` / `bots-check` PASS; `bots_dyn` PASS (6 NOTE as before); `club_check` PASS; `skeptic/ways.py` on the new `club`: the only places under 400 from a living man are the EXIT leg's (050, after the seal:
196 .. 245 from Entrance Guard#03 in the queue lane, as in c_club2, by the design in ROOM_STAY); none in a gated leg. All other checkers as in c_club3 (known: `chars` glow30.fx, `escape` 217, `guns` on the
bare folder, `preflight` / `audit` on the silent set; `club_noai` unchanged byte for byte). `python tools/kl_fa_vaultfx.py check` PASS on all 8 folders. `test --legacy` still gives `a4d024f38ba279c7e5e8584f1fd880011505bd1d`.

### H.4 Delivered folders

| folder | silent (`C:/kl_build/c_club3/`) | music (`C:/kl_build/c_club3_music/`) |
|---|---|---|
| `club` | `e727a2f0011158b4851f1818c241dac5a0d92887` 179,251,508 | `fce0cb54862aa23c7c8d2b7bd22ff7fedb90b958` |
| `club_wavslim` | the same archive | the same archive |
| `club_noai` | `e7754c1f0a2330aa439c5a32a6c39be4545dfa47` (= c_club2, unchanged) | `b1c31429f9b238ae5e8a0eab436a0855b11fd947` (unchanged) |
| `club_bare` | `b82d9a3444ee18367fed260d9c5c46fdda6249d9` | `a95cd6175233ecf730b85991a559b20c0fa055bd` |

### H.5 What C5 must show, and what is still open

Per bot: arrival at each hold (within 10 m) and the leave time, so the 30 s clock and the men's deaths can be told apart; a death before GO+60 s is a hold in somebody's line of fire. OPEN: the 15 upper-floor men and
the two lane men are waited for by nobody; Dance#02 Guard#10 and Dancefloor02a#02 Guard#04 (the south bar) are only 301 .. 400 from the stairs holds; the stairs gate will probably run its 30 s (its two men cannot
be hit from y 20); no bound on a bot that fights on or never reaches its hold (it has no clock); the two moved men's new posts are GUESSES checked on the mesh and for cover only.


## Pressure, after run C5 (2026-10-12) - how many guns the seven can stand under (tools/kl_fa_club.py; sets `C:/kl_build/c_club4` and `c_club4_music`)

OFFLINE. The game was not started; nothing under the Dog Days folder, KL_PortTools, another session's trees, `c_club3*`, `c_club2*`, `v_club` or `c_bank*` was written; intermediates in
`C:/kl_scratch/club_pressure/` (the analysis scripts are in the session's scratchpad: `lib.py`, `press.py`, `reloc3.py`). Only `tools/kl_fa_club.py` and this note were edited. Labels: MEASURED = computed on
the built level (`C:/kl_build/c_club3/club`) or read from the live log `<work>/build/klhook/live/C5_club_gates.log`; READ = from the notes / code; GUESS / ASSUMED as everywhere.
Line of sight everywhere below = third_party/anp/scripts/hvk_ray.py, a part of the level's collision blocks when flags & 0x20 (eye 160 over the post, target 120 and 175 over the floor), a gun
bears within 60 m (GUN_RANGE; kl_fa_bank.PRESSURE_RANGE's GUESS) and from the same floor (12 m).

### P.1 C5 against the level (MEASURED; GO = 03:43:04.5; the log has NO 'move:' lines: `MoveLog=1` is in the ini's first [Bots] section and no line came - the hook of the run, test_w10, or the doubled [Bots] section; places below are the 'lost' lines')

| bot | first .. last hit | hits | hits a second | stood at (x, y, z) when hit | guns with a clear ray to that place (distance m, squad, weapon) |
|---|---|---|---|---|---|
| 5 | GO+22.9 .. 25.9 | 19 | 6.4 | (1519, 360, 3344), the whole time | 5: FatBouncer 7 pistol; Dance#01 #01 10 SMG; Surprise2 #02 12 pistol; WaitingRoom #02 17 pistol; YokoGuards #01 20 SMG |
| 6 | 28.8 .. 34.7 | 18 | 3.0 | (1539, 350, 3425) -> (1535, 350, 3430) | 8: FatBouncer 8; Surprise2 #01 9 rifle; Dance#01 #01 11; Surprise2 #02 13; WaitingRoom #01 16, #02 18; YokoGuards #02 18, #01 21 |
| 2 | 30.0 .. 41.2 | 40 | 3.6 | (1521, 360, 3317), the whole time (bot 4 on the same spot) | 1: Dance#01 #01 10 SMG (the rest in the lines of sight of the next spot only) |
| 4 | 30.6 .. 112.3 | 66 | 0.8 | (1521, 363, 3317) until GO+41, then on the way across floor 2 to (-582, 40, 2813) | at the end 9: Dance#01 #08 3, Dancefloor02a#03 6, Dance#01 #10 7, ... |
| 1 | 34.8 .. 40.7 | 21 | 3.6 | walking: (1112, 379, 3054) -> (676, 379, 2568) | at the first hit 10: FatBouncer 2, Surprise2 4 and 7, Dance#01 #01 5, WaitingRoom 10 and 12, YokoGuards 13 and 15, Dancefloor02a#02 19, #04 29 |
| 7 | 43.0 .. 56.2 | 36 | 2.7 | (1532, 351, 3341) -> (1336, 379, 3283) | 5 .. 8, as bot 5 |
| 3 | 52.8 .. 63.6 | 19 | 1.8 | walking: (1237, 376, 3229) -> (933, 379, 2679) | 9 .. 10: the same eight of the walkway and the deck, one man of floor 2 at 20 m |

Damage a hit 3 .. 29 (mean 6 .. 14): rifle / SMG / pistol bullets, nothing but bullets (no 'ONE STEP', the point-blank rule of re/melee_damage.md did not fire). Four of the seven stood still on
the walkway gate's west end for 3 .. 11 s each and were shot dead there: they were at 5 .. 8 guns at once (3 .. 6 hits a second = 252 health gone in 4 .. 11 s at the 0.05 dial).
THE HEIGHT QUESTION: the hits are at y 350 .. 379 = the planned floor (the gate's holds are at y 362). The y of 446 .. 475 that the task read is only the 'dead' line (`lost 1.0 (0.0 of 252.0) ... - DOWN`,
e.g. bot 5 (1522, 452, 3346)): the position of the body when it goes down, 90 above the feet; they did not stand elsewhere than planned.
WHERE THE FIRST GATE'S SEVEN WERE PLANNED: holds (1708, 3111) (1628, 3191) (1628, 3111) (1668, 3311) (1508, 3351) (1588, 3351) (1708, 3191), y 362: the four east ones have NO gun on them by the exact ray,
the three west ones 8 / 1 / 5 (MEASURED, `hold-guns` below). The bots that died stood at the two west places and at (1521, 3317), 13 .. 19 m west of the others: they did not stand where the plan
put them (cause not established without the move lines; GUESS: the game's own cover search sends a bot that is shot to the nearest cover point, and the cover box of that room, CoverBoxH_01 at
(1508, 360, 3151), is the only one in the front office).

### P.2 Guns bearing, gate by gate, on the build C5 ran (c_club3/club; `python tools/kl_fa_club.py hold-guns C:/kl_build/c_club3/club`; the wake table is READ OFF THE SCENE and puts every squad a box or
a timer starts at gate 0, so it is an upper bound for the 'walk' / 'floor' squads)

| gate | guns on the 7 holds | worst on the walk to them (every 3 m of each bot's mesh path) | who |
|---|---|---|---|
| walkway | 0 0 0 0 8 1 0 | 5 at (1548, 362, 3360) | FatBouncer, Surprise2 x2, Dance#01 #01, WaitingRoom x2, YokoGuards |
| floor2 | 5 4 9 9 9 8 2 | 10 at (1043, 372, 3053) | + Dance#01 #08 #10, Dancefloor02a#01 x3 |
| floor1n | 11 10 9 11 13 10 11 | 14 at (-847, 40, 3068) | + Dance#02 #01 #09 |
| floor1s | 6 7 8 10 12 7 6 | 16 at (-1265, 40, 2417) | |
| stairs | 4 4 4 4 4 5 5 | 10 at (-1465, 21, 1890) | |

### P.3 The yardstick: what a crew survives at this dial (MEASURED with the same code on the tab's Withdrawal build `z_cover3/M03` = the bank of the tab (w_tab* DM03 is the same plan plus the HUD / car steps), and on Retomoto's gates)

THE NUMBER: **a seven-bot crew stands at most 2 guns (3 counting every place a rout of a man goes by) on a station of the heist and 3 (4) on a stretch between two, with a clear ray inside 60 m** -
that is Withdrawal, on which the seven escape (series I, C3_DM03: 'nobody dies, all seven escape') at the same Risk=2 / CopToCrew 0.05. Taken over its 16 stations and 251 samples every 2 m of the mesh path
(the first bot's way; the 9 arriving police of the exit leg are left out: they are not in the world until the escape is called): stations 0 .. 2 guns (rout places: 0 .. 3), stretches 1 .. 3 (1 .. 4);
with the arriving police on the way out 4 .. 7. The bank has SIX men of its own (BankMainSquad_01..03, LoadingDockSquad_01) and all of its squads are started by boxes the crew trips, none stands awake
from the load; the club has 40, 21 of which can see the route. Caps used here: **HOLD_GUNS = 3, LEG_GUNS = 4** (the upper numbers, because the club's men do not move and a rout place counts the same as a
post).
Retomoto's gates (z_rooms/retomoto_full, where the crew goes down a tower in 5 minutes, one death a minute in G1): 2 .. 6 guns on a hold, 4 .. 15 on the walks - not a yardstick for survival.

### P.4 What changed in `tools/kl_fa_club.py` (flag `PRESSURE`, default ON; `--no-pressure`; off with `--no-gates`, `--legacy`, `--no-ai`; the flag travels in van.json; `club_noai` is byte for byte c_club3's: sha1 `e7754c1f...`)

1. THE MEASURE (`Fire`, `gun_table`, command `hold-guns <folder>...`): the exact ray of hvk_ray (a part blocks when flags & 0x20; eye 160, target 120 and 175), GUN_RANGE 60 m, GUN_FLOOR 12 m, for the men of the squads that are
   awake at a gate; the wake table is READ OFF THE SCENE (`scene_wake`: field 3 = 1 or a box / timer = gate 0, named by the TriggerActorsDead of gate k = awake at gate k + 1, 99 = nothing wakes it).
   The table counts every awake man alive (the yardstick's measure) and, beside it, with the men that earlier gates name dead.
2. STAGING (`WAKE_AT`, `squads_now`, `club_street`, command `wake`): nine squads (YokoGuards, WaitingRoom, Dance#02, Lounge#01/#02, Rave#01/#02, SurpriseStairs, Entrance = 21 men) are stage 'gate': ZSquadScript field 3 = 0 and their
   SquadModifierBehaviour (field 4 eAM_Activate, as the 'walk' / 'floor' stages) named by the TriggerActorsDead of the gate BEFORE the room they are awake at (all seven bot squads' copies). Dance#02 at floor1s (3), the deck's four
   and the upper floors' squads at the stairs (4). The 15 men of the squads without a modifier child (Dancefloor02a#01/#02/#03, On_Dancefloor#02: 9 men) cannot be staged - a new node under an existing squad is a graft change nobody
   here has made - and stay awake from the load, like FatBouncer (a 3-modifier squad of his own wiring) and the 'walk' squads (Surprise2, Dance#01). THE DYNAMIC STEP DROPS THE NAMES (it rewrites a gate's next list to the one step that
   follows), so a chain step `wake` (c_club4/chain.sh `7_wake`, `7_wake_wav`) puts them back; only the .prp changes. kl_fa_bots_dyn.check faults any extra target of a chain element ('also starts ...'): `c_club4/dyncheck.py` runs the
   same check and lets through exactly the (gate, child) pairs of the plan, nothing else (checks.sh calls it in place of the plain command).
3. HOLDS BY FIRE (`rt_for_club.spots`, `pick_holds_club`): each place of a room scored by the guns that bear on it at that gate (+3 for each man woken when THIS gate opens that sees it: he would plop out in view); the seven are picked for
   the fewest guns first (then the old order: different cover boxes, behind the box, clearance). Where fewer than seven places stay under HOLD_GUNS the seven of the room before are offered as places of this one (floor2: three bots stay
   at the walkway's holds, which have 0 guns: 'one room back'; rooms_check lets a repeated hold through only then). A man who sleeps until a later room belongs to THAT room's gate (`room_men`).
4. MEN MOVED (`PRESSURE_MEN`, 13 men; found by the scratch optimiser `reloc4.py`, proved by the checks): Dance#01 #08 (-339, 2708) -> (1160, 3008), #10 (-342, 2148) -> (1008, 2148); Dance#02 #01 -> (-423, 1355), #09 -> (-535, 1429);
   On_Dancefloor#02 #01 -> (38, 204, 432), #07 -> (1223, 5, 796), #08 -> (1048, 2226); Dancefloor02a#03 #02 -> (1256, 3393), #01 #04 -> (-349, 2569), #03 -> (579, 2554), #02 -> (28, 3768), #02 #03 -> (889, 2172); FatBouncer -> (1138, 363, 3066).
   Each stays in his own room (room_of), on the START's mesh part, within 90 of his floor, 250 from every other man, 400 from every hold, 18 m of his old post at most. The front office's four were NOT moved (their placement is held by the FRONT_*
   rules: 400 from the way in, 250 apart; the optimiser's choice for two of them broke both: 397 and 77) - they sleep instead.
5. THE NEW CHECK (`pressure_check` inside `rooms_check`, so inside `bots-check` and `checks.sh`): (1) the wake table of the scene equals WAKE_AT, no waiting squad (hunters excepted) that nothing wakes; (2) hold-guns: at most HOLD_GUNS 3 men on a
   hold and LEG_GUNS 4 on any stretch (every 3 m of each bot's mesh path from its place before) - above them the check FAILS unless the gate is in `PRESSURE_KNOWN` (the delivered build's own ceilings, see P.6: a regression guard, NOT a pass);
   (3) appear: nobody woken when gate k-1 opens stands in the exact-ray sight of that gate's seven holds. `club_check` takes the 'gate' stage (no Sight rule for it: appear is its rule). The chain's and the checks' scripts are c_club4's (chain.sh +2 lines, checks.sh 2 lines, dyncheck.py new).

### P.5 The table: guns bearing on the seven holds / on the walk to them (MEASURED, `hold-guns`; worst of the 7 holds / worst of the ~20-45 samples; in brackets: the men that earlier gates name taken dead)

| gate | C5's build (c_club3, upper bound) | THIS build (c_club4/club) | awake men | caps | rooms_check |
|---|---|---|---|---|---|
| walkway | 8 / 5 | **0 / 0** (all seven holds, all 23 samples) | 15 of 40 | 3 / 4 | PASS |
| floor2 | 9 / 10 | 5 (4) / 7 (5): holds 0 0 4 5 5 0 3 (three of them the walkway's) | 15 | 3 / 4 | KNOWN over |
| floor1n | 13 / 14 | 5 (3) / 8 (3): holds 3 5 4 4 4 5 2 | 15 | 3 / 4 | KNOWN over |
| floor1s | 12 / 16 | 5 (5) / 10 (5): holds 3 3 4 5 4 3 5 | 18 | 3 / 4 | KNOWN over |
| stairs | 5 / 10 | 3 (1) / 5 (1): holds 3 3 2 3 2 3 3 | 37 | 3 / 4 | holds PASS, walk KNOWN over |

THE FIRST GATE, where C5 lost the crew, has NO gun on any of its seven holds (21 of the room's 24 places had 3 or fewer; the picks have none) and none on the walk: the deck's four sleep (they were up to 4 of the 8 guns at the west holds) and the holds are the east ones. Worst case timetable after the round-start event
(rooms_check): the quickest crew leaves the seal hold at 103 s (clock 100 s); a crew that wins no room is at the exit trigger at 277 s of 360 (83 s of margin; 262 s before: the 'one room back' holds are further from the next ones).

### P.6 Why the yardstick (HOLD_GUNS 3, LEG_GUNS 4) is NOT met in four of the five rooms - the experiments (MEASURED with `reloc2/3/4/5.py`, the optimiser moves one man at a time by the exact ray, the objective = guns over the caps summed over every sample)

| run | what was allowed | result |
|---|---|---|
| reloc2 (holds of c_club3 fixed, caps 2 / 4) | any man within 13 m, his room, stage table of the fix | 17 moves, still holds 5 / 5 / 6 / 3 and walks 6 / 6 / 9 / 6 over the caps (floor2 .. stairs) |
| reloc3 (caps 3 / 4, holds re-picked each round) | any man within 22 m, ANY room | caps MET (E = 1) - by sending 7 men out of their rooms: four into the entrance hall (one on the seal hold's place), one into the front office 6 .. 9 m from the START rows, two across the club. REFUSED: that is removing the fight, not tuning it |
| reloc4 (used) | his room, 18 m, not in the front office / entrance | 15 moves, E 727 -> 231: holds 5 .. 7, walks 7 .. 10 over the caps |
| reloc5 | as reloc4 AND the four squads without a modifier staged too | E 265 at the second round (reloc4: 297): no better. Staging the nine unstageable men would not close the gap |

The cause is the club's geometry: 23 men stand in four open halls (the dance floors, 8 .. 40 m across) and a seven-bot crew crosses them on foot. A man placed where none of the 7 holds and 3 m samples of his hall can see him is placed outside the
hall. Withdrawal gets its numbers with SIX men of its own (and the police that arrive after the exit). To meet the yardstick the lead has three choices: (a) fewer men awake at once in the halls (nine more squads staged by a graft change that
puts a SquadModifierBehaviour child into Dancefloor02a#01/#02/#03 and On_Dancefloor#02 - reloc5 says it is not enough alone), (b) the men that no hold sees stay and the rest wait in the galleries (nobody removed, but a smaller fight at the
holds), (c) accept the gates' 30 s as the bots' fight and read C6. `PRESSURE_KNOWN` carries (5, 7) (5, 8) (5, 10) (3, 5) as ceilings: rooms_check fails when a rebuild is worse than C6's build, not when it is over the yardstick.

### P.7 GUESS / ASSUMED / NOT DONE

1. ASSUMED: a TriggerActorsDead's next list starts a SquadModifierBehaviour the way a TriggerDelay2 / TriggerBox list does (the 'office', 'walk' and 'floor' stages are the same message from other senders; none of the three has been seen to work in
   a live club round - C5's log has no line that tells). If it does not, the nine gate squads never come and the club is emptier by 21 men; the gates still open by their 30 s.
2. ASSUMED: the seven copies of the message (one per bot squad's TAD) are idempotent.
3. THE HUMAN: the front office's four, Dance#02, the upper floors and the entrance's squad no longer stand awake from the start. A human who runs ahead of the bots meets none of them until the gate before their room has opened (a bot dies
   before it = they never come).
4. GUESS: GUN_RANGE 60 m (kl_fa_bank.PRESSURE_RANGE's), the two caps (the Withdrawal's upper numbers: its own posts alone give 2 / 3), the +3 for a man who would appear in view, ROOM_G_MIN, the model without kills (the table says both).
5. NOT ESTABLISHED: why four bots stood on the walkway's west end (the log has no 'move:' lines: `MoveLog=1` is in the first of the ini's two [Bots] sections and the hook of the run wrote none). Run C6 needs them.
6. NOT DONE: a graft step that gives the four modifier-less squads a start child; stock F07's yardstick (its bot squads are routs, not places - the Withdrawal build was used); a second optimiser pass on the delivered holds (the holds of
   reloc4 were c_club3's; this build's holds differ for floor2 .. floor1s); the `fa` check's DEGRADED note on club_bare ('12 of 21 squads are named by no object': the gate squads are named by the bots step, the bare folder has none).

### P.8 What run C6 must show (hook = the newest; `[Bots] Log=2 MoveLog=1` in the ini's ONE [Bots] section; the club's folder `club` of c_club4 or c_club4_music, idle human, 0.05 dial as before)

- The walkway gate: no 'lost' line before GO+60 s (C5: first hit GO+22.9 s, four dead at the walkway by GO+43 s). The bots' own positions in the 'move:' lines (this is the only way to learn where the seven stood and why the four stood at x 1520).
- Per gate the time it opened and why (a bot's positions stop within 10 m of the hold and start again before arrival + 30 s = the men died; at arrival + 30 s +- 1 s = the clock). A gate that always runs the clock names men nobody hits.
- That the gate squads COME: a picture at each gate (every 2 s) with men on the deck / upper floors after the floor1s gate opens; a hit on a bot from a man of a gate squad (the 'lost' place against WAKE_AT) before that gate's opening = the wiring is
  wrong. No such man ever = assumption 1 failed.
- The first death after GO+60 s (Retomoto's gates: GO+175 s); the casualty per gate against the table above: floor2 / floor1n / floor1s are the rooms 5 .. 10 guns bear on.

### P.9 Delivered folders (checks in each folder's `checks/summary.txt`; `chain.sh` / `checks.sh` / `dyncheck.py` / `routes.py` / `blocks.py` beside them; KL_TOOLS-aware; the builds ran on a scratch copy of HEAD's `tools/` + this commit's `kl_fa_club.py`: `C:/kl_scratch/club_pressure/h`, because `kl_fa_bank.py`, `kl_chars.py` and `kl_expansion.py` were modified in the working tree by other sessions)

| folder | silent (`C:/kl_build/c_club4/`, against the installed stream file) | with the music (`C:/kl_build/c_club4_music/`, against `C:/kl_build/v_club/PC_Def.str`) |
|---|---|---|
| `club` | `22177f4fac075124fe3599de443e762ae6aa128f` 179,251,298 | `69649165c0a735e46a56ba16672c87f344e30b98` |
| `club_wavslim` | the same archive, slim .WAV | the same archive of that set |
| `club_noai` | `e7754c1f0a2330aa439c5a32a6c39be4545dfa47` (= c_club3's, unchanged) | `b1c31429f9b238ae5e8a0eab436a0855b11fd947` (= c_club3_music's, unchanged) |
| `club_bare` | `075c78480d4ac904a9a225c7d01525524ca6aa41` | `c6699230541be0278f6e6b39cd1c60485ac1d798` |

Checks on all eight: the same known findings as c_club3 (preflight CRASH 1 / audit on the silent set = the stream clips; chars glow30.fx; escape 217; guns on the bare folder), everything else PASS, including `bots_gate` (rooms_check with the pressure table) on `club` and
`club_wavslim`, `bots_dyn` through dyncheck.py, `club_check`, `reverify`, `impact`, `vaultfx` (`python tools/kl_fa_vaultfx.py check` PASS on all eight). Rebuild: `sh C:/kl_scratch/club_pressure/deliver.sh <root> silent|music` (bare build, noai chain, full chain, checks).

## Pressure, second fix (2026-10-12) - after the skeptic's four faults on c_club4 (tools/kl_fa_club.py; sets `C:/kl_build/c_club4` and `c_club4_music` REBUILT in place; scratch `C:/kl_scratch/club_pressure/fix/`)

Built on a scratch copy of HEAD's `tools/` (`C:/kl_scratch/club_pressure/h`) + this `kl_fa_club.py`, because `kl_chars.py` is modified in the working tree by another session. Nothing has run in the game.

### Q.1 The four faults, one by one

1. **The yardstick is not met in four of five rooms - CONFIRMED, NOT CLOSABLE IN `kl_fa_club.py`.** Recounted on the rebuilt folder: holds 0 / 5 / 5 / 5 / 3, walks 0 / 7 / 8 / 10 / 5 (caps 3 / 4). `PRESSURE_KNOWN` is a regression guard, not a proof, and this note and the check's wording now say so. What stays awake from the load: 15 men (Dance#01 3, Surprise2 2, On_Dancefloor#02 3, Dancefloor02a#01/#02/#03 6, FatBouncer 1);
   the nine squads that can be staged already are (21 men). The six squads that cannot (no start child) need a graft change; Dance#01 / Surprise2 count as awake although a box wakes them (conservative). Measured this round (`fix/exp.py`): moving the deck's four from gate 4 to gate 5 changes none of the five rows. The honest reading: **C6 is a measurement run**, not a proof that seven bots survive past floor2.
   The levers left are the lead's: fewer men awake at once in the halls (a graft: start children for the four modifier-less squads, reloc5 says that alone is not enough), or fewer men. Nobody was removed.
2. **The wake fires from the first bot's gate and a laggard meets the woken men - CONFIRMED (MEASURED, skeptic's `lag.py`: floor1s walk 10 -> 12 guns at (-1360, 40, 2083)), FIXED.** The cause is three men of the deck over dance floor 2's south wall (YokoGuards Guard#01 at (0, 364, 2050), WaitingRoom Guard#02 (200, 368, 2250), Guard#01 (475, 363, 2275)):
   woken by floor1s's TriggerActorsDead they see its walk through the deck's rail (43 of its samples). Two changes: (a) `YokoGuards` and `WaitingRoom` are now awake at gate 5 = woken by the LAST gate (stairs) and named by no gate (`room_men`: a man woken by the last gate belongs to no room; `WAKE_AT` w = len(ROOMS)); (b) the check:
   `gun_table` adds `lag_worst` / `lag_at` = the most guns bearing on any leg sample or hold of gate k with the men THIS gate wakes counted (wake k + 1), the last gate also on the walk from its holds to the seal hold; `pressure_check` FAILS when it exceeds max(hold_worst, leg_worst), and the 'appear' rule now covers the last gate's holds too (`range(1, len(gates) + 1)`).
   Result: laggard case equals the plan at every gate (0, 7, 8, 10, 5); skeptic's `lag.py` on the new folder prints 10 at floor1s. The deck's four now come when the stairs fight is won - a human running ahead meets them last.
3. **club_bare differs from c_club3's - CONFIRMED, intended.** It carries the 13 moved men (`PRESSURE_MEN`) and the wake staging (`squads_now`: field 3 = 0 for the nine squads). This round's `club_bare` is byte for byte c_club4's first (sha1 `075c7848...`): the second fix changes only the chain's `wake` step, which acts after the bare build. `club_noai` is still c_club3's.
4. **The wake path is an assumption that never ran, and `dyncheck.py` was widened for it - CONFIRMED, NOT CHANGED.** A fallback timer or human box that wakes the nine squads when the gate chain does not would fire in the working case too and so defeat the staging; a fallback that fires only when the chain failed cannot be told from the data. `dyncheck.py` lets through exactly the planned (gate, child) pairs, nothing else: it is
   the stock rule with the one planned exception. Run C6 decides (P.8 / Q.3): if no man of a gate squad ever shows, the assumption failed and the club is 21 men emptier; the fix then is to wake them from a TriggerDelay2 / box, which the 'office' stage has already used.

### Q.2 Table (MEASURED, `hold-guns`; holds worst of 7 / walk worst; laggard case in the check)

| gate | holds | walk | laggard | awake |
|---|---|---|---|---|
| walkway | 0 | 0 | 0 | 15 |
| floor2 | 5 | 7 | 7 | 15 |
| floor1n | 5 | 8 | 8 | 15 |
| floor1s | 5 | 10 | 10 (12 before) | 18 |
| stairs | 3 | 5 | 5 | 33 (37 before: the deck's four now wake after it) |

### Q.3 What C6 must show beyond P.8

The deck's four (YokoGuards, WaitingRoom) appear only after the stairs gate has opened; a hit from one of them on a bot before that = wiring wrong. Set ONE `[Bots]` section with `MoveLog=1`. The first death after GO+60 s, and the rooms floor2 / floor1n / floor1s as the casualty rooms - if the crew passes them, the caps were stricter than needed; if it dies there at 5..10 guns, the lead's choice in Q.1 (1) is what is left.

### Q.4 Delivered folders (sha1 of `F01_Main.zip`; checks in each folder's `checks/summary.txt`)

| folder | silent `c_club4` | music `c_club4_music` |
|---|---|---|
| `club` / `club_wavslim` (one archive) | `d809a1bfed7afab9824303ba9e0c69a3c7712576` | `d6bdb13d3a45e1d7e28aa9ad6e77f146a0e8a2cd` |
| `club_noai` | `e7754c1f...` (unchanged) | `b1c31429...` (unchanged) |
| `club_bare` | `075c7848...` (unchanged) | `c6699230...` (unchanged) |

Checks: the same known findings as before (preflight / audit stream clips on the silent set, chars glow30.fx, escape 217, guns.json on the bare folder); `bots_gate` (rooms_check with the laggard rule), `bots_dyn` (dyncheck.py), `club_check`, `reverify`, `impact`, `vaultfx` PASS on all eight; the music set's `stream_whd` PASS. Rebuild: `sh C:/kl_scratch/club_pressure/deliver.sh <root> silent|music` after removing `club*` (not `club_noai`) from the root.


## Wake, after run C8 (2026-10-12) - do the nine staged squads ever come into the world? (tools/kl_fa_club.py; sets `C:/kl_build/c_club5` and `c_club5_music`; scratch `C:/kl_scratch/club_wake/`)

Labels: MEASURED = run on the files / logs, READ = read in kl2.exe (debug/dasm.py, debug/vtfuncs.py), ASSUMED / GUESS as said. NOT RUN IN THE GAME.

### W.1 What C8 shows (MEASURED: `C:/kl_scratch/club_wake/c8hits.py`, `c8rooms.py`; log `live/C8_club_staged.log`, GO = state 0x19 at 06:05:48.2)

- The log has no line that tells a squad came into the world: the hook logs the seven bots' health only (`lost ... at x y z`), no gate, no squad, no actor list. The pictures (`C8_club_staged_100s .. 400s`; read: 160 s and 220 s) are the idle human's view in the front office ('Loot area', the ammo panel, a plant and a balcony): no staged man is in them, and they say nothing about the rooms the crew was in.
- The 199 `lost` lines by room (room_of): walkway GO+53..57 s (23), floor2 GO+55..123 (31), floor1n GO+121..152 (68), floor1s GO+149..183 (73), stairs none, lane 4 at GO+217..218 (the pavement). So the crew was in floor1n at about GO+120 and in floor1s at about GO+150.
- Which man could have hit each of them: every hit was tested against the exact ray (Fire: eyes 160, 60 m, same floor) from all 40 men of the club. 195 of 199 have a line from at least one man who is awake from the load, 1 from nobody of the club (police), and the 3 left (bot 6 at (232, 30, -2850) .. (109, 30, -2846), GO+217 s) have a line from the Entrance squad's lane men (Guard#01 at (134, 29, -2398), 4.5 m) AND from nobody else of the club - but it is the pavement where the police arrive (they are not in the club's men), so it proves nothing. **No hit of C8 is attributable to a staged man alone. Whether the nine squads ever woke is NOT shown by C8, in either direction.** (C7, when the Entrance squad was awake from the load, has the same picture: its 7 lost lines at z < -300 are all on the pavement at z -2690 .. -2660, none in the lane itself.)

### W.2 What starts a parked squad (READ in kl2.exe)

| step | routine | what was read |
|---|---|---|
| the squad is parked | `ZSquadScript` slot 4 0x8b2120 inverts field 3 into `[this+0x58]`; slot 16 0x787a10 (phase 5) hides the members once (`0x8d2e20`) | field 3 = 0 -> the men exist but are hidden and not in the actor tables (re/retomoto_spawns.md 1). All nine have field 3 = 0 in c_club5 (MEASURED `wake_check`) |
| the sender | `ZTriggerActorsDead` 0x8def80 (only in session state 0x19): at its deadline or when its groups are dead it sends message [0x168ccf0] = 'AITrigger' to every entry of its list (field 2); `ZTriggerBox` and `ZTriggerDelay2` send the same word to theirs (fields 17 / 4) | the same name string in three .cpp files = one message id; the gates' own steps (DefendBehaviourRout) are started by exactly this and ran live on Retomoto |
| the receiver | `ZSquadModifierBehaviour` and `ZDefendBehaviourRout` share slot 26 = 0x4ebed0: message [0x168d804] ('AITrigger') runs slot 34 unless `[+0x41]` (set by 'AIBlocker', sent by nothing here) or (`[+0x42]` = field 8 and `[+0x40]` = started before). Field 8 is 1 on all nine modifiers, so the second and third copy of the message are no-ops | `[+0x42]` is the last-but-one field of the modifier: MEASURED 1 on all nine (`dump3.py`); idempotent for the seven bot squads' seven copies, which was ASSUMED in P.7 and is now READ |
| slot 34 of the modifier | 0x833830 -> `0x791090(rout, [rout+0xb0])` (the Defend rout's slot 34 is 0x457720 -> the same 0x791090 with `[rout+0x60]`) | 0x833830 skips only when the session is a game-mode-3 client (`[rules+0x54]` = 3: 0x4b0a40 true AND 0x863a60 true; the latter is 0 for any mode above 3); the log of every run says 'game mode 4' |
| the goal | 0x791090 proceeds when `[goal+8]` is 0 or 4: the modifier's goal is the 0x1c-byte object of slot 14 (0x681210), its constructor 0x68eab0 sets `[+8]` = 0 | then, unless `[squad+0xbc]` is set (the last bool of a rout; it is 0 on all nine), `0x7f6750(squad, goal)` |
| the show | 0x7f6750: for a squad that is not a mode-3 client it runs 0x706fc0(1) and, with members counted (`[squad+0x8c]` / `+0x90`), `0x7c0d50(squad, 0)` unless `[[squad+0x19c]+0x20d]` | `0x7c0d50` shows and enters again every member whose node has the hidden bit (re/retomoto_spawns.md 1). **The modifier is a first goal of any kind: it brings a parked squad into the world by the same path as a Defend rout.** |

So the answer to 'does the gate's message reach 0x7c0d50' is **yes, READ**. It has not been seen to work in OUR level: (1) no build of ours has had a squad that only a modifier starts shown by a trigger (the 'office', 'walk' and 'floor' stages started squads this way too, but C8 and its log cannot say they showed); (2) what stock does: the campaign's own 'Alert' children (eAM_Activate, six of the nine) are the only thing Dead Men names these squads by (MEASURED `dump6.py`: the club has no DefendBehaviourRout under `AI_Players!`; the campaign's static men wake by modifiers), stock FA F08 names a parked squad's modifier from a TriggerDelay2 (its `Gameplay!20_Guard_Office_A\30_SquadModifier`, eAM_NotSet; MEASURED `f08.py`, `census.py`: 2 of 12 parked squads of F08 have ONLY a modifier named from outside), and the 18 modifiers F07 names from a timer; the story levels do the eAM_Activate form 19 times.

### W.3 Per squad - what the gate's list names, and the verdict

The gate is the bots' `TriggerActorsDead` of the room before the squad's own (WAKE_AT), in each of the seven bot squads (7 copies per squad, MEASURED `dump4.py` on c_club4/club and `wake_plan_check` on c_club5/club). Class of every start child: ZGROUP node with one `SquadModifierBehaviour` controller (field 4 eAM_Activate, field 6 eALM_Alert; SurpriseStairs also eEM_FireAtWill), message 'AITrigger'.

| squad (men) | named node | named by (c_club4, before this round) | verdict from the reading |
|---|---|---|---|
| Dance#02 (3) | `\Alert` | floor1n's gate; floor1s's gate names its Guard#01 / #09 as men to wait for (not a start); the squad's own 'wiped out' list (field 8) names F07's `FollowPlayers!TriggerCounter` | wakes (READ) |
| Rave#02 (3), Rave#01 (2), Lounge#02 (2), Lounge#01 (3) | `\Alert` each | floor1s's gate | wakes (READ) |
| SurpriseStairs (2) | `\Alert` | floor1s's gate | wakes (READ) |
| Entrance (3) | `\SquadModifier` (its own ZSquadScript field 4 list names it too) | floor1s's gate; the stairs gate waits for its Guard#02 | wakes (READ) |
| YokoGuards (2) | `\SquadModifier` | the stairs gate | wakes (READ) |
| WaitingRoom (2) | `\Alert` (its `\VisionAdjust`, eAM_NotSet, is named by nothing: it is not needed and was left) | the stairs gate | wakes (READ) |

Nothing else names any of the nine (MEASURED `dump4.py`: the only referrers are the gates' TriggerActorsDead lists; in particular no campaign box or timer survived the conversion). **The weak point was not the message but the SENDER: the gates fire only when a bot has reached the hold of the room before** (`TriggerActorsDead` is armed by the bots' step; a human who runs ahead arms nothing, and a crew that dies in room k never wakes the rooms after it: the squads then sleep for good). The pictures of C8 and the log cannot tell whether a gate fired.

### W.4 What was built (flag `WAKE_MORE`, default ON with PRESSURE; `--no-wake-boxes`; off with `--no-pressure`, `--no-gates`, `--legacy`, `--no-ai`; the flag travels in van.json)

Each staged squad's start child is now named by THREE objects (any one wakes it; the others are no-ops by field 8):

1. the gate of the room before (unchanged: the `wake` chain step);
2. **a criminals-only TriggerBox** (field 0 = 1, field 14 ECPS_FA_MERCONLY, field 15 = 0 = fires once; the walk / floor boxes' form) on the hold area of THAT room (the room whose gate names the squad; it is `WAKE_BOX`: the seven holds of the plan + 100 on each side, y from 40 under the lowest hold to 170 over the highest). The human who runs ahead of the bots meets the guards when he reaches the place where the bots would hold. Three boxes, one per wake group: floor1n (Dance#02), floor1s (the upper floors, SurpriseStairs, Entrance: 15 men), stairs (YokoGuards, WaitingRoom: 4 men). They are three free single objects of F07 (WAKE_NEW: `tbExitLoot`, `tbExitFinancialAlley`, `tbEscapeAI`; named by nothing in F07, MEASURED `f07.py`);
3. **a backstop TriggerDelay2** per group (WAKE_NEW: `RandomizeFight!Timer_LEFT` / `_RIGHT`, `RivalMercVan!Timer_PFBlocker`), started by the AIMonitor's round-start list like the seal's clock: floor1n 166 s, floor1s 204 s, stairs 246 s after the round-start event (= GO+157.5, +195.5, +237.5 s). Each is the slowest crew's arrival at the room (10 s start + 18 s loot + the path at GATE_SLOW 200 / s + 30 s for every room before) + the gate's 30 s + `WAKE_DELAY` 3 s, so it never comes before the slowest crew's own gate (`wake_plan_check` fails below it) and sits before the van's margin (360 - 75 s): no squad sleeps for good.

NOT done, and why: **no DefendBehaviourRout was added to the squads.** A rout is a CHILD of its squad (every stock rout is, and the bank's waves put theirs under their own new squad): giving the nine existing squads one needs children inside existing subtrees of the .prp / .gms, or the squads re-made as new tops with cloned men - a graft change nobody has made on this level, with slot-id renumbering of the room trees, and nothing in W.2 says it would wake the men where the modifier does not (both end in 0x791090 -> 0x7f6750). If C9 shows the men do NOT come, that is the next step (the waves' form: `kl_fa_bank.extras_make`).

The PLANNER (kl_fa_bots_rt.gates_plan) keeps every hold and way out of a box that wakes a later room's men (`keep_out`); the first attempt at this build failed there ('gate floor1n: only 0 hold places': the room has two cover boxes and both lie in the new box), and `cross` is refused for a box that is not unavoidable. So `rt_for_club` now hands the planner every box of F07's except the three wake boxes (`wake_map` filter): bots may hold in them. The consequence is exactly the one the planner guarded against, bounded: the first bot (or the human) in the hold area wakes the next room's squads up to the gate's 30 s earlier than the gate would. The checks that carry it: `appear` (no man the gate wakes has a line to a hold), the laggard rule (the men woken while a bot is still on its leg / hold add no guns), and the new `wake_check` (no man a box wakes has a line to a mesh point of the box). ASSUMED: that a bot counts as a criminal for ECPS_FA_MERCONLY (if not, the box is the human's alone and only the gates and the backstops wake the squads for the bots: nothing is worse).

### W.5 New checks (in `check()` and `rooms_check`; MEASURED to fail on a wrong build, `negtest.py`, `neg2.py`)

- `wake_check` (every folder with the fix, bare too): each box and each timer of WAKE_NEW exists with the numbers of WAKE_BOX; the box's list = exactly the group's start children; fields 0 / 15 / 14; its centre and half-sizes as WAKE_BOX; inside the room's box +150; the timer's seconds, its list, a negative re-arm field (once), in the AIMonitor's round-start list and between 100 s and 285 s; every squad of the group parked and a SquadModifierBehaviour; **none of the group's men has an exact-ray line to a mesh point of the box** (100 apart, mesh heights, 60 m, not from another floor). The first try with a box moved onto Dance#02's men fails with 'has a free line to 14 of its 14 mesh points'.
- `wake_plan_check` (folders with the gates): the box holds at least 5 of the room's seven holds (the first bot fires it; all 7 in c_club5), the backstop is later than the slowest crew's gate + `WAKE_DELAY`, and **per squad one line** 'gate of X x7, box of X, backstop of X' with a FAIL if the squad is named by another gate, by fewer than seven copies, by another box or timer (a deliberately wrong WAKE_AT is refused with both messages).
- The existing 'round start names ...' rule of check() takes the three backstops as starters.

### W.6 The pressure is as before (MEASURED, `hold-guns` on c_club5/club; the same rows as P.5 / Q.2)

| gate | guns on the holds (worst) | on the walk (worst) | laggard (worst) |
|---|---|---|---|
| walkway | 0 | 0 | 0 |
| floor2 | 5 | 7 | 7 |
| floor1n | 5 | 8 | 8 |
| floor1s | 5 | 10 | 10 |
| stairs | 3 | 5 | 5 |

`PRESSURE_KNOWN` unchanged ((5, 7) (5, 8) (5, 10) (3, 5): the guard, not the yardstick). The boxes change who is awake WHEN only for a bot that is first in the hold area, and the exact-ray tests above hold for it.

### W.7 Delivered folders (sha1 of `F01_Main.zip`; checks in each folder's `checks/summary.txt`)

Built on a scratch copy of HEAD's `tools/` (`C:/kl_scratch/club_wake/h`) with this commit's `kl_fa_club.py` (`kl_fa_bank.py`, `kl_chars.py`, `kl_expansion.py` are modified in the shared working tree by other sessions). Rebuild: `sh C:/kl_scratch/club_wake/deliver.sh C:/kl_build/c_club5 silent` / `C:/kl_build/c_club5_music music` (Windows-style root: the voice check opens it from python).

| folder | silent `c_club5` | music `c_club5_music` |
|---|---|---|
| `club` / `club_wavslim` (one archive) | `3a1cb5283fc90bae927a28be6e991ed0c47ea14c` | `08e1320a80dc0cdb41ed4bd904b488548bd2cfba` |
| `club_noai` | `e7754c1f0a2330aa439c5a32a6c39be4545dfa47` (= c_club4's, byte for byte) | `b1c31429f9b238ae5e8a0eab436a0855b11fd947` (= c_club4_music's) |
| `club_bare` | `a919665cbc15b8c74cce535ea9a58a28e43ea63a` | `50dd40a7dbf07b748a107dd460a8fa827f77b279` |

Against c_club4/club only the scene members differ (`.prp`, `.gms`, `.buf`, `.oct`, `.rmi`, `.rmc`: six objects of F07 kept, three of them boxes, 26,830 -> 26,836 nodes); every other member is byte for byte. Checks: the same known findings as c_club4 (preflight / audit stream clips on the silent set, chars glow30.fx, escape 217, guns.json on the bare folder, `fa` DEGRADED: **4 of 21** squads named by no object in the bare folder - it was 12: the nine staged squads are now named by the boxes and timers), everything else PASS on all eight: `bots_gate` (rooms_check with the laggard rule and the wake lines), `bots_dyn` (dyncheck.py), `club_check` (with `wake_check`), `reverify`, `impact`, `vaultfx`.

### W.8 What run C9 must show (hook = the newest, `[Bots] Log=2 MoveLog=1` in the ini's ONE [Bots] section, the club's `club` folder of c_club5 / c_club5_music; GO = the line `session: state 0x18 -> 0x19`)

The hook cannot see the squads. What it can see is the seven bots' `lost ... at x y z`. The places below are where, at that gate, ONLY a staged man has a line (MEASURED `excl.py` on c_club5/club, the exact ray, men awake at that gate by the scene's wake table):

| squad | where only it can hit, and when | a hit there proves | no hit there BEFORE |
|---|---|---|---|
| Dance#02 (3) | the stairs holds (-365, 20, 805), (-365, 20, 685), (448, 96, 782): 2 / 2 / 3 guns, all Dance#02; its posts (-423, 37, 1355), (-535, 32, 1429), (627, 63, 1148) | a `lost` line within 2 m of one of the three after the crew reaches the stairs room (C8: the crew was in floor1s at GO+150 s, so GO+180 .. 200 s) is a Dance#02 man | any line there before the crew is in the stairs room (the holds of the earlier rooms are 8 m and more from them) |
| Entrance (3) | the queue lane between the stairs landing and the street: Guard#02 on the landing (-106, 182, -386), Guard#03 (-65, 21, -1307), Guard#01 (134, 29, -2398); the police arrive only on the pavement (z < -2500) | a `lost` line at z between -300 and -2400 (C7 and C8: none) is an Entrance man; a line at z < -2500 is ambiguous (police) | - |
| SurpriseStairs (2), Lounge#01 / #02, Rave#01 / #02 | none by design (no line to a hold or the walk: P.5); they are on the balcony over the stairs (y 480 .. 865) | only the PICTURES (below) | - |
| YokoGuards (2), WaitingRoom (2) | none by design: the deck over dance floor 2 (y 362 .. 368, z 2050 .. 2275) is awake only after the stairs gate; nothing of the crew's way is in their sight | only the pictures, or a human on dance floor 2 after the stairs gate | - |

For the five squads with no exclusive place the proof is a PICTURE: `C9b` = a human (the owner, 2 minutes; the scripted rig has no script for this map) walks the way in and stands 5 s in each wake box, with pictures every 2 s (kl_watch): box floor1n (centre (-1050, 105, 2730), half 260 x 105 x 280) -> at once after it Dance#02's three at their posts above are awake (look south-east across dance floor 1 from the doorway at (-1350, 30, 2000)); box floor1s (centre (-1306, 96, 1884), half 258 x 116 x 202; GO+about 100 s for a human who does not stop) -> the balcony over the stairs: SurpriseStairs at (-69, 504, 883) and (76, 504, 936) and Lounge#01 at (-102, 479, 1510) are looking about / shooting; box stairs (centre (-201, 123, 878), half 749 x 143 x 292) -> the deck over dance floor 2 (the four at (0, 364, 2050), (350, 362, 2050), (475, 363, 2275), (200, 368, 2250)) - visible from dance floor 2 after the human has been through the stairs box. **A man who is awake and has a line to the human shoots at once; a human who never sees them proves nothing: say it in the verdict.**

Seconds (after GO): a human who runs ahead wakes floor1n's group about GO+50 .. 90 s, floor1s's about GO+80 .. 110 s, the stairs' about GO+110 .. 140 s (GUESS: a run at 5 m / s; the hook's C8 log has no position of a human who walks); the bots' gates fire GO+120 .. 150 s (floor1n; C8), GO+150 .. 180 s (floor1s), after GO+183 s (stairs: C8 never logged a hit in the stairs room); the backstops are GO+157.5, GO+195.5 and GO+237.5 s. A squad that is not awake by its backstop + 5 s is a wake that did not work: then the sender is not the cause (all three senders reach the same receiver) and the receiver is: the next step is the waves' form (a DefendBehaviourRout per squad, W.4).

Said honestly: a hook probe that logs the hidden bit (`[node+0x3c] >> 10 & 1`) of the 21 men every second would settle every row above without a picture; it is a klhook change and not part of this round.

Files of this round (scratch, `C:/kl_scratch/club_wake/`): `dump1..6.py` (the nine squads, their controllers and referrers), `census.py` / `f08.py` / `f07.py` (stock), `c8hits.py` / `c8rooms.py` (C8), `boxes.py` / `blind.py` / `mesh_map.py` (the box places), `excl.py`, `negtest.py` / `neg2.py`, `deliver.sh`, `zipdiff.py`.


## Version 2: entrance, crowd, office, roof (2026-10-12; tools/kl_fa_club.py; sets `C:/kl_build/c_club6` and `c_club6_music`; scratch `C:/kl_scratch/club_v2/`)

Written after the owner's own round on c_club5 (C10, 14:08): 'club van doesnt spawn and idk i think we should rework it to spawn at the entrance of the club with a bunch of npcs dancing and you run
in and take the money from the office then you go to the roof like at the end of the campaign mission for a helicopter there would be better'. NOTHING OF THIS HAS RUN IN THE GAME. The build is the FALL-BACK
the design names: the crew starts at the entrance, runs in, takes the office money and fights back out to F07's van on the slab. The crowd, the roof stage and the helicopter are NOT built (V.6). Labels:
MEASURED = computed on the built files or the checkers' output; READ = read in code or notes; ASSUMED / GUESS as in the file.

### V.1 The five asks, as built

| ask | state |
|---|---|
| 1. start at the club's entrance | **IN, in part.** The 8 START points (and the TRAITOR, UCC and team-mode rows) stand on the pavement slab in front of the entrance, facing the lane mouth. NOT the queue lane (it is 1 m wide) and no crowd stands round them. |
| 2. a crowd dancing inside | **NOT BUILT.** See V.6: Dog Days has no dance clip for a civilian, the HFlow crowd needs a head-blob relocator, and the campaign's 17 civilians run on MiniCutsceneRouts that never ran in a Fragile Alliance round. The club is as empty of civilians as c_club5. |
| 3. run in, take the money from the office | **IN.** The loot (11 cases, 2.2 M, six on Yoko's desk and sofa table) and the ENTERS box are where they were; the way in is 118 m on the mesh from bot 3's first place (MEASURED, `inleg_table`), walked by the seven AI heisters too (kl_fa_bots plans START -> ENTERS -> loot -> five gated rooms -> exit by itself). |
| 4. up to the roof | **NOT BUILT.** The crew goes back OUT through the five gated rooms to the slab (the c_club5 way out). |
| 5. a helicopter | **NOT BUILT.** F07's van on the slab is the escape (`--exit van-slab`, the only exit the file builds; any other value is refused with a message). The fit test of the design (step 3) was not run: step 4 needs an edit of tools/kl_hvk.py (not allowed in this round) and the way up has no gates, holds or wake plan (V.6). |
| the van bug | **Explained (V.2) and fixed for V2.** |

### V.2 The van bug of C10 (READ in the hook log of the owner's round by the research; the arithmetic MEASURED in the file's constants)

In c_club5 the van's group is hidden from the load and shown by `van on` (ActivateGeom), which only two things start: the SEAL's clock (SEAL_AT 100 s after the round-start event = about GO+91.5 s, +2 s) or the counter of
the two dance-floor squads, and one second after the wardrobe's box. The owner reached the street at GO+65 s: stage 2 GO+63.2 s, stage 3 and 'THE CREW IS CALLED' GO+65.4 s, the van's state 3 (waiting) GO+76.4 s, left GO+84.2 s after
one wait of 8 s - about 7 s BEFORE the clock would have shown it. He saw an empty street. The hidden van was driving all the time (the state machine does not care): 'it did not spawn' = it was not drawn. The seal did not stop
him either (he stood 1.2 m beyond its far wall 2 s before the exit trigger: the heroes-only collision does not stop a Fragile Alliance human - the old note 'stops a FA human' was an ASSUMPTION). INFERRED from the log
and the clock; never SEEN (the hook logs neither the group's hidden bit nor the counter; the watch took no picture between 14:09:10 and 14:09:54). In V2 there is no seal and the van's show hangs on the ALARM (V.3), which
comes when the crew is in the office, 100 s before it can be at the van. `--v1` keeps the old form. A weaker unexplained sign: 'the vehicle's health object cannot be read (state 3)' at the first visit in every club run.

### V.3 The round as built (V2; every number is a constant of tools/kl_fa_club.py, V2 block after TRAITOR / set_v2)

- **START** (`START_V2`, y 30, on the slab z -3450..-2650): row 1 z -2740 x 160, 280, 400, 520; row 2 z -2840 x 220, 340, 460, 580; they face the lane mouth (118, 20, -2623). **TRAITOR** (`TRAITOR_V2`): z -2790, x -340, -240, -140, -40.
  UCC / team-mode rows: the START rows shifted (60, 0, 20) / `TEAM_MERC_V2` x -800..-620 z -2700, -2780. AFTER_DEATH (the police who come back) stay at x 900..1500, z -2760. Spawn camera and the jump point `01_Start` over the START rows.
  WHY EAST OF THE MOUTH (MEASURED, the first form failed): kl_fa_bots puts each bot 110..420 from the nearest START point and FAILS a bot that begins inside a level exit box ('is inside level exit box ... after 0 of path ... it
  calls the escape vehicle on the way in'); rows at x -300..120 gave six such FAILs. Every way into the club passes the lane mouth, so the exit box had to leave it and the rows had to be 420+ from the box.
- **Nothing is sealed** (`SEAL_OPEN`: both seal pieces out at build time; the office leaves were already open). The `route_in` walk (`routes.py`, START slab -> lane -> hall -> wardrobe -> landing -> dance floors -> walkway -> office, 753 samples) is FREE.
- **The way in has no gate.** 10 men of 'load' squads (Dancefloor02a#01/#02/#03, On_Dancefloor#02, FatBounceronWalkway) are awake along it; the 22 men of the squads with a start child (Entrance, SurpriseStairs, Dance#02, the upper floors, YokoGuards, WaitingRoom) sleep until their out-gate as in c_club5;
  Surprise2 and Dance#01 (the 'walk' stage, 5 men) wake at the ALARM. MEASURED (`inleg_table`, exact ray): at most **6 guns** bear on a stretch of the way in (bot 3, 92 m along, on dance floor 2's ramp (267, 204, 2978));
  the out gates' known numbers over the same floors are 7..10 on a walk (PRESSURE_KNOWN: floor2 7, floor1n 8, floor1s 10). `INLEG_KNOWN = 6` is a regression guard, not a yardstick (Withdrawal: 4).
- **The ALARM** = the first criminal through the inner office door (WALK_BOX, the end of the way in; ASSUMED that a bot counts as a criminal for `ECPS_FA_MERCONLY`). It starts `van timer b` (ALARM_DELAY 25 s) which shows the van, lets the hunters and the ten police in (GatePath of the gate) and
  speaks the exit line; the round-start clock `seal timer` (ALARM_BACKSTOP 200 s) does the same whatever a bot counts as. The counter of the two dance floors' squads still opens the gate too. The wardrobe's box says nothing now and sends the music's muffle switch (the crew is inside).
- **Exit**: the exit box and the three escape-area triggers are the slab's south-west corner x -1150..-300, z -3450..-2900 (`EXIT_V2`) - the van's boarding place (-637, 30, -3100) is inside, no START / TRAITOR point and neither the lane's street end is.
- **Wake boxes and backstops are OFF** (`WAKE_MORE` False under V2: they would wake the sleepers on the way in). The nine gate-staged squads wake only at their gate; a human who runs ahead of the bots meets them asleep.
- Texts: the start window and the briefing say 'run in ... fight your way out'. Everything else as c_club5: 40 guards in 17 squads, 10 police, 7 AI heisters (57 actors in 21 squads + 16 bodies, live precedent 99 / 55), the 160 rule, the room gates by fire, round-2 reset lists, voice lines in memory, the cloth check.

### V.4 Proofs (MEASURED)

- `--v1` is c_club5: the bare archive of `test --v1 --plan c_club2/club_bare/van.json` = `a919665cbc15b8c74cce535ea9a58a28e43ea63a` = c_club5's `club_bare` (built with a scratch copy of HEAD's tools; the same without `--v1` takes 2 min). The whole chain of `--v1` (bare -> `chain.sh`) gives `club` = `club_wavslim` = `3a1cb5283fc90bae927a28be6e991ed0c47ea14c`, c_club5's, byte for byte (run on the final file).
- V2 `club_check`: PASS on all four folders (spawn points: 79 places on the START's mesh part and free floor; the exit box holds the boarding place and no START point; the late-van chain; the reset covers the layer). `reverify` problems 0, `impact` 0, `bots_dyn` PASS, `bots_gate` PASS, `fake` PASS, `vaultfx` PASS, `voice` 0 left.
  Known and unchanged against c_club5: preflight `CRASH 1` / audit `FAIL 2` (the stream clips, silent set), `chars` (glow30.fx), `escape` 217 (the plain van-check, 211 'no ground under it'; `van-check` with the drawn pavement: 0), `guns` on the bare folder (no guns.json), noai audit 3.
- Timetable (rooms_check, after the round-start event; GO is about 8.5 s later): the TYPICAL crew (way in 120 m at 400 u/s, loot 18 s, every room 20 s, the 10 s hold) is at the exit trigger at **201 s** of 360 (the van needs 75); the quickest leaves the seal hold at 133 s.
  The crew held in every room's 30 s is at the trigger at **366 s - past the round's end, KNOWN** (the check logs it as a NOTE for V2 and judges the typical crew; V1 judged the slow one). Not fixable by data: the 30 s is TriggerActorsDead's own limit and the way in alone is 120 m.

### V.5 What the next live run must show (hook = the newest; `[Bots] Log=2 MoveLog=1`; in the ini's ONE [Bots] section; the expansion block drops `BoardNear`, `FollowOutHold=25`, `FollowOutSpare=1`: put them back; check `[Guns] Enable=1`, Escort=1, [Crew] Random=1, Risk=2)

1. **R0 `club_bare`** by direct boot, a scripted or real human, no enemies, no bots: START on the slab (look at the picture: eight bodies on the pavement, facing the lane?), the lane walk (1 m wide), the hall, the way up to the office (stage 0 -> 1 in the ENTERS box), pick up the cases, walk back; at the lane mouth stage 2 (ExitLootArea) and 3 in the exit box in the SW corner ('THE CREW IS CALLED'), the van shown and arriving. ASSUMED, and avoided by the layout: a criminal inside the exit box before stage 2 would call the van; no START or TRAITOR point and no way into the club lies in the box (south-west corner), so only a player who walks there on purpose does.
2. **R1 `club_noai`** from the menu: the seven AI heisters: do they walk in single file through the lane and the 0.4-0.5 m corridors (ASSUMED), loot at the desk, come back through the five gates, call the van and board? Hook lines: 'record N heist stage 0 -> 1 / 1 -> 2 / 2 -> 3', 'aboard', 'over'. Read the time of stage 1 against the typical timetable (about 100 s after the round start).
3. **R2 `club`**: the alarm. Look for: the ten police on the slab ends ~25 s after a criminal passes the inner office door (or 200 s after the round start), the van shown by then, the hunters coming down from the lounge, Surprise2 / Dance#01 awake on the walkway; the guns on the way in (`lost` lines of the bots on dance floor 2 / the ramp). A probe line for the group's hidden bit would settle the van; it is a hook change (not made).
4. `club_wavslim`: same archive, slim .WAV (listen).

### V.6 NOT built, why, and what it takes (the design's 'not_in_this_build', confirmed or extended)

- **Dancing / the crowd.** Dog Days' civilian set has no dance clip; the real Dance_01..06 clips sit inside the HFlow crowd's own database (22 clips, not the .ANM layout, undecoded). The campaign's 17 civilians run on MiniCutsceneRout + MiniCutPosObject (phoners, kissers, bartenders, coat check, ticket booth, the queue
  of 5 standing IN the 1 m lane) - a controller kind this file strips from the guards (STRIP) and which has never run in a Fragile Alliance round; keeping them needs `campaign_names` to keep `AI_Players!Civilians!*`, the Queue moved out of the lane (nine PosObjects), the .ANM join (+41 clips, 75 nodes, +740 chunks MEASURED by the
  research trial) and a live look at what the bots do with civilians in the way. The HFlow crowd (a): ZHFlow field 4 and ZHFlowLnkObj fields 1 / 2 are .buf head offsets the graft leaves stale, the cells hold absolute pointers: a head relocator and a one-flow load test in the T01 slot (research, not done).
  Not started this round because a never-loaded civilian script set could stop the whole map from loading, and the three never-run pieces cannot be told apart in one live run.
- **Roof stage and helicopter.** From the research (not re-measured): the way from the office to the low-roof pad (x -3600..-2200, z 3500..4300, y 859, free air above) is one free mesh walk of 256 m (roof door (-3479, 861, 3822), checkpoint 10 (-2378, 867, 4229)); three closures (storage `Firedoor_03` REF 21773, storage `HeroColi` REF 21820,
  roof `Firedoor_02` REF 21775) are to be sunk at build; the glass roof is not on it. The donor chosen: Dead Men's park chopper (M06 `EscapeSetup!EscapeChopper`, +86 nodes, the only helicopter that ran live under an F07 host: 7 of 7 bots escaped) as a third source through `kl_maps.chain`; it needs the **one-time edit of
  `tools/kl_hvk.py` `join`** (pad only if the part has a filler; take `h.lists` only if it keeps a static placement - unedited the donor join refuses with a TypeError; a monkey-patch in a new file would do too), F07's van and monitor removed (one `OnlineEscVehicleMonitor`), the 11- and 17-point splines rewritten in the node's frame (turned 25 degrees about y), the boarding and call boxes and four camera nodes moved,
  the AllyEscapeBox step. And the WAY UP: bots, gates, holds and the wake plan for the 256 m through the lounge, the third floor, the rave, the storage and the L-hallway (0.4-0.5 m) do not exist - `rt_for_club` / WAKE_AT / PRESSURE_MEN are written for the way OUT down to the slab. That is the larger half; nothing of it was started, so the helicopter would have been a
  prop with no round leading to it.
- **Gates on the way in** (design: three rooms, 20 s). Not built: the squads that could be staged have no start child (the 'load' squads Dancefloor02a#01/#02/#03 and On_Dancefloor#02 have NO child at all - MEASURED `sq.py`), so the only thing a gate could do is make the seven stand 20 s three times (60 s of the 360) in front of at most 6 guns; the typical timetable has 84 s of margin only.
  If the live run R1 loses the crew on dance floor 2 the next step is `kl_fa_bots_rt.gates_plan` on a synthetic plan START -> ENTERS with `ROOMS_IN`; if R1 shows them standing, the way in stays as it is.
- Round clock: the 360 s is the tool's constant (the game's own value unfound); not changed.
- Entrance men off the lane axis: not needed - they sleep (Entrance is gate-staged, awake at the stairs gate).

### V.7 GUESS / ASSUMED (sorted by what a wrong value costs)

1. The exit trigger acts only for a criminal at stage 2 (not read; the layout keeps every start and every way in out of the box). 2. A bot counts as a criminal for the walk box (`ECPS_FA_MERCONLY`): if not, the alarm is the 200 s backstop and the van is shown late again (the C10 bug) - raise nothing, read the log.
3. A TriggerBox / TriggerDelay2 'AITrigger' starts the other TriggerDelay2 (`van timer b`) and the GatePath named twice by two timers is harmless (ASSUMED, as the counter's and clock's two paths already were). 4. Seven bots pass the 1 m lane and the 0.4-0.5 m corridors in single file. 5. START rows 90 / 190 from the slab's house edge are inside the bounds (MEASURED: the warn boxes are 5.5+ m west).
6. ALARM_DELAY 25 s, ALARM_BACKSTOP 200 s, ROOM_TYPICAL 20 s, INLEG_KNOWN 6: GUESS. 7. The spawn camera (420, 230, -3330) looks at the START rows: never looked through. 8. Round 2: the walk box fires once per level (RESET_CANNOT): in round 2 the alarm is the backstop only.

### V.8 Delivered folders (sha1 of `F01_Main.zip`; checks in each folder's `checks/summary.txt`; `chain.sh`, `checks.sh`, `routes.py` (now also walks the way IN), `dyncheck.py`, `blocks.py` beside them)

| folder | silent `c_club6` | music `c_club6_music` | archive bytes (silent) |
|---|---|---|---|
| `club` | `9cf623381e5f4b2818a8a9cac300cde238c913ca` | `8171b17ba24e1dc81ebb828b3c979bfbba4a30dc` | 179,266,541 |
| `club_wavslim` | `9cf623381e5f4b2818a8a9cac300cde238c913ca` | `8171b17ba24e1dc81ebb828b3c979bfbba4a30dc` | 179,266,541 |
| `club_noai` | `8f9ac4a9f447e3187a9993d2d900c415db20f760` | `1b55868afd7af4dc90662faef696d1b280a7f7aa` | 165,332,704 |
| `club_bare` | `4e93df6cbd63626a3234685b6404dd5b991ad60a` | `abab66fd75aa0c9c4750854d39b81975baabd0dd` | 150,072,464 |

(`club` and `club_wavslim` share one archive; the slim .WAV differs beside it.) Checks of the music set: the same rows plus `stream_whd` PASS on all four (the club's 12 clips resolve against `C:/kl_build/v_club/PC_Def.str`, stamped by `kl_club_str.py stamp`); preflight and audit lose the stream findings on `club_bare`, `club` and `club_wavslim`.


Rebuild (a scratch copy of HEAD's `tools/` + `re/*.json` + `third_party/` with this commit's `kl_fa_club.py`; the shared tree has other sessions' edits): `sh C:/kl_scratch/club_v2/build/deliver.sh C:/kl_build/c_club6 silent` / `C:/kl_build/c_club6_music music`.
One V1 build: `python tools/kl_fa_club.py test <out> --keep --v1 --plan C:/kl_build/c_club2/club_bare/van.json`.
Stream clips the music set needs that the stream file lacks: none new (no crowd, no helicopter); the club's own 12 clips are in `C:/kl_build/v_club/PC_Def.str` (X.5).

## Version 2, second fix (2026-10-12) - after the skeptic's six faults on the first c_club6 (tools/kl_fa_club.py; sets c_club6 and c_club6_music REBUILT in place)

### Y.1 Fault by fault (each reproduced in the source before the change)
1. **"Not what the owner asked"** - ACCEPTED, nothing to build in this round: c_club6 is the ENTRANCE-START FALL-BACK of the van round. Of the five asks only ask 3 (office money) is whole and ask 1 is in part. Crowd, roof way and helicopter are NOT built (V.6). Do not call it Last Call v2 complete.
2. **Round 2 van (the alarm fires once a level)** - ACCEPTED, FIXED. READ in `wire()`: `walk box` has BOX_PER_MAN 0 (fires once a level, in RESET_CANNOT), so the alarm that showed the van could not show it again in round 2 and only the 200 s backstop was left. Now `van timer` (TriggerDelay2, `VAN_SHOW_V2` 30 s, GUESS) is named by the AIMonitor round-start list (which runs in EVERY round; `reset hide` hides the van again first) and shows the van; the alarm and the backstop still show it too (idempotent) and still let the police in. `check()` now wants `van timer` named by the monitor alone in V2. The log of the van's hidden bit is NOT added (the hook is not in this round's files): the C10 reading stays INFERRED.
3. **ENTERS check tested START_V1** - ACCEPTED, FIXED: in V2 the check now FAILS if any START_V2 point is inside the ENTERS box (the crew must ENTER by walking), and logs the V2 count (0 of 8).
4. **Stale route outputs** - ACCEPTED, FIXED in `routes.py` (all folders): route_built / route_doors start at 'office (the way OUT starts here; V1 START)', not 'START'. They are the way OUT; the way in is route_in. Fake-test: the first blocks of fake.txt are the two control levels; the club block is the last (see Y.3).
5. **AI stiffness, cover, plopping squads** - NOT ADDRESSED, a separate job; the 10 'load' men on the way in are awake and cannot be staged (no start child, V.6). Not claimed.
6. **Ten live-only assumptions** - ACCEPTED as stated; V.7 stands. First live run: club_bare, then club_noai, then club.

### Y.2 What the next live run must show beyond V.5
The van group visible about 30 s after the round-start event in BOTH rounds (before the walk box is crossed in round 2); a human at the van by GO+65 s finds it there.

## Z. Track "Last Call as the campaign", 2026-10-17 (V2 rebuilt with the van timer; the roof and helicopter stage is a PLAN, not built)

Status: BUILT OFFLINE, NOT LOADED LIVE. The V2 round (entrance start, office loot, van at the slab corner) was rebuilt from the working tree's tools/kl_fa_club.py (VAN_SHOW_V2 = 30 s GUESS, the `van timer` named by the AIMonitor round-start list, the V2 START/ENTERS check) in a scratch copy (`C:/kl_scratch/club_1017`, `deliver.sh`, silent set). Delivered: `<work>/build/club_1017/DM05A/{club,club_bare,club_noai,club_wavslim}`. The music set was NOT built.

Sha1 of F01_Main.zip: club and club_wavslim 91bc9e3357ffa93629e0019643a6a1147af8a5fe (179,266,524 bytes); club_bare 13ab136efc73cfe9436382221aeddafcce1d8996 (150,072,455); club_noai f0db067033fda7f7afcbe44faebc39581f175065 (165,332,690).

Checks (each folder's `checks/summary.txt`): impact 0, arms 0, van-check 0 faults, fake PASS, vaultfx PASS, voice 0, reverify 0, club_check PASS, routes FREE on all four; guns, bots_dyn, bots_gate, hold_guns PASS on club, club_wavslim, club_noai (club_bare has no guns.json, so guns exits 1 as expected). Known unchanged findings: preflight CRASH 1, audit FAIL 2 (3 on club_noai) = silent stream clips, chars glow30.fx, plain escape 217 = ground under a spline van.

Not proven live: that the van shows in round 2 by `van timer` (the C10 reading of the van's hidden bit is INFERRED); VAN_SHOW_V2 = 30 s is a GUESS.

The helicopter exit is OPTIONAL and behind a flag: `--exit heli-roof` makes main() stop with a message pointing here; `--exit van-slab` (default) is the delivered round. The plan (V.6, not re-measured, GUESS): park donor M06 EscapeSetup!EscapeChopper as a third source via kl_maps.chain; join its .HVK with a monkey-patch module around kl_hvk.join (pad only with a filler, take h.lists only for a static placement) instead of editing kl_hvk.py; remove F07's van, keep one OnlineEscVehicleMonitor; re-frame the 11- and 17-point splines (25 degrees about y); move boarding/call boxes and four camera nodes; AllyEscapeBox step; sink Firedoor_03 (REF 21773), HeroColi (21820), roof Firedoor_02 (21775); a `heli timer` in the round-start list for round 2 (the reset is unproven). Roof way: office to low-roof pad (y 859) is one free mesh walk of 256 m; it needs 2-3 route squads with holds and WAKE_AT points (not designed). Crowd: a STATIC civilian crowd is the feasible form (no dance clip in Dog Days); not built.

## AA. Version 3: roof and helicopter (2026-10-17)

STATUS: PARTIAL. `--exit heli-roof` in tools/kl_fa_club.py is NOT implemented (it still stops with its plan message); no heli set was built and none of the checks ran on one. `--exit van-slab` is untouched: kl_fa_club.py was not edited, and the default was rebuilt from the pre-work tools snapshot to prove the baseline: F01_Main.zip sha1 91bc9e3357ffa93629e0019643a6a1147af8a5fe (equal to the delivered club).

BUILT AND MEASURED
- tools/kl_hvk_donor.py (new; tools/kl_hvk.py not edited). `join()` has kl_hvk.join's signature; a donor part with no kept static placement is padded with nothing and brings none of its list codes. kl_hvk.join raises a TypeError (fill is None) on M06_FA_A's chopper (one VEHICLE placement, no static collision): measured. `python tools/kl_hvk_donor.py selftest` -> problems: 0 (ordinary join byte-equal to kl_hvk.join on M05_A + F07 systems; donor join round-trips, 1819 placements = systems 1008 + chopper 1 + others, 4 list codes = F07's own). `patched()` points kl_hvk.join at it for the length of a build.
- Donor step (scratch prototype, not in the repo): kl_maps.one(out,'F07','M06_FA_A',keep=True,campaign=False,slot='R09') with a Select that takes from M06 only EscapeSetup!EscapeChopper, EscapeSetup!ForceNoLoop, EscapeSetup!HeliNetSync, the chopper's Shards_Group_A clone group, Triggers!BoardingTrigger_Heli, Triggers!BoardingGameplayTrigger, PIP_Points!Boarding, Effects/Hind_Dammage_01.zip, Locations/M06_FA_A/M06FAA_Effects.zip and the three CloneGroup_Effects CarExplotion_AllocMany tops. It verifies 0 problems in about 23 s. Without the two effects zips there were 6 dangling refs; without the CarExplotion tops 8 unresolved clone paths (measured).

NOT DONE (the next round starts here)
- The Select for the systems side of the donor step must mirror the default selection (host_keep + KEEP/DROP), else F07's whole map (245 MB) is kept; the four EscCameraSetup! tops still have to be added to the wanted list.
- kl_fa_club.py: HELI flag, build chain (donor step, PSEUDO['R09'], step 2 with the author and HOST='R09', no van_layer), KEEP without VAN, prepare_host/wire for the chopper, spline re-framing (25 deg about y), boxes and camera nodes, AllyEscapeBox, sinking REF 21773 / 21820 / 21775, 'heli timer', the way-up (WAKE_AT_UP, holds, gate timetable), chopper-aware check/van_check. Every number in that list is still a GUESS until built and measured.
- First live run must show (nothing of this is proven): the chopper arrives over free air, lands on the pad (x -3600..-2200, z 3500..4300, y 859), the boarding trigger lets the crew in, one OnlineEscVehicleMonitor, the closures sunk, and the AI walks the 256 m way up.

AA handover, step 1 (2026-10-17, donor step; NOT RUN IN THE GAME, offline only)
- tools/kl_fa_club.py: new block after `DROP` (HELI, HELI_DONOR, HELI_WANT, HELI_DONOR_EXPECTED, `heli_donor(out, log)`), module `__getattr__` KEEP drops VAN when HELI (default False: KEEP and DROP compared equal to HEAD's), CLI `python kl_fa_club.py donor <out>` (exit 0 = 0 unexpected problems). Nothing else wired; main()'s `--exit heli-roof` still stops with the plan message; default van-slab path untouched (only the KEEP filter, a no-op with HELI False).
- heli_donor = kl_maps.one(<out>/chain, 'F07', 'M06_FA_A', keep=True, campaign=False, slot='R09') under kl_hvk_donor.patched() and a kl_graft.Select subclass (Donor): m() = exact name in HELI_WANT (the prototype's list + the four EscCameraSetup! tops), s_keep/s_drop = the club's KEEP (without VAN) and DROP, added in __init__ because kl_graft.build rebuilds its Select by the name kl_graft.Select and adds host_keep itself. Sets kl_maps.PSEUDO['R09'] = <out>/chain/F07+M06_FA_A on success.
- Measured: R09 builds in about a minute, 10,276 entities (452 tops), 244.3 MB (the archive stays big: F07's .prm/.TEX are not trimmed by dropping the map subtrees; step 2 repacks), kl_graft.verify 14 problems, ALL expected without an author layer and filtered by HELI_DONOR_EXPECTED (result 'problems_expected' = 14, 'problems' = []): 9 TriggerBox[17] refs to F07's dropped RivalMercs squads and 2 GatePath refs to RunToEscape!Timer (wire() rewrites them), 3 'exit-trigger' names of F07's vans (no VAN kept; prepare_host's exit-trigger edit), 1 'no loot' (the club lays its own). So: step 2 must NOT treat these as regressions; they must be gone after prepare_host/wire on R09. kl_hvk_donor selftest still problems: 0 (kl_hvk_donor.py not edited this step).
- R09 holds, among others, EscapeSetup!EscapeChopper, ForceNoLoop, HeliNetSync, Triggers!BoardingTrigger_Heli / BoardingGameplayTrigger, PIP_Points!Boarding, the four EscCameraSetup! tops, Hind_Dammage_01 + CloneGroup, and F07's kept Gameplay!RunToEscape!* / 040_Escape!* objects. No F07 van tops.
- The scratch R09_Main.zip was deleted to save space (the rest of the build files stay in C:/kl_scratch/club_heli/d2/chain/F07+M06_FA_A); rebuild with the `donor` command before step 2.
- Step 2 must know: PSEUDO makes kl_prpjoin.sides return 'systems' for every R09 top (kl_maps.redirect, J.sides), so all of them are kept as S's and nothing of the donor is lost; but F07's kept Gameplay/Specials objects are systems there too, so the club's KEEP/DROP and host_keep do nothing on R09 (they were applied in step 1). prepare_host (HOST='R09') and the Gameplay role objects must look them up by their names, which are unchanged. Still open as listed above (prepare_host/wire/check heli branches, spline re-framing, boxes, main()).

AA handover, step 2 (2026-10-17, heli build; offline, NOT RUN IN THE GAME)
- tools/kl_fa_club.py: `python kl_fa_club.py test <out> --exit heli-roof --keep` now BUILDS and check() PASSES. New: HOST_BASE ('F07'; heli_donor uses it), HELI_GROUP = 'EscapeSetup!EscapeChopper\Escape_Chopper' (MEASURED in R09: the ZGROUP with OnlineEscHavokCar + OnlineEscVehicleController + VehicleEffects), `heli_build(out, log)` (before van_check): runs heli_donor when PSEUDO has no R09, then kl_maps.one(out,'R09','M05_A',keep,campaign,tag=' heli',author='kl_fa_club',nav_base=nav_of('R09')) with HOST='R09' (so prepare_host runs on the pseudo level) under kl_hvk_donor.patched() and doors(); no plan, no ESC.van_layer. build() returns heli_build when HELI; test() writes van.json with check=None. main(): `--exit heli-roof` sets HELI + set_roles() (refused with --v1/--legacy); other exits still refused. Gates behind HELI: van_path() (= the chopper group), prepare_host (no NO_PLAN, no ESC.van_prepare, no marker-vs-drive check; the VAN_LATE block and the exit-trigger edit use van_path()), wire() (ESC.van_wire replaced by: every OnlineExitLevelTrigger names the chopper group), check() (the van block replaced by a heli block: 0 OnlineEscAnimatedVehicle, 0 FakeTarget, exactly ONE OnlineEscVehicleMonitor, 1 OnlineEscVehicleController, 1 exit trigger naming the chopper; stop_at_all False so the van-drive/FakeTarget-path checks do not run). Also HELI_DONOR_EXPECTED is now raw strings (a SyntaxWarning).
- Classification answer: under PSEUDO every R09 top is 'systems', so picks_of keeps ALL of them in step 2 (donor tops included) and host_keep/KEEP/DROP/Select do nothing on R09; they were applied in step 1. Only names equal to an M05_A map top would make M's lose (none seen).
- 'heli timer': NOT a separate object. Heli reuses the van's VAN_LATE roles: 'van on' (ActivateGeom) now names the chopper group, hidden from the load, shown by 'van timer' (VAN_SHOW_V2 = 30 s, GUESS) / 'van timer b'; RESET's 'reset hide' hides it again. Whether showing the group Escape_Chopper starts the flight (the Incoming/Escaping HeliFlyBehaviourRout are SIBLINGS under EscapeSetup!EscapeChopper, not children) is UNKNOWN - the flight is not placed.
- Measured (scratch C:/kl_scratch/club_heli, deleted; delivered to <work>/build/club_heli_1017/DM05A/heli with build.log): R09 step 1 + step 2 build; result 27,388 entities, 20 rooms, 300 MB, F01_Main.zip sha1 4859a95efbdf3be6a1f1bb0f25075762a34a64b5; step 2 problems = only the KNOWN '5 stream clips' (all 14 donor problems are gone after prepare_host + wire: confirmed); check() PASS; 1601 .HVK placements; 'squads that are not this file's' lists EscapeSetup!EscapeChopper (its ZSquadScript; harmless note). kl_hvk_donor selftest still problems: 0 (file not edited).
- Default unchanged: the bare van-slab build rebuilt with the working tools, `test <out> --keep --plan C:/kl_build/c_club2/club_bare/van.json`, gives 13ab136efc73cfe9436382221aeddafcce1d8996 = the delivered club_bare. The club sha1 91bc9e33... is that bare through chain.sh, whose tools were not touched, so it is expected equal but I did not re-run the chain.
- NOT done (step 3): placing the chopper (its pad x -3600..-2200, z 3500..4300, y 859), spline re-framing (25 degrees about y), boarding trigger/PIP box and the four EscCameraSetup! node moves, AllyEscapeBox, sinking REF 21773 / 21820 / 21775, the roof way (squads, holds, WAKE_AT_UP, gate timetable), heli-aware van-check/bots/chain.sh (they still want van.json's plan), the kl_graft hook for exit-trigger edits other than field 2. The heli folder was only checked by check(); bots/guns/chain steps not run.

AA handover, step 3 (2026-10-17, chopper on the pad; offline, NOT RUN IN THE GAME)
- tools/kl_fa_club.py, all behind HELI (default van-slab path: Doors.sunk, place_now, bot_opt are no-ops/identical with HELI False). New block after heli_donor: HELI_PAD (-2900, 859, 3900), HELI_WALK, HELI_APPROACH, HELI_GROUND_OLD, HELI_MOVE, HELI_SUNK, HELI_EXIT, HELI_BOT_PARK, HELI_PLACE, `bot_opt()`, `heli_frame`, `heli_to`, `heli_place` (called from prepare_host after the van line), `heli_hvk`, `heli_hvk_layer` (wraps kl_hvk.join inside kl_hvk_donor.patched() in heli_build). Doors.sunk() adds HELI_SUNK; place_now() adds HELI_PLACE; check()'s HELI block reads back the sunk closures, the boarding / PIP / on-map / exit nodes on the pad and the chopper's key-framed .HVK placement.
- METHOD: one rigid motion of M06's world. The splines are NOT rewritten: their points are local to their node (ZGEOM[1] = [Z', Y', X'] images, A.rot9), so turning and moving the node re-frames them exactly. Landing point = last point of 'Incomming' (MEASURED: world (-1535, 368, -6276) in M06, 275 from the stock boarding box (-1686, 133, -6541)); it goes to HELI_PAD, final approach turned to point from checkpoint 10 to the roof door (turn -318.8 = +41.2 degrees about y; NOT the 25 degrees of the plan: that number is only the splines' own node turn; the real turn depends on the approach wanted: GUESS), lift 859 (GUESS: M06 ground at the landing is y 0). Moved with it: Escape_Chopper, both spline nodes, CrashSite_Center_01 (the rotors' face target), BoardingTrigger_Heli, BoardingGameplayTrigger, PIP_Points!Boarding, CameraTrigger01, CamPos01; EscCamera01 stays beside CamPos01 (the van's form); EscapeChopper_OnMap goes to the pad centre (GUESS: it is the map icon). The chopper's one key-framed .HVK placement gets the same motion (heli_hvk, van_hvk's arithmetic; ASSUMPTION as there: the placement is the pose at load). The generic placement check (lv.moved) stays quiet.
- MEASURED in the built level: hub lands at (-2900, 1227, 3900); start pose (5149, 5590, 18714) (outside the level, 150 m up and away); Incoming ends (-937,1926,5318) -> (-1665,1558,4583) -> (-2399,1291,4085) -> (-2900,1227,3900); Escaping leaves west to (-21891,4594,-1419). The three way-up closures (storage Firedoor_03 and Firedoor_02 leaves D03, storage HeroColi) are sunk by the office doors' machinery (9 nodes sunk now, 9 REF ids through cut_collision; placements cut). Exit box, the three escape-area POI triggers, the marker and JumpPoint 06_Exit are on the pad (HELI_PLACE). The AI heisters' waiting place for kl_fa_bots (`bot_opt()`, park) is HELI_BOT_PARK (-3250, 859, 3770) (GUESS).
- 'heli timer': still NOT a separate object; the existing van timers show the chopper group 30 s into every round (hidden at load). Whether the chopper should be hidden until the exit trigger calls it (M06 hides it?) is UNKNOWN; if the live run shows a chopper hovering at its start pose, set the show lists to empty.
- NOT done / for the next step: (1) clearance of the approach: Incoming crosses x -937..-2900, z 5318..3900 at y 1926..1227 (700 above the pad) and the start is 150 m out; NOT checked against the map's geometry or room boxes (the roof is 3000 high at most per the vision space); the pad is 1400 x 800 for a rotor of about 1700 (V.6 said free air above). (2) the way up for the bots (squads, holds, WAKE_AT_UP, gate timetable) and the round's other layout (START at the entrance, police on the slab, bounds and kill boxes are the slab's) are the van round's; the exit is on the roof. (3) kl_fa_bots / bots-check / chain.sh for the heli folder were not run; they still want van.json's plan; `kl_fa_club.py check <folder>` on a heli folder FAILS the van-form count ('0 OnlineEscAnimatedVehicle ... 1 wanted') because HELI is set only by main --exit heli-roof: run it through `test ... --exit heli-roof`. (4) PIP/gameplay boxes keep M06's heights (420 / 1050 up).
- Result: `test <out> --exit heli-roof --keep` -> RESULT: PASS (27,388 entities, 20 rooms, 300 MB); F01_Main.zip sha1 6bb44c17c31c2a063779013cd3bff0fb3fd92fdf; delivered to <work>/build/club_heli_1017/DM05A/heli (replaces step 2's; build.log beside it). Default bare van-slab rebuilt with the working tools: 13ab136efc73cfe9436382221aeddafcce1d8996 = the delivered club_bare (unchanged); the club 91bc9e33... goes through chain.sh, not re-run.

AA handover, step 4 (2026-10-17, the way up for the AI heisters; offline, NOT RUN IN THE GAME)
- tools/kl_fa_club.py, all behind HELI (default van-slab untouched: bare build rebuilt with `test --keep --plan .../club_bare/van.json` = 13ab136efc73cfe9436382221aeddafcce1d8996, same as delivered; the club 91bc9e33... is that bare through chain.sh, whose steps I did not change; kl_hvk_donor selftest problems: 0, file not edited). Changes: FLAG_NAMES now starts with 'HELI' (travels in van.json, load_flags restores it; old folders keep False); room_of() HELI branch (about 3456: y>=700 'third', y>=420 'stairs' if z<900 and x>-400 else 'lounge'); block HELI_UP_Y / HELI_ROOMS (two rooms appended to the five: 'lounge' box x -2300..-300 z -150..1250 y460, 'third' box x -2900..-1900 z -450..50 y860) / HELI_WAKE / HELI_MEN / HELI_GATE_AT / HELI_KNOWN (lines about 3316 and 3418-3455); set_route() (called from load_flags and from main's --exit heli-roof) swaps ROOMS, GATE_AT and WAKE_AT in place; room_men() skips the 'open' hunters; men_table() adds HELI_MEN; HELI_PLACE moves FASpecials!PIP!ExitLootArea to (-3450, 900, 3680); bots_gates() raises if no 'exit' station follows the seal hold or it is over 600 from GATE_AT; hold-guns / rooms_check read HELI_KNOWN.
- Route (MEASURED by `bots` + planner): 7 gates walkway, floor2, floor1n, floor1s, stairs, lounge, third, then the seal hold near (-3770, 860, 3500), then the park at (-3250, 859, 3770) in the AllyEscapeBox (7 places, clearance 186..366). The five old gates plan unchanged. New holds: lounge round (-1748, 460, 697), third round (-2525, 860, 8), 7 cover places each. Wake: stairs opens -> Rave#01, Lounge#01, SurpriseStairs; lounge opens -> Rave#02, Lounge#02, YokoGuards, WaitingRoom; third wakes nobody.
- Five men stood in the corridor (51..138 from the path) and the planner refuses a way past a living man: HELI_MEN moves Lounge#01 G08, SurpriseStairs G01 / G02, Rave#02 G02 / G07 to mesh points 600+ from it (found by scratch mv.py). GUESS: the mesh points are standable and inside the squad's room; cover and walls round them were not looked at.
- Checks on the full chain result (chain.sh from the heli build: lighten, wardrobe, bots, guns, lighten, dyn, wake, strays; 4 min 40 s): check PASS, bots-check PASS (7 squads with the seal gate), dyn PASS (0 FAIL, 2 NOTE: START 10 above feet, AllyEscapeBox not used by stock R09), wake 28 lists. hold-guns: lounge holds worst 2, walk 6 at the stairs' head (-6, 460, 850) (8 with the men the gate wakes: the laggard case), third holds worst 5, walk 5 at (-2353, 860, -27). Both are OVER the yardstick (holds 3, walks 4); HELI_KNOWN records them as regression guards, they are NOT fixed. Timetable: the typical crew reaches the exit trigger at 244 s of 360; a crew held 30 s in every room reaches it at 479 s, past the round clock (the same KNOWN note as the van's, now worse by two rooms and about 250 m). Both are model numbers, UNMEASURED live.
- Delivered: <work>/build/club_heli_1017/DM05A/heli = chain fin (replaces step 3's), F01_Main.zip sha1 18b1c8926c36393e0d3123ae57acf90b088c2375 (the pre-bots test build is not the delivery). The chain's fin_wav is byte-identical (same sha1).
- First live run must show: the AI walks office -> lounge -> third floor -> roof door without stalling at the corridor corner (-48, 460, 1443) or the stairs' head; each of the seven gates opens on its TriggerActorsDead (30 s at most); the bots stop at the park place on the pad and board the chopper (they vanish in the AllyEscapeBox); the five relocated men stand on the floor and are not inside a wall; the lounge / third squads wake when stated; the exit trigger (moved to (-3450, 900, 3680)) is reached before the round clock; the crew is not shot dead on the lounge walk (6-8 guns). If the walk is too deadly, move more men or add a gate at the stairs' head.
- Not done: the dyn route images were not inspected; the exit trigger and HELI_GATE_AT are GUESSES; the typical-case time is a model, not a run.

### AA handover, step 5 (2026-10-17, why the chopper never showed in the 14:23-14:28 load test; offline, static reading)
- Cause (strong, from code and built data): nothing CALLED the escape vehicle. The only callers are the exit trigger (level-triggered, whoever stands in it; rules slot 44 -> 0x8154f0, needs vehicle state 0) and the last-vehicle call (game at round clock 2.0 s, hook fallback <= 1.75 s, klmove.c section 6, about 358 s into a 360 s round). The player idled at the entrance and all 7 bots were at heist stage 1 (floors y 20-460); the log ended about 226 s in. 'van 0 0.0s' is state 0 = not called, as expected.
- The "about 30 s" expectation was only 'Timer' (30 s) -> 'van on' (ActivateGeom) -> Escape_Chopper group: it UNHIDES the group at its start pose (about 44 m above the hub, 169 m from the pad on the map; units are cm). It does not start the flight, the hook logs nothing for it, and whether it is out of sight from the club is NOT established (the run's 40 / 60 / 90 s shots show the Arcade menu, not the level, so they say nothing about it). A visible show at 30 s was never well founded.
- Evidence: otrExitLevel (node 27120) = [0, '', Escape_Chopper, ...] at (-2900, 1059, 3900) half (700, 250, 500); AllyEscapeBox at (-3250, 1060, 3770); pad y 859 -> box centre = floor + 200, the y ranges contain pad and hub (1227), so 1060 vs 859 is consistent. Prp refs resolve by path, no dangling ones. HELI_WAKE feeds WAKE_AT through set_route with the room gates, independent of the chopper. The hook is not van-class-keyed: it reads rules state and the kind byte (ZHeli -> picture 171); the van card only draws after the stock escape panel draws, i.e. after a call.
- Side finding: heli_hvk moved the ZHeli HVK placement (REF 20041) to (-5881, 859, 9633); in M06/F03/F06 stock it sits at the origin. Probably harmless; smallest optional fix: skip placements at the origin in heli_hvk.
- Smallest fix: none for the show. Live test that WOULD show it: a non-idle human walks the roof route and stands in the exit box (-2900, 1059, 3900), or run >= 365 s so the last-vehicle call fires. Look for 'hud: van card ON ... picture 171' and 'bots: ... van 1+'; then watch the Incomming rout from about (5149, 5590, 18714) to the pad.
- ASSUMED: the call starts the Incomming rout via OnlineEscHavokCar field 0 (exe not read for this class); unhiding does not start the flight; Escape_Chopper group field 3 = 1 means hidden; the HVK shift is harmless; M06's rout-group layout works under the DD car class; HELI_WAKE woke the right squads (static check only).
- Adversarial check (2026-10-17, KLHook.log of the run kept in <DD>): round began 14:24:41 (s19), the log of the level stops 14:28:26 = about 225 s of the 360 s round, so neither the exit trigger nor the 358 s last-vehicle call could have fired. CORRECTION to the idle-player story: the human DIED at 14:26:08 (status1) and came back as a FED ('fed: you have stood 130 s', 'Prevent the criminals from escaping' pop-up), so from 14:26 on no human could enter the exit box as a heister at all. Bots: record 7 / 2 / 4 still at g1 on y 20-460, none g3. Also unproven: the chopper was never hidden-until-called by design (VAN_LATE timers unhide it at 30 s, see step 3 note); nothing shows the call starts the flight.

### AA handover, step 6 (2026-10-17, why the last-vehicle call did not fire in L1017_HELI2; offline, hook v82d built, NOT RUN)
- Log facts (L1017_HELI2.log): GO 15:12:30.210, round over 0x19->0x1f 15:18:30.393 (= clock 0 + 0.18 s), the banner said 'last: on'. The tick ran to the end (shoulder lines each second to 15:18:29.85, move lines to 15:18:21), no 'not on the game's thread', no 'nothing is done here', no 'a vehicle is under way'. Every branch of klmv_last_vehicle (klmove.c section 6) logs once it sees the clock in (0, 2.5] s, so NO pass saw the clock in that window, or the session read failed there. Other logs: the 'last:' line only ever appears when the clock was set (klfed 'nobody is left to hunt' -> 3.0 s, L1017_DM05A 12:59:08 'left 2.45', flagged 1) or a van was flagged; every natural 360 s end without a van (v70_T1E, v72_T5, v72_T7ctl, HELI2) has none: the fallback has never fired once in a natural round.
- Design answers: (1) a living heister is NOT needed, the call reads rules only (the fed state is irrelevant; DM05A fired its branch with the human a fed). (2) clock = float [rules+0x4c], pass every 250 ms (move lines show 0.25 s cadence), so a 2.5 s window holds about 9 passes. (3) the game's own call (0x81e570) is guarded: vtable slot 0x17c must return 3 AND a vehicle must be known ([rules+0x1e4] -> 0x6ece90, else [rules+0xe80], 0x81e5aa 'je' skips on 0); with a ZHeli escape and no earlier call there is none, so the game never calls and the hook's 1.75 s step is the only one. Old code waited for 1.75 s even then.
- NOT proven: why no pass landed in the window. Candidates left: klb_read failing in the last seconds (sub-state [session+0x54] 2 / 3 refuses), or the clock jumping past the window. Not resolvable from this log.
- v82d (klmove.c only): every pass notes the clock; from 10 s on each whole second one line 'last: clock X s (pass n ...): vehicle state, e8a, kind, vehicle, e80; the call is made at <= 1.75 (vehicle known) or 2.5 s (none known)'; with no vehicle known the call is made from 2.5 s (not 1.75); one line when the round leaves state 0x19 or the session cannot be read (clock <= 15 s) without the call: 'last: ... the clock was last read X s (n ms ago; passes; passes <= 10 s) - <which of the three cases>'. Test hook hud_v82d_test 6f75a924..., ship 61316ee8....
- Live test plan: any plain round of >= 365 s on the heli build, hook v82d, human alive or fed (no need to enter the box). Expect 'last: clock 10.xx s' .. 'last: clock 1.xx s' lines then 'the exit trigger ...'s vehicle ... called as the round's last' and 'hud: van card ON'. If the clock lines stop before 2.5 s the closing 'last:' line names the case.
- ASSUMED: the three candidates above are the only ones; ZOnlineExitLevelTrigger scan finds the heli (never run for a ZHeli); calling 0x8154f0 with the chopper starts its Incomming rout.

### AA handover, step 7 (2026-10-17, v82e; static reading of kl2.exe 0490, NOT RUN)
FINDING (HELI3: GO 17:22:51.785, over at GO+360.1 s, HUD clock last read 10.25 s, no call):
- The round does not end on the HUD clock [rules+0x4c]. Rules slot 192 (0x5dff40) counts the END timer [rules+0x200] down from state >= 0x19 and, at <= 0 with vehicle
  state 0 or >= 7, sets state 0x1f through vtable +0x68. A vehicle state 1..6 holds the end.
- The game's own forced call (0x81e570) acts when [4c] <= 2.0 (float 0xb5c828) and dt + [4c] >= 2.0 (double 0xb62258), needs vtable slot 0x17c == 3 and a known
  vehicle ([rules+0x1e4], else [rules+0xe80]), then 0x8154f0(rules, vehicle, 1).
- [200] is reset to 600.0 by 0x8c7a80 and set from the level settings property ([rules+0x2c]+0x2d4, 0x5897f0); [4c] comes from slot 36 (0x7c6d70, 360.0 const
  0xb2e7fc via 0x6d3130), the state 0x17/0x19 enters (0x5e8816, score +0x3c/+0x40) and slot 41 (0x7f09a0). klfed logged [200] = 360 at GO while [4c] ended 10.25 s.
  So the HUD clock ran about 10 s AHEAD of the end timer: its 2.0 crossing (and v82d's 1.75/2.5 s window) came only after the round had ended.
- ASSUMED, not proven: the writer that makes [4c] about 370 while [200] is 360 (likely level settings versus the 0x6d3130 path); the offset may differ per level.
CHANGE (klmove.c v82e): the trigger is the time left on [rules+0x200] ('rem'), valid when finite, > 0 and <= 700. Otherwise GUESS: rem = HUD clock - 10 (KLMV_CLOCK_LEAD_GUESS).
The call fires at rem <= 2.5 s (no frame is given unless a vehicle is known AND the HUD clock is not ahead of the end timer, then 1.75 s). The log now says, from 15 s
before the end, once per whole second: time left, END timer, HUD clock, offset, vehicle state/flags; and the 'last:' closing line carries both timers.
TEST PLAN: build hud_v82e_test, an Arcade round on Retomoto, read the 'last:' lines; expect a call at about 2.5 s before the end and the van.

## 2026-10-18 handover: civilians
tools/kl_fa_civs.py (see re/civilians.md) added to a copy, not to the map tool. Builds in <work>/build:
club_owner_1018/DM05A/club (30 civilians, F07 model, seed 18) and vault_owner_1018/DM03A (24, F07 model).
Checks: civs.check 0 FAIL; kl_fa_club.py check PASS (club); kl_fa_bank.py check PASS on the F01-slot copy
(the bank CLI fails on an F07-slot folder, also on the base); debug/check_passes.py 0 failed (bank keeps the known Shards_Group_A WARN). Not run live.

## Handover 2026-10-18 (kl-merge-c4, offline): Last Call roof + civilians
Done: build/club_owner_1018/DM05A/heli_civs = club_heli_1017/DM05A/heli + 30 civilians (kl_fa_civs build ... F01 ... 30 --model F07
--seed 18): 0 FAIL / 1 NOTE (room sets []), debug/check_passes.py PASS (all 6), .prm +567,264 bytes (F07 civilian model appended;
Club's own live-proven .prm ceiling is unknown, Hasta's was 79.9 MB). NOT RUN IN THE GAME. No tool default changed (no kl_fa_club.py edit).
NOT done (honest): (1) the roof marker/route fix. Findings: the escape POI (FASpecials!POI) is wired as in stock F07, activated only by
the pad box, and its tracker has a float 2500 (GUESS: visibility distance) - so the roof is not shown from the start. A flagged
(default off) change - AITrigger the escape POI from the loot trigger, raise the 2500 - is the next step; the POI handler semantics
(ZPointOfInterest info 0xcfd578, ZActivateGameplayTrackerDisplay 0xd09714) are not yet read in kl2.exe. (2) a mesh proof start->loot->pad
for the heli build and the bots' stall at gate g1 (live log) are not worked.

## Handover 2026-10-18 (kl-merge-c4, offline, round 2): Last Call roof marker + route proof
Built: build/club_owner_1018/DM05A/heli_roof (zip md5 1bcc46db791df152ac03cb0395d6fc93) = heli_civs + `tools/kl_club_roof.py build`
(NEW tool; no existing tool touched, so every default is unchanged; diff vs heli_civs: only the .prp, only 3 nodes).
- EXE READ (kl2, ZGameplayTrackerDisplay at HUD +0x10f8, 5 x 0x110 entries, drawn by 0x8e2060): the 2500 of
  ZActivateGameplayTrackerDisplay field 3 is a HIDE-WITHIN radius for non-vehicle entries (marker not drawn while the player is
  nearer); the next float (0.0) is a max distance, 0 = unlimited. The earlier note 'visibility distance' was wrong.
- The roof was never shown because POI_TheEscapeArea has ONE sender, the pad box (as stock F07): marker only once on the pad.
- Change: POI_TheEscapeArea added to the targets of 'van timer b' (TriggerDelay2 25 s, started by the box at the inner office door =
  the alarm), and the hide-within radius 2500 -> 800 (GUESS). `--timer 'van timer'` would show it 30 s after the round start but
  kl_fa_club.check wants that timer to name 'van on' alone (FAIL), so it is not the default.
- No door/blocker to open: kl_route doors start->pad via loot/gates/lounge/stairs/roof corridor = 0 closures; stations: 17 of 17 places
  (start, loot, 12 way places, exit, pad, park) reached in the collision and ON ONE nav part (part 7, 401 polygons). So there is no
  nav island and no blocked door between START, loot and the pad: the walk is free (209 m).
- Bots 'stall at g1': NOT a mesh problem. The chain's budget is the cause (GUESS): 40330 units of path (~134 s at 300 u/s) + loot 18 s
  + start delay 10 s + 7 gate waits of up to 30 s each (the game's TriggerActorsDead limit, kl2 0x4afbbd) = up to ~372 s against a 360 s
  round, so a crew that fights every gate cannot reach the exit box in time; in the 1017 logs 'g' is the stage counter (g1 held ~57 s in
  the f06 run). Not changed; levers if wanted: fewer gates, or the exit call by a timer. Checked: heli_call_read PASS,
  kl_fa_club check PASS, kl_fa_civs check 0 FAIL, check_passes PASS. NOT RUN IN THE GAME.

2026-10-18 post-passes (Last Call heli_roof -> build/club_owner_1018/DM05A/heli_roof_post, zip 5f26fd92): kl_fa_dmsettings (fields 66-71, 171 repointed, node 27276), kl_hud all --look deadmen (check PASS), kl_dmlines (2 keys grafted), club check / civs check / check_passes / heli_call_read all PASS. Not run in game.
