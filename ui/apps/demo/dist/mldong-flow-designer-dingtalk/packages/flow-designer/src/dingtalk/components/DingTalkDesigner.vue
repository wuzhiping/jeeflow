<template>
  <div class="ding-designer" :style="containerStyle" @contextmenu.prevent="handleContextmenu">
    <!-- 控制面板（注入缩放/适应等画布工具） -->
    <ControlPanel
      :init-control="initControl"
      :control="computedControlItems"
      :viewer="viewer"
      @save="handleControlSave"
      @clear="handleControlClear"
      @view-data="handleControlViewData"
      @import-data="handleControlImportData"
      @fullscreen="handleControlFullscreen"
    />
    <div
      class="ding-designer__canvas"
      :class="{ 'is-dragging': isDragging, 'is-touch-dragging': isTouchDragging, 'is-pinching': isPinching }"
      ref="canvasRef"
      @wheel="handleWheel"
      @mousedown="handleCanvasMouseDown"
      @touchstart.passive="handleTouchStart"
      @touchmove.passive="handleTouchMove"
      @touchend.passive="handleTouchEnd"
      @touchcancel.passive="handleTouchEnd"
    >
      <div
        class="ding-designer__viewport"
        :style="viewportStyle"
        @mousedown="handleViewportMouseDown"
      >
        <NodeChain
          v-if="treeData"
          :node="treeData"
          :type-prefix="typePrefix"
          :viewer="viewer"
          :high-light="highLight"
          :theme="theme"
          :dnd-panel="computedDndPanel"
          :protected-ids="protectedIds"
          :can-delete-checker="canDeleteNode"
          @edit="handleEditNode"
          @delete="handleDeleteNode"
          @add="handleAddNode"
          @add-branch="handleAddBranch"
          @edit-branch="handleEditBranch"
          @add-to-branch="handleAddToBranch"
        />
        <!-- viewer 空状态：仅提示 -->
        <div v-else class="ding-empty">
          <div class="ding-empty__title">暂无流程数据</div>
        </div>
      </div>
    </div>
    <!-- 节点/分支编辑抽屉 -->
    <FDDrawer
      :visible="showEditPanel"
      :title="editPanelTitle"
      width="600px"
      :show-footer="false"
      @cancel="cancelEditPanel"
    >
      <FDSchemaForm :form-items="editFormFields" :model="editFormData" label-width="120px" />
    </FDDrawer>
    <!-- 查看数据弹窗 -->
    <FDModal
      v-model:visible="showDataModal"
      title="流程数据"
      cancel-text="关闭"
      ok-text="复制"
      @ok="copyData"
      @cancel="showDataModal = false"
      width="600px"
    >
      <div class="ding-modal__json">
        <FDJsonViewer :showLineNumber="true" :data="viewDataObj" />
      </div>
    </FDModal>

    <!-- 导入数据弹窗 -->
    <FDModal
      v-model:visible="showImportModal"
      title="导入流程数据"
      @ok="doImport"
      @cancel="showImportModal = false"
      width="600px"
    >
      <FDTextarea class="ding-modal__textarea" v-model="importDataJson" placeholder="请粘贴 JSON 数据"></FDTextarea>
      <div v-if="importError" class="ding-modal__error">{{ importError }}</div>
    </FDModal>

    <!-- 流程属性抽屉（与画布模式一致：无确认/取消，修改即生效，关闭时提交 emit） -->
    <FDDrawer
      :visible="showProcessDrawer"
      title="流程属性"
      width="600px"
      :show-footer="false"
      @cancel="closeProcessDrawer"
    >
      <FDSchemaForm :form-items="processFormFields" :model="processFormData" label-width="130px" />
    </FDDrawer>
    </div>
  </template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onBeforeUnmount, onMounted, PropType } from 'vue'
import type { FDConfigData, FDThemeConfig, FDHighLightType, FDPatternItem, FDControlItem, FDFormType, FDFormItemType } from '../../types'
import type { DingNode, DingConditionNode, DingBranch, DingForkNode, GraphNode, GraphEdge } from '../types'
import { isConditionNode, isForkNode } from '../types'
import type { FDDesignerAPI, FDEventName, FDNodeData, FDGraphModelProxy, DingNodeEventParams, DingEdgeEventParams } from '../types/api'
import { findNode, flattenNodes } from '../types/api'
import { graphToTree, treeToGraph } from '../utils/converter'
import { DEFAULT_FLOW_NODES, DEFAULT_FLOW_EDGES } from '../data/default-flow'
import NodeChain from './NodeChain.vue'
import ControlPanel from './ControlPanel.vue'
import { FDModal, FDDrawer, FDTextarea, FDSchemaForm, FDJsonViewer, FDMessage } from '../../ui/fd'
import * as schema from '../../plugins/schema'
import '../styles/dingtalk.scss'

const props = defineProps({
  value: {
    type: Object as PropType<FDConfigData>,
    default: () => ({})
  },
  theme: {
    type: Object as PropType<FDThemeConfig>,
    default: () => ({})
  },
  highLight: {
    type: Object as PropType<FDHighLightType>,
    default: () => ({})
  },
  viewer: {
    type: Boolean,
    default: false
  },
  dndPanel: {
    type: Array as PropType<FDPatternItem[]>,
    default: () => []
  },
  processForm: {
    type: Object as PropType<FDFormType>
  },
  edgeForm: {
    type: Object as PropType<FDFormType>
  },
  nodeClick: {
    type: Function
  },
  edgeClick: {
    type: Function
  },
  blankContextmenu: {
    type: Function
  },
  initControl: {
    type: Boolean,
    default: true
  },
  control: {
    type: Array as PropType<FDControlItem[]>
  },
  drawerWidth: {
    type: [String, Number] as PropType<string | number>,
    default: '600px'
  },
  modalWidth: {
    type: [String, Number] as PropType<string | number>,
    default: '60%'
  },
  typePrefix: {
    type: String,
    default: 'snaker:'
  },
  defaultEdgeType: {
    type: String,
    default: 'snaker:transition'
  }
})

const emit = defineEmits<{
  (e: 'update:value', data: FDConfigData): void
  (e: 'node-click', params: DingNodeEventParams): void
  (e: 'edge-click', params: DingEdgeEventParams): void
  (e: 'edit-branch', branch: DingBranch): void
  (e: 'save', data: FDConfigData): void
  (e: 'on-init', api: FDDesignerAPI): void
  (e: 'on-render', api: FDDesignerAPI): void
}>()

// ─── 默认面板项 ─────────────────────────────────────────────────────────
const defaultDndPanelItems: FDPatternItem[] = [
  { type: 'task', text: '审批人', label: '审批人' },
  { type: 'custom', text: '自定义节点', label: '自定义节点' },
  { type: 'subProcess', text: '子流程', label: '子流程' },
]

const computedDndPanel = computed<FDPatternItem[]>(() => {
  // 合并业务方自定义项 + 默认项，业务方同名 type 优先（保留 nodeClick 等自定义配置）
  const custom = props.dndPanel || []
  const merged = [...defaultDndPanelItems]
  for (const item of custom) {
    const idx = merged.findIndex(m => m.type === item.type || m.type === item.type?.replace(props.typePrefix, ''))
    if (idx >= 0) {
      merged[idx] = { ...merged[idx], ...item }
    } else {
      merged.push(item)
    }
  }
  return merged
})

// 树形数据
const treeData = ref<DingNode | undefined>(undefined)

/**
 * 受保护节点 ID 集合（不允许删除）
 * - 开始节点（snaker:start）
 * - 结束节点（snaker:end）—— 渲染在顶层链末端
 * - 顶层第一个申请节点（start 的直接子节点）—— 钉钉模式默认链路的第一个节点
 */
