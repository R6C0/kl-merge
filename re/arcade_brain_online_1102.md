# Arcade AI brain online + lobby map names: research and build plan (2026-11-02 ~22:40)

Owner 11-02 evening: online bots feel nothing like Arcade; maps listed wrong on the multiplayer screen. Workflow wf_7035f27d-510 (offline, read-only). Sections: plan, brain research, rules research, map-list research.

# Build plan: Arcade map names and Arcade AI brain in online FA

This is a plan only. Nothing was run, installed or patched. CERTAIN means read in disassembly or code. GUESS means inferred and needing a bench check. Every toggle name below is proposed, defaults to off, and is labelled "(recommended on/off)" in the options page. Pause live runs while the owner is playing.

## A. MAP LIST

### What is wrong (CERTAIN)
- The live `KLHook.ini` has no `[Names]` section, so Enable=0 and Override=0. The lobby shows the stock slot titles.
- The title key is `Menu/Online/Scenarios/Title%02i`, built from the slot. The LOC lookup is `[[[0xdd2640]+0xac]+0x94]`, vtable slot 0, which `kllocname.c` already wraps.
- With `OnlineSet=9` (random), `kllnm_name_now()` (`kllocname.c:129-165`) asks `kls_page_now()` and gets 9. `kls_find_rule(s, 9)` finds nothing and falls back to the page-0 rule, DD0x, which has no name. So even Override=1 would leave the stock title.
- The random pick is made only at load time, in `kls_rand_pick` (`klslot.c:342`, called at `:471`). It advances a round counter, so it must not be called from a text lookup.

### The fix, in three steps
1. **Ini for fixed sets** (works for `OnlineSet=2` or `3`; GUESS that the lobby re-asks the lookup when the slot changes):
   ```
   [Expansion]
   Enable=1
   [Names]
   Enable=1
   Override=1
   Log=1
   ```
   Every peer needs the same ini.
2. **Code for the random set.**
   - Where: in `kllnm_name_now()`, add a branch for `page == KLS_RANDOM` before the `kls_find_rule` call.
   - What it returns: a per-slot static label, "`<stock title> / <page2 name> / <page3 name>`". Examples are "Subway / Hot Coffee / Last Call" and "Docks / Late Night Opening / A Walk in the Park II". The stock title comes from the original lookup result.
   - Limits: the buffer is at most 47 characters, plain ASCII, no `%`, no leading `/`, as already enforced at `kllocname.c:285-290`. If the label is too long, fall back to "`<stock> / Dead Men`".
   - New ini key: `[Names] RandomLabel=1` (recommended on). Default 0 until tested.
   - Do not call `kls_rand_pick` here.
3. **Pictures** (data route, not hook code). `kl_lobbynames.py --set rand` makes the collage. The owner must install it, and it also affects Quick Match. Per-map pictures need a Patch01 change or the `[MapPool] Enable=1 Pool=n Overlay=1 OverlayDir=...` overlay (`klmappool_ov.c`, built, never run live). Do the names first, and the pictures only after the names are proven.

### Live check (two seats)
- Run Private Match → FA lobby with `OnlineSet=2`, then `OnlineSet=9`. Step slots F01 to F09 and screenshot the lobby on host and on client. Also screenshot the Arcade list and the search filter.
- Log line expected: `names: lookup ... Title01 -> '...' (OVERRIDDEN)`.
- **Pass:**
  - The client label equals the host label for every slot.
  - Quick Match still shows stock names.
  - There are 0 faults.
- If the label does not change after stepping slots, the lobby caches the text. Then find out which element reads it (focus element slot 24, `0x490730`) before coding more.

## B. ARCADE BRAIN ONLINE (staged)

### Premise
- Three tactic objects are built in the ZSoldier ctor (`0x6ab250`, branch `0x6ab56d..0x6ab66c`) only if `0x7f6850()` is true. Online hosts are role 2 or 3, so it is false.
- The ctors read no rules state (CERTAIN), so we can build the objects ourselves. The real obstacle is that every evaluate and run calls `0x508ef0(G)`, which returns NULL online, so evaluate returns 0.0.
- The tactics expect the Heist rules layout: crew table `+0x348` (stride 0x7c), van state `+0x1dc`, score block `+0x5f8`. The online Sv object is the wrong layout, so never hand it to tactic code (CERTAIN, crash risk).
- Key observation: Loot **run** (`0x7bc7d0`) touches the rules only through `0x508ef0`, `0x78f470` and `vt[0x1c8]&0x2000`. Most of it is pathing. This makes Loot the cheapest tactic to run for real.

### Stage 1: prove the objects exist and tick (no behaviour change)

**1a, construction only. Toggle `[BotFill] OnlineBrain=0|1`, default 0.**
- When: on the host, a soldier of team 2 (Ally) that is new. GUESS: no clean spawn event was found, so poll the soldier list on the host tick (the same place `klbotfill` already scans) and tag each soldier once.
- What to do:
  - Allocate with `0x89e850` (sizes 0x30, 0x14, 0x20).
  - Run ctors `0x68eab0(soldier)` for Loot and Board, and `0x51b7e0(soldier)` for Traitor.
  - Store the pointers at `[soldier+0x5f0]`, `+0x5f4` and `+0x5f8`.
  - Push them into the vectors at `+0x604` and `+0x610` with `0x403150`, in the ctor's order: Traitor, Board, ..., Loot last.
- Guard: the whole block sits in `__try`, and only runs when `+0x5f0` is still null. Never use the CRT heap for any of it.
- Give each object a DLL-owned vtable copy. Slot 0 stays the game's destructor (`0x4fe6f0`). Slots 2, 3 and 11 become logging wrappers that call the original, with no frame swap yet.
- **Pass:**
  - The log shows N constructions for N bots.
  - The wrapper's evaluate counter is above 0 (so ZDefendPosition at `0x85f8e2..0x85f933` is walking the list).
  - Every evaluate returns 0.0 as predicted, with 0 faults over a 10 minute 2-seat run on DM01 and DD05.
  - A kill and respawn of a bot does not crash the destructor.
- **Fail meaning:** a crash on the push means the vector layout guess is wrong. Compare against the ctor's exact push sequence at `0x6abcd4..0x6ac4d8`.

**1b, Loot only through a minimal shadow. Toggle `OnlineBrainLoot=0|1`.**
- Build a zeroed 0xf30 shadow rules block, with a private copy of vtable `0xbd3514`, and a 12-record crew table (stride 0x7c, in-use bytes, count, free count).
- Register each bot with one record: `+4` = soldier, `+0x79` bit 1, `+0x78` = 1 (stage), `+0x10` = 0.
- Wrap Loot evaluate (slot 11) and Loot run (slot 2) as follows:
  1. Save `[G+0x54]` and `[sm+0x54]`.
  2. Set `[G+0x54]` = shadow and `[sm+0x54]` = 0. The second makes `0x7f6850` return `[sm+0x5c]==4`.
  3. Call the original in `__try`.
  4. Restore both in `__finally`.
- Wrapper rules:
  - Host main thread only.
  - Assert on re-entry.
  - Never yield inside the frame.
  - The frame is one call wide.
- Fill the shadow vtable: keep the Heist originals for slots 75 (`0x12c`), 114 (`0x1c8`) and 56. Make slot 202 (`0x328`, loot candidates) a hook stub that returns candidates from the real online `ZOnlineMoneyCtrl` list. Stub unused slots to return 0 and log each hit.
- **Pass (behaviour, not just no crash):**
  - Bots walk to a money object by their own pathing, and stand in its trigger box.
  - Their choice is compared side by side with Arcade on the same map: do bots go for the same stacks, and in a similar order.
  - The puppeteer is OFF during this test, so any walking is the real run.
  - 0 faults.

### Stage 2: shadow crew records and bridging to online rules

