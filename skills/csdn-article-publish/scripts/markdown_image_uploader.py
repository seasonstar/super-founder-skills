#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 图片处理工具
自动识别、上传 Markdown 中的图片到 GitHub 图床
支持本地图片和外链图片
"""

import base64
import json
import os
import re
import sys
import hashlib
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import requests


# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
from github_image_uploader import GitHubImageUploader


class MarkdownImageProcessor:
    """Markdown 图片处理器"""

    # 支持的图片扩展名
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}

    def __init__(self, github_token: str, owner: str = "seasonstar", repo: str = "picx-images-hosting", proxy: str = None):
        self.uploader = GitHubImageUploader(github_token, owner, repo, proxy=proxy)
        self.uploaded_urls = {}  # 缓存已上传的图片，key是原始路径/URL

    def is_image_url(self, url: str) -> bool:
        """检查URL是否指向图片"""
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix.lower()
        return ext in self.IMAGE_EXTENSIONS

    def is_local_path(self, path: str) -> bool:
        """判断是否是本地路径（非http/https开头）"""
        return not path.startswith('http://') and not path.startswith('https://')

    def extract_images_from_markdown(self, content: str) -> list:
        """从 Markdown 内容中提取所有图片"""
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = []
        for match in re.finditer(pattern, content):
            alt_text = match.group(1)
            image_path = match.group(2)
            images.append({
                'full_match': match.group(0),
                'alt_text': alt_text,
                'path': image_path,
                'start': match.start(),
                'end': match.end()
            })
        return images

    def download_image(self, url: str) -> tuple[str, str] | None:
        """
        下载图片并返回 (临时文件路径, 原始文件名)
        """
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # 从URL或Content-Disposition获取文件名
                content_disposition = response.headers.get('content-disposition', '')
                if 'filename=' in content_disposition:
                    import re
                    filename_match = re.search(r'filename=["\']?([^"\';\n]+)', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)
                    else:
                        filename = Path(urlparse(url).path).name
                else:
                    filename = Path(urlparse(url).path).name

                if not filename or '.' not in filename:
                    # 根据Content-Type推断扩展名
                    content_type = response.headers.get('content-type', '')
                    ext_map = {
                        'image/jpeg': '.jpg',
                        'image/png': '.png',
                        'image/gif': '.gif',
                        'image/webp': '.webp',
                        'image/svg+xml': '.svg'
                    }
                    ext = ext_map.get(content_type, '.jpg')
                    filename = f"image_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"

                # 保存到临时文件
                suffix = Path(filename).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                    f.write(response.content)
                    return f.name, filename
        except Exception as e:
            print(f"  ⚠️ 下载失败 {url}: {e}")
        return None

    def upload_image(self, image_source: str, is_local: bool = True) -> str | None:
        """
        上传单张图片

        Args:
            image_source: 本地路径或 URL
            is_local: True 表示本地文件，False 表示远程URL

        Returns:
            新的 GitHub 链接，失败返回 None
        """
        # 检查缓存
        if image_source in self.uploaded_urls:
            return self.uploaded_urls[image_source]

        temp_path = None
        try:
            if is_local:
                # 本地文件直接上传
                if not os.path.exists(image_source):
                    print(f"  ⚠️ 本地文件不存在: {image_source}")
                    return None
                temp_path = image_source
                filename = Path(image_source).name
            else:
                # 远程URL需要下载
                print(f"  → 下载中: {image_source}")
                result = self.download_image(image_source)
                if not result:
                    return None
                temp_path, filename = result

            # 上传
            print(f"  → 上传中: {filename}")
            result = self.uploader.upload(temp_path, message=f"upload {filename}")

            if result['success']:
                new_url = result['raw_url']
                self.uploaded_urls[image_source] = new_url
                print(f"  ✅ 上传成功: {filename}")
                return new_url
            else:
                print(f"  ❌ 上传失败: {result.get('error')}")
                return None

        finally:
            # 清理临时文件（如果是下载的远程图片）
            if not is_local and temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def process_markdown(self, content: str, base_dir: str = None, dry_run: bool = False) -> tuple[str, list]:
        """
        处理 Markdown 内容，只上传本地图片，外链图片保持不变

        Args:
            content: Markdown 内容
            base_dir: 基础目录（用于解析相对路径）
            dry_run: 是否只预览不实际上传

        Returns:
            (处理后的内容, 上传结果列表)
        """
        images = self.extract_images_from_markdown(content)

        if not images:
            print("📝 未发现图片")
            return content, []

        # 分离本地图片和外链图片
        local_images = [img for img in images if self.is_local_path(img['path'])]
        remote_images = [img for img in images if not self.is_local_path(img['path'])]

        print(f"\n🖼️ 发现 {len(images)} 张图片")
        if local_images:
            print(f"   📦 本地图片: {len(local_images)} 张（需要上传）")
        if remote_images:
            print(f"   🔗 外链图片: {len(remote_images)} 张（保持原样）")

        if not local_images:
            print("\n✨ 没有本地图片需要处理")
            return content, []

        print(f"\n开始处理 {len(local_images)} 张本地图片...\n")

        results = []
        new_content = content

        for img in local_images:
            image_path = img['path']
            print(f"\n处理: {image_path}")

            # 转换相对路径为绝对路径
            if base_dir and not os.path.isabs(image_path):
                abs_path = os.path.abspath(os.path.join(base_dir, image_path))
            else:
                abs_path = image_path

            # 上传图片
            if dry_run:
                print(f"  🔍 预览: 本地 -> GitHub 图床")
                new_url = "[dry_run] " + image_path
            else:
                new_url = self.upload_image(abs_path, is_local=True)

            if new_url:
                # 替换 Markdown 中的图片链接
                old_md = img['full_match']
                new_md = f'![{img["alt_text"]}]({new_url})'
                new_content = new_content.replace(old_md, new_md, 1)

                results.append({
                    'original': image_path,
                    'new_url': new_url,
                    'status': 'success'
                })
            else:
                results.append({
                    'original': image_path,
                    'new_url': None,
                    'status': 'failed'
                })

        return new_content, results


def load_config():
    """从 csdn_config.json 读取配置"""
    config_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'config', 'csdn_config.json'),
        os.path.join(os.getcwd(), 'csdn_config.json'),
    ]
    for config_path in config_paths:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python markdown_image_uploader.py <markdown文件> [GitHub_TOKEN]")
        print("")
        print("示例:")
        print("  python markdown_image_uploader.py ./articles/test.md ghp_xxxx")
        print("  python markdown_image_uploader.py ./articles/test.md  # 从环境变量 GITHUB_TOKEN 读取")
        sys.exit(1)

    md_file = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('GITHUB_TOKEN')

    if not token:
        print("❌ 未提供 GitHub Token")
        print("  方式1: 作为第二个参数传入")
        print("  方式2: 设置环境变量 GITHUB_TOKEN")
        sys.exit(1)

    # 读取 Markdown 文件
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 从配置文件读取代理
    proxy = None
    if '--proxy' in sys.argv:
        idx = sys.argv.index('--proxy')
        if idx + 1 < len(sys.argv):
            proxy = sys.argv[idx + 1]

    if not proxy:
        config = load_config()
        proxy = config.get('github', {}).get('proxy')

    # 处理图片
    processor = MarkdownImageProcessor(token, proxy=proxy)
    base_dir = os.path.dirname(os.path.abspath(md_file))
    new_content, results = processor.process_markdown(content, base_dir)

    # 输出结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n\n📊 处理完成: {success_count}/{len(results)} 张图片上传成功")

    if success_count > 0:
        # 输出处理后的文件
        output_file = md_file.replace('.md', '_github.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"📝 处理后的文件已保存: {output_file}")

    # 显示失败的图片
    failed = [r for r in results if r['status'] == 'failed']
    if failed:
        print(f"\n⚠️ 以下图片上传失败:")
        for r in failed:
            print(f"  - {r['original']}")


if __name__ == "__main__":
    main()
