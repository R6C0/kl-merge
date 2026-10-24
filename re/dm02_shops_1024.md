# DM02 mall: open shops with loot, co-op shutters (2026-10-24, offline only)

Tool: `tools/kl_dm02_shops_1024.py` (build / stage). Input md5-pinned: live DM02 `F02_Main.zip` bb6fc9e0d5926f943c8ba1bf41bde649.
Staged: `C:/kl_build_1024/dm02shops_1024r2/{A,B}` (F02_Main.zip, shops.json, shops.ps1, INSTALL/UNDO .bat). Backup tag `.before-1024shops`
(A and B share it: install only one; UNDO first to switch). Target `<DD>\KLExpansion\Maps\DM02\F02_Main.zip`.

## Variants
- A (co-op): 3 floor-2 roller shutters become co-op shutters (F04 CoopAirlock control set cloned: Controller, 2 arrows, 2 boxes, Pathblocker,
  frame turned to the shutter; completion list = [Pathblocker, Open], Open = DeactivateGeom of that shutter's static HVK shape) + 2 shutters
  (NW floor 2, floor 1 Atrium_101a) opened at round start by a TriggerDelay2 (`KLShops_OpenTimer`, appended to AIMonitor field 2). 88 entities,
  REF 34149..34236, md5 30b3ddf02cc864c462c803924c1226a1.
- B (fallback, no co-op nodes): all 5 shutters open at round start. 67 entities, REF 34149..34215, md5 4bc4bf99c65cb9b829b566a4cc8cccf7.
- Both: Montre_Desk + Cashdrawer (7 nodes, StoreWatch_201a) cloned per set behind each shutter; OnlineMoneyCtrl amount 150000 (co-op shops,
  2 sets each) / 80000 (always-open, 1 set), field 11 ("behind a door") = 1. Level loot total 2,570,000 -> 3,630,000 (+1,060,000); the bots'
  own total is unchanged (cannot_take empty for all 8 new drawers). Window check (800/400): 4 of 8 drawers have a bot place within 800, none are
  excluded; nearest 696.

## Why no leaf-model graft
F04's door leaves (models 19438/19452, ~218x218) cannot span DM02's 640x331 frontage, and a real graft needs a 32-chunk .prm append,
MAT/TEX merge, hvk donor join and a .buf key-block transplant that no tool provides. So the DM02 shutter itself is the moving part.

## Guesses (need a live test)
DeactivateGeom as CoopAirlock's completion action; CoopAirlock working without MatPosAnimProxy and leaves; clones render at the root;
corridors are dark (no lights) and off the nav mesh; counters have no HVK (walk-through).

## Proven offline
check.py: no new layout problems. check_passes.py: PASS (A, B). All 66 refs in KL_Shops! resolve; shutter targets right; ASCII grids show
each shop is an empty walled floored room; 23258 slot ids renumbered consistently. Installer rehearsed on scratch copies only: install,
undo byte-identical, reinstall same md5, other variant refused, wrong live md5 refused. Rebuild is deterministic and idempotent (refuses a built zip).
