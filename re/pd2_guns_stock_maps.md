# PD2 gun looks on Dog Days' 9 stock FA maps (research + plan, 2026-11-06, offline, nothing installed)

## 1. Do the stock maps get any PD2 gun look today? NO
Read-only check (kl_chars.Lv + kl_guns.gun_node + C.person on each folder; scratch script, not committed): the Ground-node root of every SPECS template
(items 35-63) on DD01 / DD02 and Scenes F01 / F02 is the ORIGINAL low root id (F02: item 35 root 13812, item 62 13675). On DM02 the same templates point at
appended roots (58997 ... 59265), so the DM maps carry the retarget and the stock ones do not. (DD02 item 63 shows a high root 39702: an appended Dead Men
look / pics-era root, not a PD2 one.)

Where the stock levels live (DD = `C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days`):
* `<DD>\KLExpansion\Maps\DD01..DD09` (plus DD10 on slot F07): the expansion's copy of each stock slot, `F0n_Main.zip` + `F0n_Main.bots.zip` + KLGuns.ini
  (+ .WAV/.WHD/.hti/KLTalk.ini). The hook's klslot [Redirect] already redirects the stock slots to these (re/bots_online_fill.md:79), so with the hook these
  are what Arcade and private match load. Sizes (zip, bots zip +-1 MB): DD01 249955909, DD02 228497230, DD03 249382874, DD04 267630262, DD05 243596677,
  DD06 241558813, DD07 232120118, DD08 201171320, DD09 243007237, DD10 264953035.
* `<DD>\Scenes\Locations\F01..F09\F0n_Main.zip` = the real stock archives (no KLGuns.ini, no bots sibling). They are ALREADY modified in place (shop buttons
  09-13 / 10-25, shop pics 11-06 03:46-09:35) with the originals kept beside them as `.before-shopbuttons` / `.before-shoppics`.
  Sizes now: F01 221699814, F02 200304156, F03 221166437, F04 239267080, F05 215165543, F06 213424343, F07 204058526, F08 173063090, F09 214548029.
* Inis: KLGuns.ini on DD01..DD09 only (1624 bytes, Version 2, 6 Dead Men looks: Rifle_zastavam85, Rifle_FN_SCAR, Rifle_AK47, SMG_Type05, SMG_MAC_10,
  HG_M9Beretta), exactly ONE `Entries=` each, and it already equals the .prm chunk count read from the zip (46115 / 39929 / 48087 / 51572 / 38872 / 52683 /
  56374 / 48265 / 51726). No KLJoin.ini on DD01-09 (DM maps have one with [FedBody]; DD10 has a 365-byte one). Scenes F0n have no inis.
* Shop pics (open_work_log.md:171, 11-06 ~10:00): baked on stock F01-F09 (Scenes), DD01-DD09 and 9 DM maps; DD10 / DM05A left to c9. The +72 chunks are in the
  counts above.

## 2. Would build_level work on a stock .prm? YES, templates all resolve
All 19 SPECS templates resolve (kl_guns.gun_node finds exactly one Ground node each): `ok 19 miss []` on DD01..DD10 (chunks DD01 46115, DD02 39929, DD03 48087,
DD04 51572, DD05 38872, DD06 52683, DD07 56374, DD08 48265, DD09 51726, DD10 61170; Scenes F01 24923, F02 18734). The host roots on DD02 and Scenes F02 are
identical (13812 ... 16134), so the DM maps share the same Dog Days gun hosts and the frozen fits (fits.json) apply unchanged. What differs:
* Item 63's host `HG_M9Beretta_Human_Shield` is a different template from `HG_M9Beretta` (KLGuns.ini Gun.6, Item 8, Root 45888, look USP). No SPECS template equals a
  Gun.N template, so the Dead Men look table is untouched; re-check with one assert after the bake.
* KLGuns.ini has one `Entries=`; pd2_guns_layer.fix_inis rewrites a single line whatever it held, so it follows the new chunk count.
* `DETAIL` in tools/pd2_guns_layer.py has no entries for the batch 1-2 keys (SG417 G36 RPK MK17 RPK40 RPK42 RPK43): a one-layer all-keys bake needs them
  (read the body-object detail byte from a DM report.json) or verify KeyErrors.
* No Int16Ok.txt on DD01-09 (DM11B only). The DD folders show no `*.bots.base.md5` in the listing read: stage() restages it only when the live one exists and
  matched, so confirm with `ls` before staging.
* Online: a peer without the same level bytes sees the stock gun (the page II shop swap is gated off online); same as the DM maps.

## 3. Disk cost (measured from the 1106e stage: du 4.15 GB stage and 4.15 GB off-drive backup for 10 DM maps, ~410 MB a map = plain + bots)
| scope | stage (new zips) | backup of replaced live zips | note |
|---|---|---|---|
| DD01-DD09 (plain + bots) | 4.3 GB (2 x 2157 MB) | 4.3 GB | a layer adds ~1 MB a gun; new zip = old +- 1-5 MB |
| Scenes F01-F09 (plain only) | 1.9 GB | 1.9 GB | optional phase 2 |
| both | 6.2 GB | 6.2 GB | 12.4 GB if everything is kept at once |
D: has 6.7 GB free: the DD01-09 stage (4.3 GB) fits, its backup (4.3 GB) does not until the ~7 GB of duplicate backups are hard-linked away.
Plan: (a) free the 7 GB; (b) stage DD01-09 on D: (4.3 GB); (c) the off-drive installer (template: pd2guns_1106c/d/e, `backup=` key) moves the replaced
live zips to a D: backup folder (4.3 GB); C: net change about 0 (new zip in, old zip out), peak need one zip (~270 MB) vs 1.7 GB free. Do Scenes F01-F09
only after phase 1 proves out, in two groups (F01-F04, F05-F09) if D: is short. Remove the `_botsrc` / `_botsout` / `lvchk_*` scratch as the layer does.

