# Fire-line goal path: 0x8f6990 / 0x8c1830 (2026-11-03, static only)

Static only (debug/dasm.py, capstone, kl2.exe build 0490, read-only; caller scan = full `E8`/`E9` rel32 scan of .text plus every dword in the non-.text sections).
Continues re/fireline_gap_1103.md. Anything not read from code is marked GUESS. Nothing was run, patched or committed.

## 1. What 0x8f6990 is
- Signature: `__thiscall`, `ret 8`. `this` (ecx, kept in edi) = object B (the same B as `[ZSoldier+0x698]`; `[B+0x154]` = the owning ZSoldier, `[[B+0x154]+0x40]` = its actor). Return: `al` (bool = the result of 0x5706a0; the epilogue 0x8f6a27-0x8f6a2c does not touch eax).
- Args (stack): `[ebp+8]` = `float *v` (a vec3, read at 0x8f6996-0x8f69aa and copied to locals `[ebp-0x18..-0x10]`), `[ebp+0xc]` = `DWORD *out` (passed unchanged to 0x5706a0 as its third arg, which fills it from 0x51bf80 at 0x5707dd; the caller reads it back).
- Body (0x8f6990-0x8f6a2c, no loop, no yield): builds the other end of the segment in a local vec3 `[ebp-0xc..-4]`: `0x7836b0(actor, -1)` (a lookup on `[[B+0x154]+0x40]`, what it finds: GUESS, a bone / attachment); if found and its vcall `+0x30` masked with `[0x1535218]` equals `[0x1535214]` -> `0x71c5d0(esi, &vec)` (fills the vec3), else zero vec3 + `0x7b3020([[actor]+4], &vec)` and z += qword `[0xb4be50]`. Then `push out; push &local(ebp-0x18); push &vec(ebp-0xc); ecx=edi; call 0x5706a0` (0x8f6a1c-0x8f6a22). A thin wrapper: "is a friend in the line from the soldier to v?".
- Prologue bytes: `55 8b ec 83 ec 18 8b 45 08`; the first three instructions are exactly 6 bytes (push ebp / mov ebp,esp / sub esp,0x18), position independent.

## 2. Callers
Full scan (no pointer word to either function anywhere in .rdata/.data/.bss, so NO vtable slot of any class holds them):
| target | call site | inside | note |
|---|---|---|---|
| 0x8f6990 | 0x5be061 | 0x5bdfe0 (thiscall, ret 8; early out at 0x5be02b when `[x+0x774]!=0`) | 0x5bdfe0's only caller is 0x76759b inside 0x767510. ZSoldier slot 113 (vtable 0xbd0954 + 113*4 = 0xbd0b18) holds the stub 0x47a0f0 (`ecx=[ecx+0x698]; jmp 0x767510`), so 0x767510's `this` is B, not the ZSoldier; 0x767510's only caller is that jmp. Already wrapped by klbr_w_fl113 |
| 0x8f6990 | 0x8c19c9 | 0x8c1830 | the GOAL path, not covered by 113/114 |
| 0x8c1830 | 0x4a92ad | ZFriendlyFireGoal 0x4a8f40 | vtable 0xbd1274, ptr at 0xbd127c = slot 2 |
| 0x8c1830 | 0x4eea26, 0x4eea69 | ZCoveredMoveActGoal 0x4ee860 | vtable 0xbd0ed4, slot 2 |
| 0x8c1830 | 0x4f4961, 0x4f4c9f, 0x4f4dc3 | ZAttackTarget 0x4f4460 | vtable 0xbd1104, slot 2 |
| 0x8c1830 | 0x515533 | ZAttackSniperTactic 0x515020 | vtable 0xbd0424, slot 2 |
| 0x8c1830 | 0x522749 | ZCoverFire 0x5220e0 | vtable 0xbd04dc, slot 2 |
| 0x8c1830 | 0x75e687 | ZGraceShotTactic 0x75e440 | vtable 0xbd07b4, slot 2 |
| 0x8c1830 | 0x7c06ad, 0x7c097c | ZFireWeaponTask 0x7c02b0 | vtable 0xbd0bd4, slot 2 |

