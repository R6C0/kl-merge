# Putting the new HUD on the owner's game (2026-10-12)

Written offline while the owner plays: nothing here has been done to the game folder. Steps are for the game holder, game closed.
`<DD>` = `C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days`, `<work>` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools`.

## 1. What is installed now (read 2026-10-12 ~14:00)

Hook `<DD>\dinput8.dll` = SHA1 4810159a... = `<work>\build\klhook\ship_w12` (766,976 bytes; has no tags / rappel parts). `<DD>\KLHook.ini` has
`[HUD] Enable=0 Log=1 Reuse=0 PicTest=1`. Maps `<DD>\KLExpansion\Maps\<id>\` (the tree is `<work>\build\w_tabC7`, every installed archive is
byte-identical to its copy there, so w_tabC7 is also the backup of the pre-bake state):

| id | slot | installed archive | sha1 | built from (under `<work>\build`) |
|----|------|-------------------|------|-----------------------------------|
| DM03 | F03 | F03_Main.zip 200,824,762 | e92d2d7d | y_climb\slotted_e (identical zip; y_climb\DM03_e is the same content under the F01 name) |
| DM09 | F06 | F06_Main.zip 218,983,203 | 92f0f0fa | y_rappel\DM09r2 (same members after the slot rename) |
| DM01 | F01 | F01_Main.zip 205,874,199 | ba5bd473 | r_tab\DM01 (identical zip) |
| DM02 | F02 | F02_Main.zip 186,773,509 | 15e8e29d | r_tab\DM02 (same members after the slot rename) |
| DM06 | F04 | F04_Main.zip 181,690,778 | bfa01ac7 | r_tab\DM06 (same members after the slot rename) |
| DM03A | F07 | F07_Main.zip 207,944,981 | 966a997e | q_vault\DM03A_v2 (same members after the slot rename) |
| DM05A | F01 | F01_Main.zip 179,128,107 | 2c4d3b03 | q_club\DM05A_cfx (identical zip) |

(`python tools\kl_hud_tab.py plan --deep` reproduces the table. The game holder's list was right for every map. "Same members after the slot
rename": the installer renames the F0x members of a build to its slot, so the zip bytes differ, the contents do not.)

## 2. What a bake does to an archive that already has an older HUD look

All seven installed archives ALREADY carry an older bake (plate pictures as ABGR, Impact fonts, the first eight extra pictures 3000..3007 in
slots 111..118; no tags, no dials). Measured on DM01 (`kl_hud.py all <src> <out> --look deadmen`):

- bake(installed) twice = once: every zip member byte-identical (idempotent);
- bake(installed older look) = bake(a build from before any HUD step, `build\hud_new\_src\DM01`): font chunks, plate pictures, extra pictures
  and texture count identical (the .prm / .prp / .gms differ there only because `_src` is an older DM01 map, not because of the bake);
- fonts: each ZTTFONT chunk's page 0 and records are rebuilt from scratch with the new face, header / page 1 / kerning tail kept;
- plates: re-made under the same texture ids (`build_pictures`), no "taken" error;
- extras: `add_extras` finds ids 3000.. already named `KLMerge` and re-makes them in place (the older 8 become the new 14: ids 3000..3013,
  slots 111..118, 123..126, 185, 190; "taken" is only raised for a non-KLMerge texture on those ids); the 200-entry HUD lists get the six new ids.
So NO pre-HUD source is needed and `kl_hud.py` needs no change: the installed archives are the source. This also keeps the climb, the rappel
and the club's carfx, because those are in the archives as installed.

## 3. The baked set (made, verified, not installed)

`python tools\kl_hud_tab.py build <work>\build\hud_tab` made all seven (1.7 GB on G:, 3.7 GB left), `verify` PASS:
`<work>\build\hud_tab\<id>\` holds the baked `<slot>_Main.zip` and every other file of the installed folder copied unchanged (.hti .WAV .WHD
.SND the LS_* files, KLJoin / KLGuns / KLWardrobe / KLTalk.ini and DM09's `KLTalk.ini.delays-9.29-0.60`), `manifest.json` has every sha1.
Baked archive sha1 (first 8): DM03 546c2407, DM09 87570664, DM01 6e0fb52b, DM02 372a2ba1, DM06 31ba25fe, DM03A 987e3d13, DM05A eea6cd20.
`verify` shows: member list and order identical; only `.TEX`, `.prp`, `.prm` changed (DM05A: `.TEX`, `.prp`); `kl_hud.check` clean (the font
chunks, their page-0 textures, the HUD picture slots and the extras are all that changed); each zip is about 70 KB smaller (DM05A 21 KB larger).
The bake is unchanged by the v23 fixes (kl_hud.py untouched since 09:09; the hashes above stand; `verify <work>\build\hud_tab` re-run: PASS x7).
Menu scene (round-over board and menus): `<work>\build\hud_menu3\Overlay` = Patch01.zip feeb24bd (92,474) + Scenes\kaneandlynch.zip ff39ccb4
(32,403,674), re-made 2026-10-12 from `hud_menu3\installed_0612` with `kl_hud_menu.py apply ... --fonts`: byte-identical to the stored pair. It is
OPTIONAL and separate: install BOTH files together into `<DD>\KLExpansion\Overlay` (back-out: the two files of `hud_menu3\installed_0612`,
270be320 / a39517e0). Never run in the game (checks M1 / M2 below).

## 4. Steps (game closed, owner not playing)

1. Nothing needs backing up beyond what exists: the pre-bake archives are `<work>\build\w_tabC7\KLExpansion\Maps\<id>\` (hash-identical to
   the installed ones). `KL_PortBackup` is untouched (stock files are not involved). Keep a copy of the ini and the hook:
   `copy <DD>\KLHook.ini <work>\build\klhook\owner_before_hud\` and the same for `dinput8.dll`.
2. For each id: copy `<work>\build\hud_tab\<id>\<slot>_Main.zip` over `<DD>\KLExpansion\Maps\<id>\<slot>_Main.zip`. Only the zip. The side
   files are identical, so nothing else is copied (`verify`, run BEFORE the copy, proved it). After the copy check
   `sha1(<DD>\KLExpansion\Maps\<id>\<slot>_Main.zip) == hud_tab\manifest.json[<id>].files[<slot>_Main.zip].sha1` for each id (do not re-run
   `verify` after the copy: it compares against the installed folder, which is then the new one).
   (The tree's `KLExpansion\manifest.json` and `BuildInfo` are not updated by a copy; nothing at run time reads them, see 6.)
3. Hook: THE FINAL ONE IS `<work>\build\klhook\hud_v23_ship\dinput8.dll` (794,112 bytes, SHA1 a426ed7f28a3a893b554ba5513e48a898764cdf5;
   TEST sibling `hud_v23_test` 843,264 bytes, SHA1 51865f378cb544853b218525264b4e9b7503f15e). Built 2026-10-12 from `git archive HEAD klhook`
   (HEAD d116cc6) + the working tree's klhud*.c in G:\kl_scratch\hud_v23. v23 = v22 with the review's fixes: the outline copies now carry the
   initials' text (v22 drew them empty: the MUST), the tab position is zeroed before each draw, Log=2 lines read back the outline colour and
   the peak draw instances. v22 (a46e2404) is SUPERSEDED, do not use it. v21 (`hud_v21_ship`, SHA1 3e90ef58) is the one the twelve live runs
   used: it is the safe fallback (no outline, one shadow). v23 has NOT RUN: first run A1 (below) with the TEST sibling; install the SHIP one
   only after A1 (or accept the risk: the change since v21 is only the tags' extra text objects and the pop-up lift / label clamp).
   It has everything `ship_w12` has plus tags and rappel. Copy over `<DD>\dinput8.dll`.
   The hook's Cap defaults (11 15 10 10) equal what the bake prints, so no Cap keys are needed.
4. `<DD>\KLHook.ini`, section `[HUD]` (it is the owner's own, outside the expansion block): set
   ```
   [HUD]
   Enable=1
   Draft=1
   Log=1
   ```
   and DELETE `PicTest=1` (it draws test shapes) and `Reuse=0` (an old Version 1 key). `Draft=1` switches on Plates, Dials, Weapon, RoundOf,
   Popups, LootRing, Escape, HideStock, Lives, head tags (HeadTags, needs HideStock). `Stock=0` stays: the HUD draws on the expansion's maps only; stock Subway keeps the stock HUD.
   The other keys of the ini are not touched.
5. Check: start the game from the menu, open Dead Men maps, Withdrawal, play; `KLHook.log` has `hud: on (Version 3 ... Draft=1 Dials=1 Weapon=1
   Lives=1 RoundOf=1)`, `hud: weapon: on`, `hud: popup: on`, `hud: escape: on`, `tags: HeadTags=1`, no `hud: draft: this level has N of the 8
   extra pictures` line (that warning means an old archive was left; the new check expects 14).
6. Going back: copy the seven archives from `w_tabC7\KLExpansion\Maps\<id>\` over the installed ones, `dinput8.dll` from `owner_before_hud\`
   (or `ship_w12`), put the `[HUD]` lines back (`Enable=0`). An old archive with the new hook is fine (Draft falls back to plain bars; the
   hook logs it); a baked archive with the old hook is fine too (the HUD is off; fonts / plates are level data, so the stock HUD then shows the new faces).

## 5. Risks

- Never played by a person; twelve scripted runs, no fault. The fonts are 17..27 px Anton / Montserrat; stock texts that share the small fonts
  (subtitles, knock-down prompt, score page) have not been looked at.
- The bake affects stock texts on the maps (fonts are shared), nothing outside the seven archives.
- `.prm` size is unchanged within 0.1 MB, so the address-space budget (re/loading.md) does not move.

## 5b. Live checks still owed (owner away, TEST hook `hud_v23_test`, tree with the baked maps, DM03 through its slot F03)

- A1 tags + bar: `[HUD] Enable=1 Draft=1 Log=2` (Log=2 adds 'tags: outline colour ...' and the 5 s line with 'peak draw instances'). Look at: initials
  with a dark outline on a bright wall (picture), the log's outline-colour line says 'alpha byte kept: yes', peak instances under ~320, the
  pop-up bar clear of the loot ring (PopupLift=1 default; PopupTest cycle as run R1p). Optional second run with `HeadTab=1` (tab behind the letters).
  If the outline looks like grey fuzz or solid black: set `HeadOutline=0` (back to v21's single shadow).
- M1 menus: install the hud_menu3 pair, open Arcade, the Dead Men maps page, the lobby / leaderboard pages: capitals must not overflow rows
  (Montserrat 17 px is 12.5 against 14 px stock; Anton / Montserrat glyph coverage unchecked). M2: the round-over board.
- One whole heist per rebaked map load (DM01, DM02, DM03, DM06, DM09, DM03A, DM05A): loads, GO, no fault, subtitles and the knock-down prompt readable.

## 6. What a later `kl_expansion.py install` does to this

- `install <tree> --replace` moves the old `KLExpansion` aside as `.before-N` and copies the TREE's Maps. A tree is built from build folders
  (`kl_expansion.py build ... [--prebuilt id=folder]`), which have NO bake of the new look, and `kl_expansion.py` never calls `kl_hud.py`
  (its comments at lines ~186 only say the HUD look is applied "as the other five got them" by hand). So a later install DROPS the bake and the
  maps are back to the older look (or whatever the build folder had), while the hook keeps drawing - the hook then falls back as in 4.
- The ini is safe: `ini_merge` leaves `[HUD]` alone (it is not one of the sections the block owns); `dinput8.dll` is replaced only when the
  install is run with the hook (`--no-hook` keeps it).
- **WATCH LOOK (2026-10-12, 54ceb35; re/hud_cloud_review.md W1):** `kl_hud_tab.py` / `kl_hud.py` now bake the WATCH look by default (`--watch 1`)
  while the hook's `[HUD] WatchStyle` defaults to 0 (the old look). Until the owner's ini carries `WatchStyle=1`, every rebake for his game must be
  `kl_hud_tab.py build ... --watch 0`; a `--watch 1` archive under a WatchStyle=0 hook draws the wear texture as strikes / rules and the bezel as
  track rings (no crash, visibly wrong). Ship `--watch 1` maps and `WatchStyle=1` TOGETHER, never one alone.
- Remedy, in order of cost: (a) after any install re-run `kl_hud_tab.py build` + copy the zips (the whole chain is 2 minutes of CPU, 1.7 GB);
  (b) build the tree FROM baked folders: bake the build folder (`kl_hud.py all <build> <out> --look deadmen`, the build's zip carries the F01
  name, that is fine) and pass `--prebuilt DM03=<out>` (adopt() renames to the slot) - untested for a bake output, and the DM03A / DM05A
  entries are prebuilt-only already; (c) best: a step in `kl_expansion.build_map` / `adopt` that runs `kl_hud.apply(..., look deadmen)` on the
  staged archive, as `kl_hud_tab.run_hud` does. That is an edit of kl_expansion.py (the lead's), described here, not made.
- `kl_expansion.py uninstall` removes the files it listed; a copied bake keeps the same names, so it removes them as before.
- The tree's `manifest.json` / `BuildInfo\*\result.json` hashes will not match a hand-copied bake; only the installer reads them.
