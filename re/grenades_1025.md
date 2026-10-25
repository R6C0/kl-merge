# Grenades on the player, Dead Men style: options, ranking, first prototype (2026-10-25, research only)

Owner: "look into grenades in dead men and implementing them here, you got the fire extinguisher, now it is just a matter of
adding them onto your character like Dead Men". Plan plus critic pass over `re/grenades.md` (sections 1-13) and
`re/throwables_dd.md`. Nothing here was built, installed or run; no game folder was written; hook source (`klhook/*.c`,
`KLHook.ini`) is kl-merge-e8's, so the hook parts are PROPOSALS only.
Labels: PROVEN = seen in an exe or stock data (re-checked in this pass where marked "rechecked"); GUESS = inferred.

## 1. Facts re-checked in this pass (the key claims)

- PROVEN (rechecked, strings): kl2.exe has HoldGrenade, StartWithGrenadeInHand, AnalogChargeGrenade, ZThrowable,
  ZFFActionThrowBackGrenade, ZGrenadeAttackBehaviourRout, YouPickedUpGrenade, eTHROW_THROWABLE. kaneandlynch.exe has HoldGrenade,
  TapCycleGrenade, ZFFActionThrowBackGrenade, YouPickedUpGrenade and NOT ZThrowable / ZGrenadeAttackBehaviourRout.
  **TapCycleGrenade (the DM key Q to cycle grenade type) does not exist in DD**: DD has no grenade-cycle input, so a second
  grenade type needs a new key or a fixed "G = the grenade you hold".
- PROVEN (rechecked, kl_rtp json): `Throwable` controller = (ZHavokRigidBody, ZThrowable, 352 B) exists in kl2.json only;
  ZFFItemTemplateWeapon / ZFFItemTemplateAmmo exist in both exes with the same base chain (ZItemTemplate -> ZGROUP).
- PROVEN (rechecked, disassembly): **the DD hole.** `kl2.exe 0x4aa410` (HoldGrenade setter, 15 bytes) is
  `cmp byte [esp+4],0 ; jne +7 ; and [ecx+0xb90], 0xffffffbf ; ret 4`: it can only CLEAR bit 0x40 of `[player+0xb90]`. DM's twin
  `kaneandlynch.exe 0x5ef8a0` is `cmp byte [esp+4],0 ; je ; or [ecx+0x968], 0x40 ; ret 4`: it sets it. So `ecx` is the player in
  both, and DD's code was edited to drop the "set". Offsets differ between the exes (DM 0x968 / action word 0x7d0, DD 0xb90 /
  0x818): never port a DM offset.
- PROVEN (rechecked): `kl2.exe 0x544780` copies bits of `[player+0xb90]` into the action word `[player+0x818]` every frame
  (fire bits, and `or [esi+0x818], 0x800` at 0x5447f9 / `and ..., 0xfffff7ff` at 0x544805, the grenade bit; the 0x40 -> 0x800
  pairing is also the finding of re/player_down.md S2). Whoever READS 0x800 is not found (byte scan finds no `test` with that
  immediate): the throw start is not located. The rest of the chain (action 0x11 Throw, slot 432/433 at 0x432440 / 0x898a50) is
  PROVEN to exist, not proven to run for a player.
- PROVEN (re/weapon_slots.md, rechecked in its text): inventory entry kinds 0 grenade, 1 two-handed, 2 one-handed, 3 special; the
  DD pickup `0x6cc1d0` counts only kinds 1 and 2 against the 2-gun limit, so a kind-0 grenade takes no gun slot.
- PROVEN (kl_grenade.py check on DD F06): five grenade templates exist in every DD FA level (Flashbang, Smoke, Fragmentation,
  TearGas, Incendiary), each with a Ground child and an InventoryBinding; the Ammo projectile slot (field 24) is EMPTY for all; the
  F06 flare node is the stand-in projectile used by `tools/kl_grenade.py` (GR06, md5 5ead3e70, installed earlier, never seen to throw).
