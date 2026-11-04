# ZAttackFromCover (AFC) static analysis, kl2.exe (2026-11-04)

Static only (disassembly of kl2.exe, base 0x400000). Nothing run. "HASHED" = inside a range of klhook/klranges.h (calls are fine, no detours online). GUESS / UNREAD marked.

## Identity
- ZAttackFromCoverTactic vtable 0xbd02bc: run body (slot 2) 0x4fee00 (free), eval (vt+0x2c) 0x680b20 (HASHED), slot 12 0x640910. Object in [S+0x59c], ctor 0x5a13a0 (size 0x18), created at 0x6ab41e only when soldier style [[S+0x6d8]] is not 5 or 6.

## Q1. Eval gates (0x680b20, all HASHED; first failing gate returns fldz 0.0)
1. 680b28 `mov edx,[eax+0x7c]` / 680b2b `call edx` -> S vt+0x7c = 0x543f20: `cmp byte [ecx+0x108],0; je ret0; call 0x72bc70(S); test al,al; jne ret0; mov eax,1`. [S+0x108] = "use covers" byte (0 only for the dog, set at 0x6ab290). 0x72bc70 (HASHED) is a level-wide cover-ban window ([lvl+0x1640], timestamp [lvl+0x1644]); true only if now <= ts window, [S+0xb0]!=0 and [S+0xac]==[lvl+0x1640]; false in practice. Fail -> 680b2f `je 0x680b60`.
2. 680b34 `cmp dword [eax+0xb0],0` / `je`: holder [S+0xb0] must be nonzero.
3. 680b3d `mov eax,[eax+0x40]` / 680b40 `cmp byte [eax+0x5c8],0` / `jne`: body byte 0x5c8 must be 0 (0x6d9eb0 tests it too).
4. 680b4b `call 0x807c60` (cover search, HASHED), then 680b53 `cmp dword [ecx+0xec],0` / `je`: cover state [S+0xec] must be nonzero. Pass -> 680b5c `fld1` (1.0).
- There is NO LOS and NO holder-flags test in the eval. Gate 4 is the only one that does real work.

### 0x807c60 cover search (HASHED)
- Holding a cover ([S+0xec]!=0): validates via 0x491eb0, 0x62c9d0, 0x4f6070 (hysteresis around [S+0x72c]), then 0x80f8d0 (HASHED): "target not in view" = true (release: 0x772600, 0x4febc0, re-search); in-view flags (1/0x10 set, 4/0x200/0x40 clear) = false (keep, eval 1.0).
- No cover (807ddc): al = ([S+0x4fc]!=0 && [S+0x6fc]!=0). 807e07 `cmp [ecx+0xb0],0 / je 807e84`; 807e11 `cmp [ecx+0x88],0 / je 807e1e`; 807e1a `test al,al / je 807e84`.
  - TARGET path 807e1e: holder exists and (mode [S+0x88]==0 or both flags set). Calls S vt+0x18c = 0x509f30 (UNHASHED) idx -1; fails if result <= 0 (807e31 `test eax,eax; jle 808033`).
  - POINT path 807e84: no holder, or mode!=0 and not both flags.
- Point path: modes 1 and 3 (online uses 1): point P = defend block [S+0x64c] xyz (built by 0x40b540: +0..8 pos, +0x18 scale default 1.0). Other modes (Arcade = 2): P = the bot's own position (0x7b3020 on [[S+0x40]+4]). Radius = tuning[0x168d7c0+0x358] x block+0x18 (+0x35c if [S+0x4fc]!=0, +0x360 if 0, when [[[S+0x40]+0x54]+4]==0; 807f2e..807f65). Mode 3 clamped by [S+0x6dc]*tune[0x134]. Override 807ed7..807f2a: if [[[S+0x40]+0x54]+4]!=0 and bot-to-place distance > scale*1000.0 (0xb5afc0) the search point becomes the bot (GUESS: compare order; the field is UNREAD). Then S vt+0x190 = 0x7f71e0 (HASHED) with (pt, radius, 1, -1); -1 = fail (807ff8 `jl 808033`), 0 accepted. Same-cover hysteresis 807fbe..807ff1 (same id within window fails). Accept 807ffa: stores id, stamps [[[S+0x40]+0x54]+0x34]=now, calls 0x656740 (HASHED, sets [C+8]) and 0x6eda00 on [S+0x738].
- 0x509f30 and 0x7f71e0 both build a query with 0x7daf20 (HASHED): target pos [S+0x720] else [S+0xac], byte +0x98 = [S+0x4fc]; scores via 0x6ece90 -> 0x875be0 (HASHED; criteria UNREAD).

