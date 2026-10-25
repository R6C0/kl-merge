# The Dig (Gravel Pit) as a Fragile Alliance round: design + build plan (2026-10-25, DESIGN ONLY)

Nothing built, installed or launched; game folders read-only. Inputs: `re/dig_map_m07.md` (level facts, MEASURED),
`re/dig_footage_research.md` (web walk-throughs, no video), `re/dm01_ai_cover_1025.md` (cover recipe),
`re/dd_mechanics_catalog_1025.md` (dogs, doors, FX), `re/dm01_cars_1025.md` (cars), `re/bots*.md`, `re/campaign_fa_tooling.md`,
`kl_fa_v2_park.py` (the closest working template). Labels: MEASURED (a number from the files, named note), READ (existing tool or
note), PROVEN (ran in the game on another map), GUESS (mine, unproven). Section 9 collects proven vs guessed.

Owner (2026-10-25): the dig map where Kane's wife dies, "replicate this mission", same principles as the other maps: AI heisters,
smart cops, Dog Days mechanics (dogs, extinguishers, FX, scripted events), immersive, soundtrack. The screenshot (DM FA HUD, dusk
excavation, concrete pipes, scaffolds, excavator, red container "SOUTH ST...") matches M07_A except the lettering.

## 0. Result in ten lines
1. Source = Dead Men `M07_A` (chapter 7 "Reunion", internally Gravel Pit), single-source graft on Dog Days F07 systems. MEASURED: 12,336 entities,
   .prm 15,750 entries, HVK 1.1 MB, one outdoor room, about 120 x 150 m play area. Host F07 (35,101 entries) + M07 = about 50,851 entries
   (GUESS: simple sum like the other measured pairs), under the 69,632 tool limit and far under Retomoto's proven 65,119. No `compact` needed.
2. If the owner's files hold the real FA "Construction Site / Clean Cut" level, graft THAT and keep M07_A only for music/sound (dig_map_m07 section 7).
   This design is written so the layer (spawns, loot, squads, escape) moves over: it is data keyed to named places, not to M07 geometry.
3. Round shape (section 2): the crew starts IN the pit (the campaign start); a timed blast (the Subway-start / Retomoto blast pattern, see the
   CRITIC CORRECTIONS at the end: the level's two `Barikade` plugs are in the trench NORTH of the start, not at a ramp top) opens the round;
   police waves arrive by vehicle from the campaign's 7 van spawn POINTS (coordinates only: the vans and roads themselves are dropped by the
   pre-pass); loot at the containers, scaffold, pipes and excavator; the escape van comes to the EscapeArea bound at the top of the slope.
4. Cops (section 4): the Defend-chain recipe of DM01 (RunToCover + RandomTrigger + Flank + DefendPlayerPos) with cover boxes on real props;
   M07 already has 129 cover boxes (MEASURED). CORRECTED: the cover LIST is NOT dropped any more (`kl_maps.PASSIVE` holds `FFCoverList`, M07's
   `Special!CoverPoints!CoverControl` stays); the HOST's `Specials!CoverPoints!CoverControl` must be in the layer's DROP (a second list is an assert).
5. Dogs (section 5): DD has real police dogs (soldier style 6): F01, F03, F04, F06, F07 in FA, campaign L02/L03/L06/L11. Chain to clone = F01
   `Gameplay!PoliceDogs#01` (smallest) or F07 `021_FinancialAlley_Dog` (release by box). 2 dogs, released late, from the car park.
