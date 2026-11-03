# Arcade brain online, stage 2 (+ stage 3 traitor / cops): code-level design (2026-11-03, offline, no game launched)

Scope: `klhook/klbrain.c` today = stage 0 (Probe) + 1a (Build: the three tactics exist on every online soldier) + 1b (Loot EVALUATE swapped into a shadow
rules, PuppetOff). This file is what stage 2 adds: shadow contents, cadence, the swap frame for EVALUATE (slot 11) and RUN (slot 2) and EXIT (slot 3) of
Loot, Board and Traitor, the loot-to-real-money bridge, the Board-to-van path, the PuppetOff hand-off, stage-3 traitor and bot-fired cops, every crash risk.
Sources: `re/arcade_brain_online_1102.md` (plan), `re/arcade_brain_shadow_1102.md` (contract), `re/online_round_data.md`, `re/bots_loot.md`, plus this
pass's disassembly (debug/dasm.py on kl2.exe 0490): 0x451920, 0x451aea.., 0x7bc7d0, 0x727cb0, 0x8e8750, 0x8b94d0, 0x78f470, 0x5478e0, 0x488eb0, vtables.
CERTAIN = read in the exe (this pass or a cited note). GUESS = inferred; each GUESS says how it is checked. Every item in a table has the mark in its last cell.

Ship rules that bind everything below: no code-byte patch (CEG); only heap, .data/.bss, IAT, DLL-owned (VirtualAlloc) memory and DLL-owned vtable copies.
Every new behaviour: ini key default 0, label "(recommended off)", a `kl_mod_options` row, a `KLHook.ini` line (`tools/kl_mod_options_test.py` checks), pure logic
in a `*_logic.h` with a `*_test.c` in `tools/kl_tests.py` C_TESTS. Guessed fields carry a `GUESS` comment in C.

## 0. New certain facts of this pass (they change the plan)

| # | fact | where | mark |
|---|---|---|---|
| 0.1 | Tactic RUN (slot 2) takes NO stack argument for all three: every `ret` of Loot RUN 0x7bc7d0 (the `ret 4` at 0x7bccc1 belongs to the next function), Board RUN 0x82f970 and Traitor RUN 0x488eb0 is a plain `ret`. EVALUATE (slot 11) likewise (0x451920 / 0x4faf60 / 0x79b7c0: plain `ret`, float in st0). So RUN and EVALUATE are `float/void __fastcall f(DWORD self, DWORD edx)` for the frame wrapper; no naked-stub argument copy is needed. This closes the "unknown arg bytes" problem of the plan. | disasm, `ret` scan | CERTAIN |
| 0.2 | Slot 3 (EXIT) of Loot and of Traitor = 0x66b570 = a bare `ret`. No swap needed, keep the tail-jump stub (or drop the slot-3 override for those two). | vtables 0xbd0d94 / 0xbd13bc, 0x66b570 | CERTAIN |
| 0.3 | Slot 3 (EXIT) of Board = 0x5478e0: `G = 0x508ef0([0x168e9e4])`, then `mov edx,[eax]` with NO null test, `vt[0x2f4](G)`, if true: `[[tactic+4]+0x40 +0x8f1] = 1` then tail-jump 0x7bbf70(soldier). Outside the frame `0x508ef0` returns 0 online, so the CURRENT stage-1a stub `klbr_st_b3` (a pass-through) is a latent crash the first time the engine pops the Board tactic. It must run in the frame (or be replaced by a plain `ret` while the shadow is off). Rule from the contract extends: ALL of Board slot 2 and slot 3 run in the frame or not at all. | 0x5478e0 | CERTAIN |
| 0.4 | Loot RUN does not start the grab. It walks to the chosen object; the grab is started by the object's TRIGGER BOX (ZTriggerBox2 0x626ec0) -> money ctrl message `AI_TRIGGER_WITH_ACTIVATOR` -> rules slot 201 (0x56f6e0, gate: session state == 0x19, actor alive `+0x576`, crew record via 0x78f470) -> 0x8e8750. The box accepts a non-player only when `0x7f6850()` (Arcade) and the actor's team `[[actor+0x54]+4] == 2`. Online `0x7f6850` is false (roles 2/3) outside the frame, so bots never fire money boxes: that is why stage 2 needs a DLL-side trigger (section 5). | `bots_loot.md` 62-71, 0x56f6e0 | CERTAIN |
| 0.5 | Loot RUN calls the rules directly at 0x7bc8a5: `0x508ef0(G)`, `0x78f470(rules, actor-or-null)` (seat byte), vt[0x1c8](seat) `& 0x2000` (= already grabbing -> return at 0x7bcb65). Candidates live in the TACTIC (`+0x14..+0x24` = 5 object pointers, `+0x28` = chosen object, `+0x2c` = index), not in the rules. So RUN needs the same shadow facts as EVALUATE (a crew record whose `+4` is the actor and whose `+0x79` bit 0 is set) plus flags dword `[[rules+0x5f8]+0x1d4+4*seat]`. | 0x7bc7d0, 0x451920 | CERTAIN |
| 0.6 | Slot 202 (0x328, Heist 0x8b94d0) is the candidate collector. Signature: `thiscall(rules, pos, out)`, `ret 8`; EVALUATE calls it at 0x451a3f with arg1 = a local at `ebp-0x74` (position data, read by the comparator 0x455b40 and the sort 0x7bbe80/0x7b29a0/0x441f40 as the key) and arg2 = the tactic's candidate array (5 dwords at tactic+0x14, GUESS only in that the lea at 0x451a1c is garbled in the listing; consistent with RUN reading `[esi+4*i+0x14]`). It fills the nearest <=5 eligible ctrls from rules lists `+0xdc0/+0xdcc` (4-byte entries) and `+0xdac/+0xdb8` (8-byte entries, byte `+4` must be 0), filters by tuning windows `[0x168d7c0]+0xc1c/c20/c24/c28`, ctrl taken (0x4536e0), ctrl `+0x6c` in play, and returns the rest zeroed; EVALUATE returns 0.0 when `[array]==0`. | 0x8b94d0..0x8b9a85, 0x451a32 | CERTAIN (arg count and role), array position GUESS |
| 0.7 | The record tick 0x727cb0 is `thiscall(rules, seat byte, float dt)`, `ret 8`. States of `rec+0x15` via jump table 0x728204: 0 -> 0x727ce3, 1 -> 0x727f82, 2 -> 0x7281ba, 3 -> 0x727db8. State 0 and 3 are the HUMAN path (they read the local player `0x660b00([0xdd265c],0)`, `+0xa54`, `+0xa84`); the BOT path is 0x8e8750 (sets state 1) then state 1 (0x727f82). The part payout is at 0x728007..: `part = min(ctrl+0x40, remaining 0x74da10)`, `0x4e3f40(ctrl, part)`, `[[rules+0x5f8]+0x150+4*seat] += part`, `rec+0x38 += part/5`, `[[rec]+2] |= 8`, HUD calls on the global `[0x168e958]` (0x4d1380 at first tick, 0x862e70 / 0x8a7020 conditional), then the 0x2000 flag is cleared at 0x7281a1. Because of the HUD calls on bot seats and the state-0/3 player reads, the DLL does NOT run 0x727cb0 for bots: it runs its own tick (section 5). | 0x727cb0..0x7281ba | CERTAIN (reads); state naming GUESS |
| 0.8 | Online van state is mirrored on both Sv and Cl at `[rules+0x1dc]` (byte), `[rules+0x1d8]` (float), `[rules+0x1e4]` (vehicle), written by rules slots 87/94/89 from S `+0x25c/+0x38c/+0x3ac`. The shadow gets its van state by COPY of `[realrules+0x1dc]` each tick. This replaces the plan's GUESS in 3.1 / 7. | `online_round_data.md` 63-65 | CERTAIN |
| 0.9 | `rec+0x79` masks: 0x01 = registered AI/actor record (needed by 0x78f470), 0x02 = traitor (set by Traitor RUN, `or byte [rec+0x79],2` at 0x488ecd). The slot argument `[tactic+0x14]` of Traitor RUN is the record index (`movzx [esi+0x14]`). | 0x488eb0, 0x78f470 | CERTAIN |

