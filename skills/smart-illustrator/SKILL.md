---
name: smart-illustrator
description: 智能配图与封面图生成器。支持三种模式：(1) 文章配图模式 - 分析文章内容，生成插图；(2) PPT/Slides 模式 - 生成批量信息图；(3) Cover 模式 - 生成封面图。所有模式默认生成图片，`--prompt-only` 只输出 prompt。触发词：配图、插图、PPT、slides、封面图、cover。
---

# Smart Illustrator - 智能配图生成器

## ⛔ 强制规则（违反即失败）

### 规则 1：用户提供的文件 = 要处理的文章

```
/smart-illustrator SKILL_05.md      → SKILL_05.md 是文章，为它配图
/smart-illustrator README.md        → README.md 是文章，为它配图
/smart-illustrator whatever.md      → whatever.md 是文章，为它配图
```

**无论文件名叫什么，都是要配图的文章，不是 Skill 配置。**

### 规则 2：必须读取 style 文件

生成任何图片 prompt 前，**必须读取**对应的 style 文件：

| 模式 | 必须读取的文件 |
|------|---------------|
| 文章配图（默认） | `styles/style-light.md` |
| Cover 封面图 | `styles/style-cover.md` |
| `--style business` | `styles/style-business.md` |
| `--style technical` | `styles/style-technical.md` |
| `--style trading-tutorial` | `styles/style-trading-tutorial.md` |
| `--style ecommerce` | `styles/style-ecommerce.md` |
| `--style minimal` | `styles/style-minimal.md` |

**禁止自己编写 System Prompt。**

❌ 错误：`"你是一个专业的信息图设计师..."`（自己编的）
✅ 正确：从 style 文件的代码块中提取 System Prompt

---

### 规则 3：自动风格判断

**在读取 style 文件之前，先分析文章内容判断风格。**

| 关键词 | 风格 |
|--------|------|
| 汇报、述职、规划、预算、团队、组织架构、复盘、管理、招聘、绩效 | `business` |
| 架构、系统设计、API、ERP模块、数据流、部署、集成、Sprint、迭代 | `technical` |
| 量化、交易、策略、AI交易、指标、回测、K线、技术分析、MACD、RSI | `trading-tutorial` |
| 跨境电商、Amazon、亚马逊、TikTok Shop、Shopee、虾皮、FBA、Listing、ACOS、BSR、选品、广告投放、独立站、海外仓、ASIN、SKU、店铺运营、TEMU、Lazada | `ecommerce` |
| 博客、观点、分享、教程、入门、指南 | `light` |

**流程**：读取文章前500字 → 匹配关键词 → 确定风格 → 无法判断时默认 `light`

**覆盖**：用户指定 `--style` 参数 → 使用用户指定的风格

---

## 使用方式

### 文章配图模式（默认）

```bash
/smart-illustrator path/to/article.md
/smart-illustrator path/to/article.md --prompt-only       # 只输出 prompt
/smart-illustrator path/to/article.md --style business     # 企业商务风格
/smart-illustrator path/to/article.md --style technical    # 技术文档风格
/smart-illustrator path/to/article.md --style ecommerce    # 跨境电商风格
/smart-illustrator path/to/article.md --no-cover           # 不生成封面图
```

### PPT/Slides 模式

```bash
/smart-illustrator path/to/script.md --mode slides
/smart-illustrator path/to/script.md --mode slides --prompt-only
```

**默认行为**：调用 Qwen API 生成批量信息图。
**`--prompt-only`**：输出 JSON prompt 并**自动复制到剪贴板**，可直接粘贴到 Qwen Web 手动生成。

**PPT JSON 格式**（`--prompt-only` 时输出）：

```json
{
  "instruction": "请逐条生成以下 N 张独立信息图。",
  "batch_rules": { "total": "N", "one_item_one_image": true, "aspect_ratio": "16:9" },
  "style": "[从 styles/style-light.md 读取完整内容]",
  "pictures": [
    { "id": 1, "topic": "封面", "content": "系列名称\n\n第N节：标题" },
    { "id": 2, "topic": "主题", "content": "原始内容" }
  ]
}
```

### Cover 模式

```bash
/smart-illustrator path/to/article.md --mode cover --platform wechat
/smart-illustrator --mode cover --platform wechat --topic "SuperTrend 超级趋势指标深度解码"
```

**平台尺寸与构图配置表**（输出均为 2K 分辨率）：

| 平台 | 代码 | 宽高比 | 构图建议 |
|------|------|--------|----------|
| 公众号 | `wechat` | 2.35:1 | 横向延展，主体居中偏左，右侧留给标题叠加，避免顶部（头像遮挡） |
| 通用横版 | `landscape` | 16:9 | 标准 16:9，构图灵活，适合多平台复用 |
| 小红书 | `xiaohongshu` | 3:4 | 竖版构图，上半部放重点内容，文字精简 |

