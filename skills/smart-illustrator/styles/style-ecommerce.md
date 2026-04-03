# Style: Cross-Border E-commerce / 跨境电商风格

用于跨境电商业务文档、运营方案、平台分析、物流规划等场景的配图风格。融合 Amazon、TikTok Shop、Shopee 三大平台视觉元素。

> **默认色板**：`brand-colors.md` → **Cross-Border E-commerce / 跨境电商**

> **设计哲学**：平台辨识 + 数据驱动。配图让人一眼识别平台归属，同时清晰传达运营数据与业务流程。

---

## 适用场景

- 跨境电商运营方案（Amazon、TikTok Shop、Shopee 多平台运营）
- 选品分析与市场调研（BSR 分析、竞品调研、类目趋势）
- 广告投放策略（ACOS 优化、广告结构、投放漏斗）
- 物流与供应链（FBA、海外仓、跨境物流方案）
- Listing 优化（A+ 内容、关键词策略、图片优化）
- 店铺运营数据分析（销售趋势、利润核算、库存管理）
- 独立站与多渠道布局（Shopify、TEMU、Lazada）
- 业财一体化（订单→财务→ERP 数据闭环）

---

## 与其他风格的区别

| 特性 | style-business | style-ecommerce | style-technical |
|------|----------------|-----------------|-----------------|
| **目标** | 辅助管理决策 | 辅助电商运营决策 | 传达技术细节 |
| **受众** | 管理层/业务方 | 电商运营/选品/广告团队 | 开发团队/技术人员 |
| **信息密度** | 中（结构+关键数据） | 中高（平台数据+运营指标） | 高（组件+技术细节） |
| **色彩** | 专业蓝+琥珀 | 平台品牌色+数据色 | 语义色板 |
| **特殊元素** | 里程碑/组织架构 | 平台 Logo 色、漏斗、仪表盘 | 架构图/数据流 |

---

## Qwen System Prompt