## 1. Architecture in one picture

```
 real online rules R (Sv/Cl, vt 0xbd2eb4/0xbd31e4)        shadow rules W (DLL heap, vt copy of ZGameRulesHeist 0xbd3514, 0xf30 bytes)
        |  host tick (klbf_ot_run, game thread)                  ^
        |  "sync": R -> W  (money, van, crew, level, flags)      |
        v                                                        |
   FRAME(bot):  [sm+0x54] := 0 ; [G+0x54] := W ; ORIGINAL tactic slot ; restore both in __finally   (one tactic call per frame)
        |
   inside the frame the engine sees an Arcade host: 0x7f6850 true, 0x508ef0(G)=W, vt[0x12c]=W+0x1dc, 0x78f470 over W's crew table
        |
   W's DLL-owned vtable slots (stubs) hand the effects back to the real online objects:
      slot 201 (grab start)   -> DLL grab table + ledger (sec 5)        slot 202 (candidates) -> nearest 5 from the REAL ZOnlineMoneyCtrl registry
      slot 45 (0xb4, board)   -> mark bot boarded in the host ledger (sec 6)   slot 114 (0x1c8 flags)/55/56 (money getters) stay Heist originals on W
```

The frame is the one in `klbrain.c`: `klbr_swap_in` writes `*(G+0x54)=klbr_shadow`, `*(sm+0x54)=0`; `klbr_swap_out` restores; `[sm+0x5c]==4` already holds online
(shadow doc section 0). Game thread only (the existing hook point is the puppeteer tick and the tactic stubs, both on the game thread).

## 2. Shadow block layout (every offset the four routines read or write)

Allocation: one `VirtualAlloc` zero block, W = 0xf30 bytes (`+0x00` vtable copy, 256 dwords of 0xbd3514 as today), crew array `0x7c*12 = 0x5d4`, crew free bytes 12,
score block 0x400, client dummies 12 x 0x20, the DLL grab table. All inside ONE block so one `VirtualFree` removes it.

### 2.1 Rules W fields

