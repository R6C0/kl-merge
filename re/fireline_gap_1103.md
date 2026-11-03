# Fire-line friend list gap (0x5706a0 / 0x570a12) and the online 0x882470 gate (2026-11-03)

Static only (debug/dasm.py, capstone on kl2.exe build 0490). Claims not read from code are marked GUESS.
Hashed status from klhook/klranges.h (checked with a script, not by eye).

## 1. What 0x5706a0 is

Signature: `__thiscall`, `ret 0xc`, three stack args: [ebp+8] = segment start (3 floats), [ebp+0xc] = segment end (3 floats),
[ebp+0x10] = out dword (set only at 0x5707dd from 0x51bf80). CORRECTED (1103 recheck): that store happens only when `[0xce89b0] != 0` and `[entity+0x774] != 0` (0x5707c1-0x5707d1), and then that entity is NOT added to the list (jmp 0x5707fa); [ebp+0x10] is also reused as the 0/1 loop counter from 0x57092a on (the out pointer is dead by then). Returns al: 1 = "a friend stands in this line", and in
that case it also calls 0x7b3020 on the friend's [+4] (0x570b36) (what that does: GUESS, a notify/flag).
`this` (esi, [ebp-0x30]) = object B; `[B+0x154]` = the owning ZSoldier, `[[B+0x154]+0x40]` = its actor, shooter team =
`[[[actor]+0x54]+4]` ([ebp-8], 0x570708-0x570714). B is `[ZSoldier+0x698]` (see the slot 113/114 thunks below).

Flow:
1. 0x5706e3-0x570772: spatial query (0x5891f0, repeated) around the segment. A hit goes into the friend list (max 0x20,
   `[ebp+edi*4-0xe4]` = entity, `-0x168` = a float from 0x929fc0) when: entity not flagged bit10 of `[[e+4]+0x3c]`, not the
   shooter, `[[e+4]+0x70]` bit 8, `byte [e+0x576]==1`, and **same team** (`[[e+0x54]+4] == shooter team`, 0x5707b6-0x5707bf).
2. 0x570822-0x570836: shooter team 0 or 2 -> 0x57091e (humans block); team 1 -> 0x57083c (all player slots 0x828..0x898
   of `[0xdd265c]`, added if police byte +0x2723 and not +0x2727); other teams skip to 0x570a60.
3. Humans block (team 0 or 2), loop index [ebp-4] = 0x828, 0x82c (two slots of `[0xdd265c]+0x828`), counter [ebp+0x10] = 0,1:
   - 0x570936-0x570959: skip entry (jump 0x570a48) only if `0x87c980` (session mode `[0x168e598+0x5c]==2`) && `0x863a60`
     (role 2 or 3) && `!0x8df480`. Online FA (mode 4) never takes it.
   - 0x570967 `0x7f6850()`: false -> player = `[[0xdd265c] + slot]`, true -> player = `0x660b00(counter)` (GUESS: lookup by index).
   - skip the human if null / bit10 flag / `+0x2723` (police) / `+0x2726` (traitor byte): 0x57098e-0x5709b6.
   - 0x5709c2 `0x7f6850()` again: **false -> 0x570a27 = the human IS added to the friend list** (the mark is never read).
   - true -> 0x508ef0 (= `[G+0x54]` rules, only if mode==4 && 0x7f6850) -> `0x78f470(rules,0x6cbf80(actor))` ->
     `0x7fd930(rules, idx)`; **0x570a12 `test byte [rec+0x79],2`** -> jne 0x570a45 = NOT added; else `0x6a1c40(rules, idx)` true
     -> NOT added; else added.
4. 0x570a60-0x570b22: for each listed friend, 0x873dd0 + a segment-vs-sphere style test 0x5a9720; first hit -> return 1.
   (what exactly 0x5a9720 tests: GUESS, "does the fire line touch the friend".)

So a human that is on the list makes the function answer "friend in the line", the target human himself included
(no exclusion of the aimed-at entity is visible in the code). For a marked bot the list must NOT contain the human.
That is only reached when 0x7f6850 is true (Arcade). Online (role 2) it is false, so every ally bot (marked or not)
lists every human as a friend. This is the gap: even if 0x882470 lets a marked bot target a human, the fire-line test can
refuse the shot. How hard it refuses depends on the callers (GUESS, see 1b).

