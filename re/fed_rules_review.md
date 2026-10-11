# Review of track S - 'a fed is only a fed' (klfedkit.c sections 5 - 7, re/fed_kit.md 10)

Adversarial review, 2026-10-11. Offline: kl2.exe 0490 re-read with `debug\dasm.py` / capstone scans, the diff of
`klhook/klfedkit.c` and `klhook/KLHook.ini` read line by line, the compile re-run, the worker's harness re-run.
**Nothing was run in the game; none of the worker's files was changed.** EXE = I disassembled it myself for this
review; NOTE = taken from an older note of the repo, not re-read.

## Verdict: ACCEPT WITH FIXES

No claim the fix rests on could be refuted in the exe, and no write was found that is not what the file says it is.
One thing the task asked to be proved is not in the worker's note at all (MUST 1: where the paid money ends up at
the session's end), and the pay step trusts more than it has to (SHOULD 1). The lead's run S0 / S1 comes before the
owner gets a hook built from this file, as the worker says himself: the three keys act at once under the
`[Fed] Enable=1 Player=1` his ini already has.

## What was checked and holds (EXE)

| claim | evidence |
|---|---|
| the classes | RTTI: 0xbd3514 `ZGameRulesHeist`, 0xbd2eb4 `ZGameRulesFragileAllianceSv`, 0xbd31e4 `..Cl`. Slot 129: Heist 0x8fb0d0, Sv 0x41d480, Cl 0x716640 (`ret 8`). Slot 169: Heist 0x58bbd0 (`xor eax,eax / ret 4`), Sv and Cl 0x4d8950. Slots 114 / 115 / 116 / 108 / 192 / 16 as the file says |
| multiplayer never marks a cop | 0x41d49a .. 0x41d4ae: slot 114(killer), `test al, 0xc / jne end`. Read in the SERVER class, the right one (the client's is a `ret`) |
| multiplayer pays a cop 50,000 for a loyal criminal | 0x4eb260 read whole: slot 108(killer) -> nothing; slot 112(killer) false = police -> 0x4eb411: victim not a criminal -> nothing; victim a traitor -> `+0x660` (his own killer, mode not 1) or `+0x65c`; else 0x4eb4c4 `[tuning+0x664]` (`+0x67c` only with `[0x168e59c] == 2` and the counter at rules+0x290). No money term. Default 0xc350 = 50,000 (0x52a9b1) |
| the '$N' of the announcement | 0x4d8950 kind 0 = `[tuning+0x664]`; Heist's slot 169 answers 0 for every kind |
| Arcade marks ANY human killer | 0x6709dd .. 0x670a22: slot 107(victim), flag 1 of the victim, slot 122(killer, victim), then slot 129(killer, victim). No test of the killer's side. Callers of 0x6706b0: 0x4857b9 and 0x70472f only |
| slot 129, whole | 0x8fb0d0 .. 0x8fb393 read: (a) announcer + flag 2 + 5.0 s (0xbcb330) at record +0x70; (b) 0x8fb19c `test byte [score+4*killer+0x1d4], 1 / jne end`; (c) slot 115(killer, 1), 0x70f770(player 0, 1) = byte +0x2726 and 0x4801a0; (d) killer 0: `add [score+0x24], [tuning+0xc10]` and the pop-up `[osd+0x10b8]` vtable +0x2c; (e) min of record byte +0x35. The 32 code bytes the hook compares are the ones at 0x8fb193 / 0x8fb1d3 |
| -25,000 | 0x530a00: `0xffff9e58` registered for `tuning+0xc10` |
| `[tuning+0xc10]` has no other reader | scan of every instruction with displacement 0xc10: only 0x8fb1d9 and 0x8fb20c take it from `[0x168d7c0]`; the other 30 are other classes' fields (a ring buffer +0xc04 .. +0xc10, player-side pointers) or stack |
| `[score+0x24]` is written by nothing else in a round | scan of every write through `[rules+0x5f8]`: +0x24 is written at 0x8fb1e5 (slot 129), zeroed at 0x8c7bf3 (the round reset 0x8c7a80), 0x4186f1 (the pause menu's Quit, 0x418660) and by 0x696410 (round end). 0x783010 only reads it into the sum `+0x30` |
| the round's end | 0x5dff40: slot 106(0) false -> 0x491ad0 (client 0's money / rewards / counters from the 13th element of each array, e.g. `+0x184 <- +0x1b4`), `dec byte [score+0x6c]`, 0x696410 (`+4 .. +0x30` = 0); then 0x70b920, `add [score+0x38], [score+0x30]`, state 0x1f. **The state is set inside the same call** (session vtable +0x68 = 0x74c080 -> 0x488e50 writes `+0x70` at once), so the hook's frame never sees the zeroed lines in state 0x19. The same holds for Quit (0x418660 -> slot 82 = 0x4f9f90 -> state 0x20 / 0x28 in the call) |
| 'Total score' does not change by the move | 0x807520: slot 56(0) + lines `+4 .. +0x2c` + `[score+0x38]` |
| the shop | 0x8eaa4a `sub [score+0x38], edi` |
| the HUD element | RTTI 0xbbdf6c `ZFAPlayerListDisplay`, slot 5 = 0x76db00, slot 2 = 0x5e60f0. Update: state 2 with its timer over -> state 1, `+0xf00` = 0.0; state 1: `+0xf00 += dt * 0.5` (0xb35790 = 0.5); at 1.0: `+0xf00` = -1.0 (0xb3e980) and state 0. Render 0x5e622c: state 0 or 1 draws the block (alpha `+0xf00` in state 1), 0x5e66a2 / 0x5e66bb: state 1 also draws the list at `1 - +0xf00`. No side test. The two values the hook writes are exactly the two the update writes at the end of the fade. `0x588680` = `[gamedata+0x15dc]`, `0x4ddae0(0)` = `[hold]` unless byte `[hold+4]` is 0xff |
| picture 0008 | looked at: the block in orange ('r6kxo', 'Total score: -20,000', 'Round 1') over the list's header and first row, the list still well visible - a cross-fade about half way. The name still reads 'r6kxo' there, 'Traitor' comes in 0009 |
| no yellow card stands in the way | slot 122 = 0x833f70 wants flag 0x400 on the VICTIM and his card byte; NOTE re/bots_fight.md 2.2: only a ZFFPlayer attacker ever gets a card, so no AI heister has one |
| compile | `git archive dd215a6 klhook` + the working tree's klfedkit.c (byte-identical to the worker's `G:\kl_scratch\S\src` copy; `klhook/` has no change between dd215a6 and today's HEAD 28953d8): TEST and SHIP build, the only warning is klhud.c(188) C4101. My DLLs' sha1s differ from the worker's (228feee9 / f52728c9: another path and build time); the worker's two sha1s are those of the files in `G:\kl_scratch\S\test` / `ship` |
| harness | `G:\kl_scratch\S\harness\klfedkit_test.exe`: `PASS: 89 checks, 0 failed` |
| files | S changed `klhook/klfedkit.c`, `re/fed_kit.md`, `klhook/KLHook.ini` (14 comment lines + 4 commented keys inside [Fed], nobody else's lines). The other modified files of the tree are other tracks'. No code byte, no import slot, no game call in sections 5 - 7 |
| gates | sections 5 - 7 sit behind section 0 (Arcade mode 4, state 0x19, rules vtable 0xbd3514, `klx_on` and verdict 2 = not stock, record 0 in play, a type-3 police ZFFPlayer). The every-frame step asks session / state / rules / player / police byte / status again. Nothing online, nothing on a stock level. `HudFade=2` (not default) has the stock gate too |
| reset | `[tuning+0xc10]` goes back within 50 ms of the first pass that finds no fed in play (second death, round end, pause, menu, a heister again), only if it is still the hook's number on the same object; flags and lines are zeroed by the game's own round reset 0x8c7a80 (it clears all twelve flag dwords, the rewards, the lines); `klfk_r` is dropped when a heister is in play |

## MUST

1. **Say where the paid money goes at the session's end - the task asked for exactly this and the note is silent.**
   `Pay` writes into `[score+0x38]`. EXE, 0x68b9e6 .. 0x68bc29 (the stats commit 0x68b930, run by the state-0x28
   handler when the last life is lost or on Quit): that dword is read three times - `stats+0x24 = max(..)`,
   `HeistTotalPoints[slot] = stats+0x4c+4*slot = max(..)` (0x68bad9 .. 0x68baef), and it is inserted into the
   LOCAL top-12 list of the slot, `profile+0x1408 + slot*0x30` (0x68bb6d .. 0x68bc29); NOTE re/leaderboard.md 2.1 /
   2.3: the same dword is the score of `UploadLeaderboardScore` (`KL2_Heist<slot>_TotalMoney`), and 0x6587c0 then
   saves the profile to disk when a profile is loaded (the owner's normal play).
   - Steam: `klsteam.c` blocks the upload and every SetStat / StoreStats for a level that is not stock, and the kit
     acts only with `klx_on` and verdict 2 - so the hook's money does NOT reach Steam while the guard is what it is.
     That is the guard's doing, not this file's; write the dependency down.
   - NOT covered by anything: the owner's local profile. A session on a tab map already files its total under the
     STOCK slot's local high-score list (re/leaderboard.md 4.3, 'proposal, not tried'; `klsteam.c` has no code for
     it - grep). `Pay` adds money the game itself would never have given to that number (up to 7 x 50,000 a fed
     round, and a fed round banks 0 in stock Arcade). Pre-existing channel, new content.
   What is asked: a paragraph in re/fed_kit.md 10.3 and one line in the ini comment; the lead decides whether `Pay`
   stays on by default before the profile rows are protected. No code change in klfedkit.c is required for it.

## SHOULD

1. **Tie the pay and the undo to the traitor flag seen in the same frame.** `klfk_rule_frame` treats ANY change of
   `[score+0x24]` against `line0` as slot 129's add: positive -> moved to the total and the rewards, negative ->
   written back. Slot 129 always sets flag 1 together with the add (0x8fb1aa .. 0x8fb1e5), so `if (!(flags & 1))`
   the right answer to a changed line is `line0 = line`, nothing else. As written the step is correct only because
   (a) nothing else writes the line in a round and (b) both zeroing paths leave state 0x19 inside the same call -
   both true by my reading, both things the hook should not have to rely on. The case it guards: a human who
   betrayed as a heister (line -25,000), died, came back (line0 = -25,000) - any zeroing seen in state 0x19 would
   be paid as +25,000 into the total and written back as -25,000.
2. **'A heister carrying flag 1 is paid 100,000 by the game itself' is true for the round's display only.** EXE
   0x67098e / 0x670968: that money goes to the rewards column `[score+0x184]` (and `+0x18` for the revenge case),
   and 0x491ad0 / 0x696410 take both back at the round's end for a human who did not escape. So a fed keeps 50,000
   for a loyal heister and NOTHING for a traitor, where multiplayer pays 100,000 / 200,000. Bots with flag 1 exist
   on the owner's game when klgrudge.c sets it (`[score+0x1d4+4*i] |= 1`). Either move that delta of the rewards
   column to the total the same way, or say plainly 'a traitor pays nothing that is kept'.
3. **Say that slot 129's first part now runs at EVERY kill.** With flag 1 cleared each frame, (a) and (e) are no
   longer once-a-round: flag 2 + the 5 s timer at record +0x70 is set again at each kill and the min into record
   byte +0x35 of the human is taken again with the money / time of that moment. The file lists +0x35 under 'stays as
   the game left it' but not that it is recomputed per kill; what +0x35 is was not read. (The announcer is silent
   for a police client except at `[rules+0xe84] == 0`, 0x67ef20 - confirmed.)
4. **The rewards write is not needed for the fix and rests on an assumption** ('the list's Round score column
   shows it'). It is harmless (0x491ad0 puts client 0's back; the reset zeroes it), but it is a third int written
   every kill for a display nobody has seen. Keep it only if S1's picture shows it; otherwise drop it.
5. **`klfk_pen_back` after a failed restore**: `have` is cleared before the write is tried; if that write fails the
   next fed's pass takes the hook's own +50,000 as 'the game's number' and it is never put back (a heister who then
   kills crew would be PAID 50,000). Unlikely (the same address was written a round before); cheap to close: keep
   `have` set when the write fails, or refuse a `was` that is greater than 0.
