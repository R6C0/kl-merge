# AI heisters: Arcade round vs online round as host, what still differs (wk-gap2, 2026-10-28)

Static research, nothing run, nothing installed. Reads re/bots_online_arcade_1028.md, re/arcade_mods_online_1028.md, re/bot_parity_plan_1028.md, re/bots_loot.md
and the code in klhook/. CERTAIN = seen in code or a doc that cites a disassembly address. GUESS = inferred. Addresses are kl2.exe (base 0x400000).

DONE today and therefore NOT in the list: OnlineTriggers(+Extra), OnlineTacticsTake=2 (game depletion 0x4e3f40), OnlineBank/BoardAll/BankCredit, OnlineLooks,
OnlineGuardWalk/Escort/WalkReach, OnlineLootSync, klhop and klcardown online paths, OnlineBotDown (down state + lie), OnlineCopToBot / OnlinePointBlank / OnlineHealthMul.

## Remaining differences, ranked (value for "behave and loot exactly like Arcade", host-only?)

| # | Difference | Evidence | Host-only fix, no new net message? | Effort | Risk | Verdict |
|---|---|---|---|---|---|---|
| 1 | **A bot takes a stack in ONE instant lump; Arcade takes it in timed parts while the bot STAYS in the trigger.** Arcade: rules slot 201 (0x56f6e0) -> 0x8e8750 starts a part clock = stack `+0x44` x tuning `+0x624`; every part (stack `+0x40`, or what is left) is paid through 0x4e3f40 and the crew money grows part by part; leaving the trigger resets the clock, a dead bot stops where it was (re/bots_loot.md section 1, table rows "the start", "every tick", "a part is paid"). Online: klbotfill.c:1112-1116 adds the whole `amt` to the tally and calls 0x4e3f40(o, amt) the moment the bot is within Near (150) of the stack, then picks the next stack the same tick. Consequences: online bots clear a room several times faster than Arcade, are never caught standing at a stack (cops/humans can not interrupt a grab), a bot killed on the way never "half-looted", stacks vanish instantly for the human who is running to them. | klbotfill.c:1105-1117 (reach branch), re/bots_loot.md:66-74, 83-93 | YES. Same game call already used (0x4e3f40), host-only tally already exists, stack fields `+0x34 +0x40 +0x44 +0x64 +0x6c` are already read by this module. The clients see the stack shrink through whatever replication 0x4e3f40 already has (LootSync/OnlineTacticsTake=2 benches: matched). | Small (one new phase, about 60 lines in klbotfill.c, 1 ini key) | Low: all-or-nothing fallback to today's lump when a field reads implausible | **BUILD THIS (spec below)** |
| 2 | Bot hits/combat tuning: Arcade `[Balance]` YouToCrew / CrewToYou / the range sponge / Tough read klb_read and stay off online; online has only the three Online* damage keys. | klbalance.c:505, 564, 762 (all `!klb_read(...) return`), 1034 (OnlineCopToBot) | Partly: the hit-scale detour for cop->bot exists; a "bot->cop" and "human->bot" scale would be the same detour pattern. Needs the attacker identity in the hit record (+0 = attacker, GUESS from klbotdeath.c id1). | Medium | Medium (balance feel, hits are replicated) | Next after #1 |
| 3 | Revive / adrenaline / get-up help for a downed bot (a human or another bot helps it up). Online bot lies LieSeconds then rises alone. | klbotdown.c:285 ("MISSING"), :411 log "no adrenaline / revive"; bot_parity_plan_1028.md gap 9 | NO for the human helper (revive is master-routed through 0x9425a0, human down state is per peer). A bot-helps-bot rise could be host-only but has no Arcade-evidence of being worth it. | High | High | Not now |
| 4 | Loot of a dying bot: Arcade loses it (0x5e2230 skips dead/police when `[0x168e59c]==1`); online the slot is freed with the tally (klbotfill.c:1091) and the money is already off the map: the same loss, but the dead bot's tally also leaves LootSync/bank (checked: matches Arcade). | klbotfill.c:859, 1086-1091 | n/a, already equal. After #1 a dying bot loses only the PARTS already paid (as Arcade). | - | - | No work |
| 5 | Random look/name/voice per bot: look DONE (OnlineLooks); voice/banter and names still absent (speech takes a crew-record index, `rules+0x33e+slot` byte). | klcrewlook.c:29 ("Voice, Names ... NOT touched online"), re/bots_voice.md section 0.3 | Voice byte write at rules+0x33e is host data but each peer plays its own speech: needs the byte on clients (no carrier). | High | Medium (int3 at 0x51ab2d if the group digit is bad) | Blocked |
| 6 | Traits (kltrait ReviveTime etc.) per bot: getter returns 1.0 online. klbotdown.c:500 ("online: the pseudo record is no wardrobe record, no trait"). | klbotdown.c:500 | YES technically (host picks a trait from the OnlineLooks character) but affects only lie time/speed, low owner value. | Medium | Low | Later |
| 7 | Fed kit (police human kit, AK chance): human feature, Arcade fed player only. | klfedkit.c:798 gate | NO (human, per peer) | High | - | Skip |
| 8 | Traitor / backstab / grudge / bribe the driver. ZBecomeTraitorTactic needs the Arcade brain. | klgrudge.c:430, bot_parity_plan 10 | NO | - | - | Skip (also bad for co-op) |
| 9 | Escape: ZOnlineExitLevelTrigger counts no bots; hook boards by teleport/crowd. 7/7 in DD04c/F06 benches. Stage/status byte 4 "ABOARD" does not exist (no records). | klbotfill.c OnlineBoard*, bots_online_arcade_1028.md section 2 | Done as far as host-only goes. | - | - | Done |
| 10 | Cover: the game's own combat AI does cover for team Ally actors online as well (no hook part in Arcade either: grep "cover" in klbot/klbalance/klbotfill finds only a comment). | grep, klbotfill.c:1329 | n/a | - | - | No difference found |
| 11 | Cop squad (C&R) and klcrew_rt jump follow: Arcade-only by design. | klcopsquad.c:22-33, klcrew_rt.c:67 | NO | - | - | Skip |

