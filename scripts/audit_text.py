#!/usr/bin/env python3
"""书籍 688 页正文 vs TextMap 官方文本库全量比对。

方法：每页取最长的 3 个正文段（确定性），归一化后取 20 字片段，
在 TextMap 全文拼接串中做子串查找。未命中 = 转录可能与官方不一致
（或该篇未进入 TextMap / 版本滞后），输出清单人工复核。
"""
import os, re, json, glob

ROOT = "/workspace/寰宇全事/docs/books"
TM = "/workspace/寰宇全事/raw/gamedata/TextMapCHS.json"

def clean_official(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\\n", "\n")
    # BWIKI 转录会剥掉官方文本中的斜体标记与舞台指示
    t = re.sub(r"/\*|\*/", "", t)
    return t

PUNCT = (
    " \n\t\u3000"
    "。．，、；：?!"
    "\uff02\uff07\uff08\uff09"
    "\u201c\u201d\u2018\u2019"
    "（）()《》〈〉「」『』【】"
    "…·⋯—～~-―,.:;?!\"'"
    "\xa0\u200b/"
)
def norm(s):
    s = s.replace("⋯", "…")
    for p in PUNCT:
        s = s.replace(p, "")
    return s

print("构建 TextMap 拼接索引…")
tm = json.load(open(TM, encoding="utf-8"))
blob_parts = []
for t in tm.values():
    if len(t) < 20:
        continue
    blob_parts.append(norm(clean_official(t)))
blob = "\x00".join(blob_parts)
print(f"索引大小 {len(blob)//1024//1024}MB")

SKIP_PREFIX = (">", "#", "-", "|", "*", "```", "<", "!", "~")
def body_paras(md):
    # 跳过 frontmatter
    m = re.match(r"^---\n.*?\n---\n", md, re.S)
    body = md[m.end():] if m else md
    paras = []
    for p in body.split("\n\n"):
        p = p.strip()
        if len(p) < 40:
            continue
        if p.startswith(SKIP_PREFIX):
            continue
        # 剥 HTML 标签（heimu/ruby 等）与强调符号
        p = re.sub(r"<[^>]+>", "", p)
        p = p.replace("*", "")
        paras.append(p)
    return paras

total_page, ok_page = 0, 0
misses = []
for path in sorted(glob.glob(ROOT + "/*.md")):
    if path.endswith("index.md"):
        continue
    total_page += 1
    md = open(path, encoding="utf-8").read()
    paras = sorted(body_paras(md), key=len, reverse=True)[:3]
    if not paras:
        continue
    page_hit = False
    page_miss = []
    for p in paras:
        np = norm(p)
        if len(np) < 25:
            continue
        frag = np[10:30]  # 避开段首边缘
        if frag in blob:
            page_hit = True
        else:
            page_miss.append(p[:50])
    if page_hit:
        ok_page += 1
    else:
        misses.append((os.path.basename(path), page_miss))

print(f"\n比对结果：{ok_page}/{total_page} 页至少命中 1 段官方文本")
print(f"未命中页 {len(misses)} 页（人工复核）：")
for name, frags in misses[:40]:
    print(f"  {name}")
    for f in frags[:1]:
        print(f"      {f}")
if len(misses) > 40:
    print(f"  …还有 {len(misses)-40} 页")
