<template>
  <div class="ding-node-chain">
    <!-- 当前节点 -->
    <template v-if="isFork">
      <ParallelGroup
        :node="(node as DingForkNode)"
        :type-prefix="typePrefix"
        :viewer="viewer"
        :high-light="highLight"
        :theme="theme"
        :dnd-panel="dndPanel"
        :protected-ids="protectedIdsComputed"
        :can-delete-checker="canDeleteCheckerComputed"
        @edit="(n) => $emit('edit', n)"
        @delete="(n) => $emit('delete', n)"
        @add="(nodeType, parentNode) => $emit('add', nodeType, parentNode)"
        @add-branch="(n) => $emit('add-branch', n)"
        @edit-branch="(b) => $emit('edit-branch', b)"
        @add-to-branch="(nodeType, b) => $emit('add-to-branch', nodeType, b)"
      />
    </template>
    <template v-else-if="isCondition">
      <ConditionGroup
        :node="(node as DingConditionNode)"
        :type-prefix="typePrefix"
        :viewer="viewer"
        :high-light="highLight"
        :theme="theme"
        :dnd-panel="dndPanel"
        :protected-ids="protectedIdsComputed"
        :can-delete-checker="canDeleteCheckerComputed"
        @edit="(n) => $emit('edit', n)"
        @delete="(n) => $emit('delete', n)"
        @add="(nodeType, parentNode) => $emit('add', nodeType, parentNode)"
        @add-branch="(n) => $emit('add-branch', n)"
        @edit-branch="(b) => $emit('edit-branch', b)"
        @add-to-branch="(nodeType, b) => $emit('add-to-branch', nodeType, b)"
      />
    </template>
    <template v-else>
      <NodeCard
        :node="node"
        :type-prefix="typePrefix"
        :viewer="viewer"
        :high-light="highLight"
        :theme="theme"
        :depth="depth"
        :can-delete="canDelete(node)"
        @edit="(n) => $emit('edit', n)"
        @delete="(n) => $emit('delete', n)"
      />
    </template>

    <!-- 添加按钮（非 end 节点后面才有；fork 容器内自带 joinChildren 渲染，不再此处加按钮）
         start 节点后不可插入新节点（readonly 模式：仅短连接线，无 + 圆） -->
    <AddButton
      v-if="!isFork && baseType !== 'end'"
      :viewer="viewer"
      :type-prefix="typePrefix"
      :dnd-panel="dndPanel"
      :readonly="baseType === 'start'"
      :prev-node-id="node.id"
      :next-node-id="node.children?.id"
      :high-light="highLight"
      @add="(nodeType) => $emit('add', nodeType, node)"
    />

    <!-- fork 容器自己负责渲染 joinChildren 之后的链；条件/普通节点走 children 递归 -->
    <NodeChain
      v-if="!isFork && node.children"
      :node="node.children"
      :type-prefix="typePrefix"
      :viewer="viewer"
      :high-light="highLight"
      :theme="theme"
      :dnd-panel="dndPanel"
      :depth="depth + 1"
      :protected-ids="protectedIdsComputed"
      :can-delete-checker="canDeleteCheckerComputed"
      @edit="(n) => $emit('edit', n)"
      @delete="(n) => $emit('delete', n)"
      @add="(nodeType, parentNode) => $emit('add', nodeType, parentNode)"
      @add-branch="(n) => $emit('add-branch', n)"
      @edit-branch="(b) => $emit('edit-branch', b)"
      @add-to-branch="(nodeType, b) => $emit('add-to-branch', nodeType, b)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DingNode, DingConditionNode, DingForkNode, DingBranch } from '../types'
import { isConditionNode, isForkNode } from '../types'
import type { FDHighLightType, FDThemeConfig, FDPatternItem } from '../../types'
import NodeCard from './NodeCard.vue'
import AddButton from './AddButton.vue'
import ConditionGroup from './ConditionGroup.vue'
import ParallelGroup from './ParallelGroup.vue'

interface Props {
  node: DingNode
  typePrefix: string
  viewer: boolean
  highLight?: FDHighLightType
  theme?: FDThemeConfig
  dndPanel?: FDPatternItem[]
  /** 受保护节点 ID 集合（来自 DingTalkDesigner，用于隐藏 start/end/firstChild 的删除按钮） */
  protectedIds?: Set<string>
  /** 节点是否可删除检查器（false 时隐藏 × 按钮；默认全部可删除） */
  canDeleteChecker?: (node: DingNode) => boolean
  /** 节点深度（0=start, 1=第一个任务=申请人, >=2=审批人） */
  depth?: number
}

const props = withDefaults(defineProps<Props>(), {
  protectedIds: () => new Set<string>(),
  depth: 0
})

// 兜底：props 是只读的，统一通过 protectedIdsComputed 访问，避免 undefined 调用 .has
const protectedIdsComputed = computed(() => props.protectedIds ?? new Set<string>())
const canDeleteCheckerComputed = computed(
  () => props.canDeleteChecker ?? ((_n: DingNode) => true)
)

function canDelete(node: DingNode): boolean {
  if (protectedIdsComputed.value.has(node.id)) return false
  if (!canDeleteCheckerComputed.value(node)) return false
  return true
}

defineEmits<{
  (e: 'edit', node: DingNode): void
  (e: 'delete', node: DingNode): void
  (e: 'add', nodeType: string, parentNode: DingNode | null): void
  (e: 'add-branch', node: DingNode): void
  (e: 'edit-branch', branch: DingBranch): void
  (e: 'add-to-branch', nodeType: string, branch: DingBranch): void
}>()

const isCondition = computed(() => isConditionNode(props.node))
const isFork = computed(() => isForkNode(props.node))

const baseType = computed(() => {
  if (isCondition.value) return 'condition'
  if (isFork.value) return 'fork'
  return props.node.type.replace(props.typePrefix, '')
})
</script>
