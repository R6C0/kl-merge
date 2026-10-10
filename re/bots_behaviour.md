# AI heisters: backstab, pay the driver, blow the van up, help you up

Owner, 2026-10-10: 'the ai have better interactions because in the current game they arent the best,
want them to be able to backstab you and also pay the driver and leave without you or blow the van up
or help you up'.

Agent b-behave, 2026-10-10. Research only: static reading of kl2.exe (base 0x400000, addresses below)
and measurements on stock level files. NOTHING here ran in the game, no build was made, no file
outside this one was changed. No model, sound or animation is added by anything proposed here, so
the four budget sizes (.prm, .ANM, .fxc, .WAV) of every build stay as they are.
EXE = read in the disassembly. FILE = measured on stock archives. ASSUMPTION = a guess, marked.

## 0. Short answers

| asked for | does stock Dog Days have it? | cheapest way to the owner's behaviour |
|---|---|---|
| bot backstabs you | **YES, for Arcade bots**: `CPPScript::ZBecomeTraitorTactic`. But the per-Arcade-level table allows **0 bot traitors on levels 1-3**, and the rule needs the bot late in the heist with much money while you have little | hook DATA writes into the tuning table (section 1.5 A); a bot must exist and pass the map's three gameplay triggers |
| bot retaliates when you shoot it | **YES**: damage you did to it over a per-level limit (100 on level 1 ... 25 from level 7) makes it hostile | same table, field +0x18 |
| pay the driver and leave without you | the action exists **for players only** (`ShareWithDriver`, Q / pad Y: half the money, become traitor, vehicle leaves at once). Bots only board; no AI caller was found | hook: one call of the rule the player's key ends in, with the bot's client index (2.4 A), or a data write of the wait timer (2.4 B) |
| blow the van up | the van **is destructible** (three damage grades; destroyed = everybody aboard dies). Police shoot it because it carries a `FakeTarget` of team `Mercenary`. A heister bot never targets it | hook: one call of the damage rule with grade 2 (3.4 A). Data only: NOT established |
| help you up | Dog Days' downed state (`DownNotDead`) is **self-service**: you get up yourself. A partner heal (`ZFFActionHealWounded`, `HealTactic`, animations `/Special_moves/Heal_wounded`) is in the exe and in the .ANM but no stock level object uses it | not possible by data found so far; hook route is uncertain (4.3). Say so to the owner |

The one finding that changes the plan: **the stock game already makes Arcade bots loot, board and
betray**, through three tactics every Ally / Mercenary soldier gets in Arcade (1.1). "They aren't the
best" is the tuning table (1.3), not missing code. All of it is driven by a heap object the hook can
write without touching code.

## 1. Backstab

### 1.1 The bot tactics (EXE)

