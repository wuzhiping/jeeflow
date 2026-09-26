<!--
  SystemInfoCard.vue — 工作台「系统环境」卡片

  目的：
    - 客户反馈问题时，可一键复制版本元数据（version / git_sha / build_time）
    - 与客户系统实际部署对齐（v1.11.8+b4d7308 是否一致？）
    - 运维快速确认后端状态（status + pg）

  数据源：
    - GET {baseUrl}/healthz → {status, backend, version, version_full, git_sha, build_time, pg}
    - GET {baseUrl}/version  → {version, version_full, git_sha, build_time}
    （baseUrl 同 main.js 的 currentBaseUrl() 逻辑：localStorage > .env > '/jeeflow'）

  刷新策略：每 30s 自动刷新 + 手动刷新按钮
  默认折叠（仅显示摘要），点击展开全部字段

  设计原则：
    - 不引入新依赖
    - 沿用现有 jf-* CSS class 名风格
    - 与 workbench 卡片风格保持一致
-->
<template>
  <div class="sys-info-card" :class="{ 'is-expanded': expanded, 'is-down': isDown }">
    <!-- 折叠态：标题行（status 灯 + 摘要 + caret） -->
    <div class="sys-info-card__header" @click="toggle">
      <span class="sys-info-card__dot" :class="dotClass" :title="statusTitle"></span>
      <span class="sys-info-card__title">系统环境</span>
      <span v-if="healthz" class="sys-info-card__summary">
        v{{ healthz.version }}
        <span class="sys-info-card__sep">·</span>
        <span :class="pgClass">{{ pgText }}</span>
        <span v-if="healthz.version_full !== healthz.version" class="sys-info-card__sep">·</span>
        <code v-if="healthz.version_full !== healthz.version" class="sys-info-card__sha">{{ shortSha }}</code>
      </span>
      <span v-else-if="err" class="sys-info-card__summary sys-info-card__summary--err">
        {{ err }}
      </span>
      <span v-else class="sys-info-card__summary">加载中...</span>
      <span class="sys-info-card__caret">{{ expanded ? '▴' : '▾' }}</span>
    </div>

    <!-- 展开态：字段表 + 操作 -->
    <div v-if="expanded" class="sys-info-card__body">
      <table class="sys-info-table">
        <tbody>
          <tr v-for="row in rows" :key="row.label">
            <th>{{ row.label }}</th>
            <td>
              <code v-if="row.mono">{{ row.value || '-' }}</code>
              <span v-else>{{ row.value || '-' }}</span>
              <span v-if="row.tag" class="sys-info-tag" :class="row.tagClass">{{ row.tag }}</span>
            </td>
          </tr>
          <tr>
            <th>前端时间</th>
            <td>
              {{ fetchedAt || '-' }}
              <span v-if="ageText" class="sys-info-muted">（{{ ageText }}）</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="sys-info-card__actions">
        <button class="sys-info-btn sys-info-btn--primary" :disabled="copied" @click="copy">
          {{ copied ? '已复制 ✓' : '复制全部' }}
        </button>
        <button class="sys-info-btn" @click="refresh" :disabled="loading">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <div class="sys-info-card__hint">
        💡 反馈时粘贴以上信息，方便对齐系统环境
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const REFRESH_INTERVAL = 30_000  // 30s

const expanded = ref(false)
const healthz = ref(null)
const err = ref('')
const loading = ref(false)
const fetchedAt = ref('')
const copied = ref(false)

let timer = null

// 与 main.js 的 currentBaseUrl() 完全一致：
//   localStorage('jeeflow_backend') > VITE_BACKEND_PYTHON > '/jeeflow'
function baseUrl() {
  return localStorage.getItem('jeeflow_backend')
    || import.meta.env.VITE_BACKEND_PYTHON
    || '/jeeflow'
}

const isDown = computed(() =>
  healthz.value && (healthz.value.status !== 'UP' || healthz.value.pg === 'down')
)

const dotClass = computed(() => {
  if (err.value) return 'dot--err'
  if (isDown.value) return 'dot--down'
  if (healthz.value) return 'dot--up'
  return 'dot--loading'
})

const statusTitle = computed(() => {
  if (err.value) return `无法连接：${err.value}`
  if (isDown.value) return `异常：${healthz.value?.pg === 'down' ? 'PG 连接池断开' : healthz.value?.status}`
  if (healthz.value) return `正常：${healthz.value.version}`
  return '加载中'
})

const pgText = computed(() => {
  const pg = healthz.value?.pg
  if (pg === 'ok') return 'PG OK'
  if (pg === 'down') return 'PG DOWN'
  return pg || '-'
})

const pgClass = computed(() =>
  healthz.value?.pg === 'ok' ? 'sys-info-ok' : 'sys-info-warn'
)

const shortSha = computed(() => {
  const sha = healthz.value?.git_sha
  return sha && sha !== 'unknown' ? sha.slice(0, 7) : ''
})

const ageText = computed(() => {
  if (!fetchedAt.value) return ''
  const ms = Date.now() - new Date(fetchedAt.value).getTime()
  if (ms < 60_000) return `${Math.round(ms / 1000)} 秒前`
  if (ms < 3_600_000) return `${Math.round(ms / 60_000)} 分钟前`
  return `${Math.round(ms / 3_600_000)} 小时前`
})

