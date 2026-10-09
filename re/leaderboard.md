# Steam leaderboards, stats and achievements: what Arcade writes, and whether the test rounds wrote

Written 2026-10-09 (agent h-board). Offline only: the game was not started, nothing was installed,
no network service was contacted. Material: kl2.exe read with `debug\dasm.py` / capstone, the hook
logs under `<work>\build\klhook\**\*.log` and `<DD>\KLHook.log`, and two files of the Steam client
read (not written): `C:\Steam\appcache\stats\UserGameStats_1165402018_28000.bin` and
`UserGameStatsSchema_28000.bin`.

Words: **read** = read off the disassembly (address given) or off a file; **INFERENCE** = follows
from what was read plus how Steam is documented to behave, not observed; **not established** = unknown.

## 0. Answers

1. **Did the test rounds upload to a public board? No** (read + log evidence, section 3).
   An Arcade session uploads exactly once, when the session ENDS: session state 0x28. That state is
   entered from one place, `ZGameRulesHeist` slot 82 (0x4f9f90), and only when the lives byte is
   <= 0 - after the round that costs the last life, or when the player picks Quit in the pause menu
   (`ZGUIOQuitGame` zeroes the lives and ends the round). A round end with lives left (death with
   lives left, clock, **escape**) goes to state 0x20 and uploads nothing.
   Every logged test process saw at most ONE round end and was then killed by klauto
   (`TerminateProcess`) or left by AutoExit; none opened the pause menu. ESC3 ($723,625, escaped)
   was killed 46 s into round 2. So state 0x28 was never reached and
   `UploadLeaderboardScore` was never called.
2. **Stats and achievements: not changed either.** The same state-0x28 handler is the only Arcade
   caller of the stats commit (`SetStat` x 27 + `StoreStats`). Steam's local stats cache of the
   owner's account was last written 2026-03-13 and holds `PendingChanges = 0`; the newest
   achievement time in it is from December 2021 (read; that the client rewrites this file on every
   `StoreStats` / `SetAchievement` is INFERENCE).
3. **But the danger is real and close.** Three failed rounds in one process, or one Quit from the
   pause menu, on a grafted map in the F01 slot would: upload the session total to the public board
   `KL2_Heist0_TotalMoney` (Subway) with keep-best, add the session's money / kills / rounds to the
   owner's public Fragile Alliance stats **including `ExperiencePoints_FA` (the multiplayer rank)**,
   and evaluate achievements. None of this path looks at the 'profile loaded' byte 0x156b742 that
   keeps the local save untouched on the klauto route.
4. **What the test rounds did do on Steam:** read only. The score page (`HeistStatusLeaderboard`)
   calls `FindOrCreateLeaderboard("KL2_Heist0_TotalMoney", 2, 1)` and
   `DownloadLeaderboardEntries(friends)`. The board exists, so nothing is created.
5. **Fix** (section 4): wrap the import `steam_api.SteamUserStats` (IAT slot 0xb107c8, not hashed)
   and hand the game a proxy interface whose write methods fail. Until that is in the hook, the rule
   for live runs is section 4.1: **never let a session end; always kill the process.**

## 1. Every use of ISteamUserStats in kl2.exe (read)

The import slot 0xb107c8 is referenced at 14 places in 11 functions (byte search for the slot
address in `.text`; each place calls the import afresh, nothing caches the interface pointer beyond
one function). Interface version `STEAMUSERSTATS_INTERFACE_VERSION007`. Vtable offsets used:

| offset | method (007 layout) | function | owner | what |
|---|---|---|---|---|
| +0x00 | RequestCurrentStats | 0x6ca980 | `ZAsyncTaskReadUserStatsSteam` ctor (service slot 81, 0x453930) | read |
| +0x08 | GetStat(int) | 0x46f5a0 | `ZAsyncTaskReadProfileSteam` slot 8 (service slot 29, 0x41fdf0) | read: profile <- Steam |
| **+0x10** | **SetStat(int)** | **0x555020** | `ZAsyncTaskWriteUserProfileSteam` slot 8 (service slot 30, 0x512740) | **write**, 27 names, then |
| **+0x28** | **StoreStats** | 0x555020 (0x55522c), 0x72fd60 | | **write** |
| +0x18 | GetAchievement | 0x8c17d0 | `ZAchievementInfoSteam` slot 4 | read |
| **+0x1c** | **SetAchievement** | **0x72fd60** | `ZAchievementsSteam` slot 3 | **write**, then StoreStats if it returned true |
| +0x50 | FindOrCreateLeaderboard(name, 2 = descending, 1 = numeric) | 0x789700 (download), **0x5ebe20 (upload)** | the two leaderboard tasks | finds the board |
| +0x5c | GetLeaderboardEntryCount | 0x7551e0, 0x827c60, 0x8aeb20 | `ZAsyncTaskLeaderboardReadSteam` | read |
| +0x68 | DownloadLeaderboardEntries | 0x7551e0 | call result of 0x789700 | read |
| +0x6c | GetDownloadedLeaderboardEntry | 0x8aeb20 | | read |
| **+0x70** | **UploadLeaderboardScore(h, 1 = KeepBest, score, 0, 0)** | **0x7ef400** | call result of 0x5ebe20, `ZAsyncTaskWriteLeaderboardStatsSteam` | **write** |

