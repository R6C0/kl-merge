# The bank (Withdrawal, M03_FA_A): the AI heisters and the yard wall

2026-10-11. OFFLINE: nothing here ran in the game, nothing is installed. Owner, on Withdrawal: "the ai cant leave
on withdrawal because theres no climb animation ... they dont go through the wall", "the van never ends there".
Live log `<work>\build\klhook\live\R12_DM03.log` (build `z_route\M03`): all seven bots at heist stage 1 within a
minute, stage 2 by 1:24 .. 2:29 after GO, then "in-play g2", "van 0" to the end of the run (4 min 20 s).

Two answers, both built: the link in the level data is REPAIRED (the cause is established, section 1), and the
hook can carry a bot over by the teleport that is known from Retomoto (`klhook/klhop.c`, section 2), off unless
enabled. Build with both: `<work>\build\z_hop\M03`. Hooks: `<work>\build\klhook\ship_hop1`, `test_hop1`.

## 1. Why the drop link was never taken - ESTABLISHED (static reading + all stock meshes)

`tools/kl_fa_bots.py add_drop` wrote one link of kind 2 (array 7) and its two waypoints (array 5), and renumbered
everything that counts waypoints - except one byte.

- kl2.exe 0x5cdd70 is the path search (A* over polygons and waypoints). Its polygon step, after the portals:

      0x5ce320  mov eax, [esp+0x18]        ; the polygon record (array 3, 0x20 bytes)
      0x5ce324  mov ecx, [eax+0x10]        ; 'waypoints before this polygon'
      0x5ce327  cmp ecx, -1 / je  0x5ce3a9
      0x5ce32c  mov al, [eax+1]            ; BYTE +1
      0x5ce32f  test al, al / jbe 0x5ce3a9 ; 0 -> the polygon has no waypoint: nothing more
      0x5ce333  edx = [this+0x2c]          ; array 10
      0x5ce350  eax = [edx + (ecx + k) * 4]; waypoint = array5 + eax * 0x1c -> pushed as a search node (0x690460, kind -5)
      ...       k = 0 .. [polygon+1] - 1

  A waypoint node, when popped ([node+0x10] == -1, 0x5ce016), walks its link range (0x5ce01a.. `[wp+0xc]` ..
  `[wp+0x10]`, 16-byte records) and pushes the target waypoint with the target's polygon (kind -3).
  So **polygon byte +1 is the number of waypoints on the polygon** (kl_pf4's notes called it "flags"), and a
  waypoint is reached ONLY through its polygon's count.
- Measured (`scratchpad\wpcount.py`, then as a rule in `kl_maps.nav_facts`, `python tools/kl_maps.py navtest`):
  byte +1 == the number of array-5 records that name the polygon on **27,384 of 27,384** polygons of the 21 stock
  Dog Days meshes, and array 10 from 'waypoints before' on names exactly those waypoints on 4,015 of 4,015
  polygons that have any. Values 0 .. 10.
- Our mesh (`z_final\M03`, `z_route\M03`, every M03 build with `--drop` up to 2026-10-10): polygons 527 (take-off)
  and 687 (landing) each have one waypoint and byte +1 = 0. The link was in the file and **no search could ever
  see it**. Everything the earlier checks tested (ranges, running sums, the permutation) held.
- Fix (exact, one byte a polygon): `add_drop.put()` raises the byte. `kl_maps.nav_facts` has the two rules now
  (so `add_drop` refuses a mesh that breaks them), `kl_fa_bots.check` FAILs a build whose mesh does
  ("the drop link CANNOT be taken ... build it again": `z_route\M03` -> 2 FAIL), `kl_fa_bots.diff` allows exactly
  +1 on the drop's two polygons, `kl_pf4.py`'s docstring is corrected.
- NOT established: that the AI then takes the link. What is read: the search, and the mover
  `ZFFSpecialLink@Locomotion` 0x4a5160 (kind 2 = `/Movement/Fall/Fall_1m`, starts within 20 of the link's start;
  re/bots.md 12.3). 232 across is at the stock maximum (228); our waypoints lie 1.0 inside their polygons, stock's
  on the edge. Stock: 192 links in 12 levels, all kind 2, plain path finding - no stock controller (DropDown,
  Vault ...) is needed for them: the kind goes into the path node and the locomotion plays the clip.

## 2. The hook hop: `klhook/klhop.c` ([CrewHop])

A new file, not more of `klcrew_rt.c` (argued in its header: that part moves the whole crew once at the player's
jump and is tied to a jump entry; this one watches every bot for the whole round). The routine and its guards are
shared, not copied: `klcrew_rt.c` now has `klt_refuse(actor)` (vtable 0xbb3bac, node flag bit 10, the two int3
pointers +0x77c / +0x780, +0xec readable, `[actor+0x7c0]` writable, `[actor+0x50c]` an object of the game),
`klt_tele_known()` (the first 14 bytes of 0x62a900) and `klt_teleport(actor, pos)`; `klt_move` uses them (same
tests, same order). From `klbot.c`: `klb_read` (crew records), `klb_level` (not on a stock level); from
`klescort.c`: `kle_node`, `kle_human`, `kle_block`, `kle_callable`.

What it does: KLHook.ini `[CrewHop] Enable=1` AND `[CrewHop]` sections in the level's `KLJoin.ini` (the file
`kljoin.c` reads beside the archive that is opened: a file with no `[Join]` is taken - "0 box(es)" -, a file beside
a stock archive is dropped; so no new file name, `kl_expansion.SIDE` and `debug/slot.py SIDE` carry it already).
In an Arcade round (session mode 4, state 0x19) on a level that is not the stock one of its slot, on the main
loop's thread, ten times a second: every AI crew record in play whose actor has been within Radius / Height of
From for Wait seconds at heist stage >= Stage (and, Player=1, after the human was nearer to To.1 than to From) is
teleported by 0x62a900 to the next free To.n - not a place given away in the last 2 s, not one a crew member
stands within 100 of; at most one bot per 0.5 s; each bot once per hop per round; never a bot held as a human
shield. Landing places nearer than 100 to an earlier one, or inside From's own radius, are dropped at reading.

