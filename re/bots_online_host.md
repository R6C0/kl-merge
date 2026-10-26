# [BotFill] OnlineHost (2026-10-26; built, NOT run live)
Stock online: every peer loads the level and holds its own copy of the 7 Ally actors (census 7 Ally, 0 tactics, L9b). The squad filter 0x7b37d1 disables them (mask 8 lacks bit 1);
klbotfill.c spawned nothing before (read-only; OnlineFillSquads is dead: squads are collected at load). With the data route (tools/kl_botsonline.py) they are kept; as ZSoldier/ZFFActor
the client brain is gated off and DDL_ZFFActor replication (GUESS: no team test) moves them.
Design: OnlineHost=1 -> host forces [Sync] Share (KLSY2, UDP 27415, role 2 only); client Puppet (klsync.c ksp) also steers team-2 actors (ksp.bots) toward the host place; cops only with Puppet=1.
Activation is NOT done by the hook (SHIP = data/vtable only): the level zip must keep the squads. Proof lines: 'botfill: OnlineHost=1', 'botfill: OnlineHost HOST/CLIENT ...',
'sync: puppet: slot N c=ZFFActor t=2 START/CONVERGED/SNAP'. No mod-options row (menu table est. 4994 of 5000).
