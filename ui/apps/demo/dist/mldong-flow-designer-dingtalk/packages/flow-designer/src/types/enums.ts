/**
 * 颜色枚举
 */
export enum ColorEnum {
  primaryColor = '#3068EC', // 主题色
  edgePrimaryColor = '#C9CCD4', // 边主题色
  activeColor = '#FA7E55', // 进行时节点颜色
  historyColor = '#28C7A3', // 历史节点/边颜色
  backgroundColor = '#FFFFFF' // 画布背景颜色
}
/**
 * 节点状态枚举
 */
export enum NodeStateEnum {
  history = 'history',
  active = 'active',
  normal = 'normal'
}
/**
 * 节点类型枚举
 */
export enum NodeTypeEnum {
  start = 'start',
  end = 'end',
  task = 'task',
  process = 'process',
  subProcess = 'subProcess',
  decision = 'decision',
  fork = 'fork',
  join = 'join',
  custom = 'custom'
}