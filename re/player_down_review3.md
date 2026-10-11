# Adversarial review of track R3 - the belly flop as Dog Days has it (`[Down] Flop=1`, second form)

2026-10-11 ~15:45. Reviewed: the working tree's `klhook/kldown.c` (sha1 e68f347e5cf716c27d33bd623f22053821e257be),
`re/player_down.md` section 10, the `[Down]` block of `klhook/KLHook.ini`, the worker's scratch (`R3/`). OFFLINE:
nothing ran in the game, nothing was committed, no file of the worker's was changed. READ = kl2.exe by
`debug/dasm.py`; FILE = the `.ANM` of stock F01 / F07 and the five tab builds; the reviewer's own scripts are in the
session's scratchpad `R3rev/` (`fk.py` = a full forward kinematics of a clip on the heister skeleton, `census2.py`).

## Verdict: ACCEPT WITH FIXES - the identification stands; the hook form must not run live (G1) before M1 is fixed

The attempt to refute the identification FAILED: the clip is a dive onto the belly and a rise over one knee. The
explanation of what the human plays today is proved from files. But the way `Flop=1` ENDS the knock-down leaves the
game's input mask of the fall on the player (M1, read in the exe): by reading, he stands up and stays masked. The
Dry run G0 writes nothing and may run as it is.

## 1. The identification - tried to refute, not refuted

The worker told belly from back by the PELVIS alone (height + the pelvis's facing). That measure is weak (S3 shows
two clips it gets wrong), so the clips were read again with a full skeleton: every bone's rotation and position keys
composed down the hierarchy of the stock F01 heister skeleton (103 bones; parents from the `.prm`), the worker's key
decoder reused. The decoder is sound: `Get_Up_From_Stomach`'s last frame comes out as a standing man (head 161,
pelvis 95, knees 52, feet 10, hands at the hips), `Die_Backwards` ends chest up with the head 58 behind the root.
Places below are relative to the root, y up, forward = -z; FRONT = the normal of the shoulder girdle.

`Dammage/Wounded#Hero_Torso_Back` (186 frames; events 31 at 1, 0 at 39, 7 at 46, 8 at 116):

| frame | pelvis y | head (y, z) | FRONT y | what |
|---|---|---|---|---|
| 0 | 76 | 129, +39 | +0.50 | arched BACKWARD, the head behind the hips: a man hit in the back |
| 10 | 63 | 111, -38 | -0.66 | going over forward |
| 20 | 22 | 24, -64 | -0.85 | on the floor, face down; the root has gone 48 forward |
| 46 .. 116 | 22 - 23 | 9 - 12, -62 .. -65 | -0.91 | FLAT ON THE BELLY: head forward on the floor, feet 81 / 47 behind, the RIGHT hand out in front beside the head (-34, 3, -63), the LEFT hand out to the side (45, 4, -9), both knees on the floor (y 7 - 10) |
| 135 - 155 | 32 - 42 | 41 - 65 | -0.9 | pushing up on the hands, both knees still down |
| 165 - 175 | 50 - 55 | 80 - 106 | -0.2 | **ON ONE KNEE: the right knee on the floor (y 5 - 10), the left knee up (23 -> 52) with the left foot planted in front (y 10, z -36)** |
| 185 | 82 | 141 | -0.33 | nearly standing |

That is picture 1 (flat on the belly, one hand with the gun out in front, the other arm out to the side) and picture
2 (one knee). `Hero_Torso_Front` is the back: FRONT y +0.95 from frame 30 to 177, 0.8 m backward - confirmed.
`Merc_Run_Torso_Back_03` and `Impact_02#Running_torso_Front_3` are the same lying pose after a 3.2 / 2.3 m lunge -
confirmed. The stock human's fall and loop (`Down_Not_Dead_Get_Down`, `Down_Not_Dead`): thrown 23 back onto the back
(FRONT y +0.93 .. +0.99 at frames 10 - 20), then on his LEFT SIDE with the head propped up (y 48) and the right hand
raised (y 42) - 'the gun one' - confirmed.

