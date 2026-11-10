# Menu inventory for the T9 full redesign (2026-11-10, local partner, OFFLINE, no crash involved)

2026-11-10: read-only inventory of the LIVE menu files for the cloud's layout tool (tools/kl_menu_layout_1110.py). No game launch, no game file written.
Words: READ = counted by a tool on the live files (tool named); GUESS = not proven. NOT DONE here: screenshots and the ML1 / ML5 benches (they need the game;
this pass was offline only), see section 6.

Tools (new, `tools/`): `kl_menu_inventory_1110.py` (+ `_test`) parses a menu XML with kl_hud_menu.tags (the game-style lenient reader) and resolves Template chains;
`kl_menu_pictures_1110.py` lists the menu scene's pictures and who uses them. Full tables (generated, read them with grep):

| File | Content |
|---|---|
| `re/menu_inventory_1110/frontend_rows12.md` | every Window / GuiElement of `Overlay\Patch01_rows12.zip menu/frontend.xml` (the file the game opens while `[Lobby] Rows12=1`) |
| `re/menu_inventory_1110/ingame.md` | `menu/ingame.xml` of `Overlay\Patch01.zip` (`Patch01_rows12.zip` has the same element data: 0 differing elements) |
| `re/menu_inventory_1110/online.md` | `Menu/online.xml` of `Overlay\Scenes\kaneandlynch.zip` |
| `re/menu_inventory_1110/pictures.md` | the menu scene's picture families (ZWINPIC): size, tiles, .TEX id/size/format, theme-restyled?, XML users |

