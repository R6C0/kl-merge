# Review of track D - the HUD's missing values (2026-10-11; adversarial, static, NOTHING RUN IN THE GAME)

Reviewed: `klhook/klhud_values.c`, `re/hud_values.md`, `<work>/build/hud_D/wiring.patch`. Method: every address the
code relies on disassembled again from kl2.exe (capstone through `debug/kl.py`; scratch `G:/kl_scratch/revD/v.py`,
`scan.py`), the C file read line by line, the patch test-applied. Words: **RE-READ** = I disassembled it myself and it
is as the worker says; **NOT RE-READ** = taken from the worker; **GUESS** = said so.

## Verdict: ACCEPT WITH FIXES

The static reading is sound: every offset the readers use is right, the file only reads (no write, no call into the
game, no code byte, no vtable, nothing hidden), and every read is guarded. The fixes are in the WIRING and in three
places where the note says less, or more, than the code shows. Nothing here is a crash risk.

## What I re-derived (all RE-READ unless marked)

| claim | evidence |
|---|---|
| vtables | RTTI: 0xbd3514 ZGameRulesHeist, 0xbd3500 ZHeistScore, 0xbc874c ZOnlineMoneyCtrl (the only vtable whose slot 13 is 0x4d8e80: no subclass is left out by the vtable test in `klv_loot_left`) |
| score = rules+0x36c | 0x7c6d74 `lea eax,[esi+0x36c] / mov [esi+0x5f8],eax`; 0x835509 `lea ecx,[esi+0x36c]` |
| lives `[score+0x6c]` | 0x75bccd `mov byte [ecx+0x6c],3`; 0x5dfffd `dec byte [eax+0x6c]` after slot 106(0) answered 0; 0x4fa0f7 `cmp byte [eax+0x6c],0 / setle`; 0x6f3116 `movsx esi, byte [eax+0x6c]` then a loop pushing "{skull}" (0xb1db7c) into 0x7bb920 |
| skull = U+E018 | 0x926684 compares with "skull" / "skull_kb", 0x9266a2 `mov ebx, 0xe018` |
| Total | 0x807520 whole: slot 56(0) + [+0x2c,+0x24,+0x20,+0x1c,+0x18,+0x10,+0xc,+8,+4] + [+0x38] |
| round so far | 0x711010(0): the same without +0x38; for an index other than 0 it answers `record+0x2c` (0x71107c) |
| carried / rewards / flags / killer | 0x6f86f7 `[score+eax*4+0x150]`, 0x6c0627 `+0x184`, 0x771a3e `+0x1d4`, 0x483914 `movsx [score+edx+0x10c]` only in state 0x19 |
| round end bookkeeping | 0x5e0018 `mov ecx,[eax+0x30] / add [eax+0x38],ecx`, best at +0x34 |
| n, m | 0x74bcf0 `inc byte [eax+0x45]` only when `[records+0x10] == 6`; 0x7c6dec `mov [score+0x44], al` from 0x6a1a90, which is `mov al, 0xa` when 0x7f6850 says Arcade; getter 0x8e109d, setter 0x8632be |
| level loot | 0x4c1dc0: object appended at `[rules+0xdcc]`, count +0xdc0, `add [esi+0xdd0], eax`; caller 0x4d8eec..0x4d8ef9 pushes `this` and `[this+0x34]` for type 2 (type 1 goes to slot 79); reset 0x4fb669 / 0x4fb699; 0x72812b `fild [esi+0xdd0] / fmul qword 0xb21fe0` (= 0.4) |
| vehicle kind | 0x5822d0 `mov al,[ecx+0x1ec]`; 0x8356da 0xff; 0x42cfb0 three tests -> 1 / 2 / 3; 0x81e16e `cmp al,3` -> `[elem+8]+0x7f8` (= 170 x 12) else `+0x804` (171) |
| clock | 0x61d070 `fld [ecx+0x4c]` = rules slot 73, called at 0x62a12c; 0x74b724 `[+0x4c] -= dt`, `[+0x50] += dt` from state 0x19, clamp at 0; length: 0x7c6db9 `fst [score+0x3c]`, 0x6d3130 `fld [0xb2e7fc]` = 360.0; 0xb206d0 = 600.0 |
| slot 42 (the cut) | 0x47d190: min(arg, 0x6d3130()) into `[rules+0x4c]`, `[rules+0x200]`, `[score+0x40]`; +0x3c untouched |
| list order | 0x572050: 0x4000 -> 6, 4 -> 7, 1 -> 1, 0x1000 -> 2, 8 -> 5, 0x80 -> 3 (+1 with 0x40000) |
| aboard / escaped | 0x684157 `push 0x20 / mov byte [eax],4`; 0x811114 `shr eax,6 / and al,1` |
| split / payout | 0x796410: pool +0x604, sharers +0x608, leader +0x60c, `record+0x28`, `record+0x2c` = rewards (+ split) |
| result line | 0x7df067 .. 0x7df330: the three flags exactly as `klv_result` computes them; "you" is index 0 in the game |