Every 0x8c1830 call site loads `ecx = [[goal+4] + 0x6a0]`: goal+4 = the ZSoldier, `ZSoldier+0x6a0` = the fire-control object F (sibling of B at +0x698). 0x8c1830 is a plain `__thiscall` on F (plain `ret`, float result in st0, no stack args; `[F]` = the ZSoldier, `[F+8]` = flag word). 0x8c19a7-0x8c19b7 skip the check when `[F+8] & 0x40`; otherwise `ecx = [[F]+0x698]` (= B), push `&local(ebp-4)`, push `&vec3(ebp-0x1c)`, `call 0x8f6990`; on al != 0 it calls `0x655a40([F], [ebp-4])` and on true jumps to 0x8c1991 (hold fire: 0x76f850, flag |= 4, returns the "don't fire" float 0xb4c788). **CORRECTED (verification 11-03): 0x655a40 is the 4-byte stub `32 c0 c2 04` = `xor al,al; ret 4` (always false, shared by ~200 call sites, not hashed, nothing in the repo patches it). So that jne is NEVER taken: the 0x8f6990 result on this path cannot hold fire. The only hold-fire exits of 0x8c1830 are the other tests (0x8c1867 / 0x8c1883 / 0x8c1985 distance compare).**

Reachable through a ZSoldier vtable slot? NO. 0x8c1830 and 0x8f6990 are reached only by direct calls from the slot-2 method of seven goal classes (GUESS: the per-tick Run). Those methods are COROUTINES: all seven functions contain several calls to `0x55b9f0` (the scheduler yield: it saves esp into the coroutine record and calls through 0xb10370; 7 of 7 functions checked, e.g. 8 calls in 0x4a8f40, 18 in 0x4f4460), and 4 of the 11 call sites are immediately preceded by one (0x4eea10, 0x4f4c89, 0x522733, 0x75e671); the other 7 sites sit between yields of the same function. (That 0x55b9f0 really is a yield is read from its body, semantics still partly GUESS.) Consequences:
- A private copy of the goal vtables (per goal object) would put the swap around a whole coroutine slice that can yield with role 0 swapped in and leak it into other bots' slices: the failure RealRun / the Board RUN crash (c0000029) is about. Not recommended; also the goal object of a marked bot would first have to be found (not read, GUESS: a goal stack off the soldier).
- F has no virtual method for this check and B is called directly, so there is NO per-object table lever on this path. A slot 113/114 style private table cannot reach it.

## 3. Does this path read the 0x5706a0 friend list / the 0x7f6850 gate?
Yes, entirely: 0x8f6990 only calls 0x5706a0 with ecx = B (0x8f69a3 `mov edi,ecx`, 0x8f6a20 `mov ecx,edi`). B is the same object slots 113 / 114 pass (`[ZSoldier+0x698]`), so the friend list, the 0x5709c2 `0x7f6850` test, the 0x570a12 mark test and the humans block are identical. Online (role 2, mode 4) `0x7f6850` is false (not checkable statically) -> a human that passes the filters (alive, `[h+0x2723]==0`, `[h+0x2726]==0`) is added without the 0x570a12 mark test (0x5709c2 je -> 0x570a27). Only the two player-table entries `[0xdd265c]+0x828` and `+0x82c` are scanned in this block (loop bound 0x830), not "every human". -> al = 1 -> 0x8c1830 calls `0x655a40`, which is `xor al,al; ret 4` (always false), so **fire is NOT held**. CORRECTED: the earlier conclusion "the feature is incomplete without this path / the marked bot still treats humans as friends on the goal path" is REFUTED: on the goal path the friend-in-line answer is discarded. The only consumer of 0x8f6990's result that matters is slot 113 (0x767510 -> 0x5bdfe0 -> 0x8f6990 -> bit store via 0x606c30), already wrapped. Section 4 (a 0x8f6990 detour) therefore buys nothing for the goal classes and is NOT recommended. What lets a marked bot's goal code fire at a human is some other test (not found here).

