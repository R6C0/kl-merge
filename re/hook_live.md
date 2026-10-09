# KLHook for the live agent: which DLL, which ini, what each check expects

STATE 2026-10-09 12:50 (agent i-hook): **BUILT, off-game battery passed, NOTHING RUN LIVE.** Nothing was
installed into Dog Days by me. Sources: `klhook/` (`klhook.c` includes `klfix.c kljoin.c klsteam.c
klslot.c` and, for TEST, `klauto.c`). Design and evidence are in the top comments of `klsteam.c` and
`kljoin.c`; this note is only what a live run needs.

## 1. Files

| what | where |
|---|---|
| SHIP dinput8.dll (186,368 bytes, sha1 884a9133...) | scratch `...\scratchpad\ihook\ship\dinput8.dll` |
| TEST dinput8.dll (236,032 bytes, sha1 b14bbd93...) | scratch `...\scratchpad\ihook\test\dinput8.dll` |
| rebuild | `klhook\build.bat <out>` (SHIP), `klhook\build_auto.bat <out>` (TEST) |
| ini | any ini used so far works unchanged; new sections are optional (`klhook\KLHook.ini` lists them) |
| Retomoto's join | copy `klhook\KLJoin.retomoto.ini` to `<DD>\Scenes\Locations\F01\KLJoin.ini` (the folder the level archive is opened from; with `[Redirect] F01=<map>` it is `KLExpansion\Maps\<map>\KLJoin.ini`) |

scratch = `C:\Users\Henri\AppData\Local\Temp\claude\c--kl-merge-kl-merge\1e45a579-7fed-40e8-8fc6-e1bb5fcc6977\scratchpad`.
The DLL is installed as before (`<DD>\dinput8.dll`); a locked file is renamed aside, never deleted.

What is different from the hook of this morning, in every run:

- `CreateFileA` / `CreateFileW` are wrapped even with `[Expansion] Enable=0` (they change nothing then;
  the Steam guard has to see which level archive is opened). Line: `steam: CreateFileA yes, CreateFileW
  yes wrapped to see which level archive is opened (no redirect: [Expansion] is off)`.
- One more import slot is wrapped: `steam_api.SteamUserStats` (0xb107c8; range checker: 0 checks, like
  the other import slots, but this one has NOT run in a session yet - check S1).
- A TEST build blocks every Steam write, always. A TEST build still defaults to `SessionSafe=1`.
- `debug\log.py` / `triage.py` now also show `steam:`, `session: ... SESSION END` and `join:` lines.

## 2. Lines every run must show at start (both builds)

```
build: TEST (klauto), ...            (or: build: SHIP, ...)
core: 2 import slot(s) wrapped (ExitProcess yes, SteamAPI_RunCallbacks yes); EndOnFatal=1
steam: import SteamUserStats wrapped (1 slot): ISteamUserStats 007 proxy, 30 slots, 9 writes gated; policy: TEST build - every leaderboard upload, stat and achievement write is BLOCKED, on every level
        (SHIP: ...; policy: writes are BLOCKED on a level that is not the stock level of its slot (klstock.h); stats stay blocked until restart once such a level ran)
```

**If the log shows `steam: NOT GUARDED - ...` the guard is not there: treat the run as unguarded
(`re/leaderboard.md` 4.1: never let a session end) and report the line.** Causes it names: steam_api.dll
without the text `STEAMUSERSTATS_INTERFACE_VERSION007`, the import not found, a real interface whose
table has no code at one of 30 slots.

Then, once the game first uses the interface (boot: `RequestCurrentStats`, 0x6ca980) and loads a level:

```
steam: the game asked for ISteamUserStats: real interface XXXXXXXX, 30 slots checked, proxy handed out
steam: level archive f01\f01_main.zip opened from <path>: NOT stock (321104553 bytes, directory hash 157f60a8; the stock archive has 217471616 bytes, 94c9f794)
steam: level 'SCENES\Locations\F01\F01_Main.gms': <why> - leaderboard upload BLOCKED, stats and achievements BLOCKED
```

(size / hash are those of the build in the slot at 12:34; `<why>` is `TEST build: nothing is written to
Steam` in TEST and `its archive f01\f01_main.zip is not the stock one: ...` in SHIP.) Other archives the
game only probes (F05, F08, F09 at boot) give `... opened from ...: STOCK (...)` lines; `Patch01.zip
opened from ... holds menu files only` is the stock patch archive.

## 3. Live checks, one variable per run

Run `python debug\zombies.py --count` before and after each, as before.

**S0 - the guard at boot (direct boot, TEST DLL, the ini and slot build of the last good run).**
Variable: the new DLL. Expect the lines of section 2, no `patch REFUSED` line that names SteamUserStats,
no `INTEGRITY EXIT`, and the same `RESULT` as the last run with the old DLL.

**S1 - the import slot in a real session (TEST DLL + `klhook\KLHook.round.ini`, menu route, one round,
ended by `pass` at the score page as always).** Variable: a session with 0xb107c8 wrapped. Expect: the
round starts and reaches the score page; `session: state 0x.. -> 0x..` lines (plain state changes, at
most 400); the score page's friends rows as before (reads are forwarded); no `INTEGRITY EXIT`; no fault.
This is the anti-tamper test of the slot.

**S2 - the block itself (only after S0 and S1; TEST DLL; Retomoto or the bank in the slot; stand still
and die three rounds with $0, or Quit from the pause menu).** Variable: the session ENDS. Expect, in
this order:

