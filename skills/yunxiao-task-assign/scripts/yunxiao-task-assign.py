#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云效任务分配脚本。

不依赖 Codex MCP 握手，直接调用云效 OpenAPI。配置从 ~/.yunxiao/config.json
读取，鉴权优先使用 YUNXIAO_ACCESS_TOKEN 环境变量，随后回退到配置文件或
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
DEFAULT_PRIORITY = "中"
PRIORITY_CODE = {
    "高": "0",
    "中": "1",
    "低": "2",
    "紧急": "0",
}


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
    config.setdefault("bufferDays", 7)
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


class YunxiaoClient:
    def __init__(self, token: str, base_url: str, organization_id: str) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.organization_id = organization_id
        self.region_edition = is_region_edition(self.base_url)

    def org_path(self, path: str) -> str:
        if self.region_edition:
            return path
        return path.replace("/oapi/v1/", f"/oapi/v1/projex/organizations/{self.organization_id}/", 1)

    def platform_org_path(self, path: str) -> str:
        if self.region_edition:
            return path
        return path.replace("/oapi/v1/platform/", f"/oapi/v1/platform/organizations/{self.organization_id}/", 1)

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
            "User-Agent": "yunxiao-task-assign-openapi/1.0",
            "x-yunxiao-token": self.token,
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise YunxiaoError(f"云效 API 请求失败: {method} {path} -> HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise YunxiaoError(f"云效 API 请求失败: {method} {path} -> {exc}") from exc

        if not payload:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload

    def search_projects(self) -> list[dict[str, Any]]:
        path = self.org_path("/oapi/v1/projects:search" if self.region_edition else "/oapi/v1/projex/projects:search")
        if self.region_edition:
            path = "/oapi/v1/projex/projects:search"
        else:
            path = f"/oapi/v1/projex/organizations/{self.organization_id}/projects:search"
        result = self.request("POST", path, {})
        return result if isinstance(result, list) else []

    def list_sprints(self, project_id: str) -> list[dict[str, Any]]:
        if self.region_edition:
            path = f"/oapi/v1/projex/projects/{project_id}/sprints"
        else:
            path = f"/oapi/v1/projex/organizations/{self.organization_id}/projects/{project_id}/sprints"
        result = self.request("GET", path)
        return result if isinstance(result, list) else []

    def get_work_item_types(self, project_id: str, category: str = "Task") -> list[dict[str, Any]]:
        if self.region_edition:
            path = f"/oapi/v1/projex/projects/{project_id}/workitemTypes"
        else:
            path = f"/oapi/v1/projex/organizations/{self.organization_id}/projects/{project_id}/workitemTypes"
        result = self.request("GET", path, query={"category": category})
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and isinstance(result.get("result"), list):
            return result["result"]
        return []

    def search_organization_members(self, query: str) -> list[dict[str, Any]]:
        if self.region_edition:
            path = "/oapi/v1/platform/members:search"
        else:
            path = f"/oapi/v1/platform/organizations/{self.organization_id}/members:search"
        result = self.request("POST", path, {"page": 1, "perPage": 10, "query": query})
        return result if isinstance(result, list) else []

    def create_work_item(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.region_edition:
            path = "/oapi/v1/projex/workitems"
        else:
            path = f"/oapi/v1/projex/organizations/{self.organization_id}/workitems"
        result = self.request("POST", path, payload)
        return result if isinstance(result, dict) else {"result": result}


def find_project(projects: list[dict[str, Any]], project_name: str) -> dict[str, Any]:
    for project in projects:
        if project.get("name") == project_name:
            return project
    names = ", ".join(str(project.get("name", "Unknown")) for project in projects)
    raise YunxiaoError(f"未找到项目: {project_name}。可用项目: {names or '无'}")


def sprint_timestamp(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def normalize_sprint_name(name: str) -> str:
    return name.replace("Spint", "Sprint").strip()


def choose_sprint(sprints: list[dict[str, Any]], target_name: str | None) -> dict[str, Any] | None:
    if not sprints:
        return None

    sorted_sprints = sorted(sprints, key=lambda item: sprint_timestamp(item.get("startDate")))
    if target_name:
        normalized_target = normalize_sprint_name(target_name)
        for sprint in sorted_sprints:
            if normalize_sprint_name(str(sprint.get("name", ""))) == normalized_target:
                return sprint
        available = ", ".join(str(sprint.get("name", "Unknown")) for sprint in sorted_sprints)
        raise YunxiaoError(f"未找到迭代: {target_name}。可用迭代: {available}")

    now_ms = int(datetime.now().timestamp() * 1000)
    current = [
        sprint
        for sprint in sorted_sprints
        if sprint_timestamp(sprint.get("startDate")) <= now_ms <= sprint_timestamp(sprint.get("endDate"))
    ]
    if current:
        return current[-1]

    upcoming = [sprint for sprint in sorted_sprints if sprint_timestamp(sprint.get("startDate")) > now_ms]
    if upcoming:
        return upcoming[0]

    finished = [sprint for sprint in sorted_sprints if sprint_timestamp(sprint.get("endDate")) < now_ms]
    return finished[-1] if finished else None


def find_assignee(client: YunxiaoClient, members: dict[str, str], name: str) -> str:
    if name in members:
        return members[name]
    result = client.search_organization_members(name)
    if result:
        user_id = result[0].get("userId") or result[0].get("id")
        if user_id:
            return str(user_id)
    valid_names = ", ".join(sorted(members))
    raise YunxiaoError(f"未找到负责人: {name}。配置中可用人员: {valid_names}")


def choose_task_type(types: list[dict[str, Any]]) -> dict[str, Any]:
    enabled = [item for item in types if item.get("enable", True)]
    for item in enabled or types:
        if item.get("category") == "Task" or item.get("name") in {"任务", "Task"}:
            return item
    if types:
        return types[0]
    raise YunxiaoError("未找到 Task 工作项类型，请检查项目工作项配置。")


def work_item_url(project_id: str, work_item: dict[str, Any]) -> str:
    work_item_id = work_item.get("id") or work_item.get("identifier") or work_item.get("workItemId")
    if not work_item_id:
        return "https://devops.aliyun.com/"
    return f"https://devops.aliyun.com/projex/workspace/{project_id}/workitem/{work_item_id}"


def append_deadline(description: str | None, deadline: str | None) -> str | None:
    if not deadline:
        return description
    base = description or ""
    suffix = f"\n\n截止日期：{deadline}" if base else f"截止日期：{deadline}"
    return base + suffix


def send_wecom_notification(webhook_url: str, title: str, assignee: str, priority: str, sprint: str, link: str) -> bool:
    body = {
        "msgtype": "markdown",
        "markdown": {
            "content": (
                "### 新任务分配\n\n"
                f"**任务**: {title}\n"
                f"**负责人**: @{assignee}\n"
                f"**优先级**: {priority}\n"
                f"**迭代**: {sprint}\n\n"
                f"[查看详情]({link})"
            )
        },
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("errcode") == 0
    except Exception:
        return False


def build_payload(
    title: str,
    assignee_id: str,
    project_id: str,
    workitem_type_id: str,
    priority: str,
    sprint_id: str | None,
    description: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "assignedTo": assignee_id,
        "spaceId": project_id,
        "subject": title,
        "workitemTypeId": workitem_type_id,
    }
    if description:
        payload["description"] = description
        payload["formatType"] = "MARKDOWN"
    if sprint_id:
        payload["sprint"] = sprint_id
    if priority in PRIORITY_CODE:
        payload["customFieldValues"] = {"priority": PRIORITY_CODE[priority]}
    return payload


def print_summary(
    title: str,
    assignee: str,
    priority: str,
    sprint_name: str,
    work_item: dict[str, Any],
    link: str,
    notify_ok: bool | None,
    dry_run: bool,
) -> None:
    status = "任务创建预检成功（dry-run，未真正创建）" if dry_run else "任务创建成功"
    print(f"✅ {status}\n")
    print("📋 任务信息")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"标题：{title}")
    print(f"负责人：{assignee}")
    print(f"优先级：{priority}")
    print(f"迭代：{sprint_name}")
    print("状态：待处理")
    if not dry_run:
        item_id = work_item.get("id") or work_item.get("identifier") or work_item.get("workItemId")
        if item_id:
            print(f"ID：{item_id}")
    print("\n🔗 云效链接")
    print(link)
    if notify_ok is True:
        print("\n📢 已推送企微通知到IT群")
    elif notify_ok is False:
        print("\n⚠️ 企微通知推送失败，云效任务本身已创建")


def smoke_test(client: YunxiaoClient, config: dict[str, Any]) -> bool:
    project_name = str(config["projectName"])
    projects = client.search_projects()
    project = find_project(projects, project_name)
    project_id = str(project.get("id"))
    sprints = client.list_sprints(project_id)
    work_item_types = client.get_work_item_types(project_id, "Task")
    task_type = choose_task_type(work_item_types)
    print("✅ 云效 OpenAPI smoke test 通过")
    print(f"组织：{config['organizationId']}")
    print(f"项目：{project_name} ({project_id})")
    print(f"迭代数：{len(sprints)}")
    print(f"Task 类型：{task_type.get('name')} ({task_type.get('id')})")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通过云效 OpenAPI 创建并分配任务")
    parser.add_argument("positional", nargs="*", help="兼容写法：<任务标题> <负责人>")
    parser.add_argument("--title", help="任务标题")
    parser.add_argument("--assignee", help="负责人姓名")
    parser.add_argument("--priority", default=DEFAULT_PRIORITY, choices=sorted(PRIORITY_CODE), help="优先级")
    parser.add_argument("--sprint", help="迭代名称，例如 Sprint 17。默认取当前迭代，无当前迭代则取下一个")
    parser.add_argument("--description", help="任务描述")
    parser.add_argument("--deadline", help="截止日期，会追加到描述中")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="配置文件路径")
    parser.add_argument("--dry-run", action="store_true", help="只做预检，不创建任务")
    parser.add_argument("--no-notify", action="store_true", help="不推送企业微信通知")
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

    title = args.title
    assignee = args.assignee
    if args.positional:
        title = title or args.positional[0]
    if len(args.positional) > 1:
        assignee = assignee or args.positional[1]

    if not title or not assignee:
        raise YunxiaoError("必须提供任务标题和负责人，例如：--title 修复登录bug --assignee 林小鹏")

    project = find_project(client.search_projects(), str(config["projectName"]))
    project_id = str(project.get("id"))
    assignee_id = find_assignee(client, config.get("members", {}), assignee)
    sprint = choose_sprint(client.list_sprints(project_id), args.sprint)
    sprint_id = str(sprint.get("id")) if sprint and sprint.get("id") else None
    sprint_name = str(sprint.get("name")) if sprint else "未指定"
    task_type = choose_task_type(client.get_work_item_types(project_id, "Task"))
    workitem_type_id = str(task_type.get("id"))
    description = append_deadline(args.description, args.deadline)
    payload = build_payload(title, assignee_id, project_id, workitem_type_id, args.priority, sprint_id, description)

    if args.dry_run:
        print_summary(title, assignee, args.priority, sprint_name, {"id": "dry-run"}, "https://devops.aliyun.com/", None, True)
        return 0

    try:
        work_item = client.create_work_item(payload)
    except YunxiaoError:
        if "customFieldValues" not in payload:
            raise
        fallback_payload = dict(payload)
        fallback_payload.pop("customFieldValues", None)
        work_item = client.create_work_item(fallback_payload)

    link = work_item_url(project_id, work_item)
    notify_ok: bool | None = None
    webhook = config.get("wecomWebhook")
    if webhook and not args.no_notify:
        notify_ok = send_wecom_notification(str(webhook), title, assignee, args.priority, sprint_name, link)

    print_summary(title, assignee, args.priority, sprint_name, work_item, link, notify_ok, False)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except YunxiaoError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        raise SystemExit(1)
