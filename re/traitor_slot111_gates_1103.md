# Slot 111 / type-2 human entry: gate list, adversarially verified (kl2.exe 0490), 2026-11-03

Static only, read from the exe bytes with capstone. Nothing run, patched or committed. "Value" claims that need a live
process (role 2 / mode 4 online) are marked LIVE and are not verifiable here.
Verdicts: CONFIRMED / WRONG (corrected) / UNVERIFIED.

## Corrections that change the plan (read first)
1. **0x4880d0 (MarkSeen) takes an entity POINTER, not a handle.** It does `mov edi,[ebp+8]; call [[edi]+0x30]` (class mask), and
   compares `[entry+4]` with edi with no conversion (0x48823b). NoteEntity 0x7bd720 and 0x425fa0 take a HANDLE (both call
   0x8ccde0 handle->ptr first); 0x4c75f0 takes a pointer. 0x6ece90 is ptr->handle. Pushing a handle into MarkSeen finds no entry.
2. **MarkSeen creates the entry itself.** If no entry matches (0x48823b fails for every entry), 0x488327 does `or ebx,1`
   and adds a new type-2 entry with bit0 SET (list < 10: 0x488363; full: replaces an entry whose bit0 is CLEAR, 0x488380-0x4883a6).
   So NoteEntity is not needed for MarkSeen; call MarkSeen alone. Existing entry: `or [eax],1` at 0x48829a, time stamp refreshed.
   Side effect missed by the list: for a ZFFPlayer it also writes flag **bit7 = byte [human+0x25c5]** (0x488100, 0x4882a3/0x488338).
   Slot 111 reads bit7 (0x8825f9): bit7 set and byte [[cand+0x54]+0x38]==0 gives -100; byte != 0 gives +150 either way.
   Also sets B+0x184=1 (0x4880de); notifies the ally list B+0xd0.. via vcall +0x1a0 unless [soldier+0x88]==2 (0x4883ba), so park B+0xcc
   as the feed does.
3. **Gate 13 is mis-described.** At 0x4f4944 the lookup 0x4c75f0 does NOT add; null -> `je 0x4f4999` (break). 0x616480 false ->
   `je 0x4f4999` (break at once, NO retry). The 4-try loop (0x806cc0, `cmp edi,4` at 0x4f4990) only repeats after a fire call that
   returned. The add via 0x425fa0 is at 0x4f4594, earlier, in the entry part of ZAttackTarget (lookup of ebx, add `[esi+0x14]`, relookup, bail if still null).
   0x425fa0 also adds with flags 0 (edi=0 at 0x4260a7, ecx=2 type). So both add paths give bit0 clear.
4. **"Message 0x1c clears bit0 at 0x608565" is WRONG.** 0x608565 lies inside a jump-table / byte-map area (dwords 0x6082f8, 0x6082de ... at 0x608550);
   the disassembly was data. Real handlers: byte map 0x608578, table 0x60851c: msg 0x1b -> 0x60811e (calls 0x823150 or 0x50e720),
   msg 0x1c -> 0x608174 (`and [esi+0x700],~6`, vcall +0x180), msg 0x59 -> 0x6083cc. 0x823150 clears bit0 of the TARGET HOLDER
   ([soldier+0xa8], 0x82316e) and sets B+0x184, not a B entry. Who clears an entry's bit0: NOT FOUND (loop 1 and loop 2 never do).
5. **Gate 16 reasoning is unsupported.** Slot 15 -> 0x719720 (call 0x4253c6, `je 0x425723`) is a seat check: CONFIRMED.
   But "bs12-13 never reached slot 15 is consistent with gate 13" is wrong: gate 13 is only reached when a human is the TARGET, and
   bs13 saw targets only cop/nothing. The explanation stays the upstream candidate gap.
6. Gate 12 base score: there is no unconditional +25. Score starts 0; +25 only if `[soldier+0xec]!=0` and arg4 (acquaintance byte) != 0 (0x88251c-0x882537).

