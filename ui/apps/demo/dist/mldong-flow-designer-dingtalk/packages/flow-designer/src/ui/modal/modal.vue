<template>
  <FDModal v-model:visible="visible" :title="mTitle" width="640px">
    <div style="max-height: 600px; overflow-y: auto;">
      <FDTextarea
        v-if="['import', 'highlight'].includes(type)"
        style="height: 600px; font-family: monospace;"
        v-model="graphData"
      ></FDTextarea>
      <FDJsonViewer v-else :showLineNumber="true" :data="graphData" />
    </div>
    <template #footer>
      <div v-if="['import', 'highlight'].includes(type)">
        <FDButton @click="visible=false">取消</FDButton>
        <FDButton type="primary" @click="handleSumit">确定</FDButton>
      </div>
      <FDButton v-else type="primary" @click="handleCopy">复制</FDButton>
    </template>
  </FDModal>
</template>
<script setup lang="ts">
import { ref, PropType, watch } from 'vue';
import { FDModal, FDTextarea, FDButton, FDJsonViewer, FDMessage } from '../fd';
const visible = ref(false)
const props = defineProps({
  title: { // 标题
    type: String as PropType<string>
  }
})
const graphData = ref()
const mTitle = ref(props.title)
const type = ref('see')
const lf = ref()
watch(()=>props.title,()=>{
  mTitle.value = props.title
})
const handleCopy = async () => {
  try {
    const text = JSON.stringify(graphData.value, null, 2)
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      // 使用兼容方案
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    FDMessage.success('复制成功')
  } catch (err) {
    FDMessage.error(`复制失败: ${err instanceof Error ? err.message : String(err)}`)
  }
}
const handleSumit = () =>{
  // 处理导入
  try {
    const jsonObj = JSON.parse(graphData.value || '{}')
    const { eventCenter } = lf.value.graphModel;
    // 触发自定义的update:graphData
    if(type.value == 'import') {
      eventCenter.emit("update:graphData", jsonObj);
      FDMessage.success('导入成功')
    } else if(type.value == 'highlight') {
      eventCenter.emit("update:highlight", jsonObj);
      FDMessage.success('设置高亮成功')
    }
    visible.value = false
  } catch(err) {
    FDMessage.error('数据格式错误')
    return
  }
  
}
defineExpose({
  show(e: any) {
    type.value = e.type
    lf.value = e.lf
    if(e.type == 'import') {
      mTitle.value = "导入流程数据"
    } else if (e.type == 'highlight') {
      mTitle.value = "设置高亮数据"
    } else {
      mTitle.value = "查看流程数据"
    }
    graphData.value = e.graphData
    visible.value = true
  },
})
</script>
<style lang="less" scoped>

</style>
