# Coming back as a fed: the dead criminal as police, for the player and for the AI heisters

Owner, 2026-10-10: 'i want to make it so you can come back as a fed or the ai heisters can come back
as feds too'. Research only. Written 2026-10-10 from `kl2.exe` build 0490 (disassembly, `debug\kl.py`)
and from level files (stock F07, the builds `<work>\build\b_bots\M01`, `b_bots\M06`,
`rt_guns3\retomoto_ai3_guns`). **Nothing here was run in the game.** No file but this one was written.

Status words: **EXE** = read in the disassembly, address given. **FILE** = measured in level files.
**ASSUMPTION** = inferred, said why. **not established** = looked for, no answer.
Scratch tools (disassembler with vtable owners, cross-reference search, level surveys): session scratchpad
`fed\x.py`, `scan.py`, `vts.py`, `lv2.py`, `sp.py`.

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
   counts as 'not living' there, so the list fires for an escape as well (section 5.3).
5. **The fed's look exists already.** Dead Men's own police-respawn body is an FBI agent in a black suit
   with sunglasses and a headset (M01_FA_A `Heroes!Henchmen_01..08`, one model, 0.59 MB); every build
   already carries Dog Days' police player model (number 1919 in the F07-hosted builds), and the M01 build
   has `FBI-Agents_01..04` (10 actors, one model with 8 variants).
6. **Impossible**: an AI heister driving a police PLAYER object; a dead actor standing up again as police;
   the crew record of a bot going through the player's respawn routine (section 6).

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

Not read: where the police player gets his weapons (the item list has `eFF2ItemHG_Revolver_Police` = 3 and
`eFF2ItemShotgun_Hawk_Police` = 13; the object in the level names none), what the fed's kills pay, and
whether the session's 'used' byte of a police object is cleared between rounds.

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
         ZFFPlayer at +4 (+0x273c == 3), used byte +9 == 0                   -- else 0x4b2984 is an int3
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
- Optional, 'choose your police character' (re\netcode.md D): write record 0 `+0x14` = the wanted free
  police index and its used byte = 1 before the countdown ends; 0x4b28f8 then skips the pick.

What breaks or is not known:

| | |
|---|---|
| lives | lost as now (section 2.4). Giving it back would be a write of `[score+0x6c]` / `+0x44`: a rule change, not proposed |
| second death | final; the stock 'over' branch then cuts the clock to 3 s even if the crew still plays. Holding the switch through it instead leaves the human on the death camera until the hook's own round end. Coming back again = the hook writing status 1, `+0x08 = 5.0`, `+0x11 = 0`, flag 0x4000 set and 4 cleared (what 0x70482d does); 0x4b28f8 then takes a NEW police object each time (8 exist). Not proposed for the first version |
| no free police object | crash at 0x4b2984: the pre-check above. Whether the used byte survives into the next round is not established - the hook should log the table (index, type, used) at every round start |
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

`TriggerActorsDead` is NOT the tool for this (EXE, 0x8def80 / 0x4afb80): it must first be started by a
message, and from then it fires when all its actors are dead **or after 0x7800 game ticks**, whichever
comes first, once. (Its 'dead' test 0x5f4470 is `actor+0x576 == 0` and does not look at `+0x8f0`.)

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
1. accept it for the first live run and look;
2. level data: route field 8 through a gate that the vehicle's arrival closes (the monitor's 'vehicle n was
   called' lists are empty in stock and free, re\map_ai.md 2). ASSUMPTION: `GatePath` blocks a message when
   closed - not read;
3. hook, data only: klbot.c already sees stage 3 (at the vehicle) per record; writing the heister squad's
   `+0x20b = 1` then would mute field 8 for a boarding. Needs the way from a bot's actor to its
   `ZSquadScript` object, which was not read.

Cost: 7 squads x about 5 entities; no model, no texture when the police player's model is used.

### 5.4 The hook way for bots - not recommended

The hook knows the death exactly (record status 7, not 4) but has no data switch to release a squad: a
squad is released by a message to one of its routs. Sending one is a game call on an object the hook would
first have to find by name (klauto.c does that for menu elements only). Possible, more code than 5.3 and
nothing gained except the boarding catch, which 5.3 answer 3 solves with one byte.

## 6. Ranking, and what is impossible

**(a) The player**
1. **P1**: hold `[0x168ea60] = 1` while he is a living criminal; the game does everything. Plus the
   round-end write and the pre-checks. One new hook file, data writes only. EXE-supported end to end.
2. P2: the same result written after the stock 'over' branch. Fallback.
3. P3: a call of 0x4b28d0. No advantage.

**(b) The AI heisters**
1. **Level data**: one parked police squad per heister on the heister squad's field 8 (0x87ebf0). No hook.
   Catch: fires for a boarding too.
2. The same plus the mute byte (`+0x20b`) or a gate, to make it deaths only.
3. A message sent by the hook. More code, same effect.

**Impossible, or not supported by anything in the exe**
- A bot's crew record through 0x4b28d0 (takes the human's controls, 5.1).
- An AI heister as a police PLAYER object, or a dead actor revived as police (5.2).
- A setting, tuning value or game-mode field that enables the player's respawn (section 3).
- More than eight fed bodies for players (8 police objects; one is used up per respawn).
- Keeping the life: the rules take it for 'did not escape', and a policeman cannot board.

## 7. Live checks for the lead, in order (all on a map that is not stock, Steam guard on)

- **F0** (log only): at a round start print the player table (index, type byte, used byte, model) and
  record 0's `+0x14`. Expect eight entries of type 3, used 0, `+0x14` = ff.
- **F1** `[Fed] Player=1`, bots present, die: record 0 status 7 -> 1 in the same frame, 'You respawn as
  police' after 1 s, at 5 s the local player index changes to a type-3 object, flag 8, the picture shows the
  police body at an AFTER_DEATH point. Then: do the heisters shoot you, do the police ignore you, weapons?
- **F2** kill the last heister / let them escape: the hook's round end (3 s), score page, one life less,
  next round starts on the hero again and plays.
- **F3** die as a fed: round over in 3 s (stock branch).
- **F4** a second round with a death: the used bytes of F0 again (is object 1 free again?).
- **F5** bots: an M01 build with `Fed#02..08`: kill one heister -> its fed appears and hunts; let one board
  -> does a fed appear (the catch)?
- **F6** Retomoto: where the fed spawns relative to the crew.

## 8. Not established

- The police player's weapons and what his kills pay in Arcade.
- Whether the used byte of a police object and the hero object recover at the next round (F2, F4).
- What flag 0x80 and the player byte `+0x2729` are (both must be 0 for the path; they are in Arcade as far
  as read - `+0x2729` is tested together with rules slot 188 in the AI code).
- `GatePath` as a message gate; the way from an actor to its `ZSquadScript`.
- Whether a bot squad's field 8 is ever used by stock (the code path is common to all squads).
- Dead Men's exe was not read for this note.
