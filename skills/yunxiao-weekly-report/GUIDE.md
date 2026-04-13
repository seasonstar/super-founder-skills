# 云效周报技能 - 执行指南

## 执行步骤

### Step 1: 解析用户意图

| 用户输入 | 操作类型 | 迭代号 |
|---------|---------|--------|
| "XX周报" | 单人 | 默认（刚过去的迭代） |
| "全体人员周报" / "团队周报" | 批量 | 默认 |
| "Sprint 15周报（XX）" | 单人 | Sprint 15 |
| "Sprint 16 周报（全体）" | 批量 | Sprint 16 |

---

### Step 2: 推荐执行方式

使用本技能脚本直接调用云效 OpenAPI，不走 MCP：

```bash
python3 /Users/mac/.claude/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py \
  --member "林小鹏" --no-notify
```

脚本内部自动完成以下所有步骤。下面描述脚本调用的 OpenAPI 端点供参考。

---

### Step 3: 获取配置

读取配置文件获取：
- Organization ID: `688c88cc9eda9d4e3ee46203`
- 项目名称: "业财一体化"
- 用户ID映射
- 企微 Webhook
- 缓冲天数

配置路径: `~/.yunxiao/config.json`

鉴权令牌读取顺序：
1. `YUNXIAO_ACCESS_TOKEN` 环境变量
2. `~/.yunxiao/config.json` 中的 `accessToken` 或 `token`
3. `~/.codex/config.toml` 中的 `mcp_servers.yunxiao.env.YUNXIAO_ACCESS_TOKEN`

---

### Step 4: 获取项目ID

底层 OpenAPI：

```http
POST /oapi/v1/projex/organizations/{organizationId}/projects:search
```

从返回列表中匹配"业财一体化"获取项目 ID。

---

### Step 5: 获取迭代列表

```http
GET /oapi/v1/projex/organizations/{organizationId}/projects/{projectId}/sprints
```

**确定目标迭代**:

1. **用户指定**: 直接匹配 `sprint.name`
2. **默认（刚过去的迭代）**:
   - 找已结束且在缓冲期内（`endDate < now <= endDate + bufferDays * 86400000`）
   - 找不到则取最后一个已结束的迭代

**同时确定下一个迭代**：从列表中找目标迭代之后的一个迭代，用于"下周期计划"。

---

### Step 6: 获取用户ID

**优先使用映射表**（从 config.json 的 `members` 字段读取姓名->用户ID）。

**动态查询**（映射表中没有时）:

```http
POST /oapi/v1/platform/organizations/{organizationId}/members:search
```

参数：
- query: [用户名]

---

### Step 7: 获取工作项

```http
POST /oapi/v1/projex/organizations/{organizationId}/workitems:search
```

| 参数 | 值 |
|------|-----|
| spaceId | [项目ID] |
| category | "Req,Task" |
| assignedTo | [用户ID] |
| sprint | [迭代ID] |
| page | 1 |
| perPage | 200 |

分别查询目标迭代和下一个迭代的工作项。

---

### Step 8: 生成周报

按 [TEMPLATE.md](TEMPLATE.md) 格式生成，**任务分类**:

| 状态 | 归类 | 完成度 |
|------|------|--------|
| 已完成 | 核心成果 | 完成 |
| 进行中/开发中/设计中 | 核心成果 | 开发阶段/设计阶段 |
| 待处理 | 不显示 | - |

**任务自动分类**（按标题前缀）:

| 前缀 | 分类 |
|------|------|
| 业财一体化 | 业财一体化 |
| TK | TK数据看板项目 |
| RPA | RPA |
| 运维 | 运维 |
| 学习 | 学习提升 |
| 其他 | 其他工作 |

**优先级显示**: 只有"紧急"和"高"才在任务后标注

---

### Step 9: 输出结果

**单人周报**:
```
========================================
【姓名】周报
========================================

[周报内容]

========================================
统计：已完成 X | 进行中 X | 待处理 X
========================================
```

**批量周报**:
```
========================================
团队周报汇总
YYYY年MM月DD日 - YYYY年MM月DD日
========================================

----------------------------------------
【姓名】
[周报内容]

----------------------------------------
【姓名】
[周报内容]

========================================
统计：已完成 XX | 进行中 XX | 待处理 XX
========================================
```

---

### Step 10: 推送企微通知（可选）

创建成功后，推送 Markdown 格式通知到IT群：

```bash
curl -X POST \
  'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...' \
  -H 'Content-Type: application/json' \
  -d '{"msgtype":"markdown","markdown":{"content":"..."}}'
```

使用 `--no-notify` 跳过此步骤。

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| config.json 不存在 | 提示用户创建 `~/.yunxiao/config.json` |
| 找不到项目 | 报错并停止 |
| 找不到指定迭代 | 报错并列出可用迭代 |
| 工作项查询失败 | 显示 API 错误详情 |
| 用户ID找不到 | 跳过该用户，继续下一个 |
| 企微推送失败 | 提示失败，不影响周报输出 |

---

## 测试用例

| 输入 | 期望结果 |
|------|---------|
| `--member "林小鹏" --no-notify` | 生成刚过去迭代的单人周报，不推送企微 |
| （无参数） | 生成全员汇总周报并推送企微 |
| `--member "林小鹏" --sprint "Sprint 18"` | 生成 Sprint 18 的单人周报 |
| `--sprint "Sprint 99"` | 报错：未找到迭代，列出可用迭代 |
| `--smoke-test` | 验证连通性并输出项目/迭代信息 |
| `--dry-run` | 输出预检信息，不生成周报 |
