---
name: yunxiao-weekly-report
description: 云效迭代周报生成。自动从云效"业财一体化"项目获取任务，生成格式化周报。支持单人/批量查询，默认获取刚过去的迭代，支持指定迭代号。
---

# 云效周报技能

## 📋 快速调用

```
# 单人周报
林小鹏周报

# 批量周报
全体人员周报 / 团队周报

# 指定迭代
Sprint 15的周报（林小鹏）
Sprint 16 周报（全体人员）
```

---

## 🎯 核心规则

| 规则 | 说明 |
|------|------|
| **项目** | 固定为"业财一体化" |
| **默认迭代** | 刚刚过去的迭代（当前时间 < 迭代结束 + 7天） |
| **支持人员** | 林小鹏、佘溢钶、赖武法、李铭发、龚宏飞、邹凯平 |

---

## 📝 周报格式

```
汇报人：XXX
汇报周期：YYYY年MM月DD日 - YYYY年MM月DD日

一、核心成果
【业财一体化】任务项
1. [任务名称] - 完成/完成度X%

【其他工作】
1. [工作内容]

二、下周期计划
【业财一体化】任务项
1. [任务名称]【紧急/高】
```

**进度表示**: 完成 / 完成度75% / 完成度50% / 完成度25% / 设计阶段 / 开发阶段

---

## ⚙️ 执行命令

```bash
# 单人周报
python3 ~/.openclaw/workspace/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py 林小鹏

# 指定迭代
python3 ~/.openclaw/workspace/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py 林小鹏 --sprint="Sprint 15"

# 批量周报
python3 ~/.openclaw/workspace/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py --all
```

---

## 📖 详细指南

- **执行步骤**: 参考 [GUIDE.md](GUIDE.md)
- **周报模板**: 参考 [TEMPLATE.md](TEMPLATE.md)

---

## 🔧 配置

| 配置项 | 路径 |
|--------|------|
| 云效配置 | `~/.openclaw/workspace/config/mcporter.json` |
| 执行脚本 | `~/.openclaw/workspace/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py` |