### 1a. Callers of 0x5706a0 (full byte scan, `E8`/`E9` rel32 and pointer-size words in .rdata/.data)
There is no vtable pointer to 0x5706a0 and no jmp to it: exactly three direct calls.
| call site | function | what it is |
|---|---|---|
| 0x51da55 | 0x51d6c0 (ret 0x10, sets ecx from the caller) | reached from the thunk **0x6bc0a0 = ZSoldier vtable slot 114** (ptr at 0xbd0b1c; thunk does `ecx=[ecx+0x698]`, pushes 4 args, `call 0x51d6c0`). 0x51da5a: `jne 0x51dae7` = candidate dropped when a friend is in the line. A candidate/target picker (GUESS). |
| 0x76798f | 0x767510 (ret 4, 1 byte arg) | reached from the thunk **0x47a0f0 = ZSoldier vtable slot 113** (ptr at 0xbd0b18; thunk: `ecx=[ecx+0x698]; jmp 0x767510`). Result sets/clears bit 4 of `[esi]` (0x767998 / 0x76799d) = a "friend in line" flag (consumer: GUESS). |
| 0x8f6a22 | 0x8f6990 (ret 8) | end of 0x8f6990 (a normal `call`, result left in al, `ret 8`; CORRECTED wording: not a jmp tail call). 0x8f6990 is called from 0x5bdfe0 (itself called from inside 0x767510, 0x76759b) and from inside **0x8c1830** (call at 0x8c19c9). 0x8c1830 is called directly (no vtable) by goal code: ZFriendlyFireGoal 0x4a8f40, ZCoveredMoveActGoal 0x4ee860, ZAttackTarget 0x4f4460, ZAttackSniperTactic 0x515020, ZCoverFire 0x5220e0, ZGraceShotTactic 0x75e440, ZFireWeaponTask 0x7c02b0 (call 0x7c06ad). These are the fire decisions (GUESS which one holds fire). |
Who calls ZSoldier slots 113 / 114: NOT resolved (an `[reg+0x1c4]/0x1c8` byte scan hits thousands of field reads of other classes). GUESS: they are
ZSoldier "can I shoot / pick target" methods called by the AI goals.

### 1b. Hashed or not (klranges.h)
HASHED: 0x5706a0, 0x570a12, 0x5709c2, 0x5707d3, all three call sites, 0x6bc0a0, 0x51d6c0, 0x47a0f0, 0x767510, 0x882470, 0x8826ec,
0x6db900, 0x87c980, 0x508ef0, 0x78f470, 0x7fd930, 0x6a1c40, and the vtable words 0xbd0b18 / 0xbd0b1c.
NOT hashed (free): **0x8f6990, 0x8f6a22, 0x8c1830, 0x8c19c9**, and 0x7f6850.
Note the private ZSoldier table (klh_soldier_priv) is heap data, so wrapping slots there never touches a hashed byte.

## 2. Hookable points (best first)

### H1 (SHIP-safe, partial): wrap ZSoldier slots 113 and 114 on the same private table
The marked bot already has the private table copy (KLBR_TA_NSLOT = 128 dwords, so slots 113 and 114 are copied; slot 111 is wrapped).
Add two wrappers beside klbr_w_score:
- slot 114 (`+0x1c8`, original 0x6bc0a0, `ret 0x10`: args dword, dword, float, float -> declare as 4 DWORD stack args and
  pass them through untouched; the float return, if any, is whatever the original leaves in st0: 0x6bc0a0 returns eax/al from 0x51d6c0 - GUESS: al, check
  the 0x51d6c0 epilogue `ret 0x10` and use a `DWORD __fastcall` wrapper). CORRECTED (1103 recheck): the thunk's two last args ([ebp+0x10], [ebp+0x14]) are floats (pushed via fld/fstp), the first two are dwords; the return is an integer in eax = `[ebp-0xc]` (initialised 0 at 0x51d6d9, loaded at 0x51dafe), NOT a float, so `DWORD __fastcall(self, edx, a1,a2,a3,a4)` is right. Slot 113 (0x767510, `ret 4`, one byte arg at [ebp+8]) leaves no meaningful return (its only ret is 0x767675 after storing `[esi]`).
