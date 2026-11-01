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
