# Arcade vs online AI heister gaps (ce workflow wf_3337ca36, 2026-10-28, static, NOT RUN)

# Gap list: Arcade vs online AI heisters

Gaps are ranked by owner-visible value per effort. Items marked GUESS come from the surveys and are unverified.

## Ranked gaps

| # | Gap | Value | Effort | Status |
|---|---|---|---|---|
| 1 | **Bots stand idle or stall.** Bots hold at round start (DD04 and DD08: "all with a live cop within 25 m", OnlineGuardTake). DD08 waypoint legs time out. Six DD04c bots "did not reach the exit trigger after 90 s". Boarding is rescued only by OnlineExitCrowd or OnlineBoardAll. | Highest. This is the "they don't do much" complaint. | Low. The keys exist and the work is tuning and defaults. | Partial |
| 2 | **No escort or follow online (G-E).** Online bots never stay near you. Arcade klescort has Escort, EscortFar 800 and EscortSide 300. | High | Medium. The order call already works online. | Not built |
| 3 | **Bot loot is invisible to clients (G-B/G-C).** The HUD loot sum is wrong, stacks do not deplete or replicate, and there is no loot-started trigger. | High | High. It needs a host-to-client carrier whose format is a GUESS. | Not built |
| 4 | **Triggers: bots ignored by ZTriggerBox, ZTriggerBox2 and ZOnlineMoneyCtrl.** OnlineTriggers defaults to 0. It was proven live on F06 (3 fires), but OnlineTriggersExtra has not been proven. | Medium (cop waves behave as in Arcade) | Low (flip the default per map, then bench). | Built, off |
| 5 | **Escape coverage.** Exit trigger 0x6c3d50 does not count bots. Boarding is only a host tally. DD08 reached 4/7 and DD05 6/7 early on, but later benches (DD04c, F06) show 7/7. | Medium | Low | Mostly done |
| 6 | **Host-side traits and grudge on bots.** The getter returns 1.0 online. klgrudge has no online path. | Medium-low | Medium | Not built |
| 7 | **Random looks, names and voices per bot (G-D).** OnlineLooks=2 is log-only. The wk-looks branch is pending and there is no carrier. | Medium. It is visual but a big job. | High | Probe only |
| 8 | **Bot banter, names, initials and scoreboard names.** Speech takes a crew record index. The name source is untraced. | Medium-low | High | Not built |
| 9 | **Get-up help, adrenaline, shield, dying floor.** | Medium-low | Blocked. It needs a "revive slot N" message to the owner's machine. | Not built |
| 10 | **Traitor, backstab, bribe, leave, van gameplay (G-G).** | Low | Blocked. | Not built |
| 11 | **Crew follows the Retomoto jump (klcrew_rt.c) and cop squad.** | Low | Arcade only, or Cops-and-Robbers only. | Not built |
| 12 | **Fed kit online.** | Low | Blocked. It needs the online seat table and the KLCH1 carrier. | Not built |

## Build plan 1: bots that move from the first second (Gap 1, plus Gap 4's default)

**Files:** `klhook/klbotfill.c`, the init block at lines 102-192, and `klhook/KLHook.ini`. There are no new functions at first.

**Changes:**
- **Default flips.** Turn on OnlineHost and OnlineTactics, and set OnlineLegStallS=10 and OnlineLegDy=300 (the values benches already use). Also set OnlineBoxLatch with BoxLatchM=1500, and OnlineExitCrowd=1600 (already default after b0bd5343c). OnlineBoxLatch and OnlineLegScale are marked "not yet run live" in the source, so bench them before defaulting.
- **Start-of-round hold.** In `klbf_ot_goal` (line 727) and the guard check, change the OnlineGuardTake behaviour. When every free stack is cop-guarded, the bot currently stands for up to 30 s. Instead:
  - walk to the nearest guarded stack and stop at the edge of OnlineTacticsGuard (25 m), or
  - follow the nearest human (plan 2).
- **Van reach.** The "did not reach the exit trigger after 90 s" cases are 6 to 32 m short. After 15 s on the walk leg, make a bot already past OnlineBoxSlack count via the existing crowd boarding, rather than going back to idle.
- **Waypoint legs.** In `klbf_way_*` (240/264), scale the leg timeout by length. OnlineLegScale exists for this.

**Game calls (all already used):**
- `kle_order2` wrapping 0x760e50 for orders.
- `KLFC_CALL 0x4e3f40` for take mode 2.
- 0x71e180 for the van call.

**New ini keys:**
- `[BotFill] OnlineGuardWalk=1` (recommended on): approach a guarded stack instead of freezing. Default 1 once benched.
- `[BotFill] OnlineTriggers=1` per map. Default 0 stays until the F06 result is repeated on a second map. Label "(recommended on)" only after that.

**Host vs client:** host only. Clients mirror through DDL_ZFFActor and KLSY2.

**SHIP constraint:** data writes and game-function calls only. There are no .text patches.

**Bench proof lines:**
- Host log: `botfill: tactics: round 1 starts`, with the first `GRABBED stack` at 15 s or less after round start on DD04 and DD08.
- No `all with a live cop within 25 m: it holds` line longer than 5 s.
- `round summary: N boarded` equal to the number of bots, with `faults 0`.
- Client log: seven `sync: puppet` lines, with positions moving in the first 20 s.

## Build plan 2: OnlineEscort, bots stay with you (Gap 2)

**Files:**
- `klhook/klescort.c`: kle_tick 1420, kle_pick 694, kle_hold 735, kle_place 724, kle_follow 1175, and the klb_read gate at lines 1118 and 1429.
- `klhook/klbotfill.c`: klbf_ot_run (line 885) and klbf_ob[].
- `klhook/klsync.c` for the human position.

**Changes:**
- Add a `kle_online_tick()` called from `klbf_ot_run` once per second, host only. It runs after the phase logic and only for bots in the "no goal" state: phase 0 with no stack, phase 3 boarded, or idle.
- It picks the nearest human, then calls `kle_follow` and `kle_order2` with record -1 and told_soft 1 (the puppeteer already does this). It reuses EscortFar 800 and EscortSide 300.
- The human's position comes from `klsy_humans` (klsync.c:353/366) or `klco_find_own` (klcharonline.c:140, table 0x6161c0). The host's own seat is trustworthy. A remote human's position through these is a GUESS, so fall back to the host seat if it reads zero.
- The Arcade escort keeps its own `klb_read` path unchanged.

**Game calls:** 0x760e50 through kle_order2, and the defend block at [soldier+0x64c], both already used online. There are no new calls.

**New ini key:** `[Bots] OnlineEscort=0|1|2` (0 off, 1 follow the host seat, 2 nearest human). Default 0 until benched, then 1. Label: "Bots stay near you when they have nothing to loot (recommended on)". Keep `OnlineEscortFar` and `OnlineEscortSide` as overrides, defaulting to 800 and 300.

