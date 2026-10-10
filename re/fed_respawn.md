# Coming back as a fed: the dead criminal as police, for the player and for the AI heisters

Owner, 2026-10-10: 'i want to make it so you can come back as a fed or the ai heisters can come back
as feds too'. Research only. Written 2026-10-10 from `kl2.exe` build 0490 (disassembly, `debug\kl.py`)
and from level files (stock F07, the builds `<work>\build\b_bots\M01`, `b_bots\M06`,
`rt_guns3\retomoto_ai3_guns`). **Nothing here was run in the game.** No file but this one was written.

Status words: **EXE** = read in the disassembly, address given. **FILE** = measured in level files.
**ASSUMPTION** = inferred, said why. **not established** = looked for, no answer.
Scratch tools (disassembler with vtable owners, cross-reference search, level surveys): session scratchpad
`fed\x.py`, `scan.py`, `vts.py`, `lv2.py`, `sp.py`, and of the second pass `nb.py`, `ctx.py`, `lv3.py`, `lv4.py`.

**Second pass, 2026-10-10 evening** (the first writer stopped on a usage limit). Every EXE statement the
ranking rests on was disassembled again and holds; the list is in section 9. What the second pass CHANGED
or ADDED is marked **[2]**: the police-object budget (2.3), the 30 seconds of `TriggerActorsDead` (5.3), a
data-only way from a bot to its squad object and with it a deaths-only release (5.3, 5.4), the round's own
600 s limit (3), the status values klbot.c lists as 'not read'.

## 0. Short answers

1. **The player: yes, and almost for free.** `ZGameRulesHeist` (the Arcade rules, vtable 0xbd3514) is a
   one-machine copy of the Fragile Alliance server rules and still holds the **whole** 'dead criminal comes
   back as police' path: the wait, the death-camera text, the pick of a police player object, the
   AFTER_DEATH spawn point, the police flag, the switch of the local player to the police body - with
   explicit Arcade branches in the session handler, the death camera, the soldier AI and the HUD. Arcade
   never reaches it for one reason: the kill rule first asks 'is the round over?' (0x67f480), and with one
   human that answer is always yes when he dies.
2. **The switch is one dword of data.** 0x67f480 starts with `cmp dword [0x168ea60], 0` / 'not zero ->
   answer no'. 0x168ea60 is a developer variable in the zero-filled part of `.data` that nothing in the
   retail exe writes (two readers, no writer). While it is 1 at the moment the human dies, the game itself
   does the rest: 5 s death camera, 'You respawn as police', police body at an AFTER_DEATH point, playable,
   the AI heisters shoot him and the police AI does not. No game function has to be called by the hook.
