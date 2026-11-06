# Online grudge: a human who kills an AI heister becomes the traitor (2026-11-06)

Static research + an off-by-default implementation. NOT run live. Every GUESS is marked.

## 1. What stock does (human on human)
- Sv slot 11 (0x46bd40) calls the reward/kill routine 0x794190 (this = rules). It derives the killer client index from the attacker ZFFPlayer
  (`klud_idx`: `[body+0x2748]` -> byte `[c+0xdc] ^ 0xac`) and the victim index from the victim player, then calls **Sv slot 129 = 0x41d480 (killerIdx, victimIdx)**
  (`call [vt+0x204]` at 0x794af0 and 0x794d09).
- Slot 129: returns if session state is 0x1f or `flags(killer) & 0xc` (dead/police); announce block (0x426cd0 RMCAnnounceFATraitor) only when the victim index is valid;
  sets flag 1 (vt+0x1cc); RMCSetTraitor(1) (0x4f2f70) on `[player+0x380]`, the network carrier; RMCSetPrevRoundTraitor(1) (0x6899b0); then a penalty/clamp block that
  reads an array at `[score+0x58 + idx*4 + 0x130]` via 0x699030 (harmless for -1).
- Client flags dword (vt+0x1c8): 1 traitor, 4 dead, 8 police, 0x40 escaped, 0x80 undercover.

## 2. Why a bot kill never reaches it
An AI heister has no ZFFPlayer client record, so 0x794190 never gets a victim index and never calls slot 129. The old log claim "not feasible (Arcade-only hit
attribution)" is only half right: the decision routine is not fed, but the attribution exists on the host.

## 3. Attribution (the host)
- Bot last aggressor: `[soldier+0x708]` (entity) + `[soldier+0x70c]` (stamp), valid while `clock < stamp`, clock = `[[0xdd2640]+0x48]`. Soldier = `[actor+0x77c]`.
  Same fields klbrain.c HitLog reads (klbr_hl, `kbr_tgt_valid`).
- Human test: the aggressor vtable is ZFFPlayer (0xbb45f4, `klh_pvt`) AND `klbr_rec_member(body)` = 1 (body is the player of a used rules record = a session seat;
  AI heisters have no record). Client index = `klud_idx(body)`.
- Rules slot-15 damage hook (`klud_w15`): TRIED FIRST, WRONG. Static RE (skeptic-confirmed): slot 15 (forwarder 0x83ad70, sole caller 0x6e3471 inside 0x6e3400) is ZFFPlayer-only and never runs for an AI heister. The call site in klucc_down.c and `kly_og_hit` are removed (fix 1106b, below).
- GUESS: on the host a remote client's hit sets `[soldier+0x708]` to that client's puppet ZFFPlayer (the one with a record). If it is not set, the log line
  "died, no human aggressor" shows it.

## 4. Implementation (klhook/klgrudge.c `kly_og_*`, logic klogrudge_logic.h, test klogrudge_test.c)
- `[Bots] OnlineGrudge=0` (default off, own key, needs no `[Bots] Enable`); `OnlineGrudgeDry=1` logs only.
- Host-only: `klbd_online_view(3,...)` census (host in a round) gives the AI pseudo-records; polled every 250 ms on the game thread.
- While a bot lives a fresh human aggressor is LATCHED (index + tick). When the record turns dead (status 7) the latch (<= 4000 ms old, GUESS) or a still-fresh
  aggressor is the killer. Once per death. Eligible only if the killer is not already traitor/dead/police/escaped.
- Fire: `((void(__fastcall*)(void*,void*,int,int))[vt+0x204])(rules, 0, killer, -1)` inside `__try/__except`; first checks the slot still equals 0x41d480 (else logs, no call).
- GUESSES: victim -1 is accepted (skips the announce; the penalty block reads index -1 harmlessly - read from disassembly, not run); the client UI shows the traitor
  state from RMCSetTraitor without the announce; the 250 ms poll and 4 s window catch the killing blow; status 7 means dead for pseudo-records.

