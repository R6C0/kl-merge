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

## 3. Remote shot loudness: traced statically 2026-10-28, NOTHING implemented (slot and volume are the same online and in Arcade)
Static trace of kl2.exe (no game run). The weapon-event sound routine is 0x503650 (this = weapon item, arg1 = shooter/owner, arg2 = a flag; called from the
fire path 0x4cca68 and the weapon-state code 0x8c567b / 0x8c56ea / 0x8c5837; NOT in any vtable, so the data-only hook has no seat on it). It plays through
0x9025b0 (arg1 = #def slot, arg2 = "2D"), which reads the template's #def ref at `[weapon+0xc4]+0x7c` (0x9025e1, helper 0x430540).
Deciding branches in 0x503650:
- 0x5036c2..0x5036ce: shooter's class mask `& [0x1548c80] == [0x1548c7c]` = **ZFFPlayer** (the same mask re/balance.md 0x61aa0b uses). Pass -> slot 4 (shot_player,
  0x50375b / 0x503769, default state 0; states 1..6 of `[owner+0xd70]` give slots 12,11,10,9,0,3 via the table at 0x5039a4, only when `[[owner+0x54]+0x42] != 0`).
  Fail, or owner null, or the slot-4 play gave no handle -> slot 1 (shot_npc, 0x503785).
- 0x5036d4..0x503708: arg2 ("2D") = 1 when the owner is the gamedata local pawn (`0x660b00(0)` on [0xdd265c], i.e. [gd+0x898] -> [gd+0x828+4*i]), or when
  `[sm+0x5c]==2` (0x87c980) with role `[sm+0x54]<=1` (0x6db900), else 0. In mode 4 (Arcade / FA) only the local pawn is 2D.
- 0x9025b0: arg2 = 1 -> 0x90262f: sound dll +0xd0, then +0x128 with a fixed head-relative position (0,0,[0xb5c050]) = non-positional, full volume.
  arg2 = 0 -> 0x9026c7: shooter's position (shooter vfunc +0x254), emitter ctx 0x4a30e0 / 0x598460, played by 0x467e00 = POSITIONAL 3D (distance falloff),
  with a cap of 50 plays per game-time tick ([0x153558c] vs [0x1535590], 0x9026ea).
Answer per case (certainty):
- (a) local human (Arcade or online): slot 4 shot_player, 2D (flag 1). CERTAIN for the branch, the site being the shot play is MEDIUM (callers 0x4cca68 is a fire routine; not traced to the action's name).
- (b) remote human seat online: a remote seat is a ZFFPlayer replica (re/netsmooth_solo.md), so slot 4 shot_player, same group volume 0.70, but flag 0 = positional 3D
  with distance falloff and the 50/tick cap. Slot and volume are NOT different from (a); only 2D vs 3D is. CERTAIN for the code, HIGH for the replica class.
- (c) Arcade AI (cops, guards): not a ZFFPlayer, so slot 1 shot_npc (group 0.35), 3D. CERTAIN for the code.
- (d) Arcade bot heister: an actor, not a ZFFPlayer: slot 1 shot_npc, 3D. Same as (c). (Online bots: the same.)
So online and Arcade do NOT differ in slot or volume for a human's shot; a remote human is louder (0.70) than an Arcade bot (0.35) but positional. If a remote MP45
"sounds quieter than in Arcade" the likely cause is the 3D falloff versus the local pawn's 2D, not the slot. Other candidates, all unmeasured: (1) the sound dll's
own min/max distance for the group (not in kl2.exe: sound dll vtable +0x128 / 0x467e00); (2) the 50-plays-per-tick cap in a 9-player fight (0x9026ea); (3) after
death or a van escape [gd+0x898] follows a peer: that peer's shot becomes 2D and the own shot 3D (klhook.c klh_slot_player_mine); (4) which pawn `0x660b00(0)` returns on a client.
Not implemented: no toggle, because slot and volume do not differ and a 2D-for-remote change needs a code detour (0x503650 / 0x9025b0 are direct-call only; the hook
writes data only). A future option if the owner wants remote shots as loud as his own: wrap the sound dll's vtable +0x128 / 0x12c through a private vtable copy
(klsync.c `ksp_vt` technique), filter on the return address inside 0x9025b0 (0x90268b 2D, 0x90272f 3D) and call the 2D form; GUESS, needs the dll's argument layout.
Bench to decide (live, 2 seats, MP45 on both): hook-free listen test first: stand 3 m from the remote shooter, then have him stand 20 m away, and compare with
the local shot; if 3 m sounds as loud as local, falloff is the cause and the 2D wrapper above is the fix. Ini: nothing new to set.
