# Dog Days menu system (kl2.exe) - specification with evidence

Written 2026-10-09 by the `track-menus` agent. Purpose: a heister (character) select for Fragile
Alliance / Arcade, and room for more than nine maps.

Method: static only. Nothing here was run in the game. Sources:
- `Patch01.zip` `menu/frontend.xml` (9164 lines), `menu/ingame.xml` (3799 lines); `Scenes/kaneandlynch.zip`
  `Menu/online.xml` (3781 lines), its `.LOC`, `.gms`, `.buf`, `.prp`; stock levels F01..F09.
- `kl2.exe` disassembly (capstone through `debug/kl.py`), RTTI vtables, string cross references.
- Scratch scripts (not in the repo): `<scratchpad>\agents\track-menus\` - `fact.py` (factory tables),
  `attrs.py` (attributes per class), `loc.py` (text key rule), `gfx.py` (graphics), `abi.py` (names the exe
  knows), `heroes2.py`, `fachar.py`, `count.py`, `fn.py` / `xr.py` / `disp.py` / `callers.py` (disassembly helpers).

Words used: **established** = read in the code or counted in the files as stated; **ASSUMPTION** = fits
the evidence but the deciding code was not read; **not established** = unknown.

---------------------------------------------------------------------------------------------------

## 0. Summary for the lead

1. Menus are data. A page is a `<Window>` in XML; a widget is a `<GuiElement Type="...">`; `Type` is looked
   up in two hard-coded factories (146 + 18 names). New pages and new widgets of existing types need XML only.
2. Options are NOT data. Their names are compiled in: 35 names in a `strcmp` chain plus a table of 49. An
   unknown name is silently dropped on write and reads 0. So a new option cannot be added in XML.
3. But the table of 49 holds two spare integers nothing in the game uses: **`Dummy2`** (the exe itself gives
   it the range 0..7) and **`Dummy`** (the exe makes `Dummy2`'s widget greyed while `Dummy` is 0). Eight
   values = the eight heisters `Hero_01`..`Hero_08`. The character select page can be written today, XML only.
4. What the page writes must still be read by code. Today the Arcade body is RANDOM: the
   `ZGameRulesHeist` constructor stores `rand*8` in `[rules+0x33d]` (kl2 0x835837) and
   `ZGameRulesHeist` vtable slot 137 (0x8f5e90) uses it as the hero index. One 6-byte site to hook.
   In online Fragile Alliance the index comes from the session (0x74ee10); that needs a replicated value
   and is not solved here.
5. Maps: the nine-entry limit is in code in four places (two permutation tables of nine bytes built on the
   stack, and the Arcade selector's bound of 8 in two places). A tenth entry cannot be done in XML. A
   second PAGE of nine can: a second window that sets `Dummy` to the page number, and KLHook swapping the
   nine slot strings by that number when the round starts.
6. Map pictures and all other menu graphics are scene entities of the frontend scene, not files. A new
   picture means adding a `ZWINGROUP` + `ZWINPIC` to `Scenes/kaneandlynch.zip`. Reusing a stock picture
   needs nothing. Map titles can be literal text in XML (`Text="%Retomoto Tower"`).

---------------------------------------------------------------------------------------------------

## 1. Files and loading

Established:
- `ZMercsMenuElements` (vtable 0xbb7dc8) is the menu manager; the live object is `[[0xdd265c]+0x824]`.
  Slot 2 (0x71a390) picks the XML by scene name (`_stricmp`): scene `KaneAndLynch` (the frontend) loads
  `frontend.xml` then `online.xml`; any other scene loads `ingame.xml`, plus `online.xml` when
  `0x863a60` or `0x7f6850` on the session manager `[0x168e598]` returns true (multiplayer; the tests
  themselves were not decoded). Dead names in the same function: `mainmenu.xml`, `gamemenu.xml`,
  `menutestmsl.xml`, `m_options.xml`, `m_frontend.xml`.
- Files are opened as `<root>/Menu/<file>` (0x6cffa0, string `Menu` 0xb6d1f8) by one `ZGUIXMLReader2`
  (vtable 0xb23650; slot 0 = start element 0x8ce850, slot 1 = end element 0x5dcf30, slot 2 = read file
  0x87e930), all into the same manager.
- `Patch01.zip` holds only `menu/frontend.xml` and `menu/ingame.xml`. `online.xml` therefore comes from
  `Scenes/kaneandlynch.zip` (`Menu/online.xml`) in the frontend and from the level archive in a level
  (F02_Main.zip holds `Menu/online.xml`, `menu/ingame.xml`, `guielems.xml`, `windows.xml`).
  Patch01 against the frontend archive's copies: 157 changed lines in `frontend.xml`, 38 in `ingame.xml`.
- `guielems.xml` and `windows.xml` are dead: neither name occurs in kl2.exe, and their grammar
  (`<ButtonGraphicDefinition>`, `<WindowTemplateDefinition>`) is not the one the reader parses.

Consequence: to change the frontend pages put `menu/frontend.xml` in Patch01.zip (as today). To change the
in-level Fragile Alliance pages (status, weapon shop, respawn) `Menu/online.xml` has to be added to
Patch01.zip - ASSUMPTION that Patch01 overrides it like the other two (same mount rule, earlier research
`v2_f153...json`; not run).

---------------------------------------------------------------------------------------------------

## 2. XML grammar actually used

### 2.1 Elements

Counts are tags outside comments in Patch01 `frontend.xml` / Patch01 `ingame.xml` / `online.xml`.

| Element | Count | Meaning (where read) |
|---|---|---|
| `<Windows>` | 1 / 1 / 1 | root |
| `<Window Name= Template= ...>` | 136 / 55 / 40 | a page. Created through factory slot 1 with type `Standard` (0x579714, 0x667e00) |
| `<GuiElement Type= ...>` | 4023 / 1511 / 1826 | a widget. `Type` goes to the factory chain (0x7fad10) |
| `<Template Name= ...>` | 343 / 160 / 174 | named attribute set, optionally with child elements (0x4ecea0 -> 0x686270) |
| `<ColorSet Name= NormalColor= FocusColor= DisableColor=>` | 12 / 12 / 12 | 0x47d5e0 |
| `<ButtonGraphic Name=>` with `<GraphicElement Name= WinObjType= Priority=>` | 17 / 12 / 11 | 0x53c720, 0x7b0fa0 |
| `<Text Text=>`, `<Graphic Graphic=>` | 210+44 / 70 / 16 | value children of a toggle (0x7b0fa0: `Text` 0x10 bytes, `Graphic` 0x20 bytes) |
| `<Platform>`, `<ExcludeIn>`, `<Locale>`, `<GameRegion>`, `<BuildTag>`, `<MainIniOption>` | 375+14+10+6 / ... | conditional blocks (0x8ce850) |

Conditional blocks (established from 0x8ce850 and 0x87e930):
- `<Platform>`: the reader's names are `PC` (0xb44750, at reader+0x1b0) and, at reader+0x1b4,
  `PC_GC` when `[manager+0xaf68]` is set, else `PC_KEYBOARD`. The XML also uses `XENON`, `PS3`.
  How the two lookups combine is not established exactly (see 2.5).
- `<ExcludeIn>` keys the exe tests: `Arcade Campaign Demo HiddenDemo Normal GameRelease GermanSKU
  NotGermanSKU JapaneseSKU NotJapaneseSKU Extreme Hard PreviewBuild LifePreviewBuild`. The XML also writes
  `FA` and `Preview`; 2026-10-24: `FA` IS tested (0xb6ca28, first in the chain: `0x863a60 && [session+0x5c]==4`),
  only `Preview` is not. Each key's test: `re/menu_count.md` 2.
- `<Locale>`, `<GameRegion>`: language and region name as attribute, e.g. `English="True"`.
- `<BuildTag>`: attribute named after the ini value `BuildTag` (default `Default`), 0x87ea35.
- **`<MainIniOption Name="Key" Value="n">`** (0x8ced39..0x8cee40): includes its children when
  `atoi(ini value of Key)` equals `Value` (default 1); a missing key counts as 0. The ini getter is
  `0x793550` on `[0xdd2640]`, the same one that answers `DisableFAVariants` and `GermanSKU`.
  ASSUMPTION: this is the store the `-o Key=Value` launch options fill (CLAUDE.md "Boot"). If so,
  `-o KLMerge=1` can switch our pages on while the stock menu stays untouched without it. Not run.

### 2.2 How a widget class is named

`Type="X"` -> `0x7fad10` asks each registered factory, last registered first, through vtable slot 2;
the first non-null object wins. A null (unknown type) is not an error: the element is skipped (0x8cef08).
Unknown types that occur in the stock PC XML and are simply dropped: `PS3HandleInvites` (39),
`AutoSave`, `AutoLoad`, `PS3BootCheck`, `MercsInstall`, `AcceptInvite`, `DeleteFromList`,
`ControllerConnect`, `MercsShowInEfo` (a typo in ingame.xml).

Factories (established, `fact.py`): `ZMercsMenuFactory` slot 2 = 0x859460, 146 names;
`ZStandardMenuFactory` slot 2 = 0x5fa2d0, 18 names. Each entry is `strcmp(name) -> operator new(size) ->
constructor`; the class is the vtable the constructor stamps. The ones that matter here:

| Type | Class | Size | Constructor |
|---|---|---|---|
| `GUIGroup` | ZGUIGroup | 0xb0 | 0x7595b0 |
| `Graphic` | ZGraphic | 0xb8 | 0x406970 |
| `TextBlock` | ZTextBlock | 0xc0 | 0x4e6aa0 |
| `OpenWindow` | ZOpenWindow | 0x124 | 0x6d6840 |
| `CloseWindow` | ZCloseWindow | 0x108 | 0x6665b0 |
| `SendMessage` | ZSendMessage | 0x11c | 0x63d510 |
| `Toggle` | ZToggle | 0x124 | 0x88c3b0 |
| `ToggleText` | ZToggleText | 0x144 | 0x55f9c0 |
| `ToggleImages` | ZToggleImages | 0x138 | 0x768540 |
| `Slider` | ZGUISlider | 0x130 | 0x7c19c0 |
| `GUIList` | ZGUIList | 0x198c | 0x898c60 |
| `MercsLevelSelector` | ZMercsLevelSelector | 0x15c | 0x6df570 |
| `MercsLevelSelectorHeist` | ZMercsLevelSelectorHeist | 0x15c | 0x6a65c0 |
| `MercsFAToggleImages` | ZMercsFAToggleImages | 0x140 | 0x8d69d0 |
| `MercsFACustomBoundsToggleText` | ZMercsFACustomBoundsToggleText | 0x14c | 0x779a60 |
| `MercsFASelectorLobby` | ZMercsFASelectorLobby | 0x100 | 0x563d80 |
| `MercsFASelector` | ZMercsFASelector | 0xc8 | 0x5095d0 |
| `MercsFASelectorWeapons` | ZMercsFASelectorWeapons | 0xe8 | 0x4c2930 |
| `MercsShowInfo` / `MercsShowInfoFA` / `...FALobby` | ZMercsShowInfo... | 0xec / 0x108 / 0x120 | 0x5d1ad0 / 0x8cfbc0 / 0x64be40 |
| `MercsGraphicFA` | ZMercsGraphicFA | 0xcc | 0x761be0 |
| `DLCMaskToggler` | ZDLCMaskToggler | 0x144 | 0x642830 |
| `DisplayOption` | ZDisplayOption | 0xcc | 0x7bd680 |
| `ToggleGoldOnlyElements` | ZGUIToggleGoldOnlyElements | 0x94 | 0x4c7500 |
| `Invalidate` | ZInvalidate | 0x100 | 0x585770 |

79 of the 164 names are not used by `frontend.xml`, 123 not by `ingame.xml` (leftovers such as
`MercsServerBrowser`, `ZStartServerButton`, `DisplayOption`, `Invalidate`).

Class tree (RTTI): `IXMLInterface < INameInterface < ZNameBase < ZGUIBase < IGUIElement`, then
`ZNavigator` (buttons: OpenWindow, CloseWindow, SendMessage, ...), `ZOption` (`ZToggle` -> `ZToggleText`,
`ZToggleImages`; `ZGUISlider`), `ZTextBlock`, `ZGraphic`, `ZGUIGroup`.

Vtable slots that matter (same index in every widget): 1 = read attributes, 2 = add child element,
6 = set up when the window opens, 8 = per-frame update, 10 = input (key code, ...), 18 = refresh from
option (called as `[vtbl+0x48]`), 20 = receive message (`[vtbl+0x50]`, argument `ZString*`),
36 / 37 = get / set value (`[vtbl+0x90]` / `[vtbl+0x94]`).

### 2.3 Attributes per class

Established by listing the strings each class's slot 1 asks for (`attrs.py`); a class also takes
every attribute of its bases.

| Class | Attributes read in its own slot 1 (address) |
|---|---|
| ZNameBase | `Name` (0x4fe640) |
| IGUIElement | `BlockReceiveAllInput HelpText HelpTextBlock HelpText2 HelpTextBlock2 FocusGraphic MoveFocus MoveButton` (0x6df070) |
| ZNavigator | `Text ActivateButton ActivateMouse Option OptionValue OptionPlayerIndex PrivateCommand Disabled DisableInDemo DisableInHiddenDemo DisableInGermanSKU DisableInPreviewBuild DisableInLifePreviewBuild PlayerIndex TeamIndex CheckFocusIndex` (0x4b1ae0) |
| ZOpenWindow | `PushOnStack ResetStack RollBack ClosePrevious Window PushWindow KeepRollbackWindow TrimStack UseSubstringAsEvaluator CallBackupOptions PlaySound DisableClick DisableClickInGermanSKU` (0x5d5320) |
| ZCloseWindow | `CloseAll Cancel MoveFocusToParent ApplyCachedOptions RequiresWindowFocus PlaySound` (0x730450) |
| ZSendMessage | `Message Receiver PlaySound` (0x6d48f0) |
| ZOption | `LowerBound UpperBound Step Option TakeFocus ShowLimitButtons ResetOnReloadOptionValue` (0x655220) |
| ZToggle | `Text Wrap LeftRight ActivateButtonUp ActivateButtonDown ToggleReceivers ResetOnLoad` (0x415790) |
| ZToggleText | `UseBaseText TextReceiver RecCSDefault RecCSFocus UseTextReceiverAsFocus DisableInGermanSKU` (0x8db590) |
| ZToggleImages, ZMercsFAToggleImages | `ResetGUIEffects UseBaseText ResetToOldValue` (0x6c2d80) |
| ZMercsFACustomBoundsToggleText | `CustomLowerBound CustomUpperBound` (0x6611e0) |
| ZMercsLevelSelector(+Heist) | `PrivateGame` (0x7baf90) |
| ZTextBlock | `Text Disabled` (0x8f4650) |
| ZGraphic | `IsFocusGraphic IsFakeFocusGraphic MouseFocusW MouseFocusH` (0x4daac0) |
| ZGUIGroup | `GeomSpace ReverseNavigation` (0x501c30) |
| ZMercsShowInfo / FA / FALobby | `TagName TextReceiver` (+ `PlayerIndex TeamIndex CheckFocusIndex`) (0x41a2a0, 0x7e46a0, 0x70c8e0) |
| ZMercsGraphicFA | `PlayerIndex TeamIndex TagName` (0x716150) |
| ZMercsFASelector | `SelectorType` = `Leaderboard WeekendLeaderboard ServerBrowserLocal ServerBrowserOnline ServerBrowserListPlay Lobby IngameStatus PlayerStatus PlayerReview HostDisconnect Achievements GameTips LocalLeaderboard`; `PageSize FocusBar FocusBarBaseX/Y FocusBarDeltaX/Y` (0x6453d0) |
| ZMercsFASelectorLobby | `PageSize FocusBar TeamFocusBar OptionsFocusBar FocusBarBaseX/Y FocusBarDeltaX/Y` (0x66c660) |
| ZDisplayOption | `Option` (0x4400e0) |
| ZGUIToggleGoldOnlyElements | `Receivers` (0x50dc60) |
| ZBaseWindow (`<Window>`) | `PopOnBack RollBackMark PauseEngine ForceSound Dialog TRC TRCPrioritry LocaleBasePath ScaleToViewPort InputDisableTime CancelOnPop SendEcsToReceiveAllInput ForceAsTopWindow BackupOptionsOnSetup SharedOptionWindow` (0x46e860) |

Layout and effect attributes shared by every element (`X Y W H AlignH AlignV Priority Font ColorSet
TextWidth LineSpace FadeInTime FadeInDelay FadeOutTime FadeOutDelay AlphaMin AlphaMax Flash* Jitter*
Flicker*`) are read elsewhere (the effect names in slot 7, 0x784730); their reader was not traced.

### 2.4 Binding, linking, messages

- **Option binding.** `Option="Name"` on a `ZOption` widget (ToggleText, ToggleImages, Slider): the name
  is kept at widget+0xa8 and the options interface at widget+0xa4 (0x655269). At set-up (slot 6, 0x597960)
  the widget asks the interface for bounds (`[iface+0x28](name, &lower, &upper)`) and whether the option is
  enabled (`[iface+0x24](name, player)`); if not it sends `Disable` to its linked elements, and
  `ZToggleText` also to its text receiver (0x740450). `ZToggleText` / `ZToggleImages` children
  (`<Text>` / `<Graphic>`) go into a growable vector at widget+0x124 and `UpperBound` (widget+0x8c) becomes
  count-1 (0x694500, 0x50f880): no fixed size in the toggles themselves.
  A `<Graphic Graphic="N"/>` child is resolved by element name when it is added (0x50f8db), so the picture
  elements must stand BEFORE the `ToggleImages` in the file (they do in the stock XML).
- **Option on a button.** `Option="Name" OptionValue="n"` on any `ZNavigator` (the stock main menu buttons
  all carry `Option="MP_MultiPlayerMenu" OptionValue="0|1"`). ASSUMPTION: the value is written when the
  button is activated; the write itself was not traced.
- **Page links.** `Type="OpenWindow" Window="Name"` opens a page; `PushWindow`, `TrimStack`, `RollBack`,
  `KeepRollbackWindow`, `ClosePrevious` control the window stack; `<Window RollBackMark="True">` marks a
  rollback point; `Type="CloseWindow"` goes back (with `Cancel="True"` discarding cached options);
  `OpenWindowTimer Time=` opens after a delay. Back / accept keys are invisible buttons
  (`ReceiveAllInput="True" ActivateButton="ZW_CANCEL"` or `ZW_SELECT1`, `Link="False"`).
- **Messages.** `Type="SendMessage" Receiver="ElementName" Message="Text"`. The receiver is found by name
  (`0x83faf0` on the manager) and gets the text through slot 20. Messages seen in code: `Increase`,
  `Decrease` (toggles, 0x90b170); `Enable`, `Disable` (`ZTextBlock` 0x672ac0 recolours to the colour set's
  disabled colour; toggles 0x7a97c0; buttons); `Hide`, `Unhide` (buttons, 0x45eaf0); `StartGame`
  (`ZMercsLevelSelectorHeist` slot 20, 0x49f4e0); `FA` / `UC` / `TM` (game mode); `ZW_*` key names
  forwarded to selectors. `ReceiveAllInput`-type attributes belong to the shared reader.
- **Data display.** `MercsShowInfo*` with `TagName="X"` shows a value the code computes; `TextReceiver`
  redirects it into another element. The tag set is compiled in: 167 of the 191 tag names in the three XML
  files are strings with code references in kl2.exe (`abi.py`). New tags need code.
- **Names the exe knows.** 74 of 208 window names and 46 element names are named in code (`abi.py`), e.g.
  windows `MainMenu OnlineMenu HeistPlayMenu FALobby FAPlay FAStatus FABuyWeaponsNew FARespawn
  IngamePauseFA IngamePauseHeist`, elements `LobbyImageToggler LobbyLevelNameToggler LobbyArrowL_1..4
  LobbyArrowR_1..4 CoopLobbyImageToggler Headline0..2 TeamHeadline0..2`. Renaming or removing one of those
  breaks code that looks it up; the other 134 windows are reached only through XML, which is the evidence
  that a new window needs no code (not run).

### 2.5 Hard limit on the number of elements

Established: every created window, element, colour set and button graphic is entered in a table of
0x13e8 = 5096 slots in the manager (count at manager+0x9f48; 0x7fad55, 0x667e46, 0x47d629, 0x53c769).
Overflow is a bare `int3` (0x7fad8d, 0x667e6e) = crash.

Not established: the headroom. `count.py` models the conditionals and template instancing and gets 5992
objects for the frontend (frontend.xml 3973 + online.xml 2019) and 3393 for a multiplayer level - the
first exceeds the cap while the stock game runs, so the model over-counts (most likely the `<Platform>`
rule). Before adding large pages, read `[[[0xdd265c]+0x824]+0x9f48]` in KLHook once in the main menu.
A character page of about 40 elements is small either way.
2026-10-24: re-read and rewritten as `tools/kl_menu_count.py` (rules in `re/menu_count.md`): the `<Platform>`
rule is attribute `PC` OR attribute `PC_KEYBOARD` / `PC_GC` (XENON / PS3 never read), a `<Template>`'s children
are made once at the definition and re-attached on use (no clones), an element naming a template with
children makes nothing itself. ESTIMATES: stock frontend 4730 (gamepad 4927), live KLExpansion frontend
4793 (gamepad 4990), a level 2775. Second cap: 512 `<Template>` definitions per load set, frontend uses 500.

### 2.6 Text keys and the .LOC

Established on the frontend `.LOC` (`Scenes/kaneandlynchEnglish.LOC`, 3357 leaves; trie format from the
earlier research `agent_scripts/assets/loclib.py`):
- `Text="/A/B"` -> key `AllLevels/A/B`. 228 of the absolute keys in `frontend.xml` resolve.
- `Text="B"` -> `<Window LocaleBasePath>` + `/B`. 400 relative keys resolve.
- `Text="%literal"` -> shown as written, no lookup (60 uses, e.g. `%Cheat Menu`; the exe builds such
  strings itself with `%%%s`, `%%%ix%i` in the options interface).
- 131 uses do not resolve under this rule: console-only keys, keys inside templates defined outside a
  window (my parse has no base path for them) and debug text. What the game shows for a missing key is
  not established.
- Code looks keys up as (folder, key), e.g. `AllLevels/Interface/FACharacters` + `C1` (0x478df0,
  0x8c3790) through `[[[0xdd2640]+0xac]+0x94]`.
- The frontend and every level have their own `.LOC`; the menu keys (`AllLevels/Menu/...`) are in the
  frontend one. Useful existing entries: `AllLevels/Menu/Online/Scenarios/Title01..09` = Subway, Bridge,
  Airport, Fish Market, Dry Dock, Harbor, Financial, Highrise, Radio Tower (no `Title10`);
  `AllLevels/Interface/FACharacters/C1..C9` = J.C., Tommy, Pierre, Liam, Jean, Elwood, Bud, Mitchel, Glazer.

So new text needs no `.LOC` work if written as `%literal` (one language), and a `.LOC` edit for
localised text.

### 2.7 Graphics

Established (`gfx.py`): `Graphic="N"` names a scene entity, not a file. In the frontend scene 340 of the
428 distinct `Graphic=` values are `ZWINGROUP` entities (the other 88 are element names used by
`ToggleImages` children, or console art). They sit in
- `ROOT\LocalResources\Graphic\<N>` (417 entities) - page-specific art: `LevelPicture_F01..F09`,
  `LevelPicture_H01..H09` (Arcade), `LevelPicture_L01..L11` (story), each a `ZWINGROUP` with one `ZWINPIC`
  child `Box`; `Background_FABag`, `LobbyBackground`, ...
- `ROOT\AllLevels/Menu_genericresources.zip\GenericMenuResources\Graphic\<N>` and
  `...\ButtonGraphic\<N>` (`ZWINPIC`) - shared art that also exists in every level under
  `ROOT\AllLevels/mainsceneincludes_multiplayer.zip\AllLevels/MenuFA.zip\AllLevels/Menu_genericresources.zip\...`:
  `FocusBar_short#01..#20`, `FocusBar_long#01..#12`, `FocusBar_medium#01..#20`, `Line_Short_01#01..#10`,
  `Line_Long_01#01..#15`, `Icon_Heist`, `Icon_Multiplayer`, `BlackBackground#01`, `FAStatus_Ready#01..`.
