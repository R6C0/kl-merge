# Review I - klbalance.c `FedMirror` (the damage table for a police player)

Reviewer pass, 2026-10-11, offline (kl2.exe build 0490 disassembled with `debug\dasm.py`; the log of run
PT_DM03_die_r2 read; the working-tree diff of `klhook/klbalance.c` read line by line). Nothing was run in the game;
no source file was changed. READ = seen in the disassembly / source, MEASURED = taken from the run's log,
REASONED = follows from those, NOT SHOWN = could not be checked.

## Verdict: ACCEPT WITH FIXES

The reading of the exe is right and `klr_mir = {1, 0, 4, 5, 2, 3}` is the correct exchange for all three pairs. The
code does what its comment says for a dial that sets all six keys (the owner's Risk=2). One contract fault (M1) must
be fixed before the builds go to anybody whose ini does not set all six; the rest are SHOULDs and notes. A scripted
run of `test_fed1` may go ahead as it is (the test ini sets all six through Risk=2).

## What the exe says (point 1) - READ

All three routines take the local player by `0x660b00(gamedata, 0)` and return 1.0 when there is none.

| routine | argument whose team is tested | police byte 0 | police byte not 0 |
|---|---|---|---|
| 0x591b60 (NPC hits NPC; caller 0x61ad14 `push esi / push ebx`, ebx = the SHOOTER, `[ebx+0x77c]+0x704` is his own factor) | shooter | Ally (2): +0x04 (0x591bc6 -> 0x591bd4); else +0x00 (0x591bca -> 0x591bd9) | Ally: +0x00 (0x591bd2 -> 0x591bd9); else +0x04 (0x591bd4) |
| 0x8b8050 (NPC hits the player; callers 0x4db9ce `push edi`, 0x74344d: the shooter) | shooter | Ally: +0x10 (0x8b80ab -> 0x8b80ba); else +0x08 (0x8b80af -> 0x8b80c9) | Ally: +0x08 (0x8b80b8 -> 0x8b80c9); else +0x10 (0x8b80ba) |
| 0x7c1ba0 (the player hits an NPC; caller 0x61ae15 `push esi`: the victim) | victim | Ally: +0x14; else +0x0c | Ally: +0x0c (0x7c1c08 -> 0x7c1c19); else +0x14 (0x7c1c0a) |

So for a police player the unmirrored slots mean: +0x00 heister -> NPC, +0x04 non-heister NPC -> NPC, +0x08
heister -> you, +0x0c you -> heister, +0x10 police AI -> you, +0x14 you -> police AI. Putting key `klr_mir[k]` into
slot k gives every slot the key of its name. **klr_mir is right.**

- The seventh factor: 0x591be0 `test al, al / jne 0x591c28` - skipped for a police player. READ. Untouched by the
  diff. READ.
- Team 2 stays 'the heisters' with a police human: 0x8824e7 (`cmp byte [player+0x2723], 0` ... `cmp dword
  [[soldier+0x40]+0x54]+4, 2 / jne` -> return `[0xb5f1e0]` = -1e38) is the game itself treating 'not team 2' as
  'the police player's own side'. READ. The setter of the police byte, 0x43e270, writes `[player+0x2723]`,
  clears `+0x2727` and `+0xbb0` and nothing else; slot 204 (0x7622f0) adds client flag 8. READ. That NO other code
  rewrites an NPC's team id at the respawn is NOT SHOWN (a negative over the whole exe); the run agrees with
  'unchanged' (see N1).
- Other readers of +0x00 .. +0x14: my own sweep (every dword displacement 0x6ac .. 0xbe8 within 0x90 bytes after a
  load of `[0x168d7c0]`) finds the indexed form `lea r, [r + r + 0x6ac]` only in 0x591b60, 0x6a1c40, 0x79b7c0,
  0x7c1ba0, 0x8b8050 (my window misses 0x46d4d0 / 0x43ffb0's own form; they read +0x20 / +0x6c). The fixed
  displacements 0x71c / 0x720 / 0x724 I looked at (0x800185, 0x7fff84, 0x8827c3, 0x552c21) are fields of other
  objects (soldier, timer), not the table. This agrees with re\balance.md 10.2; I did not repeat its register
  tracing (NOT SHOWN beyond the sweep). 44 functions touch displacement 0x2723; of those in a damage path, 0x61a980
  (0x61ab5b, 0x61af19) only gates (no hit / no damage accounting for a police shooter), it does not pick a float.

## MUST

**M1. An unset key is no longer 'as the game has it': the mirror writes STOCK values into the other slot.**
READ (`klr_want(kk, stock[L].f[kk])` with `klr.f[kk] < 0` returns `stock[L].f[kk]`, written to slot k; the gate
before it is only `klr.any`, which PlayerHealth / RegenDelay / RegenTime alone set). Case: `Risk=0` with only
`PlayerHealth=0.7` (or only `CopToCrew=0.05`). As a criminal nothing of the untouched keys is written. The pass
after the respawn all 66 values are rewritten with the stock pairs exchanged: on level 1 police AI -> heister
3.00 -> 0.01, heister -> police AI 0.01 -> 3.00, you -> heister 2.00 -> 0.25, you -> police AI 0.25 -> 2.00 -
the hook has then changed the game's own fed balance for a user who asked for nothing of it, against the struct
comment '< 0 = leave this factor as the game has it' and section 2 a's contract. The owner's Risk=2 sets all six,
so his game is not hit. Fix (one line): exchange a pair only when at least one of its two keys is set, e.g.
`kk = mir && (klr.f[k] >= 0 || klr.f[klr_mir[k]] >= 0) ? klr_mir[k] : k`; and say in a3 what happens to the unset
partner of a set key (its stock value moves with it).

## SHOULD

**S1. The two PLAYER pairs are relative in the keys' own meaning; mirroring them is a design choice, not a
repair.** REASONED from the table above and stock's numbers (MEASURED, the log's stock rows). Pair 0 is about two
NPCs whose identity does not change (police AI, AI heister): by-name is the only sensible reading and it is what
killed the crew. Pairs 1 / 2 are 'an enemy -> you / you -> an enemy' and 'a friend -> you / you -> a friend'; the
game's own swap keeps that for a fed. The mirror instead makes the criminal's FRIENDLY-FIRE keys (CrewToYou,
YouToCrew) the fed's main combat numbers and the combat keys (CopToYou, YouToCop) his friendly fire. Under the
owner's ini it costs nothing on Arcade levels 1-5 (all 1.0) and little above (level 11: heister -> fed 1.7 instead
of 3.0, fed -> heister 1.0 instead of 0.3); under Risk=1 it gives fed -> heister 1.0 instead of 1.5 and fed ->
police AI 1.5; in the test ini (CopToYou=20) a heister's bullet on the fed costs 1.0, not 20. Either mirror pair 0
only (keys 2..5 documented as 'your enemy / your friend'), or keep it and rename nothing but say it in the ini
text. The lead / owner decides; the log line should name which.

