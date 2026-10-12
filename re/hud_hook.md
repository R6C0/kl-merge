# klhud.c - the expansion's HUD, Version 2 = the owner's draft (2026-10-11 evening, track V; NOT RUN IN THE GAME)

Second form, after the adversarial review (`re/hud_hook_review.md`: ACCEPT WITH FIXES; its two MUST and seven SHOULD
points are all in - section 8 says where). Nothing of Version 2 has run in the game; nothing is ready for the owner's tab.

Part of KLHook: `klhook/klhud.c` (wired in `klhook.c` at HEAD: `#include "klhud.c"`, `klu_init()`, `klu_tick(game_thread)`),
section `[HUD]` of KLHook.ini, OFF unless `Enable=1`. The draft: https://claude.ai/artifact/ARZVji4pNmpkFz5SFtyTL2 (read
for this version). Draw code: `re/hud.md`; pictures and fonts in the level data: `re/hud_data.md`, `tools/kl_hud.py`.
Words: **proven** = a log line or a picture of the running game shows it; **read** = read in kl2.exe, never run;
**ASSUMED / GUESS** = neither.

## 1. STATE - what is proven to draw and what is not

| thing | state | evidence |
|---|---|---|
| The LOOK in the level data (Impact capitals, chipped glyphs, brush bar pictures) on the five tab maps | **proven**, live on the owner's game | run F2_DM03, the owner's rounds since 15:55 |
| Finding the OSD, wrapping the clock element's Render (private vtable), making ZCHAROBJ texts mid-level, SetText / SetColour from the tick, hiding / showing the stock top-left block | **proven** | runs H1b .. H1q, the probe round 16:32 - 16:41 (`hud: ... 24 texts made`, `stock block hidden`, pictures) |
| A text made by the hook, drawn by the STOCK clock Render with our pair in the element's slots at our place (`Draw=2`) | **proven once** | probe step E3: picture `research/watch/20261011_160216/0029_1895s.jpg` = 'TOTAL $145,000' in our colour, right-aligned at (640, 300); +2 instances a call in the log |
| The hook's OWN Draw call with the corrected xform {0,0,1, 0,1,0, 1,0,0} (`Draw=1`, the default) | **NOT RUN** | the fix (cc1e008, 16:34) was committed after the last round that had the HUD part on (16:37 - 16:41, still the probe hook). The measurement that explains the old invisibility is exact (re/hud.md 9), the call itself has never been made in the game |
| Pictures (`klu_pic`: rule, row blocks, strike-through, money bar, Grid outlines) | **NOT RUN** | see below |
| Version 2's layout (the draft's crew list, round line, money box, the Grid) | **NOT RUN** | compiled only |

