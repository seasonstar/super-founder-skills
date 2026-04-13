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

底层执行使用本技能自带 OpenAPI 脚本，不依赖 Codex MCP：

```bash
python3 /Users/mac/.cc-switch/skills/yunxiao-task-assign/scripts/yunxiao-task-assign.py \
  --title "修复登录bug" \
  --assignee "林小鹏"
```

---

## 🎯 核心规则

| 规则 | 说明 |
|------|------|
| **项目** | 固定为"业财一体化" |
| **必填项** | 任务标题 + 负责人 |
| **可选项** | 优先级、迭代、描述、截止日期 |
| **默认迭代** | 当前时段进行中的Sprint，无则取下一个 |
| **支持人员** | 林小鹏、佘溢钶、赖武法、李铭发、龚宏飞、邹凯平 |
| **企微通知** | 创建后自动推送IT群 |
| **调用方式** | 直接调用云效 OpenAPI；不使用 `mcp__yunxiao__*` |

---

## 📝 输出格式

```
✅ 任务创建成功

📋 任务信息
━━━━━━━━━━━━━━━━━━━━━━━━━━
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

## 🔧 配置

| 配置项 | 值 |
|--------|-----|
| 云效配置 | `~/.yunxiao/config.json` |
| 云效令牌 | 优先读取环境变量 `YUNXIAO_ACCESS_TOKEN`，其次读取 `~/.yunxiao/config.json` 或 `~/.codex/config.toml` |
| 企微Webhook | 从 `~/.yunxiao/config.json` 的 `wecomWebhook` 读取 |
| 连通性测试 | `python3 /Users/mac/.cc-switch/skills/yunxiao-task-assign/scripts/yunxiao-task-assign.py --smoke-test` |

---

## 📖 详细指南

- **执行步骤**: 参考 [GUIDE.md](GUIDE.md)
