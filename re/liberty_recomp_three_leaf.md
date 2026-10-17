# LibertyRecomp and a Three Leaf Clover map

## Finding

LibertyRecomp is not an asset converter for arbitrary games. It is a static
recompilation of the Xbox 360 version of GTA IV, using a fork of ReXGlue to
translate that game's PowerPC code and Xenos graphics assumptions into a
desktop build. The repository contains GTA IV-specific generated code,
configuration, manifests, resources, and runtime integration.

Its folder layout can help locate or install the source game data, but the
layout does not make the data compatible with Dog Days. RAGE geometry,
collision, navigation, materials, mission resources, animation, audio, and
compiled script data still need separate extraction and conversion.

## What can be used

For a legally owned local copy, LibertyRecomp may be useful as:

- a way to run or inspect the source mission in a supported environment;
- a reference for how a static recompilation separates generated code,
  platform glue, runtime services, and user-provided game data;
- a source of map geometry and layout reference for an original KL2 heist,
  provided the extraction and conversion are done from the owner's legally
  obtained files.

The LibertyRecomp code itself should not be copied into KL Merge merely because
the projects have similar goals. Before reusing any code, check the applicable
GPL and dependency licenses and keep the dependency's notices and source
obligations separate from the proprietary game data.

## Map-only scope

The intended target is the **map**, not the GTA IV mission. The mission can be
discarded. After the map is converted into Glacier resources, KL Merge can
author its own Fragile Alliance layer: spawn points, loot, police squads,
triggers, routes, escape vehicles, round rules, and voice/audio references.

The useful source categories are therefore limited to:

- static bank and street geometry;
- collision and physics shapes;
- navigation or walkable-space reference;
- doors, breakable objects, props, and map materials;
- lighting and environment reference.

Mission scripts, checkpoints, GTA IV objectives, scripted camera work, and
RAGE AI logic are out of scope for the map conversion.

## What cannot be copied directly

The extracted Three Leaf Clover map cannot be dropped into `KLExpansion` or a
Dog Days location slot. Dog Days expects Glacier resources such as `.gms`, `.prp`,
`.prm`, `.TEX`, `.MAT`, `.buf`, `.oct`, `.HVK`, `.ANM`, `.SND`, `.WHD`, `.WAV`,
and `.LOC`; GTA IV uses a different engine and resource family.

The source map must be converted into those Glacier resources first. Its GTA IV
collision, navigation, materials, textures, animation, and object metadata are
not compatible merely because the files are arranged in a map directory.

## Practical implementation boundary

The feasible route is:

1. extract only the map data from the owner's LibertyRecomp/GTA IV install;
2. convert geometry, collision, materials, textures, and navigation into
   Glacier-compatible resources;
3. validate the converted resources with the existing scene, texture,
   collision, navigation, and package checks;
4. author a new Fragile Alliance layer on the converted map;
5. add original bank entry, vault loot, police waves, routes, and escape logic.

Use Dog Days or properly licensed replacement assets for the shipped result.
Keep any GTA IV files used for private reference or conversion on the owner's
machine, outside this repository and outside distributed builds. If a future
asset conversion is attempted, each imported asset needs a RAGE-to-Glacier
conversion step and validation through the existing scene, material, texture,
collision, navigation, and Fragile Alliance checks.

## Roadmap decision

LibertyRecomp is **not a direct dependency** and is not a ready-made map
converter. It may still be useful as the environment from which the owner
inspects the source map. The mod-first implementation should convert the map
only, then build the mission and Fragile Alliance gameplay independently in
the existing Glacier tooling.
