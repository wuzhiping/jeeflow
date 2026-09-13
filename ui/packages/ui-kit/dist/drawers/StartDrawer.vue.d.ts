type __VLS_Props = {
    visible: boolean;
    define?: Record<string, any> | null;
    title?: string;
    width?: string;
};
declare const _default: import("vue").DefineComponent<__VLS_Props, {}, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "update:visible": (v: boolean) => any;
    started: (instanceId: string) => any;
}, string, import("vue").PublicProps, Readonly<__VLS_Props> & Readonly<{
    "onUpdate:visible"?: ((v: boolean) => any) | undefined;
    onStarted?: ((instanceId: string) => any) | undefined;
}>, {
    title: string;
    width: string;
}, {}, {}, {}, string, import("vue").ComponentProvideOptions, false, {}, any>;
export default _default;