**Toggle `OnlineBrainBoard`, `OnlineBrainBridge` (default 0).**
- Loot grab: the shadow slot 201 stub (`0x324`) replaces `0x56f6e0`. When the shadow record goes `+0x15` 0→1→taken, remove the real money object by the existing DropTake / Carry 8 path in `klbotfill.c` and add to `klbf_ob[bot].tally`. Money for a bot has no seat, so keep the existing OnlineBank and OnlineBankCredit ledger (via `0x5a18c0`).
- Why not the real grab: online `0x6cdb40` needs a ZFFPlayer activator and does nothing for a bot (CERTAIN). The real brain decides and the host substitutes the action.
- Van: Board evaluate (`0x4faf60`) wants shadow `+0x1dc` and `+0x1d8` and stage >= 3. Mirror them every tick from where `klbf_ot` already reads the online van state. Board uses `0x7bb2a0(G)`, which already works online. GUESS: the Sv rules do not hold the van state at `+0x1dc`, so find the real field first (stage 2 step zero).
- Stage writes: `0x5dd890` is only called by gated trigger boxes. The hook sets shadow stage 1 at round start, and stage 3 when the real online exit trigger (`0x6c3d50`) fires or when a human grabs anything.
- Board: slot 45 stub sets shadow `+0x10` = 4 and the ledger board flag. The existing OnlineBoardAll path flags the actor.
- Board exit (`0x5478e0`) tail-jumps to `0x7bbf70`, which has an empty-stack risk (S1). Only allow exit with a non-empty order stack.
- **Pass:**
  - Over a full round on one map, with the puppeteer off, bots take loot, carry it, board the van and the round-over card lists them.
  - Compared with an Arcade round on the same map (take count, time to first grab, boarding time, who stays behind), the numbers are in the same band.
  - 0 faults and 0 stub hits outside the expected list.

### Stage 3: traitors and bots triggering cops

**Toggle `OnlineBrainTraitor`, default 0 (lowest priority).**
- Traitor evaluate (`0x79b7c0`) calls `0x7f6850` itself, reads `[rules+0x5f8]+0x45`, `vt[0xe0]` (money), `0x43ffb0` and `0x46d4d0`, and tuning at `[0x168d7c0]+0x6ac+level*0x70`. Run (`0x488eb0`) sets record `+0x79` bit 2 and calls `0x4322f0`.
- The shadow therefore needs the score block (`+0x5f8`: money at `+0x150+4*i`, flags at `+0x1d4+4*i`, level at `+0x45`). Feed it from the ledger.
- Honest note: `0x43ffb0`, `0x46d4d0`, `0x4322f0` were not disassembled. Read them first, because they may reach other Heist fields.
- Cops: keep OnlineTriggers (fires `0x6ae730` when a bot stands in a box). It was seen firing on F06. Its census was blind earlier, and `f38a0d145` now counts NEW cops per fire. Gate pass on that.
- **Pass:**
  - Traitor flips happen at a rate and under conditions comparable to Arcade (watch several rounds on the same map).
  - Bot-fired triggers produce new cops on the host (census > 0). The earlier tp3 run showed 0 new cops, so that is the open item.
  - 0 faults.

### Stage 4: client parity
- Clients run no AI and must not build any of this (role 3).
- Check that the client sees the bots and the cops that bots trigger: movement, weapon fire, the carried-bag animation, boarding and the round-over card. Movement relies on DDL_ZFFActor replication for AI actors, which is certain for cops and a GUESS for Ally bots, plus klsync KLSY2.
- Add a client-side census (cop count and bot positions against the host log).
- **Pass:** a two-seat run in which a screenshot and a log from the client agree with the host, side by side with Arcade footage.

### Crash risks, all stages
- Wrong rules class: only ever return the shadow to tactic code. Never the Sv object.
- Null or out-of-range record: `0x7fd930` has no bounds check. Register every bot before its first evaluate. Unregister on death or removal.
- Leaky frame: `[sm+0x54]` is the role. While it reads 0 any nested caller sees Arcade, including `0x863a60` network checks (350 sites) and damage (`0x61a980`, `0x591b60`). Keep it to one call, host thread, restore in `__finally`.
- Hashing: CEG hashes most of .text and .rdata. SHIP may only write IAT, heap, .data and .bss. Hence the DLL-owned vtable copies and no patches to `0x508ef0` or the ctor. `0x7f6850` and its table are unhashed, so a detour is possible, but only for SESSION/TEST probes.
- Do not call the real Heist ctor `0x835480` (it writes globals `0x1549f0c`/`0x1549f10` and commits network data).

## C. Puppeteer keys to switch off when the real brain runs

(Names as in the notes; confirm against the live ini.)
- Stage 1b/2: `OnlineTactics` off, because it drives movement/loot decisions. Also its Carry/DropTake decision part. Keep the DropTake action itself, since the bridge calls it.
- Stage 2: `OnlineBoardAll` and `OnlineBoardAllNear` off once Board runs for real. Keep OnlineBank, OnlineBankCredit and the OnlineBoardBots latch, because bots still have no seat.
- Keep: OnlineHost, `OnlineTriggers` (with Census), the squad route (`--squad-game eAllTypes`) and klsync.
- Switch the puppeteer off per feature, not wholesale. Two systems steering one soldier is the likeliest source of jitter.

## D. Critic: what was not verified, and what could kill stage 1

1. **`[sm+0x5c]==4` online.** Both reports say `0x508ef0` also needs this, and report 1 says it is cut off online. If it is not 4 on the host, swapping only `[G+0x54]` and `[sm+0x54]` is not enough, and we would have to write `[sm+0x5c]` too (more leakage). *Cheap check:* log `[sm+0x54]`, `[sm+0x5c]`, `[G+0x54]` once per second in a host round. Zero risk.
2. **The two reports disagree on the swap.** Report 1 swaps the rules pointer only. Report 2 also swaps the role. The role swap is needed unless `0x7f6850` is bypassed. *Cheap check:* Option B from report 1, a return-address-gated detour in a DIRECT/SESSION test, to see if the tactics evaluate non-zero without touching the role.
3. **Is the AI update single-threaded?** Report 2 says GUESS. If the AI runs on a worker, a global swap is a race. *Cheap check:* log the thread id in the evaluate wrapper in stage 1a.
4. **Does the list walk call evaluate on pushed objects?** Stage 1a answers it directly via the counter. If the counter stays 0, the vectors are not the real source (GUESS in report 2).
5. **No spawn event.** Polling may miss the first ticks, and a soldier that already ran a tick without tactics is fine, but double-tagging would leak. Tag with the `+0x5f0` null test.
6. **Unread functions:** `0x82f970` (Board run), `0x43ffb0`, `0x46d4d0`, `0x4322f0`, `0x5dd890` and `0x8b94d0` internals. Board run could touch fields the shadow lacks. The stub-hit log in stage 1 should be used to find them, and disassembly should come before stage 2.
7. **Loot candidates.** Slot 202 returns up to 5 entries, each given a `ZOnlineMoneyCtrl +0x5c` shut-door test. The online money controls may have different `+0x5c` semantics. *Cheap check:* dump the controls' fields on the host.
8. **Loot grab by bot.** A bot in the trigger box does nothing online, so Stage 1b shows walking but not looting. That is intended, but then "behaves like Arcade" cannot be graded until stage 2.
9. **Hash risk of vtable copies:** precedents (klfreeclimb, klcrew) say fine. The tactic vtables themselves live in hashed .rdata, so only copies, never edits.
10. **What could make stage 1 impossible:** a worker thread (3), the vectors not being what the AI walks (4), or `[sm+0x5c]` being outside our control (1). Items 1, 3 and 4 are each answered by one read-only logging run, so run these three probes first, before writing any frame code.

Files: `C:\kl-merge\kl-merge\klhook\kllocname.c` (129-165, 270-305), `C:\kl-merge\kl-merge\klhook\klslot.c` (233, 342, 471), `C:\kl-merge\kl-merge\klhook\klbotfill.c`, `C:\kl-merge\kl-merge\re\lobby_map_names.md`, `C:\kl-merge\kl-merge\re\bots_online_fill.md`, `C:\kl-merge\kl-merge\re\boardall_review_exe.md`, `C:\kl-merge\kl-merge\re\bots_bank_online_1028.md`.
---

# Research 1: Arcade brain (tactics)
# Arcade AI brain on the host in online Fragile Alliance: static research report

Offline, read-only. I ran no game, wrote nothing to the game folder and changed nothing in the repo. Addresses are kl2.exe build 0490. CERTAIN means I read it in disassembly or a table. GUESS means inferred.

I did not finish disassembling 0x82f970 (Board run), 0x43ffb0, 0x46d4d0 or 0x4322f0 (Traitor helpers), and 0x5dd890/0x8b94d0 internals. Their rules-slot surface is therefore only partly listed (section 2).

## 0. Bottom line

- **The ctor branch is trivial.** The three tactic ctors read no rules state, so the hook can build the tactic objects itself on any ZSoldier (CERTAIN).
- **The ctors are not the real gate.** The tactics' evaluate and run code asks the rules getter 0x508ef0 for the rules object. Online that returns null (or is cut off by the `[sm+0x5c]==4` and 0x7f6850 tests), so every evaluate returns 0.0 (CERTAIN).
- **The tactics read the Arcade ZGameRulesHeist layout directly.** That means the crew table at `+0x348` (stride 0x7c) and Heist-only vtable slots. 0x508ef0 does no type check, so handing it the online Sv rules (size 0x3a8) would make the tactics read the wrong offsets and crash (CERTAIN).
- **Brain on the host: partly feasible, but a large build.** It needs a shadow rules object and a shadow crew table, plus a host-side loot path. It is not "flip one flag".
- **The loot grab is the hard part.** The online grab (0x6cdb40 online branch, 0x6cdbd0) needs a ZFFPlayer seat as activator. A bot would only return 1 and do nothing (CERTAIN, from `re/bots_bank_online_1028.md`). Loot-carrying by AI is therefore not networked through ZOnlineMoneyCtrl as things stand.

