<script setup>
import { withBase } from 'vitepress'

defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 96 },
  rotate: { type: [Number, String], default: 0 },
  alt: { type: String, default: '《崩坏：星穹铁道》官方表情' }
})
</script>

<template>
  <img
    class="hq-emoji"
    :src="withBase('/emoji/' + name + '.webp')"
    :alt="alt"
    :style="{ '--hq-emoji-size': size + 'px', '--hq-emoji-rot': rotate + 'deg' }"
    decoding="async"
    draggable="false"
  />
</template>