- A `#NN` suffix is one instance; several windows reuse the same instance (`FocusBar_short#01` is the first
  focus bar of MainMenu, HeistModeMenu, OnlineMenu and FAPlay).

The frontend scene has 6221 entities (1278 `ZWINGROUP`, 925 `ZWINPIC`); no heister portraits exist in it
(searched names for Portrait / Character / Criminal / Hero).

The code that resolves `Graphic=` to the entity was not traced; the correspondence above is by name.

---------------------------------------------------------------------------------------------------

## 3. The option system

Established:
- One object answers every option: `ZMercsOptionsInterface` (vtable 0xbb7dec, bases `ZDefaultOptions`,
  `IOptionsInterface`), 0x120 bytes, created once by `ZMercsMenuElements` slot 5 (0x5b20f0) and kept in
  the global `[0x154d5f4]`. Code reaches it as `[[[0xdd265c]+0x824]->vtbl+0x14]()`.
- Interface slots: 2 = `Get(name, player)` (0x504b40), 5 = `Set(name, value, player)` (0x472450),
  9 = `IsEnabled(name, player)` (0x4b4560 -> 0x781a70), 10 = `GetBounds(name, &lo, &hi)` (0x611be0).
- `Get` / `Set` are a chain of 35 `strcmp`s; anything else falls through to the base table:
  `0x561ee0` searches 49 name pointers at object+8; not found returns 0x31, and then `Set` does nothing
  (0x4576fd) and `Get` returns 0 (0x7aca73).

