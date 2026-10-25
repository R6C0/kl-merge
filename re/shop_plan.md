# Weapon shop revamp - findings and staged plan (worker 'shop', 2026-10-15; owner: 'shop revamp would be good')

Nothing here was run in the game. Step 1 (below) is built; the rest is a plan.

## OWNER WISH 2026-10-24 ~14:45: hire your heister in the buy shop (NOT BUILT)
Owner: "people can buy their heister dependent on their rank e.g. go as kane but it costs them money to 'hire' them to be that guy
for the heist" - "character screen as in the buy shop screen". So: the between-rounds Buy Weapons page gets heister entries (Kane,
Lynch, the Dead Men FA crew, Dog Days' heisters) priced in the round money and locked by rank like the gun rows (star / lock glyphs);
buying one makes you that character for the next heist. Ties into the existing Heister page / wardrobe (`klhook/klchar.c`,
`re/wardrobe.md`, `re/characters.md` 6) and 'each character usable once per match' (end goal 3). Open: free default heister, price and
rank table, whether bots may take a hired heister, online. Queued after the 10-24 shop restyle, Hot Coffee II door, cover and car-blast fixes.

## 1. What the shop is

**XML (the LEVEL archive's `Menu/online.xml`, read from the installed DM01 F01_Main.zip):**
- `FABuyWeaponsNew` (opened by code from `MercsFAStatusReady` 0x7558ce): the two slots Primary / Secondary (`FAWeaponText`
  OpenWindow, focus bars `WeaponBuyFB#01/#02`), the carried guns' pictures (`MercsGraphicFA` TagName Primary/SecondaryWeapon,
  PlayerIndex 0..35 -> `FAStatus_WeaponNN#01/#02`, row 6 uses picture 36), their names (`MercsShowInfoFAWeapons`
  Old*Weapon), `FATotal`, the round counter. => the page ALREADY is a loadout view (two cards: what you carry).
- `FABuyWeaponsNewCategory`: Pistols / Shotguns / Submachine Guns / Assault Rifles (bars `WeaponBuyFB#03..#06`).
- `FABuyWeaponsNewWeapon`: 8 rows a page (`WeaponName`, PlayerIndex 0..7, bars `#07..#14`, PageSize=8, arrows), the big
  picture `FAWeaponGraphicBig` PlayerIndex 0..35 -> `FAStatus_WeaponBigNN`, 6 stars `WeaponShopStar#01..06` (X 423..591, Y 460),
  8 locks `WeaponShopLock#01..08`, `NewWeapon` (name, 432/293), `NewWeaponDescription` (TextWidth 470, LineSpace 22),
  `PackagePrice` (DirtyMoneyColorSet), `IsWeaponAvailable`, `FABuyWeaponInfotext` ('Insufficient funds').
- `BuyWeaponDialog`: 'Are you sure you want to purchase this weapon?'.
- Code that fills it: `MercsFASelectorWeapons` (vtable 0xbbd494), `MercsShowInfoFAWeapons` (update 0x50c630), `MercsGraphicFA`.

**Data:** the shop table at 0xbd1f68, 36 rows x 24 bytes `{item, ammunition, price, rank, tier, DLC}` (read from the owner's
kl2.exe today; tier = the number of stars, DLC -1 = none). It is in .rdata 0xb8b000-0xbeb000 = HASHED (re/antitamper.md): it
cannot be written, extended or re-pointed; its readers (0x6a5260 price, 0x8a3e40 rank, 0x808220 availability) are hashed
code. 64 weapon items exist (eFF2ItemCount); no new item, no new row.

