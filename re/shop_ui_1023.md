# Weapon shop cards, one clean style (2026-10-23, track shop; OFFLINE, not run in the game)

Tool: `tools/kl_shop_cards.py` (PIL + numpy only). Output of the staging run: `C:\kl_build_1019\shop_1023\` (never inside the game folder).

## What changed on screen
All 36 big cards (`FAStatus_WeaponBig#NN`, DXT1 512x256, 445x210 shown), their 36 small icons (`FAStatus_WeaponNN#01..04`, DXT5 128x128) and the
star / lock glyphs (`WeaponShopStar`, `WeaponShopLock`, DXT5 32x32) are repainted into one look:
- the stock 3D gun photograph is CUT OUT (the light table, tags, pens, notes go) and put on one dark vertical gradient, in the same frame and
  scale on every card (box 24,20 - 421,172), with a 2 px chalk-white outline, a soft contact shadow, one faint chalk hairline inset and a short chalk
  underline;
- small icons: the same cut-out, lit like a stock icon, chalk outline, transparent ground, in the stock icon band (y 38..86, left anchored);
- the 4 swapped rows (13, 16, 32, 35 -> items 52, 33, 49, 47) show the HUD silhouette of the handed-over gun (kl_shop_swap.PIC_OF_ITEM) shaded as
  metal, much larger than before (up to 4x, the HUD silhouette is 128 px);
- flat chalk cards that older bakes left on some Dead Men maps (DM01: 10 rows) are re-cut from their silhouette and shaded the same way.
- star / lock are drawn procedurally (crisp white, 1 px dark halo).
Same texture ids, sizes and formats; price, rank, stars, locks and row count are hashed and unchanged. Tiles shared with another entity are skipped
(`shop_tiles()['skipped']`), none were found on any map.

## Known imperfections (honest list)
- The cut-out is a statistical segmentation of a lit photograph, not a render. On some stock cards (DD01 rows 11, 12, 13, 15, 24, 31, 33) a grey
  patch of the table is kept as part of the gun; a few cards keep a tag or a wire. It is a finished-looking card, not a perfect one.
  Better source art would be a render of the .prm model (not attempted).
- Flat silhouettes (swapped rows, DM01's old chalk rows) are crude blocks: that is all the source has.

## Idempotency
The unseen padding of every restyled big card (bottom-right 32x12, which is outside the 445x210 shown) carries two exactly-encodable 16x12 colour
patches: tool version and item key. A card carrying them for the same item is kept as is, so a second run changes 0 bytes (asserted in
`bake_map`). A card restyled for item A cannot be re-baked for item B or for none: the stock art is gone, the tool says so; start from an archive
from before (the installer keeps `.before-1023shop`).

## Stat line (step 2): NOT done
`re/shop_plan.md` 2c wants damage / fire rate / magazine read from the weapon templates. Those fields are not established, so no number goes into
a description. (Names and descriptions of the swapped rows are the existing kl_hud_shop SWAP_ITEMS ones.)

## Staging
`python tools/kl_shop_cards.py stage C:\kl_build_1019\shop_1023 [--maps=DM01,DD01] [--swap=13:52,...]`
per map: swaps = the map's own KLGuns.ini `[Shop] Swap` if it has one, else the default line (klshop.c's order); only `.TEX` and the `.LOC` members
change; every other member is copied byte for byte and the tool asserts, member by member (CRC + size), that exactly the changed members differ,
that the member list is unchanged, that a second pass is a no-op and that no shop tile is blank. `manifest.json` has the numbers.
Also written: `KLHook.shop.patch.ini` ([Shop] Enable=1, Swap, ReserveClips=2; merge by hand), `shop1023.ps1`, `INSTALL shop 1023.bat`,
`UNDO shop 1023.bat` (backup suffix `.before-1023shop`, md5 checked, refuses while kl2.exe runs, -Undo, -DryRun).

## Regression
`tools/kl_hud_menu.py check-level` now also runs `kl_shop_cards.blank_tiles` on archives whose source has a healthy shop page (36 + 36 tiles, star,
lock found and non-uniform), and no longer calls a changed DXT1 texture "unreadable" (size and format are still compared).
`python tools/kl_shop_cards.py check <archive>` runs the same test alone.