const protectedIds = computed<Set<string>>(() => {
  const ids = new Set<string>()
  if (!treeData.value) return ids
  // 开始节点
  const baseType = treeData.value.type.replace(props.typePrefix, '')
  if (baseType === 'start') ids.add(treeData.value.id)
  // 顶层第一个子节点（第一个审批节点）
  const firstChild = treeData.value.children
  if (firstChild) ids.add(firstChild.id)
  // 找结束节点（递归找 snaker:end）
  const endId = findEndNodeId(treeData.value)
  if (endId) ids.add(endId)
  return ids
})

/** 在树中查找 snaker:end 节点 id */
function findEndNodeId(node: DingNode | undefined): string | null {
  if (!node) return null
  const baseType = node.type.replace(props.typePrefix, '')
  if (baseType === 'end') return node.id
  if (isConditionNode(node)) {
    for (const branch of node.branches) {
      if (branch.children) {
        const id = findEndNodeId(branch.children)
        if (id) return id
      }
    }
  }
  if (isForkNode(node)) {
    for (const branch of node.branches) {
      if (branch.children) {
        const id = findEndNodeId(branch.children)
        if (id) return id
      }
    }
    if (node.joinChildren) {
      const id = findEndNodeId(node.joinChildren)
      if (id) return id
    }
  }
  // fork 容器无 children 字段（用 branches/joinChildren），'children' in 收窄普通节点/条件容器
  if ('children' in node && node.children) {
    return findEndNodeId(node.children)
  }
  return null
}

// 编辑分支时记录父节点类型（condition/fork）
const editingBranchType = ref<'condition' | 'fork' | null>(null)

// 内部标记，避免 watch 循环
let isInternalUpdate = false

// ─── 画布平移/缩放状态 ──────────────────────────────────────────
const transform = reactive({ scale: 1, x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = { x: 0, y: 0, originX: 0, originY: 0 }
const canvasRef = ref<HTMLElement | null>(null)

// ─── 触摸状态（移动端 pan + pinch zoom）─────────────────────
const isTouchDragging = ref(false)
const isPinching = ref(false)
const touchStart = {
  // 单指 pan
  x: 0, y: 0, originX: 0, originY: 0,
  // 双指 pinch
  distance: 0,
  centerX: 0, centerY: 0,
  originScale: 1,
}

// 缩放/适应与 ControlPanel 工具栏合并（统一到右侧图标组）
// 外部传入的 control 优先保留（可覆盖默认）
const computedControlItems = computed<Array<{ key: string; iconClass: string; title: string; text: string; sort?: number; onClick?: () => void }>>(() => {
  const ext = (props.control || []) as any[]
  // 缩放/适应按钮对编辑/查看场景都有用，editor + viewer 都默认带
  const zoomItems: any[] = [
    { key: 'ding-zoom-out', iconClass: 'ding-icon-zoom-out', title: '缩小流程图', text: '缩小', sort: 10, onClick: zoomOut },
    { key: 'ding-zoom-in',  iconClass: 'ding-icon-zoom-in',  title: '放大流程图', text: '放大', sort: 20, onClick: zoomIn  },
    { key: 'ding-fit',      iconClass: 'ding-icon-fit',      title: '恢复初始位置和尺寸', text: '适应', sort: 30, onClick: resetView },
  ]
  const merged = [...zoomItems]
  for (const e of ext) {
    const idx = merged.findIndex(m => m.key === e.key)
    if (idx >= 0) merged[idx] = { ...merged[idx], ...e }
    else merged.push(e)
  }
  return merged.sort((a, b) => (a.sort || 0) - (b.sort || 0))
})

const viewportStyle = computed(() => ({
  transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
  transformOrigin: '0 0',
}))

function zoomIn() { zoomBy(1.1) }
function zoomOut() { zoomBy(1 / 1.1) }
function zoomBy(factor: number) {
  const next = Math.min(2, Math.max(0.3, transform.scale * factor))
  // 以画布中心为缩放原点
  const canvas = canvasRef.value
  if (canvas) {
    const rect = canvas.getBoundingClientRect()
    const cx = rect.width / 2
    const cy = rect.height / 2
    // 当前点在画布坐标系中的位置 = (cx - x) / scale
    // 缩放后保持该点位置不变：newX = cx - (cx - x) * (next / scale)
    transform.x = cx - (cx - transform.x) * (next / transform.scale)
    transform.y = cy - (cy - transform.y) * (next / transform.scale)
  }
  transform.scale = next
}

function resetView() {
  transform.scale = 1
  transform.x = 0
  transform.y = 0
}

function handleWheel(e: WheelEvent) {
  // ctrl/cmd + wheel 缩放；普通 wheel 留给 AddButton / dnd panel
  if (!(e.ctrlKey || e.metaKey)) return
  e.preventDefault()
  const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1
  const canvas = canvasRef.value
  if (canvas) {
    const rect = canvas.getBoundingClientRect()
    const px = e.clientX - rect.left
    const py = e.clientY - rect.top
    const next = Math.min(2, Math.max(0.3, transform.scale * factor))
    transform.x = px - (px - transform.x) * (next / transform.scale)
    transform.y = py - (py - transform.y) * (next / transform.scale)
    transform.scale = next
  }
}

function handleCanvasMouseDown(e: MouseEvent) {
  // 仅中键/空白处左键启动拖动；AddButton / NodeCard 上的 mousedown 不启动拖动
  if (e.button !== 0 && e.button !== 1) return
  const target = e.target as HTMLElement
  // 拖动起点：画布空白处、viewport（内容上空白处），但不在控件/按钮/卡片上
  if (target.closest('.ding-node-card, button, .ding-edit-panel, .ding-modal, .ding-designer__zoom-controls, .ding-branch-col__head, .ding-condition-group__title, .ding-add-button')) {
    return
  }
  startDrag(e)
}

function handleViewportMouseDown(e: MouseEvent) {
  if (e.button !== 0 && e.button !== 1) return
  const target = e.target as HTMLElement
  if (target.closest('.ding-node-card, button, .ding-edit-panel, .ding-modal, .ding-designer__zoom-controls, .ding-branch-col__head, .ding-condition-group__title, .ding-add-button')) {
    return
  }
  startDrag(e)
}

function startDrag(e: MouseEvent) {
  isDragging.value = true
  dragStart.x = e.clientX
  dragStart.y = e.clientY
  dragStart.originX = transform.x
  dragStart.originY = transform.y
  document.addEventListener('mousemove', handleDocumentMouseMove)
  document.addEventListener('mouseup', handleDocumentMouseUp)
}

function handleDocumentMouseMove(e: MouseEvent) {
  if (!isDragging.value) return
  transform.x = dragStart.originX + (e.clientX - dragStart.x)
  transform.y = dragStart.originY + (e.clientY - dragStart.y)
}

function handleDocumentMouseUp() {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDocumentMouseMove)
  document.removeEventListener('mouseup', handleDocumentMouseUp)
}

/** 是否在拖动起点命中"控件类"元素（按钮、卡片等），避免误拖 */
function shouldIgnoreTouchStart(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null
  if (!el) return false
  return !!el.closest('.ding-node-card, button, .ding-edit-panel, .ding-modal, .ding-designer__zoom-controls, .ding-branch-col__head, .ding-condition-group__title, .ding-add-button')
}

function getTouchDistance(t1: Touch, t2: Touch): number {
  const dx = t1.clientX - t2.clientX
  const dy = t1.clientY - t2.clientY
  return Math.hypot(dx, dy)
}

function getTouchCenter(t1: Touch, t2: Touch): { x: number; y: number } {
  return { x: (t1.clientX + t2.clientX) / 2, y: (t1.clientY + t2.clientY) / 2 }
}

function handleTouchStart(e: TouchEvent) {
  // 命中控件元素时不启动 pan（按钮等保留原生 tap 行为）
  if (shouldIgnoreTouchStart(e.target)) return
  if (e.touches.length === 1) {
    // 单指 pan
    const t = e.touches[0]
    isTouchDragging.value = true
    touchStart.x = t.clientX
    touchStart.y = t.clientY
    touchStart.originX = transform.x
    touchStart.originY = transform.y
  } else if (e.touches.length === 2) {
    // 双指 pinch zoom
    const [t1, t2] = [e.touches[0], e.touches[1]]
    isPinching.value = true
    isTouchDragging.value = false
    touchStart.distance = getTouchDistance(t1, t2)
    touchStart.originScale = transform.scale
    const center = getTouchCenter(t1, t2)
    touchStart.centerX = center.x
    touchStart.centerY = center.y
  }
}

function handleTouchMove(e: TouchEvent) {
  // 双指 pinch
  if (e.touches.length === 2 && isPinching.value) {
    const [t1, t2] = [e.touches[0], e.touches[1]]
    const dist = getTouchDistance(t1, t2)
    if (touchStart.distance > 0) {
      const factor = dist / touchStart.distance
      const next = Math.min(2, Math.max(0.3, touchStart.originScale * factor))
      const canvas = canvasRef.value
      if (canvas) {
        const rect = canvas.getBoundingClientRect()
        // 把屏幕坐标转成画布坐标
        const px = touchStart.centerX - rect.left
        const py = touchStart.centerY - rect.top
        // 缩放：以双指中心为原点，保持该点屏幕坐标不变
        transform.x = px - (px - transform.x) * (next / transform.scale)
        transform.y = py - (py - transform.y) * (next / transform.scale)
        transform.scale = next
      }
    }
    return
  }
  // 单指 pan
  if (e.touches.length === 1 && isTouchDragging.value) {
    const t = e.touches[0]
    transform.x = touchStart.originX + (t.clientX - touchStart.x)
    transform.y = touchStart.originY + (t.clientY - touchStart.y)
  }
}

function handleTouchEnd(e: TouchEvent) {
  if (e.touches.length === 0) {
    // 所有手指抬起
    isTouchDragging.value = false
    isPinching.value = false
  } else if (e.touches.length === 1 && isPinching.value) {
    // 从双指变成单指，重置 pan 起点
    const t = e.touches[0]
    isPinching.value = false
    isTouchDragging.value = true
    touchStart.x = t.clientX
    touchStart.y = t.clientY
    touchStart.originX = transform.x
    touchStart.originY = transform.y
  }
}

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', handleDocumentMouseMove)
  document.removeEventListener('mouseup', handleDocumentMouseUp)
})

