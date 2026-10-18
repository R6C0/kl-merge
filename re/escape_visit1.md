# Escape visit 1: why the van does not come (root cause, static reading)

Written 2026-10-18 by kl-merge-e5 (workflow wywlfcsgg: a read agent, then an adversarial re-check). The fix in use is klmove EscVisitProbe / EscVisitFix (08eaf15b). It is proven live on Vault L61/L63/L65, Park II L66/L68 and Hot Coffee II L67.


Static reading of kl2.exe only. I used a linear capstone sweep, vtable dumps, and callers found by scanning for `E8`/`E9` call targets. Nothing was run. The scratch scripts are in `C:\Users\Henri\AppData\Local\Temp\claude\c--kl-merge-kl-merge\d20b026f-6c1c-42c8-8d9e-2f96a87bb38d\scratchpad` (`dz.py`, `callers.py`, `clos.py`, `clos2.py`).

## Headline: a missed writer that explains the live observation

- **FACT.** **0x65ee60 writes [rules+0x1e0] and the first report missed it.**
  - Code: `cmp [ecx+1e0],0 ; jne fail ; mov eax,[esp+4] ; mov [ecx+1e0],eax ; mov al,1 ; ret 4`.
  - It is a "set only if empty" setter. It writes a non-zero value, does not touch 1e4 or the handle, and is never called from the Heist vtable.
  - Why the first report missed it: its closure followed only direct calls from the Heist vtable.
- **FACT.** ecx at the call sites is the rules object.
  - 0x7fdc89 and 0x7fdd29 do `mov ecx,[0x168e9e4] ; call 0x508ef0`.
  - 0x508ef0 returns `[[0x168e9e4]+0x54]` when `[[0x168e598]+0x5c]==4` and 0x7f6850 passes. The same expression is the rules pointer in `klbot.c:24`, whose own comment cites 0x508ef0, and 0x7bb2a0 is the equivalent getter.
  - The two callers are 0x7fdc9a and 0x7fdd3a. The argument is `[esi+0x24]`.
- **FACT.** The caller is vtable slot 26 of ZPlayerAction.
  - The function is 0x7fdbb0 (`ret 8`), at cell 0xbc2a54. The ZPlayerAction vtable is 0xbc29ec, and 0xbc2a54 is 0x68 bytes in.
  - It handles two event ids, `[0x16891a0]` (0x7fdc03) and `[0x168919c]` (0x7fdc9f).
  - It runs only when the action's active flag `[esi+0x54]` is set, 0x7f6850 passes, and the action's name string, at `[esi+0x50]+0xc`, equals the string at 0xb50920. That string is `"EnterVehicle"`.
  - On a match it calls `rules.SetBoardingOwner([esi+0x24])`.
- **FACT.** I checked every function that calls either rules getter, and every direct callee of those functions, against the set of functions containing a store to a 1e0 field. 0x7fdbb0 is the only hit, through 0x65ee60. Rules-getter callers cannot be proven to be the only route, because the pointer can also be reached through inlined `[0x168e9e4]+0x54` (GUESS).
- **Consequence (FACT).** `[1dc]==0` does NOT imply `1e0==0`.
  - The EnterVehicle action can set 1e0 to a non-zero object while the vehicle state is 0 and no handle exists, so 1e4 stays 0.
  - Slot 194 then sees `1e0!=0` and skips slot 89 (0x8fa705 → 0x8fa70b, `jne 0x8fa719`).
  - State 1 starts with `1e4==0`, so the drive-in is skipped (0x8fa76e: `cmp [1e4],0 ; je 0x8fa84a`).
  - This matches "1e0 written ~1.3 s before state 1 with no handle".
- **FACT.** Slot 194 treats 1e0 as an object with a virtual method. In states other than 3 and 4, a non-zero 1e0 gets `call [vtbl+0x54]` at 0x8fae66..0x8fae79. This fits 1e0 being the PlayerAction.
- **GUESS.** Why visit 1 fails on Park II, the Vault and Hot Coffee II but not on the working van maps.
  - Presumably the EnterVehicle action's event fires before the first call on those maps. It could be an active trigger overlapped at spawn, or an enable ordering. I have no code path or data for this.
  - Check it by logging the return address of every write to 1e0, or by checking which ZPlayerAction is named EnterVehicle and when its event fires.
