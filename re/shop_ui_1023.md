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
