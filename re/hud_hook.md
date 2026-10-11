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
