#!/usr/bin/env python3
"""全站词条结构核对：
1. 残留模板/占位符/转义泄露
2. frontmatter 完整性
3. 内链 slug 有效性
4. 正文句子 vs TextMap 官方原文抽样比对（书籍+任务）
"""
import os, re, json, glob, random, sys

ROOT = "/workspace/寰宇全事/docs"
TM = "/workspace/寰宇全事/raw/gamedata/TextMapCHS.json"

issues = []

# ---------- 1. 残留扫描 ----------
pat_residue = re.compile(r"\{\{|\}\}|<color=|<size=|<unbreak>|&nbsp;|&#\d+;")
for path in glob.glob(ROOT + "/**/*.md", recursive=True):
    rel = os.path.relpath(path, ROOT)
    if rel.startswith("emoji") or "/.vitepress" in rel:
        continue
    text = open(path, encoding="utf-8").read()
    for m in pat_residue.finditer(text):
        ctx = text[max(0, m.start()-40):m.end()+40].replace("\n", " ")
        issues.append(f"[残留] {rel}: …{ctx}…")

# ---------- 2. frontmatter 完整性 ----------
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
def simple_fields(fm):
    # 粗提取 title/type/summary 是否存在（数组字段不算）
    return {k: bool(re.search(rf"^\s*{k}:", fm, re.M)) for k in ("title", "type", "summary", "tags")}

ENTRY_DIRS = ("characters", "factions", "locations", "concepts", "events", "items", "books")
for d in ENTRY_DIRS:
    for path in glob.glob(f"{ROOT}/{d}/**/*.md", recursive=True):
        rel = os.path.relpath(path, ROOT)
        if rel.endswith("index.md"):
            continue
        text = open(path, encoding="utf-8").read()
        m = FM_RE.match(text)
        if not m:
            issues.append(f"[frontmatter] {rel}: 缺 frontmatter")
            continue
        fm = m.group(1)
        miss = [k for k, ok in simple_fields(fm).items() if not ok]
        if miss:
            issues.append(f"[frontmatter] {rel}: 缺 {','.join(miss)}")

# ---------- 3. 内链有效性 ----------
all_paths = set()
for path in glob.glob(ROOT + "/**/*.md", recursive=True):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    if rel.endswith("index.md"):
        rel = rel[:-8]
    else:
        rel = rel[:-3]
    all_paths.add("/" + rel)

LINK_RE = re.compile(r"\]\((/[^)#\s]+)(?:#[^)]*)?\)")
link_fail = {}
for path in glob.glob(ROOT + "/**/*.md", recursive=True):
    rel = os.path.relpath(path, ROOT)
    if "/.vitepress" in rel:
        continue
    text = open(path, encoding="utf-8").read()
    for m in LINK_RE.finditer(text):
        target = m.group(1)
        if target.startswith("//") or target.startswith("/huanyu"):
            continue
        if target not in all_paths:
            link_fail.setdefault(target, []).append(rel)
for t, srcs in sorted(link_fail.items()):
    issues.append(f"[死链] {t} <- " + ",".join(sorted(set(srcs))[:3]) + (f" 等{len(srcs)}处" if len(srcs) > 3 else ""))

# ---------- 4. 正文 vs TextMap 抽样 ----------
print("加载 TextMap…")
tm_raw = json.load(open(TM, encoding="utf-8"))

def clean_official(t):
    t = re.sub(r"<color=#\w+>|</color>|<unbreak>|</unbreak>|<nobr>|</nobr>|<size=\d+>|</size>", "", t)
    t = t.replace("\\n", "\n")
    return t

tm_texts = [clean_official(v) for v in tm_raw.values() if len(v) >= 30]
# 归一化：去空白，统一省略号/引号/破折号
PUNCT = (
    " \n\t\u3000"
    "。．，、；：？!"
    "\uff02\uff07\uff08\uff09"
    "\u201c\u201d\u2018\u2019"
    "（）()《》〈〉「」『』【】"
    "…·⋯—～~-―,.:;?!"
)
def normalize(s):
    s = s.replace("⋯", "…").replace("。。。。。。", "……").replace("。。。", "…")
    for p in PUNCT:
        s = s.replace(p, "")
    return s

tm_norm_set = None  # 惰性建
def build_index():
    global tm_norm_set
    tm_norm_set = set()
    for t in tm_texts:
        tm_norm_set.add(normalize(t))

# 抽样对象：书籍分卷正文 + 任务对话
def iter_samples():
    for path in glob.glob(f"{ROOT}/books/*.md"):
        if path.endswith("index.md"):
            continue
        text = open(path, encoding="utf-8").read()
        paras = [p.strip() for p in text.split("\n") if len(p.strip()) >= 40 and not p.startswith((">", "#", "-", "|", "{{", "```"))]
        if paras:
            yield os.path.basename(path), random.choice(paras)

def find_sentence(par, minlen=20):
    # 从段落里取一段 20~40 字的连续片段（去标点后长度）
    norm = normalize(par)
    if len(norm) < minlen:
        return None
    start = random.randint(0, max(0, len(norm) - 30))
    return norm[start:start + 25]

random.seed(20261124)
build_index()
books_total, books_hit = 0, 0
misses = []
for name, par in iter_samples():
    frag = find_sentence(par)
    if not frag:
        continue
    books_total += 1
    if frag in tm_norm_set:
        books_hit += 1
    else:
        misses.append((name, frag))

print(f"\n书籍正文抽样比对：{books_hit}/{books_total} 命中官方文本库")
if misses:
    print("未命中样本（人工复核）：")
    for n, f in misses[:12]:
        print(f"  {n}: {f[:30]}")

# ---------- 汇总 ----------
print(f"\n===== 结构问题 {len(issues)} 项 =====")
by_kind = {}
for i in issues:
    kind = i[1:i.index("]")]
    by_kind.setdefault(kind, []).append(i)
for kind, lst in by_kind.items():
    print(f"\n[{kind}] {len(lst)} 项")
    for i in lst[:15]:
        print("  " + i)
    if len(lst) > 15:
        print(f"  …还有 {len(lst)-15} 项")
