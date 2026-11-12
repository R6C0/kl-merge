# Unattended playtests (JC's KLHook loop)

Set up on W's PC on 10 Oct 2026. Both stock tests pass:
- main menu: `RESULT: clean exit after 47 s`;
- Arcade Subway (F01), started from the menu: `RESULT: clean exit after 91 s`.

`<DD>` below is `C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days`.

## Run a playtest

Before you start:
- The game must be closed, and nobody should be using the PC.
- The game takes over the screen.
- While a script runs, your keyboard and mouse don't reach the game.

From the repo folder, run this one command:

```
py work\ext\kl-merge\tools\kl_autotest.py 1200 --tag arcade --shots 60-400:20 --hook work\ext\kl-merge\tools\build\klhook\test\dinput8.dll --ini scripts\klhook\arcade_f01.ini
```

This one starts Arcade Subway from the menu, waits 20 s after the level loads, then quits.

- **Quickest check:** this boots to the main menu, about 50 s:
  ```
  py work\ext\kl-merge\tools\kl_autotest.py 300 --tag menu --shots 30-50:4 --hook work\ext\kl-merge\tools\build\klhook\test\dinput8.dll --ini scripts\klhook\menu.ini
  ```
- **Reading the result:** the last line matters.
  - `RESULT: clean exit after N s` means it passed (exit code 0).
  - Anything else names the crash address, the assert, an integrity exit, or a hang.
- **Your files are put back:** the tool swaps in the TEST hook and the script's ini for that run only, then restores your `dinput8.dll`, checked by sha1. Look for `restore | dinput8.dll as before the run (sha1 828a620a)`.
- **Launch options:** keep them empty. Each script adds its own engine options in memory (`[Auto] CmdAdd`).
- **Steam:** the TEST hook blocks every stat, leaderboard and achievement write. The log must say `steam: import SteamUserStats wrapped`. If it ever says `steam: NOT GUARDED`, stop.

## Where things land

