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
