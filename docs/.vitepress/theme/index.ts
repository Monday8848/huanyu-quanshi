import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import EntryFooter from './components/EntryFooter.vue'
import EntryList from './components/EntryList.vue'
import EntryGroups from './components/EntryGroups.vue'
import EntryCount from './components/EntryCount.vue'
import ProgressBar from './components/ProgressBar.vue'
import TagCloud from './components/TagCloud.vue'
import TagIndex from './components/TagIndex.vue'
import HqEmoji from './components/HqEmoji.vue'
import HqRandomEmoji from './components/HqRandomEmoji.vue'
import NotFound from './components/NotFound.vue'
import HqUid from './components/HqUid.vue'
import './custom.css'

export default {
  extends: DefaultTheme,

  Layout() {
    return h(DefaultTheme.Layout, null, {
      // 自定义 404：主题内置的 not-found 插槽
      'not-found': () => h(NotFound),
      // 标签行、导航框与文末声明统一由组件渲染，条目页无需手写
      'doc-after': () => h(EntryFooter)
    })
  },

  enhanceApp({ app }) {
    app.component('EntryList', EntryList)
    app.component('EntryGroups', EntryGroups)
    app.component('EntryCount', EntryCount)
    app.component('ProgressBar', ProgressBar)
    app.component('TagCloud', TagCloud)
    app.component('TagIndex', TagIndex)
    app.component('HqEmoji', HqEmoji)
    app.component('HqRandomEmoji', HqRandomEmoji)
    app.component('HqUid', HqUid)
  }
} satisfies Theme
