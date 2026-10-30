# 2026-10-30 scheduled check-in (cloud, 10:48-11:30 UTC): PC game folder idle, no new dump; the owner's 10-27 online rounds hitched 220-280 ms a round from the hook's own two memory scans - cached

Read-only on the PC (the DD and DM folders were again not attached to the scheduled session; one access request was granted).
Nothing launched, installed or touched on screen. The repo had a push at 10:47 UTC (ce's 7858fc1, the BP16b note), so a local
session is alive: this check-in stayed out of ce's getup work (klbotfill.c ~1150-1260) and c9's door-hold branch.

## PC state

- Game folder: newest write `dinput8.dll` 10-29 04:21 UTC = sha1 9e485dcf, `KLHook.ini` b599def6 (the ship1030 pair the benches
  restore); `KLHook.result` PASS F04 0 asserts 0 faults 128814 frames (10-27 20:00); `KLHook.log` 25.7 MB ends 10-27 20:50 in the
  owner's Alt+F4. Newest `KL_PortTools\build` folder 10-27 00:50.
- Dumps: newest `KLHook_1.dmp` 10-26 08:11, newest `kl2_490_crash_*.mdmp` 10-25 19:18, both older than the log's last note and
  already written up. Nothing to triage.
- Cloud: `python tools/kl_tests.py` on 7858fc1: 30 pass, 0 fail, 15 skip (gcc-multilib installed; the 13 logic C tests + 6 py).

## The owner's 10-27 log (PC clock), read for stutter

`KLHook.log` holds ten launches. Nine are a bench (18:28-20:00, TEST klauto build of 05:43, one F0x map each, `script 37`,
5 min): 4.4-5.1 frames over 33 ms a minute, every 1 s+ hitch inside the 25.9 s load window, hook tick slowest >= 60 ms in
8 of 233 windows. The tenth is the owner (SHIP 1027 15:09, 20:27:46-20:50:42, Medal + ReShade + the Steam overlay +
uiautomationcore loaded): a hosted Steam-lobby FA session alone (F06, OnlineSet=9, `lobby: Solo`), 3 rounds all escaped,
$12.79M, then Arcade F06 20:42-20:50.

| window | frames over 33 ms a minute | what |
|---|---|---|
| 10-24 17:35 / 19:21 (open_work_log) | 11 / 6.5 | owner |
| 10-25 14:56-17:39 | 53-128 | owner, Medal restarted 15:15 |
| 10-25 19:04-19:18 | 2.3 | owner, "stutter gone" |
| **10-27 20:27-20:50** | **17.7** (405 in 1373 s; 53 `core: hitch` lines of 120 ms+, sum 15.4 s, 4 of 1 s+) | owner, online host + Arcade |

Where the 53 hitches stood (probe samples, `stood at` / return addresses):

1. **Session teardown, 4 x ~1.0 s**: 20:28:52 + :53 and 20:41:11 + :12, both right after `session: state 0x19/0x28 -> 0x2e`
   (leaving the Steam lobby). Main thread `ntdll+0x7320c` (a wait) under `KERNELBASE+0x140d30` <- `tier0_s.dll+0x4010/+0x116cb`
   <- `steamclient.dll+0x7bf2e0`: the Steam client's own blocking leave on the game thread. Not ours; happens at the end of a session only.
2. **Lobby -> level, 20:28:46 + 20:29:16**: the same Steam wait (118-146 samples) during `state 0x11 -> 0x12` (the level archive open).
   Load time, not play.
3. **In play, once a round, 220-283 ms** (20:30:07 218 ms, 20:34:05 233 ms, 20:38:37 333 ms): the perf windows say
   `the hook's tick ... slowest 211.7 / 223.7 / 283.0 ms`, the probe has the main thread at `ntdll+0x735dc` under
   `KERNEL32+0x22640` <- `DINPUT8.dll+0x92b4e` ... `+0x27566` (this dll), and the log shows the cause one line earlier each time:
   `botfill: tactics: van: exit trigger ... found in 110 / 109 / 156 ms` immediately followed by
   `box scan: 1 ZAllyEscapeBox object(s) in 93 / 109 / 109 ms`. Two walks of all committed private memory (`klmv_exit_vehicle2`,
   `klbf_ot_boxscan`), back to back, EVERY round, the moment the first bot carries money - mid-round, while the owner plays.
   The Arcade side's equivalent (`near:` in klmove.c) was cached on 10-23 and read `kept from the last scan, checked in 0 ms`
   at 20:49:20 in the same log; the online side had no cache.
4. **Round start, 78-109 ms**: `hud: 2 ZOnScreenDisplay2 object(s) found by the scan` (20:28:43, 20:42:58) and the Arcade
   `near:` first scan 140 ms (20:42:59). At the load, where a hitch is already there; left alone.
5. The rest (120-200 ms, 2-5 a minute in play) stand in `win32u+0x101c/+0x107c` (PeekMessage / MessageCall) with
   `USER32`, `DINPUT8.dll+0x772e0`, `OpenAL32+0x3308`, `uiautomationcore+0x655f0`, `ReShade32+0x5ff67`, `gameoverlayrenderer+0x9944d`
   on the stack: the known message-pump chain of the 10-23 / 10-25 notes (Medal loaded again at 20:27:54). `stall: 10 s window
   procedures: 1.5 ms in all` every window, so the window procedure itself is not it.

## Fix (commit of this check-in): klbotfill.c `klbf_ot_kept`, [BotFill] OnlineScanEveryRound (default 0)

At a round start the last round's exit trigger and ZAllyEscapeBoxes are kept when (a) the scene name has not changed and
(b) no level archive has been opened since (klmove.c's `klmv_level_gen + klmv_scene_gen`, the 10-23 cache's generation), and
(c) the trigger still wears the vtable it had, its +0x24 entity's vtable is in the image, its node stands where it stood (1 unit)
and its vehicle field (first non-zero of +0x48..+0x54, what `klmv_exit_vehicle2` returns) is unchanged; every kept box passes
`klbf_ot_box_frame`. Trigger failing = both scans as before; a box failing = the box scan alone. The van-call path's own
"no longer valid" test also drops the kept state. The round's books (looks, call, gather, boxes' looks) reset as before.
Log: `botfill: tactics: van: exit trigger ... and N box(es) kept from the last round's scans, checked in 0 ms`. Type-checked
with `tools/run_harness_linux.sh --check-hook` (SHIP + TEST, no new warning), `kl_mod_options_test` 46/46; NOT built as a DLL,
NOT run in the game. Proof for a local session: a 3-round online host log with `kept from the last round's scans` in rounds 2
and 3, no `found in` / `box scan:` line there, bots still `van gather ... escape box 0` and `BOARDED`, hook tick slowest < 60 ms
in play.

