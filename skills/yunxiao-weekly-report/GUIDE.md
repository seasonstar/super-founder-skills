# 云效周报技能 - 详细执行指南

## 📋 执行步骤

### Step 1: 解析用户意图

| 用户输入 | 操作类型 | 迭代号 |
|---------|---------|--------|
| "林小鹏周报" | 单人 | 默认（刚过去的迭代） |
| "全体人员周报" | 批量 | 默认 |
| "Sprint 15周报（林小鹏）" | 单人 | Sprint 15 |
| "Sprint 16 周报（全体）" | 批量 | Sprint 16 |

**输出确认:**
```
操作类型: 单人/批量
目标人员: [列表] 或 [指定人名]
迭代号: Sprint XX 或 "刚过去的迭代"
```

---

### Step 2: 获取项目信息

```bash
mcporter --config ~/.openclaw/workspace/config/mcporter.json call yunxiao.search_projects --organizationId=688c88cc9eda9d4e3ee46203 --output json
```

**处理**: 从返回的 projects 列表中精确匹配 "业财一体化"，提取项目 ID

---

### Step 3: 获取迭代列表

```bash
mcporter --config ~/.openclaw/workspace/config/mcporter.json call yunxiao.list_sprints --organizationId=688c88cc9eda9d4e3ee46203 --id=<项目ID> --output json
```

**处理**: 解析每个迭代的 name, startDate, endDate, id

---

### Step 4: 确定目标迭代

**用户指定**: 直接查找匹配的 sprint.name

**默认（刚过去的迭代）**:
```python
now = Date.now()
buffer_days = 7  # 7天缓冲期

# 找"刚过去的迭代"：满足 endDate < now < endDate + buffer
target = sprints.find(s => s.endDate < now < (s.endDate + buffer_days))

# 找不到则取最后一个结束的迭代
if not target:
    target = sprints.filter(s => s.endDate < now).sort(by=endDate, desc=True)[0]
```

---

### Step 5: 确定下一个迭代

从迭代列表中找到目标迭代之后的一个迭代，用于"下周期计划"

---

### Step 6: 获取用户ID

用户ID映射见 [CONFIG.md](CONFIG.md)，或动态查询：
```bash
mcporter call yunxiao.search_organization_members --organizationId=688c88cc9eda9d4e3ee46203 --query=<用户名>
```

---

### Step 7: 获取工作项

**分别查询 Req（需求）和 Task（任务）**:
```bash
# 需求
mcporter call yunxiao.search_workitems \
  --organizationId=688c88cc9eda9d4e3ee46203 \
  --spaceId=<项目ID> \
  --category=Req \
  --assignedTo=<用户ID> \
  --sprint=<迭代ID> \
  --perPage=100

# 任务
mcporter call yunxiao.search_workitems \
  --organizationId=688c88cc9eda9d4e3ee46203 \
  --spaceId=<项目ID> \
  --category=Task \
  --assignedTo=<用户ID> \
  --sprint=<迭代ID> \
  --perPage=100
```

**关键参数**:
- `organizationId`: 688c88cc9eda9d4e3ee46203
- `category`: "Req" 或 "Task"
- `sprint`: 必须指定迭代ID

---

### Step 8: 获取下一迭代工作项

同 Step 7，使用 `nextSprint.id` 作为 sprint 参数

---

### Step 9: 生成周报

**任务分类**:
| 状态 | 归类 | 完成度 |
|------|------|--------|
| 已完成 | 核心成果 | 100% |
| 进行中/开发中/设计中 | 核心成果 | 30%-90% |
| 其他 | 不显示 | - |

**优先级显示**: 只有"紧急"和"高"才在任务后显示【优先级】

---

### Step 10: 汇总输出

**单人周报**:
```
═══════════════════════════════════════
【林小鹏】周报
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

【林小鹏】
[周报内容]
─────────────────────────────────────
【佘溢钶】
[周报内容]
...

═══════════════════════════════════════
📊 团队统计：已完成 XX | 进行中 XX | 待处理 XX
```

---

## 🚨 错误处理

| 场景 | 处理方式 |
|------|---------|
| 找不到项目 | 报错并停止 |
| 找不到指定迭代 | 报错并列出可用迭代 |
| 工作项查询失败 | 重试3次，仍失败则跳过该用户 |
| 用户ID找不到 | 跳过该用户，继续下一个 |

---

## 🔍 调试模式

启用详细日志查看每步执行情况：
```
[DEBUG] 操作类型: 单人
[DEBUG] 目标人员: 林小鹏
[DEBUG] 迭代号: 默认
[DEBUG] 项目ID: 6891a3395c231c362c0ed181
[DEBUG] 迭代ID: 68b540eb88ec6bebc2d240bb
[DEBUG] 工作项: Req (8条), Task (7条)
```

---

## ✅ 测试用例

| 输入 | 期望结果 |
|------|---------|
| "林小鹏周报" | 生成 Sprint 16（刚过去）的单人周报 |
| "全体人员周报" | 生成6人汇总周报 |
| "Sprint 15周报（佘溢钶）" | 生成 Sprint 15 的单人周报 |
| "Sprint 99周报" | 报错：未找到迭代，列出可用迭代 |
