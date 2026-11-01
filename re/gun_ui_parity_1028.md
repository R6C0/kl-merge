# Gun UI / sound parity plan (online = Arcade), 2026-10-28

Merged from three research passes (names/pictures, sound, coverage). Hook-only, SHIP-safe, data-tick logic only (no .text patch),
each behind an ini key default 0 "(recommended off)" plus a tools/kl_mod_options.py row. Include order verified: klshop.c (klhook.c:788)
comes before kllocname.c (:806), so kllocname.c may call a klshop.c getter.

## A. Code to build now (ranked)

1. **[Shop] OnlineSwapText=2, "name follows the pool"** (kllocname.c + new getter `kls_row_ours(row)` in klshop.c).
   Today OnlineSwapText=1 answers the STOCK carrier name even when OnlineSwap=1 hands over HK69/TYPE 81/REM 700/MINIMI (kllocname.c:203-209,
   no kls.osw test; init :288). Mode 2: if the pool hands over our gun (kls.applied[k]==1 for kls.row[k]==row) answer the swapped name from a 4-entry
   table {52 HK69, 33 TYPE 81, 49 REM 700, 47 MINIMI} (same words as klhud_weapon.c klwd_names), else the carrier's name. Offline too under =2
   (drops the kl_online() gate), so unbaked stock slots / DM07 / DD10 stop showing the carrier's name in Arcade. Pass through orig text if it
   already names the swapped gun (baked map). Mode 1 unchanged. Log the first 4 answers (row, ours/stock).
   Evidence: WK2 'osw: row 13: 8 object(s), 8 with gun+0x13c set ... ours are handed over' both seats; DM07 and DD10 and F01-F09 archives hold only 'TOQ'.
   GUESS carried: the name key ends 'WeaponShop/Weapon<row>' (kllocname.c:199-202), never seen live (no 'names: OnlineSwapText:' line in any log).
   Also cover the ...Desc key with the same table (short stock-style description) under =2. Picture stays the carrier's on unbaked maps (hook cannot change it).
2. **OnlineSwap early-make armed without page II pairs** ([Shop] key OnlineSwapArm=1, kspg_init in klshoppage.c ~1150, tick :1357).
   With no KLShopPage.ini pairs kspg.on=0, so the kls_osw_early hook is never armed and OnlineSwap=1 is silently dead (SHOT2D logs: OnlineSwap=1, 'no pairs', no 'osw:' line).
   Keep kspg.on for the swap only, make page II code quietly return when kspg.have==0. Also log once online: 'osw: OnlineSwap=1 but early-make not armed (ShopPage Enable=%d pairs=%d)'.
   Hits benches and any Nexus/friend install without the file; the live install has the file.
3. **Visible logging, default-on only under a log key** ([Shop] OnlineSwapLog=1): in kls_osw_tick log 'osw: map <slot/folder>, handed item N to seat S'
   and 'row stays stock' per map, so benches can grep a per-map matrix (today only DM07 has ever shown it).
4. **[Sound] RemoteShot2DLogAny=1** (log-only, klshot2d.c slot-74 wrapper): for any 3D slot-4 play with sp[0x88]==0x503772 and sp[0x8c]==4 log the caller word
   sp[0xa0] and shooter (first 10 distinct); plus log klss_n_fire/n_remote every 30 s. Needed because the gate (caller 0x4cca6d) is unverified for REMOTE
   replicas and a different caller is silent today (klshot2d.c:166-171). If the first live shot shows another caller, widen KLSS_FIRE_RET to a small allow-list (next build).
5. **[Sound] LogShotDef=1** (read-only): on the first 3 own shots per weapon read [weapon+0xc4]+0x7c and log the sound def name, so a bench proves which def
   each gun/map uses online vs Arcade.
