<template>
  <div class="fd-tooltip" ref="triggerRef" @mouseenter="show" @mouseleave="hide" @focusin="show" @focusout="hide">
    <slot />
    <Teleport to="body">
      <transition name="fd-tooltip-fade">
        <div
          v-if="visible"
          class="fd-tooltip__popup"
          :style="popupStyle"
          ref="popupRef"
        >
          <div class="fd-tooltip__inner">
            <slot name="content">{{ title }}</slot>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
/**
 * FDTooltip —— 自研文字提示（由 DingTooltip 提升为通用组件）
 * 内容支持 title prop 或 #content 插槽（抽屉表单 helpMessage 用插槽渲染多行）
 */
import { ref, computed, nextTick } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  offset?: number
}>(), {
  title: '',
  placement: 'top',
  offset: 8
})

const visible = ref(false)
const triggerRef = ref<HTMLElement | null>(null)
const popupRef = ref<HTMLElement | null>(null)
const popupPos = ref({ x: 0, y: 0 })

function show(_e: MouseEvent | FocusEvent) {
  visible.value = true
  nextTick(() => {
    if (!popupRef.value || !triggerRef.value) return
    // 用根元素 ref 定位触发器：e.currentTarget 在事件分发结束后会被置 null，不能在 nextTick 里读
    const rect = triggerRef.value.getBoundingClientRect()
    const popup = popupRef.value.getBoundingClientRect()
    const vw = window.innerWidth
    const vh = window.innerHeight

    let x: number, y: number

    switch (props.placement) {
      case 'top':
        x = rect.left + rect.width / 2 - popup.width / 2
        y = rect.top - popup.height - props.offset
        break
      case 'bottom':
        x = rect.left + rect.width / 2 - popup.width / 2
        y = rect.bottom + props.offset
        break
      case 'left':
        x = rect.left - popup.width - props.offset
        y = rect.top + rect.height / 2 - popup.height / 2
        break
      case 'right':
        x = rect.right + props.offset
        y = rect.top + rect.height / 2 - popup.height / 2
        break
    }

    // clamp to viewport
    x = Math.max(4, Math.min(x, vw - popup.width - 4))
    y = Math.max(4, Math.min(y, vh - popup.height - 4))

    popupPos.value = { x, y }
  })
}

function hide() {
  visible.value = false
}

const popupStyle = computed(() => ({
  left: `${popupPos.value.x}px`,
  top: `${popupPos.value.y}px`
}))
</script>

<style scoped>
.fd-tooltip {
  display: inline-block;
  max-width: 100%;
}

.fd-tooltip__popup {
  position: fixed;
  z-index: 9999;
  max-width: 280px;
  pointer-events: none;
}

.fd-tooltip__inner {
  padding: 6px 12px;
  font-size: 13px;
  line-height: 1.5;
  color: #fff;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 6px;
  word-break: break-all;
  white-space: normal;
}

/* fade transition */
.fd-tooltip-fade-enter-active,
.fd-tooltip-fade-leave-active {
  transition: opacity 0.15s ease;
}
.fd-tooltip-fade-enter-from,
.fd-tooltip-fade-leave-to {
  opacity: 0;
}
</style>
