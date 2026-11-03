# Traitor bot: what actually fires, and why the human holder fails (2026-11-03, workflow w53r6g2xi + bench bs21)

Follows re/traitor_handoff_1103.md. Disassembly was read with capstone. Three passes ran: two traces and one verifier.

## 0x7088c0 is not the normal shot (CONFIRMED)
- There are exactly 15 rel32 calls to 0x7088c0 and no tail jumps.
- Eleven of them pass 0.0 and never fire: Idle 0x77bbd0 (both sites), the cover, checkup, idle-walk, squad, fake-melee, follow and suspicious goals, and hit handler slot 96.
- Four pass a positive float, and all are event or message driven:
  - 0x5d7db9: hit event, only when the event has flag 0x10;
  - 0x6082c6: slot-1 message 0x3d;
  - 0x608476: message 0x59, after the enemy-team-mask gate, so a same-team human is dropped there;
  - 0x7303f6: slot 0x68 via message 0x19.
- bs21 shows `[s+0x88]` = 1 (the gate wants 2) and `[s+0x72c]` frozen on every line for the marked bot. This route is dead for it.

## The real shots: tasks, gated by the fire test 0x616480 (CONFIRMED)
- **ZTurnAndShootTask** (vt 0xbd0f94, [s+0x588], ctor 0x77bbb0 at 0x6ab9f1). Its tick 0x6b1da0 calls `[[s+0x40]+0x6e4](handle=[s+0xb0], 2, 2.0)` at 0x6b1dd1. Its only test is handle != 0.
- **ZRunToPosShootingTask** (vt 0xbd0ba4, [s+0x56c]). Its tick 0x4a7e60 runs 0x616480 at 0x4a84ff / 0x4a855d / 0x4a85a1, then shoots at 0x4a85eb.
- **ZAttackTarget** runs the same test at 0x4f494f / 0x4f4db1.
- **0x616480** is thiscall with ecx = &holder flags [s+0xa8]. It passes only when bit0 and 0x10 are set and 0x4, 0x40 and 0x200 are clear. In practice 0x11 passes and 0x05 / 0x01 fail.
- Callee convention: vt+0x6e4 is (handle, mode, float); the callee pops 12 bytes.

## Bit 0x4: the same-team sweep 0x5706a0 (CONFIRMED filter; MEDIUM on the sphere maths)
- **Shared helpers.**
  - 0x8f6990: the start is the muzzle 0x71c5d0, or the body plus 125 up.
  - 0x5bdfe0: the target is the node plus 150 up. It skips the sweep when the class matches and [E+0x774] != 0.
  - 0x606c30 is only a bit setter.
- **Sweep, step 1: who gets listed.** The sweep lists every entity E that meets all of these:
  - node on;
  - not the shooter's own body;
  - [[E+4]+0x70] bit8 set;
  - byte [E+0x576] == 1 (alive);
  - [[E+0x54]+4] == the shooter's team.

  Nothing excludes the target, so a same-team target blocks ITSELF. The aim point lies inside its own sphere: radius 125, centred 75 above the node.
- **Sweep, step 2: humans block.** This step runs for shooter teams 0 and 2, and only for player slots 0x828 / 0x82c:
  - online, 0x7f6850 is false, so the human is listed with no mark test (0x570a27);
  - under the hook's swap (OnlineBrainTraitorFireLine=2) the mark exempts the human (0x570a12).
- **Write-back.**
  - The full path in 0x767510 writes 0x4 at 0x767998.
  - The quick path rewrites the holder copy's 0x4 on every slot-113 call (0x76762e).
- **Consequence.** If online humans share the bot's team (2), 0x4 is set whatever the swap does. bs22 logs the team ints in a TEAMS line.

## Bit 0x10: the range (CONFIRMED chain)
- [ebp-0x3c] = 0x71e050 (thiscall ecx = [s+0x6a0], no args, float in st0). The value is 2 x the weapon template range (vt+0x2ec -> vt+0x2c8), or 10000.0 when the soldier has no ZItem.
- It is recomputed only on a rescan.
- 0x10 is set only when dist < range strictly. dist runs from the eye (node + 170 up) to the aim point.

## bs21 (out_tgate_1103j, read only): PASS 4 seats, 0 asserts, 0 faults
- 0x10 holds up to about 116 m and drops from about 122 m. So range ≈ 120 m with the bots' guns.
- The bench humans idle at spawn 50-190 m away, so a missing 0x10 there is real distance, not a bug.
- Holder class:
  - DM03: tagged ally bot 76/86, human 4, cop 2;
  - DD05: tagged bot 26, cop 21, human 2.

  HumanFirst nulls cops, but the marked bot now prefers ALLY bots.
- GATES (0x7088c0) for the marked bot, every line:
  - +0x88 = 1, +0x72c frozen (9078 / 15931);
  - team 2;
  - [[+0x678]+8] = 0, 0x658050 ok, [[+0x4a8]+8] = 0;
  - holder bit0 1, bit7 0;
  - Idle state 4, Attack state 0.

## Lever (88c41e3a1, OnlineBrainTraitorHolderFix, default off, UNTESTED; bench bs22)
- After each slot-113 call of a marked bot whose holder is a human ZFFPlayer, the holder flags lose 0x4.
- They also gain 0x10 when the actor distance is below 0x71e050's range. That call is pure, under __try, and switches off after 3 faults.
- It writes one flag dword and patches no code.
- It does not cover:
  - the bot picking an ally bot;
  - +0x88 staying 1;
  - whether a shooting task runs at all.

  Workflow wvf2fzwhg traces those three.

## Not recommended
- Patching 0x5706a0 (hashed) or 0x8f6990.
- Giving humans another team.
- Calling slot 83 with a nonzero handle.
