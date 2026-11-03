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
  1. 0x4db58f: early drop when `[sm+0x70] >= 0x28`. `sm` is the session object `[0x168e598]`. Role is `+0x54` (2 = host, 3 = client), type `+0x5c` (4 = FA/Arcade family), state `+0x70` (0x19 = round).
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

