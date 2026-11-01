# Scheduled check-in 2026-11-01 ~02:50 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll` written 02:47 UTC (sha1 8611f27f = c9's TEST twin of ship1101), ReShade logs 02:47-02:48, `KLHook.ini`
  01:19 (12d5f8e1 = the ship1101 ini). A local session (c9/ce) is benching right now, so no game run and no install from here.
- `KLHook.result` still the 10-27 PASS (F04); `KLHook.log` ends 10-27 20:50 (the benches log into their own live dirs).
- Dumps: newest `KLHook_1.dmp` 10-26 08:11 and `kl2_490_crash_2026_10_25T19_18_39C0.mdmp`, both older than the 10-26/10-27 triage
  notes -> nothing new to triage. `<DM>\KL_PortTools\build`: newest `lenscrack_1031` (10-31 14:55, the still-uninstalled kit).
- Repo head at the start: 6b4a99b (02:06 UTC). Cloud `kl_tests`: 30 pass, 0 fail, 15 skip (gcc -m32 installed here).

## Finding 1 (FIXED in this commit): "Recommended" in KL Mod Options would have undone ship1101
`python tools/kl_mod_options.py --ini <copy of the live ini 12d5f8e1> --recommended` (dry run) listed, among its writes:
```
[BotFill] OnlineGetUp = 0
[BotFill] OnlineGetUpBeacon = 0
[BotFill] OnlineGetUpKeepGoal = 0
[BotFill] OnlineHost = 0        (after an earlier dependency write of = 1: the row's own write wins)
[BotFill] OnlineTactics = 0
```
Cause: the rows `onlinegetup`, `onlinegetupbeacon`, `onlinegetupkeepgoal`, `onlinebothost`, `onlinetactics` still said
`'off'` / "recommended off" / "NOT run live", and the repo ini's markers for OnlineGetUp / OnlineGetUpBeacon / OnlineGetUpKeepGoal said
"(recommended off)", OnlineHost "(recommended off until the two-instance test passes)", OnlineTactics "(recommended off until BO2 passes)".
All five are live in the owner's ini (OnlineHost/OnlineTactics since 10-26 at his ask, every ship since ship1028; the get-up keys since
ship1101) and proven: BO1/BO3..BO6, WK2, Q28 (21 maps online both seats), BP18/BP19, SHIPCHK5. Every other OnlineGetUp* row said "NOT run live".
Fix: rows flipped to `'on'` with the proof names in their notes; repo ini markers "(recommended on; proven live: ...; shipped ship1101)" for
the 14 shipped get-up keys and the two masters; OnlineGetUpRange's line now says 2500 = Arcade's RushRange 25 m, ship1101 has 8000, next
ship 2500 (c9 11-01). Checks: `kl_mod_options_test` 46/46, `--check-rec` every row agrees (a deliberately flipped copy is caught),
`--check-defaults` / `--check-ini` as before, `--list` on the live copy shows all 13 get-up rows `[x]`, and the Recommended dry run on the
live copy no longer touches any OnlineGetUp* / OnlineHost / OnlineTactics key. No hook C code touched; nothing to build.