**PicTest was never run.** The session that wrote it installed hook 71d133ae (`<work>/build/klhook/hud_owner2`) with
`[HUD] PicTest=1` at about 18:15. `<DD>/KLHook.log`: the process of 16:30:28 is the last one that printed `hud: on`; its
last round ended 16:41:55; it then sat idle (`hud: render: 0 ... draw_on 0` at 17:18, 17:54, 18:15) and no line of the log
says `hud: pictest`. The next processes (18:54:41, 19:01:58: the lead's scripted runs P1 / G1) print no `hud:` line at all:
the game folder's hook is now 37949c06 and its KLHook.ini has no `[HUD]` section. `research/watch/20261011_171409` holds
only those later runs. So: no round, no picture, no log line of the picture primitive exists.

## 2. What Version 2 draws (all of it only while the round runs: session state 0x17 .. 0x19)

- **Crew list, top left.** `DEAD MEN` (coral label) and `5 / 8` (in play or aboard / records in use), then one row a crew
  record in record order: name (the string at `[[record]+8]`, what klcrew.c writes), a tag, the cash he carries. Cash as
  `$540K` / `$1.2M` as in the draft (`CashShort=0`: `$540,000`).

  | state | source | without pictures | with `Plates=1` (the draft) |
  |---|---|---|---|
  | you | record flag 1 clear | name blue `6ea3d6`, cash green `63a65b` | chalk block `f3f0ea`, name `0c0c0d`, cash `1f4a1d`, no shadow |
  | traitor | record flag 2, or score flag 1 | name + cash orange `e8831f`, tag `TRAITOR` | orange block, dark letters, tag `TRAITOR` |
  | dead | status 7 | name `8c3138`, cash `5f2a2f` | + a 3 px strike-through over the name |
  | escaped | status 6 | grey `a9a59d`, tag `OUT` | the same |
  | a fed (klfed.c) | score flag 8 | blue, tag `FED` | the same |
  | crew | else | chalk `f3f0ea`, cash green | the same |

- **Round line**, right-aligned under the game's clock: `ROUND n   LIVES n` (byte score+0x45, byte score+0x44). It
  replaces the 'Round: n' and the skulls of the hidden stock block; the draft's skull icons on the own row and its
  'of 4' are NOT drawn (no skull glyph code and no round count are known).
- **Money box**, right: `TOTAL` (the stock 'Total score' formula, bright green), a framed bar (pictures only), `LOOT`
  (the cash you carry), `REWARDS` (`[score+0x184 + 4 * you]`, the column the stock list reads - Version 1 called the row
  'Banked' because that int was not known then; klfedkit.c 6 named it). Labels coral, values right-aligned.
  The bar's painted part = Loot / Total: OUR meaning, the draft gives the bar none.
- **Kept, the game's own:** the clock, the escape marker and its bars, the ammo panel, the announcements, name tags,
  crosshair. The draft's watch dial, escape dial, weapon dial and painted announcement bars are NOT in the hook: they are
  pictures of the level data (`tools/kl_hud.py`, done as far as the stock elements' own pictures go) or new code-drawn
  shapes that wait for the picture primitive (section 6).
- **Stock top-left block hidden** (`HideStock=1`) while ours draws; shown again at once when the state leaves 0x17 ..
  0x19 (round-over page, score page, intro: other elements, untouched), on a fault, when the vtable wrap is refused, when
  the transform does not read 1280 x 720, on a stock level without `Stock=1` - one routine, `klu_stand_down`, is the only
  way the tick stops drawing with a live OSD. **The game hides the same byte itself**: `0x75f780(osd, b)` writes `+0x25`
  of the clock (0x75f796) and of the player list (0x75f7a8), ten times in the owner's round of 16:32. So the hook reads
  the clock's `+0x25` before it writes 0: when it is 1 the hide is the game's, the byte is left and ours is forgotten
  (the game's own 'show' clears both; the next tick hides the list again). A list found hidden with the clock shown is
  taken as ours (the list is in no other hide group, re/hud.md 2.3).

## 3. The layout (virtual 1280 x 720 pixels, origin top left; at 2560 x 1440 multiply by 2)

Margins follow the game's inset `[0xceeebc]` (0.05 -> 64 px / 36 px; the clock stands at (1216, 36), its escape line at
y 64). The draft's own margin is 2.6 % of the width = 33 px: `Inset=0.026` gives exactly that and moves the game's clock
and ammo panel with it (one .data float; the game's value is put back at the next scene change, so a stock level loaded
afterwards has its own margin). Numbers below are for the default inset.

| box | x | y | size | texts |
|---|---|---|---|---|
| CREW | 64 | 36 | 211 x (30 + 24 x rows) = 211 x 222 | header at y 36: `DEAD MEN` left at x 64, count right-aligned at x 275; rule (picture) y 58, 3 px; row i at y 66 + 24 i: name left at x 70, cash right-aligned at x 269; a row's block (picture) x 62, y - 3, 215 x 22 |
| ROUND | right edge 1216 | 94 | one line | right-aligned at (1216, 94) |
| MONEY | 1005 .. 1216 | 123 | 211 x 86 | `TOTAL` y 123, bar (picture) y 149, 8 px, `LOOT` y 163, `REWARDS` y 187; labels left at x 1005, values right-aligned at x 1216 |

Keys: `CrewX CrewY CrewW Row Rows`, `MoneyX` (the RIGHT edge) `MoneyY MoneyW`, `RoundY`; -1 = from the inset. The draft's
widths (16.5 % = 211 px) are kept; its type sizes are not reachable (one FA font at one size; `TotalFont=1` puts the
TOTAL value into the game's headline font, size never seen).

**`Grid=1`**: every box gets two coral labels - its name with its top-left corner (`CREW 64,36` right of the crew box,
`ROUND 1005,94` and `MONEY 1005,123` left of theirs) and its bottom-right corner under it (`275,258`, `1216,116`,
`1216,209`) - plus `+640,360 LEFT-ALIGNED`, `RIGHT-ALIGNED 640,384+`, `0,500`, `1280,698`. A left-aligned text starts at
its x, a right-aligned one ends at it; a text's y is its top (seen in the E3 picture). With `Plates=1` each box also has a
1 px coral outline and a cross whose arms meet at (640, 360): text and picture coordinates on one screenshot.
**`Grid=2`**: and the draft's own eight rows (J.C. you, Kane, Lynch, Parker traitor, Tommy, Red out, Meldal and Ashkanan
dead; Total $3,400,000, Loot $540,000) in place of the round's, so every state colour is on one picture.

## 4. How (klhud.c sections 1 - 5 have the detail)

- **OSD**: `[[gamedata+0x15dc]]` when the byte beside it is not 0xff - the game's own way (0x588680), which klfedkit.c
  walked live at 18:57. When the holder has a ZOnScreenDisplay2 that is not ready yet (no player list, or the transform
  not written: the first tick of a level - that is when the old code scanned for 125 / 157 ms, log 16:32:53 / 16:37:44)
  the hook WAITS for it; the memory scan runs only when the holder gives nothing, or after 10 s of waiting. Only in an
  Arcade round's states.
- **When a level is over**: the state is dropped when the scene name, the OSD's address or the Arcade rules object
  changes, or the session state is below 0x16. One failed scene-name read with the OSD still standing is ignored (up to
  1 s; nothing is done in those ticks).
- **Cost on the frame path**: the render slot reads its objects directly. Two checked reads (ReadProcessMemory) a
  clock-element call are left - the OSD's and text 0's vtable, the canary for 'this level is gone' - against about 150
  before (about 1,100 system calls a second in place of about 80,000; neither number measured). The tick checks every
  text and every shadow each 100 ms.
- **Render**: the clock element (`osd+0x10cc`, ZFATimeDisplay) gets a private copy of its 11-slot vtable; slot 2 = the
  stock `0x81e090` first, then ours with the same ctx / cam. One heap dword; no code byte.
- **Texts**: 25 objects + 25 shadows (+ 10 Grid labels), made once per OSD through the elements' own path; strings and
  colours set on the main-thread tick under a lock the render slot only TRIES.
- **`Draw=2`**: `0x81e090` read whole - it draws `[elem+0x28]` at `(elem+0x14, +0x18)`, `[elem+0x2c]` at (+2, +2), and
  the escape line + vehicle icon only when byte `elem+0xbc` is not 0, all only in session state 0x19. The hook puts our
  pair, our place and 0 into those four fields, calls it, puts them back.
- **Pictures**: `klu_pic` as the clock draws its vehicle icon (0x81e20b ..): the element's desc copied, width / height
  and ARGB set (the record lies INSIDE the desc at +0xc; its +0x24 is desc+0x30, the colour the stock code writes every
  frame from `elem+0x3c`), `[desc+8]` pointed at a record in the hook's static table. **Read**: DrawChunk copies
  desc[0..1] and memcpy's the record from `[desc+8]` (0x842de9 .. 0x842e03), so nothing of ours is kept after the call;
  the record's size follows the chunk's type `[chunk+0xc]` (jump table 0x842ee4: 1 = 24 bytes, 5 = 40, 6 / 8 = 0x74,
  7 = 0x54 + 64 n). The tick reads the type of pictures 181 and 170 once a level (`hud: pictures: 181 ... chunk type
  N`) and a picture that is not type 5 is not drawn. **GUESS, not read**: width / height = `pixels * T[+0xc]`,
  `* T[+0x10]` (no instruction cited; PicTest's A against B decides it).
- **Gate**: not on a stock level (klsteam.c's verdict 2, as klfedkit.c) unless `Stock=1`.
- **klfedkit.c `HudFade`** writes the same element's cross-fade fields (+0xee0, +0xf00), never +0x25; a hidden element's
  Tick (slot 5) still runs, only its Render is skipped (re/hud.md 2.3). The two parts do not write the same byte; with `HideStock=1` the cross-fade is simply not seen.

## 5. Live checks, in order (the lead; owner away; TEST build of HEAD + this klhud.c; the bank = slot F03 of page 2)

Every run: `[HUD] Enable=1 Log=2 Probe=1`, pictures every 2 s from GO + 5 s to GO + 40 s. A CRASH with the DLL or
0x842d00 / 0x5a6d40 / 0x81e090 in the callers = stop, the dump says which call.

- **H0** `Enable=0`: no `hud:` line; the game as before.
- **H1** `Grid=2 HideStock=0` (Draw=1; the review: the very first run leaves the stock block alone - it is then drawn
  UNDER ours on the same place, which is expected). LOG, in order: `hud: on (Version 2 ...`, `hud: osd ...` (and NO
  `object(s) found by the scan` line: the OSD came from the holder), `hud: element ... now renders through the private
  vtable`, `hud: osd ..., 35 texts + 25 shadows made`, then every 5 s `hud: probe: our first text (Draw=1) appended 1;
  ... SAME SHAPE as the stock clock's`, and `hud: render: ... 0 refused by the checks`.
  **PASS for the own Draw needs BOTH: the `SAME SHAPE` line AND the rows on the picture** - the line compares four
  floats of the appended instance with the clock's (the right test for the old fault), it does not prove the picture.
  **H1h** the same with `HideStock=1`: + `stock block hidden`; the stock block is gone on the picture; at every game
  cut (announcement camera, round end) the list must NOT stand alone: with Log=2 `the game has hidden the FA set itself
  ... left to the game`, and no `stock block shown again` in the same second as a game hide.
  PICTURE at GO + 10 s: top left `DEAD MEN   5 / 8` and the eight sample rows in their colours (J.C. blue, PARKER TRAITOR
  orange, RED OUT grey, MELDAL / ASHKANAN faded red), top right under the clock `ROUND 1   LIVES 3`, `TOTAL $3,400,000`,
  `LOOT $540,000`, `REWARDS $0`, the coral corner labels of section 3. Read off: does a row overlap the next (Row), does
  `ASHKANAN ... $1.2M` fit 211 px (CrewW), do the round line and the clock's escape line collide (RoundY), is the stock
  block gone.
  `NOT the stock shape` or an empty picture with `SAME SHAPE` in the log -> **H1b**.
- **H1b** the same with `Draw=2`: the proven way. LOG `35 texts + 35 shadows made` (the Grid labels get shadows here,
  the stock Render draws a pair). PICTURE as H1, corner labels included, ONLY FROM GO ON (the stock Render draws in state
  0x19): take the pictures from GO + 5 s; in the countdown ours is off and the stock block stays shown, by design.
  If H1 fails and H1b shows, `Draw=2` becomes the default and H1's two probe lines go to whoever reads the Draw next.
- **H2** `Grid=0` (the round's own data), a whole round with bots, BoardAll on: names right, cash follows the looting
  (`hud: text N: ...` lines), a dead bot turns faded red, an escaped one grey `OUT`, `5 / 8` counts down; TOTAL equals the
  stock 'Total score' of a second run with `HideStock=0` (both drawn on one place: only for that comparison); the
  round-over page and the score page look as ever (`stock block shown again` at the state change); round 2 in the same
  process: `osd ... is over` or the same OSD, texts drawn again.
- **H3** `[Bots] Backstab=100`: a bot's row turns orange `TRAITOR`. **H4** `--die --fed-walk` script with `[Fed] Player=1`:
  the own row reads `FED` in blue after the respawn, LOOT follows the money he holds, no doubled text top left.
- **P1** (pictures) `PicTest=1 Grid=1 Plates=1`. LOG: `hud: pictures: 181 (UI_White) handle ... chunk type 5, 170 ...
  chunk type 5` (another type = `IS NOT DRAWN`: stop, the record form for that type is not written), `hud: pictest: A
  ... 1, B ... 1, C ... 1` and `hud: probe: our first picture appended 1; ...`. PICTURE: (a) is anything of A / B / C at
  y 500 at all; (a2) is A 200 x 24 virtual pixels (400 x 48 at 1440p) while B has the car icon's own size - that is the
  width / height scale, a GUESS until seen; (b) the coral bar A against the label
  `0,500` and the outlines against the corner labels: bar from x 400 to 600 and y 500 to 524 = `PicAnchor=1` is right;
  shifted by half its size up-left = set `PicAnchor=0`; (c) is A coral and B chalk (UI_White takes the tint) or both
  white / brush-shaped (then picture 181 is not a plain white after `--look deadmen`: try 182); (d) do the 1 px outlines
  show at 1440p. All four right -> **P2** `Plates=1 Grid=2`: the chalk block behind J.C. with dark letters, the orange
  block behind PARKER, the strike-through over MELDAL / ASHKANAN, the rule, the framed bar 16 % painted.
- **S1** `Stock=1` on stock Subway (page 1): the layout with the stock font; no Steam line caused by the HUD.
- For the owner's tab afterwards: `Enable=1` with what passed (texts only, or `Plates=1`).

## 6. ASSUMED, and what is not done

ASSUMED (in the order it could bite): (a) the own Draw with the right xform is visible - the measurement says so, no run;
(b) `klu_pic`: the sprite's anchor (GUESS: middle), the width / height scale `T[+0xc]` / `T[+0x10]` (GUESS), that
UI_White (181) is tinted by the record's ARGB, that a width / height of 1 px survives (that DrawChunk takes a stack
desc with a static record is READ now, and the chunk's type is checked at run time); (c) the layer
byte orders plates (11) under shadows (12) under texts (13) - the stock pairs use 14 / 15 that way; (d) the per-client
flag dword `[score+0x1d4 + 4 * i]` is indexed like the money array; (e) style 0x44 = left, 0x12 = right at any x (seen
for 0x12 only); (f) ~60 objects made mid-level are freed with the scene (24 were, as far as no leak showed); (g) the
`Draw=2` writes into the clock element inside its own Render call are safe on the render thread (the probe did exactly
that for 9 minutes); (h) the render slot's direct reads: an object freed and its page given back between two ticks
(100 ms) AND with the OSD's and text 0's vtable dwords still readable would fault on the render thread - the canary
covers 'the level went', not a single object going alone; (i) the un-hide before a state-below-0x16 / new-rules reset
writes one byte (1 -> 0) into an element that still reads as the player list: harmless if that level is still up, ASSUMED
harmless if it is freed memory with the vtable dword left (in every round seen the scene name changed first and nothing
was written); (j) the holder's OSD becomes ready within a tick or two (seen: one tick later, twice).

NOT DONE: the draft's dials (watch ring above one minute, escape dial, weapon dial), painted announcement bars, skull
icons, the round-over board, kill feed, pause / shop / front-end pages - each needs either new level pictures or shapes
no stock primitive draws (a ring that empties is not a sprite); FA online (klb_read is Arcade only); localised labels
(English constants); type sizes; stock Arcade's LOOK (`Stock=1` gives the layout only - the font and pictures of a stock
level need `tools/kl_hud.py` on a copy of that level, as `tools/kl_stock_mod.py` builds them).

## 8. The review's points and where each went (`re/hud_hook_review.md`)

| point | what was done | where in klhud.c |
|---|---|---|
| M1 the hook un-hid the stock block the GAME had hidden | the clock's `+0x25` is read before a 0 is written; 1 = the game's hide: byte left, ours forgotten | `klu_hide_tick` |
| M2 two exits left the block hidden with ours off | one routine for every non-drawing exit with a live OSD (latched fault, transform, vtable wrap, stock level, not shown) | `klu_stand_down`, `klu_tick` |
| S1 the scan still ran at a level start | a holder OSD that is not ready is waited for (10 s cap), no scan | `klu_osd_direct`, `klu_current_osd` |
| S2 ~150 ReadProcessMemory a clock-element call | direct reads in the render slot; two checked reads a call as canary; the tick checks every text and shadow; handles read in the tick | `klu_draw_one`, `klu_draw_stock`, `klu_pic`, `klu_draw_ours`, `klu_apply`, `klu_pic_prep` |
| S3 Draw=2 could not show H1b | Grid labels get shadows with Draw=2; with Draw=2 ours shows and the stock block hides only in state 0x19 | `klu_make_all`, `klu_compose` |
| S4 a stale level told only by name and one dword | reset also on a new rules object or a state below 0x16; an empty scene read with the OSD standing is ignored for 1 s; a hide whose state was dropped is taken back | `klu_tick`, `klu_hide_tick` |
| S5 `Inset` outlived its level | the game's value is put back at the scene change | `klu_inset_back` |
| S6 facts not read | (a) the width / height scale is marked GUESS, decided by P1 (a2); (b) the chunk's type is read at run time, not type 5 = not drawn; (c) header line 17 corrected (Tick runs when hidden) | header sections 1, 3, 5; `klu_pic_prep` |
| S7 the probe line is not the picture | H1 passes only with the log line AND the picture | section 5 |

Builds are named by SOURCE, not by hash alone (the review got other hashes from the same klhud.c: HEAD had moved, and
the build is not known to be reproducible): `git archive` of HEAD 4267271 `klhook` + klhud.c sha1 2d1968e1 ->
TEST `G:\kl_scratch\V\test\dinput8.dll` 5da47600, SHIP `G:\kl_scratch\V\ship\dinput8.dll` 769578a7, no warning.

## 7. History of the hook side (runs H1 .. H1q, the probe)

CLAUDE.md's 'HUD MERGE' entry and `git log -- klhook/klhud.c` hold every run. In one line each: the OSD is not at
`[0x154da50]` (H1); drawing after the OSD's slot 55 is too late (H1c) -> the clock element's own Render is wrapped (H1d);
every Draw the hook issued was invisible, own objects and borrowed ones alike (H1e .. H1n), while a string put into a
stock object before the stock draw shows (H1l) -> Reuse=2 put our rows into the stock list's five pairs (H1o .. H1q);
the owner's probe round (16:32) measured the instances: the hook's xform had been misread (re/hud.md 9). Version 2 drops
the Reuse / Borrow / Hijack / Before test keys and the five-step probe; `Probe=1` now logs the one comparison that
matters.

## 9. After Version 2 (kl-merge-76, 2026-10-11 evening; compiled only, NOT RUN)

- 83b8772 `[HUD] Dials=1`: the round WATCH and the ESCAPE DIAL of the owner's draft (re/hud_layout.md). A ring that
  empties is 24 brush dabs (extra picture 113) on a circle, the part that is LEFT drawn; the watch = disc (114) + ring +
  a hand of five small dabs, fraction = `[rules+0x200]` (the round clock, klfed.c) against the longest value seen this
  round; while it stands the stock clock's two texts get " " right before the stock Render (`klu_clock_face`, the H1l
  way), in the last minute the digits stay and are set coral. Escape dial = disc + an ORANGE ring of `[rules+0x1d8]` / 8 s
  while the vehicle's state is 3 / 4 + the car icon (170; the helicopter's kind is a virtual call, not read). With
  Dials the round line and the money box sit 14 px lower. Needs the level's extra pictures: `klu_pic_prep` now reads a
  handle for EVERY picture slot and says how many of 111..118 the level has.
- Painted rows use 111 (stroke) and the strike 112 (dry) when the level has them, UI_White (181) otherwise.
- Live check D1 (after H1, P1, X0): hook `<work>/build/klhook/hud_v3_test`, the bank archive `<work>/build/hud_x/DM03`
  (the installed one + the extras), `Enable=1 Log=2 Probe=1 Grid=2 Plates=1 Dials=1 HideStock=1`.
- THE WEAPON DIAL IS NOT BUILT. Read so far (0x88bac0, ZWeaponDisplay's inner tick; element at osd+0x1110, vtable
  0xbbe8c0, Render 0x5ec380): the player is `[elem+0x10]`; the gun in hand `[player+0x920]`, the other `[player+0x924]`
  or 0x748430(player), else looked up in the inventory `[player+0xcec]` by 0x49b2f0(inv, item, 4); per slot i a state
  byte at elem+0x2f8+i / +0x2fa+i (0x40 = drawn), a colour at elem+0x2f0 + 4 i, the picture index at elem+0x2e8 + 4 i.
  Where the magazine's rounds, its size and the reserve are read is NOT established - that is the next reading before
  the dial can replace the stock panel (hide byte elem+0x25).

## 10. Version 3: the parts wired (2026-10-11 night; builds compile at /W3 without a warning; NOTHING OF IT HAS RUN)

Three reviewed parts (re/hud_values.md, re/hud_weapon.md, re/hud_popup.md) are now in the hook. Include order in klhook.c:
`klbot.c ... klgrudge.c`, `klhud_values.c` (reads only, needs klb_snap), `klhud.c` (which includes `klhud_weapon.c` just before
`klu_row`, after `klu_dials`), `klhud_popup.c` (after klhud.c). `klpu_init()` after `klu_init()`, `klpu_tick()` after `klu_tick()`.

### 10.1 What each part adds to klhud.c
- VALUES: lives are the byte `[score+0x6c]` (the old `KLU_S_LIVES` 0x44 was the number of rounds); three skull pictures (178) in
  the own row (`klu_lives_row`; 'LIVES n' in the round line when the level has no 178); the row kind is `kluv_kind` (the one
  decision: dead / waiting, escaped, fed before traitor, traitor, you, crew); round line 'ROUND n' + ' OF m' (RoundOf); the money
  bar = what the crew holds of the level's loot (`kluv_loot_share`); the watch = `kluv_round_left / _len / _played`; the escape
  dial's icon 170 or 171 (`kluv_vehicle_pic`, a ZHeli = 171); `kluv_dump` at Log=2.
- WEAPON: three texts (`KLU_T_WEAP` .. +2: first count right-aligned, second count right-aligned, label centred), disc / ring /
  divider / arrow as klhud pictures, the two gun pictures (type 6) in its own queue drawn from the ammo panel's private
  vtable (osd+0x1110, slot 2); `klwd_compose()` straight after `klu_dials`; `klwd_show` at both places klu_draw_on is set,
  `klwd_reset` in `klu_reset`.
- POPUP: nothing in klhud.c except the key `Draft` it reads; it wraps osd+0x10a8 (announcements) and reads osd+0x110c.

### 10.2 Conflicts and how they were settled
- Text objects: only the weapon part adds texts; `KLU_NTEXT` is `KLU_T_WEAP + KLU_NWEAP`, last. Values and popup add none.
- Private vtables: four different elements are wrapped (clock 0x10cc by klhud.c, ammo 0x1110 by weapon, announcements 0x10a8 by
  popup); none twice. The hide byte (+0x25) is written only by klhud.c, on the player list (0x10c4); weapon and popup never write it.
- THE KNOCK-DOWN PROMPT (kldown.c, ZMiniGameButtonMashingDisplay at osd+0x10fc) is read, hidden, wrapped or restyled by NO
  part (grep of the four files for 0x10fc: none).
- The shared picture record slot `klu_prec[KLU_NPIC]` is used by PicTest and by popup / ring: DrawChunk copies the record
  before it returns and all three run on the render thread one after the other.
- `klu_pic_prep`: now also asked for when `Weapon` is on; popup calls it itself when it finds `pic_done` 0.
- `LeftStyle` stays the one `KLU_STYLE_LEFT` (default 0x11); Grid / Probe untouched.

### 10.3 Keys ([HUD]; every one needs Enable=1)
`Draft=1` is the owner's switch: Plates, Dials, Weapon, RoundOf, Popups, LootRing default to 1 (HideStock and Lives are on by
default anyway). Any key that is written wins (`Dials=0` with `Draft=1` = no dials). The sample klhook/KLHook.ini was not
edited (another session has it uncommitted); the list is in klhud.c's header:
`Draft Lives RoundOf Weapon WeaponX WeaponY WeaponSmall WeaponOther Popups LootRing PopupFrame PopupMeasure PopupPadX PopupPadY
PopupDY PopupY PopupLayer PopupTraitor PopupTest RingMode RingX RingY`.
Suggested for the owner: `[HUD]` `Enable=1` `Draft=1` `PopupY=520` (after Q2b).

### 10.4 Live checks, in order (TEST hook `hud_v6_test`; the bank with the extras `<work>/build/hud_x/DM03`; log `Log=2`)
Stop at once for a crash with `klwd_`, `klpu_`, 0x5ec380, 0x4895b0, 0x842d00, 0x45d6e0 or 0x639700 in the callers.
- **A0** `Enable=1 Log=2` only: as Version 2 (list, round line, money box); the round line reads `ROUND n   LIVES m` unless the
  level has picture 178; no `hud: weapon:` or `hud: popup:` line except the start-up 'on' of klu.
- **A1** + `Plates=1 Dials=1 Grid=2`: skulls (2 dark, 1 faint) in the first demo row, the bar at 16 %, watch and escape dial; log
  `hud: values: lives ...`, `clock: left .. played .. length .. ring ..`.
- **W1** + `Weapon=1`: see re/hud_weapon.md W0-W6 (the log's `render: N stock panel calls skipped, 0 passed, 2N gun pictures drawn`;
  the disc at about (1145, 598), no stock ammo panel).
- **Q1** + `Popups=1 PopupTest=1 PopupFrame=1`, then Q2 .. Q3b of re/hud_popup.md; **R1** `LootRing=1 PopupTest=1`.
- **K1** the knock-down prompt with everything on: `[Down] Enable=1 Flop=3 Camera=1 Prompt=1`, go down: the game's own mash
  bar must show unchanged (no restyle, no hide) while the weapon dial shows the empty disc or the normal dial (not a fault).
- **D0** `Enable=1 Draft=1`: the whole draft; the log's 'hud: on (Version 3 ...)' line says Dials=1 Weapon=1 Lives=1 RoundOf=1, then
  `hud: popup: on; Popups=1 LootRing=1`. Round 2 of the same process (reset path), then a stock level (nothing drawn, stock HUD whole).

### 10.5 Guesses that remain
The ones named in each part (re/hud_values.md 'Remaining guesses', hud_weapon.md 9, hud_popup.md 10), plus: 'OF 10' is nominal
(RoundOf follows Draft here because the draft shows it; `RoundOf=0` removes it); the extra picture slots 111..118 must exist
in the level (Draft on a level without them falls back to plain bars and shows no rings / dials / weapon dial).

### 10.6 Review round (re/hud_v3_review.md; hooks `hud_v7_test` 8d37f104 / `hud_v7_ship` bb8f2318; NOTHING OF IT HAS RUN)

Built from `git archive HEAD klhook` + the working tree's klhud.c, klhud_weapon.c, klhud_popup.c, klhud_values.c and klhook.c (its
uncommitted diff is only the HUD wiring: include order, klpu_tick, klpu_init). TEST `build_auto.bat`, SHIP `build.bat`, /W3, no warning.

