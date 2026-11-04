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

## Workflow wvf2fzwhg (6 agents: 3 traces + 3 verifiers), read only
### Why an ally bot wins (slot 111 0x882470, CONFIRMED structure)
- No term tests human vs bot, friend or team. The mark only matters inside the Arcade gate, which online skips.
- Flag terms decide it: bit0 +100, 0x4 -100, 0x10 clear -200, a1c == 0 -100, visibility -100 x k, and [[cand+0x54]+0x38] +150 (else bit7 -100).
- Distance is flat past 400 (the -0.09 x d term needs the second-vector distance to be exactly 0). Stickiness: cand == [s+0x720] gives +300.
- The replace rule (0x767c3b) is strictly greater than the -1e38 start, so the "no target" float can never win.
### +0x88 (soldier mode)
- The base ctor 0x7cfac0 writes 2. Setter = vt+0x4c (ZSoldier 0x588000; 1 -> 2 is a plain store, side effects only when leaving 3).
- Known writers of 1: 0x421680 and 0x543fa0, each paired with 0x7088c0(0.0). The verifier REFUTED the six 0x75f960 vtables as writers. Which one hits the crew bot is unknown.
- 2 opens 0x7088c0 / 0x582033 / 0x60836f and skips the slot-111 ally notification at 0x4883ba.
### What starts the shooting tasks
- Goals: list [s+0x48], AddGoal 0x6cabf0, arbiter 0x81eb90 (max prio, an early return if the winner is already current), goal state at +8 (0 never started, 2 running, 4 terminated).
- Tasks run as children through 0x521350. Who pushes ZTurnAndShootTask / ZRunToPosShootingTask is UNRESOLVED.
- Idle 0x64 at 0x6ac605; CoverFire +0x654 at prio 0xa0 through 0x637800.
- Slot 83 with handle 0 (the shipped call 0x907c0f-0x907c46: pos = 0x7b3020(ecx=[ent+4], &pos), float 5.0 [0xbcb330]) -> 0x717f90 SetPosition + 0x637800(+0x654, 0xa0, clock+0x800) + slot 20, but only while [[s+0x5ac]+8] is 0 or 4.