- slot 113 (`+0x1c4`, original 0x47a0f0 -> 0x767510, `ret 4`: one byte arg).
Each wrapper: decide exactly as klbr_w_score does (`kbr_tarc_decide` on the soldier `self`, no candidate needed - force "marked bot, host, round") and, for a marked bot,
`kbr_frame_enter` + `klbr_swap_in(G, sm)` around the original, `klbr_swap_out` after (same `__try`/fault counter/3-fault switch-off). The swap
already provides what 0x5709c2 needs: `sm+0x54 = 0` -> 0x7f6850 true (role 0, mode 4), 0x508ef0 returns `[G+0x54]` = shadow rules, and the shadow record carries the mark
(0x570a12 then skips the human). This covers P1 (0x51d6c0), P2 (0x767510 directly and via 0x5bdfe0 -> 0x8f6990) only.
Caution added by the 1103 recheck: unlike the slot 111 wrapper (ZFFPlayer candidates only), wrappers on 113/114 hold the role-0 swap for the WHOLE of 0x51d6c0 / 0x767510, i.e. for every candidate and every other role/mode read inside them (0x51d6c0 is a candidate loop, 0x51d813..0x51daf8; slot 111 may be called from inside it and re-enters the swap: klbr_depth nesting makes the inner wrapper skip its own swap_in, which is correct). Also unresolved: 64 `mov r,[r+0x1c4]` + `call r` sites and many +0x1c8 sites exist (some inside ZGraceShotTactic 0x75e4de/0x75e6de, ZAttackSniperTactic 0x515121, ZFriendlyFireGoal 0x4a9145), so the goal code may well call these slots too (other classes share the offset; not resolved).
Risk (GUESS): with role forced to 0 the humans block takes `0x660b00(counter)` instead of the `[0xdd265c]+slot` table, so which human is listed may differ online
(remote players), and everything else the original reads from session role/rules in that call (0x6db900, 0x863a60) flips to the Arcade answer for the call.

### H2 (TEST builds only, covers the goal path): detour 0x8f6990 (free range)
Tail callers 0x8c19c9 (goal code, the likely real hold-fire) and 0x5be061 go through 0x8f6990 (`__thiscall`, `ret 8`, args: vec3*, dword; prologue
`push ebp; mov ebp,esp; sub esp,0x18` = 5+ stolen bytes at 0x8f6990 are position-independent: `55 8b ec 83 ec 18`, only 6 bytes, a 5-byte jmp steals the first 5 = `55 8b ec 83 ec`, plus 1 more instruction boundary: take all 6). Wrapper: `soldier = [ecx+0x154]`,
look it up with klbr_find / `klh_svt`, if marked bot -> swap_in, call original, swap_out. SHIP builds never patch code (klh_poke policy), so this is a
test-only toggle. Check 0x8c1830 as the alternative site (free too): ecx there is the fire-control object; its owner path `[esi]` -> `[+0x40]` is used at 0x8c1887-0x8c188d (GUESS: esi+0 = the ZSoldier).
CORRECTED (1103 recheck, now PROVEN, no longer GUESS): 0x8f6990's `this` IS B. 0x8f6993-0x8f69a3 keep ecx in edi and 0x8f6a20 `mov ecx,edi` / 0x8f6a22 `call 0x5706a0` passes it unchanged; the caller 0x8c19b9-0x8c19c9 loads `ecx = [[esi]+0x698]` (esi = the 0x8c1830 object, so `[esi]` is the ZSoldier and +0x698 is B, same field the slot 113/114 thunks read). So H2 can take `soldier = [ecx+0x154]`, or in 0x8c1830 `[esi]`. The 0x8f6990 args are (vec3 *line start-or-end, DWORD *out): the second is a POINTER to a local dword (0x8c19c1 `lea eax,[ebp-4]`) that 0x5706a0 fills (its [ebp+0x10]) and the caller then uses (0x8c19d2 push, call 0x655a40); a wrapper must pass both through untouched. Also: 0x8c19a7 skips the whole check when `[esi+8] & 0x40`.

### H3 (data only): no per-call shadow is possible without a wrapper
What 5706a0 reads in the humans block is session role/mode (global), `[G+0x54]` rules (global), per-human bytes +0x2723/+0x2726 (shared by all bots) and the shooter's team.
Nothing there is per-shooter except team, so a data-only shadow cannot single out a marked bot. A per-shooter team field is the only per-bot lever, and a team change is the invention
OnlineBrainTraitorTurn already does (not Arcade). Not recommended.

### Not possible: debug registers
klauto.c 607: a DR0 breakpoint in a session run gets the process killed by the anti-tamper (SP2 11-01). Do not use them to catch 0x5706a0.

## 3. Proposed plan
1. Implement H1 first (ship-safe): two more wrappers on the existing private table, no new state; log the first 8 results like klbr_w_score
   (`friend list: marked soldier X: line returned N`). Verify first by a log-only run: wrapper that does NOT swap and just logs the result of 0x51d6c0 / 0x767510 for a marked bot with a human
   in the line, then flip the swap on.
2. Add H2 only as a labelled TEST toggle if the log shows the goal path (0x8c1830 callers) is what blocks the shot.
3. Keep the documented gap line in klbrain.c until a live test shows a marked bot fires with the human in its line.

