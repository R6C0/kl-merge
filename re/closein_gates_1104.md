# ZCloseIn eval gates, scan 0x767510, 0x3d6 targets (research wzosc72u0, 2026-11-04)

Static + bs43 DD05 log. Report, then the adversarial verifier (verifier wins).

# Report: ZCloseIn eval 0x6724e0, target scan 0x767510, and the 0x3d6 targets (bs43 DD05)

Method: static disassembly of kl2.exe (debug/dasm.py) plus the BS43C_DD05 KLHook.log. No game launch.
Confidence tags: [H] high, [M] medium, [L] low. GUESS marks anything inferred without direct proof.

## Q1. ZCloseIn eval 0x6724e0

The function returns the float 0.0 at the tail 0x672722 and 1.0 at 0x67272b (`fld1`). The `this` pointer is the tactic and `S` is the soldier. Every path to 0.0 is a gate, listed in code order.

| # | Gate | Address | Bails when | Conf |
|---|------|---------|-----------|------|
| P1 | Timer | 0x672505 `cmp edx,[edi]; jl` (edi = tactic+0x14) | now is below the stored timer. When the timer has passed, it is re-armed on every pass, before the other gates, to now + 1 to 4 s (rand*3+1 s), or now + 0.3 to 0.8 s when bl is set (`[[S+0x6d8]]==6`) | H |
| P2 | No holder | 0x67259a `cmp [ecx+0xb0],0; je` | handle at S+0xb0 is 0 | H |
| P3 | Smoothed value | 0x6725a9 `vcall S+0x84` (0x4cdca0, returns `[[S+0x10c]]`) compared with `[[0x168d7c0]+0x108]` | the global value is below the vcall value. Meaning unknown | M for the gate, GUESS for the meaning |
| P4 | Distance | 0x6725d9 `call 0x4087f0` (S to entity `[S+0xac]`), then 0x67267e `jp` | `[S+0x6a8]` >= d. Here 6a8 = 1100 cm | H |
| P5 | Time since event | 0x67260f `call 0x8a2e50` | value is below 0.3 (bl set) or below 5.0 (bl clear) | M |
| P6 | Holder not reachable | 0x672632 `call 0x651060(holder entity)` | when bl is clear and 0x651060 is false, 8a2e50 must be >= 10.0 (const 0xb3ef8c). 0x651060 returns true when `[S+0x4f4]` is 0, false when `[squad+0x1a4]==0`, otherwise it runs a distance-min loop (loop at 0x6510c2, compare at 0x651101 against a double at 0xb18cc0). Exact meaning GUESS | M |
| P7 | Count query | 0x672670 `call 0x76ca60` (wraps 0x6a5700, `ret 8`) | `cmp eax,1; jg` bails when the result is greater than 1. 0x6a5700 counts squad members (loop at 0x6a5737) whose `0x4087f0` distance is below the float argument. It returns 1 if the squad pointer `[S+0x4f4]` is 0. So this gate is "more than one squad member is near the holder", roughly | M for the mechanism, GUESS for the intent |
| P8 | Class mask | 0x6726a1 `call 0x4ea3b0` (0x1547b28/24) or `call 0x7aace0` (0x1548c80/7c) on the holder entity | the test is false | M |
| P9 | Nav path | `vcall +0x60` on `[[0xdd2640]+0xac]+0xc`, result at `[ebp-0x64]` | result is not greater than 1 (`jg 0x67272b` not taken) | M |

**What 1.0 computes (0x67272b)** [H]:
- It calls 0x4aea40 on the nav path with `-[S+0x6a8]*0.5`, which is 550 cm back from the path end.
- The resulting point is stored in the tactic's dest at `[esi+0x18..0x20]`, then `0x5caf90(S)` is called, and the function returns 1.0.
- So the destination is a point on the nav path toward the holder entity `[S+0xac]`, stopped 550 cm short of it. It does point at the holder entity.
- Log: the single 1.0 at clock about 167.7 s had dest -5131.3 419.6 12778.2, and the holder was 0x3d6 (flags 0x10), not the human. Timer set to 170225, wait 2493 ms.

**Which gate produced the 29 zeros** [M, cause of the post-timer zeros is GUESS]:
- Most of them are P1. Evidence:
  - About 14 calls fell within 3 s while the timer is 1 to 4 s.
  - The timer values seen were 170225, 173866, 175483, 178473 and 203951.
  - Defend evaluates several times per second, so most calls land inside the window.