## v2 cut-out (2026-10-23, MARK_VERSION 2)
`cut_photo` no longer uses a window-percentile background. A ridge-regularised degree-4 polynomial `table_model` is fitted to the UPPER envelope of
the card luminance (lit table plus vignette); d = table minus pixel. Gun evidence = very dark (d > 85, or under half the table where the vignette is
dark) or coloured (tan, cyan, orange: chroma plus darker than the table, vetoed on paper = regions BRIGHTER than the table). That core is opened by
2 px (print, red ink and wires are 2-4 px strokes), blurred into a density, reconstructed, closed by 7 px, small pockets filled (big ones only when
clearly dark), then the largest blob plus solid neighbours only (`_keep_gun2`). Tag and note text, the table patches and the vignette corners are gone
on rows 12, 15, 19, 24, 26, 31 and the small tag remnants. Remaining: cable loops stay on a few rows (11, 16, 17, 20, 28), row 10 loses the silver
cylinder (as bright as the table), row 33 loses a rail sliver, rows 15, 19, 21, 23 keep a small box or note corner, the photo halo is partly kept.
`marked()` is version aware: a v1 card counts as stale; a v1 photo row can still not be re-cut from its own restyled art (guard kept, 32 refused on
the installed DD01), swapped rows are re-baked from the HUD silhouette. `python tools/kl_shop_cards.py recut <installed map dir> <outdir>` re-cuts
from `<zip>.before-1023shop` and replaces ONLY the big card and small icon tiles of the INSTALLED .TEX (everything else byte identical, asserted per
member and per texture). Staged and previewed for DD01 and DM01 under `<work>\build\shopcut2_1023`; not installed.

## 2026-10-24: WHITE style (MARK_VERSION 3, `STYLE='white'`), staged not installed
Owner: "shop looks decent, just needs to be white like the M4 and the USP were originally, they dont all match up now ... redesign it with the Dead
Men feel". The v2 photo cut-outs are gone from the default path; every row is now ONE style:
- Gun = a white flat silhouette rendered from the gun's own weapon MODEL (side view, `kl_view.View`, 1200 px, 2x supersampled, cached as
  `<work>\build\shopwhite_1024\sil\<template>.png`, RGBA: grey = flat shade 80..100 %, alpha = anti-aliased coverage). `python tools/kl_shop_cards.py
  render [outdir]` makes them (about 1 min; reads the stock DD F01 level and M01_FA_A only). Fallback when a png is missing: the 128 px HUD
  silhouette (`UI_Weapon_01#<name>`, soft when enlarged, reported as `hud ...` in the row report).
- The picture follows the gun you actually hold: the map's `KLGuns.ini` Shown look decides (`read_shown`): DM01 and DD01 both show MP5 (Zastava row 28),
  SG 552 (SCAR 33), M4A1 (AK-47 29), P90 (Type05 22), Steyr TMP (MAC-10 18), USP (M9 2); rows 13/16/32/35 show the swapped-in HK69, Type81, Rem700, Minimi.
  The Dead Men look models are rendered via `kl_chars.Source.get('M01_FA_A')` (png names `dm_<template>`).
- Ground = Dead Men menu look from the research: near-black blue-grey gradient, low-frequency smudges, dirty dark edges, a few paper specks, ONE 1 px
  steel-blue hairline frame (130,158,193 at 50 %), a thin broken ring behind the gun (the WeaponSelect ring), a small dirty-red corner bracket (the header
  splat), a faint steel bloom round the white. No outline, no photo, no chalk hatching, no underline. Same box (BIG_BOX) on every card.
- Small icons: the same white shape, transparent ground, 1 px dark halo (reads on light bars), left anchored in the stock band. Star / lock unchanged
  (already crisp white with a halo).
- Idempotent: the v3 mark (version + item) in the unseen corner; v1/v2 cards count as stale and are simply repainted (the white style needs NO art from the
  old card, so the "cannot re-bake a restyled card" guard no longer applies to it). Same texture ids, sizes, formats. `bake_map` still asserts second pass = 0 bytes.
  The mark does not include the map's look, so after changing a map's KLGuns.ini Shown line, restage from an archive that is not v3.
- Install scripts: backup suffix `.before-1024white`, `shop1024white.ps1`, `INSTALL shop 1024 white.bat`, `UNDO shop 1024 white.bat` (written by `stage`).
Known imperfections: the model renders carry a few stray model parts (DM01/DD01 row 20 MPi69 keeps its sling cable loop, row 11 sawn-off a thin dangling
line, row 2 USP a ragged lower edge of the grip); the shade only hints at detail (trigger guard, magazine well) since the silhouette is flat white; rows 11,
15, 21 etc. look fine but pistols fill the box by height so they are smaller than rifles (same box, not same scale: the models have no common unit here).
The Dead Men red/orange accents are minimal on purpose (the game draws text/price on top, position of those not measured).
