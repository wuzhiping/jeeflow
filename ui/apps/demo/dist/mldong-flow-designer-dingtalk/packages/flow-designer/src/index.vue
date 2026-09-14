<template>
  <div :class="['flow-container', { fullscreen: isFullscreen }]">
    <DingTalkDesigner
      v-if="currentMode === 'dingtalk'"
      ref="dingtalkDesignerRef"
      :key="'dingtalk'"
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
    <div
      v-else
      :key="'canvas'"
      style="display: flex; flex-direction: column; width: 100%; height: 100%"
    >
      <MDrawer ref="drawerRef" title="我是抽屉" :width="drawerWidth"></MDrawer>
      <MModal ref="modalRef" title="我是弹窗" :width="modalWidth"></MModal>
      <div ref="container" style="flex: 1; min-height: 0"></div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { onMounted, ref, computed, watch, nextTick } from 'vue';

const container = ref<HTMLElement>()
import LogicFlow from "@logicflow/core";
import "@logicflow/core/lib/style/index.css";
import '@logicflow/extension/lib/style/index.css'
import Flow from './plugins/Flow';
import './plugins/flow.css'
import type {  FDHighLightType } from './types';
import { MldongFlowDesignerProps } from './types/props'
import { NodeStateEnum } from './types/enums';
import MDrawer from './ui/drawer';
import MModal from './ui/modal';
import DingTalkDesigner from './dingtalk/components/DingTalkDesigner.vue';
// 添加全屏状态
const isFullscreen = ref(false);
const drawerRef = ref()
const modalRef = ref()
const props = defineProps(MldongFlowDesignerProps)

// 计算当前渲染模式
const currentMode = computed(() => {
  // prop 优先
  if (props.mode) return props.mode
  // 其次读数据中的 mode
  if (props.value?.mode) return props.value.mode
  // 默认 canvas
  return 'canvas'
})
/**
 * 更新全屏控制按钮的文本和图标
 */
const updateFullscreenControl = () => {
  // 通过更具体的选择器定位全屏按钮
  const fullscreenControlItem = document.querySelector('.lf-control-item .lf-control-fullscreen');
  if (fullscreenControlItem) {
    const parentItem = fullscreenControlItem.closest('.lf-control-item');
    if (parentItem) {
      // 只修改全屏按钮的文本
      const textElement = parentItem.querySelector('.lf-control-text');
      if (textElement) {
        textElement.textContent = isFullscreen.value ? '退出全屏' : '全屏';
      }
      
      // 更新图标类名
      fullscreenControlItem.className = `lf-control-fullscreen ${isFullscreen.value ? 'exit' : 'enter'}`;
    }
  }
};
/**
 * 切换全屏状态
 */
 const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  if (isFullscreen.value) {
    enterFullscreen();
  } else {
    exitFullscreen();
  }
  updateFullscreenControl();
};
LogicFlow.use(Flow, {
  ...props,
  drawerRef,
  modalRef,
  toggleFullscreen,
});
const emits = defineEmits(['update:value', 'on-init', 'on-render', 'on-save', 'node-click', 'edge-click'])
const lfInstance = ref();


/**
 * 进入全屏
 */
const enterFullscreen = () => {
  if (container.value) {
    container.value.requestFullscreen?.().catch(err => {
      console.warn('无法进入全屏模式:', err);
    });
  }
};

/**
 * 退出全屏
 */
const exitFullscreen = () => {
  if (document.fullscreenElement) {
    document.exitFullscreen?.().catch(err => {
      console.warn('无法退出全屏模式:', err);
    });
  }
};

/**
 * 设置高亮数据
 * @param data 
 */
const setHighLight = (data: FDHighLightType) =>{
  if(!data) return;
  const lf = lfInstance.value;
  if(!lf) return;
  // 设置历史节点state属性为history
  if(Array.isArray(data.historyNodeNames) && data.historyNodeNames.length) {
    data.historyNodeNames.forEach(nodeId=>{
      lf.getNodeModelById(nodeId)?.setProperties({
        state: NodeStateEnum.history,
      });
    })
  }
  // 设置历史边state属性为history
  if(Array.isArray(data.historyEdgeNames) &&data.historyEdgeNames.length) {
    data.historyEdgeNames.forEach(edgeId=>{
      lf.getEdgeModelById(edgeId)?.setProperties({
      state: NodeStateEnum.history,
    });
    })
  }
  // 设置活跃节点state属性为active
  if(Array.isArray(data.activeNodeNames) && data.activeNodeNames.length) {
    data.activeNodeNames.forEach(nodeId=>{
      lf.getNodeModelById(nodeId)?.setProperties({
        state: NodeStateEnum.active,
      });
    })
  }
}
/**
 * 自定义渲染
 * 1.默认渲染
 * 2.设置高亮属性
 * @param data 
 */
const myRender = (data: any) =>{
  const lf = lfInstance.value;
  if(!lf) return;
  lf.render(data);
  // 设置亮亮数据
  setHighLight(props.highLight)
  // emits render事件
  emits('on-render', lf)
}
const isHistoryChange = ref(false)

/**
 * 销毁 LogicFlow 实例
 */
function destroyLogicFlow() {
  if (!lfInstance.value) return
  try {
    lfInstance.value.destroy?.()
  } catch (e) {
    console.warn('[FD] lf.destroy failed', e)
  }
  lfInstance.value = null
}

