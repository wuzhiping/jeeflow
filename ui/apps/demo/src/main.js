import { createApp } from 'vue'
import App from './App.vue'
import { createJeeflowUi, JeeflowUiKey } from '@mldong/jeeflow-ui'
import ApplyForm from './forms/apply-form.vue'
import ExpenseForm from './forms/expense-form.vue'

// 演示用户（与四后端同一套 8 个具名用户）：启动时从后端 /api/users 拉取，本地缓存复用
export const DEMO_USERS = []

function currentBaseUrl() {
  return localStorage.getItem('jeeflow_backend')
    || import.meta.env.VITE_BACKEND_PYTHON
    || '/jeeflow'
}

let usersPromise = null
export function fetchUsers() {
  if (usersPromise) return usersPromise
  usersPromise = fetch(`${currentBaseUrl()}/api/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
    .then((r) => r.json())
    .then((res) => {
      const list = Array.isArray(res?.data) ? res.data : []
      DEMO_USERS.splice(0, DEMO_USERS.length, ...list)
      return DEMO_USERS
    })
    .catch((e) => {
      console.error('fetch /api/users failed:', e)
      return DEMO_USERS
    })
  return usersPromise
}
fetchUsers()

const DEMO_ROLES = []

let rolesPromise = null
function fetchRoles() {
  if (rolesPromise) return rolesPromise
  rolesPromise = fetch(`${currentBaseUrl()}/api/roles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
    .then((r) => r.json())
    .then((res) => {
      const list = Array.isArray(res?.data) ? res.data : []
      DEMO_ROLES.splice(0, DEMO_ROLES.length, ...list)
      return DEMO_ROLES
    })
    .catch((e) => {
      console.error('fetch /api/roles failed:', e)
      return DEMO_ROLES
    })
  return rolesPromise
}
fetchRoles()

const DEMO_DICTS = {}

let dictsPromise = null
function fetchDict(code) {
  if (DEMO_DICTS[code]) return Promise.resolve(DEMO_DICTS[code])
  if (!dictsPromise) {
    dictsPromise = fetch(`${currentBaseUrl()}/api/dicts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
      .then((r) => r.json())
      .then((res) => {
        const list = Array.isArray(res?.data) ? res.data : []
        for (const row of list) {
          if (row?.code) DEMO_DICTS[row.code] = Array.isArray(row.items) ? row.items : []
        }
        return DEMO_DICTS
      })
      .catch((e) => {
        console.error('fetch /api/dicts failed:', e)
        return DEMO_DICTS
      })
  }
  return dictsPromise.then(() => DEMO_DICTS[code] || [])
}

function filterByKw(list, keyword, keys) {
  const kw = (keyword || '').trim().toLowerCase()
  if (!kw) return list
  return list.filter((row) => keys.some((k) => String(row[k] || '').toLowerCase().includes(kw)))
}

// 创建流程中心上下文（非组件形式注入：注册表在注入前可用，iframe 壳同款用法）
const jeeflowUi = createJeeflowUi({
  // 懒求值：切换后端只改 localStorage，api 每次请求取最新（SPA 热切换，无需 reload）
  // 开发环境走 vite proxy（相对路径）；生产环境走 nginx proxy
  baseUrl: () => localStorage.getItem('jeeflow_backend') || '/jeeflow' || import.meta.env.VITE_BACKEND_PYTHON || '/python-api',
  getOperator: () => localStorage.getItem('jeeflow_user') || 'user1',
  getToken: () => null,
  hasPermission: () => true, // demo 无权限体系：全放行（宿主接入时按 wf:{action} 权限码判断）
  adapters: {
    listUsers: async (keyword) => filterByKw(await fetchUsers(), keyword, ['userId', 'realName']),
    getUsersByIds: async (ids) => (await fetchUsers()).filter((u) => ids.includes(u.userId)),
    listRoles: async (keyword) => filterByKw(await fetchRoles(), keyword, ['roleId', 'roleName']),
    getDict: async (code) => fetchDict(code),
    // demo 无真实存储：返回可识别的占位 path（宿主应上传后回真实 url）
    upload: async (file) => `demo://${file.name}`,
  },
})

// 业务表单注册（宿主样板：formKey → 组件）
jeeflowUi.registerForm('apply-form', ApplyForm)
jeeflowUi.registerForm('expense-form', ExpenseForm)

createApp(App)
  .provide(JeeflowUiKey, jeeflowUi)
  .mount('#app')
