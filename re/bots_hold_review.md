# Review of track N3 - FollowOutHold killed the human aboard; `FollowOutShield` (adversarial, 2026-10-11)

**OFFLINE. kl2.exe re-read, the three live logs re-read line by line, the diff of `klescort.c` / `klmove.c` read, the
compile re-run. Nothing was run in the game, nothing committed, none of the worker's files changed.**
Scratch readers: session scratchpad `n3rev\scan.py`, `tree.py`, `ctrl.py`; compile copy `G:\kl_scratch\n3rev`.

## Verdict: ACCEPT WITH FIXES

The cause holds against the exe and is not contradicted by any log line; the fix guards the routine that kills.
It is still a fix for a cause nobody has SEEN (no log has the vehicle's health): N3a / N3b decide it. One MUST
(a diagnostic the live check relies on can never print), the rest SHOULD.

## 1. The cause, re-read

| claim | checked at | result |
|---|---|---|
| rules slot 94 = 0x6a1100: grade 2 in states 1..5 -> slot 194 (6), then every used record with status 4 is killed (slot 16 for an AI member, slot 11 for a human) | 0x6a112c..0x6a124d, table 0x6a12b0 | CONFIRMED |
| state 6 is set by nothing else | all 73 uses of `[vt+0x308]`; the state machine slot 195 = 0x55ec70 (1 -> 3, 2 -> 4, 3 / 4 -> 5, 5 -> 7 / 8, 6 -> 7, 7 -> 0) never makes 6; the only `push 6` are slot 94 and the multiplayer twin 0x839380 | CONFIRMED |
| slot 94 is called with 2 only from the controller's `EscVehicleState` message (0x6d7d64 -> 0x594b10) | **NOT COMPLETE, see below** | |
| `ProjectileHit` / `DamageInfo` do nothing with `[+0x21]` set | 0x6c4740, 0x87f36e; both callers of 0x5aebb0 (0x6c4870, 0x87f387) are behind the test | CONFIRMED |
| `Invulnerable` / `Vulnerable` write `[+0x21]` | 0x87f426 / 0x87f43b; ids 0x168d6e0 / 0x168d6ec from the registrars 0xafdba0 / 0xafdbc0 | CONFIRMED |
| the ten scripted hits never go under a tenth and are ten per round object index `[+0xec0]` | 0x6db7bb..0x6db827 (max of new and max x 0.1), 0x74b843..0x74b89c | CONFIRMED |
| the health walk is the HUD's | 0x793b7e..0x793c60 (one level of children, slot + 0x5e chain) | CONFIRMED; on the bank the level agrees: `OnlineEscAnimatedVehicle` sits on the group `EscapeVehicle_Animation_F07` and `F07_EscapeVan_01 [ZAnimatedVehicle]` is its sixth direct child (`z_cover3\M03`) |

**What the worker did not find (it strengthens the cause):** the hit routine itself calls the rules. 0x5aebb0, after
`health -= amount`: if `rules slot 95` (0x5822d0 = `[rules+0x1ec]`) is 3 and the health is at or under 0
(0x5aec7c..0x5aec89) -> rules slot 33 (0x4d8a30: `[rules+0x1e8]` = the attacker) and **rules slot 84 = 0x61e570, which
in states 1..5 calls slot 94 with 2** (0x61e5e7). So 'destroyed' needs no level wiring at all, and it explains the
jump 3 -> 6 with no 'heavily damaged' departure: grade 1 exists only as a level message, grade 2 comes straight from
the hit that takes the last health. Slot 84's only other caller is the vehicle's update at 0x8fa37f, behind the dword
`[0x168d620]` (no writer in .text: a debug switch). The damage override `[0x168d61c]` at 0x5aec30 has no writer either.
Section 11.2's 'which of the three carries which grade is the level's wiring: NOT read' is therefore not what the
death rests on.

## 2. The logs, second by second

Death against every anchor a fixed clock could run from (the `record 0 (you): dead` line is written in its own tick):

| from | N1 | N1b | difference |
|---|---|---|---|
| the call (stage 2 -> 3) | 15:27:43.73 -> 15:28:11.73 = 28.00 s | 15:37:29.09 -> :57.52 = 28.43 s | 0.43 |
| the wait's begin (timer 8.0 extrapolated) | 20.83 s | 21.26 s | 0.43 |
| `aboard` | 17.61 s | 18.03 s | 0.42 |
| the first hold write | 14.7 s | 15.17 s | 0.45 |
| the wait timer AT the death | 2.25 s (never under 2 after the third hold) | 1.73 s | 0.5 |

- No game clock gives 0.4 s of scatter from each of its possible starts, and the timer was not at 0 or at one value
  in the two runs: **'the held timer ran out' and 'a second clock' are refuted.** N1c: timer 8.0 -> 0.0, state 5,
  `status6`; no state 6.
- Both records with status 4 die in the tick (N1 records 0 + 5, N1b 0 + 1), nobody else, the next `van` line says
  state 6 with 9.8 s: exactly slot 94 (2). `[Bots] Van=0` in all three runs (klbot's own blow-up is out).
- The worker's 20.9 / 21.3 s are right to 0.1 s.
- **A log the report does not use: `U_M01.log` (Hot Coffee, 2026-10-10, idle human, no hold, no FollowOut):
  `van 2` -> `van 4 8.0s` 16:28:32.3 -> `van 6 9.9s` 16:28:33.7.** The van was destroyed 1.3 s into its SECOND
  visit of a stock-length round, nobody aboard. It is the only other state 6 in `<work>\build\klhook\live`. So (a) the
  mechanism is the game's own and is seen without any hold, and (b) **'stock exposes it 16.4 s, ours stood 31 and
  lasted 21' is not a rule**: either the health is not made new between visits ('Reset', 0x87f396, is a level
  message - not read who sends it) or one step takes all of it. 'Nothing is safe beyond stock's 8 s' should read
  'nothing is safe at all without the shield; stock only makes it rare'.

## 3. The diff

Read whole. Not found: a write that is not a data byte through `klh_data`; anything before the 'not stock' / Arcade /
game-thread gates (both holds call the guard after them; `kle_veh_pass` sits after line 1146); a key that acts by
default (`FollowOutShield=2` does nothing without `FollowOutHold` / `WaitForYouHold`); a file outside the task's list
(`klfed.c`'s diff is track L's); a string over its 200 bytes (longest 180). The shield's bookkeeping is outside
`kle_r` and is taken back at state 0 / 1 / 2 / 6 / 7 / 8, at a new round, at the round's end, on a stock level and
when the round cannot be read; only the 1 this file wrote, only on an object that still has vtable 0xbcc0b4. The hold
still cannot keep a round from ending (60 s a visit, as before). Compile re-run from `git archive HEAD klhook` + the
two files: `built G:\kl_scratch\n3rev\test\dinput8.dll (TEST)` e053d5df..., `built ...\ship\dinput8.dll (SHIP)`
31117cdc...; only warning `klhud.c(188)`. **The sha1s differ from the report's (79b6403e / 786b94bf): the build is
not byte-reproducible (or the files changed after it) - the lead must take the hash of the DLL he builds, not the
report's.**

### MUST

1. **The line `DESTROYED ... ALTHOUGH ITS 'Invulnerable' BYTE IS SET` can never be printed for our own shield.**
   `kle_veh_pass` first runs the release branch (`s->veh == 6` -> `kle_shield_off("the vehicle is destroyed")`:
   `kle_sh.obj = 0`, byte written 0) and only then reads the vehicle and tests `kle_sh.obj || v.inv` - both 0 by
   then. That line is the one piece of evidence that would say 'the cause is another path than a hit' (section 11.6's
   first ASSUMED), and N3b lists it as a FAIL line. Keep what the shield was before the release (a local taken at
   the top of the pass) and say it in the DESTROYED line; or log before releasing.

### SHOULD

2. **Fail-open when the health object is not found.** `kle_veh_read` -> 0 means 'a helicopter or a car' and the hold
   goes on UNSHIELDED - the form that killed. The game itself tells the two apart: `[rules+0x1ec] == 3` is its test
   for the key-framed van (0x5aec7c, 0x55ecf4). With kind 3 and no `ZAnimatedVehicle` found: no hold. Until then add
   to N3b's FAIL list: `has no ZAnimatedVehicle health object` / `nothing to shield` on any of the four van maps.
   (On the bank the walk is right, section 1; the other three van maps were not looked at; the class test is by the
   exact vtable where the game tests the class id with a mask - a derived class would be missed.)
3. **Write the direct path into `re/bots_follow_out.md` 11.2 and klescort.c 3 c2** (0x5aec7c -> slot 84 = 0x61e570
   -> slot 94 (2)), and take 'which DamageFX carries which grade' out of the chain of the death. It also settles
   11.2's open point in part: 3 -> 6 without grade 1 is what this path does whatever took the health.
4. **`U_M01.log` into 11.1** and the wording of 'largest safe hold' (section 2 above). Consequence for the design:
   the shield goes on at the first timer write, about 6 s into the wait; for those 6 s and for a vehicle that comes
   back damaged the risk is stock's. Say so; N3a should also be read at a SECOND visit (does `health H of M` start
   at 100 % again?).
