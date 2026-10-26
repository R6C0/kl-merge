# Undercover Cop sabotage + two UCCs (2026-10-26, static research; one module built, nothing run live)

Owner decisions 4-5 of `re/ucc_design.md`: look into ALL THREE sabotages (early police wave, van hold, door jam), each from a
UCC key press and not traceable to him; two UCCs who know each other at 9+ players. Read: kl2.exe 0490 (capstone over the
staged copy), the stock F01 level (`KL_PortBackup\Scenes\Locations\F01\F01_Main.zip`, read only, staged from the PC) with
`tools/kl_map_ai.py table` and a `kl_fa` listing. DD01 = stock F01 Subway (the page-0 redirect target). GUESS = my own guess.
Rules: no code patches (Steam CEG); data writes, game calls, private vtable copies only.

## 0. Short answers

| | mechanism | runs on | per-map data | status |
|---|---|---|---|---|
| (1) early police wave | shorten a RUNNING `ZTriggerDelay`/`ZTriggerDelay2` (one dword: deadline `+0x4c` = now), or fire a not-yet-fired wave box through the box's synced fire `0x6ae730` | HOST (squads are host-only; the clients see the cops through `DDL_ZFFActor`) | yes: which timers / boxes are "police waves" (DD01 table, section 2) | research; reads listed in 1.4 |
| (2) van hold | `[rules+0x1d8] += N` while the vehicle state `[rules+0x1dc]` is 1..4 (stock 'hold the driver' slot 152 does `+= 5.0`) | HOST | none (rules fields are the same on every map) | **BUILT** `klhook/klsabotage.c` `[Sabotage] VanHold=0`, harness `klsabot_test` 58/58; host-UCC only |
| (3) door jam | kick-door controller state `[ZKickDoorController+0x5c]` = 3 ("already kicked") for N s, then put back | HOST at least (the kick goes through an RMC whose authority side tests the state); every peer to be safe | yes: which doors (DD01: 7 glass doors of the vault control room) | research; reads listed in 3.4 |
| two UCCs | the Sv rules' slot 4 picks ONE client and stops; `SetUndercoverCop` is a MODE flag pair, not per player | HOST (private copy of the Sv rules vtable, wrap slot 4) | none | plan; blocked on seats 9-12 (section 5) |

Not traceable: none of the three writes announces anything (stock slot 152 announces `HoldEscapeVehicle`; we do not call it).
A CLIENT UCC's key cannot reach the host today; section 4 is the request channel plan. Until then only a hosting UCC can sabotage.

## 1. Early police wave

### 1.1 How waves start (static, map_ai.md 2 + this read)
- A wave squad has `ZSquadScript` field 3 = 0: its men are not in the world until one of its routs is named. Routs are named by
  boxes, by `ZTriggerDelay` / `ZTriggerDelay2` timers, by the `AIMonitor`'s round-start list and by chains.
- `ZSquadScript` 0x47e440 skips on role 3: the squads are simulated on the HOST only (re/bots_online_sync.md 1). Timers and boxes
  run on every peer.
- **`ZTriggerDelay` (vt 0xbc256c) and `ZTriggerDelay2` (vt 0xbc25fc) have the same run-time layout** (READ here, slots 25/26):
  `+0x24` entity, `+0x34` disabled, `+0x38` target list (vt +0x14 count, +0x34 get i), `+0x3c` delay (int s; float in TD2),
  `+0x40` random part, `+0x49` RUNNING, `+0x4a` done, `+0x4c` DEADLINE in `[[0xdd2640]+0x48]` units (1/1024 s), `+0x54` re-arm guard.
  Arm (slot 26: TD 0x8cc850 / TD2 0x71e250, 'AITrigger' word `[0x1688fa4]` / `[0x1688fa0]`): not disabled, not running, not done,
  clock >= +0x54 -> `+0x4c = now + round((delay + random*rand) * 1024)`, `+0x49 = 1`.
  Update (slot 25: TD 0x8ec330 / TD2 0x744c30): when networked only in session state 0x19; NO role test; fires when
  `clock > [+0x4c]`: `+0x49 = 0`, then 'AITrigger' to every list entry through the owner's vt +0x124.
