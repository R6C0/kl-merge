# Gun shelf UI + remote shot loudness (T5, 2026-10-28, static, nothing run live)

## 1. Online gun shelf (rows 13/16/32/35)
Problem: baked maps name HK69 / TYPE 81 / REM 700 / MINIMI on rows 13/16/32/35; online klshop_tick returns at `kl_online()`, so the stock carrier gun
(TOQ Model 18 / Buqiang 300BP / Buqiang 800 Scoped / Buqiang 900 Scoped) is handed over: text/gun mismatch.
DONE: `[Shop] OnlineSwapText=0|1` (kllocname.c): online, the NAME key of those four rows answers the stock gun name. GUESS: the shop name reaches the LOC
slot-0 lookup with a key ending `WeaponShop/Weapon<row>` (klshoppage.c reads the same key at 0x490730). The Desc line and the picture stay baked (not changed).
NOT DONE: `[Shop] OnlineSwap` (the real pool swap online). Needs: objects made at the same point on every peer in row order (chain onto kllb_early_cb, which
kspg_early_patch owns as a single pointer; klshoppage.c is not editable here), gun+0x13c != 0 guard (kspg_netok), a host/client pair-list exchange over SHOPG.
kspg_early_body also skips rows [Shop] Swap occupies, so page II does not make them. Unbenchable offline; a design for a later step, not coded.
Bench for OnlineSwapText: 2 seats online on a baked map, open the Buy Weapons list: rows 13/16/32/35 say the stock names, buying hands the same gun; Arcade unchanged.

## 2. Unbaked maps DM07 / DD10
Tool: tools/kl_shop_swap.py (bake/stage). New `--no-ini` / `write_ini=False` bakes TEX+LOC only and leaves KLGuns.ini alone (the default Swap in KLHook.ini is used).
Staged: C:\kl_build_1024\gunui_1028\ (INSTALL_gunui_1028.bat, UNDO_gunui_1028.bat, -DryRun both run; the live file is renamed `.before-shopswap` in place,
never KL_PortBackup). DM07 F06_Main.zip bdb7728d..., DD10 F07_Main.zip 74c3d9dc...; 9 members each (TEX + 8 LOC). Install refuses while kl2.exe runs.

## 3. Remote shot loudness: NOT CERTAIN, nothing implemented
Known: the `.SND` groups are shot_npc 0.35 / shot_player 0.70, identical offline and online; the weapon `#def` has slot 1 (shot_npc, "heard from others") and
slot 4 (shot_player); which slot plays when was never traced in the exe (re/map_guns.md section 9). No runtime volume code exists; whether the engine copies the
group volume into its mixer at load is unverified (re/gun_sounds.md section 4). So both "a remote human uses the npc set" and "a hook can change it" are unproven.
Bench to decide (one 2-seat online round, a gun with distinct sets): log which #def slot index the sound system is asked for (hook the play call from the
weapon fire routine) for the local shot and for the remote seat's shot; then write the group volume (+0x24/+0x30 per gun_sounds.md) after slot 35 0x402000
and compare by ear. Only if the remote seat asks slot 1 would `[Sound] RemoteShotVolume` be added (Arcade untouched).