Hashing: from re/fireline_gap_1103.md 1b, 0x8f6990, 0x8f6a22, 0x8c1830, 0x8c19c9 are NOT hashed. 0x5be061 and the other call sites were not checked here (GUESS).

## 4. TEST-only design (SUPERSEDED by the verification: on the goal path 0x655a40 is a constant-false stub, so this detour would change nothing; kept for the record only)
No private-table option exists, so a code detour is the only way. It must be a labelled TEST toggle (ship builds never patch code).

Proposal: new ini key `[Brain] OnlineBrainTraitorFireLineGoal` (default 0, "TEST ONLY, patches kl2.exe code"). Do NOT make it mode 3 of OnlineBrainTraitorFireLine: that key is the ship-safe private-table feature, and a mode that writes code should not hide behind it. Requires OnlineBrainTraitorFireLine >= 1 (klbr_tflmode, so the logic gate is shared) and OnlineBrainTraitorArcade=1; otherwise off with a log line.

Mechanism:
1. Detour 0x8f6990: read the 9 bytes first and expect `55 8b ec 83 ec 18 8b 45 08`, else refuse and log. Allocate a trampoline: the 6 stolen bytes + `jmp 0x8f6996`. Write `jmp rel32` + 1 nop over 0x8f6990..0x8f6995 through klh_poke (the patch guard, klhook.c:430, takes expect and new bytes). Undo: write the 6 original bytes back at round end / feature off.
2. Wrapper `static DWORD __fastcall klbr_w_flgoal(DWORD B, DWORD edx, DWORD a1, DWORD a2)` (thiscall, 2 stack args, ret 8, result in al): `soldier = [B+0x154]` (guarded read, > 0xffff); `m = klbr_tfl_begin(soldier, &sw, &e)`; org = the trampoline typed like klbr_fl114fn; `!m` -> return org(...); log only -> org then klbr_tfl_log; swapped -> org inside `__try/__except` like klbr_w_fl114, then `klbr_tfl_end(soldier, sw, flt, SLOT_GOAL)` (new id for logs, e.g. 115; klbr_ta[].nlog needs a third entry); on a fault return 0 (no friend in line is the permissive answer; GUESS that a fault is rare).
3. Reuse: klbr_tfl_begin / klbr_tfl_end / klbr_tfl_log / kbr_tfl_decide unchanged. klbr_tfl_begin returns 0 when `klbr_depth > 0`, so slot 113 -> 0x5bdfe0 -> 0x8f6990 (swap already in) just calls through and is never swapped twice. The swap is held only for the 0x8f6990 body (0x7836b0, the +0x30 vcall, 0x71c5d0, 0x7b3020, 0x5706a0). The direct callees of 0x5706a0 contain no yield (0x455b40 0x506090 0x508ef0 0x51bf80 0x5891f0 0x5a9720 0x660b00 0x6a1c40 0x6b8200 0x6cbf80 0x72a000 0x763e40 0x78f470 0x7b3020 0x7bb2a0 0x7f6850 0x7fd930 0x863a60 0x873dd0 0x87c980 0x8df480 0x929fc0). Verified 11-03: the closure of DIRECT calls from 0x8f6990 is 51 functions and none calls 0x55b9f0; 19 indirect (virtual) calls in that closure are not resolved, so yield-freedom through vtables stays GUESS. That is why this swap is safe where wrapping the goal methods is not.
4. Verify in the usual order: log only (human in the line, expect 1 online) -> swap on (expect 0 for the marked bot) -> OnlineBrainTraitorHitLog shows marked hits on humans > 0. Log the first 8 results per bot.

