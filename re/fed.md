# Coming back as a fed: what was built (2026-10-10)

Owner, 2026-10-10: 'i want to make it so you can come back as a fed or the ai heisters can come back as
feds too'. Research: `re\fed_respawn.md` (two passes). This note: what was built from it, the keys, the
live checks in order. **Nothing here has run in the game. Nothing is installed, nothing is committed.**

| file | what |
|---|---|
| `klhook\klfed.c` (new) | the hook's part: data writes only, no game call, no code byte, no import slot |
| `tools\kl_fa_fed.py` (new) | level data: one parked police soldier per AI heister on a finished bots build |
| `<work>\build\x_fed\M02` (+ `M01`, `M03`, `M06`) | the builds, from `<work>\build\u_maps\<map>`; logs beside them (`<map>.build.log`, `.bots_check.log`, `.audit.log`, `.impact.log`, `.preflight.log`, `.fed_check.log`) |

Status words as in the research note: **EXE** = read in `kl2.exe` 0490 for this work (`debug\dasm.py`),
**FILE** = measured in level files, **ASSUMPTION**, **GUESS**.

## 0. Short answers

1. **(a) The player comes back as a fed: built**, `[Fed] Player=1`. One dword of zero-filled `.data`
   (0x168ea60) is held at 1 while the human is a living criminal with somebody left to hunt; the game's own
   Fragile Alliance path does everything else (5 s death camera, a police body, an AFTER_DEATH point, the
   police flag, the switch of the local player). The hook also ends the round when a fed has nobody left
   (three floats, what the game's own 'over' branch writes).
2. **(b) A dead AI heister comes back as a fed: built as level data** (`kl_fa_fed.py`), with the hook
   making it exact (`[Fed] Bots=1`). Each heister squad's 'no living man left' list names the hunt rout of
   a one-man police squad that is not in the world until then.
3. **What the key `Bots` can and cannot be.** The level data acts by itself: on a `x_fed` build a fed is
   released when its heister dies **and also when he boards the escape vehicle** (the game counts a boarded
   man as 'not living', EXE 0x71adc0 / 0x684253). The hook cannot make level data inert and cannot release
   a squad by itself (that is a message = a game call). What it can do with two data writes per heister:
   `Bots=1` deaths only, `Bots=2` no AI fed at all on that very build. So the switch for 'AI feds at all'
   is **which build is installed** (`u_maps` or `x_fed`), and the key refines it.
4. **Not built, because the exe does not support it** (section 6): an AI heister in a police *player*
   body, a dead actor standing up again, keeping the life, more than 8 returns per level load.

## 1. Addresses verified again for this work (EXE)

All of `re\fed_respawn.md` section 9's list that the two files rely on was disassembled again and holds:
the gate 0x67f480 whole (its head `83 3d 60 ea 68 01 00 56 8b f1 74 04` is compared by the hook before
arming); 0x168ea60 has exactly two references in the image, 0x67f482 and 0x86f522, both compares, and
lies in no hashed range of `klranges.h`; the kill rule 0x704610 (0x7047b5 call, 0x70482d status 1, slot
112 = 0x4549f0 refuses flags 8 / 0x80); the respawn 0x4b28d0 (`int3` at 0x4b2984, the pick 0x54cab0, the
table `[[session+4]+8]` through `ZSessionHandlerSP` slot 17 = 0x6e2650); 0x660b00 / 0x537700 (local
player); 0x7622f0 (police byte + flag 8); slots 42 / 192 / 193 (0x47d190, 0x5dff40, 0x642850: the three
clock floats, 3.0 at 0xb4a174, 600.0 at 0xb206d0); the squad script's update 0x47e440, its count
0x71adc0, 0x87ebf0; the chain actor +0x77c -> soldier (+0x40 back to the actor) -> +0x4f4 squad ->
`[squad+0x164] - 0xe8` script (0x7b390a, 0x7b3966, 0x6316b0, 0x7697f1). Vtables by RTTI: 0xbd3514,
0xbd1be4, 0xbb3bac, 0xbccdac, 0xbcce3c, and `ZFFPlayer` 0xbb45f4 (new).

Found beyond the research note:

- **0x47e70c .. 0x47e71c**: when the living count is ABOVE `[script+0x40]` the update raises `+0x40` to it
  (and clears `+0x20d`). So a squad's count follows men coming into the world, and the hook's write of
  `+0x40 = 1` is the value the field had while the heister lived.
- **`klchar.c` needs no change**: its line 274 already returns unless the local player's type byte is 2
  and his police byte is 0 (the research note asked for a line there).
- FILE: a `ZBoxPrimitive`'s three values are its FULL size (the root's group tree lists a hunt group with
  exactly centre +- size / 2 of its search box, on stock F03 and on the M02 build: 5000 / 2500 / 7000
  against 1204 / 603 / 1687 quantised units, one scale). `kl_fa_bots.INSIDE` had left that open.