### 0x509f30 (UNHASHED) geometry
d = |target - self|, s = [S+0x6a8] (1100 per gates doc). d >= 2s: P = self + dir*1000 (0xb7df80), radius 1100 (0xb2b9f0). s <= d < 2s: len = 500 + 500*(d-s)/s (0xb64e20 = 500.0), radius len+100 (0xb3dde8). d < s: P = self, radius 600 (0xb206d0). The 1400.0 (0xb21dc4) / 400.0 (0xb243f4) clause only if d > 1400. So a hop is at most about 20 m from the bot toward the target, never onto the holder. (Corrects earlier notes: the "d >= 2200" figure and "hops toward the human at 10 m".)

## Q2. What AFC does when it wins (run body 0x4fee00, UNHASHED, detour allowed)
- Returns at once if [S+0xec]==0.
- [S+0xec]==1 (walking to cover): 0x60d050 (-> 0x828c60 on [S+0x6a0]), RunChild 0x521350 on S vt+0x70 (0x477cf0 -> [S+0x498] move task), yield 0x55b9f0.
- Otherwise (in cover): 4fee57 `mov byte [eax+0x4fc],1` (AFC itself sets the arrived/combat flag), 0x86a130 body fix-up, RunChild of S vt+0x194 (0x46d330, HASHED, returns [S+0x680] = ZAttackFromCornerCover goal, vtable 0xbd032c, run 0x45fca0); yield; if still holding cover 0x6757f0. If a human (players table [0xdd265c]+0x828..0x898) is within 300 cm (0x4087f0 vs 0xb146e0): release cover 0x4febc0 and tail-jump 0x807c60 to re-search.
- Net: moves the bot to cover near itself, toward the target; it does not close in on the human.

## Q3. Fire path
- AFC's run never calls 0x616480 / 0x85ece0 itself. Its child run 0x45fca0 (HASHED): 45fe7b `cmp [ebx+0xec],4` / `jne` (4 = at firing position); 45fe84 `lea ecx,[ebx+0xa8]`; 45fe8a `call 0x616480`; `jne 0x45ff30`. Fire branch 0x45ff30 calls 0x749170(...,0x1b,3,0), sets [S+0x98]=1, RunChild S vt+0x19c.
- 0x616480 needs [S+0xa8] flags: bit0 set, bit2 (4) clear, 0x200 clear, bit4 (0x10) set, bit6 (0x40) clear.
- Consequence: with online LosGate flags 0x10 only (bit0 clear) AFC can win and hop to cover but cannot fire: no through-wall shots. Eval needs no LOS, fire does. 0x85ece0 (AttackNoCover) has its own separate flags gate.

## Q4. Why AFC rarely wins for the online traitor (prediction)
Evidence (bs45, DM03 marked bot): Board x531, DefendCover x117, NoCover x58, Loot x15, AFC x15, CloseIn x1, none 59. Arcade (mode 2): AFC x354 / x1134.
- With CombatFlag=0 the online bot walks list B with [S+0x6fc]=0, so al=0 and mode is 1: the search takes the POINT path anchored on the defend block [S+0x64c], radius tuning[0x358]*scale (values UNREAD, heap data). Arcade (mode 2) searches around the bot itself. Gates 1 and 3 are almost certainly fine.
- Most likely failing gate: 4 (cover search): [S+0xec] stays 0 because 0x7f71e0 returns -1 (no cover within radius of the defend place, or the same-cover hysteresis). Second suspect: gate 2 (the 59 "none" ticks; stock scan clears holder). Not verified without runtime data.
- Priority also matters: in list B, Board (slot 5) and ZCloseInOnTarget/CloseAttack precede AFC (slot 10); in list A (CombatFlag 3) AFC is after ZCloseIn and SwatCloseIn, and Board is before ZCloseIn.
- ZDefendCover eval 0x84dc90 (UNHASHED) FAILS when holder flags show a visible target (bits 1 and 0x10, none of 4/0x200/0x40); with online flags 0x10 only it passes, which fits the 117 DefendCover wins.