```
session: state 0x.. -> 0x28 (game mode 4) = SESSION END: the game now uploads the session total and commits stats and achievements; Steam writes: BLOCKED - TEST build: nothing is written to Steam
steam: BLOCKED SetStat('NumRoundsPlayed', N) - TEST build: nothing is written to Steam          (one line per stat name, up to 27)
steam: BLOCKED StoreStats() - TEST build: nothing is written to Steam
steam: BLOCKED UploadLeaderboardScore(board 'KL2_Heist0_TotalMoney', keep best, score N) - TEST build: nothing is written to Steam
```

(the order of the three groups is the game's and was not observed; `SetAchievement('...')` lines may
come too.) Also expect: no `steam: passed on` line for any of them; `C:\Steam\appcache\stats\
UserGameStats_1165402018_28000.bin` still dated 2026-03-13; no fault in the handler that follows
(`re/leaderboard.md` 4.2: 0x5e8b0e tolerates a failed task). When the game leaves through ExitProcess
(not after klauto's `pass` / `quit`, which end the process directly): `steam: at exit: 1 leaderboard
upload(s) and N stat / achievement write(s) blocked; 0 and 0 passed on`.
Why $0 and standing still: should the block fail against everything tested off-game, a keep-best upload
of 0 changes no board; the stats would still have moved (three rounds played) - that is the residual risk
of this check and the reason it comes last. Do NOT run S2 if S0 or S1 showed `NOT GUARDED` or lacked the
`proxy handed out` line.

**S3 - SHIP policy on a level that is not stock (SHIP DLL, three-line ini, direct boot, current slot).**
Variable: the SHIP build. Expect `steam: level archive f01\f01_main.zip opened from ...: NOT stock (...)`
and `steam: level '...F01_Main.gms': its archive f01\f01_main.zip is not the stock one: ... - leaderboard
upload BLOCKED, stats and achievements BLOCKED`.

**S4 - SHIP policy on a stock level (SHIP DLL; a stock map through the menu, e.g. entry 1 = F02; kill
the process in the round).** Expect `steam: level archive f02\f02_main.zip opened from ...: STOCK
(196125170 bytes, directory hash c30281d3)` and `steam: level 'SCENES\Locations\F02\F02_Main.gms': stock
level - leaderboard upload allowed, stats and achievements allowed`. **Never let a scripted session END
here: on a stock level the SHIP build lets the writes through, by design.**

**J1 - the join from inside the process (TEST DLL; Retomoto `--no-ai` build in the slot;
`KLJoin.ini` beside the archive; h-live's RT4 walk to the car, WITHOUT the outside script `jt.py`).**
Variable: who writes the request. Expect:

```
join: reading <DD>\Scenes\Locations\F01\KLJoin.ini for level f01\f01_main
join: box 9: (2802, 19560, 789) - (3142, 19860, 1029) -> entry 5, name '06_Exit', target (6272, 563, -6305)
join: 1 box(es) from <DD>\Scenes\Locations\F01\KLJoin.ini for level f01\f01_main
join: level 'SCENES\Locations\F01\F01_Main.gms': 1 box(es) active; jump list has 6 entries
join: box 9 -> entry 5 '<name ending in 06_Exit>' at (6272, 563, -6305)
join: player 0 entered box 9 at (x, y, z): jump to entry 5 '...06_Exit' requested ([gamedata+0x8d4] = 5, [0x156b358] = 1)
join: player 0 is at (about 6272, 563, -6305) 500 ms after the request
```

(boxes of a level's own file are numbered from 9; 1..8 are KLHook.ini's.) `pos tick` lines must show the
lobby car afterwards and the walk must go on. If instead: `join: box 9 NOT usable on this level: <why>`
- the jump list differs from RT4's (the line says how: name, position or length); `join: ... ignored:
the archive beside it is the stock ...` - the slot holds stock F01; no `join:` line at all - no
`KLJoin.ini` in the folder the archive was opened from (the `steam: level archive ... opened from <path>`
line shows that folder).

**J2 - the join in a real session (J1 through the menu route, `KLHook.round.ini` head + the walk).**
Variable: a session. Expect J1's lines and no `INTEGRITY EXIT` in the 60 s after the jump (the request
dword is `.data`, 0 checks; the entry index is heap).

**J3 (optional) - a stale file.** The bank build in the slot with Retomoto's `KLJoin.ini` left beside
it: expect `join: box 9 NOT usable on this level: ...` and no jump anywhere on the map.

## 4. Keys

```
[Steam]   Block=1 (SHIP: 2 = block always; there is no off)   Log=1 (2 = every call)   State=1 (session lines)
[KLHook]  Join=0 switches every jump box off
[Join] / [Join.2] .. [Join.8] in KLHook.ini, or the same sections in KLJoin.ini beside the level archive:
          Min=x y z   Max=x y z   Entry=n   Name=text   Target=x y z   Tolerance=8   Scene=text (KLHook.ini only)
```

## 5. Not covered

- The local high-score list on disk (`re/leaderboard.md` 4.3: slot's top-12 in the profile) is NOT
  guarded; on the klauto route the profile is never loaded, so nothing is saved there.
- `FindOrCreateLeaderboard` is forwarded: an expansion map's score page shows the stock map's rows.
- The join moves this machine's local players only; a peer needs the hook and the file too.
