<script setup>
import { computed } from 'vue'
import { withBase } from 'vitepress'
import entriesData from '../../data/entries.json'

const bySlug = computed(() => {
  const m = {}
  for (const e of entriesData.entries) m[e.slug] = e
  return m
})

const groups = computed(() =>
  Object.entries(entriesData.dims)
    .map(([dim, label]) => {
      const tags = Object.entries(entriesData.tagIndex[dim] || {}).map(([name, slugs]) => ({
        name,
        items: slugs.map(s => bySlug.value[s]).filter(Boolean)
      }))
      return { dim, label, tags }
    })
    .filter(g => g.tags.length)
)

const dimCount = computed(() =>
  Object.values(entriesData.tagIndex).reduce((n, m) => n + Object.keys(m).length, 0)
)
</script>

<template>
  <div class="hq-tagindex">
    <p class="hq-tagindex-lead">
      共 <b>{{ dimCount }}</b> 个标签、<b>{{ entriesData.total }}</b> 条条目。
      每个条目可以同时挂在多个标签下——人物的归属、地点的星球、势力信奉的命途，都在这张网里。
    </p>

    <nav class="hq-tagindex-nav">
      <a v-for="g in groups" :key="g.dim" :href="'#dim-' + g.dim">
        {{ g.label }} <span>{{ g.tags.length }}</span>
      </a>
    </nav>

    <section v-for="g in groups" :key="g.dim" class="hq-tagsec">
      <h2 :id="'dim-' + g.dim">{{ g.label }}</h2>
      <div v-for="t in g.tags" :key="t.name" class="hq-tagblock" :id="'tag-' + t.name">
        <h3>
          {{ t.name }}
          <span class="n">{{ t.items.length }}</span>
        </h3>
        <div class="hq-tagitems">
          <a v-for="e in t.items" :key="e.slug" :href="withBase(e.path)">{{ e.title }}</a>
        </div>
      </div>
    </section>
  </div>
</template>
