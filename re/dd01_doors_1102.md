# DD01 online: why 48 of 58 vault cases stay shut (2026-11-02, offline log + code read)

Logs: solo/Q34B_DD01/inst1 (round 1 start 18:19:27.209, round 2 18:24:39.870), ARC1_DD01 (Arcade), Q31/Q32_DD01. Code: klbotfill.c ~1850 (shut test), ~2040-2130 (pick/order).

## What marks a case shut
`ZOnlineMoneyCtrl +0x5c` (field 11, byte) = 1. Cleared only by the case's 'DoorOpened' message (0x6cdc0e). F01 has 58 such cases (Alu cases in DL10_CtrlRoom, 8-10 per door). The scan skips them (OnlineSkipDoorStacks=1) and counts them (`+N behind a shut door`).

## What opens them (Arcade, and online with bots.zip)
Squad script, not a player action: `merc_bot_squad!Squad#02..08` -> `020_WaitForAllNPCDead` (guards) -> `020_KickDoorBehaviourRout_loot_room_01#NN` (PosInfo at the door) -> door kicked -> `KickdoorMonitor!KickDoor_RelayList_DoorNN` ('AITrigger' -> 'DoorOpened' to that door's 8-10 cases) and the door's pathblocker opens. (re/stock_map_bots.md:45, re/fa_gamemode.md:207-214.)
Arcade evidence (ARC1_DD01): 58 shut at +5 s, 56 stacks taken by +75 s, 58 by +105 s: every door gets kicked.

## Evidence online (Q34B, with .bots.zip installed)
- The squads DO run online: round 1 first scan at +38 s (18:20:05.473) already shows 10 armed (+48 shut) = exactly ONE door's cases; round 2 shows 20 (+38) at +32 s = TWO doors. Bots stood in the vault (4-22 m from stacks) with zero hook orders before that.
- The same scan tick the first stacks appear, the hook orders ALL 7 bots at them (`bot 0..6 -> stack`, 18:20:05.473). kle_order2 takes a bot out of its squad script. Squads that had not yet reached their `KickDoorBehaviourRout` step never do.
- Shut count then stays 48 for the whole round (18:20:05 .. 18:21:50, no change), then 58 again in round 2 start. Carriers leave for the van with ndoor>0 (line 2123, tally>0), empty bots are held only by `!ndoor` in OnlineIdleVan (2094).
- Round 2 grabbed (-4022,-2502,17535): a different door than round 1, so which doors open first is script/guard timing (GUESS: RandomTrigger / guards dead).

## Cause (evidence strong, mechanism of the missing doors partly GUESS)
The hook's stack orders start as soon as ONE door opens and pre-empt the squad scripts, so the other squads never run their kick step. The earlier guess "online squads do not run every kick-door monitor" is wrong in part: monitors work (10 / 20 cases cleared by script). GUESS: a squad whose guard-wait had not finished is the one pre-empted.

## Fix design: [BotFill] OnlineDoorHold (default 0, recommended on once benched) + OnlineDoorHoldS (default 90, clamp 20..150)
- In the per-bot pick (klbotfill.c next to the OnlineLateExit block, ~line 2100): `if (klbf_ot_dhold && ndoor > 0 && klbf_ob[s].tally == 0 && now - klbf_unpl_at < holdS*1000) best = -1;` (klbf_unpl_at is set at the "round %d starts" line 1785 = round start). Bots without an order keep running their squad script, like Arcade. Ends early when ndoor == 0 (all doors open) or the timer runs out (then today's behaviour).
- Optional: also end the hold once the shut count has not fallen for 25 s after the first armed stack (door guards never die), so a bad door does not waste 90 s. Log the hold once per round.
- Not touching +0x5c, no new calls into the exe, so no BOS1 risk (the stall came from ordering bots at shut stacks / clearing the flag).
- Risks: (1) 90 s of no looting if a squad never reaches the door (cost: delay only; also humans already take stacks); (2) a squad could kick a door but not walk bots out afterwards (stock behaviour in Arcade, fine); (3) bots idle-wait under fire at the vault and die (Arcade shows the same); (4) OnlineGuardTake/DropTake unaffected (best only). Not run live.
- Grade by: `botfill: tactics: scan:` shows `armed` rising 10 -> 20 -> ... with `+shut` falling to 0 inside ~75 s (Arcade: 56 taken by +75 s); new log line `doorhold: N bot(s) held for M door(s) (round R, S s)` once a round; stacks taken > 10 and round-summary money well above Q34B's 770k; no `exit walk` before the shut count reaches 0.
- Fallback if squads still do not finish (check with the scan counts): host-side send 'DoorOpened' via the monitor relay (ref 858/860 RelayList_Door03/04) AND open the pathblocker; unsafe without a disassembly of 0x7eb880 and not proposed now.
