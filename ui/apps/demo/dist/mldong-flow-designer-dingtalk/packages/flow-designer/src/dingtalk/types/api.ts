/**
 * 钉钉模式对外暴露的"lf 等价 API"类型
 *
 * 设计目标：
 * - 与画布模式 LogicFlow 实例的 API 命名保持一致
 *   （业务方在 vben5 中习惯调用 `lf.updateText / changeNodeId / setProperties / getNodeDataById`）
 * - 让原有的二次开发代码（task-drawer / process-drawer 等）几乎无修改即可在钉钉模式下复用
 * - 配合 eventCenter.emit 让业务方自定义表单能反向更新画布
 *
 * 关键约定：
 * - 所有"按 id 操作"的方法，id 接受 DingNode.id 或 node.properties.name（vben5 base-form 习惯用 name 作为 key）
 * - 所有更新方法都会自动触发 v-model 同步（emit update:value）
 * - viewer 模式下，update 类方法为只读（不报错但不生效）
 */

import type { DingNode, DingBranch, DingConditionNode, DingForkNode } from '../types'
import type { FDConfigData, FDHighLightType } from '../../types'

/**
 * 业务方在 nodeClick / edgeClick 回调中拿到的"节点数据"（与画布模式一致）
 * - id: DingNode.id
 * - type: 完整 type（含 prefix）
 * - text.value: 显示名称
 * - properties: 业务字段集合
 */
export interface FDNodeData {
  id: string
  type: string
  text: { value: string }
  properties: Record<string, any>
}

/** eventCenter 支持的事件名 */
export type FDEventName =
  | 'update:graphModel'   // 流程属性变化（v-model.value 同步）
  | 'update:graphData'    // 节点/边数据变化（重渲染画布）
  | 'update:highlight'    // 高亮数据变化

/**
 * node-click / edge-click 事件回调参数（与画布模式 Flow.ts 中的
 * eventCenter.on('node:click', e => { nodeClick({...event, patternItem, lf}) })
 * 保持完全一致的签名结构）。
 *
 * 业务方在两种模式下写 `:node-click="onNodeClick"` 拿到的对象结构完全一致：
 * ```ts
 * const onNodeClick = ({ data, node, patternItem, lf }) => {
 *   // data: { id, type, text: { value }, properties }    // 与画布模式 LF 节点 data 一致
 *   // node: DingNode（钉钉模式原生节点对象；画布模式为 LF 的 BaseNodeModel）
 *   // patternItem: dndPanel 中匹配到的项（含 form / nodeClick 等配置）
 *   // lf: FDDesignerAPI（钉钉模式的 lf 等价 API；画布模式为 LogicFlow 实例）
 * }
 * ```
 */
export interface DingNodeEventParams {
  /** 节点数据快照（与 LF 节点 data 同构，便于业务方统一处理） */
  data: FDNodeData
  /** 原始节点对象（钉钉模式 DingNode，画布模式 LF node model） */
  node: DingNode
  /** dndPanel 中匹配的节点类型配置（业务方可在 item.nodeClick 中覆盖） */
  patternItem?: import('../../types').FDPatternItem
  /** lf 实例引用（钉钉模式为 FDDesignerAPI，画布模式为 LogicFlow） */
  lf?: FDDesignerAPI
}

/**
 * edge-click 事件回调参数（与画布模式 Flow.ts 的 edge:click 签名对齐）
 */
export interface DingEdgeEventParams {
  /** 分支/边数据快照 */
  data: FDNodeData
  /** 原始分支对象（钉钉模式 DingBranch；画布模式 LF edge model） */
  edge: DingBranch
  /** dndPanel 中边类型的配置（钉钉模式固定为 { form: props.edgeForm }） */
  patternItem?: { form?: any }
  /** lf 实例引用 */
  lf?: FDDesignerAPI
}

/**
 * 事件总线（简化版，自实现，避免引入外部库）
 * 业务方用法：
 * ```ts
 * const api = ref.getDesignerApi()
 * api.eventCenter.on('update:graphModel', () => { ... })
 * api.eventCenter.emit('update:graphModel', { name: 'leave' })
 * ```
 */
export interface FDEventCenter {
  emit(event: FDEventName, data?: any): void
  on(event: FDEventName, handler: (data?: any) => void): void
  off(event: FDEventName, handler: (data?: any) => void): void
}

/**
 * 钉钉模式对外暴露的 API（与 LogicFlow 兼容命名）
 *
 * 典型用法（与画布模式对照）：
 * ```ts
 * // 画布模式
 * const lf = ref.getLfInstance()
 * lf.updateText('apply', '请假申请-改')
 *
 * // 钉钉模式
 * const api = ref.getDesignerApi()
 * api.updateText('apply', '请假申请-改')
 * ```
 */
export interface FDDesignerAPI {
  // ─── 节点查询 ───────────────────────────────────────────
  /** 按 id 查找节点（含 start/end/task/custom/subProcess/condition/fork/join） */
  getNodeDataById(id: string): FDNodeData | null
  /** 按 properties.name 查找节点（vben5 base-form 习惯） */
  getNodeDataByName(name: string): FDNodeData | null
  /** 获取所有节点数据（扁平） */
  getAllNodes(): FDNodeData[]

