#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 图床图片上传工具
基于 GitHub API 将图片上传到 picx-images-hosting 仓库
"""

import base64
import os
import sys
import hashlib
import requests
from pathlib import Path


class GitHubImageUploader:
    """GitHub 图床上传器"""

    def __init__(self, token: str, owner: str = "seasonstar", repo: str = "picx-images-hosting", proxy: str = None):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        # 代理配置：优先传入 > 环境变量 > 系统代理
        self.proxies = None
        if proxy:
            self.proxies = {"http": proxy, "https": proxy}
        elif os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"):
            p = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
            self.proxies = {"http": p, "https": p}

    def _get_file_sha(self, path: str) -> str | None:
        """获取文件 SHA（用于更新已存在的文件）"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{path}"
        resp = requests.get(url, headers=self.headers, proxies=self.proxies)
        if resp.status_code == 200:
            return resp.json().get("sha")
        return None

    def _compute_hash(self, content: bytes) -> str:
        """计算文件 SHA1（不带引号）"""
        return hashlib.sha1(content).hexdigest()

    def upload(self, image_path: str, branch: str = "master", message: str = None) -> dict:
        """
        上传图片到 GitHub

        Args:
            image_path: 本地图片路径
            branch: 分支名，默认 master
            message: 提交信息，默认 "upload {filename}"

        Returns:
            dict: 包含下载链接等信息
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {image_path}")

        filename = path.name
        with open(path, "rb") as f:
            content = f.read()

        # Base64 编码
        b64_content = base64.b64encode(content).decode("utf-8")

        # 提交信息
        if message is None:
            message = f"upload {filename}"

        # 文件路径：images/文件名
        file_path = f"images/{filename}"

        # 检查文件是否已存在，获取 SHA
        sha = self._get_file_sha(file_path)

        # 构建请求
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{file_path}"
        data = {
            "message": message,
            "content": b64_content,
            "branch": branch,
        }
        if sha:
            data["sha"] = sha  # 更新已存在文件需要 SHA

        resp = requests.put(url, headers=self.headers, json=data, proxies=self.proxies)

        if resp.status_code in (200, 201):
            result = resp.json()
            # 返回多种链接格式
            download_url = result["content"]["download_url"]
            raw_url = download_url.replace("raw.githubusercontent.com", "raw.githubusercontent.com")

            # GitHub Pages 链接（需启用 GitHub Pages）
            pages_url = f"https://seasonstar.github.io/picx-images-hosting/{filename}"

            return {
                "success": True,
                "filename": filename,
                "download_url": download_url,
                "pages_url": pages_url,
                "raw_url": f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{branch}/{file_path}",
                "commit": result["commit"]["sha"],
            }
        else:
            return {
                "success": False,
                "error": resp.json(),
                "status_code": resp.status_code,
            }

    def upload_base64(self, filename: str, base64_data: str, branch: str = "master") -> dict:
        """
        上传 Base64 编码的图片数据

        Args:
            filename: 文件名
            base64_data: Base64 编码的图片数据（不含 data:image/xxx;base64, 前缀）
            branch: 分支名
        """
        file_path = f"images/{filename}"
        sha = self._get_file_sha(file_path)

        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{file_path}"
        data = {
            "message": f"upload {filename}",
            "content": base64_data,
            "branch": branch,
        }
        if sha:
            data["sha"] = sha

        resp = requests.put(url, headers=self.headers, json=data, proxies=self.proxies)

        if resp.status_code in (200, 201):
            result = resp.json()
            return {
                "success": True,
                "filename": filename,
                "download_url": result["content"]["download_url"],
            }
        else:
            return {
                "success": False,
                "error": resp.json(),
            }


def main():
    if len(sys.argv) < 3:
        print("用法: python github_image_uploader.py <图片路径> <GitHub_TOKEN> [--proxy http://127.0.0.1:15236]")
        print("示例: python github_image_uploader.py ./test.png ghp_xxxx")
        print("      python github_image_uploader.py ./test.png ghp_xxxx --proxy http://127.0.0.1:15236")
        sys.exit(1)

    image_path = sys.argv[1]
    token = sys.argv[2]

    # 解析 --proxy 参数
    proxy = None
    if '--proxy' in sys.argv:
        idx = sys.argv.index('--proxy')
        if idx + 1 < len(sys.argv):
            proxy = sys.argv[idx + 1]

    uploader = GitHubImageUploader(token, proxy=proxy)
    result = uploader.upload(image_path)

    if result["success"]:
        print(f"\n✅ 上传成功!")
        print(f"文件名: {result['filename']}")
        print(f"\n图片链接:")
        print(f"  下载页: {result['download_url']}")
        print(f"  原始链接: {result['raw_url']}")
        print(f"  GitHub Pages: {result['pages_url']}")
    else:
        print(f"\n❌ 上传失败: {result['error']}")


if __name__ == "__main__":
    main()
