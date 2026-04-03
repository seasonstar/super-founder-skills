---
name: yunxiao-task-assign
description: 云效任务分配。在云效"业财一体化"项目中创建任务并分配给指定人员。触发词：分配任务、创建任务、给某人分配工作。支持快速分配和带详细信息的分配。
---

# 云效任务分配技能

## 📋 快速调用

```
# 快速分配
把"修复登录bug"分配给林小鹏
创建任务"数据接口开发"并分配给李铭发

# 带详情分配
给龚宏飞分配任务：优化ERP查询性能，优先级高，属于Sprint 17

# 批量分配
创建以下任务并分配给赖武法：
1. 数据库索引优化
2. 查询性能测试
3. 监控告警配置
```

---

## 🎯 核心规则

| 规则 | 说明 |
|------|------|
| **项目** | 固定为"业财一体化" |
| **必填项** | 任务标题 + 负责人 |
| **可选项** | 优先级、迭代、描述、截止日期 |
| **默认迭代** | 当前时段进行中的Sprint，无则取下一个 |
| **支持人员** | 从 `~/.yunxiao/config.json` 的 `members` 读取 |
| **企微通知** | 创建后自动推送IT群 |

---

## 📝 输出格式

```
✅ 任务创建成功

📋 任务信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
标题：[任务名称]
负责人：[姓名]
优先级：[高/中/低]
迭代：[Sprint XX]
状态：待处理

🔗 云效链接
https://devops.aliyun.com/...

📢 已推送企微通知到IT群
```

---

## 🔧 依赖的 MCP 工具

按顺序调用以下 MCP 工具完成任务：

| 步骤 | MCP 工具 | 用途 |
|------|---------|------|
| 1 | `mcp__alibabacloud-devops__search_projects` | 获取项目 ID |
| 2 | `mcp__alibabacloud-devops__search_organization_members` | 获取用户 ID |
| 3 | `mcp__alibabacloud-devops__list_sprints` | 获取迭代列表 |
| 4 | `mcp__yunxiao__get_work_item_types` | 获取工作项类型 ID |
| 5 | `mcp__yunxiao__create_work_item` | 创建工作项 |

---

## 📖 详细指南

- **执行步骤**: 参考 [GUIDE.md](GUIDE.md)

---

## 🔧 配置

| 配置项 | 值 |
|--------|-----|
| 企微Webhook | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=23a1f0ba-bcad-4b25-bd06-e39b43569eec` |
 |
| 云效配置 | `~/.yunxiao/config.json`（组织ID、成员映射、Webhook） |
