# 2026-10-27 scheduled check-in (cloud, 10:48-11:15 UTC): PC busy, no new crash; Mod Options rows caught up with the proven online keys

The DD and DM folders were not attached to this scheduled session; one access request was granted (read-only use). The PC was
BUSY: local sessions (ce / c9) committing until 10:35 UTC, `dinput8.dll` written 10:49:07, `KLHook.log` / `KLHook.result` 10:48:43
(`RESULT PASS (script reached pass) exit code 0, asserts 0, faults 0, loads 2, frames 81057`, a bench round, 299 s). Nothing launched,
installed, staged into the game or touched on screen.

## Dumps

Newest hook dump `KLHook_1.dmp` 10-26 08:11 UTC, newest game dump `kl2_490_crash_2026_10_25T19_18_39` - both older than the last log
note and already written up. Nothing to triage.

## Head health

MinGW i686 installed here: `tools/run_harness_linux.sh --check-hook` SHIP and TEST 0 errors (7 pre-existing warnings); all 26 harnesses
compile except the two that cannot by design (klhigh_bits_test needs sed's bits.inc, klmem_test uses MSVC _ReturnAddress). No Wine, so
not run. `tools/kl_mod_options.py --check-defaults klhook` exit 0.

## Offline piece: tools/kl_mod_options.py vs klhook/KLHook.ini (SHIP 1027w installed for the owner at 10:31)

ff11724 flipped the repo ini's online keys to `(recommended on) proven live: CE27_ALL2D..G`; the owner-facing Mod Options table still
said `recommended off until benched` for 19 of those rows (hudonline, onlinecrew, onlineread, onlinenames, onlinekilled, onlinekilledai,
onlineround, onlinefeed, onlinetags, onlinetaghold, onlinevanicon, onlineboard, onlineboardstate, onlineintrostate, gradesbadge,
gradesrankup, gradesletter, hostopts, charonline). Its Recommended button would have turned the owner's proven online HUD off.

1. The 19 rows say on now, each `why` ends with the bench the ini cites. Five proven keys without a row got one: onlineboardcarrier,
   onlineintrocarrier, onlineshopnames, onlinetaghidedead, onlinetagprobe (dflt from klu_inii / GetPrivateProfileIntA, --check-defaults agrees).
2. New `--check-rec klhook\KLHook.ini`: each row's `rec` against the `(recommended on|off)` marker on its OWN key in the repo ini (on the
   key's line or in the comment lines above that name it; `until` / `after` forms = off for now), and the proven recommended-on keys no row
   offers. Exit 1 on a mismatch. Now: "every row agrees with the ini markers", no row-less proven key, 111 rows have no marker (not checked).
3. Bug found by the check's own_key: the tag rows (onlinetagstyle, onlinetaghold, ...) and the Grades rows (gradesbadge, gradesrankup,
   gradesletter, gradesonlinetags) had their shared prerequisite (`[HUD] OnlineTags`, `[Grades] Enable`) as FIRST key = the key `state()`
   reads and the key an off-write clears. So `--list` showed onlinetagstyle ON while OnlineTagStyle=0, and Recommended (gradesonlinetags off)
   would have written `[HUD] OnlineTags=0` and `[Grades] Enable=0`: every tag and Grades row off. Own key first now, prerequisite after with
   off value None (the table's existing 'helper key' convention). Against the repo ini, `--recommended` writes no tag / Grades key any more.
4. `tools/kl_mod_options_test.py`: 32 checks (marker forms, own_key, check_rec on a synthetic ini and on the repo ini, table shape, plan()).

Not run: the Tk window and the Windows profile-API read-back (no Windows here); the CLI paths exercised were --list / --recommended (dry) /
--check-defaults / --check-rec on the repo ini.

Owner / local sessions: nothing to install. When a key is moved to `(recommended on) proven live` in klhook/KLHook.ini, run
`python tools\kl_mod_options.py --check-rec klhook\KLHook.ini` and flip its row (or add one). `INSTALL KL Mod Options.bat` carries the new table
to `<DD>\KLModOptions\` when the owner next wants the window refreshed.

# 2026-10-27 second scheduled check-in (cloud, 14:49-15:10 UTC): PC busy, no new crash; the hook's ini documents every Mod Options key

Folders attached after one access request (read-only use). BUSY: local sessions committing until 14:19 UTC (head 0ae8a9f, ce's P2P5F
proof log), `dinput8.dll` written 14:44:48, `KLHook.ini` 14:44:26, `KLHook.log` / `KLHook.result` 14:44:22 (`RESULT PASS (script reached
pass) exit code 0, asserts 0, faults 0, loads 2, frames 89321`, 299 s, a bench round: the tail shows the online HUD weapon panel, the
bot bd: lines and the heli probe, `result now 'Time_Up' + LifeLost`, clock 27 s left of 360). Nothing launched, installed, staged into the
game or touched on screen.

## Dumps

Newest hook dump `KLHook_1.dmp` 10-26 08:11, newest game dump `kl2_490_crash_2026_10_25T19_18_39`: both older than the last log note and
already written up. Nothing to triage. The live ini carries `[Online]` twice (lines 1103 and 1106, both `Read=1`): harmless while they
agree (the profile API reads the first), worth folding into one the next time a session edits it.

## Head health (0ae8a9f)

MinGW i686: `tools/run_harness_linux.sh --check-hook` SHIP and TEST 0 errors (7 pre-existing warnings, unchanged). `kl_mod_options.py
--check-defaults klhook` exit 0, `--check-rec` clean, `kl_mod_options_test.py` 32/32 before the change.

## Offline piece: the keys the hook reads vs the keys klhook/KLHook.ini names

c9's client-freeze fix `[Input] PumpNoBlock` (289ce45, "recommended on" in its log line) and `MouseMoveMs`, and the `[Stall] Trace /
StallMsgMs` diagnostics, were read by klhook.c (lines 1017-1023) but named in no ini: neither the repo ini nor the owner's live one has an
`[Input]` or `[Stall]` section, so nobody could switch them on from the ini without reading the source. Scanning every
`GetPrivateProfileInt/String(..., klh_ini)` call and the per-module helpers (`klu_inii`, `klu_inif`, `klb_inif`, ...) against the repo
ini: 1036 keys read, 37 of them the keys of KL Mod Options rows with no line at all (17 modules without a section: [Shop], [Adrenaline],
[BotDown], [Shield], [Stinger], [Traits], ...; also [Voice] Enable, [KLHook] FastExit, [Lobby] Rows12/TimeMin/TimeMax/RoundsMax,
[HUD] HideIdleEscape / OnlinePopups, [FrameLimit] Adaptive / MapCap, [ReShade] ReloadFx, [ShopPage] TabNames).

1. `klhook/KLHook.ini`: new `[Stall]` and `[Input]` sections after [FrameLimit] (Trace=1 / StallMsgMs=20 / MouseMoveMs=0 / PumpNoBlock=0
   commented at the DLL defaults, c9's WHY in short; PumpNoBlock=1 `(recommended on) proven live: C27_PNB1 / HUD6` - c9 committed a second
   `[Input] PumpNoBlock=1` section at 14:54 while this ran (22e5150, 'PNB1/HUD6 proven, both seats, 0 faults'); the rebase kept both, the
   profile API reads only the first [Input], so the two were folded into one right after the push);
   one commented `;Key=<DLL default>   ; KL Mod Options row '<id>': <label> (recommended on|off)` line per rowless key at the end of its
   section, 17 new sections before [Online]. 95 lines added, nothing changed or moved.
2. `tools/kl_mod_options.py`: row `pumpnoblock` (G_STAB, recommended on, benched PNB1/HUD6; a DLL without the wrap ignores the key, the
   owner's SHIP 1027x is one); `scan_keys()` (the key scan check_defaults had, now also string helpers, and only calls that read klh_ini:
   klauto.c's kla_ini and kljoin.c's `file` keys are not KLHook.ini keys); `--check-ini KLHOOK_DIR INI` = row keys the ini never mentions
   (exit 1) + the count of other read keys it leaves out (`--verbose` lists them: 487, probes / logs / per-map tuning, left as they are);
   `ini_rec` reads a `(recommended ...)` marker on a commented `;Key=` line too, so `--check-rec` checks 47 more rows (66 unchecked, was 113),
   all agree. Tried and dropped: the other direction (ini keys no source reads): keys come from name tables, sprintf (P%d, Thr%d, F%02d)
   and per-map sections, every version listed live keys as stale.
3. `tools/kl_mod_options_test.py` 44 checks (commented-key markers, ini_mentions, scan_keys on a synthetic source with an Int helper, a
   String helper and a kla_ini read, check_ini both ways, the repo ini mentions every row key).

Not run: the Tk window and the Windows profile-API read-back (no Windows here); `--set pumpnoblock=on --apply` on a temp copy inserts
`PumpNoBlock=1` under the new `[Input]` header (the commented documentation line stays).

Owner / local sessions: nothing to install (the next SHIP with klhook.c's wrap gets PumpNoBlock=1 from the ini). New keys: a line in the repo ini (commented at the default is
enough) keeps `--check-ini` green and gives the owner a place to see them.

# 2026-10-27 scheduled check-in (cloud, 18:48-19:05 UTC): PC busy, no new crash; page II online rows caught up

The folders were again not attached; one access request was granted. BUSY: head 3dc716a 17:56 (c9), `dinput8.dll` written 18:45:15,
`KLHook.ini` 18:44:57, `KLHook.log` / `KLHook.result` 18:44:54 (`exit=0 scene F03 level_loaded=1 asserts=0 faults=0 frames=100970
script=62 ms=300000`, a 300 s bench round in the F03 slot). Nothing launched, installed, staged into the game or touched on screen.

## Dumps

Newest hook dump `KLHook_1.dmp` 10-26 08:11, newest game dump `kl2_490_crash_2026_10_25T19_18_39`: both older than the last log note and
already written up. Nothing to triage.

## Head health

`tools/kl_mod_options.py --check-rec klhook/KLHook.ini` FAILED at head and `kl_mod_options_test.py` with it (1 of 44): ce's 2fe8304 marked
`[ShopPage] OnlineLook` `(recommended on; implied by OnlineApply)` after ALL2Y, the `shoponline` row still said off. `--check-defaults` and
`--check-ini` clean. Fix in this commit (see re/mod_options.md 19:00 entry): row flipped, rows `shoponlinebuy` / `shoponlineearly` added for the
proven OnlineApply (+OnlineSend) / OnlineEarlyMake keys, and the row-less scan of `check_rec` now reads commented `;Key=` lines (that is how
the hook's ini carries all four keys, so the scan had missed them). 46 checks PASS, `--check-rec` "every row agrees".

Owner: nothing to install in the game; the installed copy of the table (`<DD>\KLModOptions\`, put there by `INSTALL KL Mod Options.bat`) only
learns the new rows when that bat is run again from an updated KL_PortTools.

# 2026-10-27 scheduled check-in (cloud, 22:47-23:30 UTC): PC busy, no new crash; PF4 navmesh floats decoded for the int16 map shift

Folders attached after one access request (read-only use). BUSY: `KLHook.ini` written 22:35:46 UTC, `dinput8.dll` 21:51:19, `KLHook.log`
20:50:42 (its tail: an Alt+F4 close of a DM09 round at 255 fps), `KLHook.result` 20:00:28 (`state=PASS` F04, 0 asserts 0 faults, 128814 frames,
299 s); head at 6a73923 (G8b Plan B static check). Nothing launched, installed, staged into the game or touched on screen; the only write on
the PC is `<DM>\KL_PortTools\sched_1027_gms\` (the stock levels' `*_Main.gms` members and the DM11B build's, unzipped for this analysis;
safe to delete).

## Dumps

Newest hook dump `KLHook_1.dmp` 10-26 08:11, newest game dump `kl2_490_crash_2026_10_25T19_18_39`: both older than the last log note and
already written up. Nothing to triage.

## Offline piece: the PF4 navigation mesh under a world translation (re/map_shift_int16_1027.md listed it as "NOT fully decoded")

Read in kl2.exe (capstone on the staged exe):

- `0x55e6e0` locate(point): for each area (0x48 bytes, `[ZData+4]`, count `[+0x48]`) whose box holds the point's x (`+0x30 <= x <= +0x3c`)
  and z (`+0x38 <= z <= +0x44`; `+0x34`/`+0x40` are the y bounds, untested here) it calls `0x80d600(area, x, z)` and keeps the polygon whose
  height (`0x55f5a0`) is nearest the point's y (start 100000).
- `0x80d600`: walks array 0 (`[ZData+0x18]`, 20-byte nodes) from `area[9]` (`[area+0x24]`, -1 = none): `next = (a*x + b*z >= c) ? child1 :
  child0` with a = +8, b = +0xc, c = +0x10 (the "three floats"); a negative child is a leaf, polygon = -2 - child.
- `0x55f5a0(ZData, polygon, x, z)`: walks array 1 (`[ZData+0x1c]`) from the polygon's `+0x18` node; the children are RELATIVE to that start
  node (`add edx, edi` at 0x55f5c7); leaf = -1 - child = an array-2 record (`[ZData+0x20]`, 12 bytes) P, Q, R: height = P*x + Q*z + R.
- The parser `0x63e750` fixes the ZData layout: +0x4 areas, +0x8 waypoints, +0xc vertices, +0x10 links, +0x14 polygons, +0x18/+0x1c trees,
  +0x20 planes, +0x24.. arrays 8-12, counts at +0x38..+0x68.

Checked on the 20 stock Dog Days meshes and the DM11B build (`tools/kl_pf4_translate_test.py`): the centroid of 27786 of 27800 polygons
descends tree 0 to its own polygon (the 13 others are slivers / none); 27288 of 27799 centroid heights are within 1 unit of the mean vertex
height (the rest non-planar polygons); the vertex "normal" (array 6 +0xc) is the unit sum of the inward normals of the wall edges (neighbour
-1) meeting at the vertex, exact on 66592 of 67499 used vertices (zero on the 464 unused ones), so it carries no distance term; waypoints are
(x, z, h) like vertices; 121711 of 121713 vertices lie inside their area's box in all three axes.

So a world translation t only changes: node c += a*tx + b*tz, plane R += ty - P*tx - Q*tz, vertices / waypoints / boxes += t. Implemented as
`kl_pf4.translate(block, t)` (plus `locate` / `height` helpers that follow the two functions above). The test moves every mesh by the DM11B
T = (-12288, 0, -16384) and by (4096, 100, -8192): `check()` passes before and after, every position moved by exactly t, every centroid
locates the SAME polygon, the height is the original + ty (two centroids per T sit within float32 rounding of a tree-1 split line of a
non-planar polygon and get the neighbouring sub-plane: 0.4-0.7 units, accepted when the original mesh gives that height within 0.01 units of
the point), and the round trip returns within float32 rounding. Exactness caveat for the study: the split constants c are ~1e7 (a, b are not
unit), ulp 1, so moving them is NOT bit-exact (worst drift 0.0035 units across the line); the stock meshes already carry that precision.

What this changes for G8b: PF4 is no longer a reason not to build the shift; `.buf` head / `.sgp` floats still are, and the bots' behaviour on a
shifted mesh is only testable live. Nothing built or staged for the game.

Owner / local sessions: nothing to install. `<DM>\KL_PortTools\sched_1027_gms\` can be deleted.
