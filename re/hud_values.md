# The values the HUD draft still lacked (2026-10-11, track D + its review round; static reading, NOT RUN IN THE GAME)

Code: `klhook/klhud_values.c` (new; reads only, no write, no call into the game). Wiring into `klhud.c` / `klhook.c`:
section 3. Review: `re/hud_values_review.md`; what was done about it: section 5. Words: **READ** = read in kl2.exe
build 0490 (capstone through `debug/kl.py`), **LOG** = a line of a live log, **GUESS / NOT ESTABLISHED** = said so.

Names: everything in the file is `kluv_` / `KLUV_` ('klu values'). `klv_` / `KLV_` are klhop.c's and klvis.c's.

Objects: `rules` = `[[0x168e9e4]+0x54]`, **ZGameRulesHeist** (vtable 0xbd3514) - this IS the Arcade class (the
multiplayer ones are ZGameRulesFragileAllianceSv 0xbd2eb4 / Cl 0xbd31e4). `score` = `[rules+0x5f8]` = `rules+0x36c`, a
**ZHeistScore** (vtable 0xbd3500) built inside the rules object (ctor 0x835509, slot 36 0x7c6d74). Every reader first
checks that vtable.

## 1. The table

| value | where | how established | confidence |
|---|---|---|---|
| **(a) lives** | signed byte `[score+0x6c]` | READ: ctor 0x75bccd = 3; `dec` at 0x5dfffd when client 0 did not escape; 0 on Quit (0x418730); game over when <= 0 (0x4fa0f7). **The stock list reads this byte**: 0x6f3116 `movsx esi, byte [eax+0x6c]`, then appends `{skull}` that many times to the name; the round-over page 0x7dfa5c and the intro 0x6d82ac the same | high |
| `[score+0x44]` is NOT lives | it is the number of rounds (c) | READ (0x7c6dec); LOG: run P1_DM03_pic 20:55:25 `hud: text 18: '' -> 'ROUND 1'` - klhud.c prints 'LIVES n' only for 0..9 and it did not (the byte is 10) | high |
| the STOCK list's skull | a **font glyph**, U+E018, UTF-8 `EE 80 98`, a space before each (0xb787a0, 0x7bb9c4) | READ: 0x7bb920 turns `{name}` into a private-use character through the table 0x926350 (`skull` / `skull_kb` -> 0xe018 at 0x9266a2; `moneysymbol` 0xe019; `heist1up` 0xe017; pad buttons from 0xe000); the string reader 0x4e8460 is a UTF-8 decoder | high for the code point; ASSUMED that SetText decodes UTF-8 the same way. Only our TEST key `Lives=2` uses it |
| **OUR skulls** (the agreed draft, re/hud_layout.md: 'three skulls (178) 12 x 12 from x 33 + name width + 8, ink / 4c0c0c0d when lost') | three **pictures**, HUD picture 178 ('Kill', 32 x 32), queued with `klu_addpic` in the own row; held = ink ff0c0c0d, lost = 4c0c0c0d (chalk fff3f0ea / 4cf3f0ea without the painted block) | re/hud_layout.md, re/hud_data.md for the slot | **GUESS**: picture 178's chunk is type 5 like 170 / 181 (klhud.c's `handle[]` test decides at run time; no handle -> 'LIVES n' in the round line); that it takes the tint; the name's WIDTH is estimated (klhud.c has no text width): `KLUV_NAME_CHARW` 9 px a character, `KLUV_CASH_ROOM` 64 px kept free at the right - named constants, live check L2b |
| lost-life look in the stock HUD | none: the stock list simply shows fewer skulls; 3 is the most (the ctor) | READ (the loop 0x6f3120) | high |
| **(b) Total** (the stock 'Total score') | `carried(client 0) + [score+4,+8,+c,+10,+18,+1c,+20,+24,+2c] + [score+0x38]` | READ 0x807520, whole. klhud.c's sum is the same | high |
| the round so far | the same without `[score+0x38]` | READ rules slot 54 = 0x711010(0) | high |
| **Loot** = carried | `[score+0x150 + 4 i]` | READ slot 56 = 0x6f86c0; the stock list's second column | high |
| **Rewards** | `[score+0x184 + 4 i]` (kill pay and fines: can be negative) | READ slot 55 = 0x6c05f0; written by the kill rule (0x670968); third column | high |
| split / payout, live | crew record `+0x28` = his share if the round ended now (pool / sharers once he has flag 0x40; a police man: what he carries), `+0x2c` = rewards + split; pool `[rules+0x604]`, sharers `+0x608`, leader `+0x60c` | READ 0x796410, run every frame in state 0x19 / 0x29 (0x74b77e) | high |
| **Round score** | `[score+0x30]` = sum of the nine lines; **0 during the round**, written at its end by 0x783010 (escape bonus `[tuning+0xbec]` -> +4, time bonus -> +0x1c, your payout -> +0xc only if you escaped), then `[score+0x38] += [score+0x30]` (0x5e001b), best round `[score+0x34]` | READ (the inside of 0x783010 by the first worker only) | high |
| the score lines' names | +4 Escape, +8 NPCEscape, +0xc Loot, +0x10 Kills, +0x14 the kill count, +0x18 Revenge, +0x1c Time, +0x20 Yellow, +0x24 Traitor, +0x2c Civilians, +0x30 Round, +0x38 Total (`HeistPoints<name>`) | READ: the menu variables of 0x5b5f40 (0x5ba2b0 .. 0x5ba8e3) | high; +0x28 has no variable of its own |
| the round-over page's money lines | 'Your split' = record+0x28 (traitor: 'Your grab' = carried; police: 'Finder's fee' = record+0x28), 'Your reward' = rewards, 'Round score' = +0x30, 'Total score' = +0x38, then the skulls | READ 0x7dede0 (0x7df1fb .. 0x7dfa5c) | high |
| **(c) n** | signed byte `[score+0x45]`; ++ only when record 0's status is 6 (0x74bcf0): a failed round keeps its number. It is also the Arcade LEVEL of the difficulty tables | READ | high |
| **m** | byte `[score+0x44]` = 0x6a1a90() = **10 in Arcade** (constant, 0x6a1aa2), the lobby's 'number of rounds' otherwise; getter slot 40 = 0x8e1090 | READ | high for the value. **NOT ESTABLISHED** that an Arcade session ends after round 10: no compare of n with m in the Heist class, none in a sweep of every byte access to +0x44 / +0x45 in .text; and AGAINST it the difficulty tables take n clamped to 1 .. **11** (0x591b89 .. 0x591b97; re/balance.md has eleven rows). The page's own counter is `Round %d` with n only (0x5ba92e). So `RoundOf` stays 0 by default - the layout's 'ROUND n OF m' is one key away (the owner's call) |
| **(d) the level's loot** | int `[rules+0xdd0]` | READ: slot 81 = 0x4c1dc0(amount, object) `add [esi+0xdd0], eax`, called by ZOnlineMoneyCtrl (vtable 0xbc874c) slot 13 = 0x4d8e80 for money of type `[obj+0x38]` 0 and 2 with `[obj+0x34]`; reset by slot 3 = 0x4fb620; the game tests `carried >= [rules+0xdd0] * 0.4` itself (0x72812b) | medium: a civilian's money counts like a safe; and the next row |
| the second registration | slot 22 = 0x8ea4e0 is the money object's STATE RESTORE: reads a stream, `[obj+0x34] = [obj+0x8c]` (0x8ea50e), and in Arcade only (0x8ea601) calls rules slot 81 again for types 0 and 2 (0x8ea622). 0x4c1dc0 has **no test for an object already listed** | READ (0x4c1dc0 whole) | most likely the re-registration after the rules' reset; whether it can run WITHOUT the reset is NOT ESTABLISHED. `kluv_loot_scan` counts list entries that name an object twice and `kluv_loot_total` takes their `[obj+0x8c]` off (ASSUMED the amount added twice); the dump prints raw sum, duplicates, corrected number. Live check L1b |
| what is left | sum of `[obj+0x34] > 0` over the list `[rules+0xdcc]`, count `[rules+0xdc0]`, each object once | READ 0x8b94d0 (the loot tactic walks it), 0x4536e0 (`[obj+0x34] <= 0` = depleted) | medium (dropped money, type 1, is in the other list at rules+0xda8 and not counted) |
| **(e) vehicle kind** | byte `[rules+0x1ec]` (slot 95 = 0x5822d0): 0xff none yet, then 1 / 2 / 3 by three class tests of `[rules+0x1e4]` (0x42cfb0). None of the three -> `int3` at 0x42d007 (an assert in retail): 0 is not a value of a running round | READ | high |
| the three classes | **1 = ZHavokCar** (0x7d29f0 tests pair 0x168cddc; static initialiser 0xafcd10: name "ZHavokCar", parent "ZHavokLnkObj"), **2 = ZHeli** (0x7ae760, pair 0x168ce48; 0xafcde0), **3 = ZAnimatedVehicle** (0x409920, pair 0x168d624; 0xafda50, parent ZSTDOBJ) = the key-framed vehicle, F07's van | READ (the registrations that hand each type pair to its class name) | high. Older notes (re/player_down.md 657, kldown.c 1207) call pair 0x168cddc 'ZHavokLnkObj': by the initialiser it is ZHavokCar's own pair (ZHavokLnkObj is the parent's name in the same call) |
| its picture | STOCK clock: **3 -> 170, anything else -> 171** (0x81e16e `cmp al, 3`) - a Havok car (Dead Men's spline ZHavokCar builds) gets the helicopter. **OUR dial: 2 -> 171, else 170** (`kluv_vehicle_pic`); the stock rule is kept for the log (`kluv_vehicle_pic_stock`) | READ; ours is a choice | high |
| **(f) round length** | float `[score+0x3c]` = 0x6d3130() = **360.0 in Arcade** (constant 0xb2e7fc) | READ slot 36 = 0x7c6d70, slot 41 = 0x7f09a0 | high; ASSUMED nothing shortens it in a round (slot 42 = 0x47d190, the 'cut', writes `[rules+0x4c]`, `[rules+0x200]`, `[score+0x40]` and leaves it) |
| time left (what the clock prints) | float `[rules+0x4c]` | READ: slot 73 = 0x61d070 `fld [ecx+0x4c]`, called by the clock's tick 0x62a12c; counted down in 0x74b724 from state 0x19 | high |
| time played | float `[rules+0x50]`, counted up in the same place | READ | high |
| `[rules+0x200]` | the Heist class's own END timer (0x5dff40), 600.0 at the round start (0x8c7a8b): **not** the clock (klhud.c's watch read it) | READ | high |
| the next round's clock | the round reset 0x8c7a80 writes `[rules+0x4c] = 0`, `[rules+0x200] = 600`; what puts 360 back was **NOT read** (slot 36 is the only writer of 360 found) | READ for the reset | the ring is left / length whatever does it; live check L1b |
| **(g) flags of crew index i** | `[score+0x1d4 + 4 i]`, indexed like the money | READ slot 114 = 0x771a10 (klhud.c's assumption d is settled) | high |
| the stock list's row state | in this order: 0x4000 -> 6 waiting to return as police, 4 -> 7 dead, 1 -> 1 traitor, 0x1000 -> 2 dirty cop, 8 -> 5 police, 0x80 -> 3 (4 with 0x40000) undercover, 0x10 -> 6 | READ 0x572050, whole (`kluv_stock_state`, log only) | high |
| aboard / escaped | flag 0x20 (set with status 4 by the boarding rule 0x684157 / 0x684236) / flag 0x40 (slot 106 = 0x8110e0); the stock list has no look for either | READ | high |
| the flags at a death | the kill rule sets 4 (0x70479c `or eax, 4`), THEN the waiting branch adds 0x4000 + status 1 (0x704840): a human waiting to return most likely reads **00004004**; slot 204 = 0x7622f0 clears 0x34 and sets 8, the respawn 0x4b28d0 clears 0x4000 (0x4b2a54): the living fed reads **00000008** | READ (0x70479c, 0x704840, 0x4b2a54 and the `and eax, 0xffffffcb` of 0x7622f0 here; the `or 8` by the reviewer) | high for the bits, the order at run time is for L4 |
| klbot.c's reading | agrees: status 0 in play, 1 waiting, 4 aboard, 6 escaped, 7 dead; record+0x79 mask 2 = the BOT's own traitor mark, which the stock list does NOT show (it tests flag 1 only). **Status 5 is NOT established** (klfed.c's table prints 'escaped' for it): no reader gives it a meaning | READ | high |
| **OUR row state** (`kluv_state` -> `kluv_kind`, THE decision klhud.c runs) | waiting / dead -> dead look; escaped ('OUT', also a traitor who got out - as klhud.c Version 2 had it); **fed BEFORE traitor** (the owner, 2026-10-11: 'as a fed youre only a fed'; the stock list has traitor first); traitor (score flag 1 or the bot's mark); flag 0x10 -> waiting (the stock list's last test; what sets 0x10 was not read); aboard (no look yet); you / crew | a choice, written at `kluv_state` | - |
| **(h) killed by** | signed byte `[score+0x10c + i]` = the killer's crew index, -1 = nobody of the crew | READ slot 25 = 0x4838d0 (answers only in state 0x19); the panel text is built by 0x500670 from `AllLevels/Menu/Online/Respawn` `KilledBy` + `AllLevels/Interface/Online/Kill` `FA_DieFrom<role>` / `FA_DieFromSelf` | medium (the role string of an NPC killer was not read) |
| the result line | keys under `AllLevels/Interface/Online/GameEnd/`: all in use have flag 0x40 -> `All_Esc`; you have it -> `You_Esc`; all have 4 or 8 -> `All_Dead`; nobody left who is neither escaped nor police -> `Last_Esc`; you have 4 or 8 -> `You_Dead`; else `Time_Up`; `LifeLost` added when your flag 0x40 is clear; title `Game_Over` when lives <= 0 else `Round_Over` | READ 0x7df067 .. 0x7df428 | high for the logic; the English wording in kluv_result_text is OURS |

## 2. The readers (`klhook/klhud_values.c`; each takes klbot.c's `struct klb_snap`, each answers 0 / 'nothing' on a failed read)

**Wired into klhud.c by section 3:** `kluv_lives` (0..9), `kluv_skull_x(name, crew_w, k)` / `kluv_skull_y(row pitch)` /
`kluv_skull_argb(k, lives, block)` (the own row's three pictures), `kluv_skulls(out, cap, n)` (the glyph string,
`Lives=2` only), `kluv_kind(s, i)` (klu_row's kind 0..5, through `kluv_state`), `kluv_round(s, &n, &m)`,
`kluv_loot_total` (the rules' sum less double entries) and `kluv_loot_share` (what the crew carries / the level's loot,
0..1 = re/hud_layout.md's loot bar), `kluv_vehicle_pic` (170 / 171 / 0), `kluv_round_left`, `kluv_round_len`,
`kluv_round_played`, `kluv_dump(s, me)`.

**A library for the pop-up / round-over tracks, used by the dump only so far (NOT wired):** `kluv_money(s, i, struct
kluv_money *)` (total, round_now, carried, rewards, split, payout, banked, round_score, best, pool, sharers, leader),
`kluv_money3`, `kluv_round_frac`, `kluv_flags`, `kluv_state`, `kluv_stock_state(flags)`, `kluv_killer` (-1 none),
`kluv_result(s, me, &life_lost, &game_over)` + `kluv_result_key` / `kluv_result_text`, `kluv_loot_raw`,
`kluv_loot_scan(s, struct kluv_loot *)` (left, count, dups, dupsum), `kluv_loot_left`, `kluv_vehicle_kind` (1 car, 2
helicopter, 3 animated; 0 = none yet / not read), `kluv_vehicle_raw` (the byte and the pointer, for the log),
`kluv_vehicle_pic_stock`.

Cost: the money list is walked at most once a second (`kluv_loot_cached`; two reads an object), never per frame.
`kluv_dump` LOOKS once a second at most (nothing is computed between two looks) and says its line when a value other
than the clock changed, and every 10 s anyway. The wired readers without Log=2 cost about 35 `ReadProcessMemory` calls a
compose (each re-checks the score vtable) - left as it is.

Off-game check: `<work>/build/hud_D/kluv_test.c` (the file included as it is; a made-up rules / score / records / money
objects): **83 checks PASS**, `/W4` clean. That proves the file's arithmetic and guards, nothing about the game.

## 3. WIRING (the lead applies it)

As a patch against HEAD 0d16a7a: `<work>/build/hud_D/wiring.patch` (`git apply --check` passes on HEAD and on the
working tree with its one uncommitted klhud.c line). The same as exact old -> new text blocks, one pair after the
other: `<work>/build/hud_D/wiring.pairs.txt` (17 pairs; applied by a script that insists each old text is found
exactly once). The steps:

1. `klhook.c`: after `#include "klgrudge.c"`, before `#include "klhud.c"`: `#include "klhud_values.c"`.
2. `klhud.c` defines: delete the line `#define KLU_S_LIVES     0x44 ...` (that byte is the number of rounds).
3. `klhud.c` `klu` struct, after the `int on, log, ... dials;` line: `int lives, roundof;`.
4. `klu_init`, after the `klu.dials = klu_inii("Dials", 0, 0, 1);` line:
   ```c
   klu.lives = klu_inii("Lives", 1, 0, 3);
   klu.roundof = klu_inii("RoundOf", 0, 0, 1);
   ```
   `Lives`: 0 none; **1 (default) three skull pictures (178) in your row** - 'LIVES n' in the round line when the
   level has no sprite handle for 178; 2 TEST: skull glyphs after your name (the stock way); 3 'LIVES n' in the round
   line. `RoundOf=1`: 'ROUND n OF m'.
5. New function before `klu_grid`:
   ```c
   static void klu_lives_row(int row, const char *name, int lives, int block)
   {
       float y = klu_r.cy + 30.0f + klu.row * row + kluv_skull_y(klu.row); int k;
       if (!klu.crew || klu.lives != 1 || !klu_r.handle[KLUV_SKULL_PIC]) return;
       for (k = 0; k < KLUV_LIVES_MAX; k++)
           klu_addpic(KLUV_SKULL_PIC, klu_r.cx + kluv_skull_x(name, klu.crew_w, k), y, KLUV_SKULL_SIZE, KLUV_SKULL_SIZE, kluv_skull_argb(k, lives, block), klu.layer);
   }
   ```
6. `klu_compose`, declarations: `char name[40]; BYTE lives = 0;` -> `char name[56]; int lives = 0, rn = 0, rm = 0;`
   and after `human = s.human >= 0 ? s.human : 0;`: `lives = klu.grid == 2 ? 2 : kluv_lives(&s);`
   In the Grid=2 demo, after the `for (row ...) klu_row(...)` line: `klu_lives_row(0, demo[0].n, lives, klu.plates);`
7. `klu_compose`, the row loop: `DWORD blk, str = 0, fl = 0; int kind;` -> `DWORD blk, str = 0; int kind;` and the
   three lines `klh_rd(s.score + KLU_S_FLAGS ...)` / `kind = r->status == 7 ? ...` / `klu_row(row++, ...)` become
   ```c
   kind = kluv_kind(&s, i);
   if (i == human && (kind == KLUV_K_YOU || kind == KLUV_K_TRAITOR)) {
       if (klu.lives == 2) {
           size_t l = strlen(name); int nl = lives > KLUV_LIVES_MAX ? KLUV_LIVES_MAX : lives;
           if (nl && l + 4 * (size_t)nl < sizeof name) kluv_skulls(name + l, (int)(sizeof name - l), nl);
       } else {
           char full[96];
           snprintf(full, sizeof full, "%s%s", name, kind == KLUV_K_TRAITOR && klu.tags ? "  TRAITOR" : "");
           klu_lives_row(row, full, lives, klu.plates);
       }
   }
   klu_row(row++, name, (long)r->money, kind);
   ```
   ONE decision: `kluv_kind` (through `kluv_state`) is the only place a row's state is decided; klhud.c no longer has
   an order of its own. New against Version 2: a human waiting to come back as police (flags 4 / 0x4000, status 1) gets
   the dead look; the fed that comes back (flags 8) is a fed.
8. `klu_compose`: `klh_rd(s.score + KLU_S_LIVES, &lives, 1);` -> `if (!kluv_round(&s, &rn, &rm)) rn = s.level;`
9. `klu_compose`, the round line's two `snprintf` lines ->
   ```c
   {
       char of[16] = "", lv[16] = "";
       if (klu.roundof && rm > 0) snprintf(of, sizeof of, " OF %d", rm);
       if (klu.lives == 3 || (klu.lives == 1 && !klu_r.handle[KLUV_SKULL_PIC])) snprintf(lv, sizeof lv, "   LIVES %d", lives);
       snprintf(klu_r.t[KLU_T_ROUND].want, KLU_TEXTLEN, "ROUND %d%s%s", rn, of, lv);
   }
   ```
10. `klu_compose`, the money bar: after the `float x = ..., f = ...;` line add
    `if (klu.grid == 2) f = 0.16f; else if (kluv_loot_total(&s) > 0) f = kluv_loot_share(&s);` (and the comment: the
    bar is re/hud_layout.md's loot bar - the crew's money against the level's loot).
11. `klu_compose`, before `klu_dials(&s);`: `if (klu.log >= 2) kluv_dump(&s, human);`
12. `klu_dials`, the watch: the three lines `/* the round watch: [rules+0x200] ... */`, `else if (!klh_rd(s->rules +
    0x200, ...)) clock = 0;` and `if (clock > klu_r.clock_max) klu_r.clock_max = clock;` ->
    `else { clock = kluv_round_left(s); klu_r.clock_max = kluv_round_len(s); if (clock > klu_r.clock_max) klu_r.clock_max = clock + kluv_round_played(s); }`
13. `klu_dials`, the escape dial: before its `if` add
    `i = kluv_vehicle_pic(s) == KLUV_PIC_CHOPPER && klu_r.handle[KLUV_PIC_CHOPPER] ? KLUV_PIC_CHOPPER : KLUV_PIC_CAR;`,
    the condition's `klu_r.handle[170]` -> `klu_r.handle[i]`, and `klu_addpic(170, ...)` -> `klu_addpic(i, ...)`.

Not wired: the money box could show the live **split** (`kluv_money` `.split`, 0 until you are out) beside LOOT;
`.round_score` is 0 until the round is over. The skulls' x wants a real text width once klhud.c has one.

Build with the wiring in a worktree of HEAD 0d16a7a (`G:/kl_scratch/D2`, removed again): SHIP
`<work>/build/hud_D/ship/dinput8.dll` **4210a01c**, TEST `<work>/build/hud_D/test/dinput8.dll` **814d6dd0**, no
warning at /W3 from the hook build and none at /W4 from the new file in the unit test. NOT RUN IN THE GAME.

## 4. Live checks, in order (owner away; TEST build of HEAD + the wiring; the bank unless said)

- **L1** `[HUD] Enable=1 Log=2` (+ what H1 used). LOG at GO: `hud: values: lives 3 of 3 | round 1 of 10 | money total 0
  = now 0 + banked 0; ... | loot: level N (rules sum N, 0 listed twice = 0), left N in K object(s), crew holds 0% |
  vehicle 00000000 kind byte 255 -> kind 0, picture 0 (stock clock 0) | you: flags 00000000 state 0 kind 1 (stock list
  0), killer -1 | result now 'Time_Up' + LifeLost | clock: left 360 s, played 0 s, length 360 s, ring 1.00`. Must
  hold: `left` = the stock clock's digits on the picture of the same second; `length 360`; `level` = `left` before
  anybody loots and about the sum of the map's money.
- **L2b** `Plates=1` (Lives=1 is the default): PICTURE: three dark skulls inside your chalk block, after the name, not
  over the cash; no 'LIVES' in the round line. No skulls and `ROUND 1   LIVES 3` instead = slot 178 has no type-5
  sprite in this level (the GUESS failed: say so, stay on digits). Skulls there but white-on-chalk / untinted = the
  tint guess failed. Read off whether `KLUV_NAME_CHARW` 9 puts them right after the name (a long and a short name).
  `Grid=2` shows the demo row 'J.C.' with two held and one faint.
- **L2** `Lives=2` (TEST key): three skull glyphs after the own name as the stock block shows them. Boxes / nothing =
  SetText does not take UTF-8 this way. Only of interest if L2b fails.
- **L3** a round with bots through to the vehicle: `carried` follows the looting, `crew holds %` rises and the bar
  with it, `left` falls by what was taken; aboard: `flags 00000020 state 8`; `split` > 0 only after `state 9` (flag
  0x40), `payout = rewards + split`.
- **L3b** the kind byte per map when the vehicle is there: the bank / Retomoto (F07's key-framed van) expect `kind
  byte 3 -> kind 3, picture 170 (stock clock 170)`; the park's helicopter `kind byte 2 ... picture 171 (stock clock
  171)`; a build with Dead Men's spline ZHavokCar `kind byte 1 ... picture 170 (stock clock 171)`. One 3 on a van map
  and one 2 on the park confirm the class table in the game.
- **L4** die (`--die` script) with `[Fed] Player=1`: while waiting expect `flags 00004004 state 6 kind 3 (stock list
  6)`, the row struck; after the respawn `flags 00000008 state 5 kind 5 (stock list 5)` and the row drawn as a FED,
  not struck; `killer -1` for a police kill. Without the fed: `flags 00000004 state 7 kind 3`.
- **L1b** GO of round 2 after a failed round (the same process): `lives 2 of 3`, `round 1` still, `banked` = the last
  round's `round score`; `level` and `K object(s)` EQUAL round 1's and `0 listed twice` (anything else = the restore
  ran without the reset: the corrected `level` should then still equal round 1's - if it does not, the +0x8c
  assumption is wrong); `clock: left 360 s ... length 360 s, ring 1.00`; PICTURE: two dark skulls and one faint.
- **L5** `RoundOf=1`: `ROUND 1 OF 10`. **L6** `Dials=1`: the watch's ring full at GO and half empty at 3:00 (180 of
  360), in round 1 AND round 2, also right after a klfed.c clock cut (left 3 s: no ring, the digits).

## 5. Review round (re/hud_values_review.md: ACCEPT WITH FIXES) - finding -> what was done

Every finding was checked against the exe / the code first; all MUST and SHOULD hold and are applied.

| finding | checked | done |
|---|---|---|
| **M1** the wiring gave 'LIVES n' / glyphs, not the draft's three skull pictures | re/hud_layout.md lines 27 / 40: holds | `Lives=1` (default) = three `klu_addpic(178, ...)` in the own row, ink / 4c0c0c0d (chalk without the block), through `klu_lives_row` + `kluv_skull_x / _y / _argb`; x from an ESTIMATED name width (named constants, said as a guess); digits only as fall-back (no handle) or `Lives=3`; glyphs kept as the test key `Lives=2`. The note's 'not a HUD picture' now says 'the stock list's' |
| **M2** the patch decided a row inline, `klv_state` by another order | holds (police + flag 1, waiting, status 5 differed) | one decision: `kluv_state` (our order, the owner's fed-before-traitor reason written at it) -> `kluv_kind` -> klhud.c; the inline order is gone; the stock order lives on as `kluv_stock_state` for the log only; the unit test pins both |
| **S1** `klv_` / `KLV_` are klhop.c's / klvis.c's | holds (81 + 9 uses there) | everything renamed `kluv_` / `KLUV_`; no other file referenced the old names |
| **S2** the vehicle classes | re-read, and taken further: the three static initialisers | 1 = **ZHavokCar** (not ZHavokLnkObj: that is the parent's name in the call), 2 = ZHeli, 3 = **ZAnimatedVehicle** - READ, no longer a hint; our dial `kind == 2 ? 171 : 170`, the stock rule in the dump; the int3 at 0x42d007 is in the note, kind 0 = 'no vehicle / not read' only |
| **S3** the dump recomputed every frame | holds | its own 'looked' tick: one look a second, nothing computed between; the redundant compare is gone; the list walk is cached a second for the wired readers too |
| **S4** slot 22 described from the wrong side | holds (0x8ea50e, 0x8ea601, 0x8ea622 re-read; 0x4c1dc0 has no 'already listed' test) | described as the state restore; duplicates are counted and taken off (`kluv_loot_scan`, an ASSUMPTION that does nothing while there are none); L1b added |
| **S5** L4's flags were a guess | holds (0x70479c before 0x704840; 0x4b2a54) | the note has the death sequence; L4 expects 00004004 then 00000008 |
| **S6** round 2's clock | holds (0x8c7a80 re-read; the 360 writer for round 2 not found) | said as NOT ESTABLISHED; L1b / L6 look at round 2 |
| N1 status 5 | holds | no reader gives status 5 a meaning |
| N2 'the meaning of the loot bar is ours' | holds | corrected: it is re/hud_layout.md's |
| N3 `RoundOf` default | checked further: n is clamped to 11 in the difficulty tables, one more than m | default stays 0, with that reason; the owner's call |
| N4 the space before a glyph | 0x7bb9c4 as the reviewer says | `kluv_skulls` writes a space before each glyph (test key only) |
| N5 kind 0 ambiguous | holds | the dump prints the vehicle pointer and the raw byte (`kluv_vehicle_raw`) |
| N6 `*m` half filled on a failure | holds | filled only on success |
| N7 which readers are wired | holds | section 2 and the file's head say it |
| N8 reads per compose | holds, acceptable | not changed |
| N9 a name cut inside a UTF-8 sequence | not new | not changed (`name[56]`, klu_row cuts at 63) |

Remaining guesses, all named in the code: picture 178 is a type-5 sprite and takes the tint; the name-width estimate
(9 px a character) and the 64 px kept for the cash; SetText decodes UTF-8 (`Lives=2` only); `[obj+0x8c]` is what a
second registration added; nothing shortens `[score+0x3c]` in a round; what restores 360 for round 2; whether Arcade
ends after round 10; flag 0x10's meaning; the order of flags 4 / 0x4000 as seen at run time.