The 35 multiplayer names and where they live (from the two chains):

| Option | Storage |
|---|---|
| `MP_SelectedLevel` | byte `[0x154d61e]` (menu index 0..8, not the slot number) |
| `Heist_SelectedLevel` | byte `[0x154d632]` |
| `MP_SelectedLevelCl` | byte `[0x154d61f]` (search filter; `Set` also goes through `0x746570`) |
| `HeistHighscoreIndex` | dword `[0x154d634]` |
| `CoopNetMode` | dword `[0x154d63c]` |
| `MP_LB_Filter`, `MP_LB_Screen`, `Heist_LB_Screen` | bytes `[0x154d61a]`, `[0x154d61b]`, `[0x154d61c]` |
| `MP_BuyWeaponsIndex`, `FAProfileIndex`, `MP_Profile_Screen` | bytes `[0x154d61d]`, `[0x154d623]`, `[0x154d633]` |
| `MP_Status_Screen`, `MP_Weapon_Screen` | bytes `[0x154d638]`, `[0x154d639]` |
| `MP_OG_ServerIndexPageOffset`, `MP_LB_PageIndex`, `MP_Weapon_PageIndex` | dwords `[0x154d624]`, `[0x154d628]`, `[0x154d62c]` |
| `Audio_Enable_Microphone` | dword `[0x154d644]` |
| `MercsGameMode`, `MP_GameModeCl`, `MP_StatusReadyCl`, `MP_NumberOfPlayers(Cl)` | session manager `[0x168e598]` |
| `MP_TimeLimit(Cl)`, `MP_NumberOfRounds(Cl)` | game settings `[0x168e9e4]` |
| `MP_PrivateGame`, `MP_GoldOnlyGame`, `MP_RankedGame`, `MP_MultiPlayerMenu`, `Difficulty`, `SelectedLevel`, `SelectedLevelCl`, `SearchDifficulty`, `Audio_Volume_VoiceChat` | in the chain; storage not listed here |

