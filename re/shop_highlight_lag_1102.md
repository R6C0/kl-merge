# Shop list highlight lags the info panel by one row (GUN15 note, 2026-11-01) - diagnosis 2026-11-02

Offline, read-only. Result: NOT shown to be caused by our swap. Most likely stock. No code written.

## Evidence
- GUN15_DD10 / GUN15_DM07 / GUN14_* (solo dirs) contain NO row-level shop shots. Their script only sends ZW_SELECT3 (shop opens on the
  category page: Pistols / Shotguns / SMGs / Assault rifles, no row highlighted) and never presses DOWN in the shop; the 2 s shots show the
  score page, the category page (GUN15_DD10 shot 196) and the next round's loading card. So the 'lag' observation cannot be reproduced
  from those files. (GUESS: it was seen in a shot set that is not in these folders, or by eye during the run.)
- Same symptom pre-dates our online code: shop_more_guns.md S11 (1020d, ARCADE, [Shop] Swap only, no picture code): 'the shop's highlight
  showed the row above (TYPE 88 description) ... the description pane is not a reliable read of the cursor in shots'.
- GUN12b log (online, OnlineSwapPic=1): per DOWN the 'WeaponBig shown row' (stock global 0x154d80c) steps 11,12,13,14,15,16 about 0.1-0.4 s
  after each key, and the script's own 'SHOWN row N' line is stamped 2 s later; the panel is driven by that global, the highlight by
  [selector+0x90]. Two stock indices updated by different code paths, so a one-row skew in a still frame is expected whenever a shot lands
  inside one key's 0.1-0.4 s update.
- Our code never writes the highlight: klshoppage.c only (a) swaps the picture element's index at +0xc4 for ONE update and restores it in the
  same call (OnlineSwapPic, lines ~553-575), (b) on the hire page sets 0x154d80c to 99 for one price update and restores it (~500-510).
  Neither touches [selector+0x90] or inserts rows (swap 'never adds a row').

## Verdict
Stock skew (Arcade shows it too, S11). Fix: none. Only if the owner still sees it with all shop hook keys at 0 would it be ours.

## Probe that would settle it (not written; would be a default-0 log-only key)
Offline Arcade, hook with [Shop] Swap=0, OnlineSwapPic=0: script DOWN x1 in a category, shot at +0.05/+0.2/+1.0 s, and log
[selector+0x90] vs 0x154d80c at each. If the two differ for >0 ms in Arcade, it is stock. Online repeat with the keys on; equal skew = stock.
