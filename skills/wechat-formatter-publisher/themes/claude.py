"""Claude theme (简约橙) element generators.

Clean, minimal style with left-border headings, warm orange accent.
Default primary: #D97757
"""

import html as html_module

from color_utils import derive_palette, hex_to_rgb


def get_palette(primary: str = "#D97757") -> dict:
    return derive_palette(primary)


def container(content: str, palette: dict) -> str:
    return (
        '<section style="background: rgba(0,0,0,0.02); border-radius: 8px; '
        'padding: 12px; font-family: -apple-system, BlinkMacSystemFont, '
        "'PingFang SC', 'Microsoft YaHei', sans-serif;\">"
        f"{content}"
        "</section>"
    )


def h1(text: str, palette: dict) -> str:
    return (
        f'<h1 style="font-size: 22px; font-weight: bold; color: {palette["heading_color"]}; '
        f'margin-bottom: 30px; text-align: center; line-height: 1.4;">{text}</h1>'
    )


def h2(text: str, palette: dict) -> str:
    return (
        f'<h2 style="font-family: -apple-system, BlinkMacSystemFont, \'PingFang SC\', '
        f'\'Microsoft YaHei\', sans-serif; font-size: 20px; font-weight: bold; '
        f'color: {palette["heading_color"]}; margin-top: 40px; margin-bottom: 20px; '
        f'padding-left: 12px; padding-bottom: 8px; '
        f'border-left: 4px solid {palette["primary"]}; '
        f'border-bottom: 1px dashed {palette["primary"]};">{text}</h2>'
    )


def h3(text: str, palette: dict) -> str:
    return (
        f'<h3 style="font-size: 18px; font-weight: bold; color: {palette["primary"]}; '
        f'margin-top: 30px; margin-bottom: 16px;">{text}</h3>'
    )


def paragraph(text: str, palette: dict) -> str:
    return (
        f'<p style="font-size: 16px; color: {palette["text_color"]}; '
        f'margin-bottom: 20px; line-height: 1.75; letter-spacing: 0.05em; '
        f'text-align: left;">{text}</p>'
    )


def tags(text: str, palette: dict) -> str:
    """Render tags/labels line in small muted text."""
    return (
        f'<p style="font-size: 13px; color: #999999; '
        f'margin-bottom: 16px; line-height: 1.6; letter-spacing: 0.05em; '
        f'text-align: left;">{text}</p>'
    )


def bold(text: str, palette: dict) -> str:
    return f'<strong style="font-weight: bold; color: {palette["primary"]};">{text}</strong>'


def inline_code(text: str, palette: dict) -> str:
    return (
        f'<span style="background-color: #F0F0F0; color: {palette["primary"]}; '
        f'padding: 2px 6px; border-radius: 4px; font-family: Menlo, Monaco, Consolas, monospace; '
        f'font-size: 14px; letter-spacing: 0;">{text}</span>'
    )


def code_block(content: str, palette: dict) -> str:
    lines = content.split("\n")
    html_lines = []
    for line in lines:
        escaped = html_module.escape(line)
        # Replace only leading spaces with &nbsp;
        stripped = escaped.lstrip(" ")
        leading = len(escaped) - len(stripped)
        nbsp_prefix = "&nbsp;" * leading if leading else ""
        rendered = nbsp_prefix + stripped
        html_lines.append(rendered)
    body = "<br>\n".join(html_lines)
    return (
        f'<section style="background-color: {palette["code_bg"]}; color: {palette["code_text"]}; '
        f'padding: 16px 20px; border-radius: 8px; margin: 20px 0; '
        f"font-family: Menlo, Monaco, Consolas, 'Microsoft YaHei', monospace; "
        f'font-size: 14px; line-height: 2; letter-spacing: 0; display: block;">'
        f"{body}</section>"
    )


def blockquote(text: str, palette: dict) -> str:
    return (
        f'<section style="border-radius: 0px; '
        f'padding: 12px 16px; margin: 0; border-left: 4px solid {palette["primary"]}; '
        f'box-sizing: border-box;">'
        f'<section style="font-size: 14px; color: #666666; line-height: 1.7; '
        f'letter-spacing: 0.05em; text-align: left; margin: 0;">{text}</section></section>'
    )


def unordered_list(items: list[str], palette: dict) -> str:
    li_items = "".join(
        f'<section style="margin-bottom: 10px; padding-left: 6px; font-size: 16px; line-height: 1.8;">'
        f'<span style="color: {palette["primary"]}; margin-right: 6px; font-size: 16px;">•</span>{item}</section>'
        for item in items
    )
    return f'<section style="margin-bottom: 20px;">{li_items}</section>'


def ordered_list(items: list[str], palette: dict) -> str:
    li_items = "".join(
        f'<li style="margin-bottom: 10px; font-size: 16px; line-height: 1.8;">{item}</li>'
        for item in items
    )
    return f'<ol style="margin-bottom: 20px; padding-left: 20px;">{li_items}</ol>'


def table(headers: list[str], rows: list[list[str]], palette: dict) -> str:
    th_cells = "".join(
        f'<th style="padding: 12px 15px; text-align: left; border: 1px solid #E5E5E5; '
        f'background-color: {palette["primary"]}; color: #FFFFFF; font-size: 16px;">'
        f'{h}</th>'
        for h in headers
    )
    tr_rows = ""
    for i, row in enumerate(rows):
        bg = "#FFFFFF" if i % 2 == 0 else palette["bg_gray"]
        td_cells = "".join(
            f'<td style="padding: 12px 15px; border: 1px solid #E5E5E5; '
            f'background-color: {bg}; font-size: 16px;">{cell}</td>'
            for cell in row
        )
        tr_rows += f"<tr>{td_cells}</tr>"
    return (
        f'<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 16px;">'
        f"<thead><tr>{th_cells}</tr></thead><tbody>{tr_rows}</tbody></table>"
    )


def image_placeholder(index: int, palette: dict, alt: str = "") -> str:
    caption = ""
    if alt and alt.strip():
        caption = (
            f'<section style="font-size: 13px; color: #999999; text-align: center; '
            f'margin-top: 6px; letter-spacing: 0.05em;">{html_module.escape(alt.strip())}</section>'
        )
    return (
        '<section style="margin: 20px 0; text-align: center;">'
        f'WECHATIMGPH_{index}'
        f'{caption}</section>'
    )


def link(text: str, url: str, palette: dict) -> str:
    return (
        f'<a href="{url}" style="color: {palette["primary"]}; text-decoration: none; '
        f'border-bottom: 1px solid {palette["primary"]}; word-break: break-all;">{text}</a>'
    )


def divider(palette: dict) -> str:
    r, g, b = hex_to_rgb(palette["primary"])
    return (
        f'<hr style="background: linear-gradient(to right, rgba({r},{g},{b},0), '
        f'rgba({r},{g},{b},0.2), rgba({r},{g},{b},0)); height: 1px; border: none; '
        f'margin: 40px 0;">'
    )
