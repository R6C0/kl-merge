# Dog Days multiplayer: reconnaissance of kl2.exe

Static analysis only (2026-10-09). Nothing was run, no connection was opened, no game file was written.
Subject: `kl2.exe`, PE timestamp 0x4c80f728 (2010-09-03), string `Build 0490 (09-03-2010)` at 0xb2a80c,
image base 0x400000, plus `steam_api.dll` beside it. All addresses are kl2.exe virtual addresses.

How to read this: every statement carries what was looked at. **ASSUMPTION** marks an interpretation that
the bytes do not prove. "Not established" means it was looked for and not settled, or not looked for.

Method (scripts are in the scratch folder `...\scratchpad\agents\track-netcode`, not in the repo):
string dump of the exe with addresses; MSVC RTTI names and class hierarchies; xrefs = search of `.text`
for the 4-byte address; `call`/`jmp rel32` callers; vtable owners through `debug/rtti.py`;
capstone disassembly (`debug/kl.py` `Exe`). The Quazal DDL parse trees embedded in `.data` were decoded
with a small parser (grammar in Appendix A) - they give every replicated class, dataset and remote
method **by name**, which is why this file can name things the exe otherwise has no symbols for.

---------------------------------------------------------------------------------------------------

## 1. Answers in short

| Question | Answer | Standing |
|---|---|---|
| Which Quazal products | **Net-Z only** (object replication, sessions, PRUDP). No Rendez-Vous. | established (2) |
| Version | `Quazal Net-Z` / `Version 2008.9 SP1` (0xbdf308 / 0xbdf318); DDL trees stamped 2,18,0,1885,114 (game) and 0,17,1,1808,215 (Net-Z's own) | established |
| Session discovery | **Steam lobbies** (`SteamMatchMaking008`). Lobby data keys: name, Scenario, GameType, FAGameMode, RoundTime, NumRounds, Ranked, Rank, CoopDifficulty | established (3) |
| Transport | Net-Z packets carried as **Steam P2P packets** (`SteamNetworking003`, unreliable send type), through `Quazal::SteamSocketDriver` | established (3.4) |
| Servers the game needs | For lobby + play: only Steam. The Eidos hosts are metrics / "infocast" news / rankings. | Steam path established; "Eidos hosts are optional" is **not established** by test |
| Private sessions | Already there: session property bit 4 creates a **friends-only** lobby; invites and `+connect_lobby <id>` are handled | established (3.2, 3.3) |
| Anti-cheat / file hash between peers | None found. No hash of level files seen in the join path. Steam DRM/CEG-named code exists in the exe. | absence is **not established** (5) |
| Version check between peers | `DDL_ZServer.m_szVersion`, `DDL_ZClient.m_bSoftVersion`, join-denial code 3 "Clash" exist. Where they are compared: not found | not established (5) |
| Host model | One station is server: rules exist as `...Sv` and `...Cl` classes and only the `Sv` class issues traitor / police / spawn commands; score, money and escape state sit on server objects. Players move themselves. | class split established; host migration not established (6) |
| Movement replication | Each player's own machine writes position (int16 world units), heading (1/1024 turn, unwrapped), camera angle, aim point, move input. Unreliable, behind Net-Z's extrapolation filter: min 100 ms between updates, forced refresh after 2000 ms, error dead-band 20 units / 30 angle units. Remote side: two-sample linear extrapolation, then the game steers the remote character with the replicated stick input plus an error correction. | established (8) |
| Traitor state | Server side: `ZGameRulesFragileAllianceSv` vtable slot 129 (0x41d480). Stored as per-client flags plus `RMCSetTraitor` on the player object. | functions established, flag bit meanings not (9) |
| Criminal -> police on death | Server: 0x6bb910. Police character = **first free player entity whose type byte is 3** (0x6ee860). Sent to the client with `RMCRespawn(bBecomePolice, iRespawnPlayerIndex, iFollowClientIndex)`. | established (10) |

---------------------------------------------------------------------------------------------------

## 2. What is linked in

RTTI holds 413 names containing `Quazal` (counted in the string dump). Present: `NetZ`, `NetZProductInfo`,
`Session`, `Station`, `SessionClock`, `DuplicatedObject`, `DuplicationSpace`, `PromotionReferee`,
`IDGenerator`, `DefaultCell`, `PRUDPStream`/`PRUDPEndPoint`, `UDPTransport`, `BerkeleySocketDriver`,
`NATTraversalEngine`, `LANSessionDiscovery`, `GlobalDiscovery`, `ConnectivityTester`, `RC4Encryption`,
`MD5Checksum`, `HMACChecksum`, `NetworkEmulator` templates, `PHBDRModel` (dead reckoning), and four
Steam-specific classes placed in the Quazal namespace: `SteamSocketDriver`, `SteamTransportAdapter`,
`SteamConnectivityTester`, `SteamSocketContext`.
Source paths left in asserts: `ff2\net\OnlineServices\SteamSocket.cpp`, `...\SteamTransport.cpp`,
`ff2\net\SessionManagerMultiplayer.cpp`, `Z:\code\libraries\netz\NetZ_Win32\WINTEL\include\...`.

Not present: a search of all strings for `RendezVous|Rendez-Vous|BackEndServices|MatchMakingClient|
SecureConnection|Kerberos|FriendsClient|RVConnection|ProtocolFoundation` returns 0 lines. So there is no
Quazal lobby/authentication server client in this exe; `StationURL.cpp` still knows the `XLSPID`/`RVCID`
URL fields.

Product string: 0x97f170 builds the product info with `"Quazal Net-Z"` and `"Version 2008.9 SP1"`;
copyright `Copyright (C) 1998-2009, Quazal Technologies Inc.` at 0xbd8234.

Steam: imports `SteamAPI_Init, SteamAPI_RestartAppIfNecessary, SteamAPI_RunCallbacks, SteamUser, SteamApps,
SteamUserStats, SteamFriends, SteamMatchmaking, SteamNetworking, SteamUtils, SteamClient,
Register/UnregisterCallback, Register/UnregisterCallResult, WriteMiniDump, SetMiniDumpComment, Shutdown`
(IAT 0xb107ac..0xb107f0). `steam_api.dll` strings: `SteamMatchMaking008`, `SteamNetworking003`,
`SteamFriends005`, `SteamUser013`, `SteamUtils005`, `SteamClient009`, `STEAMUSERSTATS_INTERFACE_VERSION007`.

Other network code: `WS2_32` (sockets), `WININET.InternetGetConnectedState` only; an Eidos HTTP client
(`otnet`, `otpsp`, `otmetrics`, `otcontent` namespaces, user agent `Eidos-OnlineSuite/1.0 (Windows)`).

Game-side classes (RTTI): `OnlineServices::IOnlineService`, `ZOnlineServiceWintel`, `ZOnlineServiceSteam`
(vtable 0xbd597c), async tasks `ZAsyncTaskCreateLobbySteam`, `ZAsyncTaskJoinLobbySteam`,
`ZAsyncTaskSessionSearchSteam`, `ZAsyncStartSessionAndSyncLobby`, `ZAsyncTaskPingSteam`,
`ZAsyncTaskRemoteUserLeaveSteam`; `ZSessionManager`, `ZSessionManagerMultiplayer` (vtable 0xbd1ebc);
`ZSessionHandlerBase`, `SP`, `FrontEnd`, `MP`, `Client`, `Server`; `ZGameRulesBase`,
`ZGameRulesFragileAlliance`, `...Sv`, `...Cl`; `ZGameRulesCoop`, `Sv`, `Cl`; `ZGameRulesHeist`;
net-sync entities `ZHavokRigidBodyNetSync`, `ZHavokShatterNetSync`, `ZHavokShatterGlassNetSync`,
`ZMatPosAnimNetSync`, `ZHeliNetSync`, `ZShotActivateNetSync`, `ZVehicleEffectsNetSync`,
`ZGenericNetObjectController`, `ZOnlineSyncGate`, `ZOnlineTriggerSync_*`.

---------------------------------------------------------------------------------------------------

## 3. A session from creation to play

### 3.1 Start mode
`ZSessionManagerMultiplayer` vtable slot 15 (0x8733e0) reads these `-o` keys through 0x793550:
`MPTutor` (atoi, this+0x14c), `StartAsServer`, `StartAsClient` (sets this+0x54 = 3), `StartAsCoop`,
`EnableCoop`, `StartAsSinglePlayer`, then calls its slot 13 with "a mode was forced" as argument.
`MPMap` is read at 0x491f50, 0x6c49a0 (`ZSessionManagerMultiplayer[27]`), 0x6c9c10, 0x89fa20.
What `StartAsServer` does without a lobby was not traced: **not established** whether a forced
server/client pair can meet without Steam matchmaking.

### 3.2 Creating (host)
`ZOnlineServiceSteam` slot 40 (0x8e4fe0; RTTI names a CEG wrapper for
`ZOnlineServiceSteam::CreateSession(ZSessionProperties const&)`) reads the property block: dword +0 = which
fields are set, byte +5 = max players (0x607290), word +8 bit 4 (0x556f80) and bit 5 (0x5e1080). It takes
the local Steam id (`SteamUser` vtable +8), then starts `ZAsyncTaskCreateLobbySteam` (slot 8 = 0x705000)
with a lobby type (0x8e514b..0x8e5174):

| condition | value pushed | Steam `ELobbyType` |
|---|---|---|
| property bit 5 set (the same bit that is written to lobby key `Ranked`) | 3 | Invisible |
| else property bit 4 set | 1 | FriendsOnly |
| else | 2 | Public |

0x705000 calls `SteamMatchmaking` vtable +0x30 with (type, max members); max members is 16
(`mov edi,0x10`) unless property flag 8 supplies byte +5. Completion handler 0x822900 stores the lobby
id and calls 0x869430, which writes the lobby data through vtable +0x4c:
`name` (persona name), `Scenario` (a number; two source fields depending on game type 4),
`CoopDifficulty` or `FAGameMode`, `RoundTime`, `NumRounds`, `Ranked`, `Rank` (only if ranked), `GameType`;
and the member limit through vtable +0x78.

### 3.3 Finding and joining (client)
- Search: `ZOnlineServiceSteam` slot 42 (0x559dc0) references the keys `Scenario`, `CoopDifficulty`,
  `FAGameMode`, `Ranked`, `Rank`; `ZAsyncTaskSessionSearchSteam` slot 12 (0x424840) calls vtable
  +0x10 (lobby list request), slot 11 (0x6f2d50) calls +0x6c per lobby; 0x86b0e0 reads the keys back.
  **No key carries a build or data version** (the nine keys above are all that 0x869430 writes).
- Join: `ZAsyncTaskJoinLobbySteam` slot 8 (0x572010) calls vtable +0x34 with the lobby id.
- Invite / command line: `CCallback` classes for `GameLobbyJoinRequested_t`, `LobbyInvite_t`,
  `LobbyChatMsg_t` on `ZOnlineServiceSteam` are in RTTI; `ZSessionManager` slot 23 (0x506cc0) does
  `strstr(..., "+connect_lobby")` then `sscanf("%I64u")`.
- Start of play: `ZAsyncStartSessionAndSyncLobby` (0x406560): if the local user is the lobby owner it calls
  vtable +0x84 (lobby, 0) and sends the lobby chat message `SyncLobbyWithNetZ` (+0x64). The receiver
  (0x8bd520) reads chat (+0x68), on `SyncLobbyWithNetZ` runs 0x4d2a40 and answers `SyncedWithLobby`;
  a third message is `ExitLobby`.
- 0x4d2a40 walks the lobby members (+0x44) and makes the P2P peer table equal to the lobby: adds missing
  members (0x763070), and with its flag set removes peers that left (0x503040, which closes the P2P session).

Steam vtable offsets to method names are an **ASSUMPTION** from the Steamworks headers of that generation
(Appendix B). They are anchored by argument counts and by the string keys passed, not by symbols.

### 3.4 Transport
`Quazal::SteamSocketDriver::Socket` (vtable 0xbd5f9c): slot 4 (0x883dd0) sends: looks the destination up in
the peer table of a singleton (global 0x168f960; table at +0x28, count +0x2c, 16-byte entries with the
Steam id at +1, a "session open" byte at +9, a tick at +0xc) and calls `SteamNetworking`
vtable +0 with send type **0 (unreliable)**. Slot 3 (0x48ca80) receives: +4 (packet available), +8 (read);
a packet from a Steam id that is not in the table is dropped and +0x10 (close session) is called for it.
Reliability therefore comes from Net-Z's own PRUDP layer, not from Steam.
0x6e2690 (ASSUMPTION: the `P2PSessionRequest_t` handler; it takes a pointer to a Steam id) calls +0xc
(accept) for a known peer, and for an **unknown** one also accepts and adds it to the table (0x6fc1c0).
0x6fc1c0 with its flag set sends one packet of send type 2 (reliable) to open the session.
Strings `Network: set RC4 encryption engine` / `no encryption engine used` exist (0xbd7c94); which one
the game selects was not traced: **not established**.

LAN / system link: `LANSessionDiscovery` and GUI classes `ZGUIOQuickJoinSystemLinkServerButton`,
`ZGUIDIXboxLiveServersList` are in the exe (shared console code). Whether the PC front end can reach them:
**not established**. `K&L server` (0xb535c0) is used at 0x83c040.

### 3.5 Join answers
`ZSessionHandlerClient` slot 98 (0x8309d0) turns the join result into a message. Codes
0x8006000b = `Online/ConnectionTimeOut`, 0x8006000d = `Online/ConnectivityTestFailed`, 0 =
`Online/JoinSessionFailedDefault`; positive codes go through the jump table at 0x830fc8:
1 `Online/GameAlreadyStarted`, 2 `...FailedNotInGame`, 3 `...FailedClash`, 4 `Online/JoinSessionClientSide`,
5 `Online/LobbyClosedByServer`, 6 `Online/BadConnection`, 7 other (table entry 0 = `...ServerFull`, a string
also used at 0x79ae20 and 0x7d8680). The host-side function that chooses the code was **not found**.

---------------------------------------------------------------------------------------------------

## 4. Compiled-in hosts

| String | Address | Used by | What it is |
|---|---|---|---|
| `http://kl2-pc-game.infocast.eidos.co.uk` | 0xb16a40 | 0x49fe80, 0x60ce00, 0x677010, 0x713020, 0x7ec6d0 | "infocast" (lobby news; `InfocastLobby*` strings) |
| `.../GData/Infocast/feed/user/steam` | 0xb67ab8 | not searched | same service |
| `https://kl2-pc-game-content.eidos.co.uk` | 0xb58668 | 0x495790 | content service, chosen by `UseEidosMetricsServers` |
| `http://web-w2k8.eidos.com` | 0xb18844 | 0x495790 | the other branch of the same switch |
| `https://kl2-pc-game-metrics.eidos.co.uk` | 0xb73544 | 0x71b300 and others | gameplay metrics (`otmetrics`) |
| `http://content.eidos.co.uk/GData/Rankings` | 0xbe4460 | 0x99c7a0, 0x99e7d0, 0x99f560 | `otpsp::ZEidosRankingSystem` |
| `http://10.118.11.206/` | 0xb52b34 | 0x541c50 | a private-range address |

None of the lobby / P2P / Net-Z functions read in section 3 references any of them. Whether a front-end
screen blocks when they do not answer was **not established** statically.

`-o` keys seen in this area: `UseEidosMetricsServers` (six readers), `DisableClientCountDisconnect`
(`ZSessionHandlerMP` slot 2, 0x56e093: skips a periodic check that otherwise raises `Online/BadConnection`),
`DisableSyncChange2` (0x601789, section 8.4), `DisableFAVariants` (0x8228a3, `ZGameRulesFragileAlliance`
slot 34), `SoftVersion` (0x40d627), `MPTutor`. `NetLog.txt` is referenced three times in the Net-Z start-up
function 0x7ee0c0; the condition that enables it was not traced.

---------------------------------------------------------------------------------------------------

## 5. Integrity, version, anti-cheat

Found:
- `DDL_ZServer.m_szVersion` (string) and `m_szServerMap` (string), `m_iScenarioIndex`/`m_iNextScenarioIndex`
  (int8) are replicated from the server; `DDL_ZClient.m_bSoftVersion` (bool), `m_iAvailableLevels` and
  `m_iAvailableCampaignLevels` (uint16) from each client. `SoftVersion` is a configuration key
  read at 0x40d627 next to `Demo`, `PreviewBuild`, `DisableCensoring`.
- Join-denial code 3 = `Online/JoinSessionFailedClash`.
- The string `Build 0490 (09-03-2010)` has **no absolute reference** in `.text`.
- RTTI names `CEG_ForceRefClass_*` for nine functions (`ZOnlineServiceSteam::CreateSession`,
  `CreateClientSession`, `ZFFPlayer::AdjustHitPoints`, `EnterVehicle`, `KickDoorRequest`,
  `ZOnlineEscAnimatedVehicle::Command`, three leaderboard/achievement writers) and the strings
  `STEAM_DRM_IPC`, `.STEAMSTART`: Valve's DRM / CEG scaffolding is compiled in.
- 0x873500 (right after the start-mode function) walks 104 self-relative table entries and XORs a value
  with 0x135e. Purpose unknown.

Not found: any call that hashes a level archive, any comparison of `m_szVersion`, any string naming an
anti-cheat product (VAC, PunkBuster, GameGuard).

Standing: **not established**. In particular "a patched exe will not be rejected" must be tested, not
assumed: CEG-wrapped functions may verify themselves, and the nine include `CreateSession`.

Established from the DDL alone: objects are addressed across the wire by 16-bit references into the scene
(`m_iGeomRef`, `m_iRef`, `m_iFFWeaponRef`, `iKickDoorRef`, `refCutSequence` ...). Two peers must therefore
load the same scene with the same entity order. A grafted map can only work between players who hold the
identical build of it; nothing found so far would stop mismatched players from connecting or warn them.

---------------------------------------------------------------------------------------------------

## 6. Host model

- `DDL_ZServer`, `DDL_ZScoreFragileAlliance`, `DDL_ZScoreDeathMatch`, `DDL_ZFFActor`, `DDL_ZFFItemWeapon`,
  `DDL_ZGenericNetObject`, `DDL_ZSimpleNetObject`, `DDL_ZClient`, `DDL_ZFFPlayer` are all declared
  `userdo globaldo` (Appendix A).
- AI: `DDL_ZFFActor` replicates position, angle, animation-state ids, hit points, target, ragdoll flags, and
  has commands `RMCMoveToPosition`, `RMCServerForcePosition`, `RMCFireWeapon`, `RMCAimAtTarget`... So actors are
  simulated on one station and mirrored elsewhere. That this station is always the host is an ASSUMPTION
  from the name `RMCServerForcePosition`; the creation site of the actor objects was not traced.
- Rules: `ZGameRulesFragileAllianceSv` and `...Cl` differ in 52 of 203 vtable slots (compared slot by
  slot; Sv vtable = 0xbd2eb4). Only `Sv` methods call the wrappers for `RMCSetTraitor`, `RMCSetPoliceMan`,
  `RMCSpawn`, `RMCFARespawnData`, `RMCAnnounceFATraitor` (sections 9, 10).
- Loot and escape: `DDL_ZServer` carries `RMCOnlineMoneyContainerOpenStart/Done`,
  `RMCOnlineMoneyControllerActivate`, `RMCDropMoney`, `RMCRemoveSharableMoney`, `RMCHoldEscapeVehicle`,
  `RMCResetEscapeVehicle`, `RMCSynchronizeVehicleHitpoints`, `RMCPlayerBoards`; the score object carries
  `m_iEscapeSeqState`, `m_fEscapeSeqTimer`, `m_iEscapeSeqTransportRef`, `m_iEscTransportState` and the round
  clock. So money and escape state live on server objects.
- Players: each client is master of its own `DDL_ZFFPlayer` (the write function 0x6300f0 begins with the
  test 0x9425a0, the same test every RMC wrapper uses to choose "run here" or "send") - movement is
  client-authoritative.
- Hits: `DDL_ZFFActor::RMCReceiveHit(m_refOwner, m_eDamageType, m_refWeaponTemplate, m_iDamage, m_iHeadshot)`
  and the player's `RMCUpdateHitPoints` / `m_DeathInfo` suggest the shooter's machine reports the hit:
  ASSUMPTION from the parameter lists, dispatch not traced.
- Host loss: Net-Z's `PromotionReferee`, `ChangeMasterStationOperation`, `MigrationContext`,
  `FaultRecoveryOperation` are linked; the game has `HostDisconnect` (0x6455bc, `ZMercsFASelector`),
  `Online/LobbyClosedByServer`, `RMCAnnounceFALastPlayerDisconnected`, `RMCSetOneTeamDisconnected`.
  Whether a session survives the host leaving: **not established**.
- Limits: every per-player array in the DDL has 12 entries.

---------------------------------------------------------------------------------------------------

## 7. Replicated objects

Full list in Appendix A (the game's twelve DDL units; 303 remote methods: NetServer 113, NetFFPlayer 87,
NetClient 70, NetActor 27, NetWeapon 5, OnlineServiceBroker 1).

Dataset properties as declared: `unreliable`; `extrapolation_filter` (Net-Z dead reckoning: send only when
the remote prediction is wrong enough, section 8.2); `upon_request_filter`; `basic_update_protocol`.

`DDL_ZFFPlayer` object layout, from its constructor 0x539e90 and the generated update function 0x7a3a50
(dataset vtables identified by RTTI):

| offset | dataset id | type | member |
|---|---|---|---|
| +0x58 | 1 | `DDL_SPlayerAngleData` (int16 at +0x60) | m_Angle |
| +0xd8 | 2 | `DDL_SPlayerCamAngleData` (int16 at +0xe0) | m_CamAngle |
| +0x158 | 3 | 0x18 bytes | m_DeathInfo - by size, ASSUMPTION |
| +0x170 | 4 | `DDL_SPlayerFireAimPosData` | m_FireAimPos |
| +0x260 | 5 | 0x10 bytes | m_InputData - by size, ASSUMPTION |
| +0x270 | 6 | 0x28 bytes | m_Inventory - by size, ASSUMPTION |
| +0x298 | 7 | `DDL_SMoveInputData` (int8 at +0x2a0, +0x2a1) | m_MoveInputData |
| +0x350 | 8 | `DDL_SPlayerPositionData` (int16 x3 at +0x358) | m_Position; per-axis models at +0x388, +0x3c0, +0x3f8 |
| +0x440.. | 10.. | eight 0x20-byte reliable scalars | the UInt16/Int8 members (order not established) |
| +0x540 | | pointer | the game's `ZFFPlayer` |

`DDL_SContinuousData`, `DDL_SPlayerHitPointsData`, `DDL_SPlayerCoverData`, `DDL_SThrowGrenadeData`,
`DDL_SEscapeState`, `DDL_SRoundProgress`, `DDL_ZAnimationData` are declared but are not members of any DO
class in the trees.

---------------------------------------------------------------------------------------------------

## 8. Player movement replication

### 8.1 Sender (the player's own machine): 0x6300f0
Called from five places (0x4d2f10, 0x62df10, 0x633590, 0x78aed0, 0x7edc20; which of them is the per-frame
one was not traced). Runs only if the object is the master (0x9425a0), the `ZFFPlayer` exists, and the
state returned by 0x8e6a20 on the session handler (global 0x168e598) is 0x17, 0x18, 0x19 or 0x1f.
- If `ZFFPlayer`+0xd50 is non-zero (attached to something: ASSUMPTION): only aim point and move input go out.
- Heading: an angle from 0x429ff0 times the double at 0xb78bc8 = **162.97466 = 1024 / 2 pi**, truncated to
  16 bits, handed to 0x8b6990. That function does **not** store it; it takes the stored value modulo 1024,
  forms the difference to the new one, folds the difference into -512..+512 and **adds** it. So `m_iAngle`
  is a running, unwrapped heading in 1/1024 turns held in an int16.
- Position: 0x5a0ff0 truncates the three world coordinates to int16 with **no scale** (`_ftol2`, 0xa8d330).
  One unit = one world unit; range +-32767 units. (World unit = centimetre: ASSUMPTION.)
- Move input: virtuals +0x5b8 / +0x5bc of the player times 100.0 (0xb3dde8), two int8.
- Then 0x8dbb30 ("update this dataset") for position, angle, camera angle, aim point, and move input.

### 8.2 The filter between "update" and a packet
One settings pair per extrapolated dataset type, in `.data`, laid out by static initialisers
(0xb047b0..0xb04fd0) as [tolerance object][policy object][type name]:

| dataset | tolerance object | set to | interval globals {max, min} ms | min set to |
|---|---|---|---|---|
| DDL_SActorPositionData | 0x168f1e4 | 30.0 | 0xd34664 / 0xd34668 | B |
| DDL_SActorAngleData | 0x168f244 | 30.0 | 0xd34684 / 0xd34688 | B |
| DDL_SPlayerPositionData | 0x168f440 | **20.0** | 0xd35420 / 0xd35424 | B |
| DDL_SPlayerAngleData | 0x168f4b0 | **30.0** | 0xd35458 / 0xd3545c | B |
| DDL_SPlayerCamAngleData | 0x168f510 | 40.0 | 0xd35478 / 0xd3547c | 2 x B |
| DDL_SPlayerFireAimPosData | 0x168f570 | 5.0 | 0xd35498 / 0xd3549c | 1.5 x B |

All set in **0x4825b0**, called once from the Net-Z start-up 0x7ee0c0 (`this` = `ZSessionManagerMultiplayer`).
B = `[this+0x158]`, which the constructor 0x8c49e0 sets to **100** (0x8c4b5b; no other immediate write to
+0x158 inside that class's constructor/destructor was found; a later computed write is not excluded).
The "max" globals keep their initialised value **2000**; the "min" globals are initialised to 150 and
overwritten by 0x4825b0. 0x990e40 stores the tolerance **squared** at object +0.
The pairing of tolerance object to dataset rests on the static-initialiser order plus one direct check:
0x168f440 is the object the player-position decision function uses, and 0x168f460 is the one the
player-position read/write functions (0x77ebe0, 0x8df1c0) pass.

The decision for one remote station, read for player position (0x48db30; the other types were not read
individually, their globals have matching small accessor functions):
1. 0x902e80: if less than `[0xd35424]` ms since the last update to that station: do nothing.
2. 0x4ac330: sum over the three axes of (actual - what that station is predicted to be extrapolating)^2
   (0x993a40, 0x992c50). 0x990f30 turns the tolerance object and a distance (0x94b980) into the allowed
   error. If the error is larger: send.
3. else 0x861430: if more than `[0xd35420]` ms since the last update: send anyway.

So for a remote player: at most one position and one heading update per 100 ms, nothing at all while the
remote prediction is within 20 units / 30 angle units (30/1024 turn = 10.5 degrees), and a forced refresh
only every 2 s. All of it declared `unreliable`.

0x4825b0 also calls `0x990d40(250, 1000)` on the two player policy objects (0x168f460, 0x168f4d0) and
`(50, 250)` on the others, and 0x990d30 writes 100 or 0 to global 0x1691d40. 0x990d40 stores the pair at
policy +0xc / +8 (defaults 250 / 1000 from 0x990de0, with 4.0 at +0 and 3500 at +0x14). What these
numbers do in the model was **not established**.

### 8.3 The model
`PHBDRModel` (0xd0-byte allocation at 0x4675a0 and six sibling functions, one per extrapolated type, all
referring to `Extensions/PHBDR/EDataSetTemplate.h` line 0x75). Reading a value at a time: 0x992f10 walks a
list of timestamped int16 samples, takes two neighbouring samples and returns
`v0 + (v1 - v0) / (t1 - t0) * (t - t0)`: linear, from two samples, on integer values. Only the first half
of 0x992f10 was read; a clamp on `t` further down is not excluded.

### 8.4 Receiver (a remote player on my machine): 0x600eb0
Called from 0x73c830. Skipped while `ZFFPlayer`+0x2760 > 0, +0xd5c != 0, or two virtual tests fail; same
state gate as the sender.
1. 0x519e80 (refresh at the session clock time, 0x49d020 then 0x942bf0) for move input, position, angle,
   camera angle.
2. Heading = `m_iAngle / 162.97466` radians, turned into a rotation (0x7f07a0, 0x589440). No smoothing is
   visible between the refreshed integer and the rotation.
3. Position: if the three raw int16 are all zero they are seeded from the current local position. The
   extrapolated coordinates come from 0x77ebe0, once per axis model.
4. If |extrapolated - current|^2 > 1,000,000 (0xb49b40, i.e. 1000 units): 0x5f21c0 (ASSUMPTION: snap).
5. Otherwise the character is **not placed** at the extrapolated point. The function forms the offset,
   applies several thresholds (9.0 or 100.0 on a squared horizontal distance depending on a flag, 40.0,
   40000.0, a 0xc00-tick timer at DO+0x544, state 0x19), an extra block gated by `-o DisableSyncChange2`
   (0x601789), and finally feeds the character `m_iMoveFrontBack / 100` and `m_iMoveSides / 100` as stick
   input (0x72cf20, 0x7e4510) together with the offset vector (0x5b5920). When the offset is small
   (double at 0xb3c350) and 0x40f840 is false, both inputs are forced to 0.
   What each threshold means was not worked out.

### 8.5 What this says about "jittery / spinning"
The facts above can each produce it. Which one is the cause in practice is **not established**.
- H1 (spin): the heading is extrapolated linearly from the last two samples, and the "stopped turning"
  correction is an unreliable packet. If it is lost, the sender does not know (step 2 of 8.2 compares
  against the *predicted* remote state) and sends nothing until its own prediction drifts 10.5 degrees or
  2 s pass. Meanwhile the remote copy keeps rotating at the last angular velocity. A fast mouse flick
  followed by one lost packet fits "spinning character".
- H2 (spin, rarer): the unwrapped int16 heading overflows after 32 net turns in one direction
  (32768 / 1024); the next sample pair then differs by 65536 units.
- H3 (jitter): 10 updates a second at best, a 20-unit dead-band, integer positions, and a receiver that
  steers by replicated stick input plus correction instead of interpolating between received points.

---------------------------------------------------------------------------------------------------

## 9. Betrayal, trust, score

Where the state lives (DDL, established):
- `DDL_ZScoreFragileAllianceContainer` on the score object, 12 slots each: money (`m_iTotalRewardMoney`,
  `m_iTotalLootMoney`, `m_iBestGrab`, `m_iSharableMoney`, `m_iUnsharableMoney`), `m_iKills`, `m_iPoliceKills`,
  `m_iAssists`, `m_iTrust`, `m_iKillerIndex`, `m_iRating`, `m_iCustomFlags` (int32), `m_iNumRoundsEscapedAsMerc`,
  `m_iNumRoundsEscapedAsTraitor`, `m_iNumMercsKilled`, `m_iNumTraitorsKilled`, `m_iNumRoguesKilled`,
  `m_iNumOthersKilled`, `m_iNumPersonalRevenges`, `m_iPlayStyleMasks`, `m_iPlaystyleKillPoints`, `m_iExperience`.
- `DDL_ZClient`: `m_iTeam`, `m_TrustHistory` (int8[25]), `m_iTotalTrust`, `m_iTotalPlaystyle`,
  `m_iTotalExperience`, `m_iUseMask`, `m_iRank`.
- `DDL_ZFFPlayer`: `m_iFlags` (uint16) and the commands `RMCSetTraitor`, `RMCSetPoliceMan`,
  `RMCSetUndercoverCop`, `RMCSetGhost`, `RMCSetSpectating`, `RMCSetInvulnerable`.
- Server commands: `RMCBecomeTraitor(iClientIndex, iVictimIndex)`, `RMCBecomeDirtyCop`,
  `RMCSetYellowcard(iClientIndex, iDamageDealerIndex)`, `RMCSetDamageDealer`, `RMCUnsetDamageDealer`,
  `RMCSetKillMarked`, `RMCAddAssistAtServer`, `RMCSetCustomFlagsOnServer` / `RMCUnsetCustomFlagsOnServer`,
  and the `RMCAnnounce*` family (traitor, dirty cop, revenge, cash majority, perfect split ...).

Code (established by tracing callers of the generated call stubs; a stub is the small function that
looks its method up by name string):
- **Make a traitor, server side: `ZGameRulesFragileAllianceSv` slot 129 = 0x41d480.** It returns early in
  state 0x1f or if the flags got through virtual +0x1c8 for the first index have 0x4 or 0x8; tests flags
  0x1, 0x20, 0x40 on the indices passed; sets flag value 2 and 1 through virtual +0x1cc; calls the
  `RMCAnnounceFATraitor` wrapper 0x426cd0 (its last argument is 1 when this+0x36c is 0), the
  `RMCSetTraitor(1)` wrapper 0x4f2f70 on the player object, and the `RMCSetPrevRoundTraitor(1)` wrapper
  0x6899b0. The function's first argument is handed to the announce wrapper in the position of
  `iKillerClientIndex` and its second in the position of `iDeadClientIndex`
  (`RMCAnnounceFATraitor(iKillerClientIndex, iDeadClientIndex, bFirstTime)`), so first = the traitor, second =
  the victim, if the wrapper keeps the RMC's parameter order (ASSUMPTION). The names of the flag bits are
  **not established** (ASSUMPTION: the flags are `m_iCustomFlags`).
- Who asks for it:
  1. `RMCBecomeTraitor` to the server (stub 0x7c9d90, wrapper 0x745da0, which on the master calls the
     game-rules object's virtual +0x204 = slot 129). Its only other caller is 0x76bf20, called only from
     0x4d7b00, which is reached from the `DDL_ZFFPlayer` dispatcher (0x658b60) in the branch for
     **`RMCRealStartHumanShieldPvP`** (0x658f35, 0x7cbc60, 0x5949a0) and from 0x4aa100. So grabbing another
     player as a human shield is one trigger, and it is raised from a client. (The branch-to-name mapping
     comes from the registration order in 0x4b0ad0; checked against `RMCSetTraitor` = class word +0xac.)
  2. `ZGameRulesFragileAlliance` slot 149 (0x785fa0), shared by Sv and Cl: calls slot 129 with -1 after
     halving a value (0x699030, `shr 1`, 0x5632d0). What event this is: not established.
  3. The ordinary "shot a partner" path was **not traced**; the `RMCSetYellowcard` stub 0x835e20 is called
     from 0x6441b0.
- Dirty cop: `RMCBecomeDirtyCop` stub 0x4ba2a0, called from 0x770da0, from 0x768250, from the server
  dispatcher 0x693780.

---------------------------------------------------------------------------------------------------

## 10. Death and the switch to police

Server function **0x6bb910** (argument: client index; reached from `ZGameRulesFragileAllianceSv` slot 7 =
0x827f00 through 0x80ad60):
- per-client record of 0x74 bytes at `[rules+8]`: +0 the client's object, +0xc a byte cleared here,
  +0x10 the player index to respawn as.
- `bBecomePolice` starts as 1. Only when global 0x168e59c == 2 (ASSUMPTION: a game-mode value) and the
  client's flags lack 0x8 does it become 0.
- If the client's flags have 0x100: set 0x200 and choose
  `record.playerIndex = 0x6ee860(clientIndex, bBecomePolice ? 3 : 2, 0)`. Otherwise only set 0x100.
  (ASSUMPTION: 0x100 = "has died once".)
- **0x6ee860** walks the session's player table (0x6161c0 on global 0x168e598; 12-byte entries,
  `ZFFPlayer*` at +4, in-use byte at +9) and returns the **first** entry that exists, is not in use, and
  whose `ZFFPlayer`+0x273c byte equals the requested type; it marks it in use. -1 if none.
- Then the `RMCRespawn(bBecomePolice, record.playerIndex, followClient)` wrapper 0x63a0a0, and the
  `RMCAnnounceFASpawnPolice` wrapper 0x795470 the first time.
- `ZGameRulesFragileAllianceSv` slot 11 (0x46bd40) calls the `RMCSetPoliceMan` and `RMCFARespawnData(fRespawnTime)`
  wrappers; slots 4, 10, 127 also `RMCSetPoliceMan`; slot 10 `RMCSpawn`.

So the police "character" is a pre-placed player entity of type 3 in the level, and the server hands out
the first free one. Type 3 also appears in `ZGameRulesFragileAlliance` slot 34 (`cmp byte [x+0x273c], 3`).

Already present and reusable for a choice: `DDL_ZClient.m_iRespawnPointSelect` (int8),
`RMCSetRespawnIndex(iClientIndex:int8)` (one int8, named so in the DDL; stub 0x5caf00, called from 0x531ee0, from 0x530da0, from the client-object
dispatcher 0x7825a0), `RMCSetRespawnFollowCam`, `RMCSyncAvailTeamModeSpawnpoints`, and the input actions
`TeamSpawnNext`, `TeamSpawnPrev`, `TeamSpawnAccept` in the default key map string.

---------------------------------------------------------------------------------------------------

## 11. The owner's four goals

### A. Private peer-to-peer sessions with friends
- Plausible: **yes, and mostly already built.** Sessions are Steam lobbies, traffic is Steam P2P between
  the members, no Quazal or Eidos server appears in that path (section 3), and a friends-only lobby type is
  selected by session property bit 4.
- To patch: possibly nothing. If the menu does not expose the private flag, force lobby type 1 at
  0x8e5169..0x8e5173 (`xor edx,edx / cmp / sete dl / inc edx / push edx`), or set the bit in the property
  block before 0x8e4fe0 runs. 0x8e4fe0 is one of the CEG-named functions: patch in memory from KLHook and
  check that it still runs.
- Depends on Valve still serving the old lobby and P2P interfaces for this app id: outside this exe,
  **not established**.
- Cheapest experiment (needs the owner and one friend; owner's stage 4): host a private Fragile Alliance
  game from the stock menu on stock files and join by Steam invite. If that works, the goal is met and what
  remains is that both players hold the same grafted maps (section 5).

### B. Jittery / spinning characters
- Plausible: **yes**; the parameters are plain globals in writable `.data`, written once by 0x4825b0.
- To patch (no code change; KLHook writes after 0x4825b0 has run, i.e. after the Net-Z start-up 0x7ee0c0):
  - `[0xd35424]`, `[0xd3545c]` min interval for player position / heading: 100, try 33;
  - `[0xd35420]`, `[0xd35458]` forced refresh: 2000, try 250 (bounds H1 to a quarter second);
  - floats at 0x168f440 (position tolerance squared, 400.0) and 0x168f4b0 (heading, 900.0): smaller;
  - the same four for actors (0xd34664/8, 0xd34684/8, 0x168f1e4, 0x168f244) if AI jitters too.
  Only the *sender's* values matter, so both players need the hook; a hooked player already looks better to
  an unhooked one. Cost: more upstream packets.
  A real fix for H1 would cap extrapolation time on the receiver or resend the end of a turn; that needs
  code, in 0x600eb0 or in the model read 0x992f10.
- Cheapest experiments, in order: (1) launch with `-o DisableSyncChange2` and see whether remote movement
  changes at all - it is a switch the developers left in 0x600eb0; (2) the interval writes above;
  (3) to tell H1 from H2, log `m_iAngle` (object +0x60) of a remote player when a spin is seen: a value near
  +-32768 means H2, an ordinary value with a long gap since the last update means H1.
- Not established: that these are the cause. The evidence is that the mechanism can produce both symptoms.
  All of this needs two machines to observe; Arcade mode will not show it.

### C. A more believable betrayal mechanic
- Plausible: **yes, on the host alone** for the rule itself, because the decision is taken in the server
  rules class (0x41d480) and clients are told through existing messages. A host with changed rules stays
  wire-compatible with unpatched clients as long as only existing RMCs and flags are used.
- To patch: the conditions at the top of 0x41d480, its callers (what counts as betrayal), and the
  yellow-card path (0x6441b0, not yet read). Tunable numbers may live in the level object
  `ZOnlineFragileAllianceSettings` rather than in code (other tracks cover that object).
- Cheapest experiment: log at 0x41d480 in a local Arcade round (ASSUMPTION: Arcade runs the same `Sv` rules
  class) and record the arguments and flag values for each event (friendly fire, human shield, taking
  money, killing). That turns the flag bits and slot 149 from unknown to known without any network.

### D. Choosing a police character after dying
- Plausible: **yes**, and small. The choice is one call: 0x6bb994 / 0x6bb9a1 call 0x6ee860(client, type, 0).
- To patch: replace the first-free pick with "the entry the client asked for, if free and of the right
  type, else first free". The request can ride on something that already exists (`m_iRespawnPointSelect`
  or `RMCSetRespawnIndex`), so no new message is needed and an unpatched client simply never asks.
  The client side needs a selection screen; the team-spawn inputs exist.
  The pool of choices is the set of type-3 player entities placed in the level, so "which cops exist" is a
  level-content question, not a netcode one.
- Cheapest experiment: in a local round, log the table that 0x6ee860 walks (index, type byte at
  `ZFFPlayer`+0x273c, in-use byte) at the first police respawn. That shows how many police entities a stock
  map has.

---------------------------------------------------------------------------------------------------

## 12. Open questions, most useful first

1. Does a memory-patched exe still create and join sessions (CEG, 0x873500)? Blocks B, C, D online.
2. Where is `m_szVersion` compared and what makes join code 3 "Clash"? Decides whether modded and stock
   players can meet, and whether `m_iAvailableLevels` (16 bits) gates a map beyond the stock list.
3. Which caller of 0x6300f0 is the per-frame one, and is `[ZSessionManagerMultiplayer+0x158]` changed
   after construction?
4. Meaning of the policy pairs (250, 1000) / (50, 250) and of global 0x1691d40 in the model.
5. The flag bits (0x1, 0x2, 0x4, 0x8, 0x20, 0x40, 0x80, 0x100, 0x200, 0x10000) used by 0x41d480 and
   0x6bb910.
6. The yellow-card / friendly-fire path to traitor.
7. Is RC4 or compression enabled on the Net-Z streams?
8. Does the game survive the host leaving?
9. Do `StartAsServer` / `StartAsClient` work without a lobby (would give a two-instance test bench)?

---------------------------------------------------------------------------------------------------

## Appendix B. Steam vtable offsets used

ASSUMPTION: names from the Steamworks SDK headers of the `SteamMatchMaking008` / `SteamNetworking003`
generation, matched to the offsets by argument count and by the literal keys passed.

`ISteamMatchmaking`: +0x10 RequestLobbyList, +0x30 CreateLobby(type, maxMembers), +0x34 JoinLobby(id),
+0x40 GetNumLobbyMembers, +0x44 GetLobbyMemberByIndex, +0x4c SetLobbyData(id, key, value),
+0x64 SendLobbyChatMsg, +0x68 GetLobbyChatEntry, +0x6c RequestLobbyData, +0x78 SetLobbyMemberLimit,
+0x84 SetLobbyJoinable.
`ISteamNetworking`: +0 SendP2PPacket(id, data, len, sendType), +4 IsP2PPacketAvailable, +8 ReadP2PPacket,
+0xc AcceptP2PSessionWithUser, +0x10 CloseP2PSessionWithUser, +0x14 GetP2PSessionState.
`ISteamUser`: +8 GetSteamID. `ISteamFriends`: +0 GetPersonaName.

## Appendix A. The game's DDL, decoded from kl2.exe

Each tree starts with the magic `CD 65 23 12`, then u8 2, then big-endian u32 18, 0, 1885, 114, then a
namespace = u32 count + elements. Strings are u32 BE length + bytes. Element = u8 type + body:
0x13 unit (declaration, name, string); 0x04 dataset (declaration, namespace of 0x06); 0x06 variable
(name, name, type reference = u8 + string, u32 array size); 0x03 DO class (declaration, parent string, u32,
namespace of 0x06 and 0x08); 0x08 remote method (declaration, parameter namespace, a second copy of it);
0x0d parameter (name, name, type reference, u32, type reference, u32, u8); 0x0b property (declaration, u32,
u32); 0x11 simple type (declaration). A declaration = name, name, unit name, u32 property count + properties.
Every tree with the 2,18,0,1885,114 stamp parses with this grammar and ends before the next object in
`.data`; two of the three Net-Z-internal trees use further element types and were not decoded.
In the lists below `x:int16[3]` is an array of three.

### DDL_Defines  (kl2.exe 0xd1be60..0xd1bebe)


### DDL_Types  (kl2.exe 0xd1bf38..0xd1cb37)

- dataset `DDL_String` [update_perf_counter basic_update_protocol]: m_szContent:string
- dataset `DDL_Int64Reliable` [update_perf_counter basic_update_protocol]: m_iContent:int64
- dataset `DDL_UInt64Reliable` [update_perf_counter basic_update_protocol]: m_iContent:uint64
- dataset `DDL_Int32Reliable` [update_perf_counter basic_update_protocol]: m_iContent:int32
- dataset `DDL_UInt32Reliable` [update_perf_counter basic_update_protocol]: m_iContent:uint32
- dataset `DDL_Int16Reliable` [update_perf_counter basic_update_protocol]: m_iContent:int16
- dataset `DDL_UInt16Reliable` [update_perf_counter basic_update_protocol]: m_iContent:uint16
- dataset `DDL_Int8Reliable` [update_perf_counter basic_update_protocol]: m_iContent:int8
- dataset `DDL_UInt8Reliable` [update_perf_counter basic_update_protocol]: m_iContent:byte
- dataset `DDL_BoolReliable` [update_perf_counter basic_update_protocol]: m_bContent:bool
- dataset `DDL_FloatReliable` [update_perf_counter basic_update_protocol]: m_fContent:float
- dataset `DDL_VectorReliable` [update_perf_counter basic_update_protocol]: m_vecContent:int16[3]

### GenericNetObject  (kl2.exe 0xd1cb68..0xd1cee4)

- dataset `DDL_SGenericNetData` [update_perf_counter basic_update_protocol]: m_arr_bool:bool[5], m_arr_int32:int16[8], m_arr_float:float[5], m_arr_vec3_x:int16[5], m_arr_vec3_y:int16[5], m_arr_vec3_z:int16[5]
- **DO class `DDL_ZGenericNetObject`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_iGeomRef:DDL_UInt16Reliable, m_Data:DDL_SGenericNetData

### SimpleNetObject  (kl2.exe 0xd1cf20..0xd1d31b)

- dataset `DDL_ZSNOActionMarker` [basic_update_protocol]: m_iActionMarker:int8, m_iVerticalOffset:int16, m_iFadeDistIn:uint16, m_iFadeDistOut:uint16, m_iColor:uint32
- **DO class `DDL_ZSimpleNetObject`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_iGeomRef:DDL_UInt16Reliable, m_vecPos:DDL_VectorReliable, m_bIsActive:DDL_BoolReliable, m_ActionMarker:DDL_ZSNOActionMarker, m_iData:DDL_Int32Reliable, m_bInUse:DDL_BoolReliable

### NetWeapon  (kl2.exe 0xd1d350..0xd1db75)

- dataset `DDL_SWeaponDropData` [update_perf_counter basic_update_protocol]: m_vecDropPos:int16[3]
- **DO class `DDL_ZFFItemWeapon`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_bActive:DDL_BoolReliable, m_iFFWeaponRef:DDL_UInt16Reliable, m_DropData:DDL_SWeaponDropData, m_iProjectilesInMagazine:DDL_UInt16Reliable, m_iProjectilesOutsideMagazine:DDL_UInt16Reliable
  - 5 RMCs (the `RMC` prefix dropped): SetAmmoInside(iAmmo:uint16), SetAmmoOutside(iAmmo:uint16), SetDropData(x:int16, y:int16, z:int16, iAmmoInMag:uint16, iAmmoOutside:uint16), WantPickUpWeapon(iClientIndex:int8), WantPickUpAsAmmo(iClientIndex:int8)

### NetServer  (kl2.exe 0xd1dba8..0xd251a2)

- simple type `DDL_ZServerPerfCounterStats`
- dataset `DDL_ZServerClientPlayers` [update_perf_counter basic_update_protocol]: m_iPlayerIndex:int8[12], m_iTwoHandedWeapon:int8[12]
- dataset `DDL_ZServerCoopWeaponCarryOver` [update_perf_counter basic_update_protocol]: m_bCarriedOver:bool, m_ePlayerWeapons:int8[4], m_ePlayerAmmo:int16[4]
- **DO class `DDL_ZServer`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_iScenarioIndex:DDL_Int8Reliable, m_iNextScenarioIndex:DDL_Int8Reliable, m_szServerMap:DDL_String, m_szVersion:DDL_String, m_iNATStatus:DDL_Int8Reliable, m_iConnectedClients:DDL_UInt16Reliable, m_szName:DDL_String, m_iGameType:DDL_UInt8Reliable, m_iConnectionType:DDL_UInt8Reliable, m_iMinPlayers:DDL_UInt8Reliable, m_iMaxPlayers:DDL_UInt8Reliable, m_iGameRulesState:DDL_Int8Reliable, m_iSessionState:DDL_Int8Reliable, m_iCoopDifficulty:DDL_Int8Reliable, m_iUnrankedRandRank:DDL_UInt32Reliable, m_ClientPlayers:DDL_ZServerClientPlayers, m_CoopCarryOver:DDL_ZServerCoopWeaponCarryOver
  - 113 RMCs (the `RMC` prefix dropped): LoadCurrentMap(), QuitGame(), SetClientPlayerIndex(iClientIndex:int8, iPlayerIndex:int8), ScheduleCheckPointSave(), ScheduleCheckPointLoad(), ScheduleCheckPointLoadInit(), toClientsCoopCPLoad_START(iCheckPointIndex:int8), toServerCoopCPLoad_DONE_Local(iClientIndex:int8), toClientsCoopCPLoad_DONE_ALL(), StartCutSequence(refCutSequence:uint32), SkipCutSequence(rMiniCut:uint32), SetGeomActive(iGeomRef:uint16, bActive:bool, bParent:bool), SetActorActive(iActorRef:uint16, bActive:bool, bShootIntoGroundOnActivate:bool, bCheckIfDeadOnInactivate:bool), SetVehicleActive(iVehicleRef:uint16, bActive:bool), SetHeliActive(iHeliRef:uint16, bActive:bool), HeliFireWeapons(iHeliRef:uint16, iTargetRef:uint16), HeliSetAttackProfile(iHeliRef:uint16, iAttackMode:int8, iAttackWhen:int8), KickDoorRequest(iPlayerIndex:int8, iKickDoorRef:uint32), KickDoorAutomatic(iKickDoorRef:uint32, bKickingBackSide:bool), KickDoorSetActive(iKickDoorRef:uint32, bSetActive:bool), ShotActivateApplyDamage(iGeomRef:uint16, iTargetGeomRef:uint16, iDamage:int16), RemoteShotActivateApplyDamage(iGeomRef:uint16, iTargetGeomRef:uint16, iDamage:int16), BarrelEffectsApplyDamage(iGeomRef:uint16, iOwnerRef:uint16, iDamage:int16, x:int16, y:int16, z:int16), RemoteBarrelEffectsApplyDamage(iGeomRef:uint16, iOwnerRef:uint16, iDamage:int16, x:int16, y:int16, z:int16), BarrelEffectsChangeInvulnerability(iGeomRef:uint16, bInvulnerable:bool), RemoteBarrelEffectsChangeInvulnerability(iGeomRef:uint16, bInvulnerable:bool), OnlineMoneyContainerOpenStart(iGeomRef:uint16), OnlineMoneyContainerOpenDone(iGeomRef:uint16), OnlineMoneyControllerActivate(iRef:uint16, bCanBePickedUp:bool), PickupThrowableRequest(iPlayerIndex:int8, iObj:uint32), BehaviourTriggerEvent(iGeomRef:uint16, iParam:int8), DropMoney(iClientIndex:int8, iMoney:uint32), BuyWeaponPack(iClientIndex:int8, iPrimaryWeapon:int8, iSecondaryWeapon:int8, iProtectionSuit:int8), PlayerBoards(iClientIndex:int8, iPIPRef:uint32), AnnounceFAPlayerDeath(iClientIndex:int8, bPlayerPoliceMan:bool, iKillerClientIndex:int8, bKillerPoliceMan:bool), AnnounceFAPlayerResurrected(iClientIndex:int8, iHealerClientIndex:int8), AnnounceFAPlayerLeavesLevel(iClientIndex:int8), AnnounceFAPlayerEntersBank(iClientIndex:int8, iPIPRef:uint32), AnnounceFAPlayerExitsBank(iClientIndex:int8, iPIPRef:uint32), AnnounceFAPlayerBoarded(iClientIndex:int8, iPIPRef:uint32), AnnounceFAPlayerEscapedWithMoney(iClientIndex:int8, bLastPlayerEscaped:bool), AnnounceFAMissionReminder(iClientIndex:int8), AnnounceFACashMajority(iClientIndex:int8), AnnounceFAAllianceReminder(iClientIndex:int8), AnnounceFAPoliceKillPolice(), AnnounceFAEscapeVehicleHit(iClientIndex:int8), AnnounceFAEscapeVehicleHeavilyDamaged(), AnnounceFAEscapeVehicleDestroyed(), AnnounceFAEscapeVehicleArrived(), AnnounceFAEscapeVehicleLeaving(), AnnounceFATraitor(iKillerClientIndex:int8, iDeadClientIndex:int8, bFirstTime:bool), AnnounceFADirtyCop(iDirtyClientIndex:int8), AnnounceFATimeReminder(iMinutesRemaining:int8), AnnounceFALastPossibleTransport(), AnnounceFATimeExtended(), AnnounceEscAndPlayerDead(), AnnounceEscAndPlayerDeadPolice(), AnnounceUCCOneLeft(), AnnounceUCCLost(), AnnounceUCCWon(), AnnounceUCCCrimeCommitted(bAnnounce:bool), AnnounceUCCKilledBeforeCrimeCommitted(), AnnounceShareWithDriver(iClientIndex:int8), AnnounceTeamDeadCriminal(iClientIndex:int8, bBigLoot:bool), AnnounceTeamDeadPolice(iClientIndex:int8), AnnounceTeamLastMerc(), AnnounceDirtyCopRevenge(iKillerIndex:int8, iDeadClientIndex:int8, bPersonal:bool), AnnounceTeamMoneyGoneQuit(), AnnounceTeamCashMajority(iClientIndex:int8), AnnounceTeamCashMajorityPolice(iClientIndex:int8), AnnounceCnRSuddenDeath(), AnnounceFATimeOut(), AnnounceFALastPlayerEscaped(), AnnounceFALastPlayerDied(), AnnounceFALastPlayerDisconnected(), AnnounceFAPerfectSplit(), AnnounceFANumPlayersLeft(iNumPlayers:int8), LootingStarted(), SetCustomFlagsOnServer(iPlayerIndex:int8, iFlags:int32), UnsetCustomFlagsOnServer(iPlayerIndex:int8, iFlags:int32), SetYellowcard(iClientIndex:int8, iDamageDealerIndex:int8), SetDamageDealer(iPlayerIndex:int8, iDamageDealer:int8), UnsetDamageDealer(iPlayerIndex:int8, iDamageDealer:int8), AddAssistAtServer(iPlayerIndex:int8), SetOneTeamDisconnected(val:bool), PlayVehicleDoorAnim(rVehicle:uint32, eDoorAnimType:int8, bOpen:bool), StartPerfCounterCapture(captureID:uint32, captureEndTime:uint64), ReturnPerfCounterCapture(captureID:uint32, stationID:uint32, stats:DDL_ZServerPerfCounterStats), CoopAirlockRequest(iPlayerIndex:int8, refCoopAirlockGeom:uint16), CoopAirlockComplete(refCoopAirlockGeom:uint16, refEntityA:uint16, refEntityB:uint16), CoopAirlockCompletedOnServer(refCoopAirlockGeom:uint16, refEntityA:uint16, refEntityB:uint16), CoopAirlockActivate(refCoopAirlockGeom:uint16), CoopAirlockAbortRequest(iPlayerIndex:int8, refCoopAirlockGeom:uint16), OnlineTriggerSync_toServer_Triggered(iOnlineSyncGateref:uint32, iCheckPointIndex:byte), OnlineTriggerSync_toClients_TriggerAll(iOnlineSyncGateref:uint32, iCheckPointIndex:byte), StartCrashAnimation(), ShareWithDriver(iClientIndex:int8), HoldEscapeVehicle(iClientIndex:int8), AnnounceHoldEscapeVehicle(iClientIndex:int8), ResetEscapeVehicle(rEscVehicle:uint32), SynchronizeVehicleHitpoints(rEscVehicle:uint32, fHitpoints:int16), SynchronizeVehicleEffectsHitpoints(rEscVehicle:uint32, fHitpoints:uint16), RemoveSharableMoney(iClientIndex:int8, iMoney:uint32), SetKillMarked(iClientIndex:int8, bVal:bool, iType:int8), SetLastMercKilledUCCIndex(iClientIndex:int8), BecomeTraitor(iClientIndex:int8, iVictimIndex:int8), BecomeDirtyCop(iClientIndex:int8, rPlayer:uint16, iVictimIndex:int8), ActorDied(rActor:uint32, rKiller:uint32), SyncAvailTeamModeSpawnpoints(iAvailSpawnpoints:uint32), RealSyncAvailTeamModeSpawnpoints(iAvailSpawnpoints:uint32), UCCMissionFailed(bUCCMissionFailed:bool, bUCCAIHostile:bool), SetDropMoneyDirty(rMoneyController:uint32, bDirty:bool), TriggerMissionCompleted()

### NetActor  (kl2.exe 0xd251d8..0xd27e11)

- dataset `DDL_ZRagdollData` [update_perf_counter basic_update_protocol]: m_bActive:bool, m_bInMotion:bool
- dataset `DDL_ZAnimationData` [upon_request_filter update_perf_counter basic_update_protocol]: m_iAnimHeaderRef:int32, m_iAnimCon:int32, m_fStartFrame:float, m_fEndFrame:float, m_fAnimSpeed:float
- dataset `DDL_ZAttachedToData` [upon_request_filter update_perf_counter basic_update_protocol]: m_iGeomRef:uint16, m_iBoneId:byte
- dataset `DDL_STargetInfo` [update_perf_counter basic_update_protocol]: m_iTargetRef:uint16, m_iVision:uint16
- dataset `DDL_SActorPositionData` [unreliable extrapolation_filter update_perf_counter]: m_vecPos:int16[3]
- dataset `DDL_SActorAngleData` [unreliable extrapolation_filter update_perf_counter]: m_iAngle:int16
- dataset `DDL_SActorGeneralData` [unreliable update_perf_counter basic_update_protocol]: m_iASHCurrentStateId:int16, m_iASHTargetStateId:int16, m_iASHFaceState:int8, m_iAimMode:int8, m_iHitPoints:int16, m_bShootIntoGround:bool, m_iMSSetNr:int8, m_iMSPrefferedState:int16, m_bMSKeepVariations:bool
- **DO class `DDL_ZFFActor`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_iRef:DDL_UInt16Reliable, m_bDropedWeapons:DDL_BoolReliable, m_PositionData:DDL_SActorPositionData, m_AngleData:DDL_SActorAngleData, m_bOnPathfinder:DDL_BoolReliable, m_GeneralData:DDL_SActorGeneralData, m_iActorState:DDL_Int8Reliable, m_TargetInfo:DDL_STargetInfo, m_RagdollData:DDL_ZRagdollData, m_AttachedToData:DDL_ZAttachedToData
  - 27 RMCs (the `RMC` prefix dropped): ReceiveHit(m_refOwner:uint16, m_eDamageType:byte, m_refWeaponTemplate:uint16, m_iDamage:int16, m_iHeadshot:bool), MoveToPosition(iToX:int16, iToY:int16, iToZ:int16), MoveToPositionWithContinuityBreak(iPosX:int16, iPosY:int16, iPosZ:int16, iAngle:int16), ServerForcePosition(iPosX:int16, iPosY:int16, iPosZ:int16, iAngle:int16), TeleportToPosition(iPosX:int16, iPosY:int16, iPosZ:int16, iAngle:int16), InterpolateToPos(iPosX:int16, iPosy:int16, iPosz:int16, iAngle:int16, iFramesQuant:uint16), PullWeapon(iIndex:int8), HolsterWeapon(iIndex:int8, iReason:byte), FireWeapon(iNumShots:byte), ForceStopFire(), FireThrowWeapon(iWeapon:int8, iNumShots:byte), ReloadWeapon(iWeaponRef:uint16), AimAtTarget(iObjRef:uint16, fXOffset:int16, fYOffset:int16, fZOffset:int16, fDelay:float, iBoneId:byte), AimAtPos(fXPos:int16, fYPos:int16, fZPos:int16, fDelay:float), RemoveAimAt(), LookAt(iObjRef:uint16), StartHumanShield(iAttackerRef:uint16), RealStartHumanShield(iAttackerRef:uint16), EndHumanShield(bDie:bool, bAddBool:bool), RealEndHumanShield(bDie:bool, bAddBool:bool), ActivateAnimSegment(iAnimHeaderRef:int16, iAnimCon:int16, fStartFrame:int16, fEndFrame:int16, fAnimSpeed:float), DeactivateMoneyController(), ResetMinicut(), BlowHeadOff(), CoverInfoSetIndex(iCoverIndex:int16), CoverInfoSetState(iCoverState:int8), CoverInfoSetPeek(iCoverPeek:int8)

### NetScores  (kl2.exe 0xd27e48..0xd28e7c)

- dataset `DDL_ZScoreDeathmatchContainer` [upon_request_filter basic_update_protocol]: m_iFrags:uint16[12], m_iDeaths:uint16[12]
- **DO class `DDL_ZScoreDeathMatch`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_Container:DDL_ZScoreDeathmatchContainer, m_iMaxFrags:DDL_UInt16Reliable
- dataset `DDL_ZScoreFragileAllianceContainer` [update_perf_counter basic_update_protocol]: m_iTotalRewardMoney:uint32[12], m_iTotalLootMoney:uint32[12], m_iBestGrab:uint32[12], m_iKillerIndex:int8[12], m_iRating:int8[12], m_iKills:int8[12], m_iPoliceKills:int8[12], m_iAssists:int8[12], m_iTrust:int8[12], m_iSharableMoney:uint32[12], m_iUnsharableMoney:uint32[12], m_iPlaystyleKillPoints:int16[12], m_iCustomFlags:int32[12], m_iNumRoundsEscapedAsMerc:int8[12], m_iNumRoundsEscapedAsTraitor:int8[12], m_iNumMercsKilled:int8[12], m_iNumTraitorsKilled:int8[12], m_iNumRoguesKilled:int8[12], m_iNumOthersKilled:int8[12], m_iNumPersonalRevenges:int8[12], m_iPlayStyleMasks:int8[12], m_iExperience:int16[12]
- dataset `DDL_SEscapeState` [update_perf_counter basic_update_protocol]: m_iEscapeSeqState:int8, m_fEscapeSeqTimer:float, m_iEscapeSeqTransportRef:uint16, m_iEscTransportState:int8
- dataset `DDL_SRoundProgress` [update_perf_counter basic_update_protocol]: m_iRoundTime:int16, m_iRemainingRoundTime:int16, m_iCurrentRound:int8, m_iRoundOverTime:int16, m_iGameOverTime:int16, m_iRoundEndTimer:int16
- **DO class `DDL_ZScoreFragileAlliance`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_Container:DDL_ZScoreFragileAllianceContainer, m_iNumRounds:DDL_Int8Reliable, m_fRoundTime:DDL_FloatReliable, m_fRemainingRoundTime:DDL_FloatReliable, m_iCurrentRound:DDL_Int8Reliable, m_fRoundOverTime:DDL_FloatReliable, m_fGameOverTime:DDL_FloatReliable, m_fRoundEndTimer:DDL_FloatReliable, m_iEscapeSeqState:DDL_Int8Reliable, m_fEscapeSeqTimer:DDL_FloatReliable, m_iEscapeSeqTransportRef:DDL_UInt32Reliable, m_iEscTransportState:DDL_Int8Reliable

### NetFFPlayer  (kl2.exe 0xd28eb0..0xd2ea4a)

- dataset `DDL_ZFFPlayerDeathInfo` [update_perf_counter basic_update_protocol]: m_iRefKiller:uint16, m_fXDiePos:int16, m_fYDiePos:int16, m_fZDiePos:int16, m_fDamage:int8, m_bHeadshot:bool, m_bDead:bool
- dataset `DDL_SInventoryItems` [basic_update_protocol]: m_iItem:int8[5], m_iRef:uint16[5]
- dataset `DDL_SInputData` [unreliable update_perf_counter basic_update_protocol]: m_iInputFlags:uint16
- dataset `DDL_SMoveInputData` [unreliable extrapolation_filter update_perf_counter]: m_iMoveFrontBack:int8, m_iMoveSides:int8
- dataset `DDL_SContinuousData` [unreliable extrapolation_filter update_perf_counter]: m_iPlayerAngle:int16, m_vecPos:int16[3], m_iCamYAngle:int16, m_vecFireAimPos:int16[3], m_iHitPoints:int16
- dataset `DDL_SPlayerAngleData` [unreliable extrapolation_filter update_perf_counter]: m_iAngle:int16
- dataset `DDL_SPlayerPositionData` [unreliable extrapolation_filter update_perf_counter]: m_vecPos:int16[3]
- dataset `DDL_SPlayerCamAngleData` [unreliable extrapolation_filter update_perf_counter]: m_iCamAngle:int16
- dataset `DDL_SPlayerFireAimPosData` [unreliable extrapolation_filter update_perf_counter]: m_vecFireAimPos:int16[3]
- dataset `DDL_SPlayerHitPointsData` [unreliable extrapolation_filter update_perf_counter]: m_iHitPoints:int16
- dataset `DDL_SPlayerCoverData` [basic_update_protocol]: m_iSide:int8, m_iCorner:int8, m_iPrevCoverBoxIndex:int16, m_iCoverBoxIndex:int16
- **DO class `DDL_ZFFPlayer`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_iMaxHitPoints:DDL_UInt16Reliable, m_iPlayerIndex:DDL_Int8Reliable, m_iClientIndex:DDL_Int8Reliable, m_iFlags:DDL_UInt16Reliable, m_iWeaponInHand:DDL_Int8Reliable, m_iActiveMovement:DDL_UInt16Reliable, m_iAdvancedDamageFlags:DDL_UInt16Reliable, m_iDownNotDeadFlags:DDL_UInt16Reliable, m_Position:DDL_SPlayerPositionData, m_Angle:DDL_SPlayerAngleData, m_CamAngle:DDL_SPlayerCamAngleData, m_FireAimPos:DDL_SPlayerFireAimPosData, m_DeathInfo:DDL_ZFFPlayerDeathInfo, m_Inventory:DDL_SInventoryItems, m_InputData:DDL_SInputData, m_MoveInputData:DDL_SMoveInputData
  - 87 RMCs (the `RMC` prefix dropped): PickupThrowableObjectConfirmed(iObj:uint16), PickupThrowableObjectPerform(rObject:uint16), ThrowObject(rObject:uint16, iPosX:int16, iPosY:int16, iPosZ:int16, rTarget:uint16, bAiming:bool), ThrowWeapon(rWeapon:uint16, iPosX:int16, iPosY:int16, iPosZ:int16, bDiscardWeapon:bool), DropThrowableObject(rObject:uint16), GrenadeSync(iGrenadeRef:uint16, iPosX:int16, iPosY:int16, iPosZ:int16, iVelX:int16, iVelY:int16, iVelZ:int16), ThrowableSync(iGrenadeRef:uint16, iPosX:int16, iPosY:int16, iPosZ:int16), SetCover(iCoverBox:int16, iPrevCoverBox:int16, iSide:int8, iCorner:int8, eSwitch:byte), OnCoverLeave(), LeaveCover(bSkip:bool, bForward:bool), ReceiveHit(m_refOwner:uint16, m_eDamageType:byte, m_refWeaponTemplate:uint16, m_iDamage:int16, m_iMomentum:int16, m_bHeadshot:bool), ReceiveStressBreaking(rOpponent:uint16, iTimeOffset:int16), ReceiveStressBreakingOnDuplicas(rOpponent:uint16, iTimeOffset:int16), StressBreaking(refOpponent:uint16, bRetaliate:bool, bAutoHit:bool), PopPill(), CheckPulse(), StopCheckPulse(), Suicide(), StopSuicide(), TalkToLynch(), StressBreakEffectKane(), TrackKill(bIsPlayer:bool), TrackDownNotDeadCoopKill(), TrackExplosionKill(), ResetPisolKills(), Resurrected(bWeaponChange:bool), SetMaxHitPoints(iMaxHitPoints:uint16), UpdateHitPoints(iHitPoints:uint16), SetGhost(bGhost:bool), SetSpectating(bSpectating:bool), SetPoliceMan(bPoliceMan:bool), SetUndercoverCop(bUndercoverCop:bool), SetTraitor(bTraitor:bool), SetInvulnerable(bInvulnerable:bool), SetActive(bActive:bool), SetHidden(bHidden:bool), MoveToPositionWithContinuityBreak(iPosX:int16, iPosY:int16, iPosZ:int16, iAngle:int16), ServerForcePosition(iPosX:int16, iPosY:int16, iPosZ:int16, iAngle:int16), TeleportToPosition(iPosX:int16, iPosY:int16, iPosZ:int16, iAngle:int16), ConfirmPickUpWeapon(iWeaponRef:uint16, bShakeCam:bool, bForce:bool), ConfirmPickUpAsAmmo(iWeaponRef:uint16), PickUpWeapon(iNewWeaponRef:uint16, iOldWeaponRef:uint16), PickUpAmmo(iWeaponRef:uint16), ChangeWeapon(iWeapon:byte), RemoveItem(iWeaponRef:uint16, iItemWeapon:int8), KickDoorConfirm(iKickDoorGeom:uint32), KickDoor(iKickDoorGeom:uint32, iBackSide:bool), CoopAirlockConfirmed(refCoopAirlockGeom:uint16, iPositionIndex:int8), CoopAirlockEnter(refCoopAirlockGeom:uint16, iPositionIndex:int8), CoopAirlockAbortConfirmed(), CoopAirlockAbort(), StartHumanShieldPvP(iAttackerRef:uint16), RealStartHumanShieldPvP(iAttackerRef:uint16), EndHumanShieldPvP(bDie:bool), RealEndHumanShieldPvP(bDie:bool), ResetHumanShieldPvP(), RealResetHumanShieldPvP(), ReleaseHumanShieldPvPCarrier(bDie:bool), RealReleaseHumanShieldPvPCarrier(bDie:bool), ReleaseHumanShieldPvPShield(bDie:bool), RealReleaseHumanShieldPvPShield(bDie:bool), ReleaseHumanShieldNPC(bKill:bool), SetLeftShoulder(bLeftShoulder:bool), PullHimDown(rPlayer:uint16), SetHumanShieldPvPTapsShield(fTaps:float), SetHumanShieldPvPTapsCarrier(fTaps:float), HumanShieldPvPResetStruggle(), GrabShieldWeapon(), ThrowHumanShield(), ExecuteHumanShield(), VaultOverCover(bLeft:bool, iPosX:int16, iPosY:int16, iPosZ:int16, iAngle:int16), ReservePlayerCover(iCoverId:int32), ReleasePlayerCover(), ReceiveCloseCombat(rOpponent:uint16, iTimeOffset:int16), ReceiveCloseCombatOnDuplicas(rOpponent:uint16, iTimeOffset:int16), CloseCombat(refOpponent:uint16, iMode:int8, bAutoHit:bool), DownNotDead_SetDowned(rWhatDownMe:uint16), DownNotDead_SetInsulted(bInstantResponse:bool), DownNotDead_DoRespondInsult(), DownNotDead_GettingUp(), SetAblativeHitpoints(fVal:float), DeathCycleTimeout(), DeathCycleOnResurrectRequest(), DeathCycleOnResurrectBegin(), DeathCycleOnResurrectCompleted(), DeathCycleMiniGameProgressUpdate(fProgr:float), HeliChangeSeat()

### NetClient  (kl2.exe 0xd2ea80..0xd3258f)

- dataset `DDL_SThrowGrenadeData` [update_perf_counter basic_update_protocol]: m_iWeaponRef:uint16, m_vecProjectileStartPos:int16[3], m_vecProjectileTarget:int16[3], m_iPlayerIndex:int8
- dataset `DDL_ZOnlineUserID` [update_perf_counter basic_update_protocol]: m_aContent:uint64[5]
- dataset `DDL_ZTrustHistory` [update_perf_counter basic_update_protocol]: m_iTrustHistory:int8[25]
- **DO class `DDL_ZClient`** : RootDO [userdo globaldo]
  - datasets, in declaration order: m_szName:DDL_String, m_iRank:DDL_Int8Reliable, m_iNATStatus:DDL_Int8Reliable, m_iConnectedClients:DDL_UInt16Reliable, m_bSoftVersion:DDL_BoolReliable, m_iLeaderboardStatusFlags:DDL_UInt8Reliable, m_iTeam:DDL_Int8Reliable, m_TrustHistory:DDL_ZTrustHistory, m_iTotalTrust:DDL_Int16Reliable, m_iTotalPlaystyle:DDL_Int8Reliable, m_iTotalExperience:DDL_Int16Reliable, m_iUseMask:DDL_Int8Reliable, m_iClientIndex:DDL_Int8Reliable, m_iRMCPlayerIndex:DDL_Int8Reliable, m_iOnlineServiceID:DDL_ZOnlineUserID, m_iClientSessionState:DDL_Int8Reliable, m_iReadyForPlay:DDL_Int8Reliable, m_iAvailableLevels:DDL_UInt16Reliable, m_iAvailableCampaignLevels:DDL_UInt16Reliable, m_iProtectionSuit:DDL_Int8Reliable, m_iPrimaryWeapon:DDL_Int8Reliable, m_iSecondaryWeapon:DDL_Int8Reliable, m_iRespawnPointSelect:DDL_Int8Reliable
  - 70 RMCs (the `RMC` prefix dropped): SetClientIndex(iClientIndex:int8), SetPlayerIndex(iPlayerIndex:int8), SetPrevRoundTraitor(bPrevRoundTraitor:bool), SetTeam(iTeam:int8), SetTeamWithBalanceCheck(iTeam:int8), Disconnect(iReason:int8), Spawn(bSpawnAsGhost:bool), Reload(iWeaponRef:uint16, iPlayerIndex:int8, iAmmoInMagazine:int8, iAmmoOutsideMagazine:int16), DMRespawnData(fRespawnTime:float), FARespawnData(fRespawnTime:float), Respawn(bBecomePolice:bool, iRespawnPlayerIndex:int8, iFollowClientIndex:int8), SetRespawnIndex(iClientIndex:int8), SetRespawnFollowCam(iClientIndex:int8), FADeathCam(bActivate:bool, bRespawn:bool, bFollow:bool, iKillerIndex:int8, rKiller:uint32), ActivateFAEscapedMenu(bActivate:bool), DMResurrect(), SetPrimaryWeapon(iWeapon:int8), SetSecondaryWeapon(iWeapon:int8), SetProtectionSuit(iSuit:int8), AnnounceFARevenge(bKiller:bool), AnnounceFAPersonalRevenge(iClientIndex:int8), AnnounceFARevengeRejected(bKiller:bool), AnnounceFAPersonalRevengeRejected(bKiller:bool, iClientIndex:int8), AnnounceFAEscape(), AnnounceFACashAddict(), AnnounceFARoundCompleted(bEscaped:bool, bRoundWinner:bool, bGameLeader:bool, bTraitor:bool, iRoundMoney:int32, bLastRound:bool, bEscapedAllRounds:bool, bStartedRoundLowest:bool), AnnounceFADirtyMoney(), AnnounceFADroppedMoney(), AnnounceFAShotOffMoney(bDamageDealer:bool), AnnounceFAJackPot(), PlaySoundFASuckMoney(bPlay:bool), PlaySoundFASuckMoneyDone(), PlaySoundFAPoliceSuckMoneyRejected(), AnnounceFATookMoney(), AnnounceFAShotMerc(), AnnounceFASpawnPolice(), AnnounceFARespawnMerc(), AnnounceFAPipeBomb(), AnnounceFANinjaLooter(bKatana:bool, bVase:bool), AnnounceFAFrontRunner(), AnnounceFANottingham(iStall:int8), AnnounceFAAllowance(iRegister:int8), AnnounceFACasinoJackpot(iSlotMachine:int8), AnnounceFASecretFile(), AnnounceFARunLikeHell(), SetGameMode(iGameMode:int8), SetYellowcardBlinking(bBlinking:bool), ResetYellowcard(iClientIndex:int8, iDamageDealerIndex:int8), ResetYellowcardOnDamageDealer(iClientIndex:int8, iDamageDealerIndex:int8), IncrementTeamRevengeKills(iDeadClientIndex:int8), ResetTeamRevengeKills(iDeadClientIndex:int8), IncrementTeamRevengeDeaths(iKillerIndex:int8), ResetTeamRevengeDeaths(iKillerIndex:int8), AnnounceShareWithDriver(), ShowShareWithDriver(bShow:bool), AnnounceDirtyCopKilled(), AnnounceTeamOneMercLeft(), AnnounceFollowCam(), AnnounceUCCFirstKill(), AnnounceUCCPoliceShootingUCC(), AnnounceTeamAlliance(iClientIndex:int8), AnnounceTeamAlliancePolice(iClientIndex:int8), ResetCheapCamFX(), AnnounceTeamRevengeReward(iClientIndex:int8), AnnounceUCCCrimeCommitted(), AnnounceUCCKilledBeforeCrimeCommitted(), OnDownedYellowcardKill(), UnlockAchievement(iAchievementID:int32), TrackEscapeVeryFastDLC(fRoundTimePassed:float), TrackEscapeAsLastDLC(bEscapedLast:bool)

### mercs  (kl2.exe 0xd325d8..0xd3261e)


### OnlineServiceBroker  (kl2.exe 0xd32650..0xd328b3)

- **DO class `DDL_ZOnlineServiceBroker`** : RootDO [userdo globaldo]
  - datasets, in declaration order: 
  - 1 RMCs (the `RMC` prefix dropped): ProcessMessage(msg_type:uint16, msg_payload:qBuffer)
