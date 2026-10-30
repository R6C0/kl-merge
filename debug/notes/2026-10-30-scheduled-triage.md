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