The offsets are self-consistent with the 007 header: the argument counts match
(`FindOrCreateLeaderboard` 3 args, `UploadLeaderboardScore` 6 dwords, `DownloadLeaderboardEntries`
5). `ResetAllStats`, `ClearAchievement`, `IndicateAchievementProgress`, `UpdateAvgRateStat` are
never called.

Board names: pointer table at 0xd36aa8 (`.data`), 13 entries: 0 `KL2_FA_TotalMoney`,
1 `KL2_UCC_TotalMoney`, 2 `KL2_TM_TotalMoney`, 3..11 `KL2_Heist0_TotalMoney` ..
`KL2_Heist8_TotalMoney`, 12 `KL2_HeistAllStats_TotalMoney`.

Stat names written by 0x555020, from the stats block of the profile (`0x4f0730(profile->slot 80)`):
`NumRoundsPlayed` +4, `NumRoundsEscapedAsMercOrTraitor` +8, `NumRoundsEscapedAsTraitor` +0xc,
`MPModesPlayed` +0x10, `NumKilled` +0x14, `NumKilledMercs` +0x18, `NumAssists` +0x1c,
`NumKilledRogues` +0x20, `NumPersonalRevenge_FA` +0x2c, `NumTraitorsKilled_FA` +0x30,
`TotalRewardMoney` +0x38, `TotalLootMoney` +0x40, `BiggestGrab` +0x48, `HeistTotalPoints_0..8`
+0x4c + 4 * slot, `NumCompletedSessions_FA` +0x7c, `NumSessionsWon_CnR` +0x80,
`NumRoundsWonAsMerc_FA` +0x84, `NumRoundsWon_FA` +0x88, `MoneyEscapedWith_FA` +0x8c,
`ExperiencePoints_FA` +0x90 (word), `NewestAddedPointsAmount` +0x92 (word).
The schema file Steam holds for app 28000 defines stats 4..22 = the names above from
`NumRoundsPlayed` to `ExperiencePoints_FA`; it has **no** `HeistTotalPoints_*` and no
`NewestAddedPointsAmount` (read), so those `SetStat` calls fail on Steam's side (INFERENCE).

## 2. Which moments reach the writes (read)

### 2.1 The upload: `ZLeaderBoardServiceSteam` slot 1 (0x4b3bd0)

```
4b3c10  if 0x7f6850(session)            ; "is Arcade": session+0x54 (net state) not 2 / 3 and session+0x5c (game mode) == 4
4b3c1f      slot = byte [session+0xbe]  ; 0x464b70, the level slot chosen in the menu
4b3c2b      n = 0x80c9f0(slot)          ; fixed map {0,1,2,3,6,4,5,7,8}; -1 / > 9 -> garbage or -1
4b3c33      board = 3 + n  (n 0..8)     ; anything else -> board 3 = KL2_Heist0 = SUBWAY
4b3c90  else board = [0x168e59c]  (0 FA, 1 UCC, 2 TM; other values: no upload, dummy task 0x494fb0)
4b3d2a  score = [arg] + [arg+4]
4b3d3f  0x5ebe20(task, board, score, 0, 0) -> FindOrCreateLeaderboard(name[board], 2, 1)
7ef400  call result: if found and no IO failure -> UploadLeaderboardScore(h, 1, score, 0, 0)
        else task status = 3 (failed); the same when FindOrCreateLeaderboard returns handle 0 (5ebe77)
```

Slot 1 has two callers (search: every `+0x13c` service fetch followed by a call through `[vt+4]`):

