# Fragile Alliance player limit (2026-10-25, static; nothing here ran live)

Question: why 8, is 12 / 16 possible. Short answer: the ENGINE cap is 12 (every setter and table). FA shows 8 only in one menu clamp.
A stock level has 8 heister seats. 16 needs new tables and is not a data change.

## 1. Where the number lives (kl2.exe, base 0x400000)

| Place | Address | Value / what | Data-only change? |
|---|---|---|---|
| Lobby row RIGHT cap (players) | 0x7dcb57 block in `ZMercsFASelectorLobby` slot 10 = 0x7dc060: `cmp dword [0x168e59c],2` 0x7dcb66; C&R cap `0xc` 0x7dcb6f; FA `cmp eax,8` 0x7dcb78, `mov al,8` 0x7dcb7d | FA 8, C&R 12 | code immediates (kllobbyopt.c does the press itself, see 7) |
| Lobby row LEFT floor | 0x7dc4f9 block; floor 6 (C&R) / 4 (FA) at 0x7dc510 / 0x7dc519 | 4 | code |
| Host start action (message 0x7f) | 0x5a9920 | floor X = 4, 6 in C&R | code |
| Target-size setter `b9` | 0x739f20 (stores `[sm+0xb9]`, writes at 0x739f37/41) | clamp [connected, **12**] | no change needed up to 12 |
| Max-players setter `b8` | 0x6f7fb0(n, publish): `[sm+0xb8]`, lobby attribute `ZSA_MAX_PLAYERS` via 0x947c70 | clamp [connected, **12**] | no change needed up to 12 |
| Option store `MP_NumberOfPlayers` | 0x472450 slot 5 of `ZMercsOptionsInterface`, clamp at 0x472b9d | 4..**12** | no |
| `MP_NumberOfPlayersCl` | client copy of the same | | |
| Join gate | ZSessionHandlerServer slot 49, 0x5067c7: refuse when `b9 <= connected` | b9 | follows b9 |
| Connected count | 0x698250 (kllobby.c reads `hi-lo` of `[[[sm+4]+8]+8/+0xc]`) | | |
| Steam lobby member limit | `ZAsyncTaskCreateLobbySteam` 0x705000: CreateLobby(type, **16** or property byte +5); byte written by 0x678d90 (`or [ecx],8 ; mov [ecx+5],al`) from b9 at 0x6c9ce4 (online create 0x6c9c10); 0x869430 also calls SetLobbyMemberLimit (vtable +0x78) with that byte | = b9 at create | YES, klmm.c `[Lobby] MaxPlayers` raises it |
| Rules records | `[rules+8]` 0x74-byte records (0x426c54 `imul 0x74`), `[rules+0x14]` 12 slots; ScoreFragileAllianceContainer / DeathmatchContainer `[12]`; `m_ClientPlayers.m_iPlayerIndex[12]`; 12 client slots (0x8fdf90 / 0x7ca830) | **12** | table sizes: 13+ overruns |
| Session player table | `0x6161c0`, 12-byte entries `{ZFFPlayer*, ..., used byte +9}` ; pick 0x6ee860 / 0x54cab0(index, type, 0) = first free entry whose `ZFFPlayer+0x273c == type` | = number of ZFFPlayer entities in the level | scene data |
| Level seats | 16 `ZFFPlayer`: `Heroes!Hero_01..08` (type 2 = heister, enum `eZFFP_TYPE_MULTIPLAYER_NORMAL`) + `Heroes!RespawnPolice#01..08` (type 3 = `MULTIPLAYER_POLICEMAN`). 8 `FA_START` spawns, ~7-8 `AFTER_DEATH`, 4-6 `TRAITOR`; team sets `TEAM_MERC` 6-8, `TEAM_POLICE` 6-8, `UCC_MERC` 8 | **8 heisters** | scene data |

So: the stock design is 8 heisters + 8 cop bodies = the 16 entities, and 12 as the engine ceiling (C&R: 6 v 6 on the same 16 entities).

## 2. What to do for each target

