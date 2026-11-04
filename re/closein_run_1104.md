# ZCloseIn after 1.0: run body, movement task, aborts (wgdab5lbj, 2026-11-04, static)

Research report followed by the adversarial verifier. Where they disagree the VERIFIER wins: the cover branch is NOT the likeliest bs44 cause (it only runs on the 2/7 winning ticks); most probe sites named in the report are HASHED (only 0x6724e0, 0x76e8c0, 0x800630, 0x5faeb0, 0x4a7e60 entry, 0x509f30 may be detoured online).

## Report

FINDINGS: what runs after ZCloseIn eval 0x6724e0 returns 1.0 (static, kl2.exe)

Items marked GUESS or UNREAD were not confirmed. All addresses are kl2.exe. S is the ZSoldier brain (vtable 0xbd0954).

**(1) Defend and the ZCloseIn run/activate vfuncs**
- Defend (0x85f6c0) does not consume the destination.
  - Defend takes the first tactic in the chosen list whose vt+0x2c eval is greater than [0xb69b98] (0.0).
  - It stores the tactic in [goal+0x14] and calls RunChild 0x521350 on it (loop 0x85f8f0..0x85f924).
  - It then yields on 0x55b9f0. If aborted it returns at 0x860300. Otherwise it clears [goal+0x14] and goes to 0x8602bc, then back to the loop top at 0x85f860.
  - So the winner is simply run, and [tactic+0x18..0x20] is read only by the tactic itself.
- The ZCloseInTactic vtable is 0xbd0c64.
  - +4 (init) is 0x66b570, a bare ret.
  - +8 (RUN BODY) is 0x76e8c0.
  - +0xc is 0x66b570.
  - +0x2c (eval) is 0x6724e0.
- The success tail of eval (0x67272b..) does three things:
  - It stores the point 550 cm back along the path ("fstp [esi+0x18/0x1c/0x20]").
  - It calls 0x5caf90(S).
  - It returns 1.0 via `fld1`.
- The run body 0x76e8c0 has two branches.
  - It first calls S vt+0x7c, which is 0x543f20.
    - That returns true if byte [S+0x108]!=0 and 0x72bc70(S) is false.
    - Per bots_dynamic.md, [S+0x108] is 1 for every soldier except the dog (set at 0x6ab290).
  - COVER branch (0x76e935), taken when vt+0x7c is true and S vt+0x18c (0x509f30) returns an index >= 0:
    - It sets [S+0x64c] to the cover position (via 0x713130 on table [0xdd265c]).
    - It runs the task from S vt+0x70 (0x477cf0, returns [S+0x498]) through RunChild.
    - It then checks 0x7b0b70 and may print "PathError in ZCloseInTactic".
    - This branch IGNORES the 550 cm destination in [tactic+0x18..0x20].
  - DIRECT branch (0x76e8ed), taken otherwise:
    - It calls 0x412910 on [S+0x64c] with &tactic+0x18.
    - It then calls S vt+0x74(&dest, 0.0f, 1) = 0x800630, which loads [S+0x56c] and calls 0x5faeb0.
    - The returned task goes to RunChild, then the yield.
    - The tactic's own destination is used ONLY here.

**(2) 0x5caf90(S)**
It only writes a timestamp and starts no movement.
- If [S+0x69c] is non-null, it writes now ([[0xdd2640]+0x48]) into [[S+0x69c]+0xcd0]+0x14.
- Otherwise it writes now into [[S+0x4f4]+0x94], the squad's "last order time".

