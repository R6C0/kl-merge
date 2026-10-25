# Quick Match, Ranked and the host-server mode (2026-10-25)

Static reading of kl2.exe 0490 plus frontend.xml; NOTHING of this has run live. Code: `klhook/klserver.c`, `klhook/klmm.c`, `klhook/kllobby.c`.
Builds: `klhook/out_server_1025a` (SHIP) and `out_server_1025a_test` (TEST).

## 1. How Quick Match and Ranked find and make lobbies

- CERTAIN (disassembly, frontend.xml): `FAPlay` offers Ranked (`XBoxLiveCreateRanked`, option `MP_RankedGame=0`) and Player Match
  (`XboxLiveStart`, `MP_RankedGame=1`). `XboxLiveStart` offers Join Game (`QuickPlayerMatch`), Find Game, Create public, Create private.
- CERTAIN: the game-mode line ("FA") of `QuickPlayerMatch` and of `XBoxLiveCreateRanked` reaches the toggle-text handler 0x474e10..0x4752bc.
  With `QuickPlayerMatch` on top it clears `[sm+0x1a1]` and calls the session manager's QuickJoin `0x4196e0(1,1)`; with `MP_RankedGame==0`
  it calls `0x4196e0(1,1)` directly; otherwise the plain create `0x6c9c10`.
- CERTAIN: `0x4196e0` SEARCHES first (FASessionSearchingInterlude / QuickJoinInterlude). When no server is known it picks a random available
  level, sets `MP_PrivateGame=0` and CREATES a public lobby with `0x6c9c10`. So Quick Match and Ranked are both "search, else host".
- CERTAIN: lobby type: Ranked creates ELobbyType 3 (Invisible) and writes `Ranked`; Quick Match is type 2 (public). The game uses only
  numeric search filters (Ranked, Rank, GameType, Scenario, FAGameMode); no string filter.
- GUESS: Steam returns Invisible lobbies from `RequestLobbyList` (Steamworks docs say so; not seen in this build).
- Ranked statistics: `klsteam.c` blocks Steam stat/leaderboard writes for non-stock levels (`[Steam] Block=1 AllMaps=1`). On the 9 stock FA
  maps a modded ranked match can still write real stats/leaderboards (GUESS: no ranked-specific path found beyond the lobby flag). A server
  on Dead Men maps (`OnlineSet` 2/3/9) is covered by the block.

## 2. BuildKey (klmm.c) now covers both

All three entry points go through the ISteamMatchmaking import proxy: `CreateLobby` (slot 12), `SetLobbyData` (19), `RequestLobbyList` (4).
`[Net] BuildKey=1` writes `klx_build` (map-set hash) AND, new, `klx_set` = `set<N>` (`[Expansion] OnlineSet`, 0 = stock page) on the lobby
at the `name` SetLobbyData, and adds BOTH as string filters before the search. So modded hosts and searchers meet only with the same
maps and the same OnlineSet; Quick Match and Ranked searches that find nothing create their own lobby as before. Log lines
`mm: RequestLobbyList: string filter klx_build=...`, `...klx_set=...`, `mm: CreateLobby(type 3 = Ranked ...)`, `mm: SetLobbyData key 'name' seen: klx_build=... klx_set=...`.
GUESS (as before): string filter comparison 0 = Equal. Changing the filter set means old (pre-1025) modded lobbies without `klx_set` are no longer found.

## 3. Host-server mode: [Server] (klserver.c)

No dedicated binary exists: a server is a PC running kl2.exe as host. Limits: one Steam account per running copy, a GPU and a window
(low-res windowed is fine; the game must run, minimised can stall it), the launch options must NOT carry `-o DefaultScene=...` (it would load F01 instead of staying in the menu).
Flow (all game-thread calls to the game's own functions plus data writes, so SHIP-safe):
1. Menu: set options `MP_RankedGame` (1 quick, 0 ranked) and `MP_PrivateGame=0` through the option object (vtable slot 5); open `QuickPlayerMatch`
   / `XBoxLiveCreateRanked` with `0x6bee50`; send "FA" to `SLCreateGameModeQuickPlayerMatch` / `SLCreateGameModeXboxLive` (`0x83faf0` + element slot 20).
   GUESS: opening the window straight from any page, without the Play pages and `ZCheckGamerPrivileges`, is accepted.
2. Lobby (host, role 2, type 4, state 0xd): waits `WaitSec` for `MinPlayers`, then lowers `[sm+0xb9]` to the number connected (the kllobby.c lever),
   calls `0x6484d0(n)` for the clients' copy when 2 or more are connected (GUESS, `re/lobby_start.md` 4), and lets the game's own 15 s countdown run
   (GUESS `re/lobby_start.md` 3: no host button needed). `PressReady=1` fallback: RETURN then SPACE as scan codes via SendInput if still in 0xd 25 s later.
3. After the round/session ends: waits `RehostSec`, starts again at 1. If QuickJoin finds another host it joins as a client and the server stays until that session ends.
`[Server] Enable=1` implies `[Lobby] Solo=1` and MinPlayers=1 (kllobby.c), so a lone host is not thrown out by the "all players left" window.
The host's own player is a normal seat: it stands at its spawn in the round (CERTAIN); no spectator or harmless mode exists (GUESS: could be done by the fed machinery, not tried).
BuildKey is NOT implied: with `[Net] BuildKey=0` strangers without the maps can join and, with `OnlineSet != 0`, fail on the level load; a log line says so.

## 4. Live test recipe

Hook: copy `out_server_1025a_test\dinput8.dll` (TEST) next to kl2.exe; launch WITHOUT DefaultScene. KLHook.ini:
```
[Server]
Enable=1
Mode=quick
MinPlayers=1
WaitSec=20
[Net]
BuildKey=1
[Expansion]
OnlineSet=2
```
Pass lines in KLHook.log, in order: `server: ON - mode quick`, `lobby: [Server] Enable=1 implies Solo=1`, `server: option MP_RankedGame = 1 (read back 1)`,
`server: attempt 1: menu [...] -> open QuickPlayerMatch`, `server: QuickPlayerMatch open: sending FA`, `mm: RequestLobbyList: string filter klx_build/klx_set`,
`mm: CreateLobby(type 2 = public ...)`, `mm: SetLobbyData key 'name' seen: klx_build=... klx_set=set2`, `server: lobby open`,
`server: lobby target ... -> 1`, then `LOAD F01: online=1 OnlineSet=2 ...` and the round; after the round `server: the hosted session is over ... hosting again`.
Fail signals: `option object not ready`, `no GUI element`, `did not come to the top`, `no hosting session N s after the message`, `still in 0xd` (set `PressReady=1`).
Second step: a second PC/account with the same maps searching (Player Match > Join Game) must find and join. Ranked: `Mode=ranked`, expect `CreateLobby(type 3 = Ranked`.
