#!/bin/sh
# Build and run a klhook off-game harness on Linux (cloud sessions): MinGW i686 + Wine, no Visual Studio, no game.
#   tools/run_harness_linux.sh <name> [args...]      e.g.  klsb_test   kladren_test   klwatch_test sweep
# Needs: apt-get install gcc-mingw-w64-i686 wine wine32:i386 (dpkg --add-architecture i386 first).
# The DLL itself (klhook.c) cannot be built this way (MSVC naked __asm forwarders in klsteam.c); a type check of it:
#   tools/run_harness_linux.sh --check-hook        (compiles a scratch copy with those forwarders stubbed; -fsyntax-only)
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); OUT=${TMPDIR:-/tmp}/klhook_harness; mkdir -p "$OUT"
if [ "$1" = "--check-hook" ]; then
    rm -rf "$OUT/cc"; cp -r "$HERE/klhook" "$OUT/cc"
    sed -i 's/^#define KLX_FWD(n) .*/#define KLX_FWD(n) static void klx_fwd##n(void) { }   \/* GCC TYPE CHECK ONLY *\//' "$OUT/cc/klsteam.c"
    for v in SHIP TEST; do D=; [ $v = TEST ] && D=-DKLHOOK_TEST
        i686-w64-mingw32-gcc -fsyntax-only -Wall -Wno-unused-function -Wno-misleading-indentation -Wno-unknown-pragmas -Wno-parentheses \
            -Wno-sign-compare -Wno-missing-braces -Wno-maybe-uninitialized -Wno-unused-but-set-variable -Wno-format-truncation $D "$OUT/cc/klhook.c" 2>&1 \
            | grep -E "error|warning" | sed "s/^/$v: /" || true
        echo "$v: type check done"; done
    exit 0
fi
N=$1; shift; D=; [ "$N" = kladren_test ] && D=-DKAD_TEST
i686-w64-mingw32-gcc -O0 -w $D -D_CRT_SECURE_NO_WARNINGS -I"$HERE/klhook" -o "$OUT/$N.exe" "$HERE/klhook/$N.c" -lm
cd "$HERE/klhook" && WINEDEBUG=-all wine "$OUT/$N.exe" "$@"
