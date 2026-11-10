# Van lane vs exit (call) box audit, 2026-11-10 (offline; nothing installed)

Question: does the key-framed escape van drive/park/leave through the box that CALLS it (`Gameplay!EscapeSetup!otrExitLevel`, OnlineExitLevelTrigger, field 2 = van group)?
A heister waiting in that box for the van is then run over (DD10 bench dd10call1109: seat at the box centre died ~4 s into the drive-in, a seat in the clear strip lived).
Footprint rule used by the fix tools: van half width 110 + 40 capsule = 150, half length 340 both ways, every frame of the main drive (keys 0..drive()), heading = rotation key.
Crash legs (keys after drive()) only play when the van is destroyed: reported, not swept.

| Map (slot) | Verdict | Fix staged |
|---|---|---|
| DD10 (F07) | KILL-LIKELY: lane z 1030 inside box z 650..1550; bench-proven | `tools/kl_dd10_exitsouth_1110.py`, C:/kl_build_1024/dd10exitsouth_1110: box z 650..900 (pushed ae6e1943). NOTE: its strip edge z 900 is 25 cm off the van's half width 110 but only -20 cm vs the 150 rule (lane edge 880): a heister at z 880..900 is inside the 40 cm capsule margin, not under the body. Not changed. |
| DM01B (F03) | KILL-LIKELY: final approach z 31907 along x through the box centre (4118, 31907); parks x 4452 (frames 202..272) inside the box; twin triggers share the exact box | `tools/kl_exitstrip_1110.py`, C:/kl_build_1024/exitstrip_1110/DM01B: z 32070..32350 (north strip) |
| DM06B (F02) | KILL-LIKELY: diagonal NW->SE lane through the box (centre line z -8063..-7777 inside it), parks ~1 s at (-2255, -8028) | exitstrip DM06B: x -3020..-2400, z -8380..-8170 (SW corner) |
| DM07 (F06) | KILL-LIKELY: lane z 10400 straight through the centre, arrives AND reverses out along it, parks x -2607 (frames 199..276) | exitstrip DM07: z 9950..10230 (south strip) |
| DM01 (F0?) | lower risk: exit trigger boxes are huge (CallExitVehicle_01 1204x880, _02 2098x1400 half); sweep overlaps are partial (no centre/stop hit flagged) | none (not in the kill-likely list; sweep numbers in the audit scratch only) |
| DM02, DM03 | lower risk: ExitTrigger_01 6000x4000 / 4000x1000 half, van sweeps ~160 m2 of a >1000 m2 box | none |
| DM03A, DM09 | van present, exit box large (DM03A 1500x1150 half, DM09 2700x2250 half); not flagged | none (not re-measured in this task) |
| DM05A, DM06, DM11B | heli / cop cars only, no van lane | none |
| DD01 | WATCH: van #9940 drive-in line passes 131 cm from the centre of otrExitLevel (6855, 26051; box half 4509x2371); #10134 177 cm, #10312 174 cm. Cause for concern is BotFill: it orders bots to the otrExitLevel CENTRE (klbotfill.c ~2668 / 2804) | nothing staged. Option (hook side): offset the BotFill target off the lane, e.g. 3 m toward the AllyEscapeBox side, for maps whose centre is within ~200 cm of a van line |
| DD02, DD03, DD06, DD08 | heli call boxes (huge), no van lane | none |
| DD04, DD05, DD07, DD09 | vans, exit boxes very large; centres not on the lane in the scratch dumps (not re-measured) | none |

## The three new stages (measured here from the LIVE zips' van keys, 500 drive frames each)

| Map | Live md5 zip / bots / base | Staged md5 zip / bots / base | Old box | New box |
|---|---|---|---|---|
| DM01B | 5eab5ecc / cadfb74e / 4db9726f | b5196d80 / be27cc91 / ad790474 | x 3668..4568, z 31457..32357 | x 3668..4568, z 32070..32350 |
| DM06B | 7cee043d / ec42c5e4 / 171f7443 | 4ce7ebc7 / 3d0f5a7f / c7ad563c | x -3024..-2124, z -8389..-7489 | x -3020..-2400, z -8380..-8170 |
| DM07 | f35e4133 / 1f514d51 / 08478b6e | 852bda37 / 9ac8b388 / 52c1ee4e | x -3387..-2487, z 9950..10850 | x -3387..-2487, z 9950..10230 |

* AllyEscapeBox itself overlaps the lane on all three (4..6 of 50 m2 inside the footprint; DM01B ally z 32002..32702 vs lane edge 32057), so its far side is clean but the box edge is not.
  The chosen strips are the free rectangles with the most AllyEscapeBox overlap (DM01B and DM07 20 m2, DM06B ~13 m2), so bots that wait in the ally box still stand in the call box.
* Twin triggers at the identical box (DM01B, DM07, DM06B): `POI_TheEscapeArea`, `..._OffenseOnlyRespawn` (ECPS_CP_OFFENSEONLY, never fires in FA), `..._FA_RespawnOnly`. They only
  send the escape-area marker (PointOfInterest) and kill nobody: left alone (GUESS: no need to move together).
* KLJoin.ini: DM01B and DM07 have only `[FedBody]` (no `[Join*]` Land/Target), DM06B has no KLJoin.ini. The `06_Exit` jump point is a place, not a KLJoin target: it sits on the lane
  (DM07 (-2937, 10400)); nothing in the hook reads it as a call position, so it was not moved.
* Proofs per map (tool `check`): only the .prp differs in the plain and the bots zip; 3..9 bytes differ inside one entity; `.prp` round trip; exactly the exit-box node differs;
  new box wholly outside the footprint on a 10 cm grid (old box: 2800..3000 cells inside); scratch install, 2nd install refused, undo byte-exact, `--dry` writes nothing.
* GUESSES: the .gms record keeps the old translation (loader reads the .prp); the strip floor is walkable (the ally-box centre lies inside the DM06B strip; DM01B/DM07 strips are
  next to the lane in the street); BotFill walks bots to the new centre (inside the strip, off the lane). Not benched.