- `ZTriggerBox` (vt 0xbc232c): synced fire `0x6ae730` = `[box+0x6c]` slot 3 (the network trigger sync) then slot 34 `0x45f5d0`
  (posts 'AITrigger' to the list; field 10 = -1 makes it one-shot by writing `+0x40 = 0`). re/triggerbox.md.

### 1.2 The sabotage
- **Variant T (timer, preferred):** on the host, find the running wave timers (`+0x49 == 1`, `+0x4a == 0`, `+0x34 == 0`) of the
  map's allow-list; take the one with the soonest deadline; write `+0x4c = clock + 1024` (one second). Its squad arrives on the
  next tick, exactly as when the timer ends normally. One aligned dword, heap data. The client copies of the timer still end at
  their stock time and send 'AITrigger' to a rout that does nothing on a client (GUESS: the rout's handler is host-only like
  `ZSquadScript`; read 1.4 b). So choose ONLY timers whose list names AI routs / other AI timers (no geometry, sound, camera).
- **Variant B (box, when no timer runs):** fire the map's next wave box through `0x6ae730` (synced: the clients get the trigger
  too). One-shot boxes are spent by it, as if the crew had walked in. `klbotfill.c` OnlineRampFire is the code pattern (it uses the
  unsynced `0x45f5d0`; use `0x6ae730` here). Not run live yet anywhere (BOS_DD02f is queued).
- Untraceable: the cops come from the level's own spawn places, the radio chatter is the squad's own. Cap: one sabotage per N s
  (GUESS 60 s) and never in the first 30 s of a round.

### 1.3 DD01 (stock F01 Subway) wave table, read from the stock .prp
Squads with soldiers: 14, all field 3 = 0 (spawn when named). `_HEIST` squads are `eHeistOnly` (dropped online, re/stock_map_bots.md).

| trigger (node) | class, field values | names | men | sabotage use |
|---|---|---|---|---|
| `Gameplay!tbEnterVault` (15592) centre (-3194,-2335,17976) | TriggerBox, one-shot, ECPS_FA_MERCONLY, ALL_MODES | `tdSwats` | - | B: start the vault wave now |
| `Gameplay!tdSwats` (15586) | TriggerDelay 20 s | `PoliceDogs#01\10_Defend`, `PolicePlatform#01\10_Defend`, `PolicePlatform#02\10_Defend`, `tdSwats#01`, `tdSwats#02` | 4 street cops (SMG) + dog | **T: the best first target** (20 s, list = AI only) |
| `Gameplay!tdSwats#01` (15590) | TriggerDelay 90 s | `SwatExit#02\11_RunToCover` | 3 SWAT (AK74, 175 hp) | T |
| `Gameplay!tdSwats#02` (15589) | TriggerDelay 100 s | `SwatExit#01\11_RunToCover` | 3 SWAT | T |
| `Gameplay!Timer_SwatMoreForward` (15591) | TriggerDelay2 15 s | `SwatExit#02\12_RunToCover` | (same 3, push forward) | T (pressure, no new men) |
| `Gameplay!tdPolice` (15583) | TriggerDelay 10 s, via `PlayerCount!tcPlayers#01` | `PolicePlatform#03\10_Defend` | 2 street cops | T |
| `Gameplay!tbPlatform_UCConly` (15598) centre (1105,-2249,18810) | TriggerBox, one-shot, **ECPS_FA_UCCONLY** | PoliceDogs#01, PolicePlatform#01/#02, SwatExit#01/#02 routs | 10 + dog | B: the stock "UCC brings the police" box. NOTE: the UCC walking there already fires it in stock (the census reads `[player+0x2729]`); `tbPlatform#01_MercOnly` at the same place fires for every heister, so it is no tell by itself |
| `Gameplay!tbNearVault_UCConly` (15594) centre (317,-2335,17505) | TriggerBox, one-shot, ECPS_FA_UCCONLY | `SGuard#01\Way#02`, `Timer_Wakeup` (TD2 10 s -> `SGuard#02\Way#01`) | 2 + 2 guards (pistol) | B (weak) |
| `Gameplay!tbExitStairs_MercOnly` (15585) centre (4697,-1230,26456) | TriggerBox, one-shot | `SwatStreet#01\10_Defend`, `SwatStreet#02\10_Defend` | 4 SWAT on the street by the van | B: the street wave before the crew reaches the van |
| `Gameplay!tbStreet_RespawnOnly` (15574) | TriggerBox, ECPS_FA_RESPAWNONLY (police players) | all of the above routs | - | do not use (a cop player's box) |
Timer seconds on F01 (all 59): mostly 0..20 s; the long ones are 90/100 (SWAT exits), 55 (train), 44/26 (platform cops move on).
Not police waves (never in the allow-list): `Blowout!*`, `MovingTrain*`, `PointOfIntrest!*`, `Audio!*`, `EscapeVan_Anim!*`,
`merc_bot_squad!Squad#0n\*` (the AI heisters' own timers).

### 1.4 Read in the exe before building (1)
a. How a timer's list entry resolves to a node (`[+0x38]` vt +0x34 get -> the owner's vt +0x124): needed to match a run-time timer
   to a table row by its target's REF label (names: the `[[obj+4]+0x6c]` path is klclubholster's GUESS and BOS_DD02r found no
   ZTriggerBox by the entity-table walk; the private-memory vtable scan of klbotfill's ramp probe found them).
b. The behaviour rout's AITrigger handler on a CLIENT (RunToCover 0x4ebed0 / Defend): does it return on role 3, or does it make a
   local show that later fights the host's replica? (The cop sync bench UCC2 says the clients mirror the host's 13 cops, so the
   stock timers firing on both sides is already the normal case: GUESS low risk.)
