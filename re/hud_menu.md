# The menu pages and the round-over board in the new look (track M, 2026-10-11; review round the same day)

Tool: `tools/kl_hud_menu.py` (apply / level / check / check-level / diff / sheet / abi). Builds: `<work>\build\hud_menu2\`.
NOTHING HERE HAS RUN IN THE GAME and nothing is installed. Words: READ = read in kl2.exe (debug\dasm.py, tools/kl_exe.py
+ capstone) or in the files as stated; RAN = the tool was run offline; ASSUMED / GUESS = not established.
The review is `re/hud_menu_review.md`; what was done about each finding: section 9.

## 0. Summary

1. The menu XML can change a page's colours (through colour sets), fonts (by name), positions, fades, and which
   existing picture an element shows. It cannot add a picture, a colour that depends on game state, a data text, or
   an element without moving the menu manager's table (section 1.1).
2. `apply` restyles every page of the three XML files and repaints the menu scene's focus bars and separator
   lines as brush strokes, WITHOUT adding or removing one element, colour set, entity, chunk or texture id.
   `check` proves the table of each file is the reference's.
3. The pages inside a level (round over, shop, status, pause) take `online.xml` and their bar / line textures from
   the LEVEL archive, not from the overlay. `level` does the same restyle on one level archive; `check-level` tests it.
4. The fault class of the 14:24 menu crash is now whole: the cursor over the button `DefaultFocus` asks for table
   entry **5000**. A load set must keep its live count at 5000 or less. The live counts are NOT KNOWN: live check
   K0 (a log line, section 8) reads them, also during the owner's own play.
5. The draft's round-over board is a heister list; the Arcade page the game opens (`HeistStatus`) is a bonus /
   penalty sheet. The sheet is restyled by default. `level --board` adds the crew (name, empty fate block, score)
   under it in ONE level archive: 48 new elements, a table shift, only after K0. `apply --board` is refused.
   Fate, the traitor row's colour, lives as skulls and the continue ring need hook code (section 5).

## 1. What was established

### 1.1 The table and the 14:24 crash class (READ)

- The menu manager is `[[0xdd265c]+0x824]` (ZMercsMenuElements, vtable 0xbb7dc8). It holds one table of 5096
  pairs `{object, kind}` from +8 and a count at +0x9f48. An entry is made for every created `<GuiElement>` (kind 0:
  0x7fad5d `[mgr+count*8+8] = element`, 0x7fad67 kind, the element keeps its index at +0x5c, `cmp ecx,0x13e8 / jge
  -> int3` at 0x7fad8d), every `<Window>` (kind 1, 0x667e5e), `<ColorSet>` (kind 2, 0x47d641) and `<ButtonGraphic>`
  (kind 3, 0x53c781). Order = file order, the files one after the other (frontend.xml + online.xml in the menu;
  ingame.xml + online.xml in a level; re/menus.md 1).
- 0x8d1c10 `(index)`: `index < [this+0x9f48] ? [this+index*8+8] : 0`.
- The window system (ZXMLGUISystem, `[mgr+4]`) keeps THE SAME manager at its +0x4b4: `mov eax,[0xdd265c] / mov
  ecx,[eax+0x824] / mov [esi+0x4b4],ecx` at 0x8a43c7..0x8a43d8 (the routine that also clears the window stack
  +0x328 / +0x32c). So the table 0x861720 reads is the one the XML loader fills - no longer an assumption.
- ZXMLGUISystem slot 25 = 0x861720 (the crash's function): takes the object under the cursor
  (`this->vtbl[0x88]()->vtbl[0x288]()`), tests `vtbl[0x30]() & [0x15399e4] == [0x15399e0]`, takes `id = vtbl[0x2b0]()`,
  `index = id & 0xffff`, `obj = 0x8d1c10([this+0x4b4], index)` and, for a non-null obj, calls `obj->vtbl[0x84]()`
  (0x8617fe, 0x861824, 0x8618b7). There is NO test of the entry's kind.
- ZBaseWindow's vtable 0xbaf6c4: `[+0x80] = 0`, `[+0x84] = 0x3f800000`. A window at the index = a call to 0x3f800000.
- WHERE THE ID COMES FROM: ZBUTTON (vtable 0xbabc3c) `[+0x2b0]` = 0x83d5d0 = `mov eax,[ecx+0x60] / ret`. In the
  menu scene (READ in `hud_mappics\Overlay\Scenes\kaneandlynch.zip`, .gms + .prp) there are 121 ZBUTTON entities
  (type 0x100033); 120 carry eight zero integers, ONE carries `0, 5000, 0, ...`: `ZWINDOWS\Menu\DefaultFocus`.
  The review read the dump of 14:24: `ebx = 0x1388`, `ebp` -> a ZBaseWindow. INFERRED, not read in the loader:
  that this property is what lands in `[button+0x60]`. NOT ESTABLISHED: who writes `[button+0x60]` of the 120
  pool buttons at run time (they get an element's index from somewhere; with 0 they would ask for entry 0).
- SO: whenever the cursor is over `DefaultFocus` (GUESS: the catch-all behind a page) the game asks for entry 5000.
  With 5000 entries or fewer it gets 0 and nothing happens - stock. Past 5000, entry 5000 is whatever the XML put
  there: an element takes a stray hover; a window, colour set or button graphic is called through a vtable not
  made for it. The 14:24 package had grown the table past 5000 with a `<Window>` on 5000.
- **THE RULE: per load set, live count <= 5000, or entry 5000 is an element. The budget is 5000, not 5096.**
  The live counts are NOT KNOWN (the tag counts of the files, 4342 + 1889 for the menu, are over 5096: `<Platform>`
  blocks and uninstanced templates drop out; re/menus.md open question 3). K0 reads them.
- THE GUARD IN THE TOOL: `apply` keeps the table as it is (sufficient: count and every index unchanged), and
  `check <overlay> <reference>` proves it per file (the sequence of Window / GuiElement / ColorSet / ButtonGraphic /
  Template tags with Name, Type, Template, the conditional blocks, Text / Graphic children). A table that grew is a
  FAIL unless `--menu-count N` (`check`) or `--level-count N` (`check-level`) gives the live count and N + new <=
  5000. `apply --board` is refused outright.

### 1.2 What the XML can restyle (READ in the three files; attribute readers per class: re/menus.md 2.3)

| Thing | How | Limit |
|---|---|---|
| text colour | `ColorSet="Name"` on the element or its template; a `<ColorSet Name NormalColor FocusColor DisableColor>` (ARGB hex; the reader at 0x8ab978..0x8ab988 takes exactly these three names with sscanf). 12 sets per file | No colour attribute on an element. A NEW set is a new table entry. Sets are found by name over all loaded files (online.xml uses `White`, which only frontend.xml / ingame.xml define); which of two same-named definitions wins is NOT established (online.xml defines `Default` twice, every file `Legend` twice) |
| a value's text colour on a toggle row | `RecCSFocus` / `RecCSDefault` (set names) | same |
| slider colours | `ColorSetValue` / `ColorSetBackground` | same |
| font | `Font=` one of the scene's fonts: Button, Text, DebugText, Menu, Header, H3, H2, H1 (stock also writes `Buttons`, which is none of them) | glyphs are the scene's atlases (tools/kl_hud.py bakes them; `<work>\build\hud_menu`) |
| place, size, alignment | `X Y W H AlignH AlignV AnimX AnimY TextWidth LineSpace Priority GeomSpace` | - |
| fades, flicker | `FadeIn* FadeOut* AlphaMin AlphaMax Flash* Jitter* Flicker*` | - |
| which picture | `Graphic="N"` = an entity of the scene that is loaded (menu scene: `LocalResources\Graphic`, `GenericMenuResources`; level: the level's copy under `MenuFA.zip`) | an entity stands in one place; a new picture = new entities in the scene (kl_portraits) |
| a picture's look | not XML: the entity's ZWINPIC -> picture chunk -> sprite chunks -> textures (kl_portraits' docstring) | the bars are 1024 x 32 in two 512 x 32 tiles; tiles are SHARED between families (section 2) |
| data text | `TagName=` of a `MercsShowInfo*`; 191 names, compiled in | no new tag |

`DisabledColor` (online.xml's last four sets: the second `Default`, `WANTED`, `DirtyMoneyColorSet`, `Black`) is a
misspelling nothing reads: kl2.exe has the string `DisableColor` (0xb2c8b4, one reference, 0x8ab988) and no
`DisabledColor`. Those sets have whatever disabled colour the constructor gives (not read).

Stock facts the restyle leans on (READ): the focus bars are DXT5, grey 167 at alpha 246, drawn with
DRAWMODE_OPACITY and the XML's `AlphaMax` (192 on a menu entry, 64 on status / leaderboard rows, 255 on the shop's
`WeaponBuyFB` and the lobby's static bars); the separator lines are 'ABGR' textures with ONE row of grey 26 on
opaque black and another draw-mode word (GUESS: additive); `MenuFocus_long` is DXT1 (flag 0x4000) and
`FocusBar_medium_02` has a dark groove drawn into it - both left alone.

### 1.3 The pages and the code behind them

| Page | XML window (file) | Opened / filled by (READ unless marked) |
|---|---|---|
| Arcade round over | `HeistStatus`; with a leaderboard `HeistStatusLeaderboard` (online.xml) | opened by name through 0x7ed9a0 at 0x4970a6 / 0x4970c0 / 0x4970de (one routine that also opens `FAStatus` 0x49711f, `FAStatus_Team` 0x497105, `FARoundSummary` 0x49703c, `IngamePauseFA` 0x496ffc). Every number on it is a `MercsShowInfoFA` tag (`HeistPoints*`, `HeistBonusRound`, `HeistPenaltyRound`, `HeistRoundsCounter`, `MoneyTotal`); the labels are .LOC keys under `AllLevels/Menu/Heist/Status`. Ready / Buy weapons: `MercsFAStatusReady` (vtable 0xbbd84c, input 0x7557f0) |
| Arcade game over | `HeistStatus_EndGame`, `HeistStatusLeaderboard_EndGame`, then `HeistHighscore` | `HeistStatusLeaderboard_EndGame` is named at 0x864904; `HeistStatus_EndGame` and `HeistHighscore`'s opener were not found as strings with a reference (NOT established who opens them). `HeistHighscore` rows: tags `HeistLLBRank / GamerTag / TotalMoney`, `MercsHeistHighscoreReady` (0xbbd7ac) |
| Buy weapons | `FABuyWeaponsNew`, `...Category`, `...Weapon`, dialog `BuyWeaponDialog` | `FABuyWeaponsNew` opened at 0x7558ce (inside `MercsFAStatusReady`'s input routine: 'opened via code', the XML's own comment), `BuyWeaponDialog` at 0x7f7586. Rows: `MercsFASelectorWeapons` (0xbbd494), `MercsShowInfoFAWeapons` (update 0x50c630) - the list, prices, locks and stat bars are drawn by that code into the XML's elements |
| Status during a round | `FAScore` | tags `StatusPlayerNameIngame`, `StatusTotalIngame`, ... (opener not looked for) |
| Dead / respawn / escaped | `FADead`, `FADeadNoPIP`, `FARespawn*`, `FAEscaped` | named in the list at 0x704141.. ; tags `KilledBy`, `YouRespawnAs`, `YouFollow`, `RoundGrab`, `RoundSplit` |
| Pause | `IngamePauseFA` (ingame.xml), `IngamePauseHeist` | `IngamePauseFA` at 0x420988, 0x496ffc, 0x7ea150; `IngamePauseHeist` has no string in the exe (reached from XML or not at all: NOT established) |
| Lobby / waiting | `FALobby` (frontend.xml), `FAWaitForPlayers` (online.xml) | 0x54d788, 0x74c1bf / 0x4bd1f0, 0x74c532; `MercsFASelectorLobby`; the lobby elements the code looks up by name are in KNOWN_ELEMENTS of the tool |
| Front end | `MainMenu`, `HeistModeMenu`, `HeistPlayMenu` (+ mkoverlay's `HeistPlayMenu<N>`, `KLHeister`, `KLGuns`), options | XML; re/menus.md 4 |

The data elements: `ZMercsShowInfoFA` vtable 0xbbcd1c, slot 8 (per-frame update) = 0x5b5f40, one long chain of tag
compares (0x57a5a0) that reads the rules object through `0x7bb2a0([0x168e9e4])` and its VIRTUAL slots.
0x7bb2a0 returns the rules object (`[ecx+0x54]`) only while `[[0x168e598]+0x5c] == 4` - the mode klbalance.c calls
Arcade - and 0 otherwise. So the per-player tags answer in Arcade through ZGameRulesHeist's own slots (vtable
0xbd3514); what the multiplayer pages get was not looked at.

THE ROW TAGS (READ, section 4 leans on it): `PlayerIndex` is a ROW of the game's own ordering, not a record number.
- `StatusTotal` (0x5bb45e): row < `session->vtbl[0x48]()` (0x698250 on `[0x168e598]`, set up at 0x5b6198) and
  `0x4fed60(row) != -1`; then `record = rules->vtbl[0x188](row)` (or `vtbl[0x184](row, team)` with a `Team` attribute
  at +0xf8), `0xff` = nothing printed.
- `StatusPlayerName` (0x5bb7df): in mode 2 (`0x87c980`) another path; otherwise row < `rules->vtbl[0x50]()`, then
  THE SAME `rules->vtbl[0x188](row)` (0x5bb8bb) and the name of that record by 0x67f300.
- ZGameRulesHeist slot 0x188 = 0x5a0fa0: `[rules+0x1d4] == 0 -> 0` (record 0 for every row while the order is not
  made); else `row < [rules+0x35c] ? byte [[rules+0x368]+row] : 0xff`. A plain byte table.
So in Arcade name row k and score row k ARE the same heister (both through slot 0x188; their row limits come from
two different counts, not compared), and the record behind row k is `byte [[rules+0x368]+k]`.

`python tools/kl_hud_menu.py abi <kl2.exe> <overlay>` lists the window and element names of the XML that the exe
holds as a string with a reference (59 + 40 on 2026-10-11; baked as KNOWN_WINDOWS / KNOWN_ELEMENTS). A LOWER BOUND:
a name need not stand in the exe that way (the colour set `White`, named by 87 elements, has no such string). For
that reason `check` also fails on ANY window or element name of the reference that is gone.

## 2. What `apply` changes (RAN; `diff <hud_mappics> <hud_menu2\Overlay_nofonts>` prints it)

Colour sets, every definition (the diff lists both definitions of a doubled name): white -> chalk f3f0ea, black ->
ink 0c0c0d, grey -> 8d8982, bright red (Header d7373a, the PC legend's focus d00000) -> coral f0475a, dark red ->
8c3138; alpha kept. Colours of another kind (online.xml's second `Default`, 829EC1; its focus white does become
chalk) and the two malformed stock values are left as they are.
Spare sets (named by no XML element of the three files - that code never asks for them by name is NOT shown):
`Debug` (all three files) and `DirtyMoneyColorSet` -> green 63a65b / 63a65b / 4f8f49, `WANTED` -> orange e8831f /
e8831f / 8c3138, `Black` -> ink. Their alpha is ff ON PURPOSE (stock `Debug` 80 normal, stock `WANTED` 00
disabled). The three of online.xml get a real `DisableColor=` ADDED (an attribute on an existing tag: no table
entry); their dead `DisabledColor=` is left as it stands. The second `Default` gets none: adding one would change
the disabled colour of in-level text that may use that definition today.

| Page | Changed | Cannot be done in XML -> what it needs |
|---|---|---|
| every page | text chalk, headings of the set `Header` and the legend's focus coral, disabled grey; the focused entry's bar a chalk brush stroke with ink text; separator lines dry-brush | a painted bar BEHIND A HEADLINE: a new Graphic element per page (table shift) and a picture entity for it |
| Arcade round over / game over (`HeistStatus*`, 4 windows) | the 'Bonus' / 'Penalty' headings (set `OnFocus` = INK, not coral) sit on brush bars (they already had a bar); bonus values, round and total score green (8 / 11 per window); yellow card, civilians, penalty total coral (3); the traitor label and value orange (2) | the heister list of the draft (`level --board`, section 4); fate text; the traitor ROW in orange and the own row painted (state the XML does not know); lives as skulls; 'killed by' (the tag exists, placing it is a new element); the continue RING (hook draw; the countdown number exists as tag `NextRoundIntCounter`, on FAStatus only) |
| multiplayer round over (`FAStatus*`, templates) | split / rewards / total columns green (50 template rows) | as above |
| dead / respawn | `KilledBy` coral (5) | respawn ring |
| escaped | `RoundGrab`, `RoundSplit` green | - |
| shop | `PackagePrice` green (2; it stands under the list at Y 470, on no bar); bars and lines. The 15 `WeaponBuyFB` bars are `AlphaMax="255"`: fully opaque chalk where stock had mid grey | locked guns dimmed and stat bars are drawn by `MercsShowInfoFAWeapons` / `MercsFASelectorWeapons`; whether a locked row's text is readable on opaque chalk is NOT ESTABLISHED (M3). Their pictures are level art (`WeaponShop*`), not touched |
| profile, leaderboards (frontend.xml) | money columns green (44, set `Debug`) | - |
| key assignment | its bar `AssignKeyFocus_long` shares tiles 958 / 959 with `FocusBar_medium`: chalk too; its set `AssignKeys` has ink focus text | - |
| pause, options, lobby, map pages, Heister, Guns | colours, bars, lines only | sliders / switches of the kit: the slider is code (`ZGUISlider`) with two colour sets; map picture in a chalk frame: a frame entity + one element per page |

Pictures (menu scene `.TEX`, 22 textures: 15 bar tiles, 7 line tiles; `sheet` draws them:
`<work>\build\hud_menu2\sheet.png`, LOOKED AT).
- Bars, `--bars kit` (default; `_stroke_kit`, constants BAR_*): each bar tile keeps its extent and mean alpha and
  becomes SOLID chalk: the top and bottom edge hold their height over runs of 20-40 px and step by one pixel
  between runs; an end where the bar ends inside the tile is a hand-cut slant of 2-4 px with a step every few
  rows; 2-3 dry streaks, one row high and 14-44 px long, start AT a cut end and fade back into the paint. No
  pinholes, no cuts through the bar. Format DXT5 -> one-mip 'ABGR' (ASSUMED fine: stock icons are ABGR).
- Bars, `--bars hud`: tools/kl_hud.py's own stroke painter (`kl_hud._extra_pixels('stroke', ...)`, HUD picture 111)
  BY IMPORT, cut to the bar. Built for comparison only (`Overlay_nofonts_hudbars`, `sheet_hudbars.png`): at menu
  size it is the barcode the review describes (a full-height cut every ~42 px, 1.5 % pinholes, per-column edge
  noise). FOR THE HUD SESSION: the same painter makes HUD pictures 111 / 112; nobody has seen them in the game.
- Lines: two rows of chalk x 0.34 / 0.19 with short gaps on the stock's opaque black (LINE_*). The round-over page
  draws lines in PAIRS 3 px apart (AnimY 309 / 312, 352 / 355, 395 / 398): rows y, y+1 and y+3, y+4 leave one
  virtual pixel between them. If they close into a band in M3: LINE_ROWS = 1.
- NOT repainted (stock look stays beside the chalk): `FocusBar_medium_02` (26 uses in frontend.xml; the grooved
  3-D bar), `MenuFocus_long` and `FAFocusBar_long`, which shares its DXT1 tiles. `FocusBar_tap_01 / _02` (1001 /
  1002) ARE repainted.

## 3. Builds (RAN 2026-10-11 21:20; nothing installed; sha1 = first 8; rebuilding gives the same bytes)

| Folder under `<work>\build\hud_menu2` | Made from | Patch01.zip / scene (or archive) | check |
|---|---|---|---|
| `Overlay_nofonts` | `hud_mappics\Overlay` (THE INSTALLED ONE) | 5bfa600f / cddfb8b2 | `check` PASS 0 notes: table identical in all three files (4342 / 1593 / 1889 tags), 22 textures differ, every other scene member identical. FIRST RUN: it separates this track from the unproven menu fonts |
| `Overlay` | `hud_menu\Overlay` (menu fonts baked; itself never run) | f4446575 / bad4635c | PASS 0 notes |
| `Overlay_online` | `hud_menu\Overlay` + `--online-in-patch` | d6e1b4dd / bad4635c | PASS, 1 NOTE (Patch01.zip gains `Menu/online.xml`) |
| `Overlay_nofonts_hudbars` | `hud_mappics\Overlay` + `--bars hud` | 5bfa600f / ba251e56 | PASS; comparison only, not proposed |
| `level_DM03\F03_Main.zip` | `hud_new\DM03\F03_Main.zip` by `level` | d59bf72a | `check-level` PASS: only `.TEX` (22 textures, same ids and sizes) and `Menu/online.xml` differ; table identical; the online.xml is byte-identical to the overlay's |
| `level_DM03_board\F03_Main.zip` | the same + `--board` | 2253b8ea | `check-level` FAIL ON PURPOSE without a count: 'TABLE BUDGET NOT TESTED' (48 entries); with `--level-count N` PASS when N + 48 <= 5000 |
| `klhook_k0\ship`, `klhook_k0\test` | HEAD 0d16a7a's klhook + the WIRING of section 8 (scratch copy, `build.bat` / `build_auto.bat`, no warning) | dinput8.dll 6dcc03c1 / 6b1bb695 | compiled only |
| `sheet.png`, `sheet_hudbars.png` | the repainted textures | | looked at |

`Overlay_board` of the first round is DELETED (it carried the board in Patch01.zip: review finding 3).
An independent test (RAN): with every ` ColorSet=` / ` DisableColor=` attribute removed and the three colour values
blanked, each XML file of `Overlay`, `Overlay_nofonts`, `Overlay_online` equals its source byte for byte.

## 4. `level --board` (opt-in, one level archive; positions are a GUESS)

Adds to `HeistStatus` and `HeistStatus_EndGame`, before the bottom line, two columns of four rows:
`KLB_Name<k>` (`MercsShowInfoFA TagName="StatusPlayerName" PlayerIndex=k`), `KLB_Fate<k>` (an EMPTY TextBlock,
coral, for hook code to fill), `KLB_Cash<k>` (`TagName="StatusTotal"`, green, right-aligned); suffix `_E` on the
end-game page. Rows at Y 418 + 27 r (the stock tables end at 398, the bottom line is at 534); columns at the
'Bonus' / 'Penalty' headings' X (-125, 395); right-aligned X 418 / -107 are a GUESS. All in constants BOARD_*.
- Row k is the k-th heister of the game's own order; name and score of one row are the same heister (1.3).
  A hook that fills `KLB_Fate<k>` must take the record from `byte [[rules+0x368]+k]` (valid while `[rules+0x1d4]
  != 0` and k < `[rules+0x35c]`), then klb_read's record of that number - never k itself.
- NOT in it: a heading, killed-by, lives.
- It moves every table index behind `HeistStatus` in that level (the rest of online.xml: status, respawn, shop
  pages) and adds 48 to the level's count: K0 first, `check-level --level-count N`, then T1.
- Not through an overlay: an overlay's online.xml is loaded at the menu (frontend.xml + online.xml), and from
  Patch01.zip it would reach every stock level, the campaign and multiplayer.

## 5. What needs hook code (none written in this track besides the log line of section 8)

- Fate per heister ('ESCAPED', 'DEAD', 'LEFT BEHIND', 'TRAITOR'): klb_read's status and flags are the data. Two ways:
  (a) klhud draws the whole board itself while the top window is `HeistStatus` / `HeistStatus_EndGame` (the window
  stack is read by name already, klslot.c), with klu_row and the text objects - no XML change, no table question;
  or (b) fill the `KLB_Fate<k>` blocks: find the element by name (0x83faf0 on the manager, re/menus.md 2.4) and set
  its text - the text block's set-text routine is NOT read yet; rows by the byte table of section 4.
  (a) is the safer one after the review.
- The traitor row orange / own row painted / dead rows struck: per-row state -> (a) above, or message `Disable` to a
  row (it takes the set's disabled colour, 0x672ac0) for the dead ones.
- Continue ring, respawn ring, lives as skulls: klu_ring / klu_pic over the page.
- A painted bar behind headlines, a chalk frame round the map picture, tabs: new picture entities in the menu scene
  (kl_portraits' way) plus one Graphic element per use = more table entries in frontend.xml. Only with K0's count.

## 6. Risks

1. SCOPE: `menu/frontend.xml` and `menu/ingame.xml` are Patch01.zip members, so the colours also reach the
   campaign's pause / options pages and the multiplayer pages, and the menu scene's bars likewise - whenever
   `[Expansion]` mounts the overlay. That is the owner's 'for the HUD AND the menus', but it is not 'Arcade only':
   THE LEAD DECIDES. `Overlay_online` extends the colours to the stock levels' round-over pages too.
2. Which definition of a doubled colour set wins is unknown; every definition was mapped by the same rule, but
   online.xml's second `Default` (bluish) kept its hue. If THAT one is in effect in a level today, in-level text
   keeps its stock colour.
3. The four spare sets are unused BY THE XML only. `Debug`: the one string 'Debug' with a reference stands in
   a run `Debug\0Info\0W...` (a log-level table by its look; the reference was not read). `Default` has 16
   references (counted, not read): code does look some sets up by name.
4. Green / orange / coral on a data element overrides what its template says (`FAStatusTextFocus` carries `White`).
   92 elements of online.xml now use `DirtyMoneyColorSet`; one sent `Disable` shows 4f8f49.
5. A bar texture as 'ABGR' in place of DXT5; +64 KB each (the scene's .TEX grows 0.8 MB).
6. Opaque chalk bars in the shop and lobby (AlphaMax 255): text coloured by code on them (section 2).
7. The brighter separator lines assume additive drawing (brightness only: LINE_LEVEL); the pairs (section 2).
8. `--online-in-patch`: one more member in Patch01.zip (ASSUMED harmless and overriding; menus.md open question 9).
9. `level --board`: section 4; the tags may print nothing (e.g. `[rules+0x1d4] == 0` at the page = record 0 on
   every row).
10. The reference `hud_menu` has itself not run (run M0_menu_caps); `Overlay_nofonts` avoids that.
11. `check` against a reference proves 'nothing moved', not 'sound': a fault the reference has passes.
12. klauto scripts: no name changed (check: 'names of the reference are gone' = FAIL).

## 7. Live checks (owner away for all but K0; pictures every 2 s)

| Run | Set-up | PASS shows |
|---|---|---|
| K0 | a hook with the WIRING of section 8 (reads only; no overlay change, no key). Works in the owner's OWN play: the line is written after every XML load | `menu: table N of 5096 entries (... elements, ... windows, ...); M free below entry 5000; scene '...'` once at the main menu and once in a level of ours. N(menu) and N(level) are the numbers every later element needs. `OVER 5000 ... entry 5000 is a WINDOW` = the installed overlay itself is one hover from the 14:24 crash |
| M1 | `Overlay_nofonts` in `<DD>\KLExpansion\Overlay` (BOTH files), menu only: main menu -> Arcade -> 'Dead Men maps' -> back -> Heister -> Guns -> Options -> key assignment; then MOVE THE MOUSE over the entries, the map picture and the page background for 30 s (the 0x861720 path) | no fault; the focused entry on a chalk brush bar with dark text; headings coral; lines visible, not glaring; Heister pictures unchanged; K0's menu count the same as before |
| M3 | `level_DM03\F03_Main.zip` copied over the tab's DM03 archive for one run to the round-over page (put the archive back after) | level loads; `HeistStatus`: 'BONUS' / 'PENALTY' in ink on brush bars, bonus values and totals green, penalties coral, the traitor line orange, the paired lines still two lines; then Buy weapons: bars, price green, A LOCKED ROW'S TEXT READABLE on the chalk bar |
| M4 | `Overlay_online` with the tab's UNCHANGED levels, one round to round over | coloured round-over page = Patch01.zip overrides the level's online.xml (then no per-level step is needed for the XML; the bars still need `level`) |
| M2 | `Overlay` (after M0_menu_caps has passed) | as M1 with the capitals |
| T1 | only when K0 gave N(level) <= 4952 and `check-level level_DM03_board\F03_Main.zip <source> --level-count N` says PASS: that archive over the tab's DM03 for one run; a round to round over, the mouse over the page AND ITS BACKGROUND for 30 s, Ready, Buy weapons, second round | no fault anywhere behind HeistStatus; names and scores on matching rows (one known heister's money against the HUD's list), or which rows stay empty |

Order: K0, M1, M3, M4, M2, T1. A fault at 0x3f800000 from 0x8618b9 in any of them = entry 5000 is a window: `ebx`
in the dump reads 0x1388.

## 8. WIRING (klhook.c only; klhud.c needs nothing)

One read-only log function and one call. Compiled in a scratch copy of HEAD 0d16a7a's klhook (SHIP and TEST, no
warning; DLLs in `<work>\build\hud_menu2\klhook_k0`). No .text patch, no write to game memory, every read through
klh_rd / klh_rd32, the manager's vtable tested, game thread only, two guarded reads every 500 ms and one block read
per XML load. No ini key: it is a log line.

(1) klhook.c - OLD:

```c
static volatile LONG klh_game_ticks;                  /* frames of the main loop: half of the stall watch's heartbeat */
```

NEW (the function goes in front of that line, which stays):

```c
/* ---- the menu manager's table: a LOG LINE, reads only (re\hud_menu.md 8; live check K0) ----
 * READ in kl2.exe: the manager [[0xdd265c]+0x824] (ZMercsMenuElements, vtable 0xbb7dc8; the window system keeps the
 * same pointer at +0x4b4, 0x8a43d8) holds a count at +0x9f48 and {object, kind} pairs from +8: kind 0 element
 * (0x7fad67), 1 window (0x667e5e), 2 colour set (0x47d641), 3 button graphic (0x53c781); int3 past 0x13e8 (0x7fad8d).
 * 0x861720 (the mouse over the menu) calls vtable +0x84 on entry (id & 0xffff) of the object under the cursor with
 * no kind test; the menu scene's button ZWINDOWS\Menu\DefaultFocus carries id 5000. So: an entry 5000 that is not an
 * element is the crash of 2026-10-10 14:24 (a call to 0x3f800000). One line whenever the count has changed and
 * stood for 2 s (= after each XML load: the menu, a level). */
