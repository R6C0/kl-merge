# KL Merge: Kane & Lynch: Dead Men → Kane & Lynch 2: Dog Days

Hobby mod that brings Dead Men's Fragile Alliance content (maps, weapons, characters, audio)
into Dog Days. Both games run on IOI's Glacier 1 engine (the Hitman: Blood Money family), so
Dead Men data is converted into Dog Days' formats and loaded by the unmodified Dog Days exe.
You need to own both games on Steam; no game files are in this repository.

## Layout

| Folder | What it is |
|---|---|
| `tools/` | Python converters for every Glacier 1 file format involved, plus install/restore. |
| `klhook/` | `dinput8.dll` proxy loaded by Dog Days: logs engine asserts/crashes and writes full dumps. |
| `debug/` | Crash-dump triage: decodes kl2.exe minidumps and maps a crash to the exact map object. |

## Formats handled (tools/)

| File | Module | Notes |
|---|---|---|
| `.prp` scene properties (IOPacked v0.1) | `kl_prp.py`, `kl_convert.py` | Round-trips byte-identically. Per-class layout conversion learned from every Dog Days level; enum tables come from kl2.exe (`dd_enums.json`). |
| `.gms` scene graph | `kl_gms.py` | Entity table, class retyping, cluster/pool table rebuild. |
| `.TEX` textures | `kl_tex.py` | Table layout, cube maps, animated textures. |
| `.prm` models | `kl_prm.py` | Mesh descriptor 32 → 48 bytes. |
| `.MAT` materials / `.fxc` shaders | `kl_mat.py` | Property record 16 → 12 bytes; shader union. |
| `PC_Def.str` audio streams | `kl_audio.py` | Merge of Dead Men clips into Dog Days' stream file. |
| level archive | `kl_package.py` | Builds a Dog Days `Fxx_Main.zip`; install backs up originals into `KL_PortBackup/`. |

`verify_levels.py` converts the four FA maps and checks every object against Dog Days' own
levels (layout, enum values, reference lists, fixed array sizes, duplicate item bindings).

## Status

M01 FA (Dead Men) loads into the Dog Days Subway slot (F01) through the whole property stream;
the current work is the post-load scene fix-ups. Sound banks (SND/WHD/WAV) still use Dog Days'
own for the slot.

## Testing loop

1. `tools/INSTALL test map (M01 FA into F01).bat`
2. Dog Days → Arcade Mode → Subway → Accept.
3. On a crash: `KLHook.log` + `KLHook_N.dmp` in the Dog Days folder → `debug/triage.sh`.
4. `tools/RESTORE Dog Days originals.bat` puts every original file back.

## Credits

Built on public Glacier 1 research: glacier-modding (Blood Money BMEdit/BMExport),
HHCHunter's Hitman: Blood Money tools and docs (PRM converter).
