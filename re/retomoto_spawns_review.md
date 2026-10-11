# Review of track X1 (Retomoto spawns), 2026-10-11 evening

Reviewer: adversarial, offline. Nothing changed in the worker's files. Build read: `<work>\build\x_spawn\retomoto`
(zip sha1 307b2716..., matches the report).

## VERDICT: ACCEPT WITH FIXES (one MUST before the build goes on the owner's tab)

The mechanism is right and the build is clean. But the fed's tower places now sit in a hall that still has seven
sleeping men in it, so the owner's complaint 1 ('they just plop out') is only half fixed for the case he reported.

## Re-run by me

- `py_compile` of the four tools: ok.
- `kl_map_ai spawndiff z_fedpts\retomoto_lanes -> x_spawn\retomoto`: "only what the steps mean to change differs"
  (26,650 records equal apart from the moved groups and the three points).
- My own member-by-member zip compare against `z_fedpts\retomoto_lanes`: same member set; only `.prp` (same length,
  372 bytes in 57 spans = 22 bools + 29 places + 3 points) and `.gms` (it is scrambled: only dwords 0..1 are plain, so
  the 17-byte length change cannot be read raw; the parsed records are what spawndiff compares, and it is the
  same kind of change `fedpoints apply` already made on the reference, 618,209 -> 618,335). `KLJoin.ini`, `KLTalk.ini`,
  `KLGuns.ini`, `KLWardrobe.ini` are byte-equal to the lanes' build. So gates, lanes, joins and talk are untouched.
- `kl_fa_fedpoints check`: PASS, 7 good. `kl_fa_bots_rt check`: PASS (0 FAIL, 12 NOTE). `kl_fa_bots_dyn check`: PASS.
  `kl_impact`: problems 0. `kl_map_ai spawns`: same totals as the report. `spawnplan` on the output plans nothing.
- kl2.exe: vtable `0xbcce3c` slot 4 = `0x8b2120` (inverts the byte at +0x58, `sete`), slot 16 = `0x787a10`
  (`if [+0x58] -> 0x8d2e20; [+0x58]=0`). The reading of section 1 is correct.
- No man of any enemy squad carries the .gms hidden flag 0x400, so field 3 = 1 really leaves them in the world
  (checked for the whole subtree of every squad).
- Files touched: only the four allowed tools plus `re/retomoto_spawns.md`; klhook, `kl_fa_bots_rt/dyn/bank` untouched.
  New options are off by default except where the task asks (`LOW` 3 only matters for a two-halves map).
