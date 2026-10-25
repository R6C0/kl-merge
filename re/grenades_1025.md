# Grenades step 1 (2026-10-25): data side for DM01, staged, NOT installed, NOT run

Owner ask: "look into grenades in dead men and implementing them here ... adding them onto your character like dead men".
Earlier research: re/grenades.md (sections 1-13). Labels: PROVEN = seen in files/exe or checked by the offline gates, GUESS = not verified.

## 1. Result

- Stage: `C:/kl_build_1024/grenade_1025a` (INSTALL DM01 grenade.bat, UNDO DM01 grenade.bat, grenade.ps1, grenade.json, six member files).
- Builder: `tools/kl_grenade_1025.py` (pinned on the live DM01 zip md5 `4d520614...`, the vans pass). Rehearsed on a scratch copy.
- New DM01 zip md5 `1bcac96b31afcfd10fc9749a626c0973` (deterministic: a second install gave the same md5). Backup tag `.before-1025grenade`.
- Only DM01 is touched. The 9 stock FA maps, KL_PortBackup, KLHook.ini and the hook are not.

## 2. Where the pieces are (PROVEN, from the live DM01 zip)

- DM01 is a Dog Days systems build (`AllLevels/mainsceneincludes_multiplayer.zip\AllLevels/equipment.zip\...`). It holds Dog Days' 5 grenade
  item templates (Flashbang, Smoke, Fragmentation, TearGas, Incendiary) and their Ammo templates, 61 ZFFItemTemplateWeapon, 54 Ammo. It holds NO
  Dead Men `Projectile\Grenade_*` group (those live only in Dead Men's own M01_FA_A systems subtree, which the graft drops).
- `Ammo\Grenade_Fragmentation` (node 9337 in the vans build), field 24 (the projectile ref) is EMPTY. Same in every DD FA map. RPG_7V is the
  only template that names a projectile (`Projectile\Projectiles_01\Rocket_RPG7`).
- `Weapon\Grenade_Fragmentation` (ZFFItemTemplateWeapon): WT_GRENADE, eOODThrow, IH_ONEHANDED, own `Ground` child. The inventory binding exists
  already (Grenade_Frag, kind 0 = does not use a gun slot).
- DD has no pickup of any grenade in FA. Pickups elsewhere: ZFFItemWeapon in L03/L04/L05/L07/L11 (single node + `Action` controller
  `['_Pickup',0,'AT_PICKUP','','',200,0,1,'','','']`, fields: template ref (ZItem[0]), 0, count (ZItemWeapon[0]), `eBOTH_PLAYERS`). Dead Men
  M03_A has the same shape with `Weapon\Grenade_Fragmentation`, count 1.
- Stock pickups are top-level entities under ROOT and are in NO .oct room tree (checked L03, L04, L05).
- Heister spawns: DM01 has 8 START spawn points (`SpawnPoint!SpawnPoint_Start_01..08`) around x 1400-2100, z 30240-30900, y 75.

## 3. What the builder changes (kl_grenade_1025.py)

1. DD assets are reused, no Dead Men asset is imported: the Ammo projectile slot names DD's `Projectile\Projectiles_01\Rocket_Flare`;
   `kl_grenade.patch_level(n_actors=0)` turns that node into the frag round (fuse 3.3, eGRENADE_FRAG, Explode with Dead Men's frag numbers
   550/200/1000/350 and the DD RPG effect + sound as stand-ins, ShakeCamera from RPG_7). Side effect: `Ammo\Launcher_HK69A1_Flare` shares the node.
2. Three ZFFItemWeapon nodes `Special!Pickups!Grenade_Frag_01..03`, cloned from DD's L05 `TEMP_GUN_DESERT`, template = `Weapon\Grenade_Fragmentation`,
   count 1, 3 m in front of START_02/04/06 (positions about (2017,88,30606), (1737,85,30550), (1665,85,30280)).
3. Entities were added, so slot ids moved (16342 of them); .gms .buf .oct .rmi .rmc are rewritten and the .prp gains 3 nodes. The .prm, sound,
   .ANM, .HVK, .sgd are the live ones byte for byte.

## 4. Proven offline vs guessed

PROVEN offline (rehearsal, all passed): live .prp re-serialises byte for byte; new .prp round-trips; no new misfit (the 2 VehicleExitBehaviourRout
misfits are in the live map already); room-set check identical before/after the renumbering; .oct records unmoved; kl_scene.check clean; seal finds
0 strays; the patched zip loads again (16543 nodes), flare controllers = Ballistic + Explode + ShakeCamera, 3 pickups whose template ref resolves
to exactly one node; dry run, install, undo (byte identical), second install (same md5), "already installed", undo twice, changed-live refused.

GUESS (needs a live run; the code carries GUESS comments):
- that a Dead Men style pickup of a WT_GRENADE template works in Dog Days FA (the pickup path 0x5ee220 is DM; the DD equivalent was not read);
- ZItemWeapon[0] is the count (donor guns show 90 / 20 / 1; grenades in DM use 1);
- the offset (300 forward, +10 up) puts the item on the floor, not in a wall or air; a pickup with no room tree may be fine (stock is the same);
- the frag stand-ins (RPG effect/sound, shared Rocket_Flare node, Explode field 14/16 swap per kl_grenade.py section 10) behave and do not hurt friendlies wrongly;
- that picking up gives an inventory grenade at all: DD has no HUD count (re/hud_weapon.md) and the throw chain below needs the hook.

## 5. What is still missing: the player cannot THROW (hook, e8's area; nothing edited here)

Chain (PROVEN in exe reading, re/grenades.md 7 and 13): HoldGrenade key -> setter 0x4aa410 in kl2.exe -> bit 0x40 of `[player+0xb90]` -> action
word `[player+0x818]` bit 0x800 (0x544780) -> ZFFActionThrow (action id 0x11) -> projectile from the Ammo slot. DM's setter SETS bit 0x40, DD's
0x4aa410 CLEARS it, so HoldGrenade is dead in DD regardless of data. Proposal for `klgrenade.c` (after Probe=0 has logged the real values on a
pickup, commit 411ad3ed1):
1. Option `[Grenade] Enable=1` in the mod options as "Grenades (recommended on)"; default per the owner's rule, off until proven.
2. When the key is down and the player holds a grenade in the inventory (kind 0 slot, count > 0), set bit 0x40 of `[P+0xb90]` (and 0x800 of
   `[P+0x818]` if the action word is not rebuilt from it), once per press; decrement the count on `eLAST_GRENADE_THROWN`/the throw start.
3. Give-on-spawn option (`GiveFrag=N`): call the equip routine (kl2 analog of DM 0x5f8d80) with `Weapon\Grenade_Fragmentation`, so grenades are
   "on your character like Dead Men" without a pickup. The pickups in this stage are the data-only way to get one into the inventory first.
4. The probe must first answer: after walking over a pickup, does `[P+0x818]`/the inventory kinds show a kind-0 entry?

## 6. Test plan (live run, when the game is free)

1. `INSTALL DM01 grenade.bat` (kl2.exe must be closed). Launch DM01 (F01 slot, autotest) with `[Grenade] Probe=1` if the hook is current.
2. PASS A, load: clean exit of the 120 s autotest (`python tools/kl_autotest.py`), no assert. FAIL -> triage, then UNDO.
3. PASS B, pickup: walk onto each of the three items at the start row. Expect the "You picked up a grenade" message; log the inventory kinds.
4. PASS C, throw (needs the hook step above): throw one; expect fuse about 3.3 s, a blast with shake, damage near 5.5 m/2 m radii as per the
   numbers (check against RPG).
5. Regression: Last Call or any stock FA map must be untouched (the data change is DM01-only; run one stock map for a clean exit).
6. Undo: `UNDO DM01 grenade.bat` restores the 4d520614 zip byte for byte.

Not done here: police throws (route steps, kl_grenade.py section 12, a later job), smoke/gas/incendiary/flashbang (need effect pools), Dead Men's real
frag sounds (kl_snd.merge), the other KLExpansion maps (DM01 only; the builder is pinned on one zip).
