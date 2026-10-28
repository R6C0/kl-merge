# Bots bench 1028: OnlineTriggers + OnlineTacticsTake=2 (T3/T4, wk-bots)

Not run live (owner away, hard rule: no launches in the writing session). Both features default OFF.
Research docs `re/bots_trigger_cops_1028.md` / `re/bots_online_arcade_1028.md` were NOT in the worktree when this was
written; the work rests on `re/triggerbox.md` plus a fresh read of kl2.exe (`debug/dasm.py`): update `0x42afd0`,
inside test `0x8c16c0`, stack depletion `0x4e3f40`.

## What the code does (klhook/klbotfill.c, host only, needs OnlineHost=1 + OnlineTactics=1)
- `[BotFill] OnlineTriggers=0|1|2` (2 = dry: log only). ~7 s and 30 s into a round the host scans private memory for the
  ZTriggerBox vtable 0xbc232c (klbf_ramp_probe's method), then once a second for each box that passes the update's own
  gates (+0x34 == 0, +0x40 enabled, +0x41 player-enter, +0x58 empty, +0x64 == 0, ECPS +0x60 in {0,4}, EFAMPS +0x68 / session
  sub-mode table, +0x74 re-arm clock over, +0x78 player flag clear) it asks `0x8c16c0(box, botActor)` per live Ally bot.
  Enough bots inside (+0x44) on a fresh entry: `[box+0x78]=1`, then `0x6ae730` (or `0x45f5d0` when `[box+0x6c]` is 0).
  One-shot boxes (+0x50 == -1) once a round; others need the bots to leave first, re-fire after their own re-arm time,
  max 3 fires per box per round. Ramp box (OnlineRampFire section) is skipped; money / exit controllers are other classes.
- `[BotFill] OnlineTacticsTake=2`: a grab calls `0x4e3f40(stack, remaining)` (fastcall shim: ecx = stack, edx = 0, arg =
  amount) instead of writing +0x34 = 0. State byte +0x64 of 2/3 is refused (the game's own refusal, logged by us).
  `OnlineTacticsTake=1` is the old raw write, `0` off.

## GUESSES / open
- A bot actor is a valid argument of `0x8c16c0` (it reads [obj+4] node +0x30..+0x38; actors have the same layout as the tracker's objects).
- The update's skips (node flag bit 10, `0x806cc0`) are not mirrored.
- Clients: the fire goes through the box's online sync object; whether the client sees the effect is what the bench shows.
- TODO ZTriggerBox2 / ZOnlineTriggerBox: other vtables, layout not verified: not scanned.

## Bench recipe (2 seats, kl_solo_test)
Inis (copied from `a1hire_1027`, with the new keys prepended): `C:\kl_build_1024\bots_1028\BOTS_host.ini` and `BOTS_join.ini`:
```
[Bots]    OnlineFill=1  OnlineFillSquads=1
[BotFill] OnlineHost=1  OnlineTactics=1  OnlineTacticsTake=2  OnlineTriggers=1   (set 2 for the dry first run)
```
The rest is the A1HIRE [Auto]/[Script] (host creates a System Link match, client joins, F9, round 1, shop, round 2).
Stage KLShopPage.ini into solo/<TAG>/inst1+2 if the page is used (see memory note), then, when the owner has been idle 5 min:
```
python kl_solo_test.py --hook C:/kl-merge/wt/wk-bots/klhook/out_bots_1028_test --n 2 --secs 700 --gap 45 --relaunch 2 --tag BOTS1028 --owner-away
```
(inis per instance: BOTS_host.ini -> inst1, BOTS_join.ini -> inst2, as for A1HIRE). Run 1 with `OnlineTriggers=2`, run 2 with 1.
Use the SHIP dll `out_bots_1028` for the final proof.

## PASS log lines (host KLHook.log)
- `botfill: trig: OnlineTriggers=1 ... OnlineTacticsTake=2 ...` at init, then `botfill: trig: on (host, N boxes)` (N > 0 on a stock FA map) and `botfill: trig: scan 1: ...`.
- Dry run: at least one `botfill: trig: DRY would fire box XXXXXXXX (k bot(s) inside, ...)` once a bot crosses a player-enter box.
- Live run: `botfill: trig: FIRE box XXXXXXXX via 0x6ae730 (...)` followed by the map's reaction (cops / door / spawn appear; cross-check with squad logs); no repeat spam (max 3 per box, one for re-arm -1).
- `botfill: tactics: bot N ... GRABBED stack ... (taken through the game's 0x4e3f40 on the host)` and the stack really disappears / lowers on the host; no `0x4e3f40 refuses` line for fresh stacks.
- FAIL signs: any fault / `kl2_*_crash` dump after a FIRE line, a box fired with 0 bots inside, an exit or ramp box in the FIRE lines, the same box firing more than 3 times, the round not reaching state 0x19 / 0x20 cleanly.

## wk-bots2 (2026-10-28): OnlineBank + OnlineBoardAll (host only, default 0, not run live)
Gates read in kl2.exe: the online grab (ZOnlineMoneyCtrl 0x6cdb40, call 0x6cdb9c to 0x7f6850, branch 0x6cdbd0 to 0x7aace0) ends in the Sv rules
slot 46 = 0x8234d0 (vtable 0xbd2eb4), which needs a ZFFPlayer with a seat (`[player+0x2748]`, 12-seat table). A bot has no seat, so the game
cannot bank for it online (Arcade: slot 201 0x56f6e0 -> 0x8e8750, crew record). So OnlineBank is a host ledger (log + round summary), not a score change.
- `OnlineBank=1|2`: books a bot's carried money once when it is counted aboard. Lines: `botfill: bank: bot N ... banked $X aboard; ledger now $Y` and
  in the round summary `bank: round ledger: N bot(s) banked $Y of Z carried`. 2 tags lines DRY (same ledger).
- `OnlineBoardAll=1|2` (+ `OnlineBoardAllM`, cm): van state 4 or 5 (GUESS: 4 = last call, 5 = leaving) and a carrier within M of the escape box is counted aboard:
  `botfill: boardall: bot N ... counted aboard` (2 = `DRY would board`). Removal from the world still needs OnlineBoard=1.
Run as the BOTS1028 recipe above, hook `C:/kl-merge/wt/wk-bots2/klhook/out_bots2_1028_test`, tag BOTS2, first with both keys 2, then 1.
PASS: bank lines match the `GRABBED` tallies of the bots that boarded; boardall lines only in state 4/5; 0 faults. FAIL: bank for a bot that never boarded, boardall at state 3.

## wk-bots2 (2026-10-28): OnlineBankCredit (host only, default 0, not run live)
Route (a) of re/bots_bank_online_1028.md: the call at 0x681103 (settlement 0x5e2230, ecx = rules) is retargeted; before it runs the host adds the OnlineBank ledger to the first
escaped human seat with 0x5a18c0, so 0x6f4960 pools it into the team money. Needs `OnlineBank=1|2`, `OnlineTacticsTake=1|2`, `OnlineTactics=1`. `OnlineBankCredit=2` = log only.
Run as the BOTS2 recipe, hook `C:/kl-merge/wt/wk-bots2/klhook/out_bots3_1028_test`, tag BOTS3, first `OnlineBankCredit=2`, then 1; one bot must board with loot and one human must escape.
PASS: host log `botfill: bankcredit: settlement call 0x681103 -> 0x5e2230 retargeted` at start; at round end `botfill: bankcredit: seat N +$X (ledger $Y) Sharable A -> B`
(X = Y unless clamped, B = A + X); mode 2 shows `DRY would credit`; the client HUD / end-of-round score of the escaped humans includes X split by the escaped count; 0 faults; the round ends normally (state 0x1f).
FAIL signs: `REFUSED` at patch time, `FAULT` line, no bankcredit line although the ledger had money, a client score that does not move (replication GUESS wrong), a crash in 0x5a18c0 / 0x942b20
(Quazal exception 0xe0030000 = not the master), money credited twice (Take=0 must log `skipped`), the seat credited was dead or police.

## wk-bots2 (2026-10-28): OnlineTriggersExtra (ZTriggerBox2 / ZOnlineTriggerBox, host only, default 0, not run live)
Hook `C:/kl-merge/wt/wk-bots2/klhook/out_bots4_1028_test`, tag BOTS4. Ini: `[BotFill] OnlineTriggers=1 OnlineTriggersExtra=2` first, then 1 (OnlineTriggers=2 makes everything dry).
Stock maps hold no ZOnlineTriggerBox and no cop-wave ZTriggerBox2, so the bench is a graft map (Dead Men map with TriggerBox2 / OnlineTriggerBox nodes) or a stock map to prove the scan and the skip of the loot-stack boxes.
PASS lines (host KLHook.log): `botfill: trig: OnlineTriggers=1 ... OnlineTriggersExtra=2`; `botfill: trig: scan N: ... tracked (ZTriggerBox a, ZTriggerBox2 b, ZOnlineTriggerBox c)` with the loot-stack boxes counted in "ramp box(es) left" and NOT in b;
dry: `botfill: trig: DRY would fire ZTriggerBox2 xxxxxxxx (k bot(s) inside, delay d, one-shot o, entry edge)` or `... ZOnlineTriggerBox ...` when a bot enters a players-only box;
live: `botfill: trig: FIRE ZTriggerBox2 ...` or `FIRE ZOnlineTriggerBox ... starting the update's own delay`, then the box's effect (list targets react / the net event reaches the client), no repeat spam, 0 faults.
FAIL signs: a FIRE for a loot-stack box, a box fired with 0 bots inside, the same box more than 3 times, a fault after a FIRE line, a ZTriggerBox2 skip line `not in the update list` on a box that should be live (the `+0x18` bit GUESS is wrong).
Build checks run here: build.bat and build_auto.bat compile clean, `python tools/kl_mod_options_test.py` PASS (46 checks).
