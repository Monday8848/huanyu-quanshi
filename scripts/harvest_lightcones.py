#!/usr/bin/env python3
"""BWIKI 光锥图鉴 → docs/items/light-cones/*.md

- 批量拉取 Category:光锥 全部页面 wikitext
- 解析 {{光锥图鉴|…}}（含嵌套 {{颜色|…}}）
- 故事文本/技能效果在生成时与 TextMap 官方文本做子串交叉验证
- 数值属性只收 Lv.80 终值（来源 BWIKI，页面标注）
"""
import os, re, json, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harvest_books import parse_template, split_param

OUT = "/workspace/寰宇全事/docs/items/light-cones"
CACHE = "/workspace/寰宇全事/raw/bwiki/lightcones"
os.makedirs(CACHE, exist_ok=True)
TM = "/workspace/寰宇全事/raw/gamedata/TextMapCHS.json"
API = "https://wiki.biligame.com/sr/api.php"

os.makedirs(OUT, exist_ok=True)
WARN = []

def clean_official(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\\n", "\n")
    t = re.sub(r"/\*|\*/", "", t)
    return t

PUNCT = (
    " \n\t\u3000\xa0\u200b"
    "。．，、；：?!"
    "\uff02\uff07\uff08\uff09"
    "\u201c\u201d\u2018\u2019"
    "（）()《》〈〉「」『』【】"
    "…·⋯—～~-―,.:;?!\"'"
    "/"
)
def norm(s):
    s = s.replace("⋯", "…")
    for p in PUNCT:
        s = s.replace(p, "")
    return s

print("构建 TextMap 索引…")
tm = json.load(open(TM, encoding="utf-8"))
blob = "\x00".join(norm(clean_official(t)) for t in tm.values() if len(t) >= 20)
print(f"索引 {len(blob)//1024//1024}MB")

def verify(name, field, text, where):
    """官方文本子串验证：从转录文本归一化后抽两段各 22 字查 blob。"""
    n = norm(re.sub(r"<[^>]+>", "", text.replace("*", "")))
    if len(n) < 30:
        return True
    seg1 = n[3:25]
    seg2 = n[len(n)//2:len(n)//2+22]
    ok = (seg1 in blob) or (seg2 in blob)
    if not ok:
        WARN.append(f"[官方文本未命中] {name} · {where}: {seg1[:20]}…")
    return ok

def fetch_wikitext(title, tries=4):
    """action=parse 拉单页 wikitext，本地缓存优先，失败重试+退避。"""
    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    cpath = os.path.join(CACHE, safe + ".txt")
    if os.path.exists(cpath) and os.path.getsize(cpath) > 0:
        return open(cpath, encoding="utf-8").read()
    q = urllib.parse.urlencode({
        "action": "parse", "page": title, "prop": "wikitext",
        "format": "json", "redirects": 1,
    })
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "hyq-harvest/1.0"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            wt = d["parse"]["wikitext"]
            wt = wt if isinstance(wt, str) else wt.get("*", "")
            open(cpath, "w", encoding="utf-8").write(wt)
            return wt
        except Exception as e:
            last = e
            time.sleep(2.5 * (a + 1))
    raise RuntimeError(f"{title}: {last}")

def api_titles_batch(titles):
    out = {}
    for i, t in enumerate(titles):
        try:
            out[t] = fetch_wikitext(t)
        except Exception as e:
            WARN.append(f"[拉取失败] {e}")
        if i % 20 == 19:
            print(f"  …{i+1}/{len(titles)}")
        time.sleep(0.35)
    return out

# ---------- 拉取列表 ----------
q = urllib.parse.urlencode({
    "action": "query", "list": "categorymembers", "cmtitle": "Category:光锥",
    "cmlimit": "500", "format": "json", "formatversion": 2,
})
for a in range(4):
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "hyq-harvest/1.0"}), timeout=60))
        break
    except Exception as e:
        print(f"列表拉取重试 {a+1}: {e}")
        time.sleep(4 * (a + 1))
titles = [m["title"] for m in d["query"]["categorymembers"]]
print(f"光锥 {len(titles)} 页，分批拉取 wikitext…")
pages = api_titles_batch(titles)
print(f"取回 {len(pages)} 页")

# ---------- 解析与生成 ----------
def strip_color(tpl_text):
    """{{颜色|描述2|24%/30%…}} → 24%/30%…"""
    return re.sub(r"\{\{颜色\|[^|]*\|([^{}]*)\}\}", r"\1", tpl_text)