c. Whether `+0x4c` lower than "now" on the first pass after a write is enough (no other test in 0x8ec330 / 0x744c30: READ, yes).
Live test: UCC host on DD01, press after entering the vault: log shows the timer and its deadline, the four cops + dog arrive
~1 s later instead of 20 s; client log (klsync Compare) shows the same slots appear.

## 2. Van hold (BUILT, default off)

### 2.1 Facts (re/van_hold_online.md, re/bots_follow_out.md 1.6)
- Sv rules `[[0x168e9e4]+0x54]` (vt 0xbd2eb4 or klroundkeep's private copy: `KLH_RULES_SV_OK`): `+0x1dc` state (1/2 coming,
  3/4 waiting, 5 leaving, 6 destroyed, 7 cooldown, 0 idle), `+0x1d8` seconds left in the state (slot 195 counts down; 1/2 -> 3 and
  3/4 -> 5 at 0). Stock 'hold the driver' slot 152 0x8b3930: `+0x1d8 += 5.0` once per vehicle, with an announcement.
- Slot 192 0x5dff40 never ends the round while the state is 1..6: a hold cannot lose the round by the clock.
- The scripted hits while a human sits aboard are 10 per wait, fixed: a longer wait adds no scripted hits; police fire at the van's
  `FakeTarget` adds real ones (F01 has a FakeTarget on each of its 3 vans).