## 4. Step plan
1. Free D: (hard-link duplicate backups). Need D: >= 10 GB, C: >= 1 GB free.
2. New layer in tools/pd2_guns_layer.py `'1106s'`: keys = all 19 SPECS keys, `base=None` (bakes on the live DD zips: pics yes, PD2 no), maps DD01..DD09,
   out `D:\kl_stage\pd2guns_1106s`, backup `D:\kl_stage\pd2guns_1106s_backup`, tag `.before-pd2guns1106s`, seeds `D:\kl_stage\pd2guns_1106e\fits.json`, DETAIL entries
   added. (Alternative: run the five existing layers in order on DD maps: 5x the bake and 5 backups, not advised.)
3. `python tools/kl_tests.py`, then `python tools/pd2_guns_layer.py build --layer 1106s` and `verify`: expect `LAYER RESULT: PASS`, `old_chunks_diff=0`,
   plain and bots chunks equal, Entries == new chunk count.
4. Files touched per DD map: `F0n_Main.zip`, `F0n_Main.bots.zip`, `KLGuns.ini` (Entries only). Renamed to backups, never written through; md5 pins as in
   install.py (pins.json). `install-py` writes install.py / INSTALL.bat / UNDO.bat. Undo: install.py --undo (undo any layer put on top first); add it as step 0 of
   `UNDO ALL 1105.bat`.
5. Bench (game free, owner not playing, one at a time): 2-seat online bench on DD02 as the DM02 benches of 1106d/e: both seats in round 2, 0 faults / asserts, items
   from several batches (35, 62, 49) made on host and client; then Arcade DD05 and DD09; then install the rest in one go.
6. Phase 2 (optional): Scenes F01-F09 with src_root = `Scenes\Locations`, plain zip only, no ini, `.before-pd2guns1106s` kept on D:. These ARE stock files: allowed
   only with backup and undo, as the buttons / pics layers did; never KL_PortBackup. Only matters for runs without the hook redirect.

## 5. Risks
* 200-270 MB zips on a nearly full C: (1.7 GB free): installer must check free space, copy in before rename out, retry.
* DD10 is slot F07 (same id as DD07): exclude (c9 owns its buttons / pics step E).
* A 19-spec bake from the unmodified base is new ground (DM maps got it in five steps); hosts of items 47 and 63 sit at different root ids per map. verify's
  `others_unchanged` and `old_chunks_diff` catch a mismatch. Fits are frozen, no re-fit drift.
* GUESS items stay GUESS and have not been seen in hands on any map: pose of rifle-as-MG items 42-44, GL40 far copy 190 -> 191, Deagle detail 31.
* Online: a peer on the old zip sees stock guns, and a KLGuns.ini whose Entries differs from the zip is ignored (looks fall back to what was built in), so install all
  9 DD maps together and keep the inis in step.
* A zombie kl2.exe blocks the installers' run check: `--skip-run-check` (+ `--root`) as in the notes.

## 6. Staged 2026-11-06 (layer 1106s, NOT installed, offline)
`python tools/pd2_guns_layer.py build --layer 1106s` then `verify --layer 1106s`: `LAYER RESULT: PASS` (plain + bots, 9 maps, 19 guns each, 39 other Ground nodes unchanged,
old_chunks_diff 0). Stage `D:\kl_stage\pd2guns_1106s` (log `D:\kl_stage\build1106s.log`, `verify1106s.log`), off-drive backup folder `D:\kl_stage\pd2guns_1106s_backup`
(filled by install.py). Each map folder holds `F0n_Main.zip`, `F0n_Main.bots.zip`, `KLGuns.ini` only: no `*.bots.base.md5`, KLJoin.ini or Int16Ok.txt exist on DD01-09.
Chunks before -> after (every map +203): DD01 46115 -> 46318, DD02 39929 -> 40132, DD03 48087 -> 48290, DD04 51572 -> 51775, DD05 38872 -> 39075, DD06 52683 -> 52886,
DD07 56374 -> 56577, DD08 48265 -> 48468, DD09 51726 -> 51929; KLGuns.ini Entries = the new count. Fits = union of the 1106c / d / e fits.json (all 19 keys).
Dry install: 9 maps, 0 skipped; backup drive needs 4114 MB. NOTE: C: net grows by +76..+96 MB a map (about +750 MB for the 9), not ~0 as section 3 assumed
(the new zip is larger than the old one; the old one goes to D:). Host root ids differ per map (DD02 SG417 host 13812, DD05 2556), the templates and fits are the same.
Body detail bytes of SG417 / G36 / RPK / MK17 / RPK40 / RPK42 / RPK43 = 15 (build_level default for hosts with the hidden detail-16 part; verify reads the real byte: PASS).
Still to do: 2-seat bench on DD02 (items 35, 62, 49), Arcade DD05 / DD09, then install all 9 together (inis follow in step).
