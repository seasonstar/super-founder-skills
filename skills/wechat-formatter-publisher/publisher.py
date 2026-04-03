"""WeChat Official Account article publisher via API.

Publishes HTML content as drafts to the WeChat MP platform.
Supports image upload with placeholder replacement.

Usage:
    python publisher.py article.html [--manifest manifest.json] [--cover cover.png]
"""

import argparse
import io
import json
import os
import sys
import time

import requests

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config


def get_access_token() -> str:
    """Get a valid access token, refreshing if expired."""
    if config._access_token and time.time() < config._token_expires_at:
        return config._access_token

    url = (
        f"https://api.weixin.qq.com/cgi-bin/token?"
        f"grant_type=client_credential&appid={config.APPID}&secret={config.APPSECRET}"
    )
    resp = requests.get(url, timeout=10)
    data = resp.json()

    if "access_token" not in data:
        raise RuntimeError(f"Failed to get access token: {data}")

    config._access_token = data["access_token"]
    config._token_expires_at = time.time() + data.get("expires_in", 7200) - 300  # 5min buffer
    return config._access_token


def upload_image(image_path: str, access_token: str) -> str:
    """Upload a local image to WeChat material library. Returns the URL."""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    filename = os.path.basename(image_path)

    with open(image_path, "rb") as f:
        files = {"media": (filename, f)}
        resp = requests.post(url, files=files, timeout=30)

    data = resp.json()
    if "url" not in data:
        raise RuntimeError(f"Failed to upload image {image_path}: {data}")

    return data["url"]


def upload_image_bytes(image_data: bytes, filename: str, access_token: str) -> str:
    """Upload image bytes directly to WeChat material library. Returns the URL.

    Used for external URLs: download to memory, upload from memory,
    no temp file needed.
    """
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    buf = io.BytesIO(image_data)
    files = {"media": (filename, buf)}
    resp = requests.post(url, files=files, timeout=30)

    data = resp.json()
    if "url" not in data:
        raise RuntimeError(f"Failed to upload image bytes ({filename}): {data}")

    return data["url"]


def upload_thumb(image_path: str, access_token: str) -> str:
    """Upload a cover image as permanent material. Returns media_id."""
    url = (
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?"
        f"access_token={access_token}&type=image"
    )
    filename = os.path.basename(image_path)

    with open(image_path, "rb") as f:
        files = {"media": (filename, f)}
        resp = requests.post(url, files=files, timeout=30)

    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"Failed to upload thumb {image_path}: {data}")

    return data["media_id"]


def replace_placeholders(html: str, images: dict[str, str]) -> str:
    """Replace WECHATIMGPH_N placeholders with actual <img> tags."""
    for placeholder, url in images.items():
        img_tag = (
            f'<section style="text-align: center; margin: 20px 0;">'
            f'<img src="{url}" style="width: 100%; border-radius: 8px; display: block;" />'
            f"</section>"
        )
        html = html.replace(placeholder, img_tag)
    return html


def create_draft(
    title: str,
    html: str,
    digest: str = "",
    thumb_media_id: str = "",
    author: str = "",
) -> str:
    """Create a draft article in WeChat MP. Returns the media_id."""
    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": html,
        "content_source_url": "",
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }

    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id

    payload = {"articles": [article]}
    # Use ensure_ascii=False to send Chinese characters directly,
    # not \uXXXX escapes — WeChat counts escaped length against its title limit.
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    data = resp.json()

    if "media_id" not in data:
        raise RuntimeError(f"Failed to create draft: {data}")

    return data["media_id"]


