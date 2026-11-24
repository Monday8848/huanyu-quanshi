#!/bin/bash
# 并行分块下载 TextMapCHS.json（2MB/块，6路并行，每块最长10分钟）
TOTAL=54499453
CHUNK=2097152
URL="https://raw.githubusercontent.com/DimbreathBot/TurnBasedGameData/main/TextMap/TextMapCHS.json"
N=$(( (TOTAL + CHUNK - 1) / CHUNK ))
dl_chunk() {
  i=$1
  start=$(( i * CHUNK ))
  end=$(( start + CHUNK - 1 ))
  [ $end -ge $TOTAL ] && end=$(( TOTAL - 1 ))
  exp=$(( end - start + 1 ))
  f=$(printf "p%05d.bin" $i)
  while true; do
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
    if [ "$sz" -eq "$exp" ]; then break; fi
    curl -s -m 600 --retry 2 -r "${start}-$((start + sz))" -o - "$URL" >> "$f" 2>/dev/null
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
    [ "$sz" -eq "$exp" ] && break
    sleep 2
  done
  echo "chunk $i done ($exp bytes)"
}
export -f dl_chunk
export TOTAL CHUNK URL
seq 0 $((N-1)) | xargs -P 6 -I {} bash -c 'dl_chunk {}'
echo ALL_CHUNKS_DONE