- **GUESS.** Visit 2 works because state 0 or 7 has cleared 1e0 by then (0x8fa6fd, 0x8fad58, 0x4fb63b), so slot 89 runs again. Nothing shows whether the action can re-fire after the clear.
- **FACT.** The `klmv_escvisit` fix matches this mechanism. It clears 1e0 and re-runs slot 194, which makes `1e0==0` true again.
- **FACT.** `klmove.c:1546` already says "owner set by 0x65ee60". The mechanism had been recorded before but not tied to the visit-1 failure.

## Class layout (corrections applied)

- **FACT.** Heist vtable 0xbd3514, FA vtable 0xbd2b9c, Sv vtable 0xbd2eb4, Cl vtable 0xbd31e4 (RTTI). Fields 1dc (state, a **byte**), 1e0, 1e4 and 1ec are shared by all four, as the first report said.
- **FACT, corrected.** The per-class vtable slots are:

| Class | Slot 3 | Slot 89 | Slot 194 |
|---|---|---|---|
| Heist | 0x4fb620 | 0x49d170 | 0x8fa6d0 |
| FA | 0x5b59d0 | 0x70f0a0 | 0x5b1410 |
| Sv | 0x717140 | 0x70f0a0 | **0x51e390** |
| Cl | **0x8c4df0** | 0x70f0a0 | 0x5b1410 |

  The first report wrongly said slot 3 and slot 194 were the FA versions for all three siblings. Slot 89 is shared by all three.
- **FACT.** Heist's slot 44 is 0x6cd8e0, slot 86 is 0x6df7d0, slot 119 is 0x521d30, and the other Heist slots cited are as in the first report.
- **FACT, corrected.** The old "Slot 119 (0x521e16) only reads 1e0" is wrong. 0x521e16 is `mov edx,[edx+0x1e0]` after `mov edx,[esi]`, which is vtable slot 120 (0x1e0 / 4). It is not the rules field. Some of the 320 sweep hits are vtable-offset noise of this kind.
- **FACT.** The constructor writes the vtable at 0x8354ba, after the base constructor call at 0x8354ad. The base constructor 0x7de590 stores 1e0 at 0x7de680, which is the only 1e0 store there. The two other addresses the first report cited for the base constructor (0x7de674 and 0x7de68c) are not 1e0 writes. They are neighbouring stores I did not decode, so I drop them as 1e0 writers. The Heist constructor stores 1dc (byte, 0x8356b0), 1e0 (0x8356bc) and 1e4 (0x8356c8).

## Every writer in Heist context (re-verified)

| # | Instruction | Where | Stores | Status |
|---|---|---|---|---|
| 1 | 0x8356bc (ctor), 0x7de680 (base ctor) | construction | 0 | FACT |
| 2 | 0x4fb63b | Heist slot 3 = 0x4fb620 | 0 | FACT, corrected (see below) |
| 3 | 0x49d1c9, 0x49d1e4, 0x49d1f2 | slot 89 = 0x49d170 | pool object, or 0 if the handle is 0 | FACT |
| 4 | 0x8fa6fd | slot 194, state 0 | 0 | FACT |
| 5 | 0x8fa74d | slot 194, case 0 | 0 | FACT |
| 6 | 0x8fad58 | slot 194, case 7 | 0 | FACT |
| 7 | 0x8faecc | slot 194, states 3 and 4 | `8ccde0(vehicle component +0x40 or +0x38)` | FACT |
| **8** | **0x65ee6d** | **0x65ee60, from ZPlayerAction slot 26 (0x7fdbb0), "EnterVehicle"** | **non-zero object (`[action+0x24]`), only if 1e0==0** | **FACT, new** |

