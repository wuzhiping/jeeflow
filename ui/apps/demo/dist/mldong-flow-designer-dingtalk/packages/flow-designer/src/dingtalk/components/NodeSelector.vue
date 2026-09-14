<template>
  <div class="ding-node-selector" v-if="visible">
    <div ref="panelRef" class="ding-node-selector__panel">
      <div
        v-for="item in filteredItems"
        :key="item.type"
        class="ding-node-selector__item"
        @click="handleSelect(item)"
      >
        <span :class="['ding-node-selector__item__icon', getIconClass(item)]">
          {{ getIconText(item) }}
        </span>
        <span>{{ item.label || item.text || getDefaultLabel(item) }}</span>
      </div>
      <!-- 条件分支选项 -->
      <div class="ding-node-selector__item" @click="handleSelectCondition">
        <span class="ding-node-selector__item__icon ding-node-selector__item__icon--condition">
          &#x2726;
        </span>
        <span>条件分支</span>
      </div>
      <!-- 并行分支选项 -->
      <div class="ding-node-selector__item" @click="handleSelectParallel">
        <span class="ding-node-selector__item__icon ding-node-selector__item__icon--parallel">
          &#x2263;
        </span>
        <span>并行分支</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import type { FDPatternItem } from '../../types'

const props = defineProps<{
  visible: boolean
  dndPanel?: FDPatternItem[]
  typePrefix: string
}>()

const emit = defineEmits<{
  (e: 'select', nodeType: string): void
  (e: 'update:visible', value: boolean): void
}>()

const panelRef = ref<HTMLElement | null>(null)

/** 过滤掉 start/end 以及 decision/fork 类型 */
const filteredItems = computed(() => {
  if (!props.dndPanel) return []
  return props.dndPanel.filter(item => {
    if (!item.type) return false
    if (item.hide) return false
    const baseType = item.type.replace(props.typePrefix, '')
    return !['start', 'end', 'decision', 'fork', 'join'].includes(baseType)
  })
})

function getIconClass(item: FDPatternItem) {
  if (!item.type) return ''
  const baseType = item.type.replace(props.typePrefix, '')
  switch (baseType) {
    case 'task': return 'ding-node-selector__item__icon--task'
    case 'custom': return 'ding-node-selector__item__icon--custom'
    case 'subProcess': return 'ding-node-selector__item__icon--subprocess'
    default: return 'ding-node-selector__item__icon--task'
  }
}

function getIconText(item: FDPatternItem) {
  if (!item.type) return '?'
  const baseType = item.type.replace(props.typePrefix, '')
  switch (baseType) {
    case 'task': return '\u2713'
    case 'custom': return '\u2605'
    case 'subProcess': return '\u25A3'
    default: return '\u2713'
  }
}

/** 兜底中文标签（type → 名称映射，兼容 canvas 模式 dndPanel 无 label 的写法） */
function getDefaultLabel(item: FDPatternItem) {
  if (!item.type) return '未知'
  const baseType = item.type.replace(props.typePrefix, '')
  switch (baseType) {
    case 'task': return '审批节点'
    case 'custom': return '自定义节点'
    case 'subProcess': return '子流程'
    default: return item.type
  }
}

function handleSelect(item: FDPatternItem) {
  if (item.type) {
    emit('select', item.type)
  }
  close()
}

function handleSelectCondition() {
  emit('select', '__condition__')
  close()
}

function handleSelectParallel() {
  emit('select', '__parallel__')
  close()
}

function close() {
  emit('update:visible', false)
}

/**
 * 点击外部画布区域关闭面板。
 *
 * 背景：原本用 <div class="ding-node-selector__overlay" position: fixed> 作为遮罩，
 * 但钉钉模式的画布 pan/zoom 容器 .ding-designer__viewport 上有
 * transform: translate(x,y) scale(s) + will-change: transform，
 * 根据 CSS 规范（CSS Containment / Fixed positioning），这会导致
 * position: fixed 元素不再相对 viewport，而是相对该祖先，
 * overlay 退化为只能覆盖父容器大小（约 176x196），点击画布其他位置无反应。
 *
 * 改用 document click 监听绕过 transform 边界：
 * - toggle 按钮已用 @click.stop 阻止冒泡，点 toggle 时本 handler 不触发（避免误关）
 * - 点 panel 内部 / panel 上的 item 也不关（panel.contains(target) 判定）
 * - 其他任何 click（画布空白、其他节点、其他按钮）都关
 */
function handleDocumentClick(e: MouseEvent) {
  if (!props.visible) return
  const target = e.target as Node | null
  if (!target) return
  if (panelRef.value?.contains(target)) return
  close()
}

onMounted(() => document.addEventListener('click', handleDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', handleDocumentClick))
</script>