## Gate-by-gate
| # | Claim | Verdict |
|---|---|---|
| 1 | 0x76751e quick path only if arg==0, B+0x184==0, now < B+0x180; else full scan 0x767678. Full scan clears B+0x184 (0x7676fd). NoteEntity sets 0x184=1 for ZFFPlayer (0x7bd753; also on add 0x7bd8d4) | CONFIRMED |
| 2 | Prune 0x767714 -> 0x51e480: removed iff 0x559190(handle) true; type-2 non-null entry gets bl=1 and is kept; aging only if bl==0 and bit0 clear. Detail: 0x559190 is NOT a plain class-mask test; for ZFFPlayer it tail-jumps to vcall **+0x3d0** (0x559218), the same predicate as slot 111's 0x8824fc. For the 0x1547b24 class it tests 0x539dd0 float and vcall +0x5f4; other classes bit10 of [[e+4]+0x3c] | CONFIRMED, reading corrected |
| 3 | Loop 1 (0x7678c0): entries with bit0 SET; sets bit4 (0x5706a0, 0x767998), 0x10 (dist vs range from 0x71e050: set iff range > dist, 0x767aa4), 0x20/0x40 from 0x78ef30 (0: clear both, 1: 0x20, else 0x40), clears 0x200 then 0x655a40 (`xor al,al; ret 4`, always false). Type 2 with non-null entity -> vcall +0x1bc (call 0x767bfc); type 1 -> +0x1b8; else +0x1c0. No team-mask test, no LOS or distance cutoff before the call | CONFIRMED |
| 4 | Loop 2 (0x767c80): entries with bit0 CLEAR; `and [esi],0xfffffcf9` (clears 0x306 incl. bit4); recency (now-ts)<0x1000; dist 0x60b160; 0x10 set iff range > dist; no LOS, no 0x5706a0; type 2 -> call at 0x767e47 (vtable load 0x767e41) | CONFIRMED |
| 5 | Selection: best starts at -1e38 (0xb5f1e0 = 0xff... float -9.99999968e37); needs strictly greater (fcomp, test ah,5, jp skip); best!=0 -> 0x8bd420 and `[soldier+0xbc]` = entry time (0x767ef9) | CONFIRMED |
| 6 | 0x88247a: bit10 of [[cand+4]+0x3c] set -> NoTarget | CONFIRMED |
| 7 | 0x882490: [cand+0x2721]!=0 -> NoTarget | CONFIRMED |
| 8 | 0x863a60: role 0,1 false, role 2,3 true (table 0x863a78); true and [0x168e59c]==1 runs the 0x8824b1 rules branch; else both go to 0x8824e7 | CONFIRMED |
| 9 | 0x8824e7: [cand+0x2723]!=0 and [[[self+0x40]+0x54]+4]!=2 -> NoTarget | CONFIRMED |
| 10 | 0x8824fc vcall +0x3d0 true -> NoTarget; 0x88250c [cand+0x2728]!=0; 0x882514 [cand+0xad4]==cand. Addresses right. The +0x3d0 test is the same predicate the prune uses to DROP the entry, so a live human never fails it (upgrade from UNVERIFIED). "bit18 of +0x438" meaning not checked: UNVERIFIED. +0x2728 / +0xad4 meaning UNVERIFIED | CONFIRMED (addr), meaning UNVERIFIED |
| 11 | Current-target test 0x88253d (0x5da810 = [self+0x708] if now < [self+0x70c], else 0); cand != it -> 0x882614. Gate entered iff 0x6db900 (role<=1) or 0x87c980 ([+0x5c]==2); else straight to scoring 0x882584. Gate body: self team 0/2 -> [ebp-1]; self team not 1/4 -> [ebp-2]; mark = byte [rec+0x79] bit1 of the SELF (bot) record (0x8826b6-0x8826c2); 0x6a1c40 friendly-fire -> [ebp-3]; with [ebp-2] set: needs 0x7f6850 true AND [ebp-1], then passes (score) iff cand +0x2723!=0 OR +0x2726!=0 OR mark OR [ebp-3]; else NoTarget 0x882726 | CONFIRMED |
| 11a | 0x7f6850 true only for role 0/1 with [+0x5c]==4 (table 0x7f6874), false for role 2/3. **Precondition the list omits:** under the role-0 swap, if the shadow rules' [+0x5c] != 4, 0x7f6850 is false and the gate returns NoTarget even for a marked bot (0x8826f3). Value of [+0x5c] online: LIVE | NEW |
| 12 | Scoring additive: random +-5 (0x41aa70 -0.5 x10, 0x8825a5), +100 bit0 (0x8825a2), -100 bit2 (0x8825c8), -200 bit4 clear (0x8825da), -100 recency 0 (0x8825eb), current-target term (2000 scale, x300, 0x882554-0x882581), +150 near term (0x882848), bit7 term (above). Later terms 0x882762-0x8828a7 only partly read, none returns NoTarget. NoteEntity-only entry loses +100 and the 0x10 compare is still computed; still far above -1e38 | CONFIRMED (base 25 corrected) |
| 13 | NoteEntity 0x7bd720 -> new type-2 entry flags 0 (0x7bd846 xor edi; ecx=2; [+0x10]=[ent+0x54]); existing entry only gets its time stamp (0x7bd806). 0x616480 true iff bit0 SET, bit2 CLEAR, 0x200 CLEAR, 0x10 SET, 0x40 CLEAR (exact). Fire call 0x8c1830 at 0x4f4961. Flags-0 entry never fires | CONFIRMED core; retry/add detail WRONG (see 3) |
| 13b | Lever "MarkSeen after NoteEntity, push handle, ret 4" | handle WRONG (pointer); NoteEntity unnecessary; bit0 persistence UNVERIFIED (see 4) |
| 13c | Forcing bit0 does not force fire: the next loop-1 scan recomputes 0x10, 0x20/0x40, bit4, so out of range, class-2 LOS (0x40) or friend-in-line still block. Keeps wall-sight out of the fire step but not out of target choice (+100) | NEW |
| 14 | Friend-in-line bit4 from 0x5706a0 at 0x767998; blocks 0x616480 and costs -100 | CONFIRMED (slot 113/114 wrap coverage not re-checked) |
| 15 | 0x8c1830 hold-fire tests: virtual calls at 0x8c1859/0x8c1865/0x8c1881/0x8c1983, 0x655a40 stub false. No team read visible, but the vcall bodies were not read. 0x655a40 is not called in 0x8c1830 itself (the repo note puts it in 0x8f6990) | UNVERIFIED (stub CONFIRMED) |
| 16 | Slot 15 0x425320 -> 0x719720 seat check (null, no [a+0x2748], seat -1/<0/>=[rules+0x14], byte[seat]!=0 -> 0) | CONFIRMED; the inference is WRONG (item 5) |
| 17 | 0x6e3400: both plain heisters (+0x2723==0, +0x2726==0 on attacker and victim) -> rules (0x7bb2a0) vcall **+0x2f4**; false -> delta 0 (0x6e35a5). Else x[0xce8a40] once with a window set from [0xce8a3c] at [victim+0x2784] (0x6e35d3-0x6e35f8). Byte +0x285 as "looting started": from notes, not re-read. Sub-mode 0 gate (0x6e3486) not re-read. Lever +0x2726=1 on the attacker body skips the zeroing (0x6e3581 jne 0x6e35ab, then 0x6e35c1 jne 0x6e35fc) | CONFIRMED (structure) |

## Net
Nothing in the verified chain blocks a flags-0 NoteEntity entry as a TARGET (loop 2 scores it, slot 111 passes a live non-police human
online). The hard stop for FIRING is 0x616480 (bit0), as claimed, and the lever is MarkSeen 0x4880d0 with an entity POINTER (it adds the
entry with bit0 itself). Extra preconditions found: shadow rules [+0x5c]==4 for the swap gate (11a), flag bit7 side effect (2).
Unknown: who clears an entry's bit0, so MarkSeen must be repeated on the feed cadence; vcall bodies inside 0x8c1830.
