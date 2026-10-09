# gfx: graphics work for Dog Days (KLGfx proxy, neural rendering bridge)

Owner of this folder: the graphics work stream (not the graft loop). Nothing here touches level data
or kl2.exe code. Branch `gfx`.

## What is here

| path | what |
| --- | --- |
| `klgfx/klgfx.cpp` | `d3d9.dll` proxy for kl2.exe (32-bit). Mode 0 pass-through, 1 wrap (perf/memory log, frame capture), 2 wrap on D3D9On12 |
| `klgfx/gen_wrappers.py` | generates `d3d9_wrap.inl` (forwarding methods) from MinGW's `d3d9.h` |
| `klgfx/KLGfx.ini` | settings, installed next to `kl2.exe` |
| `build_gfx.sh` | MinGW i686 build -> `out/d3d9.dll` (out/ is not committed) |
| `tools/frame_report.py` | turns a frame capture (`KLGfx/frame_*/calls.txt`) into a pass list |

## Facts that shape the design

- kl2.exe: 32-bit, D3D9 only (imports `d3d9!Direct3DCreate9`, `d3dx9_42`), no DX10/11 path (the `-dx10`
  option does nothing), not large-address-aware (2 GB). Device flags 0x44 = hardware VP + **multithreaded**:
  the game calls the device from more than one thread, so every wrapper that keeps state must lock.
- Steam CEG hashes kl2.exe's code (`re/antitamper.md` on rtp-schemas): no code patches; a proxy DLL and
  import wrappers are fine.
- Address space is tight: the grafted maps have failed `HeapAlloc` for one-block scene files (kl2 0x7bb336 ->
  NULL -> write fault 0x8e5bbd; 28.9 MB in RD1, 101 MB on 2026-10-09 11:07). Anything heavy must live in
  another process. The proxy logs `address space free / largest block` every StatsEvery seconds.
- Seen on the owner's PC: RTX 4070 Ti, driver 591.59 (32.0.15.9159).

## Upscalers and neural rendering: what fits

- **DLSS 4.5 (NVIDIA SDK 310.9.1)**: no 32-bit Windows build, so not in-process; would need a 64-bit helper
  with D3D12 interop and MSVC-built NGX libraries. Parked.
- **OpenDLSS-NR** (github.com/maanHimself/OpenDLSS-NR, MIT, 2026-09): a Vulkan reimplementation of the DLSS 5
  neural rendering network (71 blocks, FP8). Facts from its README/docs:
  - not an upscaler: same resolution in and out; it restyles the frame (tone, structure, skin);
  - input per pixel: an sRGB display proxy of the frame, 3 lanes of Gaussian noise, the previous output
    reprojected by motion vectors, 5 conditioning scalars; output: RGB residual + temporal blend logit;
  - Windows x64, NVIDIA Ada or newer, Vulkan with `VK_KHR_cooperative_matrix`, `VK_NV_cooperative_matrix2`,
    `VK_EXT_shader_float8`, `VK_NV_cuda_kernel_launch`;
  - 4070 SUPER, network only: 7.8 ms at 1080p, 12.6 ms at 1440p, 29.3 ms at 4K;
  - **ships no weights**: the user supplies a model directory (`manifest.json` + 11 E4M3 stage files,
    141 MiB) and is responsible for the rights to it. Nothing in this repository extracts or ships them.

## The bridge (being built)

```
kl2.exe (32-bit, D3D9)                         klnr.exe (64-bit, Vulkan, OpenDLSS-NR code)
  KLGfx d3d9.dll                                  NrPass: preprocess -> 71-block network -> composite
   at the insertion point (before the HUD):
   StretchRect -> GetRenderTargetData ---- shared memory (BGRA8 frame + header) ---->  upload
                                       <--- shared memory (BGRA8 result) ----------  readback
   UpdateSurface -> StretchRect back
```

- v0 transport is CPU shared memory (works on native D3D9, a few tens of MB of address space at 1080p).
  A zero-copy route (D3D9On12 shared D3D12 resources imported into Vulkan) is possible later but costs the
  game process the D3D12 runtime and driver, which the 2 GB budget may not allow.
- Without a model directory the helper runs in pass-through (input copied to output through the whole path),
  which tests the bridge and its cost without NVIDIA's data.
- Insertion point: first version at Present (the HUD is then processed too); the frame capture identifies
  the HUD's first draw so the pass can run just before it.
- Motion: K&L2 has no velocity buffer. First version: zero motion (the network's own blend logit rejects
  bad history); later camera reprojection from depth and the view-projection constants (named in the
  shaders' constant tables, which the capture prints).

## Status

- KLGfx 0.1 built (MinGW), ran once in the game on 2026-10-09 11:07 (mode 1): device made, then the run hit
  the out-of-address-space fault above. Disabled since (renamed to `d3d9.dll.klgfx`).
- Not installed in the game folder. Install only in a run agreed with the graft loop.
