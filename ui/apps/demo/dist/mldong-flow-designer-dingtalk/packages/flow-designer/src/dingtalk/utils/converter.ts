import type {
  DingNode,
  DingConditionNode,
  DingBranch,
  DingForkNode,
  GraphNode,
  GraphEdge,
  GraphData,
} from '../types'
import { isConditionNode, isForkNode } from '../types'

const DEFAULT_PREFIX = 'snaker:'

// ─── graphToTree ────────────────────────────────────────────────────────────────

/**
 * 将 LogicFlow 的图数据（nodes + edges）转换为钉钉风格的树形结构
 */
export function graphToTree(
  nodes: GraphNode[],
  edges: GraphEdge[],
  typePrefix: string = DEFAULT_PREFIX
): DingNode | undefined {
  if (!nodes.length) return undefined

  const nodeMap = new Map<string, GraphNode>(nodes.map(n => [n.id, n]))
  const outEdgesMap = buildOutEdgesMap(edges)

  // 找到 start 节点
  const startNode = nodes.find(n => n.type === `${typePrefix}start`)
  if (!startNode) return undefined

  return buildChain(startNode.id, new Set(), nodeMap, outEdgesMap, edges, typePrefix)
}

/**
 * 递归构建节点链表
 * @param nodeId 当前要处理的节点 ID
 * @param stopIds 汇聚点集合（遇到时停止，不包含在当前链中）
 * @param visited 已访问节点集合（防止环路导致无限递归；命中时返回叶子节点）
 */
function buildChain(
  nodeId: string,
  stopIds: Set<string>,
  nodeMap: Map<string, GraphNode>,
  outEdgesMap: Map<string, GraphEdge[]>,
  allEdges: GraphEdge[],
  prefix: string,
  visited: Set<string> = new Set()
): DingNode | undefined {
  if (stopIds.has(nodeId)) return undefined

  const graphNode = nodeMap.get(nodeId)
  if (!graphNode) return undefined

  // 环路检测：已访问过该节点则返回叶子节点，不再继续展开
  if (visited.has(nodeId)) {
    return {
      id: graphNode.id,
      type: graphNode.type,
      name: graphNode.text?.value || '',
      properties: { ...graphNode.properties },
    }
  }
  visited.add(nodeId)

  const outEdges = outEdgesMap.get(nodeId) || []
  const baseType = graphNode.type.replace(prefix, '')

  // 判断是否为分支节点（decision 或 fork，且有多条出边）
  if (baseType === 'decision' && outEdges.length > 1) {
    return buildConditionNode(graphNode, outEdges, stopIds, nodeMap, outEdgesMap, allEdges, prefix, visited)
  }

  // fork 节点：并行分支，对齐 wf-fork-join.json 数据结构（fork 节点 + 多个独立 task 节点 + join 节点）
  if (baseType === 'fork' && outEdges.length > 1) {
    return buildForkNode(graphNode, outEdges, stopIds, nodeMap, outEdgesMap, allEdges, prefix, visited)
  }

  // 普通节点
  const dingNode: DingNode = {
    id: graphNode.id,
    type: graphNode.type,
    name: graphNode.text?.value || '',
    properties: { ...graphNode.properties },
  }

  // end 节点无后续
  if (baseType === 'end') return dingNode

  // 单出边，继续构建链表
  if (outEdges.length === 1) {
    const next = buildChain(outEdges[0].targetNodeId, stopIds, nodeMap, outEdgesMap, allEdges, prefix, visited)
    if (next) dingNode.children = next
  }

  return dingNode
}

/**
 * 构建条件分支容器节点（decision 节点）
 */
function buildConditionNode(
  graphNode: GraphNode,
  outEdges: GraphEdge[],
  parentStopIds: Set<string>,
  nodeMap: Map<string, GraphNode>,
  outEdgesMap: Map<string, GraphEdge[]>,
  allEdges: GraphEdge[],
  prefix: string,
  visited: Set<string>
): DingConditionNode {
  // 找到汇聚点（decision 走"公共可达节点"算法）
  const convergence = findCommonConvergence(
    outEdges.map(e => e.targetNodeId),
    allEdges,
    graphNode.id,
    nodeMap,
    prefix
  )

  // 构建各分支
  const branchStopIds = new Set(parentStopIds)
  if (convergence) branchStopIds.add(convergence)

  const branches: DingBranch[] = outEdges.map(edge => {
    const branchChildren = buildChain(
      edge.targetNodeId,
      branchStopIds,
      nodeMap,
      outEdgesMap,
      allEdges,
      prefix,
      visited
    )
    return {
      id: edge.id,
      name: edge.text?.value || '',
      properties: { ...edge.properties },
      children: branchChildren,
    }
  })

  const condNode: DingConditionNode = {
    id: graphNode.id,
    type: 'condition',
    name: graphNode.text?.value || '',
    properties: { ...graphNode.properties },
    branches,
  }

  // 汇聚点作为 children 继续
  if (convergence) {
    const next = buildChain(convergence, parentStopIds, nodeMap, outEdgesMap, allEdges, prefix, visited)
    if (next) condNode.children = next
  }

  return condNode
}