Left open, and said so by the worker: WHICH clip of the family the footage shows (the heister's impact
`/Damage/Impact/FB/Running/Front_Torso` is the likeliest), and picture 3. Nothing was rendered; the first frames of
`Hero_Torso_Back` are a man hit in the BACK - on a human who is shot from the front that may look shoved from
behind (the owner's eyes, G1).

**What the human plays today, per body**: FILE, re-run by the reviewer on stock F01, F07 and all five tab builds
(`z_route3/M01`, `z_loot3/M02`, `z_cover3/M03`, `z_route/M06`, `z_rooms/retomoto_full`): in EVERY character set
that has a list (7 - 11 a level; the weapon sets have none) `Down_Not_Dead_Get_Down` = {cond 0x10 `..._No_Weapon`,
cond 0 `Down_Not_Dead_Get_Down` 48 frames}, `Down_Not_Dead_Get_Up` = the 37-frame clip, `On_Spot_..` the same
clips, `Compact_.._Get_Down` is no slot name, `Hero_Torso_F` = Back (1), Back (1), Front (0). So whichever set a
wardrobe body wears, the six words resolve to stock's clips: proved from files, not per body from a log (the logs
D1 / D2 name only the get-up's 36 frames, Char=9; the fall has no name in any log - G0 now prints it). The owner's
'the belly flop shouldnt be when im already dead' was said at 14:31 on the hook `ship_main1`, which has no
`kldown.c` at all: so the flop he knows IS the stock death (0x789b10 names `/Damage/Wounded/Hero_Torso_F`: READ
again) - the worker's reading holds.

READ again and found as written: 0x7c6750 (bits 0 - 2 of a pair's word are weights, bits 3.. the condition class);
0x478270's fall branch (start frame 0 unless the state before was 4; `[M+0x8dc]` = now + frames / 25 x 1024);
0x843fa0 (true once the tick has reached `[M+0x8e0]`; the two constants are 1/1024 and 1024); 0x640c60 writes 5;
0x47cf0f tests M at 5 whatever D is; 0x8eea90 does nothing at 5; 0x77ca60 (event 31's case) asks the action's slot
12 for an item and returns when there is none - not a fault by reading.

## 2. MUST

**M1. The knock-down ends with the fall's input mask still on him.** READ: the down state's start (0x76a450, at
0x76a827 / 0x76a830) sets bits 1 and 0x10 of the input object's `[[obj+8]+0xed0]` (obj = 0x61ef90(`[gamedata+0x1590]`,
`[player+0x91e]`); setter 0x6feb90). The bits are taken off by 0x787600 in exactly three places of the down state:
**0x8ee220** (the fall is over: bit 0x10 at the event tick, both when D goes 2 -> 1), **0x8b1900** (the `[D+0x21]`
request) and **0x88a990** (the reset; callers 0x49c180, 0x6daf30, 0x803c40). **0x7107b0 - the end the new form
relies on - does not touch the mask** (read whole to its `ret` at 0x7108aa: `[D+8]` bit 0, 0x7033d0, `[D+4]` = 0,
0x841db0, 0x7aea80(`[player+0x7e4]`), 0x810550, three floats, 0x74a120); it is reached only from 0x47cd80
(0x47cedc, 0x47cf40) and in stock always AFTER one of the two clearers has run. In `kld_flop_one` the ticks are held so
that 0x843fa0 is never true, then `[M+0x8ec]` = 5 is written while D is 2: the next frame 0x8ee220 does nothing
(0x843fa0 false, M not 2), 0x47cd80 goes to 0x7107b0, D is 0 - and bits 1 and 0x10 stay set. The four tests of the
mask (0x417310 bits 1|4, 0x76fd40 1|2, 0x4d9ec0 0x10|0x20, 0x87d930 0x10|0x40) then say 'no' until the next
reset or a later fall that ends the stock way: he stands and cannot do what the fall forbade (WHICH inputs each
test gates was not read). Section 10.2 point 4 ('0x7107b0: D cleared, the input mask off') and 10.5 ('0x88a990
behind 0x7107b0') are wrong: 0x7107b0 does not call 0x88a990.
Fix, either: (a) data - when the state-5 write is made (and when the bound gives the fall back, nothing is
needed: the game's own 2 -> 1 clears), take the two bits off `[[obj+8]+0xed0]` by the reads of 0x61ef90 (read it
whole first; say what the lookup touches), log the dword before and after; or (b) let the game end the fall
itself: at the clip's end write both ticks = now, wait for D 1 / M 2 (0x8ee220 has then cleared the mask and
0x773d20 has run), then write M = 5 - one or two frames of the lying clip blend in, for the owner's eyes.
G1's PASS must then say: after `UP` he WALKS, AIMS AND FIRES (a scripted shot, and the mask dword logged 0 in
bits 1 / 0x10), not only 'a goto is reached'.

**M2. No bound before the landing.** `kld_s.cap` is set and tested only inside `if (frame >= land)`. While the
channel reads valid with a frame under the landing frame that does not advance - or a stopped channel that reads
frame 0 .. 2 (the 'through' test needs `frame > 2`; what an ended channel reads was never seen for this clip) -
the two ticks are pushed 2 s ahead every frame without end: D 2 / M 1 for good, masked and immune. Section 10.2
point 5 promises 'the state always ends'. Fix: one absolute bound from `t_down` (the clip's length at the game's
speed to the landing + the rest at `FlopBase` + a margin), tested before any write; past it `fdone = 2` and one
line.

## 3. SHOULD