- Only about 5 passes were past the timer. Those returned 0 at a later gate.
  - P2 is plausible: the log shows the holder alternating between "set" and "no handle" with flags 0 or 1. HolderSet and the 1024 ms scan, which clears or replaces the holder, race each other.
  - P4 is ruled out. The distances are about 7500 cm and up to 15000 to 18000 cm, far above 1100.
  - P3, P5, P6, P7, P8 and P9 are not probed in the log, so the log cannot separate them.
- After about 178.6 s there are no more eval calls, even though both bytes are set (4fc=1, 6fc=1) and the log says list A "would walk". [M] Either an earlier list A tactic wins and stops the walk (ZReactToHumanShield, ZBecomeTraitor, ZBoardEscapeVehicle, ZAttackMountedWeapon or ZCloseAttack), or Defend is not reaching the loop at 0x85f8f0. Not proven (GUESS).

## Q2. Target scan 0x767510

How the winner is chosen [H unless noted]:
- Candidates are only entries in the scan object B's array (`B = [S+0x698]`, `[B+0x154] = S`). Stride is 0x14 from B+4, count `[B]`. Entry fields are +0 flags, +4 entity, +8 type, +0xc time.
- Scoring comes from a vcall chosen by entry type:
  - type 1 (ZSoldier body) uses +0x1b8 = 0x7ffd20, which returns -1e38 if `[S+0x6d8][0]==6`, `[body+0x774]!=0` or byte `[body+0x5d8]!=0`.
  - type 2 uses +0x1bc = 0x882470.
  - other types use +0x1c0 = 0x7ebf50.
- Best starts at -1e38 (0xb5f1e0) and is replaced only if strictly greater.
- No winner: `test ebx,ebx; je 0x767f77` leads to `SetHolder(0, &0x168e35c)` at 0x767f8a, which clears the holder. A winner leads to SetHolder at 0x767eee, with the handle from 0x6ece90.
- There is no team test in the loops. [M]

Why a non-human wins over the human:
- Under LosGate, the human is not in B's array (Sense skips blocked humans). The log's "traitor target ... B list" lines show only `t1 ZSoldier` entries with flags f010, 0 to 5 of them, and no human.
- So the human cannot be chosen. Some ZSoldier with flag 0x10 (in range) wins, or nothing wins and the holder is cleared. [H for the mechanism]

When it overwrites [H]:
- The quick path at 0x767527 to 0x767675 applies when arg is 0, `[B+0x184]==0` and now is below `[B+0x180]`. It returns at once if the holder is 0 or now <= `[B+0x18c]`. Otherwise it rewrites only the flags dword (store at 0x76762e) and keeps the handle.
- The full scan runs at 0x767678. It sets `[B+0x180] = now + 0x400` (a fixed 1024 ms) and `[B+0x18c] = now + rand*0.5*const`.
- A forced rescan happens when MarkSeen (0x4880d0) sets `[B+0x184]=1`, so it can be more frequent than 1024 ms.
- The log fits this: HolderSet writes were 29/27/16/25/21/13 per 30 s round, about one per second.

Is there a data-only way to keep or prefer the human?
- No, not while LosGate hides the human. The scan has no stickiness for an externally set holder and only considers B's array.
- Removing LosGate is the data lever, but bs42 showed that it brings back through-wall fire. [H]
- HolderSet must re-assert after each full scan. The scan is at least about 1 s apart except for forced rescans, so a 100 ms re-assert cadence can keep the holder most of the time. A forced rescan or the arg!=0 path can still clear it between ticks. The log shows "no handle" in about half the samples around 09:38:30 to 09:38:40 (cause GUESS: forced rescans or the re-assert timing). [M]

## Q3. What 0x3d6-like targets are

- The handles 0x39a, 0x3b4, 0x3ba, 0x3c0, 0x3d6 and 0x3e8 are ZSoldier-controlled bodies. The log tags them "t1 ZSoldier" in the B list. [H that they are type-1 ZSoldier entries]
- They are most likely the other 6 of the 7 tagged Ally crew bots. Cops are 0 in this run. The concrete class name (for example a ZFFActor body) is GUESS.
- The human handle is 0x1ab, which is far outside that range. The Arcade holder values (0x320, 0x364 to 0x3e8) are in the same pool range.
- Yes, the marked bot is shooting at them, and this is expected stock behaviour:
  - TraitorFoe=1 makes a turned bot team Enemy, so the crew and escort shoot him and he shoots them.
  - Fireprobe7 shows target `[+0x828]` and holder `[soldier+0xac]` both = 554d0660 ("something else"), about 22 mentions in 28 lines.
  - The human is about 75 to 175 m away, outside range R 6000 cm, so flag 0x10 is clear for him and he could not be fired on anyway. The 100 marked shots at "something else" are all LOS-blocked.

