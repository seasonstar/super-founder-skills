# 云效周报技能 - 执行指南

## 📋 执行步骤

### Step 1: 解析用户意图

| 用户输入 | 操作类型 | 迭代号 |
|---------|---------|--------|
| "XX周报" | 单人 | 默认（刚过去的迭代） |
| "全体人员周报" / "团队周报" | 批量 | 默认 |
| "Sprint 15周报（XX）" | 单人 | Sprint 15 |
| "Sprint 16 周报（全体）" | 批量 | Sprint 16 |

---

### Step 2: 读取本地配置

```
Read file: ~/.yunxiao/config.json
```

从中获取：
- `organizationId` — 组织 ID
- `projectName` — 项目名称
- `members` — 姓名→用户ID 映射表
- `bufferDays` — 迭代缓冲天数

---

### Step 3: 获取项目ID

```
mcp__alibabacloud-devops__search_projects
```

参数：
- organizationId: 从 config.json 获取

从返回列表中精确匹配 `config.json` 中的 `projectName`，获取项目 ID。

---

### Step 4: 获取迭代列表

```
mcp__alibabacloud-devops__list_sprints
```

参数：
- organizationId: 从 config.json 获取
- id: [项目ID]

**处理**: 解析每个迭代的 name, startDate, endDate, id

---

### Step 5: 确定目标迭代

**用户指定**: 直接查找匹配 `sprint.name`

**默认（刚过去的迭代）**:
```python
now = Date.now()
buffer_ms = config.bufferDays * 24 * 60 * 60 * 1000

# 找"刚过去的迭代"：已结束且在缓冲期内
target = sprints.find(s => s.endDate < now <= (s.endDate + buffer_ms))

# 找不到则取最后一个已结束的迭代
if not target:
    target = sprints.filter(s => s.endDate < now).sort(by=endDate, desc=True)[0]
```

**同时确定下一个迭代**：从列表中找目标迭代之后的一个迭代，用于"下周期计划"。

---

### Step 6: 获取用户ID

**优先使用映射表**（从 config.json 的 `members` 字段读取姓名→用户ID）。

**动态查询**（映射表中没有时）:
```
mcp__alibabacloud-devops__search_organization_members
```

参数：
- organizationId: 从 config.json 获取
- query: [用户名]

---

### Step 7: 获取工作项

**分别查询 Req（需求）和 Task（任务）**:

```
mcp__yunxiao__search_workitems
```

| 参数 | 值 |
|------|-----|
| organizationId | 从 config.json 获取 |
| spaceId | [项目ID] |
| category | "Req" 或 "Task" |
| assignedTo | [用户ID] |
| sprint | [迭代ID] |
| perPage | 100 |

---

### Step 8: 获取下一迭代工作项

同 Step 7，使用 `nextSprint.id` 作为 sprint 参数。

---

### Step 9: 生成周报

按 [TEMPLATE.md](TEMPLATE.md) 格式生成，**任务分类**:

| 状态 | 归类 | 完成度 |
|------|------|--------|
| 已完成 | 核心成果 | 100% |
| 进行中/开发中/设计中 | 核心成果 | 30%-90%（智能标注设计阶段/开发阶段） |
| 待处理 | 不显示 | - |

**优先级显示**: 只有"紧急"和"高"才在任务后显示【优先级】

---

### Step 10: 输出结果

**单人周报**:
```
═══════════════════════════════════════
【姓名】周报
═══════════════════════════════════════

[周报内容]

═══════════════════════════════════════
📊 统计：已完成 X | 进行中 X | 待处理 X
```

**批量周报**:
```
═══════════════════════════════════════
📋 团队周报汇总
📅 YYYY-MM-DD
═══════════════════════════════════════

【姓名】
[周报内容]
─────────────────────────────────────
【姓名】
[周报内容]
...

═══════════════════════════════════════
📊 团队统计：已完成 XX | 进行中 XX | 待处理 XX
```

---

## 🚨 错误处理

| 场景 | 处理方式 |
|------|---------|
| config.json 不存在 | 提示用户创建 `~/.yunxiao/config.json` |
| 找不到项目 | 报错并停止 |
| 找不到指定迭代 | 报错并列出可用迭代 |
| 工作项查询失败 | 重试 1 次，仍失败则跳过该用户 |
| 用户ID找不到 | 跳过该用户，继续下一个 |

---

## ✅ 测试用例

| 输入 | 期望结果 |
|------|---------|
| "XX周报" | 生成刚过去迭代的单人周报 |
| "全体人员周报" | 生成全员汇总周报 |
| "Sprint 15周报（XX）" | 生成 Sprint 15 的单人周报 |
| "Sprint 99周报" | 报错：未找到迭代，列出可用迭代 |
