import type { JeeflowUserPickerScene } from '../adapters';
type __VLS_Props = {
    /** 已选 userId 列表（v-model） */
    modelValue?: string[];
    /** 任务上下文：scene=candidate 时走 candidatePage */
    taskId?: string | null;
    /** 选人场景；有 taskId 时默认 candidate，否则 cc */
    scene?: JeeflowUserPickerScene;
    /** 流程 JSON selectUserApi，透传给 adapters.listUsers */
    apiHint?: string;
    placeholder?: string;
    disabled?: boolean;
};
declare const _default: import("vue").DefineComponent<__VLS_Props, {}, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "update:modelValue": (v: string[]) => any;
    change: (v: string[]) => any;
}, string, import("vue").PublicProps, Readonly<__VLS_Props> & Readonly<{
    "onUpdate:modelValue"?: ((v: string[]) => any) | undefined;
    onChange?: ((v: string[]) => any) | undefined;
}>, {
    placeholder: string;
    modelValue: string[];
    disabled: boolean;
    taskId: string | null;
    apiHint: string;
}, {}, {}, {}, string, import("vue").ComponentProvideOptions, false, {}, any>;
export default _default;
