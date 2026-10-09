#!/bin/sh
# Generate OpenDLSS-NR's PTX kernels (the same list and arguments as its scripts/build_shaders.ps1, pinned commit).
#   gen_ptx.sh <OpenDLSS-NR checkout> <output dir>
set -e
S="$1/scripts/ptx"; O="$2"; mkdir -p "$O"
gen() { s="$1"; shift; python3 "$S/$s" "$@" >/dev/null || { echo "PTX generator failed: $s $*"; exit 1; }; }
for k in 64 128 256; do gen mlp_e4m3.py $k "$O/mlp_e4m3_K$k.ptx" 3 1 1; done
for c in 64 128 256 512; do gen qkv_e4m3.py $c "$O/qkv_e4m3_K$c.ptx" 80; done
for k in 32 64 128 256 512 1024; do for f in 5 13 4 8 6; do gen gemm2_e4m3.py $k $f "$O/gemm2_e4m3_K${k}_f$f.ptx"; done; done
for cfg in "64 4 0" "128 4 0" "256 3 80" "256 4 64"; do
  set -- $cfg
  gen ffn_e4m3.py $1 $2 "$O/ffn_e4m3_C$1_R$2.ptx" $3
  gen ffn_e4m3.py $1 $2 "$O/ffn_e4m3_C$1_R$2_proj.ptx" $3 1
done
for cfg in "4096 1 32 4" "1024 0 16 2" "1024 1 8 4" "1024 0 8 4"; do
  set -- $cfg; gen gemmt_e4m3.py $1 $2 $3 $4 "$O/gemmt_e4m3_K$1_f$2_p$3_s$4.ptx"
done
for cfg in "4 4" "2 8" "4 8"; do set -- $cfg; gen reduce_e4m3.py $1 $2 "$O/reduce_e4m3_s$1_f$2.ptx"; done
for cfg in "1024 6 1" "4096 5 4" "1024 8 2" "1024 5 4"; do
  set -- $cfg
  gen gemmv_e4m3.py $1 $2 $3 "$O/gemmv_e4m3_K$1_f$2_s$3.ptx"
  gen gemmv_e4m3.py $1 $2 $3 "$O/gemmv_e4m3_K$1_f$2_s$3_m96.ptx" 4 6 0 0 0 96
done
for p in 64 128 192 256; do gen global_attention_e4m3.py $p "$O/global_attention_e4m3_p$p.ptx"; done
gen global_attention_stream_e4m3.py normalize "$O/global_normalize_e4m3.ptx"
gen global_attention_stream_e4m3.py attention "$O/global_attention_stream_e4m3.ptx" 4
for cfg in "512 4" "512 5" "512 13" "256 5" "4096 5" "1024 8" "1024 5"; do
  set -- $cfg; gen gemmv_e4m3.py $1 $2 1 "$O/gemmv_e4m3_K$1_f$2_s1_m96.ptx" 4 6 0 0 0 96
done
for f in 2 66 74 130 48; do gen block32_e4m3.py $f "$O/block32_e4m3_f$f.ptx"; done
echo "PTX: $(ls "$O"/*.ptx | wc -l) kernels in $O"
