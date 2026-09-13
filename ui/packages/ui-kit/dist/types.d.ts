/**
 * 统一门面契约类型（@mldong/jeeflow-ui）
 *
 * 与 jeeflow-doc 规范 06 · 统一门面完整接口文档一一对应：
 *  - id 一律 string（雪花 id > 2^53，四语言出口已保证）
 *  - 时间一律 `yyyy-MM-dd HH:mm:ss`
 *  - 响应 `{code, msg, data}`：code=0 成功 / 99999999 业务失败
 *  - 分页 `{pageNum, pageSize, recordCount, totalPage, rows}`
 */
export interface JeeflowResponse<T = unknown> {
    code: number;
    msg: string;
    data: T;
}
export interface PageResult<T> {
    pageNum: number;
    pageSize: number;
    recordCount: number;
    totalPage: number;
    rows: T[];
}
/** 分页/过滤查询参数（m_ 前缀三段式过滤，见规范 06 §2.2） */
export interface PageQuery {
    pageNum?: number;
    pageSize?: number;
    orderBy?: string;
    [key: string]: unknown;
}
/** 执行类型（processTask/execute 的 submitType） */
export declare const SubmitType: {
    readonly APPLY: 0;
    readonly AGREE: 1;
    readonly REJECT: 2;
    readonly ROLLBACK: 3;
    readonly JUMP: 4;
    readonly RE_APPLY: 5;
    readonly ROLLBACK_TO_OPERATOR: 6;
    readonly COUNTERSIGN_DISAGREE: 20;
};
export type SubmitTypeValue = (typeof SubmitType)[keyof typeof SubmitType];
/** 任务状态 taskState / 实例状态 state */
export declare const TaskState: {
    readonly DOING: 10;
    readonly FINISHED: 20;
    readonly WITHDRAW: 30;
    readonly INTERRUPT: 40;
    readonly PENDING: 50;
    readonly ABANDON: 99;
};
export type TaskStateValue = (typeof TaskState)[keyof typeof TaskState];
/** 参与方式 performType */
export declare const PerformType: {
    readonly NORMAL: 0;
    readonly COUNTERSIGN: 1;
};
export type PerformTypeValue = (typeof PerformType)[keyof typeof PerformType];
/** 会签模式 countersignType */
export declare const CountersignType: {
    readonly PARALLEL: "PARALLEL";
    readonly SEQUENTIAL: "SEQUENTIAL";
    readonly RATIO: "RATIO";
};
/** processDefine/page 行 */
export interface DefineRow {
    id: string;
    name: string;
    displayName: string;
    type: string;
    state: number;
    version: number;
    createTime?: string | null;
    createUser?: string | null;
    updateTime?: string | null;
    updateUser?: string | null;
}
export interface DefineDetail extends DefineRow {
    jsonObject?: Record<string, any> | null;
}
/** processInstance/page 行 */
export interface InstanceRow {
    id: string;
    parentId?: string | null;
    processDefineId: string;
    state: number;
    parentNodeName?: string | null;
    businessNo?: string | null;
    operator?: string | null;
    expireTime?: string | null;
    variable?: Record<string, any> | null;
    ext: Record<string, any>;
    displayName?: string | null;
    version?: number | null;
    processDefineName?: string | null;
    processDefineDisplayName?: string | null;
    processDefineVersion?: number | null;
    createTime?: string | null;
    createUser?: string | null;
    updateTime?: string | null;
    updateUser?: string | null;
}
/** 任务行（taskVo，taskDetail/todoList/doneList 通用） */
export interface TaskRow {
    id: string;
    processInstanceId: string;
    taskName: string;
    displayName: string;
    taskType?: string | null;
    performType?: number | null;
    taskState: number;
    operator?: string | null;
    formKey?: string | null;
    taskParentId?: string | null;
    taskActorIdList?: string[];
    taskFormData?: Record<string, any>;
    ext?: Record<string, any>;
    instanceExt?: Record<string, any> | null;
    finishTime?: string | null;
    expireTime?: string | null;
    createTime?: string | null;
    processDefineName?: string | null;
    processDefineDisplayName?: string | null;
    version?: number | null;
    [key: string]: unknown;
}
/** processTask/detail 额外字段 */
export interface TaskDetail extends TaskRow {
    executable: boolean;
    jsonObject?: Record<string, any> | null;
    taskModel?: {
        name: string;
        displayName: string;
        type: string;
    } | null;
}
/** processInstance/detail */
export interface InstanceDetail {
    id: string;
    parentId?: string | null;
    processDefineId: string;
    state: number;
    parentNodeName?: string | null;
    businessNo?: string | null;
    operator?: string | null;
    variables?: Record<string, any> | null;
    formData?: Record<string, any>;
    displayName?: string | null;
    name?: string | null;
    version?: number | null;
    jsonObject?: Record<string, any> | null;
    tasks: TaskRow[];
    activeTaskList: TaskRow[];
    createTime?: string | null;
    createUser?: string | null;
}
/** processInstance/highLight */
export interface HighLightData {
    activeNodeNames: string[];
    historyNodeNames: string[];
    historyEdgeNames: string[];
    nodeProgress: Record<string, NodeProgress>;
}
export interface NodeProgress {
    members: Array<{
        id: string;
        name: string;
        done?: boolean;
        active?: boolean;
    }>;
    type?: 'PARALLEL' | 'SEQUENTIAL';
}
/** processInstance/approvalRecord 行 */
export interface ApprovalRecordRow {
    taskName: string;
    displayName: string;
    taskType?: string | null;
    performType?: number | null;
    taskState?: number | null;
    operator?: string | null;
    finishTime?: string | null;
    variable?: Record<string, any> | null;
    ext?: Record<string, any> | null;
}
/** processDesign/page 行 */
export interface DesignRow {
    id: string;
    name: string;
    displayName: string;
    type: string;
    icon?: string | null;
    isDeployed: number;
    remark?: string | null;
    createTime?: string | null;
    createUser?: string | null;
    updateTime?: string | null;
    updateUser?: string | null;
}
/** processDesign/listByType：{type: items[]} 或 boot3 转换后 [{type,title,items}] */
export interface ListByTypeItem {
    processDesignId: string;
    name: string;
    displayName: string;
    icon?: string | null;
    remark?: string | null;
    processDefineId?: string | null;
    processDefineState?: number | null;
    jsonObject?: Record<string, any> | null;
}
/** processSurrogate/page 行 */
export interface SurrogateRow {
    id: string;
    processName?: string | null;
    operator?: string | null;
    surrogate?: string | null;
    startTime?: string | null;
    endTime?: string | null;
    enabled?: number | null;
    createTime?: string | null;
    createUser?: string | null;
    updateTime?: string | null;
    updateUser?: string | null;
}
/** processTask/candidatePage 行 */
export interface CandidateRow {
    userId: string;
    realName: string;
}
/** processTask/jumpAbleTaskNameList 行 */
export interface JumpableTaskRow {
    label: string;
    value: string;
}
/** processInstance/getAssigneeTextData 行 */
export interface AssigneeTextRow {
    value: string;
    label: string;
}
/** 流程 JSON 图（LogicFlow 模型，渲染/表单定位用） */
export interface FlowGraph {
    name?: string;
    displayName?: string;
    type?: string;
    relTableName?: string;
    persistMode?: string;
    nodes: Array<{
        id: string;
        type: string;
        x?: number;
        y?: number;
        properties?: Record<string, any>;
        text?: {
            value?: string;
        };
    }>;
    edges: Array<{
        id: string;
        sourceNodeId: string;
        targetNodeId: string;
        properties?: Record<string, any>;
        text?: {
            value?: string;
        };
    }>;
}
/** stats/trend 时间粒度 */
export type StatsGranularity = 'hour' | 'day' | 'week' | 'month';
/** stats/group 维度（9 个全纯列） */
export type StatsDimension = 'state' | 'define' | 'category' | 'approver' | 'applicant' | 'node' | 'stuckNode' | 'stuckApprover' | 'durationBucket';
/** stats/overview 指标卡（全局口径；expire_time 未填充时 overdueTaskCount/onTimeRate 恒 0，前端可隐藏） */
export interface StatsOverview {
    total: number;
    inProgress: number;
    completed: number;
    rejected: number;
    withdrawn: number;
    suspended: number;
    /** 当日新发起（恒按服务器当天，不受 start/end 影响） */
    todayNew: number;
    /** 已完成实例平均时长（秒） */
    avgDurationSeconds: number;
    /** 驳回率：rejected / max(1, completed+rejected) */
    rejectRate: number;
    /** 全系统进行中任务数（实时） */
    pendingTaskCount: number;
    /** 逾期未办任务数（实时；expire_time 未填充恒 0） */
    overdueTaskCount: number;
    /** 会签占比（已完成任务） */
    countersignRate: number;
    /** 及时办结率（expire_time 非空的已完成任务） */
    onTimeRate: number;
}
/** stats/trend 行：连续桶补 0；bucket 格式随粒度（day=yyyy-MM-dd） */
export interface StatsTrendRow {
    bucket: string;
    started: number;
    finished: number;
}
/** stats/group 行：count 降序；state 维度 label 可空（前端走字典） */
export interface StatsGroupRow {
    key: string;
    label: string | null;
    count: number;
    /** 仅 define/node 维度有 */
    avgDurationSeconds?: number;
}
