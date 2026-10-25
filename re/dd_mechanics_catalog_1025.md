# Dog Days mechanics catalogue for the Dead Men maps (research, 2026-10-25)

Task: owner (10-25 night) asked for "dog days mechanics like dogs, fire extinguishers ... their FX and any scripted events ...
immersive ... soundtracks", "cops ai being smart", and PD2 guns for shop page II. This note is the catalogue of every Dog Days (DD)
mechanic or set-piece that can go on the Dead Men (DM) FA maps, with the stock level and entity chain, a graft recipe, what is
already done on DM maps, and a ranking.

OFFLINE and READ-ONLY. Nothing was launched, installed or written outside the scratchpad. Nothing here ran in the game.
Builds on `re/dd_setpieces.md` (set-piece census, 10-24), `re/interactivity.md` (wiring), `re/dm01_ai_cover_1025.md` (AI cover spec),
`re/grenades.md`, `re/rappel.md`, `re/heli_call.md`, `re/stinger_1023.md`, `re/music_hook.md`, `re/ambience_1023.md`. This note adds what
those lack: the DOG evidence, the grenade / tear-gas / flashbang picture, the radio / megaphone / siren sound nodes, the music
nodes, and the ranking.

Evidence labels: MEASURED = counted today by `kl_prpjoin.Scene` (name + class of every node) over F01..F09 and L00..L11
(scratch `C:\Users\Henri\AppData\Local\Temp\claude\scr\scan.py`, `sub.py`, `dogf.py`; outputs `fa.txt`, `l.txt`); NOTE = taken from
an existing re/ note (file named); GUESS = mine, unproven. Name matches are by node name and are noisy: a name hit is a
candidate, not proof of a working feature (for example "breach" and "charge" only matched `Trash`/`CD_Single` props, so there is
NO breaching-charge set-piece in DD FA maps).

## 0. Result in ten lines

1. DD has real police dogs: a normal `ZFFActor` + `ZSoldier` whose soldier style (field 0 of the soldier block) is 6. MEASURED
   in FA: F01, F03, F04, F06, F07 (one dog each, 1 actor); campaign: L02 (2 squads + a spline), L03, L06 (`Burger_Dogs_Inside` +
   `RanDogTM` random timer + dog barks), L11 (`SQ_DogsFinal_03`, airfield). F02, F05, F08, F09 have none. NOTE (map_ai.md, bots_dynamic.md):
   a dog never uses cover (soldier+0x108 = 0) and never throws (grenade entry refuses style 6). DM has NO dog on any map.
2. The DM zips already carry the Dog animation set (every installed DM/DD .ANM has the "Dog" strings, 115 hits where the F03 donor
   ANM was joined; 4-7 `/CloseCombat/Dog` hits elsewhere; MEASURED today on all 27 zips in `KLExpansion\Maps`). So a dog on a DM map
   needs the MODEL and its textures (kl_prmgraph path, as for cans), the Ground actor + squad chain, and a bark sound; no animation port.
3. DD's grenade / tear-gas / flashbang pieces are all in the systems side that DM maps keep: items + ammo in
   `mainsceneincludes_multiplayer` (5 WT_GRENADE items on all 9 FA maps), particle templates `Template_Flashbang_01`,
   `Grenade_Impact_Templates\Gren_TearGas_01..03`, `Template_StreetSteam_01\TearGas_F07`, and the screen filters
   `Cameras-Player0/1\TeargasFilter`. What is missing is the projectile (DD Ammo projectile slot empty, NOTE grenades.md) and any AI
   that throws: zero `GrenadeAttackBehaviourRout` in all 21 stock levels, so NO stock police squad ever throws a grenade.
4. The only stock tear gas is SCRIPTED: F07 `Gameplay!010_FirstFight!Shutters` (`GeomActivator_TearGas_LEFT/RIGHT`, `TimerShuttersOpen`).
   It is already reused on DM01B (`kl_hc2_garagedoor`, NOTE open_work_log).
5. Scripted entries that exist in DD: heli drop-off and attack heli (F02/F03/F06/F08), police cars arriving (F03 `Activator_SWAT_Cars`,
   F06 `make_police_cars_arrive`), rappelling SWAT (campaign L07 `Backlit_Squad_RapellingSW#04..07\MC_Repell`, `Squad_Repelling_01/02`
   + `Trigger_Box_Repel`; L10 12 nodes), SWAT kicking doors (F01/F03/F06), tear-gas shutter assault (F07), truck through a wall (F06),
   train in (F01/F02). No breaching charge, no flashbang entry, no stock sniper in FA (snipers are campaign: L04 21 nodes, L05, L07, L08, L10, L11).
