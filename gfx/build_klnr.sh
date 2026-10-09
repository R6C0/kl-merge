#!/bin/sh
# Build klnr.exe, the 64-bit helper that runs OpenDLSS-NR's network for KLGfx, with MinGW-w64 on Linux.
# Fetches its dependencies at pinned versions into gfx/deps (git-ignored) and writes gfx/out/KLNR/:
#   klnr.exe, spv/ (the network's GLSL kernels), ptx/ (its PTX kernels), shaders/ (frame preprocess + composite),
#   LICENSE.OpenDLSS-NR. No model: the user supplies one in KLNR\model, or runs with none / zero.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
DEPS=${KLNR_DEPS:-$HERE/deps}
OUT=${KLNR_OUT:-$HERE/out/KLNR}
BUILD=$HERE/out/klnr-build
NR_COMMIT=9d08f4184bbcb9d858e2fb7a7834ec0837a9d2f1      # OpenDLSS-NR, 2026-09-21
mkdir -p "$DEPS"
if [ ! -f "$DEPS/opendlss-nr/src/nr_graph.cpp" ]; then
  git init -q "$DEPS/opendlss-nr"
  git -C "$DEPS/opendlss-nr" remote add origin https://github.com/maanHimself/OpenDLSS-NR.git
  git -C "$DEPS/opendlss-nr" fetch -q --depth 1 origin $NR_COMMIT
  git -C "$DEPS/opendlss-nr" checkout -q FETCH_HEAD
fi
[ -f "$DEPS/vulkan-headers/include/vulkan/vulkan.h" ] ||
  git clone -q --depth 1 --branch v1.4.363 https://github.com/KhronosGroup/Vulkan-Headers.git "$DEPS/vulkan-headers"
[ -f "$DEPS/volk/volk.c" ] || git clone -q --depth 1 --branch vulkan-sdk-1.4.357.0 https://github.com/zeux/volk.git "$DEPS/volk"
if [ ! -x "$DEPS/glslang/bin/glslang" ]; then
  mkdir -p "$DEPS/glslang"
  curl -sSL -o "$DEPS/glslang/g.zip" https://github.com/KhronosGroup/glslang/releases/download/16.6.0/glslang-16.6.0-linux-x86_64-release.zip
  (cd "$DEPS/glslang" && unzip -q -o g.zip && rm g.zip)
fi
NR=$DEPS/opendlss-nr
GLSLANG=$DEPS/glslang/bin/glslang

rm -rf "$BUILD" && mkdir -p "$BUILD/obj" "$OUT/spv" "$OUT/ptx" "$OUT/shaders"
cp -r "$NR/src" "$BUILD/src"
(cd "$BUILD" && patch -s -p1 < "$HERE/klnr/opendlss-nr.patch")

for f in "$NR"/shaders/*.comp; do
  "$GLSLANG" -V --target-env vulkan1.3 -I"$NR/shaders" "$f" -o "$OUT/spv/$(basename "$f" .comp).spv" >/dev/null 2>&1 || { echo "glslang failed: $f"; exit 1; }
done
sh "$HERE/klnr/gen_ptx.sh" "$NR" "$OUT/ptx"
"$GLSLANG" -V --target-env vulkan1.3 -I"$NR/demo/shaders" "$NR/demo/shaders/nr_preprocess.comp" -o "$OUT/shaders/nr_preprocess.spv" >/dev/null 2>&1
"$GLSLANG" -V --target-env vulkan1.3 -I"$NR/demo/shaders" "$HERE/klnr/shaders/kl_composite.comp" -o "$OUT/shaders/kl_composite.spv" >/dev/null 2>&1

CXX=x86_64-w64-mingw32-g++
FLAGS="-O2 -DNOMINMAX -DWIN32_LEAN_AND_MEAN -DVK_ENABLE_BETA_EXTENSIONS -I$DEPS/vulkan-headers/include -I$DEPS/volk -I$BUILD/src -I$HERE/klnr"
x86_64-w64-mingw32-gcc -O2 -DVK_ENABLE_BETA_EXTENSIONS -I"$DEPS/vulkan-headers/include" -c "$DEPS/volk/volk.c" -o "$BUILD/obj/volk.o"
for f in kernels nr_graph nr_model vk_context reference; do
  $CXX -std=c++20 $FLAGS -c "$BUILD/src/$f.cpp" -o "$BUILD/obj/$f.o" &
done
$CXX -std=c++20 $FLAGS -Wall -c "$HERE/klnr/klnr_pass.cpp" -o "$BUILD/obj/klnr_pass.o" &
$CXX -std=c++20 $FLAGS -Wall -c "$HERE/klnr/klnr_main.cpp" -o "$BUILD/obj/klnr_main.o" &
wait
$CXX -static -static-libgcc -static-libstdc++ -s -o "$OUT/klnr.exe" "$BUILD"/obj/*.o
# the stand-in game (klnr_client + checks), 64-bit and 32-bit (the game is 32-bit)
$CXX -std=c++17 -O2 -Wall -static -s -I"$HERE/klnr" -o "$OUT/klnr_harness.exe" "$HERE/klnr/klnr_harness.cpp" "$HERE/klnr/klnr_client.cpp"
i686-w64-mingw32-g++ -std=c++17 -O2 -Wall -static -s -I"$HERE/klnr" -o "$OUT/klnr_harness32.exe" "$HERE/klnr/klnr_harness.cpp" "$HERE/klnr/klnr_client.cpp"
cp "$HERE/klnr/LICENSE.OpenDLSS-NR" "$OUT/"
echo "built $OUT/klnr.exe ($(stat -c %s "$OUT/klnr.exe") bytes), $(ls "$OUT/spv" | wc -l) spv, $(ls "$OUT/ptx" | wc -l) ptx"
