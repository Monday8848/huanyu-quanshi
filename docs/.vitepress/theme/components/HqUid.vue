<script setup>
import { onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  uid: { type: String, default: '110325153' }
})

const copied = ref(false)
let timer = null

const copy = async () => {
  const text = props.uid
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // 非 HTTPS / 旧浏览器的降级路径
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    ta.remove()
  }
  copied.value = true
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => { copied.value = false }, 1600)
}

onBeforeUnmount(() => timer && clearTimeout(timer))
</script>

<template>
  <p class="hq-owner">
    站主 UID <span>{{ uid }}</span>
    <button type="button" class="hq-copy" :class="{ 'is-done': copied }" @click="copy">
      {{ copied ? '已复制' : '复制' }}
    </button>
  </p>
</template>
