# gfx: graphics work for Dog Days (KLGfx proxy, neural rendering bridge)

Owner of this folder: the graphics work stream (not the graft loop). Nothing here touches level data
or kl2.exe code. Branch `gfx`.

## What is here

| path | what |
| --- | --- |
| `klgfx/klgfx.cpp` | `d3d9.dll` proxy for kl2.exe (32-bit). Mode 0 pass-through, 1 wrap (perf/memory log, frame capture, NR bridge), 2 wrap on D3D9On12 |
| `klgfx/gen_wrappers.py` | generates `d3d9_wrap.inl` (forwarding methods) from MinGW's `d3d9.h` |
| `klnr/` | KLNR: the neural rendering bridge. `klnr_protocol.h` (shared memory layout), `klnr_client.*` (game side, compiled into the proxy), `klnr_main.cpp` + `klnr_pass.*` (klnr.exe, 64-bit, OpenDLSS-NR's network), `shaders/kl_composite.comp`, `opendlss-nr.patch` (GCC fix + synthetic zero model), `gen_ptx.sh` |
| `klnr/klnr_harness.cpp`, `klnr/klgfx_testapp.cpp` | stand-ins for the game: 32/64-bit bridge client, and a 32-bit D3D9 program that loads the proxy like kl2.exe |
| `build_gfx.sh`, `build_klnr.sh` | MinGW builds (Linux) -> `out/d3d9.dll`, `out/KLNR/` (out/ and deps/ are not committed) |
| `test_wine.sh` | end-to-end test without the game or an NVIDIA GPU: Wine + Xvfb + Mesa (llvmpipe / lavapipe) |
| `dist/`, `package_dist.sh` | what goes to the PC: test / install / remove scripts, KLGfx.ini presets -> `out/KLGfx_dist` |
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

## The bridge (KLNR)

```
kl2.exe (32-bit, D3D9)                         klnr.exe (64-bit, Vulkan, OpenDLSS-NR code)
  KLGfx d3d9.dll, at Present:                     KlNrPass: upload -> preprocess -> 71-block network
   GetRenderTargetData(back buffer) -> system          -> temporal composite -> readback
   surface -> shared memory  ---- Local\KLNR_<pid>_f<gen>, _req event ---->
   <--------------------------------------------- result in place, _done event
   UpdateSurface back into the back buffer, Present
```

- Transport v0 is CPU shared memory (works on native D3D9; at 1920x1080 it costs the game process about 16 MB of
  address space: one system-memory surface and the shared frame). Synchronous: the frame waits for the helper
  (TimeoutMs, default 100; MaxMisses frames in a row without a result switch it off for the session).
- klnr.exe without a model ("none") makes a plain Vulkan device and only does the round trip + composite, so the
  bridge works and can be tested on any GPU. "zero" builds a synthetic all-zero model in OpenDLSS-NR's layout (no
  NVIDIA data): the whole network runs at its real cost and its non-finite head is treated as "no change".
  A model directory (manifest.json + model\) must be supplied by the user in `KLNR\model`.
- Composite for a game frame (`kl_composite.comp`): the frame arrives as an sRGB image (sampled linear, paper
  white 1), leaves as the same encoding (no ACES display transform), B,G,R,A for D3D9; split view; test pattern.
