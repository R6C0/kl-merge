# Undercover Cop + Cops and Robbers: owner request (2026-10-26)

Written by the cloud session (kl-merge-2d) so the VS Code sessions pick it up. The owner asked for it directly, so this
work is AUTHORISED now, alongside the FA online work (it is online, stage 4, which the owner is already driving).

## What the owner asked (his words, lightly tidied)
"We need that syncing on Cops and Robbers and Undercover Cop, and to rebalance those game modes, and also fix syncing on
them. Undercover Cop needs to make it harder for other players to know who it is: take notes from Death Note: Killer
Within or Among Us, to make the undercover more easily undercover. For Cops and Robbers I'd say give a squad of 4 to each
cop so they can command 4 AI cops, like the AI heisters or like 'luvsics AI', so it's harder for the robbers to play.
Needs more mix-up."
Earlier the same day he asked whether the cop sync fix also covers co-op: answer given = no (co-op is not game type 4).

## Facts already in the repo (static unless marked)
- UCC and C&R are NOT separate modes: game type `[sm+0x5c]==4` like FA; sub-mode word `[0x168e59c]` 0 FA, 1 UCC, 2 C&R
  (re/cops_and_robbers.md). One rules class pair (Sv 0xbd2eb4 / Cl 0xbd31e4) branches on the word.
- So klsync.c's gate (`role 2/3 && mode == 4 && state 0x13..0x1f`, klsy_tick) ALREADY ARMS in UCC and C&R. Nothing was
  ever benched there. Unverified: that UCC / C&R rounds sit in the same session states 0x13..0x1f (GUESS: same rules
  object, so likely), and that Track's cop selection (team 3) is right when HUMANS are on the police side in C&R:
  Track must never move a human's actor (klsy_human guards it; check it holds for type-3 human seats).
- Levels: only Dog Days' 9 stock FA maps carry TEAM_MERC / TEAM_POLICE / UCC spawn sets; our Dead Men maps do not
  (re/fa_round.md, DEGRADED). Bench UCC / C&R on stock maps first (DD01 ...); DM maps need those sets authored.
- C&R lobby: 6..12 players, Ready floor 6, rounds 4+ step 2. UCC has its own voice lines (speaker -5, re/bain.md) and
  the RMC `SetUndercoverCop(bool)` (re/netcode.md), replicated to every peer.
- Bot squads: `ZSquadScript` field-1 EGameType bits FA 1, TeamMode 2, Campaign 4, Heist 8, UCC 16 (re/bots_online_fill.md);
  the online bot machinery (klbotfill.c, BO1-BO14) is the base for AI squads under a human cop.

## Work items (in this order; proposals are marked, the owner picks)
1. SYNC BENCH (no code first): two-instance System Link on stock DD01 with `[Sync] Probe=1 Share=1 Compare=1` and the
   Track settings that passed SP1h, sub-mode UCC (`-o FA2TeamMode` / UCC toggle, re/cops_and_robbers.md) and then C&R.
   Measure as S2b / SP1h did. Expect: AI cops drift as in FA; human cops must be untouched.
2. UCC TELL AUDIT (static, then live): list everything that can give the undercover away today - HUD / name colour /
   scoreboard / kill feed / voice line speaker / loadout / AI cops not shooting him / spawn point / the
   `SetUndercoverCop` flag reaching all clients. Each tell gets a fix or a note why it stays.
3. UCC DESIGN (PROPOSALS from Among Us and Death Note: Killer Within, for the owner to choose; none decided):
   - Fake the job: the UCC can carry and bank loot and is scored like a heister until he acts (Among Us fake tasks).
   - No behavioural tell: AI police treat him like any heister until reveal (otherwise "cops never shoot him" outs him).
   - Kill cooldown / silent takedown, and the kill feed does not name the killer while he is hidden.
   - Sabotage instead of only shooting: call the police early, jam the van or a door for N s (Among Us sabotage).
   - Misdirection: an occasional false "suspicious" ping on a random heister; with 9-12 players, optionally 2 UCCs.
   - Reveal only by his own choice or when seen killing (Killer Within: the killer stays hidden until caught).
4. C&R SQUADS (PROPOSAL from the owner's ask): each human cop leads 4 AI cops that follow him and take simple orders
   (follow / hold / attack), built on the online bot machinery; their count must fit the 12-seat cap and the AI budget.
   ANSWERED (owner, 2026-10-26): luvsic is a collaborator working on co-op for the Dead Men campaign and Dog Days
   (github.com/luvsicccc/a-newer-perspective; our pass: re/luvsic_pass.md). "luvsics AI" = his crew-order AI:
   `third_party/anp/loader/squad.inc` (READ, not run here) gives Dead Men's Follow / Fire at / Defend orders through
   kl2's OWN ZSquadControl, no code bytes changed: 0x908040 Recruit(sc, body) puts a soldier under a player
   (receivers sc+0x1c[], max 16, no duplicate check), 0x4c3900 Follow, ZSoldier script slot 79 0x760e50 MoveTo,
   slot 83 0x831850 Attack(handle, pos, T), 0x6eac60 Refuse; P = ZFFPlayer, sc = *(P+0xcd0). His notes say DD calls
   Recruit only in a HOSTED session and the Attack network path 0x6f64f9 streams the handle - so the engine already has
   an online squad-order path (GUESS that it replicates the orders; unmeasured). This is the base for "4 AI cops per
   human cop": recruit 4 type-3/police ZSoldiers into each human cop's ZSquadControl on the host, give his keys the
   three orders. Open: which police soldiers (spawned per cop, from the level's police squads), and the AI budget.
   His module is ANP-levels-only and single-player; read it, don't link it, and credit him.
5. REBALANCE both modes: needs the owner's feel after items 1-4 (what is too easy / too hard now). Not started.

Rules unchanged: stock maps + private match must work; no stock files outside the test slot; mark guesses.
