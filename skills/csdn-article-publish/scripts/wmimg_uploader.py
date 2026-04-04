#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无铭图床(wmimg.com)图片上传工具
基于 wmimg.com API 上传图片，国内稳定访问
API 文档: https://wmimg.com/page/api-docs.html
"""

import json
import os
import sys
from pathlib import Path

import requests


class WmimgUploader:
    """无铭图床上传器"""

    API_BASE = "https://wmimg.com/api/v1"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def upload(self, image_path: str, permission: int = 1) -> dict:
        """
        上传图片到无铭图床

        Args:
            image_path: 本地图片路径
            permission: 权限，1=公开（默认），0=私有

        Returns:
            dict: 包含图片链接等信息
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {image_path}")

        url = f"{self.API_BASE}/upload"
        with open(path, "rb") as f:
            files = {"file": (path.name, f)}
            data = {"permission": permission}
            resp = requests.post(
                url, headers=self.headers, files=files, data=data, timeout=60
            )

        if resp.status_code == 200:
            result = resp.json()
            if result.get("status"):
                img_data = result["data"]
                links = img_data.get("links", {})
                return {
                    "success": True,
                    "filename": img_data.get("origin_name", path.name),
                    "url": links.get("url", ""),
                    "markdown": links.get("markdown", ""),
                    "thumbnail_url": links.get("thumbnail_url", ""),
                    "delete_url": links.get("delete_url", ""),
                    "key": img_data.get("key", ""),
                    "size_kb": img_data.get("size", 0),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "未知错误"),
                }
        elif resp.status_code == 429:
            return {"success": False, "error": "请求超出配额，请稍后再试"}
        elif resp.status_code == 401:
            return {"success": False, "error": "Token 无效或已过期"}
        else:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }


def load_config():
    """从 csdn_config.json 读取配置"""
    config_paths = [
        os.path.join(os.path.dirname(__file__), "..", "config", "csdn_config.json"),
        os.path.join(os.getcwd(), "csdn_config.json"),
    ]
    for config_path in config_paths:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def main():
    if len(sys.argv) < 2:
        print("用法: python wmimg_uploader.py <图片路径> [TOKEN]")
        print("示例: python wmimg_uploader.py ./test.png")
        print("      python wmimg_uploader.py ./test.png 804|AyKazkrkLtChWgsKNURWKBWovKaBNBEsN28CPD5P")
        sys.exit(1)

    image_path = sys.argv[1]

    # Token 优先级：命令行参数 > 配置文件 > 环境变量
    token = None
    if len(sys.argv) > 2:
        token = sys.argv[2]

    if not token:
        config = load_config()
        token = config.get("wmimg", {}).get("token")

    if not token:
        token = os.environ.get("WMIMG_TOKEN")

    if not token:
        print("❌ 未提供 wmimg Token")
        print("  方式1: 作为第二个参数传入")
        print("  方式2: 在 csdn_config.json 的 wmimg.token 字段配置")
        print("  方式3: 设置环境变量 WMIMG_TOKEN")
        sys.exit(1)

    uploader = WmimgUploader(token)
    result = uploader.upload(image_path)

    if result["success"]:
        print(f"\n✅ 上传成功!")
        print(f"文件名: {result['filename']}")
        print(f"大小: {result['size_kb']} KB")
        print(f"\n图片链接:")
        print(f"  直链: {result['url']}")
        print(f"  缩略图: {result['thumbnail_url']}")
        print(f"  Markdown: {result['markdown']}")
    else:
        print(f"\n❌ 上传失败: {result['error']}")


if __name__ == "__main__":
    main()
