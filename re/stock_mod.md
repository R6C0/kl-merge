# The nine stock Fragile Alliance maps with the mods (2026-10-10, kl-merge-b6)

Owner, 2026-10-10: "also want the original FA dog days maps to have these mods in the game too so its changed all
around makes it a bit more fresh". Tool: `tools/kl_stock_mod.py` (docstring = the spec). OFFLINE: built and checked,
never loaded in the game, nothing installed, no stock file touched.

## Result

`python tools/kl_stock_mod.py all` -> `G:/kl_scratch/stock_mod/<F01..F09>`: **RESULT: PASS**, nine of nine. Per map:
`kl_chars.py wardrobe <Fnn> --plates=wolf,dallas,chains,hoxton` problems 0, then `kl_map_guns.py build ... --no-audit`
problems 0 and `kl_map_guns.py check` on the written folder. Each folder holds the archive, the stock files beside
it, `KLWardrobe.ini` and `KLGuns.ini` (Version 2).

| map | .prm stock -> now (MB) | .TEX | .ANM | .fxc | .WAV | archive (MB) |
|---|---|---|---|---|---|---|
| F01 | 66.6 -> 86.3 | 288.4 -> 320.7 | 20.7 | 17.8 | 15.4 | 217 -> 292 |
| F02 | 64.7 -> 84.3 | 307.1 -> 339.5 | 20.3 | 17.8 | 17.0 | 196 -> 270 |
| F03 | 58.5 -> 78.1 | 354.5 -> 386.9 | 21.9 | 17.8 | 14.5 | 217 -> 294 |
| F04 | 64.5 -> 84.1 | 348.5 -> 380.9 | 21.6 | 17.8 | 21.2 | 235 -> 316 |
| F05 | 42.3 -> 61.9 | 296.3 -> 328.7 | 20.2 | 17.8 | 16.6 | 212 -> 282 |
| F06 | 67.4 -> 87.1 | 290.3 -> 322.7 | 19.8 | 17.8 | 22.2 | 210 -> 282 |
| F07 | 63.6 -> 83.2 | 281.0 -> 313.4 | 21.6 | 17.8 | 18.3 | 200 -> 273 |
| F08 | 64.0 -> 83.6 | 266.0 -> 298.4 | 20.3 | 17.8 | 14.6 | 169 -> 240 |
| F09 | 67.4 -> 87.1 | 285.8 -> 318.2 | 21.2 | 17.8 | 13.8 | 211 -> 285 |

## What a map gets
- The wardrobe: the eight Dead Men heisters as bodies, the eight Dog Days masks plus the four Payday 2 plates, the
  outfits. What the Heister page picks from. Seen live on stock F01 before (`<work>/build/pd2/pd2_F01`).
- The six Dead Men gun looks, baked (MP5 on the Zastava with an SMG's sound, SG 552, M4A1, P90, Steyr TMP, USP),
  fitted to the Dog Days hold. Police who carry one of those six guns show the look too.
- Nothing of the map itself: police, waves, loot, escape and AI heisters are stock's.

## What it does not get, and why
- Retomoto's soldier rows: stock's police ARE those rows (`kl_arms.ROWS` was copied from them).
- Fall-back chains, the elevator trigger, the straight van: authored object by object for Retomoto's street.
  `kl_map_ai.py` is keyed by Dead Men level names (its PLANS). Nothing generic was found for nine hand-made levels
  that would not be a guess per level. If the owner wants the police themselves changed on stock maps, that is a
  per-map authoring job (one map first).
- What else changes a stock round comes from the hook and needs no build: random crew bodies, bot tuning, talk.

## THE COST: the .prm block grows by about 20 MB
A stock level has almost no dead chunk indices to reuse (F01: 2 of 24,843), so the wardrobe's models go on top:
.prm 62..87 MB, larger than any build loaded so far (Retomoto 76..79 MB). The level's largest allocation is that
block (file size + 0x60000); it has failed before at 60..76 MB without the hook's reserve (crash kl2 0x8e5bbd). With
the reserve (128 MB, klmem.c) a 76 MB block was served every time; 87 MB has NOT been tried. .TEX grows by 32 MB.
First live check: F06 or F09 (87.1 MB), a second load in the same process. If it fails: `--armour=0` on the wardrobe
(fewer outfit variants) or fewer plates makes the .prm smaller.

## Delivery (not done; kl-merge-01's and the owner's call)
Each folder goes under `KLExpansion/Maps` with a `[Redirect] Fnn=<folder>` line: no stock file is replaced, and
without the line the game plays the stock map. The hook's Steam guard treats a redirected stock map as NOT stock:
rounds on it write no stats, no achievements and no leaderboard score. Online, every player needs the same build.
Nine folders take 2.5 GB.

## Not known
- Everything live: no folder of the nine was loaded (F01's wardrobe + plates alone was).
- Whether `kl_maps.audit` could be taught a stock level as its own base (it compares the sound bank with a grafted
  map's systems level and reports ten sound findings on a stock level; left out with `--no-audit`).
