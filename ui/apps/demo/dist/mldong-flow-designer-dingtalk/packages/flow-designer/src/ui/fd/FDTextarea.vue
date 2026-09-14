<template>
  <textarea
    class="fd-textarea"
    :class="{ 'fd-textarea--disabled': disabled }"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :readonly="readonly"
    :rows="rows"
    @input="onInput"
  ></textarea>
</template>

<script setup lang="ts">
/**
 * FDTextarea —— 自研多行输入框（替代 antd Input.TextArea / element-plus Input[textarea]）
 */
withDefaults(defineProps<{
  modelValue?: any
  placeholder?: string
  rows?: number
  disabled?: boolean
  readonly?: boolean
}>(), {
  modelValue: '',
  placeholder: '',
  rows: 4,
  disabled: false,
  readonly: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: any): void
}>()

function onInput(evt: Event) {
  emit('update:modelValue', (evt.target as HTMLTextAreaElement).value)
}
</script>

<style scoped>
.fd-textarea {
  width: 100%;
  padding: 8px 11px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  box-sizing: border-box;
  resize: vertical;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.fd-textarea:hover {
  border-color: #4096ff;
}

.fd-textarea:focus {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.fd-textarea::placeholder {
  color: #bfbfbf;
}

.fd-textarea--disabled {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}
</style>
