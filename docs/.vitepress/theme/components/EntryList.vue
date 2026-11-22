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
  if (props.type) slugs = entriesData.typeIndex[props.type]?.items || []
  else if (props.dim && props.tag) slugs = entriesData.tagIndex[props.dim]?.[props.tag] || []
  return slugs.map(s => bySlug.value[s]).filter(Boolean)
})

const dimLabels = entriesData.dims

function subTags(entry) {
  const out = []
  for (const [dim, label] of Object.entries(dimLabels)) {
    const list = entry.tags?.[dim]
    if (Array.isArray(list) && list.length) out.push({ dim, label, text: list.join(' · ') })
  }
  return out
}
</script>

<template>
  <div v-if="items.length" class="hq-elist" :class="{ 'is-grouped': group }">
    <a v-for="e in items" :key="e.slug" class="hq-erow" :href="withBase(e.path)">
      <span class="hq-erow-head">
        <span class="hq-erow-name">{{ e.title }}</span>
        <span v-for="s in subTags(e)" :key="s.dim" class="hq-erow-tag">{{ s.text }}</span>
      </span>
      <span v-if="e.summary" class="hq-erow-sum">{{ e.summary }}</span>
    </a>
  </div>
  <p v-else class="hq-elist-empty">这一组还没有条目。</p>
</template>
