# Traitor bot: from the pick to a shot (2026-11-03, workflow wkbj5dple, static only)

Follows re/traitor_target_holder_1103.md. Question: in bs19 the marked bot's holder (soldier+0xa8) held a human,
but the ZAttackTarget goal handle [[s+0x658]+0x14] stayed 0 (DM03) or a stale value (DD05). Is that the broken hand-off?

## Answer: no, that goal is not the hand-off
- The only gameplay writer of [ZAttackTarget+0x14] is Attack slot 83 (0x831850) at 0x8318e1-0x8318ef (via 0x68fd70),
  and only with a nonzero handle while [[s+0x5ac]+8] is 0 or 4. CONFIRMED.
- Every static caller of slot 83 passes handle 0. 0x49a666 and 0x907c34 are CONFIRMED; 0x59b995, 0x60ff57 and 0x748e7e are reported only.
  Handle 0 takes the CoverFire route instead: 0x717f90 on [s+0x654], at a position.
- So in shipped code the holder never feeds ZAttackTarget. A 0 / stale [goal+0x14] is normal and says nothing.
  The goal ctor never initialises +0x14, which explains the stale value (GUESS).
- 0x4f18a5 / 0x8db8d0 are the goal's stream Load / Save, not gameplay.

## The engine's real route (verifier, partly confirmed)
- ZSoldierIdle tick 0x77bbd0:
  - calls selection slot 113 (push 1) at 0x77bc2a;
  - needs holder handle [s+0xb0] != 0 (0x77bc37) and holder flags [s+0xa8] bit7 CLEAR (0x77bc40-0x77bc4c);
  - then calls 0x7088c0(0.0f) at 0x77bc54. A second site 0x77bcd2-0x77bce1 does the same.
- ZSoldierAttack tick 0x6c8350:
  - calls slot 113 (push 0) at 0x6c83c5;
  - if [s+0xb0] == 0 it calls 0x60d050; otherwise the goal's children fire.
- 0x7088c0 (ret 4), gates as reported; whether esi is the goal or the soldier is UNSURE:
  - [esi+0x72c] != clock (0x7088d5);
  - [esi+0x88] == 2 (0x708912);
  - [[esi+0x40]+0x54]+4 != 0 (0x708925);
  - arg > 0 (0x708931; the Idle caller passes 0.0f, sign test unresolved);
  - [[esi+0x678]+8] in {0,4} (0x70893b);
  - 0x658050 == 0 and 0x8eb610 == 0 (0x70894f / 0x70895a);
  - holder handle != 0 and bit0 set (0x708969 / 0x708970);
  - if all pass, [vt+0x6e4](handle, 2, float*) at 0x708991 = aim and engage.
- AddGoal network gate 0x6cabf0 (also inside 0x637800): skips the add on a real client, role 3. CONFIRMED.
  It passes for roles 0/1/2 and under the hook's role-0 swap.
- B entry flags 0x15 have bit 0x4 set. If the fire test is bit0 + 0x10 set and 0x4 / 0x40 / 0x200 clear,
  0x15 is blocked at the fire step and 0x11 passes (to re-verify 0x616480).

## Levers, in order of risk (none run)
1. Read only: log holder bit7 and bit0, the 0x7088c0 gate fields, and which goal runs (Idle +0x634 vs Attack +0x638).
   Follow-up workflow w0g1x0zbt pins the exact fields.
2. Clear holder bit7 for a marked bot's human holder after selection returns (in the private slot-113 wrapper). No new calls.
3. Call 0x7088c0 ourselves (thiscall on the Idle goal, one float, ret 4) with a positive float. GUESS.
4. Shipped pattern 0x907c34: slot 83 (handle 0, pos = the holder entity's position, float [0xbcb330]).
   This is CoverFire at a position, priority 0xa0.
- Do NOT call slot 83 with a nonzero handle: that is code shipped DD never runs, and the 0x6cabf0 gate refuses it on a client.
- Selection still matters: HumanFirst (73e41f775, bs20) stops cops outscoring the human.