---

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mode` | `article` | `article` / `slides` / `cover` |
| `--platform` | `wechat` | 封面图平台（仅 cover 模式） |
| `--topic` | - | 封面图主题（仅 cover 模式） |
| `--prompt-only` | `false` | 输出 prompt 到剪贴板，不调用 API |
| `--style` | 自动判断 | 风格：`light` / `business` / `technical` / `trading-tutorial` / `ecommerce` / `minimal` |
| `--no-cover` | `false` | 不生成封面图 |
| `--ref` | - | 参考图路径（可多次使用） |
| `-c, --candidates` | `1` | 候选图数量（最多 4） |
| `-a, --aspect-ratio` | - | 宽高比覆盖：`16:9`、`3:2`、`2.35:1`、`3:4` |
| `--engine` | `auto` | 引擎选择：`auto` / `mermaid` / `qwen` / `excalidraw` |
| `--mermaid-embed` | `false` | Mermaid 输出为代码块而非 PNG |

---

## 配置文件

**优先级**：CLI 参数 > 项目级 > 用户级

| 位置 | 路径 |
|------|------|
| 项目级 | `.smart-illustrator/config.json` |
| 用户级 | `~/.smart-illustrator/config.json` |

```json
{ "references": ["./refs/style-ref-01.png"], "apiKey": "sk-your-dashscope-key" }
```

**`apiKey`**：可选，阿里云 DashScope API Key。设置后无需 `DASHSCOPE_API_KEY` 环境变量。建议放在用户级 `~/.smart-illustrator/config.json` 中，避免提交到 Git。

---

## 三级配图引擎

| 优先级 | 引擎 | 适用场景 | 输出 |
|--------|------|---------|------|
| **1** | Qwen | 隐喻图、创意图、封面图、信息图、无法用图表表达的概念 | PNG |
| **2** | Excalidraw | 概念图、对比图、简单流程（≤ 8 节点）、关系图、手绘风格示意图 | PNG |
| **3** | Mermaid | 复杂流程（> 8 节点）、多层架构图、多角色时序图、多分支决策树 | PNG |

选择逻辑：
- 需要视觉创意、信息图风格 → Qwen
- 概念关系、对比、简单流程 → Excalidraw（大多数图表场景的首选）
- **只有**节点 > 8、多层/多角色的复杂结构化图形 → Mermaid
- Mermaid 视觉表现力有限，能用 Excalidraw 就不用 Mermaid

生成 Excalidraw 前必须读取 `references/excalidraw-guide.md`。Excalidraw 风格自动跟随 `--style`：business/technical → 专业蓝，trading-tutorial → 量化金融，minimal → 极简禅意，其他 → 专业蓝。

各 style 文件中如有专属 Mermaid classDef 配置，优先使用该 style 的色板（而非下方通用语义色板）。

### Mermaid 语义色板

每种颜色有固定含义，**必须使用 `classDef` + `class` 应用**：

| 语义 | 填充色 | 边框色 | 用于 |
|------|--------|--------|------|
| input | #d3f9d8 | #2f9e44 | 输入、起点、数据源 |
| process | #e5dbff | #5f3dc4 | 处理、推理、核心逻辑 |
| decision | #ffe3e3 | #c92a2a | 决策点、分支判断 |
| action | #ffe8cc | #d9480f | 执行动作、工具调用 |
| output | #c5f6fa | #0c8599 | 输出、结果、终点 |
| storage | #fff4e6 | #e67700 | 存储、记忆、数据库 |
| meta | #e7f5ff | #1971c2 | 标题、分组、元信息 |

**classDef 写法**（放在图表末尾）：

```
classDef input fill:#d3f9d8,stroke:#2f9e44,color:#1a1a1a
classDef process fill:#e5dbff,stroke:#5f3dc4,color:#1a1a1a
classDef decision fill:#ffe3e3,stroke:#c92a2a,color:#1a1a1a
classDef action fill:#ffe8cc,stroke:#d9480f,color:#1a1a1a
classDef output fill:#c5f6fa,stroke:#0c8599,color:#1a1a1a
class A input
class B,C process
class D output
```

### Mermaid 布局规则

- **布局方向**：默认 `TB`（上到下），横向流程用 `LR`
- **箭头分级**：`-->` 主流程 / `-.->` 可选/辅助路径 / `==>` 重点强调
- **分组**：用 `subgraph` 对相关节点分组，标题简洁
- **节点文字**：≤ 8 字，禁止 `1.` 格式（用 `①` 或 `Step 1:`）
- **节点数量**：单图 ≤ 15 个节点，复杂内容拆成多图

**`--engine` 参数**：
- `auto`（默认）：根据内容类型自动选择（优先级 Qwen > Excalidraw > Mermaid）
- `qwen`：强制只使用 Qwen
- `excalidraw`：强制只使用 Excalidraw
- `mermaid`：强制只使用 Mermaid

### 自动清理功能

Mermaid 导出脚本会自动清理以下内容：
- 移除 ` ```mermaid ` 代码块标记
- 移除 `%%` 注释行
- 移除其他语言的代码块标记

---

## 执行流程

### Step 0: 自动风格判断