| row | item | stock name | shop name (decec9b) | ammo | price | rank | stars | DLC |
|---|---|---|---|---|---|---|---|---|
| 0 | 6 | N 77P | M-77B | 150 | 2,000 | 0 | 2 | |
| 1 | 7 | N 77P Silenced | M-77B SIL | 150 | 4,000 | -1 | 2 | 2 |
| 2 | 8 | Doretta | M9 BERETTA (look USP) | 150 | 6,000 | 0 | 3 | |
| 3 | 9 | Doretta Silenced | M9 BERETTA SIL | 150 | 8,000 | -1 | 3 | 0 |
| 4 | 3 | Copper | POLICE REVOLVER | 150 | 10,000 | 0 | 3 | |
| 5 | 11 | DD 33 | TT-33 | 150 | 13,000 | -1 | 3 | 3 |
| 6 | 4 | Nianshi 226 | SIG 226 | 150 | 15,000 | 1 | 4 | |
| 7 | 1 | SM45 | SW MP45 | 150 | 18,000 | 0 | 4 | |
| 8 | 10 | Wasteland Hawk | DESERT EAGLE | 60 | 30,000 | 3 | 4 | |
| 9 | 5 | KL Viper | COLT COBRA | 60 | 35,000 | -3 | 4 | 3 |
| 10 | 2 | TOQ Model 66X | TAURUS JUDGE | 35 | 60,000 | 7 | 5 | |
| 11 | 14 | Nianshi 40XR | HAWK SAWN-OFF | 40 | 32,000 | 0 | 3 | |
| 12 | 16 | Steele 870 | REMINGTON 870 | 40 | 55,000 | -4 | 3 | 0 |
| 13 | 13 | TOQ Model 18 | HAWK POLICE | 40 | 68,000 | 4 | 4 | |
| 14 | 17 | Gras 12 | SPAS-12 | 60 | 120,000 | 5 | 5 | |
| 15 | 15 | RTS | TPS | 60 | 170,000 | -7 | 5 | 3 |
| 16 | 12 | Buqiang 300BP | HAWK BULLPUP | 60 | 200,000 | 7 | 6 | |
| 17 | 22 | DK ST80 | SP89 SIL | 300 | 45,000 | 2 | 4 | |
| 18 | 23 | PAC 10 | MAC-10 (look STEYR TMP) | 300 | 26,000 | 0 | 3 | |
| 19 | 24 | PAC 10 Silenced | MAC-10 SIL | 300 | 28,000 | -2 | 3 | 2 |
| 20 | 25 | SMi 69 | MPI 69 | 300 | 30,000 | -1 | 3 | 3 |
| 21 | 18 | Desert Spider | SA61 | 300 | 24,000 | 0 | 2 | |
| 22 | 27 | Nianshi 500 | TYPE 05 (look P90) | 300 | 65,000 | 3 | 5 | |
| 23 | 28 | Nianshi 500 Silenced | TYPE 05 SIL | 300 | 67,000 | 6 | 5 | |
| 24 | 26 | Nianshi 700 | TYPE 79 | 300 | 30,000 | 0 | 3 | |
| 25 | 20 | TOQ Model Four | UMP | 300 | 50,000 | 5 | 4 | |
| 26 | 21 | TOQ Model Four S | UMP SIL | 300 | 52,000 | -6 | 4 | 3 |
| 27 | 19 | TOQ SBR | UMP SBR | 300 | 55,000 | -1 | 4 | 0 |
| 28 | 29 | Vamazast | ZASTAVA M85 (look MP5) | 300 | 100,000 | 0 | 2 | |
| 29 | 31 | Kaliningrad 47 | AK-47 (look M4A1) | 250 | 145,000 | -1 | 3 | 1 |
| 30 | 32 | Kaliningrad 74 | AK-74 | 250 | 135,000 | 0 | 3 | |
| 31 | 34 | Buqiang 800 | TYPE 88 | 50 | 160,000 | 1 | 4 | |
| 32 | 36 | Buqiang 800 Scoped | TYPE 88 SCOPE | 50 | 210,000 | 4 | 4 | |
| 33 | 30 | TOQ Elite | FN SCAR (look SG 552) | 250 | 180,000 | -5 | 4 | 2 |
| 34 | 37 | Buqiang 900 | TYPE 95 | 250 | 240,000 | 6 | 5 | |
| 35 | 39 | Buqiang 900 Scoped | TYPE 95 SCOPE | 250 | 245,000 | 6 | 5 | |

