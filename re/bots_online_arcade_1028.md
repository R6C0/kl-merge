# AI heisters online vs Arcade (T3 research, 2026-10-28)

Static research only. CERTAIN = seen in code, log or disassembly. GUESS = inferred, not verified.
Addresses are kl2.exe (base 0x400000). Nothing was installed, run or committed.

## 1. Why bots "dont do much" online

1. CERTAIN. Stock online has no bot brain. 0x7f6850 ("Arcade?") is false for roles 2/3. The ZSoldier ctor (0x6ab250) builds
   ZLootTactic, ZBoardEscapeVehicleTactic and ZBecomeTraitorTactic ([soldier+0x5f0/4/8]) only when it is true.
   Census in Q27_DD08/DD06/DM07 host logs: "7 team Ally, 0 with tactics".
2. CERTAIN. No crew records online. Rules slot 198 online (0x832930) keeps a 0x74-byte table of 12 seats; Arcade's (0x588980)
   makes the 0x7c-byte crew record at [rules+0x348]. Every Arcade-only module that reads crew records is inert online.
3. CERTAIN. Trigger boxes ignore bots online. ZTriggerBox2 update 0x626ec0 (vt 0xbc953c slot 25) calls 0x7f6850 at 0x626f92 and only then
   accepts a team-Ally actor as activator (0x626fb2). With byte [box+0x44] ("people only") set, a non-player visitor is skipped.
   Same pattern in ZOnlineTriggerBox 0x49ab90 and ZTriggerBox 0x42afd0. So cop waves, doors, beat boxes, speak triggers are never fired by
   bots. The only special case in the hook is the ramp (OnlineRampFire).
4. CERTAIN. Bot money take does nothing online. ZOnlineMoneyCtrl slot 26 (0x6cdb40) with 'AI_TRIGGER_WITH_ACTIVATOR': online the branch at
   0x6cdbd0 needs a ZFFPlayer activator (0x7aace0); with a bot it returns 1 and does nothing. Arcade goes to rules slot 201 (0x56f6e0) then 0x8e8750.
5. CERTAIN. The hook's loot tally is host-only. klbotfill.c OnlineTactics: with OnlineTacticsTake=0 stacks stay on the map; with 1 it writes
   a raw 0 to [stack+0x34] on the host only (klbotfill.c ~698): no hide, no state 3, clients not told, no score, no "loot started/depleted" trigger.
   The HUD (klonline_read.c klor_loot) sums +0x34 but bot money is not exported.
6. CERTAIN. Online ZFFActor hit (0x61a980) skips Arcade's police-to-crew damage table (0x591b60); the hook substitutes OnlineHealthMul / OnlineCopToBot / OnlinePointBlank.
7. CERTAIN. Clients run no tactics: orders (ZSoldier 0x760e50 MoveTo) are dropped on a client. Bots reach clients via DDL_ZFFActor and KLSY2 (klsync.c, UDP 27415).
   Exact replication of hide/board on clients is GUESS.
8. CERTAIN. The squad route (ZSquadScript slot 14, 0x7b3790) drops a member lacking mask bit 1 online; bot squads are eHeistOnly(8). The data route
   (tools/kl_botsonline.py + F0n_Main.bots.zip, klslot.c "botgate") is what puts bots in; a runtime byte pass is dead (squads collected at load).

## 2. Per-module table

| Module | Arcade | Online | Gate | Why |
|---|---|---|---|---|
| klbotfill OnlineFill / OnlineHost | n/a (Arcade has its own squads) | runs, host only | [Bots] OnlineFill, [BotFill] OnlineHost | CERTAIN, benched |
| klbotfill OnlineTactics (loot/van/waypoints/health) | n/a | host puppeteer, benched | [BotFill] OnlineTactics, Take, Carry, Near, Board | CERTAIN. Tally only, see sec. 1.5 |
| klbotdown | down/adrenaline/revive via crew records | host path: down state only, no revive/adrenaline | [Down] OnlineBotDown=1, role 2 Sv rules, state 0x13..0x1f | CERTAIN |
| klcrew / klcrew_rt | random look, voice, name per crew record | inert ("vtable 52513af4, not ZGameRulesHeist") | klr_arcade() | CERTAIN |
| klgrudge | backstab/traitor via ZBecomeTraitorTactic 0x79b7c0 | inert | klr_arcade() | CERTAIN |
| klhop | hop teleports | inert | klr_arcade() | CERTAIN |
| klcardown / klcdying / klshield | car downs, dying, shield | inert | klr_arcade() | CERTAIN |
| klescort / klcopsquad / klfedkit / klbot | escort follow, C&R squads, kits, crew traits | inert | klr_arcade() (klbalance.c:414) | CERTAIN |
| Board / exit | Arcade ZBoardEscapeVehicleTactic | ZOnlineExitLevelTrigger 0x6c3d50 uses 0x7f6850, bots not counted; hook uses OnlineBoard (0x89c890), OnlineVanHold, OnlineBoxForce | [BotFill] | CERTAIN; DD08 4/7, DD04 3/7, DD05 6/7 boarded |

## 3. Ranked gaps (owner value / risk)

