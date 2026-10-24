# DM01 Hot Coffee: squads, warehouse doors, scaffolding, cars (PLAN, critiqued and corrected 2026-10-25)

Status: plan, nothing built, nothing installed. Input = live DM01 zip md5 3f503f58 (dm01fix_1025a). Build ON TOP of the output of
doors2_1025a (the job that rebuilds DM01's kick doors/extinguishers); do not start from 3f503f58 directly or the two builds fork.
Cars: see re/dm01_cars_1025.md (both notes were adversarially reviewed against the live zip; corrections below are marked FIXED).

Owner request (2026-10-25): (1) some agents sit in the room they come from, others keep the dm01fix behaviour; (2) more agents in the
warehouse; (3) warehouse doors shut once they are in, so the heisters must kick them; (4) people on the scaffolding, the top of the
warehouse; (5) agents/SWAT arrive in cars and get out.

## Current state (measured on the live zip, scratch copy, read-only)
50 ZFFActor in 23 actor groups (FIXED: not 25). Squad#02..08 = the heisters' own bot squads at x1400-1800, z30400-30800.
Heister START is far NORTH (1632,76,30643) (FIXED: not "east/van side"); van (6153,0,20659); the open route is 171 m (FIXED: not 216).
Engine proven max 99/55, stock 148/90. Headroom about +49 actors / +30 squads.
Enemy squads: FrontMall_01 (2) / FrontMall_02 (2) = 4 men at the Bentleys (x5959-6957, z23924-23995), CheckFront, KitchenBoy, CornerShop,
TheBoss, BossFlank_01..03, plus OldWaves (9 men each, cloned by tools/kl_old_waves.py):
- OldWaves!Wave_1: starts (3130,-10,22750), the SHOP ROOM (x1899-3900, z21900-23608). f3=1 via kl_spawns_1024.ACTIVE.
- OldWaves!Wave_2: starts (5350,0,21550), back lot east of the shop. f3=1.
- OldWaves!Wave_3: starts (2170,60,19030), the WAREHOUSE HALL (floor y60). f3=0, released by the clock chain (OldWaves!Clock).
What the owner saw as "coming to the main building" is the Hunt/Flank (alarm) behaviour of the waves, not the Go_n delays.

## 1. Split Wave_1 (stay in the shop vs keep the route)
FIXED cell choice: Wave_1 cells _06 and _07 (z 21790) stand OUTSIDE the shop back door; _09 (x 1810) is outside the shop x bound
(1899-3900). Hold squad takes ONLY in-shop cells: _01 _02 _03 _04 _05 _08 (4 of them; _09 excluded).
- KL_Hold!Shop (4 men, f3=1): DefendBehaviourRout ONLY (no Hunt, no Flank, no Go_n), fields {1:[Pos refs], 2:1, 3:0, 4:'eDMS_NotSet',
  5:'eDF_NotSet', 8:1}, Pos at their own cells, so they never leave. Behind the staff-corridor kick door.
- OldWaves!Wave_1 (remaining 5: the _06/_07/_09 men + 2 in-shop) keeps the dm01fix behaviour unchanged.
Tool: add `split_wave(B, squad, keep_idx, new_name)` next to make_waves in tools/kl_old_waves.py (clone the squad group, move the actor
slots + Pos refs into the new group, Defend rout cloned from FORM \020_DefendBehaviour_rout_merc_fight_left); add 'KL_Hold!Shop' to
kl_spawns_1024.ACTIVE['DM01']. Wave_2 / back lot: optional KL_Hold!Lot (3 of 9), default off.

## 2. Warehouse: more agents
Warehouse hall: doors 841/842 (hinges (2955,62,19684), (2960,62,17312)), floor y60, x about 1100-2960, z about 16800-19900; Wave_3 (9)
already there but parked (f3=0).
- KL_WH!Floor: 8 men, f3=1, Defend routs on 4 Pos pairs along the hall, template AI_Enemies!FrontMall_01 (kl_old_waves.ENEMY_TEMPLATE['dm01']).
  Positions must be chosen on the crew nav mesh floor y60 and be 600 m-class apart from each other (nav spacing rule of lastcall checks).
- Wave_3 stays the timed counter-attack. Cost +8 actors, +1 squad.

## 3. Scaffolding / upper level
FIXED: there IS real upper-level geometry (not only a control room): Bridge_01 node 838 at (2300,865,19662), Bridge_02 node 839 at
(2300,865,17315), doors 548 / 840 at y 860, floor tiles at y 860, a staircase. But nav covers only 16 polys of part 1, at z 16565-17265
(the control-room end); everything else at y 860 is off-mesh, and part 1 is disconnected from the crew mesh. Nav must not be edited.
- KL_WH!Top, 4 men, f3=1, Defend/hold, positioned ON those 16 polys only (picked with kl_fa_bots.Nav, clearest line to the hall, 2 per
  window at z17300). They are snipers and cannot walk down. Bridges at z 19662 have no nav: nobody stands there.
- Doors 548 / 840 are on the upper level (not warehouse-floor doors; do not put them in the floor door set).
Unproven: AI shoots through glass from a Defend post; heisters reach the level by the existing stairs (verify live). If it fails, drop Top.
Real scaffolding with walkable nav = separate stage-2 job. Cost +4 actors, +1 squad.

## 4. Doors shut once they go in
PLAN['DM01'] in tools/kl_interact_graft.py already holds the dm01fix doors: ('snap',2433,(1,0,0),21909.5), ('at',(4700,0,22160),(0,0,1)),
('snap',961,(1,0,0),21914). Add for the warehouse:
- 841, 842 and BOTH 2569 AND 2570 (FIXED: 2569 is the twin of 2570 and was omitted; 2570 hinge (2479,60,19851), 120 x 240): 'snap' doors, shut.
- West bay 290 cm: virtual_host gives 120 only; two hosts of 145 side by side, or leave open and block with cover. Decide with doors2.
State machine (re/interactivity.md): KickableDoor is ONE-SHOT; its PathBlocker keeps the AI route shut until opened and it does not close
again. So "close behind them" is NOT achievable; "start shut with the squads already inside" IS (Floor, Top, Wave_3 pre-placed before the
heisters arrive). Squads that must leave (Wave_3 counter-attack) either kick the door (KickDoorBehaviourRout as in tools/kl_dm03a_swat_1025.py,
10_Defend -> 20_KickDoor -> 30_Defend; UNPROVEN for the Enemy team on a grafted door) or use an open door (south door).
STILL OPEN (check in the build job with route.py/Nav): a second route into the hall around the doors (the PathBlocker only blocks AI
paths; the mesh is open, DM03A cops walked round a door). If a second route exists the doors are cosmetic for AI, but still force the
heisters to kick (collision is physical).
Clone sources: kl_interact_graft DOOR_GRP 4167, DOOR_KIDS 4168..4189, DOOR_LEAF 4189, DOOR_SHAPE 234 (flags 0x3044000 visible leaf).

## 5. Cars
See re/dm01_cars_1025.md. Summary: the Bentleys are about 7 m from the walked route (visible, not hidden); F03 SWAT cars graft needs the
F03 ANM clips merged (not avoidable); recommended buildable choice = parked car with a plop squad hidden until a timer.

## Build order
1. doors2_1025a output = base. 2. PLAN['DM01'] += 841, 842, 2569, 2570 (+ bay hosts). 3. kl_old_waves: split_wave + make_group helper.
4. kl_spawns_1024.ACTIVE['DM01'] += KL_Hold!Shop, KL_WH!Floor, KL_WH!Top. 5. cars per the cars note. 6. check.py, check_passes,
old_waves.check; count 74/33 (+car squad) against 99/55.
Unproven: idle Defend squads, PathBlocker on Enemy bots, window shots from the upper level, Enemy KickDoor on a grafted door, VehicleExit in DD.