## 1. The ctor branch (ZSoldier ctor, slot 17 = 0x6ab250, branch 0x6ab56d..0x6ab66c)

All CERTAIN.

- The branch loads team as `ebx=[[[soldier+0x40]+0x54]+4]`.
- Each tactic is built only if 0x7f6850 returns true (calls at 0x6ab57c, 0x6ab5d6, 0x6ab628) AND team is 0 or 2.
- 0x7f6850 is a thiscall with ecx=`[0x168e598]` (the session manager, "sm"). It switches on `[sm+0x54]` (role) through the table at 0x7f6874:

| Role | Target | Result |
|---|---|---|
| 0, 1 | 0x7f6865 | `[sm+0x5c]==4` |
| 2, 3 | 0x7f686e | false |
| above 3 | default | `[sm+0x5c]==4` |

- So online hosts (role 2, 3) never build the tactics, which matches the SL8 census of "7 Ally, 0 tactics".

| Tactic | Alloc | Ctor | Vtable | Stored at | What the ctor does |
|---|---|---|---|---|---|
| ZLootTactic | `0x89e850(0x30)` | 0x68eab0(soldier) | 0xbd0d94 | `[soldier+0x5f0]` | base ctor sets `[+4]=soldier`, vtable 0xbd1a2c, zeroes +8, +0xc, +0x10..+0x12; then writes the vtable and zeroes +0x28 and +0x2c |
| ZBoardEscapeVehicleTactic | `0x89e850(0x14)` | 0x68eab0(soldier) | 0xbd0dd4 | `[soldier+0x5f4]` | base ctor only |
| ZBecomeTraitorTactic | `0x89e850(0x20)` | 0x51b7e0(soldier), which calls 0x6340e0 | 0xbd13bc | `[soldier+0x5f8]` | zeroes `[+0x14]` and `[+0x18]`; `[+0x1c]` = LCG random float from the RNG at `[0xdd2640]+0xb30` |

- None of the ctors reads rules. Building the objects ourselves is safe.
- The tactic lists are the soldier vectors at `[soldier+0x604]` (begin, +0x608 end, +0x60c cap) and `[soldier+0x610]` (cap at +0x618).
- They are filled by a conditional push_back through 0x403150 (`test ptr; je skip`).
- Order in list A: ..., `[+0x5dc]`, Traitor, Board, `[+0x5ac]`, `[+0x5bc]`, `[+0x5b8]`, `[+0x590]`, `[+0x598]`, `[+0x59c]`, `[+0x5c0]`, `[+0x5b0]`, Loot last. List B has the same pattern.
- ZDefendPosition run (0x85f6c0, walk at 0x85f8e2..0x85f933) runs the first tactic whose evaluate is above 0, then loops (CERTAIN, per `re/boardall_review_exe.md`).

## 2. Per-tactic update code and the rules surface

Tactic vtables: slot 2 = run, slot 3 = exit, slot 11 = evaluate.

| Tactic | run | exit | evaluate |
|---|---|---|---|
| Loot | 0x7bc7d0 | 0x66b570 (ret) | 0x451920 |
| Board | 0x82f970 | 0x5478e0 | 0x4faf60 |
| Traitor | 0x488eb0 | 0x66b570 | 0x79b7c0 |

All CERTAIN unless tagged.

### ZLootTactic evaluate 0x451920
1. Time gate: `(now - [[actor+0x54]+0x30]) * k >= [0x168d7c0]+0xc34`.
2. `rules = 0x508ef0([0x168e9e4])`. Null gives 0.0.
3. Actor class mask check with 0x1547b24 and 0x1547b28.
4. `idx = 0x78f470(rules, actor)`, then `rec = 0x7fd930(rules, idx)`.
5. Stage `[rec+0x78]`: below 1 gives 0.0. Stage 3 gives 0.0 when rules vt[0x12c]() (state byte `[rules+0x1dc]`) is 3 or 4.
6. Candidates come from rules slot 202 (Heist 0x8b94d0, Sv 0x74a290, Cl none) into `[this+0x14..0x24]` (5 entries). Each entry gets a ZOnlineMoneyCtrl `+0x5c` shut-door test. Then rules vt[0x1c8](idx) & 0x2000 (busy) gives 1.0.
7. It stores `[this+0x28]` and `[this+0x2c]`.

### ZLootTactic run 0x7bc7d0
- Rules touches are only 0x508ef0, 0x78f470(actor) and vt[0x1c8](idx) & 0x2000.
- The rest is path and goal helpers: 0x850b00, 0x5f8fb0, 0x5d1eb0, 0x521350, 0x55b9f0, 0x630b50, 0x6d9eb0, 0x7b0b70, 0x8997a0.
- It never starts the grab. The grab starts when the bot stands in the money object's ZTriggerBox2, which leads to ZOnlineMoneyCtrl slot 26 (0x6cdb40).

### ZBoardEscapeVehicleTactic evaluate 0x4faf60
- Time gate as above, then 0x508ef0 (null gives 0.0).
- Calls rules vt[0x12c]() and switches on the result minus 1 (4 cases, jump table 0x4fb128).
- Case 1 calls 0x7bb2a0 on `[0x168e9e4]`. That returns `[holder+0x54]` only if `[sm+0x5c]==4`. It then calls its vt[0x130] and exits the tactic if the value is positive.
- Other branches call 0x5aeb00, 0x6cbf80, 0x78f470, 0x7fd930, and test `[rec+0x78] >= 3`.
- The scene calls go through `[0xdd2640]+0xac` (obj vt[0x7c]) and rules vt[0x60] with a query struct. The result is `*(ebp-0xa8) > 1` giving 1.0.
- Stage 3 is needed (the player must have looted).

### Board run 0x82f970 (GUESS on internals, not fully read)
- Uses 0x508ef0, 0x78f470, 0x6c7700, 0x7fd930.
- I did not finish it. It most likely drives vehicle boarding through rules slot 45 (Heist 0x6840a0, Sv 0x6c6c10, Cl 0x719230) and `[rules+0x1dc]`, `[rules+0x1d8]`.

### Board exit 0x5478e0
- 0x508ef0, then rules vt[0x2f4]. If true, it sets `[soldier+0x40+0x8f1]=1` and tail-jumps to 0x7bbf70.
- Slot 0x2f4 is 0x4ee010 in all three classes (Heist, Sv, Cl).
- Per `re/boardall_review_exe.md`, 0x7bbf70 has an empty-stack risk (S1).

### ZBecomeTraitorTactic evaluate 0x79b7c0
- Calls 0x7f6850 itself. False gives 0.0.
- Timer gate `[this+0x18] > [0xdd2640]+0x48` gives 0.0.
- 0x508ef0 (null gives 0.0), then `0x78f470(rules, 0x6cbf80(actor+0x40))` stored into `[this+0x14]`.
- 0x43ffb0(rules, idx) must be true (GUESS: a traitor eligibility check; it reads TUNING and the clock).
- Reads `[rules+0x5f8]` (the traitor sub-object) `+0x45` for the level, clamped 1..11, and calls rules vt[0xe0] twice (Heist 0x6f86c0, Sv 0x819aa0).
- Reads the tuning table `[0x168d7c0]+0x6ac+level*0x70`.
- Reads stage `[rec+0x78]`, calls 0x6c7700 (a player index that itself calls 0x7f6850), and compares thresholds from the table against 0x46d4d0(rules).
- Full dependency on Heist: `rules+0x5f8` is a Heist-only field.

### Traitor run 0x488eb0
- Gets rules, then `or byte [rec+0x79], 2` (marks traitor) and calls 0x4322f0(rules, idx).
- Hard dependency on the crew record (`[rules+0x348]+idx*0x7c`).

### Crew record table (Heist only)
- Table at `[rules+0x348]`, stride 0x7c, count `[rules+0x354]`, in-use bytes at `[rules+0x34c]` (0 = in use).
- Fields:
  - +4 object
  - +0x10 status (4 = aboard)
  - +0x15 grab state
  - +0x18 timer
  - +0x1c object
  - +0x78 stage 0..3
  - +0x79 flags (bit 1 = bot, bit 2 = traitor)
