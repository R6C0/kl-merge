# Attack goal stays at state 0 (static research, 2026-11-04)

Static only, kl2.exe (base 0x400000). Labels: H verified in disassembly, M inferred, L guess.
Hashed status checked against klhook/klranges.h only coarsely (see Q6; re-check before coding).

## Q1 prio 0x96 goals
AddGoal 0x6cabf0(goal, prio) callers with prio 0x96 (H):
- 0x4699f8 `[S+0x65c]` ZStayInCover, in 0x4699a0
- 0x760f53 `[S+0x648]` ZDefendPosition, in 0x760e50 (vt slot 79)
- 0x831986 `[S+0x658]` ZAttackTarget, in 0x831850 (vt slot 83)
- 0x4be809 `[S+0x63c]` ZFollow, prio 0x96 or 0x2ee, in 0x4be760 (vt slot 80)
`[S+0x74]` at prio 0x96 is therefore Defend, StayInCover or Follow (M: Defend most likely, the ZSoldier default stance).
Each of the four calls vt+0x1b4 (0x6e49b0) first, which removes EVERY prio-0x96 entry (offsets 0x63c 0x640 0x648 0x638 0x660 0x650 0x654 0x658 0x65c 0x644 0x664).

## Q2 who sets [S+0x658], why state 0
The ctor allocates it (H), so it is always non-null. It only becomes a goal via slot 83 (0x831850) with a nonzero handle. Goal state 0 means "queued, never made current".
Arbiter 0x81eb90 (H): max prio wins, first list entry wins ties; same prio calls winner->vt+0x28 (class-name compare 0x57e770), same class keeps the current goal. Because any later Defend/StayInCover/Follow add wipes all other 0x96 entries (Q1), a queued ZAttackTarget is deleted from the scheduler list while the object stays allocated: state stays 0. Slot 83 was never hit in bs40, so it was never queued at all; the 25 hits of 0x800650 only arm the run task.

## Q3 ZRunToPosShootingTask
- 0x5fb040 (the 0x5fb4f3 physics vt+0x264 call) is a position-clamp raycast that overwrites a position on a hit. It is not a fire-time LOS gate (H).
- 0x5faeb0 (ecx=task, args pos*, float, byte) just stores `[task+0x14..0x1c]` position, `+0x20` float, `+0x24` byte, then calls 0x76f850 on `[[task+4]+0x6a0]` (H).
- Tick 0x4a7e60: path following, "Stuck in ZRunToPosShootingTask. Leaving."; when `[task+0x24]` set and holder nonzero it calls body vt+0x6e4(holder, 2, float) at 0x4a86b7..0x4a86d8. No LOS test (H). It moves the bot to the stored position; it does not search for one.
- The firing-position search for a target with no line is in ZAttackTarget mode B (0x4f4460/0x4f4b5f..0x4f4bed, only via slot 83 with goal states 0/4, per w4funhvyl). Arcade for an unseen target: that path or tactics (Q4); no separate approach code was found elsewhere (M).

## Q4 ZSoldierAttack (+0x638)
Constructed, but no AddGoal activates it in the whole exe (H: none of the prio AddGoal sites uses 0x638; 0x863990 has no callers or dispatches). Its tick 0x6c8350 only runs tactic children. So the task premise (Arcade runs +0x638) is false. The real Arcade fire path is the tactics list run by a looping goal (Defend 0x85f6c0, Idle 0x77bbd0, AttackTarget): first tactic whose vt+0x2c eval exceeds `[0xb69b98]` runs as RunChild 0x521350.
Key tactic: ZAttackNoCoverTactic (+0x5b0) eval 0x85ece0 returns 1.0 only if ALL: (`[S+0x4fc]!=0` or `[S+0x88]!=1`), clock >= `[[S+0x40]+0x698]+0x800`, 0x6d9eb0() true, holder `[S+0xb0]!=0`, holder flags `[S+0xa8]`: bit0 set, bit2 clear, 0x200 clear, 0x10 set, 0x40 clear (H).

