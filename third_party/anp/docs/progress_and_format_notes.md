# A Newer Perspective: progress and format notes

*Written by Claude for W. Last updated 10 Oct 2026, evening.*

## Where things stand

**Goal:** all of Dead Men's levels running inside the Dog Days engine, built by a converter that runs on each player's own Dead Men install. No Dead Men assets get redistributed.

**Campaign:** all 16 story levels convert without errors (M01 M02 M03 M03B M05 M06 M07 M08 M09 M09B M11 M11B M12 M13 M13B M14). M01 is the test level. M02 loads.

**Level 1 (M01)**

What works:
- Loads and stays stable. Death and respawn work.
- **Enemies die** (W confirmed). See "Soldier settings" below.
- Lynch follows Kane.
- Police AI engages.
- Dead Men's dialogue streams are decoded on the fly.
- **Dead Men's animations are merged into the level** (cutscenes, level-specific acting, climbing). See ANM_FORMAT.md.

Being tested now:
- **Van climb:** a use prompt plus a Dog Days MiniCutscene that plays Dead Men's climb clips (details below).
- **Sound and intro:** these broke for one build and the fix is being tested.
- **Brightness:** world environment lights scaled down; awaiting W's verdict.
- **Load time:** foreground-window throttle in the loader.

Still broken:
- Pause menu: it opens but isn't drawn.
- Kane's gun hold looks wrong.
- Alt-tab crash. Possibly overlays: JC saw Discord's hook crash the game.
- Missing shaders: ScatterNew (grass), GlassSurface, rigid Glow.

## How to run it

1. Press Play in Steam. `ANP_autoload.txt` (`M01 1 12`) starts M01 about 12 seconds after launch.
2. Press **Enter** at "Buffering 100%".
3. To get the normal menu back, delete or rename `ANP_autoload.txt`.

The log is `ANP_log.txt` in the Dog Days folder.

**Loader test hooks** (create the file in the Dog Days folder):
- `ANP_quit.txt`: quits the game.
- `ANP_shot.txt`: screenshot to `ANP_shot.bmp`.
- `ANP_nodes.txt`: dumps the node table.
- `ANP_gui.txt`: dumps the GUI state.
- `ANP_where.txt`: positions of the listed nodes plus all Player objects.

The old first-person mod (`KL2_FirstPerson.asi`) was moved to `_claude_removed/old_firstperson_mod`. Its overlay covered the screen.

## New findings (10 Oct)

### Soldier settings (ZSoldier, class ZSoldierRout)

The converter matched these up statistically and got them wrong: Dog Days inserted four floats in the middle.

| Values | Dead Men | Dog Days |
|---|---|---|
| Enums | 4: type, two eNever/eAlways switches, skill | same |
| Floats | 9 | 14 |
| Then | int, string, merc enum, bool | string, merc enum, bool, enum, bool |

