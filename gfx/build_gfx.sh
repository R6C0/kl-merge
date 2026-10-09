#!/bin/sh
# Builds gfx/out/d3d9.dll (32-bit) with MinGW. Static C/C++ runtime: the DLL needs nothing but Windows.
set -e
cd "$(dirname "$0")"
mkdir -p out
i686-w64-mingw32-g++ -std=c++17 -O2 -Wall -Wno-unknown-pragmas -shared -static -static-libgcc -static-libstdc++ \
    -Wno-delete-non-virtual-dtor -fno-exceptions -fno-rtti -o out/d3d9.dll klgfx/klgfx.cpp klnr/klnr_client.cpp klgfx/exports_mingw.def -luuid \
    -Wl,--enable-stdcall-fixup -s
echo "built gfx/out/d3d9.dll"