/**
 * 构建并行分支 fork 节点（fork + 多个独立分支 + join）
 *
 * 对齐 wf-fork-join.json 数据结构：
 *   fork 节点（type='fork'） → 多个独立 task 节点链（branches[]） → join 节点 → 后续节点
 *
 * @returns 第一个分支的第一个节点（用于上层接续到 fork 节点之前）；fork+join 节点通过 joinId/joinChildren 关联
 *
 * 注意：当前实现把 fork 节点本身作为返回值，以便挂到父节点的 children 上。
 *       但 fork 节点不参与子链构建，其 branches/joinId/joinChildren 是"挂件"属性。
 */
function buildForkNode(
  graphNode: GraphNode,
  outEdges: GraphEdge[],
  parentStopIds: Set<string>,
  nodeMap: Map<string, GraphNode>,
  outEdgesMap: Map<string, GraphEdge[]>,
  allEdges: GraphEdge[],
  prefix: string,
  visited: Set<string>
): DingForkNode {
  // 找到 join 节点
  const joinId = findJoinNode(
    outEdges.map(e => e.targetNodeId),
    allEdges,
    nodeMap,
    prefix
  )

  // 构建各分支（每条分支是独立的 DingNode 节点链，包成 DingBranch）
  const branchStopIds = new Set(parentStopIds)
  if (joinId) branchStopIds.add(joinId)

  const branches: DingBranch[] = outEdges.map(edge => {
    const branchChildren = buildChain(
      edge.targetNodeId,
      branchStopIds,
      nodeMap,
      outEdgesMap,
      allEdges,
      prefix,
      visited
    )
    return {
      id: edge.id,
      name: edge.text?.value || '',
      properties: { ...edge.properties },
      children: branchChildren,
    }
  })

  const forkNode: DingForkNode = {
    id: graphNode.id,
    type: 'fork',
    name: graphNode.text?.value || '',
    properties: { ...graphNode.properties },
    branches,
  }

  // 设置 joinId 和 joinChildren
  // joinChildren 链起点 = join 节点本身（保留 join 节点的 DingNode 表示，便于渲染"合并节点"卡片）
  if (joinId) {
    forkNode.joinId = joinId
    const joinChildren = buildChain(
      joinId,
      parentStopIds,
      nodeMap,
      outEdgesMap,
      allEdges,
      prefix,
      visited
    )
    if (joinChildren) forkNode.joinChildren = joinChildren
  }

  return forkNode
}

/**
 * BFS 查找 join 节点（fork 专用）
 */
function findJoinNode(
  startIds: string[],
  allEdges: GraphEdge[],
  nodeMap: Map<string, GraphNode>,
  prefix: string
): string | null {
  const outMap = buildOutEdgesMap(allEdges)
  const visited = new Set<string>()
  const queue = [...startIds]

  while (queue.length > 0) {
    const current = queue.shift()!
    if (visited.has(current)) continue
    visited.add(current)

    const node = nodeMap.get(current)
    if (node && node.type === `${prefix}join`) return current

    const nextEdges = outMap.get(current) || []
    for (const e of nextEdges) {
      if (!visited.has(e.targetNodeId)) queue.push(e.targetNodeId)
    }
  }

  return null
}

/**
 * 查找所有分支的公共可达节点（最近的汇聚点）
 * 算法：对每个分支做 BFS，统计每个节点被多少分支可达，
 * 然后按拓扑序找第一个被所有分支可达的节点。
 * 找不到公共汇聚时（如各分支直达 end 不交汇），fallback 到第一个 end 节点。
 */
