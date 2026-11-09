# third_party/anp - files from luvsic's "A Newer Perspective" (campaign port)

Source: `github.com/luvsicccc/a-newer-perspective` (private), commit **`32aa649`** ("Converter and loader work from 12-15
Oct"), read from the local clone `G:\kl_scratch\luvsic\anp` (never written). Author: **luvsic** (and his Claude sessions).
Everything here is **ported from luvsic's a-newer-perspective @32aa649, in contribution with luvsic**. Refreshed on
2026-11-09 from the earlier copy (`c053aa2`, 2026-10-11) on the owner's word: "pull luvsiccs repo and merge it with mine
somehow? i want his campaign stuff everything hes been doing for that in my game but maybe not the whole ui thing hes done".

His project converts whole Dead Men STORY levels (M01..M14) so they run as the campaign in Dog Days. This project grafts a
Dead Men MAP under a Dog Days level (`tools/kl_graft.py`, `tools/kl_convert.py`). The two pipelines are kept apart: his
converter only ever writes NEW folders `M01`, `M02` ... `M14`, `M07F`, never an `F0x` slot. Run it through
**`tools/kl_campaign.py`** (see `re/campaign_merge.md`); do not run the vendored scripts from this folder.

## The files are his, unchanged - with ONE exception
`tools/anp_paths.py` has one marked edit: `KLMERGE` honours `ANP_KLMERGE` (kl_campaign sets it to this repo, where commit
`8466319` with the pinned schemas and `tools/kl_hvk.py`, `kl_gms.py` are reachable). Any other change goes into a `kl_`
copy under `tools/`, with a note where it came from. No game data is in this folder (checked: no .zip/.str/.bik/.pkl/
.tex/.prm/.dll/.exe, largest file under 1 MB); the generated `fxc/union.pkl` and the work folder are never committed -
`kl_campaign.py` runs from a copy in `<workdir>\anp_work\runtree`.

## What is here
| Folder | Files |
|---|---|
| `tools/` | the whole converter: `port_level.py` (+ `prpconv`, `prpwrite`, `prp`, `gms`, `zipraw`, `clusters`, `pval`, `scene`, `mattab`, `texconv`, `matconv`, `prmconv`, `pfconv`, `whdconv`, `sndconv`, `locconv`, `scriptconv`, `graft`), the new-since-10-11 pieces `rappel.py`, `coverconv.py`, `sndimport.py`, `climbs.py`, `clone_level.py`, animation library (`anm_*`, `verify_merge`, `gunfit`, `clipsnd`, `fxc*`), setup (`setup_workspace`, `anp_paths`, `build_dd_db`, `build_arrlen`, `enumcheck`), dumpers (`actordump`, `entdump`, `evdump`, `worldxf`, `matdump`, `pfdump`, `prmwalk` ...) |
| `loader/` | his runtime companion `ANP_Loader.asi` as **reference source, not built**: `anp_loader.c` + `campaign.inc`, `climb.inc`, `rappel.inc`, `squad.inc`, `give.inc`, `equipassist.inc`, `grenade.inc`, `revive.inc`, `failwatch.inc`, `heapguard.inc`, `resetguard.inc`, `godmode.inc`, `d3dshot.inc`, `cutdiag.inc`, `adpcm.h`, `ANP_*.sample.txt`, `build.bat/.sh`, `test/` |
| `scripts/` | `hvk_ray.py`, `climb_spots.py`, `fxmiss_harvest.py`, his unattended smoke tests (`smoke_*.py`, `kltest.py`, `install_build.py`, `shot.py` ...) as reference; `klhook/arcade_f01.ini` |
| `docs/` | `HANDOFF_CODEX.md` (newest, 12 Oct), `HANDOFF.md`, `PLAYTEST_GUIDE.md` (what plays in each chapter), `TESTING.md`, `ANM_FORMAT.md`, `progress_and_format_notes.md`, `anm_skeleton_report.txt`, `LUVSIC_CLAUDE.md` (his running log to 15 Oct, 80 KB), `LUVSIC_README.md` (his README), `agent_prompts/` (his CODEX_PROMPT / HELPER_PROMPT, agent briefs) |
| `fxc/` | `miss_<level>.txt` (shader permutation names the converted levels asked Dog Days for) |
| `re/` | `rtp.py`, `disx.py`, `xref.py`, `findimm.py`, `vtscan.py` (need capstone, pefile) |

## What was left out, and why
- **The UI the owner does not want**: `tools/dmhud.py` (Dead Men HUD art), `tools/dmfont.py` (Dead Men typefaces),
  `tools/anp_menu.py` (his campaign front-end menu page), `tools/anp_movie.py` (Bink movie handling for that menu),
  `scripts/smoke_menu.py`, `scripts/run_menu_test.ps1`, `scripts/klhook/menu.ini` (their tests). `prpconv.py` still imports
  `dmhud.xhair_props()`; kl_campaign's run tree supplies a 15-line shim that returns None (= Dog Days defaults), and runs with
  `ANP_DM_HUD=0 ANP_DM_FONTS=0`.
- **`tools/locconv.py` is KEPT** (the scouting pass listed it as UI). It is the Dead Men .LOC -> Dog Days text conversion
  `port_level.py` imports: icon-tag renames and cp1252 fixes make the existing text readable; the chapter-title and
  "Morphine+" difficulty keys it adds are LOC keys read by Dog Days' own menus (switch: `ANP_CHAPTER_TITLES=0`,
  `ANP_LOC_EXTREME=0`). Not his menu.
