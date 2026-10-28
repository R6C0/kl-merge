# Bot-carried loot in the REAL online money (static research, 2026-10-28)

Static reading of kl2.exe only (base 0x400000). Nothing was run, installed or committed. CERTAIN = read in disassembly.
GUESS = inferred. Companion docs: re/bots_online_arcade_1028.md, re/bots_bench_1028.md, re/online_round_data.md.

## 0. The online money model (CERTAIN, this pass)

The score object S = [rules+0x2c] (DDL_ZScoreFragileAlliance, a globaldo; the HOST owns it) holds 12-entry arrays at container C = S+0x58:
- `S+0x188` = **Sharable** (C+0x130 + 4*seat). This is the CARRIED / team-pot money. Getter `0x699030` (thiscall ecx=S, 1 arg seat, ret 4).
- `S+0x224` = **Unsharable** (C+0x1cc + 4*seat). Getter `0x783780` (same shape). Added by `0x7f3050(seat, amt)`, subtracted by `0x4ef8b0`.
- Status flags (C+0xc..): getter `0x571750(S, seat)`; setter `0x601fd0(S, seat, bits)` (or) / `0x514530` (clear). Bits: 0x01 (kept-own, "traitor/rogue" branch), 0x04 dead, 0x08 police, 0x40 escaped, 0x80 lost, 0x2000 busy looting.

### The one function that adds money: `0x5a18c0` (AddSharable)
```
thiscall, ecx = S ([rules+0x2c]); stack: int8 seat (pushed as a dword), int32 amount; ret 8
  7dea30(C, seat)         ; dirty seat byte  C+0x1fc = seat
  76b490(C, seat, amount) ; [C + seat*4 + 0x130] += amount ; word [C+0x1fe] |= 2  (field mask)
  942b20(S, <timestamp>)  ; commits the DO delta (see risk section)
  57aca0(C)               ; clear dirty byte/mask
```
Callers: the online grab (0x6135f0 at 0x6137ec and 0x61398d), the settlement (0x5e2230 at 0x5e22d4, 0x5e2394), 0x5e2230-like helpers. Push order at
0x613988: `push ebx(amount); push edx(seat)` so seat is arg1, amount arg2.

### How a human grab pays (the online state machine, 0x6135f0)
`ZOnlineMoneyCtrl` slot 26 (0x6cdb40) -> online rules slot 46 (0x8234d0) -> `0x7ceaf0(seat, ctrl)` starts a grab: seat record
(`[rules+8] + seat*0x74`, byte +0x11 = 1, +0x18 = the stack, +0x14 = time of one part), flag 0x2000 set via 0x601fd0, `0x5973c0(player,1)` (loot anim).
The per-record tick `0x6135f0(this=rules, seat, dt)` (jump table 0x613b38, called from 0x80ae43) pays a part when the clock runs out:
`0x4e3f40(stack, part)` (depletes the stack), then `0x5a18c0(S, seat, part)` at 0x61398d, then `rec+0x34 += part/5` (0x66666667 magic). The part is capped
at the stack's remaining (0x74da10). A per-seat cap is checked by `0x699030 >= [0xd1b3d0]` (0xf4240 = 1,000,000), which only gates a "bag full" UI/state.
Everything keys on the seat: `0x8e8010(player+0x2748)` (seat table +0xd8 -> 0x5b1400). A bot has no ZFFPlayer seat, no record, so none of this runs for it.

### Where the money turns into the team pot and the round score
- `0x6f4960` (thiscall rules; run from the rules tick at 0x567286 while state is 0x19 or 0x29, so on host and clients) rebuilds the table every tick:
  `[rules+0x34]` = sum of Sharable of seats with flag 0x40 and not (0x01|0x04... see 0x6f49af: skips seats with 0x01 or 0x04), `[+0x38]` = their count,
  `[+0x3c]/[+0x40]` = same for police (0x08). Per seat (record +0x24 "reward", +0x28 "total"): escaped merc (0x40, bit 0x01 clear) gets
  `own*(1-p) + pot*p/n`, with `p = 0x7360a0() = fld1 = 1.0` (a constant, not a setting) -> **the pot of all escapees is split equally**. Seats with bit 0x01 keep their own.
  Police/dead seats get the police average. The HUD money (0x5675fc) is the OWN seat only: Sharable + Unsharable.