**(3) The movement task armed (direct branch only)**
- The task is the ZRunToPosShootingTask object at [S+0x56c]. It is created at 0x6ab2d3..0x6ab2fe with vtable 0xbd0ba4 (+4 init 0x8b7940, +8 run 0x4a7e60).
- 0x5faeb0 copies the destination to [task+0x14..0x1c] and the radius (0.0 from ZCloseIn) to [task+0x20]. It sets byte [task+0x24]=1 (shoot flag), then calls 0x76f850 via [[task+4]+0x6a0]. The purpose of 0x76f850 is UNREAD.
- Init 0x8b7940:
  - It calls 0x449cf0 on [S+0x64c] with arg 2. The mode result is UNREAD.
  - It calls 0x510730(S, &dest, mode, radius, 1.0).
  - It sets [S+0x98]=2.
- 0x510730 does three things:
  - It calls S vt+0xb8 to stop the current move and sets [S+0x4e8]=0.
  - It calls 0x46ce40 on the movement component [S+0x4a4], which stores the mode at +0x14, speed at +0x18 ([S+0x500]*scale), radius at +0x20 and target at +0x24..0x2c.
  - It calls 0x5a8dd0 to set the body animation state.
- 0x4d99a0 dispatches by mode through body vt+0x6f4. Mode 0xb is forced when 0x6fd7c0([S+0x40]) and byte [0x168bcea] are set.
- How the component tick turns the target into a path request is UNREAD.

**(4) What aborts, stalls or replaces the movement**
- Cover branch (GUESS, the likeliest cause of the bs44 result).
  - With [S+0x108]=1 the cover finder 0x509f30 runs (the vt+0x7c gate also needs 0x72bc70 false).
  - It aims at a point 10 m (1000.0, 0xb7df80) from the bot toward the target when d >= 2200 (d is the bot-to-target distance, compared against [S+0x6a8]). That point is not the 550 cm point.
  - It then searches for cover within 1100.0 (0xb2b9f0) of that point.
  - If no cover is found (-1), the direct branch runs. If a cover is found, the bot hops to cover nearest that point, not to the human.
- Stall gate "may act" 0x6d9eb0 (inside the run task, at 0x4a8018).
  - It is true only if [S+0x700]==0 and ([[S+0x6d8]]==6 or byte [[S+0x40]+0x5c8]==0).
  - If false, the task never moves. It sleeps a random time and loops via 0x4a86a2.
- Immediate end gate 0x7cad60 (tested at 0x4a7f66 and again at 0x4a86a5).
  - It is true only if [S+0x4e8]==0 and body vcall [[S+0x40]+0x50c]->+0x7c returns 0. When false the task ends at once (0x4a80c8). The body vcall's meaning is UNREAD.
  - Writers of [S+0x4e8] found: 0x42d360 (-1/2/1), 0x541150, 0x653e00 (3), 0x6bee50 (1), 0x769900 (1), 0x7cfac0 (1), 0x7d72c0. The others write 0: 0x47b4c0, 0x4aaf00, 0x510730, 0x56f400, 0x619730, 0x660f60, 0x7a24a0, 0x861720, 0x90a660. Each is a candidate reset or blocker and none has been traced.
- Arrival and hold.
  - The arrival test is 0x60b160(S,&dest) against 300.0 (0xb146e0).
  - With holder [S+0xb0]!=0 and [task+0x24]=1 the task holds and engages at the destination.
  - Far branch 0x4a812c: with no holder it waits randomly. With a holder it moves and shoots via body vt+0x6e4 and re-issues the move at 0x4a8473.
  - A stuck timer (2 s, armed when dist < 100 or 200) leads to "Stuck in ZRunToPosShootingTask. Leaving.".
- Re-evaluation.
  - ZCloseIn's eval timer is re-armed every 1-4 s, and Defend loops. Another winner can displace the run.
  - 0x8602bc writes [S+0x4fc]=1 itself if 0x60b160 < 400.0.
- No squad/StayBack/HeistOnly clamp was found in these paths.
  - The only [S+0x6fc] readers are 0x7b1565, 0x7e576a, 0x807de8 and 0x85f89f, and none is in the ZCloseIn path.
  - Whether the squad +0x30 mode is consulted in the component tick or the tail of 0x875be0 (0x8760dc on) is UNREAD.
  - Goal-priority preemption of Defend (AddGoal 0x6cabf0, prio 0x96) is UNREAD.

