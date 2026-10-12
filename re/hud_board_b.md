# Design B - the round-over board drawn by the hook (2026-10-12; OFFLINE, static reading of kl2.exe + the repo; NOTHING BUILT, NOTHING RUN)

READ = read in kl2.exe 0490 (debug/dasm.py); PROVEN = a live run drew it (re/hud_hook.md); GUESS = neither.

## 1. VERDICT
FEASIBLE for the translucent centre panel (what the owner sees at the end of a round, over the world). NOT feasible as the replacement of
the BUY WEAPONS / READY page: that page is XML in a menu state, drawn on black with the world gone; the HUD very probably does not render
there. So Design B = a board that replaces the 'ROUND 1 / ROUND OVER / LIVES / SCORE / CONTINUE IN' panel (about 8 s), and the XML page
after it stays (restyled by kl_hud_menu.py level, as committed). That is the 'full draft attempt' the owner can have without touching the
5,096-element menu table. Effort: about 1.5 days of code (one new file klhud_board2.c, ~500 lines, reusing klu_* primitives), 2 live runs.

## 2. What the game does after a round ends (READ)
| state | what | evidence |
|---|---|---|
| 0x19 | round runs; clock element draws; klhud draws | proven |
| 0x1f | ROUND OVER. Entered through the rules' state-enter routine 0x5e8570 (switch on new state; 0x1f -> case at 0x5e85ae / 0x5e8827), which calls **0x7dede0** (twice on the path), sets the state timer `[rules+0x4c]` = 8.0 s (const 0xb4aaec) | READ |
| 0x20 | score page: timer 30 s (0xb7ee44); the XML `HeistStatusLeaderboard`; black background in G2_DM03_tags_184s.png | READ + picture |
| 0x28 | session end ('0x1f -> 0x28' in the old log): rules / crew torn down | fa_round.md |

**What draws the translucent panel (the open point of hud_board.md): ZHeistOutroDisplay = `[osd+0x10b4]`, vtable 0xbbde28, 0xdc bytes, Arcade
only (Render gate 0x7f6850).** (re/hud.md lists it, key 0x24; nobody had linked it to the panel.) Proof chain:
- 0x7dede0 (called at state 0x1f) builds nine strings (title `Round_Over` / `Game_Over`, the result line All_Esc / You_Esc / ..., lives, score, round
  score, total score, keys `AllLevels/Interface/Online/GameEnd/Outro_Heist_Lifes`, `Outro_Lives`, `Outro_Points`, `Outro_Heist`) and, at 0x7dfb6d, calls
  `0x75f780(osd, 1)` (the HIDE of the clock and the player list, the byte klhud already knows) and then **`0x8a5340` on `[osd+0x10b4]`** with the nine strings.
- 0x8a5340 (ret 0x24): SetText (vtable +0x244) on 20 text objects at element offsets +0x2c .. +0x98 (text / shadow pairs), and sets the
  element's deadline `[el+0xd8]` = (engine ms `[0xdd2640]+0x48` + 0x2800 = 10.24 s) / 1024. The empty-string branch resets it to -1.0.
- Render = slot 2 = **0x577e70** (thiscall ret 8, `sub esp,0x3c` ... same shape as Intro's 0x768c40): draws the plate `[el+0x28]` (alpha 0xff,
  size 630 x 100 from 0xcedd60 / 0xcedd64) only while engine time < deadline, then `[el+0x2c]`, `[el+0x30]` ... at (el+0x14, +0x18), 2 px shadows.
- Tick = slot 5 = **0x5528c0**: while the deadline is live it builds `GoingToMenu` with `{Time}` = the countdown ('CONTINUE IN: 4') and re-sets
  the texts; when the deadline passes it clears them.
