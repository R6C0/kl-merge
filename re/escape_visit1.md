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

## 2026-10-18: where the van's boarding box sits before the call

Units are cm (box half extents 95 x 135 x 80 = the 1.9 x 1.6 m box). Scratch scripts are in the session scratchpad (`ex.py`, `van.py`, `stop.py`, `b.py`, `inb.py`). They use `kl_scene`, `kl_graft.keys_tracks`, `kl_map_escape.VanKeys`, and `kl_fa_bots.Built`, `Nav` and `stations`. Nothing was written to the repo or the game folder.

**Method**
- FACT: for each map I took `V_Van_00`'s stored translation and the box's local offset `(-1.75, 119.35, -337.14)`.
- FACT: the stored 3x3 matrix has its axes permuted (determinant -1). Its row 0 is the van's nose (the quaternion's local +Z), and row 2 is local X.
- FACT: I rotated the offset with the animation's frame-0 quaternion, not the stored matrix. That is the same convention `kl_map_escape.van_prepare` uses.
- FACT: key 0's position equals the stored translation to 0.1 in all four maps, and its heading equals the matrix's.
- FACT: the rest transform and frame 0 give the same box position, so (a) = (b).
- FACT: frame 795 returns to the frame-0 pose. The van sits at that pose until `Activate_Enter` (frames 50..230) drives it in.

**Box centre in world space**

| map | (a) = (b) at rest / frame 0 | at the stop (`Activate_Enter` last frame) | rest to stop, plan |
|---|---|---|---|
| DM06B (F02) | (-6498.5, 2508.2, -5216.6) | (-2571.9, 2625.3, -7932.3) | 47.8 m |
| DM03A (F07) | (-3578.2, 821.3, -11791.1) | (635.5, 821.4, -11228.9) | 42.5 m |
| DM01B (F03) | (5697.1, 106.3, 30799.7) | (2000.1, 106.3, 30793.0) | 37.0 m |
| DD07 van 01 (control) | (6024.1, -79.0, 25950.9) | (9257.2, -78.7, 23624.1) | 39.8 m |

**Distances from the rest box, in metres (plan distance; 3D is within 1 m of it except where noted)**