/** 递归查找分支所属的父节点类型 */
function findBranchParentType(node: DingNode, branchId: string): 'condition' | 'fork' | null {
  if (isConditionNode(node)) {
    if (node.branches.some(b => b.id === branchId)) {
      return 'condition'
    }
    for (const branch of node.branches) {
      if (branch.children) {
        const found = findBranchParentType(branch.children, branchId)
        if (found) return found
      }
    }
  }
  if (isForkNode(node)) {
    if (node.branches.some(b => b.id === branchId)) {
      return 'fork'
    }
    for (const branch of node.branches) {
      if (branch.children) {
        const found = findBranchParentType(branch.children, branchId)
        if (found) return found
      }
    }
  }
  if (node.children) {
    return findBranchParentType(node.children, branchId)
  }
  return null
}

/** 是否已初始化过默认三节点（防止外部空数据触发重复初始化） */
let defaultFlowInitialized = false

/** 从 graph 数据转为树 */
function convertToTree() {
  const nodes = props.value?.nodes || []
  const edges = props.value?.edges || []
  const tree = graphToTree(nodes as GraphNode[], edges as GraphEdge[], props.typePrefix)
  if (tree) {
    treeData.value = tree
  } else if (!props.viewer && !defaultFlowInitialized) {
    // 空流程数据（编辑模式）：初始化默认三节点 开始 → 审批人 → 结束，仅首次
    defaultFlowInitialized = true
    initDefaultFlow()
  }
  // tree 为空且已初始化过：保持现有 treeData 不变（防止外部空数据覆盖已初始化的默认流程）
}

/**
 * 初始化默认流程：start → task → end 三个节点
 * 使用标准图数据（DEFAULT_FLOW_NODES/EDGES，与演示 wf-leave.json 同构），
 * 通过 graphToTree 走标准转换链路，保证数据结构与业务格式一致。
 * 注：不 emit update:value，初始化只作为内部状态；
 *     用户后续编辑/保存时由 syncToGraph 将完整数据回写外部 v-model
 */
function initDefaultFlow() {
  treeData.value = graphToTree(DEFAULT_FLOW_NODES, DEFAULT_FLOW_EDGES, props.typePrefix)
}

/** 从树转回 graph 数据并 emit */
function syncToGraph() {
  const graphData = treeToGraph(treeData.value, props.typePrefix)
  const newValue: FDConfigData = {
    ...props.value,
    nodes: graphData.nodes,
    edges: graphData.edges,
    mode: 'dingtalk',
  }
  isInternalUpdate = true
  emit('update:value', newValue)
  // 触发 update:graphData 事件（业务方可通过 api.eventCenter.on 订阅）
  eventCenter.emit('update:graphData', newValue)
}

// ─── 事件总线（与画布模式 lf.eventCenter 兼容命名）────────────────────
const eventHandlers: Record<string, Array<(data?: any) => void>> = reactive({})
const eventCenter = {
  emit(event: FDEventName, data?: any) {
    const handlers = eventHandlers[event] || []
    handlers.forEach(h => h(data))
  },
  on(event: FDEventName, handler: (data?: any) => void) {
    if (!eventHandlers[event]) eventHandlers[event] = []
    eventHandlers[event].push(handler)
  },
  off(event: FDEventName, handler: (data?: any) => void) {
    const handlers = eventHandlers[event] || []
    const idx = handlers.indexOf(handler)
    if (idx >= 0) handlers.splice(idx, 1)
  }
}

// 初始转换（需在 eventCenter 定义后执行，initDefaultFlow → syncToGraph 依赖它）
convertToTree()

// ─── 节点/流程数据 ↔ 业务方感知格式转换 ────────────────────────────

/**
 * 把 DingTree 内部 type 转换成业务方感知的完整 type（带 prefix）
 *
 * 钉钉内部表示（无 prefix）：
 *   - 'condition' → 画布模式为 'snaker:decision'（注意：不是 condition！）
 *   - 'fork'      → 画布模式为 'snaker:fork'
 *
 * DingNode 自带的 type 通常已带 prefix（'snaker:task' / 'snaker:start' / 'snaker:join'），
 * 这里只对内部表示做映射，对已有 prefix 的原样返回。
 */
function normalizeNodeType(rawType: string): string {
  const prefix = props.typePrefix
  if (rawType === 'condition') return `${prefix}decision`
  if (rawType === 'fork') return `${prefix}fork`
  if (rawType === 'join') return `${prefix}join`
  // 其他类型（task/start/end/custom/subProcess 等）通常已带 prefix，原样返回
  if (rawType.startsWith(prefix)) return rawType
  // 兜底：未识别的内部表示，自动补 prefix（保守做法）
  return `${prefix}${rawType}`
}

function nodeToFDData(node: DingNode): FDNodeData {
  return {
    id: node.id,
    type: normalizeNodeType(node.type),
    text: { value: node.name },
    properties: node.properties || {}
  }
}

function findByIdOrName(idOrName: string): DingNode | null {
  return findNode(treeData.value, (n) =>
    n.id === idOrName || n.properties?.name === idOrName
  )
}

// ─── 公开 API（与画布模式 lf 实例兼容命名）────────────────────────────
function _resolveNode(id: string, allowFallback: boolean): DingNode | null {
  if (!treeData.value) return null
  const found = findByIdOrName(id)
  if (found) return found
  // base-form 习惯用 properties.name 作 key；如果传入的不是 id 但匹配 name 也能找到
  if (allowFallback) {
    return findNode(treeData.value, (n) => n.properties?.name === id)
  }
  return null
}

