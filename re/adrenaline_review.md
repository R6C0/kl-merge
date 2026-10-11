# Track Y2 (adrenaline) - adversarial review, 2026-10-11

Verdict: **ACCEPT WITH FIXES.** Nothing in klhook/kladren.c can crash the game on the evidence I could check (every read goes
through klh_rd / the vtable checks, every write through klh_data, it is off by default, and a Dry mode exists). But it does not
deliver the owner's first ask, and most of what it does cannot fire in a default game.

Checked by reading only. No MSVC (`cl`) on this machine, so I could not re-run kladren_test.exe or re-compile. The two DLLs
exist at the sha1 values in the report (test 47a0ee62, ship 34de6bee), and the macros the part borrows from kldown.c exist (KLD_CLOCK
kldown.c:263, KLD_ONE :272, kld_s.meter :296).

## MUST

1. **The part is not wired in the repository.** `git diff HEAD -- klhook/klhook.c` is empty and `grep kladren klhook/klhook.c`
   finds nothing. The three wiring lines exist only in the scratch copy G:\kl_scratch\Y2\src. kladren.c and its harness are
   untracked. A build from the repo has no [Adrenaline]. Either apply the three lines (include after kldown.c, `kad_init()` after
   `kld_init()`, `kad_tick(game_thread)` before `kld_tick`, klhook.c:647 / :826) or write in the note that they are owed.
   The ordering requirement (kad before kld) must stay in the note, because kldown.c:1190 and :2294 decay the meter.
2. **The owner's point (a) is not delivered, and the report's "b to e" depend on it.** Everything for a downed bot (lie speed-up,
   share, traitor mark) keys on byte `[actor+0x64c]`. In the logs an AI heister at health 0 died in 267 of 267 cases, and
   `[Down] Bots=1` is documented in CLAUDE.md as a test key "NOT shown to work". So with the owner's ini the bot branches never
   run. The only live branch is the downed human with a bot or human beside him. Say this plainly to the owner, so the
   "traitor for flooring a crewmate, normal again if you revive him" rule is not believed to be on.
3. **The traitor-mark attribution can brand an innocent human.** `kad_tick` marks `by` when his word `[score+0x1b8+2h]` rises in
   the same pass a bot goes down. By re/player_down.md 11.1, slot 131 raises that word for any NPC the human floors, including
   a policeman or a civilian. Police hitting a bot in the same pass as the human killing a cop is rare but possible, and the mark
   (client flag 1, `[player+0x2726]`) is then removed only if he helps that bot up. Require the victim to be near the human's
   fire, or keep the mark Dry/log-only until check A4 shows the word rises only for crew victims. Until then default `Mark=0`.
4. **Check A4 in the live order must say what to do if the bots do not turn on a marked human.** The note admits the sense-manager
   call after `0x70f770` is skipped. A marked human whom nobody treats as a traitor gets the label but not the consequence.
   That is half a feature. State it in the owner-facing text.

## SHOULD

5. **The share creates money.** The helped human is never debited, so a bot helping a human or a human helping a human adds
   `Share x carried` to the pool of money. A human who floors a bot, then revives him, gets the share (banked at `[score+0x38]`)
   and the mark is removed: a farmable loop. Cap it (once per bot per round) or debit the helped man's carried money when
   he is the local human too.
6. **`HumanFast` (default 0) breaks the owner's 20:40 rule** (never faster than normal), as the report admits. The default is
   right. Keep it out of the sample ini block, or mark it in capitals.
7. **NeedUse reads bit 2 of `[player+0xa54]` as "Use"; this is a guess** (re/hud_popup.md 7.12). With NeedUse=0 any human within
   2.5 m counts as helping, so walking past a downed bot "helps" him. Run A2 before the owner sees any NeedUse=0 build, and
   raise MinHelp from 0.4 s if the walk-past shows in the log.
8. **Pulling `[dnd+0x14]` earlier** is declared unread elsewhere ("no reader but the script's compares"). It is plausible
   (player_down.md 662 and 728, where BotsLie writes it too) but not proven. A0 and A1 should include a check that the bot's
   health reads 75 % when he rises, because that is how a premature end would show.
9. Online is not a goal here, but note that `kad_g.kw[]` and the per-record state are keyed by record index and survive a
   record being reused only through `k->actor` compare; fine for groundwork.

## What I confirmed

- Reads are guarded (`klh_rd`, vtable equality tests for player, soldier, actor, the `[soldier+0x40] == actor` back-pointer,
  `[dnd+4] == soldier`), the part returns on any failed read, and stalls (dt over 512 ticks) give no credit.
- The mark is only ever cleared when this part set it (`keep` flag), a foreign flag is never touched, and a death while marked
  hands the mark to the game. This is the safe design.
- The report is honest about what is assumed and what is not done.