## Q5 [S+0x88]
Soldier mode: Arcade 2, online bot 1, Follow 3. Setter is vt+0x4c = 0x588000 (calls 0x4880c0, `mov [ecx+0x88],eax`). Known callers: 0x4be79d (ZFollow, push 3), 0x82cb3c (vt+0x4c(2) inside 0x82cae0, which then re-adds Idle prio 0x64 and calls vt+0x50 re-arbitrate) (H). I did NOT find the online path that writes 1 (L: probably the net-bot spawn setup). Reader that matters: 0x85ece0 above (mode != 1 satisfies the first clause). Lever: a plain data write `[S+0x88]=2` is cheap but its other readers (0x7088c0 at 0x708912 etc.) were not fully enumerated: side effects UNVERIFIED (M-L). Prefer the 0x4fc write below, which 0x85ece0 accepts alone.

## Q6 smallest default-off lever
Premise: our LosGate correctly blocks shots; the bot must APPROACH. Two options, both data/unhashed:
A (fire clause, does not approach): per tick for the marked bot write `[S+0x4fc]=1` and keep holder flags `[S+0xa8]` in the 0x85ece0 mask. Only helps once a line exists; ZAttackNoCover has no LOS test of its own, so with LosGate it just keeps shooting only when clear. Low value alone (M).
B (approach, preferred): call slot 83 `0x831850` (vt+0x14c, ecx=S, unhashed gap 0x831000-0x832000) with a NONZERO holder handle AND then prevent the Defend/Follow re-add from wiping it (the 0x6e49b0 wipe is hashed, so do NOT detour it; instead only call slot 83 from our tick after any Defend add, i.e. re-queue every ~250 ms). Goal then runs ZAttackTarget whose mode B search 0x4f4460 chooses a firing position (the stock approach). bs24/bs25 AttackHandle probe already got the goal to state 4 within 0.6 s, so the call is known safe (H from prior notes); the open issue is that it ends at state 4 quickly when the line is blocked.
C (position): arm 0x800630 (vt slot 29, unhashed gap 0x800000-0x801000) / 0x800650 to run the shared task toward a spot near the human, args per 0x5faeb0 (pos*, float, byte); legality outside a RunChild UNVERIFIED (L).
Hashed (detour refused under SessionSafe=1, data ok): 0x760e50, 0x4be760, 0x6e49b0, 0x81eb90, 0x588000, 0x85ece0, 0x4f4460, 0x4a7e60 (all M: confirm each in klranges.h before coding). Unhashed (M): 0x831850, 0x800630, 0x800650, 0x6cabf0.
Recommendation: try B behind a new default-off flag, re-queueing slot 83 with the human handle every 250 ms while LosProbe says blocked; log `[S+0x658]+8` and `[S+0x74]` to confirm state reaches 2.

## Verifier (2026-11-04, static: debug/dasm.py + klhook/klranges.h range test + re/traitor_fire_1103.md; no game run)
Per-claim verdicts (CONFIRMED = read in the disassembly; REFUTED; UNVERIFIED = kept at M/L):
- Q1 four prio-0x96 AddGoal sites 0x4699f8, 0x760f53, 0x831986, 0x4be809: CONFIRMED by scanning every call to 0x6cabf0 (0x4be809 pushes `0x96 + x`, the 0x2ee variant; the other 3 push a literal 0x96). No other literal-0x96 caller exists. Other prios near it: 0x78 (0x4c7491, 0x518e11, 0x775054, 0x841151), 0xa0 (CoverFire via 0x637800).
- Q1 "[S+0x74] at 0x96 is Defend": stays M/UNVERIFIED (Defend, StayInCover or Follow all fit; nothing in the data separates them). Probe [S+0x74] against [S+0x648]/[S+0x65c]/[S+0x63c] to settle it.
- Q1/Q2 wipe: CONFIRMED. 0x6e49b0 copies the 11 goal pointers ([S+0x63c,0x640,0x648,0x638,0x660,0x650,0x654,0x658,0x65c,0x644,0x664]) and calls 0x8883d0(goal, 0x96) on each; 0x8883d0 is an erase from the sorted list at [S+0x48..0x4c] (find 0x4d87b0, shift 0x4d0b20, new end stored) and AddGoal 0x6cabf0 is the matching insert (0x48da70) when not found. All four sites call vt+0x1b4 first (StayInCover 0x4699e0, Follow 0x4be7c6, Defend 0x760f3b, Attack 0x83197a).
  Correction: Defend (0x760e50) and Follow (0x4be760) only reach the wipe+add when their OWN goal state is 0 or 4 (else they call 0x7bbf70 and return, 0x760f2b / 0x4be7ba). So a Defend re-add wipes ZAttackTarget only after Defend finished or was never started; "any later add wipes it" is too strong. Who calls slot 79 and how often is UNTRACED.
