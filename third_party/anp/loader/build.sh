#!/bin/sh
# Builds ANP_Loader.asi (32-bit Windows DLL loaded by an ASI loader, e.g. Ultimate ASI Loader as dinput8.dll).
# Needs MinGW-w64 (i686). Output goes in ../build/.
set -e
cd "$(dirname "$0")"
mkdir -p ../build
i686-w64-mingw32-gcc -O2 -shared -o ../build/ANP_Loader.asi anp_loader.c -static-libgcc -lgdi32
echo "built ../build/ANP_Loader.asi"
