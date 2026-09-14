<template>
  <div class="flow-container">
    <DingTalkDesigner
      ref="dingtalkDesignerRef"
      :value="value"
      :theme="theme"
      :high-light="highLight"
      :viewer="viewer"
      :dnd-panel="dndPanel"
      :process-form="processForm"
      :edge-form="edgeForm"
      :node-click="nodeClick"
      :edge-click="edgeClick"
      :blank-contextmenu="blankContextmenu"
      :control="control"
      :init-control="initControl"
      :drawer-width="drawerWidth"
      :modal-width="modalWidth"
      :type-prefix="typePrefix"
      :default-edge-type="defaultEdgeType"
      @update:value="(data) => emits('update:value', data)"
      @save="(data) => emits('on-save', data)"
      @on-init="(api) => emits('on-init', api)"
      @on-render="(api) => emits('on-render', api)"
      @node-click="(params) => emits('node-click', params)"
      @edge-click="(params) => emits('edge-click', params)"
    />
  </div>
</template>
<script lang="ts" setup>
/**
 * 钉钉精简版包装组件（mldong-flow-designer-dingtalk 专用入口）
 *
 * 与双模式包 index.vue 的 dingtalk 分支契约完全一致（props/events/expose 同名），
 * 但不引入 @logicflow/core，供精简包构建使用。
 * mode / initDndPanel / dagreOptions 等画布专属 prop 仍声明接收（保持
 * 双模式包切换时的 drop-in 兼容），仅不参与渲染。
 */
import { ref } from 'vue';
import { MldongFlowDesignerProps } from './types/props'
import DingTalkDesigner from './dingtalk/components/DingTalkDesigner.vue';

defineProps(MldongFlowDesignerProps)
const emits = defineEmits(['update:value', 'on-init', 'on-render', 'on-save', 'node-click', 'edge-click'])

const dingtalkDesignerRef = ref()

defineExpose({
  /**
   * 兼容双模式包的同名方法：返回 FDDesignerAPI
   * （其命名与画布模式 lf 实例对齐，业务方可按同一套代码消费）
   */
  getLfInstance() {
    return (dingtalkDesignerRef.value as any)
  },
  getDesignerApi() {
    return (dingtalkDesignerRef.value as any)
  }
})
</script>
<style scoped>
.flow-container {
  width: 100%;
  height: 100%;
}
</style>
