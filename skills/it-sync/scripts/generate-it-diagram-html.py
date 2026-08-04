#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT 双周会排期配图 —— HTML+CSS 渲染（推荐方案）

用代码渲染替代文生图，确保中文文字、百分比、日期 100% 准确。
依赖：Node.js + puppeteer（全局安装即可）。
业务内容请在 it_diagram_sync_config.py 修改，本脚本一般不用改。
"""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from it_diagram_sync_config import (
    SYNC_ISSUE,
    SYNC_PERIOD,
    NEXT_SYNC_HINT,
    TRACK1_LABEL,
    TRACK1_TEAM,
    TRACK1_INTAKE_LINE,
    TRACK1_PROJECTS,
    TRACK2_LABEL,
    TRACK2_TEAM,
    TRACK2_INTAKE_LINE,
    TRACK2_PROJECTS,
    TRACK2_QUEUE,
    BACKGROUND_ONE_LINE,
    POLICY_ONE_LINE,
    build_sync_notice_text,
)

OUTPUT_HTML = "IT资源管理排期图.html"
OUTPUT_PNG = "IT资源管理排期图.png"


# ---- Node.js puppeteer 渲染脚本 ----
RENDER_SCRIPT = r"""
import { createRequire } from "module";
const require = createRequire(import.meta.url);

// 从全局 node_modules 解析 puppeteer（含嵌套在 mermaid-cli 等包中的情况）
const globalRoots = [
  "/opt/homebrew/lib/node_modules",
  "/usr/local/lib/node_modules",
  process.env.HOME + "/.npm-global/lib/node_modules",
];
const nestedHints = [
  "@mermaid-js/mermaid-cli/node_modules",
  "",
];
let puppeteer = null;
outer:
for (const root of globalRoots) {
  for (const hint of nestedHints) {
    try {
      puppeteer = require(root + "/" + hint + "/puppeteer");
      break outer;
    } catch {}
  }
}
if (!puppeteer) {
  // 尝试本地 node_modules
  try { puppeteer = require("puppeteer"); } catch {}
}
if (!puppeteer) {
  console.error("找不到 puppeteer，请运行: npm install -g puppeteer");
  process.exit(1);
}

const htmlPath = process.argv[2];
const pngPath = process.argv[3];
const htmlUrl = "file://" + htmlPath;

