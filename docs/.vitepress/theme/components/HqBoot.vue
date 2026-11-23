<script setup>
import { onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { bootPool } from '../../data/emoji-pools'

const show = ref(false)
const leaving = ref(false)
const pool = bootPool
const pick = ref(pool[0])
let hideTimer = null
let removeTimer = null

onMounted(() => {
  if (typeof window === 'undefined') return

  // 每次整页加载（打开或刷新）播放一次；站内路由切换不重新挂载，不会重复
  pick.value = pool[Math.floor(Math.random() * pool.length)]
  show.value = true

  hideTimer = setTimeout(() => { leaving.value = true }, 900)
  removeTimer = setTimeout(() => { show.value = false }, 1280)
})

const dismiss = () => {
  leaving.value = true
  if (removeTimer) clearTimeout(removeTimer)
  removeTimer = setTimeout(() => { show.value = false }, 340)
}
</script>

<template>
  <div
    v-if="show"
    class="hq-boot"
    :class="{ 'is-leaving': leaving }"
    aria-hidden="true"
    @click="dismiss"
  >
    <img class="hq-boot-emoji" :src="withBase('/emoji/' + pick + '.webp')" alt="" draggable="false" />
    <p class="hq-boot-text">寰宇百科 · 正在调取档案</p>
  </div>
</template>
