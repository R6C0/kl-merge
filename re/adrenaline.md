# Adrenaline: help a downed heister up and earn a share; downing a crewmate makes you a traitor until you revive him (track Y2, 2026-10-11 night)

Owner (23:15): *'an adrenaline feature so it speeds up the down player state and the ai heisters and you get a share of
their cut since you helped them'* / *'if you get someone down like that you would be a traitor too but if you revive
them youd become normal again'*. **Offline. Nothing here has run in the game.** READ = kl2.exe 0490 (`debug/dasm.py`),
NOTES = earlier tracks' notes (named), ASSUMED = marked. Files: `klhook/kladren.c` (the part, WIRED in `klhook.c` since the review round, section 10),
`klhook/kladren_test.c` (off-game harness).

## 1. What came of the four points

| | result |
|---|---|
| a. AI heisters go down at the killing hit in place of dying | **NOT made to work - see 2.** What exists: when the GAME puts an AI heister down (byte `[actor+0x64c]`; with `[Down] Bots=1` that is the only way), the part helps him up. |
| b. help speeds the get-up | DONE for a downed AI heister (his lie tick pulled earlier) and for the downed human (kldown.c's mash meter held up; optional the game's own fast get-up). |
| c. the helper's share | DONE as a transfer at the get-up (4). |
| d. traitor by downing, normal again by reviving | DONE as data writes (5); whether the bots then treat him as a traitor is the open live question. |
| e. online groundwork, off on stock / police | state is per crew RECORD; only the banked total and `[player+0x2726]` are the local player's; gated like `kldown.c` (Arcade, `klb_level`, not police). |

## 2. Why (a) is not delivered, and the exact obstacle

Known (re/player_down.md 11): an AI heister at health 0 dies unless `0x70e0e0` says "down not dead"; in 267 of 267 logged
cases it said no; WHICH test refuses (b: ZHitAnimTask running / 16 mesh probes / attachment, d: a head hit within 15 m,
e: damage over 1,000) is not established; `[Down] Bots=1` removes only f / g.

The only way to be independent of that refusal is to catch the killing hit before the death path: wrap the soldier's damage
routine, **ZSoldier vtable slot 96 = 0x8473a0** (thiscall, ecx = the soldier, `[ebp+8]` = pointer to the hit holder; it
reads the actor's health through actor slot `+0x66c`/`+0x670` and writes it at 0x84789d, tests the 'no damage' word
`[[actor+0x54]+0x3a]` at 0x8478f4, and dies at 0x847937 ff.). Design that would work (NOT built): a wrapper that, for a crew
soldier, raises the health object's value AND maximum (`[h+4]`, `[h+8]`) by a large constant before calling the original,
reads the new health afterwards, subtracts the constant, and if the real result is <= 0 sets a small positive health and
puts the bot into a hook-made down state (the 'no damage' bit 0x800 for the lying time, as `[Down] BotsFree` does) - so the
death path never runs. **The obstacle**: the slot may only be wrapped by a PRIVATE vtable copy on each soldier object (the
hook policy: no .rdata write - the vtables sit in the hashed range), and six other parts identify a soldier by
`[soldier] == 0xbd0954` (kldown.c:1290 `kld_bot_ok`, klescort.c:500, klhop.c:183, klmove.c:894, klgrudge.c:230/280/290):
a copied vtable makes every one of them refuse the bot. Also unproven: whether the set-health slot clamps above the maximum,
and which call pauses a soldier's AI while he lies (the game's own down does it through its goal; nothing data-only was found).
**Next step if the owner wants (a)**: give those six tests a second accepted vtable (`kld_soldier_vt(s)` helper in klbot.c),
then build the wrapper in a track of its own. Until then: `[Down] Bots=1 BotsLie=6` makes the game's own down the thing
adrenaline speeds up (BotsLie lengthens it, adrenaline shortens it; with BotsLie=0 the two do not fight over `[dnd+0x14]`).

## 3. How help works (kladren.c)

- **Downed**: an AI record (flag 1 of `+0x79`, a ZFFActor whose `[+0x77c]` is a ZSoldier of vtable 0xbd0954) with `[actor+0x64c]`
  set; the local human with `[D+4]` 1 or 3 (D = `[player+0x2948]`, re/player_down.md 1).
- **Helper**: another record in play (`status` 0), not a traitor, not down, within `Range` (2.5 m; a human helper) / `BotRange`
  (4 m; an AI heister by a downed human - the escort stays about 3 m away, re/bots_escort.md), within 2 m in height. The nearest
  one counts; the milliseconds he is nearest are summed per helper (`MinHelp` 0.4 s decides whether it was help).
  `NeedUse=1` also wants bit 2 of `[player+0xa54]` ('use key held': ASSUMED, re/hud_popup.md 7.12 - `Log=2` prints that dword
  whenever it changes so the key can be checked before NeedUse is turned on).
