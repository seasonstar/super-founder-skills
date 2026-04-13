#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云效周报生成脚本。

直接调用云效 OpenAPI，不依赖 MCP。配置从 ~/.yunxiao/config.json 读取，
鉴权优先使用 YUNXIAO_ACCESS_TOKEN 环境变量，随后回退到配置文件或
~/.codex/config.toml 中的 mcp_servers.yunxiao.env.YUNXIAO_ACCESS_TOKEN。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path.home() / ".yunxiao" / "config.json"
CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
DEFAULT_API_BASE_URL = "https://openapi-rdc.aliyuncs.com"
DEFAULT_BUFFER_DAYS = 7
PRIORITY_ORDER: dict[str, int] = {"紧急": 0, "高": 1, "中": 2, "低": 3}


class YunxiaoError(RuntimeError):
    """Raised when the Yunxiao API call fails."""


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise YunxiaoError(f"配置文件不是合法 JSON: {path} ({exc})") from exc


def load_config(config_path: Path) -> dict[str, Any]:
    config = load_json(config_path)
    config.setdefault("organizationId", "688c88cc9eda9d4e3ee46203")
    config.setdefault("projectName", "业财一体化")
    config.setdefault("bufferDays", DEFAULT_BUFFER_DAYS)
    config.setdefault("members", {})
    return config


def read_codex_token() -> str | None:
    if not CODEX_CONFIG_PATH.exists():
        return None
    content = CODEX_CONFIG_PATH.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r'YUNXIAO_ACCESS_TOKEN\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else None


def resolve_token(config: dict[str, Any]) -> str:
    token = (
        os.environ.get("YUNXIAO_ACCESS_TOKEN")
        or config.get("accessToken")
        or config.get("token")
        or read_codex_token()
    )
    if not token:
        raise YunxiaoError(
            "未找到 YUNXIAO_ACCESS_TOKEN。请设置环境变量，或在 ~/.yunxiao/config.json / "
            "~/.codex/config.toml 中配置。"
        )
    return str(token)


def api_base_url(config: dict[str, Any]) -> str:
    return str(
        os.environ.get("YUNXIAO_API_BASE_URL")
        or config.get("apiBaseUrl")
        or DEFAULT_API_BASE_URL
    ).rstrip("/")


def is_region_edition(base_url: str) -> bool:
    return "openapi-rdc.aliyuncs.com" not in base_url


def format_date(ts_ms: Any) -> str:
    if not ts_ms:
        return "未知"
    try:
        dt = datetime.fromtimestamp(int(ts_ms) / 1000)
        return dt.strftime("%Y年%m月%d日")
    except (ValueError, OSError):
        return "未知"


