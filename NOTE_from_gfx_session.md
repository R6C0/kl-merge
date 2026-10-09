# Note for the graft loop from the gfx session (claude.ai), 2026-10-09 13:15

Josh asked the claude.ai session that owns the graphics work (branch `gfx`, see `gfx/README.md`
there) to pass this on. That session cannot type into VS Code (computer use allows only clicks in
VS Code, cmd and Explorer) and your game runs leave ~30 s gaps, so it cannot do these steps itself.

What exists: KLGfx, a `d3d9.dll` proxy for kl2.exe (import-level only, no code patches), plus KLNR:
a 64-bit helper `klnr.exe` that runs OpenDLSS-NR's network (MIT; no NVIDIA weights) on each frame
through shared memory. Built and tested under Wine; never run on this PC's GPU or inside the game.
Package: `<DM>\KL_PortTools\KLGfx\`. NOT installed: the Dog Days folder holds only inert leftovers
of an earlier test (KLGfx.ini, KLGfx.log, d3d9.dll.klgfx - nothing loads them).

Josh's request (he gave permission for these three steps):
1. Between your runs (no game needed, 1-2 min, GPU self-test):
   `cmd /c ""<DM>\KL_PortTools\KLGfx\TEST klnr helper (no game).bat" nopause"`
   Results land in `<DM>\KL_PortTools\KLGfx\KLNR\klnr.log` (the gfx session reads it from its side).
2. When it suits your loop: `"<DM>\KL_PortTools\KLGfx\INSTALL KLGfx into Dog Days.bat" nrtest`, one
   direct-boot autotest with shots, then `"<DM>\KL_PortTools\KLGfx\REMOVE KLGfx from Dog Days.bat"`.
   Expected: the right half of the frame comes back grey (test mode), and `<DD>\KLGfx.log` says
   "NR: N frames through klnr". At 640x480 it adds about 2.4 MB to the game process (the frame
   view is mapped at the top of the address space).
3. A run with `d3d9.dll` in the Dog Days folder is not a clean graft run: keep such runs out of
   graft crash triage.

A line in your Open work saying what you did is enough; delete this file afterwards.
