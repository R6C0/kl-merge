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

# 2026-10-28 second scheduled check-in (cloud, 10:50-11:20 UTC): PC idle, no new crash; stale .sgd leaves are Dead Men's own data, the stock octree frame rule recovered, the graft now repairs them

Folders again absent from the task; one access request granted. IDLE: newest game-folder writes are still `dinput8.dll` 00:49
UTC and the ReShade files 00:44 (the owner's session), `KLHook.log` 10-27 20:50, `KLHook.result` PASS F04 0 asserts 0 faults
128814 frames, newest `KL_PortTools\build` 10-27 00:50, newest dumps 10-26 08:11 / 10-25 19:18 (both written up). Nothing
launched, installed or touched on screen. Read-only on the PC apart from `KL_PortTools\_sched_1028_sgp\` (member copies: now also
`dmsrc\` = gms/buf/sgd of Dead Men's M01FAA M02FAA M03A M03FAA M05A M06A M06FAA M09A M09B M11B, the two .HVK of M03A / DM03A and
three zips; 38 MB, the whole folder can go).

## Dumps

None newer than the last note.

## Finding 1: the DM03A vault leaves are stale in Dead Men's own M03A_Main.sgd

The 07:20 note GUESSED the graft or a layout step moved the vault. Audit of the Dead Men SOURCE scenes (kl_sgd_audit on the
dmsrc members): `SRC_M03_A` has 83 stale leaves with the same REF names and the same distances (20328, 19413, 18526 ...) as the
graft's 82. The stored point is the entity's position with x and z SWAPPED (leaf (-12722, -590, 35), entity (35, -590, -12722),
all 83), and the .HVK placement of the same REF (metres: (0, -6, -127)) agrees with the .gms composition, so the collision
and the drawing are where the .gms says and the octree leaf is the odd one: a shipped Dead Men data bug (in Dead Men those
vault pillars / cameras / plates presumably never shattered from a grenade either). Also in the sources, below 2000 units and
left alone as conventions: M03FAA `Whole_NN` panes exactly 85 off (72 leaves), helicopter `ShatterGeom` 245 (M06FAA, M11B
050_Rooftop), M06A `While_window_*` 127..726, stock F06 `Lights_Back_Off` 1169 (explodable). Ours: the EscapeChopper
`ShatterGeom` of DM11B / DM05A (43.6k / 30.9k: the escape authoring moves the chopper; the leaf kept the source point) and the
L05 wall / ShotActivater in DD10 (11.6k / 10.9k).

## Finding 2: the stock octree frame rule (FACT, 36 of 36 trees)

The "centre" stored at +4 is the MINIMUM of the leaf points on each axis (stored order): the smallest point quantises to exactly
0x8000 on every axis in all 36 stock DD and DM source trees. scale = 32000 / the largest axis span (the largest point lands on
0xfd00; in 17 of 37 trees on 0xfcff, which means the stock quantiser truncates in float32 and the span was a hair above). The
first survey's "q range .. 64769" was the max corner (= min + 1). round() of the decoded positions reproduces all 13,227
stored leaf values (0 mismatches), so a rebuild is byte-stable for leaves that do not move. `Octree.join` (multi-source) used
a centre-of-box / 0xe000 frame before; it now builds the stock frame.

## Code (tools, self-tested in the cloud on the 30 graft member sets + 10 Dead Men sources)

- `kl_members.Octree.build(points)` (stock frame), `quantise`, `replace({REF: point})` (re-quantises inside the frame, rebuilds
  the frame when a point falls outside), `sgd_refresh(data, world, limit=STALE, skip)` -> (bytes, moved). `STALE` = 2000 units
  on both trees (the repair limit; the audit's REPORT limits stay 50 / 2000).
- `kl_sgd_audit.py`: Animation/ leaves reported apart ("expected": stock F03/F06/F07 keep their animated police cars' leaves
  off the rest position) and never repaired; `refresh(gms, buf, sgd, packed=)`; `--fix out.zip` writes a copy of one level zip
  with the .sgd member refreshed (in place refused). Exit 1 only for stale leaves outside Animation/.
- `kl_graft.py`: after `A.write()` and `sgd_join`, `kl_sgd_audit.refresh(gms, buf, sgd, packed=False)`; logs
  "  .sgd: N stale octree leaves put back on their entity (...)". Every authoring step (escape placement included) runs before.
- `debug/check.py`: prints the stale count of the zip (a build fresh from kl_graft shows 0; a post-build layout tool that
  moved entities shows up) - guarded, never fails the check.
- Result on the current builds (cloud, members only): DM03A 82 moved (30 shatter + 52 explodable), DM11B 1, DM05A 1, DD10 4,
  everything else unchanged byte for byte; every refreshed tree round-trips and audits clean.

## Owner

- Nothing to install. The repair takes effect on the NEXT graft build of DM03A / DM11B / DM05A / DD10 (or `python
  tools/kl_sgd_audit.py <zip> --fix <out.zip>` on an installed KLExpansion zip, then the usual verify + install). Expected in
  play: a grenade beside a vault pillar / camera / neon lamp in DM03A shatters it; the escape chopper's shatter body in DM11B /
  DM05A reacts where the chopper is. Not run in the game.
- `KL_PortTools\_sched_1028_sgp\` (38 MB) can be deleted. The task still starts without its folders.

---

# 2026-10-28 scheduled check-in, evening (cloud, 18:48-19:05 UTC): PC BUSY (c9 + ce, commits every few minutes), no PC read; klrappel_test de-flaked

No folder was attached to this session again (connectedFolders empty) and no access request was sent: `origin/rtp-schemas` had
commits at 18:44, 18:44, 18:38, 18:27 UTC (c9 A1LIFT3f / Ramp log, ce LPB3 merge), so the VS Code sessions hold the PC and
the game. Nothing launched, installed, staged or touched on screen; no dump read (the live sessions triage their own runs).

## Self-tests on the day's branch head (3a9e0b8)

`python tools/kl_tests.py` in the cloud after `apt-get install gcc-multilib`: 5 py + 15 C logic tests PASS, 0 fail
(klshot_test / kllootsync_test from today included), 13 SDK-only skips. Nothing committed today broke an off-game test.

## Offline piece: klrappel_test "flaky (timing)" (c9's 20:25 note) - cause found and removed

`klrp_tick` looks for a start at most once per 50 ms of `GetTickCount()` (`static DWORD scene_at`, klrappel.c:256). The harness
got past that gate with `Sleep(60)` before cases 1b-5 and 7. GetTickCount steps in ~15.6 ms units, so a 60 ms sleep can read as
46.9 ms by the clock (3 steps) and the tick is skipped; the descent then begins at some later tick inside the frame loop, or not
at all. Reproduced here: the HEAD harness built against a stub whose clock steps 15.625 ms fails "frame 52 of 104 is half the
drop" at 2 of 8 clock phases (the other cases got a second look inside their loops and passed), exactly the intermittent
picture. Fix in `klrappel_test.c` only (klrappel.c untouched): the harness owns the clock (`#define GetTickCount() fake_tick()`,
`pass_ms()`, a frame advances 40 ms), every `Sleep` is gone, and two new cases pin the behaviour the sleeps hid: 7b (a new
clip within 2 s of the channel going is not a second descent; after 2 s it is) and 8 (49 ms after the last look nothing is
looked at, 50 ms later it begins, across a GetTickCount wrap 0xFFFFFFE0 -> 0x11). 18 checks, 8/8 phases ALL PASS with the
stepped-clock stub; MinGW i686 build -Wall -Wextra clean. The stub lives only in this session's scratch (the repo's
test_shim stays types-only by design). NOT RUN with cl on the PC: `cl /nologo /W3 klrappel_test.c` next local session.

## Owner

- Nothing to install. If a scheduled cloud check-in should ever read the PC again, attach DD + DM to its task (both were missing
  again); with the live sessions working all week that is optional.
