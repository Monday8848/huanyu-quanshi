import { defineConfig } from 'vitepress'
import fs from 'node:fs'
import { autoLinkPlugin } from './plugins/auto-link'

const base = process.env.DOCS_BASE || '/'

/* ---------- 构建期读取条目数据，生成侧栏 ---------- */

const DATA_FILE = new URL('./data/entries.json', import.meta.url)

type Entry = {
  slug: string
  path: string
  title: string
  type: string
  tags: Record<string, string[]>
}

type EntriesData = {
  total: number
  dims: Record<string, string>
  entries: Entry[]
  tagIndex: Record<string, Record<string, string[]>>
  typeIndex: Record<string, { label: string; items: string[] }>
}

function loadData(): EntriesData {
  try {
    return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8')) as EntriesData
  } catch {
    return { total: 0, dims: {}, entries: [], tagIndex: {}, typeIndex: {} }
  }
}

const data = loadData()

const DIRS = [
  { dir: 'characters', label: '人物', type: 'character', dims: ['faction', 'location'] },
  { dir: 'factions', label: '势力', type: 'faction', dims: ['path', 'group'] },
  { dir: 'locations', label: '地点', type: 'location', dims: ['location', 'faction'] },
  { dir: 'concepts', label: '概念', type: 'concept', dims: ['group'] },
  { dir: 'events', label: '事件', type: 'event', dims: ['location', 'faction'] },
  { dir: 'items', label: '物品', type: 'item', dims: ['group', 'location'] },
  { dir: 'books', label: '书籍', type: 'book', dims: ['kind', 'location'] }
]

