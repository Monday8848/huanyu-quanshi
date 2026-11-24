<script setup>
import { computed } from 'vue'
import { withBase } from 'vitepress'
import entriesData from '../../data/entries.json'

const props = defineProps({
  type: { type: String, default: '' },
  dim: { type: String, default: '' },
  tag: { type: String, default: '' },
  group: { type: Boolean, default: false }
})

const bySlug = computed(() => {
  const m = {}
  for (const e of entriesData.entries) m[e.slug] = e
  return m
})

const items = computed(() => {
  let slugs = []
  if (props.type && props.dim && props.tag) {
    // 类型 + 标签联用：书籍总览按地区分组时，只列该地区下的书籍
    const typeSet = new Set(entriesData.typeIndex[props.type]?.items || [])
    slugs = (entriesData.tagIndex[props.dim]?.[props.tag] || []).filter(s => typeSet.has(s))
  } else if (props.type) slugs = entriesData.typeIndex[props.type]?.items || []
  else if (props.dim && props.tag) slugs = entriesData.tagIndex[props.dim]?.[props.tag] || []
  return slugs.map(s => bySlug.value[s]).filter(Boolean)
})

const dimLabels = entriesData.dims

function subTags(entry) {
  const out = []
  for (const [dim, label] of Object.entries(dimLabels)) {
    const list = entry.tags?.[dim]
    if (!Array.isArray(list) || !list.length) continue
    // 上级名称已由 is-child 的「隶属」标记表达，标签行里不再重复
    const rest = entry.parent ? list.filter(t => t !== entry.parent) : list
    if (rest.length) out.push({ dim, label, text: rest.join(' · ') })
  }
  return out
}
</script>

<template>
  <div v-if="items.length" class="hq-elist" :class="{ 'is-grouped': group }">
    <a v-for="e in items" :key="e.slug" class="hq-erow" :class="{ 'is-child': e.parentSlug }" :href="withBase(e.path)">
      <span class="hq-erow-head">
        <span class="hq-erow-name">{{ e.title }}</span>
        <span v-if="e.parent" class="hq-erow-parent">{{ e.parentLabel || '隶属' }} · {{ e.parent }}</span>
        <span v-for="s in subTags(e)" :key="s.dim" class="hq-erow-tag">{{ s.text }}</span>
      </span>
      <span v-if="e.summary" class="hq-erow-sum">{{ e.summary }}</span>
    </a>
  </div>
  <p v-else class="hq-elist-empty">这一组还没有条目。</p>
</template>
