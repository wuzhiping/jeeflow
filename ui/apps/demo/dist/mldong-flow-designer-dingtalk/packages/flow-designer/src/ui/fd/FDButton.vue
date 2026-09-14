<template>
  <button
    class="fd-btn"
    :class="[
      `fd-btn--${type}`,
      `fd-btn--${size}`,
      { 'fd-btn--circle': circle }
    ]"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
/**
 * FDButton —— 自研按钮（替代 antd/element-plus Button）
 * 仅覆盖流程设计器用到的能力：type / size / circle / disabled
 */
withDefaults(defineProps<{
  type?: 'default' | 'primary' | 'danger'
  size?: 'large' | 'middle' | 'small'
  circle?: boolean
  disabled?: boolean
}>(), {
  type: 'default',
  size: 'middle',
  circle: false,
  disabled: false
})

defineEmits<{
  (e: 'click', evt: MouseEvent): void
}>()
</script>

<style scoped>
.fd-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.fd-btn--large {
  height: 40px;
  padding: 0 20px;
}

.fd-btn--middle {
  height: 32px;
  padding: 0 16px;
}

.fd-btn--small {
  height: 26px;
  padding: 0 10px;
  font-size: 13px;
}

.fd-btn--circle {
  border-radius: 50%;
  padding: 0;
  width: 32px;
}

.fd-btn--circle.fd-btn--large {
  width: 40px;
}

.fd-btn--circle.fd-btn--small {
  width: 26px;
}

.fd-btn--default:hover {
  color: #1677ff;
  border-color: #1677ff;
}

.fd-btn--primary {
  background: #1677ff;
  border-color: #1677ff;
  color: #fff;
}

.fd-btn--primary:hover {
  background: #4096ff;
  border-color: #4096ff;
}

.fd-btn--danger {
  color: #ff4d4f;
  border-color: #ff4d4f;
  background: #fff;
}

.fd-btn--danger:hover {
  color: #ff7875;
  border-color: #ff7875;
}

.fd-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.fd-btn--primary:disabled:hover {
  background: #1677ff;
  border-color: #1677ff;
}

.fd-btn--default:disabled:hover {
  color: #333;
  border-color: #d9d9d9;
}
</style>
