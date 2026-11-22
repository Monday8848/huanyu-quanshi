import { defineConfig } from 'vitepress'

const base = process.env.DOCS_BASE || '/'

export default defineConfig({
  lang: 'zh-CN',
  title: '寰宇全事',
  titleTemplate: ':title · 崩铁世界观考据手册',
  description: '《崩坏：星穹铁道》世界观考据手册',
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
    ['meta', { name: 'apple-mobile-web-app-title', content: '寰宇全事' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: '寰宇全事' }],
    ['meta', { property: 'og:title', content: '寰宇全事 · 崩铁世界观考据手册' }],
    [
      'meta',
      {
        property: 'og:description',
        content: '以社区考据与推测为主体的《崩坏：星穹铁道》世界观手册'
      }
    ]
  ],

  themeConfig: {
    logo: '/logo.svg',
    siteTitle: '寰宇全事',

    nav: [
      { text: '卷首', link: '/preface' },
      { text: '总论卷', link: '/volumes/overview/' },
      { text: '阵营卷', link: '/volumes/factions/' },
      { text: '附录卷', link: '/volumes/appendix/' },
      {
        text: '检索',
        items: [
          { text: '术语表', link: '/glossary' },
          { text: '大事年表', link: '/timeline' },
          { text: '人物与势力索引', link: '/index-figures' }
        ]
      }
    ],

    sidebar: [
      {
        text: '卷首',
        items: [{ text: '编者说明', link: '/preface' }]
      },
      {
        text: '总论卷 · 星神与命途',
        items: [
          { text: '卷首导语', link: '/volumes/overview/' },
          { text: '第一章 星神', link: '/volumes/overview/aeons' },
          { text: '第二章 命途', link: '/volumes/overview/paths' },
          { text: '第三章 宇宙纪年', link: '/volumes/overview/chronology' }
        ]
      },
      {
        text: '阵营卷',
        items: [
          { text: '卷首导语', link: '/volumes/factions/' },
          { text: '星际和平公司', link: '/volumes/factions/ipc' },
          { text: '仙舟联盟', link: '/volumes/factions/xianzhou' },
          { text: '家族', link: '/volumes/factions/family' }
        ]
      },
      {
        text: '附录卷',
        items: [{ text: '未证实档案', link: '/volumes/appendix/' }]
      },
      {
        text: '检索',
        items: [
          { text: '术语表', link: '/glossary' },
          { text: '大事年表', link: '/timeline' },
          { text: '人物与势力索引', link: '/index-figures' }
        ]
      }
    ],

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
    docFooter: { prev: '上一卷', next: '下一卷' },
    lastUpdated: { text: '最后更新于' },
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    langMenuLabel: '语言'
  }
})