- FILE: an actor group's `aux` follows the actor's MODEL (hero N and the AI heister in its model share
  one value on M02, M06 and stock F07; the eight police player groups: 13).
- FILE: **the AFTER_DEATH points are not on the crew's navigation mesh on three of the four maps.**
  M01: seven points on a roof, a mesh part of its own (16 polygons, 8.9 m above the street). M02: seven
  points 20 m outside every polygon. M06: five points 13.8 m above the mesh. Only M03's seven stand on the
  START row's part. A police PLAYER drops or walks in from there; an AI soldier cannot (section 3).

## 2. The hook: `klhook\klfed.c`

Its top comment is the spec. In short:

- **Where it acts**: an Arcade session ([session+0x5c] == 4, [session+0x54] not 2 / 3), round running
  ([session+0x70] == 0x19), rules object `ZGameRulesHeist`, and the level is NOT the stock one of its slot
  (`klx_level_verdict == 2`, the verdict under which klsteam.c blocks every Steam write; the same gate as
  klbot.c section 0, written again in this file). The log part reads only.
- **Player** (`Player=1`): each tick on the game's thread `[0x168ea60] = armed`, where armed = record 0
  is the local human AND (status 1 = dead and waiting, held until he stands; OR status 0, the local player
  a criminal `ZFFPlayer` with police byte 0, client flags 0x88 clear, at least `MinCrew` AI heisters in
  play, at least one free police body in the session's player table). Off the moment he is aboard, police,
  out of the round, the round is not running, the level is stock, or anything cannot be read - from the
  fallback thread too; ON only from the game's thread. A value there that this hook did not write is left
  alone. **No free police body = the game's `int3` 0x4b2984**: the hook counts the table before arming and
  stands down with a log line.
- **Round end** (`EndSeconds=3`): when record 0 is in play as police and no other record is in play,
  waiting or aboard, once per round: `[rules+0x4c] = [rules+0x200] = [score+0x40] = EndSeconds` if the
  clock is later. Slot 192 then ends the round itself and takes the life (a fed did not escape).
- **Bots** (`Bots=1`): per AI crew record the squad script is found by the pointer chain (every step
  checked: three vtables, two back pointers, a one-man member list holding that actor). In play: byte
  `[script+0x20b] = 1` (muted). Record status 7: `[script+0x20b] = 0`, dword `[script+0x40] = 1`; the
  game's next update sends field 8 once and sets the byte again; the hook watches that for 5 s and says
  which. `Bots=2`: muted and never released. A chain that fails a check is left alone and said.

### KLHook.ini

```
[Fed]
Enable=0          1 = klfed.c is on (then only the log)
Log=1             0 none, 1 the round's table and every change, 2 also a line a second
Player=0          1 = the dead player comes back as police
MinCrew=1         AI heisters that must be in play for the return to be armed
EndSeconds=3      the hook's round end when a police human has nobody left to hunt; 0 = leave it to the clock
Bots=0            0 = the level data alone (fed at a heister's death AND when he boards), 1 = deaths only,
                  2 = muted: no AI fed
```

### The lead's three lines in `klhook.c`

```
#include "klfed.c"           after  #include "klbot.c"
klp_tick(game_thread);       in klh_tick, after  klb_tick(game_thread);
klp_init();                  in DllMain, after  klb_init();
```

plus the `[Fed]` block in `klhook\KLHook.ini`, a row `klfed.c  x  x  the dead return as police (data only)`
in the file table, and two rows in the patch-site table: `0x168ea60  round-never-ends switch = 1 / 0  ST
.data  0 checks  NOT RUN` and `[squad script]+0x20b, +0x40  latch / count  ST  heap  outside  NOT RUN`.
klfed.c needs nothing of klbot.c; it uses `klog`, `klh_rd`, `klh_rd32`, `klh_data`, `klh_scene`, `KLH_VA`,
`klh_exe_ok`, `klh_ini`, `KL2_GAMEDATA` and klsteam.c's `klx_on` / `klx_level_verdict`.

### Compile check and off-game test

Scratch copy of `klhook` (session scratchpad `klhook_fed`, a path without spaces) with exactly those three
lines: `build.bat` -> SHIP `dinput8.dll` 251,904 bytes, `build_auto.bat` -> TEST 301,056 bytes, both at
`/W3` without a warning. `klhook.c` in the repo is untouched.
Off-game test `klfed_test.c` (same scratch folder; klfed.c included as it is over made-up session, rules,
score, handler, player table, players, actors, soldiers, squads and scripts, the kill rule's two branches,
the respawn and the script update simulated as read in the exe): **52 PASS, 0 FAIL** - armed / not armed in
every case above, the stand-down without a free body, nothing written on a stock or unknown level or with
the guard off, ON never from the fallback thread, a foreign value left alone, the gate's code compared,
the round-end write once, mute / release / 'sent' / time-out, every refusal of the chain, a second round.
That proves the file's own logic and nothing about the game.

## 3. The level data: `tools\kl_fa_fed.py`

`python tools\kl_fa_fed.py build <bots build> <out>` (docstring = the spec; `plan`, `check`, `diff` too).
Per heister squad `Gameplay!merc_bot_squad!Squad#0N` (N = 2..8), five entities:

```
Gameplay!Feds!Fed#0N          ZGROUP + ZSquadScript   eUnleashed, eHeistOnly (Arcade only), field 3 = 0 (not in the world)
   \10_Hunt                   ZGROUP + HuntBehaviourRout {its SearchBox, 1, [], 1, 0}    stock F03's form, cloned
      \SearchBox              ZBoxPrimitive
   \Fed_0N\Ground             ZGROUP \ ZFFActor + ZSoldier, team Enemy
Squad#0N  @ZSquadScript  field 8 += ROOT\Gameplay!Feds!Fed#0N\10_Hunt
```

Stock precedent, FILE: F03 `Gameplay!40_SWAT_Reinforcement_01..04` are exactly this - `eUnleashed`, field
3 = 0, a `HuntBehaviour` child with those values, named from other squads' field 8 (they are
`eFragileAllianceOnly`; all five stock hunt routs have the values 1, [], 1, 0).

