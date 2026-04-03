# -*- coding: utf-8 -*-
"""
云效迭代周报生成（优化版）
- 去除固定工作项
- 优化进度显示（智能标注"设计阶段"、"开发阶段"）
- 按照新的"项目-任务项-进度"格式生成
"""

import json
import os
import subprocess
import sys
import requests
from datetime import datetime

# 设置UTF-8编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 用户ID映射（固定，已从云效API核实）
USER_MAP = {
    "林小鹏": "68919fcf46600729fe23828c",
    "佘溢钶": "62be61bb29d72730d91006d9",
    "赖武法": "68b540eb88ec6bebc2d240bb",
    "李铭发": "63ae357da5d2aaf80f0ddab9",
    "龚宏飞": "6891a3395c231c362c0ed181",
    "邹凯平": "6915855722061217a25ea590"
}

# 固定项目名称
FIXED_PROJECT_NAME = "业财一体化"
ORG_ID = "688c88cc9eda9d4e3ee46203"

# 所有用户列表（用于批量查询）
ALL_USERS = ["林小鹏", "佘溢钶", "赖武法", "李铭发", "龚宏飞", "邹凯平"]


def run_mcporter(tool, params=None, debug=False):
    """调用 mcporter 执行云效 API"""
    cmd_str = f'mcporter --config ~/.openclaw/workspace/config/mcporter.json call yunxiao.{tool} --output json'
    if params:
        for key, value in params.items():
            if isinstance(value, list):
                cmd_str += f' {key}={json.dumps(value)}'
            elif isinstance(value, bool):
                cmd_str += f' {key}={str(value).lower()}'
            elif isinstance(value, str) and ' ' in value:
                cmd_str += f' {key}="{value}"'
            else:
                cmd_str += f' {key}={value}'
    
    if debug:
        print(f" [DEBUG] 执行命令: {cmd_str}")
    
    try:
        result = subprocess.run(cmd_str, capture_output=True, text=True, encoding='utf-8', timeout=120, shell=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error calling {tool}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None


def timestamp_to_date(ts):
    """毫秒时间戳转日期字符串"""
    dt = datetime.fromtimestamp(ts / 1000)
    return dt.strftime("%Y年%m月%d日")


def get_user_id(user_name):
    """获取用户ID"""
    # 先检查映射表
    if user_name in USER_MAP:
        return USER_MAP[user_name]
    
    # 搜索组织成员（使用正确的参数格式）
    result = run_mcporter("search_organization_members", {
        "organizationId": ORG_ID,
        "query": user_name,
        "perPage": 10
    })
    
    if result and isinstance(result, list) and len(result) > 0:
        user_id = result[0].get("userId")
        # 缓存到映射表
        USER_MAP[user_name] = user_id
        print(f"  找到用户: {user_name} (ID: {user_id})")
        return user_id
    
    print(f"  ✗ 未找到用户: {user_name}")
    return None


def get_current_user():
    """获取当前用户信息"""
    return run_mcporter("get_current_organization_info")


def get_projects(org_id):
    """获取可访问的项目，返回指定的'业财一体化'项目"""
    result = run_mcporter("search_projects", {
        "organizationId": org_id
    })
    
    if not result or not isinstance(result, list):
        return []
    
    # 查找固定项目名称
    for project in result:
        if project.get("name") == FIXED_PROJECT_NAME:
            print(f"✓ 找到项目: {FIXED_PROJECT_NAME}")
            return [project]
    
    print(f"✗ 错误: 未找到项目 '{FIXED_PROJECT_NAME}'")
    print(f"   可用项目: {', '.join([p.get('name', 'Unknown') for p in result])}")
    return []


def get_current_sprint(sprints, target_sprint_name=None):
    """根据当前日期或指定的迭代名称获取对应的迭代
    返回：(目标迭代, 下一个迭代, 匹配原因)
    
    参数:
        sprints: 迭代列表
        target_sprint_name: 指定的迭代名称（如 "Sprint 15"），None 则获取"刚刚过去的迭代"
    """
    now = datetime.now()
    current_timestamp = now.timestamp() * 1000
    buffer_days = 7  # 7天缓冲期
    buffer_ms = buffer_days * 24 * 60 * 60 * 1000
    
    # 按开始时间排序
    sorted_sprints = sorted(sprints, key=lambda x: x.get("startDate", 0))
    
    target_sprint = None
    next_sprint = None
    match_reason = None
    
    # 如果指定了迭代名称
    if target_sprint_name:
        # 精确匹配迭代名称（支持 "Sprint 16" 或 "Spint 16"）
        for i, sprint in enumerate(sorted_sprints):
            sprint_name = sprint.get("name", "")
            # 标准化名称（统一为 "Sprint"）
            normalized_sprint_name = sprint_name.replace("Spint", "Sprint")
            normalized_target_name = target_sprint_name.replace("Spint", "Sprint")
            
            if normalized_sprint_name == normalized_target_name:
                target_sprint = sprint
                match_reason = f"specified_{normalized_target_name}"
                # 下一个迭代
                if i + 1 < len(sorted_sprints):
                    next_sprint = sorted_sprints[i + 1]
                break
        
        if not target_sprint:
            print(f"✗ 错误: 未找到迭代 '{target_sprint_name}'")
            print(f"   可用迭代: {', '.join([s.get('name', 'Unknown') for s in sorted_sprints])}")
            return None, None, None
        
        return target_sprint, next_sprint, match_reason
    
    # 未指定迭代：查找"刚刚过去的迭代"（已结束且在缓冲期内的迭代）
    print(f"  [DEBUG] 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for i, sprint in enumerate(sorted_sprints):
        end = sprint.get("endDate", 0)
        start = sprint.get("startDate", 0)
        sprint_name = sprint.get("name", "")
        
        # 计算结束时间 + 缓冲
        end_with_buffer = end + buffer_ms
        
        # 判断条件：
        # 1. 迭代已结束 (end < now)
        # 2. 在缓冲期内 (now <= end + buffer)
        # 3. 不是未来的迭代 (end < now + buffer * 1 * 24 * 60 * 60 * 1000)
        
        is_finished = end < current_timestamp
        is_in_buffer = current_timestamp <= end_with_buffer
        is_not_future = end < (current_timestamp + buffer_days * 24 * 60 * 60 * 1000)
        
        if is_finished and is_in_buffer and is_not_future:
            target_sprint = sprint
            match_reason = "just_finished"
            print(f"  [DEBUG] 找到迭代: {sprint_name} (结束时间: {datetime.fromtimestamp(end/1000).strftime('%Y-%m-%d')})")
            # 下一个迭代
            if i + 1 < len(sorted_sprints):
                next_sprint = sorted_sprints[i + 1]
            break
    
    # 如果找不到（可能太久了），取最后一个已结束的迭代
    if not target_sprint and sorted_sprints:
        # 过滤掉还没结束的迭代
        finished_sprints = [s for s in sorted_sprints if s.get("endDate", 0) < current_timestamp]
        if finished_sprints:
            target_sprint = finished_sprints[-1]  # 最后一个结束的
            match_reason = "latest_finished"
            print(f"  [DEBUG] 找不到缓冲期内的迭代，使用最后一个已结束: {target_sprint.get('name')}")
            # 下一个迭代
            target_index = sorted_sprints.index(target_sprint)
            if target_index + 1 < len(sorted_sprints):
                next_sprint = sorted_sprints[target_index + 1]
    
    if target_sprint:
        print(f"  [DEBUG] 最终选择迭代: {target_sprint.get('name')} (ID: {target_sprint.get('id')})")
    else:
        print(f"  [DEBUG] 未能确定迭代")
    
    return target_sprint, next_sprint, match_reason


def get_sprints(org_id, project_id):
    """获取项目的迭代列表（包含ID）"""
    # list_sprints 不返回ID，需要从workitems中提取
    result = run_mcporter("list_sprints", {
        "organizationId": org_id,
        "id": project_id
    })
    
    if not result or not isinstance(result, list):
        print(f"  [DEBUG] list_sprints 返回: {result}")
        return []
    
    # 尝试从工作项中获取迭代ID
    workitems_result = run_mcporter("search_workitems", {
        "organizationId": org_id,
        "spaceId": project_id,
        "category": "Req",
        "perPage": 100
    })
    
    # 构建迭代名称到ID的映射
    sprint_id_map = {}
    if workitems_result and "items" in workitems_result:
        for item in workitems_result["items"]:
            sprint_info = item.get("sprint")
            if sprint_info and sprint_info.get("id") and sprint_info.get("name"):
                sprint_id_map[sprint_info["name"]] = sprint_info["id"]
                print(f"  [DEBUG] 找到迭代: {sprint_info['name']} -> ID: {sprint_info['id']}")
    
    # 为迭代添加ID
    sprints_with_id = []
    for sprint in result:
        sprint_copy = dict(sprint)
        sprint_name = sprint.get("name", "")
        if sprint_name in sprint_id_map:
            sprint_copy["id"] = sprint_id_map[sprint_name]
        else:
            print(f"  [DEBUG] 迭代 {sprint_name} 没有ID，跳过")
        sprints_with_id.append(sprint_copy)
    
    print(f"  [DEBUG] 共找到 {len(sprints_with_id)} 个有ID的迭代")
    return sprints_with_id


def get_workitems(org_id, project_id, user_id, sprint_id=None):
    """获取工作项"""
    all_items = []
    for category in ["Req", "Task"]:
        params = {
            "organizationId": org_id,
            "spaceId": project_id,
            "category": category,
            "assignedTo": user_id,
            "perPage": 100
        }
        if sprint_id:
            params["sprint"] = sprint_id
        
        result = run_mcporter("search_workitems", params, debug=False)
        if result and "items" in result:
            all_items.extend(result["items"])
    
    return all_items


def generate_report(user_name, sprint_info, workitems, next_sprint_workitems=None):
    """生成周报内容"""
    start_date = timestamp_to_date(sprint_info["startDate"])
    end_date = timestamp_to_date(sprint_info["endDate"])
    
    # 分类当前迭代任务
    completed = []
    in_progress = []
    pending = []
    
    for item in workitems:
        status = item.get("status", {}).get("name", "")
        subject = item.get("subject", "")
        
        # 提取优先级
        priority = "中"
        priority_values = item.get("customFieldValues", [])
        for fv in priority_values:
            if fv.get("fieldId") == "priority":
                priority = fv.get("values", [{}])[0].get("displayValue", "中")
        
        task_info = {
            "subject": subject,
            "status": status,
            "priority": priority,
            "serial": item.get("serialNumber", "")
        }
        
        if status == "已完成":
            completed.append(task_info)
        elif status in ["进行中", "开发中", "设计中", "处理中"]:
            in_progress.append(task_info)
        else:
            pending.append(task_info)
    
    # 生成报告
    report = f"汇报周期：{start_date} - {end_date}\n\n"
    report += "一、核心成果\n\n"
    
    task_num = 0
    
    # 已完成任务
    if completed:
        for task in completed:
            task_num += 1
            report += f"{task_num}. {task['subject']}\n"
    
    # 进行中任务（智能标注状态）
    if in_progress:
        for task in in_progress:
            task_num += 1
            status = task['status']
            # 根据任务名称和状态智能标注
            if "设计" in status or "设计" in task['subject']:
                status_text = "设计阶段"
            elif "开发" in status or "开发" in task['subject']:
                status_text = "开发阶段"
            else:
                status_text = "进行中"
            report += f"{task_num}. {task['subject']} - {status_text}\n"
    
    if not completed and not in_progress:
        report += "暂无已完成任务\n"
    
    report += "\n二、下周期计划\n\n"
    
    # 使用下一个迭代的任务作为下周期计划
    next_task_count = 0
    if next_sprint_workitems:
        for item in next_sprint_workitems:
            subject = item.get("subject", "")
            next_task_count += 1
            report += f"{next_task_count}. {subject}\n"
    
    if not next_sprint_workitems:
        report += "暂无\n"
    
    return report, len(completed), len(in_progress), len(pending)


def send_to_wecom(report, webhook_url, user_name, stats):
    """发送周报到企业微信"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 格式化消息
    message = f"📋 云效周报 - {user_name}\n"
    message += f"📅 {today}\n"
    message += "─" * 30 + "\n\n"
    message += report
    message += "\n" + "─" * 30 + "\n"
    message += f"📊 统计：已完成 {stats[0]} | 进行中 {stats[1]} | 待处理 {stats[2]}"
    
    body = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    
    try:
        response = requests.post(webhook_url, json=body, headers={'Content-Type': 'application/json'}, timeout=30)
        result = response.json()
        if result.get('errcode') == 0:
            print(f"✓ 周报已发送到企业微信")
            return True
        else:
            print(f"✗ 发送失败: {result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"✗ 发送异常: {e}")
        return False


def main(user_name=None, webhook_url=None, send_to_wecom_flag=True, target_sprint_name=None):
    """主函数"""
    
    # 加载配置
    config_path = os.path.join(os.path.expanduser("~/.openclaw/workspace"), "wecom-config.json")
    
    # 从命令行参数获取
    if hasattr(sys, 'argv'):
        args = sys.argv[1:]
        for arg in args:
            if arg.startswith("--user="):
                user_name = arg.split("=", 1)[1]
            elif arg.startswith("--webhook="):
                webhook_url = arg.split("=", 1)[1]
            elif arg == "--no-send":
                send_to_wecom_flag = False
            elif arg == "--all":
                user_name = "__ALL__"
            elif arg.startswith("--sprint="):
                target_sprint_name = arg.split("=", 1)[1]
            elif not arg.startswith("--") and not webhook_url:
                # 第一个非参数参数作为用户名
                if not user_name:
                    user_name = arg
    
    # 从配置文件获取 webhook
    if not webhook_url and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            webhook_url = config.get('weeklyReportWebhook') or config.get('webhookUrl')
    
    # 获取当前用户信息
    print("获取用户信息...")
    user_info = get_current_user()
    
    if not user_info:
        print("✗ 无法获取用户信息，请检查云效 MCP 配置")
        return False
    
    # 使用固定的组织ID
    org_id = ORG_ID
    current_user_id = user_info.get("userId")
    current_user_name = user_info.get("userName", "用户")
    
    # 确定目标用户
    if user_name == "__ALL__":
        # 批量查询所有用户
        print(f"目标用户: 所有人员 ({len(ALL_USERS)}人)")
        print(f"✓ 组织: {org_id}")
        
        # 先获取项目列表
        print("\n获取项目列表...")
        projects = get_projects(org_id)
        if not projects:
            print("✗ 未找到项目")
            return False
        
        project = projects[0]
        project_id = project.get("id")
        project_name = project.get("name")
        print(f"✓ 项目: {project_name} (ID: {project_id})")
        
        # 获取迭代列表
        print("\n获取迭代列表...")
        sprints = get_sprints(org_id, project_id)
        if not sprints:
            print("✗ 未找到迭代")
            return False
        print(f"✓ 找到 {len(sprints)} 个迭代")
        
        # 确定目标迭代
        print("\n确定目标迭代...")
        current_sprint, next_sprint, match_reason = get_current_sprint(sprints, target_sprint_name)
        if not current_sprint:
            return False
        
        sprint_name = current_sprint.get("name")
        sprint_start = timestamp_to_date(current_sprint.get("startDate", 0))
        sprint_end = timestamp_to_date(current_sprint.get("endDate", 0))
        
        print(f"✓ 目标迭代: {sprint_name}")
        print(f"✓ 迭代周期: {sprint_start} - {sprint_end}")
        
        if next_sprint:
            next_sprint_name = next_sprint.get("name", "")
            print(f"✓ 下一迭代: {next_sprint_name}")
        else:
            print(f"✓ 下一迭代: 未找到")
        
        all_reports = []
        total_stats = [0, 0, 0]
        
        for user in ALL_USERS:
            print(f"\n{'='*40}")
            print(f"处理用户: {user}")
            print(f"{'='*40}")
            
            target_user_id = get_user_id(user)
            if not target_user_id:
                print(f"✗ 未找到用户: {user}")
                continue
            
            print(f"  ✓ 用户ID: {target_user_id}")
            
            # 获取当前迭代工作项
            workitems = get_workitems(org_id, project_id, target_user_id, current_sprint.get("id"))
            print(f"  当前迭代工作项: {len(workitems)} 条")
            
            # 获取下一迭代工作项
            next_workitems = []
            if next_sprint:
                next_workitems = get_workitems(org_id, project_id, target_user_id, next_sprint.get("id"))
                print(f"  下一迭代工作项: {len(next_workitems)} 条")
            
            if workitems or next_workitems:
                report, completed, in_progress, pending = generate_report(
                    user, current_sprint, workitems, next_workitems
                )
                total_stats[0] += completed
                total_stats[1] += in_progress
                total_stats[2] += pending
                all_reports.append({
                    "user": user,
                    "sprint": sprint_name,
                    "report": report
                })
        
        if not all_reports:
            print("\n✗ 未生成任何周报")
            return False
        
        # 合并所有报告
        final_report = f"📋 团队周报汇总\n📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
        final_report += "─" * 30 + "\n\n"
        
        current_user = None
        for rpt in all_reports:
            if rpt["user"] != current_user:
                current_user = rpt["user"]
                final_report += f"【{rpt['user']}】\n"
            final_report += f"{rpt['report']}\n"
            final_report += "─" * 30 + "\n\n"
        
        print("\n" + "=" * 50)
        print("生成的周报内容:")
        print("=" * 50)
        print(final_report)
        print("=" * 50)
        
        if send_to_wecom_flag and webhook_url and False:
            print(f"\n发送到企业微信...")
            send_to_wecom(final_report, webhook_url, "团队周报", total_stats)
        
        return True
        
    elif user_name:
        print(f"目标用户: {user_name}")
        target_user_id = get_user_id(user_name)
        if not target_user_id:
            print(f"✗ 未找到用户: {user_name}")
            return False
        target_user_name = user_name
    else:
        target_user_id = current_user_id
        target_user_name = current_user_name
    
    print(f"✓ 用户: {target_user_name}")
    print(f"✓ 组织: {org_id}")
    
    # 获取项目
    print("\n获取项目列表...")
    projects = get_projects(org_id)
    if not projects:
        print("✗ 未找到项目")
        return False
    
    project = projects[0]
    project_id = project.get("id")
    project_name = project.get("name")
    print(f"✓ 项目: {project_name} (ID: {project_id})")
    
    # 获取迭代列表
    print("\n获取迭代列表...")
    sprints = get_sprints(org_id, project_id)
    if not sprints:
        print("✗ 未找到迭代")
        return False
    print(f"✓ 找到 {len(sprints)} 个迭代")
    
    # 确定目标迭代
    print("\n确定目标迭代...")
    current_sprint, next_sprint, match_reason = get_current_sprint(sprints, target_sprint_name)
    if not current_sprint:
        return False
    
    sprint_name = current_sprint.get("name")
    sprint_start = timestamp_to_date(current_sprint.get("startDate", 0))
    sprint_end = timestamp_to_date(current_sprint.get("endDate", 0))
    
    print(f"✓ 目标迭代: {sprint_name}")
    print(f"✓ 迭代周期: {sprint_start} - {sprint_end}")
    
    if next_sprint:
        next_sprint_name = next_sprint.get("name", "")
        print(f"✓ 下一迭代: {next_sprint_name}")
    else:
        print(f"✓ 下一迭代: 未找到")
    
    all_reports = []
    total_stats = [0, 0, 0]
    
    # 获取当前迭代工作项
    print(f"\n获取 {target_user_name} 的工作项...")
    workitems = get_workitems(org_id, project_id, target_user_id, current_sprint.get("id"))
    print(f"✓ 当前迭代工作项: {len(workitems)} 条")
    
    # 获取下一迭代工作项
    next_workitems = []
    if next_sprint:
        next_workitems = get_workitems(org_id, project_id, target_user_id, next_sprint.get("id"))
        print(f"✓ 下一迭代工作项: {len(next_workitems)} 条")
    
    if workitems or next_workitems:
        report, completed, in_progress, pending = generate_report(
            target_user_name, current_sprint, workitems, next_workitems
        )
        total_stats[0] += completed
        total_stats[1] += in_progress
        total_stats[2] += pending
        all_reports.append({
            "sprint": sprint_name,
            "report": report
        })
    
    if not all_reports:
        print("\n✗ 未生成任何周报")
        return False
    
    # 合并所有报告
    final_report = ""
    for i, rpt in enumerate(all_reports):
        final_report += rpt["report"]
        if i < len(all_reports) - 1:
            final_report += "\n" + "─" * 30 + "\n\n"
    
    print("\n" + "=" * 50)
    print("生成的周报内容:")
    print("=" * 50)
    print(final_report)
    print("=" * 50)
    
    # 发送到企业微信
    if send_to_wecom_flag and webhook_url and False:
        print(f"\n发送到企业微信...")
        send_to_wecom(final_report, webhook_url, target_user_name, total_stats)
    elif not webhook_url:
        print("\n⚠ 未配置企业微信 Webhook，跳过发送")
    else:
        print("\n⚠ 已跳过发送（--no-send 参数）")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
