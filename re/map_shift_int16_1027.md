# DM11B shifted into the online int16 range - design and feasibility (2026-10-27, offline, static)

Why: online positions are int16 with no scale (re/netcode.md 8; 0x5a0ff0, 0x404e60, 0x8413b0); DM11B gameplay is at x 9.5k..44.4k, z 26k..47.8k.
Measured on the live F04_Main.zip (tools/kl_shift_audit.py): placed gameplay entities x -2644..44400, z -1057..47816, y -4383..8776 (y: killbox -60000 only).
Both x AND z exceed 32767 (z by 15k), so a spawn move or an x-only shift is not enough.

CHOSEN T = (-12288, 0, -16384) (GUESS: any dx <= -11634, dz <= -15049 fits; powers of two make the float32 additions exact for every value
that stays in the same binade or goes down). After T: x -14932..32112, z -17441..31432. Fits. Tight east edge (x 32112 vs 32767).
Systems stay: AllLevels/mainsceneincludes_multiplayer (weapon dummies at z -29853), CloneGroup_*, Heroes are NOT moved (443 of 627 roots move).

## Is there a root transform?
No single one: the .gms has 627 flat top-level entities, no wrapper group. A shift is "add T to every map top-level entity's translation"
(FACT: the world position of a child is composed under its parent, kl_int16_range_check.mul; the prp carries a position only as ZGEOM[2] = node
props 14..16: 4380 large triples, all at that index, 2 more at idx 23 are sizes 32000/4000/32000, not positions).
Zero-translation top-level entities (baked world geometry, 36 model roots + 50 big vertex chunks, 235k vertex floats in .prm with bounds like
20500..23053) are fine ONLY if they get trans = T (their vertices are world coords; the entity transform composes). They are NOT local-space.

## Formats
RELATIVE (no change when the entity tree moves): .prm vertices of ordinary models (local, placed by the entity), .prm bounds of those, .ANM of
doors/props (GUESS: parent-local), the prp apart from ZGEOM[2].
MOVED BY THE ROOT SHIFT, nothing else: .gms entity translations, ZGEOM[2] in the .prp (both, kl_interact_graft.shift does the pair), baked
world models under zero-trans roots.
ABSOLUTE, each needs its own pass:
- .HVK (re/havok.md): placement position (+0x00) and the MOPP offset (x,y,z,scale) of every static code AND every list code; code bytes are
  relative to the offset and stay (precedent: tools/kl_dm02_rearwall_1026.move, live-installed 10-26). Header box. Type 2..5 placements move
  too (no code). Static shape vertices are local (FACT: position + R*v).
- .oct: every ZOctreeCompiled tree has an origin (+0x04 / record +0x08); items are quantised relative to it, so origin += T and nothing else
  (the quantised boxes are identical). Same format in .rmi/.rmc plus the room box records (centre +0x28, second point +0x34; half extents and
  matrix unchanged). 5 trees per room, copies of the origin in each slot.
- PF4 navmesh (.gms +0x34, tools/kl_pf4.py): DECODED 2026-10-27 (scheduled check-in, kl2.exe 0x55e6e0 locate / 0x80d600 tree 0 /
  0x55f5a0 height, verified on the 20 stock Dog Days meshes + the DM11B build): tree nodes are split lines `a x + b z >= c` (c += a tx + b tz),
  array 2 is the height plane `h = P x + Q z + R` (R += ty - P tx - Q tz), vertices / waypoints are (x, z, h) += t, area boxes (min xyz, max
  xyz) += t, the vertex "normal" is a unit sum of wall-edge normals (no distance term: unchanged). `kl_pf4.translate(block, t)` does it;
  `tools/kl_pf4_translate_test.py` proves on every mesh: same polygon for every centroid after the move, height + ty within 0.05, round trip
  within float32 rounding (worst split-line drift 0.0035 units, the stock meshes carry c ~ 1e7 at ulp 1 already). Risk left: none known in
  the mesh itself; the bots' use of it after a shift is only testable live.