- PROVEN (older notes, MEASURED on M01_FA_A): DM's `Projectile\Grenade_Fragmentation` is a ZGROUP + Ground ZLNKOBJ with Explode,
  ShakeCamera and FFHavokProjectileBallistic controllers; DM places pickups as `ZFFItemWeapon {template ref, 0, 1, eBOTH_PLAYERS}`
  in M02_A, M03_A, M05_A, M08_A, M11_B, M13_A. DD FA maps have no weapon/grenade pickups.

Critic notes on the two reports (inconsistencies to keep out of later work):
1. `grenades.md` section 7 says ZGameplayInput slot 7 = 0x5fbfa0 for the grenade; `throwables_dd.md` and re/player_down.md
   (line 1363) say slot 12 = 0x808720. Use slot 12 (the later, read-from-disassembly one); section 7 is stale.
2. ThrowBackGrenade is action 0x23 in DM and 0x24 in DD: action ids SHIFT between the exes. Never hard-code an id across games.
3. Both reports say grenades "bound once per level": a graft must reuse the DD template and binding (no second binding).
4. "HUD draws no grenade count in DD" (hud_weapon.md) is unverified; DM's count display is also unresolved. Plan on an
   invisible count (message only) for the first prototype.
5. The extinguisher analogy is only half right: the extinguisher is a CARRIED PROP (`[player+0x2d48]`, not an inventory item,
   action 0x2d). A Dead Men grenade is an INVENTORY ITEM (kind 0) thrown by action 0x11. They are two different chains in DD.

## 2. The three options

### A. Revive DD's leftover grenade chain (data half) + a tiny input shim (the recommended way)
Meaning: use the DD templates that every FA level already has, fill their projectile with a Dead Men grenade (or the flare
stand-in), put the grenade into the player's inventory, and restore the missing "set" in the HoldGrenade setter.
- What the player sees: a Dead Men style hold-to-throw. Hold G (the key DD already binds to HoldGrenade; PROVEN the string and
  the setter exist, key binding itself GUESS), the throw animation from the generic `/Weapon_Handling/Throw_Grenade/*` clips (MEASURED:
  the same 18 clips as DM; the player sets Kane/Lynch have them), the grenade arcs and explodes with the Frag values (550/200/1000/350,
  fuse 3.3 s: MEASURED DM values). Sound: DD rpg_explosion_01 stand-in at first; real DM `fragmentation_explosion_01-03` via
  kl_snd.merge later (section 8 of grenades.md). Effect: FX_Grenade_RPG_01 stand-in (GUESS acceptable).
- Input: existing HoldGrenade (G). No cycle key (TapCycleGrenade absent in DD): one grenade type per life first (frag).
- How many per life: DM's pickups give the template's count (GUESS: 1 per pickup node; count logic at 0x5e6e00 unresolved).
  Proposal: 2 frag on spawn (hook or a start-inventory pickup node next to the spawn), refilled at each respawn / round reset.
  FA round reset frees the parked stock items (k44 note), so a data pickup placed in the spawn room is re-created each round.
- Works on stock FA maps and private match: yes for the data half (the five templates + bindings are in all nine FA levels'
  `mainsceneincludes_multiplayer.zip`); the shim is global. Online: the inventory replicates (DDL_SInventoryItems) and the throw
  has its own messages (DDL_SThrowGrenadeData, RMCGrenadeSync: PROVEN names in netcode.md), so in principle it syncs; every
  client must have the identical map build and the hook (GUESS that remote throws render without the hook: they arrive as net
  messages). Keep it offline-only until a live run works.
- Data vs hook split. DATA (mine): Ammo projectile fill in the target map (`kl_grenade` stage B; for DM maps graft
  `Projectile\Grenade_Fragmentation` from M01_FA_A), one `ZFFItemWeapon` pickup node near spawn. HOOK (e8): detour 0x4aa410 so that
  with arg != 0 it ORs 0x40 into `[ecx+0xb90]` when the toggle is on and `ecx` is the local player (compare to the local-player
  accessor already used in klhook), otherwise run the original. Nothing else.
