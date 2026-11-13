---
name: wechat-formatter-publisher
description: 将 Markdown 文稿转换为微信公众号兼容的 HTML 并通过 API 发布草稿，也支持发布贴图（图片消息 newspic）草稿。文章支持 Claude 风格（简约橙）和贴纸风格（旋转贴纸）两种主题。触发词：「公众号排版」「微信文章格式化」「WeChat article」「格式化为公众号」「转换为微信格式」「发布公众号」「公众号贴图」「发贴图」「图片消息」。
---

# 微信文章排版发布器 (WeChat Formatter & Publisher)

将 Markdown 文稿转换为微信公众号兼容的 HTML，并通过 WeChat API 发布草稿；另支持「发贴图」图片消息草稿。

## 核心能力

- **确定性转换**: 纯 Python 脚本 (python-markdown + BeautifulSoup4)，无 AI 开销，秒级完成
- **双主题支持**: Claude 风格（简约橙）和贴纸风格（旋转贴纸）
- **自定义色系**: `--color #HEX` 自动派生完整配色
- **API 发布**: 直接通过微信 API 创建草稿，无需浏览器自动化
- **图片上传**: 自动上传本地图片到素材库并替换占位符
- **贴图发布**: `--sticker` 模式创建图片消息（newspic）草稿，图片为主、短文字为辅
- **发布参数自动填充**: 作者、留言开关自动写入草稿；合集按标题自动匹配；发布后打印后台手动确认清单（见「发布参数」节）

## 快速开始

### CLI 命令

```bash
# 转换 Markdown 为 HTML
python converter.py article.md --theme claude
python converter.py article.md --theme sticker --color #007AFF

# 发布 HTML 到公众号草稿箱（作者/留言/合集自动处理，见「发布参数」节）
python publisher.py article.html
python publisher.py article.html --manifest article-manifest.json --cover cover.png
python publisher.py article.html --collection "自定义合集名"   # 覆盖自动匹配
python publisher.py article.html --no-comment                  # 关闭留言

# 发布贴图（图片消息 newspic）草稿
python publisher.py --sticker --image /abs/card.png --title "标题" --text "一两句配文" --author "堂主"
python publisher.py --sticker --image /abs/1.png --image /abs/2.png --title "多图贴图" --text "配文"
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

询问用户是否发布到公众号。如发布，执行 `python publisher.py`。发布成功后必须把脚本打印的「后台手动确认清单」原样转述给用户。

---

## 发布参数

创建草稿时自动填充以下参数（默认值在 `config.py` 的 `PUBLISH_DEFAULTS` / `COLLECTION_MAP` / `MANUAL_PUBLISH_STEPS`，可直接编辑）：

### API 可自动设置（直接写入草稿）

| 参数 | 值 | 说明 |
|------|-----|------|
| 作者 | 堂主 | `--author` 可覆盖 |
| 留言 | 开启，所有人可评论 | `--no-comment` 可关闭 |

### 合集自动匹配（打印提醒，后台手动勾选）

按标题关键词自动匹配（`config.COLLECTION_MAP`，首个命中生效）：

| 标题包含 | 应选合集 |
|----------|----------|
| 量化指标解码 | 量化指标库 |
| 量化策略开发 | 策略实验室 |
| 以AI量化为生 | 交易系统开发 |

未命中时不指定，提醒用户手动选择；`--collection` 可覆盖自动匹配。

### 仅后台手动设置（官方 API 无对应字段）

以下 4 项微信**未开放 API**（实测 `draft/add` 传入会被静默丢弃），草稿创建后脚本自动打印确认清单，发布前在公众号后台勾选即可：

- 原创：声明原创 → 文字原创 + 快捷转载
- 合集：加入合集 →（见上表自动匹配结果）
- 创作来源：个人观点，仅供参考
- 平台推荐：开启

另有 1 项为**账号级一次性设置**：留言「自动精选公开」在 后台 设置→留言 开启一次即可，之后所有文章生效。

**代理使用技能的 Agent 注意**：发布成功后，必须把脚本输出的 📌 手动确认清单转述给用户，不要省略。

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

## 贴图发布（图片消息 newspic）

对应公众号后台「发贴图」，与文章草稿（`article_type=news`）是不同类型：`article_type=newspic`，图片为主、短文字为辅，不经过 Markdown/HTML 转换流程。

- **流程**: `add_material` 逐张上传永久素材拿 `media_id` → `draft/add` 带 `image_info.image_list`
- **首图即封面**: 无需单独 `--cover`；最多 20 张图
- **`--text` 同时作为 digest**；标题、配文有微信长度限制，保持短小
- **只建草稿**: 最终发布仍需在公众号后台手动操作
- **中文编码**: JSON 请求体显式 `ensure_ascii=False` + UTF-8，否则中文乱码（publisher.py 已内置）
- 适合场景：知识卡片、海报图、截图速记等以图为主的内容（配图可用 guizang-social-card-skill 生成）

## 输出文件

转换后输出到源文件同目录：
- `{filename}.html` — 预览页面
- `{filename}-manifest.json` — 元信息

预览页面包含复制按钮（Clipboard API + execCommand 降级），支持手动粘贴到公众号编辑器。

## 公众号信息

- 名称：堂主的ATMQuant
- AppID/AppSecret 已内置在 config.py
- Access Token 自动获取和刷新