5. `FollowOutShield=2` leaves the whole drive-out invulnerable although nothing holds the driver any more; the
   owner's line is 'it should be all the same kinda risk'. The report says it; the default is the owner's call, not
   the track's - put it to him as a choice (1 = stock's risk after the hold).
6. With the shield on the scripted hits still take the van to a tenth; with `=1`, or at the next visit, it then
   stands unshielded at that health. One log line at `shield: off` already says the health: make N3e / a second
   visit a stated check.
7. `kle_hold_guard`, case 'our object, byte 0 again': it logs `shield: off (another vehicle is held) ... left alone`
   before setting it again - a wrong reason in the log. `kle_veh_pass` already has the right line for it.
8. 11.4's per-map seconds are from straight distances and an assumed 3.5 m/s (marked); only the bank's 24.0 / 25.5 s
   are measured (re-read: `record 1 (an escort) aboard 24.0 s after the crew was called`). `FollowOutHold=25` is a
   bank value; a traitor boards with him under it (N1). Not re-derived here.
9. `[0x156b5f0]`: klbalance's start line already prints 'campaign difficulty option 1' - if that is the same dword,
   the Arcade van's maximum is known (the second of the four); one grep, not done by either of us.

## 4. Not established (still)

- That hits took the health: no log has it. The exe leaves, besides 0x5aebb0, only `FakeDamage` (no controller in the
  builds, the worker's count; not re-counted), the scripted hits (cannot) and the debug switch.
- Steady fire or one point-blank step; who sends 'Reset' to the vehicle and when.
- Everything of the fix in the game: NOT RUN.