const designerApi: FDDesignerAPI = {
  // ── 查询 ──
  getNodeDataById(id: string) {
    if (props.viewer) return null
    const n = findNode(treeData.value, (x) => x.id === id)
    return n ? nodeToFDData(n) : null
  },
  getNodeDataByName(name: string) {
    if (props.viewer) return null
    const n = findNode(treeData.value, (x) => x.properties?.name === name)
    return n ? nodeToFDData(n) : null
  },
  getAllNodes() {
    return flattenNodes(treeData.value).map(nodeToFDData)
  },
  getProperties(id: string) {
    // 只读查询，viewer 模式也允许（对齐 canvas 模式 lf.getProperties 语义）
    const n = _resolveNode(id, true)
    return n ? { ...n.properties } : {}
  },

  // ── 更新 ──
  updateText(id: string, text: string) {
    // viewer 模式允许 updateText：业务方通过 assigneeTextData 回显参与人名称
    const n = _resolveNode(id, true)
    if (n) n.name = text
    syncToGraph()
  },
  changeNodeId(oldId: string, newId: string) {
    if (props.viewer) return false
    const n = findNode(treeData.value, (x) => x.id === oldId)
    if (!n) return false
    n.id = newId
    // 同步 properties.name（base-form 习惯）
    n.properties = { ...n.properties, name: newId }
    syncToGraph()
    return true
  },
  setProperties(id: string, props: Record<string, any>) {
    if (props.viewer) return
    const n = _resolveNode(id, true)
    if (n) n.properties = { ...n.properties, ...props }
    syncToGraph()
  },
  deleteProperty(id: string, key: string) {
    if (props.viewer) return
    const n = _resolveNode(id, true)
    if (n && n.properties && key in n.properties) {
      const next = { ...n.properties }
      delete next[key]
      n.properties = next
    }
    syncToGraph()
  },

  // ── 流程属性（v-model.value） ──
  setProcessProperty(key: string, value: any) {
    if (props.viewer) return
    const newValue: FDConfigData = { ...props.value, [key]: value }
    isInternalUpdate = true
    emit('update:value', newValue)
    eventCenter.emit('update:graphModel', newValue)
  },

  // ── 导出/重渲染 ──
  getGraphData() {
    const graphData = treeToGraph(treeData.value, props.typePrefix)
    return {
      ...props.value,
      nodes: graphData.nodes,
      edges: graphData.edges,
      mode: 'dingtalk',
    }
  },
  render(data: FDConfigData) {
    isInternalUpdate = true
    treeData.value = graphToTree((data?.nodes || []) as GraphNode[], (data?.edges || []) as GraphEdge[], props.typePrefix)
    isInternalUpdate = false
    // 重渲染后 emit 一次 update:value 保持 v-model 同步
    syncToGraph()
    eventCenter.emit('update:graphData', data)
  },

  // ── 高亮 ──
  setHighlight(data: FDHighLightType) {
    eventCenter.emit('update:highlight', data)
  },

  // ── 事件总线 ──
  eventCenter,

  // ── graphModel 代理（与画布模式 lf.graphModel 兼容） ──
  // 业务方 vben5 process-drawer.vue 的写法：
  //   lfInstance.graphModel[key] = value
  //   lfInstance.graphModel.eventCenter.emit('update:graphModel', graphModel)
  // 在钉钉模式无需任何修改也能跑通
  graphModel: makeGraphModelProxy()
}

/**
 * 创建 graphModel Proxy 对象
 *
 * 设计要点：
 * - get: 从 props.value 读取，eventCenter 返回真实事件总线
 * - set: 把更新写入内部 _graphModelDraft 累积，每次 emit newValue = { ...props.value, ..._graphModelDraft }
 *        解决连续 set 时父组件 v-model 异步更新导致前几次 set 被覆盖的 bug
 * - watch props.value 变化时清空 draft（父组件 v-model 已应用完所有 pending 更新）
 */
let _graphModelDraft: Record<string, any> = {}

watch(() => props.value, () => {
  // 父组件 v-model 已更新：清空累积 draft（除非是内部 emit 触发的）
  if (!isInternalUpdate) {
    _graphModelDraft = {}
  }
})

function makeGraphModelProxy(): FDGraphModelProxy {
  return new Proxy({} as any, {
    get(_target, key: string | symbol) {
      // eventCenter 字段返回真实事件总线（兼容 vben5 写法）
      if (key === 'eventCenter') return eventCenter
      // 优先读 draft（最新写入），再 fallback 到 props.value
      if ((key as string) in _graphModelDraft) return _graphModelDraft[key as string]
      return (props.value as any)?.[key as string]
    },
    set(_target, key: string | symbol, value: any) {
      // viewer 模式只读
      if (props.viewer) return true
      _graphModelDraft[key as string] = value
      // 用 props.value 基础 + draft 累积派生新值
      // 这样连续 set 时前几次的字段不会因为 props.value 还没异步更新而丢失
      const newValue: FDConfigData = { ...props.value, ..._graphModelDraft }
      isInternalUpdate = true
      emit('update:value', newValue)
      eventCenter.emit('update:graphModel', newValue)
      return true
    },
    has(_target, key: string | symbol) {
      return (
        key === 'eventCenter' ||
        (key as string) in _graphModelDraft ||
        (key as string) in (props.value || {})
      )
    }
  })
}

// 暴露给 defineExpose / 父组件 ref
defineExpose<FDDesignerAPI>(designerApi)

// 初始渲染完成时触发 on-init / on-render，让业务方拿到 api 实例
onMounted(() => {
  emit('on-init', designerApi)
  emit('on-render', designerApi)
})

// 监听外部数据变化
watch(() => props.value, () => {
  if (isInternalUpdate) {
    isInternalUpdate = false
    return
  }
  convertToTree()
}, { deep: true })

/** 容器样式（支持主题配置） */
const containerStyle = computed(() => {
  const style: Record<string, string> = {}
  if (props.theme?.backgroundColor) {
    style['--ding-bg-color'] = props.theme.backgroundColor
  }
  if (props.theme?.primaryColor) {
    style['--ding-primary-color'] = props.theme.primaryColor
  }
  if (props.theme?.activeColor) {
    style['--ding-active-color'] = props.theme.activeColor
  }
  if (props.theme?.historyColor) {
    style['--ding-history-color'] = props.theme.historyColor
  }
  return style
})

// ─── 节点操作 ─────────────────────────────────────────────────────────

let idCounter = 0

function generateId(): string {
  // 优先用 crypto.randomUUID 避免快速点击/嵌套条件下 ID 重复
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `ding_${crypto.randomUUID()}`
  }
  return `ding_${Date.now()}_${++idCounter}`
}

/**
 * 确保节点类型有正确前缀
 */
function ensureTypePrefix(type: string): string {
  if (!type) return type
  if (type.startsWith(props.typePrefix)) return type
  return `${props.typePrefix}${type}`
}

/**
 * 在指定节点后面添加新节点
 */
function handleAddNode(nodeType: string, afterNode: DingNode | null) {
  if (!treeData.value) return

  // 特殊类型：条件分支 / 并行分支
  if (nodeType === '__condition__') {
    insertConditionNode(afterNode)
    syncToGraph()
    return
  }
  if (nodeType === '__parallel__') {
    insertForkJoinPair(afterNode)
    syncToGraph()
    return
  }

  const fullType = ensureTypePrefix(nodeType)
  const newNode: DingNode = {
    id: generateId(),
    type: fullType,
    name: getDefaultName(fullType),
    properties: {},
  }

  if (afterNode) {
    // 在 afterNode 后插入 newNode
    insertAfter(treeData.value, afterNode.id, newNode)
  } else {
    // afterNode 为 null，需要在空分支中插入 — 由 BranchColumn 处理
    // 此场景由 DingTalkDesigner 外部逻辑覆盖
  }

  syncToGraph()
}

