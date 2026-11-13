---
name: csdn-article-publish
description: csdn blog article publish skills,CSDN博客文章生成与发布技能。当用户请求"帮我发布文章到CSDN"、"保存到CSDN草稿箱"、"发布CSDN文章"时调用此技能。
---

# CSDN Blog Article Publish Skills

## 技能概述

- 支持读取指定路径的 Markdown 文件，保存为 CSDN 草稿
- 自动从文章内容中提取标签（解析"相关标签"字段）
- 图片转存后自动把正文第一张图片设置为文章首图封面
- 按文章系列自动匹配 CSDN 分类：`量化指标解码` → `量化指标解码`，`量化策略开发` → `量化策略开发`，`以AI量化为生` → `交易系统开发`
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
3. 调用 `csdn_article.js` 执行保存/更新/发布。脚本会在请求前把本地图片和外链图片上传到 CSDN 图床，并把正文里的地址替换为 `*.csdnimg.cn`
4. 已在 CSDN 图床上的图片会跳过。上传失败时直接停止，不会把会丢图的外链发出去

## ⚠️ 重要注意事项

- **图片**：不要再手工传到无铭图床。`save` / `publish` 会把 Markdown 里的本地路径和外链下载后上传到 CSDN 图床，再用 `i-blog.csdnimg.cn` 地址发布。无铭图床、GitHub 等外链会被 CSDN 转存失败后删掉。
- **首图封面**：图片转存完成后，脚本默认把正文中第一张图片写入 `cover_images`，并将 `cover_type` 设为 `1`（单图封面）。如需关闭，传 `"auto_cover": false`；如需指定其他图片，传 `"cover_image": "https://..."`。
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

### 步骤 3：图片由发布脚本自动转存

`csdn_article.js` 在保存或发布前会扫描 `![说明](路径)` 和 `<img src="...">`：

- 本地路径按 Markdown 文件所在目录解析，直接上传
- `http` 外链先下载，再上传
- 域名已经是 `csdnimg.cn` 或 `csdn.net` 的地址保持不变
- 同一张图片按内容哈希缓存在 `config/csdn_image_cache.json`，重复发布不会再次上传
- 转存完成后，正文第一张图片会自动成为文章首图封面；接口发送 `cover_images: [第一张图片URL]` 与 `cover_type: 1`

不需要改 Markdown 源文件，也不要再把图片换成 wmimg 链接。上传失败时命令会退出，文章不会发出去。

### 步骤 4：保存草稿

调用 `save` 命令。图片会在这一步自动转存到 CSDN 图床：

```bash
node ~/.claude/skills/csdn-article-publish/scripts/csdn_article.js save \
  --title "文章标题" \
  --file /path/to/article.md
```

成功后在当前工作目录生成 `csdn_article_map.json`，记录文件与文章ID的映射。

### 步骤 5：检查草稿

引导用户在 CSDN 编辑器中检查文章排版、格式、内容，确认无误后进入下一步。

### 步骤 6：发布（如需发布）

调用 `publish` 命令，使用 `--extra` 传递标签。图片同样会在发布前自动转存：

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
| creation_statement | 创作声明 | 0=无声明, 1=部分内容由AI辅助生成, 2=内容来源网络进行整合创作, 3=个人看法，仅供参考（默认值） |
| description | 文章摘要（最大256字） | - |
| categories | 手动指定分类；未指定时按标题系列自动匹配 | 默认映射见上方说明 |
| auto_cover | 是否自动使用正文第一张图片作为首图封面 | `true`（默认值）/`false` |
| cover_image | 手动指定首图封面 URL；设置后优先于自动首图 | CSDN 图床 URL 最稳妥 |

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
