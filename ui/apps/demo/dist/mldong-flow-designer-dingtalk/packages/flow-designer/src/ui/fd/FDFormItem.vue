<template>
  <div class="fd-form-item">
    <div v-if="label || $slots.label" class="fd-form-item__label" :style="{ width: labelWidth }">
      <slot name="label">{{ label }}</slot>
    </div>
    <div class="fd-form-item__content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * FDFormItem —— 自研表单项（替代 antd/element-plus FormItem）
 * label 支持 prop 或 #label 插槽（helpMessage 问号提示场景用插槽）
 */
import { inject, computed, type ComputedRef } from 'vue'

defineProps<{
  label?: string
}>()

const injectedWidth = inject<ComputedRef<string>>('fdFormLabelWidth', computed(() => '120px'))
const labelWidth = computed(() => injectedWidth.value)
</script>

<style scoped>
.fd-form-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
}

.fd-form-item__label {
  flex-shrink: 0;
  padding-right: 12px;
  padding-top: 5px;
  font-size: 14px;
  color: #333;
  line-height: 22px;
  text-align: right;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  /* 带 helpMessage 问号图标时 label 不换行（宽度由 FDForm label-width 控制，双模式统一 120px） */
  white-space: nowrap;
}

.fd-form-item__content {
  flex: 1;
  min-width: 0;
}
</style>
