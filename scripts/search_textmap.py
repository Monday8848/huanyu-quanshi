#!/usr/bin/env python3
"""在游戏内全量中文文本库（TextMapCHS.json）中按关键词检索。
用法:
  python3 scripts/search_textmap.py 关键词1 [关键词2 ...] [--limit N] [--context]
  python3 scripts/search_textmap.py --regex "幻胧|Phantylia" --limit 30
输出: hash 前 8 位 + 清理后的文本（剥离颜色标签）。"""
import json, re, sys, argparse, os

BASE = os.path.join(os.path.dirname(__file__), "..", "raw", "gamedata", "TextMapCHS.json")

def clean(t):
    t = re.sub(r"<color=#\w+>|</color>|<unbreak>|</unbreak>|<nobr>|</nobr>", "", t)
    t = re.sub(r"<size=\d+>|</size>", "", t)
    t = t.replace("\\n", "\n")
    return re.sub(r"\n{3,}", "\n\n", t).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="*")
    ap.add_argument("--regex")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--minlen", type=int, default=4, help="文本最短长度过滤")
    args = ap.parse_args()

    data = json.load(open(BASE, encoding="utf-8"))
    if args.regex:
        pat = re.compile(args.regex)
        hit = lambda t: pat.search(t)
    else:
        kws = args.keywords or ["匹配模式缺失"]
        hit = lambda t: any(k in t for k in kws)

    n = 0
    counts = {}
    for h, t in data.items():
        if len(t) < args.minlen:
            continue
        if hit(t):
            counts[h] = clean(t)
            n += 1
    print(f"命中 {n} 条（显示前 {min(n, args.limit)} 条，全库 {len(data)} 条）\n")
    for h, t in list(counts.items())[: args.limit]:
        print(f"[{h[:8]}] {t[:400]}")
        print("-" * 60)

if __name__ == "__main__":
    main()