- Effort: data 1 day (the tool exists, pickups need the kl_scene renumber path), hook ~20 lines, test 2-3 live runs.
- Risks: (1) the throw reads the item from somewhere not yet found (equip function 0x5f8d80 in DM; the kl2 twin not located); if
  the inventory item is not "selected" the action may do nothing (harmless) or deref null (crash); (2) Ammo projectile null ->
  crash at spawn (so never enable without the projectile filled); (3) friendly fire in FA; (4) the flare stand-in has no model;
  (5) renumbering when adding the pickup entity (use the proven kl_fa_civs / kl_scene procedure, then verify_levels `problems: 0`).

### B. A carried throwable "grenade" on the extinguisher chain (no hook)
Meaning: a small `Throwable` prop (cloned like `tools/kl_interact_graft.py` clones EXT_CAN 5270) with a short BarrelEffects fuse
and a grenade model, placed on the map; the player picks it up with the use key and throws it (action 0x2d, clip
`Throw_Canister_1H_2H`), it explodes on impact/fuse like the fuel cans.
- What the player sees: walk up, "pick up" prompt, he carries it in both hands (the canister pose, not a grenade pose), throws
  with the fire key (stock throwable behaviour, GUESS on which key), bang. Not "on the character": no belt count, no Dead Men grip.
- Input: stock use key and throw key; nothing new.
- Per life: 1 at a time, only what is lying on the map (dropped on death, GUESS); refill = the map respawn of the prop at round
  reset (GUESS; the stock cans are placed once).
- Stock FA maps / private match / online: map data, so every build with the data works; the carried-object net messages exist
  (RMC pickup 0x4654d0, throw 0x4d5660, drop 0x884aa0), so it is the only option that is already online-shaped. The Dead Men
  maps already received extinguishers and fuel cans (re/dm02_mall_1025.md), so the graft path is proven offline.
- Data vs hook: all data; no hook. A toggle would be a build variant (or a hook toggle of KLJoin) "(recommended on)".
- Effort: 1-2 days (reuse kl_interact_graft; the grenade look needs a model; or reuse the can model resized, ugly).
- Risks: it is not a grenade (carry-only, slow, one hand state, cannot be thrown while a gun is in hand: UNSETTLED, hands/animation
  state unchecked); damage is the BarrelEffects can blast, not the Dead Men Frag values; adds entities per pickup (renumbering).

### C. Full hook-side inventory slot + throw (hook gives and manages the grenade)
Meaning: KLHook creates the grenade item in the player's inventory (the kl2 twin of DM 0x5f8d80, plus a count), draws it in the HUD,
handles the key itself, and starts the throw action 0x11 itself.
- What the player sees: exactly Dead Men: grenades in the inventory from spawn, count on the HUD, G to throw, per-type cycle if a
  new key is added.
- Input: hooked key (G or Q).
- Per life: whatever the hook decides (2 frag, refill on respawn, on pickup of an ammo box).
- Works on stock maps and private match with no map change at all (the best coverage). Online: needs the hook on all clients and
  a replicated count; the inventory replication would desync a fake item (same warning as the third-gun shelf, weapon_slots.md
  section 4), so online stays off.
- Data vs hook: almost all hook (equip, count, HUD, throw start), plus the data projectile fill (the same as A). Hook size is
  hundreds of lines and rests on the unresolved functions (equip twin, throw start, count decrement, HUD).
- Effort: 1-2 weeks, high reverse work. Risks: highest (calls into unlocated code, desync online).

## 3. Ranking
1. **A (data + 20-line shim)**: most Dead Men result for the least new reversing; only the missing "set" is restored, the rest is
   DD's own chain; fits "on the character like Dead Men"; stock maps get it by toggle.
