# Review of track O (the AI heisters against YOU): klgrudge.c, klbot.c, klbalance.c, re/bots_fight.md

Adversarial review, 2026-10-11. OFFLINE: kl2.exe build 0490 re-read with `debug\dasm.py`, the owner's `KLHook.log`
read, both hooks rebuilt and the harness re-run in `G:\kl_scratch\O_review`. Nothing ran in the game, no worker file
was changed, nothing committed.

## Verdict: ACCEPT WITH FIXES

The hook code is data-only, off by default, gated to Arcade + a non-stock level, and its exe reading holds wherever
I re-read it. It may be WIRED and run in scripted tests as it is. It is NOT ready for the owner's ini: job 1 as the
owner refined it (the sponge BY RANGE) was not done and not declared (M1), and `Grudge=1` has two consequences for his
game that must be settled first (M2, M3).

## What was re-checked and holds

| claim | evidence |
|---|---|
| a bot's 'is the player my enemy' test ORs four things | 0x8826b6 `mov bl,[eax+0x79]; shr bl,1`, 0x8826cc `call 0x6a1c40`, 0x8826fb / 0x882708 / 0x882715 / 0x88271d |
| the switch is `[rules+0x884+4*i] > max([R+0x18], 25.0)` | 0x6a1c40 whole: level byte `[[rules+0x5f8]+0x45]` clamped 1..11, slot 141 = 0x78d5c0 = `fld [ecx+eax*4+0x884]`, 0xd1b398 = 25.0. klb_read's level is the same byte, same clamp |
| the float = per cent of the victim's MAXIMUM health, attacker index hard-wired 0 | 0x4d1973..0x4d19d3: `max - x`, `/ max`, `* 100`, `- 100`; stores `[esi+edi*4+0x884]`, `[esi+eax*4+0xac4]` (eax = 12 * victim), time `[esi+eax*4+0x614] <- [esi+0x50]`; slot 414 of ZFFActor = 0x574060 = `[[ecx+0x5fc]+8]`; only caller 0x84777d |
| forgiving after 10.0 s, state 0x19 only; index time = attacker + 12 * victim | 0x771af0 whole (0xd1b390 = 10.0); slot 119 = 0x521d30 zeroes A, B, time |
| killing a crew member without flag 1 makes the killer the traitor; a tactic traitor has the record mask only | 0x6709dd..0x670a22 (slot 107, `test byte [score+victim*4+0x1d4],1`, slot 122, slot 129 = 0x8fb0d0); 0x488eb0 = `or byte [rec+0x79],2` + 0x4322f0, which touches `[rules+0x33c]` only |
| 'traitors allowed' acts as a switch | 0x4322f0: `or edi,ecx; jne` skips `inc [rules+0x338]` always. LOG: records 5, 2, 6, 3 'traitor flag SET' 12:35:52 .. 12:36:22 with Traitors=1; records 6, 1 at 12:43 |
| accuracy is read per shot from `[[soldier+0x6d8]+0x10]` | 0x719cd8..0x719ce9 |
| a police player's bullet on an Ally NPC reads +0x0c, a criminal's +0x14 | 0x7c1ba0 whole: `[player+0x2723]`, victim team `[[v+0x54]+4] == 2`; `klr_mir = {1,0,4,5,2,3}` puts YouToCrew in slot 3 under the mirror, FedToCrew replaces exactly that |
| Ramp leaves YouToCrew as given | `klr_kind[5] = 0`; the owner runs Ramp=1 (LOG 12:27:51) |
| compile | TEST and SHIP rebuilt from the worker's scratch sources (identical to the tree's three files + the three lines): both link, only klhud.c's C4101. sha1s differ from the worker's by build time only (889b569f / aecfb25f) |
| harness | `kly_test.exe`: '25 checks, 0 failed, 63 log lines, 107 writes' / PASS |
| rules file | diffs of klbot.c / klbalance.c hold track O's lines only; KLHook.ini append only; klhook.c, klescort.c, klfed.c untouched by this track; no game function called, no vtable, no .text |