**Host vs client:** host computes and orders. Clients see movement through DDL_ZFFActor (GUESS).

**SHIP constraint:** data and calls only.

**Bench proof lines:**
- Host log: `escort: online: bot N follows seat S (dist X cm)`.
- Distance from the bots to the host seat at most EscortFar plus 200 cm for 80% of ticks after clearing a room.
- No `kle_order2` refusals.
- Client puppet positions move toward the client's own seat, in a two-seat run where the client walks away.
- `faults 0` on both seats.

## Build plan 3: bot loot shown to clients (Gap 3)

**Files:**
- `klhook/klbotfill.c`: klbf_ot_summary (line 787) and the tally.
- `klhook/klsync.c`: a new event on KLSY2 (UDP 27415).
- The HUD reader for the loot sum, the HUD file for bot rows (klhud_board2.c). Its function is unverified.

**Changes:**
- The host already holds the tally. Add a KLSY2 event record, for example `{u16 kind=LOOT, i32 total, u16 taken}`. The format is a GUESS. Packets use 20-byte records today, so reuse that size and put the new kind in the `cls` field.
- The client stores the total and feeds the HUD loot sum and the bot rows.
- Stack depletion replicating through the game's own ZOnlineMoneyCtrl replication is unproven. Do not rely on it. Show the tally, not the depleted stacks.
- Do not write the game's score. The scoreboard stays untouched.

**Game calls:** none new. It is hook-to-hook UDP plus a HUD read.

**New ini key:** `[BotFill] OnlineLootSync=0|1`. Default 0, then 1 after benching. Label: "Show what the bots have looted on every screen (recommended on)".

**Host vs client:** the host sends, the clients receive and display.

**SHIP constraint:** no .text patches. Do not touch the bank credit (OnlineBankCredit) from here.

**Bench proof lines:**
- Host: `botfill: lootsync: sent total=X taken=N`.
- Client: `sync: loot total=X` equal to the host's `round summary ... total` at round end.
- The HUD sum matches within one tick, on both seats.
- `faults 0`.

## Gaps recommended NOT to build

- **Revive and adrenaline online (9).** The revive is master-routed through 0x9425a0, and the human's down state is local to that peer. There is no "revive slot N" message, and the host must not write a client's replica.
- **Traitor, backstab, bribe, leave and the van gameplay (10).** The blocker is certain. It would also hurt a co-op round for humans.
- **Bot banter and names on the HUD (8).** Speech takes a crew record index that online bots lack, and the name source is untraced.
- **Bot random looks (7).** The model is per-peer, so a host-only look is invisible to clients. Wait for the wk-looks branch and a carrier.
- **Fed kit online (12).** It needs the online seat table and KLCH1 carrier.
- **Cop squad (11, second half).** It needs a UDP order channel and has never run live.
- **OnlineBoardTeleport.** It is "NOT Arcade" and the source marks it so. Keep it at 0.
- **OnlineBoard=1.** Its effect is a GUESS, and the source recommends off until a live run shows the bot vanishing on every screen.

## Sources and gaps

- This list rests on the three surveys. The kl2.exe addresses are as the surveys cite them. Those marked GUESS above are unverified.
- Not covered: the client-side logs beyond the `sync: puppet` lines, the AM_DM09 bench, the bodies of klb_act, and the per-map OnlineTriggers defaults.

---
## Survey: Arcade behaviours

ARCADE BOT BEHAVIOURS AND ONLINE STATUS (worktree C:\kl-merge\wt\wk-merge, klhook/). Read-only research, nothing run or edited. The first group below is the shared gate; the numbered entries after it are the behaviours.

GATE (all Arcade parts)
- klbot.c:363 klb_read needs session mode [sm+0x5c]==4 and sub-role not 2/3. It reads the ZGameRulesHeist object (vtable 0xbd3514). klbalance.c:414 klr_arcade wraps it.
- Crew records start at [rules+0x348], 0x7c bytes each, with a free-byte array at +0x34c and the count at +0x354.
- Record fields: status +0x10, actor +4, stage +0x78 (1 entered the bank, 2 left with loot, 3 at the vehicle), flags +0x79 (bit 1 human/AI, bit 2 traitor).
- Other rules fields: money at score [rules+0x5f8]+0x150+4i, hit float at rules+0x884+4i, voice table rules+0x33e+i, vehicle state [rules+0x1dc], vehicle timer [rules+0x1d8], last-vehicle byte [rules+0x1ee], loot list [rules+0xdcc].
- Tuning record: 0x168d7c0+0x6ac+L*0x70.
- Soldier = [actor+0x77c]. Tactics objects are ZLootTactic at soldier+0x5f0, ZBoardEscapeVehicleTactic at +0x5f4, ZBecomeTraitorTactic at +0x5f8. They exist only when 0x7f6850 is true.
- Order call: soldier vtable +0x13c = 0x760e50. Down byte [actor+0x64c].
- Hook gameplay parts act only on a non-stock level (klx_level_verdict==2, klsteam.c).
- Online, 0x7f6850 is false. There are no crew records or tactics. The online rules objects are small (Sv 0x3a8, Cl 0x334), so reading +0x33e or +0x5f8 there is out of bounds. kltalk.c guards this with klk_rules_onl.

1. FOLLOW / ESCORT
- Module: klescort.c. Functions: kle_tick 1420, kle_init 1493, kle_pick 694, kle_hold 735, kle_place 724, kle_release 775, kle_follow 1175, kle_order2 660.
- Keys: [Bots] Escort=1|2, EscortRecord, EscortFar 800, EscortSide 300, EscortRetarget, EscortEvery 2s, EscortUntil, EscortStage, EscortRefill, EscortBoard, EscortDry, OrderTrace.
- Data: crew records (stage, actor), human feet, the [soldier+0x64c] defend block.
- Online: none (gap G-E, "OnlineEscort" not built). A partial substitute is the klbotfill puppeteer gather/hold.

2. KEEP MOVING / WAIT FOR YOU / WALK TO VAN
- Module: klmove.c. Functions: klmv_restless 1379, klmv_gather 1579, klmv_boxes 1060, klmv_ally_reach 612, klmv_last_vehicle 861, klmv_bot_van 917, klmv_vancall 1727, klmv_walkaway 1762, klmv_escvisit 1692, klmv_crewhold 1222, klmv_driver 1176, klmv_gate 1143, klmv_sour_pass 522, klmv_make_sour 538, klmv_tick 1803, klmv_read 1909.
- Keys: [Bots] RestlessLoot, RestlessSkipDowned, WaitForYou, BoardNear*, BoardReach* (Aim, Chase, Doors, Fight, FightRange, Flat, Last, LastRange, Order, Sent, Settle), StairGather(+At), LastVehicle(+Flagged, +Lead), VanCallLast, VanCallNear, WalkAwayReorder, HalfGuard, CrewRouteAlone, CrewRouteFed, EscVisitFix, PerMap, MoveDry; [Hops] Gates, Max.
- Data: money list [rules+0xdcc], ZOnlineMoneyCtrl +0x34/+0x6c, a ZAllyEscapeBox vtable copy, [rules+0x1ee].
- Online: no equivalent for the Arcade keys. The klbotfill puppeteer substitutes (see 4 and 5).