2. **B**: the only zero-hook, online-shaped path, but it is a prop pick-up, not a Dead Men grenade; good as a fallback and as a
   map-flavour complement (grenade crates).
3. **C**: the end-state if A's shim proves the throw works but the count/HUD/refill need control. Do not start before A proves the
   action chain.
(If A's step 0 shows the throw never fires from the inventory, fall back to B and treat C as research.)

## 4. Toggle (required: every mod feature on/off, labelled)
Proposal for `tools/kl_mod_options.py` (feat format as the shoppage entry) and `KLHook.ini` (kl-merge-e8 owns both):
- ini: `[Grenade] Enable=0`, `Count=2`, `Log=1`.
- label: `Dead Men grenades: hold G to throw a frag grenade (recommended off)` until a live run proves the throw, then flip the
  recommended state to `(recommended on)` in one line. Off = the original 0x4aa410 behaviour (no throw), so a build with the data
  in the map but the toggle off is inert (the item can still be picked up; it does nothing).
- Safety defaults in the shim: local player only; offline Arcade only (inert when `kl_online()`); skip when the player is down/dead
  (re/player_down.md uses the same bit as "no throw while down").

## 5. First prototype, one Dead Men map: DM01 (M01_FA_A, Hot Coffee)
Why DM01: its pack already has the DM Frag projectile group (MEASURED), it is the map the other work is built on, and the F01 slot
is the unattended-test slot.
- Step 0 (hook only, no data, 1 run): log-only probe by e8: on G press log `[player+0xb90]`, `[player+0x818]` and the inventory
  list (`[player+0xcec]`: entry item ids and kinds). Answers whether a stock FA player holds any grenade item and whether the
  action word 0x800 appears. No behaviour change.
- Step 1 (data): `kl_grenade`-style patch of DM01's Ammo\Grenade_Fragmentation projectile (graft the DM Frag group from M01_FA_A
  through `kl_scene.graft`, convert Explode with the +3 fields from `kl_convert.LEVEL_MAPS`, effect/sound stand-ins FX_Grenade_RPG_01 +
  rpg_explosion_01) and ONE `ZFFItemWeapon` pickup `{Weapon\Grenade_Fragmentation, 0, 1, eBOTH_PLAYERS}` at the spawn room,
  cloned from DM M03_A's shape, count 2. Run `verify_levels` (`problems: 0`) and `debug/check.py`.
- Step 2 (hook, shim): the setter detour behind `[Grenade] Enable=1`. Toggle on, offline.
- Step 3 (autotest then a human run): `python tools/kl_autotest.py` for crash-free load; then walk to the pickup ("You picked up
  grenade" message), hold G: expected log lines `grenade: bit set` then the action word showing 0x800, a projectile entity, the
  explosion after about 3.3 s.
- Pass: grenade thrown and exploding, count goes down (or the item disappears), no crash, no gun slot lost (carry two guns + the
  grenade). Fail branches: bit set but no projectile = throw reads something else (find the reader of 0x800 or fall back to
  B); crash at throw = null Ammo projectile or missing effect pool.
- Rollback: toggle off + the staged build's undo; the F01 test slot only.

## 6. Open questions for a later pass (reverse work, in order)
1. The reader of action-word bit 0x800 and the ZFFActionThrow (0x11) tick in kl2.exe (DM tick 0x5fe810 is the guide; offsets differ).
2. Where the inventory grenade is consumed (count decrement) and what selects which grenade is thrown (no TapCycleGrenade in DD).
3. DD's pickup message count (YouPickedUpGrenade1/2 strings exist, the routine is the twin of DM 0x5e6e00).
4. HUD grenade count (probably absent in DD; a hook HUD line or a message is fine).
5. Whether remote clients can render a throw without the hook (DDL_SThrowGrenadeData handling).
6. Real DM sound and model for the grenade (Ground ZLNKOBJ, Projectile_HK69_Grenade ZSTDOBJ) for the graft.
