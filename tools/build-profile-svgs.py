#!/usr/bin/env python3
"""Generate the profile section SVGs (light + dark).

Text is measured with the real Segoe UI / Consolas metrics so nothing
overflows or collides. Run:  python tools/build-profile-svgs.py
"""
from __future__ import annotations

import html
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
W = 1000

FONT_DIR = Path(r"C:\Windows\Fonts")
SANS = FONT_DIR / "segoeui.ttf"
SANS_SEMI = FONT_DIR / "seguisb.ttf"
SANS_BOLD = FONT_DIR / "segoeuib.ttf"
MONO = FONT_DIR / "consola.ttf"

FAM = "Segoe UI, Helvetica Neue, Arial, sans-serif"
FAM_MONO = "Consolas, SF Mono, Menlo, monospace"

THEMES = {
    "light": dict(
        ink="#0b1116",
        body="#3d4a55",
        muted="#6b7885",
        line="#e2e7ec",
        accent="#0f766e",
        accent2="#0e7490",
        card="#f8fafb",
        cardline="#e6ecf0",
        chip="#f1f5f7",
        chipline="#dfe7ec",
    ),
    "dark": dict(
        ink="#eef3f6",
        body="#b6c2cc",
        muted="#7d8b97",
        line="#232d36",
        accent="#2dd4bf",
        accent2="#38bdf8",
        card="#0f151c",
        cardline="#1e2a35",
        chip="#131b23",
        chipline="#24313d",
    ),
}

_fonts: dict[tuple[Path, int], ImageFont.FreeTypeFont] = {}


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(path), size)
    return _fonts[key]


WEIGHT_PATH = {"regular": SANS, "semi": SANS_SEMI, "bold": SANS_BOLD, "mono": MONO}


def tw(text: str, size: int, weight: str = "regular", ls: float = 0.0) -> float:
    """Rendered width in px, including letter-spacing."""
    return font(WEIGHT_PATH[weight], size).getlength(text) + ls * len(text)


def txt(
    x: float,
    y: float,
    s: str,
    size: float,
    fill: str,
    weight: str = "regular",
    ls: float = 0.0,
    anchor: str = "start",
    extra: str = "",
) -> str:
    fam = FAM_MONO if weight == "mono" else FAM
    attrs = [f'x="{x:.1f}"', f'y="{y:.1f}"', f'font-family="{fam}"', f'font-size="{size:g}"']
    if weight in ("semi", "bold"):
        attrs.append(f'font-weight="{600 if weight == "semi" else 700}"')
    if ls:
        attrs.append(f'letter-spacing="{ls:g}"')
    attrs.append(f'fill="{fill}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if extra:
        attrs.append(extra)
    return f'<text {" ".join(attrs)}>{html.escape(s)}</text>'


def wrap(text: str, size: int, weight: str, maxw: float, lines_max: int) -> list[str]:
    words = text.split()
    out: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if tw(trial, size, weight) <= maxw or not cur:
            cur = trial
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    if len(out) > lines_max:
        out = out[:lines_max]
        last = out[-1]
        while last and tw(last + "…", size, weight) > maxw:
            last = last[:-1]
        out[-1] = last.rstrip(" ,.;") + "…"
    return out


def svg_open(h: float, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h:g}" '
        f'viewBox="0 0 {W} {h:g}" role="img" aria-label="{html.escape(label)}">'
        f"<title>{html.escape(label)}</title>"
    )


def rule(y: float, t: dict, x1: float = 0, x2: float = W, color: str | None = None) -> str:
    return (
        f'<line x1="{x1:g}" y1="{y:g}" x2="{x2:g}" y2="{y:g}" '
        f'stroke="{color or t["line"]}" stroke-width="1"/>'
    )


def section_head(t: dict, idx: str, label: str, tag: str) -> tuple[list[str], float]:
    y = 16
    parts = [txt(0, y, idx, 11.5, t["accent"], "mono", 1.2)]
    lx = tw(idx, 11.5, "mono", 1.2) + 18
    parts.append(txt(lx, y, label, 12.5, t["ink"], "semi", 2.2))
    lw = tw(label, 12.5, "semi", 2.2)
    rw = tw(tag, 10.5, "mono", 1.2)
    parts.append(txt(W - rw, y, tag, 10.5, t["muted"], "mono", 1.2))
    parts.append(rule(y - 4, t, lx + lw + 22, W - rw - 22))
    return parts, 52.0