### G-A. Bots fire trigger boxes online (cops/enemies spawn from AI heisters)  [CERTAIN cause, GUESS fix behavior on client]
Directly answers "trigger the cops or enemies ... from the ai heisters".
Change (klbotfill.c, host only, new tick next to the ramp code): walk the entity table for ZTriggerBox2 (vt 0xbc953c), ZOnlineTriggerBox, ZTriggerBox (vt of
0x42afd0). For each live bot (klbf_oh list) test inside with 0x68d030; if inside and box is people-only, honour delay [+0x48], then call fire slot 34
(ZTriggerBox2: 0x557820(visitor); ZTriggerBox: 0x45f5d0). One-shot byte +0x45: latch per box per round (set of box ptrs, cleared at round start).
Exclusions: boxes whose target list holds a ZOnlineMoneyCtrl, exit/escape triggers, the ramp boxes OnlineRampFire owns, ZLevelBound (0x62e1b0).
Toggle: `[BotFill] OnlineBotTriggers=1  ; (recommended on)`, `OnlineBotTriggersDry=0` (log only).
Risks: client boxes also run locally (GUESS) so a player-fired and bot-fired box could double-fire; one-shot latch mitigates. Message ids sent to targets are
host-side game logic, so spawned cops replicate through the normal actor path (GUESS).
Proof: log `botfill: trigger: bot N in box 0x... msg 0x... fired (delay D)`; host census "ZFFActor" count rises and the client census follows; no repeat for one-shots.

### G-B. Real stack depletion for bots  [CERTAIN function, GUESS replication]
Call the game's own depletion 0x4e3f40 (this = ZOnlineMoneyCtrl, 1 stack arg = part) on the host instead of writing +0x34. It does `[+0x34] -= part`; at <=0 sets 0,
and when host test 0x8df480 is true hides the node (0x4bf120, session-handler vtable +0x138) and sets state 3, then calls 0x7f3110. Likely network-replicated hide (GUESS).
Toggle: `OnlineTacticsTake=2  ; (recommended on after bench)` (0 off, 1 raw write kept, 2 game path).
Risks: item state 2/3 refusal, DROP type (+0x38==1) handling, stack gone for humans (intended, same as Arcade).
Proof: `tactics: bot N GRABBED stack ... via 0x4e3f40`; sync Probe "moneycontainer" equal on host and client (kl_syncdiff.py); klor_loot totals equal.

### G-C. Bot loot and escape accounting visible to all  [GUESS on format]
Export klbf_ob[].tally (klbotfill.c) and show it in the HUD crew rows (klonline_read.c / klhud). Needs a host-to-client carrier: extend the KLSY2 record or the HostOpts packet (GUESS).
Toggle: `[BotFill] OnlineTallyHud=1  ; (recommended on)`. Proof: client log `online read: CLIENT ... bot money N` equal to host `round summary ... total`.

### G-D. Random AI heister looks, names and voices online (klcrew parity)  [GUESS]
Host picks a seed, shares it (HostOpts); every peer applies the model with 0x783fb0(actor, model) and variant 0x88c810 to bots by slot. Not yet seen working on actors online.
Toggle: `[BotFill] OnlineLooks=1  ; (recommended on)`. Medium risk (model mismatch crashes). Proof: both seats log the same model per slot, 0 faults.

### G-E. Escort/follow, BoardAll, FollowOut parity  [GUESS]
Extend the puppeteer (gather/hold exist). Low-medium value, medium effort. Toggle `OnlineEscort`.

### G-F. Down/revive/adrenaline, cardown, cdying, shield parity  [GUESS]
Needs a crew-record substitute (hook-owned per-bot struct). Higher effort. Toggle per module.

### G-G. Traitor/backstab/grudge  [CERTAIN blocker]
ZBecomeTraitorTactic needs the Arcade brain; recommend leaving off online.

### G-H. Known bot failures  [CERTAIN from benches]
Waypoint legs timing out, partial boarding (DD04 3/7, DD05 6/7, DD08 4/7), van holds. Tune OnlineBoxForce / OnlineVanHold and re-bench per map.

### G-I. Config hygiene  [CERTAIN]
Every new key carries "(recommended on/off)" in KLHook.ini and Mod Options. Menu table nearly full (~4994/5000 per notes): prefer ini-only plus one Mod Options row for the group.

## 4. Bench recipe (2 seats + bots)

kl_solo_test two-seat flow (inst1 host, inst2 client) on DD08, DD06 and DM07 (maps with a bots.zip), `[Sync] Probe=1`, `[Net] Log=1`, `[Online] Read=1`,
bench ini has an [Auto] section (appended [Script] replaces the script: edit the wait line in place), KLShopPage.ini copied into solo/<TAG>/inst1+2.
Run only when the owner is idle (or --owner-away). Proof lines:
- host: `botfill: OnlineHost HOST ... 7 Ally`, `tactics: ... GRABBED`, `tactics: round summary`, new `trigger:` lines (G-A), `via 0x4e3f40` (G-B)
- client: `online read: CLIENT ... N bot(s)`, `sync: vs host: N actors compared ... 0 farther than Tol`
- both: `botdown: ... ONLINE`, 0 faults. PASS = no faults, client census equals host, loot remaining equal on both peers, bot-fired boxes spawn cops seen on both.

## 5. Open questions
1. Do client-side trigger boxes also fire locally for bots (double fire)? 2. Does 0x4bf120 replicate the hide? 3. Is 0x8df480 true on the Sv host?
4. KLSY2 extension format for tally/looks. 5. Whether OnlineBoard's 0x89c890 removal shows on every screen. 6. ZLevelBound meaning of its 0x7f6850 test.
