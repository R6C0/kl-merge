# Interactivity: what Dog Days' 9 stock FA maps have, and what can go into the Dead Men maps

2026-10-24. Owner wish: kick doors, fire extinguishers, co-op lift shutters, more open shops, scripted vehicles and
events on the Dead Men (DM) maps, "more interactive and alive". OFFLINE research; NOTHING in this note was run in the
game, and no map pass is staged (section 5 says why).

Tool: `tools/kl_interact.py` (read-only; `census`, `survey`, `gaps`, `wiring <level|zip> <regex>`). Counts below come
from `python tools/kl_interact.py census` / `survey` (kl_prpjoin over the .prp token streams).

## 1. Census of the stock maps (controller counts; name hits in brackets)

| template | F01 | F02 | F03 | F04 | F05 | F06 | F07 | F08 | F09 |
|---|---|---|---|---|---|---|---|---|---|
| KickDoorBehaviourRout / _PosInfo (AI kicks) | 7 | 0 | 28 | 0 | 0 | 21 | 0 | 0 | 0 |
| KickDoor (player, ZKickDoorController) | 7 | 0 | 16 | 1 | 0 | 3 | 0 | 0 | 0 |
| KickDoorMonitor (relay "door opened") | 6 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| CoopAirlock (co-op lift shutter) | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 |
| BarrelEffects + Throwable (can: extinguisher, gas) | 12 | 15 | 29 / 26 | 19 | 13 | 12 | 17 | 13 | 15 |
| HavokShatter (breakable) | 12 | 17 | 56 | 31 | 36 | 33 | 44 | 361 | 15 |
| OnlineMoneyContainer (closed loot case) | 58 | 0 | 12 | 0 | 0 | 0 | 0 | 47 | 0 |
| PathBlocker | 10 | 0 | 34 | 18 | 3 | 5 | 6 | 1 | 4 |
| VehicleEffects (car with blast) | 0 | 3 | 1 | 0 | 0 | 2 | 0 | 2 | 0 |
| OnlineEscHavokCar (escape car) | 0 | 1 | 1 | 0 | 0 | 1 | 0 | 1 | 0 |
| HeliFlyBehaviourRout (scripted heli) | 0 | 13 | 8 | 0 | 0 | 12 | 0 | 6 | 0 |
| names: extinguisher | 45 | 80 | 95 | 80 | 3 | 3 | 75 | 97 | 3 |
| names: gascan | 28 | 1 | 23 | 24 | 68 | 63 | 21 | 1 | 78 |
| names: alarm | 29 | 0 | 1 | 0 | 1 | 0 | 0 | 27 | 0 |

(The name counts include particle templates and sub-nodes of each prop, so they are not prop counts.) Every stock map has
both `BarrelEffects` cans and `HavokShatter`; the kick doors and the co-op door are rarer: kick doors F01, F03, F06
(F04 has one), the one co-op shutter F04 and F06.

## 2. How each is wired (read from the .prp; REF labels are the stable ids, see re/graft_formats.md)