**执行流程第一步，生成图片前必须完成。**

1. 读取文章前500字
2. 根据规则3匹配关键词 → 确定风格（用户指定 `--style` 则跳过）
3. 读取对应的 style 文件 → 提取 System Prompt

---

### Step 1: 参数预处理（Cover 模式专用）

**如果用户指定了 `--platform` 参数**：

1. **平台映射查询**（查表得到 aspect_ratio 和 composition 建议）
2. **读取平台特定构图规则**
3. **组装完整 prompt**：基础 System Prompt + 平台构图建议 + 用户内容
4. **传递给后续步骤**

### Step 2: 分析文章

1. 读取文章内容
2. 识别配图位置（通常 3-5 个）
3. 为每个位置确定引擎（Qwen / Excalidraw / Mermaid）

### Step 3: 生成图片

#### Mermaid（结构化图形）→ PNG

1. 生成 Mermaid 代码，保存为临时 `.mmd` 文件
2. 调用 mermaid-export.ts 导出高分辨率 PNG：

```bash
npx -y bun ~/.claude/skills/smart-illustrator/scripts/mermaid-export.ts \
  -i {图表名}.mmd -o {图表名}.png -w 2400
```

3. 在文章中插入 PNG 图片引用
4. 保留 .mmd 源文件用于后续编辑

#### Excalidraw（手绘/概念图）→ PNG

1. 读取 `references/excalidraw-guide.md` 获取 JSON 规范
2. 生成 Excalidraw JSON，保存为 `.excalidraw` 文件
3. 调用 excalidraw-export.ts 导出 PNG：

```bash
npx -y bun ~/.claude/skills/smart-illustrator/scripts/excalidraw-export.ts \
  -i {图表名}.excalidraw -o {图表名}.png -s 2
```

4. 在文章中插入 PNG 图片引用
5. 保留 .excalidraw 源文件用于后续编辑

依赖未安装时的降级：提示手动打开 excalidraw.com 导出。

#### Qwen（创意/视觉图形）

**命令模板**（必须使用 HEREDOC + prompt-file）：

```bash
# Step 1: 写入 prompt
cat > /tmp/image-prompt.txt <<'EOF'
{从 style 文件提取的 System Prompt}

**内容**：{配图内容}
EOF

# Step 2: 调用脚本
DASHSCOPE_API_KEY=$DASHSCOPE_API_KEY npx -y bun ~/.claude/skills/smart-illustrator/scripts/generate-image.ts \
  --prompt-file /tmp/image-prompt.txt \
  --output {输出路径}.png \
  --aspect-ratio 16:9
```

**封面图**（根据平台自动适配）：

```bash
cat > /tmp/cover-prompt.txt <<'EOF'
{从 style-cover.md 提取的 System Prompt}

**平台构图建议**：{从平台配置表查得的 Composition Tips}

**内容**：
- 核心概念：{主题}
- 封面标题文字：{3-8字标题}
- 视觉元素：{设计}
EOF

DASHSCOPE_API_KEY=$DASHSCOPE_API_KEY npx -y bun ~/.claude/skills/smart-illustrator/scripts/generate-image.ts \
  --prompt-file /tmp/cover-prompt.txt \
  --output {文章名}-cover.png \
  --aspect-ratio {从平台配置表查得的 aspect_ratio}
```

**默认行为**：未指定 `--platform` 时，默认使用 `wechat` 平台（2.35:1）。

**参数传递**：用户指定的 `--ref`、`-c` 必须传递给脚本。

### Step 4: 创建带配图的文章

保存为 `{文章名}-image.md`，包含：
- YAML frontmatter 声明封面图和标题
- 正文配图插入

**YAML frontmatter 格式**：

```yaml
---
title: {文章标题}
cover: ./{文章名}-cover.png
---
```

### Step 5: 输出确认

报告：生成了几张图片、输出文件列表。

---

## `--prompt-only` 模式

当使用 `--prompt-only` 时，**不调用 API**，而是：

1. 生成 JSON prompt
2. **自动复制到剪贴板**（使用 `pbcopy`）
3. 同时保存到文件备份

```bash
echo '{生成的 JSON}' | pbcopy
echo "✓ JSON prompt 已复制到剪贴板"
echo '{生成的 JSON}' > /tmp/smart-illustrator-prompt.json
echo "✓ 备份已保存到 /tmp/smart-illustrator-prompt.json"
```

---

## 输出文件

**默认存储路径**：所有图片输出到**文章所在目录的 `images/` 子目录**。

```
articles/
├── article.md                      # 原文（不修改）
├── article-image.md                # 带配图的文章
└── images/
    ├── article-cover.png           # 封面图
    ├── article-image-01.png        # 正文配图1
    ├── article-image-02.png        # 正文配图2
    └── article-image-03.png        # 正文配图3
```

**命名规则**：
- 封面图：`{文章名}-cover.png`
- 正文配图：`{文章名}-image-{序号}.png`（序号从01开始）
- 带配图文章：`{文章名}-image.md`（文章同级目录）