### 2.2 What `klsabotage.c` does
Host, game type 4, sub-mode 1, state 0x13..0x1f; the local ZFFPlayer has `+0x2729 == 1` (the UCC byte the pick writes, 5.1) and
`+0x2723 == 0` (not police); key `[Sabotage] Key` (default J, 0x4a) edge; state 1..4: `+0x1d8 += HoldS` (1..20, default 8), once
per visit (reset at state 0 / 7), never above 40 s, never lowered. No announcement, no voice. In 1/2 the van arrives later (it can
also stand at the stop with the state still 1/2: the board tactic only takes 1/2 under 2 s); in 3/4 the crew aboard waits longer
under fire. Test keys `AnyMode` (FA / C&R) and `AnyPlayer` (any host player) for a solo bench.
GUESS (the live check): the clients follow the host's state machine (the escape dataset `DDL_SEscapeState` m_iEscapeSeqState /
m_fEscapeSeqTimer is replicated); the HUD seconds on a client (`[score+0x58]`, slot 191) follow.
DD01 data: none needed (3 vans `Escape_Vehicle_01..03`, exit trigger `otrExitLevel` at (6855,-794,26051)).
Live test: `[Sabotage] VanHold=1 AnyMode=1 AnyPlayer=1`, Arcade is NOT covered (Arcade rules are ZGameRulesHeist, the gate
needs role 2); host a System Link FA lobby with one client, call the van, press J: host log `sabotage: VAN HELD: state 3, timer
6.2 -> 14.2 s`, the client's escape clock shows the extra seconds, the van leaves ~8 s later than stock. Then once in UCC.

## 3. Door jam

### 3.1 Facts (READ here)
- `KickDoor` controller = `ZKickDoorController` (vt 0xbc667c). Level fields at `+0x30..+0x58` (record +0x10 + 4): +0x34 field 1
  (=1 on F01), +0x3c the PathBlockers, +0x40 the door-leaf proxies, +0x58 `eBOTH_PLAYERS`.
- Run-time state `+0x5c`: slot 26 0x6d3e50: if 3, nothing; message `[0x168b3fc]` -> 0, 'AITrigger' (`[0x168b3b8]`) -> 1.
  0x735e70 (the kick): if not 3: `+0x5c = 3`, sends to the +0x3c list (path unblock) ... 0x8639e0 (the open, used by the RMC path):
  if 3 return. 0x6fdd5a..: an RMC handler (0x9425a0 "run here or send"): on the run-here side resolves the door by scene ref
  (0x8ccde0 -> 0x727960) and, `if [door+0x5c] != 3`, calls 0x8639e0.
- So every open path returns at state 3. **Jam = write 3, keep it N s, write back the value read before** (data only).
- AI heisters use the doors through `KickDoorMonitor` (net-aware) + `KickDoorBehaviourRout`; a jammed door blocks their route too.
- Owner's idea `DeactivateGeom` (vt 0xbc2ddc, slot 26 0x824950 on 'AITrigger' hides the listed geoms; `ActivateGeom` vt 0xbc2d4c
  puts them back): it REMOVES geometry; on the `KickDoor_Action_01` node it might remove the kick prompt but also the door's
  collision (GUESS), and no level node lists the doors, so the hook would have to build the message itself. The state write is simpler.

