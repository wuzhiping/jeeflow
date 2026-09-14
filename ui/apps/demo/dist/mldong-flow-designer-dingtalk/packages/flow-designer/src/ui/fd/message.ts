/**
 * FDMessage —— 自研轻量消息提示（替代 antd message / element-plus ElMessage）
 * 纯 DOM 实现，无组件实例开销；多条消息垂直堆叠，自动消失
 */
type MessageType = 'success' | 'error' | 'info'

const CONTAINER_ID = 'fd-message-container'
const DURATION = 3000

const ICONS: Record<MessageType, string> = {
  success: '<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.5" fill="none" stroke="currentColor"/><path d="M4.2 7.2l1.9 1.9 3.7-4" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  error: '<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.5" fill="none" stroke="currentColor"/><path d="M5 5l4 4M9 5l-4 4" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
  info: '<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.5" fill="none" stroke="currentColor"/><path d="M7 6.5v3.5M7 4.2v.1" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>'
}

const COLORS: Record<MessageType, string> = {
  success: '#52c41a',
  error: '#ff4d4f',
  info: '#1677ff'
}

let styleInjected = false

function injectStyle() {
  if (styleInjected) return
  styleInjected = true
  const style = document.createElement('style')
  style.textContent = `
.fd-message-container {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;
}
.fd-message-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  font-size: 14px;
  color: #333;
  opacity: 0;
  transform: translateY(-8px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fd-message-item--in {
  opacity: 1;
  transform: translateY(0);
}
`
  document.head.appendChild(style)
}

function getContainer(): HTMLElement {
  let container = document.getElementById(CONTAINER_ID)
  if (!container) {
    container = document.createElement('div')
    container.id = CONTAINER_ID
    container.className = 'fd-message-container'
    document.body.appendChild(container)
  }
  return container
}

function show(type: MessageType, content: string, duration = DURATION) {
  if (typeof document === 'undefined') return
  injectStyle()
  const container = getContainer()
  const item = document.createElement('div')
  item.className = 'fd-message-item'
  item.innerHTML = `<span style="color:${COLORS[type]};display:inline-flex;">${ICONS[type]}</span><span></span>`
  // 文本走 textContent 防注入
  item.lastElementChild!.textContent = content
  container.appendChild(item)
  requestAnimationFrame(() => {
    item.classList.add('fd-message-item--in')
  })
  setTimeout(() => {
    item.classList.remove('fd-message-item--in')
    setTimeout(() => {
      item.remove()
      if (!container.childElementCount) {
        container.remove()
      }
    }, 220)
  }, duration)
}

const FDMessage = {
  success: (content: string, duration?: number) => show('success', content, duration),
  error: (content: string, duration?: number) => show('error', content, duration),
  info: (content: string, duration?: number) => show('info', content, duration)
}

export default FDMessage
