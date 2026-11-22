import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { onMounted, watch } from 'vue'
import { useRoute } from 'vitepress'
import './custom.css'

export default {
  extends: DefaultTheme,
  setup() {
    const route = useRoute()
    let io: IntersectionObserver | null = null

    const init = () => {
      if (typeof window === 'undefined') return

      document.documentElement.classList.add('hq-js')

      io?.disconnect()
      io = new IntersectionObserver(
        (entries) => {
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

      document.querySelectorAll(selector).forEach((el) => {
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