- Street clumps after: I count 2 pairs under 1.5 m (both of the left-asleep squads), 3 under 2.2 m; before 12 pairs
  by my count in the street (the report says 15 incl. the campaign's). Direction confirmed.

## MUST

**M1. The fed's three tower places are inside the hall of four sleeping squads (7 men): he will see them plop out.**
`Atrium_1st_InfrontElevator_Squad_01`, `Atrium_1st_PillarCover_Squad_01`, `Atrium_1st_CoverMiddle_Squad_01` and `_02`
stand at y 19602..19603 in the same hall (x 2256..2652). Men positions from the build against the new points:
`CoverMiddle_01` (2256, 19603, -902) is **3.6 m from Dead_07** (2490, -630) and 6.8 m / 6.8 m from Dead_05; `CoverMiddle_01`
(2276, -1196) 6.0 m; `InfrontElevator` (2652, 695) 8.9 m from Dead_06; `CoverMiddle_02` 8.9 m. All still field 3 = 0
(audit: "out of sight", woken by `Trigger_2ndFloorStairEnd`). The report's own argument for the hall squads ("with the
guards asleep he stood in an empty hall and they appeared round him ... one box earlier would only move that moment",
3.2) applies to these seven just as well, and the second claim ("the audit finds no other squad that appears in sight")
is a property of the audit, not of the hall: it measures sight from the squad's WAKING BOX (45 m away), never from
where a fed now stands. The fed comes back before the crew reaches that floor (that is the whole situation of the
owner's check 1), so he is in the hall when `Trigger_2ndFloorStairEnd` fires.
Fix: make `HALL_ACTIVE` cover every squad whose men stand within e.g. 15 m (on the floor, in sight) of a fed place
(here the four Atrium_1st squads), or add the check "men of a sleeping squad within N m of an AFTER_DEATH point" to
`kl_fa_fedpoints check` and to `kl_map_ai spawns` (a row per fed point), and re-run the audit with the fed points as
the 'waker positions' as well as the boxes. Cost is 7 more men awake on the first floor, the floor gate 035 / 036 crew
are headed for (heisters then meet them by sight, as the gate design expects them dead anyway).
Evidence: `scratchpad rv2.py` output, lines "man ...Atrium_1st..." (also reproducible by the diff of enemy men places
against `fedpoints.json`).

## SHOULD

**S1. The picture the owner complained about is most likely the cause the worker did NOT fix.** Looking at
`0233_11534s.jpg`: a three-to-four man clump and a pair standing among the heisters' name tags in the carriageway, i.e.
men that are already fighting/at a rout. A fed only returns on the street after the crew left the lobby lift
(switch by `TriggerBox_1_LeaveElevator`), by which time wave 1 (`tbExitLoot`) is about to / has fired; posts only help
while a squad has not had its first goal. The report says so (section 0 b, 3.3 "not changed") but then lists S4 as
"three men at the SWAT truck" as if that resolved check 2. Say plainly to the owner that the Defend-with-one-place
bunching (`10_Defend`, `40_RunToEscape`; two such points 11 and 18 m from his 20:26 stand) remains, and give the
`kl_fa_street` change (one Pos per man, new entities, so a chain step before `kl_fa_fedpoints`) its own track.

**S2. Two squads still plop 'in sight' at 9 m and 17 m.** `Squad_SWAT_From_Behind_South` (3 men, `tbExitLoot`: 9 m in
sight) and `Squad_RoadBlock_South` (3 men, 17 m) are PLOP in the final audit; the justification is that they come
"from behind". That is exactly the 'plop out' the owner means; being behind the crew does not stop it being seen by
the crew (or a fed). Either leave them asleep but start them further out (their start places are 'from behind', the
ground is south of the forecourt), or admit it in the live checks: S3 should name them as the expected remaining plops.

**S3. A fed 3 m from the machine gunner and 2.8 .. 3.2 m from guard posts, and 11 m from the join box.** Two ASSUMED
facts carry this: a police human is not the guards' enemy (never seen; the fed's own hit tests are the owner's
earlier checks) and a fed will not walk 11 m north into the join box (which jumps the whole crew, report section 3.1).
The first can be tested in S1 by the lead; the second is a real design hole created by this track's own placement
(it was 23 / 129 m before). Recommend the lead a `[Join]` guard key (police + heister in the tower) or, offline, a
second look at moving the three places 5 m further south (they are 6.2 .. 10 m from the hold, far from the box
only by the 11 m the report gives).

**S4. `kl_fa_author.wire` / `kl_fa_street.relay` do not write the new tables.** A Retomoto rebuilt from scratch
silently loses the whole fix (the report says it; the repo has no check that fails). Add a line to the `kl_fa_fedpoints
check` / `kl_fa_street report` that NOTEs "N squads of HALL_ACTIVE / ACTIVE are field 3 = 0 in this build", so the
lead's next rebuild shows it.

**S5. The live risk is unmeasured.** 43 men awake from the load against 3 before (S5 / S6 of the live list are
right): in particular whether men awake with no goal stay at a post or wander / 'hunt' toward gunfire in the tower
half 200 m above, and whether the shots at the boardroom / the countdown wake the street. Run S0 with `[Bots] Log=2`
and read the street deaths in the first 90 s; if any street man leaves his post or dies before the crew arrives, switch
to `--asleep=wave1,wave2` (the option exists).

## NOTE (no action)

- The audit's sight model is collision samples only (cars, crates, glass not covered) - the worker says so; it called
  the machine gunner "out of sight" while the owner sees him. The audit should therefore be read as a lower bound.
- `spawns` verdict for `Squad_MG-Guy` etc. is now "active" so the table is not wrong, but its "first named by ... 25 / none"
  line still says box `PreLastTrigger`; harmless.
- `kl_map_ai spawnfix` run on its own output plans 0 squads / 0 moves: idempotent as claimed.
- Guesses are marked as guesses in code and in the document (PLOP_NEAR, LIFT_NEAR, POST_*); I found no unmarked one.
