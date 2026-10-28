# Arcade-only bot modules vs the online host (wk-arcmods-1028, 2026-10-28)

Static work only: NOT RUN in the game. CERTAIN = read in code / earlier logs. GUESS = inferred.

## Why they are inert online
The Arcade test 0x7f6850 is false for online roles 2/3, so there are no tactics and no crew records (ZGameRulesHeist crew table at rules+0x348, 0x7c bytes each).
klr_arcade (klbalance.c) and klb_read (klbot.c) require session mode [sm+0x5c]==4 and sub-role != 2/3. Every module below that calls them is dead online.
The online host has the AI heisters anyway (ZFFActor vtable 0xbb3bac, team Ally, a ZSoldier at actor+0x77c, health via actor+0x5fc), found by the census in klbotfill.c / klbotdown.c.
Clients run no tactics: bots reach them only as KLSY2 / DDL_ZFFActor puppets, so anything that must show on a client has to be a host-side change of the actor itself.

## Bridge added
`klbotdown.c: klbd_online_view(who, snap, why)` returns 1 only for the HOST (role 2, mode 4) in a round (states 0x13..0x1f, KLB_ROUND 0x19), and fills a klb_snap with PSEUDO records
(one per Ally bot from the census: actor, status, flags; no money, stage 0). `who` selects one of 3 private slots so modules do not disturb each other's per-bot state.
A client or a lobby returns 0. `klbf_ob_stage(actor, dflt)` (klbotfill.c) gives the heist stage of a bot from the puppeteer (aboard 3, carries loot 2, tracked empty 1, untracked dflt).

## Verdict per module

| Module | What it does in Arcade | Online gate today | Host-only run safe? | Clients need state? | Value | Verdict |
|---|---|---|---|---|---|---|
| klhop | Carries bots over a level's [CrewHop] places (teleport 0x62a900 via klt_teleport, optional re-order 0x760e50) so they pass walls/ledges nav cannot | klb_read false, klb_level gate | Yes: same game call the online board teleport already uses; no map has hops unless KLJoin.ini lists them, a stock map has none | No: position is synced as the actor | HIGH on Dead Men maps (bots stuck at climbs) | BUILT: `[CrewHop] Online=0/1/2`, `OnlineStage` |
| klcardown | A car blast floors AI (and the human) into the revivable down instead of dying (caps blast damage, inner radius 0, soldier slot 51 down call) | klr_arcade false | Yes for AI: acts on host actors with the game's own down; the actor state syncs via the puppet (GUESS how the down anim shows) | Down state through the actor sync (GUESS) | MEDIUM (cars blow on many maps; cops and bots no longer die by blast) | BUILT: `[CarDown] Online=0/1/2`, no human part online |
| klcdying (Bots NoFire) | Downed heisters hold fire | applies online already through the global klbd.nofire | n/a | n/a | n/a | NOTHING TO DO (already online). Its Human part (local drop into down) is unproven online: not built |
| klcrew / klcrew_rt | Random look, voice, name per crew record | needs crew records ("vtable ..., not ZGameRulesHeist") | A host-only look is invisible to clients (model is per-peer data) | Yes (model id per bot), no carrier exists | MEDIUM | NOT BUILT: records absent and no replication path; see bots_online_arcade_1028.md G-D |
| klgrudge | Backstab / traitor: writes rules records, uses ZBecomeTraitorTactic 0x79b7c0 (Arcade brain only) | klr_arcade false | No: needs record writes and a tactic object that online bots lack | n/a | LOW online (a traitor needs the pop-up and money rules) | NOT BUILT: blocker CERTAIN |
| klshield | Shield / health trickle for the local player | klr_arcade false | No: writes the local player's health object; online that is the host's player only | Health is server-side online | LOW | NOT BUILT |
| klbotdown | Down / adrenaline / revive | host path exists ([Down] OnlineBotDown) | Already online | already | | existing |
| klescort / klcopsquad / klfedkit / klbot traits | Escort follow, C&R squads, kits, crew traits | klr_arcade false | Need crew records | Some | MEDIUM-LOW | NOT BUILT (G-E / G-F of bots_online_arcade_1028.md) |

## New keys (KLHook.ini, all default 0 = off)
- `[CrewHop] Online=0|1|2` (0 off, 1 on, 2 dry log) and `OnlineStage=2` (stage assumed for a bot the puppeteer does not track). Works with `Enable=0` (the Arcade part stays off).
- `[CarDown] Online=0|1|2`. `Bots`, `Cops`, `Damage`, `Inner`, `Seconds`, `Radius`, `Log`, `Dry` apply as in Arcade; `Human` is forced off online.
Both are host only; a client never runs them. Logs: `hop: ONLINE ...`, `cardown: ONLINE ...` once per round plus the usual per-event lines (rate-limited by the existing rules).
Game calls are the existing ones (klt_teleport, KLBD_CALL), already under __try / guarded. No .text patch (KLH_SHIP).

## GUESS list
1. The pseudo-record census equals the Arcade crew: a cop or a non-heister Ally would be treated as a bot (the census keeps team Ally with a ZSoldier only).
2. Stage mapping from the puppeteer (aboard = 3, loot = 2); with OnlineTactics off every bot counts as OnlineStage (default 2), so a hop with Stage <= 2 fires for all bots.
3. A teleported actor and a downed actor replicate to clients through the existing actor sync with no extra packet (teleport is already used by OnlineBoardTeleport; not yet seen live).
4. The car blast fields (+0xbe8/+0xbec/+0xbf4) are the same GUESSes klcardown already makes in Arcade; online the blast runs on the host (explosion authority = host, GUESS).
5. Down on a cop through slot 51 works (unproven in Arcade too).

## Bench recipe (2 seats; only when the game is free)
Base inis: `C:\kl_build_1024\week_1028\WK2_host.ini` and `WK2_join.ini` (copy to new names; change the map step if wanted). Add to BOTH:
```
[CrewHop]
Online=2          ; dry first, then 1
Log=2
[CarDown]
Online=2          ; dry first, then 1
Log=2
[BotFill]
OnlineTactics=1   ; so the heist stage is known
```
A map with a [CrewHop] section in its KLJoin.ini (a Dead Men graft map) is needed for the hop part; a stock map only tests cardown. Run with the `_test` dll (out_arcmods_1028_test):
`python tools/kl_solo_test.py --hook <dll dir> --n 2 --secs 700 --gap 45 --relaunch 2 --tag AM_<MAP> --owner-away --ini1 <host ini> --ini2 <join ini>`
Proof lines (solo/AM_*/inst1/KLHook.log): `hop: ONLINE host round`, then `hop: bot N is at From of hop`, `carried` (live) or `Dry`; `cardown: ONLINE host round`, `car N BLEW`, `the game's down said YES (down byte 1)`.
Client log must show the bot standing at the landing place / lying down (census equal, `sync: vs host ... 0 farther than Tol`). FAIL: any fault or dump, a bot teleported and then back on the old spot on the client, a downed bot that never rises.
Compare against a run with both keys 0.
