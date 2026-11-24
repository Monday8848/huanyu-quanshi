#!/usr/bin/env python3
"""
harvest_books.py — 从 raw/bwiki 的 BWIKI 书籍页生成 docs/books/*.md

输入：raw/bwiki/<标题>.txt（文件以 {{书籍 / {{书籍2 模板开头的页面）
输出：docs/books/<slug>.md，frontmatter 含 title/summary/aliases/tags/location/kind

用法：
    python3 scripts/harvest_books.py            # 全量生成
    python3 scripts/harvest_books.py --sample   # 只生成样书（验收用）
    python3 scripts/harvest_books.py --force A B # 只生成指定标题的页面

设计要点：
  - 模板解析用括号深度扫描，正确处理嵌套 {{}} 与参数内的 |、换行
  - wikitext → markdown 转换覆盖：br/b/i/s/u/font/span/center/p/tabber/ref、
    {{注音}}→ruby、{{颜色}}/{{图标}}/{{#info:}}→纯文字、{{黑幕}}→heimu span、
    {{划掉重说}}→删除线+改口、{{切换板}}→小节标题、[[链接]]→纯文字（站内链交给 auto-link）
  - slug 用清洗后的中文标题；冲突自动加后缀并告警
"""
import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'raw' / 'bwiki'
OUT = ROOT / 'docs' / 'books'

REGION = {
    '1': '空间站「黑塔」',
    '2': '雅利洛-Ⅵ',
    '3': '仙舟「罗浮」',
    '4': '匹诺康尼',
    '5': '翁法罗斯',
    '6': '二相乐园',
}

# BWIKI 类型 → 站内「文体」标签（13 种归并为 7 组，供侧栏分组）
KIND = {
    '书籍': '书籍',
    '资料': '资料',
    '信件': '信件', '信件2': '信件',
    '便条': '便条', '留言': '便条',
    '磁带': '音像', '卡带': '音像', '录像带': '音像',
    '石碑': '石碑铭刻', '拓印': '石碑铭刻', '如意': '石碑铭刻',
    '回响': '回响寄语', '寄语': '回响寄语',
}

COPYRIGHT_NOTE = (
    '> 原文出自《崩坏：星穹铁道》游戏内阅读物，文字版权归米哈游所有。'
    '本页据 BWIKI 转录文本整理，仅供学习研究，未经许可请勿用于商业用途。'
)

FOOTNOTE_RE = re.compile(r'<ref[^>/]*>(.*?)</ref>|<ref[^>]*/>', re.S | re.I)

warnings_log = []


def warn(msg):
    warnings_log.append(msg)


# ---------------------------------------------------------------- 模板解析

def parse_template(text, pos):
    """从 text[pos] == '{' 开始解析一个 {{...}} 模板。

    返回 (params, end)：params[0] 是模板名，其余按「名称=值」或纯值存放；
    end 指向模板结束 '}}' 之后。解析失败返回 (None, pos)。
    """
    n = len(text)
    if not text.startswith('{{', pos):
        return None, pos
    depth = 0
    i = pos
    parts = []          # 顶层参数切片 [(start, end)]
    seg_start = None    # 当前参数内容起点（越过 '{{' 与顶层 '|' 之后）

    while i < n:
        if text.startswith('{{', i):
            if depth == 0 and seg_start is None:
                seg_start = i + 2
            depth += 1
            i += 2
            continue
        if text.startswith('}}', i):
            depth -= 1
            if depth == 0:
                if seg_start is not None:
                    parts.append((seg_start, i))
                return parts, i + 2
            i += 2
            continue
        if depth == 1 and text[i] == '|' and seg_start is not None:
            # 跳过 tabber 分隔符 |-| 中的竖线（内容参数里的 MediaWiki 语法）
            if text[i + 1:i + 2] == '-' or text[i - 1:i] == '-':
                i += 1
                continue
            parts.append((seg_start, i))
            seg_start = i + 1
        elif depth == 0 and text[i] == '|' and seg_start is None:
            # 模板名后的第一个 |
            seg_start = i + 1
        i += 1
    return None, pos


def split_param(raw):
    """把一个参数切片拆成 (name, value)。无名参数 name 为 None。"""
    raw = raw.strip()
    m = re.match(r'^([^=|]{1,30}?)\s*=\s*(.*)$', raw, re.S)
    if m and m.group(1).strip():
        return m.group(1).strip(), m.group(2).strip()
    return None, raw


