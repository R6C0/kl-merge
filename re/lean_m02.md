# Late Night Opening: 'broke my shoulder leaning' (2026-10-10, offline; nothing here was run in the game)

Owner, playing the Dead Men maps tab: *'on late night i think the thing u did broke my shoulder leaning but
withdrawl its fine'*. Build on the tab: `<work>\build\y_loot2\M02` (installed as `KLExpansion\Maps\DM02\F02_Main.zip`,
181,870,899 bytes - the same file). The bank: `y_loot2\M03`.

**Verdict: no cause found in the level.** Nothing the cover / camera-side code reads differs between the morning
build (`z_maps\M02`) and the evening one, and every step applied to M02 was applied to M03 in the same form. One
thing IS particular to this map and was always in it: 91 no-cover boxes (section 3). A build without them is ready
for an A / B run (section 4). What the owner means exactly ('lean out of cover' or 'the camera changes shoulder')
is not known; both mechanisms are below.

## 1. How it works in kl2.exe (read; capstone)

| what | where | facts |
|---|---|---|
| keys | binding text 0xb50af8 | `TapCover` / `HoldCover` = **C** (pad A). `SwitchCameraSide` = **hold X** (pad: right stick click). X is also `TapPulseCheck` / `HoldPulseCheck`. |
| camera side, by key | 0x640080 (action handler, third branch) | toggles `[player+0x29a0]`, then 0x74a120(player, left, 0.0) and 0x62ee80 (RMC `SetLeftShoulder`). Refused when: tuning `[[0x168d7c0]+0x209]` == 0 (a bool, default 1, set at 0x5267a9; no hook module writes it), `[player+0x2720] & 2` clear, `[player+0x2954]` set (aiming, re/firstperson_camera.md), `[player+0xd50]` set (camera bone binding), `[player+0xed0]` bit 7. No level object is read. |
| camera side, the setter | 0x74a120, 27 callers | side forced LEFT while the object `[player+0x2948]` (made by the player's constructor, 0x57cf90; ASSUMPTION: the down-not-dead state, 0x658700 starts it) has flag bit 0 and state != 3; forced RIGHT while `[player+0xa54]` bit 1. Else the caller's wish -> `[player+0x818]` bit 10. Callers include the cover movement (0x71f3f9: the side follows the cover), respawn (0x4b2d9c). |
| the blend between the shoulders | 0x9088c0 | along the level object named by the define `CameraTransitionSpline` (`AllLevels/camerasetup.zip\CameraTransitionSpline`, one in every build, the same bytes in F02, z_maps\M02, y_loot2\M02, y_loot2\M03). |
| what a cover is | `CFFCoverList` slot 13, 0x6d6a80 | every ZSTDOBJ-family entity whose NAME matches `*coverbox*` (at most 5000); `*coverboxcar*`, `*coverboxm*`, `*coverboxl*` -> low, `*coverboxh*` -> high (0x603830); another name is collected and skipped. Nothing else makes a cover: no list in the level (the `FFCoverList` ZLIST is empty in stock levels too), not the navigation mesh. |
| where cover is forbidden | `ZNoCoverBox` slot 14, 0x723fb0; `ZFFPlayerMovementStandCover` slot 14, 0x71f050 | each `NoCoverBox` links itself into a list at gamedata+0x8c0 (no limit). The stand-cover movement answers 0 at once when 0x6fa6a0 finds the PLAYER's place inside one (the box's point test, margin `[0xb554fc]` = -10). ASSUMPTION: slot 14 = 'may this movement run'; then inside such a box there is no cover and so no lean. |
| `CCameraBox` | re/map_escape.md 1.2 | an AREA camera only with fields 12 and 13 both clear. M02 has two boxes: `EscCamera01` (field 12 = 1: by message only; 10 x 10 x 10 at the origin) and `EscCameraLAST` (field 13 = 1: release). Neither is an area camera, so the mode edit `eFMM_LookFromPosFA -> eFMM_LookFromPos` cannot reach a player who is not sent the trigger's message - and the same edit is on all four maps. Field 0 (`ECP_*`) is a camera PROFILE, not a shoulder. |

## 2. What differs between the builds (all measured on the files)

`z_maps\M02` -> `t_maps2\M02` (kl_map_tune: guns, escape, ai) -> `y_loot2\M02` (kl_fa_bots). M03 the same chain.

- Members: `.MAT .TEX .buf .gms .oct .prm .prp .rmc .rmi` changed, the other 22 equal - identical list for M03.
- **.prp, node by node by path** (21,934 old nodes): M02 changes = 10 `ZSoldier` health, 6 + 2 `ZSquadScript`, 2
  `TriggerDelay`, 1 `TriggerCounter`, 1 `VehicleMoveBehaviourRout` list, 1 enemy weapon, 1 `CCameraBox` mode, 1
  `AIMonitor` list, 1 `OnlineEscVehicleMonitor` list, 7 gun model indices, 1 gun sound offset. M03: the same
  kinds (12 health, 8 + 2 squad, 1 enter-rout list ...). No `NoCoverBox`, `PlayerCoverCollision`, `CoverList`,
  cover box, camera, spline or player node differs. 288 new nodes, all under `Gameplay!merc_bot_squad!*`.
