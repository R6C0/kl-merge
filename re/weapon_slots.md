# More gun slots in Fragile Alliance (kl2.exe build 0490)

Short version: the two-gun limit is a number in code that we may not patch. A data-only "shelf" in KLHook
(`klhook/klinv.c`, off by default) can carry a third gun. Nothing of it has run in the game.

## 1. The rule (READ)
- Inventory: `[player+0xcec]`. `+8` = array of 16-byte entries, `+0xc` = count. Entry: `+8` gun object, `+0xc` binding.
  Binding: `+4` item id (GUESS), `+8` kind (eFF2ItemType: 0 grenade, 1 two-handed, 2 one-handed, 3 special, 4 count).
- `0x73c470(inv, kind)` counts entries with a non-zero object and that kind.
- Pickup `0x6cc1d0` (ZFFPlayer vtable slot 417, offset 0x684, thiscall, 4 args, arg0 = the weapon) computes
  `count(2) + count(1)` and compares with `cmp bl, 2 ; jb` at `0x6cc2ef`. Two or more guns held: the gun in the hand is dropped
  to make room. Kinds 0 and 3 skip the check.
- The floor trigger `0x7cd310` refuses before that when the count is above 1.
- Each item may be bound once per level (duplicate = assert, see CLAUDE.md), so more bindings do not help by themselves.

## 2. Data or code
Code. The `2` is an immediate in hashed code (`klranges.h`), so it cannot be changed.

## 3. Routes considered
1. Data: rebind a gun as kind 3 so it is exempt. Not chosen: kind 3 is not in the switch cycle (`0x49b2f0`) and kind probably
   drives hand and animation handling (GUESS).
2. Vtable swap of ZFFPlayer slot 417 with our own pickup. Legal, but other hook parts recognise a player by vptr `0xbb45f4`;
   rejected.
3. Shelf (chosen, `klinv.c`): write 0 into `[entry+8]` of the gun that is not selected. The count and the HUD "other gun" lookup
   (GUESS for the HUD) no longer see it, so a third gun can be picked up. A key swaps shelf and hand. Heap data only, no call.

## 4. What the player sees
- HUD: still two slots (`0x88bac0`, i = 0 and 1). The shelved gun is not drawn; the swap key changes which two.
- Online: the inventory replicates (DDL_SInventoryItems, item + ref), a shelf would desync. `klinv.c` runs only offline Arcade
  (rules `0xbd3514`) and is inert when `kl_online()`.

## 5. Use
Ini: `[Inv] Enable=1`, `Key=0x77` (F8; the key is polled, not consumed, so the game sees it too: pick one the game does not bind), `Log=1`. Wiring lines (as klnet.c): `#include "klinv.c"` after klnet.c (~651),
`klinv_tick(game_thread);` in klh_tick (~782), `klinv_init();` after `klnet_init();` (~1129).

Live test, Arcade: pick up two guns, press the key (log `inv: shelved item ..`), walk over a third gun (it is taken, not swapped),
press the key (shelves the unselected one, restores the oldest), press the key again to cycle. Expected log lines: `inv: on`, `inv: shelved`,
`inv: restored`.

## 6. GUESSES
Shelved object stays alive; its back model may still draw; the game never refills a null entry except on a pickup of the
same item (the restore then gives up); ammo boxes ignore the shelved gun; death or round end drops the shelf (the gun is
lost until the round reset); binding+4 is the item id.

Reclassified after review: the HUD lookup 0x49b2f0 tests the same object field as 0x73c470 (READ, 0x49b311
`cmp [eax+8],0`). The add path 0x8aacc0 -> 0x6a00e0 -> `mov [esi+8],ebx` (0x8aad03) fills the entry found by item id
(0x5aa000 compares `[entry+0]` with the id, READ 0x5aa020), so a third, different gun fills its own entry.

## 7. Safety rules added after review
- The shelf stores the entry's item id (`entry+0`) and the gun object's vtable. A restore is refused unless the entry still
  holds that id, the same binding and no object, and the object still has that vtable. This stops a freed pointer being
  written into a new inventory after a level reload that reuses the same addresses.
- The tick checks player and inventory on every call (not every 30 ms) and drops the shelf at once on any change.
- A full shelf no longer blocks the key: the swap shelves one gun and restores the oldest (net zero).
- The held gun is told apart by both `binding+4` and `entry+0`; both must differ from the selected id.
- A press on a non-game-thread tick is no longer lost.
- Still open: menus and pause do not block the key (GUESS: harmless, only the inventory is edited).
