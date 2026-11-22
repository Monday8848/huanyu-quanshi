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

<template>{{ value }}</template>
