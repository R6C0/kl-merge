# AI heisters for the empty seats of an online FA lobby (owner 2026-10-25)

Owner: "there should be ai heisters in the slots as well if there isnt a full lobby so if its max 6 players and you ready it
up can you make it so theres ai for the rest". Written 2026-10-25 (static reading of kl2.exe 0490 with debug/dasm.py and
debug/vtfuncs.py; NOTHING run, nothing installed). CERTAIN = read in the disassembly at the address given; GUESS = inferred.

## 0. Short answer

1. The online round has NO AI heisters because the level's heister squads are filtered out at load, and even if they were
   kept they would only WALK (no loot / board / traitor tactics, no crew record). Both are code facts, not level data.
2. Step 1 is a DATA change (squad game-type field), step 2 is CODE (online crew records and tactics). Step 1 alone gives
   escorts that walk their route and shoot police; it does not give "a heister that takes loot and boards".
3. Built (read-only, default off): the count rule and a probe, so the live test can confirm each fact below.
   `[Bots] OnlineFill=1`: the host's Ready starts the round below the lobby target (MinPlayers floor 1) and every peer logs
   `fill = target - connected` plus a census of the Ally actors that survived the load.

## 1. How AI heisters exist today (Arcade) - CERTAIN unless marked

- There is no count decision. Arcade has 7 `ZSquadScript` groups `...merc_bot_squad!Squad#02..08` (one `Glazer_Bodyguard_0N`
  actor each, team Ally = `[[actor+0x54]+4] == 2`), started by `Timer_start_bots` (10 s after the round start, list 2 of the
  `AIMonitor`). The number 7 is level data (re/bots_squad.md 1). The same on the Dead Men maps (tools/kl_fa_bots.py).
- Registering a bot: `ZSessionHandlerSP` slot 45 = 0x8e5650: `if (0x7f6850() && team == 2) rules->slot198(actor)`;
  `ZGameRulesHeist` slot 198 = 0x588980 creates the crew record (0x7c bytes at `[rules+0x348]`).
- The bot's brain: `CPPScript::ZSoldier` ctor 0x6ab250 builds `ZLootTactic` / `ZBoardEscapeVehicleTactic` /
  `ZBecomeTraitorTactic` ([soldier+0x5f0/0x5f4/0x5f8]) only when `0x7f6850()` is true. 0x7f6850 = jump table on the session
  role `[sm+0x54]`: roles 0 / 1 -> `[sm+0x5c]==4`, roles 2 / 3 -> false (re/private_match.md; table at 0x7f6874).
