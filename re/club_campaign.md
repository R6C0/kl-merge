# The club (Dead Men M05_A 'The Mizuki') as a Fragile Alliance map - build notes

Map 2 of the campaign places (map 1: re/bank_campaign.md, the worked example of every step). The study:
re/campaign_fa_club.md (its section 8 and the notes 'corrected after the critic' weigh more than the first text),
re/campaign_fa.md 4.2 and G1.3 / G1.8, re/campaign_fa_tooling.md 11 - 12. Each stage appends a section here.
`<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`.

## Stage T - the converter case (tools/kl_mat.py: TEXT/TILU = MIRRORED)

STATE: DONE (2026-10-11 19:45). All checks pass; no archive is left (the builds ran without `--keep`). Kept in
C:/kl_scratch/club/t/ (0.2 MB): s/ (baseline.py, mirror.py, results.py), out/ (before.json, after.json, mirror.txt,
check.txt, bare.log, nobounds.log, results_*.txt) and result.json / log.txt / graft.txt of the two builds.
Offline only; nothing run in the game.

### T.0 Baseline, made BEFORE the edit (tree at 26ea22d, tools/kl_mat.py sha1 fa8db3da)

`python C:/kl_scratch/club/t/s/baseline.py C:/kl_scratch/club/t/out/before.json`: for ALL 20 Dead Men levels (not only
the seven that are built today) the sha1 of the converted .MAT, twice - 'plain' = `kl_mat.convert_mat_full(data)` with
every default, 'build' = `kl_dmassets.convert_level(level)` (the path a graft takes: the converted .prm and the .TEX's
ids handed in) - plus a hash of the converter's report. MEASURED: 18 levels convert, two are refused:
M05_A (`material 538 ... TEXT/TILU value b'MIRRORED' never occurs in Dog Days`) and M01_A (material 615, the same).
The 'build' hashes of the seven named levels: M01_FA_A 4acc31b5, M02_FA_A 0250c1f1, M03_FA_A 69052ef3, M06_FA_A
ef95b22e, M03_A 5890e380, M09_A 98d3e153, M09_B 988021ef (whole values in before.json).

### T.1 What was changed (one file, tools/kl_mat.py, +19 lines)

- NEW table `STRING_MAP = {('TEXT', 'TILU', b'MIRRORED'): b'TILED'}` beside CLASS_MAP, with the comment that says
  what Dog Days has instead and what the look difference is.
- In `convert_mat_full`'s string guard (was line 396-397): a value Dog Days never has on that (node, key) is looked
  up in STRING_MAP first; a hit whose target Dog Days does have is written (node count = length + 1, value) and
  counted in the report's NEW key `strings` {('slot node/key', old, new): n}; everything else raises as before.
  The table is consulted ONLY where the old code raised, so a level that converted before cannot change.
- Docstring: the report key, and point 2's 'every string value is the same in both games' gains 'but for
  STRING_MAP's one case'.
- NOT done, on purpose: the study's other proposal (accept MIRRORED on U because Dog Days has it on V). READ
  re/campaign_fa_club.md 8 'Not corrected, but weaker than it reads': how kl2.exe turns the value's name into an
  addressing mode was not found ('MIRR' is nowhere in the exe), so MIRRORED on U stays ASSUMED; TILED is the one
  value certain to be read there (27,965 stock bindings).

THE LOOK DIFFERENCE (MEASURED `python C:/kl_scratch/club/t/s/mirror.py M05_A M01_A` -> out/mirror.txt): the picture
repeats along U where Dead Men flipped every second repeat. Carried by
- M05_A slot 538 `Locations/M05/Concrete/Concrete_Walkway_01a_M05` (class Standard/Standard, 5 uses in the .prm): three
  stages - mapDiffuse (texture 941 `Locations/M05/Concrete/Concrete_Walkway_01_M05`), mapNormal (184
  `Locations/M05/Plaster/Plaster_Basic_01_M05`), mapSpecularMask (no texture). TILV is TILED on all three already.
  ONE material of the club: a concrete walkway surface. Where its five meshes stand was NOT looked up; if a seam
  shows on a walkway's concrete in the game, this is the cause.