The elements' vtable slot layout is the same as the Intro's, so the proven private-vtable wrap (klhud_board.c, klhud.c's clock wrap) applies.

**Is the HUD rendering in 0x1f? YES for this element** (the owner's picture 0036_419s.jpg shows it over the street) and NO for the clock / player list:
0x7dede0 hides them (+0x25) - which is why klhud stands down outside 0x17..0x19 and why a wrap of the clock's Render cannot draw the board.
**In 0x20: UNKNOWN, probably not** (black page). A live probe settles it (section 7, B-P1); the design does not depend on it.

## 3. Where the hook draws
Wrap `ZHeistOutroDisplay` slot 2 (Render) with a private vtable copy, exactly as klhud_board.c does for the Intro (code bytes of 0x577e70 checked
with klu_same_code first; one heap dword written; no .text patch). Inside the wrapper, with ctx / cam as passed:
1. Decide `board_on` = our data read OK (section 4) AND state 0x1f AND the element's deadline is live ([el+0xd8] * 1024 > engine ms).
2. If board_on: do NOT call the stock Render (the plate, the 20 texts and the two rules simply are not drawn); draw ours with the proven
   primitives: `klu_draw_one(obj, ctx, cam, x, y)` for texts (our level-made ZCHAROBJs, four font roles) and `klu_pic(...)` for pictures.
   Else call stock 0x577e70 unchanged (the fall-back is the stock panel, always).
3. The stock tick (slot 5) still runs: it keeps setting its texts and the deadline; harmless, and it keeps the 'CONTINUE IN' text current,
   which we can READ (text object string) instead of recomputing; if that read fails we compute `ceil(rules+0x4c)` (GUESS: the state timer
   counts the 8 s down; the stock {Time} is built at 0x552a1b from the engine clock, not read).
Picture primitive needs one change: `klu_pic` copies the DESC from `el+0x40` (the clock element's vehicle-icon desc, `desc[0] == 1`). The Outro
element's +0x40 is a text object. FIX: cache the clock element's `desc[13]` once (klu_pic_prep time, state 0x17..0x19, proven path) in a static,
and have a `klu_pic2()` that takes that copy plus `T = [osd-side]` (the transform pointer; `el+0xc` is the base-class field present in every element
- READ for the clock at 0x81e20b, ASSUMED identical for the Outro; verify by `klh_rd32(el+0xc) == klh_rd32(clock+0xc)` and refuse otherwise).
Handles come from the same per-level picture table the tick already read (`klu_r.handle[]`; `[el+8]` is the same OSD-wide table, check equal to the clock's).
Texts: the level-made objects (25 + 25) already exist for the HUD; the board needs about 60 text draws (title, result, killed-by, 8 rows x 3, 6 summary,
countdown). Either add a pool of ~48 more through the same create path (klu_make; made once per OSD in state 0x17..0x19, so BEFORE the round ends) or
reuse the crew list's / popup's objects, which are idle in 0x1f (their draw is in the clock wrap, which does not run) - the second is free but needs a
re-style per frame (SetText/SetColour from the render slot, lock-free); choose the pool: simpler, 48 x ~0x100 bytes.

## 4. Data, per cell (klhud_values.c readers, all return 0 / 'nothing' on a failed read; `score = [rules+0x5f8]`)
| cell | source | reader / evidence |
|---|---|---|
| header `ROUND n` (`OF m` optional) | byte score+0x45 (n); m = byte score+0x44 = 10, not shown (not established that a session ends at 10) | kluv_round |
| result: ESCAPED / DEAD / LEFT BEHIND / ALL ESCAPED / TIME UP | flags and status of record 0 and the crew by the game's own logic 0x7df067..0x7df428 | kluv_result (+ our English text; or the game's own string: the stock text object `[el+0x2c+..]` holds it already, readable) |
| title `ROUND OVER` / `GAME OVER` | lives <= 0 | kluv_result |
| killed by | signed byte `[score+0x10c + i]` = killer's crew index, -1 none; the role of an NPC killer is NOT read ('the police' fallback) | kluv_killer |
| lives (skulls) | signed byte `[score+0x6c]`, 0..3 | kluv_lives + picture 178 as the own-row skulls |
| crew rows: name | the string at `[[record]+8]` (character name, as klcrew / klhud_names write it) | klhud's klu_row |
| crew rows: fate | status 6 escaped, 7 dead, 4 aboard, flags 1 / record+0x79 mask 2 traitor, 8 fed, else 'LEFT' (alive, not out) | kluv_state / kluv_kind (the klhud rules) |
| crew rows: round score (the 'cash') | record+0x2c (rewards + split: 'what he would take') / +0x28 split | kluv_money (READ 0x796410) |
| ROUND SCORE / REWARDS / TOTAL | score+0x30 (written by 0x783010 BEFORE 0x7dede0? ASSUMED: 0x7dede0 prints it, so yes at 0x1f), kluv_money3 rewards, score+0x38 (total) | kluv_money; live check B-P2 |
| continue ring + number | the stock 'CONTINUE IN' text, or `rules+0x4c` (see 3); ring = klu arc slices 123..125 as the HUD's rings | klu_ring |
Validity: 0x7dede0 itself reads these at 0x1f entry, and the score page (0x20) reads them for the XML tags, so rules, score and records live through
0x1f-0x27; teardown is around 0x28. Every reader still verifies the score vtable (0xbd3500) and rules vtable.

## 5. Layout (virtual 1280 x 720, from the draft's `.board`: 880 px wide at 100 cqw = 8.8 px per cqw; ours scaled to a 640-wide plate, QUIET sizes)
- Plate: ink gradient is not available; use picture 111 (the painted block) in ink, 640 x 400, centred x 320..960, y 150..550, alpha ~0.9, plus a
  1 px coral outline (picture 181 x4, as Grid does).
- Top row (y 168): left `ROUND n` big (Anton cap ~15, chalk), under it the label `ROUND OVER` (Montserrat cap 10, coral, spaced) and the result in coral / orange /
  chalk by fate (cap 11); right: `LIVES` label and three skulls (178, 14 px, held = ink on a chalk block / lost = 4c alpha).
- `KILLED BY` line (only when dead) cap 10 coral under the result.
- Rule: brush stroke picture 112, 600 x 4 at y 232.
- Column heads at y 242: DEAD MEN / FATE / ROUND SCORE (labels cap 10, coral).
- Rows at y 262 + 24 i, i < 8 (the game has at most 8 records): block under the row = picture 111 (own row chalk, traitor orange), name left x 336 (cap 11),
  fate at x 560 (label font cap 10), round score right-aligned at x 944 (green, cap 11); dead = faded red text + strike picture 112; out = grey.
- Summary at y 470: ROUND SCORE and REWARDS small coral labels left, TOTAL big green right (cap 15), thin money bar picture as the HUD's.
- Continue ring at (880, 500), 40 px: slot 123..125 ring + number in the middle, label `CONTINUE` cap 10.
Sizes and fonts are the HUD's four roles (they are baked in the level archive already; no new font data). All numbers go into `[HUD] Board2*` keys like the HUD's.
Per-frame budget: about 60 text draws + about 45 pictures (plate 5, rows 8 x 3, skulls 3, ring 5, rules 3); the HUD's worst case is 205 pictures a frame and a 288 queue,
so the board is lighter than a normal HUD frame. No system call in the render slot (the tick prepares a snapshot under klu_cs; the render only TRIES the lock).

## 6. Suppressing the stock panel and keeping input
- The stock panel needs no suppression beyond not calling 0x577e70 (the plate and texts are drawn by that Render only; its tick keeps them valid). Nothing is hidden by a byte, no alpha is touched, so
  a failure at any point (a read fails, the lock is busy this frame, the wrap is refused) means the stock Render is called: the owner sees the old panel, never nothing.
  One frame without ours is possible when the lock is busy: draw the stock panel that frame too (one-frame flicker, not a crash).
- Input: state 0x1f has no input; the next page (0x20) is XML with its own focus. The board does not touch the menu manager, so READY / BUY WEAPONS keep working. If the board were ALSO shown
  in 0x20 (B-P1 says the HUD renders there), the buttons must stay: draw the board only above y 0..560 of an area that the XML page does not use - NOT planned.

## 7. Risks, ranked (which could crash)
1. A wrong `desc` / transform for pictures from a non-clock element (klu_pic2): a bad DrawChunk record could fault inside the render thread. Mitigation: copy the clock's proven desc; refuse unless `el+0xc` equals the clock's; the HUD's 10 s probe `PicTest` pattern as the first run; guard by the 'canary' reads klu_draw_ours uses. CRASH-CLASS: yes (render thread). 
2. Text objects created too late: the pool must exist before 0x1f; objects of a scene die with it (the klu_r.osd identity check drops the board when the OSD changes). A board drawn from stale pointers = crash; the canary (OSD vtable + text 0 vtable) is the guard.
3. The first frame of 0x1f: the element's deadline is set by 0x8a5340 inside 0x7dede0, which runs BEFORE our wrapper's first call; if the rules / records are mid-update, the readers return 'nothing' and the stock panel shows - safe.
4. Thread: Render runs on the render thread, the tick on the main thread; same lock rule as klhud (render TRIES, never waits).
5. The slot-2 wrap of an element nobody wrapped yet: private vtable copy of 11+ slots; ZHeistOutroDisplay's vtable has more slots after 10 (0x0, floats): copy the full 0x40 bytes the Intro part copies, check slot 2 == 0x577e70 and the first code bytes (`83 ec 3c 56 8b f1 8b 0d`), refuse otherwise.
6. Guess-level (not crashes): score+0x30 set before 0x1f; `rules+0x4c` as the countdown; fate wording; the pitch of text at those cap sizes.
7. Online (Sv / Cl classes): the element is Arcade only (0x7f6850) and our reads check the Heist rules vtable 0xbd3514, so the board is inert online.

## 8. Testing
OFFLINE: (a) extend klu's snapshot test harness (`build/hud_D/kluv_test.c` style) with a made-up rules / score / 8 records and render the board layout through a stub ctx to PNG via the existing `tools/kl_hud.py preview-hud` approach (add a `preview-board` of the layout numbers - the draft HTML is the reference); (b) `/W4` compile TEST + SHIP; (c) a unit check that every cell reader returns 'nothing' on zeroed memory and that the wrapper calls the stock Render in each failure branch; (d) `check` the level archive has the extras (111, 112, 123..125, 178 or its fall-back 181).
LIVE (owner away; hook from `git archive HEAD klhook` + working klhud*.c; ONE test level: the bank, slot F03):
- B-P1 PROBE: `[HUD] Enable=1 Draft=1 Log=2 Board2=0 BoardProbe=1`: log, once a second from 0x1f on: state, `[osd+0x10b4]` vtable (must read 0xbbde28), its deadline, our wrapper's call count, and whether the CLOCK's wrapper still gets calls in 0x1f / 0x20 (expect none in 0x1f; 0x20 decides the 'is the HUD rendered on the score page' question). Pass = no fault, the vtable reads, calls counted.
- B-P2 TEST SHAPES: `Board2=1 BoardTest=1` = draw only a coral outline + three texts + three pictures at known places over the stock panel (stock still drawn): do they appear, where do they anchor (the Grid method).
- B1 die, B2 escape (the two results), B3 a fed / traitor / left-behind: full board, pictures every 1 s over the 8 s; compare with the preview; the stock panel must come back if `Board2=0`.
- Fall-back test: one run with a deliberately failing reader (`BoardFault=1`): the stock panel shows, no fault.

## 9. What stays stock / not covered
BUY WEAPONS / READY page and the leaderboard rows (XML, restyled by kl_hud_menu.py level), the death panel (FARespawn XML + ZFADeathCamDisplay), the pre-round Intro panel (klhud_board.c recolour), game-over / final-take page (XML). A hook board in state 0x20 would need the B-P1 answer and a new anchor discipline; only then.

## 10. Effort
klhud_board2.c: wrap + state / data snapshot (~200 lines, patterned on klhud_board.c and klhud's klu_row), layout + draw (~250), klu_pic2 + desc cache (~40), keys + log (~60), preview-board (~150 Python), 2 reviews. About 1.5 days plus the live runs B-P1, B-P2, B1, B2.
