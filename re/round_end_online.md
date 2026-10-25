# Why an online FA round ends early; AI as crew; 12 players (2026-10-25, static; built in out_aicrew_1025a, NOT run live)

## 1. The two early cuts (CERTAIN, read from 0x80ad60 tail, kl2.exe 0490)
Rules = `[[0x168e9e4]+0x54]` (Sv, vtable 0xbd2eb4). Records `[rules+8]`, 0x74 bytes, `[rules+0x14]` of them, free bytes `[rules+0xc]`.
A record exists only for a HUMAN connection (`[rec]->+0x378` = the ZFFPlayer). AI heisters have none.

| | where | test | action |
|---|---|---|---|
| A | 0x80b1c0..0x80b208 | game type != 2, slot 168 (0x641750) < 2, `[sm+0xb8]` > 1 (always true), `[rules+0x4c]` > 70.0 (0xb20cbc) | slot 42 (0x4c3c10, "cut") with 70.0: `[+0x4c] = [+0x200] = min(70, length)` |
| B | 0x80b18c..0x80b1be | `[rules+0x200]` > 11.0 (0xb148d8) and 0x86f520 true | slot 193 (0x8a6140: `[+0x200] = arg` while state 0x19) with 10.0 (0xb3ef8c) |

- slot 168 = number of in-use records whose status (slot 114, 0x625be0) has neither bit 0x10 nor 0x40: "heisters still in play".
- 0x86f520 = state 0x19 and every in-use type-0 record has status bit 4 (or its player has the police byte `[p+0x2723]` / `[p+0x2729]` set); true too when no record is in use.
- The owner's theory is right in this sense: the AI heisters are not counted. A lone host is ONE record -> A fires at the first frame: the 70.00 left in every live round
  (and 70 s + the ~13 s end sequence = the 83 s rounds). B ends the round 10 s after the last human is down/out, however many AI stand.
- The 2-player idle bench (both at the spawn, left 249.9 -> 7.8 at 47.6 s, end timer 0): NOT explained by A (2 records in play). Candidates: B with 0x86f520 true for another reason
  (e.g. `[p+0x2729]` set = the "skip" byte, so every record is skipped), or a status bit 4 meaning more than "down". The TEST dump names it (below).
- The 0x80b0f0 block (`[rules+0x204]` = 8/9, slot 193 with min(60?, left)) is the final-minute logic: not touched.
- Separate, already handled: the session END request (sm slot 3, word 8, raised from the same tail when connected < 2): `[Lobby] Solo=1` drops it.

## 2. What was built
- `klroundkeep.c`, `[Lobby] KeepRound` (default 0, "(recommended on) for a solo host with AI"): private vtable copy of the Sv rules (one heap pointer write: SHIP-safe),
  slots 42 and 193 wrapped; the stock function is skipped ONLY when the caller is 0x80b208 (A) / 0x80b1c0 (B). 1 = while at most one human is connected or `[Bots] OnlineFill`
  planned AI; 2 = always. Other callers of the slots pass through. klbot.c / klnet.c accept the copy (`KLH_RULES_SV_OK`).
  A dead lone host then sits until the clock (lobby time + 10 s) or the escape ends the round (he can still respawn as a cop).
- TEST probe: every call of slot 42 / 193 logs `roundkeep-test: CUT ... from <ret>` plus a dump (clock, in-play count, 0x86f520, humans, every record's type, status bits, the player's
  police bytes and seat type); the same dump at session state 0x1f. The line with `= the ... cut (A|B)` names the test.
