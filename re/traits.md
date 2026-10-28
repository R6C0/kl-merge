# Character traits (track traits, 2026-10-23) - NOT RUN IN THE GAME

`klhook/kltrait.c`: each of the 16 wardrobe characters carries a small trait. It applies to the human wearing
that body and to an AI crew bot wearing it. OFF unless `[Traits] Enable=1`. The file writes no memory and calls no
game function: it answers "which character does crew record N wear, which factors does he carry", and the modules
that already own a proven write site multiply their own number by the factor.

Who wears whom: `klcrew.c klw_who_now` (+ `klw_source` names; the stock 8 heisters when there is no wardrobe),
refreshed every 500 ms on the game thread. A body outside the list (policeman, stranger) has no trait.

## Knobs and their write sites (nothing new)

| Knob | Human | AI heister |
|---|---|---|
| Health | klbalance.c `klr_player_tick` max health (with Tough / PlayerHealth) | klgrudge.c `kly_health` (CrewHealth's write) |
| DamageIn | folded into Health: effective = Health / DamageIn (no per-victim damage write exists) | same |
| DamageOut | NOT applied (no per-shooter write site proven) | klgrudge.c `kly_aim`: accuracy % x DamageOut (clamped 0..100) |
| AimSpread | NOT applied (his aim is his hand) | klgrudge.c `kly_aim`: acc' = 100 - (100 - acc) x s |
| Regen | klbalance.c regen delay and time divided by it | NOT applied (the hook writes none) |
| ReviveTime | kldown.c get-up speed divided by it (>1 = longer) | klbotdown.c `LieSeconds` x it (needs `[BotDown] LieSeconds > 0`) |
| Adrenaline | when HE is the helper: kladren.c Meter floor x it | when HE is the helper: kladren.c Rate = 1 + (Rate - 1) x it |

Every factor is clamped to 1 +- `[Traits] MaxDelta` (default 0.25, max 0.5). Absent key = 1.0.
Gates inherited, not new: AI half = `[Bots] Enable=1`, Arcade, a level that is NOT the stock one of its slot;
human half = `[Balance] Enable=1`, same gate; recovery knobs = `[Down]` / `[BotDown]` / `[Adrenaline]` Enable.
So traits do NOT apply on Dog Days' 9 stock FA maps (open question).

Keys: `[Traits] Enable= Dry= (log only) Log= MaxDelta=`; `[Trait.<Name>] Health= DamageOut= DamageIn= Regen= ReviveTime= Adrenaline= AimSpread=`.
Log: `trait: on; ...` once, then `trait: record N = <name> (human|AI heister) Health x1.08 ...` once per record and body.

## Shipped table (flavour guessed, tune freely; `C:\kl_build_1019\traits_1023\KLHook.traits.patch.ini`)

Dead Men characters are the owner's wardrobe names; the flavours are my guesses. AimSpread < 1 = tighter, ReviveTime < 1 = back up sooner.

| Character | Flavour | Health | DamageOut | DamageIn | Regen | ReviveTime | Adrenaline | AimSpread | eff. health |
|---|---|---|---|---|---|---|---|---|---|
| J.C. | all-rounder, quick to recover | 1.00 | 1.00 | 1.00 | 1.10 | 0.90 | 1.00 | 0.95 | 1.00 |
| Tommy | brawler, sloppy aim | 1.08 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.10 | 1.08 |
| Pierre | marksman, fragile | 0.90 | 1.05 | 1.00 | 1.00 | 1.00 | 1.00 | 0.85 | 0.90 |
| Liam | medic, quick back on his feet | 0.95 | 1.00 | 1.00 | 1.15 | 0.85 | 1.15 | 1.00 | 0.95 |
| Jean | steady, slow to rise | 1.05 | 1.00 | 0.95 | 1.00 | 1.10 | 1.00 | 1.00 | 1.11 |
| Elwood | heavy, slow, loose aim | 1.15 | 1.00 | 1.00 | 1.00 | 1.10 | 1.00 | 1.15 | 1.15 |
| Bud | nervous, adrenaline junkie | 0.90 | 1.00 | 1.00 | 1.10 | 1.00 | 1.20 | 1.00 | 0.90 |
| Mitchel | hits hard, thin skin | 0.90 | 1.05 | 1.05 | 1.00 | 1.00 | 1.00 | 1.00 | 0.86 |
| Kane | steady professional | 1.05 | 1.00 | 0.95 | 1.00 | 0.95 | 1.00 | 0.90 | 1.11 |
| Lynch | volatile: hits hard, low health | 0.85 | 1.12 | 1.00 | 1.00 | 1.00 | 1.10 | 1.10 | 0.85 |
| Ashkanan | patient shot | 0.95 | 1.00 | 1.00 | 1.05 | 1.00 | 1.00 | 0.90 | 0.95 |
| Meldal | tank, slow to rise | 1.08 | 1.00 | 0.95 | 1.00 | 1.15 | 1.00 | 1.00 | 1.14 |
| Red | aggressive | 0.92 | 1.08 | 1.00 | 1.00 | 1.00 | 1.00 | 1.05 | 0.92 |
| Parker | sharpshooter, light | 0.92 | 0.95 | 1.00 | 1.00 | 0.90 | 1.00 | 0.88 | 0.92 |
| Standen | bruiser | 1.08 | 1.00 | 0.95 | 1.00 | 1.00 | 1.00 | 1.10 | 1.14 |
| Hutchison | recovering fighter | 1.00 | 1.00 | 1.00 | 1.15 | 1.00 | 1.10 | 0.95 | 1.00 |

Balance vs "the AI is too OP": mean effective health 0.998, mean AimSpread 0.996, mean DamageOut 1.016
(a crew of random bodies is neutral to slightly easier on aim; no character is beyond +-15 % effective health).

## Verification (offline)

- Both builds compile with no warnings: `klhook\build.bat` (SHIP) and `build_auto.bat` (TEST).
- `klbotdown_test.exe`: ALL PASS (0 failures) with a `kltt_get` stub (traits off in that harness).
- `kladren_test.c` already did not build at the base commit (`kltr_set`, `kle_gap_exempt` from klescort.c are missing in the
  harness); a stub was added for traits but that harness was not fixed here.
- Not run in the game.

## Live test (for the lead)

1. `INSTALL traits 1023.bat test` (or SHIP), then paste `KLHook.traits.patch.ini` into KLHook.ini; also needs `[Bots] Enable=1`,
   `[Balance] Enable=1` and the wardrobe on.
2. Scripted DM01 Arcade run (kl_autotest, same ini as the S13 run). PASS lines in KLHook.log:
   `trait: on; MaxDelta 0.25`, one `trait: record N = <name> (human|AI heister) ...` per crew record,
   `grudge: record N (...): health ... x<f>` matching Health / DamageIn of that name, accuracy lines for AI with a changed AimSpread,
   `balance: your health set ... maximum` scaled by the human's trait, no faults, clean exit.
3. Dry=1 first: only the `trait:` lines, no change in the other lines.

## ONLINE (wk-trait, 2026-10-28; NOT RUN IN THE GAME)

Two separate things, both off by default:

1. `[Voice] OnlineTraits=1`: the LOCAL online human's trait is only known and logged (for kltalk.c). `kltt_get()` still answers 1.0 for every online record: a human's health and timers are per peer, nothing is written.
2. `[BotFill] OnlineBotTraits=1` (this section): the AI heisters (bots) of an online FA round, on the HOST only. Needs `[Traits] Enable=1`, `[BotFill] OnlineHost=1`, `OnlineTactics=1` and `OnlineLooks=1`.

Who is the bot: an online bot has no crew record, so the identity is the character the host DREW for him in klcrewlook.c (OnlineLooks=1, `klcl_t.e[digit-1].ch`, an index into the wardrobe list of the host's level). `klcl_bot_look()` answers it only for a bot whose look is APPLIED (klcl_note code 1 or 4); a kept body, a skipped or still pending look is no trait. The name comes from the host's wardrobe (`klcl_bot_name`), the factors from `[Trait.<Name>]` (`kltt_set_of`, clamped by MaxDelta). Pure logic: `klbottrait.h` (`klbottrait_test.c`).

| Knob | Online bot (host) | Where |
|---|---|---|
| Health, DamageIn | APPLIED: every hit on that bot is multiplied by DamageIn / Health (same as a maximum health of Health / DamageIn for equal hit counts). Independent of, and multiplied with, OnlineBalance's Tough (1 / Tough). Point-blank steps and non-positive scales are left alone, as Tough does | `klbalance.c` `klr_cb_hit` (outer) -> `klr_cb_hit_in` -> `klr_tr_orig` (the shim every `orig` call of the existing slot-423 paths goes through) |
| ReviveTime | APPLIED: `[BotDown] LieSeconds` x it (needs `[Down] OnlineBotDown=1`, LieSeconds > 0) | `klbotdown.c` |
| DamageOut, AimSpread | NOT applied: no online accuracy write for bots exists (`klgrudge.c kly_aim` runs on Arcade crew records only) | - |
| Regen | NOT applied: the hook writes no regeneration for a bot | - |
| Adrenaline | NOT applied: online has no bot helper path (`kladren.c` needs the crew records) | - |

Design choice: the slot-423 hit wrapper is armed whenever OnlineCopToBot, `[Balance] Online`, OnlineBalance OR OnlineBotTraits is on (`klr_tick`). The old paths are untouched: the outer wrapper only decides a multiplier (`klr_tr_mult`) and the shim applies it around the real routine, restoring the scale after, as those paths do. With the key off the multiplier is always 1.0 and the shim is a pass-through. Human seats keep 1.0.
Caveats: the lost-hp counters of OnlineBalance / OnlineCopToBot include the trait while their "without the factor" numbers do not. A bot whose look is not applied yet (first seconds of the round) has no trait. `Dry=1` resolves and logs, applies nothing.

Log (grep `trait:`): `trait: OnlineBotTraits=1 ...` once; `trait: online bot <actor> wears <name>: Health x.. DamageIn x.. ReviveTime x.. APPLIED (hit scale x.., LieSeconds x..); DamageOut x.. AimSpread x.. Regen x.. Adrenaline x.. NOT applied online` once per bot and look (or `... no [Trait.<name>] block, no trait`); `trait: online bot <actor> hit: scale a -> b (DamageIn / Health x..) #n` for the first 3 hits; `trait: online bots 30 s: ...` counters (hits seen, scaled with mean multiplier, refused writes, lie applied).