const rows = computed(() => {
  const h = healthz.value
  if (!h) return []
  return [
    { label: '状态',       value: h.status,                   mono: false, tag: h.status === 'UP' ? '正常' : '异常', tagClass: h.status === 'UP' ? 'tag--ok' : 'tag--err' },
    { label: '后端',       value: h.backend,                  mono: true },
    { label: '版本',       value: h.version,                  mono: true },
    { label: '完整版本',   value: h.version_full,             mono: true },
    { label: 'Git SHA',    value: h.git_sha,                  mono: true },
    { label: '构建时间',   value: h.build_time,               mono: true },
    { label: 'PG 连接池',  value: h.pg,                       mono: true, tag: h.pg === 'ok' ? 'OK' : 'DOWN', tagClass: h.pg === 'ok' ? 'tag--ok' : 'tag--err' },
  ]
})

async function refresh() {
  if (loading.value) return
  loading.value = true
  err.value = ''
  try {
    // /healthz 含 4 字段 + status + pg，一次拿全
    const r = await fetch(`${baseUrl()}/healthz`, { method: 'GET' })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    healthz.value = data
    fetchedAt.value = new Date().toISOString()
  } catch (e) {
    healthz.value = null
    err.value = (e && e.message) || '未知错误'
  } finally {
    loading.value = false
  }
}

function toggle() {
  expanded.value = !expanded.value
}

async function copy() {
  const h = healthz.value
  if (!h) return
  const lines = [
    '【系统环境】',
    `状态：${h.status}`,
    `后端：${h.backend}`,
    `版本：${h.version}`,
    `完整版本：${h.version_full}`,
    `Git SHA：${h.git_sha}`,
    `构建时间：${h.build_time}`,
    `PG 连接池：${h.pg}`,
    `前端时间：${fetchedAt.value}`,
  ]
  const text = lines.join('\n')
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // 退化：选中文本
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    try { document.execCommand('copy') } catch {}
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, REFRESH_INTERVAL)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.sys-info-card {
  background: #fff;
  border: 1px solid var(--jf-border, #e8eaed);
  border-radius: 10px;
  margin: 16px 20px;
  overflow: hidden;
  transition: border-color .15s;
  /* 修复：JfLayout__content 是 flex-direction:column 容器，
     默认 flex-shrink:1 会让卡片被压缩到 2px（只剩 border）。
     强制 shrink=0 + min-height:fit-content 保持完整高度。 */
  flex-shrink: 0;
  min-height: fit-content;
  align-self: stretch;
}
.sys-info-card.is-expanded { border-color: var(--jf-primary, #1677ff); }
.sys-info-card.is-down { border-color: #ef4444; }

.sys-info-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}
.sys-info-card__header:hover { background: var(--jf-hover, #f5f7fa); }

.sys-info-card__dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #d1d5db;
}
.dot--loading { background: #d1d5db; }
.dot--up      { background: #22c55e; box-shadow: 0 0 0 3px rgba(34, 197, 94, .15); }
.dot--down    { background: #ef4444; box-shadow: 0 0 0 3px rgba(239, 68, 68, .15); }
.dot--err     { background: #f59e0b; }

.sys-info-card__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--jf-text, #1f2937);
}

.sys-info-card__summary {
  font-size: 12px;
  color: var(--jf-muted, #9ca3af);
  font-family: ui-monospace, 'SF Mono', Menlo, monospace;
}
.sys-info-card__summary--err { color: #ef4444; }
.sys-info-card__sep { margin: 0 4px; }
.sys-info-card__sha {
  background: #f3f4f6;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--jf-text-2, #4b5563);
}

.sys-info-card__caret {
  margin-left: auto;
  color: var(--jf-muted, #9ca3af);
  font-size: 11px;
}

.sys-info-card__body {
  border-top: 1px solid var(--jf-border, #e8eaed);
  padding: 12px 14px 14px;
}

.sys-info-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.sys-info-table th {
  text-align: left;
  color: var(--jf-muted, #9ca3af);
  font-weight: 500;
  padding: 5px 12px 5px 0;
  width: 90px;
  vertical-align: top;
}
.sys-info-table td {
  color: var(--jf-text, #1f2937);
  padding: 5px 0;
  vertical-align: top;
}
.sys-info-table code {
  font-family: ui-monospace, 'SF Mono', Menlo, monospace;
  font-size: 11.5px;
  color: var(--jf-text-2, #4b5563);
}
.sys-info-muted {
  color: var(--jf-muted, #9ca3af);
  margin-left: 6px;
}

.sys-info-ok   { color: #22c55e; }
.sys-info-warn { color: #f59e0b; }

.sys-info-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10.5px;
  font-weight: 500;
}
.tag--ok  { background: #dcfce7; color: #166534; }
.tag--err { background: #fee2e2; color: #991b1b; }

.sys-info-card__actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.sys-info-btn {
  padding: 5px 12px;
  border: 1px solid var(--jf-border, #e8eaed);
  background: #fff;
  color: var(--jf-text-2, #4b5563);
  font-size: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all .15s;
}
.sys-info-btn:hover:not(:disabled) {
  border-color: var(--jf-primary, #1677ff);
  color: var(--jf-primary, #1677ff);
}
.sys-info-btn:disabled { opacity: .6; cursor: not-allowed; }

.sys-info-btn--primary {
  background: var(--jf-primary, #1677ff);
  border-color: var(--jf-primary, #1677ff);
  color: #fff;
}
.sys-info-btn--primary:hover:not(:disabled) {
  background: #0958d9;
  color: #fff;
}

.sys-info-card__hint {
  margin-top: 10px;
  padding: 8px 10px;
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
  border-radius: 4px;
  font-size: 12px;
  color: #78350f;
}
</style>