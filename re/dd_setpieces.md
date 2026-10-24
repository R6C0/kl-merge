# Dog Days set-pieces and where to graft them on the Dead Men FA maps

Research note, 2026-10-24. Read-only survey of DD F01..F09 (`J.Scene.load('F0x')`) plus the live DM zips under
`<DD>\KLExpansion\Maps\<DM>\`. Nothing was installed. Complements `re/interactivity.md` (census) and
`re/graft_formats.md`. Items marked GUESS are not verified in the data or the game. DM coordinates are NOT
measured here; placements name rooms and existing host nodes, and the exact position must be read from the
scene before building.

Stock map identities (top-group names): F01 Subway, F02 Bridge, F03 Airport, F04 Market (Shanghai-style),
F05 Ship, F06 Money Transporter, F07 Financial Alley, F08 Office tower, F09 Shanty Town / Radio tower.

## 1. Catalogue by set-piece type

Effort: S = clone with existing tool, M = new builder on proven parts, L = needs model/key/animation graft or hook.
Risk: L/M/H = chance of a crash or a dead (non-working) piece.

| Piece | Stock nodes / classes | Wiring | Tooling now | Effort / risk |
|---|---|---|---|---|
| Kick door | F01 7 (`DL10_CtrlRoom\PC0400_..Glas_Doors_nn` `KickDoor_Action_01`), F03 16 (`PC0800_ALL_KickableDoor_E_01`, `PC1000_F03_KickableDoor_A/E`), F04 1, F06 3. ZKickDoorController (11 fields) | KickDoorBehaviourRout + KickDoor_PosInfo for the AI; `KickDoorMonitor` (F01 `Gameplay!merc_bot_squad!KickdoorMonitor`, F03 `AIDstuff` SWAT01..03_Kickdoor) lets squads use it | `kl_interact_graft` (F03 leaf replaces a static DM door leaf, PLAN hosts pinned). Installed on DM01, 01B, 03A | S where a separable leaf exists (DM01, 01B, 03A). DM06/DM09/DM11B have no leaf: L |
| Kickable bridge | F03 `AIDstuff!KickableBridge`: KickDoor + CoverState_Act/Deact, PathBlocker, FocusBox, MatPosAnimProxy | door opens a path for AI | none | L (model + anim) |
| Co-op shutter / airlock | `CoopAirlock` (ZCOOPAirlockController, 28 fields): F04 `LootHall\SI0100_F04_Coop_Move_Dxxr_04!Controller`, F06 `PC0200_F06_Coop_Move_Dxxr_01!Controller`, F02 `Scripting!kickthetrain` | two players hold; completion list fires PathBlocker + DeactivateGeom (shutter geometry off). `kl_hc2_garagedoor` is the DeactivateGeom pattern | `kl_dm02_shops_1024` (variant A: 3 co-op + 2 timer; B: 5 timer). Installed DM02 | S/M, done once; no stock leaf model, shutter uses the DM mesh |
| Fire extinguisher / can | every map 12-29 `BarrelEffects` + `Throwable`; F02 15 (`FX0900_ALL_FireExtinguisher_nn`, `FX0901_..Explosion_Extinguisher_A`), F04 15 (donor), F03 18, F07 14 | shoot -> burst FX; Throwable for the pick-up | `kl_interact_graft` (4 per map). Installed on 01, 01B, 03A, 06, 09 | S, low risk |
| Gas canister / fuel can | `FX0900_ALL_GasCanister_A/B` (F04, F05 13, F06 12, F07, F09 15), `FX0900_ALL_FuelCan_D` + `Explosion_Gas_S` in F03_Garage (with DocuCamControl_Explosion, CheapCamFx) | shot -> explosion, optional camera | same model-graft path as cans (GUESS: the canister is one more PLAN entry) | M; explosion radius vs. DM geometry unproven |
| Breakable shoot-through fence | F04 `PC_0002_LootRoomFence_Breakable_A_nn` x7: `!Shatter` HavokShatter, `!Frame_State_A/B` ShotActivate, `!blocker_relay` RelayMessage, `!CoverKill` CoverStateChanger, `!PFBlock` PathBlocker, WoodSplinters FX | shooting swaps frame states A/B/C and unblocks AI path | none | L (model + hvk + 5-way wiring); DM already has 223-331 HavokShatter on 03A/09 |
| Breakable glass / shatter | F08 361 HavokShatter; neon lights with GlassBreak sound (F01), police-van siren glass (F07, F09), police cars (F02) | HavokShatter with its own fracture data | DM maps keep their own (03A 223, 09 331, 11B 69) | already present on DM |
| Sprinklers | F03 21 `PC_0800_F03_WaterSprinkler_nn!sprinkler`, F08 66 `PC0300_F08_Sprinkler_One`, F01 `PC0912_F01_SprinklerSingle` | particle emitter, no logic | none (pure cloning of an effect node) | S (GUESS), cosmetic |
| Alarm light / siren / fire alarm | F08 `PC0100_F08_Alarmlight`, `PC0300_F08_FireAlarm`, F06 `PC0500_F06_Siren_A` | emitter + sound, F08 lights flash on timer | none | S/M cosmetic |
| Fuse box | F09 `PC0300_F09_FuseBox_A/B` with `Lid` | prop with animated lid | none | L (anim) |
| Cash drawer / register | `PC0406_M02_FA_Cashdrawer_01`, `PC0406_M02_FA_Montre_Desk_01` (DM02's own); stock loot = `OnlineMoneyContainer` (F01 58, F03 12, F08 47) + `OnlineMoneyCtrl` | container holds a stack, open on interact | `kl_dm02_shops_1024` (8 drawers, +1.06M), `kl_fa_loot` | S on any DM counter prop |
| Safe / vault | F01 `DL10_Vault`, F01 `OnlineMoneyContainer` set | same container class | `kl_fa_loot` | S |
| Vehicle drives in (train) | F01 `MovingTrainMiddle`/`Sides`: tbTrain, tdTrainArrive, tdTrainWait, mpaTrain (MatPosAnimProxy), Gate Way#01/#02 (GateGroup/GatePath), cscActivate/DeactivateCovers, 24 DocuCamSetup | TriggerDelay -> MatPosAnimProxy plays a path; covers swap while the train is in | none | L (needs the train model + the animation key) |
| Vehicle crash into wall | F06 `Scripting!`: MatPosAnimProxy_TruckCrash, GeomActivator_fx_truck_crash(_B), GeomActivator_hole_in_wall / GeomDeactivator_wall_before_hole, Timer_open_up_hole_in_wall, TriggerBox_wreckage_minicut | timer -> truck anim -> swap whole wall for the holed wall -> new path for AI | none | L (truck anim + alternate wall geometry) |
| Cops arrive by car | F06 `mat_pos_anim_proxy_make_police_cars_arrive_01`, `tbFA_UCC_Reinforcements` (TriggerBox), Timer, CoverStateChanger; F01 parked `V_Santana_CopCar_nn` | box/timer triggers anim + squad activation | `kl_arrivals_1024r2` `plop` (squad simply stands there; DM11B) and `carexit` (DM01, unproven) | M with plop; L for true drive-in |
| Cops arrive by door / SWAT assault | F07 `Gameplay!010_FirstFight!Shutters`: GeomActivator_TearGas_LEFT/RIGHT, TimerShuttersOpen/Close/OpenDif, AIDWrapper open/close, PF_Blocker timers; F03 SWAT01..03 kick monitors | timers open shutters, tear-gas particle, AI path unblocked | co-op shutter builder + waves (old_waves chain) | M. Door-gated timer waves are noted NOT buildable offline in `kl_arrivals_1024r2`; use timer-opened shutters only |
| Heli (scripted) | F02 13 routs (`Swat_Chopper_dropping_of_ais`, `Escape!EscapeHelicopter_01\Incoming_A..H`), F03 8, F06 12 (+ `Fake_Escape_Chopper`), F08 6 (`50_SWAT_Helicopter`: ZSquadScript, `10_Outgoing_01` HeliFlyBehaviourRout + CrashSite_Center, `V_Enemy_Helicopter_Group`: VehicleEffects, ZHeli, DistanceRumbleCam, HeliScriptRout, HeliWeapon, HeliNetSync) | spline path + squad drop; F08 attack heli shoots | `kl_fa_bank` heli waves; DM05A already has the escape heli (lastcall2) | M for a drop-off (spline), L for an attacking heli (HeliWeapon, net sync) |
| Round-start blast | F01 `Gameplay!Blowout`: tdExplosion, scExplosion (ShakeCamera), DocuCam_Explotion/FallingElevator, agFallingRubble/Sparks, dgBombFlash, mpaElevator, tdCivilians, awSoundAndSmokeEFX | TriggerBox/TriggerDelay start | Retomoto start (owner design) uses the same idea | M |
| Train crash / bridge collapse | F02 `mpap_make_train_*`, `mpap_explosion`, Group_camera_shake(5), TriggerBox_call_police_chopper, Box_KILL, GeomActivator/Deactivator swaps | long timer chain | none | L, map-specific |
| Civilians fleeing | F01 `CiviliansFront` (Running/Screaming/fall/wounded, ~73), `CiviliansBack` 22; F02 160; F07 22 | MiniCutsceneRout flee on aggro | `kl_fa_civs.add` (8-entity form, proven), club crowd/dance (107/79 past proven point) | S, budget-limited (proven 99 actors / 55 squads) |
| Ambient props | luggage carts (F03 `F03_Anim_LuggageCarts`), elevators (F05 `SO0102_F05_Elevator_A` with hum/squeak), vending machine (F07), phones, ice-block cover (F04), boats (F02) | MatPosAnim or static | none | L for anim, S for static |
| Camera shakes / DocuCam | F01 Blowout, F02 Group_camera_shake, F03 DokuCamShake (5) | ShakeCamera / DocuCamSetup | none | S (GUESS) |

## 2. Per-map stock highlights (what makes each map feel like DD)

- F01 Subway: round-start blast, arriving train, 7 glass kick doors in the control room, civilians fleeing, parked cop cars, sprinklers.
- F02 Bridge: train crash/bridge collapse, police chopper dropping squads, 160 civilians, kickthetrain co-op.
- F03 Airport: 16 kick doors that SWAT also kicks, kickable bridge, fuel-can explosion in the garage, sprinklers, luggage carts, security dogs.
- F04 Market: breakable loot-room fences, co-op shutter, cans and gas, huge squad counts.
- F05 Ship: gas canisters, elevators, van explosion at escape.
- F06 Transporter: truck crashes through a wall mid-round, gate opens, police cars arrive as reinforcements, co-op airlock, fake escape chopper.
- F07 Financial Alley: tear-gas shutter assault, loading-bay shutters, vending machine.
- F08 Office: SWAT attack helicopter, sprinklers/fire alarms, shattering glass, roof rain.
- F09 Shanty Town: gas canisters, fuse boxes, police vans.

Common DD feel: something happens a minute in that changes the fight (blast, wall opens, vehicle arrives, shutters
rise), plus doors the player kicks and cans the player shoots.

## 3. Placements on the Dead Men FA maps (ranked by owner-visible impact)

"Done" = already installed in the owner's game, not live-tested (see CLAUDE.md Open work).

1. DM02 mall, Parkinglot / Atrium: SWAT tear-gas shutter assault, F07 FirstFight style. Use the 12 existing
   `SI0401_M02_FA_RollerShutterA_nn` shutters: a timer opens two frontage shutters at a fixed minute and a wave squad
   (old_waves chain) pours through. Highest impact: the mall is the busiest map and its shutters already
   work (timer-opened variant proven offline). Effort M, risk M (wave budget, door-gate not buildable, so timer only).
2. DM01 Hot Coffee, StripmallBack / Diner wall: F06-style mid-round wall breach. Without a truck model, swap the
   Diner back wall geometry via GeomActivator/Deactivator on a timer with a camera shake and blast sound, then 1 cop
   squad via plop behind it. Effort L (alternate wall geometry), risk M. A fallback (blast + dust only, no new path) is M.
3. DM05A Last Call, Entrance / Stairs: alarm lights + siren (F08 `Alarmlight`) that start when the first shot
   is fired (GUESS: no data-side aggro trigger; `[ClubCalm]` is a hook feature) or at a timer, matching the
   installed wave start. Effort M, risk L, cosmetic but very visible.
4. DM03A bank, SecurityHall / Parkade: SWAT breach through the kick doors (F03 SWAT01..03 kick monitors) and
   gas canisters (F04/F07 `GasCanister`) on the Parkade deck. Kick doors are done; add the SWAT monitor wiring so squads
   kick them. Effort M, risk M (monitor wiring unproven on DM doors).
5. DM01B Hot Coffee II, Garage / Ins_Garage: F03 fuel cans with `Explosion_Gas_S` + DocuCam on a few drums
   near the loot (burning oil drums, 17 BarrelEffects, already exist). Effort M, risk M (explosion radius).
6. DM11B Hasta, Capitolio_Main_Hall / Outside_Capitolio: F08-style police chopper pass (plop wave exists;
   add a HeliFlyBehaviourRout drop-off using the 2 existing heli routs). Effort M (drop-off only), risk M.
7. DM09 Retomoto, Retomoto_Square / Hotel_Street: police cars arrive as reinforcements (F06 pattern). Static cop cars already
   stand there; add an arrival squad with `plop`. True drive-in needs MatPosAnim: L. Effort M/L.
8. DM06 park: police-car arrival on the road at escape time, plus sprinklers (F03 style) at the pavilion. Effort M, risk L.
9. DM01 / DM01B Donutshop and Diner counters: register/cash-drawer sets reusing `PC0406_M02_FA_Cashdrawer_01`
   clone (done on DM02). 1 or 2 per counter, +loot. Effort S, risk L.
10. DM02 / DM05A / DM09 civilians fleeing at the start (F01 Running/Screaming); keep inside the proven
    99 actors / 55 squads budget. DM05A is already at 99/53, so DM02 Atrium and DM09 Lobby are the free ones. Effort S.

Further ideas (lower impact): sprinklers on DM09 Lobby and DM03A Bank_Main (cosmetic S); F09 fuse box in DM01
Warehouse control room (L, anim); F05-style elevator on DM09 (exists as DM geometry; the hum/squeak audio is the
cheap part).

## 4. Risks and unproven items

- Everything in section 3 outside "done" is untested live; only offline `check.py` / `check_passes` level.
- Door-gated timer waves are not buildable offline (`kl_arrivals_1024r2`); use timers.
- Vehicle drive-ins need MatPosAnim key data and the vehicle model; no tool ingests those yet.
- Actor budget: proven 99 actors / 55 squads; more crowd on DM05A is past the proven point.
- No data-side holster / aggro trigger; those are hook features.
- DM06, DM09, DM11B have no separable door leaf, so kick doors there need a model graft first.
- DM coordinates were not measured in this pass; build steps must read node positions first.