- Q2 "state 0 = queued, never current; later Defend add deleted it": M. The mechanism exists, but bs40 never saw slot 83 (the [S+0x658] target was set earlier). The arbiter tie claim (first list entry wins at equal prio) was not re-read here. Also note [S+0x658] non-null says nothing: the ctor allocates it, so "SET" is trivial; the meaningful datum is the target handle [g+0x14] (DM03 802d5b24, DD05 0), written only by 0x68fd70 at 0x8318ef, i.e. slot 83 had run with a nonzero handle at some earlier point (our AttackHandle/other Brain code, since stock never does).
- Q3 0x5fb040 / 0x5fb4f3 is a clamp, not a fire LOS test: not re-read (UNVERIFIED, kept M). 0x5faeb0: CONFIRMED (stores pos to [task+0x14..0x1c], float +0x20, byte +0x24, then path request 0x76f850 on [[task+4]+0x6a0]). Correction: 0x800650 is NOT a function; it is the return site after `call 0x5faeb0` inside 0x800630 (vt slot 29, thiscall, args pos*, float, byte, ret 0xc; 0x800630 is stored at 0xbd09c8 = vtable 0xbd0954 + 29*4, ZSoldier). Anything that must CALL the arm must call 0x800630, not 0x800650 (0x800650 stays a fine observation/detour point).
- Q4 0x85ece0 condition list: CONFIRMED exactly as written (+0x4fc!=0 or +0x88!=1; clock >= [[S+0x40]+0x698]+0x800; 0x6d9eb0(); [S+0xb0]!=0; flags [S+0xa8] bit0 set, bit4(0x4) clear, 0x200 clear, 0x10 set, 0x40 clear). The class name ZAttackNoCoverTactic / slot +0x5b0 is M (not re-derived).
- Q4 "ZSoldierAttack never activated, so the task premise is false": UNVERIFIED, downgrade to M. Ctor store 0x6ab719 and wipe read 0x6e49ce are confirmed, and 0x863990 (`mov eax,[ecx+0x638]`) has no direct caller, BUT it sits in a vtable (0xbb4288), so a virtual getter exists and "no direct call" does not prove "never queued". wc555a9o3 in traitor_fire_1103.md itself says "Where ZSoldierAttack is activated: untraced". Treat Arcade's use of it as open, not refuted.
- Q5 setter: CONFIRMED. vt+0x4c = 0x588000 (vtable slot at 0xbd09a0); it only does extra work when the OLD mode is 3 (Follow cleanup), then 0x4880c0 stores [S+0x88]. Callers 0x4be79d (push 3) and 0x82cb3c (push 2, in 0x82cae0, an unhashed function that re-adds Idle at 0x64 and re-arbitrates) CONFIRMED. Online writer of 1: still not found. A plain data write [S+0x88]=2 skips the setter's Follow cleanup only when the old value is 3, so for old 1 it is equivalent to the setter; other readers still unenumerated (0x7088c0 needs ==2).
- NEW against Option A: slot 83 clears [S+0x4fc] to 0 at entry (0x831865), as do ZFollow (0x4be784) and StayInCover (0x4699a9). A 0x4fc=1 write is lost on the next such call; ZAttackTarget mode B's no-clear tail (0x4f4bc3) is what sets it in stock. Write it AFTER any slot-83/Follow call or each tick.
- Q6 Option B: NOT NEW and not endorsed. Slot 83 with a nonzero handle is exactly the shipped OnlineBrainTraitorAttackHandle (+ Restart, EntryFix, HoldFire in klbrain.c, bs24..bs27); bs24 DD05 showed the goal current then state 4 within 0.6 s. Stock never calls slot 83 with a nonzero handle (all 5 callers pass 0), so ZAttackTarget/mode B is not the Arcade path (wc555a9o3) and w4funhvyl's verifier already said "do not build an Approach lever yet; it repeats AttackHandle". Slot 83 with nonzero handle also does nothing when [[S+0x5ac]+8] is not 0/4 (only stores [S+0x720], 0x831896). And CoverFire (0xa0) outranks ZAttackTarget (0x96), so a live CoverFire goal masks it. Mode B itself is hashed and cannot be hooked (only observed through the 2 unhashed sites).
- Hash status (klranges.h range test, run now; all addresses checked, not coarse): UNHASHED: 0x831850, 0x800630, 0x800650, 0x6cabf0, 0x5faeb0, 0x5fb040, 0x82cae0, and 0x4a7e60. HASHED (detour refused under SessionSafe=1): 0x760e50, 0x4be760, 0x6e49b0, 0x81eb90, 0x588000, 0x85ece0, 0x4f4460, 0x4f4b5f, 0x6c8350, 0x7088c0, 0x6d9eb0, 0x4699a0. CORRECTION: the report lists 0x4a7e60 (ZRunToPosShootingTask tick) as hashed; it is NOT (gap 0x4a6000-0x4a8000). That makes a tick-level hook on the run task possible online.
- Q6 Option C (arm the shared run task toward a spot near the human via 0x800630(pos*, float, byte)): the only lever here that is not a repeat. Mechanically plausible (0x5faeb0 just stores the point and requests a path) but UNVERIFIED: the task only ticks while a parent goal runs it as a child (RunChild), pos should be a reachable nav point (a point at the human is possibly off-mesh), and the flag byte +0x24 should be checked against what the stock 25/13 arms pass. Needs a read-only look at those args first (a probe on the existing 0x800650 site: log pos, float, byte, and distance to the human).