- Motion: none yet (Dog Days renders no velocity buffer): the motion image says "history at the same pixel". GUESS
  that is fine for a still camera; in motion only the network's own blend weight rejects stale history. Next:
  camera reprojection from depth and the view-projection constants (named in the capture's constant tables).
- Insertion point: Present, so the HUD goes through the network too. Next: a capture (`dist` preset `capture`)
  to find the HUD's first draw and run the bridge just before it.
- Reference counts: the proxy counts references on its own wrapper; when the game lets go of it, the bridge's
  surfaces are released first (each holds a device reference), so the device is destroyed as without the proxy.
- Thread safety: the game's device is D3DCREATE_MULTITHREADED. Nothing keeps pointers to the game's objects
  between calls: the capture asks the device for its bindings and reads shader bytecode with GetFunction, under
  one lock (0.1 kept a shader table without a lock and scanned every token of every shader at creation, which
  could run past the end of the code).
- Address space: the shared frame view is mapped at the top of the address space (MapViewOfFileEx), away from
  the bottom-up region the game's large scene-file blocks come from; F9 off and any switch-off give both the view
  and the system-memory surface back. Until the bridge has been seen on a grafted map, test it on stock levels.
- Device lost (alt-tab from full screen): frames are skipped until the Reset, the bridge stays on. A result that
  arrives after the timeout is never mixed into the next frame (the client waits for it to finish first).

## Tested (2026-10-09, cloud, Wine 9.0 + Xvfb + Mesa llvmpipe/lavapipe; `test_wine.sh`)

- klnr.exe --selftest, no model, 640x480: round trip exact (largest channel difference 0); test pattern right.
- 64-bit and 32-bit stand-in games through klnr.exe: exact round trip, frame growth (new frame section +
  helper resize), test pattern.
- 32-bit D3D9 program with KLGfx 0.3 as its d3d9.dll (like kl2.exe): frames come back processed, Reset to a new
  size, a second thread creating ~550,000 shaders/textures while frames are captured, device released cleanly.
- Failure paths: helper missing (NR off, program goes on), helper killed mid-run (noticed, goes on), NR off,
  mode 0.
- NOT tested here: the network itself (needs an NVIDIA Ada GPU), and anything in kl2.exe. On the PC:
  `dist/TEST klnr helper (no game).bat` first (no game), then a game run with the `nrtest` preset.

## For the graft loop (VS Code agent)

Nothing of this is installed in the game folder. The package is in `<DM>\KL_PortTools\KLGfx\`.
`INSTALL KLGfx into Dog Days.bat [nrtest|nrzero|capture|off]` puts d3d9.dll + KLGfx.ini + KLNR\ into Dog Days
(no stock file is replaced: Dog Days has no d3d9.dll); `REMOVE KLGfx from Dog Days.bat` moves d3d9.dll out.
A run with KLGfx installed is not a clean graft run: remove it before crash triage of the graft.

## Status

- KLGfx 0.1 ran once in the game (2026-10-09 11:07, mode 1): device made, then that run hit the
  out-of-address-space fault above. Disabled since (renamed to `d3d9.dll.klgfx`; INSTALL deletes that file).
- KLGfx 0.3 + klnr.exe 0.1: built, tested as above (an independent review of 0.2 found the issues fixed in 0.3:
  shader scan past the end of the code, dangling pointers in the capture, wrapper lifetimes, lost device,
  late results racing the next frame, session restart), staged on the PC, not installed.
- klnr.exe 0.2 (2026-10-09): a review of the network path, which has never run (no machine here has the
  extensions), against OpenDLSS-NR's demo found what a real NVIDIA GPU would show and lavapipe hid:
  - the frame was read back from the first HOST_VISIBLE | HOST_COHERENT memory type, which on NVIDIA is
    write-combined (CPU reads an order of magnitude slower: 8-15 MB per frame would have blown the 100 ms timeout);
    now a HOST_CACHED type (a warning in the log if there is none);
  - the chained PTX launches' watchdog word was never read or cleared: one stuck wait would have made every later
    frame wrong without a word in the log. Checked after the warm-up and every frame as the demo does; on a timeout
    the frame passes unchanged and the network is rebuilt with a barrier after every launch;
  - the no-model device reset query pools from the host without `hostQueryReset`, and ran a SPIR-V 1.6 composite
    on Vulkan 1.2 (now SPIR-V 1.5);
  - started by the game, klnr.exe inherited Steam's environment, which switches on the Steam overlay's and
    Fossilize's implicit Vulkan layers: implicit layers are now off in klnr.exe (`KLNR_LAYERS=1` keeps them);
  - the kernels' split-K scratch is sized at the first frame size: made again for a larger frame (1080p -> 4K
    would have thrown); a resize sets the state to STARTING, so KLGfx shows frames untouched meanwhile instead of
    counting them as missed (30 in a row switched the bridge off);
  - the self-test prints a verdict per step (`RESULT PASS|FAIL ...`), the TEST script writes `KLNR\selftest.log`
    fresh and lists the verdicts; INSTALL / REMOVE no longer break their messages on the `&` in the Dog Days path.
  Wine run of `test_wine.sh` and the self-tests (none, test pattern) passed again; staged on the PC
  (`<DM>\KL_PortTools\KLGfx`), not installed.