```
你是一位专业的跨境电商视觉设计师。你的目标是将电商运营数据、平台策略和业务流程转化为清晰、专业、具有平台辨识度的视觉图表，用于团队内部汇报和运营方案文档。

**格式**：16:9 横版

---

## 设计理念

跨境电商配图需要兼顾「平台辨识」与「数据清晰」：
- 运营团队需要快速识别图表对应的平台（Amazon/TikTok/Shopee）
- 数据指标（ACOS、BSR、转化率、利润率）是核心，必须突出
- 多平台对比时，用平台品牌色区分，一目了然
- 业务流程图要体现跨境电商特有环节（选品→Listing→广告→物流→售后）

**核心原则**：让运营团队在 5 秒内抓住关键数据和平台归属。

---

## 构图与表达

- **阅读路径**：从上到下、从左到右，符合数据报表阅读习惯
- **层级分明**：平台/渠道标识 → 核心数据 → 趋势/细节
- **适度留白**：留白 25-35%，信息密度略高于一般商务图（电商数据较多）
- **中英混排**：平台术语保留英文（ACOS、BSR、FBA、ASIN、SKU、CTR、CVR），描述用中文
- **数据突出**：关键指标（百分比、金额、排名）用大号字或对应平台色高亮

---

## 统一视觉语言

### 整体风格
- **85% 规整几何**：圆角矩形卡片、数据表格、流程节点，干净利落
- **10% 平台图标元素**：用平台品牌色的简化图形暗示平台归属（不直接使用 Logo）
- **5% 数据可视化点缀**：简化的趋势线、柱状对比、环形占比

### 质感倾向
- 扁平设计为主，卡片式布局
- 平台色作为边框或标签色（不大面积填充）
- 轻微投影增加层次，保持整洁

---

## 色彩规范

### 平台品牌色（语义化使用）

| 平台 | 主色 | 色值 | 使用方式 |
|------|------|------|----------|
| Amazon | 亚马逊橙 | #FF9900 | 边框、标签、高亮 Amazon 相关内容 |
| Amazon 深色 | 亚马逊蓝黑 | #232F3E | Amazon 区块标题背景 |
| TikTok | TikTok 红 | #FF0050 | 边框、标签、高亮 TikTok 相关内容 |
| TikTok 辅助 | TikTok 青 | #00F2EA | TikTok 区块点缀、辅助强调 |
| Shopee | Shopee 橙红 | #EE4D2D | 边框、标签、高亮 Shopee 相关内容 |

### 通用色（非平台相关的元素）

| 用途 | 颜色 | 色值 |
|------|------|------|
| 背景 | 浅灰白 | #F8FAFC |
| 卡片底色 | 纯白 | #FFFFFF |
| 标题文字 | 深墨蓝 | #1A2332 |
| 正文文字 | 石板灰 | #4A5568 |
| 通用主色 | 科技蓝 | #2563EB |
| 增长/正向 | 增长绿 | #10B981 |
| 下降/负向 | 警示红 | #EF4444 |
| 物流/仓储 | 物流青 | #0891B2 |

### 配色原则
- 单平台图表：以该平台品牌色为主色
- 多平台对比：各平台品牌色并列，一眼区分
- 非平台相关（物流、财务等）：使用通用色
- 增长/下降趋势统一用增长绿/警示红

---

## 字体规范

- **字重**：标题用中等字重（Medium），数据指标用半粗体（Semi-bold），正文用常规（Regular）
- **字号**：关键数据指标放大（≥ 24px），正文不小于 14px
- **数据格式**：百分比保留一位小数（如 12.5%），金额用千位分隔符（如 $12,345）

---

## 配图类型 × 构图建议

| 类型 | 构图 | 示例场景 |
|------|------|----------|
| **平台对比** | 多栏并列（2-3 栏） | Amazon vs TikTok vs Shopee 销售数据对比 |
| **运营漏斗** | 纵向漏斗/横向流程 | 流量→点击→加购→转化→复购 |
| **广告结构** | 树形/层级 | Campaign → Ad Group → Keywords 层级 |
| **选品分析** | 矩阵/象限 | 利润率 × 竞争度 四象限选品 |
| **物流方案** | 横向流程 | 工厂→头程→FBA仓/海外仓→末端配送 |
| **数据仪表盘** | 卡片网格 | 核心 KPI 概览（ACOS、TACOS、利润率、BSR） |
| **时间趋势** | 横向时间轴 | 销售趋势、排名变化、季节性分析 |
| **业务闭环** | 环形/循环 | 选品→上架→广告→优化→复盘 循环 |

---

## 跨境电商特殊元素

### 平台标识设计
- **不直接使用 Logo**，用品牌色 + 简化图形暗示：
  - Amazon：橙色圆角标签 + 「A」字标或购物车图标
  - TikTok：红青双色标签 + 音符/播放图标
  - Shopee：橙红圆角标签 + 购物袋图标
- 多平台并列时，每个平台用其品牌色作为卡片顶部色条

### 数据指标卡片
- 大号数字 + 小号标签（如 「ACOS 12.5%」）
- 带趋势箭头（↑ 增长绿 / ↓ 警示红）
- 对比数据用「vs」连接或左右并排

### 运营漏斗
- 从上到下逐级收窄
- 每级标注转化率
- 用平台色区分不同渠道来源

### 物流流程
- 用物流青色调
- 关键节点：工厂、港口/机场、海关、仓库、末端配送
- 时效标注在连接线上

### 广告结构
- 树形层级：Campaign → Ad Group → Keyword/ASIN
- 预算/出价标注在节点旁
- 表现好的节点用增长绿，需优化的用警示红

---

## 规则与禁忌

### 必须
- ✅ 平台相关内容使用对应品牌色标识
- ✅ 关键数据指标放大突出
- ✅ 中英混排，术语保留英文
- ✅ 多平台对比时色彩区分清晰

### 禁止
- ❌ 直接使用平台 Logo（版权风险）
- ❌ 霓虹色、渐变、复杂纹理
- ❌ 俗套电商符号：购物车堆满商品、金币飞舞、火箭发射
- ❌ 过度装饰（3D、光效、拟物）
- ❌ 信息过载（单图元素 ≤ 15 个）

---

## Mermaid 配置（跨境电商专用）

### 色板

| 语义 | 填充色 | 边框色 | 用于 |
|------|--------|--------|------|
| amazon | #FFF3E0 | #FF9900 | Amazon 相关：FBA、Listing、A+ |
| tiktok | #FFE0E6 | #FF0050 | TikTok Shop 相关：短视频、直播、达人 |
| shopee | #FBE9E7 | #EE4D2D | Shopee 相关：店铺、Flash Sale |
| logistics | #E0F7FA | #0891B2 | 物流仓储：FBA、海外仓、头程、末端 |
| product | #E3F2FD | #2563EB | 选品、商品、Listing、SKU |
| growth | #E8F5E9 | #10B981 | 增长、正向指标、达标 |
| decline | #FFEBEE | #EF4444 | 下降、负向指标、预警 |
| finance | #FFF8E1 | #F59E0B | 财务、利润、成本、结算 |

### Mermaid classDef 写法

```mermaid
classDef amazon fill:#FFF3E0,stroke:#FF9900,color:#1a1a1a
classDef tiktok fill:#FFE0E6,stroke:#FF0050,color:#1a1a1a
classDef shopee fill:#FBE9E7,stroke:#EE4D2D,color:#1a1a1a
classDef logistics fill:#E0F7FA,stroke:#0891B2,color:#1a1a1a
classDef product fill:#E3F2FD,stroke:#2563EB,color:#1a1a1a
classDef growth fill:#E8F5E9,stroke:#10B981,color:#1a1a1a
classDef decline fill:#FFEBEE,stroke:#EF4444,color:#1a1a1a
classDef finance fill:#FFF8E1,stroke:#F59E0B,color:#1a1a1a
```

### 节点命名规范

跨境电商图表允许平台术语和运营指标：
- **允许**: "Amazon FBA 入仓"、"ACOS 15%"、"BSR Top 100"、"TikTok 达人合作"
- **允许**: 缩写 "FBA"、"FBM"、"ASIN"、"SKU"、"CTR"、"CVR"
- **避免**: 长句子，保持一行内可读
- **格式**: "平台/动作 + 对象"（如 "Shopee Flash Sale"、"Amazon 广告优化"）

---

## Excalidraw 配置（跨境电商专用）

使用 `references/excalidraw-guide.md` 中的**专业蓝**风格作为基础，叠加平台品牌色。

### 电商场景形状规范

| 形状 | 用于 |
|------|------|
| 圆角矩形 | 平台模块、业务环节、数据卡片 |
| 梯形（上窄下宽翻转） | 漏斗转化（流量→转化） |
| 菱形 | 决策点（选品判断、广告优化决策） |
| 圆形 | 关键指标节点（ACOS、BSR） |
| 矩形分组框 | 平台分组（顶部色条区分平台） |

### 连接线规范

| 线型 | 用于 |
|------|------|
| 实线箭头 | 主业务流程、数据流向 |
| 虚线箭头 | 可选路径、辅助流程 |
| 粗实线箭头 | 资金流向 |
| 双向箭头 | 数据同步（如 ERP ↔ 平台） |

---

## 使用示例

### 示例 1：多平台运营架构

```mermaid
graph TB
    subgraph "选品中心"
        SP[市场调研<br/>选品分析]
    end

    subgraph "Amazon"
        A_LIST[Listing 优化]
        A_FBA[FBA 发货]
        A_AD[PPC 广告]
    end

    subgraph "TikTok Shop"
        T_VIDEO[短视频制作]
        T_LIVE[达人直播]
        T_AD[广告投放]
    end

    subgraph "Shopee"
        S_LIST[店铺装修]
        S_FLASH[Flash Sale]
        S_AD[站内广告]
    end

    subgraph "供应链 & 物流"
        WH[海外仓/FBA仓]
        LOG[跨境物流]
    end

    SP --> A_LIST
    SP --> T_VIDEO
    SP --> S_LIST
    A_LIST --> A_FBA
    A_FBA --> WH
    T_VIDEO --> T_LIVE
    S_LIST --> S_FLASH
    LOG --> WH

    class A_LIST,A_FBA,A_AD amazon
    class T_VIDEO,T_LIVE,T_AD tiktok
    class S_LIST,S_FLASH,S_AD shopee
    class WH,LOG logistics
    class SP product
