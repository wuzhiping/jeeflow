# mldong-flow-designer-dingtalk

钉钉风格流程设计器（精简版）。仅含钉钉树形设计器，**不含 LogicFlow 画布**，零 LogicFlow 依赖，适合纯审批流场景极简引入。

> 版本与双模式包 `mldong-flow-designer-plus` 联动发布（同一 commit、同一版本号）。
> 需要 canvas/dingtalk 双模式或存量画布流程兼容时，请使用双模式包。

## 安装

```shell
npm install mldong-flow-designer-dingtalk --registry=https://registry.npmmirror.com
```

## 使用

```ts
import { createApp } from 'vue'
import FlowDesigner from 'mldong-flow-designer-dingtalk'
import 'mldong-flow-designer-dingtalk/lib/style.css'

createApp(App).use(FlowDesigner).mount('#app')
```

```html
<MldongFlowDesignerPlus v-model:value="graphData" @on-save="handleSave" />
```

组件 props/events 与双模式包的钉钉模式完全一致，`@on-init` 回调参数为 `FDDesignerAPI`（命名与 LogicFlow 实例对齐）。
