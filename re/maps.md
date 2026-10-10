# Every map through the graft - what builds, what verifies, what is missing

2026-10-09. Offline only: nothing here was installed or started in the game. Everything was built with
`tools/kl_maps.py` (a driver around `kl_graft.build`) into scratch folders; `kl_graft.py` and the other
tools are unchanged. "problems" = what `kl_graft.verify` returns (0 = the build would be installed),
"FA" = `kl_fa.check` on the written archive. Numbers are read back from the written files.

Re-run (about 50 s per set on this machine, each build is a process of its own):

    python tools/kl_maps.py maps  <out>                     F07 + each Dead Men FA map
    python tools/kl_maps.py hosts <out> M03_FA_A            F01..F09 as S
    python tools/kl_maps.py m09   <out>                     F07 + M09_A / M09_B, raw and with the pre-pass
    python tools/kl_maps.py chain <out> F07 M09_B M09_A --heroes     three sources
    python tools/kl_maps.py table <out>                     the table below
    python tools/kl_maps.py what M06_FA_A | sides M09_A | clash M09_A M09_B | hostfacts M03_FA_A | navtest

Words: S = systems level (Dog Days), M = map level. NOT ESTABLISHED = I did not prove it. A statement
without that mark was run and seen.

---------------------------------------------------------------------------------------------------

## 0. Short answers

1. **All four Dead Men FA maps build and verify with 0 problems under F07** - M02_FA_A and M06_FA_A
   needed no change to any tool. No CRASH or BROKEN finding from `kl_fa.check` on any of them.
2. **The maps, by Dead Men's own menu text** (`AllLevels/Menu/Online/Scenarios/TitleNN`, `BriefingNN`):
   M01_FA_A = "Hot Coffee" (the diner), **M02_FA_A = "Late Night Opening"** (the jewel shop Hertzer &
   Sons in a three-floor mall with a car park - NOT streets), M03_FA_A = "Withdrawal" (the bank),
   **M06_FA_A = "A Walk in the Park"** (the Japanese Gardens, loot = cocaine, escape by helicopter).