- **What stays on although it sounds like menu**: `ANP_GRAFT_MENU=1` / `ANP_GRAFT_OSD=1` graft **Dog Days' own** menu,
  pause and OSD subtrees (the level has no pause menu / HUD without them). Only Dead Men's HUD/fonts/menu go.
- `.gitignore`, the empty `campaign.inc` at his repo root, `__pycache__`, `fxc/union.pkl` (generated), his `work/`.
- **Missing in his repo**: `tools/dd_enums_extra.json` (squad-modifier enum supplement, `ANP_SMB_FIX`). kl_campaign runs with
  `ANP_SMB_FIX=0` and an empty supplement; ask luvsic to commit it to get the patrol move-set detail back.

## How klhook modules map to his loader `.inc` files
The runtime half is NOT built from here: KLHook ports each piece (other slices write them; names are the plan).

| his `loader/*.inc` | klhook module | what it does |
|---|---|---|
| `campaign.inc` | `klcampaign.c` (+ `klcampaign_gate.h`) | scene-id resolver / level start without the menu, chaining, saves redirect, progress ini |
| `squad.inc` | `klcampsquad.c` | crew orders 1/2/3/Tab |
| `give.inc`, `equipassist.inc` | `klcampgive.c` | give / swap weapon with a crew member (key 4) |
| `grenade.inc` | `klgrenade.c` | G key throw through the NPC release path |
| `rappel.inc` | `klcamprappel.c` | native `ZFFPlayerMovementRappel` modes |
| `revive.inc` (+ `failwatch.inc`) | `klcamprevive.c` | down-not-dead + heal prompt |
| `heapguard.inc` (+ `resetguard.inc`) | `klcampguard.c` | Appendage heap-unlink guard, D3D-reset guard |
| `climb.inc` | already `klhook/klfreeclimb.c` | taken 10-11 (`re/luvsic_pass.md`) |
| `adpcm.h`, `anp_loader.c` ADPCM | not used | our voice path plays without the loader (`tools/kl_voice.py`) |

`CLAUDE.md` rule for the legacy code patches in his loader (`0x6d100f`, `0x71166d` ...): NOT ported. KLHook SHIP builds write
only import slots and data, never hashed code ranges.
