# The Dog Days HUD as DATA (pictures and fonts) - 2026-10-11

Written by kl-merge (Fable) for the owner's HUD request ("merge the two UIs, gritty yet polished, for FA and
Arcade going forward"). Companion: `re/hud.md` (the draw CODE, by the hud_re agent) and the design draft
https://claude.ai/artifact/ARZVji4pNmpkFz5SFtyTL2 . Everything here was read from stock F07 (Dog Days)
and M01_FA_A (Dead Men) with the repo tools; nothing was run in the game.
Words: **established** = read in the files; **ASSUMPTION** = fits but not proven.

## 1. What the HUD is made of

Established:
- Two `ZOnScreenDisplay2` objects per level: `AllLevels/mainsceneincludes_multiplayer.zip/AllLevels/FFOsdMP1.zip/
  OnScreenDisplay` (field [5] = 0) and `OnScreenDisplay#01` ([5] = 1; coop border camera set). They have NO children.
  Stored fields: [0] ZCHAROBJ path, [1..4] four `ZTTFONT` paths (H1, H2, H3, DebugText), [5] int, [6] OSD camera,
  [7] a fixed array of **200 .TEX ids** (the HUD pictures, indexed by CODE), [8] subtitles camera, [9] coop camera.
- So layout, text, colours and which picture goes where are in kl2.exe. What is data: the 200 pictures and the fonts.
- The in-game MENU pages (pause, weapon shop, status) are XML (`re/menus.md`); not the HUD.

## 2. The 200 picture slots (F07; same ids 951..1109 in every stock FA level, checked F07 only)

Slot -> picture (name after `tex:UserInterface/...`). `-` = 0 (unused). Full list: scratch `hud/dd_tex/index.txt`,
contact sheet `hud/dd_sheet.png`; the exporter is `scratchpad hud/export_hud.py` (DXT1/3/5 + ABGR with alpha).

| slots | what | size |
|---|---|---|
| 0-1 | `_Test/Borders_01` Border, Red Border | 128x32 DXT3 |
| 2-34 | crosshairs (Empty, Gun, Rifle, MachineGun, Shotgun, Grenade, RocketLauncher + Shadow / Aim variants, GrenadeThrow, Heal, Command, Select, TransferLeft/Right) | 64x64 DXT5 |
| 35-56 | communication / marker icons (Ok, Merc_01..04, Attack, Target, Defend, Follow, Medic, Arrow, Coop, SniperWarning, Ammo, GroundPlane, Loot 128, Money 128, Rappel, Objective) | 64 / 128 |
| 57 | `UI_Icons_01#Icons_PS2` (button glyph sheet) | 256x128 DXT1 |
| 58-106 | weapon pictures `WeaponsPics/UI_Weapon_01#...` (49 guns, grenades, AmmoPickup, AmmoNoPickup) | 128x128 DXT5 |
| 107, 108 | `UI_KL2_Weapon_BG_01` Weapon_BG, Weapon_BG_L09 (the ammo panel plate: a plain grey rounded box with a slot line) | 256x128 DXT5 |
| 109, 193 | `UI_KL2_AmmoCount_01` (one magazine tick) | 32x32 DXT1 |
| 110 | Icons Arrow | 64 |
| 119-122 | CheckPoint, Objective, ObjectiveDone, ObjectiveFail | 64 |
| 127-160 | Sound, Reload, TakeCover, cover prompts (EnterCover, CoverStick*, CoverRush*, CoverLeft/Right, Vault, Exit*), canister icons, HitEnemy / KillEnemy (+Shotgun), Cover x6 | 64 |
| 161-164 | `UI_KL2_Tracker_01` GameplayTracker (4 bar frames) | 256x64 |
| 165-168 | `UI_KL2_Arrows_01` down / up / left / right | 32 |
| 169 | `UI_KL2_Meter_BG` | 256x64 |
| 170-172 | BoardingCar, BoardingChopper, Money (the escape marker icons) | 64 |
| 173-179 | `UI_KL2_Small_Icons_01` Escape, EscapeChopper, Money, YellowCard, YellowCardFollow, Kill, Star | 32 |
| 180 | `UI_KL2_FocusBars_01#Focusbar_Medium_06` | 1024x32 |
| 181-182 | `UI_White` (the plate fill the code tints) | 256x256 DXT1 |
| 183 | sniper laser; 184 E3 logo; 186-187 smoke trail; 188 blood droplets; 189 HitDirection; 191-192 lens flares | |
| 194-199 | Communications Throw x2, Door x4 | 128 |

Dead Men's M01_FA_A list (slots 0..106 used, different art, `hud/dm_sheet.png`): the same families plus what Dog
Days dropped: `UI_KL_MapSmall` / `MapBig` / `MapMask` (the RADAR, slots 79-85), `UI_Health_01` (86-87), `UI_KL_Recruit*`
(90-99), `UI_AmmoClip` (73-77), `UI_FA_Respawn_pip_mask` (106). The radar pictures are of no use without radar code.

