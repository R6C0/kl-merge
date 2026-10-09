# Retomoto Tower: the window blast, "volatile like the Subway one"

2026-10-09, agent t-blast. **Offline only**: nothing was installed, the game was not started (the
owner was playing). Tool: `tools/kl_fa_blast.py`. It sits on top of `tools/kl_fa_author.py` (the
sequence: bomb armed at 9 s, blast 4 s later, re/retomoto_fa.md 11.2) and `tools/kl_fa_street.py`
and edits nothing of either. Owner, 18:40, after the balcony start (`<work>\build\play2`): *"i want
the explosion to be a bit more volatile like the subway one in the original game when u start in -
it does the explosion but not smoke or anything or camera shake"*.

Words: **read** = read off the level files or kl2.exe (address given); **GUESS** = a value of mine;
**ASSUMPTION** = fits the evidence, not proven; **LIVE** = only a run can settle it (section 7).

    python tools/kl_fa_blast.py test <out> --keep [--blast 0.5|1.0|1.5] [options]   build + verify + read back (12 min)
    python tools/kl_fa_blast.py report <archive>      the blast of a built level: objects, what they name, timeline
    python tools/kl_fa_blast.py subway                stock F01's breach, object by object
    python tools/kl_fa_blast.py selftest              the controllers this file writes against stock ones (20 s)

## 0. Result

- **Why there was no shake** (established): nothing in the level shakes a camera. `Explode` has no
  shake of its own in Dog Days (2.2); the campaign shook from a cutscene camera that went with the
  campaign; host F07 has neither of the two controllers that do it.
- **Why there was no smoke** (half established): the bomb's particle group is Dead Men's glass burst.
  It is complete in the archive and by its own templates would leave a 7 m dust cloud for 30 s - the
  owner saw none, so it does not draw; why not could not be found offline (2.3). Subway's own cloud
  cannot be borrowed: its two templates are in F01's map, not in the systems (1.3).