/**
 * 节点是否可删除检查器（用于控制 × 按钮显示）
 * - protectedIds（受保护节点）→ false
 * - willEmptyBranch（并行分支 2 条时删 task 让分支变空）→ false
 * - 条件分支允许空分支（直通路径），不拦截
 */
function canDeleteNode(node: DingNode): boolean {
  if (!treeData.value) return true
  if (protectedIds.value.has(node.id)) return false
  if (willEmptyBranch(treeData.value, node.id)) return false
  return true
}

/**
 * 删除节点（start/end 不允许删除）
 * - 普通节点：调用 removeNode 把 children 接到父节点
 * - 条件容器：调用 removeConditionContainerById 把容器的 children 接续到所在位置
 * - 并行容器：调用 removeForkContainerById 把 joinChildren 接续到所在位置
 *
 * 额外保护：
 * - 条件分支：允许空分支（直通路径），不拦截删除
 * - 并行分支（fork）只有 2 条分支时，禁止删除会让分支变空的 task（避免空并行）
 */
function handleDeleteNode(node: DingNode) {
  if (!treeData.value) return
  const baseType = node.type.replace(props.typePrefix, '')
  // 保护节点不允许删除：start / end / 顶层第一个申请节点
  if (protectedIds.value.has(node.id)) {
    // eslint-disable-next-line no-console
    console.warn('[DingTalkDesigner] 受保护节点不允许删除：', node.id)
    return
  }
  if (baseType === 'start' || baseType === 'end') return
  // 并行分支仅 2 条时禁止删 task（避免出现空并行）；条件分支允许空分支
  if (willEmptyBranch(treeData.value, node.id)) {
    // eslint-disable-next-line no-console
    console.warn('[DingTalkDesigner] 并行分支只有 2 条，不允许删除会让分支变空的任务：', node.id)
    return
  }
  if (isConditionNode(node)) {
    removeConditionContainerById(treeData.value, node.id)
  } else if (isForkNode(node)) {
    removeForkContainerById(treeData.value, node.id)
  } else {
    removeNode(treeData.value, node.id)
  }
  // 清理空 branch：仅当 branches > 2 时才删除空 branch
  cleanupEmptyBranches(treeData.value)
  syncToGraph()
}

/**
 * 检查删除 target 后是否会让某个 2 条分支的并行（fork）容器出现空分支
 * 即 target 是某 branch.children 的首节点且没有 children（删了就变空）
 *
 * 条件分支（condition）允许空分支（直通路径），不在此拦截；
 * 仅并行分支（fork）保留此约束，避免空并行路径。
 */
function willEmptyBranch(root: DingNode, targetId: string): boolean {
  function check(node: DingNode): boolean {
    // 条件分支：允许空分支（直通路径），仅递归检查嵌套
    if (isConditionNode(node)) {
      const cond = node as DingConditionNode
      for (const b of cond.branches) {
        if (b.children && check(b.children)) return true
      }
    }
    // 并行分支：保留原有约束（2 条时禁止删空）
    if (isForkNode(node)) {
      const fork = node as DingForkNode
      if (fork.branches.length === 2) {
        for (const branch of fork.branches) {
          if (
            branch.children &&
            branch.children.id === targetId &&
            !branch.children.children
          ) {
            return true
          }
        }
      }
      for (const b of fork.branches) {
        if (b.children && check(b.children)) return true
      }
      if (fork.joinChildren && check(fork.joinChildren)) return true
    }
    if (node.children) return check(node.children)
    return false
  }
  return check(root)
}

/**
 * 编辑节点 - 事件优先级: dndPanel.nodeClick > 全局 nodeClick > 默认编辑面板
 * viewer 模式：不触发任何编辑回调，与画布模式 index.vue 中
 *   eventCenter.on('node:click', e => { if (props.viewer === true) return }) 行为一致
 */
function handleEditNode(node: DingNode) {
  // viewer 模式下不打开任何编辑弹窗（与画布模式行为对齐）
  if (props.viewer) return

  const baseType = node.type.replace(props.typePrefix, '')
  // 从 dndPanel 匹配对应类型的配置项
  // 兼容两种 type 写法：'task'（去前缀）和 'snaker:task'（带前缀）
  const matchedPatternItem = computedDndPanel.value.find(
    (item: FDPatternItem) => item.type === baseType || item.type === node.type
  )

  // ⭐ 对齐画布模式 Flow.ts 中 eventCenter.on('node:click', e => nodeClick({...event, patternItem, lf})) 的签名
  // 业务方在两种模式下写 :node-click 拿到的对象结构完全一致
  const eventParams: DingNodeEventParams = {
    data: nodeToFDData(node),
    node,
    patternItem: matchedPatternItem,
    lf: designerApi
  }

  // 优先级1: dndPanel 中该类型的 nodeClick
  if (matchedPatternItem?.nodeClick && typeof matchedPatternItem.nodeClick === 'function') {
    matchedPatternItem.nodeClick(eventParams)
    return
  }

  // 优先级2: 全局 nodeClick prop
  if (props.nodeClick && typeof props.nodeClick === 'function') {
    props.nodeClick(eventParams)
    return
  }

  // 优先级3: 打开内置编辑面板
  editingBranch.value = null
  editingNode.value = node
  // 记住 dndPanel 自定义表单（优先于内置 schema，与画布模式 patternItem.form 一致）
  editingPatternForm.value = matchedPatternItem?.form
  editFormData.name = node.properties?.name || node.id
  editFormData.displayName = node.name || ''
  // 通用初始化：遍历当前表单字段从 properties 回填（含 schema defaultValue）
  for (const f of editFormFields.value) {
    if (f.name === 'name' || f.name === 'displayName') continue
    editFormData[f.name] = node.properties?.[f.name] ?? f.defaultValue ?? ''
  }

  // emit 与画布模式 lf.eventCenter.on('node:click') 拿到的签名一致，
  // 业务方在钉钉/画布模式下都能用 @node-click="(p) => {...}" 监听
  emit('node-click', eventParams)
}

/**
 * 编辑分支条件 - 事件优先级: 全局 edgeClick > 默认编辑面板
 */
function handleEditBranch(branch: DingBranch) {
  if (props.viewer) return

  // ⭐ 对齐画布模式 Flow.ts 中 eventCenter.on('edge:click', e => edgeClick({...event, patternItem, lf})) 的签名
  const eventParams: DingEdgeEventParams = {
    data: {
      id: branch.id,
      type: 'transition',
      text: { value: branch.name },
      properties: branch.properties || {}
    },
    edge: branch,
    patternItem: { form: props.edgeForm },
    lf: designerApi
  }

  // 优先级1: 全局 edgeClick prop
  if (props.edgeClick && typeof props.edgeClick === 'function') {
    props.edgeClick(eventParams)
    return
  }

  // 优先级2: 打开内置编辑面板
  editingNode.value = null
  editingBranch.value = branch
  // 查找分支父节点类型
  editingBranchType.value = treeData.value ? findBranchParentType(treeData.value, branch.id) : null
  editFormData.displayName = branch.name || ''
  editFormData.expr = branch.properties?.expr || ''
  editFormData.name = branch.properties?.name || branch.id

  // emit 与画布模式 edge:click 签名一致，业务方 @edge-click="(p) => {...}" 可监听
  emit('edge-click', eventParams)
}

/**
 * 添加条件/并行分支
 * - condition/fork：向 branches 追加 DingBranch，默认携带一个"审批人"任务节点（边+任务一起添加）
 */