## Why #1 is the pick
It is the only remaining difference that changes the whole shape of every online round (loot pacing, exposure, what a human can still reach), it needs no message,
no record and no new game address, and a failure mode (bad stack fields) falls back to the proven lump grab. #2 needs unverified hit-record offsets, #3/#5/#7 need
peer state, #4/#9/#10 are already equal.

## BUILD SPEC: OnlineLootParts (timed parts, bot must stay at the stack)

Key: `[BotFill] OnlineLootParts=0|1|2` (default 0). 1 = on, 2 = dry (log only, grabs stay lumps). Needs OnlineTactics=1 and OnlineTacticsTake=2 (with Take 0/1 it logs once
"OnlineLootParts needs OnlineTacticsTake=2" and stays off). Second key `OnlineLootPartScale=1.0` (float 0.1..4.0, multiplies the part time; GUESS for the tuning object's
`+0x624`, which nobody has read in a live run; 1.0 until a debugger dump says otherwise). Third key `OnlineLootStayM=250` (cm, 80..800: how far the bot may drift from the stack
before the clock resets; Arcade's ball is trigger radius + 40, field 2 of the trigger, which is not read here).
KLHook.ini comment (exact style): `; OnlineLootParts (recommended off until benched; needs OnlineTactics=1 and OnlineTacticsTake=2; HOST only): an AI heister takes a stack in timed parts while it stands at it, like the Arcade loot rule, instead of all at once.`
Row in tools/kl_mod_options.py: "AI heisters loot in timed parts like Arcade (recommended off)" -> `[BotFill] OnlineLootParts` (0/1). The other two keys are ini-only.
No .text patch: data reads, KLFC_CALL of 0x4e3f40 as already done at klbotfill.c:1115.

### Files and functions
1. `klhook/klbotfill.c` only (plus KLHook.ini, tools/kl_mod_options.py, and tools/kl_tests.py needs nothing).
2. Init block (klbotfill.c ~line 120-126, next to `klbf_ot_take`): read the three keys into `klbf_lp` (int), `klbf_lp_scale` (float), `klbf_lp_stay` (float). Log once in the OnlineTactics banner line (~204).
3. Struct `klbf_ob[]` (line 240): append `DWORD lootAt, lootTick; int lootPaid, lootPart, lootLeft; float lootSec;` (memset on slot free already clears them).
4. Reach branch, klbotfill.c:1105-1117. Replace the unconditional lump with:
   - after the existing state check (`st0` 2..3 refusal), if `klbf_lp == 1 || klbf_lp == 2`: read `part = [o+0x40]` (int) and `sec = [o+0x44]` (float).
     GUESS: field 4 at +0x40 is an int and field 5 at +0x44 a float (re/bots_loot.md:88 gives +0x44 float, :70 gives +0x40 as "field 4"); accept only `1 <= part <= amt` and `0.05 <= sec <= 10`;
     anything else logs `botfill: lootparts: stack %08lx fields implausible (part %d sec %f): lump grab` once per stack and falls through to the old lump code.
   - else set `klbf_ob[s].phase = 4; lootAt = now; lootTick = now; lootPaid = 0; lootPart = part; lootSec = sec * klbf_lp_scale; target stays o`,
     log `botfill: lootparts: bot %d starts stack %08lx (amt %d, part %d, %.2f s/part, ~%.1f s total)`, and `continue` (no tally yet). With mode 2 log `DRY` and run the old lump.
5. New branch placed after the `phase == 1` block and before the `phase == 0` block (same loop, same `bots[b]` data; the bot is already in range and its walk order has completed so it stands):
   ```
   if (klbf_ob[s].phase == 4) {
       DWORD o = target; int amt=0; BYTE act=0,st=0; float mp[3]; due;
       /* abort rules, each logs once: stack gone/hidden/freed (vtable != KLMV_MONEY_VT, amt<=0, +0x6c==0, +0x64 != 1) -> "taken by someone else", phase 0;
          bot farther than klbf_lp_stay (xz) or higher than 400 -> "left the stack", phase 0, partial tally KEPT;
          now - since > 60000 -> phase 0 (safety). */
       due = (int)((now - lootAt) / (lootSec*1000)) - lootPaid;      /* catch-up: the tick is ~1 s, a part is ~0.7 s, so several parts can fall due in one tick (the game's own clock does the same at 30 fps) */
       while (due-- > 0 && amt > 0) {
           int give = amt < lootPart ? amt : lootPart;
           KLFC_CALL(void (__fastcall *)(DWORD, DWORD, int), 0x004e3f40)(o, 0, give);     /* same call as the lump, thiscall(stack, remaining) */
           tally += give; lootPaid++; amt -= give;                    /* re-read [o+0x34] after the call to see the true remainder; use the game's number */
       }
       if (amt <= 0) { grabs++; claim o (klbf_ot_claimed) as the lump code does; log GRABBED with "(timed parts, N parts in X s)"; phase = 0; }
   }
   ```
   The tally increments feed the existing consumers unchanged (round summary, lootsync, bankcredit, klbf_ob_stage), so a dead bot loses only the parts already paid (Arcade: 0x5e2230 loses dead crew money).
6. Interactions to check in the same file: (a) `klbf_ot_gat` van-gather sets `phase = 2` for any bot with `phase < 2`: phase 4 is NOT < 2, so extend that test to `phase < 2 || phase == 4` (interrupt keeps the partial tally); (b) the dead/gone free pass (line 1086) frees phase 4 slots like others (partial tally lost = Arcade); (c) `klbf_ob_stage` returns 2 while `tally > 0` (fine); (d) the orders for walking use `phase == 1`; phase 4 sends no order, the bot stands where it reached (GUESS: the game's chain does not walk it off; if the bench shows drifting, re-issue the stand order with kle_order2 at the stack place every KLBF_OT_REORD).
7. Per-stack claim so two bots do not share one stack: the pick code already skips claimed/targeted stacks via `klbf_ob[].target` (phase 1 holds it); phase 4 keeps `target` set, so the existing "taken by another slot" test still blocks it (verify the test reads `target` regardless of phase; GUESS, check at klbotfill.c ~1140 when building).

### Log lines a bench can grep (host KLHook.log)
- `botfill: lootparts: OnlineLootParts=1 scale 1.00 stay 250` once at init.
- `botfill: lootparts: bot N starts stack 0x... (amt A, part P, S s/part, ~T s total)`
- `botfill: tactics: bot N (actor ...) GRABBED stack 0x... = A; its tally X after G grab(s) (timed parts, K parts in Y s)` (the old GRABBED text with a suffix, so existing greps keep working)
- `botfill: lootparts: bot N left stack 0x... after K of M parts (partial tally X)` / `stack 0x... taken by someone else` / `fields implausible`
PASS = every `starts` has a GRABBED or a left/taken line; Y is within +-1.5 s of T; a stack never reaches amt < 0; faults 0 asserts 0 on both seats; `round summary` total equals the sum of GRABBED amounts plus partials.

### Bench recipe
Two seats, TEST build (klhook\build_auto.bat, out_gap2_X_test), map DD04 or F06 (benches already exist: MV1_* and WKBC7_* inis in C:\kl_build_1024\week_1028\ as the base),
add to BOTH inis: `[BotFill] OnlineTactics=1 / OnlineTacticsTake=2 / OnlineLootParts=1 / OnlineLootSync=1`, `[Sync] Probe=1`. Run once with OnlineLootParts=2 (dry: lumps, but the `DRY starts` lines show part/sec read sanely on real stacks: this proves the field GUESS before anything is changed), then =1.
Compare against OnlineLootParts=0: time from round start to first GRABBED should rise, stack count shrinking over time (client log `sync: loot` steps in parts, not in lumps), bank total at the van unchanged within the bots that died.
Run only with the owner away or the game free (peer bench rule). Stop condition: any `fields implausible` on more than half of stacks means the +0x40/+0x44 GUESS is wrong: keep default 0 and dump a stack object.

### Not in this build
Busy-looting bit 0x2000 and the crew-record loot state (no records online); the tuning `+0x624` read (the scale key stands in); interrupting a looting bot when shot (the game's own combat takes over the soldier; a bot that dies is freed).