def chip(
    x: float, y: float, s: str, t: dict, size: float = 12, h: float = 26, padx: float = 12
) -> tuple[str, float]:
    w = tw(s, size) + padx * 2
    el = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:g}" rx="{h / 2:g}" '
        f'fill="{t["chip"]}" stroke="{t["chipline"]}" stroke-width="1"/>'
        f'{txt(x + padx, y + h / 2 + size * 0.36, s, size, t["ink"])}'
    )
    return el, w


def key_value_chip(
    x: float, y: float, key: str, value: str, t: dict, h: float = 28, padx: float = 13
) -> tuple[str, float]:
    kw = tw(key, 10, "mono", 0.8)
    vw = tw(value, 11.5, "mono")
    w = padx + kw + 9 + vw + padx
    el = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:g}" rx="{h / 2:g}" '
        f'fill="{t["chip"]}" stroke="{t["chipline"]}" stroke-width="1"/>'
        f'{txt(x + padx, y + h / 2 + 3.6, key, 10, t["accent"], "mono", 0.8)}'
        f'{txt(x + padx + kw + 9, y + h / 2 + 4.4, value, 11.5, t["ink"], "mono")}'
    )
    return el, w


# --------------------------------------------------------------------------- header


def build_header(t: dict) -> str:
    H = 312
    s = [svg_open(H, "Atilio Obadia, open source systems developer")]
    s.append("<defs>")
    s.append(
        f'<radialGradient id="glow" cx="0.92" cy="0.1" r="0.85">'
        f'<stop offset="0" stop-color="{t["accent"]}" stop-opacity="0.16"/>'
        f'<stop offset="0.55" stop-color="{t["accent"]}" stop-opacity="0.035"/>'
        f'<stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/>'
        "</radialGradient>"
    )
    s.append(
        f'<linearGradient id="mark" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["accent"]}"/>'
        f'<stop offset="1" stop-color="{t["accent2"]}"/>'
        "</linearGradient>"
    )
    s.append("</defs>")
    s.append(f'<rect width="{W}" height="{H}" fill="url(#glow)"/>')

    # brand
    s.append(
        f'<rect x="0" y="26" width="6" height="14" rx="1.5" fill="url(#mark)"/>'
    )
    s.append(txt(16, 37, "ERPcodec", 11.5, t["accent"], "mono", 2.4))

    # name + role + description
    s.append(txt(0, 118, "Atilio Obadia", 54, t["ink"], "bold", -0.6))
    s.append(txt(2, 156, "Open source systems developer", 20, t["accent"], "semi", 0.2))
    s.append(
        txt(
            2,
            188,
            "ERPNext and Frappe systems, built and run for organisations across East Africa.",
            15,
            t["body"],
        )
    )

    # monogram
    cx, cy = 884.0, 150.0
    s.append(
        f'<circle cx="{cx}" cy="{cy}" r="86" fill="none" stroke="{t["accent"]}" '
        f'stroke-width="1.3" stroke-dasharray="2 11" stroke-linecap="round" opacity="0.5">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" '
        f'to="360 {cx} {cy}" dur="90s" repeatCount="indefinite"/>'
        "</circle>"
    )
    s.append(
        f'<circle cx="{cx}" cy="{cy}" r="72" fill="{t["accent"]}" opacity="0.07"/>'
    )
    s.append(
        f'<circle cx="{cx}" cy="{cy}" r="72" fill="none" stroke="{t["line"]}" stroke-width="1"/>'
    )
    s.append(txt(cx, cy + 14, "AO", 40, t["ink"], "semi", 3, "middle"))

    # availability pill under the monogram
    label = "open to projects"
    pw = tw(label, 11, "mono") + 38
    px = cx - pw / 2
    py = 250
    s.append(
        f'<rect x="{px:.1f}" y="{py}" width="{pw:.1f}" height="26" rx="13" '
        f'fill="{t["chip"]}" stroke="{t["chipline"]}"/>'
    )
    s.append(f'<circle cx="{px + 14:.1f}" cy="{py + 13}" r="3" fill="{t["accent"]}"/>')
    s.append(txt(px + 24, py + 17, label, 11, t["body"], "mono"))

    # meta line
    s.append(rule(224, t))
    meta = [
        "East Africa Community, Tanzania",
        "Alpha Associates Tanzania Limited",
        "atilioobadia@gmail.com",
    ]
    x = 0.0
    for i, item in enumerate(meta):
        s.append(txt(x, 256, item, 11, t["muted"], "mono"))
        x += tw(item, 11, "mono")
        if i < len(meta) - 1:
            s.append(f'<circle cx="{x + 13:.1f}" cy="252" r="2" fill="{t["accent"]}"/>')
            x += 30

    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- 01 whoami


