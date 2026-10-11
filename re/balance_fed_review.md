# Review of track X2 (Tough, CrewToFed, FedHeadShot / HeadShot) - adversarial, 2026-10-11 ~21:15

Reviewed: the working tree's `klhook/klbalance.c` (mtime 20:55:37, identical to `G:\kl_scratch\X2\src\klhook\klbalance.c`),
the `[Balance]` sample lines of `klhook/KLHook.ini`, `re/balance.md` section 11, the harness `G:\kl_scratch\X2\t`.
Everything OFFLINE; nothing was run in the game; no file of the worker was changed. My scratch: `G:\kl_scratch\X2rev`.

## Verdict: ACCEPT WITH FIXES

The exe reading holds wherever I re-read it, every damage number re-derives, the code does what the notes say, default
is off, both harnesses pass and both builds compile. One claim is stated as fact and is not proved (M1); two holes in
the player-health half were found with scenarios of my own (S1, S2). Nothing was found that scales a health twice.

## What was re-derived and holds

- **The three routines for a police human** (disassembled again):
  0x591b60 at 0x591bbe: police byte set -> attacker team Ally reads `[R+0x00]`, any other `[R+0x04]`; the seventh
  (0x591be0) is skipped. 0x8b8050 at 0x8b80a0: Ally attacker reads `[R+0x08]`, any other `[R+0x10]`. 0x7c1ba0 at
  0x7c1bf0: Ally victim reads `[R+0x0c]`, any other `[R+0x14]`. `klr_mir = {1,0,4,5,2,3}` puts the right key in each;
  `CrewToFed` at k == 2 (+0x08) and `FedToCrew` at k == 3 (+0x0c) are the right slots.
- **His settings** (log 20:19:12 / 20:19:57: Arcade level 1, Risk=1, Ramp=1, CopToCrew 0.05): fed -> heister 1.00,
  heister -> fed 0.50, police AI -> heister 0.05, heister -> police AI 1.50, fed 550 with 4 s + 4 s ('your health
  object ... a POLICEMAN ... 550.0 of 550.0; 4.0 s ... 4.0 s'). The fed's guns are M-77B + Zastava (re/fed_kit.md 4.1).
- **Every hits-to-kill figure** of the report, the ini comment and 11.1 / 11.4 (ceil(health / (gun x factor)), guns
  72 / 64 / 52 / 37 and 58 / 51 / 42 / 30): today 4 / 4 / 5 / 7 and 19 / 22 / 27 / 37; proposed 9 / 10 / 13 / 18, head
  3 / 4 / 5 / 6, against 10 / 11 / 14 / 19; with Tough 14 / 15 / 19 / 26 (head 5 / 5 / 7 / 9) against 15 / 17 / 20 / 28;
  CrewToFed 0.75 + Tough = 19 / 22 / 27 / 37; parity factor 0.369. All correct.
- **NPC health**: 0x8fbac0 (vtable pointer 0xbd0a04, ZSoldier@CPPScript slot 44) reads `ROW[+8]` at 0x8fbb5b, 0x74d960
  at 0x74d99c. Image scan: 0x831f00 has eleven callers, their uses of the result are +0xc, +0xc, +4, +0x18, +0x1c,
  **+8**, +0x20, +0, **+8**, +0x10, +0x14 - the two named are the only readers of +8. No instruction within 0x60 bytes
  of a load of `[0x168d7c0]` uses displacement 0x434 / 0x458 / 0x47c / 0x4a0. 0x831f00 in Arcade: 0x863a60 is true
  only for `[session+0x54]` 2 / 3 (jump table 0x863a78), 0x87c980 is `[session+0x5c] == 2`: both false -> `[tuning +
  0x594 + 4 * Difficulty]`. Regeneration 0x4195ff / 0x419602 = `x max / [H+0x18]`: the same seconds under Tough.
- **Head floats**: 0xcdeffc / 0xcdf000 are named four times in the image (stores 0x45d5a8 / 0x45d5b4 inside 0x45c490,
  reads 0x572fbb / 0x572f73); 0x572f60 has two callers (0x4db7ff, 0x61acb8); both turn a ZActor shooter's bone type
  2 / 3 into 1 first (0x61ac87, 0x4db7e7).
- **0x882470**: in Arcade it goes to 0x8824e7; police byte set and the soldier's team not 2 -> 'no target'; an Ally
  soldier falls through to the score, and at 0x8826fb a police player is scored by an Ally soldier without the
  traitor byte. The static claim holds.
- **Checks re-run**: `klx_test.exe` '36 checks, 0 failed, 131 log lines, 854 writes / PASS'; `klr_test.exe` '20 checks,
  0 failed ... PASS'. Compile from HEAD (now c9d654d: klhud.c was committed at 20:57, after the worker's build) + this
  klbalance.c: TEST 21e2ab1b67c6ceda87decf27be7a433344ccf16d, SHIP 589da556cbb91c5ea6ab49e5e844af09da82f2e1, no
  warning. The worker's two sha1s match the files in `G:\kl_scratch\X2\test` / `ship` but are of the older HEAD.
- **Scope**: of the task's files only klbalance.c, the `[Balance]` comment lines of KLHook.ini and re/balance.md are
  touched by this track (balance.md +200 / -0); klfedkit.c, klbot.c, klhook.c unchanged. The other modified files in
  the tree belong to other tracks (kldown.c R8, klmove.c + the BoardReach ini lines N4, HUD files). Every new key is
  off without its line; nothing is written on a stock level or outside Arcade (`act`); data writes only.
