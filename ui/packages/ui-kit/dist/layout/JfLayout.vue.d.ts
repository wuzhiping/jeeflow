import type { Component } from 'vue';
export interface JfMenuItem {
    /** 唯一 key（路由 path 或 id） */
    key: string;
    title: string;
    /** 图标：JfIcon 图标名（home/apply/todo/done/mine/cc/define/design/surrogate…）；未知名降级文本 */
    icon?: string;
    /** 权限码：任一命中才显示（superAdmin 由宿主 hasPermission 处理） */
    perms?: string[];
    /** 页面组件（内容区渲染） */
    component?: Component;
    /** 外部链接（iframe/跳转，与 component 二选一） */
    href?: string;
}
type __VLS_Props = {
    menus: JfMenuItem[];
    title?: string;
    logo?: string;
    /** 初始选中 key */
    defaultKey?: string;
};
declare var __VLS_4: {}, __VLS_9: {
    current: JfMenuItem | null;
};
type __VLS_Slots = {} & {
    'header-right'?: (props: typeof __VLS_4) => any;
} & {
    default?: (props: typeof __VLS_9) => any;
};
declare const __VLS_component: import("vue").DefineComponent<__VLS_Props, {}, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    select: (key: string) => any;
}, string, import("vue").PublicProps, Readonly<__VLS_Props> & Readonly<{
    onSelect?: ((key: string) => any) | undefined;
}>, {
    title: string;
}, {}, {}, {}, string, import("vue").ComponentProvideOptions, false, {}, any>;
declare const _default: __VLS_WithSlots<typeof __VLS_component, __VLS_Slots>;
export default _default;
type __VLS_WithSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
