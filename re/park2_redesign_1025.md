# DM06B "A Walk in the Park II": redesign (design only, 2026-10-25)

Nothing was built, installed or launched. Read-only on the game folder. Scratch: `C:\kl_build_1024\park2_1025a`
(`live_F02_Main.zip` copy, `live_nodes.tsv` 20,605 rows, `dump_live.py`, `dump_dd.py`, `scan_dd.py`, `nav_q.py` = the mesh queries below).

Owner ask (2026-10-25): start on the highway bridge instead of the middle; go to the bridge where the current spawn is, as a "set up" with
a sniper and more cover; then back to the highway to escape; shootable vans (heisters, feds, AI); more things; DD campaign sound effects;
flat-raid style heists as a later idea.

Labels: MEASURED = read from the live zip / mesh by script today. DD-SEEN = found in DD stock levels by name scan. GUESS = not checked in game.

## 0. Pin and baseline
- Live `<DD>/KLExpansion/Maps/DM06B/F02_Main.zip` md5 `64bb5dc9ee15501904cff612dbea592d` (MEASURED 2026-10-25). Any stage pins on whatever the
  md5 is at build time; refuse on mismatch; backup tag `.before-1025park2`; `.prm` is 56,841,936 bytes (stock F07 63 MB, chunk table 69,632 is
  the wall, `re/engine_facts.md`), so the extras below add props only through donors that already share chunks (the DM02 recipe added ~0 .prm risk: check.py reads it).
- Live census (MEASURED): 58 actors / 38 squads (20 FA_Crowd civilians, 7 merc_bot_squad, 4 ring police squads = 10 men, 7 campaign squads = 21 men).
  Proven caps 99 / 55 (`re/actor_caps.md`), stock max 148 / 90.
- The flow today: pagoda inner room (z 2300) -> terrace -> causeway down -> garden (shrines, statues, z -2400..-8900) -> stair tower
  (foot (-1,580,-10940), top (106,2564,-10934)) -> ring road -> van (stop (-2572,2498,-7933)).

## 1. New heister start on the highway (MEASURED on the nav mesh, polygons 371..382, part 3 = the main connected part)
The ring is the highway. Only its arc from -180 to about -115 deg (and 165..180) lies on the main part: mesh height 2560 (at -180) down to 2348 (at -120).
From -105 deg round to +90 the ring is on a different part (part 0, y 2877..3522, a spiral ramp): NOT reachable from the park. So the start has to be on
the western arc. `ring(deg, r)` = (r sin, ., -100 + r cos), centre (0,-100); the mesh is on at r 8150..8450 (r 8000 is off it).

| Set | Points (x, mesh y, z), all five probes (centre and +-70 on both axes) inside the mesh | Facing |
|---|---|---|
| START x8, two rows of four | row A r 8200: (-6417,2379,-5205) (-6309,2383,-5338) (-6198,2387,-5469) (-6084,2391,-5597); row B r 8380: (-6558,2379,-5317) (-6448,2382,-5453) (-6334,2387,-5587) (-6218,2391,-5718) | along the road towards -180 (south-east): yaw to the stair tower (106,-10934) |
| TRAITOR x4 | (-5913,2400,-5911) (-5811,2405,-6013) (-5706,2408,-6113) (-5601,2411,-6212) | same |
| TEAM_MERC x8 | (-6700,2368,-4879) (-6616,2372,-4995) (-6529,2375,-5110) (-6783,2364,-4762) (-6798,2368,-4949) (-6712,2371,-5067) (-6625,2375,-5183) (-6881,2362,-4829) | same |

- Distances (MEASURED): start (-130 deg) to the van stop 4,533; to the stair top 8,485; the nearest police ARRIVE squad (angles +-168..176) is > 6,000 away round the curve.
- "Out of police sight": the ring is an open arc, so police are not placed on it before the alarm and the ARRIVE squads (10 men) only appear on the alarm
  (existing `POLICE_ARRIVE`, `BACKSTOP_AT=240`). Sight along the curve is GUESS. If a test shows the line from the stair top reaching the start, add two
  wrecked cars (F03 car donor, section 6) across the lane at about -150 deg.
- The `PLACE_FIXED` entries must move with the start (all GUESS, see `tools/kl_fa_v2_park.py` 148-165): `SpawnCam_000_A` camera over the new rows
  (e.g. (-6000,2700,-5000) looking at (-6300,2385,-5400)); `FASpecials!POI!*TheLootArea`, `EnterLootArea` stay at the pagoda (loot is there); the
  bots' first stage `EnterLootArea` is the pagoda, so the bots walk ring -> stairs -> garden -> pagoda: unproven, the bots' planner assumed start in the pagoda.
  `ExitLootArea` (now the stairs foot, before the pagoda in the new order) moves to the van stop (-2572,2498,-7933), plane 300 wide.
