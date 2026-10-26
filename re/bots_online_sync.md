# Online FA: do all peers see the same cops and objects? (2026-10-26)

Owner, 9-instance System Link round on a Dead Men map: "the ai they dont even look remotely synced up", meant the COPS ("completely
different on each screen"); "they all need to be in the same position for everything to be fair"; "this goes for any object".
Static reading of kl2.exe 0490 + the L9b / L4 logs + a class census of the level archives. NOTHING here has run live.
Code: `klhook/klsync.c` ([Sync], read-only), `tools/kl_syncdiff.py`. Builds: `klhook/out_botsync_1026a` (SHIP), `out_botsync_1026a_test` (TEST).

## 1. What is verified (CERTAIN)

- Every peer loads the whole level and so holds its OWN copy of every ZFFActor. L9b host (role 2) and client (role 3) both log
  `round census: 71 ZFFActor, 7 team Ally (7 alive, 0 with tactics), 64 other teams` (botfill census, `KL_PortTools/build/klhook/solo/L9b/inst1|inst2`).
  So the hypothesis "each peer has its own copy" is true. Cops are not spawned by the host and sent: they are level data.
- Dead Men FA (DM01 = `KLExpansion/Maps/DM01/F01_Main.zip`) carries 71 ZFFActor (68 ZSoldier + 3 ZCivilian), 32 ZSquadScript, 21 ZSpawnPoint,
  0 OnlineSpawnpointTrigger. Stock F01 carries 49 ZFFActor (36 + 13), 30 squads, 45 spawn points, 2 OnlineSpawnpointTrigger (census by
  `kl_fa.census`, 2026-10-26). So both the stock and the converted maps have level-loaded actors; the DM map simply has more of them.
- My first theory (a stock FA level uses Dog Days' net-sync entities which our graft drops) is WRONG. Stock F01 has NO ZOnlineTriggerSync_*,
  ZOnlineSyncGate, *NetSync, ZGenericNetObjectController (class names are the exe's; none occurs in F01/F03; F03 has one HeliNetSync). Stock
  FA maps are plain TriggerBox2 / RandomTrigger / TriggerDelay2 / KickDoorMonitor / OnlineMoneyContainer scripts. Their sync is the exe's.
- Role split in the exe (CERTAIN, disassembly): session manager `sm=[0x168e598]`, role `[sm+0x54]` 2 host / 3 client, mode `[sm+0x5c]==4` FA.
  Host-only logic skips on role 3: ZSquadScript 0x47e440, ZGatePath, ZRelayPath, ZSquadModifierBehaviour, ZShootAtTrigger,
  ZAnimatedVehicleMonitor, ZSoldier orders 0x760e50, ZCivilian, ZWounded, ZLieWounded; ZFFActor slot 192 (0x676ec0) sets `[actor+0x8fc]=1` on a
  client. Net-aware (call 0x863a60 "networked"): ZTriggerBox, ZTriggerActorsDead, ZTriggerLootDepleted, ZKickDoorMonitor, ZAIMonitor,
  ZHavokShatter(+Glass), ZHavokCar, ZHeli, ZHavokVehicleInstance, ZAnimatedVehicle, ZSceneChanger, ZLevelBound, ZKillBox, ZFFItemWeapon,
  ZRandomTrigger, ZTriggerDelay(2). The cop is therefore designed as: simulated on the host only, replicated to clients as `DDL_ZFFActor`
  (`re/netcode.md` 593: position int16[3] unreliable + extrapolation filter, angle, anim state ids, hit points, target, 27 RMCs). The object
  is addressed by its 16-bit scene ref `m_iRef`, so all peers must have the same entity order.
- Our hooks do not touch cops online: klbot, klescort, klbalance, klbotdown and friends are Arcade-only by construction (inert in role 2/3);
  klnet / netsmooth only read unless `[Net] Tune=1` (it was 0 in L9b). klbotfill is read-only. kllobby only changes the lobby target.
  The one thing that CAN change which actors exist is `[Bots] OnlineFillSquads` (off in L9b/L9c).

## 2. What is NOT verified, and so what the verified cause is

I could NOT prove offline why the cops differ. The honest status of the possible causes, most likely first:

| # | cause | status | what decides it |
|---|-------|--------|-----------------|
| A | The clients DO run the cop AI (the role-3 skips do not cover the path the DM scripts use: a TriggerBox2 / RandomTrigger / spawn chain that activates squads on every peer, or `ZAIMonitor` / ZSpawnPoint dynamic spawning) and the replicated position is applied only as a correction, or not at all | GUESS, most likely | `Compare` shows a cop drifting apart from the first seconds; `[Census]`-style per-peer cop counts differ (spawn points create cops locally) |
| B | The DDL_ZFFActor of a level actor is not bound between peers (scene refs differ because the peers load different entity orders, or the actor's DO is created lazily and never matched), so clients show their own local walkers | GUESS | slot N has the same class/team on all peers (the probe prints it) but different positions from t=0, no host correction at all |
| C | Dynamic cops (ZSpawnPoint / OnlineSpawnpointTrigger waves) are created locally with peer-local random choice (RandomTrigger / TriggerDelay2 are net-aware but the DM scripts have 47 RandomTrigger, 78 TriggerDelay2, 34 OnlineSpeakTrigger that Dog Days' FA maps lack) | GUESS | slots present on one peer only (`one side only` in kl_syncdiff) |
| D | A hook of ours writes AI state online | RULED OUT by reading (Arcade-only / read-only), not by a run | the L9b log has no such write |

What I can say is CERTAIN: the cops are level data on every peer; sync can only come from the exe's host/replica split, and the logs so far
(L9b/L9c) never listed a cop's place on more than one peer, so nobody has YET measured a divergence. The probe below measures it.

## 3. The probe and the host list (klsync.c)

`[Sync] Probe=1` (any peer): every `Every` ms in an online round (state 0x13..0x1f) it logs `sync: list T=<wall-clock ms> role .. state ..` then
`sync: s=<slot> c=<class> t=<team> p=x,y,z hp=<health> f=<flag>` for every ZFFActor, then for the other kinds, ending `sync: list end`.
Slot = entity table slot = the same object on every peer. Class = RTTI name. Kinds after the actors: moneycontainer, kickdoor, shatter,
havokcar, heli, animatedvehicle, vehicleonspline, rigidbody, itemweapon, pickup, throwable, grenade (scripts excluded). `f` of an actor is the
byte `[actor+0x5cd]` (GUESS, meaning unknown, logged to be compared). Other kinds only log the place (GUESS: `kle_node([obj+4])` works for them;
`p=none` where not); a state field per kind (door open, glass broken, container depleted) is the next step once the first bench shows
which kinds differ at all.
`python tools/kl_syncdiff.py <host KLHook.log> <client logs...> [--tol 1.0]` lines the blocks up by T and prints per client: objects on one side
only, farther than tol, health differing, by class, worst slots.
`[Sync] Share=1` (host) broadcasts the actor list on UDP 27415 every `ShareMs`; `[Sync] Compare=1` (client) logs once a second
`sync: vs host: N actors compared (host list X ms old), M farther than Tol, K with another health, worst slot S d=..` plus the first 8 offenders
with both positions. That is the live "same cop at the same place" test. A moving cop differs by speed x list age (about 3 units a second x 0.25-0.5 s).

Acceptance: at one moment the same slot has the same class, team, health and a position within about 1.5 units on the host and every client,
for every cop, for 60 s. `M` stays near 0 and `one side only` is 0.

## 4. Why there is no fix key yet (and what it will be)

A fix chosen before the cause is measured would be a guess written into a running game. The candidates, by cause:
- A (clients simulate): make the client behave like the stock role 3 for the paths the DM scripts use; the exe has the gate (0x863a60 / 0x4b0a40),
  the fix is data: give the DM scripts the net-aware classes that stock FA uses for the same job (the graft step, `kl_fa.py` / `kl_fa_bots.py`),
  or a hook that makes the offending class check the role. Which class it is shows in the first diff (the first slot that diverges, and its team / squad).
- B (unbound): the entity order must be identical; check `kl_convert` / graft for anything that sorts or filters per peer (it is deterministic
  offline, so this would be a runtime load-order difference, e.g. an optional sub-archive).
- C (local spawns): replace local random in the spawn scripts by the host-only form (`OnlineSpawnpointTrigger`, which the DM map has 0 of).
- Generic fallback for any cause: the host snaps client actors with a position push. The exe has the network send of a teleport (`0x62a900`
  teleports the actor; the send is `0x47d840(DO=[actor+0x8d8], float pos[3], uint16 angle)` which calls `0x68b070`, a function guarded by
  `0x905460` and `0x9425a0` (master check) - it looks like the ZFFPlayer path, NOT verified to be the ZFFActor ServerForcePosition RMC). Calling it blind
  from the host every few hundred ms could also reset animation (the teleport resets `[[actor+0x7c0]]`). Left unwritten; `Compare` first.
- A dedicated host (`[Server] Enable`, `re/online_server.md`) changes nothing here: the server is still a game process whose own copy of the
  level is the authority; it only removes the host's player as a variable and gives a stable machine to run the probe on.

## 5. Object kinds: how Dog Days syncs each, and whether we break it

"Stock" = the exe's own mechanism read from the role gates and RTTI above. "Ours" = our DM conversion or hooks. All rows are UNMEASURED until
the probe has run; what is CERTAIN is marked.

| kind | stock online sync | broken by our conversion / hooks? | fix / probe |
|------|-------------------|------------------------------------|-------------|
| Cops, guards (ZSoldier) | host-simulated (squad scripts skip role 3), replicated DDL_ZFFActor (CERTAIN design) | UNKNOWN (see 2); hooks no (CERTAIN: Arcade-only) | probe s=slot t=team; Compare; section 4 |
| Civilians (ZCivilian) | host-simulated, replicated | UNKNOWN, same path | same probe (3 in DM01, 13 in F01) |
| AI heisters (7 Ally) | present on every peer, no tactics online (`0 with tactics`, CERTAIN from L9b); they only walk | by design: not replicated heisters in the stock online game | second item; cannot be made loot-taking online without new code (`re/bots_online_fill.md`) |
| Loot / money (OnlineMoneyContainer, OnlineMoneyCtrl) | the container is a level object; money state through the score DO (`DDL_ZScoreFragileAlliance`) and TriggerLootDepleted (net-aware) | DM01 has 1 OnlineMoneyContainer + 306 OnlineMoneyCtrl vs stock F01 58 + 183: another loot model (briefcases / statues via Ctrl) | log container positions; check `ZTriggerLootDepleted` fires on all peers (round end text) |
| Doors (KickDoor + Monitor) | KickDoorMonitor is net-aware | DM01: 7 KickDoor, 31 KickDoorBehaviourRout, 0 KickDoorMonitor (stock F01 6): doors have no net-aware monitor | probe kind kickdoor positions; add monitors in the graft if they diverge |
| Glass / shatter (HavokShatter) | net-aware (ZHavokShatter, Glass); stock has *NetSync classes for some | DM01 10 vs F01 12; no NetSync entity | probe; broken state needs the per-kind flag (next step) |
| Vehicles, escape van (ZAnimatedVehicle, OnlineEscAnimatedVehicle, OnlineEsc*) | host-driven, ZAnimatedVehicleMonitor skips role 3, ZAnimatedVehicle net-aware | DM01 has 1 + 4 ZHavokCar + 2 OnlineVehicleOnSpline (new classes, F01 has 0) | probe havokcar / animatedvehicle; escape state is in `DDL_SEscapeState` (stock) |
| Helicopter (ZHeli, HeliNetSync) | HeliNetSync | DM01 has no heli | n/a |
| Physics props (ZHavokRigidBody) | not synced as such except where a *NetSync or the class is net-aware (ZHavokVehicleInstance) | DM01 45 + 11 HavokDynamicsExtend vs 19 | cosmetic, last; probe rigidbody positions |
| Pickups / grenades / dropped weapons (ZFFItemWeapon) | DDL_ZFFItemWeapon (own DO) | untouched | probe itemweapon |
| Players | DDL_ZFFPlayer (own DO), CERTAIN stock | untouched (looks via klcharonline) | not in scope |

## 6. Bench for the next LAN run

1. All instances: `[Sync] Probe=1`, `Every=3000`; host also `Share=1`; clients `Compare=1`. TEST build is not required (SHIP has the same code).
2. After the round: `python tools/kl_syncdiff.py <host log> <client logs>`; read `one side only`, `farther than tol`, the worst slots.
3. First client `sync: vs host` line: M = 0 early and growing = clients simulate (A); M > 0 from the first list with no convergence = unbound (B);
   slot on one side only = local spawns (C).
4. Report which cops (slot, team, class) differ first; that picks the fix of section 4.