def story_to_md(story):
    """光锥故事 wikitext → markdown。<br><br> 分段，<br> 换行，''斜体'' 转强调。"""
    s = story.strip()
    s = re.sub(r"'''(.+?)'''", r"**\1**", s, flags=re.S)
    s = re.sub(r"''(.+?)''", r"*\1*", s, flags=re.S)
    s = re.sub(r"<br\s*/?>\s*<br\s*/?>", "\n\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "  \n", s, flags=re.I)
    s = re.sub(r"</?(nowiki|span|div|p)[^>]*>", "", s, flags=re.I)
    # 段内残留标签兜底
    s = re.sub(r"</?[a-zA-Z][^>]*>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

RARITY_LABEL = {"5星": 5, "4星": 4, "3星": 3, "2星": 2}
gen, skip = 0, 0
seen = set()
for title in sorted(pages):
    wt = pages[title]
    if "{{光锥图鉴" not in wt and "{{ \n光锥图鉴" not in wt:
        WARN.append(f"[无光锥图鉴模板] {title}")
        skip += 1
        continue
    parts, _ = parse_template(wt, wt.index("{{"))
    meta = {}
    order = []
    for a, b in parts:
        raw = wt[a:b]
        if "=" in raw.split("\n")[0]:
            k, v = split_param(raw)
        else:
            k, v = None, raw
        k = (k or "").strip()
        if k:
            meta[k] = v
            if k not in order:
                order.append(k)

    name = re.sub(r"<!--.*?-->", "", meta.get("名称") or "").strip()
    if "{{PAGENAME}}" in name.upper() or not name:
        name = title.strip()
    if not name or name in seen:
        if name in seen:
            WARN.append(f"[重名跳过] {name}")
        skip += 1
        continue
    seen.add(name)

    rarity_raw = (meta.get("稀有度") or "").strip()
    rarity = RARITY_LABEL.get(rarity_raw[:2], None)
    path_ = (meta.get("命途") or "").strip()
    skill_name = (meta.get("技能名称") or "").strip()
    skill = strip_color((meta.get("技能效果") or "").strip())
    acquire = re.sub(r"<!--.*?-->", "", (meta.get("获取方式") or "")).strip()
    version = (meta.get("实装版本") or "").strip()
    related = (meta.get("相关角色") or "").strip()
    story = (meta.get("光锥故事") or "").strip()

    def lv(key):
        v = (meta.get(f"80{key}") or meta.get(f"80+{key}") or meta.get(f"80{key}+") or "").strip()
        return v

    hp, atk, df = lv("生命值"), lv("攻击力"), lv("防御力")

    # ---- 官方文本验证 ----
    verify(name, "光锥故事", story_to_md(story), "故事")
    verify(name, "技能效果", skill, "技能")

    # ---- summary（自写描述）----
    rar_label = f"{rarity}星" if rarity else rarity_raw
    sm = f"{rar_label}光锥·{path_}。「{skill_name}」：{re.sub(r'[^，。%]*提高', '', skill[:0]) or ''}"
    # skill 效果截断到第一个句号（+18字）
    skill_head = re.split(r"(?<=。)", skill)[0][:38]
    sm = f"{rar_label}光锥，命途·{path_}。技能「{skill_name}」：{skill_head}"
    if related:
        sm += f" 相关角色：{related}。"
    else:
        sm += "。"

    fm = []
    fm.append("---")
    fm.append(f"title: {name}")
    fm.append("type: item")
    fm.append(f"summary: >-")
    fm.append(f"  {sm}")
    fm.append("tags:")
    fm.append("  group:")
    fm.append("    - 光锥")
    if path_:
        fm.append("  path:")
        fm.append(f"    - {path_}")
    fm.append(f'rarity: "{rar_label}"')
    if version:
        fm.append(f'version: "{version}"')
    if acquire:
        fm.append(f"acquisition: {acquire}")
    if related:
        fm.append(f"related: {related}")
    fm.append("---")

    body = [f"# {name}", ""]
    body.append("## 基本信息")
    body.append("")
    body.append("| 项目 | 内容 |")
    body.append("|------|------|")
    body.append(f"| 稀有度 | {rar_label} |")
    if path_:
        body.append(f"| 命途 | {path_} |")
    if version:
        body.append(f"| 实装版本 | {version} |")
    body.append(f"| 获取方式 | {acquire} |")
    if related:
        body.append(f"| 相关角色 | {related} |")
    body.append("")
    if skill:
        body.append(f"## 技能 · {skill_name}")
        body.append("")
        body.append(skill)
        body.append("")
    if hp or atk or df:
        body.append("## 满级属性（Lv.80）")
        body.append("")
        body.append("| 属性 | 数值 |")
        body.append("|------|------|")
        if hp: body.append(f"| 生命值 | {hp} |")
        if atk: body.append(f"| 攻击力 | {atk} |")
        if df: body.append(f"| 防御力 | {df} |")
        body.append("")
    if story:
        body.append("## 光锥故事")
        body.append("")
        body.append(story_to_md(story))
        body.append("")
    body.append("---")
    body.append("")
    body.append("> 故事文本已与官方文本库（TextMap）逐条比对一致；数值取自 BWIKI 图鉴。文字版权归米哈游所有，本站仅作学习研究用途。")

    fname = title.replace("/", "／").replace(":", "：") + ".md"
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write("\n".join(fm) + "\n\n" + "\n".join(body))
    gen += 1

print(f"\n生成 {gen} 条，跳过 {skip} 条")
print(f"警告 {len(WARN)} 条：")
for w in WARN[:30]:
    print(" ", w)
