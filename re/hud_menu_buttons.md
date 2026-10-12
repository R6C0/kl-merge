# BUY WEAPONS / READY (the page after the scoreboard) as the draft's painted-bar buttons - PLAN for tools/kl_hud_menu.py (cloud session, 2026-10-12)

No code. Nothing built or run, and the level XML was not available here (game files are never in the repo): every element name below
that is not in re/hud_menu.md or re/hud_board.md is a GUESS to be confirmed against `Menu/online.xml` of a baked level archive locally.

## 1. Where the buttons are and what limits any change (from re/)

- The page = state 0x20, XML window `HeistStatusLeaderboard` / `HeistStatus` (and the two `_EndGame` twins) in the LEVEL archive's
  `Menu/online.xml`; Ready / Buy weapons input = `MercsFAStatusReady` (vtable 0xbbd84c, input 0x7557f0), which opens `FABuyWeaponsNew`
  by code (0x7558ce) (re/hud_menu.md 1.3). The bottom legend in the stock picture reads 'Select / Back / Ready' in the `Button` font
  (kl_hud_menu.py's preview list, line ~1189).
- **The table rule** (re/hud_menu.md 1.1 and the tool's TABLE docstring): every `<Window>`, created `<GuiElement>`, `<ColorSet>`,
  `<ButtonGraphic>` takes the next slot of ONE table of 5,096 pairs; the hot index is 5,000 (`DefaultFocus`, the mouse path 0x861720
  calls `vt+0x84` on table[5000] with no kind test -> the 2026-10-10 14:24 crash when entry 5000 was a Window; and the 2026-10-12 page-3
  overlay that ran past the table: bare int3 at 0x7fad8d). The LIVE counts are still unknown (K0 never ran). So: **attribute values
  and new attributes only; no new tag of the four kinds; `check-level` must report the table identical** ('TABLE SHIFT' = refused).
- What attributes can do (re/hud_menu.md 1.2): ColorSet= (existing sets), Font= (the scene's eight), X / Y / W / H / Align*, fades,
  AlphaMin / AlphaMax, `Graphic="N"` naming an entity that is already loaded. A picture's LOOK is the .TEX (`repaint`).
- Already done by `level` today: every `FocusBar_*` / `MenuFocus_*` tile of the level's .TEX repainted as a solid chalk brush stroke
  (kit painter), lines dry-brush, colour sets in the draft's tokens - EXCEPT `FocusBar_medium_02` (grooved), `MenuFocus_long` and
  `FAFocusBar_long` (shared DXT1 tiles), which are left stock.

## 2. Step 0 (local, static, ten minutes): read what the two buttons are

In a baked level's `Menu/online.xml`, for each of the four `HeistStatus*` windows, list the element(s) that carry the Ready and Buy weapons
texts (their .LOC keys under `AllLevels/Menu/...`), with: tag, Name, Template (and the template's attributes), Font, ColorSet,
`Graphic` / `FocusGraphic` / `ButtonGraphic` and which bar entity / tile those name, AlphaMin / AlphaMax, X / Y / W / H. A
`kl_hud_menu.py buttons <archive>` sub-command that only PRINTS this (read-only, like `diff`) is the right tool for it.
Three cases follow, decided by that list:

| case | what step 0 shows | route |
|---|---|---|
| A | the buttons are elements with a focus bar that `level` already repaints | only colours / font / alpha: section 3 |
| B | their bar is one of the three left-alone families (`FocusBar_medium_02`, `MenuFocus_long`, `FAFocusBar_long`) | repaint THAT family in the LEVEL archive only (section 4) |
| C | the 'buttons' are the legend (key glyph + word) drawn by `ButtonGraphic` / legend code with NO bar element | no bar is possible without a new element (table shift): colours / font only, and the painted bar waits for K0 (section 6) |

## 3. Case A: attribute-only restyle (proposed `level --buttons`, default OFF until M3-B)

A new function `board_buttons(xml, member, log)` in the `level` path, after `board_page()`:
- focused: the existing chalk brush bar (repainted tile), text INK - by pointing `ColorSet=` at the existing set whose FocusColor is ink
  (the 'Bonus' / 'Penalty' headings' set `OnFocus`, re/hud_menu.md 2) - no new set.
- not focused: the draft shows every button as a bar; XML can only show the SAME focus bar at a lower alpha if the element already has a
  normal-state `Graphic`. If it has: `AlphaMin` -> about 48 (a faint chalk bar), text chalk. If it has only a `FocusGraphic`: leave the
  unfocused state as text only (adding `Graphic=` is an attribute, but whether the loader then CREATES a picture element - a table entry -
  is NOT established; do not add it before K0).
- font: `Font="Button"` stays (the level bake's Button face = Anton capitals); letter-spacing cannot be set in XML.
- size / place: W / H of the bar to the draft's proportion (bar about text + 2 x 24 px, 34 px high at 1280 x 720 - the pop-up bar's
  constants, re/hud_hook.md 11.2) ONLY if the element's W / H are attributes it already has; otherwise leave.
- `check-level` gains a rule: with `--buttons`, the ONLY attribute names that may change on those elements are ColorSet, AlphaMin,
  AlphaMax, W, H, X, Y; any other difference = FAIL. The table test stays as it is.

## 4. Case B: repaint a left-alone bar family in the level archive

`repaint()` skips `FocusBar_medium_02` because of its drawn groove and the two DXT1 families because their tiles are shared. In a LEVEL
archive the menu pages are few (the status pages, shop, pause, death), so the sharing argument is narrower there:
- `picture_uses(z, stem)` already lists every entity that uses a tile; if, inside the level, the family's tiles are used only by the
  status / shop pages, repaint them with the kit painter (groove dropped: the draft has no 3-D bars). Same texture ids, sizes, format rule.
- If a tile is shared with something that must stay (a stock 3-D bar on the shop), leave it and fall back to case C's text-only form.
- Proposed flag `level --bars-all` (default off), reported by `diff` per tile.

## 5. What the hook could add (not planned)

The scoreboard part (klhud_board2.c) draws in state 0x1f only. Painting bars UNDER the XML buttons in 0x20 would need (1) the answer to
'does the HUD render in 0x20' (re/hud_board_b.md B-P1, open), (2) the buttons' screen places read from the XML elements, (3) input to
stay with the XML. Not proposed while the XML route is open.

## 6. Case C and anything that needs NEW elements

A bar behind the legend words, a frame around the page, painted skulls on the page: each is at least one new `<GuiElement>` (+ a picture
entity), i.e. a table shift. Order, unchanged from re/hud_menu.md 7: K0 (the hook's read-only `menu: table N of 5096` log line, NOT in
the committed klhook.c, re/hud_menu.md 11.5 item 6) -> the level's live count N -> `check-level --level-count N` proves N + new <= 5000
-> one live run with the mouse moved over the page AND its background for 30 s (the 0x861720 path). Never in the menu overlay
(`apply` refuses `--board` for that reason: an overlay's online.xml reaches every level).

## 7. Live checks (local, owner away; one archive over the tab's DM03 for one run, the old one put back after)

- M3-B (case A or B): die or escape -> scoreboard -> the page: READY / BUY WEAPONS on chalk brush bars, ink letters when focused, the
  unfocused one faint (if case A allows it); Buy weapons opens, the shop as before; second round starts. Move the mouse over the buttons
  and the page background for 30 s (the crash path of 14:24). Log: no assert; K0's line (once wired) shows the same count as before.
- Pass = no fault; the table count unchanged; the owner judges the look.
