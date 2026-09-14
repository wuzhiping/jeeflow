<template>
  <div class="fd-json-viewer" :class="{ 'fd-json-viewer--linenum': showLineNumber }">
    <FDJsonNode :data="data" :depth="0" :is-last="true" :default-expand-depth="defaultExpandDepth" />
  </div>
</template>

<script setup lang="ts">
/**
 * FDJsonViewer —— 自研 JSON 查看器（替代 vue-json-pretty）
 * 支持行号（CSS counter 实现）、按层折叠
 */
import FDJsonNode from './FDJsonNode.vue'

withDefaults(defineProps<{
  data: any
  showLineNumber?: boolean
  defaultExpandDepth?: number
}>(), {
  showLineNumber: false,
  defaultExpandDepth: 2
})
</script>

<style scoped>
.fd-json-viewer {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 13px;
  color: #333;
  background: #fafafa;
  border-radius: 6px;
  padding: 8px;
  box-sizing: border-box;
}

/* 行号：CSS counter，零 JS 开销 */
.fd-json-viewer--linenum {
  counter-reset: fdjson;
}

.fd-json-viewer--linenum :deep(.fd-json-line) {
  counter-increment: fdjson;
}

.fd-json-viewer--linenum :deep(.fd-json-line::before) {
  content: counter(fdjson);
  display: inline-block;
  width: 28px;
  flex-shrink: 0;
  text-align: right;
  padding-right: 8px;
  color: #c0c0c0;
  user-select: none;
}
</style>
