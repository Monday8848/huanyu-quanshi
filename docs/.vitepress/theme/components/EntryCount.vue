<script setup>
import { computed } from 'vue'
import entriesData from '../../data/entries.json'

const props = defineProps({
  type: { type: String, default: '' },
  of: { type: String, default: '' }
})

const value = computed(() => {
  if (props.of === 'total') return entriesData.total
  return entriesData.typeIndex[props.type]?.items.length || 0
})
</script>

<template>
  <!-- 裸文本根会与相邻文本在 SSR 输出中合并成单个 text node，
       与客户端 vdom 的 vnode 边界不一致，触发全站 hydration mismatch。
       加一层 span 让 SSR 输出与 vdom 结构对齐。 -->
  <span class="hq-inline-count">{{ value }}</span>
</template>
