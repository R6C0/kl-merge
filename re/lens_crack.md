# Cracked lens (2026-10-17)

Owner: "if you get shot a lot you get some glass breaking, to show the camera frame glass is cracked ... not too crazy, a chance".
Cosmetic and local: reads game memory only, sends nothing, so it is allowed online too. NOT RUN IN THE GAME (hook compiled, shader
compiled with fxc as ps_3_0 only; never seen on screen).

## Files
- `klhook/klreshade.c` (section 6 of its header): hit detection, trigger rule, crack state, uniforms, technique `TechCrack`.
- `reshade/KL_LensCrack.fx`: the procedural glass (technique `KL_LensCrack`).
- `klhook/KLHook.ini`: documented keys (commented). `reshade/README.md`: file table.

## How a hit is seen
Same reading as KL_Hurt (klbalance.c 2b): health object `[player+0xa48]` (+4 now, +8 maximum, +0x24 = player). A hit = one tick where
the current value fell by >= 1 % of the maximum, the object is the same as last tick, the maximum is unchanged, and the player is not
in the down state (`[[player+0x2948]+4]`). The hook does not know the direction of fire, so the place is random.

## Trigger rule (all GUESS defaults)
Hit times go in a ring (32). On each hit: `hits in LensCrackWindow (4 s) >= LensCrackHits (6)`, or `health < LensCrackHealth (0.35)` with
>= 2 hits in the window -> ONE roll, the ring is emptied (one roll per burst). The crack is added when: fewer than LensCrackMax (3)
stand, LensCrackCooldown (8 s) since the last crack, and `rand*100 < LensCrackChance (35)`. Place: corner (both axes 0.06..0.32 from an
edge, biased to the edge) or edge (one axis so, the other 0.15..0.85); reach 0.17..0.31 of the screen height; intensity 0.75..1.
Cleared when: health reaches 0, the player object / health object changes (respawn as a fed, new round, level load), no player,
health jumps up by > 25 % of the maximum in one tick; the cooldown restarts after a clear. `Log>=1`: a line per crack and per clear; `Log=2` also the failed rolls.

## Ini
`[Graphics]` LensCrack (1; 0 = off: no technique asked for, no uniform), LensCrackHits, LensCrackWindow, LensCrackChance (percent),
LensCrackMax (1..3), LensCrackCooldown, LensCrackHealth. `[ReShade]` TechCrack (default `KL_LensCrack@KL_LensCrack.fx`). Ini only: no
klset.c row (a row needs menu XML + string work, not trivial). Needs `[ReShade] Bridge=1` and ReShade loaded; otherwise no cost, no effect.

## Uniforms (set by name every frame, `source=` annotated, no initializer: performance mode)
`float KL_CrackN` (0..3); `float4 KL_Crack0/1/2` = (x, y in 0..1 of the screen, reach in screen heights, intensity). The reach grows
ease-out cubic over `KLRS_CRACK_SPREAD_MS` = 120 ms from the crack's birth (the hook computes it per frame). The seed of a crack's
pattern is a hash of its x, y. The three float4 are set with `set_uniform_value_float(count 4)`; arrays are avoided.

## Shader
Per crack: 8..14 jagged radial lines (+1 fork each), two partial concentric rings, a pitted bright crater with a dark rim; thin bright
core and a dark band on one side of each line, the picture displaced up to ~1.8 px along the normals (refraction), red/blue split
(1.6 px) near the centre. Nothing within 0.10 screen heights of the middle (crosshair), soft until 0.20. Idle (KL_CrackN 0): one tap.
fxc ps_3_0 (stub header, annotations stripped): compiles clean, ~8500 slots, only evaluated for pixels within a crack's reach
(`[branch]`). Preview slider `PreviewCracks` = 1 shows three cracks without the hook.

## Install (by the owner; nothing was installed)
1. `KL_LensCrack.fx` -> `<DD>\reshade-shaders\Shaders\` (beside KL_CameraFX.fx).
2. New `dinput8.dll` (SHIP build) -> `<DD>`; KLHook.ini needs `[ReShade] Bridge=1` (the Graphics keys are optional, defaults apply).
3. The bridge writes the live preset itself (technique listed last, after CameraFX). With a custom `[ReShade] Sorting=` add
   `KL_LensCrack@KL_LensCrack.fx` last. If the .fx is missing the log says "wanted but not among the loaded effects" once.

## GUESS / unchecked
Every number in the trigger rule, the crack placement, the 120 ms spread, the look constants (widths, strengths); that ReShade accepts a
`source=` annotation on a float4 and a count-4 set on it (the scalar path is proven in the game, the vector path is not); the shader never
seen rendered (only compiled with fxc, not with ReShade's own compiler); the 25 % jump clear; 1 % of max as the hit threshold.
