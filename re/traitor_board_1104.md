# Why ZBoardEscapeVehicle wins for the online marked traitor (w4t14cjcd, 2026-11-04)

Report, then the adversarial verifier; the VERIFIER wins where they disagree. Cause: the hook's own OnlineBoard fallback boards the Arcade-marked traitor (puppeteer treats it as a normal Ally: klbf_brain_turned skips only TraitorTurn bots), it is then parked at the van ~109 s. Endorsed lever C (narrowed): skip marked traitors in klbf_brain_turned + klbr_turned_actor guards; leave the stage byte alone (Arcade keeps stage 3 in van windows).

## Report

**Q1. Who makes ZBoardEscapeVehicle's eval return > 0 online?**

The eval is the stock `0x4faf60`, run under the DLL's shadow rules block. The mod supplies every input that lets it pass.

- **Van state.** The DLL mirrors the real rules' van state into the shadow at `klbrain.c:710` (`+0x1dc/+0x1d8/+0x1e0/+0x1e4`, and `klbr_van = vb`). The stock gates need van 3 or 4. `kbr_board_state_ok` is `van == 3 || van == 4` (`klbrain_logic.h:130`).
- **Stage byte.** `klbrain.c:721` sets `[rec+0x78]` to `kbr_stage_byte(klbr_bstage, aboard, tally, klbr_van, klbr_bstage ? klbf_ob_called(e->actor) : 0)`. `kbr_stage_byte` (`klbrain_logic.h:233`) returns 3 when board_stage is on, the van is in state 3 or 4, and the bot has tally > 0 or is in or ordered to the exit box.
  - It does not exclude a marked traitor.
  - Bot 5 carried about $1.22M, so it qualified.
  - The stock gate that wants this is `cmp byte [eax+0x78],3 / jb 0x4fb11e` at `0x4fb064`. A single path then gives `fld1` at `0x4fb10d`.
- **Visibility.** `klbrain.c:393` is `vis = cls==0 ? (...) : cls==1 ? (klbr_boardreal && van_ok) : 1; return vis ? r : 0.0f;`. With the real-Board class on, the wrapper passes the stock value through whenever the van is in state 3 or 4.
- **Why Board wins.** In list A, Board is index 2 and CloseIn is index 5, so Board is tried first. Defend then keeps Board as the child until it returns, which explains the 531 of 798 samples.
- **Run log (BS45B_DM03/inst1/KLHook.log).** The bot was marked traitor at 10:28:17. The van went to state 3 at 29:19. The Board child started at 29:24.896. OnlineBoard "BOARDED" bot 5 at 29:22.274.

**Q2. Is "traitor runs to the van" Arcade-faithful?**

Partly.

- **Arcade (ARC45_DM03).** The traitor has slot 7 and stage byte 3, marked at 10:44:57.962. Board was the Defend winner at 45:00 (van 3) and again at 46:02. CloseIn and AttackFromCover win in between, because the van state is only 3 or 4 in short windows (3 at 44:57, 5 at 45:05, 7 at 45:13, 1 at 45:19, 3 at 45:27). So Arcade also lets a traitor with stage 3 board during a window, then falls back to attacking.
- **Online (bs45).** Board persists as the child for about 130 s after the van leaves (van 5 at 29:27, 7 at 29:35, 0 at 29:41). Log lines for bot 5 show no more run-task re-arms after about 29:28, and the "traitor target" lines show an empty known list and a failing fire test. That points to a bot parked at the van.
- **Cause: GUESS.** The Board RUN is parked in a wait. The bot was hook-boarded (a ghost with a live body, `[rec+0x10]` = 4), and the RUN's exit goes through the DLL's slot-45 stub `klbr_s45` (original `0x6840a0`) instead of Arcade's squad removal (`0x89c890`). Which yield it is parked on (`0x55b9f0`, `0x8997a0`, `0x630b50`, `0x6d9eb0`) is UNREAD.
- **Still UNREAD.** Where the Arcade traitor's own stage 3 comes from.
- **Not read.** BS45C_DD05 beyond its swap-in count line.

**Q3. Cheapest Arcade-faithful SessionSafe lever**

All three options are data or wrapper changes in code the DLL owns. Nothing is detoured in a hashed range.

