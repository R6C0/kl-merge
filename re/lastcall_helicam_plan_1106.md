# Last Call (DM05A) heli outro camera: plan, 2026-11-06 (research only, nothing installed)

Target: live `KLExpansion\Maps\DM05A\F01_Main.zip` md5 e6d2f73e (.prp length 4198642). Units cm.
Marked GUESS = not proven; verify in the bench.

## Problem
EscCamera01 (CCameraBox, mode LookFromPos, eye fixed at CamPos01 (7093, 2181, 2727)) shows an all-black frame
after the heli leaves, also with the heli parked 17.8 m away (lcoutro_1106 77a42f74). Distance is not the cause:
the fixed eye looks at the heli and the sky/void behind it, which is unlit (no geometry below or around the
route, heli model unlit). Stock F06 instead rides in the vehicle.

## Part 1: F06 reference
- Trigger chain: OnlineEscCamTrigger (node 778) -> RelayMessage (779) -> heli group (744) -> EscCamMsgRelay (766)
  -> CameraInVan_01 (CCameraBox, node 761). Focus point = node 762, a ZBoxPrimitive sibling of the ZHeli in the
  heli group, flags 0x200000.
- CameraInVan_01 mode = eFMM_LookAtPos (enum EFMMode: NotSet 0, LookAtPos 1, LookAtKane 2, LookFromPos 3,
  LookFromPosFA 4). Field 9 = node ref to the focus point (REF label, string in key table); floats f1..f6 stock
  values 0, -270, -270, 80, 0, -170 (GUESS on exact meaning of f1..f4; f5/f6 are the world x/y eye offsets).
- CCameraBox fields (unit indices): 0 ECP enum; 1-6 floats; 7,8 flags; 9 node ref string; 10 eFMC enum;
  11 mode enum; 12 by-message-only; 13 release; 14 list; 15 int; 16 player enum.
- LookAtPos: eye = player place + (f5, f6) (world x,y; z not offset), aims at field 9's node place.
  LookFromPos: eye = field 9 node, looks at player. LookFromPosFA: eye = the box's own node, aims at field 9.
  Because children follow a moving heli group, a LookAtPos camera whose player place is the heli pivot rides along.

## Part 2: DM05A as built
- EscCamera01 = node 11576 (CCameraBox), CamPos01 position (7093, 2181, 2727), nodes 11575..11583 are the
  EscCameraSetup group (11575 EscCameraLAST at (7800, 2271, 3500)). Heli tree nodes 10802..10822
  (ShatterGeom 10820 and RotorSound 10819 sit at the group origin with flag 0x200000: usable focus siblings).
- Chain: OnlineEscCamTrigger `CameraTrigger01` -> field 1 -> EscCamera01 directly (no relay). f12 = 1 (message only).
- Byte facts in the e6d2f73e .prp: the EscCamera01 field run occurs exactly once at file offset 2416945:
  floats `0a 00000000 | 0a 00004842`, flags `06 00 06 00`, field 9 `0c 4d080000`, eFMC `0e 4e080000`,
  mode `0e b4100000`. Field 9 token starts at +30 (2416975); the mode token is at 2416985, payload at 2416986.
  New key strings are appended to the key table, the file grows 49 bytes (4198691); bytes after the table shift.

## Part 3: smallest safe patch (in place, no entities)
Edit node 11576 only (kl_fa.edit(sc, cb, ci, fn)):
- us[11] = key `eFMM_LookAtPos`
- us[9]  = key `ROOT\EscCameraSetup!EscCameraLAST` (existing node 11575; or keep CamPos01)
- us[5]  = f5 (float), us[6] = f6 (float)
- keep f12 = 1, so the CameraTrigger01 -> EscCamera01 chain is unchanged.
No entities added, therefore NO SLOT renumbering (.oct/.rmi/.rmc/.HVK untouched); only the .prp changes
(key table append). REF labels unchanged. Round-trip of the edit was verified in memory.

Variant A (recommended, "tower behind"): f5 about -900 (range -750..-1000), f6 about +200 (+150..+300).
Eye rides with the heli, looks back at the lit roof and tower, heli in the foreground; scan showed worst
heli-vs-aim angle of 19-20 degrees along the cut route.
Variant B (stock-faithful): floats 0, -270, -270, 80, 0, -170 with a heli-sibling focus (ShatterGeom 10820 or
RotorSound 10819). Risk (GUESS): pivot about 259 above the group origin, eye nearly vertical over the target
and inside the hull.

## GUESS list (verify live)
1. Sign and axis of f5/f6 offsets.
2. Player place used by LookAtPos equals the heli pivot (piv398) during the outro.
3. Pivot-minus-ZHeli offset (-47, -71, -31).
4. That the tower view is lit enough (not black).
5. Variant B field meanings f1..f4.

## Staging / install
- New script `tools/kl_club_helicam_1106.py` modelled on `tools/kl_club_outro_1106.py`: md5-pinned
  (KNOWN_IN = e6d2f73e, a24d7432), backup `.before-helicam1106`, `--undo`, `--dry`, options `--f5 --f6 --aim`,
  `--variant B`; rebuild the bots zip with `kl_botsonline`. Not yet written.
- Independent of the lcoutro spline cut (60 s -> ~23 s), which stays useful. All staged passes pin live
  e6d2f73e: install one, restage the rest on the new live md5.
- Checks after staging: `python tools/kl_map_escape.py cameras` / `check` (a LookAtPos box lists under
  cameras_no_eye), `kl_fa.check`, `debug/check_passes.py`, `python tools/kl_tests.py`. Check C: free space first.

## Bench plan
Escape run on DM05A: camev/cam log lines should show the eye following piv398; screenshots around shots 19-22
show heli plus tower. If still black: fallback is a light node near the route, or trimming heli visit 2 in the hook.
