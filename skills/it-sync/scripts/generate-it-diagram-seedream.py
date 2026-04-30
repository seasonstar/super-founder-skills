#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT 双周会排期配图 —— 豆包 Seedream 文生图
业务内容请在 it_diagram_sync_config.py 修改，本脚本一般不用改。
"""

import os
import sys

from volcenginesdkarkruntime import Ark

from it_diagram_sync_config import build_full_image_prompt, build_sync_notice_text

# 从环境变量读取，请勿把 Key 写进代码库
api_key = os.environ.get("ARK_API_KEY")
if not api_key:
    print("❌ 请设置环境变量 ARK_API_KEY")
    sys.exit(1)

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=api_key,
)

prompt = build_full_image_prompt()

print("正在生成图片（Seedream），请稍候...")
print("提示词长度:", len(prompt), "字符\n")
print("=" * 60)
print("【发群简短通知 —— 可与配图一起发】")
print("=" * 60)
print(build_sync_notice_text())
print("=" * 60)
print()

try:
    images_response = client.images.generate(
        model="doubao-seedream-5-0-260128",
        prompt=prompt,
        sequential_image_generation="disabled",
        response_format="url",
        size="2K",
        stream=False,
        watermark=False,
    )

    image_url = images_response.data[0].url
    print("✅ 图片生成成功！")
    print(f"\n图片 URL: {image_url}")
    print("\n提示：可打开 URL 查看/下载，再发到 IT 业务支持群。")

except Exception as e:
    print(f"❌ 生成失败: {e}")
    import traceback

    traceback.print_exc()