- **A (preferred).** At `klbrain.c:721`, for a bot with `e->traitor` set that has not yet hit a human, force the stage byte below 3 (use 2 if tally > 0, else 1). The stock eval then fails the `cmp [eax+0x78],3` gate at `0x4fb064` and returns 0, so Defend moves on to CloseIn, as Arcade does outside the van windows.
  - Release the override on the first marked hit on a human.
  - Release it by a time cap of about 60 to 90 s.
  - Release it in the last van window and at round end.
  - Risk: stage 2 might re-enable Loot, so check how the Loot eval treats stage 2 versus 1.
- **B.** At `klbrain.c:393`, return 0.0 for cls==1 under the same gates. It is simpler, but it hides the eval value from your own logging and does not fix the stage byte the RUN reads.
- **C.** Keep a marked traitor out of the OnlineBoard and puppeteer van and box orders, so it is never hook-boarded.
  - This removes the ghost state that likely causes the 130 s park.
  - Risk: the traitor never banks or escapes with its loot unless released.

Common risk: a stuck override strands the traitor, so the release paths above must exist.

**Q4. Read-only check before changing anything**

Add a per-second log line for the marked bot, with no behaviour change. Fields: `[rec+0x78]`, `[rec+0x10]`, the Board eval value, `[goal+0x14]`, the run-task state, the ledger aboard flag (`klbf_ob_called`), and the distance to the nearest human.

1. Compare the line against a traitor that was never hook-boarded.
2. Run lever A in dry-run mode, logging "would force stage to N" next to the real stage byte.
3. Confirm the dry-run firing coincides with the Board wins (531 of 798). If the traitor's `[rec+0x78]` is already below 3 when Board still wins, the stage byte is not the gate and the cause is elsewhere.
4. Read where the Board RUN yields after 29:41 (`0x55b9f0` and the waits listed above).

## Verifier

**Verdict:** Q1 is confirmed in mechanism but misses the real driver. Q2 is partly confirmed and one explanation in it is refuted. Q3 lever A is not Arcade-faithful and does not address the cause. I endorse a variant of C. Q4 needs one added field.

### Q1: who makes the Board eval return > 0
- **CONFIRMED, line numbers exact.** Shadow van mirror at klbrain.c:710. The visibility rule is at :393, with `vis = cls==1 ? (klbr_boardreal && van_ok)`. The stage byte is set at :721 via `kbr_stage_byte` (klbrain_logic.h:233). That function returns 3 for a bot with `aboard`, or with tally > 0 / ordered to the box while the van is in state 3 or 4. Nothing excludes a marked traitor.
- **CONFIRMED by disassembly.** `0x4fb064` is `cmp byte [eax+0x78],3 / jb 0x4fb11e`, and `0x4fb11e` is `fldz`. The `fld1` at `0x4fb10d` is reached only after `0x5aeb00` returns true, and a `jg` on `[ebp-0xa8] > 1` (a path of more than one node) passes, which matches the analyst's "single path to fld1". The report omits those two extra gates.
- **Correction.** The jump table at `0x4fb128` sends van states 1 and 2 to `0x4fafe0` (holder test via `0x7bb2a0`). Only states 3 and 4 go straight to the stage test. The wrapper at :393 hides states 1 and 2.
- **Marking.** Bot 5 is rec 6, actor 4ec37db0. The log says "Traitor RUN marked record 6" at 10:28:17.316, with stage byte 2 at that moment.
- **REFUTED / reframed: why the traitor's Board eval was nonzero.**
  - At 29:22.274 the traitor was boarded by the hook's fallback path, not by the real Board tactic.
  - The BoardStage round-end line reads "6 boarded by the real Board tactic, 1 by the fallback".
  - The BoardLog gate lines for 4ec37db0 show `live 0 has_bnz 0` up to that point.
  - Its first Board-winner sample comes after the hook boarding (29:24.896).
  - Every other rec shows `s45 age` equal to its `bnzAt age`. Rec 6 shows `s45 age -1` for the whole run, so it never called slot 45.
  - So the Board winner is a consequence of the hook boarding the marked bot, not of the stage byte alone.
  - Cause chain: the puppeteer treats the Arcade-marked traitor as a normal Ally. It logged "exit walk at Sprint" at 28:25.269. `klbf_brain_turned` (klbotfill.c:1889, used at :2093) skips only TraitorTurn bots, whose team becomes Enemy. Arcade-marked bots stay on team Ally, so they are not skipped.