| What | Where |
|---|---|
| Result | `<DD>\KLHook.result` (`state=PASS / FAIL / EXIT`). A copy goes to `work\ext\kl-merge\tools\build\klhook\live\<tag>.result`. |
| Hook log | `<DD>\KLHook.log` holds all runs. This run's part is in `...\live\<tag>.log`; the tool's own output is in `...\live\<tag>.txt`. |
| Screenshots | `work\ext\kl-merge\tools\research\shots\<tag>_<seconds>s.png` |
| Crash dumps | `<DD>\KLHook_N.dmp` comes from the hook and is overwritten by the next run. `<DD>\kl2_490_crash_*.mdmp` is the game's own. |
| Your files during a run | `...\live\_before\`. The one-time backup is `<DD>\KL_PortBackup\dinput8.dll`. |

## Triage a crash

```
py work\ext\kl-merge\debug\triage.py --keep
```

It reads three things:
- the last session of `KLHook.log`;
- the dumps that session names;
- the game's own dump from that session.

It reports what faulted. For a crash while a level loads, it also names the level's node, class and field.

`--keep` copies the log and dumps to `%TEMP%\kl_triage\<time>\`; without it, the next run overwrites them. For more detail, use `debug\dump.py <dump>` and `debug\locate.py`.

## Put your normal setup back

Usually there is nothing to do, because the tool restores after every run. If a run was interrupted, or you're not sure:

1. Close the game.
2. Copy `<DD>\KL_PortBackup\dinput8.dll` over `<DD>\dinput8.dll`. That is Ultimate ASI Loader 9.7.0, sha1 `828a620a7af4587b05ee2fa202aaa971115e9ada`.
3. Delete `<DD>\KLHook.ini` if there is one.

Never leave the TEST hook installed.

## Loader climb (manual, in game)

This is not part of the unattended loop: the TEST hook doesn't load `ANP_Loader.asi`. Play normally with the ANP loader installed. The code is in `loader/climb.inc`.

**Mode file:** `<DD>\ANP_climb.txt`. The loader re-reads it within a second of a save, so you can switch modes while the game runs.

| File content | What happens |
|---|---|
| no file | `dry` |
| `dry` | W+E runs the ledge probe and logs it; nothing moves |
| `live` | W+E plays the climb |
| `off` | the climb does nothing |

Options can follow the mode word, e.g. `live trace=1` or `dry fwd=-1`:
- `trace=1`: a state line once a second, plus a frame trace during each climb.
- `fwd=-1`: flips the facing direction, if the dry log shows it is backwards.
- `needblock=1`: only climb while pushing into something (Dead Men's rule).
- `warp=dm`: steers the climb onto the ledge in two steps, like Dead Men. The default, `warp=end`, steers it straight to the end pose, like Dog Days' vault.
- `vehicle=snap`: no animation; teleports onto the ledge.
- `cam=0`: skips the vault camera.
- `snap=0`: no safety teleport at the end. (With the default `snap=1` it only fires when the climb finished by itself, END reason `animend` or `clip end`, and is unforced like the stock vault's end teleport; engine aborts such as death or a cutscene never snap.)

**Reading `ANP_log.txt`** (lines start with `climb:`):
1. At startup: `climb frame hook (steam_api!SteamAPI_RunCallbacks) ok`.
2. In a level: `frame hook live`, then after 10 s a ticks/s figure about equal to the frame rate.
3. Each W+E logs a `press` line, up to 4 `ray down` lines, `cand` lines and one `RESULT` line (`OK class=...`, `none: ...` or `abort:...`).
4. In live mode a climb adds `START ...` and `END reason=...`. `animend` or `clip end` is good; `timeout` or `channel lost` means the anim channel was not tracked.
5. `climb: FAULT ...` followed by `DISABLED` means a guarded engine call crashed and was caught. Restart the game and send the log.

**Unattended climb test** (`scripts/smoke_climb.py dry|live [spot ...]`; needs the loader built 11 Oct 06:20 or later):
- **Teleport hook:** `<DD>\ANP_tp.txt` = `x y z yawDeg [full]` moves Kane once, then the file becomes `ANP_tp.done`. The coordinates are his feet in world cm. Yaw 0 faces +z and 90 faces +x, the same convention as the probe's facing.
  - By default it uses the forced teleport `0x82cc40`, which also swings the camera behind him. `full` uses the gamedata teleport `0x8f3fa0` instead.
  - It logs `climb: tp: ...` with the pose read back at once, then a `tp: settled` line about 0.7 s later.
  - `trace=1` also logs `climb: pos: x y z yaw` once a second.
- **Spots:** `scripts/climb_spots.json`, written by `scripts/climb_spots.py`.
  - That script runs an offline copy of the probe against the level's `.HVK`, using `scripts/hvk_ray.py`.
  - The model reproduces the in-game rays of the 06:02 dry press to within 0.2 cm.
  - Each spot was checked with Kane's feet 60, 45 and 30 cm from the face.
- **Run:** the script holds `work\GAME_LOCK` and backs up and restores `ANP_climb.txt` and `ANP_autoload.txt`. For each spot it teleports Kane, holds W, taps E and records frames.
  - Output: `work\smoke\climb_<run>\` with `summary.json` (per spot: RESULT / START / END, positions before and after, pass), `log.txt` and the frames.

## Notes

- **These are stock tests.** While a TEST hook runs, `ANP_Loader.asi` and `KL2Fix.asi` are not loaded, because the hook replaces the ASI loader's `dinput8.dll`. Testing ANP levels this way needs the ASI loader under another file name (`kl2.exe` also imports `winmm.dll`). That is not done yet.
- **Local edit in the kl-merge checkout:** `klhook\build.bat` and `klhook\build_auto.bat` carry a one-line vswhere fallback. JC's versions hard-code VS 2022 *Community*, and this PC has the *Build Tools*. Keep it when pulling (`git stash`, `git pull`, `git stash pop`), or ask JC to take it upstream.
- **Rebuilding the hooks after updating kl-merge:** first run `set KL_WORK=%CD%\work\ext\kl-merge\tools`. Then build:
  - TEST: `work\ext\kl-merge\klhook\build_auto.bat --work`;
  - SHIP: `work\ext\kl-merge\klhook\build.bat --work`.
- **Use `py`, not `python`.** On this PC, `python` in a terminal opens the Microsoft Store stub.