(Correction for re/map_guns.md line ~301: the Type 05 costs 65,000, not 24,000 - 24,000 is the SA61, row 21.)

**Texts:** level .LOC `AllLevels/Menu/Online/WeaponShop/Weapon<row>` / `Weapon<row>Desc` (+ headings, buttons, messages).
**Pictures:** level .TEX art `FAStatus_WeaponNN` (small, slots) and `FAStatus_WeaponBigNN` (the card), `WeaponShopStar`,
`WeaponShopLock`, `BackgroundWeaponShop`, `FocusBar_short#..`.
**Stats, sounds, animations:** the item's template in the level (ZFFItemTemplateWeapon); a Dead Men gun is only a LOOK
(hidden parts of a Dog Days gun's model; tools/kl_guns.py, kl_map_guns.py, klhook/klgun.c).

## 2. What was already changed
- decec9b `tools/kl_hud_shop.py`: the 36 names in the HUD dial's wording; descriptions tidied (curly quotes).
- `tools/kl_hud_menu.py level`: the shop's `WeaponBuyFB` bars repainted as opaque chalk (AlphaMax 255; locked-row
  readability NOT ESTABLISHED, re/hud_menu.md M3), colour sets in the draft tokens.
- Gun looks on every installed map: MP5 / SG 552 / M4A1 / P90 / Steyr TMP / USP (KLGuns.ini Shown=1 on all eight; owner's ini
  [Guns] Enable=1 Start=1 Set=1) - but the shop and the dial still said ZASTAVA M85 / FN SCAR / ... .

## 3. The hard limits
1. No new menu element (Window / GuiElement / ColorSet / ButtonGraphic) until room is made: the table has 5,096 slots and a
   margin of about 4 (CLAUDE.md, re/hud_menu.md 1.1). Everything below is ATTRIBUTE / TEXT / TEXTURE only, or hook-drawn.
2. Prices, ranks, stars, DLC locks, ammo per purchase: the hashed table. No byte of it, no code that reads it.
3. Order of rows / sorting: decided by the table and the selector code (category = item kind, row order = table order).
   Not changeable without code patches in hashed .text. Sorting is NOT realistic.
4. New guns: not possible (64 items). Dead Men guns = looks on Dog Days items, one look shown per item per level.

## 4. STEP 1 - BUILT (this worker): the looks are sold and carried under their own names
- tools (patch `~/w_shop/shop_tools.patch`, files `~/w_shop/tb/tools/kl_hud_shop.py`, `kl_hud.py`): `apply_level(files, log,
  guns=<build>/KLGuns.ini)`; a row whose item the build shows as a look takes the look's name (MP5, SG 552, M4A1, P90, STEYR
  TMP, USP; AK-74 if Start=2 is baked) and, in English, a new description in the shop's 'Police reg.' manner ending 'Handles as
  the <Dog Days gun>.' (honest: price / stats / sound are the Dog Days gun's). `python kl_hud_shop.py names <build | KLGuns.ini>`
  prints what a build would get. The English stock-name check now also accepts our own earlier names, so a level baked with
  the shop names can be baked again. No KLGuns.ini / Shown=0: exactly as before. Offline test on DM01's .LOC: 12 leaves, a
  second pass 0, no looks 0.
- hook (patch `~/w_shop/shop.patch`): klgun.c publishes per item the name of the look on screen (the pass's, else the baked
  `Shown`), double-buffered for the render thread; klhud_weapon.c `klwd_gname()` puts it under the dial. Key `[HUD]
  LookNames=1` (default 0 = unchanged); with [Guns] off the file is still read for the names, nothing written.
- Known gap: the shop name is BAKED; switching the look later on the Guns page (Start 1 -> 2) changes the dial (live) but not
  the shop (says MP5 while the gun is the AK-74 look). Fix = stage 3 (runtime text) or bake per the owner's chosen Start.

## 5. Next stages (each one table-neutral; order = safest and most visible first)

