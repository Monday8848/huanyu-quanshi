<script setup>
import { onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

const show = ref(false)
const leaving = ref(false)
const pick = ref('hyacine-happy')
const pool = ['hyacine-happy', 'hyacine-explain', 'hyacine-think', 'hyacine-hug']
let hideTimer = null
let removeTimer = null

onMounted(() => {
  if (typeof window === 'undefined') return
  // 每个会话只在首次进入站点时出现一次
  if (sessionStorage.getItem('hq-booted')) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    sessionStorage.setItem('hq-booted', '1')
    return
  }

  pick.value = pool[Math.floor(Math.random() * pool.length)]
  show.value = true
  sessionStorage.setItem('hq-booted', '1')

  hideTimer = setTimeout(() => { leaving.value = true }, 560)
  removeTimer = setTimeout(() => { show.value = false }, 940)
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