3. HOPS OVER NAV GAPS, AND THE RETOMOTO JUMP
- klhop.c: klv_tick 389, klv_walks 293, klv_follow 340, klv_putback 266, klv_order 253.
- Keys: [CrewHop] Enable, Online (0/1/2), OnlineStage 2, Dry, Reorder, OrderTo, Log, Recheck; Bots.WalkExclusive.
- Data: klt_teleport (game call 0x62a900) and [CrewHop] places from the level's KLJoin.ini.
- Online: YES, host only. klhop.c:397-401 uses klbd_online_view(0,...) pseudo-records and klbf_ob_stage (klbotfill.c:223). Init at klhop.c:518-519.
- Retomoto jump, klcrew_rt.c: klt_tick 272, klt_move 222, klt_teleport 219. Keys: [CrewJoin] Enable, Retrigger, FedSkip, Log, Name, Places. Online: none (the file header says Arcade only, line 67).

4. LOOTING / CARRYING
- Arcade: the game's own ZLootTactic (0x451920) via rules slot 202 (0x8b94d0) and the money-ctrl take via slot 201. The bot take goes to 0x8e8750. The hook only shapes it through klmove Restless/sour (see 2).
- Online: klbotfill.c puppeteer.
  - Functions: klbf_ot_run 885, klbf_ot_health 557, klbf_ot_call_van 587, klbf_ot_boxscan 633, klbf_ot_goal 727, klbf_vh_pass 753, klbf_ot_summary 787, klbf_ob_stage 223, klbf_way_load/start 240/264.
  - Phases: 0 pick the nearest unclaimed ZOnlineMoneyCtrl from the registry 0xe09e38. 1 walk and grab within Near (take mode 0 none, 1 raw +0x34 write, 2 game call 0x4e3f40). 2 walk to the van. 3 boarded.
  - Keys (init at klbotfill.c:102-192): [BotFill] OnlineHost, OnlineTactics, OnlineTacticsCarry 2, OnlineTacticsNear 150, OnlineTacticsTake 0, OnlineHealthMul 5, OnlineGuardTake, OnlineTacticsGuard 25, OnlineTacticsVan, OnlineBoxWalk, OnlineBoxProbe, OnlineBoxForce, OnlineBoxSlack, OnlineBoxSpread, OnlineBoxLatch(+M), OnlineWaypoints (needs [BotFillWay_<SLOT>]), OnlineLegScale/Speed/MaxS/StallS/Near/Dy, OnlineSkipDoorStacks, OnlineFireStall, OnlineGiveUpRetry(+S), OnlineIdleVan(+S); [Bots] OnlineFill, OnlineFillSquads.
  - Limits: the take is a host-only tally. Clients are not told. There is no score, no loot-started trigger, and no depleted-stack replication (G-B, G-C). The stock HUD loot sum is wrong.

5. ESCAPE / BOARDING / FOLLOW-OUT / VAN BLOW
- Arcade: the game's ZBoardEscapeVehicleTactic (0x82f970) and ZAllyEscapeBox (0x907a50 -> 0x74d7f0 -> rules vtable +0xb4 = 0x6840a0). The exit trigger 0x6c3d50 sets stage 3 and calls the vehicle.
- Hook extras: klescort.c kle_board_all 827, kle_all_track 805, kle_veh_pass 1030, kle_hold_guard 947, kle_vb_pass 997, kle_spare 1113.
  - Keys: Bots.BoardAll, BoardAllStage, BoardAllOrder, BoardAllStill 15s, FollowOut, FollowOutSpare/Dry/Order/Money/CrewMoney/After/Every/Hold/Shield/HoldUnshielded/HoldAlone(+Range)/StopPlace/ComeMoved; [VanBlow] Enable (default 1), Dry, Log, EmptyDelay 1500, HealthMax.
  - Data: the stage byte write, the vehicle timer [rules+0x1d8], the vehicle state.
- Online: partial.
  - OnlineBoardAll (klbotfill.c:176-177; klbf_bank_pass 803, mode 0/1/2, OnlineBoardAllM) is a ledger/boarding substitute.
  - OnlineBank, OnlineBankCredit (klbf_bc_credit 844): pays an escaped human seat up to the Sharable cap of 1M.
  - OnlineVanState, OnlineVanCall, OnlineVanGather (+GatherM 12, GatherMaxS 25, GatherLateS 45), OnlineVanHold (+HoldM 30, HoldNearM 18, HoldMaxS 15, sets kle_vh_hold, klescort.c:444/1017, to stop the van blow), OnlineBoard (removal via 0x89c890), OnlineBoardTeleport(+S, +M), OnlineExitCrowd 1600, OnlineExitSprint, OnlineExitKeepGoal, OnlineVanRecall, OnlineLateExit 75, OnlineJoinCalled.
  - Bench: DD08 4/7, DD04 3/7 then 7/7 with OnlineExitCrowd 1600, DD05 6/7.
  - The VanBlow itself and FollowOut are Arcade only.
  - ZOnlineExitLevelTrigger 0x6c3d50 does not count bots (blocker 5). A human boards by holding E on the van BoardingTrigger (re/human_escape_online_1028.md).

6. TRIGGERS (cop waves, doors) BOTS SET OFF
- Arcade: the stock trigger boxes accept bots.
- Online: bots are ignored (ZTriggerBox2 0x626ec0 test at 0x626f92; ZOnlineMoneyCtrl 0x6cdb40 needs a ZFFPlayer activator).
- Substitute: klbotfill.c klbf_trig_scan 408, klbf_trig_other 450, klbf_trig_tick 507. OnlineTriggers=0/1/2 (default 0, init at klbotfill.c:170) and OnlineTriggersExtra.
- Ramp: klbf_ramp_* 286-406. OnlineRampFire (default 1) fires only for maps with a [BotFillRamp_<SLOT>] section. OnlineRampDry.