**Stage 2 - the cards (tool, .TEX + .LOC only).**
- 2a. Pictures of the six looks: render the Dead Men model (kl_view, as `kl_guns.py sheet` / kl_portraits.py do) into the
  texture of `FAStatus_WeaponBigNN` and `FAStatus_WeaponNN` of rows 2, 18, 22, 28, 29, 33 - same texture ids, sizes and
  format (the `repaint()` rules of kl_hud_menu.py: `picture_uses()` first; a tile shared with another entity is left).
  Look: chalk silhouette on ink, the draft's dry-brush edge (kit painter). Needs: the texture ids/sizes of those pictures
  (static read of a baked level), one look check of the sheet by the owner before baking.
- 2b. The other 30 cards in the same chalk/ink style (posterise + outline of the stock picture), so the page reads as one
  set. Same rules; `check-level` must say TABLE identical.
- 2c. Stat line in the description (text only): the tool reads each template's damage / fire rate / magazine from the level
  (properties of ZFFItemTemplateWeapon - which property is which is NOT ESTABLISHED: step 0 = list them for three guns with
  kl_prp and compare with play) and appends e.g. 'DMG 4/6  RATE 5/6  MAG 30' to `Weapon<row>Desc` (fits TextWidth 470).
- 2d. Stars / locks: `WeaponShopStar` / `WeaponShopLock` tiles repainted as chalk marks (texture only).
- Live check S2: open the shop on one tab map, page through all four categories; every card readable, no assert, round 2 starts.

**Stage 3 - runtime (hook, data only).**
- 3a. Shop name follows a live look switch: overwrite the shown text of `NewWeapon` / `WeaponName` elements in the shop
  windows (heap) - needs the text field of a MercsShowInfoFAWeapons element (not read yet) or the LOC leaf in memory
  (string in a heap tree; length <= the baked one). Step 0: find where 0x50c630 gets the name.
- 3b. Re-pricing by refund (no table write): the hook sees the purchase (the player's money [score+0x38] drops by exactly a
  row's stock price while the shop window is open) and gives back stock - new price. Only CHEAPER prices are safe (the
  afford-check still uses the stock price), and the page still SHOWS the stock price unless 3a's text overwrite also does
  `PackagePrice`. Arcade + not-stock-level gates; host only (money is the host's) - re/fed_kit.md 'score' notes first.
- 3c. Re-statting: template properties in the level (tool) = per-map balance of the Dog Days guns; or klbalance.c-style
  runtime scaling of damage. Owner decides which guns; NOT before 2c says what the numbers are.

**Stage 4 - loadout preview in the draft style (hook-drawn, after B-P1).**
- The first page already shows the two carried guns; a hook card (klu pictures/texts, as klhud_board2.c draws the board)
  over `FABuyWeaponsNew`: the two cards + money after purchase. Blocked on re/hud_board_b.md B-P1 ('does the HUD render in
  state 0x20 / the shop'); never as new XML elements.

**Stage 5 - more Dead Men guns as looks.** Only on items that have no look yet (the silenced rows 1, 3, 19, 23, 26, the
shotguns, the Type 88/95); kl_map_guns.py `fit` decides the pairing; Mini-14 / Taurus are in no Dead Men level tree
(kl_guns.py EXTRA, experimental). Each new look is automatically named in the shop and on the dial by step 1 once
LOOKS in kl_hud_shop.py has its label.

## 6. Live checks for step 1 (owed)
- L1 (hook): ini `[HUD] LookNames=1`; any tab map. KLHook.log at the load: `guns: names for the HUD dial (LookNames=1),
  item=name: 29=MP5, 30=SG 552, 31=M4A1, 27=P90, 23=STEYR TMP, 8=USP`; the dial reads MP5 . <reserve> with the Zastava.
- L2 (tool): rebake one map with `kl_hud.py ... --look deadmen` (or `markers`) from its build folder (KLGuns.ini beside the
  archive); log line 'Dead Men looks sold under their own names: ...'; in the shop: Assault Rifles shows MP5 / M4A1 / SG 552,
  the card text 'Handles as the Zastava M85.'; buy one, round 2 starts.
