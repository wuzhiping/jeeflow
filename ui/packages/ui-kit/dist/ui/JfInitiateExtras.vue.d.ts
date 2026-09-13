type __VLS_Props = {
    graph?: Record<string, any> | null;
    taskId?: string | null;
    disabled?: boolean;
    ccActors?: string[];
    nextOperators?: string[];
    applyReason?: string;
    attachment?: string;
};
declare const _default: import("vue").DefineComponent<__VLS_Props, {}, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "update:ccActors": (v: string[]) => any;
    "update:nextOperators": (v: string[]) => any;
    "update:applyReason": (v: string) => any;
    "update:attachment": (v: string) => any;
}, string, import("vue").PublicProps, Readonly<__VLS_Props> & Readonly<{
    "onUpdate:ccActors"?: ((v: string[]) => any) | undefined;
    "onUpdate:nextOperators"?: ((v: string[]) => any) | undefined;
    "onUpdate:applyReason"?: ((v: string) => any) | undefined;
    "onUpdate:attachment"?: ((v: string) => any) | undefined;
}>, {
    disabled: boolean;
    taskId: string | null;
    graph: Record<string, any> | null;
    ccActors: string[];
    nextOperators: string[];
    applyReason: string;
    attachment: string;
}, {}, {}, {}, string, import("vue").ComponentProvideOptions, false, {}, any>;
export default _default;