**Kick door (player)**: a group `Blockup_Objects_KickableDoor_A_nn` holding `KickDoor_Controller_nn` (class `KickDoor`,
ZKickDoorController, 11 fields): f0 action box (`KickDoor_Action_Backside_nn`), f1 bool, f3 the `KickDoor_Pathblocker_nn`
(AI route shut until opened), f4/f5 lists of door-leaf PROXIES (`KickableDoor_Proxy_Variation01Front_A`, `...02Back_A`,
MatPosAnimProxy that play the leaf's key-framed MatPosAnim), f6/f7 arrow boxes front/back, f8/f9 focus targets, f10 a
REF to a cover changer. The AI side is `KickDoorBehaviourRout` + `KickDoorBehaviour_PosInfo` (where the AI stands to
kick) and a `KickdoorMonitor!KickDoor_RelayList_Door08` RelayMessageList (AITrigger `DoorOpened`). The AI passes over a loot
that is "behind a door" (field 11, +0x5c) unless a kick door stands near (re/bots_loot.md). Needs: door-leaf MODELS with
MatPosAnim KEY DATA in the .buf "raw" blocks (the .ANM is skeleton-only), HVK body for the leaf, the player's
`/Special_moves/Kick_Door` clip (DD player: present).

**Co-op lift shutter (ZCOOPAirlockController, 28 fields)** F04 `SI0100_F04_Coop_Move_Dxxr_04!Controller`, F06
`PC0200_F06_Coop_Move_Dxxr_01!Controller`. A set of ~15 siblings, almost all MODEL-FREE boxes: Controller (ZBoxPrimitive +
CoopAirlock); f2/f3 `CoopAirLock_ArrowBegin_A/B_00` (ZSTDOBJ, model 0); f4/f5 `CoopAirLock_Box_A/B_00` (ZBoxPrimitive, the
two stand-here boxes); f6 bool; f11 string `CoopAirlockEnter`; f12..f15 player clips
(`/Movement/Transitions/Stand_To_Crouch`, `/Movement/Crouch/Stand`, `/Movement/Transitions/Crouch_To_Stand`,
`/Special_moves/Kick_Door`); f23 COMPLETION LIST = `MatPosAnimProxy_coop` (plays `left_dxxr_01`/`right_dxxr_01`, MatPosAnim
message `Activate`), `CoopAirLock_Pathblocker_00` (PathBlocker, AI route opens), `Box_crash_sound` (Audio_PlaySound, message
Deactivate), `GeomActivator_shake_area` (ActivateGeom of `TriggerBox_shake_area`, a TriggerBox -> `camera_shake`
DocuCamControl), `Timer_get_rid_of_triggerbox_again` (TriggerDelay2 -> `GeomDeactivator_shake_area`); f24 =
`KickDoor_CoverState_Act_01` (CoverStateChanger), and `..._Deact_Startup_01` at load. A `Gate_was_or_wasnt_blocked`
GateGroup (2 GatePath) tells the AI which way exists. Needs: the two leaf models + their key data for the lifting
animation. A model-free variant (hide the existing static shutter with DeactivateGeom) is possible: see 4.

**Extinguisher / gas can**: `FX0900_ALL_FireExtinguisher_nn!Can` is a ZHavokRigidBody (so it needs a body in the .HVK and a
model in the .prm) with controllers BarrelEffects (12 fields: f0..f5 floats = fuse/time/radius numbers, f9 REF to
`...!GeomActivator`) and Throwable (clip names `/Special_moves/Throw_Canister_1H_2H/*`, `Throwable_FireExtinguisher`),
siblings `!RightHandPosBox`, `!GeomActivator`, emitters (smoke/debris) and sound. The DM maps have only the particle
TEMPLATES (`Extinguisher_Smoke_#`, `Flames_GasCanister_#`), no can objects (kl_interact survey: BarrelEffects 0 on all
DM maps except DM01B 13 and DM11B 2, and those are the DM barrels).

**Loot case**: `OnlineMoneyContainer` node (a CONTAINER object is inactive until opened by a RelayMessageList message
`AITrigger Open`) + `OnlineMoneyCtrl`/`TriggerBox2`. Used by F01 (58), F03 (12), F08 (47). DM02 has 26 already (watch store
and jewelry store, floor 2).

**Alarm / vehicles / events**: alarms are Audio nodes (F01 29, F08 27 names); scripted helicopters are
`HeliFlyBehaviourRout` + `HeliScriptRout` + `HeliNetSync` (F02 13, F03 8, F06 12, F08 6); vehicles `VehicleEffects` +
`ZHavokCar`/`OnlineEscHavokCar` (see re/engine_facts.md, re/maps.md).

## 3. What the DM maps have (survey, same tool)

All DM maps have HavokShatter (DM01B 50, DM02 59, DM03 198, DM09 331 ...) and ShotActivate, MatPosAnim (91..166, but the
animated ones are cosmetic: DM02's MatPosAnim controllers are not on its shutters). Missing everywhere: KickDoor*, CoopAirlock,
Throwable, extinguisher cans (BarrelEffects only DM01B 13, DM11B 2). DM02: 13 SHUTTER nodes (`SI0401_M02_FA_RollerShutterA_01..04`
on three floors, `Shutters_A_01` in the respawn room) are plain STATIC ZSTDOBJ with no controller: at room-local
(x +-1990, y 0/500/1000, z -2665, -2033, 1032, 1660). The open shops (StoreWatch west and StoreJewel east, floor 2) already
carry 26 OnlineMoneyContainers; the other frontages are closed and EMPTY.

## 4. Graftability with the existing tooling (re/graft_formats.md, kl_fa_bots.Maker)

| piece | what must be brought | existing tool | verdict |
|---|---|---|---|
| Co-op shutter control set (controller, arrows, boxes, PathBlocker, completion nodes) | clone nodes only (no model) with `Maker.clone('F04', ...)`; arrows/boxes need new positions; REF labels renumbered by the apply step (kl_fa_cover.apply is the template; it only writes cover boxes now) | Maker, kl_prpjoin.join, kl_scene | feasible; the apply step needs generalising |
| ... its lifting animation | leaf models + MatPosAnim raw key data | none for keys (kl_prmgraph merges meshes) | not available; instead hide the DM static shutter with `DeactivateGeom` (stock pattern F07 `GeomDeactivator`) in f23 |
| Loot behind the shutters | OnlineMoneyCtrl/TriggerBox2 + a prop; totals/AI loot field 11 | kl_fa_loot.Edit, clone path (re/campaign_fa_tooling.md 269) | feasible but large; every new stack changes the AI loot choice and the exit totals: needs a live round |
| Kick door | leaf model + key data + HVK + PathBlocker | kl_prmgraph, kl_texmat, kl_hvk_donor | graft, not clone; DM doors with an existing leaf could host the controller if the leaf had a clip: none found |
| Extinguisher / gas can | model in .prm (+textures), HVK rigid body, emitters, sound | kl_prmgraph, kl_texmat, kl_hvk_donor | graft; per map one group `FX0900_ALL_FireExtinguisher_nn` |
| Scripted vehicles / events | the F02/F03/F06/F08 heli and car sets | kl_fa_bank (heli), kl_escape | done for escape; ambient vehicles not started |

## 5. Why no map pass is staged

The only piece needing no new model data is the co-op shutter control set. Staged blind it would (a) rest on three
unproven assumptions: `DeactivateGeom` removes the key-framed/static collision of a DM shutter (support: F07 vision
blocker only), the airlock completion list accepts a DeactivateGeom as target without a `MatPosAnimProxy`, and the
controller does not require its animation proxy to be present, and (b) open EMPTY shops, which is the opposite of the
wish (loot behind the doors). The loot half is a separate large job (stack clone + AI loot field 11 + exit totals). A
half-built door that crashes DM02 is worse than none, so nothing is installed or staged. The plan below is the order in
which to do it with a live round between steps.

## 6. Plan

1. DM02 co-op shutters, step A (no new loot): add the control set at the four atrium frontages of floor 1
   (`RollerShutterA_01..04` of `Atrium_101a`), completion list = [PathBlocker, DeactivateGeom -> shutter], boxes 120 in front.
   Live test: do both players get the CoopAirlockEnter prompt, does the shutter vanish, can the player walk through.
2. Step B: loot behind them: clone the StoreWatch cashbox group (`PC0406_M02_FA_Cashdrawer_01`, MatPosAnim drawer, in-map
   models, no .prm work) and the 6 case groups into the opened shops; rerun `kl_fa_bots` loot planning so the AI's loot
   pick and the total are right.
3. Kick doors: pick DM doors that exist as separate leaf nodes (DM03, DM09 interiors), graft the F03 `KickDoor_Controller`
   set with `kl_prmgraph` (leaf model) + a new MatPosAnim.
4. Extinguishers/gas cans: graft one can group per map from F04 (`FX0900_ALL_FireExtinguisher_01`: model, HVK body,
   emitters, `GeomActivator`) at 8..12 places per map near cover; feature toggle "(recommended on)" in
   `tools/kl_mod_options.py` is unnecessary because they are map data, but a hook toggle is needed if the throw clip gets
   a hook patch.
5. Ambient vehicles and events: copy the heli set per map only where a heli already exists; no new work before step 1-2 pass.

Excluded (rule of this job): DM05A and Hasta (DM11B) zips.

## Result 2026-10-24 (round 2): steps 3 and 4 built, staged, not installed
tools/kl_interact_graft.py grafts from F03 (doors) and F04 (cans) via kl_prpjoin/kl_prmgraph/kl_octree, three-leg donor chain with sequential dry-run append.
- Door: F03 PC0800_ALL_KickableDoor_E_01 group (leaf 4189, model 13862, HVK shape 234 type 4 slab) placed at the host hinge with stored_rot(host R); leaf model
  scaled (sx,sy,1) from host width/height (root box + vertex chunks 13857, 13852); KEYS tracks (raw+40) point at one copy of the F03 .buf region 0x47270..0x47800.
  Host entity, its HVK placement/shape refs and .prp subtree are removed (kl_prpjoin.join skip=); hosts that other nodes reference are refused.
- Can: F04 FX0900_ALL_FireExtinguisher_01 (rigid HVK + .hrd, GeomActivator, Emitter_Debris templates), 4 per map near fights.
- Plan/hosts: DM01 [1330 961 841 842 493], DM01B [1373 7169 8844 7166 7167], DM03A [6521 3594 3647 3737 3790]; DM06 and DM09 have no separable door leaf.
- Unknown until a live run: kick trigger fires, KEYS swing plays on a type-4 body, door side, door oct record unscaled (up to ~8%), DM cover/path controllers.