- It is written by slot 198, which is 0x588980 on Heist but 0x832930 (`ret 8`) on online Sv, and 0xca36bc on Cl. Online never creates the record.
- 0x78f470 needs `+0x79` bit 1 and `+4 == actor`. 0x7fd930 returns `[rules+0x348]+idx*0x7c`.
- Stage writer 0x5dd890(rules, activator, n). Callers are trigger boxes 0x6c3d9e, 0x8d2781, 0x8d27dd, 0x8d2835.

### Rules vtable slots the tactics call (vtables: Heist 0xbd3514, Sv 0xbd2eb4, Cl 0xbd31e4)

| Slot | Heist | Sv | Cl | Note |
|---|---|---|---|---|
| 0x12c | 0x5d52f0 | 0x5d52f0 | 0x5d52f0 | same everywhere; reads `[rules+0x1dc]`-type state, which would be Heist-layout data (GUESS) |
| 0x130 | 0x63b300 | 0x63b300 | n/a | same |
| 0x1c8 | 0x771a10 | 0x625be0 | 0x625be0 | status/busy bits, class-specific |
| 0x2f4 | 0x4ee010 | 0x4ee010 | 0x4ee010 | same |
| 0xe0 | 0x6f86c0 | 0x819aa0 | n/a | class-specific |
| 0x60 | 0x4c21f0 | 0x681c50 | 0x681c50 | class-specific |
| 202 | 0x8b94d0 | 0x74a290 | none | loot candidate list |
| 45 | 0x6840a0 | 0x6c6c10 | 0x719230 | boarding rule |
| 198 | 0x588980 | 0x832930 | 0xca36bc | crew-record registration |
| 201 | 0x56f6e0 | 0x8f2f60 | 0x860b00 | grab start |
| 46 | 0x716640 | 0x8234d0 | 0x716640 | online grab entry |

## 3. Inventory of reads, writes and gates

### 0x508ef0 (Arcade rules getter), ecx=`[0x168e9e4]`
- Returns `[this+0x54]` only if `[sm+0x5c]==4` AND 0x7f6850() is true. Otherwise null.
- It does not type-check the class (CERTAIN).
- 139 call sites in 55 functions. The behaviour-relevant ones:
  - Tactic tests and actions: 0x451920, 0x7bc7d0, 0x4faf60, 0x82f970, 0x5478e0, 0x79b7c0, 0x488e50, 0x488eb0.
  - Money and triggers: 0x6cdb40, 0x6c3d50, 0x8d2740, 0x907a50 (ZAllyEscapeBox).
  - Session and damage: 0x8e5650, 0x61a980, 0x882470, 0x5706a0.
  - Others: 0x435c40, 0x5b5f40, 0x466b30.
- 0x7bb2a0 is a variant that tests only `[sm+0x5c]==4` and returns `[holder+0x54]`. Online it returns null on its own `[sm+0x5c]` check.

### 0x7f6850 and 0x863a60
- 0x7f6850 has 291 call sites in 219 functions. The tactic and money-related ones:
  - Ctor: 0x6ab57c, 0x6ab5d6, 0x6ab628.
  - Traitor evaluate: 0x79b7d2.
  - Trigger boxes: 0x626f92 (ZTriggerBox2 update 0x626ec0), ZOnlineTriggerBox 0x49ab90, ZTriggerBox 0x42afd0.
  - Squad filter: 0x7b3790 (tests at 0x7b37d1, 0x7b3805, 0x7b382c, 0x7b385c).
  - Session handler: 0x8e5650 (Arcade slot 45; online uses 0x466ea0).
  - Player index: 0x6c7700.
- 0x863a60 ("networked": true for role 2 or 3) has 350 sites in 287 functions. I did not enumerate them. Treat anything calling it as an online branch (GUESS).

### Other Arcade-only gates a bot hits online
- Trigger boxes ignore Ally activators online (0x626f92 pattern), so bots cannot start grabs or set crew stage.
- 0x6cdb40 online branch (0x6cdbd0) needs a ZFFPlayer activator (0x7aace0). A bot returns 1 and does nothing.
- 0x8e5650: `if (0x7f6850 && team==2) rules->slot198(actor)`. Online uses 0x466ea0, which never registers the actor, so there is no crew record.
- 0x61a980: online skips the damage table 0x591b60 (from `re/bots_online_arcade_1028.md`).
- ZSquadScript filter 0x7b3790 passes Ally squads online only through the data route (`tools/kl_botsonline.py`, `kl_fa_bots --squad-game eAllTypes`). The bot squads are eHeistOnly (8).
- 0x508ef0 "who shoots whom" lock: I read it as the same getter (the Heist team/hit-attribution tests ride on the rules pointer). It is not verified separately (GUESS).
- Clients run no AI: squad update 0x47e440 is skipped on role 3, and ZSoldier orders 0x760e50 are dropped on clients (CERTAIN, from `re/bots_online_fill.md`).

## 4. Technique: real tactics for Ally soldiers, host only

### Hashing facts (CERTAIN)
- CEG hashes 84.9% of .text and 65.9% of .rdata. Editing a hashed byte ends a real session (ExitProcess 0x8000dead).
- Unhashed: 0x7f6850, its jump table 0x7f6874, 0x7f6865, 0xb10418.
- Hashed: 0x508ef0, the whole ctor (0x6a7000-0x6ac000), every tactic function above, the trigger-box gates, 0x7b3790, 0x7aace0, and all tactic and rules vtables (.rdata 0xb8b000-0xbeb000).
- Policy: SHIP may write only IAT, heap, .data and .bss. SESSION may also write image bytes outside the hashed ranges. DIRECT may write anything, for direct-boot tests only.

### Option A, SHIP-safe (recommended): hook-built tactics with DLL-owned vtable copies
1. After a host ZSoldier of team 2 (Ally) finishes its ctor, allocate the three objects with 0x89e850 using the sizes above. Call 0x68eab0 (Loot, Board) and 0x51b7e0 (Traitor). Store them at `+0x5f0`, `+0x5f4`, `+0x5f8` and push them into the vectors at `+0x604` and `+0x610` in the order of section 1 (Traitor, Board before the `[+0x5ac]` group, Loot last). Use the game's own realloc-insert 0x403150 so end/cap stay valid.
2. Give each object a vtable copy living in the DLL (precedent: klfreeclimb, klcrew). In slots 2, 3 and 11 install wrappers.
3. A wrapper does the following, on the game thread:
   - Write the host's shadow rules object (below) into the rules holder pointer used by 0x508ef0, or flip the gate data it reads. The gate data are `[sm+0x54]` and `[holder+0x54]`; both are heap/data and writable under SHIP.
   - Call the original (0x451920, 0x7bc7d0, 0x4faf60, 0x82f970, 0x5478e0, 0x79b7c0, 0x488eb0).
   - Restore the originals on exit, including via a try/restore path.
4. The wrapper must be re-entrancy safe. The same swap also changes every other 0x508ef0 caller that runs inside the wrapper: path code, damage, triggers. Keep the window to a single tactic call and never yield inside it.

### What must be faked (shadow rules object)
- It needs the Heist layout fields that the tactics read:
  - `+0x348` crew table, stride 0x7c, with `+0x34c` in-use bytes and `+0x354` count.
  - `+0x1dc` van state and `+0x1d8`.
  - `+0x5f8` traitor sub-object, with `+0x45` level.
  - `+0x54` holder pointer behaviour.
- Its vtable (DLL copy) must supply the slots in section 2: 0x12c, 0x130, 0x1c8, 0x2f4, 0xe0, 0x60, 202, 45. Those that are identical across classes (0x12c, 0x130, 0x2f4) can reuse the game addresses only if the shadow object's fields feed them correctly. The class-specific ones (0x1c8, 0xe0, 0x60, 202, 45, 198) need hook implementations or the Heist originals reading from the shadow fields.
- One crew record per Ally bot, with `+4` = soldier, `+0x78` stage, `+0x79` bit 1 (bot).
- Keep the stage/flags in sync with what the online ledger really knows, because 0x5dd890 and the trigger boxes will not update them (they are gated off online).

### Crash risks and guards
- **Wrong rules class (CERTAIN):** 0x508ef0 does not type-check. Guard: only ever return the shadow object, never the Sv object, to tactic code.
- **Null crew record (CERTAIN):** 0x7fd930 does not bound-check. Guard: register every bot in the shadow table before its first evaluate, and unregister before the soldier dies.
- **Gate window leak (GUESS):** while the swap is active any nested 0x508ef0 caller sees the shadow. Guard: restore on all exits, and run only from the host tick.
- **0x7bbf70 empty-stack (S1) (CERTAIN, from `re/boardall_review_exe.md`):** the Board exit tail-jumps to it. Guard: only trigger exit with a non-empty order stack.
- **Vector insert (CERTAIN):** the game's vectors use their own allocator. Guard: use 0x403150 and 0x89e850, never the C runtime heap.
- **Destructors (CERTAIN):** vtable slot 0 is 0x4fe6f0. A DLL-owned vtable copy must keep slot 0 pointing at the game's destructor so the soldier tears the objects down normally.
- **Clients:** do not build any of this on role 3. Clients run no AI, and a shadow rules object there would only diverge.

