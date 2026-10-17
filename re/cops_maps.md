# Retomoto police pattern on the owner-built maps (cops_1018)

2026-10-18, kl-merge-e5 (offline; nothing run in the game, nothing installed, nothing committed).

## What it is
GUESS: "Retomoto cop settings" = the squad AI pattern (kl_arms soldier rows, SWAT rifles, wiped-out chains), not
ZOnlineFragileAllianceSettings (340 fields, numerics identical on all maps except 324/326 = 11/20 on DM09 and the newer
maps, 8/8 on the old four; meaning unknown, nothing to copy).

## The flag
`python tools/kl_map_ai.py cops-style <finished build folder> <out folder>` (function `kl_map_ai.cops_style`):
`apply(parts=('strength','chains'), auto=True)`. Same as `retomoto-style` WITHOUT `spawnfix --auto` and without the waves
part, so timers, waves, who is in the world and the posts stay as built. Refuses out == src and a non-empty out folder.
Only the .prp member changes (verified member by member; every file beside the zip is byte-identical; map_ai.json/txt added).
Default output of apply / retomoto-style / everything else is unchanged (new function + new CLI branch only).

## Outputs (<work>/build/cops_1018/<map>; base C:/kl_build_1018/fed_e5/<map>)
| map | slot | zip md5 | strength | chains | auto plan |
|---|---|---|---|---|---|
| DM03A Vault | F07 | 9489aacca75ca15904c233146e7d67ae | 76 soldiers (smg 28, rifle 43, shotgun 5) | 4 | 0 SWAT rifles, 0 unleash |
| DM05A Last Call | F01 | b387d81261c320302fd28a1aed6b5625 | 36 (smg 20, rifle 11, shotgun 5) | 0 | 1 unleash (not applied: waves part off) |
| DM11B Hasta | F04 | e943c3872c827ec279baa4a2eff8f2d1 | 33 (mg 3, rifle 27, smg 3) | 5 | 0 |

Checks: debug/check_passes.py PASS (A, B, C1-C3) on all three (Vault: the known Shards_Group_A WARN only);
apply's own gates passed (J.check 0 misfits, lists 0 dangling / 0 order-rule faults, kl_arms.check); `kl_map_ai check`
before/after: soldiers, civilians, squads, timers, "in the world at load" (0 / 16 / 0) unchanged.
kl_fa_bank waves-check / garrison-check could not run: they need extras.json / bots.json of the bank build folder, which the
flat fed_e5 folders lack. NOT RUN.

## Things to look at before installing (GUESS)
- Difficulty: the rifle floor is eElite-as-used (accuracy 99, health 175). Mean accuracy as used: Vault 66.5 -> 79.2,
  Last Call 57.8 -> 70.2, Hasta 73.3 -> 92.6. Retomoto's rifle men read 82 / 55. Hasta in particular may be too sharp.
- Chains only reach ungated squads (autoplan skips Wave/Reinforcement/Garrison/Gate/Staged/COOP/Escort). Vault chain 1
  (PatrolGuards_01a wiped out -> 4_Vault_Part Guards_01 Defend) could wake the vault guards before the door beat.
  Hasta chains run Capitolio square -> LastRoomFight (Flanking) and could pre-empt its three-stage layer. Last Call: none.
  If either misbehaves, rebuild with the chain dropped (call apply with parts=('strength',)).
- Not done: spawnfix (staged maps are LATER by design), unleash (waves part), Last Call ARRIVE squads untouched.

## kl-merge-3f's maps: what would change (nothing written)
- DM01B Hot Coffee II (F03, 27 squads, 0 chains, all LATER): `cops-style` = strength + chains only; no spawnfix.
- DM06B (F02, 11 squads, 1 chain): same; plus `kl_fa_fedpoints report` then `fix` (first two AFTER_DEATH points BAD / DOUBTFUL).
- Settings fields 324 / 326: copy nothing; whether the old DM01/02/03/06 (8/8) should be 11/20 is unresolved.

2026-10-18 (kl-merge-e5): HELD as owner-choice tests, not handed to kl-merge-3f. Accuracy rises a lot (Hasta mean 73 -> 93), and the Vault and Hasta chains may wake guards early. The cops_1018 folders come from fed_e5, which lacks the KLJoin.ini kl-merge-3f made at install. Before any handover, run kl_fa_fedbody (the .prm is unchanged, so the installed KLJoin.ini fits) and the post-pass checklist.