function findCommonConvergence(
  branchTargets: string[],
  allEdges: GraphEdge[],
  excludeId: string,
  nodeMap?: Map<string, GraphNode>,
  prefix?: string
): string | null {
  const outMap = buildOutEdgesMap(allEdges)
  const totalBranches = branchTargets.length
  const reachCount = new Map<string, number>()

  // 统计每个节点被多少分支可达
  for (const target of branchTargets) {
    const visited = new Set<string>()
    const queue = [target]
    while (queue.length > 0) {
      const current = queue.shift()!
      if (visited.has(current)) continue
      visited.add(current)
      reachCount.set(current, (reachCount.get(current) || 0) + 1)
      const nextEdges = outMap.get(current) || []
      for (const e of nextEdges) {
        if (!visited.has(e.targetNodeId)) queue.push(e.targetNodeId)
      }
    }
  }

  // BFS 从各分支起点开始，找第一个被所有分支可达的节点
  const visited = new Set<string>([excludeId])
  const queue = [...branchTargets]

  while (queue.length > 0) {
    const current = queue.shift()!
    if (visited.has(current)) continue
    visited.add(current)

    if (reachCount.get(current) === totalBranches) {
      return current
    }

    const nextEdges = outMap.get(current) || []
    for (const e of nextEdges) {
      if (!visited.has(e.targetNodeId)) queue.push(e.targetNodeId)
    }
  }

  // 找不到公共汇聚点时 fallback 到第一个 end 节点（决策直达终点的常见场景）
  if (nodeMap && prefix) {
    for (const [id, n] of nodeMap) {
      if (n.type === `${prefix}end`) return id
    }
  }

  return null
}

// ─── treeToGraph ────────────────────────────────────────────────────────────────

/**
 * 将钉钉风格的树形结构转换回 LogicFlow 的图数据
 */
export function treeToGraph(
  tree: DingNode | undefined,
  typePrefix: string = DEFAULT_PREFIX
): GraphData {
  if (!tree) return { nodes: [], edges: [] }

  const ctx: ConvertContext = {
    nodes: [],
    edges: [],
    edgeCounter: 0,
    prefix: typePrefix,
    layoutY: 200,
    layoutX: 480,
  }

  processNodeToGraph(tree, ctx)

  return { nodes: ctx.nodes, edges: ctx.edges }
}

interface ConvertContext {
  nodes: GraphNode[]
  edges: GraphEdge[]
  edgeCounter: number
  prefix: string
  layoutY: number
  layoutX: number
}

/**
 * 递归处理树节点，生成图节点和边
 * 返回当前节点的 id（用于父节点连接边）
 */
function processNodeToGraph(dingNode: DingNode, ctx: ConvertContext): string {
  if (isConditionNode(dingNode)) {
    return processConditionToGraph(dingNode, ctx)
  }
  if (isForkNode(dingNode)) {
    return processForkJoinToGraph(dingNode, ctx)
  }

  // 普通节点
  const graphNode = createGraphNode(dingNode, ctx)
  ctx.nodes.push(graphNode)

  if (dingNode.children) {
    const childId = processNodeToGraph(dingNode.children, ctx)
    addEdge(ctx, dingNode.id, childId)
  }

  return dingNode.id
}

/**
 * 处理条件分支节点的图转换（decision 节点）
 */
function processConditionToGraph(condNode: DingConditionNode, ctx: ConvertContext): string {
  // 生成分支源节点（decision）
  const sourceNode = createGraphNode(
    { ...condNode, type: `${ctx.prefix}decision` } as unknown as DingNode,
    ctx
  )
  ctx.nodes.push(sourceNode)

  const savedY = ctx.layoutY
  const branchCount = condNode.branches.length
  const startX = ctx.layoutX - ((branchCount - 1) * 200) / 2

  // 处理各分支
  for (let i = 0; i < branchCount; i++) {
    const branch = condNode.branches[i]
    const branchX = startX + i * 200

    if (branch.children) {
      ctx.layoutX = branchX
      ctx.layoutY = savedY + 150
      const firstChildId = processNodeToGraph(branch.children, ctx)

      // 从 decision 到分支第一个节点的 edge（携带分支属性）
      addEdge(ctx, condNode.id, firstChildId, branch.id, branch.name, branch.properties)

      // 从分支最后节点到汇聚点的 edge
      if (condNode.children) {
        const lastId = findLastNodeId(branch.children)
        addEdge(ctx, lastId, condNode.children.id)
      }
    } else if (condNode.children) {
      // 空分支：直接从 decision 到汇聚点
      addEdge(ctx, condNode.id, condNode.children.id, branch.id, branch.name, branch.properties)
    }
  }

  // 恢复布局位置，处理汇聚点及后续
  ctx.layoutX = sourceNode.x
  ctx.layoutY = savedY + 150 * 2
  if (condNode.children) {
    processNodeToGraph(condNode.children, ctx)
  }

  return condNode.id
}

