---
name: yunxiao-weekly-report
description: 云效周报生成。在云效"业财一体化"项目中查询成员工作项并生成格式化周报。触发词：周报、XX周报、团队周报、Sprint XX周报。支持单人和全体周报。
---

# 云效周报技能

## 快速调用

```
# 单人周报
林小鹏周报

# 批量周报
全体人员周报 / 团队周报

# 指定迭代
Sprint 18周报（林小鹏）
Sprint 17 周报（全体人员）
```

底层执行使用本技能自带 OpenAPI 脚本，不依赖 MCP：

```bash
# 单人周报（不推送企微）
python3 /Users/mac/.claude/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py \
  --member "林小鹏" --no-notify

# 全体周报（推送企微）
python3 /Users/mac/.claude/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py

# 指定迭代
python3 /Users/mac/.claude/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py \
  --member "林小鹏" --sprint "Sprint 18" --no-notify
```

---

## 核心规则

| 规则 | 说明 |
|------|------|
| **项目** | 固定为"业财一体化" |
| **默认迭代** | 刚刚过去的迭代（当前时间 < 迭代结束 + bufferDays） |
| **支持人员** | 从 `~/.yunxiao/config.json` 的 `members` 读取 |
| **企微通知** | 默认推送，`--no-notify` 关闭 |
| **调用方式** | 直接调用云效 OpenAPI；不使用 `mcp__yunxiao__*` |

---

## 可选参数

| 参数 | 说明 |
|------|------|
| `--member "姓名"` | 指定成员，不指定则生成全体 |
| `--sprint "Sprint 18"` | 指定迭代；默认取刚过去的迭代 |
| `--no-notify` | 不推送企微通知 |
| `--dry-run` | 只做预检，不生成周报 |
| `--smoke-test` | 只验证云效 OpenAPI 连通性 |

---

## 周报格式

```
汇报人：XXX
汇报周期：YYYY年MM月DD日 - YYYY年MM月DD日

一、核心成果
【业财一体化】
1. [任务名称] - 完成 【紧急】
2. [任务名称] - 开发阶段

【其他工作】
1. [工作内容] - 完成

二、下周期计划
（Sprint XX：YYYY年MM月DD日 - YYYY年MM月DD日）
【业财一体化】
1. [任务名称] - 开发中 【紧急】
2. [任务名称] 【高】
```

**进度表示**: 完成 / 开发阶段 / 设计阶段
**优先级显示**: 只有"紧急"和"高"才在任务后标注

---

## 配置

| 配置项 | 值 |
|--------|-----|
| 云效配置 | `~/.yunxiao/config.json` |
| 云效令牌 | 优先读取环境变量 `YUNXIAO_ACCESS_TOKEN`，其次读取 `~/.yunxiao/config.json` 或 `~/.codex/config.toml` |
| 企微Webhook | 从 `~/.yunxiao/config.json` 的 `wecomWebhook` 读取 |
| 连通性测试 | `python3 /Users/mac/.claude/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py --smoke-test` |

---

## 详细指南

- **执行步骤**: 参考 [GUIDE.md](GUIDE.md)
- **周报模板**: 参考 [TEMPLATE.md](TEMPLATE.md)
