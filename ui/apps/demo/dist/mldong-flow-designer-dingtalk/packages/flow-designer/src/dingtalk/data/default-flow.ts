import type { GraphNode, GraphEdge } from '../types'

/**
 * 默认流程初始化数据（标准图数据格式，与 examples/assets/wf-leave.json 同构）
 *
 * 结构：start → apply(发起申请) → end
 * 依据 jeeflow-spec（docs/guide/02-flow-definition.md §2.1）：
 *   start 后第一个任务节点必须是"发起申请"节点，assignee = "applicant"（引擎解析为发起人）
 * 钉钉模式在编辑空流程时自动以此为基础渲染，用户可直接继续添加节点。
 * 保存时 treeToGraph 输出与之一致的标准结构（含 x/y/text/properties）。
 */
export const DEFAULT_FLOW_NODES: GraphNode[] = [
  {
    id: 'start',
    type: 'snaker:start',
    x: 280,
    y: 280,
    properties: { width: 120, height: 80 },
    text: { x: 280, y: 320, value: '开始' },
  },
  {
    id: 'apply',
    type: 'snaker:task',
    x: 480,
    y: 280,
    properties: {
      width: 120,
      height: 80,
      // 发起申请节点：assignee = "applicant"（引擎解析为发起人）
      assignee: 'applicant',
      taskType: 'Major',
      performType: 'ANY',
      autoExecute: 'N',
    },
    text: { x: 480, y: 280, value: '发起申请' },
  },
  {
    id: 'end',
    type: 'snaker:end',
    x: 680,
    y: 280,
    properties: { width: 120, height: 80 },
    text: { x: 680, y: 320, value: '结束' },
  },
]

export const DEFAULT_FLOW_EDGES: GraphEdge[] = [
  {
    id: 't1',
    type: 'snaker:transition',
    sourceNodeId: 'start',
    targetNodeId: 'apply',
    properties: {},
  },
  {
    id: 't2',
    type: 'snaker:transition',
    sourceNodeId: 'apply',
    targetNodeId: 'end',
    properties: {},
  },
]