**(5) Cheapest SessionSafe lever (GUESS until probed)**
- Data write: set byte [S+0x108]=0 on the marked traitor while it is LOS-blocked, and restore it when it is clear or the pass goes stale.
  - The dog already runs with 0, so the state is supported.
  - It forces the direct branch, so the 1.0 arms ZRunToPosShootingTask to the 550 cm point via 0x800630 / 0x5faeb0.
  - Also check [S+0x700]==0, byte [[S+0x40]+0x5c8]==0 (or [[S+0x6d8]]==6) and [S+0x4e8]==0, or the task stalls or ends at once.
  - Side effect: it also removes cover use for that bot elsewhere (GUESS, UNREAD).
- Alternative: make 0x72bc70 true. This is less clean.
- Read-only probe, sampled at 250 ms and at each 1.0 return. All the call sites below are unhashed, so count-only detours are allowed.
  - Read [S+0x108], the result of 0x72bc70, [S+0x700], byte [[S+0x40]+0x5c8], [[S+0x6d8]], [S+0x4e8], [S+0x500] and [S+0x98].
  - Read [[S+0x4a4]+0x14/+0x18/+0x24..0x2c]. This shows the movement mode, speed and target.
  - Read the [S+0x56c] task state [t+8] and its fields +0x14..+0x25.
  - Log the return of vt+0x18c (0x509f30), which tells you cover or direct.
  - Count calls to 0x76e8c0, 0x800630, 0x4a7e60, 0x510730 and 0x7b0b70. 0x800630 versus 0x7b0b70 shows which branch ran.

Scratch helper: C:\Users\Henri\AppData\Local\Temp\claude\c--kl-merge-kl-merge\d4c7e4f4-84d7-4249-a418-cad3917427d6\scratchpad\scan.py

## Verifier

**Verdict:** the static mechanics in the report mostly hold up. Two of its conclusions do not: the "likeliest cause" claim and the claim that every probe site is unhashed. I re-disassembled every cited address and checked hashed status against `klhook/klranges.h`.

## Per-claim verdicts

**(1) Defend and the ZCloseIn vfuncs**
- **CONFIRMED:** the loop at 0x85f8f0 takes the first tactic whose vt+0x2c eval is above `[0xb69b98]` (0.0). It stores the tactic in `[goal+0x14]` and calls RunChild 0x521350, then yields on 0x55b9f0. A true yield returns at 0x860300. Otherwise `[goal+0x14]` is cleared and it goes to 0x8602bc and back to 0x85f860. Defend does not read `[tactic+0x18..0x20]`.
- **CONFIRMED:** vtable 0xbd0c64 has +4 = 0x66b570, +8 = 0x76e8c0, +0xc = 0x66b570 and +0x2c = 0x6724e0.
- **CONFIRMED:** the 1.0 tail at 0x67272b computes the point 550 cm back along the path. The constant at 0xb35790 is the double 0.5, applied to `-[S+0x6a8]`. It stores the point in `[esi+0x18..0x20]`, calls 0x5caf90(S), runs `fld1` and returns.
- **CONFIRMED:** S vtable 0xbd0954 has +0x70 = 0x477cf0 (returns `[S+0x498]`), +0x74 = 0x800630, +0x7c = 0x543f20 and +0x18c = 0x509f30.
- **CONFIRMED:** 0x543f20 returns true when byte `[S+0x108]` is nonzero and 0x72bc70 is false.
- **CONFIRMED:** the run body's direct branch (0x76e8ed) calls 0x412910 on `[S+0x64c]` with `&tactic+0x18`, then vt+0x74 with `(dest, 0.0, 1)`, then RunChild and the yield.
- **CONFIRMED:** the cover branch (0x76e935) never reads the 550 cm destination. It writes the cover position into `[S+0x64c]` and runs the `[S+0x498]` task. 0x7b0b70 tests `[S+0x4e8] == -1` and gates the "PathError in ZCloseInTactic" message.

