/**
 * 轻量 toast（@mldong/jeeflow-ui）
 *
 * ui-kit 零 UI 框架依赖——成功/错误提示不引 Element Plus，
 * 宿主自带消息体系时可忽略此工具。
 */
export declare const toast: {
    success: (msg: string) => void;
    error: (msg: string) => void;
    info: (msg: string) => void;
};
/** 全局样式（style.css 引入后生效：.jf-toast-host/.jf-toast） */
