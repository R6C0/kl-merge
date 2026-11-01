# Arcade bot baseline (ARC1, 2026-11-01)

The reference for 'online = Arcade': one offline seat, round 1, ArcadeProbe on, ship1103 hook, 7 AI heisters. Numbers are the game's own crew records, not a hook tally. Kit: C:\kl_build_1024\week_1028\arc1 (tools/kl_arcade_baseline.py). Online bot benches should land near these per map (stacks taken, $ carried, van call time, aboard).

| Map | Bots | Armed stacks | Stacks taken | $ carried | Van call s (why) | Aboard / bots | Far-counted | Dead | Stack never emptied | Get-up down / sent / up s | Trigger FIREs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DD01 | 7 | 0 (+58 behind shut door) | 58 | 7.46M | 204 (clock left 166) | 1 / 7 | - | 6 | 0 | - | - |
| DD02 | 7 | 24 | 10 | 3.71M | 122 (clock left 248) | 6 / 7 | - | 1 | 14 | - | - |
| DD03 | 7 | 12 | 4 | 2.66M | 181 (clock left 189) | 3 / 7 | - | 6 | 8 | - | - |
| DD04 | 7 | 10 | 7 | 3.18M | 184 (clock left 186) | 2 / 7 | - | 5 | 3 | - | - |
| DD05 | 7 | 6 | 6 | 4.50M | 181 (clock left 189) | 5 / 7 | - | 1 | 0 | - | - |
| DD06 | 7 | 8 | 8 | 5.55M | 186 (clock left 183) | 5 / 7 | - | 1 | 0 | - | - |
| DD07 | 7 | 5 | 5 | 3.95M | 238 (clock left 132) | 1 / 7 | - | 6 | 0 | - | - |
| DD08 | 7 | 47 | 30 | 4.84M | 198 (clock left 172) | 1 / 7 | - | 6 | 17 | - | - |
| DD09 | 7 | 6 | 6 | 4.40M | 358 (clock left 12) | 0 / 7 | - | 6 | 0 | - | - |
| DM01 | 7 | 5 (+1 behind shut door) | 5 | 5.46M | 107 (clock left 262) | 6 / 7 | - | 1 | 1 | - | - |
| DM06 | 7 | 4 | 4 | 0.65M | 122 (clock left 248) | 6 / 7 | - | 1 | 0 | - | - |

Arcade baseline, round 1, offline one seat, game record fields (not a hook tally). Aboard = crew records with status 4 (ABOARD); $ carried = sum of each AI record's highest money field; Stacks never emptied = followed armed stacks still not at 0 at the round end.
RESULT: OK (11 of 11 map(s) with an ArcadeProbe round)

Reading: DD01's 58 stacks were all behind a shut door at the first scan and all 58 were still taken (7.46M); DD09 calls the van with 12 s left and nobody is aboard; DM06 carries only 0.65M (4 stacks). 6 of 7 bots die on DD01/DD03/DD07/DD08/DD09, so aboard counts are low there.
