# Style: Cover / 封面图风格

用于公众号文章封面、课程宣传图等场景的封面图风格。

> **默认色板**：`brand-colors.md` → **Cover Dark / 封面深色**

> **设计哲学**：封面图是文章在信息流中的「门面」。需要在极短时间内让读者理解主题并产生点击欲望。视觉冲击力 + 主题清晰度并重。

## 适用场景

- 公众号文章封面
- 课程/产品宣传图
- 知识星球/社交媒体配图

---

## 平台尺寸预设

| 平台 | 代码 | 尺寸 | 比例 |
|------|------|------|------|
| 公众号 | `wechat` | 900×383 | 2.35:1 |
| 通用横版 | `landscape` | 1920×1080 | 16:9 |
| 小红书 | `xiaohongshu` | 1080×1440 | 3:4 |

---

## Qwen System Prompt

> **重要**：最终发送给图像生成模型的 prompt 建议使用**英文**（生成效果更好）。中文用于构思和讨论，英文用于最终生成指令。

```
You are a professional cover image designer for WeChat Official Account articles. Your goal: create visually striking cover images that clearly communicate the article's theme and attract clicks in information feeds.

Core principle: The cover must convey the topic within 2 seconds. It should work as both a visual hook AND an information carrier.

---

DESIGN RULES:

1. TEXT IS ALLOWED AND ENCOURAGED — Cover images should include a short, impactful title (3-8 Chinese characters or equivalent). The title should be the article's core hook.

2. CLEAR VISUAL METAPHOR — Use one strong visual element that relates to the topic. Don't be too abstract — readers scrolling through feeds need instant recognition.

3. HIGH CONTRAST — Dark background with bright elements, or light background with bold colored elements. Ensure readability at small sizes (mobile phone feeds).

4. SINGLE FOCAL POINT — One visual center that draws the eye. Other elements support the focal point.

5. NO CLICHÉ TECH SYMBOLS — Avoid: robotic arms, brain circuits, generic gears, rockets, shields. Use fresh metaphors relevant to the specific topic.

---

VISUAL EXECUTION:

Space: Clean composition with strong contrast. Background can be dark (#0F172A deep navy) or gradient. Subject and text occupy 50-70% of the frame.

Materials: Mix of flat design elements with subtle depth. Icons, geometric shapes, simplified illustrations. Light glassmorphism effects are OK for cards/panels.

Color Palette:
- Background: Deep Indigo #0F172A (primary) or gradient from #0F172A to #1E3A5F
- Primary accent: Tech Blue #3B82F6 — main visual elements, glow effects
- Secondary accent: Warm Amber #F59E0B — highlights, emphasis points
- Text: Pure White #FFFFFF for main title, Light Slate #94A3B8 for subtitle

Typography:
- Main title: Bold, large, sans-serif, white. 3-8 characters. Must be readable at 200px width.
- Subtitle (optional): Lighter weight, smaller, secondary color. Provides context.
- Text placement: Center or left-aligned. Avoid edges (platform cropping).

Composition:
- **Center-focused**: Visual element in center, title overlaid or adjacent
- **Left-right split**: Visual on one side, title on the other
- Core content stays within the central 71% height zone (safe area for multi-platform cropping)

Output: High contrast, clear focal point, readable title, professional quality.

No watermarks, no logos.
```

---

## 构图模式

### A) 中心标题型
- 视觉元素作为背景/底图
- 标题居中叠加
- 适合：概念性文章、系列文章

### B) 左图右文型
- 左侧放视觉隐喻，右侧放标题和副标题
- 适合：教程类、技术分析类

### C) 上图下文型
- 上方视觉元素，下方标题栏
- 适合：产品介绍、功能展示

---

## 封面文字设计

### 字数控制

| 平台 | 建议字数 | 原因 |
|------|----------|------|
| 公众号 | 5-10 个字 | 封面在信息流中显示较小 |
| 通用横版 | 3-8 个字 | 标题需要一眼抓住 |

### 文字规则
- **主标题**：3-8 字，粗体，白色，大号
- **副标题**（可选）：一句话补充说明，较小字号
- 文字描边或加半透明底色增强可读性
- 避免四角区域（平台可能裁切）

---

## 视觉隐喻设计方法

**优先用具象、可识别的元素表达主题，而非纯抽象图形。**

### 量化交易类封面

| 概念 | 推荐隐喻 |
|------|----------|
| K线/技术指标 | 简化的 K 线走势 + 指标曲线 |
| AI 分析 | 图表 + 数据面板 + 分析标注 |
| 策略开发 | 代码片段 + 图表叠加 |
| 回测优化 | 收益曲线 + 对比图 |
| 信号识别 | K 线 + 标记箭头 + 指标面板 |

### IT 管理/技术类封面

| 概念 | 推荐隐喻 |
|------|----------|
| 系统架构 | 简化的架构图/连接节点 |
| 团队管理 | 人物图标 + 连接/组织结构 |
| 项目规划 | 时间轴 + 里程碑标记 |
| 数据分析 | 仪表盘 + 图表组合 |
| AI/自动化 | 流程节点 + 智能标记 |