7. COMBAT BALANCE AND HEALTH
- klbalance.c: klr_player_tick, klr_pb_tick 992, klr_online_host 1362.
  - Keys: [Balance] Enable, Risk 0-3, Tough, PlayerHealth, RegenDelay, RegenTime, CopToYouFar/At/NearAt, YouToCrewFar/At/NearAt/Hold, CrewToFed, FedToCrew, CrewOffStage, FedMirror, Ramp, Log, LogCrewHits(+Big).
  - Data: tuning record R=[0x168d7c0]+0x6ac+L*0x70 (+0x04 Ally to NPC, +0x1c stage factor).
  - Online: YES. [BotFill] OnlineCopToBot (klbalance.c:1427-1439, wrapper on ZFFActor slot 423), OnlinePointBlank (1420-1425) + Cap/Refund, OnlineHealthMul (klbotfill.c:111, klbf_ot_health 557).
- Grudge, klgrudge.c: kly_tick 418, kly_health 249, kly_aim 278, kly_mark 304, kly_grudge 330. Keys: [Bots] Grudge, GrudgeMix, GrudgeMark, GrudgeSnapHits, BackstabMark. Behaviour: tougher bots, a response when you shoot them, an accuracy block at [soldier+0x6d8]. Online: none.
- Online police-to-crew hits are skipped: ZFFActor hit 0x61a980 bypasses table 0x591b60 (blocker 3). OnlineCopToBot works around this.
- klaiturn.c ([Rigid] AiTurnDps) caps AI turn rate. It is global, so it works online as is.

8. DOWNS / REVIVE / ADRENALINE
- klbotdown.c: klbd_tick 393, klbd_pass 406, klbd_online_snap 360, klbd_online_view 377, klbd_ov_fill 338, klbd_census 290, klbd_init 594.
  - Keys: [BotDown] Enable, Dry, Log, DownPct 30, FloorPct 6, RefuseMs 4000, PreShield, DownsMax 2, LieSeconds 6, LieFar(+At), FreeSeconds 0.75, LiePct, UpPct, AttrMs, WatchSeconds, NoFire, Traitors, FedDowns, FedFree, FedUpPct, FedHealth.
  - Game call: soldier slot 51 (0x688190 -> 0x70e0e0, force flag 1). Data: [actor+0x64c], health object.
  - Online: down only, via [Down] OnlineBotDown (default 1) and OnlineBotDownDry (klbotdown.c:601-602, host role 2). There is no get-up help online.
- kladren.c: keys [Adrenaline] Enable, Dry, Log, NeedUse, UseKey, HumanFast, ShareBot, ShareBank, Mark, MarkFine, Take, BotHelp, Rush, RushVan, Prompt, Anim*/BotAnim*. A helper pulls the lie tick earlier ([[soldier+0x4b8]+0x14]) and gets a share of the money at the get-up. Online: none (kladren.c:1169 "online later").
- klcdying.c: almost-dead bots get a revivable floor, NoFire. The Human part is unproven online. Online: none.
- Car down, klcardown.c: klcd_tick 235, klcd_event 179, klcd_blow 165. Keys: [CarDown] Enable, Online 0/1/2, Dry, Log, Human, Bots, Cops, CountTrigger, Damage, Inner, Seconds, Radius. Online: YES, host only (klcardown.c:241 uses klbd_online_view(1,...), init at :299).
- Shield, klshield.c klsh_tick 145: [Shield] Enable, Dry, Log, ReleaseDown, Down. It acts on the local player's health object. Online: none.

9. VOICE LINES / BANTER
- kltalk.c: klk_tick 732, klk_say 471, klk_chatter_say 626, klk_fed_tick 674, klk_pool_key (voice _C1..C8 from rules+0x33e+rec), klk_pool_class (Kane / Lynch / Any / Squad by record parity, a guess), klk_init 920.
  - Keys: [Talk] Enable, Log, Chatter, LogOnly, StockLevels, StartOffset, Seed; per-level KLTalk.ini pools (event on money, stage 2, traitor, down, shoot, idle, won, plus pairs).
  - Data: crew status/stage/flags/money per record (money from score+0x150), klw_who_now, the .LOC look-up 0x828fa0.
- Online: PARTIAL, humans only. [Voice] Online=1 plus OnlineTalk=1 (kltalk.c:459-460, klk_who_any) feed the local seat and the other human rows through kvo_online_who_wide (klvoice_online.c). OnlineTalkNoScore, OnlineTraits, OnlineCrew also exist. Bot banter online: none. Online money events are absent (score=0 online), so the events that fire are limited.
- klvoice.c: Dead Men event lines swapped into the speech manager. Online: local seat only.

10. RANDOM LOOKS / VOICES / NAMES PER BOT
- klcrew.c: klw_level_tick 382, klw_draw 310, klw_dress 285, klw_voices 341, klw_rename 367, klw_init 529.
- Keys: [Crew] Random, Seed, DogDays, DeadMen, Include, Outfits, Masks, MaskChance, PaydayMasks, Voice, Names, Settle, Tries, Log.
- Game calls: 0x783fb0(actor, model), 0x88c810(actor, variant), the voice byte rules+0x33e+i, and 0x83e2e0 + 0x469250 (name string [[record]+8]).
- Online: log-only probe [BotFill] OnlineLooks=2 (klbotfill.c:124 init, klbf_lk_name 1272, klbf_lk_log 1287, probe in klbf_tick ~1325). No write is built (G-D). The model is per-peer data, so a host-only look would be invisible to clients and there is no carrier.
- klcharonline.c ([CharOnline]) syncs every human's heister, mask and outfit, but not bots.

11. NAMES / INITIALS / SCOREBOARD
- klhud_names.c: klnm_name, NameTags 0/1/2, initials above the head. It reads klw_who_now, so it is Arcade only.
- Online: klhud_board2.c shows bot rows (~640-717, generic "AI" / DEAD fate, OnlineBoardTake). klonline_read.c has klor_bots 95 and klor_bots_sorted 118. There are no character names and no overhead initials.

12. TRAITS
- kltrait.c: kltt_tick 124, kltt_init 161, getter ~103. Keys: [Traits] Enable, Dry, Log, MaxDelta. The factors are applied in klgrudge.c kly_health and klbalance.c klr_player_tick.
- Online: partial. [Voice] OnlineTraits (kltrait.c:44-48) logs the local player's trait only. The getter returns 1.0 online (kltrait.c:103). No factor is applied to bots.

13. TRAITOR / BACKSTAB / BRIBE / LEAVE
- klbot.c: klb_act 884, klb_make_traitor 737, klb_moment 751, klb_foe_tick 833, klb_foe_swap 811, klb_tune_tick 667, klb_tick 1047, klb_init 1090. The traitor flag is set via record flag bit 2 or the game's ZBecomeTraitorTactic (0x79b7c0).
- Keys: [Bots] Enable, Log, Tune, Traitors(+.N), Limit(+.N), Retaliate, Backstab, BackstabStage 2, BackstabMoney 250000, BackstabDelay 20, BackstabNear/Behind/Busy/Wait, TraitorsMax, TraitorKillMax 2, TraitorKillNear, TraitorFoe, FoeSkipWhileFed, BackstabCrew(+Near), Bribe, BribeMoney, BribeDelay, Leave, LeaveDelay, LeaveDistance, Van 0/1/2, VanChance, VanDelay, VanLeftBehind.
- Online: none, and a CERTAIN blocker (G-G, recommended off online). klbotdeath.c only logs what kills online Ally bots.

