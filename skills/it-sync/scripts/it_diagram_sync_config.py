# -*- coding: utf-8 -*-
"""
IT 双周会排期图 —— 配置文件（两个生成脚本共用）

说明：
- 项目数据来源于钉钉 AI 表格「IT部门项目面板」，可通过 /it-sync 技能自动更新。
- 三轨道对应 IT 部门三组架构（2026-06-29 起）：业务系统组 / 数据效能组 / 人工智能组。
- 每条轨道「本期是否可承接新需求」请手动修改。
- 修改后运行 generate-it-diagram-html.py 生成配图（推荐），
  或 generate-it-diagram-seedream.py / generate-it-diagram-qwen.py（文生图备选）。
"""

# ---- 本期基本信息（每次双周更新）----
SYNC_ISSUE = 27
SYNC_PERIOD = "2026-08-24 ~ 2026-09-04"
NEXT_SYNC_HINT = "2026-09-14"

CONTACT_HINT = "私我们并在需求收集表做书面提报，咱们拉会沟通，评估后统一排期"

# ---- 轨道一：业务系统组（组负责人）----
TRACK1_LABEL = "业务系统开发"
TRACK1_TEAM = "业务系统组"

TRACK1_INTAKE_LINE = "本期暂不承接大需求，正在跟进小需求"

TRACK1_PROJECTS = """
1. **ERP 完整流程-采购版本** v1.0 — 测试中（进度 100%），计划至 2026-08-24（开发已按期完成，测试收尾中）
2. **ERP 完整流程-仓库库存板块** v1.0 — 设计中（进度 72%），计划至 2026-11-13
3. **ERP 完整流程-出库板块** v1.0 — 设计中（进度 13%），计划至 2027-02-07
4. **ERP 完整流程-财务+BI板块** v1.0 — 未开始，计划至 2027-05-30
""".strip()

# ---- 轨道二：数据效能组（组负责人）----
TRACK2_LABEL = "数据智能开发"
TRACK2_TEAM = "数据效能组"

TRACK2_INTAKE_LINE = "本期暂不承接大需求，正在跟进小需求"

TRACK2_PROJECTS = """
1. **tk 利润报表项目** v1.0 — 测试中（进度 99%），计划至 2026-09-01（数据验证收尾中）
2. **TikTok 内容中台** v1.2 — 设计中（进度 5%），计划至 2026-09-16
3. **科菲康C端推销售出库单** v1.0 — 开发中（进度 15%），计划至 2026-10-16
4. **马帮金蝶一体化** v1.0 — 需求调研中，完成日期待定
5. **银企直连项目** v1.0 — 需求梳理中，完成日期待定
""".strip()

TRACK2_QUEUE = "无"

# ---- 轨道三：人工智能组（组负责人）----
TRACK3_LABEL = "AI 应用开发"
TRACK3_TEAM = "人工智能组"

TRACK3_INTAKE_LINE = "本期暂不承接大需求，正在跟进小需求"

TRACK3_PROJECTS = """
1. **沃尔玛商品库存监控和销量评估系统** v1.2 — 开发中（进度 60%），计划至 2026-09-04
2. **VeryFood 食品AI研发平台（首期闭环 2.0）** v2.0 — 开发中（进度 20%），计划至 2026-12-31
""".strip()

# ---- 背景与原则 ----
BACKGROUND_ONE_LINE = (
    "2025 年 IT 侧重打基础；2026 年起承接更多业务自动化与提效类需求。"
)

POLICY_ONE_LINE = (
    "需求按团队归属排期：业务系统组承接 ERP 相关开发，"
    "数据效能组承接业财一体化与数据看板项目，"
    "人工智能组承接 AI 应用与数据采集类项目。"
    "承接策略以各轨「本期承接说明」为准。"
)


