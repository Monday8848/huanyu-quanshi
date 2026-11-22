import { defineConfig } from 'vitepress'

const base = process.env.DOCS_BASE || '/'

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
    ['link', { rel: 'icon', type: 'image/svg+xml', href: `${base}logo.svg` }],
    ['link', { rel: 'apple-touch-icon', href: `${base}logo.svg` }],
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
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

  themeConfig: {
    logo: '/logo.svg',
    siteTitle: '寰宇百科',

    nav: [
      { text: '人物', link: '/characters/' },
      { text: '势力', link: '/factions/' },
      { text: '地点', link: '/locations/' },
      { text: '概念', link: '/concepts/' },
      { text: '事件', link: '/events/' },
      { text: '物品', link: '/items/' }
    ],

    sidebar: {
      '/characters/': [
        {
          text: '人物',
          items: [
            { text: '人物总览', link: '/characters/' },
            { text: '砂金', link: '/characters/aventurine' }
          ]
        }
      ],
      '/factions/': [
        {
          text: '势力',
          items: [
            { text: '势力总览', link: '/factions/' },
            { text: '星际和平公司', link: '/factions/ipc' }
          ]
        }
      ],
      '/locations/': [
        {
          text: '地点',
          items: [
            { text: '地点总览', link: '/locations/' },
            { text: '匹诺康尼', link: '/locations/penacony' }
          ]
        }
      ],
      '/concepts/': [
        {
          text: '概念',
          items: [
            { text: '概念总览', link: '/concepts/' },
            { text: '命途', link: '/concepts/path' }
          ]
        }
      ],
      '/events/': [
        {
          text: '事件',
          items: [
            { text: '事件总览', link: '/events/' },
            { text: '匹诺康尼危机', link: '/events/penacony-crisis' }
          ]
        }
      ],
      '/items/': [
        {
          text: '物品',
          items: [
            { text: '物品总览', link: '/items/' },
            { text: '星核', link: '/items/star-core' }
          ]
        }
      ]
    },

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