| W+ | type | value | read by | mirror source / writer | mark |
|---|---|---|---|---|---|
| 0x000 | ptr | DLL copy of vtable 0xbd3514 with slots 45, 201, 202 replaced (sec 4); all others the Heist originals | everything | built once (`klbr_make_shadow`) | CERTAIN |
| 0x054 | -- | NOT part of W. `[G+0x54]` is the settings slot that points AT W | `0x508ef0`, `0x7bb2a0` | frame only | CERTAIN |
| 0x1d8 | float | van countdown seconds | Board vt[0x130] (0x63b300) | copy `[R+0x1d8]` | CERTAIN |
| 0x1dc | byte | van state: 0 idle, 1/2 called, 3 waiting at the door, 4 boarding | Board EVAL 0x4faf60, RUN, exit; vt[0x12c] 0x5d52f0 | copy `[R+0x1dc]` | CERTAIN |
| 0x1e0 | ptr | boarding object (its `+4` is the node) | 0x5aeb00 | copy `[R+0x1e0]` if non-null else the klbf van trigger (klbotfill `klbf_ot_trig`) | CERTAIN field; whether R holds it online GUESS (check: log `[R+0x1e0]` and `[[R+0x1e0]+4]` in the Probe line) |
| 0x1e4 | ptr | boarding vehicle | 0x5aeb00 (both must be non-null) | copy `[R+0x1e4]` | CERTAIN |
| 0x338 | i32 | traitor count | 0x43ffb0 | stays 0, written by 0x4322f0 | CERTAIN |
| 0x33c | byte | traitor mask | 0x4322f0 | stays 0 | CERTAIN |
| 0x33e+idx | byte | character slot per record (voice table, not read by tactics) | 0x6ae750 | mirror of the klchar mapping, optional, GUESS | GUESS |
| 0x348 | ptr | crew array, 12 x 0x7c | 0x78f470, 0x7fd930, 0x5dd890, 0x727cb0 | built once | CERTAIN |
| 0x34c | ptr | 12 bytes: 0 = record live, nonzero = skipped | 0x78f470 | live for bot records and record 0; 1 for unused | CERTAIN |
| 0x350 | i32 | free count | not read by the three tactics | 12 - used | GUESS (name only) |
| 0x354 | i32 | record count (loop bound) | 0x78f470, 0x5dd890 | 12 | CERTAIN |
| 0x5f8 | ptr | score block S2 (sec 2.3) | 0x727cb0, 0x8e8750, 0x46d4d0, 0x43ffb0, vt[0x1c8], vt[0xe0] | built once | CERTAIN |
| 0xdac, 0xdb8, 0xdc0, 0xdcc | i32/ptr | candidate lists | Heist 0x8b94d0 only | NOT filled: slot 202 is replaced (sec 5.2); leave count 0 | CERTAIN |
| 0xdd0 | i32 | total-loot threshold used at 0x72812b (HUD cue) | 0x727cb0 | irrelevant (tick not run) | CERTAIN |
| 0xe70, 0xe78, 0xe89 | ptr/byte | first-loot cue bookkeeping | 0x727cb0 | irrelevant (tick not run) | CERTAIN |

### 2.2 Crew records (stride 0x7c, index = shadow seat)

Record 0 = the host human (mirror only). Records 1..11 = AI heisters, assigned in `OnlineBrainAssign` order (bots enumerated as klbotfill does: entity table, ZFFActor
vtable 0xbb3bac, no seat).

| rec+ | type | value for a bot | read / written by | mark |
|---|---|---|---|---|
| 0x00 | ptr | pointer to a 0x20-byte zero block C (client dummy) | 0x727cb0: `byte [C+0] == 0`, `C+1` = bit index for ctrl `+0x80`, `C+2 |= 8`; `0x5c3b10(C)` only when `rec+0x79` bit0 clear | CERTAIN; set `C+1 = idx` |
| 0x04 | ptr | the actor, `*(soldier+0x40)` (the same expression the tactics use: `[[tactic+4]+0x40]`) | 0x78f470 compares `[rec+4] == actor` | CERTAIN |
| 0x10 | byte | 0 for bots; record 0: 4 when the host human is boarded | Board RUN `lpboarded` (0x7fd930(0)+0x10 == 4) | CERTAIN |
| 0x15 | byte | grab state 0 idle / 1 grabbing (written by the DLL grab table only) | 0x8e8750, 0x727cb0 | CERTAIN |
| 0x18 | float | seconds left for the current part | same | CERTAIN |
| 0x1c | ptr | ctrl being grabbed | same | CERTAIN |
| 0x38 | i32 | xp accumulator (part/5) | 0x727cb0 | CERTAIN; unused by us |
| 0x78 | byte | stage, monotone max (0x5dd890) | gate triggers | CERTAIN; leave 0 |
| 0x79 | byte | bit 0 (1) AI record, bit 1 (2) traitor | 0x78f470, Traitor RUN, 0x727cb0 | CERTAIN; set 1 at assign |

### 2.3 Score block S2 (`[W+0x5f8]`, 0x400 bytes)

| S2+ | meaning | value | read by | mark |
|---|---|---|---|---|
| 0x45 | level byte (clamped 1..11 by 0x46d4d0 / 0x43ffb0) | `OnlineBrainLevel` ini (default 6), later derive from round number | Traitor EVAL tuning rows | CERTAIN field; derivation GUESS (online has no Arcade level twin) |
| 0x150 + 4*seat | money (i32) | the host ledger value `klbf_ob[bot].tally` copied each sync; the DLL tick adds part on a grab | Traitor EVAL, vt[0xe0], HUD cue | CERTAIN |
| 0x1d4 + 4*seat | crew status flags (dword) | bit 0x2000 = busy looting (set at grab start, cleared at end); other bits 0; the Heist getter vt[0x1c8] (kept) reads exactly this | Loot EVAL / RUN | CERTAIN |

## 3. Update cadence

Sync (R -> W) is one pure function `kbr_sync_plan(...)` in `klbrain_logic.h` fed by plain values, so it is unit-testable; the C side only reads memory with SEH guards.

