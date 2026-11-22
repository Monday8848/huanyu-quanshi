<script setup>
import { computed } from 'vue'
import { withBase } from 'vitepress'
import entriesData from '../../data/entries.json'

const hot = computed(() => {
  const all = []
  for (const dim of ['faction', 'location']) {
    const m = entriesData.tagIndex[dim] || {}
    all.push(
      ...Object.entries(m).map(([name, slugs]) => ({ dim, name, count: slugs.length }))
    )
  }
  all.sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh'))

  // 优先展示有两条以上归属的标签；不足 4 个时用单条标签补齐
  const strong = all.filter(t => t.count >= 2).slice(0, 8)
  if (strong.length >= 4) return strong
  const weak = all.filter(t => t.count < 2).slice(0, 4 - strong.length)
  return [...strong, ...weak]
})

const href = name => withBase('/tags/#tag-' + encodeURIComponent(name))
</script>

<template>
  <div class="hq-tagcloud">
    <a v-for="t in hot" :key="t.dim + t.name" class="hq-tagcloud-item" :href="href(t.name)">
      <span class="n">{{ t.name }}</span>
      <span class="c">{{ t.count }}</span>
    </a>
  </div>
</template>
