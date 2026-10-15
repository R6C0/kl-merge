# KL Merge - ReShade effects v2 (worker fx, 2026-10-15)

Files in this folder:

| File | Goes to (game folder `C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\`) | What it is |
|---|---|---|
| `KL_Look.fx` | `reshade-shaders\Shaders\` (replaces v1, back it up as `KL_Look.fx.before-v2`) | The "Heat" grade with the adaptive sky. Technique name is still `KL_Look`. |
| `KL_Glare.fx` | `reshade-shaders\Shaders\` (new) | Stable anamorphic glare on light sources only. |
| `KL_CameraFX.fx` | `reshade-shaders\Shaders\` (new) | The raw handheld-camera layer, driven by the hook. |
| `KL_Camcorder.fx` | `reshade-shaders\Shaders\` (replaces the installed one) | **Bug fix**: the installed file does not compile (see below). |
| `ReShadePreset_KL.ini` | game folder (back up the old one as `.before-fx`) | SMAA, Uplift, KL_Look, KL_Glare, KL_CameraFX. |
| `ReShadePreset_LiveLeak.ini` | game folder (back up the old one as `.before-fx`) | SMAA, Uplift, KL_Camcorder, KL_CameraFX (KL_Glare listed but off). |

No textures and no other files are needed. `ReShade.ini` does not need any change (PresetPath / F7 / F8 keys stay).
KL_FXAA stays off in both presets; SMAA stays first.

## BUG FOUND: the installed KL_Camcorder.fx does not compile

`fmod()` is not a ReShade FX intrinsic. Line 106 of the installed `KL_Camcorder.fx` fails with
`error X3004: undeclared identifier or no matching intrinsic overload for 'fmod'` (I checked it with ReShade 6.8.0's own
effect compiler built from source, the same version the owner runs). So the LiveLeak preset showed SMAA only, with no
camcorder effect at all. That fits the night's fps numbers: LiveLeak 185 fps vs KL 173. The fixed copy here uses `%`
instead, which gives the same result.

## Order in the effect list (both presets)

`SMAA` -> `Uplift` (the NR marker; it costs nothing while Neural=0) -> `KL_Look` or `KL_Camcorder` -> `KL_Glare` -> `KL_CameraFX` (always last).

## Cost (2560 x 1440, RTX 4070 Ti class; estimates, not measured)

| Effect | Passes | Expected |
|---|---|---|
| KL_Look v2 | 1/8-res analysis + 2 x 1x1 + 1 full-res | ~0.2-0.3 ms (v1: 3 quarter-res + 1 full-res, measured ~8 % at ~150 fps) |
| KL_Glare | 6 small passes at 320 x 360 + 1 full-res composite (2 taps) | ~0.05-0.08 ms |
| KL_CameraFX | 1 full-res pass. 1 tap while the inputs are 0, 6 taps while active | ~0.02 ms idle, ~0.1-0.15 ms active |

PerformanceMode=1 (owner's ReShade.ini) bakes every slider into the shader, so the sliders cost nothing and the values
in the preset files are the ones used. After a slider is changed in the overlay, ReShade recompiles that effect once.

## KL_Look v2 knobs

- **Tone**: `Exposure` (stops; negative = moodier, the highlights stay put), `AutoExposure` (0-1: pull every scene toward `SceneKey`,
  so bright levels are held down and dark ones are not mud), `Contrast` (filmic, around middle grey), `LocalContrast` (grit, texture pop),
  `BlackCrush` / `BlackFloor` (crushed blacks, but with a faint cool floor so they never go to ink).
- **Colour**: `Saturation` 0.80 (restrained), `SkinKeep` (skin keeps more of its colour), `KeepColour` (the HUD's colours and neon signs are
  not graded), `ShadowTint` / `ShadowAmount` (steel-blue shadows and mids), `PracticalTint` / `PracticalAmount` (warm sodium / tungsten on bright
  non-sky highlights).
- **Sky**: `SkyControl` (strength), `SkyRatio` / `SkyMin` / `SkyMax` (target sky brightness = scene average x ratio, clamped),
  `SkyDetail` (stretches cloud detail when the sky is flat), `SkyColour` / `SkyTint` (heavy steel grey-blue), `SkyGradient` (darker toward the top),
  `SkyDebug` (paints the sky mask magenta, to check what counts as sky).
- **Finish**: `Sharpen` (CAS-like), `Grain`, `Vignette`, `AdaptSpeed` (seconds the exposure and sky take to follow a change of view).
- Preprocessor `KL_LOOK_DEPTH` (default 1). Depth is used only when the effect detects a real depth buffer: 8 raw samples must not all be equal.
  The owner's ReShade.ini has Generic Depth disabled, so it runs on the heuristic sky (bright + smooth + low chroma, more likely high on the screen).
  Set it to 0 to remove the depth taps entirely.

## KL_Glare knobs

`Threshold` / `Knee` (how bright something must be, with a soft edge), `Isolation` + `RingRadius` (only things smaller than about RingRadius x
screen height glare; skies and lit walls never do), `Intensity`, `Length` (long tail), `MaxGlare` (hard ceiling, soft-clamped), `Tint` /
`TintAmount` (cool anamorphic blue; 0 = the light's own colour), `Smoothing` (seconds of temporal smoothing: kills the flicker and the popping;
higher values lag a little in fast camera turns), `GlareDebug` (shows the glare on its own).

About "sometimes the glare looks like the camera feel": the glare that looks like a camera is very likely **the game's own**. Dog Days draws
its lens flares and bright lights through its built-in camcorder-style post effect, before ReShade sees the frame, and in the LiveLeak preset
the camcorder's 720p crunch and bloom go on top. A ReShade effect cannot remove what the game has already drawn. KL_Glare adds a clean streak
that stays the same from frame to frame. If the hook can turn off the game's flare or camera post effect, that is the way to get rid of the
camera-looking glare (a task for the hook side; I have not found where the game does it).

## KL_CameraFX: the uniforms the hook sets (for worker rsb)

Effect file `KL_CameraFX.fx`, technique `KL_CameraFX`. The hook sets these four `float` uniforms **every frame**:

| Uniform | Range | Meaning (what the hook should feed) |
|---|---|---|
| `KL_Fire`  | 0..1 | How hard you are shooting. Suggested: +0.12-0.2 per shot (more for shotguns / LMG), decay ~2 /s, clamp to 1. |
| `KL_Hurt`  | 0..1 | Recent damage. Suggested: jump by the damage fraction (x2-3) on a hit, decay ~0.7 /s. |
| `KL_Down`  | 0 or 1 | 1 while knocked down (ramping it over ~0.3 s looks softer). |
| `KL_Speed` | 0..1 | Movement speed (sprint = 1). |

- They have **no initializer on purpose**. With PerformanceMode=1, every uniform that has one is baked into the shader as a constant and can no
  longer be set from code. I checked with ReShade 6.8's compiler: these four stay real uniforms. They are hidden in the overlay (`hidden = 1`)
  and never saved to the preset (`nosave = 1`). Do not add `= 0.0` to them.
- All four at 0 = the pass returns the untouched pixel: the image is exactly clean until the hook writes them.
- `KL_FxAmount` (overlay slider, default 1) is baked in performance mode, so the hook cannot change it. For an in-game intensity setting,
  multiply the four values by the setting before writing them.
- `Preview*` sliders in the overlay let the owner try the look without the hook (they combine with the hook's values by max).
- API (ReShade add-on API, `include/reshade.hpp` of ReShade 6.8): the hook must register as an add-on once ReShade32.dll is loaded
  (`reshade::register_addon(hModule)`, the hook DLL exports `NAME` and `DESCRIPTION`), then in a `reshade_begin_effects` callback:
  `h = runtime->find_uniform_variable("KL_CameraFX.fx", "KL_Fire"); runtime->set_uniform_value_float(h, &v, 1);`
  Cache the four handles. Look them up again in `reshade_reloaded_effects` (handles die when effects reload, for example on the F7/F8 preset
  switch). `find_uniform_variable` returns 0 while effects are loading: skip that frame.
  `effect_runtime` is a C++ interface (vtable): from KLHook's C unity build, the simplest way is one small `.cpp` file compiled on its own,
  exposing a C function like `klfx_set(float fire, float hurt, float down, float speed)`.
- Technique toggles from the in-game settings: `runtime->find_technique("KL_Glare.fx", "KL_Glare")` (and `"KL_Look.fx","KL_Look"`,
  `"KL_CameraFX.fx","KL_CameraFX"`), then `runtime->set_technique_state(t, on)`. **Do not toggle KL_CameraFX on and off per frame to save the
  idle cost.** With `SkipLoadingDisabledEffects=1`, a technique that is turned on loads and compiles its effect (a hitch). Leave it on; it costs
  ~0.02 ms when idle. Toggle only when a setting changes.
- Gates: the same as the hook's other features (Arcade only / not a stock level), if the lead wants them.

What each input does: **Fire** gives a fast recoil jitter, a little barrel distortion and chromatic aberration, macro-blocking, sharpening crunch,
exposure flicker (muzzle flashes overshooting the camera's auto exposure) and sensor noise. **Hurt** gives a jolt, more distortion and aberration,
blocks, an exposure dip, drained red colour and a pulsing red-edged vignette. **Down** gives a slow sway and roll, strong distortion, a soft
blur, darkening, desaturation and a heavy vignette. **Speed** gives a walk bob and a light vignette. A matching zoom means shake and roll never
show the frame edge.

## "Optimise DLSS 5": what DLSS5_Feed.fx and Uplift are

- **DLSS5_Feed.fx** is the companion effect of the *DLSS 5 Feed* add-on (`dlss5-feed.addon32`, set aside as `.off` in the game folder). That
  add-on only attaches to D3D10/11/12, Vulkan or OpenGL. Kane & Lynch 2 runs on D3D9 (ReShade.log: `Direct3DCreate9`; dgVoodoo is set aside as
  `D3D9.dll.dgvoodoo`), so on D3D9 the file compiles to a pass-through stub with a notice. It is in neither preset and costs nothing. It cannot
  be made cheaper, and it does nothing here.
- **Uplift.fx** is only the position marker of the **GITC-Uplift** add-on (`gitc-uplift.addon32` + `gitc-uplift-helper64.exe` +
  `GITC-Uplift\nvngx_dlssnr.dll`): NVIDIA DLSS-NR neural rendering at Present. The marker is a 1-pixel pass and costs nothing. The cost
  (Neural=1: 106-178 fps against 188 without, so +0.3 to +4 ms a frame) is the add-on itself:
  1. **Main cost on D3D9: the frame copy.** Uplift's README: "DX9: NR copies each frame through memory, about 3 ms at 1080p. Use Direct3D 9Ex
     brings that down to about 0.4 ms." The owner's `ReShade.ini [Uplift] UseD3D9Ex=0`. **Setting `UseD3D9Ex=1` is the one change that should
     make Neural=1 much cheaper** (likely most of the 106-fps case). Side effects: exclusive fullscreen becomes a borderless window; it needs a game
     restart; if the game will not start, Uplift turns the option off again by itself. It needs a live test with KLHook (it changes how the D3D9
     device is created: check that the HUD / Present hooks still work).
  2. `ResolutionMode=1` is already *Quality* (67 %). 2 = Balanced (58 %), 3 = Performance (50 %) are cheaper but look worse.
  3. `PassCount=1` is already the minimum. `KeepFaces` must stay 0 (it runs NR one more time per frame).
  4. The dgVoodoo D3D11 route is faster according to Uplift's README, but the night's notes record dgVoodoo crashing in this 32-bit game
     (address space): not recommended.
  Nothing was installed or changed.

## What I could and could not verify

- **Verified**: all four .fx files go through ReShade 6.8.0's own preprocessor, parser and HLSL code generator (built from the v6.8.0 source)
  with no errors or warnings, for shader model 3 (D3D9) and for 5, with performance mode off and on. With performance mode on, `KL_Fire` /
  `KL_Hurt` / `KL_Down` / `KL_Speed` stay settable uniforms. The tone curve and the sky maths were checked numerically (for example: a blown-out
  sky at 1.0 comes out at about 0.55 steel grey; a flat 0.55 sky at about 0.47 with its cloud contrast stretched x1.6; black comes out at about
  0.015, not 0; mid grey 0.45 at about 0.43 with a cool bias).
- **Not verified**: the last step, Microsoft's fxc compiling the generated HLSL for ps_3_0 (there is no fxc, wine or vkd3d on the VM or in the
  container). I wrote around the known SM3 traps: no gradient fetches inside branches (tex2Dlod there), unrolled constant loops, analysis passes
  kept small, so they stay under the instruction limits. The ReShade.log after the first launch will show any error. Not seen in game: the look,
  the cost, the sky heuristic (a bright smooth wall high on the screen can be taken for sky: check with `SkyDebug`), and the glare's lag in fast turns.
