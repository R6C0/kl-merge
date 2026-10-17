# Grenades: Dead Men grenades in Dog Days (owner item 19, 2026-10-17)

Labels: READ = read from exe strings / schema json / code; MEASURED = checked on real level files with the
tools; GUESS = not verified. Offline research only; nothing was run in the game, no game file was edited.

## Summary

Dog Days (DD) kept the grenade ITEMS, the throw ACTIONS, the throw ANIMATIONS, the AI behaviour and the
network messages. It removed the grenade PROJECTILE groups (the Ammo template's projectile slot is empty)
and the grenade effect pools and sounds. So the job is: put Dead Men's (DM) `Projectile\Grenade_*` groups
into the DD systems subtree, repoint effects and sounds, fill the Ammo slot, and give the player a way to
hold one. No animation port is needed for the throw itself (MEASURED for the 18 generic clips; the Dodge_* clips are NOT CHECKED).

## 1. Item / weapon templates

- MEASURED: all nine DD FA levels (F01-F09, via `mainsceneincludes_multiplayer.zip`) carry 5
  ZFFItemTemplateWeapon with WT_GRENADE (Flashbang, Smoke, Fragmentation, TearGas, Incendiary), each with a
  Ground child and an InventoryBinding, plus 5 matching ZFFItemTemplateAmmo. DD story levels L00-L11 have
  none and use no WT_GRENADE.
- MEASURED: weapon templates are nearly identical in DD and DM (eOODThrow, damages 100/500/1500,
  ItemTemplateWeapon Ground ref). Weapon links to its Ammo template by ref (ItemTemplateWeapon[3]).
- MEASURED: the projectile group is referenced from the Ammo template: DM Ammo[7] =
  `AllLevels/equipment.zip\Projectile\Grenade_Fragmentation` (also _Smoke, _TearGas, _Incendiary,
  _HK69_TearGas, _HK69_Frag). DD Ammo[9] is EMPTY for Frag and Smoke; RPG_7V has
  `Projectile\Projectiles_01\Rocket_RPG7`. DD's `Projectile` group holds only Rocket_RPG7, _Hind, Rocket_Flare
  and bullet projectiles (F07).
- READ: InventoryBinding [1,4,4,'eFF2ItemGrenade_Frag','eFF2ItemTypeGrenade',0,'Grenade_Frag']. DD item enum
  (tools/dd_enums.json): 55 Grenade_Smoke, 56 Grenade_Gas, 57 Grenade_Frag, 58 Grenade_Incendiary,
  59 Grenade_FlashBang (new in DD), 52-54 GrenadeLauncher variants. Each item may be bound once per level
  (dup = assert), so a grafted template must REUSE the DD template, never add a second binding.
- READ: DM's systems subtree is dropped by the graft, so no DM item enum reaches a build (convert_audit.md).
  Item renames are exact (Frag, Gas, Incendiary, Smoke, ...).

## 2. Projectile and explosion objects

- MEASURED (M01_FA_A): each DM projectile is a ZGROUP + ZLNKOBJ `Ground` child with controllers:
  - Grenade_Fragmentation: Explode [550.0,200.0,1000.0,350.0,0,'EXPLODE_Explode_Impact',
    'Effects/BulletImpacts.zip\Grenade\FX_Grenade_Default_01',0.0,0,0,<sound>,80.0,1,0,0],
    ShakeCamera [0.5,'EXPLODE_Explode_Impact',0,1500.0], FFHavokProjectileBallistic
    [0,3.3,1,<sound>,0,0,'eGRENADE_FRAG'].
  - Grenade_Smoke: FFHavokProjectileBallistic (...3.0,0,...,'eGRENADE_SMOKE') + SmokeEffects
    (FX_Grenade_Smoke_01, trail FX_Grenade_Smoke_SMOKE).
  - Grenade_TearGas: GasEffects (FX_Grenade_Teargas_01, trail FX_Grenade_Smoke_TEAR) + FFHavok.
  - Grenade_Incendiary: IncendiaryEffects (Thermite_Grenade_01 Group_Thermite_Bomb / Fire), ShakeCamera 4000,
    FFHavok.
- READ (kl2.json vs kaneandlynch.json): DD has all controllers. SmokeEffects 152 B, GasEffects 180,
  IncendiaryEffects 192, ShakeCamera 64. `Explode` 124 B in DD (18 props) vs 116 in DM (15): +3 fields.
  `FFHavokProjectileBallistic` 336 B in DD vs 320: both 7 props + enum, pair 1:1 (DD's Rocket_Flare
  value ['0','10.0','1',<snd>,'0','0','eGRENADE_SMOKE'] shows the same shape). Pairings for CExplode and
  ZItemTemplateAmmo are marked risk 'high' in re/pairings.md (ASSUMED).
- MEASURED: DD removed the AllocMany effect pools FX_Grenade_Default_01, Teargas_01, Smoke_01,
  Grenade_Trails and Thermite_Bomb/Fire. DD kept particle templates (Gren_TearGas_01-03,
  Template_Thermite_Grenade, Template_Flashbang_01 + Flashbang_Smoke_01, Grenade_Impact_Templates) and
  FX_Grenade_RPG_01 (re/retomoto_blast.md). GUESS: Frag can use FX_Grenade_RPG_01 as its effect; smoke / gas /
  fire need pools rebuilt from the kept templates or grafted from DM (effects graft is its own job).
- READ: DD's `Throwable` controller (ZThrowable, DD-only, 352 B, owner ZHavokRigidBody) is the pick-up-and-
  throw prop system (FireExtinguisher 170, GasCanister 79, AcetyleneTank 63, FuelCan 28, WokStove 7), using
  `/Special_moves/Throw_Canister_1H_2H/*`. MEASURED. It is NOT the grenade system.

## 3. Sounds

- MEASURED (Snd walk, offsets are byte offsets into the level .SND; sound refs in prp are such offsets):
  - DM M01_FA_A bank (grenades block, ~218000-224800): grenade_can loops/explode/ignite,
    incendiary_fire_loop/end, `fragmentation_explosion_01/02/03` (+ seqs `frag_01..03`),
    `shot_fragmentation_01`, `materials/object/grenade#objectproperty`, rpg_loop_01, rpg_explosion_01-03.
    (name() offsets in the Explode / FFHavok fields land ~48 bytes inside these records.)
  - DD F07 bank: only rpg_loop_01, rpg_explosion_01 (`weapons_kl2_final/grenades/all`),
    barrel_explosion_01_for_grenade, materials/object/grenade (407632) and grenade impact materials on
    concrete / soil / wood / grass / metal.
  - DD has no fragmentation_explosion, grenade_can, incendiary sounds.
- Plan options: (a) stand-in: point the Frag Explode sound at DD's rpg_explosion_01 or the barrel explosion
  (GUESS, needs no merge); (b) real: `kl_snd.merge()` with an offset map to bring DM's fragmentation_explosion_*
  into the DD bank (infrastructure exists, re/audio.md; waves come from DM's .WHD/.WAV, needs `graft_audio`).
- NOT CHECKED: pin pull, bounce, flashbang bang, throw-grunt voice lines. The grep for a pin / bounce
  sound in DM M01_FA_A found none by name; GUESS they are a generic impact material, not a grenade-specific
  sound.

## 4. Throw animations (what DD already has)

- MEASURED (kl_anm on DD F07, L05; DM M01_FA_A, M08_A): DD F07 has 211 grenade/throw slots. Generic
  `/Weapon_Handling/Throw_Grenade/` has the same 18 clips as DM: Stand_Overhand, Stand_Underhand,
  Crouch_Overhand, Crouch_Underhand, UB_Sidearm, UB_Underhand, Cover_Crouch, Cover_stand, Cover_Stand_Left,
  Aiming, Aiming_Left, Stand_Overhand_Rifle, Throw_Back_Granade_Low/High, Cover_Crouch_High(_Left).
  Per-weapon `/Weapon_Handling/<Weapon>/Throw_Grenade/{Cover_Crouch_High, Cover_Crouch, Cover_Stand,
  Stand_Overhand_Rifle, UB_Underhand}` exist for SMG / shotgun / MG / launcher folders, and
  `/Weapon_Handling/RPG_7V/Throw_Down_RPG_7V`.
- Sets that have them (F07): Thug, Dog, Swat_02, Lynch_NPC, Kane_NPC, Civilian, Kane, Lynch; L05 adds Busy.
  Exe format string: `/Weapon_Handling/%s/Throw_Grenade/%s` (READ).
- DM extras: `/Movement/Avoidance/Dodge_Stand_Grenade`, `Dodge_jump_Grenade`, `/_Test/Kick_Grenade`.
  NOT CHECKED whether DD has the Dodge_* clips (they are cosmetic).
- Conclusion (MEASURED): the user's idea (reuse DD's throwing animations) works as-is. kl_arms' FOLDER map just
  gives grenades no weapon folder, so Swat_02 shows 0 slots; the generic folder is what a grenade uses.
  `.ANM` must never be copied between games (header 0x50 vs 0x68).
- READ (exe): ZFFActionThrow, ZFFActionThrowBackGrenade, ZFFActionThrowObject, ZFFActionThrowWeapon,
  ZFFActionThrowHumanShield; `/Special_moves/Throw_Weapons_1H_2H/*`.

## 5. Does DD's exe still have the grenade machinery?  Yes (READ, strings in kl2.exe)

ZFFActionThrow, ZFFActionThrowBackGrenade, ZGrenadeAttackBehaviourRout, CPPScript::ZGrenadeAttackBehaviourScript,
ZGrenadeAttack, ZMiniThrowGrenadeTask, ZFireThrowWeaponTask, CExplodeMolotov, WT_GRENADE, WT_MOLOTOV,
eGRENADE_FRAG, eGRENADE_SMOKE, ePICKUP_GRENADE, eSWAP_GRENADE, eLAST_GRENADE_THROWN,
eTHROW_GRENADE_STANDING / CROUCHING, eTHROW_THROWABLE, YouPickedUpGrenade1/2, YouPickedUpSmokeGrenade1/2, UI
textures `UI_Weapon_01#Grenade_*` and `Crosshair_Add_01#GrenadeThrow`, objective texts about frag grenades and
throwing back enemy grenades. `GrenadeAttackBehaviourRout` is DD-only as a controller (ZGROUP, 92 B, 7 props);
4 in L10, 0 in FA (MEASURED; re/bots_dynamic.md).

## 6. Where grenades are placed / who holds them

- MEASURED: stock DD FA (F01-F09) has no ZFFItemWeapon pickups and no grenade pickups.
- MEASURED: DM places grenade pickups in M02_A (LynchSmokeGrenade, KaneGrenades1), M03_A (FragGrenade,
  FragGrenade_COOP_Only), M05_A, M08_A, M11_B (Grenades_01 ...), M13_A (Garden_FragGrenade). A pickup node is
  ZFFItemWeapon {template ref `...Weapon\Grenade_Fragmentation`, 0, 1, eBOTH_PLAYERS} + an Action controller.
  Explode controllers per DM level: 7-42.
- MEASURED: NPC grenades are ZFFActor fields [4] and [5] (re/combat.md). Only M09 in DM has them (7 police with
  Launcher_HK69A1_01TearGas, 3 with Grenade_TearGas secondary, mercs with frag / smoke / incendiary / gas).
  `kl_arms.arm(grenades=False)` empties them because no stock DD NPC has one.

## 7. Input and how the player gets one

- READ: both exes have `HoldGrenade` (keyboard G); DM also `TapCycleGrenade` (Q); DD exe has
  `StartWithGrenadeInHand` and `AnalogChargeGrenade`. From re/player_down.md: throw button = bit 0x40 of
  `[player+0xb90]` set by 0x4aa410; ZGameplayInput slot 7 is 0x5fbfa0, HoldGrenade is `[H+0x2d2]`; the player
  action word `[player+0x818]` gets bit 0x800 via 0x544780. NOT READ: where a throw starts and where the
  inventory decides the player has a grenade to throw.
- OPEN (GUESS): stock DD FA gives the player none; the earlier player-down analysis found "no grenade of his
  own". Whether the DD HUD draws a grenade count (hud_weapon.md says no) is unverified.
- READ: network `DDL_SThrowGrenadeData` (m_iWeaponRef u16, start pos int16[3], target int16[3], player idx
  int8) and RMCGrenadeSync / RMCThrowObject / RMCFireThrowWeapon (re/netcode.md). Peers address objects by
  16-bit scene refs, so a grafted projectile needs the identical build on every player.

## 8. Staged plan

- Stage A (NPC grenade, offline, small): `kl_arms.arm(grenades=True)` for a few NPCs with the stock DD
  templates, to exercise GrenadeAttackBehaviour + ZFFActionThrow with the existing animations. Without a
  projectile the throw has nothing to spawn: GUESS that the engine ignores it, but a crash is possible (null Ammo
  projectile ref, never tried), so it is NOT harmless; test on one actor in the F01 slot under the autotest.
- Stage B (projectile): clone DM `Projectile\Grenade_Fragmentation` (ZGROUP + Ground + 3 controllers) into the
  DD systems subtree with `kl_scene.graft`; convert Explode and FFHavok through `kl_convert.LEVEL_MAPS`
  (Explode +3 fields take the DD most-common value); repoint effect to FX_Grenade_RPG_01 and sound to DD's
  rpg_explosion_01 (stand-ins, no merge); write the group ref into the DD Frag Ammo[9]. verify_levels must stay
  `problems: 0`; check the one-binding-per-item rule is untouched (no new InventoryBinding).
- Stage C (player access): (1) placed pickups: ZFFItemWeapon nodes (DM M03_A shape) in grafted maps, referencing
  the DD grenade template; (2) or a KLHook-given grenade through the HoldGrenade path once the throw start
  and inventory check are read. New hook code goes in a new klhook file. Needs the owner's in-game test.
- Stage D (other types): Smoke / TearGas / Incendiary need effect pools (from the kept DD templates or a
  DM effects graft) and the smoke/gas damage controllers; Flashbang is DD-only in its template, DM has no
  projectile for it (MEASURED: no DM Grenade_Flashbang group), so build it from the Smoke group plus
  Template_Flashbang_01 (GUESS).
- Stage E (real sounds): `kl_snd.merge` of DM's fragmentation_explosion_01-03 + offset remap.
- Stage F (online): identical builds required; test in private match only after local play works.

## 9. Risks

- CExplode / ZItemTemplateAmmo pairings are ASSUMED (high risk); wrong Explode radius order could mean a
  harmless-looking but oversized or silent blast. Compare against Rocket_RPG7's Explode in DD to check.
- Missing effect pool refs crash at load (unregistered / empty refs, see CLAUDE.md pool notes): every ref in
  the cloned group must resolve in the target level.
- Frag damage affects friendlies; FA friendly-fire handling not checked.

## 10. Stage A/B result (2026-10-18, kl-merge agent, OFFLINE, NOT RUN in game)
- Stage A finding: in the stock FA overlay F06 the Ammo\Grenade_Fragmentation projectile slot is EMPTY (as for all grenades), so stage B was needed.
- Stage B (tools/kl_grenade.py, .prp-only so no slot renumbering): Ammo\Grenade_Fragmentation projectile -> Projectile\Projectiles_01\Rocket_Flare;
  that node's ballistic controller gets fuse 3.3 s + eGRENADE_FRAG, plus Explode and ShakeCamera controllers copied from Rocket_RPG7;
  Explode floats set to Dead Men's frag values (550/200/1000/350, field 13 = 80). 10 Police/Swat_02 actors (spread over squads) get Grenade_Fragmentation in their weapon fields.
- Build: build/grenade_1018/GR06/F06_Main.zip md5 5ead3e707364bf8ad9ab13881d4ef6d5 (check_passes PASS, kl_fa.check 0 findings, J.check no misfits).
  Install: "INSTALL grenade test.bat" (F06=GR06 in KLHook.ini, backup KLHook.ini.before-grenade1018) / "UNDO grenade install.bat".
- GUESS: Explode field 14/16 swap pairing; stand-in effect FX_Grenade_RPG_01 and sound (rpg_explosion_01); fuse 3.3; that police with the grenade ammo throw at all (GrenadeAttack tactic start condition unread, UNKNOWN).
- Crash risks: Rocket_Flare node reuse (its flare effects now explode), new grenade ammo state on NPCs, friendly fire from the frag.
- Review 2026-10-17 (adversarial, offline): zip re-checked (check_passes PASS); Ammo projectile field 24 matches every other ammo template; no new InventoryBinding, no new entity or type id, no pool change; the only .SND offsets used (375312, 375392) are the level's own, none from Dead Men. REAL BUG FIXED in install_grenade.ps1: the F06= edit matched the FIRST `F06=` line in KLHook.ini, which is `F06=DM09` in [Redirect.2] (Retomoto Tower, menu page 2), not the stockfa `[Redirect]` line `F06=DD06` (the one for page 1); the install now edits only the `[Redirect]` section, undo restores from the same section of the backup. Also: a second install run overwrote the "created" state so undo no longer removed GR06 (now kept), and a stale GR06 folder is md5-checked instead of trusted. Tested on a copy of the live ini: install, re-install, undo, re-undo give the original ini byte for byte. Remaining: Launcher_HK69A1_Flare ammo shares Rocket_Flare, so a player flare launcher would also explode; page 2/3 F06 slots are NOT redirected (test on menu page 1).

## 11. Do NPCs with grenade ammo throw? (2026-10-18, kl-merge agent, OFFLINE static read of kl2.exe, NOT RUN)
Answer: NOT on their own, as far as the tactic code shows. Holding Weapon\Grenade_Fragmentation in ZFFActor[4] is
necessary (see 11.3) but nothing in the autonomous tactics starts a throw; the only start is a scripted
`GrenadeAttackBehaviourRout` step in the squad route, and no stock level has one.
- READ: `CPPScript::ZSoldier` slot 17 (0x6ab250) builds, per soldier, the throw machinery: `ZFireThrowWeaponTask`
  (vtable 0xbd0c34, at soldier+0x578, 0x6ab390), the goal `ZGrenadeAttack` (vtable 0xbd0834, ctor 0x836830, at
  soldier+0x660, 0x6ab854) and `ZGrenadeAttackBehaviourScript` (0xbd07f4, ctor 0x648260, soldier+0x664). 0x6e49b0
  registers all 11 such goal objects (soldier+0x638..0x664) with id 0x96. The name string "GrenadeAttack" (0xb62840)
  is only returned by the goal's slot 7 (0x4cdb00).
- READ: no tactic class mentions grenades: the autonomous tactics are the `Z*Tactic` classes (AttackFromCover
  0x680b20, AttackNoCover 0x85ece0, DefendCover 0x84dc90 ...), none is a grenade tactic, and of all `CPPScript::`
  classes only `ZGrenadeAttack::Run` (slot 2, 0x6eb170) and `ZDefendCoverEval` (0x604190, unrelated use of the same
  slot number) call soldier vtable +0x170.
- READ: soldier vtable +0x170 = 0x89eed0 = "start ZFireThrowWeaponTask at a position": it stores the position at task
  +0x14 and a weapon index at task +0x24 (0x6c5f90). `ZGrenadeAttack::Run` = move to its position A (0x8997a0, goal
  +0x14), draw a random 0..32767 delay into soldier+0x684, then call +0x170 with its position B (goal +0x20, weapon
  index 0) and wait. The task body (0x53a230) copies the index into actor+0x608, takes the item from actor+0x608,
  else actor+0x604 (index 0 = the default throwable = the actor's grenade field), plays the throw action
  (0x7ddc70) and waits a random time.
- READ: the entry that starts the goal is `ZSoldier` slot 84 (vtable +0x150, 0x8410d0): it refuses (sets
  soldier+0x4fc = 1 = "done") when soldier+0x700 is set, or the actor is locked (+0x5c8), or the soldier's mode
  (+0x6d8) is 6 (the dog); otherwise it loads the goal at +0x660 with (position, arg), clears +0x4fc and runs it.
  NOT FOUND: any caller of slot 84 in a `CPPScript::` class (searched for call [reg+0x150] in every method of every
  CPPScript vtable: none). UNKNOWN: callers outside CPPScript (ZFFActor, squad code, the rout controller).
- READ: `ZGrenadeAttackBehaviourRout` (vtable 0xbcf69c, 7 stored fields): 0 `s` (reference to the actors, read at
  +0x4c; resolved 0x8ccde0 -> 0x629aa0 -> squad object [+0x77c]), 1..3 `f f f` (x y z of the throw, +0x50..0x58),
  4 refs (NEXT), 5 b, 6 b. Its slot 14 (0x7d3970) makes `ZGrenadeAttackBehaviourGoal` (0xbcf72c) from them; the
  goal's body (0x7fdb10) waits until the squad member has arrived, then orders the soldier (vtable +0x13c) to the
  target's position, and finishes. So a throw exists only as a ROUTE STEP: "these actors throw a grenade at (x,y,z)".
- MEASURED (this session, all 21 stock levels): zero `GrenadeAttackBehaviourRout` controllers (the "4 in L10" in
  section 5 / re/bots_dynamic.md belongs to `DownNotDeadBehaviourRout`, not to this one). So no stock squad ever throws.
- Consequence for the F06 build (build/grenade_1018): the 10 police only carry the item; they will probably NOT
  throw. The fix needs a step, not an item: append a `GrenadeAttackBehaviourRout` controller [actors, x, y, z, NEXT,
  b, b] to an existing police route node and reference it from an earlier step's NEXT list (nodes with two
  behaviour controllers exist in stock: ('MsgForward','HeliFlyBehaviourRout') x 12 in F06, so a second controller on
  one node is a legal shape; that a NEXT reference fires every controller on the target node is a GUESS). The
  position would be a fixed world point (loot room / escape), not "the player". NOT implemented: the effect cannot be
  judged without a live run and a wrong NEXT edit can stall a squad; kl_grenade.py and the installed build
  (md5 5ead3e70...) are unchanged.
- 11.3 What an actor needs once a step fires: the grenade in its grenade field (done by kl_grenade.py), a
  projectile on the Ammo (done), not the dog / not locked / soldier+0x700 clear, an arrival at position A, then the
  throw runs after a random delay. Distance, cover and "player in the open" are NOT tested by the goal itself
  (READ: no such test in 0x6eb170 or 0x53a230); they belong to whoever picks the position.
- Open: callers of ZSoldier slot 84; whether `ZGrenadeAttackBehaviourScript` (0x559290, which reads the soldier's
  current target at +0xb0 and walks toward it) is what the rout uses instead of the three floats; GUESS either way.

## 12. Throw steps in GR06 (2026-10-17, owner item 19)
`python tools/kl_grenade.py build <overlay> <out>` now adds, by default, one `GrenadeAttackBehaviourRout` route step for
the 3 nearest eligible squads (020, 021, 030_cooridor; 010 is excluded: its RunToCover has no starter). `--no-route`
reproduces the grenade-only build (md5 5ead3e70), `--squads=N`, `--target=x,y,z`. New entities: 1 group + 3 steps
(`AI_Players!GrenadeSteps\Throw_*`); 19091 slot ids renumbered by the kl_fa_civs procedure, room sets unchanged, .oct
records unmoved. The squad's RunToCover NEXT list names the step; the step's NEXT is the old RunToCover NEXT.
Layout [s actor group path, f x, f y, f z, NEXT refs, b, b] from re/kl2.json; no stock level of either game has one.
GUESSes: the two booleans (1, 0); the 's' field takes the carrier's actor GROUP path; the xyz may be ignored (Run slot
0x7fdb10 does not read +0x20..0x28; the goal throws at the soldier's CURRENT target), so a squad with no target may do
nothing; target = mean of F06's NORMAL loot stacks; RunToCover NEXT fires the whole new node.
Sounds: Dead Men's fragmentation_explosion_01-03 / shot_fragmentation_01 are in the M01_FA_A bank (about offsets
218000-224800), kl_snd.merge + graft_audio could append them, but a stock-overlay build has no path for it and no pin
sound was found; NOT grafted, the stand-ins stay.