## MUST

**M1. Job 1 as the owner refined it is missing, and the report does not say so.** The task file's first block
(owner: 'i probably meant more bullet spongey at longer ranges') asks for: whether the game scales a hit by distance,
both directions measured at 5 / 15 / 30 / 50 m under Risk=2, a `YouToCrewFar / FarAt / NearAt` key, and a flat
`YouToCrew` 'only as the fall-back if a per-hit distance cannot be had by data - then say so plainly'. Delivered: a
flat `YouToCrew=0.4`, every number 'at 10 m', no word on range in the report, in re/bots_fight.md 8 or in the code.
The input was at hand: re/balance.md 1 a (0x46ef60(weapon, distance): four damages over four ranges, x the Arcade
range-band fields 39..42) and `kl_map_ai.bullet()`. Until it is done the proposal 0.4 answers a question the owner
corrected. Fix: the table (player's Zastava and the bots' gun at four distances, hits to kill both ways), then either
the per-hit key or the plain statement that it cannot be had by data, and values from that table.

**M2. `Grudge=1` beside the owner's `Escort=1` is not handled.** The task: 'the escort must be handled (an escort you
shoot: release it)'. klgrudge.c only offers `kly_angry()`; nothing calls it. The owner's ini has `[Bots] Escort=1`:
an escort that SNAPS is ordered back to 3 m beside him by klescort.c every re-point and shoots him from there. The
three klescort.c lines of re/bots_fight.md 4.4 must go in with the wiring (the worker could not: another track's
file) - Grudge is not for the owner's ini before that.

**M3. Shooting back at a bot the hook made hostile makes the owner THE TRAITOR - the proposal must not reach his ini
before L5 / L9 are read.** 0x6709f4 tests flag 1 of the VICTIM and slot 122 (0x833f70) needs the victim to hold a
card against the killer; a bot never gets one (0x4d17f0 tallies ZFFPlayer attackers only). So with the proposed
`GrudgeMix=40,30,30` one stray bullet makes 30 % of the crew try to kill him for the rest of the round, and killing
that bot in self-defence flips all seven (flag 1 + `[player+0x2726]`). The doc calls it 'the clean end'; the owner
asked for bots that answer 'before i turn traitor'. Either the for-good bots get the same treatment as BackstabMark
offers (a key, off by default), or the owner is told in plain words; and the same question for the tactic's own
traitor (2.4, READ NOT SEEN) is still open: LOG shows record 3 dead 2.8 s after its flag, not who killed it nor what
the owner's flags did (the vehicle was in state 5 'without you', so it was not the left-behind rule).

## SHOULD

**S1. A heist-stage sum going down is treated as a full new round.** klbot.c itself calls that sign 'only a GUESS'
(B5) and resets only the backstab pick on it; klgrudge.c undoes everything and redraws. Review harness
(`G:\kl_scratch\O_review\t\rev_test.c`): a SNAPS bot hostile for good, one record released mid-round -> 'F3=0
hostile=0 good=0', a new temper drawn. Keep tempers / tallies / for-good on that sign; reset them only on a new
rules object or state -> 0x19.

**S2. 0x6a1c40 has a second caller the notes do not name: 0x570a1b (in 0x5706a0).** It builds a list of friendly
players for a soldier and leaves a player out when the bot has mask 2 OR the float is over the limit. It supports
the assumption 'held hostile = like a mask-2 traitor' (same OR in both places) - but 're/bots_fight.md 8: nothing but
0x6a1c40, 0x4d17f0, 0x771af0 reads A' was not checked against indirect calls of slot 141 (0x78d5c0, no direct
caller). Say both.

