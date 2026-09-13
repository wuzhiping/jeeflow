/**
 * 统一门面 API 层（@mldong/jeeflow-ui）
 *
 * 封装规范 06 的 40 个 action。**框架无关**：不依赖 Vue/axios——
 * 通过依赖注入接入任意宿主（baseUrl / token / 当前用户 / 权限码）。
 * Vue 宿主用 JeeflowUiProvider（provider.ts）注入；非 Vue 宿主可自行持有 api 实例。
 */
import type { PageResult, PageQuery, DefineRow, DefineDetail, InstanceRow, InstanceDetail, TaskRow, TaskDetail, HighLightData, ApprovalRecordRow, DesignRow, ListByTypeItem, SurrogateRow, CandidateRow, JumpableTaskRow, AssigneeTextRow, SubmitTypeValue, StatsOverview, StatsTrendRow, StatsGroupRow, StatsGranularity, StatsDimension } from './types';
import type { JeeflowHostAdapters, JeeflowUserRow } from './adapters';
export interface JeeflowApiConfig {
    /** 后端根地址，如 http://localhost:8100（门面路由为 {baseUrl}/wf/{action}）；
     *  可传函数——每次请求时求值，支持宿主 SPA 内热切换后端 */
    baseUrl: string | (() => string);
    /** 当前用户 id 提供器——对应门面契约 operator（"我的"语义依赖） */
    getOperator: () => string;
    /** 登录态提供器（可选）：注入 Authorization: Bearer <token> */
    getToken?: () => string | null;
    /** 权限码判断器（可选）：宿主按 wf:{action} 权限码控制按钮显隐 */
    hasPermission?: (codes: string[]) => boolean;
    /**
     * 宿主能力注入（选人 / 角色 / 字典 / 上传）。
     * ui-kit 不调用宿主 REST；缺哪个 adapter，对应控件降级。
     */
    adapters?: JeeflowHostAdapters;
    /**
     * @deprecated 使用 adapters.listUsers。无任务上下文的选人回退。
     * 有 taskId 且 scene=candidate 时 JfUserPicker 仍走 candidatePage。
     */
    listUsers?: (keyword: string) => Promise<JeeflowUserRow[]>;
    /** 自定义 fetch（可选）：测试注入/SSR/超时控制 */
    fetchImpl?: typeof fetch;
    /** 请求拦截（可选）：统一加 header / 改 body */
    onRequest?: (action: string, body: Record<string, unknown>) => void;
}
export declare class JeeflowApiError extends Error {
    code: number;
    constructor(code: number, msg: string);
}
export declare function createJeeflowApi(cfg: JeeflowApiConfig): {
    api: {
        /** 底层调用（自定义 action 扩展用） */
        flow: <T = unknown>(action: string, args?: Record<string, unknown>) => Promise<T>;
        processDefine: {
            page: (q?: PageQuery) => Promise<PageResult<DefineRow>>;
            detail: (id: string) => Promise<DefineDetail>;
            startAndExecute: (defineId: string, formData?: Record<string, unknown>) => Promise<{
                processInstanceId: string;
            }>;
            /** 发布流程定义：流程 JSON 顶层展开（对齐 vben5；字符串 content 兼容） */
            deploy: (content: string | object) => Promise<{
                processDefineId: string;
            }>;
            /** 重新发布：流程 JSON 顶层展开（对齐 vben5；字符串 content 兼容） */
            redeploy: (defineId: string, content: string | object) => Promise<void>;
            remove: (ids: string | string[]) => Promise<void>;
            upAndDown: (ids: string | string[], state: number) => Promise<void>;
            getLastByName: (name: string) => Promise<DefineRow>;
        };
        processInstance: {
            page: (q?: PageQuery) => Promise<PageResult<InstanceRow>>;
            detail: (id: string) => Promise<InstanceDetail>;
            startAndExecute: (defineId: string, formData?: Record<string, unknown>) => Promise<{
                processInstanceId: string;
            }>;
            withdraw: (id: string) => Promise<void>;
            bizData: (processInstanceId: string) => Promise<Record<string, any>>;
            highLight: (id: string) => Promise<HighLightData>;
            approvalRecord: (id: string) => Promise<ApprovalRecordRow[]>;
            getAssigneeTextData: (id: string, includeNodeName?: boolean) => Promise<AssigneeTextRow[]>;
            createCCInstance: (processInstanceId: string, actorIds: string[]) => Promise<void>;
            updateCCStatus: (processInstanceId: string) => Promise<void>;
            ccList: (q?: PageQuery) => Promise<PageResult<InstanceRow>>;
            /** 指标卡统计（issues/103 v1.1；全局口径不带 operator 过滤；登录即可） */
            statsOverview: (q?: {
                start?: string;
                end?: string;
                stateIn?: number[];
            }) => Promise<StatsOverview>;
            /** 时间趋势：start/end 必填（yyyy-MM-dd HH:mm:ss），连续桶补 0 */
            statsTrend: (q: {
                start: string;
                end: string;
                granularity: StatsGranularity;
            }) => Promise<StatsTrendRow[]>;
            /** 维度分组：9 个纯列 dimension，Top N 降序；stuckNode/stuckApprover 实时快照忽略 start/end */
            statsGroup: (q: {
                dimension: StatsDimension;
                start?: string;
                end?: string;
                limit?: number;
            }) => Promise<StatsGroupRow[]>;
        };
        processTask: {
            todoList: (q?: PageQuery) => Promise<PageResult<TaskRow>>;
            doneList: (q?: PageQuery) => Promise<PageResult<TaskRow>>;
            execute: (taskId: string, submitType: SubmitTypeValue, extra?: Record<string, unknown>) => Promise<void>;
            detail: (id: string) => Promise<TaskDetail>;
            jumpAbleTaskNameList: (processInstanceId: string) => Promise<JumpableTaskRow[]>;
            candidatePage: (processTaskId: string, q?: PageQuery) => Promise<PageResult<CandidateRow>>;
            surrogate: (processTaskId: string, actorIds: string[]) => Promise<void>;
            addCandidate: (processTaskId: string, actorIds: string[]) => Promise<void>;
            latest: (processInstanceId: string) => Promise<TaskRow | null>;
        };
        processDesign: {
            page: (q?: PageQuery) => Promise<PageResult<DesignRow>>;
            detail: (id: string) => Promise<DesignRow & {
                jsonObject?: Record<string, any>;
                his?: unknown[];
            }>;
            save: (design: Record<string, unknown>) => Promise<{
                id: string;
            }>;
            update: (id: string, fields: Record<string, unknown>) => Promise<void>;
            /** 保存设计稿：流程 JSON 顶层展开（对齐 vben5 契约；字符串 content 兼容） */
            updateDefine: (processDesignId: string, json: string | object) => Promise<void>;
            remove: (ids: string | string[]) => Promise<void>;
            deploy: (id: string) => Promise<{
                processDefineId: string;
            }>;
            redeploy: (id: string) => Promise<{
                processDefineId: string;
            }>;
            /** 按类型分组（返回 Map<type, items>；boot3 前端转换见 guide） */
            listByType: () => Promise<Record<string, ListByTypeItem[]>>;
            /** listByType 的 boot3 形态（[{type,title,items}]），与参考实现转发层一致 */
            listByTypeAsArray: () => Promise<{
                type: string;
                title: string;
                items: ListByTypeItem[];
            }[]>;
        };
        processSurrogate: {
            page: (q?: PageQuery) => Promise<PageResult<SurrogateRow>>;
            save: (surrogate: Record<string, unknown>) => Promise<{
                id: string;
            }>;
            remove: (id: string) => Promise<void>;
        };
    };
    can: (codes: string[]) => boolean;
};
export type JeeflowApi = ReturnType<typeof createJeeflowApi>['api'];
export type JeeflowCan = ReturnType<typeof createJeeflowApi>['can'];