/**
 * 处理并行分支 fork+join 节点的图转换
 *
 * 输出节点（按 wf-fork-join.json 语义）：
 *   fork → [branch1Root, branch2Root, ...] → join → joinChildren
 *
 * 注：DingForkNode.branches[] 是 DingNode 数组（不像 condition 包了 DingBranch），
 *     因此分支 edge ID 需要基于 outEdge 自动生成；分支名等信息从 DingNode 派生。
 */
function processForkJoinToGraph(forkNode: DingForkNode, ctx: ConvertContext): string {
  // 生成 fork 节点
  const sourceNode = createGraphNode(
    { ...forkNode, type: `${ctx.prefix}fork` } as unknown as DingNode,
    ctx
  )
  ctx.nodes.push(sourceNode)

  const savedY = ctx.layoutY
  const branchCount = forkNode.branches.length
  const startX = ctx.layoutX - ((branchCount - 1) * 200) / 2

  // join 节点由 joinChildren 链自动生成；此处只取 join id 用于各分支汇聚
  const joinNodeId: string | null = forkNode.joinId
    || (forkNode.joinChildren ? forkNode.joinChildren.id : null)
    || `${forkNode.id}__join`

  // 处理各分支（每条是独立 DingNode 链）
  for (let i = 0; i < branchCount; i++) {
    const branch = forkNode.branches[i]
    const branchX = startX + i * 200

    if (!branch.children) {
      // 空分支：fork → join 直连（用户尚未填入任务）
      addEdge(ctx, forkNode.id, joinNodeId)
      continue
    }

    ctx.layoutX = branchX
    ctx.layoutY = savedY + 150
    const firstChildId = processNodeToGraph(branch.children, ctx)

    // fork → 分支第一个节点
    addEdge(ctx, forkNode.id, firstChildId)

    // 分支最后节点 → join
    const lastId = findLastNodeId(branch.children)
    addEdge(ctx, lastId, joinNodeId)
  }

  // 处理 joinChildren 链：链第一节点是 join 节点本身（会自然生成 join + 后续节点的图）
  if (forkNode.joinChildren) {
    ctx.layoutX = sourceNode.x
    ctx.layoutY = savedY + 150 * 2
    processNodeToGraph(forkNode.joinChildren, ctx)
  }

  return forkNode.id
}

// ─── 工具函数 ───────────────────────────────────────────────────────────────────

function buildOutEdgesMap(edges: GraphEdge[]): Map<string, GraphEdge[]> {
  const map = new Map<string, GraphEdge[]>()
  for (const edge of edges) {
    const list = map.get(edge.sourceNodeId)
    if (list) list.push(edge)
    else map.set(edge.sourceNodeId, [edge])
  }
  return map
}

function createGraphNode(dingNode: DingNode, ctx: ConvertContext): GraphNode {
  const x = ctx.layoutX
  const y = ctx.layoutY
  ctx.layoutY += 150

  return {
    id: dingNode.id,
    type: dingNode.type,
    x,
    y,
    text: dingNode.name ? { x, y, value: dingNode.name } : undefined,
    properties: { ...dingNode.properties },
  }
}

function addEdge(
  ctx: ConvertContext,
  sourceId: string,
  targetId: string,
  edgeId?: string,
  name?: string,
  properties?: Record<string, any>
): void {
  const id = edgeId || `edge_${++ctx.edgeCounter}`
  const edge: GraphEdge = {
    id,
    type: `${ctx.prefix}transition`,
    sourceNodeId: sourceId,
    targetNodeId: targetId,
    properties: properties ? { ...properties } : {},
  }
  if (name) edge.text = { value: name }
  ctx.edges.push(edge)
}

/**
 * 递归查找链表中最后一个节点的 id
 */
function findLastNodeId(node: DingNode): string {
  if (isConditionNode(node)) {
    if (node.children) return findLastNodeId(node.children)
    return node.id
  }
  if (isForkNode(node)) {
    // fork 的"最后节点"是 joinChildren（如果有）；否则是 fork 节点本身
    if (node.joinChildren) return findLastNodeId(node.joinChildren)
    return node.id
  }
  if (node.children) return findLastNodeId(node.children)
  return node.id
}