14. COP SQUAD (human cops command AI cops)
- klcopsquad.c: klcq_tick 233, klcq_recruit 158, klcq_follow 149, klcq_order 210, klcq_init 79. It uses ZSquadControl [P+0xcd0], Recruit 0x908040, Follow 0x4c3900.
- Keys: [CopSquad] Enable, Per, Team, FollowS, MaxM, AttackT, Log.
- Host only, game type 4 sub-mode 2, a Cops-and-Robbers feature rather than a heister-bot behaviour. Default off and never run. The order channel is not built (klcopsquad.c:22-33). Online: none.

15. KITS
- klfedkit.c: klfk_tick 952, klfk_body_tick 492, klfk_ak_tick 555, klfk_init 964.
- Keys: [Fed] Enable, Player, Kit, KitLog, Hunt, Crosshair, Body, AkChance, AkItem, KitSettle, NoTraitor, NoLoot, Pay, PayKill, HudFade, Hunted*; [FedBody] Entries, Root, Stock, AkItem, AkRecord, Name, Variants.
- This is the kit of the human who came back as a fed, not an AI bot kit. Bots' only "kit" is the klcrew look/mask (10). Online: none.

16. BOTS IN THE LOBBY / SQUADS
- Arcade has its own squads. Online: klbotfill.c OnlineFill / OnlineFillSquads (klbf_squads 53) plus OnlineHost (census, KLSY2 sharing). Clients see bots as team-2 Ally ZFFActors through DDL_ZFFActor and KLSY2 (UDP 27415, klsync.c).
- The data route for squads is kl_botsonline.py and F0n_Main.bots.zip (klslot.c "botgate"). ZSquadScript slot 14 (0x7b3790) drops mask-8 squads online (blocker 4).

ONLINE BUILT (host only unless noted): OnlineFill/Host, OnlineTactics (loot and van), OnlineBotDown (down only), CrewHop Online, CarDown Online, OnlineCopToBot, OnlinePointBlank, OnlineHealthMul, OnlineBank, OnlineBankCredit, OnlineBoardAll, OnlineRampFire, OnlineTriggers (default off), partial voice for humans, scoreboard AI rows.

ONLINE GAPS, RANKED
1. G-B / G-C: no loot score, no stack depletion or replication for bots, and the HUD loot sum is wrong.
2. Bank-credit and escape coverage: DD08 4/7, DD05 6/7, and bots uncounted by exit trigger 0x6c3d50.
3. G-E: no escort/follow online.
4. Triggers: bots ignored by ZTriggerBox2 and ZOnlineMoneyCtrl. The OnlineTriggers substitute is off by default.
5. Revive, adrenaline, shield and dying-floor: none online.
6. G-D: bot random looks, names and voices are log-only (OnlineLooks=2). A carrier is missing.
7. Bot banter and Dead Men voices for bots: not built. Only human seats talk.
8. Scoreboard names, overhead initials, traits and grudge: none. Traits are not applied to bots online.
9. G-G: traitor, backstab, bribe, leave and van gameplay: blocked, none.
10. Crew follows the Retomoto jump (klcrew_rt.c) and the cop squad: Arcade or Cops-and-Robbers only, none online.

Not read in full: the bodies of klb_act, the kltrait.c table, the KLHook.ini defaults, and the per-map OnlineTriggers defaults.

Sources: re/bots_online_arcade_1028.md, re/arcade_mods_online_1028.md, re/human_escape_online_1028.md, and the klhook/ modules cited above.

---
## Survey: online paths

BOT PATHS ONLINE (read-only map, tree at C:\kl-merge\wt\wk-merge, 2026-10-28). No files were edited.

**1. Root cause of "bots do little online"**
- The Arcade test at 0x7f6850 is false for online roles 2 and 3.
- The ZSoldier constructor at 0x6ab250 therefore builds no ZLootTactic, ZBoardEscapeVehicleTactic or ZBecomeTraitorTactic ([soldier+0x5f0/4/8]).
- Online has no crew records. Arcade's rules slot 198 (0x588980) makes the 0x7c-byte records at rules+0x348. Online Sv/Cl rules use a 0x74-byte seat table at [rules+8], and Sv uses +0x348/+0x350 for its own fields. Do not fake the table.
- Trigger boxes ignore bots: ZTriggerBox2 at 0x626ec0 (test at 0x626f92), ZOnlineTriggerBox at 0x49ab90, ZTriggerBox at 0x42afd0.
- ZOnlineMoneyCtrl slot 26 (0x6cdb40, branch 0x6cdbd0) needs a ZFFPlayer activator.
- Actor hit 0x61a980 skips the police-to-crew table at 0x591b60.

**2. Host puppeteer (klhook/klbotfill.c, host only)**
- Entry: klbf_tick (about line 1296) calls klbf_ot_run (line 885) once a second. This happens only when role==2, state is KLB_ROUND (0x19) and [BotFill] OnlineTactics=1.
- It orders bots through kle_order2, which wraps the soldier's vtable +0x13c = 0x760e50 (klescort.c).
- Bots are ZFFActors (vtable 0xbb3bac) on team Ally ([[actor+0x54]+4]==2).
- The ZSoldier is at actor+0x77c, the health object at actor+0x5fc, the feet at +0x460.
- Per-bot state lives in klbf_ob[16]. The cap is 16 (KLBF_OT_BOTS).