def build_whoami(t: dict) -> str:
    head, top = section_head(t, "01", "whoami", "profile")
    left_w = 572.0
    rail_x = 664.0
    rail_w = W - rail_x

    p1 = (
        "I build and run business systems: ERPNext and Frappe implementations, custom web "
        "platforms, and the integrations and infrastructure underneath them. Most of the work "
        "sits in Tanzania and the wider East Africa Community, where paper and spreadsheets have "
        "stopped keeping up with the operation."
    )
    p2 = (
        "My background is on the infrastructure side, servers, networks and biometric attendance, "
        "which is why I care less about the demo and more about what happens at 08:00 on a Monday. "
        "Fewer spreadsheets, cleaner ledgers, records that survive an audit."
    )

    size, lh = 16.0, 27.0
    lines1 = wrap(p1, size, "regular", left_w * 0.97, 6)
    lines2 = wrap(p2, size, "regular", left_w * 0.97, 6)

    y = top + 22
    body: list[str] = []
    for line in lines1:
        body.append(txt(2, y, line, size, t["body"]))
        y += lh
    y += 14
    for line in lines2:
        body.append(txt(2, y, line, size, t["body"]))
        y += lh
    left_bottom = y - lh + 8

    # right rail
    rail: list[str] = []
    label = "open to projects"
    pw = tw(label, 11, "mono") + 38
    py = top + 8
    rail.append(
        f'<rect x="{rail_x}" y="{py:g}" width="{pw:.1f}" height="26" rx="13" '
        f'fill="{t["chip"]}" stroke="{t["chipline"]}"/>'
    )
    rail.append(f'<circle cx="{rail_x + 14}" cy="{py + 13}" r="3" fill="{t["accent"]}"/>')
    rail.append(txt(rail_x + 24, py + 17, label, 11, t["body"], "mono"))

    rows = [
        ("company", "Alpha Associates Tanzania Limited"),
        ("brand", "ERPcodec"),
        ("base", "Tanzania, East Africa"),
        ("focus", "ERPNext and Frappe"),
    ]
    ry = top + 74
    for key, value in rows:
        rail.append(txt(rail_x, ry, key, 10, t["muted"], "mono", 1.4))
        rail.append(
            f'<text x="{rail_x}" y="{ry + 21:g}" font-family="{FAM}" font-size="13.5" '
            f'font-weight="600" fill="{t["ink"]}">{html.escape(value)}</text>'
        )
        ry += 46
    rail_bottom = ry - 46 + 24

    H = max(left_bottom, rail_bottom) + 26
    s = [svg_open(H, "About Atilio Obadia")]
    s += head
    s += body
    s.append(
        f'<line x1="{rail_x - 44:.1f}" y1="{top + 4}" x2="{rail_x - 44:.1f}" y2="{H - 26:.1f}" '
        f'stroke="{t["line"]}" stroke-width="1"/>'
    )
    s += rail
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- 02 what i do


