---
name: wechat-article-writer
description: >
  Write WeChat Official Account (公众号) articles in the author's personal conversational style
  for three series: "量化指标解码" (indicator analysis), "以AI量化为生" (system development),
  and "量化策略开发" (strategy development). Trigger when user says "写公众号", "写文章",
  "写一篇关于XX的文章", or specifies any of the three series names. Also triggers for
  "写教程" when referring to Knowledge Planet (知识星球) indicator tutorials.
---

# WeChat Article Writer

Write articles for WeChat Official Account "量策堂" in the author's personal voice.

## Before Writing

1. Read `README_atmquant.md` in the project root to get the latest article list and links for the footer
2. Determine the series from user's request:
   - **量化指标解码** → See [references/indicator-series.md](references/indicator-series.md)
   - **以AI量化为生** → See [references/system-series.md](references/system-series.md)
   - **量化策略开发** → See [references/strategy-series.md](references/strategy-series.md)
   - **知识星球教程** → See [references/tutorial-format.md](references/tutorial-format.md)
3. Load the corresponding reference file for series-specific structure

## Writing Style Rules (ALL series)

### Voice & Tone

Write like chatting with a knowledgeable friend, NOT like a textbook or AI assistant.

**DO:**
- Use "说实话", "其实", "不过", "对了", "等等" naturally
- Use "我们", "你" to connect with readers
- Allow thought jumps and self-corrections mid-paragraph
- Share real experiences: "踩过坑才知道...", "刚开始我也是这么想的，后来发现..."
- Be honest about limitations: "完全不足以证明策略的有效性"
- Short + long sentence rhythm. Pause. Skip minor details.

**DON'T:**
- Use any emoji (strict rule - causes crash in Qt UI)
- Use "让我们来探讨...", "综上所述...", "通过以上分析可以得出..."
- Use "值得注意的是...", "如图所示", "基于上述原因"
- Write "本文将介绍..." - write "这篇文章讲..." instead
- Use "问题1、问题2" format in experience sections
- Write textbook-style summaries like "本章小结：1. ... 2. ... 3. ..."
- Over-explain. Trust the reader.

### Code Display Rules

- Code blocks are **cost**, not asset. Minimize them.
- Single code block max 15-20 lines
- Only show key fragments, full code points to GitHub
- Comments only for pitfalls and key logic, not obvious steps
- Prefer text description over code when possible
- Use "伪代码" or flow description for complex logic

### Article Structure (Common)

All series share this skeleton:

```
# Title with series prefix

> Series intro blockquote (1 sentence summarizing core content)

![Header Image](./images/xxx-header.jpg)

## 写在前面
[Connect to previous article. Start with real scenario/problem.]

## [Main Content Sections]
[Multiple sections with minimal code]

## 实战经验与避坑指南
[4 points max, each 2-3 sentences, ~150 words total]

## 写在最后
[Summary + next article preview, natural transition]

---
[Footer: series credit + GitHub link + disclaimer]

---
### 加入「量策堂·AI算法指标策略」
[Planet QR code image]

---
### 往期文章回顾

**量化策略开发系列**
- [量化策略开发01：我让AI全权做交易决策：从提示词设计到决策执行](https://mp.weixin.qq.com/s/yY95qcyoTXvzOFYjQcDpHw)
- [量化策略开发02：海龟三重EMA趋势策略 - 从设计思路到回测验证](https://mp.weixin.qq.com/s/xB0_bTsrU7OzmwqdKAFfQw)
- [量化策略开发03：均值回归信号捕捉 - EMA+RSI+ATR三维共振交易系统](https://mp.weixin.qq.com/s/Nl9Oqr7nsSWlnNGM9qJBGA)

**以AI量化为生系列**
- [以AI量化为生01：普通人如何从无到有稳步构建交易系统](https://mp.weixin.qq.com/s/vHL2ZNoqe65dGn9qEQzLgQ)
- [以AI量化为生23：打造AI全驱动量化策略引擎](https://mp.weixin.qq.com/s/_QfvEdyZnJKhAWaMi98vUQ)
- [以AI量化为生24：回测结果存储与策略参数管理](https://mp.weixin.qq.com/s/nIEAYOQutAUJKy8C5Dnj6w)

**量化指标解码系列**
- [量化指标解码01：让指标开口说话！K线图表给技术指标装上AI大脑](https://mp.weixin.qq.com/s/nvF7VT25RXgHzSnVRfBEcQ)
- [量化指标解码19：K线形态识别 - 价格行为不会说谎](https://mp.weixin.qq.com/s/F2Pa-zLc7Axub9Zj__b-6A)
- [量化指标解码20：谐波形态识别 - 用斐波那契找到精准反转点](https://mp.weixin.qq.com/s/4VzYURqpDeSVRh_1A8EGAw)

---
**相关标签**：#量化交易 #... #Python #vnpy
```

