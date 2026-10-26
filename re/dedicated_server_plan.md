# Dedicated server: what exists, how to bench it, and how the host could become authoritative (2026-10-26)

Static reading + the bench files in `C:/kl_build_1024/server_1026/`. NOTHING here has run live. Implemented: nothing (design only).

## 1. What [Server] does today (klhook/klserver.c, re/online_server.md)

- There is NO headless or dedicated binary. `[Server] Enable=1` makes an ordinary kl2.exe, WITH a window and a GPU, drive its own menus
  to host a Quick Match (`Mode=quick`, public Steam lobby) or Ranked (`Mode=ranked`, lobby type 3) Fragile Alliance lobby, wait `WaitSec`
  for `MinPlayers`, lower the lobby target and let the game's countdown start the round, then host again `RehostSec` after the round.
- The host's own player is still a normal seat in the round (stands at its spawn, nothing spectates it). So "does the host run without a
  local player": no. Windowed: yes, it needs a window (minimised may stall, GUESS). It must be launched WITHOUT `-o DefaultScene` (the bench does).
- It uses the Steam lobby path only (QuickPlayerMatch / XBoxLiveCreateRanked). It does not use System Link. Never run live.

Consequence for the bench: two or more kl2.exe on ONE PC share one Steam account/ID, so they cannot meet through Steam lobbies. The proven
multi-instance route is System Link (UDP broadcast on LAN). Therefore the bench SV1/SV2 below is a "dedicated-like host" over System Link:
the host process creates the lobby, waits for all peers (`waitpeers`), presses Ready, then does NOTHING in the round (no mouse input; its
player stands at the spawn like a server's seat). That reproduces what a server does to the sync question (an idle authoritative host
process); it does not test [Server]'s menu driver. SV0 is the separate one-instance smoke of the menu driver (Steam path, GUESS that it works
with a lone instance; it only checks that the log lines of re/online_server.md 4 appear up to `server: lobby open`).

## 2. Bench files (C:/kl_build_1024/server_1026/)

| file | what |
|------|------|
| SV1_host.ini / SV1_join.ini | stock map (OnlineSet=0 -> F01 slot), host `[Sync] Probe=1 Share=1`, clients `Probe=1 Compare=1`, n=3 |
| SV2_host.ini / SV2_join.ini | Dead Men map (OnlineSet=2 -> `LOAD F01: online=1 OnlineSet=2 -> page 2, rule DM01`), same sync keys, n=3 |
| SV0_server.ini | one instance, `[Server] Enable=1 Mode=quick`, menu driver smoke |

Built from S1 (known good System Link route) with: host `waitpeers 3 400000 20000` instead of a fixed wait, no host mouse input, ~190 s
observation in the round (probe every 3 s -> ~60 lists), joiner FALobby wait 90 s, AutoExit 780. The TEST build must contain klsync.c:
use `klhook/out_all_1026a_test` (checked: contains "sync: vs host"; `out_p12_1026b_test`, the L9d build, does NOT).

## 3. What the replication path is (CERTAIN unless marked)

- `DDL_ZFFActor` (`re/netcode.md` ~593) is a `userdo globaldo` object per ZFFActor: datasets `m_PositionData` (int16[3], unreliable +
  extrapolation filter), `m_AngleData`, `m_GeneralData` (anim state ids, hit points, aim), `m_TargetInfo`, ragdoll, plus 27 RMCs including
  `ServerForcePosition`, `TeleportToPosition`, `MoveToPosition`, `InterpolateToPos`. Addressed by `m_iRef` = scene ref, so peers need the same entity order.
- Host-only logic is gated by the role (`[sm+0x54]` 2 host / 3 client): ZSquadScript 0x47e440, ZSoldier orders 0x760e50, ZCivilian, etc. skip
  on role 3; ZFFActor slot 192 (0x676ec0) sets `[actor+0x8fc]=1` on a client (re/bots_online_sync.md 1). So by design clients mirror.
- That the creation site binds the DO to the level actor on the host and replicas on clients was never traced (netcode.md 6, ASSUMPTION).
  A host that is a dedicated process changes nothing here: the authority is the host's process either way (bots_online_sync.md 4, last bullet).

## 4. Decision tree for the first bench result (sync probe)

1. `sync: vs host` M (farther than Tol) ~0 for every cop for 60 s, `one side only` 0: the replication works; the owner's sighting was perception
   (clients' own animation/ragdoll, lag) or specific to 9 players. Then raise Every/compare under load (L9d-style n=9 with out_all build).
2. M grows from t=0 and cops walk different routes: clients simulate (cause A) -> design 5a.
3. M large from the first list, no convergence, cops static on clients: unbound DO (cause B) -> look at scene refs/entity order; 5a still covers it.
4. Slots on one side only: local spawns (cause C) -> `ZSpawnPoint` waves; 5b.
5. Stock map (SV1) fine and DM01 (SV2) bad: it is our conversion (DM scripts: 47 RandomTrigger, 78 TriggerDelay2, 0 KickDoorMonitor, 1 OnlineMoneyContainer); fix in the graft data, not in the hook.

## 5. Host-authoritative sync: concrete hook designs (NOT implemented)

a. Client-side snap ("Apply", the smallest thing that works for every cause). Everything needed exists: the host already broadcasts
   `slot, hp, pos[3]` per ZFFActor on UDP 27415 (klsync.c, `Share=1`), the client already receives and matches by slot (`Compare=1`).
   Add `[Sync] Apply=1 (recommended off)` on role 3 only: for each offender with d > `ApplyTol` (e.g. 3 units) and a live, non-player,
   non-ragdoll actor, call the game's own actor teleport `0x62a900(actor, rot[9], pos[3], a, b)` (wrapper `klt_teleport` in klcrew_rt.c, which
   already has the precondition checks of re/crew_talk_review.md 2.2 a). Rate limit (<= 4 actors per tick), only when the actor is not in an animation
   segment/cover (GUESS: flag `[actor+0x5cd]` or `[actor+0x7c0]` state, unknown), keep the client's yaw. Also copy hp when the host's is lower.
   Risks: the teleport resets `[[actor+0x7c0]]` (animation) so cops would stutter if d keeps exceeding the tolerance; positions are the unquantised
   floats so a static cop stays put. Players (team of the humans) must be excluded: client-authoritative. Needs the host list to carry team/flags (extend the packet).
b. Stop client simulation (cause A): the gate is `0x863a60` ("networked") and the role byte `[sm+0x54]`. A hook that makes the offending
   class's Update return early on role 3 (the class is named by the first diverging slot in the diff) is a code patch in a session-integrity
   range possibly (SessionSafe=1 refuses those). Prefer data: give the DM scripts the net-aware stock classes (kl_fa.py / kl_fa_bots.py).
c. "Role 3 for all actors on clients": setting `[actor+0x8fc]=1` (what slot 192 does on a client) on every ZFFActor of a client is a data write,
   SHIP-safe in form, but it only means something if the AI update reads that flag; whether it freezes local pathing is a GUESS to test with
   Compare (positions then follow only the UDP/DDL data).
d. Truly dedicated authority: the host process is the authority already. The remaining server-specific work is (i) a spectator/hidden seat
   for the server's own player (the fed machinery, not tried), (ii) a Steam-lobby bench on two PCs/accounts for the [Server] driver.

Recommended order: SV1 then SV2 (diverge or not, and which slot), then implement 5a behind `[Sync] Apply=0 (recommended off)` only if M is large.