#define KLH_MENU_MGR_VT   0x00bb7dc8
#define KLH_MENU_CAP      0x13e8
#define KLH_MENU_HOT      5000
static void klh_menu_table_watch(int game_thread)
{
    static DWORD polled, seen_n = (DWORD)-1, since, said_n = (DWORD)-1, bad_vt;
    static struct { DWORD obj, kind; } tab[KLH_MENU_CAP];
    static const char *kind_name[5] = { "an element", "a WINDOW", "a COLOUR SET", "a BUTTON GRAPHIC", "of an unknown kind" };
    DWORD now = GetTickCount(), gd, mgr, vt, n, k, c[5] = { 0, 0, 0, 0, 0 };
    char scene[160];
    if (!game_thread || !klh_exe_ok || now - polled < 500) return;
    polled = now;
    gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c)); mgr = gd ? klh_rd32(gd + 0x824) : 0;
    if (!mgr) return;
    vt = klh_rd32(mgr);
    if (vt != (DWORD)(DWORD_PTR)KLH_VA(KLH_MENU_MGR_VT)) {
        if (vt != bad_vt) { bad_vt = vt; klog("menu: the manager %08lx has vtable %08lx, not ZMercsMenuElements (00bb7dc8): its table is not read", mgr, vt); }
        return;
    }
    n = klh_rd32(mgr + 0x9f48);
    if (n != seen_n) { seen_n = n; since = now; return; }
    if (n == said_n || now - since < 2000) return;
    said_n = n;
    klh_scene(scene, sizeof scene);
    if (n > KLH_MENU_CAP || !klh_rd(mgr + 8, tab, 8 * (SIZE_T)n)) { klog("menu: table count %lu, not readable (scene '%s')", n, scene); return; }
    for (k = 0; k < n; k++) c[tab[k].kind < 4 ? tab[k].kind : 4]++;
    if (n > KLH_MENU_HOT) {
        k = tab[KLH_MENU_HOT].kind < 4 ? tab[KLH_MENU_HOT].kind : 4;
        klog("menu: table %lu of 5096 entries (%lu elements, %lu windows, %lu colour sets, %lu button graphics, %lu other); OVER 5000: entry 5000 is %s%s; scene '%s'",
             n, c[0], c[1], c[2], c[3], c[4], kind_name[k], k ? " - THE MOUSE OVER THE MENU BACKGROUND WILL FAULT (0x861720)" : " (takes a stray hover)", scene);
    } else
        klog("menu: table %lu of 5096 entries (%lu elements, %lu windows, %lu colour sets, %lu button graphics, %lu other); %lu free below entry 5000; scene '%s'",
             n, c[0], c[1], c[2], c[3], c[4], KLH_MENU_HOT - n, scene);
}