function buildSidebar() {
  const sidebar: Record<string, unknown[]> = {}

  // 全站导航：不论当前在哪一页，都能回首页、切到任意分类、进标签索引。
  // 移动端没有独立的顶部导航，抽屉就是唯一入口，这一组必须放在最上面。
  const siteGroup = {
    text: '全站导航',
    items: [
      { text: '首页', link: '/' },
      ...DIRS.map(d => ({ text: d.label, link: `/${d.dir}/` })),
      { text: '标签索引', link: '/tags/' }
    ]
  }

  for (const { dir, label, type, dims } of DIRS) {
    const count = data.typeIndex[type]?.items.length || 0

    // 本类条目直接列进目录，不要让人先点总览再找
    // 下属组织（parentSlug 非空）在 entries 中已紧跟上级，这里只加缩进前缀，
    // 避免「石心十人」这类部门与「星际和平公司」在目录里看起来平级。
    const own = data.entries
      .filter(e => e.slug.startsWith(dir + '/'))
      .map(e => ({ text: e.parentSlug ? `　└ ${e.title}` : e.title, link: e.path }))

    const groups: unknown[] = [
      siteGroup
    ]

    if (dir === 'books') {
      // 书籍 688 条不适合平铺：按文体分组折叠，组内再列条目
      const kindMap = new Map<string, typeof own>()
      for (const e of data.entries) {
        if (!e.slug.startsWith(dir + '/')) continue
        for (const k of e.tags?.kind || []) {
          if (!kindMap.has(k)) kindMap.set(k, [])
          kindMap.get(k)!.push({ text: e.parentSlug ? `　└ ${e.title}` : e.title, link: e.path })
        }
      }
      const sorted = [...kindMap.entries()].sort(
        ([a], [b]) => (kindMap.get(b)!.length - kindMap.get(a)!.length)
      )
      groups.push({
        text: `${label} · ${count} 条`,
        items: [{ text: '总览', link: `/${dir}/` }]
      })
      for (const [k, items] of sorted) {
        groups.push({
          text: `${k} · ${items.length}`,
          collapsed: true,
          items
        })
      }
    } else {
      groups.push({
        text: `${label} · ${count} 条`,
        items: [{ text: '总览', link: `/${dir}/` }, ...own]
      })
    }

    // 当前目录下出现过的标签，每个维度按条目数取前 6 个
    const seen = new Map<string, { dim: string; name: string; count: number }>()
    for (const e of data.entries) {
      if (!e.slug.startsWith(dir + '/')) continue
      for (const dim of dims) {
        for (const name of e.tags?.[dim] || []) {
          const key = dim + '\u0000' + name
          const hit = seen.get(key)
          if (hit) hit.count++
          else seen.set(key, { dim, name, count: 1 })
        }
      }
    }

    const sorted = [...seen.values()].sort(
      (a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh')
    )

    // 严格按 dims 声明顺序分组，组内按条目数排序
    // 书籍的 kind 已用词条列表分组呈现，这里只保留地区标签组
    const dimList = dir === 'books' ? dims.filter(d => d !== 'kind') : dims
    for (const dim of dimList) {
      const group = sorted.filter(t => t.dim === dim).slice(0, 6)
      if (!group.length) continue
      groups.push({
        text: `按${data.dims[dim] || dim}`,
        collapsed: false,
        items: group.map(t => ({
          text: `${t.name} ${t.count}`,
          link: `/tags/#tag-${encodeURIComponent(t.name)}`
        }))
      })
    }

    sidebar[`/${dir}/`] = groups
  }

  sidebar['/tags'] = [
    siteGroup,
    {
      text: '标签索引',
      items: [
        { text: '全部标签', link: '/tags/' },
        ...Object.entries(data.dims).map(([dim, dimLabel]) => ({
          text: `${dimLabel}（${Object.keys(data.tagIndex[dim] || {}).length}）`,
          link: `/tags/#dim-${dim}`
        }))
      ]
    }
  ]

  return sidebar
}

export default defineConfig({
  lang: 'zh-CN',
  title: '寰宇百科',
  titleTemplate: ':title · 星穹铁道设定百科',
  description: '《崩坏：星穹铁道》设定百科：官方记载为基准，玩家推测为补充',
  base,
  cleanUrls: true,
  lastUpdated: true,
  appearance: 'dark',

  head: [
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: `${base}favicon-32.png` }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '16x16', href: `${base}favicon-16.png` }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '64x64', href: `${base}favicon-64.png` }],
    ['link', { rel: 'apple-touch-icon', sizes: '180x180', href: `${base}apple-touch-icon.png` }],
    ['meta', { name: 'theme-color', content: '#0a0e1a' }],
    ['meta', { name: 'apple-mobile-web-app-title', content: '寰宇百科' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: '寰宇百科' }],
    ['meta', { property: 'og:title', content: '寰宇百科 · 星穹铁道设定百科' }],
    [
      'meta',
      {
        property: 'og:description',
        content: '以官方记载为基准、玩家推测为补充的《崩坏：星穹铁道》设定百科'
      }
    ]
  ],

  markdown: {
    config: md => {
      md.use(autoLinkPlugin)
    }
  },

  // 百科条目之间没有线性顺序，全站关掉「上一条 / 下一条」
  transformPageData(pageData) {
    pageData.frontmatter.prev = false
    pageData.frontmatter.next = false
  },

  themeConfig: {
    logo: '/logo.png',
    siteTitle: '寰宇百科',

    nav: [
      { text: '首页', link: '/' },
      { text: '人物', link: '/characters/' },
      { text: '势力', link: '/factions/' },
      { text: '地点', link: '/locations/' },
      { text: '概念', link: '/concepts/' },
      { text: '事件', link: '/events/' },
      { text: '物品', link: '/items/' },
      { text: '书籍', link: '/books/' },
      { text: '标签', link: '/tags/' }
    ],

    sidebar: buildSidebar(),

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '没有找到结果',
            resetButtonTitle: '清除',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭'
            }
          }
        }
      }
    },

    outline: { label: '本页目录', level: [2, 3] },
    docFooter: { prev: '上一条', next: '下一条' },
    lastUpdated: { text: '最后更新于' },
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    langMenuLabel: '语言'
  }
})
