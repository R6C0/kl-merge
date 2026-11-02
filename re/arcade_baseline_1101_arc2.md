# Arcade bot baseline (ARC2, run 2026-11-02 00:13-01:25)

Second half of the 'online = Arcade' reference (ARC1 = re/arcade_baseline_1101.md): one offline seat, round 1, ArcadeProbe on, TEST hook out_arcbase_test, 7 AI heisters, kit C:\kl_build_1024\week_1028rc2 (tools/kl_arc2_kit.py). 10/10 exit 0. The kit's load check flagged DM01B and DM03A as WRONG MAP: false alarm, its pattern cut the rule name to 4 chars (fixed 3f3948a0e; re-checked, both loaded their own map).
`tools/kl_online_vs_arcade.py --arcade re/arcade_baseline_1101.md --arcade re/arcade_baseline_1101_arc2.md` merges both.

| Map | Bots | Armed stacks | Stacks taken | $ carried | Van call s (why) | Aboard / bots | Far-counted | Dead | Stack never emptied | Get-up down / sent / up s | Trigger FIREs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DM01B | 7 | 12 | 3 | 1.25M | 358 (clock left 12) | 0 / 7 | - | 6 | 9 | - | - |
| DM02 | 7 | 41 (+8 behind shut door) | 39 | 3.76M | 194 (clock left 175) | 4 / 7 | - | 3 | 10 | - | - |
| DM03 | 7 | 14 | 11 | 7.36M | 105 (clock left 265) | 6 / 7 | - | 1 | 3 | - | - |
| DM03A | 7 | 13 | 7 | 8.10M | 242 (clock left 128) | 4 / 7 | - | 3 | 6 | - | - |
| DM05A | 7 | 11 | 7 | 1.91M | 346 (clock left 24) | 2 / 7 | - | 3 | 4 | - | - |
| DM06B | 7 | 15 | 6 | 1.84M | 82 (clock left 287) | 7 / 7 | - | 0 | 9 | - | - |
| DM07 | 7 | 11 | 8 | 2.42M | 126 (clock left 244) | 6 / 7 | - | 1 | 3 | - | - |
| DM09 | 7 | 21 | 11 | 5.61M | 300 (clock left 70) | 0 / 7 | - | 6 | 10 | - | - |
| DM11B | 7 | 16 | 16 | 5.00M | 200 (clock left 170) | 6 / 7 | - | 1 | 0 | - | - |
| DD10 | 7 | 8 | 8 | 5.60M | 358 (clock left 12) | 1 / 7 | - | 2 | 0 | - | - |

Arcade baseline, round 1, offline one seat, game record fields (not a hook tally). Aboard = crew records with status 4 (ABOARD); $ carried = sum of each AI record's highest money field; Stacks never emptied = followed armed stacks still not at 0 at the round end.
RESULT: OK (10 of 10 map(s) with an ArcadeProbe round)

Reading: Arcade itself boards 0 / 7 on DM09 (van called at 300 s with 70 s left, 6 dead) and on DM01B (van at 358 s, 12 s left); DD10 1 / 7 (also 12 s left). So the online DM09 target is loot (11 stacks, 5.61M), not a full van: RT4 counts as parity if bots carry and some board, a 0-boarded DM09 is also what Arcade does. DM11B is the only map where every armed stack is emptied; DM02 has 8 stacks behind a shut door at the first scan and still takes 39 of 41. Late van calls (DM01B, DM05A, DM09, DD10, like DD09 in ARC1) are where aboard is low.

## Online (Q31 host tally, round 1) vs Arcade, all 21 maps

| Map | Loot Arcade | Loot Online | Ratio | Stacks Arcade | Stacks Online | Boarded Arcade | Boarded Online (hook tally, not like for like) | Van s Arcade | Van s Online | Delta stacks / boarded / van s | Gaps | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DD01 | 7.46M | 0 | 0% | 58 | 0 | 1 | 0 | 204 | 249 | -58 / -1 / +45 | STACKS VAN | BELOW |
| DD02 | 3.71M | 3.54M | 95% | 10 | 14 | 6 | 6 | 122 | 248 | +4 / +0 / +126 | VAN | PASS |
| DD03 | 2.66M | 4.20M | 158% | 4 | 7 | 3 | 7 | 181 | 189 | +3 / +4 / +8 | - | PASS |
| DD04 | 3.18M | 3.50M | 110% | 7 | 8 | 2 | 7 | 184 | 188 | +1 / +5 / +4 | - | PASS |
| DD05 | 4.50M | 0 | 0% | 6 | 0 | 5 | 7 | 181 | 167 | -6 / +2 / -14 | STACKS | BELOW |
| DD06 | 5.55M | 3.13M | 56% | 8 | 2 | 5 | 6 | 186 | 186 | -6 / +1 / +0 | STACKS | BELOW |
| DD07 | 3.95M | 0 | 0% | 5 | 0 | 1 | 2 | 238 | 201 | -5 / +1 / -37 | STACKS | BELOW |
| DD08 | 4.84M | 0.70M | 15% | 30 | 14 | 1 | 2 | 198 | 210 | -16 / +1 / +12 | STACKS | BELOW |
| DD09 | 4.40M | 0.04M | 1% | 6 | 0 | 0 | 7 | 358 | 133 | -6 / +7 / -225 | STACKS | BELOW |
| DD10 | 5.60M | 1.15M | 21% | 8 | 2 | 1 | 4 | 358 | 188 | -6 / +3 / -170 | STACKS | BELOW |
| DM01 | 5.46M | 0.56M | 10% | 5 | 0 | 6 | 5 | 107 | 177 | -5 / -1 / +70 | STACKS VAN | BELOW |
| DM01B | 1.25M | 0.99M | 79% | 3 | 5 | 0 | 4 | 358 | 221 | +2 / +4 / -137 | - | PASS |
| DM02 | 3.76M | 1.42M | 38% | 39 | 12 | 4 | 5 | 194 | 200 | -27 / +1 / +6 | STACKS | BELOW |
| DM03 | 7.36M | 4.70M | 64% | 11 | 9 | 6 | 7 | 105 | 128 | -2 / +1 / +23 | - | PASS |
| DM03A | 8.10M | 1.20M | 15% | 7 | 6 | 4 | 6 | 242 | 173 | -1 / +2 / -69 | - | BELOW |
| DM05A | 1.91M | 1.65M | 86% | 7 | 5 | 2 | 5 | 346 | 207 | -2 / +3 / -139 | - | PASS |
| DM06 | 0.65M | 0 | 0% | 4 | 0 | 6 | 7 | 122 | 140 | -4 / +1 / +18 | STACKS | BELOW |
| DM06B | 1.84M | 2.98M | 162% | 6 | 12 | 7 | 6 | 82 | 181 | +6 / -1 / +99 | VAN | PASS |
| DM07 | 2.42M | 2.38M | 98% | 8 | 8 | 6 | 6 | 126 | 71 | +0 / +0 / -55 | - | PASS |
| DM09 | 5.61M | 5.08M | 90% | 11 | 14 | 0 | 0 | 300 | 248 | +3 / +0 / -52 | - | PASS |
| DM11B | 5.00M | 3.00M | 60% | 16 | 8 | 6 | 7 | 200 | 191 | -8 / +1 / -9 | STACKS | BELOW |

RESULT: 9 PASS, 12 BELOW (60 pct loot = judgement call). Zero stacks online: DD01 DD05 DD07 DD09 DM01 DM06 (Arcade 5-58). The Q31 tally predates OnlineStackRecheck and the wk-vantime keys.
