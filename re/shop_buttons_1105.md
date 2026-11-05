# Shop buttons on the round-over page (2026-11-05)

Owner: "a button next to Buy Weapons ... sends you to page 2 and heister upgrade". Tool: `tools/kl_shop_buttons.py` (test: `tools/kl_shop_buttons_test.py`).

## What it bakes (Menu/online.xml of each map zip)
Status windows `HeistStatus`, `HeistStatusLeaderboard`, their `_EndGame` twins, `FAStatus`, `FAStatus_Team` (the ones with a Buy Weapons legend; the
FA round-over page may be either family, so both are covered). Weapon-shop windows (`FABuyWeapon*`, receiver FABuyWeaponToggler) are NOT touched.
- PC_KEYBOARD legend: after the Buy Weapons line, two `TextBlock` legend entries `[F2] More guns`, `[F3] Heisters` (GenericButtonPos_GT, ColorSet Legend, AlignH Right). No input element: the keys already work through the hook ([ShopPage] PageQueue / AutoOpen).
- PC_GC (mouse) frame, only where it has a Buy Weapons focus bar: two text-only W151 H40 groups left of the leftmost stock group (step 218). Not clickable.
- No ButtonGraphic (no F-key glyph; plain key names baked: `--more-key`, `--hire-key`, default F2 / F3, GUESS: the hook's keys are rebindable, the text is not).

## Table cost
Counter (Arcade context = keyboard platform): +12 per map (2765 -> 2777 stock; DM01 2768 -> 2780), worst case +28 with the PC_GC frames. Cap 5000 checked, over = not baked.

## Proven offline
Synthetic test (insertion, line endings kept, other windows untouched, idempotent, key text); real F05 zip: diff read, only insertions; `stage` ran for the 9 stock + 11 KLExpansion maps (all baked, +12).
## GUESS (needs a live look)
- A TextBlock between right-aligned legend entries flows like the Buy Weapons line (position / overlap, "Ready" is first).
- `%` literal text works in a legend TextBlock (it does in the hire window headline).
- PC_GC groups at X 437/219 (Heist) or 219/1 (FAStatus) are on screen and do not overlap.
- Mouse click: not done. BottomFrameButtons is engine laid out, the rectangle is not in the XML; follow-up = hook mouse poll with a rectangle measured from a screenshot ([ShopPage] ButtonClick).
- No `[ShopPage] ButtonsHint` key: ScoreboardNextHint text unchanged.

## Live recipe
Install, start Arcade (any map), finish a round, on the round-over page read the bottom line: Ready, Buy Weapons, `[F2] More guns`, `[F3] Heisters`. Press F2 / F3 as before (PageQueue/AutoOpen on). Then online host and client, one DM map. Grep nothing new in KLHook.log; a menu table overflow would show as a crash on load.

## Install
`<work>\build\shop_buttons\INSTALL shop buttons.bat` (owner runs it with the game closed): moves each live `<map>_Main.zip` to `*.before-shopbuttons` and writes the baked zip in its place; re-bakes from the live zip. `UNDO shop buttons.bat` moves them back. Never touches KL_PortBackup.