- `0x5e2230` (thiscall rules, no stack args; ONE direct caller, 0x681103 inside Sv slot 192 = 0x680f90) is the one-shot settlement at round end: dead (flag 0x80)
  and police (flag 0x08) seats lose Sharable (0x5632d0 subtract, then 0x5a18c0 gives back 1/10, or all if flag 0x1000), then it tail-jumps to 0x6f4960.
  0x680f90 reaches it once, when the round-end timer [rules+0x200] has run out and the escape byte [rules+0x1dc] is 0 or >= 7, then sets state 0x1f.
- The van does NOT total money: ZOnlineExitLevelTrigger (0x6c3d50) sets the escaped flag/record state; money is whatever Sharable the seat holds. So route (c) is the
  same sink as (a).

## 1. Route (a): host calls `0x5a18c0` for a human seat -- RECOMMENDED

What: when the host counts a bot aboard (klbotfill.c klbf_bank_pass, `phase == 3`, `tally > 0`) it adds the tally to a HUMAN seat's Sharable with
`0x5a18c0(S, seat, tally)`. At round end `0x6f4960` pools all escaped mercs' Sharable and splits it equally, so the bot's loot becomes part of the real team pot,
the end-of-round table (record +0x24/+0x28), and the scoreboard.

Call details (hook C, host only, role 2, FA sub-mode `[0x168e59c] == 0`, state 0x19):
```c
typedef int (__thiscall *add_sharable_t)(void *S, int seat, int amount);   /* ret 8 = callee pops 2 args */
S = *(void**)(rules + 0x2c);  fn = (add_sharable_t)0x5a18c0;  fn(S, seat, amount);
```
- seat: pick a host-side human that will be paid. Two modes:
  1. END (recommended, default): keep the existing ledger; at round end credit once. Hook the single call site `0x681103` (`call 0x5e2230`) or the entry of 0x5e2230 and, BEFORE the original runs,
     choose the first seat i < [rules+0x14] with record in use (`[rules+0xc][i] == 0`), `flags = 0x571750(S,i)`, `flags & 0x40` set and `flags & 0x0d == 0` (escaped, not dead/police/bit-1),
     call `0x5a18c0(S, i, ledger)` and zero the ledger. 0x5e2230 then runs its loops and tail-calls 0x6f4960, which recomputes pot and shares in the same call, so no extra tick is needed.
     If no human escaped, drop the ledger (all escapees dead or none: the same outcome as humans losing carried money).
  2. LIVE (optional): at board time credit the host's own seat (`0x7af9d0` on [0x168e598], returns al) so the host HUD jumps at once. Risk: if that human then dies, settlement
     (0x5e22a9..0x5e22d4) takes 90% back; if the human is police or never escapes, the money is not in the pot.
- amount: clamp so Sharable stays <= `[0xd1b3d0]` (1,000,000) to mirror the game's cap (GUESS that nothing breaks above it; the HUD field is 32-bit).

What is replicated, and how: `0x5a18c0` writes the container element and sets field mask C+0x1fe |= 2 (and dirty seat C+0x1fc), then `0x942b20` commits the Quazal DO
delta. The dataset `DDL_ZScoreFragileAllianceContainer` is `update_perf_counter basic_update_protocol` (reliable, not the unreliable position class), so every client's
copy of S updates and the stock client code (0x567580 HUD, 0x6f4960 table) reads the new value unchanged. No RMC, no hook-side packet.

Risks:
- Host only. 0x942b20 compares the DO owner ([S+0x14]) with the local station; on a non-master it raises Quazal exception 0xe0030000 (0x942b7b..0x947300). Gate on role 2 (host Sv).
  Never call on a client (it would also be overwritten by the next delta).