Consequence: a restyle of the stock elements' ART (plates, ticks, icons, marker) is a .TEX record swap by id: same
id, any size that is a power of two (ASSUMPTION: the code draws a slot at a coded size, so the picture's aspect must
stay). `kl_graft.hud_textures` already keeps these ids alive through `lighten`.

## 3. Fonts: `ZTTFONT` = glyph atlas + record table (established, F07)

Eight `ZTTFONT` entities under `.../FFOsdMP1.zip/AllLevels/FFFonts.zip`: Button, Text, DebugText, Menu, Header, H3,
H2, H1. Each stores `ZWINOBJ[0..4]` (255, 8, ALIGNMENT_None, DRAWMODE_OPACITY, TYPE_Normal) and `ZTTFONT[0]` = one
.prm chunk index (F07: 33201..33208). The HUD names H1, H2, H3 and DebugText.

Chunk layout (33208 = H1, 15424 bytes; 33201 = Button, 13952), PROVEN by `kl_hud.py preview` drawing the stock
H1 from the records (scratch `hud/prev_stock_H1.png` reads "Total score: $3,400,000 Round: 1 05:14"):
```
header, 40 bytes: u32 1, u32 8, u32 pixel size (18 / 20 / 28), f32 1.0, u32 glyph count (359), u32 line height
  (20 / 22 / 31), u32 kerning pair count (302 / 487), u32 2, u32 3, i32 (-12 / -13 / -18: ascent offset)
then `glyph count` records of 32 bytes from offset 0x28:
  u32 char                Unicode code point (space first; Latin-1, Latin Ext, Greek, Cyrillic, punctuation, 0xe000.. private)
  u32 atlas ref           page 0: 4096 + .TEX id (5228 = 4096 + 1132 for H1); page 1: the bare id (1133)
  u16 x0, y0, x1, y1      rectangle on the page in 512-space (page 1 is 256 px: its rectangles are halved when drawn)
  i16 w, h                ink size (x1-x0, y1-y0)
  i16 xoff, yoff          ink box relative to the pen (yoff negative = above the baseline)
  u16 advance, u16 size   pen advance; the font's pixel size (31 for the 28 px font: the line height)
  u16 0, u16 0xcdcd       padding
then kerning pairs of 8 bytes {u16 a, u16 b, i32 adjust} x pair count (exact: 0x28 + 32 x 359 + 8 x 487 = 15424).
```
The 4096 bit on page 0 (white glyphs, tinted by the text colour) against the bare id on page 1 (coloured button /
skull / '$' pictures) is ASSUMED to mean 'tint'.
Atlas textures (F07 .TEX): `Fonts/FOUNMB__.ttf-<size>#<n>` = **Foundry Monoline Bold** at 18, 20 and 28 px, and
`Fonts/MorSCCB_.ttf-20` (Morris Sans? one font: Menu or Header). Each font has two pages: a 512x512 ABGR with flags
0x10002 (white RGB, alpha = coverage: `hud/font_1132.png`) and a 256x256 ABGR page (flags 0x2, coloured: not yet
understood - ASSUMPTION: an outline / shadow variant or an overflow page). Ids: 1111/1112 (18), 1114/1115 (20),
1117/1118 (MorSCCB 20), 1120/1121, 1123/1124 (28), 1126/1127, 1129/1130 (20), 1132/1133 (28).

Consequence: a new TYPEFACE for the HUD is data only. DONE in `tools/kl_hud.py` (`fonts <build> <out> --face
"Bahnschrift SemiCondensed" --weight 600`): GDI through ctypes rasterizes the 333 page-0 characters of every font at
its own pixel size, shelf-packs a 512 x 512 page (189 rows used at 28 px), rewrites the records (same chars, same
order, page-1 records and the kerning tail untouched), writes the atlas under the same .TEX id and the chunk under
the same index; `check` proves only the eight font chunks and their page-0 textures differ. `preview` draws a line
from the records (`hud/prev_bahn_H1.png`). The face is baked into the level: players need no font installed.
BUILT, NOT RUN: `<work>/build/hud_font/DM03` (the tab's bank, w_tabC DM03, with the new fonts: check PASS).
RISKS before a live look: the game may read kerning for pairs the new face spaces differently (small); a glyph
wider than its stock advance could touch its neighbour; ascent / line height header values are the stock ones.

## 4. How this reaches every FA / Arcade map

- Grafted Dead Men maps and Retomoto: `AllLevels/mainsceneincludes_multiplayer.zip` comes from the F07 systems
  copy in `kl_graft.build`; a `kl_hud.apply(build_dir)` step after `lighten` rewrites the .TEX records and the
  font chunks in place (ids and chunk indices unchanged, so nothing else moves).
- Stock FA maps (F01..F09): the same step through `tools/kl_stock_mod.py` (kl-merge-b6's stock-with-mods builds),
  or, for the pictures alone, a Patch01.zip override is NOT possible (the .TEX is inside each level archive).

## 5. Not data (needs the hook): positions, colours, new elements

Crew list, money box (Total / Loot / Rewards), objective strip, clock restyle: all code. See `re/hud.md` for the
draw primitives and constants once the hud_re agent reports.
