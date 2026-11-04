# [S+0x6fc] writers, 0x7f6850, list A (research wzerqnft4, 2026-11-04)

Static only. Research report, then the adversarial verifier's corrected table (the verifier wins on conflicts).

# Report: `[S+0x6fc]` writers, `0x7f6850`, and list A for the online marked bot

Static research only. I didn't launch the game or write to the game folder. I used `debug/dasm.py`, a full `.text` sweep (0x401000..0xb0fe30, 2.54M instructions, capstone resync on bad bytes) and the hash ranges in `klhook/klranges.h`.

Confidence tags are H (read in disassembly), M (inferred) and GUESS.

## Corrections to the brief and earlier notes

1. **`[S+0x6fc]` is a byte, and list A needs it nonzero.** At 0x85f896:
   ```
   85f896 cmp byte [eax+0x4fc],0
   85f89d je  0x85f8ac            ; flag=0
   85f89f cmp byte [eax+0x6fc],0
   85f8a6 mov byte [ebp-1],1      ; mov leaves ZF alone
   85f8aa jne 0x85f8b0            ; 6fc!=0 -> flag stays 1
   85f8ac mov byte [ebp-1],0
   85f8b4 lea ebx,[eax+0x610]     ; B
   85f8bc lea ebx,[eax+0x604]     ; A, only if flag
   ```
   List A is walked only when 4fc is nonzero AND 6fc is nonzero. The "6fc==0" wording in the `re/approach_lever_1104.md` verifier section and in `re/holder_b0_1104.md` is wrong. This matches the klbrain.c CombatFlag comment (mode 2). (H)

2. **ZCloseIn is NOT gated by `0x7f6850`. It is built unconditionally.** The ZSoldier setup function 0x6ab250 runs this sequence:
   ```
   6ab39e push 0x24 ; call 0x89e850          ; alloc
   6ab3b1 call 0x68eab0                      ; base ctor
   6ab3b6 mov [edi],0xbd0c64                 ; ZCloseInTactic vtable
   6ab3c9 mov [esi+0x590],edi
   ```
   - It is null only if the allocation fails.
   - The `0x7f6850` gates at 0x6ab57c, 0x6ab5d6 and 0x6ab628 guard Loot `[+0x5f0]`, Board `[+0x5f4]` and Traitor `[+0x5f8]` only. They also require team 0 or 2.
   - So online, `[S+0x590]` is non-null and ZCloseIn is in list A. (H, static)
   - I read no live `[S+0x590]` value; the CloseInProbe has not been run yet.

## Q1. Writers of `[ZSoldier+0x6fc]`

I swept every instruction whose operand ends in `0x6fc]`. Only four direct byte stores target a ZSoldier brain (the first three set it to 1):

| Site | Function | Value and condition |
|---|---|---|
| 0x7b3991 | `ZSquadScript` slot 14 (vt 0xbcce3c), 0x7b3790 | `mov byte [S+0x6fc],1` when `[squad+0x30]==1`, i.e. attitude `eUnleashed` (field 0, `eStayBack`=0, `eUnleashed`=1). This is the member-join path, right after `[S+0x4f4]=squad` at 0x7b3966. (H on the store, M on the field mapping) |
| 0x578d3b / 0x578d93 | `ZSquadModBehaviourGoal` run, 0x578ce0 (vt 0xbcee2c) | Logs "SquadModifier: Unleash" and writes 1; logs "Leash" and writes 0. Fires per member of the modifier. This is the only code that ever writes 0 after construction. (H) |
| 0x5a3a03 | `ZAmbushGoal` run, 0x5a3430 (vt 0xbd11f4) | After `RunChild` 0x521350, if the done-check 0x55b9f0 returns false it writes `[S+0x6fc]=1`. Only the store and its condition are read. What "ambush sprung" means is GUESS. |
| 0x761b30 | ZSoldier ctor 0x761900 | `mov byte [esi+0x6fc],al`, with al = 0 from `xor eax,eax` at 0x76190f. So the initial value is 0. (H) |

- Other hits are not writes to a ZSoldier. They are stack slots (0x42ac5c, 0x84f94c and others) or reads of other classes (0x65efa5, 0x7cc2ce, 0x81ffd6, 0x881859). `lea ecx,[esi+0x6fc]; call 0x8f7eb0` at 0x761320 is in function 0x7612d0, a different class (vt 0xbbe9a0, base 0x5e8540). (H)
- `0x7d0310` (unhashed) stores `lea edx,[eax+0x6fc]` into `[edi+0x4e4]`, part of a table of pointers to 12-byte member groups at S+0x6c0, 0x6cc, 0x6d8 and so on. I did not trace who writes through that pointer. GUESS: a variable-binding or property table. Residual risk: an indirect writer I did not trace.
- All writer sites above are in HASHED ranges, so no detours there. A data write to the heap byte is fine. (H)