`CPPScript::ZSoldier` vtable entry at 0xbd0998 = 0x6ab250 builds a soldier's tactic objects. At
0x6ab56d..0x6ab66c three of them are created only when `0x7f6850()` is true (ASSUMPTION: "this is the
offline Arcade session"; the same test makes `0x6c7700` return client index 0 for the local player)
and the actor's team (`[[soldier+0x40]+0x54]+4`, the ZFFActor node property 19) is 0 `Mercenary` or
2 `Ally`:

| soldier field | class (vtable) | name (slot 7) | evaluate (slot 11) | run (slot 2) |
|---|---|---|---|---|
| +0x5f0 | `ZLootTactic` (0xbd0d94) | - | 0x451920 | 0x7bc7d0 |
| +0x5f4 | `ZBoardEscapeVehicleTactic` (0xbd0dd4) | `BoardEscapeVehicle` | 0x4faf60 | 0x82f970 |
| +0x5f8 | `ZBecomeTraitorTactic` (0xbd13bc, ctor 0x51b7e0) | `BecomeTraitor` | 0x79b7c0 | 0x488eb0 |

FILE: the stock bots are `ZFFActor` with property 19 = `Ally`, `@ZSoldier` (`eThug`, `eNever`,
`eNever`, `eCustom`, ..., `No_Mercenary`, 0, `eSR_AllTypes`, 1), weapon `Rifle_zastavam85`, 7 per
level (F01, F02, F07 read). So a bot needs nothing special in its data to get the three tactics: it
has to be an `Ally` (or `Mercenary`) soldier in an Arcade session.

### 1.2 The objects (EXE)

- Arcade rules object = `ZGameRulesHeist` (vtable 0xbd3514, derived from
  `ZGameRulesFragileAlliance`), reached as `0x508ef0([0x168e9e4])` = `[[0x168e9e4]+0x54]`, valid
  only while `[[0x168e598]+0x5c] == 4` and `0x7f6850()`.
- Per-client records: `[rules+0x348] + index*0x7c`, count `[rules+0x354]`, free-slot bytes at
  `[rules+0x34c]` (0 = in use). Bots HAVE records: `0x78f470(rules, actor)` returns the index of the
  record whose +4 is that actor and whose +0x79 has bit 1.
  - +0x04 the object (player or actor); +0x10 status byte (4 = aboard / escaped, set by the boarding
    rule); +0x6c..+0x74 three floats cleared at round start;
  - **+0x78 heist stage 0..3** - raised (never lowered) by `0x5dd890(rules, object, stage)`, called
    from `ZOnlineGamePlayTrigger` slot 34 (0x8d2740): trigger type 0 `eOGPT_PLAYER_ENTERS_BANK` -> 1,
    type 1 `..._EXITS_BANK` -> 2, type 2 `..._BOARDS` -> 3; and from `ZOnlineExitLevelTrigger`
    slot 34 (0x6c3d50) -> 3. It takes players AND actors (class masks 0x1548c7c and 0x1547b24);
  - **+0x79 flags**: bit 1 = the record is a bot; **bit 2 = this bot has turned traitor**.
  - Round start 0x8c7a80 -> 0x817d20 clears bit 2 and the stage of every record, and
    `[rules+0x338]`, `[rules+0x33c]`.
- Money of client i: `[[rules+0x5f8] + 0x150 + i*4]` (`ZGameRulesHeist` slot 56 = 0x6f86c0).
- Arcade level: byte `[[rules+0x5f8]+0x45]`, clamped to 1..11 by every reader.
- Tuning object: `[0x168d7c0]`, a heap object built by 0x524050..0x530c3f, which registers 786
  variables (`FloatVar` 0xb5ec74, `IntVar` 0xb2e200, `BoolVar` 0xb3f49c: {vtable, pointer, default})
  and writes each default. The defaults are constants in that constructor; **no file was found that
  feeds it**. The object itself is plain writable heap.

### 1.3 The rule (EXE: 0x79b7c0, 0x43ffb0, 0x46d4d0)

Per-level record R = `[0x168d7c0] + 0x6ac + level*0x70`. `evaluate` returns 1.0 (the tactic wants
to run) when ALL hold:
1. Arcade session, the bot has a client record;
2. `0x43ffb0`: `[rules+0x338] < [R+0x6c]` **and** a random roll below a constant chosen by level
   (0.05 for levels 1-2, 0.10 for 3-5, 0.30 for 6-7, 0.40 above; constants in .rdata 0xb39e08,
   0xb4c788, 0xb26690, 0xb6fe50 - not writable);
3. `stage term + bot money term + player money term >= [R+0x20]`, where
   - stage term = `[R+0x24]`, `[R+0x28]`, `[R+0x2c]`, `[R+0x30]` for the BOT's stage 0, 1, 2, 3;
   - bot money term = `[R+0x40..+0x4c]` by the bot's money against the limits `[R+0x34..+0x3c]`;
   - player money term = `[R+0x5c..+0x68]` by the LOCAL PLAYER's money against `[R+0x50..+0x58]`.

Defaults, extracted from the constructor with a small emulator (scratch `tw.py`; 750 writes found):

| level | +0x6c max traitors | +0x20 limit | stage terms 0/1/2/3 | money limits (both) | bot terms | player terms |
|---|---|---|---|---|---|---|
| 1, 2, 3 | **0** | 7 | 0 / 0 / 2 / 3 | 750,000 / 1,000,000 / 1,250,000 | 0 / 1 / 2 / 3 | 3 / 2 / 1 / 0 |
| 4, 5 | 1 | 7 | same | same | same | same |
| 6, 7, 8 | 2 | 7 | same | same | same | same |
| 9 | 3 | 7 | same | same | same | same |
| 10 | 3 | 7 | same | 100,000 / 250,000 / 750,000 | same | same |
| 11 | 4 | 7 | same | 100,000 / 250,000 / 750,000 | same | same |

Read: a bot betrays when it is far into the heist (left the bank = 2, at the vehicle = 3), carries
a lot, and YOU carry little. With a limit of 7 of 9 possible it needs e.g. stage 3 + bot over
1.25 M + you under 1.25 M. On levels 1-3 it can never happen.

`run` (0x488eb0) sets `[record+0x79] |= 2` and calls `0x4322f0(rules, index)`. That function's
counter increment `inc [rules+0x338]` sits behind a test that can never pass as compiled (bytes
`0b f9 75 06 ff 80 38 03 00 00`: `or edi, ecx / jne` with edi = 1 << index), and no other code
increments it. So `[R+0x6c]` works as an ON / OFF switch (0 = never), not as a count. EXE.

### 1.4 What a traitor bot does, and the second road to hostility (EXE)

- `ZSoldier` slot 111 (0x882470, the soldier's "is this one my enemy" test) and the friend list
  0x5706a0 both read bit 2: for a bot with bit 2 the players are no longer friends. So it fights you.
- The same two places call `0x6a1c40(rules, index)`: true when `ZGameRulesHeist` slot 141
  (0x78d5c0 = float `[rules + 0x884 + index*4]`) exceeds `max([R+0x18], 25.0)`. The float is added
  to in 0x4d17f0, a damage routine with yellow-card tests around it. ASSUMPTION: it is the
  friendly-fire damage done to that bot. `[R+0x18]` = 100, 90, 80, 70, 60, 40, then 25 from level 7.
  So **shooting a bot enough already makes it turn on you**, sooner on high levels.
- NOT established: whether a bot's betrayal is announced (the tactic does not call the "make
  traitor" rule slot 129 = 0x8fb0d0, which is what speaks `Backstab` and shows the HUD line);
  whether a traitor bot also fights the other bots (only the player branch was read).
- Speech for it exists in the settings (re/audio.md: `Backstab/Backstab_0n_R`, replies, `Revenge`).

### 1.5 Ways to the owner's behaviour, cheapest first

A. **Hook, data writes only** (no code, no hashed range; the object is heap). After the level is
   loaded in an Arcade session, for level = 1..11 write into `[0x168d7c0] + 0x6ac + level*0x70`:
   `+0x6c` (int) = 1 or more -> bots may betray from the first round; `+0x20` (float) lower than 7
   -> more often; `+0x24..+0x30` stage terms; `+0x34..+0x3c` / `+0x50..+0x58` money limits (ints);
   `+0x18` (float) the retaliation limit. Suggested first test: `+0x6c = 1` and `+0x20 = 5.0` on
   every level - then a bot at the vehicle with over 1 M betrays whoever has under 1.25 M.
   An ini section per value keeps it tunable without a rebuild.
B. **Hook, one byte**: `[record+0x79] |= 2` for a chosen bot at a chosen moment (a timer, the
   player's money passing a sum, the player boarding). Record address as in 1.2. Cleared by the game
   at the next round start. This is "backstab on demand" and needs no tuning.
C. **Level data** (needed in any case, not sufficient alone): the bot must HAVE a stage. On a grafted
   map the bot's route has to cross the map's `OnlineGamePlayTrigger` boxes (ENTERS_BANK,
   EXITS_BANK, BOARDS) or the exit-level trigger; kl_fa keeps those boxes, so it is a matter of
   where the route's position boxes stand.
D. Squad script / level only: nothing found. No controller read here changes an actor's hostility
   toward players, and `SquadModifierBehaviour` has no team field (schema, re/retomoto_ai.md 1.3).
   NOT established that none exists among the classes not read.

Impossible without new code: a bot that plans the betrayal (waits for you to open the vault, shoots
you in the back at a scripted spot). What exists is "becomes hostile when the numbers say so".

## 2. Pay the driver and leave without you

### 2.1 The player's actions (EXE + FILE)

- Input actions (table at 0xcebb38): 41 `ShareWithDriver` = keyboard Q / pad Y, 42 `HoldEscape` =
  Space / pad A (default key map string 0xb50af8).
- FILE, the game's own tip texts (F07_MainEnglish.LOC): 'As the first criminal to enter the escape
  vehicle, you can press {ShareWithDriver} to share 50/50 of the score with the driver. You will
  leave immediately, but you ...' and 'As the first criminal in the escape vehicle you can press
  {HoldEscape} to make the driver stay put for a few seconds longer so your allies can escape with
  you.' Speech: settings fields `Driver_Bribe*`, `Driver_Traitor` (re/audio.md).
- Share: `RMCShareWithDriver(client)` -> wrapper 0x5373f0 -> rules slot 149.
  `ZGameRulesHeist` slot 149 = **0x757510(clientIndex)**: slot 151 (0) (clears `[rules+0x1b2]`);
  `[rules+0x1b3] = index`; slot 182 (index); money `[[rules+0x5f8]+0x150+index*4]` loses half;
  slot 129 (index, -1) = become traitor; `[rules+0x1d8] = 0.0` = the wait is over; announce
  0x65c620. (The online class: 0x785fa0, same steps through the score object.)
- Hold: `ZGameRulesHeist` slot 152 = 0x8b3930: once per vehicle (`[rules+0xd95]`), adds 5.0 s
  (double at 0xb5a068) to `[rules+0x1d8]`.

### 2.2 How the vehicle decides to leave (EXE)

State byte `[rules+0x1dc]`, timer `[rules+0x1d8]` (seconds, counted down in 0x55ec70), state set
through slot 194 (0x8fa6d0), which loads the timer from the vehicle's `OnlineEscAnimatedVehicle`
object (+0x6c, +0x70, +0x74, +0x78 = level fields 14, 15, 16, 17) or, without one, from the tuning
object (+0x628 = 20, +0x62c = 10, +0x630 = 20, +0x634 = 20).

| state | meaning (by the timers and callers; names are mine) | timer | on expiry |
|---|---|---|---|
| 1, 2 | driving in (1 = first vehicle) | field 14 | -> 3 (from 1) or 4 |
| 3, 4 | **waiting, can be boarded** | field 15 (FILE: 8.0 s in F01 and F07) | -> 5 |
| 5 | driving out | field 16 | criminals left behind (0x4906b0 > 0) -> 7, else 8 |
| 6 | destroyed | - | -> 7 |
| 7 | next vehicle / end | field 17 | - |

Boarding = rules slot 45 (`ZGameRulesHeist` 0x6840a0, called by the BOARDS trigger and by bots):
allowed in state 3 or 4 (in state 5 only while tuning +0x630 minus the timer is under 1.0); sets the client's status to 4; if nobody else
is left `[rules+0x1d8] = 0` (leaves at once), otherwise slot 151 (1) and an announcement.

So **the vehicle already leaves without you**: it waits field 15 seconds after arriving (8 s stock),
plus 5 s once if somebody aboard holds it, and goes. Stock levels have three vehicles.

### 2.3 What bots do today (EXE + FILE)

- `ZBoardEscapeVehicleTactic`: wants to run when the vehicle is in state 3 / 4, the bot's stage is 3,
  and a path to the boarding point exists; within 3 m (squared distance under 90,000 at 0xd19a28)
  it calls 0x74d7f0 = slot 45 for itself. In states 1 / 2 it only acts in the last 2 s.
- `ZAllyEscapeBox` (level controller; slot 25 = 0x907a50): a bot record with status 0 standing in
  the box boards the same way. FILE: used by the helicopter levels only - F02 8, F06 8, F08 1
  (on `...\BoardingTrigger_Heli...`, values `[[], 1, 0, 0, 'Activate', 0]`); the van levels F01 F04
  F05 F07 F09 have none. **This is the data-only way to make a bot board a Dead Men spline car or
  helicopter** (re/maps.md 14.5 asked for such a proof): one box at the map's boarding place.
- No caller of slot 149 from AI code was found: the only callers of the wrapper are the RMC
  handler 0x867200 and the online rules' slot 149. NOT established for indirect calls (60 sites use
  vtable offset +0x254 on objects of unknown class).

### 2.4 Ways, cheapest first

A. **Hook, one game call**: `ZGameRulesHeist` slot 149 with the bot's client index (thiscall,
   `rules->vtbl[149](index)`, one stack argument), from the hook's per-frame routine on the main
   thread - the way klchar.c already calls the game's body-swap routine. When: the bot's status
   `[record+0x10] == 4` (aboard), the player's is not, vehicle state 3 or 4, and a roll (higher
   when the bot's money is high). Result with stock code and no data change: the bot pays half,
   is made a traitor by the game's own rule (so the announcement and voice are the game's), the
   vehicle leaves now. NOT tried: that slot 129 accepts a bot's index (it was written for players).