- M01_A slot 615 `Vechicles/Civil_USA_01/V_Civ_USA_01_02` (2 uses): mapDiffuse only. Not this job's level; it now
  converts too.
No other Dead Men level has the value.

### T.2 Checks

1. **The baselines are byte-identical - PASS.** `python C:/kl_scratch/club/t/s/baseline.py .../out/after.json`, then
   the comparison of the two files: 'identical levels: 18 of 20' - for each of the 18 the 'plain' hash, the 'build'
   hash, both sizes AND the report's hash (without the new, empty `strings` key) are the same; the two that differ
   are the two that were refused: M05_A now 527,600 bytes (build e7efc9cd, `strings` {'538 TEXT/TILU -> MIRRORED ->
   TILED': 3}), M01_A 763,872 bytes (build 40e5e693, {'615 ...': 1}). So the bank (M03_A), Retomoto (M09_A / M09_B)
   and the four Fragile Alliance maps get the same .MAT as before; no rebuild of any of them was made or is needed.
2. **The written file reads back - PASS** (out/check.txt): M05_A `kl_mat.check` (690, 9), `kl_dmassets.cross_check`
   []; slot 538's three stages read TILU (6, b'TILED'); M01_A (1014, 9), [] and slot 615 the same.
3. **The stock command builds, with the study's numbers - PASS.**
   `python tools/kl_maps.py one "C:/kl_scratch/club/t/bare" F07 M05_A --campaign` (34 s; exit code 1 because verify's
   problems are not 0, as for every level without a layer) -> 'verify: problems: 11', 'built ... F01_Main.zip, 284
   MB, 30 members'. result.json: entities **26,106**, rooms 20, textures 1,676, materials 1,135, prm_chunks 52,934
   (= **52,935** chunk-table entries), dangling [], tops 395, ref_slots 36,987, archive 284.4 MB; problems **11** =
   1 sound ('5 stream clips are not in the merged stream file') + 1 CRASH (no OnlineFragileAllianceSettings) + 9
   BROKEN (define, exit trigger, START / AFTER_DEATH points, three gameplay triggers, loot, squads).
   `python s/results.py <mine> "<work>/build/cfa/club/patched/F07+M05_A campaign" ".../sk_patched/..."`: **0 of 34
   keys differ** from the first agent's and from the second agent's build made with the outside wrapper (every key
   of result.json but 'seconds').
4. **The variant without the campaign's bounds - PASS.**
   `python tools/kl_maps.py one "C:/kl_scratch/club/t/nobounds" F07 M05_A --campaign --m-drop "Boundaries!*"` ->
   'verify: problems: 11'; entities **26,091** (15 fewer), tops 380, ref_slots 36,972, dangling [], the rest as in 3;
   0 of 34 keys differ from `<work>/build/cfa/club/nobounds` and `.../sk_nobounds`.

### T.3 GUESS / ASSUMED

- ASSUMED: TILED on U is drawn as plain repetition in Dog Days (it is what 27,965 stock bindings have; not seen in
  the game for this material). The look difference itself is by definition, not measured on a picture.
- Not established (unchanged from the study): what Dog Days would draw for MIRRORED on U.

### T.4 For the next stages

- The bare build: `python tools/kl_maps.py one <out> F07 M05_A --campaign --m-drop "Boundaries!*"` (add `--keep` to
  read the archive back; the folder inside <out> is 'F07+M05_A campaign' with or without --m-drop, so two variants
  need two <out> folders). 34 s, 284 MB archive.
- No outside wrapper is needed any more: G:/kl_scratch/cfa_club/run_maps.py and the study's `build_open.py` patch of
  `TM.read_mat` give the same bytes as the stock tools now (check 3), but they substitute on TILV too and on every
  node - use the stock command.
- kl_whoref.py and every other tool that converts M05_A through kl_graft.DeadMen now runs on it (they died at the
  same line; not re-run here).
- The report key `strings` is new: `kl_dmassets`'s log line does not print it (that file is another session's).

### T.5 Open

- Whether the walkway material's five meshes are on the round's route (then the tiling is in sight) - not looked up.
- The bank's regression (`kl_fa_bank.py check` on `<work>/build/c_bank/bank_vault`) was NOT re-run: M03_A's converted
  .MAT is byte-identical (check 1) and that tree is not this stage's to touch.