Alternative detour site 0x8c1830 (this = F, plain ret, 0x1c locals, float in st0, soldier = [ecx]): worse. It would hold the swap across 0x6c81a0 / 0x76f850 / 0x573ce0 after the check, and returns in st0. 0x8f6990 is narrower and has an integer return.

Risks:
- Code patch in a live online session: SP2 anti-tamper killed a DR0 breakpoint (klauto.c 607). Whether it also scans .text at 0x8f6990 is unknown; the klranges.h list says these bytes are not hashed (GUESS that this means unchecked). Bench with 2 seats first.
- The swap flips role to 0 for the call: the humans block takes `0x660b00(counter)` instead of the `[0xdd265c]+slot` table (a different human may be listed online, GUESS) and 0x863a60 / 0x87c980 answer the Arcade way. Same risk as slots 113/114.
- Hot path: 0x8c1830 runs per fire decision of every bot; unmarked bots must pay one guarded read + klbr_find only (klbr_find cost: GUESS, a short scan).
- Non-game thread or klbr_depth > 0: klbr_tfl_begin already passes untouched.
- Round end / disable must put the 6 bytes back; the wrapper lives in the DLL, so an unrestored jmp is not a crash, but the stock bytes should return anyway.
- Not shown yet that the shot then lands (needs the hit counter live).

## 5. Unverified
- Who schedules the seven goal slot-2 methods and whether all seven are coroutines (4 of 11 call sites verified).
- (RESOLVED 11-03: 0x655a40 is `xor al,al; ret 4`, it decides nothing.)
- Deeper callees of 0x5706a0 (yield-freedom), bodies of 0x7836b0, 0x71c5d0, 0x7b3020.
- Hash status of 0x5be061 and the goal call sites.

## Verification (2026-11-03)
Independent static re-check (capstone + pefile on kl2.exe build 0490, own full `E8`/`E9` rel32 scan of .text, own dword scan of .rdata/.data, imm32 scan of .text). Nothing run, patched or committed.

