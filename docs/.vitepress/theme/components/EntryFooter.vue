<script setup>
import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
import entriesData from '../../data/entries.json'
import navboxes from '../../data/navboxes'

const { frontmatter, page } = useData()

const currentPath = computed(() => '/' + page.value.relativePath.replace(/\.md$/, ''))

const groups = computed(() => {
  const tags = frontmatter.value.tags
  if (!tags) return []
  return Object.entries(entriesData.dims)
    .map(([dim, label]) => {
      const list = tags[dim]
      return Array.isArray(list) && list.length ? { dim, label, items: list } : null
    })
    .filter(Boolean)
})

const tagHref = name => withBase('/tags/#tag-' + encodeURIComponent(name))

const boxes = computed(() => {
  const raw = frontmatter.value.navbox
  const names = Array.isArray(raw) ? raw : raw ? [raw] : []
  return names.map(n => ({ key: n, ...navboxes[n] })).filter(b => b && b.title)
})

const pathByTitle = computed(() => {
  const m = {}
  for (const e of entriesData.entries) m[e.title] = e.path
  return m
})

// 导航项支持两种写法：
//   字符串  —— 词条名，自动查表；查不到就渲染为灰色待补
//   对象    —— { text, link }，显式指定链接（用于尚未独立成条、但有锚点的对象）
const labelOf = it => (typeof it === 'string' ? it : it.text)
const hrefOf = it => (typeof it === 'string' ? pathByTitle.value[it] : it.link)
</script>

<template>
  <div v-if="groups.length || boxes.length" class="hq-entry-foot">
    <div v-for="box in boxes" :key="box.key" class="hq-navbox">
      <div class="hq-navbox-title">{{ box.title }}</div>
      <div v-for="g in box.groups" :key="g.label" class="hq-navbox-row">
        <span class="hq-navbox-label">{{ g.label }}</span>
        <span class="hq-navbox-items">
          <template v-for="(it, i) in g.items" :key="labelOf(it)">
            <a
              v-if="hrefOf(it)"
              :href="withBase(hrefOf(it))"
              :class="{ current: hrefOf(it) === currentPath }"
            >{{ labelOf(it) }}</a>
            <span v-else class="pending" :title="labelOf(it) + '（条目待补）'">{{ labelOf(it) }}</span>
            <i v-if="i < g.items.length - 1">·</i>
          </template>
        </span>
      </div>
      <div v-if="box.note" class="hq-navbox-note">{{ box.note }}</div>
    </div>

    <div v-if="groups.length" class="hq-tagline">
      <span class="hq-tagline-title">所属分类</span>
      <div class="hq-tagline-rows">
        <div v-for="g in groups" :key="g.dim" class="hq-tagline-row">
          <span class="hq-tagline-dim">{{ g.label }}</span>
          <span class="hq-tagline-tags">
            <a v-for="t in g.items" :key="t" class="hq-tag" :href="tagHref(t)">{{ t }}</a>
          </span>
        </div>
      </div>
    </div>

    <p class="hq-disclaimer">本文含玩家推测。官方记载以游戏内文本为准。</p>
  </div>
  <p v-else-if="frontmatter.type" class="hq-disclaimer hq-disclaimer-alone">
    本文含玩家推测。官方记载以游戏内文本为准。
  </p>
</template>
