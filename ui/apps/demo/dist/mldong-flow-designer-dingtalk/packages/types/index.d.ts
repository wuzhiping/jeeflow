import type { DefineComponent, ExtractPropTypes } from "vue";
import type * as LogicFlowCore from '@logicflow/core';
import type * as LogicFlowExtension from '@logicflow/extension';
import { MldongFlowDesignerProps } from '../flow-designer/src/types/props.ts'
type mProps = Partial<ExtractPropTypes<typeof MldongFlowDesignerProps>>

declare module 'mldong-flow-designer-plus' {
  const _default: DefineComponent<mProps>
  export default _default
  export const LogicFlowCore: typeof LogicFlowCore;
  export const LogicFlowExtension: typeof LogicFlowExtension;
}
// 导出所有的类型
export * from '../flow-designer/src/types'