# The escape-vehicle panel in the new look (track ESCAPE, 2026-10-11 night) - NOT RUN IN THE GAME

`klhook/klhud_escape.c` (new, untracked, NOT wired in the repo; wiring in section 6). `[HUD] Escape=1` (default = `Draft`), needs
`[HUD] Enable=1`, draws only while klhud.c draws. Owner: 'you can keep it via the restyle' (prompts in the new lettering, the plate
replaced by a painted bar). Words: READ = kl2.exe build 0490, static (capstone); GUESS = neither read nor seen.
Compile check: TEST `<work>\build\klhook\hud_esc_test` (sha1 673a90c0), SHIP `hud_esc_ship`, built from `git archive HEAD klhook` +
the working tree's klhud*.c + the wiring below, in G:\kl_scratch\hud_esc; no warnings. Scratch readers: scratchpad `esc\d.py`, `a.py`.

## 1. The element (all READ)
ZFAEscapeDisplay `[osd+0x111c]`, vtable 0xbbe9d0 (11 slots, then the next table's locator), 0x16c bytes. Slot 2 Render 0x5d7e00 (ret 8),
4 Init 0x773d50, 5 Tick 0x793ae0, 6 Update 0x548190.

| field | meaning |
|---|---|
| +0x08 / +0x0c | the OSD / the screen transform (T+0x14 = A, px -> camera units) |
| +0x14 +0x18 +0x1c | the anchor. Update: x = 1280 - 1280 x [0xceeebc] - 765 = **451**; y = 720 - 720 x inset + [0x154dcbc] (about 664 from the picture) |
| +0x24 / +0x28 | enabled / 'shown' (Init: +0x28 = 0; who sets it was not followed) |
| +0x29 / +0x2a | Share / Hold prompt usable (Tick: player vtable +0x258 / +0x264) |
| +0x2c | **the plate**: an object made from the level's `BackgroundFrame` object (class tag 'ZCOB'), style 0x14, layer 0xa |
| +0x3c / +0x4c | Share line / Hold line texts (style 0x21, layer 0xf, colour [0xbbe494] = cccccc) |
| +0x50 / +0x54 | time text (style 1, font = Init's, layer 0xf) / its shadow (colour 80000000, layer 0xe) |
| +0x58 | -> the OSD's picture-table row of the icon: osd+0x7f8 = row 170 car, +0x804 = row 171 chopper (rows are 12 bytes from osd+0) |
| +0x5c | icon colour, set by Tick from the player's state (vt +0x12c, table 0x793d94): 0,7,8 white; 1,2 green 22ff22; 3,4 yellow aaaa55; 5,6 red cc0000 |
| +0x60 / +0x94 | the icon's DrawChunk record (colour at +0x90) / its shadow's (colour at +0xc4 = 80000000) |
| +0xd4 / +0xe0 | the bar's record / its quad: 0x5ff260(+0xe0, 0, w) stores w x T+0x14 at +0x44 (w = min(ratio x 80, 80), 80 = [0xcef1f4]) |
| +0x144..+0x150 | the bar's four corner colours, copied from +0x154 in every Render; Tick: white [0xbbe490] while hp/maxhp > 0, else cc0000 |
| +0x30 / +0x40 | the Share line's place (x + 75, y - 32) / the Hold line's (x + 75, y + [0x154dcc0]); Update writes both every frame |

What the bar means: **the escape vehicle's health** (Tick walks the player's vehicle list: ratio = [obj+0x864] / [obj+0x868]); the
time is the hold time from the rules (vt +0x130) formatted `%02d:%02d` (0x7818c0). The prompts come from THIS element (.LOC section
'AllLevels/Interface/Online/Exit': FA_ShareWithDriverExit / FA_ShareWithPilotExit / FA_HoldEscapeVehicle, formatted with the key
letters by 0x7bb920; the key letter's red is in the string's own markup).

## 2. What Render draws, in order (READ)
Gates: +0x24 and +0x28 set; a local player (0x7bb2a0([0x168e9e4])); its vt+0x1c8 has bit 0x20 and not bit 4. Then: the plate
(SetAlpha 0xff, SetSize 130 x 45, Draw at (x + 215, y - 105)); the time text (x + 190, y - 85), style 1 = left, its shadow +2/+2; the
icon DrawChunk at (x + 170, y - 83) layer 0xf with colour +0x5c, and its shadow +1/+1 layer 0xe (picture 170 for session vt+0x17c == 3,
else 171); unless [0x168e59c] == 2 the Share line, then the Hold line (alpha ff / 3f by +0x29 / +0x2a); last the bar, picture 182
(osd+0x888), layer 0xb. Seen in T2_DM03_type_172s.png (aboard, vehicle state 5/6 = red icon).

## 3. How the part restyles it (all data writes, all put back)
1. Private vtable copy of the element (12 dwords from vt-4; slot 2 -> klesc_render -> stock 0x5d7e00), as klhud_popup.c.
2. **The plate is dropped by its own Draw.** The plate object's vtable pointer (one heap dword) points at a private copy (256 dwords)
   whose slot 0x1e8 (Draw, four stack arguments) is `klesc_plate_draw`. While `klesc_in_call` it draws OUR pictures and returns;
   otherwise it calls the original. The slot runs only when every gate of Render passed, so ours shows exactly when the stock panel
   would, and in the plate's place of the draw order (layers 0xb..0xd, under the texts 0xe / 0xf). The plate's class is not known
   statically (Init makes it with the same tag as the texts, yet Render calls slot 0x23c on it with TWO arguments); only 'the slot is
   code' is required, else the part stays off and logs why. The plate's vtable pointer is put back when we do not draw.
3. Icon / icon shadow / bar: their colour dwords (+0x5c, +0xc4, +0x154) go to alpha 0 for the one call (compare-and-swap back).
   GUESS: alpha 0 draws nothing (alpha is seen to count: the traitor box's 0xe6 fill, the faded dollar sign).
4. Texts through their own routines (colour 0x20c, font 0x23c, style 0x220, alpha 0x218): the time in INK on the chalk bar in the
   NAMES font, style 0x14 (centred at x: the time's centre is x + 190 = 641, the screen's middle), its shadow alpha 0; the prompts in
   chalk, names font, style 0x14, their x written to the time's centre for the call. All put back when we do not draw (statics
   klesc_tx, render thread, like klpu_dirty). `EscapeCentre=0` keeps the stock place and style.
5. Our pictures (klu_pic, the clock element's record): a chalk bar (111, else 181) = text width (the text object's half extent
   [[obj+4]+0x40] x 2, else 5 x 12) + 2 x 18, high cap + 14, its middle = the text's top + cap/2 (baked metric); the icon (the row's
   own picture 170 / 171, 30 px) to its left, tinted by the stock state class: green -> green, red -> coral, else ORANGE; a health
   bar 5 px under the chalk bar: dark track (181), orange fill (111) of width ratio (coral when the stock colour is red), frame 117.