- **0x68aa50**, called only from `ZGameRulesHeist` slot 6 (0x5e8570, "session state entered") in the
  case for **state 0x28** (0x5e8966; jump tables 0x5e8d9c / 0x5e8d78 decoded). Unconditional there.
  Inside: the online service (`session->slot 11`) must be non-null, and
  `score = [[rules+0x5f8]+0x38]` = the session's banked total (each round end adds the round's
  `+0x30` to it: 0x5e001b, 0x41870b). Slot index 0 on the Subway entry -> **`KL2_Heist0_TotalMoney`**.
- 0x65d950, called from `ZGameRulesFragileAlliance` slot 6 (0x7a9060): online Fragile Alliance /
  UCC / TM, per client, score = reward + loot. Not reached in Arcade (`ZGameRulesHeist` has its own
  slot 6 and does not call it).

**No profile test on the way.** The path does not read byte 0x156b742 (profile loaded, set by
`ZPressStart`), nor 0x1686e71, nor any 'ranked' flag. What it needs is: Arcade session, service
object present (it is - klauto's LbFix line prints its leaderboard service every run), and Steam
answering. `SteamUser()->BLoggedOn()` (0x4e87f0 / 0x698a30) gates only the top-10 download that
follows in the same handler (0x5e8a9d) and the achievement writer.

### 2.2 When is state 0x28 entered

State setter = session vtable +0x68 (0x74c080 -> 0x488e50, field session+0x70). Sites that pass
0x28 (three scans: `push 0x28` + virtual call, `mov [esp+4],0x28` + tail jump, raw bytes before
every `+0x68` fetch):

- **0x4fa2f2 in `ZGameRulesHeist` slot 82 (0x4f9f90) = end of round.** It banks the round, then
  `0x4fa0f7 cmp byte [state+0x6c], 0 ; setle` -> lives <= 0 ? **state 0x28** : state 0x20.
  (`state` = `[rules+0x5f8]`; `+0x6c` is the working lives count, `+0x44` the copy the HUD shows.)
- 0x6d3a10 in the scene-change command 0x6d36b0 (target scene `KaneAndLynch`), but only when the
  net state is 2 (`0x6db900` = net state <= 1 takes the direct-load branch instead). Arcade runs
  with net state 1 (`re/fa_round.md` section 2), so this is the online-host case, not Arcade.

Who makes lives <= 0:

- `ZGameRulesHeist` slot 192 (0x5dff40), the round clock / everybody-dead handler: when nobody
  escaped (`slot 0x1a8(0)` false) it does `dec byte [state+0x6c]` (0x5dfffd) and goes to state 0x1f,
  whose timer calls slot 82. So: **the round in which the last life is lost.**
- **`ZGUIOQuitGame` slot 10 (0x599a50) -> 0x418660: the pause menu's Quit.** On accept (message
  0x7f) in an Arcade session (0x599b24) it adds the running round to the total, writes
  `byte [state+0x6c] = 0` (0x418730) and calls slot 82 (`jmp [vt+0x148]`).
  So **quitting an Arcade session from the pause menu uploads what has been banked so far.**

