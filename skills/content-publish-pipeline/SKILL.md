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
| ③ 公众号 | `wechat-formatter-publisher` | 转 HTML + 发布草稿 |
| ④ 星球 | `zsxq-publish` | 发文章分享帖（链接在前风格） |
| ⑤ CSDN | `csdn-article-publish` | 图片转 wmimg + 保存草稿 |

**核心原则：每个子技能的细节由其自身 SKILL.md 决定，本技能只做编排和跨平台一致性保证。不要重新实现子技能的能力。**

---

## ⛔ 强制规则（违反即失败）

1. **发布前必须确认**：③④⑤ 任何一步真正发布前，都要用 AskUserQuestion 问用户「是否继续」，因为发布不可逆。
2. **参数预检**：进入分发阶段前，必须先跑 [预检清单](#预检清单)，任一项不通过就停下报告，不要带着问题硬发。
3. **风格一致性**：同一篇文章三平台的标题、配图、核心内容必须一致，不要各写各的。
4. **CSDN 签名时效**：CSDN 的 `x-ca-signature` 极易过期，更新配置后必须**立即**跑保存，不要间隔。
5. **星球发帖风格**：链接在前 + 一两句简短介绍，见 [星球发帖规范](#星球发帖规范)。

---

## 完整工作流

### 阶段 0：预检清单（分发前必跑）

在开始写作之前或写作完成后、进入分发前，检查各平台就绪状态：

```bash
# 公众号：检查 config.py 有 AppID/AppSecret
grep -E "APP_ID|APP_SECRET" ~/.agents/skills/wechat-formatter-publisher/config.py

# 星球：检查 groups.json 且 token 有效（GET 一次 group info）
node ~/.agents/skills/zsxq-publish/scripts/zsxq.js config list
# token 有效性快速验证（不发帖）：
curl -s "https://api.zsxq.com/v2/groups/<group_id>" -H "cookie: <token>" | head -c 100

# CSDN：检查配置存在（签名是否新鲜见阶段④）
ls ~/.agents/skills/csdn-article-publish/config/csdn_config.json
```

**判断规则：**
- 公众号缺配置 → 停下，让用户填 config.py
- 星球 token 失效（GET 返回 401/code≠succeeded）→ 停下，要新 cookie，按 [星球 cookie 更新](#星球-cookie-更新陷阱) 处理
- CSDN 签名过期 → 不阻塞写作，进入阶段④时再抓

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
2. 分析文章，确定 4 个配图位：封面 + 3 张正文图
3. **封面**用 Qwen（wechat 平台 2.35:1）
4. **正文图**优先用 Excalidraw（概念/对比/流程图），不用 Mermaid
5. 图片输出到 `articles/images/`，命名 `{slug}-cover.png` / `{slug}-image-01.png`
6. **直接 Edit 原 md 文件插入图片引用**，替换头图占位符

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

**3c. 发布草稿**（确认后）
```bash
python ~/.agents/skills/wechat-formatter-publisher/publisher.py "articles/xxx.html"
```
- 会自动上传本地图片到素材库
- **常见错误 40164**：出口 IP 不在白名单 → 让用户去 mp.weixin.qq.com 加白名单后重跑

**输出**：公众号文章链接 `https://mp.weixin.qq.com/s/xxxxx`（**这个链接是阶段④要用的**）

**拿到链接后**：更新 README.md 的文章列表（在该系列末尾追加一条）

---

### 阶段 ④：知识星球发帖

调用 `zsxq-publish` 技能。**用阶段③拿到的公众号链接发分享帖。**

#### 星球发帖规范

```
https://mp.weixin.qq.com/s/xxxxx

一两句简短的痛点或核心介绍，不超过2句话。
```

- 第一行直接贴公众号链接（zsxq 自动渲染成标题卡片）
- 空一行
- 1-2 句简短介绍
- **禁止**：介绍在前链接在后、多段长文、手动重复标题

```bash
node ~/.agents/skills/zsxq-publish/scripts/zsxq.js post --text "<链接>

<简短介绍>"
```

**确认后发布**（发帖不可逆，必须先问用户）。

#### 星球 cookie 更新陷阱 ⚠️

`config add` 把新 cookie 写进一个**新 alias**（按星球名命名），但 `post` 命令读的是 `default` 指向的 alias。如果两者不同，会用到旧 cookie 报 401。

**正确做法**：直接编辑 `~/.xfg-zsxq/groups.json`，把新 cookie 写进 `default` 指向的那个 alias，并确保 `default` 指向真实星球名（如「量策堂·AI算法指标策略」），删掉无意义的 ID 别名。

**401 诊断**：如果 `config list` 能识别星球（GET 成功）但 `post` 报 401，99% 是这个 alias 错位问题，不是签名问题。

---

### 阶段 ⑤：CSDN 草稿

调用 `csdn-article-publish` 技能。**注意：CSDN 需要专用版本文章（图片必须是外链）。**

**5a. 准备 CSDN 专用版**
```bash
cp articles/xxx.md articles/xxx-CSDN版.md
```

**5b. 上传所有图片到 wmimg**（本地 PNG + 远程图都要转）
```bash
python3 ~/.agents/skills/csdn-article-publish/scripts/wmimg_uploader.py <图片绝对路径>
```
- 本地图直接传；远程图先 curl 下载再传
- 每张间隔 3 秒防限流

**5c. 替换 CSDN版.md 里所有图片链接为 wmimg 直链**（用 Edit 逐张替换）

**5d. 验证无本地路径残留**
```python
import re
imgs = re.findall(r'!\[.*?\]\(([^)]+)\)', content)
local = [i for i in imgs if not i.startswith(('http://','https://'))]
assert not local  # 必须为空
```

**5e. 保存草稿**
```bash
node ~/.agents/skills/csdn-article-publish/scripts/csdn_article.js save \
  --config ~/.agents/skills/csdn-article-publish/config/csdn_config.json \
  --title "标题" --file "articles/xxx-CSDN版.md"
```

#### CSDN 签名时效 ⚠️

`x-ca-signature` 是 HMAC 签名，绑定请求 body，**不是长期 token**。每次保存/发布都要新鲜签名。

- **报错 `HMAC signature does not match`（401）**：签名过期或 body 不匹配
- **解决**：让用户去 editor.csdn.net → F12 → Network → 保存任意草稿 → 找 `saveArticle` 请求 → Copy as cURL → 提取 Cookie + x-ca-key/nonce/signature → 更新配置后**立即**重跑（1-2 分钟内）
- **更省事**：CSDN 草稿保存后，让用户直接在编辑器界面手动发布，不必再抓签名跑 publish

---

## 全链路检查清单（全部完成后核对）

发布完成后，逐项确认：

- [ ] 公众号草稿已生成，链接可访问
- [ ] README.md 文章列表已追加新文章
- [ ] 知识星球帖子已发（链接在前风格）
- [ ] CSDN 草稿已保存
- [ ] articles/ 下文章文件齐全（原版 + CSDN版）
- [ ] articles/images/ 下配图齐全
- [ ] 预告的下一篇选题已记录（供下次使用）

---

## 常见问题速查

| 症状 | 根因 | 解决 |
|------|------|------|
| 公众号 40164 | 出口 IP 不在白名单 | mp.weixin.qq.com 加白名单 |
| 星球 config list 成功但 post 报 401 | cookie 写错 alias | 编辑 groups.json，更新 default 指向的 alias |
| CSDN HMAC signature does not match | 签名过期/body 变了 | 重新抓 saveArticle 请求头，立即重跑 |
| 星球帖子风格不对 | 介绍在前链接在后 | 删除重发，链接必须在第一行 |
| 公众号代码块字大松散 | 旧样式 line-height:2 | 确认 themes/claude.py 已是 13px/1.6/overflow-x |
| 配图风格不统一 | 没读 style 文件 | smart-illustrator 必须先读 style-trading-tutorial.md |

---

## 参数速查（本项目）

| 平台 | 配置位置 | 关键参数 |
|------|---------|---------|
| 公众号 | `wechat-formatter-publisher/config.py` | AppID/AppSecret（已内置） |
| 星球 | `~/.xfg-zsxq/groups.json` | cookie token（易过期） |
| CSDN | `csdn-article-publish/config/csdn_config.json` | headers(签名易过期) + wmimg.token |
| 配图 | `smart-illustrator/config` 或 env | DASHSCOPE_API_KEY |

## 使用示例

```
/content-publish-pipeline 写一篇 XX 主题的文章
帮我写一篇关于 XX 的文章，写完发到公众号、星球和 CSDN
全链路：XX 主题
```
