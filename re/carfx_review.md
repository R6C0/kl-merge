# Review of track T: the black box on burning cars

2026-10-11, adversarial review of `tools/kl_fa_carfx.py`, `re/carfx.md` and the builds `<work>\build\z_carfx\*`.
Offline; nothing ran in the game; the worker's files were not changed.

## Verdict: ACCEPT WITH FIXES - the tool is sound, the identification is NOT proven

- The tool does exactly what it says, on all five maps, and nothing else. It may go to a live test.
- The claim "the dark block of the pictures is the HeatShimmer mesh" is not supported by the pictures. Three of the
  note's picture arguments are wrong in fact (M1, M2, S1), and the fire's own black smoke was not excluded (M3).
- The mesh may still be part of what the owner sees. It is a Dead Men refraction in a form Dog Days never draws for
  that class, so switching it off is harmless and reasonable.
- Do not install it for the owner as "the fix" before the live look. A dark column over a burning car may well remain.

## What I re-ran and confirm

| check | result |
|---|---|
| archive diff, source -> `z_carfx` (my own script, by CRC and bytes) | all five: same member list and order; only `.prm` differs, same size; one run of 1092 bytes per mesh (344 bytes differ per mesh), three runs on Retomoto; no member grew |
| archive sha1 | c2c623e9, 4414a471, 720be205, 26df702f, 521186a0: as reported |
| files beside the archive | all carried; new `carfx.json` / `carfx.txt`; `steps.json` gains `carfx`; `audit.*` differ only in the path, content id and set ordering (M02, M03, M06) |
| `kl_fa_carfx.py check --cars` | source exit 1 on all five; output exit 0 with `RESULT PASS: 0 fault(s)`; vehicle counts 9/9, 7/7, 10/10, 1/3, 67/68 |
| `kl_impact.py` on the outputs | `problems: 0 in 1 levels` x5 |
| `kl_fa_bots_dyn.py check`, source against output | 0 differing lines x5 (42, 31, 43, 26, 65 lines); exits 1/1, 0/0, 1/1, 0/0, 0/0 |
| source build folders | no file newer than 15:30 in any of the five, nor in `w_tabM` |
| `git status` | of the worker: only `tools/kl_fa_carfx.py` and `re/carfx.md`, both new |
| the mesh | 28 vertices, bottom cap + four walls, alpha 0 / 0xbf / 0 at y 0 / 195 / 367, no top: as described |
| Dead Men source | the same `HeatShimmer` entity with the same matrix is in M03_FA_A (node 6507) |
| stock Dog Days | no heat / shimmer node and no `VehicleEffects` controller in F01 or F07; the five Glass forms are right |
| HUD order | the vertex chunk's bytes are identical in `hud_new\DM03`, so `apply` on the HUD build is the right path |

