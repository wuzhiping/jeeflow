import { ref } from 'vue'

// FIX-UI-3 (2026-09-18)：DEMO_USERS 改用 Vue ref，让 App.vue 的 v-for 和 computed 响应式追踪
// 拆到独立模块避免与 App.vue 循环 import 导致 TDZ
export const DEMO_USERS = ref([])