- **Tune step, entity by entity**: all 21,934 `.gms` records equal (name, class, flags, group, frame, aux, REF,
  parent); navigation mesh, `.buf` head / tail, dynamic list, tags, heap budget, FDX, room pairs equal; the model
  closure in the `.prm` and the collision record in the `.oct` equal for every old entity except the seven gun
  models. Of the 272 entities named `*coverbox*` (182 covers, 90 no-cover boxes): 272 models equal, 272 collision
  records equal.
- **Bots step**: `python tools\kl_fa_bots.py diff t_maps2\M02 y_loot2\M02` -> 'only the squad was added': 21,934
  entities as they were, 3,328 collision records and the `.oct` tail equal, room sets / `.rmi` / `.rmc` name the
  entities they named, `.prm` differs only in 2,297 record offsets. (M03 additionally got one drop link in the
  navigation mesh - the map where leaning WORKS.)
- **What only M02 got**: 28 `RelayMessageList` boxes. Their 46 targets are 23 `HavokShatterGlass` panes
  ('Activate') and 23 `OnlineMoneyContainer` boxes ('Open'); none is or holds a cover box.
- **The hook** (`<DD>\KLHook.log`, 18:53:33 M02, 18:57:31 M03, one process): the same lines in both sessions -
  health 550 -> 401.5, body 9235 -> 9011 (Kane), look, seven bots drawn at random. Only M02 has
  `character: the tick is not on the game's thread ... the body cannot be changed` once at 18:53:35.8 (the first
  level of the process; the swap went through 2.2 s later). `klbalance.c` writes R+0x00..+0x14 and the health
  object; no module writes the fields of section 1.

So: the escape camera, the slot renumbering, the relays, kl_map_ai's lists and the gun looks are each cleared as
far as files can clear them.

## 3. What is particular to Late Night Opening (Dead Men's own data, in every build of it)

`python tools\kl_fix_lean.py check <folder>`:

| | NoCoverBox | their footprints | covers (CoverBoxH / M / L / Car) | covers within 60 of a no-cover box |
|---|---:|---:|---:|---:|
| M02 Late Night Opening | 91 | 645 m2 | 182 | 59 |
| M03 Withdrawal | 40 | 206 m2 | 104 | 19 |
| stock F01 F02 F03 F07 L03 | 0 | - | 306 / 153 / 462 / 380 / 1192 | - |

The largest on M02: the start (`Spawn_NoCoverBox_01`, 4.6 x 13 m - where the round begins), both escalators over
all three floors (3.1 x 17..18 m each), the cafe (two, 8.5 x 6 and 5.4 x 7.6 m), the cash machines (10.4 x 2.4 m),
the two long display walls of the watch shop (`Watch_NoCoverBox_01 / 02`, 9.5 x 1.6 m), `Paco`, benches, pillars,
shop fronts. Dead Men stuck the player to cover by itself and needed 'not here' boxes; Dog Days takes cover on a
key and no stock level has one.

GUESS, not established: this is what the owner feels (a third of the map's covers sit at a no-cover box, against a
fifth on the bank). AGAINST it: the boxes were in the morning build too, which the owner did not complain about.

## 4. The A / B build

`python tools\kl_fix_lean.py apply <work>\build\y_loot2\M02 <work>\build\z_lean\M02` - the NoCoverBox controller
taken off the 91 boxes (the boxes stay, as plain ZBoxPrimitive; the two `PlayerCoverCollision` boxes untouched).
Only the `.prp` member differs (4,708,655 -> 4,708,018 bytes); node diff: 91 nodes lose one controller, nothing else.
On the result: `kl_maps.py audit` PASS (0 findings, 6 known), `kl_fa_bots.py check` PASS (0 FAIL, 1 NOTE),
`kl_map_guns.py check` problems: 0, `kl_impact.py` problems: 0. NOT installed, NOT run. The same step fits the
other maps (M03 40, M01 21, M06 31 boxes) if it turns out to be right.

## 5. What tells level from hook (one variable each; the owner or a live agent)

1. Say which it is: C to take cover and it does not stick / will not lean out at a corner - or X (hold) and the
   camera does not change shoulder. And WHERE on the map (the start, the escalators, a shop).
   A Medal clip 'Saved the last 3m' was taken at the end of the 18:53 round: it shows it.
2. Late Night Opening with `z_lean\M02` in place of DM02: better -> the no-cover boxes (section 3).
3. Late Night Opening with `[Balance] Enable=0`; then `[Crew] Random=0`; then `[Character] Enable=0`; then
   `[Guns] Start=0 Set=0` (KLHook.ini, one at a time): better -> that module.
4. The morning build `z_maps\M02` on the tab (it has no bots): bad too -> it was never the evening's changes.
5. Late Night Opening is the only map of the four that ran in slot F02 that evening; the morning rounds ran it in
   slot F01 (log: 177,760,845-byte archive against stock F01). Whether kl2.exe treats slot F02 differently for
   the player was not read. A build of DM02 placed under another slot's redirect would answer it.

## 6. Not established

- What `[player+0x2948]` is (named 'down-not-dead state' above by its starter only) and when its flag bit 0 is set.
- Slot 14 of `ZFFPlayerMovementStandCover` as 'may run' (read as such; not seen live).
- The passive pictures of the round (`<work>\research\watch\20261010_185258`, one every ~10 s) show the camera on
  the left shoulder on BOTH maps most of the time and the player in cover on both; they do not show the fault.