- **The body** is a whole copy of one of the map's own police actors (group + actor + soldier row: model,
  animation set, weapon, voice sets, .SND offsets as they are - a combination this level already runs):
  M02 `AIEnemies!PoliceSwats\PoliceSwats_01..04` in turn (model 56875, AK-74 / FN SCAR, eArmy, health
  175), M03 `ArrivingCops_Squad_02\Reinforcement_03 / 04` (model 59891), M01 the `FBI-Agents_01` actor
  (model 35968, Dead Men's FBI agent). **M06 has gangs and no police**: there (and with `--body player`)
  the fed is the police PLAYER's model (1919, the body the human comes back in) on the heisters' own actor
  form: actor model = the player object's, group aux = the player group's, animation set = the player's +
  `_NPC`, stock F07's SWAT soldier row and AK-74, team Enemy. That is how stock dresses its AI heisters in
  the heroes' models; for model 1919 it is an **ASSUMPTION** (`check` says it as a NOTE per fed).
- **The place.** 'At the map's AFTER_DEATH points' is literally possible on M03 only (section 1). Rule:
  where the points stand over the START row's mesh part the feds stand round them, 110..600 away and 110
  apart (never ON a point: a police player may appear there in the same second); else on the START row's
  part at the place nearest to the points in the plan: M02 20.5 m away, M01 5.9 m away and 8.9 m below,
  M06 1.5 m away and 13.8 m below. Each place is on a polygon of the crew's part with clearance to the
  walls, and a path on the mesh to the START row exists (M02: 149..157 m of path).
- **The hunt box**: the map's own largest hunt search box if the feds' places, the START row and the
  boarding place are inside it, else the bounds of the START row's mesh part (all four maps: the second -
  none of the maps' own boxes reaches the escape vehicle). GUESS: what the box means to the rout was not
  read ('where to look', by its name).
- **Cost**: 35 entities, 14 groups listed in the root's group tree (as stock F03 lists its reinforcement
  squads). No model, texture, animation or sound: `.prm .ANM .fxc .WAV` keep their size (`apply` refuses
  otherwise). Members changed: `.prp .gms .buf .oct .rmi .rmc`, and the `.prm`'s 4-byte .oct record offsets
  in place - the same writing as `kl_fa_bots.apply`. `--no-tree` leaves the `.oct` layout and the `.prm`
  alone, for an A / B run.