def parse_book_page(text):
    """解析整页。返回 (meta, volumes)；meta 为 None 表示不是书籍页。"""
    text = re.sub(r'<!--.*?-->', '', text)
    # 找主模板：{{书籍 / {{书籍2（允许模板名前有空行）
    m = re.match(r'^\{\{\s*\n?(书籍2?|书籍)\s*\n', text)
    if not m:
        return None, []
    params, end = parse_template(text, 0)
    if not params:
        warn(f'主模板解析失败: {text[:40]!r}')
        return None, []

    meta = {}
    inline_volumes = []  # 书籍2 的内联分卷参数
    for (a, b) in params[1:]:
        name, value = split_param(text[a:b])
        if name is None:
            continue
        mv = re.match(r'^分卷(\d+)(名称|获取方式|内容)$', name)
        if mv:
            inline_volumes.append((int(mv.group(1)), mv.group(2), value))
        else:
            meta[name] = value

    volumes = []
    # 逐个解析 {{书籍/分卷}}
    idx = text.find('{{书籍/分卷', end)
    while idx != -1:
        vparams, vend = parse_template(text, idx)
        if not vparams:
            warn(f'分卷模板解析失败 @ {idx}')
            break
        vol = {}
        for (a, b) in vparams[1:]:
            name, value = split_param(text[a:b])
            if name:
                vol[name] = value
        volumes.append(vol)
        idx = text.find('{{书籍/分卷', vend)

    # 书籍2 的内联分卷
    if inline_volumes and not volumes:
        by_no = {}
        for no, key, value in inline_volumes:
            by_no.setdefault(no, {})[key] = value
        volumes = [by_no[k] for k in sorted(by_no)]

    return meta, volumes


# ---------------------------------------------------------------- 内容转换

def replace_simple_templates(text):
    """单行模板 → markdown。按已知集合逐一处理，其余原样保留并告警。"""

    def sub_pattern(pattern, repl):
        nonlocal text
        text = re.sub(pattern, repl, text, flags=re.S)

    # 注音 → 占位符（ruby，转 HTML 后还原，避免被标签兜底误伤）
    sub_pattern(r'\{\{注音\s*\|([^|{}]*)\|([^{}]*)\}\}', '\x03\\1\x04\\2\x05')
    # 颜色 → 纯文字（参数1 色号，参数2 文字；也可能只有一段文字）
    sub_pattern(r'\{\{颜色\s*\|[^|{}]+\|([^{}]*)\}\}', r'\1')
    sub_pattern(r'\{\{颜色\s*\|([^|{}]*)\}\}', r'\1')
    # 图标 → 图标名
    sub_pattern(r'\{\{图标\s*\|([^|{}]*)[^{}]*\}\}', r'\1')
    # #info: 悬停注释 → 括号小注
    sub_pattern(r'\{\{#info:([^{}]*)\}\}', r'（\1）')
    # 黑幕 → 占位符（剧透遮罩；转 HTML 后还原，避免被 span 剥壳误伤）
    sub_pattern(r'\{\{黑幕\s*\|([^{}]*)\}\}', '\x01\\1\x02')
    sub_pattern(r'\{\{划掉重说\s*\|([^|{}]*)\|([^{}]*)\}\}', r'~~\1~~ \2')
    # 提示（BWIKI 编者提示，非原文）→ 删除
    sub_pattern(r'\{\{提示\s*\|[^{}]*\}\}', '')
    # 切换板：分支标题转小节，结构标记删除
    sub_pattern(r'\{\{切换板\s*\|[^|}]*\|([^{}]*)\}\}', r'\n\n#### \1\n\n')
    sub_pattern(r'\{\{切换板\s*\|(?:开始|结束|显示内容|内容结束|折叠内容)\s*\}\}', '\n')
    # MediaWiki 等号转义模板
    sub_pattern(r'\{\{=\}\}', '=')
    # 残留的空模板与裸模板兜底告警
    for m in re.finditer(r'\{\{([^{}]*)\}\}', text):
        warn(f'未识别模板残留: {m.group(0)[:60]!r}')
    return text