### Option B, SESSION/TEST only: return-address-gated detour of 0x7f6850
- 0x7f6850 is outside the hashed ranges, so a detour is possible in a SESSION build. It could answer true for chosen callers (the ctor sites, the tactic code, the trigger gates).
- It does not solve the rules object. 0x508ef0 still needs `[sm+0x5c]==4`, and the tactics still need a Heist-layout rules object. This option is not SHIP-safe and not enough on its own. I would use it only as a probe in direct-boot tests.

## 5. Replication and loot

- **Movement and animation (CERTAIN for cops, GUESS for Ally bots):** AI actors replicate as DDL_ZFFActor, and cops already do this. The host's tactics would drive the same host-side actors, so clients see them move with no new code. The hook also mirrors bots through klsync KLSY2 (UDP 27415).
- **Loot pickups: not networked for bots.**
  - The grab needs a ZFFPlayer seat as activator (0x6cdb40 online branch, rules slot 46 = 0x8234d0, then 0x7ceaf0, per-record tick 0x6135f0, then 0x4e3f40 and 0x5a18c0).
  - A bot standing in the trigger box does nothing online, because the gate at 0x626f92 and the ZFFPlayer check both reject it.
  - Arcade's own grab runs through rules slot 201 (0x56f6e0, then 0x8e8750, then 0x727cb0). That path needs the Heist crew record, so it works only with the shadow object.
- **Money:** online money lives in the score object S=`[rules+0x2c]`. Sharable is at S+0x188 (getter 0x699030), Unsharable at S+0x224 (getter 0x783780). The one adder is 0x5a18c0 (seat, amount). A bot needs a seat to credit, or the host must credit a human or bank seat directly, as the existing OnlineTactics path does.
- **Practical split:** let the real tactics provide the decision (what to loot, when to board). Keep the host-side substitutes for the grab (the existing OnlineTriggers path) and the money credit. The brain alone does not fix the "plays badly" part if the grab and boarding actions still run through the puppeteer.

## 6. Hook sites

SHIP-safe sites:
- After ZSoldier ctor for team 2 on the host. The hook point is the tick or the soldier-created event. I did not find a clean spawn-time event (GUESS).
- `[soldier+0x5f0]`, `[soldier+0x5f4]`, `[soldier+0x5f8]` and the vectors `[soldier+0x604]` and `[soldier+0x610]` (heap).
- DLL-owned vtable copies for the three tactics (slots 2, 3, 11), based on the game's tables at 0xbd0d94, 0xbd0dd4 and 0xbd13bc.
- Shadow rules object with a DLL vtable copy, supplying slots 0x12c, 0x130, 0x1c8, 0x2f4, 0xe0, 0x60, 202, 45, and the crew table fields.
- The gate data: `[0x168e9e4]+0x54` (rules pointer) and `[0x168e598]+0x54` / `+0x5c` (role / sub-state).
- Game calls from the hook: 0x89e850, 0x68eab0, 0x51b7e0, 0x403150, 0x78f470, 0x7fd930, 0x5dd890.
- Host-side substitutes: the existing OnlineTriggers path in `klhook/klbotfill.c` and the money credit via 0x5a18c0.

SESSION/TEST-only sites:
- 0x7f6850 detour, gated by return address.

Reference files:
- `C:\kl-merge\kl-merge\klhook\klbotfill.c`
- `C:\kl-merge\kl-merge\re\bots_online_fill.md`
- `C:\kl-merge\kl-merge\re\boardall_review_exe.md`
- `C:\kl-merge\kl-merge\re\bots_bank_online_1028.md`
- `C:\kl-merge\kl-merge\re\bots_online_arcade_1028.md`
---

# Research 2: rules / crew records
# Arcade AI heisters on the online FA host: offline research report

Everything below is from read-only disassembly of kl2.exe (base 0x400000, no ASLR). Nothing was run, installed or patched. CERTAIN means read directly from disassembly. GUESS means inferred and needing a bench check.

## 0. Verdict

- **Gate (CERTAIN).** Arcade's AI heister logic is gated twice:
  - The ZSoldier ctor 0x6ab250 only builds the three tactic objects when 0x7f6850() is true.
  - Every tactic call reaches the rules through 0x508ef0(G), which returns NULL online.
- **Missing structure (CERTAIN).** The online Sv rules (0x3a8 bytes) and Cl rules (0x334 bytes) have no crew table at +0x348 and no score block at +0x5f8. Faking them into the real Sv object is impossible, because Sv uses +0x348 and +0x350 for its own fields.
- **Feasible route (GUESS).** The cleanest route is a hand-built SHADOW heist-rules object that only the bot tactics see. This uses a caller-gated frame that swaps [sm+0x54] and [G+0x54] only around the bot tactic entry points, on the main thread. The shadow's results are bridged into the existing klbotfill.c ledger (`klbf_ob[]`, tally, OnlineBankCredit) and the klsync mirror.
- **Cops (GUESS).** Cop spawning from bots through ZTriggerBox is already implemented host-side by OnlineTriggers and has been seen firing live on F06. Replication to clients is expected, because the cops are host AI actors replicated as DDL_ZFFActor, but no graded proof exists.

## 1. Crew record and how Arcade drives it

### 1.1 Containers (CERTAIN)

| What | Address / field |
|---|---|
| Rules class | ZGameRulesHeist, ctor 0x835480, vtable 0xbd3514, size 0xf30 (alloc 0x89e850) |
| Game object | G=[0x168e9e4], rules pointer at G+0x54 |
| Crew table | [rules+0x348], records of 0x7c bytes, record ctor 0x549030 |
| In-use bytes | [rules+0x34c] (0 = in use) |
| Free count | [rules+0x350] |
| Capacity / count | [rules+0x354] |
| Per-seat character byte | rules+0x33e+idx |
| Record by index | 0x7fd930(rules, idx) = [rules+0x348] + idx*0x7c |
| Find by actor | 0x78f470(rules, actor) returns the index whose +4 == actor and whose +0x79 has bit 1 |
| Index validators | slot 114 (0x771a10) and slot 56 (0x6f86c0) check idx against [rules+0x354] and [rules+0x34c] |
| Score block | [rules+0x5f8], per-client money at +0x150+4*i, per-client flags at +0x1d4+4*i |
| Van state | byte [rules+0x1dc], timer float [rules+0x1d8] |

Per-client flag bits at [score+0x1d4+4*i]: 0x2000 looting, 1 traitor, 4 dead, 8 police, 0x20 aboard, 0x40 escaped.

### 1.2 Record layout (0x7c bytes)

| Offset | Meaning | Tag |
|---|---|---|
| +0 | pointer to client block; [[rec]+2] bit flags: 1 entered, 2 exited, 4 at exit, 8 took loot; [[rec]]==0 means local player | CERTAIN |
| +4 | actor or player object | CERTAIN |
| +8, +0xc | respawn float and a float | CERTAIN layout, GUESS meaning |
| +0x10 | status: 0 in play, 1 dead or waiting for police, 3 timed state, 4 aboard, 5/6 escaped, 7 dead for good | CERTAIN values |
| +0x11, +0x12, +0x13 | death-camera phase, a byte, deaths | CERTAIN layout |
| +0x14 | police player index (0xff = none) | CERTAIN |
| +0x15 | loot state: 0 none, 1 looting, 2 waiting, 3 taking from a person | CERTAIN |
| +0x18 | float, seconds left of the part being taken | CERTAIN |
| +0x1c | the ZOnlineMoneyCtrl being looted (vtable 0xbc874c, +0x34 amount left, +0x40 one part) | CERTAIN |
| +0x20..+0x2c | zeros | CERTAIN |
| +0x30 | float 1.0 | CERTAIN |
| +0x35 | byte copied from tuning [0x168d7c0]+0x684 | CERTAIN |
| +0x6c, +0x70, +0x74 | float timers | CERTAIN layout |
| +0x78 | heist stage 0..3, not replicated | CERTAIN |
| +0x79 | flags: bit 1 = AI bot, bit 2 = traitor | CERTAIN |

### 1.3 Heist stage (+0x78)

