#!/bin/sh
# Assembles out/KLGfx_dist (what goes to the PC): d3d9.dll, KLNR\ (klnr.exe, the stand-in games, kernels, shaders,
# licence), the test / install / remove scripts and the KLGfx.ini presets. Run build_gfx.sh and build_klnr.sh first.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
D=$HERE/out/KLGfx_dist
rm -rf "$D" && mkdir -p "$D"
cp "$HERE/out/d3d9.dll" "$D/"
cp -r "$HERE/out/KLNR" "$D/KLNR"
rm -f "$D/KLNR/klnr.log" "$D"/KLNR/*.ppm
cp "$HERE"/dist/* "$D/"
(cd "$HERE/out" && tar czf KLGfx_dist.tar.gz KLGfx_dist)
echo "packaged $D ($(du -sh "$D" | cut -f1)), out/KLGfx_dist.tar.gz"