## bs22 (out_thx_1103k, HolderFix=1): PASS 4 seats, 0 asserts, 0 faults
- TEAMS: bot team 2, human holder team 0/1: they DIFFER. So the human holder's 0x4 does not come from team sharing (the human-slot stage, 0x828 / 0x82c).
- HolderFix holds: DM03 fixed 276 times; DD05 156 in range, 67 out of range.
- The fire test PASSES on the holder in 13/37 DM03 lines and 21/49 DD05 lines.
- DD05 holder: human 22, cop 21, bot 4 (bs21: human 2).
- Still 0 hits (HitLog's slot-15 hook was never reached). GATES on every line: Idle state 4 (terminated), Attack 0, +0x88 1. The bot has no running goal to shoot from.

## Levers for bs23 (both default off, UNTESTED)
- OnlineBrainTraitorHumanOnly: in the private slot 111, a marked bot returns "no target" for a tagged bot's body while a seen, in-range HUMAN is in B.
  - klbr_hf_human_in_b now skips tagged bot bodies, which also fixes HumanFirst counting an ally bot as a human.
- OnlineBrainTraitorCoverFire: after slot 113 (and after HolderFix), when the holder is a human passing 0x616480 and [[s+0x5ac]+8] is 0 or 4, call slot 83 like 0x907c34, at most every 2 s per bot.
  - It logs the CoverFire goal state and the current goal before and after.

## bs23 (out_tcf_1103l, HumanOnly + CoverFire): PASS 4 seats, 0 asserts, 0 faults
- HumanOnly nulled ally-bot scores: DM03 44 (54 passed), DD05 26. DM03 holder: human 21, bot 20; DD05: human 20, cop 20, bot 7.
- CoverFire: DM03 26 calls, DD05 17, 0 skips, 0 faults. It becomes the current goal ("current goal X -> +0x654"), state 0 at the call, 4 about 3-6 s later, then the old goal returns.
- 0 hits, but the HitLog slot-15 wrapper was entered 0 times by anyone: hits are unobservable there. bs24 reads the human's health instead.

## Workflow wee6blb1x (4 agents: 2 traces + 2 verifiers), read only
- Scheduler (CONFIRMED): [s+4..s+8) goal stack (top runs), [s+0x10..] abort queue, [s+0x48] goal list {goal, prio, expiry flag, clock}, [s+0x74] current goal, [s+0x78] its prio.
  Goal states at [g+8]: 0 new, 1 starting, 2 running, 3 exiting, 4 terminated. Goal slots: +0x634 Idle, +0x638 Attack, +0x654 CoverFire, +0x658 AttackTarget (ctor 0x6ab250).
- Idle never ends by itself: it is aborted (arbiter switch / PopGoal). The arbiter 0x81eb90 early-returns at 0x81ec18 when the winner == [s+0x74], so a stale current goal is never re-pushed.
- Idle is re-added by shipped 0x82cae0 (vt+0x4c(2), AddGoal Idle 0x64 at 0x82cb5f, re-arbitrate), when [s+0x6e8] == 0.
- REFUTED: "+0x88 = 2 lets Idle shoot". Idle calls 0x7088c0 with 0.0 and the arg test at 0x70892f skips the aim call unless arg > 0.
- The shooting tasks (ZRunToPosShootingTask [s+0x56c], ZTurnAndShootTask [s+0x588]) run only as RunChild of ZSoldierAttack 0x6c8350, ZAttackTarget 0x4f4460 / 0x4f4bed and ZAttackFromCornerCover 0x45ff54.
- Slot 83 with a NONZERO handle reaches AddGoal at 0x831986 and adds ZAttackTarget (prio 0x96); the AddGoal gate refuses only role 3 (client). Shipped DD never passes a nonzero handle (unexercised path).

## Levers for bs24 (5400b88e7)
- CoverFire health readout (read only): the human holder's health at the call, +300 ms and +2 s; also stack count / top state, +0x88, +0x6e8, Idle state.
- OnlineBrainTraitorAttackHandle (default off, UNTESTED, needs CoverFire): the same call with handle = [s+0xb0]; logs the +0x658 state and the current goal.

## bs24 (out_tah_1103m): PASS 4 seats, 0 asserts, 0 faults
- DM03, CoverFire (handle 0) + health readout: 7 calls. The current goal becomes CoverFire (stack 1, top = CoverFire); its state is 0, sometimes 2 (running), later 4.
  The human holder's health stayed 550 at +0.4 s to +3 s (6/6 flat). +0x88 1, +0x6e8 0, Idle 4 on every line.
- DD05, AttackHandle (handle = [s+0xb0] = 0x1aa): 10 calls, all nonzero (HitLog's slot-83 counter agrees). ZAttackTarget +0x658 becomes current,
  but its state is 4 at the next read (< 0.6 s). Once the stack held 3 goals with a running top (a child task, 14:44:29). Health flat 8/8.
- The bench human stood at (-11405 1001 355); the marked bot was near (-7430 400 1820): ~42 m away and 6 m lower. Line of sight is a GUESS.
- The damage hook (slot 15) was again entered 0 times.
## Workflow wedrgngwi (trace + verifier, read only, capstone on kl2.exe)
- Handle kind CONFIRMED: [s+0xb0] is the generation-checked pool handle (0x86ca10 builds idx + gen*cap + 1); 0x8ccde0 -> 0x40a880 compares the generation, so a stale handle resolves to 0.
- Slot 83 nonzero path CONFIRMED: 0x68fd70 stores the handle in [goal+0x14] BEFORE the state test; state not 0/4 -> 0x7bbf70 (pop) and no AddGoal; vt+0x1b4 0x6e49b0 removes every prio-0x96 entry
  (also a real Attack); AddGoal 0x6cabf0 refuses role 3 because ZAttackTarget vt+0x24 (0x429f30) returns 0. The entry never expires (byte 0).
- ZAttackTarget tick 0x4f4460 for a ZFFPlayer target: the class tests leave [ebp-0xc] and [ebp-0x10] at 0 (only the first class sets the target), so
  Mode A ([body+0x5c8] != 0) ends with no shot; the direct body shot 0x6e4 at 0x4f4605 is unreachable for humans.
  Mode B jumps to the route branch 0x4f4ad2 before the entry-flags test; 0x4e1750 must accept a path point (distance under ~2x weapon range + a nav check vt+0x80 on [[0xdd2640+0xac]+0xc], untraced),
  then RunChild ZRunToPosShootingTask [s+0x56c]. At 0x4f4ccd 0x8bd420 rewrites the HOLDER from the B entry (flags | 1): HolderFix is lost.
  A B entry made by 0x425fa0 for a human has flags 0, so the child's fire test 0x616480 fails unless the engine already set 0x10 (range) without 0x4 (same team).
- Crash risk CONFIRMED: no null check on 0x8ccde0's result (0x4f44a7, 0x8bd468, 0x426014). A leaver / dead human whose node is freed -> AV (whether FA frees it is a GUESS).
- Guards added (bs25, out_tag_1103n): AttackHandle calls only when 0x8ccde0(handle) == the holder pointer and the +0x658 goal state is 0 or 4; skips are counted ("stale handle").
- Next lever candidate: set 0x11 in the bot's B-list entry for the human (body+0x698, lookup 0x4c75f0) so the rewrite keeps the fire bits. Entry layout not traced yet.

## bs25 (out_tag_1103n, guarded AttackHandle on DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- Calls: DM03 10, DD05 9; skipped (busy / stale) 0, stale handle 0: the guards never fired.
- First call: ZAttackTarget state 0, becomes current; DM03 once ran a child (stack 3, top 54538e60 state 2, 14:59:33). Within ~2 s the goal is state 4.
- Every later call: goal state 4 -> 4, [s+0x74] == the goal ("it is current"), stack 1, top = the goal in state 4. Re-adding a terminated goal does not reset it,
  so the bot may sit on a dead goal (frozen-bot risk from wedrgngwi item 6). Human hp 550 flat on every read (DM03 6, DD05 9).
- Human ~ (-1214 702 -12237) on DM03, (-11803 1007 583) on DD05.
- Next: wuwffuc4b (how the engine resets a state-4 goal, why it terminated) and w0bnwus0v (B-list entry flags for the human).

## Workflow wuwffuc4b (goal restart; trace + verifier, read only)
- Nothing resets [g+8] after construction. Scheduler 0x63c5c0 takes the stack top: state 2 resumes, state 0/4 -> Run 0x65bbf0 (fresh: [g+0x11]=0, state 1, Activate vt+4, 2, tick vt+8, 3, vt+0xc, 4).
  After a state-4 run the scheduler frees [g+0xc] and pops g (0x63c7b5). CONFIRMED.
- Back on the stack only via the arbiter 0x81eb90 switch path 0x81ec3a-0x81ec91 (pops the WHOLE stack via 0x7bea40, writes [s+0x74/0x78/0x7c], pushes the winner, +0x12=1) or 0x7bbf70
  (re-pushes the BOTTOM goal). Early return 0x81ec18 when the winner is already [s+0x74]. AddGoal never restarts. CONFIRMED.
- Slot 83 correction: nonzero handle + goal state 1-3 -> only [s+0x720] = handle, return. State 0/4 -> 0x68fd70, vt+0x1b4 (0x6e49b0 -> RemoveGoal 0x8883d0 on 11 slots, prio 0x96), AddGoal, vt+0x50(1) = arbiter(1).
- bs25 "stack 1 top g state 4" = a pre-scheduler snapshot: each call DID re-run g when [s+0x74] != g (case A); the run ends at 0x4f4e01-0x4f4e04, the normal end after the entry
  fire test (0x4f4da6 / 0x4f4db1) fails on flags 0. Case B ([s+0x74] == g after a run): empty stack, every later arbiter call early-returns, Idle (0x64) cannot beat g (0x96): FROZEN bot.
- Levers: EntryFix (bs26) for the fire test; OnlineBrainTraitorRestart (out_trs_1103p, UNTESTED): clear [s+0x74] before our slot-83 call when it equals g (0x651d5b pattern), and an unfreeze
  (g state 4 + empty stack + [s+0x74] == g -> vt+0x1b4, [s+0x74]=0, arbiter(1)) so Idle runs again.

## bs26 (out_tef_1103o, EntryFix + AttackHandle on DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- ZRunToPosShootingTask (vt 0xbd0ba4) state 2 on the stack with holder = the human, holder flags 011: DM03 178 slot-113 calls (163 human holder), DD05 590 (307). Human hp 550 flat (DM03 19, DD05 20 reads).
- EntryFix round total: set 0, kept 0, no entry 0, stale 0 = the gate (+0x658 vt 0xbd1104, current, state <= 2, handle != 0) never passed. bs27 dumps the gate inputs, stack and B list per child task.
- Every call: "current goal X -> g" with X != g (case A of wuwffuc4b): each call re-runs g; it ends at once again (state 4 on the next call).

## bs27 (out_trs_1103p, EntryFix + Restart + AttackHandle on DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- DM03: EntryFix gate passed sometimes: set 1 (flags 015 -> 011, so bit 0x4 = same team was cleared), already set 5. Restart cleared [s+0x74] 8 times, unfroze 0. Human hp flat (0 drops in 22 reads).
- DD05: 0 CoverFire / attack calls; ZRunToPosShootingTask was seen under a normal goal (vt 0xbd0674): chain 0xbd02bc -> 0xbd04ac -> 0xbd0ba4.

## Workflow wqb7g1pxd (child fire path, tracer + verifier, read only)
- Tick 0x4a7e60: three call sites of body vt+0x6e4 = 0x62a540 = SetAttackTarget(handle, prio, secs): burst 0x4a85eb (0.5 s), NEAR 0x4a86d8 (3.0 s, no flag test, needs byte [task+0x24]), shot A 0x4a822d (after a ~2 s start delay + 0x80dcf0). CONFIRMED.
- 0x62a540 only stores [body+0x544] (aim, read at 0x815852 -> vt+0x344); it bails if [body+0x68c] > prio, body not alive, vt+0x620/0x624 true, or brain mode 6. No shot. CONFIRMED.
- Burst gates: [s+0x5a8]==0, 0x449cf0 != 0xb, mode [[s+0x6d8]] not 5/6, 0x616480(holder flags) true, random > 0.2, 3-4 s lockout, distance to the task dest > 300. CONFIRMED.
- The trigger (verifier): after 6e4 the burst path runs ZFireWeaponTask (vt 0xbd0bd4, tick 0x7c02b0) via brain vt+0x164(1) when 0x4d2750(body); it calls 0x8c1830 -> 0x8dc6a0 -> 0x8b84b0 (burst plan) -> 0x719b00 (accuracy), plan at [body+0xfc]. Target = holder [s+0xac] via 0x5990e0 (so HolderFix flags matter). CONFIRMED to the plan.
- 0x8b84b0 distance gate vs tuning [[0x168d7c0]+0x38c] (+0x3a4 variant): the tracer read it as a max range, the verifier as a min distance. Unresolved; probe.
- Victim: ZFFPlayer slot 423 0x458880 -> 0x4db580; friendly-fire drop at 0x4db5ab via 0x7aca80 (0 for roles >= 2, GUESS host role 2). Untraced to the final apply.
- Most likely blocker (GUESS): our slot-83 calls (Restart/EntryFix/AttackHandle) re-run or pop the parent ZAttackTarget so the child lives only 1.5-2.5 s, before ZFireWeaponTask fires.
- Next: read-only probes (0x62a540 ret + [body+0x544/0x68c], 0x7c02b0 call count, 0x8b84b0 ret + tuning floats + distance, 0x4db580 / 0x7aca80 on the victim) and a toggle that skips slot-83 calls while the child runs.

## Workflow w6wznnvc5 (ZFireWeaponTask owner, shot dispatch, victim path; tracer + verifier, read only; verifier's corrected report)
**Corrected report: why a host bot's ZFireWeaponTask never lowers a host-local human's hp (kl2.exe, static, read-only)**

Method: I disassembled each claim myself. Labels are HELD, WRONG (with the correct reading), or UNVERIFIED. CONFIRMED means I read it in the disassembly. GUESS means I did not.

**A) Where the task lives and how to observe it**
- HELD, CONFIRMED: ZFireWeaponTask has vtable 0xbd0bd4 and tick 0x7c02b0. It is entered from the ZRunToPosShootingTask burst path (vtable 0xbd0ba4, tick 0x4a7e60). That path calls body vt+0x6e4 (0x62a540), which only sets the aim target. It then calls `vt+0x164(1)` (0x8cb920), which builds the child, and RunChild (0x521350) runs it.
- Tick gates:
  - 0x7c02e0-0x7c0321: waits while the holder's `+0x774` is set.
  - 0x7c0435: `0x7836b0(body,-1)`.
  - 0x7c0455-0x7c047b: flag tests.
  - 0x7c0584: targeted aim `0x574af0(F, holder, 0, -1.0)`. This sets `[F+0x28]` and calls body vt+0x6e0.
  - 0x7c06a4: `call 0x8c1830`.
  - 0x7c0748: `call 0x8c62e0`.
  - 0x7c074d: sets `[task+0x15]=1`.
- `[task+0x15]` is a done or fired flag set after the shot call. It is not a "shot landed" flag. Treat it as that, not as proof of damage.
- Observation points: the task's tick entry 0x7c02b0, the return of 0x8c1830, and `[body+0x550]` before and after.
- UNVERIFIED: 0x8b84b0 min-distance compare and `[s+0x98]=1` at 0x8f55d0. Both are taken from online_bot_damage.md.

**B) Call chain and hold-fire gates**
- WRONG, tracer's reading of 0x8c1830 (return value): it does not just return a delay where "<=0 means no shot".
  - The shot is dispatched inside it. 0x8c19fb calls 0x8dc6a0, then 0x8c1a81 and 0x8c1a99 call 0x6c81a0.
  - Hold paths return +0.1 (`[0xb4c788]`) or 0.0 (fldz). So a returned 0.1 means held, not fired.
