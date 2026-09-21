"""
core/web/design_tokens.py — shared Figma-token comparison helpers.

Playwright's getComputedStyle() always returns colors as `rgb(r, g, b)` and
font-weight as a numeric string (e.g. "700"), never as the hex codes or
weight names ("Bold") a Figma spec or QA case states them in. Centralizing
the conversion here means every test/Page Object that probes design tokens
converts the same way once, instead of ~20 inline hex->rgb literals that can
drift or be transcribed wrong one at a time.
"""

import re

FONT_WEIGHT_NAMES = {
    "regular": "400",
    "medium": "500",
    "semibold": "600",
    "bold": "700",
}


def hex_to_rgb(hex_color: str) -> str:
    """'#911731' -> 'rgb(145, 23, 49)' — matches getComputedStyle's format."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgb({r}, {g}, {b})"


def effective_color(computed: dict) -> tuple:
    """{'color': ..., 'opacity': ...} -> ('rgb(r, g, b)', alpha).

    A spec's "#FFFFFF at 50% opacity" can legitimately be implemented as an
    rgba() alpha channel OR as a CSS `opacity` on the element; both render
    identically, so both are folded into one effective alpha before the
    comparison. `computed` is a getComputedStyle dict carrying at least
    'color'; 'opacity' is optional and treated as 1 when absent."""
    parts = re.findall(r"[\d.]+", computed["color"])
    r, g, b = (int(float(v)) for v in parts[:3])
    alpha = float(parts[3]) if len(parts) > 3 else 1.0
    alpha *= float(computed.get("opacity") or 1)
    return f"rgb({r}, {g}, {b})", round(alpha, 3)


def weight_matches(computed_weight: str, expected_name: str) -> bool:
    """expected_name is one of Regular/Medium/SemiBold/Bold (case-insensitive)."""
    numeric = FONT_WEIGHT_NAMES.get(expected_name.strip().lower())
    return numeric is not None and str(computed_weight).strip() == numeric


def font_family_contains(computed_family: str, family_name: str = "Cairo") -> bool:
    return family_name.lower() in (computed_family or "").lower()


def px_close(computed_px: str, expected_px: str, tolerance: float = 1.0) -> bool:
    """Loose px comparison — some browsers report a sub-pixel line-height
    (e.g. '38.1px' for a spec of '38px'/24*1.something), which is a real
    render value, not a defect, and must not false-red a token check."""
    try:
        c = float(str(computed_px).rstrip("px"))
        e = float(str(expected_px).rstrip("px"))
    except ValueError:
        return computed_px == expected_px
    return abs(c - e) <= tolerance