- `[Lobby] PlayersMax` (9..12, default 0) in kllobbyopt.c: focus row -3, RIGHT at >= 8 taken over exactly like time / rounds (pre-set 4 through 0x739f20 / 0x6f7fb0, stock call,
  then 0x739f20, 0x6f7fb0(n,0), 0x4b5fc0, store MP_NumberOfPlayers = n-1, 0x678d90(menu block, n) [menu block for 0x678d90 is a GUESS: the stock case's esi], dirty flag, 0x549e80).
  LEFT works from any value (floor 4). Needs `[Lobby] MaxPlayers` (klmm.c) for the Steam lobby member limit. System Link has no such limit.
- `[Lobby] ExtraSeats` (TEST build only, GUESS): see max_players.md 2: the 9th joiner finds no type-2 seat (0x54cab0 returns -1). While the host's target b9 is above 8,
  `target - (type-2 seats)` free type-3 seats get `[player+0x273c] = 2` (a heap byte), from the end of the table. Unknown: their spawn place (the police seat entity's own, not FA_START),
  and the cops then have fewer seats. Minimum without it: the level needs 12 hero entities (authored maps first).

## 3. AI as crew (design, NOT built)
A real crew record per AI heister needs: a 0x74-byte record in `[rules+8]` (type 0, `[rec]` a client struct whose +0x378 is a ZFFPlayer, free byte cleared, `[rules+0x14]` is the
fixed 12 so slots are available), score arrays (`ScoreFragileAllianceContainer[12]`), then every peer's Cl rules must receive it through the DDL replication of the 12-wide player
containers (sent by the host's replication layer from those same arrays; a client builds nothing itself). The ZFFPlayer requirement is the blocker: an AI soldier is a ZSoldier actor with no
ZFFPlayer / session entry; records are filled by the join path (0x42bdd1 and friends) from a connection. Faking one means a code-level call (TEST-only), and the clients' HUD/scoreboard reads that
record. So: not done; KeepRound removes the harmful consequence (round cut) by a vtable route instead. Remaining after that: AI heisters take no loot and do not board (below), and the
HUD crew list does not show them.

`0x7f6850` (the "Arcade/Heist" test; false online): it is a plain function called directly from the ZSoldier ctor (0x6ab250), the rules classes and others; there is NO vtable or data route to
answer it differently for the ctor only. Its jump table 0x863a78 is keyed by `[sm+0x54]` (role): roles 0/1 -> `[sm+0x5c]==4`. Options (all need code or a role flip): (a) a call-site patch in the ctor
(hashed region: TEST only); (b) the hook briefly writes `[sm+0x54]` = 0 around the ctor (needs a detour of the ctor: code). Either would make EVERY consumer of the answer see "single player"
during the ctor only, but the tactics it then builds (loot/board/traitor) read Arcade crew records (`[rules+0x348]`, slot 198 = 0x588980 exists only on ZGameRulesHeist), which the Sv class lacks.
So the tactics would build but find no records: not a safe next step.

Clients: AI heisters are replicated as ordinary actors (position streams from the host); a client sees them as heisters walking, not as crew rows, and nothing here changes that.

## 4. Live recipe
Single PC, System Link solo route (SL11.ini), TEST build `out_aicrew_1025a_test`, KLHook.ini `[Lobby] Solo=1`, `MinPlayers=1`, `KeepRound=1`, `PlayersMax=12`, `[Bots] OnlineFill=1`:
- PASS (A): `roundkeep: Sv rules ... wrapped`, `roundkeep-test: CUT slot42(70.0) from 0x80b208 = the 'fewer than 2 heisters in play' cut (A), DROPPED`, `roundkeep: cut (A) ... skipped: at most one human connected`,
  then `lobbyopt-test: round clock ...` shows left counting down from the lobby time + 10 s, and `ROUND LENGTH` ~ lobby minutes * 60.
- PASS (B): kill the host: `END TIMER slot193(10.0) from 0x80b1c0 = the 'all heisters out' cut (B), DROPPED`, round goes on.
- Players: lobby row 'Number of players', RIGHT at 8: `lobbyopt: Number of players 8 -> 9 (the stock clamp would have kept 8)` up to 12, the row shows the number.
Two-process bench (`tools/kl_solo_test.py`, 2 humans idle): with `KeepRound=0` read which `roundkeep-test:` line precedes `session: state 0x19 -> 0x1f` and the dump (record status bits);
then `KeepRound=2` should run to the clock. 12 players / ExtraSeats need a real 9th player: `ExtraSeats=1`, `roundkeep-test: ExtraSeats: target 9, 8 heister seats found, 1 police seats turned ...`.
