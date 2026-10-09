KLGfx + KLNR for Kane & Lynch 2: Dog Days  (gfx/ in the kl-merge repository, branch gfx)

KLGfx is a d3d9.dll proxy for kl2.exe. With [NR] Enable=1 it hands every finished frame to KLNR\klnr.exe, a 64-bit
helper that runs OpenDLSS-NR's network (MIT licence, github.com/maanHimself/OpenDLSS-NR), and shows what comes back.

NO MODEL IS INCLUDED. OpenDLSS-NR ships no weights: the network's 141 MiB of weights are NVIDIA's DLSS 5 model data,
which you would need the rights to use. Put a model directory (manifest.json + model\) in KLNR\model to use one.
Without it the helper runs with "none" (the frame only makes the round trip) or "zero" (synthetic zero weights: the
whole network runs at its real cost, the picture does not change).

1. TEST klnr helper (no game).bat   - checks the GPU and measures the network without touching the game
2. INSTALL KLGfx into Dog Days.bat  - nrtest (default) / nrzero / capture / off; close the game first
3. REMOVE KLGfx from Dog Days.bat   - takes d3d9.dll out again

In game: F9 switches the bridge on/off, F8 the split view (left original, right processed).
Logs: <Dog Days>\KLGfx.log, <Dog Days>\KLNR\klnr.log.
The frame is taken at Present for now, so the HUD goes through the network too; a frame capture (preset capture)
shows where the HUD starts, so the bridge can move in front of it.
