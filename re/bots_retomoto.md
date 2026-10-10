# AI heisters on Retomoto Tower (two navigation parts, one squad)

2026-10-10, agent v-rtbots. Offline: nothing here was installed or run in the game.
Tool `tools/kl_fa_bots_rt.py` (docstring = the commands), hook part `klhook/klcrew_rt.c` (NOT yet included by
`klhook.c`: three lines, section 5). Builds on `tools/kl_fa_bots.py` / `re/bots.md` (the squad, seen live on three
Dead Men maps) and `klhook/kljoin.c` (the player's jump, live in runs J1b / J2 / J3).

## 0. Short answers

- Built: `<work>\build\v_rtbots\retomoto_bots` from `<work>\build\rt_ai3\retomoto_ai3` (no gun step). Seven bots,
  ONE squad of seven actors and seven crew records from the balcony to the van. 303 entities added, nothing else
  changed (section 4). All checks pass (section 4).
- Also built: `<work>\build\v_rtbots\retomoto_bots_tower` (`--tower-only`): the same tower half, no street half,
  needs NO new hook part. The bots end beside the tower car and vanish from there when the van waits in the street.
- The join for the bots is a HOOK TELEPORT with the game's own routine `0x62a900`, done in the tick in which
  kljoin.c's jump request is pending, i.e. BEFORE the game moves the player and fires the jump point's own
  'AITrigger' list - which starts the bots' street route. Why this one of the three ways: section 2.
- The full build must only be played with `[CrewJoin] Enable=1` and a hook that has `klcrew_rt.c`. Without it the
  jump starts street steps for bots that stand in the tower (what happens then is not established): use the
  tower-only build with today's hook.
- The four large blocks do not grow: .prm 79,269,328, .ANM 21,642,904, .fxc 17,760,648, .WAV 27,158,864 before and
  after (the squad is entities, boxes and controllers only; no model, clip, shader or sound is added). Chunk table
  65,118 of 69,632 as before. Archive 215,137,729 -> 215,149,903 bytes.

## 1. What the bots do (as planned and checked on the mesh; none of it seen in the game)

Mesh: 2,241 polygons in 56 parts. The balcony and the tower floors down to the tower car are a part of 359; the
lobby, forecourt, road and the van's stop are a part of 1,615. No polygon joins them.

Tower (chain 1, started by `Timer_start_bots`):
1. Start: seven places on the balcony outside the main window (x 5918..6078, z -577..382, y 21020; the glass is at
   x 5860), 214..528 from the charge, 362..870 from the InvisiBomb, facing into the room. They stand: no step runs
   before the timer.
2. `Timer_start_bots` = the level's own blast timer + 1.0 s = 14.0 s after the round-start event (the blast timer of
   this build is 13.0 s; `--after-blast` GUESS).
3. In through the window: `FASpecials!PIP!EnterLootArea` (ENTERS_BANK, heist stage 1), places round (5722, 21086, 20).
4. The boardroom table: 6 loot objects (1,800,000) round (4670, 20995, -460); `TriggerLootDepleted` until they are
   gone or 30 s (`--loot-seconds` GUESS: the table's loot only appears when the room's guards are dead).
5. Nine way places through the tower and down the stairs (y 20995 -> 19599; the stairs are narrow: least clearance
   11..49 there, as `re/bots.md` 6.3 found).
6. Gather round (2430, 19600, 510): a square beside the jump box of `KLJoin.ini` (x 2550..2790, z 800..1100), its
   edge 153 from the box so the human can walk into it, inside an `AllyEscapeBox`, tight defence.
   Path per bot 20,750 .. 22,146 units.

The join: section 2.

