type __VLS_Props = {
    visible: boolean;
    taskId: string | null;
    width?: string;
    readonly?: boolean;
};
declare const _default: import("vue").DefineComponent<__VLS_Props, {}, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "update:visible": (v: boolean) => any;
    changed: () => any;
}, string, import("vue").PublicProps, Readonly<__VLS_Props> & Readonly<{
    "onUpdate:visible"?: ((v: boolean) => any) | undefined;
    onChanged?: (() => any) | undefined;
}>, {
    readonly: boolean;
    width: string;
}, {}, {}, {}, string, import("vue").ComponentProvideOptions, false, {}, any>;
export default _default;