## 4. Question 2: does online 0x882470 reach the 0x7f6850 gate at all?
**No. Online (role 2, mode 4) the gate is skipped, and ally bots (unmarked too) already score humans through the normal path (0x882584).** Exact reading:
- The gate block is entered only at 0x882614 (reached from 0x882544 `jne 0x882614`, i.e. when the candidate is not the soldier's current target
  `0x5da810`). At 0x882614: `0x6db900(session)` = `[session+0x54] <= 1` (role 0 or 1, offline Arcade/solo) -> go to 0x882636;
  else `0x87c980(session)` = `[session+0x5c]==2` (mode 2) -> 0x882636; else **`je 0x882584` (normal scoring)**.
  Online host: role 2, mode 4 -> both false -> 0x882584. Online client: role 3 -> same.
- If the candidate IS the current target, 0x882544 falls through to 0x88254a (bonus) and then 0x882584 as well.
- The gate itself (0x882636 onwards) needs `0x7f6850` (0x8826ec / 0x88266d): role 0/1 with mode 4 (table at 0x7f6874: role 0,1 -> `mode==4`; role 2,3 -> false; role > 3 -> `mode==4`).
  It only ever returns the "no target" float 0x882726 for a human when role is 0/1 (or mode 2) AND `0x7f6850` is true AND team is 0/2 AND all four exemptions fail.
  **CORRECTED (1103 recheck): that sentence was wrong.** The gate (shooter team not 1 and not 4, i.e. `[ebp-2]` set at 0x882655, test 0x8826dc) refuses a candidate (jumps to 0x882726, the same constant 0xb5f1e0 as 0x8824d9) in THREE ways: `0x7f6850` false (0x8826f3 `je 0x882726`), OR shooter team not 0/2 (`[ebp-1]` == 0, 0x8826f9 `je 0x882726`), OR 0x7f6850 true, team 0/2 and no exemption fires (fall-through at 0x88271d). Exemptions (each `jne 0x882584`): `+0x2723` (0x882702), `+0x2726` (0x88270f), the mark bl = `(rec+0x79 >> 1) & 1` (0x882717), and the 0x6a1c40 result `[ebp-3]` (0x882720). Consequence: a session with mode 2 (the `0x87c980` leg) and role 2/3 enters the gate with 0x7f6850 false and refuses EVERY candidate (that passes the earlier filters) for any shooter whose team is not 1 or 4; that is not online FA (mode 4), so the "online FA skips the gate" conclusion below stands.
- Earlier filters at the top (0x882480-0x8824fa) apply to every shooter: candidate flag bit10 `[[c+4]+0x3c]` -> no target; `byte [c+0x2721]` -> no target;
  online FA: `0x863a60` (role 2 or 3) is true, `[0x168e59c]` (sub-mode) is 0 for FA so the 0x8824a8 branch (`==1`) is not taken -> 0x8824e7: a police candidate (`+0x2723`) with shooter team != 2 -> no target; otherwise 0x8824fc.
  0x8824fc: virtual `[cand vtable+0x3d0]` true -> no target; `byte [c+0x2728]` -> no target; `[c+0xad4]==c` -> no target. Those can still refuse a human (nature of the vcall: GUESS).
- Consequence for klbr_w_score: the wrapper swaps role to 0 (sm+0x54=0), which makes 0x6db900 TRUE and so ENTERS the gate for a marked bot (the mark then opens it at 0x882715). The unmarked
  bot, not wrapped, never enters it. So the wrapper changes the ordinary online score only by going through the gate it would have skipped; the result for a human is the same "scored" outcome.
  The log line "still refused, the Arcade gate did not open" is therefore not expected from the gate (it could only come from the earlier filters 0x8824fc..).
- Implication (the implementer's suspicion is right): online, unmarked ally bots can already score humans in slot 111; the Traitor mark changes nothing there. Whether they then shoot is decided by the
  fire-line list (Section 1), which lists humans as friends online (0x5709c2 false -> added) - the reason bots do not shoot humans online is more likely the friend list than the score (GUESS, matches Arcade design:
  in Arcade, role 0 makes 0x5709c2 true and the mark skips the human).
- What this leaves for the feature: score wrapper is not needed for the online effect (GUESS until a live check: log 0x882470 for an unmarked bot vs a human; expect != 0xb5f1e0). The fire-line list is the real
  blocker, i.e. H1/H2 above. Also unknown: whether the AI's candidate enumerator even offers human players to ally bots (not read; it was not needed for 0x882470).

## 5. Unverified / next checks
- Callers of ZSoldier slots 113/114 and what they do with the answer (GUESS everywhere above).
- `0x660b00` (the Arcade human lookup) and `0x5a9720`, `0x7b3020` bodies not read.
- 0x7f6850 jump table read from the exe: entries 0x7f6865, 0x7f6865, 0x7f686e, 0x7f686e (role 0,1,2,3).
- A cheap live proof for 2): log the return of an UNMARKED ally bot's 0x882470 for a human (no code change beyond the existing slot-111 wrapper path with the swap skipped).
