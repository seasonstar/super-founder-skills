---
name: csdn-article-publish
description: csdn blog article publish skills,CSDN博客文章生成与发布技能。当用户请求"帮我发布文章到CSDN"、"保存到CSDN草稿箱"、"发布CSDN文章"时调用此技能。
---

# CSDN Blog Article Publish Skills

## 技能概述

- 支持读取指定路径的 Markdown 文件，保存为 CSDN 草稿
- 自动从文章内容中提取标签（解析"相关标签"字段）
- 支持本地前置校验，在请求发送前检查配置缺项、标签数量等问题
- 自动维护本地文章映射文件 `csdn_article_map.json`，记录 `file -> articleId -> url`
- 根据文章 ID 或已保存过的 Markdown 文件更新/发布文章
- 发布文章（需额外字段）

## 触发方式

直接用自然语言描述需求即可：

- "帮我发布文章：articles/以AI量化为生：20.实时图表交易系统开发.md"
- "保存到CSDN草稿箱：articles/xxx.md"
- "把这篇文章发布到CSDN：@articles/以AI量化为生：20.实时图表交易系统开发.md"
- "更新CSDN文章：articles/xxx.md"
- "发布CSDN文章 ID 159048943"

收到上述请求后：
1. 读取用户提供的 Markdown 文件路径
2. 解析文件内容，提取标题和标签（从"相关标签"字段中提取）
3. **上传本地图片到无铭图床(wmimg.com)，替换文章中的本地图片链接为 wmimg 直链**
4. 验证所有图片链接已替换完成（无本地路径残留）
5. 调用 `csdn_article.js` 执行保存/更新/发布

## ⚠️ 重要注意事项

- **图片链接替换**：上传本地图片后**必须**替换 Markdown 中的链接为 wmimg 直链，再保存/发布。未替换的本地路径在 CSDN 上无法显示。
- **防限流**：CSDN 有接口限流机制，请勿频繁调用 API
- **建议操作**：
  - 单次保存/更新操作间隔至少 5-10 秒
  - 每天保存/更新文章数量建议不超过5篇
  - 优先使用草稿状态，确认无误后再发布

## 工作流程

### 步骤 1：检查配置文件

确认 `~/.claude/skills/csdn-article-publish/config/csdn_config.json` 存在且包含有效的 CSDN 请求头（Cookie、x-ca-nonce、x-ca-signature 等）。

请求头获取方法：
1. 登录 CSDN 并打开 https://editor.csdn.net/md/
2. 填写标题和内容，点击保存草稿
3. 打开浏览器开发者工具（F12）→ Network 标签
4. 找到 `saveArticle` 请求，右键 → Copy → Copy as cURL
5. 提取请求头信息填入配置文件

### 步骤 2：读取并解析 Markdown 文件

读取用户提供的 Markdown 文件，解析出：
- **标题**：优先使用文件名（去掉路径和扩展名）；若文件首行是 `# XXXX` 格式，则取 `XXXX` 作为标题
- **标签**：从文件末尾"相关标签"行中提取（例如 `#量化交易 #Python #vnpy` → `量化交易,Python,vnpy`）
- **内容**：完整的 Markdown 正文

解析示例：

```python
import re

def parse_article(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题（优先文件名）
    title = Path(filepath).stem

    # 若文件首行是 "# XXXX" 格式，取 XXXX 为标题
    first_line_match = re.match(r'^#\s+(.+)$', content.strip(), re.MULTILINE)
    if first_line_match:
        title = first_line_match.group(1).strip()

    # 提取标签（从"相关标签"行）
    tags_match = re.search(r'相关标签[：:](.+?)$', content, re.MULTILINE)
    tags = []
    if tags_match:
        tag_line = tags_match.group(1)
        tags = re.findall(r'#(\w+)', tag_line)

    return title, ','.join(tags), content
```

### 步骤 3：上传本地图片并替换链接

**⚠️ 关键步骤：上传所有图片（本地和外链）到 wmimg 图床，替换链接后再发布。**

**所有图片都需要重新上传**：本地图片直接上传，外链图片下载后转存到 wmimg。

#### 3.1 逐张上传图片

识别文章中所有 `![alt](路径)` 格式的图片，逐张上传：

```bash
# 上传单张图片（Token 从 csdn_config.json 自动读取）
python3 ~/.claude/skills/csdn-article-publish/scripts/wmimg_uploader.py <图片绝对路径>
```

**注意**：图片路径必须相对于文章所在目录解析。例如文章在 `articles/` 目录下，图片 `xxx.png` 的绝对路径为 `articles/xxx.png`。