- **S1. `FlopBelly`'s put-back writes through remembered addresses.** `kld_bp[i].at` is an absolute address in the
  level's animation data; `kld_flop_belly(pl, 0)` runs when the part stops acting (menu, another level), i.e. often
  after that data was freed. The only guard is 'the dword still equals the clip number we put' - a small integer,
  which reused heap can hold. Keep the pool pointer and the pair's condition word with each entry and write back
  only when `[player+0x78]` is still that pool (player vtable checked, as the six words' put-back does) and the
  word before the number is unchanged; else drop the entry with a line.
- **S2. HEAD carries the new ini text on the old code.** 370bc51 (track S's commit, 15:18) took the `[Down]` block
  of this track into HEAD while HEAD's `kldown.c` is still R2's: a hook built from HEAD with the sample's
  `Flop=1 FlopBase=0.8` plays `Die_Forward` + the 202-frame rise at 0.8 (10 s). Commit the fixed `kldown.c` next,
  or say in the brief that no hook is built from HEAD with `Flop` set until then.
- **S3. Section 10's pose statements where the pelvis misleads** (full skeleton, `R3rev/fk.py`):
  `Die_Forward` does NOT end 'on his side': the shoulder girdle faces down (FRONT y -0.85 at frame 49, head 12,
  both hands 13 - 15 on the floor) with the hips twisted - it is a fall onto the belly; R2 was wrong because the
  owner wants the game's knock-down with its own rise, not because the pose is a side pose. `DownNotDead_wonded`
  (the worker's 'over onto the belly', `prone.py`'s 'B') stays on the SIDE (FRONT (0.89, -0.05, -0.46)); only the
  head sinks from 48 to 15. Correct 10.0 / 10.1 and say that B / K / s in the table are pelvis readings.
- **S4. Say the three owner decisions before anything is installed, in his words' terms.** (1) No bullet costs
  for the whole knock-down: 1.8 s + 7.0 s without a press at the defaults, against stock's 0.72 s - and the task
  asked for 'the game's own rule while he lies'. (2) He cannot shoot from the floor (the task hoped he could).
  (3) `FlopBelly=1` makes his DEATH the forward flop every time (stock: one in two) - next to 'the belly flop
  shouldnt be when im already dead' that needs his yes; and a knock-down and a death then begin with the same
  frames. Consider `FlopBelly`'s side effect as the reason to write the level step after all (a new one-pair slot,
  10.5), once the look is approved.
- **S5. G0's gate is the stock fall's queue, G1's line prints the real one.** Keep both, and make G1's FAIL list
  say: a non-zero event queue in the `THE KNOCK-DOWN` line = stop the run series there (event 31 would reach
  0x77ca60 with a current action).
- **S6. `Flop=1` changed its meaning** (R2's form is now 2). Nobody's ini has it (the owner's has no `[Down]`
  block: read), the runner's scripts of 9.5 (F1 .. F7) do: they must say `Flop=2` now.

## 4. Checked and found in order

- OFF by default: `Flop` 0, `Enable` 0; `FlopBelly` 1 acts only under `Enable=1 Flop=1`. Nothing on a stock level,
  for a police player, outside Arcade: the part's old gate (`klr_arcade`, `klb_level`, `[player+0x2723]`), and the
  six words + the pair go back when it closes. A dead / out-of-play man: the caller returns before
  `kld_flop_one`; `kld_drop` resets the new fields at every fall, at UP and with the player object.
- A Dry run writes nothing (the three write sites of mode 1 are behind `fnow`, which is 0 with `Dry=1`;
  `kld_flop_belly` logs 'WOULD').
- Events: 0 is outside the switch (`klq_ev_to`), 7 / 8 / 31 are let through for mode 1 only; every other id the
  routine acts on is still refused. No code patch, no call of a game routine, no vtable copy.
- Files: of the task's list only `klhook/kldown.c`, `re/player_down.md`, the `[Down]` block of `klhook/KLHook.ini`
  were changed by this track (the ini's block is in HEAD since 370bc51: S2); no `tools/kl_fa_flop.py`, no level
  build - so no build member to check. The other modified files in `git status` belong to other tracks.
- Compile, re-run by the reviewer: `git archive HEAD klhook` at 370bc51 + this `kldown.c` in a scratch copy:
  'built ...\test\dinput8.dll (TEST)' sha1 bcdbe99e11bcf8d5f129cc06aa12a05501588c02, 'built ...\ship\dinput8.dll
  (SHIP)' sha1 cab0ba511f07526718aaf150629966dfda744d72; the one warning is klhud.c(188) C4101. The worker's two
  DLLs in `G:\kl_scratch\R3` have the hashes of the report (built on dd215a6).

## 5. For the lead

Run G0 (Dry) when the owner is away: it is safe as written and prints the three stock clips by name and the event
queue. Do not run G1 .. G5 on this file: fix M1 and M2 first (one round), then G1 with a scripted shot after `UP`.
