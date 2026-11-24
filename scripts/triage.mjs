#!/usr/bin/env node
/**
 * triage.mjs — 对 raw/bwiki 做体检与分级，产出 raw/TRIAGE.md + raw/priority.json
 *
 * 分级口径（对应网站"设定百科"定位）：
 *   A 设定/叙事：派系、地点、事件、概念、角色背景、书籍文本、版本专题
 *   B 可用素材：任务文本、命路歧图、活动剧情、PV/动画文本
 *   C 低价值：材料/怪物/掉落/攻略/抽取建议/数值表/Data 页/沙盒
 */
import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve(process.cwd(), 'raw')
const DIR = path.join(ROOT, 'bwiki')

const files = fs.readdirSync(DIR).filter((f) => f.endsWith('.txt'))

const C_LOW = /(Data:|^沙盒\/|攻略|抽取|养成|配队|强度|节奏榜|材料|素材|食谱|消耗品|贵重物|敌人|敌方|掉落|商店|兑换|任务需要内容|成就|图鉴一览|属性梯度|筛选$)/
const A_KEYS = [
  // 组织
  '派系', '星际和平公司', '仙舟', '列车', '军团', '家族', '学会', '忆庭', '游侠', '石心', '猎手', '愚者', '悼伶人', '丰饶', '巡猎', '博识', '公司',
  // 地点
  '翁法罗斯', '匹诺康尼', '雅利洛', '罗浮', '空间站', '二相乐园', '千星城', '仙舟', '贝洛伯格', '奥赫玛', '雅努萨', '悬锋', '树庭', '斯缇科', '哀丽秘榭', '晨昏之眼',
  // 概念
  '命途', '星神', '令使', '星核', '虚数', '忆域', '忆灵', '泰坦', '黄金裔', '火种', '半神', '愿力', '愿宝', '利衡币', '谒者', '基石', '星琼',
]
const B_KEYS = /(命路歧图|任务|剧情|阅读物|记录|手记|档案|日志|书信|留言|短信|语音|PV|动画|短片|千星纪游|版本「|前瞻|专题)/

function extractCats(text) {
  const cats = []
  const re = /\[\[(?:分类|Category):([^\]|]+)/g
  let m
  while ((m = re.exec(text))) cats.push(m[1].trim())
  return [...new Set(cats)]
}

const rows = []
for (const f of files) {
  const title = f.replace(/\.txt$/, '')
  const text = fs.readFileSync(path.join(DIR, f), 'utf8')
  const size = text.length
  const cats = extractCats(text)
  const catStr = cats.join(' ')

  let grade = 'C'
  let reason = ''
  if (C_LOW.test(title) || cats.some((c) => /材料|敌人|道具|攻略|活动奖励/.test(c))) {
    grade = 'C'
    reason = '功能/数值页'
  } else if (A_KEYS.some((k) => title.includes(k)) || cats.some((c) => /派系|地点|角色|设定|组织|星球|事件|书籍|读物|概念|历史|专有名词/.test(c))) {
    grade = 'A'
    reason = '设定/叙事'
  } else if (B_KEYS.test(title) || cats.some((c) => /任务|剧情|活动/.test(c))) {
    grade = 'B'
    reason = '剧情素材'
  } else if (size > 6000) {
    grade = 'B'
    reason = '长文本'
  }
  if (grade !== 'C' && size < 400) grade = 'C'

  rows.push({ title, file: f, size, cats, grade, reason })
}

rows.sort((a, b) => b.size - a.size)

const byGrade = { A: [], B: [], C: [] }
for (const r of rows) byGrade[r.grade].push(r)

const catCount = new Map()
for (const r of rows) for (const c of r.cats) catCount.set(c, (catCount.get(c) || 0) + 1)

const total = rows.reduce((s, r) => s + r.size, 0)
let md = `# BWIKI 抓取体检\n\n`
md += `- 文件数：**${rows.length}**\n- 总字符：**${(total / 1e6).toFixed(2)} M**（约 ${(total / 1024 / 1024).toFixed(1)} MB）\n`
md += `- A 设定/叙事：**${byGrade.A.length}** 页\n- B 剧情素材：**${byGrade.B.length}** 页\n- C 功能/数值：**${byGrade.C.length}** 页\n\n`
md += `## 分类分布（Top 60）\n\n| 分类 | 页数 |\n|---|---|\n`
for (const [c, n] of [...catCount.entries()].sort((a, b) => b[1] - a[1]).slice(0, 60)) md += `| ${c} | ${n} |\n`

for (const g of ['A', 'B']) {
  md += `\n## ${g} 级清单（按长度降序，前 200）\n\n| 页面 | KB | 分类 |\n|---|---|---|\n`
  for (const r of byGrade[g].slice(0, 200)) {
    md += `| ${r.title} | ${(r.size / 1024).toFixed(1)} | ${r.cats.slice(0, 3).join('、')} |\n`
  }
}

fs.writeFileSync(path.join(ROOT, 'TRIAGE.md'), md)
fs.writeFileSync(path.join(ROOT, 'priority.json'), JSON.stringify(byGrade, null, 1))
console.log(`A=${byGrade.A.length} B=${byGrade.B.length} C=${byGrade.C.length} total=${(total / 1e6).toFixed(2)}M chars`)
console.log('->', path.join(ROOT, 'TRIAGE.md'))
