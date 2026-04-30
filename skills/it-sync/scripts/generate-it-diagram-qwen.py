#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT 双周会排期配图 —— 通义千问 Qwen-Image 文生图
业务内容请在 it_diagram_sync_config.py 修改，本脚本一般不用改。
"""

import json
import os
import sys
import urllib.request

import dashscope
from dashscope import MultiModalConversation

from it_diagram_sync_config import build_full_image_prompt, build_sync_notice_text

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("❌ 请设置环境变量 DASHSCOPE_API_KEY")
    sys.exit(1)

prompt = build_full_image_prompt()

messages = [{"role": "user", "content": [{"text": prompt}]}]

print("正在生成信息图（Qwen）...")
print("模型: qwen-image-2.0-pro")
print("尺寸: 2688x1536 (16:9)")
print("-" * 50)
print("=" * 60)
print("【发群简短通知 —— 可与配图一起发】")
print("=" * 60)
print(build_sync_notice_text())
print("=" * 60)
print()

response = MultiModalConversation.call(
    api_key=api_key,
    model="qwen-image-2.0-pro-2026-03-03",
    messages=messages,
    result_format="message",
    stream=False,
    watermark=False,
    prompt_extend=True,
    negative_prompt=(
        "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，"
        "过度光滑，画面具有AI感，构图混乱，文字模糊扭曲，机器人，大脑剖面，"
        "密集电路板，卡通火箭，夸张科幻符号"
    ),
    size="2688*1536",
)

if response.status_code == 200:
    print("\n✅ 图片生成成功！")

    try:
        output = response.output
        if hasattr(output, "choices") and len(output.choices) > 0:
            content = output.choices[0].message.content
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "image" in item:
                        image_url = item["image"]
                        print(f"\n📷 图片URL: {image_url}")

                        output_file = "IT资源管理排期图-qwen.png"
                        print(f"\n正在下载图片到: {output_file}")
                        urllib.request.urlretrieve(image_url, output_file)
                        print(f"✅ 图片已保存: {output_file}")
                        break
    except Exception as e:
        print(f"\n提取/下载图片时出错: {e}")
        print("完整响应：")
        print(json.dumps(response, ensure_ascii=False, indent=2))
else:
    print("\n❌ 生成失败")
    print(f"HTTP返回码：{response.status_code}")
    if hasattr(response, "code"):
        print(f"错误码：{response.code}")
    if hasattr(response, "message"):
        print(f"错误信息：{response.message}")
