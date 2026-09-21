# skills/feedback/ · 用户反馈闭环目录

> 本目录是 jeeflow 反馈闭环的**数据落点**.
> 流程规范见 `skills/FEEDBACK.md`.

---

## 目录结构

```
skills/feedback/
├── README.md                 # 本文件
├── inbox/                    # 接收后未完成的反馈
│   └── FB-NNNN.json          # 格式见 templates/fb-template.json
├── archive/                  # 已闭环的反馈
│   └── FB-NNNN.json          # 同结构, status=closed
├── metrics/                  # 反馈指标
│   ├── monthly-YYYY-MM.json  # 月度统计
│   └── trends.md             # 趋势分析
├── templates/
│   ├── fb-template.json      # FB-NNNN 数据模板
│   └── notify-template.md    # 客户通知模板 (A-G)
└── attachments/              # 客户原始附件 (复现 JSON / 截图)
    └── FB-NNNN-*.json
```

---

## 文件流转

```
   客户反馈 (任意通道)
        ↓
   inbox/FB-NNNN.json          ← status: received
        ↓ (分类)
   inbox/FB-NNNN.json          ← status: classified
        ↓ (处理)
   inbox/FB-NNNN.json          ← status: in_progress
        ↓ (内部验证 + 客户回访)
   inbox/FB-NNNN.json          ← status: verified
        ↓ (通知客户)
   inbox/FB-NNNN.json          ← status: notified
        ↓ (客户确认 / 沉默 14 天)
   archive/FB-NNNN.json        ← status: closed
        ↓
   lessons_learned 沉淀到 docs/ 或 skills/
```

---

## 当前状态 (2026-09-21)

| 状态 | 数量 | 编号 |
|------|------|------|
| closed | 1 | FB-0001 (历史回填 + 完整闭环示范) |
| notified (待客户确认) | 0 | — |
| verified | 0 | — |
| in_progress | 0 | — |
| classified | 0 | — |
| received | 4 | FB-0002 ~ FB-0005 |
| **合计** | **5** | — |

详见 `metrics/initial.md`.

---

## 编号约定

- 自 1 起递增, 不跳号, 不重复
- 格式: `FB-NNNN` (4 位数)
- 9999 之后: `FB-10001`, `FB-10002`, ...
- 编号是追溯的 key, 不得修改

---

## 与 raw data 的关系

`skills/feedback/` 不复制 raw data.
需要引用时, 在 JSON 字段里写路径, 例如:

```json
"attachments": [
  "tdd/expense_report_repro.json",   // 引用, 不复制
  "docs/BUGS.md §111",
  "bdd/bdd-1501-1503-fix-t110-task-multi-out_20260920.sh"
]
```

如客户上传了大文件 (截图 / 视频), 存到 `attachments/` 子目录,
并在 FB-NNNN.json 中记录文件名.

---

## 维护约定

- inbox 文件可被多次更新 (status 流转)
- archive 文件**不再修改** (只读历史)
- 每月初统计上月数据, 写入 `metrics/monthly-YYYY-MM.json`
- 季度复盘写入 `metrics/trends.md`

---

## 行动项

- [ ] 完成 FB-0001 完整闭环 (本轮交付)
- [ ] 回填 ≥ 4 条历史 BUG (FB-0002 ~ FB-0005)
- [ ] 创建 `metrics/initial.md` 反馈初始统计
- [ ] 与 flowuser 建立沟通节奏
