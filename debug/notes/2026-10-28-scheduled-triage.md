# 2026-10-28 scheduled check-in (cloud, 06:49-07:20 UTC): PC idle, no new crash; .sgp / .sgd translation decoded for the int16 shift, stale octree leaves found in the grafts

The DD and DM folders were again not attached to the scheduled session (connectedFolders empty, as at 02:55); one access request
was granted, so the PC was read this time. IDLE: newest game-folder writes `dinput8.dll` 00:49 UTC (sha1 f520f5d1 and `KLHook.ini`
c3f119f4 = the hashes of the 23:07 restore, so the A1HIRE bench put the owner's dll back), `KLHook.log` 10-27 20:50 (ends in the owner's Alt+F4),
`KLHook.result` PASS F04 0 asserts 0 faults 128814 frames; newest `KL_PortTools\build` folder 10-27 00:50. Nothing launched,
installed or touched on screen. Staged into the cloud for reading only: `kl2.exe` and the .sgp/.sgd/.rmi/.rmc/.gms/.buf members
of the nine stock F0x zips and the 21 KLExpansion maps (pulled out on the PC into `KL_PortTools\_sched_1028_sgp\`, 24 MB,
two zips; the folder can go).

## Dumps

Newest hook dump `KLHook_1.dmp` 10-26 08:11, newest game dump 10-25 19:18: both older than the last note, already written up.
Nothing to triage.

## Offline piece: the .sgp and .sgd parts of the DM11B int16 shift (G8b)

re/map_shift_int16_1027.md listed ".sgp 135 x/z pairs, .sgd 1 pair ... NOT identified one by one" as the last undecoded formats
(PF4 was done 10-27). Both are decoded now; tools/kl_members.py carries the facts and the translation.

### .sgp (ZSoundGraph, vtable 0xb9a614) - READ in kl2.exe, MEASURED on 30 files

The loader (slot 1 = 0x75ee20) keeps the five arrays at this+0x1270 portals / +0x1274 edges / +0x1278 rooms / +0x127c routes /
+0x1280 portal list. A portal is 0x5c bytes; every reader of it in the exe:

| site | reads | meaning |
|---|---|---|
| 0x5866a0 route finder (from the update, slot 3 = 0x576b10) | +0x14 via 0x530e00 (squared distance listener -> point), +0x00 of both portals multiplied and tested against 0 | centre is a world point; +0x00 = openness (0 = shut) |
| 0x4563dd, slot 5 = 0x4da770 | +0x00 against 0 | openness |
| 0x43c030 | +0x0c, +0x10 against a room index | the two rooms |
| slot 4 = 0x67c4d0 -> 0x8d6ef0 | +0x14, +0x20, +0x2c, +0x38, +0x44, +0x50 copied as 3-vectors (corner order reversed by a side flag) | centre, normal, four corners |

Nothing reads +0x04 / +0x08. Data (1053 portals, 6218 edges in the 30 files): +0x00 = 1.0 and +0x04/+0x08 = 0 in all; the normal
is unit (3e-8); the four corners lie in the plane through the centre (within 1.0); the edge distance equals |centre a - centre b|
within 0.003 (translation-invariant). The other 0x5c-stride users in the exe (0x403c40, 0x40b940, 0x4c3f50, 0x5812c0, 0x73bbb0,
0x7a68b0, 0x84e000, 0x87a660) index `[0xdd2598]+0x10` (cut-sequence records), not the sound graph.

Translation = centre + four corners += T, everything else copied: `Sgp.translate(t)` (new method), `Sgp.points(k)`.

### .sgd octrees - MEASURED against the scene (REF -> composed world position)

`Octree.position()` returns the stored order; the docstring's "axes in reverse order" is now a FACT: on the nine stock FA levels
every HavokShatterOctree leaf is on its entity's origin with the stored triple read as (z, y, x) (worst 0.6 units; read as (x, y, z)
the worst is 14-45k). `Octree.world(leaf)` gives (x, y, z). The docstring's unexplained 28 % are ExplodableOctree leaves of
windows, lights and sirens 55..525 units from the origin (GUESS: the explodable's own centre) and the Animation/ police cars
(their animation moves them: 14k off in stock F03/F06/F07 too). Translation = centre += (tz, ty, tx), leaves untouched:
`Octree.translate(t)`, `sgd_translate(data, t)` (SecurityZones centre +0x24 moved in natural order, a GUESS; glass connectivity refused).

### Test

`tools/kl_sgp_sgd_translate_test.py [tx ty tz] [zips | members | folder]`: hand-made fixtures always; on the 30 member sets
(62 files, 1054 portals, 6218 edges, 9833 leaves) every point moves by exactly T, nothing else changes a byte, back within 0.01,
for T = (-12288, 0, -16384) and (4096, 100, -8192). Without the game folders it runs the fixtures only (cloud).

### Finding: stale octree leaves in the grafts (new tool `tools/kl_sgd_audit.py`)

The audit compares every leaf with its entity's composed position (thresholds: shatter 50, explodable 1000 units; Animation/
subtrees are expected to differ). Stock F01..F09: 0 map leaves off (only the animated police cars). Grafts:

- DM03A: 82 leaves of `Locations/M03_A/M03A_Locations.zip` are 7.7k..20.3k units from their entity: all bank-vault pillars /
  shatter pillars / cameras (HavokShatterOctree) and the vault wall plates, neon lamps, exit signs (ExplodableOctree). Varying
  distances with the right entity kinds, so the REFs map correctly and the ENTITIES were moved (GUESS: the vault subtree sits
  under a transform the graft or the layout step changed after the tree was built; Octree.join keeps the quantised points of
  a single source). Effect in play: a grenade next to a vault pillar or plate does not shatter it (the lookup asks the old
  place), 0 crash risk.
- DM11B and DM05A: `EscapeSetup!EscapeChopper` `ShatterGeom` 43.6k / 30.9k off (the chopper was moved by the authoring, its
  shatter point stayed). DM06: the BossChopper's 245 off. DM06B: 10 `While_window_*` 127..726 off. DM03: 72 `Whole_NN` panes
  exactly 85 off (a constant: GUESS a group-origin convention, probably harmless).
- DD10 (L05 graft): `SI0100_L05_Wall_Break_State2!ShatterStart` + 2 more 11.6k off, `AI!Triggers!B5!ShotActivater` 10.9k.

Suggested fix (not done: a build change, verify on the PC): at the end of kl_graft / the layout tools rebuild both trees from the
final scene - shatter leaves at the entity origin (exact by the stock rule), explodable leaves at the origin (GUESS: the stock
offset is unknown, 0..525 units of error against 1000+ today) - and make `kl_sgd_audit.py <map.zip>` part of `debug/check.py`.

## For the shift itself

Decoded now: .gms/.prp (root shift), PF4, .sgp, .sgd. Still undecoded: the .buf head (1942 coordinate-band floats: KEYS tracks,
room gates / lists, light records) and the .HVK / .oct / .rmi / .rmc passes, which are understood but not written as code.
re/map_shift_int16_1027.md updated.

## Owner

- Nothing to install from this check-in. `KL_PortTools\_sched_1028_sgp\` (24 MB, member copies) can be deleted.
- The scheduled task still starts without the DD/DM folders; this run got them by a one-off access request (approved). Setting them
  in the task's settings saves that prompt.
- Built but waiting on you: SHIP out_hirepage_1028 (`C:\kl_build_1024\hirepage_1027\INSTALL_hirepage_1027.bat`, hire page on F12,
  A1HIRE PASS on both seats 01:00) and the rtlift / arcade1to1 bats of 10-27 - the game folder still runs the 23:07 restore
  (dll f520f5d1 / ini c3f119f4).