| Phase | What it does |
|---|---|
| 0 pick | Takes the nearest unclaimed armed stack. Skips claimed, blacklisted, taken, door-shut (+0x5c) and cop-guarded stacks (OnlineTacticsGuard, 25 m). Idle van calls are OnlineIdleVan. |
| 1 grab | Walks to the stack and grabs within 150 cm (Near) and \|dy\|<=400. Take=1 is a raw 0 write to +0x34. Take=2 is KLFC_CALL 0x4e3f40(o,0,amt) (about line 960) and refuses stack states 2/3. Stall limit 12 s without 2 m of progress, 90 s cap, GiveUpRetry 45 s. Carry means 2 grabs. OnlineLateExit (75 s) stops a carrier taking a new stack late in the round. |
| 2 carry/van | Goal is the exit trigger (klmv_exit_vehicle2, a private-memory scan retried every 20 s), then the ZAllyEscapeBox (OnlineBoxWalk). OnlineWaypoints use [BotFillWay_<SLOT>] legs with a 15 s limit per leg. OnlineExitSprint writes move style Sprint into the defend block (blk+0xc=2, +0x10=1). The van is called once through klbf_ot_call_van (line 587): 0x71e180(rules,0,vh,0), checked against the Sv vtable 0xbd2eb4, the function head and clock >= 20 s. OnlineVanGather waits up to 25 s (OnlineGatherMaxS) for walkers within 12 m, or until 45 s are left (OnlineGatherLateS). OnlineVanRecall allows up to 2 recalls. |
| 3 board | A bot counts as boarded when inside the box (0x758cb0) or while van state [rules+0x1dc] is 3/4. Options: OnlineBoxForce, OnlineBoxSlack, OnlineExitCrowd (1600 cm after 5 s), OnlineBoardAll, OnlineBoardTeleport (0x62a900, default 0, marked "NOT Arcade"). Boarding is only a host tally. OnlineBoard=1 calls squad removal 0x89c890, but the effect is a GUESS. |
| hold | klbf_vh_pass (line 753) sets the van's Invulnerable byte (KLE_VEH_INV) while a walker is within 30 m, capped at 15 s. It holds [rules+0x1d8] at 3.0 when a walker is within 18 m. kle_vh_hold pauses VanBlow (klescort.c:444, 1017). |

Other host passes:
- **OnlineHealthMul:** bot health x5, written at h+4 and h+8.
- **OnlineTriggers:** fires ZTriggerBox through 0x6ae730 for bots. This was proven live on F06 (3 fires). OnlineTriggersExtra covers ZTriggerBox2 (0xbc953c; inside test 0x68d030; fire slot 34 = 0x557820) and ZOnlineTriggerBox (0xbc95cc).
- **OnlineRampFire:** fires 0x45f5d0 from a [BotFillRamp_<SLOT>] section. Whether clients see the ramp is a GUESS.
- **OnlineBank / OnlineBankCredit (klbf_bc_credit, line 844):** books a host ledger and credits boarded or escaped human seats via AddSharable 0x5a18c0. Seat flags come from 0x571750 (0x20 boarded, 0x40 escaped). The Sharable cap comes from 0xd1b3d0. WKBC5 paid out. A bot that banks after the last human has left is lost.
- **OnlineLooks=2:** log-only probe (klbf_lk_*, line 1272). The wk-looks apply branch with OnlineLooks=1 is not in this tree.
- **OnlineFillSquads:** the squad-mask byte pass (klbf_squads, line 53) is dead online. The real route is data (kl_botsonline.py plus F0n_Main.bots.zip, "botgate" in klslot.c).

**3. Client side and replication**
- Clients run no tactics. 0x760e50 returns early on a client (0x863a60 && 0x4b0a40), so orders exist only on the host.
- **KLSY2:** the hook's own UDP packet on port 27415. Records are 20 bytes: {u16 slot, i16 hp, f32 x3, u16 cls, i16 team}. The host shares (klsync.c:1013). The client mirrors through puppets (ksp.bots = klbf_oh, klsync.c:945). Identity is class plus team, and slot order across peers is unproven. A team-Ally bot may share a team object with a human crew (GUESS, klsync.c:372).
- **KLSYP:** the player probe (klsync.c:842).
- **KLSYL:** not found anywhere in the tree (GUESS: an old name).
- **DDL_ZFFActor:** the game's own replication of actor state. Per re/crew_online_1028.md it carries no model, outfit, name or voice field.
- **KLCH1 (UDP 27414, klcharonline.c):** the carrier for human looks only.
- Bots that boarded are not replicated as boarded. Stack take state and the bot loot tally reach clients only through the game's own replication of the money controllers (not proven).

**4. Limitation comments in the code**
- Header, klbotfill.c about lines 192-200: "NOT done (GUESS/open): nothing is replicated to clients (UDP 27415 events are not sent), the stock round money / score / end screen are not touched, a boarded bot stays a plain actor."
- The header still calls OnlineTactics "(recommended off)", which is stale.
- Take=1 is a GUESS.
- The registry holds stale entries, so each is re-checked by vtable.
- The van node can sit at (0,0,0), so van state is used instead.
- The exit trigger's node is assumed to be the box (GUESS).
- Waypoint legs of 40-60 m timed out at 15 s (DD08).
- Partial boarding in early benches (DD08 4/7, DD04 3/7, DD05 6/7). Later benches: BP_DD04c 7/7, WKBC3 F06 7/7.
- OnlineVanRecall assumes a second 0x71e180 call behaves like the first (GUESS).
- OnlineBoxLatch, LegScale, LegStallS and BoxSpread are "not yet run live". BoardTeleport is off by default.
- A 0x71e180 call with flag 0 can flag the vehicle LAST when the clock is under 20 s, so it is gated.
- Other known gaps (re/bots_online_arcade_1028.md):
  - G-C: bot loot is not shown on the HUD. A host-to-client carrier is needed (format is a GUESS).
  - G-F: down, revive, adrenaline, cardown and shield need a crew-record substitute.
  - G-G: traitor is blocked.
  - G-I: the config menu table is nearly full (about 4994/5000).
  - Open question: client-side double fire of trigger boxes.

**5. Feasibility, host-only and without Arcade crew records**

1. **Escort / follow the human: FEASIBLE.**
   - The order call already works online. The puppeteer uses kle_order2 (0x760e50, vtable +0x13c) with rec -1 and told_soft 1.
   - klescort.c's escort (EscortFar 800, EscortSide 300, EscortEvery 2 s) reads Arcade-only data via klb_read (klescort.c:1118, 1429). Change it to drive from the bot census and klbf_ob[], with the human's place from klsy_humans (klsync.c:353/366) or klco_find_own (klcharonline.c:140, table 0x6161c0).
   - Remote humans' positions through KLSYP or that table are a GUESS.
   - Clients see the movement via DDL_ZFFActor (GUESS).
   - This is the best next step.

2. **Revive downed humans: NOT FEASIBLE host-only.**
   - A bot can run to a downed human via kad_rush (kladren.c about line 318, using kle_order2), but that file is Arcade-only. The human's down state ([player+0x2948]) is local to that peer.
   - The revive itself (RMCDownNotDead_SetDowned wrapper 0x846d90, GettingUp 0x6cd720) is master-routed through 0x9425a0 (re/downed_online.md). It needs a "revive slot N" message to the owner's machine ("Way 3"), which is not built. The host must never write a client's replica.
   - Revive of a downed bot by a human is also not built (klbotdown.c:285). Bots get up by themselves.
   - Bot downing online is host-only, through klbotdown.c's klbd_online_view (line 377) with KLBD_SLOT51 0x688190 and test 0x70f330.