static volatile LONG klh_game_ticks;                  /* frames of the main loop: half of the stall watch's heartbeat */
```

(2) klhook.c, in `klh_tick` - OLD:

```c
    klf_tick();
    kls_tick();
```

NEW:

```c
    klh_menu_table_watch(game_thread);                /* a log line per XML load: the menu table's count and entry 5000 (reads only) */
    klf_tick();
    kls_tick();
```

GUESSES in it: that the count stands still for 2 s only after a whole XML load (else two lines per load, harmless);
that the kind word is exactly 0..3 (READ at the four writers; anything else is counted as 'other' and said).

For a new map on the tab the build chain gains one step after `kl_hud.py all ... --look deadmen`:
`python tools/kl_hud_menu.py level <build folder> <out folder>` and `check-level <out archive> <build archive>`
(only after M3 has passed).

## 9. Review round (re/hud_menu_review.md -> what was done)

| # | Finding | Checked | Done |
|---|---|---|---|
| 1 MUST | the dangerous index is 5000; budget 5000, not 5096 | HOLDS. Re-read: ZBUTTON +0x2b0 = 0x83d5d0 `[ecx+0x60]`; the scene: 121 ZBUTTONs, only `ZWINDOWS\Menu\DefaultFocus` carries 5000. (The dump was not re-read here: the review's reading is taken.) | section 1.1 and the tool's TABLE docstring rewritten; `check` / `check-level` fail on a grown table without a live count, test N + new <= 5000 with one; K0 added and put first |
| 2 MUST | `PlayerIndex` is a row, not klbot's record | HOLDS, and settled further: slot 0x188 = 0x5a0fa0 is a byte table `[[rules+0x368]+row]`; `StatusPlayerName` uses THE SAME slot in Arcade (0x5bb8bb), so name row = score row | section 1.3 'THE ROW TAGS', section 4, `board()`'s docstring: a fate hook reads the byte table. No hook code written (none is this track's) |
| 3 MUST | no board through Patch01.zip | HOLDS (and the scene's online.xml is loaded at the menu as well) | `apply --board` is refused; `Overlay_board` deleted; the board exists as `level_DM03_board` only |
| 4 SHOULD | snippet: kind word, logger, entry 5000, an else line | HOLDS; the 'ASSUMED' table object is now READ (0x8a43c7..0x8a43d8: the window system's +0x4b4 IS `[[0xdd265c]+0x824]`) | section 8 rewritten: kinds from the pair's second word, `klog`, entry 5000's kind, a line for an unknown vtable; compiled SHIP + TEST |
| 5 SHOULD | 'no reference in the exe' proves nothing for set names | HOLDS | docstring, section 2 and risk 3 say 'unused by the XML only'; KNOWN_* called a lower bound (1.3, the tool) |
| 6 SHOULD | `DisabledColor` is not read | HOLDS: reader 0x8ab978..0x8ab988 has `NormalColor`, `FocusColor`, `DisableColor`; no string `DisabledColor` | the three spare sets of online.xml get a real `DisableColor=`; `DisabledColor` is no longer rewritten anywhere. REJECTED for the second `Default`: a real disabled colour there could change stock in-level text. 'Alpha kept' corrected (the spare sets are ff on purpose) |
| 7 SHOULD | the bars are perforated rectangles; reuse kl_hud's stroke by import | HOLDS for the old painter. kl_hud's painter BY IMPORT is in (`--bars hud`) but is itself the barcode at menu size (`sheet_hudbars.png`), so it cannot be the default without breaking the review's own 'at least' list | new default painter `_stroke_kit`: no pinholes, no cuts, edges in 20-40 px runs, slanted cut ends, dry streaks from an end. `GREEN_INK` removed (the price is on no bar). The two hands differ still: for the HUD session to look at pictures 111 / 112 |
| 8 SHOULD | things repainted or left that the note did not list | HOLDS | section 2: shared tiles, `FocusBar_medium_02` / `FAFocusBar_long` left, tap_01 / 02 repainted (code comment fixed), the paired lines, opaque shop bars -> M3's pass criteria, 'Bonus' / 'Penalty' are ink not coral |
| 9 NOTE | the restyle is global | HOLDS | risk 1, for the lead to decide |
| 10 NOTE | `diff` hides half of a doubled set | HOLDS | `colorset_list`: by (name, occurrence); the diff prints 'Legend (definition 2)', 'Default (definition 2)' |
| 11 NOTE | what `check` cannot see | HOLDS | the tag pattern takes attributes glued together (4 stock tags; counts now 4342 / 1593 / 1889); `check-level`; the budget test; archives with fixed stamps (same sha1 every build, RAN twice); 'a reference with the same fault passes' is risk 11 |
| 12 NOTE | the mode test, smaller points | HOLDS (0x7bb2a0: mode 4) | 1.3; positions owned up to in section 4; `Debug`'s alpha in section 2 |

## 10. Still a guess

- that the integer 5000 of `DefaultFocus` is what `[button+0x60]` holds (inferred from the dump); what the 120
  pool buttons hold at run time; where on a page `DefaultFocus` is hit;
- both live table counts (K0);
- which definition of a doubled colour set wins; that no code asks for the four spare sets by name;
- that an element's own `ColorSet=` beats its template's; 'ABGR' bars; additive lines; Patch01.zip overriding a
  level's online.xml;
- the board's positions; that `[rules+0x1d4]` is set when the round-over page shows; the two row limits agreeing;
- how the constructor colours a set without `DisableColor`.
