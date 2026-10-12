# Round-over scoreboard drawn by the hook (2026-10-12; OFFLINE, NOTHING RUN IN THE GAME, nothing installed)

READ = read in kl2.exe 0490 (re/hud_board_b.md); RAN = ran offline; GUESS = not established. `<work>` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools`, `<DD>` = the Dog Days folder.

## 1. What it is
`klhook/klhud_board2.c` (NEW, `[HUD] Scoreboard=1`, default 0, NOT tied to Draft) replaces the translucent centre panel of state 0x1f
('ROUND n / ROUND OVER / YOU ESCAPED / LIVES / SCORE / ROUND SCORE / TOTAL SCORE / CONTINUE IN: n') = `ZHeistOutroDisplay`, `[osd+0x10b4]`, vtable 0xbbde28
(Render slot 2 = 0x577e70, Tick slot 5 = 0x5528c0, deadline float `[el+0xd8]`; plate drawn only while `[[0xdd2640]+0x48] < (int)(deadline*1024)`; READ).
The XML page after it (state 0x20, BUY WEAPONS / READY) stays stock, with the committed `kl_hud_menu.py level` row-pitch fix (re/hud_board.md). The pre-round panel is klhud_board.c.
Needs `[HUD] Enable=1` and the level's baked fonts (`Fonts=1`, on under `Draft=1`), plus the level's extra pictures (kl_hud.py all --look deadmen).

## 2. How it works (every failure = the stock panel; never both, never nothing)
- Wrap: private vtable copy (16 slots + RTTI), slot 2 -> `klsb_render`. Refused (and logged) unless slot 2 == 0x577e70, slot 5 == 0x5528c0, first code bytes `83 ec 3c 56 8b f1 8b 0d` (`klu_same_code`) and the element's vtable == 0xbbde28. One heap dword written, no .text patch. Dropped when the OSD identity changes.
- Render decision (render thread): draws ours only when ALL hold: the tick's snapshot is valid and was taken in state 0x1f; deadline in (0,1000) and engine frame < deadline*1024; the pictures usable (`klsb_pic2` conditions below) unless `ScoreboardTextOnly=1`; OSD vtable and pool text 0 canaries read; `klsb_cs` got with TryEnterCriticalSection (a busy lock = stock panel that frame). Otherwise it calls the stock 0x577e70 unchanged. Probe / Test modes never draw the board.
- Pictures: `klsb_pic2` = `klu_pic` with the clock element's transform `[el+0xc]`, table `[el+8]` and description `[el+0x40]` CACHED by the tick (the clock draws in 0x16..0x19: the only proven description); refuses unless the outro element's `[el+0xc]` / `[el+8]` equal the clock's and `desc[0]==1`. Handles = `klu_r.handle[]` (type-checked by klu_pic_prep). Queue built in the tick with klhud.c's own `klu_addpic / klu_outline / klu_arc / klu_track` through a new redirect (`klu_addpic_q`, klhud.c: three lines; set and cleared inside `klsb_compose`).
- Texts: 40 ZCHAROBJs made once per OSD in states 0x17..0x19 through `klu_make_obj` (the proven create path; fonts = the four roles), string / colour set in the tick under `klsb_cs` (`klsb_apply`), drawn by `klu_draw_one`. No shadows (the plate is dark).
- Data (tick, state 0x1f only, main thread): `klb_read` + klhud_values.c readers (they already existed: `kluv_result`, `kluv_killer`, `kluv_lives`, `kluv_money`, `kluv_money3`, `kluv_state`, `kluv_flags`, `kluv_round`; nothing added there). Any failed read -> no snapshot -> stock panel.
- Known cosmetic: the snapshot is taken in the first tick (<= 100 ms) of 0x1f, so the stock panel can show for a few frames before ours.

## 3. Cells and sources (score = `[rules+0x5f8]`)
| cell | source |
|---|---|
| title | ROUND OVER / GAME OVER (`kluv_result` game_over = lives <= 0) |
| ROUND n | byte score+0x45 (the 'of m' is not shown: not established that a session ends at 10) |
| result | `kluv_result` on record 0 and the crew: EVERYBODY ESCAPED / YOU ESCAPED / EVERYBODY IS DEAD / YOU ARE DEAD / LEFT BEHIND / TIME IS UP (our English, coloured by fate) |
| KILLED BY | signed byte `[score+0x10c+i]` = killer's crew index (name from the crew), else THE POLICE; only when dead |
| lives | signed byte `[score+0x6c]`, three skulls (178), lost ones faint; 'LIVES n' text when the level has no 178 |
| crew rows (8) | column head PAYOUT (record+0x2c; the summary's ROUND SCORE is score+0x30 incl. bonuses, so the two can differ); name = `[[rec]+8]` + `klnm_name`; fate = `kluv_state` (+ traitor flag score+0x1d4 bit 1 / record flag 2): DEAD / ESCAPED / TRAITOR OUT / TRAITOR / ABOARD / FED / LEFT BEHIND; round score = record+0x2c (payout), carried money if escaped and payout 0, $0 if dead. Own row chalk block (ink letters), traitor orange block, dead = faded red + strike |
| ROUND SCORE | score+0x30 (`m.round_score`), else the live sum |
| REWARDS | score+0x184+4*human |
| TOTAL SCORE | `ScoreboardTotal` **1 (default) = score+0x38 alone**; 0 = +0x38 + +0x30 and 2 = `kluv_money.total` DOUBLE-COUNT (READ: 0x5e0012..0x5e001b does `[score+0x38] += [score+0x30]` before 0x5e0040 changes the state to 0x1f; values_md row 30: the stock page prints +0x38; the owner's round 1 shows ROUND = TOTAL = $707,778). SB0 logs all three |
| CONTINUE | ceil of the deadline's seconds left (`ScoreboardCount=0`) or `[rules+0x4c]` (1); ring = fraction of its first value |

## 4. Keys `[HUD]` (all default off / as listed)
`Scoreboard=0`; `ScoreboardProbe=0` (LOG ONLY: once a second from state 0x1f: state, element vtable, deadline, frame, wrapper calls, the clock wrapper's calls, the TOTAL candidates, the state timer); `ScoreboardTest=0` (stock panel drawn, over it an outline, three texts - left at X+10, right at X+630, centre at X+320, y+6 - and three pictures at X+40 / 240 / 440, y+300); `ScoreboardFault=0` (TEST: every reader fails); `ScoreboardX=320 ScoreboardY=150`; `ScoreboardAlpha=230`; `ScoreboardTotal=1` (see 3); `ScoreboardCount=0`; `ScoreboardTextOnly=0`. Log=2 adds the 5 s counters and every text change.

## 5. What is still stock / deviations from the judge's spec
- BUY WEAPONS / READY page and leaderboard rows (XML, state 0x20, black): stock + the row-pitch / colour fix. No painted-bar buttons. XML crew rows deferred until K0 (table count) exists.
- The translucent panel is replaced only in 0x1f. Whether the Render is even called in 0x20 is what SB0 logs.
- Row blocks (own / traitor) are 181 too (review S5: 111 broke the orange block under the letters); only the rules and the strike lines stay 111.
- Plate = picture 181 (UI_White) in ink with alpha, NOT 111: 111 is a ragged brush stroke and stretched to 640 x 372 it shows vertical holes (seen in the preview). 111 stays on the row blocks and rules. Plate 640 x 372 (was 400 in the spec: summary line moved up) with a 1 px coral outline.
- Summary laid out as the draft (three labelled values left to right, ring at the right) instead of the spec's stacked lines; the label font is wide (cap 10, tracking 3), columns at 336 / 504 / 624. KILLED BY stands on the result's line (x 480).
- No 'OF m', no 'LOOT DROPPED' detail, rows in record order (the draft sorts), text pool 40 (not 48).
- GUESSES the runs decide: score+0x30 is written by 0x1f; the countdown source; TOTAL's formula; payout +0x2c written at 0x1f; the outro element's +8 / +0xc equal the clock's; picture anchor (PicAnchor, as klhud.c).

## 6. Offline results (RAN)
- Hooks: `<work>\build\klhook\hud_v26_test\dinput8.dll` (sha1 78da2939), `hud_v26_ship\dinput8.dll` (sha1 ad8a73df); source = `git archive HEAD klhook` + the working klhud*.c / klhook.c in `G:\kl_scratch\hud_v26` (klhook.c: include, tick, init lines; klhud.c: the `klu_addpic_q` redirect). TEST and SHIP build; /W4 of klhook.c: no warning from klhud_board2.c.
- `klhook/klsb_test.c` (`cl /W4 klsb_test.c` in the klhook folder, 32-bit): the real klhud_values.c / klhud.c / klhud_board2.c with the game's routines stubbed: 91 checks PASS - zeroed, garbage and wild-pointer memory give no snapshot; ScoreboardFault; the render slot takes the stock branch for: no snapshot, state 0x20, deadline passed / unset, pictures not cached, another transform / table, OSD canary, text canary, not a ZDrawBufferSimple, not the wrapped element, Probe mode, a lock held by another thread; the good case calls no stock Render; three made-up rounds (escaped / dead killed by crew 2 / traitor, game over); level without 178 / 181; the HUD's own picture queue untouched; the redirect always cleared.
- Preview `<work>\build\hud_x9\scoreboard_preview.png` (dead case, 1280 x 720, sha1 a312cf69), `scoreboard_preview_escaped.png`, `_traitor.png`, `_sheet.png`: `python tools\kl_hud.py preview-board <work>\build\hud_tab\DM03 <out.png> board_dead.txt ...` draws the layout the C code composed (klsb_test.exe <folder> writes the txt) with the baked fonts and extras (181 flat, the skull is a hand-drawn stand-in). Compared with the draft (draft_board.png, Edge screenshot of the mockup's board): same order and colours at quiet sizes; not seen in the game.
- Level: `<work>\build\hud_x9\DM03\F03_Main.zip` (168,869,142 B, sha1 d5d591e5) = hud_tab\DM03 + `kl_hud_menu.py level` (row-pitch fix `FA_Status_GeomSpace 16 -> 10`, coral totals labels); `check-level` PASS 0 fails 0 notes (same bytes as hud_x8's). The board itself needs NO level change beyond the extras the tab already has (111, 112, 114, 115, 123..125, 181, 178 stock).

## 6b. Review round (2026-10-12, hooks hud_v27)
| finding | outcome |
|---|---|
| M1 TOTAL double-counts | DONE: default `ScoreboardTotal=1` (+0x38 alone); test and preview data changed (round 3: +0x30 250,000, +0x38 650,000 -> $650,000); 0 / 2 kept for the probe |
| S1 pictures use the clock's description | DONE: `klsb_cache_odesc` reads the outro element's own description at el+0xa4 in state 0x1f (used only if desc[0]==1 and the record words are not all zero; else the clock's stays); both heads logged (`descriptions - outro element el+0xa4 head ... clock el+0x40 head ...`) |
| S2 wrap failure latches off | DONE: up to 30 ticks (3 s) of retry, then refused with the reason logged; a code / vtable mismatch still refuses at once |
| S3 pool rebuilt each round | NOTE only (40 scene-owned text objects per round on a persistent scene; the HUD does the same) - watch SB3 |
| S4 two 'round score' meanings | DONE: the rows' column is PAYOUT |
| S5 ragged 111 on row blocks | DONE: 181 (preview: the orange block is clean) |
| S6 LAST_ESC wording | DONE: human dead -> YOU ARE DEAD + KILLED BY; fed -> YOU ARE A FED + KILLED BY; else LEFT BEHIND |
| S7 stock panel flashes <= 100 ms | ACCEPTED; SB1 looks for it |
| NOTE layer clamp | DONE (`klsb_ly`, never below 0) |
| NOTE probe log spam | DONE: with Log=2 the probe line only from state 0x1f (ScoreboardProbe=1 still every second) |
| NOTE 'OF m' | not added (not established that a session ends at m) |
Re-run after the fix: `klsb_test.exe` 91 checks, 0 failed; hooks `<work>uild\klhook\hud_v27_test` (sha1 1bf4f1ab) / `hud_v27_ship` (55c23e01), source `G:\kl_scratch\hud_v27`; previews rebaked in `<work>uild\hud_x9`. The level archive `hud_x9\DM03` is unchanged (no level data changed).

## 7. Live checks (owner away; bank in slot F03, one level, pictures every 1 s, game closed first)
Common: hook `hud_v26_test` as `<DD>\dinput8.dll` (old one aside), archive `hud_x9\DM03\F03_Main.zip` over the tab's DM03 archive for ONE run (old = `hud_tab\DM03`), `[HUD] Enable=1 Draft=1 Log=2`.
- **SB0 (probe)** + `ScoreboardProbe=1`, then `ScoreboardTest=1`: die or escape. Log: `scoreboard: on`, `element ... now renders through the private vtable`, `texts made`, `clock element's picture description cached`; per second from 0x1f the probe line (vtable must read ZHeistOutroDisplay / OUR private copy, wrapper calls > 0, whether the clock wrapper is still called in 0x1f / 0x20). Test: outline, texts and pictures over the stock panel at the stated places. Pass = no fault.
- **SB1 escape**: `Scoreboard=1`; escape with the crew. Pictures must show: a dark plate with a coral outline in place of the grey panel, ROUND n, 'YOU ESCAPED', your row on a chalk block, fates green, ROUND SCORE / REWARDS / TOTAL SCORE, the ring counting down; log `first snapshot ... ready`. Then the BUY WEAPONS / READY page, rows one line apart. Compare with the preview.
- **SB2 death**: die early (`[Fed] Player=0`): YOU ARE DEAD, KILLED BY ..., your row faded red + struck, a skull gone; then the XML page.
- **SB3 second round**: a second round starts, the board shows again with new data (pool made again), no fault. Also `ScoreboardFault=1` (stock panel, log line), `Scoreboard=0` (stock panel), a traitor run.
Decide: confirm TOTAL = +0x38 against the stock page's own figure (probe line: +0x30, +0x38, round n at +0x45), the countdown source, whether score+0x30 is already written at 0x1f (round score shows $0 otherwise).

## 8. Install and back out
Install (game closed, owner away): old `dinput8.dll` aside, `hud_v26_ship\dinput8.dll` in, `[HUD] Scoreboard=1` only after SB1 / SB2 passed; for the page fix rebake the seven maps (`kl_hud_menu.py level <hud_tab\id> <out>` + `check-level`) and copy only `<slot>_Main.zip`. Back out: `Scoreboard=0` (stock panel again, nothing else changes), old dll, old archive.
