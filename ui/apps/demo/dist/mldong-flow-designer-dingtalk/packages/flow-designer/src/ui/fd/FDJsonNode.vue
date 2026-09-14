<template>
  <div class="fd-json-node">
    <!-- 对象/数组：可折叠 -->
    <template v-if="isExpandable">
      <div class="fd-json-line" :style="{ paddingLeft: indent }">
        <span class="fd-json-toggle" @click="expanded = !expanded">{{ expanded ? '▾' : '▸' }}</span>
        <template v-if="name !== null">
          <span class="fd-json-key">"{{ name }}"</span>
          <span class="fd-json-colon">: </span>
        </template>
        <span class="fd-json-bracket">{{ openBracket }}</span>
        <template v-if="!expanded">
          <span class="fd-json-ellipsis">… {{ count }} 项 </span>
          <span class="fd-json-bracket">{{ closeBracket }}</span>
          <span v-if="!isLast" class="fd-json-comma">,</span>
        </template>
      </div>
      <template v-if="expanded">
        <FDJsonNode
          v-for="(child, idx) in entries"
          :key="idx"
          :name="child.name"
          :data="child.value"
          :depth="depth + 1"
          :is-last="idx === entries.length - 1"
          :default-expand-depth="defaultExpandDepth"
        />
        <div class="fd-json-line" :style="{ paddingLeft: indent }">
          <span class="fd-json-toggle-placeholder"></span>
          <span class="fd-json-bracket">{{ closeBracket }}</span>
          <span v-if="!isLast" class="fd-json-comma">,</span>
        </div>
      </template>
    </template>
    <!-- 基本类型：单行 -->
    <div v-else class="fd-json-line" :style="{ paddingLeft: indent }">
      <span class="fd-json-toggle-placeholder"></span>
      <template v-if="name !== null">
        <span class="fd-json-key">"{{ name }}"</span>
        <span class="fd-json-colon">: </span>
      </template>
      <span :class="valueClass">{{ valueText }}</span>
      <span v-if="!isLast" class="fd-json-comma">,</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * FDJsonNode —— FDJsonViewer 的递归渲染节点（内部组件）
 */
import { ref, computed } from 'vue'
import FDJsonNode from './FDJsonNode.vue'

const props = withDefaults(defineProps<{
  name?: string | null
  data: any
  depth?: number
  isLast?: boolean
  defaultExpandDepth?: number
}>(), {
  name: null,
  depth: 0,
  isLast: true,
  defaultExpandDepth: 2
})

const expanded = ref(props.depth < props.defaultExpandDepth)

const isExpandable = computed(() =>
  props.data !== null && typeof props.data === 'object'
)

const isArray = computed(() => Array.isArray(props.data))

const openBracket = computed(() => (isArray.value ? '[' : '{'))
const closeBracket = computed(() => (isArray.value ? ']' : '}'))

const entries = computed(() => {
  if (isArray.value) {
    return (props.data as any[]).map(value => ({ name: null as string | null, value }))
  }
  return Object.keys(props.data || {}).map(key => ({ name: key, value: props.data[key] }))
})

const count = computed(() => entries.value.length)

const indent = computed(() => `${props.depth * 16}px`)

const valueType = computed(() => {
  if (props.data === null) return 'null'
  if (Array.isArray(props.data)) return 'object'
  return typeof props.data
})

const valueText = computed(() => {
  switch (valueType.value) {
    case 'string':
      return `"${props.data}"`
    case 'null':
      return 'null'
    default:
      return String(props.data)
  }
})

const valueClass = computed(() => `fd-json-value fd-json-value--${valueType.value}`)
</script>

<style scoped>
.fd-json-line {
  display: flex;
  align-items: flex-start;
  line-height: 20px;
  white-space: pre-wrap;
  word-break: break-all;
}

.fd-json-toggle {
  width: 14px;
  flex-shrink: 0;
  cursor: pointer;
  color: #999;
  user-select: none;
  font-size: 11px;
  text-align: center;
}

.fd-json-toggle:hover {
  color: #1677ff;
}

.fd-json-toggle-placeholder {
  width: 14px;
  flex-shrink: 0;
}

.fd-json-key {
  color: #881391;
}

.fd-json-colon {
  color: #666;
}

.fd-json-bracket {
  color: #666;
}

.fd-json-comma {
  color: #666;
}

.fd-json-ellipsis {
  color: #999;
  font-size: 12px;
  padding: 0 2px;
}

.fd-json-value--string {
  color: #c41a16;
}

.fd-json-value--number {
  color: #1c00cf;
}

.fd-json-value--boolean {
  color: #0d22aa;
}

.fd-json-value--null {
  color: #808080;
}
</style>