3. **Bot voice lines online: NOT FEASIBLE host-only.**
   - Speech is played locally per peer. kltalk's OnlineTalk (about lines 455-460) covers the human rows only. A1TALK_DM01 and DD04 passed with banter on both seats.
   - The speak calls are KLK_LOOKUP 0x828fa0 and KLK_SAY 0x421c70 (kltalk.c:143-144). They take a crew record index as speaker, which online bots lack.
   - Per-bot voice needs a host-to-client event carrier plus a speaker (GUESS). re/crew_online_1028.md row 2 (OnlineVoices) is a GUESS.

4. **Bot names on HUD/scoreboard: BLOCKED.**
   - The crew-list name comes from [[record]+8] (record = rules+0x348+0x7c*i, 0x841e50). That record does not exist online.
   - The head tag element is not identified (re/hud_names.md).
   - klbot.c:403 klb_online_name guesses a name at record+8 (GUESS).
   - klhud.c's klu_online_bots numbers bots through klor_bots_sorted (klonline_read.c), which shows a row but no name.
   - Do nothing until the name source is traced (crew_online_1028.md row 3).

5. **Traits online: PARTLY FEASIBLE, host-only effects only.**
   - Online, every factor answers 1.0 (kltrait.c:103), the feature is log-only, and it follows only the local seat (lines 44-48, 134-135). The lie time ignores traits (klbotdown.c:500).
   - Hp, aim and speed effects on the host's bots could be wired through the host-side pseudo records. Effects on a bot's body replicate only as far as DDL_ZFFActor carries them (GUESS).
   - Per-bot trait assignment needs a host table keyed by bot slot. It must not use cross-peer keys, since slot order across peers is unproven.

6. **Cop squad / C&R online: HOST-ONLY RECRUIT POSSIBLE, key orders for remote cops NOT BUILT.**
   - klcopsquad.c (lines 22-33) uses the game's own ZSquadControl: Recruit 0x908040 and Follow 0x4c3900, with the squad control at [player+0xcd0]. It runs on the host only, in C&R (type 4, sub-mode word [0x168e59c]==2), default off, and has never run live.
   - Only the host's own keyboard commands the squad. A remote cop's keys never reach the host, so a UDP order channel in the klcharonline pattern is needed.
   - Clients seeing the soldiers move through DDL_ZFFActor is a GUESS until benched.
   - The human cop identification (type byte [P+0x273c]==3) is partly GUESS.

7. **Fed kit online: BLOCKED.**
   - klfedkit.c gates on Arcade session and rules, and reads Arcade crew record 0 through klb_read (about line 798). It needs rules+0x348 records and the FA_Killed_Merc and FA_NoFriendlyFire announcements.
   - The klbd_online_view pseudo records carry no money.
   - It needs a rewrite on the online seat table and the KLCH1 carrier.

**Suggested order:** escort/follow (5.1), then host-side traits (5.5), then a UDP carrier. The carrier would also unblock bot voice, names and the loot tally (the gaps G-C, G-D and the bot voice/name rows above). Revive and fed kit stay blocked until crew records or an owner-side message channel exist.

Key files:
- C:\kl-merge\wt\wk-merge\klhook\klbotfill.c
- C:\kl-merge\wt\wk-merge\klhook\klsync.c
- C:\kl-merge\wt\wk-merge\klhook\klescort.c
- C:\kl-merge\wt\wk-merge\klhook\kladren.c
- C:\kl-merge\wt\wk-merge\klhook\klbotdown.c
- C:\kl-merge\wt\wk-merge\klhook\kltalk.c
- C:\kl-merge\wt\wk-merge\klhook\kltrait.c
- C:\kl-merge\wt\wk-merge\klhook\klcopsquad.c
- C:\kl-merge\wt\wk-merge\klhook\klfedkit.c
- C:\kl-merge\wt\wk-merge\klhook\klonline_read.c
- C:\kl-merge\wt\wk-merge\re\crew_online_1028.md
- C:\kl-merge\wt\wk-merge\re\bots_online_arcade_1028.md
- C:\kl-merge\wt\wk-merge\re\downed_online.md

---
## Survey: bench evidence

Evidence from the host logs (`inst1/KLHook.log`) of the eight benches, under `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\klhook\solo`. `AM_DM09` exists but I did not read it. All lines are quoted short.

## Cross-run picture
- **Looting and boarding work online.** Every run shows `botfill: tactics: round 1 starts (Carry 2, Near 150, Take 2)`, then `GRABBED stack` lines, `OnlineTriggers` firing (`FIRE box ... via 0x6ae730`), and the van going through states 1, 3, 5, 7, 0. Faults were 0 in the runs I checked.
- **Only WK2 has a `round summary`.** The host log ends before the round summary in the other runs, because the host leaves or the client wins first. WK2: `round summary: 7 bot(s) given orders, 7 stack(s) taken, 2200000 total (hook tally, not the game's), 7 boarded, 1 stack(s) given up`.
- **WK2's bank settlement was refused:** `bankcredit: settlement call 0x681103 -> 0x5e2230 REFUSED`, so nothing was credited in that run. Later runs pay.
- **Bank credit is still invisible to the owner.** Most runs end with `bankcredit: no escaped human seat yet (flags 0x40 set, 0x0d clear): ledger $... waits`. Bots bank into a hook ledger, but the human seat only receives it once the human boards.
- **Arcade-only modules never act online.** `talk:`, `hop:` and `cardown:` appear only as one config line each per run (`cardown: on (Dry=1: nothing is called ...)`). I saw no `bd: DOWN` lines; botdown's one real action was in BP_DD04c.

## Per map

**F06 (Heat/bank), host-side results**

| Run | Never grabbed | Never boarded | Died | Ledger |
|---|---|---|---|---|
| WKBC2 | none | none | none | `ledger $550000 waits` |
| WKBC3 | bot 6 (boarded with `tally 0`) | bot 0 not logged as boarded | none | `ledger $1350000 waits` |
| WKBC5 | bot 6 (boarded with `tally 0`) | bot 4 (dead) | bot 4: `bd: DEAD ... hp=945.0 now=0.0`, then `is dead or gone: slot freed` | paid up to the cap |
| LOOKS1 | none | bots 0 and 3 not logged as boarded | bot 1 | `ledger $300000 waits` |
| WK2 | none | one bot late | none | summary above |

