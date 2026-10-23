# Lobby map names and pictures for expansion maps (plan, 2026-10-23)

Static reading only, nothing run. Trigger: the owner's Dead Men map (slot F01 via `[Redirect]`)
showed as "Subway" in a LAN lobby. Sources: re/menus.md 2.6, 2.7, 4.2, 8; re/fa_slots.md 5, 7;
re/slot_redirect.md 4; re/wardrobe.md (ZToggleText); klhook/klslot.c, mkoverlay.py, klpm.c.

## 1. Where the names and pictures come from (CERTAIN unless marked)

Names. One LOC node serves everything: `/Menu/Online/Scenarios/Title01..09` = Subway .. Radio Tower,
in `Scenes/kaneandlynch<Language>.LOC` (frontend) and repeated in every level's `<L>_Main<Language>.LOC`.
Two readers:
- XML lists: the Arcade selector `HeistLevel`, the search filters and two lists in `Menu/online.xml`
  hold `<Text Text="/Menu/Online/Scenarios/TitleNN"/>` (order 01 02 03 04 06 07 05 08 09). A
  ZToggleText shows child[value]'s text: `%...` literally, anything else via the LOC lookup (0x6712b0).
- The FA lobby does NOT use the XML text: `LobbyLevelNameToggler` has nine EMPTY `<Text>`; the shown
  name is the code tag `LobbyLevelName` (`MercsShowInfoFALobby`), and the exe builds the key itself,
  `Title%02i` with slot + 1 (0x436762, 0x5b6a25, 0x62b1a5, 0x631995; `%02d` at 0x43ab5d, 0x5baef5),
  then looks it up as (folder, key) through the LOC object `[[[0xdd2640]+0xac]+0x94]` (slot 37;
  callers 0x478df0, 0x8c3790 seen). So the lobby title follows the SLOT, never the file loaded
  into it, and the Arcade-page overlay (literal titles) does not reach it.

Pictures. `Graphic="LevelPicture_F01..F09"` names an ENTITY of the frontend scene (`ZWINGROUP` + one
`ZWINPIC`), not a file: names in `Scenes/kaneandlynch.buf` (nine `_F`, nine `_H` Arcade, eleven `_L`
story), pixels in `Scenes/kaneandlynch.TEX` (84.8 MB), both members of `Scenes/kaneandlynch.zip`. The lobby shows them through `LobbyPictureF01..F09`
+ `ToggleImages LobbyImageToggler` (Option `MP_SelectedLevel`, order F01 02 03 04 06 07 05 08 09). The code
that resolves `Graphic=` to the entity was not traced.

What the hook knows at lobby time: the lobby is an online page, no map page is open, so page 0 =
`[Redirect]` rules (klslot.c drops the latch). "Slot F0k will load map M" is `kls_page_now()` + the
rule table, every tick. For Arcade the page is the window name (klpm's playlist sets the override);
mkoverlay already gives each page literal titles and story pictures (page 2 seen live in MP1).

## 2. Routes, cheapest first

A. **Hook answers the LOC lookup (recommended, no XML, no LOC file).** Wrap slot 37 of the LOC
object (the same private-vtable trick klchar.c uses on the options interface): when key is
`/Menu/Online/Scenarios/Title0k` and slot k-1 is redirected on the page a load would use now, return
the expansion map's name from a static buffer; else fall through. Covers the lobby tag, every XML
list that holds the LOC path (Arcade, filters, online.xml), the loading screen / HUD wherever they
print the title, and the client side of a LAN lobby if its hook has the same ini (netcode: the slot
is what travels). Name source: `maps.ini` `[Map.N] Name=` (klpm.c, format a GUESS) or a new
`[Names] DM03=Withdrawal`. GUESS: the slot's signature `(this, folder, key) -> const char*` (or a
string object out-parameter) and whether callers copy the result; both must be read before wiring.
GUESS: the lobby recomputes the tag when `MP_SelectedLevel` changes (it refreshes the togglers each
step, menus.md 4.2), so a page-0 change needs no poke. Risk: a wrong signature crashes the first
menu text; test in TEST build with `Log=2` first.

B. **Write the text object.** The tag's receiver is a stock text block; klhud's proven SetText is on
the hook's OWN ZCHAROBJ texts, and the stock block's set-text routine is NOT read (hud_menu.md 5b).
Dearer than A for one tag only; fallback if A's slot proves unusable.

C. **Patch01 / Overlay XML + LOC.** `%literal` titles in the overlay frontend.xml fix the lists but
NOT the lobby; that needs nine `kaneandlynch<Language>.LOC` members with `Title0k` rewritten
(ASSUMPTION the patch overrides LOC members; needs a LOC writer) and the map's own LOC. One static
table for every page: wrong when a slot holds different maps per page. No-hook installs only.

Pictures (both routes need XML or a scene graft, no cheap data write is known):
- Cheapest, same as mkoverlay does for Arcade: `Overlay\Patch01.zip` frontend.xml with
  `LobbyPictureF0k Graphic="LevelPicture_L0k"` (story art, never the wrong FA map) for each slot in
  `[Redirect]`; mkoverlay gets a `[Page.0]`-style section (`F01.Picture=`). Static per slot: right
  for the lobby because online play always uses page 0.
- Real Dead Men art: replace the `LevelPicture_F0k` texture inside `kaneandlynch.TEX` (same id and
  format) and ship `Overlay\Scenes\kaneandlynch.zip` (whole archive; the Overlay replaces any path),
  or graft a new entity (expansion.md: not started). GUESS for a hook swap: the `Graphic` element
  holds an entity pointer that could be repointed to another `LevelPicture_*`; untraced.

## 3. Certain vs guess, first live check

CERTAIN: lobby name = LOC `Title%02i` by slot via the LOC object slot 37; pictures = frontend-scene
entities; the hook knows the slot->map table at lobby time; the Arcade page already has its own
titles/pictures mechanism. GUESS: slot 37's signature and result lifetime; that the lobby re-asks the
tag on each change; maps.ini format; any picture pointer swap.

First live check (TEST build, Log=2, one process, no network): wrap slot 37 as a pass-through that
only logs `(folder, key) -> result` for keys containing `Scenarios/Title`, open Online -> System Link
-> Create -> lobby, step the map once. Expected: a log line per step with `Title01` then `Title02`,
proving the slot, the key format and the call rate. Then return a literal for `Title01` and confirm
the lobby shows it; then the Arcade list and the search filter without any XML.
