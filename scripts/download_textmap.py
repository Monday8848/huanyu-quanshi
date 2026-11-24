#!/usr/bin/env python3
"""分块下载 TextMapCHS.json（v2）。
主源 ghfast.top（~178KB/s），备源 api.github.com 匿名（~108KB/s）。
2MB/块，断点续传（块完整则跳过），全部完成后拼接并校验 JSON。"""
import os, sys, json, time, urllib.request

TOTAL = 54499453
CHUNK = 2 * 1024 * 1024  # 2MB
OUT = "TextMapCHS.json"
PARTS = "parts"
SRC_MAIN = "https://ghfast.top/https://raw.githubusercontent.com/DimbreathBot/TurnBasedGameData/main/TextMap/TextMapCHS.json"
SRC_BACK = "https://api.github.com/repos/DimbreathBot/TurnBasedGameData/contents/TextMap/TextMapCHS.json"

def fetch(url, start, end, timeout=90):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
        "Range": f"bytes={start}-{end}",
        "Accept": "application/vnd.github.raw",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def chunk_ok(idx):
    f = os.path.join(PARTS, f"p{idx:05d}.bin")
    expected = min((idx + 1) * CHUNK, TOTAL) - idx * CHUNK
    return os.path.exists(f) and os.path.getsize(f) == expected

def download_chunk(idx):
    start = idx * CHUNK
    expected = min(start + CHUNK, TOTAL) - start
    f = os.path.join(PARTS, f"p{idx:05d}.bin")
    have = os.path.getsize(f) if os.path.exists(f) else 0
    # 续传：从已有字节后接着要
    for attempt in range(8):
        pos = os.path.getsize(f) if os.path.exists(f) else 0
        if pos >= expected:
            break
        src = SRC_MAIN if attempt % 3 != 2 else SRC_BACK
        try:
            data = fetch(src, start + pos, start + expected - 1)
            if not data:
                raise IOError("空响应")
            with open(f, "ab") as out:
                out.write(data)
        except Exception as e:
            print(f"[{idx}] {src.split('/')[2]} @{pos}: {e}，重试{attempt+1}", flush=True)
            time.sleep(2)
    return os.path.getsize(f) == expected

def main():
    os.makedirs(PARTS, exist_ok=True)
    n = (TOTAL + CHUNK - 1) // CHUNK
    t0 = time.time()
    for idx in range(n):
        if chunk_ok(idx):
            continue
        if not download_chunk(idx):
            print(f"块 {idx} 失败，中止", flush=True)
            sys.exit(1)
        done = idx + 1
        speed = done * CHUNK / max(time.time() - t0, 1) / 1024
        eta = (n - done) * CHUNK / max(speed * 1024, 1)
        print(f"进度 {done}/{n} ({done*100//n}%) {speed:.0f}KB/s ETA {eta/60:.0f}分", flush=True)
    # 拼接
    size = 0
    with open(OUT, "wb") as out:
        for idx in range(n):
            with open(os.path.join(PARTS, f"p{idx:05d}.bin"), "rb") as f:
                while True:
                    b = f.read(1 << 20)
                    if not b:
                        break
                    out.write(b)
                    size += len(b)
    print(f"拼接完成: {size} bytes（预期 {TOTAL}）", flush=True)
    if size != TOTAL:
        sys.exit(1)
    with open(OUT, encoding="utf-8") as f:
        d = json.load(f)
    print(f"JSON 校验通过，文本条目数: {len(d)}", flush=True)

if __name__ == "__main__":
    main()