3. **What it costs / what breaks**: the life is still lost at the round end (he did not escape), a second
   death is final in this rules class, and the round no longer ends by itself when the last criminal is gone
   (the hook has to end it with the game's own two data writes). All of it happens on a level that is not
   stock, where the Steam write guard blocks every stat. Details in section 3.
4. **The AI heisters: not through that path** - it is built for a client with a player object and would
   take the human's controls away (section 5.1). An AI heister comes back as a **parked police actor**: a
   one-man police squad that is not in the world at load, named in the heister squad's own 'everybody dead'
   list. That list is real: `ZSquadScript` field 8 is sent by 0x87ebf0 when the squad's count of living men
   reaches 0 (no longer an assumption). One catch found in the code: a heister who BOARDS the vehicle also
   counts as 'not living' there, so the list fires for an escape as well (section 5.3). **[2]** The catch
   can be closed by the hook with two data writes per bot, because the squad object is reachable from the
   crew record by pointers alone (record -> actor -> soldier -> squad -> squad script, section 5.3).
   `TriggerActorsDead` is no alternative: it fires by itself 30 seconds after it is started.
5. **The fed's look exists already.** Dead Men's own police-respawn body is an FBI agent in a black suit
   with sunglasses and a headset (M01_FA_A `Heroes!Henchmen_01..08`, one model, 0.59 MB); every build
   already carries Dog Days' police player model (number 1919 in the F07-hosted builds), and the M01 build
   has `FBI-Agents_01..04` (10 actors, one model with 8 variants).
6. **Impossible**: an AI heister driving a police PLAYER object; a dead actor standing up again as police;
   the crew record of a bot going through the player's respawn routine (section 6).
7. **[2] A hard number**: a level holds 8 police player objects and Arcade never gives one back (the
   routines that release one exist only in the multiplayer session handler; the single-player handler has
   empty stubs in those slots). One is taken per fed respawn, possibly one more when the session is joined.
   The game stops on an `int3` (0x4b2984) when none is free, so the hook must count them and stand down.
   In practice a session's lives run out first (one respawn per round at most, and it costs the life).

## 1. How 'come back as a cop' works in Fragile Alliance multiplayer (EXE)

Class tree (RTTI): `ZGameRulesBase` -> `ZGameRulesFragileAlliance` -> { `...Sv` 0xbd2eb4, `...Cl` 0xbd31e4,
`ZGameRulesHeist` 0xbd3514 }. Heist is a sibling of Sv, not a child: it re-implements the server's slots.

| step | server rules (`...Sv`) | where |
|---|---|---|
| kill rule, vtable slot 11 | 0x46bd40: status of the client record = 1 ('will respawn', flag 0x4000) unless 'round over' (0x86f520) | re\netcode.md 10 |
| respawn | 0x6bb910 (from the update, slot 7 = 0x827f00 -> 0x80ad60): picks the police player, `RMCRespawn(bBecomePolice, iRespawnPlayerIndex, ...)` | re\netcode.md 10 |
| police body | 0x6ee860: the FIRST free player object whose type byte `ZFFPlayer+0x273c` is 3 (`eZFFP_TYPE_MULTIPLAYER_POLICEMAN`) in the session's player table | re\netcode.md 10 |
| on the client | `RMCRespawn` wrapper 0x63a0a0: switch the local player (0x4d2ef0), 0x4b6680 | this note |

The police 'character' is therefore a pre-placed object of the level. FILE: every stock FA level and every
one of our builds has 16 `ZFFPlayer`: 8 `MULTIPLAYER_NORMAL` (`Heroes!Hero_01..08`) and 8
`MULTIPLAYER_POLICEMAN`, `eZFFP_RANK_NONE`, animation set Lynch, all eight on ONE model (F07 and our builds:
`Heroes!Henchmen_01..08`, model 1919; F01 calls them `RespawnPolice#01..08`). The object has no children and
no controllers: its weapons are not level data.

Being police is one byte on the player object, `ZFFPlayer+0x2723`, set by 0x43e270(player, 1) (which also
clears `+0x2727` and `+0xbb0`). 59 places read it (scan): trigger boxes (`ECPS_FA_RESPAWNONLY` /
`MERCONLY`), money containers, close combat, the spawn-point trigger, the boarding rule, the AI.

## 2. The same path inside `ZGameRulesHeist` (Arcade), step by step (EXE)

Objects as in `klhook\klbot.c` section 1: rules = `[[0x168e9e4]+0x54]`, crew records of 0x7c bytes at
`[rules+0x348]`, one 'in use' byte each at `[rules+0x34c]` (0 = in use), count `[rules+0x354]`, score object
`[rules+0x5f8]`. New here:

- record `+0x08` float: the respawn countdown. `+0x11` byte: death-camera phase. `+0x13` byte: deaths.
  **`+0x14` byte: index of the police player object this record respawns as, 0xff = none yet** (set to 0xff
  by the record's constructor 0x549030 and again at every round start, 0x817e10).
  `+0x70`, `+0x74` floats: two timers that clear flags 2 and 0x80000 (0x58b30d .. 0x58b371).
- **record `+0x10` status, complete** (jump table 0x58b618 of the per-record update 0x58b2c0):
  0 in play, **1 dead and waiting to come back as police**, 3 a timed state that ends in spectating
  (0x58b476; nothing in this class sets it), 4 aboard, 5 / 6 escaped (0x805270, 0x805367), 7 dead for good.
- **client flags** = dword `[score + 0x1d4 + 4 * index]` (getter slot 114 = 0x771a10, set slot 115, clear
  slot 116): 1 traitor, 4 dead, **8 police** (slot 107 = 0x5aae60), 0x10 spectating, 0x20 aboard,
  0x40 escaped (slot 106 = 0x8110e0), 0x80 (slot 110, not identified), 0x100 'has died once',
  0x200 'has died twice', 0x4000 'waiting to respawn', 0x80000 'just respawned' (10 s).

### 2.1 Death of the human: the kill rule, slot 11 = 0x704610(player, killer)

Runs only in session state 0x19. It always works on the record of the local client (`[[rules+0x348]]`, index
byte `+1`), i.e. it assumes ONE human.

1. 0x7046aa: status = 7, countdown `+0x08` = 5.0 (float 0xbcb330), `+4.0` more for a traitor (slot 108),
   deaths `+0x13` + 1; 0x70479c: flag 4 (dead).
2. **0x7047b5: `call 0x67f480` = 'is the round over?'**
   - **yes** (stock Arcade, always): if slot 167 (0x7d2c20, criminals still in play) is 0 the 'all dead'
     announcement 0x8429d0; slot 42 (0x47d190) cuts the round clock to 3.0 s; slot 193 (0x642850)
     `[rules+0x200] = 3.0`; slot 21 (1, 0, 0, index, killer) = the death camera. Three seconds later slot
     192 (0x5dff40) ends the round: `dec byte [score+0x6c]` (a life) when the human has not escaped, then
     state 0x1f (re\leaderboard.md 2.2).
   - **no**: 0x70482d: if slot 112 (0x4549f0: not police, flag 0x80 clear) -> **status = 1**, `+0x11 = 0`,
     flag 0x4000 set, flag 4 cleared. The round goes on.
3. Either way: the money he carried is dropped (0x5ab010), a traitor flag is cleared, `[rules+0xe8a] = 1`.

### 2.2 'Is the round over?' 0x67f480 - the one gate

```
67f480  cmp dword ptr [0x168ea60], 0
67f48a  je  0x67f490
67f48c  xor al, al / ret                 ; variable set -> 'no', whatever happened
67f490  state must be 0x19, else 'no'
        ebp = number of OTHER clients (1 .. n-1) whose flags lack 4 (not dead: in play, aboard or escaped)
        client 0 escaped (slot 106) or dead (flag 4)            -> yes
        record 0 status 4 (aboard)                              -> no
        record 0 status 1: 'no' while the local player is not police, else yes
        record 0 status 0, local player a criminal              -> no  (yes if his byte +0x2729 is set)
        record 0 status 0, local player POLICE                  -> no if ebp > 1, else yes
        any other status                                        -> yes
```

Three callers and no other (cross-reference search): the kill rule (0x7047b5), the respawn routine
(0x4b2a2c) and the 'vehicle has left' routine 0x805120 (0x80530e, from slot 195).
**0x168ea60**: `.data` runs from 0xcd7000 for 0x9bbe5c bytes with 0x73600 bytes in the file, so the address is
in the zero-filled tail (never part of a file hash). The whole exe refers to it twice - here and in the
server class's twin 0x86f520 - both `cmp ..., 0`. Its neighbours 0x168ea64 .. 0x168ea9c are the same kind of
thing (read by 0x894450, the boarding rule, both updates), so this is a block of developer switches whose
writers were compiled out. ASSUMPTION by that pattern: 0x168ea60 was 'the round never ends'.

### 2.3 The wait and the respawn: 0x58b2c0 (per record, from the update slot 7 at 0x74bc48) -> 0x4b28d0

Status 1, each frame (0x58b40c): countdown `+0x08` -= dt. Below 4.0 (i.e. one second after the death) and
`+0x11 == 0`: `+0x11 = 2` and slot 21 (1, 1, 0, killer's index, 0) = the second death-camera phase.
`ZFADeathCamDisplay` slot 5 (0x728580) is where 'YouRespawnAsPolice' / 'YouRespawnAs%s' are built, and it
asks 0x7f6850 (Arcade?) and 0x7bb2a0 (the Heist rules) itself. At 0: **0x4b28d0(index)**:

| at | what |
|---|---|
| 0x4b28f8 | flags have 0x100 ('died once'): set 0x200 and pick a NEW police object. Else: pick one only if `+0x14` is 0xff, then set 0x100. **So a `+0x14` written beforehand is used as it is** |
| 0x4b2929 / 0x4b2940 | pick = 0x54cab0(index, 3, 0): first entry of the session's player table that is free and whose `ZFFPlayer+0x273c == 3`; marks it used (byte `+9` of the 12-byte entry). -1 if none |
| 0x4b296b | slot 21 (0, 1, 0, -1, 0): death camera off |
| **0x4b2984** | **`int3` when `+0x14` is still 0xff** - no free police object = a crash in retail |
| 0x4b29b7 | slot 199 = 0x518e30(police player, **2**, 0): a random free spawn point whose type is 2 = `eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH` (0x5614f0; a point whose node has bit 0x400 of `+0x3c` is skipped), then place the player there (0x82cc40). No such point: the call is skipped and the police body stays where the level put it. (The round start does the same with type 1 = START: `ZSessionHandlerSP` slot 11, 0x466bb1.) |
| 0x4b29c8 | slot 204 = 0x7622f0(index, player): 0x43e270(player, 1) = the police byte; flags 4 / 0x10 / 0x20 cleared, **flag 8 set** |
| 0x4b29ea | status = 0 (in play again), `+0x0c = 0.0` |
| 0x4b29ef | 0x748540(session, index): in Arcade and for client 0 it returns the current local player index (explicit `call 0x7f6850`), for any other client 0xff. Then 0x4d2ef0 -> session handler slot 53 |
| handler | Arcade's handler is `ZSessionHandlerSP` (vtable 0xbd1be4), slot 53 = **0x42deb0**(client, old, new, 1): 0x537700 writes the LOCAL player index `[gamedata+0x898]` = the police object; then `cmp [session+0x5c], 4` (Arcade) -> rules slot 137 (0x8f5e90, the body swap klchar.c uses) - which returns at once for a policeman (0x8f5eb0 `cmp byte [player+0x2723], 0 / jne`) |
| 0x4b2a0e | 0x4b6680 (a small per-type call, as the multiplayer client does) |
| 0x4b2a2c | once per client: if 0x67f480 says 'not over', 0x4ea400(client) (camera / HUD of the local client back to play) |
| 0x4b2a3c | flags 0x4000 and 0x800 cleared, 0x80000 set, `+0x74 = 10.0` |

Order of the arguments at the switch (0x4b29e3 .. 0x4b2a09): `0x4d2ef0(session, client index, old local
player index from 0x748540, new = record +0x14, 1)`; 0x4d2ef0 forwards to handler slot 53 unless the session
state is 0x2e. In 0x42deb0 the third argument is what goes to 0x537700; only `new == 0xff` skips it.

### 2.3a [2] The police objects are a budget: eight per level load, never given back (EXE)

- The table: `T = [handler + 8]` (handler = `[session + 4]`, `ZSessionHandlerSP` slot 17 = 0x6e2650 returns
  it): `[T]` entries of 12 bytes, `[T+4]` one 'slot in use' byte per entry (0 = in use), `[T+0xc]` the count.
  An entry: `+0` owner, `+4` the `ZFFPlayer`, `+8` a state byte, **`+9` used**.
- An entry is made when a player object registers with the session (`ZSessionHandlerSP` slot 54 = 0x50a1c0,
  index = `ZFFPlayer+0x91d`; constructor 0x458740 zeroes it). In Arcade that routine also hands the type
  byte, `+0x2740` and the model number `[[player+4]+0x68]` to rules slot 135 (0x5684f0).
- The used byte is set by the pick 0x54cab0 (0x54cb1a) and by NOTHING ELSE in single player. The two routines
  that clear it are `ZSessionHandlerMP` slots 57 (0x741930) and 59 (0x56f360) - there with calls that reset
  the player object (0x5797c0, the player's own slot 221, 0x694a90, 0x747ea0). `ZSessionHandlerSP` has the
  empty stubs 0x8bf680 / 0x66b570 in slots 55..59. So Arcade has no 'give the police body back'.
- Three callers of the pick: the respawn (twice, above), rules slot 9 (0x6a20c0) and **rules slot 197 =
  0x42bc80, the routine that sets up the local client's record: it already picks a police object (type 3)
  and writes it to record `+0x14`** (0x42bdc9). The round start then puts `+0x14` back to 0xff (0x817e10)
  without freeing the object. Whether the table is filled at that moment (the level's players registered
  before the client is set up) is not established: if it is, one of the eight is gone before the first
  round, and seven are left.
- The round start also clears all twelve flag dwords (0x8c7ad2), so every round's first respawn takes the
  'no flag 0x100, `+0x14` is 0xff -> pick' branch: one new object per round with a respawn.
- Rounds of a session run on the same loaded level (re\fa_round.md, live). So: **at most 8 (or 7) fed
  respawns per level load, then `int3`**. Against that: one respawn per round at most (a second death is
  final), each costs the life at the round end, and a session has only a few lives - the budget is not
  reached by play as long as the level is loaded again for the next session. The hook still has to count
  (pre-check in section 3) because nothing else stands between the ninth respawn and the `int3`.
- Reusing a body by data (clear the used byte at a round start, or write the same index to `+0x14` every
  time) is possible to write but leaves the object as the last round left it - a dead policeman. What a
  dead police player object does when it is made the local player again: not established, not proposed.

### 2.4 What the rest of the game does with a police human in Arcade (EXE)

- **AI**: `ZSoldier` slot 111 (0x882470, how much a soldier wants a player as target), 0x8824e7: a POLICE
  player is a target only for a soldier whose team is 2 (`[[soldier+0x40]+0x54]+4`; team 2 is the crew's:
  the kill rule 0x4859da tests the same value before looking up a bot's record). So **the AI heisters shoot
  the fed, the police AI leaves him alone.** The friend list 0x5706a0 and `ZSoldier` slot 96 (0x847805) have
  police-player branches behind `call 0x7f6850` / `call 0x7bb2a0`, i.e. written for Arcade.
- **Boarding**: 0x68414e `cmp byte [player+0x2723], 0 / jne` - a police player cannot board. He never
  'escapes'.
- **HUD**: the update sends the local client's state to the HUD (0x74bb74): escaped 3, dead 4, flag 0x1000 5,
  **police 2**, traitor 1.
- **Vehicle leaves** (0x805120): aboard -> escaped, then 0x67f480; when not over, 0x894450 counts criminals
  in play and police (status 0 with flag 8 or 0x80, or status 1 with flag 0x4000): with at most one of each
  the round clock is cut to 60 s (`[rules+0x204] = 7`). Otherwise the next vehicle.
- **A second death**: the kill rule again; slot 112 is false for police, so status stays 7. This class has
  no further respawn (the server class gives status 3 there).
- **Round end**: slot 192 takes a life when client 0 has no flag 0x40. A fed never has it: **coming back as
  a fed does not save the life** - it is what happens between the death and the round end. The Arcade level
  only advances when record 0 has status 6 (0x74bce4).

- **[2] Next round**: `ZSessionHandlerSP` slot 11 (0x466b30, state 0x18) makes the local player the hero
  again: `0x537700(gamedata, byte [hero+0x91d], 0)` with hero = `[rules+0x5fc]` (stored by slot 197 at
  0x42bcb2), places him at a START point (slot 199, type 1) and calls rules slot 34 (0x4b5b20) and slot 137
  for him. Slot 34 returns at once for a type-3 object (0x4b5b4f): masks and looks are never applied to
  the police body by the game.

Not established: where the police player gets his weapons. The item list has `eFF2ItemHG_Revolver_Police`
= 3 and `eFF2ItemShotgun_Hawk_Police` = 13; neither the police nor the hero object in the level names any
item (FILE: both have 23 properties, no controllers, no children - the hero's weapons are not level data
either). **[2]** Looked for and not found: none of the 91 places that read the police byte and none of the
places that read the type byte gives an item, and neither respawn routine (Arcade 0x4b28d0, server
0x6bb910 + client 0x63a0a0) gives one. ASSUMPTION: the weapons come with the player object itself, the same
in both modes, since the Arcade routine does every step the multiplayer pair does (object, AFTER_DEATH
point, police byte, local player). An unarmed fed is the first thing live check F1 has to rule out.
Also not read: what the fed's kills pay.

## 3. The player in Arcade: three ways, ranked

### P1. The data switch (recommended): `[0x168ea60] = 1` while the human is a living criminal

What the hook does, each tick, on the game's thread (new file, e.g. `klhook\klfed.c`, key `[Fed] Player=1`,
off by default):

```
armed =  Arcade ([session+0x5c] == 4, [session+0x54] not 2 / 3) and state [session+0x70] == 0x19
     and klx_level_verdict == 2 (not the stock level; Steam writes blocked)
     and rules vtable == 0xbd3514 and session handler vtable == 0xbd1be4
     and record 0 in use, its client block byte 0 == 0 (local)
     and ( record 0 status == 0 and the local player's +0x2723 == 0          -- a living criminal
        or record 0 status == 1 )                                            -- dead, waiting: keep it on until he stands
     and at least MinCrew AI records (flags +0x79 mask 1) with status 0      -- somebody left to hunt
     and at least one free police object: T = [[session+4]+8], entries [T], count [T+0xc], 12 bytes each,
         slot byte [[T+4]+i] == 0, ZFFPlayer at +4 (+0x273c == 3), used byte +9 == 0
                                                                             -- else 0x4b2984 is an int3 (2.3a)
[0x168ea60] = armed ? 1 : 0          (and 0 on unload / outside a round, always)
```

Why holding it changes nothing else: of the three callers of 0x67f480, the vehicle routine gets 'no' for a
living criminal on foot anyway (table in 2.2), and the hook takes the switch off the moment record 0 is
aboard (status 4), police, or dead for good. Precedent for a `.data` write next to heap writes: kljoin's
`[0x156b358] = 1`, live five times of five.

What the hook must add, all data:

- **End the round when nothing is left to do.** With the human as police nothing ends the round when the
  last criminal dies (the bot kill rule, slot 16 = 0x485740, has no such test) - it would run to the clock.
  When record 0 is police and no record has status 0 besides his, and the vehicle state `[rules+0x1dc]` is
  0 or 7: write once what the game writes in its own 'over' branch: `[rules+0x4c] = [rules+0x200] =
  [score+0x40] = 3.0` (slots 42 and 193). Slot 192 then ends the round by itself.
  **[2]** Slot 192 (0x5dff40) reads only `[rules+0x200]`: it subtracts the frame time and ends the round
  when that reaches 0 and the vehicle state is 0 or at least 7. The round reset writes 600.0 there
  (0x8c7a8b, float 0xb206d0). So without the hook's write the round does not hang: it ends by that timer,
  ten minutes after its start at the latest (ASSUMPTION that nothing refills it; slot 42 only lowers it).
- Optional, 'choose your police character' (re\netcode.md D): write record 0 `+0x14` = the wanted free
  police index and its used byte = 1 before the countdown ends; 0x4b28f8 then skips the pick.

What breaks or is not known:

| | |
|---|---|
| lives | lost as now (section 2.4). Giving it back would be a write of `[score+0x6c]` / `+0x44`: a rule change, not proposed |
| second death | final; the stock 'over' branch then cuts the clock to 3 s even if the crew still plays. Holding the switch through it instead leaves the human on the death camera until the hook's own round end. Coming back again = the hook writing status 1, `+0x08 = 5.0`, `+0x11 = 0`, flag 0x4000 set and 4 cleared (what 0x70482d does); 0x4b28f8 then takes a NEW police object each time (8 exist). Not proposed for the first version |
| no free police object | crash at 0x4b2984: the pre-check above. **[2]** The used byte DOES survive: nothing in single player clears it (2.3a). Eight respawns per level load, perhaps seven. The hook logs the table (index, type, used) at every round start and says so in the log when it stands down for want of a body |
| no AFTER_DEATH point | the fed stands where `Heroes!Henchmen_0N` was placed (outside the map). FILE: 7 points in every build looked at (M01: Dead Men's own seven; Retomoto: five in the tower at y 19601..19613, two in the street at y -50) |
| Retomoto | the two parts are joined by the hook's jump only: a fed spawned in the wrong part has to use the join himself. Either hide the wrong part's points (a hidden point is skipped, 0x561557) or accept |
| klchar.c | sees a new local player. Its body swap (slot 137) is refused by the game for a policeman, but its look call 0x88c810 is not: klchar must stand down while `[player+0x2723] != 0` (lead: one line; I did not edit the file) |
| klbot.c | its log calls record 0 'you'; status 1 and the police flag are new to it. No conflict found with Bribe / Leave / Van (they test status 0 / 4) |
| next round | the session handler puts the local player back on the hero (0x466b6b, state 0x18) and 0x817d20 resets the records. Whether the hero object is whole again after having died while another body was played: not established, must be seen |
| leaderboard / stats | unchanged from today: on a non-stock level klsteam.c blocks every write; on a stock level the hook does nothing |
| anti-tamper | no code byte changes, no import; one dword in the zero-filled `.data` |

### P2. After the fact, data only (fallback if P1 misbehaves)

Let stock run the 'over' branch, then undo it within the same tick sequence: record 0 status = 1,
`+0x08 = 5.0`, `+0x11 = 0`, flag 0x4000 set and 4 cleared, and the three clock floats put back from a copy
the hook took the frame before. The game's update then calls 0x4b28d0 itself. Worse than P1: the 'round
over' death camera and, with no criminal in play, the 'all dead' announcement have already been shown.

### P3. Calling 0x4b28d0(rules, 0) from the hook

Possible (a `__thiscall` with one byte argument, on the game's thread) but pointless: its preconditions are
exactly the data P2 writes, and with them the game calls it itself.

### Not possible for the player

- A rules flag, tuning value or game-mode field that turns it on: none exists. `ZOnlineFragileAllianceSettings`
  and the tuning object `[0x168d7c0]` are not read on this path; the only condition is 0x67f480.
- Running the real server class in Arcade: the session creates `ZGameRulesHeist` for mode 4; the Sv class
  sends RMCs to clients that do not exist.

## 4. The fed's body (FILE)

| body | where | note |
|---|---|---|
| Dog Days police player, model 1919 (F07 hosts; F01: 1526) | all eight `Heroes!Henchmen_0N` of every build | SWAT-style: materials `Police_SWAT_01` x2, goggles, balaclava, a holstered M77 (re\characters.md 4). One variant |
| **Dead Men's police-respawn body = an FBI agent**: black suit, sunglasses, headset | Dead Men M01_FA_A `Heroes!Henchmen_01..08`, model root 6336, 95 bones, 16 objects, 0.59 MB | materials `FBI_Agents_BlackSuit`, `SunGlasses_*`, `USA_Headset_01` (re\characters_graft.md table). `kl_chars` can put it on the eight police objects 'with one pick listing the eight targets joined by +' (same note, section 6): that is the fed |
| `FBI-Agents_01..04` | already in the M01 build: 10 actors on one model (35968 there), 8 variants | NPC model; usable for the AI feds on M01 at no cost |
| Dog Days street police / SWAT, models 718 (18 actors) and 841 (8) | F07's own `Gameplay!` squads: in the Retomoto build, NOT in the M01 / M06 builds | |
| Japanese police, models 52003 / 52248 / 52323 | Retomoto build | fits that map |

A model is a number (`[[entity+4]+0x68]`, klchar.c 2) and stock actors already wear player models (the
`Glazer_Bodyguard_0N` bots use `Hero_0N`'s chunk), so an AI fed can wear the police player's model at no
`.prm` cost. ASSUMPTION for the Dead Men FBI body on a Dog Days police player: that it behaves like the
Dead Men heroes that were seen working (wardrobe, run W5); its skeleton has 95 bones against the heroes' own.

## 5. The AI heisters

### 5.1 Not through the player's path (EXE)

Setting a bot's record to status 1 would make the update call 0x4b28d0(bot index): it takes a police
PLAYER object for the bot, places it at an AFTER_DEATH point, and ends in 0x42deb0, where
`0x537700(gamedata, new index, 0)` rewrites the LOCAL player index whatever client was named - the human
would be moved into that body. A `ZFFPlayer` is driven by input; the bots are `ZFFActor` + `ZSoldier`.

### 5.2 What a dead bot is, and what the rules do (EXE)

Slot 16 = 0x485740(actor, killer): 0x78f470 finds the record, flag 4, status 7, `+0x70 = 5.0`, kill text
and money. Nothing else: no respawn, no round test. No routine that revives an actor was found in the rules
classes (`ZFFPlayer`'s `Resurrect` is CEG-wrapped and for players, klbot.c 6).

### 5.3 The level-data way: a parked one-man police squad per heister

How squads fire lists (EXE, `ZSquadScript` slot 25 = 0x47e440, its update; members = actor pointers at
`[script+0x4c] .. [script+0x50]`, initial count `+0x48`, last count `+0x40`):

- living = 0x71adc0: `actor+0x576 != 0` and `actor+0x8f0 == 0` and `actor+0x5cd == 0`;
- per man lost: the list at `+0x78` (field 5); first loss: `+0x5c` (field 4, 0x51c8e0); half lost: `+0x94`
  (field 6, 0x649d30); one left: `+0xb0` (field 7, 0x86b470); **none left: `+0xcc` = field 8 (0x87ebf0),
  once** (byte `+0x20b`). Offsets against the schema: the 15 lists are fields 4..18 at `+0x5c + 0x1c * n`.
  This settles the ASSUMPTION of re\fa_gamemode.md finding 6.
- **the catch**: the boarding rule sets `actor+0x8f0 = 1` (0x684253) - a heister who boards is 'not living'
  for his squad, so field 8 fires for an escape too.

`TriggerActorsDead` is NOT the tool for this (EXE, slots 25 / 26 = 0x8def80 / 0x4afb80): it must first be
started by a message, and from then it fires when all its actors are dead **or after 0x7800 game ticks**,
whichever comes first, once. **[2]** A tick is 1/1024 s (the game converts the same counter with the double
0.0009765625 at 0xb5c498, e.g. 0x685427), so that is **30 seconds**: started at the round start it would
release the fed half a minute in, whatever the heister does. (Its 'dead' test 0x5f4470 is
`actor+0x576 == 0` and does not look at `+0x8f0`, so it would have been the deaths-only test - the timer
rules it out.)

**[2] From the crew record to the squad script by pointers alone** (EXE; every step has a vtable to check):

```
actor   = [record + 4]                 ZFFActor            vtable 0xbb3bac
soldier = [actor + 0x77c]              the actor's ZSoldier (0x7b390a)
squad   = [soldier + 0x4f4]            ZSquad@CPPScript    vtable 0xbccdac   (set by 0x7b3966; put to 0 when
                                                                               the soldier leaves, 0x523138)
script  = [squad + 0x164] - 0xe8       ZSquadScript        vtable 0xbcce3c   (check: [script + 0x3c] == squad,
                                                                               [squad + 0x168] == script + 0x104)
```

The last step: `ZSquadScript` slot 13 (0x6316b0) builds the squad object with pointers to ten of its own
lists (`script+0xe8`, `+0x104`, ... `+0x1e4`), and the constructor 0x7696f0 keeps them at `squad+0x164` ..
(0x7697f1). The pointer chain must be walked while the bot is alive (round start) and the script kept.
The script's count and latch fields are private to it: `+0x40`, `+0x48`, `+0x208` .. `+0x20d` are touched
only by its constructor 0x455c60, its member list (slot 14), its update (slot 25), its save / load (slots
21, 22) and 0x87ebf0. The 'fired' latch `+0x20b` is never cleared after the constructor.

The build (per heister `Squad#0N`, N = 2..8; stock objects only, re\bots_squad.md 3 and re\map_ai.md 2):

```
Gameplay!Feds!Fed#0N          [ZGROUP] @ZSquadScript   field 1 = eHeistOnly (Arcade only), field 3 = 0 (not in the world at load)
   \10_Hunt                   [ZGROUP] @HuntBehaviourRout
   \Fed_0N\Ground             [ZFFActor] @ZSoldier      a police soldier row (eArmy / eGuard as the map's own police),
                                                        model = the police player's (1919) or the map's fed model, a police weapon
Squad#0N  @ZSquadScript  field 8 += 'Gameplay!Feds!Fed#0N\10_Hunt'
```

placed at the AFTER_DEATH points (one each; M06 has five points for seven feds). A squad with field 3 = 0
enters the world when one of its routs is named ('they spawn in', seen live on Retomoto, re\map_ai.md 2).
A police soldier attacks the crew and the criminal player as every stock police soldier does; when the
human is himself a fed the police AI ignores him (2.4).

About the catch: without anything more, a heister who escapes also releases his fed (from the police spawn,
while the vehicle waits at most 8 s). Three answers, cheapest first:
1. accept it for the first live run and look (an escaped heister 'sends' one more policeman after the
   rest of the crew - not far from what the mode does to those left behind anyway);
2. level data: route field 8 through a gate that the vehicle's arrival closes (the monitor's 'vehicle n was
   called' lists are empty in stock and free, re\map_ai.md 2). ASSUMPTION: `GatePath` blocks a message when
   closed - not read;
3. **[2]** the hook, data only, section 5.4 - the one that is exact.

Cost: 7 squads x about 5 entities; no model, no texture when the police player's model is used.

Between rounds: the heister squads' latches and the released feds are level state. How Arcade puts the
level's AI back for the next round on the same loaded level was not read (the bots do play again, so their
squads are reset somehow; `+0x20b` has no writer that clears it besides the constructor and the load slot
22). ASSUMPTION: the squads are built anew or loaded from a saved state, as stock's own field-8 chains
(F01: 9 squads) would otherwise work in the first round only. Live check F5 has to show a fed in round 2.

### 5.4 [2] The hook's part for bots: deaths only, two data writes (no game call)

The hook cannot release a squad by itself (that is a message to a rout), but with the pointer chain of 5.3
it can decide WHEN the heister squad's own field 8 fires. From the update (0x47e440): the lists are only
looked at when `living < [script+0x40]`; field 8 then fires when `living == 0` and `[script+0x20b] == 0`.

```
round start, per AI record (flags +0x79 mask 1, status 0):
    walk the chain, keep script; require [script+0x48] == 1 (a one-man squad) and its vtable
    byte [script+0x20b] = 1                       -- muted: boarding and death both fire nothing
record status becomes 7 (dead; never for 4 / 5 / 6):
    byte [script+0x20b] = 0 ; dword [script+0x40] = 1
    -- next update: living 0 < 1 -> field 8 fires once (0x47e509 .. 0x47e518) and latches again
```

What else the second write re-runs: the per-man list (field 5, `+0x78`) once more; fields 4, 6, 7 are
latched by `+0x208`, `+0x20a`, `+0x209` from the real death. FILE: the heister squads' fields 4..18 are all
empty (stock: re\bots_squad.md; build `u_maps\M01`: `Gameplay!merc_bot_squad!Squad#02..08` read again,
one man each), so only field 8 - the fed - is sent. The Retomoto build `rt_guns3\retomoto_ai3_guns` showed
no squad under that name in the same survey: where its AI heisters' squads are was not followed up.
ASSUMPTION it rests on: the script's update still runs after its only man has died. If live check F5 shows
it does not, the variant without that need: leave the squad un-muted and write `[script+0x20b] = 1` when
the record reaches heist stage 3 (at the vehicle, record `+0x78`, klbot.c 1) - a heister who dies beside
the vehicle then has no fed, everything else is exact.
Not usable in Arcade: the script's pending-event mask `+0x20e` (bit 0x10 = 'fire field 8') is only read
when `[session+0x54] == 3` (0x4b0a40, a network client).

A message sent by the hook (a game call on a rout found by name) stays possible and stays pointless.

## 6. Ranking, and what is impossible

**(a) The player**
1. **P1**: hold `[0x168ea60] = 1` while he is a living criminal; the game does everything. Plus the
   round-end write and the pre-checks. One new hook file, data writes only. EXE-supported end to end.
2. P2: the same result written after the stock 'over' branch. Fallback.
3. P3: a call of 0x4b28d0. No advantage.

**(b) The AI heisters**
1. **Level data**: one parked police squad per heister on the heister squad's field 8 (0x87ebf0). No hook.
   Catch: fires for a boarding too. Build this first; it is also the base of 2.
2. **[2] The same plus the hook's mute / re-fire** (5.4: `[script+0x20b]`, `[script+0x40]`, script found
   through `record+4 -> +0x77c -> +0x4f4 -> [+0x164] - 0xe8`): deaths only. Data writes, behind its own key.
3. The same plus a level-data gate instead of the hook (`GatePath` not read).
4. A message sent by the hook. More code, same effect as 1.
Not a way: `TriggerActorsDead` (fires after 30 s by itself).

**Impossible, or not supported by anything in the exe**
- A bot's crew record through 0x4b28d0 (takes the human's controls, 5.1).
- An AI heister as a police PLAYER object, or a dead actor revived as police (5.2).
- A setting, tuning value or game-mode field that enables the player's respawn (section 3).
- More than eight fed respawns per level load (8 police objects, one used up per respawn, none ever
  released in single player, 2.3a) - short of the hook calling the multiplayer handler's release steps on
  a player object, which nothing here proposes.
- `TriggerActorsDead` as the bots' death test (its own 30 s timer, 5.3).
- Keeping the life: the rules take it for 'did not escape', and a policeman cannot board.

## 7. Live checks for the lead, in order (all on a map that is not stock, Steam guard on)

- **F0** (log only): at a round start print the player table (index, type byte, used byte, model) and
  record 0's `+0x14`. Expect eight entries of type 3 and `+0x14` = ff; **used 0 on all eight, or 1 on the
  first** if slot 197 found the table filled when the session was joined (2.3a) - that settles 8 or 7.
  Also per AI record the chain of 5.3 (actor, soldier, squad, script, `+0x40`, `+0x48`, `+0x20b`).
- **F1** `[Fed] Player=1`, bots present, die: record 0 status 7 -> 1 in the same frame, 'You respawn as
  police' after 1 s, at 5 s the local player index changes to a type-3 object, flag 8, the picture shows the
  police body at an AFTER_DEATH point. Then: do the heisters shoot you, do the police ignore you, weapons?
- **F2** kill the last heister / let them escape: the hook's round end (3 s), score page, one life less,
  next round starts on the hero again and plays.
- **F3** die as a fed: round over in 3 s (stock branch).
- **F4** a second round with a death: the used bytes of F0 again. Expected by the code: object 1 is still
  used and the second respawn takes object 2.
- **F5** bots: an M01 build with `Fed#02..08`: kill one heister -> its fed appears and hunts; let one board
  -> does a fed appear (the catch)? Then a second round: do the feds of round 1 leave, and does a heister's
  death release a fed again (the latch `+0x20b` after the level's reset)?
- **F5b** the hook's mute / re-fire (5.4): boarding releases nobody; a death releases the fed within a
  frame or two of the log's 'dead' line. If nothing comes: the script's update has stopped - use the
  stage-3 variant.
- **F6** Retomoto: where the fed spawns relative to the crew.

## 8. Not established

- The police player's weapons (looked for twice, 2.4) and what his kills pay in Arcade.
- Whether slot 197 already uses up one police object when the session is joined (F0), and whether the hero
  object is whole again at the next round after another body was played (F2). The used byte itself is
  settled: it does not recover (2.3a).
- What flag 0x80 and the player byte `+0x2729` are (both must be 0 for the path; they are in Arcade as far
  as read - `+0x2729` is tested together with rules slot 188 in the AI code).
- `GatePath` as a message gate.
- How the level's AI (squads, their latches, released men) is put back between two Arcade rounds on the
  same loaded level, and whether a squad script's update still runs once all its men are dead (5.3, 5.4).
- Field 8 in stock: settled since - F01 uses it on 9 squads, F03 on 8 (re\stock_mod.md); no stock AI-heister
  squad uses it (their fields 4..18 are empty).
- Dead Men's exe was not read for this note.

## 9. [2] What the second pass read again, and found as written

Disassembled again from the exe, statement by statement: 0x67f480 whole (the gate, its table in 2.2, the
`cmp dword [0x168ea60], 0` head) and its twin 0x86f520; the references to 0x168ea60 (two, both compares;
0x168ea64 .. 0x168ea9c likewise only compared or loaded, the two words before it belong to static objects
with their own exit routines at 0xb03040 / 0xb03060); the three callers of the gate; the kill rule
0x704610 whole (it returns early for status 1 and 3, not for 7); the respawn 0x4b28d0 whole, the pick
0x54cab0, 0x748540, 0x4d2ef0, 0x42deb0, 0x7622f0, 0x43e270; the handler's round start 0x466b30; the round
reset 0x8c7a80 / 0x817d20; slots 42, 192, 193; the soldier's target test 0x882470; the boarding rule
0x6840a0 (police refused at 0x68414e, `actor+0x8f0 = 1` at 0x684253, which the round reset clears at
0x817e7c); the squad script's update 0x47e440, its count 0x71adc0, 0x87ebf0, its member list 0x7b3790;
`TriggerActorsDead` 0x8def80 / 0x4afb80 / 0x5f4470. Vtables by RTTI: 0xbd3514 `ZGameRulesHeist`, 0xbd1be4
`ZSessionHandlerSP`, 0xbb3bac `ZFFActor`, 0xbcce3c `ZSquadScript`, 0xbccdac `ZSquad@CPPScript`.
FILE again on the current builds `<work>\build\u_maps\M01, M02, M03, M06`: 16 `ZFFPlayer` each, 8 of type
`MULTIPLAYER_POLICEMAN` (`Heroes!Henchmen_01..08`, rank NONE, animation set Lynch); AFTER_DEATH points
7 / 7 / 7 / 5, START 8 each.
Not read again (taken from the first pass): the death camera display 0x728580, the friend list 0x5706a0,
`ZSoldier` slot 96, 0x805120 / 0x894450, the bot kill rule 0x485740 beyond its status write (0x48581d), the
model table of section 4.
Corrections to other notes: klbot.c 1 says of the record status '1 and 3 exist, not read' - they are 1 =
dead and waiting to return as police, 3 = a timed state before spectating (2, top); `kl2.exe` has no
single-player release of a police object, which no earlier note says.