- **Now: 8.** Nothing needed.
- **9..12 (engine ceiling).**
  1. Lobby row must offer it: `kllobbyopt.c` (other agent): the players RIGHT clamp. Exact change for them: the FA branch `cmp eax,8 ; jl ; mov al,8` at 0x7dcb78..0x7dcb7d must become 12 (the C&R branch already is 12). Their handler pre-sets-and-reapplies through the same setters 0x739f20 / 0x6f7fb0 (which clamp to 12), so a press to 9..12 works the way the time/rounds presses do (see lobby_options.md).
  2. Steam member limit: done here, `[Lobby] MaxPlayers=N` (klmm.c, below).
  3. **Seats are the real blocker.** Joiners 9..12 find no free type-2 `ZFFPlayer`: `0x54cab0` returns -1 (the code that stores the result, e.g. 0x42bdd1 `mov [esi+0x14],al`, does not test it, so the 9th player gets index 0xff). Not read: what happens next (spawn fails / stuck on the loading screen / assert). Two fixes, both need the live game: (a) the extra players start as type 3 (cops, AFTER_DEATH spawn) like a dead heister; (b) the map gets 12 hero entities (new scene data, not a code change; the Dead Men graft maps are authored by us, so (b) is possible THERE first).
- **16.** Needs 12 -> 16 in at least: the `[12]` DDL arrays (their element counts are baked in the replicated class layout, so every peer must agree), the `[rules+8]` record array, the `[rules+0x14]` slots, the setters' clamps (code immediates 0xc), the player table, the HUD lists and the voice slots. Those are code and layout, not a data patch. Cost: a rewrite of the replication layer. Do not start it; 12 is the sensible ceiling. (The engine ships `ZSA_MAX_PLAYERS` as one byte; Steam itself allows 250.)

## 3. Bandwidth and per-peer streams (GUESS, not measured)

Net-Z sends a station's position at most every `min` ms per peer (stock 100 ms; klnet.c section 2), so a sender's upload is peers x 10 position updates a second plus the heading, camera and aim streams (camera 2 x, aim 1.5 x). 8 players = 7 peers, 12 = 11 (57 % more). The transport is Steam P2P UNRELIABLE (`Quazal::SteamSocketDriver::Socket` slot 4 = 0x883dd0, send type 0) with Net-Z PRUDP reliability on top: a saturated upstream shows as late/lost packets which the receiver extrapolates linearly from two samples (the spin, re/netcode_receiver.md). The host additionally replicates every AI to every client.

## 4. HUD, voice, ghosts

Not located for >8 (no address list yet). The HUD crew list reads `[12]` containers, so 9..12 should fit; the 8-row layouts of the custom HUD (klhud.c) draw 8 rows at most (check before raising). Voice: not read.

## 5. Risks of 9..12

1. A 9th seat does not exist (above): the most likely crash/hang. 2. Spawn points: 8 `FA_START` -> 4 players share spawns (they will be pushed apart by collision; with `OnlineSpawnpointTrigger` unknown). 3. Bandwidth (3). 4. Heist loot / traitor sets sized for 8. 5. `kllobby.c` MinPlayers / Solo untouched by this. 6. Both peers need the same hook version.

## 6. What was implemented (out_netmax_1025a)

- `[Lobby] MaxPlayers` (klmm.c, default 0, accepts 9..16; 8 is stock): the lobby's CreateLobby member count is raised to at least N and slot 30 SetLobbyMemberLimit is wrapped by a naked stub that raises its cMax argument in place (SDK layout, GUESS for this call site). It does NOT raise the in-game target; that is the selector (kllobbyopt.c) or b9 itself.
- `[NetLoad] Probe=1` (klnetload.c, read-only) and `ScaleSend=1` (opt-in; sender min interval x (1 + pct * (peers - from)), capped; data writes to the same 6 min-interval dwords klnet.c tunes; not in ranked lobbies; skipped while klnet Tune writes them).
- The existing `core: perf` line (every 10 s, always on) already reports the hook's tick cost and frames over 33 ms; the new probe adds peers and gap histogram per second.

## 7. Live recipe (owner)

1. `KLHook.ini`: `[NetLoad] Probe=1`, `[Net] Log=1`. Host a System Link lobby with 2+ real players. PASS lines: `netload: SERVER state 0x19 peers 3 (target 8, max 8) eligible | frames ~58 ...`; look at `gap max` and `over 100 ms` on host and client: a client that shows gaps over 100 ms is the unstable one (frame hitches), a host with clean gaps and a client with spin points at the network.
2. Compare with `ScaleSend=1` (all peers) and the same lobby: the `sender min ms` columns rise (player pos 100 -> up to 200) and `netload: ScaleSend: N peers -> sender intervals x1.xx` appears; `... put back` at the end of the session.
3. MaxPlayers: `[Lobby] MaxPlayers=12`, host any lobby: `mm: CreateLobby(type 2, max 8 -> 12 [Lobby] MaxPlayers=12)` must appear. If kllobbyopt offers 9..12, the third log is `net: session: SERVER ... players 9..12`; join with 9 clients and look for the first failure at the seat (above).
