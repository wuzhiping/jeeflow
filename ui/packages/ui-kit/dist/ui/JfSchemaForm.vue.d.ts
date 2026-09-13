import type { SchemaColumn } from '../helpers';
import { type FieldPermValue } from '../helpers';
type __VLS_Props = {
    modelValue?: Record<string, any>;
    schema?: {
        layout?: string;
        columns: SchemaColumn[];
    } | null;
    fieldLabels?: Record<string, string>;
    permissions?: Record<string, FieldPermValue>;
    readonly?: boolean;
    fieldPrefix?: string;
    emptyHint?: string;
};
declare function validate(): string | null;
declare const _default: import("vue").DefineComponent<__VLS_Props, {
    validate: typeof validate;
}, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "update:modelValue": (v: Record<string, any>) => any;
}, string, import("vue").PublicProps, Readonly<__VLS_Props> & Readonly<{
    "onUpdate:modelValue"?: ((v: Record<string, any>) => any) | undefined;
}>, {
    modelValue: Record<string, any>;
    schema: {
        layout?: string;
        columns: SchemaColumn[];
    } | null;
    fieldLabels: Record<string, string>;
    permissions: Record<string, FieldPermValue>;
    readonly: boolean;
    fieldPrefix: string;
    emptyHint: string;
}, {}, {}, {}, string, import("vue").ComponentProvideOptions, false, {}, any>;
export default _default;
