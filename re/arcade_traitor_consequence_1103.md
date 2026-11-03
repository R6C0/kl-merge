# Arcade Traitor mark: what stock does with rec bit 2 (2026-11-03)

Verified by disassembling kl2.exe (debug/dasm.py): 0x488eb0, 0x4322f0, 0x882636-0x882726, 0x570a0b-0x570a22. Two independent static analyses agreed; no contradiction found.

## 1. Answer
- The mark (`[rec+0x79] |= 2`) does NOT change the bot team, adds no HUD marker, no loot/van change, and makes crew/cops not target him specially.
- Its only effect: the bot becomes hostile to HUMAN players. (a) 0x882470 (ZSoldier slot 111, target score for a ZFFPlayer) stops returning "no target"; (b) 0x5706a0 stops listing humans as friends in his fire line.
- The same "hostile to players" state is reachable without the mark via 0x6a1c40 (friendly-fire float over max(25.0, tuning+0x18)).
- Bench (5 bots marked, no team change) is exactly what the exe predicts; the only visible effect would be those bots shooting the idle player.

## 2. Readers and writers of rec+0x79 bit 2
- 0x8826b6 (in 0x882470): `bl = (byte[rec+0x79]>>1)&1`, rec of the soldier himself (0x78f470 -> 0x7fd930). Used at 0x882715. For a shooter on team 0 or 2 (`[[s+0x40]+0x54]+4`), in Arcade (0x7f6850 true, rules present), a human candidate is scored only if one of: candidate byte +0x2723 (police), +0x2726 (traitor byte), shooter bit 2, or 0x6a1c40(rules,idx) true (tests 0x8826fb/708/715/71d, all jump to 0x882584 = normal scoring). Otherwise return `[0xb5f1e0]` (no target). Teams 1 and 4 skip the gate (0x8826dc). Note: outside Arcade (0x7f6850 false) the path also ends at 0x882726, so ally-side bots never target humans there.
- 0x570a12 (in 0x5706a0): `test byte [rec+0x79],2`; set -> skip adding the human to the fire-line friend list (also skipped when 0x6a1c40 true, 0x570a1b). Callers: 0x51d6c0 (call 0x51da55), 0x8f6990 (call 0x8f6a22), a function at ~0x76798f. Effect on callers (hold fire, flag 4, drop body) is GUESS; consistent with "do not hold fire for humans". Earlier note calling it a Traitor-candidate list builder was wrong.
- Writer: RUN 0x488ecd `or byte [rec+0x79],2` then 0x4322f0(rules,slot). 0x4322f0 only touches [rules+0x338]/[rules+0x33c]; the inc at 0x432310 is dead (edi is never 0), so both stay 0 (confirms traitor_cap_1103.md).
- Clear: 0x817e8a `and byte [rec+0x79],0xfd` in 0x817d20 (round reset, called from 0x8c7a80). Marks do not survive into the next round.
- Replication: 0x6264e9 serializes +0x78..+0x7b (GUESS: bit 2 goes to clients, nothing reads it there).
- Not readers: all other +0x79 users test bit 0 (0x51bde5, 0x5e618e, 0x6cd95f, 0x74b942, 0x78f4b1, 0x7d1062, 0x7eb009, 0x8fb025, 0x907ab8, 0x727f9f ...) or are other classes. The "voice reader 0x6ae750" in arcade_brain_stage2_1103.md is not supported. Payout code 0x796576 reads score-table flag 1, which RUN does not set.
- Gaps (GUESS): reads through shifted base registers or dword reads at +0x76/+0x77 were only spot-checked; evaluate 0x79b7c0 has no "already marked" test, so re-marking is possible.

## 3. Online implication
- Stock = bit 2 only, no team swap. OnlineBrainTraitorTurn's team swap (and TraitorFoe) is our own invention, not Arcade. To match Arcade 1:1, online should set bit 2 in the record and leave the team at 2; the team swap should be off by default (keep only as an optional, labelled non-Arcade toggle).
- To get the real effect online the original 0x882470 and 0x5706a0 must read the bit: both call 0x78f470(rules,[shooter+0x40]) then 0x7fd930, which indexes blindly past the table if the index is 0xff. A shadow table needs a real record for every soldier reaching them, plus real floats at rules+0xc0+4*idx and level at [[rules+0x5f8]+0x45] (read by 0x6a1c40). Also needs 0x7f6850 true (Arcade); online that gate is GUESS-unknown, otherwise 0x882470 returns no target regardless of the bit.
- Confirm by logging the 0x882470 return for a marked bot vs the player against the 0xb5f1e0 constant, or watch player health.
