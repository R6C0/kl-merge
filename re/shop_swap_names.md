# Swapped shop rows that look like the gun they hand over (2026-10-20; static reading + offline bake; NOTHING RUN IN THE GAME)

Context: `klhook/klshop.c` ([Shop] Enable=1, Swap=row:item) makes a bought shop row hand over a different gun (re/shop_more_guns.md). The shop kept
showing the carrier row's name and picture. This note covers the declaration of swaps, the name / picture bake, the price limit and a default set.

## 1. Where a map declares its swaps (hook and tools agree)
`KLGuns.ini` beside the level archive, new section:

    [Shop]
    Swap=13:52,16:33,32:49,35:47

- `klshop_level_open(key, opened)` (klshop.c) is called from `klh_level_open` (klsteam.c, after `klg_level_open`) for every level archive the game opens.
  It reads `[Shop] Swap` from the KLGuns.ini beside the opened archive. The parse is the old one (row 0..35, item 1..63, one swap per row, at most 8).
- No `[Shop] Swap` line = the default, KLHook.ini `[Shop] Swap` (old behaviour, nothing changes for existing setups). An empty `Swap=` = no swap on that map.
  The module is still off unless `[Shop] Enable=1` (it no longer switches itself off for an empty default list, because a map may bring its own).
- The set reaches the game thread through a staging copy and a generation counter (spin lock, no init): the tick adopts it, forgets the previous
  map's state (applied flags, made objects) and re-applies when the pool is built. Same gates as before: Arcade, ZGameRulesHeist, kl_online()==0, state < 0x19,
  code-byte check. No code byte or hashed byte is written (data writes only), as before.
- The bake tools read the SAME line (`kl_hud_shop.read_swaps`: file first, else the default text), so the baked names match what the hook hands over.
- Build compile check: `cmd /c klhook\build.bat C:\kl_build_1019\shopnames_build` -> `built ... dinput8.dll (SHIP)`, no warnings seen.
- Caveats (CERTAIN, read in the repo): `kl_map_guns.py` / `kl_guns.write_ini` REGENERATE KLGuns.ini and drop `[Shop]` (run `kl_shop_swap.py set` again after a rebuild);
  `kl_buildprint.py` hashes KLGuns.ini with comments stripped, so a `[Shop]` line changes that map's build code. Online the shop is inert (kl_online gate) and
  the baked LOC / TEX differ from other players' copy of the map like any map change: every player needs the identical build (re/netcode.md).

## 2. What is baked (tools/kl_shop_swap.py, tools/kl_hud_shop.py)
Names / descriptions (CERTAIN mechanism, same as the existing shop-name bake): the .LOC leaves `AllLevels/Menu/Online/WeaponShop/Weapon<row>` and `...<row>Desc`.
- Item names are NOT in any .LOC (the shop strings are per ROW), so the name is the HUD wording of `klhud_weapon.c klwd_names`: TYPE 81, MINIMI, REM 700, RPG-7, HK69 (CERTAIN: our own capitals).
  `TYPE 88 MG` (item 40) is a GUESS: the HUD has no name and no picture for item 40.
- Descriptions are NEW flavour text in the shop's "Police reg." manner (GUESS, invented numbers and origin lines; origin = the real gun's country), ending
  "Sold in the <carrier> row: same price, same rank." (honest about the price, see section 3). English only; other languages get the name and keep their description.
- A swap beats a Dead Men look on the same carrier row. Idempotent (a second pass changes nothing; the stock-name check accepts swap names).
- The picture question (CERTAIN, read on DM01): the row's pictures are `FAStatus_WeaponBig#NN` (DXT1 512x256, 445x210 shown) and `FAStatus_WeaponNN#01..04` (DXT5 128x128,
  one texture for the four copies), NN from Menu/online.xml: row 0-5 -> row+1, row 6 -> 36, rows 7-35 -> row. Texture ids are found per archive from the scene (ZWINPIC entity ->
  .prm sprite chunk -> texture id), every id belongs to that picture alone, no material uses it (checked in code, as in the stage-2a cards). The HUD dial's
  pictures `UI_Weapon_01#<name>` (128x128) are separate and chosen by item id, so they already show the handed gun.
- The bake paints the card from the level's own HUD silhouette of the handed gun (`UI_Weapon_01#Rifle_Type81`, `MG_MiniMi_SPW`, `Sn_Rem700`, `RPG_7V`, `Launcher_HK69A1`; all present
  in DM01's .TEX): chalk-on-ink like the stage-2a cards (ink ground, light top / hatched shadow side, dry-brush edge, chalk underline), the small icon as a chalk silhouette in the
  stock icon's own box. Pixels are spliced over the old pixel bytes in the same format and size, so every other byte of the .TEX is identical; every zip member but the .TEX and
  the 8 language .LOC is copied byte for byte (`rezip_raw_multi`, verified member by member). Item 40 has no HUD silhouette: the picture stays the carrier's and the report says so.
  The look of the card is judged by the preview PNGs only (not seen in the game). It is a flat 2D silhouette, not a shaded 3D render (GUESS that this reads well in the shop).