### Levers (all data writes or calls outside hashed ranges)
- L1 (preferred): write [S+0x88]=2 on the marked traitor. Gives the Arcade-identical self-centred point path and the 0x7088c0 / 0x85ece0 mode clause. Per re/attack_goal_1104.md writing it directly equals the setter when the old value is 1 (other readers not fully enumerated: GUESS). Fire still gated by 0x616480, LosGate holds. Needs a new ini toggle (name to choose; default off).
- L2: keep [S+0x64c] xyz on the bot's own position each tick. Side effects on DefendCover, leashing, puppeteer defend-block orders.
- L3: CombatFlag=3 plus OnlineBrainTraitorNoBoard=1 (commit 49677dd93): list A reachable past Board; AFC then takes the TARGET path (0x509f30 hop) after CloseIn and SwatCloseIn fail.
- L4 (rejected): pre-fill the cover record by calling 0x509f30 + 0x656740. Complex, risky.

## Q5. Tactic order
Fields: [S+0x604] list A, [S+0x610] list B, [S+0x61c] list C. Null entries skipped. Defend loop 0x85f8e2..0x85f93c. First eval > 0 wins (RunChild 0x521350).

List B (build 0x6abede; push addresses): dog ([[S+0x6d8]]==6) first pushes 0x600 (6abf67), 0x5fc (6abf7f) and dog-only entries. Non-dog:
1 0x5ec ZReactToHumanShield (6abfa9); 2 0x5dc ZFakeCloseCombat (6abfe0, eval 0x8ab2b0, created if [S+0x6e8]==0); 3 0x5cc unset, null (6ac017); 4 0x5f8 ZBecomeTraitor (6ac04e, eval 0x79b7c0, only if 0x7f6850 passes); 5 0x5f4 ZBoardEscapeVehicle (6ac085, eval 0x4faf60); 6 0x5ac ZAttackMountedWeapon (6ac0bc, eval 0x68ee30); 7 0x5bc null (6ac0f3, zeroed 0x6ab672); 8 0x5b8 ZCloseAttack (6ac12d, eval 0x49b070); 9 0x594 ZCloseInOnTarget (6ac15b, vtable 0xbd0d54, eval 0x552b00, reads [S+0x720]; allocated unconditionally); 10 0x59c ZAttackFromCover (6ac192, eval 0x680b20); 11 0x598 ZSwatCloseIn (6ac1c9, vtable 0xbd0ca4, eval 0x7e56d0); 12 0x5b0 ZAttackNoCover (6ac203, eval 0x85ece0); 13 0x5c0 ZGraceShot (6ac231, eval 0x41a5b0, free); 14 0x5a0 ZDefendCover (6ac268, eval 0x84dc90, free); 15 0x5f0 ZLoot (6ac29f, vtable 0xbd0d94, eval 0x451920).
A further list [S+0x628] follows from 6ac2dc (0x630, 0x5dc, 0x5f8, 0x5f4, 0x5b8, 0x59c, 0x5c0, 0x5b0, 0x5f0, 0x624); list C [S+0x61c] from 6ac51b.

List A (from 0x6abb6f): 0x600/0x5fc (dog), 0x5ec, 0x5dc, 0x5f8, 0x5f4 (Board), 0x5ac, 0x5bc, 0x5b8, 0x590 ZCloseIn (vtable 0xbd0c64, run 0x76e8c0, eval 0x6724e0, free), 0x598 SwatCloseIn, 0x59c AFC, 0x5c0, 0x5b0, 0x5f0. No 0x594 and no DefendCover in A. AFC comes after ZCloseIn and SwatCloseIn; Board before ZCloseIn.