The 49 base names (index = position in the table, constructor 0x800f90):
1 `Audio_Volume_Dialog`, 2 `Audio_Volume_Music`, 3 `Audio_Volume_Ambience`, 4 `Audio_LanguageEnglish`,
5 `UseEAX`, 6 `MouseSensitivity`, 7 `Sensitivity`, 8 `InvertVertical`, 9 `InvertHorizontal`,
10 `InvertControllerVertical`, 11 `InvertControllerHorizontal`, 12 `CameraAutoCentering`, 13 `AimAssist`,
14 `SwitchControllerSticks`, 15 `ControlScheme`, 16 `Subtitles`, 17 `Vibration`, 18 `Brightness`,
19 `Gamma`, 20 `Online_Voice_Chat`, 21 `Online_Tutor`, 22 `Online_Speak`, 23 `Difficulty`,
24 `GameSteadyCam`, 25 `GamePlayerNames`, 26 `GameOSD`, 27 `FATutorial`, 28 `UseMask`, 29 `WideScreen`,
**30 `Dummy`, 31 `Dummy2`**, 32 `TextureResolution`, 33 `Resolution`, 34 `LevelOfDetail`,
35 `PostFilterLOD`, 36 `ShadowDetail`, 37 `SelfShadows`, 38 `BlurShadows`, 39 `Anisotropy`,
40 `EnableVSync`, 41 `Antialias`, 42 `SoundRender`, 43 `AspectRatio`, 44 `Refresh`,
45 `FullscreenEffects`, 46 `TripleBuffer`, 47 `Sharpen`, 48 `AmbientOcclusion` (0 not recovered by the
scan; the XML uses `Audio_Volume_Sfx`).

### 3.1 The two spare options

Established:
- `Set("Dummy", v)` stores `[object+0xd4] = v` (0x576580); `Set("Dummy2", v)` stores `[object+0xd8] = v`
  (0x576594). `Get` returns them (0x4c6c10, 0x4c6c23). The constructor zeroes both (0x800fcb, 0x800fd1).
- `GetBounds("Dummy2")` returns lower 0, upper 7 (0x611bf0..0x611c0f).
- `IsEnabled("Dummy2")` returns `Dummy != 0` (0x781a80..0x781a94).
- Nothing else reads them: the string `Dummy2` has one reference (the name table); `Dummy` has one more,
  `ZInvalidate` slot 10 (0x66e250), which sets `Dummy = 3` when that widget is activated; the widget type
  `Invalidate` is not used in any of the three XML files. `[object+0xd8]` has three references in the
  whole exe (constructor, get, set).
- The attribute `Dummy="..."` that the options pages carry (`Dummy="UseMask"`) is a different thing; no
  reader for it was found.

Not established: whether the two are written to the saved profile (they live at least as long as the
process, which covers menu -> level).

### 3.2 How the game reads a menu option in a level: the mask precedent

Established: `UseMask` (base option 28) is read by game code, not menu code:
- `ZGameRulesHeist` slot 34 (0x4b5b20), per hero: unless the ini key `DisableFAVariants` is set, it reads
  `Get("UseMask", 0)` through the menu manager and calls `hero->0x88c810(2)` (mask) or `(1)` (no mask).
- `0x88c810(v)`: `[hero+0x50] = v`, then notifies through `0x541960()->vtbl+0x70`. So hero+0x50 is the
  appearance variant (1 or 2 in stock use).
- `ZGameRulesFragileAlliance` slot 34 (0x822830) does the same from the player's session record
  (`0x76adb0` = record+0x338, an obfuscated byte, `^0xac`), i.e. online the flag is replicated per player
  (the replicated field list at 0x8da640 contains `m_iUseMask`).

This is the pattern a character option follows: a menu option, read by the game rules when the hero is set up.

---------------------------------------------------------------------------------------------------

## 4. The flows today

### 4.1 Arcade (internal name "Heist"): main menu to Accept

| Page (`<Window>`, frontend.xml line) | Widgets that matter | Sets |
|---|---|---|
| `MainMenu` (702) | `OpenWindow Name="Button_Heist" Text="Button_HeistMode" Window="HeistModeMenu"` (755). Text key resolves to "Arcade Mode" | `MP_MultiPlayerMenu = 0` |
| `HeistModeMenu` (1326) | `OpenWindow Window="HeistPlayMenu" Text="Button_StartHeist"` (1363); also rules movie, stats, leaderboards | nothing |
| `HeistPlayMenu` (2380) | nine `Graphic` elements `H01_LevelPicture`..`H09_LevelPicture` (-> `LevelPicture_H01..H09`); `ToggleImages Name="HeistLevelImageToggler"` with nine `<Graphic>`; `MercsLevelSelectorHeist Name="HeistLevel" Option="Heist_SelectedLevel" TextReceiver="HeistChapterData" ToggleReceivers="HeistLevelImageToggler,HeistIndicator"` with nine `<Text>` in the order Title01, 02, 03, 04, 06, 07, 05, 08, 09; arrows `SendMessage Receiver="HeistLevel" Message="Decrease|Increase"`; `MercsShowInfo TagName="HeistBriefing"`; `MercsHeistScoreKeyboard`; Accept | `Heist_SelectedLevel` = menu index 0..8 |