- **Row 2, corrected.** Slot 3 loads the slot-194 pointer at 0x4fb626 but does not call it there. It zeroes 1e0 (0x4fb63b), 1e4 (0x4fb641) and 1ee (0x4fb647) first, then calls slot 194(0) at 0x4fb64d. The first report's "SetState(0) at 0x4fb626" was wrong.
- **Row 3.** Slot 89 loads the handle `[[this+5f8]+5c]`.
  - If the handle is non-zero it stores 1e4 = `8ccde0(handle)`.
  - 8ccde0 is `[0xe0ff90]` plus a lookup in 0x796ff0. The lookup returns `[obj+0x60]`, or 0 if not found.
  - It then derives 1e0 from `1e4->vtbl+0xfc(typeinfo)`. For vehicle kind 3 (slot 0x17c returns 3) it uses typeinfo 0xb73408 and field +0x40. Otherwise it uses typeinfo 0xb7b5b0 and field +0x38.
  - If the handle is 0 it writes 1e4 = 0 and 1e0 = 0.
  - A null 1e4 after a non-zero handle would fault at 0x49d1aa. A live "1e4=0 at state 1, no crash" therefore means slot 89 did not run, which is consistent with row 8.
- **Row 7.** It runs only if 1e0==0 and `1e4!=0` (0x8fae80 and 0x8fae89).
- **Slot 194 details (FACT).**
  - The state byte is stored at 0x8fa6f3.
  - With state != 0 and `1e0==0`, it calls slot 89 through `[vtbl+0x164]` at 0x8fa717.
  - The jump table at 0x8fb078 is: 0 → 0x8fa74d, 1 → 0x8fa75f, 2 → 0x8fa758 (sets 1ee=1 and joins state 1), 3 and 4 → 0x8fa8b3, 5 → 0x8faac5, 6 → 0x8faceb, 7 → 0x8fad58.
  - States 1 and 2 do not touch 1e0.
  - The tail at 0x8faf2d..0x8faf50 stores the state in `[[5f8]+0x54]`. States 0 and 7 zero the handle `[[5f8]+0x5c]`.
- **FACT.** Non-Heist writers are in FA slot 194 (0x5b143e, 0x5b149b, 0x5b1809 and 0x5b1971, all inside 0x5b1410), FA slot 3 (0x5b59e8), Sv slot 3 (0x71718e), FA/Sv/Cl slot 89 (0x70f0f8, 0x70f113, 0x70f121), and Cl slot 3 (0x8c4e0f, inside 0x8c4df0). The first report omitted that last one. Cl's constructor is at 0x8c4ab8.
- **FACT.** I confirmed the "other classes" attribution by function range for these: 0x4045ac, 0x41994a, 0x44804c, 0x4739c6, 0x487e3b, 0x4cda02, 0x559fea, 0x65c6bb, 0x65417a, 0x7c1610, 0x7d7523, 0x855b51, 0x880cb0, 0x6b0b3f, 0x6faa72 and 0x700b63. None is in the Heist vtable closure to depth 3 from the vtable.
- **FACT, partly unchecked.** 0x643de6 is inside 0x643ce0, which is in the closure. It is a list-count increment (`mov [esi+1e0],edi ; inc`), and I did not verify its receiver.
- **FACT.** 0x6749b2 is a new indirect writer of the form `lea eax,[esi+1e0] … mov [eax],0`, which a displacement sweep cannot see. It sits with `mov [esi+1d8],0 ; mov [esi+1dc],0 ; mov [esi+1e4],0`, in a function that starts at 0x674950. The receiver is not Heist (1dc is written as a dword there). It stores only 0.
- **GUESS.** The other `lea [reg+1e0]` and `lea [reg+1dc/1d8/1e4]` sites were skimmed by neighbouring instructions only, not resolved one by one. None looked like the rules object.

## Path from the exit trigger to state 1 (FACT, verified)

