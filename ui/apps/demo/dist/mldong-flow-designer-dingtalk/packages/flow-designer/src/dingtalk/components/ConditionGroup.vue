<template>
  <div class="ding-condition-group">
    <!-- 条件组头部 -->
    <div class="ding-condition-group__header">
      <span
        class="ding-condition-group__title"
        :class="{ 'ding-condition-group__title--clickable': !viewer }"
        :title="!viewer ? '点击编辑决策配置' : ''"
        @click="!viewer && $emit('edit', node)"
      >条件分支</span>
      <span
        v-if="!viewer"
        class="ding-condition-group__add-branch"
        @click="$emit('add-branch', node)"
      >
        + 添加条件
      </span>
      <button
        v-if="!viewer && !protectedIdsComputed.has(node.id)"
        class="ding-condition-group__delete"
        title="删除整个条件分支组"
        @click="$emit('delete', node)"
      >&times;</button>
    </div>
    <!-- 分支区域 -->
    <div class="ding-condition-group__branches" ref="branchesRef">
      <!-- 顶部横线 -->
      <div class="ding-condition-group__top-line" :style="topLineStyle"></div>
      <!-- 各分支列 -->
      <BranchColumn
        v-for="(branch, index) in node.branches"
        :key="branch.id"
        :branch="branch"
        :type-prefix="typePrefix"
        :viewer="viewer"
        :high-light="highLight"
        :theme="theme"
        :dnd-panel="dndPanel"
        :can-delete-checker="canDeleteChecker"
        @edit="(n) => $emit('edit', n)"
        @delete="(n) => $emit('delete', n)"
        @add="(nodeType, parentNode) => $emit('add', nodeType, parentNode, index)"
        @add-branch="(n) => $emit('add-branch', n)"
        @edit-branch="(b) => $emit('edit-branch', b)"
        @add-to-branch="(nodeType, b) => $emit('add-to-branch', nodeType, b)"
      />
      <!-- 底部横线 -->
      <div class="ding-condition-group__bottom-line" :style="bottomLineStyle"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import type { DingConditionNode, DingNode, DingBranch } from '../types'
import type { FDHighLightType, FDThemeConfig, FDPatternItem } from '../../types'
import BranchColumn from './BranchColumn.vue'

const props = withDefaults(defineProps<{
  node: DingConditionNode
  typePrefix: string
  viewer: boolean
  highLight?: FDHighLightType
  theme?: FDThemeConfig
  dndPanel?: FDPatternItem[]
  /** 受保护节点 ID 集合（来自 DingTalkDesigner，用于隐藏 start/end/firstChild 的删除按钮） */
  protectedIds?: Set<string>
  /** 节点是否可删除检查器（false 时隐藏 × 按钮；默认全部可删除） */
  canDeleteChecker?: (node: DingNode) => boolean
}>(), {
  protectedIds: () => new Set<string>()
})

// 兜底：props 是只读的，统一通过 protectedIdsComputed 访问，避免 undefined 调用 .has
const protectedIdsComputed = computed(() => props.protectedIds ?? new Set<string>())

defineEmits<{
  (e: 'edit', node: DingNode): void
  (e: 'delete', node: DingNode): void
  (e: 'add', nodeType: string, parentNode: DingNode | null, branchIndex: number): void
  (e: 'add-branch', node: DingNode): void
  (e: 'edit-branch', branch: DingBranch): void
  (e: 'add-to-branch', nodeType: string, branch: DingBranch): void
}>()

const branchesRef = ref<HTMLElement>()
const lineWidth = ref('0px')
const lineLeft = ref('0px')
let resizeObserver: ResizeObserver | null = null

function updateLines() {
  if (!branchesRef.value) return
  const container = branchesRef.value
  const cols = container.querySelectorAll('.ding-branch-col')
  if (cols.length < 2) {
    lineWidth.value = '0px'
    return
  }
  const first = cols[0] as HTMLElement
  const last = cols[cols.length - 1] as HTMLElement
  const containerRect = container.getBoundingClientRect()
  const firstCenter = first.getBoundingClientRect().left + first.offsetWidth / 2 - containerRect.left
  const lastCenter = last.getBoundingClientRect().left + last.offsetWidth / 2 - containerRect.left
  lineWidth.value = `${lastCenter - firstCenter}px`
  lineLeft.value = `${firstCenter}px`
}

const topLineStyle = computed(() => ({
  width: lineWidth.value,
  left: lineLeft.value,
}))

const bottomLineStyle = computed(() => ({
  width: lineWidth.value,
  left: lineLeft.value,
}))

onMounted(() => {
  nextTick(() => {
    updateLines()
    // 监听容器尺寸变化（PC ↔ 移动端切换 / 浏览器缩放 / 父容器 resize）
    // 重新计算 __top-line / __bottom-line 的 left + width，
    // 否则移动端切换后横线位置会"飘"出框外（视觉上乱）
    if (branchesRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => updateLines())
      resizeObserver.observe(branchesRef.value)
    }
  })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

watch(() => props.node.branches.length, () => {
  nextTick(updateLines)
})
</script>
