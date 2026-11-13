"""WeChat Official Account article publisher via API.

Publishes HTML content as drafts to the WeChat MP platform.
Supports image upload with placeholder replacement.

Usage:
    python publisher.py article.html [--manifest manifest.json] [--cover cover.png]
    python publisher.py --sticker --image a.png --image b.png --title "标题" --text "配文"
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


def detect_collection(title: str) -> str | None:
    """Auto-detect the collection (合集) name from the article title.

    Uses config.COLLECTION_MAP (keyword -> collection name), first match wins.
    Returns None when no keyword matches — the user picks manually.
    """
    for keyword, name in config.COLLECTION_MAP:
        if keyword in title:
            return name
    return None


def print_manual_checklist(collection: str | None) -> None:
    """Print post-draft steps the official API cannot automate.

    原创声明/合集/创作来源/平台推荐 are MP-backend-only settings —
    the draft/add API silently drops these fields (verified empirically).
    Print the exact values to tick in the backend before publishing.
    """
    print()
    print("📌 后台发布前需手动确认（官方 API 不支持自动设置）:")
    for step in config.MANUAL_PUBLISH_STEPS:
        print(f"   - {step.format(collection=collection or '未匹配，请手动选择')}")
    print("   - 留言「自动精选公开」为账号级一次性设置: 后台 设置→留言")


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


def upload_material_image(image_path: str, access_token: str) -> str:
    """Upload an image as permanent material. Returns media_id.

    Same API for article covers and newspic (贴图) image lists.
    """
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
        raise RuntimeError(f"Failed to upload image {image_path}: {data}")

    return data["media_id"]


def upload_thumb(image_path: str, access_token: str) -> str:
    """Upload a cover image as permanent material. Returns media_id."""
    return upload_material_image(image_path, access_token)


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
    need_open_comment: int | None = None,
    only_fans_can_comment: int | None = None,
) -> str:
    """Create a draft article in WeChat MP. Returns the media_id.

    Comment flags fall back to config.PUBLISH_DEFAULTS (留言开启、所有人可评论).
    """
    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

    defaults = config.PUBLISH_DEFAULTS
    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": html,
        "content_source_url": "",
        "need_open_comment": defaults["need_open_comment"] if need_open_comment is None else need_open_comment,
        "only_fans_can_comment": defaults["only_fans_can_comment"] if only_fans_can_comment is None else only_fans_can_comment,
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


def create_sticker_draft(
    title: str,
    text: str,
    image_media_ids: list[str],
    author: str = "",
    need_open_comment: int | None = None,
    only_fans_can_comment: int | None = None,
) -> str:
    """Create a newspic (贴图/图片消息) draft. Returns the media_id.

    Distinct from article drafts (article_type=news): image-first posts,
    first image becomes the cover, plain text instead of HTML content.
    """
    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

    defaults = config.PUBLISH_DEFAULTS
    payload = {
        "articles": [
            {
                "article_type": "newspic",
                "title": title,
                "author": author,
                "digest": text,
                "content": text,
                "need_open_comment": defaults["need_open_comment"] if need_open_comment is None else need_open_comment,
                "only_fans_can_comment": defaults["only_fans_can_comment"] if only_fans_can_comment is None else only_fans_can_comment,
                "image_info": {
                    "image_list": [
                        {"image_media_id": mid} for mid in image_media_ids
                    ]
                },
            }
        ]
    }
    # ensure_ascii=False + UTF-8 body: escaped \uXXXX would garble Chinese
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    data = resp.json()

    if "media_id" not in data:
        raise RuntimeError(f"Failed to create sticker draft: {data}")

    return data["media_id"]


def publish_sticker(
    image_paths: list[str],
    title: str,
    text: str,
    author: str = "",
    need_open_comment: int | None = None,
) -> str:
    """Publish a sticker/image-message (newspic) draft.

    Args:
        image_paths: Local image paths (max 20; the first one is the cover).
        title: Post title.
        text: Short supporting text (also used as digest).
        author: Optional author name; empty falls back to config default.
        need_open_comment: Optional comment flag; None uses config default.

    Returns:
        The draft media_id.
    """
    if not image_paths:
        raise SystemExit("Sticker mode requires at least one --image")
    if len(image_paths) > 20:
        raise SystemExit("Sticker mode allows at most 20 images")

    resolved = []
    for p in image_paths:
        path = os.path.abspath(os.path.expanduser(p))
        if not os.path.exists(path):
            raise SystemExit(f"Image not found: {path}")
        resolved.append(path)

    if not author:
        author = config.PUBLISH_DEFAULTS["author"]

    token = get_access_token()
    media_ids = []
    for path in resolved:
        print(f"Uploading image: {path}")
        media_id = upload_material_image(path, token)
        media_ids.append(media_id)
        print(f"  -> media_id: {media_id}")

    print(f"Creating sticker draft: {title}")
    media_id = create_sticker_draft(
        title, text, media_ids, author, need_open_comment
    )
    print(f"Draft created: media_id={media_id}")
    print_manual_checklist(detect_collection(title))
    return media_id


def publish(
    html_path: str,
    manifest_path: str | None = None,
    cover_path: str | None = None,
    author: str = "",
    need_open_comment: int | None = None,
    collection: str | None = None,
) -> str:
    """Publish an HTML file as a WeChat draft.

    Args:
        html_path: Path to the HTML file.
        manifest_path: Optional path to manifest.json with metadata.
        cover_path: Optional path to cover image.
        author: Optional author name; empty falls back to config default.
        need_open_comment: Optional comment flag; None uses config default.
        collection: Optional collection (合集) name for the checklist;
            None auto-detects from the article title via config.COLLECTION_MAP.

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
    if not author:
        author = config.PUBLISH_DEFAULTS["author"]
    print(f"Creating draft: {title}")
    media_id = create_draft(
        title=title,
        html=body_html,
        digest=digest,
        thumb_media_id=thumb_media_id,
        author=author,
        need_open_comment=need_open_comment,
    )
    print(f"Draft created: media_id={media_id}")
    print(f"Author: {author} | 留言: 已开启（所有人可评论）")

    if collection is None:
        collection = detect_collection(title)
    if collection:
        print(f"合集: 应选「{collection}」（按标题自动匹配）")
    else:
        print("合集: 标题未命中 COLLECTION_MAP，请在后台手动选择")
    print_manual_checklist(collection)
    return media_id