**What makes it nonzero in Arcade:** an `eUnleashed` squad (0x7b3991), a SquadModifier Unleash step (0x578d3b), or a sprung `ZAmbushGoal` (0x5a3a03).
- `re/bots_dynamic.md` says stock F08 has all seven bots `eUnleashed`.
- Our generated bot squads are `eStayBack`/`eHeistOnly` (`tools/kl_fa_bots.py` line ~106). So 6fc is 0 for them unless a modifier step or ambush fires. (M)

**Online gating of the writers:**
- None of the four writers tests the net role directly.
- 0x7b3790 can drop the member (vcall `+0x54`, then `jmp 0x7b39ff`, skipping the store) on four mode and mask tests, three of them networked-and-mode-specific. Squads of mask 8 (`eHeistOnly`) are removed online unless `[squad+0x34]` bit 1 is set (0x7b37d1..0x7b37f0).
- A kept member passes through 0x7b3963 and gets 6fc=1 if its squad is Unleashed, on the same code path online.
- So online 6fc is 0 mainly because our squads are `eStayBack`, not because of a role check. (M)

## Q2. What `0x7f6850` tests, and list A

**What it tests (H):**
```
7f6850 mov ecx,[0x168e598]      ; sm, the session manager
7f6856 mov eax,[ecx+0x54]       ; role
7f6859 cmp eax,3 ; ja 7f6865
7f685e jmp [eax*4+0x7f6874]     ; raw dwords: 0x7f6865, 0x7f6865, 0x7f686e, 0x7f686e
7f6865 cmp [ecx+0x5c],4 ; jne -> 0
```
- Roles 0 and 1 return `[sm+0x5c]==4`. The default (role above 3) returns `[sm+0x5c]==4` too. Roles 2 and 3 (host, client) return false.
- Not true in an online FA host (role 2), so Loot, Board and Traitor are not built there.
- `0x863a60` is the sibling that returns true for roles 2 and 3 and false otherwise.
- The marked traitor works online only through the hook's shadow frame (`re/arcade_brain_shadow_1102.md`).

**ZCloseIn online:** `[S+0x590]` is non-null (see correction 2).

**List A membership (H):**
- ZCloseIn is a member of list A. The push at 0x6abda9 (`mov ecx,[esi+0x590]` … `mov [eax],ecx`) is unconditional, with no `test`.
- The order around it is `…, [+0x5b8], [+0x590], [+0x598], …, Loot`.
- The only other `+0x590` read in the ctor range is the store at 0x6ab3c9.
- It is not in list B (0x610) or list C (0x61c); the only `+0x61c` hits are at 0x6ac50f and 0x6ac51b (list C).
- Defend (0x85f6c0) runs the first tactic in the chosen list whose eval is above the threshold (`re/boardall_review_exe.md`). The order of NoCover relative to CloseIn inside A is still unread. GUESS (open): if NoCover precedes CloseIn, the through-wall firing risk stays.

**Meaning of the two bytes (M):**
- `ZAttackNoCoverTactic` run (0x7b1550) sets `[S+0x4fc]=1` at 0x7b162c once it has reached its spot. So 4fc is roughly "arrived".
- 6fc is "unleashed". Together they mean "arrived and unleashed", and only then does Defend consider the aggressive list A.

## Q3. Minimal data-only lever (no hashed detour)

Write byte `[S+0x6fc]=1` together with `[S+0x4fc]=1`, for the marked bot only, while every human is LOS-blocked. That is exactly the case that never occurs online, because 6fc is 0 there.
- The current `OnlineBrainTraitorCombatFlag` mode 2 only writes 4fc when 6fc is already nonzero. Online 6fc is normally 0, so mode 2 likely does nothing. Mode 1 (write only when 6fc==0) does not satisfy the 0x85f89f test either.
- The fix is to extend the lever to set both bytes: set 6fc=1 in the same write, remember it, and restore it to 0 (the stock value) whenever the 4fc undo runs. (H on the mechanism, GUESS on the outcome.)
- The holder `[S+0xb0]`, the `HolderSet` lever, must still be live. ZCloseIn's remaining gates are in `re/approach_lever_1104.md`: timer `[tactic+0x14]`, distance greater than `[S+0x6a8]`, and a nav path longer than 1 node.

**Side effects of 6fc=1 with 4fc=1 (H on the reads, GUESS on the effects):**
- `ZAttackNoCoverTactic` run: the 0x7b1565 branch jumps to 0x7b1633, skipping the "walk to cover and attack position" block.
- Cover search `0x807c60` at 0x807de8 gets a "both set" flag (al=1). I did not read what it does with it.
- `SwatCloseIn` reads 6fc at 0x7e576a. Not read.
- The byte is a heap byte of the brain object, so a write is safe from a SHIP-integrity point of view. (M)