function handleAddBranch(node: DingNode) {
  const taskType = ensureTypePrefix('task')
  const branchTask: DingNode = {
    id: generateId(),
    type: taskType,
    name: getDefaultName(taskType),
    properties: {},
  }
  if (isConditionNode(node)) {
    const condNode = node as DingConditionNode
    const newBranch: DingBranch = {
      id: generateId(),
      name: `条件${condNode.branches.length + 1}`,
      properties: {},
      children: branchTask,
    }
    condNode.branches.push(newBranch)
    syncToGraph()
    return
  }
  if (isForkNode(node)) {
    const forkNode = node as DingForkNode
    const newBranch: DingBranch = {
      id: generateId(),
      name: `分支${forkNode.branches.length + 1}`,
      properties: {},
      children: branchTask,
    }
    forkNode.branches.push(newBranch)
    syncToGraph()
  }
}

/**
 * 向空分支中添加节点
 */
function handleAddToBranch(nodeType: string, branch: DingBranch) {
  if (!treeData.value) return

  // 特殊类型：条件分支
  if (nodeType === '__condition__') {
    const condNode: DingConditionNode = {
      id: generateId(),
      type: 'condition',
      name: '',
      properties: {},
      branches: [
        { id: generateId(), name: '条件1', properties: {} },
        { id: generateId(), name: '条件2', properties: {} },
      ],
    }
    branch.children = condNode as unknown as DingNode
    syncToGraph()
    return
  }

  const fullType = ensureTypePrefix(nodeType)
  const newNode: DingNode = {
    id: generateId(),
    type: fullType,
    name: getDefaultName(fullType),
    properties: {},
  }
  branch.children = newNode
  syncToGraph()
}

// ─── 树操作工具函数 ────────────────────────────────────────────────────

/**
 * 在目标节点后面插入新节点
 */
function insertAfter(root: DingNode, targetId: string, newNode: DingNode): boolean {
  if (root.id === targetId) {
    // 将新节点插入：root -> newNode -> root.children
    newNode.children = root.children
    root.children = newNode
    return true
  }

  if (isConditionNode(root)) {
    const condNode = root as DingConditionNode
    for (const branch of condNode.branches) {
      if (branch.children && insertAfter(branch.children, targetId, newNode)) {
        return true
      }
    }
  }

  // 关键：fork 容器的 joinChildren 链也需要递归（join 节点也在此链中）
  if (isForkNode(root)) {
    const forkNode = root as DingForkNode
    // 1) fork 的每个分支的 children 链
    for (const branch of forkNode.branches) {
      if (branch.children && insertAfter(branch.children, targetId, newNode)) {
        return true
      }
    }
    // 2) fork 后的 joinChildren 链
    if (forkNode.joinChildren && insertAfter(forkNode.joinChildren, targetId, newNode)) {
      return true
    }
  }

  if (root.children) {
    return insertAfter(root.children, targetId, newNode)
  }

  return false
}

/**
 * 从树中移除指定节点（将其 children 接到父节点）
 * 关键边界：若 target 本身是条件/并行容器（嵌套），不能简单丢弃其 children，
 * 否则会丢失该容器内部的 branches 信息；改为把容器的 children（汇聚后的下一节点）接续上去。
 */
function removeNode(root: DingNode, targetId: string): boolean {
  // 场景 1：root.children 就是要删除的节点
  if (root.children && root.children.id === targetId) {
    const target = root.children
    // 条件容器或普通节点统一处理：把它的 children 接续到 root（条件容器时为汇聚后的下一节点）
    root.children = target.children
    return true
  }

  // 场景 2：条件容器的某个分支中
  if (isConditionNode(root)) {
    const condNode = root as DingConditionNode
    for (const branch of condNode.branches) {
      if (branch.children) {
        if (branch.children.id === targetId) {
          const target = branch.children
          // 嵌套条件容器：把容器的 children（汇聚后的下一节点）接续到分支
          // 普通节点：原逻辑接续其 children
          branch.children = target.children
          return true
        }
        if (removeNode(branch.children, targetId)) {
          return true
        }
      }
    }
  }

  // 场景 2b：fork 容器的某个分支或 joinChildren 链中
  if (isForkNode(root)) {
    const forkNode = root as DingForkNode
    for (const branch of forkNode.branches) {
      if (branch.children) {
        if (branch.children.id === targetId) {
          branch.children = branch.children.children
          return true
        }
        if (removeNode(branch.children, targetId)) {
          return true
        }
      }
    }
    if (forkNode.joinChildren) {
      // join 节点本身（joinChildren 的第一节点）允许被删除：把 join 的 children 接到 fork
      if (forkNode.joinChildren.id === targetId) {
        forkNode.joinChildren = forkNode.joinChildren.children || undefined
        return true
      }
      if (removeNode(forkNode.joinChildren, targetId)) {
        return true
      }
    }
  }

  // 场景 3：继续递归到 root.children
  if (root.children) {
    return removeNode(root.children, targetId)
  }

  return false
}

/**
 * 清理空的 branch（条件/fork 容器的分支）
 * 规则：分支数 > 2 时空 branch 自动删除；= 2 时保留（条件分支保留空分支作为直通路径，并行分支保留以防误删）
 */
function cleanupEmptyBranches(root: DingNode | undefined) {
  if (!root) return
  function walk(node: DingNode) {
    if (isConditionNode(node)) {
      const cond = node as DingConditionNode
      if (cond.branches.length > 2) {
        cond.branches = cond.branches.filter(b => b.children !== undefined)
      }
      for (const b of cond.branches) {
        if (b.children) walk(b.children)
      }
    } else if (isForkNode(node)) {
      const fork = node as DingForkNode
      if (fork.branches.length > 2) {
        fork.branches = fork.branches.filter(b => b.children !== undefined)
      }
      for (const b of fork.branches) {
        if (b.children) walk(b.children)
      }
      if (fork.joinChildren) walk(fork.joinChildren)
    } else if (node.children) {
      walk(node.children)
    }
  }
  walk(root)
}

/**
 * 删除整个条件容器：把容器的 children（汇聚后的下一节点）接续到所在位置
 * 适用于 root.children 是条件容器、或分支的 children 是条件容器的两种位置
 */
function removeConditionContainerById(root: DingNode, containerId: string): boolean {
  // 位置 1：root.children 是要删除的条件容器
  if (root.children && root.children.id === containerId && isConditionNode(root.children)) {
    root.children = (root.children as DingConditionNode).children
    return true
  }
  // 位置 2：条件容器的某个分支的 children 是要删除的条件容器
  if (isConditionNode(root)) {
    const condNode = root as DingConditionNode
    for (const branch of condNode.branches) {
      if (
        branch.children &&
        branch.children.id === containerId &&
        isConditionNode(branch.children)
      ) {
        branch.children = (branch.children as DingConditionNode).children
        return true
      }
      if (branch.children && removeConditionContainerById(branch.children, containerId)) {
        return true
      }
    }
  }
  // 位置 2b：fork 容器的某个分支或 joinChildren 中
  if (isForkNode(root)) {
    const forkNode = root as DingForkNode
    for (const branch of forkNode.branches) {
      if (branch.children && removeConditionContainerById(branch.children, containerId)) {
        return true
      }
    }
    if (forkNode.joinChildren && removeConditionContainerById(forkNode.joinChildren, containerId)) {
      return true
    }
  }
  // 位置 3：继续递归到 root.children
  if (root.children) {
    return removeConditionContainerById(root.children, containerId)
  }
  return false
}

/**
 * 删除整个 fork 容器：把 joinChildren 接续到所在位置
 */
function removeForkContainerById(root: DingNode, containerId: string): boolean {
  // 位置 1：root.children 是要删除的 fork 容器
  if (root.children && root.children.id === containerId && isForkNode(root.children)) {
    root.children = (root.children as DingForkNode).joinChildren?.children
    return true
  }
  // 位置 2：fork 内部递归（分支链 + joinChildren 链）
  if (isForkNode(root)) {
    const forkNode = root as DingForkNode
    for (const branch of forkNode.branches) {
      if (branch.children && removeForkContainerById(branch.children, containerId)) {
        return true
      }
    }
    if (forkNode.joinChildren && removeForkContainerById(forkNode.joinChildren, containerId)) {
      return true
    }
  }
  // 位置 3：继续递归到 root.children
  if (root.children) {
    return removeForkContainerById(root.children, containerId)
  }
  return false
}