- WRONG, tracer's argument order for 0x6c81a0: it is (count, item), not (F, item, count).
- What 0x6c81a0 does, CONFIRMED:
  - `[body+0x550] += count`.
  - It stamps `[[body+0x54]+0x34]`.
  - It calls body vt+0x6c0 (0x432440) with (count, 0).
  - So `[body+0x550]` rising means a shot was dispatched.
- Item side:
  - Item vt+0x2cc (0x536dc0) only stores a vector to `[item+0xc8..0xd0]`. It does not create a projectile or raycast, so the tracer's GUESS is resolved as no.
  - Item vt+0x25c (0x8a3510) is a state switch. State 8 calls vt+0x338 (0x7d3360) when `[0x15351e4]==0`.
  - The weapon controller is `F=[s+0x6a0]`, item `[F+4]`, burst plan at `F+0x34` stored in `[item+0xfc]`. 0x4f2460 resets F (`[F+0xc]=[F+0x10]=0`, `[F+0x1c]=-1`, random burst count, flags in `[F+8]`).
- GAP, not located: the actual ProjectileHit or bullet creation site. It is in the item tick or after state 8, along vt+0x338 -> 0x7d3360 -> vt+0x344 (0x8bf680). That chain is a GUESS and not traced.

**C) Victim side (ZFFPlayer)**
- Chain, CONFIRMED: ProjectileHit message (`[0x1548d10]`) -> victim slot 89 -> slot 424 (0x4db580) -> router slot 422 -> slot 423 -> 0x6e3400 -> health write 0x8a7c60.
- WRONG, tracer's claim that 424 "does the hp write": 0x4db580 only builds the record. It calls slot 422 at 0x4dbc61. The hp write happens later via 423 -> 0x6e3400 -> 0x8a7c60.
- Gaps the tracer missed. Each can zero or drop damage:
  1. 0x4db58c (call 0x8e6a20; cmp eax,0x28 at 0x4db591): early drop when `[sm+0x70] >= 0x28`. `sm` is the session object `[0x168e598]`. Role is `+0x54` (2 = host, 3 = client), type `+0x5c` (4 = FA/Arcade family), state `+0x70` (0x19 = round).
  2. 0x7e1700 routing: it drops only when the attacker is not a ZFFPlayer and the victim is remote (station ownership 0x7de570 / 0x9425a0, `[victim+0x274c]`). A host-local victim reaches slot 423 directly, so routing is NOT the blocker for a host-local human.
  3. 0x6e3400 sub-mode 0 (`[0x168e59c]`: 0 = FA, 1 = UCC, 2 = C&R): it zeroes the delta when all of these hold.
     - The attacker is a ZFFPlayer-class crew member that is not a traitor (`+0x2726`) and not police (`+0x2723`).
     - The victim is neither police nor traitor.
     - `[rules+0x285]==0`, where rules is `[0x168e9e4]+0x54`.
     - Fix for a bot that must hurt crew: set the bot's `+0x2726=1`.
  4. Global `[0x1535a2c]`: 1 skips the health write at 0x8a7c60. 2 puts health back to 0.01.
  5. 0x458880 has the down trigger 0x8da3b0 gate at 0x458e7f, then calls 0x6e3400 at 0x458ea8. If the trigger fires, the hit is routed to the down handling instead of a plain hp loss.

