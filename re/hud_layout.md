# The agreed HUD, as numbers for klhud.c (2026-10-11, kl-merge-76)

The owner's draft is https://claude.ai/artifact/ARZVji4pNmpkFz5SFtyTL2 (version 24, 'looks good'). This file turns its stage
into the game's 1280 x 720 virtual screen (origin top left; the draft's unit 1 cqw = 12.8 px) and says which primitive
draws what. Text = a ZCHAROBJ through the corrected transform (re/hud.md 9); picture = `klu_pic(el, ctx, slot, x, y, w, h,
argb, layer)` (re/hud.md 8, klhud.c). NOTHING here has been seen in the game: klu_pic's anchor (centre or corner) and the
right-aligned text style are the two things live check P2 settles; every x below assumes pictures are anchored at their
CENTRE and that style 0x12 right-aligns at x, 0x44 left-aligns (ASSUMPTIONS).

## Colours (ARGB)

| name | value | use |
|---|---|---|
| chalk | ff f3f0ea | text, strokes, rings |
| ink | ff 0c0c0d | text on a painted block |
| coral | ff f0475a | labels, last-minute timer, kill marker |
| orange | ff e8831f | traitor block, escape dial, traitor pop-up |
| green hi | ff 63a65b | total, cash in the list |
| green | ff 4f8f49 | loot, rewards |
| dead | ff 8c3138 | dead rows and their strike |
| dim | ff 6f6c66 | the inactive gun, lost lives |
| back | 9c 080809 | dial discs |

## Pictures (HUD picture slots; the extras are `kl_hud.py --look deadmen`, textures 3000..3007)

111 stroke 256x32, 112 dry 256x32, 113 dab 32x32, 114 disc 128x128, 115 ring 128x128, 116 dollar 128x128, 117 frame 256x32,
118 box 256x64; stock: 170 car, 171 chopper, 178 skull (Kill, 32x32), 58..106 weapon pictures (128x128), 181 white.
A RING that empties = N dabs (113) on a circle of radius r, dab k at angle 2 pi k / N from the top, clockwise; only the dabs
of the part that is left are drawn. N = 24 for the watch and the escape dial, 32 for the weapon dial, 20 for the loot ring.

## Elements

| element | where (px) | drawn with |
|---|---|---|
| **heister list** | left 33, top 38, width 211 | |
| label 'DEAD MEN' | text left at (33, 38), font H3, coral | text |
| count 'n / 8' | text right at (244, 38), H3, chalk | text |
| rule | stroke centre (138, 60), 211 x 5, chalk | pic 112 |
| row i (0..7) | pitch 30, row box centre (138, 81 + 30 i), 219 x 28 | |
| own row | block: pic 111 chalk 219 x 28; name ink; cash dark green ff1f4a1d; lives = three skulls (178) 12 x 12 from x 33 + name width + 8, ink / 4c0c0c0d when lost | pic + text |
| traitor row | block: pic 111 orange; name + cash ink; tag 'TRAITOR' in the label font | pic + text |
| other row | name chalk left at (41, 72 + 30 i), H2; cash green hi right at (236, same) | text |
| dead row | name + cash dead; strike: pic 112 dead, centre (33 + name width / 2 + 8, 81 + 30 i), (name width + 12) x 4 | text + pic |
| escaped row | name ffa9a59d, tag 'OUT' | text |
| **round watch** | centre (1212, 66), diameter 69 | |
| back | pic 114 back 69 x 69 | pic |
| ring | 24 dabs chalk 9 x 11 on r = 29; left = time left / round length | pic 113 |
| hand | 6 dabs 5 x 5 from the centre to r = 22 at the ring's current angle; hub dab 8 x 8 | pic 113 |
| last minute | the watch is not drawn; text 'mm:ss' right at (1247, 44), H1, coral | text |
| round | text right at (1247, 106), H3, coral: 'ROUND n OF m' | text |
| **escape dial** | centre (1137, 71), diameter 55; only while the vehicle waits (rules vt+0x12c state 3) | |
| back, ring | pic 114 back 55 x 55; 24 dabs orange 7 x 9 on r = 23; left = wait time left (vt+0x130) / 8 s | pic |
| icon | pic 170 (car) or 171 (chopper, vt+0x17c != 3) chalk 30 x 30 | pic |
| **money** | right 1247, top 123, width 211 | |
| TOTAL | label left at (36, ...) -> (1036, 131) coral H3; value right at (1247, 123), H1, green hi | text |
| loot bar | frame: pic 117 chalk centre (1141, 163), 211 x 12; fill: pic 111 chalk left part, width 211 x share | pic |
| LOOT, REWARDS | labels left at (1036, 178 / 204) coral H3; values right at (1247, 174 / 200), H2, green | text |
| **weapon dial** | centre (1177, 598), diameter 141; the stock ZWeaponDisplay (osd+0x1110) hidden (+0x25) | |
| back | pic 114 back 141 x 141 | pic |
| ring | 32 dabs chalk 12 x 16 on r = 62; left = rounds in the magazine / magazine size | pic 113 |
| active gun | count: text right at (1170, 566), H2, chalk; picture: its weapon picture (58..106) 64 x 64 centre (1205, 572) | text + pic |
| divider | pic 112 chalk a=73, centre (1177, 600), 87 x 2 | pic |
| inactive gun | count: text right at (1172, 618), H3, dim; picture 36 x 36 centre (1198, 622), dim | text + pic |
| label | 'NAME . reserve' centre (1177, 684), H3, coral | text |
| **pop-up** | centre (640, 520): the game's own ZFAAnnouncementDisplay text, restyled | |
| bar | pic 111 chalk, (text width + 62) x 34, text ink; the traitor message: pic 118 orange box + pic 181 back fill, text orange | pic + text |
| **loot ring** | at the game's use-action prompt while a loot action runs | |
| ring, disc, sign | 20 dabs chalk on r = 26 (filled part = progress), pic 114 ff0f100f 40 x 40, pic 115 ff8d8982 40 x 40, pic 116 green hi 34 x 34 | pic |

## Data each element needs (re/hud.md 5, klbot.c, klfedkit.c)

- list: klb_read records (name [[record]+8], money, status 0 in play / 4 aboard / 6 escaped / 7 dead, flags bit 0 = AI,
  bit 1 = traitor); lives: the stock list's skull count (NOT established where it is read: re/hud.md 2.2 player list).
- watch: rules vt+0x124 (seconds left) against the round length (the first value seen after state 0x19).
- escape dial: rules vt+0x12c (state), vt+0x130 (time), vt+0x17c (kind).
- money: 0x807520(rules) total; carried = record money; rewards = NOT established (shown as BANKED = total - carried until read).
- weapon dial: ZWeaponDisplay's own fields after its Tick 0x88bac0 (counts and picture indices elem+0x2e8 + 4 i) - read the
  element, do not re-derive from the player (ASSUMPTION in re/hud.md 5 marked 'partly').
- loot bar share: sum of the crew's money against the level's loot total (NOT established: leave the bar out until it is).

## Order of work (each step needs its own picture before the next)

1. P2: text + three test shapes (klu_pic's anchor, size, colour).  2. X0: a level with the extras loads.
3. The list with blocks and strikes.  4. Money.  5. Watch + escape dial (rings of dabs).  6. Weapon dial, stock panel hidden.
7. Pop-up bar, loot ring.  8. Round-over / menus (XML pages: re/menus.md), separate.