6. Mechanics (section 6): barricade blast start, floodlights as the waves come (the level's own 94 WorkLights + 12 timers), kick door only if a door
   prop exists (none found: GUESS), extinguishers on container/scaffold posts, gas cans/propane next to the pipes, police radio/siren sound nodes.
7. Music (section 7): the level's own 7 clips under `Music/InHouse/M07` + `LevelSetup/Level/M07_A/Music/Gravelpit_Layer_V2/V3` as ENGINE music,
   the Retomoto way (campaign PlayMusic groups kept, stream file carries the clips). Hook jukebox must skip this map (EngineMaps).
8. Budget (section 8): about 62 actors / 40 squads, inside PROVEN 99/55 (stock FA tops out at 57/36). .prm about 16.5 MB, entries about 51k.
9. Biggest risks: nav mesh + cover for AI on a 120 x 150 m pit with ramps (unconfirmed), 3,610 particle emitters, rain materials,
   DD cars on a ZRoad/spline escape (untested), and everything being unrun. Three go/no-go gates in the plan (section 10).
10. Effort: about 0.4 of a Retomoto for the layer (campaign_fa_tooling 0 point 6: single-level map 0.25 - 0.4) + 0.3 for cops/dogs/blast extras.

## 1. Facts the design stands on (MEASURED, dig_map_m07.md)
- Start `Hero!Hero_01` (-2691, -555, 2953) in the pit; checkpoints CP_00..04 around (-2300..-3250, -420..-600, 2470..3690) (pit + ramp);
  `Shovel_01` (-2569,-515,3069); grave cam box (-4459,-563,2276).
- Playable ground x -9900..2200, z -2400..12500 (units cm). Pit floor y -550 rising to y +400 (car park / ramp at z 9600..11700) and +1250 (truck road z -8000).
- EscapeArea bound (2310, 601, 8418); `LevelBound_Truckland` z -3000 (closes the truck road).
- Campaign vans arrive at 7 spawn points: NE (3700,-278,-2600), (3790,-270,-1570); SW car park (-5400,404,11500), (-4900,416,10300), (-1100,394,9630);
  SE (7200,837,11600), (7000,460,10900). Wave squads `02_01a, 02_02a/b, 02_03a/b, 02_04a/b` (2..4 men each). Footage: wave 1 from the ramp by the
  backhoe, wave 2 from a garage-like structure right of the pit, wave 3 from the left with little cover, wave 4 in two vans (walk-throughs, READ).
- Lights: `WorkLight` x94, `Floodlight_triggers` 12 timer boxes; rain `RainOnHardSurface`, 5 `RedPipes`, 20 water-drip emitters; collie barking, crane creak.
- Shatter families: `Pillar_A/E`, `Wall_Wood_B`, `Concrete_Tall`, `StonePile`, `Barikade` (1,153 + 780 nodes). Cover boxes 129. Containers, mud tiles.
- Campaign systems to DROP (pre-pass): AI_Players 1,208 nodes, CutScenes 144, Special 75, COOP 35, Hero 5, MonsterTruck bits 7 (1,474 nodes);
  45 scripted soldiers; map keeps 5,170 nodes; DD (F07 mainsceneincludes_multiplayer, CloneGroup_Effects, Heroes!) provides the systems.
- Not in the data: "SOUTH ST" lettering (a retexture of the red container, texture 03 red, or the DLC level).

## 2. The round (what the crew experiences)
Principle: heisters never see a cop plop in; every cop group either walks in from an out-of-sight lane or is carried in by a vehicle.

| beat | what happens | source of the piece |
|---|---|---|
| T0 start | crew spawns in the pit at Hero_01 (8 spawn points spread over the CP_00..04 cluster; spawn ONLY on nav part 1, see critic section: Hero_01 itself stands on a 2-polygon island), rain and dusk, ambience bed `Construction_Site` plays, calm music. Guards unaware. CORRECTED: the level's `Barikade_PRE` plugs are at (-2660,-655,-70) and (-2660,-575,1440) in the low trench 15 m and 30 m NORTH of the start (towards `LevelBound_Truckland`, z -3000), NOT at a ramp top; the way out for the crew is the slope to the south (z up, y -550 to +400). | spawns: kl_fa_v2_park pattern; bound: the level's own |
| T0+9 s blast | an explosion sound, then a barricade blows (smoke, dust, debris, camera shake). Use the z 1440 `Barikade` (15 m from the crew, real shatter FX + `Concrete_Shatter_Sound` + `Car_Ram_Sound` in the level) as the visible blast, opening the trench as a flank lane for wave D; the blast is dressed from `kl_fa_blast.py`'s PATTERN (it is Retomoto-specific code: it re-places six spare F07 helper boxes at fixed Retomoto coordinates and hangs on `kl_fa_author`'s blast timer, so the dig's own layer module needs that timer; it is not callable on another map). Owner's start rule (volatile blast, guards unaware until it) carried over. | `kl_fa_blast.py` pattern; blast+shake PROVEN live on Retomoto (owner 10-09 22:00 'amazing'); Barikade swap GUESS |
| Phase 1 | 6 to 8 mercenary-type enemies (the campaign's "The7" role, DD mercs, NOT police) hold the ramp area and the backhoe. They are the "wave 1" of the footage. Cover boxes at every post. | squads authored from DD F07 merc squad clones (kl_old_waves/Maker) |
| Phase 2 | loot: 14 briefcases at the containers, pipes, scaffold and excavator (see 3). Pick-up starts the money and raises the music to ACTION. | kl_fa_loot dress, OnlineMoneyCtrl as other maps |
| Phase 3 police | police arrive in 3 waves (by clock + by the crew's loot count): wave A two cars from the NE road (3700,-278,-2600); wave B one car + a van from the SW car park; wave C a heli drop or two cars SE (7200,837,11600). SWAT get out and run to cover (section 4). Dogs join wave B or C (section 5). Floodlights switch on as each wave comes. | kl_dm01cars_1025 / kl_arrivals_1024r2 pattern; lights: level timers |
| Phase 4 escape | after enough loot (or a clock), the escape van drives down the SE road and parks at the EscapeArea (2310,601,8418) at the ramp top; the heli/van call is the standard FA call. Cops press from three sides while the crew carries the loot up the ramp. | kl_map_escape van plan |

Optional garnish (not in the first build): the campaign monster dump truck passing on the high truck road as a visual/sound hazard
(road z -8000..-3000, outside the play area; GUESS 195 nodes and a road spline can run under DD's rules; see 8, R6).

## 3. Layout and loot (all coordinates GUESS until the survey runs)
- Survey first: `python kl_maps.py what M07_A`, `kl_fa_loot.py survey` (briefcase props, pick-up reach), `kl_fa_cover.py` boxes list, nav mesh picture
  via `kl_fa_bots.Nav` (park study `pic.py`). Output decides every point below.
- Spawns: the pit cluster. Heister start must be out of sight of phase 1 men: the pit walls (floor -550 vs ground 0..+400) give it for free.
- Loot (14 cases + 1 stack of 5 near the escape, owner: stacks reachable and nearer the outer ring, briefcase props): 4 at the containers around
  the red shipping container, 3 at the concrete pipes, 3 on the scaffold decks, 2 at the excavator, 2 in the car-park structure. Props: briefcases
  (`kl_fa_loot props` finds them). Statues rule of Retomoto does not apply (no statues on this site).
- Owner's HUD screenshot numbers (Total 3.4 M, Loot 540 k) = the DM FA payout scale; set the money controller to the same ratio as DM01 (copy,
  do not invent).
- Cop lanes: ramp (phase 1), NE road, SW car park, SE road. Three approach faces into a pit with one ramp = natural pressure; nav chokes to be measured
  (method of `dm01_ai_cover_1025.md` section 3: single-polygon bans).

## 4. Smart cops (recipe from `re/dm01_ai_cover_1025.md`, READ)
Campaign "smart" is structure, not a difficulty table: `RunToCover` (per-actor point behind a box) -> `RandomTrigger` (3 to 5 outcomes) -> `Flank` / `Defend`
with different points -> `SquadModifier Unleash` -> `DefendPlayerPos`. Apply to each police squad of each wave:
1. Cover: every Defend post needs a box within 5 m. M07 has 129 boxes (MEASURED, plus 25 `NoCoverBox`). CORRECTED (critic): the pre-pass no longer drops
   the list (`kl_maps.PASSIVE` has `FFCoverList`; kept 7 `Special!` nodes include `Special!CoverPoints!CoverControl`), but F07 carries its own
   `Specials!CoverPoints!CoverControl` (ZLIST, node 17296), so the layer needs `DROP = ('Specials!CoverPoints!*',)` as `kl_fa_v2_park` has. Boxes are
   dense in the pit (z -1000..7000: about 150 hits) and THIN on the south plateau (z >= 8000: about 13), exactly where the SW/car-park and escape
   fights would be: add boxes there by `kl_cover_add` (containers, pipes) and vet with `kl_cover_vet scan <zip>` (the player must be able to stand at each side).
2. Per squad: `RunToCover` entries (one per actor), one `RandomTrigger` choosing `FlankLeft` / `FlankRight` / `Defend`, a modifier (`eCOM_UseCovers`,
   vision x2) and a `DefendPlayerPos` push after 40 s. CORRECTED (critic): `kl_dm01squads_chain.py` is a 22-line DM01-only driver (fixed paths, `IG.PLAN['DM01']`) and
   `kl_dm01squads_1025.py` contains no RunToCover/RandomTrigger/Flank at all: that recipe is NOT built on any map yet (spec only). The real, existing
   templates are `kl_fa_v2_park.py` (`SQUADS`, `squad_plan`, `place_police`, `ARRIVE_START='10_RunToCover'`) and `kl_fa_hasta_police.py`; write a new
   `kl_dig_squads` from those.
3. Four faces, four squads with different approach order so the crew cannot hold one ramp edge: A on the NE road side, B on the SW car-park side,
   C from the SE, D flank team from the pit rim.
4. Do NOT touch accuracy/health (DM01 values 75 / 100 to 175, same band as stock FA); the runtime Difficulty option already scales rows.
5. Cars: police squads that arrive by car use `DontUseCovers` only while still in the car (the DM01 cars precedent, not for fights).
GUESS: what a Flank's two points do; how far RunToCover searches by itself (the two open guesses of the DM01 spec, same here).

## 5. Dogs (Dog Days mechanic, found in DD)
- Class: a normal `ZFFActor` + `ZSoldier` with soldier style 6 (MEASURED in dd_mechanics_catalog_1025 section 1). In FA: F01, F03, F04, F06, F07 have
  one each; campaign L02 (2 squads), L03, L06 (`Burger_Dogs_Inside`), L11 (`SQ_DogsFinal_03`). F02, F05, F08, F09 none.
- The DM zips' ANM already hold the Dog animation set (MEASURED, 27 zips). A dog needs the MODEL + textures (kl_prmgraph/kl_texmat path, as the
  cans), a Ground actor and squad, and a bark (F04 `Dogs_01/02` ZSNDOBJ or the M07 collie-bark ambience, already in the level).
- Recipe: clone F01 `Gameplay!PoliceDogs#01` (nodes 266..271: `10_Defend\Pos#01/#02`, `Dog#01\Ground`) with `kl_fa_bots.Maker.clone('F01'...)`; or F07
  `021_FinancialAlley_Dog` with `tbReleaseDog` (release-by-box, 6 nodes). Place the box on the loot route at the car park.
- Rules (catalog section 1, GUESS): dogs never use cover and never throw; release late (wave B), never at the spawn; 2 dogs max (+2 actors, +2 squads);
  run along the nav mesh (same mesh, unproven). Tool: new small step `kl_dig_dogs` modelled on `kl_old_waves.py` (clone + place + wire).
- Why it fits here: open pit, no corners, the dogs "go for" a lone looter and the owner's M07 audio already has a collie barking in the distance.

## 6. Dog Days mechanics and FX (what to add, where)
| mechanic | placement on the dig | recipe | status |
|---|---|---|---|
| Round-start blast | the z 1440 `Barikade_PRE` in the trench north of the start (CORRECTED, not a ramp top) | pattern of `kl_fa_blast.py` (Retomoto-specific code, see section 2) | blast+shake PROVEN live on Retomoto (owner 10-09); Barikade swap GUESS |
| Police cars arrive, SWAT get out | NE road, SW car park (main-part point only), SE road | `kl_dm01cars_1025.py` + `kl_arrivals_1024r2.py` (F03 `Activator_SWAT_Cars`, ANM clips merged by `kl_anm`/`anmjoin`) | installed on DM01, unproven live. CORRECTED: all 10 M07 `ZHavokCar` and all 35 `ZRoad` sit under `AI_Players!` (dropped), so the campaign vans/roads do not exist in the graft: only the 7 spawn COORDINATES are usable, the cars are DD's and the lanes must be re-authored (tool re-keys DM01/DM02 only) |
| Kick door | needs a door prop; none found in M07 | add a shed/garage door prop (GUESS) or skip; `kl_dm03a_swat_1025.py` is the recipe | optional |
| Wall extinguishers | on container walls and scaffold posts near the pit; prop is wall-mounted | `kl_dm01fb_1025.py` (extinguishers) | built, not live-checked |
| Gas / propane cans | CORRECTED: M07 already has them: 3 `ExplosiveBarrel_B` at (-1055,-601,812), (-5317,-581,1119), (-3875,-369,4511), a `PropaneTank` PRE/POST at (-2660,-655,-70) (on the north Barikade) with `GeomActivator_PropaneTank` (301,-145,3252) and the propane explosion/burning sounds; whether they survive the pre-pass as live destructibles is unchecked. Add DD cans only where none | `kl_dm01b_gas_1025.py` (cans via `kl_prmgraph`) | staged on DM01B, unproven |
| Tear gas | a SWAT shutter assault has no shutters here; instead throw tear gas into the pit during wave C (GUESS; no police squad throws grenades in stock) | F07 `Shutters\GeomActivator_TearGas_*` | skip in v1 |
| Heli drop | wave C alternative, 4 SWAT from a heli over the SE road | `kl_fa_hasta_heli.py` / `kl_fa_bank` heli waves | PROVEN in part (Last Call / Hasta escape heli); drop-off needs a spline (M) |
| Floodlights | 94 WorkLights switched by the level's 12 timer boxes as the waves come | keep the campaign's `Floodlight_triggers`, re-point their trigger to wave start | GUESS (timer wiring) |
| Radio / siren / megaphone | police squads get `RadioCom` ZSNDOBJ (F07 `Police_SWAT_01\RadioCom`) | clone with the squad | S |
| Human shield cams | free, in DD systems kept by the graft | verify only | GUESS |
| Rappel SWAT | the pit rim looks down: L07 `MC_Repell` cells (DD campaign) could drop wave D into the pit | `kl_fa_rappel.py` / `kl_fa_rappel_bots.py` (DM09 owner start) | optional, high effect, M |
| Dump truck hazard | high road, timed pass-by | campaign `Enemy!03_MonsterTruck` bits (dropped by the pre-pass) | leave out of v1 (R6) |
| Rain | M07's own `RainOnHardSurface` + emitters | kept if it loads | R2 |

## 7. Soundtrack and ambience
- Level music (MEASURED, dig_map_m07 section 4): 7 clips `Music/InHouse/M07/M07_Gravel_Pit_START`, `_Layer_A`, `_Layer_A_V2`, `_Layer_B_TStarts`,
  `M07_GravelpitTruckBoss_mono`, `M07_GravelpitTruck_Kill`, `M07_Subway_Layer_1og2`; LevelSetup `Gravelpit_Layer_V2`, `_V3`; controls
  `Special!Music!PlayMusic_start / V2 / V3 / STOPSTREAM` + 9 trigger boxes `2p..9p`.
- Mapping to FA moods (GUESS, by name): calm = START + Layer_A; ACTION (first shot / first loot) = Layer_A_V2 then V3 / Layer_B; ESCAPE (van called) = Truck_Kill
  stinger; "TruckBoss" as a wave-C stinger. Same layered scheme as Retomoto and Havana (READ).
- Delivery: engine music like the park (kl_fa_v2_park MUSIC: campaign PlayMusic groups kept, layer starts them at round start and fades at the alarm);
  needs the 7 clips in the merged `PC_Def.str` (`kl_v2_str.py` / `kl_club_str.py` pattern; `kl_v2_str.SETS` is keyed by level and has only `M06_A` and `M01_A`: add an `M07_A` entry; the 7 names were re-checked in the DM sound strings; note `Construction_Site_01.wav` is already in the stream via M06_A's SET) and the sound bank's WHD records; the stream file must be
  the INSTALLED one or the level is silent (park precedent, kl_expansion note). Register `DM07` in the hook's `EngineMaps` (default list now DM09, DM06B,
  DM03A, DM05A) so the jukebox does not double up; the owner's PD2 jukebox is off by default anyway.
- Ambience: `Construction_Site_01` bed, rain on hard surfaces, 20 dripping pipes, crane creak, collie barking, propane explosion: all kept by the graft
  (map-local sounds); add the F07/F04 police radio nodes. Voices: M07 has 89 lines; only the OneLiners (DaughterMove/Scream/Die, HeroEscapingGrave) are
  usable as banter and "Jenny" lines would make no sense in FA, so `kl_dmlines`/`kl_fa_talk` use Kane/Lynch-neutral lines only (GUESS: pick by reading the .LOC).

## 8. Budget and risks
Budget (GUESS from other maps; MEASURED where noted):
| item | plan | limit / precedent |
|---|---|---|
| .prm entries | about 50,851 (F07 35,101 + M07 15,750), + about 1,500 for cans, dogs, extra FX | limit 69,632 (re/prm_limit.md); M06_A host build 53,960 |
| .prm bytes | about 17 MB | M09_A 29.0, M06_FA_A 31.6 MB |
| .HVK | 1.1 MB + small | stock loaded up to 5.0 MB |
| .TEX | 166 MB, 933 textures | M06_A 179 MB; memory is the wall (re/actor_caps.md: 1828 MB measured after load on an owner crash) |
| actors | 7 bot heisters + 6 phase-1 mercs + 8 police wave A + 8 B + 8 C + 4 D (rappel, optional) + 2 dogs + 8 SWAT car crews + 3 civ-free = about 62 | stock FA max 57, proven 99, DM05A 129 unproven |
| squads | about 40 | stock FA max 36, proven 55 |
| cars | 3 police cars + 1 van + 1 escape van = 5 (campaign had 10 ZHavokCar) | DM01 plans 3 cars |
| particles | 3,610 emitters in M07 (many in clone groups) | check pool counters like M09 |
| entities | 12,336 -> about 5,170 map nodes kept + DD systems | |
Risks:
- R1 nav and cover: READ BY THE CRITIC (see end): the nav exists (598 polygons) but has islands and gaps. The cover list is kept (R3 is stale). Mitigation: the Gate 1 check below.
- R2 rain materials and 5 `RedPipes` emitters through the lit-descriptor path (`kl_prm`): not run. Fallback: strip the rain emitters in `lighten`.
- R3 STALE (critic): the cover list is no longer lost (`PASSIVE`); the live risk is the opposite, a second list from the host (DROP it).
- R4 vehicles on a ZRoad: DD never drives a ZHavokCar, arrivals are animated cars (dm01_cars section 2); the escape van is the key-framed van of
  `kl_map_escape` (PROVEN on Hot Coffee and Withdrawal, per campaign_fa_tooling). Both need M07 route points; the pit and ramp may be steep for a van.
- R5 pit wake-up cut scene dropped (no wake-up); the start is a plain spawn (accepted).
- R6 truck and Jenny/wife systems have no DD counterpart; left out. The `MF_*` fail boxes (Jenny/you/Lynch/driver died) MUST be dropped: they would end
  the round. Pre-pass drops `Special` but check that no fail gate remains.
- R7 time-of-day fields (ZENVIRONMENT) not read; dusk look is a GUESS until a screenshot compares.
- R8 menu: `kl_expansion` has page 3 holding DM05A (F01), DM06B (F02), DM01B (F03), DM11B (F04); page 3 is "the last that fits" (campaign_fa_tooling 0.5).
  DM07 needs the next free slot on page 3 and a `LevelPicture_M07` entity (menu scene has pictures for M03A M03B M05 M06 M08 M11A M11B only; reuse by
  `ICON_MAPS` pattern; the picture list is UNVERIFIED by the critic). CORRECTED: NOT F05 (F05, F08, F09 are the paid-DLC slots, re/expansion.md 846).
  `ORDER = [1,2,3,4,6,7,5,8,9]`: page 3 uses F01 (DM05A), F02 (DM06B), F03 (DM01B), F04 (DM11B, in `ICON_MAPS` only); the free entries are F06 and F07.
  Use F06. `kl_fa_v2_park`-style modules are slot-bound (`SLOT`), so build with slot F06.
- R9 everything is unrun. Owner rule: install only on the F01 test slot first.
- R10 no footage of the real FA level. Layout is built from M07 geometry; if the owner provides Construction Site / Clean Cut files, re-point the layer.

## 9. Proven vs guessed
| thing | state |
|---|---|
| M07_A facts (counts, places, music, sizes) | MEASURED (dig_map_m07.md) |
| Single-level campaign graft on F07 | PROVEN live for M06_A (Park II runs L81/L82 etc. in open_work_log) and M09 (Retomoto, owner played); Hot Coffee II / Hasta built, status per log; M07 never built |
| Authoring layer by data (spawns, loot, squads, escape) | READ (kl_fa_v2_park); runs on Park II (unproven live), Retomoto (live) |
| AI heisters (7 bots, dyn) | PROVEN on several maps (Last Call L51, etc.) |
| Round-start blast | PROVEN live on Retomoto (owner 10-09 'amazing'); Barikade variant GUESS; the code is Retomoto-bound, copy the pattern |
| Cop cover structure (RunToCover etc.) | spec from DM01; not built even there |
| Police cars arriving | DM01 staged/installed, unproven live |
| Dogs on a DM map | NOT BUILT anywhere; stock chains MEASURED in DD; recipe all GUESS |
| Extinguishers, gas cans, kick doors | built on other DM maps, not live-checked; no door on M07 (GUESS) |
| Engine music | built on Park II and Retomoto; clip mapping for M07 GUESS |
| Rain/particles, nav, cover list on M07 | UNKNOWN (gates 1 and 2) |
| Dump truck hazard, rappel start, tear gas | GUESS, optional |

## 10. Phased build plan (tool per step; each phase ends with verify, preflight, autotest on the F01 slot)
Gate order: do not start a phase before the previous gate is green; each build gets a commit message with what crashed and why.
1. Phase 0, survey (read-only, 1 day of agent time): `kl_maps.py what/sides M07_A`; `kl_fa_cover` box list; nav mesh via `kl_fa_bots.Nav` (draw the pit
   picture); `kl_fa_loot survey`; read ZENVIRONMENT fields; decide spawn/loot/escape coordinates. Output: `dig_layout.json` (the data file).
2. Phase 1, bare graft: `python kl_maps.py one <out> F07 M07_A --campaign --heroes` (CORRECTED by the critic: the CLI takes the OUT folder first, and `--heroes` needs a new
   `kl_maps.HERO_AT['M07_A']` entry for a marker that survives the pre-pass, since `Hero!` is dropped; start on nav part 1) (single-source), `kl_graft lighten`, `kl_chars wardrobe`, `kl_impact`; `verify_levels` problems 0
   (new entry), `debug/check.py`, `kl_prm` limits. GATE 1: loads and the autotest ends clean on the F01 slot with a bare player (rain, particles, nav, cover list present).
3. Phase 2, FA layer v1 (no cops yet): new `kl_fa_v2_dig.py` cut from `kl_fa_v2_park.py` (nine `AUTHOR_NAMES`), spawns in the pit, loot (`kl_fa_loot dress`), bounds
   (pit step-off kill), escape van plan (`kl_map_escape.van_prepare` / `kl_fa_v2_park.py plan`), merc phase-1 squads (clone with `kl_fa_bots.Maker`). Bots:
   `kl_fa_bots` + `kl_fa_bots_dyn` (7 heisters). Music via campaign PlayMusic groups. GATE 2: a round plays start to escape with bots and loot.
4. Phase 3, blast start: `kl_fa_blast.py` hung on the start timer (Barikade at the ramp top), pit bound lifted by the blast. GUESS check: guards unaware.
5. Phase 4, police and cover: `kl_cover_add` / `kl_cover_vet` / `kl_fa_cover`; cover-list fix (park `trial2` cure); police squads A to D with the DM01 chain
   (`kl_dm01squads_chain.py`, `kl_old_waves.py`); arrivals by car (`kl_dm01cars_1025.py`, `kl_arrivals_1024r2.py`, `kl_anm` merge). GATE 3: cops use cover, arrive in sight lines
   of nobody, no pop-in.
6. Phase 5, Dog Days extras in order of effect/effort: dogs (new `kl_dig_dogs`, model graft by `kl_prmgraph`), police radio nodes, extinguishers
   (`kl_dm01fb_1025`), gas cans (`kl_dm01b_gas_1025`), floodlight timing, optional heli drop / rappel (`kl_fa_rappel`).
7. Phase 6, post-pass (memory checklist): `dmlines --fed`, `gunpics` once, `fedbody KLJoin.ini` after the last .prm change, then `check_passes` + `klt_audit`.
   The fed outfit: police bodies for the feds come from the map's own police group (`kl_fa_fed.py build ... --body map`), `kl_fa_fedbody.py` for the player's fed
   body (owner: the fed should not be the Chinese fed on any FA map); same step as the other maps.
8. Phase 7, package: add `dict(id='DM07', slot=<free page-3 slot>, page=3, title='The Dig', build='prebuilt', sources=['M07_A'], picture=<reuse M06/M01>, ...)` to
   `kl_expansion.EXTRA` (mind the PAGE=2 hard-coding: tool work), hook `[Music.DM07]` + `EngineMaps`, merged `PC_Def.str` for the 7 clips. `python tools/kl_expansion.py build`.
9. Phase 8, live: owner not playing; `kl_autotest.py`, `debug/triage.py --keep`; then a test round. Do not install outside the F01 slot until the owner says so.

## 11. Questions for the owner
1. Do the real Construction Site / Clean Cut files exist in what was sent? If yes graft them and keep M07 for music.
2. Name: "The Dig" / "Gravel Pit" / "Clean Cut" (it would be a campaign remake, not that map).
3. Cop style: SWAT only, or the merc-style The7 men for phase 1? (default above: mercs phase 1, police waves after.)
4. Dogs on by default or a toggle (owner rule: every feature a toggle, labelled recommended on/off): propose `Dig.Dogs`, `Dig.Rappel`, `Dig.Truck` toggles.

## 12. CRITIC PASS (2026-10-25, adversarial; scratch C:/kl_build_1024/dig_research_1025a/crit2.py, crit3.py, crit4.py; read-only on both games)
Verdict: GO for Phase 0 and Phase 1 (bare graft), NO-GO for committing to the round shape as written until the corrections below are folded in.
Method: re-loaded M07_A with `kl_prpjoin.Scene`, `kl_maps.world`, `kl_maps.nav_of` + `kl_pf4.convert` + `kl_fa_bots.Nav`; scanned the DD stock zips for dog chains.

CONFIRMED (checked against the data)
- Level: `Scenes/Locations/M07_A/M07A_Main.zip`, 12,336 entities, `kl_maps.py sides`: 125 subtrees / 1,474 nodes dropped, 5,170 stay; Hero_01 (-2691,-555,2953),
  EscapeArea bound (2310,601,8418), LevelBound_Truckland (-2415,-664,-3041); 129 cover boxes (154 name hits minus 25 NoCoverBox). Identification of the level is right.
- Dogs are real in stock DD: F01 `Gameplay!PoliceDogs#01`, F03 `10_AirportSecurityDog01` + `RandomTrigger_Dog` (also a dog chain, the note missed it), F04 `030_AfterLoot!032_LeftFlankDOG`,
  F06 `AI_Players!Enemys!030_dog`, F07 `020_Loot!021_FinancialAlley_Dog`; campaign L02 (`02_Dog#01/#02`), L03, L06, L11. F02/F05/F08/F09 none. M07 has only a `Collie_Barking` sound.
- No kick/door prop in M07: every "door" hit (75) is a car door of the vans. Optional kick doors stay optional.
- 7 music clips present in the DM sound strings (`Music/InHouse/M07/...` incl. `M07_GravelpitTruck_Kill.wav`), LevelSetup `Gravelpit_Layer_V2/V3`. `EngineMaps` default is DM09,DM06B,DM03A,DM05A.
- Functions/tools that exist: `kl_maps.one/campaign_drop/nav_of`, `kl_graft.author_module` + `AUTHOR_NAMES` (nine names), `kl_fa_bots.Nav`, `Maker.clone(level, path, name)`,
  `kl_fa_loot survey/props/dress`, `kl_cover_vet scan`, `kl_cover_add plan/build`, `kl_fa_v2_park plan/test/check`, `kl_fa_fed build/plan --body auto|map|player`, `kl_map_escape.van_prepare/van_plan/van_build`,
  `kl_dm01cars_1025.cars`, `kl_arrivals_1024r2`, `kl_fa_rappel`, `kl_expansion.EXTRA/PAGES/ORDER`.
- Budget: F07 chunk table 35,101/35,102, limit 69,632, Retomoto 65,119 (campaign_fa_bank 190); 99/55 live-proven (actor_caps). The simple-sum 50,851 is conservative (M06_A measured 53,960 vs 25,504+35,101 = 60,605).

WRONG IN THE FIRST DRAFT (fixed above)
1. "Barricade at the ramp top": the two `Barikade_PRE` objects are at (-2660,-655,-70) and (-2660,-575,1440), in the low trench north of the start (the Truckland end), and one carries
   a PropaneTank. They are car-ram plugs. There is no data for a ramp-top barricade.
2. "Pre-pass drops the cover list / re-register it": false now. `kl_maps.PASSIVE` keeps `FFCoverList`; the reverse is the live risk (host list must be DROPped).
3. "Police arrive from the campaign's vans / ready roads": all 10 `ZHavokCar` and 35 `ZRoad` are under `AI_Players!` and are dropped. Only coordinates survive.
4. "`kl_dm01squads_chain.py` is the template": it is a DM01-only driver, and RunToCover/RandomTrigger/Flank appear in no DM01 tool (spec only). Real templates: `kl_fa_v2_park`, `kl_fa_hasta_police`.
5. "`kl_fa_blast.py` hangs on a timer, edits nothing": it is Retomoto-bound (fixed boxes at 5850,21150,-100 etc., kl_fa_author's blast timer). Copy the pattern.
6. Menu slot F05 is a paid-DLC slot; the free page-3 entries are F06 and F07.
7. Park II is not "unproven live": it has run many times (open_work_log L81/L82); the blast is owner-approved.
8. "M07 AI data not read": it exists (below).

NEW MEASUREMENTS (nav, `kl_pf4.convert(nav_of('M07_A'))`, 131 KB Dead Men block, bigger than Retomoto's M09_A 118 KB)
- 598 polygons, main part 520 (with the 30 drop links kept; 522 with `Nav(links=True)`), extent x -6092..2945, y -898..400, z -4117..12175. Walk start-area -> escape polygon = 124 m through 22 portals (a straight line is about 71 m).
- Hero_01 itself stands on a 2-polygon island (part of size 2, y -594); the nearest main-part polygon is 143 cm away and 140 cm higher. With `links=True` the island joins via a one-way drop. Heister and bot spawns must be placed on part 1.
- A 50-polygon island (x -9201..-4698, y 20..400, z up to 10,516) holds the SW car-park spawns (-5246,11194) and (-5054,10738); it is NOT connected to the main part even with links: cops spawned there cannot walk to the pit. Use only (-1100,394,9630), which is on the main part, or add nav.
- Off-mesh by polygon-middle distance: NE spawns (3661,-2226), (3567,-1205) about 12 to 15 m; SE spawns (7423,11331), (7274,11049) about 44 m (beyond x 2945). Cars drop men at the road end; the men then walk on, so a hand-placed unload point on the main part is needed for each lane.
- The south plateau (z 8000 to 12175, y 400 flat) has only 45 big polygons and about 13 cover boxes: cops there will be exposed unless boxes are added.
- Terrain: the pit is a long slope, floor y -520 (z 2000..3000) rising to 0 at z 6000 and +379 at z 7000..8000, +400..+670 at z 11000..12000, not a closed bowl. "Sealed by a barricade" was wrong; nothing seals it but the Truckland bound.

PROVEN vs GUESSED, updated: nav and cover list READ (above); round shape, blast object, lanes, dogs, cover recipe, engine music mapping all GUESS or unbuilt.

GO / NO-GO
- GO: Phase 0 survey and Phase 1 bare graft (low risk, M07 is the smallest campaign level, nav and cover list present, no `.prm` limit issue).
- NO-GO as a finished-round plan until: (a) wave lanes are re-authored on the main nav part (3 usable: NE after hand-placed unload, SW3 car-park point, one SE unload), (b) blast object is the z 1440 Barikade or an authored one, (c) cover is added on the plateau.
- FIRST BUILD STEP (spelled out), from `C:/kl-merge/kl-merge/tools`:
  1. Add to `kl_maps.HERO_AT` an `'M07_A'` entry whose source marker survives the pre-pass (check with `python kl_maps.py sides M07_A`; if none does, instead keep Heroes! at F07 and move the bare-test start with a one-line override). Target place for the bare player: a main-part polygon near the pit, e.g. (-2300,-454,3000) (polygon 100, part 1).
  2. `python kl_maps.py one C:/kl_build_1024/dig_research_1025a/gate1 F07 M07_A --campaign --heroes` (write only into scratch; the CLI takes out first).
  3. `python verify_levels.py`-style check for the new level (must report `problems: 0`), `python ../debug/check.py` on the output, then the chunk-table line from `kl_impact` (expected about 50 to 54k of 69,632).
  4. Only then (owner approval, F01 test slot or the new F06 page-3 slot) `kl_autotest.py`. Nothing here installs or launches anything.