## 5. Crash risks
- Slot 129 with victim -1: the 0x699030 array read at `idx*4+0x130` with -1 is a negative offset into a valid score object (no fault expected). A fault is caught
  (`__except`) and the feature switches itself off for the session.
- Stale `rules`/vtable: guarded by the slot-pointer check and by re-reading rules each poll.
- Calling on a non-host: impossible by construction (census returns 0 unless host in round).

## 6. Why online AI heisters may still not betray humans (c9, 11-04/11-05; traitor_*_1103 notes)
The bot-turns-traitor work is separate: it needs the bot's brain to pick a human target (`klbr` traitor target / `kbr_tgt_valid`) and the handoff/cap rules
(traitor_target_holder, traitor_handoff, traitor_cap). Likely gaps: the bot's last aggressor is often a cop or nobody (class not human), the target holder is
cleared on round change, and the cap (one traitor at a time) blocks a second turn. Summary only; not built here.

## 7. First live bench: grep KLHook.log for
`OnlineGrudge on`, `online grudge: new round`, `online grudge: human N killed an AI heister`, `no human aggressor` (attribution guess wrong),
`not eligible`, `slot 129 is`, `faulted`. Run with `OnlineGrudgeDry=1` first; then check the client shows the traitor state.

## 8. Review fixes (2026-11-06, three reviewers; each checked against the code / kl2.exe)
Offline only, NOT run live, default 0. `[Bots] OnlineGrudge`, `OnlineGrudgeDry`. Files: `klgrudge.c` (kog_w_hit, private ZSoldier table), `klhook.c` (klh_soldier_og, mapped in klh_svt), `klbrain.c` (klbr_was_traitor_actor, klbr_traitor_bots read only; the traitor-arcade vtable check also accepts our table), `klogrudge_logic.h` (kgo_hurt, kgo_lethal).

