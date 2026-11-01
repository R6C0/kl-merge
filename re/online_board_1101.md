# Online round-over board = Arcade (2026-11-01, branch wk-onlineboard-1101)

Status: code written, off-game tests pass, NOT run in the game. Key: `[HUD] OnlineBoardBots` (default 0).

## 1. What the log really says (correction of the task text)

The line `hud: scoreboard: ONLINE state 24 (the stock round-over panel stays; the Arcade board is not drawn online yet) ... 12 rules records (NOT seats), 0 names`
is a STALE diagnostic. It is printed by klsb_tick's `!have` branch (the ARCADE readers klb_read refuse online) once per state >= 0x1d, whatever the card does.
It never said the card was missing. In the same real round (RT2L_DM09/inst1, 2 humans + 7 bots, round 1 of 3):

- `OnlineBoardCarrier: 3 s in state 1f: ZFAOutroDisplay ... OUR private copy ... card drawn on it +765, stock +0 (shown)` = the Arcade-style card IS drawn online
  ([HUD] OnlineBoard=1, OnlineBoardState=1, OnlineBoardCarrier=1, proven BOSE5g, 184 draws on both peers; the three keys are already on in the owner's ini).
- The pre-round card is drawn too (OnlineIntroCarrier, `card drawn on it +241, stock +0`).

So the board exists online; the log line only misled. I reworded it (log text only, no behaviour change).

What the online card did NOT have (the real gap):
1. AI heister rows: no payout (`-`), fate only `AI` or `DEAD` (live-or-dead from the Actor scan). With `OnlineBoardTake=1` a living bot is `LEFT BEHIND`
   (the code comment already says: a bot has no score row, flags and money read 0, so `ESCAPED` NEVER shows). An escaped bot (boarded, removed from the world) simply
   disappears from `o->bot[]`, so it had no row at all in the final board.
2. No per-round memory of the bots, so the roster at 0x1f is whatever the scan sees at that moment.

## 2. Design

`klhud_boardbots_logic.h` (pure, no windows.h, `klhud_boardbots_test.c`, 24 checks) holds a LATCH table (`kbb_tab`, 12 slots) of the AI heisters.
`klsb_bots_track` (klhud_board2.c, game thread, tick) fills it every tick in states 0x19..0x1f and clears it in the intro states 0x16..0x18 (so every round starts empty).
`klsb_compose_online` uses the table (instead of the live scan only) for the bot rows when `[HUD] OnlineBoardBots=1` and the table is not empty; else exactly today's code.

### Where each cell comes from

| Cell | Source | Seat | Status |
|---|---|---|---|
| Humans (all columns) | klonline_read snapshot (seat table, S arrays, +0xefc local seat) | both | unchanged, proven BOSE5g |
| Bot name | character from the body's model (`klor_char`), as before | both | proven (names_ok) |
| Bot row exists after it left the world | latch (seen alive earlier in the round) | both | NEW, GUESS that a boarded bot leaves the scan |
| Bot fate DEAD | seen with health 0 in the scan (latched; stays DEAD if the body despawns) | both | NEW |
| Bot fate LEFT BEHIND | in the scan, alive, at 0x1f | both | as OnlineBoardTake |
| Bot fate ESCAPED, host | `klbf_ob[i].phase == 3` (aboard) of the hook's puppeteer, via `klbf_ob_ledger(actor)` (klbotfill.c, read only) | host | NEW; GUESS: klbf_ob actor == the HUD scan's actor (same ZFFActor), the OB1 line counts matches |
| Bot fate ESCAPED, client | INFERRED: latched alive, no longer in the scan, never seen dead, van state `esc_state >= 4` (`KBB_VAN_LASTCALL`, GUESS: 4 last call, 5 leaving, 7 seen at 0x1f) | client | GUESS, wrong if a live bot is deleted for another reason |
| Bot fate AI | no evidence either way | both | shown as `AI`, not invented |
| Bot PAYOUT | host ledger `klbf_ob[i].tally` for ESCAPED, 0 for dead / left behind | host only | NEW |
| Bot PAYOUT on a client | nothing replicates the ledger (the game's seat table has no bot rows) | client | `-` (cannot be filled; not faked) |

NOT changed: the human columns, KILLED BY, LIVES, ROUND n OF m, the ring, ROUND SCORE slot (still KILLS unless OnlineBoardTake), TOTAL SCORE.
The GRADE letter column stays humans only (bots have no record).

Why host-only money: `klbotfill.c` (OnlineBank, line ~1034) documents that online rules slot 46 needs a ZFFPlayer with a seat, so the game itself cannot bank for a bot;
the only record of bot loot is the hook ledger on the host. In the real RT2L round the ledger was `0 bot(s) banked $0 of 675000 carried`, i.e. bots carried money but none boarded.
To get the same payout on the client one would have to ship the ledger over the hook's net channel (klnetchan) -- not done, out of scope, would be a netcode change.

### Safety
SHIP-safe: no .text patch, no debug registers, no new vtable. Reads only (the actor scan the snapshot already did plus one read-only accessor into klbotfill's table). No new game writes.
Default 0 = byte-identical behaviour (compose takes the old branch when `klsb.bots == 0`). Options row `onlineboardbots` in tools/kl_mod_options.py, ini doc line in KLHook.ini.

## 3. What this does not do (open points)
- Arcade's board has other columns online has no data for: round score per heister (the stock online money is Sharable+Unsharable), per-bot kills. They stay as before (kills slot of the local seat only).
- The Arcade shop lead on the countdown (G13) is unchanged.
- An undead-then-despawn rule: a bot seen dead whose body vanishes stays DEAD (tested); a bot that vanishes before it was ever seen alive (killed between two 100 ms ticks) shows `AI`.
- Ordering: latch order is first-seen, not "living first" as the old rows; with 9 bots + 2 humans the 12-row cap hides the last ones (`KBB_MAX` 12, `KLSB_NROW` 12).

## 4. Bench plan OB1 (DM09 + DD06, two seats, NOT run)

Ini on both seats (on top of the current live ini): `[HUD] OnlineBoardBots=1`, and on the HOST `[BotFill] OnlineBank=1`, `OnlineBoardAll=1` (so the ledger exists and bots board). Run a full 3-round match on DM09 (Retomoto, 7 bots) and on DD06, with
one round where the humans let the van leave with some bots aboard, one where a bot is killed, one where the van never fills.

Lines to grep (`KLHook.log` of each seat):
- `grep 'OnlineBoardBots' KLHook.log` -- one summary per round at state 1f: `N AI heister(s) latched, D DEAD, E ESCAPED (...), L LEFT BEHIND, A unknown; host ledger knows K (this seat is the HOST | no ledger: CLIENT...)`, then one `bot i actor ... -> fate n` line each (fate 0 AI, 1 DEAD, 2 ESCAPED, 3 LEFT).
- Host: K must equal N (GUESS actor identity holds). K == 0 on the host with OnlineBank=1 = the actor ids differ: then the ESCAPED fate is only the inference; fix before trusting.
- `grep 'botfill: bank:' KLHook.log` -- the host's `round ledger: n bot(s) banked $X`: the sum of `ESCAPED` payouts on the host card must equal X.
- `grep 'OnlineBoardCarrier: 3 s in state 1f' KLHook.log` -- still `shown` (the card draw path is unchanged).
- Compare with the screenshots at state 1f: host card shows `$` on ESCAPED bots, client card shows `-`; both show the same fates (host from ledger, client inferred): any host/client disagreement is a finding about the inference.
- Pass = both seats draw the card, no `FAULT`, fates plausible against what happened on screen; the client ESCAPED inference agrees with the host ledger in all rounds.
