# 2026-10-31 scheduled check-in (cloud, 06:47-07:10 UTC): PC game folder idle, no new dump; the lift keys and six get-up keys get Mod Options rows and ini text

Read-only on the PC (the DD and DM folders were not attached to the scheduled session; one access request was granted). Nothing
launched, installed or touched on screen; the only file taken from the PC was a copy of the live `KLHook.ini` for a dry run of the tool.

## PC state

- Game folder: newest write still `dinput8.dll` 10-29 04:21 UTC (sha1 9e485dcf) with `KLHook.ini` b599def6 = the ship1030 pair;
  `KLHook.result` PASS F04 0 asserts 0 faults 128814 frames; `KLHook.log` 25.7 MB ends 10-27 20:50. Newest `KL_PortTools\build`
  folder 10-27 00:50 (mappool_1027). No local session has written anything since 10-29 (ce/c9 stopped on the monthly spend limit).
- Dumps: newest `KLHook_1.dmp` 10-26 08:11, newest `kl2_490_crash_*.mdmp` 10-25 19:18, both older than the log's notes and already
  written up. Nothing to triage.
- Cloud: `python tools/kl_tests.py` on 6c980ec: 30 pass, 0 fail, 15 skip (gcc-multilib installed here each run).

## Offline piece: the shipped lift keys were documented nowhere a player looks

The live ini carries `[KLHook] DoorCloseMs=8000`, `JoinOnline=1`, `DoorCloseRemote=1` (ship1029 / ship1030), and the repo has
`DoorRemoteStillMs` / `DoorRemoteMaxMs` since c9-doorhold-1029 - but the repo `klhook/KLHook.ini` (the sample `build.bat --work`
copies next to the DLL) named only `DoorCloseMs`, and that as "recommended off until benched", under a commented `;[KLHook]` header
inside the [Join] block, where `kl_mod_options.py` could not even see it; `JoinOnline`, `DoorCloseRemote` and the two Remote
timings were not in the ini at all, and none of the five had a Mod Options row (owner 10-24: "everything needs to be an option in
the mod ... (recommended on) next to it"; week plan T1: "not a secret feature").

Done (commit of this check-in, data and text only, no hook C code touched):

- `klhook/KLHook.ini`: a lift block in the real `[KLHook]` section: `DoorCloseMs` (recommended on at 8000; proven live A1LIFT7 +
  A1LIFT8, shipped ship1029), `JoinOnline` (recommended on; A1LIFTNET2F + A1LIFTNET3, shipped ship1030), `DoorCloseRemote`
  (recommended on; A1HOLD1 'doors held', shipped ship1030), `DoorRemoteStillMs` / `DoorRemoteMaxMs` (recommended on at 6000 / 30000;
  A1HOLD2; in the repo, NOT in the installed ship1030; GUESS values as in kldoorclose.c). The stale lower block is now a two-line
  pointer. Everything is written as `;Key=value` (documented, not set), so the sample still behaves as the DLL defaults.
- `tools/kl_mod_options.py`: rows `liftdoors` ([KLHook] DoorCloseMs 8000/0), `liftonline` (JoinOnline), `liftdoorsremote`
  (DoorCloseRemote + the two timings as helper keys, left alone on off), all G_CORE, recommended on; and six G_EXP get-up rows
  for keys the ini already marked recommended-on but no row offered: `onlinegetupreorder` (ReorderS 8), `onlinegetuprecede`,
  `onlinegetupfreefirst`, `onlinegetupbusyrange` (1500), `onlinegetuphold`, `onlinegetupplateau` (the 10-30 key; NOT built, NOT run,
  the row says so). Each carries `OnlineGetUp` (and KeepGoal / Busy where the DLL needs it) as a prerequisite helper key with
  off_value None, so turning a row off never turns the master off (the 10-27 rule).
- Checks: `kl_mod_options_test` 46/46; `--check-defaults klhook` every new row's dflt = the GetPrivateProfileInt literal
  (DoorCloseMs 0, JoinOnline 0, DoorCloseRemote 0, StillMs 6000, MaxMs 30000, the get-up keys 0); `--check-rec`: every row agrees
  with the ini markers, no proven key without a row; `--check-ini`: every row key mentioned. Dry run on a COPY of the live ini:
  `--list` reads liftdoors / liftonline / liftdoorsremote as [x] (= the installed state), `--set liftdoorsremote=off
  onlinegetupplateau=on onlinegetuphold=on --apply` wrote exactly `DoorCloseRemote=0`, `OnlineGetUpPlateau=1`, `OnlineGetUp=1`,
  `OnlineGetUpHold=1` (4 keys, nothing else moved); on a copy of the repo ini `--set liftdoors=on liftonline=on liftdoorsremote=on`
  wrote the five lift keys into `[KLHook]`. The Windows profile read-back is skipped on Linux (ctypes.windll), as always here.
  `kl_tests` 30/0/15 after the change.

## Owner

- Nothing to install from this check-in: it changes the Mod Options window and the sample ini only (a player who copies the sample
  gets the same DLL defaults as before). The next time Mod Options is opened the three lift rows show as on, matching ship1030.
- Still open from the earlier notes: a round with Medal quit (stutter comparison), `[Input] MouseMoveMs=16`, and the first build +
  bench of the three unbuilt 10-30 klbotfill changes (OnlineScanEveryRound cache, OnlineGetUpPlateau, the review fixes).