def build_image_prompt_body() -> str:
    """拼进文生图的「业务内容」区块（不含画师指令）。"""
    return f"""
# IT 资源管理与需求排期（双周同步）

## 图上时间怎么画（简单即可）
- 顶部：标题「IT 资源管理与需求排期」+ **第 {SYNC_ISSUE} 期 · {SYNC_PERIOD}**（可加小字「下次同步：{NEXT_SYNC_HINT}」）
- 每个项目旁边标出 **计划至** 的日期（YYYY-MM-DD），与列表一致；待定的写「待定」
- 延期项目用醒目标记

## 背景说明
{BACKGROUND_ONE_LINE}

## 三轨道（按负责团队划分）

### 轨道一：{TRACK1_LABEL}
**负责团队**：{TRACK1_TEAM}
**本期承接说明**：{TRACK1_INTAKE_LINE}

**当前项目**：
{TRACK1_PROJECTS}

### 轨道二：{TRACK2_LABEL}
**负责团队**：{TRACK2_TEAM}
**本期承接说明**：{TRACK2_INTAKE_LINE}

**当前项目**：
{TRACK2_PROJECTS}

### 轨道三：{TRACK3_LABEL}
**负责团队**：{TRACK3_TEAM}
**本期承接说明**：{TRACK3_INTAKE_LINE}

**当前项目**：
{TRACK3_PROJECTS}

---

**排期原则**：{POLICY_ONE_LINE}
""".strip()


def build_sync_notice_text() -> str:
    """发群用的简短通知（与配图同口径）。"""
    if TRACK2_QUEUE and TRACK2_QUEUE.strip() != "无":
        queue_block = f"**排队 / 待确认排期**：{TRACK2_QUEUE}"
    else:
        queue_block = "**排队 / 待确认排期**：无"

    return f"""【IT 排期双周同步 · 第 {SYNC_ISSUE} 期 · {SYNC_PERIOD}】

各位好，双周会已对齐当前排期，**附图**同步整体负载，方便各部门规划提需时间。

**轨道一（{TRACK1_LABEL}）** · 负责团队：{TRACK1_TEAM}
**本期承接**：{TRACK1_INTAKE_LINE}
当前项目：
{TRACK1_PROJECTS}

**轨道二（{TRACK2_LABEL}）** · 负责团队：{TRACK2_TEAM}
**本期承接**：{TRACK2_INTAKE_LINE}
当前项目：
{TRACK2_PROJECTS}

**轨道三（{TRACK3_LABEL}）** · 负责团队：{TRACK3_TEAM}
**本期承接**：{TRACK3_INTAKE_LINE}
当前项目：
{TRACK3_PROJECTS}

{queue_block}

有需求请{CONTACT_HINT}。
*下次同步：{NEXT_SYNC_HINT}*
""".strip()


def build_full_image_prompt() -> str:
    """完整文生图提示词 = 通用画师指令 + 业务内容 + 统一视觉尾缀。"""
    prefix = """你是一位信息图绘图大师。把下方「业务内容」转化为一张用于公司内部同步的横版信息图（16:9）。

## 受众
各部门业务负责人：一眼看清「三条轨各自在做什么、计划完成时间、本期由谁负责、本期是否承接新需求」。

## 工作方式（先理解，再设计）
1) 主干：三轨道对比；每项 = 项目名 + **计划完成时间**（或待定）
2) 每轨需显式呈现：**负责团队**名称 + **本期承接说明**（简短一句）
3) 结构：三栏并列或上下分层，阅读路径清晰
4) 文字克制：标题、轨道名、团队名、承接说明、项目名、状态、日期；禁止长段落
5) 视觉：商务、留白、配色克制（蓝灰 + 一处强调色）

## 绘制规则
- **计划完成时间必须上屏**；顶部要有「第几期 + 双周区间」
- **三轨的「负责团队」「本期承接说明」必须上屏**
- 延期项目用醒目标记（如橙色标签）
- 日期字号清晰可读
- 中文为主；英文术语可保留（如 ERP、TikTok、AI）
- 状态不用 emoji，用小标签/色点即可
- 禁止：夸张机器人、大脑剖面、密集电路板、人脸特写；不要卡通火箭

---

**业务内容**：

"""
    suffix = f"""

---
请输出一张专业、简洁、可读性强的排期看板式信息图：
1) 顶部：主标题 + 第几期 + 双周区间（可选下次同步一行）；
2) 左/上为「{TRACK1_LABEL}」：标明负责团队、本期承接说明、项目列表及各项目计划完成时间；
3) 中为「{TRACK2_LABEL}」：同上；
4) 右/下为「{TRACK3_LABEL}」：同上。"""
    return prefix + build_image_prompt_body() + suffix