6. Already on DM maps (not live-tested): kick doors, wall extinguishers, fuel cans / gas canisters, SWAT kick-in, DM02 shutter assault,
   police cars arriving (DM01, DM02), co-op shutters (DM02), rappel start (DM09), escape heli (Last Call, Hasta), civilians and crowds,
   hook-side music / ambience / stinger. Section 3 has the list with sources.
7. Not done and ranked highest by immersion per effort: DOGS (owner asked by name), then the stock police radio / megaphone / siren
   sound nodes and alarm lights (cheap, very audible), hook music phases switched on, a tear-gas gas cloud on the SWAT entries, rappelling SWAT
   on DM09/DM03A, then the cover / flank structure on the other maps (DM01 spec exists).
8. FX: keep DD's `CloneGroup_Effects` and `mainsceneincludes_multiplayer`; every DD FX named below is a particle template already
   present in every graft (the graft keeps the DD systems subtree), so FX are referenced by name, not copied, except map-local ones
   (`TearGas` and `Explosion_*` emitter groups live under the prop, they come with the prop clone).
9. PD2 guns for shop page II: out of scope here (shop page II is e8's area); see `re/pd2_guns.md`, `re/shop_more_guns.md`.
10. Top risks: actor / squad budget (proven 99 / 55, DM05A past that; each dog is one actor and one squad), model memory (2 GB wall,
    int3 0x4a3060), and every item below being unproven live.

## 1. Police dogs (new; not on any DM map)

| item | stock source | chain | status |
|---|---|---|---|
| FA dog, released by a box | F07 `Gameplay!020_Loot!021_FinancialAlley_Dog` (MEASURED nodes 123..128) | ZSquadScript group; child `DefendBehaviour\Pos#01` (ZBoxPrimitive); child `Dog` (ZGROUP) holding `Ground` (ZFFActor); `tbReleaseDog` (ZBoxPrimitive) | stock |
| FA dog on a leash modifier | F04 `Gameplay!030_AfterLoot!032_LeftFlankDOG` (nodes 652..659) | `10_Defend\Pos#01`, `20_MoveToEscape\Pos#01`, `30_smLeash` (squad modifier group), `Dog_German_Sheperd\Ground` | stock; `smLeash` = a modifier that frees or holds the dog (GUESS: not read) |
| security dog, random | F03 `Gameplay!10_AirportSecurityDog01` + `Gameplay!AIDstuff!RandomTrigger_Dog` (nodes 33..43, 18485) | squad with `20_DefendBehaviour_alt`, one `Dog_German_Sheperd_01\Ground`; a RandomTrigger decides whether it appears | stock |
| run-to-cover dog | F06 `AI_Players!Enemys!030_dog` (nodes 467..475) | DefendBehaviour, `RunToCover\RunToPosInfo#01/#02`, `TriggerBox_rtc`, `Dog\Ground` | stock; note a dog has no cover use, the RunToCover only moves it |
| street police dog | F01 `Gameplay!PoliceDogs#01` (nodes 266..271) | `10_Defend\Pos#01/#02`, `Dog#01\Ground` | stock |
| campaign dogs | L02 `AI!Enemies!02_Dog#01/#02`, L06 `Burger_Dogs_Inside` (+`RanDogTM` timer), L11 `SQ_DogsFinal_03`, L03 | same shape | stock |
| dog sound | F04 `F04_Audio.zip\Audio!SFX!Dogs!Dogs_01_Sound / Dogs_02_Sound` (ZSNDOBJ); L06 `Audio!Outside!3D_Objects!Dog!Timer` | positional ZSNDOBJ | stock |

Actor facts. MEASURED: the dog `Ground` node is the same class pair as a human, `ZFFActor` (20 own fields) + `ZSoldier`/`ZSoldierRout`
(23 fields), with a ZLNKOBJ model link; it is not a special class. NOTE: soldier style 6 = dog (map_ai.md section 1, 60 comparisons);
it uses no cover (bots_dynamic.md 3.1), cannot throw (grenades.md 11.1), and a "hit by hand" test is skipped for it (bots_down.md: the
ask at 0x688190 says no for a dog). The Dog animation set exists in the F01 ANM (characters.md: "F01 Kane, Lynch, Swat_02, Civilian, Police, Dog, ...").
The F03 / F07 donors carry Dog and the DM .ANM already holds it (MEASURED, point 2 of section 0).

Graft recipe (all steps GUESS until a load test; nothing like it was ever built):
1. Pick the F07 chain (it is a plain release-by-box, smallest: 6 nodes, no random). Clone the group `021_FinancialAlley_Dog` with
   `kl_fa_bots.Maker.clone('F07', ...)` as every squad graft does (kl_old_waves is the template), place `Pos#01` and `tbReleaseDog`
   at DM coordinates read from the scene, and name the squad in the map's AIMonitor start list or a timer / box.
2. The dog MODEL and textures: use the model-graft path of the cans (`kl_prmgraph` + `kl_texmat`, re/graft_formats.md), source F07 or F03.
   Check `.prm` size first (re/prm_limit.md), the dog is small but its textures count.
3. Bark: re-point the squad's sound by name into the DM map's own SND bank (done for DM02 mall: "Sounds re-pointed by name") or play
   F04's `Dogs_01/02` ZSNDOBJ clone; or hook-side `klambience` one-shots (already holds "dogs+horns (city)" in the `Spot` group, NOTE ambience_1023).
4. Budget: +1 actor, +1 squad per dog; keep 1 to 3 per map (DM01 headroom is about +49 actors / +30 squads, NOTE dm01_squads_1025).
5. Where: DM01 Hot Coffee (street police: F01 pattern, `PoliceDogs`), DM03A Vault garage / street (F07 alley pattern), DM06 park (F04
   `smLeash` pattern, the dog runs the escape path), DM09 Retomoto street part. Skip DM05A (actor count past proven point).
6. Design: release on the first alarm or the round's loud moment, or by a box on the loot route, never at the spawn (dogs have 0 cover use and a
   kill in 2 s on a spawn camper is the failure mode; GUESS).

