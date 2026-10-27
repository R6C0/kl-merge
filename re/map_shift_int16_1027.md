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
- PF4 navmesh (.gms +0x34, tools/kl_pf4.py): waypoints, polygon / edge vertices, kd-tree floats, area bounding boxes. NOT fully decoded
  (tree node "three floats", array 6 "edge vertex and 2-D normal" - a plane distance would need recomputing). Highest risk: bots path on it.
- .sgp (room sound graph) 135 x/z pairs, .sgd 1, .buf head 1942 pairs (KEYS tracks, room gates/lists, GUESS: some are positions), light
  records, SND/ZLNK emitter data: NOT identified one by one.
Rooms: .rmi/.rmc lookups use the point, so a missed box = "no room" = silent/lit wrongly, not a crash.

## Verdict
Feasible in principle (every part is a translation, exactness is free with T above), but NOT built: it needs a decoded PF4 and .buf/.sgp
translation (undecoded float meanings), cannot be validated offline, and a half-shifted map is worse than the stopgap. Staged: nothing.
Build order if done: (1) roots + gms/prp, (2) HVK, (3) oct/rmi/rmc, (4) sgp/.buf/PF4 after decoding, (5) verify with a new check: every
absolute float of the map minus T equals the original (round-trip), kl_int16_range_check reports 0, then ship as its own folder (e.g. DM11S) so
[Int16Guard] OnlineSkip=DM11B does not apply (no key change), and test: load, 'pos: player' near the spawn, bots walk, shoot/loot/grenade,
escape, glass/doors, ambience (rooms), and compare nav (bots reach loot) with the unshifted map.

## Cheaper alternative (GUESS, not checked in the exe)
A codec bias in the hook: subtract/add a constant (Bx, Bz) in the three int16 pack/unpack helpers (0x5a0ff0 player+actor positions, 0x404e60 /
0x8413b0 the RMC vec3 args). One symmetric patch on both peers covers grenades, drops, barrels, actors with no map change. Risk: if the
helpers are also used for non-position int16 (velocity, direction) they would be biased too - read the callers first.
