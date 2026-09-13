import 'mldong-flow-designer-dingtalk/lib/style.css';
import type { FlowGraph, HighLightData, AssigneeTextRow } from '../types';
type __VLS_Props = {
    graphData?: FlowGraph | Record<string, any> | null;
    highLight?: HighLightData | Record<string, any> | null;
    /** 节点处理人回显（getAssigneeTextData，对齐 vben5 assignee-text-data） */
    assigneeTextData?: AssigneeTextRow[] | null;
    /** 容器高度（默认铺满父容器） */
    height?: string;
    /** 主题色覆盖（默认蓝） */
    primaryColor?: string;
};
declare const _default: import("vue").DefineComponent<__VLS_Props, {}, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").PublicProps, Readonly<__VLS_Props> & Readonly<{}>, {
    assigneeTextData: AssigneeTextRow[] | null;
    height: string;
    primaryColor: string;
}, {}, {}, {}, string, import("vue").ComponentProvideOptions, false, {}, any>;
export default _default;
