# OnlineTriggersExtra: status, per-map assessment, one bug (2026-11-06, n9 parity gap 4)

Static work only: level zips read read-only (`tools/kl_trig_census.py`), logs of old benches read, no game started, nothing installed.

## 1. Status correction (the parity plan is stale)
`re/bot_parity_plan_1028.md` gap 4 says OnlineTriggersExtra "has not been proven". It has, as a SAFE run:
- TP2A, DM03, 2 seats, 2026-11-02 13:12 (`G:\...\KL_PortTools\build\klhook\solo\TP2A_DM03\inst1\KLHook.log`): 47 boxes tracked (ZTriggerBox 18, ZTriggerBox2 25, ZOnlineTriggerBox 4), 300 loot-stack boxes + 18 pick-ups left alone. FIRE lines: ZOnlineTriggerBox x4 (delays 0/2/3/5, fire #1-#2), ZTriggerBox2 via slot 34 (about 10 boxes, fire #1-#3) and via the delay fields (54c62da0, delay 5, one-shot). 4/4 seats RESULT PASS, asserts 0, faults 0.
- What is NOT proven: that a bot-fired Extra box brings cops in. Census never rose (DM03 21 flat; the crew kills faster than a wave arrives).
- ZOnlineMoneyCtrl is NOT touched by OnlineTriggers or Extra at all (neither scan collects it). Bots bank through OnlineBank/OnlineBankCredit/OnlineTactics (re/bots_online_scorecard_1101.md). So "money ctrl double counting" cannot come from the trigger code; the only money-adjacent risk is a TB2 pick-up box (section 3).

## 2. Per-map assessment (census of the level zips, kind = keyword guess on names)
Stock (DD01-09 = slots F01-F09, zips in `<DD>\Scenes\Locations\Fxx\`): ZOnlineTriggerBox 0 everywhere; players-only non-loot ZTriggerBox2 = 0 everywhere (F03 has 12 civ/npc interact boxes, F09 has 6 all-objects boxes the game already fires). So Extra is idle on stock maps. OnlineTriggers (plain ZTriggerBox, the F06-proven part) covers the missed boxes: F01 9, F02 16, F03 7, F04 6, F05 5, F06 14, F07 4, F08 8, F09 7. F09's 3 wave boxes (WaveOne/Two/Three, one-shot, Timer targets) and F08's SWAT_A/B/Stairs/Roof one-shots are the ones that start cops: all `-1` one-shots, fired once per round, so no wave stacking.

Dead Men grafts (installed slot zips under `<DD>\KLExpansion\Maps\`): where Extra has work.
| Map (slot) | ZOnlineTriggerBox (players-only) | TB2 players-only non-loot | TB2 loot-kind | Verdict for Extra |
|---|---|---|---|---|
| DM02 (F02) | 2: PoliceSwats_01 (sends HuntBehaviour/VehicleMove), PoliceSwats_02 | 1 npc (CreditCard_01 interact) | 378 | useful: the swat arrival is only reachable by Extra. Risk: 378 pick-up boxes, SkipPickups must be on |
| DM03 (F03) | 4: ArrivingCops_Squad_01/02/03 (VehicleEnter + PoliceCarArriveSound), GarageDoors | 2 civ (clerk, bank civilian), 1 script GarageDoors (one-shot, door anims) | 340 (332 + 8 `MoneyBox_NN\Attach01`) | useful: arriving cops and the garage door. Proven safe in TP2A |
| DM01, DM01B, DM03A, DM05A, DM06, DM06B, DM07, DM09, DM11B | 0 | 0 | 133-302 on DM01/DM05A | Extra not needed; leave 0 (it would only add pick-up risk). Plain OnlineTriggers=1 covers their cop/door boxes |
Dead Men ZTriggerBox misses (OnlineTriggers=1 territory): DM01 10, DM01B 30, DM02 0, DM03 16, DM03A 11, DM05A 46, DM06 3, DM06B 24, DM07 3, DM09 22, DM11B 5 (table in `re/bots_trigger_cops_1028.md` section 8).

What firing could break:
- Wave starts: ZOnlineTriggerBox is not one-shot (the game re-fires it on every human entry edge). With bots flapping on the edge it fired twice in 3 s (TP2A: 54af3490 at 13:15:32 and :35, delay 0). Hook cap is 3 per box per round. ArrivingCops_Squad_N fired twice means two car arrivals possible; no flood was seen (cops 21 -> 15 over 30 s). Accept; if the A row shows more than the 3 cars, add a cooldown (not built, no evidence).
- Gates: GarageDoors OTB + TB2 are door scripts; opening early is the same as Arcade (a bot counts there). The exit trigger is never fired (`klbf_ot_trig` guard).
- Double count: the `MoneyStack`/`DropMoney` TB2 are skipped by name; pick-ups by SkipPickups. See the bug below.
- Client: the OTB fire sends net event 0x642f20 through the box's own delay; TP2A client seats had no assert.

## 3. Bug found: SkipPickups misses `Attach01` money boxes (fixed, default OFF)
TP2A kept three boxes named `Attach01` ("kept ... 'Attach01'") and fired them (fire #1-#3 on 54b12810, 54b128b0, 54b12d70, 54b13780...). The scene-node name is only the leaf. The census shows the DM03 map has 8 `Garage_01a\PC0500_M03_MoneyBox_NN\Attach01` TB2 boxes (the pick-up boxes of the money boxes), so `kvp_pickup_box` (which does match the full path, test at klgetup_test.c line 94) never saw the `PC0500_` segment. A bot firing a pick-up box posts 'AITrigger' to its target list: possible phantom pick-up / a second grab on a stack the tactics module already took.
Fix (all default 0): new key `[BotFill] OnlineTriggersAttachParent=1` (needs Extra + SkipPickups). When the node name is `Attach` + digits, the hook reads the parent node (`[node+0x50]`, name at `+0x6c`; GUESS, the parent link klmove.c klmv_frame walks) and judges `<parent>\<name>`. Code: `kvp_attach_leaf`, `kvp_join_parent` in klhook/klgetup_logic.h; use in klbotfill.c klbf_trig_scan; ini line + doc in klhook/KLHook.ini; options row `onlinetriggersattach` (off, "recommended off until benched") in tools/kl_mod_options.py. Tests: klgetup_test.c (bare leaf kept, leaf test, join, truncation, non-pick-up parent kept). `python tools/kl_tests.py`: RESULT PASS - 81 pass, 0 fail, 5 skip.
TEST dll built (cl, not installed): `C:\kl_build_1024\n9_1106\out_trig_test\dinput8.dll`, sha1 d881da8b7b7ccd0a1dce0c3629e524835ba93518. It carries the working tree of the repo at 2026-11-06 (including other sessions' uncommitted klhook edits), so use it only as the A/B bench dll, not as ship.

## 4. A/B overlay and proof patterns
Overlay: `C:\kl_build_1024\n9_1106\overlay_triggers.ini`. Maps: DM03 (F03 page 2) and DM02 (F02 page 2), host seat ini only. Row A = Extra 1 + SkipPickups 1 + AttachParent 1 + Census 1; row B = same ini with Extra/SkipPickups/AttachParent 0.
Grep on the host KLHook.log (patterns):
- init, A: `botfill: trig: OnlineTriggers=1 .* OnlineTriggersExtra=1`; `OnlineTriggersSkipPickups=1`; `OnlineTriggersAttachParent=1`. B: `OnlineTriggersExtra=0`.
- scan: `botfill: trig: scan 1: .* tracked \(ZTriggerBox [0-9]+, ZTriggerBox2 [0-9]+, ZOnlineTriggerBox [0-9]+\)`. A on DM03 expects ZOnlineTriggerBox 4, pick-up count about 326 (318 in TP1); DM02 expects ZOnlineTriggerBox 2. B: ZTriggerBox2 0, ZOnlineTriggerBox 0.
- the fix worked: `name joined with its parent node: 'PC0500_M03_MoneyBox_` (DM03) and NO `kept .* 'Attach01'` line; the tracked ZTriggerBox2 count drops by the 8 (TP2A 25 -> about 17). Old dll: `kept ... 'Attach01'` still present.
- fires: `botfill: trig: FIRE ZOnlineTriggerBox` (DM03 ArrivingCops/GarageDoors, DM02 PoliceSwats), `FIRE ZTriggerBox2`; none above `fire #3`: `grep -c "fire #[4-9]"` must be 0. B: 0 FIRE ZOnlineTriggerBox / ZTriggerBox2 lines (plain `FIRE box` lines are OnlineTriggers and stay in both).
- no pick-up fired: `grep "FIRE ZTriggerBox2"` addresses must not be any address in `left to the game` lines; also compare banked $ A vs B (in the range of the TP1A/CS1A runs).
- effect (first time): `trig: census after FIRE <box>`: more cops at +10/+30 s than at the fire = a wave came (Arcade-like). Also `grep -E "ASSERT|FAULT|fault"` 0 on both seats.
PASS: both seats RESULT PASS, asserts 0, faults 0, the join line present, no Attach01 kept, no fire #4. FEATURE: a census rise or visible arriving police cars after an OTB fire.

## 5. Open risks
- Parent link `[node+0x50]` and name `+0x6c` are a GUESS (klmove.c uses +0x50 as the parent for placement; the +0x6c name on a parent is the same field kle_node/klauto read). If the join line is missing in the A log, the parent read failed and Attach01 boxes stay kept (no worse than today).
- Cops arriving from OTB boxes were never seen to rise in the census; the proof may stay "safe, effect small".
- The parity plan's claim "OnlineTriggers proven on F06 only" is also stale: Q34/Q31/CS1/pqq runs fired boxes on DD01, DD05, DM03, DM06, DM09.

## 6. Next live step
Game must be free. In the n9 kit run DM03 then DM02 as A and B pairs (host ini = base + overlay section A / B), 900 s each, TEST dll `out_trig_test\dinput8.dll`; grade with the patterns in section 4; only after a PASS flip `onlinetriggersattach` to "recommended on" and consider Extra=1 + SkipPickups=1 + AttachParent=1 for DM02 and DM03 only.
