/**
 * JeeflowUiProvider（@mldong/jeeflow-ui）
 *
 * Vue 宿主的统一注入入口——与后端门面的 3 个注入点前后端对称：
 *
 * ```
 * <JeeflowUiProvider :config="{
 *   baseUrl: '/api',
 *   getToken: () => store.token,
 *   getOperator: () => store.userId,
 *   hasPermission: (codes) => ...,
 *   adapters: { listUsers, getDict, upload },
 * }">
 *   <App />
 * </JeeflowUiProvider>
 * ```
 *
 * 提供：api（40 action）/ can / adapters / registerForm。
 * 未使用 Vue 的宿主可直接用 createJeeflowApi（api.ts）。
 */
import type { PropType } from 'vue';
import type { JeeflowApiConfig, JeeflowApi, JeeflowCan } from './api';
import { JeeflowUiKey } from './adapters';
import type { JeeflowHostAdapters } from './adapters';
import type { FormRegistry } from './form-registry';
export { JeeflowUiKey };
export interface JeeflowUiContext {
    api: JeeflowApi;
    can: JeeflowCan;
    registerForm: FormRegistry['register'];
    getForm: FormRegistry['get'];
    config: JeeflowApiConfig;
    /** 已解析（含顶层 listUsers 回退） */
    adapters: JeeflowHostAdapters;
}
export declare function createJeeflowUi(config: JeeflowApiConfig): JeeflowUiContext;
export declare function useJeeflowUi(): JeeflowUiContext;
export declare const JeeflowUiProvider: import("vue").DefineComponent<import("vue").ExtractPropTypes<{
    config: {
        type: PropType<JeeflowApiConfig>;
        required: true;
    };
}>, () => import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
    [key: string]: any;
}>[] | undefined, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").PublicProps, Readonly<import("vue").ExtractPropTypes<{
    config: {
        type: PropType<JeeflowApiConfig>;
        required: true;
    };
}>> & Readonly<{}>, {}, {}, {}, {}, string, import("vue").ComponentProvideOptions, true, {}, any>;
export type { JeeflowApiConfig };