### 跨境电商类封面

**色彩提示**：可根据文章涉及的平台，将平台品牌色融入封面主色调。多平台文章用深色背景 + 多色光效点缀。

| 概念 | 推荐隐喻 |
|------|----------|
| Amazon 运营 | 简化的 Amazon 搜索栏 + 产品卡片排列 + 橙色(#FF9900)光效 |
| TikTok Shop | 短视频播放界面 + 购物车弹窗 + 红青(#FF0050/#00F2EA)双色光效 |
| Shopee 运营 | 移动端商城界面 + Flash Sale 倒计时元素 + 橙红(#EE4D2D)光效 |
| 多平台布局 | 多个平台卡片(带品牌色标识)以网格/环形排列 + 中心连接节点 |
| 选品策略 | 商品卡片 + 数据图表(趋势线/排名) + 放大镜/筛选漏斗 |
| 广告投放 | 漏斗图(曝光→转化) + 数据仪表盘 + 增长曲线 |
| FBA/物流 | 简化的地图路线 + 仓库图标 + 包裹/货柜 + 物流青(#0891B2)色调 |
| 业财一体化 | 平台订单 → ERP 数据流 → 财务报表，三段式连接 |
| 爆款打造 | 产品居中放大 + 上升趋势线 + 星标/排名徽章 |
| 市场分析 | 世界地图轮廓 + 各区域市场数据标注 + 连接线 |

---

## 安全区域

- **多平台兼容**：核心视觉内容控制在画面中央 71% 高度区域内
- 上下留出的背景区域不放重要内容
- 文字避开四角（平台头像、标签可能遮挡）

---

## Prompt 模板

先用中文确定主题和隐喻，然后组装英文 prompt：

```
[Insert System Prompt above]

---

**Title text on image**: "[封面标题，3-8字]"
**Subtitle** (optional): "[副标题]"

**Visual concept**: [描述视觉元素、隐喻、布局]

**Composition**: [center-focused / left-right split / top-bottom split]

Aspect ratio [2.35:1 / 16:9 / 3:4]. High contrast, clear focal point, readable title text, professional quality.
```

---

## 使用示例

### 示例 1：量化交易文章封面

**主题**：以AI量化为生：SuperTrend 超级趋势指标深度解码

**Prompt**：
```
[System Prompt]

Title text on image: "SuperTrend 深度解码"
Subtitle: "量化指标解码系列"

Visual concept: A simplified candlestick chart with a glowing blue SuperTrend line weaving through it. The trend line changes color at key reversal points. Clean dark navy background with subtle grid. The chart elements are semi-transparent with depth.

Composition: Left-right split — chart visual on left 60%, title text on right 40%.

Aspect ratio 2.35:1. High contrast, clear focal point, readable title text.
```

### 示例 2：IT 管理文章封面

**主题**：ERP 1.0 研发实施路径与迭代规划方案

**Prompt**：
```
[System Prompt]

Title text on image: "ERP 研发路线图"
Subtitle: "从规划到落地的实施路径"

Visual concept: A horizontal timeline/roadmap with milestone markers (amber dots) and sprint blocks. Connected by flowing blue lines. Key modules shown as rounded rectangle cards along the path. Clean, professional, architectural feel.

Composition: Center-focused — roadmap spans the width, title overlaid at top.

Aspect ratio 2.35:1. High contrast, professional quality.
```

### 示例 3：跨境电商文章封面

**主题**：2026 亚马逊广告投放策略：ACOS 从 30% 降到 15% 的实战方法

**Prompt**：
```
[System Prompt]

Title text on image: "Amazon 广告实战"
Subtitle: "ACOS 优化全攻略"

Visual concept: Dark navy background. Left side: a simplified Amazon-style search bar with product listing cards stacked below, rendered in warm orange (#FF9900) glow lines on dark background. Right side: a descending ACOS curve (from 30% to 15%) with key data points highlighted in amber. A subtle funnel shape connects impressions to conversions. Clean, data-driven, professional.

Composition: Left-right split — product/platform visual on left 50%, data trend + title on right 50%.

Aspect ratio 2.35:1. High contrast, clear focal point, readable title text.
```

### 示例 4：多平台跨境电商封面

**主题**：全渠道布局：Amazon + TikTok Shop + Shopee 三大平台运营全攻略

**Prompt**：
```
[System Prompt]

Title text on image: "三大平台全攻略"
Subtitle: "Amazon · TikTok · Shopee"

Visual concept: Dark navy background. Three stylized platform cards arranged in a triangular layout at center, each with its signature color glow: left card in orange (#FF9900) representing Amazon, top-right card in pink-red (#FF0050) with cyan (#00F2EA) accent representing TikTok, bottom-right card in orange-red (#EE4D2D) representing Shopee. Connecting lines between cards form a network. Subtle world map outline in background suggesting global reach.

Composition: Center-focused — three platform cards at center, title overlaid at bottom.

Aspect ratio 2.35:1. High contrast, vibrant but professional.
```
