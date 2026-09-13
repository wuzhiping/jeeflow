/**
 * 展示辅助（@mldong/jeeflow-ui）：状态标签/时间格式化（规范 06 §2.9 枚举）
 */
/** 实例状态 → 展示标签 */
export declare function stateLabel(s: number | string | null | undefined): string;
/** 实例状态 → JfBadge type */
export declare function stateBadgeType(s: number | string | null | undefined): 'doing' | 'done' | 'reject' | 'info';
/** 任务状态 → 展示标签 */
export declare function taskStateLabel(s: number | string | null | undefined): string;
/** 任务状态 → JfBadge type */
export declare function taskStateBadgeType(s: number | string | null | undefined): 'doing' | 'done' | 'reject' | 'info';
/** 时间格式化：yyyy-MM-dd HH:mm:ss 或宽松（非法时间原样返回） */
export declare function fmtTime(t: string | null | undefined, short?: boolean): string;
/** 流程 JSON 图中 start 的下一个任务节点（对齐 vben5 getFirstTaskNode） */
export declare function firstTaskNode(graph: any): any | null;
/** 按 taskName / 节点 id 定位任务节点 */
export declare function findTaskNode(graph: any, taskName?: string | null): any | null;
/** 流程 JSON 图中首个任务节点的 formKey（发起表单定位） */
export declare function firstTaskFormKey(graph: any): string;
/** 流程 JSON 图中任务节点列表（发起页 groupByType 需要） */
export declare function taskNodes(graph: any): Array<{
    id: string;
    displayName: string;
    form?: string;
}>;
/** 字段权限：1 只读 / 2 可编 / 3 隐藏 */
export declare const FieldPerm: {
    readonly READ_ONLY: 1;
    readonly EDIT: 2;
    readonly HIDDEN: 3;
};
export type FieldPermValue = (typeof FieldPerm)[keyof typeof FieldPerm];
/** 解析 __schema__：优先 vben5 columns，兼容旧 fields */
export interface SchemaColumn {
    fieldName: string;
    remark: string;
    component: string;
    ext?: {
        span?: number;
        required?: number | boolean;
        placeholder?: string;
        options?: Array<{
            label: string;
            value: string | number;
        }>;
        [key: string]: unknown;
    };
}
export interface ParsedSchema {
    layout?: string;
    columns: SchemaColumn[];
}
export declare function parseSchema(graph: any): ParsedSchema | null;
/** 从 schema 提取 fieldLabels（兼容旧 SchemaForm fieldLabels 用法） */
export declare function schemaFieldLabels(graph: any, prefix?: string): Record<string, string>;
/**
 * 解析节点字段权限。enableFieldPerm 未开则一律可编。
 * 键优先 PERMISSION_f_{name}，再 PERMISSION_{name}（集成规范双格式）。
 */
export declare function resolveFieldPerm(graph: any, taskNode: any, fieldName: string): FieldPermValue;
/** 列 → fieldName 权限表（同时写入裸名与 f_ 前缀，方便 SchemaForm 查找） */
export declare function buildPermissionMap(graph: any, taskNode: any, columns?: SchemaColumn[]): Record<string, FieldPermValue>;
export type ActionBtnKey = 'AGREE' | 'REJECT' | 'ROLLBACK' | 'ROLLBACK_TO_OPERATOR' | 'JUMP' | 'COUNTERSIGN_DISAGREE' | 'ADD_CANDIDATE' | 'SURROGATE';
export declare function isCountersign(performType: unknown): boolean;
/** 有 actionBtns 用配置；否则按会签/普通给默认集 */
export declare function resolveActionBtns(taskNode: any, performType?: unknown): ActionBtnKey[];
/** submitType → 中文（无字典服务，写死对照表） */
export declare function submitTypeLabel(n: number | string | null | undefined): string;
/** jsonObject 上的发起附加项开关 */
export declare function initiateExtraFlags(graph: any): {
    selectUser: boolean;
    cc: boolean;
    reason: boolean;
    attachment: boolean;
    any: boolean;
};
/** 从实例/任务变量里抽出 f_* 表单数据 */
export declare function extractBizFormData(source: any): Record<string, any>;
/** SchemaWfForm / SchemaTfForm 是 vben5 元数据表单占位名，走内置 SchemaForm */
export declare function isBuiltinSchemaFormKey(formKey: string | null | undefined): boolean;