NOT RE-READ: the score line NAMES (0x5b5f40), 0x783010's inside, the round-over page's money lines past 0x7df20e,
0x500670, the Quit site 0x418730 (the listing there is misaligned, the byte write is visible), the ctor's +0x44 / +0x45.

## Findings

### MUST

**M1. The wiring does not give the own row the agreed look, and the note is wrong about why.**
`re/hud_layout.md` line 40: *lives = three skulls (picture 178) 12 x 12 ..., ink / 4c0c0c0d when lost*; line 27 lists
178 as a stock HUD picture (Kill, 32 x 32). The task asked for "skull pictures in the own row per re/hud_layout.md".
The patch gives `LIVES n` as text in the round line by default and, with `Lives=2`, U+E018 glyphs appended to the
name - neither is the draft, and the dim lost skulls are "left for later, needs one more text object". The note's
"the skull is a font glyph, not a HUD picture" is true of the STOCK LIST only. With `klu_addpic(178, ...)` three
pictures drawn in the row loop (ink for `i < lives`, 0x4c0c0c0d else) give the draft's look with no UTF-8
assumption, no new text object and no question about glyph tint. The one thing klhud.c lacks is the name's width
(the layout's "x 33 + name width + 8"): use a named constant at the block's right part until a width is had, and
say so. Keep `Lives=2` (glyphs) only as a test key. Until this is in, wiring steps 3 / 5 / 7 are a stop-gap, not the
draft. (GUESS on my side: picture 178 has chunk type 5 like 170 / 181 - klhud's own `handle[]` test covers it.)

**M2. Wiring step 5 and `klv_state` decide a row's state by two different rules.** The patch computes `kind`
inline (dead / waiting -> escaped -> police -> traitor -> you) and never calls `klv_state` (waiting, dead, traitor,
dirty cop, police, undercover, 0x10, status 1, escaped, aboard, bot's mark). They already differ: a police man with
flag 1, a waiting human, status 5. One of the two is dead code that will drift. Either the wiring maps
`klv_state()` to klhud's six kinds (and the "fed before traitor" exception is written INTO klv_state with the
owner's reason), or klv_state goes. As delivered the reviewed function is not the one that runs.

### SHOULD

**S1. The prefix `klv_` / `KLV_` is already klhop.c's** (`klv_init`, `klv_tick`, `klv_r`, `klv_hop` ..., `KLV_NHOP`;
klvis.c has `KLV_GRID`, `KLV_REC_FF`), all in the one translation unit klhook.c makes. No name collides today
(the build proves it), but `KLV_REC_SPLIT` beside `KLV_REC_FF` and `klv_round` beside `klv_r` is an accident waiting.
Rename before wiring (e.g. `kluv_` / `KLUV_`); the other HUD tracks do not reference these names yet.

**S2. The vehicle classes ARE in the repo's notes; the note says "NOT ESTABLISHED".** 0x7d29f0 tests type pair
0x168cddc = ZHavokLnkObj (re/player_down.md 657, kldown.c 1207), 0x7ae760 tests 0x168ce48 = ZHeli (re/maps.md 669;
the export `ZHeli_HeliWeapon_ClassInfo` lies beside it), 0x409920 tests 0x168d624, which lies between the exports
`ZGROUP_ZVehicleBroken_ClassInfo` (0x168d5e0) and `ZEventBase_RelayAnimatedVehicleHit_ClassInfo` (0x168d720) - a HINT
that kind 3 is the animated (key-framed) vehicle = F07's van. So: 1 = Havok car, 2 = helicopter, 3 = animated
vehicle (hint). The stock rule "not 3 -> 171" therefore gives a Havok car (Dead Men's spline ZHavokCar builds) the
picture hud_data.md names BoardingChopper. For OUR dial `kind == 2 ? 171 : 170` is the better rule; keep the stock
rule in the dump line. Also: the function has an `int3` at 0x42d007 before the "else 0" branch - a vehicle of none
of the three classes is an assert in retail, so kind 0 is not a value to plan for; the note leaves the int3 out.

**S3. `klv_dump` recomputes everything every frame for nine seconds in ten.** `said` moves only when a line is
printed, so from 1 s after a print until the next one each call builds the whole line: `klv_money`, `klv_result`,
and `klv_loot_left` = two `ReadProcessMemory` calls per money object (klh_rd is a system call), plus two 420-byte
snprintf. Log=2 only, but that is the setting the live checks run under. Gate the computation with its own
"last looked" tick (1 s), not with `said`. The first `strcmp(line, last)` test is redundant with the key test.

**S4. Slot 22 is described from the wrong side.** 0x8ea4e0 is ZOnlineMoneyCtrl's state-restore (it reads a stream,
puts `[+0x8c]` back into `[+0x34]`) and, in Arcade only (0x8ea601 `call 0x7f6850`), calls rules slot 81 again for
types 0 and 2 (0x8ea622) - that looks like the re-registration after the rules' reset (slot 3 zeroes +0xdd0 and
+0xdc0), not a stray second count. Whether the reset always runs first is NOT established by either of us; the live
check must therefore be made in ROUND 2 as well: `level` of round 2 = `level` of round 1 (twice = double count;
and `in K object(s)` must not double either).

**S5. Live check L4's flag values are a guess presented as expectation.** RE-READ: the kill rule sets flag 4
(0x70479c) BEFORE the waiting branch adds 0x4000 (0x704840), so the waiting human most likely reads `00004004`, not
`00004000`; slot 204 = 0x7622f0 clears 0x34 and sets 8, and the respawn 0x4b28d0 clears 0x4000 (0x4b2a54), so the
fed reads `00000008` (that part holds, and it is what keeps wiring step 5 from showing a LIVING fed as dead - worth
one line in the note, because step 5 newly makes flags 4 / 0x4000 mean "dead look"). State 6 either way.

**S6. Add round 2 to the clock check.** The round reset 0x8c7a80 writes `[rules+0x4c] = 0` and `[rules+0x200] = 600`
(0xb206d0); what puts 360 back for the next round was not read by the worker or by me. The new watch (left against
`[score+0x3c]`) is right whatever does it, and it removes the old code's 600-as-longest-seen fault - but L6 must be
looked at in a second round: `left 360, length 360, ring 1.00` at GO.

### NOTE

N1. `klv_state` treats record status 5 as escaped. Nothing in the note or in klbot.c establishes status 5 (klfed.c's
table merely prints "escaped" for both 5 and 6). A silent guess; mark it or drop it.

N2. "The MEANING of the loot bar is ours (the draft gives it none)" - re/hud_layout.md line 79 gives exactly this
meaning (crew's money against the level's loot) and line 56 the bar. Correct the sentence; the code is right.

N3. `RoundOf` defaults to 0 while the layout's round line (line 50) is 'ROUND n OF m'. Defensible while "does
Arcade end after 10" is open, but then the layout should say so, or the default be 1. Owner's call via the lead.

N4. The stock code puts a SPACE (byte 0x20 at 0xb787a0, appended at 0x7bb9c4) before each `{..}` glyph and one
after unless a space follows. `klv_skulls` packs the glyphs tight. Only matters if `Lives=2` survives M1. That the
virtual at `[gamedata vt+0xb8]` (0x7bba85) appends the code point as UTF-8 is the worker's reading; NOT RE-READ.

N5. `klv_vehicle_kind` answers 0 for "no vehicle", "kind 0xff" and "read failed" alike; the dump line cannot tell
them apart. Print the raw byte and the vehicle pointer in the dump.

N6. `klv_money` returns 0 after it has already filled part of `*m`; the dump then prints those numbers with
"(NOT READ)". Harmless, but zero `*m` again on the failure paths.

N7. `klv_round_frac`, `klv_money3`, `klv_killer`, `klv_result*`, `klv_loot_left` are used by the dump only (or not
at all). Fine as a library for the pop-up / round-over tracks; say so in the note so nobody thinks they are wired.

N8. Per-frame cost of the wired readers without Log=2: about 35 `ReadProcessMemory` calls a compose (each reader
re-checks the score vtable). Acceptable; a `klv_ok` cached once per compose would halve it.

N9. `name[56]` with `klh_rdstr` can cut a multi-byte UTF-8 player name in the middle (it could at 40 too:
not new). SetText's behaviour on a cut sequence is not known.

## Rule checks

- .text patches, writes, calls into the game, wrapped vtables, hidden elements: **none** in the new file.
- Unguarded reads: **none** (every dereference is `klh_rd` / `klh_rd32`; the constant 0xb2e7fc goes through `KLH_VA`).
- Stack / calling convention: not applicable, the file calls nothing in the game.
- Scene change: the readers hold no pointer between calls; a stale money list is covered by the count (reset to 0),
  the 1024 cap and the vtable test per object.
- Stock level / outside Arcade: every reader needs a `klb_snap`, which `klb_read` only fills for session mode 4 with
  a ZGameRulesHeist; the readers themselves only read, the gate stays klhud.c's.
- Build: `ship/dinput8.dll` sha1 93ea224a, `test/dinput8.dll` 8788843c - as reported; `<work>/build/hud_D/klhud_values.c`
  is byte-identical to the repo file. The patch applies cleanly to HEAD (a009beb / bac2f86) AND to the working tree
  (klhud.c carries one uncommitted line). The worktree registration is gone. I did not rebuild and did not rerun
  `klv_test.c`.
- Claims marked READ that are guesses: S2 (the opposite: marked NOT ESTABLISHED though noted in the repo), S5, N1, N2.

## Live checks to add to the worker's L1 - L6

- **L1b** (S4, S6) the same line at GO of ROUND 2 after a failed round: `level` and `K object(s)` equal round 1's,
  `left 360 ... length 360 ... ring 1.00`, `lives 2 of 3`, `round 1`.
- **L3b** (S2) the kind byte per map with the raw value: the bank / Retomoto (F07's van) expect 3; the park's
  helicopter expect 2; any build with Dead Men's spline car expect 1. One 3 on a van map and one 2 on the park
  settle the class table.
- **L2b** (M1) `Plates=1` with the 178 pictures: three skulls in the own block, the lost one dim after a failed
  round; PICTURE must show them inside the chalk block and not over the cash.
- **L4** expect `00004004 state 6` while waiting (S5), then `00000008`, and the FED row drawn as a fed, not struck.
