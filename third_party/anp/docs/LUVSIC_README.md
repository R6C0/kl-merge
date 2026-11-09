# A Newer Perspective

A mod that brings **Kane & Lynch: Dead Men**'s story levels into the **Kane & Lynch 2: Dog Days** engine. Later goals are Dead Men's multiplayer maps, guns and characters, upscaled textures, true first-person and a free camera.

The converter runs on **each player's own copy of both games**. This repository contains no game files and no data copied out of either game. Do not commit any. `.gitignore` excludes the usual suspects.

## What's here

| Folder | What it is |
|---|---|
| `tools/` | The level converter (Python 3). `port_level.py` turns a Dead Men level into a Dog Days scene folder. Other files: format readers and writers (`prp`, `gms`, `prm`, `mat`, `tex`, `snd`, `anm_*`), property conversion (`prpconv.py`), subtree grafting (`graft.py`), climb rebuilding (`climbs.py`), and analysis helpers (`actordump.py`, `entdump.py`, `evdump.py`, `worldxf.py`). |
| `loader/` | `ANP_Loader.asi`, the runtime companion, loaded by an ASI loader (`dinput8.dll`). It handles the scene-ID resolver and autoload, decodes Dead Men's ADPCM speech streams on the fly, aliases missing shader permutations, adds crash guards and logging, throttles the per-millisecond foreground nudge (fast loads), and provides the test hooks listed below. Build it with `loader\build.bat` (MinGW-w64 i686 GCC, e.g. MSYS2's; `build.sh` on Linux). |
| `re/` | Reverse-engineering helpers. `rtp.py` reads class property lists from either exe. `disx.py` disassembles, `xref.py` finds string references, `findimm.py` finds constants, `vtscan.py` scans member accesses. They need `capstone` and `pefile`. |
| `docs/` | Progress and format notes, the full `.ANM` (animation library) spec, and the skeleton comparison. |
| `fxc/` | Per-level lists of shader permutations a level asked for that Dog Days lacked (`miss_<ID>.txt`, collected from `ANP_log.txt`). `union.pkl` is generated. |
| `scripts/` | `shot.py` (screenshot through the loader's hook into `work/shots/`) and `klhook/`, the test scripts for JC's unattended test loop (`docs/TESTING.md`). |
| `work/` | Generated workspace (git-ignored). |

## Setup

1. Install the tools:
   - Python 3.10+ (on Windows run it as `py`), then `py -m pip install capstone pefile` for `re/`.
   - For the loader, MinGW-w64 i686 GCC: MSYS2's `pacman -S mingw-w64-i686-gcc`. `loader\build.bat` finds it in `C:\msys64\mingw32\bin`.
2. Clone JC's `R6C0/kl-merge` (private, used with permission) into `work/ext/kl-merge` with git.
   - Only its exact class schemas are read, pinned to the commit the tested builds used (`tools/anp_paths.py`).
   - The setup step copies them to `work/ext/schemas`.
3. Build the workspace from your own installs (about 2.5 min; the work folder defaults to `<repo>/work`):
   ```
   py tools\setup_workspace.py --dd "C:\...\Kane & Lynch 2 - Dog Days" --dm "C:\...\Kane and Lynch Dead Men"
   ```
4. The games are found in your Steam libraries. Override with environment variables:
   - `ANP_WORK`: the work folder (default `<repo>/work`).
   - `ANP_DD_GAME`: the Dog Days folder.
   - `ANP_DM_GAME`: the Dead Men folder. **It is only read, never written.**
5. Convert a level, for example Dead Men level 1 (`M01_A`, file prefix `M01A`) into Dog Days scene `M01`:
   ```
   py tools\port_level.py M01_A M01A M01
   ```
   This writes `Scenes/Locations/M01/` into the Dog Days folder, or into `ANP_OUT` when that is set. It refuses to write into the game folder while the game runs.
6. Copy `ANP_Loader.asi` into the Dog Days folder, next to an ASI loader `dinput8.dll`. Put `M01 1 12` in `ANP_autoload.txt` to load the level about 12 seconds after start, and press Enter at "Buffering 100%".

## Loader test hooks

Create these files in the Dog Days folder while the game runs:

| File | Effect |
|---|---|
| `ANP_quit.txt` | quit |
| `ANP_shot.txt` | screenshot to `ANP_shot.bmp` |
| `ANP_nodes.txt` | node table dump |
| `ANP_gui.txt` | GUI state |
| `ANP_where.txt` | positions of the listed node indices, all Player objects, and every registered use prompt |

Everything is logged to `ANP_log.txt`.

## Useful converter switches (environment variables)

| Variable | Effect |
|---|---|
| `ANP_SET` = `CameraFogBegin=0.25` | patch scene settings. PowerShell: `$env:ANP_SET='CameraFogBegin=0.25'`; cmd: `set "ANP_SET=CameraFogBegin=0.25"`. A key that isn't found shows as `setting NOT FOUND` in the report. |
| `ANP_OUT` | write the level to `<ANP_OUT>\<ID>\` instead of the Dog Days folder (test builds) |
| `ANP_ANM_MERGE=0` | Dog Days' animation library only |
| `ANP_ANM_ALL=1` | merge every Dead Men clip (memory heavy) |
| `ANP_CLIMB=0` | no rebuilt climbs |
| `ANP_ENV_SUN`, `ANP_ENV_AMB`, `ANP_ENV_CHAR` | environment light scaling |
| `ANP_EXACT=0`, `ANP_SOLDIER=0`, `ANP_ENUM_EXE=0` | fall back to the older statistical conversions. Without kl-merge's schemas the converter stops unless these are set. |

## Credits

- **W:** project lead, testing, everything Dead Men.
- **JC** (kl-merge, Dead Men Fragile Alliance maps in Dog Days): exact property schemas and many engine notes.
- **Claude** (Anthropic): converter, loader and reverse engineering.