**D) Cheapest probe set, in order**
1. `[body+0x550]` delta per burst, plus the 0x8c1830 return. This shows whether shots are dispatched at all.
2. At 0x4db580 entry, log the attacker body class, `[sm+0x70]` and `[0x1535a2c]`. This tells which of gaps 1, 3 and 4 is hit.
3. At 0x6e3400, log the delta before and after, `[rules+0x285]`, and the attacker and victim `+0x2726` / `+0x2723`.
4. Also log `[victim+0x438]` bit 0x12, `[victim+0x274c]`, and the 0x8da3b0 result at 0x458e7f.
5. Decision rule:
   - `[body+0x550]` flat: the problem is upstream (B), meaning the hold-fire gates or the 0.1 returns.
   - `[body+0x550]` rises but no record reaches 0x4db580: look at the missing projectile creation site (B gap).
   - The record arrives but the delta is zero: gap 3 first, then `[0x1535a2c]`, then `[sm+0x70]`.

**What changed from the tracer's report**
- 0x8c1830 return semantics: the shot is dispatched inside it, and hold returns are +0.1 or 0.0.
- 0x6c81a0 argument order: (count, item).
- Slot 424 (0x4db580) builds the record; it does not write hp.
- Item vt+0x2cc: only a vector setter.
- New gates added: `[sm+0x70]>=0x28`, the 0x8da3b0 down trigger, the 0x6e3400 same-side zeroing with `[rules+0x285]`, `[0x1535a2c]`, and the 0x7e1700 ownership drop, which does not apply to a host-local victim.
- `[task+0x15]` is a fired flag, not a damage result.
- Still open: the bullet creation site, and a re-check of 0x8b84b0 and `[s+0x98]`.


## bs28 (out_tfp_1103q, FireProbe + HoldFire on top of bs27 keys, DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- HoldFire: orders skipped DM03 165 (allowed after 6 s 1), DD05 197 (3). ZRunToPosShootingTask episodes: DM03 12 (longest 6047 ms), DD05 26 (longest 43625 ms, one still open at round end).
- In EVERY FireProbe sample the body aim target [body+0x544] = 0 (prio 0, once 5; expiry 0), b576 01, b57d&0x10 1, [s+0x5a8] 0, [s+0x700] 0, mode 1. So SetAttackTarget (0x62a540) never registers:
  the run task's burst path (0x4a84b7) never reaches its 6e4 call, or 6e4 bails. The fire child is never started (ZFireWeaponTask 0 on the stack; it would be a child anyway).
- Holder: human 35c66030 flags 011 alternates with another holder 35ce6760 flags 010 (fails 0x616480: bit 0x10 = in range clear). Distance to the human 55-72 m. Tuning [[0x168d7c0]+0x38c/0x394/0x3a4/0x3ac] = 600 2.5 50 5.
- hp 550 flat (DM03 6, DD05 4 CoverFire checks).
- Candidates for the dead burst path: 0x449cf0([s+0x64c]) == 0xb; the 0.2 random roll (cannot block every time); d to the task destination <= 300 (the NEAR leg, which never shoots unless byte [task+0x24]);
  holder flag flips between ticks; 0x6d9eb0 hold. Next probe: [task+0x14..0x1c] destination vs bot position, byte [task+0x24], the 0x449cf0 stance, [body+0x550] shot counter.

## Workflow wdntba8eu (why the burst path never aims; read only, tracer + verifier)
- The tick 0x4a7e60 is a coroutine; one shared ZRunToPosShootingTask per soldier at [s+0x56c] (built 0x6ab2f4), args set by soldier vt+0x74 -> 0x5faeb0 (dest [task+0x14..0x1c], [task+0x20], byte [task+0x24]).
- SKIP1 0x6d9eb0 = [s+0x700]==0 && (mode==6 || byte [body+0x5c8]==0); false -> wait 0.2-0.4 s, loop, never any 0x62a540 site. CONFIRMED.
- [body+0x5c8]: set 1 by the body ctor 0x83043e (and 0x6420d4), cleared only in SelectWeapon 0x511450 (0x511536 on a real switch, 0x51149b mode 6). CONFIRMED by a .text byte scan.
- Arcade: soldier tick block 0x708912 runs only when [s+0x88]==2: body vt+0x6e4(holder) at 0x70898e and SelectWeapon(-1) when [body+0x5c8]!=0 at 0x7089ad. Online bot [s+0x88]=1. CONFIRMED.
- Only 0x44ab50 (from ZFireWeaponTask 0x7c02b0) clears [body+0x544], so an always-0 aim = 0x6e4 never reached. Shot A at 55-72 m is nearly dead (0x80dcf0 alt path); the burst is the live route.
- Ranked: SKIP1 false via [body+0x5c8] ~55-60 % (GUESS until probed); bl latched ([s+0x5a8] at task start) ~10 %.
- Built: FireProbe ext2 + OnlineBrainTraitorWeaponReady (b2be1851a). bs29 (TraitorByte) had no data (owner came home).

## bs30 (out_twr_1103s, + TraitorByte + WeaponReady, DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- [body+0x5c8] == 0 on every slot-113 call (DM03 696, DD05 1000): SKIP1 0x6d9eb0 is OPEN online. wdntba8eu's lever 1 refuted; WeaponReady cleared 0.
- Both marked bots (DM03 bot 5, DD05 bot 1) have ZFFActor bodies (vt 0xbb3bac): TraitorByte not applicable (ZFFActor 696 / 1000).
- Still: aim [body+0x544] 0 in every sample, ZFireWeaponTask 0 episodes, hp 550 flat (DM03 6, DD05 10 checks). [s+0x5a8] 0 (bl not latched), [body+0x76c]/[body+0x770] 0, [body+0x860] 0, [s+0x88] 1.
- Episode starts: the shared run task is re-armed every ~1-2 s with a new dest, [task+0x20] -50.0, byte [task+0x24] 0, [task+0x28] 2; d to dest mostly 1-5 m (near leg, which needs [task+0x24]) and sometimes 25-160 m. ZAttackTarget's own call (byte 1) seen with dest 55-72 m. DM03 episodes 18 (longest 5.7 s), DD05 19 (longest 30.4 s).
- [body+0x550] on ZFFActor holds a float-looking value (0x3eXXXXXX), not the 0x6c81a0 shot counter; [s+0x550] rose 124 -> 261 / 41 -> 380 (meaning unknown).
- Holder still flips 011 / 010. Human 37-72 m away.