B. **Hook, data writes only** (if A misbehaves): `[rules+0x1d8] = 0.0` while `[rules+0x1dc]` is
   3 or 4 makes the vehicle leave at once (exactly what "heavily damaged" does, 3.2); halve the
   bot's money dword by hand. No announcement, no traitor status.
C. **Level data**: field 15 of `OnlineEscAnimatedVehicle` shorter = everybody is left behind more
   often. No per-bot decision.

Impossible without new code: a bot that pays the driver through the game's own AI (there is no
such tactic to switch on).

## 3. Blow the van up

### 3.1 The stock mechanism (EXE + FILE)

- FILE (F01 F04 F05 F07 F09): three `ZAnimatedVehicle` each with the same seven numbers before the
  last three properties: 9600, 10000, 8000, 3000, 5000, 7000, 10000 (ASSUMPTION: health and the
  damage thresholds; the reader was not traced). Body_Main, Door_Back_Left / Right carry
  `@RelayAnimatedVehicleHit` -> the vehicle (9 per level); Body_Main also `@FakeTarget`
  `['Mercenary', -1, '', 20.0, [], 0, 1, 0.0, 0.0]` (3 per level, 9 in F05 and F09).
  The helicopter / car levels (F02 F03 F06 F08, `OnlineEscHavokCar`) have NO FakeTarget and no
  ZAnimatedVehicle.