- **Writers (CERTAIN):**
  - the ctor;
  - round reset 0x817d20, called from 0x8c7ab3 inside 0x8c7a80;
  - 0x5dd890(rules, activator, n), which stores max(old, n).
- **Callers of 0x5dd890 (CERTAIN):**
  - the exit trigger at 0x6c3d9e raises stage 3;
  - the gameplay trigger 0x8d2740 raises stage 1, 2 or 3 for trigger types 0, 1 or 2.
- **Readers:**
  - R1 Loot eval 0x451920: stage 0 gives 0, and stage 3 with van state 3 or 4 gives 0.
  - R2 Board eval 0x4faf60: needs stage >= 3.
  - R3 damage 0x591b60.
  - R4 Traitor eval 0x79b7c0.
  - R5 slot 194 (0x8fa6d0).

### 1.4 Creating a record per AI heister (CERTAIN unless noted)

Slot 198 (vtable offset 0x318, function 0x588980) does the following:

1. It builds a temporary 0x7c record on the stack with ctor 0x549030.
2. It sets rec+4 to the actor, rec+0x79 |= 1 and rec+0x10 to 0.
3. It computes the index as [rules+0x354] - [rules+0x350] + 1.
4. It stores the character digit from the actor name (Glazer_Bodyguard_0N, text built by 0x478df0 and 0x83e2e0) at rules+0x33e+idx.
5. If the free byte at idx is nonzero, it copies the record into the table with `rep movsd` of 0x1f dwords, clears the byte and decrements [rules+0x350].
6. It finishes with 0x588680, 0x960d70 and 0x7ad590(ecx=[x+0x10c4], idx), which fills a 12-entry seat table with a 0x10c stride and a byte at +0x2c.

Callers (CERTAIN):

- ZSessionHandlerSP slot 45 is 0x8e5650: `if (0x7f6850() && [[actor+0x54]+4]==2) 0x508ef0(G)->vt[0xc6](actor)`.
- Slot 197 (0x42bc80) registers the human at record 0.
- The round-start reset is 0x8c7a80 calling 0x817d20.
- **Not found:** what calls the SP session's slot 45. The caller at round start stays GUESS (likely the actor-spawn or team-join path).
- Online, the session handler's slot 45 is 0x466ea0 and never reaches the rules (CERTAIN).

### 1.5 What the AI heister tactics read and write

The tactics are three standalone heap objects built in the ZSoldier ctor at 0x6ab56d..0x6ab66c. This happens only if 0x7f6850() is true and team is 0 (Mercenary) or 2 (Ally). Each is allocated with 0x89e850.

| Slot in soldier | Tactic | Size | Vtable | Ctor |
|---|---|---|---|---|
| +0x5f0 | ZLootTactic | 0x30 | 0xbd0d94 | 0x68eab0(soldier) |
| +0x5f4 | ZBoardEscapeVehicleTactic | 0x14 | 0xbd0dd4 | 0x68eab0 |
| +0x5f8 | ZBecomeTraitorTactic | 0x20 | 0xbd13bc | 0x51b7e0(soldier) |

The base ctor 0x68eab0 stores the soldier at +4, sets vtable 0xbd1a2c and zeros +8, +0xc and +0x10..0x12. ZLootTactic also zeros +0x28 and +0x2c. The soldier's priority vectors are at +0x604 and +0x610 (begin, end at +4, cap at +8). The ctor pushes the tactic pointers at about 0x6abcd4..0x6ac4d8, with Board second and Loot last. The destructor at 0x4155c2 tolerates null pointers.

Rules calls made by each tactic (all through 0x508ef0, so NULL online):

| Tactic | Functions | Rules members touched |
|---|---|---|
| Loot (eval 0x451920, run 0x7bc7d0) | 0x78f470, 0x7fd930, slot 75 (0x5d52f0, van state), slot 114 (0x771a10, flags), slot 202 (0x328, 0x8b94d0, loot candidates), 0x6bb730 | record +0x78 (read), +0x15, +0x18, +0x1c; client flag 0x2000 |
| Board (eval 0x4faf60, run 0x82f970) | slot 75, slot 76 (0x130, 0x63b300, van timer), 0x74d7f0 (wraps boarding slot 45; boarding itself is 0x6840a0), slot 200 (0x320, 0x71e2f0, vehicle position), 0x7fd930 | record +0x78 (stage >= 3), +0x10 |
| Traitor (eval 0x79b7c0, run 0x488eb0) | 0x43ffb0, 0x46d4d0 (tuning, level record R=[0x168d7c0]+0x6ac+level*0x70), slot 56 (0x6f86c0, money), 0x4322f0, slot 244 (0x64c000, which jumps to 0x59fea0 with ecx=sm) | money [[rules+0x5f8]+0x150+i*4], record +0x79 bit 2 |

The money-bank path is slot 201 (0x324, 0x56f6e0). It checks `0x8e6a20(sm)==0x19`, runs the actor class mask test and 0x78f470, then calls 0x8e8750.

0x8e8750(rules, idx, ctrl), the grab, in detail:
- state +0x15 == 0: sets client flag 0x2000, sets +0x15 to 1, stores ctrl at +0x1c, and sets +0x18 = ctrl[+0x44] * 0x4f3e50(G) (the time to take);
- state +0x15 == 2 and ctrl matches +0x1c: sets +0x15 back to 1;
- anything else: no-op.

The vt[0x198/4] call at the end is the rules' own "start looting" notification, which is probably only animation or UI (GUESS).

### 1.6 Van state machine (CERTAIN)

State byte [rules+0x1dc], timer [rules+0x1d8], set through slot 194 (0x8fa6d0).

- States 1 and 2: driving in.
- States 3 and 4: waiting and boardable.
- State 5: driving out.
- State 6: destroyed.
- State 7: next vehicle or end.

The slot 194 order pass runs for states 1, 2, 5 and 6.

## 2. What the online rules hold instead

- **Classes (CERTAIN).** Sv has vtable 0xbd2eb4, size 0x3a8 and ctor 0x79acc0. Cl has vtable 0xbd31e4, size 0x334 and ctor 0x6fe090. They are siblings of the Heist class, not subclasses.
- **Factory (CERTAIN).** The rules factory is at 0x725d70..0x725f6f. Arcade allocates 0xf30 and runs ctor 0x835480. The online host allocates 0x3a8, and the client allocates 0x334. All paths then call vt[36], vt[39](byte), vt[42](float) and 0x645150.
- **Per-client table (CERTAIN).** 0x74-byte records at [rules+8], 12 seats (re/netcode.md section 10).
- **Score object (CERTAIN).** S=[rules+0x2c]. 0x571750(S,seat) returns [S+0x58+0x40+4*seat], with 0x20 meaning aboard and 0x40 meaning escaped. AddSharable is 0x5a18c0, thiscall with S in ecx, stack args (seat, amount), `ret 8`.
- **Round-end settlement.** 0x5e2230 is called at 0x681103 inside Sv slot 192 (0x680f90). That call site is hash-checked, so it must not be retargeted. 0x6f4960 splits the sharable pool among escapees (CERTAIN).
- **Boarding online.** Sv slot 45 is 0x6c6c10 (sets state 4 and flag 0x20). 0x776ef0 turns that into state 5 and flag 0x40 (CERTAIN).
- **Banking per player (CERTAIN).** Sv slot 46 (0x8234d0) needs a ZFFPlayer with a seat ([player+0x2748]). A bot has none, so the game cannot bank money for a bot.
- **Money pickup (CERTAIN).** ZOnlineMoneyCtrl handler 0x6cdb40 fires on message id [0x168c3c8] with byte [this+0x74] set, and then branches:
  - Arcade (0x7f6850 true): `0x508ef0(G)->vt[201](actor, ctrl)`.
  - Online: `0x7aace0(player)`, then `0x7bb2a0(G)->vt[46](player, ctrl)`.
- **Exit trigger.** ZOnlineExitLevelTrigger is 0x6c3d50. It raises stage 3 via 0x5dd890 at 0x6c3d9e. I did not trace the rest of its body offline, so how it feeds the online board stays at documentation level (GUESS beyond that).
- **Gate functions (CERTAIN).**
  - 0x7f6850 uses a jump table at 0x7f6874. Roles 0 and 1 return [sm+0x5c]==4, roles 2 and 3 return false.
  - 0x863a60 is the networked check (roles 2 and 3).
  - 0x8df480 is true for host and Arcade, false for client.
