# More guns in the weapon shop (track 3f, 2026-10-19; static reading + compile; NOTHING RUN)

## Verdict
More ROWS than 36 are impossible (CERTAIN, read): the shop is the hashed table 0xbd1f68 (36 x 24 bytes); the pool builder 0x78a8d0
loops exactly 0xbd1f68..0xbd22c8, the buy RMC carries ROW BYTES and the server pricing (0x6a5260) and loadout (0x410710) index the same
hashed table. A private vtable on MercsFASelectorWeapons (0xbbd494) / MercsShowInfoFAWeapons (0x50c630) changes only what the menu
shows, not what a row means to the buy and the loadout, so it was rejected. Candidate (c) (more looks) is shop_plan stage 5, no new gun.
What IS possible: change WHAT A ROW HANDS OVER. `klhook/klshop.c` ([Shop] Enable=1, Swap=row:item,...) does it with the weapon pool.

## How (CERTAIN = read in kl2.exe)
- CERTAIN: the loadout gives table[row].item via 0x538ec0 -> 0x55bee0 = a pool search for a free object LABELLED with that item
  (`[0x168e96c]` -> vector {+4 count, +8 cap, +0xc grow, +0x10 array of 12-byte {object, item label, byte+8 free, byte+9 dropped}}).
  Ammo and handling come from the OBJECT (vtbl +0x304/+0x308), not from the table's ammo column. The label is used only for the search.
- CERTAIN: the builder makes objects with 0x710ad0 (`this` = [[0xdd265c]+0x15b0], args 0 and the template from 0x5d2f50(item)) and appends
  {obj, item, 1} with cap += grow / realloc via IAT 0xb10328; klshop copies that recipe, with the carrier's label and the extra gun's template.
- klshop: parks the carrier's stock entries (byte +8 := 0), adds 8 objects of the extra gun labelled as the carrier. Buying the carrier row
  hands over the extra gun. Gate: Arcade only, kl_online()==0, ZGameRulesHeist, state < 0x19; code-byte check of 0x710ad0 and 0x5d2f50.
  Re-applied when the pool was rebuilt (a new round). No code byte, no hashed byte is written.

## What the owner sees
The shop still shows the CARRIER's name, picture, stars, lock and price (text/pictures are indexed by row; they would need baking via
LOC/menu text, tools/kl_hud_shop.py style). So a swap is "row 28 now secretly gives a different gun"; rename it yourself.
Price: the carrier's price (the table is hashed; a swapped-in gun cannot have its own price). Pick a carrier whose price fits the gun.
Rows (read from the exe, `python tools/kl_shop_extra.py rows`): 0 item 6 2,000 ... 35 item 39 245,000 (full list in shop_plan.md).
Non-shop weapon items: 33, 35, 38, 40-59, 62, 63 (41-48 variants). `python tools/kl_shop_extra.py check <build>` lists which have a template.
Offline survey of the M01 build: templates for nearly all of 1-63 (not 51, 55-59 for handling); the police set has handling for the MGs,
Rem700, RPG and HK69 only.

## GUESS (not proven)
1. Handling clips: the criminal animation sets must carry the extra gun's clips, else T-pose / broken arms. Choose items whose handling the set has.
2. The inventory may need a binding for the item (a missing one may block the pick-up silently).
3. 0x753150(session, 0.0f, -1), called per item by the builder, is NOT repeated (probably net spawn bookkeeping; offline irrelevant?).
4. DLC / rank gating of the carrier row still applies (choose an unlocked carrier).
5. Objects are freed by the pool reset like the builder's.
6. Online: untouched (kl_online() gate); peers would not know the gun.

## Live tests (owner, Arcade, game closed for install)
1. `[Shop] Enable=1`, `Swap=0:40` (row 0, M-77B, 2,000 -> item 40, if the build has its template). Log must say "shop: row 0 ... now hands over item 40".
2. Buy row 0, start the round: which gun is in the hands? Animations OK? Shoot, reload, pick up ammo.
3. Round 2: log again "now hands over" (pool rebuilt); a second buy works.
4. A pair for an item without template: log says skipped, shop unchanged.
5. Quit mid-shop and re-enter: no crash at int3 0x538f02 (that would mean the pool lost its free objects).

