# Super Founder Skills

Claude Code 技能集合 - 内容创作与项目管理自动化工具。

## Skills

| Skill | Description | Trigger |
|-------|-------------|---------|
| [wechat-formatter-publisher](skills/wechat-formatter-publisher/) | Markdown 转微信公众号 HTML 并发布草稿 | 公众号排版、微信文章格式化 |
| [csdn-article-publish](skills/csdn-article-publish/) | CSDN 博客文章发布（含图片上传） | 发布到CSDN、CSDN草稿箱 |
| [smart-illustrator](skills/smart-illustrator/) | 智能配图与封面图生成器 | 配图、插图、封面图、PPT |
| [zsxq-publish](skills/zsxq-publish/) | 知识星球自动化（发帖/回帖/通知） | 知识星球、发帖、zsxq |
| [yunxiao-task-assign](skills/yunxiao-task-assign/) | 云效任务分配 | 分配任务、创建任务 |
| [yunxiao-weekly-report](skills/yunxiao-weekly-report/) | 云效迭代周报生成 | 周报、Sprint周报 |

## Installation

### 方式一：Clone + Symlink（推荐）

Clone 到 `~/.claude/skills/` 下，用 symlink 链接各技能，方便 `git pull` 统一更新：

```bash
# 1. Clone 仓库
git clone https://github.com/seasonstar/super-founder-skills.git ~/.claude/skills/super-founder-skills

# 2. 为每个技能创建 symlink
for skill in wechat-formatter-publisher csdn-article-publish smart-illustrator zsxq-publish yunxiao-task-assign yunxiao-weekly-report; do
  ln -sf ~/.claude/skills/super-founder-skills/skills/$skill ~/.claude/skills/$skill
done

# 3. 后续更新只需
cd ~/.claude/skills/super-founder-skills && git pull
```

### 方式二：直接复制

```bash
git clone https://github.com/seasonstar/super-founder-skills.git
cp -r super-founder-skills/skills/* ~/.claude/skills/
```

## 各技能配置

### wechat-formatter-publisher

Markdown 转微信公众号兼容 HTML，通过 API 发布草稿。支持 Claude 风格（简约橙）和贴纸风格（旋转贴纸）。

```bash
# 1. 安装 Python 依赖
pip install markdown beautifulsoup4 requests

# 2. 配置公众号 API 凭证
cd ~/.claude/skills/wechat-formatter-publisher
cp config.example.py config.py
# 编辑 config.py，填入：
#   APPID = "你的公众号AppID"
#   APPSECRET = "你的公众号AppSecret"
```

### csdn-article-publish

CSDN 博客文章生成与发布，支持图片上传到 GitHub 图床。

```bash
# 1. 配置 CSDN 请求头（从浏览器 DevTools 抓取）
cd ~/.claude/skills/csdn-article-publish
cp config/config_example.json config/csdn_config.json
# 编辑 config/csdn_config.json，填入：
#   - headers: 从浏览器 DevTools > Network > saveArticle 请求中复制 Cookie、x-ca-signature 等
#   - github: token、owner、repo（用于图片上传到 GitHub 图床）

# 2. 确保 Node.js 和 Python3 已安装
# CSDN 请求头会过期，需定期从浏览器重新抓取
```

### smart-illustrator

智能配图与封面图生成器，支持文章配图、PPT 信息图、封面图三种模式。

```bash
# 1. 安装依赖（需要 Bun 运行时）
cd ~/.claude/skills/smart-illustrator
bun install

# 2. 配置阿里云 DashScope API Key（两种方式二选一）
# 方式A：环境变量
export DASHSCOPE_API_KEY="你的API Key"

# 方式B：写入配置文件（推荐，避免每次设置环境变量）
mkdir -p ~/.smart-illustrator
cat > ~/.smart-illustrator/config.json << 'EOF'
{
  "apiKey": "你的DashScope API Key",
  "references": ["./refs/style-ref-01.png"]
}
EOF

# 3. 项目级配置（可选，用于风格参考图）
# .smart-illustrator/config.json
# 内容示例: { "references": ["./refs/style-ref-01.png"] }
```

### zsxq-publish

知识星球自动化，支持发帖、回帖、浏览帖子、检查通知、自动回帖。

```bash
# 1. 安装依赖
cd ~/.claude/skills/zsxq-publish/scripts
npm install

# 2. 配置知识星球 Cookie
node zsxq.js config add --url "https://wx.zsxq.com/group/你的GROUP_ID" --cookie "完整Cookie"

# Cookie 从浏览器 DevTools > Application > Cookies > zsxq_access_token 获取
# Cookie 会过期，API 返回 1004/1059 错误时需重新配置
```

### yunxiao-task-assign & yunxiao-weekly-report

云效任务分配 + 周报生成。通过 Claude 原生 MCP 工具调用云效 API，敏感配置统一存放在本地。

```bash
# 1. 配置 MCP Server
# 在 ~/.claude/mcp.json 中添加 alibabacloud-devops server
# 设置 YUNXIAO_ACCESS_TOKEN 环境变量

# 2. 创建本地配置文件（敏感信息不入库）
mkdir -p ~/.yunxiao
cat > ~/.yunxiao/config.json << 'EOF'
{
  "organizationId": "你的云效组织ID",
  "projectName": "项目名称",
  "bufferDays": 7,
  "wecomWebhook": "企微Webhook地址",
  "members": {
    "姓名": "用户ID"
  }
}
EOF

# 3. 云效 Access Token 获取：
#    登录云效 > 个人设置 > Access Token > 创建 Token（勾选项目管理权限）
```

## 更新技能

```bash
cd ~/.claude/skills/super-founder-skills && git pull
```

使用 symlink 方式安装的，`git pull` 即可同步全部 6 个技能。直接复制方式安装的需重新执行 `cp -r` 覆盖。

## License

MIT