6. **A kill in the round's very last frame** (slot 192 leaving state 0x19 in the frame of the kill): flag 1 and the
   byte +0x2726 stay set, the score page can read 'Traitor', that kill is not paid. The game's round reset clears
   the flags; +0x2726 of the police object is not cleared by anything read here (the object is not used again,
   re/fed_respawn.md 2.3a). One line in 'what stays'.
7. **Live check to add (S2b)**: end a SESSION as a fed with pay (last life), with `[Steam]` log on: the lines
   `steam: BLOCKED UploadLeaderboardScore(.., <total with the 50,000s>)` and the blocked SetStats must be there -
   that is the proof of MUST 1's first half in the game. And S4 should name its log line: after the fed round,
   `fedkit: traitor: [tuning+0xc10] put back to -25000` BEFORE the heister's kill.
8. **`HudFade` is a guess about the owner's words, and marked as one - keep it so in the lead's note to him.** The
   code is right about the element; picture 0008 is a cross-fade. But the fade is stock design (a heister has it
   after every kill line), and half of what made 0008 ugly was the orange 'Traitor' block, which `NoTraitor`
   removes by itself. S3 with `HudFade=0 NoTraitor=1` beside S3 would show the owner both.

## Not in this track (for the lead)

- The owner's same message ends 'the belly flop shouldnt be when im already dead': nothing of it is in track S's
  task or files (kldown.c). Make sure a track holds it.
- The text 'You killed a criminal. $0' stays (slot 169 is code - confirmed); the worker's level-side idea (the
  `.LOC` string without `{Reward1}`) is the cheap cure and belongs to the map tools.
- The life is still lost in a fed round (0x5dfffd), as before.

## Not re-read by this review

0x48592a (the 5,000 of the kill line), 0x463b70 / 0x468430 (the announcement text), 0x73dcd3 / 0x7df24c (the
outro's finder's fee), 0x796410 (the payout), 0x68414e (a policeman cannot board), the other readers of byte
+0x2726 and of `[rules+0xe84]`, klfed.c's side of the respawn. Sections 1 - 4 of the file (track M) were reviewed
in re/fed_kit_review.md and are unchanged by this diff.
