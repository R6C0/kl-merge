# The three fixes on the four Dead Men maps, in one command

2026-10-10, agent t-join. OFFLINE: nothing was installed, the game was not started, nothing was written
into the Dog Days folder. Tool: `tools/kl_map_tune.py`. Builds: `<work>\build\t_maps\M01 M02 M03 M06`,
made from `<work>\build\z_maps\<map>` (read, not changed). Run log: `<work>\build\t_maps\run.log`; per
map `tune.txt` / `tune.json` in the folder. NOTHING HERE RAN IN THE GAME.

Owner, after Late Night Opening: "dead men guns dont show up in the late night, the late night van
sometimes is a bit weird? camera goes under the map when ur in it and then the ai a bit too easy so just
probably take some logic from retomoto and put it in there and do the same fixes for the other maps, i
think the walk in the park is a heli so it shouldnt be as bad".

## 1. The command

```
python tools\kl_map_tune.py build <finished build folder> <out folder> [options]
python tools\kl_map_tune.py all [<folder of builds> <out root>] [M01 ...]     default z_maps -> t_maps
python tools\kl_map_tune.py check <tuned folder>       every checker again (exit 1 on a failure)
python tools\kl_map_tune.py table <out root>           the tables of section 3 from the folders' tune.json
  --no-guns --no-escape --no-ai        leave a step out
  --start=1 --set=1                    the gun looks to bake (kl_map_guns)
  --no-strength --no-waves --no-chains --no-called --health=1.5      kl_map_ai's parts
  --keep                               keep the steps' folders (<out root>\_work\<name>\1_guns ...)
```

It calls the three agents' tools as libraries and changes none of them:

| # | step | tool (note) | kind | archive members it changes |
|---|---|---|---|---|
| 1 | guns | `kl_map_guns.build` (re/map_guns.md) | ADDS chunks, textures, material rows; writes `KLGuns.ini` | .prm .TEX .MAT .gms .oct .prp |
| 2 | escape | `kl_map_escape.repair` (re/map_escape.md) | one enum per escape camera | .prp |
| 3 | ai | `kl_map_ai.apply` (re/map_ai.md) | values and reference lists of existing objects | .prp |

Why this order:

- The gun step is the only one that adds chunks or renumbers anything, and `KLGuns.ini` names chunk
  indices of the `.prm` it wrote. Steps 2 and 3 each prove by CRC and size of every member that they
  changed the `.prp` and nothing else, so after them `KLGuns.ini`'s and `KLWardrobe.ini`'s numbers still
  name what they named. `kl_map_guns` also refuses a folder that already has a `KLGuns.ini`.
- The ai step sets its health / accuracy floors by the weapon template an actor carries and asks to run
  after anything that touches weapons (re/map_ai.md 10.5). The gun step keeps every template, so the
  result is the same either way - checked: the ai totals of each tuned map EQUAL those of
  `<work>\build\t_ai\<map>` (the ai step alone).
- Escape and ai do not touch the same objects. Escape goes first because nothing in it is assumed; if the
  ai step failed on a map the map would still have guns + camera. The two were NOT tried in the other order.

A step that raises or reports a problem of its own is left out of that map: its folder is removed, the
chain goes on from the folder before, and the RESULT line says `DELIVERED WITHOUT ...` (or FAIL when a
checker then fails). Tried with a made-up failure of the escape step on M06 in a scratch folder: guns + ai
delivered, `kl_map_escape.check` FAIL with the camera eye at (0, 0, 0), exit 1. **No step failed on any of
the four maps; no wrapper repair was needed.**