| what | when | cost / guard | mark |
|---|---|---|---|
| crew assign (record per bot, `rec+4`, `rec+0x79=1`, `34c[i]=0`) | when a bot is first seen with a built brain, and whenever `[soldier+0x40]` changes (respawn); free the record when the actor is gone or dead (set `34c[i]=1`) | list of <= 11; no allocation after init | CERTAIN need; policy GUESS |
| van fields (0x1d8, 0x1dc, 0x1e0, 0x1e4) | every puppeteer tick (about 100 ms) and ALWAYS right before a frame whose last sync is older than 250 ms | 4 SEH-guarded reads of R; if R is not Sv/Cl (vtable check) skip and leave the old values | CERTAIN fields |
| money (S2+0x150+4i) | every tick from the ledger `klbf_ob[]` (bots) and from S Sharable+Unsharable for the host human at record 0 (S `+0x188`/`+0x224`, seat of the host) | `kbr_money_row()` pure | CERTAIN |
| status flags (0x1d4+4i) | never copied from R (they are W-owned: only the DLL grab table writes 0x2000) | -- | CERTAIN |
| record 0 `+0x10` (boarded) | every tick: 4 when the host human is on the van (the existing `OnlineBoardAll` / S CustomFlags bit 0x40 "escaped" test, `online_round_data.md` 41-42), else 0 | one byte | CERTAIN field; source bit GUESS-free (flag 0x40 is "escaped") |
| level | at round start and when the round counter changes | one byte | GUESS (derivation) |
| shadow teardown | state leaves 0x19 (`0x8e6a20(sm) != 0x19`), map change, or `OnlineBrain*` all off: free every grab table entry, zero `34c`, keep the block | no pointer from the engine into W survives the frame (the frame writes `[G+0x54]` back) | CERTAIN |