## Finding 2 (NOT changed; for ce/c9 to judge): other live settings "Recommended" would still rewrite
Live value -> what the preset writes (own-row recommendation). Some are owner taste (Glare, FrameLimit), some are test-only (Lobby Solo),
some rows still say "until benched" though the keys have been live since 10-26/27:
```
[BotFill] OnlineBoard 1 -> 0      [BotFill] OnlineGuardTake 1 -> 0    [BotFill] OnlineTacticsTake 0 -> 2 (forward: WK2's 0x4e3f40 grab)
[Bots] OnlineFill 1 -> 0          [Dying] Enable 1 -> 0               [Expansion] OnlineSet 9 -> 0 (owner 10-26: random stock + DM map)
[Grenade] Throw 1 -> 0            [Hire] Enable 1 -> 0  [Hire] Online 1 -> 0
[HUD] OnlineIntro/OnlineLoot/OnlineSkulls/OnlineTab/OnlineVan 1 -> 0 ("recommended off until benched")
[Lobby] Solo 1 -> 0  RoundsMax 10 -> 0  TimeMax 10 -> 0
[FrameLimit] Enable 0 -> 1, Fps 0 -> 60   [Graphics] Glare 0 -> 1   (the owner's choices; the preset should perhaps not touch taste keys)
```
Suggested rule: a row whose key the owner set himself (the live ini's inline "; 10xx owner:" comments) should be recommended as he has it,
or the preset should skip owner-commented lines. Not done here: each needs the bench history the local sessions hold.

## Finding 3 (research, no code): online get-up is STRICTER than Arcade once the van is called
`klhook/klbotfill.c` klbf_gu_pass (~line 1220): `if (vstate >= 1 && vstate <= 5) continue;  /* ... (Arcade RushVan) */` - no helper is ever
sent while the van is called / comes / waits / leaves. But Arcade's `[Adrenaline] RushVan` defaults to 0 (kladren.c ~1274): the van never
stops a rush there; RushVan=1 is the opt-in that shrinks it to RushVanRange 8 m. So for "online = Arcade 1:1" (owner rule) the online pass
should NOT skip on van state by default. Note BP20's late down at the van logged "no free bot is within OnlineGetUpRange 8000 cm", i.e. the
pass got PAST this skip - so vstate was not 1..5 at that moment (6+ = gone? or the online vstate read is 0): worth one log line of vstate.
Suggested fix (one key, klbotfill.c + ini + a Mod Options row): `[BotFill] OnlineGetUpIgnoreVan` (recommended on = Arcade):
`if (!klbf_gu_ignorevan && vstate >= 1 && vstate <= 5) continue;` - the repo ini's OnlineGetUp comment now states the current rule.
Left to ce (klbotfill.c's get-up block is theirs and in motion today).

## Owner
- Nothing to install from this check-in (documentation + Mod Options rows only; the next hook build carries nothing new from here).
- Still open from 10-31: `<DM>\KL_PortTools\build\lenscrack_1031\INSTALL_lenscrack.bat` (game closed) if you still want the cracked lens.

# Scheduled check-in 2026-11-01 ~07:00 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll` written 06:43 UTC (md5 6a8bd65c.., 2197504 bytes = c9's Q30 TEST twin), ReShade logs 06:43-06:44 (a launch
  in progress), `KLHook.ini` 01:19 = the ship1101 ini (sha1 12d5f8e1, verified on a staged copy). The Q30 round-2 sweep is running,
  so no game run, no install, no screen from here.
- `KLHook.result` still the 10-27 PASS (F04, 0 asserts, 0 faults); `KLHook.log` ends 10-27 20:50 (Alt+F4 exit; the benches log into
  their own dirs). Dumps: nothing newer than the 10-26 `KLHook_1.dmp` -> nothing to triage. `<DM>\KL_PortTools\build`: newest still
  `lenscrack_1031`. Repo head at the start: ada738d. Cloud `kl_tests` 30/0/15 (gcc-multilib installed here again).

## Finding 1 (FIXED): KL Mod Options 'Recommended' flip-flopped [BotFill] OnlineGuardMode
`onlineguardliveonly` (recommended on) needs OnlineGuardMode and writes it 1 as a prerequisite; `onlineguardmode` itself was still
recommended OFF (row text "NOT run live"). On an ini where the key is absent the first press wrote `OnlineGuardMode=1`; the second
press wrote `OnlineGuardMode=0` (the own-row off write, the prerequisite write is skipped because LiveOnly is already on) - so after
two presses LiveOnly is on and dead, and every further press toggles the key. Reproduced with `plan()` on a copy of the live ini.
Fix (table + proofs, no C code): `onlineguardmode` recommended on - BP8 DD08 (every bot took the least guarded stack, 5 finished 10/10,
0 faults; BP5 before it: 0 loot), BP9 + BP11 (with LiveOnly: 14 stacks finished); repo ini marker to match. Two new table self-tests
in `kl_mod_options_test.py`: no recommended-on row may need a key that a recommended-off row switches off, and Recommended pressed
twice writes nothing the second time (synthetic ini, synthetic + guard keys, and the repo ini). The old table fails all three
(verified on a copy), the new one passes: 59/59, `--check-rec` clean, `--check-defaults` / `--check-ini` as before, kl_tests 30/0/15.

## Finding 2 (FIXED): the dry run and the window said nothing about what a write changes
`--recommended` printed `[BotFill] OnlineTactics = 1` next to real changes, though the live ini already has 1 (a prerequisite write),
and a key the ini never names was indistinguishable from a 1 -> 0 flip. Now every planned write says `(was 1)`, `(already 1)` or
`(new key; the DLL default was 0)` plus a summary line ("14 value change(s), 3 write(s) that keep the value"), and the window's
Save asks first with the list of the value changes (`describe_writes` / `writes_summary`, 7 checks). A new key written to its own DLL
default (OnlineVanGather=1) counts as no change.

## Finding 3 (for ce / c9; nothing changed): the owner's live ini carries NONE of the week's T1 / T3 / T4 keys
Recommended on the staged ship1101 ini (12d5f8e1) = exactly 14 value changes, and they are the week's features:
```
T1  [Keys] Map 1, Hints 1                      (MOD CONTROLS page, 9 keyed features; WK2 10-28)     -> absent, DLL default 0 = OFF live
T4  [BotFill] OnlineTriggers 1                 (bots fire the cop-wave trigger boxes; WK2 10-28)    -> absent = OFF live
T3  [BotFill] OnlineTacticsTake 0 -> 2, OnlineLootParts 1, OnlineLootFinish 1, OnlineLootFinishPause 1, OnlineGuardTake 1 -> 0,
    OnlineGuardMode 1, OnlineGuardLiveOnly 1, OnlineEscortNode 1, OnlineVanGatherSmart 1, OnlineBoardAll 1   (BP4..BP20, WKBC)
    [Grenade] Throw 1 -> 0 (dead feature)
```
[Voice] OnlineTalk (crew banter online, A1TALK PASS), [Shop] OnlineSwap* (T5) and [BotFill] OnlineBank/OnlineBankCredit (WKBC5 pays) have rows
still recommended OFF and are absent from the live ini too (not judged here: their rows' texts name the open points).
So the owner's game (ship1101) runs the get-up rescue and the lift from the week, and nothing of "not a secret feature" (T1),
"AI heisters trigger the cops" (T4) or the Arcade-style looting (T3) that the week plan marks [x]. The NEXT_SHIP list (GuardTake 0 /
Take 2 / LootParts 1 + Grenade Throw 0) covers 4 of the 14. Q29 / Q30 regress the installed ini, i.e. without these keys; the only
multi-map proof with the week keys on is the BP / WKBC / MV1 set (DD04, DD08, F06).
Suggested (c9, needs the game): Q31 = Q29's 21 maps on a TEST twin with the ini = ship1101 + the Recommended delta (`python
tools\kl_mod_options.py --ini <copy> --recommended --apply` on a COPY), then ship it as ship1102 with the same INSTALL/UNDO pattern.
Until then the owner can get the same delta himself with the KL Mod Options window (Recommended, Save: it now shows the 14 changes
first, keeps every owner-noted row and keeps one backup).

## Owner
- Nothing to install from this check-in (Python tool + ini markers only; the next hook build carries nothing new from here).
- Still open from 10-31: `<DM>\KL_PortTools\build\lenscrack_1031\INSTALL_lenscrack.bat` (game closed) if you still want the cracked lens.

# Scheduled check-in 2026-11-01 ~10:50 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll` written 10:47 UTC (sha1 8611f27f, c9's TEST twin), ReShade logs 10:47 = c9's Q31 sweep (all 21 maps on the
  ship1102 candidate ini) in progress, so no game run, no install, no screen from here. `KLHook.ini` 01:19 = ship1101 (12d5f8e1).
- `KLHook.result` still the 10-27 PASS; `KLHook.log` ends 10-27 20:50; no dump newer than the 10-26 `KLHook_1.dmp` -> nothing to triage.
  `<DM>\KL_PortTools\build`: newest still `lenscrack_1031`. Repo head at the start: 740a15d (10:31 UTC).
- Head health in the cloud: `kl_tests` 30 pass / 0 fail / 15 skip (gcc-multilib), `run_harness_linux.sh --check-hook` SHIP + TEST 0 errors,
  15 warnings = the baseline (the `%I64d` one in klslot.c is MSVC-correct), `--check-rec` / `--check-defaults` / `--check-ini` clean.

## Finding 1 (FIXED in the table; the ship1102 ini is c9's call): Take=2 without the bank LOSES the bots' loot
The Recommended set (and so, by inference, c9's ship1102 candidate = ship1101 + the 14-key delta of the 07:05 note + IgnoreVan + Range 2500;
its DELTA.txt is on the PC and was not read) switches `[BotFill] OnlineTacticsTake` 0 -> 2 while the `onlinebank` row stayed recommended OFF,
so `OnlineBank` / `OnlineBankCredit` stay absent (DLL default 0). What that does online, from the code and the research, not a guess:
- Take=2 depletes the stack through the game's own `0x4e3f40` (klbotfill.c ~1527 / ~1570: lump and timed parts), replicated to the clients.
- Online the game cannot bank for a bot: ZOnlineMoneyCtrl slot 26 needs a ZFFPlayer seat (re/bots_online_arcade_1028.md item 4,
  re/bots_bank_online_1028.md "a bot has no ZFFPlayer seat, no record, so none of this runs for it"). Only the hook's ledger (`OnlineBank`)
  + `OnlineBankCredit` (AddSharable 0x5a18c0 to an escaped human seat, before the settlement's equal split) bring that money to the team.
- With Take=0 (ship1101, the live ini) the stack stays for a human (`klbf_bc_log_skip`: "OnlineTacticsTake=0 would double count").
So Take=2 alone = the bots carry money out of the round that the humans could have taken: WK2 10-28 F06 had $1.35M on the ledger, MV1 DD04
$4.56M. The owner would see the AI take the loot and the team score not get it: the opposite of "same as Arcade", where a boarded bot banks
through rules slot 201. The bank code HAS paid live: WKBC5 F06 (+550k +300k +150k to seat 0 up to the 1,000,000 cap), WKBC7 F06 (the
overflow waits in the ledger), MV1 DD04 ($4.56M banked, the client's loot sync matched every step), 0 faults both seats each time; and the
repo ini's own marker said "recommended off UNTIL OnlineBankCredit has paid once". Done here (table + ini markers only, no C code):
- `onlinebank` row recommended ON with those proofs; `onlinetacticstake` now also writes `OnlineBank=1` + `OnlineBankCredit=1` (ticking Take
  alone can no longer lose money); ini markers for OnlineBank / OnlineBankCredit / OnlineTacticsTake say why.
- `kl_mod_options_test`: +3 checks (the take row writes the two bank keys; take and bank rows recommended the same way; a plan that ticks
  take alone writes the bank) - the old table fails all three, the new one passes 62/62; --check-rec / --check-ini / twice-pressed clean.
- Dry run on a copy of the live ship1101 ini (12d5f8e1): 17 value changes = the 07:05 list + OnlineGetUpIgnoreVan + OnlineBank + OnlineBankCredit.
For c9 (ship1102): add `OnlineBank=1` + `OnlineBankCredit=1` to the candidate next to Take=2 (the bank keys were benched together with
Take=2 in WK2/WKBC/MV1; the credit path needs a human to board the van, as the owner does), or keep Take=0 until they are in. Suggested
hook line (klbotfill.c init, ce's file, not touched here): WARN when OnlineTacticsTake=2 and OnlineBank=0 ("money a bot takes leaves the round").
Not covered by the bank: a bot that boards after the last human escaped (said in the round summary); the cap overflow (WKBC7) waits for the
next escapee. `OnlineLootSync` (every seat sees the bots' loot) stays recommended off: every player must set it, LAN broadcast only.

## Owner
- Nothing to install from this check-in (Python tool + ini markers only).
- Still open from 10-31: `<DM>\KL_PortTools\build\lenscrack_1031\INSTALL_lenscrack.bat` (game closed) if you still want the cracked lens.
