# Grenades and carried throwables, Dog Days side (2026-10-25, research only)

Companion to `re/grenades.md` (items, projectiles, sounds, NPC route). Addresses are kl2.exe
(32-bit, base 0x400000). PROVEN = seen in exe or stock data. GUESS = inferred, not checked.

## Classes and ids
- PROVEN: kl2.exe keeps the grenade and throw action classes and the RMC messages. Action ids
  (via ZFFPlayer vtable slot 225, +0x384, "get action by id"; factory 0x839740): PickupItem 4,
  Throw 0x11, ThrowBackGrenade 0x24, ThrowObject 0x2d, ThrowWeapon 0x2e, PickupObject 0x43.
- PROVEN: ZThrowable is DD-only (ZHavokRigidBody based, 352 B, has BarrelEffects). Dead Men has no
  such class; its grenade is an inventory item plus projectile (see grenades.md).
- GUESS: class type ids match DM for the shared classes (same family); not compared per class here.

## Carried throwable (extinguisher, gas can)
- PROVEN: the carried object lives at `[player+0x2d48]`, separate from the inventory at `[player+0xcec]`.
- Prompt/use per frame 0x54e040 -> pickup action creator 0x8f5cf0 (action 0x43) -> SetCarried 0x407140.
- Getters 0x5423b0 and 0x890fa0. Clear carried 0x56ad60.
- Throw: wrapper 0x7c58c0 -> DoThrowObject 0x5d3bc0 (action 0x2d); eligibility check 0x651000.
- Net: RMC senders 0x4654d0, 0x4d5660, 0x884aa0 (pickup, throw, drop; signatures in re/netcode.md).
- Stock chains: F04 EXT_CAN 5270 (cloned by tools/kl_interact_graft.py); layout in re/interactivity.md.

## Player grenade input (the missing piece)
- PROVEN: input path is ZGameplayInput vtable slot 12 (0x808720) -> per-button setters writing
  bits of `[player+0xb90]` -> 0x544780 copies them into the action word `[player+0x818]`.
- PROVEN: DD's HoldGrenade setter 0x4aa410 has no "set" branch; it only clears bit 0x40 of
  `[player+0xb90]`. So the player never starts a grenade throw through input in DD.
- PROVEN: ZFFActor grenade-throw slots 432 / 433 (0x432440, 0x898a50) still exist.
- DM contrast: HoldGrenade string at 0x96b6e8 (reg. 0x672eb1, fn 0x672d60); ZGameplayInput vtable
  0x96b7fc, slot 12 = 0x637f10 (big per-frame poll). No `b90` write found in the part read
  (0x637f10..0x638400), so DM's setter is elsewhere. NOT FINISHED.

## Levels
- PROVEN (scan of all 21 stock levels): no grenade templates in campaign levels, no AI
  grenade-throw route steps anywhere; grenade item names exist only in FA levels.

## Open
- Does a carried throwable coexist with a gun in hand? Not settled (GUESS: yes, since the carried
  slot is outside the inventory, but the hands/animation state is unchecked).
- Who reads throw bit 0x800 of the action word, and where inventory grenades are consumed.

## Hook proposal (for kl-merge-e8; NOT built, hook source is theirs)
1. Hook the 0x4aa410 setter (or 0x544780) and OR the grenade bit into `[player+0xb90]` while the
   grenade key is held and the inventory holds a grenade item; local player only, offline first.
2. Verify the action 0x11 / slot 432 path runs with an F06 grenade item (tools/kl_grenade.py stand-in).
3. Toggle in KLHook.ini, "(recommended off)" until a live run proves it.