What does NOT upload: a round end with lives left (death, clock or escape -> states 0x20, 0x21,
0x22 ... 0x25 score page ... next round); the process being killed; AutoExit (it sets the engine's
quit byte, no rules code runs - INFERENCE from `klauto.c`'s notes on 0x5c7203, not re-read here).

### 2.3 The same handler commits stats and achievements

State 0x28 handler, after the upload: `0x57e400` = `0x5e3250(0x156c108)` (achievement evaluation;
skipped when `[[0xdd265c]+0x8ad]` or `+0x8af` is set) and **`0x68b930(session, 1)`**:

```
68b96a  only when game mode == 4 and the online service exists
68b9e6  Arcade branch: stats.NumRoundsPlayed += round ; rounds escaped ; TotalRewardMoney += ... ;
        TotalLootMoney += ... ; BiggestGrab = max ; ExperiencePoints_FA += (0x76c260) ;
        HeistTotalPoints[slot] = max(old, [state+0x38]) ; insert into the LOCAL top-12 list of that
        slot (profile+0x1408 + slot*0x30, names at +0x10c) ; kills / assists counters
68be77  0x6587c0(profile, 0)             ; local save writer - returns at once while 0x156b742 == 0
68be82  if [[0xdd265c]+0x8ad] == 0:      ; (the flag that also makes the Arcade selector refuse to start)
68be91      service->slot 30(stats)      ; ZAsyncTaskWriteUserProfileSteam: SetStat x 27 + StoreStats
```

The Steam write at 0x68be91 is **outside** the 0x156b742 test: on the klauto route the local save
is skipped but the Steam stats are not.
Second caller of 0x68b930: 0x538810 <- 0x70a920 <- 0x56cc60, the receive stub of the client RMC
`AnnounceFARoundCompleted` (4 bools, int32, 3 bools - matches `re/netcode.md`), taken when
`bLastRound` is set: online Fragile Alliance. Whether an Arcade session ever sends that RMC to
itself is **not established** (the sender was not found); the state-0x28 path makes it moot.

Achievements outside the session end: `ZAchievementsSteam` (object 0x156c108) slot 3 (0x72fd60) is
`SetAchievement` + `StoreStats`, gated by `SteamUser()->BLoggedOn()` only. About twenty profile
counters test `achievements->slot 1()` and can reach it in the middle of play (kills, escapes,
round results: 0x432ec0, 0x4ce430, 0x622ea0, 0x64c350, 0x782e80, 0x802bc0, 0x861b30, 0x8fe280, and
0x84c410 at every round end through 0x8e40e0). Which thresholds exist was not read. So an
achievement can in principle unlock during any round, grafted map or not, without a session end.

## 3. The test rounds: did anything get written

Conditions of the runs: Arcade from `HeistModeMenu`, slot 0 (Subway entry), klauto route (no
`ZPressStart`, so 0x156b742 = 0), Steam running and online, account 76561199125667746
(= account id 1165402018; the id is on the stack of the RN11 dump, `re/crash_scorepage.md`).

Following 2.1 - 2.3 with those conditions: Arcade test true, service present, slot 0 -> board 3.
**If state 0x28 had been entered, the upload and the stats commit would have gone out** - nothing
on the path would have stopped them. So the whole question is whether state 0x28 was entered.

Evidence that it was not:

- **Logs.** Every klauto log that has window lines (41 processes across `build\klhook\**\*.log`
  and `<DD>\KLHook.log`, split at each `klauto: enabled` line) was tallied: 29 processes never
  showed the score page, 3 showed it once and ended there, 9 showed it once and went on into
  round 2 (`FAWaitForPlayers` once). **No process has a second round end**, and three are needed
  to lose three lives. The only windows ever seen are `MainMenu`, `MainMenu > CampaignMenu`,
  `MainMenu > HeistModeMenu`, `... > HeistPlayMenu`, `HeistStatusLeaderboard`, `FAWaitForPlayers`
  and `MissionFailedReload` (story runs) - **no pause menu**, so no Quit.
- Every run ends by `kla_finish` -> `TerminateProcess` (`klauto.c` 519 - 525) or by the game's own
  exit under AutoExit; neither runs rules code.
- ESC3: score page at 10:42:16 ('ROUND OVER - All surviving criminals escaped', lives left > 0 ->
  state 0x20 branch), Ready at 10:42:24, round 2 standing still, `RESULT PASS` and kill at
  10:43:10. The $723,625 lived in `[state+0x38]` of a process that was killed.
- **Steam's local stats cache** `UserGameStats_1165402018_28000.bin`: last written
  **2026-03-13 11:23**, `PendingChanges = 0`, crc set. Values (schema names from
  `UserGameStatsSchema_28000.bin`): NumRoundsPlayed 40, NumRoundsEscapedAsMercOrTraitor 17,
  NumKilled 289, TotalRewardMoney 3,269,732, TotalLootMoney 43,580,000, BiggestGrab 4,000,000,
  MoneyEscapedWith_FA 20,167,332, ExperiencePoints_FA 331; newest achievement time 1639259514
  (2021-12-11). The game did run under this account today (`userdata\1165402018\28000\
  remotecache.vdf` written 2026-10-09 11:07). INFERENCE: a `StoreStats` or `SetAchievement` during
  the tests would have rewritten this file; it did not happen.
  (A second, empty cache `UserGameStats_838861569_28000.bin`, 38 bytes, was written 2026-10-08
  14:19. Whose account id that is was not established; it holds no stats.)

Limits of that evidence: logs of runs that were overwritten are not covered; runs before klauto
logged windows (the direct `DefaultScene` boots) never were Arcade sessions at all - a level
started by `DefaultScene` has no game mode 4, so both 0x4b3bd0's Arcade branch and 0x68b930 are
closed (the `[0x168e59c]` branch of 0x4b3bd0 is reached only from the online rules).
Leaderboard entries are not cached on disk, so the board itself can only be checked by looking at
it: the Leaderboards page of the Arcade menu, or the game's community page (owner, in a browser).
Expected: the owner's Subway entry is whatever it was before 2026-10-08.

If it ever does happen: `UploadLeaderboardScore` is called with method 1 = keep best. A later
lower score does not replace the entry, and nothing in the game can lower or remove it (the game
never uses force-update and never deletes). Only a higher score from a real Subway session would
overwrite a grafted-map score. Removing an entry is in the hands of the game's publisher, not of a
client. Stats (`SetStat`) are plain overwrites by the game's own totals and cannot be rolled back
by the game either (`ResetAllStats` is never called and would wipe everything).

## 4. Keeping test rounds and expansion maps off the stock boards

Boundary (`re/antitamper.md`): import-table slots, `.data` and heap writes are not hashed; `.text`
and vtables in `.rdata` are.

### 4.1 Now, before any hook change (rule for live runs)

- **Never end a session normally.** No pause-menu Quit in Arcade; no script that plays a third
  failed round in one process. End every run with klauto's `pass` / `quit` (TerminateProcess).
- Losing lives is fine as long as the process dies before the last one is gone: one death =
  two skulls left (seen), so at most **two** failed rounds per process. Escapes do not cost a life.
- Cheap belt for klauto (data write, heap): while an Arcade session runs, keep
  `byte [[[[0x168e9e4]+0x54]+0x5f8]+0x6c] >= 1` (valid only when `[[0x168e598]+0x5c] == 4`; the
  chain is what 0x508ef0 returns). That closes the 'last life' door. It does **not** close the
  Quit door (0x418730 writes 0 and calls slot 82 in the same call) - hence the first rule.
- Useful log line: session state changes (`[[0x168e598]+0x70]`), with a loud line for 0x28.

Steam offline mode is not a full answer: leaderboard uploads fail offline, but `SetStat` /
`StoreStats` / `SetAchievement` are kept by the client and sent at the next sign-in (INFERENCE,
Steamworks behaviour; the `PendingChanges` field of the cache file is that queue). And the launch
/ Steam settings are not ours to change.

### 4.2 The mechanism: a proxy ISteamUserStats behind the import slot

One wrapper covers the board, the stats and the achievements, in the place the game itself treats
as fallible.

1. At hook start replace IAT slot **0xb107c8** (`steam_api.SteamUserStats`, inside the unhashed
   0xb10000-0xb107f8) with `klx_SteamUserStats`, exactly as klauto wraps ExitProcess.
2. `klx_SteamUserStats()` calls the real export. NULL -> return NULL. Otherwise, **if blocking is
   on**, return a proxy object: one dword pointing at a heap table of 30 entries (ASSUMPTION: the
   007 interface has 30 methods, +0x00 .. +0x74 `GetNumberOfCurrentPlayers`; the game uses none
   above +0x70, so a shorter real table could only matter to a caller that does not exist).
   If blocking is off, return the real pointer.
   Because the game calls the import again at every use, switching is immediate.
3. Proxy table entries (thunks in memory the hook allocates; `this` in ecx, callee cleans):

   | offset | method | thunk |
   |---|---|---|
   | +0x70 | UploadLeaderboardScore | `xor eax,eax ; xor edx,edx ; ret 0x18` -> handle 0 -> the game's own failure branch 0x7ef458 (task status 3) |
   | +0x0c, +0x10 | SetStat (float / int) | `xor al,al ; ret 8` (return value ignored at 0x555020) |
   | +0x28 | StoreStats | `xor al,al ; ret` |
   | +0x1c | SetAchievement | `xor al,al ; ret 4` -> 0x72fdb0 skips StoreStats |
   | +0x14, +0x20, +0x34, +0x4c | UpdateAvgRateStat, ClearAchievement, IndicateAchievementProgress, ResetAllStats | never called by the game; fail them too (`ret 0x10` / `ret 4` / `ret 0xc` / `ret 4`; argument sizes from the 007 header, not from game code) |
   | all others | reads | `mov ecx, <real this> ; jmp [<real vtable> + offset]` |
   | +0x50 | FindOrCreateLeaderboard | optional, see 4.3: `xor eax,eax ; xor edx,edx ; ret 0xc` makes the score page show no stock rows |

   The proxy never touches steam_api.dll or steamclient.dll memory and changes no byte of kl2.exe
   outside the IAT. ASSUMPTION to check on the first run: no anti-tamper range covers 0xb107c8
   (the range map says so; the ExitProcess / CreateFileA wrappers in the same table ran clean).
4. When is blocking on:
   - **klauto (tests): always**, ini key e.g. `[Auto] SteamWrites=0` (default 0). A test harness
     has no business writing the owner's profile, stock map or not.
   - **Shipped hook: whenever the level being played is not the stock level of its slot** - i.e.
     the slot redirect of `klslot.c` is active for the current session, or the scene path lies
     under the expansion folder. Decide at load start, hold until the next frontend load.
   - Log every blocked call once per session (name, score / stat), so a run shows what would have
     gone out.

Check that it works (first live run with the wrapper, one process): lose three rounds or Quit from
the pause menu on the grafted map; expect the log lines 'state 0x28', 'blocked
UploadLeaderboardScore(score)', 'blocked SetStat ...', 'blocked StoreStats'; expect the cache file
`UserGameStats_1165402018_28000.bin` to keep its date; expect no crash in the handler's top-10
read that follows (0x5e8b0e waits up to 4000 ms on a download task and tolerates failure: status
!= 1 -> skip).

Alternative without the import (data only): give the leaderboard service object
(`[[[0x168e598]+0x17c]+0x198]`, a heap object) a private copy of its vtable 0xbd5cc4 whose slot 1
returns the game's own dummy task (`new(4)` 0x89e850 + 0x494fb0, as 0x4b3ca4 does for 'no board';
`ret 0x24`). That stops the board upload only - stats and achievements would need the same trick
on the online service's slot 30 and on `ZAchievementsSteam` (whose vtable pointer sits in `.data`
at 0x156c108). The import wrapper is one place instead of three.