Risks: dog bite / melee reaction on the player is in the player's own clip set (DD player: present, kill clips are not checked here);
dog nav (a dog uses the same nav mesh, GUESS); the Dog set's bones differ (`tail*`, `NECK1`), the DM .ANM bone table was joined with the F03 donor so
the names exist (NOTE anmjoin.md). Effort M (model graft) to L (if the .prm is near its limit). Immersion: high, owner asked.

## 2. Catalogue by mechanic

Effort S/M/L as in dd_setpieces.md. "On DM" = already installed or staged on a DM map (source in section 3).

### 2.1 K9 / police unit types and tactics

| mechanic | stock evidence | recipe | On DM | effort |
|---|---|---|---|---|
| Dog | section 1 | section 1 | no | M |
| SWAT squads (`Police_SWAT_01..` with `RadioCom` sound per squad) | F07 `Gameplay!020_Loot!...\Police_SWAT_01__\RadioCom` (MEASURED 8 ZSNDOBJ), F01 swat 32 nodes, F04 68, F03 45 | clone squad groups; a `RadioCom` ZSNDOBJ plays chatter at the squad | squads yes (PoliceSwats), RadioCom no | S for the sound |
| Human shield (player grabs an enemy / civilian) | `AllLevels/FA_Cam_Handheld.zip\Cam_Handheld\Human_Shield_Cam00..03` + `Human_Shield_Execution_Cam` in the multiplayer systems, MEASURED in all 9 FA maps; AI tactic `ReactToHumanShield` (bots_dynamic.md) | free: lives in the DD systems the graft keeps | yes by construction (GUESS: not live-checked on DM) | S (verify only) |
| Riot shield cop | none found in FA (shield hits are the human-shield cameras and two grenade-weapon names), campaign L00..L11 same | not available | no | L |
| Snipers | campaign only: L04 21 nodes, L05 4, L07 3, L08 5, L10 5, L11 3; FA F06 3, F08 2 name hits (rooftop `Sniper` posts, GUESS) | clone the F06/F08 sniper squad group onto a roof; position at a sight line to the loot | no | M |
| Mounted weapons / turrets | `AttackMountedWeapon` tactic exists in the soldier (bots_dynamic.md 3.1), no FA map names a turret (F07 `WallMounted` are street signs) | none found | no | L |

### 2.2 Scripted entries

