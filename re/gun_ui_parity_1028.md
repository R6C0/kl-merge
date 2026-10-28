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

## C. Needs game-folder data (owner step, not hook code)

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
