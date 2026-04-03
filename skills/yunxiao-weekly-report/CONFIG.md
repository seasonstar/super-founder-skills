# 云效技能 - 配置

所有敏感配置（组织ID、用户映射等）统一存放在本地文件中，**不进入 Git 仓库**。

## 配置文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 云效配置 | `~/.yunxiao/config.json` | 组织ID、项目名、用户ID映射 |

## config.json 结构

```json
{
  "organizationId": "组织ID",
  "projectName": "项目名称",
  "bufferDays": 7,
  "wecomWebhook": "企微Webhook地址",
  "members": {
    "姓名": "用户ID"
  }
}
```

## 使用方式

技能执行时，**自动读取** `~/.yunxiao/config.json`，获取：
- `organizationId` — 云效组织 ID
- `projectName` — 项目名称（用于匹配项目）
- `members` — 姓名→用户ID 映射（避免硬编码）
- `wecomWebhook` — 企微通知地址
- `bufferDays` — 迭代缓冲天数