Columns of the element tables: `i` = element index inside its window (document order, nested elements count), `par` = parent element index, `d` = nesting depth,
name, Type, Template, X Y W H AlignH AlignV Priority Font ColorSet (a trailing `~` = inherited from the Template chain, otherwise the element's own value),
text key or literal (`Text=` plus child `<Text>` lists), picture (`Graphic=` plus child `<Graphic>` lists and FocusGraphic), `cond` = enclosing Platform / ExcludeIn / Locale / GameRegion.
Template definitions that carry child GuiElements ("template bodies", instanced where used) are listed as `## Template body Template:<name>`.

## 1. Live files (md5 first 8, READ 2026-11-10)

| File (`<DD>\KLExpansion\Overlay\...`) | md5 | members with XML |
|---|---|---|
| `Patch01.zip` | df16480f | menu/frontend.xml, menu/ingame.xml |
| `Patch01_rows12.zip` | 2d7120c1 | same (used while Rows12=1; GUESS that rule still applies) |
| `Patch01_deadmen.zip` / `Patch01_rows12_deadmen.zip` | ba1154de / 3a452a28 | same (stage-1 themed copies) |
| `Scenes\kaneandlynch.zip` | 630d451d | guielems.xml, windows.xml, Menu/online.xml, menu/frontend.xml, menu/ingame.xml |
| `Scenes\kaneandlynch_deadmen.zip` | **9de0f526** (stage 1 + 6b stages A and B/C/F) | same; the layout tool must pin on this |

The `_deadmen` copies differ from the un-themed ones ONLY in `<ColorSet>` values and `Font=` (READ, tag-by-tag compare; same tag count and structure):
frontend (both): 13 ColorSet tags + 19 GuiElement + 9 Template `Font` changes (the Text -> H3 body repoint); ingame: 12 ColorSet tags only;
scene `Menu/online.xml`: 11 ColorSet tags + 2 Template Font. The scene's embedded frontend/ingame XML is unchanged (unused fallback; the overlay Patch01 overrides it).
So positions (X Y W H, Align, Priority, order, names) of every XML are still Dog Days' own.
The hook log (DD `KLHook.log`, 00:33) shows `menulook:` redirect lines (Patch01 -> Patch01_deadmen, KaneAndLynch.WHD/.WAV -> _deadmen): the redirect is active.

## 2. Counts per file (READ: kl_menu_inventory_1110.py summary)

| File | Windows | GuiElements in windows | Template bodies | GuiElements in template bodies | Template definitions (duplicate names) |
|---|---|---|---|---|---|
| frontend.xml, Patch01_rows12 | 131 | 3625 | 53 | 471 | 331 (14) |
| frontend.xml, Patch01 | 131 | 3615 | 53 | 471 | 331 (14) |
| ingame.xml (both zips) | 55 | 1281 | 28 | 232 | 145 (15) |
| online.xml (scene) | 40 | 1402 | 39 | 424 | 173 (3) |

frontend rows12 vs Patch01 differ in 3 windows: FALobby 297 vs 277 elements (rows-12 lobby), KLGuns 50 vs 58, HeistPlayMenu3 25 vs 27.
Raw `<GuiElement>` open tags: frontend 4096 (= 3625 + 471), ingame 1514, online 1826.

`ZMercsMenuElements` (the menu manager's live table count): **none found.** No `menu: table N of 5096` line exists in the logs searched:
`<DD>\KLHook*.log` (KLHook.log, KLHook.old.log, KLHook.v62_stut.log), `C:\kl_build_1024\menulook_1109`, `C:\kl_build_1024\c9_1028`,
`G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\klhook`. Static ESTIMATE only (re/menu_count.md): live frontend set 4793 entries
(gamepad 4990) of the 5096 cap, 502 of 512 template slots. Consequence: the layout tool must ADD NO element and no template; moving / resizing / re-pointing existing ones is free.

Window lists (name + element count) are the `## Window` headings of the three tables.

Font / ColorSet use (effective, per element; READ): frontend Text 873, Button 228, Header 148, Menu 16; ColorSets Legend 165, Default 88, CreditsLarge 92, White 74,
OnFocus 39, Header 9, KLFocus 9, AssignKeys 2, MoreSettings 2. online: Text 225, **`Buttons` 104** (plural; no font of that name is among the 8 (GUESS: resolves to `Button`)), Header 41.

## 3. Picture entities (task b; READ: kl_menu_pictures_1110.py on `kaneandlynch_deadmen.zip` 9de0f526)

- Scene: **1337 ZWINGROUP** (folder tree `Menu/Resources/Frames/Winpics/Graphic/...`; each picture is a group named like the picture with a ZWINPIC child `Box`),
  **984 ZWINPIC**, of which **977 parsed** into **247 families** (`name#NN` instances); 1048 .TEX records. A picture's LOOK = its tiles' .TEX, SIZE / PLACE = W x H in the .prp node + sprite chunk.
- **7 ZWINPIC are EMPTY (W = H = chunk = 0, PROVEN on the .prp nodes): `Background_Kane`, `Background_Lynch`, `Background_KaneOptions`, `Background_LynchOptions`, `Background_FABag`,
  `Background_HeaderSplat`, `FAStatus_WeaponBig#00`.** XML elements name them (OptionsKane_T / OptionsLynch_T) but nothing draws. Showing Dead Men's Kane / Lynch columns needs a sprite
  chunk (.prm + .prp change), not a pixel swap. `Controller`, `ControllerOnline`, `IngameBriefingLevelPicture` are XML names with no ZWINPIC at all (6 unresolved names in total, see pictures.md).
- Theme state vs the un-themed overlay copy: 74 .TEX records differ = 8 font pages (stage 1) + 66 picture tiles (6b A: 25, B/C/F: 41). **33 theme-restyled families:**
  `Background`, `Background_Tape`, `Background_Dirt01/02`; `FocusBar_short/_short_02/_short_03/_medium/_medium_03/_04/_05/_long/_long_02/_tap_01/_tap_02`, `Line_Short_01`, `Line_Medium_01..04`,
  `Line_Long_01`, `AssignKeyFocus_long`; plates `LobbyBackground`, `BackgroundWeaponShop`, `ChapterBackground`, `DoubleBackground`, `BlackBandBackground`, `BlackBandErrorBackground(2)`;
  logos `GameLogo`, `GameLogo_big`, `GameLogoFA` (6b said it was already Dead Men's; unexplained, GUESS a re-encode); `LobbyMap_DM07`.
  All keep id / name / W x H: **no position or size changed**.
- Mod art that predates the theme (differs from STOCK, 59 tex): `KLPic_*`, `LevelPicture_DM*`, `LobbyMap_DM*`/`DD10`, `LobbyRand_F*`.
- 58 families are named by no menu XML (hook-driven lists like KLPic*/LobbyMap_*, or dead); listed at the bottom of pictures.md.
- Not yet restyled and relevant to a re-layout: `LevelPicture_*` / `LobbyMap_*` (only DM07 swapped), `FAStatus_*` icons, `KLPic_*`, the Kane / Lynch columns (empty), `ListBorder`, `Cursor`.

## 4. Fonts shared with the HUD (task c)

The menu scene has its own 8 ZTTFONT entities (`Button Text DebugText Menu Header H3 H2 H1`, parent `AllLevels/FFFonts.zip`); every level archive carries the same eight as its own copy
(checked on `Scenes\Locations\F01\F01_Main.zip`). READ: front-end pages (frontend.xml) use only the scene copy, which no HUD text shares. In-level pages (ingame.xml, online.xml: pause, shop,
scoreboard) use the LEVEL's copy, the same fonts the in-level HUD texts use, so changing a level font changes the HUD too (a bake per map).

## 5. Resolution facts (task c)

- READ: the menu is laid out on a **1280 x 720 virtual screen**: the full-screen `Background` ZWINPIC is 1280 x 720 (.prp node), and windows use `ScaleToViewPort="True"` (template WindowDefault).
  Template `ScreenBaseSize` = W=768 H=576, AlignH/AlignV Center, X=0 Y=0: a 4:3 box centred on the virtual screen, i.e. offset (256, 72). Most pages nest their content in one or more of these groups.
- PROVEN (re/shop_hire.md:332): a card at X=432 Y=60 in the group measured at (688, 132) virtual = 432+256, 60+72, and the virtual screen is stretched to the back buffer by (W/1280, H/720)
  (measured at 640 x 480, a non-uniform 0.5 x 0.667).
- GUESS (not measured): at 1920 x 1080 the factor is 1.5 on both axes, so the 768 x 576 group becomes 1152 x 864 at (384, 108); the 256 virtual px strips each side are free for a wide layout.
  Non-16:9 back buffers stretch non-uniformly. Whether content outside the 768 box is clipped: not checked (GUESS no).

## 6. Not done in this pass

Screenshots into `C:\kl_build_1024\menulook_1109\shots\<stock|deadmen>\<page>.png` and the ML1 (clipped rows) / ML5 (menu clicks) benches need the game; this step was offline and read-only
on the game folder. Open for the PC session.

## 7. Open guesses

1. Template resolution = template attrs first, element's own on top; duplicate template names -> the last definition wins. Shown values are the tool's EFFECTIVE values, not read from the exe.
2. XML picture-name lookup is case-insensitive with a family fallback (pictures.md marks `[case]` / `[fam]`).
3. 1920 x 1080 scale = 1.5 uniform; no clipping outside the 768 group.
4. `Font="Buttons"` in online.xml resolves to `Button`.
5. The 7 empty pictures are DD stubs; drawing them needs sprite chunks.
6. `GameLogoFA` differing from the un-themed scene is a re-encode.
7. The static table count 4793 is an estimate; no live TableLog run exists.

## 8. Verification pass (2026-11-10, adversarial, offline, no crash involved)

Re-counted from the live zips with an independent regex (comments stripped): 131 / 55 / 40 Windows and 4096 / 1514 / 1826 GuiElement open tags; the per-window element count of EVERY window matches the headings (0 mismatches in all three tables).
Spot-checked against the raw XML + Template tags: CoopOnline, IngameQuit, DifficultyScreen, QuickPlayerMatch, FAGTDieRespawnTip, ExitMenu, FAWaitForPlayers (X Y W H, Align, Font, ColorSet, Priority all equal). Texture records 732, 733, 440, 441, 376, 373: w x h x bytes/px + 41-byte header = entry length (ABGR 4, DXT3 1, DXT5 1), as listed.
ERROR FOUND AND FIXED: online.xml defines `<Template Name="ScreenBaseSize" Name="ScreenBaseSize(SafeFrame)" ...>` (duplicate Name attribute). The first tool run kept only the last Name, so all 40 ScreenBaseSize groups of `online.md` showed blank X/Y/W/H/Align. The tool now registers the template under every Name value; `online.md` regenerated (42 lines changed). WHICH name the exe keeps is a GUESS; the other files carry one Name and are unaffected.
Note (not an error): the `WindowDialog` template has ScaleToViewPort=False, so dialog windows are not stretched by the 1280x720 rule in section 5; `WindowDefault` has True. The 1920x1080 factor stays a GUESS.
