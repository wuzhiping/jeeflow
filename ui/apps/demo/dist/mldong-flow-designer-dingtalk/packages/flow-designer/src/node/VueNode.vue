<template>
  <div>
    <button @click="handleClick">点我</button>
  </div>
</template>
<script setup lang="ts">
import type { PropType } from 'vue'
import { BaseNodeModel } from '@logicflow/core'
const props = defineProps({
  model: {
    type: Object as PropType<BaseNodeModel>,
    required: true
  },
  isHovered: {
    type: Boolean,
    default: false
  },
  isSelected: {
    type: Boolean,
    default: false
  }
})
const handleClick = (e: any) => {
  const { eventCenter } = props.model.graphModel
  eventCenter.emit('node-vue:click', {
    e,
    data: props.model.data
  })
}
</script>
<style lang="less" scoped>

</style>