- 0x6cd8e0 (slot 44, `ret 8`) returns early unless the net mode from 0x8e6a20 is 0x19 and `[rules+0xe8a]==0` (0x6cd8e1..0x6cd8fe).
- It also needs `[rules+0x1dc]==0` (0x6cd988) before calling `0x8154f0(handle, 0)` at 0x6cd9af.
- 0x8154f0 returns if `[1dc]!=0`. For vehicle kind 3 it computes `[rules+0xe7c]` as the sum of three component floats (+0x70, +0x6c, +0x74).
- It sets `e8a=1` if its flag argument is non-zero or the clock test at 0x815547..0x81555d does not take the jump to 0x815571. This is about the second case, and I did not decode the clock test beyond this.
- It stores the handle at `[[5f8]+0x5c]` (0x815577) and calls slot 194 with `1 + (e8a != 0)` (0x815583..0x815594). That is state 1 when e8a is 0, and state 2 otherwise.
- The other callers of 0x8154f0, at 0x81e602 and 0x81e63b, push flag 1 and have clock-test guards in front. I did not decode the vehicle source, so calling them the "last call" path stays a **GUESS**.
- Other callers of slot 194:
  - 0x6df7dc (slot 86, which re-applies the saved `[[5f8]+0x54]` byte)
  - 0x6cd242 (calls `+0x300` then `+0x308`)
  - 0x6a114a
  - 0x4fa2c8
  - 0x51bc27
  - **GUESS:** the receivers of all of these except 0x815583 and 0x4fb626 are not verified. `+0x308` is a shared slot number across many classes, and a scan of `[reg+0x308]` and `[reg+0x164]` loads finds hundreds.
- The first report's claim that slot 89 has no direct callers is consistent with what I saw. I confirmed the single Heist call into it, `call edx` at 0x8fa717 after `mov edx,[eax+0x164]` at 0x8fa70f.

## Status of the first report's guesses

- **G1** (log is pre-slot-89): **GUESS**, superseded. The `1e4=0` reading is explained without it if 1e0 is already set by row 8.
- **G2** (visit 1 does not use 0x8154f0): **GUESS**, now unneeded. The state-1 route through 0x8154f0 also fits.
- **G3**: dismissed.
- **Retracted claim:** "I cannot explain it from the instructions". It is explained by row 8, up to the unknown trigger for the EnterVehicle event on the failing maps.

## Suggested checks (read-only, 3f)

1. Log the return address of each write to `rules+0x1e0` (a hardware write watch). Expect 0x65ee6d from 0x7fdc9a or 0x7fdd3a, about 1.3 s before state 1.
2. Log which ZPlayerAction (the one named EnterVehicle) fires, by `[action+0x24]` and by the ids `[0x16891a0]` and `[0x168919c]`. Compare a failing map (Vault) with a working one.
3. If the action fires early, a cleaner fix than re-running slot 194 is to clear 1e0 at state 0 entry (0x8fa6d0), or to block the event until the first call. Note that a clear at state 0 does not stop a later re-fire.

## 2026-10-18: the EnterVehicle action in the level data

**Escape visit 1: every EnterVehicle ZPlayerAction on Park II, the Vault, Hot Coffee II, Hasta, Last Call and the stock FA levels**

