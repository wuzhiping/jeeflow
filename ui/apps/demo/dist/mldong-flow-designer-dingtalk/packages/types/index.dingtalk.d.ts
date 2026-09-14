import type { DefineComponent, ExtractPropTypes } from "vue";
import { MldongFlowDesignerProps } from '../flow-designer/src/types/props.ts'
type mProps = Partial<ExtractPropTypes<typeof MldongFlowDesignerProps>>

declare module 'mldong-flow-designer-dingtalk' {
  const _default: DefineComponent<mProps>
  export default _default
}
// 导出所有的类型（自包含，不依赖 @logicflow/core）
export * from '../flow-designer/src/types'
// 钉钉设计器 API 类型（与画布模式 lf 实例兼容命名）
export type { FDDesignerAPI, FDEventCenter, FDEventName, FDNodeData } from '../flow-designer/src/dingtalk/types/api'