- EXE: `ZRelayAnimatedVehicleHit` slot 26 (0x745740) forwards the hit message to the vehicle.
  `ZOnlineEscVehicleController` slot 26 (0x6d7d20) turns messages into rule calls: hit -> rules
  slot 93 (attacker); damage grade -> 0x594b10 -> **rules slot 94 (grade)**.
- `ZGameRulesFragileAllianceSv` slot 94 = 0x839380 (the Arcade class has its own, 0x6a1100, not read
  line by line):
  - grade 0: nothing;
  - grade 1 'heavily damaged': announcement; if the vehicle is waiting (state 3 / 4) the timer is
    set to 0 - **it drives off at once**;
  - grade 2 'destroyed': state 6; every client with status 4 (aboard) is killed through slot 11,
    credited to the attacker `[rules+0x1e8]`; announcement `RMCAnnounceFAEscapeVehicleDestroyed`.
  The level then plays `Activate_Crash_01..04` (-> `Relay_VanExplotion` -> an `@Explode`,
  re/fa_gamemode.md section 2) and `OnlineEscVehicleMonitor` list 3 / list 8 ('last escape van').
- Who shoots it: AI that is hostile to team `Mercenary` (the police), because of the FakeTarget -
  re/retomoto_ai.md 1.3 says the same. Players can shoot it too.

