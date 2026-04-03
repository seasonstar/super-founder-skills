# WeChat Formatter & Publisher

将 **Markdown** 转为**微信公众号兼容的 HTML**，并可通过**微信公众平台接口**将文章发布为**草稿**。

- **转换**：纯 Python（`python-markdown` + `BeautifulSoup4`），无大模型依赖，输出稳定、速度快。  
- **发布**：调用官方 API 创建草稿，支持本地图片上传与正文内占位替换。

## 功能概览

| 能力 | 说明 |
|------|------|
| 双主题 | **Claude 风格**（简约橙、左边框标题） / **贴纸风格**（旋转 SECTION 徽章、渐变分隔） |
| 自定义主色 | `--color #RRGGBB` 自动派生标题、背景、表格等配色 |
| 草稿发布 | `publisher.py` 写入公众号草稿箱 |
| 图片 | 自动上传素材并替换正文中的本地图片引用；可选封面图 |

## 环境要求

- Python 3.10+（建议）
- 已开通**微信公众平台**接口权限的账号（发布能力依赖 `client_credential` 与草稿相关接口）

## 安装

```bash
git clone https://github.com/seasonstar/wechat-formatter-publisher.git
cd wechat-formatter-publisher
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 配置（必做）

仓库中的 **`config.py` 不会提交到 Git**（见 `.gitignore`），避免泄露密钥。

1. 复制模板：  
   `cp config.example.py config.py`
2. 编辑 `config.py`，填入公众号的 **AppID** 与 **AppSecret**（微信公众平台 → 开发 → 基本配置）。

## 使用

### 1. Markdown → HTML

```bash
python converter.py article.md --theme claude
python converter.py article.md --theme sticker --color "#007AFF"
```

同目录会生成：

- `article.html` — 带复制按钮的预览页，可粘贴到公众号编辑器  
- `article-manifest.json` — 标题、摘要、图片列表等元数据（发布时可选用）

### 2. HTML → 公众号草稿

```bash
python publisher.py article.html
python publisher.py article.html --manifest article-manifest.json --cover cover.png
python publisher.py article.html --author "作者名"
```

## 命令行参数摘要

**converter.py**

| 参数 | 说明 |
|------|------|
| `input` | 输入 Markdown 文件路径 |
| `--theme` | `claude`（默认）或 `sticker` |
| `--color` | 可选，主色，如 `#D97757` |

**publisher.py**

| 参数 | 说明 |
|------|------|
| `html` | 待发布的 HTML 文件 |
| `--manifest` | 可选，转换生成的 manifest JSON |
| `--cover` | 可选，封面图路径 |
| `--author` | 可选，作者显示名 |

## 与 Claude / Cursor 技能配合

本仓库可作为 **Agent Skill** 使用：将 `SKILL.md` 所在目录按你的工具说明挂载为技能后，可用自然语言触发「排版 → 预览 → 发布」流程（具体以各客户端技能配置为准）。

## 公众号排版兼容性说明

微信图文编辑器对 CSS 支持有限，本项目已做适配，例如：关键样式**内联**、部分结构用 **table** 承载背景、代码块换行处理等。贴纸主题使用 `transform` 旋转，**部分 Android WebView 下效果可能不一致**。

## 安全提示

- **切勿**将含真实 `APPSECRET` 的 `config.py` 推送到公开仓库。  
- 若密钥曾误提交，请在公众平台**重置 AppSecret**，并轮换所有副本。

## 许可证

若未单独提供 LICENSE 文件，默认保留所有权利；如需开源协议可自行补充。

## 相关链接

- 仓库：<https://github.com/seasonstar/wechat-formatter-publisher>
