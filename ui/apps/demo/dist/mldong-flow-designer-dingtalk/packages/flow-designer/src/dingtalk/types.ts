/**
 * 钉钉风格流程树形结构类型定义
 */

/** 基础节点（单链表形式） */
export interface DingNode {
  id: string
  type: string               // 原始 node.type (如 'snaker:task')
  name: string               // 显示文本（从 node.text.value 获取）
  properties: Record<string, any>  // 原始 node.properties
  children?: DingNode        // 下一个节点（单链表形式）
}

/** 条件分支容器（decision 节点）— 单条 children 汇聚 */
export interface DingConditionNode extends Omit<DingNode, 'type'> {
  type: 'condition'          // 对应 decision 节点
  branches: DingBranch[]
  children?: DingNode        // 所有分支汇聚后的下一个节点
}

/** 分支 */
export interface DingBranch {
  id: string                 // 对应 edge 的 id
  name: string               // 分支名称（从 edge.text.value 获取）
  properties: Record<string, any>  // edge 的 properties（包含 expr 等）
  children?: DingNode        // 分支内的节点链
}

/**
 * 并行分支 fork 容器（fork 节点）
 *
 * 与 DingConditionNode 共享 DingBranch 分支结构（统一处理 add/remove）：
 * - branches 每项是 DingBranch（id/name 来自 edge，children 是 DingNode 链）
 * - joinId 关联的 join 节点是独立的 DingNode（不在此容器内），通过 joinId 关联
 * - 视觉上：fork 节点 → 多个独立 task 节点链 → join 节点 → joinChildren
 */
export interface DingForkNode extends Omit<DingNode, 'type' | 'children'> {
  type: 'fork'               // 对应 fork 节点
  branches: DingBranch[]     // 多条分支，每条是 DingBranch（children 是独立 DingNode 链）
  joinId?: string            // 汇聚点 join 节点 ID（独立 DingNode）
  joinChildren?: DingNode    // join 节点之后的下一个节点
}

/** 联合类型（便于转换函数内部使用） */
export type DingTreeNode = DingNode | DingConditionNode | DingForkNode

/** 类型守卫：判断节点是否为条件容器（decision） */
export function isConditionNode(node: DingNode): node is DingConditionNode {
  return node.type === 'condition'
}

/** 类型守卫：判断节点是否为 fork 容器（并行分支） */
export function isForkNode(node: DingNode): node is DingForkNode {
  return node.type === 'fork'
}

/** 类型守卫：判断节点是否为 join 节点 */
export function isJoinNode(node: DingNode, typePrefix: string = 'snaker:'): boolean {
  return node.type === `${typePrefix}join` || node.type === 'join'
}

/** 图节点（对应 LogicFlow 的节点数据） */
export interface GraphNode {
  id: string
  type: string
  x: number
  y: number
  text?: { x?: number; y?: number; value?: string }
  properties: Record<string, any>
}

/** 图边（对应 LogicFlow 的边数据） */
export interface GraphEdge {
  id: string
  type: string
  sourceNodeId: string
  targetNodeId: string
  text?: { value?: string }
  properties: Record<string, any>
}

/** graphToTree / treeToGraph 的图数据结构 */
export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}