Evaluate cadence: the engine already calls EVALUATE about every AI tick for each of the 3 tactics on each soldier; the frame costs two writes and a try/finally. Run is only
called while the tactic is selected. Measure with `[Brain] Probe=1` frame counter (the plan's bench) before enabling for all 11 bots.

## 4. The swap frame for EVALUATE, RUN, EXIT of all three tactics

One wrapper per (tactic, slot). All are `__fastcall(self, edx)`; the original is `org[id]` saved when the vtable copy is built (`klbr_org[]`). Slot 11 wrappers return the float (x87).

```
float __fastcall ev(DWORD self, DWORD edx)            void __fastcall run(DWORD self, DWORD edx)
  if (!frame_wanted(self)) return 0.0f (ev) / return (run)     // see 'frame_wanted'
  if (reentry) return org(self)  /* same-thread nesting: NOT allowed to swap again; see risks R3 */
  reentry = 1; sync_if_stale(); swap_in(); __try { r = org(self); } __finally { swap_out(); reentry = 0; }
```

`frame_wanted(self)`: the shadow exists, `[sm+0x5c]==4`, `[sm+0x70]==0x19` (round), the soldier of `[self+4]` is one of OUR assigned bots (its record index known), and the
per-tactic switch (below) is on. If not wanted the wrapper must NOT call the original (it would fault on a NULL rules in Board and on a wrong layout elsewhere); it returns the
inert value (EVAL 0.0 = "not wanted", RUN nothing).

| tactic | slot | original | frame? | what it needs from W | inert answer | mark |
|---|---|---|---|---|---|---|
| Loot | 11 EVAL | 0x451920 | YES (already in 1b) | `0x508ef0`=W, `0x78f470` record, vt[0x1c8] flags, vt[0x328] candidates (stub), `0x7fd930(+0x78)` stage, vt[0x12c] van state (3/4 -> not wanted) | 0.0 | CERTAIN |
| Loot | 2 RUN | 0x7bc7d0 | YES (new) | `0x508ef0`, `0x78f470`, vt[0x1c8] flags `&0x2000`; tactic fields `+0x14..+0x2c` hold the candidates; rest is pathing | return | CERTAIN |
| Loot | 3 EXIT | 0x66b570 (bare ret) | NO, pass-through | -- | -- | CERTAIN |
| Board | 11 EVAL | 0x4faf60 | YES (new, stage 2 switch `OnlineBrainBoard`) | `0x508ef0`, vt[0x12c], (vt[0x130] in state 1/2), `0x5aeb00` | 0.0 | CERTAIN |
| Board | 2 RUN | 0x82f970 | YES | section 6 | return | CERTAIN |
| Board | 3 EXIT | 0x5478e0 | YES (fixes 0.3; do it in stage 1c as a bugfix even with Board off, by installing a plain-`ret` replacement while the shadow is off) | `0x508ef0` non-null, vt[0x2f4] | return | CERTAIN |
| Traitor | 11 EVAL | 0x79b7c0 | YES (`OnlineBrainTraitor`) | `0x7f6850`, S2 `+0x45`, `+0x150+4i`, vt[0xe0], 0x46d4d0, 0x43ffb0 (advances `[[0xdd2640]+0xb30]`, the game LCG: consumes one random number per EVAL, same as Arcade) | 0.0 | CERTAIN reads; the rest of the EVAL body not read (open item 11.3) |
| Traitor | 2 RUN | 0x488eb0 | YES | `0x508ef0`, `0x7fd930(+0x14 slot)`, `0x4322f0` | return | CERTAIN |
| Traitor | 3 EXIT | 0x66b570 | NO | -- | -- | CERTAIN |

The vtable copy: today `klbr_make_vtables` overrides 2/3/11 with the naked `KLBR_STUB` tail jumps (slot 2 un-swapped). Stage 2 replaces the slot-2 and slot-11 entries by the
C wrappers above (naked stubs only remain for slot 3 of Loot and Traitor, and only to keep the ids; they could just be left original). Because the wrappers are plain
`__fastcall` C, no stack-argument copying is needed (0.1).

Per-tactic switches in `klbrain_logic.h`: `kbr_switches2(probe, build, loot, board, traitor, bridge, puppet, out)`: Board needs Build; Traitor needs Build + Bridge; Bridge needs
Loot; PuppetOff needs Loot (+ Bridge for the money to count). Pure, tested.

## 5. Loot taken by a bot becomes real online loot

### 5.1 The decision

Option A (rejected): run Arcade's own tick 0x727cb0 in a frame. It pays into `[S2+0x150]` only (a shadow field, not a score object), and it calls HUD functions on the
global `[0x168e958]` (0x4d1380 / 0x862e70 / 0x8a7020) with the bot's seat index, and its state-0/3 branches read the local player. Risky and still needs a bridge. CERTAIN reading.

Option B (chosen): the DLL owns the grab. It reuses what the puppeteer already does (klbotfill grab substitute around the `0x4e3f40` call, OnlineBank, `klbf_ob[].tally`,
OnlineBankCredit `0x5a18c0`), but the START now comes from the real Loot tactic walking, and the BOT state lives on the shadow record so the real EVAL/RUN see "busy looting".

### 5.2 Slot 202 stub (candidate collector) on W

`DWORD __fastcall brain_s202(DWORD rules /*W*/, DWORD edx, const float *pos, DWORD *out)` with `ret 8` semantics (the compiler's `__fastcall` with 2 stack args does `ret 8`: CERTAIN
match for 0x8b94d0). Behaviour:
1. Iterate the real registry (`klonline_read.c` loot registry scan: base `0xe09e38`, count `0xe0e63c`; 0x451c30 zeroes the count at level start; stride GUESS, reuse the already-working `klonline_read` scan).
2. Keep an object when: not taken (`0x4536e0` false; or `+0x34 > 0`), `+0x6c` in play, `+0x64 == 1` state "ready", `+0x38 != 1` (skip DROP when the Arcade tuning window would, as the Heist original does through the window values), `+0x5c == 0` OR a KickDoor opened (use the original rule: pass 0x454c20 the same way EVAL does later at 0x451b57, so keep only the first filter here and let EVAL's own `+0x5c` check apply), within the tuning window `[0x168d7c0]+0xc1c..c28` of `pos` (read with SEH guard).
3. Sort by squared distance to `pos` (the same comparator), write <= 5 pointers to `out[0..4]`, zero the rest.
4. Return (no value used).
Mark: arg roles CERTAIN (0.6); registry stride GUESS (verify by logging count vs the klbotfill scan in the Probe line before enabling).

### 5.3 The DLL grab table (replaces slot 201 + the tick)

Table `kbr_grab[12]`: `{ ctrl, timer, started, seat }`. State is mirrored into the shadow record so the real code sees it: `rec+0x15=1`, `rec+0x1c=ctrl`, `rec+0x18=timer`, flag `0x2000` in `S2+0x1d4+4*seat`.

Start (`kbr_grab_start(seat, ctrl)`), called from the bot-trigger check, once per bot per ctrl:
- precondition (pure `kbr_grab_ok(state, round_state, hidden, ctrl_state, active, taken, bot_alive)`): `rec+0x15 == 0`, session state 0x19, ctrl `+0x64 == 1`, ctrl `+0x74` active (byte), node not hidden (entity flag 0x400), `+0x34 > 0`, `+0x80` bit free. CERTAIN (these are 0x6cdb40's own gates, `bots_loot.md` 66).
- effect (mirrors 0x8e8750 exactly): `rec+0x15=1`, `rec+0x1c=ctrl`, `rec+0x18 = [ctrl+0x44] * tune(0x4f3e50)` (the same product at 0x8e87b3..0x8e87cc; the multiplier call is made with the REAL G, tuning is global), flag |= 0x2000. If state is 2 with the same ctrl: back to 1 (0x8e8775). CERTAIN.
- where the trigger comes from: the DLL tests proximity itself (the same ball as ZTriggerBox2 radius mode: field 2 + 40 around the ctrl node centre, `bots_loot.md` 64; the klbotfill substitute already has this test) for bots whose real Loot tactic currently has `[tactic+0x28] == ctrl` (the EVAL chose it) so the DLL never grabs something the brain did not pick. GUESS: `[tactic+0x28]` is the chosen pointer (0x451b94 stores `eax` at `[ecx+0x28]`, `esi` index at `+0x2c`; CERTAIN stores, role GUESS-free by RUN's use).

Tick (every puppeteer tick, per active entry; pure `kbr_grab_step(timer, dt, inside, alive)` -> {keep, pay, abort}):
- abort (state reset: `rec+0x15=0`, flag 0x2000 cleared, ctrl `+0x80` bit cleared) when: ctrl taken, ctrl `+0x64 != 1`, bot dead (`[actor+0x576] != 1`, as 0x727f82..), bot left the ball for more than one tick (Arcade state 2 rule, `bots_loot.md` 69).
- else timer -= dt; ctrl `+0x80 |= 1<<seat`.
- when timer <= 0: `part = min([ctrl+0x40], remaining)`, remaining from `0x74da10(ctrl)`; call REAL `0x4e3f40(ctrl, part)` (`thiscall ecx=ctrl, push part`, `ret 4`; it already does nothing while the ctrl state is 2/3; CERTAIN; the klbotfill substitute already calls it) ; credit the ledger `klbf_ob[bot].tally += part` (the loot bar sums Sharable+Unsharable over seats, so the ctrl depletion is what the HUD bar sees; the ledger is what the round-end screen/"bank" shows via OnlineBank/OnlineBankCredit); mirror the shadow money `S2+0x150+4*seat += part`; `rec+0x38 += part/5`; timer = `[ctrl+0x44]*tune`. If ctrl is now empty: DROP stack goes back to its pool through `0x57f320(rules, ctrl)` ONLY for type 1 (DROP) and only with the REAL rules R (CERTAIN call shape 0x728165; online R is a different class, so GUESS that 0x57f320 is safe on R: the klbotfill substitute does not call it today, leave DROP out in stage 2, see risk R9), clear 0x2000, state 0.
- The 0x4e3f40 and ledger writes are on the real objects; the shadow only gets copies. If `0x4e3f40` faults (SEH guard) the grab is aborted and the bot is released.

How it becomes REAL loot online, per layer: (1) the ctrl's remaining amount goes down by the real function, so every client's loot bar and the ctrl's HUD marker update through the normal replication of the ctrl; (2) the ledger `klbf_ob[].tally` is what OnlineBankCredit hands to the score object: `0x5a18c0(seat, amount)` needs a seat, bots have none, so the existing OnlineBank design (credit the host human's row, or the Unsharable row of the traitor-aware seat) stays unchanged: stage 2 does not change who is credited, it only changes who decides to grab. CERTAIN for calls; the credit policy is the existing one.

## 6. Board RUN reaches the van online

What RUN needs (shadow doc section 2, complete rules touch list): `W+0x1dc` (3 or 4 for the "go to the van" branch; 1/2 reaches vt[0x130] and `0x7bb2a0`), `W+0x1e4` and `W+0x1e0` for `0x5aeb00` and the position through `0x7b3020([[W+0x1e0]+4], out)`, record 0 `+0x10`, `0x78f470` for the bot's own record, and rules slot 45 (0xb4) when within 300 units (90000.0 squared) of the board position.

Steps:
1. Sync the four van fields from R each tick (0.8). The online van is called by the host's round logic (`[R+0x1dc]` 3 = waiting at the door, 4 = boarding), so the bot walks only when the real round says the van is there. CERTAIN.
2. `0x1e0/0x1e4`: if R's are non-null copy them; else use the klbotfill van trigger object and the vehicle that klbotfill reads at lines 1979-1984 (the same fields the puppeteer reads today for OnlineBoardAll). GUESS that `[[obj]+4]` is a node the position helper accepts; check with the Probe line.
3. Slot 45 (0xb4) of W is a DLL stub `void __fastcall brain_s45(DWORD rules, DWORD edx, DWORD seat_or_actor_arg)`: it must NOT run the Heist 0x6840a0 (it uses the Arcade vehicle/escape state of W). It does: mark the bot as boarded in the ledger (`klbf_ob[bot].phase = 3`, the same phase the existing `OnlineBoardAll` sets), set `rec+0x10 = 4` of the bot's shadow record, and request the real boarding rule on R through the existing `klmv_ally_reach` / OnlineBoardAll path (it calls the real online rule with the real rules). The argument layout of `0x74d7f0 -> vt[0xb4]` is `(G, idx)` -> the stub receives the seat index in a stack dword (0x74d7f0 passes it; ret size of 0xb4's original 0x6840a0 must be read before shipping the stub: GUESS `ret 4`; bench check: the stub must restore ESP by the same count, test by calling the original path on an Arcade run is impossible here, so verify the `ret N` of 0x6840a0 by `dasm.py 6840a0` when writing the stub).
4. With the puppeteer OnlineBoardAll still the source of truth for "bot is on the van", Board RUN only provides the walking. Stage 2's Board therefore is "walk by the real tactic, board by the existing OnlineBoardAll", which is the safe split (see `boardall_review_exe.md`). A pure real-brain boarding (stub 45 doing the real board) is stage 2b behind `OnlineBrainBoardReal`.
5. Record 0 `+0x10`: mirrored (section 3), otherwise Board RUN would pick the "hurry" order set (`0x8997a0`) wrongly. CERTAIN.

Switches: `OnlineBrainBoard` = Board EVAL/RUN/EXIT wrappers (walk only; boarding by the puppeteer); `OnlineBrainBoardReal` = stub 45 boards for real. Both default 0.

## 7. PuppetOff: handing steering to the real tactic and back

Today (`kbr_puppet_released`): the puppeteer leaves a soldier alone only while the REAL Loot EVAL returned > 0 within `win_ms`. Stage 2 generalises it to a per-bot, per-tactic hand-off:

| tactic | the real tactic steers when | the puppeteer takes back when | mark |
|---|---|---|---|
| Loot | EVAL returned > 0 within `LootWinMs` (default 1500) AND `[tactic+0x28]` non-null | EVAL 0 for the whole window, grab abort with no candidate, van state 3/4 | CERTAIN logic; window GUESS (bench) |
| Board | van state in {3,4} on R AND Board EVAL > 0 within `BoardWinMs` | bot far (> 300 units) AND no path (RUN returned with no order for 2 s: `!0x55b9f0(tactic)` ) | CERTAIN fields; windows GUESS |
| Traitor | never steers (it only flips a flag) | -- | CERTAIN (RUN sets a flag) |

`kbr_hand(st, now, nz_loot, nz_board, van, windows...)` -> `{loot_real, board_real}` is pure (extends `kbr_puppet_released`). A bot with `loot_real` has the puppeteer's loot walking and grab substitute skipped (`klbr_puppet_off` already exists at klbotfill line 2046; extend its argument by the tactic mask). Rule: at most ONE steerer per soldier at any time; the puppeteer's order push (`0x521350` equivalent) is skipped for a real-steered soldier, so no two orders fight. When a hand-back happens the puppeteer re-issues its own goal on the next tick (it is stateless per tick today: GUESS, verify in `klbf_ot_run`).

## 8. Stage 3: traitor and bot-triggered cops, as far as the contract allows

### 8.1 Traitor (`OnlineBrainTraitor`, needs Build + Bridge)

What the contract proves: the Traitor tactic decides (EVAL: roll 0x43ffb0 gated by `[W+0x338] < tuning limit` and by money/level), then RUN does `rec+0x79 |= 2` and the
odd 0x4322f0. The decision cadence needs a stable W+0x5f8 level and money row.
What it does online (what is NOT in the contract): a traitor must (a) change team for the AI (`[[actor+0x54]+4]`, Ally 2 -> Enemy), (b) stop being credited as a crew thief and be hunted, (c) announce
(`AnnounceFATraitor`, netcode.md). None of these is done by RUN. Stage 3a therefore only MIRRORS: after RUN, if `rec+0x79 & 2` for a bot, call the existing online traitor path of the puppeteer (klbotfill traitor logic; the old puppet roll becomes the real roll) — the bot's hostility and the announce stay the puppeteer's job. CERTAIN that RUN only sets a bit; GUESS that nothing else in Arcade reads it before the next round; the bit is read by `rec+0x79` consumers `0x6ae750`-class voice code only.
Rules: the roll consumes the game LCG once per EVAL; at 11 bots x EVAL rate this changes the sequence of every other random user (hit chance, spawn). To keep Arcade's cadence EVAL is called at the engine rate; the sync of the 11 records is cheap. Risk R7.
Switches: `OnlineBrainTraitor` default 0, label "(recommended off)".

### 8.2 Bot-triggered cops

Status: the existing `OnlineTriggers` fires `0x6ae730` from the puppeteer when a bot is inside a cop trigger; the census fix (`f38a0d145`) counts NEW cops per bot-fired trigger and tp3 still showed 0 new cops. Contract limit: Arcade fires cops through the ZTriggerBox2 `AI_TRIGGER_WITH_ACTIVATOR` message with the bot as activator and the cop gates (`0x5dd890` stage, `0x8d2740` kinds 1/2/3, shadow doc section 5 "open"). In the frame, the same box path would work for bots (0x7f6850 true) but frames last one tactic call, not the trigger update. So the contract does NOT cover cops: a bot must be inside the box during the box's own update, which runs outside any frame.
What stage 3b does within the contract: while a bot's brain is steered by the real Loot/Board tactic and the DLL sees the bot inside a cop trigger's ball, the DLL calls the same function the box calls, `0x5dd890(R, rec_idx, stage)`-equivalent on the SHADOW crew table (`SetStage(activator, n)` = `rec+0x78 = max(rec+0x78, n)`) and then fires the gate with the REAL `0x6ae730` (existing). This needs 0x8d2740 read first (open item 11.2). Deliver as research + a probe line (`[Brain] CopProbe`) before any behaviour; no code.
Switch: `OnlineBrainCops` default 0.

## 9. ini keys, options rows, tests (all default 0, "(recommended off)")

| key (section `[Brain]`) | default | depends on | label (kl_mod_options) | KLHook.ini line |
|---|---|---|---|---|
| `OnlineBrainBridge` | 0 | Loot | "AI loot through the real brain (recommended off)" | `OnlineBrainBridge=0` |
| `OnlineBrainBoard` | 0 | Build | "AI van walk by the real brain (recommended off)" | `OnlineBrainBoard=0` |
| `OnlineBrainBoardReal` | 0 | Board | "AI boarding by the real brain (recommended off)" | `OnlineBrainBoardReal=0` |
| `OnlineBrainTraitor` | 0 | Build + Bridge | "AI traitor roll by the real brain (recommended off)" | `OnlineBrainTraitor=0` |
| `OnlineBrainCops` | 0 | Bridge | "AI cop triggers by the real brain (recommended off)" | `OnlineBrainCops=0` |
| `OnlineBrainLevel` | 6 | Traitor | "Brain level for the traitor roll" (value row, 1..11) | `OnlineBrainLevel=6` |
| `LootWinMs` / `BoardWinMs` | 1500 / 2000 | -- | (value rows) | same names |

Pure additions to `klbrain_logic.h`: `kbr_switches2`, `kbr_sync_plan`, `kbr_money_row`, `kbr_grab_ok`, `kbr_grab_step`, `kbr_hand`, `kbr_level_clamp`, `kbr_board_state_ok`, `kbr_cand_sort` (keep 5 nearest from a plain array).
New tests in `klbrain_test.c` (already registered in `tools/kl_tests.py` C_TESTS; extend, do not add a new file): dependency chain truth table; grab_step for timer / inside / dead / abort; money_row; hand-off with wraparound `GetTickCount`; cand_sort ties and < 5; level clamp.

## 10. Crash risks and their guards

| # | risk | why (evidence) | guard |
|---|---|---|---|
| R1 | Board EXIT called outside a frame (current stub) | 0.3: `0x508ef0` NULL online, `mov edx,[eax]` | frame or inert replacement in stage 1c; wrapper never calls the original when the shadow is off |
| R2 | any original called with `[G+0x54]` = Sv/Cl layout | `0x7bb2a0` has no role test and returns the online rules object | ALL tactic originals inside the frame (shadow doc rule); the wrapper returns inert when the frame is not wanted |
| R3 | re-entry: a tactic call inside a frame calls another tactic (Loot RUN -> ... -> engine pushes an order that evaluates a tactic) | recursion would save `sv = shadow` and restore the wrong value | per-thread depth counter; nested call runs the original WITHOUT a second swap; `swap_out` restores the values captured at the OUTERMOST `swap_in` only |
| R4 | exception in the original leaves `[sm+0x54]` / `[G+0x54]` swapped | engine continues with role 0 = Arcade host | `__try/__finally` restore (exists); `klbr_swap_out` verifies the restore (re-read) and logs |
| R5 | frame on a non-game thread | rules writes by the swap are visible to other threads (audio, net) | wrappers check `GetCurrentThreadId() == game thread` (stored when the first stub runs on the game thread); otherwise return inert |
| R6 | network thread reads role/rules during a frame | role 0 visible for the duration of one tactic call only | frame is a few microseconds; no `Sleep`/IO inside; the Probe line counts max frame time and gates the switch off above a limit |
| R7 | LCG consumption of Traitor EVAL changes gameplay randomness | 0x43ffb0 advances `[[0xdd2640]+0xb30]` | only with `OnlineBrainTraitor`; and only for bots; the sequence is the game's own anyway |
| R8 | stale pointers in W (`rec+4`, `rec+0x1c`, `+0x1e0/+0x1e4`) after a bot dies / ctrl is destroyed | engine frees entities | re-validate `rec+4` each sync (vtable check 0xbb3bac); `rec+0x1c` ctrl re-validated by registry membership before `0x4e3f40`; zero all pointers on state != 0x19 |
| R9 | DROP stack return `0x57f320` on the online rules | different class; not exercised online | not called in stage 2; DROP ctrls (type 1) are skipped by the slot-202 stub |
| R10 | `0x4e3f40` on a ctrl in state 2/3 | it is a no-op in those states (0x4e3f40 gate) | additionally check `+0x64 == 1` before each part |
| R11 | HUD calls on `[0x168e958]` with bot seats | 0x727cb0 does this | the DLL never runs 0x727cb0 (option B) |
| R12 | the `0x5aeb00` / `0x7b3020` position helper on a bad `[W+0x1e0]+4` | no null test after the first check | only copy `+0x1e0/+0x1e4` when both pass a vtable/readable check; otherwise leave 0 so `0x5aeb00` returns false and Board RUN returns |
| R13 | slot 45 stub with wrong `ret N` | stack imbalance = crash on return | read `ret` of 0x6840a0 before writing; keep the stub as `__fastcall` with exactly N stack dwords; unit-check against the original's N in `dasm`-derived constant |
| R14 | shadow vtable copy slot count | 256 dwords copied; slot 0x328/4 = 202, 0x324/4 = 201, 0xb4/4 = 45 are inside | assert each replaced index < 256 at init |
| R15 | memory ordering / the CEG | none of the above patches `.text` | only `VirtualAlloc` blocks, DLL vtable copies, existing `klbr_org` pointers; the soldier vector insertion (stage 1a) already writes heap |
| R16 | sort stub returns fewer than 5 | EVAL stops at the first null (0x451a41 `cmp [edi],ebx; je`) | zero-fill the tail |

## 11. Bench plan (no game launch from this document)

Offline now: `python tools/kl_tests.py` (new pure tests), `python tools/kl_mod_options_test.py` (rows + ini lines), `dasm.py` of 0x6840a0 (R13), 0x8d2740, 0x79b7c0 full (11.3), 0x5aeb00 / 0x7b3020 (R12).
Live, when the PC is free (never during br1): kits in this order, each 21 maps both seats per the q35 pattern, `Probe=1` on:
1. `brain-s1c`: Board EXIT fix only. PASS = 0 asserts, Board popped once without fault.
2. `brain-s2a`: `OnlineBrainBridge=1`, PuppetOff on for Loot. PASS = bots walk to ctrls chosen by the real EVAL, `kbr_grab` parts paid, loot bar grows, 0 asserts, exit clean.
3. `brain-s2b`: + `OnlineBrainBoard=1`. PASS = bots walk to the van at state 3/4 and OnlineBoardAll boards them; RT9A/B-style exit times unchanged.
4. `brain-s2c`: `OnlineBrainBoardReal=1`. PASS = same without the puppeteer's boarding.
5. `brain-s3a`: `OnlineBrainTraitor=1`, host-only, 3 rounds. PASS = at most the tuned rate of traitors; no extra crashes.
6. `brain-s3b`: cops probe only.
Metrics logged by Probe: frame count per second, max frame microseconds, EVAL > 0 count per bot, grab parts paid, hand-off flips.

## 12. Open items (not read in this pass)

1. `0x6840a0` ret size and body (R13); `0x74d7f0`.
2. `0x8d2740` (the three gameplay trigger callers of `0x5dd890`) for the cop contract.
3. Traitor EVAL `0x79b7c0` in full (rules reads after the roll; only the `0x46d4d0` and `0x43ffb0` calls are certain).
4. The garbled lea at 0x451a1c: confirm candidate array = `tactic+0x14`.
5. Registry stride at `0xe09e38` for the slot-202 stub (reuse `klonline_read`'s scan).
6. Whether `[R+0x1e0]` / `[R+0x1e4]` are populated on Sv/Cl before the van arrives (Probe line).

## 13. Order of work

1. (S1c) Board EXIT safe: frame-or-inert; test; ship with Board off.
2. `klbrain_logic.h` pure functions + tests (section 9).
3. Crew assign + sync + level + van mirror + record 0 + EVAL/RUN wrappers for Loot (Bridge off still runs EVAL as today).
4. Slot 202 stub + DLL grab table + payout; PuppetOff per tactic; kit s2a.
5. Board EVAL/RUN/EXIT wrappers; van fields; kit s2b; then slot 45 stub; kit s2c.
6. Traitor EVAL/RUN; kit s3a. Cops probe, no behaviour, kit s3b.
Every step: ini key default 0, "(recommended off)", options row, KLHook.ini line, `kl_tests.py` green, commit message says what crashed and why when something did.