- **Twice-scaling, tried and not found** (my scenarios in `G:\kl_scratch\X2rev\t\klz_extra.inc`): hero dead -> fed
  body 825 -> next round the hero refilled by the game to 550 / 550 -> 825, not 1237.5; another rules object with the
  hook's 825 still in the object -> 825; the head floats rewritten by the game while a fed -> 3 again, 5 for the
  heister, 10 when the dial stops; the NPC rows are always `code's value x Tough`, never a product of what is found.

## MUST

1. **'The AI heisters DO shoot a police human' is a static reading, not a seen fact - and the note says 'only the
   crew can have done that'.** No log of any run holds a single hit on a fed. The only `Log=2` fed run,
   FD3_DM03_die, has a fed of **27.5** health alive for 145 s with five heisters in play and **0 'you lost' lines**
   (PT_DM03_die_f2 / _r2 ran with Log=1). His two deaths as a fed (20:22:40, 20:27:06) name no killer; police AI
   bullets still cost him (stray fire reads +0x10 = 0.50), and blasts and the point-blank rule exist. What the log
   does show and the note does not use: `shoulder: CHANGE ... in 0->17 dstate 0->2` at 20:22:33.7 = he was knocked
   down 6 s after the respawn, up at 20:22:39, dead at 20:22:40.9 - so something was hurting him, by whom is open.
   The task's answer '(a), not (b)' therefore rests on 0x882470 alone, and how a soldier RANKS him among the police
   AI is 'NOT READ' by the note's own words. Required: 11.0 point 2, 11.2 and the comment in klbalance.c (2 a8,
   'They DO shoot at him') worded as EXE reading + circumstantial; a live check BEFORE the ini lines are offered as
   the answer to 'they do nothing to me' - a fed round with `[Balance] Log=2` where the fed stands in sight of live
   heisters with no police AI near: PASS = 'you lost' lines of 21 - 29 (today's x 0.50) within seconds; none in 30 s
   = (b) holds after all and `[Fed] Hunted` is owed. T4 assumes 'a fed that is shot at' and so cannot decide it.

## SHOULD

1. **The hook goes blind when the game rewrites only the maximum** (new with this track: it is the first key that
   raises the CURRENT health). `klr_player_tick` returns at `cur > max * 1.01 + 1`. Scenario R1: armed 825 of 825,
   the game writes max 550 and leaves the health -> '825.0 of 550.0', 0 writes, no log line, for as long as he is
   over 556; after a hit to 500 the maximum goes back to 825. His log shows the game DOES write the maximum a second
   time in every level (two 'your health set' lines ~21 s apart, e.g. 20:52:25 / 20:52:46); whether it writes the
   health with it is not known. Harmless in effect, but silent. Fix: take `cur > max` with `max` = the game's known
   base as 'a new maximum of the game's' and write; add to T1: the second 'your health set: maximum 825.0' line must
   come as it does today.
2. **A dial that stops for one pass heals a hurt man.** Scenario R2: hurt 600 of 825 -> dial off: 550 of 550 -> on
   again: 825 of 825 (`wasfull` is true because the put-back clamped him). Needs `act` to drop in mid-round (the
   archive verdict or a failed read of the rules object); not seen in his logs, cheap to close (remember that the
   object was clamped by the hook, not full by the game).
3. **'Every ratio stays' has exceptions the owner will feel**; the report lists them only under 'not done'. The
   game's own knock-down comes at an ABSOLUTE health (run D1: 'YOU ARE DOWN ... health 80.0 of 401.5'; kldown's
   `DownHealth` / `MinHit` / `Burst` are absolute too): under Tough 1.5 it comes at 9.7 % of the maximum instead of
   14.5 %. Point-blank steps, the departure kill and every fixed-damage blast do not scale either. With R8 changing
   the down state now, the lead has to set `DownHealth` x Tough by hand or R8 has to read the maximum.
4. **T1's FAIL rule can mislead for one record**: the actor that is `[gamedata+0x4cf0]` takes `ROW[+0]`, not +8
   (0x8fbb29 / 0x6fd7c0). The logs so far show no such heister (all 252), but a single odd number in the proof line
   is that, not 'made before the write'. Say so in the line or in 11.7.
5. **The arming pass is ~200 ms after the archive opens, not ~40 ms**, in the later loads of his log (20:52:21.178
   archive -> .374 'not the stock one'; 20:57:19.422 -> .623), and the rules object exists BEFORE the archive is
   opened (.171). Still 1.6 - 2 s before the player's health object appears, so the assumption 'no actor yet' is not
   weakened, but the number in klbalance.c 2 a7 and 11.3 should be the larger one. The assumption itself (who calls
   slot 44, and whether a second round of one level re-makes the actors while the rows are written) stays open and
   is correctly left to T1 / T2.
6. **`HeadShot` (the heister side) was not asked for**; it is off and harmless, but it is a fourth new key to keep.
   Fine to keep; not to be proposed (the note does not).
7. **Harness gaps**: no case for R1 / R2 above, none for `Tough` under 1 (works: 275 of 275, rows 0.25 / 0.45), none
   for a Tough line with a fed under `FedMirror=0` (by reading: the fed's object is left alone, the NPC rows are still
   written - then the fed is the only one without Tough; one line at start should say so).
8. **The sha1s in 11.6 are of a HEAD that has moved**; the lead rebuilds anyway (mine above compile clean).

## Not faults

- Tough and track R8 do not double: Tough is only in the maximum, nothing of the down state is read or written.
- `CrewToFed` / `FedToCrew` with no pair key set (Risk=0) write exactly one slot each and leave the game's own swap
  (harness section 6; review M1 of the FedMirror round still holds). S3 of that review (one record per health
  object) holds under Tough (scenario R3).
- The proposed values are arithmetic, marked as never run; CrewToFed 1.0 leaves the point-blank step at ~5,800
  (dead in one step today too at 2,900) - said in the note.
