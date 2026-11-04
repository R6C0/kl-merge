# Approach lever for the marked traitor bot (static research, 2026-11-04)

Read-only static work on kl2.exe (base 0x400000) via debug/dasm.py. Nothing was run. Labels: H = read straight
from disassembly, M = inferred from several call sites, L = guess or untraced.

## Hashed status (klhook/klranges.h, checked by a range test)
Hashed (do not detour; calling and data writes are fine): 0x5ccea0 SetApproachTarget, 0x552b00, 0x5c4360, 0x6c8350
ZSoldierAttack tick, 0x521350 RunChild, 0x6e49b0, 0x81eb90, 0x85ece0, 0x4f4460.
Unhashed (detour allowed): 0x6724e0 ZCloseInTactic eval/run, 0x76e8c0, 0x55b9f0 done check, 0x800630 (slot 29 arm),
0x800650, 0x5faeb0, 0x4a7e60 (task tick), 0x76f850, 0x831850 (slot 83), 0x6cabf0 AddGoal.

## Q1 Option C: slot 29 = 0x800630 (H)
- Signature: thiscall, ecx = S, `ret 0xc`: `arm(pos*, float, byte)`. It forwards to 0x5faeb0 on the run task `[S+0x56c]`.
- 0x5faeb0 stores pos into `[task+0x14..0x1c]`, the float into `+0x20`, the byte into `+0x24`, then calls 0x76f850 on
  `[[task+4]+0x6a0]` (the movement/path object).
- Stock callers pass float 0.0 nearly always; byte 1 = shoot the holder while moving (M).
- The task never ticks itself: every stock caller RunChilds it from a parent goal or tactic (H, all callers inspected).
  Arming it alone from our tick moves nothing. Cancelled when the parent finishes or is replaced (M).
  The online bot re-arms 25/13 times per round (ModeBProbe), so something does run it, with a destination we do not control.

## Q2 Tactic lists (M)
- List A `[S+0x604..0x608]` is walked by ZSoldierAttack tick 0x6c8350: for each tactic, call vt+0x2c (eval), compare the
  float with a threshold (0xb69b98), and if passed RunChild it. ZCloseInTactic (0x6724e0) is the approach tactic: it paths to
  the holder `[S+0xac]`/`[S+0xb0]`, gated by `[S+0x6a8]` preferred distance, distance check 0x4087f0, timer `[S+0x590]+0x14`.
- List B `[S+0x610]` (ZCloseInOnTarget, fed by `[S+0x720]` approach target + `[S+0x724]` timestamp) has readers at 0x502924
  and 0x404308/0x44cc3d; who iterates it for an FA heister is NOT traced (L).
- Defend `[S+0x648]` does not use the lists (M). ZSoldierAttack `[S+0x638]` activation (who makes it current, prio vs 0x96) is
  NOT traced (L); 0x415337..0x415349 is a destructor-style sweep of S members, not an activator (H).

## Q3 Pursuit of an unseen target (M/L)
Only two approach paths found: ZCloseIn (needs list A running via ZSoldierAttack) and ZAttackTarget mode B (slot 83 with a
handle, known to end at state 4 in 0.6 s). Hunt/Suspicious/Flanking goals were not examined (L). Neither found path is a pure data write.