Keys (KLHook.ini): `Enable`, `Dry` (watch and log, call nothing), `Reorder`, `Log` (2 = every 5 s where every bot
stands against every hop). Side file: `From`, `Radius` (300), `Height` (150), `Wait` (3), `Stage` (2), `Player`
(0), `Places`, `To.1` .. `To.8`, `Lift`; up to four hops (`[CrewHop.2]` ..).

After the hop: the bot's chain had ended the gather step and STARTED the next step, whose places are beyond the
drop; a Defend step waits for its man to arrive (klescort.c section 1). Put on the far side he can walk to the
order he holds: the chain needs no message. ASSUMPTION (only the game can show it): the soldier plans a path to an
order it already has once it stands on the other mesh part. If not: `Reorder=1` gives the soldier ITS OWN order
again 0.5 s after the hop through the soldier's order routine 0x760e50 (place from its own defend block, arguments
of a Defend step; klescort.c's call - which has not run live either). And on the bank the landing places are in the
level exit box: stage 3, the vehicle is called, and when it starts to wait the rules order every stage-3 bot to
the boarding place themselves (slot 194, 0x8fb04c).

A bot's place is read two ways (its node's world place; the floats at actor+0x460) and EITHER counts: neither is
proven for a ZFFActor. Every line prints both; the first live run settles it.

## 3. Level data: `tools/kl_fa_bots.py`

- `hop_plan` (in `plan()`, per drop link): From = the middle of the seven gather places; Radius = their farthest
  + 120, and it must not hold the link's end; Height 60 (the landing is 70 lower); seven landing places on the
  landing's own mesh part (mesh read without links), 100 and more beyond the foot of the wall, 60 from every
  mesh edge, 110 apart, 250 from the van's line. `hop_write` puts the section into `<out>\KLJoin.ini`.
- `hop_check` (in `check()`, so in `kl_fa_bots_dyn.py check` too): From and every To on the mesh, on the two
  sides of a drop link; every squad's place before the link inside From; the link's end NOT inside it; clearance,
  100 apart, out of the lane, as many places as bots; from every landing place a way without a link to every
  place the chains name beyond the drop. Negative test (`scratchpad\hopneg.py`, seven spoiled hops): PASS.
- Other maps: no drop, no section, no file (M02 check unchanged: PASS).

`<work>\build\z_hop\M03\KLJoin.ini`:

    [CrewHop]
    From=-1729.3 220 -909.3
    Radius=240
    Height=60
    Wait=6
    Stage=2
    Player=0
    Places=7
    To.1=-1695.4 150 -283.6
    To.2=-1775.4 150 -363.6
    To.3=-1775.4 150 -203.6
    To.4=-1615.4 150 -363.6
    To.5=-1615.4 150 -203.6
    To.6=-1855.4 150 -283.6
    To.7=-1535.4 150 -283.6