def main():
    parser = argparse.ArgumentParser(description="Publish HTML to WeChat Official Account")
    parser.add_argument("html", nargs="?", help="HTML file path (article mode)")
    parser.add_argument("--manifest", default=None, help="Manifest JSON file path")
    parser.add_argument("--cover", default=None, help="Cover image path")
    parser.add_argument(
        "--author",
        default=None,
        help=f"Author name (default: {config.PUBLISH_DEFAULTS['author']})",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="合集 name for the manual checklist; default auto-detects from title via config.COLLECTION_MAP",
    )
    parser.add_argument(
        "--no-comment",
        action="store_true",
        help="Disable comments (default: enabled per config.PUBLISH_DEFAULTS)",
    )
    parser.add_argument(
        "--sticker",
        action="store_true",
        help="贴图模式: publish an image-message (newspic) draft",
    )
    parser.add_argument(
        "--image",
        action="append",
        default=None,
        help="贴图模式: image path, repeatable up to 20 (first image is the cover)",
    )
    parser.add_argument("--title", default=None, help="贴图模式: post title")
    parser.add_argument("--text", default=None, help="贴图模式: short supporting text")

    args = parser.parse_args()
    author = args.author or ""
    comment_flag = 0 if args.no_comment else None

    if args.sticker:
        if not args.title or not args.text:
            raise SystemExit("Sticker mode requires --title and --text")
        media_id = publish_sticker(
            args.image or [],
            args.title,
            args.text,
            author,
            need_open_comment=comment_flag,
        )
        print(f"Done! Draft media_id: {media_id}")
        return

    if not args.html:
        raise SystemExit("Provide an HTML file, or use --sticker mode (see --help)")

    # Auto-detect manifest if not provided: same dir, same base name + -manifest.json
    if not args.manifest:
        base = os.path.splitext(args.html)[0]
        candidate = base + "-manifest.json"
        if os.path.exists(candidate):
            args.manifest = candidate

    media_id = publish(
        args.html,
        args.manifest,
        args.cover,
        author,
        need_open_comment=comment_flag,
        collection=args.collection,
    )
    print(f"Done! Draft media_id: {media_id}")


if __name__ == "__main__":
    main()
