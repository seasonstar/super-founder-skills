---
name: it-sync
description: >
  IT双周汇报与同步技能。自动从钉钉AI表格拉取项目数据，更新排期图配置，生成群通知文案和信息图。
  触发场景：(1) 用户说"IT同步"、"IT汇报"、"双周排期"、"排期图"、"更新排期"、"生成排期图"；
  (2) 用户输入 /it-sync；(3) 用户要求更新或发送IT排期同步信息。
---

# IT 双周汇报与同步

## 工作流程

### Step 1：拉取钉钉数据

使用 `dingtalk-ai-table` 技能查询「项目整体进度」表：

```bash
mcporter call dingtalk-ai-table query_records \
  --args '{"baseId":"pYLaezmVNe1Ql0r1Tkax5x1GWrMqPxX6","tableId":"2vegybbg9tgmaki5ie3sh","limit":50}' \
  --output json
```

字段映射详见 [references/dingtalk-schema.md](references/dingtalk-schema.md)。

### Step 2：云效 Sprint 交叉验证

调用 `yunxiao-weekly-report` 技能获取当前 Sprint 的实际时间排期，用于验证钉钉表格中的项目状态和日期：

```bash
python3 /Users/mac/.claude/skills/yunxiao-weekly-report/scripts/yunxiao-weekly-report.py \
  --sprint "Sprint XX" --no-notify --dry-run
```

**验证要点**：
- Sprint 起止日期是否与本期双周区间匹配
- 各成员当前 Sprint 的任务状态是否与钉钉表格项目进度一致
- 是否有未录入钉钉表格的新任务或已完成任务
- 如发现不一致，向用户提示差异并建议修正

### Step 3：整理数据

1. **过滤**：仅保留「当前阶段」不是「已完工」的项目
2. **分组**：按「项目组」分为两组
   - **业务系统组** → 轨道一（业务系统开发）
   - **数据效能组** → 轨道二（数据智能开发）
3. **排序**：延期项目优先 → 按计划结束日期升序
4. **格式化**每条项目一行：`N. **项目名称** — 当前阶段（进度 XX%），计划至 YYYY-MM-DD（延期原因摘要）`
   - 无进度数据时省略百分比；无结束日期时写「完成日期待定」
5. **交叉验证**：结合 Step 2 的云效数据，补充或修正项目状态

### Step 4：确认期数信息

向用户确认（括号内为自动建议值）：

- **期数**：当前 config `SYNC_ISSUE` + 1
- **双周区间**：上期结束日 +1 ~ +14 天（参考云效 Sprint 实际日期）
- **下次同步日期**：本期结束日 +3 个工作日
- **各轨承接说明**：默认沿用上期，用户可修改

确认后更新 `05-AI与自动化/it_diagram_sync_config.py`。

### Step 5：生成群通知文案并归档

更新 config 后运行验证并输出通知文案：

```bash
cd 05-AI与自动化 && python3 -c "from it_diagram_sync_config import build_sync_notice_text; print(build_sync_notice_text())"
```

展示给用户确认后，**将文案归档到 `01-团队运营/IT双周汇报/` 目录**：

- **命名规则**：`Sprint {N}.md`，N 取当前云效 Sprint 编号
  - 例：`Sprint 22.md`
- **内容**：`build_sync_notice_text()` 输出的完整文案
- 确认后自动写入，无需用户额外操作

### Step 6：生成排期信息图

询问用户选择图片生成方式：

- **Seedream**（豆包）：`cd 05-AI与自动化 && python3 generate-it-diagram-seedream.py`
- **Qwen**（通义千问）：`cd 05-AI与自动化 && python3 generate-it-diagram-qwen.py`

### Step 7：输出交付物

最终交付：

1. **群通知文案**：可直接复制发送到「IT业务信息同步群」
2. **排期信息图**：PNG 文件，与文案一起发送
3. **发送提示**：提醒用户将文案和图片一起发到群内

## 脚本与文件

脚本原始副本保存在技能目录 [scripts/](scripts/) 下，运行时同步到项目目录 `05-AI与自动化/`。

| 技能目录（原始副本） | 项目目录（运行位置） | 用途 |
|----------------------|---------------------|------|
| `scripts/it_diagram_sync_config.py` | `05-AI与自动化/it_diagram_sync_config.py` | 配置文件（期数、项目列表、通知模板） |
| `scripts/generate-it-diagram-seedream.py` | `05-AI与自动化/generate-it-diagram-seedream.py` | 豆包 Seedream 文生图 |
| `scripts/generate-it-diagram-qwen.py` | `05-AI与自动化/generate-it-diagram-qwen.py` | 通义千问文生图 |

**同步规则**：每次执行技能时，先检查项目目录是否存在这三个脚本，若缺失则从技能目录 `scripts/` 复制过去。

## 钉钉表格定位

- **Base**：IT部门项目面板（`pYLaezmVNe1Ql0r1Tkax5x1GWrMqPxX6`）
- **主表**：项目整体进度（`2vegybbg9tgmaki5ie3sh`，14 个字段）
