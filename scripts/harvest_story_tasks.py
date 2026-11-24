#!/usr/bin/env python3
"""故事任务词条通用生成：支持单任务页与系列任务聚合。

输入清单 JSON：{"entries": [{"title": ..., "pages": [页面名...], "series_desc": 可选}]}
页面可为 {{任务}} 单页或 {{系列任务}} 主页（其子任务页在 pages 中显式列出）。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'raw' / 'bwiki'
OUT = ROOT / 'docs' / 'events'

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


def parse_template(body, name='任务'):
    m = re.search(r'\{\{' + name + r'\s*\n(.*?)\n\}\}', body, re.S) or re.search(
        r'\{\{' + name + r'\|(.*?)\n\}\}', body, re.S)
    params = {}
    if m:
        for line in m.group(1).split('\n'):
            mm = re.match(r'\|?(\w+)=(.*)', line)
            if mm:
                params[mm.group(1)] = re.sub(r'<!--.*?-->', '', mm.group(2)).strip()
    return params


def clean(text):
    if not text:
        return ''
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{\{图标\|([^|}]+)(?:\|[^}]*)?\}\}', r'\1', text)
    text = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', text)
    # 黑幕 → 纯文字（任务描述中的剧透遮蔽内容）
    text = re.sub(r'\{\{黑幕\s*\|([^{}]*)\}\}', r'\1', text)
    # 其余裸模板剥壳留首参数文字
    text = re.sub(r'\{\{[^{}]*?\|([^{}]*)\}\}', r'\1', text)
    text = re.sub(r'\{\{[^{}]*\}\}', '', text)
    text = text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def extract_dialog(body, limit=14, exclude_desc=None):
    sec = re.search(r'==剧情内容==(.*?)$', body, re.S)
    if not sec:
        return []
    text = sec.group(1)
    lines = []
    for m in re.finditer(r'\{\{任务描述\|([^|{}]+)\|', text):
        t = clean(m.group(1))
        if len(t) > 12:
            lines.append(('场景', t))
    for m in re.finditer(r'\{\{角色对话\|左\|([^|]+)\|文本\|(.*?)(?:\|是)?\}\}', text):
        who, t = m.group(1).strip(), clean(m.group(2))
        if who in ('模板开始',) or len(t) < 3:
            continue
        lines.append((who, t))
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


def load_page(name):
    fn = RAW / f'{name}.txt'
    if not fn.exists():
        return None
    return fn.read_text(encoding='utf-8')


def build_entry(title, spec, default_group):
    """spec: {'pages': [...], 'series_desc': str|None, 'kind': 任务类型}"""
    bodies = []
    for pn in spec['pages']:
        b = load_page(pn)
        if b is None:
            print('  缺页:', pn)
            continue
        bodies.append((pn, b))
    if not bodies:
        return None

    first_body = bodies[0][1]
    # 主页可能是 {{系列任务}} 或 {{任务}}
    main_kind = '系列任务' if '{{系列任务' in first_body else '任务'
    main_par = parse_template(first_body, main_kind)
    series_desc = spec.get('series_desc') or main_par.get('描述', '')

    # 收集子任务参数
    sub_paras = []
    for pn, b in bodies:
        if '{{系列任务' in b and len(bodies) > 1:
            continue  # 跳过系列主页（子任务信息从子页取）
        sub_paras.append((pn, parse_template(b, '任务'), b))

    ver = main_par.get('所属版本', '') or (sub_paras[0][1].get('所属版本', '') if sub_paras else '')
    region_raw = main_par.get('任务地区', '') or (sub_paras[0][1].get('任务地区', '') if sub_paras else '')
    region = REGION_SHORT.get(region_raw.split('-')[0].split('（')[0].split('，')[0], region_raw)
    kind = main_par.get('任务类型', '') or spec.get('kind', '冒险任务')

    # 任务描述集合
    descs = [clean(main_par.get('描述', ''))] if main_kind == '系列任务' else []
    fps = {d[:50] for d in descs if d}
    for pn, par, _ in sub_paras:
        d = clean(par.get('任务描述', ''))
        # 前 50 字与已有描述雷同的（系列页复读），跳过
        if d and not any(d.startswith(f) or f.startswith(d[:50]) for f in fps):
            descs.append(d)
            fps.add(d[:50])
    desc_main = '；'.join(d for d in descs if d)

    # 出场人物并集
    chars = []
    for pn, par, _ in sub_paras:
        for c in re.split('[、,，]', par.get('出场人物', '')):
            c = c.strip()
            if c and c not in chars:
                chars.append(c)

    lines = ['---']
    lines.append(f'title: {title}')
    lines.append('type: event')
    lines.append(f'summary: {ver} {kind}「{title}」：{desc_main[:88]}')
    aliases = [pn for pn, _ in bodies if pn != title and pn != title + '（任务）']
    if aliases:
        lines.append('aliases:')
        lines.extend(f'  - {a}' for a in aliases)
    lines.append('tags:')
    lines.append('  group:')
    lines.append(f'    - {default_group}')
    lines.append('  location:')
    lines.append(f'    - {region}')
    lines.append('---')
    lines.append('')
    lines.append(f'# {title}')
    lines.append('')
    lines.append(f'> {desc_main}')
    lines.append('>')
    lines.append(f'> ——{ver} {kind}官方描述')
    lines.append('')
    lines.append('## 基本信息')
    lines.append('')
    lines.append('| 项目 | 内容 |')
    lines.append('|------|------|')
    lines.append(f'| 类型 | {kind} |')
    lines.append(f'| 版本 | {ver} |')
    lines.append(f'| 地点 | {region} |')
    if chars:
        lines.append(f'| 出场人物 | {"、".join(chars)} |')
    if len(spec['pages']) > 1 and len(sub_paras) > 1:
        lines.append(f'| 章节 | {"、".join(pn for pn, _, _ in sub_paras)} |')
    lines.append('')

    if len(sub_paras) <= 1 and bodies:
        dlg = extract_dialog(bodies[0][1], exclude_desc=descs[0] if descs else None)
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
        shown_descs = set()
        for pn, par, b in sub_paras:
            lines.append(f'## {pn}')
            lines.append('')
            d = clean(par.get('任务描述', ''))
            # 与主描述或前一小节重复的引用块不再重复输出
            if d and d not in shown_descs and not any(d[:50] == x[:50] for x in shown_descs):
                lines.append(f'> {d}')
                lines.append('')
            shown_descs.add(d)
            dlg = extract_dialog(b, exclude_desc=d)
            if dlg:
                for who, t in dlg[:8]:
                    lines.append(f'> **{who}**：{t}')
                lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def main():
    manifest = json.load(open(sys.argv[1]))
    default_group = manifest.get('group', '冒险任务')
    for spec in manifest['entries']:
        md = build_entry(spec['title'], spec, default_group)
        if md is None:
            print('跳过（无页面）:', spec['title'])
            continue
        (OUT / f"{spec['title']}.md").write_text(md, encoding='utf-8')
        print('生成:', spec['title'])


if __name__ == '__main__':
    main()
