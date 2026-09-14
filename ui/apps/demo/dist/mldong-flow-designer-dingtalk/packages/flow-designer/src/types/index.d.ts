import type { VNode, PropType } from "vue";
/**
 * 图数据结构（自包含，与 @logicflow/core 的 GraphConfigData 结构等价）
 * 不直接引用 @logicflow/core，使钉钉精简包（mldong-flow-designer-dingtalk）
 * 的类型链可在无 LogicFlow 依赖环境下解析
 */
export declare type FDGraphConfigData = {
  nodes?: Array<Record<string, any>>;
  edges?: Array<Record<string, any>>;
}
/**
 * 流程设计器配置数据
 */
export declare type FDConfigData = {
  name?: string; // 唯一编码-流程名称
  displayName?: string; // 流程显示名称
  type?: string; // 流程类型
  instanceUrl?: string; // 启动实例要填写的表单key
  expireTime?: string; // 期待完成时间变量key
  instanceNoClass?: string; // xx.DefaultNoGenerator	实例编号生成器实现类
  mode?: 'canvas' | 'dingtalk'; // 渲染模式
} & FDGraphConfigData
/**
 * 主题颜色配置
 */
export declare type FDThemeConfig = {
  primaryColor?: string; // 主题色
  edgePrimaryColor?: string; // 边主题色
  activeColor?: string; // 进行时节点颜色
  historyColor?: string; // 历史节点/边颜色
  backgroundColor ?: string;// 画布背景颜色
}
/**
 * 节点成员进度（nodeProgress 列表项）
 */
export declare type FDNodeProgressMember = {
  id: string; // 用户ID
  name: string; // 用户姓名（后端组装）
  done?: boolean; // 是否已完成（历史任务办理人）
  active?: boolean; // 当前轮到的办理人（进行中任务 / 顺序会签）
}
/**
 * 高亮数据类型
 */
export declare type FDHighLightType = {
  historyNodeNames?: Array<string>; // 历史节点名称
  historyEdgeNames?: Array<string>; // 历史边名称
  activeNodeNames?: Array<string>; // 活跃节点名称
  /**
   * 节点成员进度（可选）：key=节点 id，value=该节点办理人列表及完成状态
   * 任意节点可带（历史节点 done、进行中节点 active）；会签节点额外带 type 区分并行/顺序
   * 钉钉模式 NodeCard 存在时渲染成员列表回显，不存在时保持现状
   */
  nodeProgress?: {
    [nodeId: string]: {
      type?: 'PARALLEL' | 'SEQUENTIAL'; // 会签类型（仅会签节点）
      members: Array<FDNodeProgressMember>;
    }
  }
}
/**
 * 拖拽面板数据类型
 */
export declare type FDPatternItem = {
  type?: string;
  text?: string;
  label?: string;
  icon?: string;
  className?: string;
  properties?: object;
  callback?: () => void;
  hide?: boolean; // 是否隐藏
  sort?: number; // 排序字段
  drawerTitle?: string;// 抽屉标题
  nodeClick?: (e: any) => void;
  form?: FDFormType; // 表单配置
};
/**
 * 表单数据类型
 */
export declare type FDFormType = {
  labelWidth?: string;
  formItems: Array<FDFormItemType>;
} 
/**
 * 表单项数据类型
 */
export declare type FDFormItemType = {
  name: string; // 表单项名称
  label?: string; // 表单项标签
  component?: 'Input' | 'Select'; // 表单组件
  render?: (args: any) => VNode;
  componentProps?: any; // 表单组件属性
  slot?: string;
  helpMessage?: string | Array<string>;
  formItemProps?: any;
  // 默认值
  defaultValue?: any;
} 
/**
 * 控制面板数据类型
 */
export declare type FDControlItem = {
  key?: string; // 唯一编码
  iconClass?: string; // 图标类
  title?: string; // 标题
  text?: string; // 文本
  onClick?: Function // 事件函数
  hide?: boolean; // 是否隐藏
  sort?: number; // 排序字段
}