- .sgp (room sound graph): DECODED 2026-10-28 (scheduled check-in, kl2.exe ZSoundGraph 0x5866a0 / 0x8d6ef0 / 0x4da770 read,
  30 files measured; kl_members docstring): a portal (0x5c) = openness, 0, 0, room a, room b, centre, unit normal, 4 corners;
  the edge distance is |centre a - centre b|. Centre + corners += t, nothing else: `kl_members.Sgp.translate(t)`.
- .sgd: the two point octrees store their centre as (z, y, x) (FACT: every stock HavokShatter leaf is on its entity's origin that
  way, worst 0.6); centre += (tz, ty, tx), the quantised leaves stay: `Octree.translate` / `sgd_translate` (SecurityZones centre
  moved in natural order = GUESS; DM11B has none). `tools/kl_sgp_sgd_translate_test.py` proves both on every stock and graft
  member (exact move, back within 0.01, no other byte changed). NOTE the grafts carry stale leaves already (DM11B's EscapeChopper
  ShatterGeom 43.6k off, DM03A 82 vault leaves 8..20k off): `tools/kl_sgd_audit.py`, debug/notes/2026-10-28-scheduled-triage.md.
  2026-10-28 second check-in: the DM03A vault leaves are stale in Dead Men's OWN M03A_Main.sgd (same 83 REFs and distances, x/z
  swapped while the .HVK placement agrees with the .gms): source data, not the graft. Frame rule recovered (36 stock + DM
  trees exact): stored centre = MIN corner of the leaf points, scale = 32000 / largest span, quantiser truncates in float32.
  `Octree.build` / `Octree.replace` / `sgd_refresh` (kl_members), `kl_sgd_audit.refresh` + `--fix out.zip`; kl_graft calls the
  refresh on the joined .sgd (leaves over 2000 units from their entity go back on it, Animation/ subtrees excepted); debug/check.py
  prints the count. Not yet run through a real build on the PC.
- .buf head 1942 pairs (KEYS tracks, room gates/lists, GUESS: some are positions), light records, SND/ZLNK emitter data: NOT
  identified one by one.
Rooms: .rmi/.rmc lookups use the point, so a missed box = "no room" = silent/lit wrongly, not a crash.

## Verdict
Feasible in principle (every part is a translation; exactness: NOT free, see below), but NOT built: it still needs the .buf head translation
(undecoded float meanings), cannot be validated offline, and a half-shifted map is worse than the stopgap. Staged: nothing. PF4, .sgp and
.sgd are no longer blockers (translate() of each, above); .HVK / .oct / .rmi / .rmc are understood but not written as code. Exactness note (measured 2026-10-27): a power-of-two T keeps the INTEGER part exact, not every float32: a vertex
like 1950.369384765625 (needs 2^-12) moved to 14238.37 (ulp 2^-10) is rounded by up to 0.0005 units; the mesh's split-line constants c ~ 1e7
are rounded by up to 1 (= 0.004 units across the line). Harmless, but a bit-exact round trip is not available; compare with tolerances.
Build order if done: (1) roots + gms/prp, (2) HVK, (3) oct/rmi/rmc, (4) PF4 (kl_pf4.translate), .sgp (Sgp.translate), .sgd (sgd_translate), .buf after decoding, (5) verify with a new check: every
absolute float of the map minus T equals the original (round-trip), kl_int16_range_check reports 0, then ship as its own folder (e.g. DM11S) so
[Int16Guard] OnlineSkip=DM11B does not apply (no key change), and test: load, 'pos: player' near the spawn, bots walk, shoot/loot/grenade,
escape, glass/doors, ambience (rooms), and compare nav (bots reach loot) with the unshifted map.

## Cheaper alternative (GUESS, not checked in the exe)
A codec bias in the hook: subtract/add a constant (Bx, Bz) in the three int16 pack/unpack helpers (0x5a0ff0 player+actor positions, 0x404e60 /
0x8413b0 the RMC vec3 args). One symmetric patch on both peers covers grenades, drops, barrels, actors with no map change. Risk: if the
helpers are also used for non-position int16 (velocity, direction) they would be biased too - read the callers first.

