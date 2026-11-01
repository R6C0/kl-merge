# Arcade get-up helper: range and van rules (2026-11-01, static, no game run)

## Answer
Arcade's "bot helps a downed human" is NOT stock kl2.exe code (stock heal needs player state 5 = co-op only, re/adrenaline.md). It is this mod's `klhook/kladren.c` `kad_rush` (line ~313), running on the Arcade crew records. So "Arcade 1:1" = kladren's rules. No kl2.exe address is involved in the choice; only the order call `kle_order2` (0x760e50).

## The rules (kladren.c kad_rush; keys read at ~1272)
- Range gate: `[Adrenaline] RushRange`, default 25 m, clamp 2..80 m (`kad_inif`, line 1273). Distance is horizontal `kad_dist`.
- Floor gate: `|dy| > 3.0 m` skips the bot ("another floor: the path may be long"). BP20 (bots 24 m higher) fails this even before range.
- Eligible bot: AI member (flags&1), not traitor, `status == 0` (not aboard=4, escaped=6, dead=7), not down, not already rushing, not an escort of the human, `kle_bot` ok.
- NOT excluded: a bot carrying money, a bot walking out to the van, a bot standing at the van but not yet boarded. Only `status != 0` (aboard/escaped) removes a bot.
- Van rule: `RushVan` default 0 = no van exclusion at all. With RushVan=1 and van state 1..5 the range shrinks to `RushVanRange` (8 m, GUESS) and no rush-back. Default Arcade: the van does not stop a rush.
- Downed human is rushed at once (no 600 ms delay). Order repeats every 2.5 s until the bot is within `BotAnimNear` (2 m).
- Nearest eligible bot wins. Rush-back to the old defend spot after he is up (skipped only if RushVan=1 and van live).

## Verdict for BP20 (bots ~90 m away, 24 m higher, at the van)
Arcade would NOT have sent anyone: 90 m > RushRange 25 m (even > the 80 m max clamp) and 24 m > the 3 m floor gate. Our online result (no bot came, seat rose alone) matches Arcade. A bot already boarded is excluded in any case.
Where Arcade differs from us: it ignores van state and carrying (we need OnlineGetUpBusy=1 for carrying/walking-out bots; re/bot_getup_online.md says no helper while van called/waiting, vstate 1..5 - not re-verified in the current klgetup_logic.h) and its range is 25 m (we use 80 m = OnlineGetUpRange 8000; ini default 2500). Height: Arcade 3 m, we use 4 m.

## Confidence
High (reading kladren.c source; the 25 m / 3 m / status gates are explicit). Medium that the live game ini has no `[Adrenaline] RushRange` override (the live ini has `[Adrenaline] Range=4` only; repo ini has no RushRange line, so defaults apply). kl2.exe itself has no helper logic to check.

## Recommendation for our keys
- OnlineGetUpRange=8000 is already 3x more generous than Arcade (2500). For 1:1 parity set it to 2500; keeping 8000 is a deliberate "better than Arcade" choice, label it so.
- Do NOT add a larger-range-during-escape rule: Arcade has none, and the owner rule is 1:1.
- Optional new toggle for parity: `OnlineGetUpIgnoreVan` (recommended on = Arcade; 0 = off = today's block during van states 1..5). Arcade sends a bot at van state 1..5 as long as status 0 and in range; only an aboard/escaped bot (status 4/6) is never pulled. Keep "aboard is never pulled".
- Keep `OnlineGetUpBusy` recommended on (Arcade pulls carrying/walking-out bots).
- Height gate: Arcade 3 m vs ours 4 m; trivial, leave.
