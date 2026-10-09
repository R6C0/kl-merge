# KLHook for the live agent: which DLL, which ini, what each check expects

STATE 2026-10-09 15:20 (agent i-hook, second pass). Two builds exist:

- **`ihook` (12:49)** - HAS RUN LIVE (agent i-live, runs HK1 HK3 S0 S1 S2 J1 J1b J2 J3; logs in
  `<work>\build\klhook\live\`). Section 3 says what was seen. Still usable.
- **`jhook` (15:16)** - the same plus the fixes those runs asked for (section 2). BUILT, off-game batteries
  passed, **NOT RUN LIVE**. Nothing was installed into Dog Days by me. Use this one from now on; its first run
  is check N0.

Sources: `klhook/` (`klhook.c` includes `klfix.c kljoin.c klsteam.c klslot.c` and, for TEST, `klauto.c`).
Design and evidence are in the top comments of `klsteam.c` and `kljoin.c`; this note is only what a live run
needs.

## 1. Files

| what | where |
|---|---|
| SHIP dinput8.dll (189,440 bytes, sha1 1972cc1f...) | scratch `...\scratchpad\jhook\ship\dinput8.dll` |
| TEST dinput8.dll (238,592 bytes, sha1 60e345a4...) | scratch `...\scratchpad\jhook\test\dinput8.dll` |
| the 12:49 pair (sha1 884a9133... / b14bbd93...) | scratch `...\scratchpad\ihook\ship`, `...\ihook\test` |
| rebuild | `klhook\build.bat <out>` (SHIP), `klhook\build_auto.bat <out>` (TEST) |
| ini | any ini used so far works unchanged; new keys are optional (`klhook\KLHook.ini` lists them) |
| Retomoto's join | copy `klhook\KLJoin.retomoto.ini` to `<DD>\Scenes\Locations\F01\KLJoin.ini` (the folder the level archive is opened from; with `[Redirect] F01=<map>` it is `KLExpansion\Maps\<map>\KLJoin.ini`). The file now holds J1b's box (x 2550..2790, y 19500..19800, z 800..1100 = `kl_fa_author.JOIN_BOX`), not the inside of the car. |

scratch = `C:\Users\Henri\AppData\Local\Temp\claude\c--kl-merge-kl-merge\1e45a579-7fed-40e8-8fc6-e1bb5fcc6977\scratchpad`.
The DLL is installed as before (`kl_autotest.py --hook <folder> --ini <ini>` swaps it in and puts the original
back); a locked file is renamed aside, never deleted.

**Rule for every scripted run that may reach a score page: the DLL must be a TEST build of klhook and the log
must show `steam: import SteamUserStats wrapped`.** Run S2 showed why: at a session end the game sends 29
stats as ABSOLUTE totals from the profile block in memory, and the klauto route (DisableSplashScreens) never
loads a profile - everything but NumRoundsPlayed was 0. Unguarded, that overwrites the owner's Steam totals
with zeros. The owner's installed dinput8.dll and a SHIP build do not block a stock level.

## 2. What the 15:16 build changes (each from a live observation)

| seen live | change | where |
|---|---|---|
| `join: box 9 NOT usable ... entry 5 is past the end of the jump list (1 entries` during every load, although the box worked | the jump list is described, and boxes are checked for the log, only when its length has stood still for 1.5 s; a player entering a box is still resolved against the list as it is then | `kljoin.c` |
| J1b: `500 ms after the request` came in the same millisecond, with the old position | timer bug (`tick \| 1`, unsigned compare) fixed | `kljoin.c` |
| HK1: `tick: driven by` flipped four times in two seconds | the same bug in the fallback test: on an even tick count the fallback thread ticked although the main loop was ticking. Fixed; off-game the line now comes twice instead of six times | `klhook.c` |
| S2: the SESSION END line came 29 ms AFTER the BLOCKED lines | the session state is looked at before every write call too; the line now stands first | `klsteam.c` |
| HK1: the filter under ours was CSERHelper.dll / wrap_oal.dll, never the game's, so a fatal fault would not have written Steam's `kl2_490_crash_*.mdmp` | the game's filter (0x90b780) is taken from the instruction that installs it (0x58ffc3, compared byte for byte, read only) | `klhook.c` |
| HK1: no `exit:` line at an AutoExit end | MSVCR90 `exit` / `_exit` import slots (0xb103d0, 0xb104b0; 0 checks; the slots klauto has wrapped since X1) are wrapped in both builds. ASSUMPTION that AutoExit leaves through `exit()`: check X1 | `klhook.c` |
| S3 / S4 not runnable: a SHIP build cannot be scripted | a TEST build still blocks everything but now logs what the SHIP policy would have decided (lines below) | `klsteam.c` |
| J1: the box inside the car is unreachable (doors shut, player stops at x 2727) | `KLJoin.retomoto.ini` = the box that fired in J1b / J2 / J3 | `klhook\KLJoin.retomoto.ini` |
| - | new key `[Steam] StockRows=0`: FindOrCreateLeaderboard fails while the upload is blocked (no stock rows on an expansion map's score page). Default 1 = as before. Check S5 | `klsteam.c` |

## 3. Seen live with the 12:49 build (do not repeat unless something changes)

| check | run | result |
|---|---|---|
| S0 the guard at boot, direct boot | S0 | wrapper lines, `level archive f01\f01_main.zip ... NOT stock`; PASS. The `proxy handed out` line does not come on a direct boot |
| S1 import slot 0xb107c8 in a real session | S1, then S2 HK3 J2 J3 | no `INTEGRITY EXIT` in six sessions; `proxy handed out` at the first score page (state 0x20) |
| S2 a session that ENDS | S2 | 29 `BLOCKED SetStat`, `BLOCKED StoreStats()`, `BLOCKED UploadLeaderboardScore(board 'KL2_Heist0_TotalMoney', keep best, score 0)`, `SESSION END`, end page with 'Quit'; Steam's cache file unchanged (date and sha1) |
| HK3 `Hooks=1` under SessionSafe | HK3 | 13 `patch REFUSED`, 5 detours, round starts and ends |
| J1b the join, direct boot | J1b | `join: player 0 entered box 9 at (2719, 19601, 1100): jump to entry 5 'Specials!JumpPoints!06_Exit' requested`; next position the lobby car |
| J2 the join in a session | J2, J3 | the same at (2709, 19601, 1099); `is at (6411, 570, -6221) 500 ms after`; alive 4.5 min after, no integrity exit |
| session states | all | 0x12 0x15 0x16 0x18 0x19 (round runs) 0x1f 0x20 (score page) 0x23 0x24 0x25 0x26 0x16 ...; 0x1f -> 0x28 = session end |

## 4. Lines every run must show at start (15:16 build)

```
build: TEST (klauto), Oct  9 2026 15:16:0x; ...        (or: build: SHIP, ...)
core: 2 more import slot(s) wrapped for the exit line (MSVCR90 exit yes, _exit yes)
core: 2 import slot(s) wrapped (ExitProcess yes, SteamAPI_RunCallbacks yes); EndOnFatal=1
steam: import SteamUserStats wrapped (1 slot): ISteamUserStats 007 proxy, 30 slots, 9 writes gated; policy: TEST build - every leaderboard upload, stat and achievement write is BLOCKED, on every level
        (SHIP: ...; policy: writes are BLOCKED on a level that is not the stock level of its slot (klstock.h); stats stay blocked until restart once such a level ran)
steam: CreateFileA yes, CreateFileW yes wrapped to see which level archive is opened (no redirect: [Expansion] is off)
```

A SHIP build, or a TEST build with `[Auto] Enable=0`, also shows
`fatal-fault filter: the game's own is kl2.exe+0x50b780 (read from its start-up code); it is called after ours has logged`.
With klauto on, klauto's own `end hooks: 5 of 5 import slots wrapped` still comes (it wraps exit / _exit on top
of the core's; both chain).

**If the log shows `steam: NOT GUARDED - ...` the guard is not there: end the run before any score page and
report the line.** Causes it names: steam_api.dll without the text `STEAMUSERSTATS_INTERFACE_VERSION007`, the
import not found, a real interface whose table has no code at one of 30 slots.

When a level loads (TEST build; size / hash are those of the build in the slot at 14:01):

```
steam: level archive f01\f01_main.zip opened from SCENES\Locations\F01\F01_Main.zip: NOT stock (295929966 bytes, directory hash 29c76ee0; the stock archive has 217471616 bytes, 94c9f794)
steam: level 'SCENES\Locations\F01\F01_Main.gms': TEST build: nothing is written to Steam - leaderboard upload BLOCKED, stats and achievements BLOCKED
steam: level 'SCENES\Locations\F01\F01_Main.gms' under the SHIP policy: its archive f01\f01_main.zip is not the stock one: 295929966 bytes, directory hash 29c76ee0; the stock archive has 217471616 bytes, 94c9f794 - leaderboard upload would be BLOCKED, stats and achievements would be BLOCKED
```

(The `level archive` line comes up to three times per load, as in the 14:12 log: the game opens the archive
under two spellings of the path, `SCENES\Locations\...` and `SCENES/Locations/...`.
On a DIRECT BOOT the scene name is set before the archive is opened, first as
`'SCENES\Locations/F01/F01_Main.gms'` (15:14 log): there the first pair of `level` lines says, under the SHIP
policy, `its archive f01\f01_main.zip was not seen being opened` - blocked all the same - and a second pair
with the archive's verdict follows within a second. The 15:16 build says a level again whenever its verdict
changes.)

## 5. Live checks for the 15:16 build, one variable per run

Run `python debug\zombies.py --count` before and after each, as before.

**N0 - the new DLL, nothing else (TEST DLL from `jhook\test`; the ini, slot build and walk of run J2).**
Variable: the DLL. Expect the lines of section 4; the same RESULT as J2; and, new against J2's log:

```
join: reading <DD>\SCENES\Locations\F01\KLJoin.ini for level f01\f01_main
join: box 9: (2550, 19500, 800) - (2790, 19800, 1100) -> entry 5, name '06_Exit', target (6272, 563, -6305)
join: 1 box(es) from ...\KLJoin.ini for level f01\f01_main
join: level 'SCENES\Locations\F01\F01_Main.gms': 1 box(es) active; jump list has 6 entries          <- about 1.5 s after the list stopped growing; NOT 'has 0 entries'
join: box 9 -> entry 5 'Specials!JumpPoints!06_Exit' at (6272, 563, -6305)
join: player 0 entered box 9 at (27xx, 19601, 1099): jump to entry 5 'Specials!JumpPoints!06_Exit' requested ([gamedata+0x8d4] = 5, [0x156b358] = 1)
join: player 0 is at (about 6400, 570, -6221) 500 ms after the request                                 <- half a second later, the lobby car, not the tower
```

Must NOT show: `join: box 9 NOT usable on this level` (if it does now, the list really lacks the entry: the
line says how), more than about two `tick: driven by` lines per level load, `INTEGRITY EXIT`.
(`has 6 entries` is RT4's count; if the build has another number of JumpPoints the line says so and `box 9 ->
entry 5` must still name 06_Exit.)

**S2b - order at a session end (TEST DLL; S2's ini and script: stand still, three lost rounds, $0).**
Variable: none but the DLL - run it once to see the new order. Expect, in this order:

```
session: state 0x1f -> 0x28 (game mode 4) = SESSION END: the game now uploads the session total and commits stats and achievements; Steam writes: BLOCKED - TEST build: nothing is written to Steam | SHIP policy: would BLOCK - its archive f01\f01_main.zip is not the stock one: ...
steam: BLOCKED SetStat('NumRoundsPlayed', 1) - TEST build: nothing is written to Steam | SHIP policy: would BLOCK - 'SCENES\Locations\F01\F01_Main.gms' ran in this process and was not the stock level of its slot: stats stay blocked until the game is restarted
... 28 more BLOCKED SetStat lines
steam: BLOCKED StoreStats() - TEST build: ... | SHIP policy: would BLOCK - ...
steam: BLOCKED UploadLeaderboardScore(board 'KL2_Heist0_TotalMoney', keep best, score 0) - TEST build: ... | SHIP policy: would BLOCK - its archive f01\f01_main.zip is not the stock one: ...
```

If the SESSION END line still comes after the BLOCKED lines, the game sets state 0x28 after its handler ran
(then the old order is simply how it is; report it). No `passed on` line; Steam's
`C:\Steam\appcache\stats\UserGameStats_1165402018_28000.bin` keeps date 2026-03-13 11:23:16 / sha1 00b95332.
This run is also **S3 seen through a TEST build**: every `SHIP policy: would BLOCK` is what a SHIP build
would have done on this level.

**S4t - the SHIP policy on a STOCK level, seen through a TEST build (TEST DLL; menu route; start menu entry 1
= F02 instead of entry 0; nothing else loaded before in that process; the session may end - a TEST build
blocks).** Variable: the level. Expect:

```
steam: level archive f02\f02_main.zip opened from ...: STOCK (196125170 bytes, directory hash c30281d3)
steam: level 'SCENES\Locations\F02\F02_Main.gms': TEST build: nothing is written to Steam - leaderboard upload BLOCKED, stats and achievements BLOCKED
steam: level 'SCENES\Locations\F02\F02_Main.gms' under the SHIP policy: stock level - leaderboard upload would be allowed, stats and achievements would be allowed
```

and at a session end `... | SHIP policy: would PASS ON - stock level` behind each BLOCKED line. That is the
proof that a SHIP build leaves a stock map alone. (If the F01 slot's level was loaded earlier in the same
process, stats read `would BLOCK - ... ran in this process ...: stats stay blocked until the game is
restarted` - also by design.)

**S5 - StockRows=0 (TEST DLL; S1's ini plus `[Steam]` `StockRows=0` and `Log=2`; one round to the score
page, Ready, a second round).** Variable: the key. Expect at start `...; StockRows=0: FindOrCreateLeaderboard
fails too while the upload is blocked`; at the first score page

```
steam: BLOCKED FindOrCreateLeaderboard('KL2_Heist0_TotalMoney') ([Steam] StockRows=0: no rows of that board, and no upload can follow) - TEST build: nothing is written to Steam | SHIP policy: would BLOCK - ...
```

the page `HeistStatusLeaderboard` up with the round's own numbers and NO friends rows; RETURN = Ready works;
round 2 starts; no fault (the path is the game's own 'call failed' branch 0x789763, task status 3, and
klfix's row count line `leaderboard service ...: row count ...` covers the read that follows). If the page
faults or hangs: report the address - the key stays off by default until this has been seen.
At a session end with this key there is no `UploadLeaderboardScore` line at all (the upload task fails at
its own FindOrCreateLeaderboard, 0x5ebe77).

**X1 - SHIP build, direct boot, AutoExit (SHIP DLL from `jhook\ship`, three-line ini; HK1 again).**
Variable: the DLL. Expect `build: SHIP`, the section 4 lines with the `fatal-fault filter: the game's own is
kl2.exe+0x50b780` line, `steam: level archive f01\f01_main.zip ... NOT stock`, `steam: level '...': its
archive f01\f01_main.zip is not the stock one: ... - leaderboard upload BLOCKED, stats and achievements
BLOCKED` (this IS S3 on a real SHIP build: no `under the SHIP policy` line there), `tick: driven by` at most a
few times, and at the end ONE of `exit: exit(n)` / `exit: _exit(n)` / `exit: ExitProcess(n)`. If the run still
ends without any `exit:` line, AutoExit leaves by a fourth way (TerminateProcess?): report it, nothing is
wrong with the run.

**HK4 - SHIP DLL on a build known to fault (unchanged from h-hook's check 4).** Expect `FATAL unhandled
exception`, a KLHook dump, a new `kl2_490_crash_*.mdmp` (the game's filter is now always found), `process
ended here`, no new 'Application Error' event, an unchanged zombies count.

**J3 (optional) - a stale file.** The bank build in the slot with Retomoto's `KLJoin.ini` left beside it:
expect `join: box 9 NOT usable on this level: ...` about 1.5 s after the list is complete, and no jump.

Not needed any more: S3 / S4 on a real SHIP build through the menu by hand (S2b, S4t and X1 show the same
decisions). **Never let a SHIP build or the owner's hook end a scripted session on a stock level: there the
writes go through, by design.**

## 6. Keys

```
[KLHook]  ExitLog=1 (ExitProcess, exit, _exit)   Tick=1   EndOnFatal=1   LbFix=1   SessionSafe=1 (TEST)   Join=1
[Steam]   Block=1 (SHIP: 2 = block always; there is no off; TEST always blocks)
          Log=1 (2 = every call, 0 = none)   State=1 (session lines)   StockRows=1 (0 = see S5)
[Join] / [Join.2] .. [Join.8] in KLHook.ini, or the same sections in KLJoin.ini beside the level archive:
          Min=x y z   Max=x y z   Entry=n   Name=text   Target=x y z   Tolerance=8   Scene=text (KLHook.ini only)
```

Boxes of a level's own file are numbered from 9; 1..8 are KLHook.ini's.

## 7. Not covered

- The local high-score list on disk (`re/leaderboard.md` 4.3: the slot's top-12 and `HeistTotalPoints[slot]`
  in the profile, written by 0x68b930 / 0x6587c0) is NOT guarded. On the klauto route the profile is never
  loaded, so nothing is saved there; a player who starts an expansion map from the real menu gets its score
  into the stock slot's LOCAL list. Not Steam; not done because it means writing into the owner's profile
  in memory at the right frame, which nothing has tested.
- With `StockRows=1` (default) an expansion map's score page shows the stock map's friends rows.
- The join moves this machine's local players only (0x8f3fa0 loops over local players; the hook reads local
  feet): a peer needs the hook and the same KLJoin.ini. Not run with two machines.
- A SHIP build blocks stats from the first non-stock level until the process ends: a stock round played
  afterwards in the same process is not counted by Steam either (the stats block is re-read from Steam at
  the next start, `ZAsyncTaskReadProfileSteam` 0x46f5a0 - ASSUMPTION that this read runs at every normal
  boot; on the klauto route it does not run at all).
