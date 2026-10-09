# KLHook for the live agent: which DLL, which ini, what each check expects

STATE 2026-10-09 16:35 (agent j-hook, offline). Three builds exist:

- **`ihook` (12:49)** and **`jhook` (15:16)** - both HAVE RUN LIVE (agent i-live, 30 runs; logs in
  `<work>\build\klhook\live\`). Section 3 says what was seen. They sit in the agents' scratch folder and are not
  needed any more, except `jhook\test` for check MPa below.
- **`<work>\build\klhook\ship` and `\test` (16:32)** - the same plus the fixes those runs asked for (section 2).
  BUILT, off-game batteries passed (34 of 34 mode runs, 12 klauto modes), **NOT RUN LIVE**. Nothing was installed
  into Dog Days and the game was not started by me. Use these from now on.

Sources: `klhook/` (`klhook.c` includes `klfix.c kljoin.c klsteam.c klslot.c` and, for TEST, `klauto.c`). Design
and evidence are in the top comments of `klslot.c`, `klsteam.c`, `kljoin.c` and in `mkoverlay.py`'s docstring; this
note is only what a live run needs.

## 1. Files - a fixed place, no scratch path

`<work>` = `tools\kl_port_check.workdir()` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools`.

| what | where |
|---|---|
| SHIP | `<work>\build\klhook\ship\` : `dinput8.dll` (192,512 bytes), `dinput8.dll.sha1`, `KLHook.ini` (= `klhook\KLHook.ini`: expansion off), `READ ME.txt` (for the owner; written by hand, not by the build) |
| TEST | `<work>\build\klhook\test\` : `dinput8.dll` (242,688 bytes), `dinput8.dll.sha1`, `KLHook.ini` (the same plain sample: no script), `KLHook.round.ini` (the scripted bank round) |
| which build | the first word of `dinput8.dll.sha1` is the DLL's sha1; the line also says SHIP / TEST, when and from which source folder. At the time of writing: SHIP `3f3f4f00a015116c83ec9d0dc44e9364ea84cedb`, TEST `0d638ec797476b298129c1bfbaf5e6eae2eaaa10` (both 16:32). A rebuild changes the hash (the build time is compiled in): trust the file, not this table |
| rebuild | `klhook\build.bat --work` (SHIP), `klhook\build_auto.bat --work` (TEST). They compile, delete the compiler's by-products, write the sha1 file and copy the ini(s); other files in the folder are left alone. The work folder comes from `KL_WORK` if set, else from `python klhook\workdir.py`. `build.bat <folder>` / `build_auto.bat <folder>` still build into any folder as before (only the DLL; `tools\kl_expansion.py` uses that form) |
| test inis of this pass | `<work>\research\agent_scripts\j-hook\MP2.ini`, `MP3.ini` |
| menu overlay | `python klhook\mkoverlay.py <KLHook.ini of the run> "<DD>\Patch01.zip" "<DD>\KLExpansion"` -> `<DD>\KLExpansion\Overlay\Patch01.zip`. **Rebuild it with the mkoverlay.py of this pass before any menu-page run** (the old one's page cannot work, section 2) |
| Retomoto's join | `klhook\KLJoin.retomoto.ini` as `KLJoin.ini` beside the level archive that is opened (unchanged) |

A run: `python tools\kl_autotest.py ... --hook "<work>\build\klhook\test" --ini <ini>` (it swaps the DLL in and puts
the original back; a locked file is renamed aside, never deleted).

**Rule for every scripted run that may reach a score page: the DLL must be a TEST build of klhook and the log must
show `steam: import SteamUserStats wrapped`.** Run S2 showed why: at a session end the game sends 29 stats as
ABSOLUTE totals from the profile block in memory, and the klauto route (DisableSplashScreens) never loads a
profile - everything but NumRoundsPlayed was 0. Unguarded, that overwrites the owner's Steam totals with zeros.
The owner's installed dinput8.dll and a SHIP build do not block a stock level.

## 2. What the 16:32 build changes (each from a live observation)

| seen live | cause (how established) | change | where |
|---|---|---|---|
| MP1: `menu page option is 2` with HeistPlayMenu2 open, but at StartGame `slot F01: menu page 0 from now on -> the stock level`; the archive came from the slot | the page was carried in the menu option `Dummy`, a field of the options object `[0x154d5f4]`. That object is deleted in the menu manager's destructor (kl2 0x673340) and the global is zeroed again in its constructor (0x617701); the game data object `[0xdd265c]` builds new managers (0x553d06, 0x553d38). Read in the disassembly; seen live only as 2 -> 0. StartGame itself never reads `Dummy` (0x502b40 -> 0x746570 -> 0x7e01a0: selector value -> slot -> scene name) | the page is read off the **window stack**: `HeistPlayMenu<N>` anywhere in it latches page N, the stock `HeistPlayMenu` page 1. Kept while there is no menu (the load), in a level and through the session; dropped when the frontend has shown a stack without a map page for 1 s and no StartGame / session-state change was seen in the last 10 s. Reads only, no call into the game, no new write site (`ceg_ranges.py`: the byte 0x156b73a 0 checks; the code and vtables it compares are hashed and are only read) | `klslot.c` kls_menu_watch |
| MP1: the 'Location:' row of the new page is empty (no focus bar, no label, no map title); the picture and the arrows show | the game finds an element by NAME over all windows, first in the file wins (0x83faf0 -> 0x4fa730: one table, 5096 entries). The copied page had the stock names, so its title went to the stock page's `HeistChapterData` and its focus to the stock `HPMfb#01` - in a window that is not open. Read in the disassembly. NOT established: why the label was missing too | every element name of the copy gets the suffix `_P<N>`, references inside the copy follow; the gamepad's bottom frame is a copy of its template that names the page's own selector. **In a script: `sel HeistLevel_P2 ...`, `msg HeistLevel_P2 StartGame`** | `mkoverlay.py` |
| MP1: the sixth Arcade button has no icon and touches 'Back' | the first version added button and focus bar only; stock rows also have an icon element and a line, and Y 390 in that group is where 'Back' is | icon `Icon_Marketplace` (an entity the window does not use yet), line `Line_Short_01#07`, and the group of all rows moved up by 34 per added button (group Y 110 -> 76) | `mkoverlay.py` |
| MP1: the new entry 'Withdrawal' shows Subway's picture | the entry kept the stock Arcade picture of its slot | default now the story-mode picture `LevelPicture_L0<slot>` (stock entity, same template). NOT VIEWED what each shows; `<slot>.Picture=` chooses, `Pictures=slot` gives the old behaviour. Dead Men's own pictures need the frontend-scene graft (not started) | `mkoverlay.py` |
| X1j: the first level line of a direct boot said `... was not seen being opened - leaderboard upload BLOCKED, stats and achievements allowed` for 0.5 s | only the LOG line: it printed the 'until restart' mark instead of asking the policy; a write in that window was blocked (a level whose archive was not seen blocks both kinds) | the line asks the policy for both halves. And one real gap closed: from the MENU the archive is opened while the scene name is still the frontend's, where the LAST level's verdict decided - now every write is blocked from the open of an archive that is not stock until its scene is up | `klsteam.c` |
| J3s: the bank with Retomoto's KLJoin.ini beside it: no jump, but also no `NOT usable` line | the bank has no jump point: an empty list was never described | once a local player exists and the list has stood still: `join: level '...': 1 box(es) active but the jump list is EMPTY ...` and `join: box 9 NOT usable on this level: the jump list is empty ...` | `kljoin.c` |
| - | - | `debug\log.py` lists the page lines (kind PAGE) and the empty-list line | `debug\log.py` |

Unchanged from 15:16 and seen live there: the fatal-fault filter, the exit line, StockRows, the session line order,
the join.

## 3. Seen live so far (12:49 and 15:16 builds; do not repeat unless something changes)

| check | run | result |
|---|---|---|
| S0 the guard at boot, direct boot | S0 | wrapper lines, `level archive f01\f01_main.zip ... NOT stock`; PASS |
| S1 import slot 0xb107c8 in a real session | S1, then S2 HK3 J2 J3 S5 N0 N0b ... | no `INTEGRITY EXIT` in eleven sessions; `proxy handed out` at the first score page (state 0x20) |
| S2 a session that ENDS | S2 | 29 `BLOCKED SetStat`, `BLOCKED StoreStats()`, `BLOCKED UploadLeaderboardScore(board 'KL2_Heist0_TotalMoney', keep best, score 0)`, `SESSION END`; Steam's cache file unchanged (date and sha1) after all 30 runs |
| S4t the SHIP policy on a stock level, through a TEST build | S4tb | F02 `STOCK (196125170 bytes, directory hash c30281d3)`, `under the SHIP policy: stock level - ... would be allowed` |
| S5 `[Steam] StockRows=0` | S5 | `BLOCKED FindOrCreateLeaderboard`, score page without rows, Ready, round 2, no fault |
| X1 SHIP build, direct boot, AutoExit | X1j | `fatal-fault filter: the game's own is kl2.exe+0x50b780`; `exit: exit(0)` - AutoExit leaves through MSVCR90 exit |
| HK4 a fatal fault under SHIP | HK4j | `FATAL`, KLHook_1.dmp, the game's mdmp (210,840 bytes), `process ended here`, no Windows error entry, zombies count unchanged. The fault was a thread started from outside at address 1, not a main-thread fault |
| HK3 `Hooks=1` under SessionSafe | HK3 | 13 `patch REFUSED`, 5 detours, round starts and ends |
| N0 the join with the settle time | N0, N0b (and J1b J2 J3 before) | `entered box 9 at (2718..2720, 19601, 1099)`, at `(6408..6411, 570, -6221)` 500 ms later; five of five |
| MP1 the menu page, first version | MP1 | overlay Patch01.zip taken; sixth button; HeistPlayMenu2 opens with its headline; option set. Faults: section 2 |
| session states | all | 0x0 (frontend) 0x12 0x15 0x16 0x18 0x19 (round runs) 0x1f 0x20 (score page) 0x23..0x26 0x16 ...; 0x1f -> 0x28 = session end |

Not run so far: S2b (line order at a session end with a build that has the fix), a fatal fault on the game's own main
thread, a stale KLJoin.ini with the new line (J3k below), anything of section 2.

## 4. Lines every run must show at start (16:32 build)

```
build: TEST (klauto), Oct  9 2026 16:32:5x; exe is kl2.exe build 0490; patch policy: session (nothing inside a hashed range)
        (or: build: SHIP, ...; patch policy: ship (import slots and data only))
core: 2 more import slot(s) wrapped for the exit line (MSVCR90 exit yes, _exit yes)
core: 2 import slot(s) wrapped (ExitProcess yes, SteamAPI_RunCallbacks yes); EndOnFatal=1
steam: import SteamUserStats wrapped (1 slot): ISteamUserStats 007 proxy, 30 slots, 9 writes gated; policy: TEST build - every leaderboard upload, stat and achievement write is BLOCKED, on every level
        (SHIP: ...; policy: writes are BLOCKED on a level that is not the stock level of its slot (klstock.h); stats stay blocked until restart once such a level ran)
steam: CreateFileA yes, CreateFileW yes wrapped to see which level archive is opened (no redirect: [Expansion] is off)
        (with [Expansion] Enable=1 instead: expansion: enabled; root ...   and   expansion: 5 import(s) of the exe wrapped (...))
```

A SHIP build, or a TEST build with `[Auto] Enable=0`, also shows
`fatal-fault filter: the game's own is kl2.exe+0x50b780 (read from its start-up code); it is called after ours has logged`.

**If the log shows `steam: NOT GUARDED - ...` the guard is not there: end the run before any score page and report
the line.**

When a level loads (TEST build; size / hash are those of the bank build that was in the slot at 15:58):

```
steam: level archive f01\f01_main.zip opened from SCENES\Locations\F01\F01_Main.zip: NOT stock (321104553 bytes, directory hash 6b9f8df2; the stock archive has 217471616 bytes, 94c9f794)
steam: level 'SCENES\Locations\F01\F01_Main.gms': TEST build: nothing is written to Steam - leaderboard upload BLOCKED, stats and achievements BLOCKED
steam: level 'SCENES\Locations\F01\F01_Main.gms' under the SHIP policy: its archive f01\f01_main.zip is not the stock one: 321104553 bytes, directory hash 6b9f8df2; the stock archive has 217471616 bytes, 94c9f794 - leaderboard upload would be BLOCKED, stats and achievements would be BLOCKED
```

On a DIRECT BOOT the scene name comes about half a second before the archive, first as
`'SCENES\Locations/F01/F01_Main.gms'`: the first pair of `level` lines then says `its archive f01\f01_main.zip was
not seen being opened - ... BLOCKED, stats and achievements BLOCKED` (TEST: `would be BLOCKED ... would be BLOCKED`
in the SHIP-policy line), and a second pair with the archive's verdict follows. **`stats and achievements allowed`
(or `would be allowed`) behind `was not seen being opened` must not appear any more.**

## 5. Live checks for the 16:32 build, one variable per run

Run `python debug\zombies.py --count` before and after each, as before. The slot build, `KLExpansion\Maps\DM03` and
the walk are those of run MP1 unless a check says otherwise.

**MPa - the new overlay, OLD hook (TEST DLL from scratch `jhook\test`, sha1 60e345a4; ini
`<work>\research\agent_scripts\j-hook\MP2.ini`; overlay rebuilt by `mkoverlay.py` from that ini; shots every 3 s
from the open of HeistModeMenu).** Variable: the overlay. This run is about what the PAGE looks like; the load is
expected to go wrong exactly as in MP1 (the old hook). Expect on the pictures:

- Arcade page: six rows, all one row higher than in `MP1_36s.png`; the sixth row 'Dead Men maps' with an icon at
  its left like the five above and a thin line under it; a clear gap between it and 'Back'. Five DOWN from the
  open still reach it (if not: say which key does).
- HeistPlayMenu2: the focus bar across the row as on the stock page (`S4t_100s.png`), with `Location:` at the left
  and `Withdrawal` between the arrows; a picture that is NOT the subway; no briefing text at the right;
  'Your Criminal name' as before.

and in the log:

```
windows: 3 [MainMenu > HeistModeMenu > HeistPlayMenu2]
script 27: HeistLevel_P2 is at 0 after 0 step(s)
msg: 'StartGame' -> ZMercsLevelSelectorHeist 'HeistLevel_P2' at ...
expansion: slot F01: menu page 0 from now on -> the stock level          <- the OLD hook; this is what MP2 changes
```

If `sel HeistLevel_P2` / `msg HeistLevel_P2` fails ('not found') the renamed selector is not there: report the
line; the page is then no better than MP1's. If the row is still empty although the names are the page's own, the
by-name look-up is not the (whole) cause: send a shot and the `windows` / `focus` lines.

**MP2 - the latch (TEST DLL from `<work>\build\klhook\test`; everything else as MPa).** Variable: the DLL.
Expect, in this order:

```
expansion: [Redirect.2] Scenes\Locations\F01\ -> C:\...\KLExpansion\Maps\DM03\
expansion: menu page 2 is 'Dead Men maps'
expansion: 5 import(s) of the exe wrapped (...); 1 redirect rule(s) for 1 slot(s); 0 slot name(s)
expansion: CreateFileA overlay: C:\...\Patch01.zip -> C:\...\KLExpansion\Overlay\Patch01.zip
expansion: menu windows [MainMenu > CampaignMenu] - no map page                       (Log=2 lines, one per change of the stack)
expansion: menu windows [MainMenu > HeistModeMenu] - no map page
expansion: menu windows [MainMenu > HeistModeMenu > HeistPlayMenu2]
expansion: menu page 2 latched: window 'HeistPlayMenu2' is open ([Redirect.2] F01=DM03)     <- within a frame of klauto's 'windows: 3 [...]'
expansion: menu option 'Dummy' reads 2 (information only: the page is taken from the window stack)
msg: 'StartGame' -> ZMercsLevelSelectorHeist 'HeistLevel_P2' at ...
session: state 0x0 -> 0x12 (game mode 4)
expansion: slot F01: menu page 2 from now on -> DM03
expansion: CreateFileA redirect: C:\...\SCENES\Locations\F01\F01_Main.zip -> C:\...\KLExpansion\Maps\DM03\F01_Main.zip
steam: level archive f01\f01_main.zip opened from C:\...\KLExpansion\Maps\DM03\F01_Main.zip: NOT stock (321100626 bytes, ...)
```

then `redirect:` lines for the `_LS` files, the `.WHD` and the `.WAV`, the level loads, RESULT PASS. Must NOT
show before the `slot F01: menu page 2` line: `expansion: menu page 2 dropped`, `slot F01: menu page 0 from now on`,
`the menu's window system at ... has vtable` (that line means the stack cannot be read on this exe: report it).
If `menu page 2 dropped: the frontend shows [...]` does come between StartGame and the archive: the line shows the
stack that was seen, and the times of the `msg:` and `session:` lines say how long the frontend stood - send the
three; `[Expansion] Page=2` is then the stop-gap for further page runs.
`menu option 'Dummy' reads 0` right after the `session:` line is expected (that is the MP1 finding).

**MP3 - the page does not stick (TEST DLL; ini `...\j-hook\MP3.ini`: opens HeistPlayMenu2, Back, opens the stock
HeistPlayMenu, starts entry 0).** Variable: the route. Expect:

```
expansion: menu page 2 latched: window 'HeistPlayMenu2' is open ([Redirect.2] F01=DM03)
expansion: menu page 1 latched: window 'HeistPlayMenu' is open (the stock map page: [Redirect] only)
msg: 'StartGame' -> ZMercsLevelSelectorHeist 'HeistLevel' at ...
expansion: slot F01: menu page 1 from now on -> the stock level
steam: level archive f01\f01_main.zip opened from SCENES\Locations\F01\F01_Main.zip: NOT stock (321104553 bytes, ...)      <- the SLOT's file
```

(`menu page 2 dropped: the frontend shows [MainMenu > HeistModeMenu]` may come between the two latch lines if the
script waits longer than a second on the Arcade page; both orders are right.) This is also the old hook check 8.

**MP4 (optional, long) - the page after a session (TEST DLL; MP2's start, then S2's 'stand still, three lost
rounds').** Variable: the session's end. Expect the level archive opened from `Maps\DM03` at EVERY round start
(`slot F01: menu page 2` is said once; the `level archive ... opened from ...Maps\DM03...` lines repeat), the S2
lines at the end, the frontend with `windows: 2 [MainMenu > HeistModeMenu]`, and about 10 s later
`expansion: menu page 2 dropped: the frontend shows [MainMenu > HeistModeMenu] ...`.

**X1k - SHIP build, direct boot (SHIP DLL from `<work>\build\klhook\ship`, its KLHook.ini; X1j again).**
Variable: the DLL. Expect the section 4 lines with `build: SHIP`, then

```
steam: level 'SCENES\Locations/F01/F01_Main.gms': its archive f01\f01_main.zip was not seen being opened - leaderboard upload BLOCKED, stats and achievements BLOCKED
steam: level archive f01\f01_main.zip opened from SCENES\Locations\F01\F01_Main.zip: NOT stock (...)
steam: level 'SCENES\Locations\F01\F01_Main.gms': its archive f01\f01_main.zip is not the stock one: ... - leaderboard upload BLOCKED, stats and achievements BLOCKED
exit: exit(0)
```

**J3k - a stale KLJoin.ini (TEST DLL; J3s again: the bank in the slot, Retomoto's KLJoin.ini beside it).**
Variable: the DLL. Expect, a moment after `players: 16 ZFFPlayer object(s) found`:

```
join: level 'SCENES\Locations\F01\F01_Main.gms': 1 box(es) active but the jump list is EMPTY - the level has no ZJumpPoint
join: box 9 NOT usable on this level: the jump list is empty (a KLJoin.ini of another level beside this archive?)
```

each once, and no `join: player` line. (If instead `jump list has N entries` and `box 9 NOT usable ...: entry 5 is
past the end ...` come, the bank has jump points after all and the old code would have said so too: report N.)

**N0k (optional) - the join still works (TEST DLL; N0's set-up).** Expect N0's lines unchanged.

Still open from the 15:16 list, unchanged: **S2b** (SESSION END before the BLOCKED lines), **HK4** with a fault on
the game's own main thread. **Never let a SHIP build or the owner's hook end a scripted session on a stock level:
there the writes go through, by design.**

## 6. Keys

```
[KLHook]     ExitLog=1 (ExitProcess, exit, _exit)   Tick=1   EndOnFatal=1   LbFix=1   SessionSafe=1 (TEST)   Join=1
[Expansion]  Enable=0   Root=KLExpansion   Overlay=1   Fallback=1   Log=1 (2 = also every open, the menu's window
             stack at each change, the option 'Dummy')   Page=-1 (0..9 = that page always: direct-boot tests)
[Redirect]   F01=<folder under KLExpansion\Maps>            every page
[Redirect.N] the same for menu page N (2..9; mkoverlay.py builds buttons for 2..5)
[Page.N]     Title=   Icon=   Pictures=story|slot   F01=<entry title>   F01.Picture=<LevelPicture_* entity>     (mkoverlay.py)
[Steam]      Block=1 (SHIP: 2 = block always; there is no off; TEST always blocks)
             Log=1 (2 = every call, 0 = none)   State=1 (session lines)   StockRows=1 (0 = no stock rows, seen in S5)
[Join] / [Join.2] .. [Join.8] in KLHook.ini, or the same sections in KLJoin.ini beside the level archive:
             Min=x y z   Max=x y z   Entry=n   Name=text   Target=x y z   Tolerance=8   Scene=text (KLHook.ini only)
```

Boxes of a level's own file are numbered from 9; 1..8 are KLHook.ini's.

## 7. Not covered

- The local high-score list on disk (`re/leaderboard.md` 4.3) is NOT guarded: a player who starts an expansion map
  from the real menu gets its score into the stock slot's LOCAL list. Not Steam.
- With `StockRows=1` (default) an expansion map's score page shows the stock map's friends rows.
- The lobby title, the briefing and the tags `IsHeistLevelAvailable` / `HeistBriefing` belong to the stock map of the
  slot; the new page has no briefing element. `IsHeistLevelAvailable` is computed only while the window named
  `HeistPlayMenu` is open (0x436ca2), so the new page never shows 'not available' for a locked DLL slot - the
  selector itself still skips such a slot.
- The page latch covers the Arcade route (HeistPlayMenu<N>). A Fragile Alliance lobby has no page: it loads what
  `[Redirect]` gives. A load that starts within 10 s of a session-state change without any map page having been
  opened would still use a page latched before - no such route is known (after an Arcade session the game opens
  the Arcade page, from which a load needs a map page).
- The gamepad layout of the new page (its own template copy) has not been seen: no run used a gamepad.
- The menu's element table (5096): a page adds 54 `<GuiElement>` tags plus one template; headroom not established.
- The join moves this machine's local players only: a peer needs the hook and the same KLJoin.ini.
- A SHIP build blocks stats from the first non-stock level until the process ends (by design; ASSUMPTION that the
  game re-reads the block from Steam at every normal boot, `ZAsyncTaskReadProfileSteam` 0x46f5a0).