- **Rules getters (CERTAIN).** 0x508ef0(G) returns [G+0x54] only if [sm+0x5c]==4 AND 0x7f6850(), so it is NULL online. 0x7bb2a0(G) returns [G+0x54] if [sm+0x5c]==4 with no Arcade check, so it works online. The Board tactic uses it for the van timer.
- **Already bridged in klbotfill.c (CERTAIN from docs and source header):**
  - `klbf_ot` puppeteer and `klbf_ob[]` ledger (phases, tally, banked), under the OnlineHost and OnlineTactics options.
  - OnlineBank: a host ledger, since bots have no seat.
  - OnlineBankCredit: adds the ledger to an escaped human seat via 0x5a18c0.
  - OnlineBoardAll and OnlineBoardAllNear, plus OnlineTriggers with Extra, SkipPickups and Census.
  - The OnlineBoardBots latch in klhud_board2.c and klhud_boardbots_logic.h for the round-over card.
  - klsync.c (KLSY2, UDP port 27415) mirrors bot actors.
  - Constraint: the SHIP policy forbids .text patches.

## 3. Shadow heist-rules design

### 3.1 The shadow block

- Allocate a private 0xf30-byte zeroed block (alloc via 0x89e850 or the CRT, not the ctor).
- Give it a private copy of the Heist vtable 0xbd3514. This is copied once and writable. Populate only the slots the tactics call.

| Slot | Offset | Original | In shadow |
|---|---|---|---|
| 56 | 0xe0 | 0x6f86c0 | original works (reads shadow table) |
| 75 | 0x12c | 0x5d52f0 | original works (reads shadow +0x1dc) |
| 76 | 0x130 | 0x63b300 | original works (reads shadow +0x1d8) |
| 114 | 0x1c8 | 0x771a10 | original works |
| 194 | 0x308 | 0x8fa6d0 | hook stub, no-op (order pass), or keep the mirror |
| 198 | 0x318 | 0x588980 | original may work on the shadow, or a stub that writes the record itself |
| 200 | 0x320 | 0x71e2f0 | hook stub or original (pure geometry) |
| 201 | 0x324 | 0x56f6e0 | hook stub: do the grab on the shadow, bridge to the ledger |
| 202 | 0x328 | 0x8b94d0 | hook stub: loot candidates from the real online money controls |
| 244 | 0x3d0 | 0x64c000 | hook stub or original |
| 45 | 0xb4 | boarding | hook stub: set record +0x10 = 4, set ledger board flag |

All other slots are stubbed to return 0 or are left null. Whether any other slot is reached is a bench question (GUESS).

- Table fields, filled by the hook:
  - [shadow+0x348] = array of N*0x7c bytes, with N = 12 so it matches the seat table;
  - [shadow+0x34c] in-use bytes (0 = in use);
  - [shadow+0x350] free count;
  - [shadow+0x354] capacity;
  - [shadow+0x33e+idx] character digit.
- Score block: [shadow+0x5f8] = private 0x1d4+4*12 byte zeroed block. Money lives at +0x150+4*i and flags at +0x1d4+4*i.
- Per-tick mirror of van state: copy byte [real_rules+0x1dc]... **but** this is the open question. The Sv rules do not hold the van state at +0x1dc, because the layout differs. The Board tactic already uses 0x7bb2a0(G) and reads the real online van timer, so `klbotfill` already knows where the online van state lives. Reuse that source for the mirror (GUESS: the mirror source is whatever klbf_ot reads today).

### 3.2 Making 0x508ef0 return the shadow (GUESS)

Do not patch 0x508ef0 (no .text patches in SHIP). Instead use a caller-gated frame:

- On the host, for each bot soldier, give each tactic object a private vtable copy (the vtable pointer is at +0, not shared with other tactics) and replace the eval and run slots (vtable slots 2 and 11, from the existing klbf_ot puppeteer if it already does this).
- The wrapper does, on the main thread, in this order:
  1. save [sm+0x54] and [G+0x54];
  2. set [sm+0x54] = 0 (so 0x7f6850 reports Arcade) and [G+0x54] = shadow;
  3. call the original;
  4. restore both unconditionally.
- Risk: while the frame is open, anything the original calls sees "Arcade". The tactics call into pathing, animation and sound code, so a side effect such as Arcade-style death handling is possible. The frame must stay as narrow as the single eval or run call. Threads: the game's AI update runs on the main thread, which keeps the swap invisible to network and render code (GUESS, needs a bench check).
- Alternative that avoids swapping the role: set only [G+0x54] (shadow) and hook only the 0x508ef0 return by wrapping the tactic's call. That is not possible without a .text patch, because 0x508ef0's gate is read from the sm, so the swap of sm+0x54 stays necessary.

### 3.3 Building the tactics post hoc (GUESS)

The ZSoldier ctor skips the tactic construction online. To add them afterward, for each host bot soldier (Mercenary or Ally team):

1. Allocate with 0x89e850 and run the ctors 0x68eab0 / 0x51b7e0 (set vtables 0xbd0d94, 0xbd0dd4, 0xbd13bc).
2. Write the pointers to [soldier+0x5f0], +0x5f4 and +0x5f8.
3. Push them into the vectors at +0x604 and +0x610 in the original order (Board second, Loot last). Vector push is a GUESS: the vector element type and allocator are not confirmed, so reproduce the ctor's exact push sequence from 0x6abcd4..0x6ac4d8.

If post-hoc construction proves fragile, klbf_ot's existing puppeteer (a non-tactic host script) is the fallback and is what ships today.

### 3.4 Bridging results out

| Shadow event | Bridge |
|---|---|
| Record +0x15 transitions 1 to taken (slot 201 stub) | add the take to `klbf_ob[bot].tally` |
| Record +0x10 = 4 or 5 (aboard or escaped) | set the ledger phase, and the OnlineBoardAll path flags the bot actor |
| Round end | OnlineBankCredit adds the ledger to an escaped human seat via 0x5a18c0 (existing); the board latch (OnlineBoardBots) shows bots on the round-over card |
| Position / state for clients | klsync KLSY2 mirror (existing) |
| Round start | zero the shadow table, then register each bot with slot 198 (shadow) |

The real online money control still has to be removed from the world when a bot takes it. Use the same handler path as today's DropTake / Carry 8 code in klbotfill.c.

## 4. Trigger-box gate and cops

- **Gate (CERTAIN).** ZTriggerBox update 0x42afd0 makes its team-2 gate call at 0x42b1e0. ZTriggerBox2 update 0x626ec0 has its gate at 0x626f92 (slot 34 = 0x557820). ZOnlineTriggerBox update 0x49ab90 is gated by 0x8df480, which is true for the host.
- **Fire path (CERTAIN).** 0x6ae730 calls the sync object [box+0x6c] vt[3](0), then box vt[0x88] (slot 34 = 0x45f5d0). Slot 34 posts the AITrigger word [0x1688e70] to the target list [box+0x38] and applies the re-arm at [box+0x50]. Inside test is 0x8c16c0. Network path of the Online box is 0x6557b0 to 0x642f20 to 0x900970 or 0x942b20. The hook sets [box+0x78]=1 to avoid double fires.
- **Caller-gated approach (CERTAIN for the existing code).** The same idea already works: OnlineTriggers scans boxes on the host and calls 0x6ae730 directly when a bot stands inside, so the 0x7f6850 gate is never relevant. It was seen firing on F06 (three fires, "trig: FIRE box 557eb920 via 0x6ae730 ... fire #1").
- **Do the spawned cops replicate? (GUESS, likely yes.)**
  - Squad update 0x47e440 is skipped on a client (role 3), so cops are host AI actors replicated as DDL_ZFFActor.
  - Stock online FA already spawns cops through ZTriggerBox when a human enters, which uses the same path.
  - No graded run proves a client sees a bot-triggered cop. OnlineTriggersCensus (log only) counts cops at the fire, +10 s and +30 s on the host, but nothing is compared on a client.
- **Squad filter (CERTAIN).** 0x7b3790 (ZSquadScript slot 14) drops eHeistOnly (8) squads online unless the mask has bit 1. Fix by data (`--squad-game eAllTypes` in kl_botsonline.py or kl_fa_bots.py) or klbf_squads.

## 5. Hook sites

| Site | Purpose | Tag |
|---|---|---|
| 0x6ab250 end (ZSoldier ctor) | host post-hook: build the three tactics when role is 2 and team is 0 or 2 | GUESS |
| tactic vtable slots 2 and 11 (private copies) | open and close the caller-gated frame | GUESS |
| [sm+0x54], [G+0x54] | frame swap targets | CERTAIN addresses |
| shadow vtable slots 45, 194, 198, 200, 201, 202, 244 | stubs bridging into klbf_ob[] | GUESS |
| 0x5a18c0 | AddSharable bank | CERTAIN |
| 0x6ae730 | trigger fire | CERTAIN |
| 0x681103 (call to 0x5e2230) | do not touch, hash-checked | CERTAIN |

