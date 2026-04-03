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

## 🔧 依赖的 MCP 工具

按顺序调用以下 MCP 工具完成任务：

| 步骤 | MCP 工具 | 用途 |
|------|---------|------|
| 1 | `mcp__alibabacloud-devops__search_projects` | 获取项目 ID |
| 2 | `mcp__alibabacloud-devops__list_sprints` | 获取迭代列表 |
| 3 | `mcp__alibabacloud-devops__search_organization_members` | 获取用户 ID |
| 4 | `mcp__yunxiao__search_workitems` | 查询工作项（Req + Task） |

---

## 📖 详细指南

- **执行步骤**: 参考 [GUIDE.md](GUIDE.md)
- **周报模板**: 参考 [TEMPLATE.md](TEMPLATE.md)

---

## 🔧 配置

参考 [CONFIG.md](CONFIG.md) 获取组织 ID、项目名称和用户 ID 映射。
