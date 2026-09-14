<template>
  <div class="fd-select" :class="{ 'fd-select--open': open, 'fd-select--disabled': disabled }" ref="triggerRef">
    <div class="fd-select__trigger" @click="toggle">
      <span v-if="selectedLabel !== null && selectedLabel !== undefined && selectedLabel !== ''" class="fd-select__value">{{ selectedLabel }}</span>
      <span v-else class="fd-select__placeholder">{{ placeholder }}</span>
      <span class="fd-select__arrow" :class="{ 'fd-select__arrow--up': open }">
        <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2.5 4.5L6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </span>
    </div>
    <Teleport to="body">
      <transition name="fd-select-drop">
        <div v-if="open" class="fd-select__dropdown" :style="dropdownStyle">
          <div class="fd-select__empty" v-if="!options?.length">暂无选项</div>
          <div
            v-for="opt in options"
            :key="String(opt.value)"
            class="fd-select__option"
            :class="{ 'fd-select__option--active': opt.value === modelValue }"
            @click="handleSelect(opt)"
          >{{ opt.label }}</div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
/**
 * FDSelect —— 自研下拉选择（替代 antd/element-plus Select + Option）
 * 选项经 options prop 传入：[{ label, value }]
 * 弹层 Teleport 到 body 并用 fixed 定位，避免被抽屉/弹窗的 overflow 裁剪
 */
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'

interface FDSelectOption {
  label: string
  value: any
}

const props = withDefaults(defineProps<{
  modelValue?: any
  options?: FDSelectOption[]
  placeholder?: string
  disabled?: boolean
}>(), {
  options: () => [],
  placeholder: '请选择',
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: any): void
  (e: 'change', v: any): void
}>()

const open = ref(false)
const triggerRef = ref<HTMLElement | null>(null)
const dropdownPos = ref({ x: 0, y: 0, w: 0 })

const selectedLabel = computed(() => {
  const matched = props.options.find(o => o.value === props.modelValue)
  return matched?.label
})

const dropdownStyle = computed(() => ({
  left: `${dropdownPos.value.x}px`,
  top: `${dropdownPos.value.y}px`,
  minWidth: `${dropdownPos.value.w}px`
}))

function updatePos() {
  if (!triggerRef.value) return
  const rect = triggerRef.value.getBoundingClientRect()
  dropdownPos.value = { x: rect.left, y: rect.bottom + 4, w: rect.width }
}

function toggle() {
  if (props.disabled) return
  if (open.value) {
    open.value = false
  } else {
    updatePos()
    open.value = true
    nextTick(() => {
      document.addEventListener('mousedown', handleOutsideClick)
    })
  }
}

function handleSelect(opt: FDSelectOption) {
  emit('update:modelValue', opt.value)
  emit('change', opt.value)
  open.value = false
  document.removeEventListener('mousedown', handleOutsideClick)
}

function handleOutsideClick(e: MouseEvent) {
  const target = e.target as Node
  if (triggerRef.value && triggerRef.value.contains(target)) return
  open.value = false
  document.removeEventListener('mousedown', handleOutsideClick)
}

onMounted(() => {
  window.addEventListener('resize', updatePos)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleOutsideClick)
  window.removeEventListener('resize', updatePos)
})
</script>

<style scoped>
.fd-select {
  position: relative;
  width: 100%;
}

.fd-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 32px;
  padding: 4px 11px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  font-size: 14px;
  cursor: pointer;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.fd-select--open .fd-select__trigger {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.fd-select--disabled .fd-select__trigger {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.fd-select__value {
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fd-select__placeholder {
  color: #bfbfbf;
}

.fd-select__arrow {
  display: inline-flex;
  color: #999;
  transition: transform 0.2s;
  flex-shrink: 0;
  margin-left: 4px;
}

.fd-select__arrow--up {
  transform: rotate(180deg);
}

.fd-select__dropdown {
  position: fixed;
  z-index: 9999;
  max-height: 240px;
  overflow-y: auto;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  padding: 4px;
  box-sizing: border-box;
}

.fd-select__option {
  padding: 6px 10px;
  font-size: 14px;
  color: #333;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.fd-select__option:hover {
  background: #f5f5f5;
}

.fd-select__option--active {
  background: #e6f4ff;
  color: #1677ff;
}

.fd-select__empty {
  padding: 8px 10px;
  font-size: 13px;
  color: #999;
}

.fd-select-drop-enter-active,
.fd-select-drop-leave-active {
  transition: opacity 0.15s ease;
}
.fd-select-drop-enter-from,
.fd-select-drop-leave-to {
  opacity: 0;
}
</style>
