# 反馈闭环 · 客户通知模板

> 适用: `FEEDBACK.md §3.5` 步骤 5 (通知客户)
> 填写: 把 `{占位符}` 替换为真实内容即可

---

## 模板 A · BUG 修复类 (主要)

```
【jeeflow 反馈闭环 · {FB-NNNN}】

你好 {客户名},

你 {反馈日期} 反馈的 "{原问题一句话摘要}" 已处理:

✅ 状态: 已修复
🔧 修复编号: {FIX-Tnnn} (2026-09-DD)
🔗 修复要点: {一句技术语言描述}
📄 文档更新: {docs/BUGS.md §X 或 docs/known-issues.md §Y}
🧪 验证用例: {BDD 编号, 9/9 PASS}
🌐 双端一致性: MEM (8101) + PG (8102) 行为一致

📌 建议复测:
- 重启 main.py 后重跑你的流程
- 关注点: {客户场景里需要特别看的细节}
- 如果仍有问题, 随时 DM 我们

感谢你的反馈, 帮助 jeeflow 变得更好.

— hermes (流程设计师) / bro (引擎开发者)
```

---

## 模板 B · 改进建议类

```
【jeeflow 反馈闭环 · {FB-NNNN}】

你好 {客户名},

感谢你 {反馈日期} 提出的改进建议: "{建议一句话摘要}".

📋 当前决策: {接受 / 排期 / 拒绝}
- 接受 → 预计 {YYYY-MM} 纳入路线图
- 排期 → 进入 Phase {X.Y} 候选池, 季度评估
- 拒绝 → 理由: {一句话}

我们已把这条建议记入 `skills/roadmap/candidates/{FB-NNNN}.md`,
下季度复盘时会再次评估.

如果你能补充更多场景 (例如: "我希望能支持 XXX, 因为 YYY"),
会帮助我们在排期时权衡.

— hermes
```

---

## 模板 C · 文档问题类

```
【jeeflow 反馈闭环 · {FB-NNNN}】

你好 {客户名},

感谢你 {反馈日期} 指出文档问题: "{问题一句话摘要}".

📄 修订:
- 文件: `docs/{file}.md §{section}`
- 内容: {修订要点, 一句话}
- 修订时间: 2026-09-DD

修订后内容已同步到 dv 分支, 你下次拉取即可看到.
如仍有歧义, 欢迎继续指出.

— hermes
```

---

## 模板 D · UX 问题类 (转 UI 团队)

```
【jeeflow 反馈闭环 · {FB-NNNN}】

你好 {客户名},

感谢你 {反馈日期} 反馈的体验问题: "{痛点一句话摘要}".

📋 当前进度: 已转交 UI 团队
- 需求单: `ui/requirements/{FB-NNNN}.md`
- 预计回复: {YYYY-MM-DD} 前

由于本阶段我们聚焦在反馈闭环本身,
UI 改进会纳入下一阶段 (Phase 9) 路线图.

— hermes
```

---

## 模板 E · 即时咨询类

```
【jeeflow 答疑 · {FB-NNNN}】

{咨询内容原文}

📌 答复:
{答复内容, 引用 docs/flow.md §X 或其他文档}

如仍有疑问, 欢迎追问.

— hermes
```

---

## 模板 F · 客户沉默提醒 (二次通知)

```
【jeeflow 反馈闭环 · {FB-NNNN} · 二次提醒】

你好 {客户名},

我们 {首次通知日期} 通知过你关于 "{原问题}" 的修复,
想确认一下: 你方便的时候能否复测一下?

如果已无问题, 无需回复.
如果仍有问题或有新发现, 欢迎随时 DM 我们.

(若无回复, 14 天后我们会标记为"已通知-客户沉默"并归档.)

— hermes
```

---

## 模板 G · 归档通知 (团队内部)

```
【FB 归档 · {FB-NNNN}】

📋 基本信息
- 反馈 ID: {FB-NNNN}
- 类型: {type} / 优先级: {priority}
- 客户: {customer_id} ({type})
- 反馈日期: {date}
- 闭环日期: {date}

🔧 修复
- FIX: {FIX-Tnnn}
- 验证: {BDD IDs}

📚 沉淀
- docs/BUGS.md §X
- docs/known-issues.md §Y
- skills/FEEDBACK.md lessons: {一句话}

📊 闭环 SLA
- 首次响应: {date}
- 处理完成: {date}
- 客户通知: {date}
- 总周期: {N 天}
- SLA 达标: ✅ / ❌
```

---

## 填写示例

参见 `skills/feedback/archive/FB-0001.json` 的 `notified.content_summary` 字段.
