# In-game menu UI in the Dead Men look (track T9, 2026-11-09, cloud, OFFLINE)

Owner (11-09 ~19:10, live): "overhaul the whole in game menu UI to make it feel more like dead men too, even the menu button
sounds; also in settings make a button for the mod so you can change it (make it however you desire) but I want the default to
have this on".

Written in the cloud with NO game file: every fact below is cited from `re/` or the tools; `NEEDS FILE` marks what only the
owner's PC can tell; `GUESS` marks a design choice nothing has proven. Nothing here ran in the game and nothing is installed.
Words: READ = read in kl2.exe or the files as the cited note says; RAN = a tool was run offline; GUESS as above.

Deliverables of this round: this plan, the stage-1 tool `tools/kl_menu_look_1109.py` (+ `_test.py`, synthetic data), the
how-to block at the end (section 8).

## 0. Summary

1. The look already exists as code: `tools/kl_hud_menu.py apply <overlay> <out> --fonts` (2026-10-12, re/hud_menu.md 11) bakes
   the menu scene's eight fonts (Anton / Impact capitals, light chips on the big sizes), recolours every `<ColorSet>` of the three
   menu XML files to chalk / coral / ink / grey, and repaints the focus bars and separator lines as chalk brush strokes - without
   adding or moving ONE element (the menu manager's table stays as it is: `check`). It was built from the installed overlay of
   2026-10-12 and NEVER installed or seen in the game (hud_menu3). The live overlay has moved on since (Mod settings rows, Match
   page, Lobby rows 12, hire / shop pages, Dead Men portraits), so it has to be re-made from the LIVE files, not from hud_menu3.
2. Stage 1 (this round's tool) = fonts + colour sets as a themed COPY of the live overlay pair `<DD>\KLExpansion\Overlay\Patch01.zip`
   (+ `Patch01_rows12.zip`, the file the game actually opens while `[Lobby] Rows12=1`) and `Overlay\Scenes\kaneandlynch.zip`, staged in
   `C:\kl_build_1024\menulook_1109\` with install.py / UNDO (pinned md5s, `.before-menulook_1109` backups, byte-exact undo). The
   stock files under `<DD>\Patch01.zip` and `<DD>\Scenes\kaneandlynch.zip` are NEVER touched: the overlay IS the mod's own copy of them
   (klslot.c overlay rule, section 4).
3. In-level pages (pause, shop I / II / hire, scoreboard, respawn) take their fonts, bars and `Menu/online.xml` from the LEVEL archive
   (re/hud_menu.md 0.3, 11.2). Their fonts are ALREADY the Dead Men bake on every expansion map (`kl_hud.py all --look deadmen`,
   re/hud_install.md 2) - a second bake there is forbidden (double-bake risk, 5.1). Their colour sets are stage 3 (`kl_hud_menu.py level`
   per archive, 27 maps).
4. Toggle: the hook has NO keyed per-file alias except for `Patch01.zip` (MountFirst / `[Lobby] Rows12`, klslot.c 963-985) and the
   overlay rule itself is unconditional. `[MenuLook] DeadMen=1` therefore needs a small klslot.c addition (a `_deadmen` VARIANT lookup
   on the resolved path, the BotGate `.bots.zip` pattern; section 4, design only). Until it exists the toggle is install / UNDO.
5. Sounds: Dog Days' menu clicks are in-memory waves `SFX/OSD/*.wav` of `Scenes\kaneandlynch.WHD` (+ `.WAV`), both under the game
   folder = overlay-redirectable (`Overlay\Scenes\kaneandlynch.WHD`). Dead Men's front-end clips sit under `SFX/UserInterface/` (the only
   long one, `MenuLoop_01`, is the menu theme, Vorbis in PC_Def.str). Plan: a themed copy of the .WHD / .WAV pair with the OSD records'
   DATA swapped for Dead Men's clips at the same record offsets, .SND untouched (section 3). NEEDS FILE for the names.

## 1. Inventory: every menu surface the player sees

Legend: files are the archive MEMBERS; "overlay" = `<DD>\KLExpansion\Overlay\...` (the copy the game opens while `[Expansion]
Overlay=1`, klslot.c 558-562); "level" = the level archive `Scenes\Locations\<slot>\<slot>_Main.zip` of the map that is playing
(expansion maps: `KLExpansion\Maps\<id>\<slot>_Main.zip` through `[Redirect.N]`).

| Surface | XML window(s) | XML file (archive) | Fonts (ZTTFONT chunks) | Colour sets | Pictures (bars / lines / plates) | Sounds |
|---|---|---|---|---|---|---|
| Main menu, Arcade, Dead Men maps page(s), Heister, Guns, Mod settings, Match, Options, key assignment, credits, leaderboards, profile | `MainMenu`, `HeistModeMenu`, `HeistPlayMenu`(+`2..9`), `KLHeister`, `KLGuns`, `KLMatch`, `OptionsMenu`, ... (re/menus.md 4.1, 2.4; mkoverlay.py) | `menu/frontend.xml` in overlay `Patch01.zip`; **`Patch01_rows12.zip` is what the game opens while `[Lobby] Rows12=1` (default 1)** (klslot.c 972-985): stage BOTH | the menu scene's 8: Button 18, Text 20, DebugText 20, Menu 20, Header 28, H3 20, H2, H1 (`kaneandlynch.prm` chunks in overlay `Scenes\kaneandlynch.zip`; re/hud_menu.md 11.1) | 12 `<ColorSet>` in frontend.xml (names READ: Default, White, Header, OnFocus, Legend x2, Debug, AssignKeys, ... re/hud_menu.md 1.2, 2) + mkoverlay's `KLFocus` (white / headline red) | focus bars `FocusBar_short/long/medium*`, `MenuFocus_long`, lines `Line_Short/Long_01#NN` = ZWINPIC entities -> 22 `.TEX` textures of the scene (15 bar tiles, 7 line tiles; re/hud_menu.md 2); `FocusBar_medium_02` grooved, `MenuFocus_long` / `FAFocusBar_long` DXT1 shared (left alone there); backgrounds `BackgroundTemplate`, `ChapterBackgroundTemplate`, `LobbyBackground`, `Background_FABag`, `LevelPicture_*` (re/menus.md 2.7) | `SFX/OSD/*.wav` records of `Scenes\kaneandlynch.WHD` + `.WAV` (READ in a dump: `SFX/OSD/Up_Down.wav` and a `Menu` one, re/gun_echo_1107.md 8); XML `PlaySound` on OpenWindow / CloseWindow / SendMessage, `ForceSound` on Window (re/menus.md 2.3) |
| Online menu, lobby, waiting | `OnlineMenu`, `FAPlay`, `XboxLive*`, `FALobby` (frontend.xml), `FAWaitForPlayers` (online.xml) | frontend.xml as above; `Menu/online.xml` of overlay `Scenes\kaneandlynch.zip` (loaded at the menu, re/menus.md 1) | the same 8 | online.xml: 12 sets, `Default` twice (second one bluish 829EC1), `WANTED`, `DirtyMoneyColorSet`, `Black`, `Legend` x2 (re/hud_menu.md 1.2, 2) | lobby static bars `LobbyFB#..`, `FocusBar_Long_02`, lines; `FAStatus_Ready#NN` icons (not touched) | as above |
| Pause (Arcade / FA) | `IngamePauseHeist`, `IngamePauseFA` | `menu/ingame.xml` in overlay `Patch01*.zip` (also the campaign's pause: scope risk 5.3) | the LEVEL's 8 fonts (already `--look deadmen` on expansion maps; stock on the 9 stock maps) | ingame.xml: 12 sets | the level's `MenuFA.zip` copies of the bars / lines (level `.TEX`) | level bank `<slot>_Main.SND` + `.WHD/.WAV` (GUESS: the OSD waves are also in the level pair; the DD09 dump named `kaneandlynch.WHD` offsets, so the global pair may stay loaded - NEEDS FILE) |
| Round over / scoreboard, Ready / Buy weapons | `HeistStatus*`, `FAStatus*`, `FARoundSummary` | `Menu/online.xml` of the LEVEL archive (re/hud_menu.md 1.3, hud_menu_buttons.md 1) | level fonts | level online.xml sets (DM01 variant has 3 more, re/menu_count.md 1) | level `.TEX` bars (shopbar 1023 already repainted the `FocusBar_short` family dark #4a4744 on 27 maps, re/open_work_log.md 2026-10-23 07:10) | level bank |
| Shop page I (stock), page II (PD2 guns), hire page, MOD CONTROLS | `FABuyWeaponsNew` / `...Category` / `...Weapon`, `BuyWeaponDialog`; pages II / hire / controls are the hook's text rewrite over the same window (klshoppage.c carrier, re/keybinds_ui_1028.md 5.3) | level online.xml | level fonts; the hook writes TEXT only (no font choice of its own) | `White` on the 8 rows over the dark band (shopbar 1023) | `WeaponBuyFB#01..#15` opaque (AlphaMax 255), `WeaponShop*` pictures = level art, stat bars drawn by code | level bank |
| Dead / respawn / escaped | `FADead*`, `FARespawn*`, `FAEscaped` | level online.xml | level fonts | `KilledBy` coral etc. (restyle_data) | - | level bank |
| Loading screen | not XML: `Loader_Sequence.*` of the slot + the `_LS` bank (re/expansion.md 1, re/audio.md 1) | - | - | - | - | out of scope (fallback = stock slot's) |
| Subtitles, HUD | not menu | - | level fonts (H3 small) | - | - | - |

NEEDS FILE (first local step, read-only, 10 min): (a) `python tools/kl_hud_menu.py diff` is not it - run the stage tool's
`inventory` sub-command on the live overlay: it lists every `<ColorSet>` of the three XML files with its values (the exact stock
hex was never written into re/; only the roles are READ: white, black, grey, red d7373a / d00000, dark red, bluish 829EC1), the
font chunks with px, and whether `Patch01_rows12.zip` is present and newer than `Patch01.zip`. (b) `python tools/kl_whd.py`-based
listing of the `SFX/OSD/` names in `<DD>\Scenes\kaneandlynch.WHD` and of `SFX/UserInterface/` + `Menu` names in Dead Men's front-end
.WHD (the exact DM front-end bank file name is NEEDS FILE too: CLAUDE.md names `gamemenu.zip` and `mainsceneincludes.zip` as Dead
Men's menu archives; the `.WHD/.WAV` pair sits beside the archive as for a level).

## 2. The look mapping (what changes, what must not)

Palette (tools/kl_hud.py 1032-1040, kl_hud_menu.py 69-78, design_mock_1109.html :root): CHALK f3f0ea, CORAL f0475a, INK 0c0c0d,
AMBER e0962e (the HUD's ORANGE e8831f is the traitor colour; both are "amber" to the owner), GREEN 63a65b / 4f8f49, DEAD 8c3138,
GREY/DIM 8d8982 (mock 9a968f). The stage-1 tool carries all of it in `COLORS`.

### 2.1 Fonts (menu scene only: `Scenes\kaneandlynch.zip` .prm chunks + their page-0 textures)

Rule from the owner's look (2026-10-11, kl_hud.py `--look deadmen`): Impact (Anton when `<work>\fonts` has it), weight 400,
lower case DRAWN as capitals, LIGHT chips (`_chip`, at most two nicks on the outline, <= 3 % of the ink, a hairline crack only at
>= 24 px), **no chips under 16 px** (a 0.5 px nick eats a 6 px stem: kl_hud.py DRAFT_SPECS_ANTON note). Baseline NOT moved
(`build_font(baseline=False)`: XML Y positions keep their baseline; only cap tops rise, re/hud_menu.md 11.1). Sizes are
re/hud_menu.md 11.1's (every capital at least as tall as the stock's); the table is `MENU_FONTS` in the tool:

| Font slot | Used by (READ, re/hud_menu.md 11.1) | Face | px | track | caps | chip |
|---|---|---|---|---|---|---|
| Header, H1 | page headlines, lobby level line | Impact / Anton | 28 | 1 | yes | 0.5 |
| Menu | lobby focus lines, error menus | Impact / Anton | 20 | 1 | yes | 0.3 |
| Text, H2 | every row / cell / number (168 + 35 + 26 uses) | Impact / Anton | 19 | 1 | yes | 0 (under the chip floor: 19 px glyph, cap ~17 - kept 0 for readability of prices, GUESS) |
| Button | footer prompts, key hints | Impact / Anton | 17 | 1 | yes | 0 |
| H3 | the BODY face: paragraphs re-pointed here by `repoint_body` (tips, help, legal, briefing) | Segoe UI Black / Montserrat 600 | 17 | 0 | NO (mixed case) | 0 |
| DebugText | nothing names it | Segoe UI Black / Montserrat 800 | 15 | 3 | yes | 0 |

Chips: `chip` is the `amount` of `kl_hud._chip`; the tool zeroes it for any px < 16 whatever the table says (`chip_for`).
Widths: Impact capitals are wider than the stock lower case. `kl_hud_menu.py` measures nothing at bake time; its `fontsheet`
sub-command draws every page's own strings with the new records (widths and shapes, not the game's vertical placement: re/hud_menu.md
11.5 item 7), and `preview` of kl_hud.py draws one line. The stage tool therefore writes `fontsheet.png` and a `widths.txt`
(advance sums of the longest row texts per font, stock vs new, from the records) so the local session can see overflow candidates
BEFORE a bench: leaderboard names, lobby rows with fixed columns, 'Lens glare / cracks (cracks: next start)' (the longest Mod
settings label), the shop's 'Police reg.' column, hire 'Pierre  $45K'. Where a row runs over, the fix is a smaller px for `Text`
(19 -> 18) or `TextWidth=` on that element, never a new element.

### 2.2 Colour sets (attribute VALUES of existing `<ColorSet>` tags; no tag added)

The reader takes exactly `NormalColor FocusColor DisableColor` as `0xAARRGGBB` (READ 0x8ab978..0x8ab988; `DisabledColor` in online.xml's
last four sets is read by nothing). Stock values are not in re/ except by role; the tool maps by NAME first (`COLORSETS`, GUESS-marked
values where the stock hex is unknown) and by ROLE second (`kl_hud_menu._role`: greys -> chalk / ink / dim by brightness, reds -> coral /
dead by brightness, alpha kept; anything else - e.g. the bluish second `Default` of online.xml - left alone and LOGGED).

| Set (file) | Stock (role, READ) | Proposed normal / focus / disable | Why |
|---|---|---|---|
| `Default` (all three; online.xml's FIRST) | white text, focus INK on the bar (a00c0c0d focus seen on the shop rows, 2026-10-23 note) | chalk / ink / dim | rows: chalk, ink on the chalk focus bar |
| `White` | white / white | chalk / chalk / dim | data rows with faint bars (AlphaMax 64) |
| `Header` | bright red d7373a | coral / coral / dead | headlines, penalties (restyle_data) |
| `OnFocus` | **ink / ink / grey** (READ 11-10: ff000000 / ff000000 / ff888888 in all three files) = text ON a light plate, always: `RecCSFocus="OnFocus"` receivers (the focused row), lobby column headers, Heister values, leaderboard titles, 'Bonus' / 'Penalty' | **ink / ink / dim** (FIXED 11-10; was chalk / ink / dim = PALE on the plate, unreadable: 02:55 lobby shots) | the plate is light; the stock role stands. Live files built before the fix: `tools/kl_menu_plates_1110.py` (kit `C:\kl_build_1024\menuplates_1110`) |
| `Legend` (x2) | PC legend, focus d00000 | chalk / coral / dim | footer key legend |
| `AssignKeys` | ink focus text | chalk / ink / dim | key assignment bar is chalk too |
| `KLFocus` (mkoverlay, Mod settings rows) | white / headline red | chalk / coral / dim | the rows have NO focus bar: focus must stay a COLOUR change (mkoverlay.py 388) |
| `Debug` (spare, 3 files) | grey 80 alpha | GREEN_HI / GREEN_HI / GREEN, alpha ff | money columns (restyle_data's GREEN_SET) |
| `DirtyMoneyColorSet` (online.xml) | - | green as above | money in level pages |
| `WANTED` (online.xml) | - | AMBER / AMBER / DEAD | the traitor line |
| `Black` (online.xml) | black | ink | - |
| second `Default` (online.xml) | bluish 829EC1 | LEFT ALONE (logged) | which of two same-named definitions wins is NOT established (re/hud_menu.md risk 2) |
| any set not in the table | - | by role, else left alone and logged | never a silent guess |

Must NOT change (readability): the shop rows' `White` over the dark band (2026-10-23 pass): stays chalk = same contrast; money /
prices stay GREEN_HI on no bar (`PackagePrice` under the list); a `Disable`d row keeps a visible grey (DIM 8d8982, never INK). Alpha
is kept except on the four spare sets (ff on purpose, re/hud_menu.md 2).

### 2.3 Plates / backgrounds (stage 2, pictures; NOT in the stage-1 default)

What exists (READ, re/menus.md 2.7, re/hud_menu.md 1.2 / 2): pictures are ZWINGROUP -> ZWINPIC entities of the scene, each drawing
sprite chunks from `.TEX` textures; a picture's LOOK is its texture, its PLACE is the entity (fixed). So "torn dark smear behind a
panel" = repaint the texture of the panel entity the page already has (`ChapterBackgroundTemplate`'s picture, `LobbyBackground`,
`BlackBackground#01`, `Background_FABag`), never a new entity (table!). The focus bars (`_stroke_kit`: solid chalk, wandering edges,
hand-cut slanted ends, dry streaks) and lines (two chalk rows with gaps on black) are DONE by `kl_hud_menu.repaint` and are stage 2
option `--bars` of the tool. The smear / grain for the backgrounds needs the entity -> texture map of those four names (NEEDS FILE:
`kl_hud_menu.picture_uses`) and a painter (`kl_hud._plate_pixels`'s torn-edge frame, dark 0a0a0b at alpha .86 as the mock) - stage 2b,
after M1 has shown the bars. Map pictures `LevelPicture_*`, icons, the Dead Men portraits: unchanged.

### 2.4 What must not change at all

- Element count and order of every XML file (TABLE: re/hud_menu.md 1.1; live frontend count READ 5061..5065 of 5096 with v27b/c,
  mkoverlay.py 322-325 - entry 5000 is therefore an element today; the tool PROVES `signature(old) == signature(new)` per file).
- Names kl2.exe looks up (KNOWN_WINDOWS / KNOWN_ELEMENTS of kl_hud_menu.py).
- The `_rows12` / `Patch01.zip` mtime order (klslot.c 981: rows12 older than Patch01.zip = not used): install copies Patch01.zip FIRST.
- Level archives (fonts already baked; shopbar pass; 200 MB each): not in stage 1.
- `<DD>\Patch01.zip`, `<DD>\Scenes\*`, `KL_PortBackup`: stock, never.

## 3. Sounds

### 3.1 What Dog Days plays (READ / GUESS)

- The menu's clicks are in-memory waves. In the OSS_DD09_ECHO_S2 dump two UI voices (`k1`, rel 1 = 2D) had descriptors =
  `kaneandlynch.WHD` records: name 0x64d0 `SFX/OSD/Up_Down.wav` (rate 0x7d00 = 32000, size 0x2b06) and one 0x70 bytes before it
  (0x6460, "Menu"; re/gun_echo_1107.md 8, klechoprobe_logic.h 89). So: navigate = `Up_Down`, and a `Menu*` one; the rest of the
  `SFX/OSD/` family (confirm / back / error / slider) is NEEDS FILE (kl_whd.parse names with `OSD`).
- Which sound a widget plays is CODE (the XML only carries `PlaySound` on buttons and `ForceSound` on windows: re/menus.md 2.3;
  GUESS they are bools that suppress / force the default click). So the names cannot be re-pointed in XML; the DATA behind the
  names can be swapped.
- The pair `Scenes\kaneandlynch.WHD` / `.WAV` lies under the game folder: the overlay rule covers it (`Overlay\Scenes\kaneandlynch.WHD`
  replaces it, klslot.c 558-562) - no hook change for the sounds. The `.SND` sits in the scene archive (GUESS by the level layout,
  re/audio.md 1) and is NOT touched by the plan.
- In a level the dump still named `kaneandlynch.WHD` offsets (re/gun_echo_1107.md 8) -> GUESS the global pair stays loaded, so the
  pause / shop clicks follow the same swap. If not, the level pairs need the same record swap (stage 4b, per map).

### 3.2 What Dead Men has

- `SFX/UserInterface/MenuLoop_01.wav` (Vorbis, 77 s, PC_Def.str) = the main menu THEME (the launcher plays it, tools/kl_launcher_music.py).
  A streamed clip: replacing Dog Days' menu music needs a stream record in the merged PC_Def.str + the .SND wave object = kl_snd / kl_str
  territory (re/audio.md 0.6: the build id must stay 4c08b8d5) - stage 4c, optional.
- The clicks: NEEDS FILE. Expected under `SFX/UserInterface/` (the `--list` of kl_launcher_music.py showed MenuLoop_01 as "the only LONG
  clip under SFX/UserInterface" in the stream file, so the short ones are in-memory records of Dead Men's front-end .WHD/.WAV, Dead Men
  record = 14 dwords, kl_whd.py DM_F).

### 3.3 The graft (stage 4a, data only, themed copy)

`tools/kl_menu_sounds_1109.py` (WRITTEN 11-09, section 9; the text below was its plan): read `<DD>\Scenes\kaneandlynch.WHD` + `.WAV` (`kl_whd.parse('dd')`), pick the OSD
records by a NAME MAP `{'SFX/OSD/Up_Down.wav': '<DM navigate clip>', ...}` (NEEDS FILE to fill), decode the Dead Men clip (`kl_audio`
PCM / IMA; a Vorbis one through kl_oggdec / kl_pyvorbis), resample to the DD record's rate / channels / 16-bit PCM, write a NEW `.WAV`
(data appended in record order) and a `.WHD` rebuilt with `kl_whd.build` where ONLY `size` / `off` / `samples` of the swapped records
change; check that every record OFFSET equals the old one (names and record order unchanged -> the `.SND`'s wave pointers stay
valid; `kl_whd.build` is byte-identical for 183 of 184 stock files, so the rebuilt stock part must equal the original byte for byte
or the tool refuses). Output `Overlay\Scenes\kaneandlynch.WHD` + `.WAV` (themed copies; the stock pair under `<DD>\Scenes` untouched),
install / UNDO as stage 1. Never into the stock file; never into the level pairs in this stage.

## 4. The toggle `[MenuLook] DeadMen=1`

### 4.1 What klslot.c can carry today (READ in klhook/klslot.c)

| Mechanism | Keyed by | Carries a non-level archive? | Verdict |
|---|---|---|---|
| Overlay rule (558-562): any read-only open of `<game>\X` -> `<Root>\Overlay\X` if that file exists | `[Expansion] Overlay=1` only (all or nothing) | YES: `Patch01.zip`, `Scenes\kaneandlynch.zip`, `Scenes\kaneandlynch.WHD/.WAV`, any file under the game folder (not the exe, not DELETE opens) | carries the look, cannot TOGGLE it per key |
| `kls_patch_alias` (505-509, 963-985): an open of `<game>\Patch01.zip` answered with ONE other file | `[Expansion] MountFirst=` or `[Lobby] Rows12=1` (first wins) | Patch01.zip only, one alias | not reusable: single-valued and taken by Rows12 |
| `[Redirect]` / `[Redirect.N]` (511-553): `Scenes\Locations\<slot>\` -> `Maps\<id>\` | menu page | level files only | no |
| BotGate variant (464-491): the level archive -> `<name>.bots.zip` beside it | `[BotGate]` + host value | level zip only | the PATTERN to copy |

So: a non-level archive IS redirectable (overlay), but no ini key chooses BETWEEN two versions of it. `[MenuLook] DeadMen` needs:

### 4.2 Design (GUESS; no C written this round)

In `kls_map`, after the path is resolved (redirect target, patch alias, overlay copy or the stock path) and before the return:
```
if (kls_menulook_on && path is one of: patch01*.zip (after the alias), scenes\kaneandlynch.zip, scenes\kaneandlynch.whd, scenes\kaneandlynch.wav)
    try <dir>\<stem>_deadmen.<ext>  (kls_isfile) -> use it, kls_note(api, "menulook", full, out) once
```
~25 lines, data only (a path change inside the existing wrappers, no code byte: the same safety class as BotGate). `kls_menulook_on` =
`GetPrivateProfileIntA("MenuLook", "DeadMen", 1, klh_ini)` at init (DEFAULT 1 in the DLL as the owner wants, and `DeadMen=1
(recommended on)` in the shipped ini) OR the live `kset_v` value of a Mod settings row (then a change applies at the NEXT ARCHIVE OPEN:
the scene loader unmounts everything and mounts Patch01.zip + the scene archive at every scene load, klslot.c 129-131, so after a
round, or at the next start; say "(next menu load)" in the label). Variant files that are missing = stock look (logged once), never a
failed open. The `_rows12` case: the alias answers `Patch01_rows12.zip`, the variant step then looks for `Patch01_rows12_deadmen.zip` -
so the stage ships BOTH themed patches (the tool does).
- In-game row: klset.c answers `KLS*` names from the overlay's Mod settings window (KLGuns). A NEW row costs 4 table entries
  (ToggleText, `_Data` text, two arrows; mkoverlay.py 322-325) and the live frontend table was READ at 5065 of 5096 (31 free) before
  the HostOpts rows (+4) and Rows12 (lines / bars moved, rows 9..12 appended: +N) - the margin is unknown until `[Menu] TableLog=1`
  logs the live count (klset.c, re/hud_menu.md 8). RECOMMENDED: fold it into an existing 2-value row at ZERO table cost, as
  `KLSAdren` / `KLSNext` / `KLSLens` were: `KLS_Tex` 'Sharper textures (next start)' Off / On -> option `KLSTexLook` with 4 `<Text>`
  values 'Off', 'Textures', 'Dead Men menu', 'Textures + Dead Men menu' (`<Text>` children cost no slot, re/mod_options.md 'Why no
  in-game page'); klset.c `KLS_TEXLOOK` = Textures | DeadMen << 1 writing `[Graphics] Textures` and `[MenuLook] DeadMen`. Its own row
  only if TableLog shows >= 8 free AND entry 5000 stays an element (kl_hud_menu.check --menu-count N).
- KL Mod Options (Tk) row, zero risk, this round's proposal (`tools/kl_mod_options.py`, add after `hidevan`'s group or in G_GFX):
  `feat('menulook', G_GFX, 'Dead Men menu look: fonts, colours, menu sounds (recommended on)', 'on', 'start', 'T9 11-09: themed copies of the
  overlay menu pair + the menu sound pair, chosen by klslot.c [MenuLook] variants; stock look with 0', [('MenuLook', 'DeadMen', 1, 0, 1)])`
  + the `;DeadMen=1 ; (recommended on)` line in a new `[MenuLook]` section of klhook/KLHook.ini (`--check-ini` / `--check-rec` must
  agree). Not added here: the row would claim a key no DLL reads yet.

Toggle verdict (the klslot.c step now EXISTS as code, unbuilt: section 9): **install / UNDO until the klslot.c variant step is built and benched; then `[MenuLook] DeadMen` (DLL default 1) + the folded Mod
settings row.** The stage tool already writes the `_deadmen` variant names beside the live names (`install.py --variant`) so the same
stage serves both.

## 5. Staged plan, benches, install / undo, risks

Install pattern (every stage): stage folder `C:\kl_build_1024\menulook_1109\<stage>\` with the themed files, `pins.json` (md5 of
every INPUT as read, written by `--accept-input` on the owner's PC), `install.py` (refuses unless every live md5 == its pin, backs
each file up as `<name>.before-menulook_1109` NEXT TO it, never overwrites an existing backup, all-or-nothing, refuses while kl2.exe
runs, `--dry`, `--undo` byte-exact only when the live file is exactly what it wrote; `--variant` writes `<stem>_deadmen.<ext>` beside
the live file instead and touches nothing else), `INSTALL ... .bat` / `UNDO ... .bat`, `build_report.json`. Rehearse in a scratch copy
(`--game <copy>`) before the live install, as every 1108 kit did.

| Stage | What | Tool | Bench recipe (local, owner away, TEST hook, shots every 2 s) | PASS |
|---|---|---|---|---|
| 1 | fonts + colour sets of the menu pair (frontend / ingame / online.xml; the 8 scene fonts), themed copies of `Patch01.zip`, `Patch01_rows12.zip`, `Scenes\kaneandlynch.zip` | `kl_menu_look_1109.py stage --accept-input` then `install.py` (mode A) | **ML1**: main menu -> Options -> Mod settings -> back -> Arcade -> Dead Men maps -> Heister -> Guns -> Leaderboards -> Online -> lobby (LAN create) -> back; the mouse over entries, a map picture and the page background for 30 s (the 0x861720 path); `[Menu] TableLog=1` on | no fault / assert; `menu: table N` = the count with the old pair; capitals in rows, headlines not touching lines, no row over its column (shots: MainMenu, OptionsMenu, Mod settings, HeistPlayMenu2, KLHeister, FALobby, leaderboard), paragraphs in the body face |
| 1b | the same pair through one Arcade round on a Dead Men map to round over, Ready, shop I / II (F6) / hire (F3) / MOD CONTROLS (F2), pause (Esc) | - | **ML2** (`tools/kl_bench_1106.py` kit as the 1108 benches, 480 s) | pause / shop / scoreboard coloured as before (level files unchanged), no fault; prices readable |
| 2 | bars + lines of the menu scene (`--bars`) and the plate smears (2b, after the entity -> texture map) | stage tool `--bars`, then a painter | **ML3** = ML1 | chalk brush focus bars with ink text, dry-brush lines, torn dark panels; nothing glaring |
| 3 | in-level colour sets (27 level archives: `kl_hud_menu.py level <zip> <out>`, pinned per map, hard-link aware; fonts NOT re-baked) | kl_hud_menu.py level + a per-map install.py | **ML4** one map (DM01) to round over + shop | 'BONUS' / 'PENALTY' ink on bars, money green, penalties coral, a LOCKED shop row readable (re/hud_menu.md 7 M3) |
| 4 | sounds: 4a OSD record swap (themed `Scenes\kaneandlynch.WHD/.WAV` copies in the overlay), 4b level pairs if the global pair is not what plays in a level, 4c MenuLoop_01 as menu music (stream record) | `kl_menu_sounds_1109.py` (3.3, 9) | **ML5** = ML1 with the `[Echo]`-style voice probe log on (klechoprobe names the wave of every UI voice: 'SFX/OSD/Up_Down.wav' lines) | the probe names the OSD waves as before (same records), the owner hears Dead Men's clicks; no silence on navigate / confirm / back |
| 5 | toggle: klslot.c `_deadmen` variant step + `[MenuLook] DeadMen` (DLL default 1) + folded Mod settings row (`KLSTexLook`) + Tk row + ini line; `install.py --variant` | klhook (c9 / 81), mkoverlay.py, klset.c, kl_mod_options.py | **ML6**: ini `DeadMen=0` -> stock look (log 'menulook: ... variant not used'), `DeadMen=1` -> themed; flip the row in Mod settings, one round, back at the menu = flipped look (or at the next start) | both states clean; the row writes the key; `kl_tests --py` + `--check-rec` / `--check-ini` agree |

Undo order when several stages are live: the LAST installed first (each install.py pins the file it found, so out of order refuses).

### 5.1 Risks

1. **Double bake**: the LEVEL archives already carry `kl_hud.py all --look deadmen` fonts (re/hud_install.md 2); the stage tool never
   opens a level archive. The MENU scene's fonts were never baked (hud_menu3 was not installed; the live scene is the portraits build
   30e0fd90 / later), and a bake from a baked file is idempotent anyway (page 0 and records rebuilt from scratch, explicit px). The
   risk is a bake with the WRONG input: `pins.json` + `--accept-input` make the local session own that decision.
2. **Wider glyphs**: Impact capitals vs stock lower case: a long leaderboard name or lobby row may run into the next column
   (re/hud_menu.md 11.5 item 1); `widths.txt` / `fontsheet.png` before ML1; the fix is px or `TextWidth=`, never an element.
3. **Table**: nothing moves (signature equality is enforced); the live count stays what it is. A later in-game row must be a
   folded one (4.2) until TableLog says otherwise.
4. **Scope**: `menu/ingame.xml` and the scene reach the campaign's pause / options and the 9 stock maps' pages too (re/hud_menu.md 6
   risk 1) - the owner asked for "the whole in game menu UI", so that is wanted; it is said here so nobody is surprised.
5. **Which of two same-named colour sets wins** is not established (risk 2 there): the bluish second `Default` is left alone, so some
   in-level text may keep its stock colour.
6. **Rows12 staleness**: a themed `Patch01.zip` newer than `Patch01_rows12.zip` silently drops the 12-row lobby (klslot.c 981-982):
   the tool themes BOTH and install.py writes Patch01.zip first; `--check` warns when rows12 is older.
7. **Faces**: Anton / Montserrat only when `<work>\fonts` has them (GDI private fonts); otherwise Impact / Segoe UI Black - the owner's
   look of 10-11 WAS Impact, so stand-ins are not a downgrade. Glyph coverage of accented names is unchecked (GDI falls back).
8. **Sounds** (stage 4): record offsets must not move (the `.SND` points at them); a rate / channel mismatch = a chipmunk click; the
   tool resamples to the DD record's format and refuses when the rebuilt stock part is not byte-identical.
9. **Toggle** (stage 5): a variant step in `kls_map` runs on every open: the 4-name test must be a cheap tail compare (as the slot key
   `strstr` is), and the `_deadmen` file must be a COMPLETE archive (as the overlay's).
10. Everything here is a first look for the owner: taste calls (chip amount, bar alpha, smear darkness) are the constants at the top
    of the tool and `kl_hud_menu.py`, not code.

## 6. Open questions (for the local sessions)

1. The exact `<ColorSet>` names and hex values of the live three XML files (`inventory`).
2. The `SFX/OSD/` names (how many click kinds) and Dead Men's `SFX/UserInterface/` short clips, with rates.
3. Is the global `kaneandlynch.WHD` pair what plays UI clicks INSIDE a level (dump offsets say yes; GUESS)?
4. Live table count with Rows12 + HostOpts (`[Menu] TableLog=1`, one main-menu visit).
5. Does `kaneandlynch.zip` hold `kaneandlynch.SND` (level layout) - matters only for stage 4c.

## 7. Files

- `re/menu_look_1109.md` (this), `tools/kl_menu_look_1109.py` (stage 1 + `inventory` + `check`), `tools/kl_menu_look_1109_test.py`
  (synthetic data: 40+ checks), `tools/kl_menu_sounds_1109.py` + `_test.py` (stage 4, section 9; 104 checks), klslot.c / klset.c / mkoverlay.py / kl_mod_options.py edits (stage 5).

## 8. How to run + bench (local sessions, owner away)

```
:: 0. read-only: what the live overlay holds (colour sets, fonts, rows12 state)
python tools\kl_menu_look_1109.py inventory

:: 1. stage (reads <DD>\KLExpansion\Overlay\Patch01.zip, Patch01_rows12.zip (if there), Scenes\kaneandlynch.zip; writes
::    C:\kl_build_1024\menulook_1109\stage1\...; first run records the input md5s as the pins)
python tools\kl_menu_look_1109.py stage --accept-input              (add --bars for stage 2; --face anton if <work>\fonts has Anton)
python tools\kl_menu_look_1109.py check C:\kl_build_1024\menulook_1109\stage1   (table signature per file, fonts, rows12 mtime order)
:: look at stage1\fontsheet.png and stage1\widths.txt (rows wider than their stock text by > 15 % are listed first)

:: 2. rehearse, then install (game closed)
python C:\kl_build_1024\menulook_1109\stage1\install.py --dry
python C:\kl_build_1024\menulook_1109\stage1\install.py --game D:\scratch\dd_copy      (round trip with --undo, md5s byte-exact)
python C:\kl_build_1024\menulook_1109\stage1\install.py                                 (live; backups <name>.before-menulook_1109)
:: undo: python ...\install.py --undo

:: 3. bench ML1 (menu only; TEST hook, [Menu] TableLog=1, shots every 2 s): main menu -> Options -> Mod settings -> back -> Arcade ->
::    Dead Men maps -> Heister -> Guns -> Leaderboards -> Online -> LAN lobby -> back; mouse over entries + a map picture + the background 30 s.
::    Look at: MainMenu, OptionsMenu, Mod settings (the long 'Lens glare / cracks' label), HeistPlayMenu2, KLHeister, FALobby (12 rows),
::    leaderboard columns. PASS = no fault, 'menu: table N' unchanged, no row over its column, headlines clear of lines.
:: 4. bench ML2 (one Arcade round on DM01 to round over; kl_bench_1106 kit, 480 s): pause (Esc), shop page I, F6 page II, F3 hire,
::    F2 MOD CONTROLS, Ready, round 2. PASS = pages as before (level files untouched), prices readable, 0 faults.
```

## 9. Toggle implemented (2026-11-09, cloud, OFFLINE: not built, not run)

Stage 5's hook side exists as code (track T9). Nothing was compiled with cl, no DLL was built, nothing ran in the game; the pure logic was
syntax-checked with gcc (native) and run as a 64-bit host binary (107 checks, 0 fails); the repo's ILP32 path (`gcc -m32`, `kl_tests.py`)
could not run in the cloud (no 32-bit libc). The in-game Mod settings row (the folded `KLSTexLook` option of 4.2: klset.c + mkoverlay.py +
a regenerated overlay) is NOT part of this: it needs the overlay rebuilt and a table count, so it stays a later step; the Tk row is in.

Files: `klhook/klmenulook_logic.h` (decision), `klhook/klmenulook_test.c` (kind 'logic' in `tools/kl_tests.py` C_TESTS), `klhook/klslot.c`
(the step), `klhook/KLHook.ini` (`[MenuLook] DeadMen=1 (recommended on)`), `tools/kl_mod_options.py` (row `menulook`, G_GFX, recommended on;
`kl_mod_options_test.py` 77/0, `--check-rec` / `--check-ini` / `--check-defaults` agree).

Behaviour (`[MenuLook] DeadMen`, DLL default 1, read once in `kls_init` beside `[BotGate]`; needs `[Expansion] Enable=1` like every path step):
in `kls_map`, after the path is final, the open of one of these NAMES (case-insensitive, any directory) is answered with `<dir>\<stem>_deadmen.<ext>`
when that file exists, else with the path as it was:

| The game opens | After alias / overlay (what the step sees) | Themed copy tried |
|---|---|---|
| `<DD>\Patch01.zip` | `Overlay\Patch01_rows12.zip` (Rows12 alias) or `Overlay\Patch01.zip` (overlay) or a MountFirst file `Patch01_<x>.zip` or the stock file | `<same dir>\<same stem>_deadmen.zip` |
| `<DD>\Scenes\kaneandlynch.zip` | `Overlay\Scenes\kaneandlynch.zip` or the stock file | `kaneandlynch_deadmen.zip` beside it |
| `<DD>\Scenes\kaneandlynch.WHD` / `.WAV` | overlay copy or stock | `kaneandlynch_deadmen.WHD` / `.WAV` beside it (each file decided alone; stage BOTH) |

Decision table (klmenulook_logic.h `klml_variant`): off -> stock, nothing probed; not one of the names (also `*`/`?` patterns, no extension) ->
stock, no probe (a tail compare only: risk 9 of 5.1); stem already `_deadmen` -> stock (no double suffix); sibling path would not fit MAX_PATH ->
stock; sibling missing -> stock; else the sibling. Three call sites in `kls_map`: the MountFirst / Rows12 alias return, the overlay return, and the
stock fall-through (`!wild`, before the Log=2 'open' note). Redirect targets (level files under `Scenes\Locations\`) never reach it.

Log lines (one per distinct file AND outcome, 16-entry once-table under `kls_cs`; `klog`, prefix `menulook:`):
- `menulook: on - the menu files ... open their <stem>_deadmen.<ext> copy ...` / `menulook: off ([MenuLook] DeadMen=0) - ...` at init
- `menulook: CreateFileA <path> -> <sibling>` when swapped
- `menulook: CreateFileA ON but no <sibling> beside <path> - stock look (tools/kl_menu_look_1109.py install.py --variant writes it)` when missing
- `menulook: <api> <path>: variant path too long - stock look` (theoretical)

GUESSES in the code: a key change applies at the next game start (the files are re-opened at each scene load, so maybe the next menu load; the
.WHD/.WAV pair may be opened once per process); the `_deadmen` file must be a COMPLETE archive / pair as the overlay's is.

Build + bench for the hook owner (ML6 of section 5):
```
:: 1. self-tests (Windows: cl path) - klmenulook_test.c must PASS, kl_mod_options_test.py PASS
python tools\kl_tests.py
:: 2. build SHIP + TEST twin (klhook\build.bat, klhook\build_auto.bat); pin md5s in the install kit as every 1108 kit did
:: 3. one themed sibling beside the LIVE overlay pair (nothing live changes): stage 1's install.py --variant
python C:\kl_build_1024\menulook_1109\stage1\install.py --variant --dry
python C:\kl_build_1024\menulook_1109\stage1\install.py --variant        (writes Overlay\Patch01_deadmen.zip, Patch01_rows12_deadmen.zip, Scenes\kaneandlynch_deadmen.zip)
:: 4. TEST hook, [MenuLook] DeadMen=1 (or the key absent): main menu -> Options -> Mod settings -> Arcade -> Dead Men maps -> back; shots every 2 s.
::    PASS: KLHook.log 'menulook: CreateFileA ...Patch01_rows12.zip -> ...Patch01_rows12_deadmen.zip' + the kaneandlynch.zip line, no 'ON but no',
::    'menu: table N' unchanged ([Menu] TableLog=1), capitals in rows, 0 faults; the .WHD/.WAV lines say 'ON but no' until stage 4 ships the pair (expected).
:: 5. flip: DeadMen=0 (KL Mod Options row 'Dead Men menu look' off), restart -> stock look, NO 'menulook:' per-file line at all, 'menulook: off' at init.
:: 6. undo: install.py --variant --undo (removes the copies, md5-checked); the DLL/ini undo of the kit.
```

## 9. Stage 4 tool: `tools/kl_menu_sounds_1109.py` (written offline 2026-11-09, test 104/0, NOT run on a game file)

What it does (3.3 made concrete): a themed COPY `Scenes\kaneandlynch_deadmen.WHD` + `.WAV` of the global pair in which ONLY the
mapped `SFX/OSD/*` records' sample data is Dead Men's (decoded -> channel fit -> windowed-sinc resample -> peak match -> the record's
own codec: IMA ADPCM through `kl_gunsnd.ima_encode`, or 16-bit PCM). Names, record offsets and every other record stay byte for byte;
the tool REFUSES when the untouched part is not byte-identical (proofs in its docstring; `kl_gunsnd.check_bank_preserved` agrees).
Record fields are read through `kl_whd` (DD_F / DM_F); the Dead Men side opens every `.WHD` under `<DM>\Scenes` (front-end first,
GUESS `KaneAndLynch.WHD`, then the level banks) and `PC_Def.str` (`kl_launcher_music.Stream` + its PCM / IMA / Vorbis chain).
Length rule DEFAULT "grow" (the whole Dead Men clip; a longer one is appended to the `.WAV`, pcm / size / samples / off follow, as
`kl_gunsnd.rebuild` did in the 42 live gun banks); `--keep-length` trims (5 ms fade) / pads to the stock frame count so the `.WHD`
stays byte-identical (first fallback if a grown bank misbehaves). GUESSES: which record is which click (name pairs), the global pair
plays in a level too, sinc parameters, peak match, `.SND` wave seconds stay stock.

The toggle exists in the tree: klslot.c `[MenuLook] DeadMen=1` (DLL default 1, klmenulook_logic.h, NOT run live) opens
`<stem>_deadmen.<ext>` beside `Scenes\kaneandlynch.WHD / .WAV` when it exists - exactly what `install.py` (variant) writes. When an
OVERLAY copy `KLExpansion\Overlay\Scenes\kaneandlynch.WHD` exists the step looks for the sibling THERE (klslot.c 596):
`install.py --overlay-variant`. `install.py --overlay` instead writes the STOCK names into the overlay folder (plays with
`[Expansion] Overlay=1` and any DLL, no toggle). The stock pair is never written (asserted on every path); undo removes only files
with the staged md5.

```
:: 1. probe (read-only): the OSD records of the live global pair + Dead Men's short UI-looking clips; writes probe.json / probe.txt /
::    mapping.json (TEMPLATE: GUESS pairs by name, '_candidates' per record, null = leave stock) under C:\kl_build_1024\menusounds_1109
python tools\kl_menu_sounds_1109.py probe --dd "C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days" --dm "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men"
::    read probe.txt: how many SFX/OSD/* records (Up_Down, Menu*, confirm / back / error / slider?), their rate / ms; which Dead Men
::    names are the clicks (SFX/UserInterface/*, < 3 s; MenuLoop_01 is the LONG theme, never a click); which .WHD held them (the
::    "opened" list). Paste the OSD list + the Dead Men UI list into this doc (6. open question 2).
:: 2. edit mapping.json: value = Dead Men clip name, or {"clip": name, "gain_db": -3, "level": "none"}; null keeps the record stock.
:: 3. stage (first run on the PC: --accept-input pins the stock pair's md5s); --previews writes previews\<record>_{stock,deadmen}.wav
::    for the owner's ear BEFORE anything is installed; --keep-length / --linear / --rail / --level none are the fallbacks
python tools\kl_menu_sounds_1109.py stage --dd "<DD>" --dm "<DM>" --accept-input --previews
python tools\kl_menu_sounds_1109.py check C:\kl_build_1024\menusounds_1109 --dd "<DD>"       (re-runs every proof: must say PASS)
:: 4. rehearse on a scratch copy of <DD> (only Scenes\kaneandlynch.WHD/.WAV + KLExpansion\Overlay are needed in it), then live
python C:\kl_build_1024\menusounds_1109\install.py --game D:\scratch\dd_copy --skip-run-check   (+ --undo: siblings gone, stock md5 unchanged)
python C:\kl_build_1024\menusounds_1109\install.py --dry
python C:\kl_build_1024\menusounds_1109\install.py            (variant siblings beside the stock pair; --overlay-variant when an overlay copy exists)
:: 5. bench ML5 (TEST hook with the [MenuLook] step, [MenuLook] DeadMen=1, [Echo]-style voice probe on): main menu -> up / down x5 ->
::    Options (confirm) -> back (Esc) -> a locked / refused action (error) -> Arcade -> back; then one Arcade round's pause (Esc) + shop.
::    PASS: KLHook.log shows, once each, 'menulook: <api> <DD>\Scenes\kaneandlynch.WHD -> <DD>\Scenes\kaneandlynch_deadmen.WHD' and the
::    same for .WAV (a 'menulook: ... ON but no ...kaneandlynch_deadmen.WHD beside ... - stock look' line = install.py did not run or ran
::    into the wrong folder; 'menulook: off ([MenuLook] DeadMen=0)' at start = the key is off); the echo-probe lines still name the same
::    waves ('SFX/OSD/Up_Down.wav' on navigate: same records, new data); the owner hears Dead Men's clicks, no silence, no chipmunk
::    (a wrong rate would be one), no fault / assert; with DeadMen=0 the stock clicks are back. In a level (pause / shop) the clicks are
::    Dead Men's too if GUESS 3.1 holds (the global pair stays loaded); if stock there, stage 4b (level pairs) is needed.
:: undo: python C:\kl_build_1024\menusounds_1109\install.py --undo   (removes only the siblings it wrote, md5-checked)
```
