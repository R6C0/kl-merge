# Task brief for the cloud coding agent (Codex)

You are joining **A Newer Perspective (ANP)**, a mod that ports all of *Kane & Lynch: Dead Men* (DM, 2007) into *Kane & Lynch 2: Dog Days* (DD, 2010). Both games run on IO Interactive's Glacier 1 engine, and both exes are 32-bit Windows with base 0x400000. A Python converter turns each player's own DM level files into DD format. A 32-bit ASI plugin, `ANP_Loader.asi`, patches behaviour at run time. You have:
- this repo;
- a copy of the DD install folder;
- a copy of the DM install folder.

The project lead is W. A local Claude session (the "lead") does all in-game testing on W's Windows PC. **You cannot run the games.** Your job is reverse engineering, implementation and offline verification. The lead tests what you hand back.

## 1. Read first
0. `docs/HANDOFF_CODEX.md`: the organised hand-over. It has every finding with addresses and object layouts, M02's gate chain (§8, the test bed for Tasks 1–3), the RappellingBox census, the ANM merge filter (new moves need it extended), where per-frame loader code runs, and which parts of CLAUDE.md are stale.
1. `CLAUDE.md`. It's long, but it holds hard-won engine facts and rules. Read all of it, especially "Hard-won facts", "CEG-clean loader", "Crew orders", "Climbing" and "Next steps".
2. `loader/climb.inc`: the proven pattern for a new player move. It uses:
   - a frame hook through the kl2 import slot `steam_api!SteamAPI_RunCallbacks`;
   - a real `ZFFActionVaultOver` whose vptr points at a loader-owned vtable copy;
   - warping along root motion;
   - every engine call inside a VEH fault guard, with a `climb: FAULT` line that disables the feature.
3. `loader/squad.inc`: crew orders. It shows how to read input, select a merc, call Recruit `0x908040`, Follow `0x4c3900`, slot 83 `0x831850` and slot 79 `0x760e50`, and its pointer-validation style.
4. `tools/port_level.py`, `tools/prpconv.py` and `tools/scriptconv.py`: the converter. Note the env-switch convention (`ANP_*`, default on or off, and byte-identical output when a new switch is at its old value).

## 2. Setup (Linux container)
- Install: Python 3 with `pip install capstone pefile`; `ffmpeg`; and a 32-bit MinGW cross compiler (`i686-w64-mingw32-gcc`).
  - `loader/build.sh` exists.
  - If it assumes MSYS2, build with `i686-w64-mingw32-gcc` and the same flags as `loader/build.bat`.
- Point the tools at the game copies: `ANP_DD_GAME=<DD folder>`, `ANP_DM_GAME=<DM folder>` and `ANP_WORK=<repo>/work`. `tools/anp_paths.py` reads these.
- `tools/setup_workspace.py` needs JC's kl-merge schemas pinned at commit `8466319`: `re/schemas_dd.json`, `re/schemas_dm.json` and `tools/dd_enums.json` (see CLAUDE.md, "Getting set up").
  - If `work/ext/kl-merge` can't be cloned, stop and say so in your report. Don't fall back to the statistical conversion (`ANP_EXACT=0`).
- Run `py tools/setup_workspace.py --dd "$ANP_DD_GAME" --dm "$ANP_DM_GAME"`. It takes a few minutes and fills `work/`.
- Check the pipeline by building M02: `ANP_OUT=work/out_codex ANP_SET=CameraFogBegin=0.25 python tools/port_level.py M02_A M02A M02`. The build log must contain `validate OK` and `validate nodes moved 0`.
- Never run two `port_level.py` builds at once: they share `work/_tex_out.bin`.

## 3. Hard rules (non-negotiable)
- **Never commit or push game data, or anything derived from it.** That covers zips, prp, gms, prm, TEX, ANM, SND, WAV, WHD, str, bik, extracted scenes, built levels and `work/`. `.gitignore` covers most of it; check `git status` before every commit. Nothing from either game is redistributed.
- **Never modify the game files.** Treat both game folders as read-only, and never change `kl2.exe`.
- **No code-byte patches in kl2.exe.** Valve CEG hashes most of `.text` and `.rdata` and kills the game. The loader may only use:
  - import-slot hooks;
  - writes to `.data` or the heap;
  - vptr swaps onto loader-owned vtable copies;
  - VEH guards.
- **Node order.** Never insert level entities anywhere except at the tail. Static node indices are baked into several files. `tools/ovlcheck.py` (and the in-build validator) must report 0 nodes moved.
- **Switches.** Every new behaviour goes behind an `ANP_*` env switch (converter) or a mode word in an `<DD>\ANP_*.txt` file (loader).
  - Anything not proven in game defaults to `dry`/`off`. `dry` means it probes and logs what it would do.
  - With a switch at its old value, the build output must be byte-identical: prove it with SHA-1 of every output file.
- **Honest reporting.** Label every claim as either proven (disassembly or data you looked at) or inferred.

## 4. What to do, in priority order
W playtested today. He says these three DM mechanics are **required to progress M02 and later levels**. They're missing in the port.

### Task 1: weapon giving and swapping with squad mates (highest)
DM has an inventory wheel. The player (Kane) gives his current weapon to a crew member and takes theirs in exchange.

M02 is the tutorial. In `020_GettingGuns`, the player must give Lynch a shotgun (`Shotgun_Remington_870`) and a pistol (`Gun_Taurus_01`). `WeaponFilter` events check that `ROOT\Lynch` holds that weapon. DM PlayerMonitor list 19 ("inventory changed") re-runs the check. Right now the converter bypasses this with `ANP_BUDDY_WEAPONFILTER=pass` (in `port_level.py`, search for it).

