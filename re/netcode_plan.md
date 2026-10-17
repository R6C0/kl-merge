# Netcode plan: private matches on a Dead Men map, and the remote 'spin' (2026-10-17, audit track; OFFLINE, NOTHING BUILT OR RUN)

Builds on re/netcode.md and re/netcode_fa.md (sections 1-5 read, 6-9 only by heading). It is a PLAN; GUESS marks what is not established.

## 1. How a private match starts a Dead Men map today
- The host replicates a SLOT INDEX (0..8 = F01..F09), never a map name. Each machine maps it through its own level list (host 0x6c536f, client 0x491fd1).
  klslot's redirect (F0x -> Maps\DMxx) sits below that, so it acts the same on every machine that runs it.
- `[Redirect.N]` needs the page latch, which the game drops before the online menu, so online games load STOCK maps. Stage 0 needs no new code:
  `[Expansion] Page=2` on BOTH machines, identical tree and hook, invite-only private game; the host picks Airport=F03 (Withdrawal), Subway F01 (Hot Coffee),
  Bridge F02 (Late Night), Fish Market F04 (Park), Harbor F06 (Retomoto; single-part maps first).
- HAZARD (no guard exists): with Page=2 forced, Quick Match or a public lobby loads a Dead Men map against a stranger's stock map. No level-hash or version
  check was found (0x53919c throws the version text away). Private lobbies only until stage 1.
- AI parts are inert online (they test ZGameRulesHeist; online uses ...FragileAllianceSv/Cl). Online FA has no AI heisters; the fed return is the game's own rule.

## 2. Hook changes (concrete)
1. `[Net] OnlineSafe=1` (default 1): one helper `kl_online()` (rules class is not ZGameRulesHeist / session is not Arcade). Every part that writes game state returns early when it is true.
   - klgun.c (~line 365) tests only the game type and WOULD write gun looks online: add the guard before the variant-byte writes.
   - kljoin.c (Retomoto jump) has no mode test; its debug jump request (gamedata+0x8d4 = 5, [0x156b358] = 1) would desync online: same guard.
   - klfreeclimb.c, kldown.c, klclimb.c: NOT confirmed to test the rules class (the AI parts are). GUESS they act online and move a body peers only see through position updates: audit and guard.
   - klchar (wardrobe) is local-only (peers see the stock model): harmless, log it.
2. `[Net] Log=1`: wire klnet.c (exists, unwired). Logs role / lobby / private bit / update numbers (check N1). Zero risk.
3. `[Net] Tune=1` (+ `TuneClient=1` on a joined machine): klnet.c's twelve numbers. Host-only in a game-made friends-only lobby.
4. `[Net] Fingerprint=1` (stage 1, new code): lobby data key = hash of (hook version, tree manifest). The host sets it; a joiner refuses a lobby that differs or lacks it.
   Done by an ISteamMatchmaking proxy at import slot 0xb107d8 that also forces CreateLobby to type 1 and fails RequestLobbyList while Page=2 is on.
   Cheaper alternative (GUESS it works): the game's own "everybody has this map" availability gate (state machine 0x6c49a0, m_iAvailableLevels, 0x7ca830 / 0x73f270).
5. Redirect from lobby data (stage 1): the host publishes the DMxx name, clients redirect from it, Page=2 goes away and the stranger hazard with it. New code.

## 3. The spin
Read in netcode_fa.md 4: heading is sent at most every 100 ms, only when the receiver's prediction is off by more than 10.5 degrees, unreliable; the receiver
extrapolates linearly with no cap (0x992f10) for up to 2 s. One lost heading packet leaves a body turning or sliding on its old rate.
- By data now (stage 0b): `[Net] Tune=1 PlayerMs=50 RefreshMs=300 AngTol=12` as in netcode_fa.md 5, and `-o DisableSyncChange2`. Which direction of AngTol helps is a GUESS: test 6 and 12.
- Needs code: cap the extrapolation (clamp at 0x992f10 to about 250 ms of velocity, then hold position) and send the heading on a heartbeat (every 500 ms even inside the dead band).
  Wrap through a private copy, never patch .text in place; host side first. GUESS: the cap alone removes most of the visible spin.

