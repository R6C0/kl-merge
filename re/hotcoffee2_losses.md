# Hot Coffee II (DM01B, slot F03): why crew members are lost

Offline reading of the KLHook logs only (no game run, nothing installed). Written 2026-10-18.
Runs: L52, L54, L67, L69 (earlier), L70 (hook s + BoardReachFlat, ini PT_DM01B_flat.ini, hook out_e5_1018s),
L71 (VanCallNear=40, ini PT_DM01B_vancall.ini, hook out_e5_1018u). Round logs split per round live in the
scratchpad of session d20b026f (hl/L70.log etc.); the one-line summaries are in
research outputs L52.out ... L71.out. Units are cm; crew max health 378. Times are KLHook.log wall clock.
"t+N" is seconds after the botdown "a round runs" line. Killer is NOT logged: any killer named here is a GUESS
taken from the nearest living non-crew actor in the census.

## Per crew member (L70 and L71, the two best runs)

L70 (KLHook loaded 10:50:49; botdown 'a round runs' 10:52:00.885)
- rec 1: 'dead' line 10:55:41.730 (t+220), at (3966,23,24169) in the next census (10:55:42.4, so a body position). At 10:55:40.4 it stood at (4383,-15,23956) with 256 of 378 hp; the nearest guard then was slot 786 at 5.4 m (86 of 157.5 hp), and that guard was itself at 0 hp by 10:55:42.4, so it is no clearer a killer than anything else. Dead together with rec 5 (same log line).
- rec 5: 'dead' line 10:55:41.730 (same line), body (4364,-15,24084); 308 of 378 hp at 10:55:40.4 (4353,-15,24009). 256 and 308 hp lost in under 2 s with no down logged: bullets cannot do that (see Biggest lever). Grenade/explosion or other unscaled damage is a GUESS.
- rec 3: 'dead' line 10:56:19.465 (t+258), body (2707,14,26011). 296 of 378 hp at 10:56:18.4 (2863,-15,25994), so about 300 hp in 1 s. Nearest living guard 22 m away: killer not identified.
- rec 2: alive (378 hp), never boarded. Escort bot: record 2 re-pointed to the human (idle at (-390,0,4150)) 31 times (log count 'escort: record 2 re-pointed'; census 10:52-10:58 shows it oscillating at (-339,0,4449)); released only at 10:58:06.700 ("escort: record 2 released", stage 0); the van left at 10:58:59.450 ("near:" line: rec 2 64 m away).
- rec 7: alive (378 hp), did not board. Stage 2, stuck 6.4-6.9 m from its place (1893,0,30432), re-ordered three times, target dropped 10:58:54; van left with it 6 m away.
- rec 4 (traitor) and rec 6: reached the van, escaped on visit 1 (rec 4 318 hp, rec 6 258 hp).

L71 (KLHook loaded 13:37:14; 'a round runs' 13:38:23.709)
- rec 3: 'dead' line 13:41:13.121 (t+170), body (4948,77,24157) in the census 13:41:13.2; y 77 is airborne (knock-back or blast, a hint, not proof). 304 of 378 hp at 13:41:11.2 at (5254,-15,23937). Nearest guard slot 810 at 14 m (157.5 hp at 13:41:11, at 0 hp by 13:41:13.2).
- rec 4: 'dead' line 13:42:18.530 (t+235), body (3395,17,25799). 346 of 378 hp at 13:42:17.2 at (3015,-12,25950), with guard slot 794 3.2 m away at (2935,-15,26258), i.e. about 346 hp lost in 1.3 s. That guard was at 0 hp by 13:42:19.2.
- rec 2: alive (378 hp), not aboard; escort bot again held at (-364,0,4449) beside the idle human, 30 re-points, released 13:43:28.495 at stage 0; the van left at 13:44:21.248 with rec 2 52 m away ("near:" line); census 13:44:29 has it at (2669,-15,27953), 366 hp.
- recs 1, 5, 6, 7: aboard on visit 1 (called by VanCallNear=40).

Earlier runs, same map: L52 lost 6 of 7 (its log shows 6 'dead' lines, 08:00-08:04; the 0.05 is the Arcade level-2 row of its balance table, level 1 shows 0.01, so the 0.05 attribution is NOT confirmed); L69 (this log) has 2 crew deaths: rec 3 at 10:08:51.7 in the west detour (-2682,17,6064) and rec 7 at 10:10:21.7 at (4816,17,20175), a different place; L54 / L67 deaths at x 4660..5600, z 23400..26200 plus at the van (2488,3,30223).