6. **OnlineSwapText=1 fallback fix** (only if #1 is rejected): skip the override when kls.osw==1 for an active row. Superseded by #1; do not build both.

## B. Needs a live bench first (bench recipe, not code)

- **RemoteShot2D is unproven**: SHOT2D died at 'FABuyWeaponsNewWeapon did not come up' before any shot; only 'vtable route ... slot 74' lines exist, zero 'played 2D'.
  Recipe: TEST dll, RemoteShot2D=2 (dry) then 1, no shop step (start MP45 = item 1 row 7), both seats shoot at 3 m and 20 m; pass = 'DRY ... would play 2D' or 'played 2D ... site V'.
  Use #4 logging. The route is map-independent, one proven map transfers.
- **OnlineSwap purchase never benched** (WK2 pressed F12 into the HIRE page; no buy). Recipe: stage KLShopPage.ini into solo/<TAG>/inst1+2, buy rows 13/16/32/35, log shop name,
  HUD name, held item, then fire each. Maps: DD04, DM01 (own [Shop] line, hash must equal 8ff822a6), DM09, DM11B, DD10 and unbaked DM07/F06. Compare Arcade.
- Per-map 'osw: ... row stays stock / has no template' outcome (carrier absent from a map's pool) is never observed beyond DM07.
- Remote reload / weapon-switch sounds: no evidence either way; log slot numbers of non-shot plays through the slot-74 wrapper first (extend #4), build nothing before.
- Optional NPC loudness ([Sound] NpcShotVol, patching the shot_npc group volume 0.35): a GUESS needing a locate step; bots are identical in Arcade and online, so NOT a parity gap. Dropped.
- After benches pass: flip live keys (OnlineSwap=1, OnlineSwapText=2, RemoteShot2D=1). Today none is in the live KLHook.ini, so online=Arcade for these is inactive everywhere.

## C. Needs game-folder data (owner step, not hook code) - gunui_1029 INSTALLED 11-01 ~02:10 (archives checked in section E); the baked shop picture is NOT yet confirmed in a shot (GUN13 open, its --d3shots caught only the lobby), so "DONE" is unconfirmed on screen. Text below is the 10-28 state

- Bake DM07 (F06) and DD10 (F07) shelf text/pictures: staged C:\kl_build_1024\gunui_1028\INSTALL_gunui_1028.bat. It touches only the plain F06/F07_Main.zip,
  but online uses F06/F07_Main.bots.zip (both unbaked, 'TOQ' only). Extend stage\shopswap.ps1 + manifest to the .bots.zip siblings and refresh the .bots.base.md5 first,
  else it fixes Arcade only. Hook route #1 gives names without any file change; pictures need the bake.
- DM07/DD10 lack HUD dial pictures 113/114 (Q27_DM07/DD10: 'hud: weapon: no dial'): run tools/kl_hud.py --look deadmen on plain + bots zips. Stock ammo panel meanwhile (consistent online/Arcade).
- Stock F01-F09 archives stay untouched by project rule.

## D. Dropped (duplicates / refuted / not parity)

- MP45 icon/name/sound divergence: REFUTED (item 1 row 7 is not a swap row; pic 58 'SW MP45'; Desert Eagle records, same banks). Only 3D-vs-2D remote shot, covered by RemoteShot2D.
- Sound banks/volumes differ per map: REFUTED (same 61 shot records, gunraw/fxraw on all 42 banks; DM07/DD10 unbaked concerns the shelf only).
- Bot/cop shot loudness gap: not a gap (slot 1 at 0.35 in both modes).
- [Guns] Start/Set online: needs the variant-byte write blocked by OnlineSafe; no SHIP-safe hook fix. Document as Arcade-only in the mod options.
- Dropped-gun pickup prompt: new feature, not parity.
- Weapon dial on unbaked maps: bake only (section C).

## E. Matrix of the 21 maps, 2026-11-01 (job T5, `python tools/kl_gunui_matrix.py --md ...`, read-only)

Read from the installed `KLExpansion\Maps\<map>\F0x_Main.zip` (Arcade) and `.bots.zip` (online) plus the GUN* bench logs. text = rows 13/16/32/35
of the English .LOC name the swapped gun (HK69 / TYPE 81 / REM 700 / MINIMI); card = big+small shop pictures differ from the stock pixels (md5 of
mip 0, measured on the untouched Scenes\Locations\F02..F09, identical in all eight); hud = textures 113/114 (the dial) present. The number after
"baked" is a bake-generation fingerprint (1dbd01 = common bake; ff017d = DD10 and DM07, the 1029 bake; 8f69a4 = DM01, its row-16 card differs, it
has its own `[Shop] Swap=13:52,16:33,32:49,35:47` line in KLGuns.ini, same pairs as the default).

RESULT: this is a STATIC ARCHIVE STATE, not a live result. All 21 maps, both archives, read as baked on text, cards and the dial pictures
(113/114 present). Only 4 of the 21 maps (DD04, DM02, DM07, DD10) have any bench evidence, and only DM02/DD04 (osw lines) and DM07 (shop-text
and picture lines, pre-bake) say anything about the shelf; the dial is an archive check only (no log line proves it drew: "now renders through
the private vtable" is just the element's vtable wrap, and "the dial stands again" / "no dial" are not what GUN13-15 print). The shelf picture
after the 1029 bake is not yet confirmed in a shot.
Caveat: the DD01-DD09 rows are the KLExpansion copies. The untouched stock slots `Scenes\Locations\F01..F09` (project rule: never edited) still hold
the stock TOQ text/cards; for a stock-slot FA map (not through KLExpansion) `OnlineSwapText=2` is only a no-harm safety net (it passes a baked
name through and swaps an unbaked one), and the picture stays the carrier's (no bake possible there; `OnlineSwapPic=1` gives a look-alike).

Bench evidence column: logs older than the gunui_1029 install (11-01 ~02:10) on the rebaked maps DM07 and DD10 show the UNBAKED state and are
listed as STALE (DM07 GUN7-GUN12b), never mixed with the current status. GUN13-15 (DM07, DD10; post-bake) ran without OnlineSwapLog, so they
add no shelf evidence. "pool STOCK at the first report, flipped to OURS" is the client seat: it logs `STOCK handed over`, then about a second
later `OURS (flipped after the first report, state 0x16)` for all four rows (GUN1-5, 7, 10-12 inst2); the host seat logs OURS at once.

Static facts only for maps with "none" in the evidence column: the archives are right, but no bench has looked at them live.

| # | map | slot | swap rows | text plain | text bots | card plain | card bots | hud plain | hud bots | bench evidence | status |
|---|-----|------|-----------|------------|-----------|------------|-----------|-----------|----------|----------------|--------|
| 1 | DD01 | F01 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 2 | DD02 | F02 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 3 | DD03 | F03 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 4 | DD04 | F04 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | GUN1: pool STOCK at the first report, flipped to OURS; GUN2: pool STOCK at the first report, flipped to OURS; GUN3: pool STOCK at the first report, flipped to OURS | OK |
| 5 | DD05 | F05 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 6 | DD06 | F06 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 7 | DD07 | F07 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 8 | DD08 | F08 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 9 | DD09 | F09 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 10 | DD10 | F07 | 13:52,16:33,32:49,35:47 | baked | baked | baked ff017d | baked ff017d | dial | dial | none | OK |
| 11 | DM01 | F01 | 13:52,16:33,32:49,35:47 | baked | baked | baked 8f69a4 | baked 8f69a4 | dial | dial | none | OK |
| 12 | DM01B | F03 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 13 | DM02 | F02 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | GUN4: pool STOCK at the first report, flipped to OURS; GUN5: pool STOCK at the first report, flipped to OURS; GUN6: shop text baked, pool OURS | OK |
| 14 | DM03 | F03 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 15 | DM03A | F07 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 16 | DM05A | F01 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 17 | DM06 | F04 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 18 | DM06B | F02 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 19 | DM07 | F06 | 13:52,16:33,32:49,35:47 | baked | baked | baked ff017d | baked ff017d | dial | dial | STALE (before the bake, unbaked state, not current): GUN7, GUN8, GUN9, GUN10, GUN11, GUN12, GUN12b | OK |
| 20 | DM09 | F06 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |
| 21 | DM11B | F04 | 13:52,16:33,32:49,35:47 | baked | baked | baked 1dbd01 | baked 1dbd01 | dial | dial | none | OK |

### Ship proposal (per [Shop] key; NOT for NEXT_SHIP.txt)

| key | maps | value | bench tag that proved it |
|-----|------|-------|--------------------------|
| Enable, Swap=13:52,16:33,32:49,35:47 | all 21 | 1 / the default line | GUN5, GUN6 (DM02), GUN12b (DM07): 'osw: set 4 pair(s), hash 8ff822a6' |
| OnlineSwap=1 + OnlineSwapArm=1 | all 21 | 1 | GUN5, GUN6: 'OURS handed over' on rows 13/16/32/35 (host seat at once; the client seat reports STOCK first, then 'OURS (flipped after the first report, state 0x16)' about a second later); GUN12b (DM07) is pre-bake |
| OnlineSwapText=2 | all 21 as a no-harm safety net for the untouched stock Scenes\Locations slots (not a need on the baked KLExpansion maps) | 2 | GUN12b (DM07, PRE-BAKE, stale for the current archives): answered HK69 / Type 81 over 'TOQ Model 18'; GUN6 (DM02, baked): pass-through, 'stock text 0' |
| OnlineSwapPic | none (stay 0) | 0 | GUN12b: fired only on the unbaked DM07 (row 13); never on a baked map, and a look-alike is unwanted when the true card exists |
| HUD dial | all 21 (data, no key) | present | ARCHIVE CHECK ONLY (113/114 in every .TEX). Not proven live: 'now renders through the private vtable' only says the element's vtable was wrapped, not that the dial drew |

Not yet seen live (static OK only): DD01-03, DD05-09, DM01, DM01B, DM03, DM03A, DM05A, DM06, DM06B, DM09, DM11B.
Bench proposal: one two-seat pass per group with OnlineSwapLog=1 on a TEST dll, grep `oswlog:` (all four rows OURS), `shoptext:` and `hud: weapon:`:
(1) DD01/DD02/DD03 (one each), (2) DD05-DD09 (one of them is enough for the .bots archive family 1dbd01, then spot-check DD08), (3) DM01 (own
fingerprint 8f69a4 and own [Shop] line, hash must equal 8ff822a6), DM01B, DM03, DM03A, (4) DM05A, DM06, DM06B, DM09, DM11B. Fingerprint 1dbd01 is
shared by 18 maps, so a pass on three of them is strong, but each map has its own pool (carrier present or not), which only 'oswlog' shows.

Resolved from the matrix run: the 'pool OURS/STOCK' of GUN1-5 (DD04, DM02) is the client seat's first report (`STOCK handed over`, all four rows)
followed about a second later by `OURS (flipped after the first report, state 0x16)` (GUN5 inst2 22:44:04.826 -> 22:44:05.6). The earlier
"carrier absent from the pool" GUESS is contradicted by that log and dropped; the matrix regex now reads the flipped line. Not yet explained:
why the first report is STOCK (what changes by state 0x16); whether a purchase in that second would get the stock gun.