const browser = await puppeteer.launch({
  headless: "new",
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
await page.goto(htmlUrl, { waitUntil: "networkidle0" });
// 额外等待确保字体渲染完成
await new Promise(r => setTimeout(r, 500));

// 截取完整页面（高度自适应，不被 1080 裁剪）
await page.screenshot({
  path: pngPath,
  fullPage: true,
  type: "png",
});

await browser.close();
console.log("PNG saved: " + pngPath);
"""


def parse_projects(raw: str) -> list[dict]:
    """将 config 中的多行项目文本解析为结构化数据。

    格式: N. **项目名** — 状态（进度 XX%），[延期，]计划至 YYYY-MM-DD
    """
    projects = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # 去掉前缀序号 "N. "
        if ". " in line:
            line = line.split(". ", 1)[1]

        # 提取项目名（** ** 包裹）
        name = ""
        if "**" in line:
            parts = line.split("**")
            if len(parts) >= 3:
                name = parts[1]

        # 提取版本号（v1.0 / v1.1 等，紧跟在 **项目名** 后面）
        import re as _re
        version = ""
        vm = _re.search(r'\*\*\s*v(\d+(?:\.\d+)*)', line)
        if vm:
            version = "v" + vm.group(1)
        elif _re.search(r'v(\d+(?:\.\d+)*)', line.split("**")[-1] if "**" in line else line):
            vm2 = _re.search(r'v(\d+(?:\.\d+)*)', line.split("**")[-1] if "**" in line else line)
            version = "v" + vm2.group(1)

        # 延期标记
        delayed = "延期" in line

        # 进度
        progress = None
        if "进度" in line:
            pidx = line.find("进度")
            seg = line[pidx:]
            for ch in seg:
                if ch.isdigit():
                    # 提取数字
                    num_str = ""
                    i = line.index(ch, pidx)
                    while i < len(line) and line[i].isdigit():
                        num_str += line[i]
                        i += 1
                    if num_str:
                        progress = int(num_str)
                    break

        # 状态
        if "开发中" in line:
            status = "开发中"
        elif "未开始" in line:
            status = "未开始"
        elif "设计中" in line:
            status = "设计中"
        elif "测试中" in line:
            status = "测试中"
        else:
            status = "进行中"

        # 日期
        date = ""
        if "计划至" in line:
            didx = line.find("计划至")
            seg = line[didx:]
            for i, ch in enumerate(seg):
                if ch.isdigit() and i + 9 < len(seg):
                    candidate = seg[i : i + 10]
                    if candidate.count("-") == 2 and candidate[:4].isdigit():
                        date = candidate
                        break
        if not date:
            date = "待定"

        projects.append(
            {
                "name": name.strip(),
                "version": version,
                "status": status,
                "progress": progress,
                "delayed": delayed,
                "date": date,
            }
        )
    return projects


def status_class(status: str, delayed: bool) -> str:
    """返回状态标签的 CSS 类名。"""
    if delayed:
        return "tag-delayed"
    if status == "未开始":
        return "tag-pending"
    return "tag-active"


def status_label(status: str, delayed: bool) -> str:
    """返回状态标签文本。"""
    if delayed:
        return f"{status} · 延期"
    return status


def render_project_card(p: dict, index: int) -> str:
    """渲染单个项目卡片 HTML。"""
    delay_class = " project-delayed" if p["delayed"] else ""
    tag_cls = status_class(p["status"], p["delayed"])
    tag_text = status_label(p["status"], p["delayed"])

    # 进度条
    if p["progress"] is not None:
        pct = p["progress"]
        bar_html = f"""
            <div class="progress-wrap">
                <div class="progress-track">
                    <div class="progress-fill {'fill-delayed' if p['delayed'] else ''}" style="width:{pct}%"></div>
                </div>
                <span class="progress-text">{pct}%</span>
            </div>"""
    else:
        bar_html = '<div class="progress-wrap"><div class="progress-track"></div><span class="progress-text progress-na">—</span></div>'

    version_html = f'<span class="version-badge">{p["version"]}</span>' if p.get("version") else ""

    return f"""
          <div class="project-card{delay_class}">
            <div class="project-top">
              <span class="project-name">{index}. {p['name']}</span>
              <span class="project-tags">
                {version_html}
                <span class="status-tag {tag_cls}">{tag_text}</span>
              </span>
            </div>
            {bar_html}
            <div class="project-date">计划至 <strong>{p['date']}</strong></div>
          </div>"""


def render_track(label: str, team: str, intake: str, projects_raw: str, accent: str) -> str:
    """渲染单个轨道（左/右栏）HTML。"""
    projects = parse_projects(projects_raw)
    cards = "\n".join(render_project_card(p, i + 1) for i, p in enumerate(projects))
    return f"""
        <div class="track-col track-{accent}">
          <div class="track-header">
            <div class="track-label">{label}</div>
            <div class="track-meta">
              <span class="team-badge">👤 {team}</span>
            </div>
          </div>
          <div class="intake-line">📋 {intake}</div>
          <div class="project-list">
{cards}
          </div>
        </div>"""


def build_html() -> str:
    """生成完整 HTML 文件内容。"""
    track1_html = render_track(TRACK1_LABEL, TRACK1_TEAM, TRACK1_INTAKE_LINE, TRACK1_PROJECTS, "blue")
    track2_html = render_track(TRACK2_LABEL, TRACK2_TEAM, TRACK2_INTAKE_LINE, TRACK2_PROJECTS, "green")

    queue_text = TRACK2_QUEUE if TRACK2_QUEUE.strip() != "无" else "无"

    return textwrap.dedent("""\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
    background: #EEF2F7;
    width: 100%;
    color: #1A2B4A;
    -webkit-font-smoothing: antialiased;
  }

  .container {
    width: 100%;
    max-width: 1920px;
    margin: 0 auto;
    min-height: 100vh;
    padding: 36px 48px 28px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  /* ---- Header ---- */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 18px;
    border-bottom: 2px solid #D0D9E8;
  }
  .header-left h1 {
    font-size: 48px;
    font-weight: 700;
    color: #0F1E36;
    letter-spacing: 1px;
  }
  .header-left .subtitle {
    font-size: 26px;
    color: #5A6B85;
    margin-top: 8px;
  }
  .header-right {
    text-align: right;
  }
  .issue-badge {
    display: inline-block;
    background: #2D6CDF;
    color: #fff;
    font-size: 36px;
    font-weight: 700;
    padding: 10px 36px;
    border-radius: 10px;
  }
  .period-text {
    font-size: 26px;
    color: #5A6B85;
    margin-top: 10px;
  }
  .next-sync {
    font-size: 22px;
    color: #8896AC;
    margin-top: 6px;
  }

  /* ---- Main 双栏 ---- */
  .main {
    flex: 1;
    display: flex;
    gap: 24px;
    min-height: 0;
  }

  .track-col {
    flex: 1;
    min-width: 0;
    background: #fff;
    border-radius: 14px;
    padding: 24px 22px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    box-shadow: 0 2px 12px rgba(30, 50, 80, 0.06);
  }

  .track-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 10px;
    border-bottom: 2px solid;
  }
  .track-blue .track-header { border-color: #2D6CDF; }
  .track-green .track-header { border-color: #0EA371; }

  .track-label {
    font-size: 34px;
    font-weight: 700;
  }
  .track-blue .track-label { color: #2D6CDF; }
  .track-green .track-label { color: #0EA371; }

  .team-badge {
    font-size: 24px;
    color: #4A5A75;
    background: #F0F3F8;
    padding: 8px 18px;
    border-radius: 8px;
    font-weight: 500;
  }

  .intake-line {
    font-size: 22px;
    color: #6A7A95;
    background: #F7F9FC;
    padding: 12px 20px;
    border-radius: 8px;
    border-left: 4px solid #C5D0E0;
  }

  /* ---- 项目卡片 ---- */
  .project-list {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .project-card {
    background: #FAFBFD;
    border-radius: 10px;
    padding: 18px 22px;
    border: 1px solid #E8EDF4;
    border-left: 5px solid #C5D0E0;
  }
  .project-delayed {
    border-left-color: #F59E0B;
    background: #FFFBF3;
  }

  .project-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 12px;
  }
  .project-name {
    font-size: 26px;
    font-weight: 600;
    color: #1A2B4A;
    flex: 1;
    min-width: 0;
    word-break: break-word;
    line-height: 1.3;
  }

  .project-tags {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .version-badge {
    font-size: 19px;
    font-weight: 600;
    padding: 5px 16px;
    border-radius: 14px;
    white-space: nowrap;
    background: #E8F5EE;
    color: #0EA371;
  }

  .status-tag {
    font-size: 19px;
    font-weight: 600;
    padding: 5px 16px;
    border-radius: 14px;
    white-space: nowrap;
  }
  .tag-active {
    background: #E0EDFF;
    color: #2D6CDF;
  }
  .tag-pending {
    background: #EEF0F4;
    color: #8896AC;
  }
  .tag-delayed {
    background: #FFF3D6;
    color: #B87A00;
  }

  .progress-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
  }
  .progress-track {
    flex: 1;
    height: 14px;
    background: #E8EDF4;
    border-radius: 7px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #2D6CDF, #5B9CFF);
    border-radius: 7px;
    transition: width 0.3s;
  }
  .fill-delayed {
    background: linear-gradient(90deg, #F59E0B, #FBBF24);
  }
  .progress-text {
    font-size: 22px;
    font-weight: 600;
    color: #4A5A75;
    min-width: 64px;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
  .progress-na {
    color: #B0BCCF;
    font-weight: 400;
  }

  .project-date {
    font-size: 22px;
    color: #6A7A95;
  }
  .project-date strong {
    color: #2D6CDF;
    font-variant-numeric: tabular-nums;
  }

  /* ---- Footer ---- */
  .footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 14px;
    border-top: 1px solid #D0D9E8;
  }
  .footer-text {
    font-size: 22px;
    color: #7A8BA5;
    max-width: 75%;
    line-height: 1.5;
  }
  .footer-queue {
    font-size: 22px;
    color: #5A6B85;
    background: #F0F3F8;
    padding: 10px 20px;
    border-radius: 8px;
    white-space: nowrap;
  }
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <h1>IT 资源管理与需求排期</h1>
      <div class="subtitle">双周同步看板 · 各部门业务负责人参考</div>
    </div>
    <div class="header-right">
      <div class="issue-badge">第 """ + str(SYNC_ISSUE) + """ 期</div>
      <div class="period-text">""" + SYNC_PERIOD + """</div>
      <div class="next-sync">下次同步：""" + NEXT_SYNC_HINT + """</div>
    </div>
  </div>

  <!-- 双轨道 -->
  <div class="main">""" + track1_html + track2_html + """
  </div>

  <!-- Footer -->
  <div class="footer">
    <div class="footer-text">""" + POLICY_ONE_LINE + """</div>
    <div class="footer-queue">排队 / 待确认排期：""" + queue_text + """</div>
  </div>

</div>
</body>
</html>""")


def find_node() -> str:
    """查找可用的 node 路径。"""
    for candidate in ["/opt/homebrew/bin/node", "/usr/local/bin/node", "node"]:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    print("❌ 找不到 Node.js，请先安装：brew install node")
    sys.exit(1)


def render_png(html_path: str, png_path: str) -> None:
    """用 puppeteer 将 HTML 渲染为 PNG。"""
    node = find_node()

    # 写入临时 .mjs 脚本
    render_mjs = Path("_render_diagram.mjs")
    render_mjs.write_text(RENDER_SCRIPT, encoding="utf-8")

    abs_html = str(Path(html_path).resolve())
    abs_png = str(Path(png_path).resolve())

    try:
        result = subprocess.run(
            [node, str(render_mjs), abs_html, abs_png],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"❌ Puppeteer 渲染失败:\n{result.stderr}")
            sys.exit(1)
        if result.stdout:
            print(result.stdout.strip())
    finally:
        render_mjs.unlink(missing_ok=True)


def main() -> None:
    print("=" * 60)
    print("【发群简短通知 —— 可与配图一起发】")
    print("=" * 60)
    print(build_sync_notice_text())
    print("=" * 60)
    print()

    # 生成 HTML
    html = build_html()
    Path(OUTPUT_HTML).write_text(html, encoding="utf-8")
    print(f"✅ HTML 已生成: {OUTPUT_HTML}")

    # 渲染 PNG
    print("正在渲染 PNG（Puppeteer），请稍候...")
    render_png(OUTPUT_HTML, OUTPUT_PNG)
    print(f"✅ PNG 已生成: {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