### 3.2 Can a heister bot?

Not today: a bot is team `Ally`, the FakeTarget is `Mercenary`; nothing was found that makes an
Ally soldier attack it, traitor or not (the traitor bit only changes how it sees PLAYERS, 1.4).

### 3.3 Ways, cheapest first

A. **Hook, one game call**: rules slot 94 with grade 2 (or 1) - `rules->vtbl[94](2)` - when a
   traitor bot (bit 2) is alive, not aboard, near the vehicle, and somebody is aboard. With stock
   code this gives the explosion, the deaths and the announcement. `[rules+0x1e8]` (the attacker,
   read as a player object) should be left as it is or null; a bot cannot be credited. NOT tried.
B. **Level data, uncertain**: a second `FakeTarget` on Body_Main with a team the bots attack,
   switched on when the betrayal happens. Two unknowns: which team an `Ally` soldier attacks
   (the relation table was not read) and how a FakeTarget is switched (fields 5..8 not decoded);
   and the bot's rifle would need many seconds against 10,000. ASSUMPTION throughout.
C. Visual only: sending `Activate_Crash_0n` to the vehicle from a level trigger plays the crash
   but the rules do not follow (nobody aboard dies, the state stays). Not wanted.

On the Dead Men maps with a spline car or helicopter (M01 M02 M03 M06) there is no
`ZAnimatedVehicle` and no damage path at all: there only A can work, and whether slot 94 behaves
for an `OnlineEscHavokCar` is NOT established (0x8fa6d0 does look the vehicle up under both
controller names).

