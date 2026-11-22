<script setup>
import { computed } from 'vue'
import entriesData from '../../data/entries.json'

const goal = 200
const total = computed(() => entriesData.total)
const pct = computed(() => Math.min(100, Math.max(1, Math.round((total.value / goal) * 100))))
</script>

<template>
  <div class="hq-progress">
    <span class="label">条目收录 <b>{{ total }} / {{ goal }}</b></span>
    <span class="bar"><span :style="{ width: pct + '%' }"></span></span>
    <span class="label">骨架期 · 六类样板已成</span>
  </div>
</template>