/**
 * 在指定节点位置插入条件/并发分支节点
 * 默认带两个"审批人"任务节点（与合并分支保持一致，"生而有用"）
 */
function insertConditionNode(afterNode: DingNode | null) {
  if (!treeData.value || !afterNode) return

  const taskType = ensureTypePrefix('task')
  const branch1Task: DingNode = {
    id: generateId(),
    type: taskType,
    name: getDefaultName(taskType),
    properties: {},
  }
  const branch2Task: DingNode = {
    id: generateId(),
    type: taskType,
    name: getDefaultName(taskType),
    properties: {},
  }

  const condNode: DingConditionNode = {
    id: generateId(),
    type: 'condition',
    name: '',
    properties: {},
    branches: [
      { id: generateId(), name: '条件1', properties: {}, children: branch1Task },
      { id: generateId(), name: '条件2', properties: {}, children: branch2Task },
    ],
  }

  // 在 afterNode 后插入 condNode
  insertAfter(treeData.value, afterNode.id, condNode as unknown as DingNode)
}

/**
 * 在 afterNode 后插入 fork+join 对（含两个空分支 + join 节点 + joinChildren）
 * 语义：afterNode → fork → [branch1, branch2] → join → joinChildren(原 afterNode.children)
 *
 * 注：join 节点作为独立 DingNode 包装在 joinChildren 链中，确保渲染和回写 graph 时 join 节点能正确显示与还原
 */
function insertForkJoinPair(afterNode: DingNode | null) {
  if (!treeData.value || !afterNode) return

  const joinId = generateId()
  // 创建 join 节点（作为 joinChildren 链的第一节点）
  const joinNode: DingNode = {
    id: joinId,
    type: ensureTypePrefix('join'),
    name: '合并节点',
    properties: {},
    children: afterNode.children, // 接管原 afterNode.children
  }
  const taskType = ensureTypePrefix('task')
  // 默认给每个分支塞一个"审批人"任务节点，确保分支"生而有用"
  const branch1Task: DingNode = {
    id: generateId(),
    type: taskType,
    name: getDefaultName(taskType),
    properties: {},
  }
  const branch2Task: DingNode = {
    id: generateId(),
    type: taskType,
    name: getDefaultName(taskType),
    properties: {},
  }
  const forkNode: DingForkNode = {
    id: generateId(),
    type: 'fork',
    name: '',
    properties: {},
    branches: [
      { id: generateId(), name: '分支1', properties: {}, children: branch1Task },
      { id: generateId(), name: '分支2', properties: {}, children: branch2Task },
    ],
    joinId,
    joinChildren: joinNode,
  }
  // afterNode 原本的 children 转交给 join 节点
  afterNode.children = forkNode as unknown as DingNode
}

/**
 * 获取节点默认名称
 */
function getDefaultName(nodeType: string): string {
  const baseType = nodeType.replace(props.typePrefix, '')
  switch (baseType) {
    case 'task': return '审批人'
    case 'custom': return '自定义节点'
    case 'subProcess': return '子流程'
    default: return '新节点'
  }
}

// ─── 编辑面板 ─────────────────────────────────────────────────────────

const editingNode = ref<DingNode | null>(null)
const editingBranch = ref<DingBranch | null>(null)
const showEditPanel = computed(() => !!editingNode.value || !!editingBranch.value)
const editFormData = reactive<Record<string, string>>({
  name: '',
  displayName: '',
  assignee: '',
  assignmentHandler: '',
  candidateUsers: '',
  candidateGroups: '',
  candidateHandler: '',
  taskType: '',
  performType: '',
  countersignType: '',
  countersignCompletionCondition: '',
  actionBtns: '',
  callback: '',
  reminderTime: '',
  reminderRepeat: '',
  expireTime: '',
  autoExecute: '',
  clazz: '',
  methodName: '',
  args: '',
  form: '',
  version: '',
  preInterceptors: '',
  postInterceptors: '',
  expr: '',
  handleClass: '',
})

const editPanelTitle = computed(() => {
  if (editingBranch.value) return '编辑分支条件'
  if (!editingNode.value) return ''
  const baseType = editingNode.value.type.replace(props.typePrefix, '')
  switch (baseType) {
    case 'start': return '编辑开始节点'
    case 'end': return '编辑结束节点'
    case 'task': return '编辑审批节点'
    case 'custom': return '编辑自定义节点'
    case 'subProcess': return '编辑子流程'
    case 'condition': return '编辑条件分支（决策配置）'
    case 'fork': return '编辑并行分支'
    default: return '编辑节点'
  }
})

// 内置表单元数据单一事实源：与画布模式共用 plugins/schema.ts，
// 字段集/label/helpMessage/defaultValue/Select options 双模式完全一致
const schemaByType: Record<string, FDFormType> = {
  task: schema.task,
  condition: schema.decision,
  custom: schema.custom,
  subProcess: schema.subProcess,
  start: schema.start,
  end: schema.end,
}
// 当前编辑节点来自 dndPanel 的自定义表单（优先于内置 schema）
const editingPatternForm = ref<FDFormType | undefined>(undefined)

const editFormFields = computed<FDFormItemType[]>(() => {
  if (editingBranch.value) {
    const fields: FDFormItemType[] = [
      { name: 'displayName', label: '分支名称', component: 'Input', componentProps: { placeholder: '请输入分支名称' } },
    ]
    // 只有条件分支（condition）才显示条件表达式，并行分支（parallel）不显示
    if (editingBranchType.value === 'condition') {
      fields.push({ name: 'expr', label: '条件表达式', component: 'Input', componentProps: { placeholder: '请输入条件表达式' } })
    }
    return fields
  }
  if (!editingNode.value) return []
  const baseType = editingNode.value.type.replace(props.typePrefix, '')
  const common: FDFormItemType[] = [
    { name: 'name', label: '唯一编码', component: 'Input', componentProps: { placeholder: '请输入唯一编码' } },
    { name: 'displayName', label: '显示名称', component: 'Input', componentProps: { placeholder: '请输入显示名称' } },
  ]
  const formConfig = editingPatternForm.value || schemaByType[baseType]
  if (!formConfig?.formItems) return common
  let fields = formConfig.formItems.filter(f => f.name !== '__schema__')
  // schema.decision 未含 displayName；可改名节点类型补插到 name 之后（start/end 不支持改名）
  if (!fields.some(f => f.name === 'displayName') && baseType !== 'start' && baseType !== 'end') {
    const idx = fields.findIndex(f => f.name === 'name')
    const dn: FDFormItemType = { name: 'displayName', label: '显示名称', component: 'Input', componentProps: { placeholder: '请输入显示名称' } }
    fields = [...fields.slice(0, idx + 1), dn, ...fields.slice(idx + 1)]
  }
  return fields
})

function cancelEditPanel() {
  editingNode.value = null
  editingBranch.value = null
}

/**
 * 将 editFormData 当前值同步到 editingNode/editingBranch（实时生效，页面不需"保存"）
 * 字段映射与原来的 saveEdit 一致，保证 properties 中未列出的原字段不丢失
 */
