/**
 * 构建前扫描 docs 下的所有条目，生成 .vitepress/data/entries.json
 *
 * 产物同时供三处消费：
 *   1. 自动内链插件（词条表）
 *   2. 分类页 / 标签页 / 侧栏 / 首页计数
 *   3. 条目底部的标签行
 *
 * 运行时机：docs:dev 与 docs:build 之前各跑一次。
 * 新增 md 文件或改动 frontmatter 后需要重启 dev 服务。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import matter from 'gray-matter'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '..')
const docsDir = path.join(root, 'docs')
const outFile = path.join(root, 'docs/.vitepress/data/entries.json')

/** 目录 → 条目类型 */
const TYPE_MAP = {
  characters: { key: 'character', label: '人物' },
  factions: { key: 'faction', label: '势力' },
  locations: { key: 'location', label: '地点' },
  concepts: { key: 'concept', label: '概念' },
  events: { key: 'event', label: '事件' },
  items: { key: 'item', label: '物品' }
}

/** 标签维度 → 中文名，顺序即展示顺序 */
const TAG_DIMS = {
  faction: '势力',
  location: '星球 / 地区',
  path: '命途',
  group: '集合'
}

const collator = new Intl.Collator('zh-Hans-CN')

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, name.name)
    if (name.isDirectory()) {
      if (name.name === '.vitepress' || name.name === 'public' || name.name === 'tags') continue
      walk(full, out)
    } else if (name.name.endsWith('.md') && name.name !== 'index.md') {
      out.push(full)
    }
  }
  return out
}

const files = walk(docsDir)
const entries = []
const anchors = []

for (const file of files) {
  const rel = path.relative(docsDir, file).replace(/\\/g, '/')
  const seg = rel.split('/')[0]
  const typeInfo = TYPE_MAP[seg]
  if (!typeInfo) continue

  const raw = fs.readFileSync(file, 'utf8')
  const { data } = matter(raw)
  const slug = rel.replace(/\.md$/, '')
  const urlPath = '/' + slug

  // 没有 frontmatter 的页面给一份兜底，避免整站报错
  const title = data.title || path.basename(slug)
  const tags = {}
  for (const dim of Object.keys(TAG_DIMS)) {
    const v = data.tags?.[dim]
    if (Array.isArray(v) && v.length) tags[dim] = v.filter(Boolean)
  }

  entries.push({
    slug,
    path: urlPath,
    title,
    type: typeInfo.key,
    typeLabel: typeInfo.label,
    summary: data.summary || '',
    aliases: Array.isArray(data.aliases) ? data.aliases.filter(Boolean) : [],
    tags
  })

  // 段落锚点：frontmatter 显式声明，避免把「加入公司」这类通用小节也变成词条
  // 两种写法：
  //   - 字符串：词条名与小节标题同名（anchors: [石心十人]）
  //   - 对象：词条名与小节标题不同（anchors: [{ term: 星核猎手, heading: 与星核猎手的关系 }]）
  for (const a of data.anchors || []) {
    if (typeof a === 'string' && a.trim()) {
      const name = a.trim()
      anchors.push({
        title: name,
        heading: name,
        path: `${urlPath}#${name}`,
        parent: title,
        parentSlug: slug
      })
    } else if (a && typeof a === 'object' && a.term) {
      const name = String(a.term).trim()
      const heading = String(a.heading || a.term).trim()
      if (!name) continue
      anchors.push({
        title: name,
        heading,
        path: `${urlPath}#${heading}`,
        parent: title,
        parentSlug: slug
      })
    }
  }
}

// 拼音排序
entries.sort((a, b) => collator.compare(a.title, b.title))

// 标签索引：维度 → 标签名 → 条目 slug 列表
const tagIndex = {}
for (const dim of Object.keys(TAG_DIMS)) {
  tagIndex[dim] = {}
  for (const e of entries) {
    for (const name of e.tags[dim] || []) {
      if (!tagIndex[dim][name]) tagIndex[dim][name] = []
      tagIndex[dim][name].push(e.slug)
    }
  }
  // 组内标签名也按拼音排
  tagIndex[dim] = Object.fromEntries(
    Object.entries(tagIndex[dim]).sort(([a], [b]) => collator.compare(a, b))
  )
}

// 类型索引
const typeIndex = {}
for (const info of Object.values(TYPE_MAP)) {
  typeIndex[info.key] = {
    label: info.label,
    items: entries.filter(e => e.type === info.key).map(e => e.slug)
  }
}

// 内链词条表：条目名 + 别名 + 段落锚点
const linkTargets = []
const seenTerm = new Set()

function pushTerm(term, path, kind, slug) {
  if (!term || seenTerm.has(term)) return
  seenTerm.add(term)
  linkTargets.push({ term, path, kind, slug })
}

for (const e of entries) {
  // 条目主名一律入表。它本身就是专有名词，两字也应可点（砂金、星核、命途）
  pushTerm(e.title, e.path, 'entry', e.slug)
  for (const alias of e.aliases) {
    // 别名里的双字词多为通用词（公司、家族），三字以上才自动链，避免误链
    if (alias.length < 3) continue
    pushTerm(alias, e.path, 'entry', e.slug)
  }
}
for (const a of anchors) {
  pushTerm(a.title, a.path, 'anchor', a.parentSlug)
}
// 长词优先，保证「星际和平公司」先于「公司」匹配
linkTargets.sort((a, b) => b.term.length - a.term.length)

const payload = {
  generatedAt: new Date().toISOString(),
  total: entries.length,
  dims: TAG_DIMS,
  entries,
  tagIndex,
  typeIndex,
  linkTargets
}

fs.mkdirSync(path.dirname(outFile), { recursive: true })
fs.writeFileSync(outFile, JSON.stringify(payload, null, 2) + '\n', 'utf8')

const tagCount = Object.values(tagIndex).reduce((n, t) => n + Object.keys(t).length, 0)
console.log(
  `[collect] ${entries.length} 条条目 · ${tagCount} 个标签 · ${anchors.length} 个锚点 · ${linkTargets.length} 个内链词条`
)