**(2) 0x5caf90**
- **CONFIRMED:** it only writes a timestamp, to `[[S+0x69c]+0xcd0]+0x14` or else `[[S+0x4f4]+0x94]`. It starts no movement.

**(3) The armed movement task**
- **CONFIRMED:** the task object is created at 0x6ab2fe with vtable 0xbd0ba4 (+4 = 0x8b7940, +8 = 0x4a7e60), stored in `[S+0x56c]`.
- **CONFIRMED:** 0x800630 â†’ 0x5faeb0 copies the destination to `[task+0x14..0x1c]`, the radius to `+0x20` and the flag to byte `+0x24`. It then calls 0x76f850 on `[S+0x6a0]`.
- **Now read, was UNREAD:** 0x76f850 calls 0x7490e0 and, if that is true, clears bit 1 (mask 0xfffffffd) of the flags dword at `[obj+8]`. It is not a movement start.
- **CONFIRMED:** init 0x8b7940 calls 0x449cf0 on `[S+0x64c]` with arg 2, then 0x510730 and sets `[S+0x98] = 2`. 0x510730 calls vt+0xb8, sets `[S+0x4e8] = 0`, calls 0x46ce40 on `[S+0x4a4]` and then 0x5a8dd0.
- **Consequence the report missed:** init forces `[S+0x4e8] = 0`, so the immediate-end gate 0x7cad60 passes at task start. It fails only if `[S+0x4e8]` is rewritten, or the `[[S+0x40]+0x50c]` vcall +0x7c is nonzero.

**(4) Aborts and stalls**
- **CONFIRMED:**
  - 0x6d9eb0 is true only if `[S+0x700] == 0` and (`[[S+0x6d8]] == 6` or byte `[[S+0x40]+0x5c8] == 0`).
  - 0x7cad60 is true only if `[S+0x4e8] == 0` and the body vcall returns 0.
  - The arrival test is 0x60b160 against 300.0 (`jp` is taken when d >= 300, which goes to the far branch 0x4a812c).
  - The "Stuck in ZRunToPosShootingTask. Leaving." message is at 0x4a80ab.
  - 0x8602bc sets `[S+0x4fc] = 1` when 0x60b160 returns less than the double at 0xb3c350. I did not read that constant; the report says 400.
- **UNVERIFIED:** the list of `[S+0x4e8]` writers. My scan found the same addresses, but several hits (0x4aaf00, 0x6bee50, 0x861720, 0x90a660) use byte-sized access and may belong to other classes.
- **PLAUSIBLE:** "the only `[S+0x6fc]` readers are 0x7b1565, 0x7e576a, 0x807de8 and 0x85f89f". The other hits are dword/word accesses or `lea`, and probably belong to other classes. The writers 0x578d3b, 0x5a3a03, 0x7b3991 and the ctor 0x761b30 are consistent with CLAUDE.md.

**(4) "Cover branch is the likeliest cause of bs44": REFUTED (downgraded to unlikely)**
- **The detail is wrong.** 0x509f30 picks its point by distance against `[S+0x6a8]`, not a fixed 2200.
  - d > 2Â·`[S+0x6a8]`: the point is bot + dir Ã— 1000 (`0xb7df80`), with a 1100 cm search radius (`0xb2b9f0`).
  - `[S+0x6a8]` < d <= 2Â·`[S+0x6a8]`: the point is an interpolated one, with a different radius.
  - d <= `[S+0x6a8]`: it uses a third branch (radius at `0xb206d0`).
  - The result is passed to 0x875be0 as the cover query. The "d >= 2200" figure only holds if `[S+0x6a8]` = 1100, which the gates doc gives.
