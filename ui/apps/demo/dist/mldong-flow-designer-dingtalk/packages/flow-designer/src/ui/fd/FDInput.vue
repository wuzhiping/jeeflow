<template>
  <input
    class="fd-input"
    :class="{ 'fd-input--disabled': disabled }"
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :readonly="readonly"
    @input="onInput"
  />
</template>

<script setup lang="ts">
/**
 * FDInput —— 自研单行输入框（替代 antd/element-plus Input）
 */
withDefaults(defineProps<{
  modelValue?: any
  type?: string
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
}>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  disabled: false,
  readonly: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: any): void
}>()

function onInput(evt: Event) {
  emit('update:modelValue', (evt.target as HTMLInputElement).value)
}
</script>

<style scoped>
.fd-input {
  width: 100%;
  height: 32px;
  padding: 4px 11px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.fd-input:hover {
  border-color: #4096ff;
}

.fd-input:focus {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.fd-input::placeholder {
  color: #bfbfbf;
}

.fd-input--disabled {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}
</style>