- `AFTER_DEATH` points (`ring()` in the file) stay: they were already on the ring. Keep >= `FED_CLEAR` 1000 from the boarding place; the START arc is
  4,500 from the van, fine. `LevelSpeak` trigger (stair top) fires on arrival now instead of the exit: leave it (it speaks when the crew reaches the top).
- Round-start event: the stock M06A start jingle plays as now. The alarm/van timing (`VAN_DELAY=8`) is unchanged.

## 2. Route and the ambush ("a set up") at the old spawn bridge
Geometry (MEASURED by mesh queries): the "bridge" is a causeway of mesh x 650..814 (about 360 wide, wider at z -100..-400: x 650..1000) that climbs from
the garden plaza (h 220, mesh x 200..1450, z -1800..-2300) to the pagoda hill: h 264 at z -1300, 339 at -900, 387 at -650 (the BRIDGE landing), 430 at -400,
473 at -100, 522 at 300, 584 at 900, the pagoda terrace at h 583..635 (z 900..2900).
Heisters now arrive from the south (garden), cross the plaza, then must go UP the causeway to the pagoda: the cops hold the plaza foot and a sniper
rakes the causeway from the pagoda terrace. Nobody guards the garden loot en route (shrines B1 B2 A1 A2 + statues 1..4 + tea house stay as now).

Ambush squads (all spawn awake at `START_AT`-style trigger OR are placed in cover from the load and held with `SM_HoldFire` until the crew crosses
a trigger box at the plaza's south edge z -2900: GUESS which is better; the stock "Bridge" squad `Gameplay!Enemy!01_Bridge!01_RetoMoto_Squad` shows the hold-fire pattern
(`15_SquadModifier_HoldFire`, `20_SquadModifier_Unleash`, `10_MiniCutScene_Hellfire`) and is reused as the template).

| Squad | Men | Position (nav checked: plaza h 220) | Behaviour |
|---|---|---|---|
| Plaza cops A | 3 | cover points (420,220,-2150) (700,220,-2250) (1000,220,-2200) behind parked cars | DefendBehaviour box (700,220,-2150) + RunToCover chain to the cars |
| Plaza cops B | 3 | (1250,220,-2000) (1400,220,-2150) (300,220,-2000) | flank pair, RunToCover with RandomTrigger |
| Plaza SWAT | 3 | (550,220,-1850) (850,220,-1850) (1150,220,-1850) shotguns, at the causeway mouth | `SM_Alert`, defend box on the mouth |
| Pagoda sniper nest | 2 | perch 1 (971,583,897) mesh poly 114; perch 2 (695,596,1075) poly 107 | see section 2.1 |

Cop rows in `kl_arms` use the `cop` / `swat` skill rows; skill/weapon pick is existing code. GUESS: all positions are plain mesh points, cover quality is
not checked (the existing `CoverBoxH/M` boxes sit in the garden at x -6375..-1735, z -530..1779; none near the plaza, hence the cars and props in section 5).

### 2.1 The sniper (DD-SEEN + MEASURED)
- DD campaign/FA sniper recipe: the only real sniper groups in stock FA are F08 `Gameplay!40_SWAT_Roof_Snipers` and F06 `030_swat_guarding_snipers`
  (re/dd_mechanics_catalog_1025.md corrects the "sniper 1" noise: `Projectile_Sniper_01` is a bullet template). F08, read today: group `ZSquadScript`
  (`eStayBack`, `eFragileAllianceUCC`, `eNormalAlertness`) with `DefendBehaviourRout` (one Pos box), a `SquadModifierBehaviour` (`eVIM_Factor_2_0`,
  `eCOM_DontUseCovers`, `ePreventDownNotDead`), a `RunToCoverBehaviourRout` with `RunToCoverPosInfoRout` nodes referencing each actor, and per man a
  `ZFFActor` + `ZSoldier` (`eArmy`, skill 50/50/50/175/50, health 5000, `Rifle_Type88_S`, animdb `Swat_02`). L04 has the same in the campaign (21 nodes).
- Weapon: `AllLevels/mainsceneincludes_multiplayer.zip\AllLevels/equipment.zip\Weapon\Rifle_Type88_S` (the scoped NPC rifle). The player rifle
  `Sn_Rem700` is a different template; do not use it for NPCs.
