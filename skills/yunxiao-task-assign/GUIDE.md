# 云效任务分配技能 - 执行指南

## 📋 执行步骤

### Step 1: 解析用户意图

提取关键信息：
| 字段 | 必填 | 示例 |
|------|------|------|
| 任务标题 | ✅ | "修复登录bug" |
| 负责人 | ✅ | 林小鹏 |
| 优先级 | ❌ | 高/中/低（默认：中） |
| 迭代 | ❌ | Sprint 17（默认：当前迭代） |
| 描述 | ❌ | 详细说明 |
| 截止日期 | ❌ | 2026-03-15 |

---

### Step 2: 获取配置

读取配置文件获取：
- Organization ID: `688c88cc9eda9d4e3ee46203`
- 项目名称: "业财一体化"
- 用户ID映射
- 企微 Webhook

配置路径: `~/.yunxiao/config.json`

鉴权令牌读取顺序：
1. `YUNXIAO_ACCESS_TOKEN` 环境变量
2. `~/.yunxiao/config.json` 中的 `accessToken` 或 `token`
3. `~/.codex/config.toml` 中的 `mcp_servers.yunxiao.env.YUNXIAO_ACCESS_TOKEN`

`~/.openclaw/workspace/config/mcporter.json` 已不再是本技能依赖项。

---

### Step 3: 推荐执行方式

使用本技能脚本直接调用云效 OpenAPI，不走 Codex MCP：

```bash
python3 /Users/mac/.cc-switch/skills/yunxiao-task-assign/scripts/yunxiao-task-assign.py \
  --title "修复登录bug" \
  --assignee "林小鹏" \
  --priority "中"
```

可选参数：

| 参数 | 说明 |
|------|------|
| `--priority 高/中/低/紧急` | 默认 `中` |
| `--sprint "Sprint 17"` | 指定迭代；未指定则取当前迭代，无当前迭代则取下一个 |
| `--description "..."` | 任务描述，按 Markdown 写入 |
| `--deadline YYYY-MM-DD` | 追加到任务描述中 |
| `--no-notify` | 不推送企微通知 |
| `--dry-run` | 只做预检，不创建任务 |
| `--smoke-test` | 只验证云效 OpenAPI 连通性 |

---

### Step 4: 获取项目ID

底层 OpenAPI：

```http
POST /oapi/v1/projex/organizations/{organizationId}/projects:search
```

参数：
- organizationId: `688c88cc9eda9d4e3ee46203`

从返回列表中匹配"业财一体化"获取项目ID。

---

### Step 5: 验证/获取用户ID

**方式1**: 使用配置映射
```
姓名 → 用户ID（从 ~/.yunxiao/config.json 读取）
```

**方式2**: 动态查询
```http
POST /oapi/v1/platform/organizations/{organizationId}/members:search
```

参数：
- organizationId: `688c88cc9eda9d4e3ee46203`
- query: [用户名]

---

### Step 6: 确定迭代ID

```http
GET /oapi/v1/projex/organizations/{organizationId}/projects/{projectId}/sprints
```

参数：
- organizationId: `688c88cc9eda9d4e3ee46203`
- id: [项目ID]

**迭代选择逻辑**:

1. **用户指定**: 直接匹配 `sprint.name`
2. **默认（当前时段）**: 找 `startDate <= now <= endDate` 的迭代

```python
now = Date.now()
# 当前时段的迭代
current_sprint = sprints.find(s => s.startDate <= now <= endDate)

# 若无进行中的迭代，取下一个即将开始的
if not current_sprint:
    current_sprint = sprints.filter(s => s.startDate > now).sort(by=startDate)[0]
```

---

### Step 7: 获取工作项类型ID

```http
GET /oapi/v1/projex/organizations/{organizationId}/projects/{projectId}/workitemTypes?category=Task
```

参数：
- organizationId: `688c88cc9eda9d4e3ee46203`
- projectId: [项目ID]
- category: "Task"

从返回列表中获取 Task 类型的 `id` 字段。

---

### Step 8: 创建工作项

```http
POST /oapi/v1/projex/organizations/{organizationId}/workitems
```

**核心参数**:
| 参数 | 必填 | 说明 |
|------|------|------|
| organizationId | ✅ | 组织ID |
| spaceId | ✅ | 项目ID |
| subject | ✅ | 任务标题 |
| assignedTo | ✅ | 负责人ID |
| workitemTypeId | ✅ | 工作项类型ID（从 Step 6 获取） |
| customFieldValues.priority | ❌ | 0-高, 1-中, 2-低 |
| sprint | ❌ | 迭代ID |
| description | ❌ | 任务描述 |

**⚠️ 注意**: `workitemTypeId` 必须是实际的类型 ID（如 `ba102e46bc6a8483d9b7f25c`），不能传字符串 "Task"

---

### Step 9: 推送企微通知

创建成功后，推送通知到IT群：

```bash
curl -X POST \
  'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=23a1f0ba-bcad-4b25-bd06-e39b43569eec' \
  -H 'Content-Type: application/json' \
  -d '{
    "msgtype": "markdown",
    "markdown": {
      "content": "### 📋 新任务分配\n\n**任务**: [任务标题]\n**负责人**: @[姓名]\n**优先级**: [高/中/低]\n**迭代**: [Sprint XX]\n\n[查看详情](云效链接)"
    }
  }'
```

---

### Step 10: 输出结果

```
✅ 任务创建成功

📋 任务信息
━━━━━━━━━━━━━━━━━━━━━━━━━━
标题：[任务名称]
负责人：[姓名]
优先级：[高/中/低]
迭代：[Sprint XX]
状态：待处理
ID：[工作项ID]

🔗 云效链接
https://devops.aliyun.com/projex/workspace/[spaceId]/workitem/[itemId]

📢 已推送企微通知到IT群
```

---

## 🚨 错误处理

| 场景 | 处理方式 |
|------|---------|
| 找不到项目 | 报错并停止 |
| 用户名无效 | 列出有效人员名单 |
| 迭代不存在 | 列出可用迭代 |
| 创建失败 | 显示错误详情，提供重试建议 |

---

## ✅ 测试用例

| 输入 | 期望结果 |
|------|---------|
| 把"修复bug"分配给林小鹏 | 创建任务，负责人林小鹏 |
| 给李铭发创建高优先级任务"接口开发" | 创建任务，优先级高 |
| Sprint 18任务"优化查询"分配给赖武法 | 创建任务，分配到Sprint 18 |
