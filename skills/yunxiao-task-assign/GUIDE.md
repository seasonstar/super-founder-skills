# 云效任务分配技能 - 执行指南

## 📋 执行步骤

### Step 1: 解析用户意图

提取关键信息：
| 字段 | 必填 | 示例 |
|------|------|------|
| 任务标题 | ✅ | "修复登录bug" |
| 负责人 | ✅ | 姓名 |
| 优先级 | ❌ | 高/中/低（默认：中） |
| 迭代 | ❌ | Sprint 17（默认：当前迭代） |
| 描述 | ❌ | 详细说明 |
| 截止日期 | ❌ | 2026-03-15 |

---

### Step 2: 读取本地配置

```
Read file: ~/.yunxiao/config.json
```

从中获取：
- `organizationId` — 组织 ID
- `projectName` — 项目名称
- `members` — 姓名→用户ID 映射表

---

### Step 3: 获取项目ID

```
mcp__alibabacloud-devops__search_projects
```

参数：
- organizationId: 从 config.json 获取

从返回列表中精确匹配项目名称获取项目 ID。

---

### Step 4: 验证/获取用户ID

**优先使用映射表**（从 config.json 的 `members` 字段读取姓名→用户ID）。

**动态查询**（映射表中没有时）:
```
mcp__alibabacloud-devops__search_organization_members
```

参数：
- organizationId: 从 config.json 获取
- query: [用户名]

---

### Step 5: 确定迭代ID

```
mcp__alibabacloud-devops__list_sprints
```

参数：
- organizationId: 从 config.json 获取
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

### Step 6: 获取工作项类型ID

```
mcp__yunxiao__get_work_item_types
```

参数：
- organizationId: 从 config.json 获取
- projectId: [项目ID]
- category: "Task"

从返回列表中获取 Task 类型的 `id` 字段。

---

### Step 7: 创建工作项

```
mcp__yunxiao__create_work_item
```

**核心参数**:
| 参数 | 必填 | 说明 |
|------|------|------|
| organizationId | ✅ | 组织ID |
| spaceId | ✅ | 项目ID |
| subject | ✅ | 任务标题 |
| assignedTo | ✅ | 负责人ID |
| workitemTypeId | ✅ | 工作项类型ID（从 Step 6 获取） |
| priority | ❌ | 0-高, 1-中, 2-低 |
| sprint | ❌ | 迭代ID |
| description | ❌ | 任务描述 |

**⚠️ 注意**: `workitemTypeId` 必须是实际的类型 ID（如 `ba102e46bc6a8483d9b7f25c`），不能传字符串 "Task"

---

### Step 8: 推送企微通知

创建成功后，从 config.json 读取 `wecomWebhook`，推送通知：

```bash
curl -X POST \
  '[wecomWebhook URL]' \
  -H 'Content-Type: application/json' \
  -d '{
    "msgtype": "markdown",
    "markdown": {
      "content": "### 📋 新任务分配\n\n**任务**: [任务标题]\n**负责人**: @[姓名]\n**优先级**: [高/中/低]\n**迭代**: [Sprint XX]\n\n[查看详情](云效链接)"
    }
  }'
```

---

### Step 9: 输出结果

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
https://devops.aliyun.com/projex/workspace/[spaceId]/workitem/[itemId]

📢 已推送企微通知到IT群
```

---

## 🚨 错误处理

| 场景 | 处理方式 |
|------|---------|
| config.json 不存在 | 提示用户创建 `~/.yunxiao/config.json` |
| 找不到项目 | 报错并停止 |
| 用户名无效 | 列出 config.json 中配置的成员名单 |
| 迭代不存在 | 列出可用迭代 |
| 创建失败 | 显示错误详情，提供重试建议 |