3. **The choice of S matters in one hard way and several soft ways.** F01, F02, F03 cannot be S (11
   problems each: their particle and cartridge templates live in their map, as kl_graft's notes say).
   F04..F09 all give 0 problems with M03_FA_A. Among those the differences are the post-filter palette,
   which animation sets are native, bank size and archive size (section 3). F07 stays a good default;
   **F08 is the better S for M06_FA_A and the leanest for M03_FA_A** (section 3.3).
4. **Retomoto, single parts:** F07 + M09_A and F07 + M09_B build as they are (kl_pf4 no longer refuses
   M09_A's array 7), but `kl_prpjoin.sides` calls the whole campaign 'map'. With the campaign pre-pass
   of `kl_maps.py` each part verifies except for (a) the Fragile Alliance layer, which does not exist,
   (b) 6 / 9 stream clips the merged PC_Def.str lacks, (c) in B three emitters naming Dead Men's
   `Impacts_Default_Smoke`.
5. **Retomoto, both parts in ONE level: built.** `kl_maps.py chain` runs `kl_graft.build` twice (S + B,
   then that + A) and gets one archive: 24,165 entities, 22 rooms, 2,141 textures of 4096, 1,397
   materials of 2048, 4,801 sounds / 4,635 waves, 314 MB, both navigation meshes in one (603,332
   bytes, `nav_join`, an EXPERIMENT that passes `kl_pf4.check`), A's FDX block, 0 dangling scene paths.
   Same problems as the single parts and nothing else. Missing: section 6.
6. **Third pass (sections 9, 10): M02_FA_A and M06_FA_A are ready for their first live run.** Every
   build of this file was made again with kl_graft as committed in 6238e30 and gives the same
   problem counts. `kl_maps.py preflight` runs every offline check on a kept build and looks for the
   crashes the diner and the bank hit: CRASH 0 on all four delivered builds. What these two maps have
   that no map which ran live had is listed with the Dog Days code behind it (9.3); the one with a
   pre-pass is M02's seven `ZEnvSampler` (a renderer path no stock Dog Days level enters): the first
   M02 build loads them as ZSTDOBJ (`--flat ZEnvSampler`).
7. **The map names are now from the exe, not from content:** Dead Men's own table (kaneandlynch.exe
   0x641570) lists the four scenes in the order of `Title00..03` (section 2).
8. **Fourth pass (section 14, 2026-10-10): the four FA maps with every fix the played Retomoto build
   has** - kl_arms, the execution fix, bone ids, voices on, lightened, the wardrobe - in
   `<work>\build\z_maps\M01 M02 M03 M06`, every checker at 0 or a listed finding, `python
   tools\kl_maps.py ready <out>`. Archives 178 .. 197 MB, .prm 49.6 .. 60.5 MB (below stock F07's 63).
   M02's boarding action stood at the bank's coordinates and is moved to its car. Not run in the game.

---------------------------------------------------------------------------------------------------

## 1. The table

`python tools/kl_maps.py table <out>` after the runs above. The table was made with kl_graft.py as
committed in a07de47; F07 + M02 / M03 / M06 and the three-source chain were run again after the live
agent's `stream_groups` edit of kl_graft.py and gave the same rows.

| S + M | problems | FA crash/broken/degraded/note | archive MB | beside MB | entities | rooms | textures /4096 | materials /2048 | sounds | waves |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F07 + M01_FA_A | 0 | 0 / 0 / 4 / 2 | 336 | 47 | 14999 | 12 | 1999 | 1354 | 4878 | 4741 |
| F07 + M02_FA_A | 0 | 0 / 0 / 4 / 2 | 310 | 47 | 21934 | 32 | 1697 | 1076 | 4910 | 4773 |
| F07 + M03_FA_A | 0 | 0 / 0 / 5 / 2 | 320 | 48 | 19827 | 20 | 1864 | 1193 | 4918 | 4782 |
| F07 + M06_FA_A | 0 | 0 / 0 / 3 / 2 | 310 | 46 | 15599 | 7 | 1576 | 995 | 4797 | 4658 |
| F06 + M06_FA_A | 0 | 0 / 0 / 3 / 2 | 320 | 40 | 15598 | 7 | 1591 | 922 | 4877 | 4680 |
| F08 + M06_FA_A | 0 | 0 / 0 / 3 / 2 | 278 | 50 | 15598 | 7 | 1658 | 914 | 4680 | 4520 |
| F01 + M03_FA_A | 11 | 0 / 0 / 6 / 2 | 339 | 37 | 19228 | 20 | 1942 | 1115 | 4964 | 4808 |
| F02 + M03_FA_A | 11 | 0 / 0 / 6 / 2 | 317 | 41 | 19228 | 20 | 1723 | 951 | 4938 | 4748 |
| F03 + M03_FA_A | 11 | 0 / 0 / 6 / 2 | 341 | 42 | 19227 | 20 | 1900 | 1141 | 4870 | 4705 |
| F04 + M03_FA_A | 0 | 0 / 0 / 5 / 2 | 363 | 53 | 19827 | 20 | 1942 | 1067 | 5065 | 4913 |
| F05 + M03_FA_A | 0 | 0 / 0 / 5 / 2 | 330 | 52 | 19827 | 20 | 1726 | 889 | 5154 | 4859 |
| F06 + M03_FA_A | 0 | 0 / 0 / 5 / 2 | 330 | 42 | 19826 | 20 | 1879 | 1119 | 4997 | 4801 |
| F08 + M03_FA_A | 0 | 0 / 0 / 5 / 2 | 287 | 52 | 19826 | 20 | 1946 | 1111 | 4800 | 4641 |
| F09 + M03_FA_A | 0 | 0 / 0 / 5 / 2 | 331 | 50 | 19832 | 20 | 1835 | 1002 | 4723 | 4600 |
| F07 + M09_A (as kl_graft takes it) | 13 | 1 / 9 / 6 / 1 | 317 | 48 | 15378 | 12 | 1714 | 1038 | 5514 | 5316 |
| F07 + M09_A, campaign pre-pass | 11 | 1 / 9 / 5 / 1 | 277 | 45 | 14425 | 12 | 1585 | 973 | 4670 | 4528 |
| F07 + M09_B (as kl_graft takes it) | 12 | 1 / 9 / 5 / 1 | 334 | 49 | 20999 | 15 | 2046 | 1307 | 5611 | 5392 |
| F07 + M09_B, campaign pre-pass | 12 | 1 / 9 / 4 / 1 | 291 | 46 | 19111 | 12 | 1903 | 1221 | 4700 | 4541 |
| **F07 + M09_B + M09_A** (chain, pre-pass) | 12 | 1 / 9 / 4 / 1 | 314 | 48 | 24165 | 22 | 2141 | 1397 | 4801 | 4635 |
| F07 + M09_A + M09_B (the other order) | 12 | 1 / 9 / 4 / 1 | 314 | 48 | 24165 | 22 | 2141 | 1397 | 4801 | 4635 |

Reading the limits:
- **Textures / materials**: the worst case is 2,141 of 4096 and 1,397 of 2048 (Retomoto, both parts).
  Of those 1,188 textures and 700 material slots are F07's own, map leftovers included (kl_graft keeps
  S's dead map models: "bloat, no risk"). Room is not the problem.
- **Entities**: 24,165 for Retomoto before any authored FA layer; the largest stock level has 42,915.
- **Sounds / waves**: the largest stock bank has 4,806 / 4,568. Every Dead Men map under F07 is above
  the stock wave count (F07 + M03 ran live at 4,914 / 4,778 without a pool fault, run S3). Retomoto with
  both parts is at 4,801 / 4,635: below what already ran. F04 and F05 as S are the heaviest banks (5,065 /
  4,913 and 5,154 / 4,859): untested sizes.
- **Archive**: 278..363 MB; the .TEX is 330..460 MB unpacked. REF slot count 25,306..45,053 (stock
  F08's own ids are sparse); the .prm of the three-source build has 62,614 chunks, 90 MB.
- The rows of the two M09 orders are equal in every count; they differ in what the second step of the
  chain carries (section 5.3).

`kl_fa.check` findings on the four FA maps (all DEGRADED or NOTE, none fails the build):
- all: no spawn points of the Dog Days-only kinds (TEAM_MERC, TEAM_POLICE, UCC), 0 `PointOfInterest`, no
  bot squads, Dead Men's music fields 157 / 158, no `MercSpawnCam*`;
- M01, M02, M03: the escape vehicle is a `ZHavokCar` on a spline (`OnlineVehicleOnSpline` x4 / x3 / x4):
  untested path in Dog Days. **M06 has no such finding**: its escape vehicles are 2 `ZHeli` driven by
  `OnlineEscHavokCar` + `OnlineEscVehicleController`, the form stock F02, F03, F06, F08 use;
- M03: 1 of 15 squads named by no object.
Notes the builds print: 1 (M01) and 2 (M02) `OnlineSpeakTrigger` cut because their line is not in the
merged bank; "dynamic lists name different classes; kept F07's" on every Dead Men map (F07's dynamic list
has 8 classes, those of M03_FA_A, M09_A and M09_B 12 - kl_graft keeps S's list. What a Dead Men map then lacks at
run time is NOT ESTABLISHED; M01 and M03 ran clean live with it).

---------------------------------------------------------------------------------------------------

## 2. What each Dead Men FA map is

`python tools/kl_maps.py what <level>`. The titles are in every Dead Men level's English .LOC
(`AllLevels/Menu/Online/Scenarios/Title00..03`, `Briefing00..03`, the same four as
`.../CreateGame/Scenario1..4`). The pairing title <-> level folder was first made by content (the
table below); the third pass found the table itself:

    kaneandlynch.exe 0x641570 (a menu message handler; image base 0x400000):
      0x6415a3  mov [esp+0x28], 0x970f30   "Locations/M01_FA_A/M01FAA_Main"
      0x6415ab  mov [esp+0x2c], 0x970f10   "Locations/M02_FA_A/M02FAA_Main"
      0x6415b3  mov [esp+0x30], 0x970ef0   "Locations/M03_FA_A/M03FAA_Main"
      0x6415bb  mov [esp+0x34], 0x970ed0   "Locations/M06_FA_A/M06FAA_Main"
    and the titles are fetched as "/Menu/Online/Scenarios/Title%02d" (0x64f87d) / "...Title%02i" (0x64d65d)

a local array of four scene names in the order M01, M02, M03, M06, and four titles numbered 00..03
(the exe has no other reference to an FA scene name but one to M03's at 0x75eae6). Where the handler
indexes the array was not followed to the load call: the ORDER is read, the use is an ASSUMPTION that
content confirms four times over.

| Dead Men Fragile Alliance map | level folder | campaign chapter of the same place |
|---|---|---|
| Hot Coffee (`Title00`, `Scenario1`) | M01_FA_A | M01 'Impact' is another place; the diner is FA-only |
| **Late Night Opening** (`Title01`, `Scenario2`) | **M02_FA_A** | none (campaign M02 is 'Trial'); textures `Metal_WatchStoreSign_01_M02_FA`, `Glass_Jewels_01_M02_FA`, `Glass_Window_Mallsigns_01_M02_FA`, 22 borrowed from `Locations/M03` |
| Withdrawal (`Title02`, `Scenario3`) | M03_FA_A | M03A 'Withdrawal' (the bank) |
| **A Walk in the Park** (`Title03`, `Scenario4`) | **M06_FA_A** | Tokyo: textures `Locations/M06` 237 and `Locations/_JPN` 27 (`Paper_Rice_Lantern_01_JPN`, `Metal_Sign_Escape_01_M06`) |

'The Mizuki' is the campaign chapter M05A (`AllLevels/Menu/Play/M05A_ChapterTitle`), 'Retomoto Tower'
M09A; neither is a Fragile Alliance map. No string 'Late Hours' exists in Dead Men's .LOC: the map is
'Late Night Opening'. The .LOC also holds placeholder titles for ten maps that never shipped on PC
(`TitleDL01..10`, briefings 'Bank Vault', 'Construction Site', 'Prison', 'Tokyo', 'Mansion', 'Jungle',
'Havana', 'Las Vegas', 'Whitehouse', 'Subway').

| level | title | briefing (shortened) | what the level's own data shows |
|---|---|---|---|
| M01_FA_A | Hot Coffee | "Senator Simmens ... eats in the same diner ... escape rides out back behind the diner" | seen live (Sunny Hill Plaza street, car park); `ZHavokCar` x5 |
| M02_FA_A | Late Night Opening | "The jewel shop Hertzer & Sons ... smash the shop displays ... out to the front where our escape cars will pick us up" | 29 rooms: `Ins_Atrium_101a / 201a / 301a` (three floors, 960 / 1631 / 1218 entities), `Ins_StoreJewel_201a` 626, `Ins_StoreWatch_201a` 606, `Ins_OfficeJewel_201a`, `Ins_StoreExit_101a`, `Ins_RespawnRoom_101a`, hallways and corridors per floor, `Out_Parkinglot_101a` 718, `Out_Skyline`; 303 `Jewelbag` loot objects, 26 `OnlineMoneyContainer`, 1,952 `GlassRaling`, 528 `escalatorB`; atrium about 80 m x 60 m, car park out to z -18500; `ZHavokCar` x2 |
| M03_FA_A | Withdrawal | "The US Credit Bank, Downtown ... loading dock ... money boxes" | seen live (the bank plaza) |
| M06_FA_A | A Walk in the Park | "Yakuza crime lord Mr. Yuudai ... coke transaction ... at the Japanese Gardens ... other side of the garden where our chopper will pick you up" | 5 rooms, all outdoors (`M06_FAA_Out_Part_01a..04a`, `Out_Visible_01a`); 299 `DopeBag` loot objects (307 `OnlineMoneyCtrl`); names `ParkLamp` 686, `Pavilion`, `Shrine`, `Spiritual`, `BridgePillar`, `HighwayLamps`, `LowPalm`, `Pine`; 2 `ZHeli`; top-level `BossChopper!` (7 subtrees) and `Effects/Hind_Dammage_01.zip`; 145 scatter objects (grass); the largest room spans about 415 m x 330 m (entity positions, scenery included) |

CLAUDE.md says "M02 = streets": that is wrong; M02_FA_A is the mall with the jewel shop. (CLAUDE.md is
not mine to edit.)

Per map, what the conversion did (from the logs): M02_FA_A 78 gates, 1,375 lit descriptors handled by
`kl_prm` ("lit 1375, lit_meshes 1375"), 137 .LOC keys + 341 sounds grafted; M06_FA_A 8 gates, 145
scatter records converted, 129 .LOC keys + 228 sounds. FDX blocks: M01, M02, M06 have one (carried),
M03 has none. Navigation meshes 101 KB / 238 KB / 187 KB / 259 KB.

---------------------------------------------------------------------------------------------------

## 3. Does the choice of S matter? (every stock F level against M03_FA_A)

`python tools/kl_maps.py hosts <out> M03_FA_A` and `hostfacts M03_FA_A`.

### 3.1 The hard part

F01, F02, F03: 11 problems each, the same ones: 10 (of more) `ZFFItemTemplateAmmo ZItemTemplateAmmo[10]`
paths into `ROOT\Locations/F0x/...\Effects/ParticleTemplates.zip\Cartridge_Templates_*` that left with
S's map, and "6030 particle template names do not resolve". Their systems subtree has 8,538 nodes;
F04..F09 have 9,137 (F09 9,142): the 599 extra nodes are those templates. **S must be F04..F09.**

### 3.2 What differs among F04..F09 (all 0 problems)

| S | palette group | native sets of M03's six (`Army Civilian Female Police Police_USA Van`) | .ANM stand-ins the join had to take | FDX of its own | escape vehicle of the level | kept by kl_fa | bank after graft (sounds / waves) | archive MB |
|---|---|---|---|---|---|---|---|---:|
| F04 | own | Civilian | Police from F03 | yes (dropped) | 3 `ZAnimatedVehicle` | 7, monitor | 5065 / 4913 | 363 |
| F05 | = F02 | none | Police, Civilian, Female<-Civilian from F03 | no | 3 `ZAnimatedVehicle` | 7, monitor | 5154 / 4859 | 330 |
| F06 | = F07 F08 F09 | Police | Civilian, Female<-Civilian from F03 | no | 2 `ZHeli` + `OnlineEscHavokCar` | 6, monitor | 4997 / 4801 | 330 |
| F07 | = F06 F08 F09 | Civilian | Police from F03 | no | 3 `ZAnimatedVehicle` | 7, monitor | 4918 / 4782 | 320 |
| F08 | = F06 F07 F09 | Civilian, Police | none from a donor | no | 2 `ZHeli` + `OnlineEscHavokCar` | 6, no monitor (kl_fa adds an empty one) | 4800 / 4641 | 287 |
| F09 | = F06 F07 F08 | Civilian | Police from F03 | no | 3 `ZAnimatedVehicle` | 7, monitor | 4723 / 4600 | 331 |

("Army" -> copy of Swat_02 and "Female" -> copy of Civilian are stand-ins under every S; Police_USA and
Van are converted from Dead Men under every S. `kl_anmjoin.STAND_IN`, guesses.)

- **Palettes.** `PostFilterPalettes` is S's (kl_graft). Four of the six hosts carry the same blob (F06 =
  F07 = F08 = F09), F05's equals F02's, F04's is its own. Every Dead Men FA map has 22 `PostFilterSet`
  and 2 `PostFilter` controllers that index the palette; kl_graft leaves Dead Men's `PostFilterBoxes`
  out. So with F06..F09 the picture's grading is the same whichever is S; F04 / F05 would grade
  differently. Which grading suits a Dead Men map is a matter for the eye: NOT ESTABLISHED here.
- **Animation sets.** S decides which sets are native and which come from the donor F03. Under F08 no
  set of M03's has to be borrowed from a third level.
- **FDX.** The map's own block is used; an S with one of its own (F04) loses it, which is right: it
  belonged to F04's lamps.
- **Escape plumbing kept by `kl_fa.host_keep`.** The kept objects are position-free; `kl_fa.prune` then
  cuts their references into S's removed map (2 under F08, 5 F05, 8 F09, 13 F07, 15 F04, 18 F06). S's
  escape vehicles themselves always leave with S's map, so the KIND of S's vehicle does not reach the
  result except through whatever the kept monitor still holds (its fields after the prune were not
  read one by one). F08 (and F03) keep no monitor - theirs is not a single top-level node - and
  `kl_fa.monitor` adds an empty one. The briefing trigger, its timer,
  the AIMonitor and the three speakers are kept from every S.
- **S's bank and loading sound** stay (S's `_LS` files beside the archive, S's level-specific sounds in
  the bank): F04 and F05 bring the largest banks, F09 and F08 the smallest.
- **Everything of S that no id space covers** is S's: the .xml UI members, .sup, .zgf, .hti, surface
  table (cleared of S's map effects).
- Not looked at: whether the systems subtrees differ in CONTENT between hosts. By count they nearly
  agree: kl_graft picks 141 subtrees / 9,144 nodes from F04, F05, F07, 140 / 9,143 from F06 and F08,
  142 / 9,149 from F09.

### 3.3 Which S for which map

| map | suggestion | why |
|---|---|---|
| M01_FA_A | F07 (as now) | ran live; map names `Civilian Female Generic Mercenary_04 Police_USA Van` |
| M02_FA_A | F07 or F08 | same six sets as M03; under F08 Police is native |
| M03_FA_A | F07 (as now); F08 if the bank size ever bites | F08: no donor set, 4,800 / 4,641 (under the stock maxima), 287 MB |
| M06_FA_A | **F08** (or F06) - but **F07 for the FIRST live run** (section 10: the only S that has run under a Dead Men map) | helicopter level like the map; verified 0 problems under F06, F07 and F08; F08 gives the smallest bank (4,680 / 4,520, below the stock maxima) and archive (278 MB). The map names only `Female_Fighter` and `Mercenary_04` (stand-ins under every S) |
| M09_A / M09_B | F07 (used here) | nothing in the map needs a particular S: no animation set at all comes from the map once the campaign is dropped (".ANM joined: clips +0") |

ASSUMPTION in the M06 suggestion: that a helicopter host is the safer company for a helicopter map. The
offline evidence does not support more than "equal": the kept plumbing is the same shell under every S.
What a live round shows decides.

---------------------------------------------------------------------------------------------------

## 4. Story levels through the graft: M09_A and M09_B alone

### 4.1 What `kl_prpjoin.sides` does with a story level

`python tools/kl_maps.py sides M09_A`. sides() has two answers. Systems = the names in
`kl_prpjoin.SYSTEMS['dm']`, `Heroes!*` and the clone groups of templates in those; **everything else is
'map'**. A story level has no `Heroes!` groups and keeps its game layer under names the FA levels do
not use, so the graft takes all of it:

| | M09_A | M09_B |
|---|---|---|
| counted systems (left out by kl_graft) | 5,693 nodes: `AllLevels/mainsceneincludes.zip` 2,491, `CloneGroup_Effects` 3,199, 3 singles | 2,926: 2,062, 861, 3 singles |
| counted map and really map | `Locations/*` 3,479, `CloneGroup_Locations` 1,129, `Locations/M09_A/M09A_Audio.zip!` 44, `Effects/AllocMany/M09/AllocMany_BigWindow_M09.zip` 13, backdrop 2, clone groups of map templates 555 | `Locations/*` 7,867, `CloneGroup_Locations` 923, `...M09B_Audio.zip!` 44, backdrop 2, clone groups of map templates 2,861 |
| counted map, in fact campaign | `AI_Players!` 517 (88 squads), `Characters!` 196, `Markup!` 99, `CutScenes/*` 64, `Music!` 46, `COOP!` 28, `Covers!` 20, `WindowBlowup!` 14, `Ropes!` 10, `SFX!` 6, `Audiotriggers!` 5, `CutSequence!` 2, 4 singles | `Enemies!` 1,209, `Civilians!` 383, `HeroCovers!` 118, `Mercenaries!` 92, `CutScenes/*` 64, `Music!` 29, `Crowd!` 21 (three ZROOMs), `COOP!` 19, `Traffic!` 19, `CutsceneStuff!` 16, `MapObjectives!` 16, `Audiotriggers!` 11, `Checkpoints!` 7, `Hero!` 6, `Endlevel!` 4, `Jumps!` 2, 7 singles |

Built that way ("as kl_graft takes it" in the table) the level carries the campaign's 79 / 91 soldiers,
cut scenes, music triggers, `EndOfLevelTrigger` and `SceneChanger` (-> `M09B_Main.zip` / `M11A_Main.zip`),
co-op gates, the rappel, 18 `ZFFPlayer` (the campaign's two heroes + S's 16), 945 / about 1,040 extra sounds and
56 / 51 stream clips the merged PC_Def.str lacks. It still builds; verify reports 2 dangling `Explode`
paths in A (`...BulletImpacts.zip\Grenade\FX_Grenade_Smoke_01 / _Default_01`: Dog Days' systems have no
such node). Nobody should install that build.

### 4.2 The campaign pre-pass (`kl_maps.campaign_drop`, option `--campaign`)

A top-level 'map' subtree STAYS when it is
- geometry: `Locations/*`, `CloneGroup_Locations`, a backdrop (`kl_graft.geometry`);
- the level's ambience or an effect template: name starts with `Locations/` or `Effects/`;
- a passive marker: all its controllers are in `PASSIVE = {PlayerCoverCollision, NoCoverBox, LevelBound}`,
  and everything it names is kept or is a script-free box (M09_B's `LevelBound` boxes name
  `...!Warn01` / `Warn02`, plain `ZBoxPrimitive`s: they come along);
- a clone group whose template stays (kl_graft.picks_of already follows the template).
Everything else is dropped by name through `Select(m_drop=...)`: no tool is edited.

| | dropped | kept beyond geometry |
|---|---|---|
| M09_A | 259 subtrees, 953 nodes | `Markup!` 39 (the 14 `...HeroCovers!Statues!PlayerCoverColiStatue#NN` and the other cover / no-cover boxes), `Covers!` 19 |
| M09_B | 256 subtrees, 1,888 nodes | `HeroCovers!` 118, `Enemies!` 17 (the nine `LevelBound` boxes of `010_RetoBldFront`, `020_Street` North / South, `040_Busterminal` with their warn boxes) |

`Crowd!RoomStreet / RoomBus / RoomLobby` (three ZROOMs outside the map tree, re/retomoto.md 1.2) leave
with the pre-pass; kl_graft drops their tree sets from the .oct (15 -> 12 rooms) and verify finds the room
trees, .rmi, .rmc and .sgp consistent.

Result after the pre-pass (`result.json` of each build holds the full lists):
- **0 scene paths that name nothing**, in both parts. The 60 / 78 references from map objects into Dead
  Men's systems that re/retomoto.md 7.3 item 4 feared are either re-pointed by `kl_graft.dm_rename`
  ("Dead Men paths re-pointed: 1") or were clone-group names, which follow their template.
- Particle template names without a template: A 36 (stock M09_A itself has 36: nothing new), B 27 against
  24 in stock M09_B. The three new ones are emitters under `Locations/M09_B/M09B_Locations.zip` naming
  `Impacts_Default_Smoke`, the one Dead Men template Dog Days lacks (kl_graft's notes; M01_FA_A has the
  same three and passes only because verify allows 18). Patch 2 in section 7.
- Stream clips not in the merged PC_Def.str (counted by `kl_snd`, named by `kl_maps`):
  A 6 - `SFX/Ambiences/M09_A/Inside/Ambience_Atrium_M09`, `.../Ambience_Office_M09`,
  `SFX/Ambiences/M09_A/Outside/Ambience_Rooftop_M09`,
  `SFX/Characters/Voice/EmergencyAnnouncement/EmergencyAnnounce_Japanese_Male_01`,
  `SFX/Characters/Voice/GuardsAttackDoor/GuardsBreakDoor_01`, `.../GuardsShoutAndShoot_01`;
  B 9 - `Dialog/M09/Dialogue/M09B_OneLiners/PoliceWarning/PoliceWarning_010..050_JapanesePolice` (5),
  `SFX/Ambiences/100_Bullets/100_Bullets_Tokyo_Street_01`, `SFX/Ambiences/M09_B/Inside/CrowdLobby_01`,
  `.../Lobby_01`, `SFX/Ambiences/M09_B/Outside/Highway_Distance_mono_01`.
  These are the map's ambience beds. `kl_audio.merge`'s filter took Fragile Alliance clips only; the fix
  is there (patch 3) and needs the merged PC_Def.str rebuilt and installed - a job for the live side.
  The 7 music clips of `Music/InHouse/Japan/M09_A/` are not among them: the `Music!*` objects are
  campaign and dropped; music has to come back with the authored FA layer (settings fields 157 / 158).
- Lights (`kl_light`, mode stock): A 70 lights, 3 suns flagged, nothing unknown. **B: 2 environments "in
  no stock form"** - `Environment#01_EDITOR` ('main', 4, True, False, 0, 0) and `Environment_Character`
  ('char', 4, 1, 1, False, True) - and 52 dead `ZLIGHT[2]` references removed on one light. kl_light.check
  does not fail the build on them; what they do on screen is for the lighting work (re/lighting.md).
- .ANM: nothing is taken from Dead Men ("clips +0") - once the campaign is gone the map names no
  animation set S lacks. re/retomoto.md 7.3 item 8 is void for the map as grafted.
- `.hrd`: carried in a single-part build (all rigid bodies come from one level: A 8, B 28).
- FDX: A has a block (hanging objects of the tower), B none.
- Navigation: A 146,424 bytes, B 456,964 bytes after `kl_pf4.convert`. **re/retomoto.md section 5
  ("A's navigation mesh is REFUSED") is out of date**: kl_pf4 converts array 7 as waypoint links now and
  drops the kinds no Dog Days level has (10 of A's 15).
- What is left in verify is the FA layer, exactly as it should be for a level that has none: no
  `OnlineFragileAllianceSettings` (CRASH in a real round), no `IsMultiplayerLevel` define, no exit
  trigger, no START / AFTER_DEATH spawn points, no gameplay triggers, no loot, no squads.

### 4.3 Where the player stands (`--heroes`)

A story level has no `Heroes!` groups, so S's sixteen would stay at F07's coordinates, somewhere in the
void. `kl_maps.py --heroes` presents two of the campaign's checkpoint markers to kl_graft as
`Heroes!Hero_01` / `Hero_02` (`HERO_AT`; the marker node is rewritten as a plain ZGROUP with its own
rotation and position, kl_graft then does what it does for an FA map's Heroes! groups):

| level | marker | position |
|---|---|---|
| M09_A | `Markup!CP_02_PosP1`, `CP_02_PosP2` | (4164, 20994, -261), (4168, 20994, 78): in the boardroom, 17 m inside the main window |
| M09_B | `Checkpoints!CP_01_PosP1`, `CP_01_PosP2` | (3076, 162, -6354), (3100, 162, -6594): the lobby floor just inside the front entrance |

"Heroes! groups placed where M09_A has them: 2" in the log. ASSUMPTION: a direct boot puts the player
at Hero_01 (it did for the FA maps); the other fourteen groups stay at F07's coordinates and matter
once more than two players exist. For a real round the spawn points decide, not these groups.

### 4.4 What a campaign level needs before a live test

1. The pre-pass and `--heroes` (done here, in `kl_maps.py`).
2. Nothing else for a DIRECT BOOT of a single part, as far as offline checks go: the build is internally
   consistent. Expected on screen: the map without enemies. The paired states of re/retomoto.md 4.3
   (window pre / post, chairs, the boardroom door, elevator doors) keep their load-time state, because the
   scripts that switch them are gone. Which state that is: NOT ESTABLISHED (stored in the objects).
3. For a round: the whole FA layer (section 6, item 1).

---------------------------------------------------------------------------------------------------

## 5. Retomoto Tower: both parts in one level

### 5.1 How it was built

`python tools/kl_maps.py chain <out> F07 M09_B M09_A --heroes`

`kl_graft.build` takes one S and one M. The chain calls it twice without editing it:
1. F07 + M09_B (pre-pass) -> a level named `R09` in `<out>/chain/`, archive and the files beside it.
2. `R09` as S + M09_A (pre-pass, `--heroes`) -> the slot's archive.
For step 2 `kl_maps.redirect()` makes the stock-file lookups (`kl_prpjoin.level_zip`,
`kl_snd.level_zip / beside / ls_files`, `kl_graft.stock_beside`) find `R09`, and makes
`kl_prpjoin.sides` call every subtree of `R09` 'systems'. That is the whole trick: S is the base of
every id space and nothing of S is renumbered or removed, so the first map rides through the second
graft like F07's systems do. Seen in the log of step 2: "R09 systems (359 subtrees, 19111 nodes) + M09_A
map (127 subtrees, 5054 nodes)", ".rmi: 22 boxes of R09 + 19 of M09_A", ".oct: 23 room sets, 2631 + 932
records", "255 REF cells in gates / lists", "KEYS blocks moved by 0x3762f0".

What verify checks on the result and finds in order: .gms / .buf round trip and tables, 24,165 entities =
.prp nodes, every model root, 34,253 reachable .prm chunks, textures, materials, .oct records, 23 room
tree sets in room order with every item under its room, .rmi / .rmc boxes naming rooms, 360 gate / list
REF cells, KEYS offsets, .HVK placements, .sgd leaves, .sgp rooms, surface table, FDX records, every sound
reference an object of the merged bank, lights, 0 dangling scene paths, no top-level name twice.

### 5.2 What each module needed (answer to "what must change to take two maps")

| module | two maps today | note |
|---|---|---|
| `kl_scene` (`remove`, `graft`) | works, called twice | each graft appends M's .buf head at a constant shift; REF ids of the grafted part are new, S's stay. Heap budget = sum of three (F07 403,200 + B 500,928 + A 284,136; ASSUMPTION as before), dynamic list = S's |
| `kl_prpjoin.join` / `picks_of` | works | a top-level name both bring is taken once, from S (section 5.4) |
| `kl_prmgraph.append`, `kl_texmat.merge_*` | works | 17,195 + 10,318 chunks appended to F07's 35,101; +715 and +238 textures, +521 and +176 materials: the second part shares many with the first |
| `kl_octree` | works | root set joined twice (`join_room_trees`), records appended twice |
| `kl_hvk.join` | works | step 2: A's file is the base, R09's static part (B's collision + F07's) is "one more part behind the maps", padded to 510. The ASSUMPTION in `kl_hvk.join` (a list code addresses the placements of its own 510 only) now carries real weight: three static parts. Passing both maps in one call, `join([(A, refs), (B, refs)], (S, refs))`, is what the function was written for and avoids the detour |
| `kl_members.sgd_join`, `Sgp.join` | works | both sides' octrees / portals, called twice |
| `kl_members.fdx_join` | takes a list, but build() passes one part | step 2 drops S's block (`A.fdx = None`) and writes M's. With A second its block survives (B has none). In the other order A's is LOST (measured: `fdx: false`). Patch 4 |
| `kl_members.hrd_join` | **refuses** | "the rigid bodies do not all come from one level": A has 8 `ZHavokRigidBody`, B 28 -> no `.hrd` member (30 members instead of 31). Needs the record order of the .hrd decoded (kl_members' own note) |
| navigation mesh | **`A.nav = B.nav`: the second map's replaces the first's** | solved outside: `kl_maps.nav_join`, section 5.5 |
| scene block | last M's | `CameraFar` A 240,000 / B 50,000, fog begin / full A 0.4 / 0.95, B 2.0 / 3.0. One level has one of each: with A second the street is drawn with the tower's far plane and fog. A decision, not a bug |
| `kl_snd.graft_audio` | works, called twice | the second call's base is the bank of step 1 and its `_LS.SND` |
| `kl_anmjoin` | works | nothing added in either step |
| `kl_light.normalise` | works | runs on each map's own nodes in its step |
| `kl_fa` | works | `host_keep` finds F07's plumbing in step 1; in step 2 everything of R09 is systems |
| `verify` | one false count | "39 particle template names (stock M09_A: 36)": the baseline is the second map's alone; the 3 extra are B's `Impacts_Default_Smoke` |

### 5.3 The order

| | F07 + B, then + A (used) | F07 + A, then + B |
|---|---|---|
| FDX block | A's, kept | lost |
| scene block | A's (far 240,000) | B's (far 50,000: the skyline seen from the tower would be cut at 500 m) |
| Heroes! (`--heroes`) | the boardroom - the owner's start | the lobby |
| navigation (with `nav_join`) | both | both |
| counts | equal | equal |

So: the street first, the tower second.

### 5.4 Name clashes

`python tools/kl_maps.py clash M09_A M09_B`: after the pre-pass A keeps 145 top-level subtrees, B 255;
**18 names are in both**:
- `M09_Backdrop_A_00` (2 entities in each). The chain keeps the first map's (B's) and drops A's. Stock
  Dog Days story levels L03 and L10 have two `ZBackdrop`s each, F05 and F07 none, so two are legal; to
  keep both, one has to be renamed in the .gms and the .prp before the graft (no path names it).
  Whether the tower wants its own backdrop is a look question: A's is the city seen from 200 m up.
- 17 clone groups `CloneGroup_Effects/AllocMany/M09/AllocMany_GlassRailing_M09.zip/<x>` (9 to 22 entities,
  identical sizes in both parts): the same effect file is instanced by a template in each part's
  `Locations`. The chain keeps B's groups; A's templates then find a group of that name. Stock Dead Men
  levels already have several templates on one clone group (M02_FA_A 12 groups, M06_FA_A 13, M03_FA_A 1 -
  the car explosion with 8 templates, which ran live under F07), so this is a form the engine knows.
  ASSUMPTION: that the pool sizes of one group are enough for the templates of both parts.
No two rooms share a name (`M09_A_*` / `M09_B_*`); no other name clashes.

### 5.5 Two navigation meshes in one (`kl_maps.nav_join`, `python tools/kl_maps.py navtest`)

New facts about the PF4 mesh, each tested on all 21 stock Dog Days meshes (`nav_facts`, 0 exceptions):

| rule | holds |
|---|---:|
| tree 0: a child node lies in its area's node range (area[9] .. next area's [9]) | 108,091 of 108,091 |
| tree 0: a leaf c <= -2 is polygon -2 - c, a polygon of that area (-1 = nothing) | 59,873 of 59,873 |
| area[6] = sum of area[1] of the areas before; the sums add up to array 6 (vertices) | 3,163 of 3,163; 21 of 21 |
| a polygon's edges name vertices of its area | 27,384 of 27,384 |
| array 10 is a permutation inside each area's own waypoint range | 3,163 of 3,163 |
| tree 1: -1 - c of the leaves reaches the last record of array 2 | 21 of 21 |

So **tree 0 is one BSP per area** (kl_pf4's notes call it "tree over the polygons" with -1 - c leaves:
the leaf code is -2 - c with -1 for nothing, as in array 9), area[1] / [6] are the vertex count and first
vertex, and **no array spans two areas**. A join is then pure concatenation: the second mesh's areas
behind the first's, every absolute index moved by the first mesh's counts (tree-0 nodes and polygon
leaves, tree-1 nodes and array-2 leaves, polygon area / first edge / waypoints-before / tree-1 node, area
starts [5] [6] [7] [9] [10] [11], waypoint link range and polygon, link target area, edge neighbour and
vertex, array 10). `nav_join` does that and runs `kl_pf4.check` and `nav_facts` on the result.
Trial joins F07 + F09, F09 + F07, F04 + F04 pass; the Retomoto mesh is B 456,964 + A 146,424 = 603,332
bytes (56-byte header counted once).

EXPERIMENT - not loaded by the game yet. ASSUMPTIONS: the game finds the area of a point from the area
records alone (their bounding boxes; arrays 8, 11, 12 are empty and nothing else could hold a structure
over the areas), and the order of areas has no meaning beyond the running sums. No link joins the two
parts, so an AI never walks from the tower to the street - which fits a level whose parts are 190 m apart.

### 5.6 World positions and the join between the parts

Both parts stay where the campaign has them (re/retomoto.md section 2): the tower interior at
x -2800..6000, y 19600..25900, z -2200..2000, the lobby and street at y -1000..1250 around the tower shell
(x 2550..9570, z -8830..-4150). Nothing was moved, so every baked file is used as baked. On the joined
level verify finds 22 rooms, every .rmi / .rmc box naming a room and every gate leading to a room; that
no box of one part overlaps a box of the other rests on re/retomoto.md 2.4 (the tower's bounds start at
y 17,840, the highest bound of B under it ends at y 10,373) and was not re-measured here.
Hero start (`--heroes`): (4164, 20994, -261), the boardroom.

Getting a player from y 19,600 to y 560 is the open design point. What the exe and the stock levels
offer (schema from `re/kl2.json`, use from the stock .prp files):

| means | what is known | state |
|---|---|---|
| `TeleportList` (`CTelePortList`, on a ZLIST; fields: one sound reference, one string) | registered in both exes, used by no stock level of either game | unproven; the fields do not even look like a list of places |
| `Elevator` (`ZElevator`, on ZGEOM: two reference lists, a sound, a string) | Dead Men: one use, M09_A's atrium lift; Dog Days: no use | converts through the schema; moves a car between floors of ONE shaft, not between two places |
| `OnlineSpawnpointTrigger` (bool, spawn type, team) | every stock FA level, e.g. F07 `FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B / _020_C / _030_D` = (1, `eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1 / 2 / 3`, `eMerc`) | switches which spawn set a TEAM uses (the team modes). Moves where people RESPAWN, not the living |
| KLHook writes the player position | the hook exists (dinput8 proxy) | works without any level data; not a level feature, not for online |
| lower the tower onto the lobby (re/retomoto.md option 3) | A moved by about (3298, -18300, -7214) | every baked file of A re-made; the atrium end sticks through B's entrance facade |

PROPOSAL (the owner asked me to design the join; nothing of it is built):
1. Round start in the boardroom at the blown window; tower loot = statues, then the boardroom.
2. The way down is the campaign's own: escape elevator `SI0101_JPN_Elevator_Int_A_03` at (2974, 19600, 909)
   in `M09_A_Ins_Elevators_101`, arriving in the lobby car `..._Int_A_00` at (6272, 560, -6305):
   **B - A = (3298, -19040, -7214)**, same model, same rotation, so a player keeps his place in the car.
3. First try, cheapest: a trigger box in the tower car that moves whoever stands in it by that offset,
   behind a fade to black. The mover is the missing piece: test `TeleportList` live on
   a two-box scratch level first (one evening's test, decides the whole design); if it does nothing, do
   the move in KLHook for single-player and Arcade, and keep the tower-only and street-only halves as two
   maps for online.
4. Police who die and respawn follow the heisters through `OnlineSpawnpointTrigger`-style spawn sets:
   AFTER_DEATH points in the tower while loot is left there, in the street afterwards.
5. Part 2 as the owner wrote it: lobby (start (3076, 162, -6354) is 5 m inside the door) -> front
   entrance at x 2600 -> road (x -5700..-300) -> van. Van places: re/retomoto.md 3.4.

---------------------------------------------------------------------------------------------------

## 6. What is missing for Retomoto, in order

1. **The Fragile Alliance layer** (authoring; `kl_fa.check` lists it): one `OnlineFragileAllianceSettings`
   (without it a real round crashes: 0x500990 / 0x728ba3), `ZSetZDefine IsMultiplayerLevel`, 8 START +
   AFTER_DEATH (+ TRAITOR) spawn points, `OnlineGamePlayTrigger` ENTERS_BANK / EXITS_BANK / BOARDS,
   loot (`OnlineMoneyCtrl` NORMAL / CONTAINER on the 15 samurai cases and in the boardroom), an exit
   trigger + escape vehicle + monitor lists, police squads (`ZSquadScript`), `PointOfInterest`, level
   bounds for the tower (A has none; B's nine are kept). A direct boot needs none of this.
2. **A mover between the parts** (section 5.6): unproven in every form but the hook.
3. **Live proof of the chain itself**: three static Havok parts in one .HVK, `nav_join`, 17 shared clone
   groups, no `.hrd`. Suggested first runs, each a direct boot: F07 + M09_A pre-pass `--heroes` (single
   part, nothing experimental); F07 + M09_B pre-pass `--heroes`; then the chain.
4. **`.hrd` for two maps** (36 rigid bodies, none shipped now). What the game does with rigid bodies and
   no .hrd member: NOT ESTABLISHED (kl_graft already ships none when a map's bodies are only partly
   carried; I found no live run of such a build in the log).
5. **Stream clips**: 6 + 9 ambience beds and police-warning lines (section 4.2), plus the 7 music clips
   and the window explosion (`M09_Explosion_Window_Office_01`, re/retomoto.md 6) for the authored layer.
6. **The start**: the window in its blown state, `Chairs_Post`, the broken door, the explosion sound and
   particles at round start (re/retomoto.md 3.1, 4.3). The pre-pass drops `WindowBlowup!*` with the rest
   of the campaign; `BombWindow03` + its particle group are the two objects to bring back by hand.
7. **One backdrop or two**, one far plane and fog for both parts (5.2, 5.4): decisions.
8. Lighting: B's two environments in no stock form (4.2).

---------------------------------------------------------------------------------------------------

## 7. Patches for the tools I do not own, most valuable first

Nothing below is applied. Line numbers are of the COMMITTED `tools/kl_graft.py` (a07de47, 1,197 lines);
the working copy gained `broken_groups` / `stream_groups` (92 lines, the live agent's) while this was
written - go by the quoted code, not the number.

**1. kl_graft.build - a story level's campaign must not come along.** Either call
`kl_maps.campaign_drop(m_name)[0]` and add it to `sel.m_drop`, or move `campaign_drop` + `PASSIVE` into
`kl_prpjoin` as a third side. In `build()`, after `sel = sel or Select()` (line 607):

    if M.dm and not any(n.startswith('Heroes!') for n in M.prp.names):      # a story level
        import kl_maps
        sel = Select(sel.geometry, sel.m_add, tuple(sel.m_drop) + tuple(kl_maps.campaign_drop(m_name)[0]), sel.s_keep, sel.s_drop)

(`M.prp.names` has `Heroes!*` in every FA level of both games and in no story level looked at: M09_A,
M09_B.) Without it `python kl_graft.py build F07 M09_A` builds a level that changes scene to M09_B.

**2. kl_graft.verify - the particle-template baseline (lines 971..976).** `Impacts_Default_Smoke` is the
known Dead Men template without a Dog Days namesake; it only passes today where the count stays under
18. Replace

    base_names = max(len(J.dangling(M.prp)[1]), 18)

by

    lost = {s.lower() for _k, _h, _f, s in J.dangling(M.prp)[1]} | ({'impacts_default_smoke'} if M.dm else set())
    names = [n for n in names if n[3].lower() not in lost]      # what M lacked in its own game, + Dead Men's smoke
    base_names = 18

(every build that passes today still passes; "27 names (stock M09_B: 24)" goes away; a NEW missing
template still fails. In a chain the first map's own stock names are counted against the second map's
baseline - "39 (stock M09_A: 36)" in one order, "39 (stock M09_B: 24)" in the other - which only a
build() that knows both maps can count right). Better still, and not offline work: give the three emitters a Dog Days template.

**3. kl_audio.merge - the clips a map names.** `want=lambda n: any(f in n for f in FA_FILTER)` takes
Fragile Alliance clips only. Add the 15 names of section 4.2 (and, for the authored layer,
`Music/InHouse/Japan/M09_A/` and `SFX/Explosions/Bomb/M09_Explosion_Window_Office/`) to `FA_FILTER`, or
better pass the set `kl_maps` writes to `result.json['stream_clips_missing']`. Then rebuild and install
PC_Def.str (live side).

**4. kl_graft.build - two maps.** The chain works without edits; what build() itself loses in step 2:
   - FDX (lines 859..865): keep S's records when nothing of S was removed. Replace `A.fdx = None` /
     `if B.fdx is not None:` / `block = MB.fdx_join([(M['.buf'], B.fdx, cmap)])` by

         s_fdx = A.fdx
         parts = [(M['.buf'], B.fdx if B.fdx is not None else -1, cmap)]
         if s_fdx is not None and len(s_kept) == len(S.ents):               # a chained S: its lamps are still there
             parts.insert(0, (S['.buf'], s_fdx, {i: i for i in range(len(prm_s.chunks))}))
         A.fdx = None
         block = MB.fdx_join(parts)
         if block: ...                                                       # as now

     (`s_kept` is the set of S's entities after the removals, line 626.)
   - navigation (line 660): `A.nav = B.nav` ->
     `A.nav = kl_maps.nav_join(A.nav, B.nav) if len(s_kept) == len(S.ents) and A.nav is not None and B.nav is not None else B.nav`
     (kl_maps does this from outside today by handing build() an M whose mesh is already the join).
   - `.hrd` (line 886): needs `kl_members.hrd_join` to merge two files - not possible until the record
     order is known.
   - `Level.__init__` (line 279): a `path` argument and an `all_systems` flag would replace
     `kl_maps.redirect()` (five monkey-patched lookups).
   A cleaner `build(s_name, [m1, m2])` would also call `kl_hvk.join` and `Sgp.join` once with both maps.

**5. kl_prpjoin.sides / picks_of - same top-level name in two maps.** For two backdrops: rename the
second map's `M09_Backdrop_A_00` (entity name in the scene and `prp.names`) before `picks_of`; nothing
names it by path. Not needed if one backdrop is the decision.

**6. re/retomoto.md** (not mine): section 0 item 6 and section 5 ("REFUSED: array 7") and 7.3 item 1 are
out of date; 7.3 item 4 (dangling references) and item 8 (.ANM) do not occur after the pre-pass.
**CLAUDE.md**: "M02 = streets" -> M02_FA_A is "Late Night Opening", the jewel shop in the mall; M06_FA_A is
"A Walk in the Park", the Japanese Gardens with a helicopter escape; M01_FA_A is "Hot Coffee".

**7. kl_pf4 docstring**: tree 0 is per area with leaf code -2 - c (-1 nothing); area[1] / [6] = vertex
count / first vertex; array 10 is per area (section 5.5). `kl_pf4.check` could test these six rules too
(`kl_maps.nav_facts` has them).

---------------------------------------------------------------------------------------------------

## 8. What `kl_maps.py` does from outside kl_graft (so nobody is surprised)

- `kl_graft.out_dir` is replaced during a build: the archive goes to `<out>/<S>+<M>/`, never to
  `<work>/build/install`. By default the archive and the files beside it are deleted after measuring
  (`--keep` keeps them); `result.json` and `log.txt` stay.
- `kl_graft.verify` is wrapped to record EVERY dangling path and the new template names (verify itself
  shows ten); `kl_snd.merge` is wrapped to name the stream clips it counts as missing (a reconstruction
  from the carried waves; the count matched kl_snd's in both M09 parts and is not used when kl_snd
  counts 0).
- `kl_graft.DeadMen` is subclassed for `--heroes` and for the chain's navigation mesh.
- `redirect()` (chain only) patches five lookups and `kl_prpjoin.sides` for the name `R09`.
- `--flat <class>` adds one entry to `kl_gms.RETYPE` for the length of the build (third pass).
All of it is undone when the build returns; nothing is written outside `<out>`, with two exceptions
added in the third pass: `stock_use()` caches a census of the stock Dog Days levels as
`kl_maps_stock_use.json` in the system temp folder, and `kl_maps.py stage <folder>` - a command for
the live side, never run by the offline work - copies a kept build into `<work>/build/install`.

---------------------------------------------------------------------------------------------------

## 9. Before the first live run of M02_FA_A and M06_FA_A (third pass, 2026-10-09, agent f-maps)

Offline only, as everything in this file: nothing was installed, the game was not started. What is
new against sections 0 - 8: `tools/kl_graft.py` as committed in 6238e30 (it now calls
`kl_light.fit_shaders` and `stream_groups` and runs `kl_fa`), three new commands of `kl_maps.py`
(`first`, `preflight`, `deliver`) and the pre-pass `--flat`, and the reading of kl2.exe behind each
prediction. "read" = read off the disassembly at the address given.

### 9.1 Every build again, with the current kl_graft

| build | problems | against the table of section 1 |
|---|---:|---|
| F07 + M02_FA_A | 0 | same row; new notes: 11 materials fitted, **6 without any compiled shader** (not drawn) |
| F07 + M02_FA_A `--flat ZEnvSampler` | 0 | same counts; the 7 samplers are ZSTDOBJ |
| F08 + M06_FA_A (section 3.3's S) | 0 | same row; 13 materials fitted, 6 without a shader |
| F07 + M06_FA_A | 0 | same row |
| F07 + M09_A, pre-pass, `--heroes` | 11 | same 11 (FA layer + 6 stream clips); 10 materials fitted, 0 left |
| F07 + M09_B, pre-pass, `--heroes` | 12 | same 12 |
| chain F07 + M09_B + M09_A | 12 | same 12; 24,165 entities, 22 rooms, 2,141 textures, 1,399 materials (was 1,397), 4,801 / 4,635, 314 MB, nav 603,332 bytes, FDX kept |

Materials without a compiled shader (kl_graft's notes; `fit_shaders` found no permutation):
M02: `Plastic_Basic_01a_LampMexi_M02_FA`; both maps: `Effect_Glow_Turkis_Round_01a_M06`,
`Glow_Flare_01a_M07`, `Glow_Headlights_01b_M07`, `Glow_Beam_01a_M07`, `_Basic/Colour_White_Glow`;
M06: `Paper_Rice_Lantern_01a_JPN` (the paper lanterns will be invisible - and they are what the
garden is lit by at night). Not a crash: the bank ran live with 35 such materials.

The offline checks that exist, all run on the kept builds by `python tools/kl_maps.py preflight <folder>`:

| check | M02 (F07, flat) | M06 (F07) | M06 (F08) |
|---|---|---|---|
| `kl_graft.verify` | 0 problems | 0 | 0 |
| `kl_fa.check` | 0 CRASH, 0 BROKEN, 4 DEGRADED, 2 NOTE | 0 / 0 / 3 / 2 | 0 / 0 / 3 / 2 |
| `kl_light.check` on the map's nodes | nothing; 3 environments "in no stock form" (`AmbientDirectional` x2, `AmbientOut`: ('main', 3, True, True, 3, 3)) - a matter of look | nothing, 0 unknown | nothing |
| `kl_light.missing_shaders` on the written .MAT / .fxc | 6 of 1,076 | 6 of 995 | 6 of 914 |
| `kl_snd.verify` (inside `graft_audio`) + `broken_groups` on the written .WHD | no problem; 128 torn records left, none named by a wave | 123, none named | 123, none named |
| `kl_anmjoin.verify` | no problem; `Van`, `Police_USA` converted from Dead Men; stand-ins Female <- Civilian, Police <- F03's, Army <- Swat_02 | stand-ins `Female_Fighter` <- F03's Thug, `Mercenary_04` <- Lynch_NPC; 103 clips added | the same |
| `kl_pf4.check` on the written mesh | 55 areas, 908 polygons, 106 waypoints, 0 links | 14 areas, 954 polygons, 18 waypoints, 0 links | the same |

### 9.2 The crashes the diner and the bank hit, looked for here

| crash (run) | what it was | cheap offline check (in `preflight`) | M02 | M06 |
|---|---|---|---|---|
| jump into ZFFGameData+0x3e3c at 99 % (B-2) | an event that deletes itself after it was entered in the save-state table: `OnlineSpeakTrigger` without its line | `kl_graft.mute_speech` on the written .prp / .SND; and the other self-deleting inits: `OnlineMoneyContainer` (kl2 0x837000: first reference must resolve), `PhysicsLinkage` (0x80bd20 -> 0x78cd90: first reference must resolve to a ZLNKOBJ, class id [0x15355a0]) | 2 triggers cut by the build, 0 left; 26 containers, 26 resolve; no linkage | no trigger cut; no container; **8 linkages (new on a Dead Men map), all 8 name a ZLNKOBJ + a bone** (the paper lanterns; stock L01's lamps have the same form) |
| 0x81e714, key index outside the .buf (B-3) | a KEYS chunk at the end of a long raw block, offsets not shifted | every 'SYEK' tag in every raw block is found by `keys_tracks`, every offset lies in the head; other four-letter tags in raw blocks | 112 chunks, all found; no other tag | 93, all found; no other tag |
| 0x58a7fc (B1), assert 0x531708 (M03) | a vehicle controller on a car that RETYPE had made a ZSTDOBJ | controllers whose registered owner is an entity class the node is not; nodes retyped | `GatePath` (owner ZGROUP) on a ZBoxPrimitive x2 - init read (0x449120: asks the PARENT for `GateGroup`, never uses its node as a group); nothing retyped but ZIngameMapGroup in Dead Men's systems | none |
| divide fault 0x44668b on the sound thread (RN5) | an interleaved stream group torn apart | `broken_groups` on the written .WHD against the waves of the written .SND | 0 named | 0 named |

A fifth trap of the same family was read for this pass and is NOT one: `ZHeliFlyBehaviourRout`
init (slot 14, 0x815aa0), listed in re/crash_gamedata.md section 4 as "deletes itself when: not
read". The `[vtbl+0x78]` call in it is on a child iterator, not on itself. It looks for the ZHeli
under its group and that heli's `HeliScript` controller and returns quietly when there is none.
`ZOnlineSpeakPlayer` init (0x8cb6e0, M06 has one) frees its buffer when a line is missing and
stays alive: no self-delete either.

### 9.3 What these maps have that the diner and the bank do not (`python tools/kl_maps.py first <map>`)

Map side only, as kl_graft takes it. "stock" = objects in the 21 stock Dog Days levels.

**M02_FA_A**

| class / controller | n | stock Dog Days | Dog Days init | what it dereferences (read) | risk |
|---|---:|---|---|---|---|
| `ZEnvSampler` (entity) | 7, slots 0,0,0,1,2,2,3 | **0 - no level** | object: bounding box only (re/cars.md). But 0x718f20 gives every ZEnvSampler a `ZRenderEntryEnvSamplerD3D` (ctor 0x7ee4b0, vtable 0xb99f58) | ctor: slot = [sampler+0x14], entered in a table of 4 x 16 at 0x138c718 (counts 0x138c844; the count is tested against 16, **the slot is not tested**); render function 0x61b5a0 (frame of 0x1e4b4 bytes): each frame picks the nearest sampler per slot and renders through it | **highest of M02**: a renderer path no stock level ever enters, and the launch is `-dx10`. Slots are 0..3 here, in range. `--flat ZEnvSampler` takes the path away |
| `SoundSpline` on ZSNDOBJ | 2 | **0 - no level** | slot 15 0x61e690, slot 16 0x544e60, update slot 25 0x48a240 | the node's sound instance (0x6c6ab0 -> 0x659370 by handle) **without a null test** at 0x61e733 / 0x544ea1; the spline reference is tested three times (empty, unresolved, wrong class all skipped); the update does not touch the reference | medium: code alive in both exes, never run by a Dog Days level. Check: the node has a sound of the merged bank (2 of 2) |
| `PatrolBehaviourRout` on ZGROUP | 3 | 17 (F03 F04 L06 L08) | slot 13 0x4aff50, slot 14 0x536e00 | slot 13: the PARENT's `ZSquadScript` / `ZMercSquad` / `ZFusionSquad` / `ZProxySquad` controller -> squad at +0x38; slot 14: when the start flag (+0x50, field [2]) is set it calls 0x59a0e0, which calls through the squad untested | low: flag = 1 in all five Dead Men uses, 0 in the FA levels but 1 in stock L06; every one hangs under a `ZSquadScript` (check `behaviour`). Pairing is an ASSUMPTION (9.4) |
| `GatePath` on ZBoxPrimitive, `GateGroup` | 2, 1 | 1,242 / 700 | 0x449120 / none | parent's `GateGroup` controller (may be 0) | low |

**M06_FA_A**

| class / controller | n | stock Dog Days | Dog Days init | what it dereferences (read) | risk |
|---|---:|---|---|---|---|
| `SoundSpline` on ZSNDOBJ | 4 (one with an EMPTY spline list: `...highway_SoundSpline_03!Highway_03`) | **0** | as above | as above; the empty list is skipped at 0x544ee8 | medium |
| `SoundVolumetricRandom` on ZSNDOBJ | 4 (water drips) | **0** | slot 13 0x651260, update slot 25 0x63de00 | init: the node's box (0x857110) into +0x30 / +0x54; update tests the sound instance for 0 (0x63de25) | low / medium: never run by a Dog Days level |
| `ZHeli` (entity) | 2 (`EscapeSetup!EscapeChopper\Escape_Chopper\V_Coli_Shot_01`, `BossChopper!...\Jpn_Boss_Chopper\V_Coli_Shot_01`) | 21 (F02 F03 F06 F08 L04 L08 L09 L10) | slots 16 0x8269d0, 17 0x802660, 18 0x57ae30 - not read | - | medium: the subtree has the same shape as stock F08's (group with `OnlineEscHavokCar` + `OnlineEscVehicleController` + `VehicleEffects`, ZHeli child with `HeliWeapon` + `HeliScriptRout`, sibling groups with `HeliFlyBehaviourRout`, a `HeliNetSync` box), but the DATA is Dead Men's: 10 of ZHeli's 24 own fields are Dog Days defaults (9.4), and its model, bones and .HVK shapes are Dead Men's |
| `HeliFlyBehaviourRout` x4, `HeliScriptRout` x2, `HeliNetSync` x2, `HeliWeapon` x1, `MsgForward` x3 | | 165 / 19 / 21 / 17 / 46 | 0x815aa0 (9.2), 0x8c51f0, 0x8988d0, 0x5f5340 (not read), 0x63ef80 | HeliScriptRout: allocates 0xa0 and registers with [[0xdd265c]+0x15ac]; HeliNetSync: only acts when its node IS a ZHeli (class id [0x168ce48]); here it sits on a ZBoxPrimitive, as one of stock F08's does: returns; MsgForward: parent's object | low |
| `PhysicsLinkage` on ZCloth / ZSTDOBJ | 8 | 274 (story levels only) | slot 14 0x80bd20 | 9.2: deletes itself unless its first reference is a ZLNKOBJ | low after the check |
| `ZFFItemWeapon` + `Action` | 4 (`BossChopper!Items!Minime_01`, `RPG7_01` ...) | 101 (story levels only) | 0x4c7560 / 0x44b700 | Action: its node and the node's parent flags | low / medium: weapons lying in an FA map do not occur in stock FA levels; their templates are `dm_rename` guesses (`Mg_Minimi_SPW_01` -> `Mg_Minimi_SPW_L10_Heli`, `Smg_MP5-A3_01` -> `SMG_UMP_SBR`, `Rifle_SG552_01` -> `Rifle_Type95_L09_NPC`) |
| `SquadModifierBehaviour`, `PatrolBehaviourRout` x2, `OnlineSpeakPlayer` | 1, 2, 1 | 1,200 / 17 / 6 | 0x681210, 0x536e00, 0x8cb6e0 | see M02 / 9.2 | low |
| `ShowPipCam` | 1 | not registered by kl2.exe | - | the converter drops it | none (the picture-in-picture camera of the incoming chopper is lost) |

Also only in these maps, from the conversion logs: M02's .prm has one `prop2` record (stripped by
kl_prm; none in M01 / M03 / M06); M06 has 145 scatter objects (each becomes an empty mesh, 436 chunks
added; M01 had 4 and ran) - the garden's grass and bushes are not drawn.

### 9.4 Pairings by assumption that these maps use

`Converter.assumed` holds 26 class levels today (re/pairings.md settled the rest). Of those, on the
map side of M02 / M06 and of neither M01 nor M03:

| class level | objects | the pairing | values that matter |
|---|---|---|---|
| `ZPatrolBehaviourRout` | M02 3, M06 2 | Dead Men `e path, list, b, e moveset, list, b` -> Dog Days `e, list, b, e, b*, f*, b*, f*, list, b, b*` (* = new, Dog Days' usual value: 1, 50.0, 1, 200.0, 0) | [2] b = 1 (start flag, read at 0x536e90); the two lists keep their order. The second Dead Men list is empty in all five |
| `ZHeli` | M06 2 | the 14 Dead Men fields in place, 10 new ones behind them (an I, six f, two b, `EHeliTeam`) = Dog Days' usual values | own field [7] (a sound reference, type handler 70) is 0 in every stock ZHeli read (18 of 18 in F02 F03 F04 F06 F08 L04 L08 L09); here it names a sound, rewritten into the merged bank like any other |
| `ZSquadModifierBehaviour` | M06 1 | twelve enums, each of its own type, so the pairing is by type | `eAM_Deactivate`, everything else `NotSet` |

Classes with an assumed pairing that the proven maps also have, with values those maps never had
(ZHavokShatter's floats and its three .buf-like integers [9] [11], ZParticleTemplate [25], ZTrafficFlow
[3], ZDefendBehaviourRout `eDMS_Sprint`): same code paths as in the runs that passed.
`preflight` prints, for the first-timer classes, every bool / enum / flag value that no stock Dog Days
level stores in that field: none in either map.

### 9.5 Shapes

| | M01 (ran) | M03 (ran) | M02 | M06 |
|---|---|---|---|---|
| rooms of the map / gates / neighbour lists | 11 / 48 / - | 19 / 73 / - | 31 / 78 (most in one room 12) / 67 | 6 / 8 / 8 |
| .rmi / .rmc boxes | 20 / 11 | 60 / 18 | 44 / 30 | 10 / 6 |
| .oct room sets, map records | 13, 818 | 21, 2,198 | 33, 2,004 | 8, 694 |
| REF cells in gates / lists | 231 | 688 | 732 | 124 (one id names no entity in stock M06: sent to a free id, as before) |
| .buf head of the map | 0x40b0 | 0x4cb0 | 0x4540 | 0x1e20 |
| fields that look like .buf offsets (scan of every integer field: 4-aligned, inside the head, distinct) | ZROOM[9], [10] | the same | the same, no other | ZROOM[10] only, no other |
| navigation mesh (Dog Days form) | 101,492 B | 186,672 B | 238,188 B, 0 links | 258,640 B, 0 links (the largest of the four) |
| Dead Men links dropped by kind | - | 1 (kind 6) | none | none |
| FDX block | yes | no | 1 record, 5 instances | 2 records, 6 instances (the lanterns `PhysicsLinkage` hangs things on) |
| .sgd | both octrees | both; glass section stripped | both; **HavokShatterGlassConnectivity (25,412 B) stripped**, as on the bank | **no ExplodableOctree at all** (stock M06 has none; 21 of 21 stock Dog Days levels have one) |
| PostFilterBox controllers of the map (the box table is left out for a Dead Men map) | not counted | not counted | 14 | 1 |
| filter sets against S's palette | | | 12 sets, 39 curves, none past the palette | the same |
| lit descriptors / scatter | 0 / 4 | 2,250 / 0 | 1,375 / 0 | 0 / 145 |

The missing ExplodableOctree was read: the loader (ZGameData slot 3 -> 0x5e38c0) skips a section it
does not find and leaves game data +0x814 as it was; the two users (0x60b426, 0x82e5a9) and the
destructor (0x86c243) test it for 0. ASSUMPTION: it is 0 at that point (what clears it before a level load was not followed; a direct
boot starts from a fresh object). `kl_members.sgd_join` could write
an empty section instead (9.7, patch C) - not needed if the reading is right.

### 9.6 Predictions, most likely first (where to look when a run faults)

M02_FA_A
1. `ZRenderEntryEnvSamplerD3D` (0x61b5a0 and what it calls) on the first frame that draws, unless
   the build is `--flat ZEnvSampler`. A fault there has kl2 0x61b5a0..0x61c0dc or 0x7ee4b0 on the stack.
2. `ZSoundSpline` 0x61e733 / 0x544ea1 (read of [sound instance + 0x84] / +0xa8) at level start if
   0x659370 returns 0 for the node. Fix then: drop the two controllers (`MultiPlayerSounds_Only!
   Nearest_Lane_Traffic_Sound`, `...Furthermost_Lane_Traffic_Sound`).
3. Size: 21,934 entities, 32 rooms and a 238 KB mesh are each more than any Dead Men build that ran
   (19,827 / 20 / 187 KB); stock L10 has 42,915 entities. No fixed limit is known to be near.
4. In a round: the escape car is a ZHavokCar on a spline (as in M01 / M03: `kl_fa` 'vehicle', never
   driven live yet), 303 jewel bags + 26 money containers, 3 patrols.

M06_FA_A
1. The two helicopters: `ZHeli` with Dead Men's model and mostly default fields, `HeliWeapon`
   (0x5f5340, 123 instructions, not read) on the escape chopper. A direct boot only loads them; the
   boss chopper flies when its squad is alerted, the escape chopper when the exit trigger fires.
2. `ZSoundSpline` x4 (as M02) and `ZSoundVolumetricRandom` x4.
3. No ExplodableOctree (9.5): if the reading is wrong the fault is at 0x60b4a7 or 0x82e62a
   (a call through [game data + 0x814]) the first time something explodes.
4. Look, not crash: no grass (scatter), no paper lanterns (shader), no picture-in-picture camera.

Both: the things every Dead Men map has had so far and that ran (dynamic list kept from S, three
`kl_fa` DEGRADED findings, music fields 157 / 158).

### 9.7 Patches for kl_graft.py (not mine; none is needed for the builds of section 10)

**A. verify() - the two other self-deleting inits** (after the `mute` test, about line 1117):

    first = lambda cls: next(i for i, f in enumerate(sch.fields(cls)) if f.owner == cls)
    for k in range(1, len(Jn.nodes)):
        for nm, obj in Jn.nodes[k]['ctrls']:
            name = Jn.p.key(nm)
            if name in ('OnlineMoneyContainer', 'PhysicsLinkage'):
                refs = J.strings(Jn, units(obj[1:-1])[first('Z' + name)])
                hit = Jn.resolve(refs[0]) if refs else []
                if not hit or (name == 'PhysicsLinkage' and not any('ZLNKOBJ' in sch.bases(Jn.cls(x)) for x in hit)):
                    bad.append('%s: %s deletes itself at init (kl2 0x837000 / 0x80bd20)' % (Jn.path[k], name))

**B. build() - Dead Men classes as their base, per build.** `kl_maps --flat` does it from outside by
adding `0x20010f: 0x200002` to `kl_gms.RETYPE` for the length of a build (the bisect that table's
comment describes). As a build option: `build(..., flat=())` with the same two lines around
`DeadMen(m_name, log)`, and `--flat ZEnvSampler` in the CLI.

**C. kl_members.sgd_join - always write both octree sections** (only if 9.5's reading fails live):
replace `if body:` by `if body or name == 'ExplodableOctree':` and give `Octree.join` of nothing the
serialisation of an empty tree (take the 880-byte section of stock L00 as the pattern; what the
smallest legal tree is was not worked out).

**D. install from a folder.** `kl_maps.py stage <folder>` copies a kept build into
`<work>/build/install/Scenes/Locations/<slot>`; `kl_graft.install(slot, src=None)` with
`d = src or out_dir(slot)` would make the copy unnecessary.

**E. re/crash_gamedata.md section 4** (not mine): ZHeliFlyBehaviourRout does not delete itself;
ZPhysicsLinkage (0x80bd20) does and is missing from the table (whether it is in the save-state table
at that point: not read).

---------------------------------------------------------------------------------------------------

## 10. The builds for the first live runs, and the commands

Built by `python tools/kl_maps.py deliver <out>`; each folder holds the slot's archive, the files
beside it (.WHD .WAV .hti and the `_LS` bank), `graft.txt`, `log.txt`, `result.json`,
`preflight.txt` / `.json`. All four: `verify: problems: 0`, preflight `CRASH 0`.

| folder under `<out>` | what | preflight |
|---|---|---|
| `F07+M02_FA_A flat` | **first M02 run**: Late Night Opening under F07, the 7 ZEnvSampler loaded as ZSTDOBJ | RISK 1 (SoundSpline) |
| `F07+M02_FA_A` | second M02 run: the samplers alive (the difference between the two runs IS the sampler) | RISK 3 |
| `F07+M06_FA_A` | **first M06 run**: A Walk in the Park under F07 | RISK 2 (SoundSpline, SoundVolumetricRandom) |
| `F08+M06_FA_A` | second M06 run: the helicopter host | RISK 2 |

Why F07 first for M06, against section 3.3: F07 is the only S that has run live under a Dead Men map
(every run of the log, a whole Arcade round included), and its kept escape-vehicle monitor is the one
that round ran with. Under F08 `kl_fa` has to add an empty monitor to the map's own exit trigger
(`Triggers!Call_ExitChpooer_Trigger`) - a path no run has taken. F08's advantages (smaller bank and
archive, a helicopter level) are worth a second run, not the first.

For the live side, one line each (run from the repo; `<out>` = the folder named in the agent's result):

    python tools\kl_maps.py preflight "<out>\F07+M02_FA_A flat"          (again, if in doubt: exit code 1 = do not install)
    python tools\kl_maps.py stage "<out>\F07+M02_FA_A flat"              copy the build into <work>\build\install (replaces the build there)
    python tools\kl_graft.py install F01                                 into the test slot
    python tools\kl_autotest.py 420 --shots 100-200:10 --tag M02a        direct boot; a healthy level leaves after 205 .. 325 s
    python debug\triage.py --keep                                        on a crash; then section 9.6

and the same with `F07+M02_FA_A` (tag M02b), `F07+M06_FA_A` (M06a), `F08+M06_FA_A` (M06b). To rebuild
one: `python tools\kl_maps.py one <out> F07 M02_FA_A --keep --flat ZEnvSampler`, or all four:
`python tools\kl_maps.py deliver <out>`. A round through the menu: as run RN6 (klhook\KLHook.round.ini),
wait 1000. `stage` and `install` write to the work folder and the game folder: the live side's step,
not done here.

---------------------------------------------------------------------------------------------------

## 11. First live runs of M02_FA_A and M06_FA_A (2026-10-09, agent g-live)

Run in the game, F01 slot, `python tools/kl_autotest.py`; pictures `<work>\research\shots\<run>_<s>s.png`,
logs of the scripted rounds `<work>\build\klhook\live\<run>.*`. The builds are the four of section 10,
rebuilt with the current tools (`python tools/kl_maps.py deliver <work>\build\v_maps`, all four
`problems: 0`, preflight `CRASH 0`) - `kl_maps.one` and `preflight` had fallen behind kl_graft
(`DeadMen(ao=)`, `broken_groups` moved to `kl_whd.torn_groups`); both fixed.

| run | build | how | RESULT | what was seen |
|---|---|---|---|---|
| M02a | F07 + M02_FA_A, `--flat ZEnvSampler` | direct boot | clean exit after 271 s | the mall: tiled floor, shop fronts, lit perfume posters ('Rose Lily', 'Directory'); the player is shot down at the start ('C Get Up', 'You died') - M02a_150s / 160s / 200s |
| M02b | F07 + M02_FA_A, samplers alive | direct boot | **crash kl2.exe+0xe5068 after 192 s** | not the samplers: see below |
| M02c | the same, rebuilt with the fix | direct boot | clean exit after 284 s | as M02a (M02c_170s) |
| M06a | F07 + M06_FA_A | direct boot | clean exit after 231 s | the Japanese garden at night under the motorway: gravel, rocks, stone lanterns that are lit, office towers behind (M06a_150s, M06a_190s) |
| M06r | the same | real Arcade round from the menu (klauto `Hooks=0`, the route of KLHook.round.ini, then: walk 3 x, look round, wait) | clean exit after 617 s, KLHook.result PASS | HUD, three lives, clock from 05:40; nobody attacked in the 5.5 minutes; the clock ended the round, score page, RETURN = Ready, round 2 with two lives (M06r_300s, _420s, _600s) |
| M02r | F07 + M02_FA_A (samplers alive) | the same script | clean exit after 647 s, PASS | start in a closed shop ('MIDASEC - Opening Soon'), the player stands behind a column for the whole round (M02r_290s, _450s), clock, score page, round 2 |

So: **all four Dead Men Fragile Alliance maps now load and run a real Arcade round under F07.** `--flat
ZEnvSampler` is not needed (prediction 1 of 9.6 for M02 did not come true: the seven samplers ran for
two direct boots and a whole round). The SoundSpline / SoundVolumetricRandom controllers, the missing
ExplodableOctree of M06 and the two ZHeli did not fault while loaded and idle. NOT exercised: the
helicopters flying (nobody was alerted, the exit was not reached), an explosion on M06, loot and escape
on either map, the F08 + M06_FA_A build (not run: F07 worked, and each run costs four minutes).

### 11.1 The one crash: a bullet on car glass (M02b), a tool fault of every Dead Men map

`0x4e5068` is in `0x4e5040(row, column, n)`: `rows + (row - 1) * row size + column offset` of the
level's surface table (`[0xea2878]`: the `.buf` tail, here F07's, 24 rows of 0x480 bytes), called from a
projectile's impact (`ZProjectileBase` slot 36, 0x512ed7) with the surface the bullet hit. No bounds
test. The fault read row 30.

The `.HVK` sub-parts carry that number (`re/havok.md`: 'surface index, 0..30 in Dead Men, 0..24 in Dog
Days'), and it is the row id of the surface table, 1-based, 0 = none: Dead Men's 27 sits on the car
bodies and 30 on their glass (`CarGlass`), Dog Days' 2 = `Car`, 23 = `Glass`. kl_mat already renumbers
the `.MAT`'s surface types to Dog Days' table (`kl_mat.surface_map`, 14 rows by GUESS); the `.HVK` was
copied with Dead Men's numbers. Rows 25..31 lie past F07's table: Paper, Gravel, Car, Glass, CarGlass
- every car and every window of every Dead Men map. The diner and the bank ran with the same fault
unnoticed (a read past the table that happened to hit mapped memory, and the wrong impact effect).

Fix: `kl_hvk.resurface` (called from `kl_graft.DeadMen`), the same map as the `.MAT`'s; `kl_graft.verify`
now fails a build with a sub-part past the table. M03: 807 sub-parts renumbered, M02 468, M06 160.
The bank was rebuilt with it.

### 11.2 For the tables above

- 9.6, M02 prediction 1 (env sampler render entry): did not happen. Prediction 3 (size): no limit hit.
- 9.6, M06 predictions 1 - 3: nothing while idle; none of them was provoked.
- New address for the table: `0x4e5068` / caller `0x512edc` = a surface row past the table (fixed).
- 9.7 patch D (`install` from a folder) is in: `python tools/kl_graft.py install F01 --from <folder>`.
  Patch A (the two other self-deleting inits in verify) and B (`build(flat=)`) are not; `--flat` stays
  in kl_maps.

## 12. Retomoto Tower loads (2026-10-09, agent h-live; runs RT1 - RT6, M01W)

Full account: re/retomoto_fa.md section 9. For this file:
- **The chain is proven live** (section 6 item 3): three static Havok parts, `nav_join`, 17 shared clone
  groups and no .hrd load and play. Two tool faults were in the way and are fixed: the joined .prm was too
  large for the loader's single heap block (kl_graft `PRM_LIMIT`, 99.5 -> 60.3 MB) and `nav_join` moved
  tree 1's children, which are relative to their polygon's root (rule added to `navtest`).
- A second `FFCoverList` asserts (kl2 0x6682c5): a Dead Men map brings `CoverList`, so S's
  `Specials!CoverPoints!*` must never be kept beside it. `kl_graft.verify` counts them now.
- The mover between the parts (section 6 item 2): a `JumpPoint` fired by a level object crashes for a
  Fragile Alliance player (kl2 0x8f40c9); the game's debug jump request, a two-dword data write, moves
  him in one frame. That write belongs in the hook.
- `python tools/kl_maps.py chain <out> F07 M09_B M09_A --author` builds the level with the FA layer;
  `kl_fa_author.py hero <build> <out> x y z` makes a copy whose direct boot starts somewhere else.
- M01_FA_A on the final tool: verify 0 problems, kl_fa 0 CRASH / BROKEN, direct boot with a walk clean
  (M01W; the walker is shot twice by the police on the way to the diner).
- Load time: the two-part level needs 200 s to its first frame on a direct boot (the bank 100 s).

## 13. M01's first menu round; the skeleton rebind on the maps (2026-10-09, agent i-live; runs M01R, BN0 - BR1, CH0 - CH1d)

### 13.1 M01_FA_A (the diner / Sunny Hill Plaza): first Arcade round - run M01R

Build `<work>\build\i_m01` (`kl_graft.py build F07 M01_FA_A`, verify problems: 0, zip 336,379,622
bytes, sha1 6d5577bd; built with the rebind of 13.2). TEST hook `scratch\ihook\test`, the menu route
of re/fa_round.md 3 and the walk of run M01W; `RESULT: clean exit after 335 s`, PASS.
- Session game mode 4, `FRAGILE ALLIANCE ARCADE - ROUND 1`, three lives, the clock runs.
- The player starts at (1757, 0, 30864) on the street (Amigo's Market, the plaza signs), walks to
  the diner ('ARNIE DINER' sign and window: M01R_216s.png), to the cash register at
  (6458, 0, 23173), out by exit 2 (5938, 0, 20412) and exit 1 (1682, 0, 20988) - 63 s, every way
  point reached. He is shot at from the moment he enters the diner (red screen, a guard's arm and
  pistol close up in M01R_234s.png) and is still alive 2.5 minutes into the round at (5389, 0,
  19282), where a police car has pulled up (M01R_324s.png).
- The last way point (9563, 15090), the escape car of the walk, was NOT reached: 5.8 km away after
  12 s, then the player stood for a minute. The run was ended by `pass` in the round: no round
  end, no score page, no loot taken (the scripted player does not press E here).
- No assert, no fault, no `INTEGRITY EXIT`; `MissionFailedReload` did not come up (in the direct
  boot M01W it did twice).
Not established for M01: loot, the escape, a round end, sound. It needs the walk extended the way
re/fa_round.md 6 - 7 did for the bank, or a person playing it.

### 13.2 kl_chars reid / rebind after the .ANM join (kl_graft.build), and what the pictures can say

The change of research\h_player-models.json 'blocked_on' is in `kl_graft.build`: after the .ANM
join every appended skeleton gets `kl_chars.reid` (bone ids of the destination level) and
`kl_chars.rebind` (animation numbers of the joined bone table); a bone no clip of the joined file
moves (M01's 'bone01'..'bone04') gets an entry at the end of the table; `kl_chars.check_bones` is
part of verify. Bank build log: `skeletons of M03_FA_A: 23 of 23 renumbered to the joined level:
649 bone ids, 361 animation numbers changed`, verify problems: 0. The only member that differs from
the build before is `F01_Main.prm` (`<work>\build\i_bank_before`, sha1 91ee4ba4, against
`<work>\build\install` = `i_bank`, 791dbd15 / 20aa9d7c, same members by CRC).

Live, before / after, same walk, direct boot (runs BN0 / BN1, CH0c, CH0d / CH1d; the walk goes to
the plaza civilian, the delivery truck, through the bank door past the clerk to the guards):
- Both builds load, walk identically (positions equal to a few units) and show the same plaza,
  bank hall and people. Nothing is worse with the rebind: no fault, no assert, no missing or
  exploded model in the pictures looked at (about 30 of the 400 taken). Round BR1 (menu route, the rebind build): PASS, round 2 started.
- **A difference could NOT be shown either.** The pictures are 640 x 480 from behind the player
  with the game's noise filter; people are 20 - 40 pixels tall except when they shoot the player
  point blank through a red screen. What can be read: before the rebind a guard's forearm, glove
  and wrist watch around a rifle are well formed (CH0c_78s.png), the delivery truck stands whole
  with doors shut (BN0_176s.png); after it the guards and the hero look the same at the same
  distance (CH1d_70s..82s.png). No frame shows a face or a car door in a state that would differ.
  The truck is a `ZHavokCar` that is not at its spot in every run (seen parked in BN0 and at the
  plaza edge in CH0d_90s.png, not seen in CH0c / CH1d).
- Kept, by the task's rule (not worse) and on the static evidence: `kl_chars.check_bones` is 0 on
  the rebind build, and h-chars' negative test (rebind off) reports bones that carry another level's
  animation number.
What would settle it: a person standing in front of a Dead Men guard's face and of a car whose
door is opened by a script (the escape van's sliding door, a police car arriving in a round), or
larger pictures - the game's window is 640 x 480 in these runs.

---------------------------------------------------------------------------------------------------

## 14. The four Fragile Alliance maps to the standard of the played Retomoto build (2026-10-10, agent z-maps)

OFFLINE: nothing was installed, the game was not started, nothing was written into the Dog Days
folder. Everything is in `<work>\build\z_maps\`. Commands (each map is a process of its own, about
100 s a map on this machine, two at a time):

    python tools\kl_maps.py ready <work>\build\z_maps [M01 M03 ...]     build + lighten + wardrobe + every checker
    python tools\kl_maps.py audit <work>\build\z_maps\M03               every checker again on a finished folder
    python tools\kl_maps.py readytable <work>\build\z_maps              the table below
    python tools\kl_maps.py stations <folder> ...   |   bots F07        14.5

### 14.0 Short answers

1. **All four are READY**: `kl_graft.verify` problems: 0 at the build, and on the finished folder
   `kl_fa.check` 0 CRASH / 0 BROKEN, `kl_impact.check` (bone ids, chunk table, surface rows) 0,
   `kl_arms.check` 0, `kl_chars.undrawn` 0 people, `kl_chars.check` 0 beyond the known materials,
   `kl_snd.verify` 0, `kl_maps.preflight` CRASH 0. Known and listed: 14.2.
2. **They are lighter than stock F07 where it matters for the 0x8e5bbd allocation** (stock F07: .prm
   63 MB, .TEX 281 MB, archive 200 MB): .prm 49.6 .. 60.5 MB WITH the wardrobe (15.5 MB of it), .TEX
   205 .. 235 MB, archives 178 .. 197 MB. The builds that ran live on 2026-10-09 were .prm 76 .. 87 MB,
   .TEX 374 .. 413 MB, archives 310 .. 336 MB.
3. **One map fault was found and repaired: M02_FA_A's boarding action stands at the BANK's
   coordinates, 95 m from its own escape car** (14.4). The first form of that repair moved M06's good
   box 102 m away from its helicopter; the audit caught it, it is fixed, M06 was rebuilt.
4. **The builds are reproducible**: M01, M02, M03 built twice (01:35 and 06:23, the second time on
   the lead's commit b276ad2) have the same content id; M06 differs in `.gms` and `.prp` only (the
   boarding box back in Dead Men's place).
5. **AI heisters: not kept, on any of the four** - F07's squad is 694 nodes of route authored for
   F07's alley; keeping it is authoring per map (14.5). The player is alone with the police, as on
   Retomoto.
6. NOT RUN IN THE GAME. What each map has that no live run exercised: 14.3.

### 14.1 What a build is

`kl_maps.ready_one` = the steps the lead used for the Retomoto candidate (`<work>\build\play3.log`,
`y_loot\build.log`), in the order re/prm_limit.md gives:

1. `kl_graft.build('F07', <M>)` with today's defaults and `kl_snd.VOICE = True`: kl_arms (seed 2026),
   kl_fa.repair (define order, money triggers for people only, boarding action in stock form, settings
   lists, exit / camera trigger, monitor), kl_escape.repair, kl_light (stock mode, `fit_shaders` +
   plain twins), the map's post filter sets, light map baked at 0.5, merged bank with kl_voice's
   repairs, joined .ANM, kl_chars reid / rebind + `kl_impact.sync_bone_ids`, .HVK surfaces renumbered.
   `kl_graft.verify` must say problems: 0.
2. `kl_graft.relight(..., 'trim,slim')` (= `kl_graft.py lighten`): 8,650 dead vertex / index chunks of
   F07's own map emptied, 451 of its textures down to 4 x 4.
3. `python tools\kl_chars.py wardrobe <lightened> <out>`: the eight Dead Men heroes and the mask /
   outfit variants in dead chunk indices (15,509 taken on every map), `KLWardrobe.ini`.
4. `kl_maps.preflight`, then `kl_maps.audit`: every checker on the FINISHED folder; `steps.json`
   records which members steps 2 and 3 changed (lighten: .TEX .prm; wardrobe: .MAT .TEX .gms .oct
   .prm .prp; the other 21 of 27 members and all 18 files beside the archive are the verified
   build's byte for byte).

A folder holds `F01_Main.zip`, the 18 files beside it, `KLWardrobe.ini`, `graft.txt`, `log.txt`,
`result.json`, `wardrobe.txt`, `chars.json`, `steps.json`, `preflight.txt / .json`, `audit.txt / .json`.
No `KLJoin.ini` (none is needed; `debug\slot.py put` removes the slot's). The systems level is F07 for
all four: nothing proved another one better (section 3.3's F08 for M06 is a suggestion without a run).
The `content id` is a sha1 over the members' CRC and size and the sha1 of the files beside the
archive: the wardrobe step stamps the members with the build time, so the zip's own sha1 changes
from run to run while the content does not.

| folder | map | archive MB | beside MB (of it .WAV) | .prm MB | chunk-table entries (limit 69,632 / 73,728) | .TEX MB | nodes | people (actors / players) | sounds / waves | verify | FA | impact | arms | undrawn | chars | sound | boarding action from the vehicle's stop | known: materials without a shader | content id |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| `M01` | M01_FA_A "Hot Coffee" | 196.9 | 46.9 (21.7) | 55.1 | 50,042 | 234.5 | 15,000 | 32 (16 / 16) | 4,878 / 4,741 | 0 | 4 DEGRADED, 2 NOTE | 0 | 0 | 0 | 0 | 0 | 364 | 1 | `79d6df638c` |
| `M02` | M02_FA_A "Late Night Opening" | 177.8 | 47.7 (22.5) | 54.6 | 58,371 | 216.1 | 21,935 | 31 (15 / 16) | 4,911 / 4,774 | 0 | 4 DEGRADED, 2 NOTE | 0 | 0 | 0 | 0 | 0 | 199 (was 9,534) | 6 | `b5838e7a63` |
| `M03` | M03_FA_A "Withdrawal" | 188.5 | 47.9 (22.7) | 60.5 | 62,680 | 217.8 | 19,828 | 36 (20 / 16) | 4,919 / 4,783 | 0 | 5 DEGRADED, 2 NOTE | 0 | 0 | 0 | 0 | 0 | 288 | 0 | `cf1ace987a` |
| `M06` | M06_FA_A "A Walk in the Park" | 177.6 | 47.0 (21.8) | 49.6 | 46,902 | 204.6 | 15,600 | 30 (14 / 16) | 4,797 / 4,658 | 0 | 3 DEGRADED, 2 NOTE | 0 | 0 | 0 | 0 | 0 | 305 | 6 | `6305f50b49` |

Per step (from each `<tag>.ready.log`): archive 336 / 310 / 321 / 310 MB as built -> 179 / 153 / 164 /
153 MB lightened -> 197 / 178 / 189 / 178 MB with the wardrobe; .prm 81.3 / 80.8 / 86.7 / 75.8 -> 38.9 /
38.5 / 44.4 / 33.5 -> 55.1 / 54.6 / 60.5 / 49.6 MB; .TEX 413 / 386 / 387 / 374 -> 223 / 195 / 197 / 184 MB
(+ 12 .. 21 MB of wardrobe textures). 8,835 .. 8,854 dead chunk indices are still free on each.

Install one (the lead's step; the game must be closed; the slot's stock files are in KL_PortBackup):

    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\z_maps\M03" F01
    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\z_maps\M01" F01
    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\z_maps\M02" F01
    python debug\slot.py put "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\z_maps\M06" F01

Not applied, one command each if wanted: the shader-cache cut of b276ad2 (`kl_graft.py lighten
<folder> <out> --load fxc`, NOT LOADED LIVE): measured dry on these four it takes the .fxc from 242
entries / 17.8 MB to 126 / 9.3 (M01), 125 / 9.1 (M02), 126 / 9.2 (M03), 122 / 8.8 MB (M06). Give it
the FINISHED folder (the wardrobe adds materials) and copy `KLWardrobe.ini` along.

### 14.2 Findings that are known and listed

- `kl_fa.check` DEGRADED on all four: no spawn points of the Dog Days-only kinds (TEAM_MERC,
  TEAM_POLICE, UCC: Cops & Robbers / Undercover Cop cannot place players), 0 `PointOfInterest` (no loot
  / escape marker on the HUD), no bot squads (14.5). M01, M02, M03: the escape vehicle is a `ZHavokCar`
  on a spline (never driven live). M03: 1 of 15 squads named by no object (`Civilians!Civ_in_02`).
  NOTE on all: settings fields 157 / 158 are Dead Men's music, no `MercSpawnCam*` define.
- Materials without a compiled shader (not drawn in that pass; no person is among them:
  `kl_chars.undrawn` 0): M01 `Locations/M01/Glass/Glass_Grid_01b_M01`; M02
  `Plastic_Basic_01a_LampMexi_M02_FA` and the five glows `Effect_Glow_Turkis_Round_01a_M06`,
  `Glow_Flare_01a_M07`, `Glow_Headlights_01b_M07`, `Glow_Beam_01a_M07`, `_Basic/Colour_White_Glow`;
  M06 the same five glows and `Paper_Rice_Lantern_01a_JPN`; M03 none.
  The glass of M01, measured: it asks for `glass.fx`, MESH_STANDARD, {BLENDENABLED,
  REFLECTIONENABLED, SPECULARENABLED, STDSAMPLERSTATE, USEDEFAULTREFLECTIONMAP}; all 14 `glass.fx`
  entries of the cache have REFRACTION2DENABLED, and one of them is exactly the asked set plus that
  switch. `fit_shaders` only switches features OFF. Switching that one ON would resolve it (NOT
  TRIED: what the 2-D refraction reads when the material has no input for it was not looked at).
- M01: 3 emitters name `Impacts_Default_Smoke`, the one Dead Men template Dog Days lacks (verify
  allows it; section 7 patch 2). M01 / M02: 1 / 2 `OnlineSpeakTrigger` cut, their line is not in the bank.
- `preflight` RISK (code no stock Dog Days level runs; all of it was LOADED live on 2026-10-09 in
  runs M02c / M02r / M06a / M06r without a fault): M02 `ZEnvSampler` x7, `SoundSpline` x2; M06
  `SoundSpline` x4, `SoundVolumetricRandom` x4.
- "dynamic lists name different classes; kept F07's" on all four, as in every Dead Men build that ran.

### 14.3 Per map: the round, the weapons, the voices, and what no live run has exercised

Counts are read from the finished archive (`audit.json`: `round`, `weapons`, `voice`). "loot" =
objects with `OnlineMoneyCtrl`; the dollar figure is the sum of its field 1 (ASSUMPTION: the amount).

| | M01 Hot Coffee | M02 Late Night Opening | M03 Withdrawal | M06 A Walk in the Park |
|---|---|---|---|---|
| loot objects / field-1 sum / containers | 306 / 10,050,000 / 1 | 363 / 6,135,000 / 26 | 340 / 5,750,000 / 12 | 307 / 11,340,000 / 0 |
| enter / leave / board triggers | 1 / 3 / 1 | 1 / 1 / 1 | 1 / 2 / 1 | 1 / 1 / 1 |
| level exit (calls the vehicle) | 2 (`CallExitVehicle_01 / _02`) | 1 | 1 | 1 (`Call_ExitChpooer_Trigger`) |
| escape vehicle | ZHavokCar on a spline | ZHavokCar on a spline | ZHavokCar on a spline | **ZHeli** (`OnlineEscHavokCar` + `OnlineEscVehicleController`, the form of stock F02 F03 F06 F08) |
| escape monitor | 1 (F07's) | 1 | 1 | 1 |
| START / AFTER_DEATH / TRAITOR points | 8 / 7 / 6 | 8 / 7 / 4 | 8 / 7 / 6 | 8 / 5 / 5 |
| squads / actors | 16 / 16 | 10 / 15 | 15 / 20 | 11 / 14 |
| bot squads | 0 | 0 | 0 | 0 |
| weapons after kl_arms (seed 2026) | SMG_Type05 4, HG_SW_MP45 2, Shotgun_Hawk_Police 2, Rifle_AK74 1, SMG_Type79 1, HG_M-77B 1, SMG_MAC_10 1, Rifle_Type81 1, unarmed 3 | Rifle_AK74 3, SMG_MPi69 3, HG_M9Beretta 2, Rifle_FN_SCAR 2, SMG_Type79 1, Shotgun_Hawk_Police 1, unarmed 3 | Rifle_AK74 5, Rifle_Type81 3, SMG_Type79 2, HG_SigSauer226 1, Rifle_FN_SCAR 1, Shotgun_Hawk_Bullpup 1, HG_SW_MP45 1, HG_M9Beretta 1, unarmed 5 | SMG_Type79 3, SMG_MPi69 2, SMG_Type05 2, Rifle_AK74 2, Rifle_Type81 1, SMG_MAC_10 1, SMG_HK_sp89 1, Shotgun_Hawk_Police 1, Rifle_FN_SCAR 1 |
| Dead Men gave them | USP 7, P90 5, Remington 870 1, none 3 | USP 4, M4A1 4, P90 4, none 3 | M4A1 9, USP 6, none 5 | P90 10, MP5 3, SG552 1 |
| voice sets in use (characters) | police_01 / _02 / _03 (13 soldiers, F07's sets), civilian_male_01 / _03 (1) | usa_swat_01 (12, the map's own set), civilian_male_01 / _03 (1) | usa_swat_01 (15), civilian_male_01 / _03 (2) | police_01 / _02 / _03 (14, F07's sets) |
| without a voice | 2 women | 2 women | 3 women | - |
| line fields heard / empty; silent lines | 134 / 64; 0 | 134 / 64; 0 | 134 / 65; 0 | 134 / 66; 0 |
| speak triggers with their line | 8 | 6 | 7 | 1 |
| light map baked | none (no lit descriptor) | 1,375 meshes, mean 0.858 | 2,250 meshes, mean 0.793 | none |
| post filter | palette 39 -> 51, 3 sets | 39 -> 47, 3 sets | 39 -> 53, 3 sets | 39 -> 58, 1 set |

(Heisters and police players have no voice set in a character field in stock F07 either: `kl_voice
census` of stock F07 says the same 8 + 8 "without". The bank's log: 6 sets widened by
`kl_voice.planner`, 34 silent members in them.)

What each map has that neither the bank's nor Retomoto's live rounds exercised:

- **M01**: the diner's loot (306 stacks, one register) and BOTH of its exits were never played; the
  spline car `Escape!EscapeCars\EscapeCar` never called. P90 / shotgun carriers now hold stock SMGs
  and Hawk shotguns (shotguns in a Fragile Alliance round ran on Retomoto only). `Heroes!` groups
  placed: 16 (the other three maps: 8).
- **M02**: 26 `OnlineMoneyContainer` (the jewel displays; the bank has 12 that ran) and 303 jewel
  bags; three floors with escalators; 32 rooms, 21,934 entities and a 238 KB mesh (each more than any
  build that played a round with loot); `ZEnvSampler` x7 alive; 3 `PatrolBehaviourRout`; the spline
  car; and the MOVED boarding action (14.4) - the one thing in these four builds that is new data.
- **M03**: the opened wall, the reach of garage boxes 10 / 11 and the spline van are in (kl_escape, as
  in ESC3, which ran WITHOUT the map's guards); with the guards and kl_arms's rifles the escape has
  not been played. The wardrobe on the bank ran once (2026-10-09 19:11, a 96.5 MB .prm, before the
  dead-index reuse); this build's .prm is 60.5 MB.
- **M06**: everything about the helicopters - the escape `ZHeli` arriving on its spline and being
  boarded, the boss chopper flying when its squad is alerted (run M06r: nobody was alerted in 5.5
  minutes); weapon PICK-UPS lying on the map (`BossChopper!Items!Minime_01` -> `MG_GP_Type88`, three
  `RPG7_01*` -> `RPG_7V`: stock Fragile Alliance has no pick-up at all, the class runs in story levels
  only); the escape chopper's `HeliWeapon` now has an EMPTY weapon template (kl_arms does not hand
  out the `_Heli` specials) - that is the stock form: the five escape helicopters of F02, F03, F06
  (two), F08 and L04's have it empty, the SWAT choppers of F02 and F08 name `MG_GP_Type88_L09_Heli`; the builds that ran
  live had `Mg_Minimi_SPW_L10_Heli` there. No `ExplodableOctree`, 8 `PhysicsLinkage`, no grass
  (scatter), no paper lanterns (shader).
- All four: `trim,slim` and the wardrobe ran live on Retomoto only; kl_arms and the voice repairs
  ran live on Retomoto only (the owner: "guards good"); the execution fix (define order) has not
  been confirmed by an execution on any map.

### 14.4 The boarding action: M02_FA_A's stands at the bank's coordinates

`OnlineEscHavokCar` field 2 names a box with `PlayerAction` "EnterVehicle". Measured on Dead Men's
own data (`kl_maps.boarding`: the box against the last point of the vehicle's incoming spline, both
through the entities' matrices):

| map | boarding box | vehicle stops at | apart | the level's BOARDS trigger |
|---|---|---|---:|---|
| M01_FA_A | (5884, 181, 20448) | (6165, 6, 20680) | 364 | (5876, 141, 20745) |
| M03_FA_A | (3252, 133, -20) | (2971, 26, 41) | 288 | (0, 0, 0) |
| M06_FA_A | (-1687, 133, -6542) | (-1536, 368, -6276) | 305 | (-1577, 554, -6499) |
| **M02_FA_A** | **(3252, 132, -20)** = the bank's box, half extents and all | (-583, 8, -8749), the car park | **9,534** | (-426, 136, -8627) |

Read in kl2.exe: `ZOnlineEscHavokCar` (vtable 0xbc94ac, members +0x30 incoming route, +0x34 escaping
route, +0x38 boarding box, +0x3c map icon) touches +0x38 in ONE place, slot 15 (0x769d80: the node's
virtual +0x54 on its own group and on the box); its message handler (slot 26, 0x5497a0, 214
instructions) sends to +0x30, +0x34 and +0x3c only. Dead Men's class (vtable 0x982254) does not use
+0x38 in its handler (0x6c90a0, 340 instructions) either, and its slot 15 (0x6c8e00) calls +0x54 on
its own node only. So nothing of that class moves the box to the car. ASSUMPTION (from run ESC3, where the scripted player boarded standing in the bank's box): Dog
Days offers the action at the box. How Dead Men's own M02 round got its players into the car with the
box 95 m away is NOT ESTABLISHED.

Repair, `kl_escape.board_box` (in `kl_escape.repair`, so in every `kl_graft.build` with the FA
layer): a boarding box farther than 1,000 from its vehicle's stop is put where the level's own BOARDS
trigger stands when that place is within the box's half extent of the stop (M02: (-426, 136, -8627),
199 from the stop), else on the stop, 107 up as on the bank. `.prp` ZGEOM[2] and the `.gms` record;
nothing else changes. M01, M03, M06 are left alone. NOT RUN IN THE GAME.

The slip, for the record: the first `_spline_end` tested "the spline node is unrotated" with
`round()`, which lets M06's 25 degrees about y pass; it then read the helicopter's stop as node +
point = (7116, 368, -11795) and moved M06's good box there, 102 m from the real stop. `kl_maps.audit`
(which composes the matrices) failed the build: "boarding: ... stands 10262 from the end of its
vehicle's incoming route". Fixed: `_spline_end` applies the node's rotation as `kl_maps.world` does;
that the reading is right shows in the level itself - the stop it gives is where M06's BOARDS
trigger, exit trigger (-1593, 206, -8050) and Dead Men's own box stand.

### 14.5 The AI heisters ("no bot squads")

`python tools\kl_maps.py bots F07`: stock F07's squad is 8 top-level subtrees
`Gameplay!merc_bot_squad!Squad#02..#08` + `...!Timer_start_bots`, **694 nodes**: 7 squads of one
`ZFFActor` (Rifle_zastavam85) with 28 `DefendBehaviourRout` steps and 65 boxes each (329 of the 455
are plain position boxes)
(`020_..._pos_merc_fight_middle`, `031_..._pos_on_top_of_loot`, `050_..._rout_out_of_loot_area_left`,
`060_..._rout_junction_garage`, ...: the alley of F07, x 8169..36283, z -3359..24504), 9
`RandomTrigger`, 4 `TriggerDelay2`, 4 `TriggerActorsDead` and 1 `TriggerLootDepleted` per squad. Out
of it: 175 references of `TriggerActorsDead[0]` to F07's own police and rival mercs, 35 of
`TriggerLootDepleted[0]`, 7 of `DefendBehaviourRout[0]` - all into F07's MAP, which the graft
removes; started by `Gameplay!AIMonitor` field 2 (kept by kl_fa already) through `Timer_start_bots`.

So `--s-keep Gameplay!merc_bot_squad!*` alone would keep seven actors standing at F07's START row
(10459, 440, 3252) - in the void of a Dead Men map - and 217 references into a map that is gone
(`kl_fa.prune` cuts such references of kept objects). Keeping
the squad means, PER MAP: 7 actors placed at the map's START row; a route of position boxes on the
map's navigation mesh (start -> fight -> loot -> leave -> vehicle; 329 in stock, a cut-down route
would do); the actor-dead waits re-pointed to the map's squads; the loot-depleted triggers to the
map's loot; and a proof that a bot boards a Dead Men spline car / helicopter (stock bots board the
baked van). That is what `kl_fa_street.py` did for Retomoto's police: authoring, not a switch. NOT
BUILT for any of the four.

What the map offers such a route (`python tools\kl_maps.py stations <folder>`: the round's stations
looked up on the built navigation mesh; parts = polygons connected by the edges' neighbour fields):

| map | mesh | START row, loot, way out, level exit and boarding box on one connected part? |
|---|---|---|
| M01 | 393 polygons, 6 parts (371, 16, ...) | yes, all on the part of 371 (the police's AFTER_DEATH points are on the part of 16) |
| M02 | 908 polygons, 18 parts (859, 24, ...) | yes, all on the part of 859 |
| M03 | 697 polygons, 9 parts (490, 159, 36, ...) | **no**: START, hall and garage on the part of 490; exit trigger, boarding box and van street on the part of 159. The wall kl_escape opens for the player is not opened in the mesh (Dead Men's AI never crossed it): a bot needs the two parts joined first |
| M06 | 954 polygons, 7 parts (936, 12, ...) | yes, all on the part of 936 |

So for bots the garden (M06) and the diner (M01) are the cheapest maps, the bank the most expensive.

### 14.6 Not known

- Nothing of section 14 ran in the game: no load of a lightened + wardrobe build of these four, no
  round on any of them with kl_arms or the voice repairs, no escape with guards, no boarding on M02.
- M02: that the action is offered at the box and not at the vehicle (14.4).
- M06: the helicopters in flight, the pick-ups, a rocket at the boss chopper.
- The dollar meaning of `OnlineMoneyCtrl` field 1 (the sums of 14.3).
- Whether `--load fxc` changes anything on screen (the lead's live check F1).

### 14.7 Changes outside kl_maps.py / kl_expansion.py, and for the lead

- `tools/kl_escape.py` (may be edited for a proven fault): `board_box` + `_spline_end` + the `move`
  entry of `repair()` / `place_entities()` (14.4), constants `BOARD_FAR`, `BOARD_UP`. `kl_graft.py`
  needed no change: it already passes `repair()`'s result to `place_entities()`.
- `kl_graft.py`, `kl_fa.py`, `kl_arms.py`, `kl_light.py`, `kl_snd.py`, `kl_voice.py`, `kl_chars.py`: not
  touched.
- Suggestions, not applied: (a) `kl_light.fit_shaders`: M01's glass (14.2) is one switch ON away from
  a compiled entry; (b) `kl_graft.verify` could call `kl_maps.boarding` so a misplaced boarding
  action fails a build and not only the audit; (c) CLAUDE.md lists the four maps' .prm as 75 - 87 MB
  ("larger than any stock level"): with `ready` they are 49.6 - 60.5 MB, wardrobe included.
- The expansion tree made from these four and the owner's Retomoto: re/expansion.md section 9.