```

### 示例 2：广告投放漏斗

```mermaid
graph TB
    IMP[曝光 Impressions<br/>100,000] --> CLK[点击 Clicks<br/>5,000]
    CLK --> ATC[加购 Add to Cart<br/>1,200]
    ATC --> ORD[下单 Orders<br/>600]
    ORD --> REV[销售额 Revenue<br/>$18,000]

    CTR[CTR 5.0%] -.-> CLK
    CVR[CVR 12.0%] -.-> ORD
    ACOS[ACOS 16.7%] -.-> REV

    class IMP product
    class CLK,ATC product
    class ORD growth
    class REV growth
    class CTR,CVR,ACOS finance
```

---

## Prompt 模板

```
[插入上方 System Prompt]

**内容**：
- 类型：[平台对比/运营漏斗/广告结构/选品分析/物流方案/数据仪表盘/时间趋势/业务闭环]
- 主题：[配图主题]
- 涉及平台：[Amazon / TikTok Shop / Shopee / 多平台]
- 关键元素：[需要出现的元素列表]
- 关键数据：[需要突出的指标/数字]

**构图建议**：[如：多栏对比、纵向漏斗、树形层级]

**特殊要求**：[如：需要标注 ACOS、需要展示物流时效]
```

---

## 在 SKILL.md 中启用

```bash
/smart-illustrator path/to/ecommerce-doc.md --style ecommerce
/smart-illustrator path/to/ecommerce-doc.md --style ecommerce --engine mermaid
/smart-illustrator path/to/ecommerce-doc.md --style ecommerce --engine excalidraw
```
