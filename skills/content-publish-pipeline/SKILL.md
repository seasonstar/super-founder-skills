---
name: content-publish-pipeline
description: 内容生产到分发全链路编排技能。从选题/写作→配图→排版→三平台分发（公众号/知识星球/CSDN），编排现有的 5 个子技能，自动完成端到端流程，仅在关键节点确认。
---

# 内容生产分发全链路 (Content Publish Pipeline)

把一篇量化文章从写作到三个平台分发的完整流程编排成一个全自动 pipeline。

## 何时使用

用户说以下任意一句时触发：
- "帮我写一篇文章并分发" / "写完发到公众号/星球/CSDN"
- "全链路发布" / "一键发布"
- "/content-publish-pipeline [主题]"
- 指定主题要求"写完发出去"

## 编排的 5 个子技能（按执行顺序）

| 阶段 | 技能 | 作用 |
|------|------|------|
| ① 写作 | `wechat-article-writer` | 按《以AI量化为生》等系列规范写 Markdown |
| ② 配图 | `smart-illustrator` | 生成封面 + 正文配图，插入文章 |
| ③ 公众号 | `wechat-formatter-publisher` | 转 HTML + 创建草稿，转述后台手动确认清单 |
| ④ 星球 | `zsxq` | `zsxq-cli` 发文章分享帖 / 源码包帖（支持 `--files` 附件），发后核验 |
| ⑤ CSDN | `csdn-article-publish` | 图片自动转 csdnimg + 保存草稿/直接发布，发后线上核验 |

**核心原则：每个子技能的细节由其自身 SKILL.md 决定，本技能只做编排和跨平台一致性保证。不要重新实现子技能的能力。**

> 旧版说明：星球阶段曾用 `zsxq-publish`（zsxq.js + ~/.xfg-zsxq/groups.json），2026-11-20 起本管线统一改用 `zsxq` 技能（zsxq-cli 通道，附件/核验/定时能力更全）。旧技能保留但不再被本管线调用。

---

## ⛔ 强制规则（违反即失败）

