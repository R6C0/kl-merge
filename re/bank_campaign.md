# The bank the campaign way (M03_A under F07): the build, stage by stage

**START AT THE SECTION 'DELIVERY' just below (D0 what was built, D1 the folders and every checker, D2 the round as
built and the flags, D3 guesses by cost, D4 the live order, D5 packaging, D6 not done). The stage sections after it
are the record.**

The study: re/campaign_fa.md (summary), re/campaign_fa_bank.md (the place; its section 8 and the notes
'corrected after the critic' weigh more than the first text), re/campaign_fa_tooling.md (the tools). This file is
the working note of the workflow that BUILDS the map: one section per stage, appended by the stage itself and kept
current while it runs (a usage limit can cut a stage off: what is here and on disk is what survives).
Evidence labels as in the study: MEASURED = an output produced here (command named), READ = code or a note,
ASSUMPTION = says why, GUESS = a value nobody measured. Everything is OFFLINE: nothing is installed, the game is
not started. Scratch: C:/kl_scratch/bank/<stage>/; delivered builds: <work>/build/c_bank/.

## DELIVERY (2026-10-11 evening) - start here

Written by the workflow's last stage from the files as they lie; every checker was RE-RUN on the four delivered
folders for this section (D1). The stage sections below (T1 .. Review round 1) are the record of how it came
about; where one of them disagrees with this section, this section is the later one. NOTHING OF THIS MAP HAS EVER
RUN IN THE GAME. Nothing is installed. `<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`,
`<c_bank>` = `<work>/build/c_bank`.

### D0 What was built

1. A second bank map, 'The Vault': Dead Men's CAMPAIGN level M03_A (chapter 3, 'Withdrawal') alone under the Dog Days
   systems level F07, as a Fragile Alliance / Arcade map beside the Fragile Alliance bank M03_FA_A the owner plays.
2. The round: start in the secure yard -> loading dock and vault lobby -> two flights down -> a 48 s beat in the
   vault's ante-room -> seven briefcases in the vault (2.3 M) + four stacks at the tellers (0.3 M) -> up into the
   banking hall -> out of the front entrance -> F07's key-framed van on the front street.
3. 61 enemies in 25 squads, staged in five waves (the campaign's own guards, police and SWAT + three of F07's
   police squads in the hall); seven AI heisters walk the whole way and wait for the vault at a gate of their own.
4. Every door of the way is OPEN AT BUILD TIME (leaves sunk 25 m, their collision cut); only the vault door stands,
   and it is switched off 6 s after the beat whatever its animation does.
5. One authoring module, `tools/kl_fa_bank.py` (2,454 lines; twelve flags for the live questions), on three tool
   changes: the authored layer as a module (`kl_maps.py` / `kl_graft.py` `--author <module>`), the escape van from
   way points (`kl_map_escape.py`), the collision route test (`tools/kl_route.py`).
6. Then the finishing chain other sessions' tools make (wardrobe with the four Payday 2 masks, AI heisters + dynamic
   step, six gun looks, talk, cut shader cache) and a seal step of this module: `<c_bank>/chain.sh`.
7. FOUR FOLDERS are delivered, all built for the F01 test slot (D1). Offline every checker passes on them except the
   two that only repeat one KNOWN finding (16 sound clips that the installed stream file does not hold).
8. The map is complete without them, but SILENT in three things: its music, the vault's ambience, nine guard lines
   (D6). Bringing them needs a larger PC_Def.str = the owner's go-ahead.
9. It is not on the menu: slot packaging and the menu entry are `tools/kl_expansion.py`'s (another session's); the
   facts for it are in D5.
10. What decides whether it plays is the live order D4, safest first; what a wrong guess would cost is D3.

### D1 The delivered folders (`<c_bank>/`, 0.93 GB) and every checker, re-run on them

| folder | what | F01_Main.zip sha1 | archive bytes | folder | chunk table | five large blocks |
|---|---|---|---|---|---|---|
| `bank_vault` | the finished map (enemies, AI heisters, wardrobe, gun looks, talk), sound bank whole | `ac97b4f13ca27fc51c629c162263cdf75dc7d1c2` | 207,977,920 | 246 MB | 65,852 | 159.9 MB |
| `bank_vault_wavslim` | THE SAME ARCHIVE; only `F01_Main.WAV` (13.3 MB, sha1 `fcbd62b8...`; whole: 23.3 MB, `2e1d7827...`) and `F01_Main.WHD` differ | `ac97b4f13ca27fc51c629c162263cdf75dc7d1c2` | 207,977,920 | 236 MB | 65,852 | 149.8 MB |
| `bank_vault_noai` | the same chain on the `--no-ai` build: NO ENEMIES, but the seven AI heisters, wardrobe, gun looks and talk are in | `ecf445f1ceac692fe206f89c650404a581e895e2` | 191,319,066 | 230 MB | 65,083 | 150.1 MB |
| `bank_vault_bare` | the map as `kl_fa_bank.py test` leaves it, before the chain: enemies, beat, loot, van; no AI heisters, no wardrobe, FULL shader cache | `b7e48d31634c9c33cf19a7e8cc315eb65bbcf0af` | 178,157,196 | 217 MB | 65,640 | 149.1 MB |

Yardsticks (`<c_bank>/blocks.txt`, made by `<c_bank>/blocks.py`): chunk-table line of the tools 69,632; five blocks of
stock F07 144.7 MB, of the tab's Retomoto 180.3; stage F measured the tab's Withdrawal at 158.5 (both load live). Members of
`bank_vault`: .prm 72.2, .fxc 9.3, .ANM 21.9, .TEX 245.8 MB, .WAV beside it 23.3.
Beside each finished archive: `KLWardrobe.ini` (16 characters, 12 masks), `KLGuns.ini` (Version 2), `KLTalk.ini`
(Map=M03, StreamBytes=1686681836), `van.json`, `bots.json` / `bots.txt`, `dyn.json` / `dyn.txt` / `dyn_map.png`, NO
`KLJoin.ini`; `checks.txt` + `checks/` = this section's run. `result.json`, `log.txt`, `graft.txt` in the three
finished folders are the BARE build's (20,643 / 20,246 entities): the chain does not rewrite them.
There is NO folder 'no enemies and no AI heisters'; it is one command (D2: `test <out> --keep --no-ai`).

THE RE-RUN (2026-10-11, about 18:05 - 18:30): `sh <c_bank>/checks.sh <folder> C:/kl_scratch/bank/deliver/out/<name>` on each
of the four, one after another; the outputs are also copied into each folder's `checks/` and `checks.txt`. The
archives' sha1 were the same after the run as before it.

| checker | `bank_vault` | `bank_vault_wavslim` | `bank_vault_noai` | `bank_vault_bare` |
|---|---|---|---|---|
| `kl_maps.py preflight` | FAIL (exit 1): 'preflight: CRASH 1, RISK 0, NOTE 77' | the same | FAIL (exit 1): 'preflight: CRASH 1, RISK 0, NOTE 77' | FAIL (exit 1): 'preflight: CRASH 1, RISK 0, NOTE 78' |
| `kl_maps.py audit` | FAIL (exit 1): 'RESULT: FAIL (2 findings that must be 0, 0 known and accepted)' | the same | FAIL (exit 1): 'RESULT: FAIL (3 findings that must be 0, 0 known and accepted)' | FAIL (exit 1): 'RESULT: FAIL (2 findings that must be 0, 0 known and accepted)' |
| `kl_fa.py check` | PASS (exit 0): 'no finding; 21219 nodes, ZSquadScript 32' | the same | PASS (exit 0): 'no finding; 20822 nodes, ZSquadScript 7' | PASS (exit 0): '1 DEGRADED (no bot squads: the chain brings them), 0 CRASH, 0 BROKEN' |
| `kl_impact.py` | PASS (exit 0): 'problems: 0 in 1 levels' | the same | the same | the same |
| `kl_arms.py check` | PASS (exit 0): '0 findings' | the same | the same | the same |
| `kl_chars.py check` | PASS (exit 0): '21219 nodes, 84 people, 65851 chunks: problems: 0' | the same | PASS (exit 0): '20822 nodes, 23 people, 65082 chunks: problems: 0' | PASS (exit 0): '20644 nodes, 77 people, 65639 chunks: problems: 0' |
| `kl_map_guns.py check` | PASS (exit 0): '6 guns with looks; problems: 0' | the same | PASS (exit 0): '6 guns with looks; problems: 0' | does not apply: the folder has no gun looks and no KLTalk.ini (the checker stops for want of its input, exit 1) |
| `kl_map_guns.py sizes` | PASS (exit 0): 'chunk table 65852 entries' | the same | PASS (exit 0): 'chunk table 65083 entries' | PASS (exit 0): 'chunk table 65640 entries' |
| `kl_map_escape.py van-check` | PASS (exit 0): '0 fault(s)' | the same | the same | the same |
| `kl_map_escape.py check` | PASS (exit 0): '0 fault(s)' | the same | the same | the same |
| `kl_fa_bots_dyn.py check` | PASS (exit 0): 'RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 0 NOTE)' | the same | PASS (exit 0): 'RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 0 NOTE)' | not run (the folder has no bot squad) |
| `kl_fa_bank.py bots-check` | PASS (exit 0): '7 squads, 7 with the gate: PASS' | the same | PASS (exit 0): '7 squads, 7 with the gate: PASS' | not run (the folder has no bot squad) |
| `kl_fa_talk.py check` | PASS (exit 0): 'findings: FAIL 0, NOTE 1' | the same | PASS (exit 0): 'findings: FAIL 0, NOTE 1' | does not apply: the folder has no gun looks and no KLTalk.ini (the checker stops for want of its input, exit 1) |
| `kl_fa_bots_dyn.py fake-test` | PASS (exit 0): 'RESULT (fake-test): PASS (grid control 1, parked control 1, lattice 3)' | the same | the same | the same |
| cover lists (`C:/kl_scratch/bank/t1/s/covers.py`) | PASS (exit 0): 'FFCoverList on ROOT\Special!CoverList (ZLIST)' | the same | the same | the same |
| `kl_route.py walk`, the vault door opened | PASS (exit 0): 'RESULT: FREE; the mesh way: 1064 samples, all free' | the same | the same | the same |
| `kl_route.py doors` | PASS (exit 0): 'RESULT: 1 closures in 1 sets, 1 necessary' | the same | the same | the same |
| `kl_route.py walk` as built, without the vault | PASS (exit 0): 'RESULT: FREE; the mesh way: 1008 samples, all free' | the same | the same | the same |
| `kl_fa_bank.py reverify` | PASS (exit 0): 'problems: 0' | the same | the same | the same |
| `kl_fa_bank.py check` | PASS (exit 0): 'PASS' | the same | the same | the same |

THE TWO THAT FAIL, said plainly: `kl_maps.py preflight` and `kl_maps.py audit` FAIL on all four folders. Both only
quote the build's `result.json` ('verify kl_graft.verify reported 1 problems'): 'sound: 10 stream clips are not in the
merged stream file' - on `bank_vault_noai` also 'FA: BROKEN squads no ZSquadScript: no police', which is what that
build is. Inside the audit every checker of its own is at 0. kl_maps.audit has no 'known' entry for a verify finding
and is not this workflow's file; the finding goes only with a rebuild after the stream file holds the clips (D6).
WHOEVER GATES AN INSTALL ON `audit.json` 'bad' OR ON preflight's 'CRASH' MUST READ THOSE LINES AS KNOWN - or decide
that the map waits for the stream file. That is the lead's / the owner's call; it was not made here.

### D2 The round as BUILT (read back from the folders: `python tools/kl_fa_bank.py inventory <folder>`, `check <folder>`)

Floors: yard and dock y 200, vault lobby 240, ante-room and vault -960, banking hall and plaza 800, front street 700.
All of it is on ONE part of the navigation mesh (566 polygons).

| step | what stands in the level | where |
|---|---|---|
| START | 8 START points in two stacks of four beside the dock's roller door; 4 TRAITOR behind them; the 16 player bodies with them (`Heroes!Hero_01` at (150, 200, -4350)) | x 150..450 and 700..1000, y 200, z -4350; traitors z -4000 |
| loot marker / stage 1 | marker in the vault's middle (400, -800, -13000); ENTERS plane 1 m inside the dock door | (560, 380, -4800) half (250, 230, 50) |
| doors, open from the load | 11 leaves of 5 sets sunk 2,500 with 0 collision placements: dock roller door (560, -, -4706), glass door 1 (+-125, -, -6808), glass door 2 (274 / 525, -, -7602), airlock (1000 / 1215, -, -6895 / -7105), hall / foyer (195 / 405, -, -5801) | `LEAVES` |
| wave 'start' + 'down' | 13 guards of dock and vault lobby + 3 pairs on the way down come into the world 10 s after the round-start event (= about 1.4 s after GO) | their campaign places |
| the way down | vault lobby (394, 241, -7129) -> glass door 2 -> upper flight (-70, -158, -9200) -> cross corridor (-75, -558, -10600) -> ante-room (400, -959, -11800) | `ROUTE_IN` |
| THE BEAT BOX | F07's `Gameplay!010_FirstFight!tb_LEFT_TheySpotYou`, criminals only, fires ONCE (field 15 = 0) | (460, -714, -12152) half (550, 254, 556) |
| ... at once | six rod timers (2, 10, 18, 26, 34, 42 s: each pulls one locking rod, with its sound); 14 police come into the world BEHIND THE AIRLOCK and walk down; the music's rise; the beat timer 48 s | police: x 1415..1585, y 240 / 420, z -6700..-5380 (`BEAT_MEN`) |
| ... 48 s | the vault door gets 'Activate'; the 7 hidden cases appear; alarm sound and the 11 lamps' glow; music to the way-out set; 5 squads hunt into the vault (search box (427, -733, -12986)); 3 F07 police squads (8 men) take the banking hall; door timer | vault door body at (571, -760, -12509) |
| ... 6 s more | the door's body is switched OFF (DeactivateGeom); the blast as a harmless show (3 Explode boxes with reach 1 / 1, a camera shake, the blast sound); the intact vault is swapped for the blown one (57 bodies come, 148 go) | - |
| LOOT, vault | 6 x 300,000 at the deposit-box walls + 500,000 in the middle; Dead Men's briefcase model x 1.25; takable in the intact AND the blown vault | (200 / 300 / 600, -960, -13310), (110, -960, -13230 / -13030 / -12830), (430, -960, -12950) |
| LOOT, tellers | 4 x 75,000, F07's money bags on the counters' public edge, shown from the start | (-765, 899, -7202 / -8002), (1367, 899, -7206 / -8006) |
| the way out | ante-room -> vault lobby -> airlock (1100, 240, -7000) -> stairs (1538, 355, -5822) -> foyer (309, 803, -5624) -> hall (377, 801, -8423) -> front entrance (300, 800, -9350; no door, a 2 m gap) -> plaza (281, 812, -9700) | `ROUTE_OUT` |
| the foyer box | F07's `Specials!LevelSpeak!TriggerBox`: the line 'Get out on the street! straight ahead!' and the plaza's 7 squads (20 men, two SWAT fours) | (300, 930, -5650) half (300, 180, 150) |
| stage 2 | EXITS plane at the front entrance | (303, 974, -9407) half (300, 200, 100) |
| the exit box (calls the van) | `Gameplay!EscapeSetup!otrExitLevel`: plaza and street; holds the van's stop and the boarding place, not the hall | (300, 800, -10550) half (1500, 300, 1150) |
| escape marker | beside the van's lane: 425 from the drive, 358 from the boarding place | (316, 890, -11070), over the station (316, 702, -11070) |
| THE VAN | F07's first van only. Waits at the west end of the square (IN SIGHT from the plaza, 41 m) -> 48 m in 7.2 s -> stops, nose east-north-east -> 71 m in 8.48 s east, passing the east level bound 26 - 30 m after the stop as stock vans do | waits (-3248, 702, -11859); stops (949, 702, -11104); ends (8000, 702, -11172); boarding place at the stop (636, 702, -11231); camera eye (-712, 1030, -11800) |
| police who come back | 8 bodies, 7 AFTER_DEATH points on the front street | x -1750..-1437 and 2016..2178, y 705, z -9900 |
| AI heisters (finished folders) | 7 squads `Gameplay!merc_bot_squad!Squad#02..#08`, 16 stations along the same way; at the ante-room round (417, -960, -11871) each waits 56 s (`020_Timer_vault_opens`) before the vault; they are taken aboard from an AllyEscapeBox at (316, 700, -11070) | `bots.txt`, `dyn.txt` in the folder |
| texts | start windows `AllLevels/Interface/Online/GameStart/M03A_FA_Start` / `_Team_B_Start` / `_UCC_Start`; title and briefing under Dead Men's unused keys `AllLevels/Menu/Online/Scenarios/TitleDL01` / `BriefingDL01`; 8 stock briefing / reminder lines | the level's .LOC |

People: 61 soldiers (9,450 hit points, stock rows by weapon class: 23 x eCustom 50 / 175, 15 x 50 / 100, 15 x 75 / 175
+ F07's 8) + 7 AI heisters = 68 ZFFActor in 32 squads + 16 player bodies (the largest build that ran live: 99 / 55).

THE FLAGS of `python tools/kl_fa_bank.py test <out> [--keep] ...` (each is a module name; the delivered folders are
all DEFAULTS except `--no-ai` on `bank_vault_noai`):

| flag | module name, default | what the flag does |
|---|---|---|
| `--doors-animate` | `DOORS_ANIMATE = False` | the 11 leaves stay and get 'Activate' at the round start (glass leaves with LAST 50); default: open at build time |
| `--vault-open` | `VAULT_OPEN = False` | the vault door is sunk at build time too |
| `--vault-stays` | `VAULT_DOOR_GOES = True` | the vault door's body is NOT switched off after the swing |
| `--loot-shown` | `GATE_VAULT = True` | the vault's cases lie there from the load |
| `--loot-bags` | `CASE = 'dm'` | F07's money bags instead of the briefcase model |
| `--beat S` | `BEAT = 48.0` | seconds from the ante-room box to the vault door (the rods squeeze under it) |
| `--no-ai` | `NO_AI = False` | no enemy squad at all; beat, loot, blast, van as with them |
| `--alarm-lights` | `ALARM_LIGHTS = False` | the 22 alarm lights keep their `LightToggle` (a controller no stock Dog Days level runs); default: taken off, 22 lights + 8 slave spots hidden |
| `--music-layer4` | `MUSIC_LAYER4 = False` | the nine `eLayer4` fades stay; NEEDED once the music clips are in the stream file |
| `--blast-real` | `VAULT_BLAST = 'show'` | the campaign's reach (1300 / 1000, 800 / 800) and damage field |
| `--no-blast` | (`VAULT_BLAST = None`) | no blast, the vault stays intact |
| `--dead-men-rows` | `STOCK_ROWS = True` | the soldiers keep Dead Men's skill / health rows |
| `--plan FILE` | - | the van's plan from a kept `van.json` (60 s less; refused if `ROAD` changed) |

Rebuild any variant (about 8 min; `chain.sh` deletes its intermediate folders as it goes; ONE build at a time):
```
python tools/kl_fa_bank.py test <out> --keep [flags] --plan "<c_bank>/bank_vault_bare/van.json"     -> "<out>/F07+M03_A campaign"  (the bare map; 'RESULT: PASS')
sh "<c_bank>/chain.sh" "<out>/F07+M03_A campaign" <work dir> <log dir>                              -> <work dir>/fin and <work dir>/fin_wav  ('CHAIN DONE')
sh "<c_bank>/checks.sh" <folder> <out dir>                                                          -> <out dir>/summary.txt
```
`python tools/kl_maps.py one ... --author kl_fa_bank` alone does NOT build this map (it stops in prepare_host and says
why: the van's plan). Any tool that adds entities after the chain needs `python tools/kl_fa_bank.py seal <folder>` again
(`check` / `reverify` say so).

### D3 Everything that is GUESS or ASSUMED, sorted by what a wrong value would cost

Nothing below was seen in the game. 'Way out' = what to build or switch if it is wrong.

**A. Wrong = the level does not load, or faults (cost: no map until fixed)**

| # | what is assumed | evidence | way out |
|---|---|---|---|
| A1 | A Dead Men CAMPAIGN level grafted by the `--campaign` pre-pass loads at all: 28 rooms, 20,643 entities, its own `Special!CoverList` (118 cover boxes) kept. No campaign graft but Retomoto has ever loaded | offline: verify, reverify 'problems: 0', exactly 1 FFCoverList | L0 is this test; triage |
| A2 | 11 leaves sunk 2,500 under their rooms do nothing to the rooms' draw lists or the room fix-up (study G1.6) | read, not seen | `--doors-animate` (then A7) |
| A3 | The CUT shader cache (9.3 MB, in the three finished folders) loads and shows every material. It has NEVER loaded live on any map | offline: 126 effects asked for by 1,277 materials, 0 in no entry | `bank_vault_bare` has the full cache (L0); a full-cache finished folder = `chain.sh` without its step 6 (five blocks 168.4 MB) |
| A4 | 229 room list entries parked on the free REF id (seal) resolve to nothing at load | the same form loaded and played on Late Night Opening (80 entries) | - |
| A5 | The one FakeTarget (the van's, at its waiting place) gets a vision record at load, at the stop and at the end of the drive (the 0x686a66 rule) | kl2's arithmetic re-done offline: inside; fake-test PASS | - |
| A6 | 22 lights and 8 slave spots HIDDEN in the file (ZGEOM[3] = 1, flag 0x400) with their `LightToggle` taken off load cleanly | the level's own fire lights have that form | - |
| A7 | (flags only) `LightToggle` x22 and Dead Men door animations run in Dog Days: `--alarm-lights`, `--doors-animate` | none: first-timers | they are OFF by default for this reason |
| A8 | Chunk table 65,852 of 69,632, five blocks 159.9 MB, 68 actors / 32 squads are inside what loads | Retomoto on the tab: 65,331 entries, 180.3 MB, 99 / 55 | `bank_vault_wavslim` (149.8 MB) |
| A9 | The slimmed sound bank of `bank_vault_wavslim` (151 clips dropped) loads and misses nothing that plays | kl_snd.verify 0; never loaded live | `bank_vault` |
| A10 | A hidden rigid body / the campaign's two postfilter boxes in the blast's lists do no harm when shown at run time under F07's palette | not known | `--no-blast` |

**B. Wrong = the round cannot be finished, or the crew is stuck (cost: a rebuild with a flag)**

| # | what is assumed | evidence | way out |
|---|---|---|---|
| B1 | A squad with `ZSquadScript` field 3 = 0 is not in the world until one of its routs is named (the whole staging) | seen live on Retomoto | `--no-ai` build to play meanwhile |
| B2 | The beat box (ECPS_FA_MERCONLY) is tripped by a Fragile Alliance HUMAN and by an AI heister; TriggerBox field 15 = 0 means 'once' | field 15: a census of 226 stock boxes, not read in kl2.exe; bots tripping such a box: 'measured in effect' on Retomoto | if the beat never starts there is no loot and the vault stays shut: `--vault-open --loot-shown` |
| B3 | A body switched off by DeactivateGeom stops colliding (the vault door's guarantee) | stock F07 removes its BlockVisionPlane so | `--vault-open` |
| B4 | ActivateGeom makes the 7 hidden cases appear AND takable | stock form | `--loot-shown` |
| B5 | The blast's swap: ActivateGeom brings the blown vault's collision, DeactivateGeom takes the intact one's. Route and loot are tested in both states and with both at once; only 'the intact floor goes and the blown one does not come' hurts | not seen | `--no-blast` |
| B6 | A player can stand at the START points in the yard and a body 60 wide walks every leg (kl_route's walker: step 45 up / 60 down, body 60 x 60 - never read in kl2.exe); 'FREE' is the only evidence that the way is open | offline walk: 1,064 samples free, 1 closure = the vault door | L1 walks it |
| B7 | The exit box calls the van; a key-framed van moves with its entity; a human aboard is not ended by the level bound the drive passes 26 - 30 m after the stop | every one of 15 stock vans passes a bound; bots did it live on the tab's bank; no human seen | shorten `ROAD`'s leave leg (x 4600 passes MIN_OUT by arithmetic, not run) |
| B8 | The 14 police of the beat WALK from behind the airlock through the lobby and down (their own defend routs, one mesh part) | measured: on the mesh, on free floor | `BEAT_MEN = None` (the campaign's places; check then fails BEAT_CLEAR) |
| B9 | The AI heisters' vault gate is a CLOCK (56 s = beat + door delay + 2, read off the level): a started squad step is not started again. If no criminal trips the beat box while they wait, they walk on to a shut door, their loot wait runs out and they leave without the vault's money | Retomoto's bots waited on timers live | - |
| B10 | AI heisters are taken aboard from the AllyEscapeBox beside the stop when the van stands (kl2 0x907a50) | seen live on the tab's maps | the hook's [Bots] BoardAll |
| B11 | Three men moved 15 inside the mesh (`snap_men`), 7 rout places off the START's mesh part (the campaign's own: five hunt search boxes, one defend point 7 beside the mesh) | - | - |

**C. Wrong = it looks, sounds or plays badly (cost: a value to turn)**

- THE FIRST CRIMINAL in the ante-room starts the beat - with AI heisters that is usually a bot (the point man starts at
  +0 s and has about 80 m to walk): the rods, the 14 police and the 48 s can begin while the human still fights
  upstairs. No field is known that tells a human from a bot. Whether that is wanted is the owner's to say.
- The vault door's 'Activate' swing: if it plays, the door vanishes 3.6 s after it stands open (ugly): `--vault-stays`
  once the swing has been SEEN to let people in. If it does not play, the door disappears at the blast.
- The blast 'show' is harmless (ASSUMED: Explode fields 0 / 1 are its reach, field 4 its damage; box #01 stands in the
  ante-room among the crew). `--blast-real` = the campaign's values (30 in the damage field: a light hit by stock rows).
- Hidden alarm lights do not shine (if they do, eleven red lamps are lit from the load). The lamps' glow animation
  still gets 'Activate'.
- STRENGTH: 61 soldiers with 9,450 hit points = 1.5 times the hardest stock level, in five waves. Knobs:
  `--dead-men-rows`, `kl_arms.ROWS`, the hook's [Balance].
- The 13 'start' guards come into the world in the dock 10 - 15 m behind the open roller door about 1.4 s after GO
  (`SQUADS_AT` 10 s rests on two clock readings of 8.4 - 8.8 s between the round-start event and GO).
- Whether a human in the vault lobby SEES the 14 police appear in the corridor behind the airlock: no sight line computed.
- THE VAN WAITS IN SIGHT (41 m from the plaza); a longer in-road does not hide it (measured). It would take a blind.
- The leave leg carried on east from (3958, 713, -11173) to x 8600: the collision floor is measured, what is DRAWN
  out there was never looked at. The escape camera's eye is `cam_spot`'s choice and does not see the end of the drive.
- A player who waits where the van's rear doors WILL be stands 80 from the arriving van's line (its kill box).
- GUESS, placed and only measured 'on the mesh, on free floor, in no bound box': every spawn row, the team / Undercover
  Cop sets and their cameras and stage boxes (nothing of those modes was thought through), the two back level bounds,
  the exit and escape-area boxes' extents, `ESC_AT`, the police rows, the hall's eight men, `BEAT_MEN`.
- GUESS: loot places, turns and values (2.6 M); `CASE_SCALE` 1.25; F07's bag as the tellers' prop. NO PICTURE of the
  briefcases, the vault or anything else of the map was ever rendered or looked at.
- GUESS: `BEAT` 48, `DOOR_GONE` 6, rods 2 s + 8 s steps, `MUSIC_AT` 1, `GATE_AT` / `GATE_REACH` / `GATE_MORE`, the bots'
  30 s loot wait; 20 of the bots' 56 hold places have no cover box in reach (yard, stairs, plaza).
- GUESS: every wording (start windows, 'The Vault', the briefing) and the choice of stock briefing / reminder / exit
  lines; the other eight languages show the English text.
- ASSUMPTION (only once the music clips exist): a second PlayMusic does not stop the first, hence `--music-layer4`.
- The gun options (`--start=1 --set=1`) are copied from the tab's maps; `tools/kl_chars.py` ran with another session's
  uncommitted change in the working tree.

### D4 THE LIVE ORDER, for the session that holds the game (safest first)

Before any of it: the owner's word that they are away (a scripted run takes keyboard and mouse); `kl2.exe` closed;
`python debug/slot.py status F01` and the hook pair noted so that everything is put back afterwards. Never Quit
inside a session on this map with an unguarded hook. The folders are built for the F01 TEST SLOT:
`python debug/slot.py put "<c_bank>/<folder>" F01` copies the archive, the files beside it and the three side inis.
Scripted run: `python tools/kl_autotest.py 1200 --hook <TEST hook folder> --ini <run ini> --tag <tag> --shots ...`.
In every run's ini: `[Load] NudgeMs=1000`; `[KLHook] StallMs=30000`, `StallEndMs=0`; `[Expansion]` so that an open of
F01 is NOT answered from `Maps\DM01` (`Enable=0`, or `Page=1`); `[Vis] Log=1` on the TEST hook.
FAIL in every run: a `FATAL` line / a `KLHook_N.dmp` / kl_autotest's `RESULT: crash ...`, `RESULT: assert ...` or
`RESULT: hung`; a 'stall watch:' line inside a level; then `python debug/triage.py --keep`. Addresses that would name a
cause here: 0x686a66 (FakeTarget outside the vision space), 0x8e5bbd (a large block refused), 0x719884 / 0x48e910
(room index / gates), 0x8adbba (empty pool), 0x46fe87 / 0x8add12 (unregistered type), 0x796ff4 (a relay naming itself),
kl2+0x207280 (chunk table).

| run | folder | how, ini keys | look at | PASS / FAIL in the log |
|---|---|---|---|---|
| L0 | `bank_vault_bare` | DIRECT BOOT: the launch options kl_autotest's docstring names (`-o DefaultScene=Locations/F01/F01_Main.gms -o AutoExit=120`; if they are not set any more, do NOT change them - load it from the stock Arcade page as L1). `[Bots] Enable=0`, `[Character] Enable=0`. This folder has the FULL shader cache and no side ini | does it load; the yard, lit and textured, the hero beside the dock door at (150, 200, -4350); the roller doorway OPEN; no red lamp lit; walk (scripted) dock -> vault lobby -> glass doors -> down: every door set but the vault's is a hole | PASS: `RESULT: clean exit after N s`, klauto 'level loaded and running', with `[Vis] Log=1` the line 'vis: 30 s after the grid appeared: record 0xff has never held 'no cell'' (FAIL: 'A TARGET OUTSIDE THE GRID WRITES THERE EVERY FRAME'). This run answers A1, A2, A4, A5, A6. FAIL: any fault during the load (the percentage it stops at) |
| L1 | `bank_vault_noai` | from the menu, stock Arcade page -> Subway (the F01 slot). `[Bots] Enable=1`, `Log=1`; `[Character] Enable=1`; `[Crew] Random=0` for the first run. NO ENEMIES; the seven AI heisters ARE in this folder | start window text; 'Heist starts in ...' in the yard; walk to the ante-room: do six rods pull one by one over 48 s, does the door swing, do seven briefcases appear, alarm sound, does the door vanish 6 s later and the vault 'blow' without hurting; take a case; up through the airlock; the line in the foyer; out of the front; DOES THE VAN COME when the plaza is entered, 'Get in' at the rear doors, the fixed camera, the score page | 'character: level ... has a wardrobe (version 2): 16 characters, 12 masks'; session state 0x19 (GO); 'bots: Arcade round object ...: ... 7 AI'; 'bots: record N (bot): heist stage 0 -> 1' within a minute, later '-> 2', '-> 3'; the `bots:` line's 'van 3' (waits) then 5 -> 7; 'record N (bot): aboard'. FAIL: bots stay at stage 0 (the dock's ENTERS plane), no case appears after 48 s (B2 / B4), nobody can enter the vault 54 s after the box (B3), no van (B7). This run also first loads the CUT shader cache (A3): anything drawn black or missing that L0 showed = the cache |
| L2 | `bank_vault` | as L1; then `[Crew] Random=1`, `[Talk] Enable=1` | 13 guards in the dock just after GO and not before; nobody else in the world until the ante-room; 14 police arriving ON FOOT from the airlock after the box; hunts and the hall's 8 at the beat's end; 20 on the plaza at the foyer box; police bodies for returning players on the street; how hard it is; do the AI heisters live to the van | the same lines; `bots:` lines 'lost ...' show where the crew dies; a crash 0x686a66 would be a FakeTarget (fake-test said no). Play it twice in one process (the second load is the memory test) |
| L3 | `bank_vault_wavslim` | only `F01_Main.WAV` + `F01_Main.WHD` differ from L2's slot: put the folder, same ini | by ear: gunfire, footsteps, doors, alarm, the heisters' and guards' lines as in L2 | no new line; 'memory: at the level's largest block' line shows 10 MB less asked |
| L4 | a NEW build: `test <out> --keep --doors-animate --vault-stays --plan ...` then `chain.sh` (D2) | as L2 | at the round start the roller door rolls up, the glass doors swing to 109 degrees and STAY, the airlock and foyer leaves slide; the vault door stays swung open. If a leaf stays shut the crew is locked in the yard: that is the answer, not a fault | no fault at the load = Dead Men's door KEYS play or are ignored; the route's verdict is by eye. Until this passes the default (open at build time) stays |
| L5 | a NEW build: `test <out> --keep --alarm-lights ...` then `chain.sh` | as L2 | lobby lit white until the alarm; at the beat's end eleven red lamps spin and the white rows go off | a fault at LOAD here = `LightToggle` (22 of them, a controller no stock level runs): the default stays off for good |

After L2: `--vault-stays` if the swing was seen to work (C); `--blast-real`, `--beat S`, `--dead-men-rows` are taste.
`--music-layer4` belongs to the build that follows the stream file (D6), not to a test of its own.

### D5 Packaging facts for `tools/kl_expansion.py` (that file was NOT edited; it is another session's)

- **id**: `DM03A` is PROPOSED (the table's ids are DM01 DM02 DM03 DM06 DM09; `DM03` is the Fragile Alliance bank).
- **slot**: `F07` = entry 6 of page 2, the ONE entry left (`ORDER` = 1 2 3 4 6 7 5 8 9; F05 F08 F09 are the paid DLC
  slots; the five maps hold F01 F02 F03 F04 F06). `[Redirect.2] F07=DM03A`, `[Page.2] F07=The Vault`. F07 is also the
  systems level, but only as a build input: the stock F07 files are not touched, the hook answers the opens from
  `Maps\DM03A`. NOT TRIED: no map has been loaded under the slot name F07 through the redirect.
- **title**: 'The Vault' (`kl_fa_bank.TITLE`). **briefing**: the text of `kl_fa_bank.TEXTS` under
  `AllLevels/Menu/Online/Scenarios/BriefingDL01` (Dead Men's own unused 'Bank Vault' slot); both are in the level's
  .LOC, in all 8 languages as English. The wording is a GUESS.
- **picture**: `LevelPicture_M03A` - the entity EXISTS in Dead Men's frontend scene (read for this section with
  `kl_expansion.front_scene('dm')`: FA01 FA02 FA03 FA06, M01, M02, M03A, M03B, M05 ... M14); it is the campaign
  chapter's picture. `kl_expansion.pictures()` has not been run on it.
- **sources**: `['M03_A']` under systems `F07`, with kl_maps' `campaign=True`.
- **build**: neither 'one' nor 'chain'. The map is made by `kl_fa_bank.build()` + `finish()` (the van's plan and
  `kl_map_escape.van_layer` round kl_maps.one, `author='kl_fa_bank'`) and then `<c_bank>/chain.sh`. For the tree it is
  a FINISHED FOLDER: `--prebuilt DM03A=<c_bank>/bank_vault` (adopt() renames members and files F01 -> F07, bytes
  untouched). `result.json` is in the folder (adopt() wants it).
- **'author' module**: `kl_fa_bank`. **known**: `('stream clips are not in the merged stream file',)`.
- **side files** (all in kl_expansion.SIDE): `KLWardrobe.ini`, `KLGuns.ini`, `KLTalk.ini`; NO `KLJoin.ini`
  (`join` unset). `van.json`, `bots.json`, `dyn.json` and the notes go to `BuildInfo\DM03A` by adopt()'s rule; the
  folder's `checks/` is a subfolder and is skipped. Nothing inside the side files names the slot (`KLTalk.ini` has
  `Map=M03`, kl_fa_talk's script key).
- **live**: nothing. `bones_live`: the build goes through kl_graft's defaults (the skeleton step on), never run.
- **the hook's per-map behaviour** ([Bots], [Crew], [Talk]) is gated to non-stock levels by the hook, as for the
  other adopted maps; nothing of klhook/ was touched or needed.

### D6 What was NOT done, and why

- **Music, the vault's ambience, nine guard lines: SILENT.** They are wired (PlayMusic objects, fades, the alarm and
  blast sounds play from the level's own bank), but 16 clips have no record in the built .WHD because the installed
  `PC_Def.str` does not hold them, and a larger stream file is the owner's go-ahead (no stream file was built or
  installed). The 16: music `Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav`, `BO_Sus_Layer2_Bass_LOOP.wav`,
  `BO_Sus_Layer3_Intense_LOOP.wav`, `BO_Sus_Layer4_Basic_LOOP.wav` (the break-in set), `M03_Bustout_ActionV34.wav`,
  `M03_Bustout_IntenseClimax_Loop.wav` (the way-out set); ambience `SFX/Ambiences/M03_A/Inside/Ambience_Inside_Vault_Deeper.wav`;
  guard lines `Dialog/M02/Dialogue/Situation/M02_GuardsShout/M02_GuardsShout_020_Guard.wav`, `_025_`, `_050_`, `_060_`,
  `Dialog/M03/Dialogue/M03a_OneLiners/M03_GuardAlarm/M03_GuardAlarm_010_Guard02.wav`,
  `Dialog/M03/Dialogue/M03a_OneLiners/M03_Spotted/M03_Spotted_040_Guard.wav`,
  `Dialog/M03/Dialogue/Situation/M03_Enter/M03_Enter_011_Guard.wav`,
  `Dialog/M08/Dialogue/Situations/M08_Cantina/M08_Cantina_010_Guard01.wav`, `_030_Guard01.wav`.
  The kept guards' other 69 one-liners DO stream from the installed file. After the stream file: rebuild with
  `--music-layer4`, run the chain; preflight / audit then lose their one finding.
- **preflight / audit are not green** (D1) and no 'known' entry was added to kl_maps.audit (a shared file).
- **Nothing ran in the game**: the owner was playing during every stage.
- **No picture** of the map was rendered (tools/kl_view.py renders models; nobody looked).
- **The menu entry, the slot packaging, the map picture**: kl_expansion's (D5).
- **'Out of sight' for the waiting van**: not met; it needs a blind (a parked truck, a kept campaign car) - not tried.
- **The squads' retreat routs** (`40_DefendBehaviour_Moveback` as a retreat, the hall squads' `40_RunToEscape`), F07's
  police ring at the van's call, any 'wiped out' chain (ZSquadScript field 8): not wired.
- **F07's vans 2 and 3**: not in the level (a van parked under the map is the 0x686a66 crash).
- **The vault guards as a loot gate**: the loot is gated on the beat's timer only.
- **The vault's fire as damage** (`FireDamageBox`): not kept; the fire is a picture.
- **kl_fa_cover**: left out, measured (9 new boxes, not one hold more for the bots).
- **A Kane countdown to the vault door** (kl_fa_talk notes 'the level has a blast timer and KLTalk.ini no countdown'):
  that is a `SCRIPTS['M03']` entry in another session's file.
- **kl_map_ai plan for M03_A**: none on purpose (its STRENGTH floors would lift 19 riflemen to accuracy 99).
- **Team mode / Undercover Cop**: spawn sets are placed and on the mesh; nothing else was thought through.
- **In shared files, left for their owners**: kl_graft.verify has no line for ZERO cover lists; kl_maps.one's
  `stream_clips_missing` is a reconstruction by name and over-reports (85 for 16); the tab's maps carry the unsealed
  'room list entries -> Squad#02' form (`kl_fa_bank.py seal` works on any built folder); kl_fa_author.FINISH is still
  not called by kl_graft / kl_maps; M07_A, M12_A, M13_B now keep their cover list through the pre-pass, nobody built them.
- **Deviations from the order the lead gave**, both kept: the dynamic bot step runs LAST in the chain (its check holds
  the four large blocks against its own build), and the shader cache is cut twice (the wardrobe merges the whole
  cache back).

(end of DELIVERY)

## Stage T1 - the cover list survives the campaign pre-pass; the authored layer is a MODULE (tools/kl_maps.py, tools/kl_graft.py)

STATE: DONE (2026-10-11 12:50). Checks (a), (b), (c) pass; every archive is deleted. Kept in C:/kl_scratch/bank/t1/
(1 MB): the logs, the four manifests, result.json / log.txt / graft.txt of every build, the scripts in s/.
Committed as 2b092c0 (tools/kl_maps.py, tools/kl_graft.py, this section).

### T1.0 Regression baseline, made BEFORE any change (tree at 40a8a7a + the two other sessions' uncommitted files)

- Command: `python tools/kl_fa_loot.py test "C:/kl_scratch/bank/t1/before" --no-wardrobe` (READ tools/kl_fa_loot.py
  `test`: kl_fa_blast.test = kl_maps.chain(F07, M09_B, M09_A, campaign, author=True) with the street, blast and loot
  hooks and the voices on, then `lighten trim,slim`; the wardrobe is a separate later step and is left out).
  7 minutes. MEASURED last lines of before.log: 'level: 25735 entities, 22 rooms, 313 MB', 'kl_graft.verify: 1
  problems, 0 of them not known', 'RESULT: PASS (C:/kl_scratch/bank/t1/before/light)', exit 0.
- Recorded: `python C:/kl_scratch/bank/t1/s/manifest.py make before before.manifest.json` -> 68 files, 3 archives
  (first step chain/F07+M09_B/R09_Main.zip, the dressed level 'R09+M09_A (R09 = F07+M09_B)'/F01_Main.zip, the
  lightened light/F01_Main.zip), 91 members with name, size and CRC, and size + sha1 of every file beside them.
  The hashes of tools/*.py, re/*.json and klhook/KLJoin.retomoto.ini at that moment: tools_before.sha1.

### T1.1 What was changed (two files, nothing else)

**tools/kl_maps.py**
- `PASSIVE` gains `'FFCoverList'` (with the comment that says why and for which levels).
- `HERO_AT` gains `'M03_A': {'Special!JumpPoints!Jump#060': 'Heroes!Hero_01'}` (T1.3).
- `one()`: the campaign pre-pass asks `kl_graft.author_module(opt.get('author')).campaign_names(m_name)` instead of
  importing kl_fa_author by name; `result.json`'s `options.author` is the module's NAME when a module object was
  handed in (True and a name are written as they are, so Retomoto's result.json is unchanged).
- `main()`: `--author [module]` for `one` and `chain` through `kl_graft.author_arg` (was: a bare flag).
- docstring: the option under "options of 'one'", the cover list in the CAMPAIGN PRE-PASS paragraph.
  `chain()` itself needed no change: it hands `**opt` to both steps.

**tools/kl_graft.py**
- new, in front of `build()`: `AUTHOR = 'kl_fa_author'`, `AUTHOR_NAMES` (the nine names), `author_module(author)`
  (None / False -> None; True -> kl_fa_author; a str -> `importlib.import_module`; a module -> itself; a module
  that lacks one of the nine names is a ValueError BEFORE anything is built) and `author_arg(a)` (takes
  `--author [module]` out of an argument list: False / True / the name; the name is the argument directly behind
  the option when it does not start with `--`).
- `build()`: `au = author_module(author)` instead of `import kl_fa_author as au`; `au.DROP` and
  `au.layer_names(Jn)` are wrapped in `tuple()` (a module may hand a list); the five call sites are otherwise as
  they were and still read every name off the module at the moment of use (kl_fa_street.hook / kl_fa_blast.hook
  replace kl_fa_author's prepare_host / strip / wire / KEEP from outside; KEEP is a module `__getattr__` there).
- `__main__`: `author = author_arg(a)`.
- docstrings: the option line at the top; **the interface is written down in `build()`'s docstring, under
  `author:`** - the nine names and what each must be.
- NOT changed, on purpose: `verify()` still reports only MORE than one cover list (the study's item A also asks
  for a line for ZERO: it would add a problem to every build without a list and is outside this stage's two
  changes - see T1.6). kl_fa_author.py is untouched (no export was needed).

Every other place that names kl_fa_author (MEASURED `grep -n kl_fa_author tools/*.py`): kl_expansion.py (its
`join_ini` and `build_map(..., author=True)`: Retomoto's own, still valid), kl_fa_blast / kl_fa_street / kl_fa_loot
/ kl_fa_van / kl_fa_bots_rt / kl_map_escape / kl_fa_talk (Retomoto's layer and its measurements, other sessions'
files): none of them is 'the layer handed to the graft'. In kl_graft.py and kl_maps.py no import of kl_fa_author is
left; the name stands only in `AUTHOR` and in comments / the run log.

### T1.2 The cover list: what the one word changes, on all 20 Dead Men levels (no build)

MEASURED `python C:/kl_scratch/bank/t1/s/passive.py` (campaign_drop() with and without the entry, in memory; output
C:/kl_scratch/bank/t1/passive.txt). Every level has exactly ONE FFCoverList (a single ZLIST node). 15 levels have
it as the top-level `CoverList` (systems side by kl_prpjoin.sides: never a candidate of the pre-pass) - among them
M09_A and M09_B, so Retomoto's pre-pass is untouched (M09_A 259 -> 259 dropped, M09_B 256 -> 256). Five keep it in a
campaign subtree and lost it; with the entry exactly that one subtree stays and nothing else moves:

| level | its list | dropped subtrees before -> after |
|---|---|---|
| M03_A | `Special!CoverList` | 489 -> 488 |
| M06_A | `Specials!CoverPoints!CoverControl` | 238 -> 237 |
| M07_A | `Special!CoverPoints!CoverControl` | 126 -> 125 |
| M12_A | `Specials!CoverPoints!CoverControl` | 240 -> 239 |
| M13_B | `Specials!CoverPoints!CoverControl` | 220 -> 219 |

(The study named M03_A and M06_A only; M07_A, M12_A and M13_B are the same case.) For a layer that keeps F07's
`Specials!`: F07's own list is `Specials!CoverPoints!CoverControl` - the layer must DROP it (kl_fa_author.DROP =
`('Specials!CoverPoints!*',)`), or the level has two and verify() says so. On M06_A / M12_A / M13_B the map's
list even has the same top-level NAME as F07's.

### T1.3 HERO_AT for M03_A: a real marker in the secure yard

- MEASURED `awk` over the study's node dump G:/kl_scratch/cfa_bank/M03_A.tsv (every node with class,
  controllers, world place): inside the yard (x -450..2450, z -4700..-700, y 150..320) the level has TWO
  top-level nodes that are not geometry: `Special!JumpPoints!Jump#060` (ZSTDOBJ + JumpPoint) at (-313, 205, -4398)
  and the path blocker of the roller door (557, 234, -4682). The checkpoint markers (`Special!Checkpointsave!
  CP_0n_PosP1/2`, what HERO_AT uses on M09) are elsewhere: CP_01 back streets, CP_02 car-park roof, CP_03 vault
  lobby (394, 241, -7129) / hall, CP_03b / CP_04 vault, CP_05 hall. `Jump#131` (266, 202, -5002) is 5 m INSIDE the
  dock, behind the roller door, not in the yard.
- So: `Special!JumpPoints!Jump#060` -> `Heroes!Hero_01`. It is the developers' own jump point behind the rappel
  (re/campaign_fa_bank.md 1.3 beat 4). MEASURED `python G:/kl_scratch/cfa_bank/stations.py M03_A
  "Jump#060:-313:205:-4398" "study start:300:200:-4350"`: 'polygon 367 part 0 (566 polygons) off the mesh by 0
  height off -4'; the study's START place is polygon 368 of the same part, 6 m east (12 m over polygon centres).
- Its rotation (MEASURED `python C:/kl_scratch/bank/t1/s/marker.py M03_A "Special!JumpPoints!Jump#060"`): a turn
  about Y, ZGEOM[1] = [0.724 0 0.690, 0 1 0, 0.690 0 -0.724]. Read as a player group (local -Z, kl_fa_author.look9)
  it FACES (-0.72, -0.69): into the yard's south-west corner, away from the dock door. Cosmetic for a bare boot.
- kl_maps.one's `Story` class retypes the marker to a model-less ZGROUP named Heroes!Hero_01 and takes its
  controllers off (the JumpPoint goes), exactly as for M09's markers; kl_graft then puts F07's group there.
- Only ONE group is placed (the yard has one marker): Hero_02..08 and the Henchmen stay at F07's coordinates, as
  14 of the 16 do on M09. A direct boot starts at Hero_01. The authored bank (kl_fa_bank.prepare_host) places all
  sixteen itself and is built WITHOUT --heroes, as kl_fa_author.test is (heroes=False).
- ASSUMPTION (as for M09's entries): a player can stand there. Not seen in Dog Days. The yard is closed by the
  roller door: a bare boot stands locked in until that door is opened (re/campaign_fa.md 3.3 step 3).

### T1.4 Checks (a) and (c): Retomoto is the same archive, by default and through a module's name

Tool hashes: `sha1sum tools/*.py re/*.json klhook/KLJoin.retomoto.ini` before the baseline and before the rebuild
differ in tools/kl_graft.py and tools/kl_maps.py ONLY (MEASURED `diff tools_before.sha1 tools_after.sha1`); HEAD
moved 40a8a7a -> ada8830 in between (another session, CLAUDE.md only).

**(a) rebuilt after the change** - `python tools/kl_fa_loot.py test "C:/kl_scratch/bank/t1/after" --no-wardrobe`,
exit 0, 'RESULT: PASS'. MEASURED `python s/manifest.py diff before.manifest.json after.manifest.json`:
- chain/F07+M09_B/R09_Main.zip: '31 members / 31 members, 31 equal (name, size, CRC), 0 differ; archive bytes
  299581770 / 299581770'
- 'R09+M09_A (R09 = F07+M09_B)'/F01_Main.zip (the dressed level): '30 members / 30 members, 30 equal, 0 differ;
  archive bytes 187929451 / 187929451'
- light/F01_Main.zip: '30 / 30, 30 equal, 0 differ; 187929451 / 187929451'
- all 57 binary files beside the archives (.WAV .WHD .hti, the _LS bank, KLJoin.ini) and the three graft.txt: same
  size and sha1.
- the six that differ by sha1 are log.txt and result.json of the three folders. MEASURED `python s/beside.py before
  after`: 'RESULT: SAME but for the folder name and the seconds' (log.txt: the out folder in its 'built ...' line;
  result.json: 'seconds' 33 / 39 and 40 / 36). The two 203-line build logs are equal line for line after the same
  replacement (`diff`, exit 0).

**(c) through a module's name** - a dummy tools/kl_t1_dummy.py (a module `__getattr__` that hands on
kl_fa_author's nine names at the moment each is asked for; DELETED after the check) and
`python C:/kl_scratch/bank/t1/s/dummy_build.py "C:/kl_scratch/bank/t1/dummy"`: kl_fa_loot.test's steps one for one
(voices on, the street / blast / loot hooks, the loot dressed on the written level, lighten trim,slim), but the
chain is asked for through kl_maps' own command line: `kl_maps.main()` with the arguments `chain <out> F07 M09_B
M09_A --author kl_t1_dummy --keep`. MEASURED `python s/manifest.py diff after.manifest.json dummy.manifest.json`:
the same three lines - 31 / 30 / 30 members equal, 0 differ, archive bytes equal - and every binary file beside
the same. `python s/beside.py after dummy`: the only line that differs besides folder name and seconds is
result.json's `"author": true` -> `"author": "kl_t1_dummy"` (three folders). The build asked the dummy for every
one of the nine names (its counter: HOST 6, prepare_host 5, strip 6, KEEP 6, DROP 6, layer_names 6, complete 6,
wire 5, campaign_names 6 over the two steps, the presence test included).
So: default = name = the build of before the change, to the byte of every member.

Small tests of the two helpers (`python - <<` in the session, not kept): `author_arg` on `--author` at the end,
before `--load`, with a name before `--keep`, and absent -> True / True / 'kl_fa_bank' / False with the list
shortened by exactly the option (and its name); `author_module(True) is author_module('kl_fa_author')`;
a module with only HOST -> 'ValueError: authoring module thin lacks prepare_host, strip, KEEP, DROP, layer_names,
complete, wire, campaign_names'; an unknown name -> ImportError.

**(a) once more, on the files as committed** (a docstring line of kl_maps.py was touched after the builds above):
`python s/dummy_build.py "C:/kl_scratch/bank/t1/final"` = the same steps with the command line `chain <out> F07
M09_B M09_A --author --keep` (the option ALONE, through `kl_maps.main()`). MEASURED `python s/manifest.py diff
before.manifest.json final.manifest.json`: 31 / 30 / 30 members equal, 0 differ, archive bytes 299581770 /
187929451 / 187929451 as the baseline; `python s/beside.py before final`: 'RESULT: SAME but for the folder name and
the seconds' (result.json `"author": true`, as before the change).

### T1.5 Check (b): the bare campaign grafts hold exactly ONE cover list, the other numbers are the study's

Commands (with `--keep` only so that the archive can be read back; archives deleted afterwards). Each ends with
exit code 1 because verify's problems are not 0 - the findings of a level without a layer, as in the study:
- `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/m03" F07 M03_A --campaign --keep` -> 'campaign pre-pass: 488
  subtrees dropped', 'verify: problems: 11', 'built ... 310 MB, 31 members'.
  `python s/covers.py "C:/kl_scratch/bank/t1/m03/F07+M03_A campaign"`: '19676 nodes, 439 top-level, 1 FFCoverList,
  165 nodes named *coverbox*', 'FFCoverList on ROOT\Special!CoverList (ZLIST)'. Of the 165: 118 ZSTDOBJ under
  Locations (what the game makes covers of - the study's 118) and 47 ZBoxPrimitive (the kept PlayerCoverCollision /
  NoCoverBox markers, 46 under Special!).
- `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/m06" F07 M06_A --campaign --keep` -> '237 subtrees dropped',
  'verify: problems: 10', '327 MB'. covers.py: '19158 nodes, 318 top-level, 1 FFCoverList, 242 nodes named
  *coverbox*', 'FFCoverList on ROOT\Specials!CoverPoints!CoverControl (ZLIST)'; 225 ZSTDOBJ (the study's 225) + 17
  ZBoxPrimitive.
- Against the study's kept results (`python s/results.py <mine> <study plain> <study coverfix>`, the files under
  `<work>/build/cfa/tooling/` and `.../v2/`), every key of result.json but 'seconds':
  - against the second tooling agent's cover-fix builds: 1 key of 34 (M06_A: of 32) differs - the folder's 'tag'.
  - against the plain builds: 5 keys. M03_A: campaign_dropped 'Special!' 229 -> 228, campaign_kept 'Special!' 100 ->
    101, tops 438 -> 439, entities 19,675 -> **19,676**, ref_slots 30,556 -> 30,557. M06_A: 'Specials!' 99 -> 98 and
    41 -> 42, tops 317 -> 318, entities 19,157 -> **19,158**, ref_slots 30,038 -> 30,039.
  - unchanged, as re/campaign_fa.md section 1 has them: M03_A rooms 28, textures 1,866, materials 1,221, .prm
    chunks 64,870 (= 64,871 chunk-table entries), mesh 232,480 bytes, sounds / waves 4,724 / 4,586, archive 310.2 MB,
    .prm 85.7, .TEX 373.9, .HVK 3.0 MB, dangling 0, problems 11 (1 stream clip + the 10 findings of a level without
    a layer), kl_fa.check 1 CRASH / 9 BROKEN / 4 DEGRADED / 1 NOTE. M06_A rooms 7, textures 1,589, materials 1,002,
    chunks 53,959 (53,960 entries), mesh 258,988 bytes, archive 326.8 MB, .prm 79.5, .HVK 2.2 MB, dangling 0,
    problems 10.
- **HERO_AT**: `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/m03h" F07 M03_A --campaign --heroes --keep` ->
  log 'kl_maps: Heroes!Hero_01 stands at Special!JumpPoints!Jump#060 (-313, 205, -4398)', 'Heroes! groups placed
  where M03_A has them: 1' (without --heroes: 0). Read back from the built .prp (covers.py with the names):
  'Heroes!Hero_01 (ZGROUP): ZGEOM[2] [-312.7, 204.7, -4398.4], ZGEOM[1] [0.724, 0.0, 0.69, 0.0, 1.0, 0.0, 0.69, 0.0,
  -0.724]' - the marker's place and turn; Hero_02 stays at F07's (10558.2, 440.0, 3222.6), where Hero_01 is in the
  build without --heroes. result.json differs from the build without --heroes in 'heroes' only.
- **A module that is NOT kl_fa_author, on the bank** (tools/kl_t1_min.py: the nine names and nothing else, KEEP /
  DROP / layer_names / campaign_names handed as LISTS, one campaign node named by campaign_names; DELETED after
  the check): `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/min" F07 M03_A --campaign --author kl_t1_min
  --keep` -> 'campaign pre-pass: 487 subtrees dropped' (488 less the one kept), 'kl_t1_min: prepare_host(F07)',
  'kl_t1_min: strip(M03_A), 864 top-level subtrees', 'kl_t1_min: wire() on the joined scene: 19677 nodes,
  GamePlay!2_Secure_Parking!AnimProxy_Garage_Open is in it 1 time(s)', 'verify: problems: 11'; read back: 19,677
  nodes, 440 top-level, 1 FFCoverList, the kept node in the scene; result.json `options: {'author': 'kl_t1_min'}`,
  dangling 0. So the command of T1.7 works on this level with a module of its own.

### T1.6 What is GUESS / ASSUMED, what is open

- ASSUMPTION (kl_maps.HERO_AT, marked there): a player can stand at Jump#060. It is on the mesh (MEASURED) and is
  the campaign's own jump point; nobody has stood there in Dog Days. Its facing (into the south-west corner) is
  the marker's own, not chosen.
- NOT DONE, on purpose: a verify() line for a level with NO cover list (the study's item A, second half:
  re/campaign_fa.md 3.1). kl_graft.verify still fails only on more than one (`ncov > 1`). It is one line
  (`elif not ncov: bad.append('no cover list (FFCoverList): no cover box becomes a cover')`), but it changes the
  problem count of every build that has none, in a file other sessions' builds go through, and it is outside the
  two changes this stage was given. Until it is in, count them: `python C:/kl_scratch/bank/t1/s/covers.py <folder>`
  (the next stages' check 'exactly one FFCoverList').
- NOT DONE: `kl_fa_author.FINISH` is still not called by kl_graft / kl_maps (that file's own comment asks for
  it). What works on the WRITTEN level stays the authoring module's own step after `kl_maps.one` returns - as
  kl_fa_author.test / kl_fa_blast.test do it. For the bank that is kl_fa_bank's `test` / `build` command.
- The other tools that import kl_fa_author for Retomoto's numbers (kl_fa_bots_rt, kl_fa_loot.survey / walk
  defaults, kl_map_escape.van_prepare, kl_fa_talk.BLAST_TIMER, kl_expansion.join_ini: re/campaign_fa_tooling.md
  11.4 item 5) are untouched: where a later stage runs one of them on the bank it meets those names there.
- M07_A, M12_A and M13_B now keep their cover list too (T1.2). Nobody has built them; the change is the same one
  node as on M03_A / M06_A.
- Nothing here was run in the game.

### T1.7 For the next stages: how a build is called with a module of its own

```
python tools/kl_maps.py one "<out>" F07 M03_A --campaign --author kl_fa_bank --keep
```
- -> `<out>/F07+M03_A campaign/` with F01_Main.zip, the files beside it (.WAV .WHD .hti, the _LS bank), graft.txt,
  log.txt, result.json (`options.author` = 'kl_fa_bank'). Exit code 0 only when verify's problems are 0: a build
  with KNOWN problems ends with 1 and is written all the same (read result.json: 'ok', 'problems').
  Without `--keep` the archive is measured and deleted. NO `--heroes`: the module places the sixteen player
  groups itself (prepare_host); `--heroes` is for the bare boot `one <out> F07 M03_A --campaign --heroes --keep`.
- The module's name stands DIRECTLY behind `--author` (an argument that starts with `--` is not taken as a name;
  `--author` alone stays kl_fa_author = Retomoto). From Python: `kl_maps.one(out, 'F07', 'M03_A', keep=True,
  campaign=True, tag=' campaign', author='kl_fa_bank')` (a name, or the module object; `author=True` is
  kl_fa_author), `kl_maps.chain(..., author=...)` and `kl_graft.build(..., author=...)` take the same.
- tools/kl_fa_bank.py must hold the nine names of `kl_graft.AUTHOR_NAMES` - `kl_graft.build`'s docstring, under
  `author:`, says what each must be. In short, in the order they are used:
  `campaign_names(level)` (kl_maps, before the build: exact top-level names of M03_A that the pre-pass must leave
  in; `[]` for any other level) -> `HOST` ('F07') and `prepare_host(S, log)` (the stock kl_graft.Level, before the
  subtrees are chosen: places and values of F07's own objects) -> `strip(M, log)` (the converted kl_graft.DeadMen,
  before the join: controllers off kept nodes, map nodes re-placed) -> `KEEP` / `DROP` (patterns of F07's MAP
  subtrees that stay / go: `DROP` must name F07's cover list `Specials!CoverPoints!*` when `KEEP` holds
  `Specials!`, because M03_A's own `Special!CoverList` now stays) -> `layer_names(Jn)` (top-level names of the
  layer in the joined scene, for kl_fa.repair's prune) -> `complete(Jn)` (True: one map) -> `wire(Jn, log)` (once,
  on the joined scene: reference lists; values of existing controllers only). Each name is read off the module at
  the moment it is used, so a `test` command may set module globals (NO_AI, flags) before it calls kl_maps.one in
  the same process - import the module by its own name first (`import kl_fa_bank` at the bottom, as kl_fa_author
  does), or the build imports a second copy that has not seen the flags.
- A module that lacks a name fails at once: 'ValueError: authoring module kl_fa_bank lacks ...'.
- New entities and anything that needs chunk numbers are NOT part of the interface: do them on the written folder
  after `kl_maps.one` returns (kl_fa_author.FINISH is the pattern).
- Scratch scripts that stay (read-only helpers): C:/kl_scratch/bank/t1/s/covers.py (cover lists and named
  top-level nodes of a built folder), manifest.py + beside.py (two build trees member for member), results.py,
  marker.py, passive.py, dummy_build.py (the Retomoto regression through kl_maps' command line: `dummy_build.py
  <out>` rebuilds what `before.manifest.json` records; 1.5 minutes).

## Stage T3 - the collision route test as a tool (NEW tools/kl_route.py)

STATE: DONE (2026-10-11 13:40), committed as 812565b. One new file, `tools/kl_route.py` (1,316 lines), and this
section; no other file was touched, no build was run (T1 was editing kl_maps / kl_graft: every input is an
archive that existed).
Scratch C:/kl_scratch/bank/t3/ (0.2 MB): `checks.py` (every check below is one name of it: it prints the command
and runs it), `out/<name>.txt` (the outputs quoted here), `place_agree.py`, `flags_census.py`, `dbg.py` (what the
grid holds round a place). `<f1>` below = `<work>/build/cfa/fill1`.

### T3.0 What was read, and what the tool takes from each

- bank: `G:/kl_scratch/cfa_bank/skeptic/walk8.py` / `walk9.py` - kl_escape.Walk's sampled grid, a flood over
  (cell, floor height), REF ids taken out at flood time. TAKEN: the cell (20), the sampling pitch (10), the floor
  rule, the step (45 up / 60 down), the body heights (55..165), 'a place is reached from a floor near it', and
  'shut each set again in turn' as the test of NECESSARY.
- club: `G:/kl_scratch/cfa_club/skeptic/walk5.py` (kl_escape.Walk as it is: one floor per cell) - nothing new.
- Havana / prison / the critic: `G:/kl_scratch/cfa_critic/hwalk.py`, `prison_walk.py`, and on built archives
  `G:/kl_scratch/cfa_fill1/hwalk_built.py`, `prison_walk_open.py`, `havana_walk_open.py`. TAKEN: the body's
  half width (30), the 'thinnest crossing' search that names what is in the way in the order it is met, 'take
  out what was crossed and ask again', a crossing only where the mesh lies, and the snap of a place that stands
  in something to the nearest walkable spot (they took the nearest mesh cell within 2 m without saying so).
- park: `G:/kl_scratch/cfa_park/skeptic/sk_walk.py` - TAKEN whole as 'the way an AI is given': polygon middles
  joined through the middles of the shared edges, a sample every 25, a floor within 90, the body column free.
- `G:/kl_scratch/cfa_fill1/blockers.py`, `front_blockers.py` - TAKEN: the path blockers' boxes, tested against
  that mesh way. `closures.py` - read for what a closure is in the files.
NOT taken: walking only on mesh cells (hwalk: a player walks off the mesh, and a build with a broken mesh would
read as shut), and a body without width (walk8).

### T3.1 The tool

`python tools/kl_route.py walk | stations | doors <level> ...` and `route()`, `blockers()`, `stations()`,
`doors()`, `mesh_way()`, `load()` for other tools; `<level>` = a build folder, an archive or a stock level's name
of either game. The docstring is the spec: every number of the walker with whose it is, and what is ASSUMED.
In short: a lazy grid of 20-unit cells over the .HVK (floors under the cell middles, everything else sampled,
convex shapes by their planes); a walker with a body 60 x 60, 55..165 over its floor, stepping 45 up / 60 down;
a search that, when the way is shut, goes on through objects and names them; the navigation mesh for 'on the
mesh / which part', for where a crossing may be, and for the line an AI is given (with the path blockers).
Run times here: a walk 3 - 6 s, stations / doors over the whole bank 18 - 25 s.

New against the study's scripts (each one MEASURED on real files, below): the body has a width AND the walk is
not tied to the mesh; convex shapes are rasterized, not boxed; a place is walked from GROUND (not from a table
top); hidden bodies count by default and the verdict says when it hangs on them; a placement that does not
stand where its entity does is reported; path blockers and mesh links are part of the AI's line; every object
named carries its collision flags and their reading.

### T3.2 MEASURED while writing it

- Placements against entities (`python C:/kl_scratch/bank/t3/place_agree.py M03_A F07 "<f1>/F07+M03_A campaign
  open/walk_members.zip" "<f1>/F07+M03_A campaign beats/walk_members.zip"`): every STATIC / KEYFRAMED placement
  stands exactly where its entity's .gms chain puts it, in place and rotation: 0 of 3,653 (M03_A), 0 of 1,859
  (F07), 0 of 3,467 and 0 of 3,479 (the two built bank archives) differ by more than 2 units. (RIGID agrees too;
  VEHICLE placements stand elsewhere, 13 of 13 in M03_A; WEAPON placements agree in place and differ in
  rotation, 48 of 51 in F07 - neither is counted by the walker.) So 'a leaf moved, its collision left'
  is detectable: with the roller door's entity sunk by 2,500 in memory `Level.moved()` returns exactly
  `[(23559, 2500, 'M03_A_Garage_01a\SI0201_M03_BackDorAnim_01')]`, and `[]` on all four files as they are.
- Convex shapes: on the 850 convex shapes of M03_A, M11_B and F07 every vertex satisfies n.v + d <= 0 for every
  plane (largest value 1e-5) and every plane touches a vertex. Rasterized from the planes and clipped to the
  vertices' box, the 431 / 259 convex placements of M03_A / M08_A stay inside their world boxes, reach top and
  bottom, and fill 84 % / 76 % of the boxes' cells (what a turned door or car leaves free). Without the clip
  35 flat shapes (car windows) ran up to 43 over their own box: their planes do not close them.
- Collision flags by object name (`python C:/kl_scratch/bank/t3/flags_census.py M03_A M11_B M08_A F07`): 0x40
  alone = `ColiObj_Camera*` / `ColiObj_CamLamp`; 0x10 alone = `ColiObj_BlockSight` / `ColiObj_Vision` /
  `BlockVisionPlane`; 0x20 alone = `InvisibleBlock_*` / `ColiObj_NPCBlock`; 0x108 = `ColiObj_Hero*` / `OnlyHero`
  / `HeroOnly` / `ColiObj_Player*` / `ColiObj_HERO_hack`; 0x102 / 0x42 = shards, lamps, monitors; the plain world
  is 0x72. Read as: 0x20 stops every character, 0x8 the heroes only, 0x40 the camera, 0x10 sight, 0x2 shots.
  BY NAMES ONLY. One thing fits it from another side: at the Capitol's wing door the campaign has BOTH a
  hero-only plane (`ColiObj_Obj_Roadblock_01`, 0x108) and path blockers in state eBlocking
  (`PathBlocker_BunkerBackDoor_01`, `PathBlocker_LastGuys_01`) - one for the heroes, one for the AI
  (`python tools/kl_route.py walk M11_B --from 39211,830,30410 --to 40500,830,31900 --who npc`: FREE in the
  collision, 9 samples of the mesh way in those boxes; `--who hero`: BLOCKED by the plane).
- The bank's mesh: its narrowest shared edge on the round's way is 49 (a doorway: the mesh is drawn in from the
  walls), so 'no edge under 100' (the park's rule) cannot be a condition; the tool prefers 100, then 50, then
  any, and prints the narrowest it used. (The tab's Fragile Alliance bank: narrowest edges 18 and 29 on the two
  legs through its garage exit. Recorded; whether that has to do with the bots' deaths there was not looked at.)
- Path blockers as the tool reads them: bank 'open' build 4, all eBlocking, at the front entrance (boxes round
  (108, 802, -9400), (129, 802, -9359), (467, 802, -9356), (486, 802, -9399): G1.2's four); prison 'open' build
  35 with `PathBlocker_CageDoorB` eNotBlocking, prison 'beats' build the same one eBlocking (G1.4); the tab's
  Fragile Alliance bank 2 (`Triggers!GarageDoors!PathBlocker` eBlocking at (296, 203, -4682)).
- Places that are not ground: the Capitol's checkpoint 5 (37600, 830, 30521) lies INSIDE the block
  `Collapsed_Rubble_005` (collision y 696..963) and 75 off the mesh; 'wing C_01' is a display case; 'table' is
  the table. The study's walk snapped such a place to the nearest mesh cell within 2 m; this tool walks to the
  nearest GROUND within 2 m and says how far that is. A free floor is not enough: the chairs round the
  Capitol's table have free seats 54 over the floor, and a place given at the mesh's height (830 over a floor
  at 800) is nearer to a seat than to the floor - hence 'ground' (300 away and more than 400 floors reachable,
  by steps that can be taken back).

### T3.3 The checks (each: `python C:/kl_scratch/bank/t3/checks.py <name>`; output `out/<name>.txt`)

| what the study measured | input | the tool's line |
|---|---|---|
| bank: six door sets in series, each necessary (`walk9.py`) | `doors "<f1>/F07+M03_A campaign beats" --from "START yard=300,200,-4350" --via vault=399,-960,-12818 --to "street east=3958,700,-11173"` (name `bank_doors`: the built level with every door in its place) | `-> 7 closure(s) in 6 set(s); 7 necessary; with all of them out the way is FREE` - the roller door (REF 23559), a leaf of glass door 1 (27653), of glass door 2 (27648), the vault door (27063), the airlock's two planes (27787, 27790: one set), the hall / foyer leaf (26950) |
| the same on the stock level | `doors M03_A ...` (`bank_stock`) | the same line; REF 7437, 13998, 13986, 12805, 14012, 14015, 12596 = the ids of `G:/kl_scratch/cfa_fill1/closures_M03_A.txt` |
| bank, 'campaign open' build: free from the yard to the street (`walk8.py`: flood A reaches 45 of 46, the statue not) | `stations "<f1>/F07+M03_A campaign open"` + walk8's 46 places (`bank_open`) | `-> 45 of 46 places reached from the first in the collision; NOT: statue (behind bars)`; the statue: `NOT reached even through objects` |
| | `walk` yard -> vault -> street east on it (`bank_open_walk`) | `FREE, 86 m of cells, floor y -960..242` and `FREE, 173 m of cells, floor y -960..803`; `RESULT: FREE; the mesh way: 1187 samples, all free` |
| the plain build: only the yard (`walk8_built.txt`: 5 of 46) | `stations "<f1>/F07+M03_A campaign beats"` + the 46 (`bank_plain`) | `-> 5 of 46 places reached` (START, both stacks, the traitor row, the dock door) |
| Capitol: four static switches, each on the only way (`walk3.py`) | `doors M11_B --from START=33981,830,30387 --via table=42500,830,31915 --to "van stop=27000,20,22600"` (`havana_strict`) | `-> 5 closure(s) in 5 set(s); 5 necessary; with all of them out the way is FREE`: `M11B_OYCHECK_BEFORE01` (4333) and `SI0100_M11_BarricadeB_01` (4617) = the bunker's ONE switch, `ColiObj_Obj_Roadblock_01` (5313, the wing door), `SO0201_M11_Corner_01` (10618), `SO0201_M11_BarricadeXX_01` (10619) - the five static pieces G1.5 took out for the four switches |
| Capitol 'open' build: all 13 legs free | `walk "<f1>/F07+M11_B campaign open"` + walk3's chain (`havana_open`) | 13 x FREE (39, 14, 15, 26, 41, 53, 24, 47, 5, 32, 14, 39, 29 m) |
| prison: seven closures in series (`prison_walk.py`) | `doors M08_A` + the critic's ten stations, `--hidden-out` (`prison`) | `-> 7 closure(s) in 7 set(s); 7 necessary; with all of them out the way is FREE`: cage door B, two in the ground passage, two of the last gate, the two fences |
| | the same with hidden bodies counted (`prison_strict`) | the same seven; the two fences now each hold `FenceFall_Pre` AND its hidden twin `FenceFall` (13736, 13730) |
| prison 'open' build: 9 of 9 legs free | `walk "<f1>/F07+M08_A campaign open"` + the ten (`prison_open`) | 9 x FREE; `the mesh way: 788 samples, all free` |
| park: 1,271 samples free (`sk_walk.py`) | `walk M06_A` + its eight places (`park`) | `RESULT: FREE; the mesh way: 1271 samples, all free`; per leg 18, 128, 61, 272, 311, 270, 211 samples over 4, 30, 14, 66, 74, 62, 51 m: sk_walk.txt's own figures, leg for leg |
| club (not asked; for the record) | `stations "<f1>/F07+M05_A campaign open"` + round A's 14; `doors` on the 'beats' build (`club_open`, `club_doors`) | `14 of 14 places reached`; `4 closure(s) in 4 set(s); 4 necessary`: a leaf of each office door and the two entrance seals (`HeroColi`, `Plane01`, both 0x108) |
| the tab's Fragile Alliance bank: a known-good route | `walk "<work>/build/w_tabM/KLExpansion/Maps/DM03"` through the places of its bots' own route (`<work>/build/z_route/M03/bots.txt`: START row (-1808, 700, -11838) -> entrance -> hall -> stairs -> the dock's loot (424, 224, -6154) -> garage exit -> yard -> before the opened wall -> alley (-1650, 149, -170) -> level exit -> boarding place) (`fa_bank`) | 10 x FREE (31, 16, 30, 29, 29, 32, 10, 6, 26, 12 m; the opened wall: `floor y 150..200`); the mesh way crosses by `a LINK of the mesh (kind 2) from (-1704, 220, -766) to (-1700, 150, -534): 232 across, 70 down` - the link bots.txt names |
| the other way round: the stock map, the wall standing | `python tools/kl_route.py walk M03_FA_A --from -1706,219,-899 --to -1650,149,-170` | `NO WAY even through objects`; first of what bounds the reached area: `SO0101_M03_Wall_Low_8m_05` - the piece tools/kl_escape.py opens |

Also run: `--open` by name and by REF (the 'beats' build with five sets named out and the vault door left:
both legs `BLOCKED` by REF 27063 `SI0102_M03_BankVault_Door_PRE` and nothing else, `with them out: FREE`, 9
samples of the mesh way in the door; with the door named too: `RESULT: FREE`), `--rigid`, `--who`, `--no-mesh`,
bad arguments (exit 2 with one line), and the five functions called from Python in one process (48 s for a route,
its blockers, a stations run, a doors run and a mesh way on the bank).

### T3.4 Where the tool's figures differ from the study's, and why

- Lengths are of cells through the collision (bank 86 m in, 173 m out), not of mesh polygons (the study: 120 /
  164 m; the tool's own mesh way: 96 / 188 m).
- `doors` names the LEAF crossed, not the whole door: one leaf of a double door out is a gap of 1.2 m and enough
  for the walker (it needs 0.8). Sets are counted by parent + name (less the number, less LEFT / RIGHT), so the
  bank's airlock (two planes, four leaves) is one set and its vault door, crossed twice by one way, one closure.
  The Capitol's bunker is one switch in the campaign and two closures here (two static pieces 5 m apart).
- 'Reached' is 'the walk comes to a free floor within 86 of the place, nothing between the two but what the
  place stands in'. 86 = the bank walk's rule (a floor within two cells: a square, 56 at its corners) plus the
  half width (30) the bank walk's walker did not have. With 70 (40 + 30) the trolley place fails by 2 units -
  the walk comes to within 72 of it, the trolley and two cartons stand there - which is why the constant is
  argued in the source. For loot use `--near 125` (a money container's reach); for a spawn point read 'gap'.
- Hidden bodies COUNT by default (the study's second agents left them out, fill1 ran both). It matters once in
  these checks: at the Capitol's corner the only floor on the way is that of the HIDDEN `SO0201_M11_CornerBroken_01`
  (`dbg.py M11_B 32255,864,28907`), so with `--hidden-out` the stock level has no way there at all - not even
  through `Corner_01`; hwalk did not see it because it walked on the mesh where it found no collision floor.
- In the bank 'open' build the six loot-wall places stand inside `Vault_POST` (REF 26914, the vault's blasted
  state, hidden at load) - `stations` prints it. The walk comes to within 50 of each all the same.

### T3.5 GUESS / ASSUMED (all in the docstring and at the constants)

ASSUMED: the step (45 / 60) and the body (60 x 60, 55..165) - never read in kl2.exe; that a hidden body may
collide (counted, `--hidden-out` for the other reading); the flag reading behind `--who` (names only); that the
.HVK's place of a key-framed body is the one that holds when its entity was moved (the tool only reports the
disagreement). GUESS: `ISLAND` / `ISLAND_N` (what is ground: 300 away, 400 floors), `PB_DY` (a path blocker's box
counts 100 above and below itself: what a blocker does to the mesh was not read), `GAP` (2 m, the Havana walk's).
LIMITS: no climb, vault or drop over 60 (`--down`); RIGID bodies, vehicles and weapons do not count (`--rigid`
for the first two) but a car's KEYFRAMED doors, wheels and windows do, where the file has the car (the tab's
bank has one on its yard way point: 45 samples of the mesh way); a convex plate thinner than 5 can slip through;
a convex shape is never a floor (a lift, a plank); the mesh way runs between polygon MIDDLES, so a leg inside
one polygon is one sample.

### T3.6 For the next stages: testing the bank's route

From the command line (`<b>` = the build folder; exit 0 = free / all reached):
```
python tools/kl_route.py walk <b> --from "START=<x,y,z>" --via "vault=399,-960,-12818" --to "street=3958,700,-11173"
python tools/kl_route.py walk <b> ... --open SI0102_M03_BankVault_Door_PRE_01      (the same with the vault door out)
python tools/kl_route.py doors <b> --from ... --via ... --to ...                   (what is still a closure, and is each necessary)
python tools/kl_route.py stations <b> "START=<x,y,z>" <every spawn place> --near 30
python tools/kl_route.py stations <b> "START=<x,y,z>" <every loot place> --near 125 --open SI0102_M03_BankVault_Door_PRE_01
```
What to expect of the authored bank with the lead's defaults (every door set open at build time EXCEPT the vault
door) - MEASURED on the study's 'beats' build with the five other sets named out by `--open`, not on a build of
the layer, which does not exist yet: `walk` without the vault door named: the legs into and out of the vault
`BLOCKED` by `SI0102_M03_BankVault_Door_PRE` (there REF 27063) and nothing else, `with them out: FREE`, 9 samples
of the mesh way in the door; with it named (or once its fall-back took its collision out at build time):
`RESULT: FREE; the mesh way: 1187 samples, all free`. `doors` should then say `1 closure(s) in 1 set(s); 1
necessary`. A `MOVED:` line in the head means a leaf was sunk and its placement left behind, or the reverse:
fix the build, do not argue with the line.
From a module (the same answers as dicts; one Level and one grid per process, so several questions cost one read):
```
import kl_route
r = kl_route.route(folder, [START, VAULT, STREET], opened=['SI0102_M03_BankVault_Door_PRE_01'])   # r['free'], r['legs'][k]['crossed']
objs, free = kl_route.blockers(folder, [START, VAULT, STREET])            # [{'ref', 'name', 'kind', 'at', 'dist', 'hidden'}] nearest first
rows = kl_route.stations(folder, [START] + places, near=30)               # row['mesh'], row['part'], row['reached'], row['gap'], row['in']
d = kl_route.doors(folder, [START, VAULT, STREET])                        # d['closures'][k]['necessary'], d['sets'], d['free']
m = kl_route.mesh_way(folder, [START, VAULT, STREET])                     # per leg: 'samples', 'nofloor', 'hit', 'blockers', 'links'
```
`opened` takes REF ids and / or text looked for in the entities' paths (a group's name opens its subtree).
What the bank's later stages should look at beside FREE: (1) the four path blockers at the front entrance are
eBlocking in the bare build; the mesh way passes between their boxes (0 samples in them) - if the layer moves
the way or the engine blocks whole polygons (not read), `walk` shows it as `PATH BLOCKER ...`; (2) `stations`
puts every place on a mesh PART: all of the round must be on the part of the START (566 polygons); (3) hidden
things the layer shows or blows (`Vault_POST`) are in the walk by default - use `hidden=False` / `--hidden-out`
to see the level as it is at load, and both when a beat swaps geometry.

### T3.7 Open

- Nothing of the walker was held against the running game beyond what kl_escape.Walk's rules already were (the
  yard wall). The body width is the new part: a FREE of this tool means a gap of at least 60 - 80.
- What a path blocker does to the mesh, and whether a hidden body collides: both would be read in kl2.exe, not
  measured in files.
- tools/kl_maps.py and tools/kl_graft.py were neither imported nor run by this stage. The tool imports kl_gms,
  kl_hvk, kl_pf4 and kl_scene, and kl_prpjoin / kl_fa only for a stock level's archive and for the path blockers
  (when those two cannot read a .prp the walk still runs and says that the path blockers were not read).

(end of Stage T3)

## Stage T2 - the escape van from WAY POINTS (tools/kl_map_escape.py: a second front end)

State 2026-10-11: DONE, all three checks PASS. Offline; nothing installed, the game not started (the owner was
playing). Scratch: C:/kl_scratch/bank/t2/ (2 MB: scripts `s/`, outputs `out/`, the three manifests, the build logs;
every archive deleted, the bare graft too).

### T2.0 Baseline, made BEFORE any edit

`python tools/kl_map_escape.py van <work>/build/t_maps2 C:/kl_scratch/bank/t2/before M03` (tree at dca38bf + the
other sessions' uncommitted files) -> `RESULT M03: van built; kl_map_tune PASS; van check: 0 fault(s)`;
`before.manifest.json` = 2 archives, 62 members (the graft step and the tuned map), `before/M03/*` = its 32 text
files. sha1 of tools/*.py and re/*.json before and after the stage: only kl_map_escape.py (mine) and
kl_fa_bots_rt.py (another session's, not used by this build) differ.

### T2.1 What was changed (one file)

tools/kl_map_escape.py, +219 / -20 lines. The old `van_plan` is CUT IN TWO at the line after its two routes are
read; nothing of what follows was rewritten, only guarded for 'no car':
- `van_plan(src, log)`: as before reads the ONE Dead Men escape car and its two spline routes, then calls
- `_van_road(src, L, G, P, pin, pout, log, v=None, back=BOARD_BACK, heading=None, cam=None, clear=())`: the old
  body from the curve on (road height, LIMIT_IN / LIMIT_OUT / MIN_IN / MIN_OUT, the lane, the cuts, wait / stop /
  end / heading / board, bounds, other cars, camera, drop list, the log). Guards: `v` None -> no own REFs, no gate,
  no 'things the car switched' loop, `car` None, `drop` empty, no boarding action looked for, the first log line
  says 'the road as way points'. `back` = how far beyond the last way-in point the van's origin stands (337 = the
  old rule, 0 = the point IS the origin). `clear` REFs are left out of the lane AND of the road height.
- NEW `van_plan_points(src, arrive, stop, leave, heading=None, at='origin', cam=None, clear=(), log=print)`: THE
  SECOND FRONT END. Docstring = the spec. `at='box'` gives the stop the meaning a Dead Men car's stop has (rear
  box there). `heading` given is MADE by two guide points STRAIGHT = 300 either side of the stop and a plan more
  than REL_MAX (6 degrees) off is a fault. A build that still has ONE escape car is planned as `van_plan` plans it
  (drop list, gate, switches) with only the road from the points: that is what makes check (a) an identity.
- NEW `van_road(src)`: a car map's own road in that form (`arrive`, `stop`, `at='box'`, `leave`).
- NEW `cam_spot(L, G, stop, heading, must, wish)` + `_van_cam(L, G, P, cam)`: a campaign level has no escape camera.
  `cam` given = that eye; None = the designers' when the build has one (old rule), else cam_spot's: a ring CAM_FAR
  = 18 / 22 m round the stop, CAM_OVER = 330 / 430 / 530 over the road, a floor under the eye, clear sight to the
  stop and to the drive CAM_SEES = 850 and 2500 after it; chosen: sees the end if any does, then most nearly behind
  the standing van. Faults: eye outside / under the map, within EYE_MIN of a floor, or NOT SEEING THE STOP.
- NEW `van_layer(P, log)`: a context manager for a build whose layer is an authoring module (T2.5).
- `van_build(..., road=None)`: with `road` the plan is made from points (the test); `other_cars(L, v, ...)` takes
  `v` None; `main()`: `van-plan <build> --points <road.json> [--json]`, `van-plan <build> --road`,
  `van <builds> <out> M03 --points <road.json>`. Without `--points` the argument list is parsed as before.
Not touched: `curve`, `lane`, `Poly`, `van_prepare`, `van_wire`, `van_hvk`, `van_check`, `gate_*`, `repair`, `check`.

### T2.2 Check (a): M03_FA_A's own two spline routes, given back as points, give the same van - PASS

- THE PLAN. `python C:/kl_scratch/bank/t2/s/check_a.py <work>/build/t_maps2/M03 out/road_M03.json` (van_plan against
  van_plan_points(**van_road(src)), every key of the two plans compared as JSON):
  `keys of the plan: 23 (spline front end), 24 (points front end); only in one: ['points']; in both and different:
  none`, `path 701 points, SAME, every coordinate`, `RESULT: SAME PLAN`. Numbers: lin 6000.0, lout 7999.9, waits
  (-2555.4, 152.0, 558.5), stops (3305.6, 2.0, 3.8), ends (10289.6, 2.0, -1102.8), headings 129.1 / 95.3 / 171.7,
  rear box (2970.0, 0.0, 34.8), camera (1576.7, 328.8, 407.6) from EscCameraSetup!CamPos01 = re/map_escape.md 10.4's
  bank row. The same on M01 (25 / 26 keys: gate and second camera too) and M02: `RESULT: SAME PLAN` twice
  (`out/check_a_M01.txt`, `_M02.txt`, `_M03.txt`).
- THE BUILD. `python tools/kl_map_escape.py van <work>/build/t_maps2 C:/kl_scratch/bank/t2/points M03 --points
  C:/kl_scratch/bank/t2/out/road_M03.json` -> `RESULT M03: van built; kl_map_tune PASS; van check: 0 fault(s)`.
  `python s/compare.py before.manifest.json points.manifest.json before points`:
  `M03/F01_Main.zip: 31 / 31 members, 0 differ; archive bytes 200762666 / 200762666`,
  `_graft/M03/F01_Main.zip: 31 / 31 members, 0 differ; archive bytes 196717360 / 196717360`,
  `M03/van.json: equal once the plan's "points" key (8 + 1 + 8 points) is taken out`,
  `RESULT: archive members that differ: 0; files beside M03's archive: 32 equal (but for the folder name), 0
  different, 0 only in one`. So the van laid from points IS the map's existing van, byte for byte.

### T2.3 Check (b): the old front end is unchanged - PASS

`python tools/kl_map_escape.py van <work>/build/t_maps2 C:/kl_scratch/bank/t2/after M03` on the file as committed
(its sha1 checked again after the run) -> `RESULT M03: van built; kl_map_tune PASS; van check: 0 fault(s)`;
`python s/compare.py before.manifest.json after.manifest.json before after`: both archives `31 / 31 members, 0
differ`, same archive bytes; `RESULT: archive members that differ: 0; files beside M03's archive: 32 equal (but for
the folder name), 0 different, 0 only in one` (van.json and van.txt among them: the plan's key order and every log
line are the old ones). `python tools/kl_map_escape.py van-plan <bare bank graft>` (old front end, no car) prints
nothing, as before (the '0 escape cars' fault is returned in the plan; that path is the old code, line for line).

### T2.4 Check (c): the bank's through lane against M03_A's collision - PASS, with ONE change to the study's road

Bare graft: `python tools/kl_maps.py one C:/kl_scratch/bank/t2/m03 F07 M03_A --campaign --keep` (310 MB, 11
problems as T1 says; deleted after the checks). Ground: 103,131 triangles of map collision, 525 convex bodies.
- THE STUDY'S LANE AS WRITTEN FAILS ONE LIMIT, on the leave leg: `FAULT only 2426 of clear lane after the stop
  (least 3000)`. Not collision: the designers' away road ENDS at (3958, 713, -11173), 30.1 m after the stop, the lane
  is tested VAN_NOSE = 600 beyond the drive's end, and MIN_OUT is 3000. Everything else of it passes (lane clear,
  drive in 48 m).
- THE CURE: the away road carried on east along its own line to (8600, 705, -11173). MEASURED (`s/east.py`,
  `s/probe.py`): the square's ground plane (S00701_M03_Square_PlaneA_03 / _15, y 700.0) runs unbroken along z -11173
  from x -2900 to 8600; the square is furnished out to x 8000 (benches, walls, palms; 12 - 15 map entities per
  1000 of x), 'UNIQUE_StreetFAR' stands at 9000 - 10000. What is DRAWN in the lane out there was not looked at.
- THE PASSING PLAN = `C:/kl_scratch/bank/t2/out/road_bank.json`:
  ```
  arrive  (-3248, 710, -11859) (-1917, 712, -12126) (-231, 707, -12332)        the designers' in-road, first three points
  stop    (949, 704, -11105)   at = origin, heading not forced
  leave   (2473, 705, -11177) (3958, 713, -11173) (8600, 705, -11173)          their away road + the extension
  ```
  `python tools/kl_map_escape.py van-plan "<bare graft>" --points out/road_bank.json` -> exit 0, 0 faults:
  `waits (-3248, 702, -11859) heading 102 -> 48 m in 7.2 s -> stops (949, 702, -11105) heading 67 (rear box at (638,
  700, -11235)) -> 71 m in 8.48 s -> ends (8000, 702, -11172) heading 90`; `road under the drive y 700.0 .. 700.0`;
  lane first pass: nothing (no cut); exact: lin 4805.3, lout 7068.2, wait [-3248.0, 702.0, -11859.0], stop [949.1,
  702.0, -11105.0], end [8000.0, 702.0, -11172.9], headings 101.6 / 67.3 / 90.0, board [638.3, 700.0, -11235.3],
  camera [-711.5, 1030.0, -11799.6] (cam_spot, GUESS: 18 m behind the stop, 330 over the square; `54 of the 144
  places tried see the stop and the drive 850 and 2500 after it; this one does not see the end` - ColiObj_Camera_01
  and SO0502_M03_Coner_01_01 are between, as on two of the three car maps).
  The four limits: 4805 of at most 6000 in (least 2000), 7068 of at most 8000 away (least 3000).
- MARGIN (`s/bank.py through`): the lane is also clear 260 and 320 wide (the test is 220); at 400 wide the planter
  S00701_M03_Square_DirtB_04 comes in 27 m before the stop, at 520 four benches on the drive away. The study's own
  script found 7 ray places on that planter: it walked straight legs, the tool walks the curve through the points.
- LEVEL BOUNDS the drive passes: Special!Levelbound!LevelBound_Outside_Right!Bound 46.3 .. 41.5 m BEFORE the stop
  (empty van), ...LevelBound_Outside_Left!Bound 25.8 .. 30.6 m AFTER it (players aboard). The same case as the
  Fragile Alliance bank's van (its Back_West bound 15.8 .. 17.6 m after the stop), where bots boarded and escaped
  live (CLAUDE.md, run H0_DM03). Not seen for a human passenger.
- ON F07'S KEYS (`s/prepare_dry.py`, van_prepare on stock F07 in memory): `563 position and 550 rotation keys
  rewritten in place (391 of them the drive, stop at key 159); drive in 5063 -> 4805 (x 0.95), away 7019 -> 7068 (x
  1.01)`, speed away 8.3 m/s mean, 14.8 top (stock 14.7): nearly F07's own drive, unscaled.
- END TO END (`s/trial.py`: F07 + M03_A --campaign with a throw-away module = KEEP VAN_KEEP, prepare_host ->
  van_prepare, the build inside van_layer; no layer, so no exit trigger to wire): the build `ok True, problems 10`
  (the layer findings), `.HVK: 9 static placements of the van's subtree cut, 5 key-framed placements of the van put
  at its waiting place`, then van_check on the WRITTEN folder with the plan: `keys 0.0 off the road height at most,
  largest step 59, nose up to 1.1 degrees off the tangent ... lane (5 rays, every 20, 350 before and 600 beyond):
  clear`, `boarding box at the stop: (636, 702, -11230); key-framed placements 5, at most 1.1 from their entities;
  camera: {'eye': [-712, 1030, -11800], 'over': 330, 'far': 1814, 'sight': []}`, `.HVK 3268992 bytes`, `0 fault(s)`.
  One note it prints: `no define FAEscCameraLAST in the level` (the layer's to bring: T2.5).
- THE CREW CAN GET THERE: `python tools/kl_route.py stations <bare graft> ... "rear box=638,700,-11235" "van
  stop=949,702,-11105"`: both `on the mesh, part 0 (566 polygons)` = the START's part; `kl_route.py walk --from
  "front entrance=300,800,-9350" --to "rear box=638,700,-11235"`: `FREE, 18 m of cells, floor y 700..800`, mesh way
  20 m, narrowest shared edge 310.
- OTHER STOPS TRIED (`s/paths.py`, `out/paths.txt`): heading 90 asked -> 93.7 made, rear box (613, 700, -11083), 0
  faults; heading 44 -> 39.9, 0 faults; heading 0 -> fault (-8 made, the bend refuses it); `at='box'` with the box at
  (638, 700, -11235) -> 0 faults; the first agent's stop (250, 707, -10700): `FAULT only 414 of clear lane before
  the stop (least 2000)` - confirmed dead. A way in laid THROUGH the planter and a bench: fault (1075 of lane);
  with both named in `clear`: 0 faults.

### T2.5 For the layer stage: the calls

```
import kl_map_escape as E
ROAD = dict(arrive=[(-3248, 710, -11859), (-1917, 712, -12126), (-231, 707, -12332)], stop=(949, 704, -11105),
            leave=[(2473, 705, -11177), (3958, 713, -11173), (8600, 705, -11173)])       # at='origin', heading None
P = E.van_plan_points(<a built F07 + M03_A folder>, log=log, **ROAD)      # P['faults'] must be empty
KEEP          += E.VAN_KEEP             # 'Animation/F07/F07_Escape_Vehicle_01.zip', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01'
prepare_host:    E.van_prepare(S, P, log)       # F07's keys + the 19 objects beside the drive
wire:            E.van_wire(Jn, P, log)         # names the van in EVERY OnlineExitLevelTrigger; raises when there is none
with E.van_layer(P, log): kl_maps.one(out, 'F07', 'M03_A', keep=True, campaign=True, tag=' campaign', author='kl_fa_bank')
rep = E.van_check(E.Level(<written folder>), log, P)                      # rep['faults'] must be empty
```
- The plan needs a BUILT folder for its collision (`Level` reads a build's F01_Main.zip, not a stock Dead Men
  archive). Either plan once on a bare graft and keep P as JSON beside the module (`van-plan ... --points ROAD.json
  --json` prints it; it is the map's collision that counts, and the layer does not change the square), or build
  twice. If the layer puts ANYTHING with collision on the square (kept squads' cars, cover objects), plan again on
  the layered build: the lane test sees only what stands under a 'Locations/' subtree plus every convex body.
- `van_layer` raises on leaving when one of van_prepare / van_wire / the collision join did not run.
- P['board'] (638.3, 700.0, -11235.3) = where the van's own BoardingTrigger stands at the stop: the bots' boarding
  station, the exit box and the escape marker go round it. In the FILE that box stands at the waiting place (it
  rides on the van): kl_fa_bots takes its place from the file - re/map_escape.md 12 and 15 say what was done for
  the three car maps ('--park' is superseded there).
- The layer brings: at least one OnlineExitLevelTrigger (F07's or a made one) and the box with the define
  FAEscCameraLAST (van_check prints a note without it; the three car maps have Dead Men's EscCameraSetup!EscCameraLAST).
- F07's second and third van are not kept by this (VAN_KEEP is the first only). Whatever unused van stays: CLAUDE.md's
  rule about a FakeTarget outside the rooms' bounds (crash 0x686a66) is the layer's to hold; the kept van's own
  waiting place (-3248, 702, -11859) is on the square, 46 m from the stop.
- Command-line twin: `python tools/kl_map_escape.py van-plan <folder> --points C:/kl_scratch/bank/t2/out/road_bank.json`
  (exit 1 on a fault), `python tools/kl_map_escape.py van-check <folder>`.

### T2.6 GUESS / ASSUMED (each marked in the code)

- GUESS (the lead's to turn): the leave leg's extension to x 8600. The collision floor and the furniture are
  MEASURED; that the square LOOKS like a road out there, and that nothing only drawn stands in the lane, is not.
  A shorter drive away should pass too - by arithmetic, not run: the end 3000 after the stop is at about x 3950, and
  the lane is tested 600 beyond it, so a leave leg that reaches x 4600.
- GUESS: cam_spot's choice (CAM_FAR, CAM_OVER, CAM_SEES, 'behind the van first'). The eye (-711, 1030, -11800) is
  over the square west of the stop, looking east along the drive. `cam=(x, y, z)` in ROAD overrides it.
- ASSUMPTION: STRAIGHT = 300 (what a forced heading means). Not used by the delivered plan (heading None).
- ASSUMPTION (the old ones, unchanged and now also the bank's): the Catmull-Rom curve, LIMIT_IN / LIMIT_OUT (GUESS
  in the code), the van not pitched to the road (flat here: y 700.0 all the way), a key-framed body moves with its
  entity, a passenger of a key-framed van passing a level bound.
- The stop's heading 67 is what the curve gives at the bend between the straight in (44) and the away road (90):
  the van stops already turning. Heading 90 (east) passes too and puts the rear box at (613, 700, -11083), nearer
  the steps; not chosen - the lead's / the owner's taste.

### T2.7 Open

- Nothing ran in the game. First live questions for this van: does it show and drive on the square; the bound
  25.8 .. 30.6 m after the stop with a human aboard; the camera's picture.
- `kl_fa_bots` / the talk and tune tools that read `van.json` of a `van_build` folder were not run on a
  points plan; the plan has the same keys plus 'points' ('car' is None, 'drop' and 'exits' empty on a level
  without a layer).
- The lane test does not see what is only DRAWN, nor what a layer adds outside 'Locations/' unless it is a convex
  body. van_check on the layered build is the gate.
- Another systems level than F07: `_van_nodes` still looks the van up by F07's names (re/campaign_fa.md, 'Another systems level as the way out of the chunk table');
  not this stage's.

(end of Stage T2)

## Stage L1 - the authoring module, first half: a round without enemies (NEW tools/kl_fa_bank.py)

STATE: DONE (2026-10-11 14:45). `tools/kl_fa_bank.py` (1,058 lines) holds the nine names of the interface and builds
F07 + M03_A with the first half of the layer; every check of the stage passes with TWO known findings, both justified
below (L1.3). NOTHING RAN IN THE GAME. Kept for the next stage: `C:/kl_scratch/bank/l1/build/F07+M03_A campaign/`
(201 MB: F01_Main.zip 161,288,648 bytes sha1 d3ad5986..., lightened, briefcases and texts in; result.json, log.txt,
graft.txt, preflight.json). Scratch `C:/kl_scratch/bank/l1/`: `s/` (f07.py, dm.py, dmloc.py, places.py, bounds.py),
`out/` (every output named below). No other file of the repo was touched; kl_fa_author.py is only imported.
Committed as 7fa3910 (tools/kl_fa_bank.py, this section).

### L1.1 What the file is

Pattern: kl_fa_author.py (Retomoto). Its small tools are IMPORTED (`import kl_fa_author as A`: place, setv, ctrl_of,
node_of, rot9 / look9, named, van_path), none of its tables. No new entity, no new controller.

| part | where | what |
|---|---|---|
| the measured bank | `START TRAITOR POLICE STAGE_B/C/D SPAWN HENCH_SHIFT` | 8 START in two stacks of four beside the dock door (x 150..450 and 700..1000, y 200, z -4350), 4 TRAITOR (z -4000), 7 AFTER_DEATH on the front street (west x -1750..-1437, east x 2016..2178), every other kind F07 has (UCC 8 + 4 + 7, team 6 + 4 + 4 + 4 + 7) in rows of their own; 16 player groups |
| loot | `VAULT_LOOT TELLER_LOOT LOOT_REACH GATE_VAULT CASE CASE_SCALE` | 7 in the vault (6 x 300,000 at the deposit-box walls, 500,000 on the trolley's cartons), 4 x 75,000 on the teller counters' public edge = 2,600,000; F07 pool stacks re-used (the last 8 of the 108 + the last 3 of the team 25: 100 + 22 left); radius 125 |
| doors | `LEAVES VAULT_DOOR VAULT_BODY DOORS_ANIMATE DOOR_DY GLASS_LAST VAULT_OPEN VAULT_DOOR_GOES BEAT DOOR_GONE`, class `Doors`, `doors()` | eleven leaves of five sets + the vault door, by exact path with their stock world place |
| host layer | `PLACE PARKED ROLE KEEP_MORE VAN VAN_GROUP VAN_WAIT ESCAPE _KEEP` -> `KEEP`, `DROP` | 39 re-placed objects (markers, planes, cameras, stage boxes, jump points, two back bounds), 12 parked bound boxes, 11 objects with a new job |
| texts | `TITLE TEXTS START_KEY START_FIELDS LINES EXIT_LINE` | 5 .LOC keys of the level's own, 8 briefing / reminder lines, the exit line |
| the interface | `HOST prepare_host strip KEEP DROP layer_names complete wire campaign_names` | as kl_graft.build's docstring asks; `campaign_names` and `strip` keep / strip nothing yet (`NO_AI = True`) |
| the written level | `finish(folder)` | lighten (trim, slim) -> briefcase model into dead chunk indices -> texts |
| checks | `check(folder)`, `inventory(folder)`, `ROUTE_IN ROUTE_VAULT ROUTE_OUT LOOT_WALKS BLOCKS_LIVE KNOWN` | L1.3 |
| commands | `test <out> [--keep] [flags]`, `finish`, `check`, `inventory` | `test` = build + finish + check in one process |

**The round as wired** (MEASURED: `python tools/kl_fa_bank.py inventory <kept folder>` -> `out/inventory2.txt`, and check()'s
'chain' line):
- round start (AIMonitor list 2): F07's `FASpecials!Timer_MissionBriefing` only. wire() WRITES that list: F07's own names
  five timers of its opening, two of which (`RivalMercVan!Timer`, `TimerVanGo`) are ROLE objects here and must not start
  with the round.
- `Gameplay!010_FirstFight!tb_LEFT_TheySpotYou` = the BEAT BOX, at the campaign's own `TB_VbByVault` (460, -714, -12152)
  half (550, 254, 556), ECPS_FA_MERCONLY, field 15 = 1 (0 since Review round 1) -> `RivalMercVan!Timer` (TriggerDelay2 `BEAT` = 48 s) ->
  `Activator_VanSound` (AIDWrapper 'Activate' -> the vault door's group) + `GeomActivator_TearGas_LEFT` (ActivateGeom ->
  the 7 hidden loot objects) + `TimerVanGo` (TriggerDelay2 `DOOR_GONE` = 6 s) -> `GeomDeactivator_DriveInVan`
  (DeactivateGeom -> the door's body `...\SI0102_M03_BankVault_Door_PRE`).
- `Specials!LevelSpeak!TriggerBox` in the foyer -> its speaker, line `Multiplayer/F04/ExitHeist_01_R` ('Get out on the
  street! straight ahead!').
- ENTERS plane 1 m inside the dock door; EXITS plane at the front entrance (M03_FA_A's own ENTERS box there:
  (303, 974, -9407) half (300, 200, 100)); exit trigger `otrExitLevel` over plaza and street (300, 800, -10300) half
  (1500, 300, 900): z -11200..-9400, so it begins 50 beyond the entrance's gap.
- loot marker in the vault, its 11 s box round the START stacks; escape marker at the van's stop (949, 890, -11105), its
  box = hall, plaza and street from y 650 up (NOT the vault lobby under the hall: floor 240, ceiling 640).

**The doors** (the lead's default). `DOORS_ANIMATE = False`: the eleven leaves (dock roller door, glass doors 1 and 2,
four airlock leaves, two hall / foyer leaves) are SUNK 2,500 in world y and their key-framed collision placements cut,
by `Doors` = the study's `G:/kl_scratch/cfa_fill1/build_open.py` as a class: kl_escape.repair / place_entities /
cut_collision wrapped for one build (both traps of re/campaign_fa.md G1.1 kept: the world move is turned into the parent's
frame in the .prp and in the .gms separately, and the two world places are held against each other before and after).
The interface has no place for this, so `prepare_host()` puts the wrappers in (`Doors.arm`) and the last wrapper that
runs takes them out; `with kl_fa_bank.doors(): ...` is the same for a script. `--doors-animate`: the leaves stay, the
round-start event sends each 'Activate' through `Activator_OLD_VanGo`, and the four glass leaves store LAST 50.
THE VAULT DOOR keeps its collision and is the one gate; `--vault-open` sinks it with the others, `--vault-stays` leaves
out the DeactivateGeom.

**The van.** F07's first van only (`VAN` + `ESCAPE` = kl_map_escape.VAN_KEEP + the exit trigger and the two 'last van'
objects); vans 2 and 3 are NOT kept (not 'parked as Retomoto parks unused host objects': a van under the map is the
0x686a66 crash, re/campaign_fa.md 2.1 item 11). Van 1 does not go under the map either: `park_van()` moves its group
so that the van STANDS at the place it will wait at, `VAN_WAIT` (-3248, 702, -11859) (T2.5), and the exit trigger names
it alone. Its drive is still F07's baked one - a first-half state: if the exit trigger fires, the van drives F07's
L-shaped 121 m from there, through whatever stands in the way. The next stage replaces `park_van` by
`kl_map_escape.van_prepare`.

**Texts.** The start window is a TEXT KEY of the level's .LOC (settings fields 12 / 13 / 14 / 15; MEASURED `python
tools/kl_loc.py keys F07 AllLevels/Interface/Online/GameStart`: one `Fxx_FA_Start` per stock level). finish() writes
`AllLevels/Interface/Online/GameStart/M03A_FA_Start / _Team_B_Start / _UCC_Start` and - found while looking for Dead
Men's style (`python C:/kl_scratch/bank/l1/s/dmloc.py "Menu/Online/Scenarios"`) - Dead Men's own unused menu slots
`AllLevels/Menu/Online/Scenarios/TitleDL01` = 'The Vault' and `BriefingDL01` (its stock text: 'Briefing DL01 - Bank
Vault': a vault map that never shipped) = a briefing in the style of its four. Nothing in Dog Days reads those two; they
are there for the menu page. `TITLE` is the constant the menu stage takes.

### L1.2 The build

```
python tools/kl_maps.py one "C:/kl_scratch/bank/l1/build" F07 M03_A --campaign --author kl_fa_bank --keep     (40 s, exit 1 = problems not 0)
python tools/kl_fa_bank.py finish "C:/kl_scratch/bank/l1/build/F07+M03_A campaign"                             (16 s, exit 0)
python tools/kl_fa_bank.py check  "C:/kl_scratch/bank/l1/build/F07+M03_A campaign"                             (26 s, exit 0)
```
or in one process `python tools/kl_fa_bank.py test C:/kl_scratch/bank/l1/build --keep` (85 s, 'RESULT: PASS'; ran so too:
`out/test3.txt`). Lines of the build (`out/build.txt`):
- 'F07 systems (413 subtrees, 9638 nodes) + M03_A map (298 subtrees, 10532 nodes)'; 'verified: 20170 entities, 20171
  nodes, 37054 reachable chunks, 29 room sets, 694 gate / list REF cells, 1866 textures, 1221 materials'
- 'kl_fa_bank: doors: 11 nodes sunk by 2500 (world y) in the joined .prp; 4 of them stand in a parent frame with another
  y axis than the world's' / '11 entities moved in the .gms (0 of them hold another local place there than in the .prp;
  the world places agree); 11 REF ids go to cut_collision' / 'kl_escape: collision of 11 entities taken out of the .HVK
  (placements by shape type: {4: 11})' / '11 placements ... none is left'
- 'Heroes! groups placed where M03_A has them: 0' (the module's own placing stands)
- 'verify: problems: 2'; 'built ... F01_Main.zip, 310 MB, 31 members'
finish (`out/finish.txt`): 'load weight: 1346 dead model roots; .prm 85.7 -> 44.7 MB ...; .TEX 373.9 -> 195.6 MB';
'briefcase M01_FA_A root 6380 (DropMoney!KillDrop!Suitcase) -> chunk 70: 18 chunks into dead indices, 0 at the end';
'7 briefcases in the vault (model 70, x 1.25, its underside 0.3 over its origin); chunk table 64871 entries, as before';
'5 text keys in 8 languages (the English text in each); settings fields [12, 13, 14, 15] name the start windows'.

### L1.3 The checks (all on the kept, finished build; outputs in `C:/kl_scratch/bank/l1/out/`)

| check | command | result |
|---|---|---|
| verify problems | the build's last lines; check()'s 'verify:' lines | **2, both KNOWN**: (1) 'sound: 1 stream clips are not in the merged stream file' = the study's one missing ambience clip (a larger PC_Def.str is the owner's go-ahead); (2) 'FA: BROKEN squads no ZSquadScript: no police' = this half IS a round without enemies. The bare graft has 11 (1 + the 10 findings of a level without a layer): the layer removes the other nine |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | **0 CRASH, 1 BROKEN** = the same 'no ZSquadScript' (the stage asked for 0 BROKEN and for no squads: the two cannot both hold; the next stage's squads remove it). 1 DEGRADED (no bot squads: a later stage). Counts: settings 1, exit trigger 1, monitor 1, animated vehicle 1, AIMonitor 1, OnlineMoneyCtrl 133 |
| cover list | `python C:/kl_scratch/bank/t1/s/covers.py <folder>` -> `covers.txt`; check() | 'exactly 1 FFCoverList' on `ROOT\Special!CoverList`; 20,170 nodes, 711 top-level |
| spawn points | check() (kl_route.stations, near 30) | '79 places, 79 on the mesh part of the START (566 polygons) and on free floor within 30' = 63 ZSpawnPoint + 16 player groups |
| level bounds | check() | '27 bound and warn boxes; 0 of the 98 spawn points, player groups and stations inside one' (it FOUND five on the first build: the campaign's own west warn box reaches x -1805, the study's west police point is x -1842 - the row now begins at x -1750) |
| loot | check() (kl_fa_loot's pick-up test as read at kl2 0x783e60, from floors a walk reaches) | '11 objects, 2600000; 11 can be taken', least 107 of reach to spare; the trolley's case from (130, -959, -13150), 54 away |
| the route as built | `python tools/kl_route.py walk <folder> --from START=250,200,-4350 --via ... --to street=949,702,-11105` -> `route_built.txt` (12 places); check() (18 stations) | 'NOT FREE': the two legs into and out of the vault 'BLOCKED - the thinnest crossing (9 m) goes through' the vault door's body, nothing else; check(): 'route without the vault (yard -> ante-room -> hall -> street), as built: FREE, 208 m' |
| ... the vault door out | the same `--open SI0102_M03_BankVault_Door_PRE_01` -> `route_open.txt` | 'RESULT: FREE; the mesh way: 1084 samples, all free'; check(): 'FREE, 226 m' |
| doors | `python tools/kl_route.py doors <folder> ...` -> `route_doors.txt` | '-> 1 closure(s) in 1 set(s); 1 necessary; with all of them out the way is FREE' (T3's forecast) |
| doors read back | check() | 11 leaves at their stock x / z, 2,500 lower, 0 placements; the vault door at (571, -760, -12509) with 1 |
| the chain | check() | 'round start -> [Timer_MissionBriefing]; ante-room box -> Timer -> [Activator_VanSound, GeomActivator_TearGas_LEFT, TimerVanGo]'; no dead reference in any ROLE object |
| FakeTarget | check() (kl_fa_bots_dyn.vision_space / fake_targets) | 'FakeTarget Animation/F07/F07_Escape_Vehicle_01.zip at (-3243, 701, -11843): inside the vision space, kl2's arithmetic gives a record' |
| chunk table, blocks | check() | 'chunk table: 64871 entries (the tools' line: 69632); .prm 44.0, .fxc 17.8, .ANM 21.6, .WAV 22.9 MB; the five load blocks 139 MB (Retomoto on the tab: 171)' |
| kl_impact | `python tools/kl_impact.py <archive>` -> `impact.txt` | 'problems: 0' |
| preflight | `python tools/kl_maps.py preflight <folder>` -> `preflight.txt` | 'preflight: CRASH 1, RISK 2, NOTE 77': CRASH = 'kl_graft.verify reported 2 problems' (the two above); RISK = 'fa:squads' and 'controller LightToggle x22 ... stock Dog Days: 0 in NO LEVEL' (the study's known first-timer). The bare graft: CRASH 2, RISK 10, NOTE 81 |
| the flags | `python tools/kl_fa_bank.py test <out> --doors-animate --vault-stays` -> `var_animate.txt`; `... --vault-open --loot-shown --loot-bags --beat 30` -> `var_open.txt` | animate: PASS - 12 doors stand, 'route with the 12 standing door(s) out: FREE, 226 m', round start -> + `Activator_OLD_VanGo`, glass leaves LAST 50 (read back). vault-open: PASS - 12 sunk, 'route, 18 stations, the level as built: FREE, 226 m', the loot shown, bags kept, the door's wrapper and DeactivateGeom name nothing (its first run failed on 'five load blocks 181 MB': finish() did not lighten a build that keeps the bags - it always lightens now; run again: 140 MB). Both archives deleted |

check() reads what the BUILD did off the level (a leaf is 'sunk' when it stands 2,500 low), not off the module's flags:
`check <folder>` is right for any variant.

### L1.4 GUESS / ASSUMED (each marked in the file)

- GUESS: every spawn row (the study's places; MEASURED only that each is on the mesh and on free floor), the camera
  places (not looked through), the stage boxes, the two back bounds, the loot's places, turns and values, `BEAT` 48 s,
  `DOOR_GONE` 6 s, the escape box's extent, every wording in `TEXTS`, the choice of `LINES` / `EXIT_LINE`.
- ASSUMPTION: a body switched off by a DeactivateGeom at run time stops colliding (the vault door's guarantee; stock F07
  removes its `BlockVisionPlane` so). If not: `--vault-open`.
- ASSUMPTION: TriggerBox field 15 = 'once' (stock F07's own box -> timer pair has 1, its squad boxes 0): the beat's
  timer must not be started twice. Not read in kl2.exe. **WRONG WAY ROUND - corrected in Review round 1 (R1.1 #4): by the
  stock census 1 = 'for every criminal that enters', 0 = once; the beat box now has 0.**
- ASSUMPTION: the vault door's 'Activate' plays in Dog Days (frames 0..200, one way; G1.8). If the swing plays, the door
  vanishes 3.6 s after it stands open - ugly; `--vault-stays` once it has been SEEN.
- ASSUMPTION carried from the study: a leaf sunk 2,500 under its room does nothing to the room's draw list (G1.6); a
  key-framed body follows its entity (the van's five placements still stand at F07's place: check()'s note).
- GUESS: F07's money bag is a fitting prop on a teller counter; the eight other languages show the English text.
- Not done / not known: nothing was LOOKED AT (no picture of the briefcases or the trolley's case was rendered).

### L1.5 For the next stage

- **Build with `python tools/kl_fa_bank.py test <out> --keep`** from now on: as soon as the van is laid,
  `kl_map_escape.van_layer` has to wrap the build and the plain `kl_maps.py one` cannot do that. In `test()`:
  `with E.van_layer(P, log), doors(log): r = kl_maps.one(...)`. (`doors()` is optional there - prepare_host arms it -
  but tidy.) The plan P needs a BUILT folder for its collision: the kept build of this stage serves
  (`E.van_plan_points("C:/kl_scratch/bank/l1/build/F07+M03_A campaign", log=log, **ROAD)`), unless the layer puts collision
  on the square.
- **The van**: in `prepare_host` replace `park_van(S, log)` by `E.van_prepare(S, P, log)`; in `wire` add
  `E.van_wire(sc, P, log)`; drop `VAN_WAIT`, `park_van`, check()'s van note. `_KEEP` already holds E.VAN_KEEP. T2 also
  wants the box with the define `FAEscCameraLAST` brought by the layer. The 9 static placements of `V_Van_Reflection`
  at F07's origin ((-450, 0, 0) in the bank's world: the back alley, not on the route) are still in this build.
- **Squads**: `campaign_names()` returns the kept squads + single nodes, `strip()` takes the mini-cutscene controllers
  off, `NO_AI` becomes a real flag, `KNOWN`'s second entry goes. Starters: the round start (`wire()`: the list `start`)
  for the dock, the beat timer's list for the reinforcements, a foyer box for the plaza.
- **The beat**: the rods, the alarm, the music and the reinforcements hang on `ROLE['beat timer']` (48 s) or on further
  timers started by `ROLE['beat box']`. Free host objects are listed above `KEEP_MORE` in the file: put the name into
  `KEEP_MORE`, give it a `ROLE`. A ROLE object is automatically kept out of the round-start list.
- **finish()** is where anything goes that needs chunk numbers or the .LOC; a level finished before is left alone
  (the vault loot's model is the test). check() is where a new rule goes; it takes no flag.
- **The vault's own blast** (lead's default: a harmless show) and the PRE -> POST swap are not in this half. The six
  wall places are 100 in front of their walls because the hidden `Vault_POST` has rubble at the walls' feet: with the
  swap, re-run check() (its loot test leaves hidden things out; kl_route counts them unless `--hidden-out`).
- Tables other tools hold per level were NOT touched and nothing of them was needed for this half.

### L1.6 Open

- The 'no ZSquadScript' finding stands until the squads are in; the build command's exit code is 1 until then.
- Vans 2 and 3 are dropped, van 1 stands in sight at the west end of the street with F07's drive (see 'The van').
- The loot is not gated on the vault's guards (there are none) - only on the beat's timer.
- The briefing text and title are in the level's .LOC only; the menu page (kl_expansion's table) is a later stage.
- Team mode / Undercover Cop spawn sets are placed but nothing of those modes was thought through (cameras, stages: GUESS).
- `LightToggle` x22 at load, the 28 rooms, the doors' draw state 25 m under the map: the first live load.

(end of Stage L1)

## Stage L2 - the enemies and the beat (tools/kl_fa_bank.py, second half)

STATE: DONE (2026-10-11 15:35). `tools/kl_fa_bank.py` (1,682 lines) now holds the squads, the hall's police, the beat
(rods, door, loot, alarm, blast, music) and the checks for them; every check of the stage passes on the kept build with
ONE known verify finding (the stream clips: L2.3). NOTHING RAN IN THE GAME (kl2.exe was running: the owner was playing).
Kept for the next stage: `C:/kl_scratch/bank/l2/build/F07+M03_A campaign/` (217 MB: F01_Main.zip 178,166,674 bytes sha1
7948ec14..., finished = lightened + briefcases + texts; result.json, log.txt, graft.txt, preflight.json).
`C:/kl_scratch/bank/l1/build` is deleted. Scratch `C:/kl_scratch/bank/l2/`: `s/` (tops.py, built.py, squads.py, ctl.py,
lists.py, pts.py, loot2.py, floor2.py: what the tables below were measured with), `out/` (every output named below).
No other file of the repo was touched; no table of another tool gained an entry (L2.5).
Committed as c3a1f82 (tools/kl_fa_bank.py, this section).

### L2.1 What was built into the module

| part | where | what |
|---|---|---|
| campaign squads | `SQUAD_ROOTS STAGE START_ROUT HUNT SQUADS_AT SQUAD_ACTIVE`, `squad_plan()`, `campaign_names()`, `strip()`, `snap_men()` | 22 squads / 53 men stay by `kl_fa_author.squad_plan`'s own rule (the real function, its name-root table lent the bank's entry for the call); 83 mini-cutscene controllers come off; every squad waits (`ZSquadScript` field 3 = 0: not in the world until a rout is named) |
| soldier rows | `STOCK_ROWS`, `soldier_rows()` | stock Fragile Alliance rows (`kl_arms.ROWS` by `kl_arms.SKILL`) written in wire(), after kl_arms armed them |
| the hall | `HALL HALL_Y HALL_START`, `place_hall()` | three of F07's own police squads (3 + 3 + 2 men) re-placed in the banking hall |
| the beat | `RODS ROD_FIRST ROD_STEP rod_times()`, `CAMP`, `ALARM_LIGHTS LAMP`, `VAULT_BLAST EXPLODE_REACH BLAST_* blast_lists()`, `MUSIC_* MUSIC_LAYER4`, 16 new `ROLE` entries | below |
| returning police | `POLICE` (moved), `POLICE_CLEAR` | the rows 2 m beyond the plaza squads' men (they stood ON them: 0 apart) |
| loot | `VAULT_LOOT` (two places moved) | a case must lie on bare floor in BOTH vaults (intact / blown) |
| checks | `check()`: 'the beat', 'enemies', 'police who come back', 'people', 'chunk table ... dead'; `KNOWN_NO_AI WARDROBE_CHUNKS ACTORS_LIVE` | L2.3 |
| inventory | `inventory()`: 'THE CAMPAIGN'S KEPT OBJECTS', 'SQUADS' | each squad's stage, each man's weapon and row |
| flags | `test`: `--no-ai --alarm-lights --music-layer4 --blast-real --no-blast --dead-men-rows` | one each, beside L1's six |

**The staging** (MEASURED `python tools/kl_fa_bank.py inventory <kept>` -> `out/inventory.txt`; `python C:/kl_scratch/bank/l2/s/squads.py
<build>` -> `out/squads0.txt` = every squad's nodes, rout lists and rows as converted):

| stage | started by | squads (men) | what they do |
|---|---|---|---|
| start | round-start event -> `start timer` (`SQUADS_AT` 10 s: just after GO) | `3_Garage_Part!PatrolGuards_01a` (2), `4_Vault_Part!Guards_Reinforcement_StayUpstairs` (4), `...#01` (3), `Guards_Reinforcement_01a` (2), `01b` (2) = 13 | their `10_DefendBehaviour`: dock and vault lobby |
| down | the same timer | `Guards_01` (2), `Guards_02` (2), `Guards_03` (2) | defend the upper flight, the cross corridor, the ante-room |
| beat | the ante-room box | `Police_Reinforcement_02` (2), `_03` (4), `Police_Reinforcement_Teargas_01` (1), `...#01` (1), `Vault_Reinforcement_Police_01..03` (6) = 14 | defend places that run DOWN the stairs (e.g. (432, -157, -9414), (202, -559, -10698), (396, -956, -12332)): they come down behind the crew |
| (hunt) | the beat's timer | the five squads with `49_SquadMod` (Police_Reinforcement_02 / _03 / Teargas_01, Guards_Reinforcement_01a / 01b) | unleash + fire at will -> `50_HuntBehaviour`, search box in the vault (427, -733, -12986) |
| hall | the beat's timer | F07 `030_FinancialAlleyExit_Left` (3), `_Right` (3), `030_FinancialAlleyExitStreet_Left` (2) = 8 | stock `10_RunToCover` at re-placed points west / east / before the entrance |
| plaza | the foyer box (`Specials!LevelSpeak!TriggerBox`, with the exit line) | `5_Lobby!Police_OutSide_01` (4), `Police_Outside_Teargas_01` (4), `COOP!Squads_Lobby!Police_OutSide_SWAT_02` (4), `_03` (4), `..._02_ShieldSupport` (1), `..._03_ShieldSupport` (1), `Police_Reinforce_Wave1_COOP_03` (2) = 20 | their flank routs into the hall; the two single SWAT men by `050_Move_In_01` (START_ROUT: squad_plan's pick `080_Cutscene_MoveOutside` is a place ON the van's stop) |

61 soldiers in 25 squads, 9,450 hit points, accuracy 61.8 as used (MEASURED `python tools/kl_map_ai.py table <kept>` ->
`out/map_ai_table.txt`; stock Fragile Alliance: 21..45 soldiers, 2,575..6,120 hit points; F07 34 / 4,640). Rows as
converted: skill NAMES (eN00b 1, eAmateur 24, eRegular 16, eVeteran 12 = accuracy 20 / 35 / 50 / 60 by the name) and
health 50 (13 of them 120); after `soldier_rows`: 15 'cop' (eCustom 50 / 100), 23 'swat' (50 / 175), 15 'sharp'
(75 / 175). Weapons by kl_arms (seed 2026): Rifle_AK74 10, Rifle_FN_SCAR 5, SMGs 18, pistols 15, shotguns 5.
Three men stood 9 - 32 beside the navigation mesh in the campaign's own places; `snap_men` puts them 15 inside it.

**The beat as wired** (MEASURED: check()'s 'chain' and 'the beat' lines, `out/check.txt`; `out/inventory.txt` lines 'THE CHAIN'):
- round start (AIMonitor list 2) -> F07's `Timer_MissionBriefing`, `start timer` (10 s -> 8 routs), `music timer` (1 s ->
  `Special!Audio!PlayMusic_Outside`).
- the ante-room box (ECPS_FA_MERCONLY, field 15 = 1; 0 since Review round 1) -> all at once: `beat timer` (48 s); six `rod timer n` (2, 10, 18,
  26, 34, 42 s; `rod_times()` squeezes them under a short `--beat`) -> `rod n` (AIDWrapper 'Activate' ->
  `M03_A_VaultEntrance_01a\Rod_A01 .. F01`, each rod's own one-way `MatPosAnim`) + the campaign's
  `Special!Audio!GeomActivator_PlaysoundVaultRod01..05` / `...FinalRod`; the 7 start routs of stage 'beat'; the music's
  `03_Ambient` / `03_Intense` fades.
- `beat timer` ends -> the vault door's 'Activate' + `GeomActivator_PlaysoundVaultOpen`; the 7 hidden cases on; the alarm
  (`GeomActivator_PlaysoundAlarm` -> `Audio!3D!Alarm_01 / _02`; `3_Garage_Part!Activator_AlarmRedLights` -> 'Activate' to
  the 11 lamps); the music's `23_*` fade-outs + `PlayMusic_Inside_Part2`; the three hall squads; the five hunts;
  `door timer`.
- `door timer` (6 s) -> the door's body off (L1's guarantee) AND THE BLAST: `BoomBox_BlowVault#01..#03` (each its own
  AIDWrapper -> Explode; #01 a ShakeCamera), `4_Vault_Part!Activator_SetOffAlarm` (the campaign's empty wrapper, now ->
  `Audio!3D!Sound_VaultExplosion`), `post on` (ActivateGeom: 36 objects = the campaign's `GeomActivator_POST_Vault` +
  `GeomActivator_Efx_Geoms` lists: `Vault_POST`, overlays, burnt ceiling, fire and smoke groups, flame sounds, the 'post
  explosion' filter box), `pre off` (DeactivateGeom: 17 of the campaign's 26 = `Vault_PRE` and 16 more; the other 9 are
  the story's plastic bombs and sports bag, not in the build). A door that did not swing is 'blown away'.
- the six rod proxies, the door proxy and every other object of the vault breaker's two `ZMercSquad` are NOT kept: no
  husk was needed (each rod and the door take 'Activate' themselves).

**The three flags the lead asked for, and the fourth**
- `ALARM_LIGHTS = False` (default; preflight called `LightToggle` x22 a RISK): strip() takes the 22 controllers off and
  hides the 22 lights (ZGEOM[3] = 1 + .gms flag 0x400, the form the level's own fire lights have); the lamps still get
  'Activate' (their glow's VertAnim), no light, the vault lobby's white light stays. `--alarm-lights`: the controllers stay,
  `3_Garage_Part!GeomDeactivator_Lights` (white halogen rows off) joins the alarm, as the campaign's `Timer_Alarm` has it.
- `VAULT_BLAST = 'show'` (default): Explode fields 0 / 1 = 1.0 on the three boxes (kl_fa_author.BLAST_HARMLESS's way).
  `--blast-real`: the campaign's 1300 / 1000 and 800 / 800 with field 4 = 30 (MEASURED `python .../s/ctl.py F07 dd Explode`:
  stock grenade 350, RPG 200..300, gas tank 1000 in that field - GUESS that it is the damage: even 'real' is a light hit).
  `--no-blast`: the vault stays intact. The fire is a picture in both (`FireDamageBox` = EffectDmgBox is not kept).
- `MUSIC_LAYER4 = False` (default; NOT asked for - preflight raised it once the music objects were kept: 'RISK value x9
  ZPlayMusicLayerFade[0] = eLayer4; stock has only eLayer1..3'): strip() takes the nine fourth-layer fades' controller
  off and nothing names them. Dog Days' enum HAS the value (MEASURED tools/dd_enums.json enum 155: four names). With
  the clips in the stream file the 'basic' layer (the one that sounds from the start, -14 dB) would play on under the
  way-out set: THE STAGE THAT BRINGS THE MUSIC MUST BUILD WITH `--music-layer4`.
- music clips (silent until the stream file has them; `MUSIC_CLIPS`): `Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav`,
  `..._Layer2_Bass_LOOP.wav`, `..._Layer3_Intense_LOOP.wav`, `..._Layer4_Basic_LOOP.wav` (set BO_Sus_LOOP, 144 s, 36.9 MB),
  `M03_Bustout_ActionV34.wav`, `M03_Bustout_IntenseClimax_Loop.wav` (set M03A_Bustout_A_I, 168 s, 21.5 MB). The build's
  result.json lists 85 clips not in the installed PC_Def.str: these 6, `SFX/Ambiences/M03_A/Inside/
  Ambience_Inside_Vault_Deeper.wav` and 78 guards' / SWAT one-liners (`Dialog/AllLevels/Oneliners/...`, `Dialog/M02 / M03 /
  M08/...Guard*.wav`) - the kept guards' voices. No stream file was built or installed.
  **CORRECTED in Review round 1 (R1.1 #8, R1.2): only 16 of the 85 names have no record in the built .WHD - these 6, the
  ambience and 9 guard lines; the other 69 one-liners stream from the installed merged file.**

### L2.2 The build

`python tools/kl_fa_bank.py test C:/kl_scratch/bank/l2/build --keep` (110 s, exit 0, 'RESULT: PASS', `out/test.txt`). Lines:
- 'M03_A: 12 of 12 door nodes of the route found; 22 squads stay, 83 mini-cutscene controllers taken off them'
- '3 men of the kept squads stood beside the navigation mesh and were put on it: Police_Reinforcement_Teargas_01\Police_01
  14 off, moved 29, Police_Reinforcement_03\Police_04 9 off, moved 24, Guards_Reinforcement_01a\Guard_01#02 32 off, moved 46'
- 'the music: 9 fades of the fourth layer lose their controller'; 'the alarm lamps: 22 lights; their LightToggle taken off
  and the lights hidden'
- 'the banking hall: 3 of F07's police squads re-placed (8 men)'
- 'kl_arms: 53 actors of M03_A armed ...'; 'the vault's blast (show): 3 Explode with reach 1, 36 objects on, 17 off; of the
  campaign's lists 0 / 9 entries are not in the build'
- 'enemies: 22 campaign squads (53 men): round start + 10 s -> 8 routs; ante-room box -> 7; the beat's end -> 5 hunts + 3
  of F07's squads in the hall; foyer box -> 7; stock soldier rows: {'cop': 15, 'swat': 23, 'sharp': 15}'
- 'verified: 20643 entities ... 1903 textures, 1239 materials'; 'verify: problems: 1'; 'level: 20643 entities, 28 rooms, 305 MB'
The plain interface still builds: `python tools/kl_maps.py one <out> F07 M03_A --campaign --author kl_fa_bank` -> 'verify:
problems: 1', exit 1 (`out/one.txt`; then `finish` and `check` on the folder, as in L1).

### L2.3 The checks (all on the kept build; outputs in `C:/kl_scratch/bank/l2/out/`)

| check | command | result |
|---|---|---|
| verify problems = KNOWN | check()'s 'verify:' lines | **1, known**: 'sound: 10 stream clips are not in the merged stream file' (the 85 clip names of L2.1 - 16 really lost, R1.2; the owner's go-ahead). The 'no ZSquadScript' finding of L1 is gone |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | **0 CRASH, 0 BROKEN**, exit 0; 1 DEGRADED (no bot squads: a later stage). ZSquadScript 25 |
| one cover list | `python C:/kl_scratch/bank/t1/s/covers.py <folder>` -> `covers.txt` | '1 FFCoverList' on `ROOT\Special!CoverList`; 20,643 nodes, 768 top-level |
| route | check(); `python tools/kl_route.py doors <folder> --from START=250,200,-4350 --via vault=399,-960,-12818 --to street=949,702,-11105` -> `route_doors.txt`; `... walk ... --open SI0102_M03_BankVault_Door_PRE_01` -> `route_open.txt` | as built 'NOT free', crossed = the vault door's body alone; 'route without the vault ... FREE, 208 m'; 'with the 1 standing door(s) out: FREE, 226 m'; NEW 'route after the blast (the standing door(s) and the 148 bodies the blast takes away out, the blown vault in): FREE, 226 m'. doors: '1 closure(s) in 1 set(s); 1 necessary'. walk: 'RESULT: FREE; the mesh way: 1059 samples, all free' |
| loot in both vaults | check() | '11 objects, 2600000; 11 can be taken in the intact and in the blown vault'; no case 'UNDER' anything. (MEASURED first with `s/loot2.py`, `s/floor2.py`: L1's case at (400, -960, -13310) lay in the blown vault's rubble heap (collision up to y -891) and the trolley with its cartons goes with the intact vault: the south wall's cases are now at x 200 / 300 / 600, the big one at (430, -960, -12950)) |
| every man on the mesh | check() (kl_route.stations near 30, the standing door out) | '22 campaign squads (53 men) + 3 of F07's in the hall (8 men); 61 of the 61 men on the mesh part of the START and on free floor within 30' |
| the places their routs name | check() | '83 places their behaviour routs name; 7 not on the START's mesh part': all the campaign's own - five hunts' `SearchBox` (427, -733, -12986), a volume 227 over the vault's floor, and `Pos#01` (71, 241, -6855) of two squads, 7 beside the mesh. The hall's 11 points are all on it (a hall point off it is a FAIL) |
| no dropped node named | check(); result.json | 'dangling' [] in result.json; no list of any squad node, CAMP node or ROLE object names a node that is not there |
| behaviour kinds | check() | 'controllers of the squads: ZSquadScript 25, SquadModifierBehaviour 35, DefendBehaviourRout 32, ZSoldier 61, HuntBehaviourRout 5, FlankingBehaviourRout 5, RunToCoverBehaviourRout 3, RunToCoverPosInfoRout 8': all in kl_fa_author.PLAIN / BEHAVE (the kinds Retomoto's layer ran live); no first-timer |
| squads start where they should | check() | 'started by: {start timer: 8, beat box: 7, speak box: 7, beat timer: 3}; 5 hunts at the beat's end'; every squad's field 3 is 0 |
| rows | check() | 'soldier rows of the campaign's men: 23 x eCustom 50 / 175, 15 x eCustom 50 / 100, 15 x eCustom 75 / 175' |
| the beat's chain | check() | 'chain: round start -> [Timer_MissionBriefing, Timer, Timer]; ante-room box -> rods at 2, 10, 18, 26, 34, 42 s, 9 more -> 48 s -> 18 objects; -> 6 s -> [GeomDeactivator_DriveInVan, BoomBox_BlowVault#01, #02, #03, Activator_SetOffAlarm, GeomActivator_TearGas_RIGHT, GeomDeactivator]'; 'the beat: vault door swings at the beat's end, its body off 6 s later; blast show: Explode reach [(1.0, 1.0)], 57 bodies come, 148 go; alarm lamps 11, no LightToggle in the level, 22 lights hidden; music: break-in set at 1 s, way-out set at the beat's end; 0 fades of the fourth layer' |
| police who come back | check() | '8 bodies, 7 AFTER_DEATH points; the nearest of the squads' men stands 214 from one' (before the move: 0). The 8 bodies are F07's eight `Heroes!Henchmen_0n`: nothing here adds a police body |
| actors against the limits | check() | 'people: 61 ZFFActor in 25 squads + 16 player bodies (ran live: 99 actors, 55 squads)' (re/campaign_fa_tooling.md 5.4: stock Fragile Alliance 35..57 actors) |
| chunk table, blocks | check() | 'chunk table: 65640 entries (the tools' line: 69632); .prm 53.2, .fxc 17.8, .ANM 21.9, .WAV 23.1 MB; the five load blocks 149 MB (Retomoto on the tab: 171)'; 'chunk table: 23690 of its indices are dead (free for the wardrobe, which took 15509 on the study's build, and the gun looks)' |
| kl_impact | `python tools/kl_impact.py <archive>` -> `impact.txt` | 'problems: 0' |
| kl_arms | `python tools/kl_arms.py check <archive>` | '0 findings' |
| preflight | `python tools/kl_maps.py preflight <folder>` -> `preflight.txt` | **'preflight: CRASH 1, RISK 0, NOTE 78'**: CRASH = 'kl_graft.verify reported 1 problems' (the known one). L1 had RISK 2 (`fa:squads`, `LightToggle` x22); with the music kept and the fourth layer's fades left in it is RISK 1 ('value x9 ... eLayer4') |
| NO_AI still builds | `python tools/kl_fa_bank.py test <out> --no-ai` -> `var_noai.txt` | 'RESULT: PASS': 20,246 entities, 'verify: problems: 2' both known ('sound: 1 stream clips ...', 'no ZSquadScript' = `KNOWN_NO_AI`, which check() accepts only when the level has no squad); 'enemies: none (a build without squads)'; the beat, loot, blast and music as with them |
| every flag on | `... test <out> --alarm-lights --music-layer4 --blast-real --doors-animate --vault-stays` -> `var_all.txt` | 'RESULT: PASS': 12 doors stand, 'route with the 12 standing door(s) out: FREE, 226 m', 'blast REAL: Explode reach [(800.0, 800.0), (1300.0, 1000.0)]', 'alarm lamps 11, 22 LightToggle', '9 fades of the fourth layer', the door timer names the blast alone |
| every flag the other way | `... test <out> --no-blast --vault-open --loot-shown --loot-bags --beat 30 --dead-men-rows` -> `var_plain.txt` | 'RESULT: PASS': 'route ... the level as built: FREE, 226 m', 'rods at 2, 7, 12, 16, 21, 26 s ... -> 30 s', 'blast none (the vault stays intact)', Dead Men's rows read back (16 x eAmateur 50 / 50 ...) |

Variant archives are deleted; only the default build is kept.

### L2.4 GUESS / ASSUMED (each marked in the file)

- GUESS: the split of the 22 squads over the stages; `SQUADS_AT` 10 s (on two clock readings of 8.4 - 8.8 s between the
  round-start event and GO); `ROD_FIRST` 2 / `ROD_STEP` 8; every point of `HALL` (MEASURED only: on the START's mesh part,
  on free floor); `MAN_OFF` 60 / `MAN_IN` 15; `POLICE_CLEAR` 100; the new police rows at z -9900; the two moved loot places.
- GUESS: Explode fields 0 / 1 are its reach and field 4 its damage (by the stock rows; not read in kl2.exe).
- ASSUMPTION: a squad whose field 3 is 0 is not in the world until a rout of it is named (re/map_ai.md 2; seen live on
  Retomoto) - the whole staging rests on it, and the round's first seconds (no fire through the open dock door in the
  countdown).
- ASSUMPTION: a hidden light (ZGEOM[3] = 1, flag 0x400) does not shine. If it does: eleven red lamps lit all round.
- ASSUMPTION: an ActivateGeom brings the blown vault's collision and a DeactivateGeom takes the intact one's away (L1's
  for the door). The route and the loot are tested in both states AND with both vaults standing at once (kl_route counts
  hidden bodies), so only 'the intact floor goes and the blown one does not come' would hurt; `--no-blast` avoids it.
- ASSUMPTION: TriggerBox field 15 = 'once' (L1's; **wrong way round, see R1.1 #4: 0 is 'once' and is written now**). The ante-room box now also names seven squads' routs and two fades;
  if it fires again, the timers restart or fire twice - door, loot and blast named twice, nothing that breaks.
  The foyer box is F07's speak box as L1 left it (field 15 untouched): a criminal who re-enters it re-names the plaza
  squads' start routs.
- ASSUMPTION: a second PlayMusic does not stop the first (why MUSIC_LAYER4 matters once the clips play).
- ASSUMPTION: an AIDWrapper 'Activate' plays a hidden ZSNDOBJ (`Sound_VaultExplosion`): the campaign's own
  `Activator_BlowVault` sends it so; stock F07 sends 'Activate' to its van and shutter sounds.
- Not known: whether the postfilter boxes `Inside_VaultPreExplosion` / `...PostExplosion` (in the campaign's own lists,
  kept as they are) change the picture under F07's palette; whether the two rigid bodies in those lists (a chair, a
  stack of forms) behave when shown at run time.
- The men's strength is a first setting: 9,450 hit points is 1.5 times the hardest stock level's, staged in five waves.
  The knobs: `--dead-men-rows`, kl_arms.ROWS, the hook's [Balance].

### L2.5 kl_arms / kl_map_ai: what the enemy tools needed

- kl_arms: NOTHING added to its tables. `kl_arms.arm` arms M03_A's 53 by its general rules (no zone numbers in the
  bank's squad names: depth 0.5 for all); its stock-row pass is tied to `SKILL_LEVELS` (Retomoto) and would skip ten
  police whose first float is 2 - the rows are written from this module instead (`soldier_rows`, reading
  `kl_arms.POOLS / SKILL / ROWS`). `kl_arms.py check`: 0 findings.
- kl_map_ai: `table` and `balance` run on the build as it is. `apply` wants `PLANS['M03_A']`; NO plan is given, on
  purpose: its `STRENGTH` floors are made for maps of 12 - 15 men (rifles -> accuracy eElite 90) and would lift the
  bank's 19 riflemen to 99 as used. A stage that wants its 'chains' / 'escape' parts sets
  `kl_map_ai.PLANS['M03_A'] = {...}` from a script and calls `apply(..., parts=('chains', 'escape'))`.

### L2.6 For the next stage

- **Build**: `python tools/kl_fa_bank.py test <out> --keep [flags]`; `check <folder>` is right for any variant (it reads
  what the build did off the level). The first live run: `--no-ai` first (a round without enemies), then the default.
- **The van** is still L1's (parked at `VAN_WAIT` with F07's drive): L1.5's three lines stand. The plan's lane is on the
  street; nothing of this stage stands on it (the plaza squads' start places are z -9686..-9397, the police rows z
  -10220..-9900, the lane z -12332..-11105). The two single SWAT men's unused `080_Cutscene_MoveOutside` points ARE on
  the van's stop: do not name that rout.
- **Bots** (kl_fa_bots): the loot places changed (L2.3); the round has two vault states; `Gameplay!merc_bot_squad!*` is not
  kept yet (check() lists squads that are not this file's without failing). The ante-room box is MERCONLY.
- **Free F07 objects left**: six TriggerDelay2 under `Gameplay!010_FirstFight!Shutters!`, three under `Gameplay!RunToEscape!`,
  the trigger boxes and counters listed over `KEEP_MORE`. NO AIDWrapper / ActivateGeom / DeactivateGeom of F07 is free;
  the campaign has single ones that stay when `CAMP` names them.
- **Music stage**: `--music-layer4`, the 16 clips of R1.2 (not the 85 names of L2.1), `kl_str.py` (the owner's go-ahead).
- **Wardrobe**: 23,690 dead chunk indices are free (it took 15,509 on the study's build, without the four plates; with them 20,989 - F.4, R1.1 #9); table 65,640 of 69,632.

### L2.7 Open

- Nothing ran in the game. Live only: do the squads come into the world when named and stay out before; do the rods and
  the door move; the blast's look and whether 'show' is harmless; the alarm with hidden lights; the hall's eight men at
  guessed points; the plaza under 20 men; how hard 61 soldiers are.
- The van (drive, camera, boarding) and the AI heisters are later stages; `kl_fa.check` has 1 DEGRADED (no bot squads).
- The campaign squads' retreat routs (`40_DefendBehaviour_Moveback`), the hall squads' `40_RunToEscape` and the ring
  round the van F07 runs its police to are not wired; no 'wiped out' chain (ZSquadScript field 8) is written.
- Team mode / Undercover Cop: nothing of this stage was thought through for them (the squads' game-type fields are the
  campaign's 'all types'; F07's eight are FragileAllianceOnly / FragileAllianceUCC as stock).
- `check()`'s FakeTarget test still leans on kl_fa_bots_dyn (another session's file).

(end of Stage L2)

## Stage L3 - the escape (tools/kl_fa_bank.py: F07's van on stage T2's way-point plan)

STATE: DONE (2026-10-11 16:10). Built on stage L2's module state (c3a1f82). `tools/kl_fa_bank.py` lays F07's first
key-framed van on the passing plan of T2.4, and check() has a block 'the escape'; every check of the stage passes and
all of L1's / L2's still do ('RESULT: PASS', the same one known verify finding) - with ONE wish of the stage NOT met:
the waiting van is not out of sight (L3.4). NOTHING RAN IN THE GAME (the owner was playing). Kept = 'the bare map' the
finishing stage starts from: `C:/kl_scratch/bank/l3/build/F07+M03_A campaign/` (217 MB: F01_Main.zip 178,157,778 bytes
sha1 5f11b846..., finished = lightened + briefcases + texts; result.json, log.txt, graft.txt, preflight.json, NEW
van.json). `C:/kl_scratch/bank/l2/build` is deleted. Scratch `C:/kl_scratch/bank/l3/`: `s/` (stockbound.py, stockexit.py,
sight.py, defs.py, stockesc.py), `out/` (every output named below).
No other file of the repo was touched; kl_map_escape.py is only called (T2's front end, unchanged).
Committed as c9c3847 (tools/kl_fa_bank.py, this section).

### L3.1 What was changed (one file)

| part | where | what |
|---|---|---|
| the road | `ROAD` (replaces `VAN_WAIT`) | T2.4's passing plan as way points: `arrive` = the first three points of the designers' in-road, `stop` (949, 704, -11105) at = origin, `leave` = their away road + its line carried on to x 8600; heading and camera not forced |
| the plan | `van_plan(src)`, `plan_of(file)`, `lay_van(P)`, `PLAN` | `kl_map_escape.van_plan_points(src, **ROAD)`, a fault is an error; a plan from a file is refused when its way points are not ROAD's |
| the build | NEW `build(out, log, plan=None)` | bare graft into `<out>/_bare` (60 s, 310 MB, deleted again) -> plan -> `with kl_map_escape.van_layer(plan), doors(): kl_maps.one(...)`; -> (result, folder, plan, what was done to the van) |
| the layer | `prepare_host()` | `park_van()` is gone: `kl_map_escape.van_prepare(S, PLAN, log)` (F07's 563 position and 550 rotation keys rewritten in place, 19 objects moved with the drive); the escape marker `POI_TheEscapeArea` is put `ESC_POI_UP` = 188 over the PLAN's stop |
| | `wire()` | `kl_map_escape.van_wire(sc, PLAN, log)`: the exit trigger's field 0 false, field 2 the van's group, 1 and 3..5 empty |
| | `PLACE['Gameplay!EscapeSetup!otrExitLevel']` | the box carried 500 farther south: (300, 800, -10550) half (1500, 300, 1150) = z -11700..-9400 (L3.3: it did not hold the boarding place) |
| test | `test(out, keep, log, plan)`, `--plan FILE` | writes `van.json` beside the archive (kl_map_escape.van_build's form: tag, plan, van, wired, hvk, check) |
| check | check(): 'the escape'; `BOARD_NEAR LANE_CLEAR BOUND_AFTER` | L3.2 |

`python tools/kl_maps.py one <out> F07 M03_A --campaign --author kl_fa_bank` ALONE NO LONGER BUILDS: it stops in
prepare_host with "kl_fa_bank: the van has no plan: build with 'kl_fa_bank.py test <out>' or kl_fa_bank.build() ..."
(`out/one.txt`): the plan needs a built level without the layer, and the van's collision placements are set in
kl_hvk.join, which no name of the module interface reaches. From Python: `kl_fa_bank.build(out)`.

**The van as built** (MEASURED: `van.json`, the build's lines in `out/test_final.txt`, check()'s lines in `out/check.txt`):
- plan = T2's to the last digit, all 594 path points too (`C:/kl_scratch/bank/t2/out/plan_through.json` against this
  build's van.json): waits (-3248, 702, -11859) heading 101.6 -> 48.05 m in 7.2 s -> stops (949.1, 702.0, -11105.0)
  heading 67.3 -> 70.68 m in 8.48 s -> ends (8000, 702, -11172.9) heading 90; 0 faults, lane empty on the first pass;
  camera eye (-711.5, 1030, -11799.6) (cam_spot: GUESS).
- 'kl_map_escape: ... 563 position and 550 rotation keys rewritten in place (391 of them the drive, stop at key 159);
  drive in 5063 -> 4805 (x 0.95), away 7019 -> 7068 (x 1.01); crash pieces -120..120 to the side; 19 objects moved:
  PathBlockerVan, CameraTrigger_InVan, CamPos_InVan_FocusPoint, TriggerBox_RearDoors_Open, CameraTrigger01, CamPos01,
  EscCamera01_01, V_Van_00, V_Van_Reflection, 8 Smear_*, 2 ShadowCaster_Van*' (the last eleven are the loose pieces,
  put at y -60000; none carries a controller). Speed away 8.3 m/s mean, 14.8 top (stock F07: 14.7).
- 'exit trigger Gameplay!EscapeSetup!otrExitLevel calls Animation/F07/F07_Escape_Vehicle_01.zip\EscapeVehicle_Animation_F07'
- '.HVK: 9 static placements of the van's subtree cut, 5 key-framed placements of the van put at its waiting place'
  (.HVK 3,697,040 -> 3,260,320 bytes: L1's and L2's builds still had the reflection template's placements and their
  filler copies). No collision placement stands away from its entity any more; check() fails any that does, the van's
  included (L1's note about the van's five is gone).
- THE ROUND'S LAST STAGE is F07's own, as the graft leaves it (MEASURED `python C:/kl_scratch/bank/l3/s/stockesc.py F07`
  -> `out/stock_f07_esc.txt`, against the build): `OnlineEscVehicleMonitor` list 2 `Specials!Audio!EscSoundHandling!Activate`,
  list 3 `RelayDestroyedEsc_01` (stock: _01.._03), list 8 the 'last van' message and its 4 s timer, the others empty as
  in stock; `OnlineEscAnimatedVehicle` field for field stock's (its boarding box, the six messages, 7.2 / 8.0 / 8.48 /
  6.0). The car maps on the tab have the same exit-trigger form (`out/zfinal_m03_esc.txt`: field 2 the van, 3..5 empty).
- F07's SECOND AND THIRD VAN ARE NOT IN THE LEVEL (L1's decision, kept: 'parked safely' = not there, the form of the
  three car maps): one `OnlineEscAnimatedVehicle`, one `FakeTarget`; check() fails any other count.
- Against L2's build (`python C:/kl_scratch/bank/t1/s/manifest.py diff out/l2.manifest.json out/l3.manifest.json` ->
  `out/l2_l3_diff.txt`): 27 of 31 archive members equal by name, size and CRC; `.HVK`, `.buf` (the keys), `.gms`,
  `.prp` differ; every file beside the archive equal but log.txt / result.json, + van.json.

### L3.2 The checks (all on the kept build; outputs in `C:/kl_scratch/bank/l3/out/`)

| check | command | result |
|---|---|---|
| build + finish + check | `python tools/kl_fa_bank.py test C:/kl_scratch/bank/l3/final --keep` -> `test_final.txt` (150 - 210 s: bare graft, plan, build, finish, check; on the file as committed) | **'RESULT: PASS'**, exit 0; 20,643 entities, 28 rooms, 'verify: problems: 1' (the known stream clips). Its archive = the kept build's member for member ('31 members / 31 members, 31 equal', the same 178,157,778 bytes; the kept one was built with `--plan out/van1.json`: `test2.txt`); deleted |
| check alone | `python tools/kl_fa_bank.py check <kept>` -> `check.txt` | 'PASS', exit 0 |
| van-check | `python tools/kl_map_escape.py van-check <kept>` -> `van_check.txt`; inside check() with the plan | **'0 fault(s)'**: 'keys 0.0 off the road height at most, largest step 59, nose up to 1.1 degrees off the tangent (7.2 if a key is held, not interpolated), crash pieces up to 120 to the side; lane (5 rays, every 20, 350 before and 600 beyond): clear'; 'boarding box at the stop: (636, 702, -11230); key-framed placements 5, at most 1.1 from their entities'; '.HVK 3260320 bytes'; wait / stop / end within 25 of the plan's. One note: 'no define FAEscCameraLAST' = the STOCK form (L3.3) |
| the lane | the plan's own test on the bare graft (`test_final.txt`, 'van plan for ...') and van_check's on the layered, finished build | both clear, plan faults 0. Nothing of the layer stands near it: 'of 61 spawn points, player bodies and men at the street's height the nearest to the drive is ...SpawnPoint_TEAM_Police#06, 971 from it' (`LANE_CLEAR` 250) |
| fake-test | `python tools/kl_fa_bots_dyn.py fake-test <work>/build/z_route/M01 <work>/build/rt_full6/retomoto_full <kept>` -> `fake_test.txt` | **'RESULT (fake-test): PASS (grid control 1, parked control 1, lattice 3)'**; the bank: 'FakeTarget Animation/F07/F07_Escape_Vehicle_01.zip at (-3264.2, 702.0, -11855.6): inside; kl2's arithmetic: cell (8, 0, 3) (a record)', the only FakeTarget of the level; vision space x -21046..11362, y -960..5589, z -16592..5011. check(): the same at the load, and 'on the drive: at the stop inside; at the end of the drive inside' |
| the boarding place | check() (`kl_route.stations` near 30, `kl_route.route`); `python tools/kl_route.py stations <kept> START=250,200,-4350 "boarding place=636,702,-11231" "van stop=949,702,-11105" "van waits=-3248,702,-11859" --near 30 --open SI0102_M03_BankVault_Door_PRE_01` -> `route_stations.txt` | 'boarding place at the stop (636, 702, -11231): mesh True, part 0 (the START's: 0), free floor within 30: True; the van's stop: mesh True, part 0; hall -> front entrance -> plaza -> boarding place in the collision: FREE, 25 m'. stations: '4 of 4 on the mesh, on 1 part(s)'; the WAITING place is 'NOT reached ... behind REF 12341 Body\Body_Main [KEYFRAMED ...]' (exit 1 for that): the van's own body stands there in the file, as it should |
| the whole round to the van | `python tools/kl_route.py walk <kept> --from START=250,200,-4350 --via vault=399,-960,-12818 --via hall=377,801,-8423 --via "front entrance=300,800,-9350" --to "boarding place=636,702,-11231" --open SI0102_M03_BankVault_Door_PRE_01` -> `route_open.txt`; the same places with `doors` -> `route_doors.txt` | 'RESULT: FREE; the mesh way: 1064 samples, all free' (front entrance -> boarding place: 'FREE, 18 m of cells, floor y 700..800', mesh way 20 m, narrowest shared edge 310); doors: 'RESULT: 1 closures in 1 sets, 1 necessary' (the vault door) |
| stop height | check() | 'the stop: origin y 702.0, the road under it y 700.0 (S00701_M03_Square_PlaneA_02); keys at most 0.0 off the road's height on the whole drive; drive in 48 m, away 71 m' (the origin stands `VAN_UP` = 2 over its road, as F07's) |
| path blocker | check() | 'PathBlockerVan at (952, 817, -11100) half (101, 130, 250): the boarding place is outside it' (stock: outside on 12 of 12 vans, `out/stockexit.txt`) |
| exit box | check(); `python C:/kl_scratch/bank/l3/s/stockexit.py F07 F01 F04 F05` -> `stockexit.txt` | 'exit trigger(s) ['otrExitLevel']: holds the hall False, the front entrance False, the plaza True, the van's stop True, the boarding place True; drive in 7.2 s' (L3.3) |
| the bound at x 3763 | check(); `python C:/kl_scratch/bank/l3/s/stockbound.py F07 F01 F04 F05 F09` -> `stockbound.txt` | 'the drive passes the level bound LevelBound_Outside_Left 26.1 .. 30.4 m after the stop: players aboard - the stock form'; '... LevelBound_Outside_Right 46.3 .. 41.3 m before the stop: the van is empty there'; neither the stop nor the boarding place in one of the 27 bound and warn boxes (L3.3) |
| the camera | `python tools/kl_map_escape.py check <kept>` -> `escape_check.txt` | '0 fault(s)': 'EscCamera01_01 ... mode eFMM_LookFromPos ... Dog Days' eye: (-711, 1030, -11799), 330 over S00701_M03_Square_PlaneA_02; looks at the player' - F07's own camera IS in the mode kl_map_escape.fix_cameras gives a Dead Men one, so there is nothing to repair; the in-van camera eFMM_LookAtPos as stock. Clear sight to the stop; it does not see the end of the drive (T2.4) |
| is the waiting van out of sight | check(); `python C:/kl_scratch/bank/l3/s/sight.py <kept>` -> `sight.txt` | **NO**: 'waits at (-3248, 702, -11859), 43 m from its stop; from front entrance: hidden by SI0102_M03_Column_A_01...; from plaza: SEEN (41 m); from the boarding place: SEEN (39 m)' (L3.4) |
| L1's / L2's checks | check() on the kept build | all as L2.3: verify 1 known; 79 spawn places on the mesh; 27 bound boxes, 0 of 98 places inside; loot 11 / 2,600,000 takable in both vaults; route as built crossed = the vault door alone, 'FREE, 226 m' with it out and after the blast; 22 + 3 squads, 61 of 61 men on the mesh; staging; beat chain; police who come back 214 clear; 61 actors in 25 squads; chunk table 65,640 entries, 23,690 dead; five load blocks 149 MB |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | exit 0: 0 CRASH, 0 BROKEN, 1 DEGRADED (no bot squads) |
| kl_impact / kl_arms / cover list | `kl_impact.py <archive>`, `kl_arms.py check <archive>`, `C:/kl_scratch/bank/t1/s/covers.py <kept>` -> `impact.txt`, `arms.txt`, `covers.txt` | 'problems: 0 in 1 levels'; '0 findings'; '1 FFCoverList' |
| preflight | `python tools/kl_maps.py preflight <kept>` -> `preflight.txt` | 'preflight: CRASH 1, RISK 0, NOTE 78' (CRASH = 'kl_graft.verify reported 1 problems', the known one): as L2 |
| the flags | `python tools/kl_fa_bank.py test <out> --no-ai --plan out/van1.json` -> `var_noai.txt`; `... --alarm-lights --music-layer4 --blast-real --doors-animate --vault-stays --plan ...` -> `var_all.txt`; `... --no-blast --vault-open --loot-shown --loot-bags --beat 30 --dead-men-rows --plan ...` -> `var_plain.txt` | 'RESULT: PASS' three times, exit 0; archives deleted |

### L3.3 What the stage found beside laying the van

- **THE BOUND ON THE DRIVE AWAY IS THE STOCK FORM** (re/campaign_fa.md 5 item 9 and re/map_escape.md V5 had it open).
  MEASURED on the stock levels' own files (`stockbound.py`: each stock van's keys against its level's `LevelBound`
  boxes, 100 over the key): every one of the 15 vans of F01 F04 F05 F07 F09 passes one bound box on its drive in and
  ANOTHER on its drive away, 10.9 m (F01) .. 105 m (F09) after its stop, F07's own three 18.6 .. 39.8 m - with its
  passengers aboard. The bank's 26.1 .. 30.4 m is inside that. Nothing is moved; `BOUND_AFTER` = 1000 is check()'s
  rule (a bound nearer the stop than the nearest stock one would be new ground). What a bound does to a player on
  foot is still not read.
- **THE EXIT BOX DID NOT HOLD THE BOARDING PLACE.** STOCK (`stockexit.py`): the exit trigger's box holds the stop AND
  the boarding box (at the stop) of every van, 12 of 12 on F01 F04 F05 F07 (boxes 65 - 90 m long). L1's box ended at
  z -11200, the boarding place is at z -11231: the first build of this stage said 'the boarding place False'
  (`test1.txt`). The box now reaches z -11700; check() fails a build where it does not hold both. What the trigger
  does with a player inside it beyond calling the van was not read - this follows stock.
- **NO DEFINE `FAEscCameraLAST` IS THE STOCK FORM**, not a gap (T2.5 asked the layer to bring the box): MEASURED - the
  .prp of stock F07, F02 and F05 hold no such string. It is Dead Men's box, which the three car maps kept with their
  maps. Nothing is brought; kl_map_escape.van_check's note stays (that tool's) and check() prints the reason under it.
- A registered FakeTarget that leaves the grid is harmless (re/crash_686a66.md: 0x79bae0), and here it does not even
  leave it: the stop and the end of the drive (x 8000) are inside the vision space (x up to 11362).

### L3.4 GUESS / ASSUMED (each marked in the file), and the one wish not met

- **NOT MET: 'out of sight'.** The van waits in plain sight at the west end of the front square, 41 m from the plaza
  (as the Fragile Alliance bank's van waits 'up the road', which the owner has played). MEASURED (`sight.py`: six eyes
  - front entrance, plaza, steps, kerb, boarding place, stop - to the van 60 and 200 over the road; a 'ColiObj' is not
  drawn and does not count): the square is OPEN. Farther back on the in-road's own line the floor runs on (ground y
  700 at 6, 12, 20 and 30 m; a planter at 40), and at none of the five distances is the van hidden from all six eyes:
  planters and palm trunks hide its lower part from more and more of them (at 30 m: from all but the steps, which
  still see its roof), nothing hides the whole of it. kl_map_escape's `LIMIT_IN` (60 m of drive in for the 7.2 s of
  F07's keys, a GUESS itself) allows 12 m more. So 'out of sight' is not to be had on this square by a longer in-road;
  it would take a blind (a parked truck, a kept campaign car) or another way in. The lead's call; nothing was tried.
- GUESS (T2's, now the map's): the leave leg's extension east to x 8600 (collision floor and furniture MEASURED; what
  is DRAWN in the lane out there was not looked at), the camera's eye (cam_spot), the stop's heading 67 (the curve's).
- GUESS: `LANE_CLEAR` 250, `BOUND_AFTER` 1000, `BOARD_NEAR` 30 (the spawn points' measure).
- GUESS (L1's, moved): the exit box's extent. It begins 50 beyond the entrance's gap: the van is called the moment a
  criminal steps onto the plaza and stands 7.2 s later; the kerb is 18 - 20 m from the entrance.
- ASSUMPTION (kl_map_escape's, unchanged): a key-framed body moves with its entity (the file is right either way);
  the Catmull-Rom curve; the engine interpolates rotation keys (the nose is 1.1 degrees off the tangent if so, 7.2 if
  a key is held).
- NOT KNOWN: the waiting van stands ON the navigation mesh (part 0) and its path blocker stands at the STOP: nothing
  tells the AI about the van's body at the waiting place. Whether stock vans wait on the mesh was not measured.

### L3.5 For the next stage

- **Build**: `python tools/kl_fa_bank.py test <out> --keep [flags] [--plan <van.json>]`; from Python
  `r, folder, plan, did = kl_fa_bank.build(out)`, then `finish(folder)`, `check(folder)`.
  `--plan "C:/kl_scratch/bank/l3/build/F07+M03_A campaign/van.json"` saves the bare graft (60 s) as long as ROAD is
  unchanged (plan_of refuses the plan of another road).
- **Whoever copies the build folder copies van.json with it**: check() holds the drive against its plan (without the
  file the drive is tested as the level has it, and a line says so).
- **Bots** (kl_fa_bots): the boarding place at the stop is (636, 702, -11231) (`van.json` 'check' 'board'; the plan's:
  (638.3, 700, -11235.3)); in the FILE the box rides on the van at the waiting place (re/map_escape.md 12 / 15).
  van.json has kl_map_escape.van_build's keys ('plan' has 'points'; 'car' None, 'drop' and 'exits' empty): the bot,
  talk and tune tools that read a van_build folder's van.json were NOT run on it.
- **Anything a later stage puts on the square** (cover boxes, bot stations, a kept car): run check() again -
  van_check's lane sees collision under 'Locations/' and convex bodies, `LANE_CLEAR` sees spawn points, player bodies
  and squads' men only.
- Still not wired (L2.7): the squads' retreat routs and F07's police ring at the van's call; the vehicle monitor's list
  4 is empty (the Fragile Alliance bank has four squad routs there: `out/zfinal_m03_esc.txt`).
- The first live questions of this stage: does the van show at the west end and drive in when the plaza is entered;
  'Get in' at the rear doors; the in-van view, then the fixed camera; the east bound 26 m into the drive away; the
  score page.

### L3.6 Open

- Nothing ran in the game.
- 'Out of sight' (L3.4): the lead's call.
- What is drawn east of x 3958 along z -11173 (the leave leg's extension) was not looked at: a render (tools/kl_view.py)
  or the first live run shows it.
- The escape camera's picture.
- The `LightToggle`, door-animation and blast questions of L1.6 / L2.7 are untouched.
- check()'s FakeTarget test still leans on kl_fa_bots / kl_fa_bots_dyn (another session's files; it prints 'NOT
  CHECKED' if their names change - then run the fake-test command of L3.2).

(end of Stage L3)

## Stage F - the finishing chain: wardrobe, the seven AI heisters, gun looks, talk, the load weight (tools/kl_fa_bank.py: `bots`)

STATE: DONE (2026-10-11 17:00). Four folders are DELIVERED in `<work>/build/c_bank/` (0.93 GB): `bank_vault`,
`bank_vault_wavslim`, `bank_vault_noai`, `bank_vault_bare`. Every checker passes on the three finished folders
EXCEPT the two that repeat the build's ONE known verify finding (`kl_maps.py preflight` 'CRASH 1' and
`kl_maps.py audit` 'FAIL (2 ...)': the stream clips of L2, the lead's default 3; on the no-AI folder also its 'no
police', which is what that build is). NOTHING RAN IN THE GAME (the owner was playing). No file of another session
was edited and no table of another tool got an entry: the bank's bot data is passed in from `tools/kl_fa_bank.py`.
Tools as run: the working tree at d560c53 (tools/kl_chars.py carries another session's uncommitted change; it was
RUN as it stands). Scratch `C:/kl_scratch/bank/f/`: `s/` (chain.sh, checks.sh, blocks.py - copies lie in c_bank),
`out/` (every output named below); every intermediate archive is deleted.
Committed as 784df6e (tools/kl_fa_bank.py, this section).

### F.1 What was changed (one file, `tools/kl_fa_bank.py`)

| part | what |
|---|---|
| NEW `bots(src, dst)`, command `bots <finished folder> <out>` | the seven AI heisters into a copy: `kl_fa_bots.build` with `BOT_OPT` (the M03_FA_A row of kl_fa_bots.RECIPE without its drop, one loot stop, 30 s) and THE VAULT GATE. `kl_fa_bots.plan` is wrapped for the length of the one build (as `Doors` wraps kl_escape): no line of kl_fa_bots.py is changed and no 'M03_A' entry was needed in it |
| NEW `bots_gate(B, P)`; `GATE_AT GATE_REACH GATE_MORE GATE_NAME GATE_CLEAR BOT_SQUAD` | the plan's last way station before the loot becomes seven places in the ANTE-ROOM (the mesh's round (400, -960, -11900), inside the beat's box, 800 + 100 or more from every vault object), and every squad's chain gets a plain `TriggerDelay2` `020_Timer_vault_opens` behind it = kl_fa_bots' own two-stop form (stop 0: a wait without loot; stop 1: the vault). Seconds = the beat timer's + the door timer's delay READ FROM THE BUILT LEVEL + 2 (56 s with the defaults) |
| NEW `bots_check(folder)`, command `bots-check <folder>` | on a folder with the squad, before or after the dynamic step: seven squads each with ONE gate timer at least beat + door long, started by steps whose last place is inside the beat's box; no place of a step before the gate inside the loot window (800 / 400) of a vault object |
| `check()` | (1) a NO_AI build is known by having no squad OF ENEMIES (the bots' seven are squads too: the first run on the finished no-AI folder said '0 of the 22 campaign squads'); squads and actors are counted with the bots against ACTORS_LIVE; (2) 'room for the wardrobe' is not asked of a folder that has KLWardrobe.ini. On the bare maps check() says what it said (PASS, same lines) |

WHY A CLOCK AND NOT THE EVENT (the comment over `BOT_OPT` says it in full). The mesh runs through the vault door,
whose body stands until 6 s after the beat's end, and the loot is hidden until the beat's end (a take message to a
hidden object is dropped, kl2 0x6cdb65). A bot that holds in the ante-room stands inside the beat's box, so the beat
began when it arrived at the latest; beat + door later the body is off whatever the swing did. Naming the squads'
vault step from the beat's timer instead would start it while a hold timer of the way in may still be armed - that
timer then starts a way-in step for a bot that is in the vault, and a step starts only once
(re/retomoto_bots_rooms.md 9.1, 'the join'): the chain could not come back. The price: a bot that arrives when the
vault is already open still waits its 56 s.

### F.2 The chain as built, and the two places where it is NOT the order asked for

`sh C:/kl_scratch/bank/f/s/chain.sh <bare folder> <work dir> <log dir>` (3.5 min; `out/main/`, `out/noai/` = one
file a step):

| # | step | command | result on the map with enemies (`out/main/`) |
|---|---|---|---|
| 1 | lighten | `kl_graft.py lighten <bare> <1> --load trim,slim,fxc` | nothing left to trim or slim (finish() had done it: '0 dead vertex / index chunks', '0 shrunk'); shader cache 242 -> 127 entries, 16.94 -> 8.85 MB; archive 178.2 -> 176.3 MB |
| 2 | wardrobe | `kl_chars.py wardrobe <1> <2> --plates=wolf,dallas,chains,hoxton` | 'problems: 0'; NO compaction needed: 'chunk table: 65640 entries (20989 of the base's 23690 dead indices taken, 2701 still free; limit 69632 ...)'; .prm 53.2 -> 71.5 MB; KLWardrobe.ini Masks=12 OutfitStep=14. It writes the FULL shader cache back (17.76 MB: its merge, re/campaign_fa_tooling.md 12.8) |
| 3 | bots, base | `kl_fa_bank.py bots <2> <3>` | 'RESULT: PASS (0 FAIL, 2 NOTE); 7 bots, 205 squad nodes'; bots_check PASS (F.3) |
| 4 | gun looks | `kl_map_guns.py build <3> <4> --start=1 --set=1` (the tab's maps' options: `<work>/build/z_final/M03/map_guns.json`) | six guns, 65640 -> 65852 entries, .prm 71.5 -> 72.2 MB, .TEX 237.7 -> 245.8 MB, KLGuns.ini Version 2 `Entries=65852`; exit 1 = its audit's two lines for the known verify finding and nothing else (chain.sh tests that) |
| 5 | talk | `kl_fa_talk.py build <4> <5> --map M03 --str <work>/build/v_bain/over_talk/PC_Def.str` | '10 lines in 6 scenes (M03_A)', 7 ADPCM clips into the .WAV (+0.25 MB), 'findings: FAIL 0, NOTE 1' (the note: 'the level has a blast timer (48.00 s) and KLTalk.ini no countdown' - the beat's timer has the name Retomoto's blast timer has); KLTalk.ini. No new stream file: the one named is the twin of the INSTALLED `<DD>/PC_Def.str` (1,694,610,488 bytes, read only) and its map file equals v_talk's |
| 6 | shader cache again | `kl_graft.py lighten <5> <6> --load fxc` | 242 -> 127 entries, 16.94 -> 8.85 MB ('126 effects asked for by 1277 materials, 0 of them in no entry') |
| 7 | [the sound bank] | `kl_graft.py lighten <6> <7> --load wav` (only for `bank_vault_wavslim`) | 'kl_wavslim: 972 in-memory clips, 338 reached; 151 dropped (10.0 MB, 2 silence block(s)); .WAV 23.3 -> 13.3 MB' |
| 8 | bots, dynamic - LAST | `kl_fa_bots_dyn.py build <6 or 7> <fin>` | 'RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 0 NOTE)'; 161 entities out, 531 in (575 squad nodes) |
| - | fake-fix | not needed: fake-test PASS, 'FakeTargets: 1, outside the vision space: 0' | |
| - | kl_fa_cover | LEFT OUT, measured: `kl_fa_cover.py plan <3>` -> 9 new boxes, 'holds found / asked ...: 36 / 56 before -> 36 / 53 with the boxes' - not one hold more (`out/3_cover_plan.txt`) | |

- **DEVIATION 1, the dynamic step is the LAST step, not part of step 3.** kl_fa_bots_dyn.check holds the four large
  blocks against what its build recorded (dyn.json). MEASURED on the first run in the order asked (`out/chk_fin/` of
  16:25, overwritten): 'FAIL a large block changed its size: {.prm 71548176 ... .fxc 17760648, .WAV 23074256} ->
  {.prm 72157904 ... .fxc 9279136, .WAV 23325136}' - the gun looks, the talk and the cache cut each change one.
  With the step last every checker of the squad passes on the delivered folder. (The tab's maps were made the same
  way round: gun looks, then the squad, the dynamic step on the finished folder.)
- **DEVIATION 2, the shader cache is cut TWICE** (steps 1 and 6): the wardrobe merges the whole cache back, so the
  cut of step 1 is gone after step 2 - the order the study measured ('cut, wardrobe, gun looks, cut again',
  re/campaign_fa_tooling.md 12.8). The delivered folders have the CUT cache (9.3 MB).
- The no-AI chain is the same script on a bare map built here with `python tools/kl_fa_bank.py test
  C:/kl_scratch/bank/f/noai_bare --keep --no-ai --plan <L3's van.json>` ('RESULT: PASS', 20,246 entities, 'verify:
  problems: 2' both known; `out/noai_bare.txt`).

### F.3 The seven AI heisters (MEASURED: `bots.txt`, `dyn.txt`, `dyn_map.png` in each delivered folder)

- kl_fa_bots plans the level WITHOUT help: 'navigation mesh: 902 polygons in 30 parts; the START row is on a part of
  566', loot '11 objects ... in 3 areas; the richest: 7 objects, 2300000 round (390, -960, -12950)', 'route order:
  loot before the way out = 26059 of path'. The stations (16): the dock's ENTERS box (stage 1) -> vault lobby (0,
  240, -6368), (394, 240, -7948) -> the flights (399, -165, -9649) -> THE ANTE-ROOM round (417, -960, -11871)
  [bots_gate; the plan had the foot of the stairs (403, -806, -11293)] -> wait 56 s -> the vault (390, -960, -12950),
  loot wait -> back up -> airlock (1546, 240, -6970) -> stairs (1230, 487, -5453) -> hall (300, 799, -6265), (736,
  799, -8014) -> the front entrance's EXITS box (stage 2) -> the exit box (stage 3, calls the van) -> an
  AllyEscapeBox at (316, 700, -11070), 424 beside the van's line and 357 from its boarding box at the stop.
  25,366 - 28,247 of path a bot = 254 - 282 m.
- 'level exit boxes (...otrExitLevel): a bot is first inside one after 23584..26409 of path, after its loot wait':
  no bot calls the van on the way in. 'loot window (800 / 400): no place of any squad has an object in reach that a
  bot cannot take there (11 plain)' - kl_fa_bots does not know that the vault's seven are HIDDEN until the beat's
  end; bots_check does: '76 places before the gate, the nearest 906 from one of the vault's 7 money objects (7
  hidden at the load; the window is 800): PASS'.
- The dynamic step (default options = the form on the owner's tab: random routes, no fork gap): 'cover boxes ... 74
  high, 44 low' (the campaign's own 118); 'holds: 56 route places asked for one; found 36; without: {no free cover
  box in reach: 20}'; forks 2 / 4 / 3 / 4 / 2 / 5 / 6 a bot, 'every branch walked and checked, in 3 branch sets';
  starts +0 / +3 / +3 / +5 / +5 / +8 / +0 s; 64 - 84 s of timers a bot (the gate's 56 s is in that sum, so the
  holds of the way are 4 - 5 s each); loot seconds 15 / 45 / 30 / 30 / 45 / 30 / 15. During the gate's wait each
  bot takes a cover near the ante-room ('+ takes cover at (459, -931, -11554) 126 from CoverBoxH_10').
  'the hold places alone: 64, median 160, 100 % within 250'.
- The tellers' four stacks are no stop of the route (150,000 a side, under kl_fa_bots' share): the bots pass within
  their window in the hall and the loot tactic may take them.

### F.4 The checks on the delivered folders

`sh C:/kl_scratch/bank/f/s/checks.sh <folder> <out dir>` (2 min a folder); the last line of each is `checks.txt` in
the delivered folder, the whole outputs `checks/`. V = `bank_vault`, W = `bank_vault_wavslim`, N = `bank_vault_noai`.

| checker | command | V | W | N |
|---|---|---|---|---|
| preflight | `kl_maps.py preflight <f>` | 'CRASH 1, RISK 0, NOTE 77' - the one CRASH is 'verify kl_graft.verify reported 1 problems (result.json)' | the same | 'CRASH 1, RISK 0, NOTE 77' ('... reported 2 problems') |
| audit | `kl_maps.py audit <f>` | 'RESULT: FAIL (2 findings that must be 0, 0 known ...)' = 'verify: sound: 10 stream clips are not in the merged stream file' + preflight's echo of it; every checker inside it at 0: kl_fa.check nothing, kl_impact 0, kl_arms 0 findings, kl_chars.undrawn 0 of 84 people, kl_chars.check 0, missing shaders 0 of 1277, kl_snd.verify 0 (4839 sounds, 4686 waves) | the same (kl_snd.verify 0 on the slimmed bank) | 'FAIL (3 ...)': 'sound: 1 stream clips ...', 'FA: BROKEN squads no ZSquadScript: no police' (the BUILD's verify: a round without enemies), the echo |
| Fragile Alliance | `kl_fa.py check <zip>` | exit 0, no finding at all (L3 had 1 DEGRADED 'no bot squads'); ZSquadScript 32 | the same | exit 0, no finding; ZSquadScript 7 |
| impacts | `kl_impact.py <zip>` | 'problems: 0 in 1 levels' | the same | the same |
| weapons | `kl_arms.py check <zip>` | '0 findings' | the same | the same |
| people, wardrobe | `kl_chars.py check <f>` | '21219 nodes, 84 people, .prm 65851 chunks ... problems: 0' | the same | '20822 nodes, 23 people, .prm 65082 chunks ... problems: 0' |
| gun looks | `kl_map_guns.py check <f>` | '6 guns with looks, shows Rifle_zastavam85=MP5, Rifle_FN_SCAR=SG 552, Rifle_AK47=M4A1, SMG_Type05=P90, SMG_MAC_10=Steyr TMP, HG_M9Beretta=USP; problems: 0' | the same | the same |
| the van | `kl_map_escape.py van-check <f>`; `... check <f>` | '0 fault(s)'; '0 fault(s)' | the same | the same |
| the squad | `kl_fa_bots_dyn.py check <f>` (kl_fa_bots.check inside) | 'RESULT: PASS (0 FAIL, 2 NOTE); 7 bots, 575 squad nodes'; 'RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 0 NOTE)'. The notes: START points 0 above the bots' feet (stock 92..137); AllyEscapeBox is not F07's kind (stock F02 F06 F08 run it; every tab map has it) | the same | the same |
| the gate | `kl_fa_bank.py bots-check <f>` | '7 squads, 7 with the gate (020_Timer_vault_opens >= 54 s); 76 places before the gate, the nearest 906 ...: PASS' | the same | the same |
| talk | `kl_fa_talk.py check <f> --str <work>/build/v_bain/over_talk/PC_Def.str` | 'findings: FAIL 0, NOTE 1' | the same, on the slimmed pair | the same |
| FakeTarget | `kl_fa_bots_dyn.py fake-test <work>/build/z_route/M01 <work>/build/rt_full6/retomoto_full <f>` | 'RESULT (fake-test): PASS (grid control 1, parked control 1, lattice 3)' | the same | the same |
| cover list | `C:/kl_scratch/bank/t1/s/covers.py <f>` | 1 FFCoverList, on ROOT\Special!CoverList | the same | the same |
| route | `kl_route.py walk <f> --from START=250,200,-4350 --via vault=399,-960,-12818 --via hall=377,801,-8423 --via "front entrance=300,800,-9350" --to "boarding place=636,702,-11231" --open SI0102_M03_BankVault_Door_PRE_01` | 'RESULT: FREE; the mesh way: 1064 samples, all free' | the same | the same |
| route, as built, without the vault | `kl_route.py walk <f> --from START... --via "ante-room=400,-959,-11800" --via hall... --to "boarding place..."` | 'RESULT: FREE; the mesh way: 1008 samples, all free' | the same | the same |
| doors | `kl_route.py doors <f> --from START... --via vault... --to "street=949,702,-11105"` | 'RESULT: 1 closures in 1 sets, 1 necessary' (the vault door) | the same | the same |
| the layer | `kl_fa_bank.py check <f>` | 'PASS' ('68 ZFFActor in 32 squads + 16 player bodies (ran live: 99 actors, 55 squads)') | 'PASS' | 'PASS' ('enemies: none', '7 ZFFActor in 7 squads') |

The bare maps: `kl_fa_bank.py check` PASS on `bank_vault_bare` (= L3's kept build, sha1 5f11b846..., byte for byte)
and on the no-AI bare (deleted after its chain).

**Chunk table and the five large blocks** (`python C:/kl_scratch/bank/f/s/blocks.py <label>=<zip> ...` ->
`c_bank/blocks.txt`; MB = 10^6; five blocks = 32.0 + (.fxc, .prm, .ANM each + 0x60000) + the .WAV beside):

| level | .prm | .fxc | .ANM | .WAV | .TEX | five blocks | chunk table (line 69,632) | archive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `bank_vault` | 72.2 | 9.3 | 21.9 | 23.3 | 245.8 | **159.9** | 65,852 | 208.0 |
| `bank_vault_wavslim` | 72.2 | 9.3 | 21.9 | 13.3 | 245.8 | **149.8** | 65,852 | 208.0 |
| `bank_vault_noai` | 63.0 | 9.3 | 21.6 | 23.1 | 228.1 | **150.1** | 65,083 | 191.3 |
| `bank_vault_bare` | 53.2 | 17.8 | 21.9 | 23.1 | 213.9 | 149.1 | 65,640 | 178.2 |
| stock F07 | 63.6 | 8.1 | 21.6 | 18.3 | 281.0 | 144.7 | 35,102 | 200.2 |
| the tab's Retomoto (`w_tabK` DM09) | 79.9 | 17.8 | 21.6 | 27.8 | 264.9 | 180.3 | 65,331 | 218.9 |
| the tab's Withdrawal (`w_tabK` DM03) | 62.6 | 17.8 | 22.3 | 22.7 | 237.6 | 158.5 | 62,892 | 200.9 |

So the finished bank asks for 15 MB more than stock F07 in large blocks, 20 MB LESS than the Retomoto that loads,
and as much as the Fragile Alliance bank on the tab - with the cut cache; with the full one it would be 168.4.
Chunk table: 3,780 entries under the tools' line; 5,364 indices are still dead.

### F.5 What is delivered (`<work>/build/c_bank/`)

| folder | what | F01_Main.zip sha1 | first use |
|---|---|---|---|
| `bank_vault` | the finished map, the sound bank WHOLE | 943e1e5c031c... | the map |
| `bank_vault_wavslim` | the same archive byte for byte; `F01_Main.WAV` (13.3 MB) and `F01_Main.WHD` are the slim pair (kl_wavslim: NEVER LOADED LIVE). KLGuns.ini, KLTalk.ini, KLWardrobe.ini, van.json equal | 943e1e5c031c... | only after `bank_vault` has loaded |
| `bank_vault_noai` | the same chain on the NO_AI build: no enemy, the beat, loot, van, bots, wardrobe, guns, talk as with them | 14b51ed39031... | THE FIRST LIVE LOAD |
| `bank_vault_bare` | L3's bare map before the chain (enemies, no wardrobe / bots / guns / talk; full shader cache) | 5f11b846ec79... | a direct boot; the start of a new chain |

Each finished folder: `F01_Main.zip`, the 18 files beside it, `KLWardrobe.ini` (16 characters, 12 masks),
`KLGuns.ini` (Version 2, Entries = the .prm's chunk count), `KLTalk.ini`; NO KLJoin.ini (one mesh part, no join, no
drop: kl_fa_bots writes no [CrewHop]); `van.json` (check() holds the drive against it), `result.json`, `log.txt`,
`graft.txt`, `bots.txt / .json`, `dyn.txt / .json`, `dyn_map.png`, `guns.json`, `map_guns.json`, `talk.json`,
`chars.json`, `audit.txt / .json`, `preflight.txt / .json`, `checks.txt`, `checks/`. Member and file names are
kl_maps' (slot name F01); the packaging onto a slot and the menu entry are another session's.
Beside the folders: `chain.sh`, `checks.sh`, `blocks.py`, `blocks.txt`.

### F.6 GUESS / ASSUMED (each marked in the file)

- ASSUMPTION the gate rests on: an AI heister trips the `ECPS_FA_MERCONLY` beat box (re/retomoto_bots_rooms.md 8:
  'measured in effect', never read in kl2.exe). If not, and no human is in the ante-room: the bots walk on to a
  shut door after 56 s, their loot wait runs out and they leave without the vault's money. Nothing worse.
- CONSEQUENCE of the same assumption, the lead should know: the FIRST BOT in the ante-room starts the beat (rods,
  the 14 police, the 48 s), not only the human. The point man starts at +0 s and has about 80 m to walk, with three holds of 5 s.
- ASSUMPTION: a step that was started does not start again and a started step replaces the running one (the reason
  for the clock; re/retomoto_bots_rooms.md 3.2).
- GUESS: `GATE_AT` (400, -960, -11900), `GATE_REACH` 400, `GATE_MORE` 2 s, `GATE_CLEAR` 100; the 30 s loot wait
  (the dynamic step makes 15 / 30 / 45 of it by role).
- ASSUMPTION (kl_fa_bots'): the bots are taken aboard from the AllyEscapeBox beside the van's stop when the van
  stands (kl2 0x907a50); they do not walk to its doors.
- NOT KNOWN: what a bot with heist stage 1 does about HIDDEN money inside its window. The places before the gate
  keep out of it (906); the 'cover' a bot takes during the wait is chosen by the dynamic step within its own reach
  and is tested by nothing here against that window (the one seen: (459, -931, -11554), 1,400 from the loot).
- The guns' options (`--start=1 --set=1`) are the tab's; which stream file the owner's game has was READ by size only.

### F.7 For the next stage / the lead

- **First live order**: `bank_vault_noai` (a round without enemies: start in the yard, doors, the bots' walk, the
  gate, the vault, the van) -> `bank_vault` -> `bank_vault_wavslim`. Install is the game holder's
  (`python debug/slot.py put "<work>/build/c_bank/bank_vault_noai" F01`; the folders hold no KLJoin.ini, slot.py
  removes the slot's).
- TWO THINGS IN THESE FOLDERS HAVE NEVER LOADED LIVE ANYWHERE, beside the level itself: the cut shader cache
  (the owner's tab maps carry the full 17.8 MB one; READ kl_graft.load_options: 'NOT LOADED LIVE') and, in
  `bank_vault_wavslim`, the slimmed bank. If a first load faults, a folder with the FULL cache is the chain
  without its step 6 (`chain.sh`: 3.5 min; five blocks then 168.4 MB, still under Retomoto's 180.3).
- **Rebuild**: `python tools/kl_fa_bank.py test <out> --keep [flags] --plan "<work>/build/c_bank/bank_vault_bare/van.json"`,
  then `sh <work>/build/c_bank/chain.sh "<out>/F07+M03_A campaign" <work dir> <log dir>` -> `<work dir>/fin`,
  `fin_wav`; then `sh .../checks.sh <folder> <out dir>`. A `--beat S` build needs nothing else: the gate reads the
  two delays off the level. A `--vault-open --loot-shown` build still gets the 56 s wait (harmless, not needed).
- The audit's 'FAIL' goes only with a rebuild after the stream file has the level's clips (the owner's go-ahead;
  re/campaign_fa_tooling.md 12.7: 'a first-build line').
- `kl_maps.audit` has no 'known' entry for a verify finding: whoever gates an install on `audit.json` 'bad' must
  read the two (three) lines above as the known ones.

### F.8 Open

- Nothing ran in the game.
- The bots through the six open door sets, down two flights and back up the airlock stairs: one order a leg over
  20 - 45 m of stairs is what Retomoto's bots managed live (G1), nothing of this level's was seen.
- Whether the first bot starting the beat is wanted (F.6). To make the HUMAN start it the beat box would have to
  tell a human from a bot; no such field is known.
- 20 of 56 hold places have no cover box in reach (the yard, the stairs, the plaza: `dyn.txt`); kl_fa_cover finds
  nothing for them.
- The bots do not go for the tellers' stacks by route; the vault's 2.3 M is shared with the human by the loot
  waits (15 - 45 s).
- 'Out of sight' for the waiting van (L3.4), the retreat routs and the police ring at the van's call (L2.7), the
  menu entry / slot packaging, the stream file with the music and the guards' lines: untouched.
- kl_fa_talk's note 'the level has a blast timer and KLTalk.ini no countdown': a Kane countdown to the vault door
  (SCRIPTS['M03'] has none) would be a talk-script entry in another session's file; not done.

(end of Stage F)

## Review round 1 - the fixes (tools/kl_fa_bank.py, tools/kl_route.py; a docstring line each in kl_maps.py / kl_graft.py)

STATE: DONE (2026-10-11 evening). All thirteen findings were reproduced and fixed, none rejected. The four folders
in `<work>/build/c_bank/` are REBUILT from the fixed module (same names, same chain + its new last step `seal`) and
every checker was run again: all pass except the two that only repeat the build's known verify finding, exactly as
in stage F (`kl_maps.py preflight` 'CRASH 1', `kl_maps.py audit` 'FAIL 2' / no-AI 3). Scratch:
`C:/kl_scratch/bank/fix_1/` (0.8 MB: `s/` scripts, `out/` every output; no archive is left there).
NOTHING RAN IN THE GAME (kl2.exe was running: the owner was playing). No file of another session was edited.
Committed as fedea0e (tools/kl_fa_bank.py, tools/kl_route.py, the two docstrings, this section).

### R1.1 The thirteen findings: reproduced or not, what changed

| # | finding (lens) | reproduced | what changed |
|---|---|---|---|
| 1 | 8 slave spots of the alarm lamps' gate lights stay shown (crash) | yes: `review_crash_1/s/slaves.py bank_vault` -> 11 + 11 masters hidden, '8 (ZSPOTLIGHT, slave, not hidden)' | `strip()`: the slaves named by each hidden ZGateLightSpot's last field (`SLAVES`) are hidden with their masters (8 expected, else an error); `check()` wants 22 + 8 hidden when no LightToggle is in the level |
| 2 | 229 room list entries name the bots' squad group (crash) | yes: `refs.py bank_vault_bare bank_vault` -> bare '229 NO ENTITY' (REF 30965), finished '229 x Squad#02 [ZGROUP]' | NEW `seal(folder)` (command `seal`): entries that name an entity outside 'Locations/...' go to the written scene's free REF id; the LAST step of `chain.sh` (the dynamic bot step adds entities too, so `bots()` alone could not hold it); rule in `reverify()` |
| 3 | no checker re-runs verify's cross-references on the delivered archive (crash) | yes (audit.txt quotes 'at the build') | NEW `reverify(folder)` (command `reverify`; `check()` calls it; `checks.sh` runs it): kl_graft.verify's tests lifted from the reviewer's `verify2.py` |
| 4 | the beat box has TriggerBox field 15 = 1, which by stock data is 'for every criminal' (round) | yes: `review_round_1/tb.py` -> 101 boxes with 1, none names a squad rout; 125 with 0; `tbRunToEscape` (1) -> TriggerCounter, its twin (0) -> timer; stock F07's own `tb_LEFT_TheySpotYou` has 0 | `wire()`: field 15 (`BOX_PER_MAN`) = 0 on the beat box; `check()` fails on anything else. L1.4 / L2.4's 'field 15 = once' was the wrong way round |
| 5 | the escape marker stands on the van's stop (round) | yes: `fix_1/s/lane.py` -> marker 0 from the drive's line, boarding place 80, the bots' place 425 | `ESC_AT` = (316, 702, -11070): 425 from the drive, 357 from the boarding place, on the mesh and free floor; marker `ESC_POI` 188 over it; `prepare_host()` holds it against the plan (`LANE_CLEAR`); ROUTE_OUT's last station is that place; `check()`: marker and stations of the way out in the lane rule |
| 6 | the 14 'beat' police come into the world in the dock and vault lobby (round) | yes: inventory of bank_vault - seven within 4.5 m of the 'vault lobby' station | `BEAT_MEN`: 14 measured places behind the airlock (8 in the corridor to the hall's stairs, 6 on the landing above), `strip()` -> `beat_men()`; `check()`: `BEAT_CLEAR` 1000 from every station before a later squad's trigger |
| 7 | the escape-area box (takes the loot marker away) holds the banking hall (round) | yes: PLACE had z -11500..-5700 | the three `Trigger_POI_TheEscapeArea*` boxes are the plaza and street only (z -11700..-9400, as the exit box) |
| 8 | '85 clips need a larger PC_Def.str' is wrong: 16 (regress) | yes: `review_regress_1/s/clips.py` -> '69 streamed, 16 NO RECORD' | `KNOWN`'s reason; NEW `lost_clips()` + a line of `check()` that lists the names without a record in the built .WHD; the notes L2.1 / L2.3 / L2.6 corrected in R1.2 below |
| 9 | WARDROBE_CHUNKS 15,509, the chain's wardrobe took 20,989 (regress) | yes: `f/out/main/2_ward.txt` | `WARDROBE_CHUNKS = 20989` |
| 10 | bots-check passes a folder without a squad (regress) | yes: 'bank_vault_bare: 0 squads ... PASS' | `bots_check()` fails unless there are `len(kl_fa_bots.BOTS)` squads |
| 11 | the docstring example stops by design and leaves kl_escape wrapped (regress) | yes (read: `Doors.arm` stood before the plan test) | `prepare_host()` tests the plan FIRST; kl_maps.py / kl_graft.py docstrings no longer give the command as a way to build the bank |
| 12 | BLOCKS_LIVE 171 called 'Retomoto on the tab' (regress) | yes (blocks.txt: 180.3) | the comment and the check's line say which build 171 is |
| 13 | guesses without the word, dead names (regress) | yes | GUESS added (BOT_OPT, VAULT_BOX, LOOT_WALKS, POI_TheLootArea; kl_route: HULL, NEAR, GAP, LINE_FLOOR); STREET, DOCK_DOOR and Doors' 'rows' removed |

No finding was rejected.

### R1.2 What is really lost of the sound (finding 8), for the owner's go-ahead

`check()` now prints it from the built .WHD ('sound: of the 85 clip names result.json lists, 69 have a streamed record
... 16 have NO record'). The 16 clips a larger PC_Def.str would bring:
- music (6, `MUSIC_CLIPS`): `Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav`, `..._Layer2_Bass_LOOP.wav`,
  `..._Layer3_Intense_LOOP.wav`, `..._Layer4_Basic_LOOP.wav`, `M03_Bustout_ActionV34.wav`, `M03_Bustout_IntenseClimax_Loop.wav`
- ambience (1): `SFX/Ambiences/M03_A/Inside/Ambience_Inside_Vault_Deeper.wav`
- guard lines (9): `Dialog/M02/Dialogue/Situation/M02_GuardsShout/M02_GuardsShout_020 / 025 / 050 / 060_Guard.wav`,
  `Dialog/M03/Dialogue/M03a_OneLiners/M03_GuardAlarm/M03_GuardAlarm_010_Guard02.wav`,
  `Dialog/M03/Dialogue/M03a_OneLiners/M03_Spotted/M03_Spotted_040_Guard.wav`,
  `Dialog/M03/Dialogue/Situation/M03_Enter/M03_Enter_011_Guard.wav`,
  `Dialog/M08/Dialogue/Situations/M08_Cantina/M08_Cantina_010 / 030_Guard01.wav`
The other 69 names (`Dialog/AllLevels/Oneliners/...`) have streamed records that point into the installed merged
file: the kept guards speak. result.json's longer list is kl_maps.one's reconstruction BY NAME (kl_maps.py, 'the
names are a reconstruction': a name is listed when any record of that name is a language-file one) - that code is
outside stage T1's two changes and was left; FOR THE LEAD: it over-reports on every campaign map.

### R1.3 The rebuild and every checker again

Built with the fixed module (the docstring lines added afterwards change no build):
- `python tools/kl_fa_bank.py test C:/kl_scratch/bank/fix_1/bare --keep --plan <the delivered van.json>` -> 'RESULT: PASS',
  20,643 entities, 'verify: problems: 1' (known); `out/test_bare.txt`. New lines of the build: 'the escape marker stands
  425 from the van's drive, 362 from the boarding place at the stop', 'the 14 police of the beat (7 squads) re-placed
  behind the airlock, off the way in: from x -901..716, z -7489..-6010 to x 1415..1585, z -6700..-5380', 'the alarm
  lamps: 22 lights and 8 slave spots of theirs in the rooms next door; the LightToggle taken off and all of them hidden'.
- `... test C:/kl_scratch/bank/fix_1/noai_bare --keep --no-ai --plan ...` -> 'RESULT: PASS', 20,246 entities, 'verify:
  problems: 2' both known; `out/test_noai_bare.txt`.
- `sh <work>/build/c_bank/chain.sh <bare folder> <work dir> <log dir>` on each (3.9 min): the steps of F.2 with the
  same result lines, then NEW `8_seal`: 'kl_fa_bank.seal ...: 229 room list entries named an entity outside the map (229 x
  Gameplay!merc_bot_squad!Squad#02) and now name the free REF id 31540; 0 named no entity before' (no-AI: id 31192).
  `out/main/`, `out/noai/`.
- `sh <work>/build/c_bank/checks.sh <folder> <out dir>` on the three finished folders (`out/chk_main_fin/`,
  `chk_main_fin_wav/`, `chk_noai_fin/`; copies in each folder's `checks/`, summary = `checks.txt`):

| checker | bank_vault | bank_vault_wavslim | bank_vault_noai |
|---|---|---|---|
| `kl_maps.py preflight` | 'CRASH 1, RISK 0, NOTE 77' (the known verify finding) | the same | 'CRASH 1, RISK 0, NOTE 77' ('reported 2 problems') |
| `kl_maps.py audit` | 'FAIL (2 findings that must be 0 ...)' = the stream clips + preflight's echo | the same | 'FAIL (3 ...)' = + 'no ZSquadScript: no police' |
| `kl_fa.py check` | exit 0, no finding, ZSquadScript 32 | the same | exit 0, ZSquadScript 7 |
| `kl_impact.py` | 'problems: 0' | 'problems: 0' | 'problems: 0' |
| `kl_arms.py check` | '0 findings' | '0 findings' | '0 findings' |
| `kl_chars.py check` | '21219 nodes, 84 people ... problems: 0' | the same | '20822 nodes, 23 people ... problems: 0' |
| `kl_map_guns.py check` | '6 guns with looks ... problems: 0' | the same | the same |
| `kl_map_escape.py van-check` / `check` | '0 fault(s)' / '0 fault(s)' | the same | the same |
| `kl_fa_bots_dyn.py check` | 'PASS (0 FAIL, 0 NOTE)' (after the seal) | the same | the same |
| `kl_fa_bank.py bots-check` | '7 squads, 7 with the gate ... 76 places before the gate, the nearest 906 ...: PASS' | the same | the same |
| `kl_fa_talk.py check` | 'findings: FAIL 0, NOTE 1' | the same | the same |
| `kl_fa_bots_dyn.py fake-test` | 'PASS (grid control 1, parked control 1, lattice 3)' | the same | the same |
| cover lists | 1, `ROOT\Special!CoverList` | 1 | 1 |
| `kl_route.py walk` (vault door opened) / without the vault | 'FREE; the mesh way: 1064 samples, all free' / '1008 samples, all free' | the same | the same |
| `kl_route.py doors` (to the new last station (316, 702, -11070)) | '1 closures in 1 sets, 1 necessary' | the same | the same |
| NEW `kl_fa_bank.py reverify` | 'problems: 0' (21,218 entities, 694 gate / list cells, 229 parked on REF 31540) | 'problems: 0' | 'problems: 0' |
| `kl_fa_bank.py check` (now with the lines of findings 1, 4, 5, 6, 8 and reverify) | 'PASS' | 'PASS' | 'PASS' |

- `bank_vault_bare`: `kl_fa_bank.py check` 'PASS' (`bank_check.txt` in the folder), `kl_maps.py preflight` 'CRASH 1,
  RISK 0, NOTE 78'; reverify inside check: 'problems: 0', 229 entries parked on the free REF id 30965 (the graft's form).
- Read back with the reviewers' own scripts on the rebuilt bank_vault: `slaves.py` -> '8 (ZSPOTLIGHT, slave, flag 0x400
  (hidden), ZGEOM[3] 1)'; `refs.py` -> 'list entry NO ENTITY 229', no 'ZGROUP' line (bank_vault and bank_vault_noai);
  `pairs.py ... TriggerBox:ZBoxPrimitive` -> the beat box's field 15 is 0; `armed.py` -> 'kl_escape.repair /
  place_entities / cut_collision are the real ones again: [True, True, True]'; inventory: the escape marker at
  (316, 890, -11070), the three escape-area boxes at (300, 1075, -10550) half (1500, 425, 1150), the beat's men at the
  places of `BEAT_MEN`.
- check()'s new lines on the bare map: 'of the 42 men who come after the round's start the nearest to a station that
  lies before his squad's trigger: ...Vault_Reinforcement_Police_03\Police_02\Ground, 1165 from 'dock door''; 'the
  escape marker stands 425 from the drive, 358 from the boarding place at the stop'; '61 of the 61 men on the mesh part
  of the START and on free floor within 30'; 'alarm lamps 11, no LightToggle in the level, 22 lights and 8 slave spots hidden'.
- Sizes (`<work>/build/c_bank/blocks.txt`, unchanged to the first decimal): bank_vault five blocks 159.9 MB, chunk table
  65,852; wavslim 149.8; noai 150.1 / 65,083; bare 149.1 / 65,640. c_bank is 0.93 GB.
- Delivered archives (sha1, first 12): bank_vault = bank_vault_wavslim `ac97b4f13ca2` (only F01_Main.WAV / .WHD differ,
  as before), bank_vault_noai `ecf445f1ceac`, bank_vault_bare `b7e48d31634c`.

### R1.4 GUESS / ASSUMED that the fixes bring (each marked in the file)

- GUESS: the 14 places of `BEAT_MEN` (measured: on the START's mesh part, on free collision floor, 100 - 125 apart, the
  nearest 1165 from a station of the way in) and `BEAT_CLEAR` 1000. ASSUMPTION: the squads' defend routs walk their men
  from there through the airlock and the lobby and down (one mesh part; the airlock's four leaves are open at build
  time). With `--doors-animate` the airlock leaves stand until the round start's 'Activate' - then the police depend on
  that animation too.
- NOT TESTED: sight. The corridor is round the corner from the airlock's doorway (the room behind the airlock is x
  1285..1625, z -7125..-6867; the nearest man stands at z -6700), but no sight line was computed.
- The 13 guards of stage 'start' still come into the world in the dock, 10 - 15 m behind the open roller door, about
  1.4 s after GO (the reviewer's 'same mechanism, smaller'): left - it is the round's opening fight, as Retomoto's.
- ASSUMPTION still: TriggerBox field 15's meaning is read off the stock census (226 boxes), not in kl2.exe.
- GUESS: `ESC_AT` (the marker's place; measured 425 from the drive, on the mesh). The BOARDING place stays 80 from the
  drive's line by nature (the box rides on the van): a player who waits where the rear doors WILL be is in the kill box's
  sweep. The marker no longer sends him there; nothing else was done about it.
- ASSUMPTION: a slave spot hidden in the file (ZGEOM[3] = 1, flag 0x400) does not shine - the same assumption as for the
  22 masters. With `--alarm-lights` nothing is hidden and the engine's own calls carry the state to the slaves.
- seal(): the form 'a room list entry names REF id = the header's slot count, which no entity has' is the graft's own
  and has LOADED AND PLAYED (Late Night Opening, `<work>/build/z_maps/M02`: 80 such entries; 2026-10-10). The other form
  (entries name the bots' squad group) is what the tab's maps carry and play with. Neither was read in kl2.exe.
- reverify() is a COPY of kl_graft.verify's tests: when that function gains a test this one does not follow by itself.

### R1.5 For the next stage / the lead

- Build, chain and checks as before; the chain has one more step: `python tools/kl_fa_bank.py seal <folder>` LAST (after
  `kl_fa_bots_dyn.py build`). Any tool that adds entities after it needs the seal again; `kl_fa_bank.py reverify <folder>`
  (or `check`) says so ('... room list entries name an entity outside the map').
- `kl_fa_bank.py check` now also re-runs the cross-references on the written level: a finished folder that was not
  sealed FAILS check.
- FOR kl_fa_bots' OWNER (told here, no file of theirs touched): the tab's maps carry the same 'list entries -> Squad#02'
  form (w_tabX DM03 224 entries, DM02 80, DM06 2 by the reviewer's count); `kl_fa_bank.seal` works on any built folder.
- The first live order is unchanged: bank_vault_noai -> bank_vault -> bank_vault_wavslim.
- New things to look at in a live round: the 14 police arriving on foot from the airlock after the first criminal
  reaches the ante-room; the escape marker on the street 4 m beside the van's lane; no red lamp lit before the alarm.

### R1.6 Open

- Nothing ran in the game.
- preflight / audit stay 'not green' for the known verify finding (F.8's first item): unchanged, the lead's call.
- kl_maps.one's by-name clip list (R1.2) and kl_graft.verify's missing 'ZERO cover lists' line (T1's open item) are
  in shared files outside this workflow's two changes: not touched.
- Whether a human in the vault lobby SEES the police come into the world in the corridor behind the airlock (R1.4).
- The boarding place inside the arriving van's sweep (R1.4): only moving the stop's heading or the boarding box would
  change it; the van stands when 'Get in' shows.
- 'Out of sight' for the waiting van, the retreat routs, the menu entry, the stream file: as in F.8.

(end of Review round 1)

---

## Music stage - the stream file with the map's sixteen clips, and the four folders rebuilt against it (2026-10-11, about 18:50 - 19:30)

The owner, today: 'May a larger music file be rebuilt and installed so the music plays? yes'. This stage BUILT, offline.
NOTHING OF IT HAS RUN IN THE GAME, nothing is installed, the game folder was only read (one sha1). The silent folders in
`<c_bank>` are untouched (they are the ones under test). `<work>` as above; `<v_vault>` = `<work>/build/v_vault`,
`<c_bank_music>` = `<work>/build/c_bank_music`. Outputs of every command: `C:/kl_scratch/vault_music/out/`.
Files of this stage: NEW `tools/kl_vault_str.py` (the driver), `tools/kl_fa_bank.py` (+ `--str`, `music_records`, three
lines of check()), this section. No other tool was edited.

### M.1 The stream file: `<v_vault>/PC_Def.str`

| | bytes | sha1 |
|---|---|---|
| base = the installed pair `<work>/build/v_bain/over_talk/PC_Def.str` (MEASURED: `<DD>/PC_Def.str` has the same sha1) | 1,694,610,488 | `b0cb8bcd5040462d3caec025e65939d85702a5f0` |
| NEW `<v_vault>/PC_Def.str` | 1,753,469,945 (1.633 GB; + 58,859,457 = 56.13 MB; 394 MB under 2 GB) | `80e53495ae550feb281f08d63b33619907f700cb` |
| NEW `<v_vault>/PC_Def.str.map.json` (2,086 blocks = the base's 2,074 + 12) | 71,727 | `6b86aab44df05a7e18aee273cacbb54bcaf4d8eb` |
| `<v_vault>/PC_Def.str.bain.json` (carried, byte for byte the base's) | 2,359 | `3321f08ad61adc0f2ff93137e6ce933046932f98` |

HOW (one method, the one the earlier files were made with): `kl_str.merge(base, Dead Men's PC_Def.str, want, out, prior =
the base's .map.json)` - the call `kl_fa_talk.py stream` made for the talk clips; kl_bain.stream_add is the same writing
for clips that are not Dead Men's. `python tools/kl_vault_str.py build <base> <out>` (`out/str_build.txt`).
`want` = the Dead Men blocks of the sixteen names, taken from M03_A's own .WHD records BY OFFSET
(`kl_vault_str.need()`; MEASURED equal to `kl_fa_bank.lost_clips` on `<c_bank>/bank_vault_bare`: 16 of 16).

WHICH PROOF HOLDS FOR THIS FORMAT (READ: kl_str.py's docstring; MEASURED: `kl_vault_str.py proof`, `out/proof.txt`, PASS).
The index of an IOISNDSTREAM file is at the END (format table, name table, index behind the last data block; the header
names the index's offset), and a level names a clip by the OFFSET of its block. So 'the first 1,694,610,488 bytes are
the installed file' does NOT hold and is not claimed: the new blocks stand where the base's tables stood (from byte
1,692,882,176), one fresh table and index for all 10,217 clips follows them. What holds:
1. bytes 0x38 .. 1,692,882,176 (the base's whole data area, 1,692,882,120 bytes): sha1 `d2bc5972368f87b1d9e28d1fcfc646cf52d855e3`
   in both files; the header differs only in 0x18..0x24 (index offset, clip count), build id 4c08b8d5 as the banks';
2. clip by clip: 10,199 of the base's 10,199 index entries stand in the new index with the same id, name, block offset,
   size, format bytes, lip word and layer;
3. 2,074 of the base's 2,074 map entries keep their new offset (and byte count); the 26 Bain clips of the .bain.json are
   found by name at their offsets with the base's bytes;
4. the 12 appended blocks equal Dead Men's bytes and stand in the index with Dead Men's format, lip word and layer;
5. `Stream.account()`: every byte of the file claimed, 0 problems (`kl_str.py info`: 'problems: none').

THE SIXTEEN CLIPS = 12 blocks, 18 index entries (the two set entries come with their sets):

| new offset | Dead Men block | bytes | what |
|---|---|---|---|
| 1,692,882,176 | 0x1e1e00 | 21,504 | `M03_Spotted_040_Guard.wav` (LIP + IMA ADPCM, 32 kHz mono) |
| 1,692,903,680 | 0x3711a00 | 51,200 | `M02_GuardsShout_025_Guard.wav` |
| 1,692,954,880 | 0x6a8bc00 | 52,224 | `M02_GuardsShout_020_Guard.wav` |
| 1,693,007,104 | 0x6d3d900 | 16,384 | `M03_Enter_011_Guard.wav` |
| 1,693,023,488 | 0x7578d00 | 28,672 | `M02_GuardsShout_060_Guard.wav` |
| 1,693,052,160 | 0x7768300 | 182,693 | `SFX/Ambiences/M03_A/Inside/Ambience_Inside_Vault_Deeper.wav` (Vorbis, 120 s) |
| 1,693,234,944 | 0x9e6a900 | 21,504 | `M03_GuardAlarm_010_Guard02.wav` |
| 1,693,256,448 | 0xb8f7e00 | 18,432 | `M02_GuardsShout_050_Guard.wav` |
| 1,693,274,880 | 0xc94bd00 | 79,872 | `M08_Cantina_010_Guard01.wav` |
| 1,693,354,752 | 0xfd7f600 | 17,408 | `M08_Cantina_030_Guard01.wav` |
| 1,693,372,160 | 0x17ea5900 | 21,503,688 | the WAY-OUT set `LevelSetup/Level/M03_A/Music/M03A_Bustout_A_I`: `M03_Bustout_ActionV34.wav` + `M03_Bustout_IntenseClimax_Loop.wav`, interleaved PCM, 2 stereo layers, 32 kHz, 168 s |
| 1,714,875,904 | 0x2685e900 | 36,862,624 | the BREAK-IN set `LevelSetup/Level/M03_A/Music/BO_Sus_LOOP`: `BO_Sus_Layer1_Ambient` / `Layer2_Bass` / `Layer3_Intense` / `Layer4_Basic_LOOP.wav`, interleaved PCM, 4 stereo layers, 32 kHz, 144 s |

(Dead Men's file also holds a shorter set `BO_Sus_..._LOOP2.wav`, 56 s, at 0x1e049d00: the level does not name it.)
NOT taken: `kl_str.py check <new> M03_A` says '33 clips missing' (49 with the installed file): kl_str's selection for a
story level is ALL of its map side, also what the campaign pre-pass drops (cut scenes, the crew's lines). The Vault's
own build needs none of them: its verify reports 0 (M.2). The six levels the tab's maps are made from: `kl_str.py check
<new>` -> 'RESULT: PASS', 0 records without a block, 0 clips missing on M01_FA_A, M02_FA_A, M03_FA_A, M06_FA_A, M09_A,
M09_B (`out/str_check_levels.txt`).

THE TAB'S MAPS AND RETOMOTO against the new file (tree `<work>/build/w_tabM/KLExpansion/Maps`, read only;
`kl_vault_str.py tab`, `out/tab.txt`: PASS): DM01 3,847 streamed PC_Def.str records, DM02 3,847, DM03 3,849, DM06 3,833,
DM09 3,690 - on each 0 name no block of the new file, 0 name a block the base does not have at the same place with the
same clips, 0 are larger than their block; DM09's KLTalk.ini StreamBytes 1,688,413,044 fits. `kl_bain.check` with the
new file on all five: 0 problems each. `kl_fa_talk.check` on DM09: FAIL 1 'the countdown's NOW! starts at [7.51], the
blast is at 16.50' - THE SAME LINE with the installed file (`out/tabtalk.txt` = `out/tabtalk_base.txt`): a finding of that
build's timing, not of the stream file; not this stage's.

### M.2 The map with the music: `<c_bank_music>/` (0.93 GB), the same four names

How a build is told its stream file (READ): kl_snd has ONE fixed place, `kl_snd.stream_file('merged')` =
`<work>/build/PC_Def.str`, and `stream_map()` reads the .map.json beside it; `kl_snd.merge` inside `kl_maps.one` resolves
Dead Men's streamed records through that map. That file is another session's and stays. `kl_fa_bank.py test ... --str
<file>` (NEW, `use_stream`) replaces `kl_snd.stream_file` for the length of the process - the way Doors replaces
kl_escape's three functions. kl_fa_talk has its own `--str`.

- `python tools/kl_fa_bank.py test C:/kl_scratch/vault_music/bare --keep --music-layer4 --str <v_vault>/PC_Def.str --plan
  <the delivered van.json>` -> 'verify: problems: 0', 'RESULT: PASS', 20,643 entities (`out/test_bare.txt`); the line
  'sound: ... stream records added 94, interleaved stream groups added 2'.
- the same with `--no-ai` -> 'verify: problems: 1' (the known 'no ZSquadScript: no police'), 'RESULT: PASS', 20,246
  entities (`out/test_noai_bare.txt`).
- `sh <c_bank_music>/chain.sh <bare folder> <work dir> <log dir>` on each: `<c_bank>/chain.sh` with ONE changed line (the
  talk step's `--str` names `<v_vault>/PC_Def.str`); all steps exit 0 as before, and `4_guns` now exits 0 on the main build
  ('problems: 0': its audit is green); on the no-AI build it exits 1 with the one known line (`out/main/`, `out/noai/`).
- `sh <c_bank_music>/checks.sh <folder> <out dir>` (one changed line, the same) + `kl_vault_str.py whd` on each of the four:
  copies in each folder's `checks/`, summary `checks.txt`. The archives' sha1 were the same after the checks as before.

| folder | F01_Main.zip sha1 | archive bytes | F01_Main.WAV | five blocks | chunk table |
|---|---|---|---|---|---|
| `bank_vault` | `dd763485d90b11a94fa4db6698e4284bb8e9c1da` | 207.98 MB | 23.3 MB, sha1 `2e1d7827...` (= the silent build's) | 159.9 MB | 65,852 |
| `bank_vault_wavslim` | the same archive | | 13.3 MB, `fcbd62b8...` (= the silent build's) | 149.8 MB | 65,852 |
| `bank_vault_noai` | `5acb5e429cd0f84ed0239bac286aa3445dbab269` | 191.3 MB | 23.1 MB | 150.1 MB | 65,083 |
| `bank_vault_bare` | `5489199a2a689fdce8bc771347fba237c31dbd5a` | 178.2 MB | 23.1 MB | 149.1 MB | 65,640 |

The music costs the level load NOTHING: the clips are streamed, the .WAV of each of the four folders is byte for
byte the silent build's (cmp), the five blocks are the same to the decimal (`<c_bank_music>/blocks.txt`); only the .WHD and
the bank / level members inside the archive grow.

| checker | `bank_vault` | `bank_vault_wavslim` | `bank_vault_noai` | `bank_vault_bare` |
|---|---|---|---|---|
| `kl_maps.py preflight` | PASS (exit 0): 'CRASH 0, RISK 1, NOTE 76' | the same | exit 1: 'CRASH 1, RISK 1, NOTE 76' = 'no police', what the build is | PASS: 'CRASH 0, RISK 1, NOTE 77' |
| `kl_maps.py audit` | PASS (exit 0): 'RESULT: PASS (0 findings that must be 0, 0 known and accepted)' | the same | exit 1: 'FAIL (2 findings ...)' = 'no ZSquadScript: no police' + preflight's echo | PASS |
| `kl_fa.py check`, `kl_impact.py`, `kl_arms.py check`, `kl_chars.py check`, `kl_map_guns.py check` / `sizes`, `kl_map_escape.py van-check` / `check`, `kl_fa_bots_dyn.py check` / `fake-test`, `kl_fa_bank.py bots-check` / `reverify` / `check`, `kl_fa_talk.py check --str <new>`, cover lists, `kl_route.py` x 3 | exit 0, the lines of D1 | the same | the same | as D1 (no gun looks, no talk, no bot squad in a bare folder: those two checkers stop for want of their input) |
| NEW `kl_vault_str.py whd` | PASS: 3,730 streamed records, 0 without a block; 16 of 16 clips read back | the same | PASS (`--no-ai`): 7 of 7 (music + ambience; a build without guards names no guard line) | PASS: 16 of 16 |

THE STREAM-CLIP FINDING IS GONE on `bank_vault`, `bank_vault_wavslim` and `bank_vault_bare`; `bank_vault_noai` keeps
its 'no police'. NEW in preflight, on all four: 'RISK value x9 ZPlayMusicLayerFade[0] = eLayer4; stock has only eLayer1 ..
eLayer3' - the nine fades of the fourth layer that `--music-layer4` keeps (the stage that brings the music sets the
flag: MUSIC_LAYER4's note; without them the break-in set's basic layer is never faded out).
READ BACK (`checks/stream_whd.txt` in each folder): each of the sixteen names has ONE streamed record in the built .WHD;
its offset is the block of the table above; the index entry of that block and layer has the record's rate, channels and
size (music: PCM 32,000 Hz 2 ch, 9,215,656 bytes a break-in layer, 10,751,844 a way-out layer; ambience: Vorbis 2 ch
182,693; guards: ADPCM 32,000 Hz mono), and the bytes there are Dead Men's. Each folder has `stream.json`: the file, its
sha1, and 'bytes_needed' 1,751,738,528 (the end of the last block a record names).

### M.3 INSTALL, for the session that holds the game (this stage installed nothing)

THE ORDER MATTERS: THE STREAM FILE FIRST. A folder of `<c_bank_music>` loaded with the 1,694,610,488-byte file still in
the game folder has sixteen records that point at that file's TABLES (the guard lines, the ambience) or PAST ITS END (the
music, from 1,693,372,160): what the stream player does with that was never tried - do not try it. (KLTalk.ini's
StreamBytes 1,686,681,836 is the talk lines' need only and does not guard this; `stream.json` does, for a human.)
(Steps 2, 4 and 5 were REWRITTEN after the review, M.6: the first text copied straight over the live file and did not
name the expansion's overlay copy.)
THE SECOND TRAP: WHICH FILE THE GAME OPENS. READ klhook/klslot.c (Overlay) and kltalk.c (klk_stream_size): with
[Expansion] Enable=1 and Overlay=1 - the owner's KLHook.ini has both - a file `<DD>/KLExpansion/Overlay/PC_Def.str`
REPLACES `<DD>/PC_Def.str`. READ tools/kl_expansion.py build() (the 'merged' lines) and install(): BOTH put one there
unless `--no-stream`, and the file they take is `<tree's parent>/PC_Def.str` or else kl_snd's 'merged' place
`<work>/build/PC_Def.str` = MEASURED 1,684,486,009 bytes, sha1 `3b14a846...`, the file of 2026-10-09: older than the
talk, Bain and these clips (the installed tree's manifest names exactly that file, `in_tree: false`). With it in the
overlay Retomoto's talk is refused (StreamBytes 1,688,413,044 > 1,684,486,009), the Bain clips of all five tab maps
(from 1,688,475,392: the skeptic's figure, not re-measured) and the Vault's sixteen point into that file's tables or past its end. MEASURED today: no
`Overlay/PC_Def.str` exists in the game folder or in `<work>/build/w_tabM/KLExpansion` (every install so far used
`--no-stream`), so the trap is not sprung - it is sprung by ONE kl_expansion call without the flag.
1. Game closed (no kl2.exe with a thread).
2. The stream file, NOT by a plain copy over the live one (a copy cut short leaves no streamed sound on any map):
   `python tools/kl_vault_str.py put "<v_vault>/PC_Def.str" "<DD>" --kept "<work>/build/v_bain/over_talk/PC_Def.str"`
   = refusals first (a kl2.exe with a thread; an overlay copy that is another file; a sound bank under the game folder
   that names a block the source lacks; less than size + 1 GB free - C: had 45 GB), then copy to `<DD>/PC_Def.str.new`,
   read back (1,753,469,945 bytes, sha1 `80e53495ae550feb281f08d63b33619907f700cb`; else the .new file is removed and the
   game's file was never touched), then two renames; the old file is deleted only because `--kept` has its size and
   sha1 (MEASURED today: `<DD>/PC_Def.str` = over_talk's, sha1 `b0cb8bcd...`), otherwise it stays as
   `PC_Def.str.old_<sha1[:8]>`. BY HAND the same: copy to `PC_Def.str.new` in `<DD>`, check size and sha1 THERE, rename
   the old one aside, rename the new one in. Dog Days' ORIGINAL is `<DD>/KL_PortBackup/PC_Def.str` (1,217,890,070
   bytes): never touched, refused by `put` as a source. The .map.json and .bain.json stay in `<v_vault>`.
   `put` was run on a MADE-UP game folder only (M.6); on the real one it is the game holder's first run of it.
3. Every map already installed keeps working: stock, the tab's five (M.1), the silent `<c_bank>` folders (their
   records are a subset). So step 2 can be done at any time, also before the silent folders' first load.
4. Then the map, in D4's order but from `<c_bank_music>`: `bank_vault_noai` -> `bank_vault` -> `bank_vault_wavslim`
   (`python debug/slot.py put "<c_bank_music>/bank_vault" F01`, or the packaging of D5 with `--prebuilt`: the folder's
   audit.json is green now, so kl_expansion's 'known' entry for this map is not needed for these folders).
   EVERY `kl_expansion.py build` AND `install` FOR THIS MAP WITH `--no-stream`, as all tab installs so far.
   (noai first also isolates the forms: it has both music sets and the ambience but no ADPCM guard line.)
4b. BEFORE the first load and after every install: `python tools/kl_vault_str.py installed "<v_vault>/PC_Def.str" "<DD>"
   ["<tree about to be installed>"]` (read only, about 30 s) must end `INSTALLED: PASS`: no overlay copy (or it IS the
   wanted file), the file the game opens has the size and sha1 above, all sound banks under the game folder (240 to 248 today)
   resolve in it, no tree carries another stream file. In the game: the hook's line on Retomoto
   `talk: stream file ...\PC_Def.str has 1753469945 bytes ... ok` names the file that was opened and its size.
5. TO GO BACK: game closed; FIRST the map back to a `<c_bank>` folder (or off the slot), THEN
   `python tools/kl_vault_str.py put "<work>/build/v_bain/over_talk/PC_Def.str" "<DD>" --kept "<v_vault>/PC_Def.str"`
   (1,694,610,488 bytes, sha1 `b0cb8bcd5040462d3caec025e65939d85702a5f0`). `put` REFUSES the old file while a
   `<c_bank_music>` folder is anywhere under the game folder (16 records without a block) - never force it by hand.
   To stock: `tools/RESTORE Dog Days originals.bat` as always.
6. FOR LATER BUILDS OF ANY MAP: a build against `<work>/build/PC_Def.str.map.json` or the over_talk map stays valid with
   the new file. The next extension must take `<v_vault>/PC_Def.str` as its base (`kl_fa_talk.py stream --base`, `kl_bain.py
   build --stream`, `kl_vault_str.py build`), or these sixteen are lost again. `<work>/build/PC_Def.str` was not replaced.

### M.4 What to listen for, and what is GUESS / ASSUMED

- The break-in set from 1 s after the round-start event (MUSIC_AT, GUESS), its 'basic' layer at -14 dB and the others
  silent; the rise at the ante-room box; at the beat's end all four layers fade in 1 s and the way-out set starts; the
  vault's deeper ambience in the vault; the nine guard lines among the guards' other one-liners.
- ASSUMED, NEVER HEARD: a FOUR-layer interleaved PCM set (8 channels in turn). MEASURED: no map that has played holds a
  group of more than 3 (the tab's bank DM03: groups of 2 and 3; Retomoto, whose theme the owner HEARD: groups of 2); the
  .WHD's group byte and kl_whd.Writer.add_group carry 4 the same way. If the break-in set is noise, silent or faults,
  the way-out set (2 layers, Retomoto's form) is the control; the fall-back is the silent `<c_bank>` folder.
- ASSUMED: Dog Days fades `eLayer4` (READ: tools/dd_enums.json has eLayer1 .. eLayer4 = 0 .. 3; no stock level uses
  the fourth - preflight's RISK). A build without the nine fades: the same `test` line without `--music-layer4` (check() then
  prints a NOTE that the basic layer plays on).
- ASSUMED, as before this stage: streamed single IMA ADPCM records play (re/voice.md 7.3: a decode path no stock clip
  uses). The silent build already has 66 such records (the kept guards' one-liners), this one 75; the tab's maps have 0
  (their lines were moved into the .WAV). If the guards of this map are mute or garbled it is this, not the stream file.
- ASSUMED: Dead Men's Vorbis ambience plays from the merged file (the form of the ambiences merged for Retomoto).
- ASSUMED (kl_str): the engine reads the 0x38 header bytes and no table of the stream file; a file between 1.69 and
  2 GB behaves as the 1.69 GB one (the largest that ran). 394 MB are left under 2 GB; nothing past 2 GB was ever tried.
- Whether the round's own Fragile Alliance music (F07's) plays OVER the map's music was not looked at.

### M.5 Open

- Nothing ran in the game; nothing is installed.
- `kl_expansion.py`'s EXTRA entry for this map still names `<c_bank>` and pins the known finding: with a
  `<c_bank_music>` folder the finding is absent; the entry's text is that session's.
- `<work>/build/PC_Def.str` (kl_snd's fixed 'merged' place) is still the 1,684,486,009-byte file of 2026-10-09: every
  tool that builds without a `--str` resolves against ITS map (a subset of the new one). Making the new pair the
  default is the lead's call (it means replacing that file).
- kl_fa_talk.check's last line calls sizes() with slot F01 whatever the folder's slot is (it stops on the tab's DM09 =
  F06 unless called with the slot from Python): that file is another session's, told here.
- `kl_expansion.py` (another session's file) still takes `<work>/build/PC_Def.str` as the tree's stream file and copies
  it into `Overlay/` by default (M.3, M.6): until its default is `--no-stream` or its 'merged' is the installed file,
  the flag is a thing to REMEMBER. `kl_vault_str.py installed` is the check that does not depend on remembering.

### M.6 Review of the stage (2026-10-11, about 19:35 - 20:10): what the skeptic found, reproduced, and what changed

The stream file and the four folders were NOT rebuilt: no finding touches them. sha1 of `<v_vault>`'s three files, of
over_talk's and of all eight archives (`<c_bank_music>`, `<c_bank>`) are the same before and after this section's runs
(`C:/kl_scratch/vault_music/fix/sha1_before.txt` = `sha1_after.txt`). Changed: `tools/kl_vault_str.py` (+ `installed`,
`put`, `opened`, `unresolved`), M.3 above, this section. Outputs: `C:/kl_scratch/vault_music/fix/`.

1. CONFIRMED - the install text did not name the overlay copy. READ: klslot.c's overlay branch (any
   `<Root>/Overlay/<path relative to the game folder>` that is a file wins), kltalk.c klk_stream_size, kl_expansion.py
   build() / install(). MEASURED: `<work>/build/PC_Def.str` 1,684,486,009 bytes; the installed and the w_tabM manifest:
   `needs.stream_file` bytes 1684486009, `in_tree` false; under `<DD>` only `PC_Def.str` (1,694,610,488) and
   `KL_PortBackup/PC_Def.str` (1,217,890,070); `<DD>/KLExpansion/Overlay` holds Patch01.zip and Scenes only; the
   owner's KLHook.ini: [Expansion] Enable=1 Overlay=1. FIX: M.3's second trap, steps 4 / 4b, and `installed`.
   `installed` on the REAL game folder now (read only, before any install): overlay copy none; the game opens the
   1,694,610,488-byte file `b0cb8bcd...` = 'NOT the wanted file' (right: nothing is installed); at 19:38 240 sound banks, 92,970 streamed records, at 20:08 248 and 96,684 (the game holder installed something in between); both times
   0 findings; exit 1 for that one reason (`installed_before.txt`).
2. CONFIRMED - a 1.75 GB copy straight over the live file. MEASURED: C: 45 GB free (96 % full), G: 21 GB. FIX: `put`
   (M.3 step 2). TESTED on a made-up game folder `C:/kl_scratch/vault_music/fix/game` (dummy kl2.exe / dinput8.dll, the
   owner's KLHook.ini, the REAL two stream files, the tab's DM03 and DM09 banks; removed afterwards), `test_put.py`,
   16 of 16 PASS: a copy cut short at 64 MB is refused and the game's file keeps its sha1, no .new left; an overlay
   copy that is another file stops `put` and `installed` names it, `opened()` = the overlay copy; a music folder's bank
   with the old file = '16 streamed records name no block (first at 1692882176)'; the install comes out with the new
   sha1 and nothing beside it; a second `put` is a no-op; the WAY BACK is refused while the music bank is in the slot
   and done with the silent bank in it (without `--kept` the replaced file stays aside); a folder without kl2.exe and
   KL_PortBackup as a source are refused. NOT TESTED: the kl2.exe-is-running refusal against a running game (the rename
   fails by itself while the game holds the file: ASSUMED from Windows' sharing rules, not tried).
3. NOT A FAULT TO FIX, agreed with the skeptic and already in M.4: a four-clip PCM group, 75 streamed single ADPCM
   records and nine eLayer4 fades have never played in Dog Days. They are confined to The Vault; a failure is a mute,
   garbled or faulting Vault, not lost sound on a map the owner has. Nothing changed; the test order stays noai first.
RE-RUN after the change, all with the results of M.1 / M.2: `proof` PASS (5 of 5 parts), `levels` PASS (six levels),
`kl_str.py info` 'problems: none', `kl_str.py check ... M03_A` the known '33 clips' line, `tab` PASS on the five maps,
tabtalk byte-equal to the build stage's output (DM09's own countdown line, 0 Bain problems), `whd` PASS 16 / 16 / 16 and
7 with --no-ai, checks.sh on all four folders with every summary line equal to the build stage's (main and wavslim:
all exit 0, preflight 'CRASH 0, RISK 1, NOTE 76', audit PASS; noai: the one 'no police' finding in preflight and
audit; bare: guns and talk exit 1 for want of their input), `kl_fa_bank.py check <c_bank>/bank_vault` PASS. The
skeptic's own scripts cmp1 .. cmp8 again: same numbers (no differing byte in 0x38 .. 1,692,882,176; 10,199 of 10,199
clips; 40 tab banks / 19,066 records and 248 game banks / 96,682 records with 0 of every finding; 12 blocks equal Dead
Men's, problems 0).
STILL TRUE: NOTHING RAN IN THE GAME, nothing is installed, the game folder was only read.

(end of the Music stage)

---

## Run V2, diagnosed from the build (2026-10-11 night; OFFLINE, nothing built, nothing installed, no tool edited)

Asked: why the crew failed in live run V2 (`<work>/build/klhook/live/V2_vault_full.log`: the full map, an idle human,
`[Bots] Log=2 Escort=1`, `CopToCrew 0.05`), with the lead's hypothesis 'the tellers' four stacks pull the crew into
the hall instead of down to the vault'. Read: that log and V1's, the built level `<c_bank>/bank_vault` and, for
comparison, the tab's Withdrawal `<work>/build/w_tabM/KLExpansion/Maps/DM03` (read only). Scripts and their outputs:
`C:/kl_scratch/vault_fix/build/` (`diag.py` -> `vault.txt`, `dm03.txt`; `diag2.py` -> `vault2.txt`; `diag3.py` ->
`vault3.txt`). MEASURED = counted there; READ = the log's or the level's own words; GUESS says so.

### V2.1 THE HYPOTHESIS IS REFUTED: the crew went down, emptied the vault and died ON THE WAY OUT

- READ (the log's once-a-second crew line, GO = 19:26:57.9): at GO + 137 s the first vault money is paid
  (`4 bot ... $30000` at 19:29:15.2), and by GO + 155 s five bots hold 330,000 + 615,000 + 500,000 + 180,000 +
  675,000 = **2,300,000 = the vault's seven cases to the dollar**. The tellers' 300,000 was never touched.
- Why it looked otherwise: a 'lost' line exists only where a bot is HIT. MEASURED, hits by 20 s and floor: yard /
  dock 0 - 20 s (9); vault lobby 20 - 40 s (124 hits, 361 health at the 0.05 dial); the flights 40 - 80 s (115); the
  ante-room 60 - 80 s (9); **GO + 80 .. 160 s: one hit** (the gate's 56 s and the vault - nobody shot at them down
  there, so no line names y -960); the hall GO + 160 .. 220 s: **445 hits, 1,261 health**. 'Still at stage 1' is what
  a bot on the way out has: stage 2 is the EXITS plane AT the front entrance (303, 974, -9407), which none reached.
- Deaths (READ): record 1 at GO + 32 s, one step of 240 at (-900, 334, -6109) = the vault lobby's west end;
  record 7 at + 185 s (79 + 79 + 53 in 0.2 s at (617, 800, -8150)); record 4 at + 203 s (78 + 78 + 27 at
  (614 .. 631, 800, -8229 .. -8256)); records 6, 2, 5 at + 205 / 211 / 217 s by 150 - 200 small hits each (1 .. 8 a
  hit) at (609, 800, -8034), (229, 800, -6770) and (615, 800, -7647). Two of the five hall deaths are the point-blank
  rule (re/melee_damage.md: a step of the victim's whole rest), three are plain fire from many guns.
- The same crew in V1 (no enemies; READ): vault 2,300,000 by GO + 121 s, then THREE of the four teller stacks are
  taken IN THE HALL ON THE WAY OUT (records 2, 7, 3: + 75,000 each, GO + 155 .. 165 s), stage 2 from + 153 s, six
  aboard. So the tellers do pull - on the way out, for about 5 s a stack - and record 3, who took one last, got
  stage 3 but was never 'aboard': left in play with 495,000 to the end of the run.

### V2.2 The crew as BUILT (MEASURED, `vault.txt`; `bots.txt` / `dyn.txt` of the folder say the same)

- No station, hold or fork of any of the seven squads lies in the hall before the vault. Way in: ENTERS box
  (582, 199, -4822) -> vault lobby (0, 239, -6368), (394, 239, -7948) -> flights (399, -165, -9649) -> ante-room
  round (417, -960, -11871), `020_Timer_vault_opens` 56 s -> vault (390, -960, -12950), loot wait 15 / 30 / 45 s.
  Way out: -> lobby (394, 239, -7875) -> airlock (1546, 240, -6970) -> stairs (1230, 487, -5453) -> hall
  (300, 799, -6265), (736, 799, -8014) -> EXITS box (303, 799, -9362) -> street. Forks (2 - 6 a squad) are side
  ways of the same corridors; in the hall they use BOTH aisles (x 656 .. 816 and x -135 .. -214) and the east wall
  (x 1056 .. 1279).
- **There is no other way.** With the hall's 120 mesh polygons banned there is NO path from the ante-room, or from
  the yard, to the escape station (316, 700, -11070). The hall has one door in (foyer, (300, 800, -5800)), one out
  (front entrance, (300, 800, -9500), a 2 m gap) and four stairs to a gallery at y 1220: a 36 m crossing.
- In the hall the squads have 4 - 14 places each, NO sprint step, and holds with timers of 4 / 6 / 8 s (Squad#02
  4 s at (420, 800, -6246) and 4 s at (464, 800, -9264); #04 and #05 6 s; #07 8 s). Record 2 died standing at
  (229, 800, -6770) for 16 s = the hold `051_DefendBehaviour_pos_cover` (245, 800, -6778); record 5 at
  (615, 800, -7647) = the hold `052_DefendBehaviour_pos_cover_a` (659, 800, -7683).
- Loot window (800 / 400, re/bots_loot.md): 31 of the 81 places the seven squads have on the hall's floor have a teller stack in it (the east aisle:
  `TM_MoneyStack_025` (1367, 899, -8006) from every place x 656 .. 816; the west way: `_023` / `MoneyStack_100`).
  They can be taken (check(): 55 - 57 from the public edge), so the loot tactic may send a bot from the aisle to a
  counter at x 1310 / -710 - past the hall police's cover points (below). Not SEEN in V2 (nobody lived that long).
- Mesh path from the first bot (575, 200, -4350): the tellers 9,320 .. 10,176, the vault's cases 9,279 .. 9,841 -
  the same distance; at GO the tellers are 660 ABOVE the dock's floor, outside the window's 400 of height, and the
  seven cases are HIDDEN (entity flag 0x400) until the beat's end. Live at GO: the four teller stacks only (plain,
  shown, radius 125).

### V2.3 What stands in the hall when the crew comes up (MEASURED / READ, `vault.txt`, `vault2.txt`, `vault3.txt`)

| who | men | where they stand / go | when |
|---|---|---|---|
| F07's three hall squads (`HALL`) | 8 | in a row at z -9000, x -500 .. 1100: 3.5 - 4 m INSIDE the front entrance, between the crew and its only exit; `10_RunToCover` to (-500, -8400), (-300, -7800), (-500, -7200), (1100, -8400), (900, -7800), (1100, -7200), (100, -8600), (500, -8600) | not in the world until the beat timer (`RivalMercVan!Timer`, 48 s after the ante-room box) names `10_RunToCover`: about GO + 118 s in V2, 57 s before the crew |
| `Police_OutSide_SWAT_02`, `_03` (rifles) | 8 | `FlankingBehaviour` points IN the hall: (-545, 805, -7069), **(394, 802, -9406) = the front entrance itself**, (-70, 830, -8937), (671, 801, -8937) | the foyer box `Specials!LevelSpeak!TriggerBox` (300, 930, -5650): the FIRST criminal in the foyer = an AI heister at the hall's north door |
| `Police_Outside_Teargas_01`, `Police_OutSide_01`, `Police_Reinforce_Wave1_COOP_03` | 10 | flank points on the hall's GALLERY, y 1220, both sides: (-661, -7943), (1256, -7452), (-652, -7862), (1265, -7371), (1119, -6626); COOP_03's left flank (1113, 1222, -8524) is on no mesh | the same box |
| the two `..._ShieldSupport` men | 2 | `050_Move_In_01`: into the hall (`START_ROUT`, on purpose) | the same box |

- So 8 men are set up in the hall a minute before the crew, and at the moment the first bot steps into the foyer
  the whole 'plaza' wave of 20 is sent INTO the hall and onto its gallery: 28 guns on a 36 m crossing whose 2 m exit
  is a SWAT squad's own flank point. The plaza itself is left empty.
- READ: `10_RunToCover`'s next list is empty and nothing names `10_Defend` or `30_smUnleash` (the comment over
  `HALL` says 'the point of 10_Defend'; no rout ever goes there): the hall squads stay at their cover points.
- MEASURED, nearest place of each bot squad to a hall cover point: 85 (Squad#05's hold `052_..._pos_cover_c_c`
  (575, 800, -8639) against (500, -8600)), 159, 173, 174, 237, 265, 302; to a SWAT flank point: every squad's EXITS
  place is 44 .. 186 from (394, 802, -9406). The point-blank rule's ball is 160. check() / bots_check test none of
  this: `BEAT_CLEAR` asks only that late squads stand 1000 from stations BEFORE their trigger, `LANE_CLEAR` is the van's.
- For scale, the tab's Withdrawal (MEASURED, `dm03.txt`): the same hall, crossed the other way; 15 armed men in the
  whole level in 9 squads, TWO of them in the hall (at its foyer end, (625, 803, -5996) and (-144, 803, -5947)),
  the nearest man to any place of a bot squad 132. The Vault: 61 men, 28 of them told into the hall.
- The 14 police of the beat and the five hunts into the vault: between GO + 80 and + 160 s no bot lost a point, so
  none of them fought the crew at the vault or on the way up. Whether they came down at all is NOT established
  (the log has no line for enemies). GUESS: they were still upstairs, or dead - one more thing a watched run shows.

### V2.4 The escort and the dial (READ)

- `[Bots] Escort=1` with an idle human: record 3 was chosen 3 s after GO and re-pointed 15 times to 8 - 14 m from the
  player, who stood at (250, 200, -4350); it never went past z -5446, earned nothing, and is the one survivor.
  So V2's crew was FIVE after the first death, not seven. An idle-human test of the crew wants `Escort=0`.
- While that bot stood in the yard its squad's chain went on: the escort's lines give 'its route place' as the
  ante-room (479, -960, -11973) at GO + 43 s, the vault (505, -960, -13031) at + 109 s, the street at + 195 s.
  So a chain can run ahead of its man. NOT established why (the escort's own order may end a Defend step).
  Consequence for `bots_gate`: 'a bot that holds in the ante-room stands inside the beat's box, so the beat began
  when it arrived' holds only for a bot that is THERE; a squad whose man is held up can be sent on to the vault
  place while the door's body still stands. Harmless in V2 (others had started the beat).
- The dial was 0.05. On the way IN one bot was at 26 of 252 in the vault lobby (GO + 44 s) and the lobby cost 361
  health in 20 s; the owner's ini has 0.15. At 0.15 this crew, alone, does not reach the vault. The map is laid out
  for a human who shoots; V2 measured six bots alone against 61.

### V2.5 WHAT THE FIX MUST BE, in this module's terms (nothing of it is written; every place below is to be MEASURED)

1. **The plaza wave stays on the plaza** (the largest term: 20 of the 28). `STAGE`'s 'plaza' squads are started by
   the foyer box and their flank points are the campaign's, in the hall. Wanted, behind a named flag (default = as
   built, e.g. `PLAZA_IN_HALL = True` / `--plaza-outside`): (a) started by the EXITS plane at the front entrance
   (the stage-2 trigger) or a box just inside it, not by the foyer box - the foyer box keeps the line 'Get out on
   the street!'; (b) the five flanking squads' `LeftFlank#1` / `RightFlank#1` re-laid on the plaza and the street
   (z < -9500, y 700 .. 812), as `HALL` re-lays F07's squads; (c) `START_ROUT` of the two shield men back off the
   hall. That is the owner's 'big shootout' where the van is, with 61 men still in the level.
2. **The hall squads off the crew's line** (`HALL`): the men's row at z -9000 and the cover points at x 100 / 500,
   z -8600 are in the mouth of the only exit; cover points at x -300 / 900 are 159 - 174 from the aisles' places.
   Wanted: places at the hall's sides or on the gallery, and a new test in `bots_check`: no place of a bot squad
   within the point-blank ball (160) + a margin (GUESS 250) of a man's start, a cover point, a flank point or a
   defend place of any enemy squad - it FAILS the delivered folder as it is (85, 44).
3. **The crew crosses the hall in one go**: a step after the dynamic one (this module's, as `seal` is; the dynamic
   tool is not this file's): every `DefendBehaviourRout` of the bots' squads with a place in the hall box gets
   `eDMS_Sprint` (field 4) and the hold timers those steps start are set to 0 (or the hold steps taken out).
   Flag, default off.
4. **The tellers**: not the cause, but a cost in the same 36 m - a bot stops for a stack under every gun of the hall,
   and one missed the van for it in V1. Flag (default = as built): the four stacks out, or their 300,000 moved into
   the vault lobby (y 240, on the way in, where the tab's Withdrawal has its eight cases).
5. Not this module's: an idle-human test with `Escort=0`; `[Balance] CopToCrew` is not a cure (V2 had 0.05).

### V2.6 Other faults seen on the way

- `HALL`'s comment promises a 'point of 10_Defend'; no rout names it (V2.3).
- `Police_Reinforce_Wave1_COOP_03\FlankingBehaviour\LeftFlank#1` (1113, 1222, -8524) is on no mesh polygon;
  check() counts only Defend places and search boxes ('83 places their behaviour routs name').
- The hall's 8 come into the world at their row inside the front entrance: a human who is in the hall at the
  beat's end (nothing stops him: every door is open from the load, the tellers are live at GO) sees them appear.
- Record 1's death at GO + 32 s: a hold of the dynamic step at a cover box in the lobby's west end
  (`010_DefendBehaviour_pos_cover_b` (-965, 240, -6244) of Squad#08, or `_c` (-645, 240, -6014) of Squad#02), 9 - 10 m
  off the route, where a guard reached arm's length. GUESS: one of the dock patrol's two (their place
  (-496, 241, -5083)). Holds are chosen by cover boxes alone; where the enemies stand is not asked.
- V1: record 3 at stage 3 with 495,000 was never aboard (the van stands 8 s; `BoardAll` was off in that run's first
  `[Bots]` block and on in the second - which the hook took is not read here).
- The run's ini has `[Bots]` three times and `[Balance]` twice with different values (`Escort`, `BoardAll`,
  `FollowOut`, `Tune`, `Log` each twice): what the hook used is what its first log lines say, not the file.

(end of the V2 diagnosis)

## Crew fix after run V2 (2026-10-11 night; OFFLINE: built and checked, NOT RUN IN THE GAME, nothing installed)

Folders: `<work>/build/c_bank2` (silent, against the installed stream file) and `<work>/build/c_bank2_music` (with
`--music-layer4 --str <work>/build/v_vault/PC_Def.str`), the four names each. `c_bank` / `c_bank_music` (runs V0 - V2)
are untouched. Each folder set holds its own `chain.sh`, `checks.sh`, `crew_route.py`; the driver of the whole rebuild
is `C:/kl_scratch/vault_fix/s/run_all.sh <silent|music>`.

### X.1 The diagnosis (two readers, settled on the log and the build)
- MEASURED: the crew did NOT go to the hall instead of the vault. $0 for every bot until GO + 137 s, then five bots
  take 2,300,000 = the vault's seven cases; they come up again and die in the BANKING HALL ON THE WAY OUT
  (GO + 185 .. 217 s). 'Stage 1' is right for a bot short of the EXITS plane; 'nobody at y -960' was read off 'lost'
  lines, which exist only where a bot is hit (one hit in all between GO + 80 and + 160 s). The lead's hypothesis
  (teller stacks + open doors pull the crew into the hall first) is REFUTED: no station, hold or fork lies in the
  hall before the vault (`crew_route.py`: gate's hold station 5, vault's loot 6, first hall station 12 of 16).
- WHY THEY DIE THERE (MEASURED on the build of V2): the hall is the only way out (one door in, a 2 m door out, 36 m);
  F07's 8 hall police came into the world in a row 3.5 - 4 m inside that exit and their places lay 39 .. 174 from the
  heisters' own on both aisles; the foyer box started the plaza's 20 for the first criminal at the hall's NORTH door
  and their campaign flank points are in the hall, one IN the entrance gap (394, 802, -9406), six on the gallery;
  the heisters crossed with cover holds (28 s of hold timers) and no sprint. Two of five hall deaths are point-blank
  steps (79 + 79 + 53, 78 + 78 + 27; re/melee_damage.md), three were shot standing 9 - 25 s at holds.
- THE ONE DISAGREEMENT, settled (MEASURED): the balance dial was OFF in V2. `V2_vault_full.ini` has `[Balance]`
  twice - the first one is `Log=1[Crew]` (a lost newline) without `Enable` - and `V2_vault_full.log` has 0 'balance:'
  lines (V1: 20, 'balance: on; ... police->crew 0.05'). V2 ran on stock Arcade level 1: police -> crew 0.01, a
  heister off the human's stage x 0.5 against police. 79 a step = 66 x 1.2 x 100 x 0.01. 'CopToCrew 0.05' was NOT in
  force; at 0.05 a point-blank step is 395. NOTHING ABOUT THE BALANCE CAN BE READ FROM V2.
- Not this module's, for the run: `Escort=1` with an idle human parks one of the seven in the yard for the round.

### X.2 The change (tools/kl_fa_bank.py; every flag OFF by default = the level of V0 - V2; no man taken out: 61)
The tellers and the route's order are NOT changed (they were not the cause).
1. `PLAZA_OUTSIDE` (`test --plaza-outside`): the plaza's seven squads (20 men) stay on the plaza. `PLAZA_PLACES`: 14
   places of their routs (ten flank points, the two shield men's `050_Move_In_01`, COOP_03's `Cutscene_MoveOutside`)
   re-laid on the two sides of the plaza, x -1450 .. 1700, z -10650 .. -9900 (GUESS: every place; MEASURED: on the
   START's mesh part, free floor, 12 of them were in the hall, none is left in `HALL_BOX`). They are started by
   stock F07's own box `Gameplay!030_AfterLoot!tbExitFinancialAlley`, re-placed across the hall's SOUTH end
   (z -9200 .. -8200, fires once, criminals only), not by the foyer box, which keeps only the line.
   ASSUMPTION: a flanking rout takes its men to its two places and they fight from there.
2. `HALL_UP` (`test --hall-gallery`): F07's eight hall police on the hall's GALLERY (y 1221; `HALL_GALLERY`): three on
   each long side, a pair at the north corners. The floor is the crew's; the nearest police place to a heister's is
   421 (straight up). GUESS: every place; MEASURED: on the mesh part of the START. ASSUMPTION: they fire down from the
   rail (F07's cover-point rout, unchanged in kind). Still true: nothing names `10_Defend` - they stay at the rail.
3. `hall-dash <folder>` (a chain step after kl_fa_bots_dyn, before seal; .prp only): every Defend step of a heister
   squad with a place in `DASH_BOX` (the hall's floor south of the foyer) is `eDMS_Sprint`, the hold timers those
   steps start are 0 s. On the build: 25 steps of 7 squads, 5 timers (4 / 6 s) -> 0. GUESS: a sprint is better than a
   hold under fire from above.
4. `crew-check <folder>` (new test, in checks.sh): no heister place within `CREW_CLEAR` 400 (160 point-blank reach +
   GUESS 240) of a man, cover point, flank point or defend place of a hall / plaza squad. `c_bank/bank_vault`: FAILS
   (hall 39, 92 pairs; plaza 43, 27 pairs). `c_bank2/bank_vault`: PASS (hall 421, plaza 469).
   `check()` also says where the hall's police stand and FAILS a plaza rout place left in the hall.
`test --crew-fix` = 1 + 2; `c_bank2*/chain.sh` runs 3.

### X.3 The rebuild
`kl_fa_bank.py test <out> --keep --crew-fix [--no-ai] [--music-layer4 --str ...] --plan <c_bank>/bank_vault_bare/van.json`,
then chain.sh (the delivery's + `hall-dash`), then checks.sh (the delivery's + `crew`, `crew_route`).
Silent, `c_bank2` (zip sha1): bank_vault 8f67ac56 = bank_vault_wavslim; bank_vault_noai e48e40a7; bank_vault_bare
ba85322a. Blocks as before (159.9 / 149.8 / 150.1 / 149.1 MB, chunk table 65,852). EVERY CHECKER PASSES except
`kl_maps preflight` CRASH 1 / `audit` FAIL 2 (noai 3) = the known stream-clip finding of the silent set, and on the
bare folder `guns` / `talk` (no such step there, as in the delivery). kl_route: route_walk FREE (START -> vault ->
hall -> front entrance -> boarding place), route_built FREE, crew_route PASS on the 16 stations 'THE VAULT BEFORE THE
HALL'.
Music, `c_bank2_music` (zip sha1): bank_vault c869dda8 = bank_vault_wavslim; bank_vault_noai 2e6d5163;
bank_vault_bare 0ac3c519. Same blocks. All checkers PASS incl. `kl_vault_str.py whd` (WHD: PASS on all four), crew,
crew_route; left: the known RISK 'eLayer4' (x9), on noai 'no ZSquadScript: no police' (by design), on bare guns / talk.
The music set needs the stream file `<work>/build/v_vault/PC_Def.str` installed first (Music stage M.3 / M.6).
CONTROL (MEASURED): `test --keep --plan ...` WITHOUT the new flags still gives the bare archive of runs V0 - V2
byte for byte (sha1 b7e48d31): the defaults are unchanged. tools/kl_fa_club.py imports the module as before.

### X.4 What the next live run must show (V3 = c_bank2/bank_vault, owner away)
THE INI FIRST: one `[Balance]` and one `[Bots]` section; the log must have 'balance: on; ... police->crew 0.05' (V2
had no 'balance:' line). `Escort=0` for an idle human (else one of seven is parked in the yard).
- as V2 up to the vault: stage 1 at GO + 12 .. 19 s, first vault money about GO + 137 s, 2,300,000 in the crew;
- NEW: heisters past z -8635 in the hall, 'heist stage 1 -> 2' lines (the EXITS plane; V2: none), then stage 3, the
  van's state leaving 0, 'aboard' / 'status6'; hall 'lost' lines (y 800) well under V2's 445, no bot standing more
  than a few seconds between z -6400 and -9420; no point-blank step (three hits of 79 or 395 within 0.3 s) there;
- the second fight is on the plaza: 'lost' lines at y 700, z < -9500 after the first bot is in the hall's last 10 m;
- to LOOK at (pictures / a human): the eight police on the gallery do fire down and do not stand in the air; the
  plaza's men are on the two sides of the plaza, not in the entrance; nobody appears in the human's sight.
NOT SHOWN BY ANY CHECK: that the crew now survives. With the dial really at 0.05 the way IN is five times harder
than V2 was (bot 4 was at 24 of 252 in the vault lobby at 0.01): if they die before the vault, that is the 19 guards
of 'start' / 'down' and the balance, not this change. Still open from V2: whether the 14 beat police and the five
hunts ever reach the crew in the vault (no hit GO + 74 .. 170 s); the point-blank key (re/melee_damage.patch).


## Waves (2026-10-11 night, SECOND ROUND; OFFLINE: built and checked, NOT RUN IN THE GAME, nothing installed)

Folders (second round): `C:/kl_build/c_bank4_fx` (silent, against the installed stream file) and `C:/kl_build/c_bank4_music_fx` (with
`--music-layer4 --str <work>/build/v_vault/PC_Def.str`), the four names each, every one padded by `kl_fa_vaultfx.py apply` (`check` PASS). They
are on C: because G: is full; copy them into `<work>/build/` when there is room. `c_bank3*` (the first waves build: a one-shot set of 24 men)
and `c_bank2*` / `c_bank*` are untouched and superseded by these. The owner, 21:48: 'i want the vault enemies to keep spawning in like its
in waves'; ~21:45: 'all the police outside the vault shoot the van straight away ... only spawns in once theyre close'; ~22:00:
'after the first round the vault door is open so thats a bug'; 'need better enemy spawns ... for them to be in that lobby underneath
... should put some money in the cash registers up top so people could hold the swat from coming in and get rewarded'. This section is the
tool (`tools/kl_fa_bank.py`: `test --waves`, the chain step `extras`, the check `waves-check`), the supply AS BUILT, the flags, the skeptic's
seven findings on the first waves build and what became of each (W.10), and what the live run must show.

### W.1 The mechanism (every flag OFF by default: no flag = the crew-fix build byte for byte)
1. **Parked squads, started by the crew's own progress.** A wave is 2 - 3 cloned police (the models, weapons and soldier rows of an
   existing squad's men) in a new top-level squad `Gameplay!bank_waves!Wave_<name>` with `ZSquadScript` field 3 = 0 (not in the world until
   a rout is named: ran live in every stock FA round, on Retomoto, and for all 25 squads of The Vault). Below it ONE `DefendBehaviourRout`
   `10_Defend` and one `Pos#NN` box a man: each man his own post. The rout has no next list: they hold their posts, in position waiting.
2. **A supply is a CHAIN of links, three chains by the crew's phase (new in this round).** Link i of a chain starts wave i and arms link
   i + 1; a link is three `TriggerDelay2` nodes of the clock group `Gameplay!bank_waves!Clock` (one-shot, re-arm -1, cloned from the
   start timer):
   `Pace_<w>` (the wait: the chain's gap) -> `Go_<w>` (0.1 s; its list: the wave's `10_Defend` and the NEXT `Pace`) and `Fast_<w>`
   (the latch: 12 s) -> `Go_<w>`, named by the 'wiped out' list (`ZSquadScript` field 8) of the PREVIOUS wave. `Go` fires once, so the
   timer and the latch can both reach it and the first wins; the latch only ever brings a wave EARLIER. The first `Pace` of a chain is
   named by ONE existing trigger: phase A the round-start timer (the whole round: the FLOOR), phase B the ante-room box (once; the crew is
   downstairs), phase D the plaza box (once; the crew is at the hall's south end). The last link names no timer: **every chain stops**,
   and the round ends with the vehicle's departure. Nothing in level data cancels an armed timer (GUESS that a leftover one is harmless).
   ASSUMED: that field 8 fires when a squad's men have all died (nothing in this level uses it; Retomoto's street chain was never watched);
   if it fired for a parked squad at the load, every `Fast` would run 12 s after its `Go` and the supply would take 12 s a link instead of
   the gap - which is why the floor is tested on the `Pace` chain alone. The latch is OFF by default since the second skeptic (W.11); `--waves-latch` adds it.
3. **Sight and distance chosen at build time, tested again on the folder.** `wave_plan` picks entries and posts in the boxes of
   `chain_table()` (a post box may be a tuple of boxes, the first preferred); `waves-check` re-tests every man of the written level: on
   the START's mesh part, 30 from a wall, **blind from the stations of the regions the crew is in while the wave comes** (`Sight`:
   `kl_route.Grid` of the collision, flag 0x10 shapes block - ASSUMED meaning -, eye 160 / target 120 and 175, 90 m), 250 (phase D 400)
   from any station of those regions, 70 from another man's entry of a wave within 20 s, **300 from every LEG of the round's way**
   (`route_dist`: ROUTE_IN + ROUTE_VAULT + ROUTE_OUT, point to segment, 3D - entries AND posts; was the finding that phase B stood ON
   the leg vault lobby - airlock - stairs). A post is 45 from a wall, 150 .. 300 from every other wave post (`POST_GAPS`: the planner
   tries 3.0 m, 2.2 m, then 1.5 m = `POST_GAP_MIN`; MEASURED: all 54 posts came out at 3.0 m), 100 / 150 from a place of an old squad,
   and phase D's are `LANE_CLEAR` (250) from the van's drive. Phase A and B posts are picked NEAREST THE CREW'S WAY (just beyond the 3 m)
   so that the men a slow human meets stand where he is, not 30 m off in the yard.

### W.2 The supply as built (MEASURED by `waves-check` on the written folders; GUESS: every box, gap and number)
Totals: **A 11 waves / 25 men, B 5 / 5, D 8 / 24 = 24 squads, 54 men** on top of the 61 (+ the 7 heisters): 122 actors, 56 squads (W.11: B is five single-man links). Against
12 men a squad (largest 3), 500 squads (53), the largest stock STORY level 147 actors (122), and what has run live in the game, Retomoto
on the tab with 99 actors / 55 squads: **the actors are 23 past what has run live** (`check()` allows `WAVES_ACTORS` = 147 / 500 and says
so; `--waves-extra N` thins it, a chain is cut from its END). 273 entities added (MEASURED, `extras.json`): 21 squads with 21 routs, 54 posts and 54 men (a group and an actor each), the clock group, 60 chain
nodes (21 `Pace`, 21 `Go`, 18 `Fast`) and 8 switches (reset 2, van 1 + 3 timers, teller 1 + 1 timer); the chunk table is unchanged (65,852: a cloned `ZFFActor` that reuses a police model adds
entities, not chunks: ASSUMED for the clone, MEASURED by `sizes`).
| chain: trigger | links | first after the trigger | then every | last wave at | men a wave | where they come from -> where they stand |
|---|---|---|---|---|---|---|
| A: the round-start timer | 11 (A01 .. A11) | 12 s | 35 s | 362 s | 3, 3, 3, then 2 | the yard's east lane and west end, one after the other -> posts 3 .. 12 m beside the crew's first leg (dock, yard, armoury) |
| B: the ante-room box (once) | 5 (B01 .. B05) | 22 s | 30 s | 142 s | 1 each | the airlock corridor (1580, 240, -6560), 3 m+ from the leg -> the lobby underneath, 3 .. 8.5 m off the way |
| D: the plaza box (once) | 8 (D01 .. D08) | 3 s | 25 s | 178 s | 3 | the hall's two corner recesses, left and right in turn -> posts on the plaza's two sides, 8 .. 31 m from the crew's way, 2.5 m+ off the van's drive |
**THE FLOOR: chain A alone outlasts a human who takes his time (last wave 362 s >= `SUPPLY_MIN` 360 s; `waves-check` FAILS below it).** A
human who sprints reaches B at about GO + 90 s and D at about GO + 190 s; each adds its pressure where he is. One who dawdles in the dock
for six minutes meets 25 men in eleven arrivals 35 s apart; one who dawdles on the plaza meets D's 24 over 3 minutes. The seven AI heisters
alone meet A on the way in (a wave of three is at their posts by +12 + 20 s) and B on the way down; the hall's exit gets D only after the
dash (the first D wave comes into the world 3 s after the plaza box from the recesses, 400 from every station).

### W.3 The flags (`kl_fa_bank.py test <out> ... `; each is also a module variable; `bank_opts.json` beside the archive carries them to the chain's steps)
| flag | variable | what | default |
|---|---|---|---|
| `--waves` | `WAVES` | the three chains; implies `--crew-fix`, `--crew-fix2`, `--teller-late`, `--teller-more`, `--van-late`, `--reset` | off |
| `--waves-extra N` | `WAVES_EXTRA` | men on top of the 61 (0 .. 79 = `WAVES_ACTORS` 147 less the 68 there are); a chain is cut from its END | 54 |
| `--waves-near M` | `WAVES_NEAR` | the softer crew line of phases A and B | 250 |
| `--waves-latch` | `WAVES_LATCH` | add the 'wiped out' latch (W.1 point 2) | latch OFF (W.11) |
| `--crew-fix2` | `CREW_FIX2` | the review points (a) and (c) of W.4; `dash_chain` now follows a '_pos_cover' rout the step names DIRECTLY too | off |
| `--teller-late` | `TELLER_LATE` | the teller stacks lie hidden, shown `TELLER_SHOW` (20 s) after the plaza box | off; on with `--waves` |
| `--teller-more` / `--no-teller-more` | `TELLER_MORE` | six stacks of 100,000 (the two middle counters too) instead of four of 75,000 | off; on with `--waves` |
| `--van-late` | `VAN_LATE` | the van is hidden from the load, its FakeTarget off; shown by the foyer box + 6 s, the plaza box + 1 s, or (backstop) the ante-room box + 120 s | off; on with `--waves` (`--no-van-late`) |
| `--no-van-hide`, `--no-van-target-off` | `VAN_HIDE`, `VAN_NO_TARGET` | the two halves of `--van-late` separately | both on |
| `--reset` | `RESET` | the round-restart objects (W.5) | off; on with `--waves` |
The delivery's commands: `kl_fa_bank.py test <out> --keep --waves [--no-ai] [--music-layer4 --str ...] --plan <c_bank>/bank_vault_bare/van.json`
for the chain's input, `test <out> --keep --crew-fix [--music-layer4 --str ...] --plan ...` for the DELIVERED `bank_vault_bare` (nothing
hidden, no chain is owed: W.10 finding 5), then `chain.sh` (the crew fix's + the step `extras` between `hall-dash` and `seal`: it adds
entities, `seal` must stay last), `kl_fa_vaultfx.py apply`, `checks.sh` (+ `waves`). The scripts are in each folder (`chain.sh`, `checks.sh`,
`crew_route.py`, `blocks.py`); the driver of this round is `C:/kl_scratch/vault_waves2/scripts/` (`all.sh` -> `run_all.sh`, `final.sh`).

### W.4 The three review points of the crew fix
- **(a) DONE.** `DASH_BOX`'s north edge z -6400 -> `DASH_NORTH` -5800, the foyer-to-hall door (READ, the research: mesh polygon 815,
  x 235..364, z -5799..-5744). MEASURED: 10 more Defend steps of the heister squads are dashes now, among them the four live
  6 - 8 s holds of Squad#04 / #07 (z -6235 .. -6116); the foyer room (z > -5744) is left alone; the gallery pair is 421 .. 657 from
  those places and stays.
- **(b) DONE in the second round (W.10 finding 4).** The owner's 21:40 word (the tellers stay, 'cash registers') is met: six stacks of
  100,000 on the counters, shown 20 s after the plaza box, not with the vault's loot. MEASURED: a stack pulls a bot only inside the
  loot window (800 / 400); the crew crosses the hall on the way OUT after the vault; at the box a bot is 2 .. 10 m from the stacks, 20 s
  later (GUESS: ~60 m of a dash) it is past them. NOT made un-takeable for the bots (no such kind in the loot tactic's reading).
- **(c) FALLBACK.** The review's cure (the cover reference out of a dash step's next list) was built (`DASH_CUT_COVER`) and TRIED on
  the delivered chain's folder: `kl_fa_bots_dyn.check` FAILS ('N step(s) nothing starts', 4 squads, 36 cover steps) - the cover
  steps and the `RandomTrigger` are then named by nothing, and taking nodes out below the top level needs an entity removal
  `kl_prpjoin.join` does not offer. (Second round: the fallback now also reaches the '_pos_cover' rout a dash step names DIRECTLY - Squad#02 / #03 / #04: 3 more timers, 4 - 6 s -> 1.5 s - and `crew-check` follows 4 hops.) So the default is the proven form: the cover branch STAYS (a cover rout and a hold timer in one list
  ran live in V0 - V2, with 4 - 8 s) and the hold timers of the dash steps are `DASH_GAP` = 1.5 s (a shorter number of the live form) instead of
  the 0 s of the crew fix, which has no precedent. `crew-check` FAILS a dash step with a cover branch and a timer under 0.05 s.
  GUESS: that 1.5 s under a cover order is better than 6 - 8 s or none.

### W.5 The round-restart bug ('the vault door is open in round 2')
READ (re/fa_round.md 4, 6: 'Ready, round 2 ... the next round on the same loaded level'; re/fa_gamemode.md 3, 5; re/fed_points.md): a
round after the first is NOT a level load - the scene, its objects and their show / hide state stay. What a stock level brings back
per round is done by the round-start event's list (AIMonitor list 2, raised every round): F02 switches its money objects off there
(`GeomDeactivator ... level_start_get_rid_of_ai_relevant_stuff`), Retomoto's blast timer names the chair pair (`GeomActivator_ChairPost` /
`GeomDeactivator_ChairsPre`) EVERY round and so puts the points right 'whether or not the game restored them'. This module never did:
what the beat switches (`DeactivateGeom` of the door's body 6 s after the door's 'Activate', the intact vault off, the blown vault, fire
and smoke on, the vault's loot on, the alarm / rod / door sounds on) was left switched in round 2. The vault door is 'open' because its
body is gone and the blown vault is shown.
THE FIX (`--reset`, the step `extras`): `Clock\Reset_show` (an `ActivateGeom`) and `Clock\Reset_hide` (a `DeactivateGeom`), the FIRST two
entries of the round-start list; lists READ from the finished level (`reset_lists`): shown again = every target of every
`DeactivateGeom` the module switches in a round (28 here: the door's body, the intact vault's 26 parts, ...), hidden again = every
target of every `ActivateGeom` (+ the late van's group): the blown vault, fire, smoke, the vault's loot, the teller stacks, the
sounds (53). In round 1 both are no-ops (shown stays shown, hidden stays hidden: kl2 0x4c4912, 0x668172 - the Retomoto chairs'
precedent). `waves-check` / `check()` FAIL when a node the module switches is not named by the reset (ROLE, CAMP, the clock group's
own) or when the reset is not first in the list.
**CANNOT BE RESET BY DATA** (printed by `extras`; for the session that holds klhook): the `MatPosAnim` end poses - the vault door's
group (`SI0102_M03_BankVault_Door_PRE_01`, frames 0..200, one way, 'Activate' only), the six rods (`Rod_A01` .. `Rod_F01`), and the
leaves with `--doors-animate`; the alarm lamps' glow (`VertAnim`, AIDWrapper 'Activate'); the blast's `Explode` (one-shot); the music
(the round-start list starts it again). A hook-side reset would write the MatPosAnim's current-time field to its first frame and
re-apply the group's start transform for those 8 nodes at the round start (state 0x19 edge); the field offsets of the instance were
NOT read. If round 2 shows the door SHUT but swung (the leaf at its end pose, body back), that is this.
ASSUMED: that the engine does not already restore the state (it does not, by the owner's report), that 'Squads and one-shot
triggers come back by the game' (stock rounds rely on it - the squads of round 1 are not read), and that a `TriggerDelay2` / `TriggerBox`
of this module (field 15 = 0) fires again in round 2.

### W.6 The late van
MEASURED in the written level: the van carries ONE `FakeTarget` (faction 'Mercenary', `V_Van_00\Body\Body_Main`) - the object police
aim at - and waits 54 m west of its stop from the load, in sight of the plaza's squads. `--van-late`: the FakeTarget controller is taken
off (the 0x686a66 rule - a FakeTarget outside the vision space - cannot bite with none; `check()` and `kl_fa_bots_dyn` wanted one and
want none now) and the van's group is hidden at the load (`ZGEOM[3]` + the .gms flag, the form the vault's loot has); `Clock\Van_show`
(`ActivateGeom`) shows it `VAN_SHOW` (1 s) after the plaza box (`Timer_van`), `VAN_FOYER` (6 s) after the FOYER box (`Specials!LevelSpeak!TriggerBox`,
`Timer_van_c`: 30 m earlier; the plaza box has never fired live in the Vault) and, as a backstop, `VAN_BACKSTOP` (120 s) after the ante-room box
(`Timer_van_b`); all three show the same group, the first one wins and the others do nothing. `waves-check` FAILS: a FakeTarget left on the van; the group not hidden; the timer named by anything but the plaza
box; any police rout / search box / squad list of the old squads or the waves naming the van. **A waiting van that kept a FakeTarget
would do so because every stock van has one (12 of 12) - it does not here.**
NOT BUILT, and why: the van does not 'arrive from afar when the exit box calls it'. The exit trigger names the van only in its field 2
(no list to hang a show on), the vehicle monitor's lists 2 and 3 are clean-up lists, and `ESC.van_plan_points` pins the waiting place
to the key length (6000 units = 54 m before the stop even with a way point at x -8200: MEASURED, `lin` 6000). A hidden keyed vehicle
is ASSUMED to run its key frames hidden and to board normally when shown (not seen: V3 decides). Fallbacks, in this order:
`--no-van-hide` (FakeTarget off, van visible), then `--no-van-late` (the V2 van).

### W.7 What the next live run (V3 on `c_bank4_fx/bank_vault`, owner away) must show
THE INI: one `[Balance]`, one `[Bots]`; `Escort=0` for an idle human (X.4). Copy the folder from C: first.
- round 1 to the vault as X.4; NEW: 'wave' squads in `[Bots] Log=2` / the pictures: A01 walks in from the yard's east lane GO + ~12 s + ~20 s
  (nobody 'plops'), A02 from the west end 35 s later, then a pair every 35 s up to A11 at GO + 362 s: a slow human in the dock is never
  without an arrival; B01 / B02 come into the airlock corridor 22 / 46 s after the ante-room box and walk to the lobby posts; D01 .. D08 come
  from the bank's two corner recesses 3 s, then every 25 s, after the hall's south end box (left, right, left ...) and walk to posts on the
  plaza's two sides; nobody comes into the world in sight of a heister. THE LATCH: if a wave is killed, the next one should come 12 s
  after, not at the full gap (a wave of the same chain arriving EARLIER than its Pace is the latch working; arriving 12 s after the
  previous Go at the very start, all of them, is the latch firing for parked squads: the build has no latch unless `--waves-latch` was given);
- the van is not there until the foyer box + 6 s (or the plaza box + 1 s); no police fire at it before; it boards as before;
- the cash registers: six stacks appear in the hall 20 s after the plaza box (the first D wave is then 17 s old): a human who holds the
  hall's south end and kills D01 / D02 can pick up 600,000 behind him; the bots mostly have left (look at whether any turns back);
- round 2 (play a second round in the same process): the vault door's body is back and the intact vault shown, no blown vault / fire /
  smoke, the vault's loot and the teller stacks hidden until the beat, no alarm sound at the start; the chains start again (A01 at
  +12 s). If the door leaf stands at its swung pose it is the MatPosAnim (W.5), and the hook-side reset is what is missing. If NO wave comes
  in round 2 the one-shot timers did not come back (ASSUMED that the game re-arms them with the round, as the stock one-shot triggers);
- to LOOK at: 54 men are 'in position' and not bunched (3 m apart or more); the crew does not die before the vault more than in V1 / V2
  (the way in has 25 more men over six minutes and phase B 5 more behind the crew: if the bots die in the lobby, `--waves-extra 0` /
  `--no-van-late` / `--waves-latch` separate the causes); the actor count is past what has run live (122 against 99).
NOT SHOWN BY ANY CHECK: that the crew survives; that the latch fires; that the load with 122 actors is as stable as Retomoto's 99.

### W.8 GUESS / ASSUMED / NOT BUILT (each marked in the file)
- **The supply does not run dry for six minutes**: chain A alone ends at GO + 362 s; B (46 s) and D (178 s) add where the crew is. It still ends:
  a human who takes ten minutes meets nothing new after minute six on the dock, after 46 s in the lobby, after 3 minutes on the plaza.
  NOT BUILT: a ring that re-arms (`TriggerDelay2` re-arm >= 0 would fire again after its deaf time; a loop needs a delay in it: `waves-check`
  refuses a node under 0.05 s) and a hook revive.
- 61 stay; 54 more = 115 men, 122 actors with the heisters / 53 squads (the engine: 12 a squad, 500 squads; the largest stock story level:
  147 actors; what has run live: 99 / 55). Never loaded together; the chunk table is unchanged (shared models, ASSUMED for the cloned
  `ZFFActor`, MEASURED 65,852).
- GUESS: every delay (12 / 35, 22 / 24, 3 / 25 s), box, gap and wall distance; the latch's 12 s; `SUPPLY_MIN` 360 s = 'about six minutes of
  Arcade round clock'; the teller show at 20 s and 100,000 a stack. ASSUMED: sight shapes = collision flag bit 0x10; police walk 3 m/s; a
  hidden group hides its subtree; the posts hold (a rout with no next list); `ZSquadScript` field 8 = 'wiped out'; a `TriggerDelay2` naming a
  `TriggerDelay2` passes the message on.
- NOT BUILT: `--distribute-start` (the 13 start men spread over the building), `--register-pay` as NEW money objects (the six counters
  of the hall are the six stacks; a seventh needs a pool stack of the host), `--waves-clock`.
- `Escort=1` with an idle human parks one of the seven (X.1).

### W.9 The rebuild, the checks, the control (MEASURED)
Driver (not in the repo; `C:/kl_scratch/vault_waves2/scripts/all.sh`, `run_all.sh <silent|music>`, `final.sh <silent|music>`, `chain_*.sh`,
`checks_*.sh` copied from the first round's; every intermediate on C:): `test --keep --waves [--no-ai] [--music-layer4 --str ...] --plan
<c_bank>/bank_vault_bare/van.json` (chain input) and `test --keep --crew-fix [--music-layer4 --str ...]` (the delivered bare folder) -> chain
(lighten, wardrobe, bots, gun looks, talk, fxc, dyn, **hall-dash, extras, seal**) -> `kl_fa_vaultfx.py apply` -> `checks.sh` (+ `waves`) +
`vaultfx check`. One test build is 95 s, a chain about 6 min.
Folders (zip sha1 first 8 / chunk table; the full map and the wav-slim share a zip, as before): silent `C:/kl_build/c_bank4_fx`: bank_vault b12c9fed =
bank_vault_wavslim, bank_vault_noai 411fc312, bank_vault_bare c3fd8eb6; music `C:/kl_build/c_bank4_music_fx`: bank_vault 695ecbed = bank_vault_wavslim,
bank_vault_noai 7dc5a565, bank_vault_bare 4ddf9883. Blocks as X.3 (159.9 / 149.8 / 150.1 / 149.1 MB), chunk table 65,852 (full) / 65,083 (noai) /
65,640 (bare) of 69,632. `kl_fa_vaultfx.py check` PASS on all eight. Every checker PASSES (bank_check, waves, crew - the three long hold timers are
gone -, crew_route, bots_dyn, bots_gate, reverify, van, escape, fake, impact, route_walk / route_built FREE, stream_whd PASS for the music set) except the
known: the silent set's `preflight` CRASH 1 / `audit` FAIL 2 (noai 3) = the stream-clip finding; the noai folders' 'no police' (music noai: preflight
CRASH 1, audit FAIL 2); the bare folders' `guns` / `talk` (no such step there, as in the delivery) and `waves` (no `extras.json`: the bare folder has no chain).
Music full / wavslim / bare: preflight CRASH 0 (RISK 1 = the eLayer4 risk). Disk: C: 36 GB free after the two sets (927 MB each).
CONTROL: `kl_fa_bank.py test <out> --keep --plan <c_bank>/bank_vault_bare/van.json` WITHOUT any flag gives `F01_Main.zip` sha1 **b7e48d31634c9c33cf19a7e8cc315eb65bbcf0af**

### G2 Gates, second fix (2026-10-12, after the skeptic of the first gates; tools/kl_fa_bank.py and this note only; OFFLINE, NOT RUN IN THE GAME; sets C:/kl_build/c_bank6_fx and c_bank6_music_fx rebuilt in place)
The skeptic found one round-breaking and five lesser faults in G.2 - G.8. Everything below was re-measured (scripts `C:/kl_scratch/vault_gates2/`: a1 / f1 .. f7 finders, chk_g3, wv; the skeptic's own `dockray.py` re-run on the new folder). Where this section and G.2 .. G.7 disagree, THIS ONE counts.

**G2.1 The dock gate is OFF (fault 1, round-broken - REPRODUCED).** MEASURED with the exact ray: the old dock holds had 7 6 7 8 7 7 8 of the nine dock men in a free line at 5 .. 17 m; the club's yardstick is 3 (kl_fa_club.HOLD_GUNS, Withdrawal), its run C5 lost the crew under 5 .. 8. Could the men be put out of the holds' sight? No: the dock hall is one room about 9 m wide; once ALL SEVEN bots' paths and both ways to the lobby (the west stair, where W4's hits were, and the south ramp: ROOM_ALT_VIA) are walked, nearly every cell of it is within 160 of a line (map: C:/kl_scratch/vault_gates2/d2.py) and a man moved off the lines has nowhere to go but the yard (the START rows' side). So the answer is the skeptic's (a): `ROOM_ON = ('lobby', 'flights', 'hall')`; `--gate-rooms dock,...` still builds it (a first gate that is not the dock now comes AFTER the stage-1 station: rooms_plan, `door_first`). The way in past the dock is therefore NOT cured by this build: the crew walks through nine men as in W4, minus what G2.3 hides. This is the biggest open risk. If W5 loses the crew in the dock, the next step is to put the dock's squads to sleep until the crew is through (the club's WAKE_AT staging, kl_fa_club 'Pressure, after run C5'); that is NOT done here: it needs a wake step in the chain and the men would then wake behind the crew. The 30 s of the dock go back to the budget (G2.5).

**G2.2 What a hold's guns are (fault 2, wrong - REPRODUCED).** The first fix counted only the gate's own room. MEASURED with the exact ray, 25 m, same floor, ALL start / down men: lobby holds 3 7 0 0 7 7 0 (dock men at 4.7 .. 10 m through the ramp), flights holds 2 .. 4 (lobby men, e.g. 3.6 m). Now (a) the planner's hold search tags every spot with the number of men of ALL squads in the world at that gate with a free exact ray within HOLD_GUN_RANGE = 40 m (GUESS; the club uses 60 m) on its floor (|dy| < 120), and `pick_holds_bank` first looks for a set of seven under HOLD_GUNS = 3 (the widest separation for which one exists), then falls back to the fewest; (b) `rooms_check` counts the same on the finished folder ('hold-guns <gate> [per hold]') and FAILS at 6 or more (HOLD_GUNS_MAX 5, the skeptic's 'do not ship 6'), NOTES 4 .. 5 (HOLD_GUNS_KNOWN). MEASURED on the delivered silent bank_vault: **lobby [4, 4, 4, 0, 4, 4, 0]** (four dock men: StayUpstairs #01 #02 #03 and Reinforcement_01b#02 see the corridor's end through the ramp; KNOWN, over the yardstick), **flights [2, 2, 2, 0, 2, 1, 2]**, **hall [0 .. 0]** (the gallery is one floor up). The skeptic's own dockray.py agrees (`exact within 25 m, any room`: 4 4 4 0 4 4 0 / 2 2 2 0 2 1 2 / 0). NOT measured: the guns on a bot's WALK to a hold (the club's LEG_GUNS), and men woken later.

**G2.3 The men (CLEAR_MEN, faults 3 / 4 - REPRODUCED).** `rooms_check` now takes the crew's line from ALL seven bots (the first fix: the first bot) and, for every leg from the dock floor to the lobby's floor, from both ways (stair, ramp). A moved man must be ROOM_LINE_WANT = 165 (was 200 in the data and 160 in the check; GUESS: 5 over the point-blank reach) from all of them; any other man 160 (ROOM_LINE_CLEAR). With the new lines three of the first fix's moves failed (PatrolGuards_01a 7 and 86, StayUpstairs#02 18 from a line). New places (f4 / f6 / f7: nearest place on the start's mesh part, in the man's own room, not in the yard, off the lines, hidden from the lobby's and the flights' hold zones where one exists, 150 from the other men): PatrolGuards_01a to the upper west level's pocket (-968,240,-4908) and (-1038,240,-4726) (293 / 479 from the lines; they stood ON the stair top route), StayUpstairs#04 (384,200,-5223) and 01b#01 (-334,240,-5132) (both hidden from the lobby's holds: 8 and 7 lines -> 0), StayUpstairs#02 (761,200,-5375), StayUpstairs#01#03 (-334,240,-7164) (20 lines to the flights -> 1); 01a#01 and 01a#02 as before. NOT PLACEABLE: StayUpstairs#01 / #03 and 01b#02 stay at their stock places (194 / 249 / 206 from a line, each one sees the lobby's holds); (-39,203,-5775) was tried for #02 and lay within 400 of the lobby's holds (no hold left). **Guards_03 (fault 3: 162 from the vault walk):** the pocket was at x 225; now (100,-960,-12445) and (100,-960,-12200), defend place (100,-960,-12330), against the west wall (clearance below 80, no cover box): MEASURED 301 / 273 / 292 from every one of the seven bots' vault walks (chk_g3.py; the skeptic's line.py still prints the OLD pocket, its coordinates are hard-coded). The stand-in path is still a stand-in: which way the pathfinder takes dock -> lobby cannot be shown offline.

**G2.4 The wave posts (fault 5 - REPRODUCED, my report was wrong).** Dropping way-out station 7 re-runs wave_plan: eight posts moved (MEASURED, wv.py): A01 (600,-560,-10550) -> (750,-160,-9200), A02 (800,-560,-10650) -> (850,-160,-9400), A03 (650,-160,-8950) -> (200,-160,-9350), A04 (850,-160,-9200) -> (200,-160,-8950), B01 (700,240,-7450) -> (50,240,-6650), B02 (-250,240,-7450) -> (700,240,-6700), B03 (-450,240,-7450) -> (-300,240,-7000), B04 (700,240,-6700) -> (-450,240,-7000). waves-check PASSES; whether A01 / A02 on the upper landing still reach the crew in time was not simulated. The ladder is not 'unchanged'.

**G2.5 The timetable (fault 6 - accepted in part).** Three gates: the slowest crew calls the van at GO + 164.1 + 3 x 30 = **254 s**, the budget GO + 291 s: slack **37 s** (was 7). ROOM_VAN_MARGIN 60 s stays a GUESS (W3 measured call -> all aboard 12 s, with nobody shooting). TriggerActorsDead's 30 s is the game's own limit, not changed.

**G2.6 Round 2 (fault 7 - not fixable offline).** The gates add 7 squads x 3 one-shot TriggerActorsDead and hold steps; their re-arm in round 2 stays ASSUMED (W.7). The next live run must log it: after 'round 2' of the same load, whether the lobby gate's bots leave their holds within 36 s.

**G2.7 Builds and checks (MEASURED).** `test --gates` and the chain as in G.8 (scripts `C:/kl_scratch/vault_gates2/run7.sh`, `final7.sh`). The noai and bare archives were not rebuilt - nothing in them changes; only their bank_opts.json sidecar's `room_on` was set to the three rooms. Zip sha1: silent bank_vault = bank_vault_wavslim **1eca57fb5f0e16e68d88ae4de326d02943a1b01a**, noai ddd5d908 and bare 051d57e2 as before; music bank_vault = wavslim **ec45217b84d3718f3548de429db4affb42357829**, noai 62cda999 and bare 749dbfb1 as before. Every checker as in G.8 (rooms: 3 gates, 18 men, PASS; waves, bots_dyn, bots_gate, crew, crew_route, reverify, impact, route_walk, vaultfx PASS; silent set preflight CRASH 1 / audit FAIL 2 = the stream clips, music set preflight / audit exit 0, stream_whd PASS). CONTROL: `test` with no flag still gives b7e48d31634c9c33cf19a7e8cc315eb65bbcf0af. start_guns at GO+60: 6 men bear on a START row (was 7).

**G2.8 What W5 must show:** nobody dead before GO + 60 s (W4: GO + 29 s), the dock crossed without a 'ONE STEP' (the stair top is empty of the patrol), the lobby gate's seven alive at their holds under 4 guns, the human at START alive past GO + 96 s, van called by GO + 254 s at the latest, and round 2 (G2.6). If the dock still eats the crew: G2.1's wake staging.
= the first delivery's bare archive, RESULT PASS (20,643 entities, MEASURED after every edit of this round).

### W.10 The skeptic's seven findings on the first waves build, and what became of each
| # | finding | what was done | what fails now |
|---|---|---|---|
| 1 | the supply is a one-shot set of 24 men | three chains (W.1 / W.2): 21 waves, links every 24 .. 35 s, gated on phase triggers, a wiped-out latch, floor 362 s, finite | `waves-check`: a Pace/Go/Fast that is not what it should be (delay, one-shot, who names it), a chain whose gaps do not add up, a last link that still names a timer, a chain past 600 s, chain A ending before 360 s |
| 2 | B2 / B3 stand ON the crew's way out | entries and posts 300 .. from every leg of ROUTE_IN + ROUTE_VAULT + ROUTE_OUT (`route_dist`), B shrunk to 5 men because the lobby only has 3 spots at that distance (MEASURED: `cap.py`) | an entry or post nearer than 300 to a leg |
| 3 | three long hold timers at the hall's north end | `dash_chain` follows a '_pos_cover' rout the dash step names DIRECTLY (Squad#02 / #03 / #04 051_Timer_hold, 4 - 6 s -> 1.5 s); `crew-check` follows 4 hops and FAILS a long hold timer started by a step with a place in the hall | crew-check: 'hold timer ... within 4 steps' |
| 4 | the teller stacks pull the bots sideways | six stacks of 100,000 on the counters' public edge (the two middle counters added), shown 20 s after the plaza box instead of 2 s (a bot at the box edge is 2 .. 10 m from the stacks: inside the loot window, 800 / 400; 20 s later the heisters' dash is some 60 m on); MEASURED the stacks sit 0.6 .. 1 m from mesh floor; NOT made un-takeable for the bots (no such kind in the tactic's reading) | `waves-check`: Teller_show names all hidden stacks, nothing else shows them, one timer named by the plaza box alone |
| 5 | the bare folders keep the van hidden for good | the DELIVERED `bank_vault_bare` is the `--crew-fix` build: van visible with its FakeTarget (V2's), stacks and the vault's loot as the first delivery; the chain's `--waves` bare stays an intermediate | (none: no extras.json = nothing to test) |
| 6 | the late van hangs on the plaza box | also the foyer box (`Specials!LevelSpeak!TriggerBox`) + 6 s (30 m earlier = 6 .. 10 s of a sprint) and, as backstop, the ante-room box + 120 s; `ActivateGeom` twice is idempotent | `waves-check`: each timer named by its box alone, the foyer timer shows the van |
| 7 | posts 1.5 m apart are a bunch | `POST_GAPS` tries 3.0 m, then 2.2, then 1.5 m (the floor); MEASURED: all 54 posts at 3.0 m | a post nearer than 1.5 m to another wave post |


### W.11 The second skeptic's five faults on the second waves build (2026-10-12)
| # | fault | verdict | what was done |
|---|---|---|---|
| 1 | chain A is time-based, not phase-gated; a human in the vault gets nothing | CONFIRMED in part | MEASURED (`cap.py`, 300 from every leg): the lobby under the vault takes 5 men at 3 m (6 at 1.5 m), the airlock and the vault 0, the hall 158 but that is the crew's exit (V2's grave). So no more men can be posted where the vault stretch is. Chain B now spreads the same 5 men over FIVE single-man links (22 s, then every 30 s: last at 142 s instead of 46 s). Honest scope: A is ambient pressure on the dock and yard (the way in and, coming back up, the way out); a human who sits five minutes in the vault meets B's 5 men by +142 s and the beat's 14, nothing more, until he comes up through A's men |
| 2 | the latch is on by default and rests on an unproven field 8 | CONFIRMED | `WAVES_LATCH` default OFF, flag `--waves-latch` to add it; bank_opts.json says `waves_latch: false`; no `Fast` nodes, no field 8 list in the delivered folders. The chains are plain timer chains. `waves-check` still fails a missing Fast when the latch is on |
| 3 | round 2 rests on two assumptions (one-shot timers re-armed, parked squads respawned) | CONFIRMED as an assumption, no fix possible in data | now the FIRST live check of round 2 (W.7): if no wave comes in round 2 the one-shot nodes were spent. The reset does not touch the chain nodes (a node cannot re-arm another) |
| 4 | the registers cannot be had while holding the front | REJECTED, reason: the stacks are shown 20 s after the plaza box; a human who holds the hall's south end is still there (D01 comes at +3 s, D02 at +28 s), so he is paid while holding; the heisters' dash is past by then. Showing them from the foyer box would put them in the bots' loot window during the dash (10 .. 17 m from the hall station) = the V2 death. The 20 s is a GUESS; told to the owner: the reward comes about 20 s after the plaza box |
| 5 | bare folder = old bare, no reset/waves | CONFIRMED, by design | `bank_vault_bare` is the plain `--crew-fix` build for L0 load tests: no reset (round 2 shows the open vault), no waves, no `extras.json` |

**W.11 rebuild (MEASURED).** Same driver (`C:/kl_scratch/vault_waves2/scripts/all.sh`), both sets on C: (`c_bank4_fx`, `c_bank4_music_fx`, replaced). 267 entities added (24 squads, 56 single switches, no Fast node: `grep Fast extras.json` = 0, `bank_opts.json` `waves_latch: false`); chunk table unchanged. Zip sha1: silent bank_vault = wavslim 50bfbb82, noai 411fc312, bare c3fd8eb6; music bank_vault = wavslim 52a0c915, noai 7dc5a565, bare 4ddf9883. `waves-check`, `crew-check`, `kl_fa_vaultfx.py check` PASS on all full/noai folders; the known findings (stream clips; noai 'no police'; bare guns/talk) unchanged; music full/bare preflight CRASH 0. CONTROL `test` with no flag: b7e48d31 again. LIVE CHECK ORDER for round 2 now starts with: does A01 come at +12 s in round 2 (one-shot nodes re-armed, parked squads back)?


## Waves, after run W2 (2026-10-12; OFFLINE: built and checked, NOT RUN IN THE GAME, nothing installed)

Folders (third round): `C:/kl_build/c_bank5_fx` (silent, against the installed stream file) and `C:/kl_build/c_bank5_music_fx` (with `--music-layer4 --str
<work>/build/v_vault/PC_Def.str`), the four names each, every one padded by `kl_fa_vaultfx.py apply` (`check` PASS). On C: because G: is full. `c_bank4*` (the
build run W2 tested) and every older set are untouched. Driver: `C:/kl_scratch/vault_tune/scripts/` (`all.sh` -> `run_all.sh`, `final.sh`; the second round's
scripts re-pathed; changed: the flags of the three `test` calls, the bare folder's `extras` + `seal`, two lines in `checks.sh` - `start_guns`, and `waves` for a
folder without a chain). This section is: the diagnosis of run W2 (W2.1), the change (W2.2), the supply as built (W2.3), the new check rules and the proof that
they would have caught W2 (W2.4), the registers (W2.5), the voice (W2.6), the delivered bare folder (W2.7), the rebuild (W2.8), GUESS / ASSUMED / what the next live
run must show (W2.9). Labels: MEASURED = read off a log or a built level; READ = read in code / a note; ASSUMED; GUESS.

### W2.1 The diagnosis of run W2 (idle human dead GO + 32.6 s, three bots dead GO + 14 / + 25 / + 27 s)
MEASURED (log `W2_vault_waves.log`, GO = the line 'session: state 0x18 -> 0x19'):
- THE DIAL WAS NOT THE ONE OF V2. W2's `[Balance]` is `Risk=2 CopToCrew=0.05` (the task text said Risk=1 / Tough=1.5: the ini and the log say Risk=2, 'Tough x1.00'):
  'balance: on; ... police->crew 0.05 crew->police 1.00 police->you 1.00 ... crew off your stage x 1.00; your health x 0.73' = 401.5 health. V2 had NO balance line (the dial
  was off, re/bank_campaign.md X.1): stock Arcade level 1 = police->crew 0.01, police->you 0.10, off-stage x 0.5. So per bullet W2 hurts a bot 5 - 10 times as much and the
  human 10 times. The hits on the bots show it: median hit GO+12..25 s V2 2.0 / W2 12.0; GO+25..35 s 3.0 / 8.0; GO+35..60 s 2.0 / 10.5 (script `C:/kl_scratch/vault_tune/hits.py`).
  The NUMBER of hits is not higher in W2 (GO+12..25: 15 in V2, 21 in W2; GO+25..35: 97 / 57); the hits in the yard and the dock (z > -5300) before GO+35 are 9 of 117 in V2 and 26 of
  86 in W2. NOTHING CAN BE CONCLUDED FROM A COMPARISON OF W2 WITH V2 ALONE - the dial differs by an order of magnitude. The log has NO shooter ids (klbot.c logs the victim and its place).
- Bot 5, the first dead (GO + 14.3 s), died at (461, 307, -4952) after seven hits of 12 - 17 in a second ('ONE STEP - DOWN' at 158 of 252) - 2.0 m from the first post of wave A01
  ((600, 200, -5100)), 4.9 m from its second ((0, 200, -4850)). Bot 7 (GO+25.2 s) died at (-762, 331, -5221) (the security side), bot 2 (GO+26.7 s) in the lobby (55, 336, -6983).
READ / MEASURED on the built level (`kl_fa_bank.py start-guns`, new; men in the world at a time T, each at every place he may stand = an UPPER BOUND, the same for both builds;
a wave man on the straight line from his entry to his post at 3 m/s; a gun BEARS when it is within 60 m of a START row with a free line under any of the three sight rules):
| build | GO+12 s | GO+25 s | GO+35 s | GO+60 s | within 15 m with a line (12 / 25 / 35 / 60 s) | nearest |
|---|---|---|---|---|---|---|
| c_bank2 (the 61 enemies, no waves: the form the owner has; 19 men of stage start / down) | 8 | 8 | 8 | 8 | 6 / 6 / 6 / 6 | 13.3 m (Guards_Reinforcement_StayUpstairs#4 to the row at x 700) |
| c_bank4 (W2's build; + chain A from the round-start timer) | 9 | 10 | 10 | 13 | 7 / 8 / 8 / 11 | 1.1 m at GO+12 s (A01_2 crossing the yard), 7.6 m at +25 s, 2.5 m at +60 s (A02_3) |
| c_bank5 (this round) | 8 | 8 | 8 | 8 | 6 / 6 / 6 / 6 | as c_bank2 |
- Chain A's first link was started by the round-start timer 12 s after the event = GO + 3.5 s (the event is 8.5 s before GO). Its three men ENTER from the yard's east lane
  (2080, 200, -2500) and walk to posts 7.5 .. 12 m from the START rows ((600, -5100), (0, -4850), (600, -5500); START is at z -4350): their straight lines pass 23, 9 and 124 cm from
  a START row (`waves-check` on c_bank4_fx: 'the walk ... passes 9 from a START row'), i.e. THROUGH the group of the humans, inside the point-blank reach (160) of re/melee_damage.md,
  at GO + 10 .. 12 s. The next wave's posts (A02, entering GO+38.5 s) are 2.5 - 7 m from the START rows with a line. At the post itself A01 has NO line to the row at x 900 (the dock
  wall) - the exposure is the WALK across the yard and the next waves' posts, not A01's posts. The 8 men of the 61 that bear on the START rows (c_bank2 row of the table) have NO
  line to the row at x 900 (the idle human's row in W2: 'pos t30: me #2 (900, 200, -4350)').
- WHY THE RULES LET IT THROUGH (READ in `wave_plan`): a post only had to be 250 from 'a heister station of the regions the wave names' and 300 from a leg of the way; the START rows are
  stations of the dock region, so a post 2.5 m from them passed; nothing tested a post's or a walk's line to the START rows; the entries were tested blind but not the walk.
- CONCLUSION (what is established and what is not): ESTABLISHED - chain A put three, then three more, armed men into the yard / dock at GO+3.5 s and GO+38.5 s, walking through the
  START group; nothing in the checks forbade it. NOT ESTABLISHED - which gun killed the human: the dial alone (10 x the stock police->you on a 401-health body) could have done it
  with the 61 enemies, none of whom bears on his row, so the waves are the likely cause but the log cannot say. The fix removes the waves from the yard and the first minute either way.

### W2.2 The change (tools/kl_fa_bank.py only; `--waves2`; every older flag keeps its meaning; no flag = the byte-identical bare archive b7e48d31, see W2.8)
1. `--waves2` (implies `--waves`): `WAVES2`, in `bank_opts.json` as `waves2`. `chain_table(v2=True)`.
2. CHAIN A DOES NOT RUN FROM THE ROUND START. Its first Pace is named by a new TriggerBox of the clock group, `Box_in`, cloned from the foyer box (criminals only, fires once,
   field 15 = 0), placed on the dock door's plane (`DOCK_BOX_AT` = EnterLootArea's: (560, 380, -4800), half (250, 230, 50): z -4850 .. -4750, the doorway is at z -4706 - the box lies
   wholly beyond the door, i.e. a criminal has left the yard), and by a backstop `Timer_A_late` (A_BACKSTOP 80 s after the start timer = GO + 81.5 s: the start timer is 10 s after the round-start event, the GO 8.5 s after it, so it fires at GO + 1.5 s; CORRECTED in W3.4, it said GO + 71 s) named by the start timer, for a
   crew that never passes the box. Pace_A01 is a one-shot, so whichever comes first wins. ASSUMED: that a TriggerBox cloned into the clock group fires for an AI heister like the
   beat box does (the beat box and the foyer box are the same kind of node and fired in V2 / W1 / W2) - NOT SEEN for a new node.
3. ITS MEN ARE NOT THE YARD'S. Four single-man links (gaps 30, then 45 s: at +30, +75, +120, +165 s after the box), entering at the airlock corridor (E_AIRLOCK, blind from the way,
   as chain B's) and standing AT COVER (a cover box within `POST_COVER` 400 of the post) on the flights' two landings: the lower landing (floor y -560) twice, the upper (y -160) twice.
   The 3 m route rule is relaxed ONLY here, and only to `POST_ROUTE_MIN` 200 from a leg; the station rule is `POST_STATION` 400, then 300, then `POST_STATION_MIN` 250 from every heister
   station (the planner takes the first the mesh allows for the whole wave). MEASURED (`C:/kl_scratch/vault_tune/explore.py`, `cap2.py` on c_bank4_fx/bank_vault; mesh part of the
   START, 45 from a wall, at cover, 15 m from and blind from every START row under all three sight rules, 1.5 m from an old place): with 4 m from every heister station the dock has 0
   posts, the security side 0, the lobby 0, the airlock corridor 0, the upper landing 0, the lower landing 29 spots (3 .. 4 men at 2.2 .. 3 m apart), the cross corridor 1; with 3 m the
   lobby gets 15 spots (3 men at 3 m), with 2.5 m the lobby 38 (5 men), the upper landing 4, the lower 33. So the interior CANNOT take a supply of more than a handful: the first build's
   eleven links of 25 men do not fit; four fit. THE LEAD'S 4 m WAS NOT KEPT FOR TWO OF THE FOUR (A03 and A04 stand 2.5 m from a station): at 4 m there are three spots. The lobby
   'underneath' stays chain B's five single men (22 s, then every 30 s after the ante-room box), which already stood there. The floor of chain A is `SUPPLY_MIN2` 150 s (the last link at 165 s),
   not 360 s: the yard that made 360 s possible is the thing that is out.
4. `wave_plan`: with WAVES2 every entry, every post and every walk keeps `START_CLEAR` 1500 from every START row and has no line to one under any of the three rules (`start_ok`, `seg_dist`);
   a wave that finds no place is still an ERROR. `Sight.sees_by`: the module's own rule (flag 0x10), the player ray of third_party/anp/scripts/hvk_ray.py (0x20) and the same with the hero-only
   walls (0x28) - kl_route's grids 'sight', 'npc', 'hero'. MEASURED: they give the SAME answer for all 1,744 (post, START row) pairs sampled in the yard, the dock, the security side, the lobby
   and the airlock corridor (`rules.py`): no difference on this level, so the module's assumption (0x10) did not hide a line; the three are used together (a wave man must be blind under all).
   WHERE THEY CAN DIFFER: hvk_ray models the player's ray at the game's own heights; the module casts 160 -> 120 / 175; neither models doors or moving bodies.
5. `Box_in`, `Timer_A_late` and the registers' timers are clone nodes of the build itself (kl_fa_fed.clone_built) - no new model, no new chunk (chunk table unchanged: 65,852).

### W2.3 The supply as built (MEASURED by `waves-check`; GUESS: every box, gap, number)
| chain: trigger | links | first after the trigger | then every | last | men a wave | entries -> posts |
|---|---|---|---|---|---|---|
| A: the dock box (or the backstop) | 4 | 30 s | 45 s | 165 s | 1 | the corridor behind the airlock (1580, 240, -6560) -> the flights' landings at cover: (600, -559, -10550), (800, -559, -10650), (650, -160, -8950), (850, -160, -9200) |
| B: the ante-room box (once) | 5 | 22 s | 30 s | 142 s | 1 | as before (lobby posts) |
| D: the plaza box (once) | 8 | 3 s | 25 s | 178 s | 3 | as before (the plaza) |
33 men in 17 squads (was 54 in 24): 61 + 7 + 33 = **101 actors / 49 squads** (c_bank4: 122 / 56; what ran live: Retomoto 99 / 55; the engine 147 / 500); 179 entities added (c_bank4: 267).
The A men walk the crew's own way from behind (the airlock stairs, the lobby, the flights): they are the 'police coming down behind the crew' the beat already has. They also stand on the way
BACK UP: the returning crew meets whoever of A is alive on the landings (4 men, in cover) plus the beat's 14 - the same trade as chain B had in the lobby.

### W2.4 The new check rules (all in `waves_check`, run by `check()` and `checks.sh`) and the proof that they catch W2
1. every wave man's ENTRY and POST: `START_CLEAR` (1500) from every START row and no line under any rule; every WALK entry -> post at least `START_CLEAR` from every START row;
2. WAVES2 chain A's posts: at cover (`POST_COVER`), `POST_ROUTE_MIN` from a leg, `POST_STATION_MIN` from every station;
3. NO WAVE BEFORE THE CREW HAS LEFT THE YARD: without WAVES2 the check FAILS 'chain A starts from the round-start timer'; with it the dock box must lie wholly beyond the door (z + half < -4726), fire
   for criminals only, once, name only Pace_A01, and the backstop timer must be >= 60 s and named by the start timer alone; the floor is `SUPPLY_MIN2`;
4. GUNS ON THE START ROWS: for GO+12 / 25 / 35 / 60 s the waves add no gun that bears on a START row and none within 15 m with a line to those of the 61 enemies alone (`start_pressure`).
PROOF (MEASURED): `waves-check C:/kl_build/c_bank4_fx/bank_vault` (W2's build, read-only) now reports 76 FAILs - 25 posts 250 .. 1,484 cm from a START row, 19 posts with a line to one, one man entering the world with a line (A02_3), 25 walks passing 9 .. 1,101 cm
from one (A01's at 23 / 9 / 124 cm) - and 'chain A starts from the round-start timer'; the same command on `c_bank5_fx/bank_vault` is PASS with 'guns on the START rows ... with the
waves 8/8/8/8, the 61 enemies alone 8/8/8/8'.

### W2.5 The cash registers (the owner's wish outweighs the bots' detour)
`--teller-foyer` (on with `--waves2`; `--no-teller-foyer` gives the plaza-box form of the second round back): the six teller stacks (100,000 each, hidden from the load) are shown
`TELLER_FOYER_S` 2 s after the FOYER box (the hall's north end, (300, 930, -5650), where the crew comes up); the plaza box shows them 1 s after it too (backstop; `Teller_show` is an ActivateGeom, twice is
idempotent). A human who holds the front is paid for the men he stops, and the stacks are there while the 8 police on the gallery and the plaza's squads are in play.
WHAT THE BOTS WILL DO (READ / GUESS): a loot-tactic candidate is one of the five nearest untaken money objects within 800 (horizontal) / 400 (vertical) (re/bots_loot.md); the aisles the AI heisters use
(x -500 and x 1100) are 2.7 m from the stacks (x -765 and 1367), so EVERY bot that arrives in the hall's south half while they are shown turns to the nearest stack and stays until it is taken (the loot
wait, 30 s at the longest) before it dashes - under the eight police on the gallery. This is the V2 grave with 600,000 as bait. It is the owner's word against that finding (W.10 finding 4); if the next run
shows the crew dying at the counters, `--no-teller-foyer` is one flag.

### W2.6 The voice
`--voice` (not implied by `--waves2`; every folder of this round was built with it): `kl_snd.VOICE = True` around the graft (kl_fa_club's way), so that `kl_snd.merge(inmem=kl_voice.stream_clip)` turns
every streamed single IMA ADPCM record into an in-memory record. READ in `kl_voice.stream_clip`: the 0x1000-byte 'LIP ' block at a record's start is skipped (the read moves behind it); a record that is not
mono, not 0x400-byte blocks or too long stays streamed (counted by `check()`: FAILS when any is left under `--voice`). MEASURED (`kl_whd` on the written .WHD, `streamed_singles`): streamed single IMA ADPCM
records, silent set: c_bank4_fx bank_vault / bare 66 (noai 0 - no guards), c_bank5_fx 0 on all four; music set: c_bank4_music_fx bank_vault 75 (the nine added guard lines), c_bank5_music_fx see W2.8.
WHAT IT ADDS: the .WAV block bank_vault 23.3 -> 24.8 MB (+1.5 MB), bare 23.1 -> 24.6 MB, noai unchanged (23.1; no guards); the wavslim .WAV 13.3 -> 14.8 MB; the five load blocks 159.9 -> 161.4 MB (full), 149.8 -> 151.4
(wavslim); the chunk table, .prm, .fxc, .ANM do not change. By-product: the audit's known finding 'stream clips are not in the merged stream file' goes from 10 clips to 1 in the silent set. NOT HEARD: ears.

### W2.7 The delivered bare folder
`bank_vault_bare` = `--crew-fix --reset --van-late --voice` + the step `extras` + `seal` (it was `--crew-fix` alone): the round-2 reset and the late van ARE in it, with ONE FLAG PLUS TWO COMMANDS in `run_all.sh`
(the reset objects and the van's show are made by `extras`, and `extras` needs a group to clone for the clock: the bare folder has no AI heisters yet, so it takes the dock patrol's squad group
(`extras_make`: `src_`). No waves, no tellers hidden, no chain (no `bots.json`): the load test of the vault, the beat, the van and round 2. `waves_check` PASS on it; the checks `guns` / `talk` do not
apply (as in the delivery). The van is shown by the foyer box + 6 s, the plaza box + 1 s, or the ante-room box + 120 s: a lone human triggers the foyer box.

### W2.8 The rebuild and the checks (MEASURED)
Driver `C:/kl_scratch/vault_tune/scripts/all.sh` (one build at a time; about 40 min a set): `test <out> --keep --waves2 --voice [--music-layer4 --str ...] --plan <c_bank>/bank_vault_bare/van.json` (the chain's input),
the same with `--no-ai`, `test <out> --keep --crew-fix --reset --van-late --voice` (the bare folder) + `extras` + `seal`, then `chain.sh` (the delivery's: lighten, wardrobe, bots, guns, talk, fxc, dyn, hall-dash, extras, seal)
on the first two, `kl_fa_vaultfx.py apply` (check PASS on all eight), `checks.sh` (the second round's + `start_guns`).
Folders (zip sha1 first 8; the full map and the wav-slim share a zip; chunk table 65,852 / 65,083 noai / 65,640 bare of 69,632; blocks 161.4 / 151.4 wavslim / 150.1 noai / 150.6 bare MB):
silent `C:/kl_build/c_bank5_fx`: bank_vault = bank_vault_wavslim d00f4c4f, bank_vault_noai ddd5d908, bank_vault_bare 051d57e2; music `C:/kl_build/c_bank5_music_fx`: bank_vault = wavslim 877379a3, noai 62cda999,
bare 749dbfb1. EVERY CHECKER PASSES (bank_check, waves, crew, crew_route, bots_dyn, bots_gate, reverify, van, escape, fake, impact, arms, chars, guns, route_walk / route_built FREE, stream_whd for the music set,
`kl_fa_vaultfx.py check`) except the known: the silent set's `preflight` CRASH 1 / `audit` FAIL 2 (noai 3) = the stream-clip finding, now ONE clip (was 10); the noai folders' 'no police' (music noai: preflight
CRASH 1, RISK 1, audit FAIL 2); the bare folders' `guns` / `talk` (no such step there). The music full / wavslim / bare folders: preflight and audit exit 0 (CRASH 0 / no finding that must be 0; the RISK count of the second round, the eLayer4 risk, was not read again). Disk: C: 32 GB free before the two sets.
CONTROL: `kl_fa_bank.py test <out> --keep --plan <c_bank>/bank_vault_bare/van.json` WITHOUT any flag gives `F01_Main.zip` sha1 **b7e48d31634c9c33cf19a7e8cc315eb65bbcf0af** again (20,643 entities, RESULT PASS, MEASURED after the last edit).
`tools/kl_fa_club.py` still imports the module (`import kl_fa_bank, kl_fa_club`).

### W2.9 GUESS / ASSUMED / NOT BUILT, and what the next live run (V3 on `c_bank5_fx/bank_vault`, owner away; the ini first: one `[Balance]`, one `[Bots]`, `Escort=0`) must show
- ASSUMED, never seen: that the new TriggerBox `Box_in` fires for an AI heister (log: 'wave A01' comes in the airlock corridor GO + ~12 s + 30 s after the first bot passes the dock door; if nothing comes by GO + 111.5 s (81.5 + the first Pace 30 s) the box did not fire and the backstop did - the latter is the same log line); that a cloned node of the clock group is updated outside the group's listed bound (the group's bound is the union of its kids' places, as for the other tops).
- GUESS: A_BACKSTOP 80 s, the gaps 30 / 45 s, `START_CLEAR` 15 m, `POST_COVER` 4 m, `POST_ROUTE_MIN` 2 m, `POST_STATION` 4 / 3 / 2.5 m, `PRESSURE_RANGE` 60 m, `ENTER_AT` 12 s (MEASURED in three runs: 'heist stage 0 -> 1' at GO+12 .. 19 s), the 3 m/s walk of
  the pressure model (a wave man's real way is the mesh's, much longer than the straight line: A01 needs 60 .. 90 s from the corridor to the landing).
- `start_pressure` is a MODEL: old men at every place they may stand, wave men on a straight line, no real AI sight / hearing, no cover use; it counts lines to the eight START rows, not to a moving player. It would have shown W2's
  difference (9 / 10 / 10 / 13 against 8) and the crossing of the yard; it does not say who would shoot first.
- NOT BUILT: more men in the building. The interior takes four wave men at the lead's constraints (W2.2 item 3); to put more there the heisters' own stations must thin out (the dynamic step's places are every 3 m of the route) or the
  rule `POST_STATION_MIN` must go under 2.5 m (point-blank reach 1.6 m). The 13 'start' men are still all in the garage part (`--distribute-start`, W.8): the owner's 'they all spawn in the garage part' is about THEM, not about the supply.
- TO SEE LIVE: (1) the first minute is the 61-enemy build's again: the human idle at START is not shot before GO + 60 s, the first bot dies later than GO + 33 s (V2) at the dial of W2 (not to be compared with W2's 14 s: the dial); no 'wave' squad
  in the yard or the dock; (2) A01 comes into the world at the airlock corridor, walks down behind the crew and stands at cover on the lower landing, A02 the same, A03 / A04 on the upper landing; B in the lobby, D on the plaza as before;
  (3) 'tellers: shown' 2 s after the foyer box: do the bots turn to the stacks (loot lines in `[Bots] Log=2` 'record N ... $100000' at z -7200 .. -8000) and how many die there; (4) the voice: the guards' and SWAT lines are heard (66 lines were silent);
  (5) round 2: the vault door's body back, the intact vault shown, the late van hidden until the foyer box, A01 comes again (the one-shot nodes re-armed: ASSUMED); (6) `bank_vault_bare` (L0, the load test) now has the reset and the late van.

## Waves, second fix (W3; after the skeptic of the W2 fix; tools/kl_fa_bank.py only; sets C:/kl_build/c_bank5_fx and c_bank5_music_fx rebuilt)
The skeptic found six faults. Reproduced, fixed or rejected (MEASURED unless marked):
### W3.1 Posts of chains B and D not at cover (REPRODUCED, FIXED)
`C:/kl_scratch/vault_tune/skeptic/posts.py` on the new build: every post of A, B, D is now within 8 m of a cover box (A 146 .. 308, B 155 .. 338, D 181 .. 782 cm), 2.5 m or more from a heister station of the planner (S.places) and, for B and D, still 3 m from the crew's legs and the regions' stations as before.
`--waves2` now plans EVERY chain at cover and `POST_STATION` 400 / 300 / 250 from every station; chain A stays at `POST_COVER` 400; B and D try `COVER_LADDER` 400, 600, 800 and the first radius that holds the whole wave wins. The radius used is stored in `extras.json` (`post_cover`, `post_station`)
and `waves-check` tests each wave against ITS OWN radius and logs a note where it is over 400 (D03 .. D08 stand within 600, D07 within 800: the plaza has no cover box nearer for three men 3 .. 5 m apart). Chain D's men of one wave stand `POST_GAPS_V2` 500 / 400 / 300 apart (the first build's 300 was the fault's 'threes 3 m apart'): D01, D02, D04 500, D03 / D06 400, D05 / D07 / D08 300 (the plaza takes no more).
CHAIN B IS NOW FOUR MEN (was five): MEASURED, a fifth finds no post within 8 m of cover and 2.5 m off a station in the lobby. Supply: A 4 + B 4 + D 24 = 32 men in 16 squads; actors 61 + 7 + 32 = 100, squads 48.
### W3.2 Entries in sight of the way OUT (REPRODUCED, FIXED)
All 246 spots of E_AIRLOCK had a free line (hvk_ray 0x20 and the module's grid) to the 'stairs' station (1538, 355, -5822), 7.5 m away; `way_out_sees(S, p)` now tests every ROUTE_OUT station under the four rules of `RULES_X` for the entries of chains A and B (`wave_plan` and `waves_check`). On the whole mesh of the building's floors
(`ent_scan.py`, `ent_scan2.py`; blind from BLIND_WAY, from ROUTE_OUT, 15 m and no line from the START rows, 3 m from the way, 2.5 m from the crew's places) there are EIGHT spots, in two clusters of the armoury / security side: `E_ARM_A` (-1000, 240, -5460 ..) for chain A and `E_ARM_B` (-660, 240, -5640 ..) for chain B. One man at a time (single-man links 22 .. 45 s apart), so one cluster each is enough.
Re-run of the skeptic's `entry.py`: neither entry has a line, under hvk_ray 0x20 or 0x28, to ANY route station (in, vault, out). The men walk 17 .. 55 m from there to their posts (the walk keeps 15 m from the START rows: checked). ASSUMED: nothing but sight is meant by 'plop out'; a man that has walked in is seen by whoever is looking when he passes. Chain D's recess entries (the plaza) are not tested against the way out: they come after the plaza box, when the crew is at the plaza already.
### W3.3 The module's grid against the exact ray (REPRODUCED, FIXED)
The skeptic is right: the grid blocked B04's old post (-200, 240, -7400) -> row (450, 200, -4350) at ShatterPillar_09, hvk_ray's cast passed beside it. `Sight.sees_by` takes a fourth rule 'exact' (hvk_ray.Collision of the folder's archive, masks 0x20 and 0x28, same eye / target heights) and `start_ok`, `way_out_sees` and `waves_check`'s line tests use all four (`RULES_X`): a line under any of them counts. `start_pressure` / `start-guns` keep the three grid rules (speed: it casts for every old man's every place); WHERE THEY DIFFER is still the thin and round shapes, and this one is a corrected statement: the W2.4 item 'no difference was found' held only for the 1,744 sampled pairs.
### W3.4 Backstop timing (REPRODUCED, FIXED in the text)
Start timer = round-start event + 10 s; the GO = the event + 8.5 s; so it fires at GO + 1.5 s, `Timer_A_late` (80 s) at GO + 81.5 s and the first backstopped man (Pace 30 s) at GO + 111.5 s. W2.2 and W2.9 and the comment at `A_BACKSTOP` said GO + 71 s / 101 s; corrected. A live check waits for GO + 112 s.
### W3.5 Supply for a human who stays at the vault (CONFIRMED; NOT CHANGED, with the reason)
Only chain A (4 men, last box + 165 s) reaches the vault's neighbourhood; nothing is sent after about GO + 4.5 min. Recycling chain A's squads or a second chain keyed on a vault box would put more men on the SAME four cover posts (the interior holds four at the owner's rules: W2.2 item 3, W3.1) -
men would stand on one spot or off cover, i.e. 'bunched' and 'plopped out', which the owner forbade, or the stations of the heisters must thin out (the dynamic step), which is another module's change. Left to the owner: say whether 'keep spawning' outranks 'strictly cover' for a human who camps the vault. GUESS: a camper is rare because the 56 s vault gate and the beat's 14 police are the pressure there.
### W3.6 The registers as bait (MEASURED by the skeptic, NOT CHANGED)
Heister places within the loot window of each stack: 3, 7, 23, 4, 16, 4 (east stacks 23 and 16). Bots will turn to them under the gallery police: the decision stands, `--no-teller-foyer` is the one flag; the next live log's loot lines at z -7200 .. -8000 decide.
### W3.7 The rebuild (MEASURED)
Scripts C:/kl_scratch/vault_tune/scripts/run_main.sh / final_main.sh / all_main.sh (the full and wavslim folders only: noai has no police and bare no waves, so their archives are unchanged and kept: noai ddd5d908 / 62cda999, bare 051d57e2 / 749dbfb1). New zips: silent `c_bank5_fx` bank_vault = bank_vault_wavslim **d77396c0**, music `c_bank5_music_fx` **f3e5ce61**. Every checker PASS as in W2.8 (waves: PASS with the new entries, posts and the four rules; stream_whd PASS for the music set; the silent set's preflight CRASH 1 / audit FAIL 2 are the one stream-clip finding), blocks 161.4 / 151.4 MB, chunk table 65,852.
`start-guns`: 8/8/8/8 guns bear on the START rows, the same eight old 'start' guards as before (StayUpstairs, Reinforcement 01a / 01b) and no wave man at GO+12 / 25 / 35 / 60 s. These eight old guards remain what a V3 at W2's dial (Risk=2) can be killed by; run V3 once at W2's dial and once at V2's (stock) dial to separate the dial from the waves.

## Gates, after run W4 (2026-10-12; SEE G2 BELOW: the dock gate was taken out and the men re-placed after the skeptic; tools/kl_fa_bank.py only; OFFLINE: built and checked, NOT RUN IN THE GAME, nothing installed; sets C:/kl_build/c_bank6_fx and c_bank6_music_fx)
Task: run W4 (the full map, 100 actors, an idle human, Risk=2 Ramp=1, police -> crew 0.05) lost ALL SEVEN AI heisters GO + 29 .. 68 s, every one at heist stage 1, on the way IN. Retomoto's cure (kl_fa_bots_rt GATES, re/retomoto_bots_rooms.md) is built here for this map. Labels: MEASURED (log, build, checker), READ (code), ASSUMED, GUESS. Scripts of the analysis: `C:/kl_scratch/vault_gates/` (w4.py, analyse.py, line.py, posts.py, finder.py).

### G.1 Run W4 against run W3, read from the logs (MEASURED)
GO = the talk line 'round 1: clock starts' (W3 03:23:43.1, W4 03:30:44.7). **W3 (no enemies):** 'heist stage 0 -> 1' at GO + 11.7 .. 19.6 s (all seven), 'stage 1 -> 2 -> 3' GO + 156.7 .. 164.1 s (the vault gate 56 s + the 30 s loot wait + the walks), all seven aboard GO + 169.8 s, nobody hit. **W4:** 'stage 0 -> 1' GO + 12.6 .. 17.3 s (the same), then:

| bot | first hit | last hit | log lines | lost | where it fell |
|---|---|---|---|---|---|
| 5 | GO+11.2 yard (655,200,-4470) | +28.6 | 30 | 275 | (56,316,-6849) |
| 7 | +12.8 yard (196,200,-3543) | +35.8 | 10 | 274 | (101,240,-7178) 'lost 203.0 ... ONE STEP' |
| 6 | +11.2 yard (575,202,-4590) | +36.8 | 21 | 257 | (233,335,-7445) |
| 4 | +11.8 yard (565,200,-4415) | +37.8 | 15 | 260 | (143,240,-7336) 'lost 118.0 ... ONE STEP' |
| 3 | +14.8 dock door (305,200,-4812) | +49.5 | 38 | 290 | (313,240,-7716) |
| 1 | +15.3 dock door (313,200,-4857) | +53.4 | 47 | 308 | (388,336,-8001) |
| 2 | +16.9 dock door (134,200,-4871) | +67.9 | 49 | 478 | (414,78,-8364), the first flight |

The idle human in the yard died at GO + 96 s (W2: GO + 35 s). The bots' path, from the hits: START rows -> the dock door (z -4706) -> the dock -> the west stair up (-342 .. -545, 240, -4937 .. -5105) -> the corridor (45 .. 60, 240, -6360 .. -6660) -> the vault lobby (37 .. 143, 240, -7019 .. -7336) -> the glass door (357 .. 395, 240, -7700 .. -7940) -> the flights. The rate: bot 5 took 21 hits in 3 s standing at (60,241,-6360) (GO + 24 .. 29 s, 3 .. 22 a hit); bots 4 and 7 died to the point-blank rule (re/melee_damage.md) beside the lobby guard whose start (166,241,-7064) is 29 from the way.
**Who was near** (the module's tables; the 13 'start' guards, the 6 on the flights, wave B), per hit place, the men at their START places (the upper bound for an old squad; analyse.py): within 160: PatrolGuards_01a (2 men) at the stair top for bots 2 and 7 (17 a hit); StayUpstairs#01 (166,241,-7064) for bots 2, 4, 6, 7. Within 400: none in the yard and the dock (the dock's 7 guards stand at its south end, z -5656 .. -5832, 12 .. 14 m from the door); 1 .. 2 in the lobby. In a free line (the four rules of RULES_X): the dock's three squads (Guards_Reinforcement_StayUpstairs, 01a, 01b) for EVERY first hit (GO + 11 .. 17 s, through the open roller door, 12 .. 20 m), PatrolGuards_01a at the stair top, StayUpstairs#01 over the whole lobby (the model also reports Guards_03 from the glass door down the stair well: a model). Wave B (4 men, 22 s after the ante-room box) and the 6 on the flights were not reached: nobody got that far. So: a free line from the dock's guards into the yard, no stop at the dock, a stair climbed past two men 3 .. 5 m from it, a corridor and a lobby crossed in the open at a hit every 0.1 s, two men inside the point-blank reach of the way.
**What the squad did between the dock door and the stairs** (c_bank5 bots.json / dyn.txt, READ): one Defend step '010_DefendBehaviour_to_loot' of three stations (enter (582,200,-4822), way (0,240,-6368), way (395,240,-7949)) as ONE order, then '011' to the ante-room hold; no gate, no stop but the dynamic step's (2 .. 7 holds of 4 .. 5 s at cover boxes it chose against the cover list and no post: 'Squad#02 point man ... 7 holds, 83 s of timers'), staggered starts 0 / 3 / 5 / 8 s, forks, the 56 s vault timer in the ante-room.

### G.2 What is built (tools/kl_fa_bank.py, behind `--gates`, in the delivered flag set; no flag = every earlier build byte for byte)
Retomoto's planner (kl_fa_bots_rt.gates_plan) is IMPORTED and called with this level's table through a context manager `rt_for_bank` (LIFTED from kl_fa_club.rt_for_club, which the club's workflow built for the same job; `pick_holds_bank` is lifted from kl_fa_club.pick_holds_club with the score changed; `dyn` from kl_fa_club.dyn made to cover the way in; kl_fa_club.py is not imported - another session is editing it - and kl_fa_bots_rt.py is not edited). The way is cut into ROOMS (ROOMS, room_of): before each room the seven HOLD at distinct places at cover boxes (60 .. 240 from a box, 80 apart or more, ONE METRE INSIDE THE MESH = the 16 probes of the game's 'down' test, tools/kl_pf4_probe.py, all reach 1.0; on a lattice four times as fine as the planner's - the box itself is a hole of the mesh and the probes pass only on its outer ring), each step ends in a TriggerActorsDead (stock F07's form, as in Retomoto: it sends its list when every named group is dead OR 0x7800 ticks = 30 s after the hold step called its place reached) and the chain goes on only through it. The rooms:
- **dock** (in): the dock's north end inside the roller door (holds round (422,199,-4878)); names the dock's seven guards and the two patrol men (9 groups).
- **lobby** (in): the west corridor's south end (round (-254,239,-6156)); names the lobby's four.
- **flights** (in): the vault lobby's south end before the glass door (round (375,239,-7340)); names the six guards of the two flights and the ante-room (what a hold can see of them: 1 of 6; the clock otherwise). A hold ON the landing is not possible: it is 12 m wide with the line on its west side and the campaign's men on it, and their routs run up the stairs to the glass door anyway (Guards_01's rout 10 ends at (398,242,-7554)); the fight comes to the lobby's end.
- **vault gate (ante-room hold, 56 s)**: the build's own, unchanged in kind; its seven places are now 400 from the two ante-room guards.
- **hall** (out): the hall's north end at the foyer door (round (117,799,-6257)); names the gallery's eight (2 .. 3 are in a free line of a hold).
- **airlock** and **front** are in the table and OFF. THE AIRLOCK cannot be planned at all with the table's box (MEASURED: `--gate-rooms dock,lobby,flights,airlock,hall,front` stops at 'gate airlock: only 13 hold places at 1 cover boxes in x 300..1000, z -7700..-7000': the beat's police start in the corridor east of it, 537 of 553 places are within 400 of one); THE FRONT plans (holds round (230,799,-9006), 20 men) but is REFUSED BY THE BUDGET, which is the rule for any fifth gate: A gate that wins nothing costs 30 s. W3's slowest van call is GO + 164.1 s; the round is 360 s from the round-start event (GO - 8.5 s); the van must be called ROOM_VAN_MARGIN = 60 s before its end (W3: call -> everybody aboard 12 s; the van drives in 7.2 s and waits 8 s; GUESS): 360 - 60 - 8.5 - 164.1 = **127 s = four gates of 30 s** (slack 7 s). `--gate-rooms dock,lobby,flights,hall,front` is REFUSED by rooms_note with the numbers. Why these four: W4's deaths were the dock and the lobby; the hall is where eight guns look down on a 36 m crossing (W2's three deaths); the airlock's police have LEFT their start places for the ante-room when the crew comes back (the box that wakes them fires when the first criminal is in the ante-room) and the front's twenty are woken by the box at the hall's south end and ARE the escape fight.
**No dynamic hold or timer behind a gate** (`kl_fa_bank.py dyn`): kl_fa_bots_dyn.PERS' out_holds False for the seven and the last loot wait read as 'none' (every leg is then 'behind' it: no hold of its own, no 4 .. 5 s timer), no fork on any leg but the last (the van leg keeps its forks and the dash); a folder without gates (no enemies) gets the step as it always was. MEASURED on the finished folders: `0 holds on the build's way` for all seven squads, 'timers 56 .. 64 s' = the vault timer + the stagger of 0 / 3 / 5 / 8 s; rooms_check fails any 'Timer_hold'.
**The hall dash (kept, behind the gate)**: the eight hall police stand on the GALLERY (HALL_UP: y 1221, both long sides and the north corners); the floor is the crew's; the hall gate's holds are one floor below them, 5 of 7 out of every line (rooms_check). After the gate (the eight dead - 2 .. 3 are seen by a hold - or the 30 s) the crew crosses the 36 m in one go: the gate decides WHEN, hall_dash HOW (eDMS_Sprint on the steps with a place in DASH_BOX; the gate's own hold step is excluded: it is named `NNN_DefendBehaviour_out_<room>`). The dash is the answer to W2's hall deaths (three at holds in the open hall); a second wait there would be that again. NOTE (planner, MEASURED): the hall gate's men are on another floor - no hold is within 25 m of path of a post of theirs on its floor - so this gate mostly runs its 30 s unless the gallery men come down.
**The cash registers**: the stacks lie at (-765 / 1367, 899, -7202 .. -8006 / -7606) and show 20 s after the plaza box or from the foyer box. The hall gate's holds are 850 or more from every stack (rooms_check FAILS a hold inside 850; the loot tactic takes any stack within 800 / 400, kl2 0x8b9641): the gate never stands at them; the dash steps behind it pass them as before (W2.5: the registers pay for holding the front, the owner's wish outweighs the detour).
**The out way station dropped**: way-out station 7 (400,-160,-9577) lay in the middle of the upper landing, within 311 of Guards_01; a landing of 12 m with the line at its west side cannot hold men 400 from a station in its middle, so rooms_plan drops every way-out station within 400 of a start place of the way-in squads (`P['dropped_stations']`): the first out step is then two stations ((405,-774,-11228) and (394,240,-7876)) and its second order runs from the ante-room's neck up both flights to the lobby's south end through the game's pathfinder (ASSUMED to be fine: ~70 m; the escort's and the boarding orders are ~100 m, E3_DM01).

### G.3 The men (CLEAR_MEN, applied in strip() under ROOM_GATES; nobody removed: 61 stay)
Rule: no START of a 'start' or 'down' man within ROOM_LINE_CLEAR = 160 (the point-blank reach, re/melee_damage.md) of the crew's line, the line being the stand-in path through the plan's stations AND the places the bots were really hit in W4 (the stand-in path does not take the west stair that the game's pathfinder took). `finder.py`: the nearest place on the START's mesh part, 70 .. 230 from a cover box, 200 or more from the line, 150 from the other men. MEASURED in the build log: 12 men and one defend place moved: PatrolGuards_01a 492 and 473 (the patrol: one to the dock floor's west end, one into the dock), StayUpstairs#01 Guard_01#03 319, StayUpstairs Guard_01#02 403, 01a 500 and 599, Guards_02 (lower landing) 701 and 799, Guards_01 (upper landing) 756 and 657 (all four to the landings' east sides, 200+ from the line), Guards_03 (the ante-room) 600 and 788 with their defend place Pos#01 720 to the south-west pocket (x 75 .. 225, z -12445 .. -12340): there is no cover box there, so for these two 'at cover' is NOT met; the vault gate's hold (the mesh's north half, z >= -11900) is 400 from them and the crew's line 175. Every other start was already 160+ from the line (201 .. 323 the nearest). The squads' defend and sneak places are NOT moved (the men walk to them when woken - they come to the crew; that is the fight a gate waits for); the planner counts a gate's own squads by their START places only, every later room's squads by every place, and the beat's / the plaza's squads not at all before their box fires (rt_for_bank.near). Waves: wave_plan keeps its rules (a post 200 from the route = the 160 with margin, at cover, 150 from an old man) and ITS OWN station ladder 400 / 300 / 250: MEASURED in extras: A01, A02 and B01 .. B04 and D 400 from every station and hold, A03 and A04 300 (the landings have no room for 400); the strict 400 for all failed (A04, 0 of 1 posts) until the middle way station of the landing was dropped and the ladder restored. start_guns: 7 men bear on the START rows (was 8: the patrol man moved into the dock is the seventh; the dock's guards are the rest).

### G.4 The rules that fail now (rooms_check; run by bots-check and by checks.sh as `rooms`)
MEASURED to catch each, by the faults of the first builds while this was developed: the ante-room hold within 129 .. 378 of Guards_03; two out stations on the beat's start places; a man 96 from the line; three hall holds within 834 .. 890 of a stack. The rules: a hold or station within 400 of a post (start place) of a man who may be alive on his floor (an earlier room's man: 300; out stations only against the hall's men and the start/down men no gate names); a gate whose TriggerActorsDead is missing from any of the seven squads, names other groups than planned, a missing group or a group WITHOUT AN ACTOR (no 30 s clock), a man a gate before it named, has field 1 other than 0, or names more than 9 groups; seven holds not at seven distinct places 80 apart; a hold not 60 .. 240 from a cover box or not 1 m inside the mesh (the 16 probes); a hold inside 850 of a teller stack; a start within 160 of the line; a hold timer ('Timer_hold') of the dynamic step in any squad; the timetable past the budget. Said, not failed: how many of a room's men a hold has a free line to (all four rules, the exact ray too) and how many holds are hidden.

### G.5 The timetable (worst case = MEASURED baseline + the clocks)
The slowest crew (every room runs its 30 s out): W3's GO + 164.1 s + 4 x 30 s = **GO + 284 s** at the van call; the budget GO + 291 s (360 - 60 - 8.5): slack **7 s**. A gate's clock starts when its hold step is called reached (within 10 m 3D: the dock gate's holds are 5 .. 8 m from the START rows, so its clock starts at about GO + 2 s: the planner's note 'armed early'); the seven arrive spread out, so the ante-room timer (56 s from each bot's arrival) is not later than in W3 by more than the gates. Best case (every room won at once): W3's round + the walk. **The no-enemy round**: no man in a gated room -> rooms_plan returns the plan untouched ('no gates'), the dynamic step runs as it always did: the same plan (bots.json identical but for the paths), and the archive is c_bank5's BYTE FOR BYTE (MEASURED: silent bank_vault_noai ddd5d908186afdc5e3e11e0cfd8c70e3a435ae6d, music 62cda999acd49ff7afe8aa2e2110ba47639fee03 - the same sha1 as in c_bank5_fx / c_bank5_music_fx): W3's round, van call GO + 164 s, over at 279 s, its bots finish (the plan is the same, the checkers pass).

### G.6 'Out of the room's sight' - what the mesh allows (MEASURED, rooms_check)
Holds prefer the place the FEWEST of the room's men have a free line to (the club's C5 run: seven holds under 5 .. 8 guns died standing there; the pick sums the men with a line over the seven): lobby 7 of 7 hidden, flights 7 of 7 hidden, hall 5 of 7; DOCK 0 of 7 - the dock's cover boxes are the only cover, every place near the door is in the line of 6 .. 9 of the nine (the yard side 6 .. 7 through the door, the doorway all, the dock's north end all). The dock gate is therefore a fight at 9 .. 14 m behind a low box, the weak one; the other three run on the 30 s clock unless the men come to the crew (an idle human = nobody kills them and the bots do not see them). `--gates-seen` (ROOM_HIDE off) picks places in sight at cover for all.

### G.7 What the next live run must show (the same ini as W4: Risk=2 Ramp=1, police -> crew 0.05, police -> you 1.00, health x 0.73; [Bots] Log=2 Escort=0; the game: a first run on `C:/kl_build/c_bank6_fx/bank_vault` after bank_vault_noai to see the unchanged round)
Per gate (the log: 'bots: record N (bot): lost ...', 'heist stage'):
- **dock** - the seven at their holds (round (422,199,-4878)) from about GO + 4 .. 8 s; they go on at the latest GO + 36 s (30 s after the step is called), earlier if the nine die; hits in the yard before GO + 12 s are START-row hits, not the gate's.
- **lobby** - the first bot there about GO + 30 .. 50 s; the gate opens at the latest 30 s after, none dead; no 'ONE STEP' (the lobby guard at (166,241,-7064) is moved 320 away; the patrol men are off the stair top).
- **flights** - the lobby's south end about GO + 60 .. 90 s; open at the latest 30 s after; the first flight's men come up to the glass door (Guards_01's rout 10) and meet the seven at cover.
- **vault gate** - unchanged (56 s from each bot's arrival; the beat starts at the first); after it the loot and the way out; **hall** - the foyer door about GO + 190 .. 230 s, open 30 s later at the latest; van called by GO + 291 s at the latest (worst case 284).
The pass line for the way in: nobody dead before GO + 60 s (W4: GO + 29 s), no 'ONE STEP' kill before the ante-room, the human at START alive past GO + 96 s. If the clocks of lobby and flights run out and the crew still falls in the next room: build once with `--gates-seen`. If a bot does not stand at its hold when its gate's clock ends: the clock counts from the step being called (ASSUMED from kl2 0x686c4c and Retomoto's runs), so he walks on late, not never. NOT SEEN, ASSUMED: that a Defend order of ~90 m (vault to the lobby's south end) finishes, that the gates' TriggerActorsDead fire for a group whose men are on another floor, and that bots hold at the planned place under fire (club C5: they went to the nearest cover box instead).

### G.8 The rebuild and the checks (MEASURED)
Driver `C:/kl_scratch/vault_gates/all6b.sh` / `all6c.sh` (one build at a time): `test <out> --keep --waves2 --voice --gates [--music-layer4 --str C:/kl_build/v_club/PC_Def.str] --plan <c_bank>/bank_vault_bare/van.json`, the same with `--no-ai`, `test --crew-fix --reset --van-late --voice` (the bare folder; NO `--gates`: it has no squad to gate) + `extras` + `seal`, then `chain.sh` (lighten, wardrobe, bots, guns, talk, fxc, **`dyn`** now `kl_fa_bank.py dyn`, hall-dash, extras, seal), `kl_fa_vaultfx.py apply` (check PASS on all eight), `checks.sh` (the second round's + `rooms`). The music set is built against `C:/kl_build/v_club/PC_Def.str` (the one stream file for both maps; `kl_vault_str.py whd` checks every streamed record of the four music folders into it). Scripts copied into each set: chain.sh, checks.sh, crew_route.py, blocks.py.
RESULTS (MEASURED, each folder's `checks.txt` and `checks/`): every checker PASSES on all eight folders (bank_check, waves, crew, crew_route, bots_dyn, bots_gate, rooms, reverify, van, escape, fake, impact, arms, chars, guns, route_walk / route_built FREE, stream_whd for the music set, `kl_fa_vaultfx.py check`) except the known: the silent set's `preflight` CRASH 1 / `audit` FAIL 2 (the noai: 3) = the one stream-clip finding; the noai folders' 'no police' (music noai: preflight CRASH 1, RISK 1, audit FAIL 2); the bare folders' `guns` / `talk` (no such step there). The music full / wavslim / bare folders: preflight and audit exit 0. The `rooms` checker on the full folders: 4 gates, 27 men in them, 0 men started within 160 of the line: PASS; on the noai and bare folders 'bots.json has no room gates: not checked'.
Zip sha1 (first 8): silent `C:/kl_build/c_bank6_fx` bank_vault = bank_vault_wavslim **40fb91c9** (full 40fb91c94a9620a438b4ceb6db80ff078fb7ce17), bank_vault_noai ddd5d908, bank_vault_bare 051d57e2; music `C:/kl_build/c_bank6_music_fx` bank_vault = wavslim **017a494a** (017a494ae0f7540c1b2c8a3f90c9eb121f11c8de), bank_vault_noai 62cda999, bank_vault_bare 749dbfb1 (the noai and bare archives are the c_bank5 ones byte for byte). Blocks (MB): bank_vault .prm 72.2, .fxc 9.3, .ANM 21.9, .WAV 24.8, .TEX 245.8 = five blocks 161.4; wavslim 151.4; chunk table 65,852 (the same as c_bank5); entities 21,168 nodes. Dynamic step: 0 holds on the way for all seven squads, 56 .. 64 s of timers (vault timer + stagger). The extras (waves) with the gates: A01, A02, B01 .. B04, D01 .. D08 400 from every heister station and hold, A03 and A04 300 (256 and 202 from the way), D03 .. D08 at the ladder's 600 / 800 from cover as before. start_guns: 7 men bear on the START rows at GO + 12 / 25 / 35 / 60 s (W3.7: 8).
CONTROL: `kl_fa_bank.py test <out> --keep --plan <c_bank>/bank_vault_bare/van.json` WITHOUT any flag gives `F01_Main.zip` sha1 **b7e48d31634c9c33cf19a7e8cc315eb65bbcf0af** again (20,643 entities, RESULT PASS, MEASURED after the last edit of tools/kl_fa_bank.py).

## Pressure and staging (2026-10-12; tools/kl_fa_bank.py and this note only; OFFLINE: built and checked, NOT RUN IN THE GAME, nothing installed; sets C:/kl_build/c_bank7_fx and c_bank7_music_fx)
Task: bring the guns that can fire on the crew down to the yardstick of the tab's Withdrawal (kl_fa_club's, measured the same way: at most 3 guns with a clear exact ray on a station of the heist, 4 on a stretch between two), without removing a man (61 stay, the waves stay), by STAGING the rooms of the way in: their squads sleep and are woken room by room. Labels: MEASURED (the built folders, the exact ray), READ (code, logs), ASSUMED, GUESS. Scripts of the analysis: `C:/kl_scratch/vault_pressure/` (meas.py, plan5.py = the search, mv.py / mv2.py = the men that could be moved, hits.py = the logs against the table, tbl.py, scripts/run7.sh / final7.sh = the rebuild). Built from a scratch copy of HEAD's tools plus this branch's kl_fa_bank.py (tools/kl_fa_club.py and kl_chars.py are mid-edit by other sessions and were not used).

### P.1 The measurement (MEASURED; `kl_fa_bank.py pressure-check <folder>` = stage_men / pressure_rows / pressure_check)
A gun is a man of a squad that is IN THE WORLD at that time index, standing at his start post (an upper bound for a man who stays, a LOWER bound for one who walks to a place: see P.6), with a free EXACT ray (third_party/anp hvk_ray, a part blocks when flags & 0x20 or 0x28, eye 160 over the feet, target chest or head) to a place within 60 m on the same floor (|dy| < 120). Places: the seven bots' places at every station of bots.json (holds, ways, loot, exit, boarding), and every 3 m of the mesh path of each bot between two stations. Time index: station j = j, the stretch j -> j+1 = j .. j+1. In the world: the start / down squads from 0 (GO + 1.5 s), wave A from 0.5, the beat's 14 and wave B from 3 (the ante-room box), the hall's 8 from 4, the plaza's 20 and wave D from 11; the beat's police only until 5.5 (they leave their posts for the ante-room when the box fires; what they do after is not known). With STAGING the squads of WAKE_SQUADS come at their event (P.3).
**What the table says of the runs (hits.py, W6 = `W6_vault_waves_hp.log`, GO 04:39:31.2; 527 hit lines; W4 in G.1).** The first hit on five of seven bots came at GO + 12.0 .. 15.5 s in the yard or at the dock door ((655,200,-4470), (575,202,-4590), (295,200,-4802), (603,200,-4778), (427,200,-5249)): the model has 6 guns there (StayUpstairs x4, 01a #1, 01b #2: the dock's garrison through the open roller door), the sixth bot's at (197,200,-3544) 4. Two bots died in ONE STEP at GO + 28.6 / 30.5 s at (53,240,-6891) / (-52,240,-6738) beside the lobby guard (model 1 .. 2 guns: the point-blank rule of re/melee_damage.md, not a count). The heavy places of the later deaths: (408,240,-7945) and (238,240,-7379) at the flights' glass door (model 2 .. 3), (394,-160,-8997) the flights' landing (model 5), (750,240,-6981) the airlock (model 6: the lobby's men and wave B, alive), (442,336,-7649). **Not explained: the hall.** Three bots took 8 .. 23 hits at (609,800,-7132) and (340,800,-6055) at GO + 193 .. 221 s where the model has 0 guns: the hall's eight police stand on the gallery (y 1221) from the load, the exact ray says none of them sees the hall's floor, and they RUN TO COVER on the floor when started (HALL_START '10_RunToCover'), so a start-post count under-reports every walker. So: the table explains the start (6 guns), the point-blank deaths (no), the way down (2 .. 5) and the lobby / airlock (4 .. 6); it does not explain the hall.

### P.2 The delivered build (c_bank6) against the yardstick, and the new one (c_bank7); worst gun count on the seven bots' places at each station / on each stretch
| i | station | c_bank6 station | c_bank6 stretch to the next | c_bank7 station | c_bank7 stretch | |
|---|---|---|---|---|---|---|
| 0 | enter (the dock door) | **6** | **6** | 0 | 0 | |
| 1 | lobby gate's hold | **4** | **6** | 0 | 2 | |
| 2 | flights gate's hold | 2 | **5** | 2 | **5** | KNOWN: wave A's four posts + one of Guards_01 |
| 3 | ante-room hold (56 s) | 2 | 2 | 2 | 2 | |
| 4 | loot | 0 | 2 | 0 | 2 | |
| 5 | way out, the ante-room's neck | 2 | **5** | 2 | **5** | KNOWN: the same landing |
| 6 | the lobby's south end | **4** | **7** | 3 | **6** | KNOWN: wave B + the lobby squad alive |
| 7 | the airlock | **4** | 4 | **4** | 4 | KNOWN: the same men |
| 8 .. 10 | stairs, hall way place, hall gate's hold | 0 | 0 | 0 | 0 | the hall's police are on the gallery (P.1) |
| 11 | the hall's south end | 1 | **9** | 1 | **9** | KNOWN: wave D |
| 12 .. 14 | front exit, level exit, boarding place | 9 / 36 / 36 | 36 / 36 | 9 / 36 / 36 | 36 / 36 | the square: the plaza's 20 + wave D's 24 + 4 of Police_Outside: the owner's big shootout; not a yardstick place |
(c_bank6 measured with the new module on `C:/kl_build/c_bank6_fx/bank_vault`; the hold of gate 1 moved from (15,240,-6160) to (-405,240,-6160) with the rebuilt plan.) **START rows (the idle human), exact ray within 60 m:** c_bank6: GO 0 s: 0 men in the world; GO + 11: **7 guns** (of 19 men in the world); + 30: 7; + 60: 7 (the dock's six + one). c_bank7: **0 / 0 / 0 / 0** (2 .. 3 men in the world: the patrol, and the lobby squad at its backstop GO + 70 s after the fact).
**The way in is inside the yardstick: stations 0 / 0 / 2 / 2, stretches 0 / 2 / 5 / 2 - the one 5 (the flights' landing) is KNOWN.** Before: 6 / 4 / 2 / 2 and 6 / 6 / 5 / 2.

### P.3 What is built (`--staging`, needs `--gates`; the delivered flag set has it; no flag = every earlier build byte for byte)
**The squads sleep** (ZSquadScript field 3 = 0, which every squad of this module already is until a rout is named) and are WOKEN BY NAMING THE SQUAD'S START ROUT (the form every squad here has: the start timer, the beat box and the foyer box already name routs this way, and wave A's Pace / Go chain names a rout from a box and a backstop). Three events (WAKE_EVENTS), each with ONE RELAY `Gameplay!bank_waves!Clock\Wake_<event>` (a TriggerDelay2 of 0.3 s whose list is the routs; the three sources below all name the relay, none names a rout), and three sources:
| event | squads (men) | the gate before (TriggerActorsDead field 2 in all seven bots' copies) | a criminals-only box (once) | backstop (GO + s) |
|---|---|---|---|---|
| lobby | StayUpstairs#01 (3: the lobby's) | none: the dock gate is off | ROOMS lobby's box: (-100,241,-6125) half (900,80,275) | 70 |
| flights | Guards_03 (2: the ante-room's pocket) | the lobby gate | ROOMS flights' box: (400,241,-7325) half (500,80,175) | 100 |
| ante | StayUpstairs (4), 01a (2), 01b (2), Guards_02 (2), Guards_01 (2) | the flights gate | the beat box (ante-room): its list gains the relay | 150 |
(14 gate lists = 2 gates x 7 bots; 3 boxes' worth: two new boxes + the beat box; 3 backstops started by the start timer's list, delay = GO + s + 8.5 - 10 s; the squads' routs LEAVE the start timer's list.) Not staged: PatrolGuards_01a (2 men, they see none of the way in), the beat's 14 (the ante-room box, as before), the hall's 8 (the beat timer's end), the plaza's 20 (the plaza box), the waves. **Nobody is removed.** The assignment is the result of a search (plan5.py): per squad the latest event before any of its men can see the crew, at which none of its men has an exact line to the criminals who wake him (the box's floor on a 3 m lattice, the seven holds of the gate that names the relay) and the counts of the way in stay within 3 / 4; a squad wakes whole, so its worst man decides. **One man moved** (CLEAR_MEN): 01a's lobby man from (497,240,-6684) - in sight of four of the seven flights holds - to (-603,240,-5584) on the upper west level by the stair top (181 from a cover box, 0 rows of the way in seen; mv2.py). This changed the plan a little (the lobby hold is now at (-405,240,-6160)); the bots, dynamic step, guns, talk and every other step are the same code.
**The dock's garrison therefore sleeps until the crew is at the flights' gate (GO + 90 .. 130 s) and is awake behind it** (they stand where they stood: they see no hold or stretch of the way in at all, which is why the search puts them last). That is the price of the yardstick: before the ante-room the only fights are the lobby's 3 men (stretch 1 -> 2: 2 guns) and Guards_03 in the ante-room's pocket (2 at the ante-room hold). If a harder way in is wanted, raise `HOLD_GUNS` / `LEG_GUNS` in plan5.py and the dock squads wake earlier; the builder (`WAKE_SQUADS`) is the only place that changes.
**Checks (all in the module, run by checks.sh):** `stage-check` (staging_check): every squad of WAKE_SQUADS parked, its rout named by its event's relay only, the relay named by the backstop (which the start timer starts), by the event's box (the beat box for 'ante') and, where the event has a gate, by that gate's TriggerActorsDead in each of the seven squads; no man of an event has an exact line to the criminals who wake him; the backstop after the nominal arrival (GO + 40 / 70 / 110 s) and before the van-call budget. `pressure-check` (pressure_check = the 'hold-guns' check, with the men AWAKE at each time): FAILS a station above 3 or a stretch above 4 on the way in (up to the loot) and any gun on a START row at GO / + 11 / + 30 / + 60 s, unless WAKE_KNOWN lists the place with its number and reason (the way out and the square are only said, KNOWN or OVER). `rooms-check`'s old hold-guns block (every start / down man regardless of when he wakes) is off with STAGING. The timetable is unchanged (3 gates of 30 s: the slowest crew calls the van at GO + 254 s of a 291 s budget, slack 37 s; the staged squads add no clock).

### P.4 Where the yardstick is NOT reached, and what it needs
- **The flights' landing, both ways (stretch 2 -> 3 and 5 -> 6: 5 guns):** wave A's four posts (wave_plan keeps them 400 from every station, not off a stretch) and one of Guards_01's two men (the other two moves tried cannot leave the leg's line: 8 -> 6 rows seen). Needs: wave A's posts moved off the landing (wave_plan's route rule at 250 instead of 200, or chain A started by a later box).
- **The vault lobby and airlock on the way out (stretch 6 -> 7: 6, station 7: 4):** wave B's three posts and the lobby squad's men counted ALIVE. If the lobby gate did its job they are dead (3 .. 4 then). Needs a live run to say; or wave B's posts moved.
- **The square (stations 12 .. 14, the stretch to them: 9 .. 36):** the plaza's 20 men and wave D's 24, awake from the foyer / plaza box: the owner's 'big shootout on the square'. It is the finale, the yardstick of a heist station does not apply; the cash registers (stacks at y 899) pay for holding the front.
- **The airlock and the front gates (2e):** NOT BUILT. The airlock cannot be planned (G.2: only 13 hold places at 1 cover box, the beat's police start in the corridor east of it). A FRONT gate would fit the budget now that the dock gate is off (four gates of 30 s: GO + 284 s of 291, slack 7 s) but its men are the plaza's 20, whom the plaza box wakes at the hall's south end where its holds would stand, so it needs its own wake search and the owner's shootout on the square is its fight; left for the lead's call.
- **Not measurable with start posts:** every man who walks to a place (the hall's eight running down from the gallery, the 'down' squads coming up the flights, the hunters): the table is a lower bound for them (P.1).

### P.5 GUESS / ASSUMED
ASSUMED: that a TriggerActorsDead's next list may name a start rout of ANOTHER squad (its own squad's routs are what stock names; a rout is a node like any in a TriggerDelay2's or TriggerBox's list, which stock does name across squads); that the relay (TriggerDelay2) fires again harmlessly when up to nine sources name it in one round (the 7 bots' TADs fire at different moments; wave A's Pace / Go chain is the same shape and ran); that a squad whose rout is named while parked appears at its posts and walks to its Defend places (the form that loaded and was SEEN for the waves). GUESS: the two boxes (the rooms' boxes of ROOMS: the first criminal inside fires), the backstops (GO + 70 / 100 / 150 s: a minute past the arrival of the slowest crew of W3 / W4), the 0.3 s of the relay. ROUND 2: the relays, boxes and backstops are triggers and timers that switch no geometry, so the round-2 reset objects (Reset_show / Reset_hide: doors, rods, vault) do not need them; whether a one-shot box fires again in round 2 is what the older boxes (beat, plaza, dock) already assume; the staged squads are parked at the LOAD only, as every squad of this module.

### P.6 What the next live run must show (the W6 ini: `[Balance]` Risk=2 Ramp=1, police -> crew 0.05, police -> you 1.00, health x 0.73, [Down] on, [Bots] Log=2 Escort=0, an idle human at START, the game on `C:/kl_build/c_bank7_fx/bank_vault` after bank_vault_noai)
- **Nobody dead before GO + 100 s** (W6: two bots GO + 28 / 30 s, five more GO + 135 .. 230 s; W4: all seven before GO + 68 s) and no 'ONE STEP' before the ante-room; **no hit on the human at START before GO + 70 s** (W6 / W4: GO + 11 s; the backstop at GO + 70 s wakes the lobby's three, who do not see the yard).
- Per event, in the log and the pictures (every 2 s): **lobby** the box fires with the first bot at the corridor's south end, GO + 30 .. 45 s; three men appear at (-334,240,-7164), (831,241,-6755), (331,241,-6822), not in the criminals' sight; the lobby gate opens at the latest 30 s after the hold ('heist stage' of the seven moves on) - **flights** the lobby gate's TAD or the flights box wakes Guards_03 in the ante-room's pocket (100,-960,-12445 / -12200), GO + 65 .. 100 s; at the ante-room hold (stretch 2 -> 3, station 3) at most 2 guns - **ante** the flights gate (GO + 95 .. 130 s at the latest) or the beat box wakes the dock's six at (755,202,-5818) ... (384,200,-5223), 01a / 01b at (325,200,-5366), (-603,240,-5584), (-334,240,-5132), (786,201,-5656), Guards_02 (602,-560,-10623) and Guards_01 on the landing (628,-160,-9365): every one of them must be SEEN only after the crew has left (a man seen at a hold or a box of the way in is a fault of the model); the beat's 14 and the vault's 56 s run as before.
- The pass line for the table: stations and stretches of the way in at most 2 / 5; from the loot on, the hits that matter are the KNOWN ones (the landing, the lobby, the square): the log's 'lost' lines by place against `pressure-check`'s rows (hits.py).
- NOT SEEN, ASSUMED: P.5. If the lobby's three do not appear (their gun lines never start), the box or the relay did not fire: the backstop at GO + 70 s must then bring them; if the dock's six never appear by GO + 150 s the TAD form does not work as a wake - then name the routs from the box and the backstop only (WAKE_EVENTS gate=None).

### P.7 The rebuild and the checks (MEASURED)
Driver `C:/kl_scratch/vault_pressure/scripts/run7.sh <silent|music>` (`test <out> --keep --waves2 --voice --gates --staging [--music-layer4 --str C:/kl_build/v_club/PC_Def.str] --plan <c_bank>/bank_vault_bare/van.json`, then the chain: lighten, wardrobe, bots, gun looks, talk, shader cache, dynamic step, hall-dash, **extras (adds the relays, boxes, backstops and the lists)**, seal) and `final7.sh` (kl_fa_vaultfx apply on bank_vault and bank_vault_wavslim; every checker on all four). **bank_vault_noai and bank_vault_bare are the c_bank6 folders copied, not rebuilt: staging needs squads, a round without enemies has none, and `--no-ai` gives the same archive byte for byte** (the bare folder has no squads and no chain). New in checks.sh: `pressure` and `stage`.
**Results (every checker on all eight folders, MEASURED, each folder's `checks.txt` / `checks/`):** all PASS except the known: the silent set's `preflight` CRASH 1 / `audit` FAIL 2 (noai 3) = the one stream-clip finding, the music set's noai (`preflight` CRASH 1 / RISK 1, audit 2) and both bare folders' `guns` / `talk` (no such step there); the music set's full and wavslim folders pass preflight and audit too. New and passing on bank_vault and bank_vault_wavslim of both sets: `pressure` (pressure-check), `stage` (stage-check), `bots_dyn` (now `kl_fa_bank.py dyn-check`: kl_fa_bots_dyn.check does not know a relay as a side item of a chain link, so it runs on the scene with the relay names taken out of the gates' lists in memory), `bank_check` (the squads are accepted when a relay names them), `rooms` (3 gates, 17 men in them, 0 started within 160 of the line). Zip sha1: silent `C:/kl_build/c_bank7_fx` bank_vault = bank_vault_wavslim **a418a3de** (a418a3dee1986a4b609e6b9a3ddfc7e0de4a5b86), bank_vault_noai ddd5d908 and bank_vault_bare 051d57e2 (= c_bank6, copied); music `C:/kl_build/c_bank7_music_fx` bank_vault = wavslim **2e38d72c** (2e38d72c8eb67ac06aba4a2bdc0ac627e652c8dd), bank_vault_noai 62cda999, bank_vault_bare 749dbfb1 (= c_bank6). Blocks (MB): .prm 72.2, .fxc 9.3, .ANM 21.9, .WAV 24.8 (wavslim 14.8), .TEX 245.8 = five blocks 161.4 (151.4); chunk table 65,852; 21,156 entities; the extras step added 3 relays + 3 backstops + 2 boxes to the clock group (8 entities) and 14 + 1 list entries. The delivered chain.sh / checks.sh / crew_route.py point at c:/kl-merge/kl-merge/tools (re-pathed from the scratch copy the build used). CONTROL (MEASURED after the last edit): `kl_fa_bank.py test <out> --keep --plan <c_bank>/bank_vault_bare/van.json` with no flag gives `F01_Main.zip` sha1 **b7e48d31634c9c33cf19a7e8cc315eb65bbcf0af** again (20,643 entities, RESULT PASS). `--gates` WITHOUT `--staging` is no longer the c_bank6 plan: the one moved man (CLEAR_MEN) is applied under --gates alone.