Not re-run: `kl_maps.py audit` (it writes into the build folder; I compared the worker's result files instead), the
shader disassembly, and `apply` on a HUD build.

## MUST

**M1. The picture is darker than the mesh can make it, and dark in the wrong place.**
Luminance of `0007_150s.jpg` (0..255, 40 x 30 px cells):

| rows (y) | x 760..960 | x 1000..1240 |
|---|---|---|
| 0..210 | 1..10 (mostly 1..5) | 3..40 |
| 240..330 | 9..29 | 9..37 |

- The same yellow building is lit at about 100 in `0009_179s.jpg` and `0010_186s.jpg`. So the top of the frame is
  over 97 % covered. The note says "up to 75 %, never opaque".
- The mesh's alpha is 0.75 at 1.95 m and 0 at its top ring (3.67 m). It should be darkest in a band just above the
  roof and fade upward. The picture is the other way round: black at the top of the frame, lighter near the car.
- My estimate from the picture (horizon about y 340, the car's wheels at y 640): the far wall's top cannot be above
  about y 85, and the near wall's alpha at the frame's top is at most about 0.25.
- The car, which stands inside the box and behind its near wall, is not darkened.

**M2. The "hard vertical edge" is not a box corner.**
- `0004_54s.jpg` (inside the bank, x about 775) and `0005_97s.jpg` (garage, x about 1200) show the same vertical
  purple streak, in `0004` with the same one-sided veil and lens flare. No car burns in either.
- It is the game's own light streak. In `0007` it runs through the flare at (700, 460).
- The yellow building's corner against the burnt-out sky lies at the same place: its windows start at x about 680
  in a gamma-raised crop.

**M3. The fire's smoke was not excluded, and it fits better.**
- Both fires a car names carry it: `Car_Fire_USA_Sedan_01` (before the blast, no mesh) has two smoke emitters,
  `..._Cheap` has five.
- Template `Smoke_CarFire_02a`: colour ramp (26, 24, 22) at alpha 178 of 255, texture `FX_Par_Smoke_Dark_05`
  (DXT5, mean alpha 68). That is near-black smoke, and many particles stacked do reach full black.
- I compared `Smoke_CarFire_01a`, `Smoke_CarFire_02a` and `Flames_CarFire_02b` field for field against M03_FA_A:
  identical but for the sprite chunk index. Their sprite chunks have the same form as stock F01 / F07 sprites.
- So the templates are Dead Men's own. What the worker did not compare is the emitter: Dead Men's has 33 fields,
  the build's 35, and `ZParticleEmitter` is on CLAUDE.md's list of assumed pairings. `check` only tests that a
  template, a sprite chunk and a texture exist.
- The note's "None is large and dark" has no evidence behind it.

**Wanted for M1-M3:**
1. Correct sections 2.3 and 6 of `re/carfx.md`.
2. Say in the note and to the lead that a black smoke column may remain after the fix.
3. Rewrite the live check so it separates the two. As written, "no dark pane" fails on smoke.
   - Look at a car that burns but has not blown up: that fire has no mesh. A dark block there is smoke.
   - Compare `z_carfx\M03` and `z_cover3\M03` from the same spot and say what changed.
   - Judge the mesh by its shape: a fixed band at roof height, the same on all four sides, that does not move.
4. If a block remains, the next step is the smoke emitters' field pairing against Dead Men, not `V_Coli_Shot_02`.

## SHOULD

**S1. The far picture does not show the box either.**
- In `0006_104s.jpg` enlarged, the car's body and the wall beside it at roof height are not darkened.
- The dark block starts about 0.6 m inside the car's rear end and reaches about 4.5 m up with a soft top.
- A box round the car with 0.75 alpha at 1.95 m would darken a band wider than the car. This reads as a smoke
  column, so "drawn at any distance" (section 2, point 1) has no picture behind it.

**S2. The archive in the pictures is not the one the worker compared.**
- `KLHook.log` 15:58:13: the round loaded an `F03_Main.zip` of 200,772,920 bytes.
- `hud_new\DM03` is 200,754,498 bytes, written 16:02 and installed 16:04. No build of the first size is on disk.
- "The HUD step did not touch it" is shown for the build installed now, not for the one photographed.

**S3. "A form no stock level draws" is true of the class only.**
`TRANS_ON_OPAQUE` in group 0x41 is Dog Days' commonest decal form: 1045 Standard/Standard instances in the 21 stock
levels. That the refraction comes out black there is a guess with only the picture behind it. The note should mark
the whole cause chain as a guess, not just "which factor is black".

**S4. Count slip.** The five stock Glass forms are 5 + 42 + 1 + 1 + 1 = 50 instances (my count: 50), not 49.

**S5. The box's orientation is taken from the mesh alone.**
The entity's matrix is (0 0 -1 / 0 1 0 / -1 0 0); particle templates carry (0 0 1 / 0 1 0 / 1 0 0). I did not
establish which of these is the engine's "no rotation", so whether the 6.3 m side lies along the car is unchecked.
It does not affect the fix.

**S6. The zero-area mesh** is marked as an assumption, correctly. If a live run misbehaves at a blast, a build with
the positions kept and only the alpha at 0 would tell the two changes apart.