## Workflow wgby0tb0u (gates after SKIP1, tracer + verifier, read only)
- Bot bodies are ZFFActor (vt 0xbb3bac); the ZFFPlayer vtable ends at +0x6a8, so the fire task could not run on one. 0x6e3400 keeps a ZFFActor attacker's full hit: TraitorByte not needed. CONFIRMED.
- 0x8b84b0 tuning +0x38c (600) is a MINIMUM distance; it only picks plan vs single shot, 0x6c81a0 fires either way. NOT a blocker. [0x15351e4] never written (0). 0x4c36c0 = out-of-ammo reaction, not the bullet.
- 0x8cb920 returns the ctor-built ZFireWeaponTask [s+0x570] (sets +0x14=1). The fire task aims at holder [s+0xac], not [body+0x544]: aim 0 alone does not prove no shot.
- Fire task 0x7c02b0 gates: 0x5cced0 (AI stop), 0x7836b0(body,-1) active weapon, holder flags bit 1 + 0x10 (010 fails), 0x739030 empty, 0x561470 burst done; holder ZFFActor with +0x774 takes another path.
- Ctrl tick 0x8c1830: item, ammo (0 -> reload), range hold at 0x8c1985 when 2R < d (R = template [item+0xc4]+0xe0, UNREAD; 55-72 m needs R >= 27.5-36 m).
- Trigger 0x6c81a0 -> ZFFActor::FireWeapon 0x432440 ([body+0x50c] vt+0x88 stunned, vt+0x654 raised or [body+0x824]) -> item 0x8a3510 -> 0x7d3360. Bullet -> slot 89 hop UNREAD.
- 0x7e1700 tests the ATTACKER first (ZFFPlayer mask, 0x7de570([+0x274c]) = not locally owned), then the victim at 0x7e17f9: a client-seat human may route differently. UNVERIFIED.
- Ranked: (1) run-task re-arm every 1-2 s cuts the fire task, (2) burst-entry holder flags / d > 300, (3) 2R < d range hold, (4) active weapon / ammo state, (5) 0x7e1700 routing. Next: FireProbe3 (workflow wbp9fee9q) = counters on 0x7c02b0..0x7e1700 + 0x5faeb0 re-arm callers + ctrl/item/template fields.

## Workflow w8tlxwm93 (bullet -> victim hp, tracer + verifier, read only)
- 0x7d3360 sets pending shots [item+0xe8] from [item+0x104] (capped by ammo vt+0x2fc); message 0x10 = replication only. Real shot driver = item tick 0x488ad0 (per-frame cap [0x1535230] < [[0xdd265c]+0x8b4] or owner-type bl / bytes [136]/[137]; time loop vs [db+0x48]) -> per-shot 0x4cb7a0, [e8]--. CONFIRMED.
- 0x4cb7a0: owner = 0x8ccde0(handle [item+0x5c]) (null -> return at 0x4cb7cb). Byte [esp+0x1f] = bit 12 of [[owner+4]+0x3c] OR owner type matches ZLNKOBJ mask [0x153a89c]/[0x153a898]; if 0 -> 0x4cc9d2 = sound + owner message only, NO ray, NO projectile, NO hit. CONFIRMED (top suspect for a bot).
- [esp+0x17]==1 -> ray test 0x713e80; ==0 -> projectile spawn 0x4cc655. [esp+0x7c] (shooter player ptr) is set only for ZFFPlayer shooters, so for a ZFFActor the ray path skips 0x4dfb00 / 0x7472b0 / effect send vt+0x250 / 0x717f20 (where the damage record is made on that path is NOT found; 0x713e80 -> entry vt+0x8c may make it).
- Victim ZFFPlayer slot 422 0x7e1700: networked roles 2/3 (0x863a60) -> victim vt+0x3d0 = bit 18 of [victim+0x438] (not "controlled here") -> apply. Else a non-ZFFPlayer attacker (bot) -> 0x7e1800: 0x7de570([victim+0x274c]) true (station remote OR its [+0x14] id is 0) -> hit DROPPED silently. A client-seat human cannot be hurt by a host bot on the host by design. CONFIRMED.
- 0x458880 (vt+0x69c apply) early gates: word [[victim+0x54]+0x3a] != 0 skips all; vt+0x5d8()==0xb with [rec+0xc] -> return; then 0x7f6850, 0x863a60, 0x4ea3b0, 0x8da3b0 (unread).
- Ranked: (1) [esp+0x1f] = 0 for the bot owner, (2) ZFFActor ray path skipping the impact, (3) client-seat victim drop at 0x7e1800, (4) host-local victim with [victim+0x438] bit 18 clear, (5) [[victim+0x54]+0x3a], (6) null owner handle.
- Data-only probes (no hooks needed): [item+0x138] (shot routine calls, ++ at 0x4cb8b9), [item+0xe8] falling, [item+0x160] vs [[0xdd2640]+0x44], [item+0x5c] -> owner, [[owner+4]+0x3c] bit 12, owner type vs ZLNKOBJ mask; per human: [+0x438] bit 18, [+0x274c] and its [+0x14], [[+0x54]+0x3a], hp; [sm+0x54/0x5c/0x70], [0x1535a2c].

## bs31 (out_fp3_1104a, + FireProbe3, DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- Both detours installed (0x8c1830, 0x5faeb0). The weapon controller tick ran for the marked bot: DM03 bot 5 91 calls, DD05 bot 2 54 calls, every one returning to 0x7c06b2 (inside ZFireWeaponTask 0x7c02b0). The fire task IS running.
- The bot SHOOTS: ammo [item+0xdc]^0xbeebbeeb DM03 18 -> 12 -> 0, DD05 30 -> 24 -> 22 -> 14; pending shots [item+0xe8] 2 (DM03), 0xa (DD05). [F+8] 0x31/0x33/0x35/0x91/0x95 (0x10 auto, 0x20 fire phase, 4 burst done, 0x80 pause).
- Weapon template R [+0xe0] 6000.0 (2R 12000) vs bot->holder 4732-5879 cm: the range hold passes. [s+0x570] fire task present, +0x14 = 1.
- Body: [+0x5c4] 0, [+0x68c] 0, byte [+0x576] 1, [+0x654] 0, [+0x50c] set, [+0x824] 1 + [+0x42c] 4 in some samples (weapon raised).
- Run-task re-arms: one caller only, 0x800650 (also for all other soldiers); DM03 14 in the round, DD05 20, gaps mostly 3-20 s (bursts of 30-50 ms when the goal re-picks). Not the blocker.
- Correction: "aim [body+0x544] 0 = no shot" (bs28-bs30) was wrong: the fire task aims at the holder directly (wgby0tb0u). The loss is from the bullet to the human's hp.
- Host log: botfill counted "other hits on bots untouched" 2-5 per 5 s: some may be the traitor's rounds hitting bots (unproven). Next: bs32 FireProbe4 ([item+0x138] per-shot calls, owner bit 12, victim route fields).

