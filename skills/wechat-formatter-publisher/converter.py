"""Markdown to WeChat-compatible HTML converter.

Pipeline: extract title → preprocess → python-markdown → BS4 apply inline CSS →
WeChat fixes → output.

Uses python-markdown for parsing and BeautifulSoup4 for DOM manipulation,
as required by the project specification.

Usage:
    python converter.py article.md --theme claude [--color #HEX]
"""

import argparse
import html as html_module
import json
import os
import re
import sys
from dataclasses import dataclass, field

import markdown
from bs4 import BeautifulSoup

# Allow running as script or module
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from themes import claude as claude_theme
from themes import sticker as sticker_theme


@dataclass
class ConvertResult:
    html: str
    title: str
    digest: str
    images: list[str] = field(default_factory=list)


def _extract_title(md_text: str, filename: str = "") -> tuple[str, str]:
    """Extract and strip H1 title from markdown text. Returns (title, remaining_md).

    If no H1 heading is found, uses the filename (without extension) as the title.
    """
    match = re.match(r"^#\s+(.+?)(?:\n+|$)", md_text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        remaining = md_text[match.end():]
        return title, remaining
    # No H1 found — use filename (without extension) as title
    if filename:
        name = os.path.splitext(os.path.basename(filename))[0]
        if name:
            return name, md_text
    # Fallback: use first non-empty, non-heading line
    for line in md_text.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:50], md_text
    return "Untitled", md_text


