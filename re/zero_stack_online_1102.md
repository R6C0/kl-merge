# Zero stacks online on DD01 / DD07 / DM01 / DM06 (2026-11-02, offline log + code read)

Workflow wf_91b59810-ac4: one diagnosis agent per map pair, one adversarial refuter per map. Logs: solo/Q31_*, Q32_*, Q33_*, Q34B_DD01 (host inst1).

## DD01: missing data (fixed), door gap left
- Q31/Q32/Q34: `botgate: WARNING slot F01: Ally bots ON but no .bots.zip` -> 7 bots at (0,0,0), `0 armed stack(s) (+58 behind a shut door)`, idle-van after 155 s, walks from (0,0,0).
- c9 installed F01_Main.bots.zip 11-01 ~18:16; Q34B: 10 armed (+48 shut), 9 stacks, 770k, 6 boarded. Round 2: 20 armed (+38).
- Left: 48 of 58 vault cases stay shut in round 1 online (GUESS: the online squads do not run every kick-door monitor). Do not clear +0x5c by data write (BOS1 stall).
- OnlineTriggerOriginSkip=1 already ran in Q34/Q34B (`7 of 7 bot(s) read (0,0,0)`), no spurious FIRE.

## DD07 / DM06 / DM01: cops carry the money, the drain goes to drops the scan skips
- Every stack sits on a cop (`5 free stack(s) of which 5 guarded`, nearest cop 0.0 m). Guard test (klbotfill.c ~2016-2040, OnlineGuardTake=0) holds all 7 bots; bypass needs >= OnlineGuardBypassMin (8) stacks.
- Stock actor-death script 0x6d2500 empties each type-0 stack and arms a type-1 drop (DD07 4.5M -> 0 in ~57 s; DM06 +18..+127 s). The scan (~1823) tracks drops but skips them -> 0 armed -> OnlineIdleVan, bots walk out empty, most die.
- Q33 (BypassMin=3) does not fix it: the released bot's stack drains before it arrives (`is gone before it got there`).
- DM01 also: a bot that reaches a stack drifts off it under fire, OnlineLootFinishCapS 25 s ends the take at 8-28 of 40 parts, and the partial stop blacklists the stack. Refuter: the dominant DM01 loss is still the drain (bar 4.5M -> 0.28M by +160 s in Q31).
- DM06 refuter: the stall in Q33 is not a different-floor path (stack y spread 4.6 m), cause unclear.

## Fix chain (bench in this order, all keys default 0)
1. Existing: [BotFill] OnlineGuardMode=1 + OnlineGuardCarrierCm=150 (a cop at the stack is its carrier, not a guard -> bots set out at +0 s), OnlineDropFollow=1, OnlineTacticsTake=2.
2. New (wk-droptake-1102, in progress): OnlineDropTake (+M): a bot with no stack and tally 0 takes the nearest unhidden drained drop; no idle-van while one exists.
3. DM01 extra: OnlineLootFinishCapS=55, OnlinePartialRetry=1 (+S 60).
4. DD01: keep .bots.zip installed on every map (check DD02..DD09, DM*); OnlineUnplacedGuard=1 for a clean no-op when it is missing.