1. **发布前必须确认**：③④⑤ 任何一步真正发布前，都要用 AskUserQuestion 问用户「是否继续」，因为发布不可逆。
2. **参数预检**：进入分发阶段前，必须先跑 [预检清单](#预检清单)，任一项不通过就停下报告，不要带着问题硬发。
3. **风格一致性**：同一篇文章三平台的标题、配图、核心内容必须一致，不要各写各的。
4. **CSDN 失败先重试**：`Failed: undefined`（带 Trace ID）多为偶发，先原样重跑一次；连续两次失败再按签名过期处理（重抓 saveArticle 请求头后立即重跑）。2026-11 实测旧配置通常可直接 save+publish。
5. **星球发帖风格**：链接在前 + 一两句简短介绍，见 [星球发帖规范](#阶段-知识星球发帖)。
6. **发布后必须核验**：星球核验附件/图片/链接齐全；CSDN 线上抓正文确认无本地路径死图。核验不过不算完成。

---

## 完整工作流

### 阶段 0：预检清单（分发前必跑）

在开始写作之前或写作完成后、进入分发前，检查各平台就绪状态：

```bash
# 公众号：检查 config.py 有 AppID/AppSecret
grep -E "APP_ID|APP_SECRET" ~/.agents/skills/wechat-formatter-publisher/config.py

# 星球：zsxq-cli 认证有效性（能列出星球即通过）
zsxq-cli group +list

# CSDN：检查配置存在（签名问题留到阶段⑤，失败先重试再重抓）
ls ~/.agents/skills/csdn-article-publish/config/csdn_config.json
```

**判断规则：**
- 公众号缺配置 → 停下，让用户填 config.py
- zsxq-cli 认证失败 → 按 `zsxq` 技能的 `references/auth-errors.md` 处理（不要去改旧 groups.json）
- CSDN 配置缺失 → 停下让用户抓请求头；签名问题不阻塞写作

---

### 阶段 ①：写作

调用 `wechat-article-writer` 技能。关键输入：
- **系列**：以AI量化为生 / 量化指标解码 / 量化策略开发（决定序号和结构）
- **主题**：用户给定

**输出**：`articles/[系列名]：[序号].[标题].md`

**注意**：
- 文章保存到 `articles/` 目录，**不提交 git**
- 必须包含完整 footer（往期回顾用 README.md 真实链接）
- 头图位置先留占位符 `![Header Image](./images/xxx-header.jpg)`，阶段②会替换

---

### 阶段 ②：配图

调用 `smart-illustrator` 技能。流程：
1. 读取 `styles/style-trading-tutorial.md`（量化文章默认此风格）
2. 分析文章，确定配图位：封面 + 正文图（真实图表/配置截图优先于示意图）
3. **封面**用 Qwen（wechat 平台 2.35:1），两版候选（居中聚焦 + 左图右文），逐字核验中文标题后择优
4. **正文图**优先用真实数据渲染/真实截图；概念图用 Excalidraw，不用 Mermaid
5. 图片输出到 `articles/images/`，文件名**不含空格**（CSDN 转存边界）
6. **直接 Edit 原 md 文件插入图片引用**，替换头图占位符；不要用 Obsidian `![[...]]` 嵌图语法

**风格默认**：trading-tutorial（量化金融色板：米白底 + 智能蓝 + 涨红跌绿）

---

### 阶段 ③：公众号发布

调用 `wechat-formatter-publisher` 技能。

**3a. 排版转换**
```bash
python ~/.agents/skills/wechat-formatter-publisher/converter.py "articles/xxx.md" --theme claude
```
- 默认 Claude 风格 + Claude 橙 #D97757
- 代码块样式已优化：13px / 1.6 行距 / 左对齐 / `overflow-x: auto` 横向滚动（见 themes/claude.py）

**3b. 预览确认**：open 生成的 HTML，让用户看排版

**3c. 创建草稿**（确认后）
```bash
python ~/.agents/skills/wechat-formatter-publisher/publisher.py "articles/xxx.html" \
  --manifest "articles/xxx-manifest.json" --cover "articles/images/xxx-cover.png"
```
- 自动上传本地图片到素材库（含 Obsidian 嵌图，converter 会归一化）
- **常见错误 40164**：出口 IP 不在白名单 → 让用户去 mp.weixin.qq.com 加白名单后重跑

**3d. 转述手动确认清单（必须，逐条原样转述）**：原创（文字原创+快捷转载）、合集（按标题匹配，如「量化指标库」）、创作来源（个人观点）、平台推荐（开启）。

**3e. 拿到文章链接后的固定动作**：
1. 更新 README.md 该系列文章列表（标题+链接+要点）
2. commit + push 公开仓库（docs: 补充XX文章链接）

---

### 阶段 ④：知识星球发帖

调用 `zsxq` 技能（zsxq-cli 通道）。先 `zsxq-cli group +list` 拿 group_id。**用阶段③的公众号链接。**

#### 帖型 A：文章分享帖（默认）

```
https://mp.weixin.qq.com/s/xxxxx

一两句简短的痛点或核心介绍，不超过2句话。
```

```bash
zsxq-cli topic +create --group-id <group_id> --text "<链接>

<简短介绍>"
```

- 第一行直接贴公众号链接（zsxq 自动渲染成标题卡片）
- **禁止**：介绍在前链接在后、多段长文、手动重复标题

#### 帖型 B：源码包帖（发布成果包时）

```bash
zsxq-cli topic +create --group-id <group_id> \
  --files "<文章封面.png>,<源码包.zip>" \
  --text "<链接>

<一两句核心介绍>。

附件为完整源码包：<内容一句话>，解压后按 README 安装即可使用。"
```

- **配图默认直接用文章封面**，不新生成卡片（2026-11-18 用户决定）
- 源码包结构惯例：core/integration/scripts/tests/articles/research + README.md + 成果包说明.txt，zip 后附

#### 发帖后核验（必做）

```bash
zsxq-cli group +topics --group-id <group_id>   # 或 topic +detail
```
确认：链接在正文、图片数≥1、附件文件名正确。

⚠️ **topic_id 陷阱**：发帖响应里的 `topic.topic_id` 与列表/详情接口的 topic_id 可能不一致（同帖相差个位数），核验一律以 `group +topics` / `topic +detail` 返回为准，不要拿发帖响应里的 ID 直接查 `/info`。

---

### 阶段 ⑤：CSDN 发布

调用 `csdn-article-publish` 技能。

**5a. 准备 CSDN 专用版**
```bash
cp articles/xxx.md articles/xxx-CSDN版.md
```
再做三处口径调整：
- 「会员专享」措辞改为「完整源码包已发布在知识星球」口径
- Obsidian 嵌图 `![[x.png]]` → `![](x.png)`
- 带空格的图片文件名改为无空格副本（如 `Pasted image xxx.png` → `xxx-note.png`），并同步引用

**5b. 保存草稿（图片自动转 csdnimg）**
```bash
node ~/.agents/skills/csdn-article-publish/scripts/csdn_article.js save \
  --config ~/.agents/skills/csdn-article-publish/config/csdn_config.json \
  --title "标题" --file "articles/xxx-CSDN版.md"
```
- 脚本自动把本地/外链图片转存到 CSDN 图床并替换链接，正文第一张图自动作首图封面
- **转存兜底已内置**：残留未转存引用或 Obsidian 嵌图会直接报错停止，不会把死图发出去
- 首次报 `Failed: undefined` → 原样重跑一次再排查

**5c. 发布（用户确认后）**
```bash
node ~/.agents/skills/csdn-article-publish/scripts/csdn_article.js publish \
  --config ~/.agents/skills/csdn-article-publish/config/csdn_config.json \
  --id <article_id> --title "标题" --file "articles/xxx-CSDN版.md" \
  --extra '{"tags":"量化交易,X,X,X,Python","description":"摘要≤256字","creation_statement":3}'
```
- tags 最多 5 个（文章尾部标签超过 5 个时择要）
- **修改已发布文章**：只能再次 `publish` 覆盖；`update` 会报「已发布文章无法保存草稿」
- 保存/发布间隔 ≥5-10 秒防限流

**5d. 线上核验（必做）**：WebFetch 抓 CSDN 会 521，用 `curl -A "Mozilla/5.0..." <url> | grep csdnimg` 或 web_reader 工具，确认标题/正文/图片全部为 csdnimg 链接、无本地路径残留。

#### CSDN 签名问题 ⚠️

2026-11 实测：旧配置通常可直接 save+publish，签名并非每次都要重抓。
- 偶发 `Failed: undefined`（带 Trace ID）→ 先重试一次
- 连续失败或明确报 `HMAC signature does not match` → 让用户去 editor.csdn.net → F12 → Network → 保存任意草稿 → Copy as cURL 提取 `saveArticle` 请求头（Cookie + x-ca-key/nonce/signature 一整组）→ 更新配置后立即重跑
- 兜底：草稿保存成功后让用户在编辑器界面手动发布

---

## 全链路检查清单（全部完成后核对）

- [ ] 公众号草稿已创建，手动确认清单已逐条转述给用户
- [ ] README.md 文章列表已追加并 commit+push
- [ ] 星球帖子已发（分享帖链接在前 / 源码包帖附件齐全），`group +topics` 核验通过
- [ ] CSDN 已发布，线上核验无本地路径/死图
- [ ] articles/ 下文章文件齐全（原版 + CSDN版）+ images 配图齐全（无空格文件名）
- [ ] 预告的下一篇选题已记录（供下次使用）

---

## 常见问题速查

| 症状 | 根因 | 解决 |
|------|------|------|
| 公众号 40164 | 出口 IP 不在白名单 | mp.weixin.qq.com 加白名单 |
| zsxq-cli 认证失败 | cookie/登录态过期 | 按 zsxq 技能 references/auth-errors.md 处理（别改旧 groups.json） |
| 星球核验查不到帖子 | 拿发帖响应的 topic_id 去查 | 用 group +topics / topic +detail 的 ID 为准 |
| CSDN `Failed: undefined` | 多为偶发 | 原样重跑一次；连续失败再重抓请求头 |
| CSDN 「已发布文章无法保存草稿」 | 对已发布文章用 update | 直接再跑 publish 覆盖 |
| CSDN 正文残留本地图片路径 | 带空格文件名/Obsidian 嵌图（旧版漏洞） | 已内置 fail-hard 拦截；仍建议 CSDN 版预处理成无空格标准语法 |
| WebFetch 抓 CSDN 返回 521 | CSDN 拦非浏览器 UA | curl 带浏览器 UA 或 web_reader 核验 |
| 星球帖子风格不对 | 介绍在前链接在后 | 删除重发，链接必须在第一行 |
| 公众号代码块字大松散 | 旧样式 line-height:2 | 确认 themes/claude.py 已是 13px/1.6/overflow-x |
| 配图风格不统一 | 没读 style 文件 | smart-illustrator 必须先读 style-trading-tutorial.md |

---

## 参数速查（本项目）

| 平台 | 配置位置 | 关键参数 |
|------|---------|---------|
| 公众号 | `wechat-formatter-publisher/config.py` | AppID/AppSecret（已内置） |
| 星球 | zsxq-cli 认证（`zsxq-cli auth login`） | group_id 由 `group +list` 查得 |
| CSDN | `csdn-article-publish/config/csdn_config.json` | headers（Cookie+签名组）；图片缓存 csdn_image_cache.json |
| 配图 | `smart-illustrator/config` 或 env | DASHSCOPE_API_KEY（直连无需代理） |

## 使用示例

```
/content-publish-pipeline 写一篇 XX 主题的文章
帮我写一篇关于 XX 的文章，写完发到公众号、星球和 CSDN
全链路：XX 主题
```