- **WKBC2:** `van: gather: no bot is walking to the box any more (all dead or gone): cancelled`. The van also cycled twice (states 7 -> 1 -> 3 -> 5 -> 7 -> 0).
- **WKBC5:** 6 of 7 boarded. Bank credit paid: `bankcredit: seat 0 +$550000`, `+$300000`, `+$150000` (Sharable 850000 -> 1000000), then `+$0 (ledger $250000)` because of the 1M cap. The `tele REFUSED (the player's node is missing or off (flag bit 10))` lines are the script, not a bot.
- **LOOKS1:** the log shows `looks: CLIENT seat digit=2 ... applied` for six seats and `digit=3 skipped: the local player wears this body`, so OnlineLooks=2 is log-only. The van hold hit its cap: `van: hold: cap of 15 s reached (nearest walker 4 m)`.
- **WK2:** `bot 6: the van was called but this bot was not at the exit while it waited after 59 s (15 m from the trigger)`, and `bot 6 did not reach stack ... (4 m left, 26 s walking, no 2 m of progress for 12 s): given up on it`. Round ledger: `7 bot(s) banked $2200000 of 2200000 carried`.
- **What a viewer sees at round start on F06:** the bots start walking to stacks within 10 s (first `GRABBED` 9 s after the round starts, 7 stacks of 250-300k). WKBC5 and WKBC3 show no idle period.

**F04 (BP_DD04b, BP_DD04c): worst for "bots do nothing"**
- **Start of round:** `bot 4/5/6: 6 free stack(s), all with a live cop within 25 m: it holds (up to 30 s, OnlineGuardTake=1) while they are cleared`. Bots stand still until the humans clear the cops.
- **04b:**
  - Bot 1 died. Bot 2 never grabbed and boarded with `tally 0`.
  - Bots 2 and 3 gave up: `bot 2 did not reach stack 28eb9150 (2 m left, 90 s walking, no 2 m of progress for 0 s): given up on it` (bot 3: 7 m left).
  - `bot 5/6: wants the van but it is not here and no exit trigger was found to call it from`.
  - `bot 6: did not reach the exit trigger after 90 s (15 m from the trigger ...): back to idle`.
  - Bot 3 never boarded: `not at the exit while it waited after 66 s (105 m from the trigger)`, then `clock left 54 s <= OnlineLateExit 75: no new stack, tally 440000 goes to the van`.
  - FAIL here is a script wait (`did not become 0x20 within 420000 ms (it is 0x29)`), not a bot problem.
- **04c:**
  - No bot died. All 7 boarded, but bots 2 and 6 carried `tally 0` and were boarded by `OnlineVanState` / `OnlineExitCrowd 1600 cm`.
  - Bots 2 and 6 gave up on stacks (12 m left after 90 s, and 8 m left after 52 s).
  - Six bots hit `did not reach the exit trigger after 90 s (6/15/29/32/15 m from the trigger) ... back to idle`.
  - The van only left because of crowd boarding (`BOARDED by van state 3 (OnlineExitCrowd 1600 cm: 12.2 m ...)`). Crowd boarding is the fix; walking to the trigger is not working on this map.
  - `botdown:` acted: `record 1 IS DOWN, NOT DEAD (1 of 3) ... he lies until tick ... (LieSeconds=15.0)`, then `IS UP after 15.04 s`. The line before it, `the soldier's down routine (slot 51 = 0x688190 -> 0x70e0e0) is not the one this build knows: nothing is called`, shows the hook's own down call is not available; the game downed the bot itself.

**F08 (BP_DD08): waypoint legs**
- All 7 bots hold at the start: `47 free stack(s), all with a live cop within 25 m`. Five of them log `wants the van but it is not here and no exit trigger was found to call it from`.
- Nearly every leg timed out: `bot 3: waypoint leg 2 of 7 timed out (35 m from (5548, 400, -2606), 21 s on the leg ... limit 20 s)`, and likewise legs 3 to 6 for bots 0, 1, 2, 4, 5 and 6. Some bots were within 4-10 m (`bot 1 leg 5 timed out (4 m ...)`), others 35-45 m away.
- All 7 still got aboard: 6 `BOARDED in the escape box`, then `boardall: bot 2 ... 38 m from the escape point, van state 5: counted aboard`. Ledger was $1,040,000, mostly 150k each. F08 loot is therefore half of F06's per bot. The FAIL is the script wait, as in 04b.

## Ini keys that exist but are off in the tree and would add Arcade behaviour
From `klhook/KLHook.ini` and the `GetPrivateProfileInt` defaults in the worktree `C:\kl-merge\wt\wk-merge\klhook`. Benches set some of these on per run.

- **Core switches, default 0.** `OnlineHost` (ini line 1646), `OnlineTactics` (1650), `OnlineTriggers` (1769), `OnlineTacticsTake` (1656; 2 is the game's `0x4e3f40`) and `OnlineGuardTake` (1679, the hold while cops are near stacks).
- **Path and boarding, default 0:**
  - `OnlineLegScale`, `OnlineLegStallS` (benches use 10), `OnlineLegDy` (benches use 300), `OnlineLegNear`. These address the DD08 leg timeouts.
  - `OnlineBoxSpread`, `OnlineBoxLatch` (`BoxLatchM` is 1500 in the benches).
  - `OnlineBoardTeleport` (0 to 2; the source comment says it is not Arcade behaviour). The DD04/DD08 benches run `OnlineBoardTeleport=2`, the F06 benches 0. The source says `OnlineLegScale`, `OnlineBoxSpread` and `OnlineBoxLatch` were not yet run live.
  - `OnlineBoard` is 0 under `[BotFill]` (ini line 1791) and the source says "recommended off until a live run shows the bot vanishes on every screen". Separate `OnlineBoard=1` keys exist for the HUD at line 820.
  - `OnlineTriggersExtra` (0 to 2, covers `ZTriggerBox2` / `ZOnlineTriggerBox`).
- **Banter and traits, default 0 and gated on `[Voice] Online`:** `OnlineTalk` and `OnlineTalkNoScore` (kltalk.c:459-460) and `OnlineTraits` (kltalk.c:718). This is the only route to Arcade chatter online, and it also needs `Voice Online=1`.
- **Bot downs:** `OnlineBotDownDry` is 0 (live), so bot downs already act. `OnlineHealthMul` / `OnlineCopToBot` / `OnlinePointBlank` are already on.
- **Staging:** `OnlineStage` (default 2, 0 to 3, klhop.c:519) would give klhop an Online key. `OnlineFill=0` and `OnlineFillSquads=0` (ini 526 and 528) are the lobby-seat probe and squad keep, and they only plan or probe.
- **Looks:** `OnlineLooks` only accepts 2 (log only) in this tree. The writing version is in the `wk-looks` branch, which is not here yet.

Not covered: I did not read the client logs for what a client sees beyond the `sync: puppet` lines. Those show the mirror runs: `botfill: OnlineHost CLIENT (mirror only, steered toward the host's places): 7 Ally bot(s) ... 7 alive`, and in 04c `puppet: slot 898 released (host list stale) after 212859 ms`.