## Q4 Recommendation (default off, L confidence that it works; probe first)
Lever "ZSoldierAttack-first": make `[S+0x638]` the current goal for the marked bot so list A runs and ZCloseIn approaches
the holder; keep our LosGate so firing stays stock once the line clears. Use calls/data only:
1. Ensure holder is the target: `[S+0xa8]` flags set, `[S+0xac]`/`[S+0xb0]` = human (klbrain already writes these), `[S+0x88]`=1 as now.
2. Queue it once with unhashed AddGoal 0x6cabf0 (thiscall ecx = S's goal list owner, args goal=`[S+0x638]`, prio). The prio must beat
   or equal 0x96 and the 0x96 wipe 0x6e49b0 must not run; exact args need confirming from a stock caller (L).
3. Cancellation risk: Defend/StayInCover/Follow AddGoal at 0x96 wipe the 0x96 queue (4 sites), so re-check every 250 ms and re-add.
Cheaper secondary lever: write `[S+0x720]`=human entity, `[S+0x724]`=clock directly (data write, no call into hashed code) so
a ZCloseInOnTarget can fire if list B is iterated; effect unknown until the probe shows who reads list B.

## Read-only probe to run first (extends ModeBProbe sampler)
Every 250 ms for the marked bot log: `[S+0x74]` vtable vs `[S+0x638]/[S+0x648]/[S+0x65c]/[S+0x63c]` (is `[S+0x638]` ever current),
`[S+0x56c]` task fields `+0x14..0x24` (destination, byte), `[S+0x590]+0x14` timer, `[S+0x6a8]`, `[S+0x720]/[S+0x724]`, the
queue contents at prio 0x96 and 0xa0, and breakpoint-free counters of calls to 0x6724e0 and 0x4a7e60 (unhashed, count-only detours).
Decide the lever only after it shows (a) whether ZSoldierAttack is ever current and (b) whether 0x6724e0 is ever evaluated.

## Verifier (2026-11-04, static: debug/dasm.py + klranges.h range test run on every address + vtable scan; no game run)
Labels: CONFIRMED = read in disassembly; REFUTED; UNVERIFIED = stays M/L.

Hash status: CONFIRMED by an exact range test. HASHED: 0x5ccea0, 0x552b00, 0x5c4360, 0x6c8350, 0x521350, 0x4087f0, 0x6e49b0, 0x4f4460.
UNHASHED: 0x6724e0, 0x76e8c0, 0x55b9f0, 0x800630, 0x800650, 0x5faeb0, 0x4a7e60, 0x76f850, 0x831850, 0x6cabf0. Report list correct.

Per claim:
- Q1 0x800630 signature: CONFIRMED (thiscall ecx=S, [ebp+8]=pos*, [ebp+0xc]=float, [ebp+0x10]=byte, loads `ecx=[S+0x56c]`, calls 0x5faeb0, `ret 0xc`).
  CORRECTION: 0x800650 is the return site after that call, not a function (a detour there is a mid-function patch; observe at 0x800630 instead).
  "Task never ticks itself / needs a RunChild parent": M (the 0x6c8350 and 0x85f6c0 ticks both RunChild 0x521350; callers of 0x800630 not re-enumerated).
- Q2 "0x6724e0 = approach tactic, eval/run": CONFIRMED with a CORRECTION. It is the EVAL (vt+0x2c, slot 11 of ZCloseInTactic vtable 0xbd0c64, ctor stores it at 0x6ab3b6 and the object into `[S+0x590]`).
  It returns 0.0 (fldz at 0x672722) or 1.0 (0x672770). It also writes the destination into `[this+0x18..0x20]` and calls 0x5caf90(S) on success. Gates, in order: `[this+0x14]` timer vs clock (0x672505); `[S+0xb0]!=0`; S vt+0x84 float vs `[[0x168d7c0]+0x108]`;
  dist(`[S+0xac]`) via 0x4087f0 must be GREATER than `[S+0x6a8]` (preferred distance); a random roll vs 1.0 or `[0xbcb330]`; 0x8a2e50 vs that; for non-"mode 6" `[[S+0x4]...+0x6d8]!=6`: 0x651060 / 0x76ca60 count; then a nav query (vt+0x60 of the object at `[[0xdd2640]+0xac]+0xc`) that must return a path of >1 nodes (0x672714). Any gate failing returns 0 silently.
  `[S+0x6a8]` and `[S+0xac]`/`[S+0xb0]` roles: CONFIRMED by use; the 0x590 timer is `[this+0x14]` where this=`[S+0x590]`.
- Q2 "list A walked by 0x6c8350": CONFIRMED (loop 0x6c83e3..0x6c8428: eval vt+0x2c, `fcomp [0xb69b98]`, RunChild 0x521350, done-check 0x55b9f0).
- NEW, corrects "who iterates the lists is untraced": the Defend tick (0x85f6c0, loop 0x85f8e2..0x85f93c, same eval/threshold/RunChild) picks its list at 0x85f896..0x85f8bc: list A `[S+0x604]` ONLY IF `[S+0x4fc]!=0` AND `[S+0x6fc]==0`; otherwise list B `[S+0x610]`; list C `[S+0x61c]` when `[[S+0x40]+0x5c8]!=0` and 0x575100 is false.
  The ctor (0x6ab3b8..0x6abe7b) puts ZCloseIn (`[S+0x590]`) into list A only (the only `+0x590` read in the list-building code is in the A block; B/C builds do not use it). So ZCloseIn is evaluated under Defend only while `[S+0x4fc]!=0`. Stock sets 0x4fc at 0x6c83b1 (end of ZSoldierAttack's child) and in ZAttackTarget's no-clear tail; slot 83, Follow and StayInCover zero it.
  Consequence: the prior "Option A cannot approach" is REFUTED in part. Writing `[S+0x4fc]=1` makes a running Defend iterate list A, which includes ZCloseIn, whose eval is exactly the approach-on-holder. (UNVERIFIED: that Defend is the current goal, what `[S+0x6fc]` is, list order inside A, and whether a passing ZAttackNoCover (0x85ece0, no LOS test) earlier in A would just shoot through geometry again; hence it must stay behind LosGate and the holder `[S+0xb0]` must be cleared/not set while blocked.)
- Q3 "no other approach path": UNVERIFIED (only two paths looked at, as stated).
- Q4 lever "ZSoldierAttack-first via AddGoal 0x6cabf0": NOT endorsed.
  AddGoal signature CONFIRMED: thiscall ecx=S, `(goal, prio)`, `ret 8`, insert into the sorted list `[S+0x48]` via 0x4d87b0/0x48da70. BUT it silently returns without inserting when `[0x168e598]` passes 0x863a60 and 0x4b0a40 and the goal's vt+0x24 returns false (0x6cac00..0x6cac26): an unmodelled gate. ZSoldierAttack is still UNTRACED as an activated goal (no stock prio site found, a prior verifier note), so queueing it is an untested state machine online: crash/assert risk, and its prio vs 0x96 is unknown. "Four 0x96 sites wipe the queue" CONFIRMED earlier, but Defend/Follow only wipe when their own state is 0 or 4.
  "Cheaper secondary: write [S+0x720]/[S+0x724]": CORRECTED, list B is iterated by Defend whenever 0x4fc==0, so it is read, but whether a ZCloseInOnTarget sits in B and what it needs is UNVERIFIED. Drop it in favour of the 0x4fc lever.

### Lever I endorse (default off, untested; L until the probe runs)
"Combat-flag lever": per 250 ms for the marked bot, only while LosGate says every human is blocked, write byte `[S+0x4fc]=1`, and only if `[S+0x6fc]==0`. No call, no detour, data write only (same family as the existing 0x4fc write idea). Preconditions:
 1. The probe shows `[S+0x74]` is a Defend (vtable of ZDefend goal) at least some of the time, and `[S+0x6fc]==0`.
 2. List A really contains ZCloseIn: log `[S+0x604..0x608]` entries' RTTI (E.rtti(vtable)) in order.
 3. Re-write after any slot-83/Follow/StayInCover event (they zero it); never set it when a human is visible (LosGate clear) so stock firing logic is unchanged.
 4. Holder `[S+0xb0]` must be non-null for ZCloseIn to pass (gate 2); klbrain currently clears/skips it for blocked humans (LosGate/HolderFix skip), so this lever needs the holder kept set to the human while blocked, but ZAttackNoCover (0x85ece0) would then fire through walls. Resolve by logging first which of ZCloseIn / ZAttackNoCover is earlier in A; if NoCover precedes ZCloseIn, do NOT enable (bs38 reproduces).
 Without precondition 4 settled the honest status is: no lever endorsed for behaviour; endorse the probe only.

### Probe additions (read-only; supersede the researcher's list)
Every 250 ms: `[S+0x74]` RTTI; RTTI of every entry of lists A `[S+0x604..0x608]`, B `[S+0x610..0x614]`, C `[S+0x61c..0x620]` (once, then on change); bytes `[S+0x4fc]`, `[S+0x6fc]`; `[S+0x590]` object's `+0x14` timer and `+0x18..0x20` destination; `[S+0x6a8]`, `[S+0xac]`, `[S+0xb0]`; dist to the human.
Count and log the return of the unhashed eval 0x6724e0: it returns a float in st0 and its prologue is a standard `push ebp`, so use a naked wrapper that calls the original and `fst`s/preserves st0 (a plain C detour would corrupt the x87 return). Count-only detour on 0x4a7e60 is fine. 0x800630 observation: log args at 0x800630 (not 0x800650).
Decisive outcomes: (a) eval returns 0 while 4fc==0 or Defend not current: list A not iterated, the 4fc lever is the test; (b) eval returns 0 with 4fc==1: a gate fails (log which with the extra reads above: dist vs 0x6a8, holder null, timer); (c) never called: not in A or Defend not current.