- **Added**, the Subway way and with stock objects only: the rocket's `ShakeCamera` with Subway's
  values (3.0 / 80 m; 2.6 - 3.5 times Subway's strength where the heisters stand, because they stand
  6 - 9 m away and Subway's stand 29 m away), Subway's hand-held-camera event (`DocuCamControl`
  'OnExplosion'), two fireballs with smoke, sparks, debris and a flash light (the rocket's cluster)
  inside the bay, a debris and spark spray out over the balcony, two glass jets, the rocket's
  explosion sound. All harmless. One knob: `--blast 0.5 / 1.0 / 1.5`.
- `test <work>\build\t_blast --keep`: **PASS**. 25,731 entities, 22 rooms, 313 MB;
  `kl_graft.verify` 1 problem, the known one ("39 particle template names do not resolve (stock
  M09_A: 36)", unchanged from the build without this layer); `kl_fa.check` 0 CRASH / 0 BROKEN
  (1 DEGRADED, no bots); `kl_fa_street.report` 0 faults; this file's read-back 0 faults (5).
- **Not done**: a thick cloud that hangs for many seconds. The systems' clusters give about 4 s of
  smoke. A longer one needs loose emitter nodes, and no kept part of the level has any (8).

## 1. How Subway does it (stock F01, `python tools/kl_fa_blast.py subway`)

All read from stock `F01_Main` (KL_PortBackup). Positions are world, in cm.

### 1.1 The chain

| object (all top-level `Gameplay!Blowout!...`, ZBoxPrimitive) | controller, values | does |
|---|---|---|
| `Gameplay!AIMonitor` | `AIMonitor` list 2 -> `tdExplosion`, `tdCivilians`, 6 others | the round-start event (the countdown's first second) |
| `tdExplosion` | `TriggerDelay` 3 -> the two boxes, `mpaBombFlash` | **3 s** after the event |
| `TriggerBox_DocuCam_Explotion_Mercs` / `_UCC` at (1399 -1726 13380), half (1860 171 1221) | `TriggerBox` field 0 = 0 (off until named), ECPS_FA_MERCONLY / UCCONLY -> `DocuCam_Explotion`, `awSoundAndSmokeEFX` | the boxes cover the spawn: whoever stands there starts the rest |
| `DocuCam_Explotion` | `DocuCamControl` 'AITrigger', 'OnExplosion' | **the camera jolt**: every local player's hand-held camera plays profile 23 (kl2 0x718a80 -> player 0x507380) |
| `awSoundAndSmokeEFX` | `AIDWrapper` 'Activate' -> 3 emitters, 4 sounds | **the cloud and the bang** |
| `mpaBombFlash` | `MatPosAnimProxy` -> `DL10_Spawn\Flash_FX` (a ZSTDOBJ with `MatPosAnim`), then `dgBombFlash` | the flash card |
| `dgBombFlash` | `DeactivateGeom` -> `DL10_Spawn\BombFlash` (ZOMNILIGHT, hidden at load) | switches a light off that nothing switches on |
| `scExplosion` at (151 -2556 16286) | `ShakeCamera` 3.0, 'Activate', 1, 8000.0 | **named by nothing**. Its field 2 = 1 makes it shake when the object starts (kl2 0x48ed30), not at the breach |
| `tdCivilians` | `TriggerDelay` 1 -> nine civilian mini-cutscenes | 1 s: people run and scream |

No `Explode`, no physics impulse, no second pop: one moment, 3 s into the countdown.

### 1.2 The cloud and the bang

| object | at | values | template |
|---|---|---|---|
| `...DL10_Platform\Particle_Blowout_01\BlowOut_Emitter_01` | (401 -2245 15940), 23 - 27 m from the START points | box 280 x 100, one particle every 0.0143 s for 3.5 s (245), speed (0 0 350), cone 170 | `BlowOut_01`: life 3.6 s, size 450 |
| `...\BlowOut_Emitter_01_stair2` | (1787 -2245 15940), 26 - 31 m | the same | `BlowOut_01` |
| `...\BlowOut_Emitter_02` | (401 -1674 14469), 8 - 12 m | box 250, every 0.0067 s for 3 s (450), speed (0 0 -300), cone 67 | `BlowOut_02`: life 5 s, size 450 |
| `Audio!SFX!Wall_Explosion_Sound`, `#01`, `#02`, `#03` (ZSNDOBJ, hidden at load) | 9 - 24 m | three different sounds, all at once | - |

So Subway's cloud is 940 grey sprites of 4.5 m, fed for 3.5 s, gone after about 8 s, rolling at
3 m/s towards the players. (Emitter fields 3 / 4 as "interval / duration" and template fields 2 / 4
as "life / size" are ASSUMPTIONS from the values: a blast flash has 0.2, debris 2, the numbers of
1 / 70 and 1 / 150.)

### 1.3 What of it exists on Retomoto (host F07's systems are kept by the graft)

| Subway's | in F07 / the built level |
|---|---|
| templates `BlowOut_01`, `BlowOut_02` | **no**. They are in F01's map (`...F01_LOC_Inside.zip\DL10_Vault\Template_storm_01`); F01 has 9 templates F07 lacks, F07 none F01 lacks |
| loose `ZParticleEmitter` nodes to place | **none**. F07's emitters are in its map (1135, dropped), its vans (153), the mercs' arrival van (49, dropped) and the systems' clusters (2997 + 377). Dead Men's are conversions (2.3) |
| `DocuCamControl` | none in F07 (class and the 21 `DocuCamProfile` are in the systems: usable) |
| `ShakeCamera` | only on the two rocket templates (0.5, 'EXPLODE_Explode_Impact', 0, 4000) |
| explosion clusters | **yes**: `ZAllocMany` groups under `...\Effects/BulletImpacts.zip`, in every level, spawned by an `Explode`'s field 8 (the rocket: `Grenade\FX_Grenade_RPG_01`) |

## 2. What Retomoto had

### 2.1 The objects (`<work>\build\play2\F01_Main.zip`, read)

| t | object | values | does |
|---|---|---|---|
| 9 | arm timer -> `AIDWrapper` 'Activate' -> `WindowBlowup!BombWindow03` (ZLNKOBJ, **hidden**, (5867 21094 -66)) | `Explode` 1, 1, 200, 2000, 3000, 1, 0, 'Activate', -> `Particles_M09_BigWindow`, **4.0**, 1, `bomb_warmup`, `m09_explosion_window_office_01`, 10, 0, 0, 1, 0 | warm-up sound, 4 s fuse, then: explosion sound, particle group, tinnitus within 20 m |
| 13 | blast timer -> glass wrapper | 'ForceTriggerShotActivate' -> the intact window | glass swap + `Glass_Break_Big` |
| 13 | -> `Activator_KillGuyNearWindow` -> `WindowBlowup!InvisiBomb` (5685 20997 -394) | `Explode` 300, 100, 200, 1000, 200, 1, 0, 'Activate', **''**, 0, 0, 0, 0, 10, 1, 0, 1, 0 | kills the guard at the glass. No particle group, no sound |
| 13 | -> chairs, doors, music, the three room squads, `TriggerBox_FallingDebris` | | as re/retomoto_fa.md 11.2 |

Dead Men stored 15 values on the bomb (600, 400, 2000, 3000, 0, 'Activate', group, 4.0, 1, sound,
sound, 10.0, 0, 0, 1); Dog Days' `CExplode` has 18. The three new ones got the most common value
(field 2 = 200, field 5 = 1.0, field 17 = 0; re/pairings.md). None of the 18 is a shake.

### 2.2 `Explode`, `ShakeCamera`, `DocuCamControl` in kl2.exe (read with debug/dasm.py)

`CExplode` (vtable 0xbc1eac; fields in declaration order at object +0x34..+0x6b):

| field | use |
|---|---|
| 0, 1 | two radii. 0x60b230 hands both, with fields 2, 4, 13 and bool 14, to 0x8ec590 (damage and pushes; fields 1, 2, 4 inside it not read). Field 0 is also the half size of the physics query, and the scale of a 5 s per-player effect of strength 1 - (d / field 0)^2 (0x60b540..0x60b637 -> 0x590170; what draws it, 0x82c210, not read) |
| 3 | tinnitus radius: a local player nearer than this gets 0x742320(10) unless the option 'DisableTinitus' is set (0x60b3c8..0x60b406) |
| 6 | explode when the object starts, if it is not hidden (0x4eaf00, 0x5884f0) |
| 7 | its message. The handler (0x5589d0) also takes a second, built-in message whose argument becomes the attacker; its name was not found |
| 8 | the particle group: must be a `ZAllocMany` (an int3 at 0x4eaf33 if not); one copy is spawned at the object's place and turn (0x60b4c3..0x60b514) |
| 9 | fuse. > 0: play sound 11 and explode this many seconds later (0x8fb660, tick 0x682c70); 0: at once |
| 11, 12 | sound during the fuse, sound of the explosion |
| 10, 15, 16, 17 | bools: 10 calls the node's slot 21 after the explosion; 15: a player within 2 x field 0 gets a message (0x5022c0); 16, 17 not read |

So kl_fa_author's "harmless" (fields 0 / 1 = 1) also switches off the physics pushes and the 5 s
effect - but with the campaign's 600 the START points (616 - 878 away) are outside that as well.

`ZShakeCamera` (vtable 0xbc220c, `ff2\levelsetup\shakecamera.cpp`): fields 0 strength, 1 message,
2 "also when the object starts", 3 radius. On its message (0x5e9bc0 -> 0x6124e0) it sends
'msgShakeCamera' {field 0, its own world position, field 3} to the camera of each local player. The
camera (0x5de4b0 -> 0x756c20): nothing if the player is at or beyond the radius; else amplitude =
strength x 25 x (max(d, 5 m) / 5 m) ^ -(ln 10 / ln(radius / 5 m)) - full within 5 m, a tenth at the
radius - started d / 75 m + 0.05 s later, **0.3 + 0.5 s long whatever the values** (0x704e60), with
the pad's rumble. `kl_fa_blast.shake_at()` is this formula.

`ZDocuCamControl` (vtable 0xbc715c): fields 0 message, 1 profile (enum ETYPE, 41 names: 'OnExplosion'
= 23, 'OnElevatorFall', 'OnHitFromLeft' ...). On its message every local player gets
0x507380(profile, 1.0): the hand-held camera's own reaction.

Messages reach a hidden entity as well: Subway's four sound objects are hidden at load and are
started by 'Activate'; the path from a list to a controller (0x6d2d10 -> 0x7592e0 -> 0x446010) has
no test of the hidden bit.

### 2.3 Why no smoke

The bomb's group, followed into the archive (`kl_fa_blast.py report`, all present):

| emitter | particles | template (`Locations/M09_A/Effects.zip\Template_M09_BigWindow_Shatter_01`) | life s | size | sprite texture |
|---|---|---|---|---|---|
| Emitter_GlassDebris_01 .. 04 | 4 x 200 | Debris_BigWindow_M09_01 / _02 | 2.5 | 20 - 30 | FX_Par_Debris_Glass_03 / _04 |
| Emitter_GlassSplinters_01 | 300 | GlassDust_BigWindow_M09_01 | 0.5 | 100 | FX_Par_Dust_Glass_01 |
| Emitter_GlassSmoke_01 | 100 | Smoke_BigWindow_M09_01 | 0.7 | 300 | Fx_Par_Smoke_Old |
| Emitter_GlassDust_03, _04 | 2 x 50 | Dust_BigWindow_M09_02 | 5 | 300 | Fx_Par_Smoke_Old |
| Emitter_GlassDust_01 | 50 | Dust_BigWindow_M09_01 | **30** | **700** | Fx_Par_Smoke_Old |
| Emitter_FrameDebris_02, Emitter_Flash_01 | 1, 3 | DebrisFrame_..., Flash_BigWindow_01 | 2, 0.2 | 10, 900 | ..., Fx_Flash_Impact_03 |

- It is a glass burst with dust, and it is whole: field 8 resolves to the `ZAllocMany`, its clone
  group is in the level (1 copy), all 11 emitters find their template, every template's sprite chunk
  (.prm lType 2) names a texture the .TEX has. Particle templates draw sprites, not material
  instances, so `kl_light.missing_shaders` has nothing to say about them (checked: all sprites).
- If it drew, 50 sprites of 7 m would hang at the window for 30 s. The owner saw nothing (frames
  `research\watch\20261009_180847\0043_304s.jpg`, `0044_311s.jpg`: glass on the floor, clear air).
  **So the group does not draw. Why is not established.** What was checked and is fine: every
  non-float field of its 11 emitters holds a value some systems emitter also has; the converted
  values look like Dog Days' own bursts (count, cone, speed along +Y). What separates it from a
  Dog Days cluster: (a) its emitters and templates are conversions (`ZParticleEmitter`: four fields
  moved, re/pairings.md A; `ZParticleTemplate`: same offsets), (b) it is spawned by a hidden entity
  with a fuse - nothing else in the level is one, (c) the build's note "dynamic lists name
  different classes; kept F07's" (the list that pre-sizes heaps for run-time objects) was not
  followed. `--blast-bomb-native` separates (a) from (b) in one run (7).

### 2.4 Why no shake

Nothing sends one. The campaign's shake was `Characters!Hero!CameraControl\Cam_Explosion`, a
`MiniCutsceneRout` holding a camera profile with 'effect Shake', named by the campaign's 4 s timer:
a cutscene camera, dropped with the campaign and of no use to a Fragile Alliance player. The bomb's
`Explode` cannot shake (2.2). F07 brings no `DocuCamControl` and no `ShakeCamera` outside its
rocket templates.

## 3. What is added (`tools/kl_fa_blast.py`)

No new entity. Six spare helper boxes of F07's shutter script (single top-level ZBoxPrimitive nodes
at (10000 0 10000), named by nothing that stays) are kept, re-placed and given other controllers:

| role | F07 box | at | controllers | particle group |
|---|---|---|---|---|
| fan | `...Shutters!Activator_Shutter_LEFT` | (5850 21150 -100) | its own `AIDWrapper`: 'Activate' -> the boxes below that are on; + `DocuCamControl` 'AITrigger', 'OnExplosion' | - |
| cloud | `...!Activator_Shutters_RIGHT` | (5650 21000 150), 2 m inside, north half | `Explode` | `Grenade\FX_Grenade_RPG_01` + the rocket's sound |
| spray | `...!Activator_Shutter_Close_LEFT` | (5800 21150 -100), turned outward | `Explode` + `ShakeCamera` 3.0 x BLAST, 'Activate', 0, 8000 | `Rocket\Rocket_Default_01` |
| glass s | `...!Activator_Shutter_Close_RIGHT` | (5850 21300 -330), outward | `Explode` | `Bullet\Glass_Exit_01` |
| glass n | `...!TimerShuttersOpenDif` | (5850 21300 130), outward | `Explode` | `Bullet\Glass_Exit_01` |
| second | `...!TimerShuttersClose` | (5400 21000 -100), 4.5 m inside | `Explode`, fuse SECOND | `Rocket\Rocket_Default_01` + the rocket's sound; **off** by default |

and the campaign's `WindowBlowup!InvisiBomb` gets `FX_Grenade_RPG_01` as its particle group (the
explosion that kills the guard at the glass is now seen; it had '').

- **The route is stock's, link for link**: kl_fa_author's blast timer (`TriggerDelay2`) names the
  fan; an `AIDWrapper` sends 'Activate'; an `Explode` / `ShakeCamera` takes it. That is F01's
  `tdExplosion -> ... -> awSoundAndSmokeEFX` 'Activate', and the rocket's `Explode` + `ShakeCamera`
  on one node and one message. The `DocuCamControl` is F01's `DocuCam_Explotion` token for token.
- **Tokens**: `Explode` and `ShakeCamera` are cloned from stock F07's `Rocket_RPG7`; of the rocket's
  18 `Explode` values eight are changed (radii 500 / 150 -> 1 / 1, tinnitus 1000 -> 0, message,
  group, fuse, the two sounds), the rest stay the rocket's (`selftest`).
- **Harmless**: both radii 1 - kl_fa_author's own way for the bomb - and no tinnitus. Whatever
  `--blast-real` does to the bomb, these stay pictures and sound.
- **The clusters** (each emitter shoots along its local +Y; "outward" turns that to world +x):

| cluster | copies that can play at once | used | shows |
|---|---|---|---|
| `FX_Grenade_RPG_01` | 3 | 2 (cloud, InvisiBomb) | fireball 45 sprites of 5 m (1 s), smoke 25 of 5 m (**4 s**), sparks 100, debris 75 + 75, a blast flash, an omni light that fades in 3 s (`ParamAnim`) |
| `Rocket_Default_01` | 4 | 1 (2 with `second`) | debris 400, sparks 500, fire, a light: a half sphere round +Y |
| `Glass_Exit_01` | 30 | 2 | glass 25 + 25 + 30, dust, smoke: a narrow jet (small - a bullet's exit hole) |
| `Concrete_02` | 15 | with `--blast-no-fire` | concrete smoke, debris, pebbles, a puff that stays 6 s (small) |

- **The knob** `--blast X` (GUESS throughout): shake strength 3.0 x X; below 0.75 the `cloud`
  fireball is left out; from 1.5 the `second` pop comes 0.5 s later. `--blast-second S`,
  `--blast-no-fire`, `--blast-quiet` set those parts alone.

| | shake field 0 | factor at the START points | against Subway (0.70) | fireballs | second pop |
|---|---|---|---|---|---|
| `--blast 0.5` mild | 1.5 | 0.92 - 1.22 | 1.3 - 1.7 x | 1 (InvisiBomb) | - |
| default 1.0 | 3.0 (Subway's) | 1.84 - 2.45 | 2.6 - 3.5 x | 2 | - |
| `--blast 1.5` heavy | 4.5 | 2.75 - 3.67 | 3.9 - 5.2 x | 2 | at 13.5 s |

- **Idempotent, and nothing else moves** (5): `prepare_host` twice = once; `wire` twice = once;
  every knob set and set back returns the scene to the build's.

## 4. Side by side

| | Subway (stock F01) | Retomoto before | Retomoto after (default) |
|---|---|---|---|
| when | 3 s after the round-start event (during the countdown) | 13 s (5 s after GO), by the owner's design | unchanged |
| started by | `AIMonitor` -> `TriggerDelay` -> two boxes round the spawn -> wrapper | `AIMonitor` -> arm timer -> bomb (fuse 4); -> blast timer | + blast timer -> fan (`AIDWrapper`) -> 4 boxes |
| bang | 4 sound objects, 3 sounds, at once | `bomb_warmup` from 9 s, `m09_explosion_window_office_01`, `Glass_Break_Big` | + `rpg_explosion_01` (the rocket's) |
| smoke / dust | 940 grey sprites of 4.5 m over 3.5 s, gone after ~8 s | the Dead Men group: not seen (2.3) | + 2 x 25 smoke sprites of 5 m, 4 s (the two fireball clusters); the Dead Men group stays as it is |
| fire | none | none | 2 fireballs (45 sprites of 5 m, 1 s) + blast flash; `--blast-no-fire`: none, small dust instead |
| debris | none (rubble later, in the vault) | the Dead Men group's glass (not seen); the blown window's own glass on the floor; a pillar 5 s after the first heister walks in | + 400 debris and 500 sparks sprayed out over the balcony, 2 x 150 debris from the fireballs, two glass jets |
| flash / light | a flash card (`Flash_FX`); the omni light is never switched on | the Dead Men group's flash sprite (not seen) | + 2 omni lights fading over 3 s, 2 blast flashes (in the clusters) |
| camera shake | `ShakeCamera` 3.0 / 8000 exists but is named by nothing (it fires when the object starts) | **none** | `ShakeCamera` 3.0 / 8000 at the bay: factor 1.84 - 2.45 at the heisters (Subway's object would give 0.70 at its players) |
| hand-held camera | `DocuCamControl` 'OnExplosion' | **none** | the same controller, the same values |
| tinnitus | none (no `Explode`) | within 20 m of the bomb (field 3 = 2000): all START points | unchanged |
| pushes on physics objects | none | none from the bomb (reach 1); within 3 m of the InvisiBomb | unchanged |
| harm to the heisters | none | none (bomb reach 1; InvisiBomb 3 m, they stand 4.3 m+ away) | unchanged; the added boxes have reach 1 |
| set dressing | 9 civilians run, 2 guards lie dead, train passes | chairs thrown, door broken, the guard at the glass dies, music starts | unchanged |

## 5. Offline test

`python tools/kl_fa_blast.py test "<work>\build\t_blast" --keep` (two builds, the second with the
route through the fan; both PASS). The second, read back from the archive
`<work>\build\t_blast\R09+M09_A (R09 = F07+M09_B)\F01_Main.zip`:

    kl_fa_blast: 6 boxes at the window (fan, cloud, spray, glass s, glass n, second); 2 references to their old job removed
    kl_fa_blast: blast 1.00: blast timer -> fan -> 4 boxes (cloud, spray, glass s, glass n); shake 3.00 / 8000 (factor 1.84 - 2.45
                 at the START points, Subway 0.70 at its own); second pop none; InvisiBomb -> FX_Grenade_RPG_01

    the opening, seconds from the round-start event (the countdown's first second):
      0.0              the heisters stand on the balcony; briefing voice at 0.5
      8.0              GO
      9.0  arm timer   the bomb gets 'Activate': its warm-up sound
     13.0  bomb        (5867 21094 -66) campaign Explode reach 1 / 1, tinnitus within 2000, fuse 4, hidden 1 -> Particles_M09_BigWindow
     13.0  InvisiBomb  (5684 20996 -393) campaign Explode reach 300 / 100 (it kills the guard at the glass) -> FX_Grenade_RPG_01
     13.0  fan         (5850 21150 -100) AIDWrapper 'Activate' -> cloud, spray, glass s, glass n; DocuCamControl 'OnExplosion'
     13.0  shake       (5800 21150 -100) ShakeCamera strength 3.00 reach 8000: factor 1.84 - 2.45 at the START points 638 - 903 away; lasts 0.8 s
     13.0  cloud       (5650 21000 150) Explode reach 1 / 1, fuse 0 -> FX_Grenade_RPG_01, the rocket's sound
     13.0  spray       (5800 21150 -100) Explode reach 1 / 1, fuse 0 -> Rocket_Default_01
     13.0  glass s     (5850 21300 -330) Explode reach 1 / 1, fuse 0 -> Glass_Exit_01
     13.0  glass n     (5850 21300 130) Explode reach 1 / 1, fuse 0 -> Glass_Exit_01
     13.0  second      OFF (nothing names it) (5400 21000 -100)
     13.0  blast timer and, as before: glass wrapper, chairs, doors, music, Activator_KillGuyNearWindow, TriggerBox_FallingDebris, 3 squad routs
                       a pillar comes down 5 s after the first heister walks in (campaign, kept)

Everything the new objects name, resolved in the archive (the report prints each line):

| names | resolves to |
|---|---|
| 3 particle groups (`FX_Grenade_RPG_01`, `Rocket_Default_01`, `Glass_Exit_01`) | `ZAllocMany` + clone groups of 3 / 4 / 30 copies; use 2 / 1 / 2 |
| 17 emitters -> 13 templates | all in `...\Effects/ParticleTemplates.zip` of the systems: Gren_Default_Smoke02, Gren_Default_FireBall_01, Gren_Fire_Blast01, Gren_Default_Debris_01 / _02, Grenade_Impact_Default_Sparks_01 / _Fire_01 / _Debris_01, Impacts_Glass_Debris / _02 / _Big_02, Impacts_Glass_Dust, Impacts_Glass_Smoke |
| 13 templates -> sprite chunks -> 11 textures | 224, 226, 229, 238, 245, 250, 252, 254, 271, 273, 279 are in the .TEX (FX_Par_Smoke_Shaded_test_01, Fx_Par_Smoke_Fireball_02, Fx_Par_FireBall_03, Fx_Par_MuzzleFlash_01, FX_Par_Debris_Stone_01 / _Default_02 / _Pebble_01 / _Glass_03 / _Glass_04, FX_SmokeAnimated_A_4x4_01, FX_Par_Debris_Water_01) |
| 2 omni lights with `ParamAnim` | inside the two clusters, stock |
| 1 sound, .SND offset 407600 | `audio:levelsetup/all/weapons_kl2_final/grenades/all/rpg_explosion_01#seq`, the value stock `Rocket_RPG7` holds in the same archive |
| materials | none: particles are sprites |

Other checks run:
- `selftest` PASS: the `DocuCamControl` equals stock F01's `DocuCam_Explotion` as token text; the
  `ShakeCamera` has the token kinds and values 0, 1, 3 of stock `scExplosion`; every `Explode` fits
  `CExplode` and differs from the rocket's only in the eight fields named above; `dress()` twice = once.
- On stock F07 with kl_fa_author's and kl_fa_street's `prepare_host`: with this layer on top only
  the six boxes differ in .prp and .gms, plus two F07 timers that named them and are not kept;
  nothing the level keeps without this layer differs; 0 misfits. `prepare_host` again: nothing.
- On the built level: `wire()` again changes nothing. heavy 1.5, mild 0.5, `--blast-second 0.8`,
  no fire + quiet, daze, bomb-native: each changes only this layer's boxes (and the InvisiBomb's or
  the bomb's field named by the option), 0 misfits, 0 dangling paths, and back at the defaults the
  scene equals the build again.
- The street layer reads back with 0 faults; `kl_graft.verify` and `kl_fa.check` as without this layer.

The build used the tools as they stood at 19:00 - 19:30, while s-visible and s-combat were editing
kl_fa_author / kl_fa_street / kl_graft / kl_fa.

## 6. Every GUESS and ASSUMPTION

GUESS:
- every position of the six boxes (from the window's measured frame: glass x 5850, bay z -550..350,
  floor y 20993), and that the cloud belongs inside the room;
- that a breaching charge may burn: the two clusters are the rocket's fireball (Subway's cloud is
  grey dust). `--blast-no-fire` is the alternative, and it is small;
- the rocket's explosion sound on top of the campaign's (`--blast-quiet` removes it);
- the knob's steps (0.75 for the second fireball, 1.5 and 0.5 s for the second pop);
- `--blast-daze` as a whole (below).

ASSUMPTION:
- a `TriggerDelay2` sends 'AITrigger' to its list (the stored message field of every stock
  `ActivateGeom`, `DocuCamControl`; kl_fa_author's whole layer rests on it; the id itself was not traced);
- the ZGEOM[1] layout for a turn that is not about Y ("outward" = [0 0 1, 1 0 0, 0 -1 0]:
  kl_fa_author.rot9's layout, seen live for turns about Y only). If wrong, the spray and the glass
  jets go another way; nothing else depends on it;
- that a spawned cluster takes the turn of the `Explode`'s node (0x60b4c3 passes a matrix and a position);
- template field 2 = life, field 4 = size; emitter field 1 = count;
- `--blast-daze`: that `CExplode` field 4 is the damage (3000 on the bomb, 700 on the campaign's
  "kill the player" bomb, 200 on a rocket, 100 on a .50 round). The option gives the bomb its reach
  back (600 / 400) with field 4 = 0, for the 5 s per-player effect and the pushes. **If the
  assumption is wrong the heisters die at 13 s.** Off by default; try it alone.

## 7. What only the owner's eyes can settle (one variable per run)

1. **Default build.** Is there a fireball with smoke at two places in the bay, a spray of debris
   and sparks, and does the screen shake? Does the hand-held camera add its own jolt? Is the
   rocket's bang on top of the window's too much?
2. **Strength.** 2.6 - 3.5 times Subway's shake may be too much from 6 m: `--blast 0.5`. Or not
   enough smoke: `--blast 1.5` (second pop 0.5 s later, shake x 1.5).
3. **Fire or dust.** A fireball on a window charge is my guess. `--blast-no-fire`.
4. **Where the spray goes.** Out over the balcony between the two stacks, or somewhere else (the
   turn is an assumption).
5. **Does the Dead Men glass burst show at all?** With something beside it to compare. If the new
   clusters show and it does not: `--blast-bomb-native` (the bomb itself spawns `Rocket_Default_01`).
   Seen -> the converted group is at fault (emitter / template pairing); not seen -> the hidden
   bomb's `Explode` does not spawn, and then its two sounds are probably not its own either.
6. **How long the smoke hangs.** About 4 s by the templates. If the owner wants Subway's 8 s
   rolling cloud: section 8.
7. `--blast-daze`, alone, last.

## 8. For the lead

Integration (until then `kl_fa_blast.hook()` does the same from outside, in any order with
`kl_fa_street.hook()`; `kl_fa_blast.py test` calls both):

    KEEP = (...) + kl_fa_blast.KEEP                               # kl_fa_author.KEEP
    kl_fa_blast.prepare_host(S, log)                              # last line of prepare_host(S, log)
    kl_fa_blast.wire(sc, log)                                     # last line of wire(sc, log)

- A build for the owner: `python tools/kl_fa_blast.py test <out> --keep` builds the whole level
  with all three layers (kl_fa_author's and kl_fa_street's own options are their module variables;
  this tool passes `--no-ai` and `--blast-real` on). The archive and the files beside it are in
  `<out>\R09+M09_A (R09 = F07+M09_B)\`. The build of this report is in `<work>\build\t_blast`.
- `kl_fa_author.layer_names()` does not know the six boxes: this file empties their old lists itself.
- **A real Subway cloud** needs loose emitters, and neither the host's kept part nor the systems
  have any. Two ways, both outside my files: (a) `kl_graft` learns to take a NESTED subtree of
  another stock level: F01's `...DL10_Platform\Particle_Blowout_01` (3 emitters) with
  `...DL10_Vault\Template_storm_01` (BlowOut_01 / _02 and their sprite) - a fourth source; or F07's
  own `...F07_Outside_LoadingBay\FX0100_ALL_TearGas_F07_A_01` (template TearGas_F07 is in the
  systems), which F07 already switches on with an `ActivateGeom` this layer's host keeps
  (`Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT`, today kl_fa_author's 'loot on').
  (b) once it is known why the Dead Men group does not draw (7.5), its 30 s dust is the cloud.
- Not touched: the bomb's hidden flag (kl_fa_author), the sequence, the street.