def build_capabilities(t: dict) -> str:
    head, top = section_head(t, "02", "what i do", "services")
    items = [
        (
            "ERP implementation",
            "Full-cycle ERPNext and Frappe rollouts: chart of accounts, workflows, custom "
            "DocTypes, server and client scripts.",
        ),
        (
            "Custom systems",
            "Purpose-built platforms when off-the-shelf stops fitting: inventory, portals, "
            "booking and operations dashboards.",
        ),
        (
            "Systems integration",
            "REST APIs, payment and messaging gateways, and AI and MCP tooling that sits inside "
            "ERP workflows.",
        ),
        (
            "Infrastructure",
            "Servers, DNS, hosting, backups, monitoring, networks and biometric attendance. "
            "The layer that keeps it usable.",
        ),
    ]
    gap = 14.0
    cw = (W - gap) / 2
    ch = 102.0
    s = [svg_open(top + ch * 2 + gap + 22, "What Atilio Obadia does")]
    s += head

    for i, (title, desc) in enumerate(items):
        col, row = i % 2, i // 2
        x = col * (cw + gap)
        y = top + row * (ch + gap)
        s.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{ch:g}" rx="12" '
            f'fill="{t["card"]}" stroke="{t["cardline"]}" stroke-width="1"/>'
        )
        s.append(
            f'<rect x="{x + 18:.1f}" y="{y + 18:.1f}" width="3" height="13" rx="1.5" '
            f'fill="{t["accent"]}"/>'
        )
        s.append(txt(x + 30, y + 29, title, 15, t["ink"], "semi"))
        s.append(txt(x + cw - 18, y + 28, f"0{i + 1}", 10.5, t["muted"], "mono", 1, "end"))
        for j, line in enumerate(wrap(desc, 14, "regular", (cw - 36) * 0.97, 2)):
            s.append(txt(x + 18, y + 56 + j * 20, line, 14, t["body"]))

    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- 03 work


def build_work(t: dict) -> str:
    head, top = section_head(t, "03", "selected work", "repositories")
    projects = [
        (
            "AIMSCAMS",
            "Back office for Tanzanian SACCOs and microfinance: members, savings, credit, "
            "ledger and regulatory returns.",
            ["TypeScript", "Next.js", "NestJS", "PostgreSQL"],
        ),
        (
            "csf_tanzania_v16",
            "Tanzania localisation for Frappe and ERPNext v16: tax, statutory and country "
            "accounting behaviour.",
            ["Python", "Frappe"],
        ),
        (
            "warehouse_management",
            "Warehouse system on Frappe for X Electronics: stock, movements and storage "
            "locations.",
            ["Python", "Frappe"],
        ),
        (
            "assignment_v16",
            "Production-ready custom app configuration and DocType schemas for the Frappe "
            "v16 framework.",
            ["Python", "Frappe"],
        ),
        (
            "erpnext_payroll_dashboard",
            "Payroll dashboard for ERPNext: salary components, runs and settlement in one "
            "place.",
            ["Python", "Frappe"],
        ),
        (
            "AIMS_Ai_Agent",
            "LLM assistant for the AIMS ecosystem, embedded where the work already happens.",
            ["TypeScript", "AI agents"],
        ),
    ]
    gap = 14.0
    cw = (W - gap * 2) / 3
    ch = 136.0
    s = [svg_open(top + ch * 2 + gap + 22, "Selected work by Atilio Obadia")]
    s += head

    for i, (name, desc, stack) in enumerate(projects):
        col, row = i % 3, i // 3
        x = col * (cw + gap)
        y = top + row * (ch + gap)
        s.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{ch:g}" rx="12" '
            f'fill="{t["card"]}" stroke="{t["cardline"]}" stroke-width="1"/>'
        )
        s.append(
            f'<rect x="{x + 16:.1f}" y="{y + 17:.1f}" width="20" height="2.5" rx="1.25" '
            f'fill="{t["accent"]}"/>'
        )
        s.append(txt(x + cw - 16, y + 34, "↗", 13, t["muted"], anchor="end"))
        s.append(txt(x + 16, y + 34, name, 14.5, t["ink"], "semi"))
        for j, line in enumerate(wrap(desc, 14, "regular", (cw - 32) * 0.97, 3)):
            s.append(txt(x + 16, y + 59 + j * 19.5, line, 14, t["body"]))

        stack_txt = ""
        for part in stack:
            trial = f"{stack_txt} · {part}" if stack_txt else part
            if tw(trial, 11, "mono") <= cw - 32:
                stack_txt = trial
        s.append(txt(x + 16, y + ch - 16, stack_txt, 11, t["muted"], "mono"))

    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- 04 activity header


def build_activity_head(t: dict) -> str:
    head, top = section_head(t, "04", "activity", "telemetry")
    s = [svg_open(46, "GitHub activity")]
    s += head
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- 05 toolkit


