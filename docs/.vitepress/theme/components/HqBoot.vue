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

  // 每个会话只播一次：刷新、跳转都不再挡内容，避免每次都像卡了一下
  let booted = false
  try {
    booted = sessionStorage.getItem('hq-booted') === '1'
  } catch {
    booted = false
  }
  if (booted) return

  try {
    sessionStorage.setItem('hq-booted', '1')
  } catch {
    // 隐私模式下不可写，忽略即可
  }

  pick.value = pool[Math.floor(Math.random() * pool.length)]
  show.value = true

  hideTimer = setTimeout(() => { leaving.value = true }, 560)
  removeTimer = setTimeout(() => { show.value = false }, 900)
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