- Laser / glint: NONE found as a placed prop or effect in any DD level (name scan over L04 L11 F03 F08, MEASURED). `ZSniperLaserDisplay` plus HUD texture 183
  "sniper laser" exist, so any laser visible to the player is HUD-side (GUESS). So a tell has to be made by hand: a small `ZParticleTemplate` flare clone or a
  muzzle-glint from a lamp prop at the perch; not proven. Plan: no laser; give the sniper an audible tell instead (the radio line plus one `Rifle_Type88_S` shot
  fired at a stone near the crew on the first sighting, via a MiniCut "fire at" position like the Bridge squad's `PosObject_FireAt#nn`).
- Build: clone F08's squad group (2 men, 2 RunToPosInfo, SquadModifier) and re-point the Pos box and RunToPos to the two perches; swap the `RadioCom` sound id
  by name into the DM06B bank (the DM02 recipe). Range check: perch 1 to plaza centre (700,-2150) is 3,100 (rifle ok, GUESS); to the causeway landing 1,550.
- Perches stand on the mesh (polys 114 and 107, MEASURED) so the man can path/stand; sight lines unchecked: the terrace has the pagoda roof behind it (GUESS).
- Counter-play so it is fair: `SM_Alert`/`eVIM_Factor_2_0` (vision factor 2.0) means he sees 2x as far, kept; make him killable: perch 1 is reachable via the
  causeway and has a stair-side approach (poly 114 is connected to the main part), health stays 5000 (stock sniper value, GUESS how many shots that is in FA).

## 3. Loot
Unchanged positions, because they sit in the order the crew now meets them (MEASURED in the file): 5 garden items (tea house (802,175,-2456), shrines
B1 (122,184,-1619), B2 (-2020,180,-6024), A1 (-3346,188,-6454), A2 (1106,199,-11613)) and 4 statues (-539,-4741), (-1073,-4566), (276,-8748), (-354,-8962),
150,000 each; 6 pagoda cases at x 1240, z 2200..2550, 300,000 each. New order: ring -> stairs (A2 first) -> garden -> plaza (tea house) -> pagoda.
Change: the pagoda is now the end of the run with the heaviest loot, so the 6 cases stay; add the pagoda terrace as the sniper's. LOOT_CLEAR 400 from
every start holds trivially (starts are > 10,000 away). 14 cases on a route of about 20,000 units: GUESS the walk takes 70..100 s at sprint, so the round timer
and `BACKSTOP_AT=240` (police arrive after 240 s) are tight: raise the Backstop to ~300 s (GUESS, test it).

## 4. Escape back on the highway
- Same van: `Animation/F07/F07_Escape_Vehicle_01.zip`, group `EscapeVehicle_Animation_F07`, stop `(-2572,2498,-7933)`, arc `RING_R` 8244 (MEASURED/kept); it is
  hidden until the alarm and then drives in (VAN_DELAY 8). Exit trigger `Gameplay!EscapeSetup!otrExitLevel` unchanged.
- The new reason this works: the stairs top (106,2564,-10934) is 2,600 from the van stop along the ring, so the crew climbs, runs along the highway, boards.
  Police ARRIVE squads stand at -167..-176 and 168..175: they sit between the stairs top and the van, so the final stretch is contested (as designed).
- Loop back safety: nothing stops a crew that picks one case and runs back at once; fine (Fragile Alliance already allows leaving early).
- Shootable vans (the owner's complaint, `re/open_work_log.md` 2026-10-25 "vans audit"): in DM06B the van's FakeTarget controller was removed
  (`kl_fa_v2_park.py` ~469..480) so police never shoot it, and `FollowOutShield` is Invulnerable while aboard with 9,600 hp, so shots did nothing. Plan from the
  audit: restore FakeTarget (`--keep-faketarget` exists, never proven), hook an FX-only damage toggle, make a "Definite" damage state before boarding so smoke/sparks show.
  Not done here (needs the e8 hook proposal). Risk: if cops can shoot the van, a camping crew's van dies before anyone boards: keep the van invulnerable while
  `VAN_HIDE`d and only enable FakeTarget at the arrival (GUESS). The police cars (section 5) are the shootable ones in this map: stock DD parked cars are not.

## 5. More cover and set dressing (DM02 recipe, `tools/kl_dm02_mall_1025.py`, `tools/kl_interact_graft.py`, `re/dm02_mall_1025.md`)
| Item | Count | Where (nav h) | Source | Status |
|---|---|---|---|---|
| Police cars (F03 `V_Santana_CopCar`, with Lights_Siren nodes) | 3 | stationary at the plaza: (450,220,-2100) (1000,220,-2150) (1350,220,-1950), turned to face south | F03 MatPosAnim donor | DM02 built them as a driving lane with SWAT cells; a parked (zero-length lane) version is UNPROVEN, GUESS. The lane version needs a plaza entry out of sight |
| Concrete / metal barriers | 6..8 | plaza edge and causeway mouth, z -1900..-2300 | `PC310_F07_Metal_Barrier_A` (12 in F07), DD-SEEN | collision unverified: GUESS, check `Dumpster`/barrier has an `.HVK` shape |
| Dumpsters with `CoverBoxM` | 4 | pagoda terrace and causeway: (700,300?,..) pick on mesh | F03 `PC0700_F03_Dumpster_Metal_Close_05..08!CoverBoxM`, `Dumpster_A_01..04` (DD-SEEN) | a ready cover box comes with the prop |
| Kick doors | 2 | pagoda inner-room doorways (positions to be measured with the nav jamb-edge check used on DM02) | F03 donor, virtual host | DM02 recipe, doors drawn x6 there |
| Wall extinguishers | 4 | pagoda inner room walls and the terrace pillars, origin +100 above the mesh floor (`ext_lift` 100, DM02 lesson) | F04 donor | proven in the DM02 build 2 recipe, not run in game |
| Fuel cans | 4 | plaza, near the cops: (300,220,-2100) (1300,220,-2100) (700,220,-1800) (1000,220,-2400) | F03 donor | recipe proven, >= 900 from starts |
All extras go through `kl_interact_graft.build` and the DM02 `Built`/`census` helpers; chain: pin md5 64bb5dc9 -> new md5, stage INSTALL/UNDO .bat + .ps1,
`-Rehearsal -Game <scratch>`, `-DryRun`, refuse if kl2.exe runs, backup `.before-1025park2`.

## 6. DD campaign sounds that fit (DD-SEEN names; none reused yet)
- Police helicopter rotor loop: `...Helicopter_Controller\V_Police_Helicopter_00\RotorSound` (L04 `AI!Vehicles!27!Helicopter`; F08 `V_Enemy_Helicopter_Group\RotorSound`;
  F03/F08 `Gameplay!99_EscapeHelicopter#01\...\RotorSound`). Use as a distant fly-by on the ring at the alarm (a ZHeli prop is not needed; the ZSNDOBJ alone).
- Radio chatter: `Police_SWAT_01__*\RadioCom` ZSNDOBJ x8 (F07), L11 `RadioCom` on the Zone6 police squads (10+), F06 8: clone one per new squad (the DM02 recipe re-points the sound id into the DM06B bank).
- Megaphone: F01 `F01_Audio.zip\Audio!SFX!Police!PoliceMegaPhone_Street` (ZSNDOBJ), for the ambush trigger ("drop your weapons").
- Sirens: light nodes `Lights_Siren02`, `Siren_Blue_On03` on F03 cop cars (visual); the siren sound is hook-side `klambience` (`Siren` group), per `re/ambience_1023.md`.
- Wind bed for a high road: F08_Audio `Audio!Ambience!Roof_A_B_Wind_Ambience`, `Roof_B_Wind_Ambience` (ZSNDOBJ at 0,0,0 = global); traffic: no named traffic loop found in L04/L11/F03/F08, so a distant-traffic bed is GUESS (the hook `Distant` group).
- Explosions: fuel-can `Sound_bam`, extinguisher `Sound_bam` ZSNDOBJ come with their prop clones.

## 7. Budget (vs `re/actor_caps.md`, proven 99 / 55)
Live 58 / 38. Added: plaza cops A, B, SWAT = 3 squads / 9 men; sniper nest = 1 squad / 2; police-car SWAT cells (DM02 pattern) = 3 squads / 6 (DM02: 61/21 -> 67/24 for 3 cars).
New total about 75 / 45: 24 actors and 10 squads under the proven cap, 73 / 45 under stock max. `.prm`: props reuse donor chunks; run `check.py`, expect the chunk table untouched (DM02 added none).
If the airspace fails the memory wall (`re/actor_caps.md`: memory is the wall), drop the SWAT cells first (-6 / -3), then plaza cops B.

## 8. Risks / open questions (ordered)
1. Bots' planner assumes pagoda start (`EnterLootArea` first stage): wrong order for ring start. Mitigation: move the PIPs as in section 1; unproven.
2. Parked police cars via MatPosAnim: unproven; fall back to cars with a lane from out of sight.
3. Sniper sight lines and `Rifle_Type88_S` range in FA mode; no laser.
4. FakeTarget restore vs. camping crew destroying the van.
5. Round length with a 20,000-unit loot route (Backstop).
6. Part 0 ring (y 2877..3522) is unreachable on foot: the level bounds must exclude it (AFTER_DEATH uses `ring()` already, check those points are on part 3: angles -180..-120 only).
Later (owner idea, not designed): a "flat raid" heist as a mission type and DD FA maps made from campaign levels: needs L-level subtrees and a graft (`re/campaign_*` notes).
