#!/bin/sh
# End-to-end test of KLGfx + klnr.exe without the game or an NVIDIA GPU: Wine (32-bit and 64-bit), Xvfb, Mesa's
# llvmpipe (OpenGL for Wine's Direct3D 9, lavapipe for Vulkan). The network itself cannot run here (it needs an
# NVIDIA Ada GPU); everything around it does: the D3D9 wrapper, shared memory, the helper, the frame round trip.
#   apt: wine64 wine32:i386 xvfb mesa-vulkan-drivers(:i386) libgl1-mesa-dri:i386
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
T=$HERE/out/test
export WINEDEBUG=-all WINEPREFIX=${WINEPREFIX:-/tmp/klgfx-wineprefix} PATH=/usr/lib/wine:$PATH WINEDLLOVERRIDES="d3d9=n,b"
rm -rf "$T" && mkdir -p "$T"
cp -r "$HERE/out/KLNR" "$T/KLNR"
rm -f "$T/KLNR/klnr.log"
cp "$HERE/out/d3d9.dll" "$T/"
i686-w64-mingw32-g++ -O2 -static -s -o "$T/klgfx_testapp.exe" "$HERE/klnr/klgfx_testapp.cpp" -ld3d9
cat > "$T/KLGfx.ini" <<'INI'
[KLGfx]
Mode=1
StatsEvery=2
CaptureAt=1.5
CaptureDumpTargets=1
CaptureMaxDumps=4
[NR]
Enable=1
Test=1
Model=none
TimeoutMs=3000
INI
echo "== 64-bit stand-in game against klnr.exe"
(cd "$T/KLNR" && xvfb-run -a wine64 klnr_harness.exe --model none --size 320x240 --frames 4 --test 2>&1 | grep -E "PASS|FAIL")
echo "== 32-bit D3D9 program with KLGfx as its d3d9.dll"
cd "$T" && xvfb-run -a -s "-screen 0 1280x1024x24" wine klgfx_testapp.exe ${1:-8} 2>&1 | grep -v "^X connection" | tail -6
echo "== KLGfx.log"; tail -n 25 "$T/KLGfx.log"
echo "== klnr.log"; tail -n 8 "$T/KLNR/klnr.log"