/**
 * 初始化 LogicFlow 实例（仅 canvas 模式调用，整个组件生命周期内只 init 一次）
 * 当初始 mode 为 dingtalk 时，onMounted 不 init；待用户切到 canvas 时由 watch 触发
 * 模式切换 canvas → dingtalk → canvas 时，需要 destroy 旧实例重新 init（新 container DOM）
 */
function initLogicFlow() {
  if (!container.value) return
  // 容器变化或实例不存在时，重新创建
  destroyLogicFlow()
  lfInstance.value = new LogicFlow({
    container: container.value,
    grid: true,
    isSilentMode: props.viewer,
    allowResize: true
  });
  const lf = lfInstance.value;
  // emits初始化事件
  emits('on-init', lf)
  const { eventCenter } = lf.graphModel;
  // ⭐ 转发画布模式节点点击为 emit（与 Flow.ts 内部 props.nodeClick 处理并存）
  // 构造与 Flow.ts 中 nodeClick(nodeEventParams) 完全一致的事件参数。
  eventCenter.on('node:click', (event: any) => {
    if (props.viewer === true) return
    const shapeList: any[] = (props as any).dndPanel || []
    const matchedItem = shapeList.find?.((it: any) => it.type === event?.data?.type?.replace?.(props.typePrefix, ''))
    emits('node-click', {
      ...event,
      patternItem: matchedItem,
      lf
    })
  })
  // ⭐ 转发画布模式边点击为 emit（与 Flow.ts 内部 props.edgeClick 处理并存）
  eventCenter.on('edge:click', (event: any) => {
    if (props.viewer === true) return
    emits('edge-click', {
      ...event,
      patternItem: { form: props.edgeForm },
      lf
    })
  })
  // 监听画布变化事件
  eventCenter.on('history:change', () =>{
    isHistoryChange.value = true
    emits('update:value', lf.getGraphData())
  })
  // 监听自定义的update:graphModel事件
  eventCenter.on('update:graphModel',() =>{
    isHistoryChange.value = true
    emits('update:value', lf.getGraphData())
  })
  // 监听自定义的update:graphData事件
  eventCenter.on('update:graphData',(data: any) =>{
    // emits('update:value', data)
    myRender(data)
  })
  // 监听自定义的update:highlight事件
  eventCenter.on('update:highlight',(data: any) =>{
    setHighLight(data)
  })
  // 监听自定义的save事件
  eventCenter.on('custom:save', (data: any) =>{
    emits('on-save', data)
  })
  myRender(props.value)
  // 监听键盘ESC事件退出全屏
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isFullscreen.value) {
      isFullscreen.value = false;
    }
  });
  // 监听全屏变化事件
  document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) {
      isFullscreen.value = false;
    }
  });
  updateFullscreenControl()
  // 暴露 lf 实例给 Playwright/测试/调试用
  //   浏览器 console: window.__lf
  //   Playwright evaluate: () => window.__lf
  if (typeof window !== 'undefined') {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(window as any).__lf = lf
  }
}

onMounted(() => {
  // 钉钉模式下不初始化 LogicFlow，由 watch(currentMode) 在切到 canvas 时补 init
  if (currentMode.value !== 'canvas') return;
  initLogicFlow()
})

/**
 * 监听模式切换：dingtalk → canvas 时补 init LogicFlow
 * 用 nextTick 等 canvas 模板挂载完成（container.value 可用）
 *
 * 关键点：模板 v-if 切换模式时会重建 canvas 分支的 DOM（container div 是新的），
 * 因此必须 destroy 旧的 LogicFlow 实例，再用新 container 重新 init。
 * 仅当 lfInstance.value 为空时才跳过（初次 onMounted 时 init 过的情况除外）
 */
watch(currentMode, async (newMode, oldMode) => {
  if (newMode === 'canvas') {
    await nextTick()
    initLogicFlow()
  } else if (oldMode === 'canvas' && newMode === 'dingtalk') {
    // canvas → dingtalk：清理 LogicFlow 实例释放资源
    destroyLogicFlow()
  }
})
watch(()=>props.value, (newVal)=>{
  if(!isHistoryChange.value) {
    myRender(newVal);
  }
  isHistoryChange.value = false
}, {
  deep: true
})
watch(()=>props.highLight, (newVal)=>{
  setHighLight(newVal)
}, {
  deep: true
})

// ─── 钉钉模式 API 暴露（与画布模式 getLfInstance 同名风格）───────────
const dingtalkDesignerRef = ref()

/**
 * 获取钉钉模式的"lf 等价 API"实例
 * 业务方用法：
 *   const ref = ... // 父组件 ref
 *   const api = ref.getDesignerApi()
 *   api.updateText('apply', '新名称')
 */
defineExpose({
  getLfInstance() {
    // 兼容画布模式
    return lfInstance.value
  },
  getDesignerApi() {
    // 钉钉模式专用
    return (dingtalkDesignerRef.value as any)?.getDesignerApi?.()
      ?? (dingtalkDesignerRef.value as any)
  }
})
</script>
<style scoped>
.flow-container {
  width: 100%;
  height: 100%;
}

.flow-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
}

.fullscreen-control {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
}

.fullscreen-btn {
  padding: 8px 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.fullscreen-btn:hover {
  background-color: #40a9ff;
}
</style>