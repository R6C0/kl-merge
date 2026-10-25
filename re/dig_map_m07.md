# The dig / construction site = Dead Men chapter 7 "Reunion", level M07_A (2026-10-25, research only)

Read-only on both game folders; nothing installed or launched. Scratch: `C:\kl_build_1024\dig_research_1025a`
(`dump1..6.py`, `tex2.py`, extracted .prp/.LOC/.SND, rendered textures). Complements `re/dig_footage_research.md`
(web walk-through notes; its "local level probably M07_A, not verified" is now VERIFIED below).

## 1. Which level

| item | result | evidence |
|---|---|---|
| Level folder | `Scenes/Locations/M07_A/M07A_Main.zip` (only; no M07_B, no M07 FA) | folder list; kaneandlynch.exe names `Locations/M07_A` and also `M10_A` (no M10 folder ships) |
| Chapter | "Chapter 7: Reunion" (`M07A_ChapterTitle`); brief "Pray that The7 will spare your wife and daughter"; post "The7 mercilessly kill Kane's wife. Lynch snaps and together with Kane, they kill Mute and fight off The7's army, as Jenny, Kane's daughter, manages to escape" | M07A_MainEnglish.LOC |
| Internal name | "Gravel Pit": music `M07_Gravel_Pit_*`, `LevelSetup/Level/M07_A/Music/Gravelpit_Layer_V2/V3`, ambience `Construction_Site_01.wav`, SND stream `Construction_Site` | PC_Def.str, M07A_Main.SND |
| Who dies | Kane's WIFE (cut scenes `Wife_Enters`, `Wife_Killed`, speaker "Wife" in `M07_FamilyArrive`). Jenny is the DAUGHTER; she survives M07 (fail string `MF_02_JennyDied` only if you let her die; she is killed by the truck in a flashback `M07_DaughterDie`/`flashback_Add_Jenny`). Owner's "wife dies" = this chapter | LOC, PC_Def.str |
| Matches the screenshot | YES for place and mood: dusk sky (red sunset under storm clouds, `Backdrop_Front_01_M07`, rendered and looked at), concrete pipes (`PC0100_M07_ConcetePipe_01_GEOM`, 16 placed), scaffolding (`PC0101_M07_Scaffold_A_01..05`, 4 placed), excavator (`V_USA_Excavator_01`, 2 placed, one at about (-6626, 136, 2580)), containers (23 placed, `Metal_Container_01..04` + `_Open_01/02`; texture 03 is a RED rust container, 01 teal, 02 black, 04 blue; I rendered all four), crane (6 parts), city backdrop (`Backdrop_*_01_M07`) | prp names, .MAT, .TEX |
| NOT found | the lettering "SOUTH ST..." : zero hits for "SOUTH", "Jenny"-unrelated strings in prp/LOC/SND/MAT; no texture name suggests a street sign; the four container diffuse maps have no lettering. So the lettering is either an overlay/decal not in M07_A, or the screenshot is from a different build of the site | grep of every member + 369 texture names |
| FA layer | NONE on disk. The only shipped FA maps are M01_FA_A, M02_FA_A, M03_FA_A, M06_FA_A (exe string table, folder list). The Dead Men .LOC holds `BriefingDL02`/`TitleDL02` = "Briefing DL02 - Construction Site" (placeholder; IO's slot for an unshipped download map: DL01 Bank Vault, DL02 Construction Site, DL03 Prison, DL04 Tokyo, DL05 Mansion, DL06 Jungle, DL07 Havana, DL08 Las Vegas ...). The screenshot is therefore the DLC "Construction Site" FA map (web notes call it "Clean Cut", Dope Bag pack, console only); its level file is NOT in this PC install, so M07_A is the nearest real geometry (same art set, same sky). Whether the owner's files hold the DLC level is for the owner to say | re/maps.md, LOC |

## 2. Size and content (M07_A)

12,336 entities (M09_A 11,926; M09_B 16,646). Classes: ZSTDOBJ 4,009, ZParticleEmitter 3,610, ZAllocMany 1,095, ZGROUP 891, ZBoxPrimitive 421,
ZSNDOBJ 278, ZOMNILIGHT 123, ZRoad 35, ZHavokCar 10, ZFFActor 44, ZCAMERA 25, ZROOM 4. Rooms: `M07_A_Outside_01A` (2,194 entities, ONE outdoor room,
x -18634..13369, z -24296..27916 incl. backdrop) + two `M07_Backdrop_A_00`. Playable ground measured from cover boxes (129), containers, mud tiles:
x about -9900..2200, z about -2400..12500 (about 120 x 150 m), floor from the pit at y -550 up to y +400 (parking/ramp area at z 9600..11700) and +1250 (truck road at z -8000).
`kl_maps.py sides M07_A`: map 5,170 nodes would stay after the campaign pre-pass (125 subtrees / 1,474 nodes dropped: AI_Players 1,208, CutScenes 144,
Special 75, COOP 35, Hero 5, MonsterTruck bits 7); systems 5,691 (DD systems replace them). Soldiers: 45 ZSoldier-class actors (The7 squads), all dropped by the pre-pass.

## 3. Mission structure (from the level's own tree)

Fixed places (world coords, y up): player start `Hero!Hero_01` (-2691, -555, 2953) in the excavation pit, `Hero!Shovel_01` (-2569, -515, 3069); checkpoints CP_00..CP_04
cluster at (-2300..-3250, -420..-600, 2470..3690) (the pit and its ramp); grave cam box `CamBox_InGrave` (-4459, -563, 2276); EscapeArea bound (2310, 601, 8418);
`LevelBound_Truckland` at z -3000.

Flow (names are the tree's own):
1. INTRO (cut scenes `M07_WakeUp01`, `M07_Punishment`, `M07_Blackou02`, `M07_WakeUp02`, `Wife_Shot/M07_Wife_Enters`, `M07_Wife_Killed`, `M07_Lynch_Attacks`, `M07_Kill_Mute`;
   squads `IntroSequence!00_Fusion_Wake01Punish`, `01_Fusion_WifeExecution` (78 nodes), `02_Fusion_LynchFight`, `02_SquadProxy_MuteLastSeconds`, `10_Squad_DriverlessVan`):
   Kane/Lynch wake in the pit, executioners; objective 005 `KillExecutioners` (Kane has the shovel `Shovel_Atack_*` anims); `Checkpoint_0WifeKilled`; `BeatMute` box
   `PlayerAction_KillMute`; `Enemy!00_Squad_The7` (6 soldiers), `00_Squad_Mute`, `00_Squad_Driver`, `00_Squad_Guard`.
2. OBJECTIVE 010 "Protect Your Daughter" (`MissionObjective_010_Daughter`, Jenny hides in the grave pit: `SP_DaughterInGrave`, `COOP_DaughterInGrave`, `00_00_DaughterSquad` 85 nodes,
   `DaughterArrive_Car`): FOUR WAVES `Checkpoint_1Wave..4Wave` + `Checkpoint_N Wave_timer` timers, squads `02_01a, 02_02a, 02_02b, 02_03a, 02_03b, 02_04a, 02_04b _Squad_Advancing`
   (2..4 soldiers each, `HavokCarScriptRout` = they arrive by van on roads); van spawn points: (3700, -278, -2600) and (3790, -270, -1570) north-east; (-5400, 404, 11500),
   (-4900, 416, 10300), (-1100, 394, 9630) south-west car park; (7200, 837, 11600), (7000, 460, 10900) south-east. Four waves match the web walk-through.
3. OBJECTIVE 015 "Go To Jenny" / cut scene `M07_Vow`, `M07_Vow_Part2`, `25_Fusion_VowTruck`.
4. OBJECTIVE 020 "Stop The Truck - Kill The Driver": `Enemy!03_MonsterTruck` (195 nodes, 8 soldiers riding, 13 road splines, start about (6500, 1240, -8000), `V_MonsterTruck_01`, the
   dump truck), camera shaker `MonsterTruckCamShaker`, `PlayAudio_TruckBoss`/`TruckKill`, `Effects/M07_MonsterTruck_Splash_01`, achievement `Behemoth`. Then `M07_Aftermath` and chapter end:
   `SceneChanger` exit point -> M08_A (Breakout). Mission-fail boxes: `MF_02_JennyDied`, `MF_03_YouDied`, `MF_05_LynchDied`, `MF_04_DriverDied` (fail-safe timer).
5. Also in the level: `Special!Floodlight_triggers` (12 timer boxes that switch work lights `WorkLight` x94 as the waves come), `Special!PsychoCtrl` (Kane psycho mode after the wife dies),
   COOP squads `COOP!TruckSQUAD_COOP_01/02`, 3 jump points `Jump#01..03`, 10 `ZHavokCar` (vans, the truck, a car at (-1915, -359, 4668) = Jenny's arriving car).
Objectives strings: `M07_005_KillExecutioners`, `010_Daughter` / `010_Lynch_Daughter`, `015_GoToDaughter`, `020_KillDriver`, `030_KillAll`.

## 4. Music and sound

Music (`PC_Def.str`, global archive): `Music/InHouse/M07/M07_Gravel_Pit_START.wav`, `M07_Gravel_Pit_Layer_A.wav`, `M07_Gravel_Pit_Layer_A_V2.wav`, `M07_Gravel_Pit_Layer_B_TStarts.wav`
(the truck-starts layer), `M07_GravelpitTruckBoss_mono.wav`, `M07_GravelpitTruck_Kill.wav`, `M07_Subway_Layer_1og2.wav` (7 clips; same layered scheme as the Retomoto and Havana sets).
LevelSetup entries: `LevelSetup/Level/M07_A/Music/Gravelpit_Layer_V2` and `_V3` (+ start/stop-stream controls `Special!Music!PlayMusic_start / V2 / V3 / STOPSTREAM` and 9 trigger boxes `2p..9p`).
Ambience: stream `Construction_Site` (`SFX/Ambiences/M07_A/Outside/Construction_Site_01.wav`), rain on hard surfaces (`RainOnHardSurface`, 5 `RedPipes`), 20 `Water_Drip_Pipe_*` emitters,
crane creak 01/02, collie barking (dog bark = a ready-made ambience), propane explosion, aluminium, aircraft. Dialogue: 89 `Dialog/M07/...` files (Situation: FamilyArrive, FirstAttack..FifthAttack,
Burial, AboutToDie, TalkToDaughter, Aftermath, KickLynch, LynchWakes; OneLiners: DaughterMove/Scream/Die, HeroEscapingGrave); the FA round would use only the one-liners as banter.
Cut-scene audio: `SFX/Cutsequences/M07/Funeral/M07_5_Funeral.wav`, `Kill_Mute/Shovel_Hit_*`.
Weather: `M07A_Weather_Boxes.zip` (3), rain emitters; the sky is dusk (red sunset, heavy cloud), consistent with the screenshot.

## 5. Already ported to Dog Days?

NOTHING. `<DD>\KLExpansion\Maps` holds DM01, DM01B, DM02, DM03, DM03A, DM05A, DM06, DM06B, DM09 (+ DM09R* parts), DM11B, DD01..09, T01: no M07. grep of re/ and tools/ finds M07_A only as
(a) the SceneChanger target of M06_A (`re/campaign_fa_park.md`), (b) textures `Locations/M07` borrowed by M06 (47 of them, the exit cut scene's set), (c) cover-list pre-pass notes
(`re/bank_campaign.md` 387: `Special!CoverPoints!CoverControl` 126 -> 125; "nobody built them"), (d) `convert_audit.md` field counts. `tools/kl_fa_talk.py` uses M02_GravelPit lines, which belong to chapter 2, not this level.

## 6. Graft feasibility vs past grafts

| measure | M07_A | past builds / limits | verdict |
|---|---|---|---|
| .prm entries (header +4) | 15,750 | M09_A 17,380; M09_B 24,219; M06_A 25,504; M03_A 39,730; limit 69,632 (`re/prm_limit.md`), Retomoto two-part 65,119 | smallest campaign level on disk; room for DD systems + FA props with a wide margin |
| .prm bytes | 16.2 MB | M09_A 29.0; M06_FA_A 31.6 | small |
| .HVK | 1.10 MB | stock-loaded up to 5.0 MB, M09_A 2.4 | far below the limit |
| .TEX | 166 MB (933 textures, 369 names) | M09_B 147, M06_A 179 | normal; 369 names, only ~90 are `Locations/M07` |
| .oct / .gms / .prp | 314 KB / 230 KB / 2.9 MB | M09_A 322 / 226 / 2.8 MB | normal |
| .sgd (explodable octree) | 11.8 KB | M06_A 9.1 KB | M06-like (the M06 pipeline handles it) |
| rooms | ONE outdoor `ZROOM` + backdrop | M06_FA_A: 5 outdoor rooms | simplest case: outdoor map like A Walk in the Park; no interior rooms, no lifts/stairs |
| escape | 10 `ZHavokCar` on `ZRoad`/spline (campaign vans) | M01/M02/M03 use `OnlineVehicleOnSpline` | untested path in DD; a van on a road is the natural exit (DM02/DM01 cars work is reusable) |
| AI | 45 scripted soldiers all dropped by the pre-pass; no FA squads exist | DM FA layer is authored in `kl_fa_author.py` | needs authored squads, as for DM01B/DM03A |
| .ANM | 16.5 MB | never copied (header size differs, CLAUDE.md) | use the slot's own, nothing to do |
| shatter groups | `Pillar_A/E`, `Wall_Wood_B`, `Concrete_Tall`, `StonePile`, `Barikade` CloneGroups (1,153 + 780 nodes, 6 shatter-FX families) | DM06 shatter works | copy; the CloneGroup_Effects of DD stay |

Risks / open: (1) the lit-descriptor path (`kl_prm`) must handle M07's rain materials and 5 `RedPipes` emitters: not run; (2) 3,610 `ZParticleEmitter` (many in clone groups) is high: check the pool counters like
M09 (`re/engine_facts.md`); (3) nav/AI: a 120 x 150 m open pit with ramps and 129 cover boxes: DD bots need their own path data, how the DM01B/DM06 builds supply it applies; (4) Shovel melee and the truck set-piece
have no DD counterpart (the truck is a `HavokCarScriptRout` road script and could stay as a timed hazard, see `dig_footage_research.md` section "Beats"); (5) cut scenes (11 zips, 144 nodes) are dropped by
the pre-pass, so the pit start is a plain spawn, not the wake-up; (6) the DLC lettering "SOUTH ST" would be a retexture of the container (texture 03 red) if the owner wants the screenshot look.

## 7. Recommended next steps (not started)

1. `kl_fa_author`-style design doc: spawns in the pit ramp area (CP_00..04 cluster), loot at the containers/scaffold/excavator, escape van at the car park (z 9600..11700) or the NE road (3700, -278, -2600);
   waves as police squads from the 7 campaign van spawn points (`02_01a..02_04b` give ready positions and roads); truck pass as a timed lane hazard; floodlights switching on as rounds progress (existing timers).
2. Music: map the 7 clips to a layered set like the Retomoto build (`START`, `Layer_A`, `Layer_A_V2`, `Layer_B`, boss/kill stingers).
3. Ask the owner whether the DLC "Construction Site" level files exist in what they sent; if so graft that instead (same art set) and use M07_A only for music/sounds.