### The builds

`python tools\kl_fa_fed.py build <work>\build\u_maps\M02 <work>\build\x_fed\M02` and the same for M01, M03,
M06 (the task asked for M02; the other three are there because the tool had to be shown on a map with its
points on the mesh and on one without police). On each of the four:

| check | result |
|---|---|
| `kl_fa_fed.py build` (plan, write, check, diff) | exit 0; check PASS 0 FAIL (M06: 7 NOTE = the player-model body); diff 'only the feds and their list entries were added' |
| `kl_fa_bots.py check` | PASS, 0 FAIL; the same NOTE count as the `u_maps` source (M02 0, M01 0, M03 8, M06 1) |
| `kl_maps.py audit` | PASS, '0 findings that must be 0', the same known findings as the source |
| `kl_impact.py` | problems: 0 |
| `kl_maps.py preflight` | exit 0 (0 CRASH) |
| the four large blocks | M02 `.prm` 55,449,184 `.ANM` 22,202,472 `.fxc` 17,760,648 `.WAV` 22,527,568: before = after |

`diff` proves through `kl_fa_bots.diff` that every old entity record, every slot id by entity, the room
trees, the collision records, every other member and the files beside the archive are as they were, and
on top that each heister squad differs in one new entry of field 8 and nothing else.
M02: the feds stand at (2402..2842, 0, -1308..-948), the mall's ground floor, 23..27 m from the START row
in the plan and two floors below it.

## 4. Live checks for the lead, in order (a map that is not stock, Steam guard on, one variable a run)

Every line below is in `<DD>\KLHook.log` with the prefix `fed:`.

