import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import { onMounted, watch } from 'vue'
import { useRoute } from 'vitepress'
import EntryFooter from './components/EntryFooter.vue'
import EntryList from './components/EntryList.vue'
import EntryCount from './components/EntryCount.vue'
import ProgressBar from './components/ProgressBar.vue'
import TagCloud from './components/TagCloud.vue'
import TagIndex from './components/TagIndex.vue'
import HqEmoji from './components/HqEmoji.vue'
import HqRandomEmoji from './components/HqRandomEmoji.vue'
import HqBoot from './components/HqBoot.vue'
import NotFound from './components/NotFound.vue'
import HqUid from './components/HqUid.vue'
import './custom.css'

export default {
  extends: DefaultTheme,

  Layout() {
    return h(DefaultTheme.Layout, null, {
      // 首次进入站点时的极简加载层（每个会话一次）
      'layout-top': () => h(HqBoot),
      // 自定义 404：主题内置的 not-found 插槽
      'not-found': () => h(NotFound),
      // 标签行、导航框与文末声明统一由组件渲染，条目页无需手写
      'doc-after': () => h(EntryFooter)
    })
  },

  enhanceApp({ app }) {
    app.component('EntryList', EntryList)
    app.component('EntryCount', EntryCount)
    app.component('ProgressBar', ProgressBar)
    app.component('TagCloud', TagCloud)
    app.component('TagIndex', TagIndex)
    app.component('HqEmoji', HqEmoji)
    app.component('HqRandomEmoji', HqRandomEmoji)
    app.component('HqUid', HqUid)
  },

  setup() {
    const route = useRoute()
    let io: IntersectionObserver | null = null

    const init = () => {
      if (typeof window === 'undefined') return

      document.documentElement.classList.add('hq-js')

      io?.disconnect()
      io = new IntersectionObserver(
        entries => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-in')
              io?.unobserve(entry.target)
            }
          }
        },
        { rootMargin: '0px 0px -6% 0px', threshold: 0.04 }
      )

      const selector = [
        '.vp-doc h2',
        '.vp-doc h3',
        '.vp-doc table',
        '.vp-doc .custom-block',
        '.hq-vol',
        '.hq-section',
        '.hq-progress'
      ].join(',')

      document.querySelectorAll(selector).forEach(el => {
        if (el.classList.contains('reveal')) return
        el.classList.add('reveal')
        io?.observe(el)
      })
    }

    onMounted(() => {
      init()
      watch(
        () => route.path,
        () => window.setTimeout(init, 150)
      )
    })
  }
} satisfies Theme