Accept: gamepad layout sends `SendMessage Receiver="HeistLevel" Message="StartGame"` (template
`BottomFrameHeistBackStartGameButtons`). The keyboard layout's Accept button names
`Receiver="PlayLevel"`, an element of the story page, not of this one; how keyboard Accept reaches the
selector is not established (the documented test "Arcade Mode -> Subway -> Accept" works, so it does).

What `StartGame` does (established):
1. `ZMercsLevelSelectorHeist` slot 20 (0x49f4e0) -> `0x502b40`: value = `[vtbl+0x90]()`;
   slot = `0x746570(value)`; level list `[0x168f750]->vtbl+0x14(slot)` must say available; then game mode
   4 (`0x5be510(4)` on `[0x168e598]`), flags, and `[0x156b73a] = 1` (start pending).
2. Slot 8, the per-frame update (0x459e90): forces `UpperBound = 8` (0x459ed9), copies the value to
   `[0xceceec]`, and when `[0x156b73a]` is set calls `0x7e01a0`.
3. `0x7e01a0`: slot = `0x746570([0xceceec])`; session `->vtbl+0x28(slot)`; scene name =
   level list `->vtbl+0x3c(slot)`; `0x4e7da0(name)` on the session manager (set map name); load.

### 4.2 Fragile Alliance (online / LAN): main menu to the lobby

| Page (line) | Widgets that matter | Sets |
|---|---|---|
| `MainMenu` (702) | `OpenWindow Name="Button_Online" Window="OnlineMenu" RulesWindow="FAShowRules" FirstGameWindow="FAFirstGame"` | `MP_MultiPlayerMenu = 1` |
| `OnlineMenu` (4937) | `ZCheckGamerPrivileges Window="FAPlay"`; `ZCheckGamerPrivileges Window="SystemLink"` (LAN); rules, profile, marketplace | LAN: `MP_RankedGame = 2` |
| `FAPlay` (6477) | `OpenWindow Window="XBoxLiveCreateRanked"`; `OpenWindow PushWindow="XboxLiveStart"`; leaderboard | `MP_RankedGame = 0 / 1` |
| `XboxLiveStart` (6609) | `OpenWindow` to `QuickPlayerMatch`, `XboxLiveFindGame`, `XBoxLiveCreate`, `XBoxLiveCreatePrivate` | `MP_RankedGame = 1`, `MP_PrivateGame = 0 / 1` |
| `XBoxLiveCreate` (6699), `...Private` (6765), `...Ranked` (6832), `SystemLinkCreate` (5123) | three `SendMessage Receiver="XLCreateGameMode" Message="FA|UC|TM"` to a `MercsFAGameModeToggleText GameType="OnlineGame|SystemLinkGame"`, which creates the session | game mode |
| `XboxLiveFindGame` (8605), `SystemLinkFindGame` (5178) | `ToggleText Option="MP_SelectedLevelCl"` (`All` + nine titles), `MP_GameModeCl`, `MP_StatusReadyCl` | search filters |
| interludes `FASessionCreatingInterlude` etc. | `ZSessionStateInterlude` | - |
| `FALobby` (7895) | `MercsFASelectorLobby Name="MercsFASelectorFALobby"` (owns all input); `ToggleText Name="LobbyLevelNameToggler" Option="MP_SelectedLevel"` with nine EMPTY `<Text>`; nine `Graphic` `LobbyPictureF01..F09` (-> `LevelPicture_F01..F09`); `ToggleImages Name="LobbyImageToggler" Option="MP_SelectedLevel"` (order F01, 02, 03, 04, 06, 07, 05, 08, 09); rows `LobbyInfoScenario / MinNumPlayers / TimeLimit / NumberOfRounds` filled by `MercsShowInfoFALobby TagName="LobbyLevelName"` ...; Ready = `SendMessage Message="ZW_SELECT"` | `MP_SelectedLevel`, time limit, rounds, players |

How the lobby changes the map (established, `ZMercsFASelectorLobby` slot 10, 0x7dc5c1..0x7dc6cd): it finds
`LobbyLevelNameToggler` by name, steps it (`[vtbl+0xa8]`), refreshes `LobbyImageToggler`, reads
`Get("MP_SelectedLevel")`, converts with `0x746570` and gives the slot to the session manager
(`vtbl+0x28`, `0x7163e0`). So in the lobby the number of selectable entries is the number of `<Text>`
children of `LobbyLevelNameToggler`, and the shown name comes from the code tag `LobbyLevelName`, not
from those children.

In-level pages are in `online.xml`: `FAWaitForPlayers`, `FAStatus`, `FAStatus_Team`, `FARespawn`,
`FADead`, `FAEscaped`, `FARoundOverMenu`, `FAGameOverMenu`, `FABuyWeaponsNew` / `...Category` /
`...Weapon` (the between-round shop: `MercsFASelectorWeapons`, `MercsShowInfoFAWeapons`,
`MercsSendMessageWeapons`), `HeistStatus*`.

### 4.3 Menu index to slot number: the nine-entry code

Established:
- `0x746570` (thiscall on the level list, one byte argument): builds the table `{0,1,2,3,5,6,4,7,8}` on
  the stack and returns `table[index]`; 0xff or an index above 9 returns 0xff. The test is `cmp al,9 / ja`,
  so **index 9 is accepted and returns an uninitialised stack byte**.
- `0x80c9f0`: the inverse, `{0,1,2,3,6,4,5,7,8}`.
- This is why the XML lists entries in the order 01, 02, 03, 04, 06, 07, 05, 08, 09 (DLC maps last).
- `ZMercsLevelSelectorHeist` slot 10 (input, 0x929360): key 0x7d = left, 0x7e = right; right stops at
  `cmp ebx,8` (0x929479, bytes `83 fb 08`) and `cmp eax,9` (0x929485, `83 f8 09`), and skips entries whose
  slot is unavailable. With slot 8's `UpperBound = 8` (0x459ed9) the Arcade selector is nine entries
  whatever the XML holds.
- `vtbl+0x14` of the level list = "is this slot available" (DLC ownership).
- The level list itself (nine 64-byte names at `[0x168f750]+0x16`) is the slots track's subject
  (`re/fa_slots.md`).

---------------------------------------------------------------------------------------------------

## 5. Where the player's character is chosen today

Established:
- Every stock FA level (9 of 9, `heroes2.py`) has eight groups `Heroes!Hero_01`..`Hero_08`, each holding
  one `ZFFPlayer` named `Ground` with enum properties `eZFFP_TYPE_MULTIPLAYER_NORMAL` (value 2) and
  `eZFFP_RANK_1`..`eZFFP_RANK_8` (values 0..7), and eight `Heroes!Henchmen_01..08` (the cop bodies).
- The game rules keep eight hero pointers at `rules+0x208`: slot 135 (0x6761f0; Heist 0x5684f0)
  `Register(type, rank, hero)` stores `heroes[rank] = hero` only for type 2; slot 136 (0x452a40)
  `GetHero(type, index)` returns `[rules + 0x208 + index*4]`.
  ASSUMPTION: the caller passes the `ZFFPlayer`'s type and rank properties (the call site was not found;
  the enum values fit).
- **Arcade.** `ZGameRulesHeist` (derives from `ZGameRulesFragileAlliance`) constructor 0x835480 draws a
  random number: `seed = seed*0x10dcd + 1` at `[0xdd2640]+0xb30`, `(seed>>8 & 0x7fff) / 32768 * 8.0`,
  truncated, stored as a byte at **`[rules+0x33d]`** (0x835837, bytes `88 86 3d 03 00 00`). That byte has
  four references in the exe: this store, and three in slot 137.
  Slot 137 (0x8f5e90, argument = player index): clamps the byte to 0..7, `hero = GetHero(2, byte)`
  (0x8f5ee8 `movzx eax, byte [esi+0x33d]`, bytes `0f b6 86 3d 03 00 00`), `player->0x783fb0(hero)`,
  then walks the crew records (0x7c bytes each at `rules+0x348`) for the one that used that hero and
  swaps (0x792290). So today the Arcade player's body is one of the eight heroes at random, and an AI crew
  member that had it is moved - the swap part is only partly decoded.
