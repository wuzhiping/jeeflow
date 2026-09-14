<template>
  <Teleport to="body">
    <transition name="fd-modal-fade">
      <div v-if="visible" class="fd-modal-root" @click.self="handleOverlayClick">
        <transition name="fd-modal-zoom">
          <div
            v-if="visible"
            class="fd-modal"
            :style="{ width: width }"
            ref="modalRef"
          >
            <!-- header -->
            <div class="fd-modal__header">
              <span class="fd-modal__title">{{ title }}</span>
              <button class="fd-modal__close" @click="handleCancel">&times;</button>
            </div>

            <!-- body -->
            <div class="fd-modal__body">
              <slot />
            </div>

            <!-- footer -->
            <div v-if="$slots.footer || showFooter" class="fd-modal__footer">
              <slot name="footer">
                <button class="fd-btn fd-btn--default" @click="handleCancel">{{ cancelText }}</button>
                <button class="fd-btn fd-btn--primary" @click="handleOk" :disabled="okDisabled">{{ okText }}</button>
              </slot>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * FDModal —— 自研弹窗（由 DingModal 提升为通用组件，canvas/dingtalk 双模式共用）
 */
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

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
  width: '520px',
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

// 模板 ref 绑定（弹窗 DOM 根节点），仅挂载用；显式引用避免 vue-tsc 3.x TS6133 误报
const modalRef = ref<HTMLElement | null>(null)
void modalRef

function handleOk() {
  emit('ok')
}

function handleCancel() {
  emit('update:visible', false)
  emit('cancel')
}

function handleOverlayClick() {
  if (props.maskClosable) {
    handleCancel()
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (!props.visible || !props.keyboard) return
  if (e.key === 'Escape') {
    handleCancel()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 弹窗打开时禁止 body 滚动
watch(() => props.visible, (v) => {
  document.body.style.overflow = v ? 'hidden' : ''
})
</script>

<style scoped>
/* ── overlay ── */
.fd-modal-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
}

/* ── modal box ── */
.fd-modal {
  position: relative;
  max-height: calc(100vh - 80px);
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 6px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── header ── */
.fd-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.fd-modal__title {
  font-size: 16px;
  font-weight: 600;
  color: #1f1f1f;
}

.fd-modal__close {
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

.fd-modal__close:hover {
  background: #f5f5f5;
  color: #333;
}

/* ── body ── */
.fd-modal__body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* ── footer ── */
.fd-modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 24px 16px;
  border-top: 1px solid #f0f0f0;
}

/* ── buttons ── */
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

.fd-btn--primary:disabled:hover {
  background: #1677ff;
}

/* ── transitions ── */
.fd-modal-fade-enter-active,
.fd-modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.fd-modal-fade-enter-from,
.fd-modal-fade-leave-to {
  opacity: 0;
}

.fd-modal-zoom-enter-active,
.fd-modal-zoom-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.fd-modal-zoom-enter-from {
  transform: scale(0.95);
  opacity: 0;
}
.fd-modal-zoom-leave-to {
  transform: scale(0.95);
  opacity: 0;
}
</style>