Not an option: pointing the names at 0xd36aa8 (`.data`, writable) to boards of our own -
`FindOrCreateLeaderboard` would then create public boards under the stock app id.

### 4.3 What the shipped expansion should do, by design

- A Dead Men map entered through a stock slot **never writes that slot's Steam board, never adds
  to the Steam stats and never unlocks stock achievements**: blocking on, as in 4.2.
- The score page's rank / name / points rows (`HeistStatusLeaderboard*`) are the stock map's
  friends list. On an expansion map they are wrong, so fail `FindOrCreateLeaderboard` too; the
  page then shows no rows (the 'count' fix `kla_lbfix` of `re/crash_scorepage.md` must be in the
  shipped hook for that case - a failed download is exactly its trigger).
- **The local high-score list is the same problem on disk.** 0x68b930 files the session under the
  slot index: `HeistTotalPoints[slot]` and the top-12 list at profile+0x1408 + slot*0x30 (names
  +0x10c), then the save writer 0x6587c0 stores it (in normal play 0x156b742 is 1). A Dead Men map
  in slot 0 would enter Subway's local list. Proposal (not tried): at state 0x28 entry the hook
  copies that slot's 0x30-byte row, its twelve 0x2d-byte names and `stats+0x4c+slot*4`, lets the
  handler run, and restores them before the save writer's file is closed - or, simpler, restores
  them and calls nothing: the next stock save then writes clean data. The expansion's own
  high scores go to a file of the hook's own (score = `[state+0x38]` read at state 0x28).
