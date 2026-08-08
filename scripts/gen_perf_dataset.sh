#!/bin/bash
# Generate a synthetic dataset for scanner performance testing.
#
# Usage: ./gen_perf_dataset.sh [small|medium|large] [output_dir]
#   small  -> 100,000 files  (~100 MB, default)
#   medium -> 1,000,000 files (~1 GB)
#   large  -> 5,000,000 files (~5 GB)
#
# Each file is 1 KB of random data, organized 10 per directory. This is a
# Linux-oriented helper (uses /dev/urandom, head, seq). Perf validation is
# expected to run on Linux; the perf test itself (test_perf.cpp) skips when
# DISKVIZ_PERF_DIR is unset.
SIZE=${1:-small}
OUT=${2:-/tmp/diskviz-perf}
rm -rf "$OUT"
mkdir -p "$OUT"
case "$SIZE" in
    small)  TOTAL=100000;;
    medium) TOTAL=1000000;;
    large)  TOTAL=5000000;;
    *) echo "Unknown size: $SIZE (use small|medium|large)"; exit 1;;
esac
DIRS=$((TOTAL / 10))
for i in $(seq 1 "$DIRS"); do
    d="$OUT/dir$((i / 100))"
    mkdir -p "$d"
    for j in 1 2 3 4 5 6 7 8 9 10; do
        head -c 1024 /dev/urandom > "$d/file${i}_${j}.bin"
    done
done
echo "Generated $TOTAL files under $OUT"