| finding | result |
|---|---|
| M1 positions | DONE. `Draft=1` defaults CrewX 33, CrewY 38, MoneyX 1247 (klhud.c) and WeaponX 1177 (klhud_weapon.c); a written key still wins. Inset untouched. |
| M2 rows | DONE under Draft: Row 30, text y = top + 34 + 30 i, name x = left + 8, cash right = right - 8, block 28 high starting 5 above the text (`klu.yoff / blockup / blockh / padx`), dead strike (name width estimate + 12) x 4 at name y + 7 from left + 2, rule = pic 112 (181 if absent) 211 x 5 at top + 19.5, skulls at name y + 3. Without Draft the Version 2 numbers (30 / 4 / row / 6) are unchanged. The name width is still the 9 px a character estimate. |
| M3 stock escape line | DONE. `klu_render_elem` zeroes byte elem+0xbc around the stock Render and puts it back, only while Dials=1, our HUD draws, `el` is the wrapped clock element and pictures 113, 114, 170 are in the level (else the stock escape line stays: no dial would show instead). |
| S1 klwd_reset unlocked | DONE: inside klu_cs in `klu_reset`. |
| S2 lock busy blinks | REJECTED for now: the busy count is already in the 5 s 'render:' line; only a log of W1 can say whether it is visible. The fix (queue built off-lock) is larger than the risk shown. |
| S3 popup swap race | REJECTED (probability tiny, which thread runs Render still suspected; watch Q2 for a message that vanishes early). |
| S4 instance bound | DONE as a measurement: the 5 s 'render:' line (Log=2) ends 'largest instance count after our draws N' (`klu_n_maxinst`, the largest [ctx+4] seen after the clock element's draws). Read it in A1 / W1 / D1. |
| S5 round line coral | DONE under Draft (the draft's colour); Version 2 look keeps chalk. |
| S6 Lives default | DONE: Lives defaults to 1 only with Draft=1, else 0, so A0 (`Enable=1 Log=2`) has no 'LIVES n' and looks like Version 2. |
| S7 level without extras | DONE: with Draft=1 `klu_pic_prep` logs 'hud: draft: this level has N of the 8 extra pictures: Draft=1 falls back ...'. |
| S8 rebuild of the five maps | NOT DONE here (tooling, not hook): `kl_hud.py all` on each installed archive into build/hud_x2/<map>; hud_x2 holds DM03 and F01 as .zip only, so V1 copies the support files (.WHD .WAV .ini .hti) from hud_x/DM03. |
| S9 text objects never freed | DEFERRED: ~56 objects a round; reuse needs a per-OSD cache, not worth an unrun change. |
| N7 83-check test of klhud_values | NOT RERUN: the harness is not in the repo (it lived in an earlier session's scratch folder) and klhud_values.c is unchanged this round; the file compiled with the wiring at /W3. |

#### Owner's ini lines (after V1 has passed; SHIP hook hud_v7_ship, the archive of his map rebuilt by kl_hud.py)
```
[HUD]
Enable=1
Draft=1
PopupY=520
```
(Log=1 default; add `Log=2` for a round that is to be read.)

#### Live check V1 (TEST hook `hud_v7_test`; owner away; the bank, slot F03 of page 2)
1. Level archive: `<work>/build/hud_x2/DM03/F03_Main.zip` (200,769,316 bytes) in place of the tab's DM03 `.zip`, the support files
   (.WHD .WAV .ini .hti .KLJoin) of `<work>/build/hud_x/DM03` beside it. The previous archive is `<work>/build/hud_new/DM03`; put it back after.
2. KLHook.ini: `[HUD] Enable=1 Draft=1 Log=2 Grid=0`. Hook test_v7 = `<work>/build/klhook/hud_v7_test/dinput8.dll`. Idle player,
   pictures every 5 s from GO.
3. Log must show, in order:
   - `hud: on (Version 3 ...; Draft=1 Dials=1 Weapon=1 Lives=1 RoundOf=1) ...` and `hud: weapon: on`, `hud: popup: on; Popups=1 LootRing=1`.
   - `hud: pictures: 8 of the 8 extra pictures (slots 111..118 ...) are in this level` (and NO 'hud: draft: this level has' line). The Log=2
     lines `slot 111 .. 118: handle ... type 5` are the answer to the one open loader guess (a slot with no table row gets flags 0x10, type 5):
     a slot with handle 0 or another type = the guess is wrong, stop and read re/hud_extras.md.
   - `hud: osd ... N texts + N shadows made ... crew list at (33, 38) 211 wide, 30 px a row; round line right-aligned at (1247, ...); money box right edge 1247`.
   - the 5 s `hud: render:` line: text draws > 0, `pictures` > 0, `pictures refused` 0, `lock busy` small, `largest instance count` (note it; hundreds is expected).
   - no fault line (`stands down`, `no longer has ZCHAROBJ's vtable`).
4. Pictures must show (bank at GO, then at +60 s): the crew list at the screen's left margin 33 px / 38 px (coral DEAD MEN, count right
   at x 244, the white rule), rows 30 px apart with your row on a chalk block 219 x 28 (ink name, dark green cash, three skulls
   after the name), a traitor row orange; coral ROUND n OF 10 right-aligned at x 1247; the round watch (ring of 24 dabs and a hand)
   centred about (1212, 66), the stock clock digits blanked; the orange escape dial at about (1137, 71) when the vehicle waits and
   NO stock 'escape' text or second vehicle icon beside it (M3); the money block with coral labels from x 1036; the weapon dial
   centred about (1177, 598) with the stock ammo panel gone; coral green money. Compare against hud_mockup.html side by side.
5. Then: a second round in the same process (reset path), and a stock level (nothing of ours drawn, the stock HUD whole). With the
   knock-down (`[Down] Enable=1 Flop=3`) the game's own mash bar must show unrestyled.
6. Stop on any crash whose callers include klwd_, klpu_, 0x5ec380, 0x4895b0, 0x842d00, 0x45d6e0 or 0x639700.

#### Guesses that remain after this round
The loader's type 5 / flags 0x10 default for slots 111..118 (V1 log); the name width (9 px a character) behind the skulls and the
strike; the draft's skull y (name y + 3) and the rule's 112 stroke height; whether DrawChunk's instance array has room for the
frame (V1 prints the largest count); 'OF 10'; the weapon dial layout; the popup parts of re/hud_popup.md 10.

## 11. 1:1 with the draft (2026-10-11 night; owner: 'its all that one font, i want it to be 1:1 with the draft ... texts in the white gritty boxes were offset, they need to be in the middle'; review re/hud_1to1_review.md; builds compile, NOTHING OF IT HAS RUN)

### 11.1 Type table (kl_hud.py DRAFT_SPECS; draft px at 1280 wide, 1 cqw = 12.8 px; baked = about 0.9 x draft: Anton is NOT installed, Impact is wider and heavier, so the 0.9 is a GUESS)
| baked font | face, px, track, cap | hook role (osd offset) | draws | draft |
|---|---|---|---|---|
| H2 | Impact 19, 1, 16 | NAME (+0xd54) | names, money rows, weapon dial's active count, the POP-UP (SetFont swap) | names 20.5, money rows 23, count 20.5, pop-up 22.4 |
| H1 | Impact 30, 1, 24 | BIG (+0xd50) | the total | 33 |
| H3 | Impact 15, 0, 13 | SMALL (+0xd58) | cash, crew count, reserve, off-gun count; stock: subtitles, tracker distance | cash 16, count 16, tracker 20.5 |
| DebugText | Segoe UI Black 13, 3, 9 | LABEL (+0xd5c) | DEAD MEN, ROUND, TOTAL / LOOT / REWARDS, gun name | Montserrat 800, 11.5 px, .32em |
| Button, Text, Menu, Header | Impact 16 / 19 / 19 / 25 | - | stock only | - |
Why this assignment (review MUST 3 / 4): H1 used to serve total, ammo and pop-up at 26 (draft 33 / 48.6 / 22.4). The ammo number is the weapon dial's count in
the agreed draft (1.6cqw = 20.5 px), so it moves to H2; the pop-up moves to H2 as well (draft 22.4, baked 19 = 0.85); H1 is now the total's alone (30 = 0.91).
The label face moved from H3 to DebugText because stock draws with H3 (subtitles, tracker: tracked Segoe Black 13 px would have made them small and wide)
and nothing stock draws with DebugText. +0xd5c AS DebugText is read from re/hud_data.md's property order ([0] template at +0xd4c, [1..4] H1 H2 H3 DebugText =
+0xd50 .. +0xd5c), not seen live: if it is no font object the hook logs it and the labels take the SMALL font (Impact). All four roles are checked for the FA font's
vtable and a log line warns when two roles resolve to ONE object (a wrong offset, or a level baked before this round).
`kl_hud.py check` now asserts header[9] = -cap and line height = round(1.3 cap) + 2 for every DRAFT_SPECS font (--look deadmen), and `all` prints the
`[HUD] Cap0..Cap3` line (16 24 9 13 = klhud.c's defaults). An archive baked BEFORE this round (hud_x2, an owner map not rebuilt) mis-places text 2 - 8 px: rebuild it.

### 11.2 Centring (computed; the rule is the one the crew rows already used)
The game puts a text's baseline at y - header[9]; the bake sets header[9] = -cap, so the capitals of a text drawn at y span y .. y + cap.
- Row: block middle rc = row top + 9 (block y - 5 .. y + 23). name y = floor(rc - 8 + .5) = rc - 8 (cap 16), cash y = floor(rc - 6.5 + .5) = rc - 6 (cap 13): ink centres rc and rc + .5, equal within half a pixel. Left and right padding 12 / 8 as built.
- Labels: the tracking (3 px) is baked after the LAST letter too, so right-aligned labels get x + 3 and centred ones x + 1.5 in the draw loop (klhud.c KLU_TRACK); the preview does the same.
- POP-UP (klhud_popup.c): the stock top-aligned style is kept (no SetStyle any more); while a bar or box shows, text and shadow take the NAME font (SetFont +0x23c, the font read from +0xac and put back with the colour). Bar middle = PopupY (default 523 = the draft's .toast: bottom 547, 47.7 high), letters' top = floor(PopupY - 16 / 2 + .5) = 515, so the capitals' middle lies on the bar's middle within 0.5 px by the baked metric. Bar = text width (the object's own half extents) + 61.4, height 33.6 + 14.1 = 47.7 (the draft's constant, no longer 1.6 x a measured extent). Several lines: + 30 a line, the bar's middle follows the block's. The traitor message uses the same rule, its box 5 px outside.
- Loot ring: 40 dabs on r = 26 (unchanged); not shown to fail by the log (klpu_n_ring counts draws); PopupTest (below) shows it.

### 11.3 Live check T1 (TEST hook <work>\build\klhook\hud_v11_test, archive <work>\build\hud_x3\DM03 through the bank's slot; the owner away; the monitor on)
KLHook.ini: `[HUD] Enable=1 Draft=1 Log=2 PopupTest=1` (+ the owner's PopupY 520 is fine). Pictures every 2 s from GO + 15 s for 40 s. Lines to find, in order:
1. `hud: fonts: names ..., big ..., labels ..., small ...; caps 16 24 9 13` - four DIFFERENT object addresses; any `WARNING roles N and M resolve to ONE object` or `the label role (+0xd5c) is no font object` is the answer to the role question (report, do not fix live).
2. A picture of the crew rows: names and cash centred in the chalk block (own row) and in the orange traitor block, the label face visibly different from the numbers (heavy tracked Segoe against Impact).
3. PopupTest, 12 s cycle on the wall clock: 0 - 4 s the chalk bar with 'LOOTING HAS STARTED. TRUST NO-ONE' in Impact on the bar's middle, bar 47.7 high; 4 - 8 s the traitor box, orange letters; 8 - 12 s the loot ring at 60 %. Log: `hud: popup: TEST message ...`, then the per-message line with the bar size (expect bh 47.7, bw = text + 61.4).
4. A stock subtitle / tracker distance and the round-over page (H3 is now a 15 px Impact: small caps, not the wide tracked face) - one picture each; the top-right: TOTAL (H1 30) against the 'ROUND n OF m' line (4 px clear in the preview).
Pass = no fault, no ONE-object warning, the pop-up letters' middle on the bar's middle (measure the picture), loot ring visible in phase 3.

### 11.4 Guesses left
Anton's real cap height (the 0.9); +0xd5c as DebugText; SetFont on the stock announcement text (+0xac holds the font; its width is read from the same frame's layout, one frame stale at worst); H1 on the stock announcement element is replaced only while OUR bar shows; the old baseline 13 of non-centred texts (the total, the weapon counts) - unmeasured; the draw-instance budget (up to 168 ring dabs + rows; klu_n_maxinst logs the peak); everything is baked for the 1280 x 720 virtual screen (soft at 1440p).
Decision for the owner: a real Anton / Montserrat would need installing the two fonts on the baking PC only (OFL; the glyphs are baked into the level) - previously declined; without them the display face stays Impact and reads as one face.


## 12. Quieter sizes + the escape element (2026-10-11 night; owner: 'the player scoreboard text should be smaller than the dead men one ... some of the other text on the HUD should be like that as well so its not all in your face'; 'you can keep it via the restyle you said'; review re/hud_sizes_escape_review.md; builds compile, NOTHING OF IT HAS RUN)

### 12.1 Sizes (the quiet round; kl_hud.py bake + the hook's Cap defaults, which must agree)
| font role | stock role | cap before -> now | line height | used by |
|---|---|---|---|---|
| H2 (names, +0xd54) | name tags, crew rows, prompts | 19 -> 11 | 16 | rows, tags, escape time + prompts |
| H1 (big, +0xd50) | intro countdown, headline, pop-ups, round-over | 30 -> 15 | 22 | pop-up bar, round line |
| DebugText (labels, +0xd5c) | small labels | 10 -> 10 | - | labels |
| H3 (small, +0xd58) | subtitles, tracker | 15 -> 10 | 15 | subtitles |
Hook defaults Cap0..3 = 11 / 15 / 10 / 10. A level baked BEFORE this round (hud_x4, any map installed with the old `kl_hud.py all`) keeps cap 19 / 30: its text is then centred 4 to 8 px off with this hook -> ship the hook and the rebaked levels TOGETHER (review S4; reading each font header's header[9] is not done). KLPU_LINE_STEP 24 -> 22 (S8). The shared roles also shrink the knock-down prompt (osd+0x10fc, kldown.c's, untouched), the human-shield break-free prompt, the intro countdown and the round-over text (S5): look at them in the next run.

### 12.2 The escape element (klhud_escape.c, re/hud_escape.md)
`[HUD] Escape=1` (default = Draft) restyles ZFAEscapeDisplay ([osd+0x111c], bottom centre): the dark plate is not drawn (its Draw slot is wrapped in a private vtable copy), a chalk bar (picture 111) carries the time in ink letters (names font, centred), the vehicle icon is orange (state kept: green arriving, orange waiting, coral leaving), the vehicle health is a framed bar, the two prompts ('Q Share 50/50 ...', 'SPACE Hold escape vehicle') are chalk, centred. The stock '00:04' plate, the health bar and the prompts are one element, so it is restyled, not hidden. Fallback keys: Escape=0, EscapeCentre=0, EscapePrompts=0. Wired in klhook.c: include after klhud_popup.c, klesc_init() before klpu_init(), klesc_tick() before klpu_tick().
Review fixes: M1 the colour is a DWORD with a set flag (ink / chalk were negative ints and never applied); S1 a refused wrap is retried after 3 s, only a wrong Render code is for good; S2 one log line per stand-down reason ('hud: escape: stands down for this call: ...'); S3 klesc_forget clears records without writing. Not done: S6 (no text-only offset key; E1 shows whether style 0x14 sits right), the popup's own put-back statics are left (its comment says they are deliberate).

### 12.3 Live check S1 (owner away; hook hud_v15_test, archive <work>\build\hud_x5\DM03 swapped in for the run)
Ini: `[HUD] Enable=1 Draft=1 Log=2`; the whole-heist script on the bank; pictures every 2 s. Log lines to find: `hud: escape: on; icon 30 px ...`, `hud: escape: element ... now renders through the private vtable`, `hud: escape: the plate object ... now draws through the private vtable`, `hud: escape: anchor (...) ... fraction ...` (once), then every 5 s `N element calls, N painted frames, 0 frames without a picture`. A line `stands down for this call: ...` names the reason.
Pictures must show:
1. Round start / crew list: names smaller than before (cap 11), skulls 11 px matching the cap, nothing clipped; pop-up (traitor box) and the round line smaller, text centred in the bars.
2. Money box under TOTAL, weapon circle counts, watch ring: centred with the smaller caps (S4: if 4-8 px off, the level was not rebaked).
3. Aboard (escape): NO dark stock plate; a chalk bar with the time in DARK letters (M1: not grey), orange icon left of it, a framed health bar below with an orange fill, both prompts chalk and centred under the bar. If the stock red icon / bar still shows, an alpha-0 picture draws (the main guess); if the time and the bar disagree vertically, style 0x14's anchor (S6) -> EscapeDY moves the pictures.
4. Last: the knock-down prompt, intro countdown and round-over page if they come up (S5) - small but readable.
Fall-back to compare: same run with `Escape=0`.

## 13. Rings as a stroke (2026-10-12; owner: 'i dont want the circles to have that circle circle' - the rings were strings of round dabs, then a dotted thin track)
How it is built (tools/kl_hud.py ARC_*, klhud.c klu_arc / klu_dabs / klu_track, mirrored number for number in `preview-hud`):
- A ring = 3 baked slices of 120 degrees, clockwise from the top; each is a square texture holding the WHOLE ring's bounding square with only its slice painted
  (centre-line radius 0.40 of the side), so slices drawn at the ring's square join. Family A (stroke 0.23 of the radius; watch, escape dial, loot ring) = slots
  123 / 124 / 125, 128 px; family B (0.12; weapon dial) = 126 / 185 / 190, 256 px (each drawn at most ~2x smaller: review S3, no mips are known). The slots are the
  17 that no stock row names (re/hud_rings_review.md). Slice 0 has the round cap at 0, slice 2 at 360.
- The part of a ring that is left = the slices wholly inside it + ONE run of dabs (113) at its moving end, step 0.4 of the stroke and at most 2.5 px, dab size x 0.97
  (S1 / S2). A level baked without the slices (hud_x2 .. x5) draws the whole stroke as dabs (S4).
- The thin track (slot 115) is now 128 px, an UNBROKEN line 2.7 texels wide (was 512 px, 5.6 texels, six breaks = the dotted circle; M2), under the stroke at the same radius.
- Review M1: klesc_full_alpha is gone (the stock Render rewrites the prompts' alpha every call: 0xff usable, 0x3f dimmed; the faint prompts are the game's own dimmed state).
  S5: small-font shadow 0x40 -> 0x60. Weapon circle KLWD_S 0.85 -> 0.76 (owner: 'could shrink the weapon one slightly').
- Worst case a frame about 205 pictures (weapon 45, watch 50, escape 28, loot 25, the rest of the HUD); the queue is 288, the draw list held 280.
- Level `<work>/build/hud_x6/DM03` (kl_hud.py all <hud_new/_src/DM03> <out> --look deadmen, check PASS), preview `<work>/build/hud_x6/preview.png`; hooks `build/klhook/hud_v17_test` / `hud_v17_ship`.
### 13.1 Live check R1 (owner away; hook hud_v17_test, archive hud_x6/DM03 swapped in for the run)
Ini `[HUD] Enable=1 Draft=1 Log=2`; the whole heist on the bank, pictures every 2 s. Look at: watch (top right), escape dial (aboard, left of the watch), weapon circle (smaller, ring
one smooth stroke, no dots), the thin track an even line. Log lines: `hud: on (Version 3: ...`, the escape lines of 12.3, no `stands down`. If the rings are broken into dashes the textures
are minified without mips: bake the slices at the drawn size.
R1p: the same, idle player, `PopupTest=1` added: the loot ring (dark disc, unbroken thin ring, stroke filling from the top, green dollar) and both pop-ups.

## 14. The watch (2026-10-12; owner / JC on the draft: 'black bar bottom right to make gun name more pronounced and a / to distinguish between gun name and ammo reserve', 'clock needs a rehaul and the circle on the gun', 'make the clock more like a watch like rolex hands and a bit more wear n tear'; builds compile, preview rendered, NOTHING OF IT HAS RUN IN THE GAME)

Chosen from three previews: A's watch (bezel, 60 pips, a triangle at 12, batons, Mercedes hour hand, sword minute hand, worn dial) with C's economy (no seconds hand by default) and C's weapon
circle (a stroke on a dim track, a big count, a hairline, a dim second gun) and A's label (a black bar, a coral slash, a dimmer chalk reserve). Wear is alpha only and LIGHT; no new picture slot.
The model is `tools/kl_hud_watch.py` (picture lists, number for number what klhud.c queues) with `tools/kl_hud_wprev.py` (a canvas that draws them with a baked level's real textures and fonts);
the hook's constants are `KLW_*` / `KLWD_LB_*` in klhud.c / klhud_weapon.c.

### 14.1 Textures (tools/kl_hud.py `--watch 1`, default; EXTRAS_NEW; all alpha, tinted at draw time; `check` regenerates every extra and compares the pixels, so a level baked with the other look FAILS)
| slot | was | now | size | content |
|---|---|---|---|---|
| 114 `disc` | plain disc | worn dial | 128 | hand-cut rim (+-0.3 px), low-frequency mottling (alpha 228..248), 15 hairline scratches (alpha -36..-62), 26 specks, 3 rim bites; disc radius 0.46875 of the side |
| 112 `wear` | dry stroke 256x32 | wear | 128 | 14 light scratches, one 36 degree arc scuff at 0.30, 70 dust specks, a soft glare wedge 292..346 degrees; drawn in chalk at alpha 0.30 |
| 115 `bezel` | thin track ring | bezel | 128 | 60 minute pips out to 0.47 of the side (every 5th long 0.065, short 0.035; 4 shortened, 2 missing), a triangle at 12 on the bezel (apex inward), 12 batons at 0.245..0.305 (one nicked), a triangle at 12 on the face |
| 123..125 | ring slices A | stroke 0.13 of the radius (was 0.23), overlap 0.6 degrees | 128 | |
| 126, 185, 190 | ring slices B | stroke 0.10 (was 0.12), overlap 0.9 degrees | 256 (kept; the spec said 224) | |
| 111 `stroke`, 113 `dab`, 116..118 | | unchanged | | 111 = row blocks, label bar, rules, strikes (thinner, 5 px, in place of 112) |
`kl_hud.py all <src> <out> --look deadmen [--watch 0|1]`, `kl_hud_tab.py build|verify ... [--watch 0|1]`; `--watch 0` bakes the look of the morning (old 112 / 114 / 115 and strokes). The hook's `[HUD] WatchStyle`
must be the same number (a mismatch = rings of the wrong width, no pips; it is not detected). Idempotent: a level baked either way can be baked again.

### 14.2 The round watch (centre (1212, 66) = [HUD] money right edge - 35, y = inset + 30; ~66..103 pictures)
Layers (call order never decreases in layer): case 114 (r 36.2, tint 07080A a 0.91; layer-4), face 114 (r 34, 14161A a 0.86; -3), wear 112 (chalk 0.30; -3), bezel 115 (pips out to r 33, chalk 0.70; -2),
time-left stroke (family A, centre line r 26 = inside the pips; grey 9A9A97; -1), hour hand, sword hand, optional seconds hand, hub (layer 0).
- hour hand = minutes left x 30 degrees (fractional: a 6 minute round starts at 6 o'clock, ends at 12); Mercedes: a shaft of dabs 3.0 wide at step 1.0, 19 long, 3.6 counter-tail, tapering to 0.8 over the last fifth,
  a ring at 62 % (chalk dab 7.0 + the dial's colour dab 3.7 over it); ~26 pictures.
- sword hand = seconds left in the minute x 6 degrees, whole seconds (ticks); 29 long, 5 tail, widest 3.4 at 55 %, 1.4 at the tip, step 1.2; ~29 pictures. Both hands run clockwise and meet at the triangle at 12 when time is up.
- stroke = from the sword tip clockwise to 12 (the time left): slices wholly inside + one dab run, round caps at both ends.
- last minute (60 s or less): stroke and sword hand turn red E8303F; the stock red digits show (they are blanked above 60 s as before; WatchLast=1 blanks them always). They were not placed under the new dial: they will overlap it (an offset is owed if W1 shows it).
- `WatchSeconds=1`: a thin coral seconds hand at 6 degrees a second, 30.4 long (+~34 pictures).
Round clock source unchanged ([rules+0x4c]); the length is only used as a sanity guard now (no dial before the round has a clock).

### 14.3 The escape dial (centre = the watch's x - 62 = (1150, 66), 50 px across; ~31..48 pictures)
The watch's base at scale 22.5 / 33 (case, face, wear, pips at 0.5 alpha), an orange stroke = the wait that is left (empties from the top as before), the car / helicopter icon 26 px in the middle, no hands.

### 14.4 The weapon circle (centre (1199, 598) = WeaponX default 1199 under Draft, KLWD_S 0.76 -> disc 107, ring r 47.1; ~13..64 pictures)
Case + face + wear as the watch; a DIM FULL RING of family B slices (2B2C2E) under the magazine stroke (family B, chalk, coral at a quarter of the magazine or less (size over 3) or when the game says the gun is low); the count big
in the upper left (coral on the same rule); the active gun's picture upper right; a 1 px hairline across the middle (picture 181: 111 breaks up at 1 px); the other gun's count and picture below, dim. No pips, no needle.

### 14.5 The label bar (right edge = circle centre + 48 = 1247, y 654..675; 1 picture + 3 texts)
Black bar (slot 111 painted, 070707 at 0.90; `LabelBar=2` = plain 181, `0` = none), then 'NAME / reserve': the name chalk E9E6DF, the slash coral, the reserve C9C5BD (coral when low). Three text objects (right-aligned, capitals centred on
the bar's middle, no shadow): KLU_NWEAP is 5 now. No text metrics in the hook: the bar's left edge and the slash use an ESTIMATE of 11.6 px a letter, 0.93 of that a digit ([HUD] LabelCharW; the preview measures the baked label
font at 11.9 a capital and 10.7 a digit: the estimate is within 3 px of the real text for four names). `LabelSlash=0` draws no slash. A gun without a count shows the name alone.

### 14.6 Keys (all `[HUD]`, read at start-up)
`WatchStyle=1` (0 = the look of the morning for the watch, escape dial, weapon circle, label and the ring strokes), `WatchSeconds=0`, `WatchWear=1`, `WatchLast=0`, `LabelBar=1`, `LabelSlash=1`, `LabelCharW=11.6` (10.5 under WatchStyle=0).
Slot 112 users (strike-through, rules, the scoreboard's lines) draw 111 under WatchStyle=1 (`KLU_DRY()`); the loot ring's and the scoreboard continue ring's track is a dim full ring of family A (115 is the bezel).
KLU_NPIC 288 -> 300.

### 14.7 Pictures a frame (the model's count; the old look in brackets)
Typical: watch 84 (50 + hands), escape 46 (28), weapon 39 + bar (45) = about 170 against 123. WORST each, at the same time (never really): watch 103, escape 48, weapon 64 = 215 against about 123, so with the crew list,
money box, pop-ups and loot ring about 280 of the queue's 300 (the draw list was tested to ~320). The spec's '+5' counted typical frames; the queue drops silently over 300. WatchSeconds=1: watch up to 137.
A cheaper cut if W1 shows dropped pictures: WatchWear=0 (-3 pictures), a larger dab step on the weapon stroke (KLU_DAB_MAXSTEP), or no pips on the escape dial.

### 14.8 Guesses / open risks
- Hands are runs of dabs: soft edges at 1x (1.3..3.7 px), the hub's dial-coloured dab and the Mercedes ring's hole rely on CALL ORDER inside one layer (the model draws in call order).
- The preview samples bilinear without mips; if the game minifies differently the 128 px bezel (70 px drawn) may alias (the pips are 2..3.6 texels wide).
- The face / case alphas (0.86 / 0.91), the dim ring colour, the wear alpha are my choices from the previews.
- The gun and car pictures in the preview are stand-ins; the stock icons may not suit the dark disc.
- Stroke widths 0.13 / 0.10 come from the spec (measured from a JPEG by track C).
- Last-minute digits (above). A level and a hook with different WatchStyle (above).

### 14.9 Live check W1 (owner away; hook `<work>\build\klhook\hud_v29_test`, level `<work>\build\hud_x10\DM03` swapped into the bank's slot for the run)
`[HUD] Enable=1 Draft=1 Log=2` (WatchStyle default 1), pictures every 2 s through the whole heist on the bank: look at (1) the watch: pips, the stroke from the sword tip to the 12 triangle, both hands move (the sword in whole seconds),
the hub / hole drawn OVER the hand, red in the last minute (play on or set the round short); (2) the escape dial aboard; (3) the weapon circle: dim ring, the stroke empties from the top, coral at a quarter, count, hairline,
second gun; (4) the black bar under it: 'NAME / reserve' fits the bar (compare the left edge with the text; adjust LabelCharW); (5) the loot ring (dim full ring, no pips) and the scoreboard's continue ring; (6) strike-through of a dead heister
(111) and the crew rules; (7) the log for dropped pictures ('hud: ... pictures' counts; none over 300). Then the same with `WatchSeconds=1` and with `WatchStyle=0` on a `--watch 0` level.
Level: kl_hud.py all hud_tab/DM03 -> hud_x10/DM03 --look deadmen (check PASS), preview hud_x10/preview.png, dials hud_x10/dials*.png (python tools/kl_hud.py preview-dials <level> <out dir>).

### 14.10 Review round (2026-10-12; re/hud_watch_review.md) - hooks hud_v30_test 925a750f / hud_v30_ship c4747b19 (built from HEAD klhook + the working klhud*.c)
- MUST 1 done: both hands run CLOCKWISE. hour = 360 - minutes_left * 30, sword = (60 - seconds_left_in_minute) * 6 (whole seconds), the seconds hand (WatchSeconds, off) too.
  Stroke = hour tip -> 12 (minutes left, drains over the round) while more than 60 s remain; sword tip -> 12 (seconds left, 360 -> 0) in the last minute. At 1:00 the stroke
  goes from 30 to 360 degrees ON PURPOSE (red last minute begins): the review's "no jump at 1:00" cannot hold with two different quantities - GUESS the owner accepts it; the
  alternative is the hour stroke all round (30 -> 0, tiny in the last minute). Model: kl_hud_watch.watch_angles / stroke_start / draw_watch, same numbers.
- MUST 2 done: [HUD] WatchStyle defaults to 0. Set WatchStyle=1 in the ini ONLY together with maps baked by kl_hud.py --watch 1 (hud_x10 / kl_hud_tab build). The hook cannot tell the textures apart (a marker file is not done).
- SHOULD 3 done: WatchLast defaults to 1 (stock red digits blanked in the last minute). SHOULD 4 done: the first dropped picture logs 'hud: the picture queue is full (300)' once; keep WatchSeconds=0.
- SHOULD 5 done (guess): the weapon gun picture sits 3 px further left in the watch look (DX 25 instead of 28); check with the real icons. A thinner weapon stroke (0.08) NOT done: it is baked into the ring slices (rebake of every map). 
- SHOULD 6 done: the label bar's left edge gets 4 px more. LabelBar=2 stays the clean option. SHOULD 7 not touched (guesses: alphas, icon corners).
- The baked textures did not change, so hud_x10/DM03 needs no rebake (kl_hud preview-dials / preview-hud re-run: hud_x10/dials*.png, preview.png; 5:30, 2:10, 0:40 read right).
- Live check W1 addition: rounds at 5:30 / 2:10 / 1:00 / 0:40 / 0:05 (stroke = time left, hands clockwise, red last minute, no stock digits); one start with an OLD-baked map under WatchStyle=1 only to see it, never for play.

### 14.11 Cloud session additions (2026-10-12 evening; off-game tests under MinGW + Wine, re/hud_cloud_review.md 6-7; NOT BUILT WITH MSVC, NOT RUN IN THE GAME)
- `klu_choose_look` (klhud.c, called first in `klu_make_all`): the level's bake decides the look when slot 112 tells (128 x 128 = watch, 256 x 32 = old);
  `[HUD] WatchStyle` (now kept as `klu.wini`) decides only when it cannot. Log `hud: watch: ...`. Test: `klwatch_test look` 9/9.
- The escape dial's icon is tinted KLW_C_CHALK (the model's), `[HUD] Layer` minimum 4, the tag drawer gets only objects that pass a vtable read.
- `klwatch_test.c` + `tools/kl_hud_watch_check.py compare|render`: the hook's queued pictures equal the model's (24/24), rendered with the baked textures.
- Live check W1 addition: one start with an OLD-baked map under WatchStyle=1 must log the 'baked with the OLD look' line and draw the old dials.