Information kept: time, vehicle state (colour class), vehicle health, both prompts and their usable / dimmed state (alpha untouched).

## 4. Guesses (live check E1 decides)
- picture 170 is a white square with the car cut out (stock look: red rounded square): 30 px may be too big / small (`EscapeIcon`).
- the quad's +0x44 holds width x A: the first log line prints the fraction and the quad; the fill is clamped to 0..1.
- layers: bars 11, icon 13, texts 0xe / 0xf; a wrong order shows as ink letters hidden under the chalk bar.
- style 0x14 centres every text at the passed x (proven for the pop-ups only); alpha-0 pictures draw nothing.
- the anchor's y (+0x18) is read live.

## 5. Not touched
The knock-down prompt (osd+0x10fc), every other element, the clock's escape line (klhud's dial), every code byte.

## 6. Wiring (klhook.c; klhud.c is NOT changed)
```
old: #include "klhud_popup.c"                              /* AFTER klhud.c: pop-ups + loot ring ...
new: (same line)
     #include "klhud_escape.c"                             /* AFTER klhud_popup.c: the escape-vehicle panel restyled (off unless [HUD] Escape / Draft) */
old: klpu_tick(game_thread);   /* klhud_popup.c ...
new: klesc_tick(game_thread);                              /* klhud_escape.c: the escape panel (after klu_tick) */
     klpu_tick(game_thread);   /* klhud_popup.c ...
old: klpu_init();   /* klhud_popup.c: after klu_init ...
new: klesc_init();                                         /* klhud_escape.c: after klu_init */
     klpu_init();   /* klhud_popup.c: after klu_init ...
```
No reset call is needed: klesc_tick forgets the level when klhud's OSD goes; the render slot puts texts and plate vtable back.

## 7. Live check E1 (hook hud_esc_test, a level with the extras e.g. build/hud_x4/DM03, `[HUD] Enable=1 Draft=1 Log=2`)
A whole heist to the van, pictures every 2 s from the call to the boarding. Look for the log lines 'hud: escape: ... now draws through
the private vtable (Draw = 005a6d40 ...)' and the geometry line (fraction, quad); no dark plate; chalk bar with ink time; orange icon
(green while the vehicle arrives, coral when it leaves); framed health bar; prompts centred in chalk with the key letter red; no fault.
Fall-backs by ini: `Escape=0`; `EscapeCentre=0`; `EscapePrompts=0`.