Street (chain 2, started by the jump point's list):
1. Arrival: seven places in front of the lobby car's door, 320..509 from the jump entry `06_Exit` (6272, 563, -6305),
   x 5832..5952, z -6665..-6065, floor 570.
2. `FASpecials!PIP!ExitLootArea` (EXITS_BANK, stage 2) round (5645, 534, -5757).
3. Ten way places: lobby -> entrance -> forecourt -> the EAST pavement of the road (x about -850..-1000), north.
4. Rally round (-1207, -39, 7995), OUTSIDE the level exit box: `070_Timer_rally` holds 10 s (`--street-hold`
   GUESS) so the squad is together before anybody calls the van (a bot inside the level exit box calls it, kl2
   0x6cd8e0, `re/bots.md` 11; Retomoto has one van).
5. Into `Gameplay!EscapeSetup!otrExitLevel` round (-1493, -39, 10048): stage 3, the van is called.
6. Beside the van's stop: round (-1491, -39, 10342), 394..577 from the boarding box at the stop (-1851, 121, 10462),
   on the east side of the van's lane (x -1850; the van waits at z 8700 and drives north through the stop, its nose
   carries a KillBox). Tight defence; boarding by the game's `ZBoardEscapeVehicleTactic` (stage 3 + a path to the
   boarding action: both hold on this part).
   14 stations in 5 steps, path 24,765 .. 27,506 units. Every place from 800 before the van's waiting place on is
   on ONE side of its lane and each leg there is a straight line that stays on the mesh and out of the lane - except
   one leg of Squad#08 (NOTE of the check: the pathfinder's way there is not known).

## 2. The join: three ways weighed