| # | Claim | Verdict |
|---|---|---|
| 1 | 0x8f6990 is `__thiscall`, `ret 8`, this = B (`mov edi,ecx` at 0x8f69a3, `mov ecx,edi` at 0x8f6a20), `[B+0x154]` = ZSoldier, stack args vec3* and DWORD* out, result in al | CONFIRMED |
| 2 | Prologue `55 8b ec 83 ec 18 8b 45 08`, first 6 bytes position independent | CONFIRMED |
| 3 | 0x8f6990 passes `out` unchanged to 0x5706a0 (call 0x8f6a22), which is `ret 0xc` with 3 args (vec, vec, out) | CONFIRMED. Note: 0x5706a0 writes `*out` only in the `[0xce89b0]!=0 && [h+0x774]!=0` branch (0x5707d5-0x5707dd), so the caller must pre-zero it (0x8c19ad does) |
| 4 | Callers of 0x8f6990 are exactly 0x5be061 and 0x8c19c9 | CONFIRMED (no E9 tail calls, no imm32 or data pointers to it) |
| 5 | Callers of 0x8c1830 are exactly the 11 sites listed, in 7 goal classes | CONFIRMED (also no data / imm references) |
| 6 | Each of the 11 sites loads `ecx=[[goal+4]+0x6a0]`; the seven functions are the slot-2 entries of vtables 0xbd1274, 0xbd0ed4, 0xbd1104, 0xbd0424, 0xbd04dc, 0xbd07b4, 0xbd0bd4 | CONFIRMED (vtable dwords read; each site lies inside its slot-2 function, no int3 gap) |
| 7 | 0x8c1830 is `__thiscall` on F, plain `ret`, float in st0, no stack args | CONFIRMED |
| 8 | 0x5bdfe0 is only called from 0x76759b inside 0x767510, "= ZSoldier slot 113" | CORRECTED: ZSoldier vtable 0xbd0954 slot 113 (0xbd0b18) = stub 0x47a0f0 (`mov ecx,[ecx+0x698]; jmp 0x767510`); 0x767510 (this = B) has that jmp as its only caller. Slot 114 (0xbd0b1c) = 0x6bc0a0 -> call 0x51d6c0. 0x767510 also calls 0x5706a0 directly (0x76798f), as does 0x51d6c0 (0x51da55) |
| 9 | Neither 0x8f6990 nor 0x8c1830 is reachable through any ZSoldier vtable slot | CONFIRMED (no pointer anywhere in .rdata/.data/.bss). Only reachable path from a ZSoldier slot is 113 -> 0x5bdfe0 -> 0x8f6990 |
| 10 | Seven goal slot-2 methods are coroutines | CONFIRMED for all 7 functions (each contains 6-18 calls to 0x55b9f0). The earlier "4 of 11 sites verified" is superseded: 4 sites directly follow a yield, the other 7 sit between yields of the same function |
| 11 | Online the 0x5706a0 friend list adds every human (0x7f6850 false) | CORRECTED: a human is added without the 0x570a12 mark test when `0x7f6850` is false (0x5709c2 je 0x570a27), but only for the two table entries `[0xdd265c]+0x828` / `+0x82c` (loop bound 0x830) and only if alive and `[h+0x2723]==0 && [h+0x2726]==0`. That `0x7f6850` is false online is UNVERIFIED (dynamic) |
| 12 | "0x8c1830 then asks 0x655a40 and normally holds fire; a marked bot still treats humans as friends on the goal path; the feature is incomplete without this path" | **REFUTED.** 0x655a40 = bytes `32 c0 c2 04` = `xor al,al; ret 4`, always false; the `jne 0x8c1991` after it (0x8c19df) is never taken. The 0x8f6990 result cannot hold fire on the goal path. Same stub is used at 0x7675de in 0x767510 (there the result of 0x5bdfe0 goes to the bit store 0x606c30 instead, which is why slot 113 matters) |
| 13 | Section 4 TEST detour of 0x8f6990 closes a gap | REFUTED/SUPERSEDED (nothing to close on the goal path; header of section 4 marked) |
| 14 | 0x8f6990, 0x8f6a22, 0x8c1830, 0x8c19c9 not hashed | CONFIRMED against klhook/klranges.h (225 ranges). Added: 0x5be061 NOT hashed, 0x515533 NOT hashed, the other 9 goal call sites ARE hashed, 0x5bdfe0 / 0x767510 / 0x47a0f0 ARE hashed |
| 15 | Direct callees of 0x5706a0 are the 22 listed and contain no yield | CONFIRMED (list identical). Direct-call closure from 0x8f6990 = 51 functions, none calls 0x55b9f0. 19 indirect calls unresolved, so full yield-freedom stays UNVERIFIED |
| 16 | klh_poke at klhook.c:430 takes expect+new bytes (expect max 16) and klbr_tfl_begin returns 0 when klbr_depth > 0 | CONFIRMED (klhook.c:430, klbrain.c:927; log-only mode 1 does not raise depth, so a nested call there would log twice) |
| 17 | Role 0 swap changes which human 0x660b00 lists; anti-tamper may scan .text at 0x8f6990 | UNVERIFIED (depends on klbr semantics and runtime; code side: with `0x7f6850` true the block calls `0x660b00(counter)` instead of the table, see 0x570961-0x570984) |
| 18 | Whether the other hold-fire / target tests in 0x8c1830 consult the friend list | UNVERIFIED (0x8c1867/0x8c1883/0x8c1985 use virtual calls on `[F+4]`, not read further) |

Net effect: the real gap for a marked bot is not the goal path's 0x8f6990 call. Slot 113/114 wraps cover every consumer of the friend-in-line result that has an effect.
