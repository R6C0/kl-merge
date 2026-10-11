# The stock ammo panel (ZWeaponDisplay) read whole, and the weapon dial - track W, 2026-10-11

Written offline while the owner played. Sources: `kl2.exe` build 0490 disassembled with capstone (`debug/kl.py`,
`tools/kl_exe.py`); scratch `<scratchpad>\W\` (`f.py` dumps a routine to `f_<addr>.txt`; every routine named here has one).
Words: **READ** = read in the code of kl2.exe; **file** = read in the exe's data; **ASSUMED / GUESS** = fits, the deciding
code or a run is missing. **Nothing here has run in the game.**

New files: `klhook/klhud_weapon.c` (the dial, `[HUD] Weapon=1`, default 0) and this note. klhud.c is NOT changed: section 5
is the wiring for the lead. Compiles SHIP + TEST with the wiring applied in a scratch worktree (section 6).

## 0. For the lead, in ten lines

1. **Rounds in the magazine** = `[weapon+0xdc] ^ 0xbeebbeeb`, **reserve** = `[weapon+0xe0] ^ 0xbeebbeeb` (both counters of a
   gun object are stored xor'ed; READ 0x511f50, 0x8b8173). The gun object = the inventory's entry of the item id
   (`[player+0xcec]`, 16-byte entries). The panel itself shows ONE number a gun: rounds + reserve.
2. **Magazine size** is three virtual calls deep (0x6c93d0). The dial does not need it: the element writes
   `rounds / size x 179` into a bar record every tick (`elem+0x1134 +0x44` against `elem+0x10b4 +0x44`), for every gun.
3. **The panel has no gun name, no separate reserve number, no grenade count** (Render read whole, section 3). The dial's
   name is our own table by picture index.
4. **Weapon pictures are NOT the kind klhud.c draws.** The OSD makes pictures 58 .. 106 as chunk type 6 (0x74-byte
   record), klu_pic only knows type 5 (40 bytes). The new file brings its own draw for them (`klwd_pic6`).
5. **Two of klhud.c's GUESSES are now READ**: a picture's width / height = pixels x `T[+0xc]` / `T[+0x10]` (0x5ec615 ..
   0x5ec653, 0x5ec9df .. 0x5eca0c), and a type-6 picture's place is its MIDDLE (corners +-0.5, 0x7c6bf0). Both agree with
   run P1 (c9d654d).
6. **ZCHAROBJ vtable +0x21c is the text's SIZE, not an offset** (ASSUMED from two READ uses, section 4): the stock panel
   draws its second gun's count at 0.8. So type sizes ARE reachable - re/hud_hook.md 3 says they are not.
7. **The stock panel is taken off by a private vtable, not by the hide byte** - a deviation from the task, on purpose:
   two stock hide groups write `elem+0x25` (section 4.3). Say so if the byte is wanted after all.
8. The whole thing needs the level's extra pictures 113 / 114 and falls back to the stock panel otherwise.

## 1. The data path: ZWeaponDisplay's Tick (slot 5 = 0x5b1e00) - READ

`0x5b1e00`: `for i in 0, 1: 0x88bac0(elem, i)`; then `0x43cb30(elem)` (the pick-up arrow) and `0x6c1780(elem)` (a
four-slot inventory strip, only when `[0x1548c18] != 0`; not seen set by anything read here).

```
0x88bac0(elem, i):                                   player = [elem+0x10]
  hand = [player+0x920]        item id of the gun IN THE HAND, 0 = hands empty (writers 0x649278, 0x70d76e: 0x47ded0's result)
  sel  = [player+0x924]        item id SELECTED (kept while holstered)
  if !sel: sel = 0x748430(player)                    the item of the object REF [player+0xbb8] when it is a weapon
  if !sel: sel = 0x49b2f0(inv, 0, 4)                 the first weapon of the inventory;  inv = [player+0xcec]
  i == 0: item = sel;  alpha[0] = talpha[0] = hand ? 0xff : 0x40;  colour[0] = white;  [elem+0x1228] = [elem+0x122b] = 0
  i == 1: item = 0x49b2f0(inv, sel, 4)               the OTHER weapon;  alpha[1] = talpha[1] = 0x40;  colour[1] = [0xbbe4d8]
  weapon = 0x417bc0(inv, item)                       -> 0x5aa000(inv+4, item): entry {item, ?, object, info}, object at +8
  if !weapon: pic[i] = [0x154db68 + 4*item]; alpha[i] = talpha[i] = 0; return
  rounds  = weapon->vt[+0x2fc]()                     0x511f50: [weapon+0xdc] ^ 0xbeebbeeb
  reserve = 0x8b80e0(weapon, 1)                      [weapon+0xe0] ^ 0xbeebbeeb; 999 - rounds when the gun has endless ammo
                                                     (template byte +0x138 = vt+0x2d8, or option byte [[0xdd2640]+0xac]+0xb4,
                                                     and [0x15351e0] == 0); 999 when REF [weapon+0x5c] is a certain class
  if template->vt[+0x2d8](): reserve = rounds        (the endless gun when [0x15351e0] != 0: the number shown is 2 x rounds)
  size    = weapon->vt[+0x304]()                     0x6c93d0: -1 when [weapon+0x54] == 0; else template->vt[+0x2d0]()
                                                     (0x5be320) when not 0; else the ammo object REF [weapon+0xd4] ->vt[+0x29c]()
  low     = 0x77b790(weapon)                         rounds + reserve < size  (items 0x28 .. 0x30: < 15; item 0x31: < 4)
  lowclip = 0x54ee60(weapon)                         size > 3 and rounds / size < 0.33
  colours: white [0xbbe490] / cccccc [0xbbe494]; when low: red cc0000 [0xbbe4d0] (gun 0 in hand) or 880000 [0xbbe4d4]
  shown   = rounds + reserve       (-1 when [session+0x60] == 0xb and [player+0xd50] and 0x8f7b40(items, weapon))
  0x4596a0(elem, i, shown, colourA, colourB)         the count texts (below);  caches: [elem+0x150c+4i] = shown, [elem+0x1514+4i]
  pic[i] = [0x154db68 + 4*item];  colour[i] = picture colour
  i == 0: 0x5c5670(elem, (float)rounds, (float)size, lowclip, hand == 0);  if item: [elem+0x122b] = [elem+0x1228] = 1
```

`0x4596a0` (count text of slot i): `sprintf("%i", shown)`; a second string of `3 - digits` zeros (the dim leading
zeros, only when talpha[i] != 0); `[elem+0x2fc+4i]` = 48 x scale - 16 x scale a pad zero (scale 1.0, slot 1: 0.8 =
`[0xbbe8b8]`); SetColour + SetText on `[elem+0xb8+4i]` (number), `[+0xc0+4i]` (its shadow), `[+0xc8+4i]` (zeros),
`[+0xd0+4i]` (their shadow).

`0x5c5670` (the magazine, slot 0 only): `[elem+0x1229] = rounds != 0`, `[elem+0x122a] = size != 0`; bar colours
`+0x122c / +0x1230 / +0x1234`; three bar records by `0x6bc990(elem, record, x0, x1)` (a quad from x0 to x1, 6 high,
times `T[+0x14]` / `T[+0x18]`): `+0x1134` from 0 to `min(179, rounds / size x 179)`, `+0x10b4` and `+0x11b4` from 0 to
179. Then by size: under 1 -> tick count `[elem+0x304] = 0`; over 30 (`[0xb45350]`) -> count 2: record 0 the filled part,
record 1 the rest at alpha 0x27; else count = size, record k a quad `(179 - 2 (size - 1)) / size` wide (0x63f2f0), its four
colours at `+0x374 + 0x74 k`: white (red when lowclip), alpha 0xff in hand / 0x40 not, 0x27 for an empty round.

## 2. Fields (READ unless marked) - what the dial reads is marked *

| where | what |
|---|---|
| elem+0x08 * | -> the OSD's picture table (`osd+0x3ec`), 12 bytes a picture: sprite handle, width, height |
| elem+0x0c * | -> the screen transform T (`osd+0x1130`) |
| elem+0x10 * | the player object |
| elem+0x14, +0x18 | the panel's origin (x, y): `1280 - 1280 inset - 103`, `720 - 720 inset - 48.8` = (1113, 635.2) at 0.05 |
| elem+0x24 / +0x25 * | enabled / hidden (never written by the dial) |
| elem+0x28 + 12 i | picture middle of gun i: (x + 38, y - 28), (x + 22.8, y + 28) |
| elem+0x40 + 12 i | count place of gun i: (x - 38, y - 28), (x - 38, y + 28) |
| elem+0x58, +0x5c | the ticks' origin (x - 90, y - 4); +0x7c, +0x80 the plate (x, y - 6); +0x64 / +0x70 the arrow |
| elem+0xb8 .. +0xd4 | eight ZCHAROBJ: number, number shadow, zeros, zeros shadow, two slots each; style 0x42, the HEADLINE font (Init arg = `osd+0xd50`), layer 0xb / 0xa |
| elem+0xd8 + 0x84 i * | desc of gun i's picture `{1, 0, -> elem+0xe4 + 0x84 i}`, the 0x74-byte record right behind it |
| elem+0x2e8 + 4 i * | HUD picture index of gun i (0 = none) |
| elem+0x2f0 + 4 i * | picture colour (RGB); red = low on ammo |
| elem+0x2f8 + i * / +0x2fa + i * | picture alpha / count alpha (0xff, 0x40; 0 = no gun object) |
| elem+0x304 * | tick desc: count (= magazine size 1 .. 30, 2 = bar, 0 = none); +0x30c -> records at +0x310, 0x74 bytes each, 30 of them |
| elem+0x10b4 / +0x1134 * / +0x11b4 | bar records (full / filled / full); right edge at record+0x44. Not referenced by the Render |
| elem+0x1228 * | 1 = gun 0 has an object (ticks drawn); +0x1229 rounds != 0; +0x122a size != 0; +0x122b plate drawn |
| elem+0x1238 | plate desc (type 5 record at +0x1244); +0x126c the arrow's; +0x12d4 arrow state |
| elem+0x150c + 4 i * | the number shown for gun i (rounds + reserve; -1 none); +0x1514 + 4 i its last colour |
| player+0x920 * / +0x924 * | item id in the hand / selected |
| player+0xa54 bit 1 * | the Render skips gun 1 |
| player+0xcec * | inventory: byte +4 (0 = array indexed by item id), +8 array of 16-byte entries, +0xc count |
| weapon+0xc4 | template (vt+0x2ec = 0x6ed320 returns it; int3 when a template flag is missing) |
| weapon+0xdc * / +0xe0 * | rounds in the magazine / reserve, each `^ 0xbeebbeeb` |
| `[0x154db68 + 4 item]` * | item id -> HUD picture index, 64 dwords, filled by the element's constructor (0x84f52e) |
| `[gamedata+0x15b0]` | the item manager: 64 entries {template, item id, ..}; 0x47ded0(mgr, object) = item id of an object |

## 3. ZWeaponDisplay::Render (slot 2 = 0x5ec380, `ret 8`) - READ whole

```
Render(ctx, cam):
  if !byte [elem+0x24]: return
  xform = 0x7f07a0()                                             {0,0,1, 0,1,0, 1,0,0}
  for i in 0, 1:
    if player->vt[+0x388]() == 0x21 and [player->vt[+0x38c]() + 0xd4] == 3:      (one action state: no guns at all)
        [elem+0x1228] = 0; [elem+0x12d4] = 0; continue
    if byte [player+0xa54] & 2 and i == 1: continue
    pos = (elem+0x40+12i, +0x44+12i, +0x48+12i)
    number[i]->SetAlpha(talpha[i])                 vt+0x218;   number[i]->Draw(ctx, cam, &xform, &pos)      vt+0x1e8
    pos.x -= [elem+0x2fc+4i]
    zeros[i]->SetAlpha(min(talpha[i], 0x40));      zeros[i]->Draw(.. &pos)
    pos = (elem+0x40.. ) + (2, 2)                  [0xbbe4ec], [0xbbe4f0]
    numberShadow[i]->SetAlpha(min(talpha[i], 0x80));  Draw;   pos.x -= pad;   zerosShadow[i]->SetAlpha(min(.., 0x40, 0x80)); Draw
    p  = (elem+0x28+12i) x T[+0x14], (elem+0x2c+12i) x T[+0x18], 0 ; 0x42a4d0(&p)          the picture's place
    record(i).width  = table[pic[i]].width  x [0xcee050] x T[+0xc]         elem+0x140 + 0x84 i   (0x5ec615)
    record(i).height = table[pic[i]].height x [0xcee050] x T[+0x10]        elem+0x144 + 0x84 i   (0x5ec643)
    i == 1: both x 0.8  ([0xb70260]; elem+0x1c4 / +0x1c8)
    record(i).colour[0..3] = colour[i] & 0xffffff | alpha[i] << 24         elem+0x148 .. +0x154 + 0x84 i
    (a second desc at elem+0x1e0 + 0x84 i gets the same size and black: a shadow that this routine never draws)
    if pic[i] != 0:
        ctx->DrawChunk(table[pic[i]].handle, &desc(i) = elem+0xd8 + 0x84 i, &xform, &p, layer 0xb, 1, 0)      0x5ec7de
  if byte [elem+0x1228]:                                                   THE MAGAZINE TICKS
    p = (elem+0x58) x T[+0x14], (elem+0x5c) x T[+0x18]
    if [elem+0x1229]: the bar colours +0x122c / +0x1230 / +0x1234 copied into the three bar records (which nothing draws)
    if [elem+0x1229] or [elem+0x122a]:
        ctx->DrawChunk(table[109].handle (UI_KL2_AmmoCount), &desc = elem+0x304, &xform, &p, layer 0xc, 1, 0)   0x5ec900
        = ONE call, `count` quads: a round a quad, or the bar and its rest
  if byte [elem+0x12d4]:                                                   the pick-up arrow, picture 110
    at (elem+0x64 / +0x68) or (elem+0x70 / +0x74) by talpha[0], y + 24 x the state; size from table[110]; desc elem+0x126c, layer 0xb
  if byte [elem+0x122b]:                                                   THE PLATE
    picture 107 (Weapon_BG), or 108 when [session+0x60] == 0xb; at (elem+0x7c, +0x80); size from the table;
    desc elem+0x1238, layer 9                                              0x5ecb3b
  if [0x1548c18]: four more pictures, descs elem+0x12d8 + 0x84 k, indices elem+0x14e8 + 4 k, layer 0xc
```

Nothing else is drawn: **no name, no reserve as its own number, no grenades.** The number is always rounds + reserve.

## 4. What else the reading settles

### 4.1 Picture chunk types - READ 0x5e3810, file 0xcee058 .. 0xceeea4

The OSD's picture loader looks each picture index up in a table of 183 rows `{index, name, flags, 1, type}` and creates
the sprite with that type (`renderer->vt[+0x104](texture id, flags | 0x10, type, 1)`); an index without a row gets flags 0,
**type 5**. DrawChunk's record size follows the chunk's type (0x842ee4: 5 = 40 bytes, 6 and 8 = 0x74).

- type 6 (89 rows): 2 .. 34 mostly, 47, 53, 54, **58 .. 106 (every weapon picture, AmmoPickup, AmmoNoPickup)**, 109 (the
  tick), 110, 182, 183, 186, 187, 189, 192, 193. Type 8: 188, 191.
- type 5: the rest, among them 107 / 108 (plate), 161 .. 172, 170 / 171, 178, 181 - and **111 .. 118 have no row**, so
  the extras of `kl_hud.py --look deadmen` are type 5, as klhud.c takes them.
- 182 (the second UI_White) is type 6: klhud.c's 'try 182' for a plain white would not be drawn by klu_pic.
- Not explained: 110 (Arrow) has type 6 in the table while the element gives it 40-byte records (Init 0x83318e uses
  0x775a10). The run-time test of `[chunk+0xc]` (klu_pic_prep, klwd_handle) is what counts.

Type-6 record, 0x74 bytes (READ Init 0x832ee4 .., 0x4bde70, 0x7c6bf0): `+0` vec3 offset (0); `+0xc` 0; `+0x10 .. +0x1c`
four 1.0; `+0x20 .. +0x28` 0; `+0x2c` four corners, vec3 each: (-0.5, -0.5) (0.5, -0.5) (0.5, 0.5) (-0.5, 0.5) - a unit
quad CENTRED on the place (the bars overwrite them with explicit edges); `+0x5c` width, `+0x60` height; `+0x64 .. +0x70`
one ARGB a corner. A desc is `{count, 0, -> records}`: the tick desc draws up to 30 records in one call.

### 4.2 Text size and alpha

- vtable +0x218 = 0x639700 = SetAlpha(byte) (READ: the Render feeds it the alpha bytes).
- vtable +0x21c = 0x45d6e0 `(&{a, b}, 0)`: stores `+0x1c / +0x20`, sets a dirty bit, re-lays out. re/hud.md 3.1 calls it
  an offset. READ: the panel's Update (0x78fb11 .. 0x78fbcb) passes (1, 1) for gun 0's four texts and (0.8, 0.8) for gun
  1's, and 0x4596a0 advances gun 1's pad zeros by 16 x 0.8. **ASSUMED from those two: it is the SIZE.** Check W3 shows it.
- The panel's texts use style 0x42 and the headline font `osd+0xd50`.

### 4.3 Why the dial does not write the hide byte

`elem+0x25` of the weapon element is written by BOTH stock hide groups: 0x75f780 (0x75f78a; six call sites; with the
clock and the player list) and 0x5e6060 (0x5e6097; seven call sites; with the crosshair, hit direction, human shield).
A hook that writes the same byte cannot tell afterwards what the game wants - klhud.c's review point M1, here with two
groups whose shows and hides can interleave. So `klhud_weapon.c` gives the element a private copy of its 11-slot vtable
(as klhud.c gives the clock) with slot 2 = `klwd_render_elem`: while the dial stands it does not call 0x5ec380 and
draws the two gun pictures; else it calls 0x5ec380. The game's own tests (`+0x24`, `+0x25`, 'HUD off', 0x8bf300) stay in
front of the slot, so the dial's pictures vanish in the very frame the game hides its panel, and the tick, reading the
bytes as the game left them, takes disc, ring and texts off within 100 ms. Nothing to restore.

## 5. The dial (`klhook/klhud_weapon.c`) and its WIRING

What it draws (all places relative to the middle `(cx, cy)` = `(1280 - 1280 inset - 70.5, 720 - 720 inset - 86)` =
(1145.5, 598) at the game's inset; re/hud_layout.md's 1177 is the draft's own margin. Every number is a `KLWD_` constant):

| part | how | source |
|---|---|---|
| disc 141 x 141, `9c080809` | klu_addpic(114) | - |
| ring: 32 dabs 12 x 16 on r 62; the part LEFT from the top clockwise, the gap last (the draft's `80 100`); one dab at least while a round is in | own loop over klu_addpic(113) - klu_ring runs the other way | `[elem+0x1134+0x44] / [elem+0x10b4+0x44]`; coral when the tick colour `elem+0x122c` is the red (magazine under a third) or the picture's colour is (all ammo under one magazine) |
| first gun: picture 64 x 64 at (+28, -26); count right-aligned at (-7, -32) | klwd_pic6 (type 6) in the weapon element's own render slot; a klhud text | `elem+0x2e8`; rounds `[weapon+0xdc] ^ key` (no object read: the panel's own number) |
| first gun not in the hand | picture and count `b9b5ad` | alpha byte 0x40 |
| divider 87 x 2 | klu_addpic(112, else 181) | only with a second gun |
| other gun: picture 36 x 36 at (+21, +24), count at (-5, +20), `6f6c66`, size 0.8 | klwd_pic6; a klhud text | `elem+0x2ec`, `elem+0x1510` (all its ammo; `WeaponOther=1`: its magazine) |
| label `NAME . reserve`, coral, CENTRED at (0, +78) | a klhud text, style 0x44 | name: own table by picture index; reserve = the panel's number `elem+0x150c` - the rounds (what the GAME counts); no number when that total is 999 or more (endless) |
| pick-up arrow, picture 110, the element's own colour, left of the disc at (-86, -26) or (-86, +24) | klu_addpic when its chunk is type 5, klwd_pic6 when type 6 | `elem+0x12d4` (-1 / 1), size `table[110]`, colour `elem+0x129c` |
| the close-combat hold (action 0x21, state 3) | the disc alone: no gun, count, ring, label, arrow | `[[player+0x19c]+4]`: vtable, `+4`, `+0xd4` |

Not drawn, on purpose: the stock plate, the ticks, the dim leading zeros. Nothing at all (and no stock panel) for a player
with no gun and the plate flag `elem+0x122b` 0 - the stock panel is empty then too.
Fall-back to the untouched stock panel, with the reason logged once (`hud: weapon: no dial ...`): no picture 113 / 114;
the element is not a ZWeaponDisplay or slot 2 is not 0x5ec380; a read fails; gun 0's picture has no type-6 chunk or the
element's record of it is not the centred unit quad; the player's vtable +0x388 / +0x38c are not 0x76ea90 / 0x7d7fb0; a
draw context that is not a ZDrawBufferSimple (that frame goes to the stock Render); klhud.c itself not drawing.

Keys (`[HUD]`, with `Enable=1`): `Weapon=0`, `WeaponX=-1 WeaponY=-1` (the middle), `WeaponSmall=0.8`, `WeaponOther=0`.

### WIRING - klhud.c only (klhook.c: nothing; the build scripts: nothing). Three more text objects (+ three shadows).

`<work>\build\hud_W\wire.py <copy of klhud.c>` applies exactly this to klhud.c at c9d654d; `klhud_wiring.diff` beside it
is the result. NOTE: the sibling tracks (`klhud_popup.c`, `klhud_values.c`) will also want text indices - chain the
defines, `KLU_NTEXT` last.

1. After `#define KLU_NGRID ...`, replacing the `KLU_NTEXT` line:
   ```c
   #define KLU_T_WEAP      (KLU_T_GRID + KLU_NGRID)      /* klhud_weapon.c: the first gun's count, the other gun's, the label */
   #define KLU_NWEAP       3
   #define KLU_NTEXT       (KLU_T_WEAP + KLU_NWEAP)
   ```
2. In `static struct { ... } klu;`: `int weapon;`
3. In `klu_layout`, after `klu_r.t[KLU_T_MVALUE(0)].big = klu.totalfont;`:
   ```c
   klu_r.t[KLU_T_WEAP + 0].style = klu_r.t[KLU_T_WEAP + 1].style = KLU_STYLE_RIGHT; klu_r.t[KLU_T_WEAP + 2].style = KLU_STYLE_CENTRE;
   ```
4. In `klu_make_all`'s loop, replacing `if (i >= KLU_T_GRID && !klu.grid) continue;`:
   ```c
   if (i >= KLU_T_GRID && i < KLU_T_WEAP && !klu.grid) continue;
   if (i >= KLU_T_WEAP && !klu.weapon) continue;
   ```
5. Between `klu_dials` and `klu_row`: `#include "klhud_weapon.c"`
6. In `klu_compose`, after `klu_dials(&s);`: `klwd_compose();`
7. In `klu_stand_down`, after `InterlockedExchange(&klu_draw_on, 0);`: `klwd_show(0);`
8. In `klu_reset`, after `EnterCriticalSection(&klu_cs);` and before the memset: `klwd_reset();`
9. In `klu_tick`: `(klu.plates || klu.pictest || klu.dials || klu.weapon) && !klu_r.pic_done` ; and after
   `InterlockedExchange(&klu_draw_on, show);`: `klwd_show(show);`
10. In `klu_init`, with the other keys: `klu.weapon = klu_inii("Weapon", 0, 0, 1); klwd_init();`
11. The key list in klhud.c's header and `klhook/KLHook.ini`: the four keys above.

The prefix is `klwd_` / `KLWD_`: `klw_` is klcrew.c's.

## 6. Build

First round: `git worktree add G:/kl_scratch/Wdial HEAD` (c9d654d) + `klhud_weapon.c` (sha1 d14fa8c9) + the wiring:
`<work>\build\hud_W\ship\dinput8.dll` 2d2ad0b6, `...\test\dinput8.dll` 827777f7 - SUPERSEDED.

After the review round (section 9): a plain copy of HEAD's `klhook/` (`git archive HEAD klhook`; no worktree) +
`klhud_weapon.c` (sha1 a70942a5; a copy lies at `<work>\build\hud_W\klhud_weapon.c.a70942a5`) + `wire.py` (unchanged,
applies cleanly): `build.bat` -> `<work>\build\hud_W\ship2\dinput8.dll` **e760a3ad**, `build_auto.bat` ->
`<work>\build\hud_W\test2\dinput8.dll` **d0cff8d5**. No error, no warning at /W3; at /W4 no warning in
`klhud_weapon.c` (the first round's C4701 is gone). The scratch copy is removed. NOT installed, NOT run.

## 7. GUESSES and what is not done

In the order they could bite:
1. **The private vtable on the weapon element** and skipping its Render: the same step klhud.c takes on the clock (seen
   live), on another class; that the Render has no side effect the game needs (it writes only its own desc fields) is
   READ, not run.
2. **klwd_pic6**: a type-6 DrawChunk from the hook with a record on the stack - the code path is the stock one (0x842e3d
   copies at once), never issued by the hook. The weapon picture as a tinted silhouette at 64 / 36 px: the stock panel
   tints it (READ) at 128 px; how it reads small is unseen.
3. **The ring's source** (the two bar records) is written every tick but drawn by nothing: if a later reading finds
   them stale in some state, rounds / size must come from the tick records or from the size call. The Log=2 line shows
   `bar x of y` beside rounds and the tick count: for a 30-round magazine with 24 in it they must say 0.800.
4. Text size by vtable +0x21c (4.2); that a right-aligned text stays right-aligned at another size.
5. `inv` in 'indexed' mode: the entry at `array + 16 x item` is taken without a bound (the stock code has none either);
   every read is checked and the object is used only when its vtable's +0x2fc is 0x511f50.
6. The first gun's item when `[player+0x924]` is 0: found back from the picture index, only when one item has it.
7. Layer order: disc `Layer - 2`, ring / divider / gun pictures `Layer - 1`, texts `Layer`.
8. The names are OUR wording (letters, digits, '-'): whether the baked fonts have '-' and '.' at that size is unseen.

Not done: a gun whose look `kl_map_guns.py` baked over keeps its Dog Days name; localised names (the shop's names
are not read); grenades (not in the stock panel either); the draft's hand-cut ring stroke (dabs); the draft's thin grey
outline of the disc; `[elem+0x150c] == -1` (session mode 0xb: the game hides its number, the dial shows the rounds).

Added by the review round:
9. What action 0x21 / state 3 IS: READ = `ZFFActionCloseCombat` after 0x76eab0 took hold of a target; GUESS = the
   human-shield hold. Not the knock-down.
10. The arrow's place left of the disc is OURS; what the arrow means (-1 = the gun offered has gun 0's picture or
   neither's, 1 = gun 1's) is read from 0x43cb30's compares, any wording beyond that is a GUESS.
11. 'A type-6 picture's place is its middle' is INFERRED from the corner values (-0.5 .. 0.5, READ); what the renderer
   does with corners, width and height was not read. It says nothing about type 5 (klhud.c's `PicAnchor`): section 0.5's
   'both agree with run P1' holds for the SIZE only. W1's picture decides.
12. A gun under the game's 'endless + [0x15351e0] != 0' rule shows reserve = rounds (the game's own number is 2 x
   rounds): not told apart from a real coincidence.
13. The arrow as a type-6 picture is drawn with gun 0's record (the centred quad); the game itself feeds picture 110 a
   40-byte record. Which type its chunk has at run time is unseen (klhud.c's Log=2 'pictures: slot 110' line says).

## 8. Live checks (the lead, owner away; the bank archive with the extras `<work>\build\hud_x\DM03`; a TEST build of
HEAD + the wiring; pictures every 2 s from GO + 5 s)

Every run `[HUD] Enable=1 Log=2 Dials=1 Plates=1` plus the keys named. A crash with `klwd_`, 0x5ec380, 0x842d00 or
0x45d6e0 in the callers = stop.

- **W0** `Weapon=0`: no `hud: weapon:` line, the stock panel as ever (the three extra texts are not made: the
  `texts made` count is unchanged).
- **W1** `Weapon=1 Grid=2` (the sample values). LOG, in order: `hud: weapon: on ...`; `hud: weapon: element ... now
  renders through the private vtable`; `... the other gun's count set to size 0.80`; every second `hud: weapon: raw:
  ...` and `hud: weapon: render: N stock panel calls skipped, 0 passed ..., 2N gun pictures drawn`. No `no dial` line.
  READ THE 'render:' LINE FIRST: `N stock panel calls skipped, 0 passed, 2N gun pictures drawn, 0 lock busy`.
  PICTURE: bottom right a dark disc about 141 px (282 at 1440p) with its middle at (1145, 598) virtual; a chalk ring of
  dabs running from the top clockwise with the LAST fifth (the upper left) missing (0.8), as on the draft; `24` and the AK silhouette above a thin line, a small grey `9` and a
  pistol below; under it, centred, coral `AK-47 . 183`; NO stock panel (no plate, no ticks, no `207`).
  Read off: is the gun picture centred where the constants say (then type 6 = middle holds), does `9` look smaller
  than `24` (text size), do the dabs sit on the disc's rim.
- **W2** `Weapon=1 Grid=0`, a round in which shots are fired and a gun is reloaded and switched (the rig has no fire
  command wired that this track knows of: the owner's own round with the log on does it). THE RAW LINE PROVES THE
  READS: for gun 0 `rounds R reserve S` and `shown number N` must satisfy **N = R + S** in every line; `picture` must
  be 58 .. 104 with a fitting name; after each shot R falls by one and `bar a of b -> f` gives f = R / size (size =
  `ticks` when 3 .. 30); after a reload R is the size and S fell by what went in; `hand item` = `selected item` while
  the gun is out. LEGAL besides N = R + S: N = 999 or N = 999 + R (a gun with endless ammo: the label then has no
  number) and N = 2 R (the endless gun under `[0x15351e0]`). Anything else = the object read is wrong: stop, send the
  line. Note for each gun whether `bar a of b` x size = R.
  PICTURE: the ring's END (upper left first) goes as he fires, the last dab stays until the magazine is empty;
  switching guns swaps the two rows.
- **W2b** the same; empty a magazine below a third with reserve left. Control with `Weapon=0`: the stock ticks go red
  while the number stays white. With `Weapon=1`: the raw line's `tick colour` becomes `..cc0000` and the ring and the big
  count turn coral while the gun picture stays chalk; when all ammo is under one magazine the picture goes coral too.
- **W3** the same, standing in a game cut (the vehicle's arrival camera, the round end): the dial must go with the
  game's panel - no disc left alone on the cut. LOG at the cut: `hud: weapon: no dial, the stock panel is left to the
  game: the game does not show its ammo panel now`, then `the dial stands again` (both at Log=2 only).
  ALSO the close-combat hold (grab an enemy as a human shield), and the knock-down for comparison: the raw line must
  say `close-combat hold 1` while he holds him and the picture an EMPTY disc (stock, `Weapon=0`: an empty plate); `0`
  again when he lets go, and `0` all through a knock-down. If the line never says 1 in the hold, the state is another
  one: send the lines with the `action` pointer.
- **W4** `Weapon=1` on the installed bank WITHOUT the extras: `hud: weapon: no dial ...: the level has no picture
  113 / 114` once, the stock panel drawn, `0 skipped, N passed`.
- **W5** die and come back as a fed (`[Fed] Player=1`): the raw line's player changes, the dial shows the police guns
  (pictures 60 / 72 or what he carries); round 2 in the same process: `element ... private vtable` again or the same
  element, the dial stands.
- **W6** stand on a dropped gun (a dead policeman's) with `Weapon=0`, then `Weapon=1`: stock shows its arrow beside a
  row; the raw line must say `arrow -1` or `arrow 1` and the dial an arrow left of the disc at that row. `picture 110 is
  W x H` gives its size; a line `the pick-up arrow ... has neither a type-5 nor a type-6 chunk` = no arrow, send it.
- Then the layout by eye: `WeaponX / WeaponY` against the clock and the money box, `WeaponSmall`, the label's length
  (`M9 BERETTA SIL . 120` is the longest).

## 9. Review round (2026-10-11; `re/hud_weapon_review.md`: ACCEPT WITH FIXES) - finding -> what was done

Every finding was checked against the exe / the code again before it was applied (scratch `<scratchpad>\Wfix_*.py`).
Only `klhook/klhud_weapon.c` and this note changed; **the WIRING (section 5) is unchanged**, `wire.py` as it was.
Sections 5, 6, 7 and 8 above are already corrected; the header's point 5 ('both agree with run P1') is limited by 7.11.

| finding | holds? | what was done |
|---|---|---|
| **M1** `klwd_text_setup` calls 0x45d6e0 on unchecked objects | yes | both objects (text, shadow) are read and must show `KLU_TEXT_VT` before either call; else no call and `scaled` stays 0 = another try next tick |
| **S1** the label's reserve is the raw counter | yes | reserve = `elem+0x150c` - rounds = the game's own count; a total of 999 or more = endless = no number; the raw `+0xe0` only in the log line, and for the label only when the game shows no number (-1) |
| **S2** the ring empties the other way than the draft | yes (`hud_mockup.html` 418: `80 100` rotated to the top; klu_ring draws dabs `first .. n-1`) | own loop: dabs `0 .. round(left x 32) - 1`; at least one dab while rounds > 0 |
| **S3** no low-magazine warning, no pick-up arrow | yes. READ 0x5c56b5 .. 0x5c56e1: `elem+0x122c` = `[0xbbe490]` white, `[0xbbe4d0]` red when the fourth argument (0x54ee60's answer) is set. READ 0x43cb30: `elem+0x12d4` = 0, -1 (the offered gun's picture is gun 0's, or neither's), 1 (gun 1's). READ Render 0x5ec95c .. 0x5eca31: picture 110 (handle `table+0x528`, size `table+0x52c / +0x530` x `[0xcee050]`; record `elem+0x1278`, 40 bytes: width +0x1c, height +0x20), 24.0 (`[0xb2e7c8]`) x state below the place, one DrawChunk, no shadow | ring and big count coral on `elem+0x122c` red OR the picture's red; the picture coral on its own red only (as stock). The arrow is DRAWN: left of the disc at the row (`KLWD_ARROW_*`), the element's colour `elem+0x129c`, by klu_addpic when 110's chunk is type 5 at run time, by klwd_pic6 (gun 0's record) when type 6; neither = one log line a level |
| **S4** a foreign draw context blanks the panel | yes | that call goes to the stock Render (counted as 'passed') |
| **S5** the state in which the game draws no gun | yes, and now READ what it is: player vt+0x388 = 0x76ea90 = `[[player+0x19c]+4]->vt[+4]()` (0 without an action), vt+0x38c = 0x7d7fb0 = that object; the same two routines in `ZFFPlayer` (0xbb45f4) and `ZPlayer` (0xba714c). Number 0x21 = `ZFFActionCloseCombat` (RTTI of vtable 0xbb4e98; its slot 1 = 0x962850 `return [this+4]`); the only `mov [reg+0xd4], 3` in the close-combat / player code is 0x76eac9 in 0x76eab0, the routine that takes hold of a target (re/convert_audit.md) | `klwd_grab`: checked reads, no call - the player's two slots must be those routines (else: dial off, stock panel, reason logged), action vtable 0xbb4e98 (or slot 1 = 0x962850), `[+4] == 0x21`, `[+0xd4] == 3` -> guns, counts, ring, label and arrow off, the disc stays (as the stock plate does). GUESS: the human-shield hold. It is NOT the knock-down (a movement state, re/player_down.md), so the owner's 'no shooting while down' is not this state |
| **S6** `[0xcee050]` not applied | yes | read each tick (0.05 .. 8, else 1.0), kept with each queue entry, applied to the gun pictures and the arrow. klhud.c's `klu_pic` has the same gap: the lead's file |
| **S7** the fall-back number changes meaning silently | yes | one line a level: `hud: weapon: gun 0 (...): no counters read ...: the dial shows the panel's own number N = rounds + reserve ...`; the label then has the name only; the ring (from the bar records) stays |
| N1 'READ' partly inferred | yes | section 7 point 11 |
| N2 names against baked looks | yes, NOT fixed | needs the level's `KLGuns.ini` (klgun.c's data): the label says 'AK-47' under an M4A1 look. For the lead / the owner to decide |
| N3 the disc's grey outline | not done | picture 115's stroke at 141 px is unseen; one klu_addpic when wanted |
| N4 middle 1145.5 against the note's 1177 | left | follows klhud.c's inset rule like every other element; move all together |
| N5 empty disc for an unarmed player | fixed | nothing is drawn when no gun shows and the plate flag `elem+0x122b` is 0. The `-1` number mode is not followed |
| N6 lone 'stands again' lines | fixed | the quiet reason no longer counts as said below Log=2 |
| N7 frames without the panel / the canary | left | the 'lock busy' counter shows it in W1 |
| N9 chaining with the sibling tracks | for the lead | `KLU_NTEXT` last; `klwd_compose()` behind `klu_dials(&s);` |

New in the Log=2 raw line: `plate`, `tick colour`, `arrow` with picture 110's size and colour, `action`, `close-combat
hold`, `size factor`.

Live order now: W0, W1 (alone, the 'render:' line first), W2, W2b, W6, W3 (with the hold), W4, W5.