- **Fragile Alliance.** Slot 137 (0x74ee10, shared by the `Sv` and `Cl` classes): takes the player from the
  session manager's player table, `index = 0x817160(session, 0x8e8010(player's session record), 8)`
  (0x74ee59, bytes `e8 02 83 0c 00`), clamps to 0..7, `hero = GetHero(2, index)`,
  `player->0x783fb0(hero)`. `0x8e8010` is the obfuscated byte at record+0xdc; `0x817160` is virtual
  (`[[session+4]->vtbl+0x3c]`), not decoded. So online the body follows a per-player session number.
- Character identity for names and voices is separate: a byte table at `rules+0x33e` (player -> 0..8),
  filled by `ZGameRulesHeist` slot 198 (0x588980) from the hero's scene path:
  `path[0x12] - '1'`, and `"ROOT\Heroes!Hero_0N"[0x12]` is the digit N. `0x478df0(index)` turns it into
  the text of `AllLevels/Interface/FACharacters/C1..C9`; `0x421c70` picks the voice variant with it
  (level sound paths end in `_C1`..`_C8`, `_C9` for the radio voice).
- The Arcade AI crew are separate `ZFFActor`s `AI_Players!merc_bot_squad!Squad#0N\Glazer_Bodyguard_0N`
  (N = 2..8) carrying the property `AllLevels/Interface/FACharacters/C2`..`C8` (7 per level, 9 of 9 levels).

---------------------------------------------------------------------------------------------------

## 6. Can it be done in XML alone?

| Want | XML only? | Why |
|---|---|---|
| new page, new button, new link between pages | yes (not run) | windows and widgets are data; 134 stock windows have no name in code |
| new widget type | no | factory is a compiled `strcmp` chain |
| new option name | no | compiled chain + table; unknown names dropped |
| a value 0..7 written by a new page | yes | `Dummy2`, see 3.1 |
| a second free value | yes, with a side effect | `Dummy` (it is also `Dummy2`'s enable flag) |
| page shown only with a launch option | yes (ASSUMPTION on `-o`) | `<MainIniOption>` |
| new data text (`TagName`) | no | tag set is compiled |
| grey out a button from XML | yes, statically or by message | `Disabled="True"`; `SendMessage Message="Disable"` |
| grey out by game state (taken) | no | something must decide and send the message |
| new picture | no | pictures are scene entities |
| tenth map entry | no | section 4.3 |
| the game acting on the chosen value | no | section 5 |

---------------------------------------------------------------------------------------------------

## 7. Design (a): heister select

The XML examples in sections 7 and 8 were checked by script against the stock data (`check_md.py`, 147
elements): well-formed; every `Type` is in a factory; every `Template` is defined in the stock
`frontend.xml` or in the example; every `Graphic` is a frontend scene entity or an element of the
example; every attribute name is one the stock XML already uses; every option name is known; every
non-literal text key exists in the frontend `.LOC` except `/Menu/Generic/UseLRToSelect`, which the stock
pages use 13 times and which is absent from the PC `.LOC` too (copied as is). They were not run.

### 7.1 What it writes

Option `Dummy2`, value 0..7 = hero rank = `Hero_01`..`Hero_08`. The opening button also sets
`Dummy = 1`, otherwise a toggle bound to `Dummy2` is greyed.
"No preference / random" cannot be a ninth value (bounds are 0..7); if wanted, encode it as `Dummy = 0`
(not chosen) against `Dummy = 1` (chosen).

### 7.2 Variant 1: one more row on the Arcade map page (smallest)

Copies the stock story page's difficulty row (`PlayMenu`, around lines 2290..2342: `DifficultyData`,
`PMfb#03`, the two arrows, the `ToggleText`). Add to `HeistModeMenu` on the existing Start button:

```xml
<GuiElement Type="OpenWindow" Template="HM_Button" Window="HeistPlayMenu" Text="Button_StartHeist"
            FocusGraphic="HMfbl#01" FadeInDelay="0.15" Y="220"
            Option="Dummy" OptionValue="1"/>
```

and inside `<Window Name="HeistPlayMenu">`, in the `ScreenBaseSize` group:

```xml
<!-- value text, next to HeistChapterData inside the group Name="CenterBox" -->
<GuiElement Type="TextBlock" FadeInDelay="0.15" FadeInTime="0.2" Text="" Name="HeistHeisterData" Y="506" AlignH="Center" />

<!-- arrows, inside the group Name="CenterBoxArrows" -->
<GuiElement Template="OptionsArrowL_T" X="0" Message="Decrease" FocusParent="HeistHeister" Receiver="HeistHeister" />
<GuiElement Template="OptionsArrowR_T" X="0" Message="Increase" FocusParent="HeistHeister" Receiver="HeistHeister" />

<!-- focus bar and the row itself -->
<GuiElement Name="HPMfb#02" Graphic="FocusBar_long#03" Y="417" X="-122" AlignH="Left" Template="FocusBar" />
<GuiElement Type="ToggleText" Name="HeistHeister" Text="%Heister:" X="-100" Y="425" Option="Dummy2"
            FocusGraphic="HPMfb#02" TextReceiver="HeistHeisterData" UseTextReceiverAsFocus="True"
            RecCSFocus="OnFocus" RecCSDefault="Default" FadeInDelay="0.15" FadeInTime="0.2"
            Template="TextIndentX" AlignV="Left"
            HelpText="/Menu/Generic/UseLRToSelect" HelpTextBlock="HelpPlay">
  <Text Text="/Interface/FACharacters/C1" />
  <Text Text="/Interface/FACharacters/C2" />
  <Text Text="/Interface/FACharacters/C3" />
  <Text Text="/Interface/FACharacters/C4" />
  <Text Text="/Interface/FACharacters/C5" />
  <Text Text="/Interface/FACharacters/C6" />
  <Text Text="/Interface/FACharacters/C7" />
  <Text Text="/Interface/FACharacters/C8" />
</GuiElement>
```