**S2. The fed is tougher than the criminal he was.** MEASURED: 'health object 473ccdc0 (player 475f5020, a
POLICEMAN: left alone): 550.0 of 550.0; ... 4.0 s ... 4.0 s' = the tuning's Arcade player block (the log's 'Arcade
550 4.0 4.0'), a fresh object of the police body. Under the owner's Risk=2 the criminal human has 550 x 0.73 =
401.5 and 8 s / 8 s. 'All the same kinda risk' (owner) does not hold for the fed: 37 % more health, twice the
regeneration. `klr_player_tick`'s `if (police) act = 0` is a choice made before any fed had run; apply the dial
to the fed too (it is the same class and the same health object layout: READ at line 389 ff.) or state it.

**S3. Health base after a fed round - the player object goes A -> B -> A.** REASONED, NOT SHOWN live. At the
respawn `klr_p` moves to the police body ('fresh'); the criminal body keeps OUR maximum (the log shows the hook
writing 27.5 into it again at the death, 08:57:37.574). In the next round the hero is the criminal body again:
'fresh' again, and `klr_track(.., fresh)` takes whatever stands there as the game's. If the hook's pass sees the
body before the game has rewritten its health (the game does rewrite it: 'the game gave 550.0' at GO and at the
death), the scaled value becomes the base and is scaled a second time until the game's next rewrite. First live
check after any fed round: the next round's 'your health object ...' and 'the game gave' numbers must say 550.

**S4. Measure the mirror, do not infer it.** The run had `[Bots] Log=1`: no hit sizes. That the seven died of
police bullets at x 1.0 instead of x 0.05 is the consistent reading, not a measurement (N1). Run `test_fed1` with
`[Bots] Log=2`: a bot's 'lost' steps before the respawn, after it with FedMirror=1 (should stay the same size) and
once with FedMirror=0 (about twenty times larger).

**S5. The 'Risk=.. written' line repeats at each flip** (READ: `act && n` holds whenever the flip changed a
value) and prints the by-name row, directly followed by the mirror line. Not wrong, but two lines for one event and
the first reads like a new arming; print it only when `mir == mirwas`.

## NOTE

- N1. The run's evidence for 'teams unchanged', MEASURED: no bot died in the 24 s before the respawn or in whole
  earlier bank rounds at CopToCrew 0.05 (C3_DM03); all seven died 15 .. 47 s after it while the fed stood stuck at
  (-4155, 300, -3645) and fired nothing. Had the police AI become team 2, its bullets would have stayed at +0x00 =
  0.05. Caveat: the bots took heist stage 1 (went in among the guards) in the same two seconds as the respawn
  (08:57:42.9 .. 44.2), so the timing alone proves less than it seems.
- N2. The moment (point 2). The police byte is set on body 8 (0x7622f0 -> 0x43e270) BEFORE that body becomes the
  local player (0x4d2ef0); the three routines and `klr_local_police()` read the same object,
  `[gd + 0x828 + 4 * (signed byte)[gd + 0x898]]` (0x660b00 READ; hook lines 273 / 389 READ), so the hook cannot see
  'police' earlier than the game does. The table is exchanged at most one hook pass (50 ms game thread, 100 ms
  fallback) after the switch: a few frames in the game's own order, i.e. what the whole of run PT_DM03_die_r2 had.
  In the run the hook's pass saw the policeman in the same pass as the status change (08:57:42.571). During the
  5 s wait the local player is still the dead criminal body (index 0, police byte 0): ordinary order, correct.
- N3. Half-written table. Each float is its own write; a hit between two writes of a pair reads one old and one
  new value - for the owner's pair 0 that is 1.0 / 1.0 for an instant, the value it had the frame before. On the
  game thread's pass no hit runs at all between the writes; only the fallback thread can interleave. Not worse
  than the six were (they are also written while a round is loaded), but it now happens once in mid-fight. REASONED.
- N4. `mir` is 0 whenever `act` is 0; the put-back path writes `stock[L].f[k]` in the ordinary order; `mirwas` is
  cleared with `tun0` and with `!act` (no line - fine, the 'stock table is back' line stands). Values moved from
  another slot are bit copies, so `want != cur` settles after one pass. A new round (hero = body 0, police byte 0)
  puts the order back the pass after; a second, final death leaves the police body local (order stays exchanged to
  the round's end) or no local player (ordinary order; the game then returns 1.0 for everything, 0x591b7f). READ /
  REASONED. Ramp: `klr_want(kk, stock[L].f[kk])` is exactly the criminal row's value of key kk on every level,
  `klr_kind[kk]` included. READ.
- N5. With the mirror the police AI is as weak against the crew as before the death (0.05) and does not shoot the
  fed; the fed has to kill up to seven heisters alone, each hitting him at 1.0. klfed's 'nobody is left to hunt'
  end will then rarely come by itself - the round runs to the clock or the crew escapes. Stock's own fed design is
  the opposite (police AI -> heister 3.00 on level 1). A middle value for 'police AI -> heister while you are a
  fed' may be wanted; that is a new key, not a fault of this diff.
- N6. The run's log (point 5), MEASURED: order sound - status 0 -> 1 at 08:57:37.575, FED 5.0 s later, body 8 of
  type 3, 7 of 8 bodies left; escort released at the death ('you are out of play') and not re-taken for the fed;
  'nobody is left to hunt' is logged 46 ms BEFORE 'record 5 (bot): dead' (the two parts read the record on
  different passes: harmless). Unlogged: nothing in the `fed:` lines says what the balance did (the new mirror line
  fills that); the fed's weapons; whether the fed was ever hit. `bots:` goes on calling record 0 'you in-play'
  through the score page though the life is taken.
- N7. Whether `test_fed1` / `ship_fed1` were built from exactly this working tree was not checked.

## Point 4: what a bullet costs (owner's ini: Risk=2, Ramp=1, CopToCrew=0.05, Arcade level 1)

Criminal row on level 1 (READ from klr_want + the stock row in the log): CopToCrew 0.05, CrewToCop 1.00, CopToYou
1.00, YouToCop 1.00, CrewToYou 1.00, YouToCrew 1.00. Factors only; body part, weapon and health come on top.

| hit, the human being a fed | slot read | FedMirror=1 | FedMirror=0 | stock game |
|---|---|---|---|---|
| police AI -> AI heister | +0x04 | **0.05** | **1.00** | 3.00 |
| AI heister -> police AI (no off-stage factor: 0x591be0) | +0x00 | 1.00 | 0.05 | 0.01 |
| AI heister -> the fed | +0x08 | 1.00 | 1.00 | 0.10 |
| the fed -> AI heister | +0x0c | 1.00 | 1.00 | 2.00 |
| police AI -> the fed (stray only: he is never its target, 0x8824e7 -> -1e38) | +0x10 | 1.00 | 1.00 | 0.10 |
| the fed -> police AI | +0x14 | 1.00 | 1.00 | 0.25 |

On levels 6-11 the player rows differ too (Ramp): heister -> fed 1.1 .. 1.7 mirrored against 1.3 .. 3.0, fed ->
heister 1.0 against 0.9 .. 0.3. The fed's health: 550, back after 4 s within 4 s (the game's Arcade block), not the
dial's 401.5 / 8 / 8 (S2).

## Not checked

- Any of it in the game: the mirror, the flip back in a second round, S3's order of events.
- That nothing but 0x43e270 / 0x7622f0 changes at the respawn that the damage path reads (NPC team ids, the 44
  other users of +0x2723 beyond the ones named).
- re\balance.md 10.2's register tracing (only my coarser sweep was run).
- Which builds the working tree produced (N7); the AI heisters' and police AI's health numbers.