## Plan B static check (2026-10-27, offline, kl2.exe disassembly) - VERDICT: NOT CLEAN, not built
Tools: capstone on kl2.exe (debug/kl.py Exe), scans: direct callers of the helpers, every `call _ftol2 0xa8d330` triple, every `movsx word / fild` unpack.

### The three "helpers" are not the codec
- 0x5a0ff0 = `SetPosition(vec3*)` of a dataset object: ftol(y)->[ecx+0xa], ftol(z)->[ecx+0xc], ftol(x)->[ecx+8] (int16, truncation toward zero, no scale).
  It is a method of several dataset classes (this = obj+0x110 / +0x170 / +0x350), called from 14 sites (table below).
- 0x404e60 / 0x8413b0 = ONE of many identical "pack xyz as 3 x int16, call RMC stub" wrappers (404e60 -> 0x4f9570, 8413b0 -> 0x4c9230).
  The same inline pack (fld [esi+8]; _ftol2; movzx; fld [esi+4]; _ftol2; ...) exists in at least 17 more functions that do NOT use the three
  helpers: 0x47d840 0x491900 0x4a5a70 0x5205e0 0x541780 0x55b530 0x623930 0x69d080 0x70aa70 0x71d600 0x7235b0 0x756bb0 0x75fb40 0x796320 0x832930 0x84d900 0x8d7e20
  (+ 0x82cc40 pushes the three ftol results itself and calls 0x404e60). So hooking the 3 helpers covers only part of the sends.
- There is NO unpack helper. Unpack is inline `movsx r, word [..]; fild` in each RMC receiver (0x4f9570, 0x4c9230, 0x4e7680, 0x68b070, 0x6e5580,
  0x4d13f0, 0x4ba7d0, 0x4e2c70, 0x60c610, 0x771d90, 0x78a580, 0x795b40, 0x79ab20, 0x5076e0, 0x539cc0, 0x595ea0, 0x55cbd0, 0x4f7b00 ...) and in the
  dataset readers (word [obj+0x118/0x11a/0x11c], [+0x178..], [+0x358..0x35c]: 0x41f6b0 0x557db0 0x569eb0 0x5c9110 0x8efe90 0x5f21c0 0x600c80 0x63a9f0 0x4ca1a0 ...).
  "Subtract T before pack, add T after unpack" therefore means patching ~20 packers and ~30 unpackers, each classified by hand; a missed one
  = a body at the wrong place by 12288/16384 units, i.e. worse than the stopgap. Receivers also re-pack what they unpack (0x4f9570 -> 5a0ff0 at 4f964b),
  so a half-patched chain double-shifts.

### 0x5a0ff0 call sites (14) - classification
| call | in function | this | value | class |
|---|---|---|---|---|
| 454b01 | 454ad0 | +0x350 | arg | absolute position (actor/player teleport/set) |
| 4c9380 | 4c9230 | +0x350 | unpacked RMC args (movsx/fild) | absolute position (receiver of 8413b0) |
| 4f964b | 4f9570 | +0x350 | unpacked RMC args | absolute position (receiver of 404e60) |
| 4e7804 | 4e7680 | +0x110 | unpacked RMC args (+ extra int16 x angle) | absolute position, other dataset |
| 68b15a, 6e56df | 68b070, 6e5580 | +0x110/edi | unpacked RMC args | absolute position (RMC receivers) |
| 630... 6301e1 | 630010 | +0x350 | vec from 0x51f910 with angle in the same fn | position-like, GUESS |
| 81b267 | 81b210 | +0x350 | local vec | position-like, GUESS |
| 71bc65, 71bcb2 | 71ba00 | +0x110 | local vec | position-like, GUESS |
| 7a8fb5 | 7a8d10 | +0x110 | cached floats at +0x2ac | position-like, GUESS |
| 8f98e3 | 8f9810 | +0x350 | arg | position-like, GUESS |
| 4b483f | 4b46a0 | +0x170 | vec (0, const[0xb724cc], const[0xb7ee44]) | NOT a world position (constant offset), a shift would corrupt it |
| 86fdb8 | 86fbc0 | +0x350 | three constants (0xb7f594, 0xb1b944, 0xb32f0c) | sentinel/reset vector, NOT a map position |
So even inside 0x5a0ff0 there are non-position uses; a blanket subtract in the helper is wrong.

