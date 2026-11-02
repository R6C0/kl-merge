# DD01 online bot loot stops at 14 stacks (2026-11-02, offline log + code read, no game launch)

Logs (host inst1 KLHook.log): `solo/DH1A_DD01`, `DH1B_DD01`, `DH1C_DD01`; Arcade baseline `solo/ARC1_DD01` (the only Arcade DD01 run; ARC2 has no DD01).
Code read: `klhook/klbotfill.c` (header comment ~l.368, Carry init l.161, pick/order ~l.2160). No C changes made.

## Answer

The cap is the per-bot carry limit, `[BotFill] OnlineTacticsCarry` (default 2, existing key): 7 bots x 2 grabs = 14 stacks, in all three runs
(DH1A, B, C: 14 GRABBED each). Every bot grabs twice, walks to the van, boards, and is then finished for the round. There is no second trip.
Not deaths (0), not the round timer, not target order, not idle-van, not the doors (58 of 58 armed in DH1A; 44 stacks still armed when the last bot left).

Online does NOT match Arcade in money carried per bot (about 220k online vs 0.7-1.2M in Arcade). It is close in money banked (1.54M vs 1.88M), but only
because Arcade bots die on the way to the van. Existing key `OnlineTacticsCarry` closes the carried gap (no new key needed); proposal below.

## DH1A per-bot timeline (t = seconds after round 1 start 03:51:38.4)

| t | event |
|---|---|
| +0 | scan: 0 armed, 58 behind a shut door |
| +39..+43 | OnlineDoorHold: armed 10, 20, 50, 58 (all open by 03:52:21) |
| +46.7 | all 7 bots GRABBED stack 1 (110000 each, 4 timed parts in 3.0 s) |
| +50.7 | all 7 GRABBED stack 2 (tally 220000, 2 grabs = Carry); same tick `-> exit trigger 568a7160 ... with tally 220000`, exit walk at Sprint |
| +50.7..+114 | walk to the exit trigger: 63 s. Scan then shows 44 armed stacks left, nobody to take them |
| +114 (03:53:32) | bot 2 reaches the exit; OnlineVanGather: all within 12 m, van called at +116 (clock left 134 s) |
| +128 | bot 2 BOARDED (van state 3), bot 0 at +131, bot 1 at +133; bots 3-6 at +133 via OnlineExitCrowd |
| +133..+273 | no bot has any order: 140 s of round clock with 44 stacks armed. Round summary 03:56:11: 14 stacks, $1.54M, 7 boarded, 0 given up |

DH1B (control, doors mostly shut): stacks trickle in 20 -> 8 armed, still 14 GRABBED; DH1C (hold 120 s): 14 GRABBED, $1.14M (some partial stacks).
In all three the loot ends when the 14th grab is done, regardless of what the doors did. That is why OnlineDoorHold armed 58 stacks and the total did not move.

Code: after `grabs >= klbf_ot_carry` the bot takes the phase 2 branch (`else if ((tally > 0 || idleVan) && !holdExit)`, l.2162) -> phase 3 = boarded,
which is terminal within a round (nothing sets a boarded bot back to phase 0 except a new round). Carry is read once from `OnlineTacticsCarry` (l.161),
default 2, ini comment "(recommended 2)" and no re/*.md that I grepped gives a reason for 2 (treat it as an unexplained default).

## Arcade DD01 (ARC1_DD01, 7 AI + human script, clock 370 s)

| t | event |
|---|---|
| +5 | 58 stacks behind a shut door, $6.5M armed |
| +24..+25 | bots 1-6 heist stage 1 (entered the vault) |
| +33..+61 | first take +33, last take +61: all 58 stacks emptied (peak AI record money 7.46M incl. drops) |
| +58..+67 | stage 1 -> 2 (left with loot), money per bot: 710k, 872k, 922k, 1058k, 1120k, 1200k (about 6-11 stacks each) |
| +79, +85, +108, +141, +191, +224 | 6 bots DEAD, their money 0 |
| +204 | bot 4 (1.882M) calls the van; boarded +318 |
| end (+382) | 1 boarded, banked $1.882M |

So Arcade bots have no 2-stack limit: they empty the whole vault in 28 s, each carrying about 1M. The Arcade result is then decided by survival, not by loot.

## Comparison

| | online DH1A | Arcade ARC1 |
|---|---|---|
| stacks taken | 14 (cap) | 58 (all) |
| carried per bot | 220k | 0.71-1.2M |
| bots that reach the van | 7 of 7 | 1 of 7 |
| banked | $1.54M | $1.88M |
| bot deaths | 0 | 6 |

Caveats: Arcade is one sample (ARC1 only; 1.88M rests on one survivor); online bots are far more durable (OnlineHealthMul) and have no pursuers
on this walk, so with a higher carry they would bank much more than Arcade did. The online "banked" figure is the host hook tally
(OnlineTacticsTake=2 + bank), not the game's own.

## Verdict and recommendation

- Not already matching: the online carried amount per bot is a fifth of Arcade's. If the target is "banked total near Arcade's", the 1.54M is already
  inside the Arcade range of one run; if the target is Arcade's pickup behaviour (the vault gets emptied, the money is visible gone from the loot bar), it is not met.
- Closing key (existing, default left at 2): `[BotFill] OnlineTacticsCarry=6` (or up to 8). Prediction (not run): 7 bots x 6 x 110k = 4.6M carried, the
  44-58 stacks last about 8 more grabs per bot at 4 s each, so the vault would be empty near +80 s, walk 63 s, boards near +150 s, inside the 273 s round.
  Risks to check in a bench: (a) the 63 s walk with 6 grabs of mixed distance may overrun the stall clocks (OnlineVanGatherSmart margin 60 s, late rules);
  (b) a big bank is higher than Arcade's expected survivors, so the owner may want a death-rate or a cap that keeps the total near Arcade's
  median instead (a new key would then be `OnlineTacticsBankCap`, default 0, a ceiling on credited tally; NOT proposed until the owner says which target counts).
- Suggested bench (next step, needs the game): DH1D = DH1A with `OnlineTacticsCarry=6`, same pair, then DH1E with 8. PASS: GRABBED lines > 14 per round, boarded 7,
  asserts/faults 0, van called before clock left 60 s. Compare against Arcade ARC1 again (a second Arcade DD01 run would tighten the 1.88M sample).
- The cap is a global constant (Carry 2 for every map), not a DD01 fault; other maps were not checked here.