def publish(
    html_path: str,
    manifest_path: str | None = None,
    cover_path: str | None = None,
    author: str = "",
) -> str:
    """Publish an HTML file as a WeChat draft.

    Args:
        html_path: Path to the HTML file.
        manifest_path: Optional path to manifest.json with metadata.
        cover_path: Optional path to cover image.
        author: Optional author name.

    Returns:
        The draft media_id.
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Extract body content from preview HTML (get #output div content)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    output_div = soup.find(id="output")
    if output_div:
        body_html = str(output_div)
    else:
        body_html = html_content

    # Load manifest
    title = os.path.splitext(os.path.basename(html_path))[0]
    digest = ""
    placeholder_map = {}

    if manifest_path:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        title = manifest.get("title", title)
        digest = manifest.get("digest", digest)
        placeholder_map = manifest.get("images", {})

    # Upload images and replace placeholders
    token = get_access_token()
    uploaded_images = {}

    for placeholder, image_path in placeholder_map.items():
        is_url = image_path.startswith("http://") or image_path.startswith("https://")

        if is_url:
            # Download external image to memory, upload directly — no temp file
            print(f"Downloading remote image: {image_path[:80]}...")
            try:
                resp = requests.get(image_path, timeout=30)
                resp.raise_for_status()
                ext = os.path.splitext(image_path.split("?")[0])[1] or ".jpg"
                filename = f"image{ext}"
                print(f"Uploading from memory: {filename}")
                wechat_url = upload_image_bytes(resp.content, filename, token)
                uploaded_images[placeholder] = wechat_url
                print(f"  -> {wechat_url}")
            except Exception as e:
                print(f"Warning: Failed to download/upload {image_path}: {e}")
        else:
            # Local image file
            if not os.path.isabs(image_path):
                manifest_dir = os.path.dirname(os.path.abspath(manifest_path)) if manifest_path else os.path.dirname(os.path.abspath(html_path))
                image_path = os.path.join(manifest_dir, image_path)
            if os.path.exists(image_path):
                print(f"Uploading image: {image_path}")
                wechat_url = upload_image(image_path, token)
                uploaded_images[placeholder] = wechat_url
                print(f"  -> {wechat_url}")
            else:
                print(f"Warning: Image not found: {image_path}")

    body_html = replace_placeholders(body_html, uploaded_images)

    # Upload cover image: explicit --cover takes priority,
    # otherwise auto-detect first image (local or remote) from manifest
    thumb_media_id = ""
    if not cover_path and placeholder_map:
        for _ph, img_path in placeholder_map.items():
            is_remote = img_path.startswith("http://") or img_path.startswith("https://")
            if is_remote:
                try:
                    print(f"Downloading cover candidate: {img_path[:80]}...")
                    resp = requests.get(img_path, timeout=30)
                    resp.raise_for_status()
                    ext = os.path.splitext(img_path.split("?")[0])[1] or ".jpg"
                    filename = f"cover{ext}"
                    print(f"Uploading cover from memory: {filename}")
                    url = (
                        f"https://api.weixin.qq.com/cgi-bin/material/add_material?"
                        f"access_token={token}&type=image"
                    )
                    buf = io.BytesIO(resp.content)
                    files = {"media": (filename, buf)}
                    r = requests.post(url, files=files, timeout=30)
                    data = r.json()
                    if "media_id" in data:
                        thumb_media_id = data["media_id"]
                        print(f"  -> media_id: {thumb_media_id}")
                        break
                    else:
                        print(f"Warning: Cover upload failed: {data}")
                except Exception as e:
                    print(f"Warning: Failed to download/upload cover: {e}")
            else:
                resolved = img_path
                if not os.path.isabs(resolved):
                    manifest_dir = os.path.dirname(os.path.abspath(manifest_path)) if manifest_path else os.path.dirname(os.path.abspath(html_path))
                    resolved = os.path.join(manifest_dir, resolved)
                if os.path.exists(resolved):
                    cover_path = resolved
                    break

    if cover_path:
        print(f"Uploading cover: {cover_path}")
        thumb_media_id = upload_thumb(cover_path, token)
        print(f"  -> media_id: {thumb_media_id}")

    # Create draft
    print(f"Creating draft: {title}")
    media_id = create_draft(
        title=title,
        html=body_html,
        digest=digest,
        thumb_media_id=thumb_media_id,
        author=author,
    )
    print(f"Draft created: media_id={media_id}")
    return media_id


def main():
    parser = argparse.ArgumentParser(description="Publish HTML to WeChat Official Account")
    parser.add_argument("html", help="HTML file path")
    parser.add_argument("--manifest", default=None, help="Manifest JSON file path")
    parser.add_argument("--cover", default=None, help="Cover image path")
    parser.add_argument("--author", default="", help="Author name")

    args = parser.parse_args()

    # Auto-detect manifest if not provided: same dir, same base name + -manifest.json
    if not args.manifest:
        base = os.path.splitext(args.html)[0]
        candidate = base + "-manifest.json"
        if os.path.exists(candidate):
            args.manifest = candidate

    media_id = publish(args.html, args.manifest, args.cover, args.author)
    print(f"Done! Draft media_id: {media_id}")


if __name__ == "__main__":
    main()