### Footer (Fixed Structure)

Every article ends with these three sections in order:

1. **Series credit line** + GitHub link + disclaimer
2. **知识星球** section with QR code image
3. **往期文章回顾** with real links from README_atmquant.md (NEVER fabricate links)
4. **相关标签**

### 往期文章回顾 Rules

**Format**: Use unordered lists (`-`), NOT ordered lists (`1.`). Ordered lists break line rendering in WeChat.

**Series order** (must follow this exact order):
1. 量化策略开发系列
2. 以AI量化为生系列
3. 量化指标解码系列

**Article selection**: Each series lists exactly 3 articles:
- The **first article** of the series (e.g., XX01)
- The **two most recently published** articles

### Opening Blockquote Format

Each series has a fixed opening format:

- **量化指标解码**: `> 本文是《量化指标解码》系列的第X篇，我们将深入解码[指标名]，从[核心特性1]到[核心特性2]，从[应用场景1]到[应用场景2]，让你掌握[核心价值主张]。`
- **以AI量化为生**: `> 本文是《以AI量化为生》系列的第X篇，我们将从[问题/背景]出发，[核心内容概述]，[最终目标/效果]。`
- **量化策略开发**: `> 本文是《量化策略开发》系列的第X篇。[一句话概括文章核心价值]。`

## Colloquial Phrases

Use phrases from [references/colloquial-phrases.md](references/colloquial-phrases.md) naturally.
Each phrase max ONCE per article. Match section mood. Never force.

## Narrative Techniques

Apply these techniques for natural article flow:

### Echo Structure (契诃夫の枪)
Plant a concept early, echo it later with new meaning.
Example: Mention "均值回归" casually in intro → reveal it as the core strategy logic later.

### Escalation (升番)
Stack examples with increasing impact. Last one should be the most surprising.
Example: "参数优化完，胜率从40%提到52%。换到另一个品种，55%。再试第三个，直接60%。"

### Humble Setup (谦逊铺垫)
State uncertainty before revealing strong result. Makes conclusion credible.
Example: "说实话，开始我也不信。但跑完3000根K线的数据，结果就摆在那了。"

### Layered Reveal (层层剥开)
Don't give the answer upfront. Lead reader through discovery steps.
Example: Show raw data → point out anomaly → explain why → reveal the strategy logic behind it.

## Quality Assurance (4-Layer QA)

Run these checks AFTER writing, before finalizing:

### L1: Hard Rules Scan
- Zero emoji anywhere
- No banned machine-like phrases (see DON'T list)
- Code blocks each under 20 lines
- Footer has all 4 parts (credit, 知识星球, 往期回顾, tags)
- 往期文章 uses unordered lists (`-`), NOT ordered lists (`1.`)
- 往期文章 series order: 量化策略开发 → 以AI量化为生 → 量化指标解码
- 往期文章 links are real URLs (never fabricate)

### L2: Style Consistency
- Opening blockquote matches series format
- "写在前面" connects to previous article context
- Colloquial phrases used naturally, not forced
- Sentence rhythm varies (long + short, pause points)
- No two consecutive paragraphs start the same way

### L3: Content Quality
- Every claim has evidence or experience backing it
- Narrative techniques applied (at least 1 echo or escalation)
- "实战经验与避坑指南" under 150 words, max 4 points
- "写在最后" previews next article naturally
- Article saved to `articles/` directory (not committed to git)

### L4: Living Human Quality
- Read aloud mentally - does it sound like a real person talking?
- Can you find at least 3 places where the author's personality shows?
- Would a reader feel they learned something genuinely useful?
- Is there at least one moment of vulnerability or honest self-correction?
- Does the ending feel natural, not like a forced summary?