## Live results (scripted, 2026-10-20 night; DM01 in the F01 slot, TEST hooks, all PASS, 0 asserts, 0 faults)
- S6 (1020a, Swap=2:47): the USP row was bought, but round 2 handed over the stock USP. Cause: the pool survives the round and the
  round's end marks every gun free again, the parked stock ones included (they come first). 1020b re-parks them before each round.
- S7 (1020b): bought USP row -> round 2 holds the MINIMI, but with 'MINIMI / 0'.
- Reserve = ROW ammo (table +4, hashed) - min(clip, row ammo) (0x410710 -> 0x538ec0, 0x538f72..0x538fb4). A 150-round clip on a
  150-ammo row leaves 0. 1020c [Shop] ReserveClips=2 writes [obj+0xe0] = (2 x rounds) ^ 0xbeebbeeb once per hand-over (heap data).
- S8 (1020c): 'MINIMI / 300'; after firing 68 rounds, a reload gave 150 in the clip and 232 in reserve: the reload draws from the written reserve.
- S9 (1020c, Swap=13:52): Hawk Police (shotgun row 13) -> HK69 launcher: held, 'HK69 / 39' (stock formula 40 - 1); fires and reloads
  with the aiming pose (39 -> 30). GUESS (1) (handling clips) holds for a launcher on a shotgun row.
- S10 (TEST 1020d, Swap=16:33, route Shotguns -> DOWN x5): Hawk Bullpup (shotgun row 16) -> TYPE 81: held in round 2
  as 'TYPE 81 / 30', fires, the reload draws the 30 (/ 0). Its clip is below the row's ammo, so the stock formula gave the reserve
  and ReserveClips correctly stayed out (no log line). PASS, 0 faults. The row was LOCKED (rank 1 Mastermind) in the shop, yet the
  scripted msg BuyWeapon bought it: the lock is a UI check only. A player still needs the rank to buy it by hand.
- S11 (TEST 1020d, Swap=32:49, route Assault rifles (DOWN x3) -> DOWN x4): Type 88 Scope (row 32) -> REM 700: held in round 2 as
  'REM 700 / 45' (row ammo 50 - clip 5, stock formula), fires and reloads (-> 40). PASS, 0 faults. The shop's highlight showed the row
  above (TYPE 88 description) at that moment, yet the Rem 700 (only row 32 carries it) came out: the description pane is not a reliable
  read of the cursor in shots. Shop categories by table order: pistols 0-10, shotguns 11-16, SMGs 17-27, rifles 28-35; DOWN x (row - first).
  With S7 (Minimi on a pistol row) all four guns of the default DM01 line 13:52,16:33,32:49,35:47 are proven to hand over and fire.
- Shop route for scripts: score page -> msg MercsFAStatusReadyHeistLBStatus ZW_SELECT3 (its buttons are mouse-only) -> RETURN (Primary)
  -> DOWN per category (Pistols, Shotguns, ...) -> RETURN -> DOWN per row -> RETURN -> msg MercsFASelectorWeaponsPC3 BuyWeapon -> ESC x3
  -> RETURN (Ready). A row already carried opens no dialog. For row 13 no dialog showed, but BuyWeapon bought it anyway.

## Stock FA maps (2026-10-20, static, read-only on the stock zips)
`python tools/kl_shop_extra.py check <DD>\Scenes\Locations\Fxx\Fxx_Main.zip` for F01..F09: every one of the nine
stock maps has the SAME weapon-template set, including all four default DM01 swap guns (33 Type 81, 47 Minimi,
49 Rem 700, 52 HK69, each with its handling clip set). Items 60/61 have no template anywhere (unusable).
Usable non-shop items on every stock map: 33 35 38 40-59 62 63. A stock map has no KLGuns.ini, so the swaps come
from KLHook.ini `[Shop] Swap=16:33,32:49,...`; the shop names/pictures stay stock (shopswap only bakes DM01's).
Not run live on a stock map (needs a scripted round per map; the shop opens only after a round).