## Owner

- Nothing to install from this check-in; the fix lands with the next hook build (ce/c9).
- The two 1 s hitches per online session are the Steam lobby leave (tier0/steamclient on the game thread), not the mod.
- The session's 2-5 small hitches a minute in play match the earlier Medal-loaded sessions; a round with Medal quit is still
  the open comparison (open_work_log 10-25 ~17:58).

---

# Second check-in, 14:47-15:10 UTC: PC still idle, nothing to triage; ce's BP16b "next" list implemented as [BotFill] OnlineGetUpPlateau (default off, NOT built, NOT run)

Read-only on the PC (DD + DM attached by one access request). Game folder unchanged since the morning run: `dinput8.dll` 9e485dcf (10-29 04:21 UTC),
`KLHook.ini` b599def6, `KLHook.log` ends 10-27 20:50, `KLHook.result` PASS F04 0/0, newest dump `KLHook_1.dmp` 10-26 08:11, newest
`kl2_490_crash_*.mdmp` 10-25 19:18 (both triaged before), `KL_PortTools\build` newest 10-27 00:50. Last push to origin 11:05 UTC (the morning
check-in's aeaae90); no local commit since c9's 12:50 note. Nothing launched, installed or touched on screen.

## Offline piece: the four "Next (wk-botpar)" items of ce's 10-29 ~07:20 BP16b diagnosis, behind ONE new key

ce's build + review agents stopped on the spend limit with nothing built, so the list was taken as written (open_work_log 10-29 ~07:20):

1. **Bot x,y,z + goal state on the `closing` line** (klbotfill.c, the 2 s speed window): now `... at (x, y, z), goal set (gx, gy, gz) D m off,
   place (px, py, pz), best B m T s ago, order A s old`. Logged in every mode as before (first 40 a rush).
2. **Plateau rule** `kgu_best` / `kgu_plateau` / `kgu_plateau_out` (klgetup_logic.h): best distance since the rush began, stamped when it improves
   by >= 1 m (smaller gains add up); still > stop + 5 m and no metre in 5 s = `bot N GIVEN UP on seat S ...`, the bot is released (as the release
   line) and `kgu_plateau_out` keeps it out of the pick 10 s (`guPlat`). Figures = ce's, marked GUESS.
3. **No Recede while routing** `kgu_recede_w`: with Detour's walked distance >= 3 m and the bot <= 8 m beyond its order distance there is no
   'receding' verdict (BP16b's 9 -> 14.7 m dither); BP14's 14.7 -> 34 m runaway is still caught once > 8 m beyond. 8 m is a GUESS. Without Detour
   (walked = 0) it is kgu_recede unchanged.
4. **Fallback place = the host's replica feet**: after a plateau on a seat (`seatPlat[i]`, reset on each fresh down and each round) the Hold
   rule's beacon place is skipped when the replica is readable (klbf_feet / +0x460), so the next bot is ordered to where the host's planner can
   reach. With no readable replica the place stays (the log says so).
5. **`getup: diag` hp**: `[[P+0x5fc]+4]` printed as `hp32 %08lx` (raw dword), no longer as a float (-2.6e38 was a shared non-health object).

All of 2-4 run only with `[BotFill] OnlineGetUpPlateau=1` (needs OnlineGetUp 1); default 0 = the 10-29 behaviour byte for byte in decisions.
Key documented in klhook/KLHook.ini after OnlineGetUpHold. Checks: `klgetup_test.c` +17 checks (ALL PASS, gcc -m32), `tools/kl_tests.py`
30 pass / 0 fail / 15 skip, `kl_mod_options_test` 46/46, `run_harness_linux.sh --check-hook` SHIP + TEST: 15 warnings = the baseline's 15,
none in klbotfill.c / klgetup_logic.h. NOT built as a DLL, NOT run in the game.

Proof for a local session (BP17, DD08 online, joiner goes down at BP16b's spot, host ini + `OnlineGetUpPlateau=1 OnlineGetUpDetour=1`):
one `GIVEN UP on seat` line within ~6 s of the dither starting, no `RE-ORDER ... receding` while the `closing` line shows the bot moving
(walked >= 3 m) within 8 m of its order distance, the next `sent to seat` line's place = the replica feet (differs from the beacon place by
the 1.6 - 1.9 m of BP15), and the seat up with a bot `HOLD` by it or `is by seat`; a failure mode to watch: every bot given up in turn at the
same place (the log's "same place (no replica readable)").

## Owner

- Nothing to install; the key ships with the next hook build (ce/c9) and stays off until a bench says otherwise.
- Still open from the morning: a round with Medal quit for the stutter comparison.

---

# Third check-in, 18:48-19:20 UTC: PC still idle, nothing to triage; the two unbuilt 10-30 changes reviewed by a fresh agent, 5 findings fixed

Read-only on the PC (DD + DM attached by one access request; `KL_PortTools\week_resume\resume_index.log` shows the Windows "KLMerge Resume" task
still skipping every 2 h because a session transcript is fresh, so a local session is alive). Game folder unchanged since the morning: `dinput8.dll`
9e485dcf (10-29 04:21 UTC), `KLHook.ini` b599def6, `KLHook.log` ends 10-27 20:50, `KLHook.result` PASS F04 0/0, newest dump `KLHook_1.dmp` 10-26 08:11,
`kl2_490_crash_*.mdmp` 10-25 19:18 (both triaged), `KL_PortTools\build` newest 10-27 00:50. No commit since 7fe6155 (14:57 UTC). Nothing launched,
installed or touched on screen.

## Offline piece: independent review of aeaae90 (klbf_ot_kept cache) and 7fe6155 (OnlineGetUpPlateau)

Neither change has been compiled with cl or run; a review agent read the whole of klbotfill.c, klgetup_logic.h and the helpers (klh_rd/klh_rd32 are
ReadProcessMemory-guarded, kle_node, klmv_frame, klmv_exit_vehicle2, the gen counters and where they are bumped). Verdict: no crash path, both keys at
their old setting reproduce the old decisions byte for byte, all format strings match their arguments, every new declaration is at block top (C89/cl).
Findings and what was done:

1. **Cache gen stamped AFTER the 110-156 ms walk** (klbotfill.c, the exit-trigger look): `klmv_level_gen` is bumped from the archive hook on any thread,
   so an archive opened during the walk gave a stale hit a fresh gen and the next round kept it on the object re-reads alone (the very hole the gen test
   exists for; klmove.c's near cache reads the gen before its walk). FIXED: `gen0` read before `klmv_exit_vehicle2`, stamped from it.
2. **A level with no ZAllyEscapeBox kept only half the cure**: `klbf_ot_kept()` returned 1 with 0 boxes and `klbf_ot_bxlooks` reset, so the 93-109 ms
   box walk still ran on the first tick of every round (4 looks a round). FIXED as klmove.c's `klmv_zero_gen`: the 4th empty look stamps
   `klbf_ot_nobox_gen` (gen read before that walk); a kept round under the same gen sets `klbf_ot_bxlooks = 4` and says "this level has none: the box
   scan is skipped too". A kept box that no longer reads still rescans.
3. Plateau exclusion is per bot, not per seat (a bot given up on seat A is out of seat B's pick for 10 s too). LEFT: a design choice, 10 s, documented.
4. **`kgu_best` only ever lowered**: a rusher that once stood 3 m away and was carried back out to 12 m (BP15's 3.6 <-> 9 m pattern) had a best inside
   stop + 5 m for good and could never plateau. FIXED: standing `KGU_PLATEAU_BACK_CM` (5 m, GUESS) or more beyond the best re-stamps the best at the far
   place and starts its 5 s clock anew; +2 checks in klgetup_test.c.
5. **`seatPlat` wiped by a one-pass down flicker** (beacon freshness lapsing while the replica's D does not read: the paired "is up / IS DOWN" lines):
   the BP16b fallback place was lost and the next bot went to the unreachable beacon spot again. FIXED: `hUpAt[i]` stamps the up; a down counts as fresh
   for the reset only when the seat was up >= 3 s (GUESS).
6. The GIVEN UP line's " (beacon)" suffix was computed from `seatPlat` and wrong after a second plateau. FIXED: `hpB` is set where the beacon place is
   copied into `hp`.
7. Note, not a defect: the cache is ON by default (`;OnlineScanEveryRound=0`), unlike the other 10-30 keys: the first SHIP build carries a never-run
   cache of a vehicle handle handed to 0x71e180, mitigated by `klbf_ot_call_van`'s re-validation (vtable / entity / node) and `klbf_ot_kept`'s
   re-read of the vehicle field. LEFT ON (it is the cure for the owner's every-round hitch); a builder wanting zero live risk sets OnlineScanEveryRound=1
   until 'kept from the last round's scans' has been seen once.

Checks: `tools/kl_tests.py` 30 pass / 0 fail / 15 skip (klgetup_test ALL PASS with the 2 new checks), `kl_mod_options_test` 46/46,
`run_harness_linux.sh --check-hook` SHIP + TEST 15 warnings = the baseline 15, none new. NOT built as a DLL, NOT run in the game.

## Owner

- Nothing to install; both fixes land with the next hook build (ce/c9) and are covered by the proofs in the two sections above.
- Still open: a round with Medal quit for the stutter comparison.
