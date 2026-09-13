/**
 * 表单注册表（@mldong/jeeflow-ui）
 *
 * 业务表单无法通用——宿主通过 formKey 注册自己的表单组件：
 *
 * ```ts
 * import { useJeeflowUi } from '@mldong/jeeflow-ui'
 * const { registerForm } = useJeeflowUi()
 * registerForm('leave-form', LeaveForm)          // 发起/详情共用
 * registerForm('leave-approve', LeaveApprove)    // 办理页
 * ```
 *
 * 组件约定（props 契约）：
 *  - 发起/详情：modelValue（f_ 表单数据）、defineId、instanceId；
 *    详情场景额外收到 view：true 只读明细（命中注册组件即渲染，不再依赖 __schema__/f_* 回落）、
 *    false 表示发起人可重新提交（可编辑）。建议实现并 defineExpose({ validate })（返回错误文案或 null）。
 *  - 办理页：额外 task（TaskRow）、submitType 由宿主触发
 * 未注册的 formKey：渲染内置 SchemaForm（__schema__.columns + 组件类型/必填/字段权限）。
 * ApiDict/ApiSelect 走 adapters.getDict；Upload 走 adapters.upload；未注入则降级。
 */
import type { Component } from 'vue';
export interface FormOptions {
    /** 表单用途：start=发起 / approve=办理 / detail=详情（不传则三种都匹配） */
    scenes?: Array<'start' | 'approve' | 'detail'>;
}
export interface FormRegistry {
    register: (formKey: string, component: Component, options?: FormOptions) => void;
    get: (formKey: string, scene?: 'start' | 'approve' | 'detail') => Component | null;
    has: (formKey: string) => boolean;
    keys: () => string[];
}
export declare function createFormRegistry(): FormRegistry;
export { default as SchemaForm } from './ui/JfSchemaForm.vue';
