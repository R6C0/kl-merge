# SR1 "0 stacks taken" on DD09 / DD05 / DM06 (2026-11-02, offline, wf_3e7aa863-85d diagnose + refute: CONFIRMED)

- Not a hook bug. The stock actor-death script 0x6d2500 -> 0x4988f0 empties type-0 stacks into type-1 drops. On DD09 (SR1A) every
  stack reads `amt 0 state 3 armed 0` at +13..+15 s (loot bar 6.0M -> 0 between 02:19:04 and :11.3) while bots held 80k.
  ARC1_DD09 (Arcade, no hook) has the same first death at the same coordinates (-14531.8, 410, 22679.6) at +8 s: deterministic.
- State 3 = gone (re/bots_loot.md: +0x64 0 new, 1 active, 2 appearing, 3 gone). Exact store not located (GUESS: 0x4c95d0 / 0x4e3f40 tail).
- DM09 (RT4B) took 13 because it has 21 small stacks at 0.2 s/part; DD09/DD05 have 6 huge ones at 0.5 s/part (22-30 s per take).
- SR1 inis had no OnlineDropFollow / OnlineDropTake / OnlineGuardCarrierCm, so nothing followed the drops -> idle van, empty bots.
- Metric mismatch: Arcade's "stacks taken" (ARC1/ARC2) is the game's drain-step count; ours counts GRABBED lines. Compare money carried.
  Arcade AI money on DD09: 3.4M by +60 s, 4.35M later.
- Secondary bug: OnlineStackRecheck=1 drops stacks that are `state 0, hidden 1` at round start (not yet appeared; SR1D 3 -> 6 armed 3 s later).

Next: SR2 bench (DD09/DD05/DM06, DropFollow=1 + GuardMode=1 + GuardCarrierCm=150; one row adds DropTake=1); a per-round money summary
line; a default-0 key so the recheck ignores hidden stacks early in the round. Do not race the drain, do not touch 0x6d2500.
