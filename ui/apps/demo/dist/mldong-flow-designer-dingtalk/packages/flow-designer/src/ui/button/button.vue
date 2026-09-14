<template>
  <FDButton :type="type" :size="size" :circle="circle">
    <slot></slot>
  </FDButton>
</template>

<script setup lang="ts">
/**
 * 兼容包装层 —— 4.0.0 起底层为自研 FDButton，不再适配 antd/element-plus
 * 保留本文件仅为既有 import（'../button'）不破坏
 */
import { PropType } from 'vue';
import { FDButton } from '../fd';
defineProps({
  type: { // 按钮类型
    type: String as PropType<any>
  },
  size: { // 按钮大小：large | middle | small
    type: String as PropType<'large'| 'middle'| 'small'>
  },
  circle: { // 是否为圆角按钮
    type: Boolean as PropType<boolean>
  }
})
</script>
