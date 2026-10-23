# Balance pass 2026-10-23 ("the AI is a bit too OP")

Decision (lead): enemies / police hit the human too hard, and the AI crew is too tanky.

## 1. KLHook.ini values (patch file `C:\kl_build_1019\balance_1023\KLHook.balance.patch.ini`)
| key | live before | patch |
|---|---|---|
| [Balance] PointBlankToYou | unset (100 = game's) | 6.0 |
| [Balance] CopToYou | 1.3 | 0.9 |
| [Balance] PlayerHealth | 0.75 (412) | 0.9 (495) |
| [Bots] CrewHealth | 1.5 (378) | 1.25 (315) |
| [BotDown] FreeSeconds | 15 | 10 |

Applied by `tools/kl_ini_patch.py <ini> <patch> [--dry-run] [-o out] [--backup=SUF]` (keeps comments, order, CRLF;
replaces the first occurrence of a key in its section; appends a missing key before the comment/blank block that
precedes the next section).

## 2. Code reading (klhook/klbalance.c, klbot.c, klsteam.c) - no C change needed
- `PointBlankToYou=6.0` parses as written: line ~1322 reads it with GetPrivateProfileString, `klr_number` accepts one
  number with a decimal point, 0..100 (100 = game's own, negative = leave alone). 6.0 sets `klr_pb.want[0]`, which
  replaces the 100.0 hit scale of a guard's point-blank step when the target is the ZFFPlayer (klr_pb_step). Also goes
  through `kld_pb()` when [Down] DownPointBlank applies. Needs `[KLHook] Tick=1` (default).
- Stock maps: every [Balance] part asks `klb_level()` (klbot.c) -> `klx_level_verdict()` (klsteam.c). With
  `[KLHook] AllMaps=1` and an Arcade session (`klx_arcade_now`) a STOCK level answers 2 = "modded for the parts,
  blocked for Steam". The live ini has AllMaps=1, so [Balance]/[Bots]/[BotDown] already act on the 9 stock FA maps in
  offline Arcade. Steam writes stay blocked by the same verdict (klx_ship_blocked). Online sessions always get the raw
  verdict (stock = no balance). So nothing was added.

## 3. Pistol guards (tools/kl_map_ai.py `pistol-row` / `--pistol-row`, `pistol_row()`, `pistol_zip()`)
Pistol / revolver carriers are LOWERED to the stock guard row: accuracy as used 55 (stored 50.0 x1.1 for
No_Mercenary), aim 50, skill eCustom (preset numbers of the old name kept for the other fields). Health, riflemen,
SMG, shotgun men and AI heisters untouched. Only the `.prp` member of the installed zip is rebuilt; per-member CRC is
compared and the run refuses if anything else differs.

Accuracy as used, installed maps (python tools/kl_map_ai.py table <zip> --short), before -> after:
- DM01 (F01): 3 pistols 75 -> 55 (BossFlank_01/02 guards, The_Senator); map mean 75.0 -> 73.5
- DM02 (F02): 2 pistols 75 -> 55 (2nd/3rd floor guards); mean 75.0 -> 74.0
- DM03 (F03): 3 pistols 100 -> 55 (bank guards); mean 100.0 -> 91.0. NOTE the 9 riflemen / 2 SMG / 1 shotgun on DM03 are
  still at 100 (riflemen unchanged by order); that map is the sharpest by far.
- DM06 (F04): NO pistol carriers (SMG 66..75, rifle 75, shotgun 66): nothing to change, no zip built.
Aim before/after for the changed men: pistol carriers aim 50 (checked by reading the ZSoldier row of the new zips).

Checks run: `debug/check_passes.py` PASS on all 3 (A, B, C1-C3), `debug/check.py` 0 mismatching layouts,
`tools/verify_levels.py` problems: 0 for M01/M02/M03/M06 (it converts the Dead Men sources, it does not read these zips).

Untested in the game. Install/undo: `C:\kl_build_1019\balance_1023\INSTALL balance 1023.bat` / `UNDO balance 1023.bat`.