### Q2: is "traitor runs to the van" Arcade-faithful?
- **Arcade facts CONFIRMED.**
  - Slot 7 had stage byte 3 at the mark, 10:44:57.962 (stage term 3, bot 3, player 3, sum 9 against limit 7).
  - Board winner samples: 45:00, 45:12 (van state 5), and 46:02.
  - Van timeline: 3 at 44:57, 5 at 45:05, 7 at 45:13, 1 at 45:19, 3 at 45:27.
  - The Arcade Board child lasts about 13 s (52 samples) and ends once the van leaves. Online it lasts about 109 s through van states 5, 7, 0, 2 and 4.
  - A stage-3 traitor is the natural Arcade case, because the Traitor score needs stage term 3 at level 1. Forcing stage below 3 is therefore not Arcade-faithful. The Arcade traitor is also a stage-3 bot in the van windows.
- **CONFIRMED: the traitor is parked at the van.**
  - Rec 6 is 4.7 m from the board node at 29:22 and 2.4 m at 31:22.
  - The last `closein arm` was 28:49. The last `rearm` was 29:24.871.
  - The report said about 29:28, which is slightly off.
- **UNVERIFIED / contradiction in "Defend keeps Board as child".**
  - `re/closein_run_1104.md` line 144 says eval stops being called while Defend sits in the child via `0x55b9f0`. The Defend loop at `0x85f8f0` takes the first tactic with eval > 0, stores it in `[goal+0x14]`, runs it, and clears `[goal+0x14]` only when the child ends.
  - Yet the marked bot's ZCloseIn eval counter rose from 128 at 29:30 to 567 at round end, about 4 per second, while 436 samples showed Board as `[goal+0x14]`.
  - With van = 0 the wrapper returns 0.0 for Board, so a list walk cannot select it.
  - Either `[goal+0x14]` is stale, or the Board child is not a persistent yield and Defend re-walks the list.
  - The 531 count is a sampled field. It is not proof that Board is the active child.
  - The "which yield" question stays UNREAD. I did not disassemble past the `0x85f6c0` loop.
- **UNVERIFIED.** I did not read BS45C_DD05 or the where-the-traitor-stage-3-comes-from path.

### Q3: levers
- **A (force stage below 3): not endorsed.**
  - It is unfaithful to Arcade, which keeps stage 3 in the van windows.
  - `kbr_stage_byte` returns 3 first when `aboard`. An override at :721 would not undo `[rec+0x10]=4`, so it cannot un-board a bot the hook already boarded.
  - It also lowers the stage term that ZBecomeTraitor reads.
- **B (return 0.0 at :393 for cls==1): not endorsed.** It does not change what the Board RUN reads. It also hides the eval value.
- **Endorsed: C, narrowed.**
  - Extend `klbf_brain_turned` (klbotfill.c:1889) to also return true for a bot with `e->traitor` set while OnlineBrainTraitorArcade is active.
  - Mirror that in the `klbr_turned_actor` guards at klbrain.c:4165 (the `pendBoard` / hook boarding path) and :4183 (the grab path).
  - Leave the stage byte alone, so the real Board tactic still wins in van windows as in Arcade.
  - If `pendBoard` is not guarded, the real tactic's slot-45 call would board the traitor in a window. Guard it, or accept that as the Arcade behaviour.
- **SessionSafe:** this is DLL-owned code and data only, with no detour in a hashed range (`klranges.h`). It reuses the existing TraitorTurn skip at :2093, which has already run live.
- **Cost:** the traitor loses puppeteer loot, van and bank orders.

### Q4: read-only check
Keep the analyst's per-second line for the marked bot. Add three fields:
1. The marked soldier's ZCloseIn eval counter delta. This tests the contradiction above.
2. The result of the `0x55b9f0` yield check for the Defend goal. This tests whether `[goal+0x14]` is stale.
3. Whether the bot was hook-boarded or boarded by slot 45 (`klbf_ob` phase and `bsAt`).

Then compare a traitor with and without a fallback BOARDED event. The existing log already shows the ordering: BOARDED at 29:22.274, first Board-winner sample at 29:24.896.

I only read files; none changed. Logs are in `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\klhook\solo\` (BS45B_DM03 and ARC45_DM03 under `inst1\KLHook.log`). Source: `C:\kl-merge\kl-merge\klhook\klbrain.c`, `klbrain_logic.h`, `klbotfill.c`.