- **A downed AI heister**: `[[soldier+0x4b8]+0x14]` (the tick his script waits for - the field `BotsLie` writes, 11.3) is
  pulled earlier by `(Rate-1) x` the time since the last pass, never to less than 2 ticks from now (`kad_lie_step`; a pass
  over 0.5 s is a stall and gives nothing). READ: that field is the tick `0x7ea990` sets (now + 1.5 .. 3.0 s) and the script
  compares.
- **The downed human**: `kld_s.meter` (kldown.c's mash meter, 5.x: rate = FlopBase + FlopPerPress x meter, at most FlopTop) is
  held at `Meter` or more under the same condition kldown.c counts presses on (a get-up it drives, or a landed Flop fall). The
  part must therefore tick BEFORE `kld_tick`. With the owner's `FlopTop=1.0` the help brings him to normal speed at most,
  never faster (his 20:40 rule: slow motion up to normal). `HumanFast=1` also writes `[D+0x29]` = 1 (READ in player_down.md 1:
  0x7180b0 turns that byte into the get-up request and 0x478270 plays the clip at `[0xb89a20]` = 2.5): it ASKS FOR the fast
  get-up of the game's plain knock-down while somebody stands by; off by default, it exceeds the owner's rule.

## 4. The share (c)

x = `Share` (0.25, a GUESS) x what the helped man CARRIES (`[score+0x150+4i]`) when he is up and was helped >= `MinHelp`.
- helper = the local human: x goes into the banked total `[score+0x38]` (the int klfedkit.c's `Pay` writes; it survives the
  round and moves the HUD's 'Total score' - re/fed_kit.md 10.3, hud_values.md); `ShareBank=0` puts it into his carried money.
- helper = anybody else: x is added to his carried money (`ShareBot=0` = AI heisters earn nothing).
- `Take=1`: x is taken out of the helped man's carried money, a human's too (review 5: no money is made); `Take=0` = new money, logged. Paid ONCE per helped man per round.

**Why at the get-up and not at the payout.** READ (bots_follow_out.md 1.4, 0x796410): the escaped non-traitors' money is
POOLED and every escapee gets the same share. A transfer between two escapees changes nothing there; extra money added to the
pool is split with everybody. The only increase that stays with the helper is a write after 0x796410 into his own
`[record+0x28]/+0x2c` or into the human's `[score+0x30]` before `0x5e001b` adds it to `[score+0x38]` - those run inside one call
(slot 192, 0x5dff40) the hook cannot sit in the middle of, and 0x783010 (what `[score+0x30]` is made of) was not read whole.
So the share is a banked / carried bonus at the get-up. For the human it is real (banked); for a bot it is carried money that
only matters if he escapes (then it enters the pool and is split - an honest limitation: the owner should know a bot helper
gains next to nothing).

## 5. The traitor mark (d)

Detecting WHO put a crewmate down: READ (re/player_down.md 11.1): at health 0 with a PLAYER attacker the soldier's damage routine
calls rules slot 131 = 0x7cc270, which adds a word to `[score+0x1b8+2*attackerRecord]` BEFORE the down is asked. The part sees a
down byte appear and a human's word rise in the same pass -> that human put him down. ASSUMED (the same word also rises when a
human floors/kills a policeman; a policeman's kill in the very pass a bot goes down by police fire would be misattributed; the
check A3 reads it).

The mark itself copies what slot 129 = 0x8fb0d0 does for a killer (read whole, fed_kit.md 10.2; re-read 0x8fb170-0x8fb21c now):
`or [score+0x1d4+4*h], 1` (slot 115 = 0x7ca230 is that OR with a changed-flag), for the local player `[player+0x2726]` = 1 (0x70f770
writes it, then calls 0x4801a0 for the sense manager - NOT called here: **ASSUMED** that bots read the client flag; if they do not
turn on him, the mark is only the HUD's 'Traitor' and the score page - live check A4), and with `MarkFine=1` `[score+0x24] +=
[tuning+0xc10]` (-25,000). Skipped, as the game does (`test [score+4h+0x1d4],1 / jne`), when flag 1 is already set.
Removal: when that crewmate is up and the same human was his helper for `MinHelp`: flag cleared, the byte put back, the fine
given back. ONLY a mark this part gave: a flag set before is never touched; if any crewmate DIES while the mark stands (the game's
slot 129 would otherwise have marked him for a real kill, and it skips a client already marked) the mark is declared the game's
and kept; a new rules object (next round) clears a leftover mark of ours. The mark does NOT cost the helper-share: a marked
human can still help (that is how he gets clean).

## 6. Keys (`[Adrenaline]`; the sample ini block for the lead to add)

    [Adrenaline]
    Enable=0          ; 1 = the part
    Dry=0             ; 1 = log only, not one write
    Log=1             ; 2 = once a second with a helper, and [player+0xa54] when it changes
    Range=2.5         ; m, a human helper of a downed AI heister
    BotRange=4.0      ; m, an AI heister by a downed human
    NeedUse=0         ; 1 = the human helper must hold Use (bit 2 of [player+0xa54] - a GUESS; check with Log=2 first)
    Rate=3.0          ; a downed AI heister lies this many times faster with a helper
    Meter=3.0         ; the downed human's mash meter floor with a helper (rate = FlopBase + FlopPerPress x meter, at most FlopTop)
    HumanFast=0       ; LEAVE AT 0: 1 asks the game's fast get-up (x2.5) = FASTER THAN NORMAL, which the owner ruled out (20:40)
    MinHelp=1.0       ; s of help for a share / a revive (a walk past is not help)
    Share=0.25        ; of what the helped man carries (a GUESS)
    Take=1            ; out of an AI heister's cut
    ShareBot=1  ShareBank=1
    Mark=0  MarkFine=0   ; Mark=1 is OFF by default until live check A4 (see 10)

## 7. Wiring (done in klhook.c in the review round; HEAD already includes kldown.c)

    #include "kladren.c"                 after  #include "kldown.c"
    kad_init();                          after  kld_init();
    kad_tick(game_thread);               BEFORE kld_tick(game_thread);   (it raises kldown's mash meter first)

(`kla_` is klauto.c's prefix, so this file uses `kad_`.) Compile proof (`git archive HEAD klhook` + kladren.c + the three
lines, `G:\kl_scratch\Y2\src`): TEST `G:\kl_scratch\Y2\test\dinput8.dll` sha1 47A0EE62191947AB8D7DA518B30F89204ADC458F, SHIP
`G:\kl_scratch\Y2\ship\dinput8.dll` sha1 34DE6BEEB574EB9692A62BD7BAFDCC3C2FE6781A (the build stamps its time; no warning or
error line from either build; no line of kldown.c / klbot.c / klbalance.c was changed).
Harness: `kladren_test.exe` (built from `klhook/kladren_test.c` against a fake address space): **ALL PASS (0 failure(s))**, 7
scenarios + the pure functions - mark on a human whose word rose, lie tick pulled 2 s per second of help, share banked and Take,
mark off on a revive, mark kept when unhelped / foreign / a crewmate died, Dry = zero writes, meter floor for a downed human with
a bot 3 m away and none at 9 m / with traitors, a bot helper paid from the human's carried money without debiting him, leftover
mark cleared at a new rules object.

## 8. Live checks (the lead; the bank DM03, owner's balance; Log=2; scripted human; `[Down] Enable=1 Flop=3 Bots=1 BotsLie=6 BotsFree=0 Log=2`)

| run | keys | PASS (log lines) | FAIL |
|---|---|---|---|
| A0 dry | `[Adrenaline] Enable=1 Dry=1 Log=2`, nothing else new | `adren: on (Dry=1 ...`; `adren: a round runs`; per down `adren: record N (bot) IS DOWN ... he lies 1.5 .. 3 s` (needs `[Down] Bots=1`: klbot shows `IS DOWN` in kldown's own line too); with the human walking up `is helped by record 0 (you), 1.x m away`; `adren: Dry - record 0 WOULD get $X`; **`WOULD be marked a traitor`** at the down when the human's bullets did it; no `klh_data` write lines | any write; no `IS DOWN` (then `Bots=1` still does not make a bot go down: obstacle 2) |
| A1 help | `Enable=1` (Dry=0) | the lie tick shorter: `IS UP after` under the 1.5 s the game gives, when helped; compare unhelped (stand away): `IS UP after 1.5 .. 3.0 s` | `IS UP` not sooner with help; a fault; the bot stays down for good |
| A2 Use | `NeedUse=1` after A1, `Log=2` | `[player+0xa54] .. -> .. (bit 2 ... 1)` while the human holds E near the bot and 0 when released; help only while held | bit 2 never changes (the guess is wrong: find the byte; NeedUse stays 0) |
| A3 share | A1 + the human carrying money | `adren: SHARE - record 0 (you) gets $N (... banked: [score+0x38] A -> B)`; `record 1 (bot) carries $.. now (was $..)`; the HUD's 'Total score' jumps by N | no line; 'Total score' unchanged (then `[score+0x38]` is not the HUD's total in this state) |
| A4 mark | A1, the human shoots a bot to the floor (the owner's rules: his bullets, not police) | `adren: MARK - record 0 is a TRAITOR (client flags 00000000 -> 00000001) because his bullets put record N down`; the HUD block orange 'Traitor'; **do the bots shoot at him** (klbot / klbalance hit lines `you lost` from bots; `[Bots] Log=2`); then he helps the bot up: `UNMARK - record 0 is a normal heister again` and the HUD normal | the mark with no HUD change (the flag is not the one the HUD reads); a MARK after a police kill (the word misattribution - say which kill); the mark does not come off |
| A5 foreign | the human kills (not downs) a bot | the GAME marks him; no `adren: MARK`; after a later revive no `UNMARK` | `UNMARK` of the game's mark |
| A6 human down | `[Down] Flop=3`, the idle human shot to the floor with an escort beside | `YOU ARE DOWN`; `is helped by record N (a bot), 2.x m away`; kldown's `get-up: ... speed` lines show speed at FlopTop quickly (meter >= 3), `UP after` shorter than an unhelped knock-down; no `adren:` line when the escort is farther than BotRange | meter not raised (kld_s.up / the landing condition not met: say what kldown printed) |
| A7 round change | two rounds | `a round runs` again; a leftover mark of the first round is gone; no write at the menu | a fault; the mark carries into the next round |

## 9. ASSUMED / not done

- ASSUMED: `[dnd+0x14]` has no reader but the script's compares (11.6) so pulling it earlier ends the lie; slot 131's word rises in
  the pass a human floors a bot; `or [score+0x1d4+4h], 1` plus `[player+0x2726]` are the whole data side of the mark (the sense
  manager call is missing); bit 2 of `[player+0xa54]` is Use; kldown's `kld_s.meter` is not rewritten between my tick and its own
  (no earlier reset in the same pass); `[D+0x29]` stays until D is cleared (HumanFast writes it back to 0 when the help ends).
- NOT DONE: (a) as in 2; the share at the payout (4); another human's banked total (online: `[score+0x38]` is the local client's -
  other humans are paid in carried money, but their PLACE is not read: only the local human can be a helper or be helped); an
  AI heister helping an AI heister (no 'revive' tactic - the owner asked for human and heister roles only); the order for a
  bot to walk to a downed human (the escort's 3 m already is that); sample `KLHook.ini` block (text above, the lead adds it);
  a prompt/HUD line for the helper.
- Not touched: kldown.c, klbot.c, klbalance.c, klescort.c, klhook.c, KLHook.ini.

## 10. Review round (fixer, 2026-10-11 night; review: re/adrenaline_review.md)

Done: MUST 1 (wired in klhook.c: include after kldown.c, `kad_init()` after `kld_init()`, `kad_tick` before `kld_tick`; the order
must stay, kldown.c decays the meter), MUST 3 (`Mark` default 0 until A4), MUST 4 (stated below), SHOULD 5 (share paid once per
man per round, and debited from the helped man whoever he is under Take=1), SHOULD 6 (HumanFast stays 0, capitals in the ini
block and the header), SHOULD 7 (MinHelp default 1.0 s; run A2 first, raise it if walk-bys show), SHOULD 8 (the get-up line now
prints the lie at go-down and the helped man's health object `[+4]`/`[+8]` RAW; if the lie was ended by our pull too early it
shows as a health at or near 0; layout of that object is NOT read). Not refuted: all. MUST 2 is a fact, not a fix: (a) stays undelivered.

**For the owner, plainly:** with his ini today only the downed-HUMAN path can act (an escort bot beside him speeds his get-up up
to normal speed at most); an AI heister does not go down at all (267 of 267 died; `[Down] Bots=1` is not shown to work), so the
speed-up of bots, the share for helping a bot and the rule "you are a traitor for flooring a crewmate, normal again when you
revive him" are NOT live. The mark is off by default, and even when switched on a marked human may only get the label: the
sense-manager call is skipped, so bots may not turn on him (A4 decides). A bot helper earns next to nothing (payout pools the money).

Checks: `kladren_test.exe` ALL PASS (28 ok, 0 failures; scenario 6 now checks the debit and the once-per-round cap); builds from
`git archive HEAD klhook` + the working-tree klhook.c and kladren.c, no warning or error line: TEST `G:\kl_scratch\Y2f\test\dinput8.dll`
sha1 9022e5afc191e7e0d4c29f798bfc080bde097558, SHIP `G:\kl_scratch\Y2f\ship\dinput8.dll` sha1 f4d470580f5f4e100fbfba1a1bc87c9960631149.
Live order unchanged (A0 dry, A1, A2, A3, A4 with `Mark=1`, A5, A6, A7); A0 now needs `Mark=1` set to see the WOULD-be-marked line.