### 3.2 DD01 doors (stock F01)
The 7 glass doors of the vault control room `DL10_CtrlRoom\PC0400_DL10_Storage_Divider_Glas_Doors_0n` (n = 1..6, 8), each with
`KickDoor_Action_01`, `KickDoor_Pathblocker_01`, `Kickdoor_Blocker`; the 58 vault cases behind them are `ZOnlineMoneyCtrl`
field 11 = "behind a door" (cleared by the door's 'DoorOpened' relay). Monitors for the AI heisters: `merc_bot_squad!KickdoorMonitor!
KickDoorMonitor_Door01..04, 06, 08` (6).

| door | KickDoor node | place (x, y, z) |
|---|---|---|
| 01 | 2949 | (-3668, -2439, 17995) |
| 02 | 2973 | (-3668, -2439, 17496) |
| 03 | 2987 | (-3196, -2439, 17081) |
| 04 | 3001 | (-2694, -2439, 17081) |
| 05 | 3015 | (-2704, -2439, 18919) |
| 06 | 3029 | (-3206, -2439, 18919) |
| 08 | 2935 | (-3668, -2439, 18495) |
Which to jam: the one nearest the UCC's aim / the one the crew is walking to (by distance, no table needed beyond the list);
GUESS: jam all doors of the group within 15 m for N = 10 s.

### 3.3 Host vs client
The kick is a player action on the kicker's machine that reaches the door through the RMC above. GUESS: the run-here side for a
client's kick is the HOST (server-owned scene object), so a host-only jam blocks the real open; the kicker may still play his kick
animation. Safer: jam on every peer, which needs the host -> client channel (klhostopt lobby data, 5 s; too slow for a 10 s jam:
use a per-round "jam window" broadcast ahead, or the section 4 channel).

### 3.4 Read in the exe before building (3)
a. The start of 0x6fdd30 and its callers: which RMC (name in the DDL table) and which side runs it for a client's kick.
b. Every other reader of `+0x5c` of this class (state 0 vs 1 meaning: does the kick prompt require 1?) and the initial value.
c. `ZFFActionKickDoor` (vt 0xbb50b8): whether it tests the door state before offering the prompt (a state-3 door should show none).
d. The 'DoorOpened' relay: written only on a real open (so the money stays locked while jammed): GUESS yes.

## 4. A client UCC's key (needed by all three; not built)
- The host owns the effect; the UCC's machine must ask. Today the only hook channels are Steam lobby data / member data (klmm.c
  proxy, klcharonline.c `klx_look`, klhostopt.c `klx_opts`) and klsync's UDP 27415 (host -> clients, LAN only).
- Plan: the UCC's hook writes member data `klx_sab = <seq>:<kind>` (kind 1 wave, 2 van, 3 door); the host polls members every
  250 ms (pm_options.md 4), accepts a new seq only from the member whose client index has score flag 0x80 (the host's own flags),
  rate-limits, applies. The in-game view names nobody; a player inspecting raw lobby data with external tools could see the key
  change (acceptable GUESS; an obfuscated key name and a value that changes for every member every few seconds would hide it).
- Open: mapping a Steam member to a client index on the host (klcharonline.c's `i<idx>` is self-reported; check it against the
  session player table).
- The stock `RMCHoldEscapeVehicle` (a client aboard asks the host for slot 152) exists but announces and needs him aboard: not usable.

## 5. Two UCCs (plan only)

### 5.1 Where the single UCC is picked (READ, kl2 0490)
`ZGameRulesFragileAllianceSv` slot 4 = **0x40f870** (round start; calls the base 0x708500 which clears `+0x282..+0x285`). Block
0x40fa34..0x40fb74, only when `[0x168e59c] == 1`:
- `r = 0x8b66c0(0, n-1)` (random) with `n = [rules+0x14] - [rules+0x10]`; **override byte `[0xd1b3b4]`** (.data, 0xff in the file):
  a value 0..n-1 replaces r. A guarded data write of it on the host would choose WHO is the UCC (useful for tests).
- walk the 12 client records (stride 0x74, `edi < 0x570`), skipping unused ones (`[rules+0xc]` byte array), counting r down;
  at the chosen one: `0x601fd0(score=[rules+0x2c], idx, 0x80)` (OR into the score flags + dataset dirty 0x942b20 = REPLICATED),
  a stop byte (`[esp+0x13] = 1`: **exactly one**), then on `[rec+0x378]` (the ZFFPlayer, GUESS): 0x43e270(1), **0x4622b0(1) =
  `+0x2729 = 1`**, 0x644310(200.0 from `[0xd1b3bc]`); on `[rec+0x380]`: 0x432780(1), 0x5cf5f0(1), 0x745f20(200). `int3` at 0x40fb74
  if nobody was picked.
- Every later reader assumes one: slot 132 (vt +0x210) = **0x64c650** returns the FIRST client with 0x80 that is not police (8),
  dirty (0x1000) or dead (4), else -1. The round tick at 0x777272 (sub-mode 1): if slot 132 != -1 and `[rules+0x283] == 0` ->
  `SetUndercoverCop(1, 0)`.

### 5.2 Does a second `SetUndercoverCop(true)` work? No.
`SetUndercoverCop(a, b)` is NOT a per-player call: the RMC handler 0x418b20 lives on `[sm+0x84]` and ends in rules slot 187
**0x74d9f0: `[rules+0x283] = a; [rules+0x284] = b`** (mode state bytes; +0x283 also flips the crosshair colours for police,
re/fed_kit.md). Callers: 0x7772b2 (1,0) above, 0x5df310 (1,1), 0x7fade9, 0x53af17 (network receive). So it marks "a UCC is in
play" (GUESS for the meaning of a / b), and calling it again does nothing for a second player. **re/ucc_design.md P5's GUESS is wrong.**

### 5.3 How a second UCC would be made (host, no code patch)
1. klroundkeep.c already swaps a private heap copy of the Sv rules vtable (`klh_rules_vt2`): add slot 4 = our wrapper: call the stock
   0x40f870, then, in sub-mode 1 with >= 9 humans (owner: "9+"), pick a second used client != the first and repeat the per-player
   calls of 5.1 for it (0x601fd0 with 0x80, the five actor / player calls with the same arguments). Same function addresses, same
   arguments, same order: the stock pick is the template.
2. Knowing each other: our crew list already does it: `[HUD] UccHide` (klhud_values.c kluv_state) hides 0x80 only for viewers who
   are neither police nor 0x80, so each UCC sees the other as FED. The stock list strip (S1, slot 114 wrap) must keep the same rule.
3. Scoring: 0x4eb260 tests the flag per victim, so each UCC pays the bounty (`+0x674`, 200k / 400k per the owner) on his own.
4. To read first: all slot-132 users (`call [reg+0x210]` sites on a rules object; 189 raw `+0x210` sites, filter by the rules
   vtables) - mission success / failure (`FA_UCC_FailedMission`, `CrimeCommitted`, `KilledBeforeCrimeCommitted`, re/hud_popup.md)
   follow only the first live UCC; when he dies slot 132 returns the second (GUESS: the mission carries over, which is fine).
   Also what `[rules+0x10]` counts (the random range), whether the five actor calls replicate (they are setters on the player
   objects; the flag itself does replicate), and the UCC spawn set (`UCC_MERC`, 8 points on all 9 stock maps).

### 5.4 What blocks lobbies above 8 (re/max_players.md, re/lobby_12rows.md, kllobbyopt.c)
- Lobby row: stock 4..8 in FA/UCC (12 only in C&R). `[Lobby] PlayersMax=9..12` (kllobbyopt.c) already takes over the RIGHT clamp.
- Steam member limit: `[Lobby] MaxPlayers` (klmm.c) raises it. Lobby rows 9-12: `[Lobby] Rows12` (Patch01 overlay).
- Engine tables: 12 everywhere (records, score containers, 12 client slots): fine up to 12.
- **THE BLOCKER: seats.** A stock map has 8 type-2 `ZFFPlayer` heroes; `0x54cab0` returns -1 for the 9th joiner and the caller
  (e.g. 0x42bdd1) stores 0xff unchecked. Not seen live what follows. Fix: 12 heroes in the map (scene data: DD01..09 are already
  served from `KLExpansion\Maps\DDxx` copies, so an overlay with `Hero_09..12` + 4 more `FA_START` / `UCC_MERC` points is allowed
  there; the Dead Men maps are ours). Making joiners 9-12 type-3 bodies would make them cops: wrong for UCC.
- Order: a 9-human FA seat test (C&R 12 already works in stock, so it is the reference) -> hero overlay -> the two-UCC wrapper.

## 6. What is buildable next, in order
1. `[Sabotage] VanHold` live bench (built): solo System Link host + one client with AnyMode/AnyPlayer, then a UCC round.
2. Early wave variant T on DD01 (`tdSwats` first): a host-only dword write once the timer is found; first a DRY probe that lists
   every running ZTriggerDelay/2 (private-memory vtable scan, as klbotfill's ramp probe) with delay, deadline and target count.
3. The request channel (section 4), so a client UCC can use 1-3.
4. Door jam, after reads 3.4 a-c.
5. Two UCCs, after the 9-seat test.
Needs a live test: everything above; none of it has run.
