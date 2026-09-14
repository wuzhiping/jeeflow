<template>
  <div class="ding-condition-group ding-parallel-group">
    <!-- 分组头部 -->
    <div class="ding-condition-group__header">
      <span class="ding-condition-group__title">并行分支</span>
      <span
        v-if="!viewer"
        class="ding-condition-group__add-branch"
        @click="$emit('add-branch', node)"
      >
        + 添加分支
      </span>
      <button
        v-if="!viewer && !protectedIdsComputed.has(node.id)"
        class="ding-condition-group__delete"
        title="删除整个并行分支组"
        @click="$emit('delete', node)"
      >&times;</button>
    </div>
    <!-- 多个独立分支链（每条是 DingBranch，分支的 children 是 DingNode 链） -->
    <div class="ding-condition-group__branches" ref="branchesRef">
      <div class="ding-condition-group__top-line" :style="topLineStyle"></div>
      <div
        v-for="(branch, index) in node.branches"
        :key="branch.id"
        class="ding-branch-col"
      >
        <!-- 分支顶部竖线 -->
        <div class="ding-branch-col__line-top"></div>
        <!-- 分支编号（并行分支无需命名，仅做位置标识，避免与条件分支的'未命名'混淆） -->
        <div class="ding-branch-col__head ding-branch-col__head--static" v-if="!viewer">
          <span class="ding-branch-col__head-text">分支 {{ index + 1 }}</span>
        </div>
        <!-- 分支内容区（节点链 / 空分支占位） -->
        <div class="ding-branch-col__content">
          <template v-if="branch.children">
            <NodeChain
              :node="branch.children"
              :type-prefix="typePrefix"
              :viewer="viewer"
              :high-light="highLight"
              :theme="theme"
              :dnd-panel="dndPanel"
              :can-delete-checker="canDeleteChecker"
              @edit="(n) => $emit('edit', n)"
              @delete="(n) => $emit('delete', n)"
              @add="(nodeType, parentNode) => $emit('add', nodeType, parentNode)"
              @add-branch="(n) => $emit('add-branch', n)"
              @edit-branch="(b) => $emit('edit-branch', b)"
            />
          </template>
          <template v-else>
            <!-- 空分支：显示 + 按钮 + 提示文字，发 add-to-branch 让父组件把任务写入 branch.children -->
            <div class="ding-branch-col__empty" v-if="!viewer">
              <div class="ding-branch-col__empty-hint">点击 + 添加任务节点</div>
              <AddButton
                :viewer="viewer"
                :type-prefix="typePrefix"
                :dnd-panel="dndPanel"
                @add="(nodeType) => $emit('add-to-branch', nodeType, branch)"
              />
            </div>
          </template>
        </div>
        <div class="ding-branch-col__line-bottom"></div>
      </div>
      <div class="ding-condition-group__bottom-line" :style="bottomLineStyle"></div>
    </div>
    <!-- join 之后的节点（继续走 NodeChain） -->
    <div class="ding-line-vertical" v-if="node.joinChildren"></div>
    <NodeChain
      v-if="node.joinChildren"
      :node="node.joinChildren"
      :type-prefix="typePrefix"
      :viewer="viewer"
      :high-light="highLight"
      :theme="theme"
      :dnd-panel="dndPanel"
      :can-delete-checker="canDeleteChecker"
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import type { DingNode, DingForkNode, DingBranch } from '../types'
import type { FDHighLightType, FDThemeConfig, FDPatternItem } from '../../types'
import NodeChain from './NodeChain.vue'
import AddButton from './AddButton.vue'

const props = withDefaults(defineProps<{
  node: DingForkNode
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

const emit = defineEmits<{
  (e: 'edit', node: DingNode): void
  (e: 'delete', node: DingNode): void
  (e: 'add', nodeType: string, parentNode: DingNode | null): void
  (e: 'add-branch', node: DingNode): void
  (e: 'edit-branch', branch: DingBranch): void
  (e: 'add-to-branch', nodeType: string, branch: DingBranch): void
}>()

const branchesRef = ref<HTMLElement>()
const lineWidth = ref('0px')
const lineLeft = ref('0px')

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
  nextTick(updateLines)
})

watch(() => props.node.branches.length, () => {
  nextTick(updateLines)
})
</script>

<style lang="scss" scoped>
.ding-parallel-group {
  // 让并行分支组占满卡片宽度（区别于条件组的列内紧凑布局）
  .ding-condition-group__branches {
    width: 100%;
    justify-content: center;
  }
}
</style>