A. Hook teleport of the same seven actors - BUILT.
   - The game has an actor teleport and uses it on AI actors itself: `0x62a900(actor, rot[9], pos[3], 1, 1)`.
     22 call sites. `ZFFActor`'s own vtable slot 18 (0x6ccc80) calls it on itself at 0x6ccdc1 (restoring an actor's
     saved state), so `this` = a ZFFActor is the game's own use; AI scripts call it on their actor (ZAirlockGoal,
     ZExitVehicleGoal, ZCloseCombat, ZCustomDeath, ZPlayMiniScene, ZAttackMountedWeaponTactic); and the jump routine
     0x8f3fa0 calls it at 0x8f4128 for every member of the STORY crew, 100 units apart. The hook does for the
     Fragile Alliance crew what 0x8f4128 does for the story crew (the walk a Fragile Alliance player has no list
     for: crash 0x8f40c9, run RT3).
   - The routine has an assert (`int3` at 0x62a9b8) when `[actor+0x77c]` and `[actor+0x780]` are both zero; the hook
     does not hand such an actor over. What the two pointers are is not established.
   - The start of the street route needs no hook: 0x57e110 calls `0x72e0f0(entry's ZJumpPoint)` right after moving
     the player; it sends 'AITrigger' to the jump point's own reference list, and `ZDefendBehaviourRout` slot 26
     (0x4ebed0; the vtable entry was checked) starts on it. Stock form read from the levels: campaign L05
     `Jumppoints!Jump04` / `Jump05` name `AI!Friendly!B6!Kane_B6\FollowLynch` (a friendly AI's behaviour step); L02's
     lists name `TriggerDelay2` boxes too.
   - Keeps everything: the same actors and crew records, so loot carried, money, heist stage and the traitor flag
     are untouched (nothing of a record is written).
   - Order: the bots are moved in the tick the request is pending, so when the game fires 'AITrigger' they already
     stand on the street's mesh part.
B. Two squads (seven in the tower that vanish, seven more in the lobby) - REJECTED, the exe forbids it.
   A crew record is made per Ally actor at registration (`ZGameRulesHeist` slot 198, 0x588980): the index comes
   from the table's counters (`[rules+0x354] - [rules+0x350] + 1`, 0x588995..0x5889bc) and the voice byte is
   written at `rules + 0x33e + index` (0x5889e2). The record table's pointer is at `rules + 0x348`: the byte table
   has room for indices 0..9, a write at index 10 lands in the pointer. Fourteen bots and the human pass that
   (not tried; whether the table of `[rules+0x354]` records would take them at all was not read). No routine that replaces a record's actor was found (records are looked up BY actor, 0x78f470). Loot and
   money would not carry over either.
C. Bots on the street half only - not built: the tower would be empty of crew for most of the round, and the bots
   would stand in the lobby for minutes with the police of the street layer. `--tower-only` is the opposite half
   and is built as the fall-back that needs no hook change.

## 3. The hook part (`klhook/klcrew_rt.c`)

No data write, no code byte; calls of `0x62a900` (and `0x72e0f0` with Retrigger=1) from the game's own thread,
after comparing the first 14 bytes of each routine. Off unless `KLHook.ini` has `[CrewJoin] Enable=1`. Arcade only.
Only on the level whose archive has a `KLJoin.ini` with `[CrewJoin]` (the file kljoin.c read: never a stock archive).
Once per round.
- EARLY: `[0x156b358] != 0` and `[gamedata+0x8d4]` = the index of the `[CrewJoin]` entry (found by Name and Target
  in the jump list) and the tick is the game thread's -> every AI record in play (in use, flag 1, status 0) is put
  on `Place.n`, n = its order among those.
- LATE (the request was consumed before a game-thread tick saw it): a local player within Radius (300) of Target
  after he was farther than From (2000) -> the same. The street steps were then started while the bots stood in
  the tower: not established what they do; `Retrigger=1` sends the list again (only useful if the step's byte 0x42
  is clear; which property that is, is not established).
- Not moved: aboard / dead, not a ZFFActor, node flag bit 10, both assert pointers zero, already within Near (1500)
  of the entry.
- ASSUMPTION: `actor + 0x460` = the feet as for a player (same base class). Used for the log line and the Near test
  only. Live check R4 settles it ('now at' = the place).
- Section names: `[CrewJoin]` in both files (klcrew.c's `[Crew]` in KLHook.ini is the random-outfit part).

Off-game harness (`<work>\research\agent_scripts\v-rtbots\`: rth.c, bh.bat, harness_KLHook.log; made-up game
data, the teleport replaced by a stub with the real prologue that records its arguments, the real bytes of
0x72e0f0, the build's own KLJoin.ini): 14 of 14 PASS, with Retrigger 0 and 1 - early in the tick kljoin.c writes
the request, 5 calls for 7 bots with one dead and one without the pointers, flags 1 / 1, the places in record
order, once per round, late form only on the game thread, a bot at the entry left alone, nothing outside Arcade.
The hook with the three lines compiles at /W4 without a warning from this file (SHIP, TEST and harness builds,
in a scratch copy of klhook.c - the repository's klhook.c is not touched).

## 4. Checks run on the builds

| check | retomoto_bots | retomoto_bots_tower |
|---|---|---|
| `kl_fa_bots_rt.py build` (kl_fa_bots.check + this module's) | PASS, 0 FAIL, 9 + 1 NOTE | PASS, 0 FAIL, 9 + 1 NOTE |
| `kl_fa_bots_rt.py diff` | only the squad was added; changed subtrees: `Gameplay!AIMonitor`, `Specials!JumpPoints!06_Exit` | only the squad was added |
| `kl_impact.py` | problems: 0 | problems: 0 |
| `kl_fa_street.py report <zip>` | exit 0, output identical to the source build's | not run |
| `kl_chars.py check` | problems: 1 = material 1410 `Weapons/BombWindow_02` (glow30.fx) - the same line in the source build rt_ai3 and in rt_guns3; known, `re/invisible.md` | not run |

The NOTEs of kl_fa_bots.check ('stage 3 is never reached', 'SPLIT MESH') describe the tower chain alone: that check
does not know the second chain; this module's check covers it (stage 2 True, stage 3 from place 13 of 14, hold
after place 12, last place 394..577 from the stop, for all seven).
Written beyond kl_fa_bots: the street steps (clones of the same F07 forms), field 0 of the JumpPoint controller
of `06_Exit` (seven references), `[CrewJoin]` appended to the build's `KLJoin.ini`.

## 5. For the lead

1. `klhook.c`: `#include "klcrew_rt.c"` after `#include "kljoin.c"`; `klt_tick(game_thread);` in `klh_tick` DIRECTLY
   after `klj_tick();` (the order is the early form); `klt_init();` after `klj_init();`. File table row: 'klcrew_rt.c
   x x AI crew follows the jump; calls 0x62a900, 0x72e0f0; no data, no code'. `KLHook.ini`: `[CrewJoin]` `Enable=0`,
   `Retrigger=0`, `Log=1`.
2. Install the build's OWN `KLJoin.ini` beside the archive (it has `[Join]` and `[CrewJoin]`), not
   `klhook\KLJoin.retomoto.ini`.
3. The gun step (`kl_guns`) goes on top of `v_rtbots\retomoto_bots`; re-run `kl_fa_bots_rt.py check` after it.
4. No change was made to `tools/kl_fa_bots.py` in this job (its `apply(more=)` and `diff(also=)` hooks are in
   commit 4f88d3c).

## 6. Live checks, in order

R1. `retomoto_bots_tower`, today's hook. Picture at 'Heist starts in N sec': seven bots on the balcony beside the
    player, none walking at the glass. klbot's crew log: 7 AI records.
R2. Same run, after the blast: the bots go in about 1 s after it; klbot: stage 0 -> 1 for the seven. Picture at the
    boardroom table; money of bots > 0 in klbot's lines after the guards are dead.
R3. Same run: the bots stand beside the tower car (picture), not in the box; the player can walk into it;
    `join: player 0 entered box 9 ...` as before. (Tower-only ends here: the bots vanish when the van waits.)
R4. `retomoto_bots`, hook with klcrew_rt.c, `[CrewJoin] Enable=1`. At start `crewjoin: on`, at level open
    `crewjoin: 7 places from ...KLJoin.ini`. Walk into the box: `join: player 0 entered box 9` then in the same
    millisecond `crewjoin: the jump to entry 5 ... (EARLY)` and one `crewjoin: bot N ... -> place n (...): now at
    (...)` per living bot, 'now at' = the place. No FATAL, no assert line after it. If 'now at' shows the old
    place although the picture shows the bot in the lobby: the +0x460 ASSUMPTION is wrong (log only).
R5. Picture 1..3 s after the jump: the bots in front of the lobby car, then running for the entrance = the
    'AITrigger' list started the street step. klbot: stage 2 at the stairs.
R6. klbot's money per record before and after the jump: equal.
R7. The rally: the bots wait about 10 s short of the exit box, then go in: stage 3, the van drives to its stop,
    klbot: status 4 (aboard) for the bots; nobody is run over (every place there is at least 350 east of the lane x -1850).
R8. Rush: reach the tower car before the bots have left the boardroom. Do they stay on the street route, or does
    the tower chain's next step (the loot timer, at most 30 s) pull them back towards the tower? (section 7, N3)
R9. Late form: only if a run shows `crewjoin: LATE`; then try `Retrigger=1`.

## 7. What the bots will NOT do

N1. Use the tower car or any door: they are teleported, in one frame, from wherever they are. Seen from the
    player's side they are simply in the lobby when he arrives (the player's own jump is a cut too).
N2. Follow a player who never jumps: if the human dies in the tower, the bots end at the tower car and wait; nobody
    is in the street to call the van. (In the tower-only build the same until a human is in the street.)
N3. Guarantee the street route when the jump comes while their tower chain still has a timer running (the
    `TriggerLootDepleted` wait): its next tower step may start on a bot that is already in the street
    (ASSUMPTION that a newly started step replaces the running one - it is how every chain here and in stock
    works - so the LAST started wins). A remedy exists in the exe but is not built: the message 'AIBlocker'
    (0x168d800) makes a step ignore 'AITrigger' for good (0x4ebee5); what sends it was not looked for.
N4. Loot the statue cases one by one: the route goes to the richest loot area (the boardroom table, 6 objects);
    the other 15 loot objects in reach are taken only if a bot's own looting tactic picks them on the way.
N5. Wait for the human at the tower car before leaving: they cannot leave at all without him (N2), and in the
    street they wait 10 s at the rally, not for him. 'Leave you behind' is klbot.c's van rule, unchanged.
N6. Betray in the tower by the stock rule: the stage term stays at 1 there; stages 2 and 3 are reached in the
    street only. klbot.c's own backstab keys are not affected.
N7. Work online: Arcade only (the crew belongs to the host and every player jumps on his own machine).
N8. Survive the hook being off on the full build in a known way (section 0).

## 8. ASSUMPTIONS and guesses in one place

- A started DefendBehaviourRout replaces the squad's running step / modifier (as in every stock chain).
- `eDMS_Sprint` suits the street as it does kl_fa_bots' way out; identity rotation at the teleport.
- `actor + 0x460` = feet (log and Near test).
- The two pointers of the assert are set on every living actor (the AI scripts call the routine unguarded).
- GUESS values: after-blast 1.0 s, loot wait 30 s, rally hold 10 s, gather square 150 from the jump box, arrival
  300..900 in front of the entry, lane kept clear from 800 before the van's waiting place, Lift 0.
- Session states 0x12..0x19 = inside a round (klcrew.c's reading).