## Cause table (by place)

| # | Place (x,z) | Loss | Cause | Evidence |
|---|---|---|---|---|
| 1 | Diner (3900..5400, 23900..24200) | L70 recs 1+5, L71 rec 3 (3 of 5 deaths) | Killing-ground bursts, two dead on one log line at t+220 (L70); guards 5 m away, one dead by 10:55:42 | L70 10:55:41.730, L71 13:41:13.121 |
| 2 | Between diner and donut (2700..3400, 25800..26000) | L70 rec 3, L71 rec 4 | Point-blank guards (3-5 m, rec 4) / unidentified killer (rec 3) | L70 10:56:19.465, L71 13:42:18.530 |
| 3 | West detour (-2682, 6064) | L69 rec 3 only (1 death; L69's other death, rec 7, is at (4816,20175)) | Not seen in L70/L71; cause unknown | L69 10:08:51.717 |
| 4 | Hold point beside the human (-364, 4449) | rec 2 not boarded, L70 and L71 | Escort bot (stage 0) is re-pointed to the idle scripted human every ~5 s and released only when the vehicle waits; with a moving human this may not arise (GUESS) | L70 10:58:06.700, L71 13:43:28.495 |
| 5 | Van street (1893,30432) | L70 rec 7 not boarded | Stuck 6.4-6.9 m from its place, target dropped before departure | L70 10:58:54, near: 10:58:59.450 |
| 6 | Van street, end of round | police deaths after the van | Not crew losses | L54 08:28:15 |

## Biggest lever

Rows 1+2 are all 5 crew deaths of the two best runs (L70 3, L71 2) and is the only cause that kills; rows 4-5 are test-harness
and timing effects that the VanCallNear=40 and escort key already tune.

The earlier draft of this note proposed [Balance] PointBlankToCrew 5 -> 1. That is REFUTED by the logs:
- A point-blank step on an AI heister costs 72 x 1.2 x scale x CopToCrew (klbalance.c a4). With the live CopToCrew 0.01
  (L70 line 43 'police->crew 0.01', live KLHook.ini) and PointBlankToCrew 5 that is about 4.3 hp; at 1 it is 0.9 hp.
  Even the game's 100 would be 86 hp. The four deaths cost 250..350 hp each in 1..2 s.
- The hook logs every such step ('balance: point-blank step: ... on an AI heister'): L70 has 11, all at 10:53:26-10:54:08;
  L71 has 5, all at 13:43:03-04. None is within 60 s of any of the four death moments (10:55:41.7, 10:56:19.5, 13:41:13.1, 13:42:18.5).
- No botdown line precedes these deaths: they were not downs that ran out (DownsMax cannot help either).
So the killing damage is not scaled by CopToCrew or the point-blank key; the killer is NOT identified (GUESS: explosive or
other damage; L71 rec 3 was airborne). No existing key is shown to act on it. The next step is evidence, not a dial: log
the health drops of crew records with the source near the diner (all 5 crew deaths of L70/L71 are at the diner or between it and the donut), before choosing a lever.
The key is read by the live build (klbalance.c klr_pb_key; the live ini sets it to 5), so setting it would work, but it
would not address these deaths.

## Test ini snippet (VanCallNear / BoardReachFlat only)

    [Bots]
    VanCallNear=40
    BoardReachFlat=1

Both keys are read by klhook/klmove.c (BoardReachFlat, VanCallNear fields). PointBlankToCrew / CopToCrew changes are
not expected to change the death count (see above); do not read a drop as proof. Compare crew dead on the DM01B round
against L70/L71 (3 and 2 dead). Pair with live zip ea8cbc82 (not re-checked).
No KLJoin.ini change is needed, so nothing is staged under C:\kl_build_1018\hc2_next.

Next (2026-10-18): 3f's opt-in [Balance] LogCrewHits=1 (2f17dc43, TEST hook out_3f_1018d 3f073ebb, re/crew_hits.md) logs each crew health drop
with the soldiers targeting the victim; queued as 3f run (j) on live DM01B. Read its 'NO TARGETER' / DIED lines at the diner first.