每张图片上传成功后，记录返回的 `url`（格式：`https://wmimg.com/xxx/xxx.png`）。

#### 3.2 替换文章中的本地图片链接

**必须完成这一步才能发布！** 将文章中每张图片的路径替换为上传后返回的 wmimg 直链：

```
替换前: ![说明](本地图片名.png)
替换后: ![说明](https://wmimg.com/xxx/图片名.png)

替换前: ![说明](https://other-site.com/xxx/图片名.png)
替换后: ![说明](https://wmimg.com/xxx/图片名.png)
```

使用 Edit 工具逐张替换，确保所有 `![alt](非http开头)` 的图片链接都已替换为 wmimg URL。

#### 3.3 验证替换结果

替换完成后，用 Grep 工具检查文章中是否还有未替换的本地图片：

```
grep pattern: !\[.*\]\((?!https?://)
```

确认所有图片链接都以 `https://` 开头后，再进入下一步发布流程。

**单独上传一张图片**：
```bash
# 基本用法（Token 从 csdn_config.json 自动读取）
python3 ~/.claude/skills/csdn-article-publish/scripts/wmimg_uploader.py <图片路径>

# 指定 Token
python3 ~/.claude/skills/csdn-article-publish/scripts/wmimg_uploader.py <图片路径> <WMIMG_TOKEN>
```

**wmimg Token 获取**：从 `csdn_config.json` 的 `wmimg.token` 字段读取，或使用环境变量 `$WMIMG_TOKEN`。

### 步骤 4：保存草稿

**确保步骤3的图片链接替换已完成**，然后调用 `save` 命令：

```bash
node ~/.claude/skills/csdn-article-publish/scripts/csdn_article.js save \
  --title "文章标题" \
  --file /path/to/article.md
```

成功后在当前工作目录生成 `csdn_article_map.json`，记录文件与文章ID的映射。

### 步骤 5：检查草稿

引导用户在 CSDN 编辑器中检查文章排版、格式、内容，确认无误后进入下一步。

### 步骤 6：发布（如需发布）

**再次确认：文章中所有图片链接必须是可访问的 URL（https://开头），无本地路径残留。**

调用 `publish` 命令，使用 `--extra` 传递标签：

```bash
node ~/.claude/skills/csdn-article-publish/scripts/csdn_article.js publish \
  --id 159048943 \
  --title "文章标题" \
  --file /path/to/article.md \
  --extra '{"tags":"量化交易,Python,vnpy","description":"文章摘要","creation_statement":1}'
```

**--extra 参数说明：**
| 字段 | 说明 | 可选值 |
|------|------|--------|
| tags | 标签（逗号分隔，最多5个） | 从文章"相关标签"提取 |
| readType | 可见范围 | public(默认值), private, read_need_fans, read_need_vip |
| type | 文章类型 | original(默认值), repost, translated |
| creation_statement | 创作声明 | 0=无声明(默认值), 1=部分内容由AI辅助生成, 2=内容来源网络进行整合创作, 3=个人观点，仅供参考 |
| description | 文章摘要（最大256字） | - |

## 本地前置校验

脚本会在发送请求前拦截以下常见问题：
- 配置缺项：缺少 `Cookie`、`x-ca-nonce`、`x-ca-signature` 等
- 配置占位符未替换：仍保留 `your_cookie_here`、`xxxxxx` 等示例值
- 标题为空：无法从文件或文件名获取标题
- 标签过多：超过 5 个标签
- 发布缺字段：`publish` 模式下未提供摘要

## 本地文章映射文件

- 文件名：`csdn_article_map.json`
- 后续执行 `update` / `publish` 时，如果继续使用同一个文件，可以省略 `--id` 自动复用映射

## 目录结构

```
csdn-article-publish/
├── SKILL.md
├── scripts/
│   ├── csdn_article.js              # 核心执行脚本
│   ├── markdown_to_html.js
│   ├── marked.umd.js
│   ├── github_image_uploader.py     # GitHub 图床上传工具（已弃用）
│   ├── wmimg_uploader.py            # 无铭图床上传工具（国内稳定）
│   └── markdown_image_uploader.py   # Markdown 图片处理器（自动上传本地图片）
├── config/
│   ├── config_example.json           # 配置文件示例
│   ├── csdn_config.json              # 用户实际配置（含 wmimg Token）
│   └── user_agents.json
└── references/
    ├── api_reference.md
    └── troubleshooting.md
```

## 故障排查

常见的请求头过期、签名失效、限流、发布失败等问题，可参考 [troubleshooting.md](references/troubleshooting.md)