- **The cover branch still moves the bot toward the human.** Each hop is about 10 m toward it, so it cannot make the distance grow.
- **It affects too few ticks to matter.** It only runs on the 2 and 7 ticks where eval returned 1.0, out of 689 and 382 calls. It cannot explain 50 m growing to 110-140 m.
- **A better explanation (GUESS):** over 99% of the time some other tactic or goal drives the bot. Eval also stops being called while Defend sits in the child via 0x55b9f0. That is why bs43 showed no evals after 178.6 s.

**(4) "All the call sites below are unhashed": REFUTED**
- **Hashed:** 0x543f20, 0x72bc70, 0x4a8018 (inside the run task), 0x510730, 0x5caf90, 0x7b0b70, 0x6d9eb0, 0x7cad60, 0x85f6c0 and the Defend loop at 0x85f8f0, 0x875be0, 0x54abe0 and 0x6ab290.
- **Unhashed (detours allowed):** 0x6724e0 and its whole body, 0x76e8c0, 0x800630, 0x5faeb0, 0x4a7e60 (entry only) and 0x509f30.
- **Online, SessionSafe:** the report's "count calls to 0x510730 and 0x7b0b70" cannot be done with detours. Use data reads or calls only.

**(5) The `[S+0x108] = 0` lever: PLAUSIBLE but low value, and a data write is hashed-safe**
- **Default value UNVERIFIED:** the default of 1 comes from base ctor 0x7cfac0 (`mov byte [esi+0x108],1` at 0x7cfb1c). That ctor also writes `[S+0x4e8]`, so it is probably S's base class, but I did not prove that S derives from it.
- **Dog write:** 0x6ab290 writes the byte only when style == 6, so the dog is genuinely 0.
- **Restamping risk:** the stock SquadModifier path 0x54abe0 ("SetUseCovers") rewrites `[member+0x108]`. Squad modifiers can re-stamp it, so a one-shot data write may be overwritten.
- **Side effects:** 0x543f20 also gates AttackFromCover, per `bots_dynamic.md`, so the write removes cover use for that bot everywhere.
- **Benefit:** it only changes which branch runs after a win. It does not address the rarity of wins.

## Corrections
1. The cover branch is not the likeliest cause. The bottleneck is the rarity and cadence of eval returning 1.0, plus whatever else runs the other 99% of the time.
2. Only 0x6724e0 (including the success tail at 0x672763), 0x76e8c0, 0x800630, 0x5faeb0, 0x4a7e60 and 0x509f30 can be detoured online. Everything else must be sampled as data.
3. Branch detection can use `[S+0x64c]` after the run body, or count entries at 0x76e8ed versus 0x76e935. Both are inside 0x76e8c0, which is unhashed.

## Endorsed next step
- **Lever:** do not write `[S+0x108]` yet. Ship the per-gate ZCloseIn trace (P1..P9) that w21syogv3 already builds. All of its jcc sites are in the unhashed 0x6724e0 body.
- **Probe:** run it with the DefendProbe winner sampling. Add three cheap, unhashed read-only items:
  1. A count of 0x76e8c0 entries, plus the branch taken (entry at 0x76e8ed or 0x76e935).
  2. At each 1.0 return (0x672763), log the bot-to-human distance and `[S+0x98]` and `[S+0x4e8]`. Then log the same distance at +5 s and +15 s, to show whether a win actually moves the bot.
  3. A sampled flag for whether Defend is inside the child (`[goal+0x14]` nonzero) and which tactic it is.
- **Decision rule:** if the gate trace shows one gate (P5, P6 or P7 are the most likely) failing after the P1 window, target that gate's data. If the trace shows wins are fine but the bot is displaced by other tactics, target list A ordering rather than the cover flag.

Key files read: `C:\kl-merge\kl-merge\re\closein_gates_1104.md`, `C:\kl-merge\kl-merge\re\bots_dynamic.md`, `C:\kl-merge\kl-merge\klhook\klranges.h`.
