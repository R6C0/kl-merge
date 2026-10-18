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