1. **Wrong object (fixed).** `s.rules` of klbd_online_view is the SESSION manager ([0x168e598], vtable 0xbd1ebc). The real rules = `[[0x168e9e4] + 0x54]` (`kog_rules`, checked with KLH_RULES_SV_OK). Slot 129, `klud_flags` and the used-seat test use it; `s.rules` is only the round key.
2. **Victim role (fixed).** Skipped when `klbr_was_traitor_actor` (marked by OnlineBrainTraitorArcade, or turned by TraitorTurn: klbr_tt keeps the actor after the team is restored) or when the team `[[actor+0x54]+4]` is not 2 (Ally; police, fed, a turned bot on Enemy). Log `victim was a traitor: no mark`.
3. **Attribution (REWRITTEN fix 1106b: the earlier text claiming the killer comes from the slot-15 lethal blow was wrong, slot 15 never runs for a bot).** Best first: the LETHAL blow seen at the soldier hit handler. HOOK: ZSoldier slot 96 = vtable 0xbd0954 (+0x180, table entry 0xbd0ad4, verified = 0x8473a0), thiscall, ecx = soldier, one stack arg = hit record (attacker actor `[hit+0]`, hit type `[hit+8]`), ret 4. Actor = `[soldier+0x40]`; health `[[actor+0x5fc]+4]` with `[h+0x24]==actor`. The stock table is .rdata and a SHIP build writes data only (klh_may_write), so a PRIVATE copy of the table (128 slots; the class has 118, counted) carries slot 96 = `kog_w_hit`, and the tick points each TRACKED, living bot soldier at it (`[soldier+0]`, heap). `klh_svt` maps the copy back to 0xbd0954 (`klh_soldier_og`, next to klbrain.c's `klh_soldier_priv`), so every soldier-class test still passes. Put back (stock pointer) at a round end / when the bot leaves the census / when the sub-mode is not FA. A soldier already on klbrain.c's table is left alone (log once; a traitor bot is no victim here); klbrain.c may take a soldier over from our table (its check accepts it; its restore writes the stock one, the next tick swaps again). The wrapper reads hp0, calls the original, reads hp1; `kgo_lethal` = hp0 > 0.01 and hp1 <= 0; `kgo_hurt` = hp1 < hp0 (a hit that took nothing is ignored). The attacker goes through `kog_human` (ZFFPlayer vtable AND a used rules record) and `kgo_after_hit` updates `lw[i]`; a lethal hit stamps `lw_at[i]`. Only tracked bots, the feature on, an FA sub-mode round and the tick's game thread do any work; everything else is a straight pass-through. DRY (`OnlineGrudgeDry=1`) logs the first 8 hits on tracked bots (attacker, its vtable, human verdict, hit type, hp0 -> hp1) and still never calls slot 129. Fallback: a fresh human stamp `[soldier+0x708]` AT the death poll, refused when a non-human hit was seen in the last 4 s (hook or fresh non-human stamp), when a lethal blow by a non-human was seen, or when the stamp differs from the last alive poll. The 4 s "latch" alone is no longer a killer; a fresh non-human aggressor clears it. GUESSES: (1) the original handler has written the damage when it returns (it computes health at 0x847785..0x847795 and writes it through actor vt+0x670 at 0x84789d); if not, hp1 == hp0 and the log says "no health taken: ... completion not synchronous" - then only the stamp fallback works; (2) `[hit+0]` is the attacker's ZFFPlayer body itself (the first logged hits show the vtable; 0xbb45f4 expected); (3) no direct call of 0x8473a0 bypasses the vtable (the caller search found none); (4) 0x8473a0 returns nothing meaningful (eax passed through anyway); (5) one soldier-table copy is enough: the 118-slot class never calls past slot 127.
4. **Undercover (fixed).** `KGO_F_UNDERCOVER 0x80` is in the ineligible mask (stock 0x794a9b `test al,al; js` sends him down the other path), test case added.
5. **Stock tail (disassembled 0x794a7d..0x794b5d and the 0x794cd9 twin).** Order in stock: [slot 114 flags(killer) js -> other path] [flags(victim)&8] [flags(victim)&1] [flags(victim) js] [slot 122 = 0x8fe8c0(killer, victim): victim flags & 0x400 ...; nonzero -> reward-only path 0x794b14] then **slot 129 (killer, victim)**, **slot 105 = 0x42e510 (killer)**, `inc [rules+0x36c]`, then (0x794b2d) `flags(victim) js -> end`, **slot 132 = 0x64c650** `jl -> end`, **0x4569b0** (round-over check).
   - Replicated (inside the same __try, killer validated: used seat, flags eligible): slot 105 (0x42e510, `ret 4`, checks `[rules+0x205]` and the used byte, recomputes the killer's state byte `[rec+0xe]` from score reads 0x571750 / 0x699030; killer only, no victim). It is skipped (logged) when the slot is not 0x42e510.
   - NOT replicated: slot 122 (needs a victim seat), `inc [rules+0x36c]` (that dword is the first word of the ZHeistScore per re/hud_values.md; the increment looks like a stock counter on another object but I could not resolve it, so not touched), the victim-flag test, slot 132 and 0x4569b0 (round-over evaluation after a SEAT died; no seat died, and 0x4569b0 sets `[rules+0x282]`). Parity with stock is therefore partial: the killer ends up traitor and refreshed, the round-over bookkeeping is not run.
6. **Death detection (fixed).** `done` is a set of actor addresses for the whole round (64, oldest evicted): no second fire on a reused record slot. A bot first seen already dead (status 7) is booked and never fires (`first seen already dead`). A record dropping from the census while latched logs `AI heister left the census with a human latch`.
7. **Policy.** A human made traitor here does NOT count toward `OnlineBrainTraitorMax` (that cap counts klbr marks only). After a fire the log says `traitors now: bots %d human %d` (bots = klbr_t marks + klbr_tt turned; humans = rules flag bit 1, read for every used seat).
8. **GUESSES kept.** Victim -1 skips RMCAnnounceFATraitor (0x426cd0) and the 5 s timer, so the clients probably get no announce; RMCSetTraitor is sent inside slot 129 (0x4f2f70 at 0x41d5b9, if `[player+0x378]`). GUESS. Also with victim -1: 0x625be0(-1) returns 0xffffffff (all flag bits), so 0x7b2b20(victim) picks its "victim was a traitor" row (0xb362c8), and the read at 0x41d6e0 (0x699030 -> 0x8d1ec0 `[score+0x58+idx*4+0x130]`, `movsx` of -1) goes 4 bytes below the array start into the score object: it only feeds the killer's clamp byte `[rec+0x31]` (0x41d7d8), harmless but it is a changed value (a traitor-class penalty row for a bot kill). Not run.
9. **Re-verify fixes (2026-11-06, second pass).** (a) FA proper only: sub-mode `[0x168e59c]` must be 0 (`kgo_submode_ok`); UCC (1) / C&R (2) log `sub-mode ... not Fragile Alliance (0): off this round` once per round and the hit hook idles. (b) A NON-lethal non-human hit clears a human's earlier predicted lethal blow (`kgo_after_hit`): the bot lived, so a cop finishing him within 3 s no longer blames the human (test "cop kills after a human tag"). (c) `kog_rules` refuses the brain's shadow rules block, and the tick skips while a swap frame / thunk slice is open (`klbr_og_rules_busy`). (d) `kog_w_hit` acts only on the tick's game thread (own `kog_.tid`; `klbr_game_tid` is set only when the brain is on). Also to check in the DRY bench: victim -1 = score-feed text "Traitor" and the "victim was a traitor" penalty row (money effect unknown).

### Exact DRY-bench log lines (`OnlineGrudge=1`, `OnlineGrudgeDry=1`, grep `online grudge`)
- `grudge: OnlineGrudge on (dry log): HOST only; ...`
- `grudge: online grudge: new round, online host`
- `grudge: online grudge: private ZSoldier table ... made (slot 96 ...)` once; absent + `ZSoldier slot 96 reads ..., not 0x8473a0: the hit hook is OFF` = exe differs
- `grudge: online grudge: AI heister I soldier S has vtable V (klbrain.c's private table?), not the stock one: its hits are NOT seen` (once per bot)
- `grudge: online grudge dry: hit #N on AI heister I (actor A): attacker B vtable V (HUMAN | WHY), hit type T, health H0 -> H1 [LETHAL | (no health taken...)]` (first 8), then `lethal blow on AI heister I (actor A, health H0 -> H1): attacker B vtable V: HUMAN` or `...: vtable check: not a ZFFPlayer` / `rules-record check: ZFFPlayer without a seat` / `rules-record check: walk unavailable (treated as not human)` / `client index out of range`
- `grudge: online grudge dry: AI heister I (actor A) died: lethal blow human|NOT human|none (N ms), stamp human|fresh, not human|none (WHY; target T vtable V rec-member R, valid N more ticks), last poll latch K, non-human hit N ms ago -> killer found|no human killer (HOW)`; HOW: 1 lethal blow, 2 non-human hit in the window, 3 lethal blow by a non-human, 4 no fresh human stamp, 5 stamp changed, 6 stamp at death
- `grudge: online grudge dry: would call slot 129 (killer K, victim -1), flags F, then slot 105`
- not eligible: `grudge: online grudge: AI heister I killed by client K, flags F: not eligible (traitor / dead / police / escaped / undercover)`
- skips: `victim was a traitor: no mark`, `team N is not Ally (police / fed / turned): no mark`, `first seen already dead: no mark`, `AI heister left the census with a human latch (record I, actor A, client K)`
- real run adds: `human K killed an AI heister: made traitor (slot 129 killer K victim -1, then slot 105), fire #N, flags F -> F2 (bit 1 = SET|NOT set)` and `traitors now: bots B human H (...)`; faults: `slot 129 / 105 faulted (killer K): disabled`.
