"""Syntax highlighting for WeChat articles using Pygments.

Generates WeChat-compatible HTML with fully inline CSS styles,
since WeChat strips <style> tags and class attributes.

Uses Pygments (the de-facto standard Python syntax highlighter)
with inline style generation for self-contained HTML output.
"""

import html as html_module

from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.util import ClassNotFound


# Claude-style light color mapping for inline token styles
# Warm, elegant palette that matches Claude's aesthetic on light backgrounds
TOKEN_COLORS = {
    # Keywords — Claude 暖橙红
    "Keyword": "#CF4F15",
    "Keyword.Constant": "#8250DF",
    "Keyword.Namespace": "#CF4F15",
    "Keyword.Type": "#0550AE",
    # Names
    "Name.Builtin": "#0550AE",
    "Name.Builtin.Pseudo": "#8250DF",
    "Name.Function": "#8250DF",
    "Name.Class": "#8250DF",
    "Name.Decorator": "#8250DF",
    "Name.Exception": "#8250DF",
    "Name.Variable": "#24292F",
    "Name.Attribute": "#0550AE",
    "Name.Tag": "#116329",
    "Name.Property": "#0550AE",
    # Strings — 森林绿
    "String": "#0A6640",
    "String.Doc": "#0A6640",
    "String.Single": "#0A6640",
    "String.Double": "#0A6640",
    "String.Backtick": "#0A6640",
    "String.Regex": "#0A6640",
    "String.Escape": "#8250DF",
    # Comments — 柔灰
    "Comment": "#6E7781",
    "Comment.Single": "#6E7781",
    "Comment.Multiline": "#6E7781",
    "Comment.Special": "#6E7781",
    # Numbers — 优雅紫
    "Number": "#8250DF",
    "Number.Float": "#8250DF",
    "Number.Integer": "#8250DF",
    "Number.Hex": "#8250DF",
    # Operators
    "Operator": "#CF4F15",
    "Operator.Word": "#CF4F15",
    # Punctuation
    "Punctuation": "#24292F",
    # Generics
    "Generic.Heading": "#0550AE",
    "Generic.Subheading": "#8250DF",
    "Generic.Deleted": "#82071E",
    "Generic.Inserted": "#116329",
}

DEFAULT_COLOR = "#24292F"


def _color_for_token(token_type) -> str:
    """Resolve a Pygments token type to an inline CSS color string."""
    # Walk up the token hierarchy
    t = token_type
    while t:
        name = str(t).replace("Token.", "")
        if name in TOKEN_COLORS:
            return TOKEN_COLORS[name]
        # Also try first part (e.g. "Keyword" from "Keyword.Constant")
        if "." in name:
            first = name.split(".")[0]
            if first in TOKEN_COLORS:
                return TOKEN_COLORS[first]
        t = t.parent
    return DEFAULT_COLOR


def highlight_code(code: str, language: str = "") -> str:
    """Highlight code using Pygments with inline CSS for WeChat compatibility.

    Merges adjacent same-color tokens to minimize HTML size.

    Args:
        code: Raw source code text.
        language: Language identifier (e.g. 'python', 'js', 'json').
                  Empty string triggers auto-detection.

    Returns:
        HTML string with inline color styles, using <br> for line breaks
        and &nbsp; for indentation (WeChat-compatible).
    """
    if not code.strip():
        return ""

    lexer = _resolve_lexer(code, language)
    tokens = lexer.get_tokens(code)

    # First pass: build colored segments (merge adjacent same-color)
    segments = []  # list of (color, text) tuples
    for token_type, token_value in tokens:
        if not token_value:
            continue
        color = _color_for_token(token_type)
        escaped = html_module.escape(token_value).replace(" ", "&nbsp;")
        if segments and segments[-1][0] == color:
            segments[-1] = (color, segments[-1][1] + escaped)
        else:
            segments.append((color, escaped))

    # Second pass: split into lines and wrap in spans
    html_lines = []
    current_line_parts = []

    for color, text in segments:
        parts = text.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                html_lines.append("".join(current_line_parts))
                current_line_parts = []

            if part:
                current_line_parts.append(
                    f'<span style="color:{color};">{part}</span>'
                )

    if current_line_parts:
        html_lines.append("".join(current_line_parts))

    # Remove trailing empty line from trailing newline
    if html_lines and not html_lines[-1].strip():
        html_lines = html_lines[:-1]

    return "<br>\n".join(html_lines)


def _resolve_lexer(code: str, language: str = ""):
    """Resolve a Pygments lexer from language name or code content."""
    language = language.strip().lower()

    alias_map = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "sh": "bash",
        "shell": "bash",
        "yml": "yaml",
        "md": "markdown",
        "json5": "json",
    }
    language = alias_map.get(language, language)

    if language:
        try:
            return get_lexer_by_name(language)
        except ClassNotFound:
            pass

    try:
        return guess_lexer(code)
    except ClassNotFound:
        return TextLexer()