- Call from the game thread (the hook's per-frame tick or a detour of 0x681103). It touches the DO manager (0x48eb30/0x93fd10 lock pair around the commit); a call from another thread can corrupt it.
- 0x5a18c0 has no bounds check on seat (movsx byte, array of 12): use an index that passed the record-in-use test.
- Double count: the Arcade-style `tally` includes money a bot picked up via OnlineTacticsTake. With TacticsTake=2 the stack is also depleted through 0x4e3f40, so human pot is not double counted;
  with TacticsTake=0 (stack stays) the same loot could later be grabbed by a human: book only for take modes 1/2.
- Fairness: all escaped mercs share it equally (p = 1.0). A bit-0x01 seat keeps only its own money, so avoid crediting that seat.
- Desync: none expected; the value is host-authored in replicated state, clients never compute it. A mid-round join receives S in the full state.

Confidence: HIGH that 0x5a18c0 adds Sharable and that 0x6f4960 pools it (both read end to end). MEDIUM-HIGH that the commit replicates to clients (0x942b20 read; the stock host
grab uses the same call). MEDIUM on the choice of seat/timing (settlement flags read, never seen live).

## 2. Route (b): give bots a virtual seat -- REJECT

S has 12 entries and `PlayersMax=12` is already used (re/max_players.md), so a bot has no free index in a full lobby. Every consumer first checks the record-in-use byte
`[rules+0xc][seat] == 0` (0x625be4.., 0x6f499c, 0x5e226b, 0x819ab4): a seat without a 0x74-byte record is ignored by the pot (0x6f4960), the HUD list and 0x5e2230, so S alone is not enough.
A fake record needs `[rec] = client object` whose +0x378 player (ZFFPlayer) is dereferenced by 0x7ceaf0 (0x7ceb02), 0x6135f0 (0x613622 `[player+0xa54]`, `[player+0xad4]`) and many rules slots
(0x82350a, 0x719720 `[player+0x2748]`), plus a Quazal client object. High crash risk, phantom rows in the scoreboard, and every Arcade-vs-online parity issue again. Not worth it.

## 3. Route (c): the van total -- not a separate mechanism

There is no van-side money total online. The round-end money comes only from `0x5e2230` + `0x6f4960` (section 0), driven by the Sharable arrays; the van sets flags (0x40) and record state 6.
A bot boarding therefore needs route (a)'s credit. A hook at `0x681103` is the natural single flush point (that is the "van total" moment, once per round).

## 4. Recommendation

Route (a), END mode, one hook point:
1. Host ledger already exists (klbf_bank_total / per-bot tally with phase 3). Gate: role 2, FA sub-mode `[0x168e59c]==0`, session state 0x19..0x1f.
2. Detour the call at `0x681103` (or the entry of 0x5e2230; thiscall, ecx = rules, no stack args, plain `ret`, 6 bytes of prologue needs checking if entry-hooked, the call site is safer
   as a 5-byte rel32 patch) to a stub: choose the escaped-merc seat, `0x5a18c0(S=[ecx+0x2c], seat, ledger)`, then call the original 0x5e2230 with the same ecx.
3. Log both the seat/amount and `0x699030(S,seat)` before and after, plus `[rules+0x34]` (pot) and `[rules+0x38]` (count) after 0x6f4960 ran (read at the next tick), for the bench.
Toggle: `OnlineBank=3 ; (recommended on once benched)` (1/2 stay ledger only), `OnlineBankLive=0`.
Bench proof: host log `bank: credit seat S $X (before B, after A)`, client `online read` shows the same seat Sharable (S+0x188+4*seat) one tick later, the end-of-round table pot
`[rules+0x34]` includes the bot money, each escaped merc's record +0x28 rises by X / n; 0 faults.

## 5. Unknown / not verified

- Live behaviour: none of this ran. The 0x942b20 commit was read only up to the dispatcher call (`vt[0x34]` on object from 0x960ff0); that it is the reliable delta send is inferred from the dataset flags.
- Where record +0x24/+0x28 (the reward/total, computed on both peers) is then written to S+0x1b8/0x1e8 (TotalLoot/TotalReward) or to Unsharable (S+0x224) at the very end: not traced
  (candidates 0x8ea4e0, 0x6f9410, 0x5062d0 call 0x7f3110/0x7f3050). The credit goes through the same Sharable path as a human's, so it should follow; confirm with a live end-of-round read.
- Meaning of status bit 0x01 (traitor/rogue vs "UCC cop") and exact bits of 0x80/0x1000 in 0x5e2230: named by behaviour only.
- Whether a state-0x29 (Cops and Robbers) round matters: gated off here (FA only).
- Whether the scoreboard shows bots at all (no seat, no row): the bot money appears inside the humans' totals only, never as a bot row.
- Whether clients show the Sharable change live in the HUD before round end (0x567580 reads own seat Sharable+Unsharable: yes for a credited own seat; other seats not).