## Hashed status (script over klranges.h)
HASHED: 0x680b20 0x543f20 0x807c60 0x80f8d0 0x72bc70 0x7f71e0 0x875be0 0x6ece90 0x7daf20 0x616480 0x85ece0 0x46d330 0x45fca0 0x749170 0x552b00 0x85f6c0 0x772600 0x656740 0x6eda00 0x62c9d0 0x491eb0 0x6757f0 0x4087f0 0x7b3020 0x6d9eb0 0x521350 0x5a13a0 0x4faf60 0x8ab2b0 0x68ee30 0x49b070 0x7e56d0 0x451920.
FREE (detour allowed): 0x509f30 0x4fee00 0x84dc90 0x4febc0 0x4f6070 0x60d050 0x86a130 0x7f6850 0x55b9f0 0x4fe6f0 0x41a5b0 0x6724e0 and the push sites 0x6ac15b 0x6ac192 0x6ac1c9.

## UNREAD / GUESS
- 0x875be0 cover criteria; tuning values at [0x168d7c0]+0x358/0x35c/0x360; meaning of [[[S+0x40]+0x54]+4] and the 807ed7 override compare order (GUESS); exact meaning of [S+0xec] values 1/2/4 beyond 1 = walking, 4 = firing position; whether 0x5cc / 0x5bc are ever non-null; the 0x7f6850 condition; ZCloseInOnTarget eval looked like 0 in the visible part only; Q4 is a prediction, not measured.

## Verifier (2026-11-04, adversarial static re-check; kl2.exe disassembled with debug/dasm.py, hashed status by script over klhook/klranges.h, constants read from the image)

Method: every cited address re-disassembled; float constants read from the image; hashed/free status recomputed for all cited addresses. No game run, nothing committed.

### Identity
- CONFIRMED: vtable 0xbd02bc slot 2 = 0x4fee00, slot 11 (vt+0x2c) = 0x680b20, slot 12 = 0x640910. Ctor 0x5a13a0 is called at 0x6ab415 (join 0x6ab41e).
- CONFIRMED: not created for style 5 or 6: 0x6ab271/0x6ab279 set [ebp-1]=0 for [[S+0x6d8]] == 5 or 6, tested at 0x6ab3ff. Extra: style 6 also sets [S+0x6a8]=200.0 (0xb18ba0) and [S+0x108]=0 (0x6ab27e..0x6ab290).
- ADDED: ZSwatCloseIn ([S+0x598]) is allocated ONLY for style 5 (0x6ab3cf); for normal soldiers it is null, so "AFC after ZCloseIn and SwatCloseIn" is really "right after ZCloseIn" in list A and "after ZCloseInOnTarget" in list B.
- CONFIRMED: 0x594 is allocated unconditionally (0x6abb10..0x6abb1f). 0x5cc is never written in 0x6ab250..0x6abb6f (null); 0x5bc is zeroed at 0x6ab672 (null).

### Q1 eval gates (0x680b20)
- CONFIRMED gates 1 to 4 exactly as listed (0x680b28..0x680b5c); no LOS and no holder-flags test. 0x543f20 and the 0x72bc70 description are right.
- Hashed status CONFIRMED (inside klranges.h): 0x680b20 0x543f20 0x807c60 0x80f8d0 0x72bc70 0x7f71e0 0x875be0 0x6ece90 0x7daf20 0x616480 0x85ece0 0x46d330 0x45fca0 0x749170 0x552b00 0x4faf60 0x8ab2b0 0x68ee30 0x49b070 0x7e56d0 0x451920 0x85f6c0 0x6ab41e (ctor site) 0x45ff30 0x640910. CONFIRMED free: 0x509f30 0x4fee00 0x84dc90 0x4febc0 0x4f6070 0x60d050 0x86a130 0x7f6850 0x55b9f0 0x4fe6f0 0x41a5b0 0x6724e0 0x76e8c0 and the push sites 0x6ac15b 0x6ac192 0x6ac1c9.