| mechanic | stock level and chain | recipe | On DM | effort / risk |
|---|---|---|---|---|
| SWAT rappel from a roof | L07 `AI!Enemies!Backlit_Squad_RapellingSW#04..#07\MC_Repell` (MiniCutscene), `Squad_Repelling_01_Start_Later` + `Trigger_Box_Repel`, `Squad_Repelling_02`; L10 12 `Repell` nodes; clip `Repelling_01` (NOTE rappel.md 8.5: a one-act MiniCutscene whose PosObject is 17.6 m above the balcony moves the player's node along the clip root path) | clone one `MC_Repell` cell with a Swat_02 actor, PosObject above a roof edge, a TriggerBox / timer to start; the clip is already in DM09's .ANM (rappel build) | player only, on DM09 | M, risk M (an NPC on the clip is unproven; the rope model is not in the build) |
| Heli drop-off | F02 13 routs (`Swat_Chopper_dropping_of_ais`), F03 8, F06 12, F08 6 (`50_SWAT_Helicopter`, `10_Outgoing_01` HeliFlyBehaviourRout + CrashSite_Center) | `kl_fa_bank` heli waves, `kl_fa_hasta_heli`; NOTE dd_setpieces rank 6 (DM11B) | escape heli only (DM05A, DM11B) | M, drop-off needs a spline |
| Attack heli | F08 `V_Enemy_Helicopter_Group` (VehicleEffects, ZHeli, HeliWeapon, HeliNetSync, DistanceRumbleCam, HeliScriptRout) | copy the whole group | no | L (net sync, weapon) |
| Police cars arrive, men exit | F03 `Activator_SWAT_Cars` (18455) -> proxy `F03_Anim_PoliceCars...Animation_Backside_Policecars_01`, MiniCutscene exits; F06 `mat_pos_anim_proxy_make_police_cars_arrive_01` + `tbFA_UCC_Reinforcements` | `kl_arrivals_1024r2` / `kl_dm01_cars_1025` | DM01 (3 cars, 6 SWAT, staged then installed), DM02 mall (3 cars, staged) | done once; M elsewhere |
| SWAT kicks a door in | F03 `AIDstuff` SWAT01..03_Kickdoor, F01 `Gameplay!merc_bot_squad!KickdoorMonitor` (KickDoorBehaviourRout + KickDoor_PosInfo) | `kl_dm03a_swat_1025` | DM03A (3 men, door 1, 75 s), installed, unproven | done |
| Shutter / tear-gas assault | F07 `Gameplay!010_FirstFight!Shutters`: `GeomActivator_TearGas_LEFT/RIGHT` (17003/17004), `TimerShuttersOpen` (17011) | `kl_dm02_assault_1025` (DM02, 150 s, 2 x 6 SWAT), `kl_hc2_garagedoor` (DM01B TearGas_RIGHT lists) | DM02, DM01B | done |
| Truck through a wall | F06 `Scripting!`: `MatPosAnimProxy_TruckCrash`, hole-in-wall swaps | needs truck anim + wall variants | no | L |
| Train in | F01 `MovingTrainMiddle/Sides`, F02 | needs train model + keys | no | L |
| Round-start blast | F01 `Gameplay!Blowout` (tdExplosion, scExplosion ShakeCamera, dgBombFlash, agFallingRubble/Sparks, awSoundAndSmokeEFX) | `kl_fa_blast` | Retomoto (DM09), owner design | done |
| Breaching charge | none (MEASURED: no stock node, hits were `Trash`/`CD_Single`) | would be a kick-door variant with an explosion FX at the door (GUESS) | no | M, own design |
| Flashbang entry | none as a scripted event; the flashbang item + `Template_Flashbang_01\Flashbang_Smoke_01` exist | would be an FX group fired by a timer at a door, no stun effect on the player (GUESS: the stun is the projectile's) | no | M |
| Fake escape chopper | F06 `Fake_Escape_Chopper` | decoy only | no | M |

### 2.3 Tear gas, flashbangs, grenades

NOTE (grenades.md): DD kept the items, throw actions and animations, the AI behaviour and network messages; it removed the projectile groups
and the effect pools and sounds. Plan there (put DM `Projectile\Grenade_*` groups into the DD systems subtree, repoint effects and sounds,
fill the Ammo slot) was built for F06 in 10-17 (`kl_grenade.py`, build/grenade_1018) and never run live. combat.md: "launchers are not
handed out" by default; `kl_arms.arm(launchers=True)` hands tear-gas launchers (`HK69`) back; the soldier has an `EvadeTearGas` tactic
(bots_dynamic.md) so DD police move out of a cloud. A throw by police exists only as the route step `ZGrenadeAttackBehaviourRout`
(fields: actor group path, x, y, z, NEXT, 2 bools; MEASURED zero in 21 stock levels), added by `kl_grenade.py` for 3 squads in the F06 build
(GUESS: the position may be ignored, the goal throws at the current target).

Recipe ranked: (a) scripted gas cloud, no throw: clone the F07 `GeomActivator_TearGas_*` + particle group at an entry and fire it on the
SWAT-entry timer together with the sound (S/M, already working pattern on DM01B / DM02); (b) the player's own tear gas / flash: needs the
projectile graft (L); (c) AI throws: needs step (b) plus the route step (L, unproven).

### 2.4 Destructibles, FX sets

| item | stock chain | recipe | On DM |
|---|---|---|---|
| Fire extinguisher | `FX0900_ALL_FireExtinguisher_nn` (ZHavokRigidBody + BarrelEffects + Throwable + `!GeomActivator`, `FX0901_..Explosion_Extinguisher_A`) in every map, donor F04 | `kl_interact_graft`, 4 to 6 per map | 01, 01B, 03A, 06, 09, 02 (staged) |
| Gas canister / fuel can | `FX0900_ALL_GasCanister_A/B` (F04..F07, F09), `FuelCan_D` + `Explosion_Gas_S` (F03 Garage, with `DocuCamControl_Explosion`, CheapCamFx) | same path, donor F03/F07 | DM01B (3 fuel cans), DM03A (3 canisters), DM02 (4 fuel cans staged) |
| Car explosion | `VehicleEffects` (F02 3, F03 1, F06 2, F08 2) BlowupChance, `OnlineEscHavokCar` | `kl_blowup.py` (NOTE vanblow, 10-24) | escape vans, DM data pass staged; burning car black box fixed (`kl_fa_carfx`, installed 10-12 for DM05A club) |
| Glass / shatter | `HavokShatter` (F08 361, F03 56, F07 44, F04 31); neon GlassBreak sound (F01) | DM maps keep their own HavokShatter (DM03A 223, DM09 331) | present |
| Breakable fence | F04 `PC_0002_LootRoomFence_Breakable_A_nn` x7, 5-way wiring | model + hvk graft | no, L |
| Sprinklers | F03 21 `PC_0800_F03_WaterSprinkler_nn!sprinkler`, F08 66 `PC0300_F08_Sprinkler_One`, F01 `PC0912_F01_SprinklerSingle` | clone the emitter node (GUESS pure particle) | no, S cosmetic |
| FX sets | `CloneGroup_Effects` (impact, muzzle, BulletImpacts, WeaponsEffects) + `Effects/ParticleTemplates.zip` (Template_Flashbang_01, Grenade_Impact_Templates, Template_StreetSteam_01\TearGas_F07, Template_Helicopter_Damage_01 in L07) | already kept by the graft (DD systems), nothing to do; the DM sets are dropped (CLAUDE.md) | yes |
| Camera shake | F01 Blowout `scExplosion`, F03 `DokuCamShake` (5), F02 `Group_camera_shake`, `DocuCamControl_Explosion` | ride with the prop / event clone | with cans and blast |

### 2.5 Alarms, sirens, radio, megaphones

| item | stock nodes (MEASURED) | recipe | On DM |
|---|---|---|---|
| Alarm lamp | F01 `PC0400_DL10_LampAlarm_01` (+ `Lamp_Alarm_ON01`, bulb), F08 `PC0100_F08_Alarmlight01..04` + `PC0300_F08_FireAlarm01` (27 ZSTDOBJ) | clone the lamp group; trigger by timer (data side has NO shot / aggro trigger, NOTE dd_setpieces); cosmetic | no |
| Police light bar | F03 `V_Santana_CopCar..\Lights_Siren02 / Siren_Blue_On03 / FX0700_ALL_GlassShatter_Siren02`, F07 `V_Van_Police_05!Body\Lights_Siren01`, `SirenGlow_Blue/Red_03` | comes with every cloned car / van | with cars on DM01, DM02 |
| Police megaphone | F01 `F01_Audio.zip\Audio!SFX!Police!PoliceMegaPhone_Street` (ZSNDOBJ); F03 `PC0800_F03_MegaPhone_A_20toLEFT/RIGHT_nn` props (`!Support`, `!Head`, 10 ZSTDOBJ) | clone the ZSNDOBJ and re-point its sound id into the DM bank | hook side only: 21 Japanese megaphone / warning clips on the 8 DM09 folders (`Ambience\jpmega`, `jpwarn`, installed 10-23) |
| Squad radio chatter | F07 `Police_SWAT_01__*\RadioCom` ZSNDOBJ x8, F02 radio 8, F06 8, F03 radio props | clone with the squad | hook side: `Radio` group, 14 PoliceRadio + 7 RadioCom lines, 40-90 s |
| Level alarm bell | `Audio!SFX!Outside!Plane_Engine!Plane_Alarm` (F03) etc. | hook `Alarm` group once | hook side |

### 2.6 Music and stingers per FA phase

| item | stock | recipe | On DM |
|---|---|---|---|
| Positional music | F01 `Audio!Music!ShopMusic`, `#01..#03` (ZSNDOBJ), F07 `Audio!Music!Outside_FinancialAlley_GuardShed`, `Eye_Music`, F02 6, F04 2, F06 1, F09 2 | none needed; the DM maps use their own (Retomoto: 15 clips under Music/InHouse/Japan, Last Call club music boosted) | per map |
| Escape music | F07 `Specials!Audio!EscSoundHandling!Esc_Music` + `Activate` / `DeActivate` + `CameraOutside_01_SLF` | the escape cue graft (S/M, GUESS: the Activate list is fired by the escape state) | DM09 own music only |
| Engine music route | `ZPlayMusic`: 0 in the 9 FA maps (settings field 157 = 0, NOTE music_hook.md); needs a rebuilt sound bank per map plus PC_Def.str | L | Last Call stage B (bed through fields 157/158) unproven |
| Hook phases | `klmusic.c`: CALM -> ACTION (+stinger) -> ASSAULT (AssaultAfter 150 s / on down / on money) -> ESCAPE / DOWN, PD2 pool; `klambience.c`: bed + Radio / Alarm / Heli / Distant / Siren / Spot / Local / Panic; `klstinger.c`: Loud, Loot, Down, Dead, Betray, Last30, Open, Reached, 24 clips (21 DD `Music_Moments`, 3 PD2) | owner switch: `[Music] Enable=1` (PD2 jukebox stutters, so Enable=0 default, memory pd2-music-opt-in), `[Ambience] Enable=1`, `[Stinger] Enable=1`; no police signal in the hook, so ASSAULT uses stand-ins | ambience pass 2 installed 10-23 (26 clips, DM01/01B/03/11B beds, DM09 megaphones); sound3 and stinger add-ons NOT installed as of 10-23 (check KLHook.ini today) |

### 2.7 AI cover and flank recipes (the "smart cops" wish)

Full evidence in `re/dm01_ai_cover_1025.md` (with the critic corrections in its section 11). Summary and how to port to the other maps:

| recipe | stock / campaign evidence | status on DM |
|---|---|---|
| Cover first: `RunToCover` per actor + `RandomTrigger` 3-5 branches + `SquadModifier Unleash` + `DefendPlayerPos` | campaign RunToCover 45-141 per level (L07 141), stock FA 3-35; `DefendPlayerPos` 11-65 per campaign level | DM01: 0 RunToCover, 0 DefendPlayerPos on the enemy side (spec only, not built); other maps not measured |
| Cover boxes near defend posts | median 2-4 boxes within 5 m in stock, DM01 2, and 28 % of DM01 posts have none | spec: 14 boxes on real props |
| Flank | `ZFlankingBehaviourRout` (2 child points), campaign L07 10, L08 17 | DM01 9, all fixed world points |
| Waves / reinforcement ring | F03 `Gate_RandomRespawnSWAT` ring of 4 squads (NOTE map_ai.md 2) | `kl_old_waves` chains on DM01 / DM02 (timers only) |
| Door gating | KickDoor + KickDoorMonitor lets squads use a door | DM01, 01B, 03A, 02 |
| Tactics are already in every soldier | AttackFromCover, DefendCover (500 u), AttackNoCover, CloseIn, EvadeDangerPoint, EvadeTearGas, GrenadeAttack ... (bots_dynamic.md) | nothing to switch on; the cost is data: boxes and routs |
| Difficulty | runtime option only (health rows 0.5 / 0.9 / 1.15 / 1.3), level `Filter` in L01/L02/L03/L08 only | n/a |
| Dogs | no cover, plain Defend / release | section 1 |

## 3. What is already done on the DM maps (grep re/open_work_log.md, 10-25; all "not live-tested" unless the log says otherwise)

| map | done / staged | source |
|---|---|---|
| DM01 Hot Coffee | kick doors + wall extinguishers (doors2), AI door opening, dm01squads (shop hold 4, warehouse 8 + 4, 4 more kick doors; 62/28), dm01cars (3 F03 police cars, 6 SWAT exit, FrontMall released; 68/31) | log 10-25 "INSTALLED ... 11c874cb / c0e7b8ee", dm01_cars_1025.md, dm01_squads_1025.md |
| DM01B Hot Coffee II | 3 fuel cans, 2 extinguishers (119c9cd2), doors2 (f2a70278), garage-door tear-gas lists | dm01b_gas_1025.md, kl_hc2_garagedoor |
| DM02 Late Night Opening | co-op / timer shutters, cash drawers, SWAT shutter assault (ae193d9c installed), mall extras STAGED not installed (6 kick doors, 6 extinguishers, 4 fuel cans, 3 police cars + SWAT) | dm02_shops_1024, dm02_assault_1025, dm02_mall_1025 |
| DM03A Vault | kick doors + extinguishers + SWAT through KL_Door_1 at 75 s + 3 gas canisters (02e90dfa installed) | dm03a_swat_1025.md |
| DM05A Last Call | escape heli, bodyguards / crowd (lastcall3b lite installed; lastcall5 staged), club music boost installed | open_work_log |
| DM06 / DM09 | extinguishers + kick doors on both (f1f888c5, b76586a1 installed), DM09 rappel start, round-start blast, Japanese megaphones | rappel.md, retomoto_blast.md, ambience pass 2 |
| DM11B Hasta | escape chopper, late police `plop` wave | hasta_*.md |
| all | hook `klmusic`, `klambience`, `klstinger` (opt-in), human shield via DD systems | music_hook.md, ambience_1023.md, stinger_1023.md |

NOT done anywhere: dogs, rappelling or heli-delivered police (only the escape chopper), alarm lamps, tear-gas clouds as an effect on a SWAT entry
beyond DM01B / DM02, sprinklers, police megaphone / RadioCom nodes, snipers, escape music node, AI cover / flank structure (spec only), grenade throws.

## 4. Ranking of the rest, immersion gained per effort

Score = (immersion 1-5) / effort (S=1, M=2, L=4). Owner requested items first within a tie.

| # | item | immersion | effort / risk | why |
|---|---|---|---|---|
| 1 | Hook music + stinger + ambience switched on (config only, installed pieces) | 5 | S, risk L (PD2 jukebox stutter: use DD/DM stingers first) | "soundtracks" asked; code exists |
| 2 | Police megaphone + RadioCom + siren sound nodes cloned onto cop squads and arrival cars | 4 | S / M | very audible, no model, re-point sound ids into DM bank (pattern done on DM02 mall) |
| 3 | Dogs (F07 release-by-box chain), 1 to 2 per map on DM01, DM03A, DM06, DM09 | 5 | M (model graft), risk M | owner named dogs; only mechanic fully new to DM |
| 4 | Alarm lamp group + siren on a timer at round-loud time (Last Call, DM03A, DM09) | 3 | S / M | cosmetic, cloned nodes |
| 5 | Tear-gas cloud + sound on SWAT entries (DM03A door, DM01 warehouse, DM09 lobby), reusing the F07 GeomActivator pair | 4 | M | proven pattern on DM01B / DM02 |
| 6 | Cover / flank structure on every map: RunToCover + RandomTrigger + cover boxes (DM01 spec first, then DM02 / DM03A / DM09) | 5 | M per map (data only, no new model), risk M | "cops ai smart"; the key difference to the campaign |
| 7 | Rappelling SWAT on DM09 tower roof and DM03A Parkade | 4 | M, risk M | clip already in DM09 ANM; NPC-on-clip unproven |
| 8 | Heli drop-off squad (DM11B first, DM09 street) | 4 | M, risk M | needs spline; escape heli code exists |
| 9 | Police cars arriving on DM06 / DM09 / DM03A street at escape time | 3 | M | `kl_arrivals` pattern |
| 10 | Sprinklers, fuse boxes, vending, elevators hum | 2 | S, S, L, M | cosmetic |
| 11 | Snipers on roofs (F06/F08 groups) | 3 | M | sight lines must be checked per map |
| 12 | Player flashbang / tear gas (projectile graft) + AI throws | 4 | L, risk H | grenades.md unproven live |
| 13 | Attack helicopter, truck through wall, train, breakable fence | 4 | L | models, key data, net sync |

Recommended order for the next builds: 1 and 2 (no map risk), then 3 on one map (DM03A) as the test, then 6 on DM01 using the existing spec, 5 and 7 together
on DM03A / DM09, the rest as budget allows.

## 5. Unproven / open

- Whether a dog actor moves on DM nav meshes and plays the Dog set with the DM .ANM (strings present, behaviour not tested). A one-dog
  test on DM03A is the cheapest decider.
- `smLeash` meaning (F04 `30_smLeash`) is a name only.
- Whether `ZGrenadeAttackBehaviourRout` fires with the ignored x/y/z (grenades.md GUESS), and whether any police ever throws a launcher round.
- No data-side aggro / first-shot trigger exists (alarm lamps need a timer or hook).
- Actor budget: proven 99 actors / 55 squads, stock 148 / 90; each dog and each rappel cell costs one actor and one squad.
- Everything in section 3 is "installed, not live-tested"; the next live round decides which of these stay.
- PD2 guns (owner point 3) are untouched here; shop page II and the hook shop code belong to kl-merge-e8.

## 6. Critic corrections (2026-10-25, adversarial check against the data)

Checked: dog groups, ZFFActor `Ground` children, ZGrenadeAttackBehaviourRout count, sniper hits, alarm/megaphone/RadioCom nodes, tool and note names.

- CONFIRMED (re-read with `kl_prpjoin.Scene`): F01, F03, F04, F06, F07 each hold a dog group whose `Ground` is a `ZFFActor`; F07
  `021_FinancialAlley_Dog` + `tbReleaseDog` is real. ZGrenadeAttackBehaviourRout is 0 in F01/F03/F04/F06/F07 (the rest were not re-run here).
  Alarm lamp (F01 `PC0400_DL10_LampAlarm_01`), `PoliceMegaPhone_Street`, F06 `RadioCom`, F03 megaphone props exist. Tools named all exist.
- NOT VERIFIED by this check: soldier style 6 = dog (taken from map_ai.md only; the scene scan only lists names), the "115 Dog strings"
  in the DM .ANM files, and the F04 `smLeash` meaning (already marked GUESS).
- CORRECTION, sniper row: the "sniper 1" hits in F01-F05/F07/F09 are `Projectile_Sniper_01` (a bullet template in the systems side), NOT
  sniper posts. Real sniper groups are only F06 `030_swat_guarding_snipers` and F08 `Gameplay!40_SWAT_Roof_Snipers`.
- CORRECTION, riot shield: row 2.1 says "not available". map_ai.md counts soldier style 5 as shield and the code branches on it, so a
  shield cop type exists in the engine but no FA map ships an actor with it (data, not code, is missing). Still L.
- CORRECTION, dog effort: "M" is too low. A dog is a skinned character, not a prop like the cans: it needs the kl_chars skeleton / anim-set
  path (`C.person`, skeleton, bone names), not just `kl_prmgraph` + `kl_texmat`, plus the soldier block with style 6 and the nav behaviour.
  Honest effort is L for the first dog on any DM map, then S for each further dog. The one-dog DM03A test stays the right first step, but
  expect 2 to 3 iterations (T-pose / invisible / crash at load are the likely first results). Rank 3 stays; do not expect it overnight.
- CORRECTION, rank 1: hook music/stinger/ambience "Enable=1" is config only, but the same note says the PD2 jukebox stutters, the owner
  made `[Music] Enable=0` the default, and sound3/stinger add-ons were NOT installed as of 10-23. So it is "check what is installed, then
  flip", and music must stay opt-in (owner rule, memory pd2-music-opt-in). Not zero-risk and not unattended: it changes what the owner hears.
- Rank 6 (cover/flank) is called "data only"; it is data but needs live play to judge, since no reaction can be asserted offline. Effort M per map holds.
- Nothing in this note ran in the game; every "done" is "installed, not live-tested".
