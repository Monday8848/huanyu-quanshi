<script setup>
import { computed, ref } from 'vue'
import { withBase } from 'vitepress'
import entriesData from '../../data/entries.json'

// 分组折叠的总览列表：组头常驻（SSR 只渲染组头），条目展开时才渲染。
// 面向条目量大的分类（书籍 688 条、事件 110 条），避免整页数千 DOM 节点拖慢移动端。

const props = defineProps({
  type: { type: String, required: true },
  // 按哪个标签维度分组；每条取该维度的第一个标签，无标签进「其他」
  groupDim: { type: String, default: 'location' },
  // 组的固定顺序，中文顿号分隔；未列出的组按条目数排在后面，最后是「其他」
  order: { type: String, default: '' },
  fallback: { type: String, default: '其他' },
  // 少于该条数的组并入 fallback 组，避免零散小组刷屏
  minGroup: { type: Number, default: 0 },
  search: { type: Boolean, default: true }
})

const bySlug = {}
for (const e of entriesData.entries) bySlug[e.slug] = e

const dimLabels = entriesData.dims

function subTags(entry) {
  const out = []
  for (const [dim, label] of Object.entries(dimLabels)) {
    const list = entry.tags?.[dim]
    if (!Array.isArray(list) || !list.length) continue
    const rest = entry.parent ? list.filter(t => t !== entry.parent) : list
    if (rest.length) out.push({ dim, label, text: rest.join(' · ') })
  }
  return out
}

// 录入不一致的标签归并到统一组名（如「雅利洛-VI」→「雅利洛-Ⅵ」、简称→全称）
const GROUP_MERGE = {
  '雅利洛-VI': '雅利洛-Ⅵ',
  '雅利洛-Ⅵ-磐岩镇': '雅利洛-Ⅵ',
  '罗浮': '仙舟「罗浮」',
  '黑塔空间站': '空间站「黑塔」'
}
function groupKeyOf(entry) {
  const tags = entry.tags?.[props.groupDim] || []
  let key = tags.length ? tags[0] : props.fallback
  key = key.split('、')[0]
  return GROUP_MERGE[key] || key
}

const allItems = (entriesData.typeIndex[props.type]?.items || [])
  .map(s => bySlug[s])
  .filter(Boolean)

// 静态数据静态算，只算一次
const buckets = new Map()
for (const e of allItems) {
  const key = groupKeyOf(e)
  if (!buckets.has(key)) buckets.set(key, [])
  buckets.get(key).push(e)
}
// 零散小组并入 fallback
if (props.minGroup > 0) {
  for (const [key, items] of [...buckets.entries()]) {
    if (key !== props.fallback && items.length < props.minGroup) {
      if (!buckets.has(props.fallback)) buckets.set(props.fallback, [])
      buckets.get(props.fallback).push(...items)
      buckets.delete(key)
    }
  }
}
const ordered = []
for (const key of props.order.split('、').map(s => s.trim()).filter(Boolean)) {
  if (buckets.has(key)) {
    ordered.push([key, buckets.get(key)])
    buckets.delete(key)
  }
}
for (const [key, items] of [...buckets.entries()].sort(
  (a, b) => b[1].length - a[1].length
)) {
  ordered.push([key, items])
}
// 组内不排序：entries.json 已按拼音排好，客户端复用同一顺序，
// 避免两端 ICU 差异导致 hydration mismatch。
const groups = ordered.map(([name, items]) => ({ name, items }))

const expanded = ref({})
const q = ref('')

const searching = computed(() => q.value.trim().length > 0)

function hit(entry, kw) {
  return (
    (entry.title || '').toLowerCase().includes(kw) ||
    (entry.aliases || []).some(a => String(a).toLowerCase().includes(kw)) ||
    (entry.summary || '').toLowerCase().includes(kw)
  )
}

const matchGroups = computed(() => {
  const kw = q.value.trim().toLowerCase()
  if (!kw) return []
  return groups
    .map(g => ({ name: g.name, items: g.items.filter(e => hit(e, kw)) }))
    .filter(g => g.items.length)
})

const matchTotal = computed(() => matchGroups.value.reduce((n, g) => n + g.items.length, 0))

const shown = computed(() => (searching.value ? matchGroups.value : groups))

function toggle(name) {
  expanded.value = { ...expanded.value, [name]: !expanded.value[name] }
}

const allOpen = computed(() => groups.length > 0 && groups.every(g => expanded.value[g.name]))

function toggleAll() {
  const next = {}
  if (!allOpen.value) for (const g of groups) next[g.name] = true
  expanded.value = next
}
</script>

<template>
  <div class="hq-egroups">
    <div v-if="search" class="hq-egroup-search">
      <input v-model="q" type="search" :placeholder="`按名称 / 别名 / 摘要搜索本页 ${allItems.length} 条…`" />
      <span v-if="searching" class="hq-egroup-hint">匹配 {{ matchTotal }} 条</span>
    </div>

    <div v-if="!searching && groups.length > 1" class="hq-egroup-actions">
      <button class="hq-egroup-toggleall" type="button" @click="toggleAll">
        {{ allOpen ? '全部收起' : '全部展开' }}
      </button>
    </div>

    <section
      v-for="g in shown"
      :key="g.name"
      class="hq-egroup"
      :class="{ 'is-open': searching || expanded[g.name] }"
    >
      <button
        v-if="!searching"
        class="hq-egroup-head"
        type="button"
        :aria-expanded="!!expanded[g.name]"
        @click="toggle(g.name)"
      >
        <span class="hq-egroup-arrow" aria-hidden="true">▸</span>
        <span class="hq-egroup-name">{{ g.name }}</span>
        <span class="hq-egroup-count">{{ g.items.length }} 条</span>
      </button>
      <div v-else class="hq-egroup-head is-static">
        <span class="hq-egroup-name">{{ g.name }}</span>
        <span class="hq-egroup-count">{{ g.items.length }} 条</span>
      </div>

      <div v-if="searching || expanded[g.name]" class="hq-egroup-body">
        <a
          v-for="e in g.items"
          :key="e.slug"
          class="hq-erow"
          :class="{ 'is-child': e.parentSlug }"
          :href="withBase(e.path)"
        >
          <span class="hq-erow-head">
            <span class="hq-erow-name">{{ e.title }}</span>
            <span v-if="e.parent" class="hq-erow-parent">{{ e.parentLabel || '隶属' }} · {{ e.parent }}</span>
            <span v-for="s in subTags(e)" :key="s.dim" class="hq-erow-tag">{{ s.text }}</span>
          </span>
          <span v-if="e.summary" class="hq-erow-sum">{{ e.summary }}</span>
        </a>
      </div>
    </section>

    <p v-if="searching && !shown.length" class="hq-elist-empty">没有匹配的条目。</p>
  </div>
</template>