## 4. Help you up

### 4.1 What Dog Days has (EXE + FILE)

- The downed state is `DownNotDead`: player state `ePM_DOWNNOTDEAD`, network calls
  `RMCDownNotDead_SetDowned` / `_GettingUp` / `_SetInsulted` / `_DoRespondInsult` on the player
  object, `m_iDownNotDeadFlags`, user actions `UA_DOWNNOTDEAD_GETUP` / `_GETUPINCOVER`, speech
  `AllLevels/Oneliners/DownNotDead/...` (FILE: in F07's .SND and .LOC). The player gets up BY
  HIMSELF; there is no step in it that waits for a partner. It is not tied to a game mode in what
  was read (the set-downed wrapper 0x846d90 has no mode test), so Fragile Alliance / Arcade players
  have it. NPCs: `ZDownNotDeadNPC`, squad modifier `eDND_Default / Force / Prevent` (FILE: all
  `eDND_NotSet` in F07 (45) and L02 (72)).
- A partner heal is IN THE EXE, left from Dead Men's adrenaline shot: player action
  `ZFFActionHealWounded` (vtable 0xbb54fc, made at 0x907300 from the action factory 0x839740; user
  action `UA_HEAL_WOUNDED_COOP_PLAYER`), inputs 7 `HoldHeal` / 8 `TapHeal` (keyboard E / pad X),
  `ZHealCtrl`, `ZActorHealer` ('ff2\levelsetup\actorhealer.cpp'), AI side `ZHealTactic`
  (0xbd027c; created at 0x6ab6a2 only if the soldier's `ZSoldier` field 2 is not `eNever` and byte
  `[[0x168d7c0]+5]` is 0), `ZHealPlayerBehaviourGoal`, `ZSoldierHealGoal`, export
  `?Resurrect@ZFFPlayer@@QAEXPAVZGEOM@@_N1@Z`, `RMCDMResurrect`, `RMCResurrected`,
  `RMCAnnounceFAPlayerResurrected`.
- FILE: the animations are shipped - F07's and L02's .ANM both hold `/Special_moves/Heal_wounded`,
  `/Special_moves/Heal_Wounded_Low`, `/Special_moves/Heal_Down_not_dead`,
  `/Special_moves/Heal_Down_no_dead_Crouch`.
- FILE: no level object uses any of it. F07 has no node or controller with heal / resurrect in its
  name and its only `PlayerAction` is the vehicle's `EnterVehicle`; L02 (campaign) has
  `OnDownNotDead1..3` camera nodes and one `HealthMonitor`, no heal action. Stock bots have
  `ZSoldier` field 2 = `eNever`, so they get no `HealTactic`.

### 4.2 What that means

Stock Dog Days, any mode: nobody helps anybody up. You go down, you shoot from the floor, you stand
up or you die; in Fragile Alliance a dead criminal comes back as police.

### 4.3 Ways, and what is not possible

A. **Level data, one field, untested and uncertain**: give the bots `ZSoldier` field 2 =
   `eSometimes` / `eAlways`. That creates their `HealTactic` (if tuning byte +5 is 0; its default
   was not extracted). What the tactic then does was NOT read (its evaluate 0x64ed60 tests soldier
   flags and a player; whether its target is a downed PLAYER, a wounded squad mate, or itself is
   not established). Cheap to try in one live run: a bot build with that one field changed, go
   down next to a bot, watch. If it does something useful this is the whole feature.
B. **Hook**: call `ZFFPlayer::Resurrect` (exported, so its address is fixed and named) on the downed
   local player when a living, non-traitor bot stands within a few metres for a few seconds. It
   would be an instant stand-up with no animation on the bot, and the arguments (a ZGEOM and two
   bools) and the state it expects (downed, or dead?) were NOT read. Research first, then a run.
C. Cheapest honest substitute, data only: bots that DEFEND the place where you went down (a
   `DefendPlayerPos` behaviour exists: `ZDefendPlayerPosBehaviour`, `ZFollowPlayerBehaviourGoal`)
   while you get up by yourself. Not the same thing; say so.

Impossible without new code: a bot walking to you and playing a help-up animation with you, unless
A turns out to do exactly that.

## 5. For the lead: hook parts in one place

All offline-derived; every item needs one live run. No code patch in any of them.

| # | part | kind | what |
|---|---|---|---|
| H1 | traitor tuning | data writes | `[0x168d7c0] + 0x6ac + L*0x70` for L = 1..11: `+0x6c` int, `+0x20` float, `+0x18` float, `+0x24..+0x30` floats, `+0x34..+0x3c` and `+0x50..+0x58` ints, `+0x40..+0x4c` and `+0x5c..+0x68` floats. Write once after `[0x168d7c0]` is non-null (set at 0x530c33); the values are per process, not per level |
| H2 | backstab on demand | data write | `[[rules+0x348] + i*0x7c + 0x79] |= 2`; rules = `[[0x168e9e4]+0x54]` while `[[0x168e598]+0x5c] == 4` |
| H3 | bot pays the driver | game call | `rules->vtbl[149](i)` = 0x757510 in Arcade; guard: record bit 1, status +0x10 == 4, `[rules+0x1dc]` in (3, 4) |
| H4 | vehicle leaves now | data write | `[rules+0x1d8] = 0.0f` while `[rules+0x1dc]` in (3, 4) |
| H5 | van destroyed | game call | `rules->vtbl[94](2)` (grade 1 = "drives off damaged") |
| H6 | log first | read only | per second: level byte, each record's +0x10, +0x78, +0x79, money, `[rules+0x1dc]`, `[rules+0x1d8]`. One round on STOCK F07 with this log shows whether stock bots ever reach stage 3 and what the numbers are - do this before H1 values are chosen |

Leaderboard note (re/leaderboard.md): H3 makes the game's own traitor rule run for a bot; nothing
read here says it writes player statistics, but the Steam write guard should be on for the test.

## 6. Not established

- Everything live. In particular: that stock bots reach stage 3 on a stock map (H6), that slot 129
  / 149 accept a bot's index, that slot 94 works for a spline car, what `HealTactic` does.
- The meaning of `0x7f6850` beyond "true in Arcade" and of record +0x6c..+0x74.
- R +0x00..+0x1c (per-level difficulty multipliers read by 0x591b60, 0x7c1ba0, 0x8b8050; +0x18 is
  the retaliation limit) - not named one by one.
- The seven `ZAnimatedVehicle` numbers; who sends the damage-grade message.
- Whether a traitor bot is announced, loses its HUD marker, or fights other bots.
- What ends the round after the last vehicle (re/fa_gamemode.md has the same gap).
- `ZLootTactic` (0x451920 / 0x7bc7d0) was only identified, not read: how bots choose loot.

## 7. How this was read

Scratch scripts (session scratchpad, folder `bbehave`; not in the repo): `strs.py` / `sx.py`
(strings and their code references), `vt.py` / `vdiff.py` / `slot.py` (vtables through RTTI),
`xr.py` / `wr.py` / `pat.py` (references, writers, byte patterns), `tw.py` (the tuning
constructor's defaults -> `tw.json`), `sq.py` / `act.py` / `veh.py` / `cen.py` / `heal.py` / `ctl.py`
(stock level surveys through `kl_fa.load`). Repo tools used: `debug/dasm.py`, `debug/rtti.py`,
`debug/kl.py`, `tools/kl_fa.py`, `re/kl2.json`.
