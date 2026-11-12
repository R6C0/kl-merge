# Menu redesign (full), plan 2026-11-10 (offline, nothing installed)

Owner (11-10): "i wanted a full redesign on the ui i thought it provided it". Reality: stage 1 (fonts + colours) and
stage 4 (OSD clicks) only re-skinned text and one sound bank. Words: PROVEN = checked on the real files by a tool;
GUESS = needs the game. Tool: `tools/kl_menu_redesign_1110.py` (+ `_test`), output `C:\kl_build_1024\menulook_1109\redesign\`.

## 1. Why it still looks like Dog Days (PROVEN)
- Every menu page is data in `frontend.xml`/`ingame.xml`/`online.xml` + a menu scene (`kaneandlynch.zip`: .gms/.prp/.prm/.TEX).
  Stage 1 touched fonts, colour sets and (optionally) bars. The pictures (backdrops, logos, Kane/Lynch art, page plates,
  level pictures) are untouched, and the page LAYOUT is Dog Days'.
- DD's menu scene descends from DM's: 13 picture families share a name. Compose-and-compare of both scenes (sheets below):
  MainLogo, GameLogoFA, ListBorder/Cursor, arrows, PlatformVersion, DebugGridOverlay are ALREADY pixel-identical.
  What differs: Background, Background_Tape, Background_Dirt01/02 (DD = a blurred face, DM = near-black grunge),
  GameLogo (DD "Dog Days" 512x230 vs DM 276x229 stacked), GameLogo_big (512x348 vs 448x349), LegalText (text).
- DM-only art with NO DD counterpart (the real "Dead Men look"): Background_Kane 474x720, Background_Lynch 410x720
  (+ *Options variants), Background_HeaderSplat 365x267, Background_FABag 1280x720, LevelPicture_M01..M14 + FA01/02/03/06
  (891x530 DXT1 with torn-edge frames), RulePicture x8 768x450, ProfilePicture x8 500x500, FAWeaponsBuyCircle*, Objective*,
  LevelIndicatorGraphic x16. These need a page that has an entity to show them (stage 3+).
- Real DM font = Morpheus small caps (`Fonts/MorSCCB_.ttf-20/28/30/37`, `MorSCLB_.ttf-24`, ids 392-427, ABGR pages).
  Stage 1 used Impact/Anton as a stand-in.

## 2. Inventory
| | DM `Scenes/KaneAndLynch.zip` | DD `Scenes/kaneandlynch.zip` |
|---|---|---|
| textures | 399 (289 DXT1, 55 ABGR, 48 DXT5, 7 DXT3) | 989 (658 DXT5, 175 DXT1, 136 ABGR, 18 DXT3, 2 other) |
| pictures (ZWINPIC) | 444, 95 families | 883, 188 families |
| .TEX header | 2048 ids | 4096 ids (`0x20/0x4020`) |
| XML | frontend 363 KB, ingame 110 KB, online 92 KB | frontend 671 KB, ingame 270 KB, online 289 KB |
Full tables: `redesign\inventory.json`. Sheets: `redesign\sheets\dm_pictures_1.png`, `dm_pictures_2.png`, `pairs_dd_vs_dm.png`.
Screens (DD) and their source: main menu / Arcade+FA lobby / map select / shop / options / Mod Options = `frontend.xml` +
menu scene (Patch01(_rows12) carries the XML overrides; the scene lives in kaneandlynch.zip). Loading, pause, scoreboard, shop-in-level,
HUD = level archives (`<map>_Main.zip`: own fonts, bars, online.xml; already carry the stage-1 font bake; never bake twice).
DM equivalents: DM `frontend.xml` PlayMenu/OptionsMenu/Credits/AttractMode, DM level pictures, DM `Loader_Sequence.*`.

## 3. Ordered stages (biggest visible change first)
| # | Stage | Kind | Tool / inputs | Proof | Toggle | Risk | Owner sees |
|---|---|---|---|---|---|---|---|
| A | Backdrop swap (Background, _Tape, _Dirt01/02) | pure texture swap | `kl_menu_redesign_1110.py stage` (DONE, 25 tiles changed, rest already identical) | `check` PASS: only .TEX differs, ids/names/sizes kept (PROVEN); looks (GUESS) | `[MenuLook] DeadMen` (same _deadmen archive) | low | face backdrop becomes dark grunge. Small. |
| B | DM page art on existing slots: Kane/Lynch side portraits, HeaderSplat, FABag, level pictures for the FA map list | layout/data: needs entities. DD has Graphic names for level pictures (LevelPicture_F01..F09) -> repaint those textures with DM LevelPicture_FA01/02/03/06/M0x (same 891x530 DXT1) | extend `stage` with `--levelpics`: compose DM picture, scale to DD tile sizes, write ABGR | per-tile size equal (PROVEN by `plan` for tiles; levelpics GUESS size) | same | low-medium | DM map screenshots in the map-select/lobby |
| C | Logo: GameLogo / GameLogo_big "recut" (size differs) | texture re-cut | compose DM logo, scale to DD picture W x H, cut to DD tiles | `plan` says recut | same | low (aspect GUESS) | Dead Men logo instead of Dog Days on the main menu |
| D | Bars/lines brush look | texture | existing `kl_hud_menu --bars` (stage 1 option) | existing | `Bars` | low | already specified in menu_look_1109 |
| E | Authentic MorSC fonts | font bake | kl_menu_look_1109 with the MorSC ttf (needs the DM font pages as the glyph source, or the TTF if present) | widths.txt vs layout | same | medium (text overflow) | Dead Men lettering |
| F | Page layout (Kane/Lynch columns, DM main menu arrangement) | XML + scene entities (5096-slot / 512-template caps) | new; DM frontend.xml PlayMenu as the source, DD entities for plates | menus.md caps | new | HIGH | the real DM look; largest work |
| G | Clicks: confirm/back silent, nav still Dog Days | sound / hook | see 4 | needs a local probe | `[MenuLook]` | medium | clicks |
| H | Menu music (MenuLoop_01) | optional | menu_look 4c | | | low | DM theme |

## 4. Click report (owner: no click on confirm, DD sound on navigation) - CAUSE UNPROVEN
Candidates, all GUESS: (1) which click plays is chosen by the XML (PlaySound/ForceSound flags and Sound= names), and DD's
`frontend.xml` may call names other than the 5 records stage 4 swapped; (2) the global bank pair the game actually opens for UI
may not be only `kaneandlynch.WHD/.WAV` (level `.SND` banks can carry their own OSD records); (3) Up_Down shares a data span with Slide, so
replacing in place may have been shadowed by the stock record. Next offline step: list every `Sound=`/`PlaySound` value in DD
frontend.xml and match them to bank records by name (kl_menu_sounds_1109 probe), then add the missing records. No game run needed.

## 5. What this revision ships
- `tools/kl_menu_redesign_1110.py`: `inventory`, `sheet`, `plan`, `stage`, `check` (decoders DXT1/3/5 + ABGR, picture compositor,
  swap planner). Test `tools/kl_menu_redesign_1110_test.py` PASS. Stage: `redesign\stage\Scenes\kaneandlynch_deadmen.zip` (from stage1's
  zip so the font bake stays), NOT installed. Honest result: stage A alone is a minor visible change; the owner's "full redesign" is stages B, C, F.

## 6. Stages B / C / F built (2026-11-10, 6b): `stageb`, `checkb`
Kit `C:\kl_build_1024\menulook_1109\redesign_b` (install.py pins live stage A caf16a44, stage zip 9de0f526, `live_caf16a44.zip` = the undo copy,
`UNDO menu redesign B 1110.bat`, `contact_before_after.png`). Tool: `python tools\kl_menu_redesign_1110.py stageb --src <live caf16a44 zip> --out <dir> [--parts bars,plates,logos,lobby]`.
PROVEN by `checkb` on the real files: 41 .TEX records change (22 bars/lines, 14 plate tiles, 4 logo tiles, 1 lobby tile), each stays one-mip ABGR with the same id,
name and w x h; every other zip member is byte-identical; record count and ids equal. Looks (GUESS until seen in the game) are in the contact sheet.
- bars: `kl_hud_menu.repaint` (stage 2 of menu_look_1109): chalk dry-brush FocusBar_short/medium/long + Line_* tiles (22 textures). `MenuFocus_long` / `FAFocusBar_long` are already Dead Men's
  bars (identical, shared DXT1, left alone); `FocusBar_medium_02` has a drawing in it, left alone.
- plates: LobbyBackground, BackgroundWeaponShop, ChapterBackground, DoubleBackground, BlackBand(Error)Background(2): alpha x 0.55..1.35 by a luminance map of Dead Men's Background
  (grunge); RGB untouched, zeros stay zero, no alpha above the plate's own maximum.
- logos C: GameLogo (DD 512x230) and GameLogo_big (512x348) get Dead Men's "KANE & LYNCH / DEAD MEN" logos, left-aligned at native size, in DD's own tiles. GUESS: the menu anchors the picture left.
  MainLogo / GameLogoFA were already Dead Men's.
- F: `LobbyMap_DM07` (a text card "THE DIG") gets Dead Men's M07 picture (inner frame, 16:9 centre crop). DD already carries Dead Men's own pictures for every other DM map
  (LevelPicture_DM*, LobbyMap_DM*), and the stock F01..F09 / L / H pictures belong to Dog Days maps, so NOTHING else is swapped there. DD10 (Flat Raid) has no Dead Men original.
- Not done: KLPic_Char*/Mask* hero portraits (they show the Dog Days / ported heroes, no 1:1 Dead Men picture family; ProfilePicture x8 500x500 are Dead Men characters but need the character pairing of re/characters.md),
  Kane/Lynch side columns, HeaderSplat, FABag, weapon buy circle (need page entities = stage F proper, 5096-slot cap).

### Menu music (H): why it cannot be a file swap (PROVEN on the live files)
DD's main-menu ambience = 4 records `SFX/OSD/Menu_BG_Sounds/Menu_BG_{Plane2a,Car,Hotel,RoomBackAlley}.wav` in `Scenes\kaneandlynch.WHD`, all fmt 0x801000 = Ogg Vorbis STREAMED: the data is in the 1.88 GB
`PC_Def.str` (offsets 0x12b81000, 0x7b96100, 0x3a100d00, 0x313f7200), not in the .WAV. The bank holds 186 non-streamed records, all IMA ADPCM (fmt 0x11), none Vorbis. Dead Men's `MenuLoop_01` is a Vorbis stream of
the Dead Men `PC_Def.str`. So a `_deadmen` copy of the .WHD/.WAV cannot carry it: (a) re-pointing a Menu_BG record at another PC_Def.str offset only plays another Dog Days clip; (b) appending the clip
to the .WAV needs the record's fmt changed 0x801000 -> 0x11 (IMA, 77 s x 32 kHz stereo = 2.5 MB) and the hook's klms table (`klmenusounds_logic.h`) writes only pcm/size/samples/off/offhi, not fmt/block/spb,
so the hook needs a field extension (peer-owned, untracked); (c) which of the four BG records is the menu's is not known offline. Verdict: not done; the smallest real route is (b) + a probe that logs the
record the menu opens.

## Stage F layout tool: `tools/kl_menu_layout_1110.py` (2026-11-10, cloud, OFFLINE: no game file, nothing run in the game)

Owner approved the full redesign without mocks; stage F = the page LAYOUT. Test `tools/kl_menu_layout_1110_test.py` (82 checks, synthetic set shaped
like the live windows; `kl_tests.py --py --only kl_menu_layout_1110_test.py` PASS). A dry run of `plan` on the live WINDOW STRUCTURE (rebuilt from
`re/menu_inventory_1110/frontend_rows12.md`) says OK, 0 problems; the real files were never opened here.

What it lays out (DATA at the top of the tool: `LAYOUT` per window, `rows` rules, `ART`; every number a GUESS):
- MainMenu: Dead Men's arrangement. Logo (template body GameLogoTemplatePCMain, used by MainMenu only) to the top-left (64, 40); the six entries
  at x 150, y 300.. pitch 44 with their brush bars 10 px left / 9 px up (stock offsets); Kane (474 x 720) at x 560 and Lynch (410 x 720) at x 870,
  full height, drawn by the two re-pointed decorative icon elements (Icon_Campaign / Icon_Heist -> Background_Kane / _Lynch); the other four icons
  re-pointed at the 8 x 8 blank KLPic_None1. Ticker, band plate, bottom legend: left alone.
- HeistPlayMenu / 2 / 3 (Arcade, Dead Men maps, Dead Men campaign): picture at (120, 130), the level selector (its title in the display face) right
  under it at y 448 with its bar, briefing at (700, 130), the headline icon -> Background_HeaderSplat behind the page title.
- KLHeister: label column at x 120, pitch 36 (label, bar, value cell, both arrows re-pitched together by the `rows` rule); splat behind the title.
  KLGuns (Mod settings): the same rule at the STOCK pitch 34 (Patch01's 11 rows must end above the legend band) - labels move to x 120 only.
- FALobby: picture at (120, 130); settings rows and the player table stay (the rows-12 lobby has no room); the lobby plate element (template body
  LobbyBackgroundTemplate, FALobby only) -> Background_FABag (1280 x 720, Dead Men's own lobby backdrop) at the screen origin.
- OptionsMenu: listed, NOT moved (rows flow-positioned by the game: only the first button carries a Y; the right column is the sub-pages' body).
- NOT here: shop pages I / II / hire, pause, round-over, respawn = `online.xml` / `ingame.xml` of each LEVEL archive (stage G, per level, 27 maps).
  ingame.xml of Patch01 is untouched. No element, template or ColorSet is added or removed (table untouched; `check` proves signature + element identity).

How the Dead Men art gets in (`stage --dm <DM>\Scenes\KaneAndLynch.zip`): the DD scene already holds the six Dead Men picture ENTITIES as EMPTY
stubs (Background_Kane / _Lynch / _KaneOptions / _LynchOptions / _FABag / _HeaderSplat: ZWINPIC with W = H = chunk = 0, PROVEN by the local partner).
The tool composes each DM picture (kl_menu_redesign_1110.Scene.compose), cuts it into <= 512 x 512 power-of-two ABGR tiles (the stock Background's
layout), appends the records to the .TEX (ids after the last stock id), writes sprite + picture chunks to the .prm (kl_prmgraph.new_chunk, the
kl_portraits.py record shapes PROVEN in the game for KLPic_*) and sets the stub's three ints in its .prp node. Entity count delta 0, no slot id moves,
.gms/.buf/.oct/.rmi/.rmc untouched (`check` proves: stock .TEX records and .prm chunks byte-identical, entity list identical). GUESS: a filled stub
draws like any other picture. Without --dm the scene is copied unchanged, the art step logs SKIPPED, and the art-dependent re-points (portraits, splat,
FABag) are NOT written (an empty stub draws nothing; the stock icons / plate stay).

GUESS list (plan prints it): every X / Y / pitch; the coordinate model (1280 x 720 virtual, ScreenBaseSize at (256, 72) PROVEN, nested groups ADD
their X / Y, Right = right edge at group right - X, Center = centre + X); an own X / Y wins over the Template's; Graphic= resolved by name at window
open (re/menus.md 2.7 untraced); the stub fill; KLPic_None1 hides an icon; the re-pointed icons keep no Priority (may draw under the Priority-1 band
plate); the MercsGraphic Line_* separators (X=0 Y=0, placed by code) follow the entries - stray lines at the old column in a shot = they do not (fix:
re-point them at the blank, a LAYOUT line); text widths (themed advance tables when the scene is readable, else 0.55 x px per character; .LOC keys on
the key tail); the FABag replaces the lobby plate wholesale.

Run + bench recipe (local partner; install order: plates repair (kl_menu_plates_1110) -> redesign B -> THIS):
```
:: 0. read-only plan on the live _deadmen set (Overlay\Patch01_deadmen.zip, Patch01_rows12_deadmen.zip, Scenes\kaneandlynch_deadmen.zip 9de0f526 or later)
python tools\kl_menu_layout_1110.py plan --dm "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\Scenes\KaneAndLynch.zip"
::    (adds --dm-inventory re\menu_inventory_1110\dm_frontend.md by itself once that file exists: DM_MAP entries take the Dead Men X / Y)
:: 1. stage (first run pins the three inputs); C:\kl_build_1024\menulook_1109\layout\ gets the three files, pins.json, install.py, bats, plan.txt,
::    build_report.json, contact_layout.png (BEFORE | AFTER boxes per window: coral = moved, amber = Dead Men art, grey = pictures)
python tools\kl_menu_layout_1110.py stage --accept-input --dm "<DM>\Scenes\KaneAndLynch.zip"
python tools\kl_menu_layout_1110.py check C:\kl_build_1024\menulook_1109\layout          (must say PASS; entity delta 0, 6 stubs filled)
:: 2. rehearse on a scratch copy, then live (game closed); backups <name>.before-menulayout_1110; undo = install.py --undo (byte-exact)
python C:\kl_build_1024\menulook_1109\layout\install.py --game D:\scratch\dd_copy --skip-run-check   (+ --undo)
python C:\kl_build_1024\menulook_1109\layout\install.py --dry
python C:\kl_build_1024\menulook_1109\layout\install.py
:: 3. bench (TEST hook, [MenuLook] DeadMen=1, shots every 2 s): main menu (portraits, column, logo) -> Arcade -> Dead Men maps -> Dead Men campaign
::    -> Heister -> Options -> Mod settings -> Online -> LAN lobby (12 rows) -> back; then DeadMen=0 for the stock shots of the same pages.
::    PASS: 0 faults / asserts, 'menu: table N' unchanged, no row over its column, nothing clipped; shots of both looks to C:\kl_build_1024\menulook_1109\shots\.
::    What to compare against: contact_layout.png (the planned boxes). Stray separator lines at the old main-menu column = the Line GUESS failed.
```
What the Dead Men inventory (`re/menu_inventory_1110/dm_frontend.md`, same table format) will refine: `DM_MAP` maps DD elements to DM PlayMenu
elements; every mapped element takes the DM X / Y (plan says so per element). Extend DM_MAP (and LAYOUT) from the DM tables: the column x / pitch,
where Kane / Lynch really stand (the DM 'Kane' / 'Lynch' templates: AlignH Left / Right, Priority 4), the options page's portrait variants.
