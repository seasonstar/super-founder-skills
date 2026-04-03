---
name: wechat-formatter-publisher
description: 将 Markdown 文稿转换为微信公众号兼容的 HTML 并通过 API 发布草稿。支持 Claude 风格（简约橙）和贴纸风格（旋转贴纸）两种主题。触发词：「公众号排版」「微信文章格式化」「WeChat article」「格式化为公众号」「转换为微信格式」「发布公众号」。
---

# 微信文章排版发布器 (WeChat Formatter & Publisher)

将 Markdown 文稿转换为微信公众号兼容的 HTML，并通过 WeChat API 发布草稿。

## 核心能力

- **确定性转换**: 纯 Python 脚本 (python-markdown + BeautifulSoup4)，无 AI 开销，秒级完成
- **双主题支持**: Claude 风格（简约橙）和贴纸风格（旋转贴纸）
- **自定义色系**: `--color #HEX` 自动派生完整配色
- **API 发布**: 直接通过微信 API 创建草稿，无需浏览器自动化
- **图片上传**: 自动上传本地图片到素材库并替换占位符

## 快速开始

### CLI 命令

```bash
# 转换 Markdown 为 HTML
python converter.py article.md --theme claude
python converter.py article.md --theme sticker --color #007AFF

# 发布 HTML 到公众号草稿箱
python publisher.py article.html
python publisher.py article.html --manifest article-manifest.json --cover cover.png
```

### 交互式工作流

```
/wechat-formatter-publisher @article.md
/wechat-formatter-publisher @article.md --theme sticker --color #007AFF
```

---

## 交互模式工作流

### 第一步：主题选择

| 主题 | 特点 | 适用场景 |
|------|------|----------|
| **Claude 风格** | 简约橙色、左边框标题、清爽段落 | 技术分享、日常随笔、简短内容 |
| **贴纸风格** | 旋转贴纸编号、渐变分隔线、宽行高 | 教程指南、技术解析、趣味科普 |

### 第二步：色系选择

| 主题 | 默认主色 |
|------|----------|
| Claude 风格 | `#D97757` (温暖橙) |
| 贴纸风格 | `#D97757` (Claude 橙) |

用户可输入自定义 HEX 色值（如 `#007AFF`），系统自动派生完整色系。

### 第三步：转换

执行 `python converter.py`，输出：
- `{filename}.html` — 预览页面（含复制按钮）
- `{filename}-manifest.json` — 元信息与图片映射

### 第四步：验证

打开生成的 HTML 预览，确认排版效果。

### 第五步：发布

询问用户是否发布到公众号。如发布，执行 `python publisher.py`。

---

## CSS 兼容性规范

- 所有 CSS 内联（WeChat 剥离 `<style>` 标签）
- 不支持 `flex`/`grid`/`box-shadow`/`var()`/`position`
- 背景色使用 `table`/`section`，不使用 `div`
- 圆角 table 使用 `border-collapse: separate; border-spacing: 0`
- 代码块使用 `<br>` + `&nbsp;`，不使用 `white-space`
- 表格 `th`/`td` 必须显式声明 `font-size`

## 色系派生规则

| 角色 | 派生方式 | 用途 |
|------|----------|------|
| 主色 | 用户提供 | 标题边框、强调、引用边框 |
| 主色深 | L-15% | 渐变辅助、表头 |
| 主色浅 | L+10% | 渐变辅助 |
| 背景浅 | S=15%, L=97% | 占位符背景、高亮背景 |
| 背景灰 | 固定 #FAF9F7 | 交替行、引用块 |

## 贴纸主题说明

- 徽章编号：自动递增 01, 02, 03...
- 标签文字：固定 "SECTION"（不做 AI 推理）
- 旋转角度：`transform: rotate(-15deg)`
- 兼容性警告：部分 Android WebView 不支持 `transform`

## 输出文件

转换后输出到源文件同目录：
- `{filename}.html` — 预览页面
- `{filename}-manifest.json` — 元信息

预览页面包含复制按钮（Clipboard API + execCommand 降级），支持手动粘贴到公众号编辑器。

## 公众号信息

- 名称：堂主的ATMQuant
- AppID/AppSecret 已内置在 config.py
- Access Token 自动获取和刷新