This is a static read of the installed zips under `C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps\`. I used `kl_scene`, `kl_prp` and `kl_rtp`. Nothing was run and nothing was written outside the scratchpad. The re-check scripts are `...\scratchpad\ev.py` and `...\scratchpad\rc\chk.py`. The first draft's claims were re-run against the same files. Changes from the draft are marked **(corrected)** or **(downgraded)**.

**Terms and map keys**
- FACT: ZPlayerAction is a controller (`PlayerAction`) on a node, not a node class. Every node that carries it is a `ZBoxPrimitive`.
- The failing maps are DM06B Park II (zip `F02`), DM03A Vault (`F07`) and DM01B Hot Coffee II (`F03`).
- DM11B Hasta (`F04`) and DM05A Last Call (`F01`) are helicopter-escape maps. Their action is `Triggers!BoardingTrigger_Heli`, not a van box.
- The stock FA levels are the copies under `KLExpansion\Maps\DD01..DD09`.

**What the action looks like**
- The body of every van-parented action in DM06B, DM03A, DM01B and DD04/DD07 is: `{ s:'' [2: CamPos_InVan, BoardingCar] 0 0 0 0 s:'' s:EnterVehicle b1 <node ref> b0 b1 b1 b0 eIntDest_CtrlPos eIntDir_CtrlDir eONLY_LYNCH eNoFilter UA_FA_ESCAPE b1 b0 }`.
- FACT: the name string `EnterVehicle` is followed by a bool, which is 1 (active) in all 41 copies.
- FACT: the node reference after that bool is the `BoardingTrigger` box itself on the vans.
  - **(corrected)** On the helicopter boxes it is not always a node. DD02, DD03, DD06, DD08 and DM05A have an empty string. DM11B names `EscapeSetup!EscapeChopper\Escape_Chopper`.
- **(downgraded)** I have not confirmed the "21 level-file fields" figure or that `EnterVehicle` is exactly the 8th field. `re/kl2.json` holds no per-field list for this class, and the token stream does not fix field positions. Treat both as unverified.

**Which field becomes +0x24**
- GUESS: it is the node-reference string right after the active bool.
- FACT: `re/bots_move.md:341` says the same ("box node the vehicle controller names = [rules+0x1e0]").
- No class-layout read confirms which field sits at +0x24.
- **(added)** The stock helicopter actions have an empty reference and are fine in stock. The "reference becomes +0x24" reading therefore does not hold for helicopter maps. If it is right, it applies to the van path only.

**Every EnterVehicle action found (all `ZBoxPrimitive`)**

| Map | Count | Scene path | Parent |
|---|---|---|---|
| DM06B, DM03A, DM01B | 1 each | `Animation/F07/F07_Escape_Vehicle_01.zip/EscapeVehicle_Animation_F07/F07_Escape_Vehicle_01/V_Van_00/BoardingTrigger` | `V_Van_00` (the van) |
| DM11B Hasta, DM05A Last Call | 1 each | `Triggers!BoardingTrigger_Heli` | none (top-level) |
| DD04, DD05, DD07 | 3 each | `Animation/Fxx/..._Escape_Vehicle_0{1,2,3}...BoardingTrigger` | `V_Van_00` of each vehicle |
| DD01 | 3 | `Animation/F01/Escape_Vehicle_0{1,2,3}.zip/.../V_Ambulance_00/BoardingTrigger` | `V_Ambulance_00` |
| DD09 | 3 | same pattern, Left / Middle / Right | `V_Van_00`, `V_Van_Middle_00`, `V_Van_Right_00` |
| DD02 | **8** (draft said 7) | `Escape!EscapeHelicopter_01/Incoming_x/BoardingTrigger_Heli..` | `Incoming_A..H` |
| DD03 | 4 | `Gameplay!99_EscapeHelicopter#01/Incoming_0x/BoardingTrigger_Helicopter_0x` | `Incoming_01..04` |
| DD06 | **8** (draft said 7) | same as DD02 | `Incoming_A..H` |
| DD08 | 1 | `Gameplay!99_EscapeHelicopter#01/BoardingTrigger_Helicopter_01` | the helicopter group |

All 41 copies are `PlayerAction` on a `ZBoxPrimitive`.

- FACT: each failing map has exactly one `PlayerAction` carrying `EnterVehicle`. No other controller body in those maps contains the string. I did not check node property blocks.
- FACT: the entity flags of the van-parented box are 0x200000 in the failing three and in DD07.
- FACT: the failing three and DD07 have the same box local position `(-1.75, 119.35, -337.14)`.
  - The size values are `95.09 134.53 80.35`. `re/bots_move.md` calls them half extents.
- **(corrected)** The van-parented actions are not identical in every stock level.
  - DD04's boxes are 150 × 150 × 150 and sit at different local positions, for example `(-1.79, 119.36, -399.85)`.
  - Vehicle 03 in DD04 and DD07 lists `BoardingCar` before `CamPos_InVan`.
  - DD04 vehicle 03 uses `eOnly_Mercs` in place of `eNoFilter`.
- FACT: vehicle 01 of DD07 matches the failing maps in every field, enum and flag. The only differences are the box size and the island of vehicles 02 and 03, which the failing maps do not have.
- FACT: the helicopter boxes use `eBOTH_PLAYERS / eOnly_Mercs`.
  - Flags are 0x202000 in DM11B and DM05A, and 0x202400 in the DD levels.
  - They hang off a top-level node or an `Incoming_x` / helicopter group, never off an animated van.
- FACT: there is no stray or duplicate action in the failing maps.

**Van set-up in the failing three versus stock**
- FACT: each failing map has one `OnlineEscAnimatedVehicle` controller on `EscapeVehicle_Animation_F07`, one `ZAnimatedVehicle` (`F07_EscapeVan_01`) and one `F07_Escape_Vehicle_01.zip` subtree.
- FACT: the controller body is identical to DD07 vehicle 01 in every field.
  - Activate frames are `144 230 355 444`.
  - Times are `7.2 8 8.48 6`.