def convert_html(text):
    # wikitext 粗体/斜体最先处理，避免与 <center> 的 ** 包裹叠加出 ****
    text = re.sub(r"'''([^']+?)'''", r'**\1**', text)
    text = re.sub(r"''([^']+?)''", r'*\1*', text)

    # tabber → 多个小节
    def tabber_repl(m):
        body = m.group(1)
        chunks = re.split(r'\|-', body)
        out = []
        for c in chunks:
            c = c.strip().strip('|').strip()
            if '=' in c:
                name, _, content = c.partition('=')
                out.append(f'\n\n#### {name.strip()}\n\n{content.strip()}')
            elif c:
                out.append('\n\n' + c)
        return '\n'.join(out)

    text = re.sub(r'<tabber[^>]*>(.*?)</tabber>', tabber_repl, text, flags=re.S)
    text = re.sub(r'<references\s*/?>', '', text, flags=re.I)

    # ref 编者注 → 内联括号（VitePress 未启用脚注插件）
    text = FOOTNOTE_RE.sub(
        lambda m: f'（编者注：{m.group(1).strip()}）' if m.group(1) else '', text)

    # center → 粗体行（内容已是粗体则只包裹换行，避免 ****）
    def center_repl(m):
        inner = m.group(1).strip()
        if not inner:
            return ''
        if inner.startswith('**') and inner.endswith('**'):
            return f'\n\n{inner}\n\n'
        return f'\n\n**{inner}**\n\n'
    text = re.sub(r'<center[^>]*>(.*?)</center>', center_repl, text, flags=re.S | re.I)

    # 字符级替换
    text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.S | re.I)
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.S | re.I)
    text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.S | re.I)
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.S | re.I)
    text = re.sub(r'<s[^>]*>(.*?)</s>', r'~~\1~~', text, flags=re.S | re.I)
    text = re.sub(r'<del[^>]*>(.*?)</del>', r'~~\1~~', text, flags=re.S | re.I)
    text = re.sub(r'<strike[^>]*>(.*?)</strike>', r'~~\1~~', text, flags=re.S | re.I)
    # u / font / span / div / p / nowiki：剥壳保文字
    text = re.sub(r'</?(u|font|span|div|p|nowiki)(\s[^>]*)?/?>', '', text, flags=re.I)
    # 残余闭合标签兜底
    text = re.sub(r'</?[a-zA-Z][^>]*>', '', text)

    # 换行与实体
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')

    # 内链 → 纯文字（站内词条链接交给 auto-link 处理）
    text = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    # BWIKI 侧偶有未闭合的 [[，兜底剥壳
    text = re.sub(r'\[\[([^\]]*)', r'\1', text)

    # 列表与水平线
    text = re.sub(r'(?m)^\*\s+', '- ', text)
    text = re.sub(r'(?m)^-{4,}\s*$', '\n---\n', text)

    # 还原黑幕与注音占位符（在所有标签处理之后）
    text = text.replace('\x01', '<span class="heimu">').replace('\x02', '</span>')
    text = (text.replace('\x03', '<ruby>')
                .replace('\x04', '<rt>')
                .replace('\x05', '</rt></ruby>'))

    # 压缩空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def convert_content(text):
    text = replace_simple_templates(text)
    text = convert_html(text)
    return text


# ---------------------------------------------------------------- 页面生成

def make_slug(title):
    s = re.sub(r'[《》「」]', '', title.strip())
    for bad in '/\\:*?"<>|':
        s = s.replace(bad, '_')
    s = s.replace('*', '_').strip().strip('.')
    return s


def frontmatter(meta, tags_loc, tags_kind, aliases):
    lines = ['---']
    lines.append(f'title: >-\n      {meta["书籍名"]}')
    desc = meta.get('描述', '')
    if desc:
        desc_flat = desc.replace('\n', ' ')
        lines.append(f'summary: >-\n      {desc_flat}')
    lines.append('type: book')
    if aliases:
        lines.append('aliases:')
        for a in aliases:
            lines.append(f'  - >-\n      {a}')
    lines.append('tags:')
    lines.append('  location:')
    for t in tags_loc:
        lines.append(f'    - >-\n      {t}')
    lines.append('  kind:')
    for t in tags_kind:
        lines.append(f'    - >-\n      {t}')
    if meta.get('编号'):
        lines.append(f'bookNo: "{meta["编号"]}"')
    if meta.get('实装版本'):
        lines.append(f'version: "{meta["实装版本"]}"')
    lines.append('---')
    return '\n'.join(lines)


def build_volume_section(vol, index, single):
    name = (vol.get('名称') or '').strip() or f'第{index + 1}卷'
    obtain = convert_content(vol.get('获取方式') or '')
    content = convert_content(vol.get('内容') or '')
    head = name if not single else '全文'
    out = [f'\n## {head}\n']
    if obtain:
        out.append(f'> 获得方式：{obtain}\n')
    if content:
        out.append(content)
    else:
        warn(f'分卷「{name}」无内容')
    return '\n'.join(out)


