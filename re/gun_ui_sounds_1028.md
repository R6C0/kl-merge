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

## 3. Remote shot loudness: traced statically 2026-10-28; IMPLEMENTED as [Sound] RemoteShot2D (default off, not yet run live)
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

### Implemented 2026-10-28 (wk-shot2d, klhook/klshot2d.c; static, NOT run live)
Keys: `[Sound] RemoteShot2D` 0 off (default) / 1 on / 2 dry (log only); `RemoteShot2DDist` cm (default 1500). ONLINE only: gated on `kl_online()` (klhook.c: role 2/3, or game type 4 with a non-Heist rules vtable; 0 in Arcade/story).
Correction to the trace: 0x503650's arg2 is NOT the 2D flag. The 2D byte is computed inside (0x5036d4..0x503708) and written over the callee's own arg1 slot ([esp+0x10]), then pushed to 0x9025b0, so an E8 detour on the callers cannot ask for 2D. Patched instead, inside 0x503650 (both only reached for a ZFFPlayer shooter), with E9 rel32 to naked stubs:
- site A 0x503764 `8b 4c 24 10 51` (mov ecx,[esp+0x10]; push ecx; then `push 4` = slot 4): stub re-runs the pair, sets cl=1 when forced.
- site B 0x50375b `b8 04 00 00 00` (mov eax,4; then push ebx(0); push eax): stub pushes 1 instead of ebx when forced.
Fire-path gate: the stub acts only when 0x503650's return address is 0x4cca6d (call at 0x4cca68, `e8 e3 6b 03 00`, re-verified at init). 0x8c567b / 0x8c56ea / 0x8c5837 follow `[owner+0xd70] = 5/4/6` stores (slots 0/9/3 via 0x5039a4), not shots: excluded (GUESS).
Decision: remote (shooter != [gd+0x828+4*(char)[gd+0x898]]) and 3D distance (scene node of [pl+4], fallback [pl+0x460]) to the local pawn <= Dist; under __try, any fault keeps the original flag; the local pawn is never changed.
Bench recipe (2 seats, MP45 on both; host KLHook.ini and join KLHook.ini, same lines): `[Sound]` `RemoteShot2D=1` `RemoteShot2DDist=1500` (first pass `RemoteShot2D=2` for a dry log). Proving log line (client or host, in KLHook.log): `shot2d: remote shooter xxxxxxxx site A at NNN cm: played 2D (dist 1500; ...)` (dry: `DRY ... would play 2D`); init line `shot2d: RemoteShot2D=1 ... site A 0x503764 patched, site B 0x50375b patched` (REFUSED = SHIP build or SessionSafe: use the TEST build). Listen: the remote shooter at 3 m should now be as loud as your own shot (2D, no panning); at 20 m (beyond 1500 cm) it must stay 3D, quieter and directional; compare with 0 on the same spots. If site A and B never log, the shot goes through a path not covered (then 3D falloff may not be the cause: see candidates 1..4 above).

### SHIP route (added 2026-10-28; static, NOT run live): TEST path = code patch, SHIP path = sound-system vtable
The SHIP policy refuses code writes, so the two E9 patches above only exist in the TEST build. Same keys, same decision (klss_decide), second route that writes no code byte:
- The sound system is NOT in a DLL: heap object of the exe's own class at `[[0xdd2640]+0xb00]` (size 0xb124, `0x762f70` -> ctor `0x4ff8c0`), vtable `0xb9ae14` (.rdata, read-only). Both branches of 0x9025b0 end in its slot 74 (+0x128 = 0x592950, `ret 0x10`, forwards to slot 73 +0x124). The earlier "3D = +0x12c" was wrong: 0x467e00 calls +0x128 (0x467eb6, returns 0x467eb8); +0x12c (0x589670) is on neither path.
- Arg layout of +0x128 (thiscall, ecx = sound system): 2D (call 0x90268b, ret 0x90268d): a1 = head ctx (slot 52 +0xd0 = 0x571300, `mov eax,[ecx+0x6760]`), a2 = sound handle (ebp), a3 = 36-byte block filled by 0x7f07a0 (floats 0,0,0, 0,0,0, 1,0,0), a4 = &(0, 0, [0xb5c050]). 3D (0x467e00 from 0x90272f): a1 = emitter ctx (0x4a30e0/0x598460), a2 = same ebp, a3 = block from 0x569950, a4 = world position. 2D then runs 0x659370(handle): `[h+0x84] &= ~4; byte [h+0x145] = 1`.
- Wrapped entry: private copy of the vtable (vt[-1] + 160 slots), slot 74 -> klss_vt_stub (original target 0x592950), vptr of the current object re-pointed from klss_tick (every 500 ms, only if the vptr is the stock 0xb9ae14; the object is rebuilt per session). Stub: pushad/pushfd, C decision, popfd/popad, then `jmp` to 0x592950 untouched, or (converted) a1/a3/a4 rewritten in place to the 2D branch's values, call original, replay the post step, `ret 0x10`.
- Shot recognition (stack walk at entry, byte offsets from esp): [0]==0x467eb8, [0x2c]==0x902734 (0x467e00 called by 0x9025b0 3D branch), [0x88]==0x503772 (0x9025b0 called from 0x503650; npc path returns 0x50378a and is excluded), [0x8c]==4 (slot 4), low byte [0x90]==0 (3D), [0xa0]==0x4cca6d (fire path), shooter=[0x94] cross-checked with [0x50], weapon=[0x98]==[0x54]. A fire-path slot-4 3D play whose stack does not match logs `vtable route: slot-4 3D play from the fire path but the stack does not match ...` (first 5) and is left alone.
- Key `RemoteShot2DRoute` (diagnostic): 0 auto = code patch, and the vtable route when both sites are refused (SHIP); 1 code only; 2 vtable only (use 2 in the TEST build to hear the SHIP route).
- Log lines: init `shot2d: ... VTABLE route ready`; per object `shot2d: vtable route: sound system XXXXXXXX now on the private vtable`; proof `shot2d: remote shooter XXXXXXXX site V at NNN cm: played 2D (...)` (site V = vtable route; A/B = code route).
- Bench: same as above with `RemoteShot2DRoute=2` on the TEST build first (listen), then the SHIP build with route 0.
- GUESSes: the stack layout (never walked live); that the 3D branch's later 0x867da0 step does not undo 2D-ness; that replaying the 2D post step is right for a handle from the 3D call; that no code compares the sound system's vptr (only the ctor 0x4ff8d6 and one more store write 0xb9ae14; no compares found by byte search).