NOT AS ASKED: "not in a level exit box" cannot hold. `Triggers!ExitTrigger_01` is x -3592 .. 4408, z -540 .. 1460:
the whole street side of the wall, the link's own end (z -533) too. That is the plan since re/bots.md 12.3 (the
bot that comes down has stage 3 and calls the vehicle - the owner's "the van never ends there"); check() NOTEs
it. Wait=6 (klhop.c's default is 3) so that a bot the repaired link carries (135 to the take-off, a 1 m fall) is
gone before the hook acts; the landing is outside the radius (376 from From) and outside the height.

## 4. Builds and checks

    python tools\kl_fa_bots.py owner <work>\build\z_final\_van <work>\build\z_hop\_bots M03     (the bots build: link + hop file)
    python tools\kl_fa_bots_dyn.py build <work>\build\z_hop\_bots\M03 <work>\build\z_hop\M03    (routes, as z_route)

`z_hop\M03\F01_Main.zip` sha1 94587886e8991be0fc403595c114ab4b5d87e22c (200,794,546 bytes).

| check | last line |
|---|---|
| `kl_fa_bots.py check z_hop\M03` | RESULT: PASS (0 FAIL, 2 NOTE); 7 bots, 754 squad nodes; large blocks .prm 62581504, .ANM 22202616, .fxc 17760648, .WAV 22669648 |
| `kl_fa_bots.py diff z_final\_van\M03 z_hop\_bots\M03` | RESULT: only the squad was added, 1 drop link(s) in the navigation mesh |
| `kl_fa_bots_dyn.py check z_hop\M03` | RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 3 NOTE) |
| `kl_fa_bots_dyn.py diff z_hop\_bots\M03 z_hop\M03` | RESULT: only the squad's steps were made anew |
| `kl_impact.py z_hop\M03` | problems: 0 in 1 levels |
| `kl_maps.py audit z_hop\M03` | RESULT: PASS (0 findings that must be 0, 0 known and accepted) |
| `kl_map_guns.py check z_hop\M03` | ... problems: 0 |
| `kl_map_escape.py van-check z_hop\M03` | 0 fault(s) |
| `kl_maps.py navtest` | the two new rules 27384 of 27384 and 4015 of 4015 |
| `kl_fa_bots.py check z_route\M03` (the build that ran) | RESULT: FAIL (2 FAIL, 2 NOTE) - the mesh rule |

Hooks (both compile with no warning, `cl /W3`; scratch `G:\kl_scratch\hop1`):
`ship_hop1\dinput8.dll` sha1 212f26414a403cddadd3cb4a6335ac0a74bdb65e, `test_hop1\dinput8.dll` sha1
f82c2573f4549a1f910836c09005ce191d1c3168. klescort.c is in, off by default.

## 5. Live checks (none run)

KLHook.ini, besides what a bots run has ([Bots] Enable=1 Log=1):

    [CrewHop]
    Enable=1
    Dry=1          H0 only
    Log=2

- **H0, the link alone** (`z_hop\M03`, Dry=1): do the bots drop by themselves now? Expect `hop: 1 hop(s) from
  ...KLJoin.ini for level f03\f03_main`, `hop: hop 1: From (-1729, 220, -909) radius 240 height 60, wait 6.0 s,
  stage 2, player 0; 7 landing places, To.1 (-1695, 150, -284)`, per bot `hop: bot N is at From of hop 1: node
  (...), +0x460 (...), heist stage 2; carried over in 6.0 s if it stays`, then EITHER `hop: bot N left From of hop 1
  after x s by itself` and `bots: record N (bot): heist stage 2 -> 3` (the link works: the hook is not needed) OR
  `hop: bot N ... WOULD be put on To.k ... DRY RUN` (it does not). The two places in each line show which reading
  of a bot's place is right.
- **H1** Dry=0: `hop: bot N (actor ...) hop 1: at From for 6.x s, node (...) -> To.k (...): now node (...), +0x460
  (...); heist stage 2, vehicle state 0; its order (...)`, 2 s later `hop: bot N is at node (...) 2 s after hop 1,
  heist stage 3, vehicle state 1` (it moved on, the box gave stage 3, the van is called).
- **H2** only if H1's bots land and stand: `Reorder=1` -> `hop: bot N hop 1: its own order (...) given again by the
  soldier's order routine; the game set (...)`.
- **H3** `bots: ... van 3` and `record N (bot): aboard`; the round ends with the van leaving.
- **H4** a second round in the same process: the hops happen again (the round reset).

## 6. Assumptions, not done

- Nothing ran. The repaired link: only the search was read; that the mover plays the fall over 232 units is
  the old ASSUMPTION of re/bots.md 12.3.
- After a hop the soldier re-plans to the order it holds: ASSUMPTION (section 2). Reorder=1 and the rules' own
  boarding order are the two fall-backs.
- actor+0x460 and the node place as "where a bot stands": both read, either counts.
- Wait 6, Radius margin 120, Height 60, landing search 250 / 450 / 100: GUESS.
- The new mesh rule makes `kl_fa_bots.check` FAIL every M03 build made before today (`z_final`, `z_route`,
  `z_cover2`, the tab's DM03): they are as broken as they were, the check now says so. `z_cover2\M03` has to be
  made again on `z_hop\_bots\M03` (`kl_fa_cover.py` then `kl_fa_bots_dyn.py`): not done (not this job's files).
- Online: not looked at (klcrew_rt.c's note holds: the actors belong to the host).
- No off-game rig ran `klv_tick` against a made-up round (the harness sources are not in the repo).