function applyEditFormToTarget() {
  if (editingBranch.value) {
    // 分支编辑：displayName -> name, expr/name 写入 properties
    editingBranch.value.name = editFormData.displayName
    editingBranch.value.properties = {
      ...editingBranch.value.properties,
      expr: editFormData.expr,
      name: editFormData.name,
    }
    return
  }
  if (editingNode.value) {
    // 节点编辑：字段集由 editFormFields（schema.ts 单一事实源）驱动，
    // 新增字段无需改回写逻辑；保留原 properties 全部字段避免丢失
    const fields = editFormFields.value
    if (fields.some(f => f.name === 'displayName')) {
      // start/end 无 displayName 字段，不覆盖节点名称
      editingNode.value.name = editFormData.displayName
    }
    const nextProps: Record<string, any> = {
      ...editingNode.value.properties,
      name: editFormData.name,
    }
    for (const f of fields) {
      if (f.name === 'name' || f.name === 'displayName') continue
      nextProps[f.name] = editFormData[f.name]
    }
    editingNode.value.properties = nextProps
  }
}

// 实时同步：editFormData 任意字段变化都立即同步到目标节点
// 注：不调 syncToGraph()，避免每次 input 都 emit；仅在 closeEditPanel 时提交一次
// 写法：直接 watch reactive 对象（getter 套 {...obj} 会让 deep 失效）
watch(
  editFormData,
  () => {
    if (editingNode.value || editingBranch.value) {
      applyEditFormToTarget()
    }
  },
  { deep: true }
)

// ─── 右键菜单事件 ─────────────────────────────────────────────

function handleContextmenu(_e: MouseEvent) {
  if (props.viewer) return

  // 获取当前流程属性（未传 processForm 时 fallback 内置 schema.process，与画布模式一致）
  const processFormConfig: FDFormType = props.processForm || schema.process
  const processProperties: Record<string, any> = {}
  if (processFormConfig?.formItems) {
    for (const item of processFormConfig.formItems) {
      if (props.value && Object.prototype.hasOwnProperty.call(props.value, item.name)) {
        processProperties[item.name] = (props.value as any)[item.name]
      }
    }
  }

  const eventParams = {
    data: {
      type: 'process',
      properties: processProperties
    },
    patternItem: { form: processFormConfig },
    lf: designerApi,
  }

  if (props.blankContextmenu && typeof props.blankContextmenu === 'function') {
    props.blankContextmenu(eventParams)
    return
  }
  // fallback：业务方未传 blankContextmenu，且有 processForm 配置，自动打开内置抽屉
  if (processFormFields.value.length > 0) {
    openProcessDrawer()
  }
}

// ─── 控制面板事件 ─────────────────────────────────────────────

const showDataModal = ref(false)
const viewDataJson = ref('')
// FDJsonViewer 需要对象数据（与画布模式 modal.vue 同款展示：行号/折叠/语法着色）
const viewDataObj = computed(() => {
  try { return JSON.parse(viewDataJson.value || '{}') } catch { return {} }
})
const showImportModal = ref(false)
const importDataJson = ref('')
const importError = ref('')

// ─── 流程属性内置抽屉 ─────────────────────────────────────
const showProcessDrawer = ref(false)
const processFormData = reactive<Record<string, any>>({})
const processFormFields = computed<FDFormItemType[]>(() => {
  // 未传 processForm 时 fallback 内置 schema.process，与画布模式行为对齐
  const formItems = (props.processForm || schema.process)?.formItems
  if (!formItems) return []
  return formItems.filter(f => f.name !== '__schema__')
})

function openProcessDrawer() {
  // 从 props.value 初始化表单
  processFormFields.value.forEach(f => {
    processFormData[f.name] = (props.value as any)?.[f.name] ?? f.defaultValue ?? ''
  })
  showProcessDrawer.value = true
}
function closeProcessDrawer() {
  showProcessDrawer.value = false
  // 提交一次 emit + 触发事件
  const newValue: FDConfigData = { ...props.value, ...processFormData }
  isInternalUpdate = true
  emit('update:value', newValue)
  eventCenter.emit('update:graphModel', newValue)
}

// 字段变化时实时同步到 props.value（与画布模式 handleValuesChange 一致）
watch(
  processFormData,
  () => {
    if (!showProcessDrawer.value) return
    // 直接 emit（避免循环 setProcessProperty）
    const newValue: FDConfigData = { ...props.value, ...processFormData }
    isInternalUpdate = true
    emit('update:value', newValue)
    eventCenter.emit('update:graphModel', newValue)
  },
  { deep: true }
)

function handleControlSave() {
  const graphData = treeToGraph(treeData.value, props.typePrefix)
  const saveData: FDConfigData = {
    ...props.value,
    nodes: graphData.nodes,
    edges: graphData.edges,
    mode: 'dingtalk',
  }
  emit('save', saveData)
}

function handleControlClear() {
  // 清空树形数据，保留默认链路：start → 申请(protected) → end
  const startNode: DingNode = {
    id: generateId(),
    type: `${props.typePrefix}start`,
    name: '开始',
    properties: {},
    children: {
      id: generateId(),
      type: `${props.typePrefix}task`,
      name: '申请',
      properties: {},
      children: {
        id: generateId(),
        type: `${props.typePrefix}end`,
        name: '结束',
        properties: {},
      }
    }
  }
  treeData.value = startNode
  syncToGraph()
}

function handleControlViewData() {
  const graphData = treeToGraph(treeData.value, props.typePrefix)
  const data: FDConfigData = {
    ...props.value,
    nodes: graphData.nodes,
    edges: graphData.edges,
    mode: 'dingtalk',
  }
  viewDataJson.value = JSON.stringify(data, null, 2)
  showDataModal.value = true
}

function handleControlImportData() {
  importDataJson.value = ''
  showImportModal.value = true
}

/**
 * 导入数据：解析 + 结构校验；失败时不关闭弹窗、不破坏 treeData
 * 成功时保留外部 mode 字段（缺省时填 'dingtalk'）
 */
function doImport() {
  importError.value = ''
  const snapshot = JSON.stringify(treeData.value)
  try {
    const data = JSON.parse(importDataJson.value)
    if (!data || typeof data !== 'object') {
      importError.value = '导入失败：数据格式不正确'
      return
    }
    if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
      importError.value = '导入失败：缺少 nodes 或 edges 数组'
      return
    }
    for (const n of data.nodes) {
      if (!n || typeof n.id !== 'string' || typeof n.type !== 'string') {
        importError.value = '导入失败：节点缺少 id 或 type 字段'
        return
      }
    }
    for (const e of data.edges) {
      if (
        !e ||
        typeof e.id !== 'string' ||
        typeof e.sourceNodeId !== 'string' ||
        typeof e.targetNodeId !== 'string'
      ) {
        importError.value = '导入失败：边缺少 id / sourceNodeId / targetNodeId 字段'
        return
      }
    }
    isInternalUpdate = true
    // 仅覆盖 nodes/edges/mode，保留 props.value 其他字段（name/displayName 等）
    const newValue: FDConfigData = {
      ...props.value,
      nodes: data.nodes,
      edges: data.edges,
      mode: data.mode === 'canvas' ? 'canvas' : 'dingtalk',
    }
    emit('update:value', newValue)
    treeData.value = graphToTree((newValue.nodes || []) as GraphNode[], (newValue.edges || []) as GraphEdge[], props.typePrefix)
    showImportModal.value = false
  } catch (err) {
    importError.value = '导入失败：JSON 格式不正确'
    // 恢复 treeData 避免脏数据
    try {
      treeData.value = JSON.parse(snapshot)
    } catch {
      /* snapshot 异常时不做恢复 */
    }
  }
}

function copyData() {
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      navigator.clipboard.writeText(viewDataJson.value)
    } else {
      // 非安全上下文兼容方案（与画布模式 modal.vue 一致）
      const textarea = document.createElement('textarea')
      textarea.value = viewDataJson.value
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    FDMessage.success('复制成功')
  } catch (err) {
    FDMessage.error(`复制失败: ${err instanceof Error ? err.message : String(err)}`)
  }
}

function handleControlFullscreen() {
  const el = document.querySelector('.ding-designer') as HTMLElement
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen?.().catch(() => {})
  } else {
    document.exitFullscreen?.().catch(() => {})
  }
}
</script>
