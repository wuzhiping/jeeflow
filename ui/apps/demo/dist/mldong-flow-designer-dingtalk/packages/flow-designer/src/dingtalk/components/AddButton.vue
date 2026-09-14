<template>
  <!-- 可插入：上线 + 圆 + 下线 -->
  <div class="ding-add-btn" v-if="!viewer && !readonly">
    <div class="ding-line-vertical" :class="lineClass"></div>
    <button class="ding-add-btn__circle" @click.stop="toggleSelector">+</button>
    <div class="ding-line-vertical" :class="lineClass"></div>
    <NodeSelector
      :visible="showSelector"
      :dnd-panel="dndPanel"
      :type-prefix="typePrefix"
      @update:visible="showSelector = $event"
      @select="handleSelect"
    />
  </div>
  <!-- 受保护节点后：仅渲染短连接线（不显示 + 圆） -->
  <div class="ding-add-btn ding-add-btn--readonly" v-else-if="!viewer && readonly">
    <div class="ding-line-vertical ding-line-vertical--short" :class="lineClass"></div>
  </div>
  <!-- viewer 模式 -->
  <div class="ding-add-btn" v-else>
    <div class="ding-line-vertical" :class="lineClass"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FDPatternItem, FDHighLightType } from '../../types'
import NodeSelector from './NodeSelector.vue'

const props = withDefaults(
  defineProps<{
    viewer: boolean
    typePrefix: string
    dndPanel?: FDPatternItem[]
    /** 不可插入：仅渲染短连接线，不显示 + 圆 */
    readonly?: boolean
    /** 前一个节点 id（用于计算连线高亮状态） */
    prevNodeId?: string
    /** 后一个节点 id（用于计算连线高亮状态） */
    nextNodeId?: string
    /** 高亮数据（activeNodeNames / historyNodeNames） */
    highLight?: FDHighLightType
  }>(),
  { readonly: false, prevNodeId: undefined, nextNodeId: undefined }
)

/**
 * 边高亮判断（按端点节点状态组合）
 * - 两端都在 history → history（绿色，已审批）
 * - 前 history + 后 active → active（蓝色，指向正在审批节点）
 * - 其它 → default（默认灰）
 */
const lineState = computed<'default' | 'active' | 'history'>(() => {
  if (!props.highLight || !props.prevNodeId || !props.nextNodeId) return 'default'
  const active = props.highLight.activeNodeNames || []
  const history = props.highLight.historyNodeNames || []
  if (active.length && history.includes(props.prevNodeId) && active.includes(props.nextNodeId)) {
    return 'active'
  }
  if (history.includes(props.prevNodeId) && history.includes(props.nextNodeId)) {
    return 'history'
  }
  return 'default'
})

const lineClass = computed(() => {
  const s = lineState.value
  return s === 'default' ? '' : `ding-line-vertical--${s}`
})

const emit = defineEmits<{
  (e: 'add', nodeType: string): void
}>()

const showSelector = ref(false)

function toggleSelector() {
  showSelector.value = !showSelector.value
}

function handleSelect(nodeType: string) {
  emit('add', nodeType)
  showSelector.value = false
}
</script>