### Other answers
- Exactness: the pack is truncation toward zero of the float, no scale, so an integer T is exact for the integer part; error stays < 1 unit as stock
  (float32 near 44k has 1/256 resolution, sums stay exact for T = multiples of 4096). Not a blocker.
- Same code on host and client: GUESS yes (one kl2.exe, symmetric RMC stubs); not the problem.
- Bypass of the helpers: yes, see the 17 inline packers above, plus all receivers. Not yet examined one by one: full-float spawn RMC, projectiles,
  drops, loot (some of the 17 inline packers are probably those).
- Verdict: Plan B is feasible only as a full audit (about 50 sites, each proven absolute-vs-relative, receivers and senders paired per RMC) or
  as the map shift. Neither is a quick hook. Nothing implemented in klhook; [Int16Guard] OnlineSkip=DM11B stays.
- If someone does it: pair each packer with its receiver through the RMC stub (vtable index), patch sender+receiver of the same RMC together,
  and verify with a round-trip test in the offline harness before any live run.

## Built 2026-10-28: tools/kl_map_shift.py (map shift, DM11B in the F04 slot)

`shift(src_zip, dst_zip, T)`, default T = (-12288, 0, -16384). Output (outside the repo):
`<DM>\KL_PortTools\shift_1028\F04_Main_DM11S.zip`. Not installed, not played. Tests: `python tools/kl_map_shift_test.py` (9 s, ALL OK).

### What is translated
- Scene roots (not systems: `AllLevels/mainsceneincludes_multiplayer`, `CloneGroup_*`, `Heroes`): trans += T (zero-translation baked roots get trans = T)
  and prp ZGEOM[2] likewise. Children are parent-local, untouched. 337 of 478 roots move, 141 system roots kept.
- PF4 navmesh (`kl_pf4.translate`), 74 room gates in the .buf head (corners and centre).
- HVK: placements (m), MOPP offsets, list offsets, box grown to old+new union; `.hrd` positions. 2695 placements moved / 61 kept, 2488 static codes, 5 lists, 19 hrd.
  Raises on a REF or 510-chunk that mixes moved and kept entities.
- `.oct`: 59 room trees (origin += T); 4 trees hold system items (SLOT ids) re-quantised outward (1207 items, worst box growth 18.95 units), rebuilt via build_tree if check fails.
- `.rmi`/`.rmc`: tree origin and box centre += T; second point only when non-zero (.rmi 71 of 78, .rmc 0 of 24).
- `.sgp` (36 portals), `.sgd` (2 octrees).

### Test numbers
- (a) round trip by -T: worst root 0.00098, prp 0.00098, hvk 7.6e-6 m, nav 1.0 on split constants ~3e6 (relative tolerance 5e-7).
- (b) range check: whole map 2 -> 3 entities beyond +-32767; gameplay entities 0. Extent after: x -25704..16973, z -32725..10881.
  The 3 are scenery: `lights!Spot_Sky_DIRECT_#03/#04` (2 were already out before) and `InsideBound_01` under `F04_Outside_BuildingsBackground_01`
  (z -48541 after, was -32157). The test treats `lights!*` and anything under a `*Background*` name as non-gameplay (GUESS: never net-synced).
- (c) 21 zip members byte-identical (CRC), 10 changed, buf head only 2622 bytes changed (all in gates).
- (d) kl_pf4_translate_test OK; kl_sgp_sgd_translate_test OK on the source zip. Its default stock sweep fails on L07 (portal 5 off the plane),
  the same in the main checkout: pre-existing, not this change.

### Still GUESS
- Rest of the .buf head untouched: KEYS tracks (55,120..186,352), ZHavokShatter blocks (186,352..241,120), ZLNK, particle emitters, FDX, light/SND data.
  If any hold absolute positions they stay at the old place.
- HVK header box meaning (grown to the union to be safe); .rmi/.rmc second point rule; SecurityZones.
- 24 prp/gms place mismatches are preserved as they were, not reconciled.
- .ANM assumed local; prm bounds and SND untouched.
- Sky lights and InsideBound_01 stay out of int16 range.
