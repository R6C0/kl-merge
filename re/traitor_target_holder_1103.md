# Traitor bot: where the chosen target lives (2026-11-03, workflow wwr26esf3, static only)

Question: in bs17 the marked bot called slot 111 (0x882470) 88 times with human candidates, yet the
'traitor target:' probe showed 0. Answer: the probe was reading the wrong field.

## Confirmed from kl2.exe bytes (capstone)
- `[soldier+0x708]` / `+0x70c` is the LAST AGGRESSOR plus its stamp (setter 0x506f50, stamp = clock+0x2000;
  callers are the slot-96 hit handler 0x8473a0 at 0x8474bf and 0x5a827c / 0x5d7d30 via 0x5a8140). It is not the selection.
- Target selection 0x767510 is entered via the slot-113 thunk 0x47a0f0 (`mov ecx,[ecx+0x698]; jmp`), so `edi` = B = [soldier+0x698].
  [B+0x154] is the soldier.
- The best score starts at -1e38 (0xb5f1e0). A candidate replaces it only if its score is STRICTLY greater
  (0x767c3b, 0x767e6e). There is no threshold.
- The winner goes to the holder H = [B+0x154]+0xa8 (= soldier+0xa8) through 0x8bd420 at 0x767eee:
  +0xa8 flags, +0xac entity ptr (from 0x8ccde0; only +8 is checked by `cmp [H+8],0` at 0x767555), +0xb0 handle,
  +0xb4 refcounted [ent+0x54], +0xb8 / +0xdc clock, +0xc0 flags&1; soldier+0xbc = the entry time ([entry+0xc]).
- No winner (0x767f77): 0x8bd420(0, &0x168e35c) clears the holder.
- Throttle: B+0x180 = next rescan time, B+0x184 forces a rescan, B+0x18c = hold time; quick path 0x76751e-0x76756e.
- [soldier+0x658] = the ZAttackTarget goal (vtable 0xbd1104, ctor 0x571310 called at 0x6ab80e, stored at 0x6ab81b).
  - It fires on its own handle [goal+0x14]. It does not read the holder.
  - It writes the holder back via 0x8bd420 at 0x4f4706, after testing the entry flags: bit0 set, bit2 / 0x200 / 0x40 clear, 0x10 set.
- Attack = ZSoldier vtable slot 83, 0x831850 (vtable 0xbd0954, entry 0xbd0aa0 = +0x14c):
  - nonzero handle: sets [goal+0x14] (0x8318e1) ONLY if [[soldier+0x5ac]+8] is 0 or 4;
  - zero handle: builds a position goal on [soldier+0x654] (0x717f90).
- A position route exists: 0x907c06-0x907c46 tests holder handle [s+0xb0] != 0 and calls slot 83 with handle 0
  and the holder's position. The function around it and its callers are NOT traced.
- Gate 11a (re/traitor_slot111_gates_1103.md) reads the SESSION [0x168e598] (+0x54 role, +0x5c mode), not the rules.
  Under the hook's swap that is role 0 and mode 4, so the gate passes. Items 6-10 read only the candidate.
- Slot 111 stores its final score at [cand+0x2734] (0x8828c6) on every path except the two 'no target' exits,
  0x8824d9 and 0x882726.

## All 0x8bd420 callers
0x4f4706, 0x4f4a0a, 0x4f4ce7, 0x4f7062, 0x58300f, 0x5844c2, 0x767eee, 0x767f8a, 0x772934, 0x7729da, 0x78351a, 0x7b495e, 0x7f05a6.

## Probe (4ecfc0234, read only, TEST out_thold_1103g, bench bs19)
Per marked bot, the new 'traitor target: bot N HOLDER' line logs:
- the holder flags, pointer + class, handle and entry time;
- the goal and its handle;
- the Attack state gate;
- +0x654 and +0x720;
- B's rescan, force and hold values.

The gate log now prints session role/mode.

How to read bs19:
- Holder is a human but nothing fires: the gap is the hand-off (slot 83 / state gate) or the entry flags.
- Holder empty or a cop: the gap is the score, or cops outscoring the human.

## Open (GUESS / not traced)
- Who calls Attack(handle) with the holder's handle.
- The function around 0x907bf0.
- What the human's +0x2721 / +0x2728 mean online.
- Whether cops outscore humans.
- Possible lever (proposal only): call 0x831850 ourselves (thiscall, ecx = soldier; handle, pos ptr, float; ret 0xc) when the holder is a human.