### Corrected claim list
1. Four prio-0x96 AddGoal sites; each wipes all 0x96 entries first. (H, verified)
2. The wipe only fires when the adding goal's own state is 0 or 4 for Defend/Follow/Attack. (H, new)
3. [S+0x658] is always allocated; "set" is meaningless, the target handle [g+0x14] is the signal. (H)
4. 0x85ece0 fire clause list. (H)
5. [S+0x4fc] is zeroed by slot 83, Follow and StayInCover entry; Option A must rewrite it each tick. (H, new)
6. 0x800630 is the arm function; 0x800650 is a return site. (H, correction)
7. 0x4a7e60 is unhashed. (H, correction)
8. ZSoldierAttack activation is untraced, not refuted. (M, correction)
9. Online writer of [S+0x88]==1 not found. (open)

### Lever recommendation
Endorse NONE as a behaviour change yet. Option B repeats AttackHandle (already shipped, ends at state 4 with a blocked line); Option A cannot make the bot approach and its byte is cleared by slot 83. Next step is read-only: extend the 0x800650 site probe to log the arm args and the distance/line to the human, and add a sampler of [S+0x74] against the three candidate 0x96 goals (+0x648, +0x65c, +0x63c) to learn which goal holds the bot. Only if the arm args turn out to be plain nav points near the bot's cover, try Option C behind a default-off flag: call 0x800630 (unhashed) with a nav point toward the human, only while LosGate says blocked and the shared task is idle (state 0/4). The tick 0x4a7e60 being unhashed also allows an observe or position-override there if needed.