**S3. `BackstabMark=1` changes the payout.** 0x796576..0x79657c: an escaped record (0x40) WITH flag 1 keeps its own
money, without it its money goes into the pool that is split. A marked traitor bot that escapes is therefore out of
the pool and the split. Not 'harmless elsewhere'; write it into 3.4 and into L5. (kly_mark also keeps the bit on dead
/ aboard / escaped bots until the mask is cleared - that is what makes this reach the score page.)

**S4. The tally's own gates were not read.** 0x4d17f0 returns before the sum for: slot 123 (0x600470)(victim, 0)
false; either side's flags 0x1000 with / without 0x80 (four pair tests, 0x4d1875..0x4d1917); attacker flag 0x800
with `A[victim][0] != 0`; attacker flag 8 with victim flag 0x80. In those states Grudge sees no hit at all. Read
what 0x1000 / 0x80 / 8 are (heist stage? team?) or list them as NOT READ.

**S5. A put-back of the maximum prints a false 'ONE STEP' line.** klbot.c's Log=2 health log says 'lost > 100 in
one tick - ONE STEP' from `[hobj+4]` alone; CrewHealth 1.5 going back (round start, mask cleared, stock level)
lowers 378 -> 252 = 'lost 126.0 ... - ONE STEP' per living bot. That line is the lead's evidence for the
point-blank / left-behind questions. Say it in L2, or have klb_health_tick skip a step in which the maximum changed.

**S6. Attacker 0 is assumed, not tested.** kly_grudge writes row 0 whatever `s->human` is; the exe wires 0 too
(`push 0` throughout 0x4d17f0), so this holds while record 0 is the human (every log so far). One `s->human == 0`
test in `live` costs nothing.

**S7. klbot.c details.** TraitorsMax counts dead and escaped traitors too (the flag stays until the round start):
it is a cap per ROUND, not 'at once' as the ini line says. BackstabWait restarts whenever b's own conditions lapse
for one pass (`cand_since = 0`), so the wait can exceed it. BackstabBehind uses the direction of TRAVEL (the comment
says so): a player backing away or strafing is judged wrongly - mark it a guess in the ini line too.

**S8. BackstabAim writes into the ZSoldierRout's block.** re/map_ai.md 1: D lives at rout+0x34 and the soldier only
points at it; 'the actor's own' is true only as long as one rout makes one soldier. Keep the write, but say whose
memory it is, and refuse when two crew records show the same block.

**S9. The harness is thin where the logic is new.** Not covered: SNAPS, TAKES IT, GrudgeForget, a dead human, state
leaving 0x19, an unreadable limit. The check 'round restart handled' accepts both outcomes (`== 0 || == lim`). My
extra run shows SNAPS and the dead-human hand-over behave as written; the klbot.c / klbalance.c changes have no
harness at all (compile only, as reported).

**S10. Small.** re/bots_fight.md 2.2 names '-1.0 at 0xb87940' - not used in 0x4d1973..0x4d19aa (the minus comes
from `fsubp`). CrewHealth sits in `[Bots]`, not `[Balance]` as the task asked (reported; fine). L2 should also read
the bots line in round 2 AFTER the respawn ('378.0 of 378.0', not '252.0 of 378.0'): whether the game refills health
from the object's maximum at a round start was not read. The sample lines at the end of KLHook.ini stand under
`[Net]`: uncommented in place they do nothing (the text says to copy them; fine).

## For the lead

- Wire: the three lines as given, PLUS the klescort.c lines of 4.4 (M2).
- Scripted order: L0, L2 (two rounds), L3, L6, then L5 and L9 before anything of Grudge / BackstabMark is offered to
  the owner; L1 / L7 / L8 need the `fireat` patch (not reviewed line by line: it is not applied).
- Owner's ini today, without M1: `TraitorsMax=2`, `BackstabHealth`, `BackstabAim`, `BackstabNear / Behind / Wait`
  are safe to try after L3 / L4 / L6; `YouToCrew` waits for the range table; `Grudge` waits for M2 and M3.