- FACT: `Gameplay!EscapeSetup!OnlineEscapeVehicleMonitor` in the failing three is `0 0 1 <EscSoundHandling!Activate> 1 <RelayDestroyedEsc_01> 0 0 0 0 2 <OnScreenMSG_LastEscapeVan> <Timer_OSM_LastEscape> -1 0 -1 0 -1 0 -1 0`.
  - The relay list count is 1 (draft: "escape-van count field is 1, not 3", same fact).
- FACT: stock DD07 has three vans (`_01`, `_02`, `_03`) with different frames. Its monitor has the same layout with 3 relays (`_01`, `_02`, `_03`).
- **(corrected)** Stock DD04 also has three vans with their own frames (`191 288 502 555`, `0 195 239 348`, `137 245 313 389`).
  - Its monitor is named `Gameplay!EscapeSetup!EscMonitor` and has a different body: `0 0 0 3 <relay_01..03> 0 0 0 0 2 <Timer_OSM_LastEscape> <OnScreenMSG_LastEscapeVan> ...`.
  - It has no `Activate` sound reference.
  - The relays are in the same order. Only the last two entries (Timer and OnScreenMSG) are swapped.
- FACT: `tools/kl_fa_bank.py` states the one-van design on purpose.
  - Line 409 reads "The exit trigger names the one van in field 2 and nothing in 3..5".
  - Line 2349 reads "one van ... an unused van's target is the 0x686a66 crash".
  - Line 1028 rewrites F07's animation keys in place so the van drives along the map's road.
- FACT: the `V_Van_00` rest transform differs per map, and the vans' flags match stock (zip group 0x3000000, vehicle group 0x7200000, van 0x3244000, `ZAnimatedVehicle` 0x200000).

| Map | `V_Van_00` rest translation (x, y, z) |
|---|---|
| DM06B | (-6264.4, 2388.9, -5459.2) |
| DM03A | (-3248.0, 702.0, -11859.0) |
| DM01B | (5360.0, -13.0, 30800.0) |
| DD07 vehicle 01 | (5933.3, -198.0, 25626.1) |

- **(downgraded)** The draft said DM06B's y of 2389 "is the animation's own height". I did not trace that. Only the rest transform stored in the file is verified. The van's real path is set by the rewritten animation keys.

**What differs between the failing and working maps**
1. FACT: the failing maps use the stock F07 van animation with a single van whose path was re-keyed. The working van maps (DD01, DD04, DD05, DD07, DD09) have three vans each.
2. FACT: the working helicopter maps (Hasta, Last Call, DD02/03/06/08) have the action as a top-level or group box, not as a child of an animated van.
3. FACT: the action itself matches stock DD07 vehicle 01 in every field, enum and flag. The delta is structural:
   - one van instead of three;
   - a re-keyed or relocated van path;
   - a monitor with 1 relay.
4. GUESS: with the re-keyed path, the van's trigger box overlaps the players, a spawn or the bots at start, or the van's frame-0 position is close to them, so the action fires before the first call. Stock vans 02 and 03 sit where nothing fires.
   - I did not measure overlaps.
   - The draft's spawn-distance scan used crude name matching, and I drop it as unreliable.
5. GUESS: with one van, visit 2 reuses the same action after state 0 or 7 cleared `1e0`. That would explain "visit 2 works".
6. GUESS: the relay count and van count may feed which handle the rules object finds in slot 89 (DD07 monitor 3 relays versus 1 here). No code path was read.

**Suggested next checks (read-only, unchanged)**
- Compute the world position of the BoardingTrigger in the failing three. It is the van's rest transform plus local `(-1.75, 119.35, -337.14)`, through the van's rotation. Compare it with the spawn rows and bot parking spots.
- Use the klmove hardware write-watch on `[rules+0x1e0]` (already proposed in `re/escape_visit1.md`) to see the action's fire time against the van's animation time.
- Optional A/B: in one failing map, set the PlayerAction's active bool (the bool right after `EnterVehicle`) to 0 at load. If `EscVisitFix` is then not needed, the early fire is confirmed.