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
