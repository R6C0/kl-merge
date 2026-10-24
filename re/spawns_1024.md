# Spawns pass 2026-10-24 (tools/kl_spawns_1024.py)

Owner: enemies/citizens must not "plop in"; they should come from vehicles/doors or already be there.

## Audit (kl_map_ai spawns, live zips)
PLOP squads (shown in sight, within 40 m of a place inside their waking box): DM01B 3 (05_Squad_00, 05_Squad_02, 06_010_Wave_01_Middle),
DM09 2 (Squad_SWAT_From_Behind_South, Squad_RoadBlock_South), DM11B 2 (Hasta, other job, not touched). DM01, DM02, DM03A, DM06, DM06B:
timer-wave squads are out of sight of the start, no plop. DM05A (club): other job. Civilians: DM02's are in the world and shown from the load.

## Fix
Mechanism: ZSquadScript field 3 = 0 hides the men until the squad gets a goal. The pass sets field 3 = 1 for every PLOP squad (they stand
in the world from the load). Only the .prp member changes (no entity added/removed). Idempotent: re-audit shows 0 PLOP, rerun says nothing to change.
Staged: C:/kl_build_1024/spawns_1024n (INSTALL/UNDO spawns.bat; backups .before-1024spawns). Live md5s expected: DM01B F03 badc0bee..., DM09 F06 fa9ecf84...
(other passes chained before must keep these, else rebuild: python tools/kl_spawns_1024.py --force).

## Not done (and why)
- Vehicle/door ARRIVALS: DD's are animated cutscene vans (.ANM in DD coordinates, never copied) and KickDoor routs; DM's own spline cars
  already drive in (their exit rout is lost in conversion, see kl_map_ai cars --car-exit). Needs animation data / live test.
- New civilians: kl_fa_civs appends a .prm chunk (actor limit risk). Not staged.
- DM09: these two street squads are now present from the load (previously an ambush at tbExitLoot); actor budget and gameplay change need a live look.
