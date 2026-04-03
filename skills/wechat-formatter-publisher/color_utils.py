"""Color derivation utilities for WeChat article themes.

Derives a full color palette from a single primary hex color using HSL
manipulations via the standard library's colorsys module.
"""

import colorsys


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color string to HSL tuple (h, s, l) in 0-1 range."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)  # returns (h, l, s)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL values (0-1 range) to hex color string."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(
        int(round(r * 255)), int(round(g * 255)), int(round(b * 255))
    )


def derive_palette(primary: str) -> dict[str, str]:
    """Derive a full color palette from a primary hex color.

    Derivation rules:
    - primary_deep: L-15% (darker variant for borders, gradients)
    - primary_light: L+10% (lighter variant for accents)
    - bg_light: S=15%, L=97% (light background tints)
    - bg_gray: fixed #FAF9F7 (neutral gray for alternating rows)
    - text_color: #2D2D2D (dark gray body text)
    - heading_color: #1A1A1A (near-black headings)
    - code_bg: #2D2D2D (dark code background)
    - code_text: #E8E8E8 (light code text)
    - code_comment: #6A9955 (green code comments)
    """
    h, l, s = hex_to_hsl(primary)

    return {
        "primary": primary,
        "primary_deep": hsl_to_hex(h, s, max(0, l - 0.15)),
        "primary_light": hsl_to_hex(h, s, min(1, l + 0.10)),
        "bg_light": hsl_to_hex(h, 0.15, 0.97),
        "bg_gray": "#FAF9F7",
        "text_color": "#2D2D2D",
        "heading_color": "#1A1A1A",
        "code_bg": "#2D2D2D",
        "code_text": "#E8E8E8",
        "code_comment": "#6A9955",
    }


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