## Recommended next lever

Data-only first:
1. Re-assert the holder from HolderSet on every host tick, with flags 0x01. Use the 1024 ms scan cadence to place the write directly after each scan, not on a fixed 100 ms timer. Add a per-eval gate-trace so the log shows which gate (P1 to P9) returns 0.0. [M]
2. Log which earlier list A tactic wins after clock about 178.6 s (read each earlier tactic's eval result). This answers why ZCloseIn is never called again.
3. Do not feed the human into B through MarkSeen. LosGate keeps him out on purpose, and doing so brings back the through-wall fire seen in bs38 and bs42.

Where this leaves ZCloseIn: even with a stable holder, the nav-path gates P7 to P9 are unprobed, and the eval is timer-gated to roughly one real attempt per 1 to 4 s. A holder that is the human is therefore necessary but may not be sufficient for ZCloseIn to return 1.0. The cheap measurement is the per-gate trace in step 1.

Files referenced (all read-only): `C:\kl-merge\kl-merge\re\closein_prereqs_1104.md`, `C:\kl-merge\kl-merge\re\holder_b0_1104.md`, and `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\klhook\solo\BS43C_DD05\inst1\KLHook.log`.

## Verifier

CLAIMS TABLE (adversarial verification of the ZCloseIn 0x6724e0 / scan 0x767510 / bs43 DD05 report; static disassembly and log reading only)

| # | Claim | Verdict | Correct reading |
|---|---|---|---|
| 1 | The ZCloseIn timer is re-armed before P2 | CONFIRMED | |
| 2 | Gates P2, P3, P5, P8, P9 work as described | CONFIRMED | The meaning of P3 is UNVERIFIED (see 21). |
| 3 | The success block's destination | CONFIRMED | |
| 4 | Timer values (units are 1/1024 s) | CONFIRMED | |
| 5 | Structure of the target scan: object B = [S+0x698], [B+0x154] = S | CONFIRMED | |
| 6 | The no-winner clear at 0x767f8a | CONFIRMED | |
| 7 | HolderSet counts ("kept 62, writes 0") | CONFIRMED | |
| 8 | Defend walks list A only when [S+0x4fc] and [S+0x6fc] are both nonzero (0x85f896) | CONFIRMED | |
| 9 | No more evals after 178.6 s | REFUTED | One more eval occurs at about 200 to 202.26 s. |
| 10 | P4 is ruled out by the 7500 and 15000 to 18000 values | REFUTED | Those are distances to the nearest human or the arm position, not to the holder. P4 stays open. |
| 11 | 0x651060 is a min loop | REFUTED | It is a max-distance loop times 0.7. |
| 12 | P7 reads "below" | REFUTED | The compare is <=. |
| 13 | B-list entries have flags f010 and 0 to 5 entries | REFUTED | Sizes run 0 to 10 with varied flags. |
| 14 | Cops 0, 6 crew bots | REFUTED | The census is 7 Ally and 28 other-team actors. At least 10 distinct non-human holder handles were seen. |
| 15 | About 100 marked shots at something else, all LOS-blocked | REFUTED | The LOS test is muzzle or eye to the human chest. Aim to holder under 5 deg is 37 shots. Aim to human is 0. |
| 16 | "mentions ~22" | REFUTED | The count is 13. |
| 17 | The scan has no stickiness | REFUTED | Strictly wrong, but a LOS-hidden human is still never a candidate. |
| 18 | R=6000 | UNVERIFIED | Supported only by the notes in re/traitor_fire_1103.md. |
| 19 | "No team test" in the scan | UNVERIFIED | |
| 20 | The nav-path identity of P9 | UNVERIFIED | |
| 21 | The meaning of P3 and P6 | UNVERIFIED | |
| 22 | The class of the 0x3xx holder handles | UNVERIFIED | |
| 23 | The range source for flag 0x10 (0x71e050) | UNVERIFIED | The disassembly was partial. |

OPEN QUESTION: In the last window of about 252 samples, [S+0x4fc], [S+0x6fc] and the holder were all set. There were still 0 ZCloseIn evals. Two candidates are untested: an earlier list A tactic passes before ZCloseIn, or the list C override at 0x85f8c2 applies. Neither is proven.

ENDORSED NEXT LEVER: Not a holder re-assert, and do not feed the human into list B. First add a read-only Defend-loop probe at 0x85f8f0. It should log:
- the list chosen, including the list C condition ([body+0x5c8] and 0x575100(body));
- each list A tactic's eval result, to find which tactic passes before ZCloseIn;
- the current goal.

Then add a per-gate ZCloseIn trace (P1 to P9) to see which gate fails.