1. **RE in DM (`kaneandlynch.exe`):** the wheel and give/swap code:
   - the classes and the input;
   - the function that moves an item from player to merc;
   - the merc weapon slots (DD reads the actor weapon handle at `actor+0x7d4`);
   - any restrictions;
   - the events it raises.
2. **RE in DD (`kl2.exe`):** what can add an item to an AI soldier's inventory and equip it, and what can remove one from the player. Known facts:
   - slot 303 `0x7b6b40` removes an item from a soldier;
   - the item registry is at gameMgr+0x15b0 (gameMgr = `*(0xdd265c)`);
   - `0x7597d0` gives a weapon's item id; it falls back to the weapon's `InventoryBinding` event at +0x34;
   - `0x8847e0` maps an id to an item type, 0..3 (4 means unbound and crashes at `0x49f260`, so never let an unbound weapon reach it).
3. **Implement `loader/give.inc`:**
   - Choose a free key and check it against squad.inc, climb and DD's own bindings.
   - The key gives the player's current weapon to the merc selected in `squad.inc` and swaps theirs back, if DM swaps. Follow DM's rules and refusals; play a voice ack if one is cheap.
   - Make sure the given weapon object is the one `WeaponFilter` checks. With `ANP_BUDDY_WEAPONFILTER=off`, M02 must then progress naturally.
   - Mode file `ANP_give.txt` (`off|dry|live`, default `dry`).
   - Log lines start with `give:`.

### Task 2: grenades
Find out why the player can't use grenades in converted levels, then fix it. Candidates:
- grenade pickups (geom `0x10048a` with grenade items);
- `ITEM_MAP` in `prpconv.py` (`eFF2ItemGrenade_*`);
- the player's starting inventory (player entity properties, or script commands in mini-cutscenes; see `scriptconv.py`);
- DD's player throw input and inventory slot;
- the grenade weapon and ammo templates after `ANP_WEAPON_DMG` (`Conv.weapon_damage`);
- M02's grenade tutorial gate. DM PlayerMonitor lists 12, 13 and 20 are currently dropped as "never raised by kl2". DD event 30 `eTHROW_THROWABLE` (raised at kl2 `0x6d0c66`) is the likely equivalent; add it to `pm_map` in `prpconv.py` behind `ANP_PLAYERMON_THROW`.

Prove each step offline as far as possible.

### Task 3: rappelling
DM has a rappel move at `RappellingBox` volumes: the end of the M02 tutorial, M03A, the start of M09A's office, and more. The converter keeps `RappellingBox`, but nothing happens in DD. Rope entities (`0x200499`) are neutralised.
1. **RE the DM move:** its class, the trigger (use prompt or automatic), its clips (`/Movement/Rappel/...` or similar), the motion, and how it ends.
2. **Check DD:** does kl2 have anything usable (`RappellingBox` class code, an abseil or zipline)?
3. **Check the levels:** list every `RappellingBox` in the 16 DM levels and say which ones are on an exit chain. `work/gap/entities/gap_scan_prog.py` can help if `work/` exists.
4. **Implement `loader/rappel.inc`:**
   - Follow the `climb.inc` pattern: the action trick and warping the player down the rope line with DM clips.
   - Make sure the clips survive `tools/anm_merge.py`'s path filter in `port_level.py`.
   - Put any converter changes in a new module `tools/rappel.py` with a one-line hook into `port_level.py`.
   - Mode file `ANP_rappel.txt` (default `dry`).

### Task 4: review a half-finished change
A session was paused mid-task. `loader/squad.inc` has a new `critical=keep|clear` option. With it set to `clear`, the option zeroes `script+0x513` on friendly mercs so their death doesn't fail the mission (kl2 init `0x615c90` → slot 57 `0x725b20`; death reads it at `0x8f44a0`; merc list count at `[0x1548fd8]`, scripts at `[0x1548fdc+4*i]`).
- It was compiled once (20:25) but never reviewed, installed or run in game. Review it for pointer safety, CEG safety and correctness. A checkpoint load restores +0x513 from the save, so it must re-clear after every scene load and every change of `[0xe0e644]`.
- Fix it, or report what's wrong.

### Task 5: only if budget remains
DM vehicles are neutralised: M01 stunt car and escape van; the M03B van chase; the M07 monster truck; M11/M11B BTRs and the T72; the M13B van.
- Stock DD never uses `ZHavokCar` (0x2000d4); it uses `ZAnimatedVehicle` (0x2000d8).
- Statically resolve the DM vehicle rout schemas (MoveOnRoad, Exit, SpecialMove, Getaway, Fire) and the DD code paths a `ZHavokCar` would run.
- Write up a concrete plan in `docs/VEHICLES.md`. Research only; don't implement.

## 5. How to hand back
- **Branch:** work on `codex/dm-mechanics` and open a PR to `main`. Commit after each finished task with a clear message, so the lead can test tasks separately.
- **Loader:**
  - Each feature is its own `.inc` file, with one `#include` and one tick/init call in `loader/anp_loader.c`.
  - Every engine call goes inside a VEH guard.
  - It must build warning-free with the cross compiler.
  - Commit the source only, never the `.asi`.
- **Report:** write `docs/CODEX_REPORT.md`. For each task include:
  - what you found, with addresses, and what is proven vs inferred;
  - what you changed (files and switches, with defaults);
  - how you verified it offline (commands and their output);
  - an **in-game test plan** for the lead: which level, where, which key, which mode-file setting, and the exact `ANP_log.txt` lines to expect on success and on failure;
  - risks, and what you'd do next.
- **Budget:** work in this order and stop when the deliverables are done. Don't spend credits on speculative rewrites, reformatting or refactoring code you weren't asked to touch. If something blocks you (missing schemas, a toolchain problem), write it in the report and move on to the next task.