| | set | do | proof |
|---|---|---|---|
| **F0** | `[Fed] Enable=1` only, the installed bots build | start a round | `fed: round 1: rules ..., 8 crew record(s), 7 AI ..., record 0 is the local human, status 0, police index ff ...` and `fed: police bodies: ... (N entries, 8 of type 3, 8 free)`. **8 free or 7** settles whether joining the session uses one up (research 2.3a). Each body's `model` number is printed |
| **F0b** | + `Bots=1`, still the `u_maps` build (no fed data: the writes send an empty list) | let one heister die, one board | `fed: bot N (actor ...): squad script ... (squad ..., 1 man, latch 0, count 1): MUTED` for all seven = the pointer chain holds. Death: `fed: bot N is DEAD: latch 0 and count 1 written ...` then **`fed: bot N: the game sent the list after .. ms`** = the script's update still runs for a dead squad (the ASSUMPTION Bots=1 rests on). `... still 0 after 5 s` = it does not: Bots=1 cannot work, use Bots=0. Boarding: `fed: bot N is aboard: muted, no fed` |
| **F1** | `Player=1`, bots present | die | `fed: ARMED: your death will not end the round ... (7 AI heister(s) in play, 8 of 8 police bodies free)` before; at the death `fed: you: status 0 -> 1 (dead, waiting to return as police; countdown 5.0 s ...)`; 5 s later **`fed: YOU ARE A FED: local player object N (..., type 3, police byte 1) at (x, y, z); client flags ...8...; N of 8 police bodies still free`** and `fed: stood down: you are police`. Picture: the police body at an AFTER_DEATH point, 'You respawn as police' on the death camera. Then by eye: armed? do the heisters shoot you, do the police leave you alone? (An unarmed fed is the one thing the research could not rule out.) |
| **F2** | same | kill the last heister, or let them escape | `fed: nobody is left to hunt: the round clock N s -> 3.0 s`, the score page, one life less, the next round starts on the hero (`fed: round 2 ...` with `local player object` back on a type-2 object) |
| **F3** | same | die as a fed | the stock 3 s end; no `status 7 -> 1` line |
| **F4** | same | a second round with a death | `fed: police bodies:` of round 2 shows the first body `used 1`; the second return takes the next; the line `... N of 8 police bodies still free` counts down |
| **F5** | `Bots=0` (or `Enable=0`), build `x_fed\M02` in the slot | kill one heister far from the vehicle; later let one board | by eye / picture: a SWAT man comes from the mall's ground floor round (2600, 0, -1100) and hunts; the same when a heister boards (the catch). klbot's log gives the time of the death (`bots: record N (bot): dead`) |
| **F5b** | `Bots=1`, the same build | the same | `MUTED` x7; boarding: no fed; death: `is DEAD ...` + `the game sent the list` and the fed within a second |
| **F5c** | `Bots=2` | the same | no fed at all (control) |
| **F6** | F5b, a second round | kill a heister again | `fed: round 2`, `MUTED` again (with `latch 1` if the game kept round 1's latch), `the game sent the list` again - and by eye whether a fed comes a second time and where round 1's feds went (not known) |
| **F7** | `Player=1 Bots=1` on `x_fed\M02` | die, then watch | both: the AI feds do not shoot a police human (EXE 0x8824e7), the heisters do |

Rules for these runs as for every live run on a grafted map: do not Quit inside a session; the guard must
be on (klfed.c does nothing but log without it). If the game ever stops at `kl2.exe+0b2984` the body count
was wrong: that line and the `fed: police bodies:` line before it are what to send back.

## 5. What the owner gets, in plain words

- Die with AI heisters still in play: five seconds of death camera, then you stand as a policeman at the
  map's police spawn and hunt them. They shoot you; the police do not. You cannot board the vehicle. When
  nobody is left the round ends three seconds later. **The life is still lost** (the rules take it for 'did
  not escape'), a second death in the round is final, and it works at most 8 times per level load.
- A heister who dies sends one policeman after the rest of the crew - and after you.

## 6. Not built, and why

| | why |
|---|---|
| an AI heister in a police PLAYER body | the game's respawn 0x4b28d0 ends in 0x537700, which rewrites the LOCAL player index for whatever client it was called: the human would be moved into that body (research 5.1) |
| a dead actor standing up as police | no routine revives an actor in the rules classes; `ZFFPlayer::Resurrect` is CEG-wrapped and for players |
| AI feds that are off until the hook's key is set | level data acts by itself, and the hook cannot send a message without a game call. The build is the switch; `Bots=2` mutes a fed build |
| the fed keeps the life / a second return / choosing the police body | rule changes or more bodies used up; the research proposes none for a first version. Choosing the body is one more data write (record +0x14 and the used byte) once F1 has shown the path works |
| more than 8 returns per level load | nothing in single player frees a police player object; the hook stands down instead of reaching the `int3` |
| Retomoto | not run on it: its AFTER_DEATH points are in both parts (five in the tower, two in the street) and the feds are parked on the START row's mesh part only, so after the join they would be left in the tower. Needs its own rule |
| anything on a stock level | by policy: a round under changed rules there could go to the real board |

## 7. Not known (each has its check above)

- Whether a police player object is armed (F1), and what its kills pay.
- Whether joining the session uses up one police body (F0).
- Whether a squad script's update still runs once its only man is dead (F0b / F5b), and what Arcade does
  with squads, latches and released men between two rounds on the same loaded level (F6).
- What a `HuntBehaviourRout` does with its box, and with a squad that was not in the world (stock F03 does
  exactly this, in Fragile Alliance only).
- Whether the hero object is whole again in the next round after another body was played (F2).
- The police player's model on an AI actor (M06's feds).
