<template>
  <div class="ding-branch-col">
    <!-- 分支顶部竖线 -->
    <div class="ding-branch-col__line-top"></div>
    <!-- 分支名称 -->
    <div class="ding-branch-col__head" v-if="branch.name || !viewer" :title="branch.name || '点击编辑'" @click="handleEditBranch">
      <span class="ding-branch-col__head-text">{{ branch.name || '未命名' }}</span>
      <span class="ding-branch-col__head-edit" v-if="!viewer" title="编辑分支">
        &#x270E;
      </span>
    </div>
    <!-- 分支内容区（节点链） -->
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
        <!-- 空分支的添加按钮 -->
        <AddButton
          :viewer="viewer"
          :type-prefix="typePrefix"
          :dnd-panel="dndPanel"
          @add="(nodeType) => $emit('add-to-branch', nodeType, branch)"
        />
      </template>
    </div>
    <!-- 分支底部竖线 -->
    <div class="ding-branch-col__line-bottom"></div>
  </div>
</template>

<script setup lang="ts">
import type { DingBranch, DingNode } from '../types'
import type { FDHighLightType, FDThemeConfig, FDPatternItem } from '../../types'
import AddButton from './AddButton.vue'
import NodeChain from './NodeChain.vue'

const props = defineProps<{
  branch: DingBranch
  typePrefix: string
  viewer: boolean
  highLight?: FDHighLightType
  theme?: FDThemeConfig
  dndPanel?: FDPatternItem[]
  /** 节点是否可删除检查器（false 时隐藏 × 按钮；默认全部可删除） */
  canDeleteChecker?: (node: DingNode) => boolean
}>()

const emit = defineEmits<{
  (e: 'edit', node: DingNode): void
  (e: 'delete', node: DingNode): void
  (e: 'add', nodeType: string, parentNode: DingNode | null): void
  (e: 'add-branch', node: DingNode): void
  (e: 'edit-branch', branch: DingBranch): void
  (e: 'add-to-branch', nodeType: string, branch: DingBranch): void
}>()

function handleEditBranch() {
  if (props.viewer) return
  emit('edit-branch', props.branch)
}
</script>