- Health is float 3 (field 7). A value ≤ 0 means invulnerable.
- Dog Days fields 9–12 are health factors per difficulty, always 1.0. The old converter put Dead Men's 50/50/5000/0 there, and the 0 made enemies unkillable.
- Any skill other than eCustom applies a preset (JC's table). Dead Men's skill names exist in Dog Days and are now kept.
- Converter: `prpconv.Conv.soldier()`.

### Enum values

Statistical conversion used to replace any enum value Dog Days' own levels never used with the most common one. Some results:
- "all dead" triggers became "all inside";
- frag grenades became smoke;
- car blow-up "None" became "Definite".

It now accepts any value from Dog Days' exe enum tables (`dd_enums.json`). Two exceptions keep the old behaviour, because the old mapping was load-bearing:
- `ZMercSquad`: Merc_04 → Kane makes Lynch's squad Dog Days' buddy squad.
- ZROOM inside/outside classes, which drive room audio.

### Animations (.ANM)

- Dead Men and Dog Days use the same format except the clip record size (0x50 vs 0x68). Full spec in **ANM_FORMAT.md**.
- `tools/anm_merge.py` builds the level library: Dog Days F03's library plus every Dead Men clip that's needed. Dog Days keeps its clips for paths both have; Dead Men-only paths are added. Unmapped Dead Men databases (Female, Van, Police_USA = the police car, weapons) become their own databases.
- M01: 1,391 clips added, 46 databases, 35.6 MB.

### Climbing

- Dog Days has no climb move: Dead Men's `ZFFPlayerMovementClimb` was removed. Dead Men's heights were Up/Low 120, Medium 170, High 220 cm.
- Rebuilt per spot in `tools/climbs.py`:
  - a **ZPlayerAction** use prompt is added on the Dead Men climb-hint box, which is moved to the climb start;
  - a Dog Days MiniCutscene is grafted from L01 (`01_MiniCut_Vault_Over_Desk`), with three PosObjects. The player `act`s Dead Men's `/Movement/Climb/Up/High` and similar clips, snapped to each PosObject.
- ZPlayerAction member layout (real offsets):
  - +0x34 s
  - +0x38..+0x48: five target lists (activated on use)
  - +0x4c s
  - +0x50 prompt text key
  - **+0x54 enabled**
  - +0x58 use-geom path (empty = owner volume)
  - +0x5c..+0x5f bools
  - +0x60 InterpolateDest, +0x64 InterpolateDir, +0x68 PlayerFilter, +0x6c FA filter, +0x70 USEACTION
  - +0x74, +0x75 bools
  - Init is vtable slot 13 (0x4c4de0) and registers with gameMgr+0x15e0. The message handler is slot 26 (0x7fdbb0).
- PosObject facing: a stored 3x3 faces its third row. Identity is stored as [0,0,1,0,1,0,1,0,0].

### Lighting / brightness

- Dead Men's Environment lights (0x80000d, 48-byte PRM chunk: colour, intensity, …, ambient colour) are about 2x Dog Days' values, because Dead Men also had baked lighting.
- The converter scales world environments (sun ×0.45, ambient ×0.55) and character ones ×0.9. Env vars: `ANP_ENV_SUN`, `ANP_ENV_AMB`, `ANP_ENV_CHAR`.
- PostFilter and light chunk formats are identical in both games.

### Tips from JC (kl-merge author), for later

- **Memory:** kl2.exe isn't large-address-aware. A level load allocates 32 MB scratch, then .fxc, .prm and .ANM (each file size + 0x60000), then the whole .WAV. A failure crashes at 0x8e5bbd. Do not set the 4 GB flag (the engine tags pointers with the top bit).
- **PRM limit:** the .prm chunk table at 0xeac7b0 holds at most 73,728 entries.
- **Hit crash:** a bullet hitting a converted character can crash at 0x4c34b3 if a bone definition's id byte (+0x3e) isn't synced with the renumbered skeleton.
- **Executions:** the first execution can crash at 0x4098a1 (ExecutionBloodSpatter define order).
- **Weapon handling:** the anim folders come from a table indexed by the item enum (0x154a650).

## Format notes (the hard-won bits)

### Static handles and the node table

- Every scene entity gets a node in one runtime table: `*(*(0xe0ff90)+0xc)`, stride at +4, base at +0xc, object at node+0x60, parent at node+0x50. A static handle is `0x40000000 | index<<7`.
- Nodes are allocated:
  1. ROOT first;
  2. then block by block, blocks numbered in preorder of the group-type entities;
  3. inside a block, by slot (prio×8 + basetype);
  4. then by entity order.
- `tools/clusters.py: node_order()` reproduces this.
- The collision octree and other copied files bake these indices. Grafted subtrees therefore hang at the tail, under the nearest plain ZGROUP ancestor of the last group entity.

### Menus

- Dog Days builds in-game windows from `menu/ingame.xml` inside `ZWINDOWS\Menu`, which needs a `ZXMLGUISystem` event. The pause logic finds the manager via the `MenuZWindows` define and the camera via `MenuCam`.
- Dead Men's own window classes are made inert in place, and their events are dropped.

### Shaders

- Each level ships a precompiled permutation library (`.fxc`). The key is an exact, ordered match on (kind, effect, define list).
- No match means no draw. The loader aliases misses at runtime to the closest permutation.

### Sound

- Dog Days streams Ogg, PCM and codec 26.
- Dead Men's dialogue is IMA-ADPCM; the loader decodes it into a virtual PCM region of the `.str` file.

## Next steps

1. Climb: confirm in game with the position logger, then add the M01 warehouse wall, M03A, M03B and M13A climbs.
2. Pause menu rendering.
3. Gun hold (Dog Days grip clips on Dead Men weapon and attacher positions).
4. Proper lighting (Dead Men lightmaps and ambient-occlusion volumes).
5. Load-test M02 onward.