## bs32 (out_fp4_1104b, + FireProbe4, DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- [item+0x138] (per-shot 0x4cb7a0 calls) rose 56 (DM03 bot 6) / 34 (DD05 bot 1) between samples; pending [+0xe8] fell 11 / 0. [+0x160] < [[0xdd2640]+0x44] in every sample (no same-frame dedupe).
- Gate: "bit12 0" on all 12 samples, owner never unresolved. BUT the resolved owner's [0] is 7c2cec14 (DM03) / 506fec14 (DD05): not a kl2 vtable (0xb.....), and [[owner+4]+0x3c] = 4b418182 in both runs. The game calls owner vt+0x30 at 0x4cb819, so the real owner must have a real vtable: FireProbe4 resolves a different object. Gate verdict OPEN.
- Victim: holder ZFFPlayer, [+0x438] 0 (bit 18 clear), [+0x274c] set, [[+0x274c]+0x14] 00c00001, word [[+0x54]+0x3a] 0, hp 550 flat; session [sm+0x54] 2 (host), [+0x5c] 4, [+0x70] 0x19. Route undetermined: [0x168fd00] (local id) not logged.
- wx315tp48 (read only, 3 plans + 3 checks): lever B (impact block at 0x4cc4dd) is FX/surface only, NOT the loss. Lever C (0x7e1700 -> 0x7de570([victim+0x274c]) true -> return = drop for a non-ZFFPlayer attacker, no send on that branch; a ZFFPlayer attacker's hit is packed and sent via 0x7a8410) is the likeliest for a client-seat victim. Lever A (gate at 0x4cc389, only consumer of [esp+0x1f]; bit 12 writers 0x441041/0x441060/0x5ed841 set, 0x455562/0x6a4fa0 clear, ZRenderEntryGeom ctor 0x5ed700) is a bench A/B. 0x4ca000-0x4cd000 is unhashed.
- Next: FireProbe5 (wr2kwhoqm): counting detour at 0x4cc389 reading the game's own owner and gate byte, a counting-only slot-422 wrapper (route + hp before/after), [0x168fd00] on the victim line.

## bs33 (out_fp5_1104c, + FireProbe5, DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults: THE GATE
- Detour 0x4cc389 installed (stub 27 bytes); slot 422 wrapped on the private ZFFPlayer table.
- Gate byte [esp+0x1f]: MARKED pass 0 / fail 120 (DM03), 0 / 459 (DD05); other pass 0 / fail 102 (DM03), 0 / 4695 (DD05). Every host AI shot goes to 0x4cc9d2 (sound + message only). [esp+0x17] (ray) = 1.
- Owner register [esp+0x54] == fresh 0x8ccde0([item+0x5c]) on all logged samples (FireProbe4's owner was right after all). [owner] = 50700c14 in both maps: a heap vtable copy; its slot +0x30 = 0x557ba0 (ZFFActor getter). [[owner+4]+0x3c] = 4b418182, bit 12 = 0.
- FireProbe4 victim line with the local id: station [[victim+0x274c]+0x14] 00c00001 == [0x168fd00] 00c00001: the holder is the HOST-LOCAL human, route = apply. The slot-422 wrapper saw 0 hits (it only covers remote-seat victims; none were hit since no shot passed the gate).
- Open: why bit 12 (set by 0x5ed841 in the ZRenderEntryGeom ctor and by 0x441041/0x441060; cleared 0x6a4fa0/0x455562) is 0 for every online host shooter, whether Arcade has it set, and which object gave these bodies a heap vtable. Workflow wu60j1ez0.

## bs34 (out_gf_1104d, GateForce on top of bs33 keys, DM03 + DD05): PASS 4 seats, 0 asserts, 0 faults
- gateforce: slot 12 of the private ZFFActor table 50701c14 wrapped; real answer 00027b7c -> 0000077c. DM03: 0x4cb819 seen 202, forced 114, other bot 88. DD05: 2153, forced 408, other bot 1745.
- FireProbe5: MARKED pass 114 fail 0 (DM03), pass 407 fail 0 (DD05); other shooters pass 0 (fail 88 / 5237). The forced path (0x4cb838 -> 0x7638a0 -> 0x7cb080, 0x4cb974 transforms) did not fault.
- hp: CoverFire health checks 6 + 9 + FireProbe4 victim lines, all 550 -> 550. Slot-422 (remote victims) hits 0. FireProbe4 victim routes DD05: apply 4, drop (station remote) 2.
- The aim target [body+0x544] is still 0 (FireProbe line 03:32:18: aim 00000000, holder flags 011, dist 52.7 m), so the shot direction may not point at the human at all.
- Cops (stock ZFFActor table 0xbb3bac) fail the same gate online (bit 12 0, class 00027b7c): online cops' shots are sound only as well (cop->bot hits arrive by another path).

## w9x3uc1vs (research + adversarial verify, static) 11-04
- Item vtable starts 0xbc042c (0xbc076c is the +0x340 slot). vt+0x250 = 0x7638a0 thunk -> [vt+0x254] 0x7cb080 (shared ZItem muzzle transform). Class force == bit-12 force in post-gate state; class force avoids touching render flags.
- Gate fail jumps straight to 0x4cc9d2 (sound + owner vt+0x120 message); muzzle flash 0x4cc891 is skipped too. [esp+0x17] is rewritten at 0x4cc377/0x4cc384 (0x150cb38-class test on 0x8ca940's object): ray 0x713e80 vs projectile 0x4cc655.
- Forced path extra calls (bl=1, 0x4cb974): 0x51f910, 0x60ad10, 0x6be1c0, 0x42a4d0 (only when [item+0x140..0x148] == 0). Risks: 0x4a30e0 (fault at 0x4a3118 if word [N+0x5a]==0 with bit 30; null -> 0x4cc3a5); 0x7cb080 branch B -> 0x857110 identity = origin (0,0,0).
- Arcade passes because its bot nodes have a render entry (bit 12 set by 0x5ed700/0x441041); why online bots lack one is not found.
- Client seat: 0x7e1700 drops a bot attacker's hit at 0x7e1800. Lever: wrap kns_vt[422] (chain after FireProbe5's wrapper), host role 2, bot attacker + remote victim -> call 0x891490 (ecx = [victim+0x274c], six args) which sends RMCReceiveHit; client stub 0x59f140 applies via 0x458880.
  Gaps: kns swap is lazy (new clients keep the stock table until the next scan), position/direction floats lost, bot handle may not resolve on the client, double-apply, skipped rules vt+0x1e4 notify (kill credit). Use 0x9425a0 for the remote test, not [0x168fd00].

## bs35 (out_fp6_1104e: GateForce + FireProbe6, DM03 + DD05, 2 seats) + arc35 (same dll, Arcade offline, 1 seat): PASS, 0 faults
- Online MARKED: DM03 shots 120, bl=1 120, branch A1 120 (bit 0x200000 set, owner direct, 0x8ccde0 -> the bot), identity fallback 0, gate passed 120, ray 120, request/child non-null 120, projectile 0. DD05: 48 / 48 / A1 48 / ray 48.
- Origin is a real hand position: |origin-bot| 113-118 (DM03), y (up) ~100 above the bot root. vecB = *eax at 0x4cc440 is origin + 48.5 (or 17.7 for the DD05 weapon): probably the muzzle tip = ray start [esp+0x28]. vecA = [esp+0xf4] is a unit row of the ray matrix.
- Aim: DM03 bot ~6300 units (63 m if cm) from the host human, running ~375 u/s while firing; best muzzle-matrix-row angle to the human 2-52 deg, buckets <5/<15/<45/>=45 = 19/37/52/12 of 120. DD05 ~4000 units, bot moving away, row error 32-52 deg, (vecB-origin) 118-138 deg from the human.
- arc35 Arcade: same path (A1, ray, request, child) for all sampled shots; bots were shooting cops, not the human (human never attacked: no Arcade hit baseline yet). 2 traitor flags set on DM03, 1 on DD05, FOE/BACKSTAB 0.
- hp: host human 550/550 at round end both maps (script lines 04:07:45, 04:16:20). Faults 0, asserts 0.
- Conclusion: the loss is no longer in the shot code; it is aim (the weapon bone does not point at the human), possibly range / line of sight (40-63 m, human idle at spawn).

## wgqnxsl7e (research + verify, static) 11-04
- 0x4cb7a0 reads no aim point or target: ray = request vt+0x8c(matrix [esp+0xe8], pos [esp+0x28]); direction = weapon-bone transform from 0x7cb080 -> owner vt+0x268 (0x807620 -> 0x425ce0 bone table) -> 0x8c51b0.
- AI aim = ZFireWeaponTask 0x7c02b0 -> 0x574af0 -> body AimAt 0x70f130 ([+0x824]=1, [+0x828] handle, [+0x82c..0x834] offset, [+0x838], [+0x83c], [+0x68c]=5, 0x740270([body+0x8d8])); skipped when byte [body+0x64c] is set. [task+0x14]==0 -> 0x4deb20 aim at a position.
- [body+0x544] is cleared by 0x44ab50 (via AimAt's vt+0x6e8(5) and the fire task's vt+0x6e8(4)): 0 is expected, not a symptom. SetAttackTarget 0x62a540 (prio must be >= 6 and called twice with the same handle) only drives look-at IK; not the lever.
- Refuted: 0x857110 is not origin (0,0,0), it is the item node's world transform. [req+4] / [esp+0x10] at 0x4cc644 is a child of the pooled bullet group (sibling loop), not a hit; 0x4cc4ba stamps the shooter id into [child+0x60]+0x6c and calls child vt+0x15c (probably the real ray / damage).
- Missed by the first pass: 0x425ce0 can return without writing the outputs (stale stack) - bs35 shows this does not happen (A1, sane origin). 0x8ca940 picks a random template; 0x54efb0 may convert the ray to owner-local space; 0x4cc328 per-frame dedupe.

## bs36 (out_ra_1104f: RayAim site 5 = T + M row 2, MaxDist 0) + bs37 (out_ap_1104g: DM03 site 7, DD05 site 2 = aim point only): PASS, 0 faults
- FireProbe7: AimAt mode [+0x824] = 1 on 90/90 (bs36 DM03), 261/270 (DD05); target [+0x828] = the human 90/90 DM03, 141/270 DD05 (the rest another object); byte [+0x64c] never set; AimAt not called within 1 s of any shot (fields set earlier and kept).
- Human beyond template range R (6000) on most shots: bs36 DM03 56/90, DD05 187/270; bs37 DM03 85/104, DD05 192/225 (DD05 bot runs away while firing).
- Ray matrix M (S4, before RayAim): with the T rewrite on (bs36 both maps, bs37 DM03) row 0 is within 15 deg of the human on every sample; WITHOUT it (bs37 DD05) row 1 on 49/222, row 0 never. So M is derived from T (T row 2 -> M row 0) and the game's own ray does NOT point at the human; RayAim row 2 on T steers M row 0. Which row is the ray forward is still unproven.
- Item aim point [item+0xc8..0xd0] before our write: within 5 deg of the chest DM03 60/104 (0.05-0.1 deg), DD05 100/225; [item+0xf8] byte set 0/104 DM03, 62/225 DD05; [item+0xfc] set 104/104, 163/225. Bit 2 wrote the chest point 104/104 and 225/225 (0 refused, 0 faults).
- First ray child at 0x4cc644: [child+0x60] never the human or a player; vtable 0x00b9e9a4 every time; [[child+0x60]+0x6c] = 0 (the shooter stamp comes later at 0x4cc4ba).
- hp 550/550 at round end on all four runs; coverfire health checks flat.
- Conclusion: the pellets carry a correct aim point inside (or just beyond) range, so the loss is the bullet hit/damage path or a victim-side filter, not the aim.

## bs38 (out_fp8_1104h: FireProbe8 pellet funnel + GateForce + FireProbe6/7 + RayAim site 2): PASS, 0 faults
- Sites installed 4 of 6 (0x900d80 Activate and 0x4db580 victim entry are hashed: SessionSafe=0 only, so s2/s5 = 0 by design).
- DM03: shots 124, pellets 124 (1 per shot, s1null 0), hit callbacks 125, hits on a player 0, past the door check 125 (none on a player). DD05: 266 / 266 / 266 / 0 / 266.
- Descriptor: +8 speed 30000, +0xc R 6000, +0x2c..0x38 1000/2/1000/1000, +0x3c 1.0; [comp+0x90] 300, [comp+0x54] 9, [comp+0xb8] 1.0.
- Hit victims (rate-limited sample): DM03 handles 0x606, 0x6aa, 0x6d7; DD05 0x1968, 0x207e - all 'not a player', low handles = probably static level objects/cover between the bot and the human.
- So pellets are created, fly toward the chest and are stopped by geometry: no line of sight. hp 550 on both maps.

## wmcd2s92o + wljmqprl9 (static, verified) 11-04
- Damage carriers are the pellets of loop 0x4cc1c0 (before gate 0x4cc389); 0x713e80 children are ZParticleEmitter FX (vt 0xb9e9a4). Descriptor at esp+0x164 at the loop head (ctor 0x748900 ret 0x4c).
- ZProjectile = component (vt 0xba925c): Activate slot 35 0x900d80, Update slot 25 0x897460 (sweep 0x4cd400, layer mask 6), hit callback slot 36 0x6f7950 called only at 0x8977c9.
- desc+0x44 (moving) = 1 only when template [+0xac]==7, else hitscan (50000-unit step, R not checked): range is not the loss. Loop writes desc+0x48 (frame delay).
- Slot-36 filters F2/F3 only for ZFFPlayer shooters; 0x7aca80 returns 0 for session type 4. F1 ([[0xdd265c]+0x8b1] && [victim+0x780]) and victim-side G1 ([session+0x70] >= 0x28 at 0x4db58c), G3 (null item) remain but are moot while no pellet reaches a player.

## bs39 (out_lg_1104i: LosGate + LosProbe + FireProbe6..8 + GateForce + RayAim site 2): PASS, 0 faults
- LOS answers: DM03 clear 0 blocked 342 err 0; DD05 clear 0 blocked 312 err 0 (physics faults 0). Bot eye -> human chest 61-63 m (DM03), 100-108 m (DD05).
- DM03: Sense skipped the blocked human 342x, HolderFix 0; marked bot fired 0 shots (all callbacks 494 = other shooters).
- DD05: Sense skipped 312x, HolderFix 0, but 187 shots / 187 pellets / 187 hit callbacks, s3human 0; LosProbe at shot time: muzzle BLOCKED 187, eye BLOCKED 187; victim class ZSTDOBJ (handle 0x1bd8).
- Open: is the test ever clear (no control yet)? Which path fires on DD05 without Sense/HolderFix (shared task [S+0x56c] / AttackHandle / stale entry)? -> w18ipq4cv.

## w4funhvyl (static, verified) 11-04: ZAttackTarget mode B
- Slot 83 0x831850: handle 0 -> CoverFire (0xa0); nonzero -> if [[S+0x5ac]+8] not 0/4 only stores [S+0x720]; else retarget 0x68fd70 and, only if [[S+0x658]+8] in 0/4, AddGoal(+0x658, 0x96) + arbiter. CoverFire 0xa0 outranks ZAttackTarget 0x96.
- Mode B: candidates (point 0 = own position), test 0x4e1750 at 0x4f4b92 (al!=0 = clear point here), first clear index != 0 -> RunChild vt+0x74 at 0x4f4bed; none -> [S+0x4fc]=1 + vt+0x13c (0x4f4ba9).
- Verifier: do not build an Approach lever yet (it repeats AttackHandle); first ModeBProbe (slot 83 branch, tick, candidates, RunChild, re-arm 0x800650). Unverified whether Arcade runs ZAttackTarget at all.

## bs40 (out_lm_1104k: LosGate fixed direction + LOS control + ModeBProbe + LosProbe + FireProbe6..8 + GateForce + RayAim site 2): PASS, 0 faults
- LOS control: DM03 bot 5 eye (-91 410 -6214): up50 CLEAR, up300 BLOCKED, +x100 CLEAR, -x100 BLOCKED, +z100 CLEAR, -z100 BLOCKED, down400 BLOCKED, reversed CLEAR -> WORKS. DD05: 6/6 clear, down400 BLOCKED -> WORKS.
- Humans: DM03 54.8 / 57.4 m, DD05 48.6 / 50.5 m from the marked bot's eye, BLOCKED on every query (DM03 334/334, DD05 396/396; 0 errors, 0 physics faults). DM03 marked bot fired 0 shots.
- DD05: 302 marked shots, all blocked from the eye, pellets 302, s3human 0; aim->holder < 5 deg on 261/302 (holder class ZFFActor), aim->human chest < 5 deg 0: the bot shoots at its holder target (stock), not the human.
- ModeBProbe: 2 of 8 sites installed (0x831850 slot 83, 0x800650 re-arm; the 6 in 0x4f0000..0x4f6000 refused by the guard as expected). slot 83 calls 0 both maps; re-arm 25 (DM03), 13 (DD05).
- Data sampler: [S+0x658] set (DM03 target 802d5b24, DD05 target 0) but state 0 on 674/674 (DM03) and 792/792 (DD05) samples; [S+0x74] never the attack goal; [S+0x78] = 150 (0x96) almost always, 4000 briefly; CoverFire state 0; [S+0x4fc] set on 333/674 and 211/792; run task [[S+0x56c]+8] flips 2 <-> 4.
- Conclusion: the line test is right and the humans are behind geometry; the bot never approaches. Some other prio-0x96 goal runs and ZAttackTarget is never started (stock never starts it either, per wc555a9o3).

## wc555a9o3 (research + verify, static) 11-04
- Arcade attack path: ZSoldierAttack [S+0x638] (vt 0xbd0f14, tick 0x6c8350; built in the ZSoldier ctor 0x6ab250 at 0x6ab6fc/0x6ebb20) + Idle [S+0x634] + tactics [S+0x604..0x608] (vt+0x2c evaluate, best > [0xb69b98] via RunChild 0x521350) + ZRunToPosShootingTask [S+0x56c] armed by vt+0x74 0x800630 -> 0x5faeb0 (0x800650 is the return site inside 0x800630).
- Stock never calls slot 83 with a nonzero handle (all 5 callers pass 0 = CoverFire): ZAttackTarget / mode B is not the Arcade path. 0x4e1750's only caller is 0x4f4b92.
- Fire gate 0x616480 tests flags bits 0x1 set, 0x4 clear, 0x200 clear, 0x10 set, 0x40 clear. 0x7088c0 needs [S+0x88]==2.
- Not proven: that Arcade has no fire-time LOS test; candidate 0x5fb040 (physics vt+0x264 call at 0x5fb4f3) unread. Where ZSoldierAttack is activated: untraced.

## bs41 + arc41 (out_mb2_1104l: ModeBProbe v2, online marked bot vs offline Arcade bots): PASS, 0 faults
- Online DM03: 686 samples, current goal vt 0xbd0674 held by Defend [S+0x648] 686/686, states Attack 0 Idle 4 Defend 2; mode [S+0x88]=1 686/686; [S+0x4fc] 1 on 3/15 data lines; [S+0xa8] 0x10; [S+0xb0] 0 (15/15). LosGate blocked 342, shots 0.
- Online DD05: 293 samples, same (Defend 293/293, mode 1); [S+0xb0] 0; LosGate blocked 162, shots 0.
- Arcade DM03 (traitor + control bots): Defend 0xbd0674 mostly, Idle 0xbd0f54 (slot 634) with mode 2 on ~17%; [S+0xb0] 0x320, 0x1e91, 0x525f ... non-zero on 74/120 lines; [S+0xa8] 0x10/0x14.
- Arcade DD05 (control bots): [S+0xb0] cycles 0x364/0x36f/0x37b/0x382/0x386... (changes every second or so = the enemy it engages); [S+0xa8] 0x10..0x17 (bits 0x1/0x2/0x4 vary); [S+0x4fc] set often.
- Conclusion: same goal (Defend) and mode both sides; online the bot never gets a holder/target in [S+0xb0] and the 0x1/0x4 flags, so neither CloseIn nor the NoCover fire clause can pass.

## bs42 (out_mb2_1104l, bs41 kit with OnlineBrainTraitorLosGate=0): PASS, 0 faults
- DM03: [S+0xb0] = 0x320/0x321 on 86 of 88 data lines (bs41 with LosGate: 0 on 15/15); [S+0xa8] 0x01 x46, 0x11 x28, 0x05 x3, 0x10 x3; [S+0x4fc] 1 on 33/88.
  Goal: Defend 638/746, ZAttackTarget (slot 658) current 106/746 (bs41: 0). Shots 199, aim->human chest < 5 deg 190, all 199 BLOCKED from the eye, s3human 0: firing through walls again (bs38). HolderFix in range 262, out of range 76. hp 550 flat.
- DD05: [S+0xb0] 0x1ab/0x1aa/0x39f/0x3dc on 41/41 lines; flags 0x01/0x05/0x10/0x14; Defend 589/590; shots 0; HolderFix in range 0, range unknown 251 (0x10 never set -> fire test fails).
- Conclusion: the empty holder in bs39-bs41 is caused by LosGate (Sense skips blocked humans -> 0x767510 no-winner clear at 0x767f8a). Next: keep the holder with non-firing flags while blocked (HolderSet) + CombatFlag mode 2, so CloseIn can pass without firing through walls.

## bs43 (out_hs_1104n: LosGate + HolderSet=1 + CombatFlag=2 + CloseInProbe=1): PASS, 0 asserts, 0 faults
- DM03: HolderSet writes 28 then kept 139 (holder 0x320 = the human, 0x8ccde0 round-trip yes); [S+0x6fc] 0 on 769/769 samples -> list B; ZCloseIn eval calls 0; CombatFlag mode 2 skipped (6fc) 139, writes 0; marked shots 0 (fireprobe8 shots 0). Current goal ZDefendPosition x769.
- DD05: [S+0x6fc] nonzero 47% (stock writer: squad unleash / modifier / ambush), [S+0x4fc] 58%; list A walked; ZCloseIn eval 30 calls (1.0 x1, 0.0 x29), arm 19; the stock scan replaces our holder (0x3d6, flags 0x10, not a human); humans ~175 m away; 100 marked shots, target 'something else' 100, all BLOCKED from the eye, s3human 0.
- Lists: A[9] = ReactToHumanShield, BecomeTraitor, BoardEscapeVehicle, AttackMountedWeapon, CloseAttack, CloseIn, AttackFromCover, AttackNoCover, ...; B[9] starts the same, C empty.
- Conclusion: the research (wzerqnft4) holds: 6fc gates list A and is 0 for our StayBack squads. Next: CombatFlag mode 3 (write 4fc and 6fc while blocked, restore 6fc) + HolderSet, bs44.
