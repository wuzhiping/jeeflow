<template>
  <!-- 开始节点 -->
  <div
    v-if="baseType === 'start'"
    :class="['ding-node-pill', 'ding-node-pill--start', highlightClass, { 'is-clickable': !viewer }]"
    @click="!viewer && $emit('edit', node)"
  >
    开始
  </div>

  <!-- 结束节点 -->
  <div
    v-else-if="baseType === 'end'"
    :class="['ding-node-pill', 'ding-node-pill--end', highlightClass, { 'is-clickable': !viewer }]"
    @click="!viewer && $emit('edit', node)"
  >
    结束
  </div>

  <!-- 合并节点（join）：与并行分支容器对称的虚线框容器 -->
  <div
    v-else-if="baseType === 'join'"
    :class="['ding-condition-group', 'ding-join-marker', highlightClass, { 'is-clickable': !viewer }]"
    @click="!viewer && $emit('edit', node)"
  >
    <div class="ding-condition-group__header">
      <span class="ding-condition-group__title">合并节点</span>
    </div>
    <div class="ding-join-marker__inner">
      <span class="ding-join-marker__dot"></span>
      <span class="ding-join-marker__name">{{ node.name || '合并点' }}</span>
    </div>
  </div>

  <!-- 普通任务节点卡片 -->
  <div
    v-else
    :class="['ding-node-card', highlightClass, countersignClass]"
    @click="$emit('edit', node)"
  >
    <div class="ding-node-card__bar" :style="barStyle"></div>
    <div class="ding-node-card__header">
      <span class="ding-node-card__icon">{{ typeIcon }}</span>
      <span class="ding-node-card__title">{{ typeLabel }}</span>
      <!-- 会签角标：performType=ALL 时显示 并行会签/顺序会签 -->
      <span
        v-if="countersignBadge"
        class="ding-node-card__badge"
        :class="`ding-node-card__badge--${countersignType}`"
      >{{ countersignBadge }}</span>
      <span class="ding-node-card__actions" v-if="!viewer">
        <button
          v-if="canDelete"
          class="ding-node-card__action-btn ding-node-card__action-btn--delete"
          @click.stop="$emit('delete', node)"
          title="删除"
        >
          &times;
        </button>
      </span>
    </div>
    <FDTooltip :title="node.name || '未命名节点'">
      <div class="ding-node-card__body">
        {{ node.name || '未命名节点' }}
      </div>
    </FDTooltip>
    <!-- 成员列表：highLight.nodeProgress 存在时回显（已处理打勾 / 当前轮到高亮 / 未到灰色） -->
    <div v-if="nodeProgressMembers.length" class="ding-node-card__members">
      <div
        v-for="m in nodeProgressMembers"
        :key="m.id"
        :class="['ding-node-card__member', { 'is-done': m.done, 'is-active': m.active }]"
      >
        <span class="ding-node-card__member-mark">
          {{ m.done ? '✓' : (m.active ? '▶' : '·') }}
        </span>
        <span class="ding-node-card__member-name">{{ m.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DingNode } from '../types'
import type { FDHighLightType, FDThemeConfig } from '../../types'
import { FDTooltip } from '../../ui/fd'

const props = withDefaults(defineProps<{
  node: DingNode
  typePrefix: string
  viewer: boolean
  highLight?: FDHighLightType
  theme?: FDThemeConfig
  /** 是否可删除（默认 true：start/end/firstChild 等系统节点传 false） */
  canDelete?: boolean
  /** 节点深度（0=start, 1=第一个任务=申请人, >=2=审批人） */
  depth?: number
}>(), {
  canDelete: true,
  depth: 0
})

defineEmits<{
  (e: 'edit', node: DingNode): void
  (e: 'delete', node: DingNode): void
}>()

const baseType = computed(() => {
  return props.node.type.replace(props.typePrefix, '')
})

const typeLabel = computed(() => {
  switch (baseType.value) {
    case 'task': return props.depth === 1 ? '申请人' : '审批人'
    case 'custom': return '自定义节点'
    case 'subProcess': return '子流程'
    default: return '任务'
  }
})

const typeIcon = computed(() => {
  switch (baseType.value) {
    case 'task': return '✓'
    case 'custom': return '★'
    case 'subProcess': return '▣'
    default: return '●'
  }
})

const isActive = computed(() => {
  if (!props.highLight?.activeNodeNames) return false
  return props.highLight.activeNodeNames.includes(props.node.id)
})

const isHistory = computed(() => {
  if (!props.highLight?.historyNodeNames) return false
  return props.highLight.historyNodeNames.includes(props.node.id)
})

const highlightClass = computed(() => {
  if (isActive.value) return baseType.value === 'start' || baseType.value === 'end'
    ? 'ding-node-pill--active' : 'ding-node-card--active'
  if (isHistory.value) return baseType.value === 'start' || baseType.value === 'end'
    ? 'ding-node-pill--history' : 'ding-node-card--history'
  return ''
})

// ─── 会签识别 ────────────────────────────────────────────────────────────
// performType=ALL 为会签节点；countersignType 兼容两种存储格式：
//   properties.countersignType（平铺，vben5 面板保存）
//   properties.field.countersignType（嵌套，演示数据/旧格式，后端 NodeParser 同规则兜底）
const countersignType = computed<'PARALLEL' | 'SEQUENTIAL' | ''>(() => {
  if (props.node.properties?.performType !== 'ALL') return ''
  const raw = props.node.properties?.countersignType || props.node.properties?.field?.countersignType
  return raw === 'SEQUENTIAL' ? 'SEQUENTIAL' : 'PARALLEL'
})

const countersignBadge = computed(() => {
  if (countersignType.value === 'SEQUENTIAL') return '顺序会签'
  if (countersignType.value === 'PARALLEL') return '并行会签'
  return ''
})

/** 会签卡片修饰类（描边），供 scss 控制 */
const countersignClass = computed(() => {
  if (countersignType.value === 'SEQUENTIAL') return 'ding-node-card--seq-countersign'
  if (countersignType.value === 'PARALLEL') return 'ding-node-card--parallel-countersign'
  return ''
})

// ─── 成员进度回显（viewer 模式，来自 highLight.nodeProgress）──────────────
// 任意节点可带：历史节点 done、进行中节点 active、会签节点完整列表
// 存在则渲染成员列表（done 打勾 / active 当前轮到 / 其余未处理），不存在保持现状
const nodeProgressMembers = computed(() => {
  const progress = props.highLight?.nodeProgress?.[props.node.id]
  if (!progress?.members?.length) return []
  return progress.members.map((m) => ({
    id: m.id,
    name: m.name || m.id,
    done: !!m.done,
    active: !!m.active,
  }))
})

const barStyle = computed(() => {
  if (isActive.value && props.theme?.activeColor) {
    return { backgroundColor: props.theme.activeColor }
  }
  if (isHistory.value && props.theme?.historyColor) {
    return { backgroundColor: props.theme.historyColor }
  }
  // 会签节点彩条：并行蓝 / 顺序橙（优先于主题色，运行高亮时让位于 active/history）
  if (countersignType.value === 'SEQUENTIAL') return { backgroundColor: '#fa8c16' }
  if (countersignType.value === 'PARALLEL') return { backgroundColor: '#1677ff' }
  if (props.theme?.primaryColor) {
    return { backgroundColor: props.theme.primaryColor }
  }
  return {}
})
</script>
