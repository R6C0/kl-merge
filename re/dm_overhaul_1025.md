# DM map overhaul plan (2026-10-25) - PLAN ONLY, nothing built, installed or launched

Owner ask (10-25): apply the DM02 mall overhaul to the other maps (Hot Coffee II first), more props, DD campaign sound effects, shootable vans.
DM06B (Walk in the Park II: highway-bridge start, sniper, van explosion) is another workflow's job and is skipped here.
Rules for every stage below: build in `C:/kl_build_1024/overhaul_1025a`, pin on the CURRENT live md5 at build time (they change often),
installer = md5-chained INSTALL/UNDO .bat+.ps1 with `-Rehearsal -Game` and `-DryRun`, refuses if kl2 runs or the md5 differs, backup tag
`.before-1025overhaul`. Nothing in `KL_PortBackup` is touched. Guessed fields get a code comment.

## 0. Method (one builder chain, already proven on DM01 / DM02 / DM01B)

`kl_interact_graft` (kick doors, wall extinguishers with `ext_lift` 100 cm so they hang on the wall like stock, `spot_near` snaps to nav/geometry,
`virtual_host` for empty doorways) -> `kl_dm01b_gas_1025` (fuel cans / canisters) -> `kl_dm01cars_1025` (police cars + MiniCut SWAT cells, road side)
-> `resound()` (donor sound refs re-pointed BY NAME into the map's own bank, else 0 = silent) -> new sound pass (section 2).
Template with constants (DOORS / EXT_NEAR / FUEL / STOP / CELLS) and rehearse: `tools/kl_dm02_mall_1025.py`. New top groups are named `KL_*!`;
nothing existing is deleted; AIMonitor start list gets timer entries (Backstop 25 s, GUESS). Coordinates are NOT fixed in this plan: each is
read from the build (`B.at(k)`, nav mesh) and snapped with `spot_near`; the add-list below says WHERE (named area, anchor nodes) and HOW MANY.

## 1. Per-map state and add-list

Live md5 at survey time (re-check): DM01 c0e7b8ee, DM01B f2a70278, DM02 ae193d9c, DM03A 02e90dfa, DM06 f1f888c5, DM09 b76586a1, DM11B f896a376, DM05A 9638943a.
Census = (actors, squads). Proven 99 / 55, stock max 148 / 90, FA stock 57 / 36; memory (2 GB, int3 at 0x4a3060) is the wall (`re/actor_caps.md`).
Cops arriving from cars cost actors; extinguishers, cans, props, sounds cost none of that budget (only memory/.prm size).

| map | slot | nodes | census | headroom | ZSNDOBJ |
|---|---|---|---|---|---|
| DM01 Hot Coffee | F01 | 16514 | 68/31 | +31 actors | 169 |
| DM01B Hot Coffee II | F03 | 22850 | 91/58 | +8 actors, squads ok | 234 |
| DM02 mall | F02 | 24170 | 67/24 | +32 | 418 |
| DM03A vault | F07 | 21569 | 106/54 | none (past proven edge) | 444 |
| DM06 Walk in the Park | F04 | 16553 | 21/18 | large (+78) | 29 |
| DM09 Retomoto | F06 | 26961 | 99/56 | none | 631 |
| DM11B Hasta la Vista | F04 | 21352 | 43/24 | +56 | 110 |

### 1.1 DM01B Hot Coffee II (priority)
Has: KL_CoverMore!, KL_Interact!1 (5 kick doors + 4 wall extinguishers), KL_Gas!1 (3 fuel cans + 2 extinguishers, garage hall), garage-door
tear-gas lists. Own M01 ambience in bank (street_city_3d, warehouse, ventilation). ZTrafficFlow 3, ZAnimatedVehicle 1, no police cars.
Add:
- Police cars: 2 cars on the street/road side of the garage hall exit (not 3: only +8 actors), 4 SWAT total from the MiniCut cells, arrive on the
  first assault timer; use the DM01 cars recipe (`re/dm01_cars_1025.md`), cars from F03 donor (this map's own slot, no cross-level model graft).
- Extinguishers: +3 wall ones in the corridor/office side (total 9), 100 cm lift. Fuel cans: +2 near the loading bay (total 5). Both cost no actors.
- Kick doors: +2 on the office side doors that have nav on both sides (check nav first, DM03A lesson: a door on a cut-off nav island is dead).
- Cover: +10 collision props (crates, pallets, barrels) on the approach to the escape in the garage hall, taken from the map's own prop pool
  by clone (as KL_CoverMore!); clutter +8 non-collision props (boxes, bags) around loot rooms.
- Sound: section 2 street bed (distant sirens, traffic horns), police-car siren on the arriving cars, RadioCom on the SWAT cells.

### 1.2 DM03A vault (F07)
Has: KL_Interact!1 (5 doors, only door 1 wired; doors 2..5 are on a cut-off nav island), KL_Gas!1 (3 canisters), KL_SWAT!1 / KL_SWAT!Door_1 (3 men, 75 s).
Census already 106/54, so NO new actors. Add only free things:
- Extinguishers +3 (wall, in the lobby / stair hall), cover +8 collision props in the vault approach, clutter +10.
- Fix: wire a second SWAT door only if a nav-connected door exists (survey first); otherwise skip.
- Sound: PlayMusic 2 and PlayMusicLayerFade 35 already exist (keep). Add siren + radio chatter from in-bank clips (section 2).

### 1.3 DM06 A Walk in the Park (F04)
Has: KL_CoverMore!, KL_Interact!1 (extinguishers; no separable door leaf so kick doors need a model graft: skip). Census 21/18, sound-poor
(29 ZSNDOBJ; has ZHeli 2, ZTrafficFlow 2, SoundSpline 4, water drips). Most room for actors.
Add:
- Police cars: 3 cars on the road edge toward the escape with SWAT cells (6 SWAT), staged on a timer and on loot pickup; +12 actors.
- Cover: +16 collision props (benches, planters, low walls) along the open park path; clutter +12.
- Fuel cans: 3 near the maintenance/service area (donor F04 gas canisters: map is in the F04 slot, no cross-level graft).
- Dogs: 1 on the escape path (dd_mechanics_catalog section 1; unproven, M effort), last item.
- Sound: biggest gain here: the park is nearly silent. Bank already has M06 car_honk_1.., chopper_bell_rotor; add traffic, birds, sirens
  (section 2), tie chopper_bell to the existing ZHeli.

### 1.4 DM09 Retomoto (F06)
Has: KL_Rappel!, KL_RopeVis!, KL_CoverMore!, KL_Interact!1; round-start blast, Japanese megaphones (hook), 15 music clips. 99/56: no actor room.
Owner's own design (CLAUDE.md "Stage 1 wish") overrides this plan wherever they conflict. Add only free props:
- Cover +10 collision props in the lobby/street part (cars, planters, barriers: Heat street shoot-out), fuel cans 2 at the street, extinguishers
  +3 in the offices, clutter +10 on the office floors. Police cars on the street for the van escape need ACTORS: only by trading squads out
  (not planned; owner to decide).
- Sound: street part gets traffic + siren bed; keep Retomoto level music.

### 1.5 DM11B Hasta la Vista (F04)
Has only KL_CoverMore!; escape chopper, `plop` late police wave (kl_arrivals_1024r2). ZHeli 1, 130 rigid bodies. 43/24.
Add:
- Extinguishers 5 (wall), fuel cans 4, kick doors 4 (nav-check first), 2 police cars with SWAT on the road (+8 actors), cover +14, clutter +10.
- Sound: harbour/street bed from the campaign (L07 harbour, L11) via merge; chopper flyover tied to the existing heli.

### 1.6 Reference (already done)
DM01 (3 kick doors, 5 extinguishers, squads, 3 cars/6 SWAT, cover; installed). DM02 mall extras STAGED not installed (stage2 a8216b38: 6 kick doors,
6 wall extinguishers, 4 fuel cans, 3 police cars + SWAT). DM05A: lastcall5 staged (`CLAUDE.md` Open work). DM06B: other workflow.

## 2. Sound plan (DD campaign sound effects)

Mechanism. Every sound reference is a byte offset into the level's .SND (in the zip). .WHD/.WAV sit beside the zip. Streams live in PC_Def.str.
Placed emitter: `ZSNDOBJ` (field `ZSNDOBJ[0]` = sound id). Controllers that play it: `Audio_PlaySound` (field 0 = ZSNDOBJ id), `Audio_AttachToGeom`,
`SoundLimiterFade`, `SoundVolumetricSource`, `SoundVolumetricRandom`, `SoundSpline`/`SoundSplineFollow` (never run by a DD level: medium risk, do not use first),
`PlayMusic`/`PlayMusicLayerFade`, `Audio_ReverbActivater`.

Tier A, NO merge (already in the DM map banks; reuse by name via the `resound` pattern): police sirens (`siren_01..`, f07 sfx/sirens), PoliceRadio
(21 to 28 lines), traffic horns (`horn_01/05/10..`), dog bark/growl, M01/M06 own beds, chopper_bell. Plan: clone a ZSNDOBJ + `Audio_PlaySound`
pair (clone source: the DM02 assault used Box_crash_sound from F04) on each arriving police car, each SWAT cell (RadioCom), and as 3 to 6 ambient
emitters per map at street spots. Pure data, no .SND change. Do this FIRST.

Tier B, needs `kl_snd.merge` from a DD campaign bank into the DM map bank. The DM banks contain NO DD campaign `level_NN` ambience (only
`level_10/environment/chopper_bullet_impacts`). Candidates (names from `kl_snd.bank('Lxx','dd')`, scratch in `C:/kl_build_1024/overhaul_1025a/lbanks.json`, `lan.txt`):
- L01: `level_01/environment/window/carhorns/horn_01..37`, `enviromentspline/vehicles/sirens_looped` (04/05/07/08/10), `chopper_bell` (rotor, flying), `all/environment/vehicles/traffic` (bus/truck/3wheel running, car_horns#set).
- L02: `panic_screams` (screams_*), `sirens_looped` 01..08, `ambience/outside_default_3d_01`.
- L03: `moped_horns`, `bird_warbler`, `ambience/outside/openarea_01`.
- L04: `ambience/outside` (alley_01, alley_3d_amb_01, crowded_street_01, openarea_01), megaphone_01 lines (go_go_go, back_back_back, move, evacuating), `police_siren` (oncar_01/02), `car_idle`, `all/environment/vehicles/choppers` (chopper_flying_01/02, windrumble_01..10, police_helikopter#seq).
- L06: `city_rain_01`, `alleyambience_rain`, dog/germanshepherd bark, `sirens_looped_for_streets_03/04/09`.
- L07: `megaphoneshout_01..06`, harbour/hangar/crane, rain loops. L08: train horn. L10: `chopper_flyby`, `panic_screams#set`, wind. L11: planes, luggage.
- `all/environment/vehicles/cars/master/car_alarm` (alarmcar#seq), `all/environment/alarms` (L09, L10).
Per-map pick: DM01B / DM03A / DM09 street = L04 crowded_street + police_siren + L01 horns; DM06 = L03 openarea + bird_warbler + L01 traffic;
DM11B = L07 harbour + L10 chopper_flyby; every map = one megaphone line set (L04/L07) on the SWAT entry.

Merge path (same-game dd to dd, needs no strmap): `kl_snd.merge(base, src, base_whd, base_wav, src_whd, src_wav, roots)` returns new .SND, .WHD,
.WAV and an offset map; two packages as in `tools/kl_club_music2.py` (package A = .SND/.WHD/LS.SND members + beside-zip .WHD/.WAV; package B = the .prp
with new emitters), both pinned on members/files; `kl_zip_member.py replace/md5/same` swaps the member. UNPROVEN: no existing caller merges an L bank into a
DM bank (music2 merges for the club). First step of the sound stage is a rehearsal that merges ONE small clip into DM06 and checks the offset map and
that every pre-existing sound id still resolves (md5 chain; abort otherwise). Risk: .WAV size growth (keep each map under ~10 MB added, GUESS) and
streamed clips (PC_Def.str) not copyable this way: pick non-streamed `#sound` entries only.

Hook side (`klhook/klambience.c`, groups Radio / Alarm / Heli / Distant / Siren / Spot / Local / Panic; `re/ambience_1023.md`, `re/sound3_1023.md`) is
independent, toggle-based, default off, and unheard so far. Map emitters complement it; do not double up the same clip in both (owner toggles: every
feature a toggle, labelled recommended on/off).

## 3. Shooting the vans (owner: "make sure you can shoot the vans; feds and AI too")
Unverified claim from the owner that the van does not blow. Existing: `kl_blowup.py` (NOTE vanblow 10-24, DM data pass staged), `VehicleEffects`
BlowupChance, `kl_fa_carfx`. Plan (research + one offline check, no live run): confirm the escape van has a ZHavokRigidBody hit target with a
health/BlowupChance node and that AI weapon damage (feds, bots) uses the same hit path as player bullets (bots_down.md hit path); write the finding
into `re/vanblow` notes. DM06B's van is the other workflow's.

## 4. Research items from the owner (not built)
- "Flat raid" heist and DD FA maps built from campaign levels: needs a graft-in-reverse (DD campaign L-level -> FA systems); candidates by size from
  the L census; start with a feasibility note (spawn/loot/escape authoring from `kl_fa_author.py`, systems swap like the DM graft). Do not start before
  stage 1 maps are signed off (CLAUDE.md order).
- Dogs: dd_mechanics_catalog section 1, one-dog test on DM03A (but it has no actor room: test on DM06 instead).

## 5. Build order and gates
1. DM01B extras (cars, 3 extinguishers, 2 cans, 2 doors, cover/clutter) + Tier A sound. Verify: `verify_levels`-style census (<= 99/55), `debug/check.py`.
2. DM06 extras + Tier A sound; then Tier B merge rehearsal on DM06 (one clip).
3. DM11B, then DM03A and DM09 (free props and sound only).
4. Each stage: rehearse `-Rehearsal -Game`, `-DryRun`, one INSTALL + UNDO pair per map, tag `.before-1025overhaul`; install only on the owner's go.
Risks: all items "not live-tested"; nav islands (kick doors), actor memory wall, merge unproven, SoundSpline unproven, cars on a DM nav mesh.