### 0x807c60 cover search
- CONFIRMED: path selection (0x807ddf..0x807e1c): TARGET path iff holder != 0 and ([S+0x88]==0 or [S+0x4fc] && [S+0x6fc]); else POINT path. Modes 1 and 3 anchor on [S+0x64c]; other modes (Arcade 2) on the bot (0x7b3020). Quirk not in the report: the TARGET path rejects result <= 0 (0x807e31 jle), so cover index 0 is rejected there; the POINT path rejects only < 0 (0x807ff8 jl).
- WRONG (direction of the 0x807ed7 override, which the report marked GUESS): 0x6499b0 returns a true distance (it ends in the sqrt 0xa8d554). After `fld scale; fmul 1000.0 (0xb5afc0)` ST0 = scale*1000, ST1 = distance; `fcompp; test ah,0x41; jne 0x807f2e` SKIPS the override when scale*1000 <= distance. So the search point becomes the BOT when the bot is WITHIN scale*1000 cm (10 m at scale 1) of the defend place, and stays on the defend place when farther. The report had it reversed. Consequence: an online bot already near its defend place searches around itself like Arcade, so "POINT path anchored on the defend place" can explain gate-4 failures only for bots farther than 10 m away, and only if [[[S+0x40]+0x54]+4] != 0 (still UNREAD).
- WRONG (hysteresis as a failure cause): the same-cover hysteresis (0x807fb8 `cmp [ebx+8],0; je`, and 0x807e37) runs only when a cover is ALREADY held ([S+0xec] != 0). A failed re-search returns at 0x808033 without releasing, so the eval still sees [S+0xec] != 0 and passes. Hysteresis can never make gate 4 fail. With no cover held the only gate-4 failures are index -1 (point path) or index <= 0 (target path) from 0x7f71e0 / 0x509f30.
- PARTLY WRONG (held-cover branch): 0x80f8d0 is not just "target not in view". It returns 1 (release) only when the holder flags are NOT the in-view set (0x80f8d7..0x80f8fb) AND more conditions hold (distance result vs tuning[0x108] at 0x80f91d, time since the stamp [[S+0x40]+0x54]+0x34 scaled vs 0xb4aaec at 0x80f956, [S+0xfc]/[S+0x104] at 0x80f961, [S+0x4f4] / 0x63d070 at 0x80f978..0x80f9a6). With the online LosGate flags (bit0 clear) the not-in-view side is reachable, so a held cover is released after those timers, not at once. A revalidation path (ebp-1 set at 0x807d5f/0x807d63) also re-searches while holding. Neither changes the conclusions.

### 0x509f30 geometry
- CONFIRMED all constants (1000, 1100, 500.0, 100.0, 600, 1400, 400, read from the image) and the three branches (d > 2s: 1000 cm toward the target, radius 1100; s < d <= 2s: len 500+500(d-s)/s, radius len+100; d <= s: P = self, radius 600). The 1400/400 clause (0x50a0ca) is only reachable if s > 1400.
- CORRECTION to "s = 1100": [S+0x6a8] is not constant. 0x6aa3be..0x6aa3f5 subtracts a tuning-object field (+0x50) from it whenever that function runs and snaps it to the constant at 0xba312c at the threshold 0xb22900 (also sets [S+0x57e] |= 0x80). As s falls toward 0 the d > 2s branch (1000 cm hop) applies more often. The claim "at most about 20 m, never onto the holder" still holds for any s >= 0.

### Q2 run body 0x4fee00
- CONFIRMED: [S+0xec]==0 returns (0x4fee0d); ==1 walks via 0x60d050 + RunChild vt+0x70; `mov byte [eax+0x4fc],1` at 0x4fee57; 0x46d330 via vt+0x194; the 300 cm human check releases (0x4fef53) and tail-jumps 0x807c60.
- ADDED: the release also requires the human's flag word bit 10 clear (0x4fef10..0x4fef1b) and [[[S+0x40]+0x54]+4] != 0 (0x4fef26). When [S+0xec]==1 and the walk finishes with the cover still held, control falls through to the 0x4fee57 branch in the same call.

