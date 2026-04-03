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

```bash
# Clone to Claude Code skills directory
git clone https://github.com/seasonstar/super-founder-skills.git
cp -r super-founder-skills/skills/* ~/.claude/skills/
```

## Configuration

部分技能需要配置 API 密钥才能使用：

- **wechat-formatter-publisher**: 复制 `config.example.py` 为 `config.py`，填入公众号 AppID/AppSecret
- **csdn-article-publish**: 复制 `config/config_example.json` 为 `config/csdn_config.json`，填入 CSDN Cookie 和签名
- **smart-illustrator**: 运行 `bun install` 安装依赖
- **zsxq-publish**: 参考各技能目录下的 README/SKILL.md
- **yunxiao-task-assign / yunxiao-weekly-report**: 需配置 `alibabacloud-devops-mcp-server` MCP server 和 `YUNXIAO_ACCESS_TOKEN` 环境变量，用于访问阿里云云效 API

## License

MIT