## 6. Risks and bench plan (not run)

1. A frame that reports Arcade while the original runs could change unrelated code paths (death, damage via 0x591b60 / 0x61a980, which are Arcade-only per online_bot_damage.md). Keep the frame narrow, and assert on re-entry.
2. If one of the tactic's calls reaches a vtable slot that is not populated, it crashes on a null call. Fill unused shadow slots with a stub returning 0 and log which ones fire.
3. A real second Heist ctor (0x835480) is not recommended: it writes globals [0x1549f0c] and [0x1549f10] and commits network data via 0x942b20 / 0x9425a0.
4. Bench order: DM01 and DD05 online with two seats, Carry 8, and a log of every shadow stub hit. First step is tactics built but frame disabled, which should log only construction. Second step is frame enabled for Loot only. Third is Board. Fourth is Traitor, which is lowest priority.

## 7. Open points (all GUESS)

- Who calls the SP session slot 45 at round start.
- Whether wrapping only the tactic entry points is enough, or whether other soldier code also calls 0x508ef0.
- Where the online van state lives in Sv, so the shadow mirror can be fed.
- Whether pushing into the soldier priority vectors is enough to make it use the tactics.
- Whether a client sees bot-triggered cops (needs a two-seat graded run with a client-side census).
---

# Research 3: lobby map list
**Report: expansion map names on the multiplayer screens.** All offline and read-only: I read the code, the notes and the last session of `KLHook.log` (from line 104580). I did not launch kl2.exe, write to the game folder, or run kl_solo_test or kl_autotest. I did not disassemble kl2.exe myself. Every exe address below comes from `klhook/kllocname.c` and `re/lobby_map_names.md`. The 10-24 run plus the 22:08:08 log line of this session confirm that the LOC hook installs and its code check passes. They do not confirm what the lobby does with an override.

**Current behaviour (CERTAIN, from the log and the live `KLHook.ini`)**
- The live ini has no `[Names]` section, so Enable=0 and Override=0. There is no `[MapPool]` section either.
- The "12 name(s) for 21 rule(s)" line is the read-only mode. The names come from `[Page.2]` and `[Page.3]`. They are only used by `OnlineIntroMapName=1`, which is the intro card.
- At 22:08:08 the LOC object was wrapped (`names: LOC object 0ec2d7d0 ... slot 0 = 004099d0 ... Override=0`). Nothing is renamed on the lobby, the map list or the server list.
- Your session was a Private Match (`XBoxLiveCreatePrivate > FALobby`), host role, `OnlineSet=9` (random). The service vtable was `00bd5ad4` (the System Link / Wintel class), and the log said "seed lobby 0000000000000000 (NOT readable: fixed pick) ... round 1".
- So the lobby still shows the stock slot title: "Subway" for F01 and so on.

**How the screens get their text (CERTAIN)**
- Name text:
  - The FA lobby builds the key `Menu/Online/Scenarios/Title%02i` from slot+1 (0x436762, 0x5b6a25, 0x62b1a5, 0x631995).
  - The lookup goes through the LOC object `[[[0xdd2640]+0xac]+0x94]`, vtable slot 0 (thiscall, three stack arguments, `ret 0xc`). It is called from 0x47d8c0, and `0x490730` is slot 24 of the focus element.
  - The Arcade selector, the filters and `online.xml` use the same key through the XML `Text` paths.
  - The title therefore follows the slot, never the map file loaded into it.
- Picture:
  - It comes from `LobbyPictureF01..F09`, which map to the frontend-scene entities `LevelPicture_F0k`, shown through a toggler on `MP_SelectedLevel`. The pixels are in `kaneandlynch.TEX`.
  - There is no safe live swap. The hook module `klhook/kllocname.c` (prefix `kllnm_`) handles names only.

**Root cause**
- **Why Override is 0:** the history in `open_work_log.md` shows it was never turned on by choice. On 10-24 PD2 ran Override=1 with 0 faults, but it only saw page 1 (the stock Subway), so the renamed list was never seen. Nothing says it crashed or misbehaved. The Override=1 live check from `lobby_map_names.md` was never done.
- **Why Override=1 alone would not fix your session:** `kllnm_name_now()` (kllocname.c:129) asks `kls_page_now()` for the page. With `OnlineSet=9` that is 9 (klslot.c:233). `kls_find_rule(s, 9)` finds no rule, so it falls back to the page-0 rule, which is DD0x and has no name. The result is 0 and the stock title stays.
- **Why the lobby cannot show the real map today:** the random pick is only made at load time, in `kls_rand_pick` (klslot.c:342, called at line 471). It advances a round counter, so it is not safe to call from a text lookup. In your session it also depended on that round counter, because the lobby id was zero. The lobby cannot know which map comes next.
- **Fixed-page sets** (`OnlineSet=2` or `3`) would work with just `[Names] Enable=1 Override=1`. That is a GUESS that the lobby asks again when the slot changes; it was not seen live.

**Map-pool icons**
- `re/map_pool.md`, 10-27, built and never run live:
  - `tools/kl_mappool.py` makes one static grid picture per pool, used for all nine slots.
  - `klmappool_ov.c` draws a Direct3D thumbnail strip over the lobby. It is off by default and needs `[MapPool] Enable=1 Pool=n Overlay=1 OverlayDir=...`.
- `tools/kl_lobbynames.py` and `kl_lobbynames_install.py`, 10-25:
  - They make static per-set lobby names and pictures: `set2`, `set3`, and `rand` (a 2x2 collage of the stock picture plus the page 2/3 maps).
  - A set was installed once and taken out again. It stays installed for Quick Match too, so stock maps would show Dead Men names there.
  - Other languages get the English names.
- I did not check whether any of it is installed now.

**Minimal fix**

1. Ini only (fixed-page sets):
```
[Names]
Enable=1
Override=1
Log=1
```
This is enough for `OnlineSet=2` or `3`. The names come from `[Page.N]`. The ini needs `[Expansion] Enable=1`. Every peer needs the same ini, because the host's set is applied to the client in memory by klhostopt.c:267 and the map choice is not sent otherwise.

2. For `OnlineSet=9`, change `kllnm_name_now()`: in the `page == KLS_RANDOM` case, do not look up a rule. Return a fixed label built from the slot's stock title and the page 2/3 names. Examples are "Subway / Hot Coffee / Last Call" for F01 and "Docks / Late Night Opening / A Walk in the Park II" for F02. (Those stock titles are placeholders, since I did not look up the real LOC strings; the code gets the real one from the original lookup.)
   - Rules: a static buffer per slot, 47 characters at most and plain ASCII, as at kllocname.c:285-290.
   - If a label is too long, fall back to "<stock> / Dead Men".
   - This needs no prediction and no state change. It is honest about the random mode.
   - Do not call `kls_rand_pick` from the lookup. It changes the round counter.

3. Pictures:
   - For the random set, `kl_lobbynames` `--set rand` (the collage) matches. It is a data install, so the owner has to do it.
   - Per-map pictures need a `Patch01` / `kaneandlynch.zip` change (the data route, not hook code), or the `[MapPool]` overlay.

**Risk**
- The hook itself is low risk. It is a private vtable copy with no `.text` patch, and it has run in the PD1 (Override=0) and PD2 (Override=1) runs and in this session without faults.
- The name text must stay plain ASCII with no `%` and no leading `/`, which the init at kllocname.c:285-290 already enforces.
- The unproven part is whether the lobby label re-asks the lookup when the slot changes (menus.md 4.2). During the 10-27 MPX bench the lobby label stayed "Hot Coffee", but that run also had `LobbyName` and `Override` off. So it proves nothing either way.
- The static picture installs affect Quick Match.

**Live test (host and client, two seats)**
- Set the ini above, plus `OnlineSet=2` first. Then do the random-set variant after step 2 is coded.
- Run Online, then Private Match / System Link, then the FA lobby. Step the map (F01 through F09) and take a screenshot of each lobby slot on host and client.
- Also shoot the Arcade list and the search filter.
- Expected log lines: `names: lookup AllLevels / Menu/Online/Scenarios/Title01 -> 'Hot Coffee' (OVERRIDDEN)`.
- Check three things: the client's label matches the host's, Quick Match still shows the stock names, and there are 0 faults.
- Pause live runs while you are playing.

Relevant files:
- `C:\kl-merge\kl-merge\klhook\kllocname.c` (lines 129-165 and 270-305)
- `C:\kl-merge\kl-merge\klhook\klslot.c` (lines 233, 277, 342, 469)
- `C:\kl-merge\kl-merge\re\lobby_map_names.md`
- `C:\kl-merge\kl-merge\re\map_pool.md`
- `C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLHook.ini`