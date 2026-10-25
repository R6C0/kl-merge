# Hook-side grenade throw for Dog Days: scope and plan (2026-10-25)

Research only. Nothing built, installed or run. Confidence: H = from disassembly/log, M = inferred, L = guess.

## Why the Create+Start route is dead (H)
- Action 0x11 = ZFFActionThrow (vtable 0xbb4d24, ctor 0x6757b0, tick 0x65ce70).
- CreateAction (player vt+0x384 = 0x839740) passes [P+0xa1c] as ctor arg3, stored at [action+0xc].
- The first tick dereferences word [[action+0xc]+2]. [P+0xa1c] is zeroed by player init 0x8f5fe0 and has no
  other writer in kl2.exe. Probe2 on DM01 confirmed [P+0xa1c]=0. So the action reads a null descriptor.
- DM's counterpart fields ([P+0x8cc], [P+0x86c]) are only zeroed in the player ctor 0x6d3510 (0x6d3666, 0x6d361e);
  the real writer lives elsewhere in DM (not found yet).

## Mechanism of a real throw (H for chain, M for effects)
- The grenade is the item object already in the hand (inventory entry [P+0xcec]).
- On release the action sets a velocity on the item via item vt+0x2cc (0x536dc0, stores item+0xc8..0xd0), then calls
  0x659be0, 0x47ded0 on [[0xdd265c]+0x15b0], and 0x8f5430 on the inventory. (M) Fuse and explosion then follow from
  the item's own projectile controllers (Rocket_Flare node patched in DM01 data, fuse 3.3, eGRENADE_FRAG, Explode 550/200/1000/350).

## Classes (H for existence, via kl_rtp / kl2.json)
- ZFFActionThrow (player), ZFFHavokProjectileBallistic (projectile controller, slot 34 = launch with param struct),
  ZFireThrowWeaponTask and ZFFActorActionThrow (AI), ZGrenadeAttackBehaviourRout (route step; soldier vt+0x170 = 0x89eed0),
  ZThrowable / ZFFActionThrowObject (canisters), Explode controller, ZVehicleEffects chain (see klcardown.c:
  health 0x412430, Explode 0x590480, effects 0x877f30, damage 0x8ec590).

## AI throw path (M)
- Started only by the ZGrenadeAttackBehaviourRout step; it needs an NPC actor, not the player. Callable on a spawned
  or existing cop as a fallback ("cop throws at the aim point"), but it is not the player's hand.

## Plan
1. Probe 2a (read only, SHIP-safe): call 0x59d550(P, wordIndex) for the indices DD's throw uses, log the return values
   and dump the first 16 bytes behind each. Confirms these are animation descriptors with a word at +2. Confidence M.
2. Probe 2b: write that descriptor pointer into [P+0xa1c] (data write only), then Abort(vt+0x374) + CreateAction(0x11)
   + StartAction(vt+0x370) exactly as klgrenade.c / kladren.c do, wrapped in SEH. Expect the tick to survive and the
   release to fire. Confidence M-L. Log whether the item gets a velocity at item+0xc8..0xd0.
3. If the release does not launch: call the projectile launch (slot 34) with a param struct built from the hand position
   and the aim vector. Needs a probe of callers of vt+0x88/slot 34 first. Confidence L.
4. Fallback with no projectile: trigger the Explode controller or ZVehicleEffects explode chain at a world point on a timer.
   Confidence M that it works visually; no arc.

## SHIP-safety
- All steps are data writes plus game calls from our own frame callback on the game thread: allowed in SHIP. No code patches.
  Restore [P+0xa1c]=0 after the throw if it proves to be shared state (L).

## Open
- DM writer of the descriptor field; contents of 0x5c2f60 / 0x59d550 results; where the projectile is spawned (callers of slot 34).