## 4. What one PC can test alone
- Alone: klnet Log=1 in the online menu (create a private game on a STOCK map, sit in the lobby, leave) = check N1, including whether one player can start (the session line prints players min..max);
  harness tests of the OnlineSafe guard with a faked rules class; static reading.
- Not possible alone: two instances. Steam runs one instance per account (SteamAPI_RestartAppIfNecessary is imported) and peers are addressed by Steam id.
  `-o StartAsServer/StartAsClient` (0x8733e0) and System Link (frontend.xml line 5354, create at 0x77e220, no Steam lobby) might let two PCs meet without a lobby: NOT ESTABLISHED.
- Needs a second player (luvsic owns both games): stage 0 (index -> redirect on host and client, a whole round on a grafted map, the session-end Steam block lines = N2),
  stage 0b (spin keys = N3), stage 1 (a mismatched peer is refused).

## 5. Order and risks
S (klnet Log=1, owner alone) -> OnlineSafe guards (offline) -> stage 0 with luvsic on Withdrawal -> 0b spin keys -> stage 1 fingerprint + redirect from lobby data -> wardrobe online -> Retomoto online last.
Risks: peers on different builds desync or crash silently (no version check); stats and leaderboard writes on a grafted map (klsteam blocks them when the archive is not stock; confirm with N2 before the owner hosts).

## Addendum (fix round 2026-10-17): unverified items and what one PC can test
UNVERIFIED (static reading or inference only): the Page=2 latch being dropped before the online menu; that klfreeclimb.c / kldown.c / klclimb.c act online (no rules-class test was found in them, GUESS); the extrapolation cap at 0x992f10 as the cure for spin; the ISteamMatchmaking proxy at import slot 0xb107d8; the availability-gate alternative (0x6c49a0, 0x7ca830, 0x73f270); klgun.c ~365 and kljoin.c lacking a mode test (line numbers drift with edits; re-grep before patching).
ONE PC CAN TEST: hook compile check; offline behaviour of any new guard (a guard that turns a part off when the rules class is the online one can be exercised only where that class is reachable, which needs a lobby); the [Net] Tune keys' log lines on a private lobby the host alone opens; harness tests of a pure extrapolation-cap function.
NEEDS A SECOND PLAYER: stage 0 (identical tree and hook on both machines, redirect on host and client, a whole round on a grafted map), whether remote bodies still spin with the cap, desync from the debug jump request, and the session-end Steam block lines.

## Implemented 2026-10-17 (not run)
Plan items 2.1 and 2.2, in klhook/. Compiled only (SHIP build, no new warnings) into <work>\build\klhook\net_1017; nothing installed, no game ini touched.
- `kl_online()` (klhook.c, after klh_rd32): reads `[Net] OnlineSafe` (default 1) once. 1 when session [0x168e598] role [+0x54] is 2/3 (server/client), or game type [+0x5c] == 4 and the rules object [[0x168e9e4]+0x54] has a vtable other than ZGameRulesHeist 0xbd3514. This is the test klb_read / klr_arcade already make. No session / story mode / unreadable = 0, so offline and with the key absent nothing changes.
- Guards: klgun.c (before the variant-byte writes, after the Arcade-only test; the dirty flag stays set), kljoin.c (before the box loop, so no [gamedata+0x8d4] / [0x156b358] write; said once), klfreeclimb.c (no climb STARTS online; it had no mode test at all; one already running is let finish).
- Audited, already inert online: klclimb.c (klq_tick passes klb_read, Heist only), kldown.c (klr_arcade). klchar.c (wardrobe) is local-only: not stopped, logged once.
- 2.2 `[Net] Log=1`: klnet.c was ALREADY wired (klhook.c includes it, klnet_init / klnet_tick) and reads Log from [Net]; nothing to add.
- GUESS: role 2/3 only ever occurs in a network session (never seen live online); the klfreeclimb "finish a running climb" choice; the guards were never exercised with a real online rules class.
