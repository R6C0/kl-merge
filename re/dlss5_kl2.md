# DLSS5-Feeder on Dog Days (kl2.exe) - setup notes, NOT INSTALLED (2026-10-13)

Upstream: https://github.com/jlrouzies-fr/DLSS5-Feeder (read at 34edfe1 = 1.19.0). Only genuine source: its GitHub
Releases page (the repo warns about fake copies; check the zip's SHA-256 against the release page).
Nothing here has been downloaded, installed or run on the owner's game. These notes are for the owner, who installs it.

## Which path kl2.exe takes
- kl2.exe is 32-bit and the owner launches it with `-dx10` = Direct3D 10. Upstream's 32-bit add-on has a D3D10
  backend ("Install for a DirectX 10 game (beta)"): NO dgVoodoo2 / translation layer. Beside kl2.exe:
  ReShade 6.8+ with add-on support as `dxgi.dll`, `dlss5-feed.addon32`, `reshade-shaders\Shaders\DLSS5_Feed.fx` +
  a motion-vector provider. In a new `host64\` folder: `dlss5-feed-host64.exe`, a 64-bit ReShade `dxgi.dll`, a neural
  consumer (Deep Fried Chicken's three files, or `renodx-dlss5.addon64`), `nvngx_dlssnr.dll`, `nvngx_dlss.dll`.
- D3D10 = DLAA only (no upscaling): no engine jitter / NGX parameters; the finished frame + inferred motion.
- Motion vectors: LumeniteFX (`DLSS5_MV_PROVIDER 3`); it has a non-compute path, which D3D10 needs (SM4).
- Upstream's installer: `powershell -ExecutionPolicy Bypass -File .\Install-DLSS5Feeder.ps1` beside kl2.exe
  (`-Api D3D` if detection hesitates). It asks for UAC for some steps, downloads from reshade.me, GitHub (feeder,
  LumeniteFX) and RankFTW/rhi-repo (the NVIDIA DLLs, RenoDX); Deep Fried Chicken is Discord-only (manual).
  The default `nvngx_dlssnr` 310.8 build is RTX 50 only (older RTX: a build from the RenoDX Discord).

## With KLHook
- No name clash: KLHook is `dinput8.dll`, ReShade goes in as `dxgi.dll`. The installer reuses an existing proxy only
  if it IS ReShade (Install-DLSS5Feeder.ps1 ~2297), so it leaves our dinput8.dll alone.
- No kl2.exe code change (Steam CEG unaffected); KLHook's Steam guard is unaffected.
- Address space (32-bit): KLHook logs ~1080 MB free, largest piece ~518 MB at the front end. ReShade + the add-on
  live in the game process (the DLSS work is in the 64-bit helper), so watch KLHook.log's 'memory:' lines and
  [Memory] ReserveMB=128 for out-of-memory on the big levels.
- The HUD is part of the frame DLAA reconstructs (KLHook draws through the game). Watch the crew list / watch /
  gun dial text for softening or trails while turning.
- D3D10 costs two GPU drains a frame (no fences): measure with the add-on's own GPU-cost figures.

## Test (owner present, game closed)
1. Back up / list the Dog Days folder: dxgi.dll, d3d10*.dll, ReShade*, reshade-shaders\, host64\ must not exist yet.
2. Install (upstream script or by hand as above). Launch normally (Steam, -dx10).
3. Pass = ReShade overlay shows the DLSS 5 Feed add-on; `dlss5-feed.log` has 'feature ready ... DLAA' and
   'frame N delivered'; `host64\dlss5-feed-host.log` exists; KLHook.log shows the HUD lines and no FATAL / ASSERT.
4. Rollback = delete beside kl2.exe: dxgi.dll, dlss5-feed.addon32, dlss5-feed.cfg, dlss5-feed*.log, ReShade.ini,
   ReShadePreset.ini, ReShade.log, reshade-shaders\ ; and the whole host64\ folder. KLHook's files are untouched.

## RUN 2026-10-13 22:29 (the owner installed it with the D3D route; TEST hook hud_v42 menu route, Steam launch -dx10)
- WRONG ABOVE: kl2.exe is a Direct3D 9 game. Its imports name d3d9.dll / Direct3DCreate9 and nothing of d3d10 / d3d11 / dxgi;
  `-dx10` is on the command line but the exe has no such string (it is ignored). ReShade.log: ReShade (as dxgi.dll) was
  loaded only 25 s after the start (22:29:29, when something in the process asked for DXGI - D3D11 probe devices, again at
  22:30:55 and 22:38:03, most likely an overlay), it hooked d3d9.dll AFTER the game had made its device, d3d10.dll was never
  loaded. No ReShade banner on the pictures, no "feature ready", no frames delivered, no host64 log: the feed never ran.
- KLHook and the game were fine with it loaded (RESULT PASS, 0 asserts, 0 faults, 84708 frames).
- THE FIX (the owner runs it, the installer is upstream's): `powershell -ExecutionPolicy Bypass -File .\Install-DLSS5Feeder.ps1 -Api D3D9`
  = dgVoodoo2 as D3D9.dll (Direct3D 9 -> 11) with ReShade as dxgi.dll behind it, the route upstream gives Direct3D 9 games.
  Watch then: dgVoodoo adds a translation layer in the 32-bit process (memory lines in KLHook.log), the HUD draws through
  the game so it goes through dgVoodoo too.
