# [Shop] OnlineSwap bench recipe (2026-10-28, branch wk-swap-1028; code not run in the game)

What it does: online, shop rows named by a baked map (13/16/32/35 = HK69 / TYPE 81 / REM 700 / MINIMI) hand over that gun, like Arcade's [Shop] Swap.
No network message changes (a buy sends rows; each peer resolves row -> carrier label -> a free pool object). Code: klshop.c (kls_osw_early / kls_osw_tick),
hook point = klshoppage.c kspg_early_make (kllobby.c slot-26 wrapper, between the pool build and the Quazal DO pass).

## Setup (2 seats online, host + client, same build on both)
- Map: a BAKED grafted map, e.g. the DM07 build bound to F06 or any map whose KLGuns.ini says `Swap=13:..,16:..,32:..,35:..` (tools/kl_shop_swap.py bake). Same archive on both seats.
- KLHook.ini on BOTH seats (the same Swap set; the log hash must match):
  - `[Shop] Enable=1`, `OnlineSwap=2` first (log only), then `OnlineSwap=1`
  - `[ShopPage] Enable=1` (the hook point is armed from klshoppage.c), `OnlineLook=1` or whatever the bench already uses so the shop opens online
  - optional: `[Shop] OnlineSwapText=0` (the baked names are now correct; with =1 the names would say the STOCK gun and be wrong)
  - `[ShopPage] Log=1` for the link lines
- Round: both buy rows 13, 16, 32 and 35 in separate rounds (one per seat per round), start the round, look at the gun in hand and the HUD name.

## Run 1: OnlineSwap=2 (log only, nothing made)
grep KLHook.log (each seat):
- `osw: set 4 pair(s), hash XXXXXXXX` -> the hash is IDENTICAL on host and client
- `osw: LOG ONLY row 13 (carrier item ..., N stock object(s)) would get 8 object(s) of item ..` for each row
FAIL if: `osw: early make skipped`, `no template`, `no stock object` (then hook point or gate is wrong), no `osw:` line at all (check [ShopPage] Enable, OnlineEarlyMake not needed).

## Run 2: OnlineSwap=1
grep KLHook.log (each seat):
- `osw: row 13 (carrier item ..): 8 object(s) of item .. made (host|client)` for rows 13/16/32/35
- `osw: early make done: 4 pair(s) in the set, 4 made now`
- `osw: row 13: 8 object(s), 8 with gun+0x13c set, id 0x6ece90 of the first = N ... ours are handed over`  <- THE PASS LINE: all 8 with +0x13c set
- compare the `id 0x6ece90 ... = N` of each row: IDENTICAL on host and client (same object order)
- in game: the buyer holds the baked gun (HK69 etc.), name and icon match, sound is the gun's; no crash, no 0x9425a4 / int3 0x538f02 in the dump
PASS = all of the above on both seats, 0 faults, and Arcade unchanged.
Fallback (safe, not a pass): `STOCK gun stays (net sub-object missing)` = the DO pass did not link our objects; the stock gun is handed over as before. Then the early
make is not at the right moment (read the `shopPage: link check` lines too).
FAULT: `shop: OnlineSwap early make FAULTED` -> switched itself off, stock guns stay.

Also check: Arcade (offline) and a stock FA map with OnlineSwap=1 behave as before (the key only acts online; offline [Shop] Swap path untouched).
