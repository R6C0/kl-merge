# luvsic's Dead Men CAMPAIGN work in kl-merge (state 2026-11-09, luvsic @32aa649)

Owner, 2026-11-09: "pull luvsiccs repo and merge it with mine somehow? i want his campaign stuff everything hes been doing for that
in my game but maybe not the whole ui thing hes done". Source: luvsic's `a-newer-perspective` clone, commit 32aa649 (the older
copy was c053aa2; `re/luvsic_pass.md` is the 10-11 comparison). Credit on everything: "in contribution with luvsic".

Status words: READ = taken from his code/notes, not run here. PROVEN-BY-HIM = he saw it in game (his claim). Nothing below has
been run on this machine; no game folder was touched.

## 1. What is in kl-merge now

| Piece | Where | Toggle | Status |
|---|---|---|---|
| His converter, tools, loader sources, docs (UI left out) | `third_party/anp/` (README lists, per folder) | - | vendored, READ |
| Runner: setup / convert / status / install / undo | `tools/kl_campaign.py`, self-test `tools/kl_campaign_test.py` (50 checks PASS) | n/a (CLI) | install/undo proven on a temp fake DD tree only; setup + convert NOT run |
| Runtime half (level start without the menu, chaining, saves, crew orders, give, grenade, rappel, revive, guards) | other slices: `klhook/klcampaign.c`, `klcampsquad.c`, `klcampgive.c`, `klgrenade.c`, `klcamprappel.c`, `klcamprevive.c`, `klcampguard.c`; all gated by `klcmp_level_active()` (`[Campaign] Enable=0` + scene key `m<NN>[ab]\`) | each its own ini key, default 0 | see those slices; his `loader/*.inc` are the reference |
| Climb (W+E at ledges) | `klhook/klfreeclimb.c`, `tools/kl_fa_climb2.py` (taken 10-11) and `third_party/anp/tools/climbs.py` (campaign variant: DM climb hint box -> ZPlayerAction prompt + grafted DD MiniCutscene) | existing | climbs.py unchanged since c053aa2 |
| Rappel converter side | `third_party/anp/tools/rappel.py` (new since c053aa2; run by port_level) | `ANP_ROPES`, `ANP_PFILTER_SWAP` (his env) | READ; PROVEN-BY-HIM M02 6.4 s descent, M09 multi-stage |
| Cover boxes | `third_party/anp/tools/coverconv.py` (new; `ANP_COVERS=box`): 1,345 DM ZBoxPrimitive covers DD's list rejects (M02 61, M08 242, M12 252, M13B 474, M14 126) | `ANP_COVERS` | READ. Different job from `tools/kl_cover_1026.py` (FA-layer authoring). His own later note: "every DM cover box works, DD already used most" (PLAYTEST_GUIDE) |
| Sound import | `third_party/anp/tools/sndimport.py` (new; ~960 of 1240 donor ANM clips no longer silent), `clipsnd.py` (clip +0x2C re-point) | `ANP_SND_IMPORT_DD`, `ANP_ANM_CLIPSND` | READ; his note: sndimport untested |
| Animation merge | `anm_merge.py`, `anm_lib.py` (more complete than our `kl_anm`/`kl_anmjoin`) | `ANP_ANM_MERGE` | READ, tools unchanged since 10-11 |
| LOC text conversion | `locconv.py` (kept; see README for why it is not "UI") | `ANP_LOC_FIX`, `ANP_CHAPTER_TITLES`, `ANP_LOC_EXTREME` | READ |

Left out on purpose (the UI): `dmhud.py`, `dmfont.py`, `anp_menu.py`, `anp_movie.py`, his menu tests. `kl_campaign.py` runs with
`ANP_DM_HUD=0 ANP_DM_FONTS=0`; `ANP_GRAFT_MENU=1` and `ANP_GRAFT_OSD=1` STAY because they graft DOG DAYS' own menu/pause/OSD
subtrees (a converted level has none otherwise). Also not taken: his legacy kl2 code patches (0x6d100f, 0x71166d ...), his
ADPCM streaming (our voices play without a loader), the front-end `campaign.inc` menu delivery (fopen 0xb10430 hook).

## 2. How to build, install and start a campaign level (nothing here has been run yet)

All of it from the kl-merge repo root; `<workdir>` = `kl_port_check.workdir()` = `<DM>\KL_PortTools`.
1. `python tools/kl_campaign.py env` - prints what the converter runs with and where each value came from.
2. `python tools/kl_campaign.py setup` - about 2.5 min. Copies `third_party/anp` to `<workdir>\anp_work\runtree`, writes the three
   pinned schemas with `git show 8466319:<file>` (commit exists, ancestor of rtp-schemas, MEASURED by the scouting pass) and an
   EMPTY `dd_enums_extra.json`, then runs his `setup_workspace.py` (extracts every stock DD scene and the DM M* mains into
   `anp_work\scn`, builds dd_db / dd_arrlen / dd_enums pickles, `fxc\union.pkl`, the L01 donor TEX). Reads both installs, writes only
   `anp_work`. `setup --schemas-only` = seconds, no game needed.
3. `python tools/kl_campaign.py convert M01` (or `all`) - `port_level.py M01_A M01A M01`. Output `<workdir>\anp_out\M01\M01_Main.zip`
   (+ loose Loader_Sequence.*, LS_* banks); the funeral `M07F` goes to `anp_out\CutScenes\M07`. The Dog Days folder is never the
   output (refused). Log: `anp_work\anp_logs\convert_<ID>.log`. His own note: ~170 MB zip for M03, 18,703 entities.
   Ids: M01 M02 M03 M03B M05 M06 M07 M08 M09 M09B M11 M11B M12 M13 M13B M14 (+ M07F). M04 and M10 do not exist as levels.
4. `python tools/kl_campaign.py status` - built / installed per id.
5. `python tools/kl_campaign.py install M01` - copies into `<DD>\Scenes\Locations\M01\` (M07F: `Scenes\CutScenes\M07\`) and writes
   `KLCAMPAIGN_MANIFEST.json` (md5 per file) there plus `<workdir>\anp_work\anp_install\UNDO_<ID>.json` outside the game.
   Refuses: kl2.exe running (zombies count), target folder exists without our manifest, a file of an earlier install was edited
   (`--force`), id not in the table, any target in KL_PortBackup or outside `Scenes\`, too little free space.
   `undo M01` deletes only files whose md5 still matches, then the manifest and the directories the install created.
   The owner must run install himself (a write into the game folder can be refused; CLAUDE.md rule).
6. Starting the level: Dog Days' launch options already carry `-o DefaultScene=Locations/F01/F01_Main.gms`; luvsic's note says
   `-o DefaultScene=Locations/M01/M01_Main.gms` loads a converted level without his loader (HANDOFF_CODEX; READ, the owner does
   not change launch options without saying so). Chaining M01 -> M02 -> ... is pure level data (SceneChanger paths rewritten by
   port_level) and needs the full M-id set installed. Gameplay features (crew orders, give, grenade, rappel, revive) need the klhook
   campaign modules with `[Campaign] Enable=1`; without them the levels still load but those inputs do not exist.

## 3. Per-level state (his PLAYTEST_GUIDE / HANDOFF_CODEX, 13-15 Oct; "seen" = his unattended runs)
All 16 + M07F convert (rc 0, 0 nodes moved) and load. Played end to end: only M02. M01 loads, climb 5/5, exit reachable only in his
offline model. M03 playable (stealth start: firing = alarm = mission fail). M03B to the subway. M09 loads, rappel works. M05 M06 M07 M08
M11 M11B M12 M13 M13B M14 load and survive 5 min, nobody played them through. Vehicles, mounted guns, crowds, plants, rain are
neutralised (teleport fallbacks only). Pause menu draw unverified.

## 4. Open items
- `tools/dd_enums_extra.json` is not in luvsic's repo: ask him to commit it, or regenerate the 4 tables (EPatrolMoveset, EDefendMoveSetMod,
  EPlayerMovementModifier, EBoneType) from the kl2.exe .data via `tools/kl_rtp.py`; then drop `ANP_SMB_FIX=0`.
- Run `setup` + `convert M02` once (the only level he played through) and read the report. Needs ~2.5 min + the PC free; writes only the work folder.
- Overlap decision (kept as is): `kl_convert.py` (exact classes, FA maps) stays the FA pipeline; his `prpconv` flattens ZPlant/ZHavokCar/ZLINEOBJ to ZSTDOBJ
  (`re/luvsic_pass.md` section 5: 45 of 56 classes identical on M03_A). Never mix the outputs in one folder.
- A converted campaign level keeps Dead Men's systems in a Dog Days scene with Dog Days' menu/OSD grafted; CLAUDE.md warns that whole-level
  conversion crashes on HUD/menus. His graft is how he avoided that; unproven on this machine.
- Where an M-folder meets the F01 test slot: they do not collide; installing M01..M14 never changes F0x.
- The klhook runtime modules are separate slices; until they exist the campaign levels have no crew orders, give, grenade, rappel, revive.
- Disk: a full `all` build is several GB (C: has been tight; the work folder is on the DM drive, G:).