Checkers, on the WRITTEN folder: `kl_maps.preflight` (again: the gun step changed .gms / .prm),
`kl_maps.audit` (which runs kl_fa.check, the boarding test, kl_impact.check, kl_arms.check,
kl_chars.undrawn, kl_chars.check with the wardrobe roots, kl_snd.verify, kl_voice.census; kl_impact and
kl_chars are reported from that run, not run twice), `kl_map_guns.recheck`, `kl_map_escape.check`, the ai
step's conditions (the .prp re-serialises byte for byte, 0 misfits, no list entry names nothing), the side
files (every file beside the archive the source's by sha1, `KLWardrobe.ini` identical, `KLGuns.ini` there),
the members (only what the steps may change differs), the budget.

## 2. Result

| map | steps run | left out | checkers failed | `kl_maps.py audit` | content id | archive sha1 |
|---|---|---|---|---|---|---|
| M01 diner | guns, escape, ai | - | none | PASS (0; 1 known) | `240a59025c` | `7dd39ac30aac` |
| M02 Late Night Opening | guns, escape, ai | - | none | PASS (0; 6 known) | `30f3dbea12` | `a07524f1534c` |
| M03 the bank | guns, escape, ai | - | none | PASS (0; 0 known) | `4901935de0` | `8f1d69c834f9` |
| M06 A Walk in the Park | guns, escape, ai | - | none | PASS (0; 6 known) | `e8635b2192` | `72e8d03c9fe1` |

'Known' = materials of the MAP without a compiled shader (re/maps.md 14.2), as on the z_maps builds.
Built twice: the same content ids and archive sha1s both times. 45 .. 55 s a map.

Budget, all four: `.ANM`, `.fxc`, `F01_Main.WAV` unchanged byte for byte. `.prm` +391,264 bytes and +94
chunk-table entries (46,996 .. 62,774 of 69,632 usable) and `.TEX` +8.2 MB - all of it the gun step: six
Dead Men gun models in 291 dead chunk indices, 59 + 35 chunks at the end of the table, the guns' textures
(re/map_guns.md 3). Escape and ai add 17 and 466 .. 815 bytes of strings to the `.prp`, nothing else.

**The steps do not disturb each other** (scratch script: every node of the .prp compared by value, key
indices resolved to their strings, against the three agents' own builds `t_guns`, `t_van`, `t_ai`):

| map | nodes | changed by guns alone / escape alone / ai alone | overlap | changed in the tuned build | = the union | each equal to the step-alone node |
|---|---:|---|---:|---:|---|---|
| M01 | 15,000 | 7 / 2 / 25 | 0 | 34 | yes | 34 of 34 |
| M02 | 21,935 | 7 / 1 / 22 | 0 | 30 | yes | 30 of 30 |
| M03 | 19,828 | 7 / 1 / 25 | 0 | 33 | yes | 33 of 33 |
| M06 | 15,600 | 7 / 1 / 24 | 0 | 32 | yes | 32 of 32 |

and every member but the `.prp` is byte for byte the one of `t_guns\<map>` (CRC and size).

Each checker's own command line was also run on the four folders as a separate process:
`kl_maps.py audit` (PASS x4, exit 0), `kl_map_guns.py check` (problems: 0 x4), `kl_map_escape.py check`
(0 faults x4), `kl_impact.py` (problems: 0 x4), `kl_map_tune.py check` (M02: PASS).

One thing the chain changes against the single-step notes: the ai step re-arms squads AFTER the gun step,
so who holds a gun with a look is read from the FINISHED folder (the tables below). M01: re/map_guns.md
names a MAC-10 carrier (Steyr TMP); in the tuned build that squad has rifles and the one look on a guard
is an SG 552 on a `FrontMall_01` man.

## 3. Per map (`python tools\kl_map_tune.py table <work>\build\t_maps`)

### M01 - M01_FA_A diner (Sunny Hill Plaza), escape car

Steps run: guns -> escape -> ai. Left out: none. Result: PASS.

| step | members changed | what changed |
|---|---|---|
| guns | .MAT .TEX .gms .oct .prm .prp | looks baked (start 1, set 1): Rifle_zastavam85 = MP5, Rifle_FN_SCAR = SG 552, Rifle_AK47 = M4A1, SMG_UMP = P90, SMG_MAC_10 = Steyr TMP, HG_M9Beretta = USP; placed actors holding a look in the finished build: FrontMall_01: Rifle_FN_SCAR shows the SG 552; dead chunk indices before / still free: 11433 / 11142 |
| escape | .prp | 2 camera(s) `eFMM_LookFromPosFA` -> `eFMM_LookFromPos` (EscCamera02, EscCamera01); route points moved: 0; faults 2 -> 0 |
| ai | .prp | hit points 1325 -> 1875 (mean 101.9 -> 144.2); accuracy as used 100.0 -> 100.0; unleashed squads 3 -> 5; squads with a wiped-out list 0 -> 9; named at the round start 1 -> 1; named when the vehicle is called 0 -> 10; timers [0.5, 3.0, 3.0, 3.0] -> [0.5, 3.0, 3.0, 3.0]; weapon classes smg 6, pistol 3, rifle 2, shotgun 2 -> rifle 5, smg 3, pistol 3, shotgun 2 |

| bytes | .prm | chunk-table entries | .ANM | .fxc | F01_Main.WAV | .TEX | .prp | archive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before (z_maps) | 55,088,000 | 50,042 | 22,061,764 | 17,760,648 | 21,722,704 | 234,505,616 | 3,109,877 | 196,918,041 |
| after guns | 55,479,264 | 50,136 | 22,061,764 | 17,760,648 | 21,722,704 | 242,724,752 | 3,109,877 | 200,800,962 |
| after escape | 55,479,264 | 50,136 | 22,061,764 | 17,760,648 | 21,722,704 | 242,724,752 | 3,109,894 | 200,800,624 |
| after ai | 55,479,264 | 50,136 | 22,061,764 | 17,760,648 | 21,722,704 | 242,724,752 | 3,110,709 | 200,801,684 |
| **after (t_maps)** | 55,479,264 | 50,136 | 22,061,764 | 17,760,648 | 21,722,704 | 242,724,752 | 3,110,709 | 200,801,684 |

| checker | | result |
|---|---|---|
| kl_maps.preflight | ok | CRASH 0, RISK 0, NOTE 9 |
| kl_maps.audit | ok | PASS (0 that must be 0, 1 known and accepted), content id 240a59025c |
| kl_impact.check | ok | problems: 0 (inside the audit: bone ids, chunk limit, surface table) |
| kl_chars.check | ok | problems: 0, known (map materials without a compiled shader): 1; undrawn people 0 of 32; wardrobe roots 16 (inside the audit) |
| kl_fa / kl_arms | ok | kl_fa.check {'DEGRADED': 4, 'NOTE': 2}; kl_arms.check 0 finding(s); carried: Rifle_AK74 3, - 3, SMG_Type05 2, HG_SW_MP45 2, Shotgun_Hawk_Police 2, SMG_Type79 1, HG_M-77B 1, Rifle_FN_SCAR 1, Rifle_Type81 1 |
| kl_map_guns.check | ok | 6 guns with looks, shows Rifle_zastavam85=MP5, Rifle_FN_SCAR=SG 552, Rifle_AK47=M4A1, SMG_UMP=P90, SMG_MAC_10=Steyr TMP, HG_M9Beretta=USP; problems: 0; placed actors holding a look: 1 |
| kl_map_escape.check | ok | 0 fault(s); 1 vehicle(s), camera eyes: EscCamera02 eFMM_LookFromPos at (1803, 210, 27410) 226 over the ground; EscCamera01 eFMM_LookFromPos at (4049, 525, 19453) 526 over the ground |
| kl_map_ai | ok | .prp re-serialises byte for byte, 0 misfit(s), 0 list entries that name nothing; 13 soldiers, 1875 hit points, accuracy as used 100.0; totals EQUAL to the ai step alone (G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_ai\M01) |
| side files | ok | 18 files beside the archive equal by sha1; ini files: KLWardrobe.ini, KLGuns.ini |
| members | ok | differ from the source: .MAT .TEX .gms .oct .prm .prp |
| budget | ok | .prm 55088000 -> 55479264 (+391264), .ANM 22061764, .fxc 17760648, .WAV 21722704: unchanged; chunk table 50042 -> 50136 of 69632 |

Install: `python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_maps\M01" F01`

### M02 - M02_FA_A Late Night Opening, escape car

Steps run: guns -> escape -> ai. Left out: none. Result: PASS.

| step | members changed | what changed |
|---|---|---|
| guns | .MAT .TEX .gms .oct .prm .prp | looks baked (start 1, set 1): Rifle_zastavam85 = MP5, Rifle_FN_SCAR = SG 552, Rifle_AK47 = M4A1, SMG_UMP = P90, SMG_MAC_10 = Steyr TMP, HG_M9Beretta = USP; placed actors holding a look in the finished build: 3rdFloor_Guard_02: HG_M9Beretta shows the USP; PoliceSwats: Rifle_FN_SCAR shows the SG 552; TransporterGuards: Rifle_FN_SCAR shows the SG 552; 2ndFloor_Guards: HG_M9Beretta shows the USP; dead chunk indices before / still free: 11437 / 11146 |
| escape | .prp | 1 camera(s) `eFMM_LookFromPosFA` -> `eFMM_LookFromPos` (EscCamera01); route points moved: 0; faults 1 -> 0 |
| ai | .prp | hit points 1220 -> 1775 (mean 101.7 -> 147.9); accuracy as used 100.0 -> 100.0; unleashed squads 4 -> 6; squads with a wiped-out list 0 -> 6; named at the round start 1 -> 2; named when the vehicle is called 0 -> 7; timers [0.5, 30.0, 80.0] -> [0.5, 8.0, 45.0]; weapon classes rifle 5, smg 4, pistol 2, shotgun 1 -> rifle 6, smg 3, pistol 2, shotgun 1 |

| bytes | .prm | chunk-table entries | .ANM | .fxc | F01_Main.WAV | .TEX | .prp | archive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before (z_maps) | 54,619,216 | 58,371 | 22,202,472 | 17,760,648 | 22,527,568 | 216,130,816 | 4,642,089 | 177,760,845 |
| after guns | 55,010,480 | 58,465 | 22,202,472 | 17,760,648 | 22,527,568 | 224,349,952 | 4,642,089 | 181,643,608 |
| after escape | 55,010,480 | 58,465 | 22,202,472 | 17,760,648 | 22,527,568 | 224,349,952 | 4,642,106 | 181,644,054 |
| after ai | 55,010,480 | 58,465 | 22,202,472 | 17,760,648 | 22,527,568 | 224,349,952 | 4,642,690 | 181,643,859 |
| **after (t_maps)** | 55,010,480 | 58,465 | 22,202,472 | 17,760,648 | 22,527,568 | 224,349,952 | 4,642,690 | 181,643,859 |

| checker | | result |
|---|---|---|
| kl_maps.preflight | ok | CRASH 0, RISK 3, NOTE 14 |
| kl_maps.audit | ok | PASS (0 that must be 0, 6 known and accepted), content id 30f3dbea12 |
| kl_impact.check | ok | problems: 0 (inside the audit: bone ids, chunk limit, surface table) |
| kl_chars.check | ok | problems: 0, known (map materials without a compiled shader): 6; undrawn people 0 of 31; wardrobe roots 16 (inside the audit) |
| kl_fa / kl_arms | ok | kl_fa.check {'DEGRADED': 4, 'NOTE': 2}; kl_arms.check 0 finding(s); carried: - 3, Rifle_AK74 3, HG_M9Beretta 2, Rifle_FN_SCAR 2, SMG_MPi69 2, Rifle_Type81 1, SMG_Type79 1, Shotgun_Hawk_Police 1 |
| kl_map_guns.check | ok | 6 guns with looks, shows Rifle_zastavam85=MP5, Rifle_FN_SCAR=SG 552, Rifle_AK47=M4A1, SMG_UMP=P90, SMG_MAC_10=Steyr TMP, HG_M9Beretta=USP; problems: 0; placed actors holding a look: 4 |
| kl_map_escape.check | ok | 0 fault(s); 1 vehicle(s), camera eyes: EscCamera01 eFMM_LookFromPos at (981, 235, -9104) 235 over the ground |
| kl_map_ai | ok | .prp re-serialises byte for byte, 0 misfit(s), 0 list entries that name nothing; 12 soldiers, 1775 hit points, accuracy as used 100.0; totals EQUAL to the ai step alone (G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_ai\M02) |
| side files | ok | 18 files beside the archive equal by sha1; ini files: KLWardrobe.ini, KLGuns.ini |
| members | ok | differ from the source: .MAT .TEX .gms .oct .prm .prp |
| budget | ok | .prm 54619216 -> 55010480 (+391264), .ANM 22202472, .fxc 17760648, .WAV 22527568: unchanged; chunk table 58371 -> 58465 of 69632 |

Install: `python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_maps\M02" F01`

### M03 - M03_FA_A the bank (Withdrawal), escape van

Steps run: guns -> escape -> ai. Left out: none. Result: PASS.

| step | members changed | what changed |
|---|---|---|
| guns | .MAT .TEX .gms .oct .prm .prp | looks baked (start 1, set 1): Rifle_zastavam85 = MP5, Rifle_FN_SCAR = SG 552, Rifle_AK47 = M4A1, SMG_UMP = P90, SMG_MAC_10 = Steyr TMP, HG_M9Beretta = USP; placed actors holding a look in the finished build: ParkingLotSWAT_01: Rifle_FN_SCAR shows the SG 552; BankMainSquad_02: HG_M9Beretta shows the USP; dead chunk indices before / still free: 11452 / 11161 |
| escape | .prp | 1 camera(s) `eFMM_LookFromPosFA` -> `eFMM_LookFromPos` (EscCamera01); route points moved: 0; faults 1 -> 0 |
| ai | .prp | hit points 1500 -> 2275 (mean 100.0 -> 151.7); accuracy as used 100.0 -> 100.0; unleashed squads 6 -> 8; squads with a wiped-out list 0 -> 8; named at the round start 1 -> 1; named when the vehicle is called 0 -> 9; timers [0.5, 2.0, 2.0, 3.0, 6.0, 8.0] -> [0.5, 2.0, 2.0, 3.0, 6.0, 8.0]; weapon classes rifle 9, pistol 3, smg 2, shotgun 1 -> rifle 9, pistol 3, smg 2, shotgun 1 |

| bytes | .prm | chunk-table entries | .ANM | .fxc | F01_Main.WAV | .TEX | .prp | archive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before (z_maps) | 60,469,040 | 62,680 | 22,202,616 | 17,760,648 | 22,716,752 | 217,786,368 | 4,259,788 | 188,544,873 |
| after guns | 60,860,304 | 62,774 | 22,202,616 | 17,760,648 | 22,716,752 | 225,939,136 | 4,259,788 | 192,369,889 |
| after escape | 60,860,304 | 62,774 | 22,202,616 | 17,760,648 | 22,716,752 | 225,939,136 | 4,259,805 | 192,369,922 |
| after ai | 60,860,304 | 62,774 | 22,202,616 | 17,760,648 | 22,716,752 | 225,939,136 | 4,260,533 | 192,370,944 |
| **after (t_maps)** | 60,860,304 | 62,774 | 22,202,616 | 17,760,648 | 22,716,752 | 225,939,136 | 4,260,533 | 192,370,944 |

| checker | | result |
|---|---|---|
| kl_maps.preflight | ok | CRASH 0, RISK 0, NOTE 10 |
| kl_maps.audit | ok | PASS (0 that must be 0, 0 known and accepted), content id 4901935de0 |
| kl_impact.check | ok | problems: 0 (inside the audit: bone ids, chunk limit, surface table) |
| kl_chars.check | ok | problems: 0, known (map materials without a compiled shader): 0; undrawn people 0 of 36; wardrobe roots 16 (inside the audit) |
| kl_fa / kl_arms | ok | kl_fa.check {'DEGRADED': 5, 'NOTE': 2}; kl_arms.check 0 finding(s); carried: Rifle_AK74 5, - 5, Rifle_Type81 3, SMG_Type79 2, HG_SigSauer226 1, Rifle_FN_SCAR 1, Shotgun_Hawk_Bullpup 1, HG_SW_MP45 1, HG_M9Beretta 1 |
| kl_map_guns.check | ok | 6 guns with looks, shows Rifle_zastavam85=MP5, Rifle_FN_SCAR=SG 552, Rifle_AK47=M4A1, SMG_UMP=P90, SMG_MAC_10=Steyr TMP, HG_M9Beretta=USP; problems: 0; placed actors holding a look: 2 |
| kl_map_escape.check | ok | 0 fault(s); 1 vehicle(s), camera eyes: EscCamera01 eFMM_LookFromPos at (1576, 328, 407) 290 over the ground |
| kl_map_ai | ok | .prp re-serialises byte for byte, 0 misfit(s), 0 list entries that name nothing; 15 soldiers, 2275 hit points, accuracy as used 100.0; totals EQUAL to the ai step alone (G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_ai\M03) |
| side files | ok | 18 files beside the archive equal by sha1; ini files: KLWardrobe.ini, KLGuns.ini |
| members | ok | differ from the source: .MAT .TEX .gms .oct .prm .prp |
| budget | ok | .prm 60469040 -> 60860304 (+391264), .ANM 22202616, .fxc 17760648, .WAV 22716752: unchanged; chunk table 62680 -> 62774 of 69632 |

Install: `python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_maps\M03" F01`

### M06 - M06_FA_A A Walk in the Park, helicopter

Steps run: guns -> escape -> ai. Left out: none. Result: PASS.

| step | members changed | what changed |
|---|---|---|
| guns | .MAT .TEX .gms .oct .prm .prp | looks baked (start 1, set 1): Rifle_zastavam85 = MP5, Rifle_FN_SCAR = SG 552, Rifle_AK47 = M4A1, SMG_UMP = P90, SMG_MAC_10 = Steyr TMP, HG_M9Beretta = USP; placed actors holding a look in the finished build: JPN_DrugSquad_Island_01: SMG_MAC_10 shows the Steyr TMP; US_DrugSquad_Island_01: Rifle_FN_SCAR shows the SG 552; dead chunk indices before / still free: 11442 / 11151 |
| escape | .prp | 1 camera(s) `eFMM_LookFromPosFA` -> `eFMM_LookFromPos` (EscCamera01); route points moved: 0; faults 1 -> 0 |
| ai | .prp | hit points 1400 -> 1975 (mean 100.0 -> 141.1); accuracy as used 76.4 -> 80.1; unleashed squads 2 -> 2; squads with a wiped-out list 0 -> 8; named at the round start 1 -> 1; named when the vehicle is called 0 -> 7; timers [0.5, 3.0, 3.0, 10.0, 16.0, 45.0, 50.0] -> [0.5, 3.0, 3.0, 10.0, 16.0, 20.0, 50.0]; weapon classes smg 9, rifle 4, shotgun 1 -> smg 9, rifle 4, shotgun 1 |

| bytes | .prm | chunk-table entries | .ANM | .fxc | F01_Main.WAV | .TEX | .prp | archive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before (z_maps) | 49,585,744 | 46,902 | 21,642,576 | 17,760,648 | 21,775,744 | 204,607,072 | 3,123,108 | 177,588,995 |
| after guns | 49,977,008 | 46,996 | 21,642,576 | 17,760,648 | 21,775,744 | 212,826,208 | 3,123,108 | 181,471,608 |
| after escape | 49,977,008 | 46,996 | 21,642,576 | 17,760,648 | 21,775,744 | 212,826,208 | 3,123,125 | 181,471,653 |
| after ai | 49,977,008 | 46,996 | 21,642,576 | 17,760,648 | 21,775,744 | 212,826,208 | 3,123,591 | 181,471,854 |
| **after (t_maps)** | 49,977,008 | 46,996 | 21,642,576 | 17,760,648 | 21,775,744 | 212,826,208 | 3,123,591 | 181,471,854 |

| checker | | result |
|---|---|---|
| kl_maps.preflight | ok | CRASH 0, RISK 2, NOTE 22 |
| kl_maps.audit | ok | PASS (0 that must be 0, 6 known and accepted), content id e8635b2192 |
| kl_impact.check | ok | problems: 0 (inside the audit: bone ids, chunk limit, surface table) |
| kl_chars.check | ok | problems: 0, known (map materials without a compiled shader): 6; undrawn people 0 of 30; wardrobe roots 16 (inside the audit) |
| kl_fa / kl_arms | ok | kl_fa.check {'DEGRADED': 3, 'NOTE': 2}; kl_arms.check 0 finding(s); carried: SMG_Type79 3, SMG_MPi69 2, SMG_Type05 2, Rifle_AK74 2, Rifle_Type81 1, SMG_MAC_10 1, SMG_HK_sp89 1, Shotgun_Hawk_Police 1, Rifle_FN_SCAR 1 |
| kl_map_guns.check | ok | 6 guns with looks, shows Rifle_zastavam85=MP5, Rifle_FN_SCAR=SG 552, Rifle_AK47=M4A1, SMG_UMP=P90, SMG_MAC_10=Steyr TMP, HG_M9Beretta=USP; problems: 0; placed actors holding a look: 2 |
| kl_map_escape.check | ok | 0 fault(s); 1 vehicle(s), camera eyes: EscCamera01 eFMM_LookFromPos at (245, 1819, -279) 1716 over the ground |
| kl_map_ai | ok | .prp re-serialises byte for byte, 0 misfit(s), 0 list entries that name nothing; 14 soldiers, 1975 hit points, accuracy as used 80.1; totals EQUAL to the ai step alone (G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_ai\M06) |
| side files | ok | 18 files beside the archive equal by sha1; ini files: KLWardrobe.ini, KLGuns.ini |
| members | ok | differ from the source: .MAT .TEX .gms .oct .prm .prp |
| budget | ok | .prm 49585744 -> 49977008 (+391264), .ANM 21642576, .fxc 17760648, .WAV 21775744: unchanged; chunk table 46902 -> 46996 of 69632 |

Install: `python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\t_maps\M06" F01`

## 4. What the owner should look at

None of it has run. Each line is one thing to see; the build shows the Dead Men gun looks without any
menu step (the Guns page does nothing on these builds until the hook is changed, section 5).

**M02 Late Night Opening** (the map the report was about)
- Guns: the two pistol guards (`3rdFloor_Guard_02`, `2ndFloor_Guards`) hold a USP, one man of the police
  car squad and one transporter guard an SG 552. Is each ONE gun (not two models inside each other)?
  A Zastava in anyone's hands is an MP5; bought UMP = P90, MAC-10 = Steyr TMP, AK-47 = M4A1, M9 = USP.
  The shop's name and picture still say the Dog Days gun.
- Car camera: aboard the escape car the view should be a fixed camera about 2.4 m up, 16 m from the car
  (at (981, 235, -9104)), turning with the player as the car leaves - not the mall's atrium floor.
- The car itself: nothing was changed in its route (nothing measurable is wrong with it). If it is 'weird'
  again: is the police SWAT car on the car-park road when the escape car arrives; does the car hop while
  standing; does anything happen 11 .. 13 m into the drive away (a level bound)?
- Enemies: the police car should come about 45 s after GO whatever you do (before: 80 s after the first
  step into the mall, or never). Do the four get OUT of it, flank at once and hunt 8 s later? (If they stay
  seated: `<work>\build\t_ai\car_exit\M02` is the comparison build.) Kill the two 2nd-floor guards: do the
  others come and does the car come at once? Riflemen have health 175 against a pistol guard's 100.
  Step into the exit box: does everybody alive come?

**M01 diner**
- Guns: one man of `FrontMall_01` (the parked-car police) holds an SG 552.
- Camera: two escape cameras (25 m from the stop, and one filming the road out); before, both sat outside
  the map at the origin.
- Enemies: the four men in the two parked cars now have rifles and get their flank order when the diner is
  alarmed (before: never). The two pistol men of the back room rush. Do the car men leave their cars?

**M03 the bank**
- Guns: a man of `ParkingLotSWAT_01` holds an SG 552, one of `BankMainSquad_02` a USP.
- Camera: aboard the van the view was 104 UNDER the street; now 2.9 m over it, 15 m from the van.
- Enemies: two hall squads unleashed; a hall squad wiped out calls the next police car; the civil-war
  counter needs 2 instead of 4. Nine police come in four cars: do they get out?

**M06 A Walk in the Park** (helicopter; the least changed, as the owner expected)
- Guns: one Japanese gang man holds a Steyr TMP (MAC-10), one American an SG 552.
- Camera: aboard the helicopter the view was 100 UNDER the water; now 17 m up, 64 m from the helicopter.
- Enemies: health by weapon class (1,400 -> 1,975 hit points), four riflemen more accurate, the American
  side hunts 20 s after the first shot instead of 45 s. Nobody re-armed, nobody unleashed.

**All four**: a second load of the level in one game session (the .prm is 0.4 MB, the .TEX 8.2 MB larger
than the build played); the wardrobe (Heister page) still works - its ini is unchanged and the gun
agent measured its model chunks byte for byte the same, but that was not seen. Still no AI heisters, still
12 .. 15 enemies a map (stock: 21 .. 45): no step adds a person (re/map_ai.md 7).

## 5. For the lead

- **`debug\slot.py` does not copy `KLGuns.ini`** (`SIDE = ('KLJoin.ini', 'KLWardrobe.ini')`). With the
  hook installed today that changes nothing: klgun.c takes `Version == 1` only (klgun.c line 89) and these
  files are Version 2, so the build shows what is baked either way. Once klgun.c reads Version 2
  (re/map_guns.md 5), `'KLGuns.ini'` must be in `SIDE` - and because slot.py REMOVES a side file the build
  lacks, that also clears a stale one. The test slot has no `KLGuns.ini` today (listed, read only).
- `kl_maps.audit`'s line 'since that verify: lighten changed ..; the wardrobe changed ..' does not print
  the `guns`, `escape` and `map_ai` entries the three steps record in `steps.json` (it prints `bots`).
  The folder IS held to `steps.json`'s `final`, and passes.
- Order with the steps that are not in this command: `kl_add_plates` (Payday 2 masks) and anything else
  that stubs or renumbers chunks must run BEFORE this command (the gun step is first here for the same
  reason); a `.prp`-only step such as `kl_fa_bots.apply` can run before or after - not tried here, and
  after it `python tools\kl_map_tune.py check <folder>` only holds if the folder's source is still the
  folder `tune.json` names (the members / side-file tests compare with it).
- The four z_maps builds have the eight Dog Days masks only; so have these.
- The ai step runs with its defaults (by-pass of the lost car-exit routs, no `--car-exit`, no
  `--presets`, health x 1.0). `--car-exit` is not offered by this command: its build fails
  `kl_maps.py audit` as a separate process by design (re/map_ai.md 9); use `kl_map_ai.py` for run A2.
- Live order suggested: `t_maps\M02` first (one load = G1 of re/map_guns.md, C1 of re/map_escape.md, A1 of
  re/map_ai.md at once). If something faults, the single-step builds `t_guns\M02`, `t_van\M02`, `t_ai\M02`
  tell which step it was - that is the reason to keep them.
- `guns.json` / `map_guns.json` / `escape.json` in a tuned folder name the step's work folder
  (`t_maps\_work\..`, removed) as their `out`; `tune.json` has the real paths.

## 6. Not established

- Everything in the running game: no tuned build was loaded.
- What each agent's note lists as not established stays so: whether the hide bit is what hides a gun part
  (re/map_guns.md 2), what the three rule questions of the camera trigger are and why the car is 'weird'
  (re/map_escape.md 3, 7), whether `ZSquadScript` list 8 is 'wiped out', whether the monitor's field 4
  fires, what a seated squad does (re/map_ai.md 11).
- Escape before ai was the only order tried between those two.

## 7. After the review (2026-10-10): `t_maps2`, and the AI heisters on top: `u_maps`

`re/map_tune_review.md` found three defects of the ai step in the `t_maps` builds (F1 the 'vehicle called'
list without `ROOT\`, F2 / F3 orders on M02 and M03). They are fixed in `tools/kl_map_ai.py` and kept out by a
check (re/map_ai.md 12). **The `t_maps` folders of sections 2 and 3 are the OLD builds; use `t_maps2`.**
OFFLINE: nothing installed, the game not started.

    python tools\kl_map_tune.py all <work>\build\z_maps <work>\build\t_maps2        four of four PASS
    python tools\kl_fa_bots.py build <work>\build\t_maps2\Mxx <work>\build\u_maps\Mxx   the AI heister squad on top

| bytes | .prm | chunk-table entries (`kl_impact.CHUNK_SAFE` 69,632) | .ANM | .fxc | F01_Main.WAV | .TEX |
|---|---:|---:|---:|---:|---:|---:|
| M01 `t_maps2` = `u_maps` | 55,917,968 | 50,254 | 22,061,764 | 17,760,648 | 21,722,704 | 242,724,752 |
| M02 | 55,449,184 | 58,583 | 22,202,472 | 17,760,648 | 22,527,568 | 224,349,952 |
| M03 | 61,299,008 | 62,892 | 22,202,616 | 17,760,648 | 22,716,752 | 225,939,136 |
| M06 | 50,415,712 | 47,114 | 21,642,576 | 17,760,648 | 21,775,744 | 212,826,208 |

- The `.prm` is 438,704 bytes and the chunk table 118 entries larger than in `t_maps` (+829,968 / +212 against
  `z_maps`): the gun step (`kl_map_guns` / `kl_guns`, another session's, changed since) adds more than it did
  for `t_maps`. Not this step's doing; `kl_map_guns.py check` says problems: 0 on all eight folders.
- The checker `kl_map_ai` of this command now says 'list faults 0 (without ROOT in the whole level 0, order
  rules F2 F3 0 ...)' and 'totals EQUAL to the ai step alone (`t_ai2\<map>`)'.
- The squad step takes a tuned folder as it is (no clash with `KLGuns.ini`, which it copies; its `.prm` edit is
  the 4-byte record offset of 987 .. 2,491 model roots, none of them a gun root: `kl_map_guns.py check`
  problems: 0 after it). On the four `u_maps` folders: `kl_fa_bots.py check` PASS (0 FAIL; NOTES 0 / 0 / 8 / 1 as
  on `b_bots`), `kl_fa_bots.py diff t_maps2 u_maps` 'only the squad was added', `kl_map_guns.py check` problems: 0,
  `kl_maps.py audit` PASS (1 / 6 / 0 / 6 known), `kl_impact.py` problems: 0, `kl_maps.py preflight` CRASH 0,
  `kl_map_ai.faults` 0, `kl_map_escape.check` 0 faults. `kl_map_tune.py check` is NOT for a `u_maps` folder
  (its member test compares with `z_maps`; the squad changes .gms .buf .oct .rmi .rmc).
- **Section 5's first item is out of date**: the working tree's `klhook\klgun.c` reads Version 2, so with that
  hook `KLGuns.ini` matters, and `debug\slot.py` still neither copies nor removes it (`SIDE` has no
  `KLGuns.ini`): after `slot.py put`, copy the build's `KLGuns.ini` beside the slot's archive by hand, or
  remove a stale one - each map has other root numbers.
- A bot carries `Rifle_zastavam85`, whose model shows the MP5 look in these builds: seven MP5s beside the player.
