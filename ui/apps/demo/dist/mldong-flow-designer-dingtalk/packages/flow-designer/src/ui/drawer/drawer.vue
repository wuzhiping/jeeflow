<template>
  <FDDrawer :visible="visible" :title="mTitle" :width="widthStr" :show-footer="false" @cancel="visible=false">
    <FDSchemaForm
      :form-items="form.formItems"
      :model="formState"
      :label-width="form.labelWidth || '120px'"
      :render-context="currentData"
    >
      <!-- 业务方 slot 透传（item.slot 场景） -->
      <template v-for="(_, name) in $slots" :key="name" #[name]="scope">
        <slot :name="name" v-bind="scope" />
      </template>
    </FDSchemaForm>
  </FDDrawer>
</template>
<script setup lang="ts">
import { computed, PropType, reactive, ref, watch } from 'vue';
import { FDDrawer, FDSchemaForm } from '../fd';
import { FDFormType } from '../../types';

const visible = ref(false)
const props = defineProps({
  title: { // 标题
    type: String as PropType<string>
  },
  width: { // 抽屉宽度
    type: [String,Number] as PropType<string | number>,
    default: '600px'
  }
})
const mTitle = ref(props.title)
const formState = reactive<any>({})
watch(()=>props.title,()=>{
  mTitle.value = props.title
})
// FDDrawer width 只接受字符串，数字宽度补 px
const widthStr = computed(() => {
  return typeof props.width === 'number' ? `${props.width}px` : props.width
})
const form = ref<FDFormType>({} as any)
const currentData = ref()
let watchMap: any = {}
defineExpose({
  show(e: any){
    currentData.value = e;
    Object.keys(formState).forEach(key=>{
      formState[key] = undefined
    })
    
    form.value = e.patternItem?.form || {}
    const lf = currentData.value.lf
    const typePrefix = lf.graphModel.props.typePrefix || ''
    // 监听唯一编码变化=>修改节点id
    form.value?.formItems?.forEach(item=>{
      let stopWatch = watchMap[item.name]
      if(stopWatch) {
        stopWatch()
      }
      stopWatch = watch(()=>formState[item.name],(n, o)=>{
        if(e.data.type == 'process') {
          lf.graphModel[item.name] = n
          const { eventCenter } = lf.graphModel;
          // 触发自定义的update:graphModel
          eventCenter.emit("update:graphModel", lf.graphModel);
        } else if(e.data.type == `${typePrefix}transition`) {
          if(item.name == 'name') {
          // 如果为唯一编码，则修改节点id
            lf.changeEdgeId(o, n);
          } else if(item.name == 'displayName') {
            // 如果为显示名称，则修改节点显示名称
            lf.updateText(formState.name, n);
          } else {
            // 务属性变化=>修改节点属性
            lf.setProperties(formState.name, {
              [item.name]: n,
            });
          }
        } else {
          if(item.name == 'name') {
          // 如果为唯一编码，则修改节点id
            const lf = currentData.value.lf
            lf.changeNodeId(o, n);
          } else if(item.name == 'displayName') {
            // 如果为显示名称，则修改节点显示名称
            const lf = currentData.value.lf
            lf.updateText(formState.name, n);
          } else {
            // 务属性变化=>修改节点属性
            const lf = currentData.value.lf
            lf.setProperties(formState.name, {
              [item.name]: n,
            });
          }
        }
      }, {
        deep: true
      })
      watchMap[item.name] = stopWatch
      // 先根据默认值赋值
      if(item.defaultValue!==undefined) {
        formState[item.name] = item.defaultValue
      }
    })
    
    if(e.data.type == 'process') {
      mTitle.value = '设置流程属性'
      Object.keys(e.data.properties || {}).forEach(key=>{
        formState[key] = e.data.properties[key]
      })
    } else if(e.data.type == `${typePrefix}transition`) {
      mTitle.value = '设置边属性'
      // 赋值唯一编码
      formState.name = e.data.id
      // 赋值显示名称
      formState.displayName = e.data.text?.value
      // 赋值业务属性
      Object.keys(e.data.properties || {}).forEach(key=>{
        formState[key] = e.data.properties[key]
      })
    } else {
      if(e.patternItem?.drawerTitle) {
        mTitle.value = e.patternItem?.drawerTitle
      } else {
        if(e.patternItem?.text) {
          mTitle.value = `设置【${e.patternItem?.text.replace('节点','')}】节点属性`
        } else {
          mTitle.value = '设置属性'
        }
      }
      // 赋值唯一编码
      formState.name = e.data.id
      // 赋值显示名称
      formState.displayName = e.data.text?.value
      // 赋值业务属性
      Object.keys(e.data.properties || {}).forEach(key=>{
        formState[key] = e.data.properties[key]
      })
    }
    visible.value = true
  }
})
</script>
<style lang="less" scoped>

</style>