def sprint_timestamp(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


# ---------------------------------------------------------------------------
# Yunxiao OpenAPI Client
# ---------------------------------------------------------------------------


class YunxiaoClient:
    def __init__(self, token: str, base_url: str, organization_id: str) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.organization_id = organization_id
        self.region_edition = is_region_edition(self.base_url)

    def _projex_path(self, sub_path: str) -> str:
        if self.region_edition:
            return f"/oapi/v1/projex{sub_path}"
        return f"/oapi/v1/projex/organizations/{self.organization_id}{sub_path}"

    def _platform_path(self, sub_path: str) -> str:
        if self.region_edition:
            return f"/oapi/v1/platform{sub_path}"
        return f"/oapi/v1/platform/organizations/{self.organization_id}{sub_path}"

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        url = self.base_url + path
        if query:
            params = {k: v for k, v in query.items() if v is not None}
            if params:
                url += "?" + urllib.parse.urlencode(params, doseq=True)

        data = None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "yunxiao-weekly-report-openapi/1.0",
            "x-yunxiao-token": self.token,
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise YunxiaoError(
                f"云效 API 请求失败: {method} {path} -> HTTP {exc.code}: {error_body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise YunxiaoError(f"云效 API 请求失败: {method} {path} -> {exc}") from exc

        if not payload:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload

    def search_projects(self) -> list[dict[str, Any]]:
        path = self._projex_path("/projects:search")
        result = self.request("POST", path, {})
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and isinstance(result.get("result"), list):
            return result["result"]
        return []

    def list_sprints(self, project_id: str) -> list[dict[str, Any]]:
        path = self._projex_path(f"/projects/{project_id}/sprints")
        result = self.request("GET", path)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and isinstance(result.get("result"), list):
            return result["result"]
        return []

    def search_organization_members(self, query: str) -> list[dict[str, Any]]:
        path = self._platform_path("/members:search")
        result = self.request("POST", path, {"page": 1, "perPage": 10, "query": query})
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            members = result.get("members", result.get("result", []))
            return members if isinstance(members, list) else []
        return []

    def search_workitems(
        self,
        space_id: str,
        category: str = "Req,Task",
        assigned_to: str | None = None,
        sprint_id: str | None = None,
        page: int = 1,
        per_page: int = 200,
    ) -> dict[str, Any]:
        path = self._projex_path("/workitems:search")
        conditions: list[dict[str, Any]] = []
        if assigned_to:
            conditions.append({
                "className": "user",
                "fieldIdentifier": "assignedTo",
                "format": "list",
                "operator": "CONTAINS",
                "toValue": None,
                "value": [assigned_to],
            })
        if sprint_id:
            conditions.append({
                "className": "sprint",
                "fieldIdentifier": "sprint",
                "format": "list",
                "operator": "CONTAINS",
                "toValue": None,
                "value": [sprint_id],
            })
        body: dict[str, Any] = {
            "category": category,
            "spaceId": space_id,
            "page": page,
            "perPage": per_page,
            "orderBy": "gmtCreate",
            "sort": "desc",
        }
        if conditions:
            body["conditions"] = json.dumps({"conditionGroups": [conditions]})
        result = self.request("POST", path, body=body)
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return {"items": result, "pagination": {"total": len(result)}}
        return {"items": [], "pagination": {"total": 0}}


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------


def find_project(projects: list[dict[str, Any]], project_name: str) -> dict[str, Any]:
    for project in projects:
        if project.get("name") == project_name:
            return project
    names = ", ".join(str(p.get("name", "Unknown")) for p in projects)
    raise YunxiaoError(f"未找到项目: {project_name}。可用项目: {names or '无'}")


def choose_report_sprint(
    sprints: list[dict[str, Any]],
    buffer_days: int,
    target_name: str | None = None,
) -> dict[str, Any]:
    if not sprints:
        raise YunxiaoError("项目没有可用的迭代。")

    sorted_sprints = sorted(sprints, key=lambda s: sprint_timestamp(s.get("startDate")))

    if target_name:
        normalized = target_name.replace("Spint", "Sprint").strip()
        for sprint in sorted_sprints:
            name = sprint.get("name", "").replace("Spint", "Sprint").strip()
            if name == normalized:
                return sprint
        available = ", ".join(str(s.get("name", "Unknown")) for s in sorted_sprints)
        raise YunxiaoError(f"未找到迭代: {target_name}。可用迭代: {available}")

    now_ms = int(datetime.now().timestamp() * 1000)
    buffer_ms = buffer_days * 24 * 60 * 60 * 1000

    # "Just ended" sprint: endDate < now <= endDate + buffer
    for sprint in sorted_sprints:
        end = sprint_timestamp(sprint.get("endDate"))
        if end < now_ms <= end + buffer_ms:
            return sprint

    # Fallback: last ended sprint
    ended = [s for s in sorted_sprints if sprint_timestamp(s.get("endDate")) < now_ms]
    if ended:
        return ended[-1]

    return sorted_sprints[-1]


def find_next_sprint(
    sprints: list[dict[str, Any]],
    current_sprint_id: str,
) -> dict[str, Any] | None:
    sorted_sprints = sorted(sprints, key=lambda s: sprint_timestamp(s.get("startDate")))
    for i, sprint in enumerate(sorted_sprints):
        if sprint.get("id") == current_sprint_id and i + 1 < len(sorted_sprints):
            return sorted_sprints[i + 1]
    return None


def get_priority(custom_fields: list[dict[str, Any]] | None) -> str:
    if not custom_fields:
        return "中"
    for field in custom_fields:
        if field.get("fieldId") == "priority":
            values = field.get("values", [])
            if values:
                return values[0].get("displayValue", "中")
    return "中"


def categorize_item(subject: str) -> str:
    if subject.startswith("业财一体化"):
        return "业财一体化"
    if subject.startswith("TK"):
        return "TK数据看板项目"
    if "RPA" in subject:
        return "RPA"
    if subject.startswith("运维"):
        return "运维"
    if subject.startswith("学习"):
        return "学习提升"
    return "其他工作"


def status_completion(status: dict[str, Any]) -> str:
    name = status.get("displayName", status.get("name", ""))
    name_en = status.get("nameEn", "")
    if name_en == "Done" or "已完成" in name:
        return "完成"
    if "设计" in name or name_en == "In Design":
        return "设计阶段"
    if "开发" in name or name_en in ("In Development", "In Progress"):
        return "开发阶段"
    if "测试" in name or name_en == "In Testing":
        return "开发阶段"
    if "进行中" in name or name_en == "In Progress":
        return "开发阶段"
    return ""


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def format_member_report(
    member_name: str,
    sprint: dict[str, Any],
    next_sprint: dict[str, Any] | None,
    current_items: list[dict[str, Any]],
    next_items: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    sprint_name = sprint.get("name", "未知")
    start = format_date(sprint.get("startDate"))
    end = format_date(sprint.get("endDate"))
    lines.append(f"汇报人：{member_name}")
    lines.append(f"汇报周期：{start} - {end}（{sprint_name}）")
    lines.append("")

    # ---- Core achievements (from current sprint) ----
    done_by_cat: dict[str, list[tuple[str, str]]] = {}
    wip_by_cat: dict[str, list[tuple[str, str, str]]] = {}

    for item in current_items:
        subject = item.get("subject", "无标题")
        priority = get_priority(item.get("customFieldValues"))
        completion = status_completion(item.get("status", {}))
        cat = categorize_item(subject)
        if completion == "完成":
            done_by_cat.setdefault(cat, []).append((subject, priority))
        elif completion:
            wip_by_cat.setdefault(cat, []).append((subject, priority, completion))

    lines.append("一、核心成果")
    all_cats = list(dict.fromkeys(list(done_by_cat) + list(wip_by_cat)))
    has_achievements = False
    for cat in all_cats:
        entries: list[tuple[str, str, str]] = []
        for subj, pri in done_by_cat.get(cat, []):
            entries.append((subj, pri, "完成"))
        for subj, pri, comp in wip_by_cat.get(cat, []):
            entries.append((subj, pri, comp))
        if entries:
            has_achievements = True
            lines.append(f"【{cat}】")
            for i, (subj, pri, comp) in enumerate(entries, 1):
                tag = f" 【{pri}】" if pri in ("紧急", "高") else ""
                lines.append(f"{i}. {subj} - {comp}{tag}")
            lines.append("")

    if not has_achievements:
        lines.append("（无）")
        lines.append("")

    # ---- Next sprint plan ----
    lines.append("二、下周期计划")
    if next_sprint:
        ns_name = next_sprint.get("name", "未知")
        ns_start = format_date(next_sprint.get("startDate"))
        ns_end = format_date(next_sprint.get("endDate"))
        lines.append(f"（{ns_name}：{ns_start} - {ns_end}）")

    next_by_cat: dict[str, list[tuple[str, str, str]]] = {}
    for item in next_items:
        subject = item.get("subject", "无标题")
        priority = get_priority(item.get("customFieldValues"))
        completion = status_completion(item.get("status", {}))
        cat = categorize_item(subject)
        next_by_cat.setdefault(cat, []).append((subject, priority, completion))

    has_plan = False
    for cat, items in next_by_cat.items():
        items.sort(key=lambda x: (0 if x[2] else 1, PRIORITY_ORDER.get(x[1], 2)))
        if items:
            has_plan = True
            lines.append(f"【{cat}】")
            for i, (subj, pri, comp) in enumerate(items, 1):
                tag = f" 【{pri}】" if pri in ("紧急", "高") else ""
                comp_str = f" - {comp}" if comp else ""
                lines.append(f"{i}. {subj}{comp_str}{tag}")
            lines.append("")

    if not has_plan:
        lines.append("（暂无计划）")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# WeChat notification
# ---------------------------------------------------------------------------


def send_wecom_notification(webhook_url: str, content: str) -> bool:
    body = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("errcode") == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


def smoke_test(client: YunxiaoClient, config: dict[str, Any]) -> bool:
    project_name = str(config["projectName"])
    projects = client.search_projects()
    project = find_project(projects, project_name)
    project_id = str(project.get("id"))
    sprints = client.list_sprints(project_id)
    members = config.get("members", {})
    print("云效 OpenAPI smoke test 通过")
    print(f"组织：{config.get('organizationId')}")
    print(f"项目：{project_name} ({project_id})")
    print(f"迭代数：{len(sprints)}")
    print(f"团队成员：{len(members)} 人")
    if sprints:
        latest = max(sprints, key=lambda s: sprint_timestamp(s.get("startDate")))
        print(f"最新迭代：{latest.get('name')} ({format_date(latest.get('startDate'))} - {format_date(latest.get('endDate'))})")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通过云效 OpenAPI 生成周报")
    parser.add_argument("--member", help="指定成员姓名，不指定则生成全体周报")
    parser.add_argument("--sprint", help="指定迭代名称，默认为刚过去的迭代")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="配置文件路径")
    parser.add_argument("--no-notify", action="store_true", help="不推送企微通知")
    parser.add_argument("--dry-run", action="store_true", help="只做预检，不生成周报")
    parser.add_argument("--smoke-test", action="store_true", help="只验证云效 OpenAPI 连通性")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config).expanduser())
    token = resolve_token(config)
    client = YunxiaoClient(token, api_base_url(config), str(config["organizationId"]))

    if args.smoke_test:
        smoke_test(client, config)
        return 0

    # Find project
    project = find_project(client.search_projects(), str(config["projectName"]))
    project_id = str(project.get("id"))

    # List sprints, determine target and next
    sprints = client.list_sprints(project_id)
    buffer_days = int(config.get("bufferDays", DEFAULT_BUFFER_DAYS))
    target_sprint = choose_report_sprint(sprints, buffer_days, args.sprint)
    target_sprint_id = str(target_sprint.get("id"))
    next_sprint = find_next_sprint(sprints, target_sprint_id)

    # Determine members
    all_members: dict[str, str] = dict(config.get("members", {}))
    if args.member:
        if args.member in all_members:
            target_members: dict[str, str] = {args.member: all_members[args.member]}
        else:
            found = client.search_organization_members(args.member)
            if found:
                user_id = found[0].get("userId") or found[0].get("id")
                if user_id:
                    target_members = {args.member: str(user_id)}
                else:
                    raise YunxiaoError(f"未找到负责人: {args.member}")
            else:
                valid = ", ".join(sorted(all_members))
                raise YunxiaoError(f"未找到负责人: {args.member}。配置中可用人员: {valid}")
    else:
        target_members = all_members

    if args.dry_run:
        print("周报预检通过（dry-run）")
        print(f"项目：{config['projectName']} ({project_id})")
        print(f"目标迭代：{target_sprint.get('name')} ({format_date(target_sprint.get('startDate'))} - {format_date(target_sprint.get('endDate'))})")
        if next_sprint:
            print(f"下个迭代：{next_sprint.get('name')}")
        print(f"汇报人员：{', '.join(target_members.keys())}")
        return 0

    # Print header
    sep = "=" * 40
    print(sep)
    if len(target_members) == 1:
        print(f"【{list(target_members.keys())[0]}】周报")
    else:
        print("团队周报汇总")
        print(f"{format_date(target_sprint.get('startDate'))} - {format_date(target_sprint.get('endDate'))}")
    print(sep)
    print()

    total_completed = 0
    total_in_progress = 0
    total_pending = 0
    reports: list[tuple[str, str]] = []

    for name, user_id in target_members.items():
        cur_result = client.search_workitems(
            space_id=project_id, assigned_to=user_id, sprint_id=target_sprint_id,
        )
        cur_items = cur_result.get("items", [])

        next_items: list[dict[str, Any]] = []
        if next_sprint:
            nxt_result = client.search_workitems(
                space_id=project_id, assigned_to=user_id,
                sprint_id=str(next_sprint.get("id")),
            )
            next_items = nxt_result.get("items", [])

        # Statistics
        for item in cur_items:
            comp = status_completion(item.get("status", {}))
            if comp == "完成":
                total_completed += 1
            elif comp:
                total_in_progress += 1

        for item in next_items:
            comp = status_completion(item.get("status", {}))
            if not comp:
                total_pending += 1
            elif comp != "完成":
                total_in_progress += 1

        report = format_member_report(name, target_sprint, next_sprint, cur_items, next_items)
        reports.append((name, report))

        if len(target_members) > 1:
            print("-" * 40)
            print(f"【{name}】")
        print(report)
        print()

    # Summary
    print(sep)
    print(f"统计：已完成 {total_completed} | 进行中 {total_in_progress} | 待处理 {total_pending}")
    print(sep)

    # WeChat notification
    if not args.no_notify:
        webhook = config.get("wecomWebhook")
        if webhook:
            if len(reports) == 1:
                content = f"### 【{reports[0][0]}】周报\n\n{reports[0][1]}"
            else:
                parts = [f"### 【{name}】周报\n\n{report}" for name, report in reports]
                content = "\n\n---\n\n".join(parts)
            ok = send_wecom_notification(str(webhook), content)
            if ok:
                print("\n已推送企微通知到IT群")
            else:
                print("\n企微通知推送失败")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except YunxiaoError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
