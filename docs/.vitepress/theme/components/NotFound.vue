<script setup>
import { withBase } from 'vitepress'
import { notFoundPool } from '../../data/emoji-pools'
</script>

<template>
  <div class="hq-404">
    <div class="hq-404-emoji">
      <HqRandomEmoji :set="notFoundPool" :size="152" :rotate="-4" />
    </div>
    <p class="hq-404-code">404</p>
    <h1 class="hq-404-title">这条时间线上没有这一页</h1>
    <p class="hq-404-sub">可能名字改了、条目合并了，或者它从来没有存在过。</p>
    <div class="hq-404-actions">
      <a class="hq-btn" :href="withBase('/')">回到首页</a>
      <a class="hq-btn ghost" :href="withBase('/tags')">标签索引</a>
    </div>
  </div>
</template>