All eight keys exist in the frontend `.LOC` (J.C. ... Mitchel). `FocusBar_long#03` exists (instances
`#01..#12` are in the frontend scene; this page's `HPMfb#01` uses `#01`, the story page uses `#02`, `#03`).
Open points: the page has one focusable row today and vertical navigation between two rows on it is
untested; `MercsHeistScoreKeyboard` (`ReceiveAllInput`) may take the up / down keys.

### 7.3 Variant 2: a page with a list (the owner's request)

A new window between `HeistModeMenu` and `HeistPlayMenu`: eight buttons, one per heister; choosing one
stores the value and goes on. Each button is the stock main-menu pattern (`OpenWindow` + `Option` +
`OptionValue`), so every piece is used by the stock XML already.

```xml
<Template Name="HS_Button"   X="300" FadeInTime="0.2" AlignH="Left" />
<Template Name="HS_FocusBar" Type="Graphic" IsFocusGraphic="True" Priority="5" X="290" AlignH="Left"
          AlphaMin="0" AlphaMax="255" FadeInDelay="0.05" FadeInTime="0.1" FadeOutTime="0.01" />

<Window Name="HeisterSelect" LocaleBasePath="AllLevels/Interface/FACharacters" Template="WindowDefault">
  <GuiElement Template="BackgroundTemplate"/>
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Template="HeadlineIcon" Graphic="Icon_Heist"/>
    <GuiElement Template="HeadlineText" Text="%Choose your heister"/>
    <GuiElement Template="LongLineTop" />
  </GuiElement>

  <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="16" Y="24">
    <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="130" Y="60">
      <GuiElement Type="OpenWindow" Name="HS_C1" Template="HS_Button" Window="HeistPlayMenu" Text="C1" FocusGraphic="HSfb#01" Y="186" Option="Dummy2" OptionValue="0" />
      <GuiElement Type="OpenWindow" Name="HS_C2" Template="HS_Button" Window="HeistPlayMenu" Text="C2" FocusGraphic="HSfb#02" Y="220" Option="Dummy2" OptionValue="1" />
      <GuiElement Type="OpenWindow" Name="HS_C3" Template="HS_Button" Window="HeistPlayMenu" Text="C3" FocusGraphic="HSfb#03" Y="254" Option="Dummy2" OptionValue="2" />
      <GuiElement Type="OpenWindow" Name="HS_C4" Template="HS_Button" Window="HeistPlayMenu" Text="C4" FocusGraphic="HSfb#04" Y="288" Option="Dummy2" OptionValue="3" />
      <GuiElement Type="OpenWindow" Name="HS_C5" Template="HS_Button" Window="HeistPlayMenu" Text="C5" FocusGraphic="HSfb#05" Y="322" Option="Dummy2" OptionValue="4" />
      <GuiElement Type="OpenWindow" Name="HS_C6" Template="HS_Button" Window="HeistPlayMenu" Text="C6" FocusGraphic="HSfb#06" Y="356" Option="Dummy2" OptionValue="5" />
      <GuiElement Type="OpenWindow" Name="HS_C7" Template="HS_Button" Window="HeistPlayMenu" Text="C7" FocusGraphic="HSfb#07" Y="390" Option="Dummy2" OptionValue="6" />
      <GuiElement Type="OpenWindow" Name="HS_C8" Template="HS_Button" Window="HeistPlayMenu" Text="C8" FocusGraphic="HSfb#08" Y="424" Option="Dummy2" OptionValue="7" />

      <GuiElement Name="HSfb#01" Y="177" Graphic="FocusBar_short#01" Template="HS_FocusBar" MouseFocusW="239" />
      <GuiElement Name="HSfb#02" Y="211" Graphic="FocusBar_short#02" Template="HS_FocusBar" MouseFocusW="239" />
      <GuiElement Name="HSfb#03" Y="245" Graphic="FocusBar_short#03" Template="HS_FocusBar" MouseFocusW="239" />
      <GuiElement Name="HSfb#04" Y="279" Graphic="FocusBar_short#04" Template="HS_FocusBar" MouseFocusW="239" />
      <GuiElement Name="HSfb#05" Y="313" Graphic="FocusBar_short#05" Template="HS_FocusBar" MouseFocusW="239" />
      <GuiElement Name="HSfb#06" Y="347" Graphic="FocusBar_short#06" Template="HS_FocusBar" MouseFocusW="239" />
      <GuiElement Name="HSfb#07" Y="381" Graphic="FocusBar_short#07" Template="HS_FocusBar" MouseFocusW="239" />
      <GuiElement Name="HSfb#08" Y="415" Graphic="FocusBar_short#08" Template="HS_FocusBar" MouseFocusW="239" />
    </GuiElement>
  </GuiElement>

  <GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Type="GUIGroup" Template="BottomFramePosSize" ShowDebug="True">
      <Platform PC_GC="True">
        <GuiElement Template="BottomFrameMenuBackButton"/>
      </Platform>
      <Platform PC_KEYBOARD="True">
        <GuiElement Template="ButtonBack_INV_GT" />
        <GuiElement Template="BackButtonNoXPos_PC" AlignH="Right" X="0" />
      </Platform>
    </GuiElement>
  </GuiElement>
</Window>
```

and the Start button of `HeistModeMenu` becomes
`Window="HeisterSelect" Option="Dummy" OptionValue="1"` (instead of `Window="HeistPlayMenu"`).

Facts behind it: `LocaleBasePath="AllLevels/Interface/FACharacters"` makes `Text="C1"` the key
`AllLevels/Interface/FACharacters/C1` (rule in 2.6). `FocusBar_short#01..#20` and `Icon_Heist` exist in
the frontend scene. Spacing (34 px, bar 9 px above the text) is the stock main menu's.

**Greyed out when taken.** Each button has a name (`HS_C1`..`HS_C8`), so code can grey it: find it with
`0x83faf0` on the manager and call slot 20 with the string `Disable` (or `Enable`) - the call sequence
`ZGUIToggleGoldOnlyElements` uses at 0x5f24fe..0x5f2520. Statically, `Disabled="True"` on the element does
it (byte at element+0xf9, tested in slot 6 at 0x695151).
Not established: whether a button greyed by message also refuses activation; if not, the hook must also
reject the choice.
- Arcade has one human; the seven AI crew are fixed. Nothing is "taken" there, and the stock code already
  moves the AI that used the chosen hero. So Arcade needs no greying.
- Online / LAN: "taken" is known only from the session. The page then belongs in the lobby or in the
  level (`online.xml`, like the weapon shop), fed by KLHook. Open (stage 4).

Portraits: none exist. A picture next to the list would be a `ToggleImages Option="Dummy2"` over eight
`Graphic` elements, which needs eight new `ZWINGROUP` + `ZWINPIC` entities in the frontend scene (the
scene-join tooling), or none at all for a text-only first version.

### 7.4 The code that has to read it

Only the read side needs the exe (KLHook, in memory; no file patch):

- **Arcade (stage 3, enough for the first version).** Make `[rules+0x33d]` the chosen value instead of the
  random one. Either hook the store at 0x835837 (6 bytes `88 86 3d 03 00 00`, in the constructor, `esi` =
  rules, `al` = random 0..7) or the read at 0x8f5ebd (6 bytes `8a 86 3d 03 00 00`, start of slot 137).
  Replacement logic:

  ```
  p = [0x154d5f4]                 ; options object, null if the menu never created it (e.g. -o DefaultScene boot)
  if p != 0 and [p+0xd4] != 0:    ; Dummy = "a heister was chosen"
      al = [p+0xd8] & 7           ; Dummy2
  mov [esi+0x33d], al             ; original instruction
  ```

  The constructor site is the simplest (runs once per level; menu values are already set). ASSUMPTION:
  nothing between the constructor and slot 137 depends on the byte (it has no other reference).
- **Identity (name, voice).** Follows the hero automatically through the scene path digit (0x588980), so
  no second hook - ASSUMPTION, the Arcade swap code after 0x8f5f63 was not fully decoded.
- **Fragile Alliance online (stage 4).** The index is produced at 0x74ee59 for every player on whichever
  machine runs slot 137. A local option is not enough: the choice must travel in the session. Not solved.
  Candidates to study: reuse an existing replicated per-player field (`m_iRespawnPointSelect`,
  `m_iProtectionSuit`, `m_iUseMask` are in the list at 0x8da640), or KLHook's own channel.
- **Dead Men bodies** are a separate job: the eight `Hero_NN` `ZFFPlayer`s of the level decide what a
  heister looks like; the menu only picks which of the eight.

---------------------------------------------------------------------------------------------------

## 8. Design (b): more than nine maps

### 8.1 What blocks a tenth entry

1. `0x746570` / `0x80c9f0`: nine-byte tables on the stack (index 9 reads garbage).
2. `ZMercsLevelSelectorHeist`: `UpperBound = 8` every frame (0x459ed9) and `cmp ebx,8` (0x929479).
3. The level list has nine FA name slots (slots track).
4. Pictures: `LevelPicture_F01..F09` / `H01..H09` exist, no tenth.
5. `MercsShowInfo` tags (`HeistBriefing`, `LobbyLevelName`, `IsLevelAvailable`) are computed per slot in
   code; a tenth slot has no text there.

A true tenth entry therefore needs: detours on two small functions (both start `83 ec 10 a1 e0 9e d4 00`,
`ret 4`), two byte patches in the selector, a tenth scene name, and the tag code. Not recommended.

### 8.2 Recommended: pages of nine

Keep nine entries per page and let the PAGE choose which nine scene names are in the slots.

- XML: a second map page is a copy of `HeistPlayMenu` under a new window name with its own titles
  (literal text) and the same `MercsLevelSelectorHeist` (it still writes `Heist_SelectedLevel` 0..8).
  The buttons that open the two pages set the page number in `Dummy` (1 = stock maps, 2 = added maps;
  both non-zero, so the heister row stays enabled).
- Code (KLHook): before the scene name is taken - Arcade at `0x7e01a0` (the call
  `level list->vtbl+0x3c(slot)` at 0x7e021a) - read `Dummy` (`[[0x154d5f4]+0xd4]`) and put that page's
  nine names into `[0x168f750]+0x16+slot*0x40`, or answer the `vtbl+0x3c` call from the hook's own table.
  The availability test (`vtbl+0x14`, DLC) must answer true for added maps.
- Caveat: the permutation still applies. Menu entry k of a page loads slot `{0,1,2,3,5,6,4,7,8}[k]`.
- Caveat: the selector element must keep the name `HeistLevel` only if something looks it up by name; the
  exe does not name it (`abi.py`), the XML arrows and Accept do - rename consistently inside the new page.

Example (only what differs from the stock `HeistPlayMenu`):

```xml
<!-- HeistModeMenu: two entry buttons instead of one -->
<GuiElement Type="OpenWindow" Template="HM_Button" Window="HeistPlayMenu"  Text="Button_StartHeist"
            FocusGraphic="HMfbl#01" FadeInDelay="0.15" Y="220" Option="Dummy" OptionValue="1"/>
<GuiElement Type="OpenWindow" Template="HM_Button" Window="HeistPlayMenu2" Text="%Dead Men maps"
            FocusGraphic="HMfbl#06" FadeInDelay="0.15" Y="390" Option="Dummy" OptionValue="2"/>
<GuiElement Name="HMfbl#06" Y="381" Graphic="FocusBar_short#06" Template="HM_FocusBar" MouseFocusW="239" />

<Window Name="HeistPlayMenu2" LocaleBasePath="AllLevels/Menu/Heist" Template="WindowDefault">
  <GuiElement Template="BackgroundTemplate"/>
  <GuiElement Type="MercsHeistScoreKeyboard" Link="False" ReceiveAllInput="True"/>
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Template="ChapterBackgroundTemplate"/>
    <GuiElement Template="HeadlineIcon" Graphic="Icon_Heist"/>
    <GuiElement Template="HeadlineText" Text="%Dead Men maps"/>
    <GuiElement Template="LongLineTop" />

    <!-- pictures: stock ones reused until new entities exist in the frontend scene -->
    <GuiElement Type="GUIGroup" Template="LevelPictureGroup_T">
      <GuiElement Type="Graphic" Name="D01_LevelPicture" Template="LevelPicture_T" Graphic="LevelPicture_H01" />
      <GuiElement Type="Graphic" Name="D02_LevelPicture" Template="LevelPicture_T" Graphic="LevelPicture_H02" />
      <!-- ... nine in all -->
    </GuiElement>
    <GuiElement Type="ToggleImages" Text="" Name="HeistLevelImageToggler2" X="0" Y="0" ShowDebug="True" Link="False">
      <Graphic Graphic="D01_LevelPicture" />
      <Graphic Graphic="D02_LevelPicture" />
      <!-- ... nine in all, same order as the Text list -->
    </GuiElement>

    <GuiElement Type="GUIGroup" ShowDebug="True" Name="CenterBox" AlignH="Right" X="-100" Y="-80" W="384" H="576">
      <GuiElement Type="TextBlock" FadeInDelay="0.05" FadeInTime="0.2" Text="" Name="HeistChapterData2" Y="472" AlignH="Center" />
    </GuiElement>
    <GuiElement Type="GUIGroup" ShowDebug="True" Name="CenterBoxArrows" X="484" Y="-80" W="384" H="576" GeomSpace="2">
      <GuiElement Template="OptionsArrowL_T" X="0" Message="Decrease" FocusParent="HeistLevel2" Receiver="HeistLevel2" Y="464" />
      <GuiElement Template="OptionsArrowR_T" X="0" Message="Increase" FocusParent="HeistLevel2" Receiver="HeistLevel2" Y="464" />
    </GuiElement>
    <GuiElement Name="HPM2fb#01" Graphic="FocusBar_long#01" Y="383" X="-122" AlignH="Left" Template="FocusBar" />

    <GuiElement Type="MercsLevelSelectorHeist" Name="HeistLevel2" Text="HeistLevel" X="-100" Y="392"
                FocusGraphic="HPM2fb#01" TextReceiver="HeistChapterData2"
                RecCSFocus="OnFocus" RecCSDefault="Default" ToggleReceivers="HeistLevelImageToggler2"
                UseTextReceiverAsFocus="True" FadeInDelay="0.05" FadeInTime="0.20" AlignV="Left"
                HelpText="/Menu/Generic/UseLRToSelect" ReceiveAllInput="False" HelpTextBlock="HelpPlay"
                Option="Heist_SelectedLevel">
      <Text Text="%Retomoto Tower" />   <!-- entry 0 -> slot 0 -->
      <Text Text="%Nightclub" />        <!-- entry 1 -> slot 1 -->
      <Text Text="%Bank" />             <!-- entry 2 -> slot 2 -->
      <Text Text="%Prison Break" />     <!-- entry 3 -> slot 3 -->
      <Text Text="%-" />                <!-- entry 4 -> slot 5 -->
      <Text Text="%-" />                <!-- entry 5 -> slot 6 -->
      <Text Text="%-" />                <!-- entry 6 -> slot 4 -->
      <Text Text="%-" />                <!-- entry 7 -> slot 7 -->
      <Text Text="%-" />                <!-- entry 8 -> slot 8 -->
    </GuiElement>

    <GuiElement Type="GUIGroup" Navigation="Horizontal" ReverseNavigation="True" Template="BottomFramePosSize" ShowDebug="True">
      <Platform PC_KEYBOARD="True">
        <GuiElement AlignH="Right" Template="BackButtonNoXPos_PC" HelpTextBlock="HelpPlay" HelpText=" " />
        <GuiElement AlignH="Right" Type="SendMessage" Template="AcceptButton_PC" HelpTextBlock="HelpPlay" HelpText=" " Receiver="HeistLevel2" Message="StartGame" />
      </Platform>
      <Platform PC_GC="True">
        <GuiElement Template="ButtonBack_INV_GT" />
        <GuiElement Type="SendMessage" Receiver="HeistLevel2" Message="StartGame" Link="False" ReceiveAllInput="True" ActivateButton="ZW_SELECT1" />
      </Platform>
    </GuiElement>
  </GuiElement>
</Window>
```

Left out on purpose: `MercsShowInfo TagName="HeistBriefing"` (it would show the stock map's briefing for
the slot), `IsHeistLevelAvailable`, `HeistIndicator`. Fewer than nine real maps: unused entries stay
selectable unless the hook reports their slot unavailable, in which case the selector skips them
(0x9293ee, 0x929479).

Online lobby: the same idea needs the page number to reach every client (the host's slot names must
match the clients'), so it belongs with the online stage. With only the stock nine names changed by
KLHook on all machines the stock lobby works unchanged; its map name text comes from
`AllLevels/Menu/Online/Scenarios/TitleNN` in the frontend `.LOC`.

### 8.3 Without any hook

A stock entry can be renamed in XML for the Arcade page (`<Text Text="%Retomoto Tower" />` in place of
`/Menu/Online/Scenarios/Title01`) while the slot's scene is redirected by the means the slots track
gives (`-o MPMap=`, or the build installed under the slot's name). That is today's test set-up with a
correct title.

---------------------------------------------------------------------------------------------------

## 9. Open questions

1. Is the options object written to the profile (do `Dummy` / `Dummy2` survive a restart)?
2. Does `OptionValue` get written when a `ZNavigator` is activated, and before the window change? (Assumed
   from the stock main menu.)
3. Real element count against the 5096 cap (read `[manager+0x9f48]` in the main menu). Static ESTIMATE
   2026-10-24 (`tools/kl_menu_count.py`): frontend 4730 stock / 4793 live, level 2775 - `re/menu_count.md`.
4. Exact `<Platform>` rule: READ 2026-10-24 (`re/menu_count.md` 2: `PC` or `PC_KEYBOARD`/`PC_GC`, OR-ed). Whether
   switching keyboard / gamepad reparses the XML is still open (`[manager+0xaf68]` is read at reader set-up).
5. Does the `-o Key=Value` store feed `<MainIniOption>`?
6. How keyboard Accept reaches `StartGame` on `HeistPlayMenu` (its button names `PlayLevel`).
7. The rest of `ZGameRulesHeist` slot 137 after the hero is attached (crew swap, identity table).
8. `0x817160` (the online hero index) and which machine runs slot 137 for which player.
9. Whether `Menu/online.xml` in Patch01.zip overrides the level archives' copy.
10. Whether a button greyed by the `Disable` message can still be activated.
11. Who registers the heroes (caller of slot 135) - by the `ZFFPlayer` rank property?