### Q3 fire path
- CONFIRMED: 0x45fe7b `cmp [ebx+0xec],4`, 0x45fe8a `call 0x616480`, fire branch 0x45ff30 (0x749170 with 0x1b,3,0; [S+0x98]=1; vt+0x19c). 0x616480 flag logic CONFIRMED (bit0 set, bits 2/0x200/0x40 clear, 0x10 set).
- OVERSTATED: "AFC cannot fire with LosGate flags" is proven only for the 0x45ff30 branch. The goal function 0x45fca0 has further 0x749170(0x1b,3,0) sites: 0x4600f5 (animation from a table, then RunChild) and 0x460c14, reached from state 3 or 4 at 0x460b71 with [S+0x98]=2 and NO 0x616480 test on that route (only a distance/time test at 0x460b8f..0x460bc4). Whether [S+0x98]==2 produces shots is UNREAD. bs44/bs45 saw zero marked shots at the human, which supports "no fire" empirically, but statically it must be downgraded to "the [S+0x98]==1 route is gated; the ==2 route is unread".

### Q4 prediction
- INCONSISTENT with the evidence: the bs45 numbers (Board x531 etc.) were taken with OnlineBrainTraitorCombatFlag=3, where both flags are forced while blocked and Defend walks list A on about 90% of ticks (TARGET path for AFC). The report explains them with "CombatFlag=0, list B, POINT path". That reasoning applies only to the remaining list-B ticks (about 85 of 798 on DM03). Board (list A slot 4, list B slot 5) precedes AFC in BOTH lists, so while Board wins 531 times AFC is not evaluated at all. The AFC wins (15) and the DefendCover (117, exists only in list B) / NoCover (58) wins are the only ticks that say anything about AFC's eval. They do show AFC's eval returned 0 on at least ~175 ticks, so gate 2 or 4 fails there, but WHICH one is not identified. "Gate 4 via the POINT path / hysteresis" is unmeasured and the hysteresis half is refuted above.
- CONFIRMED: list orders. List B (0x6abede..0x6ac2d1): 0x5ec 0x5dc 0x5cc 0x5f8 0x5f4 0x5ac 0x5bc 0x5b8 0x594 0x59c 0x598 0x5b0 0x5c0 0x5a0 0x5f0 with the push addresses listed. List A (0x6abb6f..0x6abed9): 0x5ec 0x5dc 0x5f8 0x5f4 0x5ac 0x5bc 0x5b8 0x590 0x598 0x59c 0x5c0 0x5b0 0x5f0 (no 0x594, no 0x5a0). Side note: the ZDefendCover eval 0x84dc90 also RELEASES a held cover as a side effect (0x84dcd2 when 0x41bc30 fails).

### Levers
- L1 ([S+0x88]=2): SessionSafe (data write to a heap field, no code range touched, no detour). Sound only with caveats. (1) It changes nothing while CombatFlag=3 holds both flags, because the TARGET path is chosen regardless of mode. (2) Board precedes AFC, so without OnlineBrainTraitorNoBoard=1 (49677dd93) AFC is never reached while Board wins. (3) Other readers of [S+0x88] cannot be separated statically (the offset 0x88 is common across classes); attack_goal_1104.md already names 0x7088c0 and the 0x85ece0 clause (mode != 1 makes AttackNoCover eligible without [S+0x4fc]). (4) The online writer of 1 is unknown, so the value may be rewritten and must be written every tick like the CombatFlag bytes. By the override result above, L1 matters only when the bot is farther than 10 m from its defend place.
- L2: right idea, same side-effect warning; the override already centers on the bot inside 10 m, so L2 only changes the far case.
- L3: sound and already built; it is the prerequisite, not an alternative. L4 rejection ENDORSED.

### Endorsed next step
1. Do not implement L1 yet. First run the existing NoBoard build (49677dd93) together with RunProbe/DefendProbe; with Board gone, the winner distribution among CloseIn / AFC / DefendCover / NoCover on both lists shows whether AFC is reached at all.
2. Add a read-only per-second sample of the AFC eval inputs on the marked bot (hook-side reads, no detour): [S+0xb0], byte [[S+0x40]+0x5c8], [S+0xec], [S+0x88], [S+0x4fc], [S+0x6fc], [S+0x6a8], [[[S+0x40]+0x54]+4], and bot-to-defend-place distance. This separates gate 2 from gate 4 and tests the 10 m override reading.
3. Only if gate 4 fails with [S+0x88]==1 and the bot is farther than 10 m from [S+0x64c], add L1 as an ini toggle (default off, per-tick write, marked traitor only), and check the 0x7088c0 side effects in the same run.
