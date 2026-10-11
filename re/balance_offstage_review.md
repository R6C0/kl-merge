# Review: the seventh damage factor (R+0x1c), key `CrewOffStage` (track E)

Adversarial review, 2026-10-11. OFFLINE: the game was not started, nothing was written in the game folder (its
`kl2.exe`, `KLHook.ini` and `KLHook.log` were READ), nothing committed, no source file changed. Reviewed: the working
tree's `klhook/klbalance.c`, the `[Balance]` block of `klhook/KLHook.ini`, `re/balance.md` (section 10 and the edits
above it), the builds `ship_bal2` / `test_bal2`. My scripts are scratch (session scratchpad `rev_off\`); what they
did is said below so it can be done again.

**Verdict: ACCEPT WITH FIXES.** The reading of the exe is right, the code does what the note says and writes
nothing new while the dial is off. The fixes are in the TEXT (one refuted claim about how the bots die) and in the
live check (the run that is to show the effect is too weak as proposed). No code change is required before a live run.

## 1. The exe, re-derived

Own disassembly (`debug/dasm.py`) and own sweeps (capstone through `debug/kl.py`), not the worker's scripts.

- **0x591b60 has one caller and no pointer to it**: a byte scan of `.text` for `call` / `jmp rel32` to it gives
  0x61ad18 only; the dword 0x00591b60 occurs nowhere in the image.
- **The caller is ZFFActor's hit routine**: 0x61a980 stands once in the image, at 0xbb4248 = slot 423 of vtable
  0xbb3bac (RTTI: ZFFActor). `this` (esi) is the NPC that is hit. `[hit+0xc]` is kept in edi / `[esp+0x14]` when its
  class is ZFFActor (0x61aa99..0x61aab6). At 0x61ad14 `push esi` (victim), 0x61ad15 `push ebx` (ebx = `[esp+0x14]`,
  the attacker), so the routine's first argument is the ATTACKER. Only reached with an attacker that has a soldier
  (`[attacker+0x77c]`), in Arcade (0x7f6850), with a rules object.
- **0x591b60, whole**: level byte `[[rules+0x5f8]+0x45]` clamped 1..11; R = `[0x168d7c0] + 0x6ac + L * 0x70`
  (0x591bac); no local player -> 1.0; `[player+0x2723] == 0`: attacker team 2 -> `[R+4]`, else `[R+0]`; a police
  player: the two swap (0x591bcc..0x591bd9). Then 0x591be0 `test al, al / jne` (police player: out), 0x591be4 team
  not 2: out, 0x78f470(rules, attacker) -> index, stage byte `[[rules+0x348] + i*0x7c + 0x78]`, 0x6c7700(player)
  (returns 0 in Arcade), compare, and only if the two bytes differ 0x591c1d `fld [ebp+0x1c] / fmul`. The second
  argument is never read. As the worker says.
- **No other reader of R+0x1c.** (a) Every 32-bit constant 0x6ac in `.text`: with an index register only at
  0x591bac, 0x6a1c64, 0x79b8ad, 0x7c1be3, 0x8b8093; the constant 0x6c8 (= 0x6ac + 0x1c) occurs with an index
  nowhere. (b) All 401 references to 0x168d7c0 (398 loads, the compare at 0x524063, the stores 0x530c33 and
  0x5d1e18) in 215 functions; each loaded register followed forward to the end of its function without stopping at
  jumps or returns (so it over-reports): accesses off a formed record are +0x00 / +0x04 / **+0x1c** (0x591b60),
  +0x18 (0x6a1c40), +0x24..+0x68 (0x79b7c0), +0x0c / +0x14 (0x7c1ba0), +0x08 / +0x10 (0x8b8050), plus the direct
  indexed +0x20 (0x46d4eb / 0x46d505) and +0x6c (0x43ffdd). No fixed offset inside tuning+0x71c..+0xbeb anywhere.
  Every 'escape' the over-reporting trace flagged was read by hand and is none: nine `push ecx` are stack slots
  for a float, the calls with a stale ecx are C runtime helpers or another object (0x8475c3: ecx = `[0xdd2640]`).
  (c) The game does store into the tuning object after its constructor, but only at +0x628..+0x634 (0x88d780) and
  +0x154 (0x8e4680): not in the records.
- **The stock row**: the constructor's eleven blocks `fld [const] / lea ecx, [edi + 0x738 + 0x70*(L-1)] / fstp [ecx]`
  (0x52b853, 0x52bf90, 0x52c6c9, 0x52ce06, 0x52d53d, 0x52dc82, 0x52e3de, 0x52eb89, 0x52f318, 0x52fa78, 0x530207)
  give 0.5 0.5 0.5 0.4 0.3 0.3 0.2 0.2 0.2 0.1 0.1 = `klr_code_off`, all eleven.
- Limit, as the worker's: a linear sweep. Not re-read: what raises / clears the stage byte, `[actor+0x774]`.

## 2. The code, line by line

Own off-game harness (the worker's stubs, my scenarios; committed file from `git show HEAD:` against the working
file, both built x86, the working one at /W4 without a warning):

| asked | result |
|---|---|
| stock kept and put back: session not Arcade, level stock, verdict changing back and forth, Arcade level change | yes: 45 values written, the same 45 back, the 88 floats bit for bit stock each time |
| a direct boot (the first pass already acts) | first sight is before the first write; put back right |
| a new tuning object while the dial is in | stock taken again from the new object, written, put back; a new object whose +0x1c row is not the known one: the seventh refused with its line, the six as before |
| the pointer 0, then the object back at the same address with the constructor's values | written again, put back right |
| +0x1c of one level changed from outside while acting | written again (one value), put back right |
| the player a policeman | the table part is the same; health left alone |
| Enable=0; Enable=1 Risk=0 without the key; single keys; Risk 1 / 2 / 3 with `CrewOffStage=-1`; the key as text or out of range (old against new) | **72 pairs of runs over eight scenarios: identical write traces, 0 writes at +0x1c** (the worker's own 37 checks also pass when run again) |
| the known-table check | all eleven levels, 0.001, not-a-number refused; refusal said at any Log level |
| the log lines | true in every case run; the counts the live check expects (35 with the owner's ini, 45 without CopToCrew, 29 with `-1`) are what the harness prints |
| the builds | rebuilt from the tree: no warning at /W3, same sizes, **8 bytes differ** from `ship_bal2` / `test_bal2` (time stamps): the delivered DLLs are this source. sha1 as reported |

Nothing is written that was not written before while the dial is off. With the owner's ini unchanged the hook does
change his game (the worker says so): that is the task's own choice for Risk=2.

## 3. Defects

### must

**M1. 're/balance.md' 10.6 / 10.9 and the report: 'what kills them are the ONE STEP losses, which no damage factor
touches' - refuted by the owner's own log.** `KLHook.log` has 41 'bots: record N (bot): lost ... - DOWN' lines
(seven scripted processes with `[Bots] Log=2`, police->crew 0.03 .. 0.15): **39 by accumulated ordinary losses**
(at police->crew 0.05: median loss 5, nine in ten at 12 or less; e.g. six bots down within 30 s at
05:48:09..05:48:39), **2 by one step**. 21 of the
23 that were in the log when the note was written already were. Of the 27 lines that carry the stage (the older
hook did not log it) 26 are at `g1` - in scripted runs, where the human stays at `g0` - that is under this very
factor. So: (a) 'do NOT judge by bots dead' is unfounded - bots DOWN and the time to the first
DOWN is the outcome to compare; (b) in the scripted runs how fast the crew kills is what decides whether it lives,
so the factor matters MORE there than the note concludes. Text only; no code. (For the owner's PLAYED rounds the
log has no 'lost' lines - Log=1 - so nothing is known either way.)

### should

**S1. The run that is to show the effect (O3) cannot be relied on as proposed.** It compares 1.0 with 0.5 by the
bots' own losses over 'two or more runs' with a different crew and route each time. O0 / O1 / O2 are sound and will
show the VALUE in the table and its return; none shows a policeman losing 46.8 instead of 23.4. Sharper, with the
same tools, Arcade level 1, the scripted standing player, `[Bots] Log=2`, one variable a run:
`Risk=2 Ramp=0 CrewOffStage=20` (one body hit kills any policeman: 46.8 x 20) against `Risk=2 CrewOffStage=0`
(a heister at another stage cannot hurt anybody; written as given, below the Ramp limit). On level 1 Ramp=0 changes
none of the six. If the crew goes down the same way and as fast in both, the factor is not in force where the
reading says; if 20 sweeps the room, the whole chain (value -> game) is shown in two runs. Then 1.0 against -1
with DOWN count / time to first DOWN, three runs a side.

**S2. The exposure figure (11 %) is older than BoardAll.** The seven played processes are 2026-10-10 16:59..20:23;
`[Bots] BoardAll` (later) sets a held bot's stage byte to 3 before the human is there, which is 'another stage' by
this compare. Recounted on today's log: 11 % (17,655 / 1,935 bot-seconds; 12 % with the time the human is aboard or
dead counted too), scripted 75 % - the worker's numbers hold, but '+6 % for the owner' is a floor once BoardAll is on.

### note

- N1. `CrewOffStage=0,75` (a decimal comma) or `1.0abc` is taken as the leading number: `0,75` -> **0.0**, written on
  all eleven levels (seen in the harness). The comment says a text that is no number is ignored. Gameplay only, shown
  in the 'on' line, put back at the session end; the six do the same through `atof`. One line: accept only when the
  rest of the text is blank.
- N2. A number over 20 falls back to the dial's value without a line (`Risk=2 CrewOffStage=99` writes 1.0). `-0` is
  accepted, written as -0.0 and printed 'x -0.00'.
- N3. With an explicit key over 1 and a low CrewToCop the product rule makes a heister at another stage STRONGER than
  one at the human's (`CrewToCop=0.1 CrewOffStage=20`: x 15 on level 1). Only on request; the defaults never pass 1.0.
- N4. The suffix '(Ramp: crew->police x this is at most stock's own product on the level)' is also printed when Ramp
  limited nothing (`CrewOffStage=0.25` alone).
- N5. While the shape test of the table fails nothing is put back, the seventh included (old behaviour of the six;
  it resumes when the test passes again - seen in the harness).
- N6. The fed swap is real (0x591bcc..0x591bd9, re-read): for a police player an AI heister shoots with R+0x00 -
  0.05 in the owner's ini - and the police with R+0x04. Not this track's, but it wants a decision before
  `[Fed] Player=1` is played with CopToCrew under 1.
- N7. Stale beside section 10: `re/balance.md` check B1 still expects '39 value(s) changed' and '+0x1c stay';
  `tools/kl_map_ai.py balance` knows six factors; `klhook.c`'s head comment lists neither the file nor the section.
- N8. `re/balance.md` 10.8 names 4d9a91d, the report 703d007 / 2a8b461: the hook sources are the same in all three.

## 4. The before / after table

Recomputed by hand and by running the worker's script on `z_final\M02` (11 police at 90 / 112.5 / 157.5, median
157.5; Zastava 46.8; magazine 30; accuracy 55): every cell of both tables is right, as are the products 1.5 1.3 1.1
0.76 0.48 0.39 0.2 0.16 0.08 0.02 0.01, Risk=1's 0.75 0.75 0.73 0.51 0.32, the 0.63 and the +6 % / +60 %. What is
assumed is said (30 rounds = a magazine, accuracy as the hit share, fire spread evenly over time).
