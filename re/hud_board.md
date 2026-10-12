# Round-over page, pre-round panel, death panel in the new look (2026-10-12; OFFLINE, NOTHING RUN IN THE GAME, nothing installed)

Words: READ = read in kl2.exe (debug\dasm.py) or in the files; RAN = the tool ran offline; GUESS = not established.
`<work>` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools`. `<DD>` = the Dog Days folder.

## 1. How each page is made

| Page | Mechanism | Evidence |
|---|---|---|
| Arcade round over / score page (`AIRPORT ROUND 1`, BONUS / PENALTY, ROUND SCORE, TOTAL SCORE, POS / NAME row, BUY WEAPONS / READY) | XML window of the LEVEL archive: `Menu/online.xml` inside `<slot>_Main.zip`: `HeistStatusLeaderboard` (the one the game opened in G2_DM03_tags_184s; leaderboard bar at the bottom) / `HeistStatus` / the two `_EndGame` twins. Rows are `TextBlock`s (labels from .LOC keys) and `MercsShowInfoFA` tags (`HeistPoints*`); bars and lines are the level's own `.TEX` pictures (`FocusBar_*`, `Line_*`). Font = the LEVEL's `Text` / `Header` slots (kl_hud's bake) | READ in the XML (lines 1555-1740 of the baked DM03's online.xml); re/hud_menu.md 1.3 |
| Death panel (`YOU ARE DEAD`, `Killed by: The police`, `YouRespawnAs`) | XML windows `FARespawn`, `FARespawnNoPIP`, `FARespawnTeam`, `FADead`, `FADeadNoPIP` (same file); `KilledBy` etc. are data tags. A second, HUD-side element `ZFADeathCamDisplay` (osd+0x10a0, vtable 0xbbdcc8, slot 5 builds `YouRespawnAs%s`) draws the death camera's text | READ (XML); re/hud.md table, re/fa_gamemode.md |
| Pre-round panel (`FRAGILE ALLIANCE ARCADE - ROUND 1`, `LIVES LEFT` + skulls, `HEIST STARTS IN n SEC`) | NOT XML (no key of it in the XML; grep of `Lives|StartsIn|Countdown` in all four level XML members is empty). HUD element `ZFAIntroDisplay` = `[osd+0x10ac]`, vtable 0xbbdd98, Render slot 2 = 0x768c40. It draws: the plate object `[el+0x28]` (the translucent grey rounded box; text-class object: SetAlpha vt+0x218, size vt+0x23c, Draw vt+0x1e8), then text objects `+0xac/+0xb0` (text + shadow 2 px apart), `+0xb4..+0xc0`, `+0xcc/+0xd0`, and the two rules by 0x8a6ca0 (colour 0xbbe490, alpha 0x7f) | READ (0x768c40 disassembled, `G:\kl_scratch\hb\intro.txt`); re/hud.md row 0x10ac |
| `ROUND n  ROUND OVER` translucent panel (G2 182 s) | NOT FOUND: no XML window with that text (`FARoundOverMenu` is a different, plain list page) and no HUD element looked at. Left stock | not established |
| Loading page | not looked at | - |

## 2. WHY `ROUND SCORE` PRINTS OVER THE NUMBER (found; fixed in the level step)

Rows of a table are children of a `GUIGroup` with `Template="FA_Status_GeomSpace"` = `GeomSpace="16"`: the pitch of a row is the font's line height
plus 16. The stock `Text` font (20 px) has ascent 13 (`kl_hud.parse` header[9] = -13): pitch 32, which is what the page was drawn for (rows
113 / 145 / ... / 273, line pairs 309 / 312, 352 / 355, 395 / 398, and the two `Font="Header"` elements at Y 232 / 275 = ROUND SCORE / TOTAL SCORE).
The level bake's `Text` font (21 px Anton) has ascent 19 (READ in `hud_tab\DM03`'s font chunks: -19, line field 27 against 22): pitch 38 measured on
the picture (rows 59.5 display px = 38.1 virtual apart). Row 7 (the `TOTAL` row, `HeistBonusRound` / `HeistPenaltyRound`) therefore moved from
first row + 192 to + 228, on top of ROUND SCORE at + 232. So it is the wider face's taller line, not a fixed x. (Also true: stock Dog Days would show
no overlap at pitch 32; the stock page itself was not looked at.)
FIX: `GeomSpace` 16 -> 10 on that one template, level archives only (pitch 32 again; ROUND SCORE is then 40 px below the TOTAL row). The same
template feeds every status page of the level, so their rows return to the stock pitch too (their bars were drawn for 32 / 34). The menu scene's
copy of online.xml is NOT touched (its `Text` is 19 px, other metrics; the menu has no round-over page).
GUESS: pitch = ascent + 3 + GeomSpace (fits 13 + 3 + 16 = 32 and 19 + 3 + 16 = 38). If the first run shows 31 or 33, tune `BOARD_GEOM_NEW` in `tools/kl_hud_menu.py`.

## 3. What changed

`tools/kl_hud_menu.py`: new `board_page()` (called by `level` only; attribute values only, the table is untouched, `check-level` PASS):
- `FA_Status_GeomSpace` GeomSpace 10 (above);
- the totals' labels (`HeistRoundPoints`, `HeistTotalPoints`, `HeistBonusRound`, `HeistPenaltyRound` TextBlocks, 4 windows = 16 elements) get `ColorSet="Header"` = coral (the draft's labels);
- as before (the colour step): bonus values / round / total green, penalties coral, traitor orange, bars chalk with ink text, lines dry-brush.
`klhook/klhud_board.c` (NEW, `[HUD] Board=1`, DEFAULT 0, not switched on by Draft): the pre-round panel. A private vtable copy of `ZFAIntroDisplay` with slot 2
wrapped; for the length of the stock Render call the plate object's colour is INK (alpha kept) and every non-dark text of the element is CHALK,
then everything is put back in the same call. `BoardInk=0 / BoardLetters=0` switch the halves off. Wired in klhook.c: one include, one tick, one init
(`klbrd_*`; the prefix `klbd_` is taken by klbotdown.c).
`klhook/klhook.c`: three lines. No other file touched.

## 4. What could not be changed, and why

- Painted chalk plates / rules / a continue ring / skulls on the round-over page: a new picture is a new entity and a new table entry (re/hud_menu.md 1.1, 5);
  the page is XML in a LEVEL archive, and `level --board` (crew rows) shifts the table, which waits for live check K0's count. Not done.
- The heister list (name / fate / round score per crew member) of the draft: same reason; `kl_hud_menu.py level --board` exists and stays opt-in.
- The pre-round panel: the hook can only recolour. Pictures cannot be drawn there (`klu_pic` needs the clock element and draws from state 0x19 on,
  klhud.c's `klu_draw_on`), so no chalk bar, no skull restyle, the two rules stay stock (alpha 0x7f grey-white from the static colour 0xbbe490: a global I do not write).
  Whether `klu_r.osd` is known before state 0x19 (the scan runs in Arcade round states only) is a GUESS: if not, `Board` does nothing before GO and the log says no 'board: element' line.
- Row labels in the draft's small spaced Montserrat: the label and value groups are separate flow groups, one font per group changes its pitch; not done.
- Death panel: colours only (KilledBy coral from the colour step); the death-camera element `ZFADeathCamDisplay` is not read and not touched. The pre-round / death panels' fonts are the level's.
- The stock player-name on the leaderboard row (`R6KXO`) stays the profile name.

## 5. Builds (RAN; nothing installed)

| What | Where | Result |
|---|---|---|
| ONE level, DM03, level bake + board step | `<work>\build\hud_x8\DM03\F03_Main.zip` (168,869,142 B, sha1 d5d591e5), from `hud_tab\DM03\F03_Main.zip` by `kl_hud_menu.py level` | `check-level` PASS 0 fails 0 notes: only `.TEX` (22 textures, same ids / sizes) and `Menu/online.xml` differ, table identical (1889 tags). The other six maps are NOT rebuilt: each needs `kl_hud_menu.py level <hud_tab\<id>> <out>` (about 1 min and 170-210 MB each) |
| Menu overlay pair | `<work>\build\hud_menu4\Overlay` (Patch01.zip feeb24bd, Scenes\kaneandlynch.zip ff39ccb4), made from the INSTALLED pair (270be320 / a39517e0) | `check` against the installed pair PASS 0 / 0. Byte-identical to `hud_menu3`: the menu itself has no round-over page, so this track changed nothing there |
| Hooks | `<work>\build\klhook\hud_v24_test\dinput8.dll` (4e05e5c1), `hud_v24_ship\dinput8.dll` (f3b73cf8); source = `git archive HEAD klhook` + the working tree's klhud*.c / klhook.c, scratch `G:\kl_scratch\hud_v24` | compiles TEST and SHIP, no new warning (the klhud_weapon.c unused-variable warnings are older) |
| Preview | `<work>\build\hud_menu4\board_preview.png` | see 6 |

## 6. Preview (what it is and is not)

`board_preview.png` is a LAYOUT reconstruction (script `G:\kl_scratch\hb\preview.py`, Pillow + Anton): rows, columns, bars and colours from the XML
numbers and the calibration of the screenshot G2_DM03_tags_184s (1280 x 720 virtual). Top = the page as the game drew it (pitch 38: the
ROUND SCORE / TOTAL row overprint reproduced), bottom = after the fix. It is NOT the game's renderer: no brush bars (the bars are flat chalk), no
.LOC strings other than the screenshot's, no baseline of the real glyph records. Not previewable: the pre-round plate (a hook effect), the
real chalk bars and lines (the repaint is in `hud_menu3\sheet.png`'s form), the death page.

## 7. Risks

1. Pitch guess (section 2). 2. `GeomSpace` is read as an attribute of the template: that an element's / template's attribute wins is an assumption of the whole tool. 3. Coral labels on the page: `Header` is coral in the restyled colour sets only; on an archive that went through `level` (it did). 4. `klhud_board.c`: plate object colour (does SetColour change what its Draw paints: yes for the escape plate, class equal; not seen here), alpha-byte handling, shadow test by darkness, `klu_r.osd` before 0x19. Fault class: a wrapped slot-2 only, no .text patch, every read guarded; off by default. 5. Deleting nothing: the hud_x8 archive is a test archive only.

## 8. Live checks (owner away; the game folder is not touched by this note)

Common: game closed first; pictures every 2 s; log `<DD>\KLHook.log`.
- **B1 (die -> death panel -> round-over page)**: put `hud_x8\DM03\F03_Main.zip` over the tab's DM03 archive for ONE run (the installed one = `hud_tab`-bake or `w_tabC7` copy, byte-identical to its tree; back it up first); hook `hud_v25_test`, ini `[HUD] Enable=1 Draft=1 Log=2`, `[Fed] Player=0` (a fed round shows other pages). Die early. PICTURES MUST SHOW: `YOU ARE DEAD` header, `Killed by` line coral; then the page: rows one line apart (about 32 virtual px: TOTAL row clearly above ROUND SCORE, no overprint), labels TOTAL / ROUND SCORE / TOTAL SCORE coral, values green, bars chalk with ink headings.
- **B2 (escape -> round-over page)**: same set-up, escape with the crew. Same page; `ESCAPE / ESCAPED ALLIES / LOOT / TIME BONUS` values green, `YELLOW CARDS / CIVILIAN KILLS` coral, `TRAITOR` orange (when non-zero); POS / NAME row on the faint chalk bar; BUY WEAPONS / READY then Buy weapons page opens (no fault: the table is unchanged); second round starts.
- **B3 (pre-round panel)**: hook `hud_v25_test`, `[HUD] Enable=1 Draft=1 Log=2 Board=1`; the owner's tab maps are expansion levels, so `klu_r.osd` is set there (states 0x16-0x19); on a genuinely stock level the part does nothing unless `[HUD] Stock=1`. At the countdown: log `hud: board: on` at start, then `hud: board: element ... now renders through the private vtable`; the plate ink-dark (or unchanged = the colour is not honoured: set `BoardInk=0`), letters chalk, `HEIST STARTS IN n SEC` readable on the bright square, no fault; `hud: board: N intro calls, M restyled` every 5 s while the panel shows. If no 'element' line appears the OSD is not known before 0x19 (risk 4): then the part is useless as built.
Pass = no fault in all three; a failure of B3 alone does not block B1 / B2.

## 9. Install and back out

Install (game closed, owner not playing): for each map `python tools\kl_hud_menu.py level <work>\build\hud_tab\<id> <work>\build\hud_x8\<id>` then `check-level <new zip> <hud_tab zip>`, copy ONLY `<slot>_Main.zip` over `<DD>\KLExpansion\Maps\<id>\`. Hook: `hud_v25_ship` as `<DD>\dinput8.dll` after copying the old one aside; `[HUD] Board=1` only after B3. Menu pair: unchanged (hud_menu3 / hud_menu4 are the same bytes).
Back out: copy the old archive back (`hud_tab\<id>` or `w_tabC7\KLExpansion\Maps\<id>`), the old dinput8.dll; `Board=0`.

## 10. Review round (2026-10-12; OFFLINE, nothing run)

Verdict ACCEPT WITH FIXES, no MUST. Findings -> outcome:
1. SHOULD 1 `FAWaitForOtherPlayersMenu` also moves (18 uses of the template): CONSIDERED, KEPT. That page uses the same `Text` font and was drawn for pitch 32 like the
   four board windows, so pitch 32 returns it to its design. Restricting to the board windows means dropping `Template=` from their groups, and `signature()` /
   `check-level` count the template name per element (instancing may add table entries): the try made check-level FAIL ('TABLE SHIFT'), so it was reverted. LOOK at that
   page in B1 / B2 (it shows while a round waits for others); if it is wrong, give its groups an explicit `GeomSpace="16"` instead (Template kept).
2. SHOULD 2 B3's note: reworded in section 8 (expansion levels engage; stock levels need `Stock=1`).
3. SHOULD 3 restore hazard: DONE in `klhud_board.c`: after the stock call only the RGB bytes are put back, the alpha byte is whatever the stock Render left.
4. SHOULD 4 thread / lock: no change; noted in the file header (if B3 faults, look at `klbrd_render` first).
5. SHOULD 5 pitch: no change; B1 must MEASURE the row pitch (expect 32 +-1 virtual px, about 50 display px in G2_DM03_tags_184s's scale of 1.57; compare V2_DM03_draft_125s's rows).
Rebuilt: level archive `hud_x8\DM03\F03_Main.zip` regenerated (same bytes, sha1 d5d591e5; check-level PASS, table identical at 1889). Menu pair `hud_menu4\Overlay`
unchanged (`board_page` is level-only; check against the installed pair PASS 0 / 0; Patch01.zip feeb24bd, kaneandlynch.zip ff39ccb4); the preview is unchanged for the same reason.
Hooks `<work>uild\klhook\hud_v25_test` (96b5fefa) / `hud_v25_ship` (11898237) from `git archive HEAD klhook` + working klhud*.c (klhud_board.c is untracked: copied) + klhook.c in
`G:\kl_scratch\hud_v25`; TEST and SHIP compile, only the old klhud_weapon.c C4101 warnings.
