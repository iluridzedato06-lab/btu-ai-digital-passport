"""Generate the stamp and sticker artwork used by the passport PDF and the website.

Recreated from the BTU design reference (Passport.png). Run:
    python scripts/generate_pdf_assets.py
Outputs SVG files into backend/templates/pdf/assets/ and frontend/public/stamps/.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_ASSETS = ROOT / "backend" / "templates" / "pdf" / "assets"
WEB_ASSETS = ROOT / "frontend" / "public" / "stamps"

RED = "#F0433A"
PURPLE = "#5B1CF5"
NAVY = "#14286B"
ORANGE = "#FF6B00"
GREEN = "#34E089"
CYAN = "#16D3F5"
MAGENTA = "#D4198F"
PINK = "#FF1F7A"
FONT = "Montserrat, Arial, sans-serif"


def text(x, y, s, size, weight=800, fill="#fff", anchor="middle", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'
    )


def svg(w, h, body, vb=None):
    vb = vb or f"0 0 {w} {h}"
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{vb}">{body}</svg>\n'


def stamp_focused():
    # Red triangle, white inner outline, stacked label.
    body = (
        f'<polygon points="100,6 196,170 4,170" fill="{RED}"/>'
        f'<polygon points="100,26 178,160 22,160" fill="none" stroke="#fff" stroke-width="3"/>'
        + text(100, 92, "AI", 22)
        + text(100, 116, "SKILL", 22)
        + text(100, 137, "FOCUSED", 13, 400)
        + text(100, 152, "LEARNING", 13, 400)
    )
    return svg(200, 176, f'<g transform="rotate(-4 100 90)">{body}</g>')


def stamp_applied():
    body = (
        f'<rect x="6" y="18" width="228" height="76" fill="{PURPLE}"/>'
        f'<rect x="14" y="26" width="212" height="60" fill="none" stroke="#fff" stroke-width="2"/>'
        + text(120, 55, "AI APPLIED SKILL", 22)
        + text(120, 77, "APPLIED LEARNING", 15, 400)
    )
    return svg(240, 112, f'<g transform="rotate(-6 120 56)">{body}</g>')


def stamp_advanced():
    body = (
        f'<circle cx="90" cy="90" r="86" fill="{NAVY}"/>'
        f'<circle cx="90" cy="90" r="74" fill="none" stroke="#fff" stroke-width="2.5"/>'
        + text(90, 56, "AI", 16)
        + text(90, 76, "ADVANCED", 16)
        + text(90, 96, "SKILL", 16)
        + text(90, 116, "EXTENDED", 10.5, 400)
        + text(90, 129, "ACADEMIC", 10.5, 400)
        + text(90, 142, "LEARNING", 10.5, 400)
    )
    return svg(180, 180, body)


def circular_text(cx, cy, r, s, size, start_deg, spread_deg, weight=800, fill="#111"):
    """Lay characters along a circle; each glyph is placed and rotated individually."""
    out = []
    n = len(s)
    step = spread_deg / max(n - 1, 1)
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        a = math.radians(start_deg + i * step)
        x = cx + r * math.sin(a)
        y = cy - r * math.cos(a)
        rot = start_deg + i * step
        out.append(
            f'<text x="0" y="0" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="middle" transform="translate({x:.2f},{y:.2f}) rotate({rot:.2f})">{ch}</text>'
        )
    return "".join(out)


def asterisk(cx, cy, r, fill, stroke_w):
    arms = []
    for k in range(4):
        a = math.radians(k * 45)
        dx, dy = r * math.cos(a), r * math.sin(a)
        arms.append(
            f'<line x1="{cx - dx:.2f}" y1="{cy - dy:.2f}" x2="{cx + dx:.2f}" y2="{cy + dy:.2f}" '
            f'stroke="{fill}" stroke-width="{stroke_w}" stroke-linecap="butt"/>'
        )
    return "".join(arms)


def cover_stickers():
    """The sticker cluster on the passport cover (approx. 470x300 units)."""
    parts = []
    # Orange "Issued by" banner
    parts.append(
        '<g transform="translate(150,10) rotate(4)">'
        f'<rect x="0" y="0" width="250" height="66" fill="{ORANGE}"/>'
        '<rect x="6" y="6" width="238" height="54" fill="none" stroke="#111" stroke-width="2.5"/>'
        + text(125, 30, "ISSUED BY BUSINESS AND", 16.5, 800, "#111")
        + text(125, 50, "TECHNOLOGY UNIVERSITY", 16.5, 800, "#111")
        + "</g>"
    )
    # Green circular seal
    seal = (
        f'<circle cx="80" cy="150" r="72" fill="{GREEN}"/>'
        '<circle cx="80" cy="150" r="66" fill="none" stroke="#111" stroke-width="2.5"/>'
        '<circle cx="80" cy="150" r="40" fill="none" stroke="#111" stroke-width="2.5"/>'
        + circular_text(80, 150, 50, "SKILLS IN AI · INTERNATIONALLY · RECOGNISED ·", 11, -150, 330)
        + asterisk(80, 150, 22, "#111", 9)
    )
    parts.append(seal)
    # Cyan triangle
    parts.append(
        '<g transform="translate(150,98)">'
        f'<polygon points="85,0 175,150 -5,150" fill="{CYAN}"/>'
        '<polyline points="35,72 85,20 135,72" fill="none" stroke="#111" stroke-width="2.5"/>'
        '<polyline points="45,82 85,40 125,82" fill="none" stroke="#111" stroke-width="2.5"/>'
        + text(85, 104, "AI", 15, 800, "#111")
        + text(85, 121, "SKILLS", 15, 800, "#111")
        + text(85, 140, "DIGITAL PASSPORT", 14, 800, "#111")
        + "</g>"
    )
    # Magenta "Blockchain verified"
    parts.append(
        '<g transform="translate(300,80) rotate(-16)">'
        f'<rect x="0" y="0" width="170" height="66" fill="{MAGENTA}"/>'
        '<rect x="6" y="6" width="158" height="54" fill="none" stroke="#fff" stroke-width="2" stroke-dasharray="5 4"/>'
        + text(85, 30, "BLOCKCHAIN", 19, 800)
        + text(85, 52, "VERIFIED", 19, 800)
        + "</g>"
    )
    # Pink "Latest AI skillset"
    parts.append(
        '<g transform="translate(60,210) rotate(24)">'
        f'<rect x="0" y="0" width="250" height="48" fill="{PINK}"/>'
        '<rect x="5" y="5" width="240" height="38" fill="none" stroke="#fff" stroke-width="2"/>'
        + text(125, 32, "LATEST AI SKILLSET", 21, 800)
        + "</g>"
    )
    return svg(480, 330, "".join(parts))


def orange_asterisk():
    return svg(40, 40, asterisk(20, 20, 18, ORANGE, 8))


def main():
    assets = {
        "stamps/focused.svg": stamp_focused(),
        "stamps/applied.svg": stamp_applied(),
        "stamps/advanced.svg": stamp_advanced(),
        "cover-stickers.svg": cover_stickers(),
        "asterisk.svg": orange_asterisk(),
    }
    for rel, content in assets.items():
        for base in (PDF_ASSETS, WEB_ASSETS):
            target = base / (rel if base == PDF_ASSETS else Path(rel).name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    logo = (PDF_ASSETS / "btu-logo.svg").read_text(encoding="utf-8")
    (PDF_ASSETS / "btu-logo-black.svg").write_text(logo.replace("#fe017e", "#111111"), encoding="utf-8")
    print("assets written")


if __name__ == "__main__":
    main()
