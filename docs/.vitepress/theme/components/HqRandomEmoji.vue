<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

const props = defineProps({
  set: {
    type: Array,
    default: () => ['hyacine-happy', 'hyacine-explain', 'hyacine-think', 'hyacine-hug']
  },
  size: { type: [Number, String], default: 120 },
  rotate: { type: [Number, String], default: 0 },
  // 0 表示只随机选一张；大于 0 时按毫秒间隔轮换
  interval: { type: Number, default: 0 }
})

const idx = ref(0)
const visible = ref(true)
let timer = null
let swapTimer = null

onMounted(() => {
  if (props.set.length > 1) {
    idx.value = Math.floor(Math.random() * props.set.length)
  }
  if (props.interval > 0 && props.set.length > 1) {
    timer = setInterval(() => {
      visible.value = false
      swapTimer = setTimeout(() => {
        // 随机跳到另一张，避免总是按顺序轮播
        const step = 1 + Math.floor(Math.random() * (props.set.length - 1))
        idx.value = (idx.value + step) % props.set.length
        visible.value = true
      }, 340)
    }, props.interval)
  }
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  if (swapTimer) clearTimeout(swapTimer)
})
</script>

<template>
  <img
    class="hq-emoji hq-emoji-fade"
    :class="{ 'is-hidden': !visible }"
    :src="withBase('/emoji/' + set[idx] + '.webp')"
    :style="{ '--hq-emoji-size': size + 'px', '--hq-emoji-rot': rotate + 'deg' }"
    alt="《崩坏：星穹铁道》官方表情"
    draggable="false"
  />
</template>
