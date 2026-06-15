# Super Founder Skills

Claude Code 技能集合 - 内容创作与项目管理自动化工具。

## Skills

| Skill | Description | Trigger |
|-------|-------------|---------|
| [wechat-article-writer](skills/wechat-article-writer/) | 微信公众号文章写作辅助 | 公众号写作、微信文章 |
| [wechat-formatter-publisher](skills/wechat-formatter-publisher/) | Markdown 转微信公众号 HTML 并发布草稿 | 公众号排版、微信文章格式化 |
| [csdn-article-publish](skills/csdn-article-publish/) | CSDN 博客文章发布（含图片上传） | 发布到CSDN、CSDN草稿箱 |
| [smart-illustrator](skills/smart-illustrator/) | 智能配图与封面图生成器 | 配图、插图、封面图、PPT |
| [zsxq-publish](skills/zsxq-publish/) | 知识星球自动化（发帖/回帖/通知） | 知识星球、发帖、zsxq |
| [yunxiao-task-assign](skills/yunxiao-task-assign/) | 云效任务分配 | 分配任务、创建任务 |
| [yunxiao-weekly-report](skills/yunxiao-weekly-report/) | 云效迭代周报生成 | 周报、Sprint周报 |
| [it-sync](skills/it-sync/) | IT双周汇报与排期同步（钉钉数据 + 信息图生成） | IT同步、排期图、双周排期 |
| [ruankao-quiz](skills/ruankao-quiz/) | 软考案例分析速记练习（AI智能评分） | 软考练习、ruankao、quiz |
| [project-decision-log](skills/project-decision-log/) | 会议录音笔记提炼，生成项目决议日志（changelog 式） | 总结会议、会议决议、提炼会议、会议纪要 |
| [dingtalk-ai-table](skills/dingtalk-ai-table/) | 钉钉 AI 表格（多维表）操作 | 钉钉表格、AI表格、多维表 |
| [dingtalk-docs](skills/dingtalk-docs/) | 钉钉云文档管理（文档/表格/脑图/文件夹） | 钉钉文档、云文档、创建文档 |
| [wukong-knowledge-audit](skills/wukong-knowledge-audit/) | 钉钉知识库系统性诊断审计 | 审计知识库、知识库体检、文档索引 |
| [12306-train-query](skills/12306-train-query/) | 12306 火车票班次查询 | 查火车票、12306、车次 |
| [ctrip-flight-search](skills/ctrip-flight-search/) | 携程航班查询（单程/往返） | 查机票、携程航班、航班查询 |
| [dianping-info-query](skills/dianping-info-query/) | 大众点评商户信息查询 | 大众点评、查店铺、商户评分 |
| [professional-patent-agents](skills/professional-patent-agents/) | 专利撰写与优化多代理套件 | 专利撰写、专利优化、权利要求、技术交底书 |

## Installation

### 方式一：Clone + Symlink（推荐）

Clone 到 `~/.claude/skills/` 下，用 symlink 链接各技能，方便 `git pull` 统一更新：

```bash
# 1. Clone 仓库
git clone https://github.com/seasonstar/super-founder-skills.git ~/.claude/skills/super-founder-skills

# 2. 为每个技能创建 symlink
for skill in wechat-article-writer wechat-formatter-publisher csdn-article-publish smart-illustrator zsxq-publish yunxiao-task-assign yunxiao-weekly-report it-sync ruankao-quiz project-decision-log dingtalk-ai-table dingtalk-docs wukong-knowledge-audit 12306-train-query ctrip-flight-search dianping-info-query professional-patent-agents pm-ruankao-paper-generator; do
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

### wechat-article-writer

微信公众号文章写作辅助，提供选题分析、大纲生成、全文撰写等 AI 辅助写作能力。

无额外配置，开箱即用。

### it-sync

IT 双周汇报与排期同步。自动从钉钉 AI 表格拉取项目数据，生成群通知文案和信息图。

```bash
# 1. 依赖：钉钉 AI 表格 MCP（dingtalk-ai-table）+ 云效 MCP（yunxiao）
# 2. 图片生成 API Key（二选一）：
export ARK_API_KEY="豆包/火山引擎 API Key"        # Seedream 文生图
export DASHSCOPE_API_KEY="阿里云 DashScope API Key" # Qwen 文生图

# 3. 运行时脚本会同步到项目目录 05-AI与自动化/ 下执行
```

### ruankao-quiz

软考（信息系统项目管理师）案例分析速记练习系统，开箱即用。

- 默写题库和找茬题库已内置于 `references/` 目录
- 进度文件 `references/.quiz-progress.json` 自动创建和维护
- 无需额外配置

### dingtalk-ai-table & dingtalk-docs

钉钉 AI 表格 + 云文档操作，通过 mcporter 连接钉钉官方 MCP server。

```bash
# 1. 安装 mcporter
npm install -g mcporter

# 2. 配置 MCP URL（从 https://mcp.dingtalk.com 获取）
mcporter config add dingtalk-ai-table --type streamable-http --url "<你的MCP URL>"
mcporter config add dingtalk-docs --type streamable-http --url "<你的MCP URL>"
```

### wukong-knowledge-audit

钉钉知识库诊断审计，依赖钉钉文档 MCP（dingtalk-docs）。开箱即用，无需额外配置。

### 12306-train-query / ctrip-flight-search / dianping-info-query

出行与本地生活查询类技能，基于浏览器自动化操作，无需额外配置。

### professional-patent-agents

专利撰写与优化多代理套件，覆盖专利申请全流程。

```bash
# 依赖（可选）：
# - exa MCP（web 检索）
# - aminer-data-search（学术/专利检索，需 AMINER_API_KEY）
# - pandoc（Markdown 转 Word）
pip install requests python-docx
```

## 更新技能

```bash
cd ~/.claude/skills/super-founder-skills && git pull
```

使用 symlink 方式安装的，`git pull` 即可同步全部 19 个技能。直接复制方式安装的需重新执行 `cp -r` 覆盖。

## License

MIT