- The filter that keeps the squad: `ZSquadScript` slot 14 = 0x7b3790 (collects the members at load; drops one by calling the
  member's vtable slot 21 = `[vt+0x54]`, whose effect I did not follow - GUESS: removes it from play). The mask is `[squad+0x34]`
  (the field-1 `EGameType`, enum values FA 1, TeamMode 2, Campaign 4, Heist 8, UCC 16, all types = all bits):

  | test | address | drops a squad whose mask lacks |
  |---|---|---|
  | `0x863a60` (role 2 or 3) and `[0x168e59c]==0` (FA) | 0x7b37d1..0x7b37f0 | bit 1 |
  | `0x7f6850` (Arcade) | 0x7b3805..0x7b381b | bits 1 and 8 (`test 9`) |
  | role 2 / 3 and `[0x168e59c]==2` (Cops & Robbers) | 0x7b382c..0x7b384b | bit 2 |
  | role 2 / 3 and `[0x168e59c]==1` (UCC) | 0x7b3852..0x7b3878 | bit 0x10 |

  The bot squads are `eHeistOnly` (8) on all 9 stock levels (63 of 63) and on every kl_fa_bots map: dropped online.
- Stock Arcade bots are therefore NOT a spawner that can be "enabled online": they are the map's squads plus Heist-only code.

## 2. What happens online today

- CERTAIN: the squad update 0x47e440 skips on a client (`call 0x4b0a40` = role 3, jne 0x47e70c); ZSoldier orders 0x760e50 are
  dropped on a client. AI actors replicate as `DDL_ZFFActor` (cops are AI online through exactly this: squads of mask
  eAllTypes / eFragileAllianceUCC, run on the host, followed by the clients). Ally soldiers are ordinary `ZFFActor` + `ZSoldier`,
  so their replication would be the same path (GUESS that nothing in it tests the team; unproven).
- Online the session handler's slot 45 is 0x466ea0 (the Server and Client handler share it): it puts the actor in the net
  object table (0x452ab0 / 0x4fe5e0), it does NOT go to the rules. The online rules (`ZGameRulesFragileAllianceSv` 0xbd2eb4 /
  `Cl` 0xbd31e4) have a different slot 198 (0x832930 on Sv: a `ret 8` position-writing function) and a per-client table of
  0x74-byte records at `[rules+8]` for 12 client seats (`m_iTotalLootMoney[12]` etc., re/netcode.md 9, 10). A bot has no
  seat: it cannot hold money, appear on the score page, be a "left behind" victim or board (the board rule works on seats).
- So online: the map-authored heister squads are not in the world (CERTAIN by the filter), and the Heist tactics could not
  run for them (CERTAIN: 0x7f6850 false), and the rules could not account for them (CERTAIN: no crew record).

## 3. The count rule (what the hook can read) - the part that is built

- `sm = [0x168e598]` (vtable 0xbd1ebc); `[sm+0xb9]` = lobby target, `[sm+0xb8]` = max, connected = size of `[[sm+4]+8]`
  (kllobby.c). With `[Lobby] MinPlayers` the host's Ready lowers `[sm+0xb9]` to the connected count (not replicated to clients).
- `kllobby.c` now remembers the target it lowered (`kllb_orig`, cleared when the lobby state falls below 0xd) and
  `[Bots] OnlineFill=1` implies MinPlayers=1.
- `klbotfill.c` computes on host and client: `target = host ? kllb_orig : [sm+0xb9]` (GUESS that a client still sees the
  host's original target), `fill = target - connected` and logs it once per session, then every 5 s in a round the census:
  ZFFActors by team, Ally ones with `[soldier+0x5f0/4/8]` (expected 0 online = proof of 2.) and health.
- Deterministic on all peers: the inputs are the lobby list and target, both readable on a client (the client side is a
  GUESS until the log line is seen on a client); a later action must be taken either by every peer from the same numbers or
  by the host only through a replicated call (`RMCSetActorActive` family, re/private_match.md; not looked at here).

## 4. How to switch the surplus off (design, not built)

Per-squad, not per-actor: `squad k (k = 0..6)` stays when `k < fill`. Options, best first:
1. LEVEL DATA: build the bot squads with `EGameType` = `eFragileAllianceOnly` (1) instead of `eHeistOnly` (kept in Arcade by
   `test 9` AND online). Every peer then loads all 7. The surplus is switched off at round start by the host with the same
   lever the map already has for squads: their `Timer_start_bots` list 4 (the first steps) - start only `fill` of the 7 chains
   (parked squads stay standing at the START row, still in the world: a visible idler, so this is not a clean off).
2. A vtable/object-copy hook on `ZSquadScript` slot 14 that writes `[squad+0x34]` for squads at index >= fill before the
   collect: the squads are then dropped by the game's own filter (clean: no actor at all), deterministic if every peer
   passes the same `fill` (needs the numbers of 3. on clients). Needs a way to run before the first collect: caller of slot 14
   NOT found (not in ctor 0x455c60, slots 21 / 22 - GUESS: the squad's start). Without the caller it is untested; probe first.
3. The stock-map route: an overlay build of DD01..09 (the expansion already redirects those slots; klslot [Redirect]) with the
   same one-field change, or option 2 on the stock squads (the filter code is the same, so one hook covers F01..F09, the Dead
   Men maps and Retomoto).

## 5. Stock maps F01..F09 (Q4)

Their squads are the very same 7 `eHeistOnly` chains, so they have the same two obstacles. There is no separate "Arcade bot
spawner" to reuse: the stock Arcade bots are map data + Heist code. Option 2 of 4. covers them without a data build.

## 6. What a REAL heister needs (CODE, not in this change; honest estimate)

(a) crew/seat for a bot in the Sv rules: the 12-seat tables are replicated datasets (score, money, state), a new seat would
have to be a client index with no peer (re/netcode.md 9: `m_iTotalLootMoney[12]`, `m_iRating[12]`...), and the Sv rules
functions that read seats; (b) loot / board / traitor tactics, which ask `ZGameRulesHeist` (their evaluate 0x451920 /
0x4faf60 / 0x79b7c0 call Heist slots; calling them with an Sv object is a wrong-layout crash) - they would have to be
rewritten against the Sv records, i.e. new code in hashed regions or a re-implementation. NOT an import-slot / vtable / data
change: SHIP rules do not allow it. Cheaper approximation to offer the owner: Step 1 (walkers) + the host scripting the bots
with `ZSoldier` orders (`klescort`-style; host only, 0x760e50) to the loot boxes: no score, no escape, they would vanish at the end.

## 7. Built

- `klhook/klbotfill.c` (new), `klhook/kllobby.c` (`kllb_orig`, OnlineFill implies MinPlayers 1), `klhook/klhook.c` (include,
  tick, init), `klhook/KLHook.ini` sample `[Bots] OnlineFill=0` ("(recommended off)" until the live test passes).
- Builds: `klhook/out_botfill_1025a` SHIP, `klhook/out_botfill_1025a_test` TEST (md5 in the commit / final report). Not installed.
- Writes nothing but what kllobby.c already wrote (the lobby target byte, MinPlayers only). With `OnlineFill=0` the behaviour is
  that of the previous hook.

## 8. Live test plan (owner runs it)

Same route as SL2 (System Link > Create > FALobby, `[Expansion] OnlineSet=2`), TEST hook `out_botfill_1025a_test`:
1. ini: `[Bots] OnlineFill=1`, `[Net] Log=1`, rest as the live ini. Solo host, Ready alone, DM01.
2. Expect in KLHook.log: `lobby: [Bots] OnlineFill=1 implies MinPlayers=1`, `lobby: host Ready ... target players 6 -> 1`,
   `botfill: role 2 state 0x.. lobby target 6 ... connected 1 -> fill 5 ...`. FAIL if target prints 1 (kllb_orig not kept) or no line.
3. After load: `botfill: round census: N ZFFActor, 0 team Ally` = CONFIRMS 1. (the heister squads were filtered). If Ally > 0 the filter
   reading is wrong: send the log.
4. Then the same round with a DM01 build whose bot squads have `EGameType` = eFragileAllianceOnly (one field in the 7 `Squad#0N`
   groups; kl_fa_bots writes eHeistOnly at its line 2688 check - NOT changed here, the file has another agent's edits): expect
   `7 team Ally`, tactics `00000000 00000000 00000000` (CONFIRMS 2.), and watch whether they walk, fight, and whether 0 faults.
5. Two-PC (when available): the same with a client; the client log must print the same `fill` (answers the GUESS of 3.).

## SL8 result and the data-side route (2026-10-25)
- SL8 (out_parity_1025a_test, System Link solo, DM01): round state 0x19 confirmed online. The hook byte pass (bit 1 into [squad+0x34]) found 0 ZSquadScript:
  it ran only in the lobby (8 passes) and squads are collected at level load, when the hook tick does not run. Hook route is dead; do not retry it.
- Census after load: 71 ZFFActor, 7 team Ally, 7 alive, 0 with tactics. 7 = the number of Squad#02..08 (Glazer_Bodyguard_0N), 0 tactics = ZSoldier ctor under
  0x7f6850 == false (it builds ZLootTactic/ZBoardEscapeVehicleTactic/ZBecomeTraitorTactic only when true). So most likely they are the map's own bots, which the
  filter at 0x7b37d1 reaches through member slot 21 (0x63ddf0 -> 0x6edd50, reads as a deactivate/flag set, not a delete): present but disabled. NOT proven
  (empty-seat player pawns are not ruled out by code; the numbers say squads). Test: with the botsonline zip the 7 should start walking.
- DATA ROUTE BUILT: tools/kl_botsonline.py <in> <out> [eAllTypes|eFragileAllianceOnly] sets ZSquadScript field 1 of the 7 squads (only the .prp changes);
  tools/kl_fa_bots.py build ... --squad-game eAllTypes does the same at clone time (check() accepts all three values). Default eAllTypes: keeps Arcade (mask has 8).
  Zip: C:/kl_build_1024/botsonline_1025/F01_Main.zip (md5 95eba206..., from the live DM01 978475ed), install.py / install.py --undo (backup .before-1025botsonline).
- What the host still lacks even if they walk: 0x7f6850 is false for roles 2/3, so no ZLootTactic / board-van / traitor tactics and no crew record
  (Sv rules have none; slot 198 is 0x832930). Expect walkers that shoot and follow their route, but they will not pick up loot or board the van until
  a code change (answer true from 0x7f6850 for the ZSoldier ctor only, or build the tactics ourselves). Not done.