def build_toolkit(t: dict) -> str:
    head, top = section_head(t, "05", "toolkit", "stack")
    groups = [
        ("Languages", ["TypeScript", "Python", "JavaScript", "PHP", "HTML", "CSS"]),
        ("Platforms", ["ERPNext", "Frappe", "Next.js", "NestJS", "Node.js", "React"]),
        ("Data", ["PostgreSQL", "MariaDB", "Redis"]),
        ("Infrastructure", ["Docker", "Linux", "Nginx", "Git"]),
    ]
    label_x = 0.0
    chip_x = 172.0
    row_h = 48.0
    s = [svg_open(top + len(groups) * row_h + 8, "Toolkit")]
    s += head

    for i, (label, chips) in enumerate(groups):
        y = top + i * row_h
        s.append(txt(label_x, y + 20, label, 10.5, t["muted"], "mono", 1.4))
        x = chip_x
        chip_y = y + 4
        for item in chips:
            el, w = chip(x, chip_y, item, t)
            if x + w > W:
                raise SystemExit(f"toolkit row overflows: {label}")
            s.append(el)
            x += w + 8

    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- 06 how i work


def build_process(t: dict) -> str:
    head, top = section_head(t, "06", "how i work", "method")
    rows = [
        ("Written scope", "The problem, the constraint and the definition of done, in one page."),
        ("Data model first", "Schemas, ledgers and permissions settled before a screen is drawn."),
        ("Small, reviewable changes", "One logical change per pull request, with tests where it counts."),
        ("Run and document", "Deployment, backups, monitoring and docs ship with the system."),
    ]
    row_h = 50.0
    s = [svg_open(top + len(rows) * row_h + 10, "How Atilio Obadia works")]
    s += head

    for i, (title, desc) in enumerate(rows):
        y = top + i * row_h
        s.append(txt(0, y + 20, f"0{i + 1}", 11, t["accent"], "mono", 1.2))
        s.append(txt(40, y + 20, title, 14, t["ink"], "semi"))
        s.append(txt(330, y + 20, desc, 13.6, t["body"]))
        if i < len(rows) - 1:
            s.append(rule(y + row_h - 6, t))

    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------- 07 connect


def build_connect(t: dict) -> str:
    head, top = section_head(t, "07", "connect", "contact")
    H = top + 196
    s = [svg_open(H, "Contact Atilio Obadia")]
    s += head

    s.append(
        txt(
            0,
            top + 30,
            "Open to ERPNext implementation, custom systems and integration work.",
            21,
            t["ink"],
            "semi",
            -0.1,
        )
    )
    s.append(
        txt(
            0,
            top + 56,
            "East Africa Community, Tanzania. Accepting project work across the region.",
            14,
            t["body"],
        )
    )

    rows = [
        [("email", "atilioobadia@gmail.com"), ("phone", "+255 773 500 811")],
        [
            ("linkedin", "/in/eng-atilio-obadia"),
            ("portfolio", "atilioobadia-cpu.github.io"),
            ("github", "@atilioobadia-cpu"),
        ],
    ]
    for r, row in enumerate(rows):
        x = 0.0
        y = top + 84 + r * 38
        for key, value in row:
            el, w = key_value_chip(x, y, key, value, t)
            if x + w > W:
                raise SystemExit(f"connect row overflows: {key}")
            s.append(el)
            x += w + 10

    s.append(rule(top + 166, t))
    s.append(
        txt(0, top + 190, "MIT licensed · built and maintained in Tanzania", 10.5, t["muted"], "mono")
    )
    s.append(txt(W, top + 190, "Atilio Obadia", 10.5, t["muted"], "mono", 1, "end"))
    s.append("</svg>")
    return "".join(s)


BUILDERS = {
    "header": build_header,
    "whoami": build_whoami,
    "capabilities": build_capabilities,
    "work": build_work,
    "activity": build_activity_head,
    "toolkit": build_toolkit,
    "process": build_process,
    "connect": build_connect,
}


def main() -> None:
    (ASSETS / "dark").mkdir(parents=True, exist_ok=True)
    for name, fn in BUILDERS.items():
        for theme_name, theme in THEMES.items():
            out = ASSETS / name if theme_name == "light" else ASSETS / "dark" / name
            out = out.with_suffix(".svg")
            out.write_text(fn(theme), encoding="utf-8")
            print(f"{out.relative_to(ROOT)}  {out.stat().st_size:>6} bytes")


if __name__ == "__main__":
    main()
