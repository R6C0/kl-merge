# third_party/anp - files from luvsic's "A Newer Perspective"

Source: `github.com/luvsicccc/a-newer-perspective` (private), commit `c053aa2` (2026-10-11), read from the local clone
`G:\kl_scratch\luvsic\anp`. Author: **luvsic** (and his Claude sessions). Copied here on 2026-10-11 on the owner's word
("copy the files youd want / need into the repo since you are a collaborator / i am").

These files are **his code, unchanged**. Credit him wherever something of this is used; do not edit them here - if one
needs a change, copy it into `tools/` under a `kl_` name, say where it came from, and change that. No game data is in
them (his repository holds none; the `fxc/miss_*.txt` lists are shader permutation NAMES collected from his log).

His project converts whole Dead Men STORY levels to run as the campaign in Dog Days; this project grafts a Dead Men MAP
under a Dog Days level's systems. So his converter (`port_level.py`, `prpconv.py` ...) is not taken: only what our
grafted maps lack or assumed. What each file is for here, and what was found by reading it against our builds, is in
`re/luvsic_pass.md`.

| Folder | Files |
|---|---|
| `docs/` | `ANM_FORMAT.md` (the whole .ANM spec with the exe evidence), `progress_and_format_notes.md`, `HANDOFF.md`, `anm_skeleton_report.txt` |
| `tools/` | `anm_lib.py`, `anm_merge.py`, `anm_codec.py`, `verify_merge.py` (animation library: parse, merge Dead Men clips into a Dog Days file, verify), `clipsnd.py` (clip sound ids), `scriptconv.py` (mini-cutscene scripts), `sndconv.py`, `whdconv.py` (Dead Men sound bank), `fxc.py`, `fxclib.py`, `fxcalias.py` (shader cache with alias entries), `pfconv.py` (pathfinder), `climbs.py`, `graft.py`, `gunfit.py` |
| `loader/` | `adpcm.h` (IMA ADPCM block decoder), `climb.inc`, `squad.inc`, `cutdiag.inc` (parts of his runtime loader, for reading) |
| `scripts/` | `hvk_ray.py` (a model of Dog Days' player ray against a level's collision, checked against the game), `climb_spots.py` |
| `fxc/` | `miss_<level>.txt`: the shader permutations each converted story level asked Dog Days for and did not get |

Several of these import his other modules (`prp`, `gms`, `anp_paths` ...) and his work folder layout: they are here to
be READ and lifted from, not to be run from this folder as they are.
