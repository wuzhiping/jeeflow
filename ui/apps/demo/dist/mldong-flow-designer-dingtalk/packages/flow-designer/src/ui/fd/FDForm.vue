<template>
  <div class="fd-form">
    <slot />
  </div>
</template>

<script setup lang="ts">
/**
 * FDForm —— 自研表单容器（替代 antd/element-plus Form）
 * 仅做布局容器 + labelWidth 下发（provide），不做校验（设计器场景无校验需求）
 */
import { provide, computed } from 'vue'

const props = withDefaults(defineProps<{
  labelWidth?: string
}>(), {
  labelWidth: '100px'
})

provide('fdFormLabelWidth', computed(() => props.labelWidth))
</script>

<style scoped>
.fd-form {
  width: 100%;
}
</style>
