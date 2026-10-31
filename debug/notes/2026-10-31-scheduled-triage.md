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

---

# 2026-10-31 second scheduled check-in (cloud, 14:48-15:05 UTC): PC idle, no new dump; the owner's 10-27 log read for what the hook asked for and did not get

Read-only on the PC again (DD + DM attached by one access request; nothing launched, installed or touched on screen). Files taken
from the PC: the installed `KL_Camcorder.fx`, `KL_Look.fx`, `ReShade.log` (compare), nothing else.

## PC state

- Game folder unchanged since 10-29 04:21 UTC: `dinput8.dll` 9e485dcf + `KLHook.ini` b599def6 (ship1030), `KLHook.log` 25.7 MB ends
  10-27 20:50, `KLHook.result` PASS F04 0/0. Dumps: newest `KLHook_1.dmp` 10-26 08:11, newest `.mdmp` 10-25 19:18 - both triaged.
  Newest `KL_PortTools\build` folder 10-27 00:50 (mappool_1027) before this check-in's `lenscrack_1031`. Nothing to triage.
- Cloud on 3f28543: `kl_tests` 30 pass / 0 fail / 15 skip (gcc-multilib); `run_harness_linux.sh --check-hook` SHIP + TEST 0 errors,
  15 warnings = the baseline (`%I64d` is a GCC false positive, the rest unused locals).

## The owner's 10-27 20:27-20:50 session, read for anomalies (not stutter this time)

The 10th session in the log (System Link host, OnlineSet=9: DM07 in F06, then DM01 in F01; two rounds each). Lines that say the
hook wanted something and did not get it, by count, with what they mean:

| line | n | meaning |
|---|---|---|
| `reshade: wanted but not among the loaded effects even after a reload: KL_LensCrack@KL_LensCrack.fx` | every launch | **the lens-crack shader was never installed** (below) |
| `charonline: my body wants Parker (char 14) and level f06\f06_main has no such model (wardrobe missing): the stock body stays` | 1 | DM07 has no wardrobe bake; known T2 item (hired / chosen body stays stock on unbaked maps) |
| `charonline: own body NOT found (gamedata sel 255 ...)` then `found by gamedata slot` 0.2 s later | 4 | the first tick after the load, before the table fills; harmless, the next tick finds it |
| `hud: scoreboard: OnlineBoardState: 3 s in state 1f: clock element renders +0 ... G15 is wrong` | 3 | the state-path fallback draws nothing online; the card came from OnlineBoardCarrier (+678 draws, 0 stock) - comment in klhud_board2.c now says so |
| `cam: FovStep REFUSED for this camera: cam+0x7a4 reads 0.06000` | 3 | known harmless (1027y note: 'FovStep REFUSED (camera, not ce) is harmless') |
| `shopnames: restored 1 slot(s), 11 dropped (pointer no longer ours)` | 3 | round-end restore, by design |
| `join: player 0 entered box 9 while a ride is in progress: ignored` | 3 | the Retomoto lift's join box ('06_Exit', y 19500) during its 2.5 s ride: the ride guard, by design |
| `fclimb: press ignored (W not held / action running)` | 9 | by design |

No fault, no assert, no refused patch, no `memory:` warning in the session; exit was the owner's Alt+F4 at 20:50:42.

## Finding: KL_LensCrack.fx never reached the game (owner's ask of 10-17)

`<DD>\reshade-shaders\Shaders\` holds KL_Camcorder (10-24), KL_CameraFX, KL_FXAA, KL_Glare, KL_Look (10-15) - no KL_LensCrack.fx
(`re/lens_crack.md`: "Install (by the owner; nothing was installed)"). The hook ([Graphics] LensCrack=1 default) puts the technique
into the live preset anyway, so every launch with the LiveLeak look does one extra effect reload (`LiveLeak look with a technique that
was not loaded: the live preset loaded again`) and the "glass breaking when shot a lot" the owner asked for never showed.
Done: kit `<work>\build\lenscrack_1031\` = the repo's `KL_LensCrack.fx` (615bdccd, written CRLF like its siblings), INSTALL_lenscrack.bat
(copy into the Shaders folder, nothing replaced; keeps a `.before-1031lenscrack` if one ever exists), UNDO_lenscrack.bat (moves it
to `.off-1031`), README.txt. The game folder was NOT touched: the shader has never been seen rendered (compiled with fxc only), so
the owner installs it (ReShade refuses a bad effect gracefully: ReShade.log names the line, the technique stays absent as now).

## Finding: the repo's KL_Look.fx was behind the owner's game

Installed `KL_Look.fx` is v2.3 (10-15, dilated 1/8 sky mask + per-pixel sky decision from the owner's "white glow round wires / palms /
the plane" pictures); the repo folder `reshade/` (added 10-25) carried the older v2.1 text. Copied the live file in (LF in the repo).
`KL_CameraFX.fx` / `KL_Glare.fx` match byte for byte; `KL_Camcorder.fx` matches as text (CRLF on the PC; the 10-24 sky shoulder is in both).

## Owner

- `G:\...\Kane and Lynch Dead Men\KL_PortTools\build\lenscrack_1031\INSTALL_lenscrack.bat` (game closed) if you still want the cracked
  lens; proof in KLHook.log: `KL_LensCrack@KL_LensCrack.fx` among "managed technique(s) present" and no "wanted but not among" line.
  Preview without being shot: ReShade overlay > KL_LensCrack > "Preview: three cracks". Numbers are all GUESS (re/lens_crack.md).
- Still open from the earlier notes: a round with Medal quit (stutter comparison), `[Input] MouseMoveMs=16`, and the first MSVC build +
  bench of the unbuilt 10-30 klbotfill changes (OnlineScanEveryRound cache, OnlineGetUpPlateau, the review fixes) and c9's door-hold
  fix (A1HOLD2 PASS, merged, not in ship1030).