**Alternative (GUESS, not recommended):** set the squad attitude `[squad+0x30]=1` before the members join. That only works if the slot-14 pass runs after our write, and a late write misses it.

## Probe to confirm (read-only, existing `CloseInProbe`)

Log `[S+0x590]` non-null, and `[S+0x6fc]` and `[S+0x4fc]` bytes, for the marked bot online. Expected: `[S+0x590]` non-null, 6fc 0, 4fc intermittent.

## Files read

- `C:\kl-merge\kl-merge\re\holder_b0_1104.md`
- `C:\kl-merge\kl-merge\re\approach_lever_1104.md`
- `C:\kl-merge\kl-merge\re\arcade_brain_online_1102.md`
- `C:\kl-merge\kl-merge\re\arcade_brain_shadow_1102.md`
- `C:\kl-merge\kl-merge\re\arcade_online_parity.md`
- `C:\kl-merge\kl-merge\re\bots_dynamic.md`
- `C:\kl-merge\kl-merge\klhook\klranges.h`
- `C:\kl-merge\kl-merge\debug\dasm.py`

## Verifier

**Corrected report: `[S+0x6fc]` writers, `0x7f6850`, and list A (static disassembly only, game not launched)**

| # | Claim | Verdict |
|---|---|---|
| 1 | Defend at 0x85f896..0x85f8bc walks list A (`[S+0x604]`) only when byte `[S+0x4fc]`!=0 AND byte `[S+0x6fc]`!=0; otherwise list B (`+0x610`). The "6fc==0" wording in `re/approach_lever_1104.md` and `re/holder_b0_1104.md` is wrong. | CONFIRMED. The `mov [ebp-1],1` leaves ZF alone, so `jne` tests the 6fc compare. `klbrain.c` (CombatFlag mode 2) already agrees. |
| 1b | Defend runs the first tactic in the chosen list whose eval is above a threshold. | CONFIRMED. At 0x85f8f0..0x85f924 it calls vcall `+0x2c`, does `fcomp [0xb69b98]` and `test ah,0x41`, and takes the tactic when eval > threshold. The first passing tactic is run. |
| 2 | ZCloseIn is NOT gated by `0x7f6850`. | CONFIRMED. ZSoldier setup 0x6ab250 reaches 0x6ab39e unconditionally. The only branches before it are inside the function's early-setup block; the `je 0x6ab39e` at 0x6ab307 jumps to it. The tactic is allocated and the vtable 0xbd0c64 (`ZCloseInTactic`) is stored. `[S+0x590]` is stored at 0x6ab3c9 and is null only if the allocation fails. |
| 2b | The `0x7f6850` calls at 0x6ab57c, 0x6ab5d6 and 0x6ab628 guard Loot `[+0x5f0]`, Board `[+0x5f4]` and Traitor `[+0x5f8]`, and also require team 0 or 2. | CONFIRMED. Each call is followed by a team test of 0 or 2. The vtables stored are `ZLootTactic` (`+0x5f0`) and `ZBoardEscapeVehicleTactic` (`+0x5f4`). I did not read the vtable for `+0x5f8`; it is assumed to be the Traitor tactic. |
| 3 | `0x7f6850` reads the role at `[sm+0x54]` through the jump table at 0x7f6874. Roles 0 and 1, and any role above 3, return `[sm+0x5c]==4`. Roles 2 and 3 return false. | CONFIRMED. The table dwords are 0x7f6865, 0x7f6865, 0x7f686e, 0x7f686e. 0x7f6865 is the compare and 0x7f686e is `xor al,al`. So it is false in an online FA host (role 2). |
| 4 | `0x863a60` is the sibling that returns true for roles 2 and 3. | UNVERIFIED. I did not disassemble it. It is called at 0x7b37d1 in the squad join path. |
| 5 | Direct byte writers of ZSoldier `+0x6fc`: 0x7b3991 (=1), 0x578d3b (=1), 0x578d93 (=0), 0x5a3a03 (=1), 0x761b30 (ctor, =0). | CONFIRMED. My byte scan over `.text` for `fc 06 00 00` found exactly these byte stores; every other hit is a dword access, a `lea` or a stack slot. |
| 5a | 0x7b3991 runs when `[squad+0x30]==1`, right after `[S+0x4f4]=squad`. | CONFIRMED. `cmp [ebx+0x30],edi` uses edi=1 (set at 0x7b3886), followed by the store at 0x7b3991. The attitude names `eUnleashed` and `eStayBack` are UNVERIFIED (inferred from field 0 and `re/bots_dynamic.md`). |
| 5b | 0x578ce0 logs "SquadModifier: Unleash" and writes 1, or logs "Leash" and writes 0. It is the only writer of 0 after construction. | CONFIRMED. The string pushes at 0x578d26 and 0x578d7e and the stores at 0x578d3b and 0x578d93 match. |
| 5c | 0x5a3a03 is in `ZAmbushGoal` run. It stores 1 when the done-check 0x55b9f0 returns false. | CONFIRMED as code (call 0x521350, call 0x55b9f0, `test al,al`, `jne` skips the store). The class name is UNVERIFIED and the meaning is GUESS. |
| 5d | The ctor value is 0 because al=0 from the `xor eax,eax` at 0x76190f. | CONFIRMED. No instruction between 0x761917 and 0x761b30 writes eax. The only register change is `mov cl,1` at 0x761a37. |
| 6 | There is no indirect writer; `7d0310` merely holds `lea edx,[eax+0x6fc]`. | UNVERIFIED. The `lea` at 0x7d0517 is real, but I did not trace who writes through it, so a script-variable binding writer is not excluded. The `lea` at 0x761320 is in 0x7612d0, a different class. |
| 7 | Online 6fc stays 0 mainly because our squads are `eStayBack`/`eHeistOnly`, not because of a role check. | UNVERIFIED. This is inference. No writer tests the role directly, which I confirmed. Only 0x7b3790 has role/mask tests that can drop a member before the store (0x7b37d1..0x7b37f2, 0x7b3805..0x7b3819). |
| 8 | ZCloseIn is in list A with an unconditional push. | CONFIRMED, but not at the address cited. The code at 0x6abda9 is a `std::vector` push_back into the vector at edi, which the code builds as `lea edi,[esi+0x604]` at 0x6abb6f; there is no null test. The push order in the A build (0x6abb6f..0x6abede) is 0x6d8, 0x600, 0x5fc, 0x5fc, 0x5ec, 0x5dc, 0x5f8, 0x5f4, 0x5ac, 0x5bc, 0x5b8, 0x590 (ZCloseIn), 0x598 (SwatCloseIn), 0x59c, 0x5c0, 0x5b0, 0x5f0. The list B build starts at 0x6abede with `lea edi,[esi+0x610]`. I did not enumerate B's contents, so "ZCloseIn is not in B" is UNVERIFIED. |
| 8b | The order of NoCover versus CloseIn in list A is open. | RESOLVED. `ZAttackNoCoverTactic` is built by the call to 0x672000 at 0x6ab4bf and stored at `[S+0x5b0]`. In list A it comes after ZCloseIn (`+0x590`). Three entries precede both: `+0x5ac`, `+0x5bc` and `+0x5b8` (unidentified). A NoCover-fires-first risk therefore applies only if one of those three passes first. |
| 9 | `ZAttackNoCoverTactic` run (0x7b1550) stores `[S+0x4fc]=1` at 0x7b162c. When both 4fc and 6fc are nonzero, 0x7b1565 jumps to 0x7b1633. | CONFIRMED for the store and the branch. "Once it has reached its spot" is UNVERIFIED. |
| 9b | Other users of 6fc: cover search 0x807c60 (`cmp [ecx+0x6fc]` at 0x807de8) and SwatCloseIn 0x7e56d0 (read at 0x7e576a). | CONFIRMED that the reads exist. Their effects are unread. |
| 10 | The current CombatFlag mode 2 only writes 4fc when 6fc is already nonzero, so it is likely a no-op online. Mode 1 does not help either. | CONFIRMED against `klbrain.c` (modes at lines 2731 and 4247). Mode 1 writes only when 6fc==0, which still fails the 0x85f89f test. Whether 6fc is actually 0 online is UNVERIFIED, since the probe has not run. |
| 11 | `ZCloseIn` also needs the other gates in `re/approach_lever_1104.md` (timer, distance, nav path) plus a nonzero holder `[S+0xb0]`. | UNVERIFIED. I did not re-read those gates this round. |

**Endorsed lever.** A data-only change to the existing CombatFlag. When every human is LOS-blocked, write both `[S+0x4fc]=1` and `[S+0x6fc]=1` (a new mode 3). Remember that we set 6fc, and write it back to 0 (the ctor value) whenever the existing 4fc undo runs. This is safe to apply: the bytes are heap data in a hashed range and no detour is needed. It must be combined with HolderSet, because ZCloseIn also needs `[S+0xb0]` nonzero. Whether it makes the bot approach is GUESS.

Run the read-only CloseInProbe first. It logs 4fc and 6fc, which should confirm that 6fc is 0 online, and `[S+0x590]`, which should be non-null. The three untraced list-A entries (`+0x5ac`, `+0x5bc`, `+0x5b8`) and the untraced writer of 6fc are the residual risks.