def _make_digest(text: str, max_bytes: int = 120) -> str:
    """Generate a UTF-8 byte-limited digest from plain text."""
    clean = re.sub(r"[#*`\[\]()>|_-]", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    encoded = clean.encode("utf-8")
    if len(encoded) <= max_bytes:
        return clean
    # Truncate and trim back to valid UTF-8 boundary
    truncated = encoded[:max_bytes]
    while truncated:
        try:
            return truncated.decode("utf-8")
        except UnicodeDecodeError:
            truncated = truncated[:-1]
    return ""


def _preprocess_obsidian_images(md_text: str) -> str:
    """Convert Obsidian ![[file.png]] to standard ![file.png](file.png) markdown."""
    return re.sub(
        r"!\[\[([^\]]+)\]\]",
        r"![\1](\1)",
        md_text,
    )


def _preprocess_list_spacing(md_text: str) -> str:
    """Ensure a blank line before list items that follow non-blank, non-list lines.

    python-markdown requires a blank line before a list block.  When authors
    write ``**Bold**\\n- item`` without a separating blank line, the entire
    block is parsed as a single <p> instead of a <ul>.
    """
    lines = md_text.split("\n")
    result = []
    for i, line in enumerate(lines):
        if i > 0 and re.match(r"^\s*[-*+]\s", line):
            prev = result[-1] if result else ""
            # Only insert blank if previous line is not blank and not itself a list item
            if prev.strip() and not re.match(r"^\s*[-*+]\s", prev):
                result.append("")
        result.append(line)
    return "\n".join(result)


def _apply_theme_to_soup(
    soup: BeautifulSoup,
    theme,
    palette: dict,
    theme_name: str,
) -> tuple[str, list[str]]:
    """Walk the BeautifulSoup DOM and apply theme-specific inline styles.

    Returns (themed_html, image_list).
    """
    images = []
    img_counter = 0
    h2_counter = 0
    result_parts = []

    for element in soup.children:
        if isinstance(element, str) and element.strip():
            # Bare text node → paragraph
            text = html_module.escape(element.strip())
            result_parts.append(theme.paragraph(text, palette))
            continue

        if not hasattr(element, "name") or element.name is None:
            continue

        tag = element.name

        if tag == "h1":
            content = element.decode_contents()
            result_parts.append(theme.h1(content, palette))

        elif tag == "h2":
            h2_counter += 1
            if theme_name == "sticker":
                result_parts.append(theme.sticker_badge(h2_counter, palette))
            content = element.decode_contents()
            result_parts.append(theme.h2(content, palette))

        elif tag == "h3":
            content = element.decode_contents()
            result_parts.append(theme.h3(content, palette))

        elif tag == "p":
            # Check if paragraph contains only an <img> (standalone image)
            img_tag = element.find("img")
            if img_tag and len(list(element.children)) <= 2:  # img + maybe whitespace
                img_counter += 1
                src = img_tag.get("src", "")
                alt = img_tag.get("alt", "")
                images.append(src)
                result_parts.append(theme.image_placeholder(img_counter, palette, alt))
            else:
                content = _render_inline_elements(element, palette, theme)
                # Detect tags line (e.g. "**相关标签**：#量化交易 ...")
                plain = element.get_text()
                if plain.startswith("相关标签"):
                    result_parts.append(theme.tags(content, palette))
                else:
                    result_parts.append(theme.paragraph(content, palette))

        elif tag == "blockquote":
            inner = _render_inline_elements(element, palette, theme)
            result_parts.append(theme.blockquote(inner, palette))

        elif tag == "pre":
            code_tag = element.find("code")
            if code_tag:
                code_text = code_tag.get_text()
            else:
                code_text = element.get_text()
            result_parts.append(theme.code_block(code_text, palette))

        elif tag == "ul":
            items = []
            for li in element.find_all("li", recursive=False):
                items.append(_render_inline_elements(li, palette, theme))
            result_parts.append(theme.unordered_list(items, palette))

        elif tag == "ol":
            items = []
            for li in element.find_all("li", recursive=False):
                items.append(_render_inline_elements(li, palette, theme))
            result_parts.append(theme.ordered_list(items, palette))

        elif tag == "table":
            headers = []
            thead = element.find("thead")
            if thead:
                for th in thead.find_all("th"):
                    headers.append(_render_inline_elements(th, palette, theme))
            rows = []
            tbody = element.find("tbody") or element
            for tr in tbody.find_all("tr"):
                cells = []
                for td in tr.find_all("td"):
                    cells.append(_render_inline_elements(td, palette, theme))
                if cells:
                    rows.append(cells)
            if headers:
                result_parts.append(theme.table(headers, rows, palette))

        elif tag == "hr":
            result_parts.append(theme.divider(palette))

        elif tag == "img":
            img_counter += 1
            src = element.get("src", "")
            images.append(src)
            result_parts.append(theme.image_placeholder(img_counter, palette))

    return "\n".join(result_parts), images


def _render_inline_elements(element, palette: dict, theme) -> str:
    """Render inline child elements of a BS4 tag to themed HTML.

    Handles <strong>, <code>, <a>, <em>, <del>, and bare text.
    All text content is HTML-escaped for safety.
    """
    parts = []
    prev_was_link = False
    for child in element.children:
        if isinstance(child, str):
            parts.append(html_module.escape(child))
            prev_was_link = False
        elif hasattr(child, "name"):
            if child.name == "strong":
                inner = html_module.escape(child.get_text())
                parts.append(theme.bold(inner, palette))
                prev_was_link = False
            elif child.name == "code":
                inner = html_module.escape(child.get_text())
                parts.append(theme.inline_code(inner, palette))
                prev_was_link = False
            elif child.name == "a":
                href = html_module.escape(child.get("href", ""))
                inner = html_module.escape(child.get_text())
                # Add line break between consecutive links so they don't run together
                if prev_was_link:
                    parts.append("<br>")
                parts.append(theme.link(inner, href, palette))
                prev_was_link = True
            elif child.name == "em":
                parts.append(f"<em>{html_module.escape(child.get_text())}</em>")
                prev_was_link = False
            elif child.name == "del":
                parts.append(f"<del>{html_module.escape(child.get_text())}</del>")
                prev_was_link = False
            else:
                # Recurse for nested elements
                parts.append(_render_inline_elements(child, palette, theme))
                prev_was_link = False
    return "".join(parts)


def convert(md_text: str, theme_name: str = "claude", color: str | None = None, filename: str = "") -> ConvertResult:
    """Convert markdown text to WeChat-compatible HTML.

    Uses python-markdown for parsing and BeautifulSoup4 for DOM manipulation.

    Args:
        md_text: Source markdown content.
        theme_name: Theme to use ("claude" or "sticker").
        color: Optional custom primary color hex string.
        filename: Optional source filename for title fallback.

    Returns:
        ConvertResult with html, title, digest, and image placeholders.
    """
    if theme_name == "sticker":
        theme = sticker_theme
        default_color = "#D97757"
    else:
        theme = claude_theme
        default_color = "#D97757"

    primary = color if color else default_color
    palette = theme.get_palette(primary)

    # Extract title
    title, body_md = _extract_title(md_text, filename=filename)

    # Generate digest
    digest = _make_digest(body_md)

    # Preprocess Obsidian image embeds
    body_md = _preprocess_obsidian_images(body_md)

    # Preprocess: ensure lists have blank line before them
    body_md = _preprocess_list_spacing(body_md)

    # Parse markdown to HTML using python-markdown
    md_extensions = ["fenced_code", "tables", "codehilite"]
    md_html = markdown.markdown(
        body_md,
        extensions=md_extensions,
        extension_configs={"codehilite": {"css_class": "highlight"}},
    )

    # Parse with BeautifulSoup for DOM manipulation
    soup = BeautifulSoup(md_html, "html.parser")

    # Sanitize: remove dangerous HTML tags that python-markdown passes through
    for dangerous in soup.find_all(["script", "iframe", "style", "object", "embed", "form"]):
        dangerous.decompose()

    # Apply theme styles to DOM elements
    body_html, images = _apply_theme_to_soup(soup, theme, palette, theme_name)

    # Wrap in theme container
    full_html = theme.container(body_html, palette)

    return ConvertResult(
        html=full_html,
        title=title,
        digest=digest,
        images=images,
    )


def preview_html(result: ConvertResult) -> str:
    """Wrap converted HTML in a full preview document with copy-to-clipboard button."""
    safe_title = html_module.escape(result.title)
    copy_js = """
async function copyContent() {
  const content = document.getElementById('output');
  const btn = document.querySelector('.copy-btn');
  try {
    const htmlContent = content.innerHTML;
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const textBlob = new Blob([content.innerText], { type: 'text/plain' });
    await navigator.clipboard.write([new ClipboardItem({'text/html': blob, 'text/plain': textBlob})]);
    btn.textContent = '\\u2705 \\u5DF2\\u590D\\u5236'; btn.classList.add('copied');
  } catch (err) {
    const range = document.createRange(); range.selectNodeContents(content);
    const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
    document.execCommand('copy'); selection.removeAllRanges();
    btn.textContent = '\\u2705 \\u5DF2\\u590D\\u5236'; btn.classList.add('copied');
  }
  setTimeout(() => { btn.textContent = '\\uD83D\\uDCCB \\u590D\\u5236\\u5168\\u6587'; btn.classList.remove('copied'); }, 2000);
}"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; max-width: 578px; margin: 0 auto; padding: 20px; }}
.copy-btn {{ position: fixed; top: 20px; right: 20px; padding: 10px 20px; background: #D97757; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; z-index: 1000; }}
.copy-btn.copied {{ background: #52c41a; }}
</style>
</head>
<body>
<button class="copy-btn" onclick="copyContent()">&#x1F4CB; 复制全文</button>
<div id="output">
{result.html}
</div>
<script>{copy_js}
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to WeChat-compatible HTML")
    parser.add_argument("input", help="Input markdown file path")
    parser.add_argument("--theme", choices=["claude", "sticker"], default="claude",
                        help="Theme to use (default: claude)")
    parser.add_argument("--color", default=None,
                        help="Custom primary color (hex, e.g. #007AFF)")

    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        md_text = f.read()

    result = convert(md_text, theme_name=args.theme, color=args.color, filename=args.input)

    # Output to same directory as input, with .html extension
    base = os.path.splitext(args.input)[0]
    output_path = base + ".html"

    preview = preview_html(result)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(preview)

    # Also output manifest.json
    manifest = {
        "title": result.title,
        "digest": result.digest,
        "images": {
            f"WECHATIMGPH_{i+1}": img
            for i, img in enumerate(result.images)
        },
    }
    manifest_path = base + "-manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Output: {output_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Title: {result.title}")
    print(f"Images: {len(result.images)} placeholder(s)")


if __name__ == "__main__":
    main()
