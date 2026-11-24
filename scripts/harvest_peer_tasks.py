#!/usr/bin/env python3
"""同行任务词条生成：从 BWIKI 任务页 raw 解析模板与剧情摘录，生成 docs/events/*.md。

一任务页 = 一词条；「•其一/其二」成对任务合并为一词条分节。
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'raw' / 'bwiki'
OUT = ROOT / 'docs' / 'events'

# 页面名 → 词条名（合并成对任务 / 去掉消歧括号）
MERGE = {
    '难得有情•其一': ('难得有情', ['难得有情•其一', '难得有情•其二']),
}
RENAME = {
    '星核猎手（任务）': '星核猎手',
}

REGION_SHORT = {
    '空间站「黑塔」': '空间站「黑塔」',
    '雅利洛-Ⅵ': '雅利洛-Ⅵ',
    '仙舟「罗浮」': '仙舟「罗浮」',
    '匹诺康尼': '匹诺康尼',
    '星穹列车': '星穹列车',
    '寰宇万象': '寰宇万象',
    '翁法罗斯': '翁法罗斯',
    '二相乐园': '二相乐园',
    '千星城': '千星城',
}


def parse_template(body):
    """解析 {{任务 ...}} 模板参数（含同行竖线保护）。"""
    m = re.search(r'\{\{任务\s*\n(.*?)\n\}\}', body, re.S) or re.search(
        r'\{\{任务\|(.*?)\n\}\}', body, re.S)
    params = {}
    if m:
        for line in m.group(1).split('\n'):
            mm = re.match(r'\|?(\w+)=(.*)', line)
            if mm:
                params[mm.group(1)] = re.sub(r'<!--.*?-->', '', mm.group(2)).strip()
    return params


def clean(text):
    """清理模板参数值：剥图标、链接、注释。"""
    if not text:
        return ''
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{\{图标\|([^|}]+)(?:\|[^}]*)?\}\}', r'\1', text)
    text = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', text)
    text = re.sub(r'\{\{黑幕\s*\|([^{}]*)\}\}', r'\1', text)
    text = re.sub(r'\{\{[^{}]*?\|([^{}]*)\}\}', r'\1', text)
    text = re.sub(r'\{\{[^{}]*\}\}', '', text)
    text = text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def extract_dialog(body, limit=14, exclude_desc=None):
    """从 ==剧情内容== 提取接取短信与场景文本摘录。exclude_desc: 需过滤的官方描述。"""
    sec = re.search(r'==剧情内容==(.*?)$', body, re.S)
    if not sec:
        return []
    text = sec.group(1)
    lines = []
    # 任务描述场景文本
    for m in re.finditer(r'\{\{任务描述\|([^|{}]+)\|', text):
        t = clean(m.group(1))
        if len(t) > 12:
            lines.append(('场景', t))
    # 左侧说话人文本（短信/对话），尾部 |是（默认选项标记）剔除
    for m in re.finditer(r'\{\{角色对话\|左\|([^|]+)\|文本\|(.*?)(?:\|是)?\}\}', text):
        who, t = m.group(1).strip(), clean(m.group(2))
        if who in ('模板开始',) or len(t) < 3:
            continue
        lines.append((who, t))
    # 去重保序（前 20 字指纹），并过滤与官方描述重复的场景
    seen, out = set(), []
    excl = [(exclude_desc or '')[:25]]
    for who, t in lines:
        fp = t[:20]
        if fp in seen:
            continue
        if any(e and t[:25].startswith(e) for e in excl):
            continue
        seen.add(fp)
        out.append((who, t))
        if len(out) >= limit:
            break
    return out


def build_entry(title, members):
    """members: [(page_name, body)] → markdown 文本。"""
    paras = [parse_template(b) for _, b in members]
    ver = paras[0].get('所属版本', '')
    region = REGION_SHORT.get(paras[0].get('任务地区', '').split('-')[0].split('（')[0],
                              paras[0].get('任务地区', ''))
    chars = paras[0].get('出场人物', '')
    series = paras[0].get('系列任务', '') or '单篇同行任务'
    cond = paras[0].get('任务条件', '')
    descs = [clean(p.get('任务描述', '')) for p in paras]
    desc_main = '；'.join(d for d in descs if d)

    lines = []
    lines.append('---')
    lines.append(f'title: {title}')
    lines.append('type: event')
    summary = f'{ver} 同行任务「{title}」：{desc_main[:90]}'
    lines.append(f'summary: {summary}')
    aliases = [page for page, _ in members if page != title]
    if aliases:
        lines.append('aliases:')
        lines.extend(f'  - {a}' for a in aliases)
    lines.append('tags:')
    lines.append('  group:')
    lines.append('    - 同行任务')
    lines.append('  location:')
    lines.append(f'    - {region}')
    lines.append('---')
    lines.append('')
    lines.append(f'# {title}')
    lines.append('')
    lines.append(f'> {desc_main}')
    lines.append('>')
    lines.append(f'> ——{ver} 同行任务官方描述')
    lines.append('')
    lines.append('## 基本信息')
    lines.append('')
    lines.append('| 项目 | 内容 |')
    lines.append('|------|------|')
    lines.append(f'| 类型 | 同行任务（{series}） |')
    lines.append(f'| 版本 | {ver} |')
    lines.append(f'| 地点 | {region} |')
    if chars:
        lines.append(f'| 出场人物 | {clean(chars)} |')
    if cond:
        lines.append(f'| 开放条件 | {clean(cond)} |')
    if len(members) > 1:
        lines.append(f'| 章节 | {"、".join(p for p, _ in members)} |')
    lines.append('')
    # 分任务呈现（多章节时）
    if len(members) == 1:
        dlg = extract_dialog(members[0][1], exclude_desc=clean(paras[0].get('任务描述', '')))
        if dlg:
            lines.append('## 剧情摘录')
            lines.append('')
            lines.append('> [!NOTE]')
            lines.append('> 以下为任务内短信与场景文本节选（官方原文）。')
            lines.append('')
            for who, t in dlg:
                lines.append(f'> **{who}**：{t}')
            lines.append('')
    else:
        for page, body in members:
            p = parse_template(body)
            lines.append(f'## {page}')
            lines.append('')
            if p.get('任务描述'):
                lines.append(f'> {clean(p["任务描述"])}')
                lines.append('')
            dlg = extract_dialog(body, exclude_desc=clean(p.get('任务描述', '')))
            if dlg:
                for who, t in dlg[:6]:
                    lines.append(f'> **{who}**：{t}')
                lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def main():
    pages = json.load(open('/tmp/peer_all.json'))
    OUT.mkdir(exist_ok=True)
    entries = {}
    for p in pages:
        name = p['name']
        if name in ('难得有情•其一', '难得有情•其二'):
            continue  # 由 MERGE 单独处理
        fn = RAW / f'{name}.txt'
        if not fn.exists():
            print('缺页:', name)
            continue
        title = RENAME.get(name, name)
        entries[title] = [(title, fn.read_text(encoding='utf-8'))]

    # 合并成对任务
    entries['难得有情'] = [
        (n, (RAW / f'{n}.txt').read_text(encoding='utf-8'))
        for n in MERGE['难得有情•其一'][1]
        if (RAW / f'{n}.txt').exists()
    ]

    count = 0
    for title, members in sorted(entries.items()):
        md = build_entry(title, members)
        (OUT / f'{title}.md').write_text(md, encoding='utf-8')
        count += 1
    print(f'生成同行任务词条 {count} 个')


if __name__ == '__main__':
    main()