## 3. The price (CERTAIN)
Price, rank (stars), tier, the lock and the DLC gate come from the shop table at 0xbd1f68 (36 x 24 bytes, hashed .rdata, re/antitamper.md): the price check of the server
(0x6a5260) and the menu index it by ROW. A swapped row therefore costs what its CARRIER costs; no hook may write the table. To price a gun sensibly pick the carrier by price
(`python tools/kl_shop_extra.py rows`; `kl_shop_swap.py parse "<line>"` prints the carrier's price and rank next to each pair). A swapped gun also needs the carrier's
rank and is hidden/locked like the carrier.

## 4. Default swap line (proposal) and why
`Swap=13:52,16:33,32:49,35:47`

| row | carrier (price, rank) | hands over | why |
|---|---|---|---|
| 13 | Hawk Police (68,000, 4) | 52 HK69 grenade launcher | a near-duplicate shotgun row; a launcher at a mid price; 35 handling clips in the sets |
| 16 | Hawk Bullpup (200,000, 7) | 33 Type 81 | a near-duplicate shotgun row; Type 81 has the most clips (50, as many as the AK-47) = lowest handling risk |
| 32 | Type 88 Scope (210,000, 4) | 49 Rem 700 sniper | the scoped Type 88 is the least-missed rifle row; a sniper rifle at a sniper-ish price; 34 clips |
| 35 | Type 95 Scope (245,000, 6) | 47 Minimi | same reasoning; the most expensive row suits the heaviest gun; 35 clips |

No duplicate items (each item is bound once per level); none of the rows is 29 / 30 (AkChance's fed rifle uses items 31 / 32 = rows 29 / 30, so those carriers are avoided).
Riskier extras (not in the default): `14:50` (RPG-7 on the Spas-12, 29 clips; rocket + explosions untested), `28:40` (Type 88 MG on the Zastava row, 46 clips, but no picture: only
the name changes, so the card would show the Zastava). Items 40 and 47..52 also need a template in the level: `kl_shop_extra.py check <build>`; a missing one makes klshop skip the pair
and log it (the baked name would then be wrong: bake only pairs the check accepts).
The earlier proposal in the working notes used 16:40; it was replaced by 16:33 because item 40 has no picture and Type 81 has more handling clips.

Handling-clip risk (GUESS until run): the criminal and NPC animation sets must carry clips for the handed gun, else T-pose / broken arms. Counts of handling clips per gun folder found
in those sets (read in the DM01 build, tools probe 2026-10-20): Type 81 50, Type 88 MG 46, Minimi 35, Rem 700 34, RPG 29, HK69 35 (AK-47 = 50 for scale). Nothing says that a clip count
is sufficient; one Arcade round with each handed gun is the test (shoot, reload, pick up ammo).

## 5. Interactions and open questions
- Bots: a bot's loadout reads the same pool / rows, so a bot buying a swapped row probably gets the handed gun (GUESS, not read); watch the first round.
- `[Inv] Enable` (klinv.c gun shelf) is independent: it shelves the gun not in hand; a swapped gun is a normal gun for it (GUESS).
- Online: untouched (kl_online() gate). The baked names / pictures are visible online but the swap is not applied, so an online match on a baked map would show
  names that do not match what is handed over. Use the baked archive for Arcade only, or leave the swaps unbaked online (a build with swaps is a different build).
- Stock FA maps (the 9 stock maps): the hook path works for them too (no KLGuns.ini there = the KLHook.ini default), but the bake targets expansion maps with an
  installed archive; baking a stock archive would mean replacing a stock file, which the project rules forbid, so stock maps get the hook swap with the carrier's name and picture.
  (Do NOT edit KL_PortBackup or stock files; use a KLExpansion map copy.)

## 6. Staged build (nothing installed)
`C:\kl_build_1019\shopnames\`: `DM01\F01_Main.zip`, `DM01\KLGuns.ini` (only gains the `[Shop]` section), `DM01\card_row*_item*.png` previews, `manifest.json`,
`shopswap.ps1`, `INSTALL shopswap.bat`, `UNDO shopswap.bat`. Regenerate with `python tools\kl_shop_swap.py stage C:\kl_build_1019\shopnames` (deterministic: same md5 twice).
- F01_Main.zip 94dc052b -> 19214258 (changed members: .TEX + 8 .LOC; the zip is smaller only because the changed members were re-deflated at level 6)
- KLGuns.ini 7e233a3b -> 907ffabf
- The install script follows noblow.ps1: refuses while a kl2.exe WITH THREADS runs (a zombie with 0 threads is ignored), md5 of live and source, the live file is renamed to
  `*.before-shopswap`, read-back, `-Undo`, `-DryRun` (a dry run only warns when the game runs). Run: `-DryRun` and `-Undo -DryRun` were run (2026-10-20 00:15, game running: warning only), nothing changed.
- To make the rows hand over the guns the hook needs the 1019d (or later) KLHook with this change and `[Shop] Enable=1` in KLHook.ini (the install does not touch KLHook.ini or dinput8.dll).
  Without the new hook the names would be wrong (the old hook only knows KLHook.ini's Swap): install the hook and the bake together, or `-Undo`.

## CERTAIN / GUESS summary
CERTAIN: declaration route and parse; pool mechanism (older note); row -> picture mapping and texture ids on DM01; formats and sizes; .TEX / zip byte-identity outside the changed members;
price/rank/lock follow the carrier row; HUD names; build compiles.
GUESS: handling clips suffice; invented descriptions and "TYPE 88 MG"; how the flat chalk silhouette looks in the game; bot behaviour; that the carrier row's rank gate is acceptable;
nothing ran in the game.