def build_page(meta, volumes, page_title):
    title = meta.get('书籍名') or page_title
    desc = convert_content(meta.get('描述') or '')
    region = REGION.get(meta.get('所属', '').strip()) or '其他'
    kind_raw = re.sub(r'<!--.*?-->', '', meta.get('类型', '')).strip()
    kind = KIND.get(kind_raw, kind_raw or '其他')

    tags_loc = [region] if region else []
    tags_kind = [kind] if kind and kind != '其他' else []

    # aliases：系列名（冒号/间隔号前缀）+ 剥书名号变体
    aliases = []
    bare = title.strip('《》')
    if bare != title:
        aliases.append(bare)
    m = re.match(r'^([^\uFF1A:·]{3,})[\uFF1A:·]', bare)
    if m and m.group(1) not in aliases:
        aliases.append(m.group(1))

    single = len(volumes) == 1
    parts = [frontmatter(meta, tags_loc, tags_kind, aliases), '']
    parts.append(f'# {title}\n')
    if desc:
        parts.append(f'> {desc}\n')

    parts.append('\n## 基本信息\n')
    rows = ['| 项目 | 内容 |', '|------|------|']
    rows.append(f'| 文体 | {kind} |')
    if region:
        rows.append(f'| 所属 | {region} |')
    if meta.get('实装版本'):
        rows.append(f'| 实装版本 | {meta["实装版本"]} |')
    if meta.get('编号'):
        rows.append(f'| 游戏内编号 | {meta["编号"]} |')
    parts.append('\n'.join(rows) + '\n')

    for i, vol in enumerate(volumes):
        parts.append(build_volume_section(vol, i, single))

    parts.append('\n---\n')
    parts.append(COPYRIGHT_NOTE + '\n')

    page = '\n'.join(parts)
    return page, title


# ---------------------------------------------------------------- 主流程

def find_book_files():
    files = []
    for fn in sorted(RAW.iterdir()):
        if not fn.name.endswith('.txt'):
            continue
        try:
            head = fn.read_text(encoding='utf-8')[:80]
        except Exception:
            continue
        if re.match(r'^\{\{\s*\n?书籍2?\s*\n', head):
            files.append(fn)
    return files


def main():
    sample = '--sample' in sys.argv
    force_titles = []
    if '--force' in sys.argv:
        i = sys.argv.index('--force')
        force_titles = sys.argv[i + 1:]

    OUT.mkdir(exist_ok=True)
    # 清理上一次生成的词条文件（保留手写的 index.md）
    for old in OUT.glob('*.md'):
        if old.name != 'index.md':
            old.unlink()
    files = find_book_files()
    print(f'[harvest] 发现书籍页 {len(files)} 个')

    used_slugs = {}
    generated = []
    for fn in files:
        page_title = fn.stem.replace('_', '*') if fn.stem.startswith('_') else fn.stem
        # raw 下载时 * 被替换成 _，还原回标题用于展示（仅当标题以 _ 开头命中已知替换）
        text = fn.read_text(encoding='utf-8')
        meta, volumes = parse_book_page(text)
        if meta is None:
            continue
        raw_title = meta.get('书籍名') or page_title
        # 占位页（书籍名为空，游戏内书籍必有名）跳过
        if not (meta.get('书籍名') or '').strip():
            continue

        if sample:
            if raw_title not in SAMPLE_BOOKS:
                continue
        if force_titles and raw_title not in force_titles:
            continue

        page, title = build_page(meta, volumes, page_title)
        slug = make_slug(title)
        if slug in used_slugs:
            warn(f'slug 冲突: {slug}（{used_slugs[slug]} vs {raw_title}）')
            slug = f'{slug}-{len(used_slugs)}'
        used_slugs[slug] = raw_title
        (OUT / f'{slug}.md').write_text(page, encoding='utf-8')
        generated.append(title)

    print(f'[harvest] 生成 {len(generated)} 个词条')
    if warnings_log:
        uniq = {}
        for w in warnings_log:
            uniq[w] = uniq.get(w, 0) + 1
        print(f'[harvest] 警告 {len(warnings_log)} 条（去重 {len(uniq)} 类）:')
        for w, c in list(uniq.items())[:30]:
            print(f'  [{c}x] {w}')


SAMPLE_BOOKS = {
    '大敌名录',
    '折纸大学七大不可思议',
    '《梦境旅游指南-交通篇》',
    '欢迎来到■■■■',
    '《布鲁斯之夜》宣传单',
    '神性的回响：大地',
    '一页寄语：阿格莱雅',
    '《仙舟通鉴》拾遗',
    '《美梦往事外传》',
    '寄给咪发迷的信',
    '二相乐园剧情阅读物',
}

if __name__ == '__main__':
    main()