  /**
   * 按 id 取节点 properties（对应 lf.getProperties）
   *
   * vben5-wf 的字段权限配置（process-form.vue）依赖此方法读取节点 field 属性：
   * ```ts
   * lfInstance.getProperties(nodeId)?.field || {}
   * ```
   * 接受节点 id 或 properties.name（与 _resolveNode 一致）。
   * viewer 模式下行为与 canvas 模式一致——读取不受 viewer 限制（只读查询）。
   */
  getProperties(id: string): Record<string, any>

  // ─── 节点更新（实时同步 props.value） ─────────────────────
  /**
   * 更新节点显示文本（对应 lf.updateText）
   * @param id 节点 id 或 properties.name
   * @param text 新的显示名称
   */
  updateText(id: string, text: string): void

  /**
   * 修改节点 ID（对应 lf.changeNodeId）
   * 同步更新 node.id 和 properties.name
   */
  changeNodeId(oldId: string, newId: string): boolean

  /**
   * 设置节点 properties（合并语义；对应 lf.setProperties）
   * @param id 节点 id 或 properties.name
   * @param props 要合并的属性
   */
  setProperties(id: string, props: Record<string, any>): void

  /**
   * 删除节点单个 property（对应 lf.deleteProperty）
   */
  deleteProperty(id: string, key: string): void

  // ─── 流程属性（v-model.value） ──────────────────────────
  /**
   * 设置流程属性（v-model.value 的字段）
   * 等同于修改 props.value 但会触发 emit('update:value')
   */
  setProcessProperty(key: string, value: any): void

  // ─── 导出/重渲染 ──────────────────────────────────────
  /** 获取当前 graph data（导出保存） */
  getGraphData(): FDConfigData

  /**
   * 重新渲染（传入完整 graph data）
   * 与画布模式 lf.render(data) 一致
   */
  render(data: FDConfigData): void

  // ─── 高亮 ───────────────────────────────────────────
  /** 设置高亮数据（同时触发重渲染） */
  setHighlight(data: FDHighLightType): void

  // ─── 事件总线（业务方表单主动通知画布） ────────────────
  eventCenter: FDEventCenter

  // ─── graphModel 代理（与画布模式 lf.graphModel 兼容） ───────
  /**
   * 画布模式下，业务方通过 `lf.graphModel[key] = value` 修改流程属性
   * 钉钉模式没有 lf 实例，暴露一个 Proxy 对象，让业务方写法零修改：
   *
   * ```ts
   * // vben5 process-drawer.vue 中原代码，在钉钉模式也能跑：
   * lfInstance.value.graphModel[key] = values[key]
   * lfInstance.value.graphModel.eventCenter.emit('update:graphModel', graphModel)
   * ```
   *
   * - get: 从 props.value（v-model）读取任意字段；访问 eventCenter 返回真实事件总线
   * - set: 写入 props.value 并 emit update:value + update:graphModel 事件
   * - viewer 模式下 set 静默不生效
   */
  graphModel: FDGraphModelProxy
}

/**
 * graphModel 代理的类型定义
 * - 任意字符串 key 映射到 v-model.value 上的字段
 * - 特殊 key 'eventCenter' 返回 FDEventCenter
 *
 * 注：用 Proxy 实现，TypeScript 类型声明为 Record<string, any>
 */
export interface FDGraphModelProxy {
  [key: string]: any
}

/**
 * 内部辅助：递归查找节点（按 id 或按 name）
 */
export function findNode(
  root: DingNode | DingConditionNode | DingForkNode | null | undefined,
  predicate: (n: DingNode) => boolean
): DingNode | null {
  if (!root) return null
  if (predicate(root as DingNode)) return root as DingNode
  if ((root as DingConditionNode).branches) {
    const cond = root as DingConditionNode
    for (const b of cond.branches) {
      if (b.children) {
        const found = findNode(b.children, predicate)
        if (found) return found
      }
    }
  }
  if ((root as DingForkNode).branches) {
    const fork = root as DingForkNode
    for (const b of fork.branches) {
      if (b.children) {
        const found = findNode(b.children, predicate)
        if (found) return found
      }
    }
    if (fork.joinChildren) {
      const found = findNode(fork.joinChildren, predicate)
      if (found) return found
    }
  }
  // fork 容器无 children 字段（用 branches/joinChildren），'children' in 收窄普通节点/条件容器
  if ('children' in root && root.children) {
    return findNode(root.children, predicate)
  }
  return null
}

/**
 * 内部辅助：扁平化所有节点
 *
 * 同一节点可能被多个分支共享引用（如汇聚点 end 节点同时被所有 condition 分支 + 主链引用），
 * 这里按 id 去重避免在调用方产生重复项。
 */
export function flattenNodes(
  root: DingNode | DingConditionNode | DingForkNode | null | undefined,
  acc: DingNode[] = [],
  seen: Set<string> = new Set()
): DingNode[] {
  if (!root) return acc
  if (seen.has(root.id)) return acc
  seen.add(root.id)
  acc.push(root as DingNode)
  const cond = root as DingConditionNode
  if (cond.branches) {
    for (const b of cond.branches) {
      if (b.children) flattenNodes(b.children, acc, seen)
    }
  }
  const fork = root as DingForkNode
  if (fork.branches) {
    for (const b of fork.branches) {
      if (b.children) flattenNodes(b.children, acc, seen)
    }
    if (fork.joinChildren) flattenNodes(fork.joinChildren, acc, seen)
  }
  // fork 容器无 children 字段（用 branches/joinChildren），'children' in 收窄普通节点/条件容器
  if ('children' in root && root.children) flattenNodes(root.children, acc, seen)
  return acc
}