- A slot index outside 0..8 is no way out: 0x4b3c33 sends every unknown index to board 3
  (Subway), and 0x68b930 uses the raw index as an array subscript.
- Online (stage 4) adds the second upload path (0x65d950, boards `KL2_FA / UCC / TM_TotalMoney`,
  one upload per player at session end, state flag `session+0x198`) and the RMC-driven stats
  commit; the same proxy covers both on every machine that runs the hook, but a stock client in
  the same lobby would still write. That is one more reason for 'every player on the same pack'.

## 5. Not established

- Whether the Steam client rewrites `UserGameStats_*.bin` at once on `StoreStats` (the evidence in
  section 3 leans on it; the log evidence does not).
- Whose account id 838861569 is.
- The sender of `AnnounceFARoundCompleted` and whether Arcade uses it.
- Which achievements the mid-round counters can unlock, and their thresholds.
- Where `[state+0x6c]` gets its starting value (the HUD copy +0x44 is 3 from the constructor
  0x835512; the working count's writer besides 0x418730 / 0x5dfffd was not looked for).
- Which menu pages carry a `ZGUIOQuitGame` option (frontend.xml was not read for it); the code
  branch is taken by any such option accepted while an Arcade session exists. Treat every 'Quit'
  inside an Arcade session as an upload.
- AutoExit's shutdown path was not re-read for rules code (taken from `klauto.c`'s notes).
