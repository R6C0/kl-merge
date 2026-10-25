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

## 4. Route A implemented (2026-10-24, klhook/kllocname.c, prefix kllnm_)

Static RE results (CERTAIN = read from kl2.exe code or the existing klhud_popup.c use):
- CERTAIN: the lookup is `[[[0xdd2640]+0xac]+0x94]` -> vtable slot 0, thiscall `(this, folder, key, third)`,
  callee pops 12, returns `const char*`. Seen at the call sites 0x47d8c0, 0x8c3790, 0x67efb2, 0x47c2a2.
- CERTAIN: the FA lobby Title key is `Menu/Online/Scenarios/Title%02i` built from slot+1 (0x464b70). Slot 24 of
  ZMercsShowInfoFAFocus (0x490730) resolves a '/'-prefixed key as folder `AllLevels`, key without the slash, via 0x47d8c0.
- CORRECTION: "slot 37" in section 2 is the GUI element's slot 0x25. The LOC lookup is vtable slot 0 of the LOC object.
- CERTAIN: the result is a dictionary pointer nobody frees; callers (0x83e2e0) copy it. A per-rule static buffer is safe.
- NOT found statically: the concrete class and callee of the LOC object. So the hook pins it at run time
  (kllnm_pin): vtable in .rdata, slot 0 is code, and the function holds `c2 0c 00` in its first 1 KB. If any test fails
  the module logs and stays inert.

Design: private copy of the vtable (the klchar.c trick, no code patch, nothing in 0x41e000..0x42a000), the object's
vtable pointer is swapped, slot 0 is wrapped. For a (AllLevels, Title%02i) key whose slot has a [Redirect] rule active,
the wrap returns the rule's name: [Names] <map folder>, else the [Page.N] entry title. Everything else passes through.

ini: `[Names] Enable=0 (default), Log=0, Override=0, <folder>=<text>`. Override=0 is the log-only pass-through
(first live check); Override=1 renames.

GUESS: that the lobby, the Arcade list and the filter all go through this same lookup (the lobby and Arcade title key
format is certain, the filter is not); that the object at the pinned address does not change after the menu is built
(kllnm_tick re-checks the pointer each tick and re-wraps).

Live test (TEST build, one process, no network): `[Expansion] Enable=1`, `[Redirect] F01=DM01`,
`[Names] Enable=1 Log=1 Override=0`. Online -> System Link -> Create -> lobby, step the map. Expect in KLHook.log
"names: LOC object ... now answers through the private vtable" and "names: lookup AllLevels / Menu/Online/Scenarios/Title01 -> 'Subway' (pass-through, Override=0)".
Then Override=1, `DM01=Hot Coffee`: expect "-> 'Hot Coffee' (OVERRIDDEN)" and the name in the lobby, Arcade list and filter.

## 5. Data route built (2026-10-25, tools/kl_lobbynames.py + kl_lobbynames_install.py; offline, NOT installed, NOT run live)
Owner: lobby says "Subway" and shows the Subway picture; random mode should show 4 pictures in one square.
- Name: LOC leaf `AllLevels/Menu/Online/Scenarios/Title0k` (k = slot) of every language's `Scenes/kaneandlynch<Lang>.LOC`
  (CERTAIN by the lobby tag reading, section 1; UNSEEN live). Picture: frontend entity `LevelPicture_F0k` 325x183 via
  `LobbyPictureF0k` in Patch01 `menu/frontend.xml` (CERTAIN by the XML). Same as the Arcade page's? NO: Arcade uses
  `LevelPicture_H0k` 540x304 (DXT5, six tiles) and its own literal titles; only the LOC key is shared.
- Built into C:\kl_build_1024\lobbynames_1025\{set2,set3,rand}: the live overlay scene + 18 entities (LobbyMap_<folder> x12,
  LobbyRand_F0k x6; 325x183, ABGR single tile, pictures = the live Arcade pictures scaled down, cards for The Dig / Flat Raid)
  + rewritten Title leaves; Patch01 re-pointed + the 3 Arcade lists (HeistLevel, two leaderboards) made literal so Arcade page 1
  keeps "Subway". Random: 2x2 = stock slot picture + the slot's maps of pages 2/3 (+ a RANDOM card). `install.py --set 2|3|rand | --undo`.
- LIMIT: static data. A set stays installed for Quick Match too (a Quick Match lobby would show Dead Men names for stock maps).
  Cure (needs klslot.c, not done): look for `<overlay path>.set<N>` first when OnlineSet=N, only in a network session.
- Loading screen: no map-name text key (generic LOC); whether the Loader_Sequence pictures bake a name is NOT checked.
- Other languages get the English names; the three literal Arcade lists are English only.
