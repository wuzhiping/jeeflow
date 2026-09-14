<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fd-drawer-root"
      :class="{ 'fd-drawer-root--open': opening }"
      @click.self="handleMaskClick"
    >
      <div class="fd-drawer" :class="{ 'fd-drawer--open': opening }" :style="{ width: width }" ref="drawerRef">
        <div class="fd-drawer__header">
          <span class="fd-drawer__title">{{ title }}</span>
          <button class="fd-drawer__close" @click="internalClose">&times;</button>
        </div>
        <div class="fd-drawer__body">
          <slot />
        </div>
        <div v-if="$slots.footer || showFooter" class="fd-drawer__footer">
          <slot name="footer">
            <button class="fd-btn fd-btn--default" @click="internalClose">{{ cancelText }}</button>
            <button class="fd-btn fd-btn--primary" @click="handleOk" :disabled="okDisabled">{{ okText }}</button>
          </slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * FDDrawer —— 自研抽屉（由 DingDrawer 提升为通用组件，canvas/dingtalk 双模式共用）
 * 相比 DingDrawer 的增强：visible 支持双向驱动（父组件置 false 时静默关闭，不重复 emit cancel）
 */
import { watch, ref, onMounted, onBeforeUnmount } from 'vue'

const props = withDefaults(defineProps<{
  visible: boolean
  title?: string
  width?: string
  cancelText?: string
  okText?: string
  okDisabled?: boolean
  showFooter?: boolean
  maskClosable?: boolean
  keyboard?: boolean
}>(), {
  title: '',
  width: '420px',
  cancelText: '取消',
  okText: '确定',
  okDisabled: false,
  showFooter: true,
  maskClosable: true,
  keyboard: true
})

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'ok'): void
  (e: 'cancel'): void
  (e: 'close'): void
}>()

const show = ref(false)       // 控制 v-if 挂载/卸载
const opening = ref(false)    // 控制滑入/滑出动画 class
const closing = ref(false)    // 关闭动画进行中，防止重复触发
let closeTimer: ReturnType<typeof setTimeout> | null = null
const drawerRef = ref<HTMLElement | null>(null)
void drawerRef

function open() {
  closing.value = false
  if (closeTimer) {
    clearTimeout(closeTimer)
    closeTimer = null
  }
  if (show.value) {
    opening.value = true
    return
  }
  show.value = true
  document.body.style.overflow = 'hidden'
  // 下一帧加 open class 触发滑入过渡
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      opening.value = true
    })
  })
}

/**
 * 静默关闭（父组件驱动 visible=false 时走这里，不 emit cancel）
 */
function silentClose() {
  if (!show.value || closing.value) return
  closing.value = true
  opening.value = false
  closeTimer = setTimeout(() => {
    closeTimer = null
    show.value = false
    closing.value = false
    document.body.style.overflow = ''
    emit('close')
  }, 260)
}

/**
 * 内部关闭（X 按钮 / 遮罩 / Esc 触发），动画结束后通知父组件
 */
function internalClose() {
  silentClose()
  emit('update:visible', false)
  emit('cancel')
}

function handleOk() {
  emit('ok')
}

function handleMaskClick() {
  if (props.maskClosable) {
    internalClose()
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (!show.value || !props.keyboard) return
  if (e.key === 'Escape') {
    internalClose()
  }
}

// 监听 visible prop 变化（双向驱动）
watch(() => props.visible, (v) => {
  if (v) {
    open()
  } else {
    silentClose()
  }
}, { immediate: true })

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  if (closeTimer) clearTimeout(closeTimer)
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.fd-drawer-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0);
  transition: background 0.25s ease;
  pointer-events: none;
}

.fd-drawer-root--open {
  background: rgba(0, 0, 0, 0.3);
  pointer-events: auto;
}

.fd-drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  /* 窄视口下不溢出（钉钉模式移动端预览 375px 场景） */
  max-width: 100%;
  background: #fff;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fd-drawer--open {
  transform: translateX(0);
}

.fd-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.fd-drawer__title {
  font-size: 16px;
  font-weight: 600;
  color: #1f1f1f;
}

.fd-drawer__close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  color: #999;
  border-radius: 4px;
  padding: 0;
}

.fd-drawer__close:hover {
  background: #f5f5f5;
  color: #333;
}

.fd-drawer__body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.fd-drawer__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 24px;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.fd-btn {
  height: 32px;
  padding: 0 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.fd-btn--default {
  background: #fff;
  border-color: #d9d9d9;
  color: #333;
}

.fd-btn--default:hover {
  color: #1677ff;
  border-color: #1677ff;
}

.fd-btn--primary {
  background: #1677ff;
  color: #fff;
}

.fd-btn--primary:hover {
  background: #4096ff;
}

.fd-btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
