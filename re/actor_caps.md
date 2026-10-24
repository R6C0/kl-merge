# Actor, squad and AI caps in kl2.exe (2026-10-24)

Question (owner: "40 people bruh theres two floors"): how many actors, squads and AI can a Last Call level hold?
Method: static reading of kl2.exe (32-bit, base 0x400000) with `debug/kl.py` and capstone, plus stock-map and live evidence.
Nothing was launched or installed. Tags: MEASURED (counted from files or a live run), READ (seen in disassembly),
GUESS (inferred), NOT FOUND (searched, no answer).

## Short answer
- No fixed actor, squad, AIMonitor-list or rout array cap was found in the exe. NOT FOUND is not proof of absence.
- Entity slots come from the 128-byte cluster pools in the level's own .gms (READ, loader 0x8ad7c0). Their size is data, not an exe constant.
- Actors (ZFFActor, over 0x900 bytes) are heap objects from operator new 0x89e850 -> 0x4a2fd0. Failure is an `int3` at 0x4a3060 (READ), a crash and not a graceful refusal.
- The heap is a custom arena: VirtualAlloc reserve of MB<<20, committed in 1 MB blocks (0x5048f0, 0x4108c0, READ). The MB source (caller 0x449500) was not traced (NOT FOUND).
- The real ceiling is the 2 GB address space of a non-large-address-aware 32-bit process. The owner crash dump sat at about 1828 MB after load (MEASURED, re/crash_owner_1009.md). It is dominated by textures and the single .prm block, not by actor count (GUESS for the split; the 1828 MB is measured).
- Civilians share the same pool as enemies (READ/GUESS). Our civilians are ZFFActor + ZCivilian + a ZSquadScript squad (re/civilians.md, 8 entities each), so they cost an actor, a squad, an AI brain and anim state exactly like a soldier. A "civilian" is only a different brain script and team (Neutral).
- Cheaper civilian: yes in principle, ZHFlow crowd (no per-person actor or brain). It has never run in a retail level and needs converter work. See below. The existing dance via MiniCutsceneRout civilians is NOT cheaper.

## Evidence
| Item | Value | Tag |
|---|---|---|
| Stock max actors / squads in one map | 148 / 90 | MEASURED (CLAUDE.md, kl_fa_bank) |
| Live-proven (ran in game) | 99 / 55 | MEASURED |
| Live DM05A now (d5f8522b) | 129 / 74, 40 civilians, 3 roof squads | MEASURED file counts, not proven in a run |
| Staged lastcall3 | 145 / 90 | MEASURED file counts, unproven |
| Tool envelope in kl_fa_bank | 147 actors / 500 squads | tool constant, GUESS for meaning |
| Pool chunk bytes | 73,728 | MEASURED (re/civilians.md) |
| Stock max civilians in a map | 60 | MEASURED |
| Players | 8 police player objects per level | MEASURED |
| .LOC buffer | static, 600,000 bytes, no size check | READ (engine_facts.md); a different limit, but a real crash |

## Exe sites READ
| Site | What |
|---|---|
| 0x89e850 / 0x4a2fd0 | operator new; int3 at 0x4a3060 on failure or size over 0x40000000 |
| 0x5048f0 / 0x4108c0 | heap arena init (MB arg) / commit one 1 MB block |
| 0x449500 | caller of the heap init (MB source not traced) |
| 0x6484f0 | allocator singleton init, global [0xdda7a0] |
| 0x8303c0 | ZFFActor ctor (chains to ZActor ctor 0x541150) |
| 0x7ff3e0 | ZAIMonitor ctor (three lists) |
| 0x455c60 | ZSquadScript ctor (15 vector lists) |
| 0x844460 / 0x538230 | ZHFlow ctor / dtor |
| 0xdd2598 | global pool object, vtable 0xbaf79c, 0x5c-byte records at [pool+0x10], used near 0x73bb10; bone/anim-class pool. Capacity not traced (NOT FOUND) |
| 0x86db80 | trivial forwarding thunk, not a registry |
| [0x168e598] | actor manager pointer, runtime-initialised; its array bound not found (NOT FOUND) |

Source files named in the exe strings that matter: ff2\characters\crowds\humanflow.cpp, ff2\levelsetup\aimonitor.cpp,
ff2\scripts\core\scheduler.cpp, ff2\scripts\behaviour\behaviour.cpp, ff2\characters\ffactor.cpp, ff2\characters\squadcontrol.cpp,
ff2\levelsetup\actormonitor.cpp.

## Not found (open, do not assume safe or unsafe)
- Scheduler task pool size (scheduler.cpp) and per-frame AI update budget.
- PF4 pathfinder agent cap. Each live AI on the navigation mesh may cost path queries; frame cost, not a hard stop (GUESS).
- Animation or skeleton instance pool capacity at 0xdd2598 (the likeliest fixed-size pool a crowd of animated people would hit).
- Quazal net actor limit. The net layer declares DDL_ZFFActor as a replicated object with per-actor position, angle and state datasets (re/netcode.md). In online play every AI actor is a replicated DO, so the cap is lower online than solo (GUESS; not measured). Private solo is the less constrained case.
- Heap arena size in MB.

## Cheaper civilian options
1. ZHFlow crowd (humanflow.cpp, ZHFlow ctor 0x844460, ZStateDanceM05 still registered, READ). Dead Men's M05 club used it for about 1,980 members (re/campaign_fa_club.md 1.5, re/club_campaign.md V.6). No per-person actor, brain or squad. No Dog Days stock level uses it. Blockers: three converter gaps, and the dance clips live in an undecoded database (re/campaign_fa_club.md). Capacity bounds of the DD ZHFlow tables not checked (NOT FOUND). Highest payoff, highest risk; research-grade, not a quick job.
2. Strip the civilians: drop the per-civilian squad and rout by sharing one squad among many actors. GUESS: it saves 1 squad and about 3 entities per person but keeps the actor and brain, so it does not remove the actor cap. Not tried.
3. Prop mannequins: static animated geometry (no ZFFActor). GUESS: a ZGEOM with a looping pose would add no AI cost, but nothing in this repo has animated one and the DD ANM header differs from DM (never copy .ANM). Visual filler only, not shootable people.

## Safe ceiling for Last Call
- Stay at or below the stock map max: 148 actors / 90 squads. The staged lastcall3 (145 / 90) sits at that edge and is unproven in a run.
- The live-proven number is 99 / 55; the current live 129 / 74 is within stock but unplayed at that count.
- Raise the count in steps, with a live test between steps: 129 -> 145. Past 148 actors or 90 squads is untested territory; the likely failure is memory (arena or 2 GB) or an unfound pool, which shows as an int3.
- Because civilians use the same machinery, 40 civilians cost the same as 40 soldiers. A two-floor club with hundreds of people is not reachable with actor civilians (MEASURED budget: stock max civilians 60). Hundreds of dancers needs the ZHFlow path (option 1).
- Offset: cut enemy squads and AfterLoot squads to buy civilian headroom (lastcall2 did this: 99/53).
- Online adds the net-actor cost (GUESS); keep the online ceiling lower than solo until measured.

## To close the gaps (next steps, no game needed)
Find the callee of the actor registry at vtable +0x3c of the object at 0xdd2598, look for `cmp reg,imm` followed by int3 on counts, trace 0x449500 for the arena MB, and read the HFlow member table bounds in 0x844460.