| to | DM06B | DM03A | DM01B | DD07 v01 |
|---|---|---|---|---|
| nearest START spawn row | 103.1 | 83.2 | 271.8 | 226.9 |
| START rows' middle | 104.3 | 85.2 | 272.9 | 228.1 |
| nearest hero spawn (`Heroes!*\Ground`), 3D | not near | 24.1 (Henchmen_08) | not near | not near |
| nearest ZSpawnPoint of any kind | 86.1 (Merc FinancialAlley) | 24.6 (TEAM_Police#01) | 62.9 (Dead/Police) | 80.1 |
| `OnlineExitLevelTrigger` box middle (half extents) | 47.8 (4.5 x 3 x 4.5) | 40.7 (15 x 3 x 11.5) | 37.0 (4.5 x 3 x 4.5) | 48.2 (35 x 9.5 x 36) |
| escape-area POI box and `AllyEscapeBox` | 47.8 / 48.9 | 40.7 / 39.6 | 37.0 / 37.2 | POI 115, no AllyEscapeBox |
| nearest guard | 20.4 | 27.3 | 15.0 | 61.5 |
| nearest loot object | 33.9 | 38.3 | 51.1 | 189 |
| nearest bot squad place (`merc_bot_squad`) | 46.0 | 36.9 | 10.2 | 31.7 |

- FACT: no entity has a position inside the rest box in any of the four maps. I tested every node, at its feet and 90 above, with the box padded by 0, 1 and 3 m.
- FACT: the rest box is not inside the exit trigger box in the three Dead Men maps.
- FACT: DD07 van 02's rest box is inside the huge exit trigger (centre 40.8 m away, half extent 35 m), and that stock map works. Overlap with a trigger is therefore not what separates failing from working maps.
- GUESS: I treated the `merc_bot_squad` child positions (all squads, every stage) as the AI heister spots. I found no per-map bots ini with spots in `tools/` or in the map folders, only the `bots.json` plan that `re/bots_move.md` mentions.
- GUESS: the "nearest" figures include the squad Pos boxes, and DM01B's 10.2 m figure is a `Pos#01` box of Squad#04's `050_DefendBehaviour_way_b_b`.

**Reachable on foot before the call**

| | DM06B | DM03A | DM01B | DD07 v01 |
|---|---|---|---|---|
| nav points inside the rest box (5x5 grid, any part) | 25 of 25 | 25 of 25 | 25 of 25 | **0** |
| on the START row's mesh part | yes | yes | yes | n/a |
| walk from the START rows' middle (nav portal path) | 327 m | 138 m | 354 m | none |
| nearest walkable polygon middle, plan | 2.5 m | 1.2 m | 2.9 m | 24.9 m |
| box height above the START rows | +18.7 m | +6.2 m | +1 m | -6 m |

- FACT: in the three Dead Men maps the rest box sits on the START row's mesh, so a walker can stand in it. On stock DD07 it sits off the mesh, about 25 m from the nearest walkable polygon. Vans 02 and 03 are also off the mesh.
- GUESS: the mesh grid and the portal-path length are approximate. `Nav.dist_map` walks through edge middles and the box grid is coarse.
- GUESS: the walk distances are far longer than the straight lines (327 m against 104 m on DM06B) because the box is on the elevated road.

**Verdict on the GUESS "the box at rest fires EnterVehicle early"**
- Static overlap at load: **REFUTED**. Nothing stands in or within 3 m of the box at load. The nearest START row is 83 to 272 m away, and the DD07 control has a similar spread (227 m). Nearest hero row, guard and bot place are all at least 10 m away.
- The early write of `[rules+0x1e0]` comes about 1.3 s before state 1, when every human is still 83 m or more from the box. That does not fit a human walking into it.
- GUESS: the early write is the `EnterVehicle` action registering when it is activated, not a box overlap. The rest-position hypothesis alone does not explain it.
- Still open, and not excluded by this check: a bot or cop walking through the box before the call. The only difference from stock I can show is that the box sits on walkable mesh in the three failing maps and off it on DD07. That would make an early fire possible but needs a walker.
- Next test (not run): the hardware write-watch on `[rules+0x1e0]` already proposed in `re/escape_visit1.md`. The optional A/B of setting the action's active bool to 0 at load is the other cheap check.

## 2026-10-18: Hot Coffee II van boarding spot vs the nav mesh

Re-checked read-only with `kl_route.load().mesh()` on the installed DM01B `F03_Main.zip`, using the scratchpad scripts q1, q2, q3 and q4. The mesh claims reproduce. The route-walker claims were not reproduced and are downgraded. The proposed STOP at x 3000 has a drawback the first report left out.

### (1) Is the target on the mesh?
- **FACT, reproduced.** The mesh has 1103 polygons in 43 parts, and part 0 holds 838 of them. START polygon 933 is in part 0.
- **FACT, reproduced.** (2011, 0, 30793) is inside polygon 301, in part 0, at mesh height 0.0 and distance 0.
  - y = -15 and y = 107 give the same polygon at distance 0, so the y level does not affect the lookup.
  - STOP (2000, -13, 30800) and the rear point (2000, -15, 30800) are also in polygon 301.
- **FACT, reproduced.** Polygon 301 has six vertices and spans x 1481..2512 and z 28567..31049.
  - The nearest boundary edge (one with no neighbour) is 236 units away, at the north side near z 31030.
  - The margin to the north edge falls as z increases (z 30900: 129; z 31000: 30).
  - The south side of 301 is open to z 28567.
- **NOT REPRODUCED, downgraded to GUESS.** "The street y of -15 is the collision floor" and "at y = 107 the walker finds no floor within 100". These come from the collision walker, which I did not get an answer from.

### (2) Is it connected to where the crew comes from?
- **FACT, reproduced.** `Mesh.way(933, 301)` routes only if the minimum portal width is 4 or less.
  - At the default 100, and at 40, 60 and 80, there is no route.
  - The widest minimum that still routes is 4.
  - The route is 130 polygons (134 points) and 37,426 units long. That is about 374 m, if 1 unit is 1 cm.
- **FACT, reproduced.** The 4-wide portals are 571/587 at (2866, 0, 11742) and 587/588 at (2866, 0, 11777).
  - The next narrowest are 29 at (4655, 0, 22100), 35 at (4093, 0, 21900) and 41 to 43 at (4731, 0, 22100) and (6100, 0, 23055..23155). Several of the route's 29..43-wide portals are in the same area.
  - All of them are 7 km or more from the van.
- **FACT, reproduced.** The last stretch is wide: 296/301 is 1877 wide, 301/316 is 894 and 301/298 is 832.
- **FACT, reproduced.** The z 30800 lane from x -500 to 6500 is all part 0, in polygons 296, 301, 318, 321, 252 and 251.
- **NOT REPRODUCED.** The claim "no one-way links used". `way(..., links=True)` returns None at the default width, so it was never tested on this route. Downgraded to unknown.
- **NOT REPRODUCED.** The `kl_route stations` result ("on the mesh, part 0", "NOT reached", the blockers named at 22 to 261 m). My rerun produced no output in 500 s. The collision-walker part, including the named blockers and the closed-door explanation, is unverified. The first report's "not reached" is consistent with closed doors only as a guess.
- **Still not done.** No collision walk of the last 20 m exists. The `--open` rerun from x 1300 is still needed.

### Verdict on the mesh
FACT: the mesh does not explain the bots' failure. The target is on a connected, wide, central part-0 area. There is no mesh reason to move the STOP.

### What could explain it (all GUESS, unchanged)
- The box is about 11 units east of STOP. `re/escape_visit1.md` gives the stopped box at (2000.1, 106.3, 30793.0).
- With heading -90, the van body spans roughly x 1400..1900. A bot 5 m west of the target is inside that footprint.
- The van is a dynamic obstacle that is in neither the mesh nor the static collision.
- An arrival test that needs a closer approach than the body allows would produce the same stall.

### (3) Alternative STOP, only if the van body is the blocker
The table reproduces exactly (z 30793). The squad positions are the men and cover points of the `ARRIVE` table at `kl_fa_v2_hotcoffee.py:240` (the anchors are not in q4's list; none are nearer to the lane than the men).

| Box x | Polygon / part | Distance to mesh edge | Distance to nearest squad position |
|---|---|---|---|
| 1000 | 296 / 0 | 545 | 1416 |
| 1500 | 296 / 0 | 254 | 1715 |
| 2000 | 301 / 0 | 235 | 2047 |
| 2500 | 318 / 0 | 311 | 2116 |
| 3000 | 321 / 0 | 313 | 1797 |
| 3250 | 321 / 0 | 314 | 1671 |
| 3500 | 321 / 0 | 315 | 1559 |
| 4000 | 321 / 0 | 317 | 1386 |

- **Correction to the x 3000 proposal.** The first report said the margin is "a little better". The margin figure does reproduce (313 against 235), but the mesh around x 2750..3500 is narrower than at x 2000.
  - For x 2750 to 3500, z 29000 to 30400 is mostly off the mesh, or in small separate parts such as 793..819 and 234.
  - At x 3000 the walkable strip is only about z 30500..31200, roughly 600 wide. At x 2000 the street is open south down to z 28567.
  - So x 3000 trades the open south side for a slightly larger north margin. It does not clearly make the van easier to get round.
  - The proposal stays untested. The road collision east of 2500 has also not been checked.
- **Cheaper test first.** Keep STOP and move the crew's order point.
  - Candidates are (2150, 0, 30793), 150 east of the box, or the north side of the lane at z 30950.
  - 30950 is tighter: the margin there is about 80..130 at x 2011, and about 100 would remain.
  - (2150, 30793) was not checked here. It lies in polygon 301, because 301 spans to x 2512 at z 30482 and the lane edge at x 2150 is further north than the north polygon edge at z ~31020.

### Not done
- The final-stretch collision walk (`kl_route walk`/`stations` from x 1300, with `--open` and `ROUTE_OPEN` from `kl_fa_v2_hotcoffee.py`) is not run.
- The collision-floor heights at y -15 and 107 are not checked.
- The one-way-link question is open.

Scripts: `q1.py` to `q4.py` in `C:\Users\Henri\AppData\Local\Temp\claude\c--kl-merge-kl-merge\d20b026f-6c1c-42c8-8d9e-2f96a87bb38d\scratchpad\`.
## 2026-10-18: Hot Coffee II L70 (3f, live): BoardReachFlat=1 makes visit-1 boarding work
HC 0765d90a + hook out_e5_1018s + the L69 ini + `[Bots] BoardReachFlat=1` (BoardReach=100): RESULT PASS, 0 asserts.
EscVisitFix fired on visit 1 (in state 2; 1e4 set). Rec 6 and traitor rec 4 boarded on visit 1 (L69 without Flat: 0).
CrewRouteHold held one walker 10.8 m off for 45 s; the van took 8704/9600 health. Of the other five, three were dead
and two were in play at heist stage 1/2 with $0 (never called). After LastVehicleFlagged every box works as in stock,
so Flat matters only until then. The full opt-in stack (EscVisitFix + CrewRouteHold 45 / CrewRouteRange 100 +
CrewRouteAlone + BoardReachFlat) has now passed visit 1 on the Vault (L65), Park II (L68) and Hot Coffee II (L70).
Adopting it into the owner's hook and ini is the owner's call.


## 2026-10-18: what fires EnterVehicle early (static, workflow wajm2i405, verified 19 of 24)

VERIFIED: 19 of 24 claims held

# Who calls ZPlayerAction slot 26 ('EnterVehicle') before escape state 1

Every address below was re-read in the kl2.exe disassembly. GUESS means the code does not show it. NOT RE-READ means it is level data or a scan this pass did not repeat.

## 1. Callers of 0x65ee60 and slot 26 (FACT, re-verified)
- 0x65ee60 is `if ([ecx+0x1e0]==0) { [ecx+0x1e0]=arg; return 1 } else return 0`. A call scan of .text finds exactly two callers, 0x7fdc9a and 0x7fdd3a. Both are inside 0x7fdbb0. No data pointer to it exists.
- 0x7fdbb0 is ZPlayerAction slot 26 (vtbl 0xbc29ec, cell 0xbc2a54, `ret 8`). Its only reference is that vtable cell.
- At both call sites ecx is `0x508ef0([0x168e9e4])`, and the pushed argument is `[esi+0x24]`.
- 0x508ef0 returns `[[0x168e9e4]+0x54]` only when `[[0x168e598]+0x5c]==4` and 0x7f6850 passes.
- `[esi+0x24]` is the controller's owner entity in other controller classes. For PlayerAction this is an inference (GUESS).
- The "454 hits for `call [reg+0x68]`" scan was NOT RE-READ. It adds nothing, because the dispatch chain below is what matters.

## 2. Dispatch path, trigger to action (FACT, re-verified)
1. ZGROUP and ZBoxPrimitive both have vtbl+0x12c = 0x523310. It resolves the target through 0x796ff0 on `[0xe0ff90]` and calls the target's vtbl+0x130 as (id, extra, sender).
2. ZBoxPrimitive's 0x130 is 0x7da000, which does `jmp [vtbl+0x120]`. That is 0x787250.
3. 0x787250 calls vtbl+0x164 and then vtbl+0x11c as 0x446010(0x20, extra, id, sender).
   - Which function is vtbl+0x164 was not resolved. 0x547000 (`xor eax,eax; ret 8`) is only a guess for it.
4. 0x446010 first checks `0x758da0([this+4])`. If that fails it returns without delivering.
   - It then walks controllers via `[0xe0ff88]` and 0x8190b0. It delivers only if `[ctrl+0x20]==0`, `([ctrl+0x18] & mask)!=0` or mask is 0x20, and `[ctrl+0x21]` is in 1..5. It calls the controller's vtbl+0x6c (slot 27).
5. Slot 27 is 0x617590 for ZPlayerAction, ZActivateGeom, ZDeactivateGeom and ZOnlineEscAnimatedVehicle. For code 0x20 it calls vtbl+0x68 (slot 26) with (id, extra).
   - Codes 8, 0x10 and 0x1000 go to slots 24, 25 and 31.
   - The sender is dropped, so the action cannot know who triggered it.
6. ZGROUP's vtbl+0x130 is 0x41a4a0. It runs its own vtbl+0x120 (the controllers on the group itself). It then walks the child list (`[this+0x40]`, sibling index at +0x5e) and calls each child's vtbl+0x130, so the broadcast reaches the whole subtree.
7. The level-data statements are NOT RE-READ this pass: the ancestors EscapeVehicle_Animation_F07, F07_Escape_Vehicle_01 and V_Van_00 being ZGROUP, and BoardingTrigger being a ZBoxPrimitive. re/escape_visit1.md has the ZBoxPrimitive part.

## 3. Conditions inside slot 26 (0x7fdbb0) (FACT, corrected)
- **The `[esi+0x7c]` gate covers all three messages, not only the firing ones.** 0x7fdbb3 does `cmp [esi+0x7c],0; je exit` before any id compare. The constructor sets it to 1 (0x8e934a).
- Message-id globals, names confirmed from their static registrations:
  - 0x16891a0 = 'AITrigger' (registered at 0x8e9392).
  - 0x168919c = 'Activate' (0x8e93b4).
  - 0x16891f0 = 'AIBlocker' (static object at 0x16891e8, created in 0xaf19c0).
- 'AIBlocker' clears +0x7c and +0x54. It also writes 0 to byte +0x64 of a table record (`[0xdd265c]+0x15e0 + idx*0x68 + 0x14`) when `[esi+0x98]` is not -1.
- 'AITrigger' sets +0x54 to (old==0), that is a toggle. 'Activate' sets +0x54=1. Both mirror the value into the same table record.
- After either message, it fires when all of these hold:
  - +0x54 is non-zero.
  - 0x7f6850 passes.
  - The string at `[[esi+0x50]+0xc]` equals 0xb50920, which is "EnterVehicle".
  - Then 0x508ef0 and 0x65ee60 run, at 0x7fdc9a for AITrigger and at 0x7fdd3a for Activate.
- **'Activate' alone is enough.** It fires regardless of the previous +0x54.
- **0x7f6850 is a session gate, not a pass-through.**
  - It reads `[0x168e598]+0x54`. Values 2 and 3 return false. Any other value falls through to `[+0x5c]==4`.
  - 0x508ef0 needs `[+0x5c]==4` as well.
  - So "nothing checks escape state, the actor or the player" is true for the heist escape state, the actor and the player. It is false in general: the session manager's state must be 4 (the round running).
  - It is not an obstacle at round start.
- The constructor does not set +0x54. The "starts active (b1)" claim comes from level data and rests on the field-to-offset pairing, which is not shown (GUESS). If it holds, the first AITrigger turns the action off and the second one fires.

## 4. Candidate senders
| Candidate | Evidence | Status |
|---|---|---|
| ZOnlineEscAnimatedVehicle slot 26 (0x518bf0) | Handles EnterAnimation 0x168c7f8, ExitAnimation 0x168c804, CrashAnimation 0x168c810 and Reset 0x168c834 (names confirmed). It sends the ids at `[esi+0x44]` / `[esi+0x46]` to the entity `[esi+0x60]` via vtbl+0x130 (broadcast). It also sends KILLBOX_ENABLE (0x168c81c) via the owner's vtbl+0x12c, and EnableFrameUpdate (0x168d6c8) via vtbl+0x120 to `[esi+0x68]`. | **The earlier "sends no plain Activate or AITrigger" is not supported.** The ids at +0x44 / +0x46 are level data and may be Activate or AITrigger (GUESS). It only runs on EnterAnimation, which arrives at state 1 or later, so it cannot be the early fire. |
| Heist slot 194, state 1 (0x8fa75f) | For vehicle kind 3 (`al==3` at 0x8fa78e) it sends Reset (0x168c834) via vtbl+0x130 at 0x8fa796 and EnterAnimation (0x168c7f8) via vtbl+0x120 at 0x8fa7ac. Other kinds send 0x168eb14 (ZMOVEMENT_MSG_RESET). | FACT. Neither message is Activate or AITrigger, and it runs at state 1, so it is ruled out as the early trigger. |
| ActivateGeom / DeactivateGeom controllers aimed at the van group | Mechanism now read, see below. | **Strongest candidate, upgraded from "mechanism unread".** |
| Other relays or triggers | The 0x86bc40 list-sender helper reads 0x16891a0 at 0x86bc7b (it sends AITrigger to a list). Owner class unidentified. | GUESS |

Level-data evidence (NOT RE-READ this pass, from the earlier read): ActivateGeom / DeactivateGeom controllers with message AITrigger target `EscapeVehicle_Animation_F07` in DM01B (entities 20617, 20619), DM06B (19071, 19073) and DM03A (21007, 21002). Stock DD07, DD04, DD05 and DD01 have only the OnlineExitLevelTrigger referencing that group.

Mechanism, now read (FACT):
- ZActivateGeom slot 26 (0x55c9f0) matches the message id against the words at `[esi+0x3a]` and `[esi+0x30]`. For each target in its list (`[esi+0x34]`) it calls 0x8ccde0(handle) and then `[0x168e598]->vtbl+0x20(entity, 0)`.
- ZDeactivateGeom slot 26 (0x824950) is the same shape. It matches `[esi+0x40]` or `[esi+0x30]` and calls vtbl+0x24 (0x62de80 on the Multiplayer class; not followed further).
- ZSessionManagerMultiplayer (vtbl 0xbd1ebc) has +0x20 = **0x7f77b0**. 0x7f77b0 calls 0x4c4900(entity, arg2). So 0x7f77b0 IS that slot. The earlier "treat as unrelated" was wrong.
- 0x4c4900 is also the base ZSessionManager's own +0x20 (vtbl 0xbd3fe4).
- With arg2 = 0, 0x4c4900 does the following if bit 10 of `[[ent+4]+0x3c]` is set:
  - It calls entity vtbl+0x58, +0x30 and +0x50(1).
  - It then **calls entity vtbl+0x130 with the word `[0x168ee34]`, which is 'Activate'** (static object 0xb03ef5).
- Sending 'Activate' (0x168ee34) to a group broadcasts down to BoardingTrigger's action. The action's slot 26 compares against 0x168919c, a separate registration of the same name. That the two ids are equal is inferred from both coming from the same name lookup (vtbl+0x4c), so GUESS-minus.
- So ActivateGeom hitting the van group very likely delivers 'Activate' to the EnterVehicle action. That sets +0x54=1, passes the gate and calls 0x65ee60. This is a static chain, still not observed live.
- Open assumptions:
  - `[0x168e598]` is the Multiplayer class in FA (constructed at 0x90ab5e under a condition not read). The Singleton class has a different +0x20.
  - The geom controller's target list contains the van group.
  - The controller actually fires about 1.3 s before state 1.

Leading hypothesis (GUESS, now mechanically supported): a "show/hide the van" geom controller fires at round start on the van group. That broadcasts 'Activate' and fires the EnterVehicle action early. Stock DD07 does not have the controller.

## 5. ONE opt-in klmove test: `[Bots] EnterVehicleTrace=1`
It needs no code patch. A heap-only vtable swap is allowed under the ship policy.
1. Model it on klmv_escvisit (klmove.c:1573) and klhp_scan_heap (klheliprobe.c:62). Once per level, heap-scan with VirtualQuery for dwords equal to 0xbc29ec.
2. Keep instances whose name is "EnterVehicle" and whose `[this+0x24]` is a ZBoxPrimitive.
3. Copy the vtable, replace slot 26 (+0x68) with a stub that logs and then jumps to 0x7fdbb0 (ecx and the 2 stack args kept, `ret 8`), and point the instance at the copy.
4. The stub logs the message id (compare with the globals 0x16891a0 / 0x168919c / 0x16891f0), `[this+0x24]`, `[this+0x54]`, `[this+0x7c]`, `[rules+0x1dc]`, `[rules+0x1e0]`, `[rules+0x1e4]`, and about 24 stack dwords that point into .text and follow a call.
5. How to read it:
   - Return addresses inside 0x55c9f0 / 0x4c4900 / 0x7f77b0 mean the Geom path. The fix to test is to retarget or remove those refs to `EscapeVehicle_Animation_F07` in DM01B, DM03A and DM06B.
   - Frames in 0x518bf0 or 0x8fa6d0 mean a van or heist-side sender.
   - Because slot 27 drops the sender and the stack is shallow, expect frames from 0x617590, 0x446010 and 0x787250, then the group's 0x41a4a0. The originator may only show in the deeper frames, so scrape deeper than 24 dwords.
   - An id that is neither AITrigger nor Activate means section 3 is wrong.
6. Optional A/B: write 0 to `[obj+0x7c]` until the state is at least 1. If `[1e4]` is then valid at state 1 without EscVisitFix, the early fire is the whole cause.

Files: C:\kl-merge\kl-merge\klhook\klmove.c, C:\kl-merge\kl-merge\klhook\klheliprobe.c, C:\kl-merge\kl-merge\re\escape_visit1.md.
## 2026-10-18: the ActivateGeom on the van group is OUR van hide/show (code read, not yet tested live)
All three failing maps hide the van's group (`EscapeVehicle_Animation_F07`) at load, and later show it with an
ActivateGeom whose target list is that whole group:
- the Vault: `kl_fa_bank.py` VAN_LATE + VAN_HIDE, `bank_waves!Clock\Van_show` (foyer box + 6 s, plaza box + 1 s, backstop);
- Park II: `kl_fa_v2_park.py` VAN_HIDE (`A.place(S, vg, hidden=True)`, shown by the alarm);
- Hot Coffee II: `kl_fa_v2_hotcoffee.py` 'van on' (`lists('van on', 'ActivateGeom', f1=[van_path()])`).
Stock DD07 never hides its van, and has no geom controller naming that group. In the chain above, ActivateGeom
-> 0x7f77b0 -> 0x4c4900 broadcasts 'Activate' down the group to `V_Van_00\BoardingTrigger`'s EnterVehicle action,
and 0x65ee60 stores the boarding object while the state is still 0. That also fits the measured "1e0 written about
1.3 s before state 1": the van is shown just before the exit trigger calls it. It also explains why the FakeTarget
looked related: taking it off and hiding the van are both part of VAN_LATE.
Data-side tests, none built yet (each needs a live A/B on the owner's hook, without EscVisitFix):
1. `--no-van-hide` (Park II and the Vault already have this flag): if [rules+0x1e4] is set at state 1 on visit 1, the
   cause is confirmed. Cost: the van stands in sight from the load (with its FakeTarget still off).
2. Show the van only AFTER the call (state >= 1): slot 89 has then already set 1e0, so the set-if-empty 0x65ee60 does
   nothing. GUESS: a hidden group can be called and animated, and is shown in time.
The hook fix (EscVisitFix, which clears 1e0 and re-runs slot 194) stays valid